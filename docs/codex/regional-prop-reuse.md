# Regional prop reuse qualification: quench trough and packing crates

The existing stone quench trough and two packing-crate pictures can be assessed
before commissioning duplicate art. This step fixes a source footprint defect
and adds the already-written water/route refusals. It does not place either
design in a region or complete its missing receiving contract.

Authorisation: [Y45 GO6499932433](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6499932433),
[ASSIGN6500067550](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6500067550),
slot `waterfront-props`, branch `codex/regional-prop-reuse`. The genuine parent
is editor375 `45ed3cad029c106977e6c0c833913dcb1c614fbd`, tree
`0bdea46338655dcb3c9922ad5cbcdd023310b87d`. The completed Y36 source remains in
lead review custody; it is not an additional implementation claim or ancestry
input here. All Claude lanes remain off.

## Exact source and reuse boundaries

| Input | Commit | Git blob |
| --- | --- | --- |
| Existing prop inventory384 | `fe00d9b147e051ea372f96a917175c907db6db6c` | `e50b7680ae255e8bff2c3ea70d4f3a3776b7c1cd` |
| Fire-country requirements338 | `d837264110ae49ba7e40a58c4d4bad91772b2985` | `477aace94859ded15c6468f12e56131efa0da9f1` |
| Tidebloom requirements386 | `d11b55661593cb8e23dd6c392524db4669bd9217` | `4c2caa84f8929f12c92f8049aaedb2cff0d042a2` |
| Sunstone requirements366 | `533be3e15e33bd016e577d503e5e8585f2705bfc` | `b588cb1fafdd1d7c8e6a300f626e5aecb5388116` |
| Baseline `crossroads_trough.json` | editor375 above | `031142b645e8288e1bca8e3e2f54593fb0ba0c28` |
| Baseline `crossroads_crates.json` | editor375 above | `57f5de06fa86806e5b2c5d0f56a818e3fc18ab1b` |
| `native/village.py` | editor375 above | `78f5e5c48602242d26a52f2e0ce9dbd37610d999` |
| `native/town.py` | editor375 above | `fedd255dcffc57aa42c7668de6c80ef1e7a17f58` |

All paths in the last two rows begin with `scripts/art/`. The inventory separates
106 candidates, 129 concepts and historical ledger grades. Its132 current PNG
references have no exact-path join to the legacy ledger: a historical KEEP
trough or crate name does not approve these pictures.

`native.village.p_trough` explicitly draws a stone quench tank. Fire338's
ordinary-smithy context names the hearth/anvil/trough relationship, but does
not supply the custom Ember great-forge layout or a receiving building ID.
No `near forge` selector is added here: a source phrase is not an implemented
receiving anchor. No Hale-specific anvil, restoration condition, forge action
or owner is borrowed. Sunstone366's windpump requires a real well within two
cells; this trough does not automatically satisfy that contract.

Tidebloom386 names fruit crates in the packing-shed cluster, while its exact
receiving building identity remains unbound. Existing `p_crate`, selected by
`native.village.prop` and `native.town`, supplies two source pictures. The
proposed reuse establishes neither their contents nor a shop, inventory,
household, resident, job or routine. No new family, species or function is added.

## Existing pictures and geometry

Every picture below is unchanged from the genuine parent. The PNG header sizes
and declared variant feet agree; byte/Git-blob equality is source evidence,
not a decoded-pixel, scale or detail approval.

| Candidate / variant | Existing picture under `game/zones/crossroads/art/` | Git blob | Canvas / foot, art px |
| --- | --- | --- | --- |
| `crossroads_trough` / `trough_35` | `trough_35.png` | `2318da5f220758081084198272412de5fdb24667` | 96x57 / [48,53] |
| `crossroads_crates` / `crates_30` | `crates_30.png` | `e22ec45be9400a3ab626fabc5efcc90d5d3c0ded` | 54x114 / [27,110] |
| `crossroads_crates` / `crates_32` | `crates_32.png` | `44ac4c9bfc423fd3d4697a5a081b800de0f92dc7` | 54x114 / [27,110] |

| Existing quench trough | Existing crate variant30 | Existing crate variant32 |
| --- | --- | --- |
| ![Existing stone quench trough](../../game/zones/crossroads/art/trough_35.png) | ![Existing packing crates30](../../game/zones/crossroads/art/crates_30.png) | ![Existing packing crates32](../../game/zones/crossroads/art/crates_32.png) |

