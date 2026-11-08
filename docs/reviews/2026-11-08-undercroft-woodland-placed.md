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
