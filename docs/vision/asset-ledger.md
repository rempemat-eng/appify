# Asset ledger: which old art may go into the new world

Matt, 20 Oct 20:04, on a patched Summit: "there is so much wrong with this. non of this looks natural (given the soft grid), there is no verticality, hard edges, the mountains could use some improvement". 20:16: "can u make sure no old assets are reused that dont fit the soft grid, level of detail etc. established for the newest version".

So every picture the game ships (everything under `assets/`, 996 files) is listed in `scripts/art/asset_ledger.json` with a grade, the numbers it was graded on, the checks it fails, its generator and its owner lane. `npm run check:assets` (`scripts/check-assets.cjs`) fails when a picture is missing from the ledger or when a region build uses anything that is not KEEP. AGENTS.md ("Keep the design coherent") makes this the rule for every lane.

Status: built by Claude A on 20 Oct, main at 74dea48. The check runs on its own and is not yet part of `npm run verify` (section 7 says when and how it joins).

## 1. The grades

| Grade  | Meaning                                                                                                                                                                                                     |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| KEEP   | Fits the newest standard on every check in section 2. A kit or region build may use it as it is.                                                                                                            |
| REWORK | The subject stays in the new world; the art is redone first. The entry's `fix` says how much: `redraw` (a new drawing), `repaint` (the same drawing on the house ramps), `outline` (the outline step only). |
| RETIRE | The picture has no place in the new world: old zone ground and scenery (the regions are rebuilt over them), sprites the prop audit dropped, pictures an open PR removes.                                    |

When in doubt the grade is REWORK: a check that cannot be measured counts only if someone has checked it by eye (section 6), never by default.

## 2. What is measured on a sprite

Every sprite (props, buildings, residents, garden and decor sprites, growth stages, journey vehicles, mission props) is brought back to its native pixel grid (the PNGs are saved at 4x) and measured with the tools of the newest standard, all of which this branch carries (section 8):

