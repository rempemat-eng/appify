# Placement logic: every object has a reason (Matt, 2 Nov)

Matt, 2 Nov: "think deeply about parts of the game like fences. where would they be? what would they fence in?"

Every placed object answers four questions before it goes in: **what is it for, who owns or uses it, why is it here and not elsewhere, and how do people reach it.** If a piece can't answer all four, it isn't placed. The ground rules ([ground-rules.md](ground-rules.md)) cover the physics: on the grid, not on water, not on paths. This page covers the sense.

## Fences, walls and hedges

A boundary exists to keep something **in**, keep something **out**, or **mark** whose land it is. It always has an entrance, and that entrance connects to the path its owner walks.

| Purpose                  | What it encloses                                                                                                               | Where it occurs                                                 | Form                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Keep animals in          | A paddock, sheep fold, goat pen, chicken run or pigsty, **with its animals inside**, plus a trough, a water source and shelter | Farms, town edges, the back of cottages; never in a town square | Post-and-rail (horses, cattle), wattle hurdles (sheep), low mesh or wattle with a coop (chickens)                                               |
| Keep animals or deer out | A kitchen garden, orchard or nursery beds                                                                                      | Beside or behind homes; orchards at village edges               | Wattle, picket, or a hedge with a wicket gate                                                                                                   |
| Front garden             | Flowers and a path to the door                                                                                                 | Cottages on village lanes. The gate sits **on** the door path.  | Low picket or a low stone wall                                                                                                                  |
| Field boundary           | Crop fields and meadows                                                                                                        | The countryside around villages and farms                       | Hedgerows in the valley and lowlands. Dry-stone walls on the Frostline, the massif and Highgarth's terraces. Rail only where wood is plentiful. |
| Property and yard        | Work yards, inn yards, depots                                                                                                  | Behind shops and smithies, at stations                          | Plank fence or a stone wall with a wide cart gate                                                                                               |
| Danger                   | Cliff edges, quays, mine shafts, lava, the launch pad                                                                          | Viewpoints, docks, the fire country, Launch Cape                | Rail or rope on posts; railings in towns                                                                                                        |
| Control                  | The Company's yards, the closed pass, the knights' walls                                                                       | Neon Harbour, the craters, Highgarth's pass, Hearthold          | Iron railings, mesh and barbed fences (the Company); stone walls (castles); a timber barrier (the pass)                                         |

**Rules**

1. A boundary is a closed loop, including any building walls or water it uses as a side, or it is a line between two things it separates. Isolated stretches that guard nothing are not allowed.
2. Every enclosure has a gate or stile on the side its users come from, joined by a path. Where a public path crosses a field boundary there is a stile or kissing gate, not a gap.
3. What it holds must be visible: animals in pens, crops in beds, goods in yards. An empty pen is a story beat (the flock scattered), not decoration.
4. Its size fits its contents: a chicken run is 3 to 4 cells, a sheep fold 6 to 10, a horse paddock 10 or more.
5. The material follows the region and the owner's wealth (see the table). The style follows the town's tech level.
6. A fence is broken only for a reason. In storm-broken Crossroads, broken fences, missing rails and toppled gates are part of the restoration: they mend as the village recovers. That makes them a visible sign of progress.

## Other objects, by the same test

| Object                    | Why it exists                    | Where it goes                                                                               | Never                                                         |
| ------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Bench                     | Rest, a view, waiting            | Beside paths at views, on squares, by doors, at stations and stops                          | On a path, facing a wall, alone in the wilds without a view   |
| Lamp                      | Light where people walk at night | Along town streets, at junctions, gates, quays and stations                                 | On wells, in wild woods (except a waystone or a camp lantern) |
| Shard lantern             | It holds the shards: the thing the town was built round, and what a raid comes for | At the heart of its square, as one of a pair with the well: either side of the square's middle walk, each on its own ring of setts, open paving all round both (Crossroads, 13 Nov) | On another prop's apron or under its reach (the well's ring, its crank); among street furniture, where it reads as a lamp |
| Signpost                  | Choosing a way                   | At junctions only, pointing down real routes                                                | On straight paths, or pointing at nothing                     |
| Well or pump              | Water for homes                  | Village squares, farmyards, the oasis                                                       | Beside a river that is easier to draw from, or in the wilds   |
| Woodpile                  | Fuel for a hearth                | Against the gable wall or under the eaves of a house with a chimney, or by a smithy or kiln | Away from any hearth                                          |
| Barrels, crates, sacks    | Goods being stored or moved      | By shops, inns, docks, stores and carts                                                     | Scattered on lawns or blocking doors                          |
| Trough                    | Animals drink                    | Inside pens and paddocks, by stables, at the inn's horse rail                               | Without animals nearby                                        |
| Hay                       | Animal feed                      | Barns, paddocks, hay fields, carts                                                          | In town centres                                               |
| Cart or wagon             | Moving goods                     | At barns, markets, depots, roads, beside a horse                                            | Inside buildings or on rooftops                               |
| Bridge                    | A path crosses water             | Exactly where a route meets a river, sized to the route's width                             | Where no path leads                                           |
| Washing line              | Laundry                          | Between a house and a post in its yard, in residential streets and the Lanes                | In shops or work yards                                        |
| Planters and flower boxes | Care for a home                  | Under windows, by doors, in front gardens                                                   | On roads                                                      |

## For the editor and the checks

- Every piece's data gains a **purpose** (contain, exclude, mark, rest, light, store, feed, cross, guide, work) and **requires** what that purpose needs: a pen requires animals, a trough and a gate; a woodpile requires a hearth within 2 cells; a signpost requires a junction; a lamp requires a route.
- `rules.fences` already rejects open runs. It extends to require an entrance joined to a path, contents that match the purpose, and a size that fits the contents.
- Codex encodes these rules in the piece schema and kit_rules, and they run in check:kit (task Y48).
