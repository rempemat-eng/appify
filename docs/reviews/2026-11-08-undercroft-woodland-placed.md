# Detail audit: placed Undercroft and woodland assets (8 Nov)

Matt ruled on 8 Nov that only independently reviewed art may be placed. Draft PR #439 (`claude-a/review-gate`) makes the gate refuse placed assets whose reviewer verdict is still `pending`. This batch is 23 of the 58 that no open PR changes, reviewed on main's bytes by a detail-auditor that drew none of them.

**Result: 3 pass, 20 fail.** The three woodland props pass, the forest bench (a style anchor) included. Every Undercroft piece fails: each is better than the round Matt flagged on 25 Oct (U1 to U7), but none reaches Eastward's detail at the same character height, and several still show the faults he named (flat targets, a flat channel line, flat boulders with moss hats, a terrazzo of specks).

## What was reviewed

- **Base:** `origin/claude-a/review-gate` at `9366301b` (main `e1ff077c` plus the gate). All 23 sha256 match their records; none was stale.
- **Assets:** `woodland/forest_bench`, `mossy_log`, `stump`; `undercroft/ground`, `channel_lit`, `plate_up`, `plate_down`, `lever_up`, `lever_down`, `seal_slab`, `seal_sunk`, `stump_nw`, `stump_se`, `shard`, `torch`, `urn_seal`, `roots_corridor`, `roots_hall`, `rubble_chamber`, `rubble_corridor`, `rubble_hall`, `rubble_seal`, `cairn_alcove`.
- **Commands:** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>` (recall 38 of 38; false positives 5 on 6 clean screens and 29 on 22 clean props; `calibration_results.json` not committed). `npm run review:asset -- <ref>` for every asset, then `--record`. I opened every sheet in `artifacts/review/assets/`, and also zoomed each picture at 5x to 10x on the Undercroft floor colour (59, 52, 72) or the woodland grass, because the sheet's 4x view shrinks large pieces. To judge the states as pairs in place, I composed the Undercroft's four rooms from `kit.json` (foot plus offset, y-sorted, torch frame 0) in both puzzle states.
- **Eastward, at x1.37 nearest neighbour** (54 native px a person against our 74), from the local official shots (never committed): shot 17 bench (410,15,472,55), shot 12 bench (180,200,248,235), shot 06 dungeon floor (160,190,240,250), and the fire column and floor beside it (330,0,420,60), plus the crystal pillars (230,205,370,290 and 160,85,215,175).

## Per-asset verdicts

| Asset                      | Gate (detectors)        | Bar         | Verdict  | Findings                                    |
| -------------------------- | ----------------------- | ----------- | -------- | ------------------------------------------- |
| woodland/forest_bench      | pass, 1 polish          | 0.61        | **pass** | B-1, B-2 (polish)                           |
| woodland/mossy_log         | pass, 2 polish          | 0.83        | **pass** | M-1 (polish); detail.light rejected         |
| woodland/stump             | pass, none              | 0.91        | **pass** | S-1 (polish)                                |
| undercroft/ground          | pass, none              | ground band | fail     | G-1 to G-3 fault, G-4 to G-6 polish         |
| undercroft/channel_lit     | pass, none              | (too thin)  | fail     | C-1                                         |
| undercroft/plate_up        | pass, 1 polish          | 0.61        | fail     | P-1, P-2, P-3                               |
| undercroft/plate_down      | pass, 1 polish          | 0.53        | fail     | P-1, P-2, P-3                               |
| undercroft/lever_up        | pass, 1 polish          | 0.81        | fail     | L-1, L-2, L-3                               |
| undercroft/lever_down      | pass, 1 polish          | 0.76        | fail     | L-1, L-2, L-3                               |
| undercroft/seal_slab       | pass, 1 polish          | 0.55        | fail     | SE-1, SE-2, SE-3                            |
| undercroft/seal_sunk       | pass, 1 polish          | 0.65        | fail     | SE-1, SE-2, SE-3                            |
| undercroft/stump_nw        | pass, 1 polish          | 0.46        | fail     | ST-1, ST-2, ST-3                            |
| undercroft/stump_se        | pass, 1 polish          | 0.46        | fail     | ST-1, ST-2, ST-3                            |
| undercroft/shard           | pass, 1 polish          | 0.49        | fail     | SH-1                                        |
| undercroft/torch           | pass, 2 polish          | 0.46        | fail     | T-1, T-2; detail.light rejected             |
| undercroft/urn_seal        | **fail**, detail.volume | 0.85        | fail     | UR-1 to UR-4; detail.volume partly rejected |
| undercroft/roots_corridor  | pass, 1 polish          | 0.60        | fail     | RT-1, RT-2, RT-3                            |
| undercroft/roots_hall      | pass, 1 polish          | 0.69        | fail     | RT-1, RT-2, RT-3                            |
| undercroft/rubble_chamber  | pass, 1 polish          | 0.52        | fail     | R-1, R-2, R-3                               |
| undercroft/rubble_corridor | pass, 2 polish          | 0.56        | fail     | R-1, R-2, R-3                               |
| undercroft/rubble_hall     | pass, 2 polish          | 0.62        | fail     | R-1 to R-4                                  |
| undercroft/rubble_seal     | pass, 2 polish          | 0.66        | fail     | R-1, R-2, R-3                               |
| undercroft/cairn_alcove    | pass, 2 polish          | 0.72        | fail     | CA-1 to CA-5                                |

`urn_seal` was recorded as a detector pass on 26 Oct. Re-recorded on the same bytes with today's detectors, it trips `detail.volume`, so its `status` is now `fail`.

## Findings

Crops are in the sheets `artifacts/review/assets/<zone>__<name>.png`, which are regenerated by the commands above and not committed. Boxes are in the asset's art px.

### Woodland (pass)

- **B-1, forest_bench, the bolt heads (polish).** Each bolt is a 1 x 2 dark slot with no lit pixel above it. Fix: draw a dark head with a lit pixel above, as the wood recipe in house-style.md says.
- **B-2, forest_bench, under the seat (polish).** The 3 to 4 rows under the seat are one flat tone across 90 px. Fix: a tone-1 band with the seat's front board in tone 2 above it, and the iron frame's cross-rail showing at the ends.
- Checklist for forest_bench: the iron posts read as cylinders (lit west column, dark east) with a cap, collar and foot. The four boards have a lit lip, grain streaks of 2 to 4 px, sibling changes at the butt joints and an outline in the timber's edge tone. The light comes from the upper left. At x1.37 it carries what Eastward's yard bench (shot 17) does: 18.6 tones and 30.7 shapes a patch, against that bench's 17.9 and 33.6. It is the same drawing as the `kit/bench` anchor. The detail bar of 0.61 is measured against the band's mean, which the lamp (39 tones), the pot and the shot 12 bench with two people sitting on it (43.7) raise. Pass.
- **M-1, mossy_log, the bark-loss patches (polish).** The two pale patches at the lower west are two-tone stickers. Fix: a dark lip along their north edge and one grain line inside.
- **S-1, stump, the rim (polish).** The cream rim runs right round the cut ellipse, including the south-east lip, which sits in shade. Fix: drop the rim to the timber's tone 3 on that side.

### Undercroft ground (fail)

Grid log (2304 x 648, eight cells of 576 x 324 viewed at 2x, plus 4x crops of the arcade and floor):

- r0c0 (room 1 north): the arcade has voussoirs, brick infill, a cap and a ledge. There are two warm floor pools, moss wedges at the wall base and specks on every flag.
- r1c0 (room 1 south, west door): the floor darkens southward in whole-flag steps. Pale stain blotches, the south rim, and a strip of courses past the void at the picture's foot.
- r0c1 (room 2 north): the arcade and two zigzag wall roots, with void above.
- r1c1 (room 2 south): two pools, the south rim and the corner return. The void band and the strip of courses again.
- r0c2 (room 3 north): the arcade with one wall root, two pools, and the wall pier in the doorway to room 4.
- r1c2 (room 3 south): the unlit channel groove (dark north side, lit south lip), the south falloff, and the door returns.
- r0c3 (room 4 north): the arcade with a blocked bay (the cairn alcove's place) and two pools, one a cool violet.
- r1c3 (room 4 south): the south falloff and the rim.

Findings:

- **G-1, floor light pools, e.g. room 1 at 130-300 x 190-300 (fault).** All eight pools are posterised contour blotches of 5 to 6 hard-edged bands. Their edges are ragged and the flag joints run straight through them, so they read like a contour map. Eastward's light (shot 06, beside the fire column) falls off in a few soft steps. Fix: one radial falloff per pool in at most 3 steps that follow the flags (whole flags or half flags a tone up), with no ragged band edges.
- **G-2, every flag (fault).** Every flag carries evenly scattered 2 x 2 pale specks: a terrazzo of specks, the grain Matt flagged in U1. Fix: remove them, and texture the flags with 2 to 4 px sibling clusters and the odd chip at a corner.
- **G-3, every flag (fault).** The flags are flat fields cut by 1 px red-brown joints, with no lit north-west lip and no dark south-east lip. Every hex flag in Eastward's dungeon floor (shot 06, 160,190,240,250) has its own lit rim and dark lower edge. Fix: a tone-4 north and west lip and a tone-2 south and east lip on each flag, with joints at the stone's tone 1.
- **G-4, the arcade round each torch, e.g. x 120-200 and 440-520 at y 60-140 (polish).** The wall's light is a translucent disc with a hard edge laid over the masonry. Fix: let it fall off over two steps along the courses.
- **G-5, wall roots at x 400 and 520 (room 2) and 1550 (room 3) (polish).** They are zigzag bars in 2 to 3 tones. Fix: the volume of the floor roots (a lit top, a dark underside, overlap).
- **G-6, the arcade at x 186, 324 and 462 (polish).** 1 px pale vertical seams run through the courses at the bay joints. Fix: stagger the courses across the joint.
- Kept: occlusion along the north wall base (43 L at the base against 68 to 79 L a quarter H south), falloff to the south, and the arcade's construction. The ground detectors' pass (calm and drawn) stands. G-1 to G-3 are what they do not measure.

### Undercroft pieces (fail)

- **C-1, channel_lit, the whole bar (fault).** It is still a flat line, as in Matt's U6: a 10 px bar of one pastel violet with a lighter streak, cut into 9 equal segments by brass dividers. It has no glow structure and puts no light on the groove's lips. Fix: deep violet at the groove walls rising to a near-white core streak broken into uneven lengths, the south lip and one row of floor on either side a tone up, and the brass dividers shaded (lit top, dark east side).
- **P-1, plate_up and plate_down, the inner panel (fault).** The cross is a flat one-tone plus sign: dark when up, flat violet when down. It reads as a UI glyph, Matt's U7 flat target. Fix: carve it as a groove with a dark north and west wall and a lit south and east lip. When it is lit, give it a glow ramp from deep violet edges to a near-white centre, with one tone of spill on the panel.
- **P-2, plates, the frame (fault).** The frame is a terrazzo of evenly scattered tan 2 x 2 specks with 1 px crack strokes. Fix: sibling clusters, two or three cracks that start at chips, and chipped corners.
- **P-3, plates, the moss (polish).** The moss is single-tone dark green dashes set in a row along the base. Fix: clumps with a lit cap, only in the low joints.
- The plates as a pair: up shows the slab proud with its front face, and down shows the north lip's shadow in the recess. Both read right.
- **L-1, levers, the grip (fault).** The grip is a lumpy blob with ink pixels inside. Fix: a turned grip 5 to 6 px across with a highlight band left of centre, a dark east side, an end-cap ellipse and a ferrule at the rod.
- **L-2, levers, the face plate (fault).** The face plate is one flat blue-grey square with 1 px rivets. Fix: a sheen (lighter at the upper left), a lit top edge and a dark lower edge, and rivets as a lit head over a dark pixel.
- **L-3, levers, the housing (polish).** It has the same tan specks as the plates.
- The levers as a pair: the pivot slot is the same in both states (x 25-28, y 38-40), and the rod throws from up-west to down-east.
- **SE-1, seal_slab and seal_sunk, every slab top (fault).** Each top carries a glossy diagonal light stripe. That is the round 3 answer review-agents.md ("Ground planes") rules wrong: flags do not shine. Fix: calm tops, each with a lit north-west lip and a dark south-east lip and sibling clusters.
- **SE-2, seals (fault).** Tan 2 x 2 terrazzo specks sit on every slab and course.
- **SE-3, seals, the ring-and-cross glyph (fault).** It is one flat tone, Matt's U7 flat target. Fix: carve it, as in P-1, and give the lit state a glow ramp.
- The seals as a pair: the raised tops sit 120 px above the sunk ones, with the front face in courses below. The glyph glows when raised and is dark when sunk, and the three-slab layout matches (54 and 52 px wide).
- **ST-1, stump_nw and stump_se, the break (fault).** The pillars are better than U4: the shaft now has cylinder shading and flutes. But the break is only a jagged silhouette, with no fracture surface and no top plane. Eastward's pillars (shot 06, 230,205,370,290, at x1.37) show their top face. Fix: a rough top plane inside the column's ellipse, with lit facets to the north-west and pits and a dark rim to the south-east.
- **ST-2, pillars, the plinth (fault).** The plinth is two flat tones (top and front), with no chips, no edge light and no occlusion where the shaft meets it.
- **ST-3, pillars (polish).** stump_nw and stump_se are nearly the same drawing. Vary the break and the debris.
- **SH-1, shard (fault).** The shard is a two-face prism with no cap facet and no edge highlights, and its sparkles are single white pixels. Eastward's crystals (shot 06) show a lit cap and lit edges. Fix: a cap facet (tone 5 edge, tone 4 plane), lit edges on the faces towards the light, 2 or 3 inner facet lines, sparkles in pairs, a 1 px edge-tone outline and a faint glow at its foot.
- **T-1, torch, the sconce (fault).** The sconce is a 6 px iron cup in three tones, with no rim, no fuel and no bracket. In the composed room it hangs in front of the arch's brick with nothing holding it. Fix: a wall plate with two rivets and an arm, a cup with a lit elliptical rim and a dark inside, and pitch or rag in the cup.
- **T-2, torch, the flame in all 4 frames (fault).** Each flame is a nested teardrop of three flat bands with smooth stepped sides, so it reads as a sticker. Fix: 2 or 3 tongues that part and rejoin over the four frames, the core offset from frame to frame, deep red-orange at the base, and embers as 2 px pairs.
- **UR-1, urn_seal, the mouth (fault).** The mouth is a flat dark 12 x 3 rectangle. Fix: an ellipse, with the inner wall lit on the far side and shaded on the near side.
- **UR-2, urn_seal, the glint (fault).** The cream glint sits right of centre on the shoulder (x 30-32 of 48), against upper-left light. Fix: move it to the upper left.
- **UR-3, urn_seal, the raised band at row 32 (polish).** It is one flat tone across the whole width. Fix: shade it as the body is shaded.
- **UR-4, urn_seal, the chips (polish).** The chips are flat pale rectangles. Fix: a dark north lip on each.
- **RT-1, roots_corridor and roots_hall, the rootlets (fault).** The roots are better than U5: the strands have volume and overlap with occlusion. But the rootlets are straight 1 to 2 px dark sticks splayed like legs, so the roots read as insects. Fix: taper them from 3 to 1 px, bend them, light their top side, make them fewer and uneven, and put their tips under the floor.
- **RT-2, roots, the stones (fault).** The stones are flat two-tone squares. Fix: three tones, a top plane and a contact line.
- **RT-3, roots (polish).** There is no dark contact line where the strands meet the floor.
- **R-1, all four rubble piles (fault).** The blocks are rounded pillow rectangles of nearly one size, each in three tones (a lit top band, the body, a dark bottom line), stamped across the pile. None has a fracture face, an east face or a chip. Fix: cut blocks with one dressed face and one rough fracture face, a top plane, a west face (tone 3 to 4) and an east face (tone 1 to 2), sizes from 6 to 20 px, and some tilted or on edge.
- **R-2, rubble (fault).** There is no occlusion where one block lies on another. Fix: a tone 0 to 1 contact line under each upper block.
- **R-3, rubble (polish).** The pebbles are two-tone dots.
- **R-4, rubble_hall, the block at the top left (fault).** One block lies about 10 px north of the pile with no contact line, so it reads as floating. Fix: seat it with a contact line and an east shadow, or join it to the pile.
- **CA-1, cairn_alcove, the guardian's body (fault).** It is one of Matt's calibration patterns, flat boulders with moss hats: large single-tone grey areas defined by dark contour lines, with moss caps and drips sitting on top. Fix: the rock recipe (lit crown, body, dark underside, cluster texture), with moss in creases and low joints, not as hats.
- **CA-2, cairn_alcove, the wall below (fault).** The wall is rounded pill stones in two tones on dark mortar. Fix: squared courses with chipped corners and lit top edges.
- **CA-3, cairn_alcove, the grass strip (fault).** It is a band of vertical stripes. Fix: tufts with lit tips over a calm base, and a reason for grass to grow underground (a shaft of light).
- **CA-4, cairn_alcove, the two grey pebbles above the figure (fault).** They float with nothing under them.
- **CA-5, cairn_alcove (polish).** Amber lines along the boulders' west edges read as a stray outline, and the east moss hat is lit from the right (detail.light 65,2,93,27, upheld).

## False positives

3 detector findings rejected in full and 1 in part, out of 27. The other 23 are upheld, or folded into a finding:

- `woodland/mossy_log` detail.light (50,37,96,53), rejected. The box covers bark plates in the shaded lower half, and their lighter sibling plates happen to fall east. The log is lit from the upper left.
- `undercroft/torch` detail.light (96,13,114,51), rejected. The box is frame 4's flame, a light source.
- `undercroft/urn_seal` detail.volume, rejected in part. Row 40 is lit at 25 to 40 % of the width and dark to the east, and "darkest at 0 %" is the outline. The urn fails on UR-1 to UR-3 regardless.
- `woodland/forest_bench` detail.bar 0.61 is accepted as polish, not rejected. Against Eastward's own yard bench it is at par.
- The rubble detail.light findings (corridor, hall, seal) are folded into R-1: some blocks' east ends are lighter than their west ends.

## Not checked

- In the game. I did not play the zone, check it at phone scale or check it under the night tint. The scene gate (`npm run review:scene -- undercroft`) was not run; the room compositions above are a source-level composite of `kit.json`, not a Godot render.
- The torch's motion. I looked at the four frames side by side, not as playback.
- Scale against Bramble. I saw it only on the gate sheets, not measured beyond `logic.scale` (no findings).

## For other reviewers and tools (not part of the verdicts)

- **Logic:** the unlit channel groove ends about 40 px west of the lever and the seal, so it does not lead to what the plate opens. A strip of wall courses runs along the ground picture's south edge beyond the void and belongs to no room.
- **Tooling:** `review:asset` crashes when a non-anchor kit sibling (`kit/bench`, `kit/log`) has not been rendered, because `siblings()` renders only anchors. I rendered the kit pictures first with `render_kit`. Also, review-agents.md says `woodland/forest_bench.json` carries `style_anchor`, but the record does not, and only `kit/bench.json` has the flag.

## Round 2 (redraw)

Draft PR #440 (`claude-a/undercroft-redraw` into `claude-a/review-gate`) redrew all 20 Undercroft pieces through the painter (`scripts/art/native/undercroft.py`) and recorded them `pending`. A fresh detail-auditor reviewed it. That auditor drew none of the art and did not take part in round 1.

**Result: 13 pass, 7 fail.** The plates, levers, sunk seal, pillars, shard, torch, urn and three of the rubble piles now reach the bar. The ground, the lit channel, the raised seal, both roots, the corridor rubble and Cairn's alcove fail. Of Matt's named faults, four are gone. One survives: the flat channel line. The unlit groove is the same flat brass strip as before, and the lit overlay is still a bar with no light around it.

### What was reviewed

- **Head:** `08dee79e`. The PR's scope matches its body: `kit.json` changes only its `inputs` hash, and `undercroft.tscn` and `plans/undercroft.json` are untouched. `test_undercroft_craft` runs 9 tests, all OK.
- **Calibration first:** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>` gives recall 38 of 38 and the same false positives as round 1 (5 on 6 clean screens, 29 on 22 clean props). `calibration_results.json` was reverted, not committed.
- **Asset gate:** `npm run review:asset` on all 20, after rendering `kit/bench` and `kit/log` first (the known crash). Then `--record`, which left the bytes and detector output unchanged. I opened every sheet and also built my own zooms at 6x to 10x on the floor colour, before beside after.
- **Scene gate:** `npm run review:scene -- undercroft` produced Godot renders at four spawns (start, corridor, seal, arena) and the zone composite. I opened all 120 grid cells (log below). I also composed the rooms from `kit.json` myself in three states: nothing pressed, plate pressed, and plate pressed with the seal open. The painter's own renders predate the urn's last commit; mine are on `08dee79e`.
- **Eastward at x1.37 nearest neighbour** (local only, never committed), from shot 06 at native 640 x 360:
  - the dungeon floor, (150,90,260,180) and (160,190,240,250);
  - the floor beside the fire column, (150,0,260,90);
  - the lit floor round the crystals, (260,110,370,200);
  - the floor pads, (500,195,560,240), (60,175,110,210) and (295,295,345,335), and the platform, (485,185,575,255).

  I set these against our room 1 (60,170,211,293), room 3 (1560,170,1711,293) and the chamber (1870,320,2021,443).

