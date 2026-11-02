# Ground rules: the world's physical model

Matt, 27 Oct 13:26: "really double down on the physics and establish correct ground rules for the
game (it will make placing stuff much easier later)". These rules say how the ground of every zone
is built and what may stand where. The world editor's validator applies the same rules. Each rule
is a check: `python3 -m scripts.review.ground_rules` (in `npm run check:kit`). A plan that sets
`"ground_rules": true` must pass; other plans get the report as advice until their region is rebuilt.

We checked the rules against Eastward's screens (`refs-games/eastward`, local only):

- **13:** the farm's canal runs straight on its tiles, with built banks. The paths turn in rounded
  bends, and the benches and lamps stand at the path's edge.
- **37:** the pond's bank is lined with stones resting side by side. The camp's props stand on
  grass beside the trodden ground.
- **15:** the swamp's channels run on the grid between land shelves. The reeds grow in clumps.

## Layers, built in this order

Each layer obeys every layer before it.

### 1. Terrain heights

- Tiers are whole cells (8 world px), and each tier has one height.
- A face is as tall as the height difference it divides. Sides and stairs agree with the rim
  (a stair's head is flush with the rim, its foot on the lower ground).
- Checked by `logic.tiers` (`scripts/review/tiers.py`) and `grid_snap`.

### 2. Water

Water has a source and flows downhill:

- It stays within one tier except where it drops.
- A waterfall happens only at a tier edge or a rock face. Its lip is flush with the rim.
- The fall is centred on the channel that feeds it and is as wide as that channel. It lands in a
  pool.
- Water never runs uphill or ends in a dead end. Every end is a pool, a lake, the sea, a fall or
  the zone edge.

Checks:

| Check | What it catches |
|---|---|
| `rules.water_source` | a stream that starts out of nowhere (it must start at the zone edge, a spring or a pool) |
| `rules.water_end` | a channel ending in a dead end |
| `rules.water_fall` | a lip not flush with the rock's top edge, a fall off the channel's centre, a fall narrower or wider than its channel, a fall that misses its pool |

### 3. Ground materials

- One material per cell region, with soft-grid edges (`eastward-edges.md`).
- No material lies under water: a route or worn ground crosses water only on a bridge's span.
- Checked by `rules.ground_water`, and by `detail.ragged_edge` and `corner_radius` for the edges.

### 4. Routes

- Routes connect real destinations: doors, bridges, zone exits, stairs, stands and named places.
- Runs are straight, on cells, along x or y, and keep one width.
- Turns are rounded bends with a radius of 0.4 to 12 cells, at least two cells apart (no
  right-angle stair steps). No free curves leave the grid.
- Nothing stands on a route except bridges and signposts, by design.

| Check | What it catches |
|---|---|
| `rules.route_grid` | points off the cells, slanting runs, turns closer than two cells, a bend radius out of range |
| `rules.route_ends` | a route end that meets no destination and no other route |
| `rules.route_clear` | any object whose foot stands on a route |

### 5. Structures

- Footprints lie on cells, and doors open onto a route.
- Nothing overlaps a footprint, and no road passes under a building.
- Checked by `roads_clear` (`check:kit`), `grid_snap`, and `logic.composition` for structures with
  props. The Crossroads plan's doors are its route ends (`rules.route_ends`).

### 6. Props by role

Every prop has a placement relation and a clearance.

- **Seating** stands beside a route or faces a view. It stands on grass or paving next to the
  route's edge (within two cells), never on the route, and faces the route or the view.
  The kit's bench faces south, so its route lies south of it.
  Checked by `rules.seating`.
- **Lamps** stand at route edges, corners and entrances. **Wells** are central to their space.
  **Stalls** stand in rows with aisles. Checked by `logic.composition`.
- **Fire** burns only in hearths, forges and campfires, and **smoke** rises only from chimneys and
  fires. The town builder enforces this: `chimney_pot` places smoke only at a drawn chimney.
- **Storm debris and puddles** appear only in the broken stage, under a stage condition. Checked by
  `rules.stage_debris` on zones that have stages.
- **Rocks and boulders** rest on the ground with contact shadows. They never overlap unless the plan
  marks one `stacked`. The depth order follows the screen: the lower stone on screen is drawn over
  the one behind, never the reverse. Checked by `rules.rock_overlap`.
- **Trees** have their trunks on cells and their crowns uncut. Checked by the crowns gate
  (`check:kit`) and `grid_snap`.

### 7. Clutter

- Tufts, flowers, pebbles and leaves are placed freely.
- They are never on a route's centre line or in water.
- Checked by `rules.clutter`.

## Using the checks

- `python3 -m scripts.review.ground_rules`: a report for every plan.
- `python3 -m scripts.review.ground_rules --check`: fails on a plan that declares
  `"ground_rules": true`. Today that is the woodland.
- `python3 -m unittest scripts.review.test_review`: the rules' tests. Each rule has a plan that
  passes and a plan that trips it.
