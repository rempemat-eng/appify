# The world editor

Status: design and first prototype (Claude A, 27 Oct). This first stage has the terrain kit's renderer and its first material pair: lawn, a packed-earth path and the turf-over-path transition. The piece schema and its validator are in, and the work split below is ready for the Codex handoff. Tiers, water, props, the dock, the validator on scenes and the woodland rebuild follow once Matt has steered this stage.

## Why

Matt, 27 Oct 13:40: "you dont need to draw every piece of path, water etc. individually all the time if you first create paths, water, lawn, sandy desert, stony mountain terrain and other background parts and perfect them ... like in a simulation game you can then pretty much plant these parts in the scenery, make some adjustments here and there to make it fit better and you're done ... you create a prop, path etc. that can be placed on the soft grid, you save it and you can use it any time".

13:43: "when creating the prop/background in the first place you need to make sure it adheres to the standard before you apply it everywhere". He also said the first terrain list "is not everything the game needs, that needs to be expanded later". He asked how ChatGPT (Codex) can take the mechanical work so Claude's tokens go to the art.

13:46: "put a lot of care into all the info each prop/part has stored (size... on the grid, where can/cannot be placed, shadow, does it tie into the story/a character, does it have a special feature/functionality ...)".

Today each zone's ground is one picture painted by Python (`screen.py`, `town.py`, `undercroft.py`), and every fix repaints it. The editor replaces that with a library of perfected pieces placed on the soft grid. The painters stay. They now paint pieces once, not zones.

## Architecture

```
game/kit/pieces/<kind>/<id>.json      the library: one piece per file (schema: game/kit/schema/piece.schema.json)
        |  python3 -m scripts.art.kit.build     (paints only what changed; the soft-grid painters)
        v
game/kit/terrain/                     fills, transition tiles, palette, materials.tres, manifest.json
game/kit/props/<id>.tscn              prop scenes generated from their piece (stage 3)
        |
        v
zones/<zone>/<zone>.tscn              a Zone: Ground (TerrainGround + Cells TileMapLayer), Tiers, Water,
                                      Decals, Props (piece instances), Actors, Spawns, Doors
        ^  game/tools/kit_zone.gd    <->  game/kit/zones/<zone>.json   (the compact plan; round trip)
        |
validator: the ground rules (scripts/review/ground_rules.py) on the scene's cell and piece metadata,
           live in the dock while placing, and in check:godot / review:scene before a PR
```

The data is authoritative. A zone holds which material is in each cell and which piece stands where. It holds no pixels. The pictures come from the kit when the zone is drawn, so a fix to a piece reaches every zone without repainting any of them.

## The kit: terrain

### Dual grid, not the 47-tile blob

The logical layer (`Cells`, a Godot `TileMapLayer` with `kit/terrain/materials.tres`) holds one material per 24-texel cell (8 world px). The picture is drawn on a second grid, offset by half a cell. Each display tile is centred on a cell corner and shows a quarter of each of its four cells. Its look depends on 4 bits (which corners hold the upper material), so a material pair needs 16 tiles (14 transitions) where a blob set needs 47.

Why dual grid:

- **It is the soft grid's own geometry.** `softgrid.py` already traces a plan as "the cell mask laid on the texel grid" (its dual-grid outline). Outlines run along cell lines through the middle of display tiles, so a rounded corner (0.4 cell outer, 0.25 inner) sits whole inside one tile.
- **It is simpler.** With 16 masks, lump profiles per crossing are affordable, and so are many material pairs.
- **It handles several materials at a corner.** Materials are layered by priority (turf over a path, a path over sand). Each higher material is laid over the one below it with its pair's tiles, so three materials meeting at a corner need no special tiles.
- **Painting is ordinary.** People paint cells, not edge tiles. The editor needs no peering bits.

