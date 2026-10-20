# The world plan (v2): sizes first, then the map

Matt, 20 Oct 01:05: "All of these need redesigns pretty much, to fit the newly established soft grids. also consult the other games mentioned for world buildings how large parts of the maps should be and how they are attached together and how you can create interesting spaces." At 10:32, on v1 of this plan: "also dont just redesign the current map exactly, really think deeply of the sizing of everything and the map".

**Status: a plan, partly decided.** Matt decided decisions 1, 2, 3, 5, 6 and 7 on 20 Oct at about 10:50 (section 7); the rest are open. v1 redrew each region inside today's 320 x 576 tiles. v2 starts from the size of a person and works up: how big a cottage, a street, a farm, a harbour, a town, a castle and a city block must be at the true scale; what the phone shows; whether the zone grid should stay; and only then the shape of each region. It keeps v1's lessons from the reference games (section 2) and replaces v1's region plans.

It builds on, and does not repeat:

- `verticality.md` (branch `claude-a/verticality-study`): the 8 px soft grid (Matt decided it), the five rules, the terrace toolkit, and the scale table (an adult is 25 px, a door 32, a storey 32, a shop storey 44, a cottage about 96 to the ridge, a tree about 90).
- `art-style.md` on main: Eastward's level of detail is required; each setting takes its forms and palette from its own world (Matt, 20 Oct 10:15).
- `prop-logic.md` and the prop audit (draft PR #97): what each prop needs and which props are kept or redrawn. Section 4 here names each place's trade; #97 says what that means prop by prop.
- `world-unlocks.md` (draft PR #95; decided: nine ways, one a day) and the ways catalogue `lib/world-ways.ts` (draft PR #118). Section 5 places the nine ways on the new map.
- `world-rules.md`, `world-ports.md` and `world-atlas.md` stay the rulebook.

The block-out images that go with this file are drawn by a script (1 px per 8 px cell, flat colours per kind of ground, tiers shaded, walk distances measured on them). They are not in the repository; how to look at them is in section 4.

## 0. In short

1. **Keep the zoom.** The phone shows 12 adults across, as Eastward (12.8) and Stardew (15) do, and about 19 adults between the HUD and the hotbar, more than twice their height. Our width is right for the scale table; the extra height means the world is composed along north and south.
2. **Drop the zone grid as the unit of the world.** Draw each region as one continuous canvas of any size on the 8 px grid; the build cuts it into small square render tiles (256 px) that the renderer streams; "zones" become named areas of any shape, used for names, the map and saves. Seams between zones disappear, and the decoded memory on a phone falls from 24 to 47 MB to about 9 to 12 MB.
3. **Size every place from the people in it.** A cottage plot is 128 x 176 px, a village square 240 x 176, a farm 384 x 288, a halt 256 x 160, a harbour 544 x 352, a castle 400 x 400, a city block 208 x 272. Everyday places stay within 15 seconds' walk of the hut's door.
4. **The world grows by about a quarter in walkable ground (22 to 27 zone-areas), not in screens.** The valley gets a real village, farm and harbour village at true scale; Cogsworth nearly doubles and gains its hill and terminus; Neon shrinks its canvas by a quarter but gains walkable streets; Sunstone becomes one continuous land from the oasis to the springs; the isles, Halcyon and Lumen keep their size.
5. **The nine ways stay where #95 and #118 put them**; on canvases they are cell sets, not zone seams.

## 1. Sizing

### 1.1 Yardsticks

| Measure            | Value                                                                         | Where it comes from                                                        |
| ------------------ | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Adult resident (A) | 25 px                                                                         | `verticality.md` 5                                                         |
| Companion          | 24 px tall                                                                    | `lib/occlusion.ts` (20 x 24 body)                                          |
| The 8 px grid      | a third of an adult; a zone today is 40 x 72 cells                            | `verticality.md` 4f                                                        |
| Walk speed         | **40 px a second** (1.6 A a second) by tap; 52 by the keys                    | `SPEED` and `KEY_SPEED` in `components/atlas-walk.tsx` (main at `7e0992e`) |
| So                 | 1 cell in 0.2 s; 100 px in 2.5 s; a 320 px zone across in 8 s, down in 14.4 s |                                                                            |

### 1.2 What the phone shows, and whether the zoom is right

`lib/pixel-scale.ts` makes one art pixel a whole number of device pixels, aiming at `ART_ACROSS = 300` art pixels across. On a 402 x 874 phone at 3x that is 4 device pixels (1.33 CSS px) per art pixel:

| Phone                                     | Device px per art pixel | Art px shown | In adults   |
| ----------------------------------------- | ----------------------- | ------------ | ----------- |
| 402 x 874 at 3x (iPhone 15 Pro class)     | 4                       | 301 x 655    | 12.0 x 26.2 |
| 360 x 800 at 3x (common Android)          | 4                       | 270 x 600    | 10.8 x 24   |
| 430 x 932 at 3x (Pro Max class)           | 4                       | 322 x 699    | 12.9 x 28   |
| The 640 px column at 2x (tablet, desktop) | 4                       | 320 across   | 12.8 across |

The floating HUD and hotbar cover about 120 CSS px each on a 402 x 874 phone (safe-area insets plus `hudBarHeight` and `hotbarHeight` at `u` = 1.33), so about **470 art px, 19 adults, are clear** between them.

**Observation, measured on official screenshots** (an adult-height grid laid over each 1920 x 1080 image; a cell is one adult; sizes in our px are cells x 25):

| Game           | Screen in adults | Shot               | What it measures                                                                                                |
| -------------- | ---------------- | ------------------ | --------------------------------------------------------------------------------------------------------------- |
| Eastward       | 12.8 x 7.2       | [eastward/12]      | a house 3.7 A wide and 3.1 A from foot to ridge; a front yard 1 A deep; a lane 1 A; a vegetable bed 4 A x 1.3 A |
| Eastward       |                  | [eastward/01]      | facades 2 to 2.6 A wide; a stair 1.3 A wide; three walking heights on one screen                                |
| Eastward       |                  | [eastward/08]      | a station building 4.5 A wide, a platform 4.5 x 2 A, a track 1 A, the whole halt about 9 x 5 A                  |
| Stardew Valley | 15 x 8.4         | [stardew/07]       | a farmhouse 4.5 A wide with a 1 A porch; crop blocks 1.5 A square; a well 1.5 A                                 |
| Stardew Valley |                  | [stardew/11]       | a smithy 2.5 A wide and 4 A to the ridge; its work yard 4 A wide behind a fence                                 |
| Moonlighter    | 20 x 11          | [moonlighter/02]   | a street 2 A wide; a house 4.5 A wide; the town plaza more than 15 A across                                     |
| Sea of Stars   | 13.6 x 7.7       | [seaofstars/38]    | a harbour boardwalk 2.5 A deep, its posts about 4 A apart, the town stacked on the cliff behind                 |
| Chained Echoes | 16 x 9           | [chainedechoes/16] | a canal 1.6 A wide between quays 2 A deep stacked with crates; a town house 4.6 A wide                          |

(Keys as in `research/world-references.md`, which lists every image's official URL.)

**Is the zoom right?** Yes, for this scale. Across, we show what the references show (12 A against 12.8 to 15), so a cottage is a quarter of the screen's width in both. Each adult is 33 CSS px tall, a 34 art px hit box is 45 CSS px (the 44 px rule just holds), and a door is 19 x 43 CSS px. Zooming in one step (5 device px per art pixel, 241 art px across) would show only 9.6 A, cut a village square (240 px) to the screen's whole width, and make every walk feel longer; zooming out one step (3 device px, 402 art px, 16 A) would drop hit boxes under 44 px. **Recommendation: keep `ART_ACROSS` at 300.**

What changes is composition. We see more than twice as far north and south as the references, so a reference "screen" of content is a third of our view. Landmarks, approaches and reveals run along north and south; side pockets run east and west.

_If Matt wants a different zoom later_, the renderer needs: `ART_ACROSS` in `lib/pixel-scale.ts` (the camera, its clamps and the mount margins already work in art px); and, because the same unit `u` sizes the HUD and the hotbar, a separate world scale so the interface does not grow with the world.

### 1.3 Pokémon's exact sizes (from v1)

From the disassembly's map table ([pret/pokered, `constants/map_constants.asm`](https://github.com/pret/pokered/blob/master/constants/map_constants.asm)): a block is 32 px, two tiles of one person each, so a block is 2 x 2 A.

| Place                               | Blocks        | In A      | In our px              | Walk across (ours) |
| ----------------------------------- | ------------- | --------- | ---------------------- | ------------------ |
| Pallet Town, Lavender Town          | 10 x 9        | 20 x 18   | 500 x 450              | 12.5 s             |
| Viridian, Pewter, Cerulean, Saffron | 20 x 18       | 40 x 36   | 1000 x 900             | 25 s               |
| Celadon                             | 25 x 18       | 50 x 36   | 1250 x 900             | 31 s               |
| Route 1                             | 10 x 18       | 20 x 36   | 500 x 900              | 22.5 s             |
| Routes 3, 4                         | 35 and 45 x 9 |           | 1750 and 2250 long     | 44 and 56 s        |
| All of Kanto outdoors               |               | 43,380 A² | about 147 of our zones |                    |

Pokémon's houses are only about 2 A wide, so its towns are emptier than ours will be; read these as upper bounds for how far a town spreads.

### 1.4 The sizing table

Our sizes are built from the scale table's parts (doors, storeys, a cottage of about 96 px to the ridge, an 8 px grid) and checked against the observations above. Walk-seconds at 40 px a second.

| Thing                                                | Size (px)                                                        | Cells   | Adults    | Walk across | Built from                                              | Reference (observation unless sourced)                          |
| ---------------------------------------------------- | ---------------------------------------------------------------- | ------- | --------- | ----------- | ------------------------------------------------------- | --------------------------------------------------------------- |
| Cottage (house)                                      | 80 wide, 96 to the ridge; foot band 80 x 48                      | 10 x 12 | 3.2 x 3.8 | 2 s         | scale table                                             | Eastward 3.7 x 3.1 A; Stardew farmhouse 4.5 A wide              |
| Cottage plot                                         | 128 x 176: 16 px each side, 32 front garden, house, 48 back yard | 16 x 22 | 5.1 x 7   | 3.2 s       | house + yard + washing line + woodpile                  | Eastward: house, 1 A yard, 1 A lane ≈ 5 x 5 A                   |
| Village lane                                         | 24 to 32                                                         | 3 to 4  | 1 to 1.3  | 0.7 s       | two people pass                                         | Eastward lane 1 A                                               |
| Town street, frontage to frontage                    | 48                                                               | 6       | 2         | 1.2 s       | a cart and a walker                                     | Moonlighter street 2 A                                          |
| City street with pavements                           | 96 (64 road, 16 each side)                                       | 12      | 3.8       | 2.4 s       | a car each way                                          | Eastward pavements about 1.3 A per tier                         |
| Stair (a module in a face)                           | 48 wide, 32 to 40 high                                           | 6       | 2         |             | `verticality.md`                                        | Eastward 1.3 to 2.4 A                                           |
| Village square                                       | 240 x 176                                                        | 30 x 22 | 9.6 x 7   | 6 s         | well at the centre, stall, benches round, four roads in | Moonlighter's plaza more than 15 A (a bigger town)              |
| City plaza                                           | 352 x 248                                                        | 44 x 31 | 14 x 10   | 9 s         |                                                         | Moonlighter's plaza                                             |
| Field block                                          | 96 x 64 to 112 x 80                                              | 12 x 8  | 3.8 x 2.6 |             | rows with walkable gaps                                 | Stardew 1.5 A blocks; Eastward beds 4 x 1.3 A                   |
| Farm (house, barn, yard, four fields, windmill)      | 384 x 288                                                        | 48 x 36 | 15 x 11.5 | 10 s        |                                                         | Stardew's farmyard fills a 15 x 8.4 A screen                    |
| Halt (station house, platform, one track, goods end) | 256 x 160                                                        | 32 x 20 | 10 x 6.4  | 6.4 s       | platform 192 to 240 x 24                                | Eastward's halt about 9 x 5 A                                   |
| Junction (two lines, square in front)                | 512 x 128 plus its square                                        | 64 x 16 | 20 x 5    | 13 s        |                                                         |                                                                 |
| Harbour (quay, basin, three jetties, slip, sheds)    | 544 x 352                                                        | 68 x 44 | 22 x 14   | 14 s        | quay 48 deep; jetties 64 to 128 long                    | Sea of Stars boardwalk 2.5 A deep; Chained Echoes quays 2 A     |
| Village (12 to 16 houses, square, shops, green)      | 640 x 560                                                        | 80 x 70 | 26 x 22   | 16 s        | about 12 plots, a square, three streets                 | Pallet Town 500 x 450 (three houses); a Pokémon city 1000 x 900 |
| Fishing hamlet                                       | 480 x 160 above its quay                                         |         |           | 12 s        | five or six cottages up one road                        |                                                                 |
| Castle (two wards, keep, gatehouse, curtain wall)    | 400 x 400 inside its moat                                        | 50 x 50 | 16 x 16   | 10 s        | keep 80 to 128 wide, walls 16                           | (no reference shot; inferred from parts)                        |
| Desert town (one street, eight false fronts)         | 544 x 320                                                        | 68 x 40 | 22 x 13   | 14 s        | fronts 64 to 96 wide, boardwalks 12                     |                                                                 |
| City block (between streets)                         | 208 x 272                                                        | 26 x 34 | 8.3 x 11  | 5 s         | four facades a side, back to back                       | Eastward facades 2 to 2.6 A                                     |
| A clearing or pocket                                 | 96 to 160 across                                                 |         | 4 to 6    | 3 s         |                                                         |                                                                 |

### 1.5 What follows from the sizes

1. **Everyday places within 15 seconds of the hut's door.** The stall, the square, the library and the spring pool are 8 to 14 s away in the block-out; the halt and the ring 19 s, the mill 21 s; the harbour is a trip (36 s).
2. **A town is one to two screens tall and two screens wide.** At 12 A across, a village of 26 A is about two phone widths, so you see its square and two of its streets at once, never the whole town.
3. **One beat every third of the view** (about 190 px, 5 s), as v1 said; the sizes above make this natural: a cottage plot, a square or a halt is itself a beat.
4. **Frame is cheap; walkable ground is what costs art.** Sea, peaks, the mesa and old forest around a region need detail only at their edges, so a region's canvas may be larger than its walkable ground.
5. **Fewer, truer buildings.** The village holds about 14 buildings, Cogsworth about 18, Dust Gulch 9, the city about 40 in nine blocks. Each is drawn to Eastward's level of detail (art-style.md), so the count is also the art budget.

## 2. The lessons from the reference games (kept from v1)

**How areas attach.** A hub in the middle with districts on its edges (Pelican Town's four exits; Hyper Light Drifter's town "smack dab in the center of the world" with four directions, three open at first). Buffers of shared character between districts (Link's Awakening's buffer screens). Chokepoints where a region changes (Pokémon's gatehouses; Skyarrow Bridge with a gate at each end and the city seen across the water). Almost everything reachable, held together by small walls (A Link to the Past: "only 6 [of 256] cannot be reached"). One-way drops and shortcuts back (Pokémon's ledges; TUNIC's shortcuts that "expand your idea of the space"). Vehicles for the far places (Eastward's trains; Chained Echoes' airship). Loops, not trees.

**How spaces get interesting.** Small pockets often (Sea of Stars: "all these small pockets"); the camera chooses when you see the landmark (TUNIC); one hidden passage makes every wall a question; dense towns invite (Eastward); height carries the composition.

**How worlds gate.** A believable obstacle being mended (Snorlax across Route 12; Stardew's bridge debris, earthquake pass, Quarry bridge and the large log at the Secret Woods); firm, not hard gates (TUNIC); an order with no dead ends.

**The rules at our scale** (inferred; numbers to tune in play):

1. An area is one character, one landmark and one node, 8 to 30 s across. A region holds 3 to 9 areas.
2. Something at the companion's scale every 5 s of walking; never 7 s of nothing.
3. Main ways and sightlines run north and south; pockets east and west.
4. Each area's landmark stands in its north third and is seen from the area before.
5. Every region of four areas or more has a loop; every area has two ways in except deliberate pockets.
6. Inside a region, areas join by open land; regions and gated areas join at one chokepoint or behind a drawn barrier on every way in.
7. Arrive at an edge, see the middle.
8. Two to four tiers per region; at most two full tiers and one low step on screen.
9. Busy and quiet areas alternate; a region's entrance is a corridor that opens into a reveal.
10. One to three secret pockets per region, holding a view, a resident or a story detail, never a reward.
11. Ways are things being mended at chokepoints; once open, open for good.
12. Density over extent: no new ground unless it adds a loop or a missing kind of place.
13. Every place has a trade, and the trade is drawn (producer, way, consumer: `prop-logic.md`).
14. Structure on the grid, texture off it.

v1's full text, with every quotation and its source, is in this file's history (commit `7c96dae`); the sources are listed again at the end.

## 3. The structure: from fixed zones to region canvases

### 3.1 What we have

Every region is a fixed grid of 320 x 576 zones (`LAYOUT` in `scripts/art/zones.py`, exported as `regionLayout`). Each zone has its own ground picture (saved 4x: 1280 x 2304, **11.8 MB decoded**), its own walk grid in 4 px cells, its stands and props. `lib/region-walk.ts` lays the zones' walk grids side by side into one region grid; `zonesToMount` mounts whole zones round the camera (two to four at a time, **24 to 47 MB**); `frames.PORTS` and `world_lint.py` make borders match across seams; a prop may not cross a seam. The isles and the Frostline already draw their land whole and cut it into zones afterwards.

The grid made sense for the first prototype. It now costs us: every seam needs a port, a border check and a border painter; props cannot straddle a seam; areas have to be 320 x 576 whether a place needs a halt or a city; the 4x zone picture is the largest memory cost in the app. Matt (19 Oct): "the world does not need to be divided into screen sized sections".

### 3.2 The options

| Option                                 | What it is                                                                                                                          | For                                                                            | Against                                                                            |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| A. Keep 320 x 576 zones                | today                                                                                                                               | no work                                                                        | seams, ports and border painting stay; sizes forced to the tile; memory stays high |
| B. Bigger zones (640 x 1152)           | four of today's zones in one                                                                                                        | fewer seams                                                                    | 47 MB per zone at 4x; still a fixed size; same seam machinery                      |
| C. Smaller zones (160 x 288)           | a quarter of today's                                                                                                                | finer mounting                                                                 | four times the seams and ports                                                     |
| **D. Region canvases, streamed tiles** | each region is one canvas of any size on the 8 px grid; the build cuts it into 256 x 256 render tiles; areas are named shapes on it | no seams inside a region; sizes follow the place; props anywhere; memory falls | the largest change: generators, exports, region walk, mounting, saves              |

### 3.3 The proposal (D)

**Authoring.** Each region generator draws one canvas (for example the valley at 1280 x 2688) in region coordinates, on the 8 px grid, with the terrace toolkit. It declares its **areas** as rectangles or cell masks on the canvas (`garden`, `town`, `harbour` and so on; names kept where they exist today), its stands, props, tiers, terrain and ways' barriers, all in region pixels. `LAYOUT` becomes `REGIONS = {id: (width, height)}` plus `AREAS`.

**Build.** `zones.py` keeps one build per region: the ground is cut into **256 x 256 px tiles** (32 x 32 cells), saved at 2x (512 x 512 PNG, 1 MB decoded each) or at 1x with nearest-neighbour scaling if that is crisp on iOS, Android and the web (a test; art-style.md already asks for it). Props stay sprites in region coordinates, sorted by foot. Exports per region: size, walk grid (one RLE grid in 4 px cells, as today), terrain, tiers, areas, stands, props, tiles, ways' cells.

**Renderer** (`components/atlas-walk.tsx`). The camera and taps already work in region pixels. Mounting changes from "zones the camera sees" to "tiles the camera sees plus a 24 px margin": at 301 x 655 art px that is at most 3 x 4 = 12 tiles, usually 9, so **9 to 12 MB at 2x (3 MB at 1x) against 24 to 47 MB today**. `zoneReach` and the 48 px overhang rule go: a tall prop is a sprite like any other. The zone name under the HUD becomes the area name, with the same hysteresis.

**`lib/region-walk.ts`.** `regionWalk` reads the region's one grid instead of stitching zones; `tileAt` becomes `areaAt`; `zonesToMount` becomes `tilesToMount`; `tileOrigin`, `GARDEN_OPENINGS` and the garden's edge spans go (the garden is part of the valley's canvas, so the hub's moved grid in `lib/home-hub.ts` becomes an offset only). Decks (`regionLevels`, `deckAt`) carry over in region pixels.

**What goes.** `frames.PORTS` and `zonePorts` inside a region (seams no longer exist; the ways' barriers become cell sets), the border-continuity lint (check 10), `beyond()` between a region's zones (the frame is part of the canvas). What remains between regions is the journey.

**Saves.** A `WorldSpot` already holds a region and a point; `lib/world-layouts.ts` gains one layout version that maps each old zone to its area and each old stand to its new stand, so a saved spot lands at the same place. `visited` keeps its ids where an area keeps its name (most do) and maps the rest (`hill`, `terminus` are new; `waterfront` and `point` fold into `docks` and the Skyport). The ways catalogue (#118) changes from zone ids to area ids and barrier cells.

**Checks.** `lib/region-walk.test.ts`, `lib/home-hub.test.ts`, `lib/world-ways.test.ts` and the hub block of `scripts/check-garden.cjs` move to region coordinates. New: every tile exists for every canvas cell; the mounted set covers the view at every window size; areas cover every walkable cell; memory per frame under a budget.

**Cost and risk.**

| Part                                          | Owner                                | Size                | Risk                                                                                                                     |
| --------------------------------------------- | ------------------------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Region build, tile cutting, exports           | A                                    | one PR              | build time and file count (the valley is 5 x 11 = 55 tiles); mitigated by building only changed regions                  |
| Renderer mounting by tile, area names         | A                                    | one PR              | a seam between render tiles (sub-pixel gaps); tiles are whole art pixels and snapped to device pixels as zones are today |
| Region walk, hub offset, saves, tests         | A, with Codex for `lib/save-data.ts` | one PR              | saved spots and visited lists; covered by the layout-version mapping and tests                                           |
| Each region's generator in region coordinates | the region's lane                    | part of each redraw | none extra: the redraw happens anyway (isles and Frostline already work this way)                                        |
| 1x pictures with nearest-neighbour scaling    | A                                    | a test              | blurry scaling on a native platform; fallback 2x                                                                         |

The redraws can start before the renderer lands: a generator draws its canvas and cuts it into today's zones (as the isles do) until the region build exists.

## 4. The world

**The images** (not committed; regenerate with `python3 -I worldplan2/blockout.py` from the scratchpad, or ask Claude A for them):

- `world-compare.png`: today's regions (left) and the plan (right) at the same scale, set where they lie, with the journeys.
- One sheet per region, today beside the plan at 4 px per cell, with landmarks (yellow) and ways (red): `valley.png`, `cogsworth.png`, `sunstone.png`, `isles.png`, `neon.png`, `halcyon.png`, `lumen.png`; and each plan alone at 1 px per cell (`*-1x.png`).
- `stats.json`: each canvas, its area and the measured walks.

The walk-seconds below are measured on the block-outs: shortest walks over walkable cells (eight directions, faces blocked, stairs and bridges open), at 40 px a second.

### 4.1 Today against the plan

| Region                                                    | Today: zones (walkable, in zone-areas) | Plan: canvas (zone-areas)   | Plan: walkable | Change                                                                                   |
| --------------------------------------------------------- | -------------------------------------- | --------------------------- | -------------- | ---------------------------------------------------------------------------------------- |
| The valley with Driftwood, the Headland and the Frostline | 13 (8.9, the garden estimated)         | 1280 x 2688 (18.7)          | 10.3           | +16 % walkable; true-scale village, farm and harbour; frame of sea, peaks and old forest |
| Cogsworth                                                 | 2 (1.6)                                | 704 x 960 (3.7)             | 2.4            | +48 %: the hill and the terminus                                                         |
| Sunstone Reach and the fire country                       | 6 (4.7)                                | 1280 x 1664 (11.6)          | 5.9            | +26 %: one land, the canyon, the castle's two wards                                      |
| Tidebloom Isles                                           | 4 (2.0)                                | 704 x 1152 (4.4)            | 2.3            | about the same                                                                           |
| Neon Harbour and the Skyport                              | 9 (3.6)                                | 960 x 1280 (6.7)            | 4.5            | canvas -26 %, walkable +25 %: streets instead of building blocks on open concrete        |
| Halcyon Station                                           | 1 (0.75)                               | 320 x 576 (1.0)             | 0.64           | the same                                                                                 |
| Lumen                                                     | 1                                      | 384 x 704 (1.5)             | 1.3            | a little wider: the crater reads                                                         |
| **The world**                                             | **36 zones (about 22 walkable)**       | **47 zone-areas of canvas** | **27**         | **+25 % walkable ground**                                                                |

**Towns, and their kinds.** Crossroads (a market village, about 14 buildings round a square); Driftwood (a fishing hamlet up one road above its quay); the halt farm (a farmstead with a windmill); Cogsworth (a railway and foundry town, about 18 buildings); Dust Gulch (a one-street frontier town, 9 buildings); Hearthold (a castle); Neon Harbour (the one city, about 40 buildings in nine blocks); Lagoon Landing (an island hamlet of three buildings); Halcyon (a station) and the Lumen habitat (an outpost). One of each kind; no region repeats another's.

**Where travel replaces walking.** Between every two regions, as today: the valley train (W3) from the halt to Cogsworth; the desert line (W5) from Cogsworth to Dust Gulch; the maglev (W7) from Cogsworth's terminus to the Skyport; the elevator (W8) and the shuttle (W9) upward; the ferry (W4) from Driftwood to the isles; the mine cart (S1) as a shortcut from the gulch to the caldera; the coastal steamer (S3, a proposal) from Neon back to Driftwood. Inside a region nothing replaces walking: no region is longer than about 75 s end to end.

### 4.2 The valley (home): garden, woodland, riverside, Crossroads, the park, the halt farm, Driftwood, the Headland and the Frostline

**Size and shape.** 1280 x 2688 px. From north to south: the Frostline in the peaks (y 0 to 1040), the T2 terrace with the woodland, the garden and the riverside (to y 1616), the valley floor with the halt farm, Crossroads and the park (to y 2336), Driftwood's quay and the sea, with the Headland east of the estuary. Old forest frames the north-east; the sea frames the south and west.

**Why this shape.** The water explains the valley: snowmelt from the lake runs through Fir Hollow, falls over the escarpment into the woodland's spring pool, runs east along the garden's south edge as the brook, fills the millpond and turns the mill where it drops to the valley floor, and runs south as the river to the estuary. The garden sits in the middle of the terrace, the village directly below its gate, so home and the everyday places are one short walk apart.

| Walk from the hut's door to  | s    |
| ---------------------------- | ---- |
| the spring pool              | 8.2  |
| the library                  | 12.2 |
| the stall                    | 12.7 |
| the cabin (ridge)            | 12.9 |
| the well (square)            | 13.6 |
| the stone circle             | 15.5 |
| the ring                     | 18.6 |
| the halt platform            | 18.9 |
| the mill                     | 20.6 |
| the bothy (saddle)           | 21.0 |
| the bandstand (park)         | 24.3 |
| Snowmelt Lake                | 28.1 |
| the scope (High Lookout)     | 30.7 |
| the ferry pier               | 36.4 |
| the Headland's lookout tower | 42.1 |
| the lighthouse               | 46.4 |

Between other places: the halt platform to the well 11.9 s, the ferry pier to the well 22.8 s, the halt platform to the ferry pier 33.8 s.

**Areas.**

- _The garden_ (T2, 320 x 576, unchanged in size): the home hub keeps its geometry and its harness; the hut on a raised yard; the gate on the axis of the square below.
- _Crossroads_ (T1, about 640 x 560): a 240 x 176 square with the well at its centre, entered on its axis by the gate lane from the garden's stair; the library and a terrace of touching cottages on its north side, the bakery on the west, the stall on the square; the harbour road south between four cottage plots of 128 x 176; the green with the ring to the south-west; roads west to the halt and east over the river to the park.
- _The halt farm_ (T1, about 400 x 480): the halt (station house, a 240 px platform, the engine shed with W3, buffers, the line running west off the canvas into the hills) with the farmyard below it (farmhouse, barn, four field blocks, the windmill on its rise) and a shingle shore at the sea.
- _The woodland_ (T2, 416 x 512): crowns in clumps, the spring pool under the fall, the stone circle in a glade (a pocket), the forester's yard by the timber stair down to the floor.
- _The riverside_ (T2, 544 x 512): the millpond, the mill on the terrace step with its ramp, the miller's cottage and orchard, hay, beehives along a hedge.
- _The park_ (T1, east of the river): the bandstand on its paving, the pump house at the river, flower beds; the lane south to the estuary footbridge.
- _Driftwood_ (T1 cottages, T0 quay): five cottages up the harbour road, the 32 px quay face with a ramp, the quay (fish market, harbour master, chandlery), the slip with the ferry (W4), three jetties and the ferry pier, a breakwater along the grid to the lighthouse on its rock.
- _The Headland_ (T1, behind its wall): the drystone wall from the estuary bank to the east cliff with the stile (W1) as its only gap, the sheep fold, the lookout tower at the point, a cove stair.
- _The Frostline_ (T3 to T5): Fir Hollow behind the rock rib (gully trail, W2's second pine), the ridge's cabin meadow, the col (W2) up to the Snow Saddle and its bothy, Snowmelt Lake in its cirque, the spur stair to the High Lookout.

**Kept from today, and why.** The garden's size and place (the hub, the harness and every save point depend on it); the order of places (ridge above the garden, woodland west, riverside east, town south, harbour on the coast), because players know it and the water already runs that way; the mill where PR #86 put it; the Frostline's four places and the col; the lighthouse, the ferry and the lookout tower. **Changed:** the town grows from one tile to a village at true scale with a square on the garden's axis; the halt becomes a farmstead with a goods yard; Driftwood becomes its own hamlet above a quay; the Headland gets its wall; the valley's empty corners become sea and old forest drawn as frame, not holes.

### 4.3 Cogsworth

**Size and shape.** 704 x 960 px (two of today's zones were 320 x 1152). The platform runs along the north edge with both lines entering from the west; the clock-tower square in front of the station; workshop rows west; Gasworks Hill one tier up to the east; the canal half a tier down across the middle; the foundry and allotments south-west; the terminus and the pump house south-east, where the maglev leaves east.

| From the platform to     | s    |
| ------------------------ | ---- |
| the clock tower          | 7.8  |
| the gasholder (hill)     | 10.3 |
| the airship mast         | 13.2 |
| the lock                 | 18.1 |
| the foundry              | 21.8 |
| the allotments           | 22.7 |
| the pump house           | 26.0 |
| the maglev terminus (W7) | 29.5 |

**Trade.** Coal and iron come in by rail and canal; the foundry casts gears, rails and pipes; the gasworks makes the gas for the lamps and the airship; the pump house drives the atmospheric line to the city. **Kept:** the square under the clock tower with the platform on its north, the canal with its lock, foundry and allotments (the region's best-reading pieces today). **Changed:** the hill and the terminus are new ground; the airship leaves the square for the hill; the canal sinks half a tier; streets of touching workshops.

### 4.4 Sunstone Reach, Hearthold and the fire country

**Size and shape.** 1280 x 1664 px, one land. South: the oasis hollow (T0) in the dunes, Dust Gulch's one street east of the platform (the desert line enters from the west and ends at buffers), the corral, the mine mouth in the mesa's 40 px face. East: the Scorched Pass, where sand turns to scrub and ash, and a basalt canyon climbs north for about 10 s to its head. North of the canyon: the lava chasm, the chasm bridge (W6), and Hearthold on its rock in a lava moat, with an outer bailey (T3) and an inner ward (T4). North of the castle: the ledge, the postern, the Ember Caldera with its lava lake, forge and cart bay; the Cinder Springs' terraces in the north-east. The mesa and the volcano's flank are frame.

| From the platform to | s    |     |                 | s    |
| -------------------- | ---- | --- | --------------- | ---- |
| the saloon           | 5.7  |     | the gatehouse   | 23.1 |
| the mine mouth       | 5.9  |     | the keep        | 27.5 |
| the water tower      | 8.9  |     | the postern     | 33.0 |
| the corral           | 9.8  |     | the bathhouse   | 37.4 |
| the caravan camp     | 10.9 |     | the basalt ring | 42.8 |
| the spring pool      | 11.2 |     | the top pool    | 43.3 |
| the canyon head      | 18.3 |     | the forge       | 46.4 |
| the ruin arch        | 18.9 |     | the cart bay    | 53.5 |

The caldera is 46 to 54 s on foot through the castle, which is why the mine cart (S1) earns its place as the quick way back once the bridge is open.

**Trade.** Cattle and ore out by rail; water piped from the oasis to the water tower and the engine crane; ore by cart to the forge, ingots back; the castle supplied over the bridge from the gulch, its water from a cistern. **Kept:** the gulch's street from the platform, the oasis and its buried-outlet story, the castle in its lava moat with two bridges, the caldera's forge and the springs' terraces (Claude D's D13 detail work carries over). **Changed:** one continuous land instead of six tiles in an L; the long straight causeway becomes the canyon and a short bridge; the castle gains its inner ward.

### 4.5 The Tidebloom Isles

**Size and shape.** 704 x 1152 px including the sea round it. The headwaters (T2) in the north-east with the crater pool and the upper fall; the rainforest (T1) across the north; Lagoon Landing (T0) in the south-west round the lagoon and the pier; Black-sand Cove (T0) in the south-east with the basalt arm, the sea stack and the cave.

| From the pier to                 | s    |
| -------------------------------- | ---- |
| the boathouse                    | 4.8  |
| the lower fall                   | 10.0 |
| the turtle beach                 | 15.8 |
| the sea cave                     | 18.0 |
| the giant tree                   | 20.0 |
| the upper fall, the rain shelter | 27.1 |
| the crater pool                  | 28.1 |

**Kept, and why:** the island whole in island coordinates (`isle_zones.island()`, already a canvas), its four places, tiers, falls and loop; its size suits a day trip by ferry. **Changed:** stairs to 48 px, the landing's packing shed and pier as its node.

### 4.6 Neon Harbour and the Skyport

**Size and shape.** 960 x 1280 px (today 960 x 1728). The maglev arrives at the Skyport on the south shore; one spine, a 64 px boulevard under the elevated tram, runs north to the central plaza; cross streets at the market and at the old wet street; the Heights one 40 px tier up in the north-west with stair streets and the sunken plaza; downtown with Dave's tower in the middle; the docks along the east quay; the Point with the lighthouse; the pier south to the elevator's anchor (W8).

| From the maglev platform to | s    |
| --------------------------- | ---- |
| the concourse               | 3.7  |
| the ring court              | 5.6  |
| the anchor (W8)             | 8.0  |
| the arcade                  | 9.7  |
| the Point's lighthouse      | 13.9 |
| the market                  | 15.9 |
| the cranes                  | 17.7 |
| Dave's tower                | 21.6 |
| the subway mouth (Heights)  | 27.1 |
| the big screen (plaza)      | 29.8 |

**Why smaller.** At true scale a city block is 208 x 272 px with about eight buildings of three to six storeys; nine blocks hold about 40 buildings, each to Eastward's detail. Today's nine zones are mostly blocks of open concrete between free-standing buildings; the plan has less canvas and more street. **Kept:** the Skyport and its pier, the docks' cranes and ship, the old wet street with the ring court, the elevated tram, Claude C's facade detail (PR #116). **Changed:** streets of touching facades from the composer; one spine with cross streets; `waterfront` folds into the docks and `point` into the Skyport's shore.

### 4.7 Halcyon Station

320 x 576 px, unchanged: rooms in the order of the climb, from the elevator's airlock at the bottom through hydroponics, the galley, the atrium and the sleep bay, to the shuttle hatch (W9) and the lounge under the windows. From the airlock: hydroponics 3.4 s, the atrium 6.3, the hatch 10.7, the lounge window 12.2. A station is a building; one screen of rooms is enough.

### 4.8 Lumen

384 x 704 px (today 320 x 576): the pad on the crater's rim (T2), the habitat with its solar arrays and the ice rig in the shadowed crater (T1), the pressure tube down to the dome on the crater floor (T0), the moon tree and the hammock. From the pad: the habitat 8.5 s, the moon tree 13.9, the hammock 16.4. A little wider so the crater reads as a crater on a 300 px screen.

## 5. Where the ways stand

Unchanged from #95 and #118 in what they are and in their order; on canvases each barrier is a set of cells and a stand.

| #   | Way                 | Where on the new map                                                                                         | It closes                                                                                       |
| --- | ------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| W1  | The Headland stile  | the gap in the wall across the Headland, valley (1148, 2232)                                                 | the only way onto the promontory (the estuary and the cliffs close the rest)                    |
| W2  | The ridge col       | the col above the cabin (624, 640) and the gully trail through the rock rib (456, 824): one storm, two pines | both ways from the ridge into the Frostline; the escarpment closes the hollow from the woodland |
| W3  | The valley train    | the engine shed at the halt (356, 1740)                                                                      | the line to Cogsworth                                                                           |
| W4  | The Driftwood ferry | the slip on Driftwood's west quay (424, 2428)                                                                | the only crossing to the isles                                                                  |
| W5  | The desert line     | a sand-caked wagon at Cogsworth's platform (640, 44)                                                         | the line to Dust Gulch                                                                          |
| W6  | The chasm bridge    | the head of the Scorched Pass's canyon (1128, 836)                                                           | the only way over the chasm; S1 waits for it                                                    |
| W7  | The maglev          | Cogsworth's terminus (632, 870)                                                                              | the line to Neon Harbour                                                                        |
| W8  | The space elevator  | the anchor at the end of the Skyport's pier (616, 1240)                                                      | the only way up                                                                                 |
| W9  | The shuttle         | Halcyon's hatch (240, 160)                                                                                   | the only way to Lumen                                                                           |

Always open: the garden, the woodland, the riverside, Crossroads, the park, the halt farm, the ridge and its cabin, Driftwood's quay and jetties. Order (as #95): W1 to W4 from the start; W5 and W7 after W3; W6 after W5; W8 after W7; W9 after W8. With every way closed, a flood fill from the garden and every open stop must reach nothing behind them (the test in #118 moves to cells).

## 6. Order of work and owners

| Step | Lane | Work                                                                                                                                                                                                                                                                                                            | Needs                        |
| ---- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| P0   | A    | The toolkit lands (`terrace.py`, `scale.py`, tiers, the facade composer, `fore.png`), as `verticality.md` 4e                                                                                                                                                                                                    |                              |
| P1   | A    | **Region canvases**: `REGIONS` and `AREAS`, the region build and tile cutting, exports; at first the build also cuts canvases into today's zones so nothing else changes                                                                                                                                        | P0; Matt's yes to decision 2 |
| P2   | A    | The renderer mounts tiles; region walk from one grid; areas for names and the map; the hub's offset; layout version and save mapping (with Codex for `lib/save-data.ts`); tests; the 1x-picture test                                                                                                            | P1                           |
| P3   | B    | Props to the scale table and #97's audit: the valley's cottages, station house, bench, stall, lamp, crate, barrel; the new valley props (engine shed in two states, bakery, pump house, forester's yard, chandlery, harbour master's hut, the stile and the pines in two states); the garden on its raised yard | P0                           |
| P4   | E    | The valley on its canvas (section 4.2): terraces, water, Crossroads, the halt farm, the riverside, the park, Driftwood and the Headland's wall                                                                                                                                                                  | P1, P3                       |
| P5   | A    | The Frostline on the valley's canvas: the rock rib, the gully, the col's corridor, the spur                                                                                                                                                                                                                     | P1                           |
| P6   | D    | Sunstone Reach as one canvas (4.4), then Halcyon and Lumen (4.7, 4.8)                                                                                                                                                                                                                                           | P1                           |
| P7   | C    | Cogsworth's canvas (4.3), then Neon's (4.6) with the composer, then the isles' stairs (4.5)                                                                                                                                                                                                                     | P1, the Neon Heights pilot   |
| P8   | A    | The ways wired on cells (#118 to areas and cells), the map's lines                                                                                                                                                                                                                                              | P2, #95's rules (Codex)      |

The valley comes first among the regions: it is home, every player sees it first, and its props become the library the others copy. Lanes C and D can start their canvases as soon as P1 lands, because P1 cuts canvases back into zones until the renderer catches up.

## 7. Decisions for Matt

**Decided (Matt, 20 Oct, about 10:50):** continuous region canvases on the 8 px grid, streamed in tiles (2); size everything from the sizing table, with everyday places within about 15 s of the hut (3); Cogsworth grows with Gasworks Hill and the Terminus, Neon's canvas a quarter smaller with more walkable street, and Sunstone Reach as one continuous land (5, 6, 7); the zoom stays at 12 adults across (1). Decisions 4 and 8 to 12 are still open.

| #   | Decision                                                                                                                                    | Recommendation or decision                         | Why                                                                                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1   | The zoom: keep 12 adults across (`ART_ACROSS` 300)?                                                                                         | **Decided 20 Oct: keep.**                          | It matches Eastward and Stardew across, keeps 44 px targets, and the extra height is room for north-south sightlines.       |
| 2   | Replace the 320 x 576 zone grid with region canvases streamed in 256 px tiles, zones becoming named areas?                                  | **Decided 20 Oct: yes.**                           | No seams, sizes from the places, props anywhere, a third to a quarter of today's picture memory. The redraws happen anyway. |
| 3   | Size places from the sizing table (section 1.4), with everyday places within 15 s of the hut?                                               | **Decided 20 Oct: yes.**                           | It is what the scale table implies; today's town tile cannot hold a true-scale village.                                     |
| 4   | Let the valley grow to a 1280 x 2688 canvas (+16 % walkable), with a real village, a farmstead at the halt and Driftwood as its own hamlet? | **Yes.**                                           | Home is where players spend most time; this is the one place worth more ground.                                             |
| 5   | Cogsworth to 704 x 960 with Gasworks Hill and the terminus?                                                                                 | **Decided 20 Oct: yes.**                           | Two tiles hold no loop and no place for the maglev; still smaller than a Kanto city.                                        |
| 6   | Neon's canvas down by a quarter (960 x 1280), streets of touching facades, `waterfront` and `point` folded in?                              | **Decided 20 Oct: yes.**                           | About 40 buildings at true scale is already a large art budget; more streets, less empty concrete.                          |
| 7   | Sunstone Reach as one continuous land with the canyon reveal and a short chasm bridge?                                                      | **Decided 20 Oct: yes.**                           | It keeps everything Claude D drew and removes the L of tiles and the long causeway.                                         |
| 8   | Ground pictures at 1x with nearest-neighbour scaling (or 2x) instead of 4x?                                                                 | **Test, then 1x if crisp on all three platforms.** | Sixteen times less decoded memory; art-style.md already asks for the test.                                                  |
| 9   | The coastal steamer (S3) from Neon to Driftwood once W7 is open?                                                                            | **Yes, later.**                                    | It closes the network into a loop and brings the player home from the screen city by sea.                                   |
| 10  | Secret pockets hold a view, a resident or a story detail, never a keepsake?                                                                 | **Yes.**                                           | No rewards for decorative places (AGENTS.md).                                                                               |
| 11  | No one-way hops down low steps; every change of height is a stair or a ramp?                                                                | **Yes, for now.**                                  | It keeps tap-walking predictable; ledges can come later as shortcuts.                                                       |
| 12  | The companion stays 24 px tall, as tall as an adult (`verticality.md`, question 7)?                                                         | **Keep.**                                          | Every size here assumes it; a smaller pet would change every companion and visitor sprite and no place's size.              |

## Sources

Developer interviews, official pages and community-maintained references, read for v1 and v2 (20 Oct 2026). Screenshot keys refer to `research/world-references.md`, which lists each official image URL (Steam store screenshots and press kits). Measurements on screenshots are observations, not developer statements.

- pret, Pokémon Red and Blue disassembly, map table: https://github.com/pret/pokered/blob/master/constants/map_constants.asm
- Bulbapedia, Ledge: https://bulbapedia.bulbagarden.net/wiki/Ledge
- Bulbapedia, Poké Flute (Snorlax on Routes 12 and 16): https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Flute
- Bulbapedia, Skyarrow Bridge: https://bulbapedia.bulbagarden.net/wiki/Skyarrow_Bridge
- Game Developer, Marshalkowski, "Overworld Overload", part 2: https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2
- ZeldaSpeedRuns, Link's Awakening in-game maps: https://zeldaspeedruns.com/la/doghouse/in-game-maps
- Zelda Dungeon Wiki, Ukuku Prairie: https://zeldadungeon.net/wiki/Ukuku_Prairie
- Set Side B, "The Hidden Structure of the Overworld of Link's Awakening": https://setsideb.com/?p=133
- Zelda Wiki, Minish Portal: https://zeldawiki.wiki/wiki/Minish_Portal
- Stardew Valley Wiki, Pelican Town: https://stardewvalleywiki.com/Pelican_Town
- Stardew Valley Wiki, Modding:Maps: https://stardewvalleywiki.com/Modding:Maps
- Stardew Valley Wiki, The Mountain (mirror read; English text): https://hu.stardewvalleywiki.com/Hegyek
- Stardew Valley Wiki, Secret Woods: https://stardewvalleywiki.com/Secret_Woods
- Nookipedia, Acre: https://nookipedia.com/wiki/Acre
- Nookipedia, Ramp: https://nookipedia.com/wiki/Ramp
- Game Developer, "Designing content for no one" (TUNIC): https://www.gamedeveloper.com/design/designing-content-for-no-one-an-interview-with-the-team-behind-tunic
- Game Informer, "Tracing Threads: The Making of Tunic": https://gameinformer.com/2022/05/30/tracing-threads-the-making-of-tunic
- MobileSyrup, Sea of Stars level design interview: https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/
- Hardcore Gaming 101, Hyper Light Drifter: https://www.hardcoregaming101.net/hyper-light-drifter/
- Wikipedia, Moonlighter: https://en.wikipedia.org/wiki/Moonlighter_(video_game)
- Wikipedia, Eastward: https://en.wikipedia.org/wiki/Eastward_(video_game)
- Nintendo, how the developers made and remade Eastward: https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward
- RPGamer, Chained Echoes interview: https://rpgamer.com/2022/11/chained-echoes-interview/

**Gaps.** No developer source gives Stardew's, Eastward's or CrossCode's map sizes or walking speeds; the reference sizes here are measured on store screenshots by character height and are good to about a quarter of an adult. No castle or desert town appears in our reference shots, so those two sizes are built from parts. The walk-seconds are measured on block-outs, not on drawn art; the redraws will move them by a few seconds. The garden's walkable share in today's totals is an estimate.
