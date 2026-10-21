# The world plan's block-out (v5.2)

This is the v5.2 block-out behind world plan v5.3 (`docs/vision/world-plan.md`, arrangement A). It was drawn by Claude A's scripts from a height field, a wetness field, the rivers and the paths, at one cell per 8 px. Until now it lived only in Claude A's scratchpad. The lanes building the world canvas (`docs/vision/region-canvas.md`) take their routes, tiers and region boxes from here.

It is a block-out, not art. Positions and tiers are the plan's; each lane's brief in `docs/vision/regions/` and the plan's later decisions take precedence where they differ (for example, the plain's many low tiers are to be merged into fewer banks, world plan 5.4).

## Files

| File                   | What it is                                                                                                                                                                                                                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `geo5.py`              | The v5 block-out: helpers (noise, polylines, rasterising), the tables (coast, massif, rivers, settlements, routes, ways, bridges, stations), the gate check, walk times and the renderer. `geo52.py` imports it.                                                                                       |
| `geo52.py`             | The v5.2 block-out on top of `geo5.py`: the land (`build51`), the Lull, delta and Neon Harbour, obstacles, borders, content, the benchmark, the tier field and the export below. Run it to regenerate every file here.                                                                                 |
| `blockout-v52.json`    | The geometry as data for the lanes (written by `export_blockout` in `geo52.py`): route and river polylines, the delta's arms, the tier grid, every tier change on a route, region and biome boxes with their origins, thresholds, lifts, settlements, bridges, stations, the ways and their crossings. |
| `stats-v52.json`       | The plan's measurements: walk times, routes' lengths, why each place is where it is, bridges, every named thing, pocket, obstacle and marker with its position, the mixing at each threshold, vertical stats per region, and the benchmark's 21 checks (all pass).                                     |
| `gates-v52.json`       | The gate check (world plan section 10): with each set of ways open, which places leak or go missing (none), and every place a route crosses a barrier with the way that opens it.                                                                                                                      |
| `continent-1x-v52.png` | Our own render of the whole continent at 1 px per 8 px cell (1408 x 864), hill-shaded from the upper left. Reduced to 256 colours to keep it small (the script writes the full-colour one to `out/`). Nothing in this folder is an image of another game.                                              |

## Coordinates

Everything is in **world px** on one plane: the continent is 11264 x 6912 px, origin (0, 0) at its top-left (north-west) corner, x running east and y running south. The fields are sampled on 8 px cells (1408 x 864 cells); cell (cx, cy) covers world px `[cx * 8, cy * 8]` to `[(cx + 1) * 8, (cy + 1) * 8]`. World tiles are 256 px, as in `region-canvas.md`. One tier is a 32 px face on the soft grid.

## What is in `blockout-v52.json`

- `coords`: the system above.
- `routes`: per route, `kind` (road, path, bar, bridge), `width_px`, `features` (the ground fitted to it, switchbacks, huts), `control` (the plan's control points) and `polyline` (the drawn line after meandering and switchbacks, the one the stats and tier changes are measured on). Both are lists of `[x, y]`.
- `rivers` and `delta_arms`: centrelines as `[x, y]` lists (the Lull, its tributaries and the other rivers; the Lull's eight distributaries).
- `tiers`: the tier grid, one row per 8 px cell row from north to south, run-length encoded as `tier, run, tier, run, ...`; each row's runs add up to 1408. Sea is -1. To decode a row in Python: `[t for t, n in zip(row[0::2], row[1::2]) for _ in range(n)]`.
- `tier_changes`: where each route changes tier: `route`, `kind` (stair, ramp or switchback), `x`, `y` and `tiers` (how many steps).
- `regions`: the plan's regions (the massif's edge, the Frostline, the home valley, the coal hills and the Narrows, the Lull plain, the Lull belt and delta, Neon Harbour, the Sunstone basin, the Rift, the fire country, the coast and the isles). Each has `box` (`[x0, y0, x1, y1]` as planned), `origin` (the box's top-left snapped down to the 8 px grid), `size` (snapped up to the 8 px grid), `tiles256` (the first and last 256 px tile columns and rows it reaches) and `vertical` (tiers walked, the full tier range, typical and largest face in px, stairs, ramps and switchback steps).
- `biomes`: the same for the content biomes `stats-v52.json` counts by.
- `crops`: the boxes of the plan's region and route crops (the images listed in the world plan).
- `thresholds`, `lifts`, `settlements` (`x`, `y`, `radius_px`, `kind`), `bridges`, `stations`, `ways` (`[x, y, radius]` discs per way), `way_names` and `crossings`.

## How the lanes use it

- **Routes (lane G).** Lay each route chunk along its `polyline`, at its `width_px`, and put a stair, ramp or switchback at each of its `tier_changes`. The `thresholds` are the places where one region turns into the next; G draws the threshold object there.
- **Tiers per region (all lanes).** Read a region's tiers from the `tiers` grid inside its box, and the summary in `regions[name].vertical`. Merge the plain's many low tiers into a few deliberate banks rather than copying them step for step.
- **Region origins (all lanes).** A region's chunk on the world canvas is placed at `regions[name].origin`, on the 8 px grid; `tiles256` says which world tiles it reaches. Chunks on one plane may touch but never overlap (`region-canvas.md`), so where two boxes overlap here, the lanes agree the line in their briefs' threshold tables.
- **Water.** The `rivers` and `delta_arms` centrelines give where the water runs; the widths are the brief's and the kits'.

Lane F takes the Frostline and the massif's edge, G the routes, thresholds and edges, H the coal hills and the Narrows (with Cogsworth and Fernhollow from `settlements`), I Neon Harbour and the Lull belt and delta (with Lullford and Gullwick).

## Regenerating

From this folder:

```
python3 -I geo52.py
```

It needs Python 3 with numpy, scipy, scikit-image and Pillow, and the DejaVu fonts at `/usr/share/fonts/truetype/dejavu/`. It writes the three JSON files next to itself and every render (the continent, the labelled map, the physical map, the tier map, the in-game map mock, the region, route and boundary crops, the content map and the transitions sheet) to `out/`, which is git-ignored; set `BLOCKOUT_OUT` to write the renders somewhere else. `QUICK=none python3 -I geo52.py` writes the JSON, the 1x continent and the tier map only (about five minutes). The output is deterministic: a fresh run reproduces the committed `stats-v52.json` and `gates-v52.json` byte for byte.
