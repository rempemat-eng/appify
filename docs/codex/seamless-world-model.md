# C20: seamless-world engineering foundation

Base: `f962275a56803f7d3ca0414696d2970bc18ee123`, 18 October 2026.
This is a **draft foundation**, not completed C20 or a shipped renderer change.
It reuses Claude's current `region-walk`, `world-places` and optional `world`
save. It does not resurrect superseded PR #19, edit artwork/screens, change
rules or rewards, write player data, or introduce a second zone catalogue.

## Model API

`lib/world-travel.ts` provides:

- `mountedNeighbours(region, here, view)`: the current tile and the viewport-aware
  preload neighbourhood, matching AtlasWalk's diagonal-inclusive policy. Pass
  the current screen `width`, `height` and pixel `scale`; wide/tall screens can
  need tiles beyond the old 3x3 set. Unknown tiles return none; distant regions
  never become foot neighbours. Invalid or non-finite dimensions fail explicitly.
- `regionEdges(region)`: each generated east/south adjacency once, including
  negative layout coordinates and singleton regions with no invented exits.
- `cameraOffset(region, point, view)` and `screenToWorld(...)`: the existing
  region-wide camera formula, including the place card's `focusY` and
  `padBottom`. Regions smaller than the available view are centred; the bottom
  place-card clearance is excluded when centring vertically. Larger regions
  stay clamped to their bounds. The output is continuous, not reset to local tile coordinates.
  Pixel snapping remains the renderer's responsibility. Invalid sizes, scales,
  non-finite coordinates and padding fail explicitly.
- `idleJourney`, `beginJourney`, `cancelJourney`, `finishJourney` and
  `skipJourney`: ephemeral, identity-checked tickets using current generated
  stations. No timers, animations, navigation, currency or save writes happen
  inside the model. Natural completion consumes one leg; SKIP consumes the whole trip.

The caller must assign the returned state **before** applying an arrival:

```ts
const result = finishJourney(current, capturedTicket, liveEligibility, savedWorld);
current = result.state;
if (result.arrival) applyArrival(result.arrival);
```

`liveEligibility` supplies the current region and the existing focused, active,
awake and not-busy guards. Cancel on Back, blur, background, unmount or a
different navigation. A callback from an old trip cannot complete or cancel a
new one, even when the destination is identical or a screen has remounted.
Tickets are not serialized. A successful arrival returns the current WorldSpot
shape and keeps the visited history through the existing `moveTo` function.

## Per-leg cancellation (Claude's 18 October feedback)

The route is copied from `travelRoute(from, to)`, never a second transport
catalogue. A ticket has the trip's origin `from`, final `to` and station `at`,
its frozen `legs`, and current `leg`. The scene stays in the origin region
until the final arrival, matching current World behaviour.

- **Natural completion:** `finishJourney` advances one leg with a fresh ticket
  identity and no arrival. Only the last leg returns a WorldSpot.
- **SKIP:** `skipJourney` consumes the current leg and returns one arrival at
  the final destination, including from the middle of a five-leg trip.
- **Whole-scene exit:** cancel unconditionally on Back, blur, background, a nap,
  battle or other navigation. Both completion paths also recheck live eligibility.
- **Leg cleanup:** use `cancelJourney(liveState, capturedTicket)`. Cleanup from
  an already-consumed leg cannot cancel a newly mounted leg or replacement trip.
- A copied ticket, previous leg, replaced trip or remounted scene cannot advance,
  arrive, or cancel the current one. Returned visit history is detached from the
  saved array; no decision mutates a save or grants anything.

Publish returned state into a **synchronous live ref before** React state,
arrival effects or mounting the next leg. React setState by itself is not an
exactly-once guard: two callbacks can run before the next render. Always pass
that live state and freshly read focus/app-active/awake/not-busy eligibility to
the model, never a closure's stale state or eligibility. A leg effect retains
its own captured ticket. Use a caller-local trip generation plus leg as the
component key; `key={leg}` alone cannot distinguish two replacement trips both
on leg zero. These identities are ephemeral, never serialized.

The model tests all **42 station pairs / 100 authored leg positions**: natural
completion, leaving, each disabled-eligibility cause, old cleanup, copied tickets,
same/different destination replacement, remount, SKIP-first and timer-first,
duplicate completion, unchanged history and one whole-trip arrival. These are
pure-model tests, not real React/native lifecycle coverage.

### Feedback for Claude: the screen still needs wiring

On the base above, a source-boundary diagnostic of the actual Journey and
World callbacks accepts a queued completion after leaving, and inactivity
advances a leg. A specific ordering queues runOnJS(finish), performs unmount
cleanup, then flushes the queued JS: an arrival is still accepted. Cancelling
an animation or timeout does not invalidate work already queued on JS. The
renderer needs the per-leg ticket/live-ref contract and an effect-generation
guard invalidated on cleanup. Do not just set the old done ref in cleanup
without handling effect reruns and replacement identity. Claude owns these
screen/component files; this PR deliberately does not edit them or claim a
shipped fix. The diagnostic was a substituted hook/worklet boundary, not an
observation of physical-device timing.

