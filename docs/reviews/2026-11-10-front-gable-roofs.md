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
