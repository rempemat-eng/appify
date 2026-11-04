# Asset gate: the woodland's water (4 Nov 2026)

An independent detail-auditor run (`.claude/agents/detail-auditor.md`) on the two woodland water assets repainted on `claude-a/water-polish` (draft PR #434). The auditor did not paint them.

**Verdicts: `woodland/ground` fail, `woodland/flow` fail.** The repainted banks meet 5.3a: one rim on every side and south shore, faces only on north banks, and wet feet on the stones. Two things still fail. The plunge pool's foam is a flat white plate. The moving water draws marks that run across the current.

## What was reviewed

- Commit **4881fee7** ("Water: a softer side and south rim; the woodland re-rendered with the new banks"), branch `claude-a/water-polish`.
- `game/zones/woodland/art/ground.png` (960 x 1728, density 3, H = 74), record `art/catalogue/woodland/ground.json`, sha256 `91d893d9...`.
- `game/zones/woodland/art/flow.png` (1584 x 832: 2 x 4 frames of 792 x 208, placed at (168, 756) by `woodland_base.tscn`, cycled at 0.16 s by `world/flow_anim.gd`), record `art/catalogue/woodland/flow.json`, sha256 `b3d7998d...`.
- The in-game capture of the spring and the fall top, before and after, at 1x (the painter's, local only).

## Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's 25 Oct screenshots> --eastward <Eastward shots>`: **recall 38 of 38**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as the last runs (rev288 and rev298).
- `npm run review:asset -- woodland/ground --record` and `npm run review:asset -- woodland/flow --record`: both PASS the detectors with 0 findings. The sheets are in `artifacts/review/assets/woodland__ground.png` and `woodland__flow.png` and are not committed.
- `python3 -m scripts.review.gate --check --zone woodland` after the verdicts: **refuses `woodland/flow`**, because it fails and is not in the fix queue. `woodland/ground` is in the seeded fix queue, so it may stay placed. **`npm run check:kit`, and so `npm run verify`, now fail on this branch until flow is fixed and re-reviewed.**
- The flow frames were composited over the ground at their scene position, one frame at a time, to judge what a player sees. Pixel samples were taken along rims, the foam, the crest and the streaks. The numbers below come from those samples.

## Eastward comparison (same character height)

Ours H = 74 art px. Eastward is about 54 native px, so each shot was brought to native (13 by `core.to_native`, 3.00x; 15 and 37 box-averaged from 1920 x 1080 to 640 x 360) and scaled 1.37 with nearest neighbour. The crops stay local and are not committed.

- **13, the canal (native box 0-240 x 295-360):** the grass lip, an earth face, a 1 px light waterline and a calm body. Our north banks match this: a three-brown clod face with a near-black foot, a light waterline and a depth band.
- **15, the channels (native box 440-640 x 0-220):** the side shores step from mud into the body through a soft band, with no light line. The body is almost bare, and a short light line sits at each reed's foot. Our side and south rims follow the 5.3a reading of this (earth_cool 1, then RIM_LINE). Ours keeps a 1-texel L≈21 line between turf (L≈63) and water (L≈53), so it still reads as a thin outline where 15 has none. 5.3a chose this, so it is noted here and not counted as a finding.
- **37, the pond and the fall's mist (native box 510-640 x 160-360):** Eastward's white water is a soft mass in many tones. Its edge dissolves through checker and leaf-shaped flecks into the grass and the water, and nothing in it has a hard outline. No local shot shows an Eastward plunge pool up close, so the foam was judged against this mist, against the house rule ("a fall has a lip, volume, streaks, foam, spray and rings", art-style.md, density 3) and against calibration fault W3.
- **Detail counts** (`bands.patch_counts`, 0.25 H patches, ours through the same JPEG pipe). `eastward_bands.json` has no water group, so `bands.score` falls back to the prop band, and its 0.12 ratio means nothing for water. Direct counts:

  | Surface | Tones a patch | Shapes a patch |
  | --- | --- | --- |
  | Ours, east-west stream | 7.8 | 6.1 |
  | Ours, rill | 7.0 | 5.9 |
  | Ours, pool including the foam | 11.9 | 14.6 |
  | Ours, the foam alone | 1.8 | 3.8 |
  | Eastward 15, channels | 3.1 | 5.9 |
  | Eastward 13, canal | 11.5 | 11.9 |

  Our water bodies sit between the two Eastward references. The foam is the flattest surface in the asset.

## Findings

Coordinates are art px in `ground.png`, or in the scene for flow (the same frame of reference). The local crops behind each finding are named. Anyone can regenerate them from the boxes.

1. **Fault (ground): the plunge pool's foam is a flat two-tone white plate.**
   - Location: box (183, 877)-(301, 896). Crops `g_fall.png` (150-420 x 740-960 at 3x) and `z_pool.png` (170-330 x 860-945 at 5x).
   - What is wrong: the plate is 118 x 19 art px in exactly two tones, (245, 244, 235) and (230, 234, 236), split by a hard vertical seam at x≈253. The sheet is 53 px wide at its lip and 62 at its foot, so the foam reaches 27 px west and 34 px east of it, beyond the size guide's pool margin of 8 each side. It has a crisp elliptical outline, with no bubbles, broken clusters, eddies, spray, rings or shadow under its downstream edge. It covers the feet of the two boulders beside the fall.
   - Why it matters: this is the calibration's flat white bar (W3) laid on its side, and the brightest thing on the screen. `detail.fall_flat` cannot see it, because it only measures regions at least 2.2 times taller than wide.
   - Fix:
     - Keep the foam within the sheet's foot plus about 8 px each side, and no more than about 10 px deep.
     - Build it from broken clusters in 4 to 5 tones: white caps on the upper left of each clump, a pale blue-grey body, mid-blue gaps where the water shows through, and a darker blue band under its south (downstream) edge.
     - Break the outline into lobes and loose 2 px flecks that dissolve into the ripples (37's mist edge).
     - Add 2 px spray specks above the foot on both sides of the sheet.
     - Add two or three light ripple arcs spreading downstream from it.
     - Let the boulders keep their wet feet and ripple lines (5.3a).
     - Animate the churn in the flow frames (finding 3).

2. **Fault (flow): current marks run across the east-flowing stream.**
   - Location: in all 8 frames, about ten 1 px vertical marks a frame, 3 to 15 px long, at columns x 448, 492, 528, 556, 564, 596, 608, 628, 696 and 804, y 854-928. They step south from frame to frame (x 564 is at y 885 in frame 0 and y 897 in frame 1). Crop `stream_frames.png` (430-670 x 845-935, frames 0 to 3, at 3x).
   - What is wrong: the stream flows east, but these marks are vertical and drift south. They read as rain or scratches on the water, against "the current as 3 to 5 px lit streaks over their own shadow", lying with the flow (house-style 7, art-style density 3). Over the eight frames, 82 such marks stand against 404 horizontal ones. Frame 0 also has a four-armed cross sparkle at about (563, 892).
   - Fix: take each mark's orientation and drift from the local flow direction. Use horizontal 3 to 5 px streaks over a darker texel moving east in the east-west stream, and vertical ones only in the rill and on the sheet. Glints should come in pairs of 1 to 2 px, not crosses.

3. **Fault (flow): the plunge pool does not churn.**
   - Location: the foam box above. In frames 0 to 7 the flow draws 32, 0, 0, 0, 0, 0, 48 and 80 px over the foam, while the sheet changes by 46 to 160 px a frame.
   - What is wrong: the fall pours into a still white plate.
   - Fix: once finding 1 has redrawn the foam as clusters, move them in the frames. Clusters swell and break, flecks pop, and ripple arcs travel downstream. Keep frame 0 the reduced-motion still.

4. **Polish (ground): the crest is a lid.**
   - Location: box (213, 764)-(266, 770). Crop `z_crest.png` (195-300 x 730-800 at 6x).
   - What is wrong: the crest is a 53 x 6 rectangle with a ruler-straight top and square ends. It overhangs the channel above it (x 216-261) by 3 to 4 px on each side, onto the rock. The channel meets it along a straight dark navy row. The "irregular break" is a single 1-texel step in the white line.
   - Fix:
     - Make the lip exactly the channel's width.
     - Bow it 1 to 2 px downstream.
     - Lighten the channel's last 3 to 4 rows into a glassy tongue instead of a dark band.
     - Break the white crest into 2 to 3 runs of different lengths, with a gap or two where the darker sheet shows.

5. **Polish (ground): six static vertical streaks in the east-west stream.**
   - Location: (478, 856) 3 px long, (593, 878) 12 px, (732, 886) 12 px, (923, 896) 9 px, (905, 911) 6 px and (724, 938) 4 px. Crops `g_stream_mid.png` and `g_stream_east.png`.
   - What is wrong: the same fault as finding 2, baked into the ground (133 horizontal marks against these 6).
   - Fix: turn them horizontal or remove them.

6. **Polish (ground): the depth core in the rill is stamped, and geometric at the bend.**
   - Location: the deep thread repeats as the same checker-edged arrowhead pointing upstream three times between y 30 and y 200 (x 225-300). At the bend near (190-250, 565-595) it turns in a straight 45-degree cut and a square notch. Crops `g_rill_top.png` and `g_rill_bend.png`.
   - What is wrong: depth should lie with the flow in soft bands (house-style 7). Repeated identical shapes read as a stamp (`detail.repetition` in spirit).
   - Fix: use one continuous deep thread that hugs the outside of each bend, widens in the pool at the jog and narrows at riffles. Step its edge in 2 to 3 tones along the flow, with no repeated shape and no straight cuts.

7. **Polish (ground): a ruler-straight cut through the north rubble band.**
   - Location: the rill's east bank stays within x 260-262 from y 16 to y 128 (1.5 H), and its west bank sits at x 216 from y 16 to y 56. Crop `tile0.png` (0-480 x 0-576 at 2x).
   - What is wrong: two parallel straight sides read as a cut canal (art-faults rule 3: no perfect shapes in nature). `logic.water_straight` passes it because the run is axis-aligned and short.
   - Fix: wobble each bank 1 to 2 texels on the soft grid. Seat one or two stones from the rubble on the rims with wet feet. Add a turf tongue where the band meets the lawn.

## Per-part notes (ground)

- **Side and south rims (5.3a): pass.**
  - Sampled on the pool's west shore (row 900), the rill's west and east shores (row 650) and the stream's south shore (column 600). Each runs grass, one texel of (67, 43, 42) (earth_cool 1), one texel of (76, 134, 180) (RIM_LINE), then the body (51, 100, 153).
  - No earth face shows on any east, west or south shore. The turf tongues carry the same rim.
- **North banks (5.3): pass.**
  - East of the pool, either side of the bridge and on the stream's north lobes: a grass lip, a clod face of three browns with a near-black foot, a 1 px light waterline, then a dark band stepping back in three steps with checker between them. This is the shade fade 5.4 allows.
  - The rill's two jogs have short north faces (x 217-267 near y 550, and x 150-215 near y 168). They read correctly, if a little wedge-like at their west ends.
- **Stones in and at the water: pass.**
  - The north-bank clusters (x 610-653, y 852-875; x 745-790, y 880-903; x 873-910, y 877-895) have darker feet and a light ripple line under them.
  - The south-shore stones of the pool (x 195-305, y 915-945) stand on land, with the lit shallows behind them.
  - The rill's bank stones (y 160-220, 508-522 and 733-747) are seated the same way.
  - The two boulders beside the fall lose their feet under the foam (finding 1).
- **Stream above the fall: pass.** It is 46 px wide (x 216-261) against the sheet's 53. That is close, but the crest overhangs (finding 4).
- **Sheet: pass.** It swells from 53 to 62 px, wanders in 4 to 5 tones, has a darker east edge and falls in front of a wet rock recess.
- **Foam:** fail (finding 1).
- **Pool shape:** organic and on the soft grid. Its ripple dashes lie east-west.
- **Bridge (in the ground):** planks with grain, nail heads and lit edges, corner posts, ashlar abutments on dry ground at both ends, and a darker strip of water under each side. Pass.
- **Reeds:** in the shallows, off the bank outline. Pass.

## Tile log (ground, every region opened)

| Tile (art px) | View | Notes |
| --- | --- | --- |
| 0-480 x 0-576 | 2x | Rubble band, the rill's straight cut (7), stamped depth cores (6), two jogs with north faces and seated stones, canopy-shadow patches (unchanged, not water) |
| 480-960 x 0-576 | 1x | Rubble band and lawn, shadow patches; no water |
| 0-480 x 576-1152 | 2x | Rill bend (6), crest (4), sheet, foam (1), pool, bridge, path; lawn and shadows to the west |
| 480-960 x 576-1152 | 2x | Stream with north lobes, stones and reeds; vertical streaks (5); lawn |
| 0-480 x 1152-1728 | 1x | Lawn, path ring, shadow patches; no water |
| 480-960 x 1152-1728 | 1x | Lawn, path, shadow patches; no water |

The lawn, path and shadow patches were looked at for the water's sake only. They are outside this change, and their own fix-queue item (`woodland/ground`: `logic.scale`) stands.

## False positives

The detectors reported 0 findings on both assets, so **0 were rejected**. They also missed every finding above. Leads for the detectors:

- `detail.fall_flat` only measures tall regions, so it should gain a foam check: a white region at a fall's foot wider than the sheet plus 0.25 H, or in three tones or fewer.
- A flow check should compare the orientation of current marks with the channel's direction.

## Not checked

- **Motion:** judged from the eight frames composited one by one, not played at speed. The rim "lapping" (about 120 to 170 rim texels a frame lifted from (67, 43, 42) to (91, 63, 58)) may crawl in motion. Look at it when played.
- **Night and reduced motion:** not checked. Reduced motion holds frame 0, which carries the cross sparkle and the vertical marks of finding 2.
- **Phone:** no phone or device check.
- **Logic-auditor lead, not graded here:** the fall drops about 115 px between two lawns that read at the same level. Four ashlar blocks flank it, but no tier or face runs across the land on either side. ground-rules.md: "a waterfall happens only at a tier edge or a rock face".

## Round 2 (02c10a25)

A second independent detail-auditor run on the repaint that answers round 1 (commit 02c10a25, "Woodland water after the audit: plunge foam, current, churn, crest, rill, terrace", branch `claude-a/water-polish`, draft PR #434). This auditor did not paint it and did not write round 1.

**Verdicts: `woodland/ground` fail, `woodland/flow` pass.** Every round-1 finding is fixed in place, not moved. The ground fails on new work: the terrace's earth face is an even field of clods below the detail bar and far taller than any earth face in Eastward. The terrace also has three logic faults, listed separately below. The flow passes with two polish notes.

### What was reviewed

- `game/zones/woodland/art/ground.png` (960 x 1728, density 3, H = 74), sha256 `0f329bb1...`, and `game/zones/woodland/art/flow.png` (1584 x 832: 2 x 4 frames of 792 x 208 at (168, 756), 0.16 s a frame), sha256 `17ea57d4...`.
- `game/zones/woodland/walk.txt` (rows 64 to 79) and the plan's `terrace` and `water.animate` in `art/scenes/woodland.json`, with `screen.terrace` in `scripts/art/native/screen.py`.
- The painter's in-game capture `woodland_native_before_after_1x_round2.png` (spring and fall top, 4881fee7 against this round, 1x; local only).
- Each flow frame composited over the ground at its scene position, and the eight frames played in sequence as local GIFs (`flow_fall_3x.gif`, `flow_stream_3x.gif`), with contact sheets of the foam and the stream. Round 1's ground and flow (from 7895e96c) were diffed against these.

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**. The new **W15** (round 1's foam, frozen as `scripts/review/calibration/woodland_plunge_foam_4881fee7.png`) is **caught by `detail.foam_flat`**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as round 1.
- `npm run review:asset -- woodland/ground --record` and `npm run review:asset -- woodland/flow --record`: both PASS the detectors with 0 findings. The new `detail.foam_flat` passes the new foam.
- `python3 -m scripts.review.gate --check --zone woodland` after the verdicts: **ok** (flow passes, and ground stays in the seeded fix queue).
- Pixel samples and connected-component counts on the composited frames. The numbers below come from them.

### Eastward comparison (same character height)

Each shot was brought to native (13 by `core.to_native` at 3.00x; 15 and 37 box-averaged from 1920 x 1080 to 640 x 360) and scaled 1.37 with nearest neighbour. Ours went through the same JPEG pipe (3x nearest, JPEG q85, `to_native` 3.0) before `bands.patch_counts` (0.25 H patches). The crops stay local.

- **13, the farm ledge (native box about 115-250 x 240-275):** a low earth face about 35 px tall at our scale (0.5 H) under an overhanging grass lip. It is dark and calm, with a few clods, plants hanging over it and tufts at its foot. The stair is set in the face with lit treads and cheeks. Our terrace face is 96 px (1.3 H), 2.6 times that height. It is a dense mosaic of lit clods all the same size, with one fern on 680 px of face (`cmp_face_e13_vs_ours.png`).
- **37, the mist (native box 510-640 x 160-360):** soft, many-toned white that frays into checker and leaf flecks. Our new foam is a heap of clumps with lit caps that frays into flecks at its south edge, with spray specks and arcs beside it. It now reads as foam, not a plate (`e37_mist.png`, `z_fall.png`).
- **15, the channels (native box 440-640 x 0-220):** a calm, almost bare body with short light lines at the reeds' feet. Our stream's moving marks are now short east-west dashes over the depth bands, the same reading (`cmp_e15_stream.png`).
- **Counts** (tones and shapes a patch):

  | Surface | Tones | Shapes |
  | --- | --- | --- |
  | Ours, terrace face (440-940 x 776-848) | 21.6 | 38.7 |
  | Eastward 13, earth face | 27.6 | 67.0 |
  | Ours, pool and foam, round 2 (198-300 x 876-912) | 25.6 | 38.8 |
  | Ours, pool and foam, round 1 (same box) | 13.2 | 15.4 |
  | Ours, stream, round 2 / round 1 | 12.9 / 13.9 | 11.7 / 12.5 |

  The face reaches 78 % of Eastward's tones (the ramp bar is 85 %) and 58 % of its shapes. The pool's count doubled with the new foam.

### Round 1's findings, checked

1. **Plunge foam (fault): fixed.** The flat plate is gone. The foam spans x 213-270 (the sheet's foot is x 212-259, so it reaches 1 px west and 11 px east) and rows 885-896 (12 px). It is broken clumps with lit caps (245, 244, 235), a body (230, 234, 236), blue-grey undersides (182, 187, 206) and (146, 184, 197), pool blue between them, a mid band under the south edge, and flecks fraying into the pool. Spray specks sit on the water either side (x 202-207 and 272-280), none on the face. Ripple arcs lie below. The boulders beside the fall have their wet feet back. A polish note on the clumps is finding R2-4 below.
2. **Current marks across the stream (fault): fixed.** Over 8 frames the moving layer draws 149 horizontal dashes and 1 vertical in the stream (x 430-960, y 845-940); round 1 drew 227 and 68. The dashes that can be tracked from frame to frame step 2 to 9 px east, never south. Measured `flow_dir` along the stream lies within 23 degrees of east everywhere. No cross sparkle is left in any frame. The plus-shaped light patterns the search finds are lawn flowers, the same in every frame. A residue of one-texel specks is finding R2-5.
3. **The foam does not churn (fault): fixed.** Between consecutive frames 356 to 512 texels change in the foam box (x 200-290, y 880-905), in all eight steps, the loop's step back to frame 0 included. Clumps swell, merge and split, a small clump pops in and out on the east side, and the arcs travel. Frame 0 is the ground's still, so reduced motion shows the clumped foam, not a plate.
4. **The crest is a lid (polish): fixed, one polish point left.** The tongue spans x 216-264 against the channel's x 216-262, so it no longer overhangs onto the rock. The channel's last rows (760-766) are lightened. The white water sits in rows 767-770 in runs at x 218-231, 235-247 and 248-261, with the middle run starting a row lower (a 1 px bow). What is left is finding R2-3.
5. **Baked vertical streaks (polish): fixed.** The light marks in the stream body are now 86 horizontal, 1 vertical (3 px, at 620, 864) and 8 diagonal; round 1 had 92, 6 and 18. The six listed streaks are gone.
6. **Stamped arrowheads and the square notch in the rill (polish): fixed.** The deep tone is one continuous thread down the rill with a checker edge. It turns the bend near (190-250, 565-595) on a rounded inside, with no straight cut or notch (`rill_top_old_new.png`, `rill_mid_old_new.png`).
7. **Ruler-straight rill bank (polish): fixed.** From y 16 to 128 the west bank wanders over x 214-225 and the east bank over x 253-264, smoothly over 20 to 40 rows. Two rubble stones sit on the rims with wet feet. The banks keep the 5.3a rim.
8. **Logic lead (the fall between two lawns at one level): fixed east of the fall, not west.** East of the cascade the lawn north of y 768 is now a tier up, so the fall drops from a real edge there. West of the fall nothing has changed (logic finding L1).

### New findings

Coordinates are art px in `ground.png`, or in the scene for flow (the same frame of reference). The crops are local, in the auditor's scratchpad, and can be regenerated from the boxes.

**R2-1. Fault (ground): the terrace face is wallpaper, below the bar and out of Eastward's range.**
- Location: x 276-960, y 768-864. Crops `cmp_face_e13_vs_ours.png` and `z_facefoot.png` (440-960 x 760-920 at 3x).
- What is wrong: the plan's face is 32 world px, which is 96 art px (1.3 H, four cells), drawn by `softground.ledge` as an earth face. It is one even mosaic of rounded clods 10 to 15 px across, all the same size and spacing, with one fern on 680 px of face. It has no roots or vines worth the name, no larger stones and no tufts hanging from the lip. At game scale it reads as a cobbled wall. Eastward's earth ledge (13; eastward-edges 2.1 and 2.2) is 0.43 to 0.55 H and mostly calm, dark earth. A face 1.3 H tall is a rock cliff there (2.3). The face also makes 78 % of 13's tones and 58 % of its shapes. ground-rules.md 2 says a face is one tier high (two cells), so this one is two tiers tall (logic L4).
- Fix, one of:
  - **Rock face, recommended.** Draw it as `ledge(kind='rock')` per eastward-edges 2.3: under the lip, a two-value shade about 6 to 8 px deep, then a band of horizontal streaks about 9 px deep, then rounded boulders 12 to 25 px across, each lit at its top left with dark gaps between, and the odd larger boulder. It matches the grey rock the fall pours over. Break it with moss in the lower joints, two or three root or vine runs from the lip, tufts hanging from the lip in lumps, and fallen stones and weeds at the foot.
  - **Two tiers.** Split it into two 16-world-px faces with a grass step at least one cell deep between them. Make the fall a two-step cascade with a small ledge pool, and the log steps two flights.
  - Either way, no 100 px run of the face should repeat the same texture.

**R2-2. Polish (ground): the earth strips between the east ashlar blocks read as a twisted rope.**
- Location: x 294-345, y 799-810, and under the lower block at x 300-345, y 852-860. Crop `z_ashlar_gap.png` (280-360 x 780-870 at 6x).
- What is wrong: the terrace face shows through the gaps in the stack as a 10 px band of diagonal lit clods. Cut to a strip, they read as a rope or a twisted log between the stones.
- Fix: fill the joints with the rock's dark crevice tone and a little moss (the stack is masonry), or seat the blocks so they touch. Begin the face east of the stack at x 348.

**R2-3. Polish (ground): the crest's glassy tongue is a flat two-tone band with a straight top.**
- Location: x 214-266, y 760-766. Crop `z_crest.png` (195-300 x 730-800 at 7x).
- What is wrong: the tongue is two flat rectangles: pale over x 216-247 and mid over x 248-264. Row 760 is a ruler-straight top across the whole channel. The white runs below are separated by only 1 to 3 px of near-white, so at 1x the crest still reads as one straight line.
- Fix:
  - Fade the tongue up into the channel over 2 to 3 rows of checker, with its top edge stepping a row or two.
  - Draw two or three lit streaks in the channel converging on the lip.
  - Open the gaps between the white runs to 3 to 4 px of the sheet's mid blue.

**R2-4. Polish (ground): the foam's clumps are mostly two near-whites.**
- Location: x 213-270, y 885-896. Crop `foam_frames_8.png` (195-300 x 860-930 at 4x, frames 0 to 7).
- What is wrong: of 542 light texels, 478 are the two near-whites and 64 are the blue-greys. The clumps are rounded puffs of similar size, so they read a little like cotton balls in a row.
- Fix: shade the lower right third of each clump in the blue-greys, and vary the clump sizes more (one large heap under the sheet's middle, smaller ones at its sides).

**R2-5. Polish (flow): one-texel specks in dotted trails across the current.**
- Location: the stream, x 430-960, y 845-940, every frame. Most trails are near x 680-720 and 900-950. Crops `specks_234.png` (the specks of frames 2 to 4, one colour each, at 3x) and `z_specks_east_f1to5.png`.
- What is wrong: besides the dashes, each frame lifts about 100 to 140 single texels one tone (round 1 had as many; it counted only the longer marks). They lie in dotted lines at 30 to 90 degrees to the current, and from frame to frame they step about 3 px south as often as east: against a shuffled-frame baseline, the south bias of their nearest-neighbour shifts doubles. At 2x they read as a faint shimmer.
- Cause: `animate.water` builds its lane coordinates as `u = (x*fx + y*fy) // 256` and `v = (-x*fy + y*fx) // 256` from absolute x and y. Where `flow_dir` turns, at the lobes, a 1/256 change in direction moves `v` by x/256, which is about 3 texels at x 700 to 900. The iso-`v` lanes there run nearly north-south and break into specks.
- Fix: build the lanes from coordinates that follow the channel:
  - `v` as the distance across the channel (from the north bank), and `u` as the distance along it (or plain x for a channel within 30 degrees of east, y for one within 30 degrees of south);
  - or `u` and `v` per 24 px cell, relative to the cell's origin, with the direction quantised per cell and blended at its edges.
  - Then drop any lifted texel with no lifted neighbour along the flow.

**R2-6. Polish (flow, predates round 1): the rill and the channel above the fall do not move.**
- Location: x 150-330, y 0-756. The plan's `water.animate` box is [0, 252, 320, 330] in world px.
- What is wrong: in the fall-top view (the capture's lower right panel) all the water on screen is still except the sheet's top. The fall pours from a frozen channel.
- Fix: extend the animate box north to cover the rill (y 0), so its marks run south. The strip grows to about 792 x 964 a frame, so weigh that against the texture budget. Or add a separate small strip for the rill.

### Logic (reported separately, as in round 1)

**L1. Fault: no tier west of the fall.**
- Location: x 0-215, y 640-880. Crops `z_west.png` (0-280 x 600-960 at 4x) and `cap_west_3x.png` (the capture).
- What is wrong: `screen.terrace` raises everything north of y 768 but paints the original ground back west of x 276 (`cv[rim:, :x0] = under`). So the rill's west bank and the pool's west shore are one continuous lawn, with the same tone and tufts, and the canopy-shadow patches lie across the rim's row as on flat ground. The west ashlar pair (x 120-200, y 795-860) and a boulder stand on that lawn, a wall that ends in the grass with the same ground in front of and behind it. On the west side the fall still drops 120 px between two lawns at one level. `ledge` would draw the side wall that eastward-edges asks for where raised ground ends ("raised ground shows its side walls wherever it ends west or east"), but it is painted over. In the game the oak crowns hide x < about 150. The lawn between the west blocks and the crowns (about x 140-215, y 700-870) stays in view and shows the two levels joining.
- Fix: carry the face west from the fall to the zone edge (x 0, rim y 768), behind the oak grove: crowns over the rim, trunks seated on one tier, the boulder heap at the foot. Block walk rows 64 to 71 for columns 0 to 22. Rows 64 and 65 are open at columns 0 to 12 today. A west side wall cannot end the tier, because the rill runs on the upper tier, so the upper tier must reach west of it.

**L2. Fault: the river's old north lobes cut up into the face, and a turf lip is left at its foot.**
- Location: x 476-625, y 838-864, and the lawn strip at x 745-905, y 864-895. Crops `z_lobe_face.png` (470-660 x 800-890 at 5x) and `z_facefoot.png`.
- What is wrong: the face is drawn over the old north bank, and the water put back over it (`cv[wm] = under[wm]`). So the face's foot runs at three levels: about y 848 over the lobes, 864 at the steps and 895 behind the lawn strip in the east. Over the lobes the old bank's green turf lip and its stones sit at the bottom of the face, a lip where only a wet foot belongs. Water standing higher up the face than the lawn beside it reads as water above the lower ground. ground-rules 1 says a face is as tall as the height difference it divides.
- Fix: one foot line. Either fill the lobes north of y 864 (the face's foot runs on, the river's north bank moves south to it), or carry the face down into the lobes so its foot meets the water as a wet foot (the dark band, wet stones, the 5.3 light waterline) with no turf lip. Drop the old bank's turf and stones under the face in either case.

**L3. Fault: the log steps land on the bridge, which has lost its north abutment.**
- Location: x 348-420, y 766-870. Crop `z_steps.png` (320-520 x 730-960 at 5x).
- What is wrong: the bottom tread ends at y 859, and the bridge's planks begin at y 866 on a 2 to 6 px strip of turf at the face's foot. The bridge's south end keeps its ashlar abutments, its north end has none. The stair's foot does not land on the path (eastward-edges 6.1, ground-rules 1), and the bridge's north end barely stands on dry ground (art-faults rule 7).
- Fix: a landing at least one cell deep (24 art px) between the stair's foot and the bridge, with the bridge's north abutment and corner posts on it, like the south pair. Get it by moving the rim one cell north at the steps (the stair in a spur, eastward-edges 6.1), or by a lower face (R2-1's two-tier option puts the first foot at y 816).

**L4. Fault (rules): the face is two tiers tall.**
- What is wrong: `terrace.face` is 32 world px, and ground-rules 2 gives a face one tier (two cells, 16 world px). This is the same fault as R2-1, seen from the rules. A rock face, the recommended fix, is what the rule allows for a drop this high ("a waterfall happens only at a tier edge or a rock face").

Walk check:
- `walk.txt` blocks the face rows 64 to 71 from column 23 (x 92) east, and the steps (columns 29 to 34) and the bridge (rows 72 to 77, columns 30 to 33) stay open. The path runs through.
- The lawn strip at the face's foot (rows 72 to 73, columns 62 to 76) is walkable but cut off from everything. It is harmless, and goes away with L2.

### Per-part notes (ground)

- **Foam, spray, arcs:** pass (above). Polish R2-4.
- **Crest and lip:** pass. Polish R2-3.
- **Sheet:** unchanged, pass.
- **Stream body and rims:** the 5.3a rims hold on the side and south shores. The baked marks lie east-west. Pass.
- **Rill:** the core, bend, banks and rim stones pass. Its north faces at the two jogs are unchanged.
- **Terrace lip:** a grass lip in lumps with a dark under-row. It reads, but has few hanging tufts (R2-1).
- **Terrace face:** fail (R2-1).
- **Log steps:** six plank treads with dark risers, the head 2 px above the rim, in a recess with the ashlar stack as the west cheek. They read as steps. Their foot is logic L3.
- **East ashlar stack:** the joints read as rope (R2-2).
- **Bridge:** planks, nails and posts as before. The north abutment is missing (L3).

### Tile log (ground, every region opened against round 1)

| Tile (art px) | View | Notes |
| --- | --- | --- |
| 0-480 x 0-576 | 1x side by side, rill at 3x | Rill core, bend, wobbling banks, rim stones and a reed clump at the rubble; jog faces unchanged; lawn and shadow patches unchanged |
| 480-960 x 0-576 | 1x | 144 texels changed (lawn dressing, x 869-940, y 499-537); no water |
| 0-480 x 576-1152 | 1x, 2x, crops at 4x to 7x | Crest (R2-3), sheet, foam (R2-4), pool, ashlar stacks (R2-2), steps and bridge (L3), level lawn west of the fall (L1) |
| 480-960 x 576-1152 | 1x, 2x, 3x and 5x | Terrace lip and face (R2-1, L4), lobes into the face (L2), lawn strip at the foot, stream, stones and reeds |
| 0-480 x 1152-1728 | 1x | Lawn dressing reshuffled (tufts, flowers); path ring unchanged; no water |
| 480-960 x 1152-1728 | 1x | Lawn dressing reshuffled; path unchanged; no water |

The lower tiles' changes (5057 and 11355 texels) are tufts and flowers that moved when the generator's random draws shifted. They are the same kind and density as before.

### False positives

The detectors reported 0 findings on both assets, so **0 were rejected**. They missed R2-1 to R2-6 and L1 to L4. Leads for the detectors:

- A face check: the height of a `ledge` face against `kind` (earth over 0.6 H), and the face's foot running at more than one level along a single rim.
- A tier-end check: a raised `top` mask whose face stops at a column while the lawn on both sides of the rim line keeps one tone (the side wall missing).
- In `animate.water`'s test: the share of moving texels that are lone single texels, and the orientation of speck chains against `flow_dir`.

### Not checked

- **Motion at speed on a device:** the frames were played as GIFs and contact sheets on a desktop. There was no phone or native check.
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0 only. It shows the clumped foam, the dashes and a static share of the R2-5 specks.
- **The kit's waterfall pieces and strips** (`game/kit/props/art/waterfall_*`) and the kitlab bakes, which share `rocks.plunge`: outside this gate. They should be gated on their own records.
- **Matt's ruling on spray** (2 Nov, none on the face) is followed. Whether he wants the west grove on the upper or the lower tier for L1 is his call.
