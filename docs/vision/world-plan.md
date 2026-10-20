# The world plan: regions redesigned on the soft grid

Matt, 20 Oct 01:05, after seeing every region rendered whole: "All of these need redesigns pretty much, to fit the newly established soft grids. also consult the other games mentioned for world buildings how large parts of the maps should be and how they are attached together and how you can create interesting spaces." And at 01:06: "the props/ buildings/ assets that are really detailled already and fit the soft grid can be reused. but really dig deep into the logic of the world an what that means for props".

**Status: a plan for Matt to review.** It decides the structure of every region: how big it is, how its areas join, what you see from where, where its heights are, what its people do and so which things must stand in it, and where the ways that open the world sit. It does not draw anything yet.

It builds on, and does not repeat:

- `verticality.md` (branch `claude-a/verticality-study`): the soft grid (8 px), the five rules, the terrace toolkit, the facade composer and the scale table (an adult is 25 px). Every size below is on that grid.
- `research/soft-grid.md` and `research/world-references.md` (branch `claude-a/world-references`): how the reference games build ledges, water, coasts, paths, fences, yards and plazas.
- `../research/2d-world-design.md` and `research/placement-paths-verticality.md`: hubs, loops, landmarks, corridors, the semantic layer and the path generator.
- `world-unlocks.md` (draft PR #95, branch `claude-a/world-unlocks`): the mechanism that opens the world. Section 4 here places its nine ways in the world.
- `prop-logic.md` (branch `claude-a/prop-logic`): the general rules for what a prop needs (support, access, supply, use). Section 3 here only says what each place makes and needs, and so which props must stand where.
- `world-rules.md`, `world-ports.md` and `world-atlas.md` stay the rulebook; this file replaces the "Zones drawn so far" layout descriptions in `world-atlas.md` as each region is redrawn.

## 0. Our yardsticks

| Measure            | Value                                                    | Source                                 |
| ------------------ | -------------------------------------------------------- | -------------------------------------- |
| Zone               | 320 x 576 px, 40 x 72 cells of 8 px                      | `scripts/art/zones.py`                 |
| Adult (A)          | 25 px                                                    | `verticality.md` 5                     |
| Companion's walk   | 40 px a second (1.6 A a second); 52 by the keys          | `SPEED` in `components/atlas-walk.tsx` |
| Across a zone      | 8 s                                                      | 320 / 40                               |
| Down a zone        | 14.4 s                                                   | 576 / 40                               |
| What a phone shows | about 300 x 650 art px, so about 12 A wide and 26 A tall | `verticality.md` 2                     |

**Observation: a reference screen is a third of our zone.** Converted by the height of a person (each game's own pixels, measured on official screenshots or from its native resolution):

| Game                        | Screen              | Person   | Screen in A  |
| --------------------------- | ------------------- | -------- | ------------ |
| Pokémon Red and Blue        | 160 x 144           | 16       | 10 x 9       |
| Link's Awakening (Game Boy) | 160 x 128 playfield | 16       | 10 x 8       |
| A Link to the Past          | 256 x 224           | about 24 | about 11 x 9 |
| Stardew Valley at 1080p     | 480 x 270 at 4x     | 32       | 15 x 8.4     |
| Eastward at 1080p           | 640 x 360 at 3x     | about 50 | 12.8 x 7.2   |
| Sea of Stars at 1080p       | 640 x 360 at 3x     | about 47 | 13.6 x 7.7   |
| **NapAttack on a phone**    | **300 x 650**       | **25**   | **12 x 26**  |

The reference games show 10 to 15 adults across and 7 to 9 down. We show as many across and three times as many down. So every lesson "one thing per screen" becomes **one thing per third of a zone** (about 190 px, 5 seconds of walking north or south), and every sightline the references build east and west we can build only north and south.

## 1. What the games teach, and the rules at our scale

### 1.1 How big things are

Measured in our units (A converted to zone px, walk-seconds at 40 px a second). Pokémon's sizes are exact, from the disassembly's map table, where a block is 32 px, two tiles of one person each ([pret/pokered, `constants/map_constants.asm`](https://github.com/pret/pokered/blob/master/constants/map_constants.asm)). The rest are sourced counts or labelled observations.

| Place                                    | Size in its game                                                                                                                                                                                 | In our zones (w x h)                                                   | Walk end to end               |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- | ----------------------------- |
| Pallet Town, Lavender Town               | 10 x 9 blocks (2 x 2 screens)                                                                                                                                                                    | 1.6 x 0.8                                                              | 12 s                          |
| Viridian, Pewter, Cerulean, Saffron      | 20 x 18 blocks (4 x 4 screens)                                                                                                                                                                   | 3.1 x 1.6                                                              | 25 s                          |
| Celadon (the biggest city)               | 25 x 18 blocks                                                                                                                                                                                   | 3.9 x 1.6                                                              | 31 s                          |
| Route 1                                  | 10 x 18 blocks                                                                                                                                                                                   | 1.6 x 1.6                                                              | 22 s                          |
| Routes 3 and 4                           | 35 and 45 x 9 blocks                                                                                                                                                                             | 5.5 and 7 x 0.8                                                        | 44 and 56 s                   |
| Route 12, Cycling Road (17)              | 10 x 54 and 10 x 72 blocks                                                                                                                                                                       | 1.6 x 4.7 and 1.6 x 6.3                                                | 68 and 90 s                   |
| All of Kanto outdoors                    | 43,380 A²                                                                                                                                                                                        | about 147 zones of area                                                |                               |
| Koholint Island (Link's Awakening)       | 256 screens in a 16 x 16 grid, 16 named regions ([ZeldaSpeedRuns, in-game maps](https://zeldaspeedruns.com/la/doghouse/in-game-maps))                                                            | about 69 zones of area; a region averages 16 screens, about 4 zones    |                               |
| Ukuku Prairie, Koholint's largest region | 32 screens, a strip four screens wide from Mabe Village to the Face Shrine, bordering six areas ([Zelda Dungeon](https://zeldadungeon.net/wiki/Ukuku_Prairie))                                   | about 9 zones                                                          |                               |
| A Link to the Past, Light World          | 8 x 8 chunks, read at 16 x 16 for obstacles ([Game Developer, Marshalkowski](https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2)) |                                                                        |                               |
| Animal Crossing town                     | acres of 16 x 16 spaces: 5 x 6 acres on the GameCube, 4 x 4 in Wild World, 5 x 4 in New Leaf, 7 x 6 in New Horizons ([Nookipedia, Acre](https://nookipedia.com/wiki/Acre))                       |                                                                        |                               |
| **NapAttack today**                      | 36 zones in 9 regions                                                                                                                                                                            | valley 13, Neon 9, Sunstone 6, isles 4, Cogsworth 2, station 1, moon 1 | valley summit to harbour 86 s |

What this says: a town is 1 to 4 of our zones and 12 to 30 seconds across; a route is 22 to 90 seconds long; a region of a Zelda island is about 4 zones. Our whole world has about half the area of Koholint and a quarter of Kanto. It does not need more ground; it needs each zone to be worth its 14 seconds. TUNIC's world was once "twice as big, but it was mostly empty space", and the team cut a desert because "running across dunes was decidedly not as interesting as the other parts of the game" ([Game Informer](https://gameinformer.com/2022/05/30/tracing-threads-the-making-of-tunic)).

### 1.2 How areas attach

- **A hub in the middle, districts on its edges.** Pelican Town's northwest exit leads to the Bus Stop and the farm, the southwest to Cindersap Forest, the south to the Beach, the north to the Mountain ([Stardew Valley Wiki, Pelican Town](https://stardewvalleywiki.com/Pelican_Town)). Hyper Light Drifter's town sits "smack dab in the center of the world" with four directions out, "though only three are unlocked, and you can conquer them in any order" ([Hardcore Gaming 101](https://www.hardcoregaming101.net/hyper-light-drifter/)). Moonlighter's village is built round the dungeon doors ([Wikipedia](<https://en.wikipedia.org/wiki/Moonlighter_(video_game)>)). The valley already is this hub; the garden is its centre.
- **Edges change maps; doors swap scenes.** Stardew moves you between maps "when you reach the edge of an area or enter a building" ([Stardew Valley Wiki, Modding:Maps](https://stardewvalleywiki.com/Modding:Maps)). Link's Awakening keeps "buffer screens" between areas with different tile sets, so two areas never meet on one walkable seam ([Set Side B, after pmorinerie's disassembly](https://setsideb.com/?p=133)). Our seams are open land; the lesson is the buffer: a strip of shared character between two districts, not a hard switch.
- **Chokepoints at the change of region.** Pokémon puts a gatehouse between a route and a city; Skyarrow Bridge has "a gate between the bridge and the connected area" at each end, and the city is seen across the water from it ([Bulbapedia, Skyarrow Bridge](https://bulbapedia.bulbagarden.net/wiki/Skyarrow_Bridge)).
- **Almost everything reachable, held together by small walls.** At 16 x 16 chunks, "only 6 [of 256] cannot be reached" in A Link to the Past, which the analysis calls what makes the world "rich vs. just expansive"; the coarse 8 x 8 view is nearly all open and "feels kind of boring" ([Game Developer](https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2)).
- **One-way drops and shortcuts back.** Pokémon's ledges are "one-way obstacles", "often used to provide shortcuts to return from a later area to an earlier one" while keeping later areas from being "reached too early" ([Bulbapedia, Ledge](https://bulbapedia.bulbagarden.net/wiki/Ledge)). TUNIC's shortcuts bring you back to a place from its other side, which "expands your idea of the space you're in" ([Game Developer](https://www.gamedeveloper.com/design/designing-content-for-no-one-an-interview-with-the-team-behind-tunic)).
- **Vehicles for the far places.** Eastward's chapters each bring "a set of map areas", reached on the trains Charon and Monkollywood ([Wikipedia](<https://en.wikipedia.org/wiki/Eastward_(video_game)>)). Chained Echoes is "very linear" until the airship, then "the world opens up and you can … easily revisit older locations" ([RPGamer](https://rpgamer.com/2022/11/chained-echoes-interview/)). Animal Crossing's GameCube station is always in acre A-3, on the top edge ([Nookipedia, Acre](https://nookipedia.com/wiki/Acre)).
- **Loops, not trees.** Team Cherry wanted "as many connections between areas as we could" (`2d-world-design.md`); Animal Crossing villagers only go where bridges and inclines connect ([Nookipedia, Ramp](https://nookipedia.com/wiki/Ramp)).

### 1.3 How spaces get interesting

- **Small pockets, often.** Sea of Stars is "all these small pockets" where players keep reaching the fun part and moving on; its levels are "dense and multitiered" ([MobileSyrup](https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/)).
- **The camera decides when you see the landmark.** TUNIC's view lets the team "control when you get these bigger vista views, and when you would see a certain landmark", and hide "a secret passage" round a corner ([Game Developer](https://www.gamedeveloper.com/design/designing-content-for-no-one-an-interview-with-the-team-behind-tunic)). Our camera is portrait: north is where the reveal happens.
- **Reveals widen the world.** One bombable wall makes every wall a question: "how big this world is suddenly just got a little bit bigger" (same source). Minish Cap's portals shrink Link so the same places hold a second, tiny scale ([Zelda Wiki, Minish Portal](https://zeldawiki.wiki/wiki/Minish_Portal)).
- **Dense towns invite.** Eastward wanted "sprawling beautiful towns to discover", grown from a sketch like the Kowloon Walled City ([Nintendo](https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward)).
- **Height carries the composition** (world-references lesson 8; verticality.md): two or three tiers per screen, stairs where paths meet faces.
- **Gaps:** no developer source gives numbers for density or pacing; the beat lengths below are our inference, measured against the references.

### 1.4 How worlds gate

- **A believable obstacle.** Snorlax sleeps across Routes 12 and 16 until the Poké Flute wakes it ([Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Flute)). Stardew clears debris from the bridge north of the lake on Spring 5, opens the Railroad with an earthquake on Summer 3, repairs the Quarry bridge when the Crafts Room bundles are done, and keeps the Secret Woods behind "a large log that can be cleared after upgrading to at least a Steel Axe" ([Stardew Valley Wiki, The Mountain](https://hu.stardewvalleywiki.com/Hegyek); [Secret Woods](https://stardewvalleywiki.com/Secret_Woods)). Link's Awakening's largest region opens only "after Link obtains the Power Bracelet" ([Zelda Dungeon](https://zeldadungeon.net/wiki/Ukuku_Prairie)).
- **Firm, not hard.** TUNIC wanted "as few hard gates as possible": "not hard gates, but soft gates", a "gentle touch without ever explicitly blocking anything off" (Game Developer, above).
- **Order without dead ends.** Zelda's item gates had to open "in a proper order without dead-ending the player" (`2d-world-design.md`); Skyarrow Bridge stays shut until a story beat, then stays open.
- **Many open, a few shut.** Hyper Light Drifter opens three directions of four at once; Moonlighter keeps a fifth door sealed until four keys are found.

### 1.5 The rules at our scale

These are decisions for NapAttack, inferred from the sources above. The numbers are starting points to tune in play.

1. **An area is 1 to 2 zones**, 8 to 30 seconds across, with one character, one landmark and one node. A **region is 4 to 9 zones** in 3 to 6 areas; a walk from end to end stays under 60 seconds (the valley, three sections joined, is the one exception at about 86).
2. **A beat every third of a zone.** Something at the companion's scale (a resident, a bench facing a view, a stall, a stair, a bridge, a vista, a work yard) at least every 190 px of walking (5 seconds); never a stretch of more than half a zone (7 seconds) with nothing in it.
3. **Main ways run north and south; pockets run east and west.** The phone sees 26 A north and south and only 12 across, so the road that carries you through a region, and the landmark that pulls you on, run along the screen's tall side. East and west hold side yards, corridors and secret pockets.
4. **One landmark per area, seen from the area before it.** It stands in the north third of its area and rises up to 48 px over the border (world-atlas, "How borders meet"), so it is on screen while you are still in the zone below.
5. **Every region of four zones or more has a loop**, and every area two ways in, except deliberate pockets (at most one per side of a region), which end in a view, a resident or a story detail.
6. **Regions attach at chokepoints; areas attach by land.** Inside a region, neighbouring areas are open land closed only by real features (world-ports). Between regions, and into every gated area, there is one chokepoint (a col, a bridge, a stile, a station) or a drawn barrier on every way in.
7. **Arrive at the edge, see the middle.** A station, pier or pad stands at the edge of its region, with a vista of the region's landmark from the moment you step off (Animal Crossing's station on the top edge; Skyarrow's view of Castelia).
8. **Two to four tiers per region, at most two full tiers and one low step per screen** (verticality.md). Important places sit low, lookouts high. Stairs stand where paths meet faces.
9. **Busy and quiet alternate by area.** No two busy areas share a seam without a quiet strip between; no quiet stretch is longer than one zone. The main entrance of each region is a corridor that opens into a reveal.
10. **Pockets and secrets: one to three per region**, hidden by the camera (behind a tall crown or building, in the notch of a tier, round a bend), reached by a narrow gap. They hold a view, a resident or a story detail; never a reward (AGENTS.md).
11. **Ways are things being mended at chokepoints.** You can see the far side before it opens; a way never strands you or blocks the way home; once open it stays open (`world-unlocks.md`).
12. **Density over extent.** No new zone unless it adds a loop or a missing kind of place; empty zones are cut or filled.
13. **Every place has a trade, and the trade is drawn.** Who lives there, what they make and need, and how goods move (cart, boat, rail, cable) decide the props: producer, way, consumer, each standing where the trade puts it (`prop-logic.md`).
14. **Structure on the grid, texture off it.** Rims, banks, paths and building feet on 8 px lines; roughness within 4 px (verticality.md 4f).

## 2. The world at a glance

```
                                      (Lumen)  <- shuttle W9 --  (Halcyon Station)
                                                                     ^ elevator W8
                                                                     |
   (Sunstone Reach) <-- desert line W5 --  (Cogsworth)  -- maglev W7 -->  (Neon Harbour)
    gulch, oasis, pass                      junction, hill,                skyport, nine areas
    | chasm bridge W6                       canal, terminus                     :
    v                                          ^                                :  coastal steamer
   (Hearthold, caldera, springs)               | valley train W3               :  (proposal, S3)
    ^ mine cart S1 (shortcut)                  |                                :
                                   (THE VALLEY: home)  - - - - - - - - - - - - -
                                    heart always open
                                    ridge col W2 -> Frostline
                                    Headland stile W1
                                    Driftwood ferry W4 -> (Tidebloom Isles)
```

| Region                                                                  | Zones now | Zones planned | Areas   | End to end on foot            | Lane             | Opened by             |
| ----------------------------------------------------------------------- | --------- | ------------- | ------- | ----------------------------- | ---------------- | --------------------- |
| The valley heart (garden, woodland, riverside, town, park, halt, ridge) | 7         | 7             | 7       | 43 s north-south, 24 s across | E, B (garden), A | always open           |
| Driftwood (harbour, headland)                                           | 2         | 2             | 2       | 16 s across                   | E                | heart; Headland by W1 |
| The Frostline (hollow, snowmelt, saddle, summit)                        | 4         | 4             | 4       | 43 s                          | A                | W2                    |
| Cogsworth                                                               | 2         | **4**         | 4       | 29 s                          | C                | W3                    |
| Tidebloom Isles                                                         | 4         | 4             | 4       | 29 s loop                     | C                | W4                    |
| Sunstone Reach (oasis, gulch, pass)                                     | 3         | 3             | 3       | 24 s                          | D                | W5                    |
| Hearthold and the fire country (castle, caldera, springs)               | 3         | 3             | 3       | 29 s                          | D                | W6                    |
| Neon Harbour and the Skyport                                            | 9         | 9             | 9       | 43 s                          | C                | W7                    |
| Halcyon Station                                                         | 1         | 1             | 6 rooms | 14 s                          | D                | W8                    |
| Lumen                                                                   | 1         | 1             | 3       | 14 s                          | D                | W9                    |
| **All**                                                                 | **36**    | **38**        |         |                               |                  |                       |

The region ids and grids in `LAYOUT` stay as they are except Cogsworth, which gains two zones (section 3.4). The valley's empty corner at (-1, 2) becomes open sea instead of forest (section 3.2). Saved spots carry over by `lib/world-layouts.ts` as before.

## 3. The regions

Each diagram is the region's zone grid, north up, one box per zone (320 x 576). Inside a box: the area's name, its tier (T0 lowest) and its landmark. On the seams: `.` open land, `=` a road or path runs on, `S` a stair, `B` a bridge, `#` closed by a face, wall or water, `~` sea, `W1`..`W9` a way from `world-unlocks.md` (section 4). Coordinates are zone px, on the 8 px grid, approximate until drawn.

### 3.1 The valley heart: the garden, woodland, riverside, Crossroads Town, the park, the halt and the ridge

```
            col -1                  col 0                   col 1
        +----------------------+----------------------+----------------------+
row -1  | FIR HOLLOW (3.3)     # THE RIDGE      T3    |  (old forest)        |
        |                      # cabin, tarn          |                      |
        +###### the fall ######+--------- S ----------+----------------------+
row  0  | THE WOODLAND   T2    . THE GARDEN     T2    . THE RIVERSIDE  T2/T1 |
        | spring pool, stones  . the hut on its yard  . mill on the step     |
        +---------- . ---------+------ S gate S ------+---------- . ---------+
row  1  | VALLEY HALT    T1    = CROSSROADS     T1    B THE PARK       T1    |
        | station, windmill    = the square, library  . bandstand, river     |
        +~~~~ shore ~~~~~~~~~~~+---------- = ---------+---------- = ---------+
row  2  |  (open sea, 3.2)     | DRIFTWOOD (3.2)      | THE HEADLAND (3.2)   |
```

**Size.** Seven zones, three across and three down (the ridge sits above the garden). 24 seconds across, 43 seconds from the ridge to the town's south edge.

**The idea.** A river valley that steps down from the mountains to the sea in three wide terraces: the ridge meadow (T3), the garden terrace with the woodland and the upper riverside (T2), and the valley floor with the town, the park and the halt (T1). The faces between them are 32 px and run east and west, so walking south always means walking down. The water explains the whole valley: snowmelt from the Frostline falls over the escarpment into the woodland's spring pool, runs east along the garden terrace as the brook, turns the mill where it drops from T2 to T1 at the riverside, and runs south as the river past the park to Driftwood's estuary.

**Areas and their character.**

| Area              | Character                                                                                                                                                          | Busy or quiet                           | Node                     | Landmark (and from where it is seen)                                                 |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------ |
| The garden (home) | the hut on a raised timber yard, the beds and orchard, the brook along its south side                                                                              | quiet                                   | the yard before the door | the hut's roof and smoke, seen from the town's square up the gate lane               |
| The woodland      | a deep wood under the escarpment: crowns closed to the west, a clearing round the spring pool where the fall lands, the stone circle in its own glade              | quiet                                   | the spring pool          | the fall in two tiers down the escarpment, seen from the garden's west side          |
| The riverside     | an open working meadow: the mill on the terrace step, the millpond above it, hay and clover below, beehives                                                        | quiet, working                          | the mill yard            | the mill wheel and its roof, seen from the garden's east lawn                        |
| Crossroads Town   | the busiest place in the valley: a square at the meeting of four roads, terraces of touching cottages, the library, the bakery, the stall, the green with the ring | busy                                    | the square and its well  | the library's bell gable on the square's north axis, seen from the garden gate       |
| The park          | the town's leisure ground on the river's east bank: the bandstand, a drinking fountain, benches facing the river, flower beds, the ice cream cart                  | quiet, social                           | the bandstand            | the bandstand's striped roof, seen from the square over the bridge                   |
| Valley Halt       | the end of the line: a platform and a goods yard, the engine shed, the farm beyond with its windmill and fields to the shore                                       | busy at the platform, quiet at the farm | the platform             | the windmill, seen from the woodland's south edge                                    |
| The ridge         | the cabin meadow under the peaks, the tarn, the trail up to the col                                                                                                | quiet                                   | the cabin's yard         | the col's rock shoulders and the fallen pine (W2), seen from the garden's north lawn |

**Height.** T3 ridge, T2 garden terrace, T1 valley floor. The T2/T1 face is 32 px of earth and stone and runs along y about 520 to 552 of row 0, under the garden's south fence, the woodland's south edge and the riverside's mill step. The T3/T2 face under the ridge is the treeline bank, 32 px, with the ridge trail's stair at the garden's north (x 196 to 244). The woodland's north is the escarpment (two 32 px faces with a ledge between, 72 px in all) that closes Fir Hollow off.

**Attachments.** The garden's gate stair (48 px wide, cheeks, a lamp at its head) leads down to the town lane: the one cut into the T2/T1 face in the garden's span. The woodland and the riverside each meet the floor through their own stair or ramp (the woodland's timber stair at x 120 to 168; the riverside's track ramp beside the mill, rising along the face, 1 in 3). Loops: garden, woodland, halt, town (the west loop); garden, riverside, park, town (the east loop); town, harbour, the estuary footbridge, the park (the coast loop). The halt is the valley's station (W3); the harbour's slip is the ferry (W4).

**Interesting spaces.**

- _Reveal from the gate._ Stepping through the garden's gate onto the stair head, the whole square opens below with the library on its axis: the valley's main view, framed by the stair's cheeks and two trees.
- _The fall._ From the woodland's spring pool you look north up the escarpment at the fall in two tiers, the hollow's firs on the rim.
- _Pocket: the stone circle glade_ in the woodland's south-west, through a gap between two clumps of trees, hidden from the path by the crowns. It holds the stones and a bench.
- _Pocket: under the mill._ A path along the tailrace on T1 to the wheel pit, where you see the wheel turn from below.
- _Pocket: the halt's shore._ Past the farm, a shingle beach below a low bank, an upturned boat and the open sea to the south.
- _Back yards in town._ A passage between the cottages north of the square (an alley 16 px wide) into the back gardens with washing lines and a cat on a wall.

**The trade, and the props it asks for.** Who lives here: the gardener and the companion, the forester (W2's), the miller, the baker, the librarian, the farmer's family at the halt, the porter and stationmaster, the shepherd (W1), townsfolk.

| Place                  | Makes or does               | Needs                                            | Moves by                                           | Props that must exist, and where                                                                                                                                                                                                                                                                                                          |
| ---------------------- | --------------------------- | ------------------------------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Halt farm              | wheat, vegetables, milk     | seed, tools, coal from Cogsworth                 | rail out (flour, vegetables, churns), cart to town | fields in blocks with tilled borders and walkable gaps; the barn with churns and hay against its wall; the windmill on the rise grinding the farm's grain (sacks at its door); a farm track to the platform's goods end                                                                                                                   |
| Halt platform and yard | the line to Cogsworth       | water and coal for the engine                    | rail                                               | the engine shed (W3's barrier: the engine inside, boiler cold) beside the platform; a water tower and a coal stage at the shed; the goods end of the platform with a sack barrow, crates and milk churns waiting; buffers at the line's end; a signal at the platform's west end; the station house on the platform with its door onto it |
| Riverside mill         | flour                       | grain (its own wheat strip on T2 and the farm's) | cart down the track ramp to the bakery             | the millpond on T2 held by a bank, the headrace and its sluice, the wheel at the T2/T1 step, the tailrace on T1 back to the river; sacks on a cart at the mill door; a wheat strip on the terrace with stooks                                                                                                                             |
| Riverside meadow       | honey, hay                  | bees need flowers                                | hand to the stall                                  | beehives in a row along a hedge facing south on the clover; hay in round bales on the lower meadow                                                                                                                                                                                                                                        |
| Woodland               | timber and firewood         |                                                  | handcart to town                                   | the forester's yard on the woodland's south edge, beside the stair: a log stack, a saw horse, a chopping block, a handcart; stumps and felled logs near the track, never on it                                                                                                                                                            |
| Town bakery            | bread                       | flour from the mill, firewood                    | sold at the stall                                  | the bakery on the square's west side with an oven chimney (smoke), a woodpile against its side wall, flour sacks at its back door off the mill track                                                                                                                                                                                      |
| Town square            | water and meeting           |                                                  |                                                    | the well at the square's centre with its worn ring; the stall with goods in front (bread, honey, fish), crates in twos and threes at its side; benches along the square's kerb facing the well; the notice board by the library's steps; lamps on the four roads into the square only                                                     |
| Library                | the Book Club outing        |                                                  |                                                    | the library on the square's north axis, steps and a door apron, a bench and book cart by the door                                                                                                                                                                                                                                         |
| The green and ring     | sparring                    |                                                  |                                                    | the ring of posts on the green south of the square, a bench for watchers                                                                                                                                                                                                                                                                  |
| Park                   | rest                        | water for the fountain                           |                                                    | the bandstand on a rounded rectangle of paving, benches facing it and the river, the drinking fountain on a pipe from the riverside (a small pump house at the river's edge), flower beds in blocks with a gardener's tool shed, the ice cream cart by the bridge (milk from the halt farm)                                               |
| Cottages               | homes                       | water from the well, firewood                    |                                                    | each with a door apron, a back yard with a washing line between a post and the wall, a woodpile under the eave, a chimney                                                                                                                                                                                                                 |
| Ridge cabin            | the Mountain Retreat outing | firewood                                         |                                                    | the cabin with its woodpile, a bench facing south over the valley, the tarn, the marmot on its rock                                                                                                                                                                                                                                       |

**Props kept and redrawn** (scale from `verticality.md` 5; footprints must also fit the grid).

- _Kept_ (detailed, on scale or close, footprint fits): `water_mill` and its frames (just redrawn on the grid, PR #86), `windmill` and frames, `barn`, `beehive`, `haystack`, `round_bale`, `scarecrow`, `pumpkins`, `willow`, `hollow_tree`, `mossy_log`, `stump`, `fern`, `reeds`, `heron`, `lily_pads`, `standing_stone` (and `_b`, `_low`), `woodpile`, `semaphore`, `bandstand`, `ice_cream_cart`, `fountain`, `well`, trees and pines, `cart`, `field_gate` and the wattle hurdles, `marmot_rock`, `snowman`, `sled`.
- _Redrawn to scale_ (Claude B's library, per verticality 5): `house_blue`, `house_red` and the harbour cottages (eaves to 44, doors 32 x 14); `station_house` (door 23 to 32); `bench` (44 long to 32); `stall` (counter 26 to 13 high); `lamp` (44 to 56); `crate` and `barrel` (18 and 19 to 11 and 14); the nap hut (B, with the raised yard).
- _Redrawn for logic_: the drystone walls get stones of three sizes, corner blocks and ends that land on something (world-references 6).
- _New_: an engine shed (two states, W3), a water tower and coal stage, a goods barrow and churns, a bakery with an oven chimney, a pump house, a forester's yard (saw horse, chopping block, log stack), a gardener's tool shed, a book cart.

**Kept from today.** The grid and every zone id; the garden at the centre; the brook's line across the garden; the mill where PR #86 put it; the town at the meeting of four roads; the river's course down the park; the halt's line running west; the two loops. **Changed:** the town's elliptical square becomes a rounded rectangle with the well at its centre and the library on its axis; the houses north of the square become a terrace of touching cottages with a passage; the park's pond goes (the river is the park's water); the garden gets its raised yard and the gate stair; the woodland's wavy cliff and diagonal fall become the two-face escarpment with a vertical fall into a pool; the ridge's own face becomes the 32 px treeline bank.

### 3.2 Driftwood: the harbour and the Headland

```
            col -1                  col 0                   col 1
        +----------------------+----------------------+----------------------+
row  1  |  VALLEY HALT         | CROSSROADS           | THE PARK             |
        +~~~~~~~~~~~~~~~~~~~~~~+---------- = ---------+------- = ------------+
row  2  |  open sea            | DRIFTWOOD     T1/T0  B lane    W1 stile    |
        |  (beyond_sea)        | cottages, fish quay, # THE HEADLAND   T1   |
        |                      | slip, ferry pier,    # fold, lookout tower |
        |                      | breakwater, light    # cliffs, cove stair  |
        +~~~~~~~~~~~~~~~~~~~~~~+~~~~~~~~~~~~~~~~~~~~~~+~~~~~~~~~~~~~~~~~~~~~~+
```

**Size.** Two zones; 16 seconds across, 14 down to the breakwater.

**The idea.** A fishing harbour in a bay where the valley's river reaches the sea. The harbour road comes down from the town on T1, turns along a quay face (32 px dressed stone) and drops by a ramp to the T0 quay. The river's estuary closes the harbour's east side; across it the Headland rises as a cliff plateau. The valley's south-west corner (-1, 2) is open sea, so the world ends in water running off the frame (world-references lesson 7), not in forest.

**Areas.**

- _The harbour_ (busy): cottages up the road on T1, the fish quay on T0 with the market, the slipway and the ferry pier on the west, jetties into the basin, the breakwater running straight south then west (on the grid, no diagonal) with the lighthouse on its rock at the head. Landmark: the lighthouse, seen from the town's south road. Node: the fish quay.
- _The Headland_ (quiet, gated by W1): a sheep pasture on the cliff top inside a drystone wall, the fold with its gate, the lookout tower at the point, benches facing the sea, and a cliff stair down to a small cove. Landmark: the lookout tower, seen from the park's south lawn.

**Height.** T1 the town road and the Headland plateau; T0 the quay and beaches; the Headland's cliffs are 40 px rock faces to the sea, two tiers where the cove stair comes down (rule 8: a long drop in two runs with a landing).

**Attachments and the Headland's one way in.** The harbour joins the town by the road (open land). The coast loop crosses the estuary on a footbridge at the harbour's north-east (about x 280 to 320 of the harbour, landing in the Headland zone's north-west corner), then a lane runs north along the Headland zone's top strip (y 0 to 96) into the park. South of that lane, a continuous drystone wall runs from the estuary's bank to the cliff edge at y about 96 and closes the whole promontory: its west end lands on the estuary bank, its east end on the cliff face, and the **stile** at about (168, 96) is the only way through (W1). The estuary (deep water, no other crossing) closes the Headland's west side; the sea and cliffs close its south and east. The lane, the footbridge and the coast loop stay open with W1 closed.

**Interesting spaces.** The view from the end of the breakwater back at the whole harbour stacked up the hill (a north-facing sightline, the long way of the screen); the cove below the Headland, reached by the cliff stair, with a rock pool and a sea cave mouth (pocket); the ferry leaving the pier toward the isles, which you can see on the horizon from the Headland's lookout before W4 opens.

**The trade.** Fishers (boats out at dawn, catch landed on the quay), the fishmonger at the market, the harbour master, the chandler, the boatwoman (W4), the lighthouse keeper, the shepherd (W1).

| Place               | Makes or does           | Needs                  | Moves by                      | Props, and where                                                                                                                                                  |
| ------------------- | ----------------------- | ---------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Boats and jetties   | fish                    | nets, pots, bait, rope | boat to quay                  | boats moored alongside jetties (bow or side on), jetties ending at a boat, a ladder or a fishing spot, bollards and rings on the quay coping, buoys in the basin  |
| Fish quay           | the market              | ice, crates, salt      | handcart up to the town stall | the fish stall under an awning on the quay, crates of fish in twos and threes, a handcart, an ice house dug into the T1 face behind the quay (a door in the face) |
| Beach and net racks | mended nets             | sun and wind           |                               | net racks on the dry upper beach west of the slip, lobster pots stacked on the quay edge, an upturned boat on the beach, driftwood at the drift line              |
| Chandlery           | rope, lamps, tar, paint | goods from the town    |                               | a chandlery building on the quay by the slipway, coils of rope, a lantern on a bracket, a tar barrel                                                              |
| Slipway             | boat repair             | timber                 |                               | the slip running into the water on the west, the ferry on it while W4 is closed (patched hull, tar pot), a winch at its head                                      |
| Ferry pier          | the ferry to the isles  |                        | ferry                         | a named pier with a ladder, a timetable board, bollards, the ferry moored when W4 is open, crates of island fruit on the pier                                     |
| Harbour master      | the harbour's order     |                        |                               | a hut at the pier's root with a window onto the basin, a bell                                                                                                     |
| Lighthouse          | the light               | oil                    |                               | the lighthouse on its rock at the breakwater's head, a walkway on the breakwater's top                                                                            |
| Cottages            | homes                   | water, firewood        |                               | doors onto the harbour road, back yards with washing lines, chimneys                                                                                              |
| Headland pasture    | wool                    | water for the sheep    |                               | sheep inside the wall, the fold with its gate, a trough, the shepherd's hut by the stile                                                                          |
| Lookout             | the coast watch         |                        |                               | the lookout tower at the point, a bench facing the sea                                                                                                            |

**Props.** _Kept:_ `boat_blue`, `boat_red`, `harbour_ferry`, `sailboat`, `buoy`, `bollard`, `lighthouse` (moved onto its rock), `net_rack`, `lobster_pots`, `upturned_boat`, `driftwood`, `deck_chair`s, `pier_ladder`, `anchor` (placed at the chandlery), `washing_line`, `sheep`, `drystone_*`. _Redrawn:_ `cottage` a to d (eaves and doors to the table), `fish_stall` (counter), `lookout_tower` (door 20 to 32). _New:_ a chandlery, a harbour master's hut, an ice house door in the face, a slipway winch, a timetable board, the stile in two states and the shepherd's hut.

**Kept from today.** The harbour's place, the jetties and the ferry, the lighthouse, the cottages up the road, the sheep field and the lookout tower. **Changed:** the diagonal breakwater runs on the grid; the lighthouse stands on rock at its head, not on the beach; the estuary closes the Headland's west side; the wall with the stile closes its north; (-1, 2) is sea.

### 3.3 Fir Hollow and the Frostline

```
            col -1                  col 0                   col 1
        +----------------------+----------------------+
row -3  |  (high peaks)        | THE HIGH LOOKOUT T5  |  (high peaks)
        |                      | switchback, scope    |
        +----------------------+---------- S ---------+
row -2  | SNOWMELT LAKE  T4    . THE SNOW SADDLE T4   |
        | cirque, frozen fall  . bothy, windsock      |
        +---------- S ---------+-------- W2 col ------+
row -1  | FIR HOLLOW     T3    # THE RIDGE (3.1) T3   |
        | firs, gully trail    W2 (second pine)       |
        +###### escarpment ####+----------------------+
row  0  | THE WOODLAND (3.1)   | THE GARDEN           |
```

**Size.** Four zones beyond the ridge; 43 seconds from the col to the scope.

**The idea.** A small high country reached through one gap above the cabin. Snowmelt Lake lies in a cirque under the peaks; its outflow runs south through Fir Hollow, a sheltered bowl of old firs, and falls over the escarpment into the woodland: the valley's water starts here. The Saddle is the broad pass between the lake and the ridge, with a stone bothy for walkers; a spur climbs from it to the High Lookout, where the whole world is seen.

**Areas.** _Fir Hollow_ (quiet, dense firs at 45 to 60 % crown cover, about 40 trees in clumps of 3 to 7; snow patches growing up the slope; the stream in a gully; landmark: the frozen top of the fall, seen from the lake). _Snowmelt Lake_ (quiet; a rounded-rectangle lake in a cirque, a frozen fall on the back wall, the outflow under a footbridge; landmark: the frozen fall, seen from the saddle). _The Snow Saddle_ (the node: the bothy with smoke, a windsock, the fork; landmark: the windsock and bothy, seen from the col). _The High Lookout_ (the summit: a flagged terrace with the scope and a bench; landmark: the scope platform on its spur, seen from the saddle).

**Height.** T3 the ridge and the hollow; T4 the saddle and the lake; T5 the lookout. Faces are rock (`rock` material) at 32 px; the climb to the lookout is a switchback stair along the spur's face (rule: a stair may run along a face) with two landings. Steep ground that cannot be walked is drawn as buttresses and gullies on the grid, not as blobs.

**Attachments and W2.** The **col** is the gap in the ridge's rock shoulders north of the cabin (x 176 to 232 on the ridge/saddle seam, as today's `RIDGE_COL`). The hollow and the ridge share a seam that is open land today; it becomes a **rock rib** (a 32 px face running north and south on the seam) cut only by the gully trail where the stream runs (about y 360 to 408 on the hollow's east edge). One storm brought down two pines: one across the col, one across the gully trail. **W2 closes both and opens both**: the forester saws both into rounds. With W2 closed, a flood fill from the garden reaches no Frostline zone; with it open, the loop ridge, col, saddle, lake, hollow, gully, ridge returns. The woodland/hollow seam stays closed by the escarpment. The lake and the saddle join by open land along the lake's south shore.

**Interesting spaces.** The **reveal at the col**: the trail climbs between the rock shoulders (a corridor 48 px wide that bends once), and at its top the saddle, the bothy's smoke and the lake's ice open northward. The **world view from the Lookout**: the scope's card names what you see; the regions you have not reached show as silhouettes on the horizon (the city's glow, Cogsworth's airship, the volcano's smoke). _Pocket:_ the ledge behind the frozen fall at the lake's back wall, reached by a narrow shelf.

**The trade.** Wild country: no industry. The bothy keeps walkers warm (a stove pipe, firewood stacked inside the porch, a bench), cairns mark the route on the snow, the forester comes up to clear storm damage, ibex and marmots live here. Props: the `bothy` (_redrawn_: door 23 to 32), `windsock`, `telescope`, `trail_post`, `ibex` (_kept_); cairns, snowy pines, frozen tarn and cotton grass (_kept_); _new:_ two fallen pines in two states, a footbridge over the outflow, a rock rib face.

**Kept from today.** The four zones, their order and ids, the lake's place, the bothy and the scope. **Changed:** the snow and rock blobs become grid-led faces and buttresses; the hollow/ridge seam closes with the rib and the gully trail; the lake becomes a rounded rectangle; the summit zone's lower half becomes the switchback spur instead of open snow.

### 3.4 Cogsworth: junction, hill, canal and terminus

```
            col 0                         col 1
        +-----------------------------+-----------------------------+
row  0  | THE JUNCTION          T1    = GASWORKS HILL        T2     |
        | platform (W3, W5), clock     S airship mast, gasholder,  |
        | tower square, workshops      | lamplighter's yard        |
        +------------ = --------------+------------ S --------------+
row  1  | THE CANAL           T1/T0   B THE TERMINUS         T1     |
        | lock, foundry, narrowboat,  = pump house, atmospheric   |
        | allotments                  | terminus (W7), basin      |
        +-----------------------------+-----------------------------+
```

**Size.** Four zones (two more than today); 16 seconds across, 29 down; one loop.

**The idea.** A railway town that runs on schedules. The valley train and the desert line meet at the junction's platform under the clock tower; coal and iron come in, brass and machines go out. The canal carries coal to the foundry and to the pump house that drives the atmospheric railway to the city. The gasworks on the hill makes the coal gas that lights every lamp and lifts the airship. Steam rises from every pipe.

**Why it grows.** Two zones stacked hold no loop and put the airship mast in the middle of the square (rule 5, rule 12). The hill gives the region its second tier and a home for the gasworks and the mast; the terminus gives the maglev (W7) its own place and a reason for the pump house. Cogsworth is still smaller than a Kanto city.

**Areas.** _The Junction_ (busy; the platform along the north edge with the trains, the clock tower square, workshops in touching rows; landmark: the clock tower, seen from the platform as you step off). _Gasworks Hill_ (quiet, high; the gasholder, the airship at its mast, the lamplighter's yard, a view down over the roofs; landmark: the airship, seen from everywhere in the region). _The Canal_ (working; the lock with its balance beams, the foundry with the pour glowing, the narrowboat at the wharf, the crane, the allotments warmed by waste steam; landmark: the foundry's sawtooth roof and chimney). _The Terminus_ (calm; the brass-and-glass atmospheric terminus, the pump house with its beam engine and stack, the canal basin; landmark: the pump house's stack, seen from the canal bridge).

**Height.** T2 the hill (40 px brick terrace with a coping and railing; the stair street down to the junction); T1 the streets; the canal half a tier down (16 px brick embankment, stairs at both bridge ends, as verticality 4d).

**Attachments.** The junction's platform is the arrival from the valley (W3) and the start of the desert line (W5); the terminus is the maglev to the city (W7). Loop: junction, hill (stair), terminus (stair), canal (bridge), junction.

**Interesting spaces.** Stepping off the train, the clock tower stands square on your axis down the street; the stair street up the hill between workshops; the walk along the towpath under the bridge; _pocket:_ the roof of the signal box (a ladder), from which you see along both lines; _pocket:_ the allotments behind the foundry wall, through a gate.

**The trade.** Tinkerers and smiths, the foundrymen, the boatwoman on the canal, the clockwork gardener, the porter, the clerk (W7), the lamplighter.

| Place                   | Makes                         | Needs                                             | Moves by       | Props, and where                                                                                                                              |
| ----------------------- | ----------------------------- | ------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Foundry                 | castings: gears, rails, pipes | coal, iron ingots (from Sunstone's forge by rail) | canal and rail | the foundry on the canal's wharf, coal heaps at its side, ingot stacks by its door, a crane over the wharf, moulds and gear piles in its yard |
| Workshops               | clocks, automatons, parts     | castings                                          | handcart       | workshops with their doors on the street, benches outside, crates of parts, a gear pile                                                       |
| Gasworks                | coal gas                      | coal                                              | pipes          | the gasholder, a retort house with a stack, pipe runs down the hill face to the street lamps                                                  |
| Airship mast            | the airship                   | gas                                               |                | the mast on the hill with the airship moored, a winch and a gas line from the holder                                                          |
| Canal                   | coal transport                |                                                   | narrowboat     | the lock with gates and beams, the narrowboat at the wharf with coal, a towpath of setts, bollards                                            |
| Pump house and terminus | the atmospheric line          | coal for the beam engine                          |                | the pump house with stack and a coal store fed from the basin, the pipe along the guideway, the terminus with the car                         |
| Allotments              | vegetables                    | warmth (waste steam)                              |                | beds and cloches behind the foundry, the steam pipe under them, the automaton tending them                                                    |
| Station                 | trains                        | water, coal                                       |                | the platform with buffers at both line ends, a water crane and coal stage, a signal box, luggage on trolleys                                  |

**Props.** _Kept:_ `locomotive`, `signal_box`, `foundry`, `canal_crane`, `narrowboat`, `airship_mast`, `automaton`, `cloche`, `gas_lamp`, `coal_cart`, `gear_pile`, `pipe_run`, `steamer_trunk`, `engine_tank`, `tea_kiosk`, `workshop` and frames, `workshop_round`, `warehouse`, `atmos_car`. _Redrawn:_ `clock_tower` (door 25 to 32), `house_slate` and `shop_ashlar` (storeys to 32, doors to 32 x 14), `tube_station` (door 18 to 32; becomes the terminus), `iron_bench` (to 32 long). _New:_ a gasholder and retort house, a pump house with a beam engine, a water crane, the luggage trolley, a sand-caked goods wagon (W5) and a dark terminus (W7) in two states.

**Kept from today.** The junction's square under the clock tower with the platform on its north; the canal with its lock, foundry and allotments. **Changed:** the airship and mast move to the hill; the terminus leaves the canal zone for its own; two zones are added to `LAYOUT` (`hill` at (1, 0), `terminus` at (1, 1)); the canal's embankment drops half a tier.

### 3.5 The Tidebloom Isles

```
            col 0                        col 1
        +----------------------------+----------------------------+
row  0  | THE RAINFOREST      T1     = THE HEADWATERS      T2     |
        | giants, river gorge,       S the falls, crater-rim pool,|
        | footbridge                 | rain shelter               |
        +-- S escarpment, fall ------+----- S terrace ------------+
row  1  | LAGOON LANDING      T0     = BLACK-SAND COVE     T0     |
        | pier (W4), boathouse,      . surf, sea stack, turtles,  |
        | lagoon, fruit sheds        | the sea cave               |
        +----------------------------+----------------------------+
          open sea all round (beyond_sea), islets and the reef off the west
```

**Size.** Four zones; a loop of about 29 seconds round, 43 from pier to pool by the stairs.

**The idea.** A dormant volcanic island: its old crater holds the pool where the river starts; the river falls twice, once off the crater rim and once over the escarpment, and runs through the forest to the sheltered lagoon where the ferry lands. The black-sand cove is the exposed side, where the old lava met the sea. A few people live by the lagoon: they fish, grow fruit and keep the ferry.

**Areas.** _Lagoon Landing_ (the node and the arrival; the pier at the lagoon's mouth, the boathouse, fruit sheds, the lagoon's clear shallows with canoes; landmark: the escarpment's lower fall, seen up the river from the pier). _The Rainforest_ (quiet, enclosed; buttress-rooted giants, tree ferns, the river in a grid-led gorge with a footbridge; landmark: the largest giant, whose crown rises over the escarpment, seen from the landing). _The Headwaters_ (high, open; the crater-rim pool and the upper fall, the rain shelter; landmark: the upper fall). _Black-sand Cove_ (wild; surf, a sea stack with its foam ring, turtles above the tide line; landmark: the sea stack, seen from the terrace stair).

**Height.** T0 the landing and the cove; T1 the rainforest terrace; T2 the headwaters. Faces in `earth` (with grass lips) and `rock` (basalt, columnar on the south faces); four stairs, each at least 48 px wide with cheeks, where the trails meet the faces; the falls drop straight down the faces into pools wider than the river (verticality 4f). The coast is grid-led at the large scale, with organic edge cells (decided 19 Oct).

**Attachments.** The ferry (W4) between Driftwood's pier and the landing's pier is the only way on and off. Loop: landing, rainforest (stair), headwaters (stair), cove (terrace stair), landing (along the shore).

**Interesting spaces.** Arriving: the ferry turns into the lagoon and the island rises ahead (the journey's last frame and the first view on foot agree). _Pocket:_ the sea cave in the cove's basalt arm, a dark mouth with a rock pool inside. _Pocket:_ behind the lower fall, a ledge with ferns. The view from the headwaters south over the forest to the lagoon and the ferry at the pier.

**The trade.** The boatwoman (the ferry), a fruit grower, two fishers, a naturalist who watches the turtles.

| Place          | Makes               | Needs             | Moves by                                  | Props, and where                                                                                                                       |
| -------------- | ------------------- | ----------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Fruit groves   | bananas, breadfruit |                   | crates on the ferry to Driftwood's market | banana and breadfruit groves on the rainforest's lower terrace by the trail, a packing shed at the landing, crates stacked on the pier |
| Lagoon fishers | fish                | canoes, nets      | canoe                                     | outrigger canoes in the shallows and hauled up on the beach, a fish-drying rack on the upper beach, the boathouse with its slip        |
| Water          | fresh water         |                   | pipe                                      | a pipe from the river above the lower fall to a tap and trough at the landing                                                          |
| Turtle watch   |                     |                   |                                           | a low rope fence round the nesting beach above the tide line at the cove, a notice post                                                |
| Walkers        |                     | shelter from rain |                                           | the rain shelter at the headwaters, a bench facing the falls                                                                           |

**Props.** _Kept:_ `jungle_tree`, `tree_fern`, `pandanus`, `banana`, `monstera`, `hibiscus`, `bird_of_paradise`, `black_rock` and `_small`, `canoe`, `crab`, `sea_turtle`, `island_ferry`, `rain_shelter`. _Redrawn:_ `boathouse` (door 15 to 32). _New:_ a packing shed, fruit crates, a drying rack, a water tap and trough, a rope fence. Modest fictional buildings only, no temple or tiki motifs, no invented Indigenous names (I3).

**Kept from today.** The island whole in island coordinates (`isle_zones.island()`), its four zones, the tiers, the river's falls and the loop. **Changed:** the wavy escarpments and trails run on the grid with rounded corners; stairs widen to 48; the pier and packing shed make the landing a node.

### 3.6 Sunstone Reach: the oasis, Dust Gulch and the Scorched Pass

```
            col -1                col 0                 col 1
        +--------------------+--------------------+---------------------+
row -1  |  (dunes)           |  (the mesa)        | HEARTHOLD (3.7)     |
        |                    |                    |                     |
        +--------------------+######## mesa face #+------- W6 ----------+
row  0  | THE OASIS   T0/T1  = DUST GULCH    T1   = THE SCORCHED  T1-T2 |
        | spring pool, dunes,= street, platform   . PASS                |
        | caravan, ruin arch = (W5), mine mouth   . canyon, the chasm   |
        +--------------------+--------------------+---------------------+
                    open dunes south and west (beyond_dunes)
```

**Size.** Three zones; 24 seconds from the oasis to the pass.

**The idea.** A western town at the end of the line from Cogsworth, living off cattle and a mine, short of water. Its creek ran dry when a dune crept over the oasis's outlet, so its water now comes by barrel and pipe from the spring. East of town the sand turns to scrub and then to ash, and a basalt canyon climbs to the edge of a lava chasm, across which Hearthold stands on its rock.

**Areas.** _Dust Gulch_ (busy; one street running east and west from the platform, saloon and store with boardwalks, the corral, the water tower, the mine mouth in the mesa face north of the street; landmark: the water tower, seen from the platform). _The Oasis_ (quiet; sculpted dunes round a hollow with the spring pool, palms and a shaduf, the caravan camp, the half-buried older town with its arch; landmark: the palms over the dune crest, seen from the gulch's west end). _The Scorched Pass_ (a corridor and a reveal; sand to scrub to ash, the canyon between basalt walls that bends once, then the chasm's edge with the long bridge; landmark: the castle's towers, seen over the canyon's head).

**Height.** T0 the oasis hollow; T1 the town and the pass's foot; T2 the canyon's head; T3 the mesa top (not walkable, a sandstone face of 40 px with strata, and the mine mouth cut into it). The pass climbs by a ramp along the canyon wall (1 in 3, rail on the open side).

**Attachments.** The platform (W5) is the arrival from Cogsworth; the line runs in from the west and ends at buffers. The mine cart (S1, a shortcut once W6 is open) leaves from its own bay at the mine mouth, joined to the platform by a dry forecourt, through the mesa to the caldera's cart bay. The chasm bridge (W6) at the pass's north edge is the only way to Hearthold and the fire country. Oasis and gulch are open land along the street and the dry creek.

**Interesting spaces.** The reveal at the canyon's head: you walk 10 seconds between dark walls with only sky to the north, then the walls end and the castle rises across the chasm with lava under the bridge. _Pocket:_ the ruin arch in the oasis's south-west, through which a sunken court with column stumps. _Pocket:_ the mesa ledge path to an old lookout over the street (a ramp along the face).

**The trade.** Cowhands, the saloon keeper, the storekeeper, miners, a caravan trader, the masons at the bridge (W6).

| Place             | Makes                        | Needs                                | Moves by                                   | Props, and where                                                                                                                                               |
| ----------------- | ---------------------------- | ------------------------------------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Corral and cattle | cattle                       | water, hay (by rail from the valley) | rail out from stock pens                   | the corral with a gate onto the street, a trough, hay bales against the barn, stock pens by the platform's east end                                            |
| Mine              | ore                          | timber props, dynamite, water        | ore tubs by cart line to the caldera forge | the mine mouth in the mesa face (a tunnel mouth module), ore tubs on the cart bay's rails, a timber stack, dynamite crates in a shed set apart, a water barrel |
| Water             | drinking water, engine water | the spring                           | pipe and wagon                             | the water crane at the platform piped from the oasis spring, the water tower on the street, the dry well with its windpump still standing, a water wagon       |
| Saloon and store  | rest; supplies               | flour and goods by rail              |                                            | saloon and store on the street with boardwalks (12 px low steps, rails, steps at each door), a hitching rail with a horse, kegs at the saloon's side           |
| Caravan camp      | trade in dates and salt      | water                                | camels                                     | tents by the spring, camels resting, a fire pit, goods under an awning                                                                                         |
| Bridge works      | the span (W6)                | stone                                |                                            | the masons' crane, stacked blocks and a hut at the bridge's south end                                                                                          |

**Props.** _Kept:_ `water_tower`, `windpump`, `dry_well`, the corral pieces, `hitching_rail`, `horse` and `horse_tied`, `trough`, `hay_bale`, `wagon`, `keg`, `tent`, `camel`s, `fire_pit`, `awning`, `palm`s, `papyrus`, `shaduf`, `water_crane`, `water_jar`, `column_stump`s, `sandstone_arch`, `saguaro`s, `prickly_pear`, `desert_scrub`, `tumbleweed`, `cow_skull`, `lizard_rock`, `acacia`, `ore_tub`, `dynamite_crate`, `mine_portal` (set into the mesa face as a mouth). _Redrawn:_ `saloon` and `store` (doors 25 to 32). _New:_ stock pens, a water wagon, a timber stack, the masons' crane and blocks (W6), the sand-caked wagon at Cogsworth (W5, Claude C's side).

**Kept from today.** The gulch's one street from the platform, the oasis's dunes and spring and the buried-outlet story, the walk east to the castle. **Changed:** the dune bands run on the grid at the large scale; the long straight causeway north becomes the canyon and a shorter bridge over the chasm at the zone's north edge; the lava in the pass is the chasm only, crusted at its edges.

### 3.7 Hearthold and the fire country: the castle, the Ember Caldera and Cinder Springs

```
            col 1                       col 2
        +--------------------------+--------------------------+
row -2  | THE EMBER CALDERA   T2   = CINDER SPRINGS   T3-T1   |
        | vent, lava lake, forge,  . travertine terraces,     |
        | cart bay, basalt ring    | bathhouse, hot stream    |
        +------- B postern --------+--------------------------+
row -1  | HEARTHOLD        T3/T4   |  (the volcano's flank)   |
        | gatehouse, bailey, keep, |                          |
        | bell tower, herb garden  |                          |
        +------- W6 chasm bridge --+--------------------------+
row  0  | THE SCORCHED PASS (3.6)  |
```

**Size.** Three zones; 29 seconds from the bridge to the bathhouse.

**The idea.** The volcano's vent feeds a lava lake in the caldera; the lava runs south round the castle's rock as its moat and pours into the chasm under the long bridge, where it crusts. Hearthold keeps hours: its bell rings bedtime. It lives on what comes over the bridge from the gulch, since nothing grows near lava except in its own walled garden. Past the castle's postern the caldera holds the forge that smelts the gulch's ore with the volcano's heat, and beyond it Cinder Springs is where the fire country rests.

**Areas.** _Hearthold_ (the castle; the gatehouse at the bridge's head, the outer bailey with the well-house, stables and store yard, the inner ward one tier up with the keep and the bell tower, the herb garden in a walled corner, the library tower; landmark: the keep with the dragon on it, seen from the pass). _The Ember Caldera_ (working; the forge on solid basalt, the cart bay at the tunnel mouth, the basalt sparring ring, the lava lake under the vent; landmark: the vent's smoke and glow). _Cinder Springs_ (quiet; terraces of milky pools stepping down, the lantern path, the bathhouse of charred cedar, fireweed; landmark: the steam over the top pool, seen from the postern).

**Height.** The chasm and the moat at T0 (lava); the castle rock T3 (outer bailey) and T4 (inner ward, a 32 px stone face with a broad stair); the caldera floor T2 round a lava lake below it; the springs from T3 down to T1 in travertine steps of 12 to 16 px (low steps, each pool's lip a face).

**Attachments.** W6 is the chasm bridge (its middle span missing while closed; `world-unlocks.md` 2.5): the only way from the pass to the castle. The postern bridge north over the moat joins the castle to the caldera. Caldera and springs are open ash. The mine cart (S1) from the gulch lands at the cart bay. With W6 closed nothing past the chasm is reachable on foot, and the cart line is closed too (S1 opens after W6).

**Interesting spaces.** The bridge itself: a long stone span on piers with the lava flowing under it and the castle growing as you cross. The bell at hour's end (presentation only). _Pocket:_ the castle's wall walk, reached by a stair in the outer bailey, looking back over the chasm to the desert. _Pocket:_ the top pool of the springs, reached by a narrow stair past the hottest terrace.

**The trade.** The steward, the garrison at practice, the smith and forge workers, the bath attendant, the dragon (scenery).

| Place         | Makes                        | Needs                                  | Moves by                                                          | Props, and where                                                                                                                           |
| ------------- | ---------------------------- | -------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Castle stores | the castle's life            | food, hay, timber (from the gulch)     | wagon over the bridge                                             | a store yard in the outer bailey with barrels, sacks and hay; stables for the wagon horses; the gatehouse arch wide enough for a cart (44) |
| Castle water  | water                        | rain                                   |                                                                   | the well-house as a cistern head fed by gutters from the keep's roofs (the rock in lava has no ground water)                               |
| Herb garden   | herbs and the kitchen garden | water from the cistern                 |                                                                   | raised beds in the walled corner, a water butt                                                                                             |
| Garrison      | keeping hours, practice      |                                        |                                                                   | training dummies and a weapon rack in the outer bailey, archery butts against the wall, banners at the gate                                |
| Forge         | iron and ingots              | ore from the gulch, heat from the vent | ingots by mine cart back to the gulch and on by rail to Cogsworth | the forge on basalt by the cart bay, ore tubs on the rails, an ingot stack on the bay's platform, a cooling trough, tools on the wall      |
| Springs       | rest                         |                                        |                                                                   | the bathhouse at the bottom terrace, stone lanterns along the path, towels drying on a rail, a bench facing the pools                      |

**Props.** _Kept:_ `keep`, `gatehouse`, `round_tower`, `bell_tower`, `castle_well` (as the cistern head), `herb_bed`, `training_dummy`, `weapon_rack`, `archery_butt`, `banner_pole` and frames, `stone_bench`, `dragon` and frames, every `basalt_*`, `obsidian`, `scree`, `charred_snag`, `fireweed`, `cooling_vent`, `bathhouse`, `stone_lantern`, `ore_tub`. _Redrawn:_ `postern` (door 22 to 32), `forge` (arch 22 to 44), `wall_run` (as wall segments on the grid with corner blocks and a wall walk). _New:_ the bridge's missing span and masons' works in two states (W6), stables and a store yard, gutters and a water butt, an ingot stack.

**Kept from today.** The castle on its rock in a lava moat, both bridges, the caldera's forge and cart bay, the springs' terraces and bathhouse, the dragon. **Changed:** the moat and the castle's outline are rounded rectangles on the grid; the castle gains its inner ward tier; the lava river is a channel of grid runs that falls at the chasm, not a wavy band; the caldera's lava lake sits below its rim.

### 3.8 Neon Harbour and the Skyport

```
            col 0                      col 1                       col 2
        +------------------------+--------------------------+------------------------+
row -2  | THE HEIGHTS      T2    S CENTRAL PLAZA     T1     = THE WATERFRONT  T1/T0 |
        | stair streets, sunken  | the big screen, square   | boardwalk, water taxi  |
        | plaza, subway mouth    |                          |                        |
        +---------- S -----------+------------ = -----------+----------- S ----------+
row -1  | MARKET STREET    T1    = DOWNTOWN            T1   = THE DOCKS       T0     |
        | covered market, stalls | Dave's tower, the spine  | cranes, containers,    |
        |                        | under the elevated line  | the cargo ship         |
        +---------- = -----------+------------ = -----------+---------- # quay ------+
row  0  | OLD NEON        T1/T0  = THE SKYPORT        T0    = THE POINT       T1/T0 |
        | the wet street, the    | maglev (W7), concourse,  | the lighthouse park    |
        | ring court, ramen      | the anchor (W8) offshore |                        |
        +------------------------+--------------------------+------------------------+
              the harbour: the anchor and the elevator's ribbon out in the water, south
```

**Size.** Nine zones, kept; 24 seconds across, 43 down.

**The idea.** A city on a slope above its harbour. The maglev from Cogsworth arrives at the Skyport on reclaimed land by the water (W7). From there one spine, the boulevard under the elevated tram, climbs north through downtown to the central plaza; cross streets run east and west, down to the docks and up stair streets to the Heights. The tallest tower downtown, Doomscroll Dave's, carries the biggest screen and is seen from everywhere, the way the lighthouse is at home. The Skyport is where the noise stops and the way up and out begins.

**Areas and rhythm.** Quiet and busy alternate across the grid: Skyport (calm) next to Old Neon (busy) and the Point (calm); Downtown (loudest) between Market Street (busy) and the Docks (working); the Heights (residential, calm) above Market Street; the Plaza (busy) between the Heights and the Waterfront (calm).

| Area           | Character                                                                                         | Landmark (seen from)                                            |
| -------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| The Skyport    | pale slabs, trees, the concourse and the maglev on its guideway, the pier to the anchor           | the ribbon rising out of the harbour (from all of row 0)        |
| Old Neon       | the original wet street at permanent dusk, ramen and arcade, the ring court                       | the arcade's sign over the street (from the Skyport's drop-off) |
| The Point      | a small park on the rock with the lighthouse, benches facing the sea                              | the lighthouse (from the docks)                                 |
| Market Street  | a covered market a low step below the street, stalls against the facades, lantern strings         | the market's glass roof (from Old Neon)                         |
| Downtown       | towers of three to six storeys and one landmark tower, the spine under the elevated line          | Dave's tower and its screen (from every zone)                   |
| The Docks      | gantry cranes, container stacks, the cargo ship at the quay                                       | the cranes (from the waterfront and the spine)                  |
| The Heights    | terraces of touching houses on 40 px faces, stair streets, the sunken plaza with the subway mouth | the water tank on the top terrace (from the plaza)              |
| Central Plaza  | a rounded-rectangle square with the big screen and a fountain on its axis                         | the big screen (from the spine)                                 |
| The Waterfront | a boardwalk over the water, the water taxi stop, benches                                          | the boardwalk's lamps over the water (from the plaza)           |

**Height.** T0 the Skyport, the docks and the waterfront's boardwalk; T1 the streets; T2 the Heights (a 40 px concrete face with a coping and railing; stair streets 48 to 96 px wide with centre rails). Decks (skybridges) stay decks under the two-level walk (`two-level-walk.md`).

**Attachments.** The maglev (W7) at the Skyport is the arrival. The elevator (W8) leaves from the anchor at the end of the Skyport's pier. Inside the city everything joins by streets and stairs; two loops (the inner loop round downtown; the outer along the waterfront, the docks' road and the Skyport). Proposal S3: a coastal steamer from the waterfront to Driftwood (open question 3).

**Interesting spaces.** The spine's view north from the Skyport (Dave's screen at the top of the street, the long axis of the phone). The sunken plaza and the subway mouth in the Heights (verticality 4d). _Pocket:_ a rooftop garden on the Heights reached by a fire escape. _Pocket:_ the Point's rocks below the lighthouse, where the neon finally stops reflecting. _Pocket:_ a back alley behind Market Street with a cat and a noodle cook on a break.

**The trade.** Street vendors, couriers, dockers, office workers, the noodle cook, the arcade keeper, the clerk at the Skyport, the porter at the anchor (W8). Goods arrive by sea and leave by road; everything runs on power and rain falls on it.

| Place                 | Makes or does  | Needs                              | Moves by                       | Props, and where                                                                                                                                                       |
| --------------------- | -------------- | ---------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Docks                 | unloading      | ships, cranes, power               | gantry crane to stack to truck | the cargo ship at the quay under the cranes, container stacks in rows (rows are right here), trucks at the stack's end, a gatehouse onto the road                      |
| Market                | food and goods | goods from the docks and the isles | truck and handcart             | stalls against the market's facades, crates and handcarts at its service door, bins, litter only where people stop                                                     |
| Food stalls and ramen | food           | water, gas, deliveries             | courier bikes                  | stalls on the pavement with stools, a gas bottle, a bike rack, a delivery bike                                                                                         |
| Towers and offices    | screens        | power                              | cables                         | substation boxes, cables on poles to the facades, AC units on walls with drips, vending machines in pairs at shop fronts                                               |
| Streets               | moving people  |                                    | tram, cars, bikes              | the elevated tram over the spine with stops at its stairs, crossings with signals at junctions, bollards at the pavement's edge, drains in the kerbs (it always rains) |
| Skyport               | departures     |                                    | maglev, elevator               | ticket gates you walk through, departure pylons, luggage bots, the anchor's capsule                                                                                    |

**Props.** _Kept:_ `maglev`, `tether`, `ticket_gates`, `departure_pylon`, `pod_tree`, `sky_bench`, `sky_planter`s, `luggage_bot`, `holo_map`, `flower_kiosk`, `city_gantry_crane`, `city_cargo_ship`, `city_container_stack`s, `containers`, `city_car`s, `city_tram`, `city_tram_stop`, `city_lighthouse`, `city_water_taxi`, `city_crossing_signal`, `city_quay_bollard`, `city_bike_rack`, `city_litter_bin`, `city_street_tree`s, `city_cat`s, `cable_pole`, `cables`, `drone`, `holo_board`, `glass_screen`. _Redrawn:_ every `city_b*` building through the facade composer (storeys 12 to 32, shop storeys 44, doors 32 x 14); `tower_pink`, `tower_cyan`, `tower_amber` (three to six storeys, one landmark tower may rise over a north border); `noodle_stall`; `vending_machine` and `city_vending_box`es (to 30); `city_market_stall`s (counters). _New:_ a substation, AC units with drips, a subway mouth (verticality), trucks, a docks gatehouse, a dark maglev car and a parked capsule in two states (W7, W8).

**Kept from today.** The nine zones, their ids, the Skyport and its pier, the docks' cranes and ship, the old wet street with the ring court. **Changed:** streets of touching buildings instead of blocks on open concrete; the Heights' faces grow to 40 px; one north-south spine and east-west cross streets instead of a uniform road grid; the fountain circle becomes a rounded-rectangle plaza.

### 3.9 Halcyon Station

```
        +--------------------------------------+
        | THE LOUNGE: viewports, Earth below,  |  north: space
        | Lumen above, benches, telescope      |
        +------------ docking spine ----------+
        | SHUTTLE HATCH (W9), cargo, suits     |
        +-----------+--------------+-----------+
        | GALLEY    | THE ATRIUM   | SLEEP BAY |
        | table,tea | pods, water  | pods,     |
        |           | column, ring | lockers   |
        +-----------+--------------+-----------+
        | HYDROPONICS: troughs, grow lights    |
        +--------------------------------------+
        | ARRIVAL HALL: the elevator capsule   |  south: the ribbon down to Neon
        | through the airlock (W8)             |
        +--------------------------------------+
```

**Size.** One zone, kept: a station is a building, and one screen of rooms is enough (Pallet Town is less).

**The idea.** A pressurised station on the elevator's ribbon. You arrive at the bottom (the Earth side) through an airlock, walk up through the rooms people live in, and reach the lounge at the top where the windows show Earth below and Lumen above, and the shuttle's hatch. Every room is a rectangle on the grid with bulkheads and lit doorways; the corridor is the station's spine, north and south.

**The trade.** The station botanist (W9), crew. The station needs air, water, light and power: solar wings outside (seen through the lounge's windows), water recycled through the hydroponics, food grown there, a galley to cook it. Props: _kept:_ `console`, `hydro_trough`s, `garden_pod`s, `aquarium_column`, `sleep_pod`, `lockers`, `galley_table`, `tea_dispenser`, `bookshelf`, `floor_cushions`, `lounge_bench`, `telescope`, `viewport`s, `airlock`, `cargo_crates`. _New:_ suits on racks by the hatch, the covered shuttle and star chart in two states (W9), a water recycler unit by the hydroponics.

**Kept from today.** The rooms (arrival, atrium, sleep bay, galley, lounge, hatch). **Changed:** their order follows the ribbon (arrival at the bottom, hatch and windows at the top), so the zone reads as a climb toward the view.

### 3.10 Lumen

```
        +--------------------------------------+
        | THE PAD on the crater rim (T2):      |  Earth over the rim
        | the shuttle, blast fence, lights     |
        +---------------- S -------------------+
        | THE HABITAT (T1): regolith-covered   |
        | hub, airlock, solar arrays west,     |
        | the ice rig east in the shadowed     |
        | crater                               |
        +--------- the pressure tube, S -------+
        | THE DREAM GROVE (T0, crater floor):  |
        | the glass dome, the moon tree, the   |
        | hammock, dream pools                 |
        +--------------------------------------+
               the moon's plain round it (beyond_regolith), space above
```

**Size.** One zone, kept; the end of the journey is one walk downhill, 14 seconds.

**The idea.** The shuttle lands on the crater's rim. You walk down past the habitat, through the pressure tube, into the dome on the crater floor, where the moon tree glows and the hammock hangs: the deepest rest. The walk down is the reveal: the dome comes into view below the habitat (the portrait camera sees it before you reach it).

**The trade.** Life needs a pressurised, shielded habitat with air, water, light and power (art-faults rule 10): regolith over the habitat for shielding, ice mined in the permanently shadowed crater and piped to the habitat, solar arrays on the sunlit rim, grow lamps in the dome, suits on the rack by the airlock, the old lander as a relic. Props: _kept:_ `shuttle`, `hab_hub`, `airlock_module`, `glass_dome`, `pressure_tube` and `_dock`, `solar_array`s, `ice_rig`, `radiator`, `comm_mast`, `old_lander`, `moon_tree`, `hammock`, `dream_pool`s, `glow_caps`, `grow_lamp`, `moon_rock`s. _New:_ a blast fence and pad lights, a pipe from the ice rig to the habitat.

**Kept from today.** Pad, habitat, tube and dome, top to bottom. **Changed:** the three tiers are explicit faces on the grid with stairs; the crater's rim is a ring face seen from above, the dome sits on its floor.

## 4. Gates: where the ways sit, and the order the world opens

The mechanism (rest or GRASS, one way a day, no loss) is `world-unlocks.md`. This section places its nine ways as world features. Every way stands at a chokepoint between areas, never inside one; every gated area has that chokepoint or a drawn barrier on every way in; with all ways closed, a flood fill from the garden and every open stop reaches nothing behind them (`lib/world-ways.test.ts`).

**Always open (the valley's heart):** the garden, the woodland, the riverside, Crossroads Town, the park, Valley Halt (platform and farm), the ridge and its cabin, Driftwood harbour (quay, jetties, the estuary footbridge and the lane to the park).

| #   | Way                 | Where it stands                                                                                                                                         | Every way in that it closes                                                                                            | Closed (being mended)                                                           | Open                                                          | Seen before it opens                                                                        | Resident             |
| --- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------- |
| W1  | The Headland stile  | the drystone wall across the Headland, about (168, 96) in `headland`                                                                                    | the only gap in a wall from the estuary to the cliff; the estuary and the cliffs close the rest                        | the stile's step broken, a hurdle across it                                     | a new stile, the hurdle against the wall                      | the lookout tower and the sheep over the wall                                               | the shepherd         |
| W2  | The ridge col       | the gap in the rock shoulders on the ridge/saddle seam (x 176 to 232), and the gully trail through the rock rib on the hollow/ridge seam (y 360 to 408) | both ways from the ridge into the Frostline (one storm, two pines); the escarpment closes the hollow from the woodland | a snowy pine across each                                                        | sawn into rounds stacked beside each trail, an axe in a block | the saddle's rock shoulders and the bothy's smoke over them; the hollow's firs over the rib | the forester         |
| W3  | The valley train    | the engine shed at Valley Halt                                                                                                                          | the line to Cogsworth                                                                                                  | the engine in its shed, boiler cold, the signal at danger                       | steam up at the platform, the signal off                      | the line running west into the hills; the journey's window shows Cogsworth's chimneys       | the porter           |
| W4  | The Driftwood ferry | the slipway at Driftwood's west quay                                                                                                                    | the only crossing to the isles                                                                                         | the ferry on the slip, a patched hull, a tar pot                                | afloat at the pier, its flag up                               | the island on the horizon from the Headland's lookout and the breakwater's end              | the boatwoman        |
| W5  | The desert line     | at Cogsworth's platform                                                                                                                                 | the line to Dust Gulch                                                                                                 | a goods wagon caked in sand at the platform, the departure board showing a dune | the wagon unloaded, the board showing a cactus                | heat haze and a mesa from Gasworks Hill (far silhouette)                                    | a tinkerer           |
| W6  | The chasm bridge    | the north edge of the Scorched Pass                                                                                                                     | the only way over the chasm; the mine cart stays closed until after W6 (S1)                                            | the middle span missing, a mason's crane and stacked blocks                     | the span closed, banners on the posts                         | the castle across the chasm (the pass's reveal)                                             | the masons           |
| W7  | The maglev          | the terminus at Cogsworth (the new `terminus` zone)                                                                                                     | the line to Neon Harbour                                                                                               | the terminus dark, the car's glass dusty, the pump house cold                   | lit and humming, the pump house's stack smoking               | the city's glow on the horizon from Gasworks Hill at night                                  | the clerk            |
| W8  | The space elevator  | the anchor at the end of the Skyport's pier                                                                                                             | the only way up                                                                                                        | the capsule parked, the ribbon unlit                                            | the ribbon lit, the capsule cycling                           | the ribbon rising out of sight from every street in row 0                                   | a porter             |
| W9  | The shuttle         | the hatch at the top of Halcyon                                                                                                                         | the only way to Lumen                                                                                                  | the shuttle under a cover, a star chart with a gap                              | the hatch lit, the chart complete                             | Lumen through the lounge's windows                                                          | the station botanist |

**The order.** As `world-unlocks.md` 2.4: W1 to W4 are in reach from the start (the Headland, the Frostline, the train, the ferry); the desert line (W5) and the maglev (W7) come in reach after the train (W3); the chasm bridge (W6) after the desert line; the elevator (W8) after the maglev; the shuttle (W9) after the elevator. This plan agrees, and the world is built to show the next ways: from the heart you see the Headland's tower, the col's pine, the halt's cold engine and the ferry on the slip; from Cogsworth's hill the mesa and the city's glow; from the pass the castle; from every street of the Skyport's row the ribbon; from Halcyon's lounge the moon.

**Shortcuts** (GRASS only, `world-unlocks.md`; presentation or a quicker way, never a reward):

| #   | Shortcut                       | Where                                            | Until it opens                                        |
| --- | ------------------------------ | ------------------------------------------------ | ----------------------------------------------------- |
| S1  | The mine cart                  | Dust Gulch's cart bay to the caldera's, after W6 | you walk over the chasm bridge and through the castle |
| S2  | A rowing boat on the millpond  | the riverside                                    | you walk round the pond                               |
| S3  | The coastal steamer (proposal) | Neon's waterfront to Driftwood, after W7         | you ride back by maglev and train                     |
| S4  | Lanterns on the ridge trail    | the ridge                                        | the trail is dark at night (presentation only)        |

**What the walk grid needs** (Claude A): each way's barrier cells and stand in `lib/world-ways.ts`; the Headland's wall and stile and the hollow's rock rib drawn into the ground and the walk grid even while open (only the barrier prop's cells open); `frames.PORTS` for `hollow/ridge` becomes a span at the gully trail; the `harbour/headland` port becomes the estuary (closed) and `park/headland` the lane (open land) plus the wall with the stile.

## 5. Order of work and who owns what

Ownership follows `coherence-plan.md`, "Who does what". Each step is one PR, drawn on the toolkit, checked at 2x and at phone scale (402 x 874) against this plan, with `world_lint` clean and `npm run verify` and `npm run check:art-repro` passing before it leaves draft. Eastward's level of detail is required (AGENTS.md, Matt 20 Oct): each PR sets its region side by side with the official references at the same character height, meets the counts in `art-style.md`, and says in its description what it compared. Reused props are checked the same way; a kept prop that falls short is redrawn, not kept.

| Step | Lane | Work                                                                                                                                                                                                                                                                                                                                               | Needs                                             |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| P0   | A    | The toolkit lands (`terrace.py`, `scale.py`, the tier map and `zoneTier`, the facade composer, `fore.png`), the gate model (`lib/world-ways.ts`: barrier cells, stands, two-state props), `LAYOUT` changes (Cogsworth's `hill` and `terminus`, the valley's sea corner), `frames.PORTS` for the Headland and the hollow, the world map's new lines | `verticality.md` 4e steps 1 to 3; PR #95 approved |
| P1   | B    | The garden on its raised yard with the gate stair; the redrawn valley props at scale (cottages, station house, bench, stall, lamp, crate, barrel); the valley's new props (engine shed in two states, bakery, pump house, forester's yard, chandlery, harbour master's hut, ice house door, stile in two states, fallen pines in two states)       | P0 (scale table)                                  |
| P2   | E    | The valley heart on the grid: the three terraces and their faces, the water from the woodland's fall to the estuary, the town square, street walls and passage, the riverside's mill step, the halt's yard and farm, the ridge's bank, each trade's props where section 3.1 puts them                                                              | P0, P1                                            |
| P3   | E    | Driftwood: the quay face and ramp, the breakwater on the grid with the lighthouse on its rock, the slipway, the ferry pier, the estuary footbridge and lane, the Headland's wall with W1's stile, the cove stair                                                                                                                                   | P2                                                |
| P4   | A    | The Frostline: the col's corridor and reveal, the rock rib and gully trail (W2's two pines), the lake as a rounded rectangle, the spur's switchback, the Lookout's world view                                                                                                                                                                      | P0                                                |
| P5   | C    | The isles on the grid (escarpments, stairs at 48, falls into pools), the landing's packing shed, pier and tap                                                                                                                                                                                                                                      | P0                                                |
| P6   | D    | Sunstone Reach: the gulch's boardwalks and mesa face with the mine mouth, the pass's canyon and reveal, the chasm bridge in two states (W6)                                                                                                                                                                                                        | P0                                                |
| P7   | C    | Cogsworth in four zones: the hill with the gasworks and the mast, the terminus with the pump house (W7), the canal's embankment, W5's wagon                                                                                                                                                                                                        | P0                                                |
| P8   | D    | Hearthold's two tiers and store yard, the caldera's lava lake and forge, the springs' terraces                                                                                                                                                                                                                                                     | P6                                                |
| P9   | C    | Neon: the spine and cross streets, street walls from the composer, the Heights' 40 px faces and stair streets, the market a step down, W8's capsule                                                                                                                                                                                                | P0, the Heights pilot (verticality 4e step 4)     |
| P10  | D    | Halcyon in its climbing order with W9's hatch; Lumen's three tiers                                                                                                                                                                                                                                                                                 | P0                                                |
| P11  | A    | The ways wired: barriers and stands in the walk, open states, the map's dashed lines; `lib/world-ways.test.ts`                                                                                                                                                                                                                                     | PR #95's store and save (Codex)                   |

The valley comes first because it is home and the first thing every player sees, and because its props are the library the other lanes copy from. Lanes C and D start their regions in parallel as soon as P0 lands; each region's resident who explains its way is added by the lane that owns the region's residents.

## 6. Open questions for Matt

1. **Cogsworth grows from two zones to four** (Gasworks Hill and the Terminus), to give it a loop, a second tier, a place for the airship and one for the maglev. Yes?
2. **Neon keeps nine zones.** The alternative is six (folding the Point into the Skyport and the Waterfront into the Docks), which is closer to a Kanto city and easier to fill. Keep nine?
3. **The coastal steamer (S3)** from Neon's waterfront back to Driftwood would close the network into a loop, and the way home from the screen city would be by sea, back to rest. Add it once W7 is open?
4. **The airship at Cogsworth:** scenery only, or later a line (for example to a mooring mast on Hearthold's keep, or to the sky islands)?
5. **The Frostline's second barrier.** W2 opens two fallen pines from one storm, so the Frostline keeps its loop through the hollow. The alternative is a single chokepoint (the col only) and the hollow reached only from the lake, a dead end. Two pines?
6. **The Headland.** The coast loop now passes outside the Headland (over the estuary footbridge and up the lane to the park), and the stile is the only way onto the promontory. Right?
7. **Secret pockets:** do they each count as a place that leaves a keepsake (the existing mechanic), or only hold a view, a resident or a detail? This plan assumes the second.
8. **Shortcuts back that open from the far side** (a gate or ladder that the companion opens the first time it reaches it from beyond, as in TUNIC) inside regions that are already open: allowed? They would need a small saved state per latch.
9. **One-way drops** (Pokémon's ledges): may the companion hop down a 12 to 16 px step where there is no stair, as a shortcut back? This plan assumes no; every change of height is a stair or a ramp.
10. **Halcyon and Lumen stay one zone each,** each a single walk to the view. Or should Lumen get a second zone outside the dome (the crater rim and the ice field)?
11. **The valley's south-west corner becomes open sea** instead of forest, so the coast runs off the frame past the halt and the harbour. Yes?

## Sources

Developer interviews and official or community-maintained references, read for this plan (20 Oct 2026). Everything about pixels and screen sizes not stated in these is marked as an observation above.

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
- Kill Screen, Hyper Light Drifter's wordless world: https://killscreen.com/building-wordless-world-hyper-light-drifter
- Wikipedia, Moonlighter: https://en.wikipedia.org/wiki/Moonlighter_(video_game)
- Wikipedia, Eastward: https://en.wikipedia.org/wiki/Eastward_(video_game)
- Nintendo, how the developers made and remade Eastward: https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward
- RPGamer, Chained Echoes interview: https://rpgamer.com/2022/11/chained-echoes-interview/

**Gaps.** No developer source gives Stardew's, Eastward's or CrossCode's map sizes in tiles, or walking speeds in a unit we could check; CrossCode's developers' interviews found here say nothing on map structure (its terraces are used from `world-references.md`'s observations only). A Link to the Past's and Minish Cap's region sizes were not found in a source we could read. The Pokémon sizes are exact; converting them by a person's height assumes our adults and theirs are the same yardstick, which is a choice, not a fact.
