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
