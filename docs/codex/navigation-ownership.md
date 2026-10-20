# C28: navigation ownership regression handoff

Status: **red, draft, not complete**. Runtime fixes belong to Claude A.

## Source and execution

The input source is main `f4b00512498407f9204b306afb039ed2d575cc84` (19 October 2026).
The harness reads the current checkout's actual:

- `app/(tabs)/world.tsx`: AtlasWalk props, journey callbacks, WorldTab and the one-shot link.
- `components/atlas-walk.tsx`: keyboard enable expression and the walkTo closure.
- `components/journey.tsx`: skip/done guard and lifecycle effect before presentation.

Run `npm run check:navigation`, or `node scripts/check-navigation.cjs /absolute/source-root`.
The command is additive to `check`; failures stay failures, not expected-failure passes.
AST extraction requires one matching declaration/component/hook. Missing or ambiguous
source fails the harness instead of silently omitting cases.

The isolated verification snapshot contains these exact three input files, the current
package file, the new script and this document. It is **not a complete application checkout**.
The local Git mirror advertises synthetic master only, not the real GitHub main/history.
Publication must use the real main tree/parent with an expected-head guard; never push the
local synthetic history. Full final-source `npm run verify` and `check:art-repro` have
not been completed, and the PR must remain draft. An attempted npm run verify in this
partial snapshot exits 1 at tsc --noEmit (no tsconfig/application tree, compiler help);
that is an environment/setup limitation, not a final application typecheck result.
No later verify stages or exports ran. No green CI/preview claim substitutes
for that missing verification.

## Results on the input source

25 cases: **20 pass, 5 fail** (exit 1). The five failures represent three ownership gaps.

| Area                   | Cases | Result and scope                                                                                                                                                                                                                                  |
| ---------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Keyboard ownership     | 8     | Parent interactive/active props combined with the actual child hook-enable expression block registration behind map, journey, blur and parent-follow ownership. Expression/registration proof, not DOM held-key event or native scheduling proof. |
| Walk controls          | 4     | Normal and reduced-motion arrivals, cancellation with finished=false, parent-follow ownership pass with controlled ground paths.                                                                                                                  |
| Superseded walk        | 3     | A completed animation queues old JS arrival, a new intention replaces the parent callback, then the old queue dispatches the latest pass/door/journey callback. All three must remain red until ownership is fixed.                               |
| Journey controls/races | 7     | Actual World arrive/legDone callbacks plus Journey lifecycle: queued finish vs SKIP in both final/intermediate cases, next-leg SKIP, cancelled timing, inactive-app completion and reduced timer pass.                                            |
| Leave screen mid-trip  | 1     | Unmount cancels the animation but commits no destination (0, expected 1). This differs from app-inactive completion, which passes.                                                                                                                |
| World tab refocus      | 2     | First visit/same-focus/blur control passes. Second visit loses the ferry link through the extra effect-driven remount.                                                                                                                            |

## Feedback for Claude A

### 1. A walk needs an ownership generation through queued JS arrival

`cancelAnimation` cannot retract a JS callback already queued by a finished worklet.
The actual arrive closure reads `calls.current.onSettle`, so an old intention can invoke
a newer parent's action and restore the old feet. Guard the callback with an intention
generation invalidated on retarget, deactivation and unmount. Carry the same ownership
through lift continuations. Do not merely capture an older callback: that still permits
stale navigation. The three fixtures use parent-action spies, not real pass/door routing.

Earlier handoff: [queued-arrival finding](https://github.com/rempemat-eng/appify/pull/47#issuecomment-6265480930).
This PR makes the regression durable against the current tabbed source, without
restoring the obsolete garden-homeward implementation.

### 2. Tab blur is not app backgrounding

The app-inactive Journey effect calls finish exactly once; unmount only cancels its
animation. WorldTab now removes World when focus is lost, so the trip owner disappears
without a destination commit. The approved C28 contract is that leaving mid-journey
arrives once. Keep one trip owner/commit guard across screen removal, or provide an
explicit whole-trip departure settlement. Preserve whole-trip SKIP and intermediate
leg semantics. Do not blindly call a per-leg onArrive from every effect cleanup:
dependency changes and leg transitions are not necessarily whole-trip departures.

### 3. Refocusing must consume a new WorldLink exactly once

After a first visit, visit remains positive. A refocus mounts World with the old key;
that child's effect clears worldLink. The parent then increments visit and remounts,
so the second child sees empty route params. The valid fixture is first hut entry,
blur, then pier→isles. Final link must still be the ferry link and only one new child
may mount. A simple focus conditional naturally unmounts on blur and mounts afresh on
focus; removing the effect-driven visit/key is a proposed minimal repair, not implemented.

[Current-source handoff](https://github.com/rempemat-eng/appify/pull/47#issuecomment-6275964397).

## Limits and follow-up

Hooks, focus, Reanimated callbacks/JS queue, timers, pathfinding, game store, router
and presentation are explicit boundary substitutes. No React reconciliation, Expo
Router event delivery, actual station traversal, save hydration, deck/lift geometry,
camera, artwork, phone, native runtime, backend or multiplayer certification.
The focused/unfocused transitions are a deterministic effect-boundary model.

The checker has no network calls and makes no app/save writes. Running it reads source
and prints results. No runtime, rule, reward, save shape, asset or generator is changed.

Once Claude integrates fixes, rerun this command and the complete current-source
verify/art checks; inspect matching Actions and a disposable browser profile before
marking ready. In the browser, hold a key while opening map/journey, retarget just as
a walk ends, race SKIP at a leg boundary, leave a trip via HOME, and enter hut/ferry
a second time. Normal/reduced motion and backgrounding are separate cases.
