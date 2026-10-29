# The Sunstone basin and the fire country

**Owner: Claude D** (lane D). The hand-over brief for this region from the world plan v5.3 (`../world-plan.md`, PR #96). Build from it once Matt approves the plan. The Drover's Road, the Canyon Road, the Lode Track, the Ash Coast, the Ember Way and the Forge Stair are routes; section 7 of the plan makes Sunstone Reach a journey, so you draw the land along them and Claude A draws only their thresholds' objects and the shortcuts' lines.

All coordinates are world pixels on the 11264 x 6912 px canvas (1 cell = 8 px; one screen = 320 x 576 px; an adult is 25 px; walking is 40 px/s). They come from the v5.3 block-out (`geo52.py`, `stats-v52.json`) and place things to within a cell or two: move a thing to fit the ground, not the ground to fit the number. The crop is `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/sunstone-basin-fire-country.png` (Claude A's scratchpad, not in the repository).

## 1. Footprint

| Part                                                                 | Box (world px)              | Size (px)   |
| -------------------------------------------------------------------- | --------------------------- | ----------- |
| the steppe west of the Brackens gap, the Rift and the Sunstone basin | x 0 to 4800, y 0 to 4300    | 4800 x 4300 |
| the fire country, Cinderwick and the Ash Coast                       | x 0 to 5600, y 4000 to 5850 | 5600 x 1850 |

The boxes are where this brief's things are counted; the land inside them follows the ground, not the box. Where two boxes touch, the threshold between them (section 3) says who draws what.

## 2. Places and why they are here

| Place               | Kind     | Centre       | Size                       | Why here                                                                                                 |
| ------------------- | -------- | ------------ | -------------------------- | -------------------------------------------------------------------------------------------------------- |
| Palm Spring         | oasis    | (3480, 2800) | 300 x 220                  | the Willow Run sinks into the gravel and comes up again here: the first water in the dry country         |
| Dust Gulch          | frontier | (2760, 2420) | 544 x 320                  | where the Amber leaves the mountains: water, the mine above, the railhead                                |
| the Lode            | mine     | (3060, 1650) | 260 x 180                  | iron and copper in the massif foothills, reached by a mule track                                         |
| Hearthold           | hilltown | (2480, 5120) | 400 x 400 inside its walls | a rock between two lava flows below the crater: the only defensible ground on the volcano's seaward side |
| Ember forge         | forge    | (2460, 4860) | as v2                      | the crater's heat at the caldera lip; ore comes down from the Lode by cart                               |
| Cinder Springs      | springs  | (2200, 5420) | as v2                      | hot springs where the sea seeps into the volcano's warm flank                                            |
| Cinderwick          | hamlet   | (2760, 5640) | 340 x 200                  | a black-sand cove between the flows: charcoal and fish                                                   |
| Dust Gulch platform | stop     | (2900, 2330) |                            | the desert line's terminus, with a water crane and a buffer                                              |
| the Lode mine mouth | stop     | (3040, 1700) |                            | the mine cart's top, down past the salt lake to the forge (after W6)                                     |
| the forge cart bay  | stop     | (2470, 4900) |                            | the mine cart's lower end, on solid basalt below the crater                                              |

**Inside.**

- Sunstone Reach is a journey into the heat (plan 7): the drove road west round the Brackens' southern end into short grass (sheepfolds, a well); the Rift's gorge with banded walls and Drover's bridge (W5), the desert line's viaduct upstream; the scrub with single trees and mesas on the skyline; Palm Spring (300 x 220), where the Willow Run comes out of its gravel (palms, a pool, orchards fed by channels, a water-seller's awning); Dust Gulch (544 x 320) on the Amber's fan (one street of false fronts, the platform and water crane, orchards, the mine track behind); the Lode up the mule track (mine mouth, ore tubs, the cart line's start); the Amber canyon between banded walls and mesas (a fossil in the wall, an egg spot); the white salt lake and the ash; the chasm bridge (W6) to Hearthold (400 x 400 inside its walls) on its rock between the flows; the forge below the crater, Cinder Springs on the seaward side, Cinderwick in its black-sand cove; and the Ash Coast home along the green shelf, through the dead forest and over the Rift's mouth by ferry.
- _The volcano_ (plan 4.7): the old flow out of the summit crater's south-west breach (crusted, edges grown over), the young flow from a flank vent about 500 px down the south-east side (a short fissure and a small spatter cone), the upper cone never walked; ash blown north, parasitic cones and a fumarole field on the north flank, the dead forest where the young flow ran through the coastal woods, hot springs and black sand on the seaward side.
- _The Rift_ swings round two spurs of the Brackens and takes the Heather burn, the Brackens beck, the Sedgeburn and two dry forks; its green strip is a thread in the gorge and wide in the bays and at the confluences.

## 3. Transitions

Each threshold is a place: a threshold object on the route (Claude A draws the object), a mixing band about 1400 px long along the route where both grounds mix, with outliers up to 700 px either way, a landmark seen from the threshold, residents crossing, and an ambience cross-fade of 160 px (4 s). You draw your side of each band.

| Threshold                              | Route         | Sides drawn by      | Mixing band (ground kinds, from side to side)             | Landmark seen                         | Residents crossing (each way)                                                                                                  | Radiates from         |
| -------------------------------------- | ------------- | ------------------- | --------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| **the Brackens gap** (5200, 3760)      | Drover's Road | Claude E / Claude D | meadow, field, field2 → steppe, meadow, broadleaf         | the bluffs (5170, 3600)               | a drover takes his flock out west; his dog ranges ahead; skylarks over the bluffs; a peat-cutter's cart comes in to the valley | the Brackens' heather |
| **Drover's bridge** (4330, 3440)       | Drover's Road | Claude D / Claude D | steppe, meadow, broadleaf → scrub, meadow, steppe         | the desert line viaduct (4290, 3720)  | the flock goes on to the far folds; a water-seller crosses to trade; lizards on the parapet; a vulture over the gorge          | the Rift              |
| **the Rift ferry** (4180, 5240)        | Ash Coast     | Claude D / Claude D | meadow, broadleaf, sand → deadwood, meadow, blacksand     | the Rift mouth (4250, 5380)           | the ferryman (he lives here) takes fishers and goats across; terns and a black-sand beachcomber come the other way             | the Rift and the sea  |
| **the Amber canyon head** (2770, 2650) | Canyon Road   | Claude D / Claude D | desert, garden, meadow → ash, desert, badland             | the canyon walls (2640, 2950)         | a mule train comes down from the Lode with ore; orchard hands walk up from the fan; a vulture rides the canyon draught         | the Amber             |
| **the Cinder Rise** (2270, 3860)       | Canyon Road   | Claude D / Claude D | ash, desert, badland → ash, desert, lavastone             | the plume over Hearthold (2470, 4300) | prospectors with sample bags go south; ash dust drifts north onto the bushes; a salamander basks on the ridge                  | the volcano           |
| **the chasm bridge** (2170, 4920)      | Canyon Road   | Claude D / Claude D | ash, desert, lavastone → steppe, ash, scrub               | Hearthold (2480, 5120)                | carters bring charcoal and ore to the forge; Hearthold's gate guard walks the bridge; steam drifts across                      | the volcano           |
| **the crust causeway** (3300, 5560)    | Ash Coast     | Claude D / Claude D | deadwood, meadow, blacksand → meadow, deadwood, blacksand | the flow's steaming toe (3290, 5800)  | charcoal burners from Cinderwick carry sacks west; goats from the coast browse the dead forest's fireweed                      | the volcano           |

The band's elements cross the line both ways: at least three of each side's grounds, props or residents on the other side (benchmark check 12). The props and residents named in section 5.2 of the plan join the ground kinds here.

## 4. Tiers, and how you go up and down

| Part               | Tiers walked | Faces            | Stairs on routes | Ramps on routes | Switchback steps |
| ------------------ | ------------ | ---------------- | ---------------- | --------------- | ---------------- |
| the Sunstone basin | 4 to 11      | 32 px; up to 32  | 9                | 5               | 2                |
| the Rift           | 2 to 8       | 32 px; up to 160 | 1                | 8               | 0                |
| the fire country   | 6 to 29      | 32 px; up to 224 | 24               | 7               | 0                |

A tier is one 32 px south face (40 px in the city); west and east ends are 5 px side bands; stairs are at least 34 px open; ramps run along a face at 1 in 3; a screen shows at most two full tiers and one low step (`verticality.md`).

- The Lode Track in switchbacks up the spur; stairs into the Amber canyon and ramps along its floor.
- Mesa tops 32 to 96 px above the plateau, reached by ladder as lookouts; canyon floors 64 to 128 px below.
- The Rift: gorge walls up to 160 px; ramps down to the ferry at its mouth; Drover's bridge across.
- The fire country: lava terraces of 32 px as natural steps, the forge stair, Hearthold's stepped streets (24 stairs) and its keep above the town; the upper cone is never walked.

## 5. Things to place (section 6.4), with coordinates

None of these gives a reward, a cost or a chore.

**Named things** (39), from each biome's own list:

| Thing                     | Kind     | At           | Route         | Where                    |
| ------------------------- | -------- | ------------ | ------------- | ------------------------ |
| lone pine viewpoint       | view     | (5497, 4411) | Ash Coast     | beside the path          |
| shepherd's hut            | npc      | (4892, 4527) | Ash Coast     | a short way off the path |
| sheepfold                 | landmark | (5368, 4677) | Ash Coast     | beside the path          |
| a lone tree               | landmark | (4825, 4828) | Ash Coast     | beside the path          |
| drove well                | well     | (4888, 4996) | Ash Coast     | beside the path          |
| hare warren               | wild     | (4586, 5053) | Ash Coast     | beside the path          |
| obsidian scree            | landmark | (4118, 5163) | Ash Coast     | beside the path          |
| barrow mound              | landmark | (4372, 5230) | Ash Coast     | beside the path          |
| ruined watchtower         | ruin     | (3404, 5250) | Ash Coast     | a short way off the path |
| lava tube mouth           | cave     | (3904, 5363) | Ash Coast     | beside the path          |
| cinder shrine             | shrine   | (3075, 5562) | Ash Coast     | beside the path          |
| steam pools               | wild     | (3353, 5609) | Ash Coast     | beside the path          |
| fumarole field            | landmark | (2836, 5685) | Ash Coast     | beside the path          |
| wagon wreck               | wreck    | (3038, 2653) | Canyon Road   | a short way off the path |
| rock arch                 | landmark | (2677, 2920) | Canyon Road   | beside the path          |
| cliff shrine              | shrine   | (2706, 3281) | Canyon Road   | beside the path          |
| bone yard                 | landmark | (2461, 3757) | Canyon Road   | beside the path          |
| lizard rocks              | wild     | (2212, 3872) | Canyon Road   | beside the path          |
| a rise over the flows     | view     | (2175, 4068) | Canyon Road   | beside the path          |
| a sulphur-gatherer's camp | camp     | (2137, 4120) | Canyon Road   | beside the path          |
| fumarole field            | landmark | (2207, 4185) | Canyon Road   | a short way off the path |
| obsidian scree            | landmark | (2024, 4645) | Canyon Road   | beside the path          |
| ruined watchtower         | ruin     | (2327, 4980) | Canyon Road   | beside the path          |
| lava tube mouth           | cave     | (1992, 5074) | Canyon Road   | a short way off the path |
| bone yard                 | landmark | (3147, 2575) | Drover's Road | beside the path          |
| rock arch                 | landmark | (3553, 2619) | Drover's Road | a short way off the path |
| lizard rocks              | wild     | (2791, 2721) | Drover's Road | a short way off the path |
| cliff shrine              | shrine   | (3287, 2787) | Drover's Road | beside the path          |
| wagon wreck               | wreck    | (3761, 3094) | Drover's Road | beside the path          |
| wind pump                 | well     | (4078, 3159) | Drover's Road | beside the path          |
| barrow mound              | landmark | (4424, 3450) | Drover's Road | beside the path          |
| hare warren               | wild     | (4663, 3573) | Drover's Road | beside the path          |
| caravan camp              | camp     | (4047, 3582) | Drover's Road | a short way off the path |
| steam pools               | wild     | (2526, 5399) | Ember Way     | a short way off the path |
| cinder shrine             | shrine   | (2151, 5475) | Ember Way     | beside the path          |
| fumarole field            | landmark | (2457, 5500) | Ember Way     | beside the path          |
| wind pump                 | well     | (2949, 1931) | Lode Track    | beside the path          |
| caravan camp              | camp     | (3001, 1988) | Lode Track    | beside the path          |
| mirage viewpoint          | view     | (2688, 2064) | Lode Track    | a short way off the path |

**Secret pockets** (7): a little dead-end path (80 px or more) off the route to a clearing that holds the thing named.

| Holds                                   | Clearing at  | Off the route |
| --------------------------------------- | ------------ | ------------- |
| a view down a gorge                     | (4759, 3270) | Drover's Road |
| a resident fishing                      | (2126, 3694) | Canyon Road   |
| a story detail: initials cut in a stone | (3088, 2026) | Lode Track    |
| a view over the land                    | (3927, 2838) | Drover's Road |
| a bench under a tree                    | (3387, 5321) | Ash Coast     |
| a story detail: an old grave            | (2212, 5762) | Ember Way     |
| a hermit at a fire                      | (2500, 5402) | Ember Way     |

**Markers for the art** (305: 116 interactables, 153 story props, 36 ambient). Along routes, ten a screen in the pattern I S S A I S S I S A; in settlements, eight interactables and eight story props a screen. Each is a slot: draw the named thing, or another of the same type that fits the ground.

- _Ash Coast_: S cold fire ring (5569, 4360); I bench (5509, 4439); S cart with a broken wheel (5507, 4532); A sheep (5411, 4487); I noticeboard (5406, 4582); S mended fence (5312, 4566); S old boot (5344, 4659); A sheep (5245, 4649); I bench (5222, 4741); S lost hat (5158, 4667); S cart with a broken wheel (5109, 4751); I noticeboard (5026, 4701); S tracks (5051, 4794); A sheep (4955, 4808); I gate (4985, 4903); S cold fire ring (4892, 4874); S marker stone (4867, 4972); A sheep (4786, 4917); I noticeboard (4776, 5012); S cairn (4683, 4985); S tracks (4699, 5089); I gate (4602, 5080); S old boot (4612, 5177); A sheep (4525, 5132); I resident (4492, 5220); S lost hat (4424, 5143); S cart with a broken wheel (4364, 5220); A sheep (4299, 5148); I gate (4279, 5247); S mended fence (4189, 5180); S old boot (4143, 5282); I resident (4109, 5192); S marker stone (4030, 5253); A steam (3979, 5174); I water trough (3956, 5272); S cairn (3861, 5250); S tracks (3877, 5348); A steam (3784, 5319); I resident (3747, 5409); S cold fire ring (3686, 5335); S marker stone (3655, 5427); I water trough (3560, 5406); S cart with a broken wheel (3590, 5500); A steam (3495, 5487); I signpost (3480, 5582); S mended fence (3410, 5505); S old boot (3344, 5598); A steam (3305, 5618); I water trough (3245, 5570); S lost hat (3179, 5572); S cart with a broken wheel (3151, 5625); I signpost (3081, 5591); S tracks (3030, 5674); A steam (2981, 5585); I door (2912, 5650); S cold fire ring (2847, 5581); S marker stone (2819, 5680)
- _Canyon Road_: I bench (2833, 2610); S cairn (2741, 2649); S tracks (2823, 2702); A vultures (2761, 2777); I door (2849, 2824); S cold fire ring (2759, 2865); S marker stone (2797, 2950); I bench (2692, 2949); S cart with a broken wheel (2735, 3031); A vultures (2650, 3078); I noticeboard (2754, 3137); S mended fence (2647, 3177); S old boot (2676, 3269); A vultures (2582, 3246); I bench (2537, 3298); S lost hat (2509, 3363); S cart with a broken wheel (2599, 3440); I noticeboard (2571, 3496); S tracks (2514, 3542); A vultures (2472, 3578); I gate (2457, 3639); S cold fire ring (2394, 3657); S marker stone (2424, 3746); A vultures (2314, 3769); I noticeboard (2385, 3836); S cairn (2292, 3861); S tracks (2301, 3955); I gate (2237, 3979); S old boot (2192, 3996); A vultures (2099, 3962); I resident (2127, 4056); S lost hat (2109, 4103); S cart with a broken wheel (2093, 4161); A steam (2065, 4221); I gate (2020, 4273); S mended fence (1979, 4307); S old boot (1947, 4343); I resident (1929, 4383); S marker stone (1931, 4424); A steam (1946, 4468); I water trough (1970, 4531); S cairn (1986, 4584); S tracks (1994, 4648); A steam (2002, 4706); I resident (2015, 4742); S cold fire ring (2000, 4836); S marker stone (2086, 4789); I water trough (2121, 4868); S cart with a broken wheel (2201, 4877); A steam (2227, 4925); I signpost (2257, 4973); S mended fence (2249, 5068); S old boot (2330, 5011); A steam (2373, 5071); I water trough (2449, 5040)
- _Cinder Springs_: I resident (2208, 5312); S cairn (2272, 5320); S cold fire ring (2216, 5328); I gate (2184, 5360); S marker stone (2224, 5360); S tracks (2184, 5368); I gate (2216, 5408); I bench (2096, 5416); S old boot (2176, 5416); S mended fence (2320, 5432); I door (2144, 5464); I door (2136, 5472); S lost hat (2224, 5480); I bench (2272, 5496); I bench (2128, 5504); S cold fire ring (2152, 5512)
- _Cinderwick_: I gate (2760, 5544); I bench (2800, 5552); S tracks (2840, 5552); S mended fence (2712, 5568); S cairn (2848, 5584); I gate (2712, 5600); S mended fence (2768, 5608); I water trough (2656, 5624); I resident (2800, 5624); S cart with a broken wheel (2848, 5624); S mended fence (2872, 5624); I signpost (2712, 5632); S cold fire ring (2808, 5648); I water trough (2672, 5656); I door (2760, 5664); S mended fence (2640, 5696)
- _Drover's Road_: I door (5563, 4012); I gate (4797, 3605); S cold fire ring (4766, 3511); S marker stone (4681, 3549); A sheep (4663, 3446); I noticeboard (4599, 3516); S cairn (4524, 3449); S tracks (4494, 3544); I gate (4421, 3480); S old boot (4363, 3558); A sheep (4340, 3463); I resident (4246, 3487); S lost hat (4275, 3394); S cart with a broken wheel (4181, 3407); A vultures (4162, 3308); I gate (4076, 3358); S mended fence (4088, 3266); S old boot (3990, 3243); I resident (4049, 3170); S marker stone (3951, 3149); A vultures (3971, 3058); I water trough (3881, 3102); S cairn (3853, 3011); S tracks (3764, 3062); A vultures (3771, 2962); I resident (3676, 2967); S cold fire ring (3698, 2871); S marker stone (3614, 2919); I water trough (3553, 2840); S cart with a broken wheel (3498, 2922); A vultures (3462, 2831); I signpost (3373, 2858); S mended fence (3402, 2758); S old boot (3309, 2766); A vultures (3306, 2668); I water trough (3222, 2726); S lost hat (3189, 2636); S cart with a broken wheel (3103, 2684); I signpost (3118, 2587); S tracks (3020, 2582); A vultures (3052, 2486); I door (2969, 2520); S cold fire ring (2922, 2440); S marker stone (2848, 2508)
- _Dust Gulch_: I signpost (2680, 2168); I gate (2840, 2168); I noticeboard (2776, 2208); I water trough (2576, 2240); S cold fire ring (2928, 2248); I bench (2952, 2256); I bench (2736, 2272); S lost hat (2704, 2288); S tracks (2728, 2288); S cold fire ring (2896, 2304); S cart with a broken wheel (2568, 2320); I noticeboard (2768, 2368); S tracks (2688, 2400); I door (2920, 2464); S cart with a broken wheel (2648, 2472); S mended fence (2808, 2472); S cold fire ring (2616, 2512); I door (2624, 2544); S tracks (2752, 2552); I bench (2680, 2624)
- _Ember Way_: I bench (2462, 5182); S cairn (2362, 5128); S tracks (2374, 5240); A steam (2274, 5236); I door (2308, 5324); S cold fire ring (2210, 5321); S marker stone (2172, 5385); I bench (2184, 5475); S cart with a broken wheel (2278, 5471); A steam (2275, 5570); I noticeboard (2356, 5519); S mended fence (2405, 5608); S old boot (2467, 5530); A steam (2513, 5615); I bench (2590, 5557); S lost hat (2614, 5649); S cart with a broken wheel (2687, 5579)
- _Ember forge_: S cairn (2416, 4776); I bench (2464, 4784); I resident (2376, 4808); I bench (2440, 4816); S mended fence (2400, 4824); I gate (2560, 4824); S mended fence (2560, 4856); I bench (2416, 4864); S cairn (2408, 4880); I bench (2504, 4880); I bench (2560, 4880); S cold fire ring (2384, 4912); I water trough (2536, 4928); S tracks (2456, 4936); S marker stone (2504, 4936)
- _Hearthold_: S old boot (2464, 4960); S mended fence (2408, 4968); S cairn (2616, 5000); I resident (2352, 5032); S tracks (2632, 5032); I door (2400, 5056); I gate (2496, 5056); I resident (2536, 5056); I door (2600, 5136); S lost hat (2672, 5144); S cold fire ring (2392, 5176); S cold fire ring (2480, 5176); I gate (2304, 5208); S cart with a broken wheel (2648, 5216); I resident (2520, 5264); I door (2520, 5296); S cold fire ring (2480, 5304)
- _Lode Track_: I bench (2807, 2282); S cairn (2902, 2263); S tracks (2872, 2194); A vultures (2915, 2130); I door (2786, 2092); S cold fire ring (2904, 2128); S marker stone (2933, 2039); I bench (2978, 2008); S cart with a broken wheel (2875, 2004); A vultures (2911, 1984); I noticeboard (2961, 1905); S mended fence (3046, 1964); S old boot (2968, 1907); A vultures (3011, 1839); I bench (2969, 1777); S lost hat (3059, 1751)
- _Palm Spring_: I bench (3440, 2640); S lost hat (3512, 2648); I signpost (3488, 2656); I door (3600, 2712); I resident (3560, 2728); S tracks (3472, 2760); I bench (3416, 2792); I door (3416, 2808); S marker stone (3424, 2808); I bench (3512, 2824); S cart with a broken wheel (3344, 2832); I door (3328, 2872); S lost hat (3432, 2880); S cairn (3368, 2888); S marker stone (3568, 2912); S tracks (3448, 2928)
- _the Lode_: S mended fence (3064, 1528); S cold fire ring (3144, 1568); S old boot (3136, 1576); S lost hat (3008, 1592); S tracks (3128, 1616); S old boot (3144, 1616); I resident (2984, 1624); I bench (3088, 1640); S cold fire ring (2992, 1648); I water trough (3008, 1648); I resident (3104, 1664); I bench (3024, 1672); S lost hat (2976, 1680); I gate (2944, 1688); I signpost (3128, 1696); I bench (3088, 1744)

**Easter-egg spots, reserved** (keep the ground there clear and reachable; nothing is placed yet): fossil in the Amber canyon (2560, 3200); lone palm in the dune sea (1050, 2900); steam cave on Ember (2800, 4300).

## 6. Boundaries, in layers

Every edge has three layers, drawn as the land itself (plan 5.5): **the fade** (walkable ground with clumps that thicken outward, 10 to 160 px), **the wall** (the ground's own three blockers in uneven patches, 64 to 180 px deep, then thinning out again over 160 to 400 px), and **what lies beyond** (drawn, never walked, hazier). Never a line, a ribbon or a checker.

| Edge                                                      | Fade and wall                                                                | Beyond                                                                      |
| --------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| West (the dune sea)                                       | scrub tussocks and low dunes thickening into a dune wall with thorn scrub    | the dune sea, its dust haze thickening westward; a far caravan route        |
| North (the massif above the basin)                        | scree and boulders thickening into crags                                     | the massif's peaks; the Amber and the Willow Run coming out of their gorges |
| Interior (between the Amber, the Willow Run and the Rift) | thorn scrub and boulders in uneven patches, thinning out again behind        | the basin's scrub and mesas, hazier                                         |
| South (the coast)                                         | none on the cliffs: the sea is the edge, with surf; black sand at Cinderwick | the sea and the drowned end of the arc                                      |

## 7. Obstacles, side paths and loops

| Obstacle         | At           | Route          | How it is passed                                                                   |
| ---------------- | ------------ | -------------- | ---------------------------------------------------------------------------------- |
| ravine           | (3890, 3184) | Drover's Road  | side path off the road at a Y about 300 px before, round the far side, back at a Y |
| ravine           | (2003, 4419) | Canyon Road    | side path off the road at a Y about 300 px before, round the far side, back at a Y |
| boulders         | (5165, 4817) | Ash Coast      | side path off the road at a Y about 300 px before, round the far side, back at a Y |
| collapsed bridge | (2680, 2976) | the Amber      | beside the ford: a ruin, not a way                                                 |
| collapsed bridge | (3408, 2776) | the Willow Run | beside the ford: a ruin, not a way                                                 |

Rules: at most one loop in any small area (obstacles at least 800 px apart); side paths never cross their own road; no one-way drops (every shortcut a two-way stair, ramp, ladder, stepping stones or a latch that stays open); an obstacle keeps every touch target at least 44 screen px clear.

## 8. Benchmark checks to hold on the drawn art

The block-out passes all 21 checks of `../research/world-benchmark.md` (plan 2.1). The block-out's markers and materials stand in for props, so the drawn art must hold them again. **Checks 1 and 9 above all:**

- **1. Density.** Each route screen 2 to 3 interactables and 3 to 5 story props; each settlement screen 6 to 10 of each. Here: about 19 screens of route and the settlements in section 2, so at least 37 interactables and 56 story props on the routes, plus 6 of each per settlement screen.
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

- **dry_kit** (Claude D, #137): `steppe`, `scrub`, `hardpan`, `gravel`, `dunes`, `salt_pan`, `badlands`, `wash`; height on the soft grid (`from_cells`, `smooth_tiers`, `Layout`, `draw_faces`, `draw_bands`, `tier_shadows`, `talus`, `rimrock`, `caprock`, `stair`); `oasis`, `pool`, `ditch`, `trail`; `ash`, `old_flow`, `young_flow`, `lava_frames`, `columns`, `causeway`, `cinder_cone`, `fumarole` with `steam_frames`, `hot_spring`, `dead_forest`; the standing things (palms, saguaro, cacti, sage, creosote, bunchgrass, boulders, snags, fireweed); `steppe_to_desert` and `scrub_to_ash`.
- **house kits** (#121): Sunstone timber and adobe for Palm Spring, Dust Gulch and the Lode; Hearthold castle stone for Hearthold and the forge.
- **river_kit** (#133): `river`, `blend` and the meadow grounds for the Rift's green strip in its bays and at its confluences, and for the Ash Coast's green windward shelf.

The kits are on open PRs and land on `main` separately; until then, build against their branches and say which head you used.

## 10. Today's zones: replaced or kept

| Zone today | Becomes      | Where and what                                                                                                                                                                                                                      |
| ---------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| gulch      | kept, placed | Dust Gulch on the Amber's fan: the street of false fronts, the platform and water crane                                                                                                                                             |
| oasis      | kept, placed | Palm Spring, where the Willow Run comes up out of its gravel                                                                                                                                                                        |
| scorch     | replaced     | the ash fields and the Cinder Rise on the Canyon Road's last stretch before the chasm bridge                                                                                                                                        |
| hearthold  | kept, placed | Hearthold on its rock between the flows, with its curtain wall and both bridges                                                                                                                                                     |
| caldera    | replaced     | the Ember forge and the cart bay below the crater (the crater itself is never walked)                                                                                                                                               |
| springs    | kept, placed | Cinder Springs on the seaward flank                                                                                                                                                                                                 |
| (none)     | new ground   | the steppe and the drove road west of the Brackens gap, the Rift and Drover's bridge, the Lode, the Amber canyon, the salt lake, Cinderwick, the dead forest and the Ash Coast; later the Launch Cape's pad, Halcyon and Lumen (P7) |

Places keep their ids where the game uses them (mission places, stops, rings in `lib/world-places.ts`), so saves and missions carry over; their stands move with them.

## v55 overview: proposals for lane D (27 Oct)

The continent overview v55 (`../research/blockout/README.md`, "v55"; Matt's brief of 27 Oct). These are proposals; this brief is unchanged until the lane adopts them.

- **Coordinates**: x 1500 to 4300 is widened by 1.14 and the south by 1.125 (`geo55.P`); the dune sea's outer 458 px run off the canvas's west edge. Dust Gulch goes to (2478, 2420), Palm Spring (3299, 2800), Hearthold (2159, 5272), Cinderwick (2478, 5857).
- **Dust Gulch, large (38 buildings)**: Front Street, the depot and goods yard, Water Street, West Row, the corrals and ore yard, the river gardens on the Amber. **Palm Spring, medium (18)**: round the spring pool and its channels, the caravanserai on the Drover's Road, the date gardens and the north grove.
- **Hearthold, large**: the castle's walls redrawn round the whole rock top with the keep at the crown, Smiths' Row, Gate Street, Ash Lane, Vine Lane and Potters' Lane below the gate, the vines and lower fields. **Cinderwick, medium**: the Strand, Kiln Lane, Ash Lane, the quay and the kilns, across the lower fields from Hearthold. The settled margins: scrub along the dry beds, green along the irrigated Amber and Willow Run.

- Proposal from the v55 town plan (28 Oct): Hearthold authored by hand (`research/blockout/towns/hearthold.json`): the wall round the rock with towers, one south gate and a walled-up west postern for later, the keep, hall, barracks with drill yard and chapel inside, Gate Street to the gate market, Smiths' Row against the cooled lava, and terraced home streets stepping down; 31 buildings.
