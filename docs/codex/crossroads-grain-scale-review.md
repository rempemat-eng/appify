# Crossroads grain-weighing station — source review

## Current detail follow-up — Y36-GRAIN-GOODS-DETAIL/r2

Owner `rivet`; [source-art-only GO6536088965](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6536088965), [ASSIGN6536174210](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6536174210), [separate ACK6536174451](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6536174451). SAME #403, genuine child of `eee6036dd1d96a6c63c6a25a6ca33a0ccf56d77e` / tree `c71eb0721229fd4dc39497ebb12323b763665844`. This batch owns **only the bodies/docstrings of `p_cart` and `p_sacks_hd` in existing `scripts/art/native/village.py`, and this detail-follow-up section**. All text below this section remains the previous batch's historical record, not current permission. No new painter, catalogue entry or mechanics.

### Actual failure and retained baseline

[H3 result/release6536097367](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6536097367) and [fresh independent receipt6536084235](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6536084235) describe actual SUCCESS run41146473403 on receiver #406 `c302b3380f99091e30ef6e7dc2b18f6118a268f3` with old source4035dd. ZERO grain repaint, ONE native composition; runtime and collector released. This source batch **does not repeat H3 or retarget its evidence**. The actual [1920×1080 working-yard image](https://chatgpt.com/library?file_id=libfile_c970bc67ad7c8191b11b6e716260faa0&account_id=personal) was viewed, along with the exact two old Git PNGs below. The cart's shafts/axle/support connections read weakly; the storage bags read bright, soft and speckled. Published catalogue detail ratios remain **0.671 / 0.509, both false**. No new score or physical output exists for this revision.

| Existing unmodified PNG | Bytes / SHA256, verified against actual eee Git blob | Unchanged canvas / foot, art texels |
| --- | --- | --- |
| `game/zones/crossroads/art/handcart.png` | 2189 / `c79efcf10302f57de118c8da5db0c924951bdaa3d9506cd3591a6d405f32c94a` | [114,84] / [57,80] |
| `game/zones/crossroads/art/sacks_12.png` | 1122 / `bd2e5e135d64ac9a0bc08eebd88cef494fbfd9ae97e50b89819212fbd0b56699` | [60,66] / [30,62] |

The source repair leaves those committed pictures, their metadata, catalogue findings, approval=candidate and function={} unchanged. New source and old PNGs are deliberately **not reproduction-consistent yet**; no old full-gate pass covers the new source. Ground noise, widely spaced context, mixed live/baked lighting, absent Moss contact, and Moss facing the camera away from the station remain separate unresolved work.

### Two forms, existing native API

The actual source plan `game/data/plans/crossroads.json` has handcart in `art.dressing[57]`, kind=cart, size=[22,8], id=handcart; sacks at index12, kind=sacks, size=[14,8], default id=sacks_12. Neither entry sets a seed. The real `town.py` dressing caller uses `seed=dr.get('seed',100+k)`, then `V.prop(kind,w,h,seed=seed,hd=PROP_HD)`, with PROP_HD=(D>=2.5). Thus the exact seeds are **157 and112**, not a new choice. ASSIGN's preliminary cart173 was corrected before authoring/generation; no invocation used173.

At D3, `prop` selects cart through unchanged PROPS['cart']=p_cart (there is no cart PROPS_HD override), and sacks through unchanged PROPS_HD['sacks']=p_sacks_hd with hd=True. Only p_cart's D>=2.5 branch changes drawing; its original lower-density statements remain AST-exact. Shared `sack()`, PROPS/PROPS_HD, all other functions/signatures/imports/top-level constants, palette and density dispatch remain byte-exact outside the two owned bodies. No new per-region painter or helper framework.

