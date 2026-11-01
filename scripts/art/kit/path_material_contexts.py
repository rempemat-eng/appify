"""Candidate packed-earth context proof; never an art or editor acceptance gate.

Run only on a reviewed private source copy, with output outside that copy::

    python3 -I -B scripts/art/kit/path_material_contexts.py \
        --source-root /private/candidate --out /private/new-output

Two 384-pixel atlases exercise the existing native painter, the periodic editor
BODY (on the same native mask, not the Godot shader), and the actual kit bake.
The output uses existing palette/cast-shadow operations. Synthetic doorstep and
shadow controls are labelled; no prop, physics, material ID or approval is added.
All target imports and rendering are deferred to main. No subprocess is used.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import sys
import traceback

CELL = 24
GRID = 16
SIZE = CELL * GRID
PERIOD = 768
OUTPUT_CAP = 32 * 1024 * 1024
CASES = ((43, (0, 0)), (83, (744, 744)))
BODY_KEYS = ("seed", "fam", "cell", "stones", "joints", "lit", "blades", "soft_joints")
DATA = (
    "art/house-palette.json", "scripts/art/native/accents.json",
    "art/scenes/woodland.json", "scripts/art/biomes/woodland.json",
    "game/kit/props/index.json",
) + tuple("game/kit/pieces/terrain/" + name + ".json"
          for name in ("lawn", "path", "worn", "earth_face"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) > 4 * 1024 * 1024:
        raise ValueError("JSON input exceeds 4 MiB: " + str(path))
    return json.loads(data)


def limits() -> None:
    """One process; external parent custody and timeout remain necessary."""
    import resource
    import signal

    resource.setrlimit(resource.RLIMIT_CPU, (110, 115))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_CAP, OUTPUT_CAP))

    def expired(_number, _frame):
        raise TimeoutError("120-second context-proof deadline")

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(120)


def plan() -> tuple[dict, list[dict]]:
    """Small lab geometry, not a proposed town layout or physical-rule waiver."""
    rows = [["l"] * GRID for _ in range(GRID)]

    def rect(x0, y0, x1, y1, letter="p"):
        for y in range(y0, y1):
            rows[y][x0:x1] = [letter] * (x1 - x0)

    rect(1, 1, 8, 2)                 # one-cell footpath
    rect(1, 4, 8, 6)                 # two-cell lane
    rect(6, 3, 8, 7)                 # synthetic widening at a doorstep/spawn
    rect(1, 8, 8, 11)                # three-cell road
    rect(1, 12, 6, 16)               # four-cell approach
    rect(6, 12, 9, 16, "w")          # contiguous worn yard; semantics stay distinct
    rect(10, 1, 15, 3)               # bend, rounded by the existing soft-grid shape
    rect(10, 1, 12, 6)
    rect(9, 7, 16, 9)                # T, never a four-way crossing
    rect(12, 7, 14, 11)
    rect(10, 12, 12, 14)             # orthogonal-cell fork, softened into a Y
    rect(14, 12, 16, 14)
    rect(11, 13, 15, 15)
    rect(12, 14, 14, 16)
    notes = [
        {"name": "footpath", "width_cells": 1, "at": [24, 0]},
        {"name": "lane / synthetic doorstep", "width_cells": 2, "at": [24, 72]},
        {"name": "road", "width_cells": 3, "at": [24, 168]},
        {"name": "wide approach -> worn yard", "width_cells": 4, "at": [24, 264]},
        {"name": "rounded bend", "at": [240, 0]},
        {"name": "T", "at": [240, 144]},
        {"name": "Y fork", "at": [240, 264]},
    ]
    return {
        "id": "path_material_contexts", "lab": True, "ship": False,
        "legend": {"l": "lawn", "p": "path", "w": "worn"},
        "rows": ["".join(row) for row in rows],
        "variants": ["." * GRID for _ in range(GRID)],
        "pieces": [], "decor": [], "spawns": {"synthetic_doorstep": [168, 120]},
    }, notes


def library(root: Path, seed: int, origin: tuple[int, int]) -> dict:
    lib = {name: read_json(root / ("game/kit/pieces/terrain/" + name + ".json"))
           for name in ("lawn", "path", "worn", "earth_face")}
    # Rendering-only test overrides. These do not define production zone origins.
    for name in ("path", "worn"):
        for field in ("fill", "paint"):
            lib[name]["terrain"][field]["args"]["seed"] = seed
        lib[name]["terrain"]["paint"]["args"]["origin"] = list(origin)
        lib[name]["terrain"]["paint"]["args"]["period"] = PERIOD
    return lib


def native_args(entry: dict, GD) -> dict:
    args = copy.deepcopy(entry["terrain"]["paint"]["args"])
    for key in ("shape", "edge_stones", "foot_pad"):
        args.pop(key, None)
    accepted = set(inspect.signature(GD.dirt).parameters) - {"cv", "m"}
    if not set(args) <= accepted:
        raise ValueError("Unforwarded native recipe fields: " + repr(set(args) - accepted))
    return args


def sample(tile, origin, height, width, np):
    yy = (origin[1] + np.arange(height)) % tile.shape[0]
    xx = (origin[0] + np.arange(width)) % tile.shape[1]
    return tile[np.ix_(yy, xx)].copy()


def native_body(args: dict, origin, height, width, GD, PAL, np):
    # A 16-pixel apron excludes the native painter's intentional four-pixel edge crumbs.
    pad = 16
    cv = np.full((height + 2 * pad, width + 2 * pad), PAL.C("path", 3), np.int32)
    kw = dict(args, origin=(origin[0] - pad, origin[1] - pad), ruts=0)
    GD.dirt(cv, np.ones(cv.shape, bool), **kw)
    return cv[pad:pad + height, pad:pad + width].copy()


def body_checks(lib, origin, F, GD, PAL, np) -> tuple[dict, object]:
    fill = lib["path"]["terrain"]["fill"]["args"]
    args = native_args(lib["path"], GD)
    tile = F.dirt(**fill)
    expected = sample(tile, origin, 64, 96, np)
    whole = native_body(args, origin, 64, 96, GD, PAL, np)
    # Separate native invocations at adjusted origins, not a tautological slice of whole.
    left = native_body(args, origin, 64, 47, GD, PAL, np)
    right = native_body(args, (origin[0] + 47, origin[1]), 64, 49, GD, PAL, np)
    top = native_body(args, origin, 31, 96, GD, PAL, np)
    bottom = native_body(args, (origin[0], origin[1] + 31), 33, 96, GD, PAL, np)
    equal = lambda a, b: bool(np.array_equal(a, b))
    checks = {
        "native_body_equals_periodic_fill": equal(whole, expected),
        "separate_native_x_fragments_equal_whole": equal(np.concatenate((left, right), 1), whole),
        "separate_native_y_fragments_equal_whole": equal(np.concatenate((top, bottom), 0), whole),
        "path_worn_fill_recipe_equal": lib["path"]["terrain"]["fill"] == lib["worn"]["terrain"]["fill"],
        "path_worn_native_body_recipe_equal": all(
            lib["path"]["terrain"]["paint"]["args"].get(k) ==
            lib["worn"]["terrain"]["paint"]["args"].get(k) for k in BODY_KEYS + ("origin", "period")),
        "body_dtype_int32": str(tile.dtype) == "int32",
        "period_768": list(tile.shape) == [PERIOD, PERIOD],
    }
    return {"checks": checks, "wrapped_edge_ratio_diagnostic": F.seam_error(tile),
            "body_sha256": digest(np.asarray(tile, dtype="<i4").tobytes()),
            "probe_art_px": [96, 64], "native_apron_art_px": 16,
            "native_edge_rut_variant_overlays_excluded_from_pixel_parity": True}, tile


def body_context(p, lib, tile, periodic, B, GD, PAL, np):
    mat = np.array([[p["legend"][c] for c in row] for row in p["rows"]])
    cv = GD.lawn(SIZE, SIZE, lib["lawn"]["terrain"]["paint"]["args"]["seed"])
    net = np.zeros((SIZE, SIZE), bool)
    for name in ("path", "worn"):
        shape = lib[name]["terrain"]["paint"]["args"].get("shape", {})
        net |= B._shape(mat == name, SIZE, SIZE, shape)
    args = native_args(lib["path"], GD)
    if periodic:
        cv[net] = sample(tile, args["origin"], SIZE, SIZE, np)[net]
    else:
        GD.dirt(cv, net, **args)
    turf = (PAL.is_fam(cv, "grass") | PAL.is_fam(cv, "leaf")) & ~net
    GD.sunken_edge(cv, net, turf, np.random.default_rng(args["seed"] + 2))
    return cv, net


def cast_control(codes, net, CO, PAL, np, ndi):
    # Deliberately synthetic shade strips cross the SAME underlying material on every width.
    shade = np.zeros(codes.shape, bool)
    shade[:, 96:144] = True
    shade[:, 288:336] = True
    ground = CO.ground_from_codes(codes, 3.0)
    CO.cast_shadows(ground, [shade], [], [], 3.0)
    after = ground.fam.astype(np.int32) * 8 + ground.tone
    zone = ndi.binary_erosion(net & shade, iterations=6)
    return ground.rgba(), {
        "operation": "native.compose.cast_shadows, density3, synthetic masks; no house/tree",
        "path_sample_pixels": int(zone.sum()),
        "palette_codes_before": int(np.unique(codes[zone]).size),
        "palette_codes_after": int(np.unique(after[zone]).size),
        "shade_pixels_changed": int(np.count_nonzero(codes[zone] != after[zone])),
        "detail_quality": "VISUAL_REVIEW_REQUIRED; counts are diagnostics, not a detail score",
    }


def source_inventory(root: Path) -> dict:
    paths = {root / path for path in DATA}
    paths.add(Path(__file__).resolve())
    for module in tuple(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if path:
            p = Path(path).resolve()
            if p.is_relative_to(root) and p.suffix == ".py":
                paths.add(p)
    result = {}
    for path in sorted(paths):
        data = path.read_bytes()
        name = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        result[name] = {"bytes": len(data), "sha256": digest(data)}
    return result


def render(root: Path, out: Path, report: dict) -> None:
    import numpy as np
    import scipy
    from scipy import ndimage as ndi
    from PIL import Image, ImageDraw, __version__ as pillow_version
    # build configures density/biome before native modules capture context globals.
    from scripts.art.kit import build as _build  # noqa: F401
    from scripts.art.kit import bake, fills
    from scripts.art.native import ctx, softground as GD, compose as CO, palette as PAL, screen as SN

    if ctx.D != 3.0 or bake.CELL != CELL or fills.PERIOD != PERIOD:
        raise ValueError("Unexpected density/cell/period; do not rescale the texture to make it fit")
    report["versions"] = {"python": platform.python_version(), "numpy": np.__version__,
                          "scipy": scipy.__version__, "pillow": pillow_version}
    p, notes = plan()
    report["plan"] = p
    report["contexts"] = notes
    report["cases"] = []
    columns = ("Native body + native edge", "Periodic editor BODY + native edge", "Actual kit bake + cast control")
    row_height = SIZE + 78
    sheet = Image.new("RGBA", (SIZE * 3, row_height * len(CASES) + 50), "#f8edd7")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "CANDIDATE / visual review required / 24 art px per cell / grain scale fixed", fill="#202020")
    for index, (seed, origin) in enumerate(CASES):
        lib = library(root, seed, origin)
        case = {"seed": seed, "render_origin_art_texels_xy": list(origin),
                "origin_is_not_a_production_zone_contract": True,
                "approvals": {k: lib[k]["approval"] for k in ("path", "worn")},
                "recipes": {k: lib[k]["terrain"] for k in ("path", "worn")}, "routes": {}}
        report["cases"].append(case)
        case["body"], tile = body_checks(lib, origin, fills, GD, PAL, np)
        native, net = body_context(p, lib, tile, False, bake, GD, PAL, np)
        periodic, _ = body_context(p, lib, tile, True, bake, GD, PAL, np)
        baked, _ = bake.bake(copy.deepcopy(p), lib=copy.deepcopy(lib))
        baked_codes = SN.to_codes(baked)
        case["baked_palette_roundtrip_exact"] = bool(np.array_equal(PAL.to_rgba(baked_codes), np.asarray(baked)))
        for col, (title, codes) in enumerate(zip(columns, (native, periodic, baked_codes))):
            image, metrics = cast_control(codes, net, CO, PAL, np, ndi)
            y = 50 + index * row_height
            x = col * SIZE
            draw.text((x + 6, y), title, fill="#202020")
            draw.text((x + 6, y + 14), "seed %d; art-origin %s" % (seed, origin), fill="#202020")
            sheet.alpha_composite(image, (x, y + 32))
            for note in notes:
                at = note["at"]
                draw.text((x + at[0], y + 33 + at[1]), note["name"], fill="#fff2d0", stroke_width=1,
                          stroke_fill="#322b22")
            draw.text((x + 6, y + SIZE + 36), "Shade strips: existing cast operation; no placed prop", fill="#202020")
            draw.text((x + 6, y + SIZE + 50), "T/Y controls only; final layout/physics NOT accepted", fill="#202020")
            case["routes"][title] = {"unshaded_codes_sha256": digest(np.asarray(codes, dtype="<i4").tobytes()),
                                   "rgba_sha256": digest(image.tobytes()), "shade": metrics}
    report["inputs_after_render"] = source_inventory(root)
    report["checks"] = {
        "body_and_phase_checks": all(all(c["body"]["checks"].values()) for c in report["cases"]),
        "baked_palette_roundtrips": all(c["baked_palette_roundtrip_exact"] for c in report["cases"]),
        "candidate_metadata_retained": all(
            c["recipes"][n]["material_id"] == mid and c["recipes"][n]["walkable"] is True
            and c["recipes"][n]["route"] is route
            and c["approvals"][n]["state"] == "candidate"
            for c in report["cases"] for n, mid, route in (("path", 2, True), ("worn", 6, False))),
    }
    report["outputs"] = {}
    for name, image in (("path-material-contexts-1x.png", sheet),
                        ("path-material-contexts-2x.png", sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST))):
        with (out / name).open("xb") as stream:
            image.save(stream, format="PNG")
        data = (out / name).read_bytes()
        report["outputs"][name] = {"bytes": len(data), "sha256": digest(data), "size": list(image.size)}
    if sum(v["bytes"] for v in report["outputs"].values()) > OUTPUT_CAP:
        raise ValueError("Aggregate image outputs exceed 32 MiB")
    report["machine_state"] = "CHECKS_COMPLETED" if all(report["checks"].values()) else "CHECKS_FAILED"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root, out = args.source_root.resolve(), args.out.resolve()
    if out == root or out.is_relative_to(root):
        parser.error("Output must be a new directory outside the reviewed source copy")
    if not root.is_dir():
        parser.error("Missing source root")
    out.mkdir(parents=True, exist_ok=False)
    report = {"kind": "candidate-path-material-context-proof", "machine_state": "STARTED",
              "visual_state": "NOT_REVIEWED", "editor_authoring": "NOT_RUN",
              "approval": "NOT_GRANTED", "source_root": str(root),
              "limits": {"cpu_soft_s": 110, "wall_alarm_s": 120, "address_space_bytes": 2 * 1024 ** 3,
                         "aggregate_image_bytes": OUTPUT_CAP, "processes": 1},
              "limitations": ["No Godot, save/reopen, device, gameplay or world-layout proof.",
                              "Periodic column tests the editor material body, not the shader/transition atlas.",
                              "Native/fill pixel parity excludes ruts, variants and intentional edge dressing.",
                              "Origins are art-texel render overrides, not production zone coordinates.",
                              "Synthetic doorway and shade controls are not approved placed props.",
                              "No X junction is generated or accepted; T/Y are review contexts.",
                              "No Eastward reference or matched character sprite is included."]}
    try:
        limits()
        sys.dont_write_bytecode = True
        for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[key] = "1"
        sys.path.insert(0, str(root))
        render(root, out, report)
    except Exception as error:
        report.update(machine_state="FAILED", error_type=type(error).__name__, error=str(error),
                      traceback=traceback.format_exc())
    with (out / "path-material-contexts.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"machine_state": report["machine_state"], "report": str(out / "path-material-contexts.json"),
                      "visual_state": "NOT_REVIEWED", "editor_authoring": "NOT_RUN"}))
    return 0 if report["machine_state"] == "CHECKS_COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
