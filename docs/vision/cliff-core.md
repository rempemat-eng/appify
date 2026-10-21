# Cliff core: one terrain system, many biomes

Status: a draft for Matt, rebuilt by Claude A's helper on 21 Oct, now at any density from 1 to 3 art texels a world px (the 2x pilot). Nothing in the game uses it yet: no zone is wired to it. Code: `scripts/art/cliff_core.py`. Pictures: `docs/vision/cliff-core/` (written by the generator, reproduced by `npm run check:art-repro`). Only our own art is in the repository; the comparison with Eastward is built locally (`--compare`) and kept out of it.

## What Matt asked for (21 Oct)

- 09:23: "can you use only eastward as the example on how to draw edges and the soft grid". The rules are measured in [eastward-edges.md](eastward-edges.md); the earlier version of this core was tuned to Sea of Stars' crag masses and is replaced.
- 09:31, on the bake-off's tile swatch: "with a touch of polish this is pretty much what i want (besides the obvious logic error here with the stairs)", and "i don't necessarily want eastwards muted color palate. the game should have it's own color palate that is consistent (and depending on terrain)". So the look is that swatch's (rounded boulder faces, clean grass lips, a dirt ledge, warm house ramps), Eastward gives the edge geometry and the value structure, and every colour is a house ramp.
- 09:51 and 09:52: reuse the polished parts elsewhere in the same biome, to speed up terrain building.
- 10:08: "the edge of the grass biome should look different from an edge in the mountain. you can safely reuse parts in the same biome, in other biomes you have to be careful."
- 10:09: "but do make sure everything has the same sort of soft grid and the visual art style is consistent".
- 10:52: "your current renders are visually too noisy. compare with eastward. i want it to be cleaner, like eastward". Ground is judged for cleanliness (eastward-edges.md 5.5).
- 10:55 and 11:05: "i really want you to use eastwards soft grids, cleanliness, the way they create atmosphere using props and their pixel density. but develop your own general style"; "1.5x is the minimum i'd want i think. ideally around eastward if you can do it properly". The core renders at any density (below); the pilot is 2x.
- 11:44, on the first pilot cliff: "i like the rocks on the cliff face here. but remember the grid shape like in eastward". Every outline is on the grid (eastward-edges.md 1.6), and the faces are packed cobbles.

## Three layers

| Layer       | What it is                                                                                                                                                                                                                                            | Crosses biomes              |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Engine**  | The world height field in plan space; rims put on the soft grid and traced as contours with arc length; strata fixed in absolute height; hash noise on world coordinates (seamless); dressing placed by rule; walk masks; attach points; `Plan`'s API | yes                         |
| **Grammar** | The rules every biome draws by, checked on every biome's output (below)                                                                                                                                                                               | yes, it is the same for all |
| **Own**     | A biome's edge set (face, lip, foot, stair, bank), its rock and ground families, its dressing, and the set pieces it owns                                                                                                                             | no                          |

### The grammar (shared)