| Form / demonstrated weakness | Authored pixel construction, **not yet drawn or measured** |
| --- | --- |
| Cart: detached-looking shafts, little visible underside/axle connection | Existing shaft tips continue into the underframe. Cross rail and diagonal brace support the bed; an iron axle/bearing connects to the existing near wheel. Back rail, exposed floor, front planks, east end and dark underside are distinct planes; corner stiles continue to the cross rail. Local iron straps/fasteners and short worn handhold edges explain construction. |
| Cart: flat rim/hub and thin spokes | Existing wheel centre/radius and six-spoke design remain; wood felloe joints, iron tyre planes, hub collar/end and upper-left highlights separate metal from wood. No solid wheel disk or added load to inflate density. Existing sack/crate load stays at its original coordinates; only that local sack's tone/fold treatment changes, not shared sack(). |
| Sacks: pale round caps and blanket diagonal weave | Existing three bag centres/radii and stack relation remain. Shoulders taper within the original radii; the lower body stays weighted. Cloth body/core/underside steps are capped at tone4, with three gathers converging on each tied mouth, a seam with paired stitches, and two short local weave clusters. Broad panels remain quiet. |
| Sacks: weak contact and ties | Each new overlap shades only previously occupied cloth down/east of the bag, never empty ground. Gathered neck, rope band/knot and short hanging end are separate clusters. No global sack-helper edit, noise field, new colours or new cast-shadow system. |

Existing `_pic` calls are retained: cart(w,h,up=18,side=7), sacks(w,h,up=12,side=2), pad3. Static D3 arithmetic gives cart W=3×(22+14)+6=114, H=3×(8+18)+6=84; sacks W=3×(14+4)+6=60, H=3×(8+12)+6=66. Feet remain W//2,H−4. No padding, scale, position, collision, snap, seed, source kind or path change. Visible alpha/edge/contact/detail and reproduction effects still need actual outputs and review; canvas arithmetic alone proves none of those.

### Reference choice and precise comparison gap

