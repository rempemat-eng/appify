# C27: named circuits on the real walk grids

Scope: `scripts/check-world-circuits.cjs`, exposed as `npm run check:world-circuits`
and appended to the existing `check` / `verify` chain. No runtime, art, save,
gate, economy or reward changes. Baseline: main
`18a8bef77d79bb81163ada1df038fbb3ce6477df` (21 October 2026).
The existing `check:world-routes` still runs lane G's route-graph tests in
`lib/world-routes.test.ts`; this circuit check is separate and preserves it.

## What is checked

The script transpiles and executes the actual image-free `region-walk.ts`,
`garden-path.ts`, `garden-map.ts` and `zone-maps.ts`, including their actual pure
`world-flag`, `world-flag-default`, `world-walk` and `world-canvas` imports. The
flag uses the committed default, without a browser override or substitution.
No movement helper is reimplemented or mocked. Names describe the itineraries; coordinates,
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

The scope is **23 named locations in seven itineraries**, within the current
36-zone corpus (the garden is an additional location). It does not claim every
zone or standing point is covered. All **54 directed legs** pass on the baseline,
including reverse walks.
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

Five loader controls reject a visual component, generated asset imports, the
browser flag sibling, parent-directory traversal and a Node built-in. The real
pure imports execute unchanged; widening the allowlist does not permit UI,
image or network substitutes.

## Feedback for Claude / integration

No failing named edge was found in current exported grids. Please retain
`check:world-circuits` alongside the current checks when integrating the shared
package check list, including lane G's existing `check:world-routes`. The
current-main package conflict is resolved with only the new command and one
additive check-chain entry; no dependency or existing check changes.

This is **movement-grid connectivity**, not proof of the artwork's physical
logic. A walkable bridge may still lack drawn supports; painted rails may still
miss a station; a climate seam may still look wrong. C23 needs the richer semantic
exports to certify those, and the stitched-render/browser review remains
separate. A named circuit passing is not approval for every door, interaction,
prop, alternate path or region, and not proof of tap/key delivery, navigation
ownership or camera continuity in React.

Passing these checks adds no unlock, reward, travel cost or shortcut. No player
save or account is read. Claude's 21 October action-RPG redesign (#223) is a
separate draft; these checks certify current exported movement grids, not its
future combat spaces, landscape framing, quest gates or save migration.

## Validation boundaries

Ran: targeted circuit check (15 map controls, 5 loader controls, 7 itineraries,
54 directed legs), plus the unchanged route-graph check;
final-source full `npm run verify` and formatting/whitespace checks (results
recorded in the PR with the exact published source and matching CI).
Not tested here: new browser play-through, manual stitched artwork review,
physical rail/bridge/door geometry, runtime input/navigation/camera lifecycle,
native runtime, phones, backend or multiplayer.
