# Front-gable roofs: detail audit (10 Nov)

## Round 1 (PR #457)

Draft #457 (`claude-a/front-gable-roofs` at 8ae80984, based on main 8273a156) gives the library, the north cottages, the bakery, the smithy and the fern cottage front-gable slate roofs (C7, approved by Matt on 9 Nov with "drop the chimney straddling the ridge" and "polish the edges before placing"). The rules are in `docs/vision/eastward-edges.md` 11.9. This round audits the 11 re-recorded pictures: the five houses, their five damage overlays and the ground. The auditor drew none of them.

**Result: 5 pass, 6 fail.** The rakes, bargeboards, ridge, finial, slope outlines, casts and the zone's diff accounting hold as claimed, most of them exactly. Three faults stop six pictures: the stacks' feet have no readable apron, soakers or contact shadow (GR3, four houses); the lapped-board gables carry flat one-tone nail heads on a grid (GR2, two houses); and two damage tarps keep their lit values on the shaded slope (GR1).

### What was reviewed and how

- Commit 8ae80984, in a fresh worktree. All 11 PNGs' sha256 matched their records. Main's bytes came from 8273a156, in a second worktree.
- Asset gate: `python3 -m scripts.review.assets <11 refs> --record`. The detectors' findings and counts came back identical to the painter's records (only `reviewed` moved to today, reverted). Library: 1 fault (`detail.volume`), the other 10 pass with polish. Bars: library 0.83, north cottages 0.825, bakery 0.858, smithy 0.834, fern cottage 0.837 (main 0.85 to 0.88).
- Every edge was measured from the bytes, column by column, with my own scripts (not the painter's): the board's top texel and its run in the bargeboard ramp (#a87c52, #8e6242, #70432f, #50261d, #2e0a0d plus the two peg tones) for every column of each rake, the silhouette's top row for every column of each slope, the 10 texels under the board for the band, and runs of hex values at the feet, ridge, finial and stacks.
- By eye: 6x to 10x nearest-neighbour crops on neutral grey, main beside the PR; every house and damage overlay at 2x; the street at 1x and 2x from `scene.composite(load_zone('crossroads'))`.
- Eastward: official shot 17 brought to its native grid (`core.to_native`, scale 3.00) and scaled x1.37 nearest (54 to 74 px a character), B5 the farmhouse gable, native box [150,0,350,140]. Counts per 16 x 16 patch with `detail_bar.counts` on masks (whole patches inside the surface only). Ours were first passed through the reference's pipeline (x3 nearest, JPEG quality 90, centre-sampled back), since 17 is a quality-90 JPEG and its noise adds tones.
- Logic: canvas growth against the scene offsets, `kit.json` solids and pots, the kit index, `check.roads_clear()`, the five prop-shadow feet against their props, and the smoke against the pots.
- Not run: calibration (no detector changed) and the scene gate.

### Verdicts (round 1)

| Picture | Verdict | Bar | Main reason |
| --- | --- | --- | --- |
| library | pass | 0.83 | edges as claimed; `detail.volume` rejected (an ashlar block); polish GR4 to GR6 |
| library_damage | **fail** | 0.66 | the green tarp on the shaded slope is lit (GR1) |
| north_cottages | **fail** | 0.825 | flat nail grid on the gable (GR2); stack foot (GR3) |
| north_cottages_damage | pass | 0.55 | tarp on the lit slope; gaps follow the courses |
| bakery | **fail** | 0.858 | stack foot (GR3) |
| bakery_damage | pass | 0.627 | polish GR11, GR12 |
| smithy | **fail** | 0.834 | stack foot (GR3) |
| smithy_damage | pass | 0.64 | polish GR11, GR12 |
| fern_cottage | **fail** | 0.837 | flat nail grid on the gable (GR2); stack foot (GR3) |
| fern_cottage_damage | **fail** | 0.658 | the tarp over the ridge is one value on both slopes (GR1) |
| ground | pass | n/a | casts follow the new volumes; diff accounting verified |

### The edge claims, measured

| Claim | Measured | Holds |
| --- | --- | --- |
| Rake rise 2 in 3, runs 2,1,2,1, 0 breaks | every rake of all five houses: only rises of 1, flats of 0 or 1 alternating (library L 48/47, R 47/47 ...); pitch 0.669 to 0.673 | yes |
| Board 9 texels, sd 0.2 to 0.3 | 9 on every column outside the feet on the stone gables, sd 0.0. On the lapped gables the run continues into the gable boards, which use the same hexes: 9 where the band separates them | yes |
| Lit top edge left, a step down right, dark underside | west board #a87c52 over #8e6242; east #8e6242 over #70432f; 2 underside texels #50261d / #2e0a0d | yes |
| Finial over the apex, outlined in timber dark | a 6-texel post (#a87c52, #70432f, #50261d) with #2e0a0d outline, pointed at the apex | yes |
| Ridge: lit west third, dark line east, rounded back | #cea681 + #bb8d6d x3, #805248 x4, #5f3434 line to the slope; back corners cut by one texel | yes |
| Feet kick 3, end grain lit west, dark east | kick to col 0 and W-1; east end #50261d (a step below #70432f) yes; **west end #8e6242, the board's body, not lit** | partly (GR5) |
| Band: 2 texels 45 %, 3 texels 18 % (B5) | line mean 36 to 49 % darker, fade 19 to 39 %; in 8 to 25 % of columns a texel at the wall's body or lit tone sits in the line | partly (GR4) |
| Slope outline: 0 breaks lit side, only at the stack shaded side | lit slopes 0 on all five; shaded slopes break only at the stack (5 to 9 steps) | yes |
| Moss on the outline 0 | 0 on four; bakery 1 (#507d49 at 17,94) | nearly (GR7) |
| Slope means L 0.54 / 0.32 | 0.513 to 0.516 / 0.284 to 0.288 over all slate texels with joints (the painter's mask likely excludes joints) | yes |
| Stack west / east face | column medians about 95 to 143 west, 38 to 82 east on all four | yes |
| Apron stepping with the courses, soakers, contact shadow | **11 to 14 lead texels a house**: a 4-texel west soaker and a 5 to 10 texel cluster at the downhill corner; elsewhere stone meets the slope's course highlights; nothing below the foot is stepped down | **no (GR3)** |

At 1x the rakes read as clean straight lines and the boards as one thickness; at 2x the stair is even. The finial and ridge read as one vertical strip from the apex back, which is what a front gable shows.

### Eastward comparison (B5, shot 17, x1.37)

Per 16 x 16 patch, tones / shapes (ours through the reference pipeline):

| Surface | B5 | Ours |
| --- | --- | --- |
| Lit roof plane | 21.5 / 39.8 | 17.8 to 19.8 / 33.2 to 36.2 (0.83 to 0.93) |
| Shaded plane | 3.0 / 4.7 | 13.5 to 18.8 / 25.6 to 31.3 |
| Gable wall | 16.2 / 33.3 | 16.5 to 21.5 / 31.6 to 43.5 |

The gable walls reach B5. The lit slopes sit just under it, which is the direction Eastward's calm planes go (cluster noise: Eastward roofs 1 to 22 %, ours 41.2 to 43.5 % on the slopes alone). The shaded slope is far busier than B5's near-flat shade (GR6). B5's verge is 9 native px with a crisp dark line under it, close to our 9-texel board with its 2-texel underside; its line under the boards is continuous at about 72 % darker, ours is not (GR4).

### Rulings on the detector findings

- **Library `detail.volume` [99,164,124,173], "the wood reads 2D": false positive.** The box is one ashlar block of the gable: a lit top arris row #ddceb3, body #c3b6a1 / #a69c8e with tooling, a dark bed joint. It is the facade's own block recipe, which the detector does not flag below the eave; it misreads the warm stone as wood. The record keeps the detector's `fail` as evidence; the reviewer verdict is pass.
- **Cluster noise 41 to 43 % (library, bakery, smithy): polish, not a fault.** All three are under the 48 % fault line and none is worse than main (by `cluster_noise.share`: library 43.6 → 43.3 %, bakery 44.0 → 42.3 %, smithy 44.9 → 40.7 %). The new roof alone measures 41.2 to 43.5 %; the walls are unchanged recipes. Calming the slopes is GR6.
- `detail.bar` and `detail.light` are kept as measurements.

### Logic

- **Canvases grow upward only.** Library +87, north cottages +48, bakery +24, smithy +18, fern cottage +27 rows; each scene offset moves by exactly that (for example −230 → −317), positions are unchanged, bottoms stay aligned. `kit.json` solids are identical; the kit index changes only `foot` (canvas coordinates), `shadow`, `size_cells` and `variants`; footprint and collision are unchanged. Doors are unchanged: below the eave, the only changes are the removed downpipes (no gutter on a gable front, correct), re-seeded grass tufts and tooling dashes at the plinth, and the volume band moving off the front wall.
- **Fern cottage `roof_depth` 29 → 22:** `check.roads_clear()` returns no overlap. The roof reads a little shallower than its neighbours, which suits the smallest cottage.
- **Five prop-shadow feet:** with the PR's feet each shadow's west edge meets its prop's base west edge exactly (smithy_rubble 1355, square_rubble_a 658, fern_rubble 1370, beds_dug and beds_scorched 1150), and runs east and down. On main they started 2 to 8 px west of the prop, against the light. The correction is right.
- **Smoke:** it starts on the pots' top row. Its x (1542) lies in the 3-texel gap between the smithy's two pots (GR9, polish).
- **Smithy stack:** it stands 40 to 80 texels east of the forge hood, as 11.9 places every stack. A forge flue away from the hearth reads oddly; Claude A's call (GR10).
- **Casts:** the kit masks now have a straight east edge (no side verge) and a north edge that peaks over the ridge's projection (library: cols 179 to 194 of the mask, 33 to 48 art px east of the house centre, as 0.19 per world px of the ridge's height gives). The ground's casts changed the same way.

### The composite (ground)

- `sha256(scene.composite(load_zone('crossroads')))`: main 233832ce…, PR 16bb4807…, both reproduced.
- 232,150 texels change:
  - 220,954 inside the ten house boxes (old and new);
  - 5,197 outside every sprite box, all of them `ground.png` changes, all within 12 texels of a house box (casts and the lawn's re-scatter);
  - 5,999 inside the boxes of the six moved sprites: the five prop shadows (`BedsDugShadow` and `BedsScorchedShadow` share one box) and `SmithySmoke`.
- The painter's split (5,185 casts + 390 margin + 3,046 prop shadows + 2,575 smoke) matches these totals; the two differ only in 378 texels where the smoke's old box overlaps the smithy's cast. Nothing else moved.

### Fix lists (round 1)

Each list is also in the picture's `reviewer.fix_list`.

**Faults**

- **GR1** (`library_damage`, `fern_cottage_damage`): the tarp keeps its lit values on the shaded slope.
  - Library: the green tarp lies wholly east of the ridge at mean Y 101, against 105.5 when it lay on main's lit flat roof (−4 %), while the slates under it fall from OKLab L 0.52 to 0.29. It is the brightest patch of that roof at 1x.
  - Fern cottage: the tarp thrown over the ridge measures Y 181 on both halves.
  - Fix: lay the part east of the ridge two ramp steps down (about 40 to 45 % darker, nothing above tone 2), with a 1-texel dark crease where it bends over the ridge and a lit fold texel on its west side; the weights on the east slope one step down. Check: the east part's mean at most 0.6 of the west part's (or of the same tarp on a lit plane).
- **GR2** (`north_cottages`, `fern_cottage`): flat nail heads on the lapped-board gable.
  - 28 and 17 one-tone 2 x 2 #2e2943 heads, none with a lit texel, on an exact grid: x every 36 texels (64, 100, 136, 172, 208, 244 on the cottages), one on every board.
  - Fix, as XR3-S1: one lit #737078 texel at each head's upper left and a dark texel under-right so it sits in the board; jitter positions by 1 to 2 texels; skip about one board in four; keep the lit texel through tidy with `finish(keep=)`.
- **GR3** (`bakery`, `smithy`, `north_cottages`, `fern_cottage`): the stack's foot has no readable apron, soakers or contact shadow.
  - Today: 11 to 14 lead texels a house (#888697, #696e87), a 4-texel column on the west side and a 5 to 10 texel cluster at the downhill corner. Along the rest of the foot the stack's stones meet the slope's course highlights (#333051, #4e4f6d) directly (bakery rows 84 to 102, x 134 to 172). No slate below the foot is stepped down; the shaded slope's body is #1a1233, the ramp's floor, so a darker shadow cannot show.
  - Fix: a lead apron along the whole foot, 2 texels deep, stepping with the courses: the top row lit lead, the lower row the lead's dark where it turns down the slope. One soaker column up each side, the east one a step darker. The contact shadow as the course highlights removed (#333051 and #4e4f6d to #1a1233) for 3 to 4 texels below the apron and 2 texels east of the east face.
  - Check it at 1x and 2x in the street: the stack must read as standing on the slope, not sunk into it.

**Polish**

- **GR4** (all five houses): make the band's 2-texel line continuous. Rows 1 and 2 under the board: no texel above 0.55 of the gable wall's median (today library x 208 has #a69c8e right under the board, x 53 #988e85). Rows 3 to 5: about 18 % (today 19 to 39 %, so on stone the line and fade merge into one 5-texel band).
- **GR5** (all five): the west end grain at the left foot is #8e6242, the board's body; make it #a87c52 with a 2-texel ring arc. Keep 1 texel of transparent margin at both canvas edges (the feet now touch columns 0 and W−1).
- **GR6** (all five): calm the shaded slope. Keep its course lines and drop most per-slate highlights (about 1 in 3 left), towards B5's 3.0 tones a patch.
- **GR7** (`bakery`): one moss texel #507d49 on the lit slope's silhouette at (17,94) and a 4-texel moss run at (14 to 17, 98).
- **GR8** (`north_cottages`, `fern_cottage`): the lapped boards' grain is scattered 1 to 2 texel dashes on every board and reads as speckle at 2x; group it into 2 or 3 streaks a board that wander and end.
- **GR9** (`smithy`): `pots` [[186,32]] places the smoke at (1542,531) in the gap between the pots (left x 1529 to 1539, right 1543 to 1554). Record each pot and start the smoke on one.
- **GR10** (`smithy`, Claude A's call): keep the stack in the east slope as 11.9 says, or let the forge have a `high` stack just east of the ridge over the hood (hood x 91 to 124, stack x 163 to 208).
- **GR11** (`library_damage`, `north_cottages_damage`, `bakery_damage`, `smithy_damage`): battens and rafters inside the holes on the shaded slope keep lit timber values (smithy east-slope hole mean Y 87, the library's west-slope hole 94); step them one tone down east of the ridge.
- **GR12** (`bakery_damage`, `smithy_damage`): the roof damage now sits mostly on the dark east slope, where it barely reads at 1x; the bakery's lit slope shows only a 1 to 2 texel notch. Move a hole or slipped slates onto the lit slope.

### Gate (round 1)

`python3 -m scripts.review.gate --check` refuses the 6 failed pictures; the queue entries hold main's bytes. It prints `ADVISORY` for the 5 passes (library, north_cottages_damage, bakery_damage, smithy_damage, ground). A house and its damage overlay place together, so Claude A decides whether a passing overlay leaves the queue before its house passes. This round edits no queue entry, no art, no detector and no threshold.

### Files changed

- `docs/reviews/2026-11-10-front-gable-roofs.md` (this file).
- `art/catalogue/crossroads/*.json` for the 11 pictures: the `reviewer` block only (verdict, date, note, and `fix_list` where there are codes). The detectors' fields are unchanged.

### Not checked (round 1)

- The scene gate (the 24-cell grid), the night tint and the phone view in the app; no device play-test.
- Thatch gables (built, not placed), the hut and the herbalist (unchanged bytes).
- The halo claim around the stacks (36 against 38 to 43) beyond the crops, where none shows.
- Crops and measuring scripts are in the auditor's scratch folder, not committed; the Eastward crops stay local.

## Round 2 (PR #457 at 5b230ffb)

Round 2 rebuilds the 10 house and damage pictures to fix GR1 to GR3 and the polish items GR4, GR5, GR7, GR9 and GR11. It also merges main 3f0e5a49 (#456, the stall) normally. Claude A decided to skip GR6, GR8, GR10 and GR12: Matt approved the shaded slope's look, and the smithy keeps its stack. `ground.png` is byte-identical to round 1, so its pass stands. This auditor did not paint any of the art and judged it from the bytes.

**Result: 10 pass, 0 fail.** All three faults are fixed and measured. Three new polish codes remain (GR2-1 to GR2-3).

### What was reviewed and how

- Three worktrees: the PR head 5b230ffb, round 1's bytes from ff4e2bc1 and main from 3f0e5a49. The sha256 of every PNG matches its record.
- Asset gate: `python3 -m scripts.review.assets <10 refs> --record` reproduces the painter's records byte for byte (no catalogue diff). The library fails on `detail.volume`, and fern_cottage_damage fails on `detail.flat` and `detail.volume` (x2). The other 8 pass with polish. Bars: library 0.844, north cottages 0.83, bakery 0.862, smithy 0.84, fern cottage 0.851. Every bar is at or above round 1.
- All measurements come from my own scripts. They compare round 1 against round 2 with the canvas offset by 2. They cover hex runs at the stack feet, 2 columns to the east and 3 to 6 rows below; the band under the board column by column (wall median from rows 9 to 20 under the board; on the lapped gables, only columns where the board run is exactly 9); nail heads as 2 x 2 iron groups; tarp texels by hue; and timber texels in each hole.
- By eye: 4x to 10x nearest crops on neutral grey with round 1 beside round 2, each house with its overlay at 2x, and the street at 1x and 2x from `scene.composite(load_zone('crossroads'))`.
- Eastward: shot 17 brought to its native grid (`core.to_native`, scale 3.00). Box [150,0,350,140] (B5 and its roof vent) is scaled x1.37 nearest beside the smithy's stack and the fern cottage's tarp at 1x.
- Not run: calibration (no detector changed), the scene gate and a device play-test.

### Verdicts (round 2)

| Picture | Verdict | Bar | Main reason |
| --- | --- | --- | --- |
| library | pass | 0.844 | GR4, GR5, GR7 hold; `detail.volume` is the same false positive (ashlar block) |
| library_damage | pass | 0.553 | GR1: tarp Y 46 against 105.5 lit (0.44) |
| north_cottages | pass | 0.83 | GR2 and GR3 fixed; polish GR2-1, GR2-2 |
| north_cottages_damage | pass | 0.534 | GR11: east timber Y 45 (was 59) |
| bakery | pass | 0.862 | GR3 and GR7 fixed; polish GR2-2 |
| bakery_damage | pass | 0.614 | GR11: east timber Y 47 (was 71) |
| smithy | pass | 0.84 | GR3 and GR9 fixed; polish GR2-2 |
| smithy_damage | pass | 0.67 | GR11: east timber Y 43 (was 69) |
| fern_cottage | pass | 0.851 | GR2 and GR3 fixed; polish GR2-1 (3 nails), GR2-2 |
| fern_cottage_damage | pass | 0.625 | GR1: east/west 0.60; detector faults ruled a result of the clamp; polish GR2-3 |
| ground | pass (round 1) | n/a | bytes unchanged (sha 18322af2) |

### Round 1 codes, measured

| Code | Asked | Measured at 5b230ffb | Ruling |
| --- | --- | --- | --- |
| GR1 library | east part at most 0.6 of lit; nothing above tone 2; weights one step down | tarp mean Y 46.0 against 105.5 on main's lit roof = 0.44; tones #25633d / #02432c / #01211a; weights #aba194 100 → 8 texels, #332937 0 → 42 | fixed |
| GR1 fern | as above, plus a ridge crease and a lit fold | west 177, east 107 = 0.60; east tones sand_cool 2/1/0 only; #ffebc8 fold column x 121 over a #684441 crease x 122 along the whole ridge; weights #aba194 41 → 3 east | fixed (see the ruling on its detectors) |
| GR2 | lit texel at upper left, dark texel under-right, jitter, about 1 board in 4 bare | north cottages: 25 heads, 25 lit (round 1: 0 of 28), 20 distinct x (was 6), 1 of 7 boards bare. Fern: 3 heads, 3 lit, on 2 of 6 boards. Under-right texel present on 1 of 25 and 0 of 3 | fault fixed; GR2-1 |
| GR3 | 2-texel apron along the whole foot; soaker each side; shadow 3-4 below and 2 east | apron under every foot column on all four (NC 27/27, bakery 36/36, smithy 42/42, fern 27/27), lit over dark on 25, 34, 40, 25. Lit lead texels 37, 50, 54, 41 (round 1: 7 or 8). Course highlights 3 to 6 rows below the foot: 24 → 3, 37 → 12, 120 → 4, 93 → 10. East: d = 2 and 3 hold 0 to 7 highlight texels. Soakers: 3 to 6 lit texels low on the west side only; none on the east | fault fixed (reads at 1x and 2x); GR2-2 |
| GR4 | rows 1-2 nothing above 0.55 of the wall median; fade about 18 % | above 0.55: library 0 of 534 (1 stray at the foot), bakery 0 of 390, smithy 0 of 486 (1 at the foot), NC 0 of 348, fern 0 of 264 (round 1: 285, 169, 187, 92, 45). Line drop 56 / 64 / 63 / 77 / 77 %; fade 26 / 34 / 33 / 35 / 33 % | fixed: the line now reads apart from the fade, as B5's 72 / 33 / 20 % does |
| GR5 | west end #a87c52 with a 2-texel ring; 1 texel of transparent margin | all five: #a87c52 x 2 at the west cut, a #70432f arc of 2 at the next column, a 1-texel #50261d / #4d2220 outline outside each end; columns 0 and W−1 transparent | fixed |
| GR7 | no moss on the bakery's outline | green within 6 rows of every slope's back edge: 0 on all five (bakery round 1: 11, smithy 10); (17,94) and (14 to 17,98) now #787e9c | fixed |
| GR9 | record each pot; smoke on one | smithy pots (181,34) and (195,32); the west pot spans canvas x 175 to 185, with its rim on row 33; SmithySmoke (1542,531) → (1535,533) = 1500 − 146 + 181, 840 − 341 + 34 | fixed |
| GR11 | hole timber east one step down | NC 59 → 45, bakery 71 → 47, smithy 69 → 43 (lit-side holes 100, 82, 60) | fixed |

At 1x in the street, every stack now carries a pale line along its foot and reads as standing on the slope. At 2x, the smithy's smoke rises from the west pot.

### Rulings on the detector findings and the painter's flags

- **(a) Library `detail.volume` [101,164,126,173]: false positive, as in round 1.** It is the same block, moved 2 texels with the canvas: lit top arris row #e8d6b7 and west arris, body #cdbea3 tooled with #afa490, shaded lower row #908377, mortar #70625f. It is a modelled ashlar block, not wood.
- **(b) fern_cottage_damage `detail.flat` [146,53,164,118] and `detail.volume` [130,44,146,95] / [146,53,164,118]: a result of the correct shading, not a fault.**
  - The east half is darkened two steps and capped at tone 2, as GR1 asked. Both ends of the map clamp, so the lit ramp's tones 1 and 2 (#926f5a, #b49271; 219 + 651 texels in round 1) both land on sand_cool 0 #684441 (825 texels). The tones above them (#ffebc8, #efd09c) fold into sand_cool 2.
  - The fold trough at x 147 to 155, y 54 to 117 is therefore a flat 9 x 64 slab. That slab is the detector's 50 % patch.
  - The cloth still reads as draped cloth at 1x and 2x: three value bands across each fold, the ridge crease, the stain and the stitched seam. Like Eastward's shaded planes, it is calm without being shapeless.
  - Polish GR2-3 restores the trough's lost value step with a dark crease, without lightening anything.
- **Cluster noise and `detail.light` on the houses:** kept as measurements. Every bar rose slightly from round 1.

### Logic and other changes

- **GR5 widening.** Every canvas grew by 4 texels, 2 each side: library and north cottages 312 → 316, bakery and fern cottage 240 → 244, smithy 288 → 292. Heights are unchanged.
  - kit.json moves each house and damage offset x by −2, and nothing else. Positions, y offsets and every other object are identical to round 1.
  - The piece files change only `version`, the foot's x (+2, in canvas coordinates), `size_px` and `size_cells` x (+1, which `rules.scale` requires). Footprint and collision are unchanged; the `.tscn` offsets match.
  - The doors stand in the same place. Below the eave, the only changes are the phase of patterns keyed to canvas x: the doors' kick-plate hatch, the smithy hood's seams, and the lit slopes' per-slate highlights. These are the same recipe, with no regression.
  - On the lapped gables, the board grain and plaster dashes re-rolled. The painter's note that the house's other draws are unchanged does not hold for these two houses, though nothing got worse.
  - The damage overlays' tarp and window boarding re-rolled with the new draws.
- **Unlisted change at the stacks.** In round 1, the slope 4 to 8 columns east of each stack had almost no course highlights (smithy: 0 or 1 a column). Round 2 draws them at the open slope's density (22 to 27). The contact shadow is now the 2 columns that GR3 asked for, but it is narrower than the vent shadows in Eastward's shot 17 (about 6 native px). This is part of GR2-2.

### The composite and the merge

- `sha256(scene.composite(load_zone('crossroads')))` gives c0de8798… at 5b230ffb, 09d21a69… at main and 16bb4807… at ff4e2bc1. All three reproduce.
- **The stall is main's new stall.** The stall box (1083,610)-(1221,772) has 0 changed texels against main and 4,078 against round 1. In the committed composite it is the chalk board with a plum and "3d", and the burlap sack. Round 1's composite shows the old lettered board and the white sack, which is probably what the earlier crop showed.
- kit.json's stall and every other object match main. The sprite set is unchanged.
- 233,508 texels change against main:
  - 222,621 inside the ten house boxes (old and new);
  - 3,046 inside the five prop-shadow boxes;
  - 2,824 inside the smoke box, outside the house boxes;
  - 5,017 elsewhere. All of these are `ground.png` changes (the casts), 1,359 of them within 6 texels of a house box.
- The painter splits the last two items as 5,005 + 358 + 2,478 = 7,841, which equals my 2,824 + 5,017. The split differs only where the smoke's box overlaps the smithy's cast. Nothing else moved.

### Eastward comparison (B5, shot 17, x1.37)

- **Stack.** B5's roof vent stands on a dark outline with a contact shadow dithered about 6 native px to its east and below. The stack's foot now has its lit edge, and the clean floor tone under it matches that grammar. The east shadow is narrower than B5's (GR2-2).
- **Tarp.** The shaded half of the tarp sits in the value range of B5's shaded wall. Its fold bands keep the cloth readable.
- **Board edge and band.** The board and its band now match B5's crisp line under the verge.

### Fix list (round 2, polish only)

Each code is also in the picture's `reviewer.fix_list`.

- **GR2-1** (`north_cottages`, `fern_cottage`): the dark under-right texel of each nail head is tidied away. It is the board's own tone on 24 of 25 heads and on 3 of 3; add it to finish()'s keep mask. On the fern cottage, only 3 heads stand on 2 of the gable's 6 boards (the boards at y 113, 143, 152 and 163 are bare). Make the skip per board so no more than about one board in three goes bare, or reseed until it does.
- **GR2-2** (`north_cottages`, `bakery`, `smithy`, `fern_cottage`):
  - Draw a 1-texel soaker column up each side face above the apron: west slate_cool 4, east slate_cool 3. Today the soakers are 3 to 6 texels low on the west side, and there is none on the east.
  - Widen the east contact shadow to about 4 columns at the floor tone, fading by columns 5 and 6, as Eastward's vents do.
- **GR2-3** (`fern_cottage_damage`): break the flat trough without lightening it.
  - Where the lit cloth had tone 1 (the fold cores), draw a 1-texel crease of the tarp's outline dark #3d2d30 down the middle of each trough wider than 4 texels.
  - Break each crease with a sag every 10 to 12 rows: 1 texel of #8c6556 on the crease's east side.
  - Check: east/west mean at most 0.6, no texel above sand_cool 2 east of the ridge, and the box's largest one-tone patch under 35 %.

Codes skipped by Claude A's decision stay open in round 1's list: GR6, GR8, GR10, GR12.

### Gate (round 2)

`python3 -m scripts.review.gate --check` passes. It prints `ADVISORY` for all 11 crossroads pictures in this PR: their records pass, so they can leave `art/catalogue/fix-queue.json`. This round edits no queue entry, art, detector, threshold or CI.

### Files changed (round 2)

- This file.
- `art/catalogue/crossroads/*.json` for the 10 house and damage pictures: the `reviewer` block only, plus `fix_list` where there are codes. Detector fields are unchanged.

### Not checked (round 2)

- The scene gate, the night tint, the phone view and a device play-test.
- `npm run verify` and the CI result: this audit changes only review files.
- The crops and measuring scripts stay in the auditor's scratch folder. The Eastward crops stay local.
