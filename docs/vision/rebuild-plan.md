# Rebuilding the whole world to one standard

Matt, 20 Oct 20:54: "Can you make absolutely sure the whole map adheres to the highest level of detail, the soft grid etc. specified. not just individual sections but everything." Earlier the same evening he rejected a patched summit ("non of this looks natural (given the soft grid), there is no verticality, hard edges") and asked that no old asset be reused unless it fits the newest standard (AGENTS.md, "Keep the design coherent").

This plan makes sure every square of the world is rebuilt to that standard and none is left old. It sits on the world plan v5.3 (`world-plan.md`) and the region briefs (`regions/`).

## 1. The standard, and how it is checked

One standard for every pixel the player sees, on the walkable land and beyond it:

- **The soft grid:** structure on the 8 px grid; terrain in tiers of 32 px with faces on south edges only, 5 px side bands lit west and dark east, constant shadows; ramps, stairs and switchbacks wherever a route changes tier (`verticality.md`, the terrace toolkit).
- **Eastward's level of detail:** every surface passes the detail bar for its kind under the house rulings, cleanliness included (`house-style.md`, section 7).
- **The house style and palette**, the outline rule and upper-left light.
- **The size guide** for every sprite (`size-guide.md`).
- **Logic:** every part has a reason and a way it is built (`prop-logic.md`, `world-rules.md`).
- **No hard edges:** no straight boundary between ground kinds longer than 96 px without a jog, nothing cut by a cell, zone or tile edge, layered edges at the world's borders (the benchmark, `research/world-benchmark.md`).
- **The benchmark's 21 checks**, held again on the drawn art.

Two checks enforce it:

- **The asset ledger** (`asset-ledger.md`, `npm run check:assets`, on `claude-a/asset-ledger`) grades every existing asset KEEP, REWORK or RETIRE. A rebuilt region may use only KEEP assets or finished REWORKs.
- **The whole-world audit** (`npm run check:world`, on `claude-a/world-audit`) measures every 32 px cell of the world against the standard and draws a heat map. A region is marked rebuilt only when every one of its cells is green, and from then on the check fails if any cell slips.

## 2. Every square has an owner

The 11264 x 6912 px canvas is covered without gaps:

| Part of the world                                                                                                                                                                                                             | Owner    | Brief                                                     |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------- |
| The home valley, the garden's surroundings, Fernhollow's approach, the Frostline and its cirque, the Col path, the Brackens to the gap                                                                                        | Claude E | `regions/home-valley-frostline-brackens.md`               |
| Cogsworth, the coal hills, the Narrows gorge and viaduct, Fernhollow                                                                                                                                                          | Claude C | `regions/cogsworth-coal-hills-narrows.md`                 |
| Neon Harbour, the Heights, the docks, the delta, the Lull belt, Lullford, Gullwick, the Skyport, the Cape Road                                                                                                                | Claude C | `regions/neon-harbour-delta.md`                           |
| The Tidebloom Isles and the Shell Bar                                                                                                                                                                                         | Claude C | `regions/tidebloom-isles.md`                              |
| The Sunstone basin, the Rift, the steppe beyond the Brackens gap, the fire country, the Ash Coast, the Launch Cape pad                                                                                                        | Claude D | `regions/sunstone-basin-fire-country.md`                  |
| The routes, the thresholds, the plain's countryside between regions, the world's edges (the massif and its glaciers, the dune sea, the fens and the old forest, the southern sea), the land beyond the edges, the in-game map | Claude A | `regions/routes-thresholds-edges.md`                      |
| Every prop in every region                                                                                                                                                                                                    | Claude B | `regions/props.md`                                        |
| The garden and the hut                                                                                                                                                                                                        | Claude B | the garden stays its own scene, held to the same standard |

## 3. The kits

Each region is painted from kits built on the soft grid, so the standard is built in rather than added afterwards:

| Kit                            | For                                                                 | Owner    | State                                       |
| ------------------------------ | ------------------------------------------------------------------- | -------- | ------------------------------------------- |
| Terrace toolkit and detail bar | every tier, face, ramp and stair                                    | Claude A | #90, waiting for Matt                       |
| House style and kits           | buildings in every setting, colourways                              | Claude A | #121, waiting for Matt                      |
| Size guide                     | every sprite                                                        | Claude A | #124, waiting for Matt                      |
| River and meadow kit           | rivers, streams, fords, canals, meadows, fields, hedges             | Claude E | #133                                        |
| Dry and fire kit               | steppe, desert, dunes, mesas, canyons, oases, ash, lava, basalt     | Claude D | #137                                        |
| Mountain and snow kit          | massif, cliffs, cirques, cols, glaciers, icefalls, snow             | Claude A | pilot on `claude-a/mountain-kit`            |
| Coast kit                      | sea cliffs, beaches, shingle, rock pools, surf, harbours' sea walls | Claude C | to build                                    |
| Forest kit                     | woodland, forest edges, clearings, the old forest's border          | Claude E | to build                                    |
| City kit                       | streets, quays, stairs between levels, the falls in the city        | Claude C | to build, from facade.py and the house kits |
| Fen kit                        | moss, bog pools, sinkholes, boardwalks                              | Claude A | to build                                    |
| Tropical kit                   | the isles' shores, palms, lagoons, reefs                            | Claude C | to build                                    |
| Edge kit                       | the three layers at every border, haze beyond                       | Claude A | to build                                    |

Kits share one core (plots, clusters, outline, shadow, blending) once #90 and #121 land: `scripts/art/kit_core.py`.

## 4. The order

**Wave 0, the ground to build on.**

1. The tools land on main: #90 (terrace toolkit and detail bar), #121 (house style and kits), #124 (size guide). These are Claude A's PRs and wait for Matt's merge or his word that Claude A may merge them.
2. The asset ledger and the whole-world audit land.
3. The mountain kit pilot is shown to Matt. Its look, once he approves it, is the reference for every other kit.
4. The world canvas renderer (#123, #126) lands behind its flag, so rebuilt regions can be walked while the old zones stay the default.

**Wave 1, one whole region as proof.** The home valley with its routes, thresholds and edges, built on the canvas from its brief and kits, walked in the browser at phone size, 100 % green on the audit, shown to Matt.

**Wave 2, everything else in parallel by lane,** each region from its brief, each done only when it is 100 % green and Matt has seen it:

- Claude C: Cogsworth and the coal hills, then Neon Harbour and the delta, then the isles.
- Claude D: the Sunstone basin, then the fire country.
- Claude E: the Frostline and the Brackens after the valley.
- Claude A: the routes and thresholds between them, the world's edges and the land beyond, the in-game map.
- Claude B: the props each region's brief lists, redrawn where the ledger says REWORK, in the order the regions need them.

**Wave 3, the switch.** When every region is green, the world canvas becomes the default, Codex migrates saves to world points, and the old zones and their generators are retired.

## 5. Meanwhile

The old zones stay playable until their region is switched. Only faults that break play (walkability, logic) are fixed there. No look-patches go into old ground, terrain or scenery.
