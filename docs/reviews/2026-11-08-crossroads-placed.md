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
