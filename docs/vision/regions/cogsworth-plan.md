# Cogsworth, the coal hills, the Narrows and Fernhollow: the plan as data

**Owner: Claude H** (lane H, from 21 Oct; taken over from Claude C). The brief is `cogsworth-coal-hills-narrows.md` (world plan v5.3, PR #96). The plan is `scripts/art/regions/cogsworth_plan.py`; the region's painter reads it, so the drawing follows one plan, and its check holds the plan to the rules a plan can show before anything is drawn.

```
python3 scripts/art/regions/cogsworth_plan.py --check      # exits non-zero on a fault
python3 scripts/art/regions/cogsworth_plan.py OUT_DIR      # town-blockout-2x.png, region-quarter.png, town-tiers.txt
```

Nothing in the game reads it yet.

## What it holds

- **The region** in world px: the footprint (x 7000 to 9300, y 1700 to 3300), the places with their boxes, the Narrows gorge (the Lull's course, 44 px of white water, the viaduct at its narrowest point), the maglev from the terminus to the viaduct, the spoil heaps, the 14 named things with the sprite or kit piece each needs, the 5 secret pockets, the 73 route and Fernhollow markers, the obstacles, the thresholds (the Millrace cutting and the Cog foot) and the edges.
- **The town** (704 x 960, decided) at world (7624, 1968), centred on the brief's (7980, 2450), in its own box px:
  - **Tiers** (the audit's digits): 0 the Cog, 1 the Millrace and the canal (half a tier, 16 px, below the street), 2 the street, 3 the coal-hill bench and Gasworks Hill. One tier is 32 px here (the coal hills' measure; the 40 px city tier is Neon's).
  - **Ground** as polygons on the 8 px grid, each with the kit that draws it: the Cog down the west side and east along the south, the Millrace through the mills, the canal across the middle with its lock at the Cog and the basin east, the platform and rails on the north edge, the station square (240 x 176) under the clock tower, Workshop Street and Main Street (48 px), the wharf, the towpath, the foundry yard, the allotments, the terminus forecourt, the riverside.
  - **Buildings** as the pictures they make: the camera looks north, so every front faces south and stands on its foot line, and the rect is the picture's screen box (what stands north of a building is behind it, and the whole picture stops a walker). Fronts are from the house kits in Cogsworth's brick and iron; the station, mills, foundry, works and terminus are wider fronts built from the same pieces. Then the **landmarks** (clock tower, airship mast on the hill, the ring in the square, canal crane, humpback and swing bridges, lock gates, the Millrace bridge, waterwheels, buffers, the maglev's piers), **stairs** (no ramps: eastward-edges.md 6.3), **railings** (the platform's edge over the square), **bridges**, the **gates** where the High Fells, the Foothill Road and the Towpath meet the town, the **stands** (today's ids kept: `junction:platform`, `tower`, `ring`, `workshop`, `canal`; `canal:junction`, `bridge`, `boat`, `lock`, `foundry`, `terminus`, `allotments`; new: `hill:gasholder`, `hill:mast`, `terminus:pump-house`) and the **areas** (`junction`, `hill`, `canal`, `terminus`: today's zone ids and the two `world-ways.ts` plans, on the world audit's 32 px cells).
  - **Slots**: 19 interactables plus 16 doors, and 25 story props (benchmark check 1 asks 6 of each a settlement screen; the town is 3.7 screens).
- **`rasterize()`** turns the town into 4 px cells: a ground-kind map, the walk and the tier map in the audit's code (`f` face, `b` side band, `s` stair or ramp), with faces carved south of every higher top at the step's height and a bridge's sides as parapets.

## What the check holds

On the grid and inside the boxes (long straight runs along the grid are right: Matt, 21 Oct 11:44, to-all-grid-2x withdrew the rule against them); faces 12, 16, 32 or 40 px; the audit's tier rules (`world_audit.py` `tier_checks`: no walkable cells on two tiers meeting without a stair, no north faces, every drop south a face, every west or east end a side band, stairs 32 px or wider); stairs at least 34 px open (no ramps); every stand, door and gate reached from the platform; nothing more than 30 % farther from the platform than the brief's walk times (nearer is no fault); the benchmark's density; the brief's counts (14 named things, 5 pockets, 91 markers); no named thing or spoil heap inside the town.

Walk times from the platform (brief, then plan): clock tower 7.8 / 6.9 s, gasholder 10.3 / 12.3, airship mast 13.2 / 13.4, lock 18.1 / 13.6, foundry 21.8 / 20.7, allotments 22.7 / 21.2, pump house 26.0 / 21.4, terminus 29.5 / 22.7. The plan's town is denser than the block-out's, so the south side is a few seconds nearer.

## The region round the town

`scripts/art/regions/cogsworth_region.py` lays the rest of the footprint as data on the world's 8 px cells, independent of the art's density (crew board to-all-density: until Matt picks the density, the lanes work on layout, routes, walk masks and set-piece placement):

- **Tiers** as rectangles on the grid in straight runs (to-all-grid-2x), lowest first, in Claude G's tier numbers (the town's street is 7): the massif's benches stepping down south-east where the High Fells come down (13 to 8), the Fern hills' shoulder carrying the Foothill Road over tier 9, the coal hills rising east of the town to the Narrows' rims (9, 10), the Cog's valley and the confluence low (6, 5) and the Lull at 4.
- **Water**: the Cog above the town and below it to the confluence, the Lull through the Narrows and on south-east to Claude I's chunk, the eel pond at Fernhollow.
- **Routes**: Claude G's lines, read from `lib/world-routes.ts` (#175, on main), with a copy of their vertices on this land as the fallback.
- **Set pieces** with the prop or kit piece each needs: the 14 named things, five spoil heaps (one with the loop), the viaduct's three piers, Fernhollow's three cottages, sawpit and log stores.
- **Cover in layers** (brief 6): the massif's wall and fade, the old forest's wall and fade, the coal forest's woods.

`--check` holds it to what a layout can show: every route vertex on land of its own tier (within 64 px of a tier change), no route on water except at its crossings, no set piece on a route, on water, in the town or on another, each named thing beside or a short way off its route, Fernhollow's doors onto the road, the Lull running from the north edge to the confluence, the town's gates on G's tiers, no wall across a route. Asked of G (h-to-g-1115): the five stairs on east-west legs, the High Fells' bridge over the Cog (W3), and the Towpath south of the Cog foot, where G and Claude I differ.

## Moved from the brief

The brief's coordinates come from a smaller, coarser block-out town and the block-out's routes; things are moved to fit the decided 704 x 960 town and Claude G's route lines (`MOVED` lists each with its reason):

- the platform stop to the town's north edge (the brief's point was the block-out town's centre);
- the named things beside or a short way off G's line for their route, off the road, out of the water and out of the town: the crow roost, the cairn and the echo cave up on the bench and its face where the High Fells come down; the burners' camp and the collapsed adit beside the Foothill Road on the Fern hills' shoulder; the rail ruin and the tram tipple on the coal hills' foot by the Towpath; the lookout above the Cog foot;
- the five spoil heaps out of the town and the Cog onto the hills round it, one above the town with the loop;
- the routes' ends to the town's gates; the 23 route markers that fell inside the town box are laid as town slots of the same kinds.

## Waiting on

- **Claude G** (routes): the gates are agreed (north 8, west 7, east 7); open are the five stairs on east-west legs, the High Fells' bridge over the Cog, and the Towpath south of the Cog foot (h-to-g-1115).
- **The cliff core** (#165): the gorge walls and the coal hills' benches. Their tiers wait for the geography chunk (P1); until then the gorge is a course and a width, not a tier map.
- **The city kit** (Claude C, #169, stacked on the coast kit #162): setts, flags, kerbs, brick retaining walls and quays for the town's ground.
- **Claude B**: the eel-catcher's camp, the fallen climber's camp and the rail ruin (to draw); the Millrace wheel; the tram tipple, pit head, lookout, charcoal clamp and burners' hut are drawn (#163), the windmill is on #172.
