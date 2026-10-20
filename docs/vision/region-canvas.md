# The world canvas: the build (step 1 of 3) and the renderer (step 2)

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

## Step 2: the renderer and the walk on world tiles (built, behind a switch)

Step 2 is built behind **`WORLD_CANVAS`**, which is **off by default**. The default lives in `lib/world-flag-default.ts`.

- **Off:** the game draws and walks the world from its zones, exactly as before.
- **On:** it draws and walks the world from the world tiles. Both paths work, so main can carry this before it is switched on.
- **Trying it on the web:** add `?world=canvas` (or `?world=zones`) to the address. `lib/world-flag.web.ts` reads it. Native reads only the default.
- The origins are still the placeholder row.

**The renderer** (`components/atlas-walk.tsx`, with the switch on):

- **World tiles, not zones.** `tilesToMount` (`lib/world-walk.ts`) mounts the tiles the camera sees plus a 24 px margin, and lets a tile go only past twice the margin.
  - A phone mounts at most 12 tiles.
  - Each tile is a `View` at its world tile position, snapped to whole device px, inside the camera's `data-pixel` view. It holds:
    - its picture at 2x, or its `fill` colour for a one-colour tile;
    - its moving water (`FlowBox`), stepped on the same clock as before, which stops with reduced motion or an inactive screen.
- **Props.** Props come from the tiles' lists in world px, through `propsFor`. A prop whose picture reaches a mounted tile draws even when its foot stands in a tile that is not mounted. On this path `zoneReach` and the overhang rule are not used.
- **The garden.** The garden draws at its offset in the valley: its ground is in the tiles, and its props, stream and pond are drawn at the garden area's place. In the hub, the home layer draws its life as before.
- **Places.** Residents, zone life and the hour's light still go by place. With the switch on, a place is an area the view reaches, and today the areas are the zones.
- **Area names.** The area name replaces the zone name under the HUD (`areaWithHysteresis`, same margin).
- **Backdrops.** The scenery past the world and the forest in the valley's corners are drawn as before (see "Memory, measured" below).
- **Prefetch.** Prefetching loads the chunk's tile pictures, moving water and props.

**The walk** (`lib/world-walk.ts`):

- **Reading the walk.** `regionWalk` reads the tiles: the zones' grids joined, with the 22 seam cells settled. The hub's planner uses it unchanged.
- **Tap-walks.** AtlasWalk's own walks go through `makeWorldWalk`:
  1. A tap-walk is searched in a window: the box round the companion and the goal, plus 2 tiles (512 px).
  2. If that fails, the window widens to 4 tiles.
  3. If that fails too, the walk is planned on the **route graph** and walked leg by leg, each leg in its own window.
