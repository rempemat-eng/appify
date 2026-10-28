"""Validate provisional X3 references without granting runtime or design approval."""
import argparse
import hashlib
import json
from pathlib import Path

PHASES = ("morning", "day", "evening", "night")
LIFE_KEYS = {"residents", "routines", "life_planning"}
SOURCE_COMMIT = "911edac6173ebf4398bcbf54b6171e4e68e62e13"
SOURCE_BLOB = "3c238e470f2da19082227a0a56580b4d1ca2810c"


def check(plan, source):
    """Return findings; source is the pinned, unchanged town layout."""
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)

    require({k: v for k, v in plan.items() if k not in LIFE_KEYS}
            == {k: v for k, v in source.items() if k not in LIFE_KEYS},
            "source: non-life town data changed")
    meta = plan.get("life_planning", {})
    require(meta.get("source_commit") == SOURCE_COMMIT and meta.get("source_blob") == SOURCE_BLOB,
            "provenance: pinned source commit/blob mismatch")
    require(meta.get("schema") == "mygame.settlement_life/1", "metadata: schema")
    require(meta.get("status") == "proposal" and meta.get("runtime_enabled") is False,
            "approval: planning must remain inactive proposal")
    require(meta.get("population_count") is None, "population: no authored headcount")
    for kind in ("animals", "props"):
        value = meta.get(kind, {})
        require(value.get("status") == "deferred" and value.get("instances") == []
                and bool(value.get("reason")), f"{kind}: deferred source inputs required")
    buildings = {b["id"]: b for b in source["buildings"]}
    streets = {s["id"] for s in source["streets"]}
    squares = {s["id"] for s in source["squares"]}
    residents = plan.get("residents", [])
    ids = [r.get("id") for r in residents]
    require(all(isinstance(x, str) and x for x in ids) and len(set(ids)) == len(ids),
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
    for entry in plan.get("routines", []):
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
    args = parser.parse_args()
    try:
        source_bytes = args.source.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(source_bytes)).encode() + b"\0" + source_bytes).hexdigest()
        if blob != SOURCE_BLOB:
            raise ValueError("source file does not match pinned Git blob")
        findings = check(json.loads(args.plan.read_text()), json.loads(source_bytes))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        print(f"Invalid input: {exc}")
        return 2
    for finding in findings:
        print(finding)
    print("Planning references PASS (runtime/design approval not established)" if not findings
          else f"Planning references FAIL: {len(findings)}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