### Matt's named faults

| Fault                        | Now                                                                                                                                                                                                                    |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flat target glyph (U7)       | Gone. The plate star and the seal sigil are carved, with dark north and west walls and lit south and east lips (checked texel by texel). Lit, they glow on a ramp to a near-white core.                                |
| Flat channel line (U6)       | **Still there.** Unlit, the groove is unchanged: a two-tone brass strip 210 px long (G-8). Lit, it has a core, but it is a 10 px bar with no light on the lips or the floor, and its east 40 % is flat lavender (C-2). |
| Flat boulders with moss hats | Gone. Cairn's moss hats are off, and his stones have a lit rim, a dark underside and texture. The bank below him is a new fault (CA-6).                                                                                |
| Floating pebbles             | Gone. Cairn's are dropped, the rubble is seated, and the stump pebbles sit on the foot line. The corridor's pebbles are flat (R-5), but they do not float.                                                             |
| Terrazzo of specks (U1)      | Gone. The floor has 0.68 to 0.95 pale specks per 1000 px (3.0 to 4.2 before); the plates, levers and seals have 0 to 1.64 (3.1 to 4.0 before).                                                                         |

### Per-asset verdicts

| Asset           | Detectors      | Bar    | Verdict  | Findings                                                 |
| --------------- | -------------- | ------ | -------- | -------------------------------------------------------- |
| ground          | pass, none     | (calm) | fail     | G-1r, G-7, G-8, G-10, G-11 fault; G-9, G-12, G-13 polish |
| channel_lit     | pass, none     | (thin) | fail     | C-2                                                      |
| plate_up        | pass, 1 polish | 0.50   | **pass** | P-4 polish                                               |
| plate_down      | pass, 3 polish | 0.52   | **pass** | P-4 polish; detail.light x2 rejected                     |
| lever_up        | pass, 1 polish | 0.78   | **pass** | L-4 polish                                               |
| lever_down      | pass, 1 polish | 0.83   | **pass** | L-4 polish                                               |
| seal_slab       | pass, 2 polish | 0.53   | fail     | SE-4; detail.light rejected                              |
| seal_sunk       | pass, 1 polish | 0.60   | **pass** | none (the pair waits on seal_slab)                       |
| stump_nw        | pass, 1 polish | 0.66   | **pass** | ST-4 polish                                              |
| stump_se        | pass, 1 polish | 0.60   | **pass** | ST-4 polish                                              |
| shard           | pass, 1 polish | 0.58   | **pass** | SH-2 polish                                              |
| torch           | pass, 3 polish | 0.68   | **pass** | T-3 polish; detail.light x2 rejected                     |
| urn_seal        | pass, 1 polish | 0.72   | **pass** | none                                                     |
| roots_corridor  | pass, 1 polish | 0.65   | fail     | RT-4                                                     |
| roots_hall      | pass, 1 polish | 0.61   | fail     | RT-4                                                     |
| rubble_chamber  | pass, 1 polish | 0.66   | **pass** | none                                                     |
| rubble_corridor | pass, 2 polish | 0.52   | fail     | R-5; detail.light upheld as polish                       |
| rubble_hall     | pass, 1 polish | 0.76   | **pass** | R-6 polish                                               |
| rubble_seal     | pass, 1 polish | 0.59   | **pass** | R-6 polish                                               |
| cairn_alcove    | pass, 1 polish | 0.89   | fail     | CA-6; CA-7 polish                                        |

The bar for plates and seals (0.50 to 0.60) is accepted. Eastward's own floor pads and platform in shot 06 score 0.40 to 0.50 on the same bar, because the prop band's mean comes from lamps, pots and seated benches. A calm, dressed floor piece is at par with Eastward at those numbers. The urn re-records at 0.72, not the 0.80 the PR body gives, because its last commit tidied it.

### Findings, ranked

1. **RT-4, roots_corridor and roots_hall, the whole root (fault).** Legs gone, but the root now reads as an animal lying on the floor, an otter or a lizard, in every render: start r0c2, corridor r0c0 and r2c3, my rooms r0c0 and r1c1. It is one smooth, fat, sinuous body that tapers to rounded ends, with a knot on its back like an ear and short runners like legs. Two pale stones sit under it like feet. In roots_hall the east end is a bulb with a dark knot like an eye. Both ends are free, so it comes from nowhere and goes nowhere. Fix: give it an origin and an end. Bring it out of the north wall's foot or a lifted flag, with one end hidden (under the coping, or behind a flag lifted on its edge with a dark gap). Dive the far end into the floor, with a broken flag tilted up beside it. Braid two or three strands of different thickness (8, 5 and 3 px) rather than one body. Bark in long fissures. No bulb or knot at either end; taper to 1 px rootlets that enter the joints. Keep the stones away from under it, or put them where a flag broke.
2. **G-1r, ground, every light pool (fault).** The pools now step in whole and half flags, as G-1 asked, but they read as a patchwork of pale tiles, not light:
   - In the Godot renders, room 2's pool is a pale rectangle with a straight lower edge (start r2c4), and so is the corridor's (seal r2c1). The skylight pool is a block of pale blue flags (arena r2c3).
   - Inside a pool the piece-to-piece contrast is 12.5 L (room 1) and 13.0 L (the chamber), over the ground band's calm limit. Eastward 06's floor measures 4.0 L.
   - The warmth is gone: the brightest torch-pool flag measures about (145,133,124), barely off grey. Eastward's pool beside the fire column is amber and falls off softly over its hex tiles.

   So the flag-stepped falloff is not acceptable against Eastward. Fix:
   - Keep the flags whole, but let the pool's outer step be a 2x2 checker band one rung apart, laid radially round the source, not on the flags. eastward-edges 5.4 and house-style 4 allow dither on ground exactly for a light fade.
   - Make the heart one or two rungs, not three: the pool may climb at most two rungs, and the contrast inside a pool must stay under the band's calm limit.
   - Bring the warm siblings back in the heart (`FLOOR_LADDER_WARM` rungs 4 and 5 on `ashlar` and `sand`, which the measured colours show barely reach the floor).

3. **G-8 and C-2, the channel, both states (fault).** Unlit (ground rows 405 to 410, x 1440 to 1650), the groove is unchanged from round 1. It is two flat rows of (163,110,38) over four of (129,77,21) for its whole length. In the Godot renders (seal r2c3 and r2c4, arena r2c0 and r2c1) it is the loudest line on the floor: Matt's U6, now orange. Lit, `channel_lit` has a core, but its east 40 % (x 137 to 218) is three flat lavender bands, and no light reaches the groove's lips or the floor. Fix:
   - Unlit: a dark groove (stone tones 0 and 1) with the brass only as a 1 px lit inner lip. Add tarnish clusters (sibling greens and browns in 2 to 4 px), grime in drifts, and two or three breaks where a divider sits.
   - Lit: a picture 16 to 18 px tall that steps the south lip and one floor row either side a rung up in violet. Carry a thinner core to the east end. This needs a new offset in `kit.json` and the scene (see the logic list).
