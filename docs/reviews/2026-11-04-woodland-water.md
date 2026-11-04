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
