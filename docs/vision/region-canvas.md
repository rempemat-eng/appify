# Region canvases: the build (step 1 of 3)

Matt decided on 20 Oct (about 10:50, world plan v2, decision 2) to replace the fixed 320 x 576 zones with one continuous canvas per region on the 8 px grid, streamed in 256 x 256 render tiles, with the zones becoming named areas. At 10:58 he asked for one connected world: the regions on one continent, joined by walkable routes. World plan v3 (branch `claude-a/world-plan`) will say whether that is one world canvas or region canvases joined by routes. This build works for both.

This is step 1, the build. **Nothing in the game changes yet.** The zones are still drawn and saved as before (`assets/zones/**`, `lib/zone-maps.ts`, `lib/zone-assets.ts`), and the game still reads them. The new outputs are written alongside and checked against the zones.

## The model: a canvas is a rectangle of the world

- **Planes.** The world has planes: `continent` for the land you walk (the valley, Cogsworth, Sunstone Reach, the isles, Neon), and one plane each for places you reach by rocket or through a door (`orbit` for Halcyon Station, `moon` for Lumen, `hut` for the inside of the nap hut).
- **Canvas.** A region's canvas is a rectangle on its plane with an **origin** in world pixels: world = origin + region px. Canvases, origins and areas sit on the 8 px grid. A canvas may be any size.
- **World tiles.** Tile (col, row) covers world px `[col * 256, row * 256]` to `[(col + 1) * 256, (row + 1) * 256]`. Its picture is built from every canvas on the plane that reaches it, so two canvases that touch share a tile with no seam. Tiles are always 256 x 256 (transparent where no canvas reaches). A tile with no ground has no picture.
- **World coordinates everywhere.** Props, stands, areas, deck connectors and the walk grid's origin are in world px. Walk rows are in 4 px cells from the canvas origin. Nothing assumes a region is a closed box: a canvas can touch another on its plane.
- **Placeholder origins.** Until v3 places the regions, `PLACES` in `scripts/art/regions.py` sets them in a row on the continent, a tile apart, with the valley at the world's origin (so the valley's world px are today's region px). Moving a region means changing its origin there. The build renames its tiles and moves every coordinate with it.

## The pipeline

`scripts/art/zones.py` draws the zones as before. At the end of its run it passes the built zones to `regions.build_all()` (`scripts/art/regions.py`), which:

1. **Gets each region's canvas.** If a lane has registered a painter for the region, the build uses it. Otherwise the **adapter** (`from_zones`) assembles the canvas from today's zones (the zone functions and `LAYOUT`). Each zone's ground, props, stands, blocked ground, walk, terrain, deck and moving water is placed at its offset. Props and stands are renamed `zone:id`. The garden (the valley's 0, 0) brings its ground (`assets/garden/ground.png`) and its walk. Its walk follows the rules `lib/region-walk.ts` applies today: the gate and the ridge trail open, and the west and east edges closed two cells deep outside their ports. Its props stay the garden's own. The areas are one rectangle per zone, plus `garden` (kind `garden`).
2. **Finishes it** (`finish`). This step derives what a painter leaves out (walk, terrain and moving water) and checks that every area is on the grid and inside the canvas and that every walkable cell lies in an area.
3. **Reports the seams.** For an adapted canvas, it walks the whole canvas by the zone rules (`derive_walk`, the same rules with no seams) and records each cell where the result differs from the joined zone grids. These differences are reported in `seams`, not hidden. Step 2 decides which to keep (see below).
4. **Writes the world** (`write_world`) to `assets/world/<plane>/`:
   - `t_<col>_<row>.png`: the ground of one world tile, at `TILE_SCALE` (nearest neighbour). Negative numbers are written `m1`.
   - `f_<col>_<row>.png`: that tile's moving water and lava (from `water_flow.py`). The box round it is cut out and its 8 frames are stacked, at 1x, the same as the zones' `flow.png`.
   - `d_` / `s_<col>_<row>.png`: a deck and its shadow over the tile (none today).