Density3 means24art pixels per8-world-pixel cell. Existing `cell` snap permits
half-cell X and whole-cell Y. Both crate variants use the same unchanged
collision rectangle[-6,-10,12,10]worldpx. At[300,192]artpx, its actual collider
intersects Xcells11,12,13 and Ycells6,7; the old four-cell metadata covered only
X11,12. The correction is the minimal conservative union
Xoffsets[-1,0,1] x Yoffsets[-2,-1], six cells. Collision, anchor, snap and both
variant definitions stay unchanged. A conservative union can include a cell
not occupied by the continuous collider at one particular phase.

The trough rectangle[-10,-8,20,8]worldpx is already covered by its existing
Xoffsets[-2,-1,0,1] x Yoffset[-1] at both admitted Xphases. Its geometry is not
changed. Negative/zero/positive whole-cell translations preserve the same phase
contract; none of these arithmetic samples is a world placement or walk test.

## Supported refusals and explicit unknowns

Both pieces now declare only `forbids:on water` and `forbids:on route`.
Ground-rules sections3–4 prohibit unsupported water crossings and objects in
the walking band except deliberately designed bridges/signposts. These ordinary
solid props are neither exception. The existing relation engine understands
both selectors; no new rule, target, schema or material ID is introduced.

Positive ground allowlists, placement roles, numerical clearances, receiving
biome tags and live-shadow bindings remain **unresolved**, not zero-valued
defaults. Their original `biomes:["village"]`, owner:null, empty function,
gameplay fields and candidate state remain unchanged. The qualification is not
permission to place a village-tagged piece on ash, basalt, deck or sand.
Door/customer/working bands need actual receiving geometry before use.

`cast_shadow.shape:baked` is retained as source provenance for the old
Crossroads ground. The current `props.entry` does not turn that into a live
ellipse; neither source metadata nor a palette presence establishes a new
region's shadow. No guessed radii, offsets, scale class or reference is added.
An absence of a receiving relation finding does not resolve these missing facts.

The new20x16-cell `regional_prop_reuse_lab.json` is a tiny, explicitly unbaked
diagnostic using existing worn earth, path and edge-connected water. Its two
entries are reference objects, not a smithy/island town. Baseline kit plans
reference neither selected ID, so this is a qualification-context gap rather
than another city layout. Illegal variants remain external controls. No image,
scene, bake or shared index was generated.
The current compiled kit lacks a worn-over-water transition at this diagnostic
boundary. A later live picture must retain/report that hard-edge fallback;
the metadata lab is not a rendered material or bank approval.

## Actual bounded controls

The external `regional-prop-reuse-evidence/controls.py` calls the existing piece
schema and relation engine; it independently intersects the actual continuous
rectangle with24px cells and compares the result to the engine's declared
occupied cells. Each unchanged variant is checked at153anchors spanning both
legal Xphases and negative/zero/positive whole-cell translations:459samples.

The actual RED run (`a945a4`, exit1) retains72uncovered samples for each crate
variant, zero for the trough, and ten falsely accepted water/route cases out
of22relation controls. That result is not hidden by the correction. The actual
GREEN run (`d5ce6a`, exit0) has zero uncovered cells across all459samples,
22relation controls passing and two existing schema checks passing. It also
checks all three original variant identities/PNG headers/feet and preserves
the explicit unknown fields. Input metadata is unchanged during each run.

Relation cases cover legal integer/half-X anchors, forbidden half-Y/quarter-X
anchors, water/route refusals and the crates' formerly omitted right-edge cell
when it contains water or a route. No numeric clearance or full compiled-zone
overlap acceptance is asserted. These are source controls, not engine physics,
editor placement, rendered ground, automatic approval or a full kit pass.

| Retained report | SHA256 |
| --- | --- |
| `before.json` | `ac0aebf70842c471b2aa3b83b0a587a277066e5603b83c8a0d018c27f096e567` |
| `after.json` | `bd6b026bf10d02d39fb31c5033da622b2d852e855a87aad42598111c458998c4` |

## Integration and remaining acceptance

Only the two existing candidate JSONs, this document and the one new lab are
authored. Painters, three PNGs, W0 concepts, schemas, palette, seeding, shared
index/scenes, existing labs, town/terrain/actor files and game rules are unchanged.
The exact four-path scope needs lead/independent source review before a later
explicit one-shot rendered qualification.

The shared seeder is an important boundary: default seeding skips existing
piece files. `seed_props --force` rebuilds geometry/footprint at cell-aligned
phase while retaining placement/rendering choices, and can put these candidate
crates back to four cells. Its reviewed-state overwrite guard does not protect
a candidate. No seeding ran and no shared seeder patch is included; the
integration owner must retain/reconcile the phase proof before a forced refresh.

