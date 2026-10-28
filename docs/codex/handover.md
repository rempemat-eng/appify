# MyGame coordination and integration handover (28 Oct)

Matt, 28 Oct 16:51: Claude is running out of tokens, so ChatGPT (Codex) takes over a lot of the work, coordinated by Hyperagent if that makes sense. This page sets out who does what from now on. [development-plan.md](../vision/development-plan.md) still gives the order of work.

## Lead authority and hourly routine

Matt appointed **MyGame Codex · lead** coordinator AND integrator on 28 October, with standing non-art merge authority. It performs the former separate coordinator role too. Newer explicit instructions from Matt override historical role restrictions.

The single source of truth is [issue149](https://github.com/rempemat-eng/appify/issues/149) and its [canonical lead task board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125), edited in place and linked from the issue body. Pinning is not exposed by the current connector; do not claim it succeeded. The crew board is retired. Existing hourly supervisor `6ad7e6835454819182e2b0e47683ec28` now runs as MyGame Codex · lead; retain the worker schedules.

- Read main handover, development-plan, coordination and AGENTS, then all new/edited issue149 comments newest first across every page. Later Claude A posts override earlier Claude A posts.
- First valid ASSIGN wins. Tell later claimants to choose again, preserving completed work.
- Post GO when the documented start condition is actually met. Answer BLOCKED from docs; batch unresolved decisions for Matt.
- Request status after more than four hours without meaningful activity on an ACTIVE claim; after eight hours mark it free, preserving its branch/checkpoint and requiring a new explicit owner before writes. Delivered handoffs, review duties and decision waits are not abandoned implementations. Inspect edited checkpoints, source and test activity.
- Maintain free, claimed (slot/branch/PR), waiting (dependency), in-review and merged states. When fewer than four suitable tasks are free, post briefs from the next applicable phase with scope, files, start condition and acceptance. No new rules or art direction.
- Once per Europe/London calendar day post SUMMARY for Matt: merged, review, blocked, decisions one line each, and art PRs awaiting review. Reconcile after material steps too; avoid unchanged idle spam.
- Never edit `game/actors/player.gd`, reset player data, force-push or change branch protection.

## Roles

| Who                                           | Does                                                                                                                                                                                                                                                                                    | Does not                                             |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Matt**                                      | Decides direction, approves art and maps, grants merge rights                                                                                                                                                                                                                           | Routine coordination                                 |
| **Codex lead: MyGame Codex · lead** | Coordinates issue149 and integrates eligible non-art PRs under Matt's explicit 28 October authority; maintains the plan/handover, stocks the queue and posts daily summaries | Take worker tasks while reviews/claims need attention; merge art without explicit Matt/Claude OK on the PR |
| **Codex workers: MyGame Codex · slot · task** | Take tasks from #149 by the routine below                                                                                                                                                                                                                                               | Hold two claims, start waiting tasks                 |
| **Claude A (on call)**                        | One batched art review a day at most: everything labelled `needs-claude-review` in one pass, plus drawing that only Claude should do when Matt asks                                                                                                                                     | Routine coordination, the board, map polishing       |

## What moves from Claude to Codex

- **Coordination:** the crew board is retired. The single source of truth is #149 and its pinned task list.
- **Merging** of non-art PRs: the Codex lead, using the merge procedure below.
- **World data:** Claude A6467789932 opened X3 and Y15 on proposed source pins; Claude A6471345306 prioritised Hearthold, Cinderwick and Launch Cape, now delivered as #335/#334/#336. This does not approve the map/art. Further X3 packets still need explicit home/work source semantics. X2/X4/Y4 require approved v55 inputs; X5 retains main-inclusion and approved-kit gates.
- **Concepts** for every kit (Y10, Y11, Y14 and the next biomes), the editor (W0 to W7) and every system (Y1 to Y9).
- **Art from generators:** Codex may change art generators in `scripts/art/` only on a task that says so. It must pass every gate and is labelled `needs-claude-review`. It merges only after Matt or Claude OKs it.

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
4. Art or map changes carry the gate numbers and the `needs-claude-review` label.
5. The PR body names the task id and the #149 claim.
6. Inspect exact-head/merge-tree provenance. Filtered, skipped and absent CI are not passes. An engineering-only PR must not carry an unapproved art/editor/map foundation into main.
7. Art, map, town-plan, kit and cast PRs require explicit Matt/Claude OK ON THAT PR. For text-only concepts, report inapplicable raster gates as N/A with source/schema evidence; do not fabricate visual acceptance.

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

## Keep Claude's tokens low

- Ask Claude only for decisions on art or direction, and batch them.
- Hand Claude one link per review: the pre-review sheet and the PR, not whole threads.
- Claude does not poll #149. The lead collects decisions for Matt, who brings Claude in for the batch.

## Current review boundaries (28 Oct)

W2#305 needs literal logical-ID lookup, inherited-gameplay preservation and sanitisation-collision round-trip regressions. W1#307 is an existing completed source offer needing allocation reconciliation, not a replacement implementation. Art foundations #302/#294 and map #303 remain approval-gated; #301 closes only after #302 actually merges. Town proposals #334–#336 still need terrain/placement review and generator adoption. Isolated Y-system models and the Y9 audit do not establish complete slice/runtime acceptance.
