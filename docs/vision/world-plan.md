# The world plan (v5.1): a window onto a larger continent

Matt, 20 Oct:

- 01:05: "All of these need redesigns pretty much, to fit the newly established soft grids. also consult the other games mentioned for world buildings how large parts of the maps should be and how they are attached together and how you can create interesting spaces."
- 10:32: "really think deeply of the sizing of everything and the map".
- 10:58: "work the whole world map out first and how everything connects (with as many physical connections as possible as well, with trains as short cuts) ... the world should feel expansive with natural looking boundaries and no abrupt cuts".
- About 11:45, on v3: "make the world roughly twice that size and everything fits together nicely and is not just stitched together. with natural transitions and not just a line. look into pokemon world design or eastward". On Sunstone Reach: "make it immersive".
- 12:25, on v4: "getting better but you need to make it more natural and think critically where each section fits in on the map and design the terrain around it to fit that. the mountains simply running in between desert and grass is not convincing yet. also is this supposed to be an island? i feel like the world map should be a piece of a larger continent with natural world borders with the island bit of the map on the bottom".
- 12:36: "can u also create one intricate larger river flowing naturally with two or three larger bridges that cross the river and possibly smaller rivers/ canals elsewhere. also think critically where the volcano/ lava world fits and how far away other parts should be. having a harbour city similar to the first of the four screenshots provided earlier could be cool (but make sure the city building and placement make sense). more empty parts of the maps should first be planned out along natural footpaths or other sorts of paths and the terrain should be build around it (e.g. canyons in the desert parts, forests in the woodlands, the large river, a mountain passage etc.). perhaps there are little easter eggs dotted around the world (but that can be handled later".
- About 14:45, on v5: "go with A more or less. this is starting to look really good. i do look the different regions. it is important that you get the transitions from one zone into the other right. while staying relatively realistic make them distinct and interesting from a game play perspective (i'm not trying to recreate earth but build a semi realistic game). also getting the verticality right in different parts of the map is super important".

**Status: a plan, partly decided.** These stand from earlier versions: v2's sizing table and decisions 1 to 7; v3's rocket, lander and one world canvas (decisions 8 and 9). Matt chose arrangement A at about 14:45 (decision 11). Everything else in section 16 is a recommendation.

v5 keeps v4's size, walk times, routes-and-shortcuts logic and the nine ways, and redraws the land. The map is now a window onto a larger continent: the sea and the isles lie only along the south, and the land runs on past the other three edges behind natural borders. Each place was put first where people would live, and the terrain was then shaped to give it what it needs. One great river, the Lull, crosses the east of the map from a glacier to a delta. The harbour city, Neon Harbour, wraps round a deep ria east of the delta, after Matt's first example. The volcano stands where the geology puts it, on a coastal arc whose rain shadow makes the desert. The paths were laid first and the ground fitted round them.

**v5.1** is a refinement pass on arrangement A. It answers Claude A's critique and Matt's note of 14:45.

- **The Lull** now widens with each tributary and meanders in a real belt: point bars, scroll bars, a fresh oxbow and a silted one, willow carr, a braided reach. It runs through a gorge at the Narrows and ends in a branching delta.
- **Neon Harbour** is drawn as organic districts wrapping the whole ria.
- **The west.** The dry-to-wet change follows the arc's rain shadow, so it no longer runs as north-south stripes. The Rift winds and has side canyons.
- **No placeholders.** The Frostline is a cirque in the relief; Hearthold is a walled hill town; fields follow the roads; the massif has peaks and glaciers.
- **Transitions are designed as places** (5.2), **each region has its own identity** (5.3), and **verticality is set out region by region on the soft grid's tiers** (5.4).

It builds on, and does not repeat:

- `verticality.md` (the soft grid and the scale table).
- `art-style.md` (Eastward's detail; each setting its own style).
- `prop-logic.md` (#97).
- `world-unlocks.md` (#95, decided: nine ways, one a day) and the ways catalogue (#118).
- `world-rules.md`, `world-ports.md`, `world-atlas.md`.
- `../research/2d-world-design.md` and `research/*.md`.

**The images** are not in the repository. Claude A has them in its scratchpad (`worldplan5/`), drawn by a script (`geo5.py`) from a height field, a wetness field, the rivers and the paths, at 1 px per 8 px cell:

| File                                                                                                                                                                                                                     | What it shows                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `thumbnails.png`                                                                                                                                                                                                         | three arrangements of the same places, sketched small (section 4.4); A is developed                                                                                   |
| `physical-map.png`                                                                                                                                                                                                       | the land before people: ground, height tint and rivers, with the natural regions named                                                                                |
| `continent-1x.png`                                                                                                                                                                                                       | the developed map with every kind of ground, hill-shaded from the upper left (1408 x 864); land beyond the walked corridors is a little hazier                        |
| `continent-labelled.png`                                                                                                                                                                                                 | the same at 2x with settlements, routes, rivers, bridges, huts, shortcuts (dashed), the ways (red) and the reserved easter-egg spots (small rings); no labels overlap |
| `overview-32px.png`                                                                                                                                                                                                      | 1 px per 32 px (352 x 216)                                                                                                                                            |
| `ingame-map-mock.png`                                                                                                                                                                                                    | the in-game map in the soft-grid style (section 12)                                                                                                                   |
| `river-and-bridges.png`, `harbour-city.png`                                                                                                                                                                              | the Lull from the Narrows to the delta with its three bridges; Neon Harbour round its ria                                                                             |
| `region-valley-and-frostline.png`, `region-cogsworth-and-the-narrows.png`, `region-sunstone-basin.png`, `region-fire-country.png`, `region-isles.png`                                                                    | crops per region                                                                                                                                                      |
| `route-drovers-road.png`, `route-ash-coast.png`, `route-canyon-road.png`, `route-lull-road-coast-path-towpath.png`, `route-high-fells-col-path-foothill-road.png`, `route-shell-bar-headland.png`, `route-cape-road.png` | crops per route                                                                                                                                                       |
| `stats.json`, `gates.json`                                                                                                                                                                                               | sizes, walk times, the "why here" lines, the bridges, the egg spots; the gate check (section 10)                                                                      |

**The v5.1 images** come from `geo51.py`, which builds on `geo5.py`. They carry the suffix `-v51`, and v5's files are kept beside them:

- every file above, with the suffix;
- `tier-map-v51.png`: the tiers, faces, stairs, ramps, switchbacks, lifts and thresholds (5.4);
- `frostline-v51.png`, `hearthold-v51.png` and `delta-v51.png`: close crops;
- `before-after-river.png`, `before-after-harbour-city.png` and `before-after-west.png`: v5 on the left, v5.1 on the right.

Matt's example maps (a fantasy city, a soft-grid tier map, all the Pokémon regions joined, Stardew's map) are in `refs-matt/maps/`, for reference only.

## 0. In short

1. **A window onto a continent.** The sea and the Tidebloom Isles lie only along the south. The other three edges are natural borders, and the land is drawn going on beyond each: the high massif and its glaciers in the north, an open dune sea in the west, and moss fens and old forest in the east.
2. **One geology explains the land.** An ocean plate dives under the continent along the south coast. That raises a volcanic arc parallel to the coast (the Ember range), with Mount Ember the one cone still alive and the Tidebloom Isles its drowned eastern end. The arc takes the sea wind's rain, so the land behind it dries westward over some 6 km into the Sunstone basin. This is the Cascades and the dry plateaus east of them, with the Tarim Basin's oasis rivers along the mountain foot. Mountains no longer run between desert and grass: the massif closes the north of both, and the change from meadow to dune sea is a wide gradient.
3. **One great river, the Lull.** It rises at a glacier in the north-east massif, takes the Sorrel, cuts the Narrows gorge through the coal hills with rapids, takes the Cog, braids round gravel islands, meanders across its floodplain past two oxbow lakes, narrows at Lullford and splits into a three-armed delta. It is 200 px (25 cells) wide at its mouth. Three landmark bridges: Lullford's old stone bridge with a swing span (W7), the Narrows Viaduct (the maglev) and the Harbour Bridge in the city.
4. **Neon Harbour is the harbour city of Matt's first example**, on a deep ria east of the delta (clear of the river's silt), with the old town on a rock between two waterfalls, docks on the deep side, terraces on the Heights, a fishing strand, two islets and a long bridge.
5. **Paths first.** Every stretch between places follows a path people would use (a drove road, a mule track, a canyon trail, a pass with switchbacks and a hut, a towpath), and the ground is fitted to it.
6. **The same size and pace as v4:** 124.6 walkable zone-areas on an 11264 x 6912 px canvas. From the hut: Fernhollow 25 s, Driftwood and the Frostline 40 s, Cogsworth 52 s (28 s by train), Neon 115 s (56 s), Dust Gulch 99 s (29 s), Hearthold 133 s (53 s).
7. **The ways sit at real barriers**: the Frostline's rim, the Cog, the Rift gorge, the lava flows, the Lull and the sea. The flood-fill check passes at every step (v5 and v5.1).
8. **Transitions are places (v5.1).** Each region change on a route has a threshold, a mixing band, a landmark and a beat: the Brackens gap, Drover's bridge, the Cinder Rise, the Millrace cutting, Lullford Bridge and more (5.2). Each region is pushed to its own colour, landform, vegetation and silhouette (5.3).
9. **Verticality region by region (v5.1).** One tier is a 32 px face. Each region has its own vertical character and its own way up and down: the massif's switchbacks, the valley's terraces, the coal hills' benches and the Narrows gorge, the desert's mesas and canyon floors, the lava terraces and the crater rim, the city's terraces down to the quays, the coast's cliffs against the flat delta (5.4, `tier-map-v51.png`).
10. **v5.1's numbers:** 123.6 walkable zone-areas. From the hut: Cogsworth 52 s (25 s by train), Neon 115 s (56 s), Dust Gulch 100 s (29 s), Hearthold 129 s (61 s, now inside its walls).

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

## 3. How Pokémon regions and Eastward's world hold together

**Pokémon builds each region on a real land, so its geography arrives already explained.**

| Region | Based on                                                                                                                                                 | Source                                                                                                                                         |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Kanto  | the Kantō region, "very similar geographically", with Mount Fuji, Mount Akagi and the volcano Mount Mihara behind Route 28, Mt. Moon and Cinnabar Island | [Bulbapedia, Pokémon world in relation to the real world](https://bulbapedia.bulbagarden.net/wiki/Pokemon_world_in_relation_to_the_real_world) |
| Johto  | "geographically more similar to the Kansai region and the western Chūbu region combined"                                                                 | same                                                                                                                                           |
| Hoenn  | Kyūshū and nearby islands                                                                                                                                | same                                                                                                                                           |
| Sinnoh | Hokkaidō                                                                                                                                                 | same                                                                                                                                           |
| Unova  | New York and its metropolitan area                                                                                                                       | same                                                                                                                                           |
| Galar  | Great Britain, rotated                                                                                                                                   | same                                                                                                                                           |
| Paldea | the Iberian Peninsula                                                                                                                                    | same                                                                                                                                           |

What the regions do with that land:

- **A spine divides the land.** In Sinnoh, Mount Coronet "splits Sinnoh into two halves"; its snowy north is sparse and its west rural, with a canyon fed by a river off the mountain (`../research/2d-world-design.md`, from Bulbapedia).
- **A volcano shapes the country downwind.** In Hoenn, "the tall grass on this route is painted a dusty gray by the volcanic ash that pours from Mt. Chimney" ([Bulbapedia, Hoenn Route 113](https://Bulbapedia.Bulbagarden.net/wiki/Hoenn_Route_113)).
- **Mountains close a region's ends, a wild middle joins its towns, and trains run where the routes do not.** Galar's Crown Tundra "is isolated from the rest of the mainland by a tall mountain range". "The Wild Area encompasses the middle section of Galar", between its two main cities. "It is impossible to travel through Galar using just these routes"; "a train system connects different cities and towns" and crosses the southern mountains ([Bulbapedia, Galar](https://bulbapedia.bulbagarden.net/wiki/Galar)).
- **A centre, provinces round it, and climates from geography.** Paldea is "a large peninsula bordered by four seas", with the Great Crater "at the center of the region, bordered by the four provinces on all sides"; the west has "large expanses of sandy desert", the north "a snowy range crowned by a towering mountain", and the coast "beaches, sandbars, and scattered offshore islets". Its north route "cuts through caves in the mountain range" ([Bulbapedia, Paldea](https://bulbapedia.bulbagarden.net/wiki/Paldea)).
- **A plan before the land.** Unova started from a hexagon with "the equivalent of Manhattan in the center" (Iwata Asks, in `../research/2d-world-design.md`).
- **Sizes** (exact, from the disassembly; section 1.3): a town is 1.6 x 0.8 to 3.9 x 1.6 of our zones, a route 22 to 90 s.
- **Matt's example 3**, every region joined on one world, shows the result. Routes are orthogonal lines with towns as nodes along them. Coasts are irregular and island chains run off them. Snow lies in the north and a desert in the interior. Sea routes join the landmasses.

**Eastward is a journey through a sequence of places.** It follows the characters out of their underground town by train, "eastward". Each chapter brings "a set of map areas to explore", reached on the trains Charon and Monkollywood ([Wikipedia](<https://en.wikipedia.org/wiki/Eastward_(video_game)>)). Its towns are dense and lived-in, drawn from "Kowloon Walled City", "packed with unique and quirky characters" ([Nintendo](https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward); [Game Developer](https://www.gamedeveloper.com/disciplines/road-to-the-igf-pixpil-s-i-eastward-i-)). No developer source found here describes how its maps join; the store screenshots (`research/world-references.md`) show the joins inside a place: ledges, stairs, bridges, tunnels.

**What we take.**

1. Start from a land that explains itself: a spine, a rain shadow, a volcano, one river system, a coast with shelter.
2. Put a wild, open middle between the towns (Galar's Wild Area is our plains).
3. Close the ends with mountains and sea.
4. Join the towns by routes in a rhythm of town, route, town, with trains as the quick way where the land is long.
5. Make each journey a sequence of places (Eastward). Inside a town, density; between towns, space.

## 4. The geography

### 4.1 The frame: a piece of a larger continent

The map is a window. Three of its edges are land that goes on, and each has a border that explains why the walk stops there. The land beyond is drawn, not walked.

| Edge  | Border                                                                                                                                                                               | Why you cannot go on                                                        | What is drawn beyond                                                      |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| North | the northern massif: a broad mass of peaks of varying height, snow above about 0.8 of the height range and glaciers above that, cut by the valleys of the Rift, the Cog and the Lull | glaciers, crags and icefalls; the rivers come out of gorges no path follows | peaks and ice to the top edge, river gorges running on north              |
| West  | the dune sea: open erg at the far end of the Sunstone basin                                                                                                                          | no water at all; the oasis rivers die in the sand long before               | dune ridges running off the edge                                          |
| East  | the moss fens (a raised bog with meres on the eastern uplands) and, north of them, the old forest                                                                                    | a bog that will not bear a cart; old forest with no paths                   | fens and meres, then forest, to the edge; the Glint comes out of the fens |
| South | the southern sea, with a coast of coves, headlands, cliffs and a delta                                                                                                               | the sea                                                                     | the Tidebloom Isles, and open sea                                         |

### 4.2 The land, physically

| Feature                       | What it is                                                                                                                                                                                                                                          | Why it is there                                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **The northern massif**       | a broad range along the whole north, its front irregular, with spurs reaching south: the Brackens (a low wooded ridge west of the valley), the Fern hills (the valley's east wall), the coal hills (round Cogsworth and the Narrows), the Lode spur | the continent's old core, raised where it meets the arc's back                                     |
| **The Ember range (the arc)** | a chain of worn volcanic hills along the south-west coast, highest at Mount Ember, low and broken east of it to the Rift                                                                                                                            | the ocean plate diving under the coast melts at depth and feeds a line of volcanoes parallel to it |
| **Mount Ember**               | the one live cone: a small crater with a lava lake inside a crag rim, two young flows from the crater to the sea, old weathered flows and parasitic cones on its flanks, ash blown north by the sea wind                                            | the arc's youngest vent                                                                            |
| **The Sunstone basin**        | a raised dry plain between the arc and the massif, falling to a salt lake at the arc's foot; dune sea in the far west                                                                                                                               | the arc takes the rain; the massif blocks the north; it is the farthest land from open sea         |
| **The Rift**                  | a deep gorge cut by a river from the massif to the sea at the basin's eastern edge                                                                                                                                                                  | the basin stands higher than the plains, and the river cut down through its edge                   |
| **The Lull**                  | the great river (4.3)                                                                                                                                                                                                                               | it drains the wet north-east                                                                       |
| **The Sleepwater**            | a short river from the Frostline's tarn through the home valley to Driftwood's cove                                                                                                                                                                 | snowmelt from the cirque, the valley the glacier left                                              |
| **The valley**                | a sheltered basin at the massif's foot between the Brackens and the Fern hills, open only to the sea                                                                                                                                                | worn out by the glacier that left the Frostline                                                    |
| **The Frostline**             | a cirque high in the massif above the valley, with a tarn and a crag rim; the Sleepwater leaves over its lip                                                                                                                                        | a glacier carved it                                                                                |
| **The Lull plain**            | the low, wet land between the valley, the coal hills and the Lull, with copses, fields and creeks                                                                                                                                                   | the river's old floodplain                                                                         |
| **The eastern uplands**       | a low plateau east of the Lull, ending in a scarp at the coast; the moss fens on top, the Glint crossing it                                                                                                                                         | a block of older rock; the scarp is why the Glint falls into the sea                               |
| **The coast**                 | coves (Driftwood, Gullwick, Cinderwick), the Headland on its neck, black cliffs where the arc meets the sea, the delta's lobe, the ria, the Launch Cape                                                                                             | shelter where there is shelter, cliffs where hills meet the sea                                    |
| **The Tidebloom Isles**       | eight islands from the volcano eastward; the main isle's lagoon is a drowned crater breached on its south side                                                                                                                                      | the arc's drowned end                                                                              |

### 4.3 The great river, its bridges and the smaller waters

**The Lull's course**, from source to sea (`river-and-bridges.png`):

1. **The glacier and the upper valley.** It rises at a glacier snout in the north-east massif and runs south down a high valley, 36 px wide.
2. **The Sorrel joins** from the north-east, out of the old forest.
3. **The Narrows.** The Lull cuts through the coal hills in a gorge about 1 km long, 44 px wide, white with rapids. The railway (now the maglev) crosses it on the Narrows Viaduct.
4. **The Cog joins** below the gorge, fast and dark from the coal hills.
5. **The braided reach.** Below the confluence the river spreads over gravel round six long gravel islands.
6. **The meander belt** (v5.1: a sine-generated curve, after Langbein and Leopold's model of meanders). The loops vary in size, and the channel widens at each bend. Each bend has sand on its inside (a point bar) and scroll bars beyond it; on its outside is a cut bank. A fresh oxbow lies hard by an outer bend, and an older one, silted to reeds, lies further out. Water meadows and willow carr cover the floodplain.
7. **Lullford.** Gravel terraces close in on both banks, and an island sits mid-river. This is the lowest place it can be bridged, so the old road crosses here and the town grew round the bridge.
8. **The delta.** Below Lullford it branches into a network of uneven arms: eight reaches from one apex, the widest about 70 px. Between them lie reed beds; in front, mudflats; at each mouth, a sandbar; and the delta builds a lobed front into the sea.

**Width grows with the water** (v5.1). The Lull is about 28 px at the glacier and grows with the Sorrel. It is pinched in the Narrows, gains with the Cog, and reaches about 110 to 130 px (14 to 16 cells) on the floodplain. Lullford's terraces narrow it to under 120 px. Widths change gradually, never in a jump.

**The three landmark bridges.**

| Bridge          | Where and why there                                                                                  | Character                                                                                                                      | Way                               |
| --------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| Lullford Bridge | the lowest bridging point, where terraces narrow the floodplain and an island takes the middle piers | old stone arches from both banks to the island, and an iron swing span over the navigation channel for the barges              | **W7**: the swing span stuck open |
| Narrows Viaduct | the gorge's narrowest point, where the railway had to cross from Cogsworth to the east bank          | tall piers on the gorge walls above the rapids; rail only, never a footway                                                     | the maglev opens with W7          |
| Harbour Bridge  | the ria's middle, using Chapel Islet as a pier, between the Heights and the docks                    | two high arches, tall enough for masts, with the chapel on its islet beside the roadway; the city's landmark seen from the sea | inside W7                         |

**The smaller waters.**

- _The Cog's Millrace_: a leat off the Cog through Cogsworth's mills and back.
- _The Lull Cut_: a canal with a towpath from Lullford's east bank to the canal basin under the Heights, so barges reach the port without going through the silted delta (Alexandria was fed by "a canal from the Nile", sited "removed from the silt thrown out by the Nile": [Wikipedia, History of Alexandria](https://en.wikipedia.org/wiki/History_of_Alexandria)).
- _Irrigation channels_ from Palm Spring and Dust Gulch through their orchards, narrow enough to step over.
- _The Glint_: out of the moss fens, across the uplands, splitting round the Falls Rock and falling into the head of the ria.
- _The Amber and the Willow Run_: snowmelt rivers that die in the basin, the Amber in the salt lake, the Willow Run in the sand.
- _Creeks_ drawn from the drainage of the height field: on the wet side only, fordable, never barriers.

### 4.4 Three arrangements, and the one developed (`thumbnails.png`)

| Option                                         | The arrangement                                                                                                                                                                                                     | For it                                                                                                                                                           | Against it                                                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **A: the arc and its rain shadow (developed)** | massif across the north; a volcanic arc along the south-west coast with the dry basin behind it; the valley in the middle; the great river in the east to a delta; the city in a ria east of the delta; isles south | one cause explains the desert, the volcano and the isles; the desert sits beside the green land and fades into it; the river is the east's spine and its barrier | the volcano is far from the city (that suits the order of the ways)                                                 |
| B: the river down the middle                   | the great river splits the land down the centre; the desert lies north beyond a broad pass in the massif; the volcano is an offshore hotspot island                                                                 | a strong central axis                                                                                                                                            | the desert is behind a wall again, which is what Matt found unconvincing; the hotspot leaves the isles unexplained  |
| C: dry east behind its own coastal range       | the mirror of A: the basin in the east behind a coastal range, the city in the west at a river mouth                                                                                                                | same logic as A                                                                                                                                                  | the home valley's neighbours (Cogsworth, the city) swap sides, so every existing place moves; nothing gained over A |

### 4.5 Why each place is where it is

The places came first. Each needs something; the terrain was then shaped to give it that.

| Place           | Why here                                                                                   | How the terrain gives it                                                                                                      | Size (sizing table)            |
| --------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| The home valley | a sheltered basin where the Sleepwater leaves the uplands: water, a mill head, flat ground | a basin worn into the massif's foot, the Brackens to the west, the Fern hills to the east, the Frostline above, the sea below | 1280 x 2688 (decided)          |
| The Frostline   | the glacier's cirque above the valley, the Sleepwater's source                             | a bowl carved into a high shoulder of the massif, a crag rim, a lip over which the river leaves                               | as v2                          |
| Driftwood       | the valley's landing place                                                                 | a cove at the Sleepwater's mouth, sheltered by the Headland to the east                                                       | 544 x 352 harbour              |
| Fernhollow      | timber                                                                                     | the wet woods on the Fern hills' western slope, on the road to Cogsworth                                                      | 320 x 240                      |
| Cogsworth       | coal and iron, power, a way out                                                            | the coal hills; the fast Cog with a fall for the Millrace; the valley floor below for the railway                             | 704 x 960 (decided)            |
| Lullford        | the river crossing                                                                         | the lowest bridgeable point: terraces narrow the floodplain, an island takes the piers                                        | 560 x 420                      |
| Gullwick        | fish                                                                                       | a cove on the open coast west of the delta                                                                                    | 420 x 220                      |
| Neon Harbour    | a port for the whole river and the coast                                                   | a deep ria east of the delta, sheltered by the Heights and the islets, falls at its head (section 8.5)                        | about 1450 x 1100 with the ria |
| The Launch Cape | rockets over open sea, away from people                                                    | an exposed headland south-east of the city                                                                                    | 480 x 360                      |
| Palm Spring     | the first water in the dry country                                                         | the Willow Run sinks into its gravel fan and comes up again here                                                              | 300 x 220                      |
| Dust Gulch      | water, the mine above, the railhead                                                        | where the Amber leaves the massif onto its fan; the desert line's terminus                                                    | 544 x 320 desert town          |
| The Lode        | iron and copper                                                                            | the Lode spur in the massif's foothills, a mule track up                                                                      | 260 x 180                      |
| Hearthold       | the only defensible ground on the volcano's seaward side                                   | a rock between the two young lava flows, below the crater                                                                     | 400 x 400 inside its walls     |
| The Ember forge | the crater's heat                                                                          | the caldera's lip, inside the flows                                                                                           | as v2                          |
| Cinder Springs  | hot springs                                                                                | where sea water seeps into the volcano's warm flank                                                                           | as v2                          |
| Cinderwick      | charcoal and fish                                                                          | a black-sand cove between the flows                                                                                           | 340 x 200                      |
| Lagoon Landing  | sheltered water                                                                            | the main isle's lagoon, a drowned crater breached to the sea                                                                  | as v2                          |

### 4.6 The desert, made believable

**The analogue.** The Cascades are a volcanic arc "produced by the subduction of the Juan de Fuca plate beneath the North American plate", and east of them "in the rain shadow of the Cascades, the climate of the Modoc Plateau is dry" ([LibreTexts, Geology of California 7](https://geo.libretexts.org/Bookshelves/Geology/Geology_of_California/07%3A_Cascade_Range_and_Modoc_Plateau)). The Ember range does the same to the Sunstone basin. The basin's water pattern follows the Tarim Basin (between the Tian Shan and the Kunlun), whose oasis towns sit where snowmelt rivers leave the mountains and whose rivers end in the desert ([Wikipedia, Tarim Basin](https://en.wikipedia.org/wiki/Tarim_Basin); not quoted here, the page could not be fetched).

**How it opens up, east to west** (the developed map; widths are observations on the block-out):

1. **Meadow to steppe** over the Rift country, about 1.5 km wide: grass thins, copses become single trees, the drove road's sheepfolds stand in short grass.
2. **Steppe to scrub** across the Rift itself: the gorge does not divide wet from dry; both its rims are steppe and scrub.
3. **Scrub with oases**: green corridors only along the Willow Run and the Amber, widening into fans where they leave the massif (Palm Spring, Dust Gulch); orchards and irrigation channels; scrub between.
4. **Badlands and mesas** where the Amber and the Rift have cut down: banded slopes along the canyon, flat-topped mesas standing between the cuts.
5. **The salt lake** where the Amber ends at the arc's foot.
6. **Desert, then the dune sea** to the western edge, the dune ridges running off the map.

The massif closes the north of both the desert and the green land, so no range runs between them. The arc's own seaward slope stays green (the windward side), so the Ash Coast is green until the volcano.

### 4.7 Where the volcano goes, and how far

**Geologically.** A volcano of this kind belongs to the arc, which lies parallel to the subducting coast, so it stands on the south-west coast in the arc's line, not in the middle of the land. A hotspot (option B) or a rift volcano would leave the dry basin and the isles unexplained.

**In distance.** It is the last place of the land's road (W6) and the hottest, so it lies farthest from the home valley and beyond the desert. From the hut, about 4 km in a straight line and 133 s on foot to Hearthold (53 s with shortcuts). From Dust Gulch, 75 s down the Canyon Road. From Neon, the far end of the map, about 4 minutes on foot. No buildings stand within the young flows except the forge and the castle on their rock.

**Its buffer, not a ring.** Round the cone, in this order and interleaving:

- ash blown north by the sea wind, thinning from grey ground to a dusting in the scrub (dithered, so there is no edge);
- old flows: weathered lava-stone tongues from flank vents, with scrub or fireweed on them;
- parasitic cones and a fumarole field on the north flank;
- a dead forest where the east flow ran through the coastal woods;
- hot springs and black sand on the seaward side.

The young flows, from the crater to the sea, are the barrier (W6), and they are not a line round the mountain but two tongues with side lobes.

## 5. Transitions and verticality

### 5.1 Bands, not lines

Every biome comes from fields: height, wetness and warmth, with large and small noise, and the wetness field is blurred over about 300 px and warped by up to 500 px before the thresholds. Snowline and treeline sit lower on north-facing slopes. Props follow the same fields (`prop-logic.md`).

| Band                  | From and to                                                                | Width (observed on the block-out)      | Mixed ground and outliers                                                     |
| --------------------- | -------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------- |
| Wet to dry            | meadow, steppe, scrub, desert, dune sea                                    | about 6 km from the valley to the edge | copses in steppe, scrub islands in dunes, green oasis strips across all of it |
| Up the massif         | meadow, broadleaf, conifer, alpine, snow, glacier                          | 600 to 1200 px, by aspect              | pines alone in alpine meadow; snow patches in north-facing hollows; tarns     |
| Into the fire country | scrub or meadow, ash dusting, ash, old flows, basalt, the crater           | about 1300 px, longer downwind         | fireweed on old flows; charred snags; fumaroles                               |
| The floodplain        | fields, water meadow with willows, the river                               | 500 to 700 px each side                | oxbow lakes; shoals                                                           |
| Country to city       | fields, then the canal and towpath, then the Heights' gardens and terraces | about 800 px along the Delta Road      | market gardens out among the fields                                           |
| Coast                 | grass, then dune or cliff, then sand or black sand, then shallows          | 40 to 80 px                            | rocks and driftwood on the beach                                              |

**The walked corridors and the land beyond.** Land farther than about 470 px (plus or minus 200) from a route or a settlement is drawn but not walked. Its own edge stops the walk (a hedge, a wood's edge, a dune crest, a snowfield's lip).

**Views across the land** (scenery, never tap targets): from the Frostline, the whole plain and the Lull shining in the east; from Dust Gulch, the plume of Mount Ember beyond the salt lake; from the Lull Road, Neon's towers beyond the delta; from Driftwood, the isles and the rocket on its cape; from the Narrows Viaduct, the rapids below.

### 5.2 Thresholds: each change of region is a place (v5.1)

Matt, 14:45: "it is important that you get the transitions from one zone into the other right. while staying relatively realistic make them distinct and interesting from a game play perspective". So each boundary a route crosses has a threshold you recognise, a short band where both regions mix, a landmark, and a beat. The thresholds are orange diamonds on `tier-map-v51.png` and circles on `continent-labelled-v51.png`.

| Transition                             | Threshold on the route                                                                    | What mixes (and the outliers)                                                                      | Landmark                                                   | Gameplay beat                                                                      |
| -------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Valley to the massif and the Frostline | the Col Path's switchbacks, the Col hut, then the Frostline lip (a moraine step)          | meadow gives way to conifers, scree and snow patches in shaded hollows; a lone pine above the line | the headwall and the tarn, seen from the hut               | W2 at the lip; the hut as a rest stop with a warden; a view back over the valley   |
| Valley to the Brackens and the steppe  | the Brackens gap: the Drover's Road between two bluffs                                    | heather and gorse on the bluffs; meadow thinning to short yellow grass; the first sheepfolds       | the stone ring on the ridge above                          | the first view west to the steppe and the plume; a drover at the well; an egg spot |
| Steppe to scrub and desert             | Drover's bridge over the Rift gorge                                                       | steppe on both rims; the far side's first cacti and red rock                                       | the gorge, and the desert line's viaduct upstream          | **W5**; the viaduct as the shortcut                                                |
| Desert to canyon                       | the Amber canyon head below Dust Gulch: the road drops off the fan into the canyon        | the orchards end; banded badland walls begin                                                       | a mesa at the canyon's mouth                               | a canyon descent in stairs; shade; the fossil in the wall (egg spot)               |
| Desert to the fire country             | the Cinder Rise: a low lava-stone ridge the Canyon Road cuts through                      | scrub dusted grey; ash drifts; fireweed                                                            | from the top: Hearthold on its rock and the crater's plume | the reveal; then the chasm bridge                                                  |
| Into the fire country (west)           | the chasm bridge over the young west flow                                                 | ash and basalt; heat shimmer                                                                       | Hearthold's walls across the flow                          | **W6**                                                                             |
| Coast to the fire country (east)       | the dead forest, then the crust causeway over the east flow                               | coastal woods turn to snags among fireweed; sand turns black                                       | the flow's steaming toe at the sea                         | **W6**; the Rift ferry (**W5**) before it                                          |
| Plain to the coal hills                | the Millrace cutting: the Foothill Road enters the hills in a cut with walls              | Fernhollow's woods darken to coal-hill forest; the first spoil heaps and pit heads                 | Cogsworth's chimneys and the airship mast                  | **W3** at the Millrace bridge; the valley train                                    |
| Coal hills to the Lull                 | the Cog foot: the Towpath crosses the Cog at the confluence                               | brick towpath and water meadow; the river turns from white water to slow                           | the Narrows Viaduct up the gorge                           | **W3**; the view up the Narrows                                                    |
| Plain to the delta and the city        | Lullford Bridge (a toll house on the island), then the canal embankment through the reeds | water meadows give way to reed beds; market gardens along the canal                                | the city's falls and the Harbour Bridge across the reeds   | **W7**; a barge stop on the canal                                                  |
| Coast to the Headland and the isles    | the Headland stile on the neck; the Shell Bar's tide pools; the ferry from Driftwood      | cliff turf and sea pinks; sand and wrack                                                           | the lighthouse; the wreck on the bar                       | **W1**, **W4**; the wreck (egg spot)                                               |

### 5.3 Each region its own identity (v5.1)

Semi-realistic, not Earth: each region is pushed so that it reads at a glance by colour, landform, vegetation and one silhouette.

| Region                    | Ground colour                                | Landform                                      | Vegetation                 | Silhouette                                   |
| ------------------------- | -------------------------------------------- | --------------------------------------------- | -------------------------- | -------------------------------------------- |
| The home valley           | bright meadow green, strip fields in gold    | a basin with terraces                         | copses, hedges, orchards   | the mill, and the Frostline's headwall above |
| The Brackens              | heather purple-brown                         | a low ridge with bluffs                       | heather, gorse, pines      | the stone ring                               |
| The steppe (Rift country) | straw and pale green                         | flat, cut by the gorge                        | short grass, lone trees    | sheepfolds; the viaduct                      |
| The Sunstone basin        | sand, ochre, red badlands                    | a plateau with mesas and canyons              | scrub; palms at the oases  | mesas and windpumps                          |
| The fire country          | charcoal, grey ash, orange lava              | the cone, lava terraces, the crater rim       | fireweed, dead snags       | the plume; Hearthold's walls                 |
| The coal hills            | dark green and black spoil                   | rounded hills with benches, the Narrows gorge | dark conifers              | chimneys, spoil heaps, the viaduct           |
| The Lull plain and belt   | lush blue-green                              | a flat floodplain with loops                  | water meadows, willow carr | the river's loops; Lullford's arches         |
| The delta                 | olive reeds, grey mud                        | dead flat                                     | reeds                      | the branching channels                       |
| Neon Harbour              | brick-red old town, violet neon, stone quays | terraces round a ria                          | the Heights' gardens       | the falls, the Harbour Bridge, the towers    |
| The massif                | grey scree, white snow, blue ice             | peaks, ridges, cirques, valley glaciers       | alpine meadow              | the headwall; the glaciers                   |
| The isles                 | bright green and pale sand                   | low volcanic isles, a breached crater         | palms                      | the lagoon                                   |

### 5.4 Verticality across the map (v5.1)

Matt, 14:45: "also getting the verticality right in different parts of the map is super important". The soft grid's rules hold everywhere (`verticality.md`, on branch `claude-a/verticality-study`):

- A tier is one 32 px face (40 px in the city).
- Only the south face is a face. West and east ends are 5 px side bands.
- Stairs are cut through faces, at least 34 px open.
- Ramps run along a face at 1 in 3.
- A screen shows at most two full tiers and one low step.

`tier-map-v51.png` steps the height field into those tiers: one colour step per tier, a dark south face, side ends lit on the west and shaded on the east. It also marks every place a route changes tier: stairs (white), ramps (yellow), switchbacks (zigzag), lifts (pink). The in-game mock (`ingame-map-mock-v51.png`) is stepped on the same tiers.

Measured on the block-out (observations; a step is one 32 px tier):

| Region                         | Tiers walked | Faces (typical, tallest stack)                      | Up and down                                                                                             | Where height makes play                                                                         |
| ------------------------------ | ------------ | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| The massif and the Frostline   | 7 to 31      | 32 px; 64 at the headwall                           | the Col Path's switchbacks (11 tier changes); the High Fells' ramps along benches (32)                  | the lip as W2; the Col hut as a lookout; a hidden ledge on the headwall                         |
| The home valley                | 2 to 11      | 32 px; 128 below the Frostline                      | v2's terraces (T0 to T2) with stairs and ramps (3 and 17 on the lanes)                                  | the garden terrace over the village; the mill's weir as a fall between levels                   |
| The coal hills and the Narrows | 3 to 18      | 32 px benches; gorge walls                          | stairs and ramps (11 and 10); a towpath ledge in the gorge (proposal)                                   | the Narrows lift down to the river (a proposal, and a candidate way); the view from the viaduct |
| The Lull plain                 | 2 to 11      | 32 px, far apart                                    | ramps along the river terraces (16), a few stairs (10)                                                  | the flat counterpoint: terrace edges as lookouts over the loops                                 |
| The Lull belt and the delta    | 1 to 5       | 32 px; the Heights rise behind                      | boardwalks over the reeds; the canal embankment                                                         | open views; a reed maze                                                                         |
| Neon Harbour                   | 2 to 11      | 40 px city faces; 320 at the falls                  | stair streets down the Heights, stairs at the falls (14), ramps to the quays (8), the Heights funicular | the funicular as a shortcut; a gallery behind the falls; the quays one tier below the streets   |
| The Sunstone basin             | 5 to 12      | mesas 32 to 96 above; canyon floors 64 to 128 below | the Lode Track's switchbacks (7 changes); stairs into the canyon (11), ramps (9)                        | mesa tops as lookouts by ladder; the canyon descent; the fossil ledge                           |
| The Rift                       | 2 to 10      | gorge walls of 128                                  | ramps down to the ferry (13); the bridge across                                                         | the gorge as the barrier; the viaduct overhead                                                  |
| The fire country               | 5 to 29      | lava terraces of 32; crater walls up to 256         | the forge stair, Hearthold's stepped streets (24 stairs), ramps along the flows (10)                    | the crater rim as a lookout; lava terraces as natural steps; Hearthold's keep above its town    |
| The coast and the isles        | 1 to 6       | cliffs of 96 to 192; beaches at 0                   | slipways and ramps (5); stairs at the quays                                                             | cliff path against beach; tide pools on the Shell Bar                                           |

Every route's tier changes are counted in `stats-v51.json` (`route_tier_changes`): the Canyon Road 33, the High Fells 32, the Drover's Road 22, the Foothill Road 17, the Ash Coast 14, the Lull Road 13. The height field steps the gentle plain into many low tiers. The geography chunk (P1) should merge those into fewer, deliberate banks, so the plain reads flat and the hills read high.

## 6. Paths first: routes, shortcuts and times

### 6.1 The routes, and the ground fitted to each

Walk times are measured end to end on the block-out at 40 px/s.

| Route                                                     | From and to                                                                             | Walk                 | The path and the ground built round it                                                                                | Way                                                            |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Col Path                                                  | the valley up to the Frostline                                                          | 28 s                 | a mountain passage: switchbacks up the cirque's step, the Col hut halfway                                             | **W2** at the lip                                              |
| High Fells                                                | the Frostline along the massif's shoulder to Cogsworth                                  | 51 s                 | a ridge walk past tarns and cairns, down to the Cog                                                                   | **W2** at the rim; **W3** at the Cog                           |
| Foothill Road                                             | the valley east through Fernhollow to Cogsworth                                         | 38 s                 | a woodland road: the trees close in on both sides as it climbs the Fern hills                                         | **W3** at the Millrace bridge                                  |
| Towpath                                                   | Cogsworth down the Cog to Lullford                                                      | 48 s                 | the river path along the Cog, then the Lull's west bank past the water meadows                                        | **W3** where it crosses the Cog                                |
| Lull Road                                                 | the valley across the plain through Lullford to Neon                                    | 87 s                 | the old road: fields, copses, water meadows, the bridge                                                               | **W7** at Lullford Bridge                                      |
| Delta Road                                                | Lullford's east bank along the Lull Cut to the Heights                                  | 59 s                 | the canal towpath beside the delta's marsh                                                                            | (inside W7)                                                    |
| Coast Path                                                | Driftwood along the cliffs and dunes through Gullwick to Lullford                       | 56 s                 | a cliff path, then dunes behind the beach                                                                             | (start)                                                        |
| Headland Lane                                             | Driftwood to the Headland                                                               | 15 s                 | the neck, with a field wall across it                                                                                 | **W1** at the stile                                            |
| Shell Bar                                                 | the Headland's tip to the main isle                                                     | 15 s                 | a sandbar by way of an islet                                                                                          | **W4**                                                         |
| Drover's Road                                             | the valley halt west across the steppe to Palm Spring and Dust Gulch                    | 90 s                 | a drove road: sheepfolds and a well in the steppe, round the Brackens' southern end, over the Rift by Drover's bridge | **W5** at the Rift                                             |
| Lode Track                                                | Dust Gulch up to the Lode                                                               | 18 s                 | a mule track in switchbacks up the spur                                                                               | (inside W5)                                                    |
| Canyon Road                                               | Dust Gulch down the Amber's canyon, past the salt lake and the ash fields, to Hearthold | 75 s                 | a canyon trail on the canyon floor between banded walls and mesas, then across the ash on the volcano's west flank    | **W6** at the chasm bridge                                     |
| Ash Coast                                                 | the valley halt along the coast to Cinderwick                                           | 91 s                 | the coastal shelf under the arc, green on its windward side, through the dead forest                                  | **W5** at the Rift's mouth ferry; **W6** at the crust crossing |
| Ember Way, Forge Stair                                    | Hearthold to the forge, the springs and Cinderwick                                      | 20 s, 4 s            | ash and basalt between the flows                                                                                      | (inside W6)                                                    |
| Old Bridges, Quay Street, Harbour Bridge, Beacon Causeway | inside Neon                                                                             | 9 s, 24 s, 17 s, 9 s | section 8.5                                                                                                           | (inside W7)                                                    |
| Cape Road                                                 | the Skyport to the Launch Cape                                                          | 18 s                 | across the cape's grass to the pad                                                                                    | the pad is **W8**                                              |

**Rhythm.** Town, route, town on every line: the valley, Fernhollow, Cogsworth, Lullford, Neon, the Cape; the valley, Driftwood, Gullwick, Lullford; the halt, Palm Spring, Dust Gulch, the Lode; Dust Gulch, Hearthold, the springs, Cinderwick, the halt.

**Loops:** valley, Col Path, Frostline, High Fells, Cogsworth, Foothill Road, valley; valley, Foothill Road, Cogsworth, Towpath, Lullford, Lull Road, valley; valley, Lull Road, Lullford, Coast Path, Driftwood, valley; the grand loop: halt, Drover's Road, Dust Gulch, Canyon Road, Hearthold, Ember Way, Cinderwick, Ash Coast, halt.

### 6.2 Shortcuts (each opens with the way of the route it runs beside)

| Shortcut                           | Between                                                                    | Way      |
| ---------------------------------- | -------------------------------------------------------------------------- | -------- |
| The valley train                   | the halt and Cogsworth's platform, up the valley floor                     | W3       |
| The desert line                    | the halt and Dust Gulch, over the Rift on its own viaduct                  | W5       |
| The maglev                         | Cogsworth's terminus over the Narrows Viaduct and down the uplands to Neon | W7       |
| The ferry                          | Driftwood's pier and Lagoon Landing                                        | W4       |
| The mine cart (S1)                 | the Lode down past the salt lake to the forge                              | after W6 |
| The coastal steamer (S3, proposal) | Neon's steamer pier and Driftwood                                          | after W7 |
| The rocket and the lander          | the Launch Cape to Halcyon, then Lumen                                     | W8, W9   |

### 6.3 Walk times from the hut (`stats.json`)

| To                                 | On foot (s)             | With shortcuts (s) |
| ---------------------------------- | ----------------------- | ------------------ |
| the stall, the square, the library | 12 to 14 (v2)           | same               |
| Fernhollow                         | 25.2                    | 25.2               |
| Driftwood                          | 40.0                    | 40.0               |
| the Frostline                      | 40.1                    | 40.1               |
| Cogsworth                          | 51.9                    | 27.9               |
| Gullwick                           | 65.9                    | 65.9               |
| Lullford                           | 69.1                    | 69.1               |
| Palm Spring                        | 76.9                    | 43.9               |
| Lagoon Landing                     | 81.1 (by the Shell Bar) | 47.9 (by ferry)    |
| Dust Gulch                         | 98.7                    | 28.6               |
| the Lode                           | 106.0                   | 42.5               |
| Cinderwick                         | 111.5                   | 69.4               |
| Neon Harbour (the market)          | 115.2                   | 56.3               |
| Cinder Springs                     | 126.8                   | 60.8               |
| the Ember forge                    | 129.2                   | 45.2               |
| Hearthold                          | 132.7                   | 52.7               |
| the Launch Cape                    | 147.1                   | 67.6               |

The far places are 2 to 2.5 minutes on foot and under about a minute with the shortcuts, as in v4. The Frostline moved higher into the massif (40 s instead of 27 s), so that it reads as a high cirque.

## 7. Sunstone Reach: a journey into the heat

Sunstone Reach is the whole rain shadow of the arc, entered from the valley's halt across the steppe. Each place is seen before it is reached.

1. **The drove road.** From the halt the Drover's Road runs west round the Brackens' southern end into short grass: sheepfolds, a well, a stone ring on the ridge above (an egg spot). The grass gets thinner and yellower.
2. **The Rift.** The land drops into a gorge with banded walls. Drover's bridge (W5) crosses it; the desert line's viaduct stands upstream.
3. **The scrub.** Beyond the gorge, scrub with single trees, mesas on the skyline to the south-west and the plume of Mount Ember beyond.
4. **Palm Spring, the first oasis.** The Willow Run comes out of its gravel: palms, a pool, orchards fed by channels, a water-seller's awning.
5. **Dust Gulch, the frontier town.** On the Amber's fan below the massif: one street of false fronts, the desert line's platform and water crane, orchards, the mine track zigzagging up behind.
6. **The Lode.** Up the mule track: the mine mouth, ore tubs and the cart line's start.
7. **The canyon.** The Canyon Road follows the Amber down between banded walls and mesas, shaded and cooler, with a fossil in the wall (an egg spot).
8. **The salt lake and the ash.** The canyon opens on the white salt lake, and the ground turns grey: ash dusting the scrub, then ash fields, the fumaroles steaming on the volcano's flank.
9. **The chasm bridge.** On the west flank the young flow blocks the way; the chasm bridge (W6) crosses it, and Hearthold stands on its rock between the flows.
10. **The fire country.** The forge at the caldera's lip, Cinder Springs on the seaward side, Cinderwick in its black-sand cove. The Ash Coast leads home along the green coastal shelf through the dead forest and over the Rift's mouth by ferry, closing the grand loop.

**Sizes.** Dust Gulch is a 544 x 320 desert town, Hearthold 400 x 400 inside its walls, Palm Spring 300 x 220. The Drover's Road is 90 s, the Canyon Road 75 s, with something every 5 s: folds, the well, the gorge, mesas, the oasis, windpumps, the canyon's ledges, the salt crust, the fumaroles. v2's and Claude D's places keep their plans inside this layout.

## 8. The places inside the land (v2's plans, with v5's changes)

### 8.1 What v5 changes from v2 and v4

- **The valley.** The Sleepwater runs through the valley to Driftwood's cove again (v4 sent it to the Lull), so Driftwood's estuary is v2's. The Frostline is higher, carved into a shoulder of the massif. The halt's lines run east to Cogsworth (valley train) and west over the Rift (desert line).
- **Cogsworth.** On the Cog's east bank in the coal hills, with the Millrace through the mills; the maglev's terminus faces the Narrows.
- **Lullford.** At the Lull's lowest crossing, the bridge on its island.
- **Sunstone Reach** (section 7) is entered from the valley over the Rift, not over a pass.
- **Neon Harbour** (8.5) is redesigned as the ria city.
- **The isles.** Eight islands; the main isle's lagoon is breached to the south.

The sections below are v2's plans as decided; their internal walk times come from v2's block-outs, and where they mention v2's or v4's neighbours, 8.1 and sections 6 and 9 take precedence.

### 8.2 The valley (home): garden, woodland, riverside, Crossroads, the park, the halt farm, Driftwood, the Headland and the Frostline

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

### 8.3 Cogsworth

**Size and shape.** 704 x 960 px (two of today's zones were 320 x 1152). In v5 it sits on the Cog's east bank in the coal hills, the Millrace running through the mills. The platform runs along the north edge with both lines entering from the west; the clock-tower square in front of the station; workshop rows west; Gasworks Hill one tier up to the east; the canal half a tier down across the middle; the foundry and allotments south-west; the terminus and the pump house south-east, where the maglev leaves east.

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

### 8.4 The Tidebloom Isles

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

### 8.5 Neon Harbour: the city round the ria

**Is it Neon Harbour or a new city?** It is Neon Harbour. A coast this size has one great port, and Neon is already the city at the river's end with the Skyport, the maglev and W7 (#95, `world-places`). The harbour city of Matt's example and the neon city are the same place in two ages: the old stone town that grew at the falls, and the neon new town that grew round the railway and the Skyport. Keeping one city keeps the places, the gate and the decided canvas size (decision 6).

**Why the bay is deep and sheltered.** It is a ria: the Glint's old valley, cut when the sea stood lower and drowned when it rose, so its sides are steep and deep water runs close to the shore. The Heights headland and Beacon Isle shelter it from the south-west swell. It lies east of the delta, clear of the Lull's silt, as Alexandria was built "removed from the silt thrown out by the Nile" and fed by "a canal from the Nile" ([Wikipedia, History of Alexandria](https://en.wikipedia.org/wiki/History_of_Alexandria)); the Lull Cut is Neon's canal.

**Where the old town grew first.** On the Falls Rock, the rock between the Glint's two waterfalls at the head of the ria. It was defensible (water on three sides), it gave the first crossing (two short bridges over the falls instead of one long one), it was the head of navigation (ships could sail up to the foot of the falls), and the falls drove its mills. That is a fall-line town: rapids "stopped ocean-going ships, so goods had to be unloaded there", and the falling water "powered mills and factories" ([Virginia Places, the Fall Line](https://virginiaplaces.org/regions/fallcolonial.html)).

**The districts** (`harbour-city.png`):

| District        | Where                                                          | Why there                                                                   |
| --------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------- |
| The Falls Rock  | between the two falls at the ria's head                        | the first town: defence, crossing, head of navigation, mills                |
| The market      | at the old bridges' east foot (a 352 x 248 plaza)              | where the roads, the canal's goods and the quay meet                        |
| The docks       | along the ria's east side, piers out into the lee water        | deep water under the steep side, out of the swell                           |
| The warehouses  | behind the docks                                               | goods between ship, rail and market                                         |
| The Heights     | terraces on the west headland, gardens and stairs between rows | views and breeze, upwind of the docks: the rich quarter                     |
| The canal basin | in a cove under the Heights                                    | where the Lull Cut meets the ria                                            |
| Chapel Islet    | in the ria's middle, under the Harbour Bridge                  | the bridge's pier, the sailors' chapel                                      |
| The Gull Strand | the beach at the ria's mouth on the east side                  | nearest the fishing grounds; boats hauled up on the sand                    |
| Beacon Isle     | in the ria's mouth, reached by a causeway from the Strand      | the old lighthouse: the landmark on an island                               |
| The new town    | the flat uplands east of the market, in blocks of 208 x 272    | flat land for a planned grid, round the maglev terminus; neon signs, towers |
| The Skyport     | a flat field south of the new town, mooring masts              | open to the sea wind, beside the cape                                       |

**How you arrive.** On foot by the Lull Road over Lullford Bridge and along the Delta Road (the canal's towpath) to the Heights, then over the Harbour Bridge or round by the old bridges at the falls. By the maglev into the new town's terminus. By the coastal steamer at the steamer pier on the docks. The Cape Road leaves past the Skyport.

**v5.1: drawn, not boxed.** The city's footprint follows the ria and the coast, and the districts share it out by nearest centre in a warped space, so their borders are crooked streets, not circles (`harbour-city-v51.png`).

- **The old town and the market quarter:** irregular blocks, buildings along lanes, two or three cells deep, broken into houses, with yards behind; the market square is one of the blocks left open.
- **The Heights:** streets along the contours over three knolls, houses on their downhill side, stair streets straight down the fall line.
- **The new town:** a looser grid turned 14 degrees, towers round each block.
- **The shore:** long piers along the docks, short jetties under the Heights, slipways at the Strand.

**Size and pace.** About 1450 x 1100 px with the ria, of which the ria is about a third. Inside: the old bridges 9 s, Quay Street from the market to the Strand 24 s, the Harbour Bridge 17 s, the Beacon Causeway 9 s, the Cape Road 18 s. Any district is within about 25 s of the market. The walkable ground stays near v2's 960 x 1280 canvas (decision 6): the ria and the terraces' gardens are frame between the streets.

**Kept from v2.** The Skyport, the docks' cranes and ship, the old wet street (now in the Falls Rock), the elevated tram (on Quay Street), Claude C's facade detail (PR #116). **Changed:** the city wraps a ria instead of standing on a straight shore; one spine becomes the quay and the bridges.

### 8.6 Halcyon Station

320 x 576 px, unchanged: rooms in the order of the climb, from the elevator's airlock at the bottom through hydroponics, the galley, the atrium and the sleep bay, to the shuttle hatch (W9) and the lounge under the windows. From the airlock: hydroponics 3.4 s, the atrium 6.3, the hatch 10.7, the lounge window 12.2. A station is a building; one screen of rooms is enough.

### 8.7 Lumen

384 x 704 px (today 320 x 576): the pad on the crater's rim (T2), the habitat with its solar arrays and the ice rig in the shadowed crater (T1), the pressure tube down to the dome on the crater floor (T0), the moon tree and the hammock. From the pad: the habitat 8.5 s, the moon tree 13.9, the hammock 16.4. A little wider so the crater reads as a crater on a 300 px screen.

## 9. Space: the rocket (decided)

**The launch site.** The Launch Cape: an exposed headland south-east of the city, 18 s from the Skyport by the Cape Road. A real spaceport launches over the sea, away from towns, and this one does. Its parts:

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

## 10. The ways on the land

The nine ways (#95, decided) keep their names, order and tasks. Each stands where a route crosses one of the land's barriers. A place with more than one way in has one way mending all of them.

| #   | Way                                     | Barrier and crossing                                                                        | What is being mended                                             | In reach after (#95)                                      |
| --- | --------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------- |
| W1  | The Headland stile                      | the field wall across the Headland's neck                                                   | the stile's broken step                                          | the start                                                 |
| W2  | The ridge col                           | the Frostline's rim; the Col Path at the lip and the High Fells at the east col             | two pines from one storm                                         | the start                                                 |
| W3  | The Millrace landslip                   | the Cog; the Foothill Road (the Millrace bridge), the High Fells and the Towpath            | a landslip at the Millrace; a rockfall; a breach, from one storm | the start                                                 |
| W4  | The Shell Bar and the ferry             | the sea; the Shell Bar                                                                      | a washed-out stretch; the ferry on the slip                      | the start                                                 |
| W5  | The Rift                                | the Rift gorge; Drover's bridge, the ferry at its mouth, the desert line's viaduct          | a flood took the bridge's deck and the ferry's rope              | W3 (by #95's day order; the land itself does not need it) |
| W6  | The chasm bridge and the crust crossing | the two young lava flows; the Canyon Road's chasm bridge and the Ash Coast's crust crossing | the bridge's missing span; a crust causeway over the flow        | W5 (the masons come from Dust Gulch)                      |
| W7  | Lullford's swing bridge and the maglev  | the Lull; Lullford Bridge's swing span (the only footway over the Lull and its delta)       | stuck open, waiting for a gear from Cogsworth's foundry          | W3                                                        |
| W8  | The rocket                              | (a journey) the Launch Cape's pad                                                           | the launch not yet fuelled                                       | W7                                                        |
| W9  | Halcyon's lander                        | (a journey) Halcyon's hatch                                                                 | under a cover                                                    | W8                                                        |

**The gate check** (`gates.json`). The script finds every place a route crosses a barrier (the rim, the Cog, the Rift, the lava flows, the Lull and its delta arms, the Headland's wall, the sea) and puts the way there. It reports any crossing with no way: there is none. Three crossings inside the city (the Harbour Bridge twice, the Beacon Causeway) are marked open because they lie behind W7. With the ways opened one at a time in road order, a flood fill from the hut reached nothing behind a closed way and everything behind an open one, at every step; Driftwood, Fernhollow, Lullford, Gullwick and the halt are reached from the start. The Narrows Viaduct is drawn as rail only, not a footway, so it is no way over the Lull.

## 11. The engine: one world canvas (decided)

v3's design stands (decided by Matt). One world canvas is authored in chunks (each settlement, each route, and the land itself, which is now generated from the geography fields and then drawn over by hand) and cut into world tiles of 256 px. The numbers grow with the land:

- **Canvas:** 11264 x 6912 px, 1408 x 864 cells. 80 % of it is land (v4: 63 %; the sea now lies only to the south).
- **Tiles:** 1188 render tiles. 248 are uniform (open sea, glacier, dune sea) and share a few pictures; 510 hold walkable ground.
- **Memory:** unchanged: 9 to 12 tiles in view.
- **Walk grid:** 4.9 million cells of 4 px. It is exported per tile and searched in a window round the companion, with a coarse route graph for far walks (v3).
- **The geography as data.** The build keeps the height, wetness and warmth fields (at 8 px) as its own data. Each chunk's ground reads them, so a chunk's grass, its transition bands and its props agree with its neighbour's without seams. The terrace toolkit turns height into tiers on the soft grid; v2's sizing still decides every built thing.

The region-canvas builder (`claude-a/region-canvas`) keeps v3's seven changes (11.1), plus an eighth: **a geography chunk that writes the fields** before any settlement or route chunk is drawn.

### 11.1 What the region-canvas builder should change (from v3)

1. **Give every canvas a world origin.** A region or route chunk is placed at a world (x, y) on the 8 px grid (section 3.1), not at (0, 0) of its own canvas.
2. **Key tiles by world tile coordinates** (tx, ty) on one world grid of 256 px, so a region's edge can fall inside a tile and two chunks can share one. Composite the chunks onto the tiles.
3. **Export walk, terrain, tiers and stands per tile**, not per region; keep areas (names, map, saves) as a separate small table of rectangles or masks in world coordinates.
4. **Deduplicate uniform tiles** (sea, peaks, forest) to one picture each.
5. **Cache per chunk**: rebuild only the tiles a changed chunk touches.
6. **Keep the compatibility cut** into today's 320 x 576 zones for now, so the app runs unchanged until the renderer streams tiles.
7. **Leave room for routes and transitions**: a chunk declares its bounding box and a margin band where it blends into its neighbour. The background (biomes between chunks) is a chunk of its own.

## 12. The in-game world map

Matt sent two styles: a soft-grid map of stepped, outlined plateaus with paths, stairs, tunnels and buildings as icons (example 2), and Stardew's illustrated map, where forest, river, mountains, farmland and coast blend (example 4).

**Recommendation: the soft-grid style (example 2), with Stardew's warmth in its colours.**

- It matches the soft grid the world is drawn on, so the map reads as the same land seen from above.
- It is drawn by the build from the same data (tiers from height, colours from ground), not painted by hand, so it never falls out of date.
- It reads at phone size, and it can reveal only what has been walked, as the map does today (C22).

The mock (`ingame-map-mock.png`) is drawn from the v5 block-out. Tiers step at 32 px, each with a darker face on its south edge and a thin outline. Water is deep blue, paths pale, settlements are house icons with their names, the ways are red dots, and the land beyond the walked corridors is hazier. A finished version would add the pixel frame and font from `interface.md`, the companion's marker, fog over places not yet walked, the journeys as dashed lines, and small pictures of each place's landmark, after Stardew's map.

## 13. Critique: what still looks artificial

Compared with Matt's four examples (the Final Falls city, the soft-grid tier map, the joined Pokémon regions, Stardew's map) and with v4.

**Fixed in v5.**

- _It read as an island._ Now only the south is coast; the other edges are land with borders, drawn going on.
- _Mountains ran between desert and grass._ The massif now closes the north of both, and the change from meadow to dune sea is a gradient about 6 km wide that crosses the Rift.
- _Placeholder shapes._ Towns grow along their roads (houses in rows along the streets, fields in a patchwork round them) instead of filling ovals; the Frostline is a cirque in a high shoulder; the volcano has no ring, only two young flows, old flows, ash blown downwind and parasitic cones; the isles are noise-shaped, the main one a breached crater; the city follows its ria.
- _Lines._ The basin's straight edge, a gorge-width step that drew straight lines across the coal hills, and creeks drawn as a grid of straight diagonals are gone: creeks are traced down the drainage and smoothed, and every threshold is softened by noise.
- _Labels overlapped._ A placer now tries several positions per label and drops none on top of another.

**Fixed in v5.1** (Claude A's critique and section 13's own list): the river's jump in width; the uniform snake and the detached oxbows; the straight delta arms; the boxed city; the west's north-south stripes and the ruler-straight Rift; badlands in bands; the Frostline as a cut-out blob; Hearthold as a box; rectangular fields; the flat massif; the dune sea's one texture; the Heights' rings; the mirrored lava flows; the in-game mock's tiers from height alone (now the same tiers as the tier map).

**Still artificial after v5.1, to fix in the geography chunk (P1).**

1. The plain is stepped into many low tiers by the height field; it should be merged into a few deliberate banks.
2. The Lull's belt has one big loop and a few small ones; a longer belt would repeat loops of similar size.
3. The new town still reads as a grid at 1x (it is planned, but its edge needs to meet the old streets more gradually), and the Skyport is a plain grey field.
4. Mount Ember's crater is round (calderas are), and its two flows still meet at the summit in a wedge.
5. Where the map is crowded, the label placer drops some threshold names rather than overlap them.
6. Pokémon's routes are orthogonal; ours curve with the ground. That is a choice.

**v5's list** (kept for the record; v5.1 fixed items 1 to 7 and 9 below).

1. The Rift runs almost straight north to south for its whole length and still reads, at 1x, as a dividing line. It should bend west round a spur of the basin's plateau, with a side canyon.
2. The fields are axis-aligned rectangles. Stardew's are too, but real fields follow the river and the slope; they should turn with the ground.
3. The dune sea is one texture. It needs star dunes, a few interdune flats and a dry river bed fading into it.
4. The city's terraces read as concentric rings on the Heights' round hill at 1x; the hill needs two or three knolls so the terraces break into separate streets, as on Final Falls' headlands.
5. The delta's arms are too even in width and spacing; a real delta has one dominant arm and several small ones that change.
6. The massif's top is a continuous snow band; it needs separate peaks with valley glaciers running down between them.
7. The in-game mock steps tiers from height alone, so the plains show few tiers and the city none. Matt's example 2 sets plateaus deliberately; the build should take the soft grid's authored tiers where a chunk has them.
8. Pokémon's joined map (example 3) uses orthogonal routes; ours curve with the ground, closer to Stardew's and Final Falls'. That is a choice, not a fault, but it means the in-game map should straighten routes a little when it simplifies them.
9. The two young lava flows are nearly symmetric about the crater; one should be older and narrower, or turn.

## 14. Easter eggs (reserved, later)

Spots are reserved and drawn as small rings on `continent-labelled.png`. They hold nothing yet and give no reward (rule 10): the stone ring on the Brackens, a wreck on the Shell Bar, a bell in the oxbow lake, a fossil in the Amber canyon, a hermit's tarn on the High Fells, a lone palm at the dune sea's edge, a steam cave on Mount Ember, the lighthouse keeper's door on Beacon Isle.

## 15. Order of work and owners

| Step | Lane | Work                                                                                                                                                                                                                                                                                                                                       | Needs                   |
| ---- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- |
| P0   | A    | The toolkit lands (`terrace.py`, `scale.py`, tiers, the facade composer, `fore.png`)                                                                                                                                                                                                                                                       |                         |
| P1   | A    | **The geography chunk**: the height, wetness and warmth fields; the massif, the arc and Mount Ember, the basin, the Rift, the Lull with its braids, oxbows and delta, the coast, the ria, the isles; biome bands with noise; the thresholds (5.2); tiers per region with the plain's merged into banks (5.4); section 13's remaining fixes | Matt's yes to 16 and 21 |
| P2   | A    | The world canvas build (11.1 plus P1) and the renderer streaming world tiles; saves in world coordinates (with Codex)                                                                                                                                                                                                                      | P1                      |
| P3   | A    | The in-game map from the build's data in the soft-grid style                                                                                                                                                                                                                                                                               | P1                      |
| P4   | B    | Props to the scale table and #97, including the paths' props: the Col hut, cairns, sheepfolds and the well, the Millrace wheel, the swing span, the viaduct's piers, the Harbour Bridge's arches, windpumps, the chasm bridge, the rocket                                                                                                  | P0                      |
| P5   | E    | The home valley in the land (v2's plan with 8.1's changes), Driftwood's cove, the Headland's wall, the Frostline's cirque with A                                                                                                                                                                                                           | P2, P4                  |
| P6   | A    | The routes' chunks, path first: Col Path, High Fells, Foothill Road, Towpath, Lull Road, Coast Path, Headland Lane, Delta Road                                                                                                                                                                                                             | P2                      |
| P7   | D    | Sunstone Reach as a journey (section 7): the Drover's Road and the Rift, Palm Spring, Dust Gulch, the Lode, the Amber canyon, the salt lake, Hearthold, the fire country, the Ash Coast and Cinderwick; then the Launch Cape, Halcyon and Lumen                                                                                            | P2                      |
| P8   | C    | Cogsworth on the Cog with the Millrace, Lullford and its bridge, Fernhollow, Gullwick; Neon Harbour round its ria (8.5); the isles and the Shell Bar                                                                                                                                                                                       | P2                      |
| P9   | A    | The ways on the land (#118 to world coordinates), the journeys as shortcuts, the gate check as a test                                                                                                                                                                                                                                      | P2, #95's rules (Codex) |

## 16. Decisions for Matt

| #   | Decision                                                                                                                    | Recommendation or decision                                                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| 1   | Keep the zoom at 12 adults across                                                                                           | **Decided 20 Oct: keep.**                                                                                          |
| 2   | Canvases streamed in tiles instead of the zone grid                                                                         | **Decided 20 Oct: yes.**                                                                                           |
| 3   | Sizes from the sizing table; everyday places within 15 s of the hut                                                         | **Decided 20 Oct: yes.**                                                                                           |
| 4   | The valley at 1280 x 2688 with a real village, a farmstead and Driftwood                                                    | **Decided 20 Oct: yes.**                                                                                           |
| 5   | Cogsworth with Gasworks Hill and the Terminus                                                                               | **Decided 20 Oct: yes.**                                                                                           |
| 6   | Neon's canvas a quarter smaller with more street                                                                            | **Decided 20 Oct: yes** (kept in 8.5: the ria is frame, the streets keep the size).                                |
| 7   | Sunstone Reach as one continuous land                                                                                       | **Decided 20 Oct: yes.**                                                                                           |
| 8   | A rocket from the Launch Cape replaces the space elevator; Halcyon's lander to Lumen                                        | **Decided 20 Oct (v3): yes.**                                                                                      |
| 9   | One world canvas, authored in chunks and streamed in tiles                                                                  | **Decided 20 Oct (v3): yes.**                                                                                      |
| 10  | The map as a window onto a larger continent: sea and isles only in the south, natural borders on the other three edges      | **Yes.** It is what Matt asked for at 12:25.                                                                       |
| 11  | Arrangement A (section 4.4): the arc, its rain shadow, the river in the east                                                | **Decided 20 Oct (about 14:45): "go with A more or less".**                                                        |
| 12  | About 125 zone-areas walked, with land beyond the corridors drawn but not walked                                            | **Yes.** v4's scale kept.                                                                                          |
| 13  | The routes as paths first, with the ground fitted to each (section 6.1)                                                     | **Yes.**                                                                                                           |
| 14  | Sunstone Reach entered from the valley over the Rift (section 7)                                                            | **Yes.** It replaces v4's pass over the spine.                                                                     |
| 15  | The Sleepwater to Driftwood's cove (reverses v4's decision 14)                                                              | **Yes.** It restores v2's estuary and keeps the valley's river short and its own.                                  |
| 16  | The Lull as the one great river, with Lullford Bridge, the Narrows Viaduct and the Harbour Bridge as its landmark bridges   | **Yes.**                                                                                                           |
| 17  | Mount Ember on the arc, at the far south-west, with a buffer of ash, old flows, springs and a dead forest instead of a ring | **Yes.**                                                                                                           |
| 18  | The ways at the barriers (section 10): W5 at the Rift, W6 at the young flows, W7 at Lullford's swing span                   | **Yes.**                                                                                                           |
| 19  | The in-game map in the soft-grid style (example 2)                                                                          | **Yes** (Claude A's recommendation too).                                                                           |
| 20  | The geography as data (height, wetness, warmth fields) that every chunk reads                                               | **Yes.**                                                                                                           |
| 21  | Neon Harbour as the ria city of Matt's first example (8.5), not a separate city                                             | **Yes.** One port, two ages; the places and W7 stay.                                                               |
| 22  | Easter-egg spots reserved now, designed later (section 14)                                                                  | **Yes, later.**                                                                                                    |
| 23  | The coastal steamer (S3)                                                                                                    | **Yes, later.**                                                                                                    |
| 24  | Ground pictures at 1x (or 2x)                                                                                               | **Test, then 1x if crisp.**                                                                                        |
| 25  | Secret pockets hold no keepsakes; no one-way ledges for now; the companion stays 24 px                                      | **Yes** (from v2).                                                                                                 |
| 26  | Every region change on a route is a designed threshold with a mixing band, a landmark and a beat (5.2)                      | **Yes** (v5.1).                                                                                                    |
| 27  | Each region pushed to its own colour, landform, vegetation and silhouette (5.3)                                             | **Yes** (v5.1).                                                                                                    |
| 28  | Verticality per region on the soft grid's tiers (5.4); the plain's many low tiers merged into a few deliberate banks        | **Yes** (v5.1).                                                                                                    |
| 29  | Lifts: the Heights funicular as a shortcut inside Neon; the Narrows lift down to the river                                  | **Funicular yes; the Narrows lift a proposal** (it would be a new shortcut, so it waits for Matt and #95's rules). |

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
- Bulbapedia, Pokémon world in relation to the real world: https://bulbapedia.bulbagarden.net/wiki/Pokemon_world_in_relation_to_the_real_world
- Bulbapedia, Hoenn Route 113: https://Bulbapedia.Bulbagarden.net/wiki/Hoenn_Route_113
- Bulbapedia, Galar: https://bulbapedia.bulbagarden.net/wiki/Galar
- Bulbapedia, Paldea: https://bulbapedia.bulbagarden.net/wiki/Paldea
- Game Developer, Road to the IGF: Pixpil's Eastward: https://www.gamedeveloper.com/disciplines/road-to-the-igf-pixpil-s-i-eastward-i-
- LibreTexts, Geology of California, 7: Cascade Range and Modoc Plateau (v5): https://geo.libretexts.org/Bookshelves/Geology/Geology_of_California/07%3A_Cascade_Range_and_Modoc_Plateau
- Virginia Places, How the Fall Line Shaped Colonial Settlement in Virginia (v5): https://virginiaplaces.org/regions/fallcolonial.html
- Wikipedia, History of Alexandria (v5): https://en.wikipedia.org/wiki/History_of_Alexandria
- Wikipedia, Tarim Basin (v5; named as the analogue, not quoted): https://en.wikipedia.org/wiki/Tarim_Basin

**Gaps.** No developer source gives Stardew's, Eastward's or CrossCode's map sizes or walking speeds; the reference sizes here are measured on store screenshots by character height and are good to about a quarter of an adult. No castle or desert town appears in our reference shots, so those two sizes are built from parts. The walk-seconds are measured on block-outs, not on drawn art; the redraws will move them by a few seconds. The garden's walkable share in today's totals is an estimate.

**Gaps (v4).** No developer interview found here explains how Game Freak lays out a region beyond the real place it is based on; the region facts are Bulbapedia's. No Pixpil interview found here describes how Eastward's maps join. The height, wetness and rain-shadow model is ours (standard physical geography), not a game's.

**Gaps (v5).** The Tarim Basin page and NASA's Oregon rain-shadow page could not be fetched from here, so the Tarim analogue is named without a quotation. The geology is a design analogue, not a simulation: the height, wetness and drainage fields are ours, the widths and distances in sections 4 to 7 are observations on the block-out, and the city's internal times are measured on its block-out streets, not on drawn art.