4. **G-7, ground, the pools' hue (fault).** The rungs are per flag, but the warm and cool hue masks are per texel (`fcool = lf_cool > lf`, `fwarm` in `undercroft.py`). So ellipse arcs cut across flags in 1 to 2 px stepped diagonals. Examples: the chamber at (1788-1800, 427-450) and (1810-1830, 453-467); room 2 at (996-1026, 399-454); also seen in seal r2c0 and corridor r2c4. Each flag then reads as two stones of different colour. Fix: take each flag's hue from the mean of `lf_cool` and `lf_warm` over it, as `flag_rungs` does for the rung, and split a flag only on the same straight line as its rung.
5. **SE-4, seal_slab, the front face and the tops (fault).** The 120 px face is blocks of one body tone with 2 or 3 cluster pixels, a lit west column and rounded corners on every block. They sit in 3 px near-black mortar: rows 146 to 148 are L 36, one connected region of 795 px. That is parts in three tones, and mortar that reads as ink. The two raised top slabs are 1515 and 1420 px of one colour, 75 % of each slab. Fix: courses 6 or 7 px of parts 8 to 15 px long, each a sibling of stone or ashlar with the odd one a tone off. Mortar 1 px at `stone_cool` 0 or 1. A chip only where a corner is knocked to mortar, not on every block. Clusters of 2 to 4 px inside each part. On the tops, two or three soft blotches a tone apart, as on seal_sunk.
6. **CA-6, cairn_alcove, the bank (fault).** The damp earth bank (rows 74 to 81) is a horizontal gradient of five bands (L 117, 92, 68, 44, 20, top to bottom), with 3 x 3 moss squares at even spacing. It reads as a timber beam laid across the alcove (my 5x crop and arena r0c5). Fix: an earth lip that wobbles 1 px (eastward-edges 3.1), a dark under-lip, then the earth body with clods and pebbles in drifts. Moss in two or three clumps of different widths with a lit cap, only where the bank meets the stones.
7. **G-10, ground, the floor's busyness (fault).** The worn sibling patches inside every flag read as mottling, and the floor is busier than Eastward's. Piece contrast is 8.1 L (room 1), 10.6 (room 3) and 9.0 (room 4), against Eastward 06's 4.0. Room 3 sits just under the calm limit. Shapes are 21 to 23 a patch, at the band's minimum, so the busyness is contrast between pieces, not detail. Fix: drop the worn patches in shade, and keep at most one soft blotch a flag in a pool. Bring flag-to-flag variation down to sibling swaps at the same tone (house-style 8).
8. **G-11, ground, Cairn's alcove frame (fault; also in round 1's bytes).** The alcove's arch in the ground is one plain pale band, pointed, in a round-arched arcade. It is centred about x 2160, while its bay's voussoir arch is centred about x 2195. So it cuts the pier to its west, and the bay's voussoirs show beside it to the east (my crop, and arena r0c5). Fix: centre the opening on its bay, and draw its arch with the arcade's voussoirs: the same ring, then the infill or the alcove recess inside it.
9. **R-5, rubble_corridor, the pebbles (fault).** Two pebbles, at (75,53) and (41,60), are flat one-tone 5 x 5 plus shapes (13 px, L 126 and L 105). In game they read as sparkle glyphs beside the pile (corridor r1c4). One more pebble is two stacked discs, a mushroom. Fix: three-tone pebbles as on rubble_chamber (a lit top-left pair, body, a dark lower row and a contact pixel), irregular outlines 3 to 5 px, no plus shapes.
10. **G-9, ground, the joints (polish).** A dark 2 to 3 px knot sits at many joint crossings, like rivets on graph paper. The dirt packed in the joints is red-brown (65,39,42), 9046 px of the floor, so the joints read as copper wire at 3x. Fix: open only some corners, as worn gaps, not knots. Put the dirt on `earth_cool` 1 or the stone's tone 0, so it reads as grime, not wire.

Polish:

- **P-4, plates:** the frame kerbs are round-ended pills; the moss is 2 x 2 squares.
- **L-4, levers:** the moss is a 2 x 2 square at the foot corner; the face plate's sheen steps at 45 degrees.
- **ST-4, pillars:** the drum joints are straight across a cylinder (they should sag as shallow arcs), the top plane has no elliptical near rim, and stump_nw's fallen drum reads as a box (no end ellipse).
- **SH-2, shard:** the three sparkles sit evenly down one ridge; no glow at the foot.
- **T-3, torch:** at 1x the bracket reads as one chunky dark post; the flame core is the same cream oval in all four frames.
- **R-6, rubble_hall and rubble_seal:** near-black 2 px holes at block corners, two of which read as eyes on rubble_seal.
- **CA-7, Cairn:** pale pillows with faint texture, the brightest stone in the room.
- **G-12, ground:** the moss at the wall foot is dark hard-edged blobs.
- **G-13, ground:** 1 px dark crack lines radiate from the shard's foot like a web.

### The new guards

- **`specks.py` (limit 2.0 per 1000 px) is a sound regression pin for the six flat stone pieces and the floor, but not a detector you can trust elsewhere.**
  - It catches terrazzo: the test fixture scores 16.7, and a sparser grid of 2 x 2 specks every 14 px scores 4.4.
  - The limit sits just above what the redraw produced: the tested pieces score at most 1.64 (seal_sunk), with the floor at 0.95.
  - Run on the 45 reviewer-passed assets with pictures, it fails 9: the willow 10.2, sacks 9.0, boulder 7.9, barrels 4.6 and 3.7, the anvil 4.2, and five fences at 2.25.
  - On the redrawn pieces it fails 5 that are not in the test: rubble_seal 2.97, stump_se 2.76, roots_hall 2.53, stump_nw 2.26 and rubble_chamber 2.22. What it counts there is flute highlights, lit facets and lit bark streaks, which are structure.
  - Its docstring ("after it under 1.5") is wrong for the set as a whole.
  - `GLOWS` exempts the `snow` family, a material, so pale specks drawn on the snow ramp would never count.

  Keep it as a test of the named pieces. Do not wire it into the asset gate until it is calibrated on approved art. Correct the docstring.

- **`test_undercroft_craft.py`:**
  - `StepsByFlag` tests `flag_rungs` on a synthetic grid of square flags. It does not test the painted ground, and so it misses G-7 (hue arcs across flags).
  - `test_undercroft_floor_carries_no_terrazzo` checks rows 160 to 440 only. The floor runs to row 600; rows 440 to 600 score 0.56, so it passes anyway.
  - The fixtures do not probe the limit: the terrazzo fixture is 8 times over it, and the "clusters pass" fixture uses darker clusters, which can never count.
  - `SceneUnmoved` is sound and useful.

### Cairn's canvas

Pinned at 108 x 100, and nothing is clipped. The opaque box is (10,32) to (97,99), with no texel on the left, right or top edge. The source frame (the last 160 px of `defeat_S.png`) is 42 to 117 by 63 to 137, inside its cell. The figure is smaller and lower than in round 1, because the bank and courses cover his lower third; the painter means him to be half sunk.

### False positives

5 detector findings rejected out of 24:

- plate_down's detail.light on the stone and on the violet. The east and south inner walls of a sunk panel lit from the upper left are the lit ones, and the violet is a glow.
- seal_slab's detail.light on the violet (a glow).
- The torch's two detail.light boxes (10,14,20,45 and 38,17,50,45), which are flames.

The 17 detail.bar findings are accepted as polish, and rubble_corridor's detail.light is upheld as polish. `specks.py` (not in the gate) is rejected on the stumps, roots_hall, rubble_seal and rubble_chamber, as above. The scene gate's 88 logic.wiring blockers are other zones' quest events, not this zone's art, and are left to the logic lane. Its 10 logic.off_grid findings are 5 props listed twice, and are upheld (logic list).

### Grid log

Godot renders at 1920 x 1080; cells 6 x 4 at 480 x 405. The zone composite is 2304 x 648.

- **start** (room 1, the stair hall):
  - r0c0: the void west, the west wall, arcade infill, HUD, moss at the wall foot.
  - r0c1: torch 1 on the arcade, the ledge, the north pool's flags.
  - r0c2: roots_hall reads as an animal with stones for feet (RT-4).
  - r0c3: the arcade's end and the return into room 2.
  - r0c4: the void, room 2's arcade, a wall root.
  - r0c5: the void, the arcade, the HUD counter.
  - r1c0: the west wall, flags in shade.
  - r1c1: a pool stepping by flags (G-1r).
  - r1c2: floor, a frog enemy.
  - r1c3: floor, the door return.
  - r1c4: a torch on the bay's infill, the wall root down to the ledge.
  - r1c5: the arcade, room 2's floor, moss blobs (G-12).
  - r2c0: the stair column, the player.
  - r2c1: the falloff steps as a skyline of dark flags (G-1r).
  - r2c2: shade, mottled flags (G-10).
  - r2c3: red-brown joints (G-9).
  - r2c4: room 2's pool as a pale rectangle; roots_corridor (G-1r, RT-4).
  - r2c5: room 2's floor, an enemy.
  - r3c0: rubble_hall seated, three-tone pebbles.
  - r3c1: shade, moss, the south rim.
  - r3c2: the south rim.
  - r3c3: the corner return, the void.
  - r3c4 and r3c5: void.
- **corridor** (room 2):
  - r0c0: roots_corridor (RT-4).
  - r0c1: a torch, pool flags.
  - r0c2: room 2's east wall, the arcade of room 3.
  - r0c3 to r0c5: void, then room 3's arcade with two wall roots and torches.
  - r1c0: shade.
  - r1c1: pool flags, a frog.
  - r1c2: the pier, room 3's arch.
  - r1c3: a torch, a wall root.
  - r1c4: the arcade.
  - r1c5: rubble_seal beside the corridor rubble's plus-shaped pebbles (R-5).
  - r2c0 and r2c1: falloff steps.
  - r2c2: the south door return, the player.
  - r2c3: roots_corridor at the south rim.
  - r2c4: the pool's disc edge arc (G-7).
  - r2c5: pale pool flags.
  - r3c0 to r3c2: shade, moss, the rim, the void; r3c3 to r3c5: void.
- **seal** (room 3):
  - r0c0 and r0c1: void, room 2's arcade, a wall root.
  - r0c2: the urn (elliptical mouth, glint at the upper left).
  - r0c3: the arcade, moss.
  - r0c4: a wall root, a torch, pool flags.
  - r0c5: the void slot, stump_nw.
  - r1c0: room 2's floor, rubble_seal.
  - r1c1: a torch, the corridor rubble.
  - r1c2: the pier, pool flags.
  - r1c3: shade, plate_up.
  - r1c4: lever_up.
  - r1c5: seal_slab with the sigil glowing in state 0 (logic).
  - r2c0: the pool arc (G-7), an enemy.
  - r2c1: the corridor pool as a pale rectangle (G-1r).
  - r2c2: the south door, the player.
  - r2c3 and r2c4: the unlit groove, a flat brass strip (G-8).
  - r2c5: the pier under the seal, the slot.
  - r3c0 and r3c1: void.
  - r3c2: rubble_seal, the rim.
  - r3c3 and r3c4: shade, the rim.
  - r3c5: the slot, the rim.
- **arena** (room 4):
  - r0c0: room 3's floor.
  - r0c1: a wall root, a torch.
  - r0c2: the seal, the lever, stump_nw.
  - r0c3: a torch, room 4's floor.
  - r0c4: the arcade.
  - r0c5: Cairn's alcove (CA-6, G-11), rubble_chamber.
  - r1c0: shade.
  - r1c1: a boar.
  - r1c2: lever_up, seal_slab.
  - r1c3: the pool edge.
  - r1c4: pool flags.
  - r1c5: the shard (cap facets, sparkles).
  - r2c0 and r2c1: plate_up, the brass groove (G-8).
  - r2c2: the boss.
  - r2c3: the skylight pool as a block of blue flags (G-1r).
  - r2c4: the shard's web of cracks (G-13).
  - r2c5: shade.
  - r3c0 to r3c4: shade, moss, the rim.
  - r3c5: stump_se with its pebble on the foot line.
- **zone composite** (`undercroft_zone.png`):
  - r0c0 to r0c2: the arcades of rooms 1 and 2, the pool.
  - r0c3 to r0c5: room 3, the urn, the lever, a wall root.
  - r1c0 to r1c2: room 1's floor, the stub of roots_hall.
  - r1c3 to r1c5: room 3's floor, the seal edge.
  - r2c0 to r2c2: the stair column, falloff steps, room 2's pale pool.
  - r2c3 to r2c5: the lit channel bar, the pier, the skylight pool.
  - r3c0 to r3c2: rubble_hall, shade, the void.
  - r3c3 to r3c5: rubble_seal, shade, the rim.

  The composite pastes the whole 4-frame torch sheet (rows of 3 to 4 flames, r0c1 and r1c2) and draws roots_corridor as a smear at the rim (r2c2 and r3c2): tool faults. The Godot renders show both correctly.

### Logic issues (not part of the verdicts)

1. **The channel stops short (plan).** The groove runs x 1440 to 1656 art px at y 408 (world 480 to 552 at y 136). The lever's foot is at (1644,288), 120 art px (40 world px) north of the groove's end. The seal's west face is at x 1677, 21 art px (7 world px) east of it. The charge leads to neither. Fix: new channel points in `plans/undercroft.json`, running east to the seal's foot with a branch, or a bend, up to the lever.
2. **The lit overlay is too short (scene).** `channel_lit` is 10 px tall at offset (-1,-5), so it cannot light the groove's lips or the floor beside it. A taller picture needs a new offset in `kit.json` and the scene.
3. **The seal does not answer the channel (plan or scene).** The seal's sigil glows in state 0, before the plate is pressed, and does not change when the channel lights (my plate-only composite). Nothing shows the charge arriving. Fix: a dark sigil until `undercroft_plate`, lit after it, and dark again when sunk, which needs a third state on the seal.
4. **Cairn's alcove sits off its bay (ground and plan).** See G-11. Also, torch 8 at (2112,168) hangs on the alcove's west jamb.
5. **Five props are off the soft grid (scene gate):** roots_corridor, urn_seal, stump_nw, stump_se and cairn_alcove, by 1 to 4 world px.
6. **The roots have no origin.** The wall roots end at the ledge. The floor roots start and end in the air, and do not meet the wall roots or a crack.
7. **The skylight pool shows no source on screen**, no shaft and no motes. The plan's skylight passes `logic.light_source`.
8. **Tooling.** The `review:scene` zone composite does not crop the torch's frames and nearly hides roots_corridor. The undercroft report carries 88 cross-zone wiring blockers. `review:asset` still needs the kit siblings rendered first.

### Not checked

- In the game by hand, at phone scale and under the night tint. The Godot renders are by day at 1920 x 1080.
- The torch as playback: I looked at the four frames side by side only.
- Scale against Bramble beyond the gate sheets (no `logic.scale` findings).

## Round 3

Draft PR #440 at `b50caa14` answered round 2 in the painter and changed ten assets: ground, channel_lit, seal_slab, roots_hall, roots_corridor, the four rubble piles and cairn_alcove. A fresh detail-auditor reviewed it. That auditor drew none of the art and took no part in rounds 1 or 2.