Godot's built-in terrain autotiling (corner matching) works on the cell grid itself and puts a coloured tile in each cell. It cannot offset the display by half a cell, and it cannot draw a fill by world position. Both are needed below, so the logical layer uses Godot's TileSet and painting tools while the picture comes from the kit's shader.

### Fills: one perfected texture per material, never repeating

A material's inside is painted once by its soft-grid painter as a periodic texture, 768 texels square (32 cells; `scripts/art/kit/fills.py`). Its right edge runs into its left edge and its bottom into its top, so it tiles without seams.

It is laid by world position (texel mod 768), so every cell shows a different part of it and nothing repeats within a screen: the screen is 960 texels wide, the period 768, and props and decals break it further. The lawn and the path are `softground.lawn` and `softground.dirt` made periodic in three ways:

- noise on a wrapped lattice;
- wrap-around morphology;
- every tuft, blade, flower and pebble stamped at all nine periodic copies.

The look is the approved woodland's, painted by the same recipes.

### Transitions: operations, not colours

A transition tile (`scripts/art/kit/edges.py`) does not store colours. Each texel is an operation on the palette codes under it:

| Op | Meaning |
| --- | --- |
| keep | show what is below |
| upper + delta | the upper material's fill, stepped along its own ramp |
| delta | what is below, stepped (the shadow under the turf's north lip, a lit row) |
| absolute | a palette code (kept for kerbs and banks) |

So one tile fits any position of the fills and any lower material of its class, and light and shade stay on the house ramps (`palette.step`).

The lawn-over-path tiles draw `softground.sunken_edge`'s bands along the outline:

- the turf's dark underside and a row of shadow on the dirt under a north lip;
- the lit south lip;
- the shade at a west edge and the lit east turf;
- the turf thinning (a tone down) at the edge.

**The outline.** Along every cell edge between two materials, the outline is displaced by a lump curve: one of four smooth profiles over the whole cell edge (24 texels, lumps 12 to 24 long and 1 to 3 deep, out, in, out-then-in, leaning), chosen by a hash of that cell edge's place. A cell edge is split between two display tiles at its middle, and both draw the same curve, so lumps run across tile borders with no seam and no flat stretch.

The curves meet at zero at the grid vertex in a tile's middle, and the corners are rounded there with radius 8 texels outer and inner. That is a third of a cell, the largest that leaves the border strips untouched; eastward-edges.md asks for 0.4 and 0.25. A lane turning reads as a rounded bend, and a single lawn cell inside a path is a rounded turf patch.

A mask's tiles are its crossings' profile combinations: 16 per mask, 256 for the two diagonal saddles, 704 for a pair (`edges.layout`). Everything in a tile follows from its mask and its profiles, and `test_kit.py` checks the border strips of every tile against each other.

**Dressing.** What is random (tufts on the south lip, blades hanging from the north lip, pebbles across the edge) is not in the tiles. It is edge dressing (`scripts/art/kit/dressing.py`): small decals from softground's own tuft and pebble recipes. Each cell edge of a dressed pair gets at most one, chosen by a hash and seated on the lumped outline. The transition's piece sets the density and the decal lists. Godot (`world/terrain/terrain_dressing.gd`) and `compose.py` place them identically.

**Fills per look.** The woodland path is calm packed earth. It uses `fills.dirt` with the clods' joints in the damp sibling at the body's tone, few lit rims and sparse stones. The cobbled look (most joints showing dark) is its own material, `cobble_road`. Ruts follow a route's direction, so they come with the route tool as decals, not with a fill.

### The renderer

`game/world/terrain/terrain.gdshader` draws a `TerrainGround` node's whole rectangle in one pass:

1. Read the four cells round the texel's display tile.
2. Sort their materials by priority.
3. Start from the lowest material's fill.
4. Apply each higher material's tile operations, from the tile chosen by the pair (that material, the one below), the mask of cells at its priority or higher, and the crossing profiles.
5. Look up the palette.

`scripts/art/kit/compose.py` is the same algorithm in numpy, so Python sheets, `review:scene` and the tests see the pixels Godot draws. It is live in the editor (`@tool`): paint a cell and the edge redraws at once.

The cost is a few texel fetches per texel, and one draw call. Memory per zone is a cells texture of a few KB, plus the shared kit: about 2.4 MB of fills per 4 materials, and about 1.6 MB per transition once its atlas is decoded.

### What each tile carries (metadata)

Per material (the piece's `terrain` block, mirrored into `materials.tres` custom data, so `get_cell_tile_data(c).get_custom_data("walkable")` works):

- `material` (piece id), `material_id` (stable, stored in zones) and `priority`;
- `walkable`;
- `surface` (turf, earth, stone, paving, sand, snow, rock, water, wood);
- `route` (a route surface: benches and lamps relate to its edge);
- `water` (body still, stream, river or sea; depth; whether cells carry flow).

Per cell, beyond the material:

- the **tier** (height level, a second channel of the cells texture);
- the **flow** direction on water cells (a third channel).

Both are painted on their own layers (`Tiers`, `Flow`).

### Tiers, faces, stairs (stage 2)

Raised ground is a `Tiers` TileMapLayer of tier numbers per cell (ground-rules 1: whole cells, one height per tier). Faces are drawn from that layer:

- **The rim's dual-grid mask** gives the lip, the outer and inner corners and the side bands (`softgrid.ledge`'s lip, rim line, under-lip, side band). These are tiles on the dual grid, like transitions.
- **The face below the rim** is a strip as tall as the tier difference:
  - 12 world px (36 texels) for the low earth ledge;
  - 16 for the high ledge;
  - 32 and up for a rock cliff.

  It is painted once per height class as a periodic strip (clods or boulders, the dark foot) and laid by world x, as fills are. Its top follows the rim tile's lumps, which are canonical at tile borders as above. The shader finds a texel's face by looking up the column for a rim within the face height.
- **Stairs** are pieces, not tiles (`softground.log_steps`): a flight is a prop-like piece with a footprint, placed in a straight run of rim. Its rule ("head flush with the rim, foot on the lower ground") is checked by `logic.tiers`.

### Water (stage 2)

Water materials (still, stream, river, sea) are terrain with a `water` block:

- Their fill is the deep middle.
- Their banks are transitions of the "bank" class: turf over water gives the earth bank under the north lip, the light waterline, the depth band and lit shallows (`softground.water`, split into a fill and edge operations).
- Flow is per cell. The shader moves the ripple texture along the flow over time, holds it under reduced motion, and stops it off screen.
- Breakers (reeds, rushes, stones in the shallows, lilies) are decals, placed freely.
- Falls are pieces placed on a tier edge (`rules.water_fall`: lip flush with the rim, centred on the channel, as wide as the channel, landing in a pool).

## The kit: pieces

Every placeable thing is a **piece**, one JSON file in `game/kit/pieces/<kind>/`. The kinds are terrain, transition, tier, water, structure, prop, decal, effect, spawn and trigger. Terrain pieces are built into the kit's textures.

Props and structures (stage 3) are built into a scene each, `game/kit/props/<id>.tscn`. A prop scene contains:

- a `Sprite2D` at its foot anchor, y-sorted by its feet;
- its shadow (baked or sprite);
- its collision from the footprint;
- an `Interactable`, a `Door`, a `RestoreSite` or a `Conditional` from its `function`;
- its light and its looping effects from `rendering`.

The generator writes these scenes from the piece. Nobody edits them by hand.

Decals (tufts, flowers, pebbles, puddles, leaves) are pieces too, with `snap: free`. The dock scatters them with a brush (a seeded Poisson-disc, so they are reproducible), and the clutter rule (never on a route's centre, never in water) holds them.

## Piece schema

`game/kit/schema/piece.schema.json` (`napattack.piece/1`) is versioned and closed: an unknown key fails, so a typo cannot pass. `python3 -m scripts.art.kit.schema` validates every piece. CI has no `jsonschema` package, so this is a small validator for the subset the schema uses; where `jsonschema` is installed, the test checks that the two agree.

The schema has semantic rules too:

- a kind's own block must be present;
- an approved piece names who approved it and when;
- the id must match the file name.

A breaking change bumps the version (`napattack.piece/2`), and the build migrates old pieces.

| Block | What it holds |
| --- | --- |
| identity | `id`, `name`, `kind`, `biomes`, `variants` (id, weight, png), `version`, `approval` (state candidate, gated, approved, rejected or retired; who, when, against which standard, from which sheet) |
| `terrain` | `material_id`, `priority`, `fill` painter and args, `walkable`, `surface`, `route`, `water` (body, depth, flow), palette swatch |
| `transition` | `upper`, `lower` (or `*`), painter and args, `variants`, whose plan is softened, `dressing` (density, decals for south, north and side edges) |
| `geometry` | size in cells and art px, foot anchor, footprint cells (solid), overhang cells (drawn over, walkable behind), height above ground, z-sort rule, collision shape, interaction points (with verb and radius), door cells |
| `placement` | role (the ground-rules role), allowed and denied ground, tiers, `requires` and `forbids` relations (adjacent, within, on, facing, near, under, at_edge, at_corner, on_anchor, not_on, not_near, not_overlap, each with what, cells and facing), clearance, orientations, snap (cell, half, free), min and max per zone, stage tags (broken, restored, night, season:x, raid), composition role (centre, edge, corner, axis, row, cluster, free) |
| `rendering` | lit picture, shadow picture, cast shadow (shape, direction, length), contact AO, light (radius, colour, flicker, when), animation clips (loop, frames, reduced-motion fallback, on-screen only), sound cues, day/night and weather variants |
| `function` | interact (verb: enter, use, read, sit, open, talk, harvest, forge, rest, restore, look; triggers: scene, menu, quest, shop, dialogue, flag, restore with a data ref), state it saves, costs and yields as data refs, raid behaviour (destructible, defended, repairable) |
| `story` | quests, dialogue ids, owner (Hale's anvil), lore note, gating (region, act, a quest condition), restoration milestone |
| `gameplay` | blocks movement, blocks shots, cover, hazard, spawn, navigation cost |
| `audit` | source painter and args, review records (gate, result, date, sha256), size-guide class, Eastward reference shot, what it was seeded from, open todos |

Relations name things the validator can find: a material id, a surface (`route`), a tier edge (`rim`), an anchor kind (`hearth`), a role (`seat`), or a piece id. Two examples from the ground rules:

```json
"placement": {"role": "seat", "snap": "cell",
  "requires": [{"rel": "adjacent", "what": "route_edge", "cells": 2, "facing": true}],
  "forbids": [{"rel": "on", "what": "route"}, {"rel": "on", "what": "water"}]}

"placement": {"role": "fire", "requires": [{"rel": "on_anchor", "what": "hearth"}]}
```

The first is a bench beside a route, facing it. The second is a fire only on a hearth.

The validator, the dock (which shows a piece's rules and function on hover and refuses a placement that breaks them), the prop-scene generator and the walk-mask derivation all read these fields. Nothing about a piece is hard-coded elsewhere.

**Seeded entries:**

- the lawn, the path and the lawn-over-path transition (complete);
- the woodland and Crossroads props, seeded from their `kit.json` (size, foot, solid box) and plans (function, story) as `candidate`, with `audit.todo` listing what a person must still decide.

## The library gate

Matt, 13:43: a piece "adheres to the standard before you apply it everywhere". A piece moves from `candidate` to `gated` only when all of these pass:

1. **`review:asset`** on its pictures: for terrain, the fill and every tile composed over its partners; for props, the sprite.
2. **The ground rules on a test layout.** Terrain gets the kit lab (`game/kit/zones/kitlab.json`, every mask). A prop gets a lab with legal and illegal placements; the illegal ones must be refused.
3. **A 3x sheet** next to Bramble and the bench and lamp style anchors (`scripts/art/kit/sheet.py`), with the Eastward side-by-side made locally.
4. A **detail-auditor** run from another chat.

It becomes `approved` only with Matt's approval for every new material and every new prop design. A new variant of an approved piece needs the gate and a reviewer. The build marks unapproved pieces, and the dock and `kit_zone.gd` refuse to place them in any zone but a lab (stage 3; today the lab is the only kit zone).

## Zone authoring

A kit zone is a Godot scene (`zones/<zone>/<zone>.tscn`). It is either painted in the editor or written as a compact JSON plan (`game/kit/zones/<zone>.json`), and `game/tools/kit_zone.gd` turns one into the other:

```sh
$GODOT --headless --path game -s tools/kit_zone.gd -- --plan=res://kit/zones/kitlab.json   # plan -> scene
$GODOT --headless --path game -s tools/kit_zone.gd -- --export=res://zones/kitlab/kitlab.tscn   # scene -> plan
```

The scene contains:

- **Ground**: a `TerrainGround` holding the `Cells` layer;
- `Tiers` and `Flow` layers (stage 2);
- **Decals**;
- **Props**: piece instances, y-sorted;
- **Actors**, **Spawns** and **Doors**: what the hand-made zones have, so `Zones.go_to`, quests and saves work unchanged.

Regenerating touches only what changed. The kit build caches each piece by its inputs, and a zone scene stores no pixels, so changing a piece redraws it everywhere without touching any zone.

**The walk mask and collision** are derived, never hand-edited. A cell is blocked when any of these holds:

- its material is not walkable;
- it lies on a face;
- it is in a solid footprint of a piece.

The derivation writes merged collision rectangles, as `gen_zone.py` does today, plus a `walk.txt` for the review tools. It replaces the woodland's hand-edited `walk.txt`.

**The dock** (stage 3, an `EditorPlugin` in `game/addons/world_editor/`) has:

- a palette of approved materials and pieces with their swatches;
- terrain painting (brush, rectangle, route tool laying runs of 2 or 3 cells with rounded turns);
- piece placement that snaps by the piece's `snap`;
- hover cards with the piece's size, rules, function and story;
- live relation hints (the bench shows where its route edge must be);
- a refusal with the rule's message when a placement breaks a rule;
- a "validate zone" button running the full checks.

## The validator

`docs/vision/ground-rules.md` and `scripts/review/ground_rules.py` define the physical model. Their checks are `rules.water_source`, `water_end`, `water_fall`, `ground_water`, `route_grid`, `route_ends`, `route_clear`, `seating`, `rock_overlap`, `clutter` and `stage_debris`, plus `logic.tiers`, `roads_clear`, `logic.composition`, the crowns gate and `grid_snap`.

The editor applies the same rules to tile and piece metadata in two ways.

**Zone-level physics** (water sources and ends, falls, route ends, tiers) runs in Python on an adapter. The adapter reads the scene (via `kit_zone.gd --export`, which writes the cells, tiers, flow and piece instances) and builds the plan shape `ground_rules.check_plan` reads:

- routes are the cells of route surfaces, as runs;
- water is the water cells and their flow;
- objects are the piece instances with their kinds and feet.

Rules that are cell-native get exact cell versions:

- **`route_clear`**: no solid footprint on a route cell.
- **`ground_water`**: no route cell on water except under a bridge piece.
- **`water_flow`**: flow never runs to a higher tier.
- **`fall_edge`**: a fall piece stands on a rim cell.
- **`overlap`**: two solid footprints share no cell.
- **`fire_hearth`**: a fire piece stands on a hearth anchor.
- **`stage_debris`**: a debris piece carries the broken stage tag.
- **`scale`**: a sprite's size against its size-guide class.

They run in `check:godot` (a GdUnit suite over every kit zone) and in `review:scene`.

**Placement rules** (a piece's `requires` and `forbids`, clearance, ground, tiers, snap, per-zone counts) are evaluated by a small relation engine. It is written twice, in GDScript for the dock's live check and in Python for CI, and both run one shared fixture file (`game/kit/schema/relations.cases.json`: placements with the expected verdict), so they cannot drift.

## How a lane builds a zone in under an hour

1. **Plan the cells (10 minutes).** Copy a plan in `game/kit/zones/` and draw the ground in its rows: lawn, routes 2 or 3 cells wide, tiers, water. Or paint it in the editor over the region brief's crop.
2. **Expand and look (2 minutes).** Run `kit_zone.gd --plan=...`, open the scene, or `--shot` at 1080p.
3. **Place pieces (20 minutes).** In the dock: structures on their footprints, props by role (the dock refuses a bench on a path), trees on cells, decals with the brush.
4. **Validate (5 minutes).** Press "validate zone" in the dock, or run `npm run check:godot`. Fix what it lists.
5. **Wire gameplay (15 minutes).** Doors, spawns, camps and quest interactables, as today (`docs/godot.md`, "How lanes add a region").
6. **Review.** Run `npm run review:scene -- <zone>`, then the two auditors, then the PR.

No painting is needed unless a piece is missing. A missing piece goes through the library first.

## Adding a material or a prop once

**A material:**

1. Add `game/kit/pieces/terrain/<id>.json` with a new `material_id`, its priority and its fill painter. Write the painter in `scripts/art/kit/fills.py` if no existing one fits; it is periodic by the three rules above.
2. Add a `transition/<upper>_over_<lower>.json` for each partner it meets, with an edge painter in `edges.py`. One painter serves a whole class: sunken, bank, kerb, ledge.
3. Run `python3 -m scripts.art.kit.build` (only the new pieces are painted) and `python3 -m scripts.art.kit.sheet <out>`.
4. Put it through the library gate and get Matt's approval.

No editor, shader or tool code changes: the manifest carries everything.

A biome pack is a set of such pieces sharing `biomes` tags. Its colours come from the house palette's families.

**A prop:**

1. Add `pieces/prop/<id>.json` with geometry, placement, rendering, function, story and gameplay, and its picture from the existing prop painters.
2. Build its scene.
3. Run the gate.

From then on every lane places it.

## Materials the regions need (backlog)

From `docs/vision/regions/` (counts of mentions across the briefs) and the region plans. Each is one terrain piece plus its transitions. The classes (sunken, bank, kerb, ledge, shore) are shared painters.

| Material | Regions | Transitions it needs | Painter today |
| --- | --- | --- | --- |
| lawn, meadow (lush and dry variants) | valley, isles, woodland | over path, sand, water bank, ledge | `softground.lawn` |
| packed-earth path, worn ground | everywhere | under lawn, under heather | `softground.dirt` |
| cobble road, wheel-rutted road | Crossroads, Cogsworth | under lawn (frayed), kerb to paving | `softground.dirt` with ruts, `town.py` |
| paving and flags (with kerb) | Crossroads, Cogsworth, Neon Harbour, Hearthold | kerb over road, under lawn | `softground.paving` |
| forest floor (litter, dapples) | woodland, the Brackens, old forest | under lawn, under path | `softground.forest_floor` |
| sand, dunes | Sunstone, isles, Shell Bar, dune sea | under lawn, shore to sea | `softground.sand`, `shore` |
| scree and gravel | the massif, coal hills, Frostline | under rock ground | new |
| rock ground and highland stone | the massif, Sunstone | ledge faces (rock cliff) | `softground.ledge` (rock) |
| snow, ice, glacier | Frostline, the massif | over rock, bank to ice | new (snow ramp exists) |
| heather, moor | Frostline, the Brackens | over path | new |
| fen, marsh, peat, mud | the fens, the delta | bank to still water | new |
| tilled field, orchard rows, garden beds | valley, Cogsworth, isles | bed frame (kerb class) | `softground.bed` |
| ash, basalt, obsidian, lava | fire country | glowing seam edges | new (ash and lava ramps exist) |
| coal, slag, cinder | coal hills, Cogsworth | under path | new |
| salt flats | Sunstone basin | under sand | new |
| docks, boardwalk, decking | Neon Harbour, isles | over water (pier class) | `village.py` timber |
| brick, concrete, rail beds | Cogsworth, Neon Harbour | kerb class | new |
| water: still, stream, river, sea, shallows | everywhere | bank class, shore class, falls | `softground.water` |
| earth ledge and rock cliff faces, stairs | everywhere | tier pieces | `softgrid.ledge`, `log_steps` |
| regolith (moon) | Lumen | crater rims as tier pieces | new |

## The work split: Codex and Claude

Matt, 13:43: "consider how chatgpt can help here to conserve claude tokens".

**Claude** keeps what needs art judgement:

- the painters and their Eastward fidelity;
- the seams and the look of every tile and prop;
- the library gate's reviews;
- the piece data that encodes design intent (roles, relations, story);
- approving Codex's PRs.

**Codex** takes the engineering that a test can define. Each task below is self-contained, names the files it owns and ends with acceptance tests. Post them on the Codex handoff issue (#149) as W1 to W7, after C29 to C34. They touch only `game/addons/world_editor/`, `game/tools/`, `game/test/` and `scripts/art/kit/` (outside the painters, which are `fills.py` and `edges.py`).

### W1. Schema tooling and seed completeness

**Files:**

- `scripts/art/kit/schema.py`;
- `scripts/art/kit/test_kit.py`;
- `scripts/art/kit/seed_props.py` (new);
- `game/kit/pieces/prop/**`, `structure/**`.

**Task:**

- Complete the seeding of every woodland and Crossroads prop and structure from `game/zones/*/kit.json`, `game/data/plans/crossroads.json` and `game/zones/*/*.tscn`. Fill in:
  - geometry: size, foot, footprint cells from the solid box, collision;
  - function and story: from the plan's `restores`, interactables, speakers and quests;
  - gameplay.
- Leave design calls (`placement.role`, `requires`, `composition`) to Claude as `audit.todo` items.
- Add `--migrate` to the schema tool, for version bumps.

**Acceptance:**

- `python3 -m scripts.art.kit.schema` passes on all pieces.
- `python3 -m unittest scripts.art.kit.test_kit` passes, including a test that every object id in both zones' `kit.json` maps to a piece.
- Where `jsonschema` is installed, it agrees with `schema.py` on every piece and on the invalid fixtures in `game/kit/schema/invalid/`.

### W2. JSON plan round trip for the whole zone

**Files:** `game/tools/kit_zone.gd`, `game/test/test_kit_zone.gd`.

**Task:** extend the plan format to tiers (rows of digits), flow (rows of arrows), piece instances (`{"piece", "at": [cx, cy], "variant", "facing", "stage"}`), doors (cell rectangle, target zone and spawn) and spawns. The plan becomes the scene with the right nodes, and the export reads the scene back.

**Acceptance:** a GdUnit test builds `kitlab.json` and a fixture with every field. It exports each one and compares the result byte for byte with the input (sorted keys). It edits one cell in the scene and checks the export changed exactly that row.

### W3. The dock plugin

**Files:** `game/addons/world_editor/**`.

**Task:** build an `EditorPlugin` with these parts:

- a palette of approved materials and pieces from the manifest and the library, with their swatches;
- terrain painting on the selected `TerrainGround`'s `Cells` (brush 1 to 3 cells, rectangle, a route tool laying 2- or 3-cell runs with rounded turns);
- piece placement snapping by `placement.snap`, with orientation keys;
- hover cards showing size, rules, function and story from the piece;
- a refusal when the relation engine (W5) says no, with the rule's message;
- a "Validate zone" button;
- undo and redo through `EditorUndoRedoManager`.

**Acceptance:**

- A GdUnit test drives the plugin's non-UI API (`paint_cells`, `place_piece`, `validate`) on a fixture zone.
- A bench placed on a path is refused with the `rules.seating` message, and a bench beside a path facing it is accepted.
- Undo restores the cells.
- `npm run check:godot` stays clean, with no editor errors on import.

### W4. Walk mask and collision from metadata

**Files:** `game/world/terrain/walk.gd`, `game/test/test_walk.gd`.

**Task:**

- From the `Cells` custom data `walkable`, the tiers' faces and the pieces' footprint cells, compute the blocked cells.
- Build merged `CollisionShape2D` rectangles at runtime (the same merge as `gen_zone.py`).
- Write `walk.txt` (4 world px cells, the format `gen_zone.py` reads) for the review tools.

**Acceptance:**

- A test zone with a water cell, a footprint and a face blocks exactly those cells.
- The player cannot walk into them (a physics test like `test_quests`).
- The merged rectangles cover the blocked cells exactly, with no overlaps.

### W5. The relation engine, twice

**Files:**

- `game/world/terrain/relations.gd`;
- `scripts/art/kit/relations.py`;
- `game/kit/schema/relations.cases.json`;
- tests in `game/test/` and `scripts/art/kit/test_kit.py`.

**Task:** evaluate a piece's `placement` (ground allow and deny, tiers, `requires` and `forbids` relations, clearance, snap, per-zone counts) against a zone's cells and pieces, in GDScript and in Python.

**Acceptance:** both pass all cases in `relations.cases.json` (Claude writes the first 30: a bench on, beside and away from a route; a lamp at an edge and a corner; a fire on and off a hearth; overlaps; snap), with identical verdicts and messages.

### W6. Validator plumbing

**Files:**

- `scripts/review/kit_scene.py` (new);
- `game/test/test_kit_rules.gd`;
- `package.json` scripts.

**Task:**

- Build the adapter that turns an exported kit zone into the plan shape `scripts/review/ground_rules.check_plan` reads.
- Add the cell-native checks listed under "The validator".
- Run both from `review:scene` for kit zones and from a GdUnit suite in `check:godot`.

**Acceptance:** for each check, one fixture zone trips it and one passes, in `scripts/review/test_review.py`. The kit lab passes. A lab with a path under a structure fails `route_clear`.

### W7. Godot equals Python

**Files:** `game/test/test_terrain.gd`, `game/tools/kit_shot.gd`.

**Task:** render a kit zone headless to an image (a SubViewport at 1:1), then compare it with `compose.render` output written by Python into `game/test/fixtures/kit/`.

**Acceptance:** the kit lab and a fixture with three materials at one corner (once a third material exists) match pixel for pixel (ground and dressing), and a deliberately shifted profile hash fails.

### What Claude does next (stage 2 onward, in order)

1. Matt's steer on this stage, then tune the lawn-over-path tiles.
2. The tier pieces (low ledge, rock cliff, sides, stairs) and the water class (still, stream, bank, falls).
3. The woodland's props as piece scenes, with their roles and relations filled in.
4. The woodland rebuilt with the kit next to the current one, at 1080p before and after.
5. The first 30 relation cases.
6. Reviews and approvals of W1 to W7.

## Status of this stage

**What exists:**

- `scripts/art/kit/`: `fills.py`, `edges.py`, `compose.py`, `build.py`, `sheet.py`, `schema.py`.
- `game/kit/`: the schema, three pieces and the built terrain.
- `game/world/terrain/`: the shader, the kit loader and `TerrainGround`.
- `game/tools/kit_zone.gd`.
- The kit lab zone `kitlab` (`--zone=kitlab`).

**Not yet:** tiers, water, props as scenes, the dock, the validator on scenes, the woodland rebuild.

**Kept identical:** the pilot golden, the woodland, Crossroads and the Undercroft. No painter they use was changed.
