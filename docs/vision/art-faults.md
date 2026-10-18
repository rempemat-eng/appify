# Faults Matt found, and the rules they teach

Matt, 19 Oct 00:24 and 00:36: "it just looks attached together but not seamlessly", "there do not need to be boundaries everywhere, only where they need to be for gameplay purposes", "work on the angling of props", "you should also get better at spotting these mistakes". His screenshots are in `faults/2026-10-19/` (numbered as below). Every worker reads this before drawing. Check new work against it before asking anyone to look.

## The faults

| #   | Where                     | What is wrong                                                                                                                                                                                                                                     |
| --- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 01  | Town, Halt, Park borders  | Thin painted strips on the tile lines: a flat hedge with tiny posts, a grey "wall" running down like a pipe, a column of identical bushes. They mark the grid instead of hiding it, and none of them was needed for play.                         |
| 02  | Garden and its neighbours | The ground changes tone in rectangles at tile edges (the woodland's strip is darker, with a straight vertical edge).                                                                                                                              |
| 03  | Woodland spring           | The rock is a dithered oval with no form, the fall a pale rectangle, the bridge a brown block, the fern a flat triangle, the checker shade noisy.                                                                                                 |
| 04  | Woodland clearing         | The clearing is a perfect lighter ellipse. The mushroom ring is a grid of the same mushroom.                                                                                                                                                      |
| 05  | Halt windmill             | Flat tower, thin sails that do not meet the cap, no base or ground contact.                                                                                                                                                                       |
| 06  | Halt farm                 | Fields are flat stripes with slanted, arbitrary edges. Crops are square dots. The wheat is a flat fill. Bales and pumpkins are sparse and float.                                                                                                  |
| 07  | Valley corner             | A whole tile of the same dark canopy (the "beyond" forest): a wall of scale pattern, with nothing to read.                                                                                                                                        |
| 08  | Washing line              | Strung across a path. The sheets are flat squares and the posts are uneven.                                                                                                                                                                       |
| 09  | Anchor                    | Pinned flat on a wall with no reason or mounting.                                                                                                                                                                                                 |
| 10  | Driftwood harbour         | The breakwater is a straight diagonal band across the water. The lighthouse stands in the sea. The jetties end in open water. The harbour is a trapezoid. A pile of black rocks sits at the edge. The sea ends at a straight line against forest. |
| 11  | Harbour bench             | The path runs into a bench and stops. The quay wall's edge is a straight diagonal.                                                                                                                                                                |
| 12  | Headland cliff            | Cliff strata are stair-stepped columns, the same all along, with straight cut sides.                                                                                                                                                              |
| 13  | South sea                 | Flat sea ending in a band of forest canopy: open water cannot end at forest.                                                                                                                                                                      |
| 14  | Sheep field               | Two drystone walls float in the field and enclose nothing.                                                                                                                                                                                        |
| 15  | Park pond                 | A perfect ellipse. A willow stands on a lawn island in the middle. The paved path runs into the water. Planters float.                                                                                                                            |
| 16  | Ice-cream cart            | The parasol is a flat top-down ellipse on a side-view cart, with a lamp growing out of it.                                                                                                                                                        |
| 17  | Park bandstand            | A cage of bars on a slab, with the label over it. Benches face the camera with nothing to look at.                                                                                                                                                |
| 18  | Cogsworth airship         | Drawn side-on but lying on the ground under its mast.                                                                                                                                                                                             |
| 19  | Sparring ring             | A flat disc that the paths run straight through.                                                                                                                                                                                                  |
| 20  | Cogsworth locomotive      | A side view parked over the platform edge. The label covers it.                                                                                                                                                                                   |
| 21  | Clock tower               | Front view only, with a step pasted on the paving and no shadow or footing.                                                                                                                                                                       |
| 22  | Kiosk                     | A box with a lid, seen from a different angle from everything round it, with no detail.                                                                                                                                                           |

Also from Matt: the home hub pops in and out (walking between the garden screen and the world).

## The rules

1. **One ground.** Each region's ground is painted in world coordinates from one painter. Biomes (meadow, forest floor, alpine turf, sand) blend over 60 to 100 px, so no change of tone lines up with a tile edge.
2. **Boundaries only for play.** A border closes only where the world itself would stop you: a cliff or height change, water, lava, a private garden, castle walls. Everything else stays open land. A boundary is a real feature, several deep and uneven: tree clumps with overlapping crowns, a ledge, a bank. It is never a painted strip on the seam.
3. **No perfect shapes in nature.** Ponds, clearings, rocks, fields and coasts get organic outlines with banks, rims and contact shadows. Ellipses and rectangles are for things people made.
4. **One camera angle.** Every prop is drawn in the same three-quarter view as the buildings: top faces visible, front faces lit from the upper left, a contact shadow below. No pure side views (carts, airships, trains) or pure top views (parasols, rings) unless the object really lies flat. Long things run east-west where they can. Things that lie flat (rugs, rings, ponds) are foreshortened to the same angle.
5. **Every object has a reason and a footing.** A wall encloses something. A bench faces a view or a path. A washing line stands in a yard, never across a path. A lighthouse stands on rock. A jetty ends at a boat or a ladder. An anchor lies on the quay or hangs from a post.
6. **Paths lead somewhere.** A path never runs into water, a bench or a wall. It ends at a door, a gate, a bridge, a view or another path.
7. **Water is logical.** It has a source and an outlet, and banks of the right material. It is crossed only on a bridge with dry ends. Sea runs on to the horizon or meets land, never forest canopy.
8. **No repeats in a row.** No column or grid of the same prop, unless people made it so: fences, crop rows, a vine line.
9. **Detail at the right density.** No large flat fills. Every surface has its material: bark, shingle, courses, leaf clusters, ground dressing. The Cainos target, within the mobile limits in `art-style.md`.
10. **World edges.** The camera does not show large areas outside the world. A region's outer edge is a natural limit drawn inside its edge zones (coast, mountains, a forest two or three trees deep). Any empty cell in a region's grid is real scenery that you cannot walk on, drawn with the same care. It is never a filler pattern.

## Checks that catch these

The world lint (`scripts/art/world_lint.py`) reports:

- tone jumps along a tile edge
- long straight lines on a seam
- repeated props in a column
- paths that end in water or against a prop
- large flat areas

Before showing work, look at it at game scale (1 art px = 1.125 screen px), in the browser at 360 px wide, not only as a stitched overview.
