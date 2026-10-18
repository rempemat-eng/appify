# C20: seamless-world engineering foundation

Base: `de010bed9f9794195969c5fef3a93530e28ccdaa`, 18 October 2026.
This is a **draft foundation**, not completed C20 or a shipped renderer change.
It reuses Claude's current `region-walk`, `world-places` and optional `world`
save. It does not resurrect superseded PR #19, edit artwork/screens, change
rules or rewards, write player data, or introduce a second zone catalogue.

## Model API

`lib/world-travel.ts` provides:

- `mountedNeighbours(region, here)`: the current tile and its eight possible
  neighbours, matching AtlasWalk's existing diagonal-inclusive policy. Unknown
  tiles return none; distant regions never become foot neighbours.
- `regionEdges(region)`: each generated east/south adjacency once, including
  negative layout coordinates and singleton regions with no invented exits.
- `cameraOffset(region, point, view)` and `screenToWorld(...)`: the existing
  region-wide camera formula, including the place card's `focusY` and
  `padBottom`. The output is continuous, not reset to local tile coordinates.
  Pixel snapping remains the renderer's responsibility. Invalid sizes, scales,
  non-finite coordinates and padding fail explicitly.
- `idleJourney`, `beginJourney`, `cancelJourney`, `finishJourney` and
  `skipJourney`: ephemeral, identity-checked tickets using current generated
  stations. No timers, animations, navigation, currency or save writes happen
  inside the model. Skip and natural completion consume the same ticket once.

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

The model has 1,572 assertions over current layouts, every physical border,
320/402/768 px camera windows, scales, card padding and all 42 distinct station
pairs. A substituted source boundary executes AtlasWalk's actual camera
worklet body and compares its snapped result with the model, so the two cannot
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
