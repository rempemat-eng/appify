# The first finished screen: the woodland at 2x

Status: a draft for Matt (21 Oct). Matt asked at 12:49 for one small part of the map finished completely, then at 12:51 for its rules to be established so the rest is easier to draw and animate. The woodland (valley, west of the garden, 320 x 576 world px) is drawn natively at density 2 (an adult 50 texels) by a library built to be lifted into kits. The terrain, tree and ground style waits on Matt's style study (13:43); every style number the painters use is data, so that verdict changes `scripts/art/biomes/woodland.json`, not the code.

## What the place is

The Hollow's escarpment stands above the north edge. At its foot a wooded shelf, 32 px up, runs across the zone in masses that step forward and back by whole cells: outcrop columns, recesses, and a bay. The Hollow's falls land on the shelf. Its brook runs to the bay and falls the shelf's cobble face into a pool, then runs south past the glade of the hollow oak to the spring pool, and leaves east as the stream on the garden's own rows. The forester keeps a woodpile under a lean-to beside the glade. The stone circle sits in its ring of trodden earth in the south-west, and the lane comes in from the garden's orchard walk. The wood is dense: belts along the north, west and south edges and two clumps, with undergrowth at their edges and crowns cut by the screen's edges.

Game function is unchanged: the same stands (garden, clearing, spring, stones), the same ports (open to the garden and to the halt, closed to the Hollow) and the forager's round. The belts are solid to the walker now (section 8 in the decisions).

## The library (`scripts/art/native/`)

| Module        | What it draws                                                                                                                                                             | Data it reads                                                |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `raster`      | parts, form shading, contact shade, the house outline, a mirrored grid for drawn west facings                                                                             | the house palette                                            |
| `terrain`     | height, faces, brook, falls, pools, stream and paths through the cliff core (`woodland` edge set: mossy packed cobbles)                                                   | the layout's `MOUNDS`, `BROOK`, `LOW_BROOK`, `POND`, `PATHS` |
| `flora`       | oak, beech, birch, pine, sapling, the hollow oak, bush, holly, bramble, fern, tuft, flowers, toadstools, pebbles                                                          | `flora` families, `style.crown`, `style.pine`, `style.tuft`  |
| `props`       | stone seat, lantern (day and lit), woodpile and lean-to, chopping block, standing stone, mossy stone, stump, log, footbridge                                              | `materials`                                                  |
| `ground`      | the floor, sun pools, banks, leaf litter, shadows (cast, dappled, the raised ground's), mass shading, contact lines                                                       | `ground`, `shadow`, `style.rock`, `style.litter`             |
| `animate`     | water (streaks, glints, lapping, the fall's ribbons) as frames of only the changing texels                                                                                | `animation.water`                                            |
| `rig`, `folk` | the character rig (proportions, a skeleton per frame, four facings, timing tables) and its first folk, Bramble and the Mossling                                           | `rig.TIMING`                                                 |
| `screen`      | a screen from a layout and a biome: the wood scattered by belts and baked into a ground layer and an overhead canopy, the dressing, the walk, the night light, the layers | the layout and the biome                                     |
| `export`      | how a native screen enters `zones.py` (a canvas in world px that saves its texels) and the character sheets                                                               |                                                              |

A second biome is a copy of `biomes/woodland.json` with its own families, plants and numbers, a layout file in `native/screens/`, and any piece it lacks.

## In the game

- `?density=2` on the web shows the woodland's art with Bramble and the Mossling a step behind (`components/folk-walker.tsx`); every other zone and the walker elsewhere stay as before. Without the parameter the woodland's pictures are the same 2x pictures (they are its only art now), drawn on the 1x grid.
- The light of the hour (`lib/daylight.ts`): dawn, day, dusk and night blended over real time, night a touch darker (0.5 against 0.42), the lanterns fading in through dusk; stepped with no blend under reduced motion.
- Moving water at 2x, packed in a 2 x 4 grid (`zoneFlowGrid`); the night light over the tint (`zoneNight`).

## Checks

`npm run check:art-density` reads the woodland's pictures as density 2. The play-test, the numbers and the comparison with Eastward are in the PR.