| Rule                                                                                                                                                                                                          | Where it lives                         | Checked by `--check` on every biome's pictures                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The 8 px soft grid: outlines by cell majority, no run under 3 cells, straight runs, turns at cell lines, vertical sides, corners rounded half a cell outside and a quarter inside (eastward-edges 1.1 to 1.6) | `grid_mask`, `World._snap`, `_densify` | at least 70 % of every render's rim columns on a cell line (`RIM_ON_GRID`)                                                                                                                                  |
| Tier heights 12, 16, 32, 40 only (world-rules 3.2)                                                                                                                                                            | each biome's `face`                    | tier                                                                                                                                                                                                        |
| The rim's 1 px wobble; a turf lip hangs 0 or 1 texel at any density in long runs; no teeth (eastward-edges 1.4, 3.1)                                                                                          | `lip_overhang`                         | lip                                                                                                                                                                                                         |
| Light from the upper left; lit lip row; rim line and darkest line under it; a shade of 1 to 3 rows; the dark foot band (2.2 to 3.2)                                                                           | `paint_rims`, `paint_faces`            | west minus east on every rock form; foot                                                                                                                                                                    |
| Side bands of 3 px with a broken ink line (3.3)                                                                                                                                                               | `paint_sides`                          | side                                                                                                                                                                                                        |
| Outlines only where height changes (4); frayed path edges, no line, no dither (5.1, 5.4)                                                                                                                      | `paint_rims`, `fray_path`              | dither in the lint                                                                                                                                                                                          |
| Shadows: the foot band under a face, east-facing sides throw east, two tones then one (7)                                                                                                                     | `paint_shadows`                        | by eye                                                                                                                                                                                                      |
| The house palette and its ramp rule, family edge tones, clusters of 2 or more, lone pixels at most 6 % (house-style 1 to 4)                                                                                   | `LUT`, `despeckle`                     | palette, lone px, dither (the lint)                                                                                                                                                                         |
| Clean like Eastward (5.5): ground as clean as its lawns and not flat; rock calm, its tones at least half the reference's                                                                                      | every painter                          | the detail bar through the reference's own pipe at the render's adult (25 x density): ground cleanliness plus 4 colours in the box; rock tones at 50 % (isolated and cluster gate at 1x, reported above it) |

### The biomes (own)

| Biome      | Its own edge and face set                                                                                                                                                                                                                                                                                  | Its pieces                                                          | May borrow, and from where                                    |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------- |
| `highland` | Packed cobbles in world units (4 to 7 world px, the odd boulder of 9 to 11), warm ochre only on each cobble's top-left, `crag_cool` body, violet-grey `stone` shade and seams; a clean turf lip (0 or 1 px), a stony foot with scree, broad stone steps in a spur, a rill in a damp-earth bed, 32 px tiers | stair, ledge, path, spring, pond, snow corner, boulders, scree, ivy | the engine and the neutral parts only                         |
| `meadow`   | A low earthy turf bank (16): soil in thin layers with lit clods and the odd field stone, pale roots under a soft sod overhang (1 or 2 px), grass thick over its foot, timber steps with posts, banks with reeds                                                                                            | stair, path, pond, boulders (field stones, in `stone`), spring      | the engine and the neutral parts only                         |
| `coast`    | Pale bedded sandstone slabs on a dark basalt foot under a thin turf lip; 32 px                                                                                                                                                                                                                             | stair, ledge, boulders, path, scree                                 | the engine and the neutral parts; its loose stones are basalt |
| `canyon`   | Red and buff slabs, a crumbling dry lip, a gritty foot; 40 px                                                                                                                                                                                                                                              | stair, ledge, boulders, path, scree                                 | the engine and the neutral parts; its loose stones are clay   |
| `city`     | Dressed courses under a coping; 40 px                                                                                                                                                                                                                                                                      | stair, ledge, path                                                  | the engine and the neutral parts                              |

