# House style: one NapAttack look at Eastward's level of detail

Matt, 20 Oct 10:15: "the level of detail here is fairly good but don't let eastward guide all of the stylistic parts (you have to consider the setting eastward is set in vs mine)". 10:18: "I want you to have a consistent (your own) art style with eastward level of detail."

Status: proposed by Claude A on 20 Oct. The rules below apply to new art now. Matt, 20 Oct 11:00: "this is starting to look really good"; 11:20: "i like this bottom row besides the brick building". So **the bottom row of the style sheet (the house versions of the seven settings) is the approved target for each setting**, with the brick building redrawn in true brick (rule 5) in the next round. The palette (`art/house-palette.json`) is a proposal until Matt chooses (see "Decisions for Matt"); until then `art/materials.json` stays as it is. Where this file and [art-style.md](art-style.md) disagree, this file wins once Matt approves it.

## Who we are

NapAttack is a cosy game about rest, so the whole world is drawn as if at the end of a warm afternoon: **warm lamplight against cool, violet shade**. Light leans to candle yellow, every shadow leans to the dusk violet of the game's own nap colour, and that lean is the thread of sleep that runs through every place, from the valley to the neon city to the moon. Forms are **soft and chunky**: every brick, board, stone, slate and plate is a small pillow with a lit top, a dark underside and its corners knocked off, so nothing is sharp. Places are clean and cared for rather than ruined; detail comes from many small, deliberate parts, never from noise. Eastward sets how much detail a patch carries. Our palette, our light and our soft forms are our own, and they stay the same in every setting; only forms, materials and accents change with the place.

## What we found (20 Oct, main at 7e0992e)

