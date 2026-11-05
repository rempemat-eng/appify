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

## Round 3 (b2410e5e)

A third independent detail-auditor run on the repaint that answers round 2: commits 95a7a6f7, c206e022 and b2410e5e on `claude-a/water-polish` (draft PR #434). This auditor did not paint it and did not write rounds 1 or 2.

**Verdicts: `woodland/ground` fail, `woodland/flow` pass.** Every round-2 art finding is fixed, and so are logic L1, L2 and L4. L3 is half fixed. The ground fails on one new fault: a boulder now sits over the channel just above the fall's lip (R3-1). The fix is small. The flow passes. Its strip is too heavy for a phone (R3-6), which is reported but not graded as art.

### The rule applied to a 32-world-px face

A single rock face 32 world px tall (96 art px, 1.3 H) is acceptable as one tier step:
- eastward-edges 2.1 gives two face heights: an earth ledge of 12 to 16, and a rock cliff of 32 and up.
- world-rules 3.2 lists 32 as a ledge between walkable tiers.
- world-rules 7.2 asks for falls to be stacked in tiers only when they drop more than 48.
- ground-rules 1 says "a face is as tall as the height difference it divides".

The sentence in ground-rules 2, "A face is one tier high (two cells), the height a face strip draws", describes the kit's two-cell face strip. It does not cap a painted rock face. So round 2's L4 read it too strictly. ground-rules 2 should say so, to stop the next reviewer from tripping on it. The face must be rock, never earth, and this one is.

### What was reviewed

- `game/zones/woodland/art/ground.png` (960 x 1728, sha256 `5961568d...`).
- `game/zones/woodland/art/flow.png`: 1576 x 3736, 2 x 4 frames of 788 x 934, placed at (172, 0), at 0.16 s a frame. Its sha256 is `b618dd08...`.
- The plan's `terrace`, `water.animate`, `rock.heap` and `objects`, plus `walk.txt` rows 59 to 79.
- `screen.terrace`, `rocks.fall`, `rocks.plunge`, `animate.water` and the bake change in `kit/bake.py`.
- The painter's capture `woodland_native_before_after_1x_round3.png`.
- `game/zones/kitlab_tiers/ground_baked.png`, before and after.
- Each flow frame was composited over the ground. The frames were played as local GIFs (fall top at 3x, rill and stream at 2x, foam at 5x) and laid out as contact sheets.

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as rounds 1 and 2. `calibration_results.json` was reverted afterwards.
- `npm run review:asset -- woodland/ground --record` and `-- woodland/flow --record`: both pass the detectors with 0 findings. They missed R3-1 to R3-5.
- The flow sheet is about 94 MP (PIL warns that it may be a decompression bomb). It is almost all empty grey, because the moving texels are sparse. The flow was therefore judged on the composites, not on the sheet.
- `python3 -m scripts.review.ground_rules --check`: woodland ok.
- `python3 -m scripts.review.gate --check --zone woodland` after the verdicts: ok. The ground stays in the seeded fix queue.

### Eastward comparison (same character height)

Each shot was brought to native: 12 and 13 by `core.to_native` at 3.00x, and 15 and 37 box-averaged to 640 x 360. Each was then scaled 1.37x with nearest neighbour. Ours went through `bands.jpeg_roundtrip` (3x, q85) before `bands.patch_counts` (0.25 H patches). The crops stay local.

- **12, the rock cliff (native box 40-80 x 40-140), against our face (560-640 x 760-900).** Crop: `cmp_e12_vs_face_3x.png`.
  - The bands now match: lip, under-lip shade, a band of horizontal slabs, then boulders lit top left with dark gaps.
  - Eastward's boulders are calmer, lower in contrast and larger. The biggest is about 35 art px at our scale; ours are 14 to 25 px.
  - Counts: the face has 23.6 tones and 39.9 shapes a patch (west part: 25.9 and 39.9). 12's cliff has 20.8 and 50.3. So the face reaches 113 % of the tones and 79 % of the shapes. Round 2's earth face had 78 % and 58 % of 13's.
- **13, the farm ledge (native box 100-200 x 230-290).** Crop: `cmp_e13_vs_face_3x.png`.
  - 13's earth ledge is about 0.5 H. That is the earth limit our face no longer has to meet, because it is now rock.
  - In 13 a bush or boulder crosses the rim every one to two tiles. Our east face has one fern and five vines over 540 px, which is the low end of eastward-edges 8.1.
- **15, the channels (water-only box 480-560 x 0-90).** Crop: `cmp_e15_vs_stream_3x.png`.
  - 15's body is almost bare (10.8 tones and 21.0 shapes, mostly JPEG grain).
  - Our stream has 9.3 and 6.0, with depth bands and short east-west dashes. That is the same calm reading.
- **37, the mist (native box 540-640 x 190-320).** Crop: `cmp_e37_vs_foam_3x.png`.
  - Our foam heap with its frayed edge reads as foam, not a plate.
  - The pool and foam box has 30.7 tones and 41.3 shapes, against 37's mist at 26.4 and 68.4.

### Round 2's findings, checked

- **R2-1 and L4, the terrace face: fixed.** Crops: `z_west_4x.png`, `w_east_3x.png`, `z_face_7x.png`, `z_lip_10x.png`.
  - The face is `ledge(kind='rock')` in stone.
  - Under a lumpy grass lip there is a 1 px dark line, then about 7 px of under-lip shade cut into horizontal slabs with lit top edges (rows 773-780). Below that is a band of small flat stones (about 781-800).
  - Then come boulders 14 to 25 px across, each lit top left with a mid body and a dark underside: (181,168,151), (152,142,133), (142,135,130), (112,103,106) and (81,72,80), with gaps of (45,33,47).
  - Vines hang from the lip at about x 70, 575, 640, 700, 885 and 932. Ferns grow in the face. Fallen boulders lie on the lower lawn at the west foot.
  - No 100 px run repeats. Residual polish is R3-2 to R3-4.
- **L1, no tier west of the fall: fixed.** The face runs from x 0 to the cascade, and `walk.txt` blocks rows 64 to 71 from column 0. The west grove is split: holly_b and bush_b stand on the upper tier with their feet at y 248 world, one cell back from the rim, and the oaks wood-16, tree-3 and wood-17 stand below with their feet at 296 to 312. The oaks' crowns overlap the face, as plants over an edge should.
- **L2, three foot levels: fixed.** The river's lobe, cut and widening are gone. East of the cascade the foot is one line at y 862-870. Wet rock runs down to a 1 px light waterline (76,134,180), then the dark band (14,32,88) and the body. There is no turf lip and no old bank. West of the fall the foot lands on the lower lawn at about y 860, with weeds and fallen stones. Polish on the wet foot is R3-4.
- **L3, the stair lands on the bridge: half fixed.** See R3-5.
  - The bridge now has a north abutment, a lit cap row at y 846-850 with blocks either side, and corner posts.
  - The plan's landing (y 840-870) is real ground, but the deck is drawn from y 850. So the deck covers 23 px of dry landing, and only 6 px of path shows between the last tread (foot at y 839) and the abutment.
  - `walk.txt` keeps the stair (columns 29 to 34) and the bridge (columns 30 to 33) open.
- **R2-2, the joints between the ashlar blocks: fixed.** They are now dark crevice stone with moss, not a rope (`z_ashlar_6x.png`).
- **R2-3, the crest's tongue: fixed.**
  - The tongue's top steps between rows 760 and 762, over a checker fade.
  - Two 1 px lit streaks (x 231-232 and x 243) run down to the lip.
  - The white water breaks at rows 767-770 into runs at x 220-237 and 243-255, with a 5 px gap of mid blue.
  - Left over: the tongue is still two flat fields, pale over x 216-242 and mid over x 243-258. This is too small to count.
  - Crops: `z_crest_8x.png` and `z_crest_r2_8x.png`.
- **R2-4, the foam's clumps: fixed.**
  - There is now one large heap under the sheet's middle, with smaller clumps at the sides.
  - Of 759 light texels in the foam, 183 are blue-greys (24 %), up from 12 % in round 2. They sit on the lower right of the clumps.
  - The foam stays within x 210-266, against a sheet foot of 214-258. In the frames it swells, splits and pops. Crop: `sheet_foam_4x.png`.
- **R2-5, the specks across the current: fixed.**
  - `animate.water` now snaps the lanes to eight directions and drops a lifted texel with no neighbour along the flow.
  - Lone moving texels fall from 151-183 a frame to 2-14. All but three lie in the foam and spray box (y 884-906), where flecks are wanted. The other three are on the sheet.
  - Every mark of two or more texels in the stream (x ≥ 430, y 845-945) is horizontal: 21 to 25 a frame, none vertical or diagonal. Tracked marks step 8 px east a frame.
  - Crop: `sheet_stream_3x.png`.
- **R2-6, the rill does not move: fixed.**
  - The animate box is now [0, 0, 320, 330].
  - The rill's dashes run south in lanes 9 to 12 px long and step 12 px a frame. At the jogs they turn diagonal.
  - Between frames, 556 to 584 texels change in the rill.
  - Crops: `sheet_rill_2x.png` and `sheet_crest_4x.png`.

### New findings

Coordinates are art px in `ground.png`, or in the scene for flow (the same frame of reference). The crops are local.

**R3-1. Fault (ground): a boulder over the channel just above the lip.**
- Location: x 243-266, y 744-762. Crops `z_crest_8x.png` and `z_lipstone_r2_vs_r3.png` (232-275 x 736-772 at 12x, round 2 beside round 3).
- What is wrong:
  - A mossy two-part boulder and a loose flat stone at its west end cover the east third of the channel from row 744 down to the tongue. At row 743 the water still reaches x 265.
  - The channel narrows from 47 to about 31 px (x 219-249), then reopens under the rock to x 260 at rows 760-766, so the water seems to run out from under a stone into a 43 px sheet.
  - The stone has no wet contact: no darker foot, no light ripple line and no shade on the water (eastward-edges 5.3a).
  - ground-rules 2 allows nothing above the rim over the stream (Matt, 2 Nov: "the waterfall overlaps in an unrealistic way on the top bit").
  - It is new in this round. Round 2 had clear water there. It sits on the most-viewed spot of the fall-top view.
  - I did not trace which step lays it. Candidates are the cascade's narrowed face ([68, 93] world, was [62, 98]) with the heap's lip slab (`rock.heap` at [80, 262]), or a seated bank stone.
- Fix:
  - Keep the channel clear down to the lip, its banks wobbling at x 216-219 and 263-267 as above row 743.
  - Set any stone at the lip wholly on the east bank (x ≥ 268, foot on grass or rock).
  - If a stone must stand in the water, lay it through `softground.seat_stones` so it gets a wet contact, and keep the sheet as wide as the channel at the lip.

**R3-2. Polish (ground): moss hats and boulders of one size.**
- Location: the whole face, x 0-960, y 790-860. Crops `z_face_7x.png` and `w_east_3x.png`.
- What is wrong:
  - About 35 boulders carry the same two-tone lime cap with a drip fringe on their crowns. The fix in R2-1 and 5.3b asked for "moss in the lower joints". Caps on crowns echo calibration's "boulders with moss hats".
  - The boulders are all 14 to 25 px, with no larger boulder (2.3: "the odd larger boulder"; 12's biggest is about 35 px at our scale). Over 960 px this reads as an even field.
- Fix:
  - Move most of the moss into the dark joints and onto the lower, shaded sides, in the leaf_cool ramp, in 3 to 6 px tufts of different shapes.
  - Keep caps on at most one boulder in five.
  - Add one boulder of 30 to 40 px every 150 to 250 px.
  - Add one or two more ferns or a small bush crossing the rim east of the bridge (8.1).

**R3-3. Polish (ground): blades hang from the lip.**
- Location: the lip, y 772-780. There are 37 thin green strokes 3 or more px long in rows 774-800, besides the vines. Crop `z_lip_10x.png`.
- What is wrong: olive grass blades 2 to 5 px long hang over the dark under-lip line. eastward-edges 3.1 (Matt, 21 Oct) asks for turf lips without teeth. Round 2's fix line "tufts hanging from the lip" was wrong on this point, and is withdrawn.
- Fix: a clean lip (`ledge(..., tufts=0)` or blades only standing up). Keep the lumps and the vines.

**R3-4. Polish (ground): a comb on the wet foot.**
- Location: x 300-960, y 861-863, and the flat wet-rock band at y 864-870. Crops `z_foot_10x.png` and `z_ashlar_6x.png` (the slab under the stack at x 315-347, y 863-873).
- What is wrong:
  - `terrace` recolours the ledge's foot weeds into rock tones (`wee`), so the blades remain as a row of 1 px vertical ticks in alternating rock tones. That is a stripe along the foot (2.4: marks run across, never down).
  - Below it the wet rock is a mostly flat two-tone band.
- Fix:
  - Clear the weed blades to the plain wet-rock tone before recolouring, or remove them instead of recolouring.
  - Break the band with 2 to 4 px wet stones, each with a lit top (3.2: "pebbles and the odd stone").

**R3-5. Logic polish (L3 left over): the deck covers the landing.**
- Location: x 355-415, y 839-873. Crops `z_steps_6x.png` and `z_steps_r2_6x.png`.
- What is wrong: the deck and its abutment start at y 846-850, where the landing begins, not at the water (y 873). The stair seems to step straight onto the bridge, with 6 px of path between. The south end is drawn correctly, with its abutment at the shore.
- Fix: start the north abutment at the water's north edge (about y 866-873), and leave y 840-866 as open path with the stair's foot on it.

**R3-6. Budget (flow, not graded as art).**
- What is wrong:
  - The strip is 1576 x 3736 RGBA, imported lossless (`compress/mode=0`), so it takes about 23.6 MB of texture memory decoded.
  - Only 8,520 of its 5.9 M texels are not transparent (0.14 %), about 550 to 1,200 a frame. The ground under it is 960 x 1728.
  - Its height is under 4096, so phones can load it. But on a phone that is 3.5 times the ground's own texture memory, spent on about 1,000 moving texels a frame.
  - Judgment: too heavy for a phone.
- Fix: split it into a rill strip (about x 150-300, y 0-770) and a stream-and-pool strip (x 172-960, y 740-934), each cropped to its water. Together that is about 2.1 M texels, about 8 MB. A scrolling shader or a palette-indexed strip would cut it further.

**Flow polish (no number):** the rill's dashes run in six fixed columns (x 188, 200, 212, 220, 240 and 248) at a 96 px period, in step, which reads slightly mechanical at 2x. Phase each lane's period by a hash of its lane index.

### The kit: kitlab_tiers' pool under the fall

**K3-1. Fault (kit bake), more than the painter's "minor".**
- Location: `game/zones/kitlab_tiers/ground_baked.png`, x 615-685, y 326-360. Crops `kt_r2_vs_r3.png` (570-740 x 230-400 at 5x) and `kt_notch_10x.png`.
- What is wrong:
  - The new bake turned the pool's north bank into water only below row 337, in a box x 621-667 by y 338-347 with straight vertical sides and square corners.
  - The rows under the sheet's foot (336-337, the bank's grass lip and rim line) are unchanged. So the white water still lands on a strip of turf and earth, and the foam sits in a separate box below it.
  - A column of bank earth (the stone c206e022 keeps, x 629-632) stands inside the box.
  - The box's sides carry no 5.3a rim, and the box breaks the soft grid's rounded corners (1.6) and art-faults rule 3.
  - Round 2's bake had the same turf strip under the sheet, so the fall has never reached its pool here.
- Fix:
  - Start the conversion at the sheet's foot row, not at `r1` in the water mask, so the lip and rim rows under the sheet's columns become water too.
  - Round the inlet's corners to 2 to 3 texels, and run the 5.3a rim (earth_cool 1, RIM_LINE) down both sides.
  - Move or drop the bank stone, so it does not stand as a pillar in the plunge.

### Per-part notes (ground)

- **Upper lawn and lip:** the field is kept. The lip is in lumps with a dark line under it. Polish R3-3.
- **Face:** pass, with polish R3-2. It is rock per 2.3, from x 0 to x 960, behind the cascade, the ashlar stack and the steps.
- **Cascade face and sheet:** the sheet is x 216-258 and falls in front of wet rock. Pass.
- **Crest and tongue:** pass, except for the stone R3-1.
- **Foam, spray and arcs:** pass.
- **East ashlar stack:** crevice joints. Pass.
- **Log steps:** five treads with dark risers, the head flush at y 766. Treads 1 and 2 are 3 px narrower on the west, where the stack's shadow falls. That is fine. The foot is R3-5.
- **Bridge:** planks, nails, posts and both abutments. The north end is R3-5.
- **Foot and river:** one line with a light waterline. Polish R3-4.
- **West foot:** the lower lawn, with fallen boulders and weeds. Pass.
- **Rill, banks and bank stones:** unchanged from round 2 apart from re-seating. Pass.

### Tile log (ground, every region opened against round 2)

| Tile (art px) | View | Notes |
| --- | --- | --- |
| 0-480 x 0-576 | 1x, rill at 2x across 8 frames | 8818 texels changed. The rill, its two jogs with north faces, bank stones with wet feet and the rubble band all read; the rill now moves |
| 480-960 x 0-576 | 1x | 526 texels changed (lawn dressing); no water |
| 0-480 x 576-1152 | 1x, 3x, crops at 4x to 12x | Upper lawn and lip (R3-3); the face from x 0 (R3-2); the west foot on the lawn with fallen stones; cascade, crest (R3-1), sheet, foam; ashlar stack; steps and landing (R3-5); bridge; pool |
| 480-960 x 576-1152 | 1x, 3x, 7x, 10x | The face, with vines and a fern (R3-2); the one-line wet foot (R3-4); the stream, its rims, stones and reeds |
| 0-480 x 1152-1728 | 1x, diff map | 6430 texels: tufts and flowers reshuffled; no water |
| 480-960 x 1152-1728 | 1x, diff map | 11427 texels: the same; the path is unchanged |

### False positives

The detectors reported 0 findings on both assets, so **0 were rejected**. They missed R3-1 to R3-5 and K3-1. Leads for the detectors:

- A lip check: any non-water texel inside the channel's columns within 24 px above a fall's rim, where the rows above were water.
- In `test_kit.WaterBanks`: under a fall, the rows between the sheet's foot and the pool must be water, and a water inlet with straight sides and square corners should fail.

### Not checked

- **Motion at speed on a device:** the frames were played as GIFs and contact sheets on a desktop. There was no phone or native check, and no measurement of texture memory on a device (R3-6 is arithmetic).
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0 only. It is the ground plus 541 texels of dashes, with no lone specks.
- **The kit's waterfall pieces and strips** (`game/kit/props/art/waterfall_*`, changed in this range): not gated here, apart from the kitlab_tiers bake above. They need their own records.
- **Whether the lower-tier oaks' crowns should hide more of the west face** is a composition call for Matt.

## Round 4 (3e19c29e)

A fourth independent detail-auditor run, on the commit that answers round 3 (3e19c29e, "Woodland water, review round 3: clear lip, face polish, landing, two flow strips, kit inlet", branch `claude-a/water-polish`, draft PR #434). This auditor did not paint it and did not write rounds 1 to 3. It also gates, for the first time, the eight kit waterfall pieces recorded in `art/catalogue/kit/`.

**Verdicts:**

| Asset | Detectors | Verdict | Why |
| --- | --- | --- | --- |
| `woodland/ground` | pass, 0 findings | **fail** | The art passes. It fails on L4-1: R3-5 is not fixed. The bridge is unchanged from round 3, and the landing is 5 world px of open path, not one cell. |
| `woodland/flow` | pass, 0 findings | **fail** | F4-1: the stream's moving marks run over the bridge deck in every frame, including the reduced-motion still. |
| `woodland/flow_rill` | pass, 0 findings | **pass** | The lanes now have their own phases. A polish note shares F4-1's cause. |
| `kit/waterfall_1` to `_4`, and `_1_tall` to `_4_tall` | 7 fail (`detail.bar`), `waterfall_4` passes | **fail, all eight** | They were graded on the water criteria, not the prop band, and fail them: K4-1 to K4-3. |

`python3 -m scripts.review.gate --check` now **refuses `woodland/flow`**, which fails and is not in the fix queue. So `npm run check:kit`, and with it `npm run verify`, fail on this branch until F4-1 is fixed and re-reviewed. The ground stays in the seeded fix queue. The kit pieces are not zone art under `game/zones/*/art`, so the gate does not read their verdicts.

### What was reviewed

- `game/zones/woodland/art/ground.png` (960 x 1728, density 3, H = 74).
- `game/zones/woodland/art/flow.png`: 1576 x 712, 2 x 4 frames of 788 x 178, placed at (172, 756).
- `game/zones/woodland/art/flow_rill.png`: 180 x 3024, 2 x 4 frames of 90 x 756, placed at (174, 0).
- `kit.json` `flow` and `flows`, the `Water` and `WaterRill` nodes in `woodland_base.tscn`, and `world/flow_anim.gd`.
- `game/kit/props/art/waterfall_{1..4}{,_tall}.png`, with their `_flow.png` strips placed by `game/kit/props/index.json` (8 frames at 10 fps).
- `game/zones/kitlab_tiers/ground_baked.png`.
- Code diffs: `screen.terrace`, `screen.terrain` (`clear`, `wspan`), `animate.water` (`thin`), `zone.py`, `assets.py` and the new tests in `test_kit.WaterBanks`.
- The plan's `terrace`, `water.strips` and `bridge`, and `walk.txt` rows 62 to 79.
- The painter's capture `woodland_native_before_after_1x_round4.png`.
- Round 3's ground, flow and kitlab_tiers bake (from b2410e5e), diffed against this round.

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**, W15 included. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as rounds 1 to 3. `calibration_results.json` was reverted afterwards.
- `npm run review:asset -- woodland/ground woodland/flow woodland/flow_rill --record`: all three pass with 0 findings. The detectors missed F4-1, L4-1 and L4-2.
- The kit pieces went through the same `assets.review` with kind `waterfall` and biome `woodland`, with `record` and the reviewer field set. The sha256 of each matches the painter's record. The detectors give:

  | Piece | Detail bar against the prop band | Findings |
  | --- | --- | --- |
  | `waterfall_1` | 0.31 | `detail.bar` fault; `detail.outline` polish |
  | `waterfall_1_tall` | 0.20 | `detail.bar` fault; `detail.outline` polish |
  | `waterfall_2` | 0.40 | `detail.bar` fault; `detail.outline` and `detail.light` polish |
  | `waterfall_2_tall` | 0.34 | `detail.bar` fault; `detail.outline` and `detail.light` polish |
  | `waterfall_3` | 0.40 | `detail.bar` fault; `detail.outline` polish |
  | `waterfall_3_tall` | 0.37 | `detail.bar` fault; `detail.outline` polish |
  | `waterfall_4` | 0.48 | three polish findings, so it passes |
  | `waterfall_4_tall` | 0.42 | `detail.bar` fault; `detail.outline` and `detail.light` polish |

- `python3 -m unittest scripts.art.kit.test_kit.WaterBanks`: 14 tests, OK. This includes `test_nothing_stands_over_the_woodlands_channel_above_its_lip`, `test_a_fall_lands_in_its_pool` and `test_flow_strips_keep_to_the_phone_budget`.
- Both strips' frames were composited over the ground at their `kit.json` rects. The composites were played as local GIFs (the rill at 2x, the stream and pool at 2x, the fall at 5x) and laid out as contact sheets. The kit pieces' frames were composited the same way (`waterfall_2` and `waterfall_4_tall` at 4x).
- Connected-component counts and column profiles on those composites. The numbers below come from them.

### Eastward comparison (same character height)

Each shot was brought to native: 12 and 13 by `core.to_native` at 3.00x, and 15 and 37 box-averaged from 1920 x 1080 to 640 x 360. Each was then scaled 1.37x with nearest neighbour. Ours went through `bands.jpeg_roundtrip` (the detector's own pipe) before `bands.patch_counts` (0.25 H patches of 18 px). The crops are local and not committed.

- **12, the rock cliff (native 40-100 x 40-140), against the face at x 640-722, y 760-897**, which holds one of the new larger boulders. Crop: `cmp_e12_vs_face_bigboulder_3x.png`.
  - Eastward's largest boulder is one calm form, lit at its top left, with a dark underside.
  - Our new larger boulders are the right size, 30 to 40 px. Each reads as three or four cracked lobes, so a heap of smaller stones (G4-1).
- **13, the canal (native 40-140 x 300-360), against the wet foot at x 480-617, y 840-922.** Crop: `cmp_e13_canal_vs_foot_3x.png`. Both show a bank, a 1 px light waterline and a darker band below it. They match.
- **15, the channels (native 470-560 x 0-90), against the stream at x 560-683, y 850-973, frame 0.** Crop: `cmp_e15_vs_stream_3x.png`. Both are calm bodies. Ours adds depth bands and short east-west dashes.
- **37, the white water (native 560-640 x 170-300), against the woodland fall and against `kit/waterfall_2`.** Crops: `cmp_e37_mist_vs_woodfall_3x.png` and `cmp_e37_mist_vs_kit2_3x.png`.
  - Eastward's white water is soft and many-toned, with no hard edge.
  - The woodland sheet has broken 2 to 4 px streaks in 4 to 5 tones.
  - The kit sheet reads as a hard-edged block of flat columns.
- **Counts** (tones and shapes a patch):

  | Surface | Tones | Shapes |
  | --- | --- | --- |
  | Eastward 13, canal water (native 20-200 x 330-358) | 17.1 | 28.6 |
  | Eastward 15, channel water (native 480-560 x 0-90) | 10.8 | 21.0 |
  | Eastward 37, pond water (native 5-60 x 100-200) | 5.7 | 16.4 |
  | Eastward 37, white water (native 560-640 x 190-300) | 27.0 | 68.1 |
  | Ours, the woodland sheet (220-256 x 772-880) | 16.8 | 39.5 |
  | Ours, the woodland pool and foam (198-300 x 876-912) | 22.2 | 27.7 |
  | Ours, the woodland stream (480-940 x 880-925) | 7.0 | 4.7 |
  | Kit sheets, short (body from row 16 to row 60) | 14.2 to 15.5 | 19.0 to 28.4 |
  | Kit sheets, tall (body from row 16 to row 108) | 13.1 to 13.9 | 18.8 to 27.9 |

### The painter's claim about the kit pieces

The claim: seven of the eight fail `detail.bar` only because it is measured against Eastward's prop band, and no water band exists.

- **Right, as far as it goes.**
  - `scripts/review/eastward_bands.json` has the groups prop, stone, foliage and ground, and no water group. `bands.score` falls back to prop.
  - `detail.bar` is the only fault-level finding on each of the seven.
  - The prop band is the wrong yardstick for a falling sheet.
  - The two polish detectors are false positives here. `detail.outline` asks for a closed outline, which house-style gives no water or spray. `detail.light` reads the foam heap's mass sitting east of centre as light from the right, but the sheet is lit from the west and each clump's cap is on its upper left.
- **Wrong in "only because".**
  - On a calm-water band (13, 15 and 37's pond: means of 11.2 tones and 22.0 shapes) the sheets would pass. Calm water is not the yardstick for a fall, though.
  - Against white water they fall well short. Against Eastward 37's white water they reach 0.49 to 0.57 of the tones and 0.28 to 0.42 of the shapes.
  - Against the house's own sheet (the woodland fall, 16.8 and 39.5) they reach 0.78 to 0.92 of the tones and 0.48 to 0.72 of the shapes.
  - On the role file's water criteria (falls that fall: streaks, spray, a plunge) and eastward-edges 5.3b they fail on structure, whatever band is used.

So all eight are graded on the water criteria below, and all eight fail, `waterfall_4` included. Its detectors pass only because it is wider. Leads for the detectors are under "False positives".

### Round 3's findings, checked

- **R3-1, a stone over the channel: fixed.** Crop: `lip_r3_r4_7x.png` (200-290 x 720-790 at 7x).
  - `terrain` passes `clear=run_in` to `softground.water`, a box from 14 world px above the fall's y0 down to the rim, 6 world px wider than the fall each side.
  - From y 700 to 766 the channel holds 45 to 50 px of water (x 214-266). No stone, rock or reed stands in it.
  - The sheet is now as wide as the channel, 49 to 51 px at y 769-787.
  - The crest breaks into two runs (x 219-241 and 247-262) with a 5 px gap.
  - The new test reads the rendered picture. It checks that no stone-family texel lies in the 24 rows above the rim inside the channel's columns, and it passes.
- **R3-2, moss hats, one boulder size, few ferns: fixed.** Crops: `face_east_r3_r4_2x.png`, `face_west_r3_r4_2x.png`, `boulder_foot_r3_r4_6x.png`.
  - On the face east of the cascade (x 276-960, y 785-860), green blobs of 15 px or more went from 48 to 24, and these include vines and ferns. All green blobs of 3 px or more went from 91 to 138, most of them tufts of 2 x 2 to 3 x 4 in the dark joints and on the undersides.
  - The larger boulders sit at x about 61, 461, 696 and 922, each 32 to 35 px across. The keep-out over the cascade and steps leaves a 400 px gap between the first two.
  - Ferns cross the rim at x about 558 and 861.
  - Residual polish: G4-1.
- **R3-3, blades hanging from the lip: fixed.** Crop: `lip_east_r3_r4_7x.png`. The olive blades are gone from y 774-800, leaving a clean lip with its lumps and vines.
- **R3-4, the comb on the wet foot: fixed.** Crops: `boulder_foot_r3_r4_6x.png`, `cmp_e13_canal_vs_foot_3x.png`.
  - The recoloured weed ticks are gone.
  - The wet band (y 862-875) carries 2 to 4 px pebbles, each with a lit top, about every 9 px or more apart. Then come the light waterline and the dark band.
- **R3-5, the deck covers the landing: not fixed.** See L4-1 below.
- **Flow, lanes in step: fixed in the rill.** `animate.water` with `thin` takes each lane's phase from a second hash.
  - The rill's dashes still run in the same six columns at a 96 px period.
  - Their starts in frame 0 are now 250, 223 and 265 in the lower run, and 80, 71 and 80 in the upper. Round 3 had 196, 208 and 224, stepped in a diagonal.
  - Two upper lanes still start on one row, which is chance and no more than polish. Crop: `rill_frames0to3_2x.png`.
  - The stream's lanes do not use `thin`, but they had no such fault.
- **R3-6, one 24 MB strip: fixed.**
  - `flow.png` is 1576 x 712 (4.49 MB decoded) and `flow_rill.png` is 180 x 3024 (2.18 MB): 6.67 MB together, against 23.6 MB.
  - Composited, the two strips never overlap, and their union covers rows 0-755 (the rill) and 756-932 (the rest).
  - The moving texels per frame match round 3's to within the changed ground (549 against 565 in frame 0).
  - Both nodes run their own `flow_anim.gd` from t = 0, so they stay in step.
  - `test_flow_strips_keep_to_the_phone_budget` caps a strip at 6 MB and a zone at 9 MB, and passes.
  - Polish D4-1: docs/godot.md says "the woodland: about 3.5 MB". It is 6.7 MB, the figure the commit message gives.
- **K3-1, the kitlab_tiers inlet: fixed, with one polish point left.** Crops: `kt_r3_r4_5x.png` and `kt_inlet_10x.png`.
  - The turf strip under the sheet is gone. Water starts at the sheet's foot row.
  - The bank stone is gone.
  - The inlet's top corners step 624, 620, 618, 617 on the west side and 671 to 679 on the east, about 4 to 7 texels, with the rim down both sides.
  - The foam lies on water.
  - `test_a_fall_lands_in_its_pool` passes.
  - What is left is K4-4.

### New findings

Coordinates are art px in `ground.png` (the scene's frame of reference), or in the kit picture. The crops are local, in the auditor's scratchpad, and can be regenerated from the boxes.

**F4-1. Fault (flow): moving water drawn over the bridge deck.**
- Location: the deck, x 352-414, y 850-941, in every frame. Crop: `bridge_flow_ground_f0_f2_5x.png` (340-430 x 855-940 at 5x: the ground, then frames 0 to 2).
- What is wrong:
  - The stream's lanes run on under the deck. In each frame 1 to 4 marks, 3 to 35 texels, lift the planks one timber tone, (142,98,66) to (168,124,82), and slide east across them.
  - Frame 0, the reduced-motion still, has 4 marks (35 texels), so they show even with motion off.
  - The same lanes lift the wet rock foot under the face, about 16 texels a frame at x 600-880, y 846-870.
  - Over 8 frames that is about 170 texel-frames on timber and 129 on rock.
  - Round 3 had the same, 160 on timber, and it was missed then.
- Cause: `animate.water` builds its lanes from the water mask, which still covers what was painted over it afterwards (the deck, the terrace's wet foot).
- Fix:
  - Lift only texels whose final ground code is open water, sheet or foam (`codes` water families), not timber, stone, earth, grass or leaf.
  - Add a test: in every strip, no moving texel lies over a non-water ground texel, outside the foam and spray box.

**G4-1. Polish (ground): the larger face boulders read as cracked piles.**
- Location: the boulders at x about 61, 461, 696 and 922 near the face's foot. The clearest is x 645-710, y 830-866. Crops: `bigboulder_10x.png`, `cmp_e12_vs_face_bigboulder_3x.png`.
- What is wrong: each is a `props.boulder4` pasted onto the face, the right size of 32 to 35 px. Its crack lines cut it into three or four lobes in the same mid tones as the face, so at 1x it reads as a heap of 12 to 18 px stones a shade paler than its neighbours, not "the odd larger boulder" (2.3). 12's largest boulder is one calm form with a dark underside.
- Fix: paint it as one rounded mass, with no cracks or at most one short one. Give it a lit top-left plane two tones up, a mid body, and a 2 to 3 px dark underside and gap separating it from the stones below. Let one or two neighbours tuck under its lower edge.

**K4-1. Fault (kit, all eight pieces): the sheet is flat vertical slabs.**
- Location: the sheet body, x 24 to 24 + w, rows 16-60 (short) or 16-108 (tall). Crops: `kit_short_4x.png`, `kit_tall_4x.png`, `kit2_8x.png`, `wood_fall_vs_kit2_5x.png` (the woodland fall beside `waterfall_2` at 5x).
- What is wrong:
  - The sheet is four bands of flat tone with hard vertical seams: lit (152), mid (124), (93), then navy (62).
  - With frame 0 of the flow overlaid, these columns hold one tone over 40 rows: 9 of 24 (`waterfall_1`), 22 of 48 (`_2`), 45 of 72 (`_3`), 59 of 96 (`_4`) and 67 of 96 (`_4_tall`). The woodland sheet has 10 of 44.
  - The east 3 to 17 px are a flat slab with no streak.
  - The streaks are 1 px white lines on fixed columns (155 vertical continuations against 5 diagonal in `_2`).
  - The silhouette is a perfect rectangle, the same width at the top and the foot, with square corners.
  - It reads as a block of ice: the calibration's flat white bar (W3) in blue.
- Fix: draw the sheet as `rocks.fall` draws the woodland's.
  - 2 to 4 px streak segments in 4 to 5 tones, broken and offset, over the whole width.
  - The darker east edge as 2 to 3 px of broken dark streaks, not a slab.
  - Edges that wander a texel and swell a little toward the foot.
  - Keep the flow overlay moving the streaks.

**K4-2. Fault (kit, all eight pieces): the crest is a lid.**
- Location: rows 12-15 across the sheet. Crop: `kit2_8x.png`.
- What is wrong:
  - Rows 12-14 are a flat three-row tongue in two tones, split by a hard vertical seam.
  - Row 15 is a ruler-straight white line over 75 % (`_1`), 96 % (`_2`), 85 % (`_3`) and 73 % (`_4`) of the width. `_2` has one gap of 2 px.
  - Icicle drips of different lengths hang from it, and it has no bow.
  - `test_a_falls_lip_is_not_stamped` passes because it checks the drips' lengths, not the white row.
- Fix (5.3b):
  - Fade the tongue into the channel over 2 to 3 rows of checker.
  - Bow the bend line a texel or two downstream.
  - Break the white water into 2 to 3 runs of different lengths, with gaps of 3 to 5 px where the darker sheet goes on.
  - Extend the test to the white row itself (its share of the width, and at least two gaps of 3 px or more from `_2` up).

**K4-3. Polish (kit, all eight pieces): a comb under the foam, and stamped spray.**
- Location: in `waterfall_2`, rows 68-70 under the foam and rows 60-64 at x 14-22 and 66-69. Crop: `kit2_8x.png`.
- What is wrong:
  - The darker band under the foam's downstream edge is a row of 1 px navy ticks alternating with gaps, which reads as teeth.
  - The west spray is a row of identical 1 px white ticks on alternate columns.
  - The east spray is a lone 3 x 2 white block.
- Fix:
  - Draw the band as a soft 1 to 2 row shade that follows the clumps' lobes.
  - Draw the spray as 1 to 2 px specks of different sizes in a loose fan, thinning outward.

**K4-4. Polish (kit bake, K3-1 left over): a sill across the inlet's mouth.**
- Location: `kitlab_tiers/ground_baked.png`, x 622-672, y 347-349. Crop: `kt_inlet_10x.png`.
- What is wrong: the pool's north waterline (76,134,180) on row 347 and its dark band (14,32,88) on rows 348-349 run straight across the inlet's mouth. So the inlet reads as a basin a step above the pool.
- Fix:
  - End the waterline and the dark band at the inlet's sides.
  - Carry the inlet's water into the pool's body.
  - Put the deep tone under the foam instead (the plunge is the deepest water).

**D4-1. Polish (docs).** docs/godot.md, "Moving water's budget", says "the woodland: about 3.5 MB". The strips decode to 6.7 MB. Correct the figure.

### Logic (reported separately, as in earlier rounds)

**L4-1. Fault: the landing is half a cell, and the bridge has not moved (R3-5 not fixed).**
- Location: x 340-440, y 760-880. Crops: `steps_r3_r4_5x.png` (335-440 x 755-905 at 5x, round 3 beside round 4) and `midleft_vs_diff.png` (the changed texels).
- Unit: art px at density 3, where a cell is 8 world px = 24 art px. World px are given in brackets.
- What is measured, at the deck's middle (x 390) and beside it (x 417-438):
  - The last riser ends at y 830.
  - Open path runs y 831-845: **15 art px (5 world px), 0.63 of a cell.**
  - The north abutment's cap row is at y 846-849, and the deck starts at y 850.
  - The waterline beside the bridge is at y 876.
  - So the abutment stands 30 art px (10 world px) north of the water, and the deck rests on 26 art px (8.7 world px) of land, not the 3 world px the commit says.
  - In x 350-425, rows 846-870 have 0 texels changed from round 3. Only the steps moved, up 8 px, and the open path grew from 6 to 15 px.
- Is "11 px" one cell deep?
  - The plan's `steps.landing` is 11 world px (33 art px), from the stair's foot (y 831) to the face's foot and the plan's bridge y0 (y 864). On the plan that is 1.4 cells.
  - In the picture, 18 of those 33 px are under the abutment and deck.
  - Read as 11 art px, it would be 0.46 of a cell.
  - Either way the open landing is under one cell, against eastward-edges 5.3b ("a landing one cell deep of open path; the bridge's north abutment starts at the water's edge"), which this commit wrote.
- Side effect: moving the foot up tightened the stair's pitch from 15 to 13 art px (risers at 775, 788, 801, 814 and 827), which is 4.3 world px a step, below 6.1's 5 to 6.
- Likely cause:
  - `footbridge` draws its north abutment from 14 texels and its deck from 10 texels north of the first row of its span mask.
  - `wspan` already extends the open water 9 texels north.
  - The bridge is painted before `terrace` brings the waterline down to y 876, and the terrace's landing restores the old ground, deck included.
- Fix:
  - Paint the bridge after the terrace, or give it the final waterline.
  - Start the north abutment no more than 3 world px (9 art px) north of the waterline, at about y 863, with the deck from about 867.
  - Put the stair's foot back to a 15 to 18 px pitch, about y 839.
  - That leaves y 839-862 open path, 24 art px (one cell).
  - Add a test on the picture: between the stair's last riser and the abutment's top row, at least 24 rows of path.

**L4-2. Polish: two stone groups across the rill read as a weir.**
- Location: x 152-232, y 378-401. Crops: `rill_r3_r4_2x.png` and `rill_dam_r3_r4_7x.png`.
- What is wrong:
  - Since the bank stones were re-seated, a group on the west bank reaches to x 194 (rows 393-400) and one on the east bank reaches to x 195 (rows 380-392), in a rill of x 169-214.
  - Seen from above they overlap across the whole channel, leaving a gap of 1 to 6 px. They read as stepping stones or a weir, though no route crosses there.
  - Each has its wet contact.
- Fix: keep a bank group to the outer third of the channel's width. Never set two groups on opposite banks within one cell (24 px) of each other along the flow.

Walk check: `walk.txt` keeps columns 29 to 34 open through the stair, landing and bridge (rows 63 to 77). Unchanged.

### Per-part notes

**`woodland/ground`:**
- **Channel above the lip, tongue and crest:** pass (R3-1).
- **Sheet:** pass. It is now the channel's width.
- **Foam, spray and arcs:** pass.
- **Face:** pass, with polish G4-1. The moss is in the joints, the caps are few, two ferns cross the rim, and vines hang from a clean lip.
- **Wet foot:** pebbles with lit tops, the waterline and the dark band. Pass.
- **East ashlar stack:** unchanged. Pass.
- **Log steps:** five treads, now on a 13 px pitch (L4-1).
- **Landing and bridge:** L4-1.
- **Rill:** pass, with L4-2.
- **Pool, stream and rims:** unchanged. Pass.

**`woodland/flow`:**
- The stream's marks are horizontal: 23 to 26 a frame, no vertical or diagonal marks, and no lone specks.
- The foam churns in all eight frames.
- The deck and the wet foot fail (F4-1).

**`woodland/flow_rill`:**
- The dashes run south and turn at the jogs.
- 0 to 2 lone texels a frame.
- 33 to 39 marks a frame.
- About 12 texels a frame lie over reeds, the rubble stones on the rims and the jogs' north faces: F4-1's cause, polish here.

**Kit pieces:**
- **Sheet:** fail (K4-1).
- **Crest:** fail (K4-2).
- **Foam:** pass on its own. It is a heap of clumps with caps on their upper left, blue-grey on the lower right, and pool blue between them, and it churns in every frame. Its base and the spray are K4-3.
- **Arcs:** light dashes in rings. Pass.
- **Light:** the sheet is lit from the west. Pass.
- **Scale:** the sheets are 1, 2, 3 and 4 cells wide, beside Bramble on the asset sheets. Pass.

### Tile log (ground, every region opened against round 3)

| Tile (art px) | View | Notes |
| --- | --- | --- |
| 0-480 x 0-576 | 2x, rill at 2x across 8 frames, 7x at y 365-415 | 9557 texels changed: bank stones re-seated (L4-2), reeds, lawn dressing. The rill moves. |
| 480-960 x 0-576 | 1x with a diff overlay | 80 texels: one tuft. No water. |
| 0-480 x 576-1152 | 1x diff overlay, 2x, crops at 5x to 10x | Clear channel and crest (R3-1); sheet as wide as the channel; west face with a larger boulder (G4-1); steps moved up, landing and bridge unchanged (L4-1); pool south rim retouched |
| 480-960 x 576-1152 | 1x diff overlay, 2x, 6x to 10x | Face: moss, larger boulders (G4-1), ferns, clean lip; wet foot pebbles; stream unchanged; south shore dressing |
| 0-480 x 1152-1728 | 1x with a diff overlay | 5962 texels: tufts reshuffled. Same kind and density. No water. |
| 480-960 x 1152-1728 | 1x with a diff overlay | 9024 texels: the same. The path is unchanged. |

### False positives

- **`woodland/*`:** 0 detector findings, so **0 rejected**.
- **Kit pieces: all 20 findings rejected.**
  - 8 `detail.bar` (7 faults, and the polish on `waterfall_4`): the wrong band. The pieces fail anyway, on K4-1 and K4-2.
  - 8 `detail.outline` polish: water and spray take no outline (house-style).
  - 4 `detail.light` polish (`_2`, `_2_tall`, `_4`, `_4_tall`): the foam heap's mass sits east of centre. The sheet is lit from the west, and each clump's cap is on its upper left.
- Leads for the detectors:
  - A water group in `eastward_bands.json`: calm water from 13, 15 and 37's pond, and white water from 37. Give falls the white-water band.
  - A `detail.fall_flat` variant for sheets: the share of a sheet's columns holding one tone over 40 rows (fail above 0.35), and a crest row that is white over more than 70 % of the sheet's width.
  - In `animate.water`'s tests: no moving texel over a non-water ground code (F4-1).
  - A landing check: rows of path between a stair's last riser and the next structure, against one cell (L4-1).

### Not checked

- **Motion at speed on a device:** played as GIFs and contact sheets on a desktop. There was no phone or native check, and no texture memory was measured on a device (R3-6 is arithmetic on the decoded sizes).
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0 only. In the woodland it shows the F4-1 marks on the deck. The kit pieces hold their frame 0.
- **The kit pieces in a composed kit zone:** seen only in the kitlab_tiers bake at 5x and 10x, not in the game.
- **Whether the bridge or the stair should move for L4-1** is the painter's call. Both fixes are above.

## Round 5 (76241d98)

A fifth independent detail-auditor run, on the two commits that answer round 4: 6068fd3c ("Woodland water, review round 4: water-only lifts, landing a cell, kit falls redrawn") and 76241d98 ("the one-cell falls reach the water band, the landing's sides lumpy"), branch `claude-a/water-polish`, draft PR #434. This auditor did not paint them and did not write rounds 1 to 4. Every number below was measured on the rendered pictures at 76241d98, in art px at density 3 (1 world px = 3 art px, a cell = 24 art px). The painter's numbers were checked, not copied.

**Verdicts:**

| Asset | Detectors | Verdict | Why |
| --- | --- | --- | --- |
| `woodland/ground` | pass, 0 findings | **pass** | L4-1, G4-1 and L4-2 are fixed. Polish P5-1 is a stray waterline chip in the face. It stays in the seeded fix queue for its own `logic.scale` item. |
| `woodland/flow` | pass, 0 findings | **pass** | F4-1 is fixed in every frame, frame 0 included. The foam still churns, and the spray is now loose specks. |
| `woodland/flow_rill` | pass, 0 findings | **pass** | No lift over the reeds, rim stones or jog faces. |
| `kit/waterfall_1` to `_4`, and `_1_tall` to `_4_tall` | pass (`detail.bar` polish 0.52 to 0.57, `detail.outline` polish) | **fail, all eight** | K4-1 to K4-3 are fixed as written, but the sheet is now a mosaic of two-texel chips with no streak running down (K5-1). The band they pass is not water (W5-1). |

`python3 -m scripts.review.gate --check` after the verdicts: **ok** (7 zones, fix queue 2 assets). The kit pieces are not zone art, so the gate does not read their verdicts.

### What was reviewed

- `game/zones/woodland/art/ground.png` (960 x 1728, sha256 `c85e1809...`).
- `game/zones/woodland/art/flow.png` (1576 x 712, 2 x 4 frames of 788 x 178 at (172, 756), sha256 `04830edb...`) and `flow_rill.png` (172 x 2984, 2 x 4 frames of 86 x 746 at (174, 10), sha256 `accb3feb...`), placed by the `flow` and `flows.rill` rects in `kit.json`.
- `game/kit/props/art/waterfall_{1..4}{,_tall}.png` with their `_flow.png` strips, placed at foot + `anim.offset` from `game/kit/props/index.json`.
- `game/zones/kitlab_tiers/ground_baked.png`, `walk.txt` rows 60 to 79, `docs/godot.md` and `scripts/review/eastward_bands.json` with `bands.build_water`.
- Round 4's ground, flow, rill and kitlab_tiers bake (from 3e19c29e) and 6068fd3c's ground, diffed against 76241d98.
- The painter's PR comment (issuecomment-6644899952) and both commit messages.

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as rounds 1 to 4. `calibration_results.json` was reverted afterwards.
- `npm run review:asset -- woodland/ground woodland/flow woodland/flow_rill`: all three pass with 0 findings. `assets.review` with kind `waterfall` and biome `woodland` on the eight kit pieces: all pass, each with `detail.bar` polish (0.544, 0.572, 0.530, 0.533, 0.542, 0.553, 0.537, 0.524 for `_1`, `_1_tall`, `_2`, `_2_tall`, `_3`, `_3_tall`, `_4`, `_4_tall`), `detail.outline` polish, and `detail.light` polish on `_3`. The painter's ratios are right. The records were written with `assets.record` and the reviewer field (`audit5/record.py` in the auditor's scratchpad). Every sha256 matches the painter's record.
- **Own captures.** Godot 4.7.2 under Xvfb rendered the woodland at 76241d98 at 1920 x 1080 (`--zone=woodland --at=130,300` and `--at=190,318`), and a movie of 110 frames at 25 fps with the player off the landing. A GIF was made of the fall, landing and bridge from the movie (`ingame_fall_landing_2x.gif`). The flow strips were also composited frame by frame over the ground (`comp_0` to `comp_7`), and the kit strips over each kit sprite, as GIFs and contact sheets. The painter's in-game sheets were not used.
- Pixel classes, column runs and connected components on those composites. The numbers below come from them.

### Eastward comparison (same character height)

12 and 13 were brought to native with `core.to_native` (3.00x), and 15 and 37 box-averaged to 640 x 360. All four were scaled 1.37x with nearest neighbour. Ours went through `bands.jpeg_roundtrip` before `bands.patch_counts` (0.25 H patches). The crops are local and not committed.

- **12, the rock cliff (native 40-100 x 40-140), against the face with the calm boulders at x 630-730, y 770-880.** Crop: `cmp_e12_vs_calm_boulder_3x.png`. 12's big boulders are single calm forms lit at their top left. Ours now are too. Counts: 12, 21.4 tones and 56.1 shapes a patch. Ours, 17.1 and 38.0. The face was passed in round 3 at these counts.
- **13, the farm stair (`eastward_study.py` crop `14-stair-farm`, native 238-332 x 244-312), against our steps and landing at x 320-460, y 750-900.** Crop: `cmp_e13_stair_vs_landing_3x.png`. 13 has four steps on a 12 E pitch (16 art px at our scale). Each is a lit tread over a dark riser, with the bottom tread on the path. Ours has five plank treads on a 15 px pitch: a 10 px tread lit at its front row, over a 5 px riser. The last tread lands on a cell of open path. They match.
- **15, the channels (native 480-560 x 0-90), against the stream, frame 0.** 15 has 10.8 tones and 21.0 shapes. Ours has 7.2 and 4.9. Both are calm bodies, as in rounds 3 and 4.
- **37, the "white water" (native 540-640 x 170-300), against the woodland fall and foam.** Crop: `cmp_e37_mist_vs_woodfall_3x.png`. The box holds no water (W5-1). Our woodland sheet has 17.0 tones and 39.5 shapes. The pool and foam have 22.0 and 28.7. The same box shows 37's mist, which frays into leaf-shaped flecks and checker. Our foam frays the same way.

### The painter's claims, checked

- **F4-1, the lifts lie only on water: true.** Over the eight composited frames, 465 (frame 0) to 1257 texels move. Every one lies on one of ten ground colours, all of them water, sheet or foam: deep (30,66,122), body (51,100,153), waterline (76,134,180), dark band (14,32,88), (107,162,194), the foam whites and blue-greys, and (149,151,176), which moves only inside the foam box (x 214-273, y 889-898). None lies on timber, rock, the wet foot, stones or reeds, in the rill strip or in frame 0.
- **L4-1, measured at the deck's middle (x 390): true to the texel.**
  - Tread tops are at 766, 781, 796, 811 and 826: a pitch of 15 (5 world px).
  - The last riser runs 836-839. Open path runs y 841-865: **25 art px, one cell**. At x 360 and 405 the landing's sides carry grass at 845-846 and 860-865, which is still open walkable ground.
  - The abutment cap is at 866-867, and the deck starts at 868. The waterline beside the bridge (x 425 and 435) is at 876. So the cap is 10 px north of the water, and the deck rests on 8 px of land.
  - `walk.txt` keeps columns 29 to 34 open through the stair and landing (rows 64 to 71), and 30 to 33 over the bridge (rows 72 to 77).
- **The landing's sides lump into the rock (76241d98): true.**
  - Between 6068fd3c and 76241d98 only 161 texels changed, all in x 344-423, y 841-870.
  - On the east side the rock now steps out to x 419-421 at rows 843-851 and 859-863, against x 423 between them. That is lumps 4 to 5 texels deep and 7 to 9 rows long, edged with the face's darkest tone (45,33,47), broken.
  - On the west side the dark mossy recess under the masonry reaches 3 texels further east at rows 849-865. The stack keeps its straight side.
  - Crop: `landing_sides_5a_5b_7x.png`.
- **K4-1 to K4-3, flat columns 0 and crest white 50 to 69 %: true, and not enough.**
  - With frame 0 overlaid, no column holds one tone over 40 rows in any piece.
  - The whitest crest row (17 or 18) covers 50 % (`_1`), 60 % (`_2`), 57 % (`_3`) and 69 % (`_4`) of the width, in two to five runs at staggered heights.
  - The sheets now fail on what replaced the slabs (K5-1).
- **G4-1, calm boulders: true.** Crop: `boulders_r4_r5_4x.png`. The four larger boulders, at x about 61, 461, 640-730 (two) and 922, are each one rounded mass: a lit top-left plane, a mid body, a dark underside and a gap below. The fallen stone on the west lawn keeps one short crack, which the fix allowed.
- **K4-4, the inlet sill: true.** In `kitlab_tiers/ground_baked.png` rows 346-350 across x 618-680, the waterline (76,134,180) and the dark band (14,32,88) stop at the inlet's sides. The inlet's deep tone (30,66,122) runs on into the pool, and the deepest water lies under the foam. Crop: `kt_r4_r5_4x.png`.
- **L4-2, rill stones: true.** Crop: `rill_weir_r4_r5_6x.png`. The west-bank group at y 393-400 is gone. The east-bank group (x 198-232, y 378-394) reaches only to x 198, in a rill of x 167-212: the outer third. Elsewhere the groups sit on alternate banks. The two nearest, at y 564-577 and 588-605, stand on opposite corners of the lower jog and do not face each other across the water.
- **D4-1: true.** docs/godot.md now says about 6.5 MB (4.5 + 2.1). The strips decode to 4.49 + 2.05 = 6.54 MB.
- **The water band, "measured from Eastward 37's white water": the arithmetic is true, the label is not.** See W5-1.

### Round 4's findings, checked

- **F4-1:** fixed (above).
- **L4-1:** fixed (above).
- **G4-1:** fixed (above).
- **L4-2:** fixed (above).
- **K4-4:** fixed (above).
- **D4-1:** fixed (above).
- **K4-1, the flat slabs: fixed as written, failed anew.** See K5-1. Round 4's fix asked for "2 to 4 px streak segments". That was too short, and it is withdrawn. The house sheet's streak segments run 8 to 30 texels down (median vertical run 15).
- **K4-2, the crest: fixed.** On the whitest row the white water breaks into two to five runs with gaps of 4 to 11 texels, and the runs sit at two or three heights. Left over (polish, not counted): the tongue in rows 12-14 is still a two-tone band with a straight top. In the bake the channel above meets it, so it shows little.
- **K4-3, the comb and the spray: fixed.** Crop: `kit2_foot_f0_f4_crest_8x.png`. The band under the foam is a one-to-two-row navy shade that follows the lobes. The spray is 1 to 2 texel specks of mixed sizes, thinning outward on both sides.
- **The woodland foam after the `rocks.plunge` change: pass.** Crops: `foam_r5_f0to7_5x.png` and `foam_r4_f0to7_5x.png`.
  - The clumps are unchanged from round 4: x 210-275 and y 880-898 over the eight frames, against a sheet foot of about 214-264.
  - What changed is the spray. Round 4's vertical tick pairs beside the foam became loose single and double specks (18 to 30 light texels outside the clumps a frame, was 24 to 34).
  - It still churns in all eight frames.

### New findings

Coordinates are art px in `ground.png` (the scene's frame), or in the kit picture. The crops are local, in the auditor's scratchpad, and can be regenerated from the boxes.

**K5-1. Fault (kit, all eight pieces): the sheet is a mosaic of chips, not falling water.**
- Location: the sheet body, x 25 to 24 + w, rows 20-52 (short) or 20-100 (tall), every frame. Crops: `woodsheet_vs_kit1tall_kit2tall_5x.png` (the woodland sheet beside `waterfall_1_tall` and `_2_tall` at 5x), `kit_waterfall_1_frames_4x.png`, `kit_waterfall_2_frames_4x.png`, `kt_r4_r5_4x.png` (in the kitlab_tiers bake), and the asset sheet `kit__waterfall_1.png` (1x beside Bramble).
- What is wrong:
  - The flat columns were replaced by a field of two-texel chips with no direction.
  - Measured with frame 0 overlaid: in the woodland sheet, 4.6 % of vertical neighbours differ in lightness (over 8 L) against 47 % of horizontal ones, a ratio of 10.2. The mean vertical run of one tone is 17.7 texels. So it reads as streaks running down.
  - In the kit sheets the ratio is 0.92 to 1.02 for the one-cell pieces and 1.21 to 1.33 for the wider ones. The mean vertical run is 1.8 to 2.6 texels, and the horizontal run 1.8 to 2.0. Tones change as often down the sheet as across it.
  - The one-cell sheets (76241d98) are the worst. The painter's "small pieces" is exactly what they read as: a column of blue static, or crumbling ice, at 1x beside Bramble and in the bake. The wider sheets read as a tiled glass wall.
  - The checklist asks for "falls that fall (streaks that wander ...)". House-style 5 asks for water as "the current as 3 to 5 px lit streaks", lying with the flow. A terrazzo of chips is the speckle the checklist rejects.
  - The silhouette is still a rectangle. The west edge is x 24 in every row of every piece, the top is row 12 straight across, and only the east edge wobbles a texel. Nothing swells toward the foot (K4-1's fourth point).
  - Reduced motion holds frame 0, so the still is the mosaic.
- Fix:
  - Draw the body as `rocks.fall` draws the woodland's: lanes 1 to 3 texels wide whose segments run 8 to 30 texels down, broken by short gaps and offset between lanes, in 4 to 5 tones.
  - Keep the lit west part and the broken darker east edge.
  - Cut the one-cell fleck family back to a few two-texel glints. A one-cell sheet needs three or four lanes, not a grid.
  - Let the west edge wander a texel and both edges swell 1 to 2 texels over the last third.
  - Test it in `test_kit`: horizontal-to-vertical change ratio at least 4, and median vertical run at least 6 texels, on every piece in frame 0 and across the loop.

**W5-1. Fault (review tooling): `groups.water` is mist over a lawn and a tree, not white water.**
- Location: `scripts/review/eastward_bands.json` `groups.water` and `bands.EW_WATER` (37, native 560-640 x 190-300 and 560-640 x 170-300). Crop: `e37_waterbox_4x.png`, the measured box at 4x.
- What is wrong:
  - The numbers reproduce: 27.6 and 26.3 tones, 69.4 and 68.4 shapes, mean 26.9 and 68.9, as recorded.
  - But the box holds no water. Shot 37 shows no fall. At its east edge a translucent mist drifts over a pine crown, its trunk, a sunlit lawn and a bush, and that is what the box measures.
  - Lawns and trees elsewhere in 37 give nearly the same counts: 470-560 x 200-300 (lawn and pines, no mist) has 21.3 and 65.7, and 140-240 x 250-330 (lawn and a tent) has 21.6 and 54.0.
  - So the band is "Eastward's busy ground with foliage", and the "white water ... for falls: their sheet, crest and foam" note is wrong.
  - Like 37's mist, it is isotropic (horizontal/vertical ratio 0.9), so it rewards a chip mosaic over streaks. It is part of how K5-1 passed its own gate.
  - Round 4 started this. Its counts table called the same box "Eastward 37, white water", and it suggested the group. That is withdrawn here.
- Fix:
  - Relabel the box as "37: mist over lawn and pines", and stop scoring falls against it.
  - Until an official Eastward shot with a falling sheet is measured, score a fall against the house sibling, the woodland sheet (17.0 tones and 39.5 shapes a patch through the same pipe), and add a direction check (K5-1's ratio).
  - If no Eastward fall exists in the official shots, say so in `bands.py` and in 5.3b, rather than borrowing mist.

**P5-1. Polish (ground): a stray waterline chip and slot in the face's foot.**
- Location: x 478-490, y 860-871. Crop: `foot_notch_10x.png`.
- What is wrong:
  - A 4 x 2 block of the waterline tone (76,134,180) sits in a rock joint at x 483-486, y 860-861, eight rows above the wet foot.
  - Under it, a 4-wide near-black (38,17,24) slot runs from y 864 to 868 across the wet foot band.
  - At the slot the waterline climbs in a 45-degree tent (x 478-490, y 868-871).
  - It was there in round 4 and missed. At 1x it reads as a blue speck in the rock above a crack: water with no source, with a spike in a shore that otherwise wobbles a texel (1.4).
- Fix: clear the chip to the joint's rock tone, close the slot with the wet-foot band and pebbles, and run the waterline flat through x 478-490 at y 871-872 (5.3). If a seep is wanted, draw it as a trickle from a crack with a wet streak down the rock, but nothing here asks for one.

### Logic (reported separately)

No new logic finding. L4-1 and L4-2 are closed (above).
- The stair lands on one cell of open path. The bridge's north abutment stands at the water's edge (10 px north of the waterline, the deck 8 px on land). The walk mask agrees.
- P5-1's water above the shore is the only "water from nowhere" left in the zone. It is graded above as polish because of its size.

### Per-part notes

**`woodland/ground`:**
- **Channel above the lip, tongue, crest and sheet:** unchanged. Pass.
- **Face:** pass. The larger boulders are calm masses, the moss sits in the joints, two ferns cross the rim, and vines hang from a clean lip. Polish P5-1.
- **Wet foot and stream:** pass, except P5-1.
- **Log steps:** five treads on a 15 px pitch, the head flush at 766. Pass.
- **Landing:** 25 px of open path, the sides lumped into the rock. Pass.
- **Bridge:** both abutments at the shores. Pass.
- **Pool, foam, spray, arcs:** pass.
- **Rill and its stones:** pass.

**`woodland/flow` and `flow_rill`:** lifts on water only, in all eight frames. Horizontal stream dashes, southward rill dashes, foam churn. Pass.

**Kit pieces:**
- **Sheet:** fail (K5-1).
- **Crest:** pass, with the tongue polish noted under K4-2.
- **Foam, its shade band, spray and arcs:** pass.
- **Inlet in the bake:** pass (K4-4).
- **Scale:** 1 to 4 cells wide, beside Bramble. Pass.

### Tile log (ground, every region opened against round 4)

| Tile (art px) | View | Notes |
| --- | --- | --- |
| 0-480 x 0-576 | 1x side by side with frame 2, 6x at y 350-420 | 2493 texels changed: the rill's west stone group at y 393-400 is gone, and other bank stones were re-seated (L4-2). No lift over reeds or stones. |
| 480-960 x 0-576 | diff | 0 texels changed. No water. |
| 0-480 x 576-1152 | 2x side by side, 4x to 7x crops, in-game 2x | 11664 texels: the steps re-pitched, the landing and the bridge's north end moved (L4-1), the landing's sides, the west boulder and fallen stones calmed (G4-1), the pool's spray. |
| 480-960 x 576-1152 | 4x and 10x crops | 4323 texels: the larger boulders calmed (G4-1). The face's foot has P5-1. |
| 0-480 x 1152-1728 | diff | 0 texels changed. No water. |
| 480-960 x 1152-1728 | diff | 0 texels changed. No water. |

### False positives

- **`woodland/*`:** 0 detector findings, so **0 rejected**. They missed P5-1.
- **Kit pieces: all 17 findings rejected.**
  - 8 `detail.bar` (polish): measured against W5-1's band, which is not water. The pieces fail on K5-1 whatever the bar says.
  - 8 `detail.outline` (polish): water and spray take no outline (house-style 2).
  - 1 `detail.light` (polish, `_3`): the foam's mass sits east of centre. The sheet's light is from the west.
- Leads for the detectors:
  - A direction check for falls (K5-1's ratio and run length) in `detail.fall_flat` or in a new `detail.fall_grain`.
  - A shore check: water-coloured texels not connected to a water body (P5-1). The woodland has one.

### Not checked

- **Motion on a device:** played as GIFs from the composites and from a Godot movie under Xvfb on a desktop. There was no phone or native check.
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0. In the woodland it shows lifts on water only. The kit pieces hold the mosaic.
- **The kit pieces in a composed kit zone in Godot:** seen only in the kitlab_tiers bake and composited over flat ground, not rendered in the game.
- **An Eastward falling sheet:** none of the local official shots shows one, so the falls were judged against the house sibling (the woodland sheet) and the checklist, not against Eastward (W5-1).

## Round 6 (5725cf90)

A sixth independent detail-auditor run, on the commit that answers round 5 (5725cf90, "Woodland water, review round 5: kit sheets fall in streaks, falls scored against their sibling", branch `claude-a/water-polish`, draft PR #434). This auditor did not paint it and did not write rounds 1 to 5. Every number below was measured on the pictures at 5725cf90, in art px at density 3 (a cell is 24 art px). The painter's numbers were checked, not copied.

**Verdicts:**

| Asset | Detectors | Verdict | Why |
| --- | --- | --- | --- |
| `woodland/ground` | pass, 0 findings | **pass** | P5-1 is fixed. The face was re-checked across its whole length. It stays in the seeded fix queue for its own `logic.scale` item. |
| `woodland/flow` | pass, 0 findings | **pass** | The file is unchanged since f1d30e58. No moving texel lies over ground that changed this round. |
| `woodland/flow_rill` | pass, 0 findings | **pass** | The file is unchanged. Its rect lies wholly above this round's changes. |
| `kit/waterfall_1` to `_4`, and `_1_tall` to `_4_tall` | pass (`detail.bar` polish 0.66 to 0.85 against `groups.fall`, `detail.outline` polish, `detail.light` polish on `_4` and `_4_tall`; no `detail.fall_grain`) | **fail, all eight** | K5-1 is fixed: the sheets fall in streaks and read as falls at 1x. They fail on K6-1: the sheet is about a third darker than its sibling, a dark blue curtain with a lit west strip rather than a lit mass falling to a narrow dark east edge. |

The painter had reset `woodland/flow` and `flow_rill` to "pending" though their files did not change. Both were re-recorded as pass. `python3 -m scripts.review.gate --check` after the verdicts: **ok** (7 zones, fix queue 2 assets). The kit pieces are not zone art, so the gate does not read their verdicts.

### What was reviewed

- `game/zones/woodland/art/ground.png` (960 x 1728, sha256 `88302378...`), diffed against round 5's (f1d30e58, `c85e1809...`).
- `game/zones/woodland/art/flow.png` (`04830edb...`) and `flow_rill.png` (`accb3feb...`): `git diff --quiet f1d30e58 5725cf90` on both, so unchanged. They were composited over the new ground at their `kit.json` rects.
- `game/kit/props/art/waterfall_{1..4}{,_tall}.png` with their `_flow.png` strips, placed at foot + `anim.offset` from `game/kit/props/index.json`, all eight frames.
- `game/zones/kitlab_tiers/ground_baked.png` and `game/zones/woodland_kit/ground_baked.png`.
- Code: `structures.fall_sheet`, `sheet_outline`, `_lanes`, `waterfall` and `fall_frames`, the bake's fall block (`bake.py`), `bands.fall_grain`, `FALL_BAND` and `build_water`, `assets.fall_grain`, `fall_sheet_box` and `group_of`, `gate.py`, and the new `test_kit` checks.
- The painter's captures `kit_pieces_before_after_round6_5x.png`, `kit_falls_ingame_round6.png` and `woodland_native_before_after_1x_round6.png`, and the commit message.

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as rounds 1 to 5. `calibration_results.json` was reverted afterwards.
- `npm run review:asset -- woodland/ground woodland/flow woodland/flow_rill`: all three pass with 0 findings. `assets.review` with kind `waterfall` and biome `woodland` on the eight kit pieces: all pass. Bar against `groups.fall`: 0.709, 0.658, 0.797, 0.747, 0.854, 0.775, 0.786, 0.737 for `_1`, `_1_tall`, `_2`, `_2_tall`, `_3`, `_3_tall`, `_4`, `_4_tall`. Tones are 1.06 to 1.31 of the band, so the ratio is the shapes ratio. No `detail.fall_grain` finding. The records were written with `assets.record` and the reviewer field (`audit6/record.py` in the auditor's scratchpad). Every sha256 matches the painter's record.
- `python3 -m unittest scripts.art.kit.test_kit.WaterBanks`: 17 tests, OK.
- **Own captures.** Godot 4.7.2 under Xvfb, at 1920 x 1080, 2 screen px a texel: `--zone=woodland --at=130,300` and `190,318`, `--zone=kitlab_tiers --at=185,120`, and `--zone=woodland_kit --at=95,300`. The woodland_kit shot was registered to its bake (an exact match at offset y 592) and diffed against it. The painter's captures were looked at but not used for any number.
- **Own measurements.** The grain was measured with an independent script, not `bands.fall_grain`. It used Rec. 601 lightness, horizontal and vertical neighbours differing by more than 8 L, and the vertical runs of one exact colour per column. It ran on the picture and on every frame with the strip overlaid, over the sheet body (rows 20 to foot - 4, interior columns 25 to 24 + w - 1), and again over the strip's own texels with the edges included. Lightness, dark and lit shares, flat single-colour areas and edge extents were measured on frame 0.

### Eastward comparison (same character height)

- **No Eastward falling sheet exists in the local official shots** (01 to 17, 21, 22, 30, 37 to 39). So the kit sheets were compared with the house sibling, the woodland sheet, as W5-1 asked. See "W5-1, judged" below.
- **13, the canal's bank (native 40-140 x 300-360, scaled 1.37x nearest) against the woodland's re-drawn foot at x 440-577, y 830-912.** Crop: `cmp_e13_canal_vs_foot_p51_3x.png`. Both have a bank edge, a dark band, a one-texel light waterline and the body below. The foot now runs on at P5-1 the same way. The patch counts are not like for like here, because the Eastward box takes in a fence and foliage. The face material is unchanged from round 5, which passed it against 12 (21.4 tones and 56.1 shapes against ours 17.1 and 38.0).

### W5-1, judged: scoring falls against the woodland sheet

- **Sound as an interim floor, for two reasons.**
  - It holds the kit to the one design the house already approved (art-style, "one design per object").
  - Inventing a band from mist was worse. The relabel is right, and `groups.mist` no longer scores anything.
- **Not an Eastward bar.** The woodland sheet was never itself measured against an Eastward fall, so the bar is circular: house art against house art. 5.3b and `bands.py` say so plainly, which is the honest position. This auditor could not repeat the web search (Steam, Octopia, press). The local set has no fall.
- **On its own, `detail.bar` points the wrong way for falls.** It counts shapes a patch, and fragmentation scores high.
  - Scored against `groups.fall`, round 5's chip-mosaic pictures (f1d30e58) reach 0.954 (`_1`), 0.937 (`_2`), 0.967 (`_3_tall`) and 0.918 (`_4_tall`), which is a pass.
  - The fixed streak sheets reach 0.73 to 0.80, which is polish.
  - So the band rewards the fault K5-1 removed. `detail.fall_grain` is what actually guards the sheet, and it must stay paired with the band.
- **Not like for like.** `FALL_BAND` is a sheet-only box with frame 0 overlaid. The pieces are scored as whole pictures (crest, sheet, foam, spray, transparent margins) on their static PNG.
- **Blind to value.** Nothing in the tooling compares a fall's lightness with its sibling's, which is how K6-1 passes every detector.

### The painter's claims, checked

- **K5-1, grain at or over 4 and run at or over 6 in every frame: true.** Measured here, over the interior body:

  | Piece | Ratio, picture / frames 0-7 | Median vertical run, picture / frames 0-7 |
  | --- | --- | --- |
  | `waterfall_1` | 9.05 / 7.37-9.23 | 7.5 / 6.0-11.0 |
  | `waterfall_1_tall` | 10.45 / 9.68-10.89 | 12 / 13-15 |
  | `waterfall_2` | 5.00 / 4.72-6.00 | 7 / 6.0-9.5 |
  | `waterfall_2_tall` | 6.64 / 5.95-6.29 | 11 / 12-13 |
  | `waterfall_3` | 4.84 / 5.52-6.01 | 6 / 7.0-8.0 |
  | `waterfall_3_tall` | 6.39 / 7.05-7.30 | 11 / 12 |
  | `waterfall_4` | 5.29 / 5.11-5.87 | 6 / 7-8 |
  | `waterfall_4_tall` | 6.56 / 6.61-6.86 | 11 / 11-12.5 |

  - The woodland sheet (x 222-254, y 780-876, frame 0) measures 9.5 and 14.
  - Over the strip's own texels with the edges included, the lowest ratio is 4.66 (`_2`, frame 4).
  - The short pieces sit at run 6 in `waterfall_1` frame 3, `_2` frame 2, and the `_3` and `_4` pictures, and nowhere lower.
  - Left over: the one-tier pieces carry more short runs than the house sheet. Runs of 2 texels or less are 14 to 30 % of all runs (25th percentile 2 to 3), against the woodland's 4 % (25th percentile 8). They pass the threshold and read as streaks at 1x, so this is no finding.
- **W5-1, relabelled: true.** `groups.mist` holds the 37 box under its right name. `groups.fall` is the woodland sheet's 17.0 tones and 39.5 shapes, with its source noted. `group_of` sends falls there, and `fall_grain` faults below 4 or 6.
- **P5-1, the chip and slot gone and the waterline flat: true.**
  - At x 476-492 no water tone lies above the shore. The joint at 483-486, 860-861 is rock, and the wet foot runs on with a pebble at 483-485, 867-868.
  - The light waterline (76,134,180) runs at y 872 through x 480-491, with one-texel wobbles up to 871 at x 478-479 and 488-489 and the dark band under it. That is within 1.4's texel of wobble.
  - Crop: `foot_notch_r5_r6_10x.png`.
- **"About 2,500 texels of moss and pebbles reshuffled": 2371, all in y 782-881.**
  - Green blobs on the face of 3 px or more: 164 to 170. Of 15 px or more: 29 to 26.
  - The moss stays in the joints and on undersides, and the pebbles keep their lit tops.
  - Not mentioned by the painter, and correct: the same terrace change turned two tongues of pool water that climbed into the face beside the plunge (x 192-209, y 851-863 and x 280-289, y 850-861) into rock. The pool still meets the face on a wet foot. No water-coloured component outside the sheet is left above any shore.
  - Crops: `face_{0,240,480,720}_r5_r6_3x.png` and `pool_west_r5_r6_6x.png`.

### Round 5's findings, checked

- **K5-1:** fixed (above).
- **W5-1:** fixed, with the judgement above.
- **P5-1:** fixed (above).
- **K4-2's tongue polish (not counted):** still there. Rows 12-14 split into two tones at s = 0.65 with a hard vertical seam. In the bakes the channel above meets it, so it shows little.

### New findings

**K6-1. Fault (kit, all eight pieces): a dark blue curtain, not the sibling's lit sheet.**
- Location: the sheet body, x 24 to 24 + w, rows 20 to foot - 4, every frame. Crops:
  - `wood_vs_kit_f0_5x.png` (the woodland sheet beside `_1`, `_2` and `_2_tall` at 5x)
  - `row_1x_shown2x.png` (the woodland sheet and five pieces at 1x, with a 74 px Bramble bar)
  - `kit4tall_f0_6x.png`
  - `wkit_bake_fall_4x.png` and `kt_bake_fall_5x.png`
- What is wrong, measured on frame 0 against the woodland sheet (x 216-262, y 790-870):

  | | Woodland | Kit pieces |
  | --- | --- | --- |
  | Mean lightness | 171 L | 134 to 142 L |
  | East half | 153 L | 98 to 110 L |
  | Texels under 90 L, whole body | 8 % | 15 to 21 % |
  | Texels under 90 L, east 40 % | 19 % | 32 to 47 % |
  | Texels over 200 L, west / middle / east third | 56 / 41 / 26 % | 37-49 / 20-26 / 0 % |

  - Cause: the body ladder in `fall_sheet` steps to water 2 from s 0.6 and to water 1 from 0.85. Alternate lanes go a step deeper again. East of 0.7 no lit run is lighter than water 4.
  - At 1x beside the woodland fall (`row_1x_shown2x.png`) the kit falls read blue where the sibling reads white. They are the same object in two designs, against 5.3b's "a lit west part and a darker east edge" and art-style's one design per object.
  - The dark east part also pools into flat navy slabs. In `waterfall_4_tall` frame 0, one 826-texel area of (30,66,122) covers x 91-119, rows 20-103, and a 300-texel (51,100,153) area covers x 107-119. In `_2_tall` a 369-texel navy area covers x 51-71, rows 75-103. The woodland sheet's largest dark area is 238 texels, in its 4 px east edge.
  - The streaks themselves are right, so this is a tonal fix, not a redraw.
- Fix:
  - In `structures.fall_sheet`, take the body tone to water 4 up to s 0.45 and water 3 up to s 0.88. Keep the dark tones (water 2, and water 1 only in its broken streaks) for the last 2 to 4 texels, s 0.88 on.
  - Apply the alternate-lane deepening only east of s 0.5, and never below water 2.
  - Lit runs: snow 5 up to s 0.45, snow 4 up to s 0.7, water 5 up to s 0.88.
  - Test in `test_kit`, beside `fall_grain`, on frame 0 and across the loop: mean lightness of the body at least 160, east half at least 140, the share under 90 L at most 0.10, the middle third's share over 200 L at least 0.35, and no single-colour area over 250 texels.

**P6-1. Polish (kit, all eight pieces): the sides are still a ruler.**
- Location: both edges of the sheet. In `waterfall_2_tall` the west edge holds x 24 for 17 rows, steps in a texel for 7, holds 20 and steps in for 6, then swells one and two texels over the last third. `waterfall_1` and `_4` show the same with one indent.
- What is wrong: at 1x the sheet is a rectangle with straight sides, white lanes laid straight against the face. The woodland sheet's sides read soft because of their tones: a pale water film outside its west lanes, and a navy edge east that merges into the shaded recess.
- Fix: shorten `sheet_outline`'s wander period to 4 to 8 rows. Paint a one-texel water 4 film outside the west lanes and a 2 to 3 texel navy edge east. These are the woodland's edge tones.

### Logic (reported separately)

**L6-1. Polish (tooling): the catalogued kit picture is not the one the game shows.**
- What is wrong:
  - `structures.waterfall` paints the piece's PNG with `seed=65 + cells_w`.
  - The bake (`rendering.paint.args.seed`) and `fall_frames` (the strip) use `9 + cells_w`.
  - Since `sheet_outline` and `_lanes` take the seed, the PNG's lanes and wandering edges differ from what a baked zone shows. The asset gate grades and hashes the 65 + c picture, which the game hides in every baked zone (`kit_piece.gd`, painted pieces).
  - In an unbaked preview the strip (9 + c) lies over the PNG (65 + c). Each frame, 9 to 45 strip texels then fall outside the PNG's sheet, over the face, and 11 to 43 PNG edge texels stay still. This dates from b3408a7a (27 Oct). It matters more now that the edges wander.
- Fix: paint the PNG with the bake's seed, so that the PNG is frame 0 of the bake. Add a test that the PNG's sheet alpha equals `sheet_mask(..., 9 + c)`.

**L6-2. Lead (tooling, older than this PR): the gate places pending assets.**
- What is wrong: `gate.py` (line 75) admits a record whose detectors pass and whose reviewer verdict is anything but "fail". So a painter's re-record as "pending" stands in the world without an independent review. This branch had `woodland/flow` and `flow_rill` pending until this round. review-agents.md asks for a detail-auditor's verdict before placement.
- Fix: require `verdict == 'pass'` for assets outside the fix queue. Have `--record` keep an existing pass when the sha256 is unchanged.

**L6-3. Polish (scene, woodland_kit; not this gate's asset): the fall seems to step out halfway down.**
- What is wrong: the oak crown west of the fall covers the channel and the sheet's top-west 12 to 14 texels, down to y 785 in the bake. At 1x the sheet seems to step out 12 texels halfway down. Crop: `wkit_ingame_vs_bake_3x.png`, in-game beside the bake.
- Fix: move the tree a cell west, or keep its crown off the sheet's columns, for the scene gate.

### Per-part notes

**`woodland/ground`:**
- **Channel, tongue, crest, sheet, foam, spray, arcs:** unchanged. Pass.
- **Face:** moss and pebbles reshuffled in kind. Pass.
- **Wet foot at x 470-500:** P5-1 closed. Pass.
- **Plunge pool's north edge:** the climbing tongues are now rock. The pool meets the face on its wet foot. Pass.
- **Steps, landing, bridge, rill, stream:** unchanged. Pass.

**`woodland/flow` and `flow_rill`:** unchanged files. Their lifts lie on water and foam only. Pass.

**Kit pieces:**
- **Sheet streaks:** pass (K5-1 closed).
- **Sheet value:** fail (K6-1).
- **Edges:** polish (P6-1).
- **Crest:** pass, with K4-2's tongue polish.
- **Foam, its shade band, spray and arcs:** unchanged. Pass.
- **Light:** lit west. Pass.
- **Scale:** 1 to 4 cells, beside Bramble. Pass.
- **At 1x in Godot** (woodland_kit with `_3_tall`, kitlab_tiers with `_2`): they read as falling water, bluer and darker than the woodland's.

### Tile log (ground, every region opened against round 5)

| Tile (art px) | View | Notes |
| --- | --- | --- |
| 0-480 x 0-576 | diff | 0 texels changed. The rill is unchanged. |
| 480-960 x 0-576 | diff | 0 texels changed. |
| 0-480 x 576-1152 | 3x side by side (y 770-890), 6x at the pool, in-game 1x | 779 texels: face moss and pebbles reshuffled. The pool's climbing tongues at x 192-209 and 280-289 are now rock. |
| 480-960 x 576-1152 | 3x side by side (y 770-890), 10x at x 460-510 | 1592 texels: moss and pebbles reshuffled. P5-1 closed, the waterline flat. |
| 0-480 x 1152-1728 | diff | 0 texels changed. |
| 480-960 x 1152-1728 | diff | 0 texels changed. |

### False positives

- **`woodland/*`:** 0 detector findings, so **0 rejected**.
- **Kit pieces: all 18 findings rejected.**
  - 8 `detail.bar` (polish): the band's shape count rewards chips (above). The pieces fail on K6-1 whatever the bar says.
  - 8 `detail.outline` (polish): water takes no outline.
  - 2 `detail.light` (polish, `_4` and `_4_tall`): the foam's mass sits east of centre. The sheet is lit from the west.
- Leads for the detectors:
  - A lightness check for falls against the sibling (K6-1's mean, east half and dark share), beside `fall_grain`.
  - A PNG-equals-bake check for painted pieces (L6-1).
  - Requiring a reviewer pass in the gate (L6-2).

### Not checked

- **Motion on a device:** the frames were measured and looked at as contact sheets, and the Godot shots were stills on a desktop. There was no phone or native check.
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0, which holds the streaks and the K6-1 value structure.
- **An Eastward falling sheet:** none exists in the local official shots. The painter's web search was not repeated.

## Round 7 (e2a3c545)

A seventh independent detail-auditor run, on the commit that answers round 6 (e2a3c545, "Woodland water, review round 6: the kit's falls as light as their sibling, picture = bake", branch `claude-a/water-polish`, draft PR #434). This auditor did not paint it and did not write rounds 1 to 6. Every number below was measured here, on the pictures and frames at e2a3c545, in art px at density 3 (a cell is 24 art px), with Rec. 601 lightness. The painter's numbers were checked, not copied.

**Verdicts:**

| Asset | Detectors | Verdict | Why |
| --- | --- | --- | --- |
| `woodland/ground`, `woodland/flow`, `woodland/flow_rill` | not re-run | **round 6's pass stands** | `git diff --quiet a5a3d874 e2a3c545` on the three pictures and their records: unchanged. Their records were left alone. |
| `kit/waterfall_1` to `_4`, and `_1_tall` to `_4_tall` | pass (`detail.bar` polish 0.73 to 0.82 on `_1`, `_1_tall`, `_2`, `_2_tall`, none on `_3` and `_4`; `detail.outline` polish on all; no `fall_grain` or `fall_value` finding) | **fail, all eight** | K6-1, P6-1, L6-1 and the tongue seam are fixed as written, and the sheets do not overshoot in brightness. They fail on K7-1: the value range is compressed and has left the sibling's ladder, so the sheet has no shaded east side and reads as a pale, greyish curtain beside the woodland fall. |

`python3 -m scripts.review.gate --check` after the verdicts: **ok** (7 zones, fix queue 2 assets). The kit pieces are not zone art, so the gate does not read their verdicts.

### What was reviewed

- `game/kit/props/art/waterfall_{1..4}{,_tall}.png` and their `_flow.png` strips, all eight frames, rebuilt here with `structures.fall_sheet(..., seed=9 + c, t)` exactly as `fall_frames` and the test do.
- `game/zones/woodland_kit/ground_baked.png` (the fall is `waterfall_3_tall` at (204, 840) texels), diffed against a5a3d874's; `game/kit/zones/woodland_kit.json` (tree-3) and `woodland_kit.tscn`.
- Code: `structures.fall_sheet` (`FALL_LANE_TONES`, the east edge, the tongue), `sheet_outline`, `bands.fall_value`, `assets.fall_grain`, the new `test_kit` checks, and the eastward-edges 5.3b edit.
- The painter's `kit_pieces_before_after_round7_5x.png` and `kit_falls_ingame_round7.png`, and the commit message. Looked at; no number was taken from them.
- The woodland's sheet as the sibling: `ground.png` with frame 0 of `flow.png` laid at (172, 756).

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as rounds 1 to 6. `calibration_results.json` was reverted afterwards.
- `assets.review` with kind `waterfall` and biome `woodland` on the eight pieces (sheets in `artifacts/review/assets/kit__waterfall_*.png`, not committed): all pass the detectors. Every sha256 matches the painter's record. The records were then written with `assets.record` and the reviewer field (`audit7/record.py` in the auditor's scratchpad).
- `python3 -m unittest scripts.art.kit.test_kit.WaterBanks`: 18 tests, OK.
- **Own captures.** Godot 4.7.2 under Xvfb at 1920 x 1080 (2 screen px a texel): `--zone=woodland --at=130,300`, `--zone=woodland_kit --at=95,300` and `68,295`, `--zone=kitlab_tiers --at=185,120`. Crops: `ig_wood_vs_wkit_2x.png` (the two falls side by side), `row_ingame_2px.png` and `row_ingame_1x.png` (both falls with Bramble, as shown and at one screen px a texel), `wkit_bake_fall_4x.png`, `wkit_bake_r6_r7_3x.png`, `wkit_foot_8x.png`, `wf4_foot_6x.png`, `diff_fallwest.png`, `diff_south.png`. All local.
- **Own measurements** (`audit7/meas.py`, `hist.py`): grain (share of horizontal against vertical neighbours differing by more than 8 L; median vertical run of one exact colour per column) over rows 20 to foot - 4 and columns 25 to 24 + w - 1; value (mean, east half, share under 90 L, share over 200 L per third, share over 230 L, standard deviation, largest one-colour area) over `sheet_mask` rows 20 to foot - 4; tone counts per third; the per-row edge offsets from `sheet_outline`; foam cover under the foot.
- `npm run review:scene -- woodland_kit` for the L6-3 scene check (below).

### Eastward comparison

No official Eastward shot in the local set shows a falling sheet (01 to 17, 21, 22, 30, 37 to 39), as rounds 5 and 6 found. The pieces were compared with their house sibling, the woodland sheet, at the same character height: side by side at 2 screen px a texel in Godot (`ig_wood_vs_wkit_2x.png`) and with Bramble beside both (`row_ingame_2px.png`).

### The painter's claims, checked

- **K6-1, value: the numbers are true.**
  - Frame 0: mean 170.7 to 181.2, east half 156.6 to 164.3, under 90 L 0.006 to 0.021, middle third over 200 L 0.38 to 0.52, largest one-colour area 58 to 122. All as reported.
  - Across the loop: mean 169.3 to 182.5, east half 153.2 to 167.0, under 90 L at most 0.021, largest area at most 122.
  - **The thin margin:** `waterfall_1`'s middle third over 200 L is 0.355 at its lowest frame against the test's 0.35. Its frame 0 is 0.47. The next lowest is `waterfall_2`, 0.364. It passes, but a reseed or a small palette change can tip it.
- **Grain: true, with the thin margin.** Ratio 6.2 to 11.4 over every frame of every piece (the woodland sheet 9.7). Median run 6.0 to 13 (the woodland 14). 6.0, at the threshold, occurs in some frames of `waterfall_1` and `waterfall_2`; the one-tier pieces' runs of 2 texels or less are 12 to 30 % of all runs, against the woodland's 4 %. They read as streaks at 1x. Not a finding.
- **P6-1: true, with one mistake.** Above the swell each edge steps in or out after runs of 4 to 8 rows in every piece. Every row's west column is the water 4 film. But the navy east edge is **one texel in 58 to 89 % of rows** and two in the rest, not "2 (now and then 3)" as the commit and 5.3b say. `fall_sheet` sets `east = xr - X <= edge_w[k]` with `edge_w` 1 or 2, and `xr` is exclusive, so the edge is `edge_w` texels wide.
- **The tongue: true.** Rows 12 to 14 meet water 4 and water 3 in a checker from s 0.55 to 0.78; no hard seam is left. What is left is P7-3.
- **L6-1: true, to the texel.** On all eight pieces the PNG's sheet (rows 12 to foot) equals `fall_sheet(9 + c)` frame 0 in colour and alpha, texel for texel. In the woodland_kit bake the sheet body equals `waterfall_3_tall.png` at (144, 732) on every body texel. `test_a_falls_picture_is_its_baked_frame_0` passes.
- **L6-3: true.** `tree-3` stands at (60, 864) texels, on the soft grid (5 x 12 across, 36 x 24 down). From `oak.png` and its foot (106, 243), its crown's east edge is at x 156 at most (rows 717 to 753); the channel and the sheet start at x 168. So 12 texels, half a cell, stay clear, and in the Godot capture nothing of the crown lies over the channel or the sheet. The bake changed in 47,468 texels: the fall itself, the canopy shade that moved with the tree, and canopy-shade dressing elsewhere reshuffled in kind (`diff_fallwest.png`, `diff_south.png`). The `.tscn` diff is node ids plus tree-3's `at`. The scene gate lists for tree-3 only its piece status (`rules.unapproved`, candidate) and two `rules.scale` polish lines about the piece's class, which do not depend on where it stands. The zone's other 562 scene findings (most of them `detail.flat` on captures and `logic.off_grid` on dressing) are about the lab zone as a whole and were not graded here.
- **"Up to 10 L brighter than the woodland sheet, paler and less blue": brighter is wrong, paler and less blue is right, for other reasons.**
  - Round 6's woodland box (x 216-262) took in 4 to 5 columns of the navy recess east of the sheet (L 61). On the sheet alone (x 216-258, y 790-870, frame 0) the woodland measures **mean 177, east half 165, sd 56, 2.2 % under 90 L, 43 % over 230 L, and 33 % of its east third under 100 L**. Against that the kit's means sit 6 L under to 10 L over. So the sheets do not overshoot in lightness.
  - What makes them read paler is the range, not the mean: see K7-1.

### Round 6's findings, checked

- **K6-1:** fixed as written. Measured above. The fix line it gave, "the dark tones only in the last 2 to 4 texels", misread the sibling and is withdrawn (K7-1).
- **P6-1:** fixed, apart from the one-texel east edge (K7-1).
- **K4-2's tongue polish:** fixed, with P7-3 left.
- **L6-1:** fixed.
- **L6-2 (lead):** unchanged and not relied on. The woodland records are pass, and the kit records are now fail.
- **L6-3:** fixed.

### New findings

Coordinates are texels in the kit picture, or in `woodland_kit/ground_baked.png`. The crops are local, in the auditor's scratchpad.

**K7-1. Fault (kit, all eight pieces): a compressed, off-ladder value range, with no shaded east side.**
- Location: the sheet body, rows 20 to foot - 4, every frame. Crops: `ig_wood_vs_wkit_2x.png`, `row_ingame_2px.png`, `wkit_bake_r6_r7_3x.png`, and the 4x view in `artifacts/review/assets/kit__waterfall_2_tall.png`.
- What is wrong, against the woodland sheet alone (frame 0):

  | | Woodland sheet | Kit pieces |
  | --- | --- | --- |
  | Mean / east half | 177 / 165 L | 171 to 181 / 157 to 164 L |
  | Standard deviation | 56 | 42 to 45 |
  | Over 230 L (the whitest runs) | 43 % | 18 to 27 % |
  | East third under 100 L (dark streaks) | 33 % | 4 to 20 % (the one-cell pieces 18 to 20, the wider 4 to 8) |
  | Navy east edge | broken dark streaks through its east third | 1 texel in most rows |
  | Tones in the body | snow 5, snow 4, water 5, 4, 3, 2, 1 | the same, plus snow 2 and snow 3 |

  - The east third is where the designs part. The woodland's (x 245-258) is lit streaks over navy: water 5 36 %, snow 4 30 %, water 2 25 %, water 1 6 %. The kit's is mid tones only: snow 2 19 to 28 %, water 3, water 4 and water 5 each 14 to 31 %, water 2 and 1 under 8 % on the wider pieces.
  - `FALL_LANE_TONES`' second palette uses snow 2 (182, 187, 206; hue 228) and snow 3 (214, 222, 234; hue 216). They are lilac-greys, and the woodland sheet never uses them. They are up to 28 % of an east third and 16 to 19 % of a middle third. That is the "less blue".
  - So at game scale beside Bramble the kit fall is a pale, chalky curtain, lit across its whole width, with a thin blue line for an east edge. The woodland fall beside it is white streaks falling to a shaded east side. The checklist asks for volume, "a highlight band left of centre and a core shadow on the right". It has the highlight but not the shadow. It is the same object in a second design (art-style, one design per object), and it is off 5.3b's ladder, which the commit itself wrote.
  - Round 6 caused part of this. Its prescription kept the dark tones to the last 2 to 4 texels, but the sibling carries them as broken streaks through its east third. That line is withdrawn.
- Fix (a tonal change, not a redraw):
  - Keep `FALL_LANE_TONES` on the ladder and disjoint per zone, for example:
    - palette 0: W (water 4, snow 5, snow 5, snow 5), M (water 3, snow 4, snow 4, snow 4), E (water 3, water 5, water 5, water 5);
    - palette 1: W (water 5, snow 4, snow 4, snow 4), M (water 4, snow 5, snow 5, snow 5), E (water 2, snow 4, snow 4, snow 4).
  - Make the east edge 2 or 3 texels (`edge_w` 2 or 3, or `<` changed to `<=` by one).
  - Feasibility, checked here with that palette (`audit7/sim4.py`; the edge change not simulated) on all eight pieces and all eight frames: `fall_value` passes (mean 170 to 187, east half 151 to 170, under 90 L at most 0.02, middle third over 200 L 0.355 to 0.57, largest area at most 122), `fall_grain` passes (ratio 6.4 to 12.1, run 6 to 13.5), sd 51 to 56, over 230 L 32 to 49 %, east third under 100 L 17 to 45 %. `waterfall_1`'s middle third stays at 0.355.
  - Add to `bands.fall_value`, beside its floors: sd at least 48, the east third at least 0.15 under 100 L, at least 0.28 over 230 L, and no snow 0 to 3 in the body. Then a lighter sheet with no shade cannot pass again.

**P7-2. Polish (kit, the wider pieces): the foot lands bare beside the foam.**
- Location: the foot row and the three under it. In frame 0 the foam covers 76 to 87 % of the foot's columns. `waterfall_4` leaves gaps of 13, 8 and 3 texels (`wf4_foot_6x.png`), and `_2` and `_3` one gap of 9 to 10. Across the loop the largest gap is 4 (`_1`), 9 (`_2`), 12 (`_3`) and 16 (`_4`). In the woodland_kit bake (`wkit_foot_8x.png`) the sheet's east 8 to 10 texels end in a straight line on the inlet water.
- Why it is new here: the bake has always used seed 9 + c. Now that the catalogued picture is the bake's frame 0 (L6-1), the gate sees the gaps.
- What is wrong: 5.3b keeps the foam to "the foot plus 8 px each side". The woodland's foam spans its whole foot. A sheet that ends in a ruler line on the water reads as cut off.
- Fix: in `rocks.plunge`, seat a clump (or a 2 to 3 row white break with flecks) under any run of 4 or more foot columns that no clump reaches, in every frame.

**P7-3. Polish (kit, all eight pieces): the tongue's checker is a rectangle.**
- Location: rows 12 to 14 (the bend row 15 too), s 0.55 to 0.78. Crop: the 4x view on each asset sheet.
- What is wrong: the seam became a checker block with straight vertical sides at both ends. On its own picture it reads as a dither patch on the lip. In the bakes the channel above has its own checker fade, so it shows less.
- Fix: stagger the checker's ends a texel or two per row, or fade the tongue with the row (water 4 to water 3 over the rows) rather than by column.

### Logic and scene (reported separately)

- **L6-3: closed** (above).
- **Lead, older than this round:** in the woodland_kit bake, 20 light-blue specks of one to two texels lie on the earth face on both sides of the sheet, from the lip to the foot, up to 10 texels from it (x 158-167 and 242-250, y 747-839; round 6's bake had 19). They read as spray on the face, against Matt's 2 Nov ruling (5.3b: "never on the face"). Their source was not traced. It is the face's or the bake's, not the piece's, and it is outside this gate.
- **Lead:** the scene gate gives `logic.occlusion` on `waterfall_3_tall` in woodland_kit (y-sort point 20 px from its drawn feet). That is unchanged by this commit.

### Per-part notes (kit pieces)

- **Sheet streaks:** pass. Ratio and runs above.
- **Sheet value:** fail (K7-1).
- **Edges:** they step every 4 to 8 rows, with a west film. Pass, apart from the one-texel east edge (K7-1).
- **Tongue and crest:** pass, with P7-3. The white runs break in two to five runs, as in round 5.
- **Foam, shade band, spray, arcs:** the clumps are unchanged in kind. P7-2 on the wider pieces.
- **Light:** lit west. The shade east is missing (K7-1).
- **Picture = bake:** pass (L6-1).
- **Scale:** 1 to 4 cells wide, beside Bramble on the asset sheets and in Godot. Pass.

### Tile log

The woodland's three pictures are unchanged since a5a3d874 (0 texels), so their round-6 tile log stands. For the woodland_kit bake (not this gate's asset), the diff map was opened in full: the fall (x 144-264, y 732-874), canopy shade moving with tree-3 (x 0-165, y 836-916), and canopy-shade dressing reshuffled in kind at about 35 places (for example x 185-555, y 1597-1728).

### False positives

- **Kit pieces: all 12 findings rejected.**
  - 4 `detail.bar` (polish, `_1`, `_1_tall`, `_2`, `_2_tall`): the band rewards fragmentation (round 6). The pieces fail on K7-1 whatever it says.
  - 8 `detail.outline` (polish): water takes no outline.
- The detectors missed K7-1, P7-2 and P7-3. Leads:
  - The range checks in K7-1's fix, in `fall_value`.
  - A foot-cover check in `test_kit`: foam over every run of 4 or more foot columns, in every frame.

### Not checked

- **Motion on a device:** frames were measured and the Godot shots were stills on a desktop. There was no phone or native check.
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0, which is the bake and holds K7-1 and P7-2.
- **An Eastward falling sheet:** none exists in the local official shots.

## Round 8 (ddc50a0b)

An eighth independent detail-auditor run, on the commit that answers round 7 (ddc50a0b, "Woodland water, review round 7: one sheet painter for the woodland and the kit", branch `claude-a/water-polish`, draft PR #434). This auditor did not paint it and did not write rounds 1 to 7. Every number below was measured here, on the pictures, the eight frames and the bakes at ddc50a0b, in texels at density 3 (a cell is 24), with Rec. 601 lightness. The painter's numbers were checked, not copied.

**Verdicts:**

| Asset | Detectors | Verdict | Why |
| --- | --- | --- | --- |
| `woodland/ground`, `woodland/flow`, `woodland/flow_rill` | not re-run | **round 6's pass stands** | `git diff --quiet f9ef6366 ddc50a0b` on the three pictures and their records: byte-identical (sha256 `88302378`, `04830edb`, `accb3feb`). Records left alone. |
| `kit/waterfall_1`, `kit/waterfall_1_tall` | pass (`detail.bar` polish 0.73, 0.74; `detail.outline` polish) | **pass** | The sibling's sheet at one cell: K7-1, P7-2 and P7-3 fixed, a broken crest, a 4 to 6 texel navy edge. Polish only (P8-2, the middle third's lit share). |
| `kit/waterfall_2`, `_2_tall`, `_3`, `_3_tall` | pass (`detail.bar` polish 0.83 to 0.88; `detail.outline` polish) | **fail** | K8-1: the shared crest at these widths is one white run of 36 or 48 texels over a straight shade row, the round-4 lid. |
| `kit/waterfall_4`, `_4_tall` | pass (`detail.bar` polish 0.78, 0.74; `detail.outline` polish) | **fail** | K8-1 (a 64-texel white run, whitest row 0.76 to 0.77) and K8-2 (a flat navy slab 15 to 17 texels wide). |

`python3 -m scripts.review.gate --check` after the verdicts: **ok** (7 zones, fix queue 2 assets). The kit pieces are not zone art, so the gate does not read their verdicts.

### What was reviewed

- `game/kit/props/art/waterfall_{1..4}{,_tall}.png`, each rebuilt here with `structures.fall_sheet(..., seed=9 + c, t)` for all eight frames, as `fall_frames` and the tests do.
- The bakes `woodland_kit`, `kitlab_tiers`, `kitlab` and `kitlab_widths`, diffed against f9ef6366's.
- Code: `rocks.sheet`, `sheet_rows`, `sheet_mask`, `crest_breaks` and `plunge(seat_gaps)`; `structures.fall_sheet`, `crest_foam`, `sheet_mask`; the bake's removed sheen and its wider run-in; `bands.fall_value` and `assets.fall_grain` (the s < 0.85 cut); `scene.check_occlusion`; the `test_kit` and `test_review` changes; the 5.3b edit.
- The painter's `kit_pieces_before_after_round8_5x.png` and `kit_falls_ingame_round8.png`. Looked at; no number was taken from them.
- The sibling: the woodland's sheet in `ground.png`, its lip found by the same channel search as `rocks.fall` (x 216-265, rows 764-888).

### Commands

- `python3 -m scripts.review.calibrate --flagged <Matt's screenshots> --eastward <Eastward shots>`: **recall 39 of 39**. False positives: 5 on 6 clean screens and 29 on 22 clean props, the same as rounds 1 to 7, so the occlusion change cost no recall. `calibration_results.json` was reverted afterwards.
- `assets.review` with kind `waterfall` and biome `woodland` on the eight pieces (sheets in `artifacts/review/assets/kit__waterfall_*.png`, not committed): all pass the detectors, with no `fall_grain` or `fall_value` finding. Every sha256 matches the painter's record. The records were written with `assets.record` and the reviewer field (`audit8/record.py` in the auditor's scratchpad).
- `python3 -m unittest scripts.art.kit.test_kit.WaterBanks scripts.review.test_review.Occlusion scripts.review.test_review.Water`: 30 tests, OK.
- **Own captures.** Godot 4.7.2 under Xvfb at 1920 x 1080 (2 screen px a texel): `--zone=woodland_kit --at=95,300`, `--zone=kitlab_tiers --at=185,120`, `--zone=woodland --at=130,300`. Crops: `ig_wkit_fall_4px.png`, `wkit_r7_r8_4x.png` and `kt_r7_r8_6x.png` (the bakes before and after), `crests_6x.png` (the sibling's crest beside `_2` and `_4` at rounds 4, 7 and 8), `wf4_lip_8x.png`. All local.
- **Own measurements** (`audit8/meas.py`, `meas2.py`, `crest.py`, `bake.py`): value on the ribbon (per row, west of s 0.85) and on the whole sheet, rows 20 to foot - 4; grain; flat columns (one tone over 40 rows) per frame; the east navy run per row; the crest's runs from `crest_foam` and from the picture; foot cover; per-row overhang beyond the lip's columns; water-blue and white on the face beside each baked fall; `scene.load_zone` on all seven zones for the occlusion change.

### Eastward comparison

No official Eastward shot in the local set shows a falling sheet, as rounds 5 to 7 found, so the pieces were compared with their house sibling, the woodland's sheet: side by side in Godot at 2 screen px a texel (`g_woodland.png` and `g_woodland_kit.png`, Bramble in both) and at 6x (`crests_6x.png`).

### The painter's claims, checked

- **One painter: true.** `structures.fall_sheet` is `rocks.sheet` plus `rocks.plunge(seat_gaps=True)`; its only piece-specific arguments are `phase_y` (the rim row), `stagger` (the tongue) and the frame `t`. `test_the_kits_sheet_is_the_woodlands` re-paints the woodland's sheet over its committed ground and matches every sheet texel, and passes here. The woodland's ground, flow and rill are byte-identical to f9ef6366, so their pass stands.
- **K7-1, measured on s < 0.85: true, and fixed.** On the ribbon, over all eight frames: mean 174 to 186, east half 172 to 191, under 90 L 0.003 to 0.032, sd 51 to 58, east third under 100 L 0.17 to 0.38, over 230 L 0.38 to 0.50, no snow 0 to 3. The sibling's ribbon: 177, 168, 0.04, 57, 0.34, 0.42. Frame 0 matches the painter's ranges. On the whole sheet, navy band included, the pieces match too: mean 157 to 166, east half 137 to 149, under 90 L 0.16 to 0.18, sd 65 to 68, east third under 100 L 0.60 to 0.72; the sibling 161, 135, 0.18, 66, 0.66. At 2 screen px a texel in Godot, woodland_kit's fall now reads as the woodland's: white streaks falling to a shaded east side.
- **P7-2, no bare foot gaps: true.** The largest stretch of foot columns with no foam in the first three rows is 0 to 3 in every frame of every piece (round 7: up to 16).
- **P7-3, the tongue staggered: true.** Where water 4 meets water 3 moves row by row (`_4`: columns 57, 66, 93, 74 in rows 12 to 15). It still reads as a flat pale band at 8x (`wf4_lip_8x.png`), which is the sibling's tongue too. Not a finding.
- **The light-blue specks were the bake's sheen: true, and gone.** Water-blue or white on the face beside the fall, from rim + 2 to foot - 2 and 42 texels either side: woodland_kit 44 → 0, kitlab_tiers 2 → 0. Outside the fall boxes, the bakes changed in 12 and 13 texels (the specks); kitlab and kitlab_widths are unchanged, so the moss kept its draw.
- **The occlusion change: true as described, sound against people, with two holes.** See "The occlusion change" below.
- **"Tests brought to the shared design": four relaxations and two report-only rules.** Judged one by one below. Two are justified, one partly, and three are not.

### The relaxations, judged

1. **Flat columns 25 % → 42 %: partly justified.** The sibling over its full height (120 rows) does hold 16 of 42 ribbon columns flat, 38 %. But flat columns depend on the window's height, and the pieces are shorter. Over a 92-row window, the tall pieces' height, the sibling holds 0.26 to 0.36; over 44 rows, 0 to 0.17. The tall pieces measure 0.22 to 0.45 across the loop, and `_4_tall` exceeds even 0.42 in frames 2, 4 and 7 (0.43, 0.45, 0.44), as does `_3_tall` in frame 6 (0.43). The test samples only frames 0 and 3. Frame 0, the still and the bake, is within the sibling's range on every piece. This does not reopen W3: the columns are lit streaks and body tones of a five-tone streaked sheet, and the grain, value and five-tone checks still stand. Polish P8-2.
2. **Whitest crest row 70 % → 80 %: not justified.** The sibling's crest measures 0.65 (`crest_foam`) to 0.67 (picture). The four-cell crest's 0.76 to 0.77 is above round 4's `_4` lid (0.73) and level with its `_1` lid (0.75), so this measure can no longer tell the crest from the lid. **It reopens the round-4 lid**: K8-1.
3. **Crest gaps two → one: not justified.** The sibling has one gap on 49 texels. `crest_breaks` keeps one or two gaps of 3 to 5 texels at any width, so the runs grow with the width: 36, 48 and 64 texels at two, three and four cells. Count the run length, not the gaps: K8-1.
4. **Run ends 1 → 1 or 2: justified.** `crest_breaks` rounds its runs, and the round-4 drips were long icicles under a straight row. A run that ends two deep is not a drip. One tiny run on `_4` (depth 1, 3, 1 at x 2 to 4) reads as a single drip at 8x. It is too small to count.
5. **The middle third's lit share (≥ 0.35) reported only: justified.** The sibling's ribbon has 0.40 to 0.48. The one-cell pieces have 0.23 to 0.32, because their middle third is about seven columns and a few streak lanes. The new floors on spread (sd ≥ 48) and whitest runs (≥ 0.28 over 230 L) guard what K6-1 was about, the dark curtain, and the one-cell pieces pass them (0.38 to 0.42 over 230 L). Noted as polish on `_1` and `_1_tall`.
6. **The 250-texel flat-area cap reported only: justified on the ribbon, not as done.** The sibling's own ribbon has a 573-texel area of snow 4 in this auditor's box (the painter's box: 419), so a 250 cap fails the approved design. But the same commit also cut `fall_value` to s < 0.85, so no check now sees the navy band. That band is a fixed share of the width. On the whole sheet the sibling's largest area is its 8 to 9 texel navy band, 915 texels over 124 rows. On `_4` and `_4_tall` it is 15 to 17 texels wide, 542 and 1,259 texels. That is K6-1's flat navy slab, back in a place the gate no longer looks: K8-2.

### Matt's ruling on spreading, checked

- **Matt's words** (2 Nov, quoted in commit 859e1c53 and ground-rules.md 2): *"the waterfall overlaps in an unrealistic way on the top bit. make sure there are no logic or detail errors"*.
- **The rule written from them** (ground-rules.md 2, unchanged at ddc50a0b): "The fall is centred on the channel that feeds it and is as wide as that channel … The sheet starts on the rim and falls down the face, in front of the face only: nothing of it (no ledge stone, no crest) stands above the rim over the banks or the stream, it never spreads over the stones either side, and spray and foam are only where it lands, on the pool". 5.3b adds "Spray flies up beside the foot over the water only, never on the face (Matt, 2 Nov)". "Never spreads over the stones either side" is Claude A's reading. Matt's own words are only about the top.
- **What the sheets do now:**
  - At the rim each sheet is exactly the lip's columns: in both bakes, `a[y0]` equals the channel's width (the rim test asserts it).
  - In woodland_kit the sheet stays within the lip's columns for 3 rows, then 1 texel over by rows 6 to 9. It is 3 to 4 west and 2 to 4 east over its lower third. kitlab_tiers is the same, 2 west and 4 east at the foot.
  - Nothing lies above the rim. The lip stones on the upper tier are untouched.
  - What the widening covers, read from f9ef6366's bakes: in woodland_kit, 183 texels of earth clods, 71 of crag, 11 of moss and a 6-texel pebble at the wet foot (rows 91 to 95). In kitlab_tiers, 85 of earth and 39 of crag. So the widening covers face material, in front of the face, from the upper third down.
  - The approved sibling does the same: its sheet runs 445 texels past its lip's columns, over its grey rock face.
- **Judgement:** the top bit, what Matt objected to, is clean. No sheet or bake stands above the rim, overlaps the rim's stones or banks, or sprays on the face. Read literally, ground-rules 2's "as wide as that channel" and "never spreads over the stones either side" forbid the lower widening, and 5.3b now requires it. The two vision docs disagree. This is not graded as a fault, because the sibling Matt saw and the reviews passed does exactly this. **D8-1:** Claude A should bring ground-rules 2 into line with 5.3b, for example: "the lip's width at the rim, widening at most 4 to 5 texels a side further down, in front of the face, as the woodland's does". If there is doubt, ask Matt.

### The occlusion change

- **Sound for people.** In Godot 4, z_index orders canvas items before y-sort does, so a sprite at z -5 never sorts against the people at z 0. Its y-sort point cannot misplace anyone.
- **What it hides today.** Run on all seven zones, the skip removes three findings: kitlab_tiers `waterfall_2.png` (gap -19), kitlab_widths `stepping_stones_2.png` (+34) and woodland_kit `waterfall_3_tall.png` (-20). All three are z -5 ground pieces that the bake hides (`visible` false). No z < 0 sprite overlaps another piece's z < 0 sprite; each overlaps only its own loop strip. So nothing real is hidden now.
- **Where it could hide a fault (lead L8-1):**
  - Ground-layer sprites still y-sort among themselves. Two overlapping ground pieces, such as a fall's foam and a footbridge, could draw in the wrong order, and this check no longer looks.
  - The kit path compares the effective z (`e['z']`, parent included), but the non-kit path still reads the sprite's own `z_index` (scene.py, the `Sprite(...)` for non-kit nodes). A sprite with `z_index -1` under a parent at +2 would be skipped while it draws above people.
  - A standing thing put on a ground layer by mistake, so that people walk over it, was never this check's to catch. Now nothing looks near it.
  - A narrower rule: skip a sprite when its effective z is below every actor's and no other piece's ground-layer sprite overlaps it. Or skip sprites the bake hides, which is what the round-7 lead was.

### New findings

Coordinates are texels in the kit picture, or in the bake named. The crops are local, in the auditor's scratchpad.

**K8-1. Fault (kit, `_2`, `_2_tall`, `_3`, `_3_tall`, `_4`, `_4_tall`): the crest is the round-4 lid again.**
- Location: rows 12 to 20 across the lip. Crops: `crests_6x.png` (the sibling, then `_2` and `_4` at rounds 4, 7 and 8), `wf4_lip_8x.png`, and `kt_r7_r8_6x.png` (kitlab_tiers' `_2` in the bake).
- What is wrong:

  | | Runs (texels) | Gaps | Longest run | Whitest row |
  | --- | --- | --- | --- | --- |
  | Woodland sheet (49) | 23, 16 | 5 | 0.47 of the lip | 0.65 to 0.67 |
  | `_1` (24) | 7, 9 | 3 | 0.38 | 0.62 |
  | `_2` (48) | 36, 5 | 4 | 0.75, depth 2 over 30 columns | 0.67 |
  | `_3` (72) | 9, 2, 48 | 3, 5 | 0.67, depth 3 over about 25 columns | 0.69 to 0.71 |
  | `_4` (96) | 3, 64, 15 | 5, 4 | 0.67, 2.7 cells | 0.76 to 0.77 |
  | Round 4's lids (3e19c29e) | | 0 to one of 2 | | 0.73 to 0.96 |

  - `crest_breaks` scales its runs with the width but keeps one or two gaps of 3 to 5 texels. At two to four cells, one run is a white bar 1.5 to 2.7 cells long, nearly constant in depth, over a straight row of its water-2 shade.
  - The bow (1 to 2 texels) is the only thing that bends it.
  - At 6x and in the kitlab_tiers bake it reads as round 4's lid without the drips. Round 7's crests broke into two to five runs at staggered heights, so this is a regression.
  - The relaxed test (whitest row ≤ 0.80, one gap) lets it pass.
- Fix:
  - In `rocks.crest_breaks`, after the existing draws, split any run longer than 24 texels with a gap of 3 to 5 texels, drawing a fresh generator from the seed so that the fall's other draws keep their order. The sibling's longest run is 23, so the woodland stays byte-identical, and `test_the_kits_sheet_is_the_woodlands` will show it. Vary each new run's depth profile as now.
  - Put the test back to a whitest row of at most 0.70 and two gaps from two cells up, and add a longest run of at most 24 texels.

**K8-2. Fault (kit, `_4`, `_4_tall`; polish on `_3`, `_3_tall`): the navy east band is a flat slab at four cells, and no check sees it.**
- Location: the east 15 to 17 texels of the sheet, rows 12 to the foot. Crops: the 4x view in `artifacts/review/assets/kit__waterfall_4_tall.png` and the painter's round-8 sheet.
- What is wrong:
  - `rocks.sheet` paints water 1 with no streaks for s ≥ 0.85, and in the last quarter also for s 0.6 to 0.85. So the band is a share of the width.
  - The east navy run per row is 8 to 9 texels on the sibling (up to 14 at the foot), 4 to 6 on `_1`, 7 to 10 on `_2`, 11 to 16 on `_3` and 15 to 17 on `_4`.
  - The largest single-colour areas on the whole sheet: the sibling 915 texels over 124 rows, `_3_tall` 985, `_4` 542, `_4_tall` 1,259.
  - At four cells it is a flat dark-blue slab a fifth of a character wide, beside the lit streaks: round 6's "flat navy slabs" (K6-1) back again. At the sibling's width the same band reads as its shaded edge. The design does not hold at this scale.
  - `fall_value` and `assets.fall_grain` now measure only s < 0.85, and `test_a_kit_sheet_is_not_flat_slabs` counts only the ribbon, so the band is never checked.
- Fix:
  - In `rocks.sheet`, make the navy band `xr - X <= min(0.15 (xr - xl), 9)` texels and let the s 0.6 to 0.85 ribbon (water 2 with its streaks) run on east of it. At the woodland's width the 0.15 share is 7.4 to 8.7, so the woodland is unchanged.
  - Add a whole-sheet check: an east band of at most 9 texels in the upper three quarters, and no water-1 area over the sibling's per-row share.

**P8-2. Polish (kit, the tall pieces): flat columns measured against a window of another height, and on two frames only.**
- What is wrong: relaxation 1, above. `_4_tall` reaches 0.45 and `_3_tall` 0.43 in frames the test does not sample. At the pieces' height the sibling holds at most 0.36.
- Fix: compare against the sibling over a window of the piece's own height (about 0.38 for the tall pieces and 0.20 for the short), on every frame. If the pieces then fail, shorten the longest streak gaps for sheets under 100 rows.

**D8-1. Docs.** ground-rules.md 2 ("as wide as that channel", "never spreads over the stones either side") and 5.3b ("its widening and wobbling edges") disagree about the lower sheet. See the ruling above.

**L8-1. Lead (tooling).** The occlusion skip's two holes: ground-layer sprites sorting among themselves, and the non-kit path's z. See above.

### Round 7's findings, checked

- **K7-1:** fixed (above).
- **P7-2:** fixed (above).
- **P7-3:** fixed (above).
- **The lead on spray on the face:** fixed (above).
- **The lead on `logic.occlusion` on `waterfall_3_tall`:** closed by the skip, judged above.

### Per-part notes (kit pieces)

- **Tongue:** pass on all eight. The two tones meet staggered.
- **Crest:** pass on `_1` and `_1_tall`. Fail on the other six (K8-1).
- **Sheet streaks and grain:** pass. Ratio 6.9 to 11.3, median run 7 to 17, over every frame on the ribbon.
- **Sheet value:** pass. It is the sibling's, on the ribbon and on the whole sheet.
- **East band:** pass on `_1`, `_1_tall`, `_2` and `_2_tall`. Polish on `_3` and `_3_tall`, fault on `_4` and `_4_tall` (K8-2).
- **Edges:** they widen and wobble as the sibling's do. The top is the lip's width.
- **Foam, shade band, spray, arcs:** pass. The foot is covered in every frame.
- **Light:** lit west, shaded east. Pass.
- **Picture = bake:** pass. In the woodland_kit bake the sheet is the piece's frame 0.
- **Scale:** 1 to 4 cells, beside Bramble on the asset sheets and in Godot. Pass.

### Tile log

- The woodland's three pictures are unchanged since f9ef6366 (0 texels), so round 6's tile log stands.
- **woodland_kit bake:** 7,038 texels changed, 7,026 of them in the fall's box (x 144-264, y 700-880). The other 12 (x 126-281, y 777-839) are the removed specks.
- **kitlab_tiers bake:** 2,676 texels changed, 2,663 in the fall's box (x 600-700, y 250-370). The other 13 are specks.
- **kitlab and kitlab_widths:** 0 texels changed.

### False positives

- **Kit pieces: all 16 findings rejected.**
  - 8 `detail.bar` (polish, 0.73 to 0.88): the fall band rewards fragmentation (round 6).
  - 8 `detail.outline` (polish): water takes no outline.
- The detectors missed K8-1 and K8-2, because the relaxed tests and the s < 0.85 cut stand between them and these faults. Leads are in the fixes.

### Not checked

- **Motion on a device:** frames were measured and the Godot shots were stills on a desktop. There was no phone or native check.
- **Night tint:** not checked.
- **Reduced motion:** judged from frame 0, which is the bake. It holds K8-1 and K8-2.
- **The four-cell pieces in a composed zone:** no baked zone places `waterfall_4` or `_4_tall`. They were judged on their asset sheets and composited frames.
- **An Eastward falling sheet:** none exists in the local official shots.