The neutral parts (`NEUTRAL`): the figure for scale, falls and plunge pools as water (their banks are the biome's), cast shadows, despeckle, and the hand-drawn stamp shapes (tufts, pebbles, ferns), always drawn in the target biome's own families. A loose boulder or pebble is always drawn in the biome's own `loose` rock. Highland and meadow are built in full; coast, canyon and city have their own edge sets but no polish pass yet. Alpine, moor, dry steppe and ash are not built: each needs its own edge set first, never a recolour of another.

`--check` fails if a biome draws with an edge set that belongs to another biome, if two edge sets are the same shapes in another colour, if a biome allows a piece the engine does not have, or if a demo places a piece its biome does not own (`Plan` refuses one as it is placed).

## The rules in the code (eastward-edges.md)

- **Soft grid** (eastward-edges 1.6). `grid_mask` takes a plan mask cell by cell (8 px cells, by majority), merges runs shorter than three cells (no one- or two-cell tabs or notches), and rounds outer corners to radius 4 (half a cell) and inner ones to 2. `World._snap` applies it to every tier, nested; `Plan.snow_corner` to the snow block; the plunge pool and the spring's pool are grid rectangles with rounded corners; a brook runs straight through each cell and jogs at a cell line. `_densify` re-rounds at texel scale (4 and 2 world px).
- **Faces.** `lump_field` is a staggered lattice of lumps in world coordinates (x, absolute height), each with its own centre and radii by hash, the lowest in front. The highland's `paint_cobbles` (Matt, 11:44) sizes them in world px (`world_lumps`; never under about 8 texels across), flat or tall by ±30 %, about one in eleven a boulder 1.9 times as large, and shades each as a calm dome in three steps: warm `crag_warm` only on the top-left, `crag_cool` or `crag` body, violet-grey `stone` shade a value below, and a dark seam only where it meets the cobble above (no outline round every stone). Coast and canyon keep `paint_faces` (slabs with facets); the meadow's `paint_earth` is soil layers in absolute height, clods, field stones and roots, its marks one world px wide at any density. Marks run round or across, never in vertical stripes (2.4).
- **Lips, under-lips, streaks, feet** (`paint_rims`). On the top: the edge row a step darker, a broken lit row two rows behind. Over the face: the lip 0 or 1 px (turf), 1 or 2 (sod, with a dark underside), 1 or 2 (snow cornice), 3 (coping). Under it: the rim line (tone 1) and the darkest line (0), then a shade stepping back (two rows on a 32 face, three on 64), then a zone of short horizontal dashes; at the bottom the foot band (2 or 3 rows dark) with the odd pebble. The ground's first row under a face is a tone down.
- **Sides** (`paint_sides`): 3 px, two of rock (lit facing west, dark facing east), then the broken ink line, and the top's darker lip row beside it.
- **Paths** (`fray_path`): the grass reaches 0 to 2 px over a path's edge in 1 px steps, dark crumbs lie along it, a tuft leans over or the path bites into the grass about every 16 px. No line.
- **Water** (`paint_water`, `_fall`, `_pool`): a pond or brook lies under a small north bank (2 rows of earth under a darker lip row), its top row a broken light waterline, then a dark band stepping back to the body. A rill (narrower than about 8 world px) has a light ribbon along its west side, its east side in shade, riffles across the flow, and a bed of damp earth with pebbles either side. Only a lake or the sea gets depth bands and a foam line. A fall leaves the top between two lip stones, widens as it drops, carries light and dark ribbons down the sheet and breaks white where it lands; its plunge pool is a grid rectangle with rounded corners, a light waterline under the foot, a dark band, ripples and foam, a damp bank and stones on its outline.
- **Stairs** (`Stair`, `Plan.stair`; eastward-edges 6.1 as ruled on 21 Oct): the flight stands in front of the face, cut into a spur, and climbs only the face: its head is flush with the rim and the upper floor runs on flat behind it, a few broad steps of 5.5 world px (11 art px at 2x) and 5 rows each step down to the foot, which lands on the path. Rock cheeks at the upper floor's height, 8 px wide, stand either side and end a tread short of the foot, so their fronts carry the face down beside the steps. Highland steps are broad slabs (one or two to a step) with worn nosings and a worn centre; meadow steps are timber planks on posts.
- **Snow**: a drift block on the grid with rounded corners, a calm plane in broad drifts with lit crests; at its margin it thins and the grass breaks in; its south edge is a cool band 2 to 3 texels deep over a soft shadow on the ground; rocks poke through it.
- **Ground** (`_lawn`, eastward-edges 5.5): one field tone, broad soft patches of the cool sibling at the same value, a few large patches a tone darker, light pools a tone up that are rare, large and never within 16 world px of a face; the detail is the clumped tufts and flowers placed by rule.
- **Ivy** (`_vines`): a short ragged cushion under the lip and strands of different lengths, longest near the middle, each a thin swaying stem with leaf pairs lit on their upper left and a soft shadow on the rock.

## Density: drawing at 1 to 3 texels a world px

Matt asked for a finer pixel density (10:55, 11:05). `Plan.world(density)` and every demo take `density`, any value from 1 to 3 (the pilot uses 2: DENSITY.md's verdict in the pilot workspace is exactly 2x, an adult of 50 px). The world stays in world px: the height field, the contours, the plan, the attach points and the walk masks are planned in world units, and only the raster scales. `World._densify` upsamples the field and masks, scales the stairs and the pieces' dressing, and rounds every tier's outline again at texel scale, so a rim still steps one texel at a time and its corners are pixel circles at the finer size. Edge measures are not doubled: `measures(s, E)` converts each from Eastward's native px at k = 25 x s / 54 (0.46 at 1x, 0.93 at 2x), so at 2x Eastward's own widths apply almost one to one. Painters size their marks in world px (cobbles, ivy, the rill, snow, the pool, the earth bank's stones and roots); the hand-drawn stamps (tufts, pebbles, flowers) stay texel-sized, so at 2x they are finer.

`python3 scripts/art/cliff_core.py --pilot OUT_DIR 2 1.5` writes the pilot cliff (`demo_pilot`, Matt's tile-swatch pick on one 300 x 180 world px screen) at each density: the picture, its height mask and walk mask as PNG and run-length JSON, and the attach points of every piece. The pilot's files live in the pilot workspace, not in the repository.

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

| Piece         | Footprint and attach points                       | Adapts to                                                                                       | Varies by hash                         |
| ------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------- |
| `stair`       | the flight and its spur; `foot`, `head`           | any face height (steps of about 5.5), any width (multiples of 8, 24 or more), the biome's steps | slab joints, worn nosings, foot stones |
| `ledge`       | the shelf; `west`, `east`                         | the face's rim along its length, any depth                                                      | lumps of its faces, path patches       |
| `path`        | its swept band; `start`, `end`                    | the tier it lies on (clipped to it)                                                             | fray, crumbs, tufts and bites          |
| `spring`      | source pool to the last fall; `source`, `outflow` | every rim the brook crosses (a fall each, sized by its drop), the lowest tier (the pool)        | brook bends and width, stones, ferns   |
| `pond`        | its box; `inlet`, `outlet`                        | the ground it lies on                                                                           | stones, plants                         |
| `snow_corner` | its box                                           | the tier's outline (cornices where it reaches a rim)                                            | the scalloped margin, drifts, rocks    |
| `boulders`    | its box (blocks walking)                          | the biome's loose rock, moss if green                                                           | count, sizes, order                    |
| `scree`       | the band under the face                           | the face's foot along its length                                                                | stones and their sizes                 |
| `ivy`         | the cushion and strands under the lip             | the face's height                                                                               | strand lengths, sway, leaf pairs       |

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

## Checks and numbers (21 Oct, after the pilot)

`python3 scripts/art/cliff_core.py --check` runs at densities 1, 1.5 and 2 (`--density d` for one). At each density it runs the seam test (a 512 px world against its four 256 px tiles: 0 px apart) and the grammar. At 1x the grammar covers the three random outlines and all five demos. At 1.5x and 2x it covers the highland and meadow demos and one random outline. Biome ownership is checked once. Everything passes.

| Picture              | Rock: tones, isolated, cluster (kind)               | Ground: edges, lone, top2, colours, variety | Light, rim columns on the grid |
| -------------------- | --------------------------------------------------- | ------------------------------------------- | ------------------------------ |
| Random outline 1, 1x | 15.2, 0.126, 4.13 (stone-wall)                      | 0.086, 0.000, 0.94, 4.8, 8                  | +7.0, 94 %                     |
| Highland demo, 1x    | 12.3, 0.103, 4.71                                   | 0.090, 0.000, 0.93, 3.8, 6                  | +7.3, 93 %                     |
| Meadow demo, 1x      | 16.0, 0.045, 7.14 (rim)                             | 0.054, 0.000, 0.97, 3.1, 8                  | +2.3, 91 %                     |
| Highland demo, 1.5x  | 12.7, 0.176, 2.99                                   | 0.075, 0.015, 0.95, 7.8, 8                  | +7.6, 88 %                     |
| Highland demo, 2x    | 15.0, 0.270, 2.12                                   | 0.035, 0.005, 0.97, 5.9, 8                  | +7.9, 91 %                     |
| Meadow demo, 2x      | 15.3, 0.125, 4.93 (rim)                             | 0.049, 0.008, 0.96, 5.3, 4                  | +0.6, 90 %                     |
| Reference (Eastward) | stone-wall 18.6, 0.173, 3.63; rim 19.5, 0.217, 2.57 | 0.148, 0.014, 0.68, 10.4                    |                                |

How a picture is judged:

- **Rock** passes on tones of at least 50 % of the reference (`ROCK_TONES`). Calm planes and cobbles fail the shape and dressing minimums, which reward noise, so those two are reported only. Isolated and cluster gate at 1x. At 1.5x and 2x they are reported, because the stone-wall references are Eastward's larger boulders and Matt's smaller cobbles break up under the bar's 2:1 mode downsample. At every density the lint gates lone pixels at the native size (at most 6 %; the pictures have 0.1 to 0.4 %).
- **Ground** passes on detail_bar's cleanliness tests: edges, lone pixels, the share of the two main colours, and the colour count. It must also show at least four colours of 0.5 % / density in its box (`GROUND_VARIETY`). The per-16 px tones minimum is reported only, because a calm lawn has 3 to 5 tones in a 16 px square.
- **Density:** at a density over 1, a crop goes through the reference's own pipe from its true adult height (25 x density): nearest upscale to the reference's adult, its JPEG quality, then the most common colour in each block.
- **Grid:** at least 70 % of every render's rim columns lie on a cell line (`RIM_ON_GRID`).

**Compared by eye** at 2x zoom with Eastward only, at the same character height: the rock cliff with a grass top (Octopia, store shot 12), its grass ledges, stair and canal bank (13), and the two cliff crops Matt sent on 21 Oct. The comparison is built locally and not committed.

## Honest weaknesses

- **The bar and the direction disagree in places.** Matt's direction is calm ground, small packed cobbles and grid outlines. The detail bar's per-patch tones and its shape and dressing minimums reward noise, so the cliff core reports them instead of gating on them (above). This is a ruling for Matt and Claude A to confirm, not a measurement. The stone-wall baselines should gain Eastward crops with cobbles like the ones Matt sent, so that isolated and cluster can gate at 2x again.
- **Stamps stay texel-sized.** Tufts, pebbles and flowers are the same stamps at every density, so at 2x they are half their 1x size in the world.
- **Ledge ends.** Where a ledge's west end meets the full-height face, a short side band shows.
- **Meadow light test is weak** (+0.6 to +2.3): the soil's clods are small, so their west and east halves barely differ.
- **Coast, canyon and city** have their own edge sets but no polish pass. Alpine, moor, dry steppe and ash are not built; each needs its own edge set first.
- **Not wired in.** No zone uses the core. The world canvas, the asset ledger and the walk map have not seen it. It has not been checked under the night tint, on a phone, or in the game. Falls are not animated.
- **New palette family.** `crag` is a new accent (`accent:highland`), awaiting Matt.

## Next

1. Matt looks at `highland-3x.png`, `edges.png` and `area-3x.png` (and the local Eastward comparison) and says whether this is the highland and whether the meadow reads as its own biome.
2. If yes: the mountain kit (PR #148) is rebuilt on the core; the valley's banks take the meadow set; then the coast and canyon sets get their polish, and new biomes get their own edge sets.
3. A zone adopts it through `Plan` and `walk_tiers()`; the asset ledger grades its outputs when a zone ships them.
