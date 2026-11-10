# Detail audit: the 24 never-reviewed woodland assets (9 Nov 2026)

The asset gate on the woodland pictures that the review gate (#439) refuses as never reviewed, by the detail-auditor (`.claude/agents/detail-auditor.md`), on `main` at **d647b98b**. This reviewer drew none of them, so the independence rule holds. Earlier "all pass" records were the detectors alone (`reviewer.verdict: pending`) and were not used.

**Result: 0 of 24 pass. 24 fail (1 blocker, the willow).** Most of the failures come from one cause. The 15 trees and shrubs share one foliage painter, and its crowns miss Eastward's foliage band by 26 to 47 % (shapes). The 8 stones share one stone painter, which speckles every face. Fixing those two painters fixes most of this list. The two hatches are separate work.

Nothing was repainted. The fix queue, `gate.py`, the scenes and `.github` are untouched. **Consequence for the gate:** all 24 now carry `reviewer.verdict: fail`, and the main gate refuses a `fail` verdict outside the fix queue. So `npm run check:kit` refuses them until the queue's owner queues them or the art is fixed and re-reviewed. Under #439 they were refused already, as pending.

## What was reviewed and how

- **Subject.** `game/zones/woodland/art/{beech, birch, bramble, bramble_b, bush, bush_b, bush_c, hatch_closed, hatch_open, hollow_tree, holly, holly_b, lintel, oak, pine, sapling, standing_stone, standing_stone_b, standing_stone_broken, standing_stone_lean, standing_stone_low, standing_stone_runes, stone_top, willow}.png`. These are placed by `woodland_base.tscn` (the hatches by `woodland.tscn`). The list is the woodland group of the #439 triage.
- **Calibration first.** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <refs-games/eastward>` gave recall **39 of 39**. False positives were 5 on 6 clean screens and 21 on 22 clean props. The rewritten `calibration_results.json` was not committed.
- **Asset gate.** `npm run review:asset -- woodland/<name>` for all 24, then `--record`. The sheets are in `artifacts/review/assets/` (not committed). Detector result: **23 pass, 1 fail** (`hatch_closed`, `detail.cluster_noise` 60.6 %, a fault). A newer detector caught this since its 4 Nov record. Every foliage, stone and prop picture carries a `detail.bar` polish under 0.9.
- **Context at 1x.** `npm run review:scene -- woodland --no-render` composed the zone (960 x 1728 art px). From it I cropped the stone circle, the east oaks and willow, the north grove with the hollow tree, and the south grove, at 1x and 3x. The hatches were pasted at their scene position (336, 1032; offset -22, -57) and viewed at 4x.
- **Enlarged.** Every asset at 4x to 7x on neutral grey, crowns and trunks at 6x to 8x, each part in turn.
- **Measurements of my own** (art px, H = 74), from `metrics.py` in the scratchpad:
  - lone texels: a texel unlike all four neighbours, as a share of the interior (house limit 6 %);
  - the largest region of one colour;
  - mean L of the west half minus the east half;
  - the longest run of a silhouette edge that stays within 1 px;
  - `scripts/review/cluster_noise.py` on all 24.
- **Eastward at the same character height.** Native 640 x 360 boxes, scaled by 1.37 with nearest neighbour:

  | Ours | Eastward shot and box |
  | --- | --- |
  | oak, beech, hollow tree, willow, birch, sapling | the red tree in 12 (465,110,590,230), the trees in 13 (345,150,395,235) and (510,150,565,230) |
  | pine | the pines in 12 (175,65,245,165) |
  | bushes, brambles, holly | the bush under the red tree in 12; the trees in 13 |
  | standing stones, lintel, stone top | the rocks in 17 (460,165,550,250), 12 (497,205,555,235) and 13 (325,247,350,268) |
  | hatches | the post box in 12 (387,200,420,248) and the bench in 17 (410,15,472,55), for wood, iron and value range |

  A 64 x 64 window of the oak's crown was put at 8x beside the same window of the red tree in 12 (`oak_crown_vs_ew.png`, in the scratchpad).

## Verdicts

The bar is `detail.bar` against Eastward's band (foliage 27.71 tones and 63.32 shapes a patch; stone 26.25 and 61.0; prop 27.0 and 50.36). House-style 7 needs 0.9, or 0.85 on tones for ramp-built art. Noise is `cluster_noise`, where 48 % or more is a fault.

| Asset | Size (art px, H) | Bar | Lone | Noise | Verdict | Findings |
| --- | --- | --- | --- | --- | --- | --- |
| oak | 194 x 233, 3.15 H | 0.56 | 2.2 % | 25.7 % | fail | W-T1, W-T2 |
| beech | 154 x 242, 3.27 H | 0.61 | 2.3 % | 22.6 % | fail | W-T1, W-T3 |
| birch | 86 x 192, 2.59 H | 0.67 | 2.4 % | 24.9 % | fail | W-T1, W-T4 |
| pine | 107 x 229, 3.09 H | 0.62 | 2.3 % | 26.0 % | fail | W-T1, W-T5 |
| hollow_tree | 211 x 299, 4.04 H | 0.57 | 1.9 % | 21.8 % | fail | W-T1, W-T6 |
| willow | 202 x 284, 3.84 H | 0.65 | 3.2 % | 26.0 % | **fail (blocker)** | W-T1, W-T7 |
| sapling | 55 x 80, 1.08 H | 0.53 | 1.9 % | 23.7 % | fail | W-T1, W-T8 |
| bush | 94 x 63, 0.85 H | 0.64 | 2.7 % | 26.1 % | fail | W-B1 |
| bush_b | 76 x 54, 0.73 H | 0.57 | 2.4 % | 31.7 % | fail | W-B1 |
| bush_c | 112 x 58, 0.78 H | 0.63 | 2.6 % | 23.6 % | fail | W-B1 |
| bramble | 102 x 47, 0.64 H | 0.68 | 3.3 % | 30.3 % | fail | W-B1, W-B2 |
| bramble_b | 89 x 47, 0.64 H | 0.63 | 3.5 % | 26.1 % | fail | W-B1, W-B2 |
| holly | 81 x 73, 0.99 H | 0.62 | 3.0 % | 35.2 % | fail | W-B1, W-B3 |
| holly_b | 91 x 79, 1.07 H | 0.74 | 3.0 % | 33.9 % | fail | W-B1, W-B3 |
| standing_stone | 35 x 89, 1.20 H | 0.61 | **9.2 %** | 31.4 % | fail | W-S1, W-S2 |
| standing_stone_b | 40 x 67, 0.91 H | 0.77 | **10.5 %** | 38.5 % | fail | W-S1, W-S2, W-S3 |
| standing_stone_broken | 43 x 56, 0.76 H | 0.78 | **11.4 %** | 36.0 % | fail | W-S1, W-S2, W-S5 |
| standing_stone_lean | 39 x 73, 0.99 H | 0.75 | **9.8 %** | 30.7 % | fail | W-S1, W-S2 |
| standing_stone_low | 67 x 56, 0.76 H | 0.78 | **9.8 %** | 33.3 % | fail | W-S1, W-S2 |
| standing_stone_runes | 39 x 65, 0.88 H | 0.85 | **11.7 %** | 45.4 % | fail | W-S1, W-S2, W-S3 |
| lintel | 79 x 28, 0.38 H | 0.57 | **6.4 %** | 35.5 % | fail | W-S4 |
| stone_top | 37 x 22, 0.30 H | 0.56 | **6.5 %** | 35.0 % | fail | W-S4 |
| hatch_closed | 44 x 40, 0.54 H | 1.06 | 1.6 % | **60.6 %** | fail | W-H1 |
| hatch_open | 44 x 66, 0.89 H | 0.91 | 1.1 % | 47.2 % | fail | W-H1, W-H2 |

## Findings and fixes

### Foliage (shared painter: every tree and shrub)

**W-T1 / W-B1. Crowns sit below Eastward's foliage band and read as soft broccoli, not leaf clusters.** Fault, on all 15 trees and shrubs. Crop: `oak_crown_vs_ew.png`.

What is wrong:
- **Bar.** 0.53 to 0.75: tones 17.1 to 24.7 against 27.71, shapes 33.5 to 47.5 against 63.32.
- **Ticks everywhere.** At 8x, the oak's crown is soft-edged domes, each covered evenly with one stamp: a lighter 2 to 3 texel tick. The tick is the same size and orientation in the lit cap, the body and the deep under-band. Art-style says the deep band stays quiet and the leaf marks are sparse.
- **Stamping.** On the big crowns, 32 to 40 % of the varied 3 x 3 windows repeat four or more times (oak 36.2 %, willow 40.3 %, hollow tree 34.6 %, beech 32.6 %). That is stamping.
- **Domes do not meet in scallops.** Eastward's red tree has leaf-shaped clusters of about 4 to 8 texels at our scale, with dark pockets between them and lit tips pointing down. Our domes meet in blotchy dithered seams.
- **Smooth silhouettes.** The silhouette is a run of smooth bumps, with no leaf tips breaking it.
- **Large one-colour regions.** The largest single-colour region is 3,180 px in the beech, 4,250 in the oak and 5,309 in the willow, mostly the deep under-band.

Fix, in the density-3 foliage painter, for every kind:
1. Build each clump's tone boundaries as leaf-shaped scallops 4 to 8 texels wide, with lit tips pointing down (art-style "Density 3"). A dark pocket (leaf tone 0 or 1, 2 to 4 texels) sits where a clump tucks under the one in front.
2. Cut the tick stamp from the deep band entirely. In the body, place ticks only along the lit rim of each clump, at about a third of today's density. Draw them from 3 or 4 shapes (domino, L, 2 x 2, 3-texel arc) in random orientation, so no 3 x 3 pattern repeats more than about 15 % (today 32 to 40 %).
3. Add sibling-ramp swaps (warm and cool leaf siblings) per clump to reach about 24 tones a patch (0.85 x 27.71) without contrast noise. Add yellow-green rim glints (grass 5) in pairs on the upper-left clumps only.
4. Break the silhouette with leaf tips, 2 to 4 texels, every 6 to 12 texels along the top and west rims, so it reads as leaves and not as a bumped outline.
5. Check: `detail.bar` at least 0.9 on shapes, `cluster_noise` 32 % or less, and lone texels 3 % or less. Compare again at 8x with `redtree12` and `tree13`.

**W-T2. The oak's trunk** (fault). The trunk is a straight column 40 px wide at 30 rows up and 48 at 12 rows up. It flares only in the last 12 rows, to 62, and has no roots. The bark is 1-texel vertical dashes 3 to 8 long. Under the crown, the top of the trunk is lit the same as its middle.

Fix:
- **Taper.** Taper the trunk 2 to 4 px over its height.
- **Roots.** Flare it into 2 or 3 roots over the last 16 to 20 rows. Each root is lit on its west top, dark on its east side, and reaches 6 to 12 px out.
- **Bark.** Draw bark as plates 3 to 5 px wide and 6 to 12 tall, each with a lit west edge and a dark crack (timber 0 or 1) between plates, not as single-texel dashes.
- **Crown shade.** Put a shade band from the crown, two tones down for 6 to 10 rows, across the top of the trunk.

**W-T3. The beech's trunk is a pipe** (fault). It is three flat vertical bands of grey with two straight horizontal rings and a one-texel step in width at about 40 % of its height, so it reads as a telescoping post. It has no flare: one texel at the foot.

Fix:
- **Shape.** Remove the rings and the step.
- **Bark.** Smooth grey bark with a cylinder ramp: a highlight band in the west third, and the core shadow at the east edge, one tone from the outline. Mottle it with sibling patches of 3 to 6 texels and 2 or 3 dark eye scars (3 x 2).
- **Foot.** Add a buttressed foot that flares 8 to 10 px over its last 10 rows.
- **Crown shade.** Add the crown's shade band, as in W-T2.

**W-T4. The birch's trunk** (fault). It stays 14 px wide for 53 rows, with no flare and the same white to its foot.

Fix:
- **Foot.** Darken the lowest 10 to 14 rows into a rough, fissured base (dark bark in plates).
- **Flare.** Add a 4 to 6 px flare.
- **Lenticels.** Vary the horizontal lenticels in length (2 to 6) and give each a lit lower lip.
- **Crown.** Shade under the crown. Thin the crown's lower edge into hanging twig clusters, so the birch reads lighter than the oak.

**W-T5. The pine** (fault).
- **Tiers.** The tiers read, but each tier's rim is a smooth stepped line.
- **Ticks.** The tiers carry the same ticks as the broadleaves.

Fix:
- **Needle tips.** Break each tier's lower edge into downward needle tips, 2 to 4 texels every 4 to 6 texels.
- **Shade.** Give each tier a dark underside (leaf 0 or 1, 2 to 3 rows), and a lit west tip, as Eastward's pines in 12.
- **Trunk.** As in W-T2.

**W-T6. The hollow tree is not a veteran tree** (fault).
- **Proportions.** The crown sits on a straight pole: its sides stay within 1 px for 85 to 93 rows (1.2 H), 44 to 52 px wide. A veteran is squat and gnarled.
- **The hollow.** It is a flat dark oval (about 12 x 16) with two yellow eye pixels and a 1-texel rim, a sticker on the bark.

Fix:
- **Bole.** Shorten the bare trunk to about 0.6 H, widen the bole to 60 to 70 px, and give it burrs, a lightning-split scar and roots as in W-T2.
- **Hollow.** Draw it as an opening with depth: a lip 2 to 3 texels thick, lit on its lower and west edge, the far inner wall lit, the near inner wall in shade, falling to near-black at the back. Keep the eyes, but set them inside the dark.

**W-T7. The willow is not a willow** (blocker).
- **Crown.** It is an oak dome with straight vertical sides: the west edge stays within 1 px for 52 rows and the east edge for 58 rows (0.7 to 0.8 H). The result is a box silhouette, against rule 3 of art-faults ("no perfect shapes in nature").
- **Strands.** They are straight vertical lines 1 to 3 texels wide, in an even comb across the whole width, starting in mid-crown. Nothing arches.
- **Outline.** Only 18 % of the silhouette is in an edge tone.
- **In context.** At 3x in the zone, the strands read as rain or a bead curtain, and the trunk's foot stands on the path. The trunk on the path is a logic finding for the logic-auditor.

Fix:
- **Redraw the form:**
  1. a short, wide trunk splitting into 3 or 4 limbs;
  2. limbs arching up and out;
  3. curtains of hanging leaves falling from the limbs in tapering swags 4 to 8 texels wide, each lit on its west side with a dark east side and leaf tips in its outline;
  4. gaps between swags that show the dark interior and the trunk.
- **Silhouette and outline.** Make the silhouette a weeping dome, wider at the bottom, with no straight sides. Close it in leaf edge tone.

**W-T8. The sapling's stem** (fault). The stem is an 8 px straight three-tone rod, ending in a bevelled pencil point with no foot.

Fix:
- **Stem.** Taper the stem from 5 to 3 px with a slight bend. Give it 2 small side twigs under the crown.
- **Foot.** Add a 2 to 4 px root flare that meets the ground, with a contact line. A stake and tie would add a story detail if it was planted.

**W-B2. Brambles are bushes with dots** (fault).
- **Berries.** Each bramble's berries are three identical 2 x 1 pairs of the same red, which read as pairs of eyes.
- **Canes.** There are no arching canes and no thorns.

Fix:
- **Canes.** Draw 3 to 5 arching canes, 2 texels thick (berry or earth ramp, a lit top edge), looping out of the mass and back to the ground past its silhouette.
- **Berries.** Draw clusters of 3 to 6 drupelet berries, each 2 x 2. Mix ripeness (green, red, near-black berry tones) and give each a one-texel glint at the top left.
- **Leaves.** Use serrated leaf tips on the silhouette.

**W-B3. Holly has no holly leaves** (fault).
- **Leaves and silhouette.** The leaves are the same soft clumps as the bush, and the silhouette is round.
- **Berries.** They are single 2 x 2 red squares spaced evenly (5 or 6), with no highlight.

Fix:
- **Leaves.** Draw the mass from glossy dark leaves (leaf cool 1 to 3) with spined points of 2 texels that break the silhouette every 3 to 5 texels. Give each leaf a hard one-texel specular glint (tone 5) on its upper-left lobe.
- **Berries.** Gather them in clusters of 3 to 5 at leaf axils, each with a glint.
- **Shape.** Give holly_b a conical habit to tell it from holly.

### Stone (shared painter: six standing stones, the lintel and the stone top)

**W-S1. Faces are single-texel speckle** (fault).
- **Speckle.** Lone texels are 9.2 to 11.7 % of the interior in the six standing stones (house limit 6 %) and 6.4 and 6.5 % in the lintel and stone top.
- **No large planes.** At 6x, every face is an even mottle of 1 to 2 texel specks over the lit band, the body and the shade alike. Eastward's rocks in 17 and 12, at the same height, are calm domes with large planes, a few tones each, clusters of 3 to 6 texels and dark gaps between masses.
- **At 1x** in the circle, the stones read as grey grain.

Fix:
- **Planes.** Paint each stone as 3 to 5 large planes, as in the stone recipe and eastward-edges 2.3:
  - a lit crown at stone 4 with a stone 5 rim on the upper-left arris;
  - a mid west face at stone 3;
  - a darker east flank at stone 1 to 2;
  - a dark underside at the foot.
- **Texture.** Add texture as sibling swaps in clusters of 2 to 4 texels at the same tone, plus a few 1-tone steps, keeping lone texels at 3 % or less.
- **Edges and cracks.** Knock off 2 or 3 chips per stone at the arrises. Cut each crack 2 texels wide: a dark line with a lit lower lip.

**W-S2. Lichen, moss and the grass skirt** (fault).
- **Lichen.** Lichen is round tan coins 4 to 6 texels across, each with a darker rim, the same shape repeated 2 to 4 times per stone.
- **Moss.** Moss is 3-texel green flecks scattered mid-face.
- **Grass skirt.** Every stone carries a baked grass skirt: a comb of vertical blades with a white daisy, ending in a straight horizontal bottom edge. In the zone at 3x that edge reads as a strip under each stone. On the large stone it runs past the stone's east side. This is art-faults 01, a thin painted strip.

Fix:
- **Lichen.** Grow lichen as irregular crusts of 2 to 3 sibling tones, 3 to 10 texels across, on the lit and upper faces. No two the same shape.
- **Moss.** Put moss low and on the shaded north and east sides and in cracks, as a 2-texel cap over a 4-texel band (the stone recipe).
- **Foot.** Remove the baked skirt. End the stone in a contact line (stone 0 or 1) one texel under its foot. Let the ground painter's tufts grow over the foot (eastward-edges 8.2), or, if they stay in the sprite, use 2 to 4 irregular tufts that fade out, with no straight bottom row.

**W-S3. Glyphs** (fault).
- **standing_stone_b.** It carries a pale blue spiral, about 9 x 9, in two flat tones. It is painted on, not carved, and pale blue is not on the stone ramp: a UI glyph (calibration: "a waystone that reads as a UI block").
- **standing_stone_runes.** Its runes are 1-texel vertical scratches with pale blue specks.

Fix:
- **Spiral.** Cut the spiral as a groove: each line 2 texels wide, stone 1 on its upper edge (in shade) and stone 4 on its lower lip (catching light), weathered and broken in 1 or 2 places.
- **Runes.** Make them branching strokes 2 texels wide, cut the same way. If they are meant to glow, use one glow family (house-style 1) inside the grooves only, and justify it in the quest.

**W-S4. The lintel and stone top** (fault).
- **What is right.** Both have the right three planes: a lit top, a mid front, a dark end.
- **What is wrong.**
  - The top plane is the speckle terrazzo (W-S1).
  - The arrises are straight lines with no chips.
  - The moss flecks are as in W-S2.
  - Bar 0.56 to 0.57 against the prop band.

Fix:
- **Top plane.** Repaint the top as one calm plane with 2 or 3 broad sibling patches and lichen crusts.
- **Arrises.** Chip both front arrises (2 to 4 chips, each a notch in the lit edge with a shade texel under it). Add a tooling or weathering band along the front.
- **Lintel.** Show the lintel's mortise sockets: two 4 x 3 recesses on the top, lit on their far wall, so it reads as a fallen lintel.

**W-S5. Detector findings rejected** (2). `logic.scale` on `standing_stone_broken` and `standing_stone_low` (56 px, 0.76 H, against 59 to 126) is rejected: a broken stone and a low stone are short by design. The broken stone still needs a fracture face. Its top should be a lit, jagged fracture plane (stone 4 to 5, with 1 to 2 texel steps) and not a rounded crown. Today it is rounded like the whole stones.

### Hatches

**W-H1. The hatch frame and lid** (fault; `detail.cluster_noise` 60.6 % on hatch_closed, the detector's fault).
- **Light.** The frame's blocks are lit evenly all round. Mean L west minus east is +1.2 (closed) and +2.4 (open), so there is no light direction. The north inner reveal is not shaded.
- **Door grain.** The door's planks carry random 2 x 2 value grain (60.6 %, over every Eastward prop box).
- **Iron.** The two iron straps are flat two-tone bars, and the ring is a black U glyph.
- **Apron.** The frame sits in a hard rectangular tan apron, 2 texels wide, with straight sides and no frayed turf edge (eastward-edges 5.1).
- **The good parts.** The ashlar blocks and the corner moss are good.

Fix:
- **Frame light.** Light the frame from the upper left:
  - the north and west copings a tone lighter on top;
  - the south and east copings a tone darker;
  - a 2-row shade on the inner north reveal (the opening's head);
  - a lit inner south lip.
- **Planks.** Follow the wood recipe: three sibling boards with a dark joint line, grain as 2 to 4 texel streaks along each board, swaps at the same tone, at most 10 % one-tone steps.
- **Straps.** Iron straps with a lit top row, a dark bottom row and nail heads (a dark texel with a lit texel above) at each board.
- **Ring.** A ring with a lit upper-left arc and a shade under it on the boards.
- **Apron.** Replace the apron with the turf's frayed edge to worn earth, 2 to 3 px with tufts and bites (5.1). Add a contact line round the frame.

**W-H2. The open hatch** (fault).
- **Lid.** The lid hangs above the frame on two 1-texel grey rods, with a 1-row gap. It has no thickness, no hinge leaves and no cast shadow.
- **Shaft.** Three flat grey horizontal stripes of equal height under a navy band, with a row of 5 or 6 blue squares in it. The squares read as debug marks, and the stripes have no tread or riser.

Fix:
- **Lid.** Hinge the lid on the north coping, with two hinge leaves (iron, 3 x 4, lit top). Show its edge as 2 to 3 rows of end grain (lit top). Cast its shadow north-east, two tones down onto the coping and turf behind.
- **Shaft.** Draw 3 or 4 stone steps going down into the shaft. Each step has a lit tread nosing (stone 4) and a dark riser (stone 1). The steps shrink a texel per step, and the light falls off to near-black at the bottom (the Undercroft's falloff).
- **Blue squares.** Remove them. If they stand for the Undercroft's glow, use a soft glow pool (one glow family) on the lowest step only.

## Per-part notes

- **Oak, beech, pine, hollow tree.**
  - Crown: domes lit at the upper left. West minus east is +20.8 to +27.8 L, so the light direction is right.
  - Outline: the silhouette's edge is clearly darker than the body (ring L 60 to 64 against 108 to 111), in leaf edge tone.
  - Trunks: as in W-T2 to W-T6.
  - Shadows: none in the sprite. The ground carries them, thrown east and down (checked in the zone at 3x).
- **Birch.** The lenticels read, but are all 1 row tall.
- **Willow.** As in W-T7. The crown's right side in the zone is a visible vertical wall.
- **Bushes.**
  - Base: sits on the ground with no stems. Good.
  - Clumps and light: the clumps read at 1x, lit at the upper left (+25 L).
  - Shortfall: only W-B1.
  - Closeness: the three bushes are the closest of the set to passing.
- **Brambles and holly.** The bush structure plus W-B2 and W-B3.
- **Stones.**
  - Light: lit west, dark east (+32.8 to +46.4 L), so the light direction is right.
  - Outline: a dark outline on the top and east, broken on the lit west (the lit break), right.
  - Shadows: the zone carries cast shadows east and down.
  - Shortfall: W-S1 to W-S3.
- **Lintel and stone top.** The planes are right. W-S4.
- **Hatches.** The frame is the one finished part. W-H1 and W-H2.

## False positives

2 rejected: `logic.scale` on `standing_stone_broken` and on `standing_stone_low` (W-S5). The `detail.outline` polish on the stones (33 to 37 % edge tone) is not rejected but is low priority, because the west side's lit break is the house rule. All other detector findings stand.

## Not checked

- **No in-game render.** The scene was composed from the scene data (`--no-render`). Day and night were not compared, and nothing was checked under the night tint or on a phone.
- **Scene grid cells.** The scene gate's 6 x 4 grid cells were not visited one by one. This was an asset gate; the context crops covered the stone circle, the east grove, the north grove and the south grove.
- **Hatch states.** The hatch was seen pasted into the composite, not in its live state switch.
- **Other woodland assets.** `forest_bench`, `mossy_log`, `stump` and `flow` were outside this list.
- **No fixes.** Nothing was repainted.

## Round 2: the redraw in #446 (9 Nov 2026)

The asset gate on draft PR #446 (`claude-a/woodland-redraw`, head **487a1b91**), which redraws all 24 assets above and changes `woodland/ground` (the redrawn trees' and stones' cast shadows). Reviewed by a detail-auditor that drew none of it.

**Result: 2 of 25 pass (`standing_stone_lean`, `ground`). 23 fail, none on a blocker.** The willow blocker (W-T7) is fixed. The stone painter's speckle (W-S1) is fixed on all eight stones. The trees and shrubs are much closer than in round 1 (bar 0.53 to 0.75 then, 0.71 to 0.84 now), but none reaches 0.9 on shapes. The crowns still read as cauliflower: masses cut apart by drawn seam bands, with fine mottle inside instead of leaf clumps.

### What was reviewed and how

- **Calibration first.** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <refs-games/eastward>`: recall **39 of 39**. False positives: 5 on 6 clean screens and 21 on 22 clean props, the same as round 1. `calibration_results.json` was reverted afterwards.
- **Asset gate.** `npm run review:asset -- woodland/<name>` for all 25, then `--record`. Detector result: **25 pass**, with no blocker or fault findings. Every foliage and stone sheet carries a `detail.bar` polish except `standing_stone_lean` and `standing_stone_runes`. The other polish findings are `detail.light` (oak, willow, hatch_closed), `detail.cluster_noise` and `detail.outline` (both hatches) and `logic.scale` (hollow tree, standing_stone, broken, low).
- **Context.** `npm run review:scene -- woodland --no-render` **refuses** at this head, with `woodland_kit: incomplete scene intake: stale bake: scene/plan material differs at 20,35`. #446 changes the plan rows of `game/kit/zones/woodland_kit.json` (rows 47 to 51) without that zone's scene. I did not check whether main refuses as well. The zone was composed directly (`scene.composite(load_zone('woodland'))`), and from it I cropped the stone circle, the willow and path, and the north grove at 2x and 3x. The hatches were pasted at their node position (313, 974).
- **Enlarged.** Every asset at 4x, and crowns, trunks, hollow, spines, berries, stones and hatches at 6x to 8x.
- **Measurements.** These use round 1's `metrics.py` unchanged:
  - lone texels;
  - the largest single-colour region;
  - west minus east L;
  - the share of varied 3 x 3 windows that repeat four or more times;
  - `cluster_noise.py`.
  
  Added this round:
  - row profiles through the crown seams;
  - trunk width per row and trunk L by fifths west to east;
  - pine tier spacing and the cone edge's deviation from a straight line;
  - enclosed sky holes and the L of their rim;
  - holly spine texels joined only at a corner, and berry-cluster patterns;
  - the scene's node offsets against each picture's opaque foot.
- **Eastward at the same character height** (x1.37, nearest neighbour):
  - the trees: the red tree in 12 (465,110,590,230) and the trees in 13 (345,150,395,235 and 510,150,565,230);
  - the pine: the pines in 12 (175,65,245,165);
  - the stones: the rocks in 17 (460,165,550,250) and 12 (497,205,555,235);
  - the hatches: the post box in 12.
  
  A 90 x 90 window of the oak's and the beech's crowns was set at 5x beside the same window of the red tree. I also read the coordinator's sheets: `wr/ew_cmp_trees2.png`, `ew_cmp_trees2b.png`, `woodland_contact2_4x.png` and `trees_pass1_vs_pass2_2x.png`.

### Verdicts

Bar is `detail.bar` (house-style 7: 0.9, or 0.85 on tones for ramp-built art). Noise is `cluster_noise` (48 % or more is a fault). "Rep" is the share of varied 3 x 3 windows repeating four or more times (round 1: 32 to 40 % on the big crowns).

| Asset | Opaque (art px, H) | Bar (tones / shapes) | Lone | Noise | Rep | W-E L | Verdict | Old codes | New codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oak | 194 x 248, 3.35 | 0.81 (24.3 / 51.0) | 0.9 % | 18.0 % | 2.2 % | +23.2 | fail | W-T1 partly, W-T2 partly | W2-F1, F2, F3, F4, W2-T2 |
| beech | 175 x 267, 3.61 | 0.74 (23.1 / 46.5) | 0.7 % | 14.1 % | 0.7 % | +30.7 | fail | W-T1 partly, W-T3 partly | W2-F1, F2, F3, F4, W2-T3 |
| birch | 92 x 205, 2.77 | 0.81 (29.6 / 51.4) | 1.8 % | 16.9 % | 0.4 % | +29.4 | fail | W-T1 partly, W-T4 partly | W2-F1, F2, F3, F4, W2-T4 |
| pine | 105 x 232, 3.14 | 0.74 (31.5 / 47.0) | 0.8 % | 38.7 % | 0.9 % | +26.9 | fail | W-T1 partly, W-T5 partly | W2-F4, W2-T5 |
| hollow_tree | 212 x 212, 2.86 | 0.76 (25.0 / 48.1) | 1.1 % | 19.0 % | 1.4 % | +15.1 | fail | W-T1 partly, W-T6 partly | W2-F1, F2, F4, W2-T6 |
| willow | 260 x 202, 2.73 | 0.84 (29.3 / 53.1) | 0.3 % | 22.6 % | 3.5 % | +12.5 | fail (no longer a blocker) | W-T1 partly, **W-T7 fixed** | W2-F1, F4, W2-T7, W2-L1 |
| sapling | 57 x 85, 1.15 | 0.78 (31.2 / 49.2) | 1.2 % | 18.7 % | 0.0 % | +22.2 | fail | W-T1 partly, **W-T8 fixed** | W2-F1, F2, F4 |
| bush | 100 x 66, 0.89 | 0.78 (33.2 / 49.2) | 1.2 % | 24.5 % | 0.3 % | +25.6 | fail | W-B1 partly | W2-B1 |
| bush_b | 81 x 56, 0.76 | 0.84 (34.5 / 53.1) | 1.4 % | 35.4 % | 0.0 % | +30.5 | fail | W-B1 partly | W2-B1 |
| bush_c | 114 x 60, 0.81 | 0.74 (31.3 / 47.1) | 1.2 % | 27.2 % | 0.0 % | +23.7 | fail | W-B1 partly | W2-B1 |
| bramble | 115 x 52, 0.70 | 0.71 (39.2 / 45.2) | 4.0 % | 31.7 % | 0.0 % | +14.5 | fail | W-B1 partly, W-B2 partly | W2-B1, W2-B2 |
| bramble_b | 100 x 50, 0.68 | 0.71 (35.5 / 45.0) | 3.9 % | 30.3 % | 0.0 % | +10.6 | fail | W-B1 partly, W-B2 partly | W2-B1, W2-B2 |
| holly | 85 x 75, 1.01 | 0.74 (31.3 / 46.9) | 5.9 % | 30.3 % | 0.1 % | +16.0 | fail | W-B1 partly, W-B3 partly | W2-B1, W2-B3 |
| holly_b | 82 x 81, 1.09 | 0.75 (33.0 / 47.2) | 5.8 % | 31.0 % | 0.0 % | +15.7 | fail | W-B1 partly, W-B3 partly | W2-B1, W2-B3 |
| standing_stone | 30 x 89, 1.20 | 0.72 (24.2 / 44.2) | 1.1 % | 18.9 % | 0.0 % | +40.6 | fail | **W-S1 fixed**, W-S2 partly | W2-S1, W2-S2 |
| standing_stone_b | 37 x 67, 0.91 | 0.83 (26.0 / 50.7) | 0.8 % | 26.1 % | 0.0 % | +44.2 | fail | **W-S1 fixed**, W-S2 partly, W-S3 partly | W2-S1, W2-S2, W2-S3 |
| standing_stone_broken | 35 x 56, 0.76 | 0.88 prop (30.0 / 44.5) | 0.7 % | 28.1 % | 0.0 % | +45.3 | fail | **W-S1 fixed**, W-S2 partly, W-S5 partly | W2-S1, W2-S2, W2-S5 |
| standing_stone_lean | 36 x 73, 0.99 | **0.94** (25.3 / 60.3) | 1.5 % | 19.4 % | 0.0 % | +49.8 | **pass** | **W-S1 fixed**, W-S2 partly (polish) | W2-S2 (polish) |
| standing_stone_low | 59 x 56, 0.76 | 0.75 (19.6 / 49.8) | 0.6 % | 19.8 % | 0.0 % | +46.9 | fail | **W-S1 fixed**, W-S2 partly | W2-S1, W2-S2 |
| standing_stone_runes | 33 x 64, 0.86 | **0.98** (26.3 / 50.3) | 0.9 % | 27.7 % | 0.0 % | +41.4 | fail | **W-S1 fixed**, W-S2 partly, **W-S3 not fixed** | W2-S2, W2-S3 |
| lintel | 78 x 26, 0.35 | 0.87 prop (24.3 / 44.0) | 0.8 % | 24.6 % | 0.0 % | +12.2 | fail | W-S4 partly | W2-S4 |
| stone_top | 36 x 20, 0.27 | 0.77 prop (30.0 / 39.0) | 1.3 % | 26.8 % | 0.0 % | +10.6 | fail | W-S4 partly | W2-S4 |
| hatch_closed | 43 x 40, 0.54 | 0.89 prop (24.0 / 51.0) | 1.4 % | 44.5 % | 12.7 % | +8.8 | fail | W-H1 partly | W2-H1 |
| hatch_open | 43 x 64, 0.86 | 0.77 prop (23.8 / 38.8) | 0.9 % | 45.4 % | 34.8 % | +8.2 | fail | W-H1 partly, W-H2 partly | W2-H1, W2-H2 |
| ground | 960 x 1728 | n/a | | | | | **pass** | (cast shadows only) | W2-L1 (scene, not ground) |

**Checking the painter's numbers.**
- **Confirmed.**
  - Tree bars 0.735 to 0.839.
  - Holly lone texels 5.9 and 5.8 %.
  - Pine cluster noise 38.7 %.
  - Hatch cluster noise 44.5 and 45.4 %.
  - Hollow tree 212 px against the veteran class 222 to 340.
- **Oak and beech tones.** These are 24.3 and 23.1 tones a patch: 0.88 and 0.83 of the band, so the beech is also under the 0.85 tones floor for ramp-built art.
- **Shrub bars.** The foliage bars of 0.71 to 0.84 hold for the shrubs.

### Status of the round 1 codes

| Code | Status | Evidence |
| --- | --- | --- |
| W-T1 / W-B1 (crowns) | **partly** | Stamping is gone: repeated 3 x 3 windows are 0.4 to 3.5 %, against 32 to 40 %. The deep band no longer carries the tick, and the silhouettes are broken by leaf tips. Shrubs have leaf-shaped dark pockets. But no crown reaches 0.9 on shapes (0.71 to 0.84), and the crown structure is now W2-F1 to F3. |
| W-T2 (oak trunk) | **partly** | Taper 34 to 25 px over 84 rows, 2 roots flaring to 55 px, lit west (trunk L by fifths 95, 90, 75, 58, 47), crown shade on the trunk top: fixed. The bark is W2-T2. |
| W-T3 (beech trunk) | **partly** | The rings and the telescoping step are gone, and the foot flares from 17 to 41 px. The trunk is still flat and has no eye scars (W2-T3). |
| W-T4 (birch) | **partly** | A dark base, varied lenticels, a 13 to 8 px taper. No flare, a sock-like base, and an oak-dense crown (W2-T4). |
| W-T5 (pine) | **partly** | Needle tips and dark tier undersides: fixed. Regular tiers, a straight cone and leg roots (W2-T5). |
| W-T6 (hollow tree) | **partly** | The bole is squat (0.7 H bare, 52 to 88 px wide) with roots: fixed. The hollow still reads as a ring sticker (W2-T6). |
| W-T7 (willow, blocker) | **fixed** | A weeping dome 1.29 times as wide as tall, wider below, no straight sides. Swags taper and vary in length. A short leaning trunk forks into limbs, with the dark interior between swags. Outline closed (ring L 31.7 against 116.3 inside). |
| W-T8 (sapling stem) | **fixed** | The stem tapers 5 to 3 px with a side twig and a small root flare with a contact line. |
| W-B2 (brambles) | **partly** | Drupelet clusters in mixed ripeness, 6 distinct patterns: fixed. The canes are geometric (W2-B2). |
| W-B3 (holly) | **partly** | The leaves are darker and cooler, and holly_b has a conical habit. The spines, berries and base are W2-B3. |
| W-S1 (stone speckle) | **fixed** | Lone texels 0.6 to 1.5 % (from 9.2 to 11.7 %), with three planes on every stone (west minus east +40.6 to +49.8 L). |
| W-S2 (lichen, moss, skirt) | **partly** | The baked skirt is gone and every stone ends in a contact line: fixed. Lichen and moss are still stamps (W2-S2). |
| W-S3 (glyphs) | **partly** on _b, **not fixed** on _runes | The spiral is on the stone ramp but uncut. The runes read as cracks (W2-S3). |
| W-S4 (lintel, stone top) | **partly** | Speckle gone and mortise recesses added. A box silhouette and no chips (W2-S4). |
| W-S5 (broken stone) | **partly** | A slanted broken top, but no lit fracture plane. The `logic.scale` rejection stands. |
| W-H1 (hatch frame) | **partly** | The copings are lit from the upper left (north 146, west 126, south 111, east 98 L). The planks are grained, and cluster noise is 44.5 % against 60.6 %. Straps, ring, apron and contact are W2-H1. |
| W-H2 (open hatch) | **partly** | The lid is hinged on the north coping on iron leaves, and the blue squares are gone. The lid's thickness and shadow and the steps are W2-H2. |

### Findings and fixes (round 2)

#### Foliage painter (`woodtrees.py`: crown_masses, willow2, shrub)

**W2-F1. Crowns are cut into masses by drawn seam bands (fault; oak, beech, birch, hollow tree, willow cap, sapling).** Crop: `oak_crown.png` (oak 40,20,90,90 and beech 40,40,90,90 at 5x beside the red tree in 12).
- **What is wrong.** Between masses runs a band of one or two dark greens (L 40 to 60), 4 to 11 px thick and 30 to 150 px long. A row profile down x = 70 on the oak crosses lit body (L 160 or more), then a 4-row band at L 40 to 60, then the next mass's lit top. Down x = 90 on the beech the band is 11 rows.
- **Why it matters.** The masses read as separate lobes outlined by a groove (cauliflower, brain). Eastward's red tree has no continuous seam. Its masses overlap: the front mass's lower rim is a row of scalloped leaf clusters with small dark pockets of 2 to 6 texels under some of them, and the mass behind shows its lit clump tops up to that rim.
- **Fix.**
  1. Delete the seam band (`under_gap` as a drawn band).
  2. Where mass A overlaps mass B, draw A's lower edge as leaf scallops 4 to 8 texels wide with lit tips pointing down (leaf 3 to 4).
  3. Under every second or third scallop, put a pocket of leaf 0 to 1, 2 to 4 texels deep. No pocket may join the next one into a line longer than about 10 texels.
  4. Let B's lit clump caps (leaf 4 to 5) run up to the scallops.
  5. Check: no dark component inside the crown, eroded by 3, longer than 16 px.

**W2-F2. Inside each mass the texture is mottle, not leaf clumps (fault; every tree, softer on the shrubs).**
- **What is wrong.** At 5x the masses are an even field of 1 to 2 texel flecks in 2 or 3 close tones. In the red tree (12) every 6 to 10 texels there is a readable leaf cluster: a lit cap, a body and a dark U-shaped underside in 3 or 4 tones, overlapping like scales. That is where its 63 shapes a patch come from. Ours: 46.5 to 53.1.
- **Fix.**
  1. Build each mass from leaf clumps 5 to 9 texels across. Each clump has:
     - a lit crescent of 2 to 3 texels at its upper left (leaf 4 to 5);
     - a body at leaf 3;
     - a 1 to 2 texel dark U under it (leaf 1 to 2).
  2. Overlap the clumps by a third, offset like scales, with sizes and orientations drawn at random.
  3. Remove the single-texel mottle inside clumps: every same-tone patch at least 2 texels.
  4. The deep band stays quiet: clumps there in leaf 0 to 2 only, no caps.
  5. Target: bar at least 0.9 on shapes (57 a patch), lone texels 3 % or less, cluster noise 32 % or less. Raise shapes with more clumps, never with grain.

**W2-F3. Sky gaps are cut-out holes (fault; oak, beech, birch, sapling).**
- **What is wrong.** Each tree has 1 to 3 fully enclosed transparent holes (oak 21 x 18 and 11 x 13 px; beech 12 x 19 and 12 x 16; birch 8 x 21 and 11 x 17). Each is ringed by a 1 px dark outline (rim L 49 to 99), with a limb stick standing inside. They read as holes punched in a sticker.
- **Fix.**
  - **Where gaps open.** Open gaps only where a limb leaves the crown's under-band or at the crown's edge, so the gap is open to the outside, or drop the enclosed holes.
  - **The gap's rim.** Edge every gap with the masses' own dark undersides (leaf 1) and with leaf tips hanging into it, never with an outline.
  - **The limb.** The limb in it is lit on its west, darker where the crown shades it, and enters a mass at both ends.

**W2-F4. Detail bar (fault).** Shapes are 0.71 to 0.84 of the foliage band on every tree and shrub, and beech tones are 0.83 (house floor 0.85). W2-F1 and F2 are the way to reach the bar.

#### Trunks

**W2-T2. Oak bark is a uniform crack mesh (fault; oak, also on the willow, hollow tree and pine).**
- **What is wrong.** The bark is polygons 4 to 8 px across, each ringed on every side in near-black (timber 0). The polygons are equally dense on the lit and shaded sides, and are no taller than they are wide (horizontal runs 1.6, vertical 3.7 texels). It reads as crocodile skin.
- **Fix.**
  1. **Plates.** Vertical plates 3 to 5 px wide and 6 to 12 tall, in 2 to 3 sibling tones.
  2. **Cracks.**
     - Draw cracks only between plate columns and at about one plate end in three.
     - On the lit west third, draw the cracks in timber 1, not 0.
     - On the east third, merge the plates into a dark field with a few cracks.
  3. **Lit edges.** A lit west edge (timber 4) on a plate one in three.

**W2-T3. The beech trunk is a flat grey column (fault).**
- **What is wrong.**
  - **Flat.** In the lower trunk (80,190 to 130,250) the largest single-colour region is 337 px, and same-colour vertical runs average 7.5 texels. Its five-band cylinder ramp is drawn as straight vertical stripes.
  - **No scars.** It has no eye scars.
  - **Roots.** The roots are four thin symmetric claws.
- **Fix.**
  - **Mottle.** Keep the cylinder ramp, but break each band with sibling mottle patches of 3 to 6 texels in warm and cool greys. Add green algae (moss 1 to 2) on the east and north side.
  - **Eye scars.** Draw 2 or 3 eye scars, each 3 x 2: a dark lens with a lit lower lip.
  - **Roots.** Turn the claws into 2 or 3 broad buttress fins that merge into the trunk over 10 to 14 rows. Make them asymmetric, each lit on its west face.

**W2-T4. The birch's foot and crown (fault).**
- **What is wrong.**
  - **Base.** The dark base is a rectangle with a straight top edge (a sock).
  - **Flare.** The foot has no flare: 13 px at the foot, 12 to 13 px above.
  - **Width step.** The trunk steps a texel in width at mid-height.
  - **Crown.** The crown is the oak's dense mass with three 1 to 2 texel drips.
- **Fix.**
  - **Base.** Break the base's top edge into fissures that rise 4 to 10 px unevenly into the white.
  - **Flare.** Flare the foot 4 to 6 px.
  - **Taper.** Taper the trunk smoothly.
  - **Crown.** Draw the crown as 4 or 5 smaller masses with open gaps at the edge (W2-F3). Give the lower edge a fringe of hanging twig clusters, 3 to 8 px long in leaf 2 to 3.

**W2-T5. The pine is a stamped cone (fault).**
- **What is wrong.**
  - **Tiers.** 13 tier lines at 13.7 ± 0.7 px spacing (cv 0.05).
  - **Silhouette.** The west and east silhouettes stay within an RMS of 3.7 and 3.1 px of a straight line: a perfect cone (art-faults 3).
  - **Trunk.** The trunk is a saturated orange and splits into two leg-like roots, which read as a wishbone on stilts in the zone at 3x.
- **Fix.**
  - **Tiers.** Vary the tier spacing over 8 to 20 px. Let 3 or 4 tiers overlap, or break into two clumps.
  - **Silhouette.** Push 2 to 4 branch clumps 6 to 12 px out past the cone line, and cut 1 or 2 notches.
  - **Top.** Tilt the top a few texels.
  - **Roots.** 2 or 3 short flares of 4 to 8 px that stay under the trunk, not legs.
  - **Bark.** Move the bark to the oak's darker, less saturated ramp, with plates as in W2-T2.

**W2-T6. The hollow tree's hollow and crown centre (fault).**
- **What is wrong.**
  - **Hollow.** The hollow is an ellipse with a tan rim lit evenly all round, over a flat near-black disc holding two eye texels. There is no inner wall, so it still reads as a ring sticker.
  - **Crown centre.** A smooth flat olive patch sits at the crown's centre (about 95 to 175, 70 to 110).
  - **Scale.** `logic.scale`: 212 px tall against the veteran class 222 to 340.
- **Fix.**
  - **Lip.** Light the lip only on its lower and west edges (timber 4). Make the upper and east lip dark (timber 1).
  - **Inner wall.** Inside the top of the opening, draw the far inner wall as a band 2 to 3 px deep at timber 2 to 3, falling to near-black at the back. Keep the eyes inside the dark.
  - **Crown centre.** Fill the olive patch with clumps (W2-F2).
  - **Height.** Raise the crown by about 10 to 14 px so the tree reaches 222, and keep the bole.

**W2-T7. Willow detail (fault).**
- **What is wrong.**
  - **Swags.** The swags are stacks of 1-texel vertical dashes.
  - **Limbs.** The limbs stop in flat cut tops under the swags.
  - **Cap.** The cap carries W2-F1 seam bands.
- **Fix.**
  - **Swags.** Draw each swag as overlapping hanging leaf clumps, 3 to 5 texels wide and 4 to 7 long. Light each on its west, with a dark east edge and leaf tips on its outline (not dashes).
  - **Limbs.** Carry the limbs up into the cap so they vanish behind clumps, not at a cut line.
  - **Cap.** As W2-F1.

#### Shrubs

**W2-B1. Shrub detail bar (fault; bushes, brambles, holly).**
- **What is wrong.**
  - **Bar.** Shapes are 45.0 to 53.1 against 63.32 (0.71 to 0.84). bush_b is closest.
  - **Clump insides.** The clumps read now, but their insides are mottled as in W2-F2.
  - **bush_c.** bush_c has a dark band 99 px long along its lower third.
- **Fix.** As W2-F2, at shrub scale: clumps 4 to 7 texels. On bush_c, break the lower band into pockets.

**W2-B2. Bramble canes are geometric (fault).**
- **What is wrong.**
  - **Arcs.** The canes are concentric circular arcs 2 texels wide in one flat magenta tone. They have no lit edge, no thorns and no leaves.
  - **Over the mass.** They lie over the top of the mass like a handle. bramble_b's two parallel arcs read as a rainbow.
  - **Notch.** The silhouette has a notch at the centre of its base.
  - **Light.** West minus east is only +10.6 to +14.5 L.
- **Fix.**
  - **Canes.** Draw 3 to 5 canes of uneven curvature that leave the mass at different heights and droop back to the ground. Each is 2 texels wide in the berry or earth ramp, with a lit top texel, dark under, and 1-texel thorn hooks every 4 to 6 texels. Pass 1 or 2 of them behind leaf clumps.
  - **Mass.** Fill the base notch. Strengthen the upper-left light on the mass.

**W2-B3. Holly spines, berries and base (fault).**
- **What is wrong.**
  - **Spines.** They are single texels that touch the mass only at a corner (18 on holly, 31 on holly_b): fuzz, not leaf points.
  - **Berries.** The berries are 5 to 6 clusters drawn from 3 identical 3-berry stamps.
  - **Base.** The base is a straight dark plinth wider than the foot.
  - **Leaves.** The leaves have no glossy glint.
  - **Lone texels.** 5.9 %.
- **Fix.**
  - **Leaf points.** Draw each spine as a 2-texel point grown from a leaf's edge (edge-joined), every 3 to 5 texels along the silhouette.
  - **Leaves.** Give 1 leaf in 4 a hard 1-texel glint at tone 5 on its upper-left lobe.
  - **Berries.** Vary the clusters (3 to 5 berries, different arrangements, each with a glint), set at leaf axils.
  - **Base.** End the base in the mass's own dark underside with a contact line, no plinth.
  - **Lone texels.** Under 3 %.

#### Stone painter (`woodstones.py`)

**W2-S1. The stone bar (fault; standing_stone, _b, _broken, _low, stone_top, lintel).**
- **What is wrong.** Bars are 0.72 to 0.88.
  - **Tones.** _low has 19.6 tones against 26.25: its face is held to three greys.
  - **Shapes.** The rest are short on shapes. The face texture is an even field of 2 to 5 texel blocks of similar size on every plane.
- **Fix.**
  - **Planes.** Vary the texture by plane: larger calm patches (5 to 10 texels) on the lit crown, and smaller ones on the shaded flank.
  - **Story details.** Add the details below, which raise shapes the way Eastward's rocks do:
    - 2 or 3 chips per stone at the arrises (W2-S2);
    - a crack with its lit lower lip;
    - lichen crusts;
    - a damp band at the foot (stone 1 to 2 with moss in the joints).
  - **_low tones.** Give _low a warm and a cool sibling plane.

**W2-S2. Lichen, moss and rim marks (polish on _lean, part of the fail elsewhere).**
- **What is wrong.**
  - **Lichen.** Tan dots of 2 to 3 texels, the same size on every stone.
  - **Moss.** The moss is a flat two-tone parallelogram at the south-east foot of 5 of the 6 standing stones, in the same place each time.
  - **Rim dashes.** Dark 1 x 2 dashes on the lit west rim read as stray marks.
- **Fix.**
  - **Lichen.** Grow irregular crusts 3 to 10 texels across in 2 or 3 sibling tones.
  - **Moss.** As a 2-texel cap over a 4-texel band in moss 1 to 3, placed differently on each stone, with one in three in a crack.
  - **Chips.** Turn the rim dashes into chips: a notch in the lit rim with a shade texel under it.

**W2-S3. Carving (fault; standing_stone_b, standing_stone_runes).**
- **What is wrong.**
  - **Spiral.** The spiral is a one-tone dark 2 px line. Without a lit lip it reads as painted on.
  - **Runes.** The runes are two vertical strokes and a diagonal in the same vocabulary as the cracks on the other five stones, so the runestone does not read as carved.
- **Fix.** Cut both as grooves:
  - **Groove.** Each stroke 2 texels wide, stone 1 on its upper edge and stone 4 on its lower lip, worn through in 1 or 2 places.
  - **Runes.** Make them branching angular strokes (3 to 5 glyphs, 5 to 8 px tall), clearly unlike the cracks.

**W2-S4. Lintel and stone top are boxes (fault).**
- **What is wrong.**
  - **Silhouette.** A perfect rectangle with right-angle corners.
  - **Arris.** A straight stone-5 line runs the full length of the arris.
  - **Outline.** The near-black outline is closed on the lit top as well.
  - **Moss.** On the lintel, four identical moss dashes sit evenly spaced along the front foot.
- **Fix.**
  - **Corners.** Round and chip the corners: 2 to 4 chips per arris, each a notch with a shade texel.
  - **Arris.** Break the lit arris line where the chips fall, and let the lit top edge show (no outline there).
  - **Sag.** Sag the top line by a texel over its length.
  - **Moss.** Place moss unevenly: 1 or 2 clumps, with drips into a joint.

**W2-S5. The broken stone's fracture (fault).** Draw the broken top as its own plane: lit (stone 4 to 5) with 1 to 2 texel steps along the break, its far edge dark, and the stone's own crown never continuing over it.

#### Hatches (`hatch.py`)

**W2-H1. Hatch hardware, apron and contact (fault; both).**
- **What is wrong.**
  - **Straps.** The straps are flat two-tone bars with no nail heads.
  - **Ring.** The ring is a 3 x 3 grey smudge.
  - **Apron.** The apron is a 1 px tan line with an even comb of 1 x 2 tufts along all four sides.
  - **Contact.** The frame sits on the turf with no contact shade, and looks pasted at 4x in the zone.
- **Fix.**
  - **Straps.** A lit top row, a dark bottom row, and nail heads at each board (a dark texel with a lit texel above).
  - **Ring.** A ring with a lit upper-left arc and a shade on the boards under it.
  - **Edge.** Replace the line and the comb with the turf's frayed edge to worn earth (eastward-edges 5.1): 2 to 3 px of bites and 2 to 4 tufts of different sizes.
  - **Contact.** A one-tone contact shade along the south and east of the frame.

**W2-H2. The open hatch's lid and steps (fault).**
- **What is wrong.**
  - **Lid.** The lid shows no edge thickness and casts no shadow. A 2 px green strip runs down its east side.
  - **Steps.** The steps are flat two-tone bars with straight square ends: 34.8 % of the varied 3 x 3 windows repeat, and the bar is 0.77.
- **Fix.**
  - **Lid.** Show the lid's top edge as 2 rows of end grain (lit top). Cast its shadow two tones down onto the coping and turf to the east, and remove the green strip.
  - **Steps.** Each step needs:
    - a worn nosing with 1 or 2 chips;
    - grit at the back of each tread;
    - riser joints;
    - ends that meet the shaft wall with a shade texel.
  - **Light.** Keep the falloff to near-black at the back.

#### Scene (for the logic-auditor and Claude A)

**W2-L1. woodland_base.tscn places the pass-2 pictures at the pass-1 offsets (fault).** Commit 7afbe76a says the scene write was refused by the placement gate, so the node offsets are stale. Here is where each picture's opaque foot falls against its node position (the plan foot):

| Picture | Opaque foot against the plan foot | What it does in the scene |
| --- | --- | --- |
| willow | 85 px north | Offset (-96,-287) for a 202 px picture. Its trunk stands on the cobble path, and its ground shadow lies orphaned south of the path. |
| hollow tree | 22 px north | |
| beech | 22 px south | |
| oak | 14 px south | |
| birch | 12 px south | |
| pine | within 2.5 px | |

Fix: regenerate the scene from the plan (`gen_zone`) once the gate allows it, and then re-run the scene gate. At its plan foot (780, 1344) the willow stands on the lawn south of the path, which also clears round 1's logic note (trunk on the path).

**W2-L2. The scene gate refuses woodland at this head** (`stale bake: scene/plan material differs at 20,35` for `woodland_kit`). #446 changes `game/kit/zones/woodland_kit.json`'s rows without that scene. Re-export the kit zone's scene, or confirm that main refuses the same way.

### False positives

5 rejected:

- **`detail.light` on the oak** (88,161,118,247): this is the east root and fork, with lit tops facing west. By fifths west to east the trunk measures L 95, 90, 75, 58 and 47.
- **`detail.light` on the willow** (139,105,163,138): this is the fork's east limb, lit on its own west face. By fifths the box measures 84, 83, 89 and 78.
- **`detail.light` on hatch_closed** (whole box): the planks measure L 110, 106 and 100 west to east, and the copings are lit from the upper left.
- **`logic.scale` on `standing_stone_broken` and `standing_stone_low`**: short by design, as in W-S5.

`logic.scale` on `standing_stone` (30 px wide against 33) is accepted as polish, since it is a slim menhir. The hollow tree's `logic.scale` stands (W2-T6).

### Not checked

- **No in-game render.** The zone was composed from the scene data. The scene gate itself refuses (W2-L2), so its grid cells were not visited. Day and night, the night tint and a phone were not checked.
- **Hatch states.** The hatches were pasted, not seen in their live state switch.
- **Kit pieces and props.** The kit pieces and props regenerated by #446 (`game/kit/props/*`, the kit grounds and `kitlab`) were not reviewed. Only the zone pictures above were.
- **No fixes.** Nothing was repainted.

## Round 3: pass 3 of the redraw (9 Nov 2026)

The asset gate on draft PR #446 (`claude-a/woodland-redraw`, head **76fc00d6**, "Woodland, pass 3"), which repaints the 23 assets that failed round 2 and changes `woodland/ground` again through the trees' and shrubs' cast shadows. `standing_stone_lean` is byte-identical to round 2 (sha256 1ecd239b). Reviewed by a detail-auditor that drew none of it.

**Result: 5 of 25 pass (`standing_stone`, `standing_stone_b`, `standing_stone_broken`, `standing_stone_lean`, `standing_stone_runes`). 20 fail, none on a blocker.** The seam bands are gone (W2-F1 fixed on every crown), the trunks are good (W2-T2 and W2-T3 fixed), and the stone painter now reaches the bar on five stones with cut carving and a real fracture plane. What still fails is the foliage painter's fill: the crowns read as soft horizontal speckle, not as distinct leaf clumps, and their darkest marks are near-black blobs standing in mid and lit leaf, not shade. Two trees (oak 0.903, birch 0.902) and the hollow tree (0.884 tones, 0.901 shapes) now meet the detail bar, so the bar alone no longer catches this; the measures below do. `woodland/ground` fails on a new fault in the shrubs' shadows (W3-G1), and its round 2 pass had been carried onto bytes it never covered (W3-P1).

### What was reviewed and how

- **Calibration first.** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <refs-games/eastward>`: recall **39 of 39**; false positives 5 on 6 clean screens and 21 on 22 clean props, as in rounds 1 and 2. `calibration_results.json` was reverted afterwards.
- **Asset gate.** `npm run review:asset -- woodland/<name>` for all 25, then `--record` (no record changed: every sha256 already matched). Detector result: **25 pass**, no blocker or fault findings. Polish: `detail.bar` on 15 (every foliage asset except the oak and birch, plus `standing_stone_low`, `lintel` and both hatches), `logic.scale` on `standing_stone`, `_broken`, `_low`, `bush_c` and `bramble`, `detail.light` on the birch, `detail.cluster_noise` and `detail.outline` on both hatches.
- **Scene gate.** `npm run review:scene -- woodland --no-render` now **reaches its report** (the painter's claim holds): 88 blockers, all `logic.wiring` on quests whose talk, camp and enter events live in zones not yet built; 14 faults (6 `logic.occlusion`, the willow's +85 px y-sort among them, W2-L1; 3 `detail.flat`; 2 `logic.reach`; 2 `logic.shadow_orphan`; 1 `detail.repetition` of ground tufts); 20 `logic.scale` polish. The scene's grid cells were not visited one by one (this is an asset gate). From the composite I cropped the stone circle with its brambles at 2x and the bramble shadows at 4x.
- **Enlarged.** Every asset at 3x to 5x; crowns, the willow's curtain, the hollow, the beech and oak trunks, the pine's foot, the carving, the fracture, the lintel, the stone top and the hatches at 5x to 10x, with L dumps of the hollow, the spiral, the runes, the hatch straps and the lintel's edges.
- **Measurements.** Round 1's `metrics.py` (lone texels, the largest one-colour region, west minus east L, repeated 3x3 windows), round 2's `seams.py`, `cluster_noise.share_png`, and new this round (scripts in the auditor's scratchpad, not committed):
  - **runs**: mean run of one level (L in 12 levels over the crown's p2 to p98) along rows (H) and columns (V); a fill of 1-row dashes has H/V well over 1.3;
  - **clump contrast**: the p90 minus p10 of L after a 3x3 box blur, in 12 x 12 windows fully inside the crown (clusters of 3 or more texels survive the blur, single-texel speckle does not);
  - **near-black pockets**: components of texels at L 50 or under inside the crown, their size, and whether their 2-texel ring is darker than the crown's 30th percentile (in shade) or not;
  - the willow's swags (count, width and outlined share of their side edges in the lower curtain), circle fits to the bramble canes, one-texel spurs on silhouettes, lone bright glints, straight runs of stone and shrub edges, the stones' same-colour patch sizes by third, and one-row ruler lines in the ground.
- **Eastward at the same character height** (x1.37, nearest neighbour), the boxes of rounds 1 and 2: the red tree in 12 (465,110,590,230), the trees in 13, the pines in 12 (175,65,245,165), the rocks in 17 (460,165,550,250) and 12 (497,205,555,235), the post box in 12. A 64 x 64 window of the oak's and the beech's crowns was set at 6x beside the same window of the red tree (`crown_cmp6x.png`), and 120 x 110 windows of the oak at 5x (`oak_tl.png`, `oak_low.png`). I also read the coordinator's sheets `wr3/sheets/ew_cmp_trees.png`, `ew_cmp_shrubs_stones.png` and the `contact_*_4x.png` sheets.

### Verdicts

Bar is `detail.bar` (house-style 7: 0.9, or 0.85 on tones for ramp-built art; group in brackets where it is not the asset's kind). Contrast is clump contrast in L (Eastward's crowns 41 to 49). H/V is the run ratio (Eastward 1.08 to 1.30). Pockets is near-black pockets not in shade, of all (Eastward's red tree: 20 of 79, median size 1 texel; ours median 4 to 6).

| Asset | Opaque (art px, H) | Bar (tones / shapes) | Lone | Noise | Contrast | H/V | Pockets | Verdict | Codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oak | 194 x 249, 3.36 | **0.903** (25.2 / 57.1) | 0.4 % | 21.8 % | 26.5 | 1.57 | 9 of 21 | fail | W3-F1, F2, F3 |
| beech | 175 x 265, 3.58 | 0.864 (24.0 / 55.5) | 0.3 % | 16.8 % | 21.8 | 1.48 | 23 of 44 | fail | W3-F1, F2, F4, T5 |
| birch | 91 x 204, 2.76 | **0.902** (27.4 / 57.1) | 1.7 % | 23.5 % | 31.9 | 1.49 | 5 of 10 | fail | W3-F1, F2, T4 |
| pine | 98 x 237, 3.20 | 0.739 (30.8 / 46.8) | 0.3 % | 30.5 % | 47.4 | 1.30 | (tiers) | fail | W3-F4, T1 |
| hollow_tree | 215 x 231, 3.12 | 0.884 (24.5 / 57.0), meets | 0.5 % | 20.2 % | 23.2 | 1.57 | 17 of 35 | fail | W3-F1, F2, T2 |
| willow | 255 x 202, 2.73 | 0.835 (26.3 / 52.9) | 0.4 % | 19.2 % | 28.8 | 0.75 | 3 of 33 | fail | W3-F1, F4, T3 |
| sapling | 55 x 84, 1.14 | 0.813 (26.5 / 51.5) | 0.9 % | 18.6 % | 33.9 | 1.46 | 2 of 4 | fail | W3-F1, F4, T6 |
| bush | 98 x 64, 0.86 | 0.858 (31.4 / 54.3) | 0.5 % | 22.9 % | 32.1 | 1.41 | 7 of 15 | fail | W3-F1, F2, B1 |
| bush_b | 79 x 55, 0.74 | 0.858 (32.0 / 54.3) | 0.7 % | 22.9 % | 35.0 | 1.31 | 1 of 4 | fail | W3-F1, F3, B1 |
| bush_c | 116 x 59, 0.80 | 0.842 (29.2 / 53.3) | 0.8 % | 22.0 % | 32.8 | 1.41 | 6 of 11 | fail | W3-F1, F2, B1 |
| bramble | 122 x 50, 0.68 | 0.79 (34.0 / 50.0) | 3.7 % | 30.6 % | 36.5 | 1.43 | 16 of 29 | fail | W3-F1, F2, F3, B1, B2 |
| bramble_b | 106 x 49, 0.66 | 0.711 (34.7 / 45.0) | 2.5 % | 27.6 % | 35.7 | 1.35 | 9 of 24 | fail | W3-F1, F3, B1, B2 |
| holly | 85 x 74, 1.00 | 0.83 (30.6 / 52.5) | 2.7 % | 27.3 % | 32.9 | 1.32 | 17 of 35 | fail | W3-F1, F2, B1, B3 |
| holly_b | 79 x 79, 1.07 | 0.804 (28.5 / 50.9) | 3.1 % | 25.6 % | 31.0 | 1.45 | 16 of 40 | fail | W3-F1, F2, B1, B3 |
| standing_stone | 30 x 89, 1.20 | **0.934** (30.2 / 57.0) | 1.3 % | 19.1 % | | | | **pass** | W3-S4 (polish) |
| standing_stone_b | 37 x 67, 0.91 | **0.967** (32.7 / 59.0) | 0.8 % | 28.7 % | | | | **pass** | W3-S4 (polish) |
| standing_stone_broken | 35 x 56, 0.76 | **0.963** prop (33.5 / 48.5) | 0.7 % | 31.3 % | | | | **pass** | W3-S4 (polish) |
| standing_stone_lean | 36 x 73, 0.99 | **0.938** prop (25.3 / 60.3) | 1.5 % | 19.4 % | | | | **pass** (unchanged) | W2-S2 (polish) |
| standing_stone_low | 59 x 56, 0.76 | 0.875 (27.0 / 53.4) | 0.9 % | 22.1 % | | | | fail | W3-S1 |
| standing_stone_runes | 33 x 64, 0.86 | **1.271** prop (36.3 / 64.0) | 1.2 % | 29.7 % | | | | **pass** | W3-S4 (polish) |
| lintel | 78 x 27, 0.36 | 0.841 prop (26.3 / 42.3) | 0.3 % | 26.2 % | | | | fail | W3-S2 |
| stone_top | 36 x 21, 0.28 | **0.913** prop (32.0 / 46.0) | 2.1 % | 23.2 % | | | | fail | W3-S3 |
| hatch_closed | 45 x 41, 0.55 | 0.889 prop (24.0 / 51.0), meets | 1.0 % | 44.7 % | | | | fail | W3-H1 |
| hatch_open | 45 x 65, 0.88 | 0.898 prop (24.8 / 45.2) | 0.6 % | 45.2 % | | | | fail | W3-H2 |
| ground | 960 x 1728 | n/a | | | | | | fail | W3-G1, W3-P1 |

**Checking the painter's numbers.** All confirmed: oak 0.903, birch 0.902, standing_stone 0.934, _b 0.967, _broken 0.963, _runes 1.271, stone_top 0.913; the rest 0.711 to 0.898; lintel down from 0.87 to 0.841 and willow from 0.84 to 0.835; `standing_stone_lean` byte-identical; the hollow tree 231 px tall (its `logic.scale` no longer fires); holly_b lone 3.1 % and bramble 3.7 %; hatch cluster noise 44.7 and 45.2 %. Two things the bar does not show: three of the bar passes are on the prop band (the broken stone, the runestone, the stone top) rather than the stone band, which sets 61.0 shapes rather than 50.36; and the oak's and birch's bars pass while their crowns still miss the structure the bar was meant to stand for (W3-F1).

### Status of the round 2 codes

| Code | Status | Evidence |
| --- | --- | --- |
| W2-F1 (seam bands) | **fixed** | No band runs through any crown. The darkest 12 % of the oak's crown is now one connected field along its east and south rim (156 x 89 px, half-thickness up to 4.5 px), its form shadow, not a groove between masses; the beech, hollow, birch, sapling and willow cap likewise. |
| W2-F2 (mottle, not clumps) | **not fixed** | The mottle is now 1-row horizontal dashes: H/V 1.41 to 1.57 on the broadleaves (pass 2: 0.98; Eastward 1.08 to 1.30). Clump contrast fell on the big crowns (oak 31.2 to 26.5 L, beech 29.5 to 21.8, willow 37.3 to 28.8) against Eastward's 41 to 49. W3-F1, W3-F2. |
| W2-F3 (cut-out sky holes) | **fixed** on the oak, beech, birch; **not fixed** on the sapling | Enclosed holes are now pinholes of 1 to 4 texels on the oak and birch (polish). The sapling keeps a 19-texel enclosed hole (W3-T6). |
| W2-F4 (bar) | **partly** | Met by the oak (0.903), birch (0.902) and hollow tree (tones 0.884, shapes 0.901). Missed by the beech 0.864, willow 0.835, sapling 0.813, pine 0.739 and all six shrubs (0.711 to 0.858). |
| W2-T2 (oak bark) | **fixed** | Vertical plates 3 to 5 wide, cracks lighter on the lit west third, a dark east field with ridges. |
| W2-T3 (beech trunk) | **fixed** | Warm and cool grey mottle on the cylinder ramp, two 2 x 1 eye scars, a buttressed foot from 21 to 42 px. Polish: the algae is a saturated stripe of square blocks down the east outline (W3-T5). |
| W2-T4 (birch) | **partly** | Fissured base rising into the white, smooth taper 10 to 13 px: fixed. The flare is all in the last 4 rows (13 to 21 px), and the crown is still one dense mass (W3-T4). |
| W2-T5 (pine) | **partly** | Tiers vary, branch clumps stand past the cone, the top tilts, the bark is the oak's plates: fixed. A 28-texel clump floats detached at (101,160), and the foot is a symmetric skirt (W3-T1). |
| W2-T6 (hollow) | **partly** | 231 px tall, lip lit only low and west (L 132 to 139, upper lip 46 to 99), crown centre filled: fixed. The opening is still a flat one-tone disc (W3-T2). |
| W2-T7 (willow) | **partly** | Cap seams gone and limbs carried up behind the cap: fixed. Swags are still ropes (W3-T3). |
| W2-B1 (shrub bar) | **partly** | bush_c's lower band is broken into pockets (fixed); bars 0.711 to 0.858, none at 0.9 (W3-B1). |
| W2-B2 (bramble canes) | **partly** | Canes now have four tones, a lit top, thorn hooks, and reach the ground: fixed. They are still circular arcs, two concentric on each bramble, and the base notch was closed by a straight full-width base row (W3-B2). |
| W2-B3 (holly) | **partly** | No corner-only spines (0, from 18 and 31), varied berry clusters, no plinth: fixed. The leaves are not holly leaves, the spines are 1-texel spurs and the glints read as sprinkle (W3-B3). |
| W2-S1 (stone bar) | **fixed** on standing_stone, _b, _broken; **not fixed** on _low, lintel | 0.934, 0.967, 0.963 against 0.875 and 0.841. The texture is still an even field of patches (median 3 texels on the lit west third and the shaded east third alike), polish on the passing stones (W3-S4). |
| W2-S2 (lichen, moss, rim) | **partly** | Moss placed differently on each stone. Lichen is drawn as tan bars with a lit top row, and the moss is one tuft-with-drip motif on four stones (polish, W3-S4). |
| W2-S3 (carving) | **fixed** | Spiral and runes are grooves at L 67 with a lit lip at L 162 on a face of 136 to 143; the runes are branching glyphs unlike the cracks. |
| W2-S4 (lintel, stone top) | **partly** | The tops sag 1 to 3 texels and the lit top edge carries no outline: fixed. Both are still boxes with straight ends and an unchipped arris (W3-S2, W3-S3). |
| W2-S5 (fracture) | **fixed** | A lit fracture plane (stone 4 to 5) with 1 to 2 texel steps and a dark far edge. |
| W2-H1 (hatch hardware) | **partly** | Ring with a lit arc and shade, frayed worn-earth edge with tufts of several sizes, contact shade: fixed. The straps are still flat two-row bars without nails (W3-H1). |
| W2-H2 (open hatch) | **partly** | Green strip gone, lid end grain, step nosings and riser joints: fixed. No lid shadow and stamped tread grit (W3-H2). |
| W2-L1 (willow offset in woodland_base.tscn) | **not fixed** | As expected while the gate refuses the scene write: the scene gate still reports the willow's y-sort point +85 px off its feet. |
| W2-L2 (scene gate refused) | **fixed, with a caveat** | `review:scene -- woodland --no-render` reaches its report. The re-export of `woodland_kit.tscn` is not only renumbering (below). |

### The re-export of woodland_kit.tscn (W2-L2)

I normalised both files (every `ExtResource` and `SubResource` id replaced by its path or its order, `unique_id` dropped) and diffed round 2's scene (075a7705, identical to main's, 06d7a1d1) against pass 3's. Of the 708 changed lines, 90 still differ after normalising; the rest are renumbered resource ids and node `unique_id`s. The 90:

- **No tile or material change**: the `Cells` and `Tiers` data are identical, consistent with plan rows 47 to 51 being back to main's.
- **9 pieces move to the plan's feet**: the six circle stones 9 world px north (stone-1 336,1305 to 336,1296 and so on), lintel-1 and stone-top 6 px north, and the oak `wood-16` 48 px south (36,840 to 36,888). These are the positions #446's first commit (f2a9d16b) wrote into `game/kit/zones/woodland_kit.json` without exporting the scene, so the scene now matches the plan.
- **`boulder-33` is renamed `boulder-32`**, as in the plan.
- **Two new nodes** from the gameplay layer (`gameplay_from: woodland.tscn`): `Actors/HatchClosed` and `Actors/HatchOpen`, conditional sprites of `hatch_closed.png` and `hatch_open.png` at (336,1032), offset (-23,-58). `woodland_kit` now places both hatch pictures, so the gate covers them there too.
- **The `ToUndercroft` door moves** from (330,1030) to (336,1020), its rect from (13.125,42.42) to (13.375,42.0), as in woodland.tscn.

So the re-export is right in substance, it brings the scene in line with the plan and with woodland.tscn, but it moves placements, adds two placed pictures and moves a door. It is not the ID-only churn the summary describes. The generator's drift on rows 47 to 51 is left unresolved, as the painter says.

### Findings and fixes (round 3)

#### Foliage painter (`woodtrees.clump_crown`)

**W3-F1. The crowns are soft horizontal speckle, not leaf clumps (fault; every broadleaf, the sapling, the willow's cap, the six shrubs).** Crops: `crown_cmp6x.png` (oak 70,40 and beech 80,40, 64 x 64 at 6x, beside the red tree in 12), `oak_tl.png`, `oak_low.png`.
- **What is wrong.** At 5x and 6x every mass is filled with 1-row dashes 2 to 5 texels long in two or three close greens. Same-tone runs average 2.98 texels across and 1.90 down on the oak (H/V 1.57; beech 1.48, birch 1.49, hollow 1.57, shrubs 1.31 to 1.45; Eastward 1.08 to 1.30). Clump contrast is 21.8 to 35.0 L on the broadleaves and shrubs against 41.2 to 48.8 in Eastward's red tree, its tree in 13 and its pines. The oak's crown has *less* contrast than pass 2 (26.5 against 31.2 L). In the red tree each clump is a lit 4 to 8 texel shape with a mid-dark gap round it; ours have no gap, so the eye sees brushed felt. The pine is the exception: 47.4 L and H/V 1.30, which is why it reads.
- **Fix.**
  1. Paint each clump as one shape 5 to 9 texels across, in two tones at most inside it (cap leaf 4 to 5, body leaf 3), filled solid, never with dashes. Every same-tone patch at least 2 texels in both directions.
  2. Separate each clump from its neighbours with a gap of leaf 1 to 2, 1 to 2 texels wide, under and to the right of it, so cap to gap is at least 40 L.
  3. Draw the clumps as scales: rows offset by half a clump, sizes from 5 to 9 at random, orientations varied, not a stack of horizontal strokes.
  4. Check: clump contrast at least 40 L in 12 x 12 windows, H/V 1.3 or less, `detail.bar` at least 0.9 on shapes. Raise shapes with more distinct clumps, never with grain.

**W3-F2. The dark pockets are black pepper, not shade (fault; oak, beech, birch, hollow tree, bush, bush_c, brambles, holly).**
- **What is wrong.** Near-black (L 50 or under) appears as solid blobs of 4 to 13 texels (median 4 to 6) dropped into mid and lit leaf: 9 of 21 on the oak, 23 of 44 on the beech, 17 of 35 on the hollow tree, 7 of 15 on the bush, 17 of 35 on the holly have a ring lighter than the crown's 30th percentile. Eastward's red tree uses near-black as single texels (median 1) at the bottom of its mid-dark gaps: 59 of 79 sit in shade.
- **Fix.** Use leaf 0 only at the deepest point of a W3-F1 gap, 1 to 2 texels, always with leaf 1 to 2 round it; step a clump into its gap through leaf 3, 2, 1, 0, never 3 to 0. Check: at least 75 % of near-black components in shade, median 2 texels or less.

**W3-F3. Leaf tips are dark hairs (polish on the trees, fault on bush_b and the brambles).** The silhouette is broken by single near-black spikes 1 texel wide and 2 to 3 tall, not by leaves. Brambles carry 30 and 38 one-texel spurs (6.8 and 8.0 % of the silhouette ring); in the zone at 2x they read as a dotted contour floating round the brambles and bush_b (`zone_shadow.png`). Fix: break the silhouette with whole clumps (3 to 6 texels, lit tip, leaf 3 to 4) on the top and west, and with leaf 2 tips under; no spur in outline tone.

**W3-F4. Detail bar (fault).** Beech 0.864 (shapes 0.877), willow 0.835, sapling 0.813, pine 0.739 (46.8 shapes against 63.32). W3-F1's distinct clumps are the way there; on the pine, add 1 or 2 more branch clumps per tier.

#### Trees

**W3-T1. The pine's floating clump and foot (fault).** A 28-texel clump stands detached east of the cone at about (101,160), with transparency all round it (a second opaque component; `logic.floating_part` did not fire). The foot is a symmetric skirt, the same slope both sides. Fix: join the clump to its tier with a branch (2 texels, timber 1 to 2) or drop it; give the foot 2 or 3 uneven flares (W2-T5).

**W3-T2. The hollow is a flat disc (fault).** Crop: `hollow.png`. Inside the lip the opening is one tone (L 24) over about 200 texels (the asset's largest one-colour region, 219), with two eye texels; the far inner wall is only 1 to 2 rows (L 73, then 46) under a dark upper lip, so the ring still reads closed. Fix: the far inner wall 3 to 4 rows graded timber 3 to 2 to 1 under the upper lip; the floor of the hollow lit one tone just inside the lower west lip; the interior in 2 or 3 tones falling to near-black at the back; leave the eyes in the darkest part.

**W3-T3. The willow's swags are ropes (fault).** Crop: `willow_sw.png`. In the lower curtain (62 to 85 % of the height) a row crosses 9.1 swags, 6 to 13 texels wide (median 7), and 95 % of their side edges are near-black outline (L under 60). Inside, the texture runs in vertical streaks (H/V 0.75). Each swag is a closed tube, so the curtain reads as dreadlocks. Fix:
  1. Group the swags into 3 to 5 curtains, each 15 to 30 texels wide, of overlapping hanging clumps 4 to 7 wide and 4 to 7 long.
  2. Outline only each curtain's outer silhouette. Between swags inside a curtain, use shade (leaf 1 to 2), never outline.
  3. Break the outline with lit leaf tips pointing down, and end each swag in 2 or 3 tips of different lengths.
  4. Let the dark interior and the trunk show between curtains, not between every swag.

**W3-T4. The birch's flare (polish).** Spread the 13 to 21 px flare over the last 8 to 10 rows.

**W3-T5. The beech's algae (polish).** The algae is a saturated stripe of square 2 to 3 texel blocks down the east outline. Use moss 1 to 2 (desaturated), in irregular patches set in from the outline, and more on the north side under the crown.

**W3-T6. The sapling's sky hole (fault).** A 19-texel hole is enclosed in the crown. Open it to the crown's edge or close it (W2-F3).

#### Shrubs

**W3-B1. Shrub bar (fault).** bush 0.858, bush_b 0.858, bush_c 0.842, bramble 0.79, bramble_b 0.711, holly 0.83, holly_b 0.804. Fix through W3-F1 at shrub scale (clumps 4 to 7 texels).

**W3-B2. Bramble canes and base (fault).**
- **Canes.** Every cane fits a circle to within 0.9 to 1.2 px rms. On bramble the two east canes share a centre (96,45 and 102,41); on bramble_b the two west canes are concentric (R 25.5 and 15.1, centres 8 px apart), still a rainbow. Fix: draw each cane as a curve whose bend changes along it (a kink at a node every 6 to 10 texels, a droop at its tip), with no two canes from one centre and at least one crossing another.
- **Base.** The lowest opaque row is 121 of 122 texels (bramble) and 105 of 106 (bramble_b), running under the cane arches, so the sprite carries a straight ground line, and its shadow repeats it (W3-G1). Fix: end the mass in its own dark underside with an uneven contact of 1 to 2 texels, and nothing opaque under an arch except the cane's foot.

**W3-B3. Holly still does not read as holly (fault).** The leaves are the shared dash fill (W3-F1). The spines are 1-texel spurs (28 on holly, 19 on holly_b; 9.8 and 6.8 % of the silhouette ring), not 2-texel points. The 15 and 13 glints are lone single specks spread evenly (3.3 to 3.8 per 1000 texels), so they read as yellow sprinkle. Fix: draw the leaves as distinct spiky ovals 5 to 7 texels long (leaf cool 1 to 3) with a lit midrib; set each glint against that leaf's lit upper-left edge, 2 texels, one leaf in four; spines 2 texels, grown from the leaf edges on the silhouette.

#### Stones

**W3-S1. standing_stone_low is a tombstone (fault).** Bar 0.875 (shapes 53.4 of 61.0; tones 27.0, from 19.6, fixed). The sides are vertical (west 31, east 34 of 56 rows within 1 px) under chamfered top corners, and two of it stand in the circle. Fix: an irregular profile (one shoulder lower, a bulge or lean of 2 to 4 px on a side), 2 chips on the shoulders, larger calm patches on the lit crown.

**W3-S2. The lintel is still a box (fault).** Crop: `lintel8.png`. Bar 0.841 (42.3 shapes), down from 0.87. The bottom runs straight for 76 of 78 columns and the ends for 27 and 26 of 27 rows; the lit arris runs the full length with no chip; the two mortises are near-black cross shapes with no lit far wall, so they read as glyphs. Fix: as W2-S4 (2 to 4 chips on the front arris, each a notch with a shade texel; round the ends 2 to 3 texels; a lip of 1 texel up or down along the bottom), and each mortise a 4 x 3 rectangle: near wall dark (stone 0 to 1), floor stone 2, far (north) wall lit (stone 4) one row.

**W3-S3. The stone top is a box with a stray mark (fault).** Crop: `stonetop8.png`. Ends straight for 21 of 21 rows, the bottom straight, the front arris unchipped, and a saturated ochre L-shaped blob at the west end that reads as a stray mark. Fix: as W3-S2 for the chips and ends; take the ochre into the lichen tones.

**W3-S4. Stone texture and lichen (polish on the five passing stones).** The patch field is even: same-colour patches have a median of 3 texels on the lit west third and the shaded east third alike (W2-S1's texture by plane is not done). Lichen is tan bars with a lit top row, several solid rectangles per stone. Moss is one tuft-with-drip motif on standing_stone, _b, _broken and _runes. The spiral groove is one texel wide in places. Next pass: larger calm patches (5 to 10 texels) on the lit crown, lichen as lobed crusts, the moss motif varied.

#### Hatches

**W3-H1. Closed hatch straps (fault).** Crop: `hatch8.png`. Each strap is a row at L 113 over a row at L 67 across all three boards, with no nail heads (one dark texel on the lower strap). The inner south lip is a solid 30-texel row at L 193. Fix: nail heads at each board on both straps (a dark texel with a lit texel above, 6 in all); break the south lip into 2 or 3 tones with one chip.

**W3-H2. Open hatch lid shadow and tread grit (fault).** The lid casts no shadow on the coping or turf. The grit on the treads is a row of evenly spaced identical brown dashes (24.6 % of varied 3 x 3 windows repeat four or more times; round 2: 34.8 %). Bar 0.898 on shapes. The straps have no nails, as W3-H1. Fix: the lid's shadow two tones down onto the coping and the turf east of it; 2 to 4 grit marks per tread at random spacing in two sizes; nails as W3-H1.

#### Ground

**W3-G1. Ruler lines in the shrubs' shadows (fault).** Crops: `ground_cmp.png`, `ground_cmp2.png` (round 2 and pass 3 side by side at 4x), `zone_shadow.png`. Pass 3 changed 3,563 texels of the ground, all in cast shadows. Seven shadows now carry a one-row dark edge 64 to 122 px long that is darker than the rows 2 above and 2 below by 6 L or more: x 360 to 481 at y 1344, 396 to 517 and 272 to 377 at y 1368, 576 to 698 at y 1584, 329 to 413 at y 1560, 81 to 157 at y 576, and 97 to 161 at y 984 (round 2 had dotted chains in some of these places; the only long lines it had are the footbridge's at y 903 to 943). Each is the projection of a shrub's flat lowest row (W3-B2: the brambles' 122 and 106 px base rows). In the zone the sprite's own straight contact line sits over the shadow's straight edge, and the bramble reads as standing on a shelf. Fix: cast the shadow from the mass's silhouette with the house scalloped rim along its leading edge, so no edge row runs straight for more than about 12 px; and fix the sprites' bases (W3-B2).

**W3-P1. A pass carried onto new bytes (process).** Pass 3 changed `ground.png` (sha256 13c60f8b to a228894b) and wrote the new sha256 into `art/catalogue/woodland/ground.json` while keeping round 2's `reviewer.verdict: pass`, so at 76fc00d6 the gate placed ground bytes no auditor had seen. The commit says the reviewer blocks were "kept as the auditor wrote them". A byte change must leave the verdict `pending` (`review:asset --record` does this); never copy a reviewer block onto a new sha256. This round now reviews those bytes and fails them.

### False positives

3 rejected:

- **`detail.light` on the birch** (50,121,60,203): the trunk is lit west; its column means fall from L 217 at the west edge to 72 at the east.
- **`detail.outline` on hatch_closed** (0 % edge tone): a hatch set flush in the ground meets the worn earth, not an outline. The same finding on hatch_open (24 %) stands as polish for the lid.
- **`logic.scale` on `standing_stone_broken` and `standing_stone_low`**: short by design, as in rounds 1 and 2 (counted once).

Accepted as polish, not rejected: `logic.scale` on `standing_stone` (30 px wide, a slim menhir), `bush_c` (116 against 115) and `bramble` (122, a bramble patch). The scene gate's 88 `logic.wiring` blockers belong to quests in zones not yet built and are outside this asset gate.

### Not checked

- **No in-game render.** The zone was composed from the scene data (`--no-render`). Day and night, the night tint and a phone were not checked.
- **Scene grid cells.** The scene gate's 6 x 4 cells were not visited one by one; the stone circle and the bramble shadows were cropped from the composite.
- **Hatch states.** The hatches were seen as pictures and in the composite, not in their live state switch.
- **Kit pieces and props.** The kit pieces, prop shadows (`game/kit/props/art/shadow_woodland_*.png`), kit grounds and `kitlab` regenerated in pass 3 were not reviewed.
- **Eastward measures from JPEG.** The run, clump-contrast and pocket measures on Eastward were taken on its 3x JPEG brought to native with a box filter; JPEG softening lowers its contrast and lengthens its runs a little, so the gaps above are if anything understated.
- **No fixes.** Nothing was repainted.

## Round 4: pass 6 of the redraw (9 Nov 2026)

The asset gate on draft PR #446 (`claude-a/woodland-redraw`, head **dbd1841b**, "Woodland, pass 6"). Since round 3 (96b992e6), pass 4 changed the pine, both hatches, `standing_stone_low`, the lintel and the stone top; passes 5 and 6 changed the 13 broadleaf and shrub pictures and `woodland/ground`. Pass 6 follows Claude A's redirection toward Eastward's two-scale crown (big masses with merged lit fields, dark pockets between them, a ragged mid band, lit greens a step lower and less yellow, shade a step higher and warmer). Reviewed by a detail-auditor that drew none of it.

**Result: 8 of 25 pass** (the five stones of round 3, unchanged, plus `standing_stone_low`, `lintel` and `hatch_closed`). **17 fail, none on a blocker:** all 13 broadleaf and shrub crowns, the pine, `stone_top`, `hatch_open` and `woodland/ground`. Pass 6 is the first pass whose crowns read as trees at 1x, and I agree with Claude A's read: the mass structure is right and its pockets are as deep as Eastward's. What still fails is one scale down. The lit fields are a soft felt of three close greens with no leaf clusters cut into them, and every crown misses the detail bar on shapes.

### What was reviewed and how

- **Calibration first.** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <refs-games/eastward>` gave recall **39 of 39**. False positives were 5 on 6 clean screens and 21 on 22 clean props, the same as rounds 1 to 3. `calibration_results.json` was reverted afterwards.
- **Asset gate.** `npm run review:asset -- woodland/<name> --record` for all 25. No record changed: every sha256 already matched. Detector result: **25 pass**, no blocker or fault. Polish findings:
  - `detail.bar` on all 13 crowns, the pine, the lintel, the stone top and `hatch_open`;
  - `detail.outline` on the birch, both brambles and both hatches;
  - `detail.cluster_noise` on both hatches (45.3 and 45.8 %);
  - `logic.scale` on `standing_stone`, `_broken`, `_low` and the bramble;
  - `detail.light` on the bramble.
- **Scene gate.** `npm run review:scene -- woodland --no-render` reaches its report: 88 blockers, all `logic.wiring` on quests whose zones are not built yet; 14 faults; 16 polish. The faults are 3 `logic.occlusion`, 3 `detail.flat`, 1 `detail.repetition`, 1 `logic.reach` and 1 `logic.shadow_orphan`. The willow's y-sort point is +87 px off its feet (W2-L1 stands). The orphan shadow at (766,1315,858,1378) is unchanged since round 3 (1 texel differs) and is left to the logic-auditor. I cropped the composite's shrub shadows at 3x (`m/scene_shadows_3x.png`). The scene's grid cells were not visited one by one.
- **The painter's sheets** in `wr6/`: `ew_cmp_crowns_p6.png`, `zone_p6_1x.png`, `cluster_p5_p6_1x.png`, `crops_p5_p6_4x.png`, `contact_trees_4x.png` and `contact_shrubs_4x.png`.
- **My own crops** (auditor scratchpad `audit446r4/m/`):
  - `litfield_ew_vs_p6_6x.png`: a 64 x 48 window of the red tree's lit field beside the oak, the beech and the bush, at 6x;
  - `oaklit6.png`, `willow3.png`, `hollow6.png` and `pine4.png`;
  - `holly6.png` and `bramble5.png`;
  - `stones8.png` and `hatch8.png`;
  - `ground_r3_vs_p6_3x.png`.
- **Measurements.**
  - Round 3's `crownm.py` and `pepper.py`, unchanged.
  - `cluster_noise.share_png` and lone texels.
  - Silhouette components, enclosed holes, the bottom row's width, and one-texel spurs as a share of the silhouette ring.
  - The willow's lower-curtain runs.
  - Trunk and silhouette diffs against pass 5 (55aeae4e).
  - The ground diff against pass 5 and against round 3's bytes, plus a scan for straight and detached one-row lines.
  - New this round, `two_scale.py` (below).
  - Every Eastward crop went through the same pipe: native 640 x 360 by box filter from the 1920 x 1080 JPEG, then x1.37 nearest neighbour, so windows are in our art px.
- **Eastward at the same character height.**
  - Trees: the red tree in 12 (462,105,598,190, crown mask by hue; lit field 480,110,530,150) and the two trees in 13 (342,163,397,224 and 508,145,565,214).
  - Pine: the pines in 12 (175,65,245,165).
  - Stones: the rocks in 17 (460,165,550,250) and 12 (497,205,555,235).
  - Hatches: the post box in 12.

### Checking the painter's numbers

All confirmed:

- **Foliage bars** are 0.768 (holly) to 0.888 (willow). The pine is 0.749. Tones a patch are 21.3 to 30.9 against 24.9 needed (0.9 x 27.71); the pine's 30.9 is the highest.
- **Cluster noise** on the 13 pass 6 pictures is 17.8 to 28.5 %; the pine is 30.9 %. H/V is 0.89 to 1.13.
- **Clump contrast** in 12 x 12 windows is 28.2 to 43.7 L. My run of `crownm.py` matches the painter's table to the decimal.
- **Near-black** sits in shade on every crown except the bramble (2 of 7 in shade, median 1 texel).
- **Trunks are byte-identical to pass 5.** For the oak, beech, birch, hollow tree and willow, no texel of the trunk's connected non-green component changed. The 6 to 56 other non-green texels that changed are glints, plus the willow's removed limb tip.
- **Silhouettes are locked to pass 5** on 11 of 13. The exceptions:
  - the willow: 71 texels, the limb tip;
  - the holly: 112 texels;
  - holly_b: its canvas grew from 78 x 78 to 79 x 81 (the spines).
- **Ground** changed 414 texels from pass 5, all in the holly and willow shadows. That is 6,239 from round 3's bytes, across passes 4 to 6.
- **The five round 3 stone passes** (`standing_stone`, `_b`, `_broken`, `_lean`, `_runes`) are byte-identical: e1059a04, 12fbece5, 4f859dc7, 1ecd239b and 32118c14. Their reviewer blocks are untouched.

**W3-P1 held.** At every pass commit (ba57a156, 55aeae4e, dbd1841b), every record whose sha256 differs from round 3's reads `pending`, and no reviewer block on unchanged bytes was edited. No verdict was carried onto new bytes.

### Ruling on the contrast measure

**The measure was wrong, not the art. It is replaced by two measures, and the one that matters still fails.**

Round 3's clump contrast (p90 minus p10 of a 3 x 3 blur in 12 x 12 windows anywhere in the crown) mixes two scales. It was written against pass 3's crowns, which had no mass structure, so it stood in for leaf clusters. On a two-scale crown it is mostly the luck of where a window falls: a window across a mass boundary scores high, and a window inside a lit field or a pocket scores low. Measured on Eastward through the same pipe, it gives 39.0 to 44.3 L (round 3 quoted 41 to 49 from a different crop and mask). The ≥ 40 L line therefore sits inside Eastward's own spread, and pass 6's 28 to 44 cannot be read either way. I drop it as a requirement.

What the eye uses, and what Eastward does, splits cleanly in `two_scale.py` (all in our art px):

- **Mass scale.**
  - *Mass*: p90 minus p10 of the crown's L after a masked Gaussian (σ 3 px).
  - *Lit to pocket*: the median L of the brightest quarter of that blur minus the crown's 5th percentile.
- **Leaf scale.**
  - *Lit-field c12*: the round 3 window measure, kept only in windows whose centre lies in the top 35 % of the mass blur, so it measures what is inside a lit field.

| | Mass (L) | Lit to pocket (L) | Lit-field c12 (L) | Whole-crown c12 (L) |
| --- | --- | --- | --- | --- |
| Eastward red tree, 12 | 51.4 | 96.1 | 40.9 | 39.0 |
| Eastward trees, 13 (west, east) | 54.3, 51.7 | 94.9, 93.9 | 46.0, 42.9 | 43.6, 44.3 |
| Eastward pines, 12 | 73.0 | 93.5 | 38.0 | 40.0 |
| oak p5 → p6 | 106.6 → 86.4 | 119.7 → 97.7 | 34.5 → 33.6 | 38.2 → 32.4 |
| beech | 108.1 → 89.0 | 114.8 → 97.2 | 33.7 → 29.3 | 33.4 → 28.6 |
| birch | 95.9 → 83.3 | 120.0 → 108.1 | 38.1 → 37.9 | 45.2 → 38.2 |
| hollow_tree | 108.8 → 87.9 | 114.8 → 97.2 | 26.9 → 28.5 | 36.4 → 31.2 |
| willow | 97.3 → 79.0 | 117.7 → 103.1 | 28.9 → 28.6 | 34.8 → 33.7 |
| sapling | 88.4 → 77.8 | 120.0 → 108.1 | 81.7 → 58.0 (3 windows) | 59.8 → 45.3 |
| bush | 110.0 → 88.7 | 110.2 → 97.2 | 32.0 → 31.9 | 44.9 → 35.6 |
| bush_b | 111.2 → 91.5 | 122.0 → 105.2 | 28.2 → 34.3 | 49.5 → 42.4 |
| bush_c | 109.1 → 92.2 | 110.2 → 97.2 | 29.3 → 20.0 | 46.7 → 34.1 |
| bramble | 90.3 → 56.4 | 97.2 → 70.5 | 48.6 → 47.1 | 53.8 → 39.0 |
| bramble_b | 90.9 → 63.2 | 97.2 → 70.5 | 43.4 → 47.8 | 45.5 → 34.6 |
| holly | 69.1 → 49.4 | 70.5 → 61.2 | 33.8 → 32.4 | 34.1 → 24.8 |
| holly_b | 68.5 → 44.5 | 70.5 → 52.9 | 39.3 → 36.8 | 38.6 → 30.3 |
| pine (unchanged) | 57.9 | 80.5 | 47.2 | 47.4 |

Read across, Claude A's redirection did what it meant to:

- **Pockets.** Pass 6's broadleaf pockets now sit where Eastward's do: lit to pocket is 97 to 108 L against 94 to 96. Pass 5's 115 to 122 was too hard.
- **Masses.** The mass step is still larger than Eastward's (79 to 92 against 51 to 54). That is a stronger whole-crown light than Eastward's evenly lit trees, not a fault.
- **Whole-crown contrast fell because the large-scale step got smaller.** That is the intended trade.
- **The lit fields were never fixed.** Inside them the leaf-scale contrast is 28.5 to 34.3 L on the big crowns and the bushes, and 20.0 on bush_c. Eastward's lit fields measure 38.0 to 46.0. Pass 6 left this where pass 5 had it (26.9 to 34.5) and lowered bush_c.

**Why the leaf scale matters visually** (`litfield_ew_vs_p6_6x.png`). In Eastward's lit field, every leaf cluster is a lit shape with a mid-dark notch cut under and right of it, so the field reads as many leaves catching light even at 1x. Ours is a camouflage of 2 to 4 texel patches in three greens within about 30 L, with a dark notch only every 15 to 20 texels. At 1x in the zone, the lit fields read as moss or felt laid over a tree-shaped form. On a phone at 2 device px a texel, sub-30 L mottle averages to one flat tone. That is the "big flat lit pad" Matt flags.

**The rule from this round** (replacing W3-F1's check 4):

- mass ≥ 50 L;
- lit to pocket ≥ 85 L;
- lit-field c12 ≥ 38 L (Eastward's least, 38.0; its mean is 43).

All three are measured with `two_scale.py` (Eastward through the JPEG pipe, which if anything understates its contrast). H/V ≤ 1.3 and near-black in shade stay as round 3 set them. The script is in the auditor's scratchpad and is not committed (detectors unchanged); its definition is the paragraph above.

### Verdicts

Bar is `detail.bar` (house-style 7: 0.9, or 0.85 on tones for ramp-built art). Lit is lit-field c12 (≥ 38 L). L-P is lit to pocket. Noise is `cluster_noise` (a fault at 48 % or more). Spurs are one-texel spurs as a share of the silhouette ring.

| Asset | Opaque (art px) | Bar (tones / shapes a patch) | Lit (L) | L-P (L) | H/V | Lone | Noise | Spurs | Verdict | Codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oak | 189 x 247 | 0.870 (24.1 / 56.1) | 33.6 | 97.7 | 1.02 | 0.3 % | 25.9 % | 0.1 % | fail | W4-F1, F2 |
| beech | 168 x 264 | 0.831 (23.0 / 56.2) | 29.3 | 97.2 | 1.02 | 0.3 % | 26.1 % | 0 | fail | W4-F1, F2; W3-T5 polish open |
| birch | 87 x 203 | 0.877 (27.4 / 55.5) | 37.9 | 108.1 | 1.00 | 1.4 % | 27.2 % | 0.8 % | fail | W4-F1, F2 |
| pine | 98 x 237 | 0.749 (30.9 / 47.4) | 47.2 | 80.5 | 1.30 | 0.3 % | 30.9 % | 0 | fail | W4-F2, T2 |
| hollow_tree | 207 x 227 | 0.868 (24.0 / 56.3) | 28.5 | 97.2 | 1.01 | 0.3 % | 24.0 % | 0 | fail | W4-F1, F2 |
| willow | 237 x 200 | 0.888 (27.8 / 56.2) | 28.6 | 103.1 | 0.89 | 0.6 % | 25.7 % | 0.1 % | fail | W4-F1, F2, T1 |
| sapling | 52 x 82 | 0.858 (30.3 / 54.3) | 58.0 | 108.1 | 1.11 | 0.6 % | 28.4 % | 3.4 % | fail | W4-F2 |
| bush | 92 x 61 | 0.858 (24.2 / 54.3) | 31.9 | 97.2 | 1.09 | 0.1 % | 24.7 % | 0 | fail | W4-F1, F2 |
| bush_b | 75 x 54 | 0.818 (25.6 / 51.8) | 34.3 | 105.2 | 1.08 | 0.6 % | 23.4 % | 0 | fail | W4-F1, F2 |
| bush_c | 109 x 57 | 0.784 (23.4 / 49.6) | 20.0 | 97.2 | 1.07 | 0.2 % | 19.4 % | 0 | fail | W4-F1, F2 |
| bramble | 126 x 48 | 0.842 (29.1 / 53.3) | 47.1 | 70.5 | 1.08 | 3.4 % | 28.5 % | 3.7 % | fail | W4-F2, B1 |
| bramble_b | 110 x 47 | 0.879 (27.7 / 55.7) | 47.8 | 70.5 | 1.11 | 2.3 % | 27.6 % | 4.0 % | fail | W4-F2, B1 |
| holly | 81 x 73 | 0.768 (21.3 / 51.5) | 32.4 | 61.2 | 1.13 | 2.1 % | 17.8 % | 9.0 % | fail | W4-F1, F2, F3 |
| holly_b | 81 x 79 | 0.826 (24.7 / 52.3) | 36.8 | 52.9 | 1.11 | 2.8 % | 24.9 % | 9.3 % | fail | W4-F1, F2, F3 |
| standing_stone | 30 x 89 | 0.934 stone (30.2 / 57.0) | | | | | | | **pass** (unchanged) | W3-S4 polish |
| standing_stone_b | 37 x 67 | 0.967 stone (32.7 / 59.0) | | | | | | | **pass** (unchanged) | W3-S4 polish |
| standing_stone_broken | 35 x 56 | 0.963 prop (33.5 / 48.5) | | | | | | | **pass** (unchanged) | W3-S4 polish |
| standing_stone_lean | 36 x 73 | 0.938 prop (25.3 / 60.3) | | | | | | | **pass** (unchanged) | W2-S2 polish |
| standing_stone_low | 61 x 56 | **0.990** stone (26.0 / 62.8) | | | | 1.2 % | 22.6 % | 0.5 % | **pass** | W3-S1 fixed; W3-S4 polish |
| standing_stone_runes | 33 x 64 | 1.271 prop (36.3 / 64.0) | | | | | | | **pass** (unchanged) | W3-S4 polish |
| lintel | 78 x 28 | **0.877** prop (23.7 / 45.7), meets | | | | 1.3 % | 29.9 % | 0 | **pass** | W3-S2 met; W4-S2 polish |
| stone_top | 36 x 21 | 0.834 prop (36.0 / 42.0) | | | | 3.7 % | 21.2 % | 0 | fail | W4-S1 |
| hatch_closed | 45 x 41 | **1.013** prop (27.5 / 51.0) | | | | 1.6 % | 45.3 % | | **pass** | W3-H1 fixed |
| hatch_open | 45 x 65 | 0.886 prop (26.0 / 44.6) | | | | 0.6 % | 45.8 % | | fail | W4-H1 |
| ground | 960 x 1728 | n/a | | | | | | | fail | W4-G1 |

### Status of the round 3 codes

| Code | Status | Evidence |
| --- | --- | --- |
| W3-F1 (horizontal dash speckle) | **fixed**, superseded by W4-F1 | The dashes are gone: H/V is 0.89 to 1.13 (from 1.31 to 1.57), and 85 to 92 % of the crown's area lies in clumps of at least 2 x 2 (median 6 texels). Its check 4 (12 x 12 contrast ≥ 40 L) is retired by the ruling above. |
| W3-F2 (black pepper) | **fixed** (bramble polish) | Near-black components are 1 to 12 a crown, median 1 to 3 texels, in shade on every crown. The exception is the bramble, at 2 of 7 (median 1). |
| W3-F3 (dark hair spurs) | **fixed** on the trees and bushes; **partly** on the brambles; **not fixed** on the hollies | Trees 0 to 0.8 % (sapling 3.4 %), bushes 0. Brambles 3.7 and 4.0 % of the ring, from 6.8 and 8.0. Hollies 9.0 and 9.3 % (W4-F3). |
| W3-F4 (bar) | **not fixed** | 0.768 to 0.888 on the 13 crowns and 0.749 on the pine; all short on shapes (W4-F2). |
| W3-T1 (pine floating clump, foot) | **partly** | One opaque component now (fixed). The foot is still a smooth symmetric skirt, west out 4 px and east 5 px over 13 rows (W4-T2, polish). |
| W3-T2 (hollow disc) | **fixed** | A graded far inner wall under the upper lip, a lit lower-west lip, an interior falling to near-black, the eyes in the dark (`hollow6.png`). |
| W3-T3 (willow ropes) | **fixed** | The lower curtain is 5.3 runs a row, median 17 texels wide (from 9.1 and 7). The outline sits on the curtains' outer edges. New speck: W4-T1. |
| W3-T4 (birch flare) | **fixed** | The width runs 13, 13, 13, 14, 15, 16, 18, 19, 19, 21, 21, 22, 22 over the last 13 rows. |
| W3-T5 (beech algae) | **open** (polish) | Still square green blocks near the east outline of the trunk. The trunk is pass 5's, unchanged. |
| W3-T6 (sapling hole) | **fixed** | No enclosed hole. |
| W3-B1 (shrub bar) | **not fixed** | Folded into W4-F2. |
| W3-B2 (bramble canes, base) | **partly** | Base fixed: the bottom row is 1 and 2 texels, and the mass ends in its own underside with notches under the arches. Canes not fixed (W4-B1). |
| W3-B3 (holly) | **not fixed** | Glints are fewer and only in the light (fixed). There are still no holly-leaf shapes, and the spines are one-texel spurs (W4-F3). |
| W3-S1 (low stone tombstone) | **fixed** | Irregular profile, bar 0.990: pass. |
| W3-S2 (lintel box) | **met** | Chips on the front bottom edge, a rounded end, bar met for ramp-built stone. The mortises are polish (W4-S2). |
| W3-S3 (stone top) | **partly** | The ochre mark has gone into the lichen tones and the corners are chipped. Bar 0.834 on shapes and a straight base (W4-S1). |
| W3-S4 (stone texture, lichen, moss) | **open** (polish) | On the passing stones: lichen as tan bars, the shared moss motif. |
| W3-H1 (closed hatch straps) | **fixed** | Nail heads at the board joints on both straps; the south lip broken into tones. Pass. |
| W3-H2 (open hatch) | **partly** | Tread marks vary. No lid shadow, no nails on the lid's straps, bar 0.886 on shapes (W4-H1). |
| W3-G1 (ruler lines) | **fixed**, replaced by W4-G1 | The only straight edge rows left are the footbridge planks (x 357 to 411, y 873 to 943), which are structure. |
| W3-P1 (verdict carried onto new bytes) | **held** | All changed records were `pending` at ba57a156, 55aeae4e and dbd1841b. |

### Findings and fixes (round 4)

**W4-F1. The lit fields have no leaf-scale contrast** (fault). Applies to the oak, beech, birch, hollow tree, willow, bush, bush_b, bush_c, holly and holly_b; not to the sapling, the brambles or the pine. Crops: `litfield_ew_vs_p6_6x.png`, `oaklit6.png`, `wr6/ew_cmp_crowns_p6.png` (bottom row).
- **What is wrong.** Lit-field c12 is 28.5 to 37.9 L (bush_c 20.0) against Eastward's 38.0 to 46.0. Each lit field is 2 to 4 texel patches of three yellow-greens within about 30 L, with one darker notch every 15 to 20 texels. In Eastward every lit cluster (5 to 8 texels across) has a mid-dark notch 1 to 2 texels deep under and right of it, so the field is made of leaves.
- **Fix.** Keep pass 6's mass layout, values and pockets: they meet Eastward (L-P 97 to 108).
  1. Inside each lit field, cut leaf clusters 5 to 8 texels across. Give about one in two a notch of leaf 2 (about 35 to 45 L under the cap tone), 1 to 2 texels deep, along its lower-right edge. The notches are scallop-shaped and point down.
  2. Do not brighten the caps. The contrast comes from the notches, so the field's mean stays a step lower and less yellow, as Claude A asked.
  3. Keep 2 tones at most inside a cluster.
  4. Check: lit-field c12 ≥ 38 L, mass ≥ 50 L and L-P ≥ 85 L with `two_scale.py`; H/V ≤ 1.3; near-black in shade.

**W4-F2. Detail bar on shapes** (fault). Applies to all 13 crowns and the pine. Shapes a patch are 49.6 (bush_c) to 56.3 against 57.0 needed (0.9 x 63.32). Every crown is short on shapes, not tones, except the oak, beech, hollow tree and holly, which are also short on tones (0.87, 0.83, 0.87 and 0.77 against 0.85). W4-F1's notched clusters add distinct shapes; that is the way there, never grain. Pine (47.4 shapes): break each tier's lower edge into 3 to 5 hanging clumps of different lengths, and add a second, darker branch layer in the gaps between tiers.

**W4-F3. Holly still does not read as holly** (fault; holly, holly_b). Crop: `holly6.png`. The crown is the shared mottle, with no leaf shapes. Its silhouette carries 25 and 26 one-texel spurs (9.0 and 9.3 % of the ring). Fix as W3-B3:
- leaves as distinct spiky ovals 5 to 7 texels long, in cool leaf 1 to 3, with a lit midrib on the lit side;
- spines 2 texels, grown from the leaf edges on the silhouette;
- no one-texel spurs.

**W4-B1. Bramble canes are still circular arcs** (fault; bramble, bramble_b). Crop: `bramble5.png`. The east canes of both brambles are a fan of 3 to 4 concentric arcs from one root (a rainbow), and each west cane is a single circular arc. Fix as W3-B2:
- each cane a curve whose bend changes along it, with a kink at a node every 6 to 10 texels and a droop at its tip;
- no two canes from one centre;
- at least one cane crossing another or crossing the mass.

**W4-T1. A detached speck by the willow** (fault). A 2 x 2 opaque component at x 158 to 159, y 143 to 144, clear of the curtain (the willow's second component). `logic.floating_part` did not fire. Fix: join it to its swag as a tip, or remove it.

**W4-T2. The pine's foot** (polish). A smooth symmetric skirt, west out 4 px and east 5 px over the last 13 rows. Fix: 2 or 3 uneven root flares, longer on the west, as W2-T5.

**W4-S1. The stone top misses the bar** (fault). Crop: `stones8.png`. 0.834 on shapes (42.0 of 50.36), and the base runs straight for 32 of 36 columns. Fix:
- 1 to 2 chips along the base, with a shade texel under each;
- calm lit-top patches of 4 to 8 texels instead of tan bars;
- a crack or a step on the front face.

**W4-S2. The lintel's mortises** (polish). Each mortise is still a near-black 3 x 3 square with one lit texel. Fix as W3-S2: a 4 x 3 socket with a dark near wall (stone 0 to 1), a stone-2 floor and a lit far (north) wall one row high. The lit top's tan lichen bars are W3-S4.

**W4-H1. The open hatch** (fault). Crop: `hatch8.png`. The bar is 0.886 on shapes (44.6 of 50.36). The lid casts no shadow on the coping or the turf east of it. Its two straps have no nail heads. Fix:
- the lid's shadow two tones down onto the coping and the turf east and below it;
- nails on the lid straps as on the closed hatch;
- grain breaks and an end-grain row on the lid for shapes.

**W4-G1. The shrub shadows' rims are detached hairlines** (fault, `woodland/ground`). Crops: `ground_r3_vs_p6_3x.png`, `scene_shadows_3x.png`.
- **What is wrong.** The straight rows are gone, but the rim was drawn as a separate one-texel wavy line 3 to 6 px above the shadow body, with grass on both sides. There are 19 such lines 12 to 42 px long, each at least 20 L darker than the grass 1 to 3 rows above and below: (425,1338) 42 px; (641,1578) 42; (282,1362) 38; (471,1362) 32; (331,1554) 25; (127,978) 21; (124,570) 19; (879,1194) 19; (374,1339) 19; (379,1555) 19; (590,1579) 19; (343,1362) 21; and others. In the composed zone they show as dark squiggles floating between the brambles' and holly's bases and their shadow bodies, like a pencil contour on the lawn.
- **Fix.** The scallop belongs on the shadow body's own leading edge: every rim texel has shadow directly under it, and no dark texel has grass on both sides vertically. Cast the body from the sprite's silhouette, starting at its base, so there is no strip of lit grass between the sprite and its shadow.

### Gate result at this branch

`python3 -m scripts.review.gate --check` **refuses 17 woodland pictures**, the 17 fails above:

- 16 because they changed since their fix-queue entry was written;
- `ground` because it failed independent review.

It prints **8 advisories**, to remove `hatch_closed`, `lintel`, `standing_stone`, `standing_stone_b`, `_broken`, `_lean`, `_low` and `_runes` from `art/catalogue/fix-queue.json`. The fix queue was not edited here; that is Claude A's call.

### False positives

3 rejected:

- **`detail.outline` on hatch_closed**: a hatch flush in the ground meets the worn earth, not an outline, as in round 3.
- **`logic.scale` on `standing_stone_broken`**: short by design (rounds 1 to 3).
- **`logic.scale` on `standing_stone_low`**: low by design (rounds 1 to 3).

Accepted as polish, not rejected:

- `logic.scale` on `standing_stone` (a slim menhir) and the bramble (a patch);
- `detail.outline` on the birch, both brambles and hatch_open;
- `detail.light` on the bramble;
- `detail.cluster_noise` on both hatches (45.3 and 45.8 %, under 48).

### Not checked

- **No in-game render.** The zone was composed from data (`--no-render`). Day and night, the night tint and a phone were not checked.
- **Scene grid cells.** Not visited one by one. The shadows and the painter's 1x cluster were looked at.
- **Kit pieces, prop shadows and kit grounds** regenerated by these passes (`woodland_kit/ground_baked.png`) were not reviewed.
- **Eastward from JPEG.** `two_scale.py`'s Eastward figures come from the 3x JPEG, box-filtered to native. Softening lowers its contrast, so the leaf-scale gap is if anything understated.
- **No fixes.** Nothing was repainted. `fix-queue.json`, `scripts/review`, `.github` and the detectors are untouched.

## Round 5: passes 7 and 8 of the redraw (10 Nov 2026)

The asset gate on draft PR #446 (`claude-a/woodland-redraw`, head **7a57b5a0**). Pass 7 (3e2979a7) answered round 4's W4 codes: leaf notches in the lit fields, holly leaves, bramble canes, the pine's hanging tiers, the stone top, the open hatch, the shrub shadows in `screen.py` and the willow's speck. Pass 8 rebuilt every broadleaf and shrub lit field from 10 to 16 texel Poisson-placed leaf clusters over pass 6's masses and deepened the hollies' core. Reviewed by a detail-auditor that drew none of it.

**Result: 10 of 25 pass** (round 4's eight, plus `stone_top` and `hatch_open`). **15 fail, none on a blocker:** the 13 broadleaf and shrub crowns, the pine and `woodland/ground`. Pass 8 is the right direction and I agree with Claude A's read: at 2x beside the red tree the lit fields are broad overlapping leaf clusters with lit caps and dark undersides, no longer felt or a notch net. They are still rounder and more regular than Eastward's, and that is now the measurable fault: the masses are twice Eastward's size, the clusters are smooth discs, and the pockets are empty. The holly still reads streaky.

### What was reviewed and how

- **Calibration first.** `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <refs-games/eastward>`: recall **39 of 39**, false positives 5 on 6 clean screens and 21 on 22 clean props, as rounds 1 to 4. `calibration_results.json` reverted.
- **Asset gate.** `npm run review:asset -- woodland/<name> --record` for all 25. Every sha256 matched; the only change was the `reviewed` date, reverted. Detectors: **25 pass**, no blocker or fault. Polish: `detail.bar` on the 13 crowns, the pine and `stone_top`; `detail.outline` on both brambles and both hatches; `detail.cluster_noise` on both hatches (45.3 and 46.8 %); `logic.scale` on `standing_stone`, `_broken`, `_low` and the bramble.
- **Scene gate.** `npm run review:scene -- woodland --no-render`: 88 blockers (all `logic.wiring`, zones not built yet), 14 faults, 16 polish, the same faults as round 4. The willow's y-sort point is still +87 px off its feet (W2-L1); the orphan shadow at (766,1315,858,1378) stands for the logic-auditor.
- **The painter's numbers** (PR body, pass 7 → 8) are confirmed to the decimal: `two_scale.py` (round 4's definition, unchanged) for mass, lit to pocket and lit-field c12; the catalogue's `detail_bar` for tones and shapes.
- **Silhouettes and bytes.** Alpha is identical to pass 7 on all 13 pass 8 pictures, and the pine, `stone_top`, `hatch_open` and the five round 3 stones, `standing_stone_low`, `lintel` and `hatch_closed` are byte-identical to pass 7. Opaque components, enclosed holes and one-texel spurs (an opaque texel with at most one 4-neighbour) were counted on all 16.
- **New this round** (auditor scratchpad `audit446r5_tools/`, not committed; detectors and thresholds unchanged):
  - `ew_shapes.py`: `bands.patch_counts` (H 74, 18 px patches, a patch counts at ≥ 60 % mask) on Eastward's foliage with the background excluded, split into lit field, mid band and pockets by round 4's mass blur; ours through `bands.jpeg_roundtrip` as `score()` does.
  - `lp.py`: the lit-field median and the crown's 5th percentile behind lit to pocket, and the **mass grain** (the median run, along rows, of the mass blur above or below its median: how wide a lit mass or a pocket is, in art px).
  - `two_scale.py` with an ellipse or rectangle mask for Eastward shrubs that a hue mask cannot cut out.
- **Eastward at the same character height.** Trees: the red tree in 12 (462,105,598,190, mask by hue), the two trees in 13, the pines in 12. Dense shrubs: the shrub east of the red tree in 12 (588,200,618,243, ellipse), the fruit hedge in 13 (30,65,125,125, inside the mass) and the plant clump in 13 (62,230,105,268, ellipse).
- **Crops** (auditor scratchpad `audit446r5_m/`): `crowns_ew_vs_p8_3x.png` (the red tree beside the oak and beech), `litfield_ew_vs_p8_6x.png`, `shrubs_ew_vs_p8_4x.png` (Eastward's shrub and hedge beside the bush, hollies and brambles), `holly_6x.png`, `bramble_6x.png`, `pine_3x.png`, `stone_top_10x.png`, `hatch_open_10x.png`, `ground_hairlines_p8_6x.png`, `scene_shrub_shadows_3x.png`, and every crown at 3x or 6x.

### Ruling 1: the shapes bar on large-cluster foliage

**The ≥ 57 shapes bar is valid for the whole crown and stays. It is not a lit-field measure, and no painter should chase it inside a lit field.**

The foliage band (63.32 shapes a patch, so 57.0 at 0.9) was measured on whole Eastward boxes, background included. The builder is not in the repository and I could not reproduce its numbers exactly (my whole-box red tree is 63.4 box-filtered, 70.7 centre-sampled, against the band's 63.56). So I measured Eastward the way the detector measures ours, crown only. The like-for-like pipe is centre sampling: Eastward's shots are 3x JPEG read at the texel centre, and `jpeg_roundtrip` does exactly that to ours. Box filtering averages JPEG noise away and is shown as a floor.

| Shapes a patch (patches) | Crown, background out | Lit field | Mid band | Pockets | Mass grain (px) |
| --- | --- | --- | --- | --- | --- |
| Eastward red tree, 12 (centre / box) | **64.5** (36) / 60.7 | **48.5** (6) / 40.1 | 41.0 / 41.5 | 54.0 / 57.2 | 15 |
| Eastward west tree, 13 | 67.2 / 63.5 | 55.0 (1) / 51.0 | 50.0 / 51.0 | 54.5 / 50.0 | 15 |
| Eastward east tree, 13 | 64.5 / 61.3 | 63.0 (2) / 51.0 | 41.0 / 44.0 | 56.5 / 50.5 | 12 |
| Eastward pines, 12 | 62.4 / 55.4 | 38.2 (8) / 29.4 | 40.5 / 40.5 | 55.0 / 52.8 | |
| oak (pass 8) | 52.4 (61) | 46.8 (17) | 44.6 | 45.7, 14.5 tones | 34 |
| beech | 51.3 | 40.9 | 40.9 | 48.9, 15.4 tones | 32 |
| hollow_tree | 50.0 | 39.2 | 41.0 | 43.9, 15.0 tones | 35.5 |
| willow | 52.8 | 44.0 | 46.8 | 45.5, 23.4 tones | 13 |
| birch | 49.5 | 42.0 | | 46.8 | 16 |
| bush, bush_b, bush_c | 47.1, 49.1, 44.2 | 38.8, 41.0, 32.8 | | 39.0, 46.5, 43.4 | 25.5, 28, 25 |
| pine | 48.7 | 46.0 | 35.0 | 37.4, 17.0 tones | |
| Eastward pockets' tones | | | | 20.5 to 22.7 | |

What this shows:

1. **Eastward's own lit field scores under 57**: 48.5 on the red tree (40.1 box-filtered), 38.2 on the pines. Large calm clusters carry fewer shapes a patch, in Eastward as in ours. Pass 8's lit fields (39 to 47 on the trees) are already at Eastward's lit-field level. The painter was right not to add speckle there.
2. **Eastward's crowns still clear 57 as a whole**: 64.5 to 67.2 (60.7 to 63.5 even box-filtered), the pines 62.4. Large clusters do not make 57 unreachable. Eastward gets there from the parts between the lit fields: its pockets are drawn (54 to 57 shapes, 20.5 to 22.7 tones: dim back leaves, not a flat dark), and its masses are small (a lit mass or pocket runs 12 to 15 px), so most 18 px patches hold a lit edge, an under-edge and a pocket at once.
3. **Ours fall short in exactly those two places.** Pockets: 44 to 49 shapes and 14.5 to 15.4 tones on the oak, beech and hollow tree (flat). Mass grain: 32 to 35.5 px on the oak, beech and hollow tree, 25 to 28 on the bushes (twice Eastward's), so many patches sit wholly inside one lit field or one pocket. This is the same thing Claude A sees as "rounder and more regular".

So the bar stays at **shapes ≥ 57 a patch over the whole picture** (the detector's own number, unchanged). The way to it is W5-F1 below: smaller masses and drawn pockets, never grain. Lit fields are judged by lit-field c12 ≥ 38 L (round 4), not by shapes.

**Tones, for the same reason.** Eastward's crowns with the background out carry 22.8 to 24.1 tones a patch (centre), 20.5 to 24.2 box-filtered: the red tree is under the detector's 0.85 floor for ramp-built art (23.6). So for foliage the tones half of the bar is met at **≥ 20.5 tones a patch** (0.9 x the red tree's 22.8). Every pass 8 crown meets it (21.1 to 32.0). This changes no verdict in this round; it stops a later one failing a crown on tones that Eastward's red tree also misses.

### Ruling 2: lit to pocket on dense shrubs

**Lit to pocket ≥ 85 L applies to the brambles and the hollies.** Eastward's dense shrubs have pockets as deep as its trees', or deeper:

| | Lit-field median (L) | Crown p5 (L) | Lit to pocket (L) | Mass (L) | Lit-field c12 (L) |
| --- | --- | --- | --- | --- | --- |
| Eastward shrub east of the red tree, 12 | 141.9 | 42.5 | **100.4** | 62.4 | 68.7 |
| Eastward fruit hedge, 13 (inside the mass) | 147.0 | 47.1 | **103.3** | 56.5 | 80.4 |
| Eastward plant clump, 13 | | | 106.7 | 51.0 | 67.4 |
| bramble, bramble_b | 117.2 | 54.0 | 63.2 | 53.3, 54.1 | 42.4, 36.6 |
| holly, holly_b | 107.0 | 54.0 | 52.9 | 50.7, 47.1 | 34.0, 43.2 |
| our trees and bushes (for scale) | 146 to 159 | 54 to 56 | 92 to 103 | | |

The painter is right that the pockets cannot go deeper: 54 L is the palette's floor (Eastward's shrubs reach 42 to 47, but that is not needed). The shortfall is on the other side. The brambles' and hollies' lit tops sit at 107 to 117 L, about 30 to 40 L under our own bushes' and 25 to 40 under Eastward's shrubs. A holly is glossy: its leaves in the top light are the brightest faces in the woodland, not the dullest. Claude A's "lit greens a step lower and less yellow" concerns the broadleaf crowns' fields; it does not mean a shrub may have no lit top. Lift the top quarter's leaf faces to the trees' lit level in cool greens (W5-B2, W5-F4).

### Verdicts

Bar is `detail.bar` (shapes ≥ 57.0 a patch; tones per ruling 1 for foliage, 0.85 x 27.0 for ramp-built props). Lit is lit-field c12 (≥ 38 L), L-P is lit to pocket (≥ 85 L), mass ≥ 50 L. Grain is the mass grain (Eastward 12 to 15 px). Noise is `cluster_noise` (a fault at 48 %). Spurs are one-texel spurs.

| Asset | Opaque (art px) | Bar (tones / shapes a patch) | Mass (L) | L-P (L) | Lit (L) | Grain (px) | H/V | Noise | Spurs, holes | Verdict | Codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oak | 189 x 247 | 0.802 (22.9 / 50.8) | 71.3 | 95.2 | 41.6 | 34 | 0.93 | 28.0 % | 1, 0 | fail | W5-F1 |
| beech | 168 x 264 | 0.789 (21.9 / 50.3) | 76.5 | 92.4 | **37.9** | 32 | 1.01 | 23.4 % | 0, 0 | fail | W5-F1, F2; W3-T5 polish |
| birch | 87 x 203 | 0.803 (28.6 / 50.9) | 73.5 | 103.1 | 40.9 | 16 | 0.93 | 26.1 % | 5, 0 | fail | W5-F1 |
| pine | 98 x 237 | 0.767 (29.7 / 48.6) | 64.3 | 89.9 | 44.4 | | 1.13 | 29.8 % | 0, **14** | fail | W5-T1, T2; W4-T2 polish |
| hollow_tree | 207 x 227 | 0.791 (22.7 / 50.1) | 75.3 | 92.4 | 38.4 | 35.5 | 1.00 | 25.8 % | 0, 0 | fail | W5-F1 |
| willow | 237 x 200 | 0.827 (28.0 / 52.4) | 69.7 | 97.7 | **35.2** | 13 | 0.82 | 26.7 % | 2, 0 | fail | W5-F1, F2 |
| sapling | 52 x 82 | 0.800 (32.0 / 50.7) | 80.4 | 105.2 | 57.7 (2 windows) | | 1.04 | 29.1 % | 9, 0 | fail | W5-F1 |
| bush | 92 x 61 | 0.754 (22.3 / 47.8) | 75.3 | 92.4 | 40.4 | 25.5 | 1.12 | 17.5 % | 0, 0 | fail | W5-F1 |
| bush_b | 75 x 54 | 0.800 (25.2 / 50.7) | 73.9 | 97.2 | 44.5 | 28 | 1.17 | 22.8 % | 0, 0 | fail | W5-F1 |
| bush_c | 109 x 57 | 0.706 (21.1 / 44.7) | 80.8 | 92.4 | **32.0** | 25 | 1.14 | 21.5 % | 0, 0 | fail | W5-F1, F2 |
| bramble | 120 x 47 | 0.735 (24.6 / 46.6) | 53.3 | **63.2** | 42.4 | 19.5 | 1.11 | 21.9 % | 14, 23 | fail | W5-F1, B2 |
| bramble_b | 97 x 48 | 0.695 (22.0 / 44.0) | 54.1 | **63.2** | **36.6** | 15 | 1.14 | 20.8 % | 8, 48 | fail | W5-F1, F2, B2 |
| holly | 83 x 74 | 0.652 (21.8 / 41.3) | 50.7 | **52.9** | **34.0** | 17 | 1.21 | 24.3 % | 0, 0 | fail | W5-F1, F2, F3, F4 |
| holly_b | 77 x 78 | 0.597 (23.4 / 37.8) | **47.1** | **52.9** | 43.2 | 26 | 1.10 | 20.7 % | 0, 0 | fail | W5-F1, F3, F4 |
| standing_stone, _b, _broken, _lean, _runes | | unchanged | | | | | | | | **pass** (unchanged) | W3-S4, W2-S2 polish |
| standing_stone_low | 61 x 56 | 0.990 stone (unchanged) | | | | | | | | **pass** (unchanged) | W3-S4 polish |
| lintel | 78 x 28 | 0.877 prop (unchanged) | | | | | | | | **pass** (unchanged) | W4-S2 polish |
| stone_top | 36 x 21 | **0.852** prop (23.0 / 47.0; shapes 0.933), meets | | | | | 1.21 | 29.8 % | 0, 0 | **pass** | W4-S1 fixed; W5-S1 polish |
| hatch_closed | 45 x 41 | 1.013 prop (unchanged) | | | | | | 45.3 % | | **pass** (unchanged) | |
| hatch_open | 45 x 65 | **0.941** prop (28.0 / 47.4) | | | | | 1.59 | 46.8 % | 2, 0 | **pass** | W4-H1 fixed |
| ground | 960 x 1728 | n/a | | | | | | | | fail | W5-G1 |

The bramble's and bramble_b's enclosed holes (23 and 48 texels) are the ground seen under the arching canes, where a cane closes over the mass. They are structure, not pinholes.

### Status of the round 4 codes

| Code | Status | Evidence |
| --- | --- | --- |
| W4-F1 (lit fields with no leaf-scale contrast) | **met on 9 of 14** | Lit-field c12 ≥ 38 on the oak, birch, hollow tree, pine, sapling, bush, bush_b, bramble and holly_b. Not on the beech (37.9), willow (35.2), bush_c (32.0, down from pass 7's 41.9), bramble_b (36.6) or holly (34.0): W5-F2. Pass 8's clusters read as leaves (`litfield_ew_vs_p8_6x.png`). |
| W4-F2 (bar on shapes) | **not met**; restated by ruling 1 as W5-F1 | Shapes 37.8 to 52.4 a patch against 57. The lit fields are not the gap; the masses and the pockets are. |
| W4-F3 (holly does not read as holly) | **partly** | Spurs fixed: 0 one-texel spurs on both (from 25 and 26), spines 2 texels. The leaves are not readable shapes: at 6x they are 1-texel diagonal slivers and streaks, not spiky ovals with a midrib (`holly_6x.png`): W5-F3. |
| W4-B1 (bramble canes as circular arcs) | **fixed** | Each cane has its own root, kinks every 6 to 10 texels and a drooping tip; the west cane crosses over the mass; no two canes share a centre (`bramble_6x.png`). Polish only: at 1x the canes still read as smooth arches; the kinks are 1-texel steps. |
| W4-T1 (willow speck) | **fixed** | One opaque component. |
| W4-T2 (pine foot) | **open** (polish, deferred) | Trunk byte-identical. |
| W4-S1 (stone top) | **fixed** | Bar 0.852 (meets the 0.85 floor for ramp-built stone; shapes 0.933). Two 1-texel chips in the base at x 20 to 21 and 35 to 36, so the longest straight run is 15 of 36 columns (from 32); calm lit-top patches of 4 to 8 texels; a crack with a step down the front face (`stone_top_10x.png`). |
| W4-S2 (lintel mortises) | **open** (polish, deferred) | Lintel byte-identical. |
| W4-H1 (open hatch) | **fixed** | Bar 0.941. Nail heads on the lid's battens, three to a batten; grain checks on the boards; the lid's shadow on the coping under the hinges and a scalloped grass-1 shadow on the turf east of the lid (`hatch_open_10x.png`). |
| W4-G1 (detached shadow rims) | **fixed at the 12 named places**, replaced by W5-G1 | My scan finds none of the round's 12 hairlines (166 thin dark lines in the whole ground at pass 6, 152 now; the rest are trees, rocks and the footbridge). The new bodies leave a one-row light seam under the rim: W5-G1. |
| W3-T5 (beech algae) | **open** (polish) | Trunk unchanged. |
| W3-P1 | **held** | At 3e2979a7 and 7a57b5a0 every re-recorded picture was `pending`; no reviewer block on unchanged bytes was edited. |

### Findings and fixes (round 5)

**W5-F1. Masses too large and pockets empty** (fault; all 13 crowns). Crops: `crowns_ew_vs_p8_3x.png`, `scene_shrub_shadows_3x.png`.
- **What is wrong.** Shapes 37.8 to 52.4 a patch against 57 (Eastward's crowns 64.5 to 67.2). The lit fields are at Eastward's level (ruling 1). The deficit is the parts between them:
  - Ours run a lit mass or pocket 32 to 35.5 px wide on the oak, beech and hollow tree and 25 to 28 on the bushes and holly_b, against Eastward's 12 to 15. At 1x the crown reads as one lit half and one dark half, each paved with even discs.
  - The pockets are flat: 14.5 to 15.4 tones and 44 to 49 shapes a patch on the big crowns, against Eastward's 20.5 to 22.7 tones and 54 to 57 shapes.
  - The clusters are smooth discs of near-equal size on an even Poisson spacing, with 2 to 4 bites each. Eastward's cluster outlines are serrated all round (a leaf tip every 2 to 3 texels), and its clusters gather into lobes.
- **Fix.** Keep pass 8's cluster cap, body, cool under-edge and the masses' values (mass ≥ 50 and L-P ≥ 85 are met).
  1. Group the clusters into lobes of 3 to 6 clusters, 14 to 22 px across. Separate the lobes by pocket notches 3 to 6 px deep, so a lit mass or pocket runs 12 to 18 px (mass grain ≤ 18 px on `lp.py`).
  2. Draw the pockets: dim back-leaf clusters 6 to 10 texels in leaf 1 to 2, each with a leaf-0 under-edge, at least 2 per 18 px of pocket, never brighter than the mid band. Pocket patches ≥ 18 tones.
  3. Serrate every cluster outline: a 1 to 2 texel leaf tip every 2 to 3 texels along the lower and outer arc, in place of the 2 to 4 bites. Let the cluster size vary 8 to 20 texels within a lobe.
  4. No grain and no lone texels. Check: shapes ≥ 57 a patch (`npm run review:asset`), mass ≥ 50, L-P ≥ 85, lit-field c12 ≥ 38 (`two_scale.py`), noise under 35 %, H/V ≤ 1.3.

**W5-F2. Lit-field c12 under 38 L** (fault; beech 37.9, willow 35.2, bush_c 32.0, bramble_b 36.6, holly 34.0). Give the clusters in these lit fields the cap and cool under-edge at the full one-tone step the oak uses (oak 41.6). The willow's lit field is mostly its cap: put the clusters on the lit curtain heads too, not only on the cap. bush_c fell from 41.9 at pass 7: its clusters overlap so far that the under-edges are covered; keep at least a 2-texel under-edge showing on each.

**W5-F3. Holly leaves are streaks** (fault; holly, holly_b). Crop: `holly_6x.png`. Agreeing with Claude A, the crown reads streaky: the pass 7 leaf ovals now show as 1-texel-wide diagonal slivers. Fix:
- leaves 6 to 8 texels long and 3 to 4 wide, in two tones split along the midrib, with a lit midrib on the lit side;
- 1 to 2 spine notches along each leaf edge;
- leaves overlapping at no more than 3 angles in a cluster;
- keep 0 one-texel spurs.

**W5-F4. Shrub lit tops too dull** (fault; holly, holly_b; ruling 2). Lit to pocket 52.9 against 85. The lit-field median is 107 L; it needs about 140 with the 54 L floor. Light the leaves in the top-left quarter as glossy faces up to the trees' lit level (140 to 155 L) in cool greens, a 1 to 2 texel highlight on the upper edge of each. This also lifts holly_b's mass from 47.1 past 50. Do not lighten the core.

**W5-B2. Bramble lit tops too dull** (fault; bramble, bramble_b; ruling 2). Lit to pocket 63.2 against 85; the lit-field median is 117 L. Light the top lobes' leaf clusters to the bushes' cap tones (lit median about 140 to 145 L) in the same cool greens, keeping the dark underside and the canes.

**W5-T1. Pinholes in the pine** (fault). Crop: `pine_3x.png`. Pass 7's tier clumps leave 6 enclosed transparent holes, 14 texels, through which the ground shows: (46,32), (76,89), (32,98), (24,147), (86,165), (15,168). `crown_holes` did not fire (too small). Fix: close them in the under-tier tone.

**W5-T2. The pine's shapes** (fault). Shapes 48.6 against 57 (Eastward's pines, crown only, 62.4). The gap is the under-tier band: 37.4 shapes and 17.0 tones a patch, against Eastward's pine pockets at 55.0 and 22.2. Fix: draw needle sprays in the under-tier shade, 4 to 8 texels long, in needle 1 to 2 with a needle-0 under-edge, 2 to 3 per 18 px, and serrate each tier's hanging clumps with needle tips every 2 texels.

**W5-S1. The stone top's moss** (polish). The front face's moss is one flat lime blob (2 tones) that reads as a sticker at 10x. Give it a lit upper edge and a dark root line, as the lit-top patches have.

**W5-G1. A light seam under the shrub shadows' rims** (fault, `woodland/ground`). Crops: `ground_hairlines_p8_6x.png`, `scene_shrub_shadows_3x.png`.
- **What is wrong.** The new bodies start one row under a separate rim line. Down a column it reads rim (about 75 L), a one-row seam (105 L), then the body (75 to 82 L). There are 17 such seams 6 to 13 texels long, all new at pass 7; 11 of them are still visible in the composed zone with the sprite drawn: (131,573), (383,1341), (393,1341), (465,1363), (465,1365), (490,1365), (609,1581), (645,1581), (670,1581), (915,1200) and, half covered, (429,1365). At 3x the shrubs' shadows show a doubled edge.
- **Fix.** Fill the rim's row and the row under it with the body tone, so every rim texel has body directly under it: no texel between a rim and its body may be 20 L or more lighter than both. A scan for a one-row seam (a row ≥ 20 L lighter than the rows above and below, both under 95 L) must find none in the shrub shadows. Pass 7's 12 named fixes stand.

### Ruling 4: may the woodland scene be regenerated?

**No.** With this round's verdicts set, `python3 -m scripts.review.gate --check` refuses **15** woodland pictures (the 15 fails), and the zone generators stop on any refusal. A fix-queue entry cannot cover them: each is a new picture since its entry was written, and the gate never lets an entry cover new bytes. The scene may be regenerated when these 15 pass, together with the logic fix for W2-L1: the willow's y-sort point is +87 px off its drawn feet, unchanged since round 2, so people in front of it draw under it. That is a plan or kit placement fix, not art, and it belongs in the same regeneration. The gate now prints 10 advisories (`stone_top` and `hatch_open` added) to remove passing pictures from `art/catalogue/fix-queue.json`. The queue is not edited here; that is Claude A's call.

### False positives

- **`detail.bar` on `stone_top`**: polish at 0.852, met for ramp-built stone (rounds 3 and 4).
- **`detail.outline` on `hatch_open`** and `hatch_closed`: a hatch flush in the ground meets the worn earth, not an outline (round 3).
- **`logic.scale` on `standing_stone_broken` and `_low`**: rejected as in rounds 1 to 4.
- Accepted as polish: `detail.outline` on both brambles (the canes' tips), `detail.cluster_noise` on both hatches (under 48 %), `logic.scale` on `standing_stone` and the bramble.

### Not checked

- **No in-game render.** The zone was composed from data (`--no-render`). Day and night, the night tint and a phone were not checked.
- **The band builder.** Ruling 1 rests on my re-measurement of Eastward with the detector's `patch_counts`; the committed band (63.32) could not be reproduced exactly from the local shots, and its builder is not in the repository. Both pipes are shown; the ruling holds under either (Eastward's crowns 60.7 to 67.2, its lit fields 38 to 63 with 1 to 8 patches each).
- **Eastward's shrubs** are cut with an ellipse or a rectangle inside the mass, not a hue mask, so a few edge texels of grass may sit in the ellipse. Shrinking each ellipse well inside the mass (12: 592,205,614,238; 13: 68,236,99,262) gives lit to pocket 114.0 and 90.5, both still over 85.
- **Kit pieces and `woodland_kit/ground_baked.png`** regenerated by these passes were not reviewed.
- **No fixes.** Nothing was repainted. `fix-queue.json`, `scripts/review`, `.github` and the detectors are untouched.

## Round 6: pass 9 of the redraw (10 Nov 2026)

The asset gate on draft PR #446 (`claude-a/woodland-redraw`, head **16b30d50**, pass 9, which includes the merge of main 3f0e5a49). Pass 9 answered round 5's W5 codes: every crown rebuilt as lobes 12 to 18 texels across with serrated clusters and drawn back-leaf pockets, glossy holly and bramble tops, the pine's pinholes closed and needle sprays added, and the shrub shadow seams filled. 15 pictures changed: the 13 crowns, the pine and `woodland/ground`. Reviewed by a detail-auditor that drew none of it, with Claude A's read (at 2x beside the red tree, pass 9 fixed the grain but lost pass 8's big-mass hierarchy: uniform cauliflower) weighed and measured, not taken on trust.

**Result: 15 of 25 pass** (round 5's ten, plus `willow`, `sapling`, `holly`, `holly_b` and `woodland/ground`). **10 fail, none on a blocker:** the oak, beech, birch, hollow tree, the three bushes, both brambles and the pine. Two rulings change the measures. The detector's shapes bar (≥ 57) compares unlike pipes and is withdrawn as a requirement for native-res foliage (ruling 1). Claude A's read holds, and is a new fault: pass 9's crowns have Eastward's large-scale contrast but not its organisation, and their leaf-scale contrast is a third too loud (ruling 2, W6-F1).

### What was reviewed and how

- **Calibration first.** `python3 -m scripts.review.calibrate` on Matt's flagged folder and `refs-games/eastward`: recall **39 of 39**, false positives 5 on 6 clean screens and 21 on 22 clean props, as rounds 1 to 5. `calibration_results.json` reverted.
- **Asset gate.** `npm run review:asset -- woodland/<name> --record` for all 25. Every sha256 matched its record; the only change was the `reviewed` date on the ten unchanged passes, reverted. Detectors: **25 pass**, no blocker or fault. Polish: `detail.bar` on the 13 crowns, the pine and `stone_top`; `detail.outline` on the birch and both brambles; `logic.scale` on the bramble.
- **W3-P1 held.** At 16b30d50 all 15 changed pictures read `pending`; no reviewer block on unchanged bytes was edited.
- **Scene gate.** `npm run review:scene -- woodland --no-render`: 88 blockers (all `logic.wiring`, zones not built yet), **15** faults (round 5: 14), 16 polish. The new fault is `detail.flat` at (109,649,157,666): the holly's cast-shadow tongue, now one body where pass 8 had a seam (false positive, below). W2-L1 stands: the willow's y-sort point is +87 px off its feet.
- **The painter's numbers** (PR body, pass 8 → 9) are confirmed to the decimal with round 5's tools: `two_scale.py` (mass, lit to pocket, lit-field c12), `lp.py` (mass grain) and `ew_shapes.py` (pocket tones and shapes), and the catalogue's `detail_bar`.
- **New this round** (auditor scratchpad `audit446r6_tools/`, not committed; detectors and thresholds unchanged):
  - `r6.py frag` and `frag2.py`: per 18 px patch, keys, tones, shapes (≥ 2 texels), one-texel fragments and shapes of ≥ 3 and ≥ 4 texels, for Eastward and ours, each with and without `bands.jpeg_roundtrip`; the key-split rate (the share of same-key neighbour pairs that a round trip parts); and **ours through Eastward's own pipe**: box-filtered down to Eastward's grid (÷ 1.37), one JPEG at 3x and q 90 read at texel centres, then × 1.37 nearest, exactly what the band applies to Eastward.
  - `w6.py` and `hier2.py`: the large-scale value structure (below).
  - `misc.py`: `cluster_noise`, H/V run ratio, one-texel spurs, holes, components, and pocket tones and shapes through Eastward's pipe.
  - `seams.py`: W5-G1's one-row seam scan on both grounds.
- **Eastward at the same character height** (× 1.37 nearest, as rounds 4 and 5): the red tree in 12 (465,110,590,230), the two trees in 13, the pines in 12; the round shrub in 12 (592,205,614,238), the plant clump in 13 (68,236,99,262) and the fruit hedge in 13 (30,65,125,125). Pass 8's bytes are 7a57b5a0.
- **Crops** (auditor scratchpad `audit446r6_m/`): `oak_ew_p8_p9_2x.png`, `beech_ew_p8_p9_2x.png` and `hollow_tree_ew_p8_p9_2x.png` (the red tree, pass 8 and pass 9), the same three as `*_sigma6_2x.png` (the σ 6 blur of L inside the crown), `birch_willow_p8_p9_2x.png`, `shrubs_p8_3x.png` and `shrubs_p9_3x.png`, `sapling_bushb_bramble_p8_p9_4x.png`, `holly_p9_6x.png`, `holly_b_p9_6x.png`, `bramble_b_p9_6x.png`, `pine_p8_p9_ew_2x.png`, `ground_shadows_p8_top_p9_bottom_4x.png` and `scene_flat_109_649_5x.png`.

### Ruling 1: the fragment argument and the shapes bar

**The painter's numbers are right and the diagnosis is half right. The JPEG round trip treats our art and Eastward's alike; the asymmetry is the × 1.37 nearest-neighbour step, applied to Eastward only. The detector's shapes ≥ 57 is withdrawn as a requirement for native-res foliage. Round 5's ruling 1 is reversed on this point.**

Same 16-level keys, 18 px patches, crown masks:

| Per patch | Keys | Shapes (≥ 2) | One-texel fragments | Shapes ≥ 4 | Key-split rate |
| --- | --- | --- | --- | --- | --- |
| Eastward red tree 12, as the band (its own JPEG, × 1.37) | 27.1 | **64.5** | 33.6 | 23.9 | |
| the same, at Eastward's own grid (13 px patches, no × 1.37) | 26.4 | **22.8** | 68.8 | (≥ 2 texels: 22.8) | |
| the same, plus our round trip (a second JPEG) | 47.7 | 49.7 | 123.5 | 13.1 | 0.56 |
| Eastward 13 trees, pines: as the band / own grid | | 62.4 to 67.2 / 19.3 to 21.0 | 34.9 to 42.6 / 71.4 to 77.1 | 20.7 to 24.0 | 0.49 to 0.58 (second JPEG) |
| ours pass 9, raw bytes | 12.1 to 16.4 | 34.3 to 44.0 | 3.3 to 13.0 | 19.9 to 25.3 | |
| ours pass 9, through `jpeg_roundtrip` (the detector) | 38.0 to 52.0 | **40.4 to 54.3** | 96.6 to 118.3 | 13.0 to 17.9 | 0.47 to 0.55 |
| ours pass 9, **through Eastward's own pipe** | | **67.5 to 78.7** | | 20.4 to 28.2 | |
| ours pass 8, through Eastward's own pipe | | 55.2 to 74.7 | | 20.4 to 27.8 | |

What this shows:

1. **The round trip does not hide our structure.** It raises our count (raw 34 to 44 shapes a patch, 40 to 54 after it), because JPEG noise parts large one-key fields into several 2+ texel pieces. It splits the same share of neighbour pairs in ours as in Eastward (0.47 to 0.55 against 0.49 to 0.58). Eastward at its own grid carries 69 to 77 one-texel fragments a patch, as many as ours (97 to 118 on 1.9 times as many texels).
2. **The × 1.37 nearest step makes Eastward's number.** It doubles about 60 % of Eastward's texels into 2-texel runs, so most of its one-texel JPEG fragments count as shapes: 22.8 shapes a patch at its own grid become 64.5 at ours. Our art never gets that step, so its fragments stay single. The painter's "90 against 30" is this, not a JPEG penalty on our greens.
3. **Through Eastward's own pipe, our crowns clear the band.** Pass 9 scores 67.5 to 78.7 against 62.4 to 67.2, and so did pass 8 (55 to 75). The shapes gap that round 5's W5-F1 chased was, in large part, the pipe.
4. **The count does not discriminate.** Shapes of ≥ 4 texels, a size match for Eastward's 2-texel shapes (one Eastward texel is 1.88 of ours), give 13 to 18 for ours through the detector, 20 to 28 through Eastward's pipe and 19 to 24 for Eastward. Depending on the pipe, ours is anywhere from 0.7 to 1.2 of Eastward, and grain would raise every version.

**The rule from this round:**

- The detector, its band and its threshold are unchanged, and `detail.bar` stays a polish finding on foliage. Its shapes number is not a pass or fail line for crowns drawn at native resolution.
- **What replaces it for foliage:**
  - shapes ≥ 57 a patch with ours sent through Eastward's own pipe (`frag2.py`'s `ewpipe`: box ÷ 1.37, `jpeg_roundtrip`, × 1.37 nearest, then `bands.patch_counts`), with `cluster_noise` under 35 % so that grain cannot buy it;
  - tones per round 5's ruling 1 (≥ 20.5 a patch);
  - pocket tones ≥ 18 a patch (round 5, detector pipe; tones barely move between the pipes, for example the oak's 22.4 against 23.3);
  - the structure tests that do discriminate: mass grain ≤ 18 px (round 5), lit-field c12 ≥ 38, mass ≥ 50 and lit to pocket ≥ 85 (round 4), and the hierarchy tests of ruling 2.
- **Where Eastward's pockets are the reference** (the pine, W6-T2), compare them through Eastward's pipe too.
- **Props, stone and hatches** are unaffected: their band and pipe are unchanged, and no prop verdict here rests on it.

### Ruling 2: the big-mass hierarchy

**Claude A's read holds, and it is a fault (W6-F1). It is not that pass 9 lost large-scale contrast: it has as much as Eastward. What is gone is the organisation. One small lobe repeats everywhere at a third more leaf contrast than Eastward's, and few lobes stand out from their pockets.**

Measured inside the crown (σ in art px; `w6.py`, `hier2.py`):

- **Lit-shade8:** the mean L where the σ 8 blur is in its top 30 % minus where it is in its bottom 30 %.
- **c12:** round 3's whole-crown window contrast.
- **Leaf/mass:** c12 over lit-shade8.
- **Lobe scale:** the first zero crossing of the autocorrelation of the σ 2 blur minus the σ 16 blur: how far one lobe-and-pocket swing runs.
- **Big lobes:** maxima of the σ 6 blur standing ≥ 15 L over their saddle, and their share of the ≥ 6 L maxima.

| | Mass σ3 / σ8 (L) | Lit-shade8 (L) | c12 (L) | Leaf/mass | Lobe scale (px) | Big lobes (share) |
| --- | --- | --- | --- | --- | --- | --- |
| Eastward red tree, 12 | 51.5 / 33.8 | 45.6 | 41.8 | **0.92** | **17.0** | 5 of 7 (0.71) |
| Eastward trees, 13 (west, east) | 58.5, 60.1 / 34.3, 37.5 | 50.2, 54.6 | 44.4, 45.8 | **0.88, 0.84** | **14.0, 13.5** | 4 of 5, 5 of 5 |
| Eastward pines, 12 | 68.9 / 52.8 | 49.7 | 41.9 | 0.84 | 14.0 | 3 of 5 |
| Eastward round shrub, 12 | | 54.7 | 52.6 | 0.96 | 14.0 | |
| Eastward clump and hedge, 13 (dense) | | 33.8, 48.1 | 55.8, 71.9 | 1.65, 1.50 | 11.0, 13.5 | |
| oak p8 → p9 | 71.3 → 56.2 / 65.1 → 39.1 | 60.0 → **38.9** | 35.3 → 56.5 | 0.59 → **1.45** | 23.0 → **9.0** | 4 of 6 → 4 of 8 (0.50) |
| beech | 76.5 → 61.8 / 73.0 → 48.6 | 68.3 → 48.4 | 30.8 → 53.5 | 0.45 → **1.11** | 21.5 → **8.0** | 4 of 6 → 4 of 9 (0.44) |
| birch | 73.5 → 62.8 / 60.1 → 45.4 | 62.6 → 45.3 | 38.0 → 56.4 | 0.61 → **1.25** | 16.0 → **9.0** | 2 of 5 → 2 of 5 |
| hollow_tree | 75.3 → 57.7 / 70.8 → 45.0 | 64.4 → **43.2** | 34.0 → 54.1 | 0.53 → **1.25** | 32.5 → **8.5** | 3 of 4 → 3 of 12 (0.25) |
| willow | 69.7 → 57.0 / 59.4 → 41.5 | 60.8 → 46.9 | 36.0 → 45.8 | 0.59 → 0.98 | 15.0 → 13.0 | 3 of 5 → 4 of 7 (0.57) |
| sapling | 80.4 → 57.0 | 59.7 → 47.7 | 48.0 → 59.5 (10 windows) | 0.80 → 1.25 | 14.0 → 14.0 | one dome |
| bush | 75.3 → 63.0 | 65.6 → 51.0 | 39.4 → 53.1 | 0.60 → **1.04** | 37.5 → **9.5** | one dome |
| bush_b | 73.9 → 68.1 | 62.6 → 50.9 | 40.4 → 60.3 | 0.65 → **1.19** | 33.5 → 22.0 | one dome |
| bush_c | 80.8 → 58.4 | 73.8 → 43.6 | 37.9 → 58.3 | 0.51 → **1.34** | 17.0 → **8.0** | 2 |
| bramble, bramble_b | 69.6, 57.0 (p9) | 60.4, 40.1 | 71.3, 68.3 | 1.18, 1.70 | 10.0, 17.0 | |
| holly, holly_b | 72.9, 67.4 (p9) | 62.0, 48.9 | 58.3, 63.2 | 0.94, 1.29 | 9.5, 16.5 | |
| pine (p9) | 64.3 / 46.3 | 53.4 | 47.2 | 0.89 | 15.0 | 1 of 3 |

What this shows (crops `oak_ew_p8_p9_2x.png` and `oak_ew_p8_p9_sigma6_2x.png`):

1. **The large-scale step did not fall below Eastward.** Pass 9's mass at σ 8 is 39 to 49 L on the trees, against Eastward's 34 to 38. The drop from 71 to 77 that Claude A notes takes the crowns from about twice Eastward's step to Eastward's level, as round 4 asked. Lit-shade8 is at Eastward on the beech, birch and willow (45 to 48), and under it on the oak (38.9) and the hollow tree (43.2).
2. **The lobe scale halved past Eastward's.**
   - Pass 8's lit or shaded run was 16 to 33 px (one lit half and one dark half; round 5's W5-F1).
   - Pass 9's is 8 to 9.5 px on the oak, beech, birch, hollow tree, bush and bush_c.
   - Eastward's is 13.5 to 17.
   - The 12 to 18 texel lobes were drawn, but each is split again by its own leaf-0 pocket notches, so the dominant swing is the cluster.
3. **Leaf contrast now outweighs mass contrast.**
   - Eastward's trees run leaf/mass 0.84 to 0.92: the lobes' light is a little stronger than the leaves inside them.
   - Pass 8 was 0.45 to 0.61 (masses with quiet leaves).
   - Pass 9 is 1.11 to 1.45 on the oak, beech, birch and hollow tree, 1.04 to 1.34 on the bushes.
   - This is the popcorn: every lobe carries the same full cap-to-notch contrast wherever it sits, so a lobe in the shaded lower right is as bright at its cap as one in the lit upper left.
4. **Few lobes stand out.** Eastward's σ 6 maxima mostly stand ≥ 15 L over their saddles (0.71 to 1.0). Pass 9's trees have 8 to 12 maxima, of which 0.25 to 0.50 do. In the σ 6 crops the red tree shows 5 bright lobes parted by deep local pockets; pass 9's oak shows an even mottle over a soft top-to-bottom gradient.
5. **Exempt from W6-F1:**
   - *The willow:* 0.98 and 13 px; its curtains are the big masses.
   - *The pine:* 0.89 and 15 px, at Eastward's pines.
   - *The hollies and brambles* (0.94 to 1.70): Eastward's dense shrubs themselves run 1.50 to 1.65, so the tree ratio does not apply.
   - *The sapling:* a 52 x 82 crown measured on 10 windows, one dome lit at the upper left.

### Verdicts

Bar is the detector's `detail.bar` (tones / shapes a patch). EW-pipe is shapes with ours through Eastward's pipe (ruling 1, ≥ 57). Mass ≥ 50, L-P ≥ 85, Lit (lit-field c12) ≥ 38, Grain ≤ 18 px, Pocket tones ≥ 18, Noise < 35 %, Leaf/mass ≤ 1.0 and lobe scale ≥ 12 px on the trees and bushes (ruling 2). H/V is the mean horizontal over vertical one-colour run (≤ 1.3).

| Asset | Bar (t / s) | EW-pipe | Mass | L-P | Lit | Grain | Pocket t | Noise | Leaf/mass, lobe px | H/V | Spurs, holes | Verdict | Codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oak | 0.788 (27.5 / 49.9) | 71.9 | 56.2 | 89.9 | 62.9 | 12 | 22.4 | 34.9 % | **1.45, 9** | 0.98 | 1, 0 | fail | W6-F1 |
| beech | 0.813 (27.8 / 51.5) | 76.1 | 61.8 | 89.9 | 64.5 | 14 | 22.2 | 30.7 % | **1.11, 8** | 1.05 | 0, 0 | fail | W6-F1; W3-T5 polish |
| birch | 0.752 (33.1 / 47.6) | 73.0 | 62.8 | 87.9 | 61.7 | 10 | 28.0 | 33.6 % | **1.25, 9** | 0.99 | 5, 0 | fail | W6-F1 |
| hollow_tree | 0.809 (29.2 / 51.2) | 75.6 | 57.7 | 99.0 | 60.1 | 12 | 22.6 | 33.7 % | **1.25, 8.5** | 1.03 | 0, 0 | fail | W6-F1 |
| willow | 0.815 (31.3 / 51.6) | 76.8 | 57.0 | 90.3 | 41.8 | 12 | 26.5 | 31.3 % | 0.98, 13 | 0.84 | 2, 0 | **pass** | W6-P1 polish; W2-L1 (scene) |
| sapling | 0.848 (32.3 / 53.7) | 78.7 | 57.0 | 103.1 | 75.4 (2 windows) | 10 | 31.0 | 33.3 % | (1.25, 14; one dome) | 0.98 | 9, 0 | **pass** | |
| bush | 0.762 (29.5 / 48.2) | 70.5 | 63.0 | 99.9 | 52.9 | 10 | 22.7 | 33.6 % | **1.04, 9.5** | 1.14 | 0, 0 | fail | W6-F1 |
| bush_b | 0.704 (28.1 / 44.6) | 67.5 | 68.1 | 87.9 | 58.0 | 11 | 18.0 | 30.2 % | **1.19**, 22 | 1.12 | 0, 0 | fail | W6-F1 |
| bush_c | 0.717 (28.4 / 45.4) | 70.2 | 58.4 | 99.0 | 65.9 | 12 | 22.8 | 30.0 % | **1.34, 8** | 1.14 | 0, 0 | fail | W6-F1 |
| bramble | 0.711 (31.3 / 45.0) | 74.1 | 69.6 | 99.0 | 70.0 | 17 | **16.0** (1 patch) | 32.6 % | (1.18, 10) | 1.15 | 14, 23 | fail | W6-B1 |
| bramble_b | 0.705 (34.8 / 44.7) | 70.0 | 57.0 | 102.3 | 73.9 | 9 | 20.0 | **35.9 %** | (1.70, 17) | 1.11 | 8, 48 | fail | W6-B2 |
| holly | 0.728 (32.3 / 46.1) | 72.2 | 72.9 | 92.7 | 67.2 | 13 | 24.3 | 30.2 % | (0.94, 9.5) | 1.14 | 0, 0 | **pass** | |
| holly_b | 0.640 (32.1 / 40.5) | 68.2 | 67.4 | 92.7 | 74.5 | 10 | 19.7 | 33.7 % | (1.29, 16.5) | 1.09 | 0, 0 | **pass** | |
| pine | 0.765 (30.0 / 48.5) | 68.7 | 64.3 | 89.9 | 44.7 | 13 | **17.4** | 30.1 % | 0.89, 15 | 1.17 | 0, 0 | fail | W6-T2; W4-T2 polish |
| ground | n/a | | | | | | | | | | | | **pass** | |
| stone_top, hatch_open, hatch_closed, lintel, the six standing stones | unchanged bytes | | | | | | | | | | | | **pass** (unchanged) | as round 5 |

The brambles' enclosed holes are the ground under the arching canes (round 5). The sapling's 4 components and 9 spurs are its twig, unchanged since pass 8. The holly, holly_b, the brambles and the sapling are measured on few patches or windows (1 to 11), so their verdicts lean on the crops too: the hollies read as glossy leaves 6 to 8 texels long, two tones a leaf, lit edges and spine notches, lit at the upper left with the berries in the shade (`holly_p9_6x.png`, `holly_b_p9_6x.png`).

### Status of the round 5 codes

| Code | Status | Evidence |
| --- | --- | --- |
| W5-F1 (masses too large, pockets empty) | **met as written**, but overshot: W6-F1 | Mass grain 9 to 17 px on every crown, pocket tones ≥ 18 on 12 of 14, serrated clusters. The shapes check is withdrawn by ruling 1. The lobes were split into cluster-size swings (ruling 2). |
| W5-F2 (lit-field c12 < 38) | **fixed** | 41.8 to 75.4 on every crown; the beech 64.5, willow 41.8, bush_c 65.9, bramble_b 73.9, holly 67.2. On the trees it is now above Eastward's 38 to 46, which is part of W6-F1. |
| W5-F3 (holly leaves as streaks) | **fixed** | Leaves 6 to 8 by 3 to 4 texels in two tones split along the midrib, a lit edge on the lit side, spine notches, 0 one-texel spurs. |
| W5-F4 (holly lit tops) | **fixed** | Lit median 136.7 L, L-P 92.7 on both; holly_b's mass 67.4. |
| W5-B2 (bramble lit tops) | **fixed** | Lit medians 143.9 and 146.4 L, L-P 99.0 and 102.3. |
| W5-T1 (pine pinholes) | **fixed** | 0 enclosed holes, one component; the trunk byte-identical. |
| W5-T2 (pine shapes) | **not met**; restated as W6-T2 | See W6-T2. |
| W5-S1 (stone top moss) | **open** (polish, deferred) | `stone_top` is byte-identical and keeps its pass. |
| W5-G1 (light seam under shrub shadows) | **fixed** | 0 one-row seams in the 21 changed shadow areas (17 at pass 8), none at the 11 named points, no hairline of 12+ texels (`ground_shadows_p8_top_p9_bottom_4x.png`). All 6,494 changed texels are shrub shadows. |
| W4-T2, W4-S2, W3-T5 | **open** (polish) | Unchanged bytes. |
| W3-P1 | **held** | The 15 re-recorded pictures read `pending` at 16b30d50. |

### Findings and fixes (round 6)

**W6-F1. One small lobe everywhere: no big-lobe value structure** (fault; oak, beech, birch, hollow tree, bush, bush_b, bush_c). Crops: `oak_ew_p8_p9_2x.png`, `oak_ew_p8_p9_sigma6_2x.png`, `beech_ew_p8_p9_2x.png`, `hollow_tree_ew_p8_p9_2x.png`, `shrubs_p8_3x.png`, `shrubs_p9_3x.png`.
- **What is wrong** (ruling 2):
  - Leaf/mass is 1.04 to 1.45 against Eastward's 0.84 to 0.92 (the round shrub 0.96).
  - The lobe scale is 8 to 9.5 px against 13.5 to 17. bush_b is at 22 px, but its leaf/mass is 1.19.
  - Only 0.25 to 0.50 of the σ 6 maxima stand 15 L over their saddle (Eastward 0.71 to 1.0).
  - Lit-shade8 is 38.9 on the oak and 43.2 on the hollow tree, against 45.6 to 54.6.
  - Every cluster carries the full cap-to-notch contrast wherever it sits, so the lit upper-left masses and the shaded lower-right masses differ little at 1x.
- **Fix.** Keep pass 9's cluster drawing (cap, two-tone body, cool under-edge, serrated outline), its back-leaf pockets and its palette, so the grain stays as it is. Change only how values are laid out:
  1. **Big lobes.** Group the 12 to 18 texel sub-lobes into big lobes:
     - the oak, beech and hollow tree: 4 to 6 lobes, 30 to 45 px across (the red tree's are about 41 px in our art px);
     - the birch: 3 to 4 lobes, 25 to 35 px;
     - each bush: 2 to 3 lobes, 25 to 35 px.
  2. **Each big lobe a dome lit from the upper left.** Shift every cluster's tones by where it sits in its lobe:
     - the upper-left third one ramp step up (caps reach leaf 4 to 5);
     - the middle as drawn;
     - the lower-right third one step down (caps no higher than leaf 2 to 3).
     - On top of that, the crown's lower-right lobes sit one step under its upper-left lobes, as pass 8's masses did.
  3. **Deep pockets only between big lobes.** Put the leaf-0 pocket notches only on big-lobe boundaries, 4 to 8 px deep, with the back-leaf clusters in leaf 0 to 1. Between sub-lobes inside a big lobe, the notch is the body tone (leaf 2), not leaf 0. This brings the leaf scale down to Eastward's without losing the clusters.
  4. **Check:**
     - with `w6.py`: leaf/mass 0.75 to 1.0, lobe scale ≥ 12 px, lit-shade8 ≥ 45 L, ≥ 4 big lobes on the oak, beech and hollow tree (≥ 2 on the birch and bushes) standing ≥ 15 L over their saddle, at a share ≥ 0.6;
     - and still mass grain ≤ 18 px (`lp.py`), lit-field c12 ≥ 38, mass ≥ 50, L-P ≥ 85 (`two_scale.py`), pocket tones ≥ 18, EW-pipe shapes ≥ 57, noise < 35 %, H/V ≤ 1.3.
     - Eastward meets all of these together (mass grain 12 to 15, lobe scale 13.5 to 17).

**W6-B1. The bramble's pocket is flat** (fault; bramble). Its one pocket patch holds 16.0 tones against 18. Fix: draw 2 to 3 back-leaf clusters in leaf 1 and 2 with a leaf-0 under-edge in the dark underside west of the root, as on bramble_b (20.0). Keep the lit tops and canes.

**W6-B2. bramble_b is grainy** (fault; bramble_b). `cluster_noise` 35.9 % against W5-F1's < 35 %. Fix: merge the 1 to 2 texel flecks in the lit tops into their clusters' caps, which merges about 2 % of the texels, so the noise falls under 35 %. Keep lit-field c12 ≥ 38 and L-P ≥ 85.

**W6-T2. The pine's under-tier pockets** (fault; restates W5-T2). Detector pipe: 17.4 tones a patch against 18. Through Eastward's pipe (ruling 1): 19.0 tones and 48.6 shapes, against Eastward's pine pockets 22.2 and 55.0 (0.86 and 0.88). Pass 9's sprays barely moved them (37.4 → 39.0 shapes). Fix: make the sprays 2 to 3 per 18 px of pocket, in needle 1 and 2 alternating spray to spray, with a needle-0 under-edge, and add a dim needle-2 tip at each hanging clump's foot. Check pocket tones ≥ 18 (detector) and ≥ 20.0 tones and 49.5 shapes through Eastward's pipe (0.9 of Eastward).

**W6-P1. The willow's crown lobes** (polish). 4 of its 7 σ 6 maxima stand 15 L over their saddle (0.57 against Eastward's 0.71). If the willow's cap is touched again, give its 2 to 3 cap lobes W6-F1's dome shift.

### False positives

- **`detail.flat` at (109,649,157,666) in the scene** (new): the holly's cast shadow east of its base, now one body because W5-G1 filled the seam. A cast shadow is two hard ramp steps by rule 8 and eastward-edges.md, so it is flat by design (`scene_flat_109_649_5x.png`). Rejected.
- **`detail.bar` on the 13 crowns and the pine**: ruling 1; foliage is judged by the replacement measures, not by this number.
- **As rounds 1 to 5:**
  - `detail.outline` on both brambles (the cane tips) and on the birch (its trunk's pale bark against the outline) is accepted as polish;
  - `logic.scale` on the bramble is accepted as polish (a patch);
  - `logic.scale` on `standing_stone_broken` and `_low` is rejected (short by design).

### Ruling 4: may the woodland scene be regenerated?

**No.** With this round's verdicts set, `python3 -m scripts.review.gate --check` refuses **10** woodland pictures (the oak, beech, birch, hollow tree, bush, bush_b, bush_c, bramble, bramble_b and pine). A fix-queue entry cannot cover them: each is a new picture since its entry was written. The zone may be regenerated when these 10 pass, together with W2-L1: the willow's y-sort point is +87 px off its drawn feet, a plan or kit placement fix that belongs in the same regeneration. The gate prints **14 advisories** to remove passing pictures from `art/catalogue/fix-queue.json`: round 5's ten plus `willow`, `sapling`, `holly` and `holly_b`. `ground` is not in the queue. The queue is not edited here; that is Claude A's call.

### Not checked

- **No in-game render.** The zone was composed from data (`--no-render`). Day and night, the night tint and a phone were not checked.
- **Ruling 1's pipe for ours** (`ewpipe`) assumes Eastward's art is drawn on its own native grid and shot at 3x with one JPEG near q 90. The shots' real JPEG quality is not known. A lower quality would add fragments to Eastward and favour ours, so the reversal holds either way.
- **The hierarchy measures** are new and rest on 4 Eastward trees and 3 shrubs. The willow's, hollies' and brambles' exemptions from W6-F1 rest on those few references and the crops.
- **Kit pieces and `woodland_kit/ground_baked.png`** regenerated by pass 9 were not reviewed.
- **No fixes.** Nothing was repainted. `fix-queue.json`, `scripts/review`, `.github` and the detectors are untouched.

## Round 7: pass 10 of the redraw (10 Nov 2026)

The asset gate on draft PR #446 (`claude-a/woodland-redraw`, head **109e778a**, pass 10 with the merge of main 82b87eec). Pass 10 answered round 6's codes: big lobes 30 to 45 px with a dome shift on the seven W6-F1 crowns, back leaves in the bramble's pocket, bramble_b's flecks merged, and the pine's sprays spread over each tier's shade. 10 pictures changed (oak, beech, birch, hollow tree, bush, bush_b, bush_c, bramble, bramble_b, pine). Reviewed by a detail-auditor that drew none of it, with Claude A's read weighed and measured: at 2x beside the red tree the big-lobe value structure is back, but the lobe boundaries read as thin dark leaf-0 lines through the crown (cracks, crazed paving, a brain), not Eastward's pockets.

**Result: 18 of 25 pass** (round 6's fifteen, plus `bramble`, `bramble_b` and `pine`). **7 fail, none on a blocker:** the oak, beech, birch, hollow tree, bush, bush_b and bush_c. Every W6 measure the painter claims is met, to the decimal. Claude A's read holds and is a new fault (ruling 1, W7-F1): the dark is the right amount and the right width, but it is drawn as one connected network along every lobe boundary instead of being gathered into pockets.

### What was reviewed and how

- **Calibration first.** `python3 -m scripts.review.calibrate` on Matt's flagged folder and `refs-games/eastward`: recall **39 of 39**, false positives 5 on 6 clean screens and 21 on 22 clean props, as rounds 1 to 6. `calibration_results.json` reverted.
- **Asset gate.** `npm run review:asset -- woodland/<name> --record` for all 25. Every sha256 matched its record; the only change was the `reviewed` date on the 15 unchanged passes, reverted. Detectors: **25 pass**, no blocker or fault. Polish: `detail.bar` on the crowns and the pine; `detail.outline` on the birch and both brambles; `logic.scale` on the bramble.
- **W3-P1 held.** At 109e778a the 10 changed pictures read `pending`; no reviewer block on unchanged bytes was edited. willow, sapling, holly, holly_b, `ground`, the stones, lintel and hatches are byte-identical to pass 9.
- **Scene gate not re-run.** `npm run review:scene -- woodland --no-render` was killed by the container (out of memory) and not repeated. Between 16b30d50 and 109e778a only the 10 sprites changed under `game/zones/woodland`; no plan or kit placement moved, so W2-L1 (the willow's y-sort point +87 px off its feet) stands as in round 6.
- **The painter's numbers** (PR body, pass 9 → 10) are confirmed to the decimal with round 6's tools run unchanged on the pass 10 bytes: `w6.py` (leaf/mass, lobe scale, lit-shade8, big lobes), `misc.py` (noise, H/V, spurs, holes, EW-pipe pockets), `two_scale.py`, `lp.py` and `ew_shapes.py`.
- **New this round** (auditor scratchpad `audit446r7_tools/`, not committed; detectors and thresholds unchanged):
  - `w7.py`: the dark structure by the Hessian of L (scale-normalised, σ 1.5, 2, 3 and 4 px, each texel at its strongest scale). A *ridge* is a line-like dark texel (largest eigenvalue a ≥ 12 L, the other under 0.35 a); a *pocket* is a blob-like one (both eigenvalues positive, the smaller over 0.6 a). Measured: the longest connected ridge network over the crown's equivalent diameter; pockets per 1000 crown px; the share of big-lobe borders (watershed of the σ 6 blur from its ≥ 15 L maxima) with a ridge or pocket within 2 px; the depth variation along the longest networks; the across-ridge asymmetry; and dark energy in each lobe's lower-right half over its upper-left half.
  - `w7width.py`: the strongest-scale mix of ridge and pocket texels and the dark band width across the longest network.
  - `cracks.py`, `cracks2.py`, `pockets.py`, `blobs.py`, `sandwich.py`, `coherence.py`, `lines.py`: threshold-based measures of the darkest classes (width, run length, closed cells, flanks, granulometry, coherence). They do **not** separate ours from Eastward (below) and are kept only as the record of what was tried.
- **Eastward at the same character height** (× 1.37 nearest, as rounds 4 to 6): the red tree in 12, the two trees in 13, the pines in 12, the round shrub in 12, the clump and hedge in 13.
- **Crops** (auditor scratchpad `audit446r7_m/`): `oak_ew_p9_p10_2x.png`, `beech_ew_p9_p10_2x.png`, `hollow_tree_ew_p9_p10_2x.png`, `birch_ew_p9_p10_2x.png` (the red tree, pass 9 and pass 10); `oak_ew_p10_4x.png`; `classes_ew_oak_hollow_tree_p10_2x.png` (five value classes, black deepest); `w7_network_ew_oak_p9_p10_2x.png` and `w7_network_ew_hollow_tree_p9_p10_2x.png` (red: the longest connected ridge network; yellow: other ridges; cyan: pockets; the red tree and the west tree of 13 first), `w7_network_beech_birch_p10_2x.png`, `w7_network_bushes_p10_4x.png`, `shrubs_p10_4x.png`, `pine_p9_p10_ew_3x.png`.

### Ruling 1: cracks, not pockets

**Claude A's read holds and is a fault (W7-F1). What separates pass 10 from Eastward is continuity and gathering, not width and not side.**

| | Longest dark network (diameters) | Pockets (px / 1000) | Borders traced (%) | Dark band across the network (px, median / p90) | Lower-right / upper-left dark |
| --- | --- | --- | --- | --- | --- |
| Eastward red tree, 12 | **0.35** (44 px) | **9.0** | 77 | 1.4 / 3.1 | 0.55 |
| Eastward trees, 13 (west, east) | **0.76, 0.61** | **6.5, 7.0** | 74, 62 | 2.8 / 7.0, 2.8 / 3.9 | 0.73, 0.53 |
| Eastward pines, 12 | 0.47 | 5.6 | 67 | 1.4 / 2.4 | 0.60 |
| Eastward round shrub, 12 | 0.38 | 15.1 | | | |
| oak p9 → p10 | 0.60 → **1.40** (230 px) | 12.2 → **2.7** | 74 → 79 | 2.0 → 2.8 / 4.1 | 0.73 → 0.70 |
| beech | 0.65 → **2.70** (424 px) | 10.8 → **3.3** | 54 → 80 | 2.0 → 2.8 / 5.0 | 0.59 → 0.56 |
| birch | 1.88 → **1.29** | 9.3 → **3.3** | 93 → 78 | 3.5 → 2.8 / 4.0 | 0.89 → 0.42 |
| hollow_tree | 0.92 → **2.23** (414 px) | 12.6 → **3.2** | 65 → 78 | 2.0 → 2.8 / 4.2 | 0.83 → 0.55 |
| bush | 0.58 → **1.51** | 5.2 → **2.8** | → 89 | 2.8 → 4.0 / 5.7 | 0.58 → 0.99 |
| bush_b | 2.15 → **1.36** | 6.5 → **0.3** | → 63 | 2.8 → 2.8 / 4.2 | 1.36 → 0.64 |
| bush_c | 0.89 → **1.72** | 7.0 → **3.3** | 86 → 94 | 2.8 → 4.2 / 7.0 | 0.54 → 0.77 |
| pine p10 | 0.74 | 5.2 | | | |
| willow, sapling (unchanged) | 0.96, 0.61 | 7.8, 2.6 | 74 | | |
| holly, holly_b, bramble, bramble_b | 2.22, 1.94, 1.02, 1.68 | 10.0, 9.3, 7.3, 4.3 | | | |
| Eastward hedge, clump 13 (dense) | 1.71, 0.47 | 11.4, 13.0 | 97, 83 | | |

What this shows (crops `w7_network_ew_*`):

1. **One network through the crown.** Eastward's longest connected dark ridge runs 0.35 to 0.76 crown diameters (44 to 57 px): its darks are short pieces that stop where a cluster in front crosses them. Pass 10's runs 1.29 to 2.70 diameters on the trees (230, 424 and 414 px on the oak, beech and hollow tree) and 1.36 to 1.72 on the bushes: one branching line follows boundary after boundary across the crown. Pass 9 was 0.58 to 0.92 on the oak, beech and hollow tree; the network is new with pass 10's boundary bands. This is the crack, paving or brain read.
2. **No pockets.** Blob-like dark (dark every way, not just across) is 5.6 to 9.0 px per 1000 in Eastward's trees and 15.1 in its round shrub; pass 10 has 0.3 to 3.3, down from pass 9's 5.2 to 12.6. The dome shift and the band put all the leaf 0 into lines; nothing gathers into a gap.
3. **Width is not the difference.** The dark band across the network is 2.8 px median (p90 4 to 7) in ours and 1.4 to 2.8 (p90 2.4 to 7.0) in Eastward; the share of ridge texels at each scale is similar. Every threshold-based width, run, flank or coherence test on the darkest classes (`cracks*.py`, `pockets.py`, `blobs.py`, `sandwich.py`, `coherence.py`, `lines.py`) finds Eastward's darkest classes as thin and as line-like as ours at leaf scale, because Eastward's leaf serrations are thin darks too. The fault is at the lobe scale: how far one dark line runs unbroken, and whether dark ever pools.
4. **Coverage by overlapping clusters** is a smaller gap: Eastward leaves 23 to 38 % of its lobe borders untraced, pass 10's trees 20 to 22 %, bush and bush_c 11 and 6 %, bush_b 37 %.
5. **"Mostly on the lower-right" is not borne out as a measure.** Within Eastward's own watershed lobes, dark energy in the lower-right half over the upper-left half is 0.53 to 0.73, and the across-ridge asymmetry is 14 to 23 L in Eastward and 19 to 23 L in ours. A pocket under one lobe is the upper-left edge of the next, so the split cannot see the side. Pass 10's dome shift already darkens each lobe's lower right (lit-shade8 54 to 62 L). The fix does not require a side; it suggests where pockets sit.
6. **Exempt:** the hollies and brambles (Eastward's hedge runs a 1.71 diameter network itself), and the pine (0.74, 5.2: at Eastward's pines). The willow (0.96) and sapling (2.6 pockets) are unchanged passes from round 6, outside this round; see W7-P1.

### Ruling 2: values at the limit

The oak's mass grain is exactly 18.0 px, the pine's detector pocket tones exactly 18.0, the beech's 18.9, the hollow tree's 18.6, bush 18.3 and bush_b 18.7. The bars are inclusive as written (grain ≤ 18, pocket tones ≥ 18), and the measures are deterministic on fixed bytes (re-run twice, identical), so a value on the line **meets** it. No margin is required for a pass. W7-F1's fix must keep them on the right side: breaking boundaries can lengthen lit runs (grain) and gathering dark can thin pocket tones in patches the band now feeds. Re-measure both after the fix, not only the new measures.

### Ruling 3: the pine's grass_cool 1

**Accepted. Not a fault, not a polish.**

- `grass_cool` is one of the pine's own crown families in `woodtrees.LOOKS` (`'pine': (('leaf_cool', 'leaf', 'grass_cool'), ...)`) and has been in its crown since before pass 9: pass 9's pine already carries grass_cool 0 to 4 (1,928 texels, 119 of them grass_cool 1). Pass 10 adds 103 texels of grass_cool 1.
- It is on the house palette (a ramp tone, no mix), and grass_cool 1 (75.2 L) sits at needle 2's value: leaf_cool 2 is 76.1 L. The third pair (grass_cool 1 / leaf_cool 2) is therefore a sibling swap at one tone, which `house-style.md` ("Clusters": most clusters swap to a sibling ramp at the same tone) and the foliage recipe (clumps from all three siblings) allow.
- The brief's "needle 1 to 2" names value steps, not a ramp; the art-style "four or five tones from its ramp" rule is met per value level. Should the pine ever be limited to leaf and leaf_cool, it is a one-line change in the pair list; no measure depends on it.

### Verdicts

Hierarchy (W6-F1): leaf/mass 0.75 to 1.0, lobe ≥ 12 px, lit-shade8 ≥ 45 L, big lobes ≥ 4 (≥ 2 on the birch and bushes) at share ≥ 0.6. Then grain ≤ 18 px, mass ≥ 50, L-P ≥ 85, Lit (lit-field c12) ≥ 38, pocket tones ≥ 18, EW-pipe shapes ≥ 57, noise < 35 %, H/V ≤ 1.3. Net is W7-F1's longest dark network (≤ 0.8 diameters), Pk its pockets (≥ 5 px / 1000).

| Asset | Leaf/mass, lobe px, lit-shade8, big lobes | Grain | Mass | L-P | Lit | Pocket t | EW-pipe | Noise | H/V | Net, Pk | Verdict | Codes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oak | 0.88, 12, 53.8, 9 of 15 (0.60) | 18.0 | 66.9 | 99.0 | 52.0 | 20.7 | 70.4 | 29.0 % | 0.93 | **1.40, 2.7** | fail | W7-F1 |
| beech | 0.85, 12, 59.6, 9 of 15 (0.60) | 16 | 74.8 | 99.0 | 54.2 | 18.9 | 73.3 | 25.9 % | 1.01 | **2.70, 3.3** | fail | W7-F1; W3-T5 polish |
| birch | 0.82, 13, 59.4, 4 of 6 (0.67) | 15 | 72.3 | 114.2 | 55.3 | 23.5 | 69.9 | 27.5 % | 0.93 | **1.29, 3.3** | fail | W7-F1 |
| hollow_tree | 0.80, 14, 55.4, 10 of 14 (0.71) | 17 | 69.3 | 91.8 | 49.3 | 18.6 | 71.4 | 27.1 % | 1.00 | **2.23, 3.2** | fail | W7-F1 |
| bush | 0.78, 18, 61.6, 2 of 3 (0.67) | 14 | 77.0 | 91.8 | 49.0 | 18.3 | 69.1 | 23.1 % | 1.10 | **1.51, 2.8** | fail | W7-F1 |
| bush_b | 0.85, 25, 61.9, 2 of 2 (1.00) | 11 | 76.7 | 99.0 | 55.0 | 18.7 | 73.3 | 24.1 % | 1.13 | **1.36, 0.3** | fail | W7-F1 |
| bush_c | 0.78, 16, 61.4, 2 of 3 (0.67) | 13 | 75.2 | 89.0 | 49.5 | 19.8 | 68.5 | 23.2 % | 1.08 | **1.72, 3.3** | fail | W7-F1 |
| bramble | (1.19, 10; dense) | 17 | 69.7 | 99.0 | 71.2 | **20.0** | 73.9 | 32.3 % | 1.14 | (1.02, 7.3; exempt) | **pass** | W6-B1 fixed |
| bramble_b | (1.60, 17; dense) | 9 | 58.5 | 102.3 | 74.2 | 20.0 | 68.5 | **33.4 %** | 1.13 | (1.68, 4.3; exempt) | **pass** | W6-B2 fixed |
| pine | 0.89, 14, 54.1, 1 of 3 | 14 | 64.7 | 89.9 | 47.8 | **18.0**; EW pipe 21.0 t / 55.0 s | 70.9 | 31.9 % | 1.15 | 0.74, 5.2 | **pass** | W6-T2 fixed; W4-T2 polish |
| willow, sapling, holly, holly_b, ground, stone_top, hatch_open, hatch_closed, lintel, the six standing stones | unchanged bytes | | | | | | | | | | **pass** (unchanged) | as round 6 |

Spurs and holes are unchanged in kind: the oak 1 spur, birch 5, bramble 14 spurs and 23 enclosed texels, bramble_b 8 and 48 (ground under the canes, round 5); every crown is one component. The bushes are compared with Eastward's round shrub, the trees with the red tree and the trees in 13, side by side at 2x (crops above).

### Status of the round 6 codes

| Code | Status | Evidence |
| --- | --- | --- |
| W6-F1 (no big-lobe value structure) | **met as written** on all seven, but the boundaries became a crack network: W7-F1 | Leaf/mass 0.78 to 0.88, lobe scale 12 to 25 px, lit-shade8 53.8 to 61.9, big lobes 9/0.60, 9/0.60, 4/0.67, 10/0.71, 2/0.67, 2/1.00, 2/0.67. |
| W6-B1 (bramble pocket) | **fixed** | Pocket tones 16.0 → 20.0; canes unchanged. |
| W6-B2 (bramble_b grain) | **fixed** | Noise 35.9 → 33.4 %; lit-field c12 74.2, L-P 102.3. |
| W6-T2 (pine pockets) | **fixed** | Detector 18.0 tones; Eastward's pipe 21.0 tones and 55.0 shapes (targets 20.0, 49.5). grass_cool 1 accepted (ruling 3). |
| W6-P1 (willow lobes) | **open** (polish, deferred) | Willow byte-identical. |
| W5-S1, W4-T2, W4-S2, W3-T5 | **open** (polish) | Unchanged bytes. |
| W3-P1 | **held** | The 10 re-recorded pictures read `pending` at 109e778a. |

### Findings and fixes (round 7)

**W7-F1. Big-lobe boundaries drawn as one crack network, no pockets** (fault; oak, beech, birch, hollow tree, bush, bush_b, bush_c). Crops: `w7_network_ew_oak_p9_p10_2x.png`, `w7_network_ew_hollow_tree_p9_p10_2x.png`, `w7_network_beech_birch_p10_2x.png`, `w7_network_bushes_p10_4x.png`, `classes_ew_oak_hollow_tree_p10_2x.png`, `oak_ew_p10_4x.png`.
- **What is wrong** (ruling 1): the ~4 px leaf-0/leaf-1 band on every big-lobe boundary joins into one branching line 1.29 to 2.70 crown diameters long (Eastward 0.35 to 0.76), and almost no dark pools into a pocket (0.3 to 3.3 px per 1000 against 5.6 to 9.0). At 2x the crown reads as cracked paving, the lobes outlined rather than overlapping.
- **Fix.** Keep pass 10's big lobes, dome shift, sub-lobe body-tone notches, clusters and palette (every W6 measure). Change only how the boundary is drawn:
  1. **Break each boundary.** Every 10 to 20 px along a big-lobe boundary, let 1 to 2 clusters of the front (lower or nearer) lobe cross it with their cap and body, so no dark run goes on past one such crossing. No dark line passes through a point where three lobes meet; end it 2 to 4 px short.
  2. **Gather the leaf 0 into pockets.** On each boundary put 1 to 3 pockets, irregular blobs 5 to 10 px across (sizes varied, spacing uneven), most where three lobes meet or where the boundary runs under a lobe's lower edge: a leaf-0 core 3 to 6 px wide, ringed by back-leaf clusters in leaf 1 with their serrated tips reaching into the core.
  3. **Between pockets** the boundary is leaf 1 to 2 only, at most 2 px wide, broken by the crossings in step 1. No leaf 0 outside a pocket, except the cluster under-edges already drawn.
  4. bush_c and bush_b: the same at their smaller scale (pockets 4 to 7 px), at least 2 pockets each.
  5. **Check:** with `w7.py`, the longest dark network ≤ 0.8 crown diameters and pockets ≥ 5 px per 1000 crown px, borders traced ≤ 77 %; and still every W6 measure: leaf/mass 0.75 to 1.0, lobe scale ≥ 12 px, lit-shade8 ≥ 45 L, big lobes ≥ 4 (≥ 2) at share ≥ 0.6 (`w6.py`); mass grain ≤ 18 px (`lp.py`; the oak is on the line now), mass ≥ 50, L-P ≥ 85, lit-field c12 ≥ 38 (`two_scale.py`); pocket tones ≥ 18 (`ew_shapes.py`; the beech, hollow tree, bush and bush_b are within 1 of it); EW-pipe shapes ≥ 57, noise < 35 %, H/V ≤ 1.3 (`misc.py`). Pass 9 met the network and pocket targets on the oak, beech and hollow tree (0.60 to 0.92, 10.8 to 12.6), so they are reachable together with the W6 hierarchy.

**W7-P1. The willow's dark network** (polish, unchanged bytes). 0.96 diameters with 7.8 pockets per 1000: its curtain gaps join a little longer than Eastward's 0.76. If the willow is repainted for W6-P1, break the longest curtain gap once.

### False positives

- **`detail.bar` on the crowns and the pine**: round 6's ruling 1; foliage is judged by the replacement measures.
- **As rounds 1 to 6:** `detail.outline` on both brambles (cane tips) and the birch (pale bark), `logic.scale` on the bramble, accepted as polish; `logic.scale` on `standing_stone_broken` and `_low`, rejected.

### Ruling 4: may the woodland scene be regenerated?

**No.** With this round's verdicts set, `python3 -m scripts.review.gate --check` refuses **7** woodland pictures (the oak, beech, birch, hollow tree, bush, bush_b and bush_c). A fix-queue entry cannot cover them: each is a new picture since its entry was written. The zone may be regenerated when these 7 pass, together with W2-L1 (the willow's y-sort point +87 px off its drawn feet, a plan or kit placement fix that belongs in the same regeneration). The gate prints **17 advisories** to remove passing pictures from `art/catalogue/fix-queue.json`: round 6's fourteen (`hatch_closed`, `hatch_open`, `holly`, `holly_b`, `lintel`, `sapling`, the six standing stones, `stone_top`, `willow`) plus `bramble`, `bramble_b` and `pine`. The queue is not edited here; that is Claude A's call.

### Not checked

- **No in-game render, and the scene gate was not re-run** (killed out of memory; only the 10 sprites changed in the zone since round 6). Day and night, the night tint and a phone were not checked.
- **The crack measures are new.** `w7.py`'s ridge and pocket classes and the 12 L depth were set on 4 Eastward trees and 3 shrubs; the network length is the measure that separates most clearly, and it agrees with the crops. The threshold-based measures tried first did not separate ours from Eastward and carry no verdict.
- **The lower-right placement** of Eastward's pockets is not confirmed by any measure here (ruling 1, point 5); the fix leaves it as advice.
- **Kit pieces and the baked grounds** regenerated by pass 10 and the merge were not reviewed.
- **No fixes.** Nothing was repainted. `fix-queue.json`, `scripts/review`, `.github` and the detectors are untouched.
