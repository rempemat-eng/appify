# Props across all regions

**Owner: Claude B** (lane B, the prop library: B6, P4). Every prop the region briefs ask for, gathered in one list so the library can draw each once, to the size guide and #97, and the lanes can reuse them. From the world plan v5.3 (`../world-plan.md`, PR #96). The crop is the whole content map: `/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/worldplan5/briefs/props.png`.

## 1. Props the routes and thresholds need (P4)

the Col hut, cairns, sheepfolds and the well, the Millrace wheel, Lullford's swing span, the Narrows Viaduct's piers, the Harbour Bridge's arches, windpumps, the chasm bridge, the crust causeway, the Rift ferry and its landing, the Headland stile in its drystone wall, the toll house on Lullford's island, a moraine step at the Frostline lip, signposts at every junction, the rocket.

## 2. Markers: what each slot can hold

| Type         | Slots | Names (count)                                                                                                                                                                                                                                                                                                                                  |
| ------------ | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| interactable | 347   | bench (73), gate (53), noticeboard (52), water trough (49), door (47), resident (42), signpost (31)                                                                                                                                                                                                                                            |
| story        | 442   | tracks (65), marker stone (63), cart with a broken wheel (57), cold fire ring (55), cairn (54), mended fence (54), old boot (47), lost hat (47)                                                                                                                                                                                                |
| ambient      | 92    | the home valley: butterflies (8); the massif and the Frostline: choughs (7); the coal hills: moths (7); the Lull plain: hares (18); the river belt and delta: egrets (4); Neon Harbour: cats (6); the coast and the isles: terns (3); the steppe and the Brackens: sheep (11); the Sunstone basin: vultures (15); the fire country: steam (13) |

Each slot can take another prop of the same type that fits its ground; draw at least three variants of each common prop (benches, signposts, fences, cairns) so no more than three identical props stand in a row (check 9).

## 3. Named things, by region

| Region                                          | Lane     | Named things                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The home valley, the Frostline and the Brackens | Claude E | wayside shrine (2), well, beehives, cairn, ibex rocks, crevasse viewpoint, herders' shieling, picnic viewpoint, scarecrow, old oak, hay barn, tide pools, seal rocks, stile and bench, sheepfold, shepherd's hut, drove well, haymakers' shelter, a tumbled field barn, a hare form in the long grass, a fallen climbers' camp, a broken sheepfold, a cliff-top view to the isles, a beachcomber's camp, a wreck on the rocks |
| Cogsworth, the coal hills and the Narrows       | Claude C | fallen climber's camp, echo cave, cairn, windmill, pit head, collapsed adit, charcoal burners' camp, rail ruin, tram tipple, lookout over the Narrows, a crow roost in a dead pine, a terrace edge over the loops, an eel-catcher's camp, a tor                                                                                                                                                                               |
| Neon Harbour, the delta and the Lull belt       | Claude C | fishing stage (2), reed hide, stilt hut, eel traps, fish market, rope walk, heron pools, hay barn, ferryman's hut, wreck in the reeds, harbour master, funicular station, street shrine, a reed hide over the channels, a stair-top view over the ria, an old harbour crane, a gull rock                                                                                                                                      |
| The Tidebloom Isles and the Shell Bar           | Claude C |                                                                                                                                                                                                                                                                                                                                                                                                                               |
| The Sunstone basin and the fire country         | Claude D | fumarole field (3), hare warren (2), barrow mound (2), caravan camp (2), wind pump (2), wagon wreck (2), rock arch (2), cliff shrine (2), bone yard (2), lizard rocks (2), obsidian scree (2), lava tube mouth (2), ruined watchtower (2), steam pools (2), cinder shrine (2), mirage viewpoint, lone pine viewpoint, sheepfold, shepherd's hut, drove well, a rise over the flows, a sulphur-gatherer's camp, a lone tree    |
| Routes, thresholds and edges                    | Claude A | standing stones (3), ruined chapel (3), heron pools (2), windmill (2), fishing stage, hay barn                                                                                                                                                                                                                                                                                                                                |

## 4. Obstacles and border blockers

Obstacles: thicket, fallen tree, boulder field, ravine, marshy pool, scree slope, driftwood pile, spoil heap, collapsed old bridges by the fords. Border blockers per ground (each in three or more variants and sizes, mixed in uneven patches):

| Ground           | Fade clumps                   | Wall                             |
| ---------------- | ----------------------------- | -------------------------------- |
| woods            | thicket, bramble, fallen tree | thicket, old trees, fallen tree  |
| grass and fields | gorse, bramble, boulders      | thicket, gorse, bramble          |
| dry country      | thorn scrub, boulders         | thorn scrub, boulders, low dune  |
| dune sea         | scrub tussock, low dune       | dune wall, thorn scrub, boulders |
| heights          | boulders, scree               | scree, boulders, crag            |
| snow             | scree, crag                   | crevasse, crag, scree            |
| ash              | boulders, aa rubble           | aa rubble, boulders, scree       |
| fens             | pool, bramble                 | mere, sinkhole, bramble          |
| beach            | driftwood, boulders           | boulders, low dune, driftwood    |

## 5. Rules

- Sizes from the size guide (#124): an adult is 25 px.
- The house palette and kits (#121); Eastward's detail at the same character height (`../art-style.md`).
- Prop logic (#97): every prop has a reason to stand where it is and a footing.
- No decoration gives a reward, a cost or a chore.
- Touch targets at least 44 screen px; props near the companion keep their hit areas usable.
