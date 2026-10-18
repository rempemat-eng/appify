# World rules: what the world means, and what follows from it

Matt, 18 Oct: "create some sort of protocol / system to spot visual and especially logical bugs in the world … figure out what it means for a part of the world to be water and what that means for objects on water … try not to build each section of the world completely separately … really hone in on game fundamentals and logic and what follows in terms of world building and detail."

This file is the rulebook for every zone generator (`scripts/art/zones.py` and the regional prop modules) and for the checks that guard them. It turns the research in `docs/research/2d-world-design.md` into rules for this repo. Where a rule is an inference rather than a sourced pattern, the research report says so; the numbers here are starting points to tune in play.

## 1. Every pixel has a meaning

Each zone is built from a **semantic layer** before any art: every cell of the zone (the 4 px walk cell) belongs to exactly one terrain class, and props, the walk grid, tap routing and decoration all read that layer. The generator records it (`zoneTerrain` in `lib/zone-maps.ts`, run-length encoded like the walk grid) so checks and the app can use it.

| Class             | Code | Walk | What may stand on it                                                                                                                   | Must border                               | Details derived from it                                          |
| ----------------- | ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------- |
| Deep water        | `~`  | no   | only **floating** props (boats, buoys, ducks, lily pads in still water) or **supported** structures (jetty, bridge, mill wheel, piles) | bank, beach, quay or bluff; never lawn    | dark band under the near bank, glints, bob animation on floaters |
| Shallow water     | `-`  | no¹  | reeds, stepping stones, wading birds                                                                                                   | deep water on one side, bank on the other | reeds where still shallows meet a bank, ripples round stones     |
| Bank / beach      | `,`  | yes  | wet-tolerant props (hauled-up boats, nets, driftwood, deck chairs on dry sand)                                                         | water on one side                         | wet band at the waterline                                        |
| Cliff / bluff     | `^`  | no   | nothing (roots and strata are part of the face)                                                                                        | a top tier and a bottom tier              | lit lip on top, cast shadow down-right                           |
| Ground            | `.`  | yes  | most ground props of the region                                                                                                        | anything, through a blend band            | darker under canopy, worn where paths say traffic flows          |
| Path              | `=`  | yes  | nothing in the walking band; lamps, signs, benches beside it                                                                           | a **node** at each end (see 3)            | lamps on grade-1 paths only, wear, puddles in hollows            |
| Floor / plaza     | `#`  | yes  | stalls, benches, wells, statues                                                                                                        | paths that lead to it                     | worn centre, drains                                              |
| Snow / sand / ash | `*`  | yes  | that region's props only (`REGION_PROPS`)                                                                                              | the next class on its gradient (see 4)    | footprints on paths (snow), ripples (sand), cinders (ash)        |
| Lava              | `!`  | no   | only stone bridges and supported structures                                                                                            | a crust or ash band, never vegetation     | glow, crust at the edges; flows downhill from a vent             |
| Building          | `B`  | no   | its own sprite                                                                                                                         | a door facing reachable open ground       | window glow at night, chimney smoke if a hearth is inside        |
| Rail              | `R`  | no²  | trains, buffers, signals                                                                                                               | a platform at a station                   | sleepers, ballast                                                |
| Off-map           | ` `  | no   | the old forest (`beyond()`), the sea, the void of space                                                                                |                                           |                                                                  |

¹ Walkable only over a drawn ford or stepping stones. ² Crossable only at a level crossing.

**Being water** therefore means three things at once. The companion cannot stand there. Anything drawn there either floats (it bobs, it can only drift with the flow) or stands on supports drawn entering the water. And every body of water belongs to a network with a **source** and a **sink**: a spring, a fall or a culvert upstream; a larger water, the sea or an explicit off-map exit downstream. A tap on something over water walks the companion to the nearest standing point on a bank, jetty or bridge, and that point must exist and be reachable. A bridge spans exactly the water beneath it, and both ends land on a path that continues to a node.

## 2. Props have a placement type

Every prop key in the generators gets one placement type (`PLACEMENT` in `zones.py`). The lint checks each prop's footprint against the classes beneath it.

