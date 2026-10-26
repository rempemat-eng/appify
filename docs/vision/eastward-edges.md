# Edges and the soft grid: Eastward only

**Density 2 (Matt, 21 Oct 18:17: "let's go with 2x. final decision."):** all new art is drawn at 2x, an adult of 50 art px, so k = 50 / 54 ≈ 0.93 and Eastward's measurements below apply almost 1:1 in art px. The "ours" figures stay in world px (k = 0.46); double them for art px ([art-style.md](art-style.md), "Density 2").

Matt, 21 Oct 09:23: "can you use only eastward as the example on how to draw edges and the soft grid". Until then the team also compared edges against Sea of Stars (and CrossCode or Chained Echoes where Eastward had no match). From now on **edges and the soft grid follow Eastward only**: how ground is laid out, how an edge steps, corners, rims and lips, faces, feet, the sides of raised ground, outlines, how two kinds of ground meet, water's edge, stairs, cast shadows and plants over edges. This file is the rulebook for those, measured from official Eastward screenshots. Where another vision file disagrees on one of these points, this file wins.

Matt, 21 Oct 09:31: "i don't necessarily want eastwards muted color palate. the game should have it's own color palate that is consistent (and depending on terrain)." So **we take Eastward's edge geometry and its value structure (the lit lip, the dark line and shade under the lip, the dark foot), not its muted colours.** Every rule below is about shape, size and which value goes where; the colours come from the house palette (`house-style.md` 1), one consistent ramp per terrain (meadow, highland rock, snow, sand, ash and so on). Where a rule names a lightness it is a value step on our ramp, not a colour to copy.

Status: study by Claude A's helper on 21 Oct. Measured, not felt: each rule says what was measured and in which shot, with a named evidence crop. The crops are made locally with `python3 scripts/art/eastward_study.py crops NATIVE_DIR OUT_DIR` (`CROPS` in the script gives each one's shot and box) from references that never go into the repository, so neither the screenshots nor the crops are committed.

## 0. How it was measured

**Sources.** The 23 official screenshots the team already had (Steam store pages of Eastward, app 977880, and Eastward: Octopia, app 2305370, and the press page eastwardgame.com/media), plus a search of the same three places for more: the media page holds 12 "features" stills and 10 Octopia stills, all of which turned out to be the same frames as the store screenshots (none new). No fan captures, no videos.

**Native pixel scale, measured per shot.** For each screenshot the edge energy between neighbouring screen pixels was folded by phase for every candidate scale, and the period confirmed with an FFT of the column and row profiles; the shot was then brought down to native pixels by taking the median of the screen pixels inside each native pixel.

| Scale        | Shots (index in the reference folder)                                   | Native frame | Used for rules            |
| ------------ | ----------------------------------------------------------------------- | ------------ | ------------------------- |
| 3 (integer)  | 01, 04, 07, 08, 11, 12, 13, 16, 17, 38, 39                              | 640 x 360    | yes                       |
| 3.3 (zoomed) | 14, 15, 30, 37 (= Octopia-7_Fishing), and 02, 22 (soft, motion-blurred) | 581 x 326    | 15 and 37 only, resampled |
| 3.6 (zoomed) | 03, 06, 09, 10 (combat camera)                                          | 532 x 299    | no                        |
| 2 (integer)  | 05 (1280 x 720 still)                                                   | 640 x 360    | no                        |
| none         | 21 (stretched: 2.67 across, 3 down)                                     |              | no                        |

Eastward's camera zooms in for some scenes, so not every official shot is an integer upscale: 3.3 and 3.6 are the game's own zoom. The integer shots carry the rules; the 3.3 shots were resampled on their measured grid and used only for the pond (37) and the swamp (15), where their numbers agree with the integer shots.

**The yardstick.** The adult (John, feet to crown) is **54 native px** in every shot where he stands upright (55 in 13, 54 in 37 after its 3.3 zoom is taken out; `detail_bar.py` uses the same 54, as 162 screen px). Ours is 25 px (`size-guide.md`). So **k = 25 / 54 = 0.46**: an Eastward length in native px times k is the same length at our scale. Every size below is given both ways: "E 24 px (0.44 A), ours 11". Lines one pixel thick stay one pixel thick at our scale (there is no half pixel): only sizes, spacings and band widths scale.

