# The world plan (v4): one land, designed from its geography

Matt, 20 Oct:

- 01:05: "All of these need redesigns pretty much, to fit the newly established soft grids. also consult the other games mentioned for world buildings how large parts of the maps should be and how they are attached together and how you can create interesting spaces."
- 10:32: "really think deeply of the sizing of everything and the map".
- 10:58: "work the whole world map out first and how everything connects (with as many physical connections as possible as well, with trains as short cuts) ... the world should feel expansive with natural looking boundaries and no abrupt cuts".
- About 11:45, on v3: "make the world roughly twice that size and everything fits together nicely and is not just stitched together. with natural transitions and not just a line. look into pokemon world design or eastward". On Sunstone Reach: "make it immersive".

**Status: a plan, partly decided.** These stand from earlier versions:

- v2's sizing table and decisions 1 to 7 (section 14).
- v3's decided items: the rocket from a launch cape, Halcyon's lander, one world canvas.

v4 replaces v3's continent with one land designed from physical logic first: a mountain spine, its rain shadow, one river system, a volcano, coasts and harbours where shelter is. The places people live sit where that land would put them. It is about twice v3's walkable ground, joined by routes along valleys, passes and coasts, with towns and hamlets along them in Pokémon's rhythm of town, route, town. Sunstone Reach is designed as a journey. The in-game map is proposed in the soft-grid style Matt sent.

It builds on, and does not repeat:

