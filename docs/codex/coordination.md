# Codex chat coordination

Live assignments, acknowledgements, blockers and handoffs: [GitHub issue #149](https://github.com/rempemat-eng/appify/issues/149).

This document coordinates the four Codex chats Matt opened on 20 October 2026. Read the latest `AGENTS.md`, `docs/vision/coherence-plan.md`, its Feedback, and the live issue before editing. The queue and existing explicit chat instructions retain authority. This document adds no mechanics, traversal rules, rewards or permission to change Claude's files.

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
