# Development plan: from here to a complete game (27 Oct)

This plan replaces the "Now / Next / Later" lists in [roadmap.md](roadmap.md) as the order of work. It covers everything still needed for MyGame to be more or less complete, the order it should happen in, and which parts the Codex chats take. MyGame Codex · lead keeps it current under the [handover](../codex/handover.md); Codex claims tasks on [#149](https://github.com/rempemat-eng/appify/issues/149) as before.

## Milestone update (29 Oct)

Main `b1dbceafc77d51358eae503f8f57bac617055fbe` now includes [E7/#371, authority #314 and bank diagnosis #373](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6495210365). Their exact shared tree `60741145` passed one local four-gate chain: 187 clean Godot methods, kit, zero lint warnings, 152 review and 46 narrative methods, web/iOS exports and 16-generator reproduction. All three PRs are actually merged/closed. After Ready, actual runs/checks/statuses were zero and all five Markdown filters were NOT RUN, not passed. Existing #314 Ready state was not cycled. Combined-tree results do not separately validate each source head. Earlier E3/E4/E6 retain their own exact-tree evidence; E6's report-only 224 asset findings remain unresolved. No unapproved editor/map/art foundation or detector waiver entered main.

Phase 1 remains open. Current editor [E8/#375](https://github.com/rempemat-eng/appify/pull/375) at `45ed3cad` / tree `0bdea463` combines main, frozen364, freshness362 and formatter374. Y26's imported W7 manifest follows the exact five-PNG/RGBA/other52-input proof; Y31 passed the same three focused ownership methods after two expected RED failures. Their new whole-editor acceptance remains separate. [E8's actual full run failed](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6497332917): import/main300 passed and 288 methods executed, but five terrain-image methods produced 23 failed assertions with display infrastructure errors. The outer headless suite launches real X11 children in `test_terrain._shot`; cleared display authority left those renders without a working display. Kit, verify and ordinary art did NOT RUN. The full session59260 and collector23947 actually ended; all current source/evidence/dependency guards matched. A separate authenticated-display diagnostic covering all 17 unchanged terrain methods was allocated under [GO6498205038](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6498205038); that allocation is not a canonical full-chain pass. Later diagnostic outcomes and allocations belong on the live board. No parity checks, methods or thresholds are skipped. Earlier364's four local passes retain their interrupted-art recovery boundary and do not replace this failed current-tree result.

Y30's transport/crop fixes are present in main/E8, but no successful current canonical Y12/composite or editor acceptance follows. The earlier ten captures/visible World dock retain startup/shutdown diagnostic limits; 14 raw findings, missing painted contexts/bridge relations, final bank provenance, references/devices and Matt's OK remain open. Unapproved #372's full geometry check still refuses six bridge relations. Source-reviewed Y34/#376 at `d63b467e` routes its exact document to incomplete source-only evidence (13 focused controls); Y32/#379 at `eedc2c9e` isolates executable bytes and per-child roots (15 mocked controls). Their new combined full gates are pending and neither supplies a real Godot/visual pass. Earlier original-engine settings Load/Save, copied-engine path proof and the unknown original raw-index change/current-baseline disposition remain explicit in the [handover](../codex/handover.md); no settings/index restoration or player-data reset is inferred.

Y35 [map revision #381](https://github.com/rempemat-eng/appify/pull/381) at `3e4ab559` retains genuine355/343/331/303 and reviewed378 input, prospective v56 river/district changes and all21-town reporting. Synthetic all-dry layout controls, retained40 Crossroads/provisional72 Neon units and81 Neon records are not real-terrain acceptance or approved size exceptions. Its first real prospective invocation92753 [failed before export/render](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6498167790): seven retained Crossroads IDs17–23 could not be placed, the complete 21-town report was not reached and all 33 outputs/report were absent. Protected/source guards remained exact. Later corrective work and any newly allocated world run follow the live board; no generation, physical or image pass is supplied by this failed invocation. First-town reconciliation #383 is source-only and does not adopt334/335/336. Waterfront #377 at `d333913c` retains four candidate sprites and focused corrected footprint coverage, with full gates/Y12/Eastward/composed-shadow/registration/Matt holds. Y40 is a separately owned readiness inventory, not catalogue approval. Other requirements keep frozen source/review duties and later exact final-gate waits; tempo's Y33 camp tests are source-only pending a separately allocated reproduction before any production correction.

The [canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) and [daily summary](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484022327) hold later results and current claims. Crossroads353 remains incomplete source-only evidence; seed355 retains inherited map/Matt holds. Medium14–22/large30–45 do not approve provisional Neon/Highgarth exceptions, and canvas/usable-land changes remain distinct. X3 needs explicit home/work semantics; X2/X4/Y4 require approved macro inputs; X5 needs W1–W3 in main, an approved Crossroads kit and GO. Every art/map/kit/cast merge still requires Matt's explicit OK on the applicable PR.

## What the process so far taught us

- **Standards before content.** Every region built before the soft grid, the cast contract and the kits existed had to be redrawn. Nothing is placed in the world until its kit piece has passed the gates.
- **Checks catch what reviews miss.** Agents repeatedly handed over faults (a double head, roads under buildings, debris in a finished stage, flat buildings). Each one now has a check. Any new kind of fault gets a check, not just a fix.
- **The Codex lead reviews art/maps against the written Eastward rules and gates before Matt sees them.** Assigned Codex workers also draw and compose existing direction. Matt approves art/map merges and any changes of direction.
- **One claim per task.** Two chats on one task wastes both. The first ASSIGN on #149 wins.
- **Commit often.** Containers restart. Push after each finished step, keep PRs as drafts while iterating, mark them ready once.

## The phases

Phases overlap: a later phase may start once the gate of the phase it depends on is met for the region or system in question.

### Phase 1. Tools and the world editor (now)

The editor and its checks are what make every later phase fast and consistent.

- World editor tasks W0 to W7 ([world-editor.md](../world-editor.md), on PR #302 until it merges): the kit catalogue, schema tooling, the plan round trip, the Godot dock, walk masks from tile metadata, the relation engine, validator plumbing, and Godot output equal to Python.
- X1 (fix the check:game crash) and X6 (the PR triage table).
- **Gate:** a zone can be built in the editor from approved pieces only, it round-trips to JSON, and every ground-rule and review check runs on it in CI.

### Phase 2. The macro world

- Matt approves the v55 continent map and the town plans (in progress: every settlement as plan data with streets on the soft grid, districts, buildings with purposes, and ground that matches the town).
- X2: journey checks on the five routes in the brief (travel times, arrivals, route choices).
- X3: settlement life data: residents, jobs, routines, animals and props per district, filled into the town plan files.
- X4: region plan proposals per lane, checked against the town plans.
- **Gate:** every region has an approved plan with its towns, routes, landmarks and gates.

### Phase 3. Kits per biome

Order: the home valley and woodland (nearly done, #302), then the Crossroads town kit, the coast and city kit (Neon Harbour's retro-future paving included), the desert, the fire country, the mountains (Highgarth's slate terraces), and the isles.

- Codex: concepts with placement rules for each biome (W0 catalogue format), variant and width-class lists, metadata (size on the grid, where it can and cannot go, shadow, story tie-in, interaction), and the validators.
- Assigned Codex workers: drawing each piece to the written Eastward bar; lead review and Matt's approval.
- **Gate:** the biome's pieces are approved in the catalogue, and a test zone built from them passes every check and Matt's look.

### Phase 4. The vertical slice for real

The first 60 to 90 minutes ([vertical-slice.md](vertical-slice.md)): the home valley, the garden, Crossroads, the woodland and the stone circle, built in the editor from approved kits.

- X5: convert Crossroads to the editor.
- Codex: quest chain wiring, NPC routines from X3, dialogue data, save and load, entering houses, the playtest harness and a scripted run of the whole slice.
- Assigned Codex workers: composition, cast and motion under written direction; lead review and Matt's playtest.
- **Gate:** Matt plays the slice start to finish and signs it off.

### Phase 5. Core systems complete

These can run in parallel with Phase 4 once their data formats are fixed.

- Combat and enemies ([fights.md](fights.md)), weapon lines and evolutions, weapon tiers at levels 8, 16 and 24, and the skill tree ([progression.md](progression.md)).
- Economy and Glint: shops, cosmetics, respec, balance from the economy simulation.
- Homes: entering houses and decorating them (cosmetic, tied to Glint).
- The in-game world map: discovery, markers, fast travel between waystones, and closed routes such as the Highgarth pass.
- The menu, inventory, journal, day and night, weather and sound.
- **Gate:** each system has data, tests and a check in `npm run verify`, and works in the slice.

### Phase 6. Region rollout

In story order: the Brackens and the Frostline, Cogsworth and Fernhollow, Sunstone Reach (Palm Spring and Dust Gulch), the fire country (Hearthold and Cinderwick), the Lull and Neon Harbour with Launch Cape, the Tidebloom Isles, and Highgarth.

Each region follows the same steps:

1. Town plans.
2. Ground from kits.
3. Props.
4. Residents and routines.
5. Quests.
6. Review gates.
7. Matt's review.

Assigned Codex workers own steps 1 to 7 and the data/checks. The lead reviews and integrates; Matt approves art/maps.

### Phase 7. Story and content

Acts 2 and 3, the bosses, side stories, visitors and cosmetic sets, written as quest and dialogue data, with Codex wiring and testing them.

### Phase 8. Polish, phones and release

- Motion, sound, accessibility, reduced motion, performance and save migration.
- Touch controls and camera on real phones, then the native iOS and Android builds ([native-readiness.md](../native-readiness.md)).
- For Matt to decide: whether the screen-time loop from the original app stays, and how.

## How the Codex chats work through this

Each chat follows Matt's 28 October hourly priority:

1. Finish its current claim.
2. W0–W7, X1 and X6: the editor core.
3. Y15 on PR303: Hearthold/Cinderwick/Launch Cape and Highgarth keep wording first; then remaining towns; then X3.
4. Y12 pre-review sheets for Matt.
5. Y5, Y6, Y1, Y2, Y3, Y4, Y7, Y8, Y9 and Y13, extending existing systems.
6. Kit concepts Y10, Y11 and Y14.
7. X2 and X4 only after Matt approves v55.
8. X5 and the first playable hour only after W1–W3 merge and the Crossroads kit is approved.
9. Former Claude PRs302/303/299/290 only when the lead assigns a continuation on a new codex/branch from the real head.

The files each chat may touch are set by its claim and by [coordination.md](../codex/coordination.md). New game rules and art direction changes require Matt. The lead has standing non-art integration authority and performs coordination too; see the handover.

## Side by side right now (27 Oct 23:45)

The Codex lead and assigned workers own the v55 map and town plans, drawing kit pieces, reviews and engineering. All Claude lanes are off. Workers follow the written direction; the lead reviews and integrates engineering, and Matt approves art/map/kit/cast merges and any direction change.

### Can start now (Codex)

The game already has quests, dialogue, saving, doors, villagers, the HUD and the pause menu (`game/core`, `game/world`, `game/ui`). Y tasks extend these. They never rebuild them. Each Y task starts by auditing what exists and lists it in its PR. Values come from the docs. Where the docs give none, the task uses clearly marked placeholders in data and adds no new rules.

| ID  | Task                                                                                                                           | Builds on                                  |
| --- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| Y1  | Skill tree and weapon tiers at runtime: points per level, node unlocks, tiers at 8, 16 and 24, with tests                      | `game/data/progression`, progression.md    |
| Y2  | Weapon lines and evolutions as data and runtime (bow to crossbow, revolver to twin), using the weapon table's current values   | world-and-cast.md, the weapon table Doc    |
| Y3  | Glint economy: earning, shops, cosmetics and a 50 Glint respec, wired to the economy simulation                                | docs/codex/economy-sim.md                  |
| Y4  | World map logic: discovery, markers, waystone fast travel and closed routes (the Highgarth pass), with placeholder art         | world-plan.md, the v55 data once approved  |
| Y5  | Quest and dialogue tooling: a validator for every quest and dialogue file (missing speakers, dead branches, unreachable steps) | `game/core/quests.gd`, `dialogue.gd`       |
| Y6  | Save versioning and migration, with tests for every save shape so far                                                          | `game/core/save_game.gd`                   |
| Y7  | Menu, inventory and journal logic (Stardew-style tabs), without new art                                                        | interface.md, `pause_menu.gd`              |
| Y8  | Day, night and weather clock as data, with hooks for routines (X3)                                                             | living-world-plan.md                       |
| Y9  | Touch controls and camera on phone-sized viewports, with a 44-point target check                                               | `game/core/inputs.gd`, native-readiness.md |
| Y10 | Kit concepts: the Crossroads town kit (W0 catalogue format, placement rules, metadata, variants and widths)                    | W0, ground-rules.md, the town plans        |
| Y11 | Kit concepts: the coast and city kit, including Neon Harbour's retro-future paving                                             | W0, the v55 Neon Harbour notes             |
| Y12 | Pre-review sheets: one script that renders a PR's changed art beside the gates' numbers, so the lead can prepare Matt's review | review:asset, review:scene                 |
| Y13 | CI and check speed: cache generators, run checks in parallel, keep results byte-identical                                      | C35's work                                 |

Phase 1 (W0 to W7, X1, X6) still comes first for any chat that can take one. Y tasks are next.

### Must wait

| Waits                                            | For                                              | Why                                                                   |
| ------------------------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------- |
| X2 journeys, X4 region plans, Y4 map integration | Approved v55/town inputs and applicable GO       | These consume the approved macro world                                |
| Further X3 resident packets                      | Explicit residential/workplace source semantics  | X3 was opened by Claude A6467789932; do not guess homes/jobs/routines |
| X5 Crossroads conversion, building the slice     | W1 to W3 merged, and the Crossroads kit approved | Nothing is placed from unapproved pieces                              |
| Drawing any new biome's pieces                   | That biome's concepts (Y10, Y11) reviewed        | Concepts set the list before assigned workers draw                    |
| Region rollout                                   | The region's plan and kit approved               | Standards before content                                              |
| Balance numbers                                  | Y1 to Y3 running in the slice                    | Balance needs the systems to measure                                  |
| Phone testing                                    | The slice signed off, and a native build         | Desktop tests are not phone tests                                     |
| House decorating                                 | Y3 and the first interior kit                    | It needs cosmetics to sell and pieces to place                        |
| Acts 2 and 3                                     | Matt's direction on the story                    | Story is his call; Codex may draft outlines as PROPOSE                |

### Former Claude work, now assigned by the Codex lead

1. The v55 map and town plans, then Matt's review.
2. Drawing the Crossroads town kit from Y10's concepts.
3. Lead art/map/kit/cast review with Y12 sheets for Matt; only Matt approves those merges.
4. Cairn, the woodland kit and other open art once Matt answers.

## Lead coordination update (28 Oct)

Matt appointed **MyGame Codex · lead** coordinator and integrator with non-art merge authority. The separate coordinator and crew board are retired. [Issue149's canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) is edited in place. The [handover](../codex/handover.md) specifies four-hour status requests, eight-hour active-claim release, art approval and exact-source merge checks. Delivered handoffs are review duties, not abandoned implementations.

Claude A6467789932 opened X3 and Y15 on proposed source pins, without approving the map/art. Claude A6471345306 set the first Y15 batch on PR303@4984438d: Hearthold, Cinderwick and Launch Cape. Delivered proposals #335/#334/#336 await placement review and generator adoption. Further X3 packets need explicit home/work source semantics. X2/X4/Y4 and X5 retain their documented approval/dependency gates.

The [canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) holds live claims and free briefs. At the 28 Oct 23:40 snapshot, free reserve requirements are Y16 Sunstone, Y18 Tidebloom, [Y20 Cogsworth](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6480837587) and [Y22 Lull river/meadow interfaces](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483455966). Y21 Brackens is claimed by Prism with source published at16ccf262; its PR/gates remain pending. Y10 Crossroads is claimed by Axiom on draft #353; Y19 Frostline is claimed by Tempo on draft #352. Y23's regional requirements-classifier correction is separately assigned from main and follows the higher Y12 priority. Y11 coast/city and Y17 fire-country reports retain their owners/review duties. Each brief pins existing sources, reuses W0 families by reference and writes one new document only. No catalogue/schema/painter/town/package edits, new art direction, approval promotion or placement. Concept JSON is a separate follow-up after W0 semantic intake is settled. Reserve concepts do not override the core/editor priority.

Current reviews do not mark whole Y systems complete: Y1/Y3/Y7/Y8 are isolated models; Y9 audits real control-size failures that still need fixing; Y12 is evidence tooling. W2#305's logical-ID/gameplay-preservation repair has28 focused passes at `64c212fc`; its original full Godot/kit/verify/art chain and all three current hosted jobs subsequently passed. Local and hosted combined-source trees remain separately attested, and full editor acceptance remains pending. Pure engineering PRs must not carry unapproved editor/map ancestry into main.

## Engineering update (28 Oct 21:14)

Y12 classifier #346 is merged at main `7f83ee03` after independently reviewed final local verify/art evidence and three matching hosted checks. Known town/cast/concept/blockout sources remain incomplete source-only evidence; fixtures are inventory, not executed tests or production-art approval. This does not accept the editor, town plans or the whole Y12 system.

Y13 actual-cache evidence is owned by CI-map on draft #350 under [ASSIGN6478940444](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6478940444). Its observed jobs missed caches, so no warm speedup is established. Full final gates remain queued. Rill #347 and Forge #343 finished their original frozen verify/art chains and all current hosted jobs passed; Rill's optional JSON-schema comparator remains skipped, not passed. Their unapproved editor/map ancestry and Matt holds remain. [Allocation6483373484](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483373484) gives the next single chain to frozen X3 #349, retaining production custody. E2 combines delivered editor source on a new Codex proposal branch under [6483540277](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483540277); combined gates and acceptance remain required. The board records later reservations; completed frozen suites are not restarted.

## Entire-project Codex ownership (28 Oct 17:24)

All Claude lanes are off until Matt says to switch back. Wherever historical sections name Claude A or a Claude lane, the lead now performs that work or assigns it to a Codex worker. The lead may launch as many isolated agents as useful. Claims, own branches and non-overlapping files remain mandatory. Art/map PRs use needs-matt-review and merge only after Matt's OK; written direction remains unchanged. See the latest handover and canonical149 board for live states.
