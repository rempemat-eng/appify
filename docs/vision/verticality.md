# Verticality and dense streets

Matt, 19 Oct 21:59: "let one of the agents figure out how you can implement such immersion and verticality and different buildings being next to each other". He sent screenshots of Eastward (subway stairs and terraces, forest ledges, a wall of dense facades, a plaza with stairs at dusk, a market plaza) and Stardew Valley (the farmhouse on a raised yard with a plank retaining wall and steps down to the crops).

This file says what those screens do, why ours read flat and sparse, and how to build the same within our engine: a shared terrace toolkit, a facade composer, a foreground layer and ground wear, then where each lane applies them first. It builds on `research/placement-paths-verticality.md` (sourced research, not repeated here), `two-level-walk.md` (decks) and `world-rules.md` (section 2a, Height). The screenshots stay out of the repo (third-party art); they are described in words.

## 1. What the references show

Measured on the screenshots against the characters' height (one "body"):

- **Ground at three heights on one screen.** The subway screens show an upper street with shopfronts, a retaining wall, a lower plaza, and a railing over a further drop at the bottom. The wall face is about **1.8 bodies** tall. Its top carries a lit coping and a railing of short posts; its foot is a dark wet band, and the lower ground is darker for a few pixels below it.
- **The wall face is a surface with things on it.** Concrete in courses, a big painted mural (a skull and a sun), pipes, a drain with a stain, moss and grass breaking out of the foot, posters, a vent. Nothing on it is noise: each mark is an object.
- **Wide stairs cut through the wall.** About **3 bodies wide**, treads about a fifth of a body, a cheek wall each side with a lit top, a post in the middle. The railing stops at the stair head. A second, narrower stair runs diagonally down the face at the side.
- **A tunnel mouth set into the face.** The subway entrance is a small building on the lower tier with its back against the wall, its roof level with the upper street, a sign over the door and a dark mouth with steps going down.
- **Buildings at different depths overlap.** Lower-tier buildings rise in front of the wall and the upper street; upper-tier buildings stand behind. The overlap itself is the depth cue.
- **Street walls of distinct buildings.** In the dense-facade screen almost the whole frame is facade: buildings of different widths and heights share party walls, with a pitched roof beside a flat one, set-backs, balconies, AC units, big painted signs, blade signs, shutters and roof gardens. Very little ground is visible and none of it is empty.
- **Foreground.** Utility poles with wires and a black silhouette pole at the bottom edge at dusk, railing tops and dry grass drawn over the lower edge of the screen.
- **Ground detail from use.** Chequered plaza tiles, worn patches, puddles, dry grass at wall feet, litter by stalls.
- **Natural ledges (forest).** Earth banks with a grass lip that overhangs, roots and a dark brown face, timber plank stairs set into the bank, a boardwalk bridge on posts over water.
- **Stardew farmhouse.** The house stands on a porch about half a body above its yard; the yard is held up by a plank retaining wall with a fence along its top, and a narrow stair runs down to the crops between stone edgings.

