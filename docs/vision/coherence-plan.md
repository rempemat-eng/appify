# Coherence plan (from Matt's review, 17 Oct 2026)

Matt's feedback, in short:

- The mission map is not coherent and text is not aligned properly.
- The game menu should feel like a real game menu. Stardew Valley's tabbed menu is the reference for structure and visual separation.
- Bugs: the companion walks behind the bridge; some houses, bushes and the stall are missing outlines on the top and sides; some props have none.
- The art style must be more consistent and the visuals tested. Characters are hard to read ("hard to tell what's what"). The whole world needs proper visual separation (craftpix top-down sets as examples). The game proportions must be right.
- Not polished yet: icons lack detail, buttons run right to the edge of their bar, there is not enough visual separation, and menus need different font sizes used appropriately.
- Shading and shadows matter, but uncluttered. Matt's shading references: cosy top-down scenes with smooth light ground, objects outlined in a dark shade of their own material, flat single-tone cast shadows, large clean planes.
- Symmetry: not everything needs centring, but a button inside a bar must sit as far from the sides as from the top and bottom.
- The pixel density of the whole game probably has to increase to achieve all of this.
- Plan everything, then do it one step at a time.

This file is the working plan. Claude implements the steps in order on `main`. Each step is verified (checks, play-test, screenshots at 320, 375 and 402 px wide, day and night, zoomed crops, before and after) and pushed before the next one starts. The status column is kept current.

## What the audit found

| Area            | Measured                                                                                                                                                                                                                                                                                                          |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pixel density   | One art pixel is about 2 CSS px (about 6 device pixels on a 3× phone). At that density there is no room for buildings to be bigger than the companion, for detailed icons, or for clean multi-tone shading.                                                                                                       |
| Bridge layering | Objects are layered by their bottom edge (`y + h`); the companion by its feet, so a crossing companion was drawn behind the bridge. **Fixed in step 1.**                                                                                                                                                          |
| Outlines        | Share of silhouette edge outlined: hut top 33%, stall top 70% and sides 76%, bush top 77%, the meadow's plants 0%, the mission-world duck, hedge and stone 0 to 52%. **Fixed in step 2.**                                                                                                                         |
| Separation      | The grass is the most saturated surface (0.48) and textured; most objects are less saturated (0.34 to 0.43) and darker. Bushes and trees are green on green. Forest shade is dithered. Objects sink into the ground.                                                                                              |
| Proportions     | The companion is 25 to 29 px wide and 26 to 31 px tall at world scale. The hut is 50 × 46 px with a 10 × 14 px door: the companion is twice the door's height and 60% of the whole house. Trees are only 46 px tall.                                                                                              |
| Characters      | The Roamling (the starter) is green on green: ears, body, tail and legs share near-identical greens with heavy dithering; eyes are 1 to 2 px. Mossling and Pebbling read better but faces are small and shading noisy.                                                                                            |
| Interface       | HUD stats use three layouts (icon over number twice, number over bar) with no shared baseline. Hotbar slots and the HUD portrait run to the bar's edge. Icons are a few flat pixels. Object labels are an unframed translucent box. Two speech bubbles can stack. Panels use one tone, so sections blur together. |
| Mission map     | A flat green board with framed cards floating over it; paths end at card edges, a tree sits on the path, the road leaves the map.                                                                                                                                                                                 |
| Game menu       | A sheet of eight equal tiles: no tabs, no character page, no sense of place.                                                                                                                                                                                                                                      |

## Targets

### Density, grid and proportions

- **One art pixel is about 4 device pixels on a 3× phone (about 1.33 CSS px)**, and the nearest whole number of device pixels on other screens. That is 1.5 times the current density. A phone shows about 300 art pixels across. One shared scale (`lib/pixel-scale.ts`) is used by the world, the characters, the frames and the icons, so everything sits on one grid.
- One tile is 16 art px. The garden is re-laid-out at the new density; the camera keeps following the companion.
- Reference sizes in art px (width × height):

