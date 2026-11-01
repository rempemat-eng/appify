# Development plan: from here to a complete game

This plan replaces the "Now / Next / Later" lists in [roadmap.md](roadmap.md) as the order of work. It covers everything still needed for MyGame to be more or less complete, the order it should happen in, and which parts the Codex chats take. MyGame Codex · lead keeps it current under the [handover](../codex/handover.md); Codex claims tasks on [#149](https://github.com/rempemat-eng/appify/issues/149) as before.

## Milestone update (1 Nov)

[Approved integration #418](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6564188517) is merged at main `3dd71e29`, retaining the real #299 Cairn, #290 world/cast/weapon baseline and ten #415 regional documents. Matt's approvals are recorded in [Claude's decisions](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6562924662). The exact combined source passed all four hosted canonical gates: 188 clean Godot cases, kit, verify with zero project lint warnings/errors, and 16 reproducing generators. Matching Ready CI passed, including 192 screenshot cases; source/index guards and the downloaded artifact were verified. The first failed JSON-number run and 224 report-only asset findings remain retained.

[Editor #417](https://github.com/rempemat-eng/appify/pull/417) at `b5a971e5` passed all four final local gates with 299 clean Godot cases; its local slot/source lease is released. The square and walkable spring spawn are corrected in the [actual woodland image](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6563821275). Woodland stays candidate, with 31 relation faults and 335 advisories; practical editor authoring/save/reload and scene/art acceptance remain open.

[Map #381](https://github.com/rempemat-eng/appify/pull/381) at `4d3fe4b5` retains the town fills and Granary-row repair. Its [standard producer ended EXIT1](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6563157009) on `hearthold-b034: authored footprint needs an unapproved terrain-tier change` (`Town.adopt`, `towns55.py:501`). Fonts/import/setup succeeded; Crossroads/Neon/exports were not reached. Zero new images/state/full 21-town report; failures remain preserved and no retry is allocated. The [six-image comment](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6563157092) is still historical v55.

[Crossroads #416](https://github.com/rempemat-eng/appify/pull/416) retains source and actual same-frame comparisons, pending final validation/editor placement/art review. [Draft slice #419](https://github.com/rempemat-eng/appify/pull/419) is narrow current-main camp/weapon-metadata integration, with combined validation not yet run. The [handover](../codex/handover.md) retains the detailed evidence and unchanged merge procedure; the current priorities below supersede historical queues.

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

Claude's current DIRECTOR orders replace the old autonomous queue. A worker takes only an explicit lead assignment, checks the real current head and first claims, then posts FIRST ASSIGN and a separate ACK for exact disjoint paths. Completed sources retain review custody; no automatic restart follows a handoff.

The existing systems and phase descriptions above remain the design context, not permission to start extra work. The current first-hour order and stream blockers are below; everything else waits. New game rules and art direction remain Claude/Matt decisions. The lead retains eligible non-art integration under the unchanged [handover procedure](../codex/handover.md#merge-procedure-codex-lead).

## Side by side right now (1 Nov)

Claude A directs priorities, art direction and Matt's review list. The Codex lead delegates scoped work, allocates one serial final validation chain per ready PR and integrates eligible work. At most four implementation claims are active; other agents review/validate only. FIRST ASSIGN and separate ACK with disjoint paths precede writes. The [canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) holds live ownership; historical queues below do not authorise new work.

### Current streams

| Stream | Current state | Next |
| --- | --- | --- |
| Approved baseline | #418 merged: #299, #290 and the ten #415 regional documents; hosted canonical gates and matching Ready CI passed | Reuse the approved baseline; no repeat approval or unchanged rerun |
| Editor #417 | Four local gates passed; woodland remains candidate, with 31 relation faults/335 advisories | Practical editor authoring/save/reload and separate visual/art review |
| Map #381 | Town fills retained; actual standard producer failed on Hearthold's terrain-tier conflict before exports | Existing owner needs an explicit source correction allocation; no retry/waiver |
| Crossroads #416 | Consolidated candidate source and actual matching-frame comparisons complete | Final validation, editor placement and art review |
| Slice #419 | Narrow camp fix and existing detached weapon metadata being integrated on current main | Independent source review, then one lead-allocated combined final chain |

### Must wait

No new audit, requirement-document or harness task starts before the first playable hour. EDITOR-FRESH-LOAD-ANCESTRY/private R4 stays stopped. A released runtime slot does not allocate a new run. Historical focused controls, old-head passes and source-only evidence do not supply current acceptance.

Existing placement and approval constraints remain: X5 uses approved pieces and the accepted editor; map adoption needs the corrected actual terrain outputs and review. Home/work semantics are explicit, not inferred. No new game rules, art direction, Player edits or player-data reset is authorised.

### First playable hour

1. Finish the editor tooling and newest-map correction/review under Claude's current orders; keep tooling separate from candidate woodland art.
2. Build Crossroads in the editor from approved pieces, then wire the existing Act 1 quests and dialogue through Crossroads, woodland and the stone circle.
3. Complete the scripted playthrough through the stone circle waking.
4. Extend Y5 quest/dialogue validation, Y6 save versions, Y1 skill tree/tiers and Y3 Glint shops only where this slice needs the existing systems. Everything else waits.

Send questions and review decisions to Claude in the same [daily SUMMARY](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6551199704); Codex does not ask Matt directly.

## Historical lead coordination update (28 Oct)

Matt appointed **MyGame Codex · lead** coordinator and integrator with non-art merge authority. The separate coordinator and crew board are retired. [Issue149's canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) is edited in place. The [handover](../codex/handover.md) specifies four-hour status requests, eight-hour active-claim release, art approval and exact-source merge checks. Delivered handoffs are review duties, not abandoned implementations.

Claude A6467789932 opened X3 and Y15 on proposed source pins, without approving the map/art. Claude A6471345306 set the first Y15 batch on PR303@4984438d: Hearthold, Cinderwick and Launch Cape. Delivered proposals #335/#334/#336 await placement review and generator adoption. Further X3 packets need explicit home/work source semantics. X2/X4/Y4 and X5 retain their documented approval/dependency gates.

The [canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) holds live claims and free briefs. At the 28 Oct 23:40 snapshot, free reserve requirements are Y16 Sunstone, Y18 Tidebloom, [Y20 Cogsworth](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6480837587) and [Y22 Lull river/meadow interfaces](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483455966). Y21 Brackens is claimed by Prism with source published at16ccf262; its PR/gates remain pending. Y10 Crossroads is claimed by Axiom on draft #353; Y19 Frostline is claimed by Tempo on draft #352. Y23's regional requirements-classifier correction is separately assigned from main and follows the higher Y12 priority. Y11 coast/city and Y17 fire-country reports retain their owners/review duties. Each brief pins existing sources, reuses W0 families by reference and writes one new document only. No catalogue/schema/painter/town/package edits, new art direction, approval promotion or placement. Concept JSON is a separate follow-up after W0 semantic intake is settled. Reserve concepts do not override the core/editor priority.

Current reviews do not mark whole Y systems complete: Y1/Y3/Y7/Y8 are isolated models; Y9 audits real control-size failures that still need fixing; Y12 is evidence tooling. W2#305's logical-ID/gameplay-preservation repair has28 focused passes at `64c212fc`; its original full Godot/kit/verify/art chain and all three current hosted jobs subsequently passed. Local and hosted combined-source trees remain separately attested, and full editor acceptance remains pending. Pure engineering PRs must not carry unapproved editor/map ancestry into main.

## Historical engineering update (28 Oct 21:14)

Y12 classifier #346 is merged at main `7f83ee03` after independently reviewed final local verify/art evidence and three matching hosted checks. Known town/cast/concept/blockout sources remain incomplete source-only evidence; fixtures are inventory, not executed tests or production-art approval. This does not accept the editor, town plans or the whole Y12 system.

Y13 actual-cache evidence is owned by CI-map on draft #350 under [ASSIGN6478940444](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6478940444). Its observed jobs missed caches, so no warm speedup is established. Full final gates remain queued. Rill #347 and Forge #343 finished their original frozen verify/art chains and all current hosted jobs passed; Rill's optional JSON-schema comparator remains skipped, not passed. Their unapproved editor/map ancestry and Matt holds remain. [Allocation6483373484](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483373484) gives the next single chain to frozen X3 #349, retaining production custody. E2 combines delivered editor source on a new Codex proposal branch under [6483540277](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483540277); combined gates and acceptance remain required. The board records later reservations; completed frozen suites are not restarted.

## Historical entire-project Codex ownership (28 Oct 17:24)

All Claude lanes are off until Matt says to switch back. Wherever historical sections name Claude A or a Claude lane, the lead now performs that work or assigns it to a Codex worker. The lead may launch as many isolated agents as useful. Claims, own branches and non-overlapping files remain mandatory. Art/map PRs use needs-matt-review and merge only after Matt's OK; written direction remains unchanged. See the latest handover and canonical149 board for live states.
