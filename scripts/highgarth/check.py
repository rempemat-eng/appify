"""Validate Y14 proposal metadata and pinned provenance; never build or place a piece."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLAN_COMMIT = "911edac6173ebf4398bcbf54b6171e4e68e62e13"
CATALOGUE_COMMIT = "7e816ab09107424af3fc7b1d01689955de8b57c6"
BRIEF_SHA256 = "8622c30f820e605348306bea26c977c1daa678c9c4d774da67404663e2b66ed9"
SOURCE_LOCK = {
    "source_highgarth.json": (PLAN_COMMIT, "docs/vision/research/blockout/towns/highgarth.json",
        "bb6e79e619497d53b96155bce364c3675a7b9f8e", "77d250737dd0ef39b23951cabf817a286dda7f430cfeea76824b3c89d36edccb"),
    "piece.schema.json": (CATALOGUE_COMMIT, "game/kit/schema/piece.schema.json",
        "da824ba6eac1a9110f7ecaddbff7a416adc6a69b", "baf021fc840e85c3874497fb9211e9ef2934824559eef601c1066c134f43ad3a"),
}
SUFFIXES = {"machiya", "post_inn", "kura", "minka", "temple_hall", "pagoda", "temple_gate",
    "shrine_gate", "stone_lantern", "bell_frame", "footbridge", "terraced_field", "retaining_wall",
    "watch_keep", "grey_paving", "raked_gravel", "moss", "stone_steps", "snow"}
IDS = {"highgarth_" + x for x in SUFFIXES}
FORMS = {"machiya": "machiya", "post_inn": "honjin", "kura": "kura", "minka": "minka_thatched",
    "temple_hall": "temple_hall", "pagoda": "pagoda", "watch_keep": "watchkeep"}
PROPOSAL_NOTE = "Status: concept only, outside the live piece library; not approved, drawn, buildable or placeable, including labs."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-finite JSON number: " + value)


def _unicode(value):
    if isinstance(value, str):
        require(not any(ord(c) == 0 or 0xD800 <= ord(c) <= 0xDFFF for c in value), "invalid Unicode/NUL in metadata")
    elif isinstance(value, dict):
        for k, v in value.items():
            _unicode(k)
            _unicode(v)
    elif isinstance(value, list):
        for v in value:
            _unicode(v)


def read_json(path):
    require(not path.is_symlink(), "symlink input refused: " + str(path))
    value = json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    _unicode(value)
    return value


def same(a, b):
    # Python equality alone aliases false/0 and true/1; metadata types matter.
    return json.dumps(a, sort_keys=True, ensure_ascii=False, allow_nan=False) == json.dumps(b, sort_keys=True, ensure_ascii=False, allow_nan=False)


def source_limits(town):
    return {
        "legacy_purpose_labels": [b["id"] for b in town["buildings"] if "chapel" in b.get("purpose", "").lower()],
        "machiya_bay_storeys": [{"id": b["id"], "storeys": bay["storeys"]}
            for b in town["buildings"] if b["form"] == "machiya" for bay in b.get("bays", []) if bay.get("storeys") != 2],
        "building_records": len(town["buildings"]),
        "counted_buildings": sum(b.get("counted") is True for b in town["buildings"]),
        "declared_buildings_counted": town["buildings_counted"],
    }


def expected_widths(town, suffix, form):
    if form:
        wr, dr = town["size_table_px"][form]
        require(all(type(x) is int and x > 0 and x % 8 == 0 for x in wr + dr), "source width/depth is not whole cells")
        return {"status": "source planning range; not approved drawing geometry", "plan_width_world_px": wr,
            "plan_depth_world_px": dr, "classes": [{"id": "source_min", "width_cells": wr[0] // 8}, {"id": "source_max", "width_cells": wr[1] // 8}]}
    if suffix == "stone_steps":
        streets = {s["id"]: s for s in town["streets"]}
        return {"status": "source route widths; not tread, rise or image dimensions", "classes": [
            {"id": "temple_flight", "width_cells": streets["highgarth-s04"]["width_cells"]},
            {"id": "keep_flight", "width_cells": streets["highgarth-s08"]["width_cells"]}]}
    return {"status": "deferred; no exact family width in the brief", "classes": []}


def check(root=ROOT):
    packet = root / "scripts/highgarth"
    manifest = read_json(packet / "manifest.json")
    require(isinstance(manifest, dict) and manifest.get("schema") == "mygame.highgarth_concepts/1", "unsupported packet schema")
    for flag in ["approved", "buildable", "placeable"]:
        require(manifest.get(flag) is False, "proposal flag must be false: " + flag)
    require(manifest.get("status") == "concept review only", "proposal status missing")
    require(same(manifest.get("units"), {"world_px_per_cell": 8, "art_px_per_cell": 24, "density": 3,
        "plan_dimensions": "world-pixel ground footprints, never image or collision bounds"}), "unit/geometry boundary changed")
    require(same(manifest.get("constraints"), {"modern_elements": False, "real_script": False,
        "vermilion_scope": {"highgarth_temple_gate": "gate", "highgarth_pagoda": "trim"}}), "sourced design constraints changed")
    sources = manifest.get("sources")
    require(isinstance(sources, dict) and set(sources) == set(SOURCE_LOCK) | {"brief.txt"}, "source inventory changed")
    for name, (commit, source_path, blob, sha) in SOURCE_LOCK.items():
        info = sources[name]
        require(same(info, {"commit": commit, "path": source_path, "blob": blob, "sha256": sha, "fixture": "fixtures/" + name}), "source provenance mismatch: " + name)
        path = packet / "fixtures" / name
        require(not path.is_symlink(), "symlink fixture refused")
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == sha, "source fingerprint mismatch: " + name)
        require(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == blob, "source Git blob mismatch")
    brief = sources["brief.txt"]
    require(brief.get("fixture") == "fixtures/brief.txt" and brief.get("issue") == 149 and brief.get("comment") == 6464788488
        and brief.get("updated_at") == "2026-10-28T08:56:07Z" and brief.get("normalization") == "comment body with one final LF", "brief provenance mismatch")
    brief_path = packet / "fixtures/brief.txt"
    require(not brief_path.is_symlink() and brief.get("sha256") == BRIEF_SHA256
        and hashlib.sha256(brief_path.read_bytes()).hexdigest() == BRIEF_SHA256, "brief fingerprint mismatch")
    town = read_json(packet / "fixtures/source_highgarth.json")
    require(town["style"]["name"] == "old_japanese_post_town", "Y14 prerequisite is not the revised post-town plan")
    require(same(manifest.get("source_limits"), source_limits(town)), "source limitations were changed or hidden")
    schema = read_json(packet / "fixtures/piece.schema.json")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    rows = manifest.get("concepts")
    require(isinstance(rows, list) and len(rows) == len(IDS) and all(isinstance(r, dict) for r in rows), "expected nineteen concept entries")
    require(len({r.get("id") for r in rows}) == len(IDS) and {r.get("id") for r in rows} == IDS, "missing/duplicate/unknown concept coverage")
    directory = root / "game/data/kit/concepts"
    paths = list(directory.glob("highgarth_*.json"))
    require({p.stem for p in paths} == IDS, "concept file inventory differs from brief")
    building_ids = {b["id"] for b in town["buildings"]}
    district_ids = {d["id"] for d in town["districts"]}
    street_ids = {s["id"] for s in town["streets"]}
    covered_buildings = set()
    variant_count = 0
    for row in rows:
        ident = row["id"]
        suffix = ident.removeprefix("highgarth_")
        record = read_json(directory / (ident + ".json"))
        errors = sorted(validator.iter_errors(record), key=lambda e: str(list(e.path)))
        require(not errors, "W0 structural schema: " + ident + (": " + errors[0].message if errors else ""))
        require(record.get("id") == ident and record.get("kind") == row.get("kind"), "record identity/kind mismatch: " + ident)
        require(record.get("biomes") == ["highgarth"] and type(record.get("version")) is int and record["version"] == 1, "record namespace/version mismatch")
        require(record.get("approval", {}).get("state") == "concept", "concept promotion refused: " + ident)
        require(set(record) == {"schema", "id", "name", "kind", "biomes", "version", "variants", "approval", "geometry", "placement", "rendering", "function", "story", "audit"}, "runtime/unknown block in concept: " + ident)
        require(record["function"] == {} and set(record["geometry"]) == {"z_sort"}, "runtime geometry/interaction binding refused: " + ident)
        require(set(record["rendering"]) == {"contact_ao"}, "runtime renderer/asset binding refused")
        require(set(record["audit"]) == {"size_class", "eastward_ref", "todo"} and record["audit"]["eastward_ref"] is None, "art review/evidence cannot be invented")
        variants = record["variants"]
        require(variants and len({v["id"] for v in variants}) == len(variants), "empty/duplicate variants: " + ident)
        require([v["id"] for v in variants] == row.get("variants") and all(set(v) == {"id", "note"} and v["note"].strip() for v in variants), "variant/asset mismatch: " + ident)
        variant_count += len(variants)
        require(row.get("source_form") == FORMS.get(suffix), "wrong source form: " + ident)
        form = row["source_form"]
        refs = row.get("references")
        require(isinstance(refs, dict) and set(refs) == {"building_ids", "district_ids", "street_ids", "feature_keys"}, "reference inventory malformed")
        for field, allowed in [("building_ids", building_ids), ("district_ids", district_ids), ("street_ids", street_ids), ("feature_keys", set(town["features"]))]:
            values = refs[field]
            require(isinstance(values, list) and all(isinstance(v, str) for v in values) and len(set(values)) == len(values) and set(values) <= allowed, "missing/duplicate source reference: " + ident)
        expected_buildings = [b["id"] for b in town["buildings"] if form and b["form"] == form]
        require(refs["building_ids"] == expected_buildings, "source building mapping mismatch: " + ident)
        covered_buildings.update(expected_buildings)
        require(refs["feature_keys"] == (["shrine_gates_px"] if suffix == "shrine_gate" else []), "shrine repetition evidence missing")
        require(refs["street_ids"] == (["highgarth-s04", "highgarth-s08"] if suffix == "stone_steps" else []), "step route provenance missing")
        widths = expected_widths(town, suffix, form)
        require(same(row.get("widths"), widths), "source width/depth/type mismatch: " + ident)
        scope = {"temple_gate": "gate", "pagoda": "trim"}.get(suffix, "none")
        require(row.get("vermilion_scope") == scope, "vermilion scope outside brief: " + ident)
        todo = record["audit"]["todo"]
        require(PROPOSAL_NOTE in todo and any(PLAN_COMMIT in t for t in todo) and any(t.startswith("Deferred geometry:") for t in todo)
            and any(t.startswith("Provisional placement:") for t in todo), "approval/source/deferred labels missing: " + ident)
        require("Widths: " + json.dumps(widths, ensure_ascii=False, separators=(",", ":")) in todo, "record width note disagrees with manifest: " + ident)
        require(any("vermilion scope=" + scope + " " in t for t in todo), "record colour boundary disagrees: " + ident)
        placement = record["placement"]
        require(type(placement.get("clearance")) is int and placement["clearance"] == 0 and "per_zone" not in placement, "unallocated clearance/population policy changed")
        require(placement.get("stages") == [] and placement.get("snap") == "cell", "stage/snap policy changed")
        if record["kind"] == "structure" and suffix != "footbridge":
            require(any(r.get("rel") == "adjacent" and r.get("what") == "route" for r in placement["requires"]), "structure approach relation missing")
        if suffix in ["temple_hall", "pagoda", "temple_gate"]:
            require(any(r.get("rel") == "on" and r.get("what") == "stone_plinth" for r in placement["requires"]), "plinth relationship missing")
    return {"status": "concept_metadata_pass", "approved": False, "buildable": False, "placeable": False,
        "concepts": len(rows), "variants": variant_count, "source_buildings_covered": len(covered_buildings),
        "source_limits": manifest["source_limits"], "limits": "W0 structural metadata only; no strict runtime material/geometry, placement, rendered art or gameplay acceptance"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = check(args.root)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print("Highgarth concepts: " + str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    else:
        print(f"Highgarth concepts: {result['concepts']} concepts / {result['variants']} variants / {result['source_buildings_covered']} source building records; metadata PASS, approval/build/place FALSE")
        print("Source review limits: " + json.dumps(result["source_limits"], sort_keys=True))
        print(result["limits"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
