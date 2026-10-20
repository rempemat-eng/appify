# Neon Harbour, the delta and the Lull belt

**Owner: Claude C** (lane C). The hand-over brief for this region from the world plan v5.3 (`../world-plan.md`, PR #96). Build from it once Matt approves the plan. P8 also gives you Lullford and Gullwick; they are in this brief. The Lull Road, the Delta Road and the Coast Path are routes (Claude A, P6). The Launch Cape's pad and the rocket are Claude D's (P7); the Skyport and the Cape Road are yours.

All coordinates are world pixels on the 11264 x 6912 px canvas (1 cell = 8 px; one screen = 320 x 576 px; an adult is 25 px; walking is 40 px/s). They come from the v5.3 block-out (`geo52.py`, `stats-v52.json`) and place things to within a cell or two: move a thing to fit the ground, not the ground to fit the number. The crop is `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/neon-harbour-delta.png` (Claude A's scratchpad, not in the repository).

## 1. Footprint

| Part                                        | Box (world px)                  | Size (px)   |
| ------------------------------------------- | ------------------------------- | ----------- |
| the Lull belt and the delta                 | x 8700 to 9450, y 3300 to 5900  | 750 x 2600  |
| Neon Harbour, the Skyport and the Cape Road | x 9450 to 11264, y 3900 to 5900 | 1814 x 2000 |
| Lullford                                    | x 8300 to 8700, y 3950 to 4650  | 400 x 700   |
| Gullwick                                    | x 7650 to 8300, y 4850 to 5450  | 650 x 600   |

The boxes are where this brief's things are counted; the land inside them follows the ground, not the box. Where two boxes touch, the threshold between them (section 3) says who draws what.

## 2. Places and why they are here

| Place             | Kind    | Centre        | Size                           | Why here                                                                                                                 |
| ----------------- | ------- | ------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| Lullford          | town    | (8700, 4300)  | 560 x 420                      | the lowest place the Lull can be bridged: gravel terraces narrow the floodplain and an island takes the piers            |
| Gullwick          | harbour | (7950, 5130)  | 420 x 220                      | a cove on the open coast west of the delta: fish, and a beach to haul boats                                              |
| Neon Harbour      | city    | (10450, 4520) | about 1450 x 1100 with the ria | a deep, sheltered ria clear of the Lull's silt; the falls gave the first crossing, the head of navigation and mill power |
| Launch Cape       | cape    | (10980, 5560) | 480 x 360                      | an exposed headland past the city: rockets go up over open sea, away from people                                         |
| Neon terminus     | stop    | (10650, 4450) |                                | the maglev's city end, in the new town                                                                                   |
| Neon steamer pier | stop    | (10420, 4950) |                                | the coastal steamer to Driftwood (a proposal, after W7)                                                                  |
| Lullford Bridge   | bridge  | (8960, 4310)  |                                | old stone arches resting on a river island, with an iron swing span for the barges (W7)                                  |
| Harbour Bridge    | bridge  | (10300, 4990) |                                | two high arches across the ria, resting on Chapel Islet; tall enough for masts                                           |

**Inside.**

- _Neon Harbour_ (about 1450 x 1100 with the ria, plan 8.5) round a ria east of the delta. The Falls Rock between the Glint's two falls at the ria's head (the first town); the market at the old bridges' east foot; the docks along the ria's east side with the warehouses behind; the Heights as separate terrace blocks on three knolls on the west headland; the canal basin under the Heights where the Lull Cut meets the ria; Chapel Islet under the Harbour Bridge; the Gull Strand and Beacon Isle at the ria's mouth; the new town grown out from the maglev station (blocks of different sizes on a grid turned 14 degrees, towers by the station, a planted boulevard east, a covered arcade north, the station square and Neon Square); the Skyport south of the new town (terminal, aprons, two hangars, three mooring masts).
- _The Lull belt_ between the Cog foot and Lullford: one even channel in six unequal bends, point bars inside, cut banks outside, a fresh oxbow and a silted one, willow carr and water meadows. _The delta_: three arms with mudflats and sandbars, reed beds, the Lull Cut along its east side to the canal basin.
- _Lullford_ (560 x 420): the lowest bridgeable point; the bridge's stone arches rest on a river island with the toll house, with an iron swing span for the barges (W7); the town on the west bank. _Gullwick_ (420 x 220): a fishing cove on the open coast west of the delta.

## 3. Transitions

Each threshold is a place: a threshold object on the route (Claude A draws the object), a mixing band about 1400 px long along the route where both grounds mix, with outliers up to 700 px either way, a landmark seen from the threshold, residents crossing, and an ambience cross-fade of 160 px (4 s). You draw your side of each band.

| Threshold                             | Route      | Sides drawn by      | Mixing band (ground kinds, from side to side)              | Landmark seen                                  | Residents crossing (each way)                                                                                      | Radiates from |
| ------------------------------------- | ---------- | ------------------- | ---------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------- |
| **the Cog foot** (8530, 3060)         | Towpath    | Claude C / Claude C | broadleaf, garden, meadow → meadow, watermeadow, broadleaf | the Narrows gorge (8960, 2750)                 | a barge horse and its bargee on the towpath; coal barges go down; a heron fishes the confluence; anglers walk up   | the Lull      |
| **Lullford Bridge** (8960, 4310)      | Lull Road  | Claude A / Claude C | meadow, watermeadow, field → watermeadow, reeds, garden    | the swing span (8960, 4310)                    | market carts bound for Neon; the toll keeper on the island; egrets in the shallows; barges wait at the swing span  | the Lull      |
| **the canal embankment** (9450, 4680) | Delta Road | Claude C / Claude C | watermeadow, broadleaf, carr → garden, meadow, broadleaf   | the falls and the Harbour Bridge (10100, 4600) | market gardeners take produce in; a lock keeper; reed cutters with bundles come out; gulls follow the canal inland | the city      |

The band's elements cross the line both ways: at least three of each side's grounds, props or residents on the other side (benchmark check 12). The props and residents named in section 5.2 of the plan join the ground kinds here.

## 4. Tiers, and how you go up and down

| Part                    | Tiers walked | Faces            | Stairs on routes | Ramps on routes | Switchback steps |
| ----------------------- | ------------ | ---------------- | ---------------- | --------------- | ---------------- |
| the Lull belt and delta | 2 to 5       | 32 px; up to 96  | 2                | 2               | 0                |
| Neon Harbour            | 2 to 10      | 32 px; up to 288 | 12               | 11              | 0                |

A tier is one 32 px south face (40 px in the city); west and east ends are 5 px side bands; stairs are at least 34 px open; ramps run along a face at 1 in 3; a screen shows at most two full tiers and one low step (`verticality.md`).

- 40 px faces in the city; the Heights in stair streets down the fall line and the Heights funicular (a shortcut).
- The falls at the ria's head, a 288 px drop, with stairs beside them and a gallery behind (a proposal).
- The quays one tier below the streets, reached by ramps; the delta and the belt flat (tiers 2 to 5), crossed on boardwalks and the canal embankment.

## 5. Things to place (section 6.4), with coordinates

None of these gives a reward, a cost or a chore.

**Named things** (18), from each biome's own list:

| Thing                         | Kind     | At            | Route      | Where                    |
| ----------------------------- | -------- | ------------- | ---------- | ------------------------ |
| funicular station             | landmark | (10839, 4866) | Cape Road  | a short way off the path |
| street shrine                 | shrine   | (10806, 5322) | Cape Road  | beside the path          |
| hay barn                      | landmark | (8590, 4281)  | Coast Path | beside the path          |
| fishing stage                 | landmark | (8477, 4607)  | Coast Path | beside the path          |
| heron pools                   | wild     | (8129, 4982)  | Coast Path | beside the path          |
| ferryman's hut                | npc      | (9422, 4256)  | Delta Road | a short way off the path |
| wreck in the reeds            | wreck    | (9364, 4688)  | Delta Road | beside the path          |
| harbour master                | npc      | (9690, 4793)  | Delta Road | beside the path          |
| fishing stage                 | landmark | (8573, 3953)  | Lull Road  | a short way off the path |
| stilt hut                     | npc      | (9027, 4282)  | Lull Road  | beside the path          |
| fish market                   | npc      | (9529, 4287)  | Lull Road  | beside the path          |
| reed hide                     | wild     | (8768, 4352)  | Lull Road  | beside the path          |
| a reed hide over the channels | view     | (8795, 4355)  | Lull Road  | beside the path          |
| a gull rock                   | wild     | (9510, 4385)  | Lull Road  | beside the path          |
| a stair-top view over the ria | view     | (9530, 4446)  | Lull Road  | beside the path          |
| rope walk                     | landmark | (9857, 4454)  | Lull Road  | beside the path          |
| an old harbour crane          | ruin     | (9492, 4498)  | Lull Road  | beside the path          |
| eel traps                     | prop     | (9133, 4567)  | Lull Road  | a short way off the path |

**Secret pockets** (7): a little dead-end path (80 px or more) off the route to a clearing that holds the thing named.

| Holds                                   | Clearing at   | Off the route |
| --------------------------------------- | ------------- | ------------- |
| a view over the land                    | (8283, 5072)  | Coast Path    |
| a story detail: an old grave            | (9799, 4170)  | Lull Road     |
| a resident fishing                      | (9188, 4572)  | Delta Road    |
| a story detail: initials cut in a stone | (9092, 3436)  | Towpath       |
| a view over the land                    | (9340, 3908)  | Lull Road     |
| a bench under a tree                    | (10652, 5548) | Quay Street   |
| a story detail: an old grave            | (10740, 4980) | Cape Road     |

**Markers for the art** (217: 92 interactables, 107 story props, 18 ambient). Along routes, ten a screen in the pattern I S S A I S S I S A; in settlements, eight interactables and eight story props a screen. Each is a slot: draw the named thing, or another of the same type that fits the ground.

- _Cape Road_: I bench (10655, 4960); S cairn (10617, 5058); S tracks (10711, 5044); A cats (10755, 5072); I door (10811, 5114); S cold fire ring (10785, 5210); S marker stone (10881, 5221); I bench (10832, 5307); S cart with a broken wheel (10934, 5316); A cats (10903, 5408); I noticeboard (10997, 5417); S mended fence (10935, 5494)
- _Coast Path_: A hares (7696, 5078); I gate (7758, 5002); S cold fire ring (7789, 5092); S marker stone (7849, 5111); A hares (7911, 5121); I noticeboard (7954, 5032); S cairn (8049, 5053); S tracks (8011, 4963); I gate (8112, 4956); S old boot (8097, 4860); A hares (8190, 4894); S mended fence (8370, 4621); S old boot (8393, 4523); I resident (8475, 4575); S marker stone (8484, 4476); A hares (8578, 4491); I water trough (8541, 4399); S cairn (8638, 4391)
- _Delta Road_: I bench (9209, 4329); S cairn (9172, 4417); S tracks (9272, 4416); A egrets (9263, 4510); I door (9375, 4470); S cold fire ring (9342, 4578); S marker stone (9440, 4589); I bench (9391, 4674); S cart with a broken wheel (9492, 4683); A cats (9477, 4777); I noticeboard (9559, 4751); S mended fence (9572, 4838); S old boot (9668, 4814); A cats (9628, 4921); I bench (9742, 4904); S lost hat (9778, 4928)
- _Gullwick_: S cold fire ring (8024, 4976); S mended fence (7920, 5048); I door (7856, 5064); I gate (7952, 5080); I gate (8008, 5080); I door (8104, 5080); S tracks (7912, 5088); S old boot (7928, 5088); I bench (8088, 5096); S old boot (7824, 5112); S marker stone (7824, 5120); I signpost (8096, 5128); S tracks (7952, 5168); S marker stone (8104, 5176); I noticeboard (8024, 5184); I resident (7832, 5200)
- _Launch Cape_: S lost hat (11048, 5424); I signpost (10848, 5456); S mended fence (10888, 5464); I signpost (10840, 5472); I noticeboard (10920, 5480); I signpost (10960, 5480); S old boot (10832, 5496); S lost hat (11040, 5544); I door (10928, 5560); S cairn (10960, 5592); S marker stone (11128, 5592); I bench (10872, 5616); S lost hat (11088, 5640); I gate (10936, 5656); S marker stone (11072, 5672); I gate (10912, 5712)
- _Lull Road_: A hares (8327, 4215); I resident (8392, 4142); S lost hat (8439, 4229); S cart with a broken wheel (8514, 4166); A hares (8519, 4262); I gate (8620, 4245); S mended fence (8622, 4339); S old boot (8685, 4266); I resident (8767, 4320); S marker stone (8795, 4227); A egrets (8877, 4231); I water trough (8891, 4328); S cairn (8980, 4292); S tracks (9020, 4311); A egrets (9084, 4385); I resident (9102, 4292); S cold fire ring (9178, 4352); S marker stone (9246, 4285); I water trough (9258, 4386); S cart with a broken wheel (9350, 4348); A egrets (9389, 4459); I signpost (9433, 4352); S mended fence (9510, 4409); S old boot (9548, 4314); A cats (9605, 4392); I water trough (9675, 4332); S lost hat (9701, 4432); S cart with a broken wheel (9773, 4366); I signpost (9852, 4445); S tracks (9855, 4308); A cats (9929, 4396)
- _Lullford_: S cold fire ring (8688, 4104); I noticeboard (8576, 4112); I water trough (8608, 4120); S marker stone (8784, 4144); S lost hat (8616, 4184); I signpost (8640, 4200); I water trough (8560, 4208); I bench (8800, 4216); I door (8784, 4232); S lost hat (8720, 4264); S cairn (8632, 4288); S lost hat (8808, 4288); I water trough (8896, 4352); I water trough (8832, 4392); S old boot (8640, 4424); S cold fire ring (8656, 4512)
- _Neon Harbour_: S marker stone (10360, 3920); S marker stone (10744, 3936); I door (10496, 3952); I resident (10536, 3952); S old boot (10456, 3968); S mended fence (10728, 3968); S old boot (10176, 3976); S cairn (10160, 3992); I bench (10808, 4000); S marker stone (9976, 4016); S old boot (10696, 4016); I gate (10088, 4032); I water trough (10192, 4032); I gate (10512, 4048); S mended fence (10464, 4080); I noticeboard (10768, 4104); S cart with a broken wheel (9904, 4112); I door (10744, 4128); I bench (10728, 4136); I signpost (10736, 4136); S cairn (10080, 4152); I signpost (10672, 4152); I water trough (10040, 4160); I water trough (10672, 4160); I water trough (9888, 4176); I gate (9832, 4184); S mended fence (10816, 4184); S cairn (9864, 4216); S mended fence (10008, 4216); I water trough (10400, 4232); S cart with a broken wheel (9888, 4240); I door (10576, 4240); I resident (9856, 4256); S cart with a broken wheel (10104, 4256); I door (10984, 4272); I signpost (10896, 4280); I door (10712, 4288); S cart with a broken wheel (10480, 4328); I water trough (11000, 4328); I gate (11024, 4360); I resident (9864, 4368); I resident (10768, 4368); S old boot (9864, 4376); S old boot (10064, 4392); I gate (10640, 4424); I resident (10752, 4424); I gate (10144, 4432); S lost hat (10944, 4480); I resident (10256, 4488); S mended fence (10344, 4504); I noticeboard (10336, 4512); S cairn (9944, 4520); S mended fence (10992, 4520); S lost hat (10568, 4528); I water trough (10576, 4552); S cart with a broken wheel (10904, 4576); I water trough (10976, 4584); S tracks (11096, 4600); S mended fence (10384, 4648); S cart with a broken wheel (10712, 4648); S lost hat (11024, 4680); I signpost (10992, 4688); S old boot (10576, 4696); S tracks (10248, 4704); I signpost (10392, 4704); S marker stone (10848, 4704); I noticeboard (10936, 4712); I noticeboard (10888, 4736); I door (9944, 4792); I bench (10320, 4800); S mended fence (10624, 4944); S cold fire ring (10264, 4952); I gate (10600, 4952); S cairn (10936, 4952); S marker stone (10440, 4960); I signpost (10648, 4976); I bench (10264, 4992); S cart with a broken wheel (10368, 4992); S lost hat (10288, 5000); I resident (10632, 5008); S mended fence (10648, 5008); S cairn (10856, 5008); S cairn (10648, 5064); S tracks (10656, 5064); S mended fence (10832, 5072); I signpost (10840, 5088)
- _Towpath_: A hares (8416, 3962); I resident (8495, 4018); S lost hat (8459, 4108); S cart with a broken wheel (8549, 4079); A hares (8551, 4178); I gate (8588, 4218)

**Easter-egg spots, reserved** (keep the ground there clear and reachable; nothing is placed yet): bell in the oxbow (9450, 3900); lighthouse keeper's door (10050, 5440).

## 6. Boundaries, in layers

Every edge has three layers, drawn as the land itself (plan 5.5): **the fade** (walkable ground with clumps that thicken outward, 10 to 160 px), **the wall** (the ground's own three blockers in uneven patches, 64 to 180 px deep, then thinning out again over 160 to 400 px), and **what lies beyond** (drawn, never walked, hazier). Never a line, a ribbon or a checker.

| Edge                                  | Fade and wall                                                            | Beyond                                         |
| ------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------- |
| East (beyond the new town)            | gorse and brambles thickening into thicket                               | the moss fens and the Glint coming out of them |
| South (the coast and the ria's mouth) | none: the sea is the edge, with surf; cliffs at the Heights and the cape | the sea and far islands                        |
| North of the belt                     | willow carr and fallen trees thickening into thicket                     | the floodplain woods, then the old forest      |

## 7. Obstacles, side paths and loops

| Obstacle | At           | Route      | How it is passed                                                                   |
| -------- | ------------ | ---------- | ---------------------------------------------------------------------------------- |
| pool     | (9388, 4288) | Lull Road  | side path off the road at a Y about 300 px before, round the far side, back at a Y |
| thicket  | (7910, 4971) | Coast Path | side path off the road at a Y about 300 px before, round the far side, back at a Y |

Rules: at most one loop in any small area (obstacles at least 800 px apart); side paths never cross their own road; no one-way drops (every shortcut a two-way stair, ramp, ladder, stepping stones or a latch that stays open); an obstacle keeps every touch target at least 44 screen px clear.

## 8. Benchmark checks to hold on the drawn art

The block-out passes all 21 checks of `../research/world-benchmark.md` (plan 2.1). The block-out's markers and materials stand in for props, so the drawn art must hold them again. **Checks 1 and 9 above all:**

- **1. Density.** Each route screen 2 to 3 interactables and 3 to 5 story props; each settlement screen 6 to 10 of each. Here: about 8 screens of route and the settlements in section 2, so at least 16 interactables and 24 story props on the routes, plus 6 of each per settlement screen.
- **9. No more than three identical props in a row**; tree walls mix three or more species and sizes. Count it on the drawn wall, hedge, fence, crop row and tree line, not on the block-out.
- 2. No stretch of walked path longer than 200 px (5 s) without something to notice.
- 3. A landmark every 1 to 2 screens of route, visible from the screen before.
- 4. Each major biome: 3 named places plus 1 per 6 screens, 3 secret pockets, a viewpoint, a camp or hut, a ruin or story site, 2 local wildlife kinds, a water feature.
- 5. No secret or decoration gives a reward, cost or chore.
- 6 to 8. No invisible walls; every outer border at least 64 px deep in two or three strata; no straight border line longer than 96 px without a jog of 8 px or more.
- 10 and 11. Every screen-length of border shows something beyond; each region shows a place seen but not yet reached, reached later.
- 12 to 15. Each threshold: a mixing band of at least one screen, a threshold object, three elements crossing each way, the next landmark hidden until a crest or bend and then seen at least a screen before arrival, a 3 s cross-fade, a source it radiates from.
- 16 to 21. The main path bends or meets an obstacle every 200 to 300 px, with no straight run over 240 px; path width 24 to 64 px; side paths at least one per two screens; a loop in the region; every dead end longer than 80 px ends in a view, resident, bench or story detail; no one-way drops; every tier change a stair (34 px or wider) or a ramp.
- And the house bar: Eastward's level of detail at the same character height (`../art-style.md`), on the house palette (`house-style.md`, #121), compared side by side in the PR.

## 9. Kits to use

- **house kits** (#121): Neon shopfronts and facades for the new town; the valley cottages' stone variants for the Falls Rock, Lullford and Gullwick where the old town is stone.
- **river_kit** (#133): `river` for the belt (cut banks on the outside of each bend, point bars inside, riffles on the crossings), `canal` for the Lull Cut and the Delta Road's towpath, reeds and marginals for the delta, `ford` where the belt's farm tracks cross the backwaters.
- The terrace toolkit (#90) for the Heights' terrace blocks and the falls.

The kits are on open PRs and land on `main` separately; until then, build against their branches and say which head you used.

## 10. Today's zones: replaced or kept

| Zone today | Becomes      | Where and what                                                                                                                    |
| ---------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| market     | kept, placed | the market at the old bridges' east foot (a 352 x 248 plaza)                                                                      |
| docks      | kept, placed | the docks along the ria's east side, with the cranes and the ship                                                                 |
| waterfront | replaced     | the old town's waterfront on the Falls Rock: warehouses, cranes, the fish market; the old wet street                              |
| heights    | replaced     | the Heights as separate terrace blocks on three knolls                                                                            |
| skyport    | kept, placed | the Skyport: a field with the terminal, aprons, two hangars and three mooring masts                                               |
| neon       | kept, placed | the neon new town's main street, with the court (the sparring ring)                                                               |
| downtown   | replaced     | the new town's blocks round the maglev terminus and the station square                                                            |
| plaza      | replaced     | Neon Square, off the boulevard                                                                                                    |
| point      | replaced     | the Gull Strand and the Beacon Causeway to Beacon Isle at the ria's mouth                                                         |
| (none)     | new ground   | the Falls Rock, the Harbour Bridge and Chapel Islet, the canal basin, the Lull belt, the delta, Lullford and its bridge, Gullwick |

Places keep their ids where the game uses them (mission places, stops, rings in `lib/world-places.ts`), so saves and missions carry over; their stands move with them.
