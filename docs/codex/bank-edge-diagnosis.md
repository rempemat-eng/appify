# Bank-edge diagnosis: width lab and woodland

Status: **engineering diagnosis; no art approval or source repair**. Y29/r1 follows [brief6486454819](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6486454819), [GO6493960807](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6493960807) and [ASSIGN6493995850](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6493995850).

The original seven-tooth and five-tooth failures reproduce exactly. Their displayed 3/4 px risers are averages of **grouped consecutive changes**, rather than seven/five separate adjacent 3/4 px jumps. The inferred mask also excludes a real light-water palette colour. Neither failure alone establishes repeated large geometric steps in the painter's authoritative outline. Preserve both original raw faults; this report does not turn either into a pass.

## Pinned cases and coordinates

The subject is frozen editor [#364](https://github.com/rempemat-eng/appify/pull/364) at `6d309ea3a0bddd38990abecce22419b85ad28d2a`, tree `e34dedaa6057c32145d8b5a43758c125f91370af`. The report branch starts independently from main `0940f0c76f51a4859344a32594d65fc03043bf7c`; it imports none of that editor's ancestry or art. [Review5691820654](https://github.com/rempemat-eng/appify/pull/357#pullrequestreview-5691820654) supplies the unresolved cases. Original JSON reports are pinned to #344 `bc9672a5a63dc15dede557b45e922c8412bb3a1c`, tree `82a8a9af246a35c05d6efe4bf3786b07710ef43f`.

| Existing native PNG                         | Size       | Original report box, half-open | Original result                            |
| ------------------------------------------- | ---------- | ------------------------------ | ------------------------------------------ |
| `game/zones/kitlab_widths/ground_baked.png` | 960 × 552  | `[280,77,315,147]`             | 7 teeth, rounded 3 px risers / 2 px treads |
| `game/zones/woodland_kit/ground_baked.png`  | 960 × 1728 | `[293,853,321,942]`            | 5 teeth, rounded 4 px risers / 2 px treads |

PNG SHA256s are respectively `fa8081e501f235bde1622c948d87ddadcb49156f21e0a2eb74c10ab616a59489` and `5d92199546fa0cc79e3ec5e2bfe772fc18c9aabcd21eb098295e50507bc2cbaf`. They exactly match the original reports and frozen #364 bytes.

There is **no crop, resampling or translation** in these asset-bank checks. `assets.review_rgba` passes the native RGBA straight to `screen.review_screen`, which calls `water.check_banks`. `box_source` equals `box`. Bake uses `CELL=24`; each plan cell is 24 × 24 native art pixels at its configured density 3. The canvases are `rows × CELL` by `columns × CELL`, and `Ground.rgba` keeps that size. These legacy evidence inputs retain H=74/density3; diagnosing them does not adopt that density over the written new-art standard.

## Authoritative outline and inferred boundary

For each water material, `bake.py:268–276` computes:

```python
wcells = mat == material_id
wcls = surface.water_class(surface.widths(wcells))
wm |= surface.taper(_shape(wcells, h, w, args["shape"]), wcells, wcls)
```

`_shape` calls `softgrid.shape` with the pinned water parameters: seed402, outer radius1.3, inner radius0.6, amplitude `[2.5,5.0]`, lump lengths `[10,26]`, plus the source narrow-channel treatment. `surface.taper` smooths only around width-class transitions, with its unchanged sigma9/threshold0.5. The analysis executes these unchanged numeric function definitions, not `bake()`, `write()`, `build` or a painter.

`wm` is the authoritative **whole water/bank footprint**, not a saved final visible-water material mask. `softground.water` carves the north bank face inside it, makes side walls, draws a waterline and adds overhanging turf and props; `tidy_bank` edits palette codes without changing `wm`. Narrow and wide render passes can also differ. Consequently, disagreement between `wm` and visible blue pixels is expected and does not by itself make the detector wrong or the painter defective.

The review mask instead uses RGB HSV selection (hue185–235°, saturation≥.32, value≥.25), one binary closing, then hole filling. `_profiles` keeps columns/rows with a single uninterrupted run. `_stairs` merges **consecutive same-sign nonzero adjacent changes**, including sequences of 1 px chamfer changes, into one synthetic riser before judging repetition. Report boxes cover the entire water-component stretch, not just the particular contour point that moves.

## Measured comparison

All measurements below are from the unchanged PNGs and unchanged numeric definitions. “Palette proxy” means equality to the pinned water/warm/cool RGB ramps; it is a diagnostic comparison, **not recovered final painter material provenance**. Palette colours can be overpainted or reused; no inferred RGB mask supersedes `wm`.

| Measurement inside the original report box | Width lab | Woodland |
| ------------------------------------------ | --------: | -------: |
| Inferred water pixels outside `wm`         |         0 |        0 |
| `wm` pixels excluded from inferred water   |       308 |      269 |
| Pixels added by closing                    |         2 |        7 |
| Pixels removed by closing                  |         0 |        0 |
| Pixels added by hole filling               |         0 |        0 |
| Raw HSV pixels outside palette proxy       |         0 |        0 |
| Palette water pixels excluded by raw HSV   |        29 |       29 |

All 29 excluded palette pixels in each box have RGB `(146,184,197)`: the unique pinned `water` tone5, H≈195.294°, S≈.258883, V≈.772549. The saturation cutoff omits this actual light-water colour. This explains a concrete mask mismatch; it does not authorize a threshold change or establish the preferred detector treatment of highlights, foam or occlusion.

| Boundary test              | Width lab                                                            | Woodland                                                      |
| -------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------- |
| Existing inferred mask     | 7 teeth; mean rise3.428571, tread2.166667; exact original box        | 5 teeth; mean rise4.2, tread2.25; exact original box          |
| Raw HSV, before closing    | 8 teeth; mean rise3, tread2.142857; same box                         | 4 teeth; mean rise4.25, tread2.333333; `[298,856,321,942]`    |
| Palette proxy              | 6 teeth; mean rise3.333333, tread2; `[280,77,307,143]`               | No staircase finding                                          |
| Authoritative tapered `wm` | Related 5-tooth aggregate at `[278,68,302,141]`, mean rise2.6/tread2 | No corresponding northern/western finding in the original box |
| Untapered `_shape`         | No staircase finding                                                 | No corresponding northern/western finding in the original box |

The width-lab `wm` comparison shows that tapering changes the outline and can trigger this aggregation rule. Its reported aggregate is not five literal 3 px jumps. Woodland has two other source-mask findings at `[457,854,480,941]` and `[625,862,648,942]`; they are outside the assigned case and are not newly accepted defects or assigned repairs.

For the original width-lab case, the detector follows the **southern** edge (`axis=1`, `hi`, where the edge value is the first excluded row), x282–312 inclusive. Adjacent differences in the inferred contour are 21 × 1 px, 8 × 0, and one 4 px jump; the corresponding `wm` contour is 19 × 1 px and 11 × 0, with maximum adjacent step1. For woodland, the detector follows the **northern** edge (`axis=1`, `lo`), x295–318 inclusive: 14 × 1 px, 2 × 2 px, 6 × 0 and one 4 px jump. Corresponding `wm`: 19 × 1 px, 3 × 0 and one 3 px jump. The larger isolated jumps and bank/palette transitions remain evidence to inspect; a list of many separate 3/4 px teeth is not present.

Exact edge values, in increasing x order, make that distinction inspectable without private masks:

**kitlab_widths**

```text
shape: [123, 124, 125, 127, 128, 130, 131, 132, 134, 135, 136, 136, 136, 137, 137, 138, 138, 139, 139, 140, 141, 142, 142, 143, 144, 144, 144, 145, 145, 145, 145]
wm: [126, 127, 128, 128, 129, 130, 131, 131, 132, 133, 134, 135, 135, 136, 137, 137, 138, 139, 139, 140, 140, 141, 141, 142, 142, 142, 143, 143, 143, 144, 145]
palette_water: [120, 121, 121, 122, 123, 123, 124, 126, 126, 127, 128, 128, 129, 130, 131, 131, 132, 133, 134, 135, 135, 136, 141, 137, 142, 142, 143, 143, 143, 144, 145]
raw_hsv: [120, 121, 121, 122, 123, 123, 124, 125, 126, 126, 127, 128, 128, 129, 130, 131, 131, 132, 133, 134, 135, 135, 136, 137, 137, 142, 143, 143, 143, 144, 145]
inferred: [120, 121, 121, 122, 123, 123, 124, 125, 126, 126, 127, 128, 128, 129, 130, 131, 131, 132, 133, 134, 135, 135, 136, 137, 138, 142, 143, 143, 143, 144, 145]
```

**woodland_kit**

```text
shape: [842, 842, 843, 844, 845, 846, 847, 848, 850, 851, 851, 852, 854, 855, 856, 858, 859, 861, 862, 863, 864, 864, 865, 866]
wm: [844, 845, 845, 846, 847, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 861, 862, 863, 864, 864, 865, 866]
palette_water: [855, 855, 855, 856, 857, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 872, 873, 874, 874, 874, 875, 876]
raw_hsv: [null, 856, null, null, null, null, 860, 860, 861, 862, 863, 863, 865, 866, 866, 867, 869, 873, 874, 875, 875, 875, 876, 877]
inferred: [855, 856, 856, 857, 858, 858, 859, 860, 861, 862, 863, 863, 865, 866, 866, 867, 869, 873, 874, 875, 875, 875, 876, 877]
```

`null` means the raw mask's column was not one uninterrupted run; it is not missing source data. Closing repairs such breaks and changes the woodland count. This and the RGB selection explain why a reported contour is not interchangeable with the source footprint.

## Disposition and smallest follow-up

Both original `logic.water_staircase` statuses remain **FAIL**, unchanged. Source-mask comparison resolves the previous uncertainty about provenance and measurement: the counts are aggregates on an inferred visible-water contour; they do not establish seven/five repeated physical 3/4 px bank steps. The data supports investigating detector grouping/applicability before altering art. It does **not** establish an error-free bank, a correct final image, a new PASS, or conformity with the Eastward references.

Two separate, bounded follow-ups are sufficient; neither is assigned by this report:

1. An engineering owner can add source-pinned controls distinguishing permitted 1 px chamfers from genuinely repeated multi-pixel risers, and review `_stairs` grouping plus the documented light-water/occlusion contract. Preserve existing thresholds until a separately reviewed semantic correction is established; no blanket exemption for water or curves.
2. Before choosing a painter fix, collect exact final palette-code/material masks at the water-pass stages (including narrow/wide selection, side faces, tidy-bank and final composition) for these same two pinned plans. Compare against the existing PNGs and inspect the isolated width x306→307 and woodland x311→312 jumps. This requires an explicit future external bake/evidence allocation. `wm` alone cannot identify which later drawing operation created every visible boundary pixel. The minimum source owner, if a real physical defect is confirmed, remains the relevant mask/bank step in `bake._shape`/`surface.taper`/`softground.water`/`tidy_bank`; never edit PNGs directly.

Current composed/editor evidence, official Eastward comparison, other raw faults and Matt's PR-specific art/editor approval remain separate. No new game rule, map geometry, material palette or art direction is proposed.

## Reproduce the bounded analysis

Use a genuine checkout at the exact frozen #364 commit above, with Python3.12.14, NumPy2.3.5, SciPy1.17.0 and Pillow12.3.0 (the observed versions). Save this block outside the checkout as `/tmp/mygame-bank-mask.py`, then run `PYTHONDONTWRITEBYTECODE=1 python3 /tmp/mygame-bank-mask.py /absolute/path/to/frozen-checkout`. It reads pinned source/PNG inputs and prints JSON only. It does not import/call the bake/build entrypoints, paint or render anything, save an image, change thresholds or write into the checkout.

```python
from __future__ import annotations
import ast, hashlib, json, pathlib, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src = pathlib.Path(sys.argv[1]).resolve()
head = subprocess.check_output(["git", "-C", str(src), "rev-parse", "HEAD"], text=True).strip()
assert head == "6d309ea3a0bddd38990abecce22419b85ad28d2a"
sys.path.insert(0, str(src))
from scripts.art.native import ctx, load_biome
ctx.configure(3.0, load_biome("woodland"), json.loads((src / "art/scenes/woodland.json").read_text()))
from scripts.art.native import softgrid as SG, palette as PAL
from scripts.review import water as W
from scripts.review.core import regions, water_mask

# Only copy unchanged function ASTs into a numeric namespace; never import/call bake or build.
ns = dict(np=np, ndi=ndi, SG=SG, CELL=24)
for file, names in [("scripts/art/kit/surface.py", {"widths", "water_class", "texels", "taper"}),
                    ("scripts/art/kit/bake.py", {"_shape"})]:
    tree = ast.parse((src / file).read_text())
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(tree, str(src / file), "exec"), ns)

cases = [
    ("kitlab_widths", [280, 77, 315, 147], 282, 312, "hi",
     "fa8081e501f235bde1622c948d87ddadcb49156f21e0a2eb74c10ab616a59489"),
    ("woodland_kit", [293, 853, 321, 942], 295, 318, "lo",
     "5d92199546fa0cc79e3ec5e2bfe772fc18c9aabcd21eb098295e50507bc2cbaf"),
]
args = json.loads((src / "game/kit/pieces/terrain/water.json").read_text())["terrain"]["paint"]["args"]
for zone, box, t0, t1, edge, expected_png in cases:
    plan = json.loads((src / f"game/kit/zones/{zone}.json").read_text())
    png = src / f"game/zones/{zone}/ground_baked.png"
    assert hashlib.sha256(png.read_bytes()).hexdigest() == expected_png
    rgb = np.asarray(Image.open(png).convert("RGB"))
    cells = np.array([[plan["legend"].get(c, "") for c in row] for row in plan["rows"]]) == "water"
    h, w = np.array(cells.shape) * 24
    cls = ns["water_class"](ns["widths"](cells))
    shape = ns["_shape"](cells, int(h), int(w), args["shape"])
    wm = ns["taper"](shape, cells, cls)
    assert wm.shape == rgb.shape[:2]
    raw = water_mask(rgb)
    closed = ndi.binary_closing(raw, iterations=1)
    inferred = W._water(rgb)
    colors = {PAL.rgb(f, t) for f in ("water", "water_warm", "water_cool") for t in range(7)}
    palette = np.zeros(wm.shape, bool)
    for color in colors:
        palette |= np.all(rgb == color, axis=2)
    x0, y0, x1, y1 = box
    roi = np.s_[y0:y1, x0:x1]
    result = dict(zone=zone, existing_check_banks=[f.to_json() for f in W.check_banks(rgb, 74)], masks={})
    for name, mask in dict(shape=shape, wm=wm, palette_water=palette,
                           raw_hsv=raw, closed_hsv=closed, inferred=inferred).items():
        lab, regs = regions(mask, min_area=int(.15 * 74 * 74))
        lid, _, _ = max(regs, key=lambda r: int((lab[roi] == r[0]).sum()))
        axis, t, lo, hi = W._profiles(lab == lid)[1]  # along columns: t=x; edge=y
        e = lo if edge == "lo" else hi
        q = (t >= t0) & (t <= t1)
        values = e[q]
        diffs = np.diff(values)
        unique, counts = np.unique(diffs[np.isfinite(diffs)], return_counts=True)
        result["masks"][name] = dict(raw_bool_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),
            profile=[None if np.isnan(v) else int(v) for v in values],
            adjacent_differences={str(int(a)): int(b) for a, b in zip(unique, counts)},
            stairs=[list(s) for s in W._stairs(t, e, 74)])
    result["roi"] = dict(hsv_outside_wm=int((inferred & ~wm)[roi].sum()),
        wm_not_hsv=int((wm & ~inferred)[roi].sum()), closing_added=int((closed & ~raw)[roi].sum()),
        closing_removed=int((raw & ~closed)[roi].sum()), filling_added=int((inferred & ~closed)[roi].sum()),
        raw_hsv_not_palette=int((raw & ~palette)[roi].sum()), palette_not_raw_hsv=int((palette & ~raw)[roi].sum()))
    print(json.dumps(result, default=lambda v: v.item() if isinstance(v, np.generic) else v, indent=2))
```

Each result includes the complete profile and C-order boolean-mask SHA256. The observed final footprint/inferred hashes are:

| Case            | `wm` boolean bytes SHA256                                          | Inferred boolean bytes SHA256                                      |
| --------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `kitlab_widths` | `4549a4e657a9a0a52704c3624743ef2c440674a2200fe06abb7180c1d1d5fc62` | `9d195b2c552b7eb92da698dfa66395cde9da75c17e9346792b9e242f32fe6991` |
| `woodland_kit`  | `44dda5c635a39017e8fcf82ccc3619c1439cf10345f13cfca51764982e92e4f3` | `bf72762acd9d1271c74ede0d0d6326ce70e06739b75a8f0eb261db1175f794af` |

## Exact source pins and verification boundary

All source rows below resolve at frozen #364 `6d309ea3a0bddd38990abecce22419b85ad28d2a`. Blob IDs bind Git identity; SHA256 binds actual consumed bytes.

| Path                                        | Git blob                                   | SHA256                                                             |
| ------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| `scripts/art/kit/bake.py`                   | `f881fbd63808b8e5c4f77cae6b53780550e9c7e6` | `50c8322db00797a1e28afc2fc36f36a1a028fd3ca9a4c7b9995d886c3c27f0e7` |
| `scripts/art/kit/surface.py`                | `fb9b1688e8352350845d5669135e83cecfce8bf3` | `ef962967dd250aaa4e745600a77e99ecfa520c0d69efa631ae541f1e766ae743` |
| `scripts/art/native/softgrid.py`            | `365cdd330b3a1628a1e7eca1114648262a506dab` | `53df92de8ecb0fc3af498ca91aff423242edf12eeb4262ed4a746f31fc3c3767` |
| `scripts/art/native/softground.py`          | `6ad07c557eefa864f1140332e382b2ef8f3101a1` | `b535d34bfc7763d7fafd20bb5f428fdf1a9ad9340303d973755d3e7dd92e9b8e` |
| `scripts/art/native/terrain/noise.py`       | `0d879d5d85126774b9df5b1b11fa81d88037cc10` | `4653ee11bc55ea6ddeaabf1325737e26ebb1a361f339f6f43dc4203d48374ffb` |
| `scripts/art/native/ctx.py`                 | `c79cfda10603fcc7092a4b879dc552c01d88f6c1` | `2a132720eb0afd05e0b9711904ac2f300e251b516a7a4aef7a3dcc6d4d6a9881` |
| `scripts/art/native/compose.py`             | `b6abc53b110b870c82755ce149e71c93448c2b6b` | `c1ac79cae8fe4cb1945a794273d6fc9ce3063f800929ac3ed187ce58f159c8a7` |
| `scripts/art/native/ground.py`              | `c74a4b8ffed4f48c2f7e6cc6e0a0d200407069f9` | `13a9447e4b705d468a09345a85aefebfa64a025ec19e3e6853fec255eeb4dc8e` |
| `scripts/art/native/palette.py`             | `7685bc30fa29bf2c6fe87cfdc4e2ecae2f908b28` | `ad8155d9b4d7f0c9afefc373e43f806ec502b7991b621b01453cc7697309d0b9` |
| `art/house-palette.json`                    | `7e97a7463b3641425e667d7b7764f34510489a54` | `7fd8e8cfd481bc627b4ca6e8425ec3001f80103ae2309f6bc7249ef6326b03dd` |
| `scripts/art/native/accents.json`           | `d612eb0e6c3eb7eedf8cf878186c26bc1aaa9486` | `4116ad6d7e32ef62efba5789a93b694d15b00db7dc8f23cf61b6f00c48a25b09` |
| `scripts/review/water.py`                   | `af50a4ed029d5b95affd6d6f8e865b7b6a8c67e5` | `92453548903236152c76eca6b9e86573fa9dd7d55e4dcf33427703b9133ff6df` |
| `scripts/review/core.py`                    | `7ba054ddf4401c041c5ac032d698798f5ad7e3f5` | `65d93d8e383658719f08e8d2b522a1aaae50bb66277f2118855e5505567fcaba` |
| `scripts/review/assets.py`                  | `e3814eb14c96ef2f9fba34a05e8566ca120fb3a4` | `6279c513ab9886be14bf08e7617cc690102ceeebd1dc451123a00ae2630ba399` |
| `scripts/review/screen.py`                  | `3fe1189d3ab028855ad2771f8b4281c721e21911` | `c5bbcf9e2eb7b23bf7b450c02039094f211e673a17eefb83d42803f2e324fb01` |
| `game/kit/pieces/terrain/water.json`        | `761221f039becd4fc91baa4cc185914988d9aadf` | `4dfbe189ee26952232f53358cf159f6c5c7095c443061ddb83761c750d92ccb2` |
| `game/kit/zones/kitlab_widths.json`         | `b725ae548d6db17d015f999b395db862b25db707` | `5b346ca0e4037e8f1b1b22eb520c821386a37e14ad2c3fdeb6425a486871be5e` |
| `game/kit/zones/woodland_kit.json`          | `cdb2de6e1961d95b525eb8bf15db1a840917e34f` | `695976fa34fedc9bf4a73577c2981a10ac29d455b35673d4af2c20a03d2cca0d` |
| `game/zones/kitlab_widths/ground_baked.png` | `59cbaad18a7652e521fd965c641d1c5499e08226` | `fa8081e501f235bde1622c948d87ddadcb49156f21e0a2eb74c10ab616a59489` |
| `game/zones/woodland_kit/ground_baked.png`  | `faf853f267bf56fb159f0adb536aeba8b254cd64` | `5d92199546fa0cc79e3ec5e2bfe772fc18c9aabcd21eb098295e50507bc2cbaf` |
| `scripts/art/kit/build.py`                  | `1c72e139cde6cee60812747d7c43a163dc32e8ed` | `7475535da6e8ffe5f3e7b230a072f232cae5f0518dd9a091235e42c4e0e63950` |
| `docs/vision/eastward-edges.md`             | `2f4a9fd4ea60526a38c8aaba71d596e394ee2cb7` | `d1ce5b67a83ed20536cf695e6ce25a59f6022b9aa0a1a7bf5f95e3c1df1b4507` |
| `docs/vision/art-style.md`                  | `9e62a481ada60441f1314e7b7cc299df55d12d9c` | `122c83d0a8693526d5e8fcf9e26f8ebc019ace80ee27f4270de16c8241d52d01` |
| `docs/vision/size-guide.md`                 | `71886a3597f9fa434b73cddc698578bed01ee7ae` | `54a36c7155365a4d109bf190cd1596564b23535557c6fa2f7273496b9978b3a0` |
| `docs/world-editor.md`                      | `8df624099fbae4461935274bcc1399380090b663` | `66a110597131d2c70cf85491bfa14d75eb7b09da6bb66a530aa2a142be6a96a1` |

Original report JSON pins resolve at #344 `bc9672a5a63dc15dede557b45e922c8412bb3a1c`:

| Report path                                                                                          | Git blob                                   | SHA256                                                             |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| `docs/reviews/editor-takeover/y12/gates/asset-f217ddc6ada3c552f107/kitlab_widths__ground_baked.json` | `29464a62008c642094c3e1d3133aed8a9093c505` | `397116141fe280716f10f3ef971b07db07f360e205ceea66904420d50f2c7df6` |
| `docs/reviews/editor-takeover/y12/gates/asset-e1ad15292fea96bf1da8/woodland_kit__ground_baked.json`  | `6649fe18114dc7a83d3848db78fc5645cdf04f24` | `a7f8fd6db486658ca024c747bd41d6193433cc765516147c6b90321e9cd99230` |

Ran: bounded mask-only extraction and the existing `check_banks` on the two existing PNGs, source/pixel/hash/profile comparisons, and before/after guards on all tracked bytes/modes, HEAD/tree/parents, index and status of the report checkout, independent frozen subject, original `e5-validation-source` and #344 `palette-editor-review`. All guards matched; no source/evidence/PNG changed during analysis. The original engine and all user/player profiles were neither invoked nor inspected. The complete analysis JSON SHA256 is `734c16466c2409f7350999e62378408c06862f2b5921126fe66e1d46a99efb71`; identical before/after source-guard JSON SHA256 is `6dce20969217ba27ca7d93aecf481b644055f2d250afa9f3075df43875a13fd8`. These supplemental scratch hashes are not required to reproduce the durable source/profile evidence above.

Not run: native bake, generator, Godot/import/editor smoke, capture, new final `npm run verify`, ordinary `npm run check:art-repro`, matching hosted checks, visual/reference/device acceptance. This report remains draft until its later exact-source final allocation and lead review; it cannot borrow E6/#369 or frozen editor gates. No new repository tests are needed for this diagnosis document.
