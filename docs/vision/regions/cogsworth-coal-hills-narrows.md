# Cogsworth, the coal hills and the Narrows

**Owner: Claude H** (lane H, from Claude C on 21 Oct). The hand-over brief for this region from the world plan v5.3 (`../world-plan.md`, PR #96). Build from it once Matt approves the plan. P8 also gives you Fernhollow, which sits at the edge of the Fern hills inside this footprint. The High Fells, the Foothill Road and the Towpath are routes (Claude A, P6).

**Lanes changed on 21 Oct** (Matt: "can you speed up the world building a bit"; `../coherence-plan.md`, "Who does what"). Where this brief names Claude E for the Frostline, the Col, the massif or the Brackens, read Claude F; Claude C for Cogsworth, the coal hills, the Narrows or Fernhollow, read Claude H; Claude C for Neon Harbour, the Heights, the docks, the delta, the Lull belt, Lullford, Gullwick, the Skyport or the Cape Road, read Claude I; Claude A for the routes' chunks, the threshold objects or the world's edges, read Claude G.

All coordinates are world pixels on the 11264 x 6912 px canvas (1 cell = 8 px; one screen = 320 x 576 px; an adult is 25 px; walking is 40 px/s). They come from the v5.3 block-out (`geo52.py`, `stats-v52.json`) and place things to within a cell or two: move a thing to fit the ground, not the ground to fit the number. The crop is `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/cogsworth-coal-hills-narrows.png` (Claude A's scratchpad, not in the repository).

## 1. Footprint

| Part                                                  | Box (world px)                 | Size (px)   |
| ----------------------------------------------------- | ------------------------------ | ----------- |
| Cogsworth, the coal hills, the Narrows and Fernhollow | x 7000 to 9300, y 1700 to 3300 | 2300 x 1600 |

The boxes are where this brief's things are counted; the land inside them follows the ground, not the box. Where two boxes touch, the threshold between them (section 3) says who draws what.

## 2. Places and why they are here

| Place              | Kind   | Centre       | Size                | Why here                                                                                                       |
| ------------------ | ------ | ------------ | ------------------- | -------------------------------------------------------------------------------------------------------------- |
| Fernhollow         | hamlet | (7150, 3080) | 320 x 240           | timber in the wet woods of the Fern hills, the valley's east wall                                              |
| Cogsworth          | town   | (7980, 2450) | 704 x 960 (decided) | coal and iron in the coal hills, the fast Cog for power (the Millrace), and the valley floor for a railway out |
| Cogsworth platform | stop   | (7960, 2420) |                     | the valley train and the desert line, both entering from the west                                              |
| Cogsworth terminus | stop   | (8240, 2790) |                     | the maglev east over the Narrows Viaduct to Neon (W7)                                                          |
| Narrows Viaduct    | bridge | (9030, 2330) |                     | the railway (now the maglev) on tall piers over the gorge                                                      |

**Inside.**

- _Cogsworth_ (704 x 960, plan 8.3): on the Cog's east bank, the Millrace through the mills. The platform along the north edge with both lines from the west; the clock-tower square in front of it; workshop rows west; Gasworks Hill one tier up east with the airship mast; the canal half a tier down across the middle with its lock; the foundry and allotments south-west; the maglev terminus and the pump house south-east, where the maglev leaves east. From the platform: the clock tower 8 s, the gasholder 10, the mast 13, the lock 18, the foundry 22, the allotments 23, the pump house 26, the terminus 30.
- _The coal hills_: rounded hills with 32 px benches under dark conifers; spoil heaps at about (7700, 2300), (8150, 2350), (8250, 2650), (7700, 2150) and (8400, 2300); pit heads, charcoal camps and rail ruins along the roads.
- _The Narrows_: the Lull's gorge through the hills, with rapids, and the Narrows Viaduct carrying the maglev over it at about (9030, 2330). The Cog joins the Lull at the gorge's foot (the Cog foot).
- _Fernhollow_ (320 x 240): a woodcutters' hamlet in the wet woods on the Fern hills' western slope, on the Foothill Road: a sawpit, log stacks, a few timber cottages.

## 3. Transitions

Each threshold is a place: a threshold object on the route (Claude A draws the object), a mixing band about 1400 px long along the route where both grounds mix, with outliers up to 700 px either way, a landmark seen from the threshold, residents crossing, and an ambience cross-fade of 160 px (4 s). You draw your side of each band.

| Threshold                             | Route         | Sides drawn by      | Mixing band (ground kinds, from side to side)              | Landmark seen                     | Residents crossing (each way)                                                                                           | Radiates from  |
| ------------------------------------- | ------------- | ------------------- | ---------------------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------- |
| **the Millrace cutting** (7650, 2740) | Foothill Road | Claude A / Claude C | broadleaf, garden, meadow → garden, meadow, broadleaf      | Cogsworth's chimneys (7980, 2450) | miners walk up to the pits; a coal cart comes down; woodcutters from Fernhollow with a timber wagon; crows over the cut | the coal seams |
| **the Cog foot** (8530, 3060)         | Towpath       | Claude C / Claude C | broadleaf, garden, meadow → meadow, watermeadow, broadleaf | the Narrows gorge (8960, 2750)    | a barge horse and its bargee on the towpath; coal barges go down; a heron fishes the confluence; anglers walk up        | the Lull       |

The band's elements cross the line both ways: at least three of each side's grounds, props or residents on the other side (benchmark check 12). The props and residents named in section 5.2 of the plan join the ground kinds here.

## 4. Tiers, and how you go up and down

| Part                           | Tiers walked | Faces           | Stairs on routes | Ramps on routes | Switchback steps |
| ------------------------------ | ------------ | --------------- | ---------------- | --------------- | ---------------- |
| the coal hills and the Narrows | 3 to 18      | 32 px; up to 32 | 12               | 10              | 0                |

A tier is one 32 px south face (40 px in the city); west and east ends are 5 px side bands; stairs are at least 34 px open; ramps run along a face at 1 in 3; a screen shows at most two full tiers and one low step (`verticality.md`).

- 32 px benches on the coal hills, with stairs and ramps on the Foothill Road and the Towpath.
- Cogsworth: Gasworks Hill one tier up east of the square; the canal half a tier down across the middle.
- The Narrows: gorge walls with the river at the bottom; the viaduct over it; a towpath ledge and the Narrows lift down to the river are proposals.

## 5. Things to place (section 6.4), with coordinates

None of these gives a reward, a cost or a chore.

**Named things** (14), from each biome's own list:

| Thing                         | Kind     | At           | Route         | Where                    |
| ----------------------------- | -------- | ------------ | ------------- | ------------------------ |
| charcoal burners' camp        | camp     | (7687, 2585) | Foothill Road | beside the path          |
| collapsed adit                | cave     | (7805, 2948) | Foothill Road | a short way off the path |
| pit head                      | landmark | (7295, 2970) | Foothill Road | beside the path          |
| windmill                      | landmark | (7107, 3208) | Foothill Road | beside the path          |
| a terrace edge over the loops | view     | (7244, 3222) | Foothill Road | beside the path          |
| an eel-catcher's camp         | camp     | (7206, 3274) | Foothill Road | beside the path          |
| a tor                         | landmark | (7079, 1793) | High Fells    | beside the path          |
| fallen climber's camp         | camp     | (7207, 1989) | High Fells    | a short way off the path |
| echo cave                     | cave     | (7645, 2078) | High Fells    | beside the path          |
| cairn                         | landmark | (7957, 2094) | High Fells    | a short way off the path |
| a crow roost in a dead pine   | wild     | (7915, 2392) | High Fells    | beside the path          |
| rail ruin                     | ruin     | (8279, 2482) | Towpath       | a short way off the path |
| tram tipple                   | landmark | (8228, 2932) | Towpath       | beside the path          |
| lookout over the Narrows      | view     | (8588, 3007) | Towpath       | beside the path          |

**Secret pockets** (5): a little dead-end path (80 px or more) off the route to a clearing that holds the thing named.

| Holds                         | Clearing at  | Off the route |
| ----------------------------- | ------------ | ------------- |
| a story detail: a buried bell | (7634, 1792) | High Fells    |
| a view down a gorge           | (7172, 1964) | High Fells    |
| a resident fishing            | (7708, 3083) | Foothill Road |
| a story detail: a buried bell | (7212, 2780) | Foothill Road |
| a view down a gorge           | (8012, 2908) | Towpath       |

**Markers for the art** (91: 34 interactables, 46 story props, 11 ambient). Along routes, ten a screen in the pattern I S S A I S S I S A; in settlements, eight interactables and eight story props a screen. Each is a slot: draw the named thing, or another of the same type that fits the ground.

- _Cogsworth_: I noticeboard (7976, 2200); S tracks (7736, 2232); I door (8160, 2232); S mended fence (8160, 2232); I water trough (7736, 2264); S cairn (8096, 2272); S lost hat (8056, 2312); I door (8208, 2328); S tracks (7920, 2336); I noticeboard (7904, 2344); I water trough (8040, 2344); S old boot (8056, 2392); S lost hat (8272, 2392); I signpost (8304, 2416); S tracks (8264, 2584); S cairn (7832, 2640); I bench (7840, 2640); I bench (7856, 2720)
- _Fernhollow_: I noticeboard (7184, 2912); S marker stone (7168, 2920); S cart with a broken wheel (7216, 2944); I signpost (7208, 2976); S marker stone (7224, 3000); I door (7232, 3000); S cairn (7304, 3032); I gate (7184, 3040); S mended fence (7248, 3048); S tracks (7304, 3048); I water trough (7240, 3072); I gate (7200, 3088); S marker stone (7224, 3088); I water trough (7288, 3112); S marker stone (7200, 3168); I gate (7032, 3176)
- _Foothill Road_: S cold fire ring (7005, 3203); S marker stone (7052, 3139); I bench (7107, 3206); S cart with a broken wheel (7162, 3122); A hares (7242, 3173); I noticeboard (7230, 3072); S mended fence (7326, 3086); S old boot (7321, 2988); A moths (7409, 3031); I bench (7437, 2937); S lost hat (7525, 2982); S cart with a broken wheel (7503, 2890); I noticeboard (7598, 2872); S tracks (7551, 2793); A moths (7631, 2770); I gate (7616, 2672); S cold fire ring (7713, 2702); S marker stone (7702, 2587); A moths (7816, 2651); I noticeboard (7776, 2541); S cairn (7817, 2487); S tracks (7881, 2445)
- _High Fells_: S lost hat (7125, 1710); I noticeboard (7238, 1771); A choughs (7344, 1788); I gate (7429, 1744); S cold fire ring (7412, 1843); S marker stone (7457, 1877); A choughs (7533, 1889); I noticeboard (7579, 1898); S cairn (7599, 1972); S tracks (7664, 1985); I gate (7668, 2059); S old boot (7685, 2094); A choughs (7772, 2133); I resident (7778, 2187); S lost hat (7792, 2234); S cart with a broken wheel (7829, 2248); A moths (7818, 2379); I gate (7918, 2328)
- _Towpath_: I bench (8080, 2585); S cairn (8162, 2616); S tracks (8145, 2656); A moths (8196, 2686); I door (8246, 2722); S cold fire ring (8196, 2825); S marker stone (8234, 2867); I bench (8237, 2928); S cart with a broken wheel (8352, 2923); A moths (8363, 3020); I noticeboard (8433, 2952); S mended fence (8504, 2962); S old boot (8585, 3032); A moths (8481, 3082); I bench (8528, 3164); S lost hat (8432, 3189); S cart with a broken wheel (8501, 3261)

**Easter-egg spots, reserved** (keep the ground there clear and reachable; nothing is placed yet): hermit's tarn (7050, 1720).

## 6. Boundaries, in layers

Every edge has three layers, drawn as the land itself (plan 5.5): **the fade** (walkable ground with clumps that thicken outward, 10 to 160 px), **the wall** (the ground's own three blockers in uneven patches, 64 to 180 px deep, then thinning out again over 160 to 400 px), and **what lies beyond** (drawn, never walked, hazier). Never a line, a ribbon or a checker.

| Edge                                                    | Fade and wall                                                  | Beyond                                               |
| ------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------- |
| North (the massif above the coal hills)                 | scree and boulders thickening into crags                       | the massif and the upper Lull's gorge going on north |
| East (beyond the Narrows)                               | bramble and fallen trees thickening into thicket and old trees | the old forest, then the moss fens                   |
| Interior (between the Foothill Road and the High Fells) | thicket and felled timber in the coal forest                   | dark conifers and spoil heaps, hazier                |

## 7. Obstacles, side paths and loops

| Obstacle     | At           | Route           | How it is passed                                                                                                |
| ------------ | ------------ | --------------- | --------------------------------------------------------------------------------------------------------------- |
| thicket      | (7120, 3276) | Foothill Road   | side path off the road at a Y about 300 px before, round the far side, back at a Y                              |
| thicket      | (7404, 1969) | High Fells      | side path off the road at a Y about 300 px before, round the far side, back at a Y                              |
| a spoil heap | (8150, 2350) | a loop round it | an irregular outline; the path closer on one side; joins the road at a Y (or where the road runs into the loop) |

Rules: at most one loop in any small area (obstacles at least 800 px apart); side paths never cross their own road; no one-way drops (every shortcut a two-way stair, ramp, ladder, stepping stones or a latch that stays open); an obstacle keeps every touch target at least 44 screen px clear.

## 8. Benchmark checks to hold on the drawn art

The block-out passes all 21 checks of `../research/world-benchmark.md` (plan 2.1). The block-out's markers and materials stand in for props, so the drawn art must hold them again. **Checks 1 and 9 above all:**

- **1. Density.** Each route screen 2 to 3 interactables and 3 to 5 story props; each settlement screen 6 to 10 of each. Here: about 6 screens of route and the settlements in section 2, so at least 11 interactables and 17 story props on the routes, plus 6 of each per settlement screen.
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

- **house kits** (#121): Cogsworth brick and iron (true stretcher bond, the green roof and sash windows kept).
- **river_kit** (#133): `race` for the Millrace, `canal` for Cogsworth's canal and lock, `riffles` and `river` for the Cog, `wood_edge` for Fernhollow's woods into the coal-hill forest.
- The terrace toolkit (#90) for the benches and Gasworks Hill.

The kits are on open PRs and land on `main` separately; until then, build against their branches and say which head you used.

## 10. Today's zones: replaced or kept

| Zone today | Becomes    | Where and what                                                                                                                                                   |
| ---------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| junction   | replaced   | Cogsworth's station square under the clock tower, the platform on its north edge; the ring stays (its stand moves with the square)                               |
| canal      | kept, sunk | the canal with its lock, half a tier down across the town; the foundry and allotments south-west                                                                 |
| (none)     | new ground | Gasworks Hill with the airship mast, the maglev terminus and pump house, the Millrace through the mills, the coal hills, the Narrows and the viaduct, Fernhollow |

Places keep their ids where the game uses them (mission places, stops, rings in `lib/world-places.ts`), so saves and missions carry over; their stands move with them.

## v55 overview: proposals for lane H (27 Oct)

The continent overview v55 (`../research/blockout/README.md`, "v55"; Matt's brief of 27 Oct) gives the towns room. These are proposals; this brief is unchanged until the lane adopts them.

- **Coordinates**: x 7000 to 8400 is widened by 1.10 and x 8400 to 9400 by 1.06 (`geo55.P`): Cogsworth to (8078, 2450), Fernhollow to (7165, 3080), the Cog foot to (8678, 3060).
- **Cogsworth, at least medium with room to grow (17 buildings, the workers' homes now brick terraces counted one a terrace)**: Foundry Row and the mills on the Millrace, Engine Street on the towpath road to the terminus, Pit Row and the brick terraces toward the pits, the station square; the railway yard and the allotments. It is the start of the Garth Road up the Cog to Highgarth (lane F).
- **Fernhollow, medium (16 buildings)**: the green with the chapel and school, the sawmill and wood yards, Green Lane and Cooper Lane, the clearing fields; open woods between it and Crossroads' Eastgate.