- `verticality.md` (the soft grid and the scale table).
- `art-style.md` (Eastward's detail; each setting its own style).
- `prop-logic.md` (#97).
- `world-unlocks.md` (#95, decided: nine ways, one a day) and the ways catalogue (#118).
- `world-rules.md`, `world-ports.md`, `world-atlas.md`.
- `../research/2d-world-design.md` and `research/*.md`.

**The images** are not in the repository. Claude A has them in its scratchpad (`worldplan4/`), drawn by a script (`geo.py`) from a height field, a wetness field and the designed features, at 1 px per 8 px cell:

| File                                                                                                                                                                                                             | What it shows                                                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `physical-map.png`                                                                                                                                                                                               | height and rivers only: the geography on its own                                                                                        |
| `continent-1x.png`                                                                                                                                                                                               | the land with every kind of ground, hill-shaded from the upper left (1408 x 864)                                                        |
| `continent-labelled.png`                                                                                                                                                                                         | the same at 2x with settlements, routes, rivers, shortcuts (dashed) and the ways (red); ground beyond the walked corridors drawn darker |
| `overview-32px.png`                                                                                                                                                                                              | 1 px per 32 px (352 x 216)                                                                                                              |
| `ingame-map-mock.png`                                                                                                                                                                                            | the in-game map in the soft-grid style (section 12)                                                                                     |
| `region-valley-and-frostline.png`, `region-cogsworth-and-lullford.png`, `region-sunstone-reach.png`, `region-fire-country.png`, `region-neon-and-cape.png`, `region-isles.png`                                   | crops per region                                                                                                                        |
| `route-foothill-road-high-fells.png`, `route-sunstone-gap.png`, `route-canyon-road-ember-way.png`, `route-ash-coast.png`, `route-lull-road-coast-path-towpath.png`, `route-shell-bar.png`, `route-cape-road.png` | crops per route                                                                                                                         |
| `stats.json`                                                                                                                                                                                                     | sizes and walk times                                                                                                                    |
| `gates.json`                                                                                                                                                                                                     | the gate check (section 10)                                                                                                             |

Matt's example maps (a fantasy city, a soft-grid tier map, all the Pokémon regions joined, Stardew's map) are in `refs-matt/maps/`, for reference only.

## 0. In short

1. **One geography.**
   - _The Greyspine_: a mountain spine running from the north-east coast to _Mount Ember_, a volcano on the south-west coast.
   - The wind comes off the southern sea, so the south-east side is wet (forest, meadow, farmland) and the north-west side lies in the rain shadow (_Sunstone Reach_: scrub, then desert, then a salt pan, then badlands at the far coast).
   - _One river system, the Lull_, drains the wet side from the snowfields to the sea at Neon Harbour. Its tributaries are the Sleepwater (out of the Frostline, through the home valley) and the Cog (past Cogsworth).
   - The _Tidebloom Isles_ are the volcanic chain that runs out to sea from Mount Ember.
2. **Places where people would settle.**
   - The home valley where the Sleepwater leaves the mountains.
   - Driftwood in the sheltered bay below it.
   - Cogsworth in the coal hills on the Cog.
   - Lullford at the Lull's crossing on the plains.
   - Neon Harbour at the Lull's mouth, with the Launch Cape on the eastern headland.
   - Dust Gulch at the foot of the mine in the rain shadow; Hearthold on a rock above the lava at the volcano's flank.
   - Hamlets along the routes: Fernhollow, Gullwick, Cinderwick, Palm Spring, the Gap Hut, the Lode.
3. **About twice v3's walkable ground: 120 zone-areas** (v3: 52), on a world canvas of 11264 x 6912 px.
   - Thirteen routes follow valleys, passes and coasts, from 8 to 93 s each.
   - From the hut: the everyday places within 15 s, Cogsworth 58 s on foot (23 s by train), Neon 102 s (50 s), Dust Gulch 121 s (28 s), Hearthold 164 s (58 s).
4. **No lines.** Every change of ground is a wide, irregular band from noise in the height and wetness, with scattered outliers. Coasts, the rim of the Frostline, the volcano's lava ring and the salt pan are rough shapes, not ellipses. Ground beyond the walked corridors is still drawn (hedged fields, old woods, high snow, deep dunes), so the land runs on to its natural edges.
5. **The nine ways sit where routes cross the land's barriers**: the crest, the Cog, the Lull, the fire ring, the Frostline's rim and the sea. A flood fill on the block-out passes at every step of the road.

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

### 4.1 The land, physically

| Feature                          | What it is                                                                                                                                                                                                                                                                | Why it is there                                           | What follows                                                                                                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **The Greyspine**                | a mountain spine about 9000 px long, from the north-east coast to Mount Ember on the south-west coast; an unbroken crest of peaks with one pass (the Sunstone Gap)                                                                                                        | a fold range along the edge of a plate                    | it divides the land into a wet south-east and a dry north-west; snowfields along its length feed every river                                                                        |
| **Mount Ember**                  | a volcano at the spine's south-west end, on the coast, with a crater, a basalt core, lava running north round Hearthold's rock and south-east to the sea, and a ring of old lava fields round its flanks                                                                  | the end of the arc where the plate dives                  | ash darkens the land downwind; nothing green grows within its ring; the isles continue its arc out to sea                                                                           |
| **The wind and the rain shadow** | the prevailing wind comes off the southern sea                                                                                                                                                                                                                            | wet air rises on the south-east slopes and drops its rain | forests on the wet side; on the lee side, heath close to the range, then scrub, then dune desert, then a salt pan where the desert's washes end, then red badlands at the far coast |
| **The Lull**                     | one river system: the Lull rises in the snowfields north of Cogsworth and runs south across the plains to its estuary at Neon. The Cog joins it below Cogsworth; the Sleepwater rises in the Frostline's cirque, runs through the home valley and joins it below Lullford | rivers run downhill from snow to sea                      | Neon at the mouth; Lullford at the crossing; Cogsworth on the Cog; marshes at the estuary; the river valleys are the natural roads                                                  |
| **The Brook**                    | a short coastal stream from the valley's southern hills to Driftwood's bay                                                                                                                                                                                                |                                                           | Driftwood's small estuary (v2's harbour keeps its look)                                                                                                                             |
| **The Dry Wash**                 | a seasonal river on the lee side, from the range to the salt pan                                                                                                                                                                                                          | rain in the mountains, none below                         | the canyon the Canyon Road follows, dry most of the year (and in flood after a storm)                                                                                               |
| **The Frostline**                | a cirque in the spine's south-east flank above the valley, with Snowmelt Lake, a cliff rim and two ways out                                                                                                                                                               | a glacier carved it                                       | the Sleepwater's source; v2's Frostline places inside it                                                                                                                            |
| **The coast**                    | grid-led at the large scale, rough at the edge; sheltered bays at Driftwood (behind the Headland) and at the Lull's mouth; black sand within the volcano's reach, pale sand elsewhere                                                                                     |                                                           | harbours where there is shelter; cliffs and beaches elsewhere                                                                                                                       |
| **The Headland**                 | a promontory off Driftwood's bay, joined by a narrow neck                                                                                                                                                                                                                 |                                                           | the stile (W1) on the neck; the Shell Bar runs from its tip                                                                                                                         |
| **The Tidebloom Isles**          | a chain of five volcanic islands from the volcano eastward; the main island south of the Headland                                                                                                                                                                         | the volcanic arc continued under the sea                  | the isles' crater pool and black-sand cove (v2) make sense                                                                                                                          |
| **The plains**                   | the low, wet land between the valley, Cogsworth and Neon; farmland round the settlements, copses, hedged fields beyond                                                                                                                                                    | the Lull's flood plain                                    | Pokémon's wild middle (Galar's Wild Area); the routes cross it                                                                                                                      |

### 4.2 Regions are where people settled

| Place                                               | Kind                                   | Why here                                                                                                 | Size (sizing table)                           |
| --------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| The home valley (garden, Crossroads, the halt farm) | market village                         | where the Sleepwater leaves the mountains: water, a mill head, shelter, the first flat ground            | v2's 1280 x 2688 canvas, now part of the land |
| Driftwood                                           | fishing harbour                        | the sheltered bay below the valley                                                                       | 544 x 352 harbour, 480 x 160 hamlet           |
| Fernhollow                                          | timber hamlet                          | in the wet forest on the Foothill Road                                                                   | 320 x 240                                     |
| Cogsworth                                           | railway and foundry town               | coal in the hills, iron from the range, the Cog for power and the canal                                  | 704 x 960 (decided)                           |
| Lullford                                            | market town                            | the crossing of the Lull's plains: the Lull Road and the towpath meet                                    | 560 x 420                                     |
| Gullwick                                            | fishing village                        | a cove on the Coast Path                                                                                 | 420 x 220                                     |
| Neon Harbour                                        | the city                               | the Lull's mouth: a port for the whole river system                                                      | 960 x 1280 (decided)                          |
| The Launch Cape                                     | spaceport                              | an eastern headland, launches over the open sea                                                          | 480 x 360                                     |
| The Gap Hut                                         | a refuge                               | at the top of the only pass                                                                              | 120 x 100                                     |
| Palm Spring                                         | the first oasis                        | a spring at the foot of the lee slope, where snowmelt surfaces                                           | 300 x 220                                     |
| Dust Gulch                                          | frontier town                          | the railhead below the mine, the oasis's water piped in                                                  | 544 x 320 desert town                         |
| The Lode                                            | mine                                   | iron and gold in the lee foothills                                                                       | 260 x 180                                     |
| Hearthold                                           | castle                                 | a rock above the lava at the volcano's north flank: the only safe ground between the desert and the fire | 400 x 400 inside its moat                     |
| The Ember Caldera forge, Cinder Springs             | forge, bathhouse                       | the volcano's heat and its hot springs                                                                   | as v2                                         |
| Cinderwick                                          | charcoal and black-sand fishing hamlet | the Ash Coast                                                                                            | 340 x 200                                     |
| Lagoon Landing                                      | island hamlet                          | the main isle's lagoon                                                                                   | as v2                                         |

## 5. Transitions: bands, not lines

Every biome comes from fields: height, wetness and warmth, each with large and small noise. A change of ground is therefore a wide, irregular band where the two grounds interleave. A fine jitter puts outliers on either side: a pine in a meadow, a cactus in the scrub, a snow patch in a hollow below the snowline. Props follow the same fields, so ground cover and props change together (`prop-logic.md`).

| Band                      | From and to                                                                                                         | Width                                     | Mixed ground and outliers                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Up the wet side           | meadow and fields, then broadleaf copses, then mixed wood, then conifers, then alpine meadow, then snow, then peaks | about 900 px from the valley to the crest | copses out in the fields; pines standing alone in alpine meadow; snow patches in shaded hollows |
| Over the crest to the lee | snow, then bare alpine, then dry heath, then scrub                                                                  | about 500 px                              | dwarf pines in the heath; the first cacti among the scrub                                       |
| Across the desert         | heath, then scrub, then dune, then salt pan or badlands                                                             | 600 to 1500 px                            | scrub islands among dunes; salt crust patches; red outcrops (mesas) rising out of both          |
| Into the fire country     | scrub or meadow, then grey ash, then basalt, then the crater                                                        | about 1300 px                             | fireweed and charred snags at the outer edge; nothing green inside the ring                     |
| The plains                | farmland, then hedged pasture, then copse, then marsh at the estuary                                                | wide, patchy                              | fields as an irregular patchwork round each settlement, thinning into pasture                   |
| Country to city           | fields, then market gardens, then allotments, then yards, then the city's quays                                     | about 800 px along the Lull Road          | glasshouses and sheds out among the fields                                                      |
| Coast                     | grass, then dune or cliff, then sand or black sand, then shallows                                                   | 40 to 80 px                               | rocks and driftwood on the beach                                                                |

**Natural edges of the world:** the sea on every side, rough coasts with bays and headlands, the badlands on the far west coast, the Greyspine's peaks inside. Nowhere ends in a straight cut.

**The walked corridors and the land beyond.** The routes and settlements are walked. Land farther than about 500 to 700 px from them is still drawn but not walked: hedged fields, old woods, deep dunes, high snow, badlands. Each kind of land has its own edge that stops the walk naturally (a hedge, a wood's edge, a dune crest, a snowfield's lip). This keeps the walked world at about twice v3's, the art budget sane, and the views wide.

**Views across the land** (scenery, never tap targets):

- From the Frostline and the Gap: Mount Ember's plume and the whole plains.
- From the valley: the Greyspine's snow and the Frostline's rim.
- From the Lull Road: Neon's towers across the river.
- From Driftwood: the isles and the rocket on its cape.
- From Dust Gulch: the range's wall and the volcano's plume.
- From the Canyon Road: Hearthold on its rock above the lava.

## 6. Settlements, routes and shortcuts

### 6.1 The routes

Walk times are measured end to end on the block-out at 40 px/s.

| Route         | From and to                                                               | Walk | Through                                                               | Rests and landmarks                                                         | Way                                                        |
| ------------- | ------------------------------------------------------------------------- | ---- | --------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Col Path      | the valley up to the Frostline                                            | 14 s | forest, then alpine                                                   | the col with its fallen pine                                                | **W2** at the rim                                          |
| High Fells    | the Frostline along the flank to Cogsworth's hill                         | 41 s | alpine and snow                                                       | a cairn line; views down to the plains                                      | **W2** at the rim; **W3** at the Cog's head                |
| Foothill Road | the valley east through Fernhollow to Cogsworth                           | 35 s | wet forest, then coal hills                                           | Fernhollow's sawmill; the Millrace gorge                                    | **W3** where it crosses the Cog                            |
| Towpath       | Cogsworth down the Cog and the Lull to Lullford                           | 25 s | the canal beside the river                                            | locks, a lock-keeper's cottage, an aqueduct                                 | **W3** at the aqueduct over the Cog                        |
| Sunstone Gap  | Cogsworth over the range to Palm Spring and Dust Gulch                    | 77 s | forest, alpine, snow, then the lee down to heath, scrub and the oasis | the Gap Hut; the first view of the desert and the plume                     | **W5**: an avalanche at the gap (and at the tunnel portal) |
| Canyon Road   | Dust Gulch down the Dry Wash's canyon to Hearthold                        | 72 s | scrub, mesas, the canyon                                              | the Lode on the way, a wash bridge, the castle seen from the canyon's mouth | **W6**: the chasm bridge over the fire ring                |
| Ember Way     | Hearthold to the caldera forge and Cinder Springs                         | 34 s | ash and basalt                                                        | the forge, the basalt ring, the springs' terraces                           | (inside W6)                                                |
| Ash Coast     | the halt along the south-west coast through Cinderwick to the springs     | 93 s | farmland, then dunes, then black sand and ash                         | Cinderwick; the fresh lava flow at the ring                                 | **W6**: the crust causeway over the new flow               |
| Lull Road     | the valley east across the plains through Lullford to Neon's swing bridge | 68 s | fields, copses, market gardens                                        | Lullford's market; the swing bridge with the city across                    | **W7**: the swing bridge                                   |
| Coast Path    | Driftwood's lane east along the cliffs through Gullwick to the Lull Road  | 62 s | cliff top, coves                                                      | Gullwick's smokehouse; the Sleepwater's footbridge                          | (joins W7)                                                 |
| Headland Lane | Driftwood to the Headland                                                 | 8 s  | the neck                                                              | the stile                                                                   | **W1**                                                     |
| Shell Bar     | the Headland's tip to the main isle                                       | 10 s | a sandbar                                                             | tide pools, a tide post                                                     | **W4** (with the ferry)                                    |
| Cape Road     | Neon to the Launch Cape                                                   | 9 s  | salt flats                                                            | the fuel farm, the pad                                                      | the pad is **W8**                                          |

**Rhythm.** Town, route, town on every line: the valley, Fernhollow, Cogsworth, the Gap Hut, Palm Spring, Dust Gulch, the Lode, Hearthold. The valley, Lullford, Neon, the Cape. Driftwood, Gullwick, Neon. The halt, Cinderwick, the springs.

**Loops:**

- valley, Col Path, Frostline, High Fells, Cogsworth, Foothill Road, valley;
- valley, Foothill Road, Cogsworth, Towpath, Lullford, Lull Road, valley;
- valley, Lull Road, Neon, Coast Path, Driftwood, valley;
- Cogsworth, the Gap, Dust Gulch, Canyon Road, Hearthold, Ember Way, the springs, Ash Coast, the valley, Foothill Road, Cogsworth (the grand loop round the range's south-west end).

### 6.2 Shortcuts (each opens with the way of the route it runs beside)

| Shortcut                           | Between                                                                                       | Way      |
| ---------------------------------- | --------------------------------------------------------------------------------------------- | -------- |
| The valley train                   | the halt and Cogsworth's platform, through the Millrace gorge                                 | W3       |
| The desert line                    | Cogsworth's platform and Dust Gulch, through a tunnel under the Gap                           | W5       |
| The maglev                         | Cogsworth's terminus down the Lull's valley to Neon's Skyport (its own viaduct over the Lull) | W7       |
| The ferry                          | Driftwood's pier and Lagoon Landing                                                           | W4       |
| The mine cart (S1)                 | the Lode down the canyon to the caldera forge                                                 | after W6 |
| The coastal steamer (S3, proposal) | Neon and Driftwood                                                                            | after W7 |
| The rocket and the lander          | the Launch Cape to Halcyon, then Lumen                                                        | W8, W9   |

### 6.3 Walk times from the hut (`stats.json`)

| To                                 | On foot (s)             | With shortcuts (s) |
| ---------------------------------- | ----------------------- | ------------------ |
| the stall, the square, the library | 12 to 14 (v2)           | same               |
| Fernhollow                         | 25.5                    | 25.5               |
| the Frostline (Snowmelt Lake)      | 26.5                    | 26.5               |
| Driftwood                          | 41.4                    | 41.4               |
| Cogsworth                          | 57.9                    | 22.9               |
| Lullford                           | 59.4                    | 59.4               |
| the Gap Hut                        | 59.6                    | 50.2               |
| Cinderwick                         | 63.2                    | 63.2               |
| Gullwick                           | 73.7                    | 73.7               |
| Palm Spring                        | 86.9                    | 57.5               |
| Lagoon Landing                     | 92.0 (by the Shell Bar) | 53.8 (by ferry)    |
| Neon Harbour                       | 102.0                   | 50.3               |
| the Lode                           | 114.5                   | 39.8               |
| Dust Gulch                         | 121.3                   | 27.9               |
| the Launch Cape                    | 121.6                   | 61.9               |
| Cinder Springs                     | 127.9                   | 64.6               |
| the Ember Caldera forge            | 149.3                   | 42.8               |
| Hearthold                          | 164.1                   | 57.6               |

The far places are 2 to 3 minutes on foot, a real journey, and under about a minute with the shortcuts. The everyday places stay within 15 s.

## 7. Sunstone Reach: a journey into the heat

Sunstone Reach is not a box west of the valley but the whole rain shadow of the Greyspine, entered over its only pass. It is designed as a sequence of places, each seen before it is reached.

1. **The climb.** From Cogsworth's platform the Sunstone Gap path climbs through wet conifer forest, mist and moss. Then come alpine meadow and snow at the Gap. The Gap Hut is a stone refuge with a stove and a bench, where W5 (the avalanche) is cleared.
2. **The reveal at the Gap.** The wind turns warm and dry (a föhn: air falling down the lee side warms). The first view is of the whole lee: heath, then the yellow of the scrub, then the desert to the horizon, the white of the salt pan, and Mount Ember's plume far to the south-west.
3. **The descent into the heat.** Snow gives way to bare rock, then dry heath with dwarf pines, then scrub with the first cacti. The light gets whiter and the shadows shorter, dust hangs in the air, and the ambient sound changes from wind to cicadas.
4. **Palm Spring, the first oasis.** Snowmelt from the range surfaces at the foot of the slope: palms, a pool, a water-seller's awning, camels resting. It explains the desert's life: all its water comes from the mountains.
5. **Dust Gulch, the frontier town.** One street of false fronts on boardwalks at the railhead, with the desert line's platform and water crane. The water tower is filled by a pipe from the spring. The corral and the saloon sit under the range's wall. The red mesas rise in the west.
6. **The Lode.** The mine in the lee foothills: a tunnel mouth in the rock, ore tubs, a timber stack and the cart line's start. It is why the town exists.
7. **The canyon.** The Canyon Road follows the Dry Wash down between mesas: a flood-cut gorge with layered red walls and a wash bridge, shaded and cooler. At its mouth the land opens and Hearthold stands on its rock across a lava chasm, the plume behind it.
8. **Hearthold, the castle above the lava.** It is reached over the chasm bridge (W6), the only safe ground between desert and fire. The bell keeps the hours.
9. **The fire country.** Ash, basalt and glowing seams: the caldera forge using the volcano's heat, the basalt sparring ring, and Cinder Springs' terraces where the fire country rests. From there the Ash Coast leads home along the black-sand shore, closing the grand loop.

**Its sizes.** Dust Gulch is a 544 x 320 desert town. Hearthold is 400 x 400 inside its moat. Palm Spring is 300 x 220. From the Gap to Dust Gulch is about 50 s on foot, and the Canyon Road to the castle about 72 s, with something to see every 5 s along the way: dunes, cacti, a windpump, a dead tree with vultures, a wagon wreck, mesa ledges, the wash bridge. v2's and Claude D's places (the gulch's street, the oasis, the castle, the caldera, the springs) keep their plans inside this layout. The mirror of v3 is dropped: Sunstone faces the range it lies behind.

## 8. The places inside the land (v2's plans, with v4's changes)

### 8.1 What v4 changes from v2 and v3

- **The valley.** The Sleepwater now leaves the valley east to join the Lull; Driftwood's estuary is the Brook's. The Headland is a promontory on a neck, with the stile on the neck. The Frostline is a cirque with a cliff rim, left by the Col Path and the High Fells (both W2). The halt's line runs east along the foothills to Cogsworth, and the Ash Coast leaves from the halt.
- **Cogsworth.** On the Cog, in the coal hills below the Gap. The platform faces the Gap, the towpath leaves south, the maglev's terminus is on the Lull side.
- **Sunstone Reach** (section 7) replaces v2's 6.4 layout; its places keep their plans.
- **Neon.** On the Lull's east bank at the mouth, with the swing bridge (W7) upstream, the estuary marshes to the west and the Launch Cape to the east.
- **The isles.** The main island of a five-island chain, reached by the Shell Bar from the Headland or by ferry.
- **Halcyon and Lumen** as v2, reached by the rocket and the lander.

The sections below are v2's plans as decided; their internal walk times come from v2's block-outs, and where they mention v2's or v3's neighbours (an estuary, the line entering from the west, the elevator), 8.1 and sections 6 and 9 take precedence.

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

### 8.5 Neon Harbour and the Skyport

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

### 8.6 Halcyon Station

320 x 576 px, unchanged: rooms in the order of the climb, from the elevator's airlock at the bottom through hydroponics, the galley, the atrium and the sleep bay, to the shuttle hatch (W9) and the lounge under the windows. From the airlock: hydroponics 3.4 s, the atrium 6.3, the hatch 10.7, the lounge window 12.2. A station is a building; one screen of rooms is enough.

### 8.7 Lumen

384 x 704 px (today 320 x 576): the pad on the crater's rim (T2), the habitat with its solar arrays and the ice rig in the shadowed crater (T1), the pressure tube down to the dome on the crater floor (T0), the moon tree and the hammock. From the pad: the habitat 8.5 s, the moon tree 13.9, the hammock 16.4. A little wider so the crater reads as a crater on a 300 px screen.

## 9. Space: the rocket (decided)

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

## 10. The ways on the land

The nine ways (#95, decided) keep their names, order and tasks. Each one stands where a route crosses one of the land's barriers. A place with more than one way in has one way mending all of them.

| #   | Way                                      | Barrier and crossing                                                                                   | What is being mended                                                                      | In reach after (#95)                     |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | ---------------------------------------- |
| W1  | The Headland stile                       | the sea round the Headland; the neck                                                                   | the stile's broken step                                                                   | the start                                |
| W2  | The ridge col                            | the Frostline's rim; the Col Path and the High Fells                                                   | two pines from one storm                                                                  | the start                                |
| W3  | The Millrace landslip                    | the Cog; the Foothill Road (the gorge), the High Fells (the Cog's head) and the Towpath (the aqueduct) | a landslip in the gorge; a rockfall at the head; a breach in the aqueduct, from one storm | the start                                |
| W4  | The Shell Bar and the ferry              | the sea; the Shell Bar                                                                                 | a washed-out stretch; the ferry on the slip                                               | the start                                |
| W5  | The Sunstone Gap                         | the Greyspine's crest; the Gap (and the desert line's tunnel portal)                                   | an avalanche                                                                              | W3 (you reach the Gap through Cogsworth) |
| W6  | The chasm bridge and the Ash Coast crust | the fire ring; the Canyon Road's bridge and the Ash Coast's crossing                                   | the bridge's missing span; a crust causeway over the new flow                             | W5 (the masons come from Dust Gulch)     |
| W7  | The Lull swing bridge                    | the Lull; the swing bridge (the Coast Path joins the Lull Road before it)                              | stuck open, waiting for a gear from Cogsworth's foundry                                   | W3                                       |
| W8  | The rocket                               | (a journey) the Launch Cape's pad                                                                      | the launch not yet fuelled                                                                | W7                                       |
| W9  | Halcyon's lander                         | (a journey) Halcyon's hatch                                                                            | under a cover                                                                             | W8                                       |

**The gate check** (`gates.json`). The script finds every place a route crosses a barrier (the crest, the rim, the Cog, the Lull, the fire ring, the sea) and puts the way there. It reports any crossing with no way; there is none, apart from the Ember Way crossing the crest inside the fire country, which is already behind W6. With the ways opened one at a time in road order, a flood fill from the hut reached nothing behind a closed way and everything behind an open one, at every step.

## 11. The engine: one world canvas (decided)

v3's design stands (decided by Matt). One world canvas is authored in chunks (each settlement, each route, and the land itself, which is now generated from the geography fields and then drawn over by hand) and cut into world tiles of 256 px. The numbers grow with the land:

- **Canvas:** 11264 x 6912 px, 1408 x 864 cells. 63 % of it is land.
- **Tiles:** 1188 render tiles. 413 are uniform (open sea, mostly) and share a few pictures; 483 hold walkable ground.
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

The mock (`ingame-map-mock.png`) is drawn from the block-out. Tiers step at 32 px, each with a darker face on its south edge and a thin outline. Water is deep blue, paths pale, settlements are house icons with their names, and the ways are red dots. A finished version would add:

- the pixel frame and font from `interface.md`;
- the companion's marker;
- fog over places not yet walked;
- the journeys as dashed lines;
- small pictures of each place's landmark, after Stardew's map.

## 13. Order of work and owners

| Step | Lane | Work                                                                                                                                                                                                                               | Needs                     |
| ---- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| P0   | A    | The toolkit lands (`terrace.py`, `scale.py`, tiers, the facade composer, `fore.png`)                                                                                                                                               |                           |
| P1   | A    | **The geography chunk**: the height, wetness and warmth fields, the spine, the volcano, the Lull system, the coast, the isles, biome bands with noise; written as data for every other chunk                                       | Matt's yes to decision 20 |
| P2   | A    | The world canvas build (11.1 plus P1) and the renderer streaming world tiles; saves in world coordinates (with Codex)                                                                                                              | P1                        |
| P3   | A    | The in-game map from the build's data in the soft-grid style                                                                                                                                                                       | P1                        |
| P4   | B    | Props to the scale table and #97, including the route props (sawmill, lock-keeper's cottage, aqueduct, Gap Hut, water-seller's awning, wagon wreck, wash bridge, smokehouse, charcoal kilns, tide post, fuel farm, the rocket)     | P0                        |
| P5   | E    | The home valley in the land (v2's plan with 8.1's changes), Driftwood, the Headland, the Frostline's cirque with A                                                                                                                 | P2, P4                    |
| P6   | A    | The routes' chunks: Col Path, High Fells, Foothill Road, Towpath, Lull Road, Coast Path, Headland Lane                                                                                                                             | P2                        |
| P7   | D    | Sunstone Reach as a journey (section 7): the Gap, Palm Spring, Dust Gulch, the Lode, the canyon, Hearthold, the fire country, the Ash Coast and Cinderwick; then the Launch Cape, Halcyon and Lumen with the rocket and the lander | P2                        |
| P8   | C    | Cogsworth on the Cog, Lullford, Fernhollow, Gullwick; Neon at the Lull's mouth; the isles' chain and the Shell Bar                                                                                                                 | P2                        |
| P9   | A    | The ways on the land (#118 to world coordinates), the journeys as shortcuts, the gate check as a test                                                                                                                              | P2, #95's rules (Codex)   |

## 14. Decisions for Matt

| #   | Decision                                                                                                                         | Recommendation or decision                                                                             |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1   | Keep the zoom at 12 adults across                                                                                                | **Decided 20 Oct: keep.**                                                                              |
| 2   | Canvases streamed in tiles instead of the zone grid                                                                              | **Decided 20 Oct: yes.**                                                                               |
| 3   | Sizes from the sizing table; everyday places within 15 s of the hut                                                              | **Decided 20 Oct: yes.**                                                                               |
| 4   | The valley at 1280 x 2688 with a real village, a farmstead and Driftwood                                                         | **Decided 20 Oct: yes.**                                                                               |
| 5   | Cogsworth with Gasworks Hill and the Terminus                                                                                    | **Decided 20 Oct: yes.**                                                                               |
| 6   | Neon's canvas a quarter smaller with more street                                                                                 | **Decided 20 Oct: yes.**                                                                               |
| 7   | Sunstone Reach as one continuous land                                                                                            | **Decided 20 Oct: yes.**                                                                               |
| 8   | A rocket from the Launch Cape replaces the space elevator; Halcyon's lander to Lumen                                             | **Decided 20 Oct (v3): yes.**                                                                          |
| 9   | One world canvas, authored in chunks and streamed in tiles                                                                       | **Decided 20 Oct (v3): yes.**                                                                          |
| 10  | One land designed from its geography (section 4): the Greyspine, its rain shadow, the Lull system, Mount Ember, the isles' chain | **Yes.** It is what Matt asked for, and every place's position now has a reason.                       |
| 11  | About twice v3's walkable ground (120 zone-areas), with land beyond the walked corridors drawn but not walked                    | **Yes.** Expansive views without an art budget that doubles again.                                     |
| 12  | The thirteen routes and the hamlets on them (section 6)                                                                          | **Yes.** Town, route, town; four loops; far places 2 to 3 minutes on foot, under a minute by shortcut. |
| 13  | Sunstone Reach as a journey over the Gap (section 7), not mirrored                                                               | **Yes.** Matt asked for it to be immersive; it now lies where a desert would.                          |
| 14  | The valley's river joins the Lull; Driftwood's estuary is the Brook's                                                            | **Yes.** One river system, as asked.                                                                   |
| 15  | The ways at the land's barriers (section 10); W5 at the Gap, W6 at the fire ring, W7 at the Lull                                 | **Yes.** Every gated place has every way in mended by its one way.                                     |
| 16  | The in-game map in the soft-grid style (example 2)                                                                               | **Yes** (Claude A's recommendation too).                                                               |
| 17  | The coastal steamer (S3)                                                                                                         | **Yes, later.**                                                                                        |
| 18  | Ground pictures at 1x (or 2x)                                                                                                    | **Test, then 1x if crisp.**                                                                            |
| 19  | Secret pockets hold no keepsakes; no one-way ledges for now; the companion stays 24 px                                           | **Yes** (from v2).                                                                                     |
| 20  | The geography as data (height, wetness, warmth fields) that every chunk reads                                                    | **Yes.** It is what keeps the land from being stitched.                                                |

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

**Gaps.** No developer source gives Stardew's, Eastward's or CrossCode's map sizes or walking speeds; the reference sizes here are measured on store screenshots by character height and are good to about a quarter of an adult. No castle or desert town appears in our reference shots, so those two sizes are built from parts. The walk-seconds are measured on block-outs, not on drawn art; the redraws will move them by a few seconds. The garden's walkable share in today's totals is an estimate.

**Gaps (v4).** No developer interview found here explains how Game Freak lays out a region beyond the real place it is based on; the region facts are Bulbapedia's. No Pixpil interview found here describes how Eastward's maps join. The height, wetness and rain-shadow model is ours (standard physical geography), not a game's.
