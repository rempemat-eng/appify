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