5. **Exports** `lib/region-canvas.ts` (typed data: `regionCanvases` with plane, origin, size, areas, props, stands, walk, terrain, decks and seams; `worldTiles`; `worldTileFlow`; `worldTileDecks`) and `lib/region-canvas-assets.ts` (each tile's picture imported one by one, so they bundle on native). They are split like `zone-maps.ts` and `zone-assets.ts`, so tests can read the data without loading pictures. Nothing in the app imports them yet.

The whole region build takes 16 to 25 s inside `zones.py`'s run (about 4 min 20 s in total here; it was 4 min 0 s before). The art-repro check's per-generator timeout went from 5 to 10 minutes to leave room.

## Painting a region directly

A lane that draws a region whole registers a painter in place of the zones:

```python
import regions, zones

@regions.painter('steam')
def cogsworth() -> regions.RegionCanvas:
    rc = regions.RegionCanvas('steam', 704, 960)   # any size on the 8 px grid
    # draw on rc.ground (a PIL RGBA image in canvas px; a pixel.Canvas's .img works too)
    rc.objects.append(('clock-tower', 'clock_tower', 312, 96))   # sprite top-left, canvas px
    rc.stands['terminus'] = (360, 820)
    rc.blocked |= canal_pixels                      # water, cliffs, walls drawn in the ground
    rc.areas += [{'id': 'junction', 'kind': 'zone', 'rect': (0, 0, 704, 480)},
                 {'id': 'hill', 'kind': 'zone', 'rect': (0, 480, 704, 480)}]
    return rc
```

`finish()` then derives the walk (a prop's foot band blocks, gateways excepted; drawn obstacles block; the cell beside lava is kept back from; ground the canvas does not cover blocks), the terrain (`world_lint.classify` over the whole canvas) and the moving water (`water_flow.sheet` over the whole canvas, so a river runs on across what used to be a seam). An area can be any shape: give it `cells`, walk rows of its rectangle with `.` inside. Areas give the names, the map, saves and the ways their places.

Until step 2 the game still reads zones, so a painted region must also cut its canvas back into zones for the game, as `isle_zones.island()` already does. The painter path has been run on the isles' and Sunstone's adapted canvases. The terrain it derives matches the joined zones' cell for cell. Its moving water differs slightly from the joined zones' only along the old seams, where it now runs on.

## Tile scale and memory

The plan's decision 8: 1x pictures with nearest-neighbour scaling if that is crisp on iOS, Android and the web, 2x until then. The numbers below come from these outputs. Each mounted count uses a 301 x 655 art px phone view (plan section 3) with the renderer's 24 px mount margin (`MOUNT_MARGIN`), slid in 16 px steps over every region (15,238 positions). A zone is mounted when it intersects the margin box, which is close to, but not the same as, `zonesToMount`. Sizes are RGBA bytes decoded (MiB).

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

The worst case for moving water is now its largest share. Each tile's flow is a full box of 8 frames. Step 2 could cut it down (only the pixels that change, or fewer frames), but this step keeps it as it is so that nothing changes.

**Crispness on the web: verified.** A 1x tile was drawn in headless Chromium (Playwright 1194) inside `data-pixel='true'`, using the rule from `global.css` (`image-rendering: pixelated`). At 3 device px per art pixel (DPR 2 and DPR 3) and at 4 (DPR 3, the 402 px phone), every device pixel equalled its art pixel: 0 of 90,000 differed. Without `data-pixel`, 31 to 43 % differed (smoothed). The renderer must keep the tiles inside a `data-pixel` view. Safari and Firefox were not tested.

**Native: not tested here.** React Native's `Image` has no filter setting. iOS (`UIImageView` / Core Animation) and Android (Fresco) scale bitmaps with linear filtering by default, so a 1x tile would likely be soft on a phone. Getting nearest-neighbour scaling there needs a native measure, for example a small view that sets the layer's magnification filter, or drawing the tiles with Skia's nearest filter. Step 2 tests this on devices.

**Default: 2x** (`TILE_SCALE = 2` in `regions.py`; `REGION_TILE_SCALE=1` builds at 1x), as the plan recommends until 1x is shown crisp on all three platforms. 2x already cuts the mounted ground from 45 to 101 MiB down to 8 to 12 MiB. 1x would save another 6 to 9 MiB per view.

## The check

`npm run check:region-canvas` (`lib/region-canvas.test.ts`, part of `npm run check`) checks:

- every region has a canvas the size of its zone grid, on the 8 px grid, and canvases on a plane do not overlap;
- the areas are the zones (and the garden) at their places, and every walkable cell lies in one;
- the walk equals `regionWalk()` from `lib/region-walk.ts`: the zones' grids joined exactly as the game joins them today, garden included;
- each zone's terrain, props and stands are its own, moved to world coordinates;
- the tiles reassemble the zones' ground pictures **pixel for pixel**. Every tile is 256 px times the scale, and each block of the scale is one colour (nearest neighbour). There is a picture for exactly the tiles that have ground. This compares 9,175,040 art pixels.
- each tile's moving water equals the zones' moving water, frame for frame (41,943,040 values);
- every reported seam difference lies within 20 px (the deepest foot band) of a zone seam.

It fails if a single tile pixel is changed (tried). `npm run check:art-repro` regenerates the outputs from scratch and compares them byte for byte (`lib/region-canvas*.ts` and `assets/world/**`).

**The seam report today:** 22 cells, all "shut" (a walk over the whole canvas would block cells that the joined grids leave open):

- valley, 11: ten cells along the Town's south edge, where props standing at the top of the Harbour reach their foot band 4 to 8 px over the Harbour's north edge (`share_feet` closes the ground only for east and west neighbours); and one cell on the Headland's west edge, where the step back from a cell read as lava in the Harbour is cut off at the zone's edge.
- isles, 11: the same north-edge foot bands, at the Rainforest and Headwaters' south edges, from props in the Landing and the Cove.

Step 2 should keep the whole-canvas walk. These cells are where a prop's foot crosses a seam, which the canvas fixes.

## Step 2: the renderer and the walk (Claude A, one PR)

- **Mount tiles, not zones.** `tilesToMount(plane, view)` gives the world tiles the camera sees plus the 24 px margin (at most 12). Each tile is drawn at `col * 256`, `row * 256`, snapped to whole device pixels as the zones are today, under a `data-pixel` view, with its flow layer (`worldTileFlow`; the clock and reduced motion work as they do for zones now). Props are drawn from `regionCanvases[region].objects` in world px, sorted by foot. `zoneReach` and the 48 px overhang rule go.
- **One walk grid.** `regionWalk` reads `regionCanvases[region].walk`; `tileAt` becomes `areaAt`; `tileOrigin`, `GARDEN_OPENINGS` and the garden's edge spans go. Settle the 22 seam cells (take the whole-canvas walk). Decks carry over in world px (`decks`, `deckWalk`).
- **Areas for names.** The area name under the HUD, with the same hysteresis. The map tiles are drawn per area.
- **The garden** joins the valley's canvas fully: its stream and pond overlays and its props move into the canvas, or stay drawn by the garden's renderer at the garden area's offset.
- **Test 1x on devices.** Build with `REGION_TILE_SCALE=1`, look at it on iOS, Android and the web at 3 and 4 device px per art pixel, and switch the default if it is crisp.
- Check that the mounted set covers the view at every window size, that the memory per frame stays under a budget, and that there is no gap between tiles (sub-pixel).

## Step 3: saves and tests (Claude A with Codex)

- **One layout version.** `lib/world-layouts.ts` maps each old zone to its area and each old stand to its new stand. A saved `WorldSpot` (a region and a point) gets world = origin + point, so it lands at the same place. `visited` keeps its ids where an area keeps its name.
- **Saves** (Codex, `lib/save-data.ts`): migrations and tests for spots, visited and the ways.
- **Tests move to world coordinates:** `lib/region-walk.test.ts`, `lib/home-hub.test.ts`, the ways' tests and the hub block of `scripts/check-garden.cjs`.
- **Then the zones retire.** `zones.py` stops writing `assets/zones/**` and `lib/zone-*.ts`. `frames.PORTS` inside a region, the border-continuity lint and `beyond()` between a region's zones go. Regions are painted whole (P4 to P7 of the plan), on their v3 origins.