The five lanes drew the same world with five drawing kits. A contact sheet of one prop per module at 3x on neutral grey (`scripts/art/style_sheet.py` draws today's crops beside the house versions; the full audit is `python3 scripts/art/style_lint.py --all`):

| Lane | Modules                                                                             | What differs                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A    | `frost_props`, frost and terrace grounds                                            | Snow and the ridge face in banded stripes; frost grounds use checker dither (2 to 3 % of pixels) and lone pixels (11 to 16 %); the terrace's proposed grass and soil are a separate palette                                                                                                                                                                                                                             |
| B    | `garden_props`, `world_props`, `valley_props`, `harbour_props`, `home_props`        | Closest to the house look (the house style grew from it): on the shared ramps, chunky, warm. But speckle: `valley_props` has 13 % lone pixels (fleece, flowers, blades), and 14 sprites with doubled outlines                                                                                                                                                                                                           |
| C    | `steampunk_props`, `cyber_props` (`facade.py`), `isle_props`                        | Neon facades are painted in RGB: 170 colours a sprite, off the ramps; Cogsworth's cobbles are salt and pepper (18 % lone pixels on the junction ground); the isles' ground dithers (4 %) and the lagoon is a saturated turquoise no other place has                                                                                                                                                                     |
| D    | `western_props`, `castle_props`, `caldera_props`, `space_props` (`reach_detail.py`) | The detail pass works in RGB (`rd.mix`, `rd.step`): the saloon has 4,216 colours and 42 % lone pixels, so its boards read as a photo; castle stone is grey and desaturated (109 colours, 2 % on the ramps); space has 111 colours a sprite; the moon is lavender (Matt asked for grey to brown-grey) with dithered craters; Lumen's hab hub is built of stone blocks (the setting rule says no brick or stone up there) |
| E    | `valley_zones` (grounds)                                                            | The most saturated ground in the game (chroma 0.09 to 0.10 against 0.03 in Cogsworth and 0.05 at Hearthold) with 11 to 13 % lone pixels from single-pixel flowers and blades                                                                                                                                                                                                                                            |

What already agrees everywhere: light from the upper left (every module's mean is lit on the west), and every outline is closed and dark (`style.finalize`). What does not: palette (each region drifted its own way), outline colour (tinted from whatever the fill was), shading style (bands in the valley, RGB gradients in the Reach and space, flat fills on the station), texture vocabulary (clusters, dither, speckle) and contrast (Hearthold and Cogsworth grey and flat, the valley bright and saturated).

## The rules

### 1. One palette, made by one rule

- **Families.** The palette is 38 families: 17 core (grass, leaf, earth, path, sand, water, stone, slate, timber, plaster, clay, iron, brass, berry, dusk, sky, snow) shared by every place, 16 setting accents (the 16th, `crag`, the highland's warm dark rock, proposed with the cliff core on 21 Oct: [cliff-core.md](cliff-core.md)), and 5 glows. Each is defined by one body colour in `scripts/art/house_palette.py` (`BASES`); everything else is computed.
- **Six tones a ramp,** 0 (deepest shade) to 5 (highlight), body at 3. In OKLab lightness the tones sit at body -0.33, -0.215, -0.105, 0, +0.085, +0.16 (squeezed only where they would pass 0.21 or 0.965), so every material has the same contrast.
- **Hue-shifted both ways.** Shade turns the hue up to 10 degrees towards dusk violet (OKLCH 298) and adds a small fixed violet tint; light turns it up to 10 degrees towards candle yellow (82) and adds a small warm tint. So even a grey has violet shade and warm highlights. Chroma eases off at both ends. The one exception is the moon (`accent:moon`): the violet in shade is light from the sky, and the moon has no sky, so its ramps keep their own hue in shade, take a tenth of the tint and fall to nearly black (tone 0 at OKLab 0.13 to 0.2).
- **Siblings.** Each family has a warm and a cool sibling ramp (body turned 9 degrees towards lamp or dusk, a touch lighter or darker). A surface made of parts gives each part one of the three. This is how a wall gets Eastward's 20 or more tones in a patch while every colour stays on the palette.
- **Edges.** Each family has one edge tone (its tone 0 pulled 62 % towards the ink `#211A22`): the outline colour for that material.
- **Glows** (lamp, neon pink, neon cyan, lava, glowflora) are light sources: deep saturated to a near-white core, the same hue throughout, no edge, never used for a lit surface.
- **A region's accents** are made by the same rule from one body colour each, at most three a setting (Cogsworth: copper and soot; the desert: bleached, adobe, cactus; Neon Harbour: concrete and asphalt plus its neon glows). A new accent is a new line in `BASES`, never a hand-picked ramp.
- **No colour arithmetic outside the palette.** Shade and light move a pixel along its own ramp (`step` in the sheet's kit, `detail.shade` today); a mix of two colours, a multiplied shadow or an RGB gradient is not allowed on a sprite.
- **At most 64 colours for a prop and 128 for a building** (over 2,500 px). The house exemplars use 18 (the moon) to 117 colours for a whole 72 x 72 scene including its ground, and the kit fronts use 37 to 113.

### 2. Outline

**Terrain edges** (rims, lips, faces, feet, sides, corners, transitions, water's edge, stairs) follow [eastward-edges.md](eastward-edges.md): Eastward is the only reference for edges and the soft grid (Matt, 21 Oct 09:23), for their geometry and value structure, while the colours stay this palette's, one ramp per terrain (Matt, 21 Oct 09:31). On terrain, only a change of height is outlined (eastward-edges 4).

- One pixel, outside the silhouette, in the **edge tone of the family it closes** (wood closes in deep brown, leaves in deep green, stone in violet grey). Never a flat ink round a light material, never a second dark ring inside the first.
- **Lit break.** Where it closes a top or left edge whose fill is tone 4 or 5, it breaks to that family's tone 1, so the light seems to wrap round the form.
- Interior lines (seams, mortar, frames) use tone 0 to 2 of the material, never ink. Ink is for eyes and the deepest gaps.
- No outline on ground textures, glows, particles, spray, specks of three pixels or fewer, or water's lit streaks.

### 3. Light

- From the upper left, always, in every setting (also at night, also on the moon).
- Top planes tone 4, west faces 3 to 4, south faces 3, east faces 1 to 2, undersides 1.
- Tone 5 only on the most lit edges: a two-pixel glint at a part's top left, a rim, a crest. Tone 0 only in crevices, contact lines and the core of cast shadows.
- The terminator is one hard step, never dithered.
- Check: `style_lint.py` reports west minus east lightness; it must be positive for every sprite.

### 4. Shading technique

- **Parts.** Surfaces are built of chunky parts: a lit top row, a body, a dark bottom row; a part four or more pixels tall also has a lit left and dark right column; corners knocked off to the seam. Small parts catch the light only along the left of their top. Joints are always darker than the parts they separate (a joint is a recess).
- **Clusters.** Texture is clusters of two to four pixels (dominoes, L shapes, 2 x 2). Most clusters only swap to a sibling ramp at the same tone (they add shape without value noise); a few step one tone up (more on the lit side) or down.
- **No speckle.** A lone pixel (unlike all four neighbours) is a rivet, a nail head, a glint or an eye, nothing else. Target: at most 6 % of a sprite's inside.
- **Dither** only on ground, only for an atmospheric fade at a place's edge (forest shade, the Skyport's tiles giving way, haze), only as the 2 x 2 checker of `style.dither_dark`. Never on a sprite, never on open walkable ground, never to shade a form.

### 5. Materials (each drawn in `scripts/art/style_sheet.py`)

| Material | Recipe                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Wood     | Lapped boards 4 or 5 px: a dark line under the board above, a lit lip, the body, a dark last row. Butt joints every 14 to 30 px with a nail head (dark, lit pixel above) beside each. Grain as 2 to 4 px streaks along the board, a knot now and then. Each board one of three siblings; weathered fronts mix timber with bleached.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Stone    | Courses 6 or 7 px of parts 8 to 15 long, each a sibling of stone or ashlar, the odd one a tone off. Mortar `stone_cool` 0 or 1. Moss in the lowest joints (leaf 2 and 3, a 2 px cap over a 4 px band). A chip is a corner knocked to mortar.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Brick    | True brick in stretcher bond, drawn as a wall of objects, not a pattern (Matt, 20 Oct: the first round read as scales, the second as a flat grid): bricks 7 x 3, courses 4 px, each course shifted half a brick. Joints recessed and dark (bed `stone_cool` 2, head `stone_cool` 1), so the grid recedes; each brick stands proud, its top lit towards the left, its east end a tone down. Colour in firing batches (broad patches of clay's warm or cool sibling), the odd brick a tone off, a few over-fired (dark purple-brown) or under-fired (pale), the odd brick spalled (set back in shade, its lower lip lit). Soot takes whole bricks in drifts under the eaves; moss in the lowest joints. Openings have gauged heads: rubbed bricks on end in fine lime joints, a warmer red, rising a pixel at the middle. Never knocked-off corners on every brick (scales), never light mortar on every joint (graph paper). |
| Metal    | Plates with square corners (machined), each a sibling, the odd one in a second family (primer). A seam is a dark line with a lit line under it. Rivets in rows: a lit head over its shadow. A slow sheen: lighter at a plate's upper left. Pipes and posts: a highlight band in the left third, dark at the right.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Glass    | Lit from inside: lamp 1 along the frame's shadow (top and left), brighter towards the bottom middle, a curtain or an object as a silhouette. By day: slate 1 at the top, 2 below, one diagonal glint in two-pixel steps at the upper left. Panes sit in a recess; a sill casts a band.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Cloth    | Folds as vertical bands: lit (4), body (3), shaded (2), deep (1). Hems scalloped. Banners: a pole lit on top, a swallowtail, an emblem in brass.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Foliage  | A crown in four light bands, leaf clumps of radius 2.6 one tone above their band, each with a light cap and a dark U under it, clumps from all three siblings, a yellow-green rim (grass 5) on the lit edge, the deep band quiet.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Water    | Dark under the near bank, depth in soft bands lying with the flow, the current as 3 to 5 px lit streaks over their own shadow, glints in pairs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Snow     | One calm, wide plane (snow 3) with broad swells a tone lighter, no grit. Where it ends, a crisp scalloped edge (scallops 6 px): a lit lip (5), the shaded south face under it (2 then 1), the ground below two tones down. Blue-violet shade (1 and 2) in hollows and on the south and east sides of everything in it; drifts piled against posts and stones on their windward west side, with a shade line at the foot; caps on top of things, scalloped underneath; footprints pressed in (shade along each print's top); a few sparkles in pairs.                                                                                                                                                                                                                                                                                                                                                                        |
| Regolith | Grey to brown-grey (the regolith family and its siblings, airless: no violet), calm broad patches, grit as sibling clusters, stones each with a hard, nearly black shadow pair. Craters: a raised rim lit outside at the upper left, the inner wall under that rim in hard shadow (tone 0), the far inner wall lit (4), a flat floor; ejecta as lighter pairs; boulders with black shadows.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

Plaster, sand, earth and grass follow the ground recipe (rule 8).

### 6. Shadows

- A cast shadow is the object's silhouette thrown down and to the right (`detail.silhouette_shadow`), hard-edged.
- It **steps the ground two tones down its own ramp**, so the shadow stays on the palette and turns violet by the ramps' own lean. Desert: two tones and a longer throw. Night: one tone. The airless moon: three tones, to nearly black (no ambient light).
- Every object meets the ground with a contact line (the ground at tone 0 or 1) one pixel under its foot.
- Overhangs (eaves, sills, porch roofs) throw a band on the wall below: two tones down in its first row, one in the next, a row deeper towards the east.
- Round blob shadows only under round things (a barrel, a pot, a tree's crown).

### 7. Detail density: the Eastward bar

Every surface is measured with `scripts/art/detail_bar.py` (the terrace toolkit branch) against Eastward at the same character height (an adult 25 px). Per 16 x 16 patch, the reference means are:

| Kind       | Tones | Shapes | Dressing |
| ---------- | ----- | ------ | -------- |
| Facade     | 25.6  | 33.9   | 28.6     |
| Wood front | 24.0  | 36.3   | 30.5     |
| Machinery  | 25.2  | 32.1   | 27.1     |
| Stone wall | 18.6  | 28.2   | 22.4     |
| Roof       | 19.1  | 41.7   | 33.3     |
| Tree       | 20.4  | 35.8   | 29.3     |
| Water      | 13.4  | 21.3   | 16.8     |
| Ground     | 12.6  | 31.9   | 24.1     |

Ours must reach 90 % of each, and be no noisier (lone pixels at most the reference's plus 2 points, clusters at least 90 % as large). The house way to reach it is more parts and more siblings, never more contrast or speckle.

**Ground is judged for cleanliness** (Matt, 21 Oct 10:52: "your current renders are visually too noisy. compare with eastward. i want it to be cleaner, like eastward"): for `ground` the bar's shape and dressing minimums are replaced by Eastward's cleanliness at our scale (visible edges, lone pixels, the two main colours' share, colours a square; `eastward-edges.md` 5.5, `detail_bar.clean_counts`) and its tones minimum drops to half. A ground is a flat fill, a few large soft blotches a tone or two apart, and sparse clumped tufts and flowers placed by rule.

Where the house exemplars stand (style sheet, 20 Oct, second round): the cottage front, Cogsworth's brick and iron (true brick: tones 30.0, shapes 48.8 against 25.6 and 33.9), the desert false front, the castle gate and the moon's ground pass; today's versions of the same subjects pass in two of seven (the castle gate and the neon shopfront). The neon shopfront (tones 20.9 of 25.6) and the station module (20.2 of 25.2) still fall short on tones only: very dark and very light surfaces lose tones in the bar's quantising, so night walls and white shells need more parts in accent families (posters, signs, primer plates, dust) than a mid-tone wall. Of the material swatches, wood, stone, foliage, water and regolith pass. Brick has no baseline of its own: against the stone-wall bar (big stones) its small bricks count as noisy, so brick is judged as a facade, where it passes. Metal is short on tones on its own. Snow is a calm plane by design (Matt: wide planes, a crisp edge) and is far below the lawn-based ground bar; it is judged by eye until there is a snow reference.

**The bar is not enough on its own** (Matt, 20 Oct 11:20: "dont get lazy with detail in the future, make sure the detail makes sense and looks right"):

- **Every detail must make sense for the object:** what it is, why it is there and how it is built. Bricks lie in a bond, boards are nailed at joints, moss grows in damp low joints, soot settles under eaves, snow drifts on the windward side, a lit window is lit from inside. A detail added only to raise a count is not allowed.
- **It must look right at game scale,** checked by eye beside a reference of the same kind of thing (a photo or an official screenshot) at the same character height, at 3x and at 1x, by day and under the night tint. A surface that passes the bar but reads wrong (the first brick round read as orange scales) goes back.
- Every art PR says what it was compared with by eye, as well as its numbers.

**Rulings on the bar (Claude A, 20 Oct 17:30, for C's #132 and #134 and every lane):**

- **Drawn in ramps, the tones bar is 85 %.** The house palette gives each material a six-tone ramp with warm and cool siblings, so a surface drawn only from ramps has fewer distinct colours than Eastward's stepped mixes. Ramp-built art passes tones at 85 % of the reference, and still needs shapes, dressing and both cleanliness tests in full. Reach the tones with materials that belong together (stone with its moss and damp families, timber with its paint and weathering families, metal with rust, grime and primer) and with sibling ramps for lit and shaded planes, never with colours outside the palette.
- **Open structures are measured on their solid parts.** A lattice crane, a truss mast, rigging or a fence is mostly air, and the cluster test reads 1 to 2 px members as specks. Measure the boxes that frame solid members (the crane's cab and counterweight, the mast's foot and platforms) against machinery; members, cables and lattices are judged by eye: every member meets another at a joint with a plate or rivet, cables hang in a catenary, lit faces upper left.
- **Cloth is judged by eye until it has a baseline:** sails, awnings, tents, banners and an airship's envelope show their panels or gores and seams, a bolt rope or hem, tension lines where they are pulled, folds where they are slack, a lit belly and a shaded lee, and weathering in clusters.

### 8. Readable on a phone

- The world is seen at 1.3 to 2 screen pixels an art pixel: detail in clusters of two or more, nothing that depends on one pixel.
- Walkable ground is calm and light: one family and its siblings, body tone 3, broad soft patches at most one tone off, clusters mostly sibling swaps. Tones 0 and 5 belong to things that stand up (props, edges, rims), so they read against the ground.
- Every prop keeps a silhouette that reads in two values, and a 44 px touch target.
- Clutter gathers against walls and under trees; paths, doors and the space round the companion stay open (art-style.md).
- Check every sheet at 3x and at game scale, by day and under the night tint.

### 9. What a setting may change, and what never changes

| A setting may change                                                                                      | Never changes                                                                    |
| --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Forms: roof shapes, false fronts, arches, pressure shells, crater fields                                  | The ramp rule: six tones, the same lightness steps, the lean to dusk and lamp    |
| Materials: which families it builds with (brick and iron; bleached boards and adobe; plates and regolith) | The outline: one pixel, the family's edge tone, the lit break                    |
| Up to three accent families made by the rule, and its glows                                               | Light from the upper left, the hard terminator, where tones 0 and 5 go           |
| Ambient: the shadow step (desert 2 and longer, night 1, moon 3), weather, the night tint                  | Shading by parts and clusters; dither only for atmospheric fades                 |
| Ground dressing and story props                                                                           | Shadow shape (thrown down and to the right, hard), contact lines, overhang bands |
| How dense the clutter is, within the phone rules                                                          | The detail bar and the no-speckle rule                                           |

## Kits: a few designs per environment, reused within it

Matt, 20 Oct ~11:35: "you can use the house style where it fits but mindful of the environment. but within the same environment you can reuse it. but to make it less repetative perhaps come up with a few different designs that you can then reuse".

So each environment has a kit in `scripts/art/house_kits.py`: a function per piece, each with a variant argument, all deterministic and all in the house style. The kits are valley and isles cottages, Cogsworth brick and iron, Sunstone frontier timber and adobe, Hearthold castle stone, Neon shopfronts and facades, Halcyon station modules, and Lumen habitats and regolith. Each kit has these pieces:

| Piece               | What it is                                                                                                                                  | Variants |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `front(env, v, cw)` | A whole building front: roof or top, one or two storeys, door, windows, signs and dressing, in a colourway                                  | 4        |
| `door(env, v)`      | A door in its surround, set into the environment's wall                                                                                     | 4 or 5   |
| `window(env, v)`    | A window in its wall: frame, panes, shutters, lintel, sill, box                                                                             | 4 or 5   |
| `roof(env, v)`      | The roof or top: ridge, gable, hip, flat roof with its rooftop things, false front, vigas, battlements, conduits, dome, a heap of moon soil | 4        |
| `sign(env, v)`      | A hanging sign, fascia, awning, neon tube, blade sign, banner, shield, stencil or status light                                              | 4        |
| `prop(env, v)`      | A small prop that belongs there (barrel, bench, planter, lamp, trough, crate, potted cactus, tank, console, dish, rock)                     | 4        |

The parts underneath (`wall`, `doorway`, `casement`, `roof_mass`, `chimney`, `hanging_sign`, `fascia`, `awning`, `lightbox`, `blade`, `stencil` and the dressing: water butt, log store, hanging basket, nets, crates, bins, vending machine, keypad, extinguisher, grab rail and the rest) are the same functions for every kit. What differs between kits is only the table of each environment's materials and forms (`ENV` and `LAYOUT`), so a kit stays mindful of its place: Cogsworth builds in brick, stock brick and ashlar under copper, slate and glass; the desert in bleached boards, adobe and corrugated iron; the neon city in concrete, glazed tile and painted harbour cladding (never brick); the moon in hull plates and heaped regolith, never stone. Every piece is sized by the scale table (`size-guide.md` 3): an adult 25 px, a door 32 x 14 (a shop's or a pair 32 x 22, a hatch 32 x 18 with its coaming), a window 16 x 12 with its head 26 above its floor, a ground storey 40 over a plinth of 4 (a shop storey 44 with its fascia), an upper storey 32, a sign's bracket 36 to 44 above the ground, an awning's front edge 36 to 40.

**Colourways** (Matt, 20 Oct 12:09: "use the same building and switch some of the colors (like the door, banners/ cloth and other pieces where it makes sense that the color would change)"). `front(env, v, cw)` keeps the structure and repaints only what a resident or owner would paint: doors and hatches, shutters, painted frames and trim, awnings, banners and curtains, sign boards, pots and their flowers, painted cladding, neon glass, livery stripes. Stone, brick, adobe, metal panels, natural roofs, timber left natural and glass stay as they are. Each colourway is a set of house ramps (so a repainted part keeps the light rule and its own edge tone), chosen per setting:

| Setting        | Colourways                                            | What changes                                                                     |
| -------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------- |
| Valley, isles  | cornflower, heather, sage, poppy, harbour             | door, shutters, painted frames, curtains, sign board, pots and flowers, cladding |
| Cogsworth      | oxblood, bottle green, prussian, black and gilt       | enamel door, fascia board (gilt lettering), sashes, blinds                       |
| Sunstone Reach | faded red, faded blue, mustard, sage, bare wood       | door and batwings, painted boards, awnings and curtains, sign boards             |
| Hearthold      | purpure, gules, azure, vert, or                       | banners (heraldic tinctures), oak or painted doors, shutters                     |
| Neon Harbour   | rose, teal, amber, mint, violet                       | awnings, roller shutters, doors, neon tubes and lightboxes, lanterns             |
| Halcyon, Lumen | rescue red, signal blue, hazard ochre, lagoon or dusk | hatch paint, livery stripe, status lamps                                         |

Each front has a default colourway (`DEFAULT_CW`) so the kit sheet shows variety. In a street, `street(env, n, seed)` picks fronts and colourways deterministically: no two neighbours are the same front, share a door colour or share a cloth colour, and a front that repeats along the street never repeats its colourway.

**Every part makes sense** (Matt, 20 Oct 12:09: "review the repeated buildings for logic issues and make sure there are not illogical parts"). Each item on a front has a box, and `logic()` holds every front in every colourway to a builder's rules; `python3 scripts/art/house_kits.py --check` runs them, and the picker on 240 streets per setting, and fails on any fault:

- nothing overlaps a door, a window or a shopfront, and fixtures do not overlap each other (a downpipe may pass a band; porch posts carry the porch; a downpipe runs into its water butt);
- nothing is cut by the front's edge; a door stands at least 3 px in from it;
- what stands on the ground meets the ground (pots, logs, barrels, crates, bins, a vending machine), and nothing stands in a doorway;
- a fascia, awning or lightbox has a shopfront or a door under it in its own storey;
- a hanging sign's bracket is 36 to 44 above the ground;
- a downpipe hangs from a gutter (never under thatch); a water butt has a downpipe running into it; firewood only where there is a chimney; a chimney only on a pitched roof over a hearth, drawn behind the roof and whole in the sprite;
- every hatch on the station and the moon has its control panel; the walls are the setting's own materials.

And by construction: every sign, lantern, basket, banner, blade, AC unit and camera hangs from a visible plate, arm, hook or bracket; square openings in masonry carry a lintel (a gauged soldier arch in brick, timber in adobe); window boxes sit on brackets; doors have a step (a coaming under a hatch, an airlock collar on the moon); lit glass shows a lit room, not a slab; in the neon city at night every lit pane and sign lights the wall round it.

**How a lane uses a kit.**

- For a building, call `front(env, v)`. For anything else, draw the environment's `wall` and set its `doorway`, `casement`, `roof_mass` and signs into it.
- Reuse freely within the environment. Never take a piece into another environment; only things found anywhere (a crate, a barrel, steam) cross over.
- Neighbours differ. No two buildings side by side use the same front, a door colour or a cloth colour; use `street()` or the same rules. On one phone screen (about three fronts at 402 x 874) a front repeats only in another colourway.
- Check every placed piece by eye at game scale. Ask whether it makes sense where it stands: a lit window has a room behind it, a sign shows what is sold there, a door meets a path.

**When to make a new variant instead of reusing one.**

- The building has a different purpose: a new trade or job needs its own door, sign and windows.
- Reuse would put the same variant twice on one screen, or the place has more buildings than its kit has variants.
- The site asks for it: a corner, a slope or tier (verticality.md), a gable end facing the path.
- A reference shows a form of the setting the kit lacks.

A new variant goes into `house_kits.py` (Claude A's file; other lanes ask on the crew board), never drawn ad hoc in a zone file. Before it is used, it is shown on its kit sheet beside today's equivalent, checked by eye, and run through the style lint and the detail bar.

**Where the kits stand** (20 Oct, second round, `python3 scripts/art/house_kits.py`): every piece is 100 % on the house palette, and all 28 fronts in all their colourways (128 variants) pass the logic check and the style lint. 121 of the 128 pass the detail bar: every valley, Cogsworth, Reach, Hearthold and Neon Harbour front in every colourway, Lumen's four habitats in 15 of 16, and two of the four Halcyon bulkheads in all colourways. Still short, all within 5 % of the bar: the Halcyon airlock in two of four colourways (clusters 3.1 to 3.2 of 3.26) and the Halcyon pod door in all four (tones 22.1 to 22.4 of 22.6, or clusters), and Lumen's dome in rescue red (tones 22.5). These are the very light and very dark surfaces that rule 7 already flags; the next step is more purposeful parts there, not noise.

## Migration

The order keeps every lane's work moving and recolours the world once, not five times.

1. **Matt approves** the palette and the rules (or asks for changes; the sheet regenerates in under a minute).
2. **One recolour, no generator changes.** Claude A writes `art/materials.json` from `house_palette.py --preview-materials` (today's names and indices, each tone replaced by its house tone by the mapping in `art/house-palette.json`, `from_materials`). Each ramp drifts 0.02 to 0.065 on average in OKLab, so on-ramp art changes little; the outline ink becomes `#211A22`. All generated art and the map are regenerated together in one PR, with before and after previews of every region.
3. **Each lane, in its next art PR, one module at a time**, runs `python3 scripts/art/style_lint.py <module>` before and after and fixes what it reports:
   - **A:** the terrace toolkit draws with the house grass and earth (replacing `PROPOSED_GRASS` and `PROPOSED_SOIL`); cast shadows become ramp steps instead of `SHADOW_MUL`; the frost grounds' dither and speckle become clusters; `frost_props` onto the house families.
   - **B:** siblings for many-part surfaces (roofs, walls, fences); outlines to edge tones (`style.close_outline` takes the family's edge instead of `outline_tone`); lone pixels out of `valley_props` (fleece, flowers, blades as clusters); doubled outlines removed.
   - **C:** `facade.py` and `cyber_props` paint with house families and `step` instead of RGB (170 colours a sprite to 64 or fewer); Cogsworth's cobbles as setts (parts) instead of speckle; the isles' ground dither to clusters and the lagoon to the `lagoon` accent.
   - **D:** `reach_detail.py` keeps its structure (planks, courses, panels, weather) but picks siblings and moves along ramps instead of `mix` and `step` in RGB (the saloon from 4,216 colours to under 64); castle stone to the ashlar family; the moon's regolith to grey brown-grey with the crater recipe; Lumen's hab hub rebuilt as a pressure shell of plates (no stone on the moon).
   - **E:** the valley's grounds to the ground recipe: calmer, sibling clusters, flowers and blades as clusters of two or more.
4. **Then the lint gates.** Once every module is through, `style_lint.py` moves from report-only to a check in `npm run check`, with each threshold set from the migrated art.

## Tools

- `scripts/art/house_palette.py`: the rule and the bases; `--write` regenerates `art/house-palette.json`, no flag checks it, `--preview-materials OUT.json` writes today's ramps recoloured for a trial render.
- `scripts/art/style_sheet.py [OUT_DIR]`: the house style sheet (palette, ten material swatches, seven settings today and redrawn) at 3x, the before and after pairs, the lint and, where `detail_bar.py` is present, the bar. Its kit (`part`, `courses`, `boards`, `roof_rows`, `plates`, `grain`, `ground`, `leafy`, `glass`, `window`, `outline`, `cast`, `step`) is the reference for the recipes above; lanes can copy from it.
- `scripts/art/house_kits.py [OUT_DIR] [env ...]`: the seven environment kits, one sheet per environment at 3x with today's equivalents, a sheet of every front and one street per setting at 2x, and the lint, the bar and the logic check for every front in every colourway. Written outside the repository by default. `--check` runs the logic check and the colourway picker only, and exits non-zero on a fault.
- `scripts/art/style_lint.py <module ...> | --all | --png FILE`: report only. Per sprite: colours and families, share on the house palette and on today's ramps, outline darkness, flat ink and doubling, west minus east and top minus bottom light, lone pixels and dither, and the rules it misses.

## Decided

- **The moon** (Matt, 20 Oct ~11:00): grey to brown-grey regolith, never lavender; shadows nearly black (the airless ramps, cast shadows three tones down); craters with lit rims, nearly black inner shadow and ejecta; nothing on the moon built of brick or stone (Lumen's hab hub becomes a pressure shell of plates).
- **The bottom row of the style sheet** is the approved target for each setting (Matt, 20 Oct 11:20), with Cogsworth in true brick.
- **Where the house style applies** (Matt, 20 Oct ~11:35): wherever it fits each environment, mindful of that environment. Within one environment, its designs are reused. To keep that from repeating, each environment has a kit of a few designs (see "Kits").

## Decisions for Matt

1. **The palette.** Approve the house palette (warm lamplight against dusk-violet shade, 17 core families, siblings) as the one palette, so step 2 recolours the whole world at once? Or keep `materials.json` and only use the rules?
2. **Siblings.** Reaching Eastward's tone counts with a strict palette needs a warm and a cool sibling for every family (606 colours in all, every one made by the rule). The alternative is fewer colours and missing the bar on tones. We recommend siblings.
3. **The bar at the extremes.** Night walls and white shells lose tones in the bar's quantising. Hold them to the same numbers (more parts in accent families), or measure them against a night or white reference of their own?
