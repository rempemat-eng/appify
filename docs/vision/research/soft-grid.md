# Soft grid: terrain, objects and height on an 8 px grid

Research for Claude A, 19 Oct 2026, after Matt's decision (23:01) to move NapAttack to a soft, natural grid like Eastward's Strange Forest, and his ask (23:24) to "really make sure you hone in on the soft grid logic and what that means for objects and verticality". It builds on `docs/vision/verticality.md` (4a toolkit, 4f grid-led terrain and side faces, 5 scale) and does not repeat `docs/vision/research/placement-paths-verticality.md` (layers, decks, Solarus, RPG Maker bridges, Pokemon ledges, ALBW, path generation).

How to read it. Sourced claims carry a number that points to the source list at the end. **(Observation)** marks something I measured or saw myself on official Steam store screenshots or one third-party guide image; no developer states it. **(Inference)** marks my reasoning. Pixel measurements were taken by finding each screenshot's pixel scale with a Fourier transform of its edges (Eastward, Sea of Stars, Moonlighter and most Chained Echoes shots are 3x of a 640 x 360 frame; CrossCode is 2x of 568 x 320; Stardew is 4x of 480 x 270), resampling to native pixels and laying an 8 px grid over them. They are approximate (plus or minus 2 px).

---

## 0. The short version

- **The grid is structural, not visible.** In Eastward I could find no repeating tile pitch at all: the edges in every official screenshot run straight and orthogonal, but the textures never repeat on a fixed period, and the step from one straight run to the next is not a multiple of 16 (Observation, section 1). Pixpil say they "handcrafted every single detail" [1], painted in Photoshop [3], and rebuilt assets in 3D for bump-mapped lighting [1]. So the "soft grid" look is: orthogonal layout, straight runs, rounded corners, roughness within a few pixels of the line, and no tile seams.
- **Only the south face is a face.** In CrossCode's height tool (as reimplemented by the community editor), wall art exists for south faces, 45 degree diagonals and two "wall end" pieces; the east and west sides of a raised level are drawn as edge tiles on the top surface plus shadow tiles, with no wall face at all [8]. Stardew and Eastward show a narrow strip at most (Observation).
- **Faces are built from rows.** CrossCode's wall art is a start row, a looping middle (two rows that alternate) and an end row at the foot, so any height composes [8]. Levels in its sample maps are 32 px apart, two 16 px tiles; levels beyond the defined ones default to two tiles [8].
- **Objects declare footprints in tiles.** Stardew buildings have a `Size` in tiles, an X/O `CollisionMap`, a door tile, a sort offset, a shadow flag and a fade-when-behind flag [11]. Map tiles on the Buildings layer act as walls; the Front layer draws over the player only when the player is north of it [12].
- **Height makes density.** Pixpil: "elevation is your friend to make an area feel dense!" and "Staircases in a bustling city let the player move behind buildings without being totally obscured" [1].

---

## 1. Grid and scale in the reference games

### 1.1 Tile size relative to the characters

| Game | Tile or grid | Character height | Cell / character | Source |
| --- | --- | --- | --- | --- |
| Stardew Valley | 16 x 16 tiles [12] | farmer frame 16 x 32 [13] | 0.5 | [12] [13] |
| CrossCode | 16 x 16 tiles ("1 equals 1 Tile(16x16 pixel)") [9]; collision art `collisiontiles-16x16.png` [10] | Lea about 31 px (Observation) | about 0.5 | [9] [10] |
| Link's Awakening (Game Boy) | 16 x 16 room tiles, each 2 x 2 hardware 8 x 8 tiles ("one for each 16x16 tile on the screen") [14] | Link fills about one tile (Observation) | about 1.0 | [14] |
| Eastward | no tile pitch found (Observation); Pixpil tested "some tile based scene" in Jan 2016 [4] | adults 48 to 52 px, Sam about 45 (Observation, 640 x 360 frame) | unknown | [1] [3] [4] |
| Sea of Stars | not published; the studio says movement "breaks free from the classic bound-to-the-grid tileset movement" [16] | Garl about 47 px (Observation, 640 x 360) | unknown | [15] [16] |
| Chained Echoes | not published | about 35 px in the tavern shot, about 45 in a cutscene shot, so the camera zooms (Observation) | unknown | [17] |
| Moonlighter | not published | Will about 32 px (Observation, about 634 x 356) | unknown | [18] |
| **NapAttack** | **8 px grid** (verticality.md 4f) | **adult 25 px** | **0.32** | |

