# Cliff core: one terrain system, many biomes

Status: a draft for Matt, rebuilt by Claude A's helper on 21 Oct. Nothing in the game uses it yet: no zone is wired to it. Code: `scripts/art/cliff_core.py`. Pictures: `docs/vision/cliff-core/` (written by the generator, reproduced by `npm run check:art-repro`). Only our own art is in the repository; the comparison with Eastward is built locally (`--compare`) and kept out of it.

## What Matt asked for (21 Oct)

- 09:23: "can you use only eastward as the example on how to draw edges and the soft grid". The rules are measured in [eastward-edges.md](eastward-edges.md); the earlier version of this core was tuned to Sea of Stars' crag masses and is replaced.
- 09:31, on the bake-off's tile swatch: "with a touch of polish this is pretty much what i want (besides the obvious logic error here with the stairs)", and "i don't necessarily want eastwards muted color palate. the game should have it's own color palate that is consistent (and depending on terrain)". So the look is that swatch's (rounded boulder faces, clean grass lips, a dirt ledge, warm house ramps), Eastward gives the edge geometry and the value structure, and every colour is a house ramp.
- 09:51 and 09:52: reuse the polished parts elsewhere in the same biome, to speed up terrain building.
- 10:08: "the edge of the grass biome should look different from an edge in the mountain. you can safely reuse parts in the same biome, in other biomes you have to be careful."
- 10:09: "but do make sure everything has the same sort of soft grid and the visual art style is consistent".

## Three layers

| Layer       | What it is                                                                                                                                                                                                                                            | Crosses biomes              |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Engine**  | The world height field in plan space; rims put on the soft grid and traced as contours with arc length; strata fixed in absolute height; hash noise on world coordinates (seamless); dressing placed by rule; walk masks; attach points; `Plan`'s API | yes                         |
| **Grammar** | The rules every biome draws by, checked on every biome's output (below)                                                                                                                                                                               | yes, it is the same for all |
| **Own**     | A biome's edge set (face, lip, foot, stair, bank), its rock and ground families, its dressing, and the set pieces it owns                                                                                                                             | no                          |

### The grammar (shared)

| Rule                                                                                                                                | Where it lives              | Checked by `--check` on every biome's pictures                               |
| ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ---------------------------------------------------------------------------- |
| The 8 px soft grid: rims run along 16 px of a rim and step in 8 px cells, corners rounded to radius 3 (eastward-edges 1.1 to 1.5)   | `World._snap`               | rim steps: every turn of a rim adds up to whole cells, ±1 px                 |
| Tier heights 12, 16, 32, 40 only (world-rules 3.2)                                                                                  | each biome's `face`         | tier                                                                         |
| The rim's 1 px wobble in runs of 1 to 10; lips hang 0 to 2 px; no teeth (eastward-edges 1.4, 3.1)                                   | `lip_overhang`              | lip                                                                          |
| Light from the upper left; lit lip row; rim line and darkest line under it; a shade of 1 to 3 rows; the dark foot band (2.2 to 3.2) | `paint_rims`, `paint_faces` | west minus east on every rock form; foot                                     |
| Side bands of 3 px with a broken ink line (3.3)                                                                                     | `paint_sides`               | side                                                                         |
| Outlines only where height changes (4); frayed path edges, no line, no dither (5.1, 5.4)                                            | `paint_rims`, `fray_path`   | dither in the lint                                                           |
| Shadows: the foot band under a face, east-facing sides throw east, two tones then one (7)                                           | `paint_shadows`             | by eye                                                                       |
| The house palette and its ramp rule, family edge tones, clusters of 2 or more, lone pixels at most 6 % (house-style 1 to 4)         | `LUT`, `despeckle`          | palette, lone px, dither (the lint)                                          |
| Eastward's detail per 16 px patch (house-style 7, ramp ruling 85 %)                                                                 | every painter               | the detail bar: rock (stone-wall and face, or rim for a low bank) and ground |

### The biomes (own)

| Biome      | Its own edge and face set                                                                                                                                                                                       | Its pieces                                                          | May borrow, and from where                                    |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------- |
| `highland` | Rounded `crag` boulders packed with small stones, a clean turf lip (0 or 1 px), a stony foot with scree, steps cut from the rock between boulder cheeks, brooks in a 2 px earth bank, 32 px tiers               | stair, ledge, path, spring, pond, snow corner, boulders, scree, ivy | the engine and the neutral parts only                         |
| `meadow`   | A low earthy turf bank (16): soil in thin layers with lit clods and the odd field stone, pale roots under a soft sod overhang (1 or 2 px), grass thick over its foot, timber steps with posts, banks with reeds | stair, path, pond, boulders (field stones, in `stone`), spring      | the engine and the neutral parts only                         |
| `coast`    | Pale bedded sandstone slabs on a dark basalt foot under a thin turf lip; 32 px                                                                                                                                  | stair, ledge, boulders, path, scree                                 | the engine and the neutral parts; its loose stones are basalt |
| `canyon`   | Red and buff slabs, a crumbling dry lip, a gritty foot; 40 px                                                                                                                                                   | stair, ledge, boulders, path, scree                                 | the engine and the neutral parts; its loose stones are clay   |
| `city`     | Dressed courses under a coping; 40 px                                                                                                                                                                           | stair, ledge, path                                                  | the engine and the neutral parts                              |