**Tools.** `python3 scripts/art/eastward_study.py` holds the steps: `scale` (period per shot), `native` (downscale), `crops` (the evidence crops named in this file, made locally), `trace` (an edge traced column by column: how far it strays from a straight line, how long its flat runs are, how big its steps are, and whether it repeats), and `strip` (the colours down a column, as runs: the cross-sections below). The screenshots stay on the machine that measures; the script records the official URL of each.

Crop `01-adult` (`eastward_study.py crops`): The adult, native and 4x.

## 1. The soft grid

**1.1 The tile is 17 native px, laid in pairs of 34.** Everything that repeats on the ground repeats every 34 px: the kerb slabs in 16 (edges at 222, 256, 290, 324, 358, 392), the watermelon rows in 13 (324, 358, 392), the checker paving in 01 (251, 285), and the farm ledge's rim line in 13, whose wobble repeats exactly every 34 px (100 % of columns equal, 77 % at 17). Ours at k: 7.9, which is **our 8 px cell**. So our 8 px soft grid is Eastward's tile at the same character height; keep it.

**1.2 Structures are whole tiles with up to 2 px of slack.** The farm stair is 65 px wide (4 tiles less 3), the dirt path 48 to 50 (3 tiles), crop beds 32 to 34 apart, the swamp's shallow shelf 48 to 50 across. Nothing structural is a fraction of a tile; the slack is in the drawing, not in the layout.

**1.3 The grid shows in the layout and never in the texture.** Plan outlines run along tile lines (the cliff in 12 is a stack of rectangles: its west sides at x 38 and 72, its rims at y 32 and 57), but the textures that fill them (grass mottle, dirt cobbles, boulders) have no visible 17 or 34 px period except where a man-made thing repeats (slabs, beds). Rim wobble may repeat per tile pair because it is short and quiet (1.4); a texture may not.

**1.4 A rim steps one pixel at a time.** Traced along the farm ledge in 13 (105 columns): the rim line strays at most 1 px from straight (range 1.1, sd 0.45), every step is exactly 1 px, flat runs are 1 to 10 px long (median 2, mean 3.4). Ours: the same, in pixels (a 1 px wobble, runs of 1 to 10), because a 1 px step cannot shrink.

**1.5 Diagonals are 45 degree chamfers of single steps; curves are pixel circles.** The farm ledge's east end in 13 turns down to the south in a chamfer 11 px long made of 1 x 1 steps with a 2 px dark edge (04-diagonal). The cliff in 12 has no long diagonals: its plan steps in rectangles. Rounded corners are pixel circles: the sand plateau's outer corner in 39 steps 2, 1, 1, 1 (radius 5); its inner (concave) corner is a 2 to 3 px chamfer. Ours: chamfers in single steps, outer radius 2 to 3, inner chamfer 1 to 2; long diagonals only as a staircase of whole cells (world-rules 2.3).

**1.5a The soft grid, as Matt drew the line (26 Oct 15:36).** With an Eastward forest screenshot (raised grass plateaus with earth ledges, a dirt path, wooden steps): "this is what i mean with soft grid. edges and paths are a bit block like but they are not sharp like minecraft. think about how this could be implemented and do it". What it governs, what it does not, and the measured rules are in "What the soft grid governs" (after section 8). The module is `scripts/art/native/softgrid.py`, the swatch sheet `scripts/art/softgrid_swatches.py`; no zone uses it until Matt approves the swatches.

**1.6 Outlines follow the grid: straight runs, rounded corners, turns at cell lines** (Matt, 21 Oct 11:44, on the first pilot cliff: "i like the rocks on the cliff face here. but remember the grid shape like in eastward"). Every rim, foot, ledge end, side and pool surround is drawn on the 8 px cell (16 art px at 2x). A run goes straight along x or y and wobbles at most 1 px (the lip's wobble, 1.4 and 3.1, not the plan's). It changes direction only at a cell line, so a curve or a diagonal in the plan becomes a staircase of whole cells. A side face is vertical. Corners are rounded pixel circles, about 2 to 3 world px in radius (4 to 6 art px at 2x). This replaces the "organic rim" rule the cliff core used on the morning of 21 Oct (lobes, no straight run over 48 to 64 px), which Matt overruled. Inside the outline the texture has no grid (1.3): the rounded rocks, the lawn's patches and the snow's drifts keep their own shapes. The cliff core snaps every tier to the grid by cell majority (`World._snap`), re-rounds the corners at each density, and `--check` requires at least 70 % of every render's rim columns to lie on a cell line (`rim_steps`, `RIM_ON_GRID`).