What this means:

- Grid-built games with published formats (Stardew, CrossCode) use a cell about half a character tall. Our 8 px cell against a 25 px adult (0.32) is finer, which is what you want for a soft grid: corners can round over one cell and roughness can sit inside it.
- **Correction to verticality.md 4f.** It says our 8 px grid is "close to Eastward's tile (about 0.45 of an adult)". On the official Steam screenshots Eastward's adults are about 50 px in a 640 x 360 frame. If Eastward were built on 16 px tiles, that tile would be 0.32 of an adult, the same ratio as our 8 px against 25. I could not confirm any tile pitch, so the honest statement is: our cell-to-adult ratio matches a 16 px grid at Eastward's scale, and Eastward's grid is not documented. (Observation)
- Pixel art practice puts most tiles at 16 x 16; Schlitter: "16x16px is probably the most common size", and "Anything over 32x32px seems like overkill for pixel art" [19].

### 1.2 How strictly terrain follows the grid

- **CrossCode** is strictly tiled: maps are 16 px tiles, levels are stacked layers, and its height tool converts a height map into tiles with square, round and 45 degree diagonal fills (`FILL_TYPE`: ROUND, SQUARE, NORTHEAST, SOUTHEAST, SOUTHWEST, NORTHWEST) [8]. Its jungle screenshot shows rock faces with straight and 45 degree runs and a waterfall exactly as wide as its channel (Observation).
- **Stardew** is strictly tiled for collision and layers [12], but its grass and dirt boundaries wander freely across tile lines (Observation, farm screenshot: a dirt path edge crosses 8 px grid lines at every angle). The tiles carry the organic edge inside them.
- **Eastward** layouts are orthogonal at every scale I looked at: plazas, platforms, water channels in the Strange Forest, building rows (Observation). In the Strange Forest cave, the terrain masses' edges hold a straight line with a wobble of 2 to 3 px (I measured one top edge at y 264 to 267 over 130 px, one side edge at x 62 to 65 over 120 px), and the steps between runs were 52 px and 80 px, not a 16 multiple (Observation, guide image [5]). The plaza checkerboard in the subway screenshot repeats every 34 px across (two squares of 16 and 18) and is foreshortened (squares about 17 x 12), so it is painted, not tiled (Observation).
- **Sea of Stars** goes the other way: its waterfalls tumble through rounded boulder tiers and its coasts are free curves (Observation); the studio wanted traversal that moves "as far away from tile-based movement as possible" [15].

### 1.3 How they hide the grid

- **Overlap across the seam.** Schlitter: "Include clusters that overlap the edges and loop around the tile to help hide the seems", mix "spaces of flat green with textured areas of differing vegetation density", and make side and corner variants "by shaving off portions of the base texture" [19] [20].
- **Low-probability variants.** Tiled gives each tile a probability; a decorative variant at 0.01 is "100 times less likely to be chosen than the regular" tile [6].
- **Offset decoration.** LDtk added rule tile "X and Y offsets", fixed or random, which "will make much easier creation of organic elements like vegetation, dirt etc." [22]; also modulo rules ("only apply every X columns or Y rows"), perlin noise areas and multi-tile groups for "larger objects, such as a tree or a big rock" [23].
- **Free props over the ground.** Eastward and Stardew both stand tall grass, bushes, rocks and trees over the terrain edges (Observation). The RPG Maker team's cliff advice: "Make sure your straight sections aren't too long", watch "when round tiles hit straight ones", and drop decorations "randomly", avoiding "lines" or "squares" [24].
- **Lighting and grading.** Eastward's deferred lighting, bump maps, SSAO and LUT grading soften the art [1] [2] (section 5).

---

## 2. Cliffs and ledges from tiles

### 2.1 Autotile conventions

