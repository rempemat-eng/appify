# Biome brief: the delta (wetland)

Owner: Claude I. This is the one-page brief that `rules-system.md` section 4 asks for before a new biome gets its JSON and edge set. The biome is used in the Lull delta and on the Lull's water meadows (`art/regions/lull-delta.json`), and its creeks run into Gullwick's coast (`art/regions/gullwick.json`).

The biome becomes `scripts/art/biomes/delta.json` and an edge set in the kit once the woodland golden has cut kit v1. Nothing here is drawn yet; the frozen painter (`scripts/art/regions/lull_delta.py`) only tried some of these ideas at 1x.

## Why it is its own biome, not the meadow

The meadow's edge is a turf bank: sod overhangs a dry earth face.

The delta has almost no dry edges.

- Land meets water at a low wet margin, 12 px at most: mud and roots under a fringe of reeds, never a sod lip.
- The ground between the arms is wet: water stands in pools.
- The walls that stop the walker are reed beds and soft mud, not faces.

Borrowing the meadow's bank and recolouring it is exactly what `check_biomes` refuses.

## Edges (what differs from the woodland and the meadow, and why)

| Edge                 | Delta                                                                                                                                                              | Eastward reference (geometry only, `eastward-edges.md`) |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| Water's edge (arms)  | No lip and no face. A 2 to 3 px band of wet mud, a dark waterline, then reed stems standing in the shallows, one clump every 16 to 32 px (rule 8)                  | the swamp shot (15) and the bank rule 5.3, no foam      |
| Low ledge            | 12 px mud bank (peat and clay courses, roots, a wet dark foot). Used only where a creek cuts the marsh                                                             | rule 2.2's low ledge, with a mud face in place of earth |
| Terrace edge (32 px) | Only where the floodplain steps down to the delta. It is the meadow's bank, seen from the delta side, so it belongs to the meadow's edge set                       | rule 2.3                                                |
| Reed bed (the wall)  | Uneven patches of reeds blocking whole cells. Taller in the middle, thinning out over 2 or 3 cells at the rim, with pools showing between the stems                | rule 8: things that grow, not noise                     |
| Mudflat to sea       | A frayed 2 to 3 px band of wet sand. Ripple marks run along the shore, a wrack line of weed sits a tier above the surf, and the surf is white only where it breaks | rules 5.1 and 5.3                                       |
| Stairs               | Timber: boardwalk steps between posts, never cut stone                                                                                                             | rule 6.1                                                |

## Families (house palette, `art/house-palette.json`)

- **Ground:** `grass_cool` for the body, with `leaf_cool` patches; `earth_cool` for mud and `earth` for peat; `sand_cool` and `sand` for the flats and bars.
- **Water:** `water` with `water_cool` in the channels. The arms are brackish and calm, so there are no riffles.
- **Wood:** `timber`, `timber_cool`, `timber_warm` for boardwalks, stilts and traps.
- **Flowers:** `brass` (marsh marigold, flag iris), `dusk` (purple loosestrife, sea lavender) and `plaster` (meadowsweet).

The delta is greener and cooler than the meadow and has no warm hay tones. Nothing is borrowed from the meadow's warm ramps.

## Ground recipe

Calm marsh: large fields of one tone, with a few big soft blotches two tones apart (the clean rule, `to-all-clean`). Then, by rule:

- Standing pools of 8 to 24 px on wet hollows, each with a light waterline on its north side.
- Tufts of rush clumped by wetness, never scattered evenly.
- Mud showing at path edges and around the pools.
- On the flats: ripple marks along the shore, worm casts in clusters, scattered shells and glasswort.

## Plants and clusters

| Plant or thing                   | Where                              | Cluster recipe                                                                  |
| -------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------- |
| common reed                      | reed beds, arm margins             | beds of 3 to 12 clumps, taller in the middle; 1 clump per 16 to 32 px of margin |
| bulrush                          | still water, oxbows                | 2 to 4 heads among reeds, about 1 in 5 clumps                                   |
| flag iris, marsh marigold        | water meadows, pool rims           | drifts of 3 to 7 by the water, never in rows                                    |
| purple loosestrife, meadowsweet  | arm banks, ditch sides             | 2 to 5 together, on the dry side of a margin                                    |
| willow and alder carr            | the delta head and the belt's edge | 3 or more of each kind, varied sizes; brambles under them                       |
| glasswort, sea lavender          | the flats near the sea             | low patches 16 to 40 px across                                                  |
| driftwood, wrack                 | the strand line                    | 1 to 3 pieces with weed at a tide line                                          |
| eel traps, stakes, a moored punt | by the stilt hut and the eel trod  | in a group of 3 to 5 at one bank, with a reason (`prop-logic.md`)               |

## Tiers and water

- **Tiers:** the delta is world tier 2 (`lull-delta.json`, local 0). It is flat except for the 12 px creek banks and the 32 px terrace edge up to the floodplain.
- **Water:** the arms run from the apex below Lullford to the sea. Every water body has a source and an outlet in the plan; oxbows and pools are declared closed.

## Ambience

- **Animals** (the brief's ambient slots: egrets): egrets standing in the shallows, a heron at the pools, curlews on the flats.
- **Sound:** reed warblers in summer, wind in the reeds, and the tide on the flats.
- **Light:** at dusk the water takes the sky's warm tone.

## Owned pieces (to draw through the kit)

- boardwalk, with posts and a timber stair
- reed bed edge
- mud bank (12 px)
- pool
- tidal creek
- mudflat front with wrack line

The named things (the stilt hut, eel traps, the reed hides, the wreck in the reeds) are hand painters made of kit parts (`rules-system.md`, Build).
