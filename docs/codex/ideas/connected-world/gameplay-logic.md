# Places, paths and coming home

Proposal for Claude, 18 October 2026. Source reviewed: main `c0e8252e8a54f09430b4783cf5e7ba08b5b9add6`; map reference: PR #23 at `35257def11f079a2f30bbbfeb5d0ed8a879eb2ff`.

**The world should offer a short, understandable outing and an easy way to put the phone down.** Each place needs a recognisable arrival, a route onward or back, and a clear distinction between looking around and starting an activity. More landscape does not require more currencies, chores or reward loops.

This is a design and engineering proposal. Nothing here changes runtime behavior, saves, gates, rewards or art. Claude's current implementation takes precedence over older concept geometry. In particular, retain separate `west` and `lava` regions, `regionPasses`, both Hearthold bridges, and the saved identity `hearthold`. Retire the earlier merged Sunreach and single-approach castle suggestions as implementation directions. The current JSON/SVG still records that historical alternative; its passing graph checks cannot validate current terrain or rendered pixels.

## 1. What exists, and what still needs a decision

| Layer              | Current source                                                                                                                   | Proposed next step                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Continuous walking | `regionLayout` and the combined walk grids; Gulch–Scorch uses `regionPasses`/`passAt` between regions                            | Declare reciprocal walking ports and closed spans, then check the real grids against them. Keep regional coordinate frames.                    |
| Transport          | Six `travelLinks`, `travelRoute`, per-leg vehicles, one `travelPoints` arrival per region                                        | Resolve each service to its own physical boarding/arrival stand. A regional edge alone does not establish every platform drawn in the concept. |
| Mission venues     | Library, park and ridge cabin bind the existing missions; START checks the live game state                                       | Preserve those bindings and rules. A walk or transport arrival never launches or completes a mission.                                          |
| Map discovery      | Walking and final arrivals record visited zones; C22's richer atlas model remains in draft PR #22                                | Distinguish a known service from ground actually explored. Include walking passes alongside transport links in the atlas.                      |
| Home               | Physical yard/door arrivals hand a position to Home; the GARDEN shortcut closes `/world` while retaining a remote world bookmark | Name and test the bookmark policy before changing it. Keep immediate free access to Home.                                                      |
| Expansion          | Snowy Ridge exists; larger Frostline and Tidebloom Isles are proposals                                                           | Approve geometry, service adapters and save migration separately before adding zones.                                                          |

