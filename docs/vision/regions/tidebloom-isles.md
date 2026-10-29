# The Tidebloom Isles and the Shell Bar

**Owner: Claude C** (lane C). The hand-over brief for this region from the world plan v5.3 (`../world-plan.md`, PR #96). Build from it once Matt approves the plan. Only the main isle is walked. The Shell Bar is the walk from the Headland's tip to the main isle (W4); Claude E draws the Headland it leaves from.

All coordinates are world pixels on the 11264 x 6912 px canvas (1 cell = 8 px; one screen = 320 x 576 px; an adult is 25 px; walking is 40 px/s). They come from the v5.3 block-out (`geo52.py`, `stats-v52.json`) and place things to within a cell or two: move a thing to fit the ground, not the ground to fit the number. The crop is `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/tidebloom-isles.png` (Claude A's scratchpad, not in the repository).

## 1. Footprint

| Part                                    | Box (world px)                 | Size (px)   |
| --------------------------------------- | ------------------------------ | ----------- |
| the isles, the lagoon and the Shell Bar | x 3700 to 9800, y 5800 to 6912 | 6100 x 1112 |

The boxes are where this brief's things are counted; the land inside them follows the ground, not the box. Where two boxes touch, the threshold between them (section 3) says who draws what.

## 2. Places and why they are here

| Place          | Kind   | Centre       | Size                             | Why here                                                                 |
| -------------- | ------ | ------------ | -------------------------------- | ------------------------------------------------------------------------ |
| Lagoon Landing | hamlet | (6560, 6200) | the isle 704 x 1152 with its sea | the main isle's lagoon: a drowned crater of the old arc, sheltered water |
| Lagoon pier    | stop   | (6480, 6150) |                                  | the ferry from Driftwood (W4)                                            |

**Inside.**

- _The main isle_ (704 x 1152 with its sea, plan 8.4): the headwaters (T2) in the north-east with the crater pool and the upper fall; the rainforest (T1) across the north; Lagoon Landing (T0) in the south-west round the lagoon and the pier; Black-sand Cove (T0) in the south-east with the basalt arm, the sea stack and the cave. From the pier: the boathouse 5 s, the lower fall 10, the turtle beach 16, the sea cave 18, the giant tree 20, the upper fall and the rain shelter 27, the crater pool 28.
- _The lagoon_ is a drowned crater breached to the sea on the south. _The other isles_ (drawn, not walked): about (5250, 6250), (4050, 6120), (7850, 6450), (8700, 6650), (4650, 6650) and (9600, 6500); the Shell Bar's islet at about (6880, 5900).
- _The Shell Bar_: a sandbar from the Headland's tip by way of an islet to the main isle (W4), with tide pools and the wreck (an egg spot).

## 3. Transitions

Each threshold is a place: a threshold object on the route (Claude A draws the object), a mixing band about 1400 px long along the route where both grounds mix, with outliers up to 700 px either way, a landmark seen from the threshold, residents crossing, and an ambience cross-fade of 160 px (4 s). You draw your side of each band.

| Threshold                      | Route     | Sides drawn by      | Mixing band (ground kinds, from side to side) | Landmark seen          | Residents crossing (each way)                                                     | Radiates from |
| ------------------------------ | --------- | ------------------- | --------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------- | ------------- |
| **the Shell Bar** (6900, 5900) | Shell Bar | Claude E / Claude C | sand, meadow, field → meadow, sand, field2    | the wreck (6930, 5870) | cocklers walk out at low tide; seals haul out on the bar; terns nest on the islet | the sea       |

The band's elements cross the line both ways: at least three of each side's grounds, props or residents on the other side (benchmark check 12). The props and residents named in section 5.2 of the plan join the ground kinds here.

## 4. Tiers, and how you go up and down

| Part                    | Tiers walked | Faces            | Stairs on routes | Ramps on routes | Switchback steps |
| ----------------------- | ------------ | ---------------- | ---------------- | --------------- | ---------------- |
| the coast and the isles | 2 to 5       | 96 px; up to 192 | 0                | 3               | 0                |

A tier is one 32 px south face (40 px in the city); west and east ends are 5 px side bands; stairs are at least 34 px open; ramps run along a face at 1 in 3; a screen shows at most two full tiers and one low step (`verticality.md`).

- The main isle: the headwaters (T2), the rainforest (T1), Lagoon Landing and Black-sand Cove (T0); stairs of 48 px.
- Cliffs of 96 to 192 px against beaches at sea level; slipways and ramps at the landings.

## 5. Things to place (section 6.4), with coordinates

None of these gives a reward, a cost or a chore.

**The main isle's places** (plan 8.4). The block-out placed things only along the walked routes, so it put none inside the isle; the isle keeps its own canvas (`isle_zones.island()`) and its places, by walk time from the pier: the boathouse 5 s, the lower fall 10, the turtle beach 16, the sea cave 18, the giant tree 20, the upper fall and the rain shelter 27, the crater pool 28. They hold check 4 with the coast's tide pools, seal rocks and sea cave. One fit to settle: the block-out drew the main isle as an oval about 1120 x 660 px round the lagoon (centre about (6650, 6380), the pier at about (6480, 6150)), while the decided island is 704 x 1152 px with its sea. Keep the island as decided; Claude A fits the coast to it in the geography chunk (P1).

**Named things** (0), from each biome's own list:

(none on the walked routes in this footprint)

**Secret pockets** (2): a little dead-end path (80 px or more) off the route to a clearing that holds the thing named.

| Holds                         | Clearing at  | Off the route |
| ----------------------------- | ------------ | ------------- |
| a story detail: a buried bell | (6444, 6412) | Shell Bar     |
| a view down a gorge           | (6924, 6372) | Shell Bar     |

The two pockets above came from the block-out's coast; inside the isle, give it three of its own (check 4), for example a view from the crater pool's rim over the lagoon, a bench under the giant tree and a story detail in the sea cave. The isle's own loop (8.4) is its loop for check 18.

**Markers for the art** (23: 10 interactables, 11 story props, 2 ambient). Along routes, ten a screen in the pattern I S S A I S S I S A; in settlements, eight interactables and eight story props a screen. Each is a slot: draw the named thing, or another of the same type that fits the ground.

- _Lagoon Landing_: S old boot (6472, 6096); S cold fire ring (6584, 6104); I resident (6488, 6120); S lost hat (6544, 6120); S cold fire ring (6648, 6128); I resident (6512, 6144); S marker stone (6552, 6160); I bench (6456, 6176); S cairn (6440, 6208); I water trough (6680, 6208); I noticeboard (6696, 6216); I resident (6552, 6232); I water trough (6568, 6264); I door (6672, 6264); S cairn (6464, 6280); S mended fence (6480, 6280)
- _Shell Bar_: A terns (6951, 5828); I door (6906, 5855); S cold fire ring (6871, 5894); S marker stone (6826, 5927); I bench (6827, 6023); S cart with a broken wheel (6790, 6056); A terns (6696, 6033)

**Easter-egg spots, reserved** (keep the ground there clear and reachable; nothing is placed yet): wreck on the Shell Bar (6930, 5870).

## 6. Boundaries, in layers

Every edge has three layers, drawn as the land itself (plan 5.5): **the fade** (walkable ground with clumps that thicken outward, 10 to 160 px), **the wall** (the ground's own three blockers in uneven patches, 64 to 180 px deep, then thinning out again over 160 to 400 px), and **what lies beyond** (drawn, never walked, hazier). Never a line, a ribbon or a checker.

| Edge      | Fade and wall                                                                           | Beyond                                                 |
| --------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| All round | none: the sea is the edge, with surf on every shore; rocks and driftwood on the beaches | far islands on the horizon (south-west and south-east) |

## 7. Obstacles, side paths and loops

(none in this footprint; see the routes brief)

Rules: at most one loop in any small area (obstacles at least 800 px apart); side paths never cross their own road; no one-way drops (every shortcut a two-way stair, ramp, ladder, stepping stones or a latch that stays open); an obstacle keeps every touch target at least 44 screen px clear.

## 8. Benchmark checks to hold on the drawn art

The block-out passes all 21 checks of `../research/world-benchmark.md` (plan 2.1). The block-out's markers and materials stand in for props, so the drawn art must hold them again. **Checks 1 and 9 above all:**

- **1. Density.** Each route screen 2 to 3 interactables and 3 to 5 story props; each settlement screen 6 to 10 of each. Here: about 1 screens of route and the settlements in section 2, so at least 1 interactables and 2 story props on the routes, plus 6 of each per settlement screen.
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

- **house kits** (#121): the valley and isles cottages for Lagoon Landing's packing shed, the boathouse and the rain shelter.
- **river_kit** (#133): `river`, `riffles` and `flow_frames` for the isle's stream and its falls; reeds at the lagoon's back.
- **dry_kit** (#137): `columns` and `boulders` (basalt with lichen) for Black-sand Cove's basalt arm and sea stack.

The kits are on open PRs and land on `main` separately; until then, build against their branches and say which head you used.

## 10. Today's zones: replaced or kept

| Zone today | Becomes    | Where and what                                                                  |
| ---------- | ---------- | ------------------------------------------------------------------------------- |
| rainforest | kept       | the rainforest (T1) across the north of the main isle                           |
| headwaters | kept       | the headwaters (T2) with the crater pool and the upper fall                     |
| landing    | kept       | Lagoon Landing (T0) round the lagoon, the pier and the packing shed as its node |
| cove       | kept       | Black-sand Cove (T0) with the basalt arm, the sea stack and the cave            |
| (none)     | new ground | the Shell Bar and its islet, the seven other isles (drawn, mostly not walked)   |

Places keep their ids where the game uses them (mission places, stops, rings in `lib/world-places.ts`), so saves and missions carry over; their stands move with them.

## v55 overview: proposals for lane C (27 Oct)

The continent overview v55 (`../research/blockout/README.md`, "v55"; Matt's brief of 27 Oct). These are proposals; this brief is unchanged until the lane adopts them.

- **Coordinates**: the isles move 256 px south with the coast band's stretch (`geo55.P`): Lagoon Landing to (6560, 6456), the Lagoon pier to (6480, 6406).
- **Lagoon Landing, medium (18 buildings)**, organised round the lagoon (the East Strand added on its east shore): boathouses and stilt houses on the lagoon front, Net Row with the net and sail lofts, Pier Lane to the ferry pier, Bar Lane to the Shell Bar, and the boatyard.
