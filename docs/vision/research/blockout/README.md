# The world plan's block-out (v5.2) and the overview map (v53, v54, v55)

## v55: room for the towns (27 Oct)

Matt's brief of 27 Oct (in full in the PR): "keep v54's overall geography, enlarge the usable world by roughly 20%, and give its settlements substantially more space and everyday activity. The expansion should follow the places that need room, especially Neon Harbour, rather than stretch every distance equally." Medium towns hold 14 to 22 buildings, large towns 30 to 45 and Neon Harbour 60 to 90 (provisionally), counting homes, shops, workshops and public buildings, enterable or not, but not stalls, sheds or the separate doors of one building. His layout order has seven steps; v55 does steps 1 to 4 on the overview, the visual consistency pass and the label hierarchy, and writes steps 5 to 7 below as a plan for the lanes and the world editor.

`geo55.py` (data), `towns55.py` (the settlement layouts) and `map55.py` (the maps) sit on top of geo54 and map54. `blockout-v55.json`, `stats-v55.json` and `gates-v55.json` are v55's own: the ground, the routes, the tiers and every check are measured on the v55 canvas. `continent-1x-v55.png` is the 1920 map, `inset-home-valley-v55.png` and `inset-neon-harbour-v55.png` the two insets (256 colours).

### How the land was enlarged: a warp that only widens

v54's ground is built exactly as before, then stretched onto a larger canvas, **12544 x 7168 world px** (v54: 11264 x 6912; 49 x 28 tiles of 256). The stretch is separable and piecewise linear (`STRETCH_X`, `STRETCH_Y`; the knots are in `stats-v55.json` v55.warp): every band of v54's x or y is widened by its own factor, and no band is narrowed, so no barrier, river or route is thinned or broken. The **anchor** (x 5400 to 7000, y 1400 to 3900) keeps its coordinates exactly: the home valley, the woodland, Crossroads, the stone circle and the Frostline are where every plan has them, and `game/data/plans/` needs no change.

| Band of v54 | Widened by | Why |
| --- | --- | --- |
| x 9400 to 11264: Neon Harbour, the ria, Launch Cape, the fens | 1.58 | the city, its outskirts, its east coast and the cape: the most room |
| x 7000 to 8400: Fernhollow, Cogsworth, the Lull plain | 1.10 | two town footprints and the plain's farms |
| x 8400 to 9400: the Narrows, the meander belt, Lullford | 1.06 | a little: the river corridor and the delta |
| x 1500 to 4300: the Sunstone basin, Dust Gulch, Palm Spring, Hearthold, Cinderwick | 1.14 | the desert and fire country towns and their settled margins |
| x 4300 to 5400: the Rift, the steppe, the Brackens | 1.06 | a little: the steppe's transition and the Rift's bays |
| y 3900 to 5950: the halt, Driftwood, Lullford, Hearthold, Gullwick, Cinderwick, Launch Cape | 1.125 | the coast band and its towns; the isles move 256 px south with it |
| y 300 to 1400: the massif | 1.20 | the mountain valley town and the approach to the closed pass |

The far west of the dune sea (its outer 458 px) and the top 220 px of the ice cap run off the canvas: both are past the walk. To move any v54 point onto v55: `geo55.P((x, y))` (np.interp over the knots in x and in y); a box by its corners (`geo55.Pbox`).

**Usable land** (land outside the frame that is walkable or built on): v54 436837 cells, v55 547843 cells, **+25.4 %**. The stretch gives +21.1 %; Highgarth's valley, the cape's new land and their surroundings the rest. Matt's band was 15 to 25 % with 20 % as the first target, so this sits just above it (the stretch alone is +21 %); the uneven allocation puts most of it where he asked (the east coast and the town footprints).

### Step 1: the settlement footprints

Every settlement is laid out from a street skeleton (its routes, plus side streets, back lanes, quays and squares written per town in `towns55.py`) and filled with separate buildings at the size guide's footprints (`size-guide.md` 4: a cottage 80 x 48, a house 64 to 96 wide, a workshop 80 to 112, a warehouse 112 to 160, a city building 64 to 96), each on one tier (a footprint that crossed a tier is levelled to its middle tier: 145 of them, the terraces and retaining walls the lanes draw), each set back from its street with a garden or yard behind. Infill fills behind and between the streets, always within 150 px of a street or route, so the large towns get residential depth: back lanes, courtyards, workshops behind shops. The working outskirts are painted round each town, so the overview shows why it is there. Every building, street, square and outskirt is in `blockout-v55.json` v55.settlement_footprints (buildings as `[x, y, w, h, use, counted]`).

| Town | Allocation | Buildings (target) | Neighbourhoods | Gathering places | Working outskirts | What it is for |
| --- | --- | ---: | --- | --- | --- | --- |
| Dust Gulch | large (desert) | **38** (30 to 45) | Front Street, the Depot, Water Street, West Row, the corrals | the depot square, the well square, the chapel yard | the corrals, the goods yard, the ore yard, the river gardens | the desert line's railhead and the Lode's ore yard |
| Palm Spring | medium (oasis) | **18** (14 to 22) | Spring Row, the caravanserai, Channel Row, Palm Row | the spring square, the pool steps | the date gardens, the north grove | the first water in the dry country |
| Crossroads | large (central meadow) | **39** (30 to 45) | the square (built), Mill End, Halt Road, Eastgate, West Lane | the square, the drovers' market, the mill green, the halt yard | the halt farms, the mill farms | the market and meeting point of the valley |
| Fernhollow | medium (central meadow) | **16** (14 to 22) | the Green, the Yards, Fern Lane | the green, the sawmill yard | the wood yards | timber from the Fern hills' wet woods |
| Hearthold | large (fire country) | **33** (30 to 45) | the Castle, Smiths' Row, Gate Street, Ash Lane | the castle yard, the gate market | the vines, the lower fields | the fire country's town of knights and crafts |
| Cinderwick | medium (fire country) | **14** (14 to 22) | the Strand, Kiln Lane, the Quay | the quay, the kiln yard | the kilns | the fire country's harbour |
| Cogsworth | at least medium (Cogsworth region) | **26** (14 to 45) | Foundry Row, Engine Street, the Terraces, the Platform | the station square, the works gate | the railway yard | coal and iron from the coal hills, the fast Cog for power (the Millrace), and the railway out |
| Lagoon Landing | medium (Tidebloom Isles) | **17** (14 to 22) | the Lagoon front, the East Strand, Net Row, the Pier | the lagoon steps, the pier head | the boatyard | the isles' town |
| Highgarth | medium (mountains; new) | **18** (14 to 22) | Garth Street, Quarry Lane, Low Street | the market cross, the sheep fair field | the slate quarry, the in-fields, the folds | slate from its quarries and wool from the summer pastures, sawn timber from the valley's larches; the drovers' inn on the Garth Road; it sends slate, timber and wool down to Cogsworth. Its old trade over the north pass stopped when the Starfall brought the rockfall down; the road beyond waits for a later region |

