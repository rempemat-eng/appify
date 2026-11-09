# Crossroads placed assets: detail audit (8 Nov)

Matt, 8 Nov: only independently reviewed art may be placed. The review gate (draft #439, `claude-a/review-gate` at 9366301b) refuses 112 placed assets on main whose reviewer verdict is `pending`. This audit covers 35 Crossroads assets that no open PR changes, judged on main's bytes by a detail-auditor that drew none of them.

**Result: 12 pass, 23 fail.** A fail keeps the asset refused until it is redrawn and reviewed again.

## What was reviewed and how

- Commit: `claude-a/review-gate` at 9366301b (main's art bytes). Every PNG's sha256 matched its record; none was stale.
- Calibration first: `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>`: recall 38 of 38; false positives 5 on 6 clean screens and 29 on 22 clean props. `calibration_results.json` was reverted afterwards.
- Asset gate: `npm run review:asset -- <ref>` on all 35, then `--record`. All 35 detector results pass (no blocker or fault findings). The verdicts below come from the checklist, worked part by part on 4x to 14x nearest-neighbour crops on neutral grey.
- Eastward comparison: official shots kept local, brought to native 640 x 360 and scaled x1.37 (54 to 74 px a character) with nearest neighbour: shot 17 fence [305, 177, 450, 218], bale [120, 165, 200, 215], churns [135, 47, 162, 112], rocks [460, 165, 550, 250] and the yard bed and path [0, 150, 320, 260]; shot 13 lamp [375, 20, 415, 125] and pot [410, 155, 470, 220].
- Context: the forge fire and chimney smoke strips were composited on `smithy.png` at their positions in `crossroads.tscn`.
- Dither check: every asset was scanned for a 1-texel checker in alpha and in colour. Only `crater_smoke` has one.

## Verdicts

| Asset | Verdict | Bar | Main reason |
| --- | --- | --- | --- |
| beds_dug | fail | 0.92 | rails: stamped tick "rope" grain, flat dot nails; one seedling stamp; outlined dirt pad |
| beds_scorched | fail | 0.95 | the same frames, unburnt, with sticker char marks; 1-texel stalks |
| coal_34 | fail | 0.61 | flat bin front; grey "stone" coal overhangs the bin |
| crater_smoke | fail | 0.56 | 1-texel alpha checker over the upper plume |
| crates_30 | pass | 0.79 | polish: slate bar sticker, flat knots, square top boards |
| crates_32 | pass | 0.78 | as crates_30 |
| fence_0 to fence_5 | pass (6) | 0.71 to 0.76 | polish: "+" knot glyph, identical rust drips |
| fern_rubble | fail | 0.79 | stamped three-plane stone blocks, flat slates |
| flower_tub_9, 10, 26, 27, 38, 59, 60 | fail (7) | 0.60 to 0.79 | body blotch noise, no rim or inner wall, blocky planting |
| fx/chimney_smoke_8 | pass | n/a | polish: perfect-disc puffs in a column |
| fx/forge_fire_8 | pass | 0.80 | polish: tongues as an even comb |
| hay_19, hay_20 | fail (2) | 0.75, 0.76 | flat front and side, terrazzo top, twine does not turn |
| kit_lantern_24, kit_lantern_25 | pass (2) | 0.60 | identical to the kit garden lantern; polish: flat iron frame |
| lantern_dark | fail | 0.47 | flat plinth slabs with three green squares (glyph) |
| lantern_lit | fail | 0.49 | as lantern_dark, plus cold blue lit glass |
| smithy_rubble | fail | 0.59 | rubble stone build; a beam cut by the left edge |
| square_rubble_a | fail | 0.60 | rubble stone build; beams cut by three edges |
| square_rubble_b | fail | 0.62 | rubble stone build |
| stall | fail | 0.64 | recoloured scale-pattern produce, overlay rectangle, menu glyph |
| waystone | fail | 0.48 | stamped diagonal dash lattice, flat base and moss |
| woodpile_11, woodpile_33 | fail (2) | 0.69, 0.67 | one stamped log end, see-through gaps |

Groups judged together because their pictures share a build: `kit_lantern_24` and `kit_lantern_25` are byte-identical (same sha256), and both are pixel-identical to the kit garden lantern. `lantern_dark` and `lantern_lit` differ only in the glass (510 texels). The six fences, the seven tubs, the two hay bales, the two woodpiles, the two crates and the four rubble piles each share one generator build.

## Findings

Crops are in the auditor's scratch folder (not committed). Boxes are in art px.

1. **Bed rails: stamped grain and dot nails.** `beds_dug`, `beds_scorched`, top rails (for example [8, 20, 120, 26]) and lower rails ([8, 70, 120, 77]). Fault. Every top rail carries the same diagonal tick every ~4.5 texels, so it reads as twisted rope. The lower rails carry flat grey 2 x 2 nail squares on the dark seam, with no lit pixel, which is Matt's "dot nails" (calibration C1). There are no butt joints on boards 130 texels long. Fix: grain as irregular 2 to 4 px streaks along each board, butt joints every 14 to 30 px with a nail head beside each (dark, a lit pixel above it, set in the board), and each board on one of three sibling ramps (house-style 5, Wood).
2. **Bed seedlings stamped.** `beds_dug` [140, 25, 245, 70] and [12, 95, 120, 140]. Polish. One 5 x 3 seedling is stamped in an exact 4 x 10 grid. Fix: three variants, with ±1 texel jitter in position and size.
3. **Outlined dirt pad.** `beds_dug`, `beds_scorched`, the pad's west, north and east edges. Fault. The dirt round the beds is a rectangle closed by a straight dark line, but ground meeting ground is never outlined (eastward-edges 4.1, 5.1). Fix: drop the line and fray the pad edge in a 2 to 3 px band with crumbs, as on the Eastward 17 yard.
4. **Scorched beds: the frames did not burn.** `beds_scorched`, char marks such as [58, 20, 67, 24]. Fault. The char marks are flat one-tone slate pills laid over unchanged grain (stickers), and the rest of the frame is as new. The burnt stalks are 1-texel dark lines. Fix: char the rail tops and ends in clusters (timber 0 to 1 with a lit crack line), blister and split the boards nearest the ash, and draw 2-texel stalks with a lit west edge.
5. **Coal bin.** `coal_34`, bin front [6, 37, 55, 57] and heap [1, 14, 59, 37]. Fault. The front is a flat tan rectangle split by three dark lines. The heap is brown-grey and striped, so it reads as stone, and it overhangs the bin on both sides with nothing under it. Fix: boards 4 to 5 px with a lip and joints, a lit top rim with an inner wall, coal as near-black lumps (slate 0 to 2) with blue-violet glints in pairs heaped inside the rim, and a few lumps spilled at the foot.
6. **Smoke dither.** `crater_smoke`, the upper plume [119, 75, 180, 122]. Fault. 1,615 of the 2,804 opaque texels form a 1-texel alpha checker, the same dither earlier audits found at `square_puddles`' damp margins. House-style 4 allows dither only on ground, as the 2 x 2 checker, and never on a sprite; at 1x it turns to grey mush. Fix: fade the plume with fewer, smaller, lighter detached puffs, or give the whole upper plume a real partial alpha. The lower puffs pass.
7. **Flower tubs: undrawn body, no rim.** `flower_tub_*`, body [6, 36, 47, 54] and planting [5, 23, 48, 36]. Fault. The body is two flat bands with random dark-red worm blotches, so there are no staves, boards or clay features. The sweep's cluster-noise reading on 26, 59 and 60 is confirmed by eye, and the other four tubs have the same build. There is no rim lip or inner wall: the soil shows only as two brown corners. The planting is a blocky slab of rectangles with no clumps and no shade where it hangs over the rim. Fix: a planked trough (three boards of 4 to 5 px, lit lip, joints, nail heads, iron corner straps) or terracotta with a rolled rim (lit top lip at tone 4 to 5, a dark under-rim band, lime bloom drips). Add a 2 px soil band with the inner wall lit on the far side, foliage as 3 to 5 leaf clumps (light caps, dark U, 1 to 2 px shade on the rim), and flowers as 2 to 3 texel clusters with one lit and one dark texel. Compared with the Eastward 13 pot, which has rims, banding and a highlight.
8. **Hay bales: flat front.** `hay_19`, `hay_20`, front [6, 38, 51, 62], side [51, 38, 60, 62] and top [6, 7, 60, 38]. Fault. The front and east side are one-tone fills with a few lone specks. The top is a terrazzo of 1-texel dashes. The twine runs straight over the top and front without turning at the edge, the corners are hard, and the loose straw is two flat 1-texel bars. Fix (Eastward 17 bale): the front in horizontal straw bands of 3 to 4 tones in 2 to 3 px clusters, a lit top-front edge, corners knocked off one step, the twine pressed in (a dark line with a lit lip) and turning over the edge, and straw tufts in clusters at the foot.
9. **Lamp plinth.** `lantern_dark`, `lantern_lit`, plinth [19, 190, 65, 222]. Fault. The plinth now has a top plane and an east chamfer (calibration C15 is answered), but its faces are flat fills with one lit line. Three evenly spaced flat green 4 x 4 squares on the front read as indicator lights: the glyph Matt flagged on the old waystone (C7). Fix: dressed stone with a bevel lit on the top-left arris, a chipped corner, a course joint, and moss as leaf 2 and 3 clusters in the joint under the upper slab (a 2 px cap over a 4 px band).
10. **Cold lit glass.** `lantern_lit`, glass [27, 74, 56, 97]. Fault. The lit glass is pale blue with a white oval. Glass lit from inside uses the lamp glow ramp: lamp 1 along the frame's shadow, brightening towards the bottom middle (house-style 5, Glass), the warm lamplight of the house look.
11. **Rubble stones stamped and flat.** `fern_rubble`, `smithy_rubble`, `square_rubble_a`, `square_rubble_b`, every stone. Fault. Each stone is the same chamfered octagonal block in three flat planes, repeated at different sizes, with no chips, cracks, cluster texture or mortar. The slates are flat blue bars. Fix: rubble from the cottages' own stone recipe: irregular lumps with a lit crown, body and dark underside in 4 to 5 tones and sibling clusters, broken faces showing mortar (stone_cool 0 to 1), a chipped corner each, and slates with a lit top edge, a 1 to 2 px edge face and a break line (Eastward 17 rocks).
12. **Rubble cut by the frame.** `smithy_rubble` (left edge, 8 opaque texels on column 0) and `square_rubble_a` (left, right and bottom edges, 7, 7 and 6 texels). Fault. Beams and a slate run off the picture's edge and end in a straight cut. Fix: keep every piece inside the frame, with at least 1 texel of margin.
13. **Stall produce, awning and signs.** `stall`, produce [21, 86, 128, 100], awning [8, 31, 130, 66], board [99, 128, 120, 158], sack [13, 132, 34, 158]. Fault. All four crates hold one chevron scale pattern, recoloured, which reads as scales. A hard-edged darker rectangle lies across the awning's middle like an overlay. The awning is a flat front-on sheet with no top plane or fold bands. The menu board is a navy block with three cream bars (a UI glyph), and the sack is a two-tone disc. Fix: produce as individual round items (lit cap, dark underside, a glint) heaped above the crate rims; awning folds as vertical bands (tones 4, 3, 2, 1) with a top plane rising back and the shade under the valance as a ramp step; chalk lettering as broken 1 to 2 px strokes in a framed board; a sack with a tied neck and fold bands. The counter boards, nails with rust and posts pass.
14. **Waystone stamped.** `waystone`, face [27, 28, 68, 110] and base [17, 118, 72, 135]. Fault. The face texture is one diagonal 4-texel dash stamped on a regular lattice. The base is the lamp plinth's flat build, and the moss is flat two-tone blobs. The form (lit west face, mid front, dark east side) and the carved rune pass. Fix (Eastward 17 rocks): lichen and weathering as sibling clusters, a few real cracks with a lit lip, chipped arrises, the base as dressed stone with a bevel and a chip, and moss in clumps with lit caps and dark undersides in the base joint.
15. **Woodpile stamped and see-through.** `woodpile_11`, `woodpile_33`, the stack [6, 31, 70, 72]. Fault. All eleven log ends are one stamp in a 4-3-4 lattice, with concentric target shading lit at the centre instead of the upper left. The gaps between them are transparent, so the ground shows through the stack. The sweep's cluster-noise reading is rejected as noise, because the texture is clean: the fault is repetition and see-through. Fix: three or four log sizes plus split halves (lit split face, dark bark arc), end grain lit upper left with one ring arc and a radial check, a dark bark rim, and a dark back wall (timber 0 to 1) behind the gaps.
16. **Crates.** `crates_30`, `crates_32`. Polish. The flat 8 x 2 slate bar on the lower front reads as a sticker (make it a hand hole: a dark recess with a lit lower lip). Knots are one-tone dark blocks (add a lit rim), and the top boards read as square tiles (run them front to back with gaps).
17. **Fences.** `fence_0` to `fence_5`. Polish. Knots are a "+" glyph (draw an oval 3 x 2 knot with a lit lower rim), and every nail drips the same 1-texel rust streak (vary the length, and give some nails none).
18. **Kit lantern.** `kit_lantern_24`, `kit_lantern_25`. Polish. The iron frame is two flat slate tones (add a lit west edge and a glint on the cap ring), and the hook only touches the arm's corner (hang it from a bracket under the arm).
19. **Chimney smoke.** `fx/chimney_smoke_8`. Polish. Every puff is a perfect disc in a vertical column, like pearls. Fix: lobe the outlines, let the puffs overlap and drift east, and fade the last frame by shrinking.
20. **Forge fire.** `fx/forge_fire_8`. Polish. The tongues stand as an evenly spaced comb of similar spikes. Fix: vary their widths, merge their bases, let them lean and lick from frame to frame, and darken the tips.

## Per-part notes on the passes

- **crates_30 and crates_32:**
  - Upper and lower crate fronts: framed planks with lit stiles, a diagonal brace lit on its top edge, grain streaks and knots, and corner irons with a lit pixel.
  - Lower crate's top plane: it shows in front of the upper crate, so the stack reads.
  - East: in shade.
  - Outline: closed, dark brown.
  - Compared with the Eastward 17 churns.
- **fence_0 to fence_5:**
  - Post caps: a lit top plane.
  - Shafts: lit west, dark east.
  - Rails: a lit top, body and dark last row, with grain.
  - Joints: occlusion where the rails cross the posts.
  - Nails: dark heads with a lit pixel and rust.
  - Compared with the Eastward 17 fence: as an open structure, judged by eye on its solid parts (house-style 7).
  - Shared build: the variants differ only in grain and knots.
- **kit_lantern_24 and kit_lantern_25:**
  - Post: lit west, dark east, with joints.
  - Arm and hook: a capped arm and a hook.
  - Cap: three tones.
  - Glass: lit from inside, with a flame.
  - Ivy: lit and dark leaves.
  - Pixel-identical to the kit garden lantern, the lamp of Matt's 26 Oct style note ("the lamp and bench are exactly the style i'm going for").
- **fx/chimney_smoke_8 and fx/forge_fire_8:** both are judged as effects strips. Each frame reads as smoke or flame at its position on the smithy, the puffs are lit at the upper left, and the fire has an edge, a body and a pale core at its base.

## False positives

12 detector findings were rejected. The records keep the detectors' own `status`, and each `reviewer.note` names the rejected finding.

- 10 × `detail.light`:
  - `kit_lantern_24` and `kit_lantern_25`: glowing glass.
  - `forge_fire_8`: the flame is the light source.
  - `flower_tub_10`: its east face is in shade.
  - `flower_tub_38`: flowers on the east side.
  - `beds_scorched`: random ash clusters.
  - `smithy_rubble` and `square_rubble_b`: a slate on the east side.
  - `stall`: the red stripes.
  - `waystone`: the moss.
- 2 × `detail.outline` (`crater_smoke`, `chimney_smoke_8`): smoke takes no outline (house-style 2).

The 33 `detail.bar` polish findings are measurements and are kept as evidence. Only the beds reach 0.9; by eye the fences and crates meet the bar for their kind.

## Not checked

- Night tint, the 1x game view on a phone, and the composed zone. This was the asset gate, not the scene gate.
- Animation timing of the two fx strips, beyond their frames and fps.
- The shadow layers (`*_shadow`), which are separate records outside this batch.

## Tool note

`npm run review:asset` crashed on the fences because their sibling `kit/fence` had no rendered picture (`siblings()` renders kit pictures only for style anchors). Rendering the kit first with `npm run review:asset -- --kit kit/bench` worked around it.

## Round 2 (PR #447, 9 Nov)

Draft #447 (`claude-a/crossroads-prop-fixes` at 99aff0a3) redraws the 23 props that failed above and regenerates the 8 pictures whose cast shadows moved with them (`ground` and seven `*_shadow` layers). This round audits all 31 on those bytes. The auditor drew none of them.

**Result: 17 pass, 14 fail.** The beds, coal bin, smoke, rubble and woodpiles answer their findings; the hay bales, flower tubs, lamp plinths, stall and waystone do not. The shadow layers pass. The ground's delta passes, but the picture as a whole fails on its old burnt-lot faults (owned by #421).

This round is filed here, beside the fix list it answers, rather than in `2026-11-04-act1-props.md` (the Act 1 props, which holds no Crossroads fix list).

### What was reviewed and how (round 2)

- Commit 99aff0a3. Every PNG's sha256 matched its record.
- Calibration first: `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>`. Recall was 39 of 39. False positives were 5 on 6 clean screens and 21 on 22 clean props. `calibration_results.json` was reverted afterwards.
- Asset gate: `python3 -m scripts.review.assets <31 refs> --record`. The detectors found 0 blockers and 0 faults on all 31 and left the records byte-identical. The detail bars below match the painter's numbers.
- Verdicts come from the checklist, worked part by part on 8x to 16x nearest-neighbour crops on neutral grey. Each crop shows the previous bytes (HEAD~2, 56d4b288) beside the new ones.
- Measurements per asset:
  - tones (palette count);
  - the largest one-tone 4-connected region;
  - border texels;
  - the alpha checker;
  - repetition between siblings.
- Eastward comparison: official shots, kept local, brought to the native grid with `core.to_native` and scaled ×1.37 with nearest neighbour (54 to 74 px a character). The same boxes as round 1 were used:
  - shot 17: bale [120,165,200,215], churns [135,47,162,112], rocks [460,165,550,250] and yard bed [0,150,320,260];
  - shot 13: lamp [375,20,415,125] and the hanging bell [410,155,470,220].
- Ground: the before and after pictures were diffed. 757 texels changed in 25 places, and the two largest were checked at 5x. The whole picture was looked at once at 0.5x, then the burnt lot at [1500,1100,1820,1260] and the west road at [0,840,320,1000] at 3x. This is not a 24-cell scene-gate pass.

### Verdicts (round 2)

| Asset | Verdict | Bar before → after | Measured | Reason |
| --- | --- | --- | --- | --- |
| beds_dug | pass | 0.92 → 0.99 | 29 tones; 0 border texels | sibling boards, joints, grain, jittered seedlings, frayed pad; polish XR2-B1 nails |
| beds_scorched | pass | 0.95 → 1.00 | 32 tones; stalks 2 texels lit west | char in clusters with lit cracks; polish XR2-B1, XR2-B2 |
| coal_34 | pass | 0.61 → 1.01 | 29 tones | boards with lip, near-black coal inside the rim with glints; polish nails, spill |
| crater_smoke | pass | 0.56 → 0.56 | 0 checker texels of 3,832; 46 alpha levels | the checker replaced by banded partial alpha |
| fern_rubble | pass | 0.79 → 0.72 | 27 tones; largest flat 70 texels; 0 border | irregular lit lumps, chips, mortar, slates with edge face |
| smithy_rubble | pass | 0.59 → 0.83 | 34 tones; 0 border (was 8 on column 0) | as fern_rubble |
| square_rubble_a | pass | 0.60 → 0.76 | 32 tones; 0 border (was 7/7/6) | as fern_rubble |
| square_rubble_b | pass | 0.62 → 0.83 | 32 tones | as fern_rubble |
| woodpile_11 | pass | 0.69 → 0.81 | 16 tones; dark back 438 texels | varied logs, end grain lit upper left, no see-through; polish XR2-P1 |
| woodpile_33 | pass | 0.67 → 0.84 | 14 tones | as woodpile_11 |
| beds_dug_shadow, beds_scorched_shadow | pass (2) | n/a | 302 x 33 (was 305 x 33) | east-and-down throw, two tones down, one-tone rim |
| fern_rubble_shadow, smithy_rubble_shadow, square_rubble_a_shadow | pass (3) | n/a | 105 x 15, 121 x 17, 108 x 15 | follow the new outlines |
| lantern_dark_shadow, lantern_lit_shadow | pass (2) | n/a | 109 x 42 | follow the new plinth |
| hay_19 | **fail** | 0.75 → 0.53 | 14 tones; one-tone top 378 texels | flat paper slab, ruled 1-texel straw, flat east end, no bale volume |
| hay_20 | **fail** | 0.76 → 0.55 | 14 tones; one-tone top 336 texels | as hay_19 |
| flower_tub_9, 10, 26, 27, 38, 59, 60 | **fail (7)** | 0.60–0.79 → 0.62–0.71 | 24–29 tones; flat body band 114–116 texels; bodies differ by ≤ 38 texels | two flat body bands, ruled lime-bloom stamp, corner square, no soil, disc clumps |
| lantern_dark | **fail** | 0.47 → 0.52 | 27 tones | plinth: flat slab bands, one-tone top planes, pill moss |
| lantern_lit | **fail** | 0.49 → 0.57 | 27 tones | the same plinth; the warm lit glass passes |
| stall | **fail** | 0.64 → 0.58 | 53 tones; one-tone counter band 416 texels | chalk board glyph, flat awning top plane, dot nails |
| waystone | **fail** | 0.48 → 0.48 | 25 tones; one-tone face 1,357 texels | terrazzo specks, diagonal slashes, pill moss, flat base |
| ground | **fail** | n/a | 757 texels changed, all at prop feet | the delta passes; the burnt lots keep the #288 S5 stipple |

### Findings and fix lists (round 2)

Crops are in the auditor's scratch folder (not committed). Boxes are in art px. Each fix list is also in the asset's `reviewer.fix_list`.

1. **Hay bales still flat** (`hay_19`, `hay_20`). Fault. Round 1 finding 8 is not answered.
   - What is wrong:
     - The top is one tone (#f8d79c) over 336 to 378 texels ([24,11,41,38]).
     - Straw on the top and the front is ruled 1-texel-tall dashes.
     - The east end is a flat mauve rectangle of about 7 x 20.
     - The twine is a straight dark line with a white line beside it. It does not sink or turn at the edge.
     - The corners are knocked off by one texel only, and there is no rounded volume.
     - The whole bale uses 14 tones. The bar fell from 0.75 to 0.53 and 0.55 (14.4 tones and 28 shapes a patch, against Eastward's 27 and 50).
     - Beside the Eastward 17 bale at ×1.37, ours reads as a pale paper box.
   - Fixes:
     - **XR2-H1:** round the top-front and top-east edges over 2 to 3 rows (tone 5 at the arris, falling to 3) and knock each corner off 2 steps.
     - **XR2-H2:** draw straw as strand clusters of 2 to 3 texels in 3 to 4 tones, running along the top and across the cut ends, with a few strands breaking the silhouette.
     - **XR2-H3:** draw the east end as a cut face (dark tufts, a core shadow), and the front in horizontal bands of 3 to 4 tones in 2 to 3 px clusters.
     - **XR2-H4:** press the twine in (a dark line with a lit lip 1 texel off it), sinking into the straw and turning over the top-front edge.
2. **Flower tubs: the body is still undrawn** (`flower_tub_*`). Fault.
   - Answered: the rolled rim, the under-rim band and the leaf clumps with a dark U.
   - Still wrong:
     - The body is two flat bands split by one diagonal terminator (a one-tone region of 114 texels at [9,39,35,44]).
     - The lime bloom is a ruled 1-texel line with two drips. It is the same stamp in the same place on all seven tubs, whose bodies differ by only 14 to 38 texels.
     - Every tub has a flat dark 3 x 3 square in its lower-right corner.
     - No soil band or far inner wall shows.
     - The leaf clumps are smooth two-tone discs.
     - The bar fell on four of the seven.
   - Fixes:
     - **XR2-T1:** shade the body as a vessel (lit west at tone 4, body at 3, dark east at 1 to 2), and break every one-tone run over 40 texels with clay pits and a hairline crack with a lit lip.
     - **XR2-T2:** draw the lime bloom as irregular pale clusters under the rim, varied on every tub.
     - **XR2-T3:** remove the corner square, or make it a chip with a lit lip.
     - **XR2-T4:** show a 2 px soil band and the far inner wall, lit, between the clumps.
     - **XR2-T5:** draw leaf clumps with scallops and dark pockets in 3 to 4 tones, and give each tub its own planting.
3. **Lamp plinth still plain** (`lantern_dark`, `lantern_lit`, plinth [19,190,65,222]). Fault. Round 1 finding 9 is half answered.
   - Answered: the green squares are gone, and a joint, chips and faint mottling are in.
   - Still wrong:
     - Each slab's front is one wide flat band.
     - The top planes are one tone, and the east faces are flat.
     - The moss is two smooth two-tone pills, which read as stickers (the C15 plain plinth).
   - Answered and passing: finding 10 (the lit glass is now warm, in the lamp ramp).
   - Fixes:
     - **XR2-L1:** draw each slab as dressed stone. Give it a distinct top plane (tone 4) with a lit 1 px front-left arris, a bevel step, a front face in 3 to 4 tones with sibling clusters, a core shadow on the east face, and chips with a lit lip at two corners.
     - **XR2-L2:** draw the moss as leaf 2 and 3 clusters in the joint under the upper slab (a 2 px lit cap over a ragged 3 to 4 px band with a dark underside).
     - **XR2-L3** (`lantern_dark`, polish): drop the white flame-shaped oval from the unlit glass.
4. **Stall** (`stall`). Fault.
   - Answered: the overlay rectangle is gone, the produce is round items heaped above the rims, and the sack has a tied neck.
   - Still wrong:
     - The chalk board ([99,128,120,158]) is a navy block holding a grid of cream 2 x 2 squares and dashes: still a UI glyph.
     - Each awning stripe's top plane is one tone over about 12 x 10 texels.
     - The counter nails are one-tone 2 x 2 navy squares (dot nails, C1).
     - The counter's top front is a one-tone band of 104 x 4 texels (#966a3d, 416 texels).
     - The bar fell from 0.64 to 0.58.
   - Fixes:
     - **XR2-S1:** write the lettering as broken 1 to 2 px chalk strokes in two tones (words and a price).
     - **XR2-S2:** give each stripe's top plane 2 to 3 tones of fold shading rising back.
     - **XR2-S3:** give each nail head a lit texel, set it at a board joint, and vary the rust.
     - **XR2-S4:** put grain streaks and a dark under-lip row on the counter's top front.
5. **Waystone** (`waystone`, face [27,28,68,110], base [17,118,72,135]). Fault. Round 1 finding 14 is not answered.
   - What is wrong:
     - The front face is one tone (#8e8782) over 1,357 texels ([39,31,64,120]), with lone 2 to 3 texel specks spread evenly (a terrazzo).
     - The "tooling" and "cracks" are diagonal 1-texel slashes again.
     - There is no lichen.
     - The moss is pills on the cap and the base.
     - The base is a flat slab with one joint.
     - The bar is unchanged at 0.48.
     - The form and the rune still pass.
   - Fixes:
     - **XR2-W1:** draw weathering and lichen clusters (3 to 6 texels, two lichen tones, sibling greys), spread unevenly and denser low and on the north-west. Remove the even specks.
     - **XR2-W2:** replace the slashes with two or three wandering cracks, each with a lit lip.
     - **XR2-W3:** chip the arrises on the west edge and the cap, each chip with a lit lip.
     - **XR2-W4:** draw moss as clumps in the base joint and on the cap, and the base as dressed stone (as XR2-L1).
6. **Ground** (`ground`). Fault (not of this PR).
   - The PR's 757 changed texels are contact and cast shadows that follow the new prop outlines (for example [1175,680,1283,710] and [1648,782,1726,808]), and they pass.
   - The picture was never passed, and its queue entry already names faults that remain. The burnt lots (for example [1500,1100,1820,1260]) are an even stipple of small dark discs, with flat one-tone char blobs and one-tone dark beams, and the scorch fringe is flat 2 to 3 tone blobs (#288 S5).
   - Fixes:
     - **XR2-G1:** draw the burnt lots' soil marks in drifts (`softedge.soil_marks`), the char as clusters with lit edges and the beams with a lit top edge and grain, and fray the fringe in 2 to 3 px clusters.
     - **XR2-G2:** the #421 redraw needs a full scene-gate pass (24 cells) before it may be placed.

### Polish on the passes (round 2)

- **XR2-B1** (`beds_dug`, `beds_scorched`, `coal_34`): each nail head is a one-tone 2 x 2 navy square (#2e2943) with no lit texel of its own. The nails now sit beside the butt joints under the boards' lit lip, so house-style 5 is met in letter. Give each head its own lit top-left texel.
- **XR2-B2** (`beds_scorched`): most of the rail length is still sound, bright timber, and the embers are flat 2 x 2 orange squares. Char the inner top edge nearest the ash as a band, and give each ember a bright core.
- **XR2-P1** (`woodpile_11`, `woodpile_33`): the split halves the fix asked for are missing, and a few upper logs sit in the dark back with no log under them. Pack the rows so each log rests on two, and add 2 split halves.
- Rubble: the faces are clean between few marks. Add 2 to 3 lichen or grit clusters per large stone (the bar is 0.72 to 0.83).

### Per-part notes on the passes (round 2)

- **beds_dug** (bar 0.99):
  - Top and lower rails: boards on three sibling ramps, each with a lit lip, a body and a dark last row, grain as 2 to 4 px streaks, and butt joints darker than the boards.
  - Posts: lit west, dark east, with a capped top.
  - Seedlings: three kinds, jittered off the grid.
  - Pad: frays into the lawn in a 2 to 3 px band with no outline.
  - Compared with the Eastward 17 yard bed.
- **beds_scorched** (bar 1.00):
  - Rails: char clusters with lit crack lines and a blistered split board.
  - Ash: clusters in several greys.
  - Stalks: 2 texels, lit west.
- **coal_34** (bar 1.01):
  - Bin: boards with a lip, joints and a lit back rim.
  - Coal: near-black lumps in slate tones 0 to 2 with paired blue-violet glints, inside the rim.
  - The east side is in shade.
- **crater_smoke**: the puffs are lit upper left, overlap and lean east. The fade uses 46 alpha levels in bands, with no checker.
- **Rubble (4)**:
  - Stones: lit crown, body and dark underside in 4 to 5 tones, with chips, mortar crust and sibling clusters.
  - Slates: a lit top edge, a 1 to 2 px edge face and a break line.
  - Beams: lit top edges.
  - Every piece is inside the frame.
  - Compared with the Eastward 17 rocks.
- **Woodpiles (2)**:
  - Rack: a lit top beam with joints, and posts.
  - Logs: four sizes, each with a bark rim, end grain lit upper left, a ring arc and a radial check.
  - Behind: a dark back wall closes the gaps.
- **Shadow layers (7)**: each is the prop's silhouette thrown east and down. The ground steps two tones down its own ramp, with the outer rim one tone down (house-style 6, eastward-edges 7.2).

### False positives (round 2)

13 detector findings were rejected, and each `reviewer.note` names them:

- 6 × `detail.light`:
  - `beds_scorched`: ash and char;
  - `fern_rubble` and `smithy_rubble`: east-lying slates;
  - `woodpile_11` and `woodpile_33`: end-grain rings;
  - `lantern_lit`: its glass is the light source.
- 6 × `detail.cluster_noise`:
  - `beds_dug` and `beds_scorched`: soil ridges;
  - `fern_rubble` and `square_rubble_a`: joints and mortar;
  - `woodpile_11` and `woodpile_33`: end grain.
- 1 × `detail.outline`: `crater_smoke` (smoke takes no outline).

The six tubs' `detail.light` findings were not ruled on and are kept as evidence. The `detail.bar` findings are kept as measurements.

### Gate (round 2)

`python3 -m scripts.review.gate --check` refuses 14 assets (exit 1): the 14 fails, whose fix-queue entries hold the pre-#447 bytes. It prints 17 `ADVISORY` lines for the passes, whose queue entries can now go. This round edits no queue entry. Claude A decides whether to re-queue the 14 failed pictures at their new bytes with the XR2 fix lists, or to hold #447 until they are redrawn.

### Not checked (round 2)

- The composed zone (the scene gate), night tint and the 1x phone view.
- The ground beyond the delta and the two 3x crops above: no 24-cell grid pass.
- Whether the shadow layers line up with their props in `crossroads.tscn`. Only the pictures were compared.

## Round 3 (PR #450, 9 Nov)

Draft #450 (`claude-a/crossroads-props-xr2` at 8c212777) redraws the 13 props that failed round 2 and regenerates the three pictures derived from them (`lantern_dark_shadow`, `lantern_lit_shadow` and `ground`). This round audits those 16 pictures. The auditor drew none of them.

**Result: 5 pass, 11 fail.** The hay bales and the waystone answer their XR2 codes and pass. The two shadow layers pass. The seven tubs, the two lamp plinths and the stall still fail. The ground's delta is correct, but the picture keeps its round 2 fail on the burnt lots (XR2-G1, XR2-G2), which this PR does not touch.

### What was reviewed and how (round 3)

- Commit 8c212777. All 16 PNGs' sha256 matched their records.
- Calibration first: `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>`. Recall was 39 of 39. False positives were 5 on 6 clean screens and 21 on 22 clean props. `calibration_results.json` was reverted afterwards.
- Asset gate: `python3 -m scripts.review.assets <16 refs> --record`. The detectors found 0 blockers and 0 faults, and the records came back byte-identical. The detail bars match the painter's numbers: hay 0.88 and 0.76, tubs 0.70 to 0.86, lanterns 0.57 and 0.61, stall 0.63, waystone 0.58.
- Cluster noise (`python3 -m scripts.review.cluster_noise`) on the old bytes (HEAD~1) and the new:
  - tubs: from 30.6–40.6 % to 39.9–47.1 %, with tub 27 at 47.1 % (its four grid phases give 46 to 47 %), 0.9 points under the 48 % fault line. The painter's "40 to 47 %" is right, except that tub 38 is at 39.9 % and has no finding;
  - hay 39.5 % and 32.3 %, stall 38.2 %, lanterns 34.6 % and 27.5 %, waystone 23.2 %.
- Verdicts come from the checklist, worked part by part on 6x to 14x nearest-neighbour crops on neutral grey. Each crop shows the old bytes beside the new ones. Measured per asset: tones, the largest one-tone 4-connected region, and (on the stall) every nail head's texels.
- Eastward comparison: official shots, kept local, brought to the native grid with `core.to_native` and scaled ×1.37 with nearest neighbour (54 to 74 px a character). Boxes:
  - shot 17: bale [120,165,200,215], churns [135,47,162,112] and rocks [460,165,550,250];
  - shot 13: lamp [375,20,415,125] and the hanging bell [410,155,470,220].
- Placed: the zone composite (`scene.composite`) was built at HEAD~1 and at HEAD. Crops were compared at 2x to 4x round hay_19, tubs 26 and 27, and the lamp.
- Ground: the old and new pictures were diffed. Each changed cluster was mapped to the sprite boxes from `crossroads.tscn`. The bakery lip was looked at 6x and the patch at 912,468 at 10x.
- Art director's read: checked against my own crops.
  - Agreed on the hay, the stall's board, counter and awning, the waystone, and the plinths.
  - On the tubs I partly disagree. At 1x the planting is now clearly different on every tub, and the body has a lit west and a dark east. They still read as box planters with a ruled line, though, and that decides the verdict.

### Verdicts (round 3)

| Asset | Verdict | Bar round 2 → 3 | Measured | Reason |
| --- | --- | --- | --- | --- |
| hay_19 | pass | 0.53 → 0.88 | 19 tones; largest flat 127 texels (was 378); noise 39.5 % | a pillowed straw bale: lit arris band, straw in strand clumps, cut east end, twine pressed in; polish XR3-H1 |
| hay_20 | pass | 0.55 → 0.76 | 17 tones; largest flat 200 texels (was 336); noise 32.3 % | as hay_19; polish XR3-H1 |
| waystone | pass | 0.48 → 0.58 | 30 tones; largest flat 258 texels (was 1,357); noise 23.2 % | stains on sibling ramps, lichen clusters, cracks with lit lips, chipped arrises, moss clumps, dressed base; polish XR3-W1 |
| lantern_dark_shadow | pass | n/a | 5 texels changed | follows the new plinth's west foot |
| lantern_lit_shadow | pass | n/a | 7 texels changed | follows the new plinth's foot |
| flower_tub_9, 10, 26, 27, 38, 59, 60 | **fail (7)** | 0.62–0.71 → 0.71–0.86 | 27–32 tones; largest flat 63–118 texels; noise 39.9–47.1 % | planting fixed; body still banded box, bloom bar, dark corner block, soil slot |
| lantern_dark | **fail** | 0.52 → 0.57 | 26 plinth tones; plinth front one tone over 203 texels (was 192) | slabs flatter than round 2; moss as four equal tufts in a row |
| lantern_lit | **fail** | 0.57 → 0.61 | plinth front one tone over 104 texels | the same plinth; the lit glass passes |
| stall | **fail** | 0.58 → 0.63 | 52 tones; 17 of 17 nail heads one-tone 2 x 2 #2e2943; board field one tone over 281 texels | dot nails (regressed); chalk is glyphs, not words |
| ground | **fail** | n/a | 698 texels changed: 521 at prop feet, 177 lawn scatter | the delta is correct; XR2-G1 and XR2-G2 stay open (#421) |

### Status of the XR2 codes

| Code | Status | Evidence |
| --- | --- | --- |
| XR2-H1 | fixed | a lit band over the top-front arris (3 rows); corners knocked off 3-2-1 |
| XR2-H2 | fixed | strand clumps of 2 to 3 texels in 4 to 5 straw tones; strands break the top and east silhouette. Polish: on the top they read more as mottle than as strands running along the bale (XR3-H1) |
| XR2-H3 | fixed | the east end is darker, with stalk-end tufts and a core shadow; the front is in horizontal courses |
| XR2-H4 | fixed | each twine is a dark groove with a lit lip, breaking at the arris |
| XR2-T1 | partly fixed | the body has a lit west, a body and a dark east, plus a hairline crack with a lit lip and a few pits. But it is drawn in 3 to 4 straight vertical bands under a full-width ruled dark line, and one-tone runs of 63 to 118 texels remain (the code asks for none over 40) |
| XR2-T2 | partly fixed | the length varies from tub to tub, but on most tubs the bloom is still a 2-row bar with drips at rows 38 to 41 (6 to 18 texels a row) |
| XR2-T3 | partly fixed | the 3 x 3 square is now the belly's darkest tone, but it is still a distinct near-black block (a one-tone region of 24 texels of #330216 on tubs 9, 38 and 59) |
| XR2-T4 | partly fixed | a dark 1-row slot with a few clods sits under the rim. There is no 2 px soil band, and no lit far inner wall |
| XR2-T5 | fixed | scalloped, lobed clumps with dark pockets in 3 to 4 tones. Each tub has its own planting |
| XR2-L1 | not fixed | tooling clusters and pocks are in, but the volume is weaker than in round 2. The lower slab's front is one tone over 203 texels on lantern_dark (104 on lantern_lit), the top planes are one row, the lit west end is one column, and the bevel does not read |
| XR2-L2 | partly fixed | the moss is clumps now, but four 4 to 6 texel tufts sit evenly spaced in one row, each with a straight dark underside. At 1x and 2x they read as a dotted green line |
| XR2-L3 | fixed | the unlit glass has a dark cradle and no pale shape |
| XR2-S1 | partly fixed | three rows of broken strokes, one row in a second tone. They are repeated blocky L glyphs on a navy field that is one tone over 281 texels, not words and a price |
| XR2-S2 | fixed | each stripe's top plane is in 3 to 4 tones, with a lit row |
| XR2-S3 | not fixed (regressed) | all 17 nail heads are one-tone 2 x 2 #2e2943 squares with no lit texel; round 2's nails had one (#737078). `village.nail_head` sets the lit texel, but `finish()` calls `tidy()`, which removes it as a lone pixel. These are the dot nails of calibration C1 |
| XR2-S4 | fixed | the counter top is sawn boards with grain streaks, joints and a dark under-lip row. The 416-texel band is gone |
| XR2-W1 | fixed | stains on sibling grey ramps, denser and darker low; grey-green and yellow lichen in clusters of 3 to 6 texels; no even specks on the face |
| XR2-W2 | fixed | two cracks with lit lips replace the slashes. Polish: the east crack reads as a zipper (XR3-W1) |
| XR2-W3 | fixed | the cap is notched and the west arris chipped, with lit lips |
| XR2-W4 | fixed | moss clumps sit in the base joint and on the cap. The base has a lit top plane, a front, a chipped corner and a shaded east end |
| XR2-G1, XR2-G2 | open | out of scope for #450 (owned by #421) |

### Fix lists (round 3)

Each list is also in the asset's `reviewer.fix_list`.

**Flower tubs** (`flower_tub_9`, `10`, `26`, `27`, `38`, `59`, `60`). Fault.

- **XR3-T1:** draw the body as a fired-clay vessel, not banded boards.
  - Let the lit west, body and dark east meet in a soft stepped curve (steps of 2 to 3 texels), not along straight vertical edges.
  - Turn the full-width ruled dark line under the rim into a shadow that thins towards the lit west.
  - Break every one-tone run over 40 texels with sibling-tone clay clusters, not value grain: keep cluster noise at or under 40 %.
- **XR3-T2:** draw the lime bloom as ragged pale clusters of 2 to 4 texels that wander under the rim and down one side, different on every tub. No 2-row bar with drips.
- **XR3-T3:** no distinct near-black block in the lower-right corner. Fade the belly's shade along the base row in 2 tones, and give any chip a lit lip.
- **XR3-T4:** show the soil as a 2 px band with clods between the clumps, with the far inner wall lit 1 to 2 px above it, not a 1-row dark slot.

**Lamp plinths** (`lantern_dark`, `lantern_lit`). Fault.

- **XR3-L1:** give each slab its volume back and keep the tooling:
  - a distinct top plane, 2 to 3 rows deep, in tone 4, with a lit front-left arris;
  - a 1-row bevel step;
  - a lit west end face 2 to 3 columns wide;
  - the front in 3 tones, with no one-tone run over 60 texels;
  - the east face in core shadow;
  - two chips with lit lips.

  Compare with the round 2 plinth (HEAD~1), whose lit top plane and west end read better.
- **XR3-L2:** draw the moss as one or two ragged clumps of different sizes in the joint: a 2 px lit cap over a 3 to 4 px band with a ragged dark underside, placed unevenly. Never four equal tufts in a row.

**Stall** (`stall`). Fault.

- **XR3-S1:** make the nail heads keep their lit texel. `tidy()` strips a lone lit texel, so either draw the light as 2 texels (the head's top row, or an L) or pass the nail heads to `tidy()` as `keep`. Check the output bytes, not the painter. The same function draws the beds' and coal bin's nails (round 2 polish XR2-B1), and their heads are one-tone 2 x 2 #2e2943 too (15 on beds_dug, 5 on coal_34).
- **XR3-S2:** write the chalk board as words and a price:
  - broken 1 to 2 px strokes in varied letter shapes (not repeated L glyphs), in two chalk tones;
  - a faint haze of the second chalk tone smudged over part of the navy field, so the field is not one tone over 281 texels.

**Polish on the passes**

- **XR3-H1** (`hay_19`, `hay_20`): on the top, lay a few clumps end to end along the bale so the straw reads as strands rather than mottle. On hay_20, break the 200-texel lit run on the top's west (#daad54 [6,9,20,35]) with one or two strand clumps.
- **XR3-W1** (`waystone`):
  - The east crack is a straight run of alternating 1 x 2 dark and lit dashes and reads as a zipper. Let it wander and close up into a continuous line with a broken lip.
  - The base front still has evenly spaced 2-texel dark dashes. Group them into two or three wear patches.
  - The cap moss sits on a straight 8-texel dark underline. Make that underline ragged.

### The two side effects

**1. 177 ground texels away from any prop.**

- Verified: 164 texels along the bakery's turf lip (three clusters, x 342–560, y 856–874; 67 of them visible in the composite) and 13 at x 906–924, y 462–480. All 13 are visible.
- The cause is as the painter says. The lawn scatter's tufts and soil marks are drawn from one random stream, and the shade steers how many draws the soil marks take. The new hay and tub shadows change the shade, so every later draw in the stream shifts. `town.py` already draws the lawn twice to keep building edits local, but not prop edits.
- At 6x and 10x the reshuffled texels are the same kind of marks at the same density: blade marks and the edge of a tuft on the bakery lip, and a few texels of the paving's shade at 912,468. There is no new fault, and at 1x the change cannot be seen.
- **Ruling: acceptable for this PR. It does not block #450 and needs no regeneration.** Pixels that move unseen still cost something: they change the composite pin, they add noise to every scene-gate delta, and they hide real changes in the diff.
- So **XR3-G1** (follow-up, not blocking, filed on `ground`'s record): make the scatter local, so that a prop edit cannot move distant ground. Either draw it per cell from a seed of that cell, or extend the twice-drawn lawn (keeping the new draw only round changed objects) from buildings to every static prop. Until then, every prop PR should list the far ground texels it moves, as this one did.

**2. The composite pin.**

- Confirmed: `sha256(scene.composite(load_zone('crossroads')))` is 7cfa360f10c56550125db7e31105a6e769fd3ac8b269d005c4fefc4d2bfe845d with the 16 pictures at HEAD~1, and c9ae22f8e33aafd1491791800c3c5ceaf01d4d454ef8c736103231fc27c5ceca at 8c212777.
- 18,719 composite texels change:
  - 18,354 inside the 13 redrawn props' sprite boxes;
  - 3 inside the lamp shadows' boxes only;
  - 362 elsewhere, all of them ground-delta texels: the hay and tub contact shadows below the boxes, the bakery lip and 912,468.

  This is the painter's 18,357 + 362.
- Of the ground's 698 changed texels, 206 fall inside prop boxes, 362 show elsewhere, and 130 are covered by other sprites.
- Note: at 8c212777, `scripts/review/test_kit_scene_intake.py` still pins 7cfa360f…. This PR does not move the pin. The pin moves to c9ae22f8… when the art is accepted, and that is Claude A's call.

### False positives (round 3)

None were newly rejected. The detectors raised no blocker or fault on the 16 pictures, only polish:

- `detail.bar` on the 13 props, kept as a measurement;
- `detail.cluster_noise` on six tubs, kept as evidence and cited under XR3-T1;
- `detail.light` on `flower_tub_26` (the red read as lit from the right): not ruled on, kept as evidence;
- round 2's rejection of `detail.light` on `lantern_lit`'s glass is carried over in its note.

### Gate (round 3)

`python3 -m scripts.review.gate --check` refuses 11 assets (exit 1):

- the 7 tubs, the 2 lanterns and the stall: failed, and their queue entries hold the pre-#450 bytes;
- `ground`: failed, and its queue entry holds the old bytes.

It prints 3 `ADVISORY` lines, for `hay_19`, `hay_20` and `waystone`: they now pass and can leave the fix queue. The two lamp shadows pass and are not queued.

This round edits no queue entry. Claude A decides whether to:

- re-queue the 11 failed pictures at the #450 bytes with their XR3 fix lists, or
- hold #450 until they are redrawn, or
- split the 5 passes off.

### Not checked (round 3)

- The scene gate (the 24-cell grid), night tint and the 1x phone view in the app.
- The ground outside the 698 changed texels and their surroundings.
- Whether the redrawn props sit correctly on their shadows at every spawn. Only the composite was compared.

## Round 4 (PR #453, 9 Nov)

Draft #453 (`claude-a/crossroads-props-xr3` at 74d275b0) redraws the 10 props that failed round 3 and the two lamp shadows that follow the new plinth. This round audits those 12 pictures. The auditor drew none of them.

**Result: 11 pass, 1 fail.** The seven tubs and the two lamp plinths answer their XR3 codes and pass, with polish. The two shadows pass. The stall fixes its nails, but its board still does not read as words, and two faults that earlier rounds missed (flat counter-front boards and the sack) are now its largest problems.

### What was reviewed and how (round 4)

- Commit 74d275b0, in a fresh worktree. All 12 PNGs' sha256 matched their records. `ground.png`, `kit.json` and `crossroads.tscn` are byte-identical to HEAD~1. Of the PNGs, only these 12 differ.
- Calibration first: `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>`. Recall was 39 of 39. False positives were 5 on 6 clean screens and 21 on 22 clean props. `calibration_results.json` was reverted afterwards.
- Asset gate: `python3 -m scripts.review.assets <12 refs> --record`. The detectors found 0 blockers and 0 faults (polish: `detail.bar` on 8). The records came back byte-identical. A second `--record` after the verdicts kept them.
- Detail bars match the painter's numbers:
  - tubs 9, 10, 26, 27, 38, 59, 60: 0.82, 0.93, 0.86, 0.83, 0.96, 0.80, 0.76 (round 3: 0.77, 0.86, 0.78, 0.74, 0.86, 0.71, 0.85; tub 60 falls 0.85 → 0.76);
  - lanterns 0.61 and 0.64;
  - stall 0.65.
- Cluster noise (`python3 -m scripts.review.cluster_noise`), from round 3 to round 4:
  - tubs 9, 10, 26, 27, 38, 59, 60: 45.0, 43.9, 42.7, 47.1, 39.9, 41.9, 41.0 % → 32.9, 38.3, 36.2, 29.4, 35.6, 29.5, 31.1 %. The painter's "29 to 38 %" is right;
  - lantern_dark 34.6 → 33.2 %, lantern_lit 27.5 → 30.9 %, stall 38.2 → 39.8 %.
- Largest one-tone 4-connected run, per asset:
  - tubs: clay at most 40 texels (tub 59 #ae5a42; the others 37 to 39). The larger runs are leaves (73, 62, 45, 42, 40 texels) in the planting, whose bytes are those of round 3, where it passed (XR2-T5). The painter's claim holds;
  - plinths (y ≥ 190): 47 texels on lantern_dark (was 203) and 46 on lantern_lit (was 104);
  - stall: 226 texels, #8e6242 [68,120,78,154], a counter-front board. Before this PR it was the second-largest run, at the same 226 texels.
- Nail heads: from the output bytes, every navy 2 x 2 head with its colours. There are 16 nail heads, and every one is #2e2943 with one lit #737078 texel (the other two navy clusters the scan found are chalk on the board). The 17th nail, behind the sack, is no longer drawn. `finish(p, line=True, keep=None)`: with the default, `tidy` runs as before, and no other picture's bytes changed.
- Verdicts come from the checklist, worked part by part on 5x to 14x nearest-neighbour crops on neutral grey, with the old bytes (HEAD~1) beside the new. On the plinths I also read a luminance map row by row (y 188–219).
- Eastward comparison: official shots, kept local, brought to the native grid and scaled ×1.37 with nearest neighbour (54 to 74 px a character). Boxes:
  - shot 17: churns [135,47,162,112] and rocks [460,165,550,250];
  - shot 13: lamp [375,20,415,125] and bell [410,155,470,220].

  I also used the painter's comparison sheet (`xr3-eastward-compare-4x.png`).
- Placed: `scene.composite(load_zone('crossroads'))` was built at HEAD~1 and at HEAD. I compared a crop at 1x (x 650–1250, y 520–990), the tubs and stall at 2x, and the lamp foot with its shadow at 5x.
- Art director's read, checked against my own crops:
  - Agreed: the tubs read as bellied clay vessels; the dark ruled line is gone; the plinths are dressed slabs with moss in clumps; the lantern bar is held down by the iron post; the bodies are slightly blotchy (polish).
  - Not agreed: "the board is legible". At 1x and 2x, NEW reads as ".EV" or "AEV", and PLUM as "PLUH". Only "3d" reads. The ruled line has also partly come back as a light taupe soil band (polish).
  - The sack and the counter boards: I agree they are unchanged, and I rule both as faults.

### Verdicts (round 4)

| Asset | Verdict | Bar round 3 → 4 | Measured | Reason |
| --- | --- | --- | --- | --- |
| flower_tub_9, 10, 26, 27, 38, 59, 60 | pass (7) | 0.71–0.86 → 0.76–0.96 | 29–34 tones; largest clay run 37–40 texels (was 63–118); noise 29.4–38.3 % (was 39.9–47.1 %) | a bellied clay vessel with lit west, belly and dark east on stepped curves; bloom clusters; no corner block; polish XR4-T1, T2 |
| lantern_dark | pass | 0.57 → 0.61 | largest plinth run 47 texels (was 203); top planes 2 and 3 rows; east core shadow 3–4 columns | dressed slabs with joints, chipped stepped corners, two unequal moss clumps; polish XR4-L1 |
| lantern_lit | pass | 0.61 → 0.64 | largest plinth run 46 texels (was 104) | as lantern_dark; the lit glass passes; polish XR4-L1 |
| lantern_dark_shadow | pass | n/a | 37 texels changed, all in x 1–59, y 3–24 | follows the new plinth foot; east and down, 2 tones |
| lantern_lit_shadow | pass | n/a | 39 texels changed, all in x 9–59, y 3–24 | as lantern_dark_shadow |
| stall | **fail** | 0.63 → 0.65 | 54 tones; 16 of 16 nails lit; board navy run gone; 6 front boards one tone over 135–226 texels | the board does not read as words; flat counter-front boards; the sack reads as a jar or a lamp globe |

### Status of the XR3 codes

| Code | Status | Evidence |
| --- | --- | --- |
| XR3-T1 | fixed | The ruled dark line under the rim is gone. Lit west, body and shade meet on curves that step down 2–3 texels; the belly turns under, deeper east. Clay runs ≤ 40 texels. Noise ≤ 38.3 %. |
| XR3-T2 | fixed | The bloom is in ragged 2–4 texel pale clusters under the rim and down one side, different on each tub. There is no bar with drips. Polish: the clusters are grey rather than chalky (XR4-T2). |
| XR3-T3 | fixed | No near-black block. The largest blob with L < 40 in the lower-right quadrant falls from 31 texels to 13, and that is the outline. The base row is a 2-tone reflected light. |
| XR3-T4 | partly fixed | A 2-row soil band (rows 31–32) with lit clods sits under a lit far wall (row 30). But it runs straight across the full width in light taupe (#8d715a, #73584a, #7a6250), and at 4x–5x it reads as a thin grey rule under the rim. Polish severity: the structure is right, the tone is not (XR4-T1). |
| XR3-L1 | fixed | Top planes are 2 rows (upper slab) and 3 rows (lower slab) in the light tone. There is a lit west column, the front is in 3 tones as dressed blocks with 1 px joints, the east end is a 3–4 column core shadow, and the corners are chipped and stepped. Largest run 47 texels (limit 60). The bevel is weak (XR4-L1). |
| XR3-L2 | fixed | One larger clump west and one smaller one east, each a lit cap over a ragged dark underside, placed unevenly. |
| XR3-S1 | fixed | 16 of 16 heads carry a lit #737078 texel in the output bytes, through `finish(keep=...)`. The nails of `beds_dug` and `coal_34` (XR2-B1, polish) are not in this PR and remain one-tone. |
| XR3-S2 | partly fixed | The field is in sibling patches with a chalk haze (no 281-texel run), and the strokes use two chalk tones. But the N is broken into dots, the 3-column M reads as H ("PLUH"), and the PLUM line touches the frame on both sides. Only "3d" reads at 1x (XR4-S1). |

### The counter-front boards (not in the fix list)

The painter asked for a ruling on the 226-texel run. It is a fault. The run is not new: at HEAD~1 the same board was one tone over the same 226 texels, behind the 281-texel board field. Rounds 1 to 3 missed it.

- Six boards are one tone over 135 to 226 texels each: #8e6242 226 and 170, #865840 191 and 135, #774a29 180, and #966a3d 151. The west post is one tone over 96 (#8e6242 [17,71,20,108]).
- Each is a flat fill with a few long dark streaks. There is no lit edge and no grain in a second or third tone.
- The plinths are held to a limit of 60 texels and the tubs to 40. These boards are 3 to 5 times that.

### Fix lists (round 4)

Each list is also in the asset's `reviewer.fix_list`.

**Stall** (`stall`). Fault.

- **XR4-S1:** make the board read at 1x.
  - Draw the N with a full diagonal, not dots.
  - Give the M 4 to 5 columns, or use a two-line layout (PLUMS / 3d) with a 1 px margin to the frame. Alternatively, replace the word with a drawn plum and the price.
  - Check it at 1x and 2x in the composite.
- **XR4-S2:** grain each counter-front board.
  - 3 tones, with a lit west edge column and a dark east joint.
  - Grain streaks that wander and end.
  - No one-tone run over 60 texels (now 6 boards at 135–226; the largest is #8e6242 [68,120,78,154]).
- **XR4-S3:** redraw the sack as burlap.
  - A mid tan, below the awning's cream.
  - Weave in 2-texel clusters.
  - A slumped base with a contact shadow, and the neck tied with twine.
  - It must not be the brightest value on the stall. Today it reads as a jar or a lamp globe.
- **XR4-S4** (polish): the awning's hanging stripe faces are each one tone over 79 to 82 texels (y 43–66). Add a fold shade down one side of each stripe.

**Polish on the passes**

- **XR4-T1** (the 7 tubs): the soil band reads as a straight grey rule.
  - Darken it to a warm earth in the clay shade's hue (#5b3f3a, with #73584a only for the clods).
  - Break its lower edge where leaves hang over the near rim.
  - Let its depth vary between 1 and 2 rows along the tub.
- **XR4-T2** (the 7 tubs):
  - Merge the body's sibling cells into fewer, larger patches that follow the belly (3 to 4 across, not 6 to 8). At 6x and above they read as blotchy.
  - Make the lime bloom chalkier, lighter than the clay's lit tone, so it does not read as grey smudges.
- **XR4-L1** (`lantern_dark`, `lantern_lit`):
  - Each dressed block is close to one tone, with even 2-texel dashes for tooling. Group the tooling into one or two wear patches a block.
  - Add a 1-row lit bevel along the lower slab's top-front arris.
  - Darken the contact row under the lower slab by one step. Placed, the plinth's blocks are as light as the paving and partly merge with it.
- The lantern bar (0.61 and 0.64) is low because the iron post, unchanged since it passed in round 1, is most of the picture. That is a measurement, not a fault. I compared the post with the Eastward 13 lamp: it has a lit stripe, a dark side, mouldings and a collar, and it reads.

### The composite pin

- `sha256(scene.composite(load_zone('crossroads')))`:
  - with the 12 pictures at HEAD~1: c9ae22f8e33aafd1491791800c3c5ceaf01d4d454ef8c736103231fc27c5ceca;
  - at 74d275b0: 233832ce7f4e8ef805d5c071d72f70f0767c8f85bb4f1b8aa2df156afa72d7b0.
- 4,233 composite texels change, all 4,233 inside the boxes of the 12 sprites (the 10 redrawn props and the 2 shadows). None change elsewhere. This confirms the painter's numbers.
- The ground does not change, so XR3-G1 is not exercised.
- `scripts/review/test_kit_scene_intake.py` still pins c9ae22f8…. Moving the pin to 233832ce… when the art is accepted is Claude A's call.

### False positives (round 4)

None were rejected. The detectors raised only `detail.bar` (polish) on tubs 9, 26, 27, 59 and 60, both lanterns and the stall, and I kept each as a measurement. Round 2's rejection of `detail.light` on `lantern_lit`'s glass is carried over in its note.

### Gate (round 4)

`python3 -m scripts.review.gate --check` refuses 1 asset (exit 1): `stall`. It is failed, and its queue entry holds the pre-#453 bytes.

It prints 9 `ADVISORY` lines: the seven tubs and the two lanterns now pass and can leave the fix queue. The two lamp shadows pass and are not queued.

This round edits no queue entry. Claude A decides whether to:

- re-queue the stall at the #453 bytes with XR4-S1 to S4, or
- hold #453 until the stall is redrawn.

### Not checked (round 4)

- The scene gate (the 24-cell grid), the night tint and the 1x phone view in the app.
- Whether the plinth sits on its shadow at every spawn. Only the composite was compared.
- `beds_dug` and `coal_34`: their one-tone nails (XR2-B1) are outside this PR.