| Thing                              | Size                          | Why                                                 |
| ---------------------------------- | ----------------------------- | --------------------------------------------------- |
| Companion and visitors             | 32 × 32 canvas, about 26 tall | about 35 CSS px on a phone: readable, not oversized |
| Hut door                           | 16 × 28                       | just taller than the companion                      |
| Hut                                | about 104 × 92                | a home, about three and a half companions tall      |
| Stall                              | about 88 × 72                 | a counter at companion height                       |
| Broadleaf tree / small tree / pine | 64 × 88 / 48 × 64 / 36 × 76   | trees tower over the companion                      |
| Bush / rock                        | 32 × 24 / 20 × 14             | below companion height                              |
| Bench (reading nook)               | 44 × 28                       | the companion fits on it                            |
| Lantern / mailbox / signpost       | 14 × 40 / 18 × 32 / 28 × 36   | posts are taller than the companion                 |
| Watering can / bowl                | 18 × 14 / 18 × 10             | small hand props                                    |
| Path / bridge deck                 | at least 36 wide / 44 wide    | the companion fits with room on both sides          |

### Shading and separation (after Matt's references)

- **Outlines** close every silhouette and use a dark shade of the material they enclose (deep brown on wood, dark olive on leaves, slate on stone). Characters keep a dark, warm outline. _(Done in step 2.)_
- **Objects** are built from large, clean planes: 3 to 4 tones per material, lit from the upper left, with a highlight along top edges. No noisy dithering.
- **Cast shadows** are one flat, darker tone of the ground, offset down and to the right, shaped by the object (a canopy blob for trees, a roof band for houses). One shadow per object, never stacked or dithered.
- **Ground** is light and smooth, with very little texture: sparse one-tone tufts and a few flowers. It never competes with the objects.
- **Hue families** separate things: ground is yellow-green; foliage is a different green or gold; wood is warm brown; stone is blue-grey; water is teal with a light rim.
- **Terrain borders**: a darker rim where grass meets a path or soil, a light bank and darker edge at water.
- Measured in the art checks: outline coverage ≥ 95% (in place), ground texture contrast, a value or hue gap between ground and foliage, and a cast shadow for every standing object.

### Characters

- A clear, unique silhouette per species and visitor, readable at 1×.
- One outline colour, 3 tones per material, no dithering on bodies.
- Faces read first: eyes 2 × 3 px with a highlight, a lighter face patch or muzzle, cheeks.
- Parts are separated by value, not just outline: ears, body, legs and tail never share one tone.
- Hats and accessories have their own outline and colour.

### Interface

- **Symmetric insets.** Every bar, panel and slot has one inset, used on all four sides and between its children. A button inside a bar is as far from the sides as from the top and bottom; nothing touches a frame edge.
- **Layers for separation**: outer frame (wood), inner panel (parchment), wells (inset, darker), items (raised, with a one-unit shadow). A child never sits on the same tone as its parent. Section dividers are engraved (a dark line over a light line).
- **Type hierarchy** (Pixelify Sans; Press Start 2P only for big numbers):

| Style   | Size / line height | Used for                                  |
| ------- | ------------------ | ----------------------------------------- |
| Title   | 20 / 28            | sheet and page titles                     |
| Heading | 16 / 24            | panel headings, the selected item's name  |
| Body    | 14 / 20            | descriptions                              |
| Label   | 12 / 16, bold caps | tabs, buttons, stat names, section labels |
| Caption | 11 / 16            | hints and small print                     |

- **Alignment**: content starts at the inset, so left edges line up. A single-line label is centred by giving it the box's line height. An icon and its value share one centre line. Numbers in stat rows are right-aligned.
- **Icons**: one generated pixel icon set (`scripts/art/icons.py`): 16 × 16 art px for the hotbar, HUD and tabs, 24 × 24 for menu headers. Each has a tinted outline, 3 tones and upper-left light. Every glyph in the UI comes from this set.
- **One speech style**: object labels and speech bubbles share one pixel frame, with one bubble at a time.

### Game menu (Stardew Valley's structure, NapAttack's palette)

- A wooden outer frame with a parchment inner panel. A row of icon tabs across the top (Companion, Bag, Journal, Garden, Rhythm, Settings); the active tab is raised and joins the panel. A close button in the corner, plus Escape and Back.
- The Companion page: a framed portrait standing in a small garden scene, name, family and level, and stat rows (mood, growth to the next level, play time, rest today) with segmented pixel bars and an icon on the left of each.
- The Bag page is a grid of inset card slots with counts; tapping one shows its details. The other pages reuse the existing content inside the same frame.

