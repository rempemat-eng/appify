# The rules system: from the first finished screen to the whole map (proposed 21 Oct)

Matt, 21 Oct 12:51: "make sure once you have finished one small part you really establish the rules for the rest of the map, so it's easier to animate and draw everything else."

The small part is the valley woodland at 2x, being built on `claude-a/first-screen`. This page says how it becomes the rules every stream draws and animates from. It is the winning draft of three ("the rules are code", graded three times), with the grafts all graders agreed on and the gaps they found fixed. Claude A owns it as art director across the five streams.

**The idea.** Every past failure (speckled ground, meandering outlines, mixed styles, old assets patched in, docs read two ways, review loops) came from a rule living in prose or in one lane's head and being re-implemented. So a rule lives in **code** when it is a technique, in **data** when it is a choice, and in a **check** when it is a measurement of the golden screen. Prose says why and holds no number a file already holds. The wrong picture should be hard to make, not merely forbidden.

## 1. The ground it stands on

**Merge order.** None of the foundations is on main, and #182 already edits `region_plan.py` while #174 is open, so they land in this order (Matt merges, or gives Claude A his word to):

1. **#183, the density engine.** `ART_DENSITY_DEFAULT = 1`, so players see no change; safe first. Merged; the density is decided: 2x (Matt, 21 Oct 18:17: "let's go with 2x. final decision.", [art-style.md](art-style.md) "Density 2"). It defines the export contract (section 5).
2. **#165, the cliff core.** Heights, faces, rims on the soft grid, biomes with their own edge sets, set pieces with attach points and walk masks.
3. **#174, then #182's plan data.** The region-plan schema and `region_plan.py --check`; then #182's plans and checker edits, rebased. Its painters fall under the freeze below.
4. **#187, the block-out.**
5. **The kit cut.** The kit is one package, `scripts/art/native/`, which the first screen already uses (`raster.py`, `terrain.py`, `screens/woodland.py`) and which Claude J's row in the coherence plan already names. rebuild-plan.md's `kit_core.py` was never written: it is this package, and Claude A corrects that line at the cut. `scripts/art/cliff_core.py` stays where it is as the kit's terrain engine, since `native/terrain.py` builds on its `Plan`.

**Freeze the in-flight painters.** About 10,000 lines of per-lane painters sit in open PRs at 1x, none on the cliff core or the kit. From today nobody adds painting to them; their plan data carries on. Each picture is graded in the asset ledger (`scripts/art/asset_ledger.json`), good techniques are ported into the kit as biome data or an edge-set module (Claude A with the lane), and the rest retires.

| PR   | Painter                          | Lane | What survives                                          |
| ---- | -------------------------------- | ---- | ------------------------------------------------------ |
| #155 | `forest_kit.py`                  | E    | ideas for the woodland and conifer biome files         |
| #162 | `coast_kit.py`, `coast_tiles.py` | C    | the coast edge set as a cliff-core module              |
| #169 | `city_kit.py` (stacked on #162)  | C    | retaining walls and stair streets as the city edge set |
| #182 | `moor_kit.py`, `brackens.py`     | F    | the moor's plants; the Brackens plan as data           |
| #180 | `regions/cogsworth_town.py`      | H    | Cogsworth's plan, as `art/regions/*.json`              |
| #177 | `regions/lull_delta.py`          | I    | the delta and Lull belt plans, as data                 |

**One woodland, one ground painter.** The pilot screen was a composite: `scene.build_new` pasted the cliff core's `highland` band (with a snow corner) onto the pilot's own `ground.meadow3`, so it had two ground painters and two sets of boulders, ferns and foliage. The first screen ends this: `woodland` is one biome in the cliff core's `BIOMES` and `EDGE_SETS`, and every ground pixel comes from `cliff_core.paint_ground`. The pilot's `ground.py` and duplicate props are ported or retired at the cut.

**One implementation per rule.** The soft grid lives in at least four places (`cliff_core.grid_mask`, the pilot's `round_corners` and `rects_to_cells`, `terrace.py`'s `GRID`, and constants in `world_audit.py` and `region_plan.py`). After the cut, `grid_mask` and one `CELL` constant are the only ones; the rest import them.

## 2. What the rules are made of