The neutral parts (`NEUTRAL`): the figure for scale, falls and plunge pools as water (their banks are the biome's), cast shadows, despeckle, and the hand-drawn stamp shapes (tufts, pebbles, ferns), always drawn in the target biome's own families. A loose boulder or pebble is always drawn in the biome's own `loose` rock. Highland and meadow are built in full; coast, canyon and city have their own edge sets but no polish pass yet. Alpine, moor, dry steppe and ash are not built: each needs its own edge set first, never a recolour of another.

`--check` fails if a biome draws with an edge set that belongs to another biome, if two edge sets are the same shapes in another colour, if a biome allows a piece the engine does not have, or if a demo places a piece its biome does not own (`Plan` refuses one as it is placed).

## The rules in the code (eastward-edges.md)

- **Soft grid.** `World._snap` takes each tier's outline cell by cell (16 px along, 8 across, by majority), so a rim runs straight for two cells or more and a diagonal is a staircase of whole cells (Eastward's cliffs are stacks of rectangles, 1.3); `terrace.rounded` rounds outer corners to radius 3 and inner ones to 2 (1.5). Tiers stay nested.
- **Faces.** `lump_field` is a staggered lattice of lumps in world coordinates (x, absolute height), each with its own centre and radii by hash, the lowest in front; small stones fill the gaps. A lump is shaded as a dome from the upper left with hard steps, cut into facets about 3.5 px across, with a crevice on its top edge, an underside on its lower right, sibling clusters, flecks, lichen on the lit crowns and damp stains under. The meadow's `paint_earth` is soil layers in absolute height, clods, field stones and roots. Marks run round or across, never in vertical stripes (2.4).
- **Lips, under-lips, streaks, feet** (`paint_rims`). On the top: the edge row a step darker, a broken lit row two rows behind. Over the face: the lip 0 or 1 px (turf), 1 or 2 (sod, with a dark underside), 1 or 2 (snow cornice), 3 (coping). Under it: the rim line (tone 1) and the darkest line (0), then a shade stepping back (two rows on a 32 face, three on 64), then a zone of short horizontal dashes; at the bottom the foot band (2 or 3 rows dark) with the odd pebble. The ground's first row under a face is a tone down.
- **Sides** (`paint_sides`): 3 px, two of rock (lit facing west, dark facing east), then the broken ink line, and the top's darker lip row beside it.
- **Paths** (`fray_path`): the grass reaches 0 to 2 px over a path's edge in 1 px steps, dark crumbs lie along it, a tuft leans over or the path bites into the grass about every 16 px. No line.
- **Water** (`paint_water`, `_fall`, `_pool`): a pond or brook lies under a small north bank (2 rows of earth under a darker lip row), its top row a broken light waterline, then a dark band (one row on a brook, two to four on a pond) stepping back to the body. Only a lake or the sea (wider than three adults) gets depth bands and a foam line. A fall is as wide as its drop (`fall_width`), narrower at the lip and spreading, swelling and pinching on the way down; its plunge pool is a rounded rectangle with a light waterline under the foot, a dark band, small ripples and foam, a damp bank and stones.
- **Stairs** (`Stair`, `Plan.stair`): cut back into the upper tier as far as they rise (6.1), steps of 3 rows with risers of about 3 px, the top step flush with the upper floor (an 8 row landing behind it), the bottom step on the lower ground where its path starts (a landing in front), the face running on unbroken for 5 px either side. Highland steps are slabs of the rock (11 to 18 px stones) between boulder cheeks; meadow steps are timber planks on posts.
- **Snow**: a calm plane in broad drifts with lit crests and a broken cool row in the lee of thick drifts only (no contour lines); where it ends on the same ground, a thin layer with a lit lip and a two-row shaded face.

## Set pieces: the API

