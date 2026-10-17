# Coherence plan (from Matt's review, 17 Oct 2026)

Matt's feedback, in short: the mission map is not coherent and text is not aligned properly. The game menu should feel like a real game menu (Stardew Valley's tabbed menu is the reference). There are still bugs: the companion walks behind the bridge, and some houses, bushes and the stall are missing outlines on the top and sides; some props have none. The art style needs to be more consistent and the visuals tested. The characters are hard to read ("hard to tell what's what"). The whole world needs proper visual separation (craftpix top-down sets are the reference), and the game proportions must be right. Plan everything, then do it one step at a time.

This file is the working plan. Claude implements the steps in order on `main`. Each step is verified (checks, play-test, screenshots at 320, 375 and 402 px wide, day and night, zoomed crops, before and after) and pushed before the next one starts. The status column is kept current.

## What the audit found

| Area               | Measured                                                                                                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bridge layering    | Objects are layered by their bottom edge (`y + h`); the companion by its feet. The bridge's bottom edge is below its whole deck, so a crossing companion is always drawn behind it.                                         |
| Outlines           | Share of silhouette edge that is outlined: hut top 33%, stall top 70% and sides 76%, bridge about 70%, bush top 77%, watering can 62 to 79%, bed bottom 64%. Trees, rocks, signpost and lantern are complete.               |
| Separation         | The grass is the most saturated thing in the garden (0.48) while most objects are less saturated (0.34 to 0.43) and darker. Bushes and trees are green on green. Objects sink into the ground instead of standing on it.    |
| Proportions        | The companion is 25 to 29 px wide and 26 to 31 px tall, drawn at world scale. The hut is 50 × 46 px with a 10 × 14 px door: the companion is twice the door's height and 60% of the whole house. Trees are only 46 px tall. |
| Characters         | The Roamling (the starter) is green on green: ears, body, tail and legs share near-identical greens with heavy dithering; eyes are 1 to 2 px. Mossling and Pebbling read better but faces are small and shading noisy.      |
| Text and alignment | HUD stats use three different layouts (icon over number, icon over number, number over bar) that do not share a baseline. Object labels are an unframed translucent box. Two speech bubbles can stack.                      |
| Mission map        | A flat green board with framed cards floating over it; paths end at card edges, a tree sits on the path, the road leaves the map. It does not look like the garden's world.                                                 |
| Game menu          | A sheet of eight equal tiles. It works, but it is not a game menu: no tabs, no character page, no sense of place.                                                                                                           |

## Targets

### Grid and proportions

- One tile is 16 px. The garden stays 192 px (12 tiles) wide so it fills a phone in portrait; it gets taller where needed and the camera keeps following the companion.
- Characters and the world share one pixel grid everywhere in the world: one sprite pixel is one world pixel.
- Reference sizes (width × height, px):

| Thing                              | Size                                   | Why                                               |
| ---------------------------------- | -------------------------------------- | ------------------------------------------------- |
| Companion and visitors             | 24 × 24 canvas, about 18 to 20 visible | readable at 2× on a phone (about 40 px)           |
| Hut door                           | 12 × 20                                | taller than the companion                         |
| Hut                                | about 72 × 64                          | a home, about three companions tall               |
| Stall                              | about 60 × 52                          | a market stall with a counter at companion height |
| Broadleaf tree / small tree / pine | 44 × 60 / 32 × 44 / 26 × 50            | trees tower over the companion                    |
| Bush / rock                        | 22 × 16 / 14 × 10                      | below companion height                            |
| Bench (reading nook)               | 30 × 20                                | the companion fits on it                          |
| Lantern / mailbox / signpost       | 10 × 28 / 12 × 22 / 20 × 26            | posts are taller than the companion               |
| Watering can / bowl                | 12 × 10 / 12 × 6                       | small hand props                                  |
| Path / bridge deck                 | ≥ 24 wide / 32 wide                    | the companion fits with room on both sides        |

### Visual separation (figure and ground)

- Ground is calm: grass saturation ≤ 0.35, luminance 0.52 to 0.62, little texture contrast, sparse tufts.
- Everything that stands on the ground is louder than the ground: a complete 1 px dark outline, a 3 to 4 tone ramp lit from the upper left, a cast shadow down and to the right, and a contact shadow at its base.
- Foliage is a different green from the grass (deeper and cooler, with warm highlights), never the same hue and value.
- Terrain changes have a border: a darker rim where grass meets a path or soil, a light bank and darker edge at water.
- Characters have the strongest contrast in the scene and a small ground shadow.
- These are measured in an art check, not just eyeballed: ground saturation and texture limits, outline coverage ≥ 95% on every sprite edge, objects more saturated than the ground.

### Characters

- A clear, unique silhouette per species and visitor, readable at 1×.
- One outline colour, 3 tones per material, no dithering on bodies.
- Faces read first: eyes 2 × 3 px with a highlight, a lighter face patch or muzzle, cheeks.
- Parts are separated by value, not just outline: ears, body, legs and tail never share one tone.
- Hats and accessories have their own outline and colour.