- **Corner sets and edge sets** need 16 tiles for two terrains; **mixed sets** need 256, and the 47-tile "blob" is the usual reduced set [6]. The blob is "a 47 tile subset of a 2-edge 2-corner Wang tileset", built so that "no tile has a blue edge between two yellow corners" [7].
- **Dual grid.** Draw the art on a second grid offset by half a tile, so each drawn tile's four corners sit on four logic cells; the example code sets `meshMap.pos = vec(-8, -8)` for 16 px tiles and needs about 5 or 6 drawn pieces with rotation instead of 47 [25]. That article credits videos by ThinMatrix, jess::codes and Oskar Stalberg's "Beyond Townscapers" talk [25]. Plain marching squares needs 16 [25].
- **RPG Maker MZ** tiles are 48 px; ground autotiles (A2) are built from half-tile parts, A3 holds buildings and A4 holds walls, both laid out 8 tiles across [26].
- **Recommendation (Inference).** For a top surface on our 8 px grid, a corner (dual-grid) lookup is the cheapest way to get rounded rims: 16 cases per terrain pair from the tier mask, drawn by code. Faces are not autotiles at all: they are composed per column from rows (2.2).

### 2.2 How a raised level is built (CrossCode, the clearest case)

From the community CrossCode map editor's height-map generator, which rebuilds levels from a height map onto the game's own tilesets [8]:

- **Wall art exists only facing the camera.** The generator's tile kinds are: top surface `FILL`; top edges `NORTH`, `EAST`, `SOUTH`, `WEST`; top corners `CORNER_NE/SE/SW/NW`; rounded or square corners `SQUARE_*`; diagonals `DIAGONAL_*`; and walls `WALL_SOUTH`, `WALL_SE`, `WALL_SW` (diagonal faces), `WALL_SQR_SE`, `WALL_SQR_SW` (corner faces) and `WALL_END_WEST`, `WALL_END_EAST`, each with a `_BASE` (foot) variant. There is no `WALL_EAST` or `WALL_WEST` [8].
- **East and west sides are edges plus shadow.** `EAST` and `WEST` are two-variant edge tiles on the top surface (`[[3, 1], [3, 2]]`, `[[2, 1], [2, 2]]`), and the lower ground gets `SHADOW` sub-tiles for `NORTH`, `WEST` and `EAST` [8].
- **Faces are rows.** Each south wall uses `{loop: [1, 2], end: [0]}`: two middle rows alternate for any height and a fixed end row sits at the foot [8]. A chasm wall has a `start` row instead [8].
- **Height per level.** Wall height in tiles is `level.height / TILE_SIZE`; levels past the defined ones add `2` tiles each [8]. The editor's sample maps space levels at 0, 32, 64 and 128 px [8]. So one level is usually two tiles: about one Lea tall (Observation: Lea about 31 px).
- **The north side** is not a wall: `NORTH` links to a south wall drawn one row up on the lower level as shadow only (`shadowOnly: true, toMaster: true, deltaY: -1`) [8].
- **Waterfalls** fall straight down a face, exactly as wide as the stream, with a foam band where they land (Observation, CrossCode jungle screenshot).

### 2.3 Stardew and Eastward details

- **Stardew cliffs**: a grass lip overhangs a cobbled rock face; where the plateau ends to the west, a strip of lit earth about 3 to 4 px wide runs down the screen beside the grass (Observation). Placing a building keeps its stairs clear through `AdditionalPlacementTiles`, the farmhouse being the example [11].
- **Eastward dungeon platforms**: a top surface, a south face of about 30 px (0.6 adult) with a 6 px lit coping band, and west and east sides drawn as 2 to 3 px rim lines on the top with no face (Observation).
- **Eastward station platform**: a low step with a face of about 11 px (0.2 adult); each end is capped by a short parapet block, lit on the west end and darker on the east (Observation).
- **Eastward Strange Forest**: banks drop to water with a short dark face and a lit lip; higher ground beyond reads as large silhouette masses with bumpy edges, and a tall rock face fills its whole area with rounded cobbles (Observation, guide images [5]).

### 2.4 Shadows from ledges