A `Plan` is a region being built. Coordinates are screen px of the ground a piece stands on, with the tier `z` it stands on. Every piece returns a `Placed` record: `box` (its footprint, on the 8 px grid), `attach` (named screen points where paths, streams and ledges join it), `z` and `variant`. `walk_mask(render(world))` gives what can be walked; crop it to a piece's box for the piece's own walk mask. Each piece adapts to the face height and the outline where it lands, and takes its variant (boulder order, plants, lip runs, brook bends) from a hash of where it stands, so two copies never match; nothing is mirrored, so the light stays upper left.

```python
import cliff_core as cc
plan = cc.Plan(512, 512, 'highland', seed=4)
plan.tier(64, [(-20, 196), (200, 188), (540, 206)])     # a tier: raise ground north of a rim (screen curve)
plan.mound(32, 40, 300, 120, 360)                       # or a raised block whose top covers a screen box

st = plan.stair(208, 64, width=40)                      # a stair through the face below tier 64 near x 208
plan.path([st.attach['foot'], (226, 330), (220, 520)], z=0)          # a footpath (a bend: give it a bend)
led = plan.ledge(168, 330, 64, depth=40)                # a ledge path cut along that face, at z 32
plan.spring(120, 120, 64)                               # a spring on tier 64: brook, falls, plunge pools
plan.pond(360, 380, 440, 424)                           # a hollow with a pool (screen box)
plan.snow_corner(420, -12, 524, 50, 96)                 # snow on a corner of tier 96
plan.boulders(40, 470, 'l')                             # a boulder cluster: 's', 'm' or 'l'
plan.scree(330, 500, 64)                                # a scree foot under tier 64's face, x 330 to 500
plan.ivy(60, 64, 18)                                    # a lip with ivy, 18 px wide, at x 60
world = plan.world()                                    # -> render(world), walk_tiers(world), world.placed
```

| Piece         | Footprint and attach points                       | Adapts to                                                                                     | Varies by hash                                 |
| ------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `stair`       | notch plus landings; `foot`, `head`               | any face height (steps of about 3), any width (multiples of 8, 24 or more), the biome's steps | stone lengths and joints, nosing chips, cheeks |
| `ledge`       | the shelf; `west`, `east`                         | the face's rim along its length, any depth                                                    | lumps of its faces, path patches               |
| `path`        | its swept band; `start`, `end`                    | the tier it lies on (clipped to it)                                                           | fray, crumbs, tufts and bites                  |
| `spring`      | source pool to the last fall; `source`, `outflow` | every rim the brook crosses (a fall each, sized by its drop), the lowest tier (the pool)      | brook bends and width, stones, ferns           |
| `pond`        | its box; `inlet`, `outlet`                        | the ground it lies on                                                                         | stones, plants                                 |
| `snow_corner` | its box                                           | the tier's outline (cornices where it reaches a rim)                                          | the scalloped margin, drifts, rocks            |
| `boulders`    | its box (blocks walking)                          | the biome's loose rock, moss if green                                                         | count, sizes, order                            |
| `scree`       | the band under the face                           | the face's foot along its length                                                              | stones and their sizes                         |
| `ivy`         | the mat under the lip                             | the face's height                                                                             | width, length, leaves, strands                 |

## How a lane builds a region from it

1. Make a `Plan` in the region's biome (`'highland'`, `'meadow'`, ...). Never borrow another biome's table: make the biome first.
2. Draw the tiers: `tier()` for rims as screen curves, `mound()` for blocks. The outline is put on the soft grid when the first piece needs it.
3. Place the pieces where the story needs them: stairs where paths meet faces, the paths between their attach points, a spring where water should come from, ponds, snow, boulders and scree at the feet, ivy over a few lips.
4. `world = plan.world()`; `render(world)` (or a window of it: `render(world, box)`, seamless with its neighbours); `walk_tiers(world)` for the zone's walk map.
5. Run `--check` on it (the grammar and the bar), look at it at 3x and at game scale beside the Eastward comparison, and give the asset ledger its outputs.

`demo_area()` is a 512 x 512 highland area built this way in about twenty lines (`area.png`, `area-3x.png`); it renders in about 5 s.

## Pictures

| File                                      | What it shows                                                                          |
| ----------------------------------------- | -------------------------------------------------------------------------------------- |
| `highland.png`, `-3x`                     | The polished swatch, from the pieces only                                              |
| `meadow.png`, `-3x`                       | The second biome, with its own edge set and pieces                                     |
| `edges.png`                               | Highland and meadow side by side on the same outline at 3x: one grammar, two edge sets |
| `area.png`, `-3x`                         | A 512 x 512 highland area built from the kit and the pieces                            |
| `modules.png`                             | Every highland piece alone at 2x with its footprint, attach points and walk mask       |
| `reuse.png`                               | The same five highland pieces in three spots of three outlines                         |
| `coast`, `canyon`, `city` (`.png`, `-3x`) | Their own edge sets, not polished yet                                                  |
| `proof-1` to `proof-3` (`.png`, `-3x`)    | Random highland outlines (nothing hand-placed), for the check                          |

