# Sunstone Reach and the fire country: the plans as data

**Owner: Claude D** (lane D). The brief is `sunstone-basin-fire-country.md` (world plan v5.3, PR #96). Crew board note a-to-d-plans (21 Oct): while Matt judges the 2x pilot, lane D lays its regions out as data, in world px, so nothing here moves when the art's density changes (to-all-density).

```
python3 scripts/art/regions/sunstone_plan.py              # writes art/regions/sunstone.json and fire-country.json
python3 scripts/art/regions/sunstone_plan.py --check      # rebuilds both and exits non-zero if the files differ
python3 scripts/art/regions/sunstone_plan.py --draw OUT   # also draws them with region_plan.py (#174) when present
```

A run takes about a minute. Nothing in the game reads the plans yet.

## The two plans

| Plan                | Box (world px)              | Holds                                                                                                                                                                       |
| ------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sunstone.json`     | x 0 to 4800, y 0 to 4320    | the steppe west of the Brackens gap, the Rift and Drover's bridge, the scrub and mesas, Palm Spring, Dust Gulch, the Lode, the Amber canyon, the salt lake, the Cinder Rise |
| `fire-country.json` | x 0 to 5600, y 4000 to 5856 | Mount Ember, the ash fields, the chasm bridge, the Ember forge, Hearthold, Cinder Springs, Cinderwick, the dead forest, the Rift ferry, the Ash Coast's green shelf         |

The boxes are the brief's, rounded to whole 32 px audit cells. Where they overlap (y 4000 to 4320) a thing belongs to the basin above y 4160 and to the fire country below.

Both are in Claude F's schema (`docs/vision/region-plans.md`, `scripts/art/region_plan.py`, #174) and pass its check except for the routes' long straight runs (below). Beyond F's fields they carry what lane D's regions need:

- **Tiers** are lane G's absolute world tiers (`base_tier` 0): 0 the sea and 1 the beach, 2 at the coast to 15 at the forge, 13 and 14 for the massif's crags and lane G's beyond, 16 to 21 for the upper cone (never walked). Outlines are in screen space on the 8 px grid, in straight runs along x and y that turn at cell boundaries (to-all-grid-2x); the painter rounds the corners (eastward-edges 1.5). A tier is a 32 px south face; west and east ends are side bands.
- **Routes** are lane G's lines, widths and tiers (`lib/world-routes.ts`, read from #175 @ef8824f; `sunstone_routes.json` is the snapshot the script uses until the file is on main). Each route keeps G's vertex tiers (`tiers`) and crossings. Lane G's side paths and pockets on lane D's land are trods; lane D adds the settlements' streets and lanes.
- **Stairs**: every tier change of G's is a stair, round-end or switchback where G put it. A stair that climbs north cuts a south face, so the higher tier's rim lies 16 px north of the stair's point. Lane D's trods get a stair wherever they change tier (a round-end on an east-west leg). No ramps (eastward-edges 6.3).
- **Water and lava**: the Rift, the Amber, the Willow Run (sinking into its fan and rising at Palm Spring's pool), the Rift's tributaries, the salt lake, the orchard channels, the hot pools and the sea's shore; the crater, the old flow (from the summit's south-west breach, in the chasm the chasm bridge crosses), the young flow (from the south-east flank vent, with its fissure, spatter cone and lobes, crossed by the crust causeway), the parasitic cones and the Cinder Rise. Every line is on the soft grid.
- **Places and areas**: the seven places with their rects; the screen areas on 32 px cells, keeping today's zone ids where a zone is kept or replaced (`gulch`, `oasis`, `scorch`, `caldera`, `hearthold`, `springs`), so saves, stands and missions carry over.
- **Stops, rails and the ring**: the Dust Gulch platform (`west`) and the forge cart bay (`lava`, stand `tunnel`); the desert line (in over the Rift's viaduct, one level crossing with the Drover's Road, to the platform) and the mine cart (the Lode past the salt lake to a tunnel under the caldera rim, after W6); today's caldera sparring ring moves to the forge yard. Each rail lists its crossings.
- **Rest spots**: the viewpoints, wells, camps and shrines on the routes, the bench and view pockets, and a bench in each settlement.
- **Named things, pockets, markers, egg spots**: all of the brief's, read from the brief by the script. Each one is moved to the nearest spot beside or a short way off its own route on G's line, on a tier top (never a face), clear of every path, stair, water, lava and rail, 12 to 16 px from the next thing, and 32 px clear of an egg spot; `moved_from` keeps the brief's point. Nothing is left unplaced.
- **Set pieces** from the cliff core (#165) in each biome's own set (to-all-reuse-rule): stairs, ledges on the mesas, scree under the canyon walls and the massif's foot (`canyon`), boulders on the coast (`coast`), Hearthold's and the forge's stairs (`city`), and the ash biome's cinder cones, spatter cone, fumaroles and steam cave (marked pending: the cliff core has no ash set yet).
- **Clusters**: the places where atmosphere comes from grouped props (Claude B's cluster library, a-to-b-clusters), each with a recipe, its members by prop key, its light, a seed and why it is there: a steppe camp, the sheepfold, the wind pump stop, the oasis nook and orchard edge, the frontier street corner, the platform yard, the mine yard, canyon shade, the salt shore, the ash field, the fumarole field, the forge yard, the castle street, the springs bath, the black-sand shore, the dead-forest glade, the ferry landing, the coast meadow.
- **Edges, thresholds, meets, residents, ground** as the brief's sections 3 and 6 give them; `overrides` and `open` (below).

## How the ground is made

The script lays a designed field on 8 px cells and traces it: the plateau rising north to the massif in bands of whole rows and falling east to the Rift in bands of whole columns (contours along x and y, never diagonal), the salt lake's pan in nested rectangles, the coastal shelf stepping down to the sea, Mount Ember in nested rounded rectangles (gentle to the north and west, steep to the sea between the flows), then the cuts: the Rift's gorge with benches and wide green floors in its bays, the Amber's canyon with banded walls under the fan's edge, the mesas, the massif's crags, the sea and the beach, the old flow's chasm. The places are laid as terraces (Hearthold on six, from the forge stair's foot to the south-west gate, its keep above). Then every route and trod sets its corridor to its tier and the ground north of it is held low enough that no face hangs over a path. The tiers are traced to outlines with no holes (a part with a hole is cut north to south through it) and rasterised back the way F's check does; the script stops if a single cell differs.

## The Dust Gulch override

Review 21 Oct 07:53, finding 1: today's Dust Gulch zone has its head and tower 60 to 140 px from the Scorched Pass lava. **OVERRIDE until the continent rebuild** (Claude A, a-to-d-override): it breaks no play, a look-patch on an old zone is ruled out (to-all-no-old-assets, to-all-old-zone-patches), and this plan puts the gulch on the Amber's fan in the desert, about 2400 px from the nearest lava. It is recorded in `sunstone.json` (`overrides`).

## Open

- **Asked of Claude G** (`open.asks_of_lane_g` in each plan): five of the Canyon Road's changes climb southward (5>6, 7>8, 8>9, 9>10, 11>12), so the rim each crosses is a north edge with no face to cut; and five of the Ember Way's stairs sit on east-west legs (10>9, 9>8, 7>6, 5>4, 3>2), where a stair has no south face to cut. Round-ends on east-west legs, or stairs moved onto north-south legs, would settle both; the plans take G's points as they are until then.
- **The routes' straight runs**: lane G laid every route in straight runs along the grid (Matt, 21 Oct 11:44), up to 416 px on the Drover's Road; F's check still holds routes to 240 px (benchmark 16), so it reports those runs on these plans as it does on others. They are lane G's lines and Matt's rule; the check needs updating, not the lines.
- **The cliff core's canyon set is 40 px a face**; these plans keep lane G's 32 px tier. Either the canyon set gets a 32 px face or its faces read a 32 px tier map (asked of Claude A).
- **The ash biome** has no edge set in the cliff core yet; its set pieces are placed and marked pending.
- **The brief's small mismatches**: the desert line's viaduct is called "upstream" of Drover's bridge but sits downstream at (4290, 3720); the plan keeps the coordinates. Table 5.2 of the world plan calls the west flow "young"; the plan follows 4.7 (the old flow is crossed by the chasm bridge, the young one by the crust causeway).
- **Hearthold's 24 stairs** come with the castle kit; the plan lays its six terraces, the routes' stairs and the streets between them.
- **The north and west walls** (`edges`) replace lane G's provisional line at y 1504; the west wall runs about x 610 to 720 from the massif down to the sea cliffs. Lane G draws the beyond past them.