- Schlitter: drop shadows "must be conservative in design to limit conflict with sprites", "limit them to one or two wall faces, minding light source", they "should not exceed a tile in length", and "No matter how tall the rock wall all shadows are the same length" [20].
- RPG Maker's cliff guide avoids auto-shadows on rounded cliffs because "the square shadows and the slightly rounded cliffs just don't work well" and suggests drawing custom shadow pieces [24].

### 2.5 Height consistency

"Height consistency is key": a plateau has "one consistent height over the whole plateau"; unconnected plateaus may differ; every variation must stay consistent [24].

---

## 3. Objects on the grid

### 3.1 Footprints, anchors and collision

- **Stardew buildings** [11]:
  - `Size`: "The building's width and height when constructed, measured in tiles."
  - `CollisionMap`: "An ASCII text block which indicates which of the building's tiles the players can walk onto", `X` blocked and `O` open, e.g. `XXXX` over `XOOX` for a stable whose door tiles are walkable.
  - `HumanDoor`: door position in tiles from the top-left tile.
  - `SortTileOffset`: "A Y tile offset applied when figuring out render layering"; 2.5 "will treat the building as if it was 2.5 tiles further up the screen".
  - `DrawShadow`: "an automatic shadow along the bottom edge of the building's sprite".
  - `FadeWhenBehind`: "semi-transparent when the player is behind it".
  - `AdditionalPlacementTiles`: extra tiles kept clear when placing, for example the farmhouse stairs, optionally `OnlyNeedsToBePassable`.
- **Stardew map tiles** [12]: "Any tiles placed on this layer [Buildings] will act like a wall unless the tile property has a "Passable" "T""; Front objects are "drawn on top of the player if the player is North of them"; AlwaysFront objects are "always drawn on top of other layers as well as the player", used for "foliage cover". Tiles are 16 x 16 [12].
- **CrossCode entities** are placed freely: x and y "in pixel" plus a `level` index; layers belong to levels [9]. Its pathfinding works on rectangles covering several tiles, with "jump-up" and "jump-down" edges between levels [27].
- **Eastward assets are modular**: "we divide the single assets into different parts according to their natural structure", then "rebuild all the assets in a 3D environment, ready to be hand painted in the bump map one by one" [1].
- **Link's Awakening** builds rooms from 16 x 16 objects made of 2 x 2 hardware tiles [14].

### 3.2 Depth sorting with heights

- **CrossCode**: the community editor sorts entities by level first, then by y (`zIndex = level * 10 + 1`, plus `y * 0.000001`), and layers by `level * 10` [8]. That reproduces the game's rule that everything on a higher level draws after the lower level (Inference from the editor).
- **Stardew**: layers draw back to front; Front swaps with the player by north and south; buildings sort by their bottom row unless `SortTileOffset` moves it [11] [12].
- **Eastward** keeps the player from being hidden: the fixed camera "forces you to adjust the world so the player is never unintentionally obscured behind the environment", and height helps "prevent elements in the foreground from occluding elements further in the background" [1].

### 3.3 Walking behind a raised tier and in front of a lower one

- With one walk level per zone and tiers drawn as ground (verticality.md 3), a foot-y sort is enough (Inference, checked case by case):
  - A walker on the upper tier stands north of the rim; anything on the lower tier south of the face has a larger foot y and draws over the walker. Correct.
  - A lower-tier building whose sprite rises over the upper tier draws over the upper ground and over a walker there. Correct, and it is the Eastward overlap.
  - Nothing on the upper tier can overlap the face, because sprites extend upwards from the foot.
  - The face, lip and grass overhang are ground, under every actor.
- A level-first sort (CrossCode) is needed only where walkable ground lies under other walkable ground: decks, which already have their own model.

---

## 4. Verticality rules

- **Levels on screen.** Eastward's subway screenshot shows three walking heights (upper street, plaza, lower walkway) (Observation). CrossCode found a tech demo stacking platforms at different heights too complex (already in the existing research).
- **Signposting.** Sea of Stars: "If it looks like you can grab on and hoist up, it's because you can", and hoisting "allows for a lot more verticality in the gameplay" [15]. Eastward uses stairs as the main connector in towns [1].
- **How ledges read from the camera.** In a top-down three-quarter view "you see about 3/4 of both the roof and facade" and the facade is shortened [21]. A south face reads by a lit lip on top, a darker face and a dark foot; a step is read by its shadow (Observation, all references).
- **What shows of a west or east wall.** Almost nothing: CrossCode draws none [8]; Eastward shows a rim line or a short end block (Observation); Stardew a 3 to 4 px strip (Observation). The cheat is to show a sliver that tells the light: lit on the west, dark on the east, with the cast shadow carrying the depth.
- **Shadows**: constant length whatever the height, at most one tile, on one or two faces [20].
- **Density through height**: "elevation is your friend to make an area feel dense!" [1].

