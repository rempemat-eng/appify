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
