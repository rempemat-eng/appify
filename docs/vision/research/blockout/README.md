# The world plan's block-out (v5.2) and the overview map (v53)

## v53: the continent overview map (27 Oct)

Matt, 27 Oct 17:25: "update and improve this overview map and add little place names and biome names for all. can you make it feel like a game map a bit more (in the way the terrain is distributed and the different zones/biomes), i like the current version and its realism but it can be changed a bit (not super massively) to be more fun and interesting to play (consider similarly expansive games). also can you add a ruler for scale (in the soft grid sense)." With his approved steps: the stone circle and the ring of craters, each crater's scorch pointing home; aligned with the region plans and routes; built zones and act 1's route shown; a cleaner overview closer to a stylised in-game map.

`geo53.py` (data) and `map53.py` (the map) sit on top of `geo52.py`. v52's land, rivers, settlements, routes and ways are kept; v53 adds to them. `continent-1x-v53.png` is the labelled overview at 1920 x 1080 (256 colours). It is our own render; nothing here is an image of another game.

### What the games do, and the principles applied

| Principle | Where it comes from | What v53 does |
| --- | --- | --- |
| A centre that everything reads from | A Link to the Past: "the most open spaces are the Village and the area northeast of it" ([Game Developer, ALttP's Light World, part 2](https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2)); Paldea's Great Crater "at the center of the region, bordered by the four provinces" (world-plan 3) | the map is centred on the stone circle; Crossroads is the routes' hub beside it; the craters ring it |
| Landmarks seen from far, revealed as you near them | Breath of the Wild: "Nintendo had to make them stick out from a distance"; "as you go towards these mountains, whatever's behind is gradually revealed" ([GMTK](https://gmtk.substack.com/p/how-nintendo-solved-zeldas-open-world)) | one great crater per region, violet glass on any ground, and the beam over the circle (world-and-cast.md) |
| Places sit where the player drifts, not on summits | "the player naturally ends up in the valleys and crevasses"; "important locations are never on a peak or summit" ([Game Developer, BotW analysis](https://gamedeveloper.com/design/breath-of-the-wild-open-world-analysis-gravity-to-go-forward)) | craters on flats and shelves 50 to 500 px off a route, each with a trail |
| Distinct, readable biome blocks | Paldea's provinces and Galar's Wild Area (world-plan 3) | the overview draws the ground as flat biome blocks with soft-grid tiers, named |
| Gates between regions | ALttP: Death Mountain "must be reached through a tunnel" (same article); Pokémon's gatehouses (world-plan 2) | every way's crossing drawn as a gate with its W number: the col, the cutting, Drover's bridge, the viaduct, the ferry, the chasm (lava) bridge, the crust causeway, the swing bridge, the stile, the Shell Bar |
| Loops and shortcuts | ALttP: "these newfound paths are simply shortcuts to locations that were already accessible by a longer route" (same article); TUNIC (world-plan 2) | four new routes, below |
| Small pockets often | Sea of Stars: "It feels like a game where it's all these small pockets" ([MobileSyrup interview](https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/)) | act 1's places given points; the v52 pockets kept |
| Varied path lengths: walking near, trains far | Eastward's trains, Galar's rail (world-plan 3) | rail, cart and ferry lines drawn and named |
| Interesting edges | world-plan 5.5 | the land past the walk drawn hazier, and the map fading out past the drawn edge (the land goes on) |
| An in-game map style | world-plan 12 (Matt's example 2, Stardew's warmth) | tiers as plateaus with south faces, house palette, upper-left light |

The Stardew Valley wiki page was not reachable from here; its point (Pelican Town in the middle, four exits) is already in world-plan 2.

### Geography changes (v52 to v53)

1. **The stone circle** at (5800, 3000) in the woodland's glade (the woodland zone's stones, placed in the valley plan's woodland rect; Claude A's golden screen keeps the exact spot). The map centres on it horizontally. Crossroads' square is at (6296, 3536).
2. **The ring of craters** (`CRATERS` in `geo53.py`): the Frostline crater (6480, 1590), the Heather crater on the Brackens (5300, 2390), the Seam crater in the coal hills (8260, 2130), the Lull crater (8150, 3560), the Company crater north of Neon's new town (10780, 4130), the Lagoon crater on the main isle (6330, 6420), the Glass field in the Sunstone basin (2160, 2760) and the Ember crater on the ash fields (3700, 4870); the Crossroads crater in the park (6484, 3712, already in `crossroads.json`) is the centre stone. Each is a glass bowl, a rim and a scorch that runs from the crater toward the circle (its heading equals the bearing home in every case, `stats-v53.json` v53.craters), with a trail to the nearest route. They lie 0.8 to 5.1 km from the circle: a rough ring, nearer in the north where the massif closes the land. Craters in deep forest blast their own clearing.
3. **Four new routes** (`NEW_ROUTES`): the **Heather Way** (the woodland's glade over the Brackens' moor top past the Heather crater, Old Fang's barrow and the drove well to the Brackens gap; a loop with the Drover's Road, 25 s), the **Glass Road** (Dust Gulch round the glass field to the Amber canyon; a loop off the Canyon Road, 17 s), **Fern Lane** (Fernhollow down to the Lull Road; closes the Foothill Road and the Lull Road into a loop, 21 s) and **Gull Lane** (the Lull Road down to Gullwick; a loop with the Coast Path, 26 s). None crosses a barrier, so the ways and their order are unchanged.
4. **Act 1's places** given points (`POI53`, proposals for lanes E and F): the ice caves (6080, 1660), the Saddle House (6440, 2010), Old Fang's barrow (4930, 2980), the spur tor (the Heather spur, 4990, 1960), the lighthouse (6600, 4995) and the Millrace landslip (the cutting). The bothy is the Frostline plan's cabin meadow.
5. **Waystones** (`WAYSTONES`): the five the plans place (Crossroads, Cogsworth, the footbridge, Fernhollow, the Cog foot) and thirteen proposed, one per settlement or threshold hub.
6. **No region plan place moved.** Every settlement, station, threshold, bridge and named thing keeps its v52 point, so no plan in `art/regions/` or `game/data/plans/` needed a change. The craters, new routes, places and waystones above are for the owning lanes to adopt in their plans (E: the valley and the Heather Way's east end; F: the Frostline, the Brackens; H: the coal hills, Fern Lane; I: Neon, Gull Lane; Sunstone and the fire country: the Glass Road and the Ember crater; C: the isles).

The biomes' identity and borders are sharpened in the drawing, not in the ground model: the overview merges speckle into biome blocks (a majority filter on the open ground), steps the tiers as soft-grid plateaus, and names every region and biome. The ground the lanes build from (`tiers`, routes, kinds) changes only where the craters, trails and new routes are painted.

### Checks

- The gate check: no leaks, nothing missing, no crossing without a way, at every step (`gates-v53.json`).
- The benchmark: **21 of 21 pass** (`stats-v53.json` benchmark). Fern Lane first failed check 16 (a straight 309 px); it now bends every 150 px or so.
- Reachable from home with every way open: every crater, act 1 place, waystone and the circle (`stats-v53.json` v53.reachable_with_every_way_open).
- Walkable zone-areas 149.5 (v52: 141.2; the new routes and crater trails widen the walked corridors). Times from the hut are unchanged at the plan's 40 px a second (Cogsworth 52 s, 25 s by train; Neon 115 s, 53 s; Dust Gulch 101 s, 30 s; Hearthold 130 s, 51 s). At Bramble's own speed (`home_to_at_hero_speed`): Cogsworth 80 s (39 s), Neon 177 s (82 s), Dust Gulch 155 s (46 s), Hearthold 200 s (78 s).
- A second run reproduces the three JSON files byte for byte.
- The labels: none overlaps another or an icon (the placer keeps every box); every name is placed except "the ria" (the city fills it), which the docks' and Harbour Bridge's names stand for.

### The scale ruler

One soft-grid cell is 8 world px, 24 art px at density 3 (`eastward-edges.md`). The hero's walk speed comes from the cast manifest: Bramble's `walk_speed` is 78.1 art px a second, 26.0 world px, 3.25 cells. So 10 cells take 3 s, 50 cells 15 s, 100 cells 31 s, and one 1080p screen (960 art px, 320 world px, 40 cells) 12.3 s to walk across. On the 1920 x 1080 map one pixel is 6.4 world px (0.8 cells). The ruler shows 10, 50, 100, 200 and 300 cells with their walk times, the screen as a box, and a north arrow.

### The maps (written to `out/`, and to `$MAP53_OUT` if set)

| File | What |
| --- | --- |
| `map53-1920.png`, `map53-3840.png` | the full map with every layer, at 1920 x 1080 and 2x |
| `map53-labels-1920.png` | the map and its names, without the overlays |
| `map53-overlay-built-1920.png`, `-act1-`, `-ring-` | each overlay alone on a muted map; `map53-layer-*-1920.png` are the transparent layers |
| `map53-realistic-1920.png` | the same layers on v52's realistic texture (the toggle) |
| `map53-v52-vs-v53.png` | v52's render and v53's map side by side at the same scale |

Overlays: the built zones (the woodland, Crossroads, and the Undercroft below the circle, dashed); act 1's route as a dotted line along the walk with its numbered beats (one order of `docs/story/act1.md`'s strands, listed in the legend); the ring of craters joined to the circle by faint lines.

```
python3 -I geo53.py                  # data and every map (about six minutes)
RENDER_ONLY=1 python3 -I geo53.py    # the maps again from out/state-v53.pkl (under a minute)
QUICK=data python3 -I geo53.py       # the JSON and the state only
```

The fonts are the game's own (`game/ui/fonts/PixelifySans-Regular.ttf` for region and biome names, Nunito for places) and DejaVu Serif for water. `game/tools/gen_blockout.py` (zone scenes from zone plans) is unchanged: it does not draw the continent.

## v5.2

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
| `geo53.py`, `map53.py`, `blockout-v53.json`, `stats-v53.json`, `gates-v53.json`, `continent-1x-v53.png` | v53, above: the same three files plus `v53` (circle, craters, new routes, places, waystones, built zones, act 1's beats), and the overview map. |
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
