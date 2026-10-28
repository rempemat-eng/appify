"""Conservative condition analysis for the narrative data validator.

Inputs have already passed structural and reference validation. Quest states are
``none``, ``done`` or ``step:<id>``; flags and restoration records are independent
booleans. No flag producer, event source or cross-quest history is assumed.

A conjunction is one Cartesian cube with an integer Glint interval. Subtracting
earlier dialogue cubes proves whether their *union* covers a later branch. The
analysis is bounded: exhausting its budget returns "possibly uncovered", never
an unsupported unreachable-branch finding. ``possible`` needs no search and is
exact for this independent-state model.

The runtime treats a missing/null condition as true before checking Glint. An
object, including ``{}``, instead requires ``glint >= 0`` unless it supplies a
different threshold. Glint therefore starts unbounded in both directions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


Axis = tuple[str, str]
Value = str | bool
Domain = frozenset[Value]

_BOOLEAN: Domain = frozenset((False, True))
_MAX_CUBES = 2048
_MAX_AXIS_OPERATIONS = 100_000


@dataclass
class _Cube:
    domains: dict[Axis, Domain] = field(default_factory=dict)
    lower: int | None = None
    upper: int | None = None


class _AnalysisLimit(Exception):
    pass


@dataclass
class _Budget:
    remaining: int = _MAX_AXIS_OPERATIONS

    def spend(self, count: int = 1) -> None:
        self.remaining -= count
        if self.remaining < 0:
            raise _AnalysisLimit


def _quest_domains(steps: dict[str, list[str]]) -> dict[Axis, Domain]:
    return {
        ("quest", qid): frozenset(("none", "done", *("step:" + sid for sid in ids)))
        for qid, ids in steps.items()
    }


def _full_domain(axis: Axis, quests: dict[Axis, Domain]) -> Domain:
    return quests[axis] if axis[0] == "quest" else _BOOLEAN


def _domain(cube: _Cube, axis: Axis, quests: dict[Axis, Domain]) -> Domain:
    return cube.domains.get(axis, _full_domain(axis, quests))


def _restrict(cube: _Cube, axis: Axis, values: Domain, quests: dict[Axis, Domain]) -> None:
    cube.domains[axis] = _domain(cube, axis, quests) & values


def _interval_exists(lower: int | None, upper: int | None) -> bool:
    return lower is None or upper is None or lower <= upper


def _condition_cube(
    cond: dict | None,
    quests: dict[Axis, Domain],
    states: dict[str, set[str]] | None = None,
) -> _Cube | None:
    cube = _Cube()
    if states is not None:
        for qid, domain in states.items():
            _restrict(cube, ("quest", qid), frozenset(domain), quests)
    if cond is not None:
        cube.lower = int(cond.get("glint_at_least", 0))
        for key, namespace, value in (
            ("flags", "flag", True),
            ("not_flags", "flag", False),
            ("restored", "restored", True),
            ("not_restored", "restored", False),
        ):
            for name in cond.get(key, []):
                _restrict(cube, (namespace, name), frozenset((value,)), quests)
        for key in ("done", "active", "not_started"):
            for qid in cond.get(key, []):
                axis = ("quest", qid)
                if key == "active":
                    values = frozenset(value for value in quests[axis] if value.startswith("step:"))
                else:
                    values = frozenset(("done" if key == "done" else "none",))
                _restrict(cube, axis, values, quests)
        if "step" in cond:
            qid, sid = cond["step"]
            _restrict(cube, ("quest", qid), frozenset(("step:" + sid,)), quests)
    if any(not domain for domain in cube.domains.values()):
        return None
    return cube


def possible(
    cond: dict | None,
    steps: dict[str, list[str]],
    states: dict[str, set[str]] | None = None,
) -> bool:
    """Whether a validated conjunction can hold within optional quest domains.

    ``states`` intersects the normal domain of each supplied quest. Callers can
    pin the quest being started to ``{"none"}``, or a current step to
    ``{"step:<id>"}``, without treating unknown external flags as false.
    Inputs are never mutated. A true result is not a whole-game reachability
    proof, since independent external state remains deliberately unconstrained.
    """
    return _condition_cube(cond, _quest_domains(steps), states) is not None


def _subtract(
    source: _Cube,
    cover: _Cube,
    quests: dict[Axis, Domain],
    budget: _Budget,
) -> list[_Cube]:
    """Return disjoint cubes for ``source - cover`` without enumerating states."""
    axes = sorted(source.domains.keys() | cover.domains.keys())
    budget.spend(len(axes) + 1)
    overlap: dict[Axis, Domain] = {}
    for axis in axes:
        intersection = _domain(source, axis, quests) & _domain(cover, axis, quests)
        if not intersection:
            return [source]
        overlap[axis] = intersection
    lower = source.lower
    if cover.lower is not None:
        lower = cover.lower if lower is None else max(lower, cover.lower)
    upper = source.upper
    if cover.upper is not None:
        upper = cover.upper if upper is None else min(upper, cover.upper)
    if not _interval_exists(lower, upper):
        return [source]

    remaining = _Cube(dict(source.domains), source.lower, source.upper)
    outside: list[_Cube] = []
    for axis in axes:
        difference = _domain(remaining, axis, quests) - overlap[axis]
        if difference:
            fragment = _Cube(dict(remaining.domains), remaining.lower, remaining.upper)
            fragment.domains[axis] = difference
            outside.append(fragment)
        remaining.domains[axis] = overlap[axis]
    if lower is not None and (remaining.lower is None or remaining.lower < lower):
        outside.append(_Cube(dict(remaining.domains), remaining.lower, lower - 1))
    if upper is not None and (remaining.upper is None or remaining.upper > upper):
        outside.append(_Cube(dict(remaining.domains), upper + 1, remaining.upper))
    return outside


def has_uncovered_state(cond: dict | None, previous: list, steps: dict[str, list[str]]) -> bool:
    """Whether a branch may match without any earlier branch matching.

    False proves that the union of earlier conjunctions covers every state of
    this condition, or that the condition itself is impossible. True can mean
    either a concrete uncovered cube or an exhausted analysis budget. In
    particular, exceeding a budget must never produce a shadowing error.
    """
    quests = _quest_domains(steps)
    initial = _condition_cube(cond, quests)
    if initial is None:
        return False
    remaining = [initial]
    budget = _Budget()
    try:
        for earlier in previous:
            budget.spend()
            cover = _condition_cube(earlier, quests)
            if cover is None:
                continue
            uncovered: list[_Cube] = []
            for cube in remaining:
                uncovered.extend(_subtract(cube, cover, quests, budget))
                if len(uncovered) > _MAX_CUBES:
                    return True
            remaining = uncovered
            if not remaining:
                return False
    except _AnalysisLimit:
        return True
    return bool(remaining)