---

## 5. What makes Eastward's grid feel soft

- **Light over pixels.** Deferred lighting [4b], "shader textures and lighting systems", "intricate fog layers and sunlight beams breaking through the landscape during dawn and dusk" [1]; a texture channel lets lights shade 2D props so they "look more stereoscopic" [2]; SSAO, CRT blur and LUT grading [3]. The LUT softens the colours [3].
- **Detail and life.** "filled with details and countless objects", "a ton of moving elements in the environment" [3]; "we handcrafted every single detail" [1].
- **Edges.** Straight runs with 2 to 3 px wobble, scalloped grass lips, tall grass and weeds over the feet of walls, foliage clusters and silhouette masses over the higher ground (Observation [5] and Steam screenshots).
- **No visible repetition.** No fixed tile period in any official screenshot (Observation).
- **Orthogonal water.** Channels and pools are rectangles with straight banks (Observation [5]).

---

## 6. What this means for NapAttack

Units are zone px. One cell = 8 px; one walk cell = 4 px (2 x 2 walk cells per grid cell). Adult A = 25. Light from the upper left.

### 6.1 Grid rules

1. **Structure snaps, texture does not.** Every rim, side column, bank, path edge, stair, ramp, waterfall and prop foot lies on an 8 px line. No texture may repeat on an 8 or 16 px period (a lint check, 6.5).
2. **Minimum run of two cells.** A straight run is at least 16 px; a diagonal is a staircase of runs of two or more cells (as 4f).
3. **Rounded corners of one cell**, by closing then opening the mask with a disc (as 4f).
4. **Roughness within 4 px** of the line, inside the edge cell: lip scallops 1 to 3 px, lumps, roots, chips, grass. Eastward's measured wobble is 2 to 3 px.
5. **Heights per plateau are constant** and come only from the set {12, 16} (low step) or {32, 40} (tier). A plateau has one height all round [24].

### 6.2 Terrain toolkit: pieces per material

`terrace.py` draws these by code, per 8 px column, seeded. Faces are composed from rows like CrossCode's `start / loop / end` [8]. Sizes are px.

**Tier top and rim**

| Piece | Size | Notes |
| --- | --- | --- |
| Top fill | 8 x 8 cells, 4 variants + decals at low probability | variants chosen by seed; decals offset 0 to 7 px [22] |
| Top corner, rounded (NW, NE, SW, SE outer; four inner) | 8 x 8, radius 6 to 8 | dual-grid lookup on the tier mask, 16 cases |
| North rim | 1 dark crease + 1 lit px, inside the top | no face; the lower ground beyond shows above it |
| South lip | 8 wide x 4 tall per column, 3 variants | lit top, lit front, mid, dark drip line; overhangs the face by 1 to 3 px |

**South face** (only face drawn at full width)

| Piece | Size | Notes |
| --- | --- | --- |
| Start row | 8 x 8 | under the lip: roots, first lumps, darker under the overhang |
| Loop rows | 8 x 8, two variants alternating | composes any height: 32 = start + 2 loops + foot; 40 = start + 3 loops + foot |
| Foot row | 8 x 8 | dark wet or weedy 4 px band, tall grass breaking over it from the lower ground |
| Low step | lip 4 + face 8 or 12 | no loop rows; treads or kerb texture by material |

**Side faces and corners** (the pieces Matt asked to get right)

