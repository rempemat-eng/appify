# Crossroads grain-weighing station — source review

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