The existing official [Eastward Steam store](https://store.steampowered.com/app/977880/Eastward/) market screenshot `ss_ddd76431b1df70e234494c92370e2391680c98ef.1920x1080.jpg` was re-viewed outside Git; SHA256 `bf709bd60afbb1551010ff80f499b5c5fa72b79c7e77a93cf65eda83f51442c5`, 594858B. Its exact previously selected raw [575,690,740,820] foreground table/support area shows connected top/edge/support planes and clustered containers against a calmer passage. The nearby cloth canopies show broad lit/body/fold shade separation. These are **structure/material context, not a matched cart or three-sack crop**; no pixels are copied. The existing size-guide cites its measured shot04 stall-cart and adult-based proportions, but that historical numbered source has not been reconciled to this raw screenshot or independently remeasured here.

**Precise gap:** no traceable native-period + adult-height + same-kind cart/sack matched crop has been established in this source-only batch; no normalised side-by-side or 16×16 tone/shape/dressing counts ran. Written upper-left light, material ramps, coherent clusters and size guidance guide the repair. Neither palette count, extra seams nor muted sacks demonstrate the detail threshold. `audit.eastward_ref` remains null; Y12 and Matt's PR-specific review remain required. The future comparison must first establish actual reference identity, native period/adult and object class, then report real counts or explicitly keep the gap open.

### Exact later two-output invocation, NOT RUN / not a runtime GO

After root+peer review and a **separate bounded allocation**, use the existing native API in one fresh private Python process from the exact reviewed private source root, with a fresh absolute output subdirectory and approved private dependency environment. This is a direct invocation of existing methods, not a committed new painter. It imports no town/terrain/world generator and draws only the two named outputs; the enclosing allocated receiver must enforce source/input/dependency/budget/collection guards and retain actual results/partial failures. No ambient dependency substitution or production output overwrite.

```bash
"$PRIVATE_PYTHON" -B - "$PRIVATE_TWO_ASSET_OUT" <<'PY'
from pathlib import Path
import sys
from scripts.art.native import ctx
ctx.configure(3.0)
from scripts.art.native import village as V
out = Path(sys.argv[1])
assert out.is_absolute()
out.mkdir(exist_ok=False)
for name, kind, w, h, seed, size, foot in (
    ('handcart.png', 'cart', 22, 8, 157, (114, 84), (57, 80)),
    ('sacks_12.png', 'sacks', 14, 8, 112, (60, 66), (30, 62)),
):
    pic = V.prop(kind, w, h, seed=seed, hd=True)
    assert (pic.W, pic.H) == size and (pic.ax, pic.ay) == foot
    pic.rgba().save(out / name, optimize=True)
assert sorted(p.name for p in out.iterdir()) == ['handcart.png', 'sacks_12.png']
PY
```

The source GO does not allocate that command, imports, dependency install, any draw, comparison or composition. Later root+peer review must reserve any minimal existing receiver change needed to consume this new native blob/source with the two new PNG hashes while preserving exact H2 grain reuse; #406c302 stays frozen now. Existing H3 inputs/pins and results cannot silently attest to the repaired goods. Two output dimensions/feet, actual alpha/outline/planes/joints/cloth and old/new comparison require real measurements before one later working-yard composition; zero grain repaint. Exact reference/receiving resources and limits need their own GO. No new receiver/framework or runtime ref is created here.

**This batch's checks:** standard-library AST/source/JSON/PNG-header/hash inspection only; exact outside-body bytes/signatures/92 other top-level definitions and lower-density cart AST retained, caller/seed/D3 canvas arithmetic, original-document suffix preservation, whitespace and genuine-history/full-other-leaf/immutable-byte proof. No subject import, test, draw, install, runtime download, engine, composition, job, execution ref, kit_golden, verify, art reproduction, kit/Godot/full gates, Ready or merge. Source lease ends at HANDOFF or 60min from ACK; execution reservation NONE. Eventual canonical `python3 -m scripts.art.kit_golden` and final exact-source gates remain held; a source clear is not visual/Matt approval.

## Current goods bindings — Y36-GRAIN-GOODS/r1, 30 October

Owner `rivet`; [source-only GO6534897411](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6534897411), [ASSIGN6534981831](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6534981831), [separate ACK6534982071](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6534982071). **Drawn equivalents exist: reuse `crossroads_handcart` and `crossroads_sacks`.** This continuation owns only this existing document, as a genuine child of #403 `5dd3825353078b8b8e231f081714144891d98feb` / tree `120c336609b393591a662beddf45a84149e73810`. No goods painter, new duplicate piece, image, index, fixture, ground, scene, zone or metadata change is needed or authorised. Source reservation ends at HANDOFF or 23:35 UTC; no execution reservation.

The grain station has since been drawn outside Git. [Actual H2 result6533592547](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6533592547) and [independent receipt6533637354](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6533637354) retain one two-state draw and one successful native/2× synthetic diagnostic on **source5dd / receiver4063e7**. [The native image](https://chatgpt.com/library?file_id=libfile_a6ecf48f6df481918611ac880b02ab6a&account_id=personal) and [2× image](https://chatgpt.com/library?file_id=libfile_31d4b24e53a08191bc4ad49749e769f3&account_id=personal) are the review baseline. No completed draw/composition is repeated here. The old NOT GENERATED/NOT RUN wording in the historical record below describes its original source-only batch, not the later H2 result. The original source definitions, #406 receiver and external H2 outputs remain unchanged.

### Exact existing inputs for the next working-yard candidate

Every path and blob in the next two tables is pinned to **5dd3825353078b8b8e231f081714144891d98feb**, remains available in this document-only child, and is a candidate, not an approved asset. PNGs were read from that actual Git commit, their headers/hashes checked, and the two unmodified pictures visually inspected before choosing reuse.

| Candidate ID / exact variant | Metadata path | Git blob / bytes |
| --- | --- | --- |
| `crossroads_handcart` / `handcart` | `game/kit/pieces/prop/crossroads_handcart.json` | `d50ff1b2469e67333ecc47b4dd58a794a3a7c21d` / 1684 |
| `crossroads_sacks` / `sacks_12` | `game/kit/pieces/prop/crossroads_sacks.json` | `ad8a77b6d5b63e9863cde3d2ba7980fc2d2c30e8` / 1625 |

| Exact `res://` PNG binding | Repository path | Git blob / bytes / SHA256 |
| --- | --- | --- |
| `res://zones/crossroads/art/handcart.png` | `game/zones/crossroads/art/handcart.png` | `c1016d875a02681ecfc24f624b98dc74e3caa35d` / 2189 / `c79efcf10302f57de118c8da5db0c924951bdaa3d9506cd3591a6d405f32c94a` |
| `res://zones/crossroads/art/sacks_12.png` | `game/zones/crossroads/art/sacks_12.png` | `26f9bc05d662407557e6c152cf7fbc8c65b41871` / 1122 / `bd2e5e135d64ac9a0bc08eebd88cef494fbfd9ae97e50b89819212fbd0b56699` |

| Existing handcart, unchanged native picture | Existing storage group, unchanged native picture |
| --- | --- |
| ![Existing candidate handcart](../../game/zones/crossroads/art/handcart.png) | ![Existing candidate sack cluster](../../game/zones/crossroads/art/sacks_12.png) |

The cart visibly supplies a plank bed/rails, ground-resting shafts, an iron-tyred spoked wheel/hub and an existing sack/crate load. It is already the ordinary goods-cart equivalent; no new `crossroads_grain_handcart` is commissioned. The storage picture supplies three tied cloth volumes, seams/folds and local shading; no new `crossroads_grain_sacks` or inventory item is commissioned. These pictures can illustrate loading/storage beside the scale without establishing a grain stock, job, shop, owner or routine. Hidden axle/load support and fine material craft still need the applicable review; an object being recognisable is not detail acceptance.

### Preserve the actual metadata and geometry

Both definitions are version2, `approval.state=candidate`, `by=null`, `at=null`, `function={}`, `biomes=["village"]`, `story.owner=null`, `blocks_move=true` and `blocks_shots=true`. They have no declared role, numerical clearance, required/forbidden relations or size class; `audit.eastward_ref=null`. None of those gaps is filled by this document. Do not change the grain station's different shot-blocking choice to match them.

| Contract | Handcart | Sack group |
| --- | --- | --- |
| PNG canvas / exact variant foot, art texels | [114,84] / [57,80] | [60,66] / [30,62] |
| Metadata canvas `size_cells` | [5,4] | [3,3] |
| Continuous `collision.rect`, **world px** | [-11,-8,22,8] | [-7,-8,14,8] |
| Existing `props.entry` collision conversion, **art texels**, static arithmetic | [-33,-24,66,24] | [-21,-24,42,24] |
| Declared footprint cells relative to foot | [-2,-1], [-1,-1], [0,-1], [1,-1] | [-1,-1], [0,-1] |
| Snap / z-sort | `cell` / `foot` | `cell` / `foot` |
| Shadow metadata | `cast_shadow.shape=baked`, `contact_ao=true` | `cast_shadow.shape=baked`, `contact_ao=true` |

Use metadata-derived entries via the existing `props.entry` API, blob `8fd407ff82f2964c862d5b810c67b5e004bba2a6`. It yields **no added live shadow** for `shape=baked`; the old image/shadow provenance is not a newly measured shadow in this yard. Do not synthesize ellipse radii or a contact-AO pass. The mixed live-grain/baked-source/Moss-lighting issue in [visual feedback6533683754](https://github.com/rempemat-eng/appify/pull/403#issuecomment-6533683754) remains open.

Existing `cell` snap admits half-cell X and full-cell Y. For the next proposed diagnostic select **whole-cell X/Y anchors** for these two bindings, while leaving the source snap unchanged. Static rectangle arithmetic exposes a receiving caveat: sacks at half-X phase +4 world px span columns -1,0,+1, whereas their current declared footprint covers only -1,0. This is not an executed validator failure or a fix. If half-X sacks are needed, first request the exact `game/kit/pieces/prop/crossroads_sacks.json` reservation and a separate receiving proof; do not silently change it or weaken the checker. The handcart's four declared columns cover its continuous rectangle at both X phases. No new clearance value or physics rule is invented.

For a reviewable **future synthetic fixture proposal only**, the two bindings can be named as below. These entries are not written into #406's frozen fixture and have not been validated, composed or approved:

| Instance ID | Piece / variant | Proposed foot, art texels | Relationship to unchanged H2 context |
| --- | --- | --- | --- |
| `yard_handcart` | `crossroads_handcart` / `handcart` | [696,312] | On the north side of the loading approach; visible shafts/wheel/load retained |
| `yard_grain_storage` | `crossroads_sacks` / `sacks_12` | [432,384] | West of the scale, in a compact goods group rather than dispersed across the public band |

Those anchors are whole24-texel cells. Their declared ground cells fall on the existing worn-yard rows; that is static fixture lookup, not a physical/overlap/clearance pass. Keep existing scale foot [552,384], south comparison-worker foot [552,432], east loading approach rows13–17 and public route rows19–21 as the baseline relationships to review. Actual worker/loading movement, occlusion, complete collider coverage and route access must be checked by the separately allocated receiving owner. No new minimum distance follows from the proposed spacing. The smithy stays a smithy; neither its identity nor these goods creates a mill.

### Source provenance, existing reuse inventory and retained craft findings

`game/zones/crossroads/kit.json`, blob `16330cf48fed673b28c001eec56601dd4caeb09c` (24853B, density3), explicitly binds source objects `handcart`/kind `cart` and `sacks_12`/kind `sacks` to the above PNGs and negative offsets [-57,-80] / [-30,-62]. Their **old source-zone positions** [708,792] / [804,192] are provenance, not new receiving coordinates. `cond=null` for both; no quest gate is invented.

The existing generator source `scripts/art/native/village.py`, blob `78f5e5c48602242d26a52f2e0ce9dbd37610d999`, supplies `p_cart` through `PROPS['cart']`, and `p_sacks_hd` through `PROPS_HD['sacks']` at density3. Its drawing code describes rails/nails/shafts/wheel/load and cloth volume/weave/folds/tied necks. `scripts/art/native/town.py` blob `fedd255dcffc57aa42c7668de6c80ef1e7a17f58` is the existing town consumer; `seed_props.py` blob `649e84b12690e763615e3b0ffcb46b6a0de815f7` records the source intake. These are source references, not a fresh generation or reproduction claim; no seed or regenerated bytes are invented. No generator or palette changes.

The read existing [Y40 readiness inventory](https://github.com/rempemat-eng/appify/blob/fe00d9b147e051ea372f96a917175c907db6db6c/docs/codex/prop-readiness-inventory.md), blob `e50b7680ae255e8bff2c3ea70d4f3a3776b7c1cd`, already lists these exact two candidate IDs/PNG bindings, missing role/clearance and no current approved pieces. Its legacy ledger has zero exact-path joins to the current132 candidate PNG paths; a legacy KEEP name does not approve this reuse. [Y45 regional reuse](https://github.com/rempemat-eng/appify/blob/d6c9beeb8d473bef519c936f06fea37b444eb29d/docs/codex/regional-prop-reuse.md), blob `3193822623654c75f4223a903c2e0ffa400e9e09`, likewise distinguishes drawn equivalents from receiving approval. No trough/crate control or inventory is rebuilt here.

The exact existing catalogue records match the inspected PNG hashes and retain contrary detail evidence:

| Record at5dd | Git blob | Stored findings, **not rerun** |
| --- | --- | --- |
| `art/catalogue/crossroads/handcart.json` | `fbb7fc539bd99171ff7ae400ca5f9838b96985f6` | 25Oct: detail ratio0.671, `detail_bar.passed=false`; agent verdict pending |
| `art/catalogue/crossroads/sacks_12.json` | `1903d4dd18aa63991ecc93a9b31f46ed736f2233` | 26Oct: ratio0.509, `detail_bar.passed=false`, outline finding40%; historical agent pass on #296 is a separate recorded judgement |

Their catalogue `status=pass` does not erase `detail_bar.passed=false`, grant kit approval, establish current Eastward matched-height acceptance or justify shipping. No new tone/shape/palette count is claimed. `size-guide.md` blob `71886a3597f9fa434b73cddc698578bed01ee7ae` gives handcart and sack size guidance; the existing group canvas is not a single sack's height or its ground footprint. Use unchanged Moss74 at native density3 for the later visual comparison, with the existing official market-table selection as functional-clustering context. Matched native period/adult/object/detail counts and Y12 remain outstanding. Any source-art correction requires a separately named exact-file reservation; do not become a second painter under this document scope.

### Minimal later receiving delta, held for lead allocation

The exact four runtime bindings above are absent from #4063e7's immutable84-file / 2553526B `INPUTS` closure. Adding only those four under a separately reviewed receiving revision would add **6620B**, yielding **88 files / 2560146B**, before any additional receiving changes. This is input-size arithmetic, not measured duty usage or a new complete-closure/fit pass. The catalogue/inventory/generator citations above explain provenance; they are not extra runtime imports. Keep each file's100644 mode and actual input bytes. Preserve fixture, baseline source/receiver history, private natural root and source/input guards; shared `props/index.json` stays unchanged. No full painter rerun is needed to obtain these already committed goods PNGs.

Next owner is the lead: review this exact one-document child, then explicitly reserve the minimal **existing #406 receiver reuse** needed for these metadata-derived entries, four input pins/sparse paths and a candidate fixture change. Preserve the actual H2 image/results as baseline; do not retarget its old execution or rebuild the controller/framework. Separately state whether/how retained H2 grain outputs may be consumed in the new invocation, with exact bytes/provenance and guards; this document does not grant artifact transfer or another grain draw. Any future composition needs a NEW bounded GO and reviewed resources/closure. This step allocates neither code edits nor a runtime command.

Ground noise is **not solved** here. Calmer ground, shadow consistency, worker-facing-equipment pose/context and the official same-height detail/Y12/Matt decisions remain separately scoped work. Goods only supply related functional clustering, while public walking and loading access must stay clear. No new game rules, inventory economy, characters, production placement, approval promotion, Ready or merge.

**This continuation's actual checks:** stdlib JSON/text/header/hash/metadata/source-path inspection and viewing the two existing native PNGs; source-only diff/whitespace/genuine-history/full-other-leaf/immutable readback proof is recorded with the HANDOFF. No painter/project imports, project validators/tests, draw/render/engine/install/dependency/job/executionref/full gates. Historical successful H2 is retained evidence, not a fresh run on the documentation child.

## Historical prototype source-only record — original5dd text below

The following record is preserved as the 16:30 source-only prototype checkpoint. Later H2 and the current reuse binding above supersede its then-current output/next-action wording; original scope, failures and evidence are not relabelled.

Owner `rivet`; task `Y36/grain-scale-prototype-r1`; source-only GO [6527386774](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6527386774), ASSIGN [6527621051](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6527621051), separate ACK [6527621460](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6527621460). Manual source reservation ends at HANDOFF or 2026-10-30 17:15 UTC. No execution reservation.

This is one new MyGame candidate, with ready and loaded **visual** states. The three source files do not supply generated PNGs, editor registration, a receiving scene, measured art quality or approval. `function` is empty; variants create no payment, stock, quest, unlock, interaction or economy. Candidate status is required by the dispatch; the explicit NOT GENERATED notes prevent it being mistaken for finished art.

## Exact source and scope

Genuine parent: PR #377 `724662fa4edb4f37673856c6e78fe5f60a7fc9c1`, tree `aa6570168eecaae854eab4f072661a8c6521d4e3`; branch `codex/rivet-crossroads-grain-scale`, Draft stacked on `codex/waterfront-props`. Authority read on current main `885b45ea4d6fd8cd2246d90903b8cebbba2705b4`, including AGENTS, handover and development plan. This review is not a replacement for that authority or the source review of #377/#400.

Only new files: `scripts/art/kit/crossroads_grain_scale.py`, `game/kit/pieces/prop/crossroads_grain_scale.json`, and this note. All 139 open PR filename inventories were read before ASSIGN: zero errors and zero overlaps with these paths. Recheck newer #149 claims before publication. Preserve every inherited leaf, including old painters and four waterfront sprites. No fixture/index work is repeated. Existing #377/#375/#302/#400, Y12, runtime, full-gate and Matt-review holds remain.

The native API is reused, not rebuilt:

| Read source at the parent | Blob | Use |
| --- | --- | --- |
| `scripts/art/kit/settlement_props.py` | `c51b9b53fb836675d305d02029c0070ae7703a1d` | Existing integer-texel `Pixel` drawing API |
| `scripts/art/native/palette.py` | `7685bc30fa29bf2c6fe87cfdc4e2ecae2f908b28` | Existing palette ramps; no palette edits |
| `game/kit/schema/piece.schema.json` | `fd61e5d29ca017e3f3796a013c86fc0afe58dc16` | Actual field names and unit descriptions |
| `game/assets/characters/moss/manifest.json` | `0840eda370a71247ce76a4f90f48bb4c59058704` | Native character comparison anchor |

The inherited schema identifier is retained verbatim for compatibility. No schema, shared index, catalogue, generated scene, production zone, package, Player or save file changes. Existing cart, trough, sacks, hay, barrel, anvil, grindstone, noticeboard, woodpile, stall and bench are not redrawn. Grain is a small pan fill belonging to this station, not a second sack or grain catalogue.

## Receiving purpose and pixel plan

The [settlement study](https://chatgpt.com/library?file_id=libfile_b30bed8af740819199558691c451d410&account_id=personal), all nine pages read, places Crossroads in a 17th–early-19th-century market/mill-town vocabulary: connected market widening, functional frontages, deep plots and rear service courts. This station belongs to a mill-yard or grain-court edge beside its work frontage. That is an authored design inference, not historical proof of this exact apparatus, accepted Crossroads terrain, or permission to move the map.

The first complete visual goal is one native play-camera frontage/yard vignette. Keep the public walking band continuous, a worker approach on the south and a loading approach on the east; neither may be fenced in by decorative equipment. Use existing approved/intaken receiving context, after its exact source/approval has been checked. Do not silently promote a candidate or invent numeric clearances. No such scene is authored or run in this batch.

All coordinates below are **authored source choices**, not decoded-image measurements. Density is 3 art texels/world pixel; one native cell is 24 art texels = 8 world pixels.

| Feature | Source plan | Review purpose / remaining evidence |
| --- | --- | --- |
| Canvas / anchor | 168×144 art texels; foot (84,132); 7×6 canvas cells | Same anchor in both variants; opaque bounds NOT MEASURED |
| Moss comparison | Manifest idle/S frame 3 bounds [62,63,100,137], height 74; sheet frame [480,0,160,144], foot [80,136] | Existing packed-bounds arithmetic, not a decoded or new runtime measurement; target label 72 must not replace 74 |
| Tabletop / front | Back edge y77; loading lip y93; apron to y101 | Top/back height above foot 55 art texels, about 0.74 Moss heights; table must read as usable equipment |
| Timber support | Rear feet near (43,118)/(113,118), front feet near (53,131)/(125,131) | Four legs, ties, two diagonal braces and corner straps meet their supports; do not read as floating boards |
| Balance | One rigid equal-arm beam about (85,45), endpoints x49/x121 | Ready level at y45/y45; loaded tilts y51/y39; bolted mast and gusset carry load |
| Pans / measures | Ready rim y66/y66; loaded y73/y62 | Hanging stays, rim, bowl front and underside; loaded grain and counterweight distinguish visual state |
| Source envelope | Lowest loaded beam end y39 before stroke width; foot y132 | Roughly 93 art texels above foot (1.26 Moss heights); stroke/opaque envelope still needs actual measurement |
| Ground blocker | Rect [-16,-8,32,8] **world px**, relative to foot | 96×24 art-texel rectangular ground envelope; no walk-under opening |
| Footprint | X offsets -2 through +2, Y -1 | Conservative five-cell union for allowed X phases; whole-cell phase occupies four rect columns, half-cell phase five |
| Live cast shadow | Ellipse size [16,3], dir [2,1] **world px** | Proposed renderer context, not baked into the sprite or visually passed |

`cell` snap uses the existing whole/half-cell X and whole-cell Y contract; half-cell Y is not added. The conservative footprint is distinct from the large image canvas. Dry earth/rock surface bindings and route/water exclusions are candidate metadata only. Collision, snap, overlap, receiving and approval gates have not been executed. No new physical-validator claim follows from this source arithmetic.

Timber uses connected top/front/side planes and dark underside/apron joints; sparse grain follows planks. Iron has a broad mid plane, cool recess, upper-left rim and restricted bright wear at the pivot/bolts. The grain fill uses existing clay ramps. Loading-lip scuffs and floor-contact wear have a cause; no random speckle or blanket noise. Existing `timber`, `timber_cool`, `iron`, `clay` ramps only. No imagegen, bitmap import, smoothing or new colours. The source is deterministic in intent; byte reproducibility is NOT RUN.

## Official Eastward comparison choice and precise gap

Read the official publisher-supplied [Steam Eastward page](https://store.steampowered.com/app/977880/Eastward/?l=english) and inspected its actual screenshot images outside Git. The selected [market screenshot](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_ddd76431b1df70e234494c92370e2391680c98ef.1920x1080.jpg?t=1782290198) shows continuous shop counters/canopies and foreground work/display tables with public circulation between them. Retrieved JPEG: 594858 bytes, SHA256 `bf709bd60afbb1551010ff80f499b5c5fa72b79c7e77a93cf65eda83f51442c5`.

Proposed **new raw-image selection**: [575,690,740,820] in that 1920×1080 screenshot, covering the left foreground pot-display table and its visible support/front. Supporting frontage band: [630,370,1690,515], with dialogue/occlusion excluded from any later count. These are selection rectangles, not pre-existing crop IDs, measured native crops or grain-scale matches. Use the table's support, top/front/underside material planes and street relationship for comparison. No matching grain balance was found in the six official screenshots inspected.

Matching-height comparison remains a precise gap: this market image's native presentation scale and a suitable unobscured adult-height reference have not been measured. Its raw crop cannot be treated as native texels. Existing `scripts/art/eastward_study.py` records screenshot `01` (different image `ss_5d50545b49db3a8502666b4195d2fabd0e31a29d`) at 3×, but that is not evidence that this market image has the same period. The old `01-adult` crop belongs to its recorded Octopia image `13`; do not relabel it as this market object or invent a shared-frame match.

Before art acceptance: resolve a traceable native object/adult crop pair, match that object's height to the new prop/Moss context, then report actual 16×16 tone/shape/dressing counts under the existing comparison procedure, with occluded patches excluded and denominators shown. **No crop extraction, native period measurement, same-height comparison or detail counts were executed here.** `audit.eastward_ref` stays null; the raw selection above is a reference choice with a gap, not a passed audit. Web search returned an empty tool error twice; the official Steam page and images were instead retrieved directly read-only. Third-party bytes stay outside Git.

## One later bounded paint → composition allocation

Lead reviews the committed three-file source first. The following is a resource request/plan, **not permission or evidence of execution**:

1. Allocate one CPU, the existing Python/Pillow/NumPy environment (no install/download), an isolated exact-head checkout and fresh owned scratch output directories. No engine, bake, full raster, CI gate or shared index generation. First draw invocation: `python3 -B -m scripts.art.kit.crossroads_grain_scale --out RUN/first`. Expected authored filenames are exactly `crossroads_grain_scale_ready.png` and `crossroads_grain_scale_loaded.png`. No other piece is generated.
2. The writer refuses a nonempty evidence directory. If separately included in that bounded GO, use `--out RUN/repro` for the same two states and compare actual PNG bytes/hashes with the first directory. Record actual size, alpha bounds, palette membership, anchor, collision/foot phases and schema/receiving boundary outcomes on the exact source. No skipped check is a pass. Keep old #377 and #388 controls frozen; no replay of unrelated controls.
3. Under that same explicit allocation's reviewed composition boundary, use the existing native compositor and approved/intaken frontage/yard resources; allocate no new scene, zone, shared index or art direction. Produce **one labelled receiving preview** at native play-camera scale with Moss idle/S frame 3, public route, south worker side, east loading side, feet/cast-shadow context and the source-state label. Choose one station state in the representative vignette; a supplemental two-state inspection strip is diagnostic only. If valid context or a matching reference is unavailable, report the exact resource gap instead of constructing a fake finished town.
4. Label any image `Y36 grain-scale candidate — synthetic receiving context — NOT Crossroads layout acceptance — Matt review required`, with exact head, generating command, state and resources. The official raw selection/matching gap must remain visible beside the evidence. Only a later explicit publication allocation may add the two approved output paths to the task; these three source files do not authorize binary publication.

Output targets after that separate authorization: `game/kit/props/art/crossroads_grain_scale_ready.png` and `game/kit/props/art/crossroads_grain_scale_loaded.png`. They are absent now. No source-only metadata pass can settle shadow/material/scale craft or Matt approval. An elapsed lease or enabled schedule grants no runtime or competing-writer authority.

## Validation record and next action

This batch permits only stdlib AST parsing, JSON parsing, static source/field/unit inspection, integer footprint arithmetic, whitespace and Git scope/history/readback proof. A partial checkout is used with an intact inherited Git index; absent working-tree base files must never be staged as deletions. Stage only the three explicit new paths; compare the resulting tree and every inherited leaf to the real parent before/after remote publication. Record exact head/tree in the Draft and #149 HANDOFF. Actual permitted static checks: Python stdlib AST parse and JSON parse passed; constants/variant/anchor/candidate/empty-function contracts passed; authored rectangle arithmetic gives 4/5 occupied columns at X phases 0/4 world px and a five-cell union; three paths are absent at the parent; whitespace checks passed. `git diff --cached --check` passed and staged name/status contains exactly these three additions. These are source checks, not test or art passes.

NOT RUN: painter/module imports, project schema or placement validators, tests, PNG generation/reproduction, pixel/alpha/palette measurements, comparison counts, controller, engine/import/build/bake/render, dependencies, execution jobs/refs, `npm run verify`, `npm run check:art-repro`, kit/Godot/full gates. No Ready, merge or art approval. Next action: lead source review, then a separately bounded actual paint → representative composition GO with exact resources and permitted publication paths.
