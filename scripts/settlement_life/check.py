"""Validate provisional X3 references without granting runtime or design approval."""
import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PHASES = ("morning", "day", "evening", "night")
LIFE_KEYS = {"residents", "routines", "life_planning"}
SOURCE_COMMIT = "911edac6173ebf4398bcbf54b6171e4e68e62e13"
SOURCE_BLOB = "3c238e470f2da19082227a0a56580b4d1ca2810c"
SOURCE_PATH = "docs/vision/research/blockout/towns/gullwick.json"
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SourcePin:
    """Caller-selected identity, never inferred from the packet being checked."""
    commit: str = SOURCE_COMMIT
    blob: str = SOURCE_BLOB
    path: str = SOURCE_PATH

    def __post_init__(self):
        for value in (self.commit, self.blob):
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
                raise ValueError("source identity requires full lowercase Git SHAs")
        if not isinstance(self.path, str) or not re.fullmatch(
                r"docs/vision/research/blockout/towns/[a-z0-9][a-z0-9_-]*\.json", self.path):
            raise ValueError("source path must be a repository town JSON path")


def read_document(raw):
    """Reject duplicate keys and non-JSON constants rather than losing evidence."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"non-JSON constant: {value}")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def verify_source(raw, pin):
    """Verify exact bytes AND commit:path using existing local Git objects."""
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != pin.blob:
        raise ValueError("source file does not match pinned Git blob")
    for args, expected in [(["cat-file", "-t", pin.commit], "commit"),
                           (["rev-parse", f"{pin.commit}:{pin.path}"], pin.blob)]:
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                                text=True, timeout=30, check=False)
        if result.returncode or result.stdout.strip() != expected:
            raise ValueError("source commit/path/blob mismatch or Git object unavailable; fetch the exact source first")


def records(value, label):
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise ValueError(f"{label}: expected an array of objects")
    return value


def source_records(source, key):
    rows = records(source.get(key), f"source {key}")
    ids = [row.get("id") for row in rows]
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"source {key}: duplicate or missing id")
    return {row["id"]: row for row in rows}


def check(plan, source, *, source_pin=None):
    """Return findings against an independently selected source/pin.

    Pure API callers supply a trusted parsed source; CLI verifies raw bytes and Git.
    The default preserves the original Gullwick packet contract.
    """
    pin = SourcePin() if source_pin is None else source_pin
    if not isinstance(pin, SourcePin) or not isinstance(plan, dict) or not isinstance(source, dict):
        raise ValueError("plan/source must be objects and source_pin must be a SourcePin")
    if source.get("id") != Path(pin.path).stem:
        raise ValueError("source town id does not match pinned path")
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)

    require({k: v for k, v in plan.items() if k not in LIFE_KEYS}
            == {k: v for k, v in source.items() if k not in LIFE_KEYS},
            "source: non-life town data changed")
    meta = plan.get("life_planning", {})
    if not isinstance(meta, dict):
        raise ValueError("life_planning must be an object")
    require(meta.get("source_commit") == pin.commit and meta.get("source_blob") == pin.blob,
            "provenance: pinned source commit/blob mismatch")
    require(meta.get("source_path", SOURCE_PATH if source_pin is None else None) == pin.path,
            "provenance: pinned source path mismatch")
    require(meta.get("schema") == "mygame.settlement_life/1", "metadata: schema")
    require(meta.get("status") == "proposal" and meta.get("runtime_enabled") is False,
            "approval: planning must remain inactive proposal")
    require(meta.get("population_count") is None, "population: no authored headcount")
    for kind in ("animals", "props"):
        value = meta.get(kind, {})
        require(value.get("status") == "deferred" and value.get("instances") == []
                and bool(value.get("reason")), f"{kind}: deferred source inputs required")
    buildings = source_records(source, "buildings")
    streets = source_records(source, "streets")
    squares = source_records(source, "squares")
    if len(set(buildings) | set(streets) | set(squares)) != len(buildings) + len(streets) + len(squares):
        raise ValueError("source: ambiguous place id across kinds")
    residents = records(plan.get("residents", []), "residents")
    ids = [r.get("id") for r in residents]
    if any(not isinstance(x, str) or not x for x in ids):
        raise ValueError("residents: id must be a nonempty string")
    require(len(set(ids)) == len(ids),
            "residents: duplicate or missing id")
    occupied = {b["id"] for b in source["buildings"] if b.get("occupants")}
    homes = [r.get("home") for r in residents]
    require(set(homes) == occupied and len(homes) == len(occupied),
            "coverage: one provisional representative per occupied home")
    for r in residents:
        tag = r.get("id", "?")
        b = buildings.get(r.get("home"))
        require(b is not None, f"{tag}: unknown home")
        if b:
            require(r.get("role") == b["occupants"] == r.get("source_occupants"),
                    f"{tag}: role must preserve source occupants")
            require(r.get("district") == b["district"], f"{tag}: district mismatch")
        require(isinstance(r.get("name"), str) and "(placeholder)" in r["name"]
                and r.get("name_status") == "placeholder", f"{tag}: placeholder name")
        require(r.get("workplace") is None and r.get("workplace_status") == "deferred",
                f"{tag}: unsourced workplace")
        require(r.get("status") == "proposal", f"{tag}: resident approval")
    seen = set()
    for entry in records(plan.get("routines", []), "routines"):
        rid, phase, place = (entry.get(k) for k in ("resident", "time_of_day", "place"))
        require(rid in ids, "routine: unknown resident")
        require(phase in PHASES, "routine: unknown provisional phase")
        require((rid, phase) not in seen, "routine: duplicate resident phase")
        seen.add((rid, phase))
        require(place in buildings or place in streets or place in squares,
                "routine: unknown place")
        require(entry.get("status") == "proposal" and entry.get("timing") == "placeholder",
                "routine: unapproved timing or activation")
        resident = next((r for r in residents if r.get("id") == rid), None)
        if resident and resident.get("home") in buildings:
            home = buildings[resident["home"]]
            expected = home["faces"] if phase == "day" else home["id"]
            require(place == expected, "routine: destination outside home/home street packet")
    require(seen == {(rid, phase) for rid in ids for phase in PHASES},
            "routines: missing phase coverage")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--source-blob")
    parser.add_argument("--source-path")
    args = parser.parse_args()
    try:
        identity = (args.source_commit, args.source_blob, args.source_path)
        if any(x is not None for x in identity) and not all(x is not None for x in identity):
            raise ValueError("supply source commit, blob and path together")
        explicit = all(x is not None for x in identity)
        pin = SourcePin(*identity) if explicit else SourcePin()
        source_bytes = args.source.read_bytes()
        verify_source(source_bytes, pin)
        findings = check(read_document(args.plan.read_bytes()), read_document(source_bytes),
                         source_pin=pin if explicit else None)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.TimeoutExpired) as exc:
        print(f"Invalid input: {exc}")
        return 2
    for finding in findings:
        print(finding)
    print("Planning references PASS (runtime/design approval not established)" if not findings
          else f"Planning references FAIL: {len(findings)}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
