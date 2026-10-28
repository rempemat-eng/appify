# Handover: ChatGPT and Hyperagent take over most of the work (28 Oct)

> **Update, 28 Oct 17:24 (Matt):** Codex takes over the entire project until Matt says to switch back to Claude. Claude A is off: the Codex lead also owns art direction, art and map work, and merging. Art and map PRs merge after Matt's OK, not Claude's. Hyperagent is optional and not set up.

Matt, 28 Oct 16:51: Claude is running out of tokens, so ChatGPT (Codex) takes over a lot of the work, coordinated by Hyperagent if that makes sense. This page sets out who does what from now on. [development-plan.md](../vision/development-plan.md) still gives the order of work.

## Roles

| Who                                           | Does                                                                                                                                                                                                                                                                                    | Does not                                             |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Matt**                                      | Decides direction, approves art and maps, grants merge rights                                                                                                                                                                                                                           | Routine coordination                                 |
| **Hyperagent: MyGame Coordinator**            | Runs hourly on #149: resolves claim collisions, posts "go" when a task's start condition is met, keeps one pinned task list (free, claimed, waiting, in review), chases chats that have gone silent, and checks ready PRs against the checklist below. Sends Matt a short daily summary | Edit code, merge, change art direction or game rules |
| **Codex lead: MyGame Codex · lead**           | Takes over Claude A's integration job: reviews and merges non-art Codex PRs that pass every check (once Matt grants it), keeps development-plan.md and this page current, and writes new task briefs when the queue runs low                                                            | Merge art PRs without Matt's or Claude's OK          |
| **Codex workers: MyGame Codex · slot · task** | Take tasks from #149 by the routine below                                                                                                                                                                                                                                               | Hold two claims, start waiting tasks                 |
| **Claude A (on call)**                        | One batched art review a day at most: everything labelled `needs-claude-review` in one pass, plus drawing that only Claude should do when Matt asks                                                                                                                                     | Routine coordination, the board, map polishing       |

## What moves from Claude to Codex

- **Coordination:** the crew board is retired. The single source of truth is #149 and its pinned task list.
- **Merging** of non-art PRs: the Codex lead, using the merge procedure below.
- **World data:** town plan polish (Y15), settlement life (X3), journeys (X2) and region plans (X4) once Matt approves v55.
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

## Ready-PR checklist (Hyperagent and the Codex lead)

1. CI is green, and the PR lists its local `npm run verify` and `npm run check:art-repro` results.
2. It stays inside its claim's files. It has no game-rule changes, no player-data resets and no force-push.
3. Lint has zero warnings. New browser APIs are recorded in `scripts/native-safe.json`.
4. Art or map changes carry the gate numbers and the `needs-claude-review` label.
5. The PR body names the task id and the #149 claim.

## Merge procedure (Codex lead)

1. If the PR head descends from main, fast-forward main to it.
2. Otherwise merge main into a scratch worktree, then run `npm run check:godot`, `npm run check:kit`, `npm run verify` and `npm run check:art-repro`, and push only if all pass. Any file under `scripts/art/native/` that changed means regenerating `python3 -m scripts.art.kit_golden`; only the manifest may change.
3. Never force-push. Post "MERGED task=<id> pr=<n> main=<sha>" on #149.

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
- Claude does not poll #149. Hyperagent pings Matt, and Matt brings Claude in.
