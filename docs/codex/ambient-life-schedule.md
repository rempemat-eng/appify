# C21: bounded ambient-life schedule

Pure presentation, based on main `df61cf4`. No renderer, artwork, game rules,
rewards, player data, dialogue, shops or movement gates are changed.

## Contract for Claude

`ambientLife(context, zoneEmitters(zone, false))` selects from the **existing**
catalogue in `components/atlas-life.tsx`; it never copies its coordinates into a
second catalogue. Residents use the existing `lib/resident-routes.ts` endpoints.
The garden currently has no atlas emitter catalogue: pass its authored candidates
if compatible, or an empty array. No unseen frogs, drones or shelters are invented.

- Pass local `minuteOfDay` explicitly. Dawn is 06:00–09:00, day 09:00–18:00,
  dusk 18:00–21:00, night 21:00–06:00, preserving the existing night boundary.
- Pass `season: 'original'` and `weather: 'original'` until a person explicitly
  chooses presentation settings. This module reads neither real weather nor GPS.
  Clear removes existing rain; Rain shelters small animals but does not create rain
  where there are no authored emitters. Winter suppresses summer insects/lizards;
  explicit autumn keeps leaf fall. Original preserves the catalogue's seasons.
- Butterfly anchors become fireflies at dusk/night. Residents use existing safe
  routes on simple daily windows (keeper at night, town workers by day). Their
  absence does not close a shop, prevent a conversation goal or affect progress.
- Supply **aggregate** `active = focused && appActive && !covered && !napping`,
  and the real Quiet-view value. Inactive or Quiet returns an empty, zero-clock
  plan. Reduced motion returns the same selected scene as **still** art, with zero
  frames/remaining duration; use a visible rest pose at each anchor, not a particle
  opacity formula that happens to be zero on frame zero.
- The budget caps a zone at 24 emitters (32 in Neon/Skyport), two residents,
  12 updates/second, and one **18-second batch**, then still. A kind gets at most
  four slots, rain twelve, so rain cannot consume all slots. These are conservative
  engineering ceilings, **not measurements of phone RAM/FPS**. Claude owns the
  visual density decision; adjust the pure budget with tests if it is too sparse.
- Keep monotonic `elapsedMs` anchored to this batch, even when the store's `now`
  ticks or weather changes. Never reset it on every render, start a catch-up loop,
  schedule a return notification, or replay a queue after an absence. Cancelling
  focus/activity must cancel the renderer's real clock immediately. A new explicit
  visit can start a fresh finite batch; nothing is granted for watching it.

The module returns a plan, not a timer or a native frame scheduler. Actual finite
motion and frame-rate enforcement still require renderer wiring in Claude's lane.
Do not interpret unit tests as evidence that the current UI already honours it.

## Feedback for Claude

On `df61cf4`, AtlasWalk passes `active && !reduced` to ZoneLife/ZoneResidents,
where `active` is `useAppActive()`, not tab focus or sheet coverage. The new
WorldWindow used in Shop/Arena also has no eligibility prop. Both life components
currently call `withRepeat(..., -1, ...)`; inactive particles disappear rather than
retaining a reduced-motion still. Please wire the aggregate eligibility and finite
plan into these visual files, including tab changes and covered world windows.
This is a **source observation**, not a browser/native background measurement.

## Verification boundaries

The test executes the actual pure `zoneEmitters` catalogue slice through a TypeScript
VM boundary, freezes its candidates, and exercises all current zones (plus the garden),
all four daily phases, five season choices, three weather choices, inactive/Quiet,
reduced motion, finite expiry, duplicate/off-map candidates and immutable routes.
Existing region-walk tests validate all resident routes against generated geometry.
No visual file is imported at runtime by the new module.

Screenshot main still waits for an old Missions title. Its existing repair is in
PR #18, not duplicated here. C21 stays draft until final matching checks and the
handoff gaps are clear. No physical phone, native runtime, live multiplayer,
screen-reader/audio output or measured performance testing is claimed.