| Layer   | Lives in                                                                                                  | Owner               | Holds                                                                                               |
| ------- | --------------------------------------------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------- |
| Kit     | `scripts/art/native/`, `cliff_core.py`                                                                    | A (rig: J)          | grid, light, outline, shading, despeckle, shadows, placement, rig, effects, export, provenance      |
| Palette | `art/house-palette.json`                                                                                  | A                   | ramps, edge tones, ink, night tint                                                                  |
| Biome   | `scripts/art/biomes/<id>.json`, its cliff-core edge set, `biomes/<id>.py` for shapes no parameter reaches | the biome's lane    | families, ground recipe, plants, cluster recipes, tiers, water, ambience, owned pieces, kit version |
| Region  | `art/regions/<id>.json` (Claude F's schema)                                                               | the region's lane   | tiers, routes, stairs, water, places, named things, `focal`, pinned kit version                     |
| Motion  | `art/characters/**`, `art/fx/<effect>.json`                                                               | J, A                | templates, poses, timing, body plans, effect budgets                                                |
| Golden  | `art/golden/woodland/`                                                                                    | A, approved by Matt | frozen pictures, `measures.json`, `envelope.json`, `overrides.json`                                 |

Drift is prevented by construction and caught at the output:

- **Palette codes, never RGB.** The kit draws in family and tone (`raster.rgb(fam, t)`); colour is applied once, at export. Night is a lookup, not a second painting.
- **`check:kit-only`** lints every biome and region module: kit imports only, no PIL drawing calls, no literal RGB, no PNG from `assets/` unless the ledger grades it KEEP.
- **The provenance map, a merge gate.** Every render writes `provenance.png`, tracing each pixel to a kit piece, the ground recipe or a declared landmark. Any other pixel fails. Landmarks (the cairn, the windmill) are capped at about 10 % of a region's pixels. The lint polices the source; provenance polices the output.
- **JSON schemas** for every data file (`art/schemas/`), so data cannot be filled in two ways.

## 3. The style bible

`docs/vision/style-bible.md` replaces 32,000 words of style docs with about 40 numbered rules, each naming its enforcer: **kit**, **data**, **check** (a named script) or **eye** (Claude A's review). `art-style.md`, `house-style.md`, `eastward-edges.md`, `art-faults.md`, `size-guide.md`, `world-rules.md` and `prop-logic.md` become cited appendices; on a conflict the bible wins and the appendix is fixed in the same PR. A small check fails any rule without an enforcer, or a "check" rule whose script does not exist. For example:

| Rule                                                                                                                                   | Enforcer                                  |
| -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| SB-01 Outlines run along x or y and turn only at a cell line (8 world px); wobble at most 1 texel                                      | kit (`grid_mask`), check                  |
| SB-02 Light from the upper left on every form                                                                                          | kit (`Sprite.render`), check (light sign) |
| SB-03 Every facing is drawn; west is mirrored geometry relit from the upper left (`raster.Grid(mirror=True)`), never a flipped picture | kit                                       |
| SB-04 Colour only from the families the biome allows                                                                                   | kit, check                                |
| SB-05 Calm ground, no speckle; dither only in light fades                                                                              | kit (despeckle), check                    |
| SB-06 Detail is placed things, not pixel variety                                                                                       | data (recipes), check                     |
| SB-07 Every prop has a reason (a bench where a path pauses, a lantern at a junction)                                                   | data, check (prop logic)                  |
| SB-08 Water has a source and an outlet, or is declared closed                                                                          | check (new)                               |
| SB-09 Each screen has a focal point and a quiet companion clearing                                                                     | data (`focal`), eye                       |

## 4. Extraction, biomes and transitions

**From the first screen:**

1. **Play-test before freezing.** Claude M and lane R walk it in the game at `?density=2`, phone size: 44 px touch targets, the companion clearing quiet, props reachable with the companion near, interrupted walks with no stale navigation or nap, reduced motion, day and night.
2. **Freeze.** `art/golden/woodland/`: day and night at 2x, the phone view at 402 CSS px, a landscape crop, the character sheet in four facings, the drawing commit, and 3x crops of nine fixed spots (ground, path edge, cliff face, lip, the fall and pool, water bank, a tree cluster, a prop on its shadow, Bramble and the Mossling).
3. **Measure.** `golden_extract.py` writes per surface kind `detail_bar.py`'s cleanliness numbers, rim columns on cell lines, the light sign, tone histograms, shadow length, and placement densities read from placement data, not pixels (clusters and props per 100 x 100 world px, the share of quiet clearing).
4. **Hand lists become recipes.** What `screens/woodland.py` places by hand (`TREES`, `BUSHES`, `FERNS`, `FLOWERS`, `MUSHROOMS`, `PEBBLES`) becomes cluster recipes in `scripts/art/biomes/woodland.json`; the layout becomes plan data.
5. **The acceptance test.** Regenerate the screen from plan, biome file and kit alone, with no hand coordinates except named things, beside the frozen one. A difference that matters is a rule not yet captured. When equivalent, the regenerated screen is the golden.
6. **The kit sheet.** Every piece at 2x and 3x beside its golden crop, plus a 300 x 180 world px swatch with Bramble in it. This, not prose, is what Matt approves.
7. **The golden's gaps.** The woodland has no stair, no ramp, only the 32 px tier, no built edge, no shore, no snow and no lit street. Those pieces are drawn in the test region and biome sheets before any lane depends on them.

The woodland supplies only the **invariants** (grid share, lone pixels, cluster size, light sign, outline rules). Every other biome is measured against its own swatch's **envelope**, so a desert is never pushed toward woodland numbers.

**Shared everywhere,** in code no biome overrides: the 8 world px cell and corner radii, upper-left light, contour and contact shade, outlines only where height changes, clusters of at least 2 px, the ramp rule, scale, the rig, the shared clock. **Per biome:** data for families, recipes, plants, tiers, water and ambience, and code for its edge set (`check_biomes` already refuses a borrowed or recoloured one).

**Adding a biome:** a one-page brief (reference shots, which edges differ from the woodland's and why, plants), the biome JSON and edge set, then its kit sheet beside the woodland's. Claude A reviews once; Matt sees it in the batched look. Each sheet carries a version (`"kit": "woodland@1"`) and each region plan pins one. Kit releases are additive, at most daily, with a before-and-after sheet.

**Transitions.** Each biome pair that meets in the block-out has an entry in `scripts/art/biomes/transitions.json`: a declared transition edge set, or a shared middle terrain (dirt, scree, shingle, leaf litter) both sides blend into, painted in the region canvas's blend margin. A check fails a meeting pair without one. Claude G drafts the table; each pair's lanes draw their side.

**The palette board.** All biome ramps and swatches on one board, by day and night, for one look at harmony across the map.

**A contrasting test region first.** Claude F builds the Frostline end to end on kit v1 before the other lanes fan out. Highland is the woodland's opposite (rock, snow, stairs, the 12, 16 and 40 px tiers, falls), already a cliff-core biome, with plans in #174 and #182. It proves the rules transfer, fills most of the golden's gaps and gives an honest time to a first region. The harbour follows as the second proof, for built edges.

## 5. A region from plan to merge

**G0, logic on plan data before any pixels.** `region_plan.py --check` already checks the 8 px grid, stair widths, tier changes only on stairs and a stair's tiers matching the ground either side. Added:

- **Water outlet** (new: no outlet check exists yet): every water body has a source and an outlet attach, or is declared closed.
- **Reachability:** a flood fill over `walk_tiers` from every threshold to every place, named thing and egg spot.
- **Prop logic,** building on `claude-a/prop-logic` (`prop-logic.md`, 412 sprites graded): every placed prop names its reason and the reason's condition holds.
- Transition entries exist; the kit version is pinned.

**Build.** One shared command renders any region: day and night at 2x, walk mask, tier map, provenance. No per-region generator. A lane draws by hand only its named things and landmarks, as painters made of kit parts.

**Export, on #183's contract.** The kit draws natively at density 2 in world units and writes each folder's export scale (zones 4 image px a world px, world tiles 2), so `measureDensity` reads 2, no picture passes 4096 px a side and `check:art-density` passes. A region ships as the region canvas's 256 px world tiles with walk and tier masks. A load check (Codex) proves the tiles decode, measure density 2 and walk as the plan does.

**Desktop kept possible.** The kit takes the viewport as a parameter and has no portrait-only constant; density is a render parameter, never stored in region data; every golden, swatch and review sheet includes a landscape crop.

**Merge gates:** grid, cleanliness bands, palette, light, `size_check.py`, G0 on the built masks, provenance, `check:assets`, `check:kit-only`, `check:fx`, `check:art-density`, and the golden passing every check itself.

- **Two-sided bands with absolute floors.** A relative band flaps on near-zero metrics (lone pixels are about 0.5 %), so each band is `[golden - margin, max(golden + margin, ceiling)]` with an absolute ceiling there (lone pixels under 2 %, from the first screen's plan), and a surface below a minimum sample area reports instead of gating.
- **Rims.** The cliff core gates `RIM_ON_GRID` at 0.7 and its highland demo measures 91 %. The 1 texel wobble and lip lobes are deliberate (eastward-edges 1.4), so 100 % is not a target: the gate is the golden's own figure minus a margin.
- **Metrics block, never approve.** Only Claude A's review approves. Nobody tunes parameters to cross a threshold. An accepted near miss goes in `art/golden/overrides.json` with region, check, value, band, reason and date.
- **Detail is counted as placed things,** never pixel variety, and no ground gate has a minimum on tones per patch. Reports print the golden's value beside the region's.

**Claude A's review.** Three screens per region: the most ordinary, the busiest and a threshold. `side_by_side.py` shows the nine crops beside the golden's at the same character height, with the phone view and the landscape crop. One pass judges composition, focal points and atmosphere. A finding that applies elsewhere is fixed in the kit or biome file, never in the region. After two rounds, the question goes into Matt's next batch.

**CI cost** (AGENTS.md: fewer minutes, same bar). Renders are cached by piece hash (the piece's code, its data and the density). A kit change re-renders only changed pieces and the tiles whose provenance lists them, never the whole world; goldens and sheets re-render once, when the PR is marked ready. The cache belongs with #185.

**Codex** cannot open the crew board, so its kit requests and Claude A's answers go through issue #149, mirrored under Feedback in the coherence plan.

## 6. Animation

**Characters (Claude J).** `art/characters/` holds rig templates (biped folk, small folk, four-legged familiar, flyer), key poses per action, facing and frame with anticipation and settle, timing, and one body plan per character (parts, families, joints, z order per facing, height from the size guide). The actions come from cast.md: idle, walk, nap, react, hit, faint, victory, attack and cast in four facings, about 110 body frames per folk plus 24 effects. Walk 6 x 110 ms and idle 4 frames at 420/260 ms are the pilot's values; the rest are proposals until confirmed. N and W are drawn. Joint rigs at a 50 texel adult make jaggies, so each template gets a hand-key cleanup pass, and any frame may be an override PNG (Aseprite) under the same gates. A new folk is a body plan and a face painter. Character cycles run on the walker's own clock, starting and stopping with the action, so the 36 s rule does not apply to them.

**World loops** run on the renderer's shared 36 s clock (`water_flow.py`, `lib/animal-life.ts`), and every period divides 36 s. Every copy of a piece shares one animation; overlays hold only changed pixels in a box, as `water_flow.py` does.

| Effect                       | Frames x ms          | Period |
| ---------------------------- | -------------------- | ------ |
| Water flow (exists)          | 8 x 150              | 1.2 s  |
| Fall sheet                   | 6 x 100              | 0.6 s  |
| Foliage sway, outer clumps   | 4 x 300 (0, 1, 2, 1) | 1.2 s  |
| Lamp flicker, night only     | 4 x 200              | 0.8 s  |
| Smoke, three puffs then rest | 6 x 150              | 12 s   |

All but water are proposals. Under reduced motion or on an inactive screen each loop holds its rest frame; event effects are always finite. Budget per 256 px world tile: at most 8 frames and 1 MB decoded, gated by `check:fx`. `lib/motion-timing.ts` is generated from the same JSON, so drawing and game cannot disagree.

## 7. Build order, by stream

**Starts now:**

| Who                   | Work                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Claude A              | finish the first screen; the merge order above; the freeze notice; draft the style bible                                       |
| Claude J (characters) | rig templates, poses and timing from the first screen's rig; N and W drawn; the cast.md actions                                |
| Lanes B to I (map)    | plans through G0; biome briefs and JSON; no painting on frozen painters; B lists each region's props by reason                 |
| Claude G (routes)     | the transitions table, thresholds and routes as plan data                                                                      |
| Codex (via #149)      | schemas, `check:kit-only`, the water-outlet check, reachability, the load check, the piece-hash cache in #185, the bible check |
| Claude M, lane R      | the golden play-test script and the landscape crop view                                                                        |
| Claude K, Claude L    | progression and fight data, independent of the art rules                                                                       |

**Waits for the golden:** the play-test, freeze, extraction and regenerate test (A); Matt's first look; the kit cut, ledger grades and ports of the frozen painters (A with C, E, F, H, I); the Frostline test region (F); biome kit sheets (lanes) and the palette board (A); then all regions in parallel, Claude B rebuilding props through the kit in the order regions need them, and J adding one folk with each region.

## 8. Matt's looks

1. **The golden screen with its kit sheet,** beside today's art at the same character height. The density is already decided: 2x (Matt, 21 Oct 18:17). One yes freezes the rules.
2. **All biome kit sheets and the palette board, in one batch,** a yes or a one-line note on each. A biome is then locked.
3. **Regions in batches of three or four,** one page each: the three chosen screens beside the golden and a short walk GIF.

He may comment on the board any time, but nobody asks him to. What he says becomes a data or code change and a dated line in the bible.

## 9. Where this breaks

Atmosphere is not a rule: recipes give believable spreads, not a lit window at a path's end, so named things, `focal` and the review stay human. One golden overfits, hence an envelope and a look per biome. Parametric drawing tops out at faces, cloth and unique landmarks, which use hand painters or override PNGs under the same gates. One kit owner is a queue, eased by additive daily releases. Repeatable renders need pinned numpy, scipy and Pillow for `check:art-repro`.
