"""Draw four unapproved Crossroads cottages with the existing native town renderer.

This opt-in diagnostic never changes the playable Crossroads plan or the library.
Run only in a separately allocated private checkout with the fixture's frozen
input closure and dependency versions. The enclosing receiver owns CPU, time,
RSS, process collection and durable evidence. Importing this module draws nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import stat
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "scripts/review/fixtures/crossroads_halt_court.json"
SOURCE = "45f2c80b657169ef4d7445bc9ff5ddd153960707"
SOURCE_TREE = "7e7561eac9b7a9f15e54ff62b169dd7cf500bad5"
SOURCE_BASELINE = "feb37c31d6de71e20df096df4df4d32ed1fa93ed"
LAYOUT = "7bf6b026a21e7996a367d6ae9b5862b3344bdd56"
LAYOUT_BLOB = "2c2c5474f2154ba1430549823a908996261572c8"
IDS = ("crossroads-b029", "crossroads-b038", "crossroads-b039", "crossroads-b040")
FLOORS = ([6000, 4080, 64, 72], [5864, 4048, 64, 48],
          [5864, 4184, 64, 48], [6056, 4192, 64, 40])


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inputs_snapshot(fixture: dict) -> dict:
    """Hash the declared conservative closure; no imports or inferred substitutions."""
    result = {}
    entries = fixture["source_input_closure"]["files"]
    if len(entries) != 112 or len({e["path"] for e in entries}) != 112:
        raise ValueError("Exact112-file source closure required")
    for entry in entries:
        path = ROOT / entry["path"]
        if not path.resolve(strict=True).is_relative_to(ROOT):
            raise ValueError("Input escaped private source checkout")
        before = path.lstat()
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or before.st_size != entry["bytes"]
                or stat.S_IMODE(before.st_mode) != int(entry["mode"][-3:], 8)):
            raise ValueError("Source input identity/size/mode differs: " + entry["path"])
        data = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        after = path.lstat()
        fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")
        if (blob != entry["blob"] or any(getattr(before, k) != getattr(after, k) for k in fields)):
            raise ValueError("Source bytes changed: " + entry["path"])
        result[entry["path"]] = {"bytes": len(data), "sha256": digest(data), "blob": blob}
    return result


def plan_from_fixture(fixture: dict) -> dict:
    if (fixture["source_native_commit"] != SOURCE or fixture["source_native_tree"] != SOURCE_TREE
            or fixture["source_native_baseline"]["commit"] != SOURCE_BASELINE
            or fixture["source_layout_commit"] != LAYOUT or fixture["source_layout_json_blob"] != LAYOUT_BLOB
            or fixture["source_layout_overlay_key"] != "native_visible_approaches_r4"
            or fixture["world_box"] != [5824, 3968, 320, 336]
            or fixture["native_box"] != [0, 0, 320, 336] or fixture["density"] != 3):
        raise ValueError("Frozen source/layout/coordinate contract differs")
    origin = fixture["world_box"][:2]
    if tuple(r["source_id"] for r in fixture["records"]) != IDS:
        raise ValueError("Exactly the four named cottage records required; no unresolvedG01")
    buildings, looks = [], {}
    for record, floor in zip(fixture["records"], FLOORS):
        x, y, w, h = floor
        expected_local = [x - origin[0], y - origin[1], w, h]
        foot = [x + w // 2 - origin[0], y + h - origin[1]]
        look = record["look"]
        if (record["world_floor"] != floor or record["local_floor"] != expected_local
                or record["local_door"] != foot or record["foot_art"] != [v * 3 for v in foot]
                or record["world_threshold"] != [x + w // 2, y + h]
                or record["collision_world"] != [-32, -h, 64, h]
                or record["expected_canvas"] != [216, 312] or record["expected_anchor"] != [108, 308]
                or record["door_cells"] != [[0, 0]] or record["variant_id"] != "south"):
            raise ValueError("Cottage geometry/threshold identity differs")
        expected_footprint = [[col, row] for row in range(-h // 8, 0) for col in range(-4, 4)]
        if record["footprint"] != expected_footprint:
            raise ValueError("Conservative physical footprint differs")
        wanted = {"w":64, "depth":h, "kind":"cottage", "roof":"slate", "wall_h":44,
                  "roof_h":40, "chimney_h":14, "door":32, "door_h":32, "door_w":14, "overhang":3}
        if any(look.get(k) != v for k, v in wanted.items()) or len(look.get("chimney", [])) != 1:
            raise ValueError("Supported physical south-cottage form differs")
        buildings.append({"id":record["native_piece_id"], "name":record["plot"] + " candidate cottage",
                          "rect":expected_local, "door":foot})
        looks[record["native_piece_id"]] = look
    routes = []
    for entry in fixture["routes"]:
        if entry["local_points"] != [[x-origin[0], y-origin[1]] for x, y in entry["world_points"]]:
            raise ValueError("Route source-to-local transform differs")
        routes.append({"id":entry["source_name"], "kind":entry["kind"],
                       "width":entry["width"], "points":entry["local_points"]})
    return {"id":"crossroads_halt_court", "box":fixture["native_box"],
            "origin_on_canvas":origin, "buildings":buildings, "routes":routes,
            "stages":[{"id":"candidate", "why":"Private unapproved native-parts diagnostic only"}],
            "art":{"biome":"meadow", "looks":looks},
            "_diagnostic_only":True, "_terrain":"UNMEASURED against actual continent", "_inputs":None}


def piece_metadata(record: dict, png_size: tuple, anchor: list) -> dict:
    """Small four-record binding adapter; never seed()/--force or a global index."""
    pid = record["native_piece_id"]
    return {"schema":"napattack.piece/1", "id":pid, "name":record["plot"] + " cottage candidate",
            "kind":"structure", "biomes":["village"], "version":1,
            "variants":[{"id":"south", "weight":1, "png":"res://zones/crossroads_halt_court/art/"+pid+".png", "foot":anchor}],
            "approval":{"state":"candidate", "by":None, "at":None, "standard":None,
                         "note":"Private diagnostic; no KEEP, library, Y12, terrain, interior or Matt approval."},
            "geometry":{"size_px":list(png_size), "size_cells":[9,13], "foot":anchor, "z_sort":"foot",
                        "collision":{"shape":"rect", "rect":record["collision_world"]},
                        "footprint":record["footprint"], "door_cells":[[0,0]]},
            "placement":{"snap":"cell"}, "rendering":{"cast_shadow":{"shape":"baked"}, "contact_ao":True},
            "function":{}, "story":{"owner":None}, "gameplay":{"blocks_move":True,"blocks_shots":True},
            "audit":{"size_class":"cottage", "eastward_ref":None,
                     "seeded_from":"scripts/review/fixtures/crossroads_halt_court.json",
                     "todo":["Actual world terrain/grade/route checks", "Placement relations and shadow reuse outside this diagnostic",
                             "Matched reference/detail/Y12 and Matt approval", "Door marker is not a working interior"]}}


def draw(output: Path) -> int:
    output = output.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        raise ValueError("Fresh output outside the source checkout required; no production writes")
    fixture_bytes = FIXTURE.read_bytes()
    entrypoint_bytes = Path(__file__).read_bytes()
    fixture = json.loads(fixture_bytes)
    plan = plan_from_fixture(fixture)
    before = inputs_snapshot(fixture)
    output.mkdir(parents=True, mode=0o700)
    result = {"state":"INCOMPLETE", "native_source":SOURCE, "native_source_tree":SOURCE_TREE,
              "native_baseline":SOURCE_BASELINE, "layout_source":LAYOUT,
              "fixture_sha256":digest(fixture_bytes), "terrain":"UNMEASURED",
              "entrypoint_sha256":digest(entrypoint_bytes), "approved":False,
              "planned_constructor_calls":{"HD_cottages":4,"legacy_cottage_silhouettes":4},
              "native_town_invocations_started":0,
              "constructor_call_measurement":"Not instrumented; planned counts are not actual execution evidence."}
    failure = None
    try:
        # Only a later allocated invocation reaches these imports. Configure density
        # BEFORE importing village/town/houses; no shared module or ROOT monkeypatch.
        if platform.python_version_tuple()[:2] != ("3", "12"):
            raise RuntimeError("Pinned CPython3.12 required")
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from PIL import Image
        import PIL
        import numpy
        import scipy
        versions = {"Pillow":PIL.__version__, "numpy":numpy.__version__, "scipy":scipy.__version__}
        if versions != {"Pillow":"12.3.0", "numpy":"2.5.3", "scipy":"1.18.1"}:
            raise RuntimeError("Pinned native drawing dependencies required; no acquisition/fallback here")
        from scripts.art.native import ctx, load_biome, load_plan
        ctx.configure(3.0, load_biome("meadow"), load_plan("pilot"))
        from scripts.art.native import town
        plan["_inputs"] = digest(json.dumps({
            "source_inputs":before, "fixture_sha256":digest(fixture_bytes),
            "entrypoint_sha256":digest(entrypoint_bytes),
        }, sort_keys=True).encode())
        write_json(output / "plan.json", plan)
        art = output / "game/zones/crossroads_halt_court/art"
        previews = output / "presentation"
        # ONE small native town render, four HD bodies plus its unchanged four
        # legacy-only lawn/shadow silhouettes. No current Crossroads/world build.
        result["native_town_invocations_started"] = 1
        result["native_result"] = town.build(plan, str(art), str(previews))
        kit = json.loads((art.parent / "kit.json").read_text())
        objects = {obj["id"]:obj for obj in kit["objects"]}
        if set(objects) != {r["native_piece_id"] for r in fixture["records"]}:
            raise RuntimeError("Only four independent static building bodies expected")
        measured = {}
        for record in fixture["records"]:
            pid = record["native_piece_id"]
            obj = objects[pid]
            if (obj["foot"] != record["foot_art"] or obj["solid"] != record["local_floor"]
                    or obj["offset"] != [-108,-308] or obj["cond"] is not None):
                raise RuntimeError("Actual native anchor/floor contract differs: "+pid)
            png = art / (pid+".png")
            with Image.open(png) as picture:
                picture.load()
                bbox = picture.getchannel("A").getbbox()
                if picture.mode != "RGBA" or list(picture.size) != [216,312] or not bbox:
                    raise RuntimeError("Actual native canvas/alpha contract differs: "+pid)
                width, height = bbox[2]-bbox[0], bbox[3]-bbox[1]
                if not (192 <= width <= 340 and 200 <= height <= 340):
                    raise RuntimeError("Opaque size gate refused; no padding credit: "+pid)
                # Retain actual pixels around the expected32×14 world-pixel door
                # for visual review. An opaque rectangle is NOT a door-quality score.
                picture.crop((84,209,132,312)).save(previews / (pid+"-door.png"))
                piece = piece_metadata(record, picture.size, record["expected_anchor"])
            write_json(output / "game/kit/pieces/structure" / (pid+".json"), piece)
            measured[pid] = {"canvas":[216,312], "foot":[108,308], "alpha_bbox":list(bbox),
                             "opaque_width":width, "opaque_height":height, "png_sha256":digest(png.read_bytes()),
                             "door_expected_rect_art":[87,212,42,96], "door_visual_review":"PENDING"}
        native = previews / "crossroads_halt_court_candidate.png"
        with Image.open(native) as image:
            image.load()
            if list(image.size) != [960,1008]:
                raise RuntimeError("Native diagnostic extent differs")
            image.resize((1920,2016), Image.Resampling.NEAREST).save(previews / "crossroads-halt-court-2x.png")
        result.update(state="NATIVE_CANDIDATE_COMPLETE_NOT_APPROVED", measured=measured, versions=versions,
                      completed_native_body_outputs=len(measured), remaining_limits=fixture["limits"],
                      input_files=len(before), source_inputs=before)
    except BaseException as error:
        failure = error
        result.update(state="FAILED_OR_INCOMPLETE", error_type=type(error).__name__, error=str(error),
                      error_traceback=traceback.format_exc())
    finally:
        try:
            if (inputs_snapshot(fixture) != before or FIXTURE.read_bytes() != fixture_bytes
                    or Path(__file__).read_bytes() != entrypoint_bytes):
                raise RuntimeError("Source/fixture bytes changed during native drawing")
            result["source_guard"] = "PASS"
        except BaseException as error:
            result.update(state="FAILED_OR_INCOMPLETE", source_guard="FAIL", source_error=str(error),
                          source_error_traceback=traceback.format_exc())
            if failure is None:
                failure = error
        files = {}
        for path in output.rglob("*"):
            if path.is_file():
                files[str(path.relative_to(output))] = {"bytes":path.stat().st_size,"sha256":digest(path.read_bytes())}
        if sum(v["bytes"] for v in files.values()) > 16*1024**2:
            result.update(state="FAILED_OR_INCOMPLETE", output_bound="16MiB exceeded")
            failure = failure or RuntimeError("Private output bound exceeded")
        result["files_before_terminal_receipt"] = files
        receipt_path = output / "native-result.json"
        receipt_bytes = (json.dumps(result, indent=2) + "\n").encode()
        total = sum(v["bytes"] for v in files.values()) + len(receipt_bytes)
        if total > 16*1024**2:
            result.update(state="FAILED_OR_INCOMPLETE", output_bound="16MiB including terminal receipt exceeded")
            failure = failure or RuntimeError("Private terminal output bound exceeded")
        write_json(receipt_path, result)
    return 1 if failure is not None else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return draw(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