The rebase preserves `battlePlace`, regional battle yards and journey layers,
`zoneFrames`, floating/turning props, twinkling stars, the garden-view harness's
journey-assets stub and `art:sheet`. It also preserves the companion riding on
journeys, the compact change-of-line label, hearth frames and ground shadows.
No battle or reward rule changes.

## Wide-screen compatibility (18 October follow-up)

Claude's main now centres small regions and mounts the full visible area.
The previous model failed its actual-camera worklet assertion on this source;
its old 3x3 preload could omit visible tiles at 768 px and wider. The pure
helpers now follow that current policy, not the retired top-left camera.

Tests cover 320, 402, 768, 1363, 1920 and 2560 px widths, 640 and 1600 px
heights, three scales and both ordinary and raised-card views. They execute
the actual camera, preload and native/web tap-conversion bodies at substituted
boundaries, check equal margins for small/singleton regions, keep every visible
authored tile mounted, and leave the generated maps unchanged. No source
boundary is proof of real React layout, image loading or device performance.
The tap model intentionally follows the renderer's unsnapped camera inversion;
the visual transform rounds to a device pixel, just as it does on main.

### Feedback for Claude

When adopting the preload helper, pass the live viewport dimensions and scale
as its third argument. The model does not impose a new image budget or remove
the existing forest filler. Border semantics/bitmap checks and the actual
journey cancellation wiring below remain outstanding. This compatibility fix
does not mark those parts done.

## Border coverage, without false visual approval

`npm run check:zone-borders` runs negative fixtures and inspects actual
neighbours using the combined regional walk grid, including the garden's gate
and trail openings. All **15** current physical borders have at least one shared
open crossing. Different fence sides and props mean the two walk-mask edges do
not always match. A walk mask cannot tell grass, a road or water apart.

Current coverage is **0/15 semantic terrain borders verified**. Neither current
generator exports the semantic terrain grid needed for this comparison. The
checker says so explicitly. `node --import tsx scripts/check-zone-borders.cjs
--require-terrain` fails on missing coverage. It does not read or approve PNG
pixels, road alignment, material blending, snow placement or visual quality.
Full bitmap-strip checking remains part of unfinished C20.

### Feedback for Claude: generator contract requested

Please export, in your generated files, at the existing walk-grid resolution:

1. `gardenTerrain: readonly string[]` from `lib/garden-map.ts`.
2. `zoneTerrain: Record<ZoneId, readonly string[]>` from `lib/zone-maps.ts`.
3. Optionally `zoneBorderBlends`, keyed by `region:left/right` or
   `region:north/south`, containing explicit pairs of one-character terrain
   codes allowed to meet at that specific seam. For example, the physical
   garden-to-town seam key is `valley:garden/town`.

Rows must have the same dimensions as each tile's walk grid, with one shared
ASCII code per cell for each semantic surface. Define the palette in the
generator so both sides use the same meaning. Matching codes pass; undeclared
differences fail with the edge-cell index. A deliberate woodland/grass blend
can be declared for that seam without silently accepting road-to-water gaps
elsewhere. The checker validates malformed metadata, even if its counterpart
is still missing. No generated file was changed by Codex.

## Renderer handoff, still required

Claude can replace the corresponding inline camera/neighbour calculations in
`components/atlas-walk.tsx` with the tested functions. Keep current pixel
snapping, night art, reduced motion and pause behaviour. This PR does not wire
the helpers or claim that source assertions prove real React scheduling.

Source observation: `components/journey.tsx` currently calls `finish()` when
the app becomes inactive, and the World arrival callback reads its captured
trip without a new focus/activity check. The new ticket model supports safe
cancellation instead. Please wire the existing route/scene guards in your
lane, then test background, Back, remount, rapid replacement and skip/timer
races in the actual screen. These behaviours are not fixed in the renderer by
this PR and have not been tested on a native device.

## Verification and remaining gates

The model checks current layouts, every physical border,
320 through 2560 px camera windows, scales, card padding and all 42 distinct station
pairs. A substituted source boundary executes AtlasWalk's actual camera
worklet, preload and tap bodies and compares their results with the model, so the two cannot
silently drift while renderer wiring is pending. Border fixtures cover blocked crossings, road-to-water gaps, explicit
blends, malformed grids and strict missing-export failure. These are pure/source
checks, not a visual or native test. `check:world` remains in the full check list.

Main still has the retired Missions screenshot heading. The already-reviewed
repair lives in C9 PR #18 at `02ce05f`; it is not duplicated here and no C9
feature is pulled into this branch. Until that test-only repair reaches main,
the matching Screenshots workflow is expected to fail its old heading selector.
Report its actual result rather than treating old green C9 CI as this PR's CI.

Keep C20 **taken/draft** until semantic exports and full border coverage are
available, renderer integration is reviewed, and final-source verification and
matching CI pass. Exact tested source, CI and preview coverage belong in the PR.
No physical-phone, native compilation/runtime, live backend/multiplayer, audio,
screen-reader or measured RAM/FPS coverage is claimed.