## Steps

| #   | Step                            | What changes                                                                                                                                                                                                                                               | Done when                                                                                                                                        | Status  |
| --- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| 1   | Ground layer for flat objects   | Bridges are baked into the ground layer in the garden and the mission worlds; the map exports `gardenFlat`.                                                                                                                                                | check-garden proves nothing can cover a walkable spot on the bridge; a browser crossing shows the whole companion.                               | done    |
| 2   | Complete, tinted outlines       | `style.close_outline` closes every silhouette and tints outlines by material; applied to every garden, growth and mission-world sprite.                                                                                                                    | `check:sprites`: all 61 sprites ≥ 95% outlined on every side; it fails on the old art.                                                           | done    |
| 3   | Interface system                | Inset, layer and type tokens in one module (`lib/ui-tokens.ts`), parameterised by the pixel unit. HUD stats become one row of equal icon-and-value chips; the hotbar, HUD and buttons get symmetric insets; panels get layers; one speech and label style. | Screenshots at 320 and 402 px with an inset overlay show equal insets and shared left edges; a source check measures insets on bars and buttons. | next    |
| 4   | Pixel icon set                  | `scripts/art/icons.py` draws detailed icons (home, missions, nap, arena, shop, shield, grass, time, heart, menu, tabs, close) with tinted outlines and shading; `PixelIcon` replaces every hand-drawn glyph.                                               | An icon sheet at 1× and 2×; every UI glyph comes from the set.                                                                                   | planned |
| 5   | Game menu                       | The tabbed menu replaces the tile sheet: wooden frame, icon tabs, Companion page with stat bars, Bag page with card slots, other pages in the same frame.                                                                                                  | Play-test every tab, keyboard and Back; menu screenshots at 320 and 402 px.                                                                      | planned |
| 6   | Density and the garden, redrawn | `lib/pixel-scale.ts` switches the whole game to the new density. The garden is re-laid-out at the proportions table and redrawn with the shading rules (clean planes, flat cast shadows, calm ground, hue families, terrain rims).                         | Art checks for sizes, shadows and ground texture pass; the garden harness passes on the new map; before/after day and night.                     | planned |
| 7   | The same rules in every world   | Mission worlds, the battle backdrop and scene vignettes at the new density and shading rules.                                                                                                                                                              | Art checks cover them; screenshots of each world.                                                                                                | planned |
| 8   | Characters                      | The three companions (three stages each), nine visitors and Dave redrawn at the new density with the character rules.                                                                                                                                      | A readability sheet at 1× and 2× on grass and on paper; screenshots of garden, HUD, battle, nap, journal and picker.                             | planned |
| 9   | The mission map as a place      | A generated map in the world style: the garden gate at the bottom, a road branching to the park, library and mountain cabin, landmarks drawn in the scene, names on signposts, the companion standing at the chosen place.                                 | No floating cards; paths meet landmarks; a play-test from map to mission and back.                                                               | planned |
| 10  | Shop and Arena as places        | Ask Matt first: the inside of Moss's stall for the Shop, a clearing beyond the fence for the Arena.                                                                                                                                                        | Matt's go-ahead.                                                                                                                                 | ask     |

Why this order: steps 3 to 5 are interface work that Matt sees on every screen and that does not depend on the art. They are written in pixel units, so the density switch in step 6 carries them along. Steps 6 to 8 redraw the art once, at the final density and proportions, rather than twice.

## Testing the visuals (every step)

- Screenshot suite in a desktop browser at 320 × 640, 375 × 667 and 402 × 874, day and night, with zoomed 3× crops of anything changed, compared before and after.
- The art checks (`check:art`, `check:sprites`) gain each measured rule as it lands, so regressions fail the build.
- Nothing here is claimed as tested on a phone until Matt or a device check confirms it.

## Working with Codex

While a step is in progress Claude owns its files (mostly `scripts/art/*`, `assets/*`, `components/garden-world.tsx`, `components/game-hud.tsx`, `components/game-menus.tsx`, `components/pixel-frame.tsx`, `components/game-ui.tsx` and the new `lib/ui-tokens.ts`). Codex: please review and test landed steps, or work on files outside the current step, and avoid editing those files until the step's status reads done.