Crop `03-ledge` (`eastward_study.py crops`): Rim of the farm ledge.
Crop `04-diagonal` (`eastward_study.py crops`): The chamfered end.
Crop `05-round-corner` (`eastward_study.py crops`): Rounded corner of the sand plateau.
Crop `06-cliff-plan` (`eastward_study.py crops`): Plan of the cliff in 12: stacked rectangles.
Crop `02-tile-kerb` (`eastward_study.py crops`): Kerb slabs in pairs of 34.

## 2. Faces

**2.1 Two heights of face.** A low earth ledge (the farm in 13) is **E 23 to 30 px (0.43 to 0.55 A), ours 11 to 14**: our 12 or 16 low step. A rock cliff (12) is **at least E 70 px (1.3 A), ours 32 or more**: our 32 tier and above. Nothing in the shots sits between (no face of 0.6 to 1.2 A).

**2.2 The low ledge, top to bottom** (13, columns x 4, 30 and 165; lightness L is 0 to 255):

| Band            | E px   | Ours   | Value                                                                                                      |
| --------------- | ------ | ------ | ---------------------------------------------------------------------------------------------------------- |
| Grass lip       | 1      | 1      | one row of the grass a step darker (L 134 under L 170), with a lit row (L 182) one to three rows behind it |
| Rim line        | 1      | 1      | the face's mid-dark (L 100)                                                                                |
| Under-lip line  | 1      | 1      | the face's darkest (L 50 to 56)                                                                            |
| Under-lip shade | 3      | 1 to 2 | three steps back up (L 73, 87, 98)                                                                         |
| Face body       | 5 to 8 | 3 to 4 | the face's mid (L 120), with clods and stones                                                              |
| Foot band       | 5 to 7 | 2 to 3 | dark (L 53 to 73), pebbles and the odd stone                                                               |
| Lower ground    |        |        | starts at once, no gap                                                                                     |

