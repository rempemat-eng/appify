# Development plan: from here to a complete game (27 Oct)

This plan replaces the "Now / Next / Later" lists in [roadmap.md](roadmap.md) as the order of work. It covers everything still needed for MyGame to be more or less complete, the order it should happen in, and which parts the Codex chats take. Claude A keeps it current; Codex claims tasks on [#149](https://github.com/rempemat-eng/appify/issues/149) as before.

## What the process so far taught us

- **Standards before content.** Every region built before the soft grid, the cast contract and the kits existed had to be redrawn. Nothing is placed in the world until its kit piece has passed the gates.
- **Checks catch what reviews miss.** Agents repeatedly handed over faults (a double head, roads under buildings, debris in a finished stage, flat buildings). Each one now has a check. Any new kind of fault gets a check, not just a fix.
- **Art is reviewed against Eastward by Claude A before Matt sees it.** Codex writes concepts, data, tools and checks. It does not set art direction.
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
- Claude: drawing every piece to the Eastward bar, review gates, Matt's approval.
- **Gate:** the biome's pieces are approved in the catalogue, and a test zone built from them passes every check and Matt's look.

### Phase 4. The vertical slice for real

The first 60 to 90 minutes ([vertical-slice.md](vertical-slice.md)): the home valley, the garden, Crossroads, the woodland and the stone circle, built in the editor from approved kits.

- X5: convert Crossroads to the editor.
- Codex: quest chain wiring, NPC routines from X3, dialogue data, save and load, entering houses, the playtest harness and a scripted run of the whole slice.
- Claude: composition, cast, motion and art review, and Matt's playtest.
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

Codex fills the data for steps 4 and 5 and runs the checks. Claude does steps 1 to 3 and the review.

### Phase 7. Story and content

Acts 2 and 3, the bosses, side stories, visitors and cosmetic sets, written as quest and dialogue data, with Codex wiring and testing them.

### Phase 8. Polish, phones and release

- Motion, sound, accessibility, reduced motion, performance and save migration.
- Touch controls and camera on real phones, then the native iOS and Android builds ([native-readiness.md](../native-readiness.md)).
- For Matt to decide: whether the screen-time loop from the original app stays, and how.

## How the Codex chats work through this

Each chat picks its own work with the hourly routine, in this priority:

1. Finish the task it holds.
2. Phase 1 tasks (W0 to W7, X1, X6) until they are all done.
3. Unblocked Phase 2 tasks (X2 to X4 once Claude A posts "go").
4. Phase 3 concepts and validators for the next biome in the order above.
5. Phase 5 systems whose data format is settled.
6. Phase 4 and 6 data (residents, quests, dialogue) for regions whose plans are approved.
7. Its own proposal, posted as PROPOSE first.

The files each chat may touch are set by its claim and by [coordination.md](../codex/coordination.md). Art, art direction and game rules stay with Claude A and Matt.

## Side by side right now (27 Oct 23:45)

Claude's critical path is narrow: the v55 map and town plans, drawing kit pieces, and reviews. Everything else that does not need new art or a decision from Matt goes to Codex now, so Claude's time goes only to work that needs judgement on art and direction.

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
| Y12 | Pre-review sheets: one script that renders a PR's changed art beside the gates' numbers, so Claude can review it at a glance   | review:asset, review:scene                 |
| Y13 | CI and check speed: cache generators, run checks in parallel, keep results byte-identical                                      | C35's work                                 |

Phase 1 (W0 to W7, X1, X6) still comes first for any chat that can take one. Y tasks are next.

### Must wait

| Waits                                            | For                                              | Why                                                    |
| ------------------------------------------------ | ------------------------------------------------ | ------------------------------------------------------ |
| X2 journeys, X3 settlement life, X4 region plans | Matt's approval of v55 and the town plans        | They are built on the town plan files                  |
| X5 Crossroads conversion, building the slice     | W1 to W3 merged, and the Crossroads kit approved | Nothing is placed from unapproved pieces               |
| Drawing any new biome's pieces                   | That biome's concepts (Y10, Y11) reviewed        | Concepts set the list before Claude draws              |
| Region rollout                                   | The region's plan and kit approved               | Standards before content                               |
| Balance numbers                                  | Y1 to Y3 running in the slice                    | Balance needs the systems to measure                   |
| Phone testing                                    | The slice signed off, and a native build         | Desktop tests are not phone tests                      |
| House decorating                                 | Y3 and the first interior kit                    | It needs cosmetics to sell and pieces to place         |
| Acts 2 and 3                                     | Matt's direction on the story                    | Story is his call; Codex may draft outlines as PROPOSE |

### Claude in the same period

1. The v55 map and town plans, then Matt's review.
2. Drawing the Crossroads town kit from Y10's concepts.
3. Reviewing and merging Codex PRs with the Y12 sheets.
4. Cairn, the woodland kit and other open art once Matt answers.