## Checks and numbers (21 Oct)

`python3 scripts/art/cliff_core.py --check`: the seam test (a 512 px world against its four 256 px tiles: 0 px apart), biome ownership, and the grammar on the three random outlines and all five demos. All PASS.

| Picture          | Rock: tones, shapes, dressing, isolated, cluster (kind)                                                         | Ground                        | Grammar (lint, light, rim, lip, foot)                |
| ---------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------------- |
| Random outline 1 | 21.8, 41.7, 35.7, 0.102, 3.59 (stone-wall and face)                                                             | 11.8, 29.6, 24.5              | 100 % palette, 1.3 % lone, 0 dither, +5.2, rim 54/55 |
| Random outline 2 | 20.3, 40.7, 35.3, 0.110, 3.48                                                                                   | 10.8, 32.8, 28.3 (85 % tones) | 100 %, 1.3 %, 0, +4.9, 48/51                         |
| Random outline 3 | 20.7, 43.0, 37.3, 0.115, 3.34                                                                                   | 11.5, 31.5, 26.4              | 100 %, 1.3 %, 0, +4.6, 31/31                         |
| Highland demo    | 15.8, 38.2, 32.5, 0.100, 3.99 (85 % tones)                                                                      | 11.5, 31.5, 26.4              | 121 colours, 100 %, 1.1 %, 0, +5.2, 11/12            |
| Meadow demo      | 20.3, 38.7, 35.0, 0.073, 4.31 (rim: a 16 px bank is judged with its lip and foot, as Eastward's farm ledge)     | 11.9, 30.0, 24.9              | 119 colours, 100 %, 0.8 %, 0, +0.9, 11/12            |
| Reference        | stone-wall 18.6, 28.2, 22.4, 0.173, 3.63; face 18.2, 36.8, 30.2, 0.205, 2.51; rim 19.5, 35.0, 31.0, 0.217, 2.57 | 12.6, 31.9, 24.1              |                                                      |

Coast, canyon and city pass too (canyon rock 24.2 tones; city wall 17.7 tones, 36.8 shapes). The margins are thin where marked: the highland demo's rock box (the top of the east face, under its lip shade) and one ground box pass on the house's 85 % ruling for ramp-built art, not on the code's 90 %. A rim turn that adds up to whole cells within 1 px passes; a handful per picture do not (where two faces of one loop overlap on screen), and the check allows up to 5 %.

**Compared by eye** at 3x, everything at an adult of 25 px, with Eastward only: its rock cliff with a grass top (Octopia, store shot 12), its grass ledges, stair and canal bank (13) and its pond (Octopia-7). The comparison is built with `--compare REFDIR OUT.png` from local copies of the official screenshots and is not committed.

## Honest weaknesses

- **Boulders are larger than Eastward's** (8 to 18 px against its 6 to 8 at our scale), on purpose: the house look Matt chose. The face kind of the bar is met by many facets and skin clusters inside them.
- **The grass is only a little calmer.** The ground bar needs Eastward's two-tone mottle, so the blades are mostly sibling swaps at the same tone; fewer of them fails the bar. Matt may still find the lawn busy at 3x.
- **Long thin side lines.** Where a tier ends west or east in a straight north-south edge (the summit's west end), the 3 px side band reads as a single dark line running up the screen.
- **Ponds and plunge pools** are rounded rectangles, calmer than before, but small pools look boxy, and a pond's stone rim is sparse.
- **Meadow light test is weak** (+0.9): the soil's clods are small, so west and east of each barely differ. Its reeds are few.
- **Coast, canyon and city** have their own edge sets but no polish pass, and alpine, moor, dry steppe and ash are not built (each needs its own edge set first).
- **Corners** are rounded by construction (radius 3) and checked only through the rim-step rule, not measured as radii.
- **Not wired in.** No zone uses the core; the world canvas, the asset ledger and the walk map have not seen it. Not checked under the night tint, on a phone, or in the game. Falls are not animated.
- **New palette family.** `crag` is a new accent (`accent:highland`), awaiting Matt.

## Next

1. Matt looks at `highland-3x.png`, `edges.png` and `area-3x.png` (and the local Eastward comparison) and says whether this is the highland and whether the meadow reads as its own biome.
2. If yes: the mountain kit (PR #148) is rebuilt on the core; the valley's banks take the meadow set; then the coast and canyon sets get their polish, and new biomes get their own edge sets.
3. A zone adopts it through `Plan` and `walk_tiers()`; the asset ledger grades its outputs when a zone ships them.
