# House style: one NapAttack look at Eastward's level of detail

Matt, 20 Oct 10:15: "the level of detail here is fairly good but don't let eastward guide all of the stylistic parts (you have to consider the setting eastward is set in vs mine)". 10:18: "I want you to have a consistent (your own) art style with eastward level of detail."

Status: proposed by Claude A on 20 Oct. The rules below apply to new art now. The palette (`art/house-palette.json`) is a proposal until Matt chooses (see "Decisions for Matt"); until then `art/materials.json` stays as it is. Where this file and [art-style.md](art-style.md) disagree, this file wins once Matt approves it.

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

- **Families.** The palette is 37 families: 17 core (grass, leaf, earth, path, sand, water, stone, slate, timber, plaster, clay, iron, brass, berry, dusk, sky, snow) shared by every place, 15 setting accents, and 5 glows. Each is defined by one body colour in `scripts/art/house_palette.py` (`BASES`); everything else is computed.
- **Six tones a ramp,** 0 (deepest shade) to 5 (highlight), body at 3. In OKLab lightness the tones sit at body -0.33, -0.215, -0.105, 0, +0.085, +0.16 (squeezed only where they would pass 0.21 or 0.965), so every material has the same contrast.
- **Hue-shifted both ways.** Shade turns the hue up to 10 degrees towards dusk violet (OKLCH 298) and adds a small fixed violet tint; light turns it up to 10 degrees towards candle yellow (82) and adds a small warm tint. So even a grey has violet shade and warm highlights. Chroma eases off at both ends.
- **Siblings.** Each family has a warm and a cool sibling ramp (body turned 9 degrees towards lamp or dusk, a touch lighter or darker). A surface made of parts gives each part one of the three. This is how a wall gets Eastward's 20 or more tones in a patch while every colour stays on the palette.
- **Edges.** Each family has one edge tone (its tone 0 pulled 62 % towards the ink `#211A22`): the outline colour for that material.
- **Glows** (lamp, neon pink, neon cyan, lava, glowflora) are light sources: deep saturated to a near-white core, the same hue throughout, no edge, never used for a lit surface.
- **A region's accents** are made by the same rule from one body colour each, at most three a setting (Cogsworth: copper and soot; the desert: bleached, adobe, cactus; Neon Harbour: concrete and asphalt plus its neon glows). A new accent is a new line in `BASES`, never a hand-picked ramp.
- **No colour arithmetic outside the palette.** Shade and light move a pixel along its own ramp (`step` in the sheet's kit, `detail.shade` today); a mix of two colours, a multiplied shadow or an RGB gradient is not allowed on a sprite.
- **At most 64 colours a sprite, from at most 10 families** (siblings count with their family). The house exemplars use 59 to 117 colours for a whole 72 x 72 scene including its ground.

### 2. Outline

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

| Material | Recipe                                                                                                                                                                                                                                                                                                                                              |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Wood     | Lapped boards 4 or 5 px: a dark line under the board above, a lit lip, the body, a dark last row. Butt joints every 14 to 30 px with a nail head (dark, lit pixel above) beside each. Grain as 2 to 4 px streaks along the board, a knot now and then. Each board one of three siblings; weathered fronts mix timber with bleached.                 |
| Stone    | Courses 6 or 7 px of parts 8 to 15 long, each a sibling of stone or ashlar, the odd one a tone off. Mortar `stone_cool` 0 or 1. Moss in the lowest joints (leaf 2 and 3, a 2 px cap over a 4 px band). A chip is a corner knocked to mortar.                                                                                                        |
| Brick    | Courses of 4 px, bricks 8 long (7 x 3 with a 1 px joint), joints in `clay_cool` 1. Lit only along the left of each brick's top. Soot (the soot family) in patches high up under the eaves.                                                                                                                                                          |
| Metal    | Plates with square corners (machined), each a sibling, the odd one in a second family (primer). A seam is a dark line with a lit line under it. Rivets in rows: a lit head over its shadow. A slow sheen: lighter at a plate's upper left. Pipes and posts: a highlight band in the left third, dark at the right.                                  |
| Glass    | Lit from inside: lamp 1 along the frame's shadow (top and left), brighter towards the bottom middle, a curtain or an object as a silhouette. By day: slate 1 at the top, 2 below, one diagonal glint in two-pixel steps at the upper left. Panes sit in a recess; a sill casts a band.                                                              |
| Cloth    | Folds as vertical bands: lit (4), body (3), shaded (2), deep (1). Hems scalloped. Banners: a pole lit on top, a swallowtail, an emblem in brass.                                                                                                                                                                                                    |
| Foliage  | A crown in four light bands, leaf clumps of radius 2.6 one tone above their band, each with a light cap and a dark U under it, clumps from all three siblings, a yellow-green rim (grass 5) on the lit edge, the deep band quiet.                                                                                                                   |
| Water    | Dark under the near bank, depth in soft bands lying with the flow, the current as 3 to 5 px lit streaks over their own shadow, glints in pairs.                                                                                                                                                                                                     |
| Snow     | Light ground (snow 3) with drifts lit at the upper left (5) and violet in the shade (2), the drift's shadow a line of `snow_cool` 2; footprints pressed in (cool 1 over 2); sparkles in pairs.                                                                                                                                                      |
| Regolith | Grey to brown-grey (the regolith family and its siblings), calm patches, grit as sibling clusters, stones each with a hard shadow pair. Craters: a raised rim lit outside at the upper left, the inner wall under that rim in hard shadow (tone 0), the far inner wall lit (4), a flat floor; ejecta as lighter pairs; boulders with black shadows. |

Plaster, sand, earth and grass follow the ground recipe (rule 8).

### 6. Shadows

- A cast shadow is the object's silhouette thrown down and to the right (`detail.silhouette_shadow`), hard-edged.
- It **steps the ground two tones down its own ramp**, so the shadow stays on the palette and turns violet by the ramps' own lean. Desert: two tones and a longer throw. Night: one tone. The airless moon: three tones (no ambient light, black shadows).
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

Where the house exemplars stand (style sheet, 20 Oct): the cottage front, Cogsworth's brick and iron, the desert false front, the castle gate and the moon's ground pass; today's versions of the same subjects pass in two of seven (the castle gate and the neon shopfront). The neon shopfront (tones 20.9 of 25.6) and the station module (20.2 of 25.2) still fall short on tones only: very dark and very light surfaces lose tones in the bar's quantising, so night walls and white shells need more parts in accent families (posters, signs, primer plates, dust) than a mid-tone wall. Of the material swatches, wood, stone, brick, foliage and water pass; metal, snow and regolith are short on tones on their own and pass only as part of a scene.

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
- `scripts/art/style_lint.py <module ...> | --all | --png FILE`: report only. Per sprite: colours and families, share on the house palette and on today's ramps, outline darkness, flat ink and doubling, west minus east and top minus bottom light, lone pixels and dither, and the rules it misses.

## Decisions for Matt

1. **The palette.** Approve the house palette (warm lamplight against dusk-violet shade, 17 core families, siblings) as the one palette, so step 2 recolours the whole world at once? Or keep `materials.json` and only use the rules?
2. **Siblings.** Reaching Eastward's tone counts with a strict palette needs a warm and a cool sibling for every family (606 colours in all, every one made by the rule). The alternative is fewer colours and missing the bar on tones. We recommend siblings.
3. **The moon and the station.** The moon becomes grey brown-grey (not lavender), shadows on it three tones down (black), and nothing on the moon is built of brick or stone. Agreed?
4. **The bar at the extremes.** Night walls and white shells lose tones in the bar's quantising. Hold them to the same numbers (more parts in accent families), or measure them against a night or white reference of their own?
