# The world canvas: the build (step 1 of 3)

**What Matt decided:**

- **20 Oct, about 10:50** (world plan v2, decision 2): replace the fixed 320 x 576 zones with continuous canvases on the 8 px grid, streamed in 256 x 256 render tiles. The zones become named areas.
- **10:58:** one connected world, with the regions on one continent joined by walkable routes.
- **About 11:45:** **one world canvas for the continent**, authored in chunks (the regions, the routes, the land between) and streamed in 256 px tiles. Halcyon Station, the moon and the inside of the hut stay separate planes. The continent will be about twice the size of world plan v3; v4 is being written.

This is step 1, the build. **Nothing in the game changes yet.**

- The zones are still drawn and saved as before (`assets/zones/**`, `lib/zone-maps.ts`, `lib/zone-assets.ts`), and the game still reads them.
- The world's outputs are written alongside them, and checked against the zones pixel for pixel.

## The model

- **Planes.** The world has four planes:
  - `continent`: the land you walk.
  - `orbit`: Halcyon Station.
  - `moon`: Lumen.
  - `hut`: the inside of the nap hut.
- **Chunks.** A chunk is the unit a lane authors and the build caches. It can be a region, a route, or the land between them. Each chunk has:
  - a plane;
  - a **world origin** (the top-left of its box, in world px);
  - a **bounding box** (its width and height);
  - a **blend margin**, which it may paint past its box over its neighbours.

  Origins, sizes and margins sit on the 8 px grid. Two chunks' boxes on one plane may touch but never overlap. Inside its box a chunk's ground is the world's ground. In its margin, the chunk's pixels are blended over the neighbour's ground (alpha over, after every box is down), so chunks meet in a drawn transition rather than a cut. Walk and terrain come from boxes only.

- **World tiles.** Tile (col, row) covers world px `[col * 256, row * 256]` to `[(col + 1) * 256, (row + 1) * 256]`.
  - Each tile is composited from every chunk on the plane that reaches it, so the continent is one picture with no seams at chunk edges.
  - Tiles are always 256 x 256 art px, transparent where no chunk reaches.
  - A tile with no ground has no picture.
- **World coordinates everywhere.** Props, stands, areas, deck connectors and seams are in world px or world cells (4 px).
- **Per-tile data; areas in a small table.** Everything a renderer or a walk needs near the camera is exported per world tile:
  - its picture;
  - its walk, terrain and tiers (64 x 64 cells);
  - its stands;
  - its props, listed in the tile their foot stands in.

  Areas (names, the map, saves, the ways) are one small table, `worldAreas`.

- **Placeholder origins.** Today's regions become one chunk each. `PLACES` in `scripts/art/world_canvas.py` sets them in a row on the continent, a tile apart, with the valley at the world's origin (so the valley's world px are today's region px). The station, the moon and the hut are on their own planes. When v4 lays out the continent, a chunk moves by changing its origin. The build renames its tiles and moves every coordinate with it.

## The pipeline

`scripts/art/zones.py` draws the zones as before. At the end of its run, it hands its built zones to `world_canvas.build_all()`, which:

1. **Gets each chunk.**
   - If a lane has registered a painter for it, the build uses the painter.
   - Otherwise the **adapter** (`from_zones`) assembles a region's chunk from today's zones (the zone functions and `LAYOUT`). Each zone's ground, props, stands, blocked ground, walk, terrain, deck and moving water are placed at its offset, and props and stands are renamed `zone:id`.
   - The garden (the valley's 0, 0) brings its ground (`assets/garden/ground.png`) and its walk. The walk follows the rules `lib/region-walk.ts` applies today: the gate and the ridge trail are open, and the west and east edges are closed two cells deep outside their ports. The garden's props stay the garden's own.
   - The areas are one rectangle per zone, plus `garden`.
2. **Settles the seams.** For an assembled chunk, the build walks the whole box by the zone rules (`derive_walk`, the same rules with no seams). Wherever that differs from the zones' grids joined, it takes the whole-box value and reports the cell in `worldSeams`. The garden keeps its own walk. The details are in "The seams, settled" below.
3. **Finishes it** (`finish`):
   - derives what a painter leaves out: walk, terrain and moving water;
   - checks that areas are on the grid and inside the box, every walkable cell is in an area, every stand is inside the box, and the walk, terrain, tiers and deck rows have the box's size.
4. **Checks the compatibility cut** (`cut_zone`, `check_cut`). Every zone cut back out of its chunk must equal that zone:
   - its ground, byte for byte;
   - its walk (the zones' grids joined; the settled walk differs only at the reported seam cells);
   - its terrain, props and stands.

   A painted region writes its zones for the game from `cut_zone` until step 2 retires them.

5. **Self-tests** (`selftest`) what today's data does not exercise. It builds two small chunks (a sea and an isle with a 16 px margin) in a scratch folder and checks that:
   - the margin blends half over the sea across a tile edge (exact colour);
   - an open-sea tile becomes one shared colour picture, and identical tiles share one picture;
   - after one chunk changes, the cache keeps the tile the change does not reach;
   - the cut returns a painted part exactly;
   - a renamed picture is not left behind.
6. **Writes the pictures** (`write_world`) to `assets/world/`:
   - `<plane>/t_<col>_<row>.png`: a tile's own ground, at `TILE_SCALE`, scaled by nearest neighbour. Negative numbers are written `m1`.
   - `shared/u_<rrggbbaa>.png`: **a tile of one colour** (open sea, deep forest). It is shared by every such tile, and the tile also carries `fill`, so the renderer can draw a plain coloured view instead of decoding a picture.
   - `shared/s_<hash>.png`: **a ground two or more tiles share exactly** (a repeated stretch of sea or forest frame), written once.
   - `<plane>/f_<col>_<row>.png`: the tile's moving water and lava (`water_flow.py`). The box round it holds its 8 frames stacked, at 1x, like the zones' `flow.png`.
   - `<plane>/d_` and `s_<col>_<row>.png`: a deck and its shadow over the tile. There are no decks today.
7. **Exports** two TypeScript files:
   - `lib/world-canvas.ts`, the typed data:
     - `worldChunks` and `worldAreas`;
     - `worldTiles[plane]['col,row']` with `art`, `fill`, `walk`, `terrain`, `tiers` (omitted while all 0), `deck`, `stands`, `objects` and `flow`. The cell layers are one run-length string per tile (`tileRows` unpacks them into 64 rows).
     - `worldSeams` and `worldDecks`.
   - `lib/world-canvas-assets.ts`, which imports each picture one by one, so they bundle on native.

   They are split like `zone-maps.ts` and `zone-assets.ts`, so the tests can read the data without loading pictures. Nothing in the app imports them yet.

**Caching per chunk.** The cache lives in `.cache/world-canvas/`, which is git-ignored.

- Each chunk has a digest of everything that shows in a picture: its plane, origin, size, margin, ground, moving water and decks.
- A tile's key is the build's code plus the digests of the chunks that reach it.
- A tile whose key is unchanged is not composited or encoded again. Its files are checked against their recorded hashes and kept, or copied under a new name if deduplication renamed them.
- A painter registered with `sources=(...)` is not even re-run while those files and the build are unchanged: its finished chunk is loaded from the cache.
- So a lane's change re-encodes only the tiles its chunks reach. To try it, I changed one pixel of the Canal: 10 tiles were composited again, 152 were kept, and one picture changed. A fresh checkout, such as the art-repro check, has no cache, builds everything, and gets the same bytes.

**Time.** The world build takes 25 to 55 s inside `zones.py`'s run, or about 25 s when the cache has every tile. `zones.py` ran in 4 min 0 s before this work and about 4 min 20 s with it. The art-repro check's per-generator timeout went from 5 to 10 minutes.

## Painting a chunk directly

A lane that draws a chunk whole registers a painter in place of the zones:

```python
import world_canvas as wc

@wc.painter('steam', sources=('scripts/art/cogsworth.py',))
def cogsworth() -> wc.Chunk:
    ch = wc.Chunk('steam', 704, 960, margin=32)     # any size on the 8 px grid
    # box pixel (x, y) is ch.at(x, y) in ch.ground (a PIL RGBA image); the 32 px round
    # the box is the margin, painted over the neighbours (soft, partly transparent)
    ch.objects.append(('steam:clock-tower', 'clock_tower', 312, 96))   # sprite top-left, box px
    ch.stands['steam:terminus'] = (360, 820)
    ch.blocked |= canal_pixels                       # water, cliffs, walls drawn in the ground
    ch.tiers = tier_rows                             # optional: the terrace of each 4 px cell
    ch.areas += [{'id': 'junction', 'kind': 'zone', 'rect': (0, 0, 704, 480)},
                 {'id': 'hill', 'kind': 'zone', 'rect': (0, 480, 704, 480)}]
    return ch
```

`finish()` then derives three things:

- **The walk.** A prop's foot band blocks, gateways excepted. Drawn obstacles block. The cell beside lava is kept back from. Ground the box does not cover blocks.
- **The terrain**, from `world_lint.classify` over the whole box.
- **The moving water**, from `water_flow.sheet` over the whole box, so a river runs on across what used to be a seam.

An area can be any shape: give it `cells`, walk rows of its rectangle with `.` inside. A route or the land between is a chunk too (`kind='route'` or `'land'`), with its own origin from v4.

I ran the painter path on the isles' and Sunstone's assembled chunks:

- The terrain it derives matches the joined zones cell for cell.
- Its moving water differs slightly from the joined zones' only along the old seams, where it now runs on.

## Tile scale and memory

The plan's decision 8: use 1x pictures with nearest-neighbour scaling if that is crisp on iOS, Android and the web, and 2x until then.

**How the numbers were measured:**

- The view is a 301 x 655 art px phone view (plan section 3) with the renderer's 24 px mount margin, slid in 16 px steps over every region (15,238 positions).
- A zone counts as mounted when it intersects the margin box. This is close to, but not the same as, `zonesToMount`.
- Sizes are decoded RGBA bytes, in MiB.

The tiles are unchanged by the chunk model; there are no uniform or duplicate tiles in today's art.

| Mounted per view (median / worst)   | Today: zones at 4x | Tiles at 2x        | Tiles at 1x        |
| ----------------------------------- | ------------------ | ------------------ | ------------------ |
| Ground pictures mounted             | 4 / 9 zones        | 8 / 12 tiles       | 8 / 12 tiles       |
| Ground decoded                      | 45 / 101 MiB       | 8 / 12 MiB         | 2 / 3 MiB          |
| Moving water decoded (1x, 8 frames) | 6.1 / 22.5 MiB     | 1.8 / 12.8 MiB     | 1.8 / 12.8 MiB     |
| **Total decoded**                   | **47 / 115 MiB**   | **9.4 / 24.8 MiB** | **3.7 / 15.8 MiB** |

| Whole world                | Today: zones at 4x           | Tiles at 2x     | Tiles at 1x |
| -------------------------- | ---------------------------- | --------------- | ----------- |
| Ground files               | 37 (36 zones and the garden) | 140 world tiles | 140         |
| Ground on disk             | 3.9 MB                       | 2.9 MB          | 2.4 MB      |
| Ground decoded, all loaded | 416 MiB                      | 140 MiB         | 35 MiB      |
| Moving-water files         | 26, 0.46 MB                  | 80, 0.40 MB     | the same    |

**Deduplication.** Nothing is shared yet: every tile of today's art is drawn and different. It pays off on the continent's frame. At twice v3's size, much of the continent will be open sea and deep forest drawn as frame. Those tiles become one colour picture each (or a plain coloured view, at no picture cost), or one shared picture per distinct pattern.

**Moving water** is the largest share in the worst case. Each tile's flow is a full box of 8 frames. Step 2 can cut it down (keep only the pixels that change, or use fewer frames). This step keeps it as it is, so that nothing changes.

**Crispness on the web: verified.** I drew a 1x tile in headless Chromium (Playwright 1194) inside `data-pixel='true'`, using the rule in `global.css` (`image-rendering: pixelated`):

- At 3 device px per art pixel (DPR 2 and DPR 3) and at 4 (DPR 3, the 402 px phone), every device pixel equalled its art pixel: 0 of 90,000 differed.
- Without `data-pixel`, 31 to 43 % differed (smoothed).
- So the renderer must keep the tiles inside a `data-pixel` view.
- Safari and Firefox were not tested.

**Native: not tested here.** React Native's `Image` has no filter setting. iOS (`UIImageView` and Core Animation) and Android (Fresco) scale bitmaps with linear filtering by default. That is why today's 4x zone pictures are crisp on a 3x phone: at 4 device px per art pixel they are drawn 1:1. **Default: 2x** (`TILE_SCALE = 2`; `WORLD_TILE_SCALE=1` builds at 1x), as the plan recommends until 1x is shown crisp on all three platforms.

## The check

`npm run check:world-canvas` (`lib/world-canvas.test.ts`, part of `npm run check`) reads everything back from the world tiles and checks:

- **Chunks.** Today there is one chunk per region, the size of its zone grid, on the 8 px grid, with no margin. Boxes on a plane never overlap.
- **Areas.** The areas are the zones (and the garden) at their places, and every walkable cell lies in one.
- **Walk.** The walk read back from the tiles equals `regionWalk()` from `lib/region-walk.ts` (the zones' grids joined exactly as the game joins them today, garden included) except at the cells listed in `worldSeams`. At each of those cells the walk really differs, is settled as reported, and lies within 20 px (the deepest foot band) of a zone seam.
- **Terrain, props and stands.** Each zone's terrain, props and stands read back from the tiles are its own, in world px. Each prop and stand is listed once, and each stand is in its own tile.
- **Ground pictures, pixel for pixel.** The pictures reassemble the zones' ground pictures exactly: 9,175,040 art px.
  - Every picture is 256 px times the scale square, and each block of the scale is one colour (nearest neighbour).
  - There is a picture for exactly the tiles that have ground.
  - A one-colour tile matches its `fill`.
- **Moving water, frame for frame.** Each tile's moving water equals the zones' moving water (41,943,040 values).

It fails if a single tile pixel is changed (tried). `npm run check:art-repro` regenerates everything in a fresh copy and compares it byte for byte (`lib/world-canvas*.ts` and `assets/world/**`). Inside that run, the build itself asserts the compatibility cut and runs the self-test.

## The seams, settled

There are 22 cells, all `shut`: the walk over the whole chunk blocks them, and the joined grids leave them open. The world walk takes the whole-chunk value. The game, which still reads the zones, is unchanged.

- **Valley, 11:**
  - Ten cells along the Town's south edge. Props standing at the top of the Harbour reach their foot band 4 to 8 px over the Harbour's north edge, and `share_feet` closes the ground only for east and west neighbours.
  - One cell on the Headland's west edge, where the step back from a cell read as lava in the Harbour is cut off at the zone's edge.
- **Isles, 11:** the same north-edge foot bands, along the Rainforest's and the Headwaters' south edges, from props in the Landing and the Cove.

## Step 2: the renderer and the walk on world tiles (Claude A, one PR)

**The renderer** (`components/atlas-walk.tsx`):

- **Mount world tiles, not zones.** `tilesToMount(plane, view)` gives the tiles the camera sees plus the 24 px margin: at most 12, usually 8. Tiles stay mounted out to twice the margin, as `zonesToMount` does today, so a walk along a tile edge does not churn.
- **How each tile is drawn.** Each tile is a `View` at `col * 256`, `row * 256`, snapped to whole device px (256 art px are a whole number of device px at every scale `pixelScale` picks). It holds:
  - its ground: an `Image` of `worldTileArt[art]`, or a plain coloured view for a `fill` tile;
  - its moving water: the same `FlowLayer`, keyed by tile;
  - its deck art.
- **Pixel rendering.** On the web the tiles sit inside a `data-pixel` view. Native depends on the 1x question below.
- **Props.** Props come from the mounted tiles' `objects`, sorted by foot across tiles. A tall prop whose foot is in an unmounted tile but whose body rises into the view must still draw. To support that, the build adds a per-tile list of props whose sprite reaches that tile (step 2 adds it to the export). That replaces `zoneReach` and the 48 px overhang rule.
- **Backdrops.** `beyond()` gaps and `zoneScenery` are replaced by the chunks' own frame, and by `BACKDROP` past the last tile.

**The walk** (`lib/region-walk.ts` becomes `lib/world-walk.ts`):

- **One walk over the plane.** `cellAt(plane, wc, wr)` reads the tiles' walk rows, with decoded rows cached per tile. `walkWindow(plane, rect)` builds a `makeWalkGrid` over a window. `regionWalk`, `tileOrigin`, `GARDEN_OPENINGS` and the garden's edge spans go. The 22 seam cells are already settled in the data.
- **Decks.** Decks carry over in world px: `worldDecks` and the tiles' `deck` rows feed `regionLevels`' two-level grid.
- **Area names.** `areaAt(plane, x, y)` reads `worldAreas` and gives the area name under the HUD, with the same hysteresis (`ZONE_HYSTERESIS`). The map tiles are drawn per area.
- **The garden** joins the valley's chunk. Its stream and pond overlays and its props stay drawn by the garden's renderer at the garden area's offset until the garden is painted into the chunk. The hub's moved grid (`lib/home-hub.ts`) becomes an offset.

**Checks:**

- The mounted set covers the view at every window size from 320 to 1440 px wide.
- There is no gap between tiles at any scale.
- The decoded memory per view stays under a budget: 25 MiB at 2x, ground and flow together (the worst view today is 24.8 MiB).
- A tap-walk crossing a tile edge and a chunk edge works.
- An interrupted walk triggers no stale navigation.
- The harness covers both normal and reduced motion.

### Open questions for step 2

1. **Native 1x crispness.** Should step 2 make 1x crisp on iOS and Android, or keep 2x and accept softness?
   - React Native's `Image` filters linearly, so 1x and 2x pictures are soft on a phone. Only a picture matching the device px per art pixel (today's 4x on a 3x phone) is 1:1.
   - **Skia:** draw the mounted tiles with `@shopify/react-native-skia` and `FilterMode.Nearest` in a `.native.tsx` file, keeping the web on `Image` with `data-pixel`. This adds a native dependency (`npx expo install`, part of the Expo SDK) and puts the tiles in one canvas.
   - **A small native view:** set `layer.magnificationFilter = .nearest` on iOS and turn off bitmap filtering on Android. This needs a config plugin or a development build.
   - **Fall back to building at 4x.** Mounted memory would go back up to about 45 MiB.
   - **Decision needed:** test the Skia route on a device before choosing; until then, 2x.
2. **The tap-walk's search window over a big world.**
   - The continent at twice v3's size is about 2 million walk cells. That is too many to run a path search over on every tap on a phone, and too much to build as one grid.
   - **Proposal:** search a window, the box round the companion and the tapped point plus 2 tiles (512 px) on every side, usually about 100,000 cells. If no path is found, widen once to 4 tiles. If there is still none, fall back to the route graph (question 3).
   - The tapped point is always on screen, so nearly every walk ends inside the first window.
   - **Open:** the margin, and whether to show the companion "looking for a way" on the fallback.
3. **The coarse route graph for far walks.** Walks from the map, residents' routes, and "walk me to the harbour" cross many tiles.
   - **Proposal:** the build exports a graph of **portals**: cells where a route chunk meets a region chunk, area exits and named stands. It also exports edges, each with the walk cost between two portals over the world walk, computed at build time.
   - A far walk plans on the graph, then walks it leg by leg, with each leg searched in a window as in question 2.
   - Ways (#118) become barriers on graph edges: a closed way removes its edges.
   - **Open:** whether the graph is per area or per tile, and whether a train shortcut is a graph edge (proposal: yes, with its own cost and a ride).
4. **Data size.**
   - `lib/world-canvas.ts` is about 200 KB for today's 140 tiles. The continent at twice v3's size may hold 1,000 or more tiles, about 1.5 MB of literals that all bundle on native.
   - **Proposal:** split it per plane and per chunk in step 2, and if it grows past about 1 MB, load the per-tile walk and terrain as JSON assets that are fetched with the tiles.
5. **Placeholder origins.** Step 2 can ship on the placeholder row. The real origins come with v4, and moving a chunk only renames tiles.

## Step 3: saves and tests (Claude A with Codex)

- **One layout version.** `lib/world-layouts.ts` maps each old zone to its area and each old stand to its new stand. A saved `WorldSpot` (a region and a point) gets plane plus world = origin + point, so it lands at the same place. `visited` keeps its ids where an area keeps its name.
- **Saves** (Codex, `lib/save-data.ts`): migrations and tests for spots, visited places and the ways.
- **Tests move to world coordinates:** `lib/region-walk.test.ts`, `lib/home-hub.test.ts`, the ways' tests and the hub block of `scripts/check-garden.cjs`.
- **Then the zones retire.** `zones.py` stops writing `assets/zones/**` and `lib/zone-*.ts`. `frames.PORTS` inside the continent, the border-continuity lint and `beyond()` between zones go. Regions, routes and the land between are painted as chunks on their v4 origins (plan P4 to P7).