### Type and alignment

- Pixelify Sans for all text; Press Start 2P only for big numbers and titles (16 px and above).
- Five text styles: Title 20/28, Heading 16/24, Body 14/20, Label 12/16 (bold capitals), Caption 11/16. Line heights are multiples of 4.
- Content starts at the frame's inner padding (3 units) everywhere, so left edges line up. Single-line labels are centred by setting the line height to the box height. An icon and its value share one centre line. Numbers in stat rows are right-aligned.

### Game menu (after Stardew Valley's tabbed menu, in NapAttack's palette)

- A wooden outer frame with a parchment inner panel. A row of icon tabs across the top (Companion, Bag, Journal, Garden, Rhythm, Settings); the active tab is raised and joins the panel. A close button in the corner, plus Escape and Back.
- The Companion page: a framed portrait standing in a small garden scene, name, family and level, and stat rows (mood, growth to the next level, play time, rest today) with segmented pixel bars and an icon on the left of each.
- The Bag page is a grid of inset card slots with counts; tapping one shows its details. The other pages reuse the existing content inside the same frame.

## Steps

| #   | Step                            | What changes                                                                                                                                                                                                               | Done when                                                                                                                        | Status  |
| --- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------- |
| 1   | Ground layer for flat objects   | The bridge (and any flat, walkable object) is drawn in the ground layer, below characters. The generator marks such objects `flat`.                                                                                        | A garden check places the companion on the bridge deck and asserts it draws above; a browser crossing shows the whole companion. | planned |
| 2   | Complete outlines               | A shared `outline` pass in `scripts/art/style.py` closes every sprite's silhouette; the generators use it for the garden, meadow, mission worlds and battle props.                                                         | Art check: every sprite ≥ 95% outlined on each side. Zoomed crops of hut, stall, bushes, bridge and props.                       | planned |
| 3   | One speech and label style      | Object labels and speech bubbles use the same pixel frame; only one bubble shows at a time (tips wait for the companion line, or replace it).                                                                              | No stacked bubbles in a play-test; labels framed; text sits on the inner padding.                                                | planned |
| 4   | Type and alignment system       | Text style tokens in one module; the HUD stats become one row of icon-and-value chips; panels and buttons use the tokens and padding rules.                                                                                | Screenshots at 320 and 402 px with a grid overlay show shared left edges and centre lines.                                       | planned |
| 5   | Proportions and garden rebuild  | New sizes from the table; a re-laid-out garden (taller map, wider path, bigger hut, stall and trees); characters drawn at world pixel scale.                                                                               | Measured sizes match the table (art check). The garden harness passes with geometry from the new map. Before/after screenshots.  | planned |
| 6   | Visual separation in the garden | Calmer ground, distinct foliage greens, consistent cast and contact shadows, terrain rims and water banks.                                                                                                                 | Art check thresholds pass. Before/after at day and night.                                                                        | planned |
| 7   | The same rules in every world   | Mission worlds, the battle backdrop and scene vignettes follow steps 2, 5 and 6.                                                                                                                                           | Art check covers them; screenshots of each world.                                                                                | planned |
| 8   | Characters                      | The three companions (three stages each), nine visitors and Dave are redrawn on a 24 px canvas with the character rules; all places that draw them use integer scales of 24.                                               | A readability sheet at 1× and 2× on grass and on paper; screenshots of garden, HUD, battle, nap, journal and picker.             | planned |
| 9   | Game menu                       | The tabbed menu replaces the tile sheet: wooden frame, icon tabs, Companion page with stat bars, Bag page with card slots, other pages in the same frame.                                                                  | Play-test every tab, keyboard and Back; menu screenshots at 320 and 402 px.                                                      | planned |
| 10  | The mission map as a place      | A generated map in the world style: the garden gate at the bottom, a road branching to the park, library and mountain cabin, landmarks drawn in the scene, names on signposts, the companion standing at the chosen place. | No floating cards; paths meet landmarks; a play-test from map to mission and back.                                               | planned |
| 11  | Shop and Arena as places        | Ask Matt first: the inside of Moss's stall for the Shop, a clearing beyond the fence for the Arena.                                                                                                                        | Matt's go-ahead.                                                                                                                 | ask     |

## Testing the visuals (every step)

- Screenshot suite in a desktop browser at 320 × 640, 375 × 667 and 402 × 874, day and night, with zoomed 3× crops of anything changed, compared before and after.
- The art check (`npm run check:art`) gains the measured rules above, so regressions fail the build.
- Nothing here is claimed as tested on a phone until Matt or a device check confirms it.

## Working with Codex

While a step is in progress Claude owns its files (mostly `scripts/art/*`, `assets/*`, `components/garden-world.tsx`, `components/game-hud.tsx`, `components/game-menus.tsx` and `components/pixel-frame.tsx`). Codex: please review and test landed steps, or work on files outside the current step, and avoid editing those files until the step's status reads done.