Shared derived index/scenes are unchanged and their fresh intake has not run.
The source correction is not credited as a delivered editor/runtime fix until
that receiving pipeline is rebuilt and checked by its owner.

Full verify/zero-warning lint, ordinary art reproduction, Godot/kit, rendering,
current Y12, official Eastward matched crops/detail counts, actual regional
ground/shadow/clearance/biome bindings, editor placement/occlusion, device evidence
and Matt's explicit OK remain outstanding. Keep this PR Draft and
`needs-matt-review`; no Ready, merge or production placement is requested.

## Y46: preserve the admitted phases through a forced metadata refresh

Caliper's [GO6500931589](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6500931589)
and [ASSIGN6501044730](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6501044730)
authorise this bounded continuation on `codex/caliper-prop-seed-phases`, from
the genuine Y45 head `d6c9beeb8d473bef519c936f06fea37b444eb29d`, tree
`c77e772cb54244b68310e79d87167a3be5638c59`. Y40 remains in lead review custody.
The preceding Y45 report and its historical seeder warning are preserved above.

The rectangular-footprint derivation now uses the existing piece's retained
`placement.snap`. For `cell`, it unions positive-area rectangle intersections
at world-X phases zero and four, with whole-cell Y. These are exactly the
relation engine's existing half-X/full-Y placements, measured from the floor
of the foot. No margin, collider, rendering foot, snap permission or relation
rule changes. Both crate variants retain six cells; the trough retains four.
Source ordering stays deterministic. Variant feet remain source-backed and
placement/rendering decisions and existing reviewed-state guards are preserved.

Other snap modes, absent snap, circles and unknown/procedural collisions keep
their previous derivation. Their coverage is not newly established: the existing
cell-aligned approximation and open runtime notes remain explicit. This change
does not implement continuous free-snap coverage, half-Y coverage or circle
physics. Existing candidate audit notes, including historical warnings, are
retained rather than silently deleted. New cell-snap rectangle output records
the two-phase qualification; exact runtime blocking still needs its receiver.

`python -B -m unittest scripts.review.test_seed_prop_phases -v` passes all
11 focused tests. The real `_assemble`, `main`, schema validator and relation
engine are exercised with tiny new temporary metadata destinations. Only source
discovery is substituted by a bounded batch, and image dimensions are injected
from the pinned metadata. The batch retains `seed()`'s final source/TODO
normalisation. No full-world `seed()`, PNG intake, painter, drawing or original
destination write is claimed.

The final tests on the unchanged parent seeder produce 22 assertion failures
and zero errors: the crate footprint regression, 18 uncovered half-X samples
across both variants, the boundary case and two missed water/route refusals.
The corrected seeder passes the same tests, including 54 independent
continuous-rectangle coverage samples across all three variants and signed
whole/half-X translations. Boundaries use positive-area intersections, excluding
mere touching and empty rectangles. Real relation checks retain quarter-X and
half-Y refusals. Default skip preserves file bytes; force preserves authored
fields and is idempotent after normalisation. All four reviewed approval states
refuse the whole batch before writes, and a concurrent destination edit is
refused. Source piece bytes remain unchanged throughout.

Earlier test-development failures are retained: an unsupported synthetic audit
key caused schema refusal, then omitting `seed()`'s final normalisation in the
bounded batch caused an idempotence failure. The fixtures were corrected; those
failures are not production fixes or passing evidence. The first patch run
still exposed that normalisation fixture error before the final green run.
An independent disjoint code/test review found no source blocker and ran no
additional controls.

| Final retained log | SHA256 |
| --- | --- |
| Parent RED, 11 tests / 22 assertion failures / 0 errors | `fb934d92b9b1835a3f6832ed8bfddf4d0ebb4402191ed8292033fc112ea76c1e` |
| Corrected GREEN, 11 tests / 0 failures / 0 errors | `734c3469ae16186ba3be117f68a332244424a771b6093c5a798e90aa41ddd15e` |

Only the seeder, the new focused test and this appended continuation change.
All existing piece JSONs, PNGs, painters, shared index/scenes, schemas and
other source remain unchanged. No broad refresh has run. A later integration
owner must separately validate the receiving pipeline. Full verify/zero-warning
lint, ordinary art reproduction, full kit/Godot, Y12, rendering, regional
bindings, runtime/device evidence and Matt's PR-specific approval remain
NOT RUN or outstanding. Keep Draft and `needs-matt-review`.
