# Painted structure context proposal and contract blockers

Y28/r1, MyGame Codex · context-plan. This is an **unapproved test-layout proposal**, not a shipping zone or a legal-placement certificate. [ASSIGN6494007899](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6494007899) follows [GO6493960807](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6493960807) and [brief6486454819](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6486454819). The branch starts from main `0940f0c76f51a4859344a32594d65fc03043bf7c`; the read-only subject is frozen editor [#364](https://github.com/rempemat-eng/appify/pull/364) at `6d309ea3a0bddd38990abecce22419b85ad28d2a`, tree `e34dedaa6057c32145d8b5a43758c125f91370af`.

All 11 painted bridge/waterfall pieces are inventoried below. Three distinct variants already occur in labs; eight lack a lab instance. The proposed JSON supplies a reproducible context for every variant, but the full physical validator **refuses the three bridges with six relation faults**. The eight-waterfall control has no fatal data-geometry findings, while retaining candidate-approval and scale advisories. Those results do not establish rendered quality, native bake alignment or physical acceptance. No library, placement, snap or approval override is supplied.

## Existing coverage and exact piece identities

[Residual review5691820654](https://github.com/rempemat-eng/appify/pull/357#pullrequestreview-5691820654) retains all 11 raw preview failures. A preview PNG is a physical drawing, not palette-code data. A later review must examine both that preview and its current composed/baked context. Existing context means a source instance, not a newly validated or approved placement. Every piece below remains `candidate`, `painted=true`, with no approved size class.

| Piece / only variant | Channel / drop in cells | Existing lab instances and texel foot | Coverage |
|---|---|---|---|
| `footbridge_2` / `river2` | 2 / — | None | Missing |
| `woodland_footbridge` / `river3` | 3 / — | `kitlab_widths` at `[360, 156]`; `woodland_kit` at `[384, 948]` | Existing |
| `footbridge_4` / `river4` | 4 / — | None | Missing |
| `waterfall_1` / `w1` | 1 / 1 tier / 2 face cells | None | Missing |
| `waterfall_2` / `w2` | 2 / 1 tier / 2 face cells | `kitlab_tiers` at `[648, 336]` | Existing |
| `waterfall_3` / `w3` | 3 / 1 tier / 2 face cells | None | Missing |
| `waterfall_4` / `w4` | 4 / 1 tier / 2 face cells | None | Missing |
| `waterfall_1_tall` / `w1` | 1 / 2 tiers / 4 face cells | None | Missing |
| `waterfall_2_tall` / `w2` | 2 / 2 tiers / 4 face cells | `woodland_kit` at `[240, 840]` | Existing |
| `waterfall_3_tall` / `w3` | 3 / 2 tiers / 4 face cells | None | Missing |
| `waterfall_4_tall` / `w4` | 4 / 2 tiers / 4 face cells | None | Missing |

The two existing `woodland_footbridge` placements count as one covered variant. `waterfall_2` and `waterfall_2_tall` are the other two. No new source instance, render, gate result or reference is inferred from the inventory.

Each row's JSON is under `game/kit/pieces/structure/<piece>.json`; each preview is under `game/kit/props/art/<piece>.png`. Pins are exact Git blob IDs for metadata and SHA256 for PNG bytes at frozen #364.

| Piece | Metadata Git blob | Preview PNG SHA256 |
|---|---|---|
| `footbridge_2` | `3a2c2561d1676e957d513d08540996503c01b78f` | `8e997f9f52cbf9295bb7b1c64ad84d1fa2efa4562413fb2b6c60d35b809c5f52` |
| `woodland_footbridge` | `e612b7fe92401a60705c58823eb66a696e0b9f5f` | `a977c909a46a156c3afe035da0d9af1ecaa834c464c0e251ed40278633453d7f` |
| `footbridge_4` | `f4b6ec917d0ba4beb13316c1da79df8feb664d9f` | `aab389a52284f1f4aa64ce6d49debc86d9e168c9bef6f70ef6109d0de353248b` |
| `waterfall_1` | `13c511fcaccc7c69d3e8c49f3698312149331e52` | `4c1ce211de6c8236799ed150cbe0a3959973889c7c91f7f6ba83fbdaf16a137a` |
| `waterfall_2` | `770a1189098bfac7ed3415a02224aa23d6d33e15` | `33760377411c80ddb1bca6a0efaf58fdabd17b28f83b10a96e2b28caec8e44a0` |
| `waterfall_3` | `f2a6936892085678055a782c1f76ead489e6f3cb` | `159f859dcf507f551e9336102874f7834f118525121e12586169ef939f684b63` |
| `waterfall_4` | `e15ea115942af9a89ce26e01a7e6fd759d4bc0f6` | `5e9af4e9360966068d8c9219575e025c402365ec1fd9c247dc47ccb98d9f79a8` |
| `waterfall_1_tall` | `01e4bf985d7c71ed331e7efe386c79f9975972e6` | `23e6d4d8ce0cc1725323896951bf1a8c8595ad4941e6025c1a6a60902363ea3f` |
| `waterfall_2_tall` | `c60e7524fdd51168cb51bf4bc56758b2c26e9f94` | `89a924767178c4e5bbe413bdb77594f44a94b69ea29dbcf6cbdd1504d182809f` |
| `waterfall_3_tall` | `9ebc51bf97588a4eec339e904f58c7bd6e13df78` | `e474c4dfc4a95de8845a99d5cf795fed986d88e3faad283c25d9f979673fb892` |
| `waterfall_4_tall` | `84c54029e55a5be431f25a08b7cba067643ec9c2` | `4f7daed1ce520a18b3304b9a13b62cdaafcfb0fafce5f27bc92bb00d100a8f82` |

## Proposed cells, banks, face and pool

The lab is 144 × 36 cells: 3,456 × 864 density-three texels, or 1,152 × 288 world pixels. It is a test canvas intended for separate native-scale crops, not a gameplay footprint or a promised single-screen camera view. `coordinate_space="texels"` is explicit. A cell is 24 texels / 8 world pixels; a foot `[cx,cy]` in the tables becomes `[24*cx,24*cy]` in JSON and `[8*cx,8*cy]` in a world-pixel finding. No renderer scale change is proposed.

All pieces use the authored south-facing drawing. Logical `facing` does not rotate geometry or the painted output. Bridges run north–south across an east–west channel; waterfalls face south over the plateau's south rim. A rotated width/orientation is a separate absent capability, not a free variant.

Bridge strips occupy rows 3 through `2+width`, all on tier 0. Each channel rectangle extends five cells west and four east of its centre column. Two route columns meet the deck at its north and south dry landings and continue to the lab boundary or the lower lawn apron. No path is painted under water. All three strips are wide enough to form a 2 × 2 water body; their existing still-water metadata is retained rather than inventing flow, springs or travel rules. The bridge points deliberately preserve the current half-cell-Y anchoring pattern to expose the contract conflict below.

| Bridge | Centre X | Foot Y | Water rows | Dry landing rows | Route columns |
|---|---:|---:|---|---|---|
| `footbridge_2` | 24 | 5.5 | 3–4 | 2 and 5 | 23–24 |
| `woodland_footbridge` | 72 | 6.5 | 3–5 | 2 and 6 | 71–72 |
| `footbridge_4` | 120 | 7.5 | 3–6 | 2 and 7 | 119–120 |

The short-fall plateau is tier 1 on rows 11–14; its derived face is rows 15–16 and its lower pool is rows 17–20. The tall plateau is tier 2 on rows 23–26; its derived face is rows 27–30 and its pool is rows 31–34. All other rows are tier 0. The face is derived from tiers using the existing two-face-cells-per-tier rule, not painted over with water.

| Width | Centre X / anchor X | Feeding channel columns | Reservoir and pool columns |
|---|---:|---|---|
| 1 | 18.5 | 18 | 17–19 |
| 2 | 50 | 49–50 | 48–51 |
| 3 | 82.5 | 81–83 | 80–84 |
| 4 | 114 | 112–115 | 111–116 |

Each reservoir occupies the plateau's first two rows. The narrow channel occupies its last two rows and has the same columns as the fall footprint. Reservoirs supply a 2 × 2 pool even for width 1. Pools start immediately at the foot and cover every landing column; their four-row depth permits a 2 × 2 water area across the full fall. Foot Y is 17 for short falls and 31 for tall falls. The footprint's negative Y offsets cover exactly the derived face. Odd-width channels use half-cell X so the painter's centre and the cell footprint's centre agree; `floor(anchor)` still selects the authored offset cells. Even widths use integer X.

Spacing is proposed lab composition, not a new clearance rule. Fall centres are 32 cells apart, with lawn margins and separate reservoirs/pools; this deliberately leaves room beyond the sheet for the native painter's slabs, wet rock and spray. `bake.py` scales slab offsets by channel width (`k = width_world/16`) and adds them well outside the footprint; the current data validator does not prove decorative overhang clearance. No authored numerical `placement.clearance` exists on these 11 pieces. Native bake/crop inspection must still establish that rocks, foam and shadows fit without overlap or clipping. The lab contains no props, actors or doors competing with those margins; its one spawn is open lawn at `[24,240]` texels. It invents no settlement, interaction, reward or density rule.

## Bridge contract that prevents a legal complete lab

The full library declares empty bridge `geometry.footprint`, `collision.shape="none"`, and a south-end foot. In `relations.py`, an empty footprint falls back to the single foot cell. The generic `requires:on water` consequently tests that **south foot cell**, rather than the span. The second requirement, `adjacent route`, uses positive distance: a foot cell already on the landing route has distance zero and is refused. The physical deck validator instead requires the span's two ends to be dry, walkable and on the same tier. These are separate checks with separate geometric inputs.

The authored walkable deck heights are 23.33, 31.33 and 39.33 world pixels, or 69.99, 93.99 and 117.99 texels after the index's density conversion. Their natural two-dry-landing positions in this layout use half-cell Y. `snap="cell"` permits half-cell X but whole-cell Y, so those positions also produce off-grid advice in a lab. Moving to either adjacent whole-cell Y shifts one deck end into water. None of the nine bounded controls below produces a legal bridge under the unchanged metadata. This is evidence about these straight-channel layouts and the current contracts, not proof that every imaginable bridge placement is impossible.

| Width | Tested foot Y (cells) | Target bridge findings, excluding approval/scale advice |
|---|---|---|
| 2 | 5 | 2 fatal `rules.deck` findings |
| 2 | 5.5 | 2 fatal `rules.requires`; off-grid advice |
| 2 | 6 | 2 fatal `rules.requires` + 2 fatal `rules.deck` |
| 3 | 6 | 2 fatal `rules.deck` |
| 3 | 6.5 | 2 fatal `rules.requires`; off-grid advice |
| 3 | 7 | 2 fatal `rules.requires` + 2 fatal `rules.deck` |
| 4 | 7 | 2 fatal `rules.deck` |
| 4 | 7.5 | 2 fatal `rules.requires`; off-grid advice |
| 4 | 8 | 2 fatal `rules.requires` + 2 fatal `rules.deck` |

All three bridges remain present in each top-band control; only the selected Y is varied. This prevents unrelated orphaned route approaches from being mistaken for that bridge's findings. A first external exploratory control removed the other bridges and consequently reported unrelated approach faults; it is retained as exploratory evidence and is not used for this table.

The needed next source contract is precise: how do bridge placement relations address the span and its two landing cells, and how do the authored south-foot anchor, deck bounds and permitted snap agree? An assigned engineering follow-up must reconcile those existing semantics with ground-rules 3–4, preserve dry landings, and demonstrate the actual editor refusal/acceptance. This document does not choose a new snap rule, falsify a water cell, add a footprint, rewrite metadata or weaken either check. Matt retains any design decision and approval.

## Full proposed JSON

Save the JSON block to an **external** file. It is deliberately not a committed `game/kit/zones/` plan and must not be adopted as a legal fixture before the bridge contract is resolved. The `bake` flag records eventual intended output, not an executed or allocated bake.

```json
{
  "zone": "painted_structure_context_proposal",
  "note": "Y28 unapproved test-layout proposal; bridge relation/snap blockers retained.",
  "coordinate_space": "texels",
  "legend": {".":"lawn","#":"path","~":"water"},
  "rows": [
    ".......................##..............................................##..............................................##.......................",
    ".......................##..............................................##..............................................##.......................",
    ".......................##..............................................##..............................................##.......................",
    "...................~~~~~~~~~~......................................~~~~~~~~~~......................................~~~~~~~~~~...................",
    "...................~~~~~~~~~~......................................~~~~~~~~~~......................................~~~~~~~~~~...................",
    ".......................##..........................................~~~~~~~~~~......................................~~~~~~~~~~...................",
    ".......................##..............................................##..........................................~~~~~~~~~~...................",
    ".......................##..............................................##..............................................##.......................",
    ".......................##..............................................##..............................................##.......................",
    ".......................##..............................................##..............................................##.......................",
    "................................................................................................................................................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    "..................~..............................~~..............................~~~............................~~~~............................",
    "..................~..............................~~..............................~~~............................~~~~............................",
    "................................................................................................................................................",
    "................................................................................................................................................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    "................................................................................................................................................",
    "................................................................................................................................................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    "..................~..............................~~..............................~~~............................~~~~............................",
    "..................~..............................~~..............................~~~............................~~~~............................",
    "................................................................................................................................................",
    "................................................................................................................................................",
    "................................................................................................................................................",
    "................................................................................................................................................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    ".................~~~............................~~~~............................~~~~~..........................~~~~~~...........................",
    "................................................................................................................................................"
  ],
  "tiers": [
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",
    "111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",
    "111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",
    "111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222",
    "222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222",
    "222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222",
    "222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
  ],
  "pieces": [
    {"id":"bridge_2","piece":"footbridge_2","at":[576,132.0],"variant":"river2","facing":"s"},
    {"id":"bridge_3","piece":"woodland_footbridge","at":[1728,156.0],"variant":"river3","facing":"s"},
    {"id":"bridge_4","piece":"footbridge_4","at":[2880,180.0],"variant":"river4","facing":"s"},
    {"id":"waterfall_1","piece":"waterfall_1","at":[444.0,408],"variant":"w1","facing":"s"},
    {"id":"waterfall_2","piece":"waterfall_2","at":[1200,408],"variant":"w2","facing":"s"},
    {"id":"waterfall_3","piece":"waterfall_3","at":[1980.0,408],"variant":"w3","facing":"s"},
    {"id":"waterfall_4","piece":"waterfall_4","at":[2736,408],"variant":"w4","facing":"s"},
    {"id":"waterfall_1_tall","piece":"waterfall_1_tall","at":[444.0,744],"variant":"w1","facing":"s"},
    {"id":"waterfall_2_tall","piece":"waterfall_2_tall","at":[1200,744],"variant":"w2","facing":"s"},
    {"id":"waterfall_3_tall","piece":"waterfall_3_tall","at":[1980.0,744],"variant":"w3","facing":"s"},
    {"id":"waterfall_4_tall","piece":"waterfall_4_tall","at":[2736,744],"variant":"w4","facing":"s"}
  ],
  "spawns": {"start":[24,240]},
  "lab": true,
  "bake": true
}
```

## Reproduction and actual bounded results

Use the unchanged frozen #364 source, not main's older absent kit or a rewritten registry. The documented `kit_scene` CLI accepts an absolute external JSON path. No Godot import, scene generation or native bake is needed for this data check:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m scripts.review.kit_scene /absolute/external/proposal.json --check --json
```

The exact parsed block serialised with `json.dumps(plan, indent=2) + "\n"` has SHA256 `c116dd5398354a483e8fbfe0e2ad10ba2df0147babc1b61f8d1db391b538bcd4`. The actual command returned **1**, with six fatal `rules.requires` findings (two per bridge), plus 14 `rules.unapproved`, three `rules.off_grid` and 19 `rules.scale` advisories. It reported no fatal deck, face/feed/pool, route-water, bounds, overlap or spawn finding for this full proposal. Exit 1 is a refusal, not a pass or an environmental error.

For a separate eight-fall data control, remove the first ten rows and tiers, keep only `waterfall_*` instances, subtract 240 texels from their Y positions, and use a lawn spawn `[24,24]`. Run the same CLI on that external JSON. The actual command returned **0**, with ten unapproved and 16 scale advisories and no fatal findings. This proves only that the current data geometry checks accept the proposed fall face/feed/pool arrangement. Approval, scale, rendered join quality, the preview's raw failures and a matching Eastward comparison remain open.

`scripts.art.kit.schema.check` on the 11 unchanged source piece files reported **11/11 with no structural/semantic errors**. This is piece-schema coverage; there is no claim of a new standalone JSON Schema for zone plans. `kit_scene.normalize` and the full validator are the executed Python plan intake. The GDScript `kit_zone.gd` importer/round-trip was read, not executed. The older `kit_rules.check_zone` reported only seven advisories (three candidate materials, three off-grid bridge feet and one aggregate candidate-piece notice); its absence of faults does not override the full validator's six relation faults.

The final CLI JSON logs have SHA256 `58c08dd93e4030e2d4516a5075a75f8c6ea0cc1d1b2d874ffb8b339771e2985f` (full proposal) and `b4134329c3bfb2c827cf4477326252ae4c0d09b54c91e2ea72170aa68d9fde8d` (fall control). External scratch evidence includes the complete JSON, nine-control findings, exact source inventories and before/after byte/index/status guards. All 10,929 tracked subject files, modes, HEAD/tree/real parents, index and clean worktree status were unchanged. No original owner checkout was edited.

Not run: Godot, import, editor placement, native painter/bake, renders, captures, reference generation, full `npm run verify`, ordinary `npm run check:art-repro`, hosted CI or Y12 raster gates. Final exact-source checks require a later lead allocation. Raster quality gates and Eastward detail ratios are N/A to this text-only proposal, not visual PASS. #364's existing 14 raw findings and this report's refused bridges remain visible. The PR stays Draft/`needs-matt-review`; Matt's explicit OK on the applicable PR is still required before any art/map/kit adoption.

## Frozen supporting source pins

All paths below are Git blobs at `6d309ea3a0bddd38990abecce22419b85ad28d2a`. Source notes above name the relevant functions; pins avoid relying on line numbers in later trees. Piece and PNG pins are in the 11-row table.

| Path | Git blob |
|---|---|
| `docs/world-editor.md` | `8df624099fbae4461935274bcc1399380090b663` |
| `docs/vision/ground-rules.md` | `0e5961477a77321c93d883a1f4ff1327a6dcbcf7` |
| `docs/vision/eastward-edges.md` | `2f4a9fd4ea60526a38c8aaba71d596e394ee2cb7` |
| `docs/vision/size-guide.md` | `71886a3597f9fa434b73cddc698578bed01ee7ae` |
| `docs/vision/art-style.md` | `9e62a481ada60441f1314e7b7cc299df55d12d9c` |
| `game/kit/schema/piece.schema.json` | `fd61e5d29ca017e3f3796a013c86fc0afe58dc16` |
| `game/kit/terrain/manifest.json` | `eaa4e0381bb1fba2ebf62657f7e42a7d1e6d21da` |
| `game/kit/props/index.json` | `a3739a19bacf2886717f1b65de695df901bc8499` |
| `game/kit/zones/kitlab.json` | `1e11de8cb0914f4000e3ff83a169a5bf4fdb653d` |
| `game/kit/zones/kitlab_tiers.json` | `c1d728ce6e9fe4f17f743ddbb398bb69b59271b3` |
| `game/kit/zones/kitlab_widths.json` | `b725ae548d6db17d015f999b395db862b25db707` |
| `game/kit/zones/woodland_kit.json` | `cdb2de6e1961d95b525eb8bf15db1a840917e34f` |
| `scripts/art/kit/schema.py` | `056c1f9a30d49e203badd97624458130c79c81b2` |
| `scripts/art/kit/relations.py` | `dd6b718b24f9f681cd5450ecbb0216e6a1ae8420` |
| `scripts/review/kit_rules.py` | `102e96adec440900b76d5d0fc45b9c624988c63d` |
| `scripts/review/kit_scene.py` | `6c71732fb52cbe86e8fa723c4d09a0af4d553371` |
| `scripts/art/kit/structures.py` | `6a2a9e4f1a70802fed4abef4e37b22ddc7d3354c` |
| `scripts/art/kit/bake.py` | `f881fbd63808b8e5c4f77cae6b53780550e9c7e6` |
| `scripts/art/native/softground.py` | `6ad07c557eefa864f1140332e382b2ef8f3101a1` |
| `scripts/art/native/rocks.py` | `915357f9e61528d1c296ab41533cca6fdffcc276` |
| `scripts/art/native/water.py` | `8a18feda4c9d6f8580471a61157529ad8293c637` |
| `game/tools/kit_zone.gd` | `c80fef7834c595b2dea2ecb45caa7c3a46789b52` |
| `game/world/terrain/kit_piece.gd` | `ab7ce936f13865b75c826d84d4b360e8d8848017` |
| `game/test/fixtures/kit/README.md` | `ca498263c1affa74a941fa0ac01c8bc38f52e3e1` |
