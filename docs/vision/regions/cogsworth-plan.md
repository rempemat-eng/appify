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
  - **Buildings** as the pictures they make: the camera looks north, so every front faces south and stands on its foot line, and the rect is the picture's screen box (what stands north of a building is behind it, and the whole picture stops a walker). Fronts are from the house kits in Cogsworth's brick and iron; the station, mills, foundry, works and terminus are wider fronts built from the same pieces. Then the **landmarks** (clock tower, airship mast on the hill, the ring in the square, canal crane, humpback and swing bridges, lock gates, the Millrace bridge, waterwheels, buffers, the maglev's piers), **stairs and ramps**, **railings** (the platform's edge over the square), **bridges**, the **gates** where the High Fells, the Foothill Road and the Towpath meet the town, the **stands** (today's ids kept: `junction:platform`, `tower`, `ring`, `workshop`, `canal`; `canal:junction`, `bridge`, `boat`, `lock`, `foundry`, `terminus`, `allotments`; new: `hill:gasholder`, `hill:mast`, `terminus:pump-house`) and the **areas** (`junction`, `hill`, `canal`, `terminus`: today's zone ids and the two `world-ways.ts` plans, on the world audit's 32 px cells).
  - **Slots**: 19 interactables plus 16 doors, and 25 story props (benchmark check 1 asks 6 of each a settlement screen; the town is 3.7 screens).
- **`rasterize()`** turns the town into 4 px cells: a ground-kind map, the walk and the tier map in the audit's code (`f` face, `b` side band, `s` stair or ramp), with faces carved south of every higher top at the step's height and a bridge's sides as parapets.

## What the check holds

On the grid and inside the boxes; no edge of ground over 96 px without a jog (rails, platform edges, streets and the riverside are reported as notes, since kerbs and fronts break them in the art); faces 12, 16, 32 or 40 px; the audit's tier rules (`world_audit.py` `tier_checks`: no walkable cells on two tiers meeting without a stair, no north faces, every drop south a face, every west or east end a side band, stairs 32 px or wider); stairs at least 34 px open and ramps 1 in 3; every stand, door and gate reached from the platform; nothing more than 30 % farther from the platform than the brief's walk times (nearer is no fault); the benchmark's density; the brief's counts (14 named things, 5 pockets, 91 markers); no named thing or spoil heap inside the town.

Walk times from the platform (brief, then plan): clock tower 7.8 / 6.9 s, gasholder 10.3 / 12.3, airship mast 13.2 / 13.4, lock 18.1 / 13.6, foundry 21.8 / 20.7, allotments 22.7 / 21.2, pump house 26.0 / 21.4, terminus 29.5 / 22.7. The plan's town is denser than the block-out's, so the south side is a few seconds nearer.

## Moved from the brief

The brief's coordinates come from a smaller, coarser block-out town; things are moved to fit the decided 704 x 960 town (`MOVED` lists each with its reason):

- the platform stop to the town's north edge (the brief's point was the block-out town's centre);
- the spoil heap with the loop to the bench above the town; the crow roost, the cairn and the echo cave up the High Fells to the bench and its face; the charcoal burners' camp to the Cog's west bank before the Millrace bridge; the rail ruin a short way off the Towpath east of the town; two spoil heaps to the Cog's west bank and one below the riverside;
- the routes' ends to the town's gates; the 23 route markers that fell inside the town box are laid as town slots of the same kinds.

## Waiting on

- **Claude G** (routes): the exact cells where the High Fells, the Foothill Road and the Towpath meet the town's gates, and the W3 object at the Millrace bridge.
- **The cliff core** (#165): the gorge walls and the coal hills' benches. Their tiers wait for the geography chunk (P1); until then the gorge is a course and a width, not a tier map.
- **The city kit** (Claude C, #169, stacked on the coast kit #162): setts, flags, kerbs, brick retaining walls and quays for the town's ground.
- **Claude B**: the eel-catcher's camp, the fallen climber's camp and the rail ruin (to draw); the Millrace wheel; the tram tipple, pit head, lookout, charcoal clamp and burners' hut are drawn (#163), the windmill is on #172.