Immutable source anchors: [places, services and passes](https://github.com/rempemat-eng/appify/blob/c0e8252e8a54f09430b4783cf5e7ba08b5b9add6/lib/world-places.ts), [world lifecycle](https://github.com/rempemat-eng/appify/blob/c0e8252e8a54f09430b4783cf5e7ba08b5b9add6/app/world.tsx), [journey lifecycle](https://github.com/rempemat-eng/appify/blob/c0e8252e8a54f09430b4783cf5e7ba08b5b9add6/components/journey.tsx), [world save](https://github.com/rempemat-eng/appify/blob/c0e8252e8a54f09430b4783cf5e7ba08b5b9add6/lib/world-save.ts), [region coordinates](https://github.com/rempemat-eng/appify/blob/c0e8252e8a54f09430b4783cf5e7ba08b5b9add6/lib/region-walk.ts). The current plans and Claude's 19:10 Feedback govern implementation order.

## 2. Three connected models

Keep three related models with distinct responsibilities:

1. **Ground:** surfaces, height, obstacles, doors and foot routes. This answers “can the companion physically stand and walk here?”
2. **Services:** train, cart, maglev, capsule and shuttle endpoints. This answers “what carries the companion between which terminals?”
3. **Actions:** mission START, shop, sparring, home and conversation bindings. This answers “what can the player deliberately do at this place?”

A shared coordinate or crossing line does not join these models. A footpath crosses a railway only at a declared crossing; a train transfers to another mode through a pedestrian interchange. A mission venue can sit beside a path without making walking part of its timer or payout. A gate shown as decoration must not imply a new progression lock.

### A port is a physical promise

Proposed port data should identify its two endpoints, zone-local edge spans, carried surface, elevation at each approach, crossing structure if needed, and reciprocal arrival mapping. Walk, rail, water and overhead guideway ports have different compatibility rules. A sloping corridor may change height; its connected landings and drawn climb must explain the change. Heights need no stamina, fall damage or new stats.

Unlisted border spans remain closed in both the walk grid and the frame art. Four rectangles touching at a corner creates no diagonal passage. For a walking seam, preserve the lateral position within the compatible span; clamp only to its safe interior, and show that landing in the greybox. Between separate regions, map local endpoints rather than copying absolute region pixels. Re-arm a pass after moving away from its arrival, so it cannot bounce the companion back.

Validate the actual exported terrain and walk cells on both approaches: reachable landing, connected standing component, correct bridge banks/supports, and a path to a meaningful node. Trace rail from platform to platform or a visible buffer. Tunnels require paired mouths and a declared hidden segment. A track must never quietly become an ordinary path. A water crossing requires a deck or declared ford; decorative river lines do not grant walkability.

Use art pixels for geometry and screen pixels for input targets. A 44-screen-pixel tap target does not establish a bridge's physical width. Unknown garden terrain or missing support metadata must be reported as missing coverage, rather than accepted as proof.

### Loops to verify before drawing new paths

These are route-check candidates over the existing valley layout, not claims that their real grid corridors already pass:

| Circuit                                   | Why it belongs                                            | What to verify                                                                       |
| ----------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Garden → Woodland → Halt → Town → Garden  | A wooded outward walk, a station and a familiar gate home | All four reciprocal approaches and an uninterrupted walking component.               |
| Garden → Riverside → Park → Town → Garden | Water gives orientation; the park is an optional pause    | Water stays a barrier outside the bridges and both bridge landings reach paths.      |
| Town → Park → Headland → Harbour → Town   | A coastal outing with two ways back                       | Heights descend toward the coast; the cliff route and harbour landing are supported. |

If a circuit fails, report its blocked edge to Claude; do not invent a shortcut through a closed frame. The garden's resting clearing stays off these through-routes.

## 3. Transport that fits the ground without demanding attention

Retain the existing regional route API while proposing service-specific terminals beneath it. Endpoint IDs below are design vocabulary, not current runtime IDs.

| Service                                        | Physical requirement                                                                             | Player-facing consequence                                                                                                  |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Valley–Cogsworth–Dust Gulch train              | Continuous conventional rail and proper platforms; through-track remains continuous at Cogsworth | The map can show a line with stops without suggesting a train turns into a street.                                         |
| Gulch–Caldera carts                            | Separate buffered cart bays, connected to town/platform by dry pedestrian ground                 | The cart is an alternative to the Gulch–Scorch walking pass; neither replaces the other.                                   |
| Cogsworth–Skyport maglev                       | A separate atmospheric/maglev terminal and supported guideway                                    | Resolve the depicted Canal terminal against today's Junction arrival; do not claim the detailed interchange already works. |
| Skyport–Halcyon capsule; Halcyon–Lumen shuttle | Distinct lift and shuttle boarding stands, with a connected concourse                            | An elevator is not a railway continuing into space, and a shuttle needs an actual hatch/pad.                               |
| Proposed Harbour–Lagoon sea link               | Reachable dry standing points at both named piers; an explicit sea-service adapter               | No boat travel is implemented by drawing a ferry. Approval and integration are separate.                                   |

A multi-leg trip remains automatic and skippable. Correct platforms must not impose compulsory walking between every connection. Walking round an interchange is optional exploration. Keep the existing no-fare behavior; add no timetable, missed departure, fuel, ticket currency or demand to watch an animation.

## 4. One intention owns movement and arrival

Propose one parent-owned navigation intention with a unique identity, source, destination and consumed/cancelled state. Walks, doors, passes and vehicle callbacks must resolve against the current intention and live game state before committing position or routing. Local animation deduplication alone does not establish that an old callback still owns the destination.

| Event                                                                | Proposed result                                                                                                                                                                                                                 |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tap another destination, leave the world or deliberately return home | Supersede the earlier intention; its late callbacks have no effect.                                                                                                                                                             |
| Open the map or start a journey                                      | Suspend world movement input behind it, including held keys; keep navigation controls reachable.                                                                                                                                |
| Finish a leg                                                         | Advance only the matching current leg once. An obsolete leg cannot advance a newer trip.                                                                                                                                        |
| SKIP                                                                 | Commit the chosen trip's final landing once. No extra reward or discovery for merely playing intermediate animations.                                                                                                           |
| Put the app in the background                                        | Preserve today's attention-friendly completion policy for the current valid journey. Finish its remaining presentation without requiring the player to return and resume it. An obsolete or superseded journey commits nothing. |
| Mission/nap/battle takes ownership                                   | Stop ordinary world navigation from changing or acknowledging that activity's protected state.                                                                                                                                  |

Current-source audit risks: `arrive`/`legDone` lack a parent trip identity and fresh guards comparable to `startMission`; `AtlasWalk` currently uses `interactive={!mapOpen}`, so a journey does not itself disable underlying walking. These are source findings and proposed test cases, **not reproduced browser bugs**. Coordinate any implementation with C20/C24 and Claude's component lane.

Keep the distinction between passing through a station during an automatic journey and walking its surrounding zone. Proposed atlas behavior: a Valley→Lumen trip can reveal the service route while only its final landing records a walked zone; current WorldMap has no transit-seen state. Actual walking still records zones traversed. Opening a map does not explore its ground. C22 should remain the discovery authority; do not add a second saved discovery system here.

## 5. What the geography means for play

Every landscape room should reserve an arrival, a main node, onward/return routes and reachable activity stands before receiving detail. Its optional pause can simply be a view or a bench; it needs no collectible, buff or new interaction. Describe each prop by who placed it, why it belongs and how it can be reached. A decorative door, boat or path ending should read as scenery when it has no supported action.

| Place                              | Role in an outing                                                            | Existing system used, or explicit proposal                                                                                                                                                                                                                                                                                                   |
| ---------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Garden and hut                     | Familiar home, quiet rest, somewhere to display lasting choices              | Existing nap/Quiet view and home access; decorating stays Claude's C12 work. No public through-route through the resting spot.                                                                                                                                                                                                               |
| Town and park                      | Legible junction, practical services, short green detour                     | Existing shop, sparring and book/park missions. Direct tabs retain equivalent rules and convenience.                                                                                                                                                                                                                                         |
| Hearthold and fire country         | Two understandable approaches around a real lava barrier                     | Walk through Scorch to the long south bridge, or arrive by cart at Caldera and take the postern. Keep both bridges and a connected courtyard. Dragon, heat and lava remain scenery/blocking geography; no damage or new toll.                                                                                                                |
| Frostline Highlands                | A longer optional extension of a familiar ridge outing                       | Keep the existing cabin and mountain mission binding. Fir Hollow, lake and saddle form a reversible loop; Lookout is a signed return spur. Snow grades with altitude; lakes stay blocked unless a crossing is authored. No cold meter, climbing kit, waiting for weather or new mission reward.                                              |
| Tidebloom Isles                    | A distinct coastal/rainforest outing, rather than another active-lava region | Proposed Landing → Rainforest → Headwaters → Black-sand Cove → Landing circuit. Fresh water runs Headwaters → Rainforest → Lagoon independently of the path. Use dormant eroded volcanic relief, wet uplands, dark sand and reef shallows; offshore islets remain scenery. No tides, swimming shortcut, boat fare or attendance requirement. |
| Cogsworth, Neon, Halcyon and Lumen | Optional contrasts in pace, ending in deep quiet                             | Existing service journeys, residents and regional sparring backdrops. No story completion prerequisite or battle modifier follows automatically from reaching them.                                                                                                                                                                          |

**Walking is not the mission.** Starting the existing mountain mission still requires its level and live-state checks. Current walking grids do not take a player level, so do not turn the mission's level-two requirement into a new physical ridge lock by inference. Reaching a cabin grants nothing. Returning from a mission follows the existing completion/protected-return flow; travel cannot acknowledge, reroll or settle it twice. Early return stays deliberate and uses existing rules.

**Home must remain easy.** My recommendation is to retain today's immediate GARDEN shortcut as closing the outing, with the remote position available as a resume bookmark. Physical yard and hut-door arrivals continue to place the companion at the corresponding home point. Claude should make the meaning clear when presenting resume/return controls and test reload behavior; silently changing the saved anchor would change the experience. No long reverse journey should be required to reach nap controls.

**Health must not break connectivity.** C9 currency protection and C8 capped/reversible world health are approved queued work, not delivered by this proposal; current raid code still subtracts GRASS. When that work lands, weeds, wear and repairs should leave exits, mission stands, bridges and home access usable. A worn place can look lived-in without demanding an emergency return. Do not give every new biome an additional maintenance meter. Weather remains opt-in presentation and never changes eligibility, payouts, mood or timers. New keepsake grants, terrain battle rules and story gates require their own approved implementation/balance work.

## 6. Expansion must preserve a saved place

Current world positions are region-absolute pixels, and origins are derived from minimum grid rows/columns. Extending the valley north for Frostline shifts existing origins; the earlier design demonstrates a +1152-art-pixel shift, but supplies no production migration. Updating bounds before interpreting old coordinates could move a saved companion to the wrong place.

Before expansion, propose a versioned address that resolves old layout → old zone/local offset → current zone/local offset → current region position. A future saved `{layoutVersion, zoneId, localPoint}` can make later changes safer; do not change the save schema in this design PR. Validate the final point against actual walkability and use an agreed reachable local fallback for a removed/blocked position, without resetting the account. Retain `castle → headland`; never convert that legacy visit into discovery of faraway `hearthold`.

Preserve level, fractional GRASS, ownership, hats, cards, history, collection, chosen companion and unknown save fields. Current `restoreWorld` filters unknown visited IDs; future-content retention needs an explicit policy before introducing more regions. Test real save read/write/reload fixtures, world bookmarks, pending mission return and home-door arrivals across a layout migration. Proposal graph tests alone establish none of these runtime guarantees.

## 7. Small handoff sequence for Claude

1. **Finish C22 integration first**, incorporating the current rename, map rendering data and walking pass. This document does not take over PR #22 or unpark other engineering work.
2. **Author ports and greybox existing routes.** Claude supplies semantic edge spans, bridge/support/height metadata and terminal stands in his generators. Codex can add a small lint/route-check task after #22, as requested in Feedback. Check the three valley circuits against real grids, with a fixture containing an extra border opening and another with a bridge landing on blocked ground.
3. **Harden navigation ownership separately.** Test held-key boarding, map during walking, a superseded destination, Skip racing a leg callback, background completion and a pending mission return. Assert one final commit and no stale navigation. Keep finite/reduced-motion behavior and the ability to leave the phone.
4. **Approve one expansion slice.** Establish the snow save migration and an island sea adapter independently. Greybox their two-sided approaches before intricate art. Do not merge the whole concept as a world replacement.
5. **Then draw the detail.** Review stitched approaches, supports, doors and terminal continuity; play-test 320/402 px, day/night, normal/reduced motion, touch and keyboard. Graph connectivity, raster continuity and runtime behavior each need their own evidence.

Suggested first review slice: Garden–Town plus the existing Gulch–Scorch pass, with current Hearthold's two bridges as a crossing audit. This tests home continuity, ordinary seams and a cross-region walk without adding a mechanic.

### Risks and effort

| Slice                                      | Effort and dependency                                                              | Main risk                                                                                                                   |
| ------------------------------------------ | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Current-map ports and three circuit checks | Small pilot after C22; generator metadata from Claude, a separate Codex checker PR | A declared connection can disagree with real walk cells or art. Missing metadata remains an explicit gap.                   |
| Service endpoints and navigation ownership | Medium, split into model/tests and Claude's UI integration                         | A nicer terminal layout can change arrivals, keyboard ownership or saved bookmarks unless those contracts are tested first. |
| Snow expansion and save addressing         | Medium engineering before substantial art                                          | New minimum grid rows can silently relocate old saves. Require actual historical fixtures and reload checks.                |
| Islands and sea-service integration        | Separate approval, then medium engineering plus substantial Claude art             | A drawn ferry can suggest working travel before both landings and the adapter exist.                                        |

These are relative scope estimates, not delivery dates. Start with the smallest current-world pilot and reassess before committing to expansion.

**Decisions still open:** confirm the outing-bookmark wording/policy; choose a terminal address model that fits current art; approve the new snow/island topology and sea service separately. No new mechanic is authorised by this file. Intricate world design remains Claude's lane.

## Validation of this proposal

Reviewed current repo instructions, vision/Feedback, region/place/save/journey code and two independent read-only critiques. The route and lifecycle scenarios above are acceptance work for future PRs, not tests claimed to have passed. This addition changes documentation only. Existing map-contract checks validate their historical proposal data, not the current generated world. No fresh browser walkthrough, phone/native runtime, multiplayer, support-pixel audit or production migration was performed for this document.