| Check | Tool and source                                                                                                                                                          | Passes when                                                                                                                                                                                                                                                                                                           |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| grid  | The soft grid (`verticality.md` 4f, `research/soft-grid.md` 6.3, `size-guide.md` 1): built things span whole 8 px cells; vegetation, people, animals and parts are free. | The foot line (the sprite's lowest 4 rows) is 8n px wide, or 8n + 1 or 8n + 2 with its outline, or 8n - 1. No module declares `FOOT` yet, so this reads the pixels; once modules declare it, the declaration is checked instead.                                                                                      |
| size  | `size_check.py` and `size_guide.json` (PR #124)                                                                                                                          | The drawn box (pixels at least half opaque) is inside its kind's height and width ranges, with 2 px for the outline, in every frame.                                                                                                                                                                                  |
| bar   | `detail_bar.py` and `detail_baselines.json` (PR #90), with the house rulings (`house-style.md` 7, 20 Oct 17:30)                                                          | On the largest fully opaque square inside the sprite (the outline ring left out, at most 96 px), against the reference kind for what it is (tree, facade, wood front, stone wall, machinery): tones at 85 % when ramp-built (90 % otherwise), shapes and dressing at 90 %, both cleanliness tests.                    |
| style | `style_lint.py`, `house_palette.py`, `art/house-palette.json` (PR #121)                                                                                                  | At least 90 % of pixels on the house palette, or on today's shared ramps (which the one decided recolour, house-style migration step 2, maps onto it); at most 64 colours (128 over 2,500 px); outline dark, in the material's edge tone, not doubled; lit from the west; lone pixels at most 6 %; no checker dither. |
| logic | The prop audit (`prop-logic.md` 10, PR #97): 412 sprites graded by eye on 20 Oct                                                                                         | KEEP in the audit. ADJUST and REDRAW are faults; a sprite changed since the audit is marked "re-check" and still fails until someone checks the fault by eye. DROP retires. A sprite not in the audit fails until it is checked by eye.                                                                               |

**Where the bar cannot measure.** A sprite with no solid 18 px square (a crate, a lamp, a resident) cannot hold one 16 px patch, and cloth, animals and people have no baseline (house-style 7: "judged by eye"). Their detail counts only if the prop audit passed them by eye and they have not changed since; otherwise they fail as "detail unverified". Open structures (masts, cranes, fences) are measured on their largest solid part, as the ruling says.

**Pictures that are not sprites** (grounds, scenery, journey and battle layers, scenes, mission worlds) get cleanliness and palette numbers (colours, share on today's ramps, lone pixels, checker dither) and the rule for their class:

- **Old zone ground and data** (`assets/zones/<zone>/ground.png`, `top.png`, `map.png`, `flow.png`, 35 zones): **RETIRE by rule.** They were painted before the soft grid: no tiers with south faces and side bands. The regions are rebuilt on the soft grid from the briefs (`docs/vision/regions/`, PR #96) with the kits. Each entry keeps the brief's verdict on the place (`kept, placed`, `kept, redrawn`, `replaced by ...`): a kept place is rebuilt where it is, its old picture is not reused. 30 of the 35 grounds also fail the cleanliness numbers (lone pixels up to 18 %, checker dither up to 6 %).
- **Scenery past the zones** (`assets/zones/scenery/*`, `beyond*.png`, 74 pictures): **RETIRE by rule**, for the same reason; the world plan's continent replaces them (lone pixels up to 30 %, checker dither up to 22 %).
- **A zone built with the terrace toolkit** (its function calls `terrace.build`): measured instead of retired, and REWORK until its ground passes the cleanliness checks and its faces, banks and ground are compared with the bar by eye. None is on main (section 4).
- **The garden** (`assets/garden/ground*.png`, `path-flagstones.png`, its water and light overlays, `assets/zones/garden/map.png`): **REWORK**, not retire. The home-valley brief keeps the hub's size, place, geometry and harness, so its picture is redone in place: on the soft grid with tiers, south faces and side bands and the raised yard (`verticality.md` 4d), keeping the geometry and the harness. Lone pixels 10.5 % today.
- **The hut inside** (`zone/home`): REWORK. Its furniture is being redrawn to the size guide in PR #136, and rooms have no indoor baseline for the bar, so they are judged by eye.
- **Journey layers** (sky, far, near, yard of each journey): REWORK. The journeys stay as shortcuts beside the routes (routes brief 9), but the layers were painted in the older style. The space elevator's capsule RETIRES: the rocket replaces it (PR #131).
- **Battle backdrops, scenes, mission worlds and the mission map**: REWORK. They are other screens in the older style (art-style.md: "still use the older style and need the same pass"); not for the world, and not reused anywhere new until redone.
- **The world canvas's tiles** (`assets/world/**`, PR #123 and #126, not on main): RETIRE by a rule in the ledger, because they are cut from the old grounds. A plane is re-graded when its region is rebuilt and its tiles are cut from the new ground.

**Copies.** A garden or mission sprite that is pixel for pixel the same drawing as a zone sprite takes that sprite's verdict (`same_as`): 13 garden copies and 22 mission copies.

## 3. Who owns what

Owners follow the lane table in `coherence-plan.md` ("Who does what"), by generator: A `frost_props`, `zones`, `frost_zones`, `scenery`, `journey`; B `world_props`, `valley_props`, `harbour_props`, `home_props`, `garden_props`, `garden`, `decor`, `home_zones`; C `steampunk_props`, `cyber_props`, `isle_props`, `isle_zones`, `city_zones`; D `western_props`, `caldera_props`, `castle_props`, `space_props`, `sunstone_zones`, `space_zones`; E `valley_zones`. Residents go to the lane of the region they live in (as in the prop audit). `battle.py`, `worlds.py`, `vignettes.py` and `mission_map.py` are not in the table; they fall to Claude A until someone takes them (`owner_note` in the ledger).

## 4. What is already on the soft grid

- **On main: nothing.** No zone on main is built with the terrace toolkit; no prop module declares a footprint.
- **Fir Hollow, PR #104 (head 59dee37):** the only zone on any branch whose ground is built on the soft grid (`terrace.build`: an earth escarpment as a tier edge with south faces, side bands, a stream in grid-led banks and its fall). Measured there with this ledger: REWORK, not yet KEEP. Its ground has 11.1 % lone pixels and 0.9 % checker dither (the house limits are 6 % and none) and 842 colours with 29 % of its pixels on today's ramps; its eight new firs and `bench_west` are not in the size guide or the audit yet and fail speckle and palette. When #104 merges, `--redo zone/hollow` measures it as a soft-grid zone instead of retiring it.
- **The kits** on open PRs (the terrace toolkit #90, the house kits #121, E's `river_kit` #133, D's `dry_kit` #137, and the mountain kit pilot to come) draw new art from code; they ship no pictures yet. Whatever they write into `assets/` is measured here before it ships.

## 5. Results (20 Oct, main at 74dea48)

649 entries, 996 files. Entries per lane and grade (REWORK split by its fix):

| Lane    | KEEP   | REWORK (redraw) | REWORK (repaint) | REWORK (outline only) | RETIRE  | Entries | Files   |
| ------- | ------ | --------------- | ---------------- | --------------------- | ------- | ------- | ------- |
| A       | 1      | 95              | 1                | 0                     | 77      | 174     | 198     |
| B       | 5      | 145             | 14               | 0                     | 1       | 165     | 217     |
| C       | 2      | 126             | 7                | 0                     | 16      | 151     | 255     |
| D       | 6      | 104             | 17               | 3                     | 11      | 141     | 222     |
| E       | 0      | 10              | 0                | 0                     | 8       | 18      | 104     |
| **All** | **14** | **480**         | **39**           | **3**                 | **113** | **649** | **996** |

**KEEP (14):** `bush` (and its garden and mission copies), the garden's `rock1`, `mossy_log`, `snowman`, `basalt_stumps_b`, `cooling_vent`, `hitching_rail`, `keg`, `stone_bench`, `trough`, `city_steam`, `steam_puff`. All are small or effects: the audit passed them by eye and every measured check passes. No building, tree, vehicle or resident passes today.

Checks failed by REWORK entries, per lane (an entry can fail several):

| Lane | logic | size | grid | bar | detail unverified | speckle | dither | light from the west | colours | palette | doubled outline | light outline | old style (pictures) | soft grid (pictures) |
| ---- | ----- | ---- | ---- | --- | ----------------- | ------- | ------ | ------------------- | ------- | ------- | --------------- | ------------- | -------------------- | -------------------- |
| A    | 27    | 4    | 11   | 11  | 22                | 34      | 21     | 6                   | 0       | 61      | 2               | 0             | 56                   | 0                    |
| B    | 89    | 20   | 38   | 45  | 57                | 74      | 4      | 24                  | 0       | 113     | 14              | 0             | 0                    | 10                   |
| C    | 75    | 31   | 42   | 51  | 26                | 40      | 3      | 31                  | 32      | 114     | 14              | 4             | 0                    | 0                    |
| D    | 26    | 2    | 34   | 26  | 23                | 55      | 4      | 11                  | 11      | 78      | 12              | 1             | 0                    | 0                    |
| E    | 0     | 0    | 0    | 0   | 0                 | 10      | 0      | 4                   | 0       | 10      | 6               | 0             | 0                    | 0                    |

What the numbers say: palette is the most common miss (art drawn with local colours on neither the house palette nor today's ramps; C's RGB facades run to 518 colours a sprite); then speckle (lone pixels over 6 %, in B's valley props, D's Reach and every resident); then the prop audit's open faults; then the bar, where buildings and trees fall short on tones (B's oak 7.3 of 20.4 a patch, the cottage 18.1 of 25.6) while D's keep, gatehouse, saloon and hab hub pass it and fail elsewhere.

**The worst five per lane** (by how many checks fail and how far):

- **A:** `bothy` (door 23, flat roof snow, bar tones low), `pennant` (flat flag on a stick, foot off the grid, detail unchecked), `windsock` (57 wide for a pole, detail unchecked), `ibex` (on a grey disc, 36 x 36 against 26 x 30), `warden` (speckle, light from the east, palette, doubled outline). Besides these and its other 7 world sprites and residents, A's 84 REWORK entries are the old screens: journey layers and vehicles, battle, scenes, mission worlds.
- **B:** the hut's `bed`, `wardrobe`, `armchair`, `bookcase` and `desk` (four of them a third to a half over the size guide, flat slabs, bar low on all three counts; PR #136 is redrawing them), then `water_mill`, `windmill`, `sailboat`, `barn`.
- **C:** `maglev` (pure side view, 25 tall for a tram's 44 to 58), `city_lighthouse` (small door, foot off the grid), `airship_mast` (side-on envelope), `narrowboat` (speckle, dither, light from the east), `city_tram` (side view, 40 tall); then the 32 city blocks (`city_b0` to `city_b31`, the audit's largest REDRAW: storeys off the table, up to 518 colours).
- **D:** `wagon` (side view, flat wheels), `sleep_pod` (bar low, noisy), `bathhouse` (door 28), `glass_dome` (over the size guide, glazing lines only), `aquarium_column` (speckle, dither).
- **E:** owns no sprites; its ten residents all fail speckle and palette (`baker`, `gardener` worst: also light from the east and doubled outlines).

**What each lane must redo before its region is built.** The full lists, worst first, are printed by `python3 scripts/art/asset_ledger.py --lanes` and were posted to each lane on the crew board. In short:

| Lane | Its own art to redo                                                                                                                                                                              | Placed today in its region's zones and not KEEP                                                                             |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| A    | 95 redraw (10 of them placed in zones: the Frostline's and the square's props), 1 repaint; 77 retire (71 scenery pictures, the four Frostline grounds, the capsule, the mission copy of `stone`) | (routes have no zones today)                                                                                                |
| B    | 145 redraw (97 placed in zones), 14 repaint; `stone` retires                                                                                                                                     | the hut: all 17 furniture sprites                                                                                           |
| C    | 126 redraw (115 placed), 7 repaint; 15 grounds and `glass_screen` retire                                                                                                                         | 127 of the 131 sprites its places use: 123 its own, 3 of B's (`driftwood`, `fern`, `heron`), 1 of D's                       |
| D    | 104 redraw (95 placed), 17 repaint, 3 outline only; 8 grounds and 3 beyond pictures retire                                                                                                       | 116 of 123: 115 its own, 1 of A's (`telescope`)                                                                             |
| E    | 10 residents redraw; 8 grounds retire                                                                                                                                                            | 97 of 100: 86 of B's (cottages, trees, animals, mills, the harbour's props), 10 of A's (`well`, `ring_post`, ...), 1 of D's |

## 6. Using the ledger

- **After a redraw:** regenerate the art as usual, then `python3 scripts/art/asset_ledger.py --redo prop/<name> ...` (entry ids or file paths) and commit the ledger with the art. A full rebuild is `--build` (about 40 s); the prop audit is read from `docs/vision/prop-logic.md` when that file exists, otherwise the audit verdicts already in the ledger are kept.
- **A by-eye verdict** goes into the entry's `eye` field and survives every rebuild: `"eye": {"logic": "fixed: door 32 since a1b2c3d (claude-b, 21 Oct)", "bar": "ok: compared with Eastward's ... at 3x, day and night (claude-b, 21 Oct)"}`. `logic` takes `fixed: ...` for an audit fault or `ok: ...` for a sprite the audit never saw; `bar` takes `ok: ...` for a sprite the bar cannot measure. A verdict says what was compared, by whom and when.
- **New art** is measured before it ships: the check fails on any picture under `assets/` the ledger does not list.
- **Comparisons and line-ups.** A kit that loads old art only to show it beside new art or as a scale figure (the resident line-ups in `terrace.py`, `dry_kit.py`, `river_kit.py`) marks that line with `ledger: compare` in a comment (on the line or the line above), and the check skips it.
- **The report:** `python3 scripts/art/asset_ledger.py --report OUT.png` draws one contact sheet per lane (KEEP green, REWORK amber with its fix and failing checks, worst first, RETIRE red).

## 7. The check

`npm run check:assets` (`node scripts/check-assets.cjs`; `--summary` adds the counts; `npm run check:assets-test` runs its own seven cases) fails when:

1. a picture under `assets/` is not in the ledger, by name or by one of its `rules` (today only the world canvas's tiles); or the ledger lists a picture that is gone;
2. a **region build** uses anything that is not KEEP. A region build is any file matching the ledger's `region_builds` globs: the world canvas (`lib/world-canvas*.ts`, `scripts/art/world_canvas.py`), a kit (`scripts/art/*_kit.py`, `*_kits.py`, `terrace.py`), or any file under a `regions/` or `kits/` folder outside `docs/`. It uses an asset by naming its path (an import, a require, a string), by joining a path under `'assets'` in Python, or by importing an old generator module (`valley_props`, `scenery`, `frost_zones`, ...): then every sprite it names from that module (`vp.props()['bench']`, `vp.bench(...)`) must be KEEP, and an import that names none counts as using everything the module draws.

On main today it passes: there is no region build on main yet. Run against the open branches (20 Oct): the world canvas (#126) fails on its tiles and on every old ground it cuts them from, as it should until the regions are rebuilt; `dry_kit.py` (#137), `river_kit.py` (#133) and `terrace.py` (#90) fail only on their resident line-ups, which need the `ledger: compare` marker; `house_kits.py` (#121) passes.

**Joining `npm run verify`.** Once each lane has re-measured its art after its first redraw round (its board note marked done) and the kits carry their markers, add `npm run check:assets-test && npm run check:assets` to the end of the `check` script in `package.json` (after `npm run check:native`), so `npm run verify` and CI run both. From then on every art PR updates the ledger in the same commit.

## 8. Tools on this branch

The ledger is measured with the newest standard's own tools, copied unchanged from their open PRs so the build and the check run on main: `scripts/art/detail_bar.py` and `detail_baselines.json` (terrace toolkit, #90, at b682aa1), `scripts/art/size_check.py` and `size_guide.json` (size guide, #124, at 771df6a), `scripts/art/style_lint.py`, `house_palette.py` and `art/house-palette.json` (house style, #121, at cea6bae). When those PRs merge, their copies are the same files; if one of them changes first, the merge takes the PR's version and the ledger is rebuilt.

## 9. Gaps

- **Footprints are read from pixels.** No module declares `FOOT`, `ANCHOR` or `APRON` yet (`research/soft-grid.md` 6.3), so the grid check reads the foot line, and placement (`prop-snap`, `prop-footprint`) is not checked here.
- **The bar sees one square per sprite.** The largest solid square may mix a roof and a wall; a sprite that passes or fails there is still compared by eye beside the reference before it is reused (AGENTS.md).
- **The prop audit is on PR #97 (draft).** Its verdicts are stored in the ledger, so the check does not need the file; a sprite added since the audit fails logic until it is checked by eye.
- **Palette against a proposal.** The house palette is still a proposal for Matt (`house-style.md`, "Decisions for Matt"); art on today's ramps passes because the decided recolour maps it either way.
- **Not covered:** the companions (`pets.py` writes TypeScript, not pictures), the UI icons (`art/icons`, `public/icons`) and sound. They are not world art.
