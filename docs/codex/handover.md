# MyGame coordination and integration handover (28 Oct)

> **Update, 28 Oct 17:24 (Matt):** Codex takes over the entire project until Matt says to switch back to Claude. Claude A is off: the Codex lead owns implementation, art/map work and merging under the existing written direction; changes in art direction require Matt. Art and map PRs merge after Matt's OK, not Claude's. The Codex lead also performs coordination; there is no separate Hyperagent role.

Matt, 28 Oct 16:51: Claude is running out of tokens, so ChatGPT (Codex) takes over a lot of the work, coordinated by Hyperagent if that makes sense. This page sets out who does what from now on. [development-plan.md](../vision/development-plan.md) still gives the order of work.

## Milestone update (29 Oct)

Current main is `b1dbceafc77d51358eae503f8f57bac617055fbe`, after [E7 #371](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6495210365) integrated the reviewed authority correction #314 and bank diagnosis #373. Actual main and all three merged/closed PR states were confirmed at 11:15:40 UTC. Exact shared tree `60741145ee1ecc5fcfa476340a08d710160cd1b9` passed one serial local chain: 187 clean Godot methods, kit, zero lint warnings, 152 review and 46 narrative methods, web/iOS exports and 16-generator reproduction. After Ready, all three heads actually had zero runs/checks/statuses; all five Markdown filters were verified as NOT RUN, not hosted passes. Existing #314 Ready metadata was retained without cycling. Source, dependency and current original/evidence guards passed; this is combined-tree coverage, not separate full runs on the two source heads. No unapproved editor/map/art foundation or threshold change entered main.

Earlier [E3](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484421908), [E4](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6485386955) and [E6](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6487946496) retain their separate exact-tree results. E6 at `0940f0c7` / tree `2d6a294a` passed four local gates and three actual hosted jobs, including 192 screenshots; hosted Godot/native and source367 Markdown filters were NOT RUN. Its report-only asset inventory exited 1 with 224 findings under continue-on-error, so workflow success did not clear that inventory. Merged Y25 material-context routing still supplies incomplete context, not rendered-quality approval. Merged Y29 explains the two bank reports with source-pinned masks and numeric replay while preserving both raw FAIL statuses; palette matching remains a diagnostic proxy, not authoritative final-image provenance or a detector waiver.

Phase 1 remains open. Earlier editor #357 at `b1b066d9` / tree `941059e2` passed four local gates with 280 clean Godot methods. Frozen [#364](https://github.com/rempemat-eng/appify/pull/364) at `6d309ea3` / tree `e34dedaa` passed Godot (285 clean methods), kit, verify (zero lint warnings, 243 review and 46 narrative methods, web/iOS exports) and ordinary 16-generator reproduction. [Its collection](https://github.com/rempemat-eng/appify/pull/364#issuecomment-6486569428) retained three completed phases after environment recovery and resumed only the unfinished art command; it was not an uninterrupted chain. Y26/#362 at `70826862` imports the exact manifest from [parent1b64's single external proof](https://github.com/rempemat-eng/appify/pull/362#issuecomment-6486996581): all five W7 PNG byte strings/RGBA, the other 52 input hashes and all metadata except the final `build.py` provenance hash were unchanged. Y31/[#374](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6494433381) reproduced two owned-formatter lifetime failures, then passed the same three focused methods after the narrow cleanup. That proves this ownership correction, not all editor startup/shutdown diagnostics.

Current editor proposal [E8 #375](https://github.com/rempemat-eng/appify/pull/375), head `45ed3cad029c106977e6c0c833913dcb1c614fbd` / tree `0bdea46338655dcb3c9922ad5cbcdd023310b87d`, has real inputs main `b1db`, editor364, freshness362 and formatter374. [Its actual full invocation failed](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6497332917): import and main300 passed, 288 GdUnit methods executed, and five terrain-image methods had 23 failed assertions with retained X11/Wayland infrastructure errors. These are neither 23 distinct failed methods nor successful negative-render proof. The outer headless suite invokes real GL/X11 children through `test_terrain._shot`; clearing DISPLAY/XAUTHORITY and leaving KIT_SHOT_XVFB unset removed their display authority. Kit, verify and ordinary art did NOT RUN. Full session59260 and read-only collector23947 are terminal/released; all current source/evidence/private-and-donor guards passed. A separate authenticated-display diagnostic covering all 17 unchanged terrain methods was allocated under [GO6498205038](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6498205038). Its allocation is not a canonical full-chain pass; the last canonical result remains session59260's failure. Later diagnostic outcomes and allocations belong on the live board. No method, parity threshold or error was skipped to obtain a pass. #375 stays Draft/needs-matt-review, with new final gates still required.

The earlier visual packet is incomplete: ten direct captures and [the root-inspected 2D/World-dock view](https://github.com/rempemat-eng/appify/pull/364#issuecomment-6487315834) establish those desktop views, with six functional smoke cases, while Vulkan/VSync/RID/ObjectDB/resource diagnostics remain. Canonical Y12 was deferred and the first composite failed on fractional crop bounds. Y30's permanent display/crop fixes are on main and included in E8, but E8's failed full run is not a successful canonical Y12/composite or current editor view. The 14 raw findings, missing legal painted contexts, bridge contracts, final bank-mask provenance, matched Eastward/reference/device evidence and Matt's PR-specific OK remain open. [Y28/#372](https://github.com/rempemat-eng/appify/pull/372) is an unapproved test-layout proposal: its existing full checker refuses six bridge relations; schema/numeric controls do not approve placement. Y34/#376 at `d63b467e` now routes that exact document to incomplete kit-concept/source-only evidence, with 13 focused controls; it grants no art acceptance. Y32/#379 at `eedc2c9e` copies only verified executable bytes before version probing and gives every child private roots; its 15 mocked controls and source review do not establish actual Godot containment. These two reviewed engineering heads have new combined final gates pending; they are separate from frozen E8.

[The verbose editor evidence](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6487758630) observed original-engine-relative editor-settings Load/Save despite configured XDG roots. Earlier runs are not retrospectively called fully private; no settings restoration or player-data reset is established. [The later copied-binary proof](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6487962898) observed private actual settings/user/config/data/cache paths with original guards unchanged. Future allocated checks use the verified private executable and actual path-containment checks, never the original engine. The earlier original `e5-validation-source` raw-index change and unknown cause remain disclosed under [6494288060](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6494288060): current semantic/source guards matched, and only a new current raw-index baseline was accepted. No original index was reset, refreshed or retrospectively declared equal. E7 and E8 guards attest their own stated current brackets.

Y35 map revision [#381](https://github.com/rempemat-eng/appify/pull/381), source `3e4ab559` / tree `7c391978`, retains real #355/#343/#331/#303 ancestry and the reviewed #378 checker. It proposes v56 Crossroads river diversion, connected Neon districts and complete 21-town reporting while preserving historical v55 artifacts and default-OFF first-town adoption. The retained 40 Crossroads and provisional 72 Neon counted units, 81 Neon records/nine landmarks and all-dry layout controls are source facts, not real-terrain acceptance or approved size exceptions. The first real prospective invocation92753 [failed before export/render](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6498167790): seven retained Crossroads IDs17–23 could not be placed. The complete 21-town report was not reached, all 33 outputs/report were absent, and protected/source guards remained exact. This supplies no map or image acceptance. A later world retry requires separately reviewed corrective source/controller and an explicit allocation; subsequent queue state and outcomes belong on the live board. Y38's [source-only first-town reconciliation #383](https://github.com/rempemat-eng/appify/pull/383) does not adopt #334/#335/#336. Y36 waterfront [#377](https://github.com/rempemat-eng/appify/pull/377) at `d333913c` contains four unchanged candidate PNGs and a corrected bollard snap/footprint contract with focused coverage; full gates, current Y12, composed shadows, Eastward comparison, registration and Matt approval remain pending. Caliper owns Y40's source-only readiness inventory; no candidate catalogue is approved by that audit.

Frozen requirements #352/#361/#363/#365/#366 retain later final-gate/approval waits; their review custody does not expire or reopen production automatically. Crossroads #353 retains local verify/art and its [incomplete source-only sheet](https://github.com/rempemat-eng/appify/pull/353#issuecomment-6485583369), physical gates N/A and hosted Markdown filters NOT RUN. #355's six actual hosted successes retain map/Matt holds without historical raw-terrain proof. Matt's medium 14–22 and large 30–45 ranges do not approve provisional Neon or Highgarth exceptions; canvas +15.49% and recorded usable-land +26.1% remain distinct approval facts. X3 needs explicit home/work semantics; X2/X4/Y4 require approved macro inputs; X5 requires W1–W3 in main, an approved Crossroads kit and applicable GO. The [canonical board](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475643125) and [29 October summary](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484022327) hold later results and current allocations. This snapshot supplies no whole-editor, kit, map, system or device acceptance.

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