- **The route graph** (`worldPortals`, built by `world_canvas.portals()`) has 257 nodes and 1,406 edges.
  - The nodes are the stands, plus the gates in the middle of each run of open cells where two areas meet.
  - The edges join two nodes of one area that a walk inside that area reaches, with their cost in px.
  - The ways (#118) will close edges.
- **Kept on the whole grid:** the hut with keepsakes (`walk` rows passed in) and regions with decks (none today).

**Checks:**

- **`npm run check:world-walk`** (`lib/world-walk.test.ts`):
  - **Reading the tiles:** the tiles' walk is the zones' join, apart from the seam cells, and a cell reads the same one at a time as in a window.
  - **Windowed search:** 685 walks between stands and random open ground, searched in windows, end where the whole-region search ends.
  - **Route graph:** 104 of those walks, forced onto the route graph, still arrive.
  - **Mounting:** in 14,484 camera positions at 9 window sizes (320 x 568 to 1440 x 900), the mounted tiles cover the view.
    - Every prop whose picture reaches the view draws.
    - A phone mounts at most 12 tiles, using at most 24.8 MiB of tile pictures and moving water at 2x, the tiles kept for the margin included.
  - **No gaps:** tiles meet with no gap at every pixel scale, and each tile edge sits on a device pixel.
  - **Area names:** the area under each stand is its zone, and the name holds within the margin along an edge.
- **`npm run check:world-canvas`** and the rest of `npm run verify` still pass with the switch off. The game is unchanged.

**Play-test** (headless Chromium at 402 x 874, DPR 3, disposable profile, both paths, screenshots compared side by side):

- **Places tried:**
  - the hub, walked from the garden out through the gate into Crossroads Town (the garden/town seam);
  - Dust Gulch east into the Scorched Pass (the gulch/scorch seam);
  - Neon Harbour from the Skyport west and north across the old seams;
  - the inside of the hut;
  - a train journey from Cogsworth to Dust Gulch.
- **What I saw:**
  - **Drawing:** both paths draw the same scenes. The seams that used to be zone edges are invisible on both. The area name shows when crossing into the town.
  - **An interrupted walk:** I tapped far west, then tapped east after 0.45 s. The walk ended where the second tap sent it and was still there 4 s later; walking west alone ends somewhere else. Both paths ended at the same spot.
  - **An inactive screen mid-walk:** the walk stops where it is, with no stale arrival after the screen comes back, and the scene holds still while hidden.
  - **Reduced motion:** a walk arrives at once and the world holds still. With motion on, the water moves.
- **Errors:** none in the console.
- **Native was not tried.** The tiles on native are React Native `Image`s at 2x, which iOS and Android scale with linear filtering. They will be slightly soft until question 1 below is settled. I am noting this, not claiming it was tested.

**Memory, measured in the browser.** These are the decoded pictures in the page: every distinct ground, tile and moving-water picture in the DOM, width x height x 4, in MiB.

| Scene (402 x 874, DPR 3)          | Zones: ground and water | World tiles: ground and water |
| --------------------------------- | ----------------------- | ----------------------------- |
| The hub, at the garden            | 78.2                    | 6.3                           |
| The hub, walked out to the town   | 77.6                    | 9.0                           |
| Dust Gulch into the Scorched Pass | 29.1                    | 6.6                           |
| Neon Harbour, walked north        | 47.1                    | 8.0                           |
| Inside the hut                    | 14.1                    | 6.2                           |
| The isles, at Lagoon Landing      | 67.5                    | 15.5                          |
| After the journey, at Dust Gulch  | 22.8                    | 8.3                           |

**What remains costly is the scenery past the world.** The `zones/scenery` cells are saved at 4x: 1440 x 2464, 13.5 MiB each. At a region's edge, two to five of them are mounted (54 to 68 MiB at the gulch and the isles). This is the same on both paths. It goes when v4's chunks draw their own frame; until then, those cells could be saved at 2x for a quarter of the cost.

### Still open

1. **Native 1x crispness.** Should native draw the tiles with Skia's nearest filter (in a `.native.tsx`), use a small native view that sets the layer's magnification filter, or go back to 4x? This needs a device test before choosing. Until then, 2x.
2. **The search window's margin.** It is 2 then 4 tiles today. Should the companion show it is "looking for a way" when a walk falls back to the route graph?
3. **The route graph across chunks.** Routes and the land between will add portals where chunks meet. Should a train shortcut be an edge with its own cost and a ride? The ways close edges (with #118).
4. **Data size.** `lib/world-canvas.ts` is about 240 KB with the route graph. Split it per plane and chunk, and load per-tile walk and terrain as JSON, once the continent grows past about 1 MB.
5. **Decks on the canvas path.** They are drawn and walked by the whole-grid path; there are none today.

## Step 3: saves and tests (Claude A with Codex)

- **One layout version.** `lib/world-layouts.ts` maps each old zone to its area and each old stand to its new stand. A saved `WorldSpot` (a region and a point) gets plane plus world = origin + point, so it lands at the same place. `visited` keeps its ids where an area keeps its name.
- **Saves** (Codex, `lib/save-data.ts`): migrations and tests for spots, visited places and the ways.
- **Tests move to world coordinates:** `lib/region-walk.test.ts`, `lib/home-hub.test.ts`, the ways' tests and the hub block of `scripts/check-garden.cjs`.
- **Then the zones retire.** `zones.py` stops writing `assets/zones/**` and `lib/zone-*.ts`. `frames.PORTS` inside the continent, the border-continuity lint and `beyond()` between zones go. Regions, routes and the land between are painted as chunks on their v4 origins (plan P4 to P7).
