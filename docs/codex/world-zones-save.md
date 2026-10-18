# C19: saved world exploration, without drawing

Integrated with main `4467eba6e1af89c9545a307d1b471fa049d82138` (18 October 2026 UTC),
including the hut interior, residents, separate moon region, moon journey,
scrolling atlas bar and Riverside pasture. All ten art generators and thirteen
generated modules remain covered by Claude's latest reproducibility checks.
C9's currency PR #18 remains separate. This change makes no economy, reward,
combat, mission, mood or ownership changes and does not wire the atlas UI.

## API for Claude

- `worldZoneIds`, `worldExits`, `worldZoneStart(zone)` in `lib/world-zones.ts`
  read the current generated layout, connection stands and walk grids. Garden
  openings reuse `region-walk.ts`; no second hand-maintained map or sprite import.
- An exit has `from`, `to`, `edge`, `departure` and `entry` in **zone-local art
  pixels**. The two boundary cells are adjacent in region coordinates and have an
  exact reverse exit. Multiple riverside paths remain separate. Nearby markers
  may offer multiple usable cells on the same border, not distinct destinations.
- Only named walking connections become exits. Neighbouring tiles alone do not
  create one. Station/Lumen requires a shuttle; distant trips remain C20. The
  house is a separate room, not a walking border to a physically adjacent tile.
  Its door transition also needs the C20 transition guard before it can commit
  exploration. No invented vehicle connection, cost or unlock is included here.
- `exitsFromWorldZone(zone, { level, mountainLevel })` filters the existing ridge
  gate. The store supplies `mountainLevel` from the actual mountain mission rule,
  not a new balance value. Do not use the ungated graph as an admission check.
- `worldProgress` is saved on the game store, not the backend player row.
  `currentWorldZone(progress, access)` gives a safe renderer start. An unknown
  future zone id or a now-locked resume projects to the garden **without deleting
  that history**. Use `worldZoneStart` for its safe initial standing point.

Before an intended border crossing, call `beginWorldWalk(exit.id)` and retain its
opaque token. Reject null before animating or crossing the ridge gate. On arrival
call `finishWorldWalk(token)`, and update the renderer's committed current zone
only if it returns true. It returns false for stale, repeated, copied, cancelled
or superseded callbacks and rechecks the current gate and account. Do not replace
this with an unrestricted `onEnter(zone)` setter: that would bypass the guard.

Call `cancelWorldWalk()` when the atlas unmounts, is hidden behind another screen
or sheet, turns back, or abandons a path without starting another crossing. The
store also cancels on load, account/mode/battle/progress/Quiet-view changes, backgrounding,
web visibility loss and game shutdown. A valid arrival persists the zone/visited
set only. It never navigates or starts a nap. No in-flight walk is saved.

The existing prototype renderer remains untouched in Claude's lane. Its current
component-only zone and ungated region grid do **not** gain these guarantees
until Claude wires this API and calls cancellation at those presentation exits.
Seamless camera/neighbour mounting, positions within zones, vehicles and fast
travel remain C20 or later. There is no `visit any zone` store action.

## Save safety

Save version 2 adds `worldProgress: { currentZone, visitedZones }`. Unversioned and
version-1 fixtures migrate to garden without resetting the account. Current
exploration state survives save/reload. Unknown ids and nested fields round-trip;
only known accessible ids can become a renderer destination. A missing or invalid
exploration field defaults safely without rejecting otherwise valid progress.
Unreadable and newer saves retain the existing explicit recovery protections.
Pending tokens are runtime-only and cannot revive after reload.

The existing historical fixtures still check level, GRASS, hats, cards, history,
collection, chosen companion, Quiet view and protected mission return. The source
integration additionally exercises real store begin/cancel/finish, battle/nap
interruption, duplicate completion, no player-field changes and persistence.
Explicit version-1 migration is checked as well as the unversioned historical
fixtures. Older version-1 clients will reject a version-2 save through the existing
newer-save protection, not reset it. Preserve version 2 when integrating PR #18,
and keep both additive check scripts if its package script line conflicts.

The graph derives all twenty current zone ids and all region keys, including
`home` and `moon`, from the generated catalogue. Regression checks cover an open
spawn and known-zone resume for every zone while retaining an unknown future
visited id. Single-zone regions never gain an invented walking exit. These tests
do not assert that the prototype's HOUSE or vehicle buttons use the store yet.

Two read-only, in-memory negative controls proved the new pure tests fail when
cancellation is removed or the mountain level comparison is bypassed. No broken
source was written or published.

## Validation scope

Ran: `npm run check:world-zones`, source integration and save-safety tests; full
`npm run verify` and matching CI results are recorded in the PR handoff.

Did not test: renderer integration (not changed), a full atlas traversal, physical
phones, native runtime, device usage, live backend/multiplayer, assistive-tech
output, audio, measured memory/FPS or visual approval.