| Piece | Size | Notes |
| --- | --- | --- |
| West side strip (lit) | 2 to 4 wide, rim to lower ground | inside the edge column; the lit tones; lip continues round with 1 to 2 px scallops; 1 px contact line on the lower ground |
| East side strip (dark) | 3 to 4 wide | the two darkest tones; casts the side shadow |
| Outer corner, SW (lit) and SE (dark) | 8 wide x face height | CrossCode's `WALL_END_WEST/EAST` [8]: face courses wrap and narrow over 8 px; foot band carried round |
| Inner corner (notch) | 8 wide x face height | flat floor, shaded crease, east-side shadow across the floor |
| Side cast shadow on lower ground | **8 constant**, stepped 3 strong, 3 medium, 2 dithered | constant length whatever the height, at most one cell [20]; replaces 4a's "3 px plus 1 per 3 rows" |
| Foot shadow below a south face | 4 to 8 constant | same rule |

**Cuts through a face**

| Piece | Size | Notes |
| --- | --- | --- |
| Stair cut | open width 40 (minimum 34), cheeks 4 each, so 48 on the grid; treads 4; landings 8 deep at top and bottom | cheeks follow the side rules: west lit, east dark with its 8 px shadow; x and width on 8 px lines |
| Grand stair | 64 to 96 with a centre rail | |
| Ramp | runs along the face, at least 24 wide, rise 1 in 3, rail on the open side | starts and ends on grid lines |
| Waterfall cut | notch in the lip as wide as the channel (stream 24, river 40+); fall body = face height; plunge pool 8 deeper and 8 wider each side; foam band 4 to 8 | straight down only; 2 to 3 frames, still under reduced motion |
| Tunnel mouth | 40 face: opening 36 to 56 x 32 to 36 | as 4a |

**Per material** (lip and texture differ, the piece list does not):

| Material | Lip | Face texture | Foot |
| --- | --- | --- | --- |
| earth | grass overhang 2 to 5, scalloped | irregular lumps about 13 x 9, roots in start row, stones | tall grass, dark damp band |
| rock | thin moss or grass lip 1 to 3 | stacked irregular blocks (`cliff()`) | scree, ferns |
| stone (dressed) | coping 4, lit top and front | 6 px courses of varied length | moss, damp |
| brick | soldier course under a 4 px coping | 3 px stretcher bond | white bloom |
| concrete | 4 px coping, chipped | 8 px courses, joints every 20, rain streaks | wet band, weeds |
| timber | cap plank 3 | 4 px planks on posts every 16 to 24 | rot band, grass |
| sandstone | 2 to 3 px lit stratum edge | strata 3 to 7, each lit on top | sand drift |

Count per material: about 4 top variants, 3 lips, 2 starts, 2 loops, 2 feet, 2 side strips, 2 outer corners, 1 inner corner, stair, ramp, waterfall and step sets. All functions, no atlas.

### 6.3 Props on the grid

Each prop module declares, beside `KIND`, `DOOR_RECTS` and `STOREYS` (verticality 5):

- `FOOT = (w_cells, d_cells)`: the footprint in 8 px cells (Stardew `Size` [11]).
- `ANCHOR`: the foot line's centre. Snap: the foot line on a grid row; the footprint's west edge on a grid column, or the centre on a cell centre for odd widths. A sprite is drawn up from the foot.
- `COLLIDE`: an X/O mask in 4 px walk cells (2 per grid cell each way), as Stardew's `CollisionMap` [11]; default all blocked.
- `APRON`: cells kept clear in front of doors and stair heads (Stardew `AdditionalPlacementTiles` [11]); feeds `door-shut-in`.
- `SORT_OFFSET` in px, for sprites whose visual base is not their foot (Stardew `SortTileOffset` [11]).
- `FADE_BEHIND`: keep the Ghost outline; optional fade for big buildings (Stardew `FadeWhenBehind` [11]).
- `FREE = True` only for kinds that may sit off the grid: trees, bushes, rocks, flowers, tufts, leaves, litter, puddles, wear. They jitter 0 to 7 px but their trunk or base cell still checks against paths, faces and tiers.
- Big props span whole cells: a cottage about 6 x 4 cells, a stall 6 x 2, a bench 4 x 1, a lamp 1 x 1, a tree trunk 1 x 1 (canopy free), crates and barrels 1 x 1, a well 3 x 3 (round art in a square footprint).

### 6.4 Sorting with tiers

