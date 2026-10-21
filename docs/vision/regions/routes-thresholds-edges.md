# The routes, the thresholds and the world's edges

**Owner: Claude G** (lane G, from Claude A on 21 Oct; Matt, 10:03, asked to speed up world building): the routes' chunks (P6), the threshold objects, the world's edges and the land between the regions' footprints (the Lull plain's countryside, the massif's north edge, the east's fens and old forest), and the land beyond the edges. Claude A keeps integration, merging and the cliff core. From the world plan v5.3 (`../world-plan.md`, PR #96).

**The routes as data (lane G, 21 Oct).** Every route below is now a line on the canvas in `scripts/art/world_routes.py`, exported to `lib/world-routes.ts` and checked by `npm run check:world-routes`: its centre line on the 8 px grid, its width and tier at each vertex, each stair, round-end and switchback, its crossings and ways, the thresholds, the side paths and pockets, and the cells where it meets each lane's land. The meeting cells, per lane, are in `route-meets.md`. Inside a footprint the region lane paints the route's surface to that line, width and tier with its own kits; between footprints the route and its land are lane G's, and every threshold object is lane G's. The tier profiles are fewer, deliberate banks rather than the block-out's counts (section 6 below; `route-meets.md` gives both). There are no ramps: Eastward has none (`../eastward-edges.md` 6.3), so a route changes tier by a stair cut through the face, by going round the end of a face where it dies out into the slope (a round-end), or by doubling back round the ends of two staggered faces (a switchback). Section 6's ramps read as round-ends. Coordinates are world pixels on the 11264 x 6912 px canvas. The crop is `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/routes-thresholds-edges.png`.

## 1. The routes

| Route           | Kind   | From and to                    | Walk | Tier changes |
| --------------- | ------ | ------------------------------ | ---- | ------------ |
| Col Path        | path   | (6280, 2960) to (6210, 1890)   | 28 s | 7            |
| High Fells      | path   | (6300, 1760) to (7920, 2390)   | 49 s | 35           |
| Foothill Road   | road   | (6760, 3400) to (7900, 2480)   | 38 s | 17           |
| Towpath         | path   | (8040, 2560) to (8650, 4220)   | 48 s | 9            |
| Lull Road       | road   | (6760, 3760) to (9980, 4360)   | 87 s | 13           |
| Coast Path      | path   | (6660, 4930) to (8640, 4330)   | 56 s | 1            |
| Headland Lane   | path   | (6900, 5110) to (7060, 5620)   | 14 s | 0            |
| Shell Bar       | bar    | (7060, 5640) to (6700, 6080)   | 15 s | 0            |
| Drover's Road   | road   | (5800, 4060) to (2860, 2470)   | 90 s | 22           |
| Lode Track      | path   | (2830, 2330) to (3040, 1700)   | 18 s | 2            |
| Canyon Road     | path   | (2800, 2560) to (2440, 5080)   | 75 s | 28           |
| Forge Stair     | path   | (2470, 5040) to (2465, 4900)   | 4 s  | 3            |
| Ember Way       | path   | (2470, 5120) to (2700, 5620)   | 18 s | 9            |
| Ash Coast       | path   | (5800, 4150) to (2780, 5650)   | 91 s | 7            |
| Delta Road      | path   | (9150, 4320) to (9800, 4985)   | 56 s | 11           |
| Harbour Bridge  | bridge | (9800, 4985) to (10470, 4990)  |      | 3            |
| Old Bridges     | road   | (9980, 4360) to (10340, 4390)  | 9 s  | 0            |
| Quay Street     | road   | (10340, 4400) to (10450, 5320) | 24 s | 6            |
| Beacon Causeway | bridge | (10450, 5320) to (10100, 5440) |      | 0            |
| Cape Road       | road   | (10600, 4950) to (10980, 5520) | 18 s | 3            |

Paths first: the ground is fitted to each route (plan 6.1). Widths vary from 24 to 64 px (wider at bends, views and junction squares). Roads bend irregularly, a short bend every 160 to 240 px on a long swing of 450 to 750 px, never a regular S-ribbon (check 16).

## 2. The thresholds

| Threshold                              | Route         | Sides drawn by      | Mixing band                                                | Landmark                                       | Residents crossing (each way)                                                                                                                         | Radiates from         |
| -------------------------------------- | ------------- | ------------------- | ---------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| **the Col hut** (6290, 2350)           | Col Path      | Claude E / Claude E | meadow, broadleaf, garden → alpine, meadow, broadleaf      | the headwall (6230, 1950)                      | sheep and their shepherd graze up as far as the hut; walkers with staffs; choughs and an ibex on the scree above; the hut warden comes down for bread | the glacier           |
| **the Frostline lip** (6230, 2040)     | Col Path      | Claude E / Claude E | meadow, broadleaf, alpine → alpine, snow, meadow           | the tarn (6200, 1800)                          | the warden and an ice-cutter with a sledge go up; meltwater, and an ibex on the moraine looking down                                                  | the glacier           |
| **the Brackens gap** (5200, 3760)      | Drover's Road | Claude E / Claude D | meadow, field, field2 → steppe, meadow, broadleaf          | the bluffs (5170, 3600)                        | a drover takes his flock out west; his dog ranges ahead; skylarks over the bluffs; a peat-cutter's cart comes in to the valley                        | the Brackens' heather |
| **Drover's bridge** (4330, 3440)       | Drover's Road | Claude D / Claude D | steppe, meadow, broadleaf → scrub, meadow, steppe          | the desert line viaduct (4290, 3720)           | the flock goes on to the far folds; a water-seller crosses to trade; lizards on the parapet; a vulture over the gorge                                 | the Rift              |
| **the Rift ferry** (4180, 5240)        | Ash Coast     | Claude D / Claude D | meadow, broadleaf, sand → deadwood, meadow, blacksand      | the Rift mouth (4250, 5380)                    | the ferryman (he lives here) takes fishers and goats across; terns and a black-sand beachcomber come the other way                                    | the Rift and the sea  |
| **the Amber canyon head** (2770, 2650) | Canyon Road   | Claude D / Claude D | desert, garden, meadow → ash, desert, badland              | the canyon walls (2640, 2950)                  | a mule train comes down from the Lode with ore; orchard hands walk up from the fan; a vulture rides the canyon draught                                | the Amber             |
| **the Cinder Rise** (2270, 3860)       | Canyon Road   | Claude D / Claude D | ash, desert, badland → ash, desert, lavastone              | the plume over Hearthold (2470, 4300)          | prospectors with sample bags go south; ash dust drifts north onto the bushes; a salamander basks on the ridge                                         | the volcano           |
| **the chasm bridge** (2170, 4920)      | Canyon Road   | Claude D / Claude D | ash, desert, lavastone → steppe, ash, scrub                | Hearthold (2480, 5120)                         | carters bring charcoal and ore to the forge; Hearthold's gate guard walks the bridge; steam drifts across                                             | the volcano           |
| **the crust causeway** (3300, 5560)    | Ash Coast     | Claude D / Claude D | deadwood, meadow, blacksand → meadow, deadwood, blacksand  | the flow's steaming toe (3290, 5800)           | charcoal burners from Cinderwick carry sacks west; goats from the coast browse the dead forest's fireweed                                             | the volcano           |
| **the Millrace cutting** (7650, 2740)  | Foothill Road | Claude A / Claude C | broadleaf, garden, meadow → garden, meadow, broadleaf      | Cogsworth's chimneys (7980, 2450)              | miners walk up to the pits; a coal cart comes down; woodcutters from Fernhollow with a timber wagon; crows over the cut                               | the coal seams        |
| **the Cog foot** (8530, 3060)          | Towpath       | Claude C / Claude C | broadleaf, garden, meadow → meadow, watermeadow, broadleaf | the Narrows gorge (8960, 2750)                 | a barge horse and its bargee on the towpath; coal barges go down; a heron fishes the confluence; anglers walk up                                      | the Lull              |
| **Lullford Bridge** (8960, 4310)       | Lull Road     | Claude A / Claude C | meadow, watermeadow, field → watermeadow, reeds, garden    | the swing span (8960, 4310)                    | market carts bound for Neon; the toll keeper on the island; egrets in the shallows; barges wait at the swing span                                     | the Lull              |
| **the canal embankment** (9450, 4680)  | Delta Road    | Claude C / Claude C | watermeadow, broadleaf, carr → garden, meadow, broadleaf   | the falls and the Harbour Bridge (10100, 4600) | market gardeners take produce in; a lock keeper; reed cutters with bundles come out; gulls follow the canal inland                                    | the city              |
| **the Headland stile** (6990, 5300)    | Headland Lane | Claude E / Claude E | meadow, sand, field → sand, meadow                         | the lighthouse (7050, 5600)                    | sheep cross the stile to the fold; the lighthouse keeper; a hare from the cliff turf; sea pinks spill over the wall                                   | the sea               |
| **the Shell Bar** (6900, 5900)         | Shell Bar     | Claude E / Claude C | sand, meadow, field → meadow, sand, field2                 | the wreck (6930, 5870)                         | cocklers walk out at low tide; seals haul out on the bar; terns nest on the islet                                                                     | the sea               |

You draw each threshold object (the hut, the lip's moraine step, the bluffs' gap, the bridges, the ferry landing, the cut, the stile, the bar) and the ambience cross-fade (160 px). The region lanes draw their side of each band.

## 3. The ways

| Way | Where                                                               |
| --- | ------------------------------------------------------------------- |
| W1  | the Headland stile                                                  |
| W2  | the ridge col (rim crossings)                                       |
| W3  | the Millrace landslip (the Cog crossings)                           |
| W4  | the Shell Bar and the ferry                                         |
| W5  | the Rift: Drover's bridge, the mouth ferry, the desert line viaduct |
| W6  | the chasm bridge and the crust crossing                             |
| W7  | Lullford's swing bridge and the maglev                              |
| W8  | the rocket                                                          |
| W9  | the lander                                                          |

The gate check (`gates.json`) closes the ways in order and flood-fills: every step passes with no leak and no crossing outside a way. Keep it as a test (P9).

## 4. The world's edges

Three layers on every edge, drawn as land (plan 5.5): the fade (walkable, clumps thickening outward), the wall (64 to 180 px of the ground's own blockers, thinning out again behind) and what lies beyond.

| Edge  | Wall                                                                     | Beyond                                                                           |
| ----- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| North | the massif: scree, crags, icefalls, glaciers                             | peaks and valley glaciers to the top edge; river gorges running on north         |
| West  | the dune sea: a dune wall with thorn scrub                               | dune ridges, interdune flats, a far caravan route, dust haze thickening westward |
| East  | the moss fens (meres, sinkholes) and the old forest (thicket, old trees) | the forest's giant trees; the Glint coming out of the fens                       |
| South | the sea, with surf; cliffs at the headlands                              | the Tidebloom Isles; far islands on the horizon                                  |

Interior edges (where the walked corridors meet land drawn but not walked) follow the same three layers. The fade is kept 200 px or more from rivers, lava and walls so it never opens a way round them.

**The edges and the land between as data (lane G, 21 Oct).** `scripts/art/world_land.py` (exported to `lib/world-land.ts`, checked by `npm run check:world-land`) classifies every 8 px cell of the canvas outside the footprints: lane G's walkable land (the Lull plain with its coast to Gullwick, and the High Fells' corridor over the massif's shoulder), its fade, its wall, the thin-out and the beyond, each with its ground (meadow, coast, heights, massif, old forest, fens, sea). Who draws what:

- Inside a footprint (or a lane's declared chunk box), the region lane draws its walkable land, its fade and its wall with its biome's own blockers (its brief's section 6).
- Lane G draws everything outside the footprints: the land between, its fade and wall where it meets the beyond, and all of the beyond. From a lane's wall (its box edge) that is the thin-out of 160 to 400 px, then the border proper to the canvas edge, hazier.
- Where a footprint reaches the canvas edge (Sunstone's north and west), the lane draws to its wall and lane G the beyond past it. Until the lane draws that wall, the provisional line in `EDGES` stands; the canvas edge is never the wall.
- On the coasts the sea is the edge: the shore's owner draws its beach or cliff and surf, lane G the open sea past it.

The check holds the layers: no walkable cell of lane G's touches the thin-out or the beyond, and the wall is 64 px or more deep everywhere between them.

## 5. Things on the land between the regions

| Thing           | Kind     | At           | Route      |
| --------------- | -------- | ------------ | ---------- |
| ruined chapel   | ruin     | (8008, 4668) | Coast Path |
| windmill        | landmark | (7280, 4940) | Coast Path |
| standing stones | landmark | (7597, 5215) | Coast Path |
| windmill        | landmark | (7465, 3821) | Lull Road  |
| heron pools     | wild     | (7975, 3940) | Lull Road  |
| hay barn        | landmark | (7139, 3972) | Lull Road  |
| standing stones | landmark | (7745, 4168) | Lull Road  |
| ruined chapel   | ruin     | (8173, 4183) | Lull Road  |
| standing stones | landmark | (8311, 3336) | Towpath    |
| heron pools     | wild     | (8512, 3614) | Towpath    |
| ruined chapel   | ruin     | (8421, 3844) | Towpath    |
| fishing stage   | landmark | (8674, 3898) | Towpath    |

**Secret pockets:** a story detail: an old grave (7093, 3405) off the Foothill Road; a hermit at a fire (6890, 1886) off the High Fells; a story detail: initials cut in a stone (7712, 4158) off the Lull Road; a bench under a tree (7556, 4823) off the Coast Path.

**Obstacles:** felltree (8384, 3465) (Towpath); thicket (7407, 3994) (Lull Road); thicket (7053, 4974) (Coast Path); a willow thicket (9350, 3250) (ring).

**Markers** (62: 19 I, 32 S, 11 A):

- _Coast Path_: A butterflies (6798, 5113); S cart with a broken wheel (7090, 5047); I noticeboard (7184, 5021); S mended fence (7267, 5066); S old boot (7288, 4969); A hares (7357, 5041); I bench (7427, 4980); S lost hat (7453, 5081); S cart with a broken wheel (7524, 5021); I noticeboard (7581, 5100); S tracks (7625, 5009); I resident (8183, 4800); S lost hat (8282, 4795); S cart with a broken wheel (8222, 4717); A hares (8313, 4686); I gate (8274, 4596)
- _High Fells_: A choughs (6815, 1690); I noticeboard (6876, 1685); S mended fence (6914, 1595); S old boot (6978, 1608); A choughs (7059, 1555); I bench (7126, 1611); S cart with a broken wheel (7213, 1615); S tracks (7309, 1698)
- _Lull Road_: S cold fire ring (7093, 3814); S marker stone (7140, 3847); I bench (7150, 3944); S cart with a broken wheel (7224, 3875); A hares (7291, 3941); I noticeboard (7321, 3845); S mended fence (7389, 3913); S old boot (7463, 3854); A hares (7476, 3954); I bench (7555, 3900); S lost hat (7610, 3978); S cart with a broken wheel (7648, 3884); I noticeboard (7720, 3949); S tracks (7784, 3880); A hares (7796, 3980); I gate (7889, 3948); S cold fire ring (7913, 4046); S marker stone (7976, 3970); A hares (8032, 4049); I noticeboard (8106, 3986); S cairn (8111, 4085); S tracks (8206, 4065); I gate (8202, 4168); S old boot (8287, 4124)
- _Neon Harbour_: I water trough (10472, 3832); S lost hat (10464, 3856)
- _Towpath_: I noticeboard (8425, 3317); S tracks (8518, 3364); A hares (8452, 3431); I gate (8532, 3488); S cold fire ring (8439, 3518); S marker stone (8482, 3608); A hares (8390, 3645); I noticeboard (8477, 3689); S cairn (8431, 3774); S tracks (8525, 3791); I gate (8449, 3856); S old boot (8509, 3932)

## 6. Tiers on the routes

The Lull plain walks tiers 2 to 11 in three deliberate banks (v5.2), with ramps along the river terraces (11) and a few stairs (4). The High Fells walk the massif's shoulder with ramps along benches; the Col Path climbs in switchbacks.

## 7. Benchmark checks on the drawn art

All 21 checks of `../research/world-benchmark.md`, above all 1 (density on every route screen), 2 (no 200 px without something to notice), 9 (no more than three identical props in a row) and 16 (a bend or obstacle every 200 to 300 px; no straight run over 240 px).

## 8. Kits

- **river_kit** (#133) for the plain's fields, hedgerows, farm tracks, fords and water meadows, and `blend` for every band.
- **dry_kit** (#137) for the edges and routes in the dry country where they meet Claude D's land.
- **house kits** (#121) for the huts, the toll house and the threshold buildings.

## 9. Today's zones

None of today's zones lie on the routes' land; the journeys (train, maglev, ferry, cart) become shortcuts beside the routes they run along (plan 6.2).