**2.3 The rock cliff, top to bottom** (12, columns x 52 and 95): grass lip; a 1 px rim line (L 81); an **under-lip shade E 8 to 11 px (ours 4 to 5)** in two values (L 49 and 61); an **upper zone of horizontal streaks E 13 px (ours 6)**, where row-to-row change outweighs column-to-column change 1.7 to 1; then **rounded boulders E 12 to 18 px across (ours 6 to 8)**, each lit at its top left (L 105 to 117, highlight 127), dark at its underside, with dark gaps (L 43 to 50) between them, marks as often across as down (ratio 1.0). Six to seven value steps on the face in all. Ours: the under-lip shade (4 to 5 px) and a streak zone of horizontal marks (2 to 6 px) under it follow Eastward; the boulders below are the house look Matt chose on 21 Oct 09:31 (the bake-off's tile swatch), 8 to 18 px across, larger than Eastward's 6 to 8 at our scale. Boulder size is texture, not edge, and at our pixel size a lump needs about 8 px to hold a lit crown, a body and a dark underside. The pilot cliff at 2x (Matt, 21 Oct 11:44, "i like the rocks on the cliff face") draws them as cobbles in bigger clusters, each a calm dome lit at its top-left, with a dark seam only where it meets the cobble above, no outline round every stone, and the odd larger boulder. Warm ochre falls on the lit tops, the crag's body takes the middle tones, and violet-grey stone takes the shade, so the face reads as stone.

**2.4 Marks on a face run across, never down in stripes.** Neither face has vertical bands or columns. The earth face's clods are wider than tall (ratio 0.9: about even); the cliff's streaks lie under the lip and its boulders are round. A vertical line on a face means a real gap (a fissure, the side of a block, 3.2), not texture.

**2.5 The face's value structure is the rule; its colour is ours.** Lit lip, a dark line and shade under it, a mid body, a dark foot. Eastward's faces are olive, plum and ochre; ours take the terrain's ramp (`house-style.md` 1) with these values at tones 4 (lip), 1 then 0 (rim line, under-lip), 1 to 2 (shade), 3 (body), 1 (foot).

Crop `07-cliff-face` (`eastward_study.py crops`): Rock face in 12.

## 3. Lips, feet and sides

**3.1 The lip is a darker row of the top's own ground, wobbling 1 px.** On the farm ledge the grass ends in one row a step darker, then the rim line; small tufts stand up above it on the cliff in 12 (1 to 2 px, every 3 to 8 px), but on the farm ledge the lip is clean. Ours (Matt asked for turf lips without teeth, 21 Oct): the clean form: no blades hanging over the face, a 1 px darker row on the 1 px wobble of 1.4. Overhang: the lip hangs over the face by 0 to 2 E px, so 0 to 1 at our scale.

**3.2 The foot is dark, stony and grown over.** Under the farm ledge a foot band E 5 to 7 px (ours 2 to 3) of the face's dark tones holds pebbles (2 to 4 px) and the odd larger stone; weeds and grass from the lower ground grow up over it 3 to 6 px (ours 2 to 3). There is no lit line at the foot and no gap: the lower ground begins in the next row.

**3.3 The side of raised ground is a narrow band with the darkest line in the picture.** Where a cliff ends west or east (12, x 38 and 72) its side is a vertical edge: 2 to 3 px of rock rim on the outside, then a 1 px line that is nearly black (`#0a0006`, the only near-black in the terrain), broken every few px, then the face. The sand plateau in 39 carries its lip down the side as a band of the same 6 px (light, then a 2 px darker inner line). Ours: a side band of 3 px (2 lit facing west, 2 dark facing east, plus the line), the line our ink, broken.

Crop `09-foot` (`eastward_study.py crops`): Foot of the farm ledge.
Crop `08-side` (`eastward_study.py crops`): Side of the cliff in 12.

## 4. Outlines on terrain

**4.1 Only height changes are outlined.** Rims (rim line plus under-lip line), the sides of raised ground (3.3) and boulders and stones are outlined; ground meeting ground on one level never is (grass to dirt, grass to cobbles, dirt to sand). Water's edge is not outlined either: it has a light line (5.3).

**4.2 Outline colours are the face's own darks,** plum and brown at L 45 to 75, never flat black, except the broken near-black line on a cliff's side. Ours: the family's edge tone (`house-style.md` 2), ink only on the side line.

## 5. Where ground meets ground

**5.1 Grass to dirt: a frayed edge, no outline, no dither.** Traced along the dirt path in 12 (180 columns): the edge wanders in a band 4 to 5 px wide in 1 px steps (46 of 66 steps are 1 px), with a bite or a tuft 6 to 9 px deep about once a tile pair; dark crumbs (1 to 2 px) of the dirt's darkest tone sit along it. The east edge of the farm path in 13 wanders 9 px in steps of 1 to 3. Ours: a band 2 to 3 px wide in 1 px steps, a tuft or bite 3 to 4 px about every 16 px, crumbs of 1 to 2 px, no line.

**5.2 Grass to cobbles or paving: the same frayed grass edge over a laid surface.** The cobble path in 13 is round cobbles 8 to 10 px in two close tones; grass breaks over its edge as in 5.1. Built paving (16) meets the street with a kerb: slabs 34 px long, a lit top row and a 2 to 3 px dark front, a low face of its own.

**5.3 Ground to still water: a small bank and a light line.** The canal bank in 13 (x 60 and 150): the grass lip, a 1 px rim line, an earth face E 4 to 5 px (ours 2), then **a 1 px very light waterline** (L 212) and the water. Under a north bank the water is darker in a band **E 5 to 17 px (ours 2 to 8)** that steps back to the water's body in 3 to 4 steps (pond in 37). Banks of stones (the pond in 37) are stones E 8 to 12 px (ours 4 to 6), each outlined, the waterline light only in the gaps. No foam on still water; white spray only where water falls.

**5.4 Dither belongs to light, never to a boundary.** Checker dither appears only where light or shade fades: sun patches on the paths in 12 and 13, the fade round the pits in 15, the edge of the forest. No material boundary in the studied crops dithers. (This is already the house rule: `house-style.md` 4.)

**5.5 Ground fills are clean** (Matt, 21 Oct 10:52: "your current renders are visually too noisy. compare with eastward. i want it to be cleaner, like eastward"). Eastward's grounds are big calm fields of one tone with a few large soft blotches and sparse clumped tufts; detail is not speckle. Measured on its lawns, yards and verges brought to our scale by area averaging (`detail_bar.clean_counts`, baselines' `clean`), per 16 x 16 square: visible edges between neighbouring pixels (RGB distance over 20) 0.09 to 0.24 of pairs (mean 0.15), lone pixels 0 to 4 % (mean 1.4 %), the two main colours covering 59 to 91 % (mean 68 %), 4 to 15 colours (mean 10.4). Ours must be at least as clean: edges at most the mean plus 4 points, lone pixels plus 1 point, the two main colours at least 90 % of the mean share, at most 25 % more colours plus one. For ground this replaces the detail bar's shape and dressing minimums (they reward noise), and its tones minimum drops to half. The cliff core goes one step further, after the pilot review on 21 Oct ("one main field tone, a few large soft patches one tone apart"). Its lawns carry 3 to 5 tones in a 16 px square, so the per-square tones minimum is reported only. Instead, a 66 x 50 box must show at least four colours that each cover 0.5 % of it (divided by the density, because stamps are drawn at texel size): the field, a patch tone and the dressing.

