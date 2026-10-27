# Codex chat coordination

Live assignments, acknowledgements, blockers and handoffs: [GitHub issue #149](https://github.com/rempemat-eng/appify/issues/149).

## Current routine (27 October 2026)

Read this guide with current `AGENTS.md`, Matt's latest instructions and the live issue. Task assignments and ownership come from the latest applicable claims, releases and decisions on #149; a dated table in a document does not reopen a completed, cancelled or reassigned task. Read the Codex queue and Feedback in `docs/vision/coherence-plan.md`, but reconcile their older entries with those live decisions before selecting work.

Claude A [cancelled C29–C31 on 21 October](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6322623299). Do not restart them because they remain in the old queue or the historical record below. A later task requires its own current claim and scope. The [27 October routine record](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6455025042) records Matt's replacement selection and scheduling instructions. Historical assignments are preserved below for provenance, not as current start conditions.

### Sync and choose one task

1. Fetch the real repository and read current main, `AGENTS.md`, this guide, the Codex queue and Feedback, open PRs and branch heads, and all new or edited #149 comments. Check feedback on your own PRs first. For W0–W7, also read `docs/world-editor.md` on the task's named base; [PR #302](https://github.com/rempemat-eng/appify/pull/302) supplies `claude-a/world-editor` while the editor work is stacked there. Use the named task base rather than assuming every task starts on main.
2. Register one short, unused word as your slot on #149 and include `slot=` in every post. A renamed continuation retains its existing task, branch, PR and checkpoint; it is not a second worker. Read the latest claims before registering or selecting work.
3. Continue an active claim before taking anything new. Keep at most one implementation claim active. Otherwise choose an unclaimed, unblocked task where you can add the most value: tooling, checks, data, editor engineering, bug fixes, tests or concepts. Prefer queued tasks and your existing area. A historical task title or an old "free" list is not evidence that a task is still available.
4. If no queued task fits, a reproducible bug, failing check, missing regression or concrete documentation gap can justify `PROPOSE slot=<slot> task=<id> ...`. State the evidence, exact paths, base and acceptance checks. Start only if no other claim owns those paths and the change introduces no game rules or art direction.
5. Before writing, post `ASSIGN slot=<slot> task=<id> branch=codex/<name>` with the file scope and base. Refresh #149 immediately: the first valid claim wins. If another worker already owns the task or files, release your competing claim and choose again. A quiet branch, elapsed timer or absent reply does not transfer ownership.

### Gates that remain closed

| Work | Required start condition |
| --- | --- |
| X2 journey checks, X3 settlement life data, X4 region plan proposals | Claude A posts an explicit **go** on #149 after the v55 map. A map PR number or a newer draft alone is insufficient. |
| X5 Crossroads editor conversion | W1–W3 are actually merged, plus the explicit #149 go required by the task's existing instructions. |
| Other blocked, waiting, parked or dependency-gated tasks | Their own current approval, ownership and integration conditions. No generic task-selection rule removes them. |

Check actual ancestry and exported APIs on the required target. A merge into a stacked branch is not inclusion on main. Do not duplicate another owner's review follow-up or import an unfinished dependency as if it had passed.

### Work, verify and hand off

- Use an isolated branch and one draft PR for the task. Reuse the existing branch/PR for feedback while it remains open; check whether it already merged before updating it. Keep writes within the claimed paths. Shared package, lockfile, save-schema, fixture and CI paths have one writer at a time.
- Follow `AGENTS.md` and the task's explicit file grants. Never edit `game/actors/player.gd`, force-push, merge, push main, enable auto-merge or change branch protection. Preserve player data and unknown save fields. No game-rule changes; new art or design direction requires Claude A's review. A narrow grant to one chat does not transfer to another.
- Finish and test one step before pushing. Keep the PR draft while iterating and push once per finished step. Use the real remote history and an expected-head check; reject unexpected branch movement rather than overwriting it. Do not repeatedly merge main just to refresh CI.
- Run `npm run verify` and `npm run check:art-repro` on the final exact source, plus `check:kit` or `check:godot` when relevant. Lint must have zero warnings. Retain useful logs and exit records; serialize heavy checks when resources are constrained. Skipped, interrupted, killed and partial runs are not passes.
- Mark ready once after the required local checks pass, then inspect the matching hosted checks. Resolve actual failures before selecting new work. Use a complete label only after applicable matching CI passes. If documented path filters produce no workflow for a docs-only change, record that absence and the local evidence; do not describe it as a hosted pass.
- Post `HANDOFF slot=<slot> task=<id> pr=<n> head=<sha>` with the exact tested head/tree/base, what ran, results, limitations, remaining blockers and the concrete request for Claude A. Keep the issue update short; technical detail belongs on the PR. A test against an old head or dependency stack does not validate its successor. Desktop or source checks do not establish native-device measurements or manual art approval.
- Claude A reviews and merges and mirrors #149 posts to the crew board. Codex uses #149 and its task PR, preserving the current ownership boundaries for vision, art, renderer and generated data. A coordinator does not implement or push another worker's task.

### Scheduled checks and blocked work

Set up one hourly continuation per chat using this routine, reusing its existing automation where possible. If scheduling is unavailable, say so once on #149 and run the routine at every task boundary. Keep durable remote checkpoints so the next run can recover without scratch files or duplicate PRs. A scheduled run must inspect a manual owner's current checkpoint before writing or launching competing validation; an enabled schedule or heartbeat does not prove that another chat is alive.

Check #149 at the start, after every push or handoff, at each task boundary, and at least every 15 minutes while working. Read every new or edited comment, including review feedback and changed claims. Paginate the comments or use a complete update cursor: counting only the first 100 comments cannot detect additions once that page is full. While a live continuation is idle, Matt's requested ten-minute polling can supplement the hourly schedule; it does not replace re-reading the thread before action.

If blocked, post `BLOCKED slot=<slot> task=<id> reason=...` with the precise missing input. Safely checkpoint and explicitly park the implementation before choosing other unclaimed work; parking does not give another worker ownership of its branch. Preserve the original blocker and next step. If nothing useful is unclaimed and unblocked, post `IDLE slot=<slot>` once per idle episode and wait for the next scheduled run. Do not repeat unchanged idle or blocker notices every hour, or disable the continuation merely because a task finished. Report actual tool/check failures rather than suppressing them as successful no-action runs.

## Historical record: 20 October 2026

The remainder preserves the original four-chat assignment, interface questions and evidence snapshot. Its imperative wording describes the instructions at that date. It is **not an active assignment list, a new file grant or a current dependency-status report**. In particular, C29–C31 were later cancelled, and later task-specific grants and decisions must be read on #149. Apply the current routine above, not these obsolete start conditions.

<details>
<summary>Original coordination notes and evidence</summary>

This record coordinated the four Codex chats Matt opened on 20 October 2026. It added no mechanics, traversal rules, rewards or permission to change Claude's files.

## Assigned work

The current continuation records identify these four scopes. Registration in #149 confirms which chat is actually working; an assignment is not a running-worker acknowledgement.

| Chat scope | Work in order | Branches | Start conditions |
| --- | --- | --- | --- |
| C29 / C30 world canvas | Save compatibility, then route gates | `codex/world-saves`, then `codex/ways-route-graph` | Both #123 and #126 changes included in main before implementation. C30 also needs the agreed #118 ways interface. |
| C32 / C31 gates and map | CI gates, then discovery model | `codex/ci-gates`, then `codex/world-map-canvas` | Both #142 and #145 changes included in main before either implementation. C31 additionally needs the canvas interface and C29 save contract. |
| C33 economy simulation | Deterministic scenarios and report | Reuse the chat's claimed branch; otherwise register one | Current rules are the baseline. L2 and #143 G10 remain labelled scenarios; no production changes. |
| C34 native pixels | Isolated native rendering spike and evidence | Reuse the chat's claimed branch; otherwise register one | Agree file ownership with Claude A and consume a pinned canvas interface. Device measurements require a native dev build. |

The first two chats have explicit instructions to leave the repository unchanged until their prerequisites land. Read-only dependency review is useful while blocked. Do not replace that waiting condition with speculative code or take another chat's task.

Do not infer that merging #126 into its stacked base means its changes reached main. Check main's ancestry and actual exported files. PR states and draft heads can change; re-read them rather than treating the snapshot below as permanent.

## Claim and update protocol

1. Read the live issue, current main, task PRs, branch heads and Feedback. Preserve any existing work, including older save or navigation PRs.
2. Post an acknowledgement in #149 naming the existing chat, task, branch/PR, main SHA, paths, state and dependency. Use the task already assigned to the chat.
3. Reuse the existing branch/PR when addressing feedback. For genuinely new work, use an isolated task branch and open one draft PR titled `[Cn taken] ...`. Create/check the branch claim before code writes; do not update a branch another chat already owns.
4. If two chats claim the same files, stop overlapping writes and resolve ownership in #149 with Claude A. An elapsed timer, quiet branch or missing reply does not transfer ownership.
5. Report meaningful state changes in the live issue: blocked, implementing, handoff ready, requested changes, or merged. Include the exact head and the next action. Put technical review feedback on the task PR and link it from the issue.
6. The coordinator reviews claims, dependencies and evidence. It does not implement a worker's assigned task, push their branch, merge or promise continuous monitoring.

Use a short structured acknowledgement, for example fields named `task`, `chat`, `branch`, `PR`, `files`, `based-on`, `state` and `needs`. Do not report "running" or "received" for another chat without an acknowledgement or observed PR activity.

## File boundaries

| Owner within this group | Writes | Consumes or requests |
| --- | --- | --- |
| C29 | Save serialization/schema in `lib/save-data.ts`, historical fixtures, save/store regression tests and moved harness tests after checking prior PR ownership | Versioned coordinate transforms and retired-place policies from Claude A; discovery payload/migration requirements from C31 |
| C30 | A new pure way-gating adapter and route/cancellation tests | Claude's ways catalogue, generated graph, actual traversal APIs and connector/transport contract |
| C31 | `lib/world-map.ts`, pure discovery/map tests and own documentation | C29 handles shared save serialization and fixtures; Claude draws the map and supplies stable canvas IDs |
| C32 | CI wiring, audit summaries, preview-cache checks and own documentation | Actual merged asset/audit commands and fixtures; preserve the existing world-save checks |
| C33 | `scripts/sim-economy.ts`, typed scenario inputs, simulator fixtures and `docs/codex/economy-sim.md` | Current engine values; proposed inputs labelled as hypothetical |
| C34 | Own spike/report files only after agreeing the platform-adapter boundary | Claude makes integration edits in his renderer/components; dependencies added with `npx expo install` |

Claude A retains `lib/world-layouts.ts`, `lib/world-save.ts`, `lib/region-walk.ts`, `lib/world-walk.ts`, generated canvas data, the renderer, art and vision files. Describe needed changes on the owning PR; do not rewrite those files from a Codex task branch.

Shared `package.json`, check lists and dependency lockfiles need one writer at a time. C32 coordinates additive command/check wiring. C33 supplies its simulator command; C34 reserves package/lockfile edits before adding a dependency. Do not turn a small additive edit into a shared-file rewrite.

A specific chat's existing narrow permission to write Feedback does not transfer to other chats. This coordinator uses #149 and PR comments and leaves `docs/vision/**` alone.

## Interfaces Claude A needs to settle

These are requested agreements, not a new implemented schema:

- **Saved location:** stable plane/area identity, world point, relevant level/deck, and layout version. Historical transforms and old stand IDs must be immutable snapshots. Current draft chunk origins are placeholders and cannot define historical migrations.
- **Routing:** stable node/edge IDs, endpoints and planes, walking versus vehicle kinds, costs and required existing way IDs. Identify cross-chunk connections and transport edges explicitly.
- **Discovery:** 256-pixel tile keys scoped by plane, floor rounding at boundaries (including negatives), what counts as walked, visited-zone migration, and a captured set for acknowledging "new since map opened".
- **Integration:** the published data/API heads each worker should target and which fixture demonstrates the combined save, route and discovery behaviour.

C31 sends its compact discovery payload and migration requirements to C29 before C29 freezes the schema. It must not independently patch the same save or fixture files.

## Checks that must not be missed

### C29: save compatibility

Preserve balances, level, companion identity, hats, cards, history, collection, decor and unknown fields. Exercise older layouts, old lava/castle identities and retired locations against versioned mappings. Check reloads at a stand, on a path, at home and around interrupted travel. Conversion fixtures do not prove production migration is wired.

### C30: actual route barriers

#126 currently has a per-region graph, without the complete cross-chunk/transport edge contract. Its direct window search can run before graph fallback. Removing graph edges alone therefore cannot establish a closed-way guarantee.

Exercise every applicable search entry point, connector and existing shortcut, stale cached paths, and interrupted/superseded movement. Closing a way must not leave a direct-search bypass. Claude owns actual traversal/renderer fixes.

### C31: discovery

Test plane separation, negative/border coordinates, old visits, marker states, open/closed ways, existing shortcut eligibility and exact acknowledgement of newly discovered tiles. A map marker does not grant a new travel route.

### C32: audit integration

Use `check:assets` and `check:world-audit`. Keep existing `check:world`, which checks saved-world behaviour. #142 also requires lane redraw measurements and corrected kit comparison markers before activating its gate.

Write per-region compliance summaries on failure as well as success. A preview cache hit must not bypass audit execution or negative-fixture checks. Include all relevant source/configuration/version inputs in the cache key. Coordinate changes that overlap #142/#145's own package/helper edits with Claude A.

### C33: simulation only

Keep current rules, approved L2 scenarios and #143 G10 scenarios separate, deterministic and reproducible over eight weeks. Document schedules, units, caps and spending assumptions. Do not modify live rewards or silently import #146's home-base proposal.

### C34: native evidence

Keep the web path unchanged and the spike behind an off-by-default flag. Run the iOS bundle check; it is not a native runtime test. A nearest-filter API choice or desktop screenshot does not establish native crispness, memory use or frame time. If a native dev build/device is unavailable, state that and leave the measurement requirement open.

## Integration and readiness

Claude A integrates #123 then its stacked #126 and reconciles the ways interface (#118). Separately he integrates #142/#145 after their own prerequisites. Save compatibility comes before enabling the new world; route barriers and discovery must agree with that saved state. Leave `WORLD_CANVAS` off until the combined checks and renderer integration are accepted.

#126 has an open review reporting retained tile counts above its stated budget. That is existing review evidence, not a newly reproduced result in this coordination change. Keep that issue visible before enabling the canvas.

Follow current `AGENTS.md` for CI economy: draft while iterating, run `npm run verify` and `npm run check:art-repro` on the final exact source, mark ready once, inspect matching CI, and use `[Cn complete]` only after it passes. A skipped workflow is not a pass. Do not repeatedly merge main merely to rerun CI; respond to conflicts or review as instructed.

Every handoff ends with what ran and what was not tested, plus exact tested head/base, preview if available, remaining blockers and the concrete request for Claude. Only Claude/the user merges under the existing authorisation; Codex does not push main or enable auto-merge.

## Initial evidence

Snapshot read on 20 October 2026, based on main `81070e190846f51930ead7f99cb955b14d5f5600`:

| Dependency | Observed head | State |
| --- | --- | --- |
| #123 canvas build | `9946d1f82f85ca91dded7da0899b24fff250df81` | Open draft |
| #126 canvas renderer | `b38bbe27b7fbedfb0610f9f512be529a1b83eb0f` | Open draft, based on #123's branch |
| #118 ways | `c7f4833f8339953749c0df70e545054592f3954d` | Open draft |
| #142 asset ledger | `2994ac2b81fdbdf5c02049dd02445fa431ea1d29` | Open draft |
| #145 world audit | `1f3158a1b4bafe4c75cbf7885b76179f78cb4a75` | Open draft |
| #143 gameplay/economy | `0aa6661319a204d997fcb0ef558966521377422f` | Open proposal |

No C29–C34 task PR or branch claim was found in the initial review. No external chat acknowledgement has been observed yet. Check #149 for later updates.

Ran: latest main, AGENTS/queue/Feedback, open PR and branch review; existing continuation assignment lookup; read-only canvas/ways/audit review; documentation consistency checks.
Did not test: full app verify/art regeneration, gameplay/browser, native build/runtime/device measurements or any new worker implementation. This change edits documentation and adds an AGENTS pointer only.

</details>
