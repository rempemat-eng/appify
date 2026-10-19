# C24: keyboard and garden exits

Source baseline: `0798b8287dbd1a70617183b2ca1bd5f7d203121d` (19 October 2026).
This is a **draft regression-test handoff**, not a completed runtime fix.

Run `npm run check:keyboard-exits`. It is appended to `check`, hence `verify`.
There are no skipped tests, expected-failure exemptions or altered runtime files.
On the baseline, 42 cases pass and three fail, representing two issues.

## What executes

- The actual `lib/keyboard-walk.ts`, transpiled in a VM with controlled React
  effects, web events and interval delivery. Cases cover normalised and cancelling
  directions, duplicate aliases, key-step priorities, typing and modifier guards,
  repeats, mixed-case release, blur, latest callbacks, disabled/native/server
  boundaries and listener/timer cleanup.
- Actual `gardenExitToward`, `atGardenExit`, `exitWalk`, `regionWalk`,
  `makeWalkGrid`, `tileAt` and generated map data. All four chosen exit routes
  reach their correct neighbour. PNG imports are opaque, not inspected images.
  This supplements the existing world-save exit checks, not a physical-art audit.
- The actual AST-selected `homeAt`, `outside`, `homeward` and `goHome` declarations from
  `app/world.tsx`, executed together with controlled spawn, focus, refs and router.
  Selection requires exactly one declaration each; missing/renamed source fails.
  Source checks also require move and settle paths to invoke `homeward`.

The home test is a narrow callback harness, **not a full component render**.
Router delivery deliberately does not immediately remove focus: multiple queued
callbacks may arrive before navigation settles. It checks dispatch ownership,
not whether a particular browser happens to show two visible transitions.

## Reproduced failures and requested changes for Claude A

### K1: opposite-key cancellation loses the interval

Sequence: keydown W; keydown S; timer tick cancels the directions and calls
`halt()`, removing the interval; keyup S; tick. W is still held, but `up()` only
halts and never restarts an interval, so there is no further step. Another
keydown can revive movement, but releasing the opposing key alone cannot.

Proposed fix: centralise timer reconciliation after both keydown and keyup.
If a direction remains and no interval exists, resume it; when there is no
direction, stop once. Preserve alias deduplication, typing guards, one interval
and current callback refs. Re-run the existing repeat, blur and cleanup cases.
This PR changes tests only, including no edit to `lib/keyboard-walk.ts`.

### H1: returning home has no synchronous once-only claim

Two failures exercise the same issue:

1. Spawn in the yard at local (160, 300). Invoke the actual callback twice at
   (184, 300), as move then settle could do. Both calls pass the distance guard
   and each writes `homeArrival` and calls `router.replace('/')`.
2. Spawn just outside at (-8, 440). Move into (20, 440), then deliver another
   queued callback at (24, 440) while the router still reports focus. Both commit.

The test observes two dispatches, expected one. Setting `outside.current=false`
does not prevent the distance-from-spawn branch from admitting another callback.
Unfocused callbacks already cause no route or arrival write and that case passes.

Proposed fix in Claude A's `app/world.tsx`: claim home navigation synchronously
with a dedicated ref before writing UI state/router. Reject subsequent callbacks
for that navigation owner; define when a new deliberate entry can reset the
claim. Do not rely on eventual focus loss or a React state update for exclusion.
Keep exact garden-local arrival coordinates and the initial anti-bounce guard.
Broader map/journey/superseded-walk ownership remains C28, not certified here.

## Handoff and limits

Please integrate runtime corrections in Claude's lane, then let Codex re-run
these exact regressions and final verification. Do not merge this draft while
its new strict check is red. No art, generated maps, navigation code, game/store,
save format, balance or rewards have changed. The package change is additive
(one command and one final check-chain entry); preserve C22/C23's independent
check entries when integrating.

Not tested: real React/effect ordering, browser key delivery, actual navigation
unmount timing, Reanimated frames, physical rails/bridges/terrain, visual quality,
real phones/native execution, multiplayer or backend behaviour.