- Keep the foot-y sort (section 3.3). Tier faces, lips and grass overhangs stay ground.
- Railings on rims are props sorted by foot y (as 4a), so they cover the feet of a walker behind them.
- Foliage over the zone's south edge goes to `fore.png` (Stardew AlwaysFront [12]).
- Use a level-first sort only for decks.

### 6.5 Lint checks (report first, then strict)

Existing from 4a and 4f, unchanged: `tier-step`, `one-tier`, `stair-ends`, `stair-width`, `face-height`, `rail-at-edge`, `upper-hidden`, `tier-seam`, `grid-edges`, `no-ellipse`, `fall-vertical`, `rim-on-grid`. New:

1. `prop-snap`: every non-`FREE` prop's foot line is on a grid row and its west edge or centre on a grid column.
2. `prop-footprint`: footprints of non-`FREE` props do not overlap, lie on one tier, and avoid face cells and stair cells.
3. `face-parts`: every rim column has lip, start, loops and foot; every face that ends at a side has an outer corner piece; every side strip ends on ground.
4. `side-width`: no west or east strip is wider than 4 px (it is a sliver, never a second front).
5. `side-light`: west strips and west cheeks use the material's two lightest tones, east ones the two darkest, and an 8 px shadow lies east of every east strip and cheek.
6. `shadow-constant`: terrain cast shadows are 8 px (foot shadows 4 to 8) on every tier, whatever the face height.
7. `edge-jitter`: along each grid-led boundary, the drawn edge stays within 4 px of its grid line.
8. `min-run`: no straight run shorter than 16 px except inside a corner's rounding.
9. `plateau-height`: all faces round one tier have the same height, from the allowed set.
10. `no-tile-repeat`: no 8 or 16 px periodic peak in a zone's ground texture (a Fourier test like the one used here).
11. `cut-on-grid`: stairs, ramps, falls and mouths start and end on grid columns.

---

## 7. Gaps

- No developer source gives Eastward's, Sea of Stars', Chained Echoes' or Moonlighter's tile size; sizes above are measured.
- The CrossCode details come from the community map editor's reimplementation of the height tool, not from Radical Fish; Radical Fish's own stream on "Auto Tiles and Height Map" (24 May 2015) exists but I did not watch it [28].
- Blocked or unreadable: Pixpil's tumblr devlog and X posts (robots), the Red Bull Eastward interview page, the "TF Mapping Tutorial: Cliff Walls" on Patreon (linked from the Stardew wiki as Draylon's cliff guide), Screen Rant's Sea of Stars interview (robots), and Boris the Brave's classification article (not reachable from here).
- The Strange Forest measurement uses a third-party guide's 640 x 360 images [5], so treat it as indicative.
- Nothing here was tested in the game or on a phone.

---

## Sources