Crop `10-grass-dirt` (`eastward_study.py crops`): Grass to dirt in 12.
Crop `11-grass-cobble` (`eastward_study.py crops`): Grass to cobbles in 13.
Crop `12-bank` (`eastward_study.py crops`): Canal bank in 13.
Crop `13-pond` (`eastward_study.py crops`): Pond in 37.
Crop `18-dither` (`eastward_study.py crops`): Dither only in light and shade fades, 15.

## 6. Stairs and ramps

**6.1 A stair runs from the lower ground through the face onto the upper floor.** The farm stair in 13: 65 px wide (1.2 A; ours 30, our standard 40 is wider on purpose for the phone), four steps on a 12 px pitch (a 6 px tread, lit at its front and back rows, over a 6 px dark riser), 48 px from the lower ground to the upper floor for a 24 px face: the flight reaches back into the upper tier as far as it rises. Its **top tread is flush with the upper floor** (the rim line runs straight across its back) and **its bottom tread lands on the path**, which starts at its foot. The face continues unbroken either side; the grass lip turns down beside it as its cheek.

Ours (Matt's review of the pilot, 21 Oct: a stair belongs only in the face it climbs): the flight does not reach back across the upper floor. It stands in front of the face, cut into a spur. Its head is flush with the rim and the upper floor runs on flat behind it. A few broad steps of 5 to 6 world px each (10 to 12 art px at 2x) step down to the foot, which lands on the path. Either side, rock cheeks at the upper floor's height end a tread short of the foot and carry the face's rock down beside the steps.

**6.2 Pitch shrinks with a longer flight.** City steps in 01 are on a 5 px pitch (3 tread, 2 riser) in a long flight; the concrete stair in 39 is on 11 px between cheek walls with posts. Ours at k: a short flight 5 to 6 px a step, a long one 3 px.

**6.3 No ramps.** No studied shot has a ramp cut into a ledge; changes of level are stairs, ladders or a path round the end.

Crop `14-stair-farm` (`eastward_study.py crops`): Farm stair in 13.
Crop `15-stair-city` (`eastward_study.py crops`): City stair in 01.

## 7. Cast shadows

**7.1 Thrown to the east, soft-edged, about 40 % darker.** The one clean daylight cast shadow in the integer shots, the palm on the beach in 39, falls to the right and a little up, reaching about 0.6 of the palm's height (some 90 px for a palm of about 145); other scenes set their own sun, so length and lean vary by scene. Its core is 43 % darker than the sand (L 121 against 213), and its edge fades over 4 to 10 px. Things standing on the ground also have a small contact ellipse right under them.

**7.2 Ours keeps the house shadow, softened at its rim.** Eastward's soft edge is its lighting engine; ours stays on the palette (`house-style.md` 6): the core two tones down, the outer 2 px one tone down (the nearest the ramp can come to the 4 to 10 px fade at our scale), thrown east and down. Under a face, the foot band (3.2) is the shadow; no separate cast shadow below a cliff.

Crop `16-shadow` (`eastward_study.py crops`): Palm shadow in 39.

## 8. Plants and props over edges

**8.1 Edges are broken by things that grow and stand there, not by noise.** Along the farm ledge in 13 a bush, a fern or a sapling crosses the rim and the face about every 34 to 68 px, each overlapping 4 to 12 px (ours 2 to 6) and casting its shade on the face; boulders sit on the lip (13) and on the grass beside the foot; vines hang from the cliff's rim (12). Between them the rim stays clean (1.4).

**8.2 The foot is grown over, the face mostly not.** Weeds 3 to 6 px tall rise from the lower ground over the foot band; on the face itself only rooted plants (a fern in a crack, a vine from the rim).

Crop `17-plants` (`eastward_study.py crops`): Plants over the farm ledge in 13.

## 9. Summary table

E is Eastward's native px at an adult of 54; ours is at an adult of 25 (k = 0.46). One-pixel lines stay one pixel.

| #   | Rule                     | Eastward (measured, shot)                                                                                                          | Ours                                                   |
| --- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 1.1 | Tile                     | 17 px, pairs of 34 (16, 13, 01)                                                                                                    | 8 px cell                                              |
| 1.2 | Structures               | whole tiles, 2 px slack (13)                                                                                                       | whole cells                                            |
| 1.4 | Rim wobble               | 1 px, 1 px steps, runs 1 to 10, median 2 (13)                                                                                      | same in px                                             |
| 1.5 | Diagonals, corners       | 45 degree chamfer of 1 x 1 steps; outer radius 5, inner chamfer 2 to 3 (13, 39)                                                    | single-step chamfers; radius 2 to 3; chamfer 1 to 2    |
| 1.6 | Outlines on the grid     | runs along tile lines, rectangles stacked (12); Matt, 21 Oct 11:44                                                                 | straight runs, turns at cell lines, vertical sides     |
| 2.1 | Face heights             | low ledge 23 to 30 (0.43 to 0.55 A); cliff 70 and up (1.3 A+) (13, 12)                                                             | 12 or 16; 32 and up                                    |
| 2.2 | Low ledge, top to bottom | lip 1, rim 1, dark 1, shade 3, body 5 to 8, foot 5 to 7 (13)                                                                       | 1, 1, 1, 1 to 2, 3 to 4, 2 to 3                        |
| 2.3 | Cliff                    | under-lip shade 8 to 11, streak zone 13, boulders 12 to 18 (12)                                                                    | 4 to 5, 2 to 6, boulders 8 to 18 (the house look, 2.3) |
| 2.4 | Marks                    | across or round; no vertical stripes (12, 13)                                                                                      | same                                                   |
| 2.5 | Values                   | lit lip, dark line, shade, mid body, dark foot                                                                                     | tones 4, 1 then 0, 1 to 2, 3, 1 of the terrain's ramp  |
| 3.1 | Lip                      | darker row of the top ground, overhang 0 to 2 (13)                                                                                 | 1 px darker row, overhang 0 to 1, no teeth             |
| 3.2 | Foot                     | dark band 5 to 7 with pebbles, weeds 3 to 6 over it (13)                                                                           | 2 to 3, weeds 2 to 3                                   |
| 3.3 | Side                     | 2 to 3 px rim plus a broken near-black line (12); lip band down the side (39)                                                      | 3 px band, broken ink line                             |
| 4   | Outlines                 | only height changes and stones; face's own darks, L 45 to 75                                                                       | family edge tones; ink only on sides                   |
| 5.1 | Grass to dirt            | frayed band 4 to 5, 1 px steps, a tuft or bite 6 to 9 per 34, crumbs (12, 13)                                                      | band 2 to 3, tuft or bite 3 to 4 per 16, crumbs        |
| 5.2 | Grass to paving          | frayed grass over cobbles 8 to 10; kerb with lit top, dark front 2 to 3 (13, 16)                                                   | cobbles 4 to 5; kerb front 1 to 2                      |
| 5.3 | Still water              | bank face 4 to 5, 1 px light waterline, dark band 5 to 17 under a north bank in 3 to 4 steps (13, 37)                              | bank 2, 1 px line, band 2 to 8                         |
| 5.4 | Dither                   | light and shade fades only (12, 13, 15)                                                                                            | same                                                   |
| 5.5 | Clean ground             | calm fields, soft blotches, clumped tufts: edges 0.15, lone 1.4 %, two main colours 68 %, 10 colours a 16 px square (at our scale) | at least as clean (detail_bar ground)                  |
| 6.1 | Stairs                   | through the face, top flush, bottom on the path; 4 steps at 12 (6 tread, 6 riser) for a 24 face; width 1.2 A (13)                  | in a spur before the face; 5 to 6 a step; width 40     |
| 6.2 | Long flights             | pitch 5 (01), 11 between cheek walls (39)                                                                                          | 3 to 5                                                 |
| 6.3 | Ramps                    | none                                                                                                                               | none                                                   |
| 7   | Cast shadows             | east, about 0.6 x height, 43 % darker, soft 4 to 10 (39)                                                                           | east and down, core two tones, rim one tone 2 px       |
| 8   | Plants over edges        | one per 34 to 68 of rim, overlap 4 to 12 (13)                                                                                      | one per 16 to 32, overlap 2 to 6                       |

## 10. What this changes

- **Sea of Stars, CrossCode and Chained Echoes are no longer references for edges or the soft grid.** Older notes that compare an edge, a face, a corner or a cliff with them are history. The detail bar's numbers (`detail_bar.py`) are not edge rules and stay as they are; its stream baselines include three Sea of Stars reaches, which Claude A may want to replace with Eastward canals.
- **Already in line:** the 8 px cell (1.1), rounded corners and staircase diagonals (world-rules 2.3), the 12 and 16 low step and the 32 tier (world-rules 3.2), dither only for fades.
- **To change in the generators:** faces with vertical bands or columns (2.4); grass lips with hanging teeth (3.1); a lit line at a foot (3.2); outlines between ground types on one level (4.1); hard straight path edges (5.1); stairs that do not reach the upper floor or the path (6.1).

## What the soft grid governs (26 Oct)

Matt, 26 Oct 17:46: "make sure to really refine the soft grid before you implement it everywhere. which parts stay as before and which parts needs to adhere to the softgrid (remember that wells for example should still be round ...). most props should probably stay as before (detailled of course) but the ground and the placement of the props changes. consider what natural terrain looks like under these constraints". 17:48: "eastward is really the example the soft grid should follow, of course adapted to my pixel density etc."

**Conversion.** At the same character height (Eastward's adult 54 native px, ours 74 art px at density 3) k = 74 / 54 = 1.37, so Eastward's 17 px tile is 23.3 of our art px: **our cell, 8 world px = 24 art px, is Eastward's tile** (1.1). Every number below is given as Eastward native px (E), in tiles, and ours in cells or art px. Measured on the local references (`eastward_study.py native`, scale 3 or 3.3), on `refs-matt/eastward-forest-ledges.png` ("Strange Forest", 1.8 screen px a native px, from John's height of 97 screen px) and on Matt's 26 Oct screenshot. Corner radii come from `edges.corners` run on colour masks of the frames; the rest are column and row traces or visual measures on 4x crops with the 17 px grid laid over them.

### Governed: plans of whole cells, rounded corners, lumpy edges

- **Boundaries between ground materials** (grass, dirt, sand, paving, snow). In 39 the sand plateau is a union of rectangles with corners of radius 2.4 E (0.14 tile); the grass patch on it is irregular and not on the grid (texture, below).
- **Paths, roads and plazas, at constant width.**
  - In 13 the dirt paths are 3 tiles wide all along (rows across the horizontal path: 48 to 54 E with the grass breaking in). Their T-junction and turns round off at 6.4 E (0.38 tile). Their edges stray 1.6 to 1.8 px (sd) in 1 px steps, with grass tufts over them (5.1).
  - Ours: a main path or road 3 cells; a lane or side path 2 cells. That is a proposal: the local refs have no 2-tile path. Turns round off at 0.4 cell outer and 0.25 inner (`R_TURN_OUT`, `R_TURN_IN`). A route runs in long straight runs: a slant becomes a few runs of about five cells, never a one-cell staircase.
- **Raised ground: plateaus, ledges, cliffs, steps cut into them.**
  - The low earth ledge is E 23 to 30 px, ours 12 world (2.1, 13). Strange Forest's ledges are taller (68 E, 4 tiles) with outer corners of about 11 E (0.65 tile), a knobbly face of rounded clods and a lumpy lip. Ours: low ledges round at 0.65 cell outer, 0.4 inner.
  - Rock cliffs are at least 70 E, ours 32 world (2.3, 12). Their plan is stacked rectangles with tight corners (12); ours round them at 0.25 cell.
  - Steps follow Strange Forest and Matt's 26 Oct screenshot: four log treads on a 14 E pitch, set into the face with earth cheeks either side. The farm stair in 13 is four steps on a 12 E pitch (6.1). Ours: a flight 3 cells wide, four treads.
- **Water plans: ponds, pools, lake shores, coast, river courses.**
  - In 37 the pond is a large rounded shape lined with stones. Ours: a union of cells rounded at 1.4 cells outer, 0.8 inner. Banks follow 5.3.
  - In 15 the swamp's channels and shelves are unions of rectangles of several sizes (1 to 6 tiles) with corners of 2.4 E (0.14 tile).
  - **The local refs have no river bend.** The closest analogues are those channels (15) and the canal's straight edge (13). Proposal: a river's plan in cells, 3 to 4 cells wide (changing in whole cells), bends rounded at 1 cell outer and 0.6 inner, banks lumpy as a ledge's lip.
- **Garden beds and fields.** In 12 and 13 a bed is a frame with a raised soil rim and rounded plots one tile each, corners tight. Ours: the frame in cells, rounded at 0.15 cell, one mound per cell.
- **Footprints of built things** (buildings, walls, fences, docks, bridges, platforms). They are whole tiles with up to 2 E of slack (1.2). Paving meets the street with a kerb of 34 E slabs (16, 5.2). Ours: whole cells, with built corners at 0.15 cell (Eastward 0.14).

### Placement on the grid

Every prop's foot anchor lies on a cell: x on the cell's centre or its half (4 world px), y on the cell line (8). Eastward's lamps, posts and benches stand on tile lines (13, 12). Rows and clusters align: beds, fence posts, stalls. Small clutter is placed freely: pebbles, flowers, tufts, leaves and debris (13's stones and flowers lie anywhere). `grid_snap --check` and `logic.off_grid` hold the anchors.