**Neon Harbour, 79 buildings** in five districts (below). **Smaller places** stay smaller: Lullford 10, Driftwood 10, Gullwick 8, Cinder Springs 6, the Lode 4, Ember forge 3. **Farms of the central green**: ten farmsteads (a farmhouse and a barn each) and three windmills, not counted in any town.

### The town plans (`towns/<id>.json`, checked by `scripts/review/town_plan.py`)

Every settlement now has a plan as data, one file a town (schema `mygame.town_plan/1`), written by `town_plans.py` after the layout and before the farms round it. The map draws its buildings from these files, and each large town has an inset drawn from its plan (`map55-town-<id>.png`, `town-<id>-v55.png`). A plan holds:

- **site**: why the town is there, the ground it sits on, how it fits that ground (the oasis gardens on the channels, Highgarth's streets on one tier each with retaining walls, Hearthold on the one stable rock between the flows, Cogsworth's terraces in the strips the works leave, Lagoon Landing round its lagoon, Neon Harbour's districts from the docks to the Heights), and the tiers under it;
- **arrivals**: each regional route's part that serves the town, with the points where it enters (a ferry for Lagoon Landing); Crossroads' valley lanes stop at the built zone's edge, where the zone's own roads (`game/data/plans/crossroads.json`) take over;
- **streets** by class on the soft grid (ground-rules.md 4: x and y runs on cell lines, one width, turns at least two cells apart): main 6 cells, side 4, lane 3, close 2 (size-guide.md 0), an arrival at its route's width; a main street on a route keeps the route's line and is widened to 6 cells round it; what each street connects;
- **squares**, **districts** (by function, worked out from what their buildings are: market and civic, homes, crafts and work, docks and transport, offices and trade, and the edge farms and yards) and **gathering places**;
- **buildings**: type, footprint in cells, the street it faces, its door, its plot behind (garden or yard), purpose and occupants (as roles), district, and whether it counts;
- **game layout**: the arrival, the first view, the landmarks seen from the ways in, the shortcuts that open later, the quiet corners next to busy ones and the town's size in screens (40 x 22.5 cells);
- **ground**: what the centre, the yards and the edges are made of;
- **terrain**: the box's ground, one character a cell (land, route, water, barrier, bridge), taken from the finished map;
- **residents** and **routines**, empty, with `x3_notes` for Codex (X3): residents by building id, routines on street and square ids.

The layout pass that finishes each plan: a street not joined to a way in gets a lane to the nearest joined street (or is lifted); a building that does not stand within three cells of a street gets a close two cells wide through its yard or garden (a building no close can reach is lifted with its plot); the parts of a street cut by water, a barrier or a building become separate streets. The checker reads only the plans and `blockout-v55.json`:

```
python3 scripts/review/town_plan.py                  # every plan: one line a town, the failures
python3 scripts/review/town_plan.py --town hearthold # one plan, every finding
```

It fails a plan when a footprint is off the cells, a street is not in x and y runs on its cell lines, a building stands on a street, a square, water or a barrier, a street crosses water off a bridge, a door is more than three cells from the street its building faces, the count is outside the range, an arrival is not on its route, a street is not joined to a way in, a large town has fewer than three districts, two functions or two gathering places, a way in has no landmark within two screens, or a medium or large town has no loop. It reports the dead ends, the blocks (loops) and the size in screens. The seven buildings of the built Crossroads zone are taken from its own plan and checked there (`rules.route_clear`); the overview's Sleepwater still runs through that zone's box, which is a proposal for the home valley's lane (in `regions/home-valley-frostline-brackens.md`).

### Step 2: the east coast, Neon Harbour and Launch Cape

- **The east coast.** The open sea now comes in along the city's east side (`EAST_SHORE`): the shore leaves the canvas edge at the fens' foot (y 4230), runs south past the East Shore's terraces and round Launch Cape, and back up its west side to the ria's mouth (`CAPE_WEST`). The east margin's clouds stand only north of it, where the land still runs on.
- **Neon Harbour, clearly the largest place in the world**, round the ria, the east coast and the Heights; its districts blend into one another and each is a `towns55` layout with its own buildings:

| District | Buildings | Character and activity (Matt's table) | Where |
| --- | ---: | --- | --- |
| the old waterfront | 16 | older buildings, narrow lanes, small businesses, Bridgefoot square and the falls steps | the Falls Rock and the old quays round the ria's head |
| the docks | 14 | the long quay, warehouses, cranes, piers, the slip and repair yard, the fish market at the steamer pier | the ria's deep east side down to its mouth |
| the Lanes and the East Shore | 16 | flats round courtyards, corner shops, washing over the lanes; terraces facing the open sea | between the old waterfront and the Company district; along the east coast |
| the Company district | 15 | offices and towers on Neon Row and two avenues, Terminus Square at the maglev, Neon Square; the Company crater fenced in its yard to the north | the flats east of the old town |
| the Heights and the Skyport | 18 | terraces on the contours, stairs and the funicular, the Skyport's three mooring masts, its terminal and hangar on the crown | the headland west of the ria |

  The outskirts are inhabited: **Canalside** (10: carters' and bargees' houses and market gardens on the Lull Road where it comes in beside the Lull Cut), **Glintside** (5: mill houses and allotments on the Glint above the falls, where the maglev comes in) and **Halcyon Row** (10: the launch staff's houses at the cape's neck).
- **Launch Cape** is a full headland (about 600 px wide and 1300 long; 4230 cells of new land), its shore continuing round the tip: cliffs on the exposed east side, a beach on the sheltered west. The **Pad Road** (a road) runs down it from Halcyon Row past the works (6 buildings: the assembly hangar, workshops, stores, the control house) to **the pad** at the tip (12085, 6455) with its service apron and tower. The nearest house is 770 px from the pad, across open heath. The rocket's way (W8) is now at the pad.

### Step 3: Highgarth and the closed pass

**Highgarth** (18 buildings, medium) sits in a sheltered valley on the upper Cog, inside the range north of Cogsworth (7905, 1190). Its purpose today: slate from its quarry, wool from the summer pastures and sawn larch from the valley floor, sent down the **Garth Road** to Cogsworth; the drovers' inn; a sheep fair. Stepped streets on the east bank (footprints levelled onto terraces), a sawmill by the river, walled in-fields below and the folds above, steep wooded slopes and snow on the peaks round it. It is reached through Cogsworth, behind W3 (the gate check holds it: not reached before the Millrace landslip opens, reached after). Its waystone is proposed at the market cross.

**The closed pass (C1).** The **Northway** climbs from the town to the valley's head, where a rockfall lies across the whole valley (`ROCKFALL_LINE`, from the Cog to the east wall). Beyond it the road is drawn on to the col at the canvas's top edge, where a gap in the cloud bank shows hazy land beyond; that part is frame, not walkable, and listed under `closed_routes`, never `routes`. In the data it is closed for movement (the rockfall and everything beyond are not walkable ground; `gates-v55.json` "closed: the Highgarth pass": nothing beyond is reachable with every way open, the road up to the rockfall is), for navigation (no route, beat or path plan crosses it) and for travel (no waystone, station, shortcut or ferry beyond it). It is 1.3 km east of the act 1 crossings (the ridge col and the Fells saddle) and shares no ground with them. A later region joins over the col without moving a town or rescaling the continent. A sign and the townsfolk's talk explain the rockfall (step 6).

### Step 4: roads, rivers and land fitted round them

- **New routes**: the Garth Road (Cogsworth to Highgarth, a path up the Cog's east bank, crossing no barrier), the Northway (Highgarth to the rockfall) and the Pad Road (the cape). The regional loops are v53's and stay closed; the stretch lengthened some routes, so where a route ran more than 260 px with nothing to meet, an obstacle with a side path round it was added (2 of them), and the towns' buildings beside a route count as what it meets.
- **Rivers** are v54's lines moved by the warp (each still runs downhill: the warp only widens, so no line changes its order). The Lull's west bank is stepped into **river terraces** (four flat steps above the floodplain, farmed).
- **The central green**: ten farmsteads with orchards and hedged fields, three windmills on the rises and seven small woods in the Lull plain and the valley's south, leaving open meadow between; Crossroads and Fernhollow carry the population, the farms the land round them.
- **Settled margins**: scrub along the desert's dry beds, green along the Amber and the Willow Run where they are irrigated (Dust Gulch's river gardens, Palm Spring's date gardens and north grove); in the fire country, Hearthold's vines and lower fields and Cinderwick's kilns on the stable ground between the flows.
- **Open countryside between towns**: no two town footprints touch; between them run fields, woods, desert or coast (Hearthold and Cinderwick are the closest pair: the stable ground between the lava flows is narrow, so about 60 px of fields and the Ember Way lie between them).

### One visual treatment

The range, the forests, the dunes, the hills, the mesas and the buildings are drawn the same way: three tones from one ramp of the house palette (lit, middle, shade), a thin ink outline and a shadow cast to the south-east (`map55.tones`). The peaks' crests are softer (fewer jags, no extra spur facet), so the range reads as the same kind of mark as a tree. The northern wall has **spurs**: chains of hills stepping down the fall line from the range front (3 spurs, 8 hills), with valleys left between them, and its foothills vary in size. Forests have **clearings** and uneven density (a density field thins the trees in places; deep woods open into glades). The cloud edge is one **irregular bank** shaped by noise at three scales and lit from the upper left, in place of v54's rows of bubbles; it stands only where the land runs off the canvas, so the coast, the city and the cape stay clear.

### Labels by zoom

| View | Names |
| --- | --- |
| the continent (`map55-1920.png`, `map55-3840.png`) | the regions, the large and medium towns and the city, Launch Cape, the stone circle, the closed pass, the principal routes (the Drover's Road, the Lull Road, the Ash Coast, the Canyon Road, the Foothill Road, the Coast Path, the High Fells, the Towpath, the Garth Road) and the rail, cart and ferry lines; the craters, gates and waystones as icons only |
| the insets (`map55-inset-home-valley.png`, `map55-inset-neon-harbour.png`) | every name inside the box: settlements, districts, squares, yards, farms, gates with their ways, craters, peaks, passes, water and routes |
| the reference (`map55-reference.png`, 5760 x 3240) | every name on the continent |

### Checks

- The gate check: no leaks, nothing missing, no crossing without a way, at every step (`gates-v55.json`), with Highgarth behind W3 and Halcyon Row, Glintside and the cape's works behind W7.
- The closed pass: nothing beyond the rockfall is reachable with every way open; the Northway up to it is (`gates-v55.json`, "closed: the Highgarth pass").
- The benchmark on the v55 canvas: **21 of 21 pass** (`stats-v55.json` benchmark).
- Reachable from home with every way open: every crater, act 1 place, waystone, the circle, Highgarth, Halcyon Row, Glintside, Canalside and the pad.
- Walk times from the hut at Bramble's speed (`home_to_at_hero_speed`): Dust Gulch 165 s, Hearthold 218 s, Neon Harbour 209 s, Highgarth 127 s, Launch Cape 287 s, Lagoon Landing 135 s.
- Looked at: the rivers run downhill as in v54; every town stands on flat or terraced ground beside water and on its routes; the labels overlap nothing.

### The maps (written to `out/`, and to `$MAP55_OUT` if set)

| File | What |
| --- | --- |
| `map55-1920.png`, `map55-3840.png` | the continent with every layer (the built zones, act 1's route and its beats, the crater ring, the ruler), labelled for the continent view |
| `map55-reference.png` | the continent at 3x with every name (the development reference) |
| `map55-inset-home-valley.png`, `map55-inset-neon-harbour.png` | the two insets, every name in the box, each with a ruler |
| `map55-v54-vs-v55.png` | v54's and v55's maps side by side at 1920 x 1080 |
| `map55-town-crossroads.png`, `map55-town-dust-gulch.png`, `map55-town-hearthold.png`, `map55-town-neon-harbour.png` | the large towns' plans, drawn from `towns/<id>.json` over their ground: streets by class, buildings outlined by district, doors, squares, landmarks, the ways in, later shortcuts, quiet corners and one phone screen for scale (committed at 256 colours as `town-<id>-v55.png`) |

The ruler: one soft-grid cell is still 8 world px; the 1920 map is now 1 px = 6.6 world px (v54: 6.4), and the ruler, its walk times and the screen box are drawn at that scale.

```
python3 -I geo55.py                  # data and every map (about twenty minutes)
RENDER_ONLY=1 python3 -I geo55.py    # the maps again from out/state-v55.pkl
QUICK=data python3 -I geo55.py       # the JSON and the state only (about ten minutes)
```

### Steps 5 to 7: the plan for the lanes and the world editor

These are not built yet. Each lane builds its towns at gameplay scale from the footprint in `blockout-v55.json` (the buildings' positions and uses are a starting layout, to be adjusted to the kits), then peoples them, then the journeys are walked and measured.

**Step 5: build one representative area at gameplay scale first**, to set the density before repeating it: per town, the area named below. A screen (320 x 576 world px) of a medium town's centre should hold 6 to 9 buildings' fronts; of a large town's back lanes 8 to 12 smaller fronts with yards; of Neon's lanes 10 to 14 frontages, taller (the size guide's city building, 3 to 6 storeys). Keep every walking route and door apron clear (the size guide's kept-clear bands).

**Step 6: residents, animals and props by function.** A mix of named characters, recurring residents with simple routines (a worker carrying between two buildings, a resident returning to a bench, someone feeding hens) and ambient inhabitants. As a first camera test (Matt's numbers; starting points, not quotas):

| Where | Visible people |
| --- | ---: |
| quiet outskirts, residential corners | 1 to 3 |
| ordinary town streets | 4 to 8 |
| busy markets, stations, city docks | 8 to 12, more where there is room |

Some streets stay quiet; a market has a reason to be busy. Animals live where their habitat is: hens and grazing animals in the meadow towns, pack animals at the desert stopping places, cats and gulls at the docks, the fire country's goats and pigs on its settled ground. Props show the work: crates by the businesses that handle goods, tools by the work, water butts and troughs by homes and stopping places; busy places keep clear walking lines and entrances.

| Town | Build first (step 5) | Who lives and works there (step 6) | Animals | Props by function |
| --- | --- | --- | --- | --- |
| Crossroads (large) | Eastgate and the drovers' market | market traders, the smith (Hale), drovers on market days, millers at Mill End, the halt's porter | hens in the yards, sheep and cattle penned at the market, a cat at the bakery | hurdles and pens, grain sacks at the mill, milk churns at the halt |
| Dust Gulch (large) | Front Street and the depot square | the sheriff (Pendle), the store and saloon, assayers, rail and repair hands, mule drivers, the water carrier | mules and horses at the corrals, a dog, vultures overhead | ore carts and bins, water barrels, the water tower, crates on the platform |
| Palm Spring (medium) | the spring square and the pool steps | the diviner (Mirra), gardeners on the channels, the caravanserai's keeper, caravan drivers resting | camels and donkeys, doves in the palms | water jars, shade awnings, irrigation sluices, date baskets |
| Fernhollow (medium) | the green and the sawmill yard | sawyers and joiners, the schoolteacher, charcoal burners passing through | a cart horse, hens, jays in the woods | log stacks, sawhorses, a cart, charcoal sacks |
| Cogsworth (medium, room to grow) | Foundry Row and the station square | foundry and mill hands at the shift change, railway staff, Clack's workshop, terrace families | pit ponies, pigeons, a cat on the terrace walls | coal carts, rails and sleepers, gears and boilers in yards, washing between the terraces |
| Hearthold (large) | the gate market and Smiths' Row | knights and squires (Ashe), armourers and smiths, potters and vintners, the castle household | goats and pigs on the lower fields, a horse in the castle yard | anvils and quench tubs, wine barrels, banners, firewood |
| Cinderwick (medium) | the Strand and the quay | fishers mending nets, the chandler, kiln workers, the coaster's crew when it calls | gulls, a cat at the quay, goats on the slopes | nets and fish racks, charcoal sacks, glass in crates, a slipway |
| Lagoon Landing (medium) | the lagoon front and the pier head | boatbuilders, divers (Brine), the naturalist, the ferry hand | gulls, terns, a dog on the boats | boats on the slip, diving gear, net lofts, the ferry's crates |
| Highgarth (medium) | Garth Street and the market cross | quarrymen, shepherds, the innkeeper and drovers, the sawyer, the townsfolk who talk of the rockfall | sheep and goats on the pastures, a sheepdog, choughs | slate stacks, wool bales, sledges, the rockfall's warning sign |
| Neon: the old waterfront | Bridgefoot | cafe owners, pawnbrokers, ferry clerks, old residents on doorsteps | cats, pigeons | cafe tables, shop signs, mooring bollards |
| Neon: the docks | the fish market and the long quay | stevedores, crane drivers, fishmongers, repair crews | gulls, cats | crates, nets, cranes, barrels, the slip's cradle |
| Neon: the Lanes and the East Shore | Courtyard Square | families, corner-shop keepers, children, the lido's swimmers | cats, pigeons, a dog | washing lines, plant pots, bikes, a lido kiosk |
| Neon: the Company district | Terminus Square | office workers, couriers (Nix), the Company's guards, delivery drivers | very few: pigeons | delivery carts, neon signs, the fence and the guard post |
| Neon: the Heights and the Skyport | the Skyport terminal and the funicular foot | the rich residents, airship crews, the funicular's attendant | gulls on the masts | mooring lines, luggage, benches at the belvedere |
| Launch Cape and Halcyon Row | the works gate | engineers and launch crews, the canteen, families at the Row | gulls; nothing near the pad | gas bottles, crates of parts, the transporter, warning signs at the buffer |

**Step 7: walk the journeys** and check the town approaches (open country, then outskirts, then the town), the transitions, the route choices and the times. The baseline on the block-out (every way open, on foot, at Bramble's speed; trains and ferries not used):

- **Crossroads - Fernhollow - Cogsworth**: Crossroads to Fernhollow 1060 px, 40.7 s; Fernhollow to Cogsworth 1159 px, 44.5 s (total 85 s on foot).
- **Crossroads - Palm Spring - Dust Gulch**: Crossroads to Palm Spring 3305 px, 126.9 s; Palm Spring to Dust Gulch 988 px, 37.9 s (total 165 s on foot).
- **Dust Gulch - Hearthold - Cinderwick**: Dust Gulch to Hearthold 3398 px, 130.5 s; Hearthold to Cinderwick 848 px, 32.6 s (total 163 s on foot).
- **Lullford - Canalside - Neon Harbour - Halcyon Row - Launch Cape**: Lullford to Canalside 1184 px, 45.5 s; Canalside to Neon Harbour 1318 px, 50.6 s; Neon Harbour to Halcyon Row 1348 px, 51.8 s; Halcyon Row to Launch Cape 891 px, 34.2 s (total 182 s on foot).
- **Cogsworth - Highgarth - the rockfall**: Cogsworth to Highgarth 1330 px, 51.1 s; Highgarth to the rockfall 616 px, 23.7 s (total 75 s on foot).

For each, check that the approach shows the town's purpose before its centre (fields before Crossroads, corrals before Dust Gulch, the walls before Hearthold, the quarry before Highgarth, warehouses and outskirts before Neon), that a quiet stretch separates neighbouring towns, and that the closed pass is seen, signed and never walked.

### Proposals for each lane (the region plans)

Lanes own their plans, so v55 changes none of them; these are proposals. Every coordinate outside the anchor moves by the warp (`geo55.P`); the anchor's do not.

| Lane | Proposed changes |
| --- | --- |
| A (Crossroads plan, the Undercroft) | none to `crossroads.json` or `undercroft.json` (in the anchor). Crossroads becomes a large town: the built square stays as it is, with four neighbourhoods outside its box for lane E (below) |
| E (the home valley, Driftwood, the Headland) | Crossroads' neighbourhoods: Mill End (the mill, the granary, Granary Row, Weir Lane), Halt Road to the halt yard, Eastgate with the drovers' market and the inn, West Lane; the mill farms; farmsteads and Coombe mill in the valley's south; Driftwood moves 132 px south (to 6420, 5092) and grows to about 10 buildings round its cove |
| F (the Frostline, the massif, the Brackens) | the Frostline does not move; Highgarth, its valley, the Northway, the rockfall and the closed pass (C1) in the massif north of Cogsworth; the massif deepened north (1.2) and its top 220 px past the canvas; the range's spurs |
| G (routes, thresholds, edges) | three new routes (the Garth Road, the Northway to the rockfall, the Pad Road) and the closed road beyond the rockfall; three obstacles with side paths on stretched routes (the Canyon Road, the Delta Road, the Pad Road); the east coast as the world's new edge; the cloud edge; the Lull plain's countryside (farmsteads, windmills, small woods, river terraces); `scripts/art/world_routes.py` would take v55's polylines (or apply the warp) if v55 is adopted |
| H (Cogsworth, the coal hills, the Narrows, Fernhollow) | Cogsworth at 26 buildings (Foundry Row, Engine Street, Pit Row, the Terraces, the station square, the railway yard, the allotments), with room to grow toward the pits; Fernhollow at 16 (the green, the sawmill and wood yards, Green Lane, Cooper Lane); both move east with the 1.10 stretch (Cogsworth to 8078, 2450) |
| I (Neon Harbour, the delta, Lullford, Gullwick, the Skyport, the Cape Road) | Neon's five districts at 79 buildings; the Skyport onto the Heights' crown (from the eastern flats, now the East Shore); the east coast; Canalside and Glintside; Launch Cape as a headland with the Pad Road, the works, the pad at its tip and Halcyon Row; Lullford (11) and Gullwick (8) footprints; every point east of x 9400 moves by the 1.58 stretch |
| C (the Tidebloom Isles) | Lagoon Landing at 15 buildings round the lagoon's north shore (the lagoon front's boathouses, Net Row, Pier Lane, Bar Lane, the boatyard); the isles move 256 px south |
| D (the Sunstone basin, the fire country) | Dust Gulch large (38: Front Street, the depot, Water Street, West Row, the corrals, the goods and ore yards, the river gardens), Palm Spring medium (18: the spring pool, Spring Row, the caravanserai, the channels, the date gardens), Hearthold large (31: the castle with its walls redrawn round the whole rock top, Smiths' Row, Gate Street, Ash Lane, Vine Lane, Potters' Lane, the vines on the rock's east slope and the lower fields), Cinderwick medium (15: the Strand, Kiln Lane, Ash Lane, the quay and kilns); Cinder Springs, the Lode and the Ember forge stay small; the west widened by 1.14 and the dune sea's outer 458 px past the canvas; scrub along the dry beds |


## v54: the overview map, second pass (27 Oct)

Matt, 27 Oct 18:23, on v53: "continue to make further improvements, especially the mountains to the north and the sandy desert. make the biomes a tiny touch more visually separated where it makes sense (not a huge amount but a bit here and there to better differentiate the biomes)".

`geo54.py` (data) and `map54.py` (the map) sit on top of `geo53.py` and `map53.py`. **The geography and every place are v53's**: the tiers, routes, ground kinds, ways, craters, places and waystones are unchanged, so `blockout-v54.json`, `stats-v54.json` and `gates-v54.json` repeat v53's numbers and each adds a `v54` block (the range, the desert features, the edges, the label tiers, the inset's box). Anything in that block that is not ground in the block-out is a drawing addition or a proposal for the owning lane (D: the desert; F: the massif's edge; G: the edges). `continent-1x-v54.png` is the labelled map at 1920 x 1080 and `inset-home-valley-v54.png` the inset (both 256 colours).

### The northern range

- **A range, not scattered marks.** The massif's high ground is drawn as peaks in the map's oblique style, the same as the trees and v53's peak marks: each lit on its west face and shaded on its east, with a shadow cast to the south-east (upper-left light). Heights come from the height field (plus a rise toward the north edge, so the range closes the whole top of the map). Peaks stand only on ridges and shoulders (where the ground is higher than its surroundings), so the valleys between them stay open. They are drawn north to south, the nearer overlapping the farther, in three shapes (single summits, twin summits on one ridge, broad shouldered massifs) with a darker spur on the lit face.
- **One snowline.** Snow caps every peak whose summit rises above `SNOWLINE` (0.90 in the height field's units; geo52's snowline runs 0.79 to 0.93 by aspect), down to the same height on every peak, with a ragged lower edge; lit snow on the west, blue-grey in shade.
- **Glaciers in the high valleys.** No peak stands where its body would cover the block-out's glacier cells, so the ice lies between the ridges, with a darker edge and crevasse strokes across its flow. Two are named: **the Rime glacier** above the tarn (the ice caves are under its snout) and **the West ice**.
- **Passes as notches.** No peak stands within 110 px of a pass, and the crest dips toward each over 450 px: **the ridge col** (the Col Path over the Frostline's lip, W2), **the Fells saddle** (the High Fells path) and **the Lode notch** (the mule track's top). Each is marked with a saddle sign (two facing brackets). Routes and rivers keep a clear corridor through the range, so the Rift's gorge and the Cog's valley read as cuts.
- **Foothills** step down from the range into the Sunstone steppe, the Frostline and the forests as low rounded hills in the colour of the ground they rise from (none in forest, where the trees carry the slope).
- **Named peaks**: the highest peak in each stretch of the range: **Whitepike**, **the Greyhorn**, **Rime Fell** (above the Frostline), **the Anvil** and **Old Cairn** (`stats-v54.json` v54.named_peaks).
- **A cloud bank** along the top edge, so the range runs up into cloud instead of stopping at a hard line.

### The desert

- **One wind**: a dry north-north-westerly off the massif (`WIND_FROM_DEG` 340). Dunes run across it: a long lit stoss slope facing the wind, a bright crest line, and a short shaded slip face on the lee (south-south-east) side, consistent with every south face on the map. The crests wander and fade in and out (a slow warp and an amplitude field), so they read as dune fields, not stripes. **The dune sea** has tall dunes (150 px apart); the sand sheet and the interdune flats low ripples (70 px).
- **Mesas and buttes**: the block-out's mesas, and five buttes proposed for lane D on open desert and scrub clear of routes (the Chimney, the Anvil butte, Table Rock, the Sentinels, the Ember butte), each with a lit flat top, a south face in strata bands, and a shadow cast to the south-east.
- **Salt flats**: the salt lake with a crack pattern and a crust edge, and two small pans proposed on the dune sea's interdune flats (the bitter pans, the white pan).
- **Dry riverbeds**: the block-out's Dry Fork and Brackens wash, and two washes proposed leading to the oasis at Palm Spring (the Thirst wash, the Long wash), drawn as pale sandy beds between dotted banks, widening downstream.
- **A gradual edge**: sand, sand sheet, scrub and steppe blend over about 100 px instead of meeting at a line; the speckle that made v53's desert flat is gone (a few pebbles remain).

### The biomes a little more separated (modest, where it is natural)

| Edge | What v54 draws |
| --- | --- |
| forest | a darker rim on every forest edge (the ground and the edge trees) |
| the valley and the moor | the Brackens' heath a touch more heather-coloured, its dots heather, with a thin darker edge against the valley's grass |
| the fire country | the ash fields' dark rim, and a fall-off of ash flecks onto the ground beside them |
| the moss fens | a marsh pattern (water lines with tufts) in place of the reeds |
| the Lull's floodplain | the watermeadows a little cooler, with a dotted flood line at their edge |
| sand to steppe | blended (above), the one edge made softer, not harder |

### The frame, the labels and the inset

- **A clean frame.** v53 stretched and blurred the outer columns into the margins. v54 carries the sea flat into the margins where the edge is sea, and closes the land's edges (and the top) with a cloud bank, lit on its upper left; the double frame line is kept.
- **A label hierarchy** (`LABEL_TIERS`): tier 1 (region names, towns and villages, the stone circle) always; tier 2 (great craters, biome names, named peaks, gates with a way) where it fits, with a leader if needed; tier 3 (small places, other gates, passes, water and route names) only where there is space around it, with no leader. On the full map tier 3 is left out inside the inset's box, which the inset names in full: the home valley loses about twenty small labels and keeps every town, crater and way.
- **The home valley inset** (`map54-inset-home-valley.png`, `inset-home-valley-v54.png`): world px 4800 to 8100 east and 1400 to 4400 south at 1 px to 2 world px (3.2 times the 1920 map), with every name, the built zones, the routes and lines, and a ruler (10, 50 and 100 cells at Bramble's walk). The full map marks its box with a dashed line.

### Checks

- The gate check: no leaks, nothing missing, no crossing without a way, at every step (`gates-v54.json`, the same as v53's).
- The benchmark: **21 of 21 pass** (`stats-v54.json` benchmark; the ground is v53's).
- Reachable from home with every way open: every crater, act 1 place, waystone and the circle (unchanged).
- The labels: none overlaps another or an icon. Every tier 1 and tier 2 name is placed on the 1920 map, the 3840 map and the inset (the run prints any that are not).
- Looked at: the rivers run downhill as in v53 (unchanged lines); the peaks, dunes, mesas, clouds and trees are lit from the upper left and shade or cast to the lower right.

### The maps (written to `out/`, and to `$MAP54_OUT` if set)

| File | What |
| --- | --- |
| `map54-1920.png`, `map54-3840.png` | the full map with every layer, at 1920 x 1080 and 2x |
| `map54-inset-home-valley.png` | the home valley inset (1650 x 1500) |
| `map54-v53-vs-v54.png` | v53's and v54's maps side by side at 1920 x 1080 |
| `map54-labels-1920.png`, `map54-overlay-*-1920.png`, `map54-layer-*-1920.png`, `map54-realistic-1920.png`, `map54-base-1920.png` | as v53's |

```
python3 -I geo54.py                  # data and every map (about eight minutes)
RENDER_ONLY=1 python3 -I geo54.py    # the maps again from out/state-v54.pkl (about a minute)
QUICK=data python3 -I geo54.py       # the JSON and the state only
```

## v53: the continent overview map (27 Oct)

Matt, 27 Oct 17:25: "update and improve this overview map and add little place names and biome names for all. can you make it feel like a game map a bit more (in the way the terrain is distributed and the different zones/biomes), i like the current version and its realism but it can be changed a bit (not super massively) to be more fun and interesting to play (consider similarly expansive games). also can you add a ruler for scale (in the soft grid sense)." With his approved steps: the stone circle and the ring of craters, each crater's scorch pointing home; aligned with the region plans and routes; built zones and act 1's route shown; a cleaner overview closer to a stylised in-game map.

`geo53.py` (data) and `map53.py` (the map) sit on top of `geo52.py`. v52's land, rivers, settlements, routes and ways are kept; v53 adds to them. `continent-1x-v53.png` is the labelled overview at 1920 x 1080 (256 colours). It is our own render; nothing here is an image of another game.

### What the games do, and the principles applied

| Principle | Where it comes from | What v53 does |
| --- | --- | --- |
| A centre that everything reads from | A Link to the Past: "the most open spaces are the Village and the area northeast of it" ([Game Developer, ALttP's Light World, part 2](https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2)); Paldea's Great Crater "at the center of the region, bordered by the four provinces" (world-plan 3) | the map is centred on the stone circle; Crossroads is the routes' hub beside it; the craters ring it |
| Landmarks seen from far, revealed as you near them | Breath of the Wild: "Nintendo had to make them stick out from a distance"; "as you go towards these mountains, whatever's behind is gradually revealed" ([GMTK](https://gmtk.substack.com/p/how-nintendo-solved-zeldas-open-world)) | one great crater per region, violet glass on any ground, and the beam over the circle (world-and-cast.md) |
| Places sit where the player drifts, not on summits | "the player naturally ends up in the valleys and crevasses"; "important locations are never on a peak or summit" ([Game Developer, BotW analysis](https://gamedeveloper.com/design/breath-of-the-wild-open-world-analysis-gravity-to-go-forward)) | craters on flats and shelves 50 to 500 px off a route, each with a trail |
| Distinct, readable biome blocks | Paldea's provinces and Galar's Wild Area (world-plan 3) | the overview draws the ground as flat biome blocks with soft-grid tiers, named |
| Gates between regions | ALttP: Death Mountain "must be reached through a tunnel" (same article); Pokémon's gatehouses (world-plan 2) | every way's crossing drawn as a gate with its W number: the col, the cutting, Drover's bridge, the viaduct, the ferry, the chasm (lava) bridge, the crust causeway, the swing bridge, the stile, the Shell Bar |
| Loops and shortcuts | ALttP: "these newfound paths are simply shortcuts to locations that were already accessible by a longer route" (same article); TUNIC (world-plan 2) | four new routes, below |
| Small pockets often | Sea of Stars: "It feels like a game where it's all these small pockets" ([MobileSyrup interview](https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/)) | act 1's places given points; the v52 pockets kept |
| Varied path lengths: walking near, trains far | Eastward's trains, Galar's rail (world-plan 3) | rail, cart and ferry lines drawn and named |
| Interesting edges | world-plan 5.5 | the land past the walk drawn hazier, and the map fading out past the drawn edge (the land goes on) |
| An in-game map style | world-plan 12 (Matt's example 2, Stardew's warmth) | tiers as plateaus with south faces, house palette, upper-left light |

The Stardew Valley wiki page was not reachable from here; its point (Pelican Town in the middle, four exits) is already in world-plan 2.

### Geography changes (v52 to v53)

1. **The stone circle** at (5800, 3000) in the woodland's glade (the woodland zone's stones, placed in the valley plan's woodland rect; Claude A's golden screen keeps the exact spot). The map centres on it horizontally. Crossroads' square is at (6296, 3536).
2. **The ring of craters** (`CRATERS` in `geo53.py`): the Frostline crater (6480, 1590), the Heather crater on the Brackens (5300, 2390), the Seam crater in the coal hills (8260, 2130), the Lull crater (8150, 3560), the Company crater north of Neon's new town (10780, 4130), the Lagoon crater on the main isle (6330, 6420), the Glass field in the Sunstone basin (2160, 2760) and the Ember crater on the ash fields (3700, 4870); the Crossroads crater in the park (6484, 3712, already in `crossroads.json`) is the centre stone. Each is a glass bowl, a rim and a scorch that runs from the crater toward the circle (its heading equals the bearing home in every case, `stats-v53.json` v53.craters), with a trail to the nearest route. They lie 0.8 to 5.1 km from the circle: a rough ring, nearer in the north where the massif closes the land. Craters in deep forest blast their own clearing.
3. **Four new routes** (`NEW_ROUTES`): the **Heather Way** (the woodland's glade over the Brackens' moor top past the Heather crater, Old Fang's barrow and the drove well to the Brackens gap; a loop with the Drover's Road, 25 s), the **Glass Road** (Dust Gulch round the glass field to the Amber canyon; a loop off the Canyon Road, 17 s), **Fern Lane** (Fernhollow down to the Lull Road; closes the Foothill Road and the Lull Road into a loop, 21 s) and **Gull Lane** (the Lull Road down to Gullwick; a loop with the Coast Path, 26 s). None crosses a barrier, so the ways and their order are unchanged.
4. **Act 1's places** given points (`POI53`, proposals for lanes E and F): the ice caves (6080, 1660), the Saddle House (6440, 2010), Old Fang's barrow (4930, 2980), the spur tor (the Heather spur, 4990, 1960), the lighthouse (6600, 4995) and the Millrace landslip (the cutting). The bothy is the Frostline plan's cabin meadow.
5. **Waystones** (`WAYSTONES`): the five the plans place (Crossroads, Cogsworth, the footbridge, Fernhollow, the Cog foot) and thirteen proposed, one per settlement or threshold hub.
6. **No region plan place moved.** Every settlement, station, threshold, bridge and named thing keeps its v52 point, so no plan in `art/regions/` or `game/data/plans/` needed a change. The craters, new routes, places and waystones above are for the owning lanes to adopt in their plans (E: the valley and the Heather Way's east end; F: the Frostline, the Brackens; H: the coal hills, Fern Lane; I: Neon, Gull Lane; Sunstone and the fire country: the Glass Road and the Ember crater; C: the isles).

The biomes' identity and borders are sharpened in the drawing, not in the ground model: the overview merges speckle into biome blocks (a majority filter on the open ground), steps the tiers as soft-grid plateaus, and names every region and biome. The ground the lanes build from (`tiers`, routes, kinds) changes only where the craters, trails and new routes are painted.

### Checks

- The gate check: no leaks, nothing missing, no crossing without a way, at every step (`gates-v53.json`).
- The benchmark: **21 of 21 pass** (`stats-v53.json` benchmark). Fern Lane first failed check 16 (a straight 309 px); it now bends every 150 px or so.
- Reachable from home with every way open: every crater, act 1 place, waystone and the circle (`stats-v53.json` v53.reachable_with_every_way_open).
- Walkable zone-areas 149.5 (v52: 141.2; the new routes and crater trails widen the walked corridors). Times from the hut are unchanged at the plan's 40 px a second (Cogsworth 52 s, 25 s by train; Neon 115 s, 53 s; Dust Gulch 101 s, 30 s; Hearthold 130 s, 51 s). At Bramble's own speed (`home_to_at_hero_speed`): Cogsworth 80 s (39 s), Neon 177 s (82 s), Dust Gulch 155 s (46 s), Hearthold 200 s (78 s).
- A second run reproduces the three JSON files byte for byte.
- The labels: none overlaps another or an icon (the placer keeps every box); every name is placed except "the ria" (the city fills it), which the docks' and Harbour Bridge's names stand for.

### The scale ruler

One soft-grid cell is 8 world px, 24 art px at density 3 (`eastward-edges.md`). The hero's walk speed comes from the cast manifest: Bramble's `walk_speed` is 78.1 art px a second, 26.0 world px, 3.25 cells. So 10 cells take 3 s, 50 cells 15 s, 100 cells 31 s, and one 1080p screen (960 art px, 320 world px, 40 cells) 12.3 s to walk across. On the 1920 x 1080 map one pixel is 6.4 world px (0.8 cells). The ruler shows 10, 50, 100, 200 and 300 cells with their walk times, the screen as a box, and a north arrow.

### The maps (written to `out/`, and to `$MAP53_OUT` if set)

| File | What |
| --- | --- |
| `map53-1920.png`, `map53-3840.png` | the full map with every layer, at 1920 x 1080 and 2x |
| `map53-labels-1920.png` | the map and its names, without the overlays |
| `map53-overlay-built-1920.png`, `-act1-`, `-ring-` | each overlay alone on a muted map; `map53-layer-*-1920.png` are the transparent layers |
| `map53-realistic-1920.png` | the same layers on v52's realistic texture (the toggle) |
| `map53-v52-vs-v53.png` | v52's render and v53's map side by side at the same scale |

Overlays: the built zones (the woodland, Crossroads, and the Undercroft below the circle, dashed); act 1's route as a dotted line along the walk with its numbered beats (one order of `docs/story/act1.md`'s strands, listed in the legend); the ring of craters joined to the circle by faint lines.

```
python3 -I geo53.py                  # data and every map (about six minutes)
RENDER_ONLY=1 python3 -I geo53.py    # the maps again from out/state-v53.pkl (under a minute)
QUICK=data python3 -I geo53.py       # the JSON and the state only
```

The fonts are the game's own (`game/ui/fonts/PixelifySans-Regular.ttf` for region and biome names, Nunito for places) and DejaVu Serif for water. `game/tools/gen_blockout.py` (zone scenes from zone plans) is unchanged: it does not draw the continent.

## v5.2

This is the v5.2 block-out behind world plan v5.3 (`docs/vision/world-plan.md`, arrangement A). It was drawn by Claude A's scripts from a height field, a wetness field, the rivers and the paths, at one cell per 8 px. Until now it lived only in Claude A's scratchpad. The lanes building the world canvas (`docs/vision/region-canvas.md`) take their routes, tiers and region boxes from here.

It is a block-out, not art. Positions and tiers are the plan's; each lane's brief in `docs/vision/regions/` and the plan's later decisions take precedence where they differ (for example, the plain's many low tiers are to be merged into fewer banks, world plan 5.4).

## Files

| File                   | What it is                                                                                                                                                                                                                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `geo5.py`              | The v5 block-out: helpers (noise, polylines, rasterising), the tables (coast, massif, rivers, settlements, routes, ways, bridges, stations), the gate check, walk times and the renderer. `geo52.py` imports it.                                                                                       |
| `geo52.py`             | The v5.2 block-out on top of `geo5.py`: the land (`build51`), the Lull, delta and Neon Harbour, obstacles, borders, content, the benchmark, the tier field and the export below. Run it to regenerate every file here.                                                                                 |
| `blockout-v52.json`    | The geometry as data for the lanes (written by `export_blockout` in `geo52.py`): route and river polylines, the delta's arms, the tier grid, every tier change on a route, region and biome boxes with their origins, thresholds, lifts, settlements, bridges, stations, the ways and their crossings. |
| `stats-v52.json`       | The plan's measurements: walk times, routes' lengths, why each place is where it is, bridges, every named thing, pocket, obstacle and marker with its position, the mixing at each threshold, vertical stats per region, and the benchmark's 21 checks (all pass).                                     |
| `gates-v52.json`       | The gate check (world plan section 10): with each set of ways open, which places leak or go missing (none), and every place a route crosses a barrier with the way that opens it.                                                                                                                      |
| `geo53.py`, `map53.py`, `blockout-v53.json`, `stats-v53.json`, `gates-v53.json`, `continent-1x-v53.png` | v53, above: the same three files plus `v53` (circle, craters, new routes, places, waystones, built zones, act 1's beats), and the overview map. |
| `geo54.py`, `map54.py`, `blockout-v54.json`, `stats-v54.json`, `gates-v54.json`, `continent-1x-v54.png`, `inset-home-valley-v54.png` | v54, above: v53's three files plus `v54` (the range, the desert, the edges, the label tiers, the inset), the overview map and the home valley inset. |
| `geo55.py`, `towns55.py`, `map55.py`, `blockout-v55.json`, `stats-v55.json`, `gates-v55.json`, `continent-1x-v55.png`, `inset-home-valley-v55.png`, `inset-neon-harbour-v55.png` | v55, above: the v55 canvas (v54's ground warped wider), the settlement footprints, the east coast and Launch Cape, Highgarth and the closed pass; its own three files, the overview map and two insets. |
| `continent-1x-v52.png` | Our own render of the whole continent at 1 px per 8 px cell (1408 x 864), hill-shaded from the upper left. Reduced to 256 colours to keep it small (the script writes the full-colour one to `out/`). Nothing in this folder is an image of another game.                                              |

## Coordinates

Everything is in **world px** on one plane: the continent is 11264 x 6912 px, origin (0, 0) at its top-left (north-west) corner, x running east and y running south. The fields are sampled on 8 px cells (1408 x 864 cells); cell (cx, cy) covers world px `[cx * 8, cy * 8]` to `[(cx + 1) * 8, (cy + 1) * 8]`. World tiles are 256 px, as in `region-canvas.md`. One tier is a 32 px face on the soft grid.

## What is in `blockout-v52.json`

- `coords`: the system above.
- `routes`: per route, `kind` (road, path, bar, bridge), `width_px`, `features` (the ground fitted to it, switchbacks, huts), `control` (the plan's control points) and `polyline` (the drawn line after meandering and switchbacks, the one the stats and tier changes are measured on). Both are lists of `[x, y]`.
- `rivers` and `delta_arms`: centrelines as `[x, y]` lists (the Lull, its tributaries and the other rivers; the Lull's eight distributaries).
- `tiers`: the tier grid, one row per 8 px cell row from north to south, run-length encoded as `tier, run, tier, run, ...`; each row's runs add up to 1408. Sea is -1. To decode a row in Python: `[t for t, n in zip(row[0::2], row[1::2]) for _ in range(n)]`.
- `tier_changes`: where each route changes tier: `route`, `kind` (stair, ramp or switchback), `x`, `y` and `tiers` (how many steps).
- `regions`: the plan's regions (the massif's edge, the Frostline, the home valley, the coal hills and the Narrows, the Lull plain, the Lull belt and delta, Neon Harbour, the Sunstone basin, the Rift, the fire country, the coast and the isles). Each has `box` (`[x0, y0, x1, y1]` as planned), `origin` (the box's top-left snapped down to the 8 px grid), `size` (snapped up to the 8 px grid), `tiles256` (the first and last 256 px tile columns and rows it reaches) and `vertical` (tiers walked, the full tier range, typical and largest face in px, stairs, ramps and switchback steps).
- `biomes`: the same for the content biomes `stats-v52.json` counts by.
- `crops`: the boxes of the plan's region and route crops (the images listed in the world plan).
- `thresholds`, `lifts`, `settlements` (`x`, `y`, `radius_px`, `kind`), `bridges`, `stations`, `ways` (`[x, y, radius]` discs per way), `way_names` and `crossings`.

## How the lanes use it

- **Routes (lane G).** Lay each route chunk along its `polyline`, at its `width_px`, and put a stair, ramp or switchback at each of its `tier_changes`. The `thresholds` are the places where one region turns into the next; G draws the threshold object there.
- **Tiers per region (all lanes).** Read a region's tiers from the `tiers` grid inside its box, and the summary in `regions[name].vertical`. Merge the plain's many low tiers into a few deliberate banks rather than copying them step for step.
- **Region origins (all lanes).** A region's chunk on the world canvas is placed at `regions[name].origin`, on the 8 px grid; `tiles256` says which world tiles it reaches. Chunks on one plane may touch but never overlap (`region-canvas.md`), so where two boxes overlap here, the lanes agree the line in their briefs' threshold tables.
- **Water.** The `rivers` and `delta_arms` centrelines give where the water runs; the widths are the brief's and the kits'.

Lane F takes the Frostline and the massif's edge, G the routes, thresholds and edges, H the coal hills and the Narrows (with Cogsworth and Fernhollow from `settlements`), I Neon Harbour and the Lull belt and delta (with Lullford and Gullwick).

## Regenerating

From this folder:

```
python3 -I geo52.py
```

It needs Python 3 with numpy, scipy, scikit-image and Pillow, and the DejaVu fonts at `/usr/share/fonts/truetype/dejavu/`. It writes the three JSON files next to itself and every render (the continent, the labelled map, the physical map, the tier map, the in-game map mock, the region, route and boundary crops, the content map and the transitions sheet) to `out/`, which is git-ignored; set `BLOCKOUT_OUT` to write the renders somewhere else. `QUICK=none python3 -I geo52.py` writes the JSON, the 1x continent and the tier map only (about five minutes). The output is deterministic: a fresh run reproduces the committed `stats-v52.json` and `gates-v52.json` byte for byte.