**Result: 6 pass, 4 fail.** roots_hall, the four rubble piles and seal_slab now pass. The ground, the lit channel, roots_corridor and Cairn's alcove fail. Across the zone that makes 16 pass and 4 fail. Of Matt's named faults, U6 survives in the lit state: the overlay is now a striped tube, but its bands still run as ruler lines. U1 comes back in a new form: dark earth grit in the warm pools, at terrazzo density.

### What was reviewed

- **Head:** `b50caa14`. `git diff c7f40de6 b50caa14` changes exactly the ten PNGs and their records. The bytes of the ten assets that passed in round 2 are unchanged (lever_up, lever_down, plate_up, plate_down, seal_sunk, shard, stump_nw, stump_se, torch, urn_seal), so their verdicts stand.
- **Calibration first:** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>` gives recall 38 of 38. False positives are unchanged: 5 on 6 clean screens and 29 on 22 clean props. `calibration_results.json` came out byte-identical and was not committed.
- **Asset gate:** I rendered `kit/bench` and `kit/log` first, then ran `npm run review:asset` and `--record` on all ten. The detectors pass on all ten (polish only), and the bytes match their records. I opened every sheet. I also made my own zooms at 4x to 8x on the floor colour, and composed the four rooms from `kit.json` in three states: nothing pressed, plate pressed, and plate pressed with the seal open.
- **Scene gate:** `npm run review:scene -- undercroft` produced Godot renders at four spawns and the zone composite. I opened all 120 grid cells (log below). The painter had not run it.
- **Eastward at x1.37 nearest neighbour** (shot 06 at native 640 x 360; local only, never committed):
  - the warm floor by the fire column, (150,0,260,90);
  - the shade floor, (160,190,240,250);
  - the lit floor round the crystals, (260,110,370,200).

  I set these against our room 1 pool (60,150,211,273), room 1's shade (200,430,310,512) and the skylight pool (1900,300,2051,423).

### Matt's named faults

| Fault                  | Now                                                                                                                                                                                                                                                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Terrazzo (U1)          | **Back in a new form.** The pale specks stay gone. But every warm pool carries earth grit: 16.3 to 17.4 dark clusters per 1000 px, each 2 to 4 px and a full tone (0.105 OKLab L) under the heart. That is the density of the terrazzo fixture (16.7). `specks.py` counts only pale specks, so it misses them (G-16).               |
| Hard room edges (U2)   | Gone.                                                                                                                                                                                                                                                                                                                               |
| No falloff (U3)        | Gone. There is occlusion at the wall feet and shade in the corners.                                                                                                                                                                                                                                                                 |
| Flat pillars (U4)      | Gone (bytes unchanged since round 2).                                                                                                                                                                                                                                                                                               |
| Flat root bar (U5)     | Gone.                                                                                                                                                                                                                                                                                                                               |
| Flat channel line (U6) | **Unlit: gone.** The groove is cut, with a dark inner wall, a navy floor with a broken sheen and a brass inner lip. **Lit: still there.** Eight straight bands each hold one colour over 96 % of 250 px, and `review:scene` flags two `detail.flat_line` ruler lines (zone composite, 1433-1679 at rows 400-405 and 409-414) (C-3). |
| Flat targets (U7)      | Gone (bytes unchanged since round 2).                                                                                                                                                                                                                                                                                               |

### Per-asset verdicts

| Asset           | Detectors      | Bar  | Verdict  | Findings                                        |
| --------------- | -------------- | ---- | -------- | ----------------------------------------------- |
| ground          | pass, none     | calm | fail     | G-14, G-15, G-16 fault; G-17, G-18 polish       |
| channel_lit     | pass, 3 polish | 0.77 | fail     | C-3; detail.light and detail.outline rejected   |
| cairn_alcove    | pass, 2 polish | 0.90 | fail     | CA-8; detail.light upheld into CA-8             |
| roots_corridor  | pass, 2 polish | 0.50 | fail     | RT-5; detail.light upheld as polish             |
| roots_hall      | pass, 1 polish | 0.56 | **pass** | RT-6 polish                                     |
| rubble_chamber  | pass, 1 polish | 0.67 | **pass** | R-6, R-7 polish                                 |
| rubble_corridor | pass, 2 polish | 0.53 | **pass** | R-7 polish; detail.light upheld as polish       |
| rubble_hall     | pass, 1 polish | 0.67 | **pass** | R-6, R-7 polish                                 |
| rubble_seal     | pass, 1 polish | 0.56 | **pass** | R-6, R-7 polish                                 |
| seal_slab       | pass, 2 polish | 0.71 | **pass** | SE-5 polish; detail.light (sigil glow) rejected |

### Round 2 findings, measured again

- **RT-4, roots.** roots_hall is fixed. It is three braided strands that come out of the wall's foot at a dark gap and dive into the floor beside a lifted flag. It has no body, knot or runners, and it reads as a root at 1x and at 4x (start r0c2, corridor r0c0). roots_corridor no longer reads as a creature, but as an object lying on the floor (RT-5). The wall roots now dive into the floor at a dark gap (corridor r1c3 and r1c5).
- **G-1r, the pools.** The pools no longer step by flags, but they now fail in a new way (G-14):
  - Room 1's 8.4 L, which the painter flags, comes from the pool's rim inside the box. Measured inside the heart (110,200,240,280), the contrast is 2.9 L, and room 2's heart is 3.2 L. Both are well under the ground band's calm limit (10.34 x 1.15).
  - So the number is not the problem. The hue, the material and the size are.
- **G-7, hue per flag.** Fixed. The tint is per flag, and the warm ladder's low rungs are grey, so no flag shows two hues at the rim.
- **G-8 and C-2, the channel.** G-8 (unlit) is fixed. C-2 (lit) is not, and becomes C-3.
- **SE-4, the raised seal.** Fixed:
  - The face is 7 px courses: a lit top row, a body and a dark bottom row, on stone and ashlar siblings.
  - Mortar is 1 px at L 66; the face's darkest pixel is L 52. Before, a single 795 px region sat at L 36.
  - The end slabs are broken in two, and the largest colour on the tops covers 30 % (75 % before).
- **CA-6 and CA-7, Cairn.** CA-7 is fixed: his stones are a step darker. CA-6 is not (CA-8).
- **G-10, the busy floor.** The worn patches are gone, and flag to flag is a close-value swap in the lit rungs. In shade, a new quilt replaces them (G-15).
- **G-11, the alcove.** Fixed. The opening is centred in its own bay under the arcade's voussoirs and cuts no pier (my 4x crop, arena r0c5).
- **R-5, the pebbles.** Fixed. They are three-tone ovals of 4 to 5 px, with no plus shapes or stacked discs.

**The painter's second shortfall** (dense clusters in the warm pools, added because the detectors flag single-colour flags as flat): this is the wrong answer to a detector false positive.

- The clusters are earth grit (`floor_codes`: `drift & warm` is drawn on `earth`), a full tone under the heart, not sibling swaps at the same value. They read as dirt grain at 4x and give the pools their sandy look at 1x.
- A calm flag inside a floor plane is what Eastward draws (shot 06's shade floor). When `detail.flat` fires on one, the auditor rejects it, as I do below for the seven skylight flags. Do not answer it with grain.

### Findings, ranked

1. **G-14, ground, the torch pools (fault).** The pools are painted on the earth ramp, so they read as rugs of sand, not light on stone.
   - Rung 3 of `FLOOR_LADDER_WARM` is `earth_warm 3` / `earth 3` at (130,105,80) and (122,98,80), OKLab hue 66. With `POOL_STEPS = 2` the heart can never pass rung 3, so every heart is a plateau of those two colours. They cover 87 % of room 1's heart, 83 % of room 2's and 80 % of room 3's.
   - Inside the pool the joints stay cool grey-violet (90,78,84), so the pool reads as tan tiles in grey grout.
   - Each pool is 2 to 3 H across and 2 H deep, and its heart lies about 2 H below its flame. There are seven near-identical ellipses, two per room (start r0c0 to r1c2, seal r0c3 to r1c4, arena r0c3 to r1c5; my crop `r1pool_4x`).
   - Eastward's warm floor (06, 150,0,260,90) is warm only within about 1 H of its source, and stays the floor's own stone with soft dark mottling.
   - The fringe is 4 x 4 blocks scattered by noise, with diagonal shards where the smoothed rung boundary runs at 45 degrees (`r1pool_edge_8x`). It reads as a torn edge at 4x.

   Fix:
   - Light the stone on its own warm siblings: `stone_warm` 2 to 3 and `ashlar` 3 to 4 for the heart, with `stone_warm` 1 for the spill. Never use `earth`, `path` or `sand`, which belong to another material (house-style 1: light moves a pixel along its own ramp).
   - Light the joints too, a rung under the lit flag on the same warm sibling.
   - Shrink each pool to about 1 to 1.3 H radius, brightest at the wall's foot under the torch, and vary the shapes (the two torches of a room need not throw twins).
   - Make the fringe a 2 x 2 checker band one rung apart (`style.dither_dark`, eastward-edges 5.4), not scattered 4 x 4 blocks.

2. **C-3, channel_lit, the lit state (fault).** It is still Matt's U6, now striped:
   - It is a symmetric tube of eight straight bands, each one colour over 96 % of 250 px (rows 402 to 413 in the zone). It has a dashed core with even dashes, and brass dividers every 24 px.
   - The "spill" is a broken violet row at y 400 and y 415, set off from the groove by an unlit floor row (401 and 414). So it reads as a dotted line beside a tube, not light (`ch_lit_8x_junc`).
   - The overlay paints over the south lip's stone and brass with flat violet.

   Fix:
   - Draw it as a lit groove seen from three-quarter view, not a tube. The far (north) inner wall is lit violet in 2 to 3 tones, the floor of the groove is the core, and the near (south) inner wall is hidden under the lip, which keeps its stone with only its inner edge a rung up in violet.
   - Break every band into uneven lengths, and let the core swell near the plate and at the T, then thin towards the ends.
   - Lay the spill on the first floor row against the groove, as a 2 x 2 checker one rung up in the floor's cool sibling, fading over 3 to 4 rows. Never leave an unlit row between the spill and the groove.

3. **G-15, ground, the shade quilt (fault).** Rung 1's two variants are `soot 2` (44,36,51) and `slate_cool 1` (37,35,64). The same goes one rung up: (59,52,62) against (51,48,81).
   - They match in lightness (0.276 against 0.274 OKLab L), but the hue turns 24 to 29 degrees and the chroma rises 2 to 3 times. That is a change of family, not a sibling swap (siblings turn 9 degrees).
   - Chosen per flag, they make a patchwork of blue and grey flags with a stepped skyline in every room's south half: start r2c1 to r3c2, corridor r2c0 to r3c1, seal r2c3 to r3c4, arena r2c0 to r3c1, zone r2c0 to r2c1. The skylight pool's north edge steps in whole blue flags too (arena r1c3 and r1c4).
   - Eastward's shade floor (06, 160,190,240,250) is one blue-violet field, with a lit rim on each tile.

   Fix:
   - Make the variant a true sibling of the body: `soot_cool 2`, or `slate_cool 1` for every shade flag, with variants only a few L apart at the same hue.
   - Give each flag its north-west lip in the shade too, as G-3 asked, so the flags read by their edges, not by their colour.

4. **G-16, ground, the earth grit in the warm pools (fault).** The pools carry 16.3 to 17.4 dark clusters per 1000 px of (101,74,59) and (95,70,61), 2 to 4 px each, 5.1 to 5.3 % of each heart. They are 0.105 OKLab L under the heart: a full tone, not a sibling swap. This is U1's terrazzo in dark. Fix: keep the grit's value at the heart's rung on a sibling (`stone_warm` or `ashlar` at the same tone), gather it in two or three drifts a room against the walls and in the corners, and leave the open floor calm. Extend `specks.py`, or its test, to dark clusters, so this is pinned.
5. **RT-5, roots_corridor (fault).** No longer a creature, but it reads as a bundle of sticks or a rifle lying on the floor (corridor r2c3, start r2c5, zone r2c2; `roots_corr_ctx_4x`).
   - Both ends are "lifted flags" drawn as a 1 to 2 px lit arris at (135,125,120), L 127, over a navy gap (27,16,51). That arris sits two rungs above the floor in shade (75,63,72), so the flags read as metal ferrules.
   - The two dark rootlets under the bundle read as legs.

   Fix:
   - Draw each lifted flag as a slab tilted up: its top plane 3 to 4 px in the floor's own tones, its arris one rung up (90,78,84), and a 1 px dark gap only along its lower edge.
   - Let one end run under a flag that stays flat, so the root comes up from the floor.
   - Keep the rootlets above the strands' line and shorter than half the bundle's width.

6. **CA-8, cairn_alcove, the bank (fault; CA-6 persists).** It still reads as a timber plank across the alcove (`cairn_8x`, arena r0c5, zone r0c5).
   - Rows 75 to 81 are horizontal bands: a dark line, a body at L 69, row 80 in one tone over 88 % of 84 px, then a dark line.
   - The lip wobbles only at the ends, the pale pebbles read as nail heads, and the moss is 2 x 3 green rectangles.
   - detail.light (the bank lit from the right, 11 L a H) is upheld into this finding.

   Fix:
   - Make the lip wobble by a texel every 4 to 8 px across the whole width.
   - Break the body into clods 3 to 6 px wide, each with a lit top-left pair and a dark lower pixel, on `earth` and its siblings, with no row holding one tone over more than 40 % of its width.
   - Lay pebbles of 3 to 4 px in two drifts, not in a row.
   - Moss in two or three clumps with a lit cap, as the kit's moss is drawn.

7. **G-17, ground (polish).**
   - Grey and brown stain blotches sit on the shade flags near the south rims (corridor r3c0, start r3c3) and as diagonal brown smears in the pools (seal r0c3). They read as smoke or spills. Give them a reason (damp under a root, soot under a torch), or drop them.
   - A straight diagonal light-band edge crosses a flag at corridor r2c4.
8. **G-18, ground (polish).**
   - The unlit groove's north inner wall carries vertical streaks at an even spacing, which read as a comb or railing at 4x (`ch_unlit_8x`). Stagger them over 6 to 15 px.
   - The navy floor of the groove is one tone over 4 rows apart from the sheen. Break it with one or two wet patches.
9. **RT-6, roots_hall (polish).** The lifted flag at the dive reads as a blade, as in RT-5. The hooked side rootlet ends in a round blob. Taper it into a joint.
10. **SE-5, seal_slab (polish).** The tops' mottle is 6.9 dark clusters per 1000 px and reads as granite dots at 4x. Merge them into two or three soft blotches a slab.
11. **R-6 and R-7, rubble (polish).** The near-black corner holes stay (two still read as eyes on rubble_seal). All the pebbles are one lozenge shape. Vary them between 3 and 5 px, some rounder and some angular.

### Logic issues (not part of the verdicts)

1. **The branch does not open into the channel (ground and channel_lit).** At the T (x 1641 to 1650), the branch's groove ends at y 398. Rows 399 to 401 are floor, then the main groove's north lip begins. In the lit state the branch's light stops there too, so the charge visibly breaks 3 px short of the lever's branch (texels checked in both states). Fix: carve the branch through the main groove's north wall, mitre the lips at the corner, and run channel_lit's branch down to the main core.
2. **The channel now reaches the seal.** The unlit groove ends at the seal's pier (x 1680, plan [560,136]), and the branch ends under the lever's plate (y 294, foot 288). Confirmed in seal r2c3 to r2c5, seal r1c4 and arena r1c2.
3. **The lit overlay covers the L.** The offset (-10,-124) puts the 260 x 134 picture at x 1430 to 1690 and y 284 to 418, so it covers both runs. Apart from the 3 px gap above, the coverage is right.
4. **The four snapped props** (roots_corridor, urn_seal, stump_nw, stump_se) and cairn_alcove stand on the soft grid. `review:scene` now reports no `logic.off_grid` (10 in round 2). Nothing floats or shows a stale shadow in the renders.
5. **Cairn's foot, y 165 to 168.** The figure and the bank sit in the alcove, and the courses below him cover the ledge across the opening with no gap (my 4x crop, arena r0c5). It is consistent.
6. **Torch 8 (lead confirmed, polish).** It is placed at x 2112 (frame x 2097 to 2127). The pier spans 2088 to 2112, so the cup and the flame's east side cover the voussoir ring's west foot by 3 to 4 px. Fix: move it to world x 700 (art 2100), the pier's middle, which is on the 4 px grid.
7. **Still open from round 2:**
   - The seal's sigil glows before the plate is pressed (seal r1c5), which needs the runtime third state the PR proposes.
   - The skylight pool shows no shaft or motes.
8. **Tooling:**
   - The `review:scene` zone composite still pastes the whole 4-frame torch sheet and draws both lever states at once.
   - `detail.flat` fires on calm flags inside a pool that lies within a ground plane (7 in the arena). `flats` should skip pools inside a ground plane, as it skips the plane's other flags.
   - `review:asset` still needs `kit/bench` and `kit/log` rendered first.
   - The scene report repeats its 44 cross-zone wiring blockers (88 counted).

### False positives

10 detector findings rejected out of 24 (15 asset findings and 9 scene findings that are not wiring):

- channel_lit `detail.light` (208,10,220,115) and seal_slab `detail.light` (11,61,43,89): both boxes are violet glow.
- channel_lit `detail.outline` (31 %): a glow carries no outline (house-style 2). Its real fault is C-3.
- The arena's seven `detail.flat` boxes (577 to 719, 217 to 370): calm flags in the skylight pool, inside the floor plane. The ground band's calm-and-drawn rule applies, not the prop rule.
- Upheld: the zone composite's two `detail.flat_line` findings (C-3). cairn_alcove's `detail.light` goes into CA-8. roots_corridor's and rubble_corridor's `detail.light` stand as polish. The ten `detail.bar` findings are accepted as polish.
- The 88 `logic.wiring` blockers are other zones' quest events, left to the logic lane.

### Grid log

Godot renders at 1920 x 1080, 6 x 4 cells of 480 x 405. The zone composite is 2304 x 648.

- **start** (room 1):
  - r0c0: HUD, the void, the west wall, the AO corner, the pool's tan edge.
  - r0c1: torch 1 on the infill, the pool as a tan plateau, moss blobs at the wall foot.
  - r0c2: roots_hall out of the wall foot, diving at a lifted flag (reads as a root), the second pool.
  - r0c3: the arcade's end, the pool, the door pier.
  - r0c4: the void, room 2's arcade.
  - r0c5: the void, the HUD counter.
  - r1c0: the pool's west fringe of scattered blocks.
  - r1c1: the pool's heart with earth grit (G-16).
  - r1c2: the pool's fringe, a frog.
  - r1c3: the pool, the door return.
  - r1c4: a torch, a wall root diving at a dark gap, the pool.
  - r1c5: room 2's arcade, a wall root.
  - r2c0: the stair, the player, a boar.
  - r2c1: the shade quilt and skyline (G-15).
  - r2c2: the quilt.
  - r2c3: the quilt, the door return, a dark AO patch.
  - r2c4: room 2's pool.
  - r2c5: roots_corridor reads as a rifle (RT-5), an enemy.
  - r3c0: rubble_hall, three-tone pebbles.
  - r3c1: the quilt, moss, the rim.
  - r3c2: the quilt, the rim.
  - r3c3: grey stain blotches (G-17), the corner return.
  - r3c4 and r3c5: void.
- **corridor** (room 2):
  - r0c0: roots_hall, the pool.
  - r0c1: a torch, the pool.
  - r0c2: the pier, room 3's arch.
  - r0c3 to r0c5: void.
  - r1c0: the pool's fringe.
  - r1c1: the pool's heart, a frog.
  - r1c2: the pier, the AO, the pool.
  - r1c3: a torch, a wall root diving at a dark gap.
  - r1c4: the arcade, an overhang shadow.
  - r1c5: a wall root diving beside rubble_seal, a torch, the pool.
  - r2c0 and r2c1: the quilt (G-15).
  - r2c2: the door return, the pool.
  - r2c3: roots_corridor (RT-5).
  - r2c4: shade, a diagonal light band (G-17).
  - r2c5: the pool.
  - r3c0: stains, moss, the rim.
  - r3c1: the quilt, the rim.
  - r3c2: the corner, a stain.
  - r3c3 to r3c5: void.
- **seal** (room 3):
  - r0c0 and r0c1: void, room 2's arcade, the wall root.
  - r0c2: the urn, a torch, the pool.
  - r0c3: the pool, a brown smear (G-17).
  - r0c4: a wall root diving into the pool, a torch.
  - r0c5: the slot, stump_nw.
  - r1c0: room 2, rubble_seal, a gem enemy.
  - r1c1: a torch, the pool.
  - r1c2: the pier, the pool.
  - r1c3: the pool's edge, plate_up.
  - r1c4: lever_up with the branch ending under its plate.
  - r1c5: seal_slab, the sigil glowing in state 0.
  - r2c0: shade, an enemy.
  - r2c1: the pool, the fringe.
  - r2c2: the door, the player.
  - r2c3: plate_up, the unlit groove.
  - r2c4: the unlit groove (comb streaks, G-18), the quilt.
  - r2c5: the seal's face in courses, the slot, the skylight fringe.
  - r3c0 and r3c1: void.
  - r3c2: rubble_seal, the quilt.
  - r3c3 and r3c4: the quilt, moss, the rim.
  - r3c5: the slot, the rim.
- **arena** (room 4):
  - r0c0: room 3's pool, the urn edge.
  - r0c1: a wall root, a torch, the pool.
  - r0c2: the slot, stump_nw, lever_up.
  - r0c3: a torch, the pool.
  - r0c4: the arcade, the pool.
  - r0c5: Cairn's alcove centred in its bay (G-11 fixed), torch 8 over the ring, the bank as a plank (CA-8), rubble_chamber.
  - r1c0: the pool, a boar.
  - r1c1: the boar.
  - r1c2: the lever, the branch, the seal sigil.
  - r1c3: the skylight's stepped north edge (G-15).
  - r1c4: the skylight pool, the warm pool above it.
  - r1c5: the shard, the pool.
  - r2c0: plate_up, the groove.
  - r2c1: the groove, the quilt.
  - r2c2: the slot, the boss.
  - r2c3: the boss, the skylight pool.
  - r2c4: the skylight fringe of scattered blocks.
  - r2c5: shade.
  - r3c0 to r3c4: the quilt, moss, the rim.
  - r3c5: stump_se.
- **zone composite:**
  - r0c0 to r0c2: room 1's arcade, the torch sheets pasted whole (tool), the void.
  - r0c3 to r0c5: rooms 3 and 4, Cairn, more torch sheets.
  - r1c0 to r1c2: room 1's twin pools, roots_hall, room 2's wall roots.
  - r1c3 to r1c5: room 3's pools, the lever in both states (tool), the seal, stump_nw, the skylight's stepped edge.
  - r2c0 to r2c2: the stair, the shade skyline (G-15), room 2's pool, roots_corridor.
  - r2c3 to r2c5: the plate, the lit channel (C-3, flat_line x2), the seal's face, the skylight pool.
  - r3c0 to r3c2: rubble_hall, the quilt, the rim, the void.
  - r3c3 to r3c5: rubble_seal, the quilt, stump_se, the rim.

### Not checked

- In the game by hand, at phone scale and under the night tint. The renders are by day at 1920 x 1080.
- The torch as playback (unchanged since round 2).
- The seal_slab and seal_sunk pair after a state change in Godot: I saw the swap in my own composites only.

## Round 4

Draft PR #440 at `a8185aca` answered round 3 in the painter and changed four assets: ground, channel_lit, roots_corridor and cairn_alcove. It also moved torch 8 to world x 700. A fresh detail-auditor reviewed it. That auditor drew none of the art and took no part in rounds 1 to 3.

**Result: 2 pass, 2 fail.** roots_corridor and Cairn's alcove now pass. The ground and the lit channel fail. Across the zone that makes 18 pass and 2 fail. Of Matt's named faults, none survives in its old form. But the light pools fail in a new way: every pool is a target of nested rings (G-19). And the lit channel still lights nothing around it (C-4), which is the last trace of U6.

### What was reviewed

- **Head:** `a8185aca`. `git diff d598bfb8 a8185aca` changes exactly the four PNGs and their records, the painter, `specks.py`, the craft test and its new fixture, the golden manifest's hash, and torch 8 in the plan, `kit.json` and the scene. The other 16 assets are byte-identical to `d598bfb8` (git blob ids compared), so their passes stand.
- **Calibration first:** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>` gives recall 38 of 38. False positives are unchanged: 5 on 6 clean screens and 29 on 22 clean props. `calibration_results.json` came out unchanged and was not committed.
- **Asset gate:** I rendered `kit/bench`, `kit/log` and `kit/lantern` first, then ran `npm run review:asset` and `--record` on the four. The detectors pass all four: no findings on ground or cairn_alcove, and one `detail.bar` polish each on channel_lit (0.77) and roots_corridor (0.61). The bytes match their records. I opened every sheet. I composed the four rooms from `kit.json` myself (foot plus offset, floor overlays first, then sorted by foot y, torch frame 0) in three states: nothing pressed, plate pressed, and plate pressed with the seal open. I also made zooms at 3x to 8x. Everything is local in the scratchpad and was not committed, for example `torchpool1_8x`, `stairpool_3x`, `shade_4x`, `skylight_ground_1x5`, `ch_lit_mid_8x`, `ch_T_lit_8x`, `ch_T_unlit_8x`, `ch_unlit_mid_8x`, `roots_corr_6x`, `cairn_6x` and `hatch_8x`.
- **Scene gate:** the painter had not run it. `npm run review:scene -- undercroft` produced Godot renders at four spawns and the zone composite. It reports 88 `logic.wiring` blockers (other zones' quests, 44 repeated) and one `detail.flat` fault in the arena. I opened all 120 grid cells (log below).
- **Eastward at x1.37 nearest neighbour** (local only, never committed). Shot 06 was brought to its art grid by `core.to_native` (scale 3.6, 532 x 299):
  - the warm floor by the fire columns, (120,30,260,130), beside our room 1 torch pool (70,150,262,287), as `sbs_warm_3x`;
  - the shade floor, (135,185,235,265), beside our room 1 shade (250,380,387,490), as `sbs_shade_3x`;
  - a clean shade box for numbers, (140,200,200,260).

### Matt's named faults

| Fault                  | Now                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Terrazzo (U1)          | Gone in every form. Pale specks score 0.48 and dark grit 0.48 in room 1's pool box; the shade scores 0.0 (round 3 had 4.6 by the same count). There are no stain blotches or grit drifts. The new dark hatching on shade flags (G-22) is strokes, not specks, but it is the same kind of texture noise.                                              |
| Hard room edges (U2)   | Gone.                                                                                                                                                                                                                                                                                                                                                |
| No falloff (U3)        | Gone. The pools are a new fault (G-19), but the falloff, the wall-foot occlusion and the corner shade are there.                                                                                                                                                                                                                                     |
| Flat pillars (U4)      | Gone (bytes unchanged since round 2).                                                                                                                                                                                                                                                                                                                |
| Flat root bar (U5)     | Gone. Both roots read as roots.                                                                                                                                                                                                                                                                                                                      |
| Flat channel line (U6) | **Unlit: gone.** **Lit: the flat line is gone, but it still lights nothing.** Each band now holds one colour over only 61 to 78 % of its run (96 % in round 3), and `review:scene` reports no `detail.flat_line`. But no pixel of floor beside the groove changes when it lights (C-4). In a dark room it reads as a glowing pipe, not a lit groove. |
| Flat targets (U7)      | Gone (bytes unchanged since round 2).                                                                                                                                                                                                                                                                                                                |

### Per-asset verdicts

| Asset          | Detectors      | Bar  | Verdict  | Findings                                         |
| -------------- | -------------- | ---- | -------- | ------------------------------------------------ |
| ground         | pass, none     | calm | fail     | G-19, G-20, G-21, G-22 fault; G-12r, G-23 polish |
| channel_lit    | pass, 1 polish | 0.77 | fail     | C-4 fault; C-5 polish                            |
| roots_corridor | pass, 1 polish | 0.61 | **pass** | RT-7 polish                                      |
| cairn_alcove   | pass, none     | 0.94 | **pass** | CA-9 polish                                      |

The other 16 (lever_up, lever_down, plate_up, plate_down, seal_slab, seal_sunk, shard, stump_nw, stump_se, torch, urn_seal, roots_hall and the four rubble piles) are unchanged and keep their pass.

### Round 3 findings, measured again

- **G-14, the torch pools.** Part fixed:
  - Fixed: the material. The pools are on `stone_warm` and `ashlar`, with no earth, path or sand. The heart is (166,156,142), a warm grey stone.
  - Fixed: the joints in a pool are lit a rung under the flag.
  - Fixed: the size. Below torch 1 the pool reaches about 80 px (1.1 H) from the wall's foot, brightest at the foot, and no two pools are twins.
  - Not fixed: the fringe. The rim is now a 2 x 2 checker, as asked, but every inner step carries a checker band too, and the steps between them are ragged. That is G-19.
- **G-15, the shade quilt.** Fixed. The shade is one colour, (37,35,64), over 84 to 87 % of a box, with no blue-and-grey patchwork. Each flag keeps a lit north-west lip ((56,57,90) and (51,48,81), 3 % each). The falloff runs on curves, so no whole-flag skyline remains (start r2c1, corridor r2c0, arena r2c0). The shade is now too dark and too flat (G-21).
- **G-16, the earth grit.** Fixed (0.48 against 4.6 on the same box).
- **G-17, the stains.** Fixed: no blotches or smears in any cell.
- **G-18, the unlit groove.** Fixed. The streaks on the far wall sit 6 to 15 px apart, and the navy floor has wet patches and a broken sheen (`ch_unlit_mid_8x`, seal r2c3 and r2c4).
- **The T junction.** Fixed in both states. Unlit, the branch's groove runs through the main groove's north wall, and the floors join (`ch_T_unlit_8x`). Lit, the branch's core runs down into the main core with no gap (`ch_T_lit_8x`).
- **C-3, the lit channel.** Part fixed. The far wall is lit in bands of uneven length, and the near lip keeps its stone. The core swells at the plate (two near-white rows over the first 12 %) and at the T, then thins towards the ends. The spill is not there (C-4).
- **RT-5, roots_corridor.** Fixed (see the verdict). The lifted flag is the weak part (RT-7).
- **CA-8, Cairn's bank.** Fixed (see the verdict).

### The painter's three shortfalls

1. **Concentric checker rings, one per step.** Upheld, and worse than the PR says. At 1x in every render, each pool reads as a target. Room 2's pool (start r1c4) is three dotted ellipses round a pale disc. The skylight (arena r1c3 to r2c5) is three nested ellipses whose outer ring runs almost to the south wall. At 8x (`torchpool1_8x`), the checker shows only on some steps. The others are hard, ragged sawtooth edges with diagonal 1 px hatching inside the heart: the "torn edge" round 3 named. This is G-19.
2. **The shade floor is dark overall.** Upheld as a fault. Our shade is OKLab L 0.274, and Eastward 06's shade floor at the same character height is 0.36 to 0.37. Our void is 0.217, so the floor sits only 0.057 above it, about half a rung. Eastward's floor sits well above its void (about 0.20). In `sbs_shade_3x`, Eastward's floor is a mid lavender field of hex tiles with soft blotches. Ours is a near-black navy with lines on it. The `ground_plane` test on room 1's shade box (200,430,310,512) gives drawn = False. This is G-21.
3. **Pool boxes at 11 to 15 L because the pools are smaller.** Not accepted as a side effect. The ground band's calm limit is 1.15 x 10.34 = 11.9 L. With `bands.contrast`, which already takes out the light's gradient over 0.5 H:
   - room 1's pool box (60,150,211,273) measures 15.4 and its heart (110,170,230,215) 20.8;
   - the skylight box (1900,300,2051,423) measures 11.9 and its heart (1870,360,1960,425) 14.3;
   - the stair pool (40,320,200,480) measures 7.9 and passes.

   So the pools are not calm. What is left after the gradient comes out is the hard steps: below torch 1 the rung falls 0.59 to 0.44 in one row (y 191) and 0.44 to 0.33 in one row (y 218). Eastward 06's clean floor measures 3.7 L (shade) to 7.7 and 8.7 (lit floor between the crystals). This is G-20, and it has the same cause as G-19.

### Findings, ranked

1. **G-19, ground, every light pool (fault).** The torch, stair and skylight pools are nested ellipses on one centre, each step edged with a 2 x 2 checker band or a ragged sawtooth. They read as targets or stage spotlights, not light on stone (start r1c4, corridor r0c1, seal r1c1, arena r0c4, arena r1c3 to r2c5; `torchpool1_8x`, `skylight_ground_1x5`). Four things cause it, all in `scripts/art/native/undercroft.py`:
   - `pool_rungs` puts a narrow checker (`frac < 0.12` and `> 0.88`) on every step of a smoothed field. Each step boundary becomes a ring line. Where the field is steep the band is too thin for the checker, which gives the sawtooth.
   - The pools climb four rungs: below torch 1, L runs 0.274, then 0.328, 0.438, 0.592 and 0.67. That is four visible rings plus the heart.
   - The warm hue is decided per flag (`flag_tint`, `mw > 0.9`). The pool's outer flags fall under that threshold and keep the cool ladder, so a blue `slate_cool 2` ring (51,48,81) sits between the warm heart and the shade. The pool turns cream, then mauve, then blue, then navy.
   - The skylight's lit zone reaches about 417 x 307 px, against the plan's ellipse of 240 x 180 (rx 40, ry 30 world). The stair pool is about 180 x 210 px (2.5 to 2.8 H).

   Fix:
   - Keep one fade only, at the pool's rim. Make it a wide staged 2 x 2 dither (eastward-edges 5.4), a quarter, a half, then three quarters coverage over 6 to 10 px. Let it stop at joints for part of its length, so the rim follows flag edges in places and never runs as one smooth ring.
   - Step the inside by whole and half flags (`flag_rungs` with `split`), not by thresholds of a smoothed field. Then the heart reads as lit stones, with no sawtooth and no hatching.
   - At most two visible steps over the ambient, the heart and one rim.
   - Give every flag a pool lifts over the ambient the warm sibling, so there is no blue ring.
   - Break the symmetry. Put the heart at the source (the wall's foot, or the stair's mouth) and let the fade run longer away from it. Give the skylight a shaft's shape, longer along the fall of the light with its heart off-centre, and cut it back to the plan's ellipse.

2. **C-4, channel_lit, the spill (fault).** No floor pixel changes when the channel lights. Diffing the plate-pressed composite against nothing-pressed, on the main run only rows 400 to 410 change: the groove and its north lip, 64 to 98 px of the lip in rows 400 and 401. The floor rows (y 399 and up) are unchanged, and row 399 is still 93 % shade. The PR's "fades over four rows" is not in the picture. The cause is in `p_channel`: the spill's checker `((Xg // 2 + Yg // 2) % 2)` flips phase every two rows, and each row must 4-touch the row before it. So rows 3 and 4 (d = -9 and -10) can never be placed. Fix:
   - Let each row touch the previous row by 8-neighbours, or pair rows d = -7/-8 and -9/-10 as one checker row each.
   - Check the result by diffing the two states: the light must reach 3 to 4 floor rows north of the groove along the whole lit run, and round the branch.
3. **G-21, ground, the shade floor (fault).** As in shortfall 2: L 0.274 against Eastward's 0.36 to 0.37, only 0.057 over the void, and 84 to 87 % one colour. Fix:
   - Lift the ambient one rung, to `slate_cool 2` and `slate 2` ((51,48,81) and (56,57,90), L 0.33 to 0.36). The skylight's outer zone already uses them, and they match Eastward's shade.
   - Keep the void at (27,16,51) and the joints a rung under the flags, so the room separates from the void by about 0.12 to 0.15 L.
   - Give each room two or three large soft blotches, one sibling apart, as Eastward's shade carries (house-style 7, "a few large soft blotches"). They are not grain.
   - Re-derive the pools from the higher ambient, which leaves room for only two steps (G-19).
4. **G-20, ground, the pools are not calm (fault).** As in shortfall 3: room 1's pool 15.4 L and its heart 20.8, the skylight 11.9 and its heart 14.3, against the limit of 11.9. G-19's fix removes it: no hard rung jumps inside a pool and at most two steps. Re-measure on the same boxes.
5. **G-22, ground, dark hatching on shade flags (fault).** Clustered 1 px vertical strokes in the joint colour (32,25,59), 3 to 12 px long, stand on many shade flags: 51 such strokes in the box (200,380,600,600), and joint-colour pixels make up 26 % of the box (400,420,440,445). At 1x they read as tufts of dead grass or scratches on the stone (start r2c2, corridor r2c0 and r2c1, `hatch_8x`). They are new; that spot was clean in round 3. They appear to come from `break_runs(cv, cv >= 0, ...)`, the final pass that breaks any column run over 48 texels. The calm shade flags now make such runs. I did not confirm this by re-running the painter. Fix: exempt floor flags from `break_runs`. A calm flag inside a floor plane is what Eastward draws. If a detector calls one flat, reject it, as round 3 did; do not dress it.
6. **G-12r, ground, the moss (polish; G-12 from round 2 persists).** The moss along every south wall foot and in the corners is dark, hard-edged round blobs (start r3c0 to r3c3, corridor r3c0 and r3c1, seal r3c3 to r3c5, arena r3c0 to r3c5). Fix: clumps with a lit cap, as the kit's moss is drawn, only in the low joints.
7. **G-23, ground, the moss in the torch pools (polish).** A saturated mid-green two-tone blob of about 10 x 9 px sits in the heart of room 1's pool, and others sit in room 2's and room 4's (start r0c1, corridor r0c1, arena r0c3). Under torchlight it reads as a sticker. Fix: put it on the moss ramp's warm-lit tones, at most 2 x 4 px, in a joint.
8. **RT-7, roots_corridor, the lifted flag (polish).** The flag at the dive is a separate 15 x 6 slab laid between the floor's flags. The floor's joints run on round it, so it reads as a tile set on the floor (`roots_corr_6x`). Fix: lift the floor flag that actually lies under the root's east end, with its own joints, and add a dark gap where it rises.
9. **CA-9, cairn_alcove, the bank's foot (polish).** Row 81 is one near-straight dark row (52 % one tone), and rows 78 and 79 hold 47 and 43 %. The bottom edge still hints at a plank's shadow line. Fix: let a few clods hang over the foot by a texel, and wobble the under-lip as the top lip does.
10. **C-5, channel_lit, the dividers (polish).** Nine brass dividers stand every 24 px along a dashed white core, so at 3x the lit run reads a little like a ruler. They are built things, so even spacing is allowed, but drop the core's dashes at each divider and dim the divider tops in the swell.

### The new guards

- **`dark_speck_scatter` is a sound regression pin, with the same limits as the pale count.**
  - It catches the round 3 pool fixture at 4.63 against the limit of 2.0, and passes the round 4 pool box at 0.48 and the shade at 0.0.
  - I sprinkled 2 x 2 dark grit (30 L down) at 5 per 1000 px into the round 4 pool box. It scored 3.23, so it catches grit at about two-thirds sensitivity.
  - It counts only grit in a calm field (three quarters of the ring one colour), so it saw 4.6 on the round 3 pool where the round 3 auditor counted 16 to 17. That is enough for a pin with a 2.3 x margin, but it is not a measure of density.
  - The fixture is the real round 3 bytes, which is the right kind of pin.
  - The dither test is sound: a 2 x 2 checker band joins into one 8-connected run.
  - One side effect: the switch to 8-connected runs also applies to the pale count. Two terrazzo specks that touch at a corner now join into one run of 8 px, over the size limit, and are not counted. That weakens the pale pin a little. The original terrazzo fixture still fails, and all 17 craft tests pass.
  - Keep it as a test of the named Undercroft pieces, as the docstring says, not as a gate detector.
- **`test_the_tint_is_decided_per_flag`** checks the painter's own masks on the real floor, which round 3 asked for. It is sound.
- None of the tests can see G-19 to G-22. A pool-calm test would pin G-20: `bands.ground_plane` on room 1's pool box and the skylight box must be calm. A test that the lit state changes floor rows next to the groove would pin C-4.

### Plan and scene: torch 8

- The plan (`torches[7]` = [700, 56]), `kit.json` (foot 2100,168) and `undercroft.tscn` (`Torch8` at 2100,168) agree.
- The torch's opaque columns are x 2093 to 2106 (2107 in frame 3). The pier between the two rings runs from x 2089 to 2108, so the torch is centred on it.
- It clears the alcove's voussoir ring, whose dark outer edge starts at x 2109 and whose stones run from 2112 to 2117 (rows 120 and 140). It also clears the west bay's ring, which ends at 2088. See `cairn_6x` and arena r0c4 and r0c5. Round 3's logic 6 is fixed.

### False positives

1 detector finding rejected, out of 4 that are not wiring:

- The arena's `detail.flat` (665,298,686,324) is rejected. The box falls on lever_up's riveted face plate: a machined metal plate with a sheen, four rivet heads and a lit top edge (L-2 fixed in round 2, bytes unchanged since). A calm plate is the metal recipe.
- Accepted as polish: the `detail.bar` findings on channel_lit (0.77) and roots_corridor (0.61).
- No `detail.flat` fired on calm flags this round, so there was no calm-flag false positive to reject.
- The 88 `logic.wiring` blockers are other zones' quests (44, each counted twice), left to the logic lane.

### Grid log

Godot renders at 1920 x 1080, 6 x 4 cells of 480 x 405, opened at 1:1. The zone composite is 2304 x 648 in cells of 384 x 162 at 3x. All renders are in state 0 (nothing pressed).

- **start** (room 1):
  - r0c0: HUD, the void, the west wall, the torch pool's ringed west half, moss blobs.
  - r0c1: torch 1, the pool's cream heart with a saturated moss blob (G-23), the blue ring and checker rings (G-19).
  - r0c2: roots_hall out of the wall foot (passes), the second pool's rings.
  - r0c3: the arcade's end, the pool's ragged edge, the door pier.
  - r0c4: the void, room 2's arcade, a wall root.
  - r0c5: the void, the HUD counter, the arcade.
  - r1c0: the west wall, the stair pool's outer checker ring, the player.
  - r1c1: dark shade flags with lit lips (G-21), the stair pool's rim.
  - r1c2: shade, a frog.
  - r1c3: shade, the pier's foot, moss.
  - r1c4: torch 3, a wall root diving at a dark gap, room 2's pool as three dotted ellipses (G-19).
  - r1c5: room 2's arcade, moss, the pool's checker rim, a crystal enemy.
  - r2c0: the stair, the player, a boar, the stair pool's mauve heart.
  - r2c1: the stair pool's checker ring against the shade.
  - r2c2: shade with dark hatching (G-22).
  - r2c3: shade, the south door return.
  - r2c4: roots_corridor reads as a root (RT-5 fixed), the lifted slab (RT-7).
  - r2c5: the root's end, a stone turtle enemy.
  - r3c0: rubble_hall seated, its pebbles, moss blobs (G-12r).
  - r3c1 and r3c2: shade, moss blobs, the south rim.
  - r3c3: the corner return, moss.
  - r3c4 and r3c5: void.
- **corridor** (room 2):
  - r0c0: HUD, roots_hall, the pool's rim.
  - r0c1: a torch, the pool's heart with a green blob, its rings.
  - r0c2: the pier, room 3's arch.
  - r0c3 to r0c5: the void, room 3's arcade, two wall roots, the HUD counter.
  - r1c0: shade, an enemy.
  - r1c1: shade, a frog.
  - r1c2: the pier, the player.
  - r1c3: a torch, a wall root diving at a dark gap, a ringed pool.
  - r1c4: the arcade, shade.
  - r1c5: a wall root diving beside rubble_seal, a torch, a ringed pool, an enemy.
  - r2c0 and r2c1: shade with hatching (G-22).
  - r2c2: the south door return, the player.
  - r2c3: roots_corridor, an enemy.
  - r2c4 and r2c5: shade, moss.
  - r3c0 to r3c2: moss blobs, the rim, the corner.
  - r3c3 to r3c5: void.
- **seal** (room 3):
  - r0c0 and r0c1: the void, room 2's arcade, a wall root.
  - r0c2: the urn, torch 5, a pool.
  - r0c3: the pool's rings, shade.
  - r0c4: a wall root diving into the pool, torch 6, the rings.
  - r0c5: the slot, stump_nw, the HUD counter.
  - r1c0: room 2, rubble_seal, a gem enemy.
  - r1c1: a torch, a ringed pool, rubble_seal, a wall root.
  - r1c2: the pier, shade.
  - r1c3: shade, plate_up.
  - r1c4: lever_up, the unlit branch groove.
  - r1c5: seal_slab with its sigil glowing in state 0 (logic), the skylight's checker rim.
  - r2c0: shade, an enemy, moss.
  - r2c1: shade, a pool's lower rim.
  - r2c2: the south door, the boss.
  - r2c3 and r2c4: plate_up, the unlit groove: dark wall, wet patches, brass lip (G-18 fixed).
  - r2c5: the seal's coursed face, the slot, the skylight's ring.
  - r3c0 and r3c1: void.
  - r3c2: rubble_seal and the rim, with orange-brown flecks around it (not in ground.png, so in-game particles).
  - r3c3 and r3c4: moss blobs, the rim.
  - r3c5: the slot, the skylight's checker ring.
- **arena** (room 4):
  - r0c0: room 3's pool rings, the urn edge.
  - r0c1: a wall root diving, a torch, the rings.
  - r0c2: the slot, stump_nw.
  - r0c3: a torch, a green blob in a heart (G-23), the rings.
  - r0c4: torch 8 on the pier, clear of the ring, the rings.
  - r0c5: Cairn's alcove, the bank as earth (CA-8 fixed), rubble_chamber.
  - r1c0: shade, plate_up.
  - r1c1: a boar.
  - r1c2: lever_up (its face plate is the rejected `detail.flat`), the branch, the seal's sigil.
  - r1c3 and r1c4: the skylight as nested rings (G-19).
  - r1c5: the shard, the skylight's outer ring.
  - r2c0 and r2c1: plate_up, the unlit groove.
  - r2c2: the slot, the boss.
  - r2c3 to r2c5: the skylight's rings and its outer checker arc (G-19).
  - r3c0 to r3c2: shade, moss blobs, the rim, the slot.
  - r3c3 and r3c4: the skylight's outer ring reaching the south wall, moss.
  - r3c5: stump_se.
- **zone composite:**
  - r0c0 and r0c1: room 1's arcade, with the torch sheets pasted whole (tool).
  - r0c2: void.
  - r0c3: room 3's arcade, torch sheets.
  - r0c4 and r0c5: rooms 3 and 4's arcades, torch 8's sheet over Cairn (tool).
  - r1c0 and r1c1: room 1's two ringed pools, roots_hall.
  - r1c2: room 2's arcade and its wall roots.
  - r1c3: room 3, the urn, a pool.
  - r1c4: both lever states (tool), the seal, stump_nw and its east shadow.
  - r1c5: room 4's pools, rubble_chamber, the shard.
  - r2c0 to r2c5: the stair pool's rings, shade with hatching, room 2's pool, roots_corridor, the plate, the lit channel (no flat_line), the seal, and the skylight's rings.
  - r3c0 to r3c5: rubble_hall, moss blobs, the rims, rubble_seal, stump_se, the void.

### Logic issues (not part of the verdicts)

1. **Torch 8 is fixed** (above).
2. **The skylight pool is larger than its plan** (G-19). It reaches about 417 x 307 px against the plan's 240 x 180, and it still shows no shaft or motes on screen.
3. **Still open from round 2:** the seal's sigil glows before the plate is pressed (seal r1c5). It needs the runtime third state the PR proposes for Codex.
4. **The PR says more than the picture does:** the channel's "four-row spill" (C-4). I found nothing else of the kind.
5. **Tooling:**
   - The zone composite still pastes the whole 4-frame torch sheet and draws both lever states.
   - `review:asset` still needs `kit/bench` and `kit/log` rendered first.
   - The scene report repeats its 44 cross-zone wiring blockers.
   - The scene gate renders only state 0, so the lit channel has no Godot render.

### Not checked

- The lit channel and the open seal in Godot: I saw them only in my own composites from `kit.json`.
- In the game by hand, at phone scale and under the night tint. The renders are by day at 1920 x 1080.
- The torch as playback (bytes unchanged since round 2).
- Whether G-22's strokes come from `break_runs`: I traced the likely pass in the painter but did not re-run it.

## Round 5

Draft PR #440 at `8c6ade9e` answered round 4 in the painter and changed four assets: ground, channel_lit, roots_corridor and cairn_alcove. A fresh detail-auditor reviewed it. That auditor drew none of the art and took no part in rounds 1 to 4.

**Result: 2 pass, 2 fail.** roots_corridor and Cairn's alcove pass. The ground and the lit channel fail. Across the zone that makes 18 pass and 2 fail. Every round 4 finding that was a number is met: the rings are gone, the pools are calm, the shade sits at Eastward 06's value, the hatching is gone. But at 1x the torch pools now read as rectangles of grey-brown paving laid under the walls, not as light (G-24). The shade carries ghost-shaped stains (G-25). Beyond 20 px from the walls the floor is one value in every room (G-27). The lit channel's spill reaches only two floor rows (C-6).

### What was reviewed

- **Head:** `8c6ade9e`. `git diff dc472ed2 8c6ade9e` changes exactly the four PNGs and their records, the painter, the craft test and two new fixtures, the golden manifest's hash, `kit.json`'s inputs hash and one line of `test_review.py`. The other 16 assets have the same git blob ids as at `dc472ed2`, and their sha256 matches their records, so their passes stand.
- **Calibration first:** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>` gives recall 38 of 38. False positives are unchanged: 5 on 6 clean screens and 29 on 22 clean props. Nothing was written to the repository.
- **Asset gate:** I rendered `kit/bench`, `kit/log` and `kit/lantern` first, then ran `npm run review:asset` and `--record` on the four. `--record` left the records byte for byte as the painter wrote them. The detectors fail ground (`detail.flat` x6, `detail.no_falloff`) and pass the other three with one `detail.bar` polish each (channel_lit 0.81, roots_corridor 0.52, cairn_alcove 0.89). I opened every sheet.
- **The painter's floor, rebuilt:** I ran `undercroft.build` from the plan into a private folder with its `fields` (slab, joint, rung, lifted, rim, tint masks). It reproduces the committed `ground.png` byte for byte. Every pool, rung and tint number below comes from those masks and the committed pixels, not from the PR.
- **Composites:** I composed the lit channel and roots_corridor over the ground at their `kit.json` feet and offsets, and diffed the plate-pressed composite against nothing-pressed. I opened the painter's `rooms_1x_state1-r5.png` and `rooms_2x_state1-r5.png` room by room, and made zooms at 3x to 8x. All of it is local in the scratchpad and was not committed: `torchpool1_5x`, `skylight_3x`, `stairpool_4x`, `blotch_room1_4x`, `hatch_r4_6x`, `hatch_r5_6x`, `southfoot_4x`, `channel_T_unlit_vs_lit_6x`, `roots_flag_r4_vs_r5_8x`, `cairn_5x`.
- **Scene gate:** not re-run. No plan or scene change in this round.
- **Eastward at x1.37 nearest neighbour** (local only, never committed). Shot 06 was brought to its art grid by `core.to_native` (scale 3.6, 532 x 299):
  - room 1 (40,140,440,440) beside Eastward (100,20,392,239), with the fire-column floor, the lit corridor and the shade, as `sbs_ew06_room1_r5`;
  - torch 1's pool (70,150,262,287) beside the warm floor under the fire columns (120,30,260,130), as `sbs_warm_r5_3x`;
  - room 1's shade (250,380,387,490) beside the shade floor (135,185,235,265), as `sbs_shade_r5_3x`;
  - the skylight (1780,290,2060,500) beside the lit corridor round the player (140,90,345,243), as `sbs_skylight_r5_2x`;
  - number boxes: shade (140,200,200,260); warm floor (150,40,250,80); lit corridor (165,90,250,130); the dark floor by the west crystal (120,95,160,140).

### The painter's claims, measured

All values are OKLab L, OKLCH chroma C and hue in degrees, or `bands.contrast` in L at H 74.

| Claim | Measured | Holds? |
| --- | --- | --- |
| Shade median L 0.359 on round 4's boxes (target about 0.36) | (200,430,310,512) 0.359; (250,380,387,490) 0.359; all ambient flag bodies 0.359 (p10 0.328). Eastward 06 shade 0.361 (and 0.359 on the wider box). Joints 0.274, void 0.210, so the room stands 0.149 over the void. | Yes |
| In-pool contrast: room 1 pool 10.0, heart 9.3, skylight 10.2, heart 3.6, stair 8.7, all under 11.9 | 10.0, 9.28, 10.24, 3.58, 8.73. Per torch pool, masked to its lifted region: 5.3 to 8.9. | Yes. But `ground_plane` finds the skylight box under-drawn (7.25 tones and 20.2 shapes a patch, against a band least of 7.5 and 23) and its heart much more so (4.8 and 10.2). The PR quoted contrast only (G-24). |
| Skylight lit zone 224 x 181 px with the rim's fade (plan 240 x 180) | 225 x 174 from the lifted and rim masks (x 1808 to 2032, y 308 to 481), 208 x 161 lifted only, 218 x 171 measured from the image (median-5 L over the ambient's p90 + 0.02). All inside the plan's ellipse (x 1800 to 2040, y 306 to 486). | Yes (about 7 px shorter than claimed) |
| At most two rungs; one staged 2 x 2 dither, at the rim only; no blue ring; heart toward the wall's foot | Rungs {2, 3} over ambient 1 in every torch pool and the skylight, {2} at the stair. All 67,992 lifted texels in the torch zones carry the warm tint and none the cool. The 4 px band outside the pools is the pool body (90,78,84) 47 % and the shade (56,57,90) 34 %, with no `slate_cool 2` ring. Every torch pool's lifted box starts at the wall's foot (y 168 or 312). The heart's edge carries no dither on any texel of its outline. | Yes. The hard heart edge is part of G-24. |
| No dark 1 px hatching on flag bodies | `_strokes` on all flag bodies: 0 (round 4's picture under the same masks: 12). The joint colour (32,25,59) covers 0.0 % of (400,420,440,445), against 26.1 % in round 4. At 6x the flag bodies are clean. Run over a whole box, `_strokes` counts the joints' jogs (179 in (200,380,600,600)); they are joints, not hatching. | Yes |
| Channel spill reaches d -7..-10: main 82/47/47/19 %, branch 86/50/50/18 % | Composite diff: main 83/49/49/17 %, branch west 86/50/50/17 %. But rows d -7 and -8 (y 401, 400) are the groove's north lip, with no floor paint. Only d -9 and -10 (y 399, 398) are floor, at 49 % and 17 %. Rows 397 and 396 hold 5 and 4 %. Nothing changes south of the main run (y 411 and on) or east of the branch. | Numbers yes. The floor reach is two rows, not four (C-6). |
| `detail.flat` x6 on calm warm rim flags, and `detail.no_falloff` 0.31 (threshold 0.33): proposed false positives | Detectors confirmed: flat 0.16 to 0.205 against 0.14, on 878 to 1123 px one-tone areas in torch pools 2, 3, 6, 7 and 8 (twice); no_falloff 0.307. | Both upheld (see False positives) |

### Round 4 findings, measured again

- **G-19, target rings.** Fixed as named: two rungs, one rim dither, no checker on inner steps, no blue ring, hearts at the source, the skylight inside its plan. But the fix produced G-24.
- **G-20, pools not calm.** Fixed (numbers above).
- **G-21, shade too dark.** The value is fixed (0.359 against 0.36). The flatness the round 4 audit also measured is not: the shade still fails `ground_plane`'s drawn test (G-26). The blotches added for it read as stains (G-25).
- **G-22, hatching.** Fixed.
- **G-12r, wall-foot moss.** Fixed. 79 clumps in the shade, median 5 x 2 px (largest 7 x 3), with a dark underside, a body and a lit cap, sparse along the feet.
- **G-23, moss in the pools.** Fixed. 19 clumps, largest 4 x 3 px, on the yellow-greens (43,81,32) and (75,113,47) rather than the shade's teal (2,67,44).
- **C-4, the spill.** Part fixed. The floor now changes, but only over two rows (C-6).
- **C-5, the dividers.** Fixed. The core breaks at each divider and runs unbroken between them (`channel_T_unlit_vs_lit_6x`). The even spacing is allowed for a built thing.
- **RT-7, roots_corridor's flag.** Fixed. The flag under the root's east end is now the floor's own flag (slab x 841 to 876, y 455 to 479), with its own joints. It is tilted, and a joint is cut across it in the floor (`roots_flag_r4_vs_r5_8x`).
- **CA-9, Cairn's bank foot.** Fixed. Row 81's commonest earth tone falls from 52 % to 23 %, and rows 78 and 79 from 48 and 44 % to 30 and 28 %. The under-lip steps, and clods hang over the foot (`cairn_5x`).

### Matt's two questions

1. **The large soft dark blotches on the shaded floor: natural variation, or stains and ghost shapes?** Stains and ghost shapes. They are hard-edged, one rung down, and painted across the masonry (G-25).
2. **The torch pools: light, or blocky rectangles of lifted flags?** Blocky rectangles, and grey ones. Their hard straight edges follow the flags, and they are less coloured than the shade they sit in (G-24). The skylight's heart is the same: a pale square inside a dithered halo.

### Per-asset verdicts

| Asset          | Detectors      | Bar  | Verdict  | Findings                                   |
| -------------- | -------------- | ---- | -------- | ------------------------------------------ |
| ground         | fail, 7 faults | n/a  | fail     | G-24, G-25, G-26, G-27 fault; G-28 polish  |
| channel_lit    | pass, 1 polish | 0.81 | fail     | C-6 fault                                  |
| roots_corridor | pass, 1 polish | 0.52 | **pass** | RT-8 polish                                |
| cairn_alcove   | pass, 1 polish | 0.89 | **pass** | none                                       |

The other 16 (lever_up, lever_down, plate_up, plate_down, seal_slab, seal_sunk, shard, stump_nw, stump_se, torch, urn_seal, roots_hall and the four rubble piles) are byte-identical to round 4 and keep their pass.

### Findings, ranked

1. **G-24, ground, the light pools read as grey paving, not light (fault).** Seen under all eight torches and at the skylight, in the composites (`torchpool1_5x`, `skylight_3x`, `sbs_warm_r5_3x`, `sbs_ew06_room1_r5`). Measured:
   - **No light colour.** The torch pools' bodies (rung 2) are L 0.438 at C 0.018, hue 346; their hearts (rung 3) are L 0.509 at C 0.018, hue 8. That is greige mauve, and it is *less* coloured than the shade around it (C 0.057, hue 282). Eastward 06's floor under the fire columns is L 0.460 at C 0.062, hue 65 (gold), and its lit corridor L 0.437 at C 0.054. In ours the light drains colour, so a pool reads as dust or a different paving. The cause is the ramp. `stone_warm` 1 and 2 (#5A4E54, #796E6D) sit at C 0.014 to 0.018 with hues of 346 to 24, because the house rule turns stone's mid-darks to violet. Two rungs over L 0.36 cannot reach a warm stone tone on this ramp.
   - **Hard rectangles.** No texel of a heart's edge is dithered, and the step is 0.07 L. Of the torch hearts' outline, 64 % lies in straight horizontal or vertical runs of 10 px or more; of the skylight heart's, 80 %. Where the body stops at a joint, it does so with a hard straight edge across a whole flag (torch 1: a 38 px straight cut at x 157 to 195, y 228). With the rim's dither only on the curved parts, each pool reads as a block of lighter flags, cut off flat by the wall, with a fuzzy hem.
   - **A light's falloff that stops at the flags.** One-tone flags of 0.16 to 0.21 H² sit inside the falloff (the six `detail.flat` boxes). In Eastward 06 the light runs across the tiles: the hex pattern keeps showing, lit, and each tile changes value within itself as the light falls off.
   - **The skylight's heart is under-drawn.** Its heart box has 4.8 tones and 10.2 shapes a patch against a band least of 7.5 and 23, because the heart's joints and lips fade nearly into the flag.

   This finding overrules part of round 4's fix list for G-19 ("step the inside by whole and half flags"). That fixed the rings, but it is the cause of the blocks.

   Fix (in `scripts/art/native/undercroft.py`, `flag_rungs`, `pool_rungs` and `floor_codes`):
   - **Give the torchlight its colour.** The pool's rungs must read as candle light on stone: rung 2 about L 0.43 to 0.45 and rung 3 about 0.50 to 0.53, both at C 0.045 to 0.065 and hue 55 to 80 (Eastward 06: 0.46, 0.062, 65). The stone ramps cannot give that, and there must be no mixing outside the palette. So add one accent family by the house rule (a line in `BASES`, for example a lamplit stone with its body near OKLCH 0.50 / 0.06 / 70, made into a ramp like every other). Use it only for the floor's lifted texels and the faces' lit blocks under a torch. This is a palette change, so Claude A must approve it (house-style 1: a region gets at most three accents). Do not use earth, path or sand (round 3's G-14).
   - **Let the light cross the flags.** Decide each pool's boundaries by the light's own curve (the smooth `lt` field), not by flag edges. Draw both boundaries (shade to body, body to heart) as the same wide staged 2 x 2 dither as the rim: a quarter, then a half, then three quarters coverage over 6 to 10 px. With only two of them, wide and soft, they will not ring. A flag that a boundary crosses then holds two values, as Eastward's tiles do. Keep the per-flag tint (G-7): the hue is decided per flag, the value per texel.
   - **Keep the floor drawn under the light.** Joints, lips, arrises and cracks keep running through the pool in that light's tones (joint a rung under the flag, lip a rung over), at the same contrast as in the shade. In the skylight's heart they now fade nearly away.
   - **Re-measure:** each pool box must stay calm (contrast under 11.9) and drawn (`ground_plane` drawn = True), with C at least 0.045 on the torch pools' bodies. No heart outline more than 25 % in straight runs of 10 px or more, and no hard step anywhere on it.
2. **G-25, ground, the shade's blotches read as stains or ghost shapes (fault).** These are the "two or three large soft blotches a room". There are six, each 1.1 to 3.9 H² (start (254,367,361,544), 107 x 177 px; corridor (929,347,1177,484); seal (1268,440,1571,580) and (1571,417,1662,577); and others), on `slate_cool 1` (51,48,81), one rung (0.031 L) under the shade body (56,57,90).
   - Their edges are hard, one texel, and run as smooth curves across 15 to 47 flags and their joints. That is round 3's G-7 fault class: a tint in arcs across the flags.
   - Some hold a lighter hole, which makes a ring. Room 1's has a head-and-shoulders outline, so at 1x it reads as a figure (`blotch_room1_4x`, and in the room views of the composite).
   - They lie in the open middle of the rooms, where nothing would make stone damp.
   - Eastward 06's shade varies at the scale of its tiles and in small ochre moss flecks, never in a crisp silhouette over the floor (`sbs_shade_r5_3x`).

   Fix:
   - Make variation per flag. A damp patch is a group of whole flags (three to eight) taking `slate_cool` 1 or `slate` 1, with its edge on joints. Where a softer edge is wanted, the staged 2 x 2 dither may cross one flag, as at a pool's rim.
   - Put the damp groups where water would gather: along the walls' feet, in the corners and under the roots. Nothing in a room's open middle.
   - No holes, and no outline over 1 H across that reads as a shape.
3. **G-26, ground, the shade is still under-drawn (fault; the part of round 4's G-21 that remains).**
   - `ground_plane` gives drawn = False on every shade box: (200,430,310,512) 6.4 tones and 10.7 shapes a patch; (250,380,387,490) 7.7 and 13.9; (300,360,520,520) 6.1 and 9.9; (1290,450,1440,570) 7.7 and 15.3. The band's least is 7.5 and 23. Eastward 06 measures 11.9 to 18.0 tones and 22.8 to 23.7 shapes on its shade.
   - 77.7 % of all ambient flag-body texels are one colour, (56,57,90). Each flag body is a single fill.
   - House-style rule 1: a surface made of parts gives each part one of the family's three siblings. The flags do not take siblings.

   Fix:
   - Each flag takes `slate`, `slate_cool` or `slate_warm` at its rung (siblings, so no value noise), and the odd flag is a tone off.
   - Give flags a chipped corner knocked to joint, and a worn lip here and there.
   - Let the G-25 damp groups supply the rest.

   That is structure that makes sense for laid stone, not grain. Re-measure drawn = True on the four boxes, with the contrast still under 11.9.
4. **G-27, ground, no falloff across the rooms (fault; `detail.no_falloff` 0.307 upheld).** In every room the floor's median L is 0.274 within 20 px of the walls (the occlusion band). It is then 0.359 everywhere from 20 px on, at 20 to 40, 40 to 80 and over 80 px alike, and the same in the north and south halves of every room. So outside the pools a room is one flat value from wall to wall. Eastward 06's floor runs from 0.27 (beside the west crystal) through 0.36 (shade) to 0.46 (by the fire): it falls off continuously away from its lights. The checklist asks for falloff into corners. Fix:
   - Grade the ambient by distance from the nearest light. Keep rung 1 (0.36) within about 1.5 H of a torch, the stair or the skylight. Let it step down one rung (about 0.30 to 0.33, `slate_cool 1` and `slate 1`) in the far half of each room and its corners, through one wide staged 2 x 2 dither that stops at joints in places.
   - Keep the void at 0.21 and the joints a rung under, so the darkest floor still stands at least 0.08 over the void.
   - Re-run `review:asset`: `detail.no_falloff` must clear 0.33 without raising the pools.
5. **C-6, channel_lit, the spill reaches only two floor rows (fault; C-4 part fixed).** The composite diff shows the changes listed in the claims table above. North of the main run, the lip rows d -7 and -8 change at 83 and 49 %. The floor rows d -9 and -10 change at 49 and 17 %, and then 5 and 4 %. West of the branch: two floor columns, at 50 and 17 %. Nothing changes south of the main run or east of the branch. The spill is drawn as ragged 2 x 2 blocks in the glow's own violets, so on grey and at 3x it reads as a violet fringe or moss along one bank (`channel_T_unlit_vs_lit_6x`, the asset sheet). A near-white core in a dark room throws no light past 2 px of floor. Round 4 asked for 3 to 4 floor rows along the whole run and round the branch. Fix:
   - Light about 0.25 to 0.35 H of floor (18 to 26 px) on both sides of the main run and the branch, fading by the same staged 2 x 2 dither as the pools.
   - Draw it as the floor's own flags lifted a rung on a violet sibling (joints and lips kept), not as blocks in the glow's colour.
   - Let the overlay's `reach` cover it.
   - Pin it with the composite diff in the test (floor rows north of the lip, not overlay alpha rows that include the lip).
6. **G-28, ground, knots and stripes (polish).**
   - 286 dark 2 x 2 knots in the joint colours (37,35,64) and (32,25,59) sit at the joints' junctions, 2.0 an H² of floor. At 3x they read as rivets or nail heads, which laid stone does not have (`blotch_room1_4x`, `hatch_r5_6x`).
   - The wall-foot fade along room 1's west wall is a straight two-column checker strip that reads as a dotted stripe (`southfoot_4x`).

   Fix:
   - Let a junction be where the joints meet, at most a one-texel widening.
   - Stagger the fade's dither depth along the wall by flag, as at the rims.
7. **RT-8, roots_corridor, the tilt reads weakly (polish).** The lifted flag is the right flag now. But at 1x its tilt reads as the root's diagonal cast shadow over a darker flag, and the dark face under its raised west edge is hidden by the root. A moss clump sits on the tilted face. Fix: show 1 to 2 px of the dark face or gap at the flag's west edge, north of the root, and move the moss into the gap.

### False positives

None of the 7 detector findings on the four assets is rejected:

- **`detail.flat` x6 on ground** ((468,205,503,233), (767,347,801,381), (1537,193,1572,229), (1848,193,1886,225), (2051,205,2086,238), (2137,194,2164,240)): upheld, not as a call for grain but as evidence of G-24. Each box is a single-tone flag of 0.16 to 0.21 H² *inside a light's falloff*. A calm flag in the shade's ground plane is right, as round 4 said, and the detector skips those. A flag that the light's curve crosses but that holds one value is the light stopping at the joints, which is what makes the pools read as tiles. Eastward's lit tiles change value within themselves. Fix it by G-24 (the light crosses the flags, and the flag's own joints and lips show in the light), never by adding grain.
- **`detail.no_falloff` 0.307 (threshold 0.33)**: upheld (G-27). The painter argues that the pools, walls' feet and corners still fall off. Measured, the corners do not: from 20 px off the walls the floor is 0.359 in every distance band, in every room, north and south.
- **`detail.bar`** on channel_lit (0.81), roots_corridor (0.52, round 4 0.61; the asset now carries a calm floor flag) and cairn_alcove (0.89): accepted as polish, as in round 4.

Count: 0 rejected of 7 faults; 3 polish accepted.

### Grid log

The scene gate was not re-run (no plan or scene change). I visited every region of the painter's composites in state 1 (plate pressed) at 1x and 2x, plus my own zooms:

- **Room 1 (start):**
  - west wall and stair: the cool stair pool, one step with a dithered rim stopped at joints in places. It reads as daylight from the mouth.
  - torch 1 and torch 2 pools: grey-brown blocks with hard straight edges (G-24).
  - roots_hall: unchanged, pass.
  - centre-left: a figure-like blotch (G-25).
  - centre and south: one flat shade value, knots at the junctions (G-26, G-27, G-28).
  - south-west: rubble_hall, the moss clumps along the foot (G-12r fixed).
  - east door: the return.
- **Room 2 (corridor):**
  - the torch pool, a grey slab (G-24).
  - the two wall roots diving at dark gaps.
  - rubble_corridor.
  - a 3.4 H² blotch east of the second root (G-25).
  - roots_corridor and its lifted flag (RT-7 fixed, RT-8).
  - south foot moss.
- **Room 3 (seal):**
  - the urn standing in torch 5's grey pool.
  - torch 6's pool with the wall root.
  - plate_up, lever_up and the lit channel: the core broken at the dividers (C-5 fixed); the violet fringe 2 px into the floor (C-6).
  - a 3.9 H² blotch below the channel (G-25).
  - rubble_seal, the south foot.
- **Room 4 (chamber):**
  - torch 7's and torch 8's grey pools (G-24).
  - stump_nw and its shadow.
  - the skylight: a pale square heart in a dithered halo, inside the plan (G-24 for its heart).
  - the shard, throwing no light on the floor (note below).
  - stump_se.
  - Cairn's alcove (CA-9 fixed).
  - the south foot.

### For other reviewers (not part of the verdicts)

- **The shard** (pass, unchanged) glows violet but lights no floor round it. Eastward's crystals light theirs. If the floor is repainted for G-24, a small cool pool at its foot would agree with it.
- **The painter's guards:**
  - `test_the_pools_are_calm` and `test_the_shade_floor_sits_at_eastwards_value` are sound pins for G-20 and G-21's value, and `test_no_dark_hatching_on_the_flags` is sound for G-22.
  - `ChannelSpill` counts overlay alpha rows that include the lip, so it passes a spill of two floor rows. Pin C-6 by a composite diff on floor rows only.
  - A chroma floor on the torch pools and a `ground_plane` drawn test on the shade and the skylight would pin G-24 and G-26.

### Not checked

- The scene gate's Godot renders and grid cells: not re-run, because the plan and the scene are unchanged since round 4.
- In the game by hand, at phone scale and under the night tint.
- The lit channel and the open seal in Godot: I saw them only in composites from `kit.json`.
- Whether the proposed accent family fits the house palette's rule: that is a palette decision for Claude A, not a measurement I made.