### Not governed: they keep their own organic shapes

- **Props' own shapes.** Wells stay round, as do barrels, carts, lamps, benches, rocks and boulders, stumps and logs (Matt, 17:46: "wells for example should still be round").
- **Trees and bushes.** Trunks stand on cells and crowns are organic (02, 22: huge trunks, crowns and undergrowth free).
- **Plants, characters and creatures.**
- **Texture inside fills:** cobbles, mottle, clods and the lawn's blotches. Blotches are low contrast, one hue family, soft and irregular (37's lawn, 5.5).
- **Shadows:** they follow their casters.
- **Light pools** (02's sun flecks), **water surfaces and ripples**, and **effects**.

### Natural terrain under the constraints

- **Landforms are unions of rectangles at several sizes.** Use 1, 2 and 3 or more cells, never a uniform staircase or repeated identical blocks. Seen in the cliff in 12, the shelves in 15 and the sand plateau in 39.
- **Notches and spurs are whole cells** (15, 39).
- **Long straight runs are broken.**
  - Lumps 8 to 20 art px long and 1 to 3 px deep (Strange Forest's lips; the path edges in 13, sd 1.6 to 1.8).
  - Overhangs of turf, and breakers on 10 to 20 % of the edge: roots, tufts, rocks straddling the rim, plants spilling over (12, 13, Strange Forest).
- **Corner radius follows the material.**
  - Earth ledges and ponds are round: 0.65 cell (Strange Forest) to 1.4 cells (37).
  - Paths turn at 0.4 cell (13).
  - Built edges, sand and swamp shelves are tight: 0.14 tile in 39 and 15, ours 0.15.
- **Rivers:** see the proposal above.
- **Lakes and ponds** are rounded unions (37).
- **Forest floors:** trunks on cells, free undergrowth (02, 22).
- **Transitions between ground types** are soft-edged and low contrast. There is no outline between grass and dirt (5.1). Patches inside a surface are its own sibling hues, frayed, never a geometric disc (37, 13).

### The painters (26 Oct, second pass)

The plans come from `softgrid.py`; what fills them and what happens where they meet is painted by `scripts/art/native/softground.py`, at Eastward's level of detail rather than as flat fills: the lawn (a calm field, damp patches of long dark tufts and dry warm ones fading through a checker, clumped tufts with dark roots and lit tips, flowers in groups), packed earth (rounded clods 10 to 15 px with soft joints, ruts, pebble clusters, dry blades, crumbs), a sunken edge (turf lobes over the dirt, a shadow under the north lip, the south lip lit, tufts leaning out, stones straddling), raised ground (a lit band and an overhanging grass lip with hanging tufts, the under-lip shade, a face of rounded clods or of boulders under a layer of flat stones with moss caps, roots or vines, a dark foot with pebbles and fallen rocks, weeds, a cast shadow on the lower ground), log steps, water (an earth bank under the north lip, a light waterline, a depth band under the bank and a deeper middle, lit shallows, ripples, stones, rushes and lilies off the shore), sand with ripple drifts and a wet band and swash at the sea, a raised bed frame with a plot and a crop per cell, flags with a kerb and its low face, and the forest floor (canopy shade with dapples, litter, roots, bare earth at the trunks). `scripts/art/softgrid_swatches.py` shows each, and every swatch passes `review:asset` (as ground) and `review:scene` with no findings. Ripples on water shores stay off the bank outline (the soft-grid gate counts plant blades over the waterline as teeth), so rushes stand in the shallows.

`detail.corner_radius` follows these numbers. A sharp corner is under 0.12 cell, below Eastward's tightest ground corners at 0.14 tile. A pure square corner measures under 0.08.
