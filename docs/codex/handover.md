# MyGame coordination and integration handover (28 Oct)

> **Update, 28 Oct 17:24 (Matt):** Codex takes over the entire project until Matt says to switch back to Claude. Claude A is off: the Codex lead owns implementation, art/map work and merging under the existing written direction; changes in art direction require Matt. Art and map PRs merge after Matt's OK, not Claude's. The Codex lead also performs coordination; there is no separate Hyperagent role.

Matt, 28 Oct 16:51: Claude is running out of tokens, so ChatGPT (Codex) takes over a lot of the work, coordinated by Hyperagent if that makes sense. This page sets out who does what from now on. [development-plan.md](../vision/development-plan.md) still gives the order of work.

## Lead authority and hourly routine

Matt appointed **MyGame Codex · lead** coordinator AND integrator on 28 October, with standing non-art merge authority. Codex now runs the entire project until Matt switches back; all Claude lanes are off. The lead performs their work or explicitly assigns it on isolated Codex branches, and also performs the former separate coordinator role. Newer explicit instructions from Matt override historical role restrictions.

The single source of truth is [issue149](https://github.com/rempemat-eng/appify/issues/149) and its [canonical lead task board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125), edited in place and linked from the issue body. Pinning is not exposed by the current connector; do not claim it succeeded. The crew board is retired. Existing hourly supervisor `6ad7e6835454819182e2b0e47683ec28` now runs as MyGame Codex · lead; retain the worker schedules.

- Read main handover, development-plan, coordination and AGENTS, then all new/edited issue149 comments newest first across every page. Later Claude A posts override earlier Claude A posts.
- First valid ASSIGN wins. Tell later claimants to choose again, preserving completed work.
- Post GO when the documented start condition is actually met. Answer BLOCKED from docs; batch unresolved decisions for Matt.
- Request status after more than four hours without meaningful activity on an ACTIVE claim; after eight hours mark it free, preserving its branch/checkpoint and requiring a new explicit owner before writes. Delivered handoffs, review duties and decision waits are not abandoned implementations. Inspect edited checkpoints, source and test activity.
- Maintain free, claimed (slot/branch/PR), waiting (dependency), in-review and merged states. When fewer than four suitable tasks are free, post briefs from the next applicable phase with scope, files, start condition and acceptance. No new rules or art direction.
- Once per Europe/London calendar day post SUMMARY for Matt: merged, review, blocked, decisions one line each, and art PRs awaiting review. Reconcile after material steps too; avoid unchanged idle spam.
- Never edit `game/actors/player.gd`, reset player data, force-push or change branch protection.

## Roles

| Who                                           | Does                                                                                                                                                                         | Does not                                                                                            |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Matt**                                      | Decides direction, approves art and maps, grants merge rights                                                                                                                | Routine coordination                                                                                |
| **Codex lead: MyGame Codex · lead**           | Coordinates issue149 and integrates eligible non-art PRs under Matt's explicit 28 October authority; maintains the plan/handover, stocks the queue and posts daily summaries | Take worker tasks while reviews/claims need attention; merge art without explicit Matt OK on the PR |
| **Codex workers: MyGame Codex · slot · task** | Take tasks from #149 by the routine below                                                                                                                                    | Hold two claims, start waiting tasks                                                                |

## What moves from Claude to Codex

- **Coordination:** the crew board is retired. The single source of truth is #149 and its canonical task-board comment, edited in place. Pinning is unavailable; use its stable link.
- **Merging** of non-art PRs: the Codex lead, using the merge procedure below.
- **World data:** Claude A6467789932 opened X3 and Y15 on proposed source pins; Claude A6471345306 prioritised Hearthold, Cinderwick and Launch Cape, now delivered as #335/#334/#336. This does not approve the map/art. Further X3 packets still need explicit home/work source semantics. X2/X4/Y4 require approved v55 inputs; X5 retains main-inclusion and approved-kit gates.
- **Concepts** for every kit (Y10, Y11, Y14 and the next biomes), the editor (W0 to W7) and every system (Y1 to Y9).
- **Art from generators:** Codex may change art generators in `scripts/art/` only on a task that says so. It must pass every gate and is labelled `needs-matt-review`. It merges only after Matt OKs it.

## Art without Claude: the gates are the reviewer

Every art PR runs these and pastes the numbers:

- `npm run review:asset` and `npm run review:scene` (the detail bar: buildings reach at least 0.8 of the Eastward reference)
- `npm run check:kit` (piece schema, approvals, ground rules) and `scripts/review/ground_rules.py`
- `scripts/review/town_plan.py` for town plans
- the cast checks in castwork (anchors, no face on N facings, squint test, arm symmetry, scale)
- `npm run check:art-repro` (the pixels reproduce exactly)

It also attaches the Y12 pre-review sheet. The Eastward references stay local to Claude and Matt. Codex follows the written rules in `docs/vision/art-style.md`, `eastward-edges.md`, `ground-rules.md` and `size-guide.md`.

## Ready-PR checklist (Codex lead)

1. CI is green, and the PR lists its local `npm run verify` and `npm run check:art-repro` results.
2. It stays inside its claim's files. It has no game-rule changes, no player-data resets and no force-push.
3. Lint has zero warnings. New browser APIs are recorded in `scripts/native-safe.json`.
4. Art or map changes carry the gate numbers and the `needs-matt-review` label.
5. The PR body names the task id and the #149 claim.
6. Inspect exact-head/merge-tree provenance. Filtered, skipped and absent CI are not passes. An engineering-only PR must not carry an unapproved art/editor/map foundation into main.
7. Art, map, town-plan, kit and cast PRs require explicit Matt OK ON THAT PR. For text-only concepts, report inapplicable raster gates as N/A with source/schema evidence; do not fabricate visual acceptance.

## Merge procedure (Codex lead)

1. Refresh main and the reviewed heads. If a PR head descends from main and the checklist and inherited approvals are satisfied, fast-forward main to it.
2. Otherwise merge main into a scratch worktree, then run `npm run check:godot`, `npm run check:kit`, `npm run verify` and `npm run check:art-repro`, and push only if all pass. Any file under `scripts/art/native/` that changed means regenerating `python3 -m scripts.art.kit_golden`; only the manifest may change.
3. Independent reviewed non-art PRs may share one exact combined validation candidate, retaining every real head and tested tree. Recheck main/head before pushing; never introduce unapproved foundation ancestry.
4. Never force-push. Post "MERGED task=<id> pr=<n> main=<sha>" on #149.

The lead maintains this handover and the development plan through small docs-only PRs; it may merge its own docs after the applicable checks, reporting local and hosted evidence separately.

## Open items handed over (28 Oct)

| Item                                  | State                                         | Next                                                                      |
| ------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------- |
| #303 continent map v55 and town plans | At 4984438d; every plan passes `town_plan.py` | Matt's OK; Codex Y15 polishes towns on `codex/town-<id>` into this branch |
| #302 world editor and woodland kit    | Waiting for Matt's approval                   | Merge after the OK (Codex lead, with the full checks)                     |
| #299 Cairn proportions                | Waiting for Matt                              | Merge after the OK                                                        |
| #290 world and cast, weapon lines     | The weapon table waits for Matt               | Matt                                                                      |
| #294, #301                            | #301 is absorbed by the editor rebuild        | Codex lead closes #301 once #302 merges; review #294                      |
| W0 to W7, X1, X6, Y1 to Y15, X3       | See #149                                      | Codex                                                                     |

## Keep Matt's reviews bounded

- The lead reviews art/maps against written rules and gates; batch only unresolved direction and final approvals for Matt.
- Give Matt one accessible pre-review sheet and PR link per item.
- All Claude lanes are off. The lead owns coordination, source review and assignments; only Matt approves art/map merges.

## Current review boundaries (28 Oct, 23:40 snapshot)

W2#305 now has the literal logical-ID/gameplay-preservation repair at `64c212fc`, with four unchanged red regression methods now passing among 28 focused cases. Its original41154 full Godot/kit/verify/art chain finished with all guards true; all three current hosted jobs subsequently passed (Godot115, zero lint,192 screenshots). Local tree2e1622f2 and hosted merge tree44f46841 differ by44 upstream files outside the two repair/test paths; attest them separately. This does not establish whole-editor acceptance. W1#307 is an existing completed source offer needing allocation reconciliation, not a replacement implementation. Art foundations #302/#294 and map #303 remain approval-gated; #301 closes only after #302 actually merges. Town proposals #334–#336 still need terrain/placement review and generator adoption. Isolated Y-system models and the Y9 audit do not establish complete slice/runtime acceptance.

X3-explicit-use #349 follows [ANSWER6477803442](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477803442): every `home=null` row remains incomplete, including empty-occupant rows; absent occupants or `work=true` cannot imply nonresidential use. Its full final gates remain pending and inherited map ancestry remains approval-gated.

## Current engineering evidence (28 Oct 21:14)

Y12 classifier #346 is merged on main at `7f83ee03781752f6c4db068185142040c8a2c319`, tree `4ec9efb434c20f17faa62c4db165f7e73ada4a6d`. The guarded nonforce fast-forward used independently verified exact-source local verify/art exits, source guards and three matching hosted job logs. Its source-only and fixture classification is engineering tooling, not art or whole-Y12 approval. The existing separate report-only asset inventory still reports findings. See [MERGED6479481908](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6479481908).

Validation capacity and ownership live on the canonical board. Rill #347's original22325 and Forge #343's original39920 verify/art chains finished with unchanged source guards; all four Rill and all five Forge current hosted jobs passed. Rill's optional JSON-schema comparison remains skipped, not passed. Inherited editor/map ancestry and Matt approval remain separate holds. [Allocation6483373484](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483373484) gives the next validation-only chain to frozen X3 #349, retaining editor-data's production custody. E2's combined-editor proposal is separately assigned by [6483540277](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483540277), with no main or art-approval authority. Historical terrain diagnostics and completed suites are not repeated. A capacity release is not permission for every queued owner to start; the lead posts each exact allocation. Paused owners retain source and review duties.

## Complete Codex takeover and task order (28 Oct 17:24)

Matt's latest instruction supersedes the earlier partial handover. The lead may assign as many isolated Codex agents as useful. Each keeps one claim, posts ASSIGN before coding, uses its own branch and has no file overlap with active owners. A former Claude PR is continued only by explicit lead assignment on a NEW codex/branch from its real head; never overwrite the old branch.

Workers finish their current claim, then prioritise: (1) W0–W7/X1/X6; (2) Y15's first three towns and Highgarth keep wording, remaining Y15 towns, then X3; (3) Y12 pre-review sheets; (4) Y5/Y6/Y1/Y2/Y3/Y4/Y7/Y8/Y9/Y13 on existing systems; (5) Y10/Y11/Y14 concepts; (6) X2/X4 only after Matt approves v55; (7) X5 and the first playable hour only after W1–W3 merge and the Crossroads kit is approved. Existing started claims finish first.

Use needs-matt-review for art/map/kit/cast/town proposals. Earlier requests for Claude approval are superseded; only Matt's OK on the PR permits their merge. No new game rules or art direction changes without Matt.