Pixpil describe the goal in their own words: "Strong colors, various buildings and objects, rich and subtle details", and "we wanted to make it look lively because people are still living there"; the city grew from "a weird monster dormitory building resembling Hong Kong's Kowloon Walled City" ([Game Developer, Road to the IGF: Eastward](https://www.gamedeveloper.com/disciplines/road-to-the-igf-pixpil-s-i-eastward-i-)). Stardew's maps have a **Front** layer "drawn on top of the player if the player is North of them" and an **AlwaysFront** layer of "objects that are always drawn on top of other layers as well as the player", used for foliage cover ([Stardew Valley Wiki, Mapping](https://wiki.stardewvalley.net/Mapping)). That is the foreground layer below.

## 2. Where we stand (19 Oct, previews of main)

Our companion's body is 20 x 24 px (`lib/occlusion.ts`), residents about 15 x 26. A phone shows about 300 x 650 art px.

| Measure                    | Eastward reference               | NapAttack now                                                                                                    |
| -------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Wall face per tier         | about 1.8 bodies                 | 18 px in the city and the isles (0.75 bodies), 24 on the ridge, 28 on the gulch mesa                             |
| Stair width                | about 3 bodies, cheeks, mid post | 56 px in the city but laid across a road; 28 px on the isles (about 32 screen px, under the 44 px rule)          |
| Facade share of the screen | most of the frame                | props cover 25 % of Neon Heights, 24 % of Neon, 31 % of Cogsworth Canal, 53 % of Crossroads Town (box area)      |
| Buildings touching         | nearly all                       | none: city buildings stand 2 to 12 px apart on open concrete, valley houses stand alone on grass                 |
| Levels on one screen       | three                            | one, except the Heights corner (two thin rims) and the isles' ledges                                             |
| Foreground over the walker | poles, wires, railings, grass    | only overhead props (cables, bunting), and railings painted into the ground, so the companion is drawn over them |
| Shadow at a wall's foot    | strong, a few px                 | 0 to 3 px                                                                                                        |
| Ground                     | worn, tiled, wet, littered       | uniform fills; the lower half of Neon Heights is empty concrete                                                  |

Why ours read flat: the faces are shorter than the companion, so a drop reads as a kerb; buildings float on open ground, so nothing overlaps; nothing stands between the camera and the walker; the ground is the same everywhere. Why sparse: blocks are sized for roads, not for people, and every building is a free-standing sprite with a margin.

## 3. The engine model we keep

- **Tiers are ground, not levels.** A tier is ground drawn higher on screen, separated from the next by a blocked face band and joined by stair cells. It needs no second walk level, no links and no level switch: walking up a stair simply moves the companion up the screen. The two-level walk (`two-level-walk.md`) stays for decks, with one rule to choose: **if anything walks under it, it is a deck; if not, it is a tier.** Skybridges and walkways over a street are decks; terraces, porches, boardwalks against a building and quays are tiers.
- **The renderer sorts by foot y.** A building on a lower tier whose sprite rises over the upper tier is drawn over the upper tier's ground and over a companion walking there (the `Ghost` outline shows it). That is the overlap Eastward uses, and we get it for free.
- **One ground image per zone** (art-style.md, memory). Faces, stairs, murals, drains and wear are painted into it. What must pass in front of the companion (railings, poles, wires, leaves) is a prop or the foreground layer.

## 4. The design

### a. The terrace toolkit (`scripts/art/terrace.py`, Claude A)

Every region's generator calls it instead of drawing its own cliffs. It replaces the city's `_terrace_faces`, the isles' face code, the ridge's and frost's ledges, the gulch mesa's face and `cliff()` in `valley_zones.py` (each owner switches its own file once the toolkit lands).

**Tier map.** A zone function returns, beside its ground, a `tiers` spec: rims as polylines with a tier number on each side, or a per-pixel tier array for natural shapes. `build()` derives the face bands, records a per-cell tier layer (`zoneTier` in `lib/zone-maps.ts`, run-length encoded like `walk`, digits for tiers, `f` for a face, `s` for a stair) and blocks the faces.

**Sizes** (zone px; the companion is 24 tall, 20 wide; 44 screen px is 33 art px at 1.33 px each):

| Part                                        | Size                                                                                                                                      | Walk grid                                                                 |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Tier face, city                             | **40** (1.7 bodies, Eastward's ratio)                                                                                                     | 10 blocked rows                                                           |
| Tier face, valley, isles, west, garden yard | **32** (1.3 bodies)                                                                                                                       | 8 blocked rows                                                            |
| Low step: porch, boardwalk, kerb terrace    | **12 to 16**                                                                                                                              | 3 to 4 blocked rows                                                       |
| Per zone                                    | at most two full tiers and one low step on screen; faces at most a quarter of the zone's height                                           |                                                                           |
| Coping or lip                               | 4: lit top, lit front, mid, dark drip line. Earth: a 2 to 3 px grass overhang, roots in the first 6 px                                    | part of the face                                                          |
| Dark foot                                   | 4 on the face (wet, weed)                                                                                                                 | part of the face                                                          |
| Cast shadow on the lower tier               | 8: 2 strong, 3 medium, 3 dithered; a down-right wedge off each east end and stair cheek (3 px plus 1 per 3 rows)                          | ground stays walkable                                                     |
| Stairs, open width                          | **at least 34** (44 screen px); 40 standard (48 with cheeks), 64 to 96 grand with a centre rail                                           | stair cells `s` through the face                                          |
| Treads                                      | 4 per step: lit nose, two tread rows, dark riser; worn treads in the middle                                                               |                                                                           |
| Cheeks                                      | 4 to 6 each side, lit cap on the west cheek, shaded east cheek; the west cheek shades the first treads                                    | blocked                                                                   |
| Landings                                    | 8 deep (2 cells) clear at the top and the bottom; a mid landing of 8 for rises over 40; a tactile strip at city stair heads               | open, no props                                                            |
| Ramp                                        | runs along the face, rise 1 in 3, at least 24 wide, rail on its open side                                                                 | open cells, tier changes along it                                         |
| Railing                                     | a 9 px sprite: top rail lit, posts every 6 px, standing on the coping; open over a stair plus 2 px each side, with a newel post each side | blocks the one cell row behind the rim                                    |
| Tunnel or subway mouth                      | needs a face of 32 or more: opening 28 to 40 wide, 24 to 28 tall (a body plus 2), surround 4 to 5, sign on the coping, apron 12 deep      | blocked; declared as a door (`MOUTHS`) so `door-shut-in` checks its apron |
| Porch or deck                               | 12 to 16 high, 3 to 4 treads, steps at least 34 open, corner posts, rail on open sides                                                    | low step tier                                                             |

**Face materials**, each a function with the same signature (`face(cv, rim, height, material, x0, x1, seed)`), lit from the upper left, four or five tones from one ramp in `art/materials.json`:

- `concrete`: 8 px courses, a joint every 20 px offset per course, rain streaks from the coping, moss on ledges.
- `brick`: 3 px courses in stretcher bond, a soldier course under the coping, white bloom near the foot.
- `stone`: dressed blocks in 6 px courses of varied length, each lit on top (Cainos detail target).
- `rock`: today's `cliff()` (irregular stacked blocks), for natural faces.
- `earth`: banded soil, a grass lip breaking over the edge, roots and stones in the face, no courses.
- `timber`: 4 px planks on posts every 16 to 24 px, nail heads, the Stardew yard wall.
- `sandstone`: strata of 3 to 7 px, each lit on its upper edge (the mesa).

**Decorations** placed on a face by name, so zones say what, not how: `mural(x0, x1, palette, motif)`, `drain(x)` (outlet, stain, puddle below), `pipe(x, run)`, `vent(x)`, `poster(x)`, `moss(density)`, `roots(density)`, `outfall(x)` (an arch with a trickle and a gully across the path below), `ladder(x)`. Stairs, ramps, railings, tunnel mouths and porches are functions too: `stairs(x0, w, rim, height, material)`, `ramp(...)`, `rail_segments(rim, gaps, material)`, `mouth(x, w, h, sign)`, `porch(box, height, steps_at)`.

**Railings are props.** A railing along a rim must cover the feet of a companion standing behind it, so the toolkit emits it as 16 px segment sprites (a few shared keys per material, placement `edge`) sorted by foot y, not painted into the ground.

**Lint** (`world_lint.py`, from the research's tier tests):

- `tier-step`: walkable neighbours on different tiers both lie on stair or ramp cells.
- `one-tier`: a building's foot band lies on one tier, and its door apron on the same tier.
- `stair-ends`: both landings are open, clear of props, and reach a path to a node.
- `stair-width`: open width at least 34 px.
- `face-height`: a face is at least 24 px, or 12 to 16 for a declared low step; nothing in between (it reads as neither).
- `rail-at-edge`: every rim run of a built face has railing segments or a declared parapet, except over stairs; natural banks are exempt.
- `upper-hidden`: no stand, door apron or tap target on an upper tier lies under a lower-tier sprite's box, and no walkable upper ground is hidden for more than 40 px of depth (the deck rule).
- `tier-seam`: a rim that reaches a zone border continues in the neighbour at the same row and face height (extends check 10).

**Existing helpers.** `decks.py` keeps drawing decks; its railing and post code moves into the toolkit so decks and tiers share one look. The city's `TERRACES` and `TERRACE_STAIRS` become a `tiers` spec; their 18 px faces grow to 40 and their stairs move off the road onto their own landings.

### b. Street walls (`scripts/art/facades.py`, Claude A)

A composer that fills a frontage (`street_wall(x0, x1, foot, district, seed)`) with distinct buildings side by side and returns props plus the details derived from their neighbours.

- **Bays from parts.** Each building picks a width class (narrow 32 to 40, mid 48 to 64, wide 72 to 96), storeys (district caps: valley 1 to 2, Cogsworth 2 to 4, city 2 to 8), a roof (flat parapet with roof clutter, gable to the street, gable side-on, hipped, mansard), a wall material (brick, plaster, tile, timber, concrete, glass), a ground floor (shop, cafe, house door, workshop, garage, lobby, stall front) and extras (blade sign, AC units, balconies, awning, shutters, plants, washing, fire escape, downpipes). The city's `building()` is the first bay type; the valley's cottages become bays too (Claude B, B6 library).
- **No two alike** (world-rules rule 8, "no rows of identical props"). Neighbours never share material, roof and storeys all at once; the same width class at most twice in a row; roof lines differ by at least 8 px between neighbours; a set-back of 4 or 8 px on at most one building in three.
- **Party walls.** Neighbours touch with no gap; the taller one owns the shared outline column. A taller west neighbour shades the lower one's roof down and to the right; a building set forward shows a 2 to 3 px side return and shades the one set back. These shadows are derived, never placed by hand.
- **Doors and taps.** Each bay declares its door positions (the `DOORS` table, per bay). A bay with a tap target is at least 34 px wide so its hit area meets 44 screen px; narrower bays are scenery. Every door keeps its apron (`door-shut-in`).
- **Backs and passages.** A continuous wall closes the land behind it. The prototype showed this: the ground behind a row is unreachable. So either the land behind is declared closed (yards, the next zone's backs), or the row has a passage (an alley at least 12 px wide, an arcade or a gate) every 120 to 200 px. Lint `row-closure` checks it.
- **Prop or ground.** Buildings, railings, poles, lamps, stalls and signs on posts are props. Faces, stairs, murals, drains, kerbs, wear and puddles are ground. Wires, hanging signs and leaves over the edge are the foreground layer.
- **Depth.** A building sorts by its foot. A lower-tier building may rise over the upper tier where the ground it covers is closed or at most 24 px deep (`upper-hidden`). Tall buildings stand north of their street (two-level-walk rule 6). A building whose roof rises over a north border needs empty ground behind it (`check_overhangs`), and `zoneReach` keeps its zone mounted while any part shows.

### c. Immersion layers

**Foreground layer (renderer, Claude A).** Each zone may have `fore.png` (transparent, zone-sized, exported as `zoneFore`), drawn as the last child of the camera view, above every actor including those on decks, under the hit and bubble layer, with `pointerEvents="none"`. It carries wires and lantern strings between declared anchors, hanging signs, washing lines, and leaves or grass over a zone's south edge from plants beyond it. Rules:

- Anchors are drawn things (a pole, a bracket, a wall); `overhead` props move here over time.
- Its pieces declare boxes; `hiddenBehind` counts them as always in front, so the `Ghost` outline shows when they cover 40 % of the body. Lint `fore-cover`: no walkable cell is covered more than that except in the zone's last 16 px.
- No parallax for now (one image, no extra motion). Leaves may sway only with motion allowed and the screen active, a finite loop on the shared clock.

**Ground wear from use.** The path pass (research section 2.2) writes `traffic`; until it exists, a breadth-first count between a zone's stands and exits stands in. Wear is drawn on the material's own grid (a sett one tone up, grass thinned to dirt along a desire line), never as a soft blend, which reads as smoke (the prototype's first try). Puddles go in hollows: at wall feet under drains, by kerbs. Litter only where people stop (bins, stalls, stair feet, benches), two or three flecks. Setts, flags and tiles change at tier boundaries, so each tier has its own surface and tone (upper a step lighter, as decks do).

**Ambient life**, all decorative, no rewards, no chores: a drip from an AC unit, steam from a vent, pigeons that lift when the companion walks close and settle again, a flickering sign letter, a cat on a wall top. Each is a finite loop on the shared clock, still with reduced motion, stopped when the screen is inactive (AGENTS.md). At most a handful of live elements per screen (art-style.md, Eastward limits).

### d. Where to apply it first

Region coordinates are region pixels (the zone grid in `zones.py` `LAYOUT`, 320 x 576 per zone).

| Lane                  | Place                                                                                                                                                                                                                                                      | Zone, approx region px                                                                  |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **C**, Neon           | Heights: the two terrace rims grow from 18 to 40 px faces in concrete, the stairs leave the road for their own landings, houses on each terrace touch as street walls                                                                                      | `heights`, x 0 to 300, y 140 to 280                                                     |
| C, Neon               | A sunken plaza one tier below Hill Street's south pavement where the Heights' lower half is empty concrete now, entered by wide stairs and a **subway mouth** in the wall under the pavement, with a mural                                                 | `heights`, x 20 to 300, y 330 to 560                                                    |
| C, Neon               | The **market plaza**: the market street's stalls move into a square a low step below the street, with stalls against the facades, chequered setts and a lantern string                                                                                     | `market`, x 160 to 470, y 860 to 960                                                    |
| C, Cogsworth          | **Canal embankments**: the canal and its towpaths sink half a tier (16 px brick face) below the streets, stairs at both bridge ends, outfalls with trickles, the bridge on abutments                                                                       | `canal`, x 0 to 320, y 740 to 830                                                       |
| **E**, valley         | **Crossroads Town street walls**: the houses north of the square become a terrace of touching cottages of different widths and roofs, with a passage to the backs                                                                                          | `town`, x 330 to 620, y 2470 to 2560                                                    |
| E, valley             | **Harbour quay steps**: a 32 px dressed-stone quay face with steps down to the water and the jetty, bollards and rings on the coping                                                                                                                       | `harbour`, x 340 to 620, y 3260 to 3340                                                 |
| E, valley             | **Woodland ledges**: earth banks with grass lips and roots, timber plank stairs where the path climbs, a boardwalk on posts over the spring's runoff                                                                                                       | `woodland`, x 0 to 320, y 1900 to 2100                                                  |
| **B**, garden         | **The hut on a raised yard**, like the Stardew farmhouse: a 12 to 16 px yard held by a timber wall with a fence on top, a porch at the door, steps (at least 34 px open) down to the path and the beds; every garden prop keeps its stand and 44 px target | `garden` (home hub), hut at x 339 to 437, y 1755 to 1849; yard edge near y 1856 to 1872 |
| **D**, Sunstone Reach | **Gulch boardwalk**: the boardwalks in front of the saloon and store become a 12 px timber low step with a rail and steps at each door and end                                                                                                             | `gulch`, x 400 to 600, y 1260 to 1420                                                   |
| D                     | **Mesa ledges**: the mesa face grows to 40 px sandstone strata with a ledge path and a ramp to the mine mouth (a tunnel mouth)                                                                                                                             | `gulch`, x 546 to 626, y 1240 to 1290                                                   |
| **C**, isles          | **Coastal terraces**: the Landing's terraced slope to the lagoon in earth and rock with timber stairs; the ledge stairs widen from 28 to at least 44 px (34 open)                                                                                          | `landing` and `cove`, x 100 to 600, y 540 to 700                                        |

Each lane edits only its own files (coherence-plan, "Who does what"); new bay types and porch or stair props go through Claude B's library where they are props.

### e. Order of work and acceptance

1. **Claude A: the toolkit.** `terrace.py` (faces by material, decorations, stairs, ramps, rail segments, mouths, porches), the `tiers` spec in `build()`, `zoneTier` in `lib/zone-maps.ts`, and the lint checks above (as a report first, then strict). Nothing changes in any zone yet.
2. **Claude A: the renderer.** The foreground layer (`fore.png`, `zoneFore`, drawn last, counted by `hiddenBehind`), rail segment sprites in the y-sort, and a source test that the fore layer never takes taps.
3. **Claude A: the composer.** `facades.py`, with the city's `building()` as its first bay type and the `row-closure` check.
4. **Pilot, Claude C with Claude A.** Neon Heights (both rims, the sunken plaza, the subway mouth), compared side by side with the prototype and the references before anything else changes.
5. **Each lane's first place**, in the order of the table above, one PR each.

Acceptance for every step:

- The zone preview at 2x and a 300 px wide crop at 3x (what a 402 x 874 phone shows), checked by eye against the references and the prototype.
- `world_lint` clean, strict, including the new checks.
- A Playwright walk at 402 x 874: up and down every stair, along every rail (the rail covers the feet), behind every lower-tier building that rises over an upper tier (the outline shows), a tap on the upper tier from below (the walk goes by the stairs), with reduced motion and at night.
- `npm run verify` and `npm run check:art-repro` pass before a PR leaves draft.

## 5. The prototype

A standalone mock (not game art) was drawn with the repo's palette, `Canvas`, `style.finalize`, the city's `building()` and street props and the companion sprite: a Neon "stair street" with an upper street of six touching buildings (one with a pitched roof), a 40 px concrete wall with a mural, a drain, a pipe, a vent and a subway mouth, 48 px stairs with cheeks and a centre rail, two lower-tier buildings rising against the wall, a plaza of setts with a market corner, a 32 px dressed-stone embankment with railing, stairs and outfalls, a brick towpath and the canal, wires and leaves in a foreground layer. Its walk grid checks reach every stand from the towpath, no tier step outside stairs, and both stairs at least 44 screen px wide. Three iterations fixed what read wrong: a wall face as dark as the plaza below it (lightened, stronger foot shadow), wear drawn as a soft blend (now on the sett grid), stairs too narrow for a thumb (widened), and a towpath in the wall's own stone. It also found the row-closure issue in (b). The images live in the study's scratchpad, not in the repo.

## 6. Open questions for Matt

1. **Tier height.** 40 px faces in the city (close to Eastward) and 32 px elsewhere: right, or should the valley stay gentler?
2. **How many heights per screen.** The prototype shows three (upper street, plaza, towpath). Is that the density you want, or two?
3. **Foreground over the companion.** May leaves, poles and wires cover the companion for a moment (its outline shows), or should the bottom edge always stay clear?
4. **Denser city.** The city's open concrete blocks would become continuous street walls with passages, which changes Claude C's layout. Go ahead?
5. **The subway mouth.** Decorative for now, or the door of a later metro between city zones (a new mechanic, so not before the polish is done)?
6. **The home garden on a raised yard.** The hut on a porch and yard with steps down to the beds, as in Stardew: shall Claude B redraw the garden's ground for it?