| Type        | Footprint must sit on                            | Examples                                          |
| ----------- | ------------------------------------------------ | ------------------------------------------------- |
| `ground`    | ground, floor, snow/sand/ash (its region's)      | trees, benches, houses, stalls, rocks             |
| `wet`       | bank or beach (may touch water)                  | nets, hauled boats, driftwood, reeds              |
| `floating`  | deep or shallow water only                       | boats, buoys, ferry, narrowboat, lily pads        |
| `supported` | water or a gap, with drawn supports at the edges | jetty, bridge, lighthouse on its rock, mill wheel |
| `edge`      | along a frame (fence, hedge, wall)               | fences, hedges, walls, gates                      |
| `overhead`  | anywhere (drawn above, never blocks)             | bunting, cables, drones, steam                    |

A `ground` prop on water is a bug; a `floating` prop on grass is a bug; a `supported` structure with no drawn support is a bug.

## 3. Places are nodes joined by graded paths

A zone is a small Lynch map: **one landmark** visible from where you enter; a **frame** of edges on all four sides made of materials that belong there (water, bluff, hedge, treeline, fence, wall); **one clearing or square** kept mostly empty as its node; and **paths in at most three grades**.

- Grade 1 joins the zone's exits and its main node. It is the only lit path at night.
- Grade 2 branches end at a door, bench, jetty, bridge, gate or stall.
- Grade 3 is a worn desire line between two nodes.

**Every path ends at a node.** A path that runs into open grass is a dead end; a path into an unbroken frame is a wall. **Every exit is a break in the frame that a path runs through**; a gap with no path reads as a hole. A gate sits in a continuous fence or hedge, the main path runs to it, the same road continues on the far side, and a lamp or sign marks it. Trees frame a gate; they never stand in its line.

Props cluster into two to four vignettes, each tied to a node (a doorstep, a jetty, a stall) and explicable: for every prop, someone can say who put it there, what for, and how one reaches it.

## 4. Neighbours are built together

A zone is a slice of its region, not a scene on a blank canvas.

- **Elevation is explicit and monotone.** Each region has tiers. The valley runs ridge (highest) → woodland and garden → town → harbour at sea level. Tiers change only at a cliff, bluff, slope or stair, and a stair or ramp always carries a path. Water flows only downhill and drops a tier at a waterfall.
- **Climate grades.** Classes meet only along an allowed-contact list: snow → alpine meadow → grass; sand → scrub → grass; lava → crust → ash → fireweed; deep water → shallow → bank → ground. Snow touching sand, lava touching grass or deep water touching lawn fails the build.
- **Edges continue across seams.** Roads, water, bluffs, rails, fences, hedges and treelines that reach a border continue in the neighbour on the same line and width, or end at a visible terminal (a post, a corner, a gatepost) inside the zone. The ground tone in the two zones' shared strip matches; palette and light drift across a region, they never switch at a border.
- **Districts change at nodes, not at screen edges.** A zone border falls inside a stretch of shared character; the gate, the bridge or the square is where the character changes.
- **The valley has loops**, not just spokes from the garden: at least two walking loops (for example riverside → park, and woodland → halt), so the outer zones join each other.

## 5. Transitions are corridors, not tubes

Where two places meet, the border is a **corridor**: each zone contributes a band of about 120 to 200 px next to the shared edge, so the transition is half to two-thirds of a screen of continuous walking. Inside it:

- the walkable width narrows to two or three companion widths (never below the 44-pixel tap rule) and **varies by about a third** along its length;
- at least one side is **permeable for half its length** (a low wall, a fence, a hedge with gaps, a bank above water, a drop to a lower tier) so the player sees beyond it;
- the path **bends once**, which also holds back the next view;
- it has **one pause** (a bench, a signpost, a stile, a viewpoint);
- the **next landmark shows before the seam** (a tall prop may rise 48 px over a north border);
- the ground and edge props **blend** the two districts along its length.

Valley corridors to build first: the garden's south gate lane into Crossroads Town, the ridge trail through the treeline, the halt's west lane, and the cliff path from the harbour to the castle with the sea as its open side.

## 6. Detail follows from the logic

The generators work in passes, each reading the layers the passes before it wrote, so detail is a consequence rather than a placement:

1. **Terrain and elevation** (classes, tiers, the water network with flow).
2. **Structure** (the path graph with grades and nodes, building footprints with doors, frames and corridors).
3. **Props** (landmark, vignettes at nodes, frame plantings), each with its placement type.
4. **Derived detail**, from rules only:
   - banks, beaches and foam where water meets land; reeds where still shallows meet a bank; a waterfall where flow crosses a tier;
   - worn grass and desire lines along the path graph's traffic; puddles in path hollows;
   - lamps along grade-1 paths and at gates and doors;
   - cast shadows and lit lips from height and the upper-left light;
   - moss and damp on shaded faces; footprints on snowy paths; crust and ash bands round lava;
   - chimney smoke from buildings with a hearth; window glow at night (already derived: `zoneWindows`);
   - small ground dressing (`dress()`) only on untouched open ground, never in a corridor's walking band.

**Overrides are declared.** When a rule must be broken on purpose (the lighthouse stands on a rock in deep water), the exception lives in one table next to the generator (`OVERRIDES` in `zones.py`) with the zone, the object, the rule it exempts and the reason. The lint fails if an override has no reason, or if the exempted rule would now pass without it, so stale exceptions disappear.

## 7. The bug protocol

Two families of bug, named so reviews can be specific:

- **Visual:** seams at borders, palette jumps, shadows that disagree with the upper-left light, z-order errors, scale mismatches, cut-off sprites, dark holes.
- **Logical:** physical impossibilities (a ground prop on water, water with no source, lava uphill), access impossibilities (an unreachable door, a bridge to nowhere, a tap target with no standing point), purposeless objects (a gate in no fence, a path ending in grass, a lamp on an unlit lane), causal contradictions (a dry well beside a full trough, a hearth with no chimney, snow outside the ridge).

Four stages, every time a zone changes:

1. **Logic lint** (automatic, in the generator and `npm run verify`): the checklist below. `scripts/art/world_lint.py` runs at the end of every `zones.py` build and prints its findings (checks 1, 2, 6 and 10 so far; report only until the valley is fixed). It reads each walk cell as a class: a blocked cell is water when blue, lava when orange, else wall; an open cell is path when drawn in the path colours, else ground. The classes and placement types are exported as `zoneTerrain` and `zonePlacement` in `lib/zone-maps.ts`, so `check:world-logic` (C23) can test the same data.
2. **Stitched region render**: `LINT_OUT=<folder> python3 scripts/art/zones.py` writes `world-lint.txt` and each region drawn whole (`region-<id>.png`, zones in place, findings boxed in red), reviewed for rivers, roads, fences and tone across seams, and for what you see from each entry edge.
3. **"Why is this here" pass**: every prop answers who put it there, what for, and how you reach it.
4. **Play-test** (AGENTS.md): normal and reduced motion, day and night, interrupted walks, overlapping props; plus walking every corridor and tapping every prop near water.

| #   | Check                                                                                                      | Automatic |
| --- | ---------------------------------------------------------------------------------------------------------- | --------- |
| 1   | Every prop's footprint sits on a class its placement type allows                                           | yes       |
| 2   | Floating props sit on water; supported structures have drawn supports                                      | yes       |
| 3   | Every water body has a source and a sink (or a declared off-map exit); flow never runs uphill              | yes       |
| 4   | A river that must read as a barrier is at least 3 cells wide                                               | yes       |
| 5   | Every bridge spans water or a gap, and both ends land on a path that reaches a node                        | yes       |
| 6   | Every path ends at a node                                                                                  | yes       |
| 7   | Every exit is a break in the frame with a path through it                                                  | yes       |
| 8   | Elevation changes only at cliffs, slopes or stairs, and stairs carry a path                                | yes       |
| 9   | Terrain contacts appear only on the allowed-contact list                                                   | yes       |
| 10  | Borders continue: roads, water, bluffs, fences, treelines; matching ground tone in the shared strip        | yes       |
| 11  | Every door faces reachable open ground; every interactive prop has a reachable standing point              | yes       |
| 12  | Tap targets are at least 44 screen px and do not overlap at standing distance                              | yes       |
| 13  | Lamps only on grade-1 paths, gates and doors                                                               | yes       |
| 14  | Region-only props outside the valley                                                                       | yes       |
| 15  | One landmark per zone visible from its entries; a mostly empty node                                        | partly    |
| 16  | Corridors: width varies, one side permeable, one bend, one pause, next landmark visible before the seam    | partly    |
| 17  | Shadows and lit edges agree with the upper-left light                                                      | partly    |
| 18  | Every override has a reason and still exempts something                                                    | yes       |
| 19  | Every prop passes "who put it here, what for, how do you reach it"                                         | review    |
| 20  | Motion is finite, reduced-motion safe, stops when inactive; interrupted walks never trigger stale arrivals | harness   |

## 8. Order of work

1. Record the semantic layer and placement types in the generators; run the lint as a report.
2. Fix the valley against it: the water network (where the stream rises, where it reaches the sea), the harbour and castle seam, the garden gate lane, the ridge trail, the halt lane, the cliff path, two loops.
3. Make the lint fail the build; then apply it to the other regions one at a time.
4. Move derived detail (section 6) into rules, region by region, deleting hand placements as rules replace them.