1. Bryant Francis, "Eastward's creators share insights on making pixel art adventures", Game Developer, 11 Oct 2021 (Tommo Zhou, Pixpil). https://www.gamedeveloper.com/art/eastward-s-creators-share-insights-on-making-pixel-art-adventures
2. "Eastward: A unique Pixel adventure", CDM Techspeak blog, 4 Oct 2021. https://blogs.thecdm.ca/techspeak/2021/10/04/eastward-a-unique-pixel-adventure/
3. "Eastward: Charming Chinese Pixel Art Adventure", 80.lv. https://80.lv/articles/eastward-charming-chinese-pixel-art-adventure
4. Pixpil on X, "Testing some tile based scene. Not very fancy so far..." (Jan 2016), search snippet only. https://x.com/pixpilgames/status/686509082652479489
4b. Pixpil on X, "Pixel art + Deferred lighting. Detail screen shot.", search snippet only. https://x.com/pixpilgames/status/659937124372758528
5. Prodigy Gamers, "Eastward: How To Solve Raft Door Puzzle At Strange Forest Cave" (screenshots measured). https://prodigygamers.com/2021/09/19/eastward-how-to-solve-raft-door-puzzle-at-strange-forest-cave/
6. Tiled documentation, "Using Terrains". https://doc.mapeditor.org/en/stable/manual/terrain/
7. Guy Walker, "Blob" tileset (Stagecast mirror on boristhebrave.com). https://boristhebrave.com/permanent/24/06/cr31/stagecast/wang/blob.html
8. CCDirectLink, crosscode-map-editor (community editor), `webapp/src/app/services/height-map/` (`heightmap.constants.ts`, `height-map.service.ts`, `gfx-mapper/gfx-mapper.constants.ts`) and `test-maps/`. https://github.com/CCDirectLink/crosscode-map-editor
9. Official CrossCode Wiki, "Map file layout". https://crosscode.fandom.com/wiki/Map_file_layout
10. The Cutting Room Floor, "CrossCode" (debug tiles `collisiontiles-16x16.png`, `heightmap-tiles.png`). https://tcrf.net/CrossCode
11. Stardew Valley Wiki, "Modding:Buildings". https://stardewvalleywiki.com/Modding:Buildings
12. Stardew Valley Wiki, "Mapping" and "Modding:Maps". https://stardewvalleywiki.com/Mapping and https://stardewvalleywiki.com/Modding:Maps
13. Stardew Valley Wiki, "Modding:Farmer sprite". https://stardewvalleywiki.com/Modding:Farmer_sprite
14. zladx, LADX-Disassembly, `src/data/rooms_gbc_overlays/overworld_a.asm` and `src/code/bank0.asm`. https://github.com/zladx/LADX-Disassembly
15. Philippe Dionne (Sabotage), PlayStation Blog, 25 Jul 2023. https://blog.playstation.com/?p=382678
16. Sabotage Studio, Sea of Stars press kit. https://sabotagestudio.com/presskits/sea-of-stars/
17. Chained Echoes, Steam store screenshots (measured). https://store.steampowered.com/app/1229240
18. Moonlighter, Steam store screenshots (measured); 80.lv, "Moonlighter: Building Pixel Art, Preparing for Switch". https://store.steampowered.com/app/606150 and https://80.lv/articles/moonlighter-building-pixel-art-preparing-for-switch/
19. Raymond Schlitter, "Pixelblog 20: Top Down Tiles". https://slynyrd.com/blog/2019/8/27/pixelblog-20-top-down-tiles
20. Raymond Schlitter, "Pixelblog 43: Top Down Tiles Part 2". https://slynyrd.com/blog/2023/3/26/pixelblog-43-top-down-tiles-part-2
21. Raymond Schlitter, "Pixelblog 3: Graphical Projection Part 1". https://www.slynyrd.com/blog/2018/3/14/pixelblog-3-graphical-projections-1
22. Deepnight, "LDtk 1.3.0: Multi-worlds preview" (rule tile offsets). https://deepnight.itch.io/ldtk/devlog/522221/130-multi-worlds-preview
23. LDtk releases (modulo, perlin, groups of tiles). https://github.com/deepnight/ldtk/releases?page=5
24. RPG Maker blog, "Tips and Tricks: Mapping Cliffs". https://rpgmakerweb.com/blog/tips-and-tricks-mapping-cliffs
25. Excalibur.js blog, "Dual Tilemap Autotiling Technique" (credits ThinMatrix, jess::codes, Oskar Stalberg "Beyond Townscapers"). https://excaliburjs.com/blog/Dual%20Tilemap%20Autotiling%20Technique
26. RPG Maker MZ Help, tileset specifications. https://rpgmakerofficial.com/product/MZ_help-en/01_11_01.html
27. Radical Fish Games, "Path Finding in CrossCode", 28 Apr 2013. https://www.radicalfishgames.com/?p=498
28. RadicalFishGames, "CrossCode Dev Stream - Auto Tiles and Height Map - 1 / 2", YouTube, 24 May 2015. https://www.youtube.com/watch?v=kPlkhsNsXaw
29. Official Steam store screenshots used for measurement: Eastward https://store.steampowered.com/app/977880 ; Sea of Stars https://store.steampowered.com/app/1244090 ; CrossCode https://store.steampowered.com/app/368340 ; Stardew Valley https://store.steampowered.com/app/413150
30. Eastward also: Nintendo, "How the developers began making (then remaking) Eastward" https://www.nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward ; Game Developer, "Road to the IGF: Pixpil's Eastward" https://www.gamedeveloper.com/disciplines/road-to-the-igf-pixpil-s-i-eastward-i-
