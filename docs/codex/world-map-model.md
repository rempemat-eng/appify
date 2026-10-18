# C22: discovery atlas model

Engineering only, based on main `6cd82804e8436fb0e4ef3f7b4b2f2a98ef764d49` and the approved C22 queue. Claude owns the map screen. No game-rule, reward, cost, navigation, drawing or terrain changes.

## Screen handoff

`buildWorldMap({ world, mapSeen, current })` returns detached `nodes`, zone-to-zone `links`, one nullable `suggestion` zone ID and a `visitedSnapshot`. Use `gameStore`/`useGame`'s current `world` and `mapSeen`.

- On the garden/Home screen, pass **`current: 'garden'`**. The saved world spot intentionally remains the resume position when `◀ GARDEN` returns Home; it is not necessarily the active screen.
- In World, pass its live `{ region, x, y }`. Omitting `current` uses the saved spot, falling back to the garden for a first account. Invalid explicit positions produce no current marker/suggestion.
- Capture the result when the map opens. Show its new flags, then call **`markWorldMapSeen(captured.visitedSnapshot)` once per deliberate opening**, not on every render, selector read, frame or walk. The action is idempotent and saves locally. Keep the captured result for that opening if the UI should display what was newly discovered.
- The action never sweeps the latest visited list: a visit made after this snapshot stays new. It cannot acknowledge unknown/unvisited places. No timer, deadline, streak, percentage, daily badge or demand to return is added.

Nodes have stable namespaced IDs (`region:valley`, `zone:town`, `station:valley`), a `kind`, `region`, optional `zone` and `unseen`/`visited`/`here` state. `unseen` means draw an outline, not locked or inaccessible. Zone `col`/`row` come directly from the generated region layout (possibly negative), not old tilted-view or screen coordinates. Labels/art remain Claude's concern.

Region state aggregates its zones; `here` takes precedence. A station is considered discovered when its zone was visited: the current save has no finer station-interaction history. A station is `here` only within the existing `PLACE_RADIUS` of its authored stand, not anywhere in its zone. `isNew` aggregates unacknowledged discoveries and is independent of `here`. The garden is already known. A valid saved position is known even if an old visited list omitted its own zone. A live unsaved location is shown ephemerally; rendering never writes it into saved history.

## Topology, not travel permission

Current data gives 8 regions, 20 zones and 7 stations. Edges join zone IDs and distinguish adjacent grid `border`s, existing transport `line`s and the hut `door`. There is **no hut train station**: all seven transport regions connect through `travelLinks`, while `home` joins the valley through the existing door. Every zone joins this schematic graph.

The suggestion uses breadth-first schematic hops and stable authored order, ignoring seen badges. It disappears when all known places are visited or the explicit current location is invalid. It does **not** start trips, grant fast travel, alter existing level gates, certify walk-grid reachability or promise the shortest physical walk. The existing walk grids, travel routes and eligibility checks remain authoritative; C23 checks terrain/seam quality. Do not use atlas edges or `unseen` as navigation permission.

## Additive save safety

`mapSeen` is an optional string list in the existing v1 save, required with an empty default in runtime state. The storage key/version stay unchanged. An old missing/malformed list defaults to that account's already known zones, avoiding a migration backlog. An explicitly empty list stays empty. Valid string IDs are deduplicated; unknown future IDs survive storage but are ignored by today's atlas. No balance, player, ownership, collection, companion, history or world-coordinate reset is performed. Existing unknown JSON fields still round-trip through the save codec.

## Validation and limits

`npm run check:world-map` is included through `check:world` in `check`/`verify`. Pure tests cover catalogue-derived nodes/topology, every existing station route, hut door, every zone's current state/grid coordinates, station radius, Home/live overrides, discovery acknowledgement races, detached/frozen inputs, deterministic suggestions and old-save codec fixtures. `check:game` exercises the actual migration, persistence, walking, repeated acknowledgements and reload, preserving progress and unknown fields with native/storage/network boundaries substituted.

No map UI exists in this PR, so no map-screen visual, phone, native runtime, screen-reader, real backend, multiplayer or performance claim follows from these source checks. Claude should wire the screen and perform its browser/mobile-width pass separately.
