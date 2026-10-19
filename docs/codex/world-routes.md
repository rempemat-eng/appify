# C27: named circuits on the real walk grids

Scope: `scripts/check-world-routes.cjs`, exposed as `npm run check:world-routes`
and appended to the existing `check` / `verify` chain. No runtime, art, save,
gate, economy or reward changes. Baseline: main
`0798b8287dbd1a70617183b2ca1bd5f7d203121d` (19 October 2026).

## What is checked

The script transpiles and executes the actual image-free `region-walk.ts`,
`garden-path.ts`, `garden-map.ts` and `zone-maps.ts`. No movement helper is
reimplemented or mocked. Names describe the approved itineraries; coordinates,
tile extents, cell size, garden opening rules, combined walk rows and port spans
come from current exports, not the old tilt-view dimensions.

| Itinerary         | Ordered zones                                          | Representative standing points               |
| ----------------- | ------------------------------------------------------ | -------------------------------------------- |
| Valley west loop  | garden → woodland → halt → town → garden               | start, clearing, platform, well              |
| Valley east loop  | garden → riverside → park → town → garden              | start, mill, fountain, well                  |
| Valley coast loop | town → park → headland → harbour → town                | well, fountain, tower, market                |
| Frostline loop    | ridge → hollow → snowmelt → saddle → ridge             | tarn, clearing, shore, fork                  |
| Summit spur       | saddle → summit → saddle                               | fork, scope                                  |
| Sunstone traverse | oasis → gulch → scorch → hearthold → caldera → springs | pool, street, track, courtyard, forge, pools |
| Isles loop        | landing → rainforest → headwaters → cove → landing     | pier, bridge, pool, beach                    |

All **54 directed legs** pass on the baseline, including reverse walks.
Each consecutive pair must share an actual tile edge and a positive declared
port. Each named standing point must itself occupy an open cell: the normal
pathfinder's nearest-walkable tap adjustment must not hide a blocked destination.

For each leg, every third zone is masked out. The actual `makeWalkGrid.findPath`
must therefore cross the intended seam, rather than pass a closed edge by
walking round another side of the circuit. The thinned route is expanded cell
by cell: every step is open, diagonal turns cannot cut blocked corners, the
crossing lies inside its declared port and the endpoint is the exact target
cell. Joining the legs at the same named point establishes the ordered circuit.
This adds a different guarantee from the existing region-wide stand-reachability
test, which intentionally permits any route through the region.

## Negative controls

**15 controls** exercise the same auditor: a good seam in both directions;
a blocked seam that is still reachable by a third/fourth-zone detour (control
proves global reachability), rejected in both directions; blocked start and
target cells; an out-of-map point; closed or missing port; a crossing outside
the declared span; a missing named stand; nonadjacent itinerary zones; a
diagonal-only corner touch; and malformed walk rows. A production failure exits
nonzero and lists the itinerary, region and directed edge for Claude.

## Feedback for Claude / integration

No failing named edge was found in current exported grids. Please retain
`check:world-routes` alongside the C22/C23/C24 additions when integrating the
shared package check list; do not replace that list from an older branch.
This PR includes none of those unmerged source changes.

This is **movement-grid connectivity**, not proof of the artwork's physical
logic. A walkable bridge may still lack drawn supports; painted rails may still
miss a station; a climate seam may still look wrong. C23 needs the richer semantic
exports to certify those, and the stitched-render/browser review remains
separate. A named circuit passing is not approval for every door, interaction,
prop, alternate path or region, and not proof of tap/key delivery, navigation
ownership or camera continuity in React.

Exploration remains optional and free under the existing gates. Passing these
checks adds no unlock, reward, travel cost, absence penalty or mission shortcut.
No player save or account is read by this script.

## Validation boundaries

Ran: targeted route check (15 controls, 7 itineraries, 54 directed legs);
final-source full `npm run verify` and formatting/whitespace checks (results
recorded in the PR with the exact published source and matching CI).
Not tested here: new browser play-through, manual stitched artwork review,
physical rail/bridge/door geometry, runtime input/navigation/camera lifecycle,
native runtime, phones, backend or multiplayer.
