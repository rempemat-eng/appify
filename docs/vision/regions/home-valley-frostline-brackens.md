# The home valley, the Frostline and the Brackens

**Owner: Claude E** (lane E). The hand-over brief for this region from the world plan v5.3 (`../world-plan.md`, PR #96). Build from it once Matt approves the plan. The Headland Lane and the Col Path are routes (Claude A draws their chunks, P6); you draw the land they cross inside this footprint, and both sides of the Col hut, the Frostline lip and the Headland stile. The Brackens gap is shared: you draw its two bluffs and the valley side; Claude D draws the steppe beyond it.

All coordinates are world pixels on the 11264 x 6912 px canvas (1 cell = 8 px; one screen = 320 x 576 px; an adult is 25 px; walking is 40 px/s). They come from the v5.3 block-out (`geo52.py`, `stats-v52.json`) and place things to within a cell or two: move a thing to fit the ground, not the ground to fit the number. The crop is `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/home-valley-frostline-brackens.png` (Claude A's scratchpad, not in the repository).

## 1. Footprint

| Part                                                | Box (world px)                 | Size (px)   |
| --------------------------------------------------- | ------------------------------ | ----------- |
| the home valley, Crossroads, the halt and Driftwood | x 5600 to 7000, y 2300 to 5100 | 1400 x 2800 |
| the Headland behind its wall                        | x 6800 to 7250, y 5100 to 5800 | 450 x 700   |
| the Frostline, the Col and Fir Hollow               | x 5700 to 6800, y 1300 to 2300 | 1100 x 1000 |
| the Brackens and their gap                          | x 4800 to 5600, y 1300 to 4000 | 800 x 2700  |

The boxes are where this brief's things are counted; the land inside them follows the ground, not the box. Where two boxes touch, the threshold between them (section 3) says who draws what.

## 2. Places and why they are here

| Place          | Kind    | Centre       | Size                                                  | Why here                                                                                                         |
| -------------- | ------- | ------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Home valley    | village | (6300, 3480) | 1280 x 2688 (decided; the garden 320 x 576 unchanged) | a sheltered basin where the Sleepwater leaves the uplands: water, a mill head, flat ground, hills on three sides |
| Driftwood      | harbour | (6420, 4960) | 544 x 352 harbour                                     | the cove at the Sleepwater's mouth, sheltered by the Headland: the valley's landing place                        |
| the Frostline  | cirque  | (6220, 1800) | as v2 (T3 to T5)                                      | a glacier's cirque above the valley: the Sleepwater's source, a tarn, snow late into summer                      |
| valley halt    | stop    | (5850, 4050) |                                                       | the valley train east to Cogsworth (W3) and the desert line west over the Rift to Dust Gulch (W5)                |
| Driftwood pier | stop    | (6520, 5080) |                                                       | the ferry to Lagoon Landing (W4)                                                                                 |

**Inside.**

- From north to south (plan 8.2): the Frostline in the peaks; the T2 terrace with the woodland, the garden and the riverside; the valley floor with the halt farm, Crossroads and the park; Driftwood's quay and the sea, with the Headland east of the estuary.
- The water explains the valley: snowmelt from the lake runs through Fir Hollow, falls over the escarpment into the woodland's spring pool, runs east along the garden's south edge as the brook, fills the millpond, turns the mill where it drops to the floor, and runs south to the estuary.
- _The garden_ (T2, 320 x 576, unchanged); _Crossroads_ (T1, about 640 x 560: a 240 x 176 square with the well, the library and a terrace of cottages north, the bakery west, the stall on the square, the green with the ring south-west); _the halt farm_ (T1, about 400 x 480); _the woodland_ (T2, 416 x 512: the spring pool, the stone circle in a glade, the forester's yard); _the riverside_ (T2, 544 x 512: millpond, mill, miller's cottage, orchard, beehives); _the park_ (T1: bandstand, pump house); _Driftwood_ (five cottages, a 32 px quay face with a ramp, fish market, harbour master, chandlery, the slip with the ferry, three jetties, the breakwater to the lighthouse); _the Headland_ (the drystone wall with the stile, the sheep fold, the lookout tower, a cove stair); _the Frostline_ (Fir Hollow, the cabin meadow, the col to the Snow Saddle and its bothy, Snowmelt Lake, the spur stair to the High Lookout).
- _The Brackens_: a low heather ridge with pines and gorse, two bluffs either side of the gap where the Drover's Road leaves the valley, the drove well, sheepfolds and a shepherd's hut along the road, the stone ring on the ridge (an egg spot), and two spurs pushing the Rift west (the Heather spur at about (4990, 1960) to (4560, 2190), the Fold spur at about (4930, 3220) to (4560, 3330)).
- Walk times from the hut's door (v2): the spring pool 8 s, the library 12, the stall 13, the cabin 13, the well 14, the stone circle 16, the ring 19, the halt platform 19, the mill 21, the bothy 21, the bandstand 24, Snowmelt Lake 28, the High Lookout 31, the ferry pier 36, the Headland's tower 42, the lighthouse 46.

## 3. Transitions

Each threshold is a place: a threshold object on the route (Claude A draws the object), a mixing band about 1400 px long along the route where both grounds mix, with outliers up to 700 px either way, a landmark seen from the threshold, residents crossing, and an ambience cross-fade of 160 px (4 s). You draw your side of each band.

| Threshold                           | Route         | Sides drawn by      | Mixing band (ground kinds, from side to side)         | Landmark seen               | Residents crossing (each way)                                                                                                                         | Radiates from         |
| ----------------------------------- | ------------- | ------------------- | ----------------------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| **the Col hut** (6290, 2350)        | Col Path      | Claude E / Claude E | meadow, broadleaf, garden → alpine, meadow, broadleaf | the headwall (6230, 1950)   | sheep and their shepherd graze up as far as the hut; walkers with staffs; choughs and an ibex on the scree above; the hut warden comes down for bread | the glacier           |
| **the Frostline lip** (6230, 2040)  | Col Path      | Claude E / Claude E | meadow, broadleaf, alpine → alpine, snow, meadow      | the tarn (6200, 1800)       | the warden and an ice-cutter with a sledge go up; meltwater, and an ibex on the moraine looking down                                                  | the glacier           |
| **the Brackens gap** (5200, 3760)   | Drover's Road | Claude E / Claude D | meadow, field, field2 → steppe, meadow, broadleaf     | the bluffs (5170, 3600)     | a drover takes his flock out west; his dog ranges ahead; skylarks over the bluffs; a peat-cutter's cart comes in to the valley                        | the Brackens' heather |
| **the Headland stile** (6990, 5300) | Headland Lane | Claude E / Claude E | meadow, sand, field → sand, meadow                    | the lighthouse (7050, 5600) | sheep cross the stile to the fold; the lighthouse keeper; a hare from the cliff turf; sea pinks spill over the wall                                   | the sea               |
| **the Shell Bar** (6900, 5900)      | Shell Bar     | Claude E / Claude C | sand, meadow, field → meadow, sand, field2            | the wreck (6930, 5870)      | cocklers walk out at low tide; seals haul out on the bar; terns nest on the islet                                                                     | the sea               |

The band's elements cross the line both ways: at least three of each side's grounds, props or residents on the other side (benchmark check 12). The props and residents named in section 5.2 of the plan join the ground kinds here.

## 4. Tiers, and how you go up and down

| Part                    | Tiers walked | Faces           | Stairs on routes | Ramps on routes | Switchback steps |
| ----------------------- | ------------ | --------------- | ---------------- | --------------- | ---------------- |
| the home valley         | 2 to 12      | 32 px; up to 96 | 4                | 12              | 4                |
| the Frostline           | 5 to 31      | 32 px; up to 64 | 0                | 19              | 3                |
| the massif (north edge) | 7 to 29      | 32 px; up to 32 | 0                | 0               | 0                |

A tier is one 32 px south face (40 px in the city); west and east ends are 5 px side bands; stairs are at least 34 px open; ramps run along a face at 1 in 3; a screen shows at most two full tiers and one low step (`verticality.md`).

- The Col Path climbs the cirque's step in switchbacks, the Col hut halfway; W2 at the lip.
- v2's terraces T0 to T2 in the valley, with stairs and ramps on the lanes; the mill's weir is a fall between levels.
- The Frostline: Fir Hollow behind the rock rib (gully trail), the col up to the Snow Saddle, the spur stair to the High Lookout.
- Driftwood's 32 px quay face with a ramp; the Headland one tier above the cove, with a cove stair.
- The Brackens: a low ridge of two or three tiers with bluffs either side of the gap; no route climbs its crest.

## 5. Things to place (section 6.4), with coordinates

None of these gives a reward, a cost or a chore.

**Named things** (26), from each biome's own list:

| Thing                         | Kind     | At           | Route         | Where                    |
| ----------------------------- | -------- | ------------ | ------------- | ------------------------ |
| wayside shrine                | shrine   | (5884, 4357) | Ash Coast     | a short way off the path |
| old oak                       | landmark | (6865, 4820) | Coast Path    | a short way off the path |
| hay barn                      | landmark | (7020, 5151) | Coast Path    | beside the path          |
| ibex rocks                    | wild     | (6136, 1949) | Col Path      | beside the path          |
| cairn                         | landmark | (6464, 2152) | Col Path      | a short way off the path |
| a fallen climbers' camp       | ruin     | (6295, 2306) | Col Path      | beside the path          |
| beehives                      | prop     | (6262, 2451) | Col Path      | beside the path          |
| a hare form in the long grass | wild     | (6320, 2528) | Col Path      | beside the path          |
| well                          | well     | (6357, 2549) | Col Path      | beside the path          |
| haymakers' shelter            | camp     | (6340, 2589) | Col Path      | beside the path          |
| a tumbled field barn          | ruin     | (6302, 2641) | Col Path      | beside the path          |
| wayside shrine                | shrine   | (6031, 2887) | Col Path      | a short way off the path |
| drove well                    | well     | (5086, 3328) | Drover's Road | a short way off the path |
| a broken sheepfold            | ruin     | (4855, 3627) | Drover's Road | beside the path          |
| shepherd's hut                | npc      | (5151, 3828) | Drover's Road | beside the path          |
| sheepfold                     | landmark | (5447, 3882) | Drover's Road | beside the path          |
| stile and bench               | landmark | (5642, 4227) | Drover's Road | a short way off the path |
| picnic viewpoint              | view     | (6671, 3134) | Foothill Road | a short way off the path |
| tide pools                    | wild     | (7206, 5115) | Headland Lane | a short way off the path |
| a wreck on the rocks          | ruin     | (6910, 5144) | Headland Lane | beside the path          |
| a cliff-top view to the isles | view     | (6930, 5205) | Headland Lane | beside the path          |
| a beachcomber's camp          | camp     | (6892, 5257) | Headland Lane | beside the path          |
| seal rocks                    | wild     | (6965, 5522) | Headland Lane | beside the path          |
| crevasse viewpoint            | view     | (6329, 1579) | High Fells    | a short way off the path |
| herders' shieling             | camp     | (6673, 1699) | High Fells    | beside the path          |
| scarecrow                     | landmark | (6904, 3652) | Lull Road     | a short way off the path |

**Secret pockets** (5): a little dead-end path (80 px or more) off the route to a clearing that holds the thing named.

| Holds                         | Clearing at  | Off the route |
| ----------------------------- | ------------ | ------------- |
| a view over the land          | (6416, 2465) | Col Path      |
| a bench under a tree          | (6488, 2679) | Col Path      |
| a hermit at a fire            | (5183, 3416) | Drover's Road |
| a story detail: a buried bell | (5444, 3604) | Drover's Road |
| a hermit at a fire            | (6876, 5636) | Shell Bar     |

**Markers for the art** (183: 76 interactables, 93 story props, 14 ambient). Along routes, ten a screen in the pattern I S S A I S S I S A; in settlements, eight interactables and eight story props a screen. Each is a slot: draw the named thing, or another of the same type that fits the ground.

- _Ash Coast_: I bench (5775, 4203); S cairn (5690, 4148); S tracks (5700, 4236); A butterflies (5603, 4255); I door (5661, 4339); S marker stone (5611, 4449)
- _Coast Path_: I bench (6715, 4937); S cairn (6677, 5036); S tracks (6766, 5017); I door (6863, 5042); S cold fire ring (6924, 5118); S marker stone (6974, 5036); I bench (7023, 5121); A hares (7153, 5120)
- _Col Path_: I bench (6236, 2914); S cairn (6323, 2869); S tracks (6240, 2818); A butterflies (6296, 2737); I door (6203, 2701); S cold fire ring (6278, 2636); S marker stone (6230, 2559); I bench (6327, 2551); S cart with a broken wheel (6227, 2529); A butterflies (6287, 2501); I noticeboard (6286, 2400); S mended fence (6334, 2352); S old boot (6264, 2421); A butterflies (6221, 2338); I bench (6183, 2309); S lost hat (6276, 2323); S cart with a broken wheel (6213, 2282); I noticeboard (6248, 2205); S tracks (6210, 2141); A choughs (6293, 2106); I gate (6203, 2067); S cold fire ring (6254, 1990); S marker stone (6166, 1948)
- _Driftwood_: S cold fire ring (6424, 4736); I noticeboard (6376, 4784); S mended fence (6368, 4800); I signpost (6312, 4840); I gate (6472, 4840); S tracks (6496, 4840); I water trough (6600, 4864); S tracks (6328, 4872); I water trough (6544, 4872); I gate (6360, 4896); I water trough (6544, 4896); S marker stone (6208, 4912); S cairn (6232, 4912); S marker stone (6408, 4944); S mended fence (6624, 4976); I bench (6328, 4992)
- _Drover's Road_: I bench (5740, 4060); S cairn (5752, 3959); S tracks (5670, 4009); A butterflies (5622, 3929); S cold fire ring (5515, 3928); S marker stone (5433, 3978); I bench (5438, 3876); S cart with a broken wheel (5343, 3886); A sheep (5361, 3790); I noticeboard (5273, 3830); S mended fence (5240, 3738); S old boot (5161, 3800); A sheep (5150, 3704); I bench (5054, 3714); S lost hat (5091, 3621); S cart with a broken wheel (4991, 3620); I noticeboard (4986, 3526); S tracks (4923, 3597); A sheep (4851, 3525)
- _Foothill Road_: I bench (6755, 3345); S cairn (6860, 3367); S tracks (6844, 3271); A butterflies (6942, 3272); I door (6921, 3174)
- _Headland Lane_: I bench (6957, 5125); S cairn (6918, 5216); S tracks (7013, 5221); A terns (6948, 5316); I door (6981, 5357); S cold fire ring (6989, 5412); S marker stone (7073, 5465); I bench (6997, 5530); S cart with a broken wheel (7107, 5564)
- _High Fells_: I bench (6328, 1706); S cairn (6404, 1764); S tracks (6409, 1663); A choughs (6504, 1682); I door (6519, 1583); S cold fire ring (6587, 1651); S marker stone (6653, 1580); I bench (6687, 1692); S cart with a broken wheel (6755, 1605)
- _Home valley_: I signpost (6256, 2944); S cart with a broken wheel (6048, 2976); I noticeboard (6312, 2992); S marker stone (6336, 3000); I signpost (6136, 3064); I resident (6128, 3072); I gate (6256, 3120); S mended fence (6312, 3136); I noticeboard (6344, 3136); S mended fence (6400, 3152); I noticeboard (6464, 3168); S marker stone (5840, 3176); I gate (6088, 3184); I door (6304, 3208); I water trough (6720, 3216); S marker stone (6064, 3224); I noticeboard (6136, 3248); I water trough (6368, 3256); S tracks (6384, 3264); I resident (6184, 3272); S cold fire ring (6336, 3272); S tracks (6616, 3272); I noticeboard (5960, 3296); I signpost (5776, 3304); I water trough (5864, 3304); S old boot (6544, 3304); I door (6088, 3312); S cairn (5992, 3320); S cart with a broken wheel (6176, 3320); S cairn (6144, 3328); S lost hat (6808, 3336); I noticeboard (6304, 3368); I signpost (6816, 3368); S cold fire ring (6616, 3376); S cold fire ring (6528, 3400); S lost hat (5912, 3416); S cart with a broken wheel (5840, 3432); I resident (6184, 3432); S mended fence (6144, 3448); I signpost (6512, 3448); S cairn (6424, 3456); S cart with a broken wheel (5776, 3464); S marker stone (6272, 3464); I water trough (5792, 3480); S cold fire ring (6032, 3480); S marker stone (6576, 3480); S cart with a broken wheel (5856, 3488); I door (6200, 3488); I gate (6216, 3488); S lost hat (5880, 3504); I water trough (6536, 3536); I water trough (6584, 3568); S tracks (6504, 3584); S cold fire ring (5824, 3608); I resident (6120, 3616); I bench (6568, 3616); S cairn (6712, 3632); S cairn (6136, 3656); S cold fire ring (6296, 3656); I water trough (6592, 3656); S tracks (6080, 3688); S tracks (6008, 3696); I gate (5800, 3704); I door (6008, 3704); I resident (6224, 3712); S marker stone (6600, 3760); I water trough (5896, 3776); I bench (6240, 3776); S marker stone (6336, 3784); I door (6288, 3808); S old boot (5912, 3816); S mended fence (6648, 3816); I gate (5976, 3864); S old boot (6264, 3888); I noticeboard (6024, 3896); I noticeboard (6648, 3896); S mended fence (6576, 3904); I resident (6080, 3920); S lost hat (6392, 3952); I water trough (6184, 4024)
- _Lull Road_: I bench (6817, 3731); S cairn (6833, 3830); S tracks (6909, 3768); A butterflies (6959, 3850); I door (6990, 3895)
- _Shell Bar_: I bench (7080, 5693); S cairn (6979, 5713); S tracks (7008, 5783)

**Easter-egg spots, reserved** (keep the ground there clear and reachable; nothing is placed yet): stone ring on the Brackens (5000, 3150).

## 6. Boundaries, in layers

Every edge has three layers, drawn as the land itself (plan 5.5): **the fade** (walkable ground with clumps that thicken outward, 10 to 160 px), **the wall** (the ground's own three blockers in uneven patches, 64 to 180 px deep, then thinning out again over 160 to 400 px), and **what lies beyond** (drawn, never walked, hazier). Never a line, a ribbon or a checker.

| Edge                                             | Fade and wall                                                                               | Beyond                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| North (above the Frostline)                      | scree and boulders thickening into crags and the headwall                                   | the massif's peaks and glaciers to the top edge |
| North-east (the old forest above the Fern hills) | bramble and fallen trees thickening into thicket and old trees                              | the forest's dark canopy                        |
| West (the Brackens' far side)                    | heather and gorse clumps thickening into gorse and thicket                                  | the steppe and the Rift country, hazier         |
| South (the coast)                                | none on the cliffs: the sea is the edge, with surf; dune grass and driftwood on the beaches | the sea, the isles and the rocket's cape        |

## 7. Obstacles, side paths and loops

| Obstacle             | At           | Route           | How it is passed                                                                                                |
| -------------------- | ------------ | --------------- | --------------------------------------------------------------------------------------------------------------- |
| thicket              | (6729, 1527) | High Fells      | side path off the road at a Y about 300 px before, round the far side, back at a Y                              |
| thicket              | (5491, 3829) | Drover's Road   | side path off the road at a Y about 300 px before, round the far side, back at a Y                              |
| the Headland's rocks | (7050, 5560) | a loop round it | an irregular outline; the path closer on one side; joins the road at a Y (or where the road runs into the loop) |
| a dew pond           | (6680, 4350) | a loop round it | an irregular outline; the path closer on one side; joins the road at a Y (or where the road runs into the loop) |
| collapsed bridge     | (6200, 1848) | the Sleepwater  | beside the ford: a ruin, not a way                                                                              |

Rules: at most one loop in any small area (obstacles at least 800 px apart); side paths never cross their own road; no one-way drops (every shortcut a two-way stair, ramp, ladder, stepping stones or a latch that stays open); an obstacle keeps every touch target at least 44 screen px clear.

## 8. Benchmark checks to hold on the drawn art

The block-out passes all 21 checks of `../research/world-benchmark.md` (plan 2.1). The block-out's markers and materials stand in for props, so the drawn art must hold them again. **Checks 1 and 9 above all:**

- **1. Density.** Each route screen 2 to 3 interactables and 3 to 5 story props; each settlement screen 6 to 10 of each. Here: about 9 screens of route and the settlements in section 2, so at least 17 interactables and 26 story props on the routes, plus 6 of each per settlement screen.
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

- **river_kit** (Claude E, #133): `river` (cut bank and point bar by side of the bend), `ford`, `stepping_stones`, `riffles`, `race` (the mill race), `flow_frames`; reeds, marginals and the bank trees (crack and pollard willow, alder); hay meadow, grazed pasture, ploughed and crop fields with margins, hedgerows with gates, the farm track; `blend`, `heath` (meadow into the Brackens' heath) and `wood_edge` (meadow into the Fern hills' wood).
- **house kits** (#121, `house_kits.py`): the valley and isles cottages (`front`, `door`, `window`, `roof`, `sign`, `prop`, four or five variants each) for Crossroads, the halt farm and Driftwood, on the house palette.
- **dry_kit** (Claude D, #137): only its `steppe` and `steppe_to_desert` where the Brackens' far side meets D's steppe, so the band matches across the lane line.

The kits are on open PRs and land on `main` separately; until then, build against their branches and say which head you used.

## 10. Today's zones: replaced or kept

| Zone today | Becomes       | Where and what                                                                                                          |
| ---------- | ------------- | ----------------------------------------------------------------------------------------------------------------------- |
| garden     | kept          | the home hub: its size, place, geometry and harness stay (8.2)                                                          |
| ridge      | kept, placed  | the cabin meadow on the Frostline's slope above the garden                                                              |
| hollow     | kept, placed  | Fir Hollow behind the rock rib, with the gully trail and W2's second pine                                               |
| saddle     | kept, placed  | the Snow Saddle and its bothy, up the col (W2)                                                                          |
| snowmelt   | kept, placed  | Snowmelt Lake in its cirque: the Frostline's tarn, the Sleepwater's source                                              |
| summit     | kept, placed  | the High Lookout, up the spur stair                                                                                     |
| woodland   | kept, redrawn | the woodland on T2 west of the garden: the spring pool under the fall, the stone circle in a glade, the forester's yard |
| riverside  | kept, redrawn | the millpond and the mill (where PR #86 put it), the miller's cottage, orchard and beehives                             |
| town       | replaced      | Crossroads, a village at true scale with a square on the garden's axis (8.2)                                            |
| park       | kept, redrawn | the park east of the river: the bandstand, the pump house, the lane to the estuary footbridge                           |
| halt       | replaced      | the halt farm: station house, a 240 px platform, the engine shed (W3), the farmyard and the windmill                    |
| harbour    | replaced      | Driftwood, its own hamlet above a quay, with the ferry pier (W4) and the lighthouse on its rock                         |
| headland   | kept, walled  | the Headland behind its drystone wall, the stile (W1) its only gap                                                      |
| (none)     | new ground    | the Brackens and their gap, the Col hut, Driftwood's cove as an estuary, the valley's frame of sea and old forest       |

Places keep their ids where the game uses them (mission places, stops, rings in `lib/world-places.ts`), so saves and missions carry over; their stands move with them.
