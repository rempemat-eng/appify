# The world plan (v3): one continent

Matt, 20 Oct 01:05: "All of these need redesigns pretty much, to fit the newly established soft grids. also consult the other games mentioned for world buildings how large parts of the maps should be and how they are attached together and how you can create interesting spaces." At 10:32, on v1: "also dont just redesign the current map exactly, really think deeply of the sizing of everything and the map". At 10:58, on v2's world map: "i like how you are creating one big map first here. work the whole world map out first and how everything connects (with as many physical connections as possible as well, with trains as short cuts). of course to reach the moon and such places you need an animation of a rocket ship of sorts. make sure you establish the sizing and soft grid for all regions ... the world should feel expansive with natural looking boundaries and no abrupt cuts".

**Status: a plan, partly decided.** v2's sizing and its seven decided items stand (section 11). v3 adds the continent. The valley, Cogsworth, Sunstone Reach, Neon Harbour and the isles sit on one world map in world coordinates on the 8 px grid. Eight walkable routes join them, each a real place, and the trains, the ferry and the maglev become shortcuts over those routes. Space is reached by a rocket from a launch cape. The nine ways become things on the routes being mended, and the engine draws one world canvas. Sections 1 and 2 are v2's sizing and lessons, unchanged. Section 6 keeps v2's region plans and says what v3 changes in each.

It builds on, and does not repeat:

- `verticality.md` (branch `claude-a/verticality-study`): the 8 px soft grid, the five rules, the terrace toolkit and the scale table.
- `art-style.md` on main: Eastward's level of detail is required, and each setting takes its own forms and palette.
- `prop-logic.md` and the prop audit (draft PR #97).
- `world-unlocks.md` (draft PR #95; decided: nine ways, one a day) and the ways catalogue `lib/world-ways.ts` (draft PR #118).
- `world-rules.md`, `world-ports.md` and `world-atlas.md` stay the rulebook.

**The images** are drawn by a script from the block-outs (1 px per 8 px cell, flat colours per kind of ground, tiers shaded, faces derived) and measured on them. They are not in the repository; Claude A has them in its scratchpad (`worldplan3/`):

- `continent-1x.png`: the whole continent, 1 px per 8 px cell (1040 x 616).
- `overview-32px.png`: the same at 1 px per 32 px (260 x 154).
- `continent-labelled.png`: 2 px per cell, with places, routes (yellow), journeys (dashed), ways (red) and the landmarks on the routes.
- One crop per region at 4 px per cell, each in its continental setting: `region-valley.png`, `region-cogsworth.png`, `region-sunstone.png`, `region-neon.png`, `region-isles.png`.
- One crop per route at 4 px per cell: `route-canal-road.png`, `route-drovers-road.png`, `route-eastern-road-and-coast-path.png`, `route-hill-path.png`, `route-ember-pass.png`, `route-shell-bar.png`, `route-cape-road.png`.
- `stats.json`: every walk from the hut, on foot and with shortcuts. `gates.json`: the gate check (section 8).
- v2's per-region comparison sheets, today beside the plan, are in `worldplan2/`.

## 0. In short

1. **One continent, west to east, as a journey.** The fire country and the desert lie in the far west. Then come the downs, Cogsworth's industry, and the home valley in the middle. To the east are orchards, the industrial edge and the neon city, with a launch cape beyond it. The isles lie off the south coast. The Northern Range closes the north; the sea closes the south, west and east.
2. **Eight walkable routes join the regions**, 8 to 40 s each, every one a place with landmarks, a rest and a reason to exist: the Canal Road, the Drover's Road, the Eastern Road, the Coast Path, the Hill Path, the Ember Pass, the Shell Bar (a causeway to the isles) and the Cape Road. There are four loops, and every region has at least two ways in.
3. **Journeys are shortcuts over routes.** The valley train runs beside the Canal Road, the desert line beside the Drover's Road, and the maglev on a sea viaduct along the coast. The ferry crosses the strait the Shell Bar walks. A way opens a route and its line together.
4. **Space by rocket.** A rocket from the Launch Cape, east of the Skyport, replaces the space elevator (W8: "the launch not yet fuelled"). Halcyon's lander takes you on to Lumen (W9). Each has a launch and a landing animation.
5. **Natural boundaries only.** Peaks, a wooded ridge (the Brackens), a flash-flood gorge (the Dry Wash), a river (the Neon), badlands, old forest and the sea close the world and make its chokepoints. Each biome blends into the next over 700 to 1200 px.
6. **One world canvas** (8320 x 4928 px), authored in chunks (regions and routes), cut into 660 tiles of 256 px. 361 of those are uniform (sea, peaks, forest) and share a picture. The renderer streams 9 to 12 tiles, as v2 planned.

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

## 3. The continent

### 3.1 The map

World coordinates are px on the 8 px grid, with the origin at the north-west corner of the world canvas (8320 x 4928). The continent runs about 7600 px west to east (190 s of walking straight across) and 2700 px north to south, with the isles 900 px off the south coast.

```
 WEST                                                                                 EAST
 +-------------------------------------------------------------------------------------+
 | volcano     |      THE NORTHERN RANGE (peaks)       | Frost-  |   old forest (wild)   |
 | springs     |  Ember Pass (W6)    Hill Path (W2,W3) | line    |                       |
 | castle  W6  |  ===========  COGSWORTH  =========  B | (W2)    |  N                    |
 | caldera     |        hill, junction,               r | garden  |  e   NEON HARBOUR     |
 | chasm       |  D     canal, terminus (W5, W7)      a | Cross-  |  o   (W7 swing        |
 | canyon      |  r  DOWNS: farm > heath > scrub      c | roads   |  n   bridge)  LAUNCH  |
 | gulch oasis |  y     Drover's Road (W5 bridge)     k | halt    |      Skyport  CAPE    |
 | badlands    |  Wash          Canal Road (W3 gorge) e | Drift-  | Eastern Road   (W8)   |
 |             |                                      n | wood    | Coast Path            |
 |             |                                      s | Headland (W1)                   |
 +------------------------------- the sea ----------------------------------------------+
                                                 Shell Bar (W4) | ferry (W4)
                                                 TIDEBLOOM ISLES
```

| Place                                                       | World origin (x, y) | Size (px)   | Notes                                                                                                                                   |
| ----------------------------------------------------------- | ------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Sunstone Reach (with Hearthold and the fire country)        | (320, 640)          | 1280 x 1664 | **mirrored from v2**: its oasis and platform face east toward the downs, the castle and the springs lie in the west against the volcano |
| Cogsworth                                                   | (2520, 1160)        | 704 x 960   | as v2                                                                                                                                   |
| The valley (with Driftwood, the Headland and the Frostline) | (4120, 360)         | 1280 x 2688 | as v2                                                                                                                                   |
| Neon Harbour and the Skyport                                | (6520, 1480)        | 960 x 1280  | as v2; its west edge is now the Neon river                                                                                              |
| Tidebloom Isles                                             | (4920, 3420)        | 704 x 1152  | as v2; the Shell Bar lands on its north shore                                                                                           |
| Launch Cape                                                 | (7480, 2400)        | 480 x 360   | new: the spaceport on a cape east of the Point                                                                                          |

**Walkable ground on the continent: 51.6 zone-areas** (v2's regions alone had 27). Most of the new ground is countryside between the regions: downs, farmland, orchards and foothills, which the routes cross.

### 3.2 Why this arrangement

- **The theme becomes geography.** The atlas's idea (a journey from rest to screens and back to sleep) now reads on the map. Home sits in the middle. Westward the land grows harder: industry, then drought, then fire. Eastward it grows louder: orchards, then yards, then the city, then the rocket to the quietest place of all.
- **Water explains the land.** Snow in the Northern Range feeds the valley's river (v2), the canal and the Neon river. The Dry Wash is a flash-flood bed that runs only after storms (which is how it took the Drover's Road bridge). The sea closes the south.
- **Cogsworth is the junction its name promises.** The valley line arrives from the east, the desert line leaves to the south-west, and the maglev leaves south-east for the coast viaduct. The canal links it to the valley's halt.
- **Each region keeps its v2 plan.** Only Sunstone is mirrored, so that it faces the land it trades with.

## 4. The routes

Each route is a place: a corridor between natural edges, with landmarks every 5 to 10 s, a rest about halfway (rule 2), and a reason to exist (rule 13). The walk-seconds are the shortest walk between the route's ends on the block-out.

| Route                    | From and to                                                       | Walk | Reason (who uses it)                                                                                | Landmarks and rests                                                                                                                                                        | Its line (shortcut)                                 | Its way                                                                                               |
| ------------------------ | ----------------------------------------------------------------- | ---- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **R1 the Canal Road**    | Cogsworth's canal to the valley's halt and coal wharf             | 28 s | barges bring coal to the valley and take flour and hay back; the towpath horses and the lock-keeper | the canal and its towpath; the lock-keeper's cottage; the brickworks kiln with its stacks of bricks; the Millrace gorge through the Brackens; the coal wharf at the halt   | the valley train                                    | **W3**: a landslip in the Millrace gorge buries the towpath and the line                              |
| **R2 the Drover's Road** | Cogsworth's south-west to Dust Gulch                              | 29 s | drovers bring cattle from the gulch to Cogsworth's market and the railhead                          | hedged pasture, then heath, then scrub; the drovers' inn at the halfway well; the stock pens; the Dry Wash bridge; a windpump; the mesa ahead                              | the desert line                                     | **W5**: a flash flood took the Dry Wash bridge, carrying road and line                                |
| **R3 the Eastern Road**  | the valley's park to Neon's swing bridge                          | 26 s | carts take fruit, vegetables and flowers to the city's markets; commuters                           | a cider orchard and its press; market gardens with glasshouses; allotments and sheds; a depot and gasworks yard; the swing bridge, with the city's towers across the river | (the maglev arrives along the coast)                | **W7**: the swing bridge is stuck open for want of a gear from Cogsworth                              |
| **R4 the Coast Path**    | the valley's estuary lane along the cliffs to the bridgehead      | 30 s | fishers' path between the coves; walkers                                                            | Gullwick, a fishing hamlet with a smokehouse; a cliff bench over the sea viaduct; the city's breakwater ahead                                                              | the coastal steamer (S3, proposal)                  | shares W7's bridge                                                                                    |
| **R5 the Hill Path**     | Snowmelt Lake down the foothills to Gasworks Hill                 | 36 s | shepherds and the lamplighter's gas-main walkers                                                    | a snow ledge out of the cirque; a long stair over the Brackens' head; a shepherd's bothy; cairns; the view down on Cogsworth's chimneys and airship                        | none                                                | **W2** to reach its top; **W3** (a rockfall at the stair's foot, from the same storm as the landslip) |
| **R6 the Ember Pass**    | Cogsworth's west street up through the range to the caldera's rim | 39 s | ore carters before the mine line; pilgrims to the springs                                           | soot meadow, then heath, then bare rock, then ash; a stone refuge; the fumarole view over the desert; the caldera's rim                                                    | the mine cart (S1) from the gulch does the same job | **W6**: a rockfall on the pass (with the chasm bridge)                                                |
| **R7 the Shell Bar**     | the Headland's cove to the isles' north shore                     | 11 s | a tombolo of sand and shell; cocklers at low tide                                                   | marram dunes, tide pools, a tide post, the island ahead                                                                                                                    | the ferry from Driftwood                            | **W4**: a storm washed out a stretch (and holed the ferry); W1 first, to reach the Headland's cove    |
| **R8 the Cape Road**     | the Point to the launch pad                                       | 8 s  | spaceport workers                                                                                   | the cape's salt flats, the fuel farm, the pad and the rocket on it                                                                                                         | (the rocket is the journey)                         | **W8**: the launch not yet fuelled                                                                    |

**Loops.**

- Valley, Canal Road, Cogsworth, Hill Path, Frostline, valley.
- Valley, Eastern Road, Neon, Coast Path, valley.
- Cogsworth, Drover's Road, Sunstone (through the canyon and over the chasm bridge), Ember Pass, Cogsworth.
- Over the sea: Driftwood, ferry, the isles, Shell Bar, the Headland.

**Shortcuts** (none is needed to reach a place; each saves a walk):

| Shortcut                                        | Between                                                    | Saves                                                                  | Opens with                             |
| ----------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------- |
| The valley train                                | the halt and Cogsworth's platform                          | hut to Cogsworth's platform 69.5 s on foot, 22.9 s with it             | W3 (the line is cleared with the road) |
| The desert line                                 | Cogsworth's platform and Dust Gulch's platform             | hut to the gulch 105.8 s on foot, 26.9 s with the trains               | W5                                     |
| The maglev                                      | Cogsworth's terminus and the Skyport, on the coast viaduct | hut to the Skyport's maglev 67.6 s on foot, 48.4 s by train and maglev | W7                                     |
| The ferry                                       | Driftwood's pier and Lagoon Landing                        | hut to the isles' pier 81.2 s on foot (Shell Bar), 40.4 s by ferry     | W4                                     |
| The mine cart (S1)                              | Dust Gulch's mine mouth and the caldera's cart bay         | the gulch to the cart bay 53.5 s on foot, about 7 s with it            | after W6                               |
| The coastal steamer (S3, proposal)              | the Skyport's pier and Driftwood                           | the way home from the city by sea                                      | after W7                               |
| The millpond boat (S2), the ridge lanterns (S4) | comforts in the valley                                     |                                                                        | GRASS only                             |

**Walks from the hut's door** (selected; all are in `stats.json`):

| To                                 | On foot (s)             | With shortcuts (s) |
| ---------------------------------- | ----------------------- | ------------------ |
| the stall, the square, the library | 12 to 14                | same               |
| the halt                           | 18.9                    | same               |
| the ferry pier                     | 36.4                    | same               |
| the Frostline's scope              | 30.7                    | same               |
| Cogsworth's platform               | 69.5                    | 22.9               |
| Gasworks Hill                      | 59.3 (by the Hill Path) | 33.1               |
| the drovers' inn                   | 73.9                    | 49.4               |
| Dust Gulch's platform              | 105.8                   | 26.9               |
| Hearthold's keep                   | 133.6                   | 54.7               |
| the caldera's forge                | 120.7                   | 43.1               |
| the swing bridge                   | 51.0                    | same               |
| Neon's market                      | 62.6                    | 59.8               |
| Neon's big screen                  | 77.4                    | 69.9               |
| the isles' pier                    | 81.2                    | 40.4               |
| the launch pad                     | 88.0                    | 58.6               |

At 40 px a second, the continent's far corners (the springs, the launch pad) are 1.5 to 2.3 minutes from the hut on foot and under a minute with the shortcuts. The everyday places stay within 15 s (v2's decided rule).

## 5. Natural boundaries and transitions

**The edges of the world:**

- **North:** the Northern Range. Peaks with snow caps, drawn as frame, never walked. The volcano's black flank in the west.
- **West:** badlands (red, cut, impassable) and the sea.
- **South:** the sea, along a coast that runs in grid-led stretches with organic sand and rock edges (the soft grid at the large scale).
- **East:** old forest over the hills north of the Eastern Road and north of the city; the sea beyond the Launch Cape.

Nothing ends in a straight cut. Each edge is a thing you would also see in the real world.

**The barriers that make the chokepoints** (inside the continent):

| Barrier                             | Where                                                                                             | What it closes                                           | The gap                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| The Brackens                        | a wooded ridge from the range to the sea, between Cogsworth's outskirts and the valley's farmland | all ground between the valley and Cogsworth              | the Millrace gorge (the Canal Road and the line, W3); the stair over its head (the Hill Path, W3) |
| The Dry Wash                        | a gorge from the range to the sea, west of the downs                                              | the desert from Cogsworth's side                         | the Drover's Road bridge (W5)                                                                     |
| The volcano's foot and the mesa     | round the fire country                                                                            | the caldera and the castle from the desert and the downs | the chasm bridge and the Ember Pass, both W6                                                      |
| The Neon river                      | the city's whole west side, from the hills to the sea                                             | the city                                                 | the swing bridge (W7); the maglev crosses on its own viaduct                                      |
| The Headland's wall and the estuary | v2                                                                                                | the Headland                                             | the stile (W1)                                                                                    |
| The rock rib and the col            | v2                                                                                                | the Frostline                                            | the two pines (W2)                                                                                |
| The sea                             | round the isles                                                                                   | the isles                                                | the Shell Bar and the ferry (W4)                                                                  |

**Transitions** (each biome blends into the next over a wide band, its edges wandering and dithered, never at a seam):

| Band                    | From and to                                                                                                                           | Width                                                  | Along                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------ |
| Valley to the Frostline | garden meadow, then fir woodland (the hollow), then alpine meadow (the ridge), then snow patches, then snow (the saddle)              | about 1100 px (the garden's north fence to the saddle) | the ridge trail, the col |
| The downs               | Cogsworth's farmland, then hedged pasture, then heath, then scrub, then the Dry Wash, then dune                                       | about 1000 px (250 each)                               | the Drover's Road        |
| Cogsworth to the valley | soot meadow and slag, then brickfields and clay pits, then the Brackens' wood, then farmland                                          | about 900 px                                           | the Canal Road           |
| The valley to the city  | the park, then cider orchards, then market gardens, then allotments and sheds, then depots and gas yards, then the river and the city | about 1000 px (370, 300, 200, 120)                     | the Eastern Road         |
| The cliffs              | cliff-top grass, then gorse, then a fishing hamlet, then the breakwater                                                               | about 1300 px                                          | the Coast Path           |
| Up to the fire country  | soot meadow, then heath, then bare rock, then ash (no green within 64 px of lava)                                                     | about 1200 px                                          | the Ember Pass           |
| Down from the snow      | snow, then a rock ledge, then alpine heath, then soot meadow                                                                          | about 1000 px                                          | the Hill Path            |
| To the isles            | Headland grass, then marram dunes, then sandbar and tide pools, then the island's beach                                               | about 450 px                                           | the Shell Bar            |

**Views out, so the world feels larger than you have walked.** Distant landmarks are drawn as far-scale silhouettes where a sightline allows. They are scenery only, and none is a tap target.

- From the High Lookout: the city's glow in the east, Cogsworth's airship and gasholder in the west, the volcano's smoke beyond.
- From the halt and the Canal Road: the gasholder and the airship over the Brackens.
- From Driftwood and the Headland: the maglev's sea viaduct across the bay, the isles' volcano, the rocket on its pad on clear days.
- From the Eastern Road: Dave's tower and its screen across the river.
- From the Drover's Road: the mesa and the volcano's smoke.
- From the Ember Pass: the whole desert below.

## 6. The places inside the continent (v2's plans, with v3's changes)

### 6.1 What v3 changes

v3 changes these from v2:

- **Sunstone Reach** is mirrored east to west: the platform's line comes from the east (Cogsworth), the oasis faces the downs and the Drover's Road, and the canyon, the chasm and the castle lie to the west. The Ember Pass enters the caldera from the east.
- **Cogsworth**: the valley line arrives at the platform from the east; the desert line leaves at the west end; the canal runs on east as the Canal Road's canal; the Hill Path enters Gasworks Hill from the east; the Ember Pass and the Drover's Road leave from the west street and the south-west fields.
- **The valley**: the halt's line runs west beside the canal to Cogsworth, and the coal wharf is at the halt. The Eastern Road leaves the park eastward. The Coast Path leaves the estuary lane. A stair down the Headland's south cliff leads to the cove where the Shell Bar starts.
- **Neon**: the river and the swing bridge close its west side; the maglev arrives on the coast viaduct; the elevator's anchor goes (the Skyport's pier becomes the steamer's); the Point leads to the Cape Road.
- **The isles**: the Shell Bar lands on the north shore, with a stair up into the rainforest.

### 6.2 The valley (home): garden, woodland, riverside, Crossroads, the park, the halt farm, Driftwood, the Headland and the Frostline

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

### 6.3 Cogsworth

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

### 6.4 Sunstone Reach, Hearthold and the fire country

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

### 6.5 The Tidebloom Isles

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

### 6.6 Neon Harbour and the Skyport

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

### 6.7 Halcyon Station

320 x 576 px, unchanged: rooms in the order of the climb, from the elevator's airlock at the bottom through hydroponics, the galley, the atrium and the sleep bay, to the shuttle hatch (W9) and the lounge under the windows. From the airlock: hydroponics 3.4 s, the atrium 6.3, the hatch 10.7, the lounge window 12.2. A station is a building; one screen of rooms is enough.

### 6.8 Lumen

384 x 704 px (today 320 x 576): the pad on the crater's rim (T2), the habitat with its solar arrays and the ice rig in the shadowed crater (T1), the pressure tube down to the dome on the crater floor (T0), the moon tree and the hammock. From the pad: the habitat 8.5 s, the moon tree 13.9, the hammock 16.4. A little wider so the crater reads as a crater on a 300 px screen.

## 7. Space: the rocket

**The launch site.** The Launch Cape: a flat cape of salt flats east of the city's Point, 8 s from the Skyport by the Cape Road. A real spaceport launches over the sea, away from towns, and this one does. Its parts:

- a pad with a service tower;
- a fuel farm (spherical tanks behind a blast wall);
- a low control bunker;
- a visitors' bench behind the fence;
- the rocket standing on the pad, visible from the Skyport and on clear days from Driftwood.

**What replaces what.** The rocket replaces the space elevator: the elevator's anchor and ribbon go from the Skyport, and its pier serves the coastal steamer. Halcyon keeps a small lander for the last leg to Lumen, because a rocket from the ground to the moon by way of a station is how a real trip would go, and the station is where you change.

- **W8, the rocket:** while it is closed, the rocket stands on the pad under its service tower, the fuel farm's gauges read empty and a technician explains. Open, the tanks are full and frost forms on the rocket's skin (fuelled). Ride from the pad to Halcyon's docking ring.
- **W9, Halcyon's lander:** as #95 ("under a cover, a star chart with a gap"). Ride from the station to Lumen's pad.

**The animations** (journey scenes, like the train's; finite, skippable with one SKIP, and three stills with a cross-fade under reduced motion; AGENTS.md):

- _Launch, about 8 s._ The service arm swings back. Vapour vents from the tanks. A countdown on the bunker's board reads 3, 2, 1 as pictograms. Ignition: the flame, then a ground cloud billowing out over the pad. Lift-off is slow, then faster, and the camera follows. The cape and the coast shrink below, the city's lights show at night, and the sky darkens from blue through violet to black. Stage separation is a small spark and a falling stage. Then the curve of the planet, and Halcyon's ring growing ahead. Docking: the ring's arm meets the rocket's nose, and the airlock light turns green.
- _The lander, about 6 s._ Undocking, a burn, Lumen growing ahead. Then the descent over the crater: a retro-burn with a dust plume, the legs touch, a settle bounce, the dust clears.
- _Coming back._ The rocket lands upright on the cape's pad: a landing burn, its legs out, steam. The lander lifts off from Lumen's pad. The reverse journeys reuse the same frames, played backwards where that reads right.

## 8. The ways on the routes

The nine ways (#95, decided) keep their names, order and tasks. On the continent each one is a thing on a route being mended. Where a place has two ways in, one way mends both (as W2 already did).

| #   | Way                                 | What is being mended                                                                                         | Where               | In reach after (#95) | Why it waits (in the world)                                           |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------- | -------------------- | --------------------------------------------------------------------- |
| W1  | The Headland stile                  | the stile's broken step                                                                                      | the Headland's wall | the start            |                                                                       |
| W2  | The ridge col                       | two pines from one storm, across the col and the gully                                                       | the Frostline       | the start            |                                                                       |
| W3  | The Millrace landslip               | the gorge's towpath and line under a landslip, and a rockfall at the Hill Path's stair foot (the same storm) | the Brackens        | the start            |                                                                       |
| W4  | The Shell Bar and the ferry         | a washed-out stretch of the causeway; the ferry holed on the slip                                            | the strait          | the start            |                                                                       |
| W5  | The Dry Wash bridge                 | the bridge carrying the Drover's Road and the desert line                                                    | the downs           | W3                   | you reach it only through Cogsworth                                   |
| W6  | The chasm bridge and the Ember Pass | the bridge's missing span; a rockfall on the pass                                                            | the fire country    | W5                   | the masons come from Dust Gulch                                       |
| W7  | The swing bridge                    | stuck open; it needs a gear from Cogsworth's foundry (the maglev waits for the same power)                   | the Neon river      | W3                   | the gear is cast in Cogsworth, so the city waits for the valley train |
| W8  | The rocket                          | the launch not yet fuelled                                                                                   | the Launch Cape     | W7                   | the cape lies past the city                                           |
| W9  | Halcyon's lander                    | under a cover, the star chart incomplete                                                                     | Halcyon Station     | W8                   |                                                                       |

**The gate check** (`gates.json`, from the block-out). With the ways opened one at a time in road order, a flood fill from the hut reached nothing behind a closed way, and everything behind an open one, at every step. The test `lib/world-ways.test.ts` (#118) should do the same on the real walk grid once the canvases exist.

**What changes in #95 and #118.**

- A line is no longer a way of its own: W3, W5 and W7 each open a route and its line together, and W4 opens the Shell Bar and the ferry.
- W8 becomes the rocket (it was the space elevator).
- The barriers become cell sets in world coordinates. The `plannedZones` (`hill`, `terminus`) become areas.
- The order and the tasks are unchanged.

## 9. The engine: one world canvas

### 9.1 What v2 proposed (decided)

v2 replaced the fixed 320 x 576 zones with region canvases streamed in 256 px tiles, and Matt decided it (decision 2). Its reasons stand: no seams inside a region, sizes that follow the places, props anywhere, and 9 to 12 MB of decoded pictures in view instead of 24 to 47 MB.

### 9.2 Region canvases joined by routes, or one world canvas

|                     | Region canvases joined by route canvases                                                           | **One world canvas, authored in chunks**                                                                                                           |
| ------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Seams               | back at every region and route edge (ports, border painting, border lint, props that cannot cross) | none on the continent                                                                                                                              |
| Transitions         | painted twice, on both sides of each seam                                                          | painted once, across the band                                                                                                                      |
| Saves, map, walking | a region id plus a point; walking from a route into a region switches canvas                       | one point in world coordinates; one walk                                                                                                           |
| Distant landmarks   | must be faked per canvas                                                                           | are simply there, drawn at the far scale where a sightline needs them                                                                              |
| Build               | per canvas                                                                                         | per chunk (a region or a route with a margin for its transitions), composited onto world tiles; only the tiles a changed chunk touches are rebuilt |
| Memory on a phone   | 9 to 12 tiles in view                                                                              | the same                                                                                                                                           |

**Recommendation: one world canvas** for the continent. Halcyon, Lumen and the hut's inside stay canvases of their own, reached through a door or a journey.

The numbers, from the block-out:

- **Size:** 8320 x 4928 px, 1040 x 616 cells.
- **Tiles:** 660 render tiles of 256 px. 361 are uniform (300 sea, 37 forest, the rest peaks, rock and basalt), so they share about seven pictures. That leaves about 300 drawn tiles, and 270 of them hold walkable ground. Today's 36 zones are about 100 tiles' worth of area, so the art to draw roughly triples. Most of the new ground is countryside; detail goes where the routes and their landmarks are (rule 2), and quiet countryside is drawn with the same care but fewer props.
- **Memory:** unchanged from v2: 9 to 12 tiles in view, 9 to 12 MB at 2x, about 3 MB at 1x.
- **Walk grid:** 2.56 million cells of 4 px in all. That is too large for one exported string, so the walk grid, the terrain and the tiers are exported per tile (64 x 64 cells each) and loaded with the tile. A tap walk searches a window round the companion (about 1024 px). A walk to a far place (the map) runs on a coarse graph of the routes, then refines in the window.
- **Build:** a chunk is drawn in world coordinates inside its bounding box plus a 256 px margin for its transitions; the composite runs per tile. A full build is about six times today's ground area, so per-chunk caching is part of the first PR, not an afterthought.

### 9.3 What the region-canvas builder (step 1, branch `claude-a/region-canvas`) should change

1. **Give every canvas a world origin.** A region or route chunk is placed at a world (x, y) on the 8 px grid (section 3.1), not at (0, 0) of its own canvas.
2. **Key tiles by world tile coordinates** (tx, ty) on one world grid of 256 px, so a region's edge can fall inside a tile and two chunks can share one. Composite the chunks onto the tiles.
3. **Export walk, terrain, tiers and stands per tile**, not per region; keep areas (names, map, saves) as a separate small table of rectangles or masks in world coordinates.
4. **Deduplicate uniform tiles** (sea, peaks, forest) to one picture each.
5. **Cache per chunk**: rebuild only the tiles a changed chunk touches.
6. **Keep the compatibility cut** into today's 320 x 576 zones for now, so the app runs unchanged until the renderer streams tiles.
7. **Leave room for routes and transitions**: a chunk declares its bounding box and a margin band where it blends into its neighbour. The background (biomes between chunks) is a chunk of its own.

## 10. Order of work and owners

| Step | Lane | Work                                                                                                                                                                                                                             | Needs                         |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| P0   | A    | The toolkit lands (`terrace.py`, `scale.py`, tiers, the facade composer, `fore.png`)                                                                                                                                             |                               |
| P1   | A    | **The world canvas build**: chunks with world origins, world tiles, per-tile walk and terrain, dedupe, per-chunk cache, the compatibility cut into today's zones (section 9.3)                                                   | P0; Matt's yes to decision 13 |
| P2   | A    | The renderer streams world tiles; a windowed walk with a coarse route graph; areas for names and the map; the hub as a window on the world; saves in world coordinates (with Codex for `lib/save-data.ts`); tests                | P1                            |
| P3   | A    | The background chunk: the coast, the Northern Range, the Brackens, the Dry Wash, the Neon river, biome bands and their transitions; distant landmarks as far-scale silhouettes                                                   | P1                            |
| P4   | B    | Props to the scale table and #97: the valley's library first, then the route props (lock-keeper's cottage, kiln, drovers' inn, windpump, stock pens, smokehouse, bothy, refuge, tide post, fuel farm, service tower, the rocket) | P0                            |
| P5   | E    | The valley chunk (section 6.2 with the changes in 6.1)                                                                                                                                                                           | P1, P4                        |
| P6   | A    | The Frostline, the Hill Path and the Canal Road (with the Brackens' gorge)                                                                                                                                                       | P3                            |
| P7   | D    | Sunstone Reach mirrored (6.4), the Drover's Road and the Ember Pass; then Halcyon, Lumen and the Launch Cape with the rocket and lander scenes                                                                                   | P1                            |
| P8   | C    | Cogsworth (6.3); Neon (6.6) with its river and swing bridge, the Eastern Road and the Coast Path; the isles with the Shell Bar (6.5)                                                                                             | P1                            |
| P9   | A    | The ways on cells (#118 to world coordinates and areas), the journeys as shortcuts, the map                                                                                                                                      | P2, #95's rules (Codex)       |

The valley goes first among the chunks, because it is home and its props become the library the others copy. The background chunk (P3) goes early, because every other chunk blends into it.

## 11. Decisions for Matt

**Decided (Matt, 20 Oct, about 10:50):** decisions 1 to 7 below (v2).

| #   | Decision                                                                                                                                   | Recommendation or decision                         | Why                                                                                                                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | The zoom: keep 12 adults across (`ART_ACROSS` 300)?                                                                                        | **Decided 20 Oct: keep.**                          | It matches Eastward and Stardew across and keeps 44 px targets.                                                                                     |
| 2   | Replace the 320 x 576 zone grid with canvases streamed in 256 px tiles, zones becoming named areas?                                        | **Decided 20 Oct: yes.**                           | No seams, sizes from the places, less memory.                                                                                                       |
| 3   | Size places from the sizing table, with everyday places within 15 s of the hut?                                                            | **Decided 20 Oct: yes.**                           | What the scale table implies.                                                                                                                       |
| 4   | The valley at 1280 x 2688 with a real village, a farmstead and Driftwood as its own hamlet?                                                | **Decided 20 Oct: yes.**                           | Home is worth the most ground.                                                                                                                      |
| 5   | Cogsworth at 704 x 960 with Gasworks Hill and the Terminus?                                                                                | **Decided 20 Oct: yes.**                           | A loop, a second tier, a home for the maglev.                                                                                                       |
| 6   | Neon's canvas a quarter smaller, with more walkable street?                                                                                | **Decided 20 Oct: yes.**                           | About 40 buildings at true scale is enough.                                                                                                         |
| 7   | Sunstone Reach as one continuous land?                                                                                                     | **Decided 20 Oct: yes.**                           | It keeps Claude D's work and removes the L of tiles.                                                                                                |
| 8   | One continent in world coordinates, as in section 3 (fire country and desert west, Cogsworth, the valley, the city east, the isles south)? | **Yes.**                                           | It is the map Matt asked to work out first; the theme reads as geography.                                                                           |
| 9   | Mirror Sunstone Reach so its oasis faces the downs and its castle the volcano?                                                             | **Yes.**                                           | The region faces the land it trades with. The generator mirrors its layout, not its pictures: every prop and face is still lit from the upper left. |
| 10  | The eight routes, 8 to 40 s each, with their barriers (the Brackens, the Dry Wash, the Neon river)?                                        | **Yes.**                                           | Every region has two ways in, four loops, and the ways stay at chokepoints.                                                                         |
| 11  | Trains, the ferry and the maglev as shortcuts that open with their route's way?                                                            | **Yes.**                                           | Matt asked for trains as shortcuts; one way per route keeps #95's nine.                                                                             |
| 12  | A rocket from the Launch Cape replaces the space elevator; Halcyon's lander takes you on to Lumen?                                         | **Yes.**                                           | Matt asked for a rocket; the station stays the place where you change.                                                                              |
| 13  | One world canvas, authored in chunks and streamed in tiles, instead of region canvases joined by routes?                                   | **Yes.**                                           | No seams anywhere on the continent; the same memory; one coordinate system.                                                                         |
| 14  | W7 stays in reach only after W3 (the swing bridge waits for a gear from Cogsworth), though you can walk up to it from the start?           | **Yes.**                                           | The screen city comes later, with a reason you can see; the bridge is a view of what is to come.                                                    |
| 15  | The coastal steamer (S3) from the Skyport to Driftwood once W7 is open?                                                                    | **Yes, later.**                                    | It closes the sea loop: home from the city by sea.                                                                                                  |
| 16  | Ground pictures at 1x (or 2x) instead of 4x?                                                                                               | **Test, then 1x if crisp on all three platforms.** | Sixteen times less decoded memory.                                                                                                                  |
| 17  | Secret pockets hold a view, a resident or a story detail, never a keepsake?                                                                | **Yes.**                                           | No rewards for decorative places.                                                                                                                   |
| 18  | No one-way hops down low steps for now?                                                                                                    | **Yes, for now.**                                  | Tap-walking stays predictable.                                                                                                                      |
| 19  | The companion stays 24 px tall?                                                                                                            | **Keep.**                                          | Every size here assumes it.                                                                                                                         |

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
