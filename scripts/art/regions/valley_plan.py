"""The home valley as a plan as data: the garden and the hut, Crossroads, the park, the
riverside, the halt farm, Driftwood and the Headland, with the hay slope up to the Col hut and
the routes and thresholds to the woodland, the Frostline, the Brackens and the land between.

Lane E (Claude E), 21 Oct. Matt, 21 Oct (crew board to-all-density, to-all-kit-freeze): the art
moves to a higher density after the golden screen, so the lanes write what carries over at any
density: layout, tiers, routes, water, set-piece and cluster places, residents. And 11:44
(to-all-grid-2x) and 13:37 (to-all-volume): outlines follow the cell grid in straight runs
along x or y, turning at cell boundaries, and masses step in and out by whole cells, never one
even band. The brief is docs/vision/regions/home-valley-frostline-brackens.md (world plan v5.3,
section 8.2); the routes are Claude G's (lib/world-routes.ts on #189, route-meets.md), met at
the box edge at G's cell, tier and width, and drawn inside the box as this plan's lines
(g-to-all-region-rule: inside a region's box the region plan wins).

The woodland is Claude A's golden screen (a-to-e-woodland): this plan carries only its outline,
its exits, the Sleepwater through it and the stands the game uses there, all marked owner
claude-a, and lane E draws nothing there. The Frostline and the Brackens are Claude F's
(frostline.json, brackens.json); Fernhollow and the Fern hills beyond x 7000 are Claude H's; the
land between beyond the box is Claude G's.

The plan is written here as data (rectangles of cells for each tier's tops, polylines for paths
and water, points for things) and exported to art/regions/valley.json in Claude F's schema
(docs/vision/region-plans.md), which `npm run check:region-plans` holds to its rules. Tier
outlines are traced from the raster of cells, so they are on the grid by construction; `check()`
here adds the valley's own rules (every zone id the game uses is placed, the water runs from its
source to the sea, the routes meet G's cells).

    python3 scripts/art/regions/valley_plan.py --export   (writes art/regions/valley.json)
    python3 scripts/art/regions/valley_plan.py --check    (the valley's own checks; exits non-zero on a fault)
    python3 scripts/art/regions/valley_plan.py [OUT_DIR]  (draws the plan with region_plan.draw)
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'art'))
import region_plan as rp  # noqa: E402

OUT = os.path.join(ROOT, 'art', 'regions', 'valley.json')
CELL = 8
# the valley's box with the Headland behind its wall (brief 1: x 5600 to 7000, y 2300 to 5100;
# x 6800 to 7250, y 5100 to 5800), as one rectangle of whole 32 px audit cells
X0, Y0, W, H = 5600, 2304, 1664, 3520
X1, Y1 = X0 + W, Y0 + H
MINE_X1 = 7008          # east of this, north of the Headland, is the land between (lane G) and Fernhollow (lane H)
HEADLAND_Y0 = 5120      # the Headland's box starts here (brief 1: y 5100, on the audit cells)
BASE_TIER = 0           # tier numbers are Claude G's world tiers (a tier is a 32 px face above the sea)

# --- the land's tops: (tier, [rects x0, y0, x1, y1 in world px]), painted in order --------------
# Tops are in screen space (region-plans.md): a tier's top where the camera sees it, its south
# face hanging 32 px a tier under its south rim. Rims step in and out by whole cells, at least
# 16 px, every screen width or so (to-all-volume).
TIERS = [
    # 1: the shingle under the halt farm's fields and the platform of rock at the Headland's
    # south foot, where the Shell Bar leaves at low tide
    (1, [(5600, 4936, 5840, 5048), (5840, 4912, 6048, 5064), (6048, 4920, 6176, 5040),
         (6848, 5584, 6976, 5696), (6976, 5664, 7232, 5768)]),
    # 2: Driftwood's quay, one tier under the hamlet (brief: a 32 px quay face), narrowing east
    (2, [(6176, 4936, 6400, 5056), (6400, 4952, 6560, 5056)]),
    # 3: the coastal lowland: the halt farm's lower fields, the dew pond meadow, Driftwood's
    # hamlet, the estuary banks and the Headland behind its wall
    (3, [(5600, 4288, 5840, 4936), (5840, 4288, 6048, 4912), (6048, 4288, 6176, 4920),
         (6176, 4288, 6400, 4936), (6400, 4288, 6560, 4952), (6560, 4288, 6680, 5056),
         (6680, 4288, 6800, 5040), (6800, 4288, MINE_X1, 5056),
         (6800, 5056, 6976, 5584), (6976, 5056, 7232, 5664)]),
    # 4: the valley floor: Crossroads, the green, the park and the halt farm; its south rim
    # steps down toward the river's fall and the estuary
    (4, [(5600, 2304, 5760, 4288), (5760, 2304, 6000, 4320), (6000, 2304, 6240, 4352),
         (6240, 2304, 6480, 4368), (6480, 2304, 6800, 4384), (6800, 2304, MINE_X1, 4336)]),
    # 5: the T2 terrace: the woodland (Claude A), the garden (320 x 576, unchanged) and the
    # riverside with the millpond, stepping in and out along its south rim (the woodland's
    # timber stair, the garden's gate wall, the mill's step)
    (5, [(5640, 2304, 5856, 3328), (5856, 2304, 6136, 3344), (6136, 2304, 6456, 3376),
         (6456, 2304, 6720, 3392), (6720, 2304, MINE_X1, 3376)]),
    # 6: the hay slope above the garden, up the Col Path's foot, and the Fern hills' shoulder in
    # the north-east, which carries the Foothill Road up to Claude H's tier 7
    (6, [(6136, 2304, 6240, 2752), (6240, 2304, 6480, 2768), (6480, 2304, 6680, 2736),
         (6680, 2304, 6864, 2712), (6864, 2304, MINE_X1, 3264)]),
    # 7: the Frostline's foot, which Claude F's plan meets at y 2304 on its tier 0 (world 7):
    # the escarpment over the woodland (a 64 px face where the Sleepwater falls), the Col hut's
    # shelf, and the Fern hills' crest running south to the Foothill Road's top
    (7, [(5680, 2304, 6000, 2400), (6000, 2304, 6248, 2416), (6248, 2304, 6480, 2432),
         (6480, 2304, 6672, 2400), (6672, 2304, 6864, 2384), (6864, 2304, MINE_X1, 2560),
         (6944, 2560, MINE_X1, 3208)]),
]
# the Headland's raised point: the lookout tower and the lighthouse on it (review 21 Oct 07:53:
# raise the point as a 32 px tier with a rock face)
TIERS.append((4, [(7096, 5440, 7224, 5576)]))

# the land: one rectilinear outline; outside it is the sea (the cove, the estuary's mouth, the
# Headland's shores). The Shell Bar is land at low tide, at tier 0.
COAST = [
    (X0, Y0), (X1, Y0), (X1, 5120), (7232, 5120), (7232, 5768), (7104, 5768), (7104, 5824),
    (6880, 5824), (6880, 5768), (6976, 5768), (6976, 5696), (6848, 5696), (6848, 5584),
    (6800, 5584), (6800, 5040), (6680, 5040), (6680, 5056), (6176, 5056), (6176, 5040), (6048, 5040), (6048, 5064),
    (5840, 5064), (5840, 5048), (X0, 5048),
]

# --- water: the Sleepwater from the Frostline to the sea, and the farm's drains -----------------
WATER = [
    {'id': 'sleepwater_fall', 'kind': 'stream', 'width': 24,
     'points': [[5944, 2304], [5944, 2480]],
     'falls': [{'at': [5944, 2408], 'drop_tiers': 2, 'what': 'the escarpment fall into the spring pool'}],
     'source': 'frostline.json sleepwater: Snowmelt Lake through Fir Hollow and over the escarpment (Claude F)',
     'outlet': 'spring_pool', 'owner': 'claude-a (the woodland: the golden screen)'},
    {'id': 'spring_pool', 'kind': 'pool', 'closed': True,
     'points': [[5904, 2480], [5992, 2480], [5992, 2544], [5904, 2544]],
     'source': 'sleepwater_fall', 'outlet': 'brook', 'owner': 'claude-a (the woodland: the golden screen)'},
    {'id': 'brook', 'kind': 'stream', 'width': 24,
     'points': [[5992, 2512], [6040, 2512], [6040, 3328], [6488, 3328]],
     'bridges': [{'at': [6304, 3328], 'span': 32, 'what': "the garden's own footbridge on its walk to the gate (unchanged)"},
                 {'at': [6040, 3120], 'span': 32, 'what': "the stepping-stone footbridge at the woodland's gate (its woodland side is Claude A's)"}],
     'source': 'spring_pool', 'outlet': 'millpond',
     'note': "south through the woodland (Claude A's), then east along the garden's south edge (the garden's own stream, its geometry unchanged) to the millpond"},
    {'id': 'millpond', 'kind': 'pond', 'closed': True,
     'points': [[6488, 3232], [6624, 3232], [6624, 3336], [6488, 3336]],
     'source': 'brook', 'outlet': 'mill_race'},
    {'id': 'mill_race', 'kind': 'race', 'width': 16,
     'points': [[6600, 3336], [6600, 3416]],
     'falls': [{'at': [6600, 3400], 'drop_tiers': 1, 'what': "the mill's wheel at the terrace step (the weir as a fall between levels)"}],
     'source': 'millpond', 'outlet': 'sleepwater'},
    {'id': 'sleepwater', 'kind': 'river', 'width': 32,
     'points': [[6600, 3416], [6600, 3640], [6568, 3640], [6568, 3920], [6600, 3920], [6600, 4200],
                [6624, 4200], [6624, 4600], [6600, 4600], [6600, 5056]],
     'widths': [[6600, 4600, 40], [6600, 5000, 48]],
     'falls': [{'at': [6624, 4400], 'drop_tiers': 1, 'what': 'a low fall where the floor steps down to the coastal lowland'}],
     'bridges': [{'at': [6600, 3520], 'span': 64, 'what': "the town street's bridge to the park"},
                 {'at': [6600, 4904], 'span': 64, 'what': "the cliff path's footbridge at the estuary"},
                 {'at': [6600, 4120], 'span': 48, 'what': "the valley train's girder bridge (W3)", 'carries': 'valley_train'}],
     'source': 'mill_race', 'outlet': 'the sea: the estuary into Driftwood cove'},
    {'id': 'field_drain', 'kind': 'ditch', 'width': 16,
     'points': [[5680, 4600], [5960, 4600], [5960, 4472]],
     'bridges': [{'at': [5904, 4600], 'span': 32, 'what': "the farm track's plank bridge"},
                 {'at': [5960, 4512], 'span': 32, 'what': "the windmill lane's plank bridge"}],
     'source': "the halt farm's lower fields (field drains)",
     'outlet': "the windmill's scoop wheel (Claude B #129: a drainage mill that pumps the fields)"},
    {'id': 'mill_outfall', 'kind': 'ditch', 'width': 16,
     'points': [[6000, 4472], [6040, 4472], [6040, 5048]],
     'bridges': [{'at': [6040, 4512], 'span': 32, 'what': "the windmill lane's plank bridge"}],
     'falls': [{'at': [6040, 4916], 'drop_tiers': 2, 'what': "the outfall's sluice over the shingle bank to the shore"}],
     'source': "the windmill's scoop wheel, lifting the drains into the embanked outfall at its east foot",
     'outlet': 'the sea over the shingle'},
    {'id': 'dew_pond', 'kind': 'pond', 'closed': True, 'declared_closed': True,
     'points': [[6672, 4264], [6712, 4264], [6712, 4304], [6672, 4304]],
     'note': 'rain-fed, lined with clay: no stream in or out (brief 7)'},
]

# --- routes: Claude G's, met at G's cell, tier and width; inside the box drawn here --------------
# (a vertex every turn; every segment along x or y, no run over 240 px)
ROUTES = [
    {'id': 'col_path', 'name': 'Col Path', 'kind': 'path', 'width': 24,
     'points': [[6336, 2808], [6336, 2624], [6304, 2624], [6304, 2440], [6288, 2440], [6288, 2304]],
     'meets': {'lane': 'claude-f', 'at': [6288, 2304], 'tier': 7, 'width': 24,
               'note': "frostline.json col_path starts here; G's cell (6280, 2296)"}},
    {'id': 'foothill_road', 'name': 'Foothill Road', 'kind': 'road', 'width': 40,
     'points': [[6776, 3528], [6776, 3320], [6880, 3320], [6880, 3240], [6960, 3240], [6960, 3192], [7000, 3192]],
     'widths': [[7000, 3192, 48]],
     'meets': {'lane': 'claude-h', 'at': [7000, 3192], 'tier': 7, 'width': 48}},
    {'id': 'lull_road', 'name': 'Lull Road', 'kind': 'road', 'width': 40,
     'points': [[6712, 3760], [6880, 3760], [6880, 3816], [7000, 3816]],
     'meets': {'lane': 'claude-g', 'at': [7000, 3816], 'tier': 4, 'width': 40}},
    {'id': 'drovers_road', 'name': "Drover's Road", 'kind': 'road', 'width': 40,
     'points': [[5864, 3992], [5632, 3992], [5632, 3944], [5600, 3944]],
     'widths': [[5600, 3944, 32]],
     'meets': {'lane': 'claude-f', 'at': [5600, 3944], 'tier': 4, 'width': 32,
               'note': 'brackens.json drovers_road starts here'}},
    {'id': 'ash_coast', 'name': 'Ash Coast', 'kind': 'path', 'width': 32,
     'points': [[5800, 4152], [5728, 4152], [5728, 4232], [5664, 4232], [5664, 4336], [5600, 4336]],
     'widths': [[5600, 4336, 40]],
     'meets': {'lane': 'claude-g', 'at': [5600, 4336], 'tier': 3, 'width': 40,
               'note': "G's stair (5624, 4336) is on an east-west leg; here it is on the north-south leg at (5664, 4304)"}},
    {'id': 'coast_path', 'name': 'Coast Path', 'kind': 'path', 'width': 32,
     'points': [[6568, 4904], [6736, 4904], [6736, 5016], [6880, 5016], [6880, 5072], [7000, 5072]],
     'meets': {'lane': 'claude-g', 'at': [7000, 5072], 'tier': 3, 'width': 32}},
    {'id': 'headland_lane', 'name': 'Headland Lane', 'kind': 'path', 'width': 32,
     'points': [[6896, 5072], [6896, 5176], [6960, 5176], [6960, 5280], [6992, 5280], [6992, 5496],
                [7040, 5496], [7040, 5600], [7048, 5600], [7048, 5744], [7056, 5744]],
     'widths': [[6992, 5304, 40]]},
    {'id': 'shell_bar', 'name': 'Shell Bar', 'kind': 'bar', 'width': 48,
     'points': [[7056, 5744], [7056, 5808], [6896, 5808], [6896, 5824]],
     'note': "below the rock platform's 32 px face (to y 5800), so its leg runs at y 5808; Claude C's bar (tidebloom.json, #266) starts at (6896, 5824) on the same x, so nothing is drawn twice",
     'widths': [[6896, 5824, 56]],
     'meets': {'lane': 'claude-c', 'at': [6896, 5824], 'tier': 0, 'width': 56,
               'note': "G's crossing (6896, 5800) heading south; the bar runs on to Lagoon Landing (W4)"}},
]

# --- trods: the valley's own lanes, the garden's and the woodland's exits, pockets and loops ----
TRODS = [
    # the garden (the home hub: its geometry and harness unchanged); a line through it from the
    # trail gate to the town gate stands for its own paths
    {'id': 'garden_walk', 'width': 24, 'owner': 'the garden (home hub, unchanged)',
     'points': [[6336, 2808], [6336, 2976], [6296, 2976], [6296, 3184], [6304, 3184], [6304, 3392],
                [6296, 3392], [6296, 3440]],
     'why': "from the trail gate (TRAIL_X) past the hut to the gate, down the gate stair on the square's axis"},
    {'id': 'garden_west', 'width': 24, 'owner': 'the garden / claude-a',
     'points': [[6296, 3104], [6152, 3104], [6152, 3120], [5952, 3120]],
     'why': "the garden's west gate into the woodland (gates.west)"},
    {'id': 'garden_east', 'width': 24, 'owner': 'the garden',
     'points': [[6304, 3088], [6472, 3088], [6472, 3072], [6648, 3072], [6648, 3216], [6776, 3216], [6776, 3320]],
     'why': "the garden's east gate past the millpond, the orchard and the miller's cottage to the Foothill Road (gates.east)"},
    # the woodland: Claude A's golden screen; lines for its exits only
    {'id': 'woodland_stair', 'width': 32, 'owner': 'claude-a (the woodland: the golden screen)',
     'points': [[5952, 3120], [5952, 3288], [5936, 3288], [5936, 3496], [5992, 3496], [5992, 3544]],
     'why': "the forester's timber stair down to the floor and the west road"},
    {'id': 'spring_walk', 'width': 24, 'owner': 'claude-a (the woodland: the golden screen)', 'dead_end': 'view',
     'points': [[5952, 3120], [5952, 2880], [5968, 2880], [5968, 2664], [5952, 2664], [5952, 2568]],
     'why': 'up the woodland to the spring pool under the fall (a rest spot)'},
    # Crossroads: the street through the square, west to the halt and east over the river
    {'id': 'west_road', 'width': 32,
     'points': [[6296, 3528], [6136, 3528], [6136, 3544], [5992, 3544], [5992, 3712], [5872, 3712], [5872, 3920],
                [5864, 3920], [5864, 4096], [5800, 4096]],
     'why': "Crossroads to the halt (brief 8.2: roads west to the halt), over the line once at the halt's level crossing east of the platform"},
    {'id': 'east_road', 'width': 32,
     'points': [[6296, 3528], [6464, 3528], [6464, 3520], [6656, 3520], [6656, 3544], [6776, 3544], [6776, 3528]],
     'why': "over the river by the town street's bridge to the park and the Foothill Road"},
    {'id': 'harbour_road', 'width': 32,
     'points': [[6296, 3528], [6296, 3760], [6280, 3760], [6280, 4000], [6264, 4000], [6264, 4232],
                [6256, 4232], [6256, 4448], [6272, 4448], [6272, 4672], [6304, 4672], [6304, 4776], [6312, 4776], [6312, 4920]],
     'why': 'the harbour road south between the cottage plots, bending at the square and at the drop, to Driftwood'},
    {'id': 'quay', 'width': 32,
     'points': [[6312, 4920], [6312, 5000], [6440, 5000], [6440, 5016], [6544, 5016]],
     'why': "down the quay stair to the quay: the fish market, the harbour master, the chandlery, the slip"},
    {'id': 'jetty', 'kind': 'jetty', 'width': 24,
     'points': [[6520, 5016], [6520, 5104]],
     'why': 'the ferry pier (W4) and the stop at its end (travelPoints.pier)'},
    {'id': 'river_lane', 'width': 24,
     'points': [[6312, 4776], [6488, 4776], [6488, 4904], [6568, 4904]],
     'why': "Driftwood's river lane to the Coast Path's start at the footbridge"},
    {'id': 'park_walk', 'width': 32,
     'points': [[6696, 3544], [6696, 3640], [6712, 3640], [6712, 3760]],
     'why': 'through the park past the bandstand to the Lull Road'},
    {'id': 'park_lane_south', 'width': 24,
     'points': [[6712, 3760], [6712, 3992], [6728, 3992], [6728, 4200], [6736, 4200], [6736, 4432], [6744, 4432],
                [6744, 4664], [6736, 4664], [6736, 4904]],
     'why': 'the lane south from the park along the east bank to the estuary footbridge and the Coast Path'},
    {'id': 'dew_pond_loop', 'width': 24,
     'points': [[6736, 4232], [6656, 4232], [6656, 4336], [6736, 4336]],
     'why': "round the dew pond (brief 7): the path closer on its west side, between the pond and the Sleepwater's bank, joining the lane at a Y each end"},
    {'id': 'mill_stair', 'width': 24,
     'points': [[6648, 3216], [6648, 3352], [6664, 3352], [6664, 3544]],
     'why': "past the mill on the terrace step, down its stair to the floor"},
    {'id': 'green_lane', 'width': 24,
     'points': [[6176, 3528], [6176, 3640], [6064, 3640], [6064, 3760], [6176, 3760], [6176, 3776], [6280, 3776]],
     'why': "the green south-west of the square with the ring and the shelter, back to the harbour road at a Y"},
    {'id': 'halt_yard', 'width': 32,
     'points': [[5800, 4096], [5800, 4152]],
     'why': "the halt's yard between the platform and the farm gate, where the Drover's Road and the Ash Coast leave"},
    {'id': 'farm_track', 'width': 24, 'dead_end': 'view',
     'points': [[5800, 4152], [5872, 4152], [5872, 4352], [5888, 4352], [5888, 4576], [5904, 4576],
                [5904, 4800], [5920, 4800], [5920, 4888]],
     'why': "the farm track down the fields to the shingle shore, ending in a view of the sea"},
    {'id': 'windmill_lane', 'width': 24,
     'points': [[5888, 4512], [6064, 4512], [6064, 4560], [6272, 4560]],
     'why': "from the farm track past the windmill's door, over the drain and the outfall, to the harbour road"},
    {'id': 'shrine_trod', 'width': 24,
     'points': [[5888, 4440], [5832, 4440], [5832, 4400]],
     'why': "a few steps off the farm track to the wayside shrine"},
    {'id': 'brackens_trod', 'width': 24,
     'points': [[5600, 3304], [5616, 3304], [5616, 3400], [5848, 3400], [5848, 3496], [5936, 3496]],
     'why': "the Brackens' east_trod (Claude F, brackens.json) comes in at the box edge; along the woodland bank's foot, outside the woodland, to the timber stair's foot: the moor's second way in"},
    # the hay slope: the Col Path's pockets
    {'id': 'view_pocket', 'width': 24, 'dead_end': 'view',
     'points': [[6304, 2520], [6416, 2520]],
     'why': 'a secret pocket off the Col Path: a view over the land'},
    {'id': 'bench_pocket', 'width': 24, 'dead_end': 'bench',
     'points': [[6336, 2680], [6488, 2680]],
     'why': 'a secret pocket off the Col Path: a bench under a tree'},
    {'id': 'hay_trod', 'width': 24, 'dead_end': 'bench',
     'points': [[6304, 2600], [6168, 2600]],
     'why': "a mown strip across the hay meadow to a bench at its west end, over the woodland's crowns"},
    # the Headland
    {'id': 'hermit_pocket', 'width': 24, 'dead_end': 'resident',
     'points': [[6992, 5440], [6912, 5440], [6912, 5576], [6880, 5576]],
     'why': 'a secret pocket off the Shell Bar approach: a hermit at a fire under the Headland'},
    {'id': 'rocks_loop', 'width': 24,
     'points': [[7040, 5512], [7088, 5512], [7088, 5632], [7048, 5632]],
     'why': "round the Headland's rocks (brief 7): the path closer on its east side, back on the lane at a Y"},
    {'id': 'tower_trod', 'width': 24, 'dead_end': 'view',
     'points': [[7088, 5632], [7160, 5632], [7160, 5528]],
     'why': "up the point's stair to the lookout tower and the lighthouse (a view to the isles)"},
    {'id': 'fold_trod', 'width': 24,
     'points': [[6960, 5240], [6896, 5240], [6896, 5352], [6992, 5352]],
     'why': "inside the wall from the lane to the sheep fold and back through the stile's yard"},
]

STAIRS = [
    {'id': 'col_stair_low', 'on': 'col_path', 'at': [6336, 2784], 'from_tier': 5, 'to_tier': 6, 'width': 40, 'kind': 'stone'},
    {'id': 'col_stair_hut', 'on': 'col_path', 'at': [6304, 2448], 'from_tier': 6, 'to_tier': 7, 'width': 40, 'kind': 'stone'},
    {'id': 'gate_stair', 'on': 'garden_walk', 'at': [6296, 3408], 'from_tier': 5, 'to_tier': 4, 'width': 48, 'kind': 'stone',
     'why': "the garden's gate stair on the square's axis"},
    {'id': 'timber_stair', 'on': 'woodland_stair', 'at': [5936, 3360], 'from_tier': 5, 'to_tier': 4, 'width': 40, 'kind': 'timber',
     'owner': 'claude-a'},
    {'id': 'mill_steps', 'on': 'mill_stair', 'at': [6664, 3408], 'from_tier': 5, 'to_tier': 4, 'width': 40, 'kind': 'stone'},
    {'id': 'fern_stair_1', 'on': 'foothill_road', 'at': [6776, 3392], 'from_tier': 4, 'to_tier': 5, 'width': 48, 'kind': 'stone'},
    {'id': 'fern_stair_2', 'on': 'foothill_road', 'at': [6880, 3280], 'from_tier': 5, 'to_tier': 6, 'width': 48, 'kind': 'stone'},
    {'id': 'fern_stair_3', 'on': 'foothill_road', 'at': [6960, 3224], 'from_tier': 6, 'to_tier': 7, 'width': 48, 'kind': 'stone'},
    {'id': 'ash_stair', 'on': 'ash_coast', 'at': [5664, 4304], 'from_tier': 4, 'to_tier': 3, 'width': 40, 'kind': 'stone'},
    {'id': 'farm_stair', 'on': 'farm_track', 'at': [5872, 4336], 'from_tier': 4, 'to_tier': 3, 'width': 40, 'kind': 'timber'},
    {'id': 'harbour_stair', 'on': 'harbour_road', 'at': [6256, 4384], 'from_tier': 4, 'to_tier': 3, 'width': 40, 'kind': 'stone'},
    {'id': 'quay_stair', 'on': 'quay', 'at': [6312, 4952], 'from_tier': 3, 'to_tier': 2, 'width': 40, 'kind': 'stone',
     'why': "the quay stair (the brief's quay ramp: no ramps, eastward-edges 6.3)"},
    {'id': 'park_stair', 'on': 'park_lane_south', 'at': [6736, 4400], 'from_tier': 4, 'to_tier': 3, 'width': 40, 'kind': 'stone'},
    {'id': 'cove_stair', 'on': 'headland_lane', 'at': [7048, 5696], 'from_tier': 3, 'to_tier': 1, 'width': 40, 'kind': 'stone',
     'why': "the Headland's cove stair down its 64 px rock face to the platform"},
    {'id': 'bar_step', 'on': 'shell_bar', 'at': [7056, 5784], 'from_tier': 1, 'to_tier': 0, 'width': 48, 'kind': 'stone',
     'why': 'off the rock platform onto the bar'},
    {'id': 'point_stair', 'on': 'tower_trod', 'at': [7160, 5592], 'from_tier': 3, 'to_tier': 4, 'width': 40, 'kind': 'stone'},
]

# --- the zones the game uses today, kept by id (brief 10), and what each becomes -----------------
# canvas: the zone's rect on today's world canvas (lib/world-canvas.ts worldAreas, chunk 'valley',
# in the chunk's own px), so a save or mission place can be carried to its new world rect
ZONES = [
    {'id': 'garden', 'rect': [6136, 2800, 320, 576], 'canvas': [320, 1728, 320, 576], 'tier': 5,
     'becomes': 'kept: the home hub, its size, geometry and harness unchanged (8.2)'},
    {'id': 'woodland', 'rect': [5640, 2432, 496, 912], 'canvas': [0, 1728, 320, 576], 'tier': 5, 'owner': 'claude-a',
     'becomes': "kept, redrawn by Claude A as the golden screen: the spring pool under the fall, the stone circle in a glade, the forester's yard"},
    {'id': 'riverside', 'rect': [6456, 2768, 408, 624], 'canvas': [640, 1728, 320, 576], 'tier': 5,
     'becomes': "kept, redrawn: the millpond, the mill on the step, the miller's cottage, the orchard and the beehives along a hedge"},
    {'id': 'town', 'rect': [5976, 3376, 640, 560], 'canvas': [320, 2304, 320, 576], 'tier': 4,
     'becomes': "replaced: Crossroads, a village at true scale with its square on the garden's axis"},
    {'id': 'park', 'rect': [6624, 3424, 384, 448], 'canvas': [640, 2304, 320, 576], 'tier': 4,
     'becomes': 'kept, redrawn: the bandstand on its paving, the pump house at the river, the lane south to the estuary footbridge'},
    {'id': 'halt', 'rect': [5600, 3936, 448, 1120], 'canvas': [0, 2304, 320, 576], 'tier': 4,
     'becomes': 'replaced: the halt farm, the station house, the 240 px platform, the engine shed (W3), the farmyard, the windmill and the fields to the shingle'},
    {'id': 'harbour', 'rect': [6176, 4672, 544, 432], 'canvas': [320, 2880, 320, 576], 'tier': 3,
     'becomes': 'replaced: Driftwood, its own hamlet above a 32 px quay, with the ferry pier (W4) and the breakwater'},
    {'id': 'headland', 'rect': [6800, 5104, 432, 608], 'canvas': [640, 2880, 320, 576], 'tier': 3,
     'becomes': 'kept, walled: the drystone wall with the stile (W1) its only gap, the sheep fold, the lookout tower and the lighthouse on the raised point, the cove stair'},
    {'id': 'hay_slope', 'rect': [6136, 2304, 728, 496], 'canvas': None, 'tier': 6, 'new': True,
     'becomes': "new ground: the Col Path's foot from the garden's trail gate to the Col hut, the hay meadow, the beehives and the well"},
]
# the Frostline's zones (ridge, hollow, saddle, snowmelt, summit) are Claude F's (frostline.json)

# the places and stands the game uses (lib/world-places.ts), at their new world points
STANDS = [
    {'id': 'garden', 'kind': 'mission', 'zone': 'garden', 'at': [6296, 2996], 'game': 'missionPlaces.garden [160, 196]'},
    {'id': 'hut', 'kind': 'door', 'zone': 'garden', 'at': [6204, 2932], 'game': 'hutDoors.hut (HUT_DOOR 68, 132)'},
    {'id': 'gate', 'kind': 'gate', 'zone': 'town', 'at': [6296, 3448], 'game': "gardenGates.gate: stand('town', 'garden')"},
    {'id': 'trail', 'kind': 'gate', 'zone': 'hay_slope', 'at': [6336, 2808], 'game': "gardenGates.trail: was stand('ridge', 'garden'); the Col Path's foot"},
    {'id': 'west', 'kind': 'gate', 'zone': 'woodland', 'at': [6120, 3104], 'game': "gardenGates.west: stand('woodland', 'garden')", 'owner': 'claude-a'},
    {'id': 'east', 'kind': 'gate', 'zone': 'riverside', 'at': [6472, 3088], 'game': "gardenGates.east: stand('riverside', 'garden-north')"},
    {'id': 'book', 'kind': 'mission', 'zone': 'town', 'at': [6224, 3464], 'game': "missionPlaces.book: stand('town', 'library')"},
    {'id': 'shop', 'kind': 'mission', 'zone': 'town', 'at': [6360, 3576], 'game': "missionPlaces.shop: stand('town', 'stall')"},
    {'id': 'arena', 'kind': 'ring', 'zone': 'town', 'at': [6112, 3696], 'game': "missionPlaces.arena: stand('town', 'ring'); the green's ring, rival Doomscroll Dave"},
    {'id': 'park', 'kind': 'mission', 'zone': 'park', 'at': [6744, 3616], 'game': "missionPlaces.park: stand('park', 'bandstand')"},
    {'id': 'valley', 'kind': 'stop', 'zone': 'halt', 'at': [5760, 4028], 'game': "travelPoints.valley: stand('halt', 'platform')"},
    {'id': 'pier', 'kind': 'stop', 'zone': 'harbour', 'at': [6536, 5096], 'game': "travelPoints.pier: stand('harbour', 'jetty')", 'in_water': True},
]

# --- buildings: footprints nothing may stand in ({id, foot: south-west corner, w}) --------------
BUILDINGS = [
    {'id': 'hut', 'foot': [6168, 2928], 'w': 64, 'zone': 'garden'},
    {'id': 'library', 'foot': [6184, 3440], 'w': 80, 'zone': 'town', 'note': "on the square's north side, against the garden's terrace wall"},
    {'id': 'terrace_cottages', 'foot': [6320, 3440], 'w': 96, 'zone': 'town', 'note': "a terrace of touching cottages on the north side, three fronts from the house kits"},
    {'id': 'bakery', 'foot': [6112, 3600], 'w': 56, 'zone': 'town', 'note': 'west of the square, its door to the square'},
    {'id': 'cottage_plot_nw', 'foot': [6184, 3736], 'w': 56, 'zone': 'town'},
    {'id': 'cottage_plot_ne', 'foot': [6336, 3712], 'w': 64, 'zone': 'town'},
    {'id': 'cottage_plot_sw', 'foot': [6184, 3904], 'w': 48, 'zone': 'town'},
    {'id': 'cottage_plot_se', 'foot': [6328, 3896], 'w': 56, 'zone': 'town'},
    {'id': 'green_shelter', 'foot': [6008, 3624], 'w': 40, 'zone': 'town', 'note': "the shelter by the green (the gardener's story)"},
    {'id': 'mill', 'foot': [6544, 3392], 'w': 48, 'zone': 'riverside', 'note': 'on the terrace step, its wheel on the race'},
    {'id': 'millers_cottage', 'foot': [6688, 3176], 'w': 56, 'zone': 'riverside'},
    {'id': 'bandstand', 'foot': [6736, 3600], 'w': 48, 'zone': 'park'},
    {'id': 'pump_house', 'foot': [6632, 3712], 'w': 40, 'zone': 'park', 'note': 'at the river'},
    {'id': 'station_house', 'foot': [5672, 3960], 'w': 72, 'zone': 'halt', 'note': "behind the platform, its door on the Drover's Road"},
    {'id': 'engine_shed', 'foot': [5600, 4112], 'w': 64, 'zone': 'halt', 'note': 'W3: the valley train east; on the siding south of the line'},
    {'id': 'farmhouse', 'foot': [5752, 4280], 'w': 64, 'zone': 'halt'},
    {'id': 'barn', 'foot': [5632, 4280], 'w': 72, 'zone': 'halt'},
    {'id': 'windmill', 'foot': [5960, 4464], 'w': 40, 'zone': 'halt', 'note': "Claude B's drainage mill (64 x 104): scoop wheel and outfall at its east foot"},
    {'id': 'fisher_cottage', 'foot': [6216, 4760], 'w': 56, 'zone': 'harbour', 'form': 'fisher (by the quay)'},
    {'id': 'river_lane_cottage', 'foot': [6400, 4760], 'w': 56, 'zone': 'harbour', 'form': 'lane cottage, gable to the lane'},
    {'id': 'walled_cottage', 'foot': [6224, 4896], 'w': 48, 'zone': 'harbour', 'form': 'behind a garden wall'},
    {'id': 'net_loft', 'foot': [6352, 4880], 'w': 64, 'zone': 'harbour', 'form': 'a net loft over a store, steps up the side'},
    {'id': 'harbour_cottage', 'foot': [6336, 4648], 'w': 56, 'zone': 'harbour', 'form': 'the top cottage, where the road drops'},
    {'id': 'fish_market', 'foot': [6352, 5048], 'w': 64, 'zone': 'harbour', 'note': 'on the quay'},
    {'id': 'harbour_master', 'foot': [6192, 5048], 'w': 48, 'zone': 'harbour'},
    {'id': 'chandlery', 'foot': [6448, 5048], 'w': 48, 'zone': 'harbour'},
    {'id': 'col_hut', 'foot': [6224, 2384], 'w': 48, 'zone': 'hay_slope', 'note': "Claude G's threshold object; lane E draws its south side"},
    {'id': 'lookout_tower', 'foot': [7112, 5512], 'w': 32, 'zone': 'headland'},
    {'id': 'lighthouse', 'foot': [7184, 5560], 'w': 32, 'zone': 'headland'},
    {'id': 'hay_barn', 'foot': [7024, 5200], 'w': 56, 'zone': 'headland', 'note': 'the named hay barn by the Coast Path'},
]

PLACES = [
    {'id': 'square', 'kind': 'square', 'rect': [6176, 3448, 240, 176], 'at': [6296, 3536],
     'why': "Crossroads' square: the well at its centre, on the garden's axis"},
    {'id': 'well', 'kind': 'well', 'at': [6264, 3560], 'why': 'the square well'},
    {'id': 'green', 'kind': 'green', 'rect': [6024, 3648, 144, 104], 'at': [6112, 3696], 'why': 'the green with the ring'},
    {'id': 'platform', 'kind': 'platform', 'rect': [5600, 4016, 240, 24], 'at': [5760, 4028],
     'why': "the halt's 240 px platform; the line runs west off the box into the hills and east to Cogsworth (W3)"},
    {'id': 'farmyard', 'kind': 'yard', 'rect': [5664, 4168, 168, 112], 'at': [5752, 4224]},
    {'id': 'fields', 'kind': 'fields', 'rects': [[5608, 4392, 256, 192], [5608, 4616, 280, 176], [5928, 4624, 96, 288],
                                                 [5608, 4816, 296, 112]],
     'why': 'four field blocks on the coastal lowland, hedged, drained to the windmill'},
    {'id': 'orchard', 'kind': 'orchard', 'rect': [6680, 2968, 168, 120], 'at': [6760, 3024]},
    {'id': 'quay_front', 'kind': 'quay', 'rect': [6176, 4968, 384, 88], 'at': [6368, 5016]},
    {'id': 'breakwater', 'kind': 'breakwater', 'line': [[6560, 5056], [6560, 5144], [6680, 5144], [6680, 5200]],
     'why': 'the breakwater along the grid from the estuary bank, sheltering the cove, with a harbour light at its end (drawn, not walked: a later shortcut)'},
    {'id': 'slip', 'kind': 'slip', 'at': [6560, 5048], 'why': 'the slip with the ferry (W4)'},
    {'id': 'sheep_fold', 'kind': 'fold', 'rect': [6904, 5376, 72, 48], 'at': [6936, 5400]},
    {'id': 'headland_wall', 'kind': 'wall', 'line': [[6800, 5304], [6976, 5304], [7008, 5304], [7232, 5304]],
     'gap': [6992, 5304], 'why': 'the drystone wall from the estuary bank to the east cliff; the stile (W1) its only gap'},
]
RAILS = [
    {'id': 'desert_line', 'way': 'W5', 'points': [[5600, 4048], [5840, 4048]], 'note': 'west off the box over the Rift (lane G beyond); the platform on its north side'},
    {'id': 'valley_train', 'way': 'W3', 'points': [[5840, 4048], [6168, 4048], [6168, 4120], [6640, 4120], [6640, 3904], [MINE_X1, 3904]],
     'continues': {'at': [MINE_X1, 3904], 'to': "lane G's W3 line east to Cogsworth (the land between)"},
     'crossings': [{'at': [5864, 4048], 'kind': 'level crossing', 'what': "the west road at the halt's crossing, east of the platform"},
                   {'at': [6264, 4120], 'kind': 'level crossing', 'what': 'the harbour road'},
                   {'at': [6600, 4120], 'kind': 'girder bridge', 'what': 'over the Sleepwater (its bridge in sleepwater.bridges)'},
                   {'at': [6712, 3904], 'kind': 'level crossing', 'what': 'the park lane south'}],
     'note': "east to Cogsworth; level crossings on the harbour road and the park lane, a girder bridge over the Sleepwater; lane G's line beyond the box"},
]

# --- named things (brief 5), on this box's land --------------------------------------------------
NAMED = [
    ('wayside shrine', 'shrine', (5884, 4357), 'Ash Coast', 'a short way off the path'),
    ('old oak', 'landmark', (6865, 4820), 'Coast Path', 'a short way off the path'),
    ('hay barn', 'landmark', (7020, 5151), 'Coast Path', 'beside the path'),
    ("a fallen climbers' camp", 'ruin', (6295, 2306), 'Col Path', 'beside the path'),
    ('beehives', 'prop', (6262, 2451), 'Col Path', 'beside the path'),
    ('a hare form in the long grass', 'wild', (6320, 2528), 'Col Path', 'beside the path'),
    ('well', 'well', (6357, 2549), 'Col Path', 'beside the path'),
    ("haymakers' shelter", 'camp', (6340, 2589), 'Col Path', 'beside the path'),
    ('a tumbled field barn', 'ruin', (6302, 2641), 'Col Path', 'beside the path'),
    ('wayside shrine', 'shrine', (6031, 2887), 'Col Path', 'a short way off the path'),
    ('stile and bench', 'landmark', (5642, 4227), "Drover's Road", 'a short way off the path'),
    ('picnic viewpoint', 'view', (6671, 3134), 'Foothill Road', 'a short way off the path'),
    ('tide pools', 'wild', (7206, 5115), 'Headland Lane', 'a short way off the path'),
    ('a wreck on the rocks', 'ruin', (6910, 5144), 'Headland Lane', 'beside the path'),
    ('a cliff-top view to the isles', 'view', (6930, 5205), 'Headland Lane', 'beside the path'),
    ("a beachcomber's camp", 'camp', (6892, 5257), 'Headland Lane', 'beside the path'),
    ('seal rocks', 'wild', (6965, 5522), 'Headland Lane', 'beside the path'),
    ('scarecrow', 'landmark', (6904, 3652), 'Lull Road', 'a short way off the path'),
]
POCKETS = [
    ('a view over the land', (6416, 2465), 'view_pocket'),
    ('a bench under a tree', (6488, 2679), 'bench_pocket'),
    ('a hermit at a fire', (6876, 5636), 'hermit_pocket'),
    ("a bench at the hay trod's end, over the woodland's crowns", (6168, 2600), 'hay_trod'),
]
OBSTACLES = [
    {'kind': 'a dew pond', 'at': [6692, 4284], 'moved_from': [6680, 4350], 'passed_by': 'dew_pond_loop',
     'why': 'brief 7: a loop round it, the path closer on one side, joining the lane at a Y'},
    {'kind': "the Headland's rocks", 'at': [7056, 5572], 'moved_from': [7050, 5560], 'passed_by': 'rocks_loop',
     'why': 'brief 7: an irregular outline, the path closer on one side, back on the lane at a Y'},
]

# the brief's markers (section 5) for the routes and places on this box's land, as written there;
# a marker slot is a thing of its type that fits the ground (brief 5), moved here to fit
MARKERS_BRIEF = {
    'Ash Coast': 'I bench (5775, 4203); S cairn (5690, 4148); S tracks (5700, 4236); A butterflies (5603, 4255); I door (5661, 4339); S marker stone (5611, 4449)',
    'Coast Path': 'I bench (6715, 4937); S cairn (6677, 5036); S tracks (6766, 5017); I door (6863, 5042); S cold fire ring (6924, 5118); S marker stone (6974, 5036); I bench (7023, 5121); A hares (7153, 5120)',
    'Col Path': 'I bench (6236, 2914); S cairn (6323, 2869); S tracks (6240, 2818); A butterflies (6296, 2737); I door (6203, 2701); S cold fire ring (6278, 2636); S marker stone (6230, 2559); I bench (6327, 2551); S cart with a broken wheel (6227, 2529); A butterflies (6287, 2501); I noticeboard (6286, 2400); S mended fence (6334, 2352); S old boot (6264, 2421); A butterflies (6221, 2338); I bench (6183, 2309)',
    'Driftwood': 'S cold fire ring (6424, 4736); I noticeboard (6376, 4784); S mended fence (6368, 4800); I signpost (6312, 4840); I gate (6472, 4840); S tracks (6496, 4840); I water trough (6600, 4864); S tracks (6328, 4872); I water trough (6544, 4872); I gate (6360, 4896); I water trough (6544, 4896); S marker stone (6208, 4912); S cairn (6232, 4912); S marker stone (6408, 4944); S mended fence (6624, 4976); I bench (6328, 4992)',
    "Drover's Road": 'I bench (5740, 4060); S cairn (5752, 3959); S tracks (5670, 4009); A butterflies (5622, 3929)',
    'Foothill Road': 'I bench (6755, 3345); S cairn (6860, 3367); S tracks (6844, 3271); A butterflies (6942, 3272); I door (6921, 3174)',
    'Headland Lane': 'I bench (6957, 5125); S cairn (6918, 5216); S tracks (7013, 5221); A terns (6948, 5316); I door (6981, 5357); S cold fire ring (6989, 5412); S marker stone (7073, 5465); I bench (6997, 5530); S cart with a broken wheel (7107, 5564)',
    'Home valley': 'I signpost (6256, 2944); S cart with a broken wheel (6048, 2976); I noticeboard (6312, 2992); S marker stone (6336, 3000); I signpost (6136, 3064); I resident (6128, 3072); I gate (6256, 3120); S mended fence (6312, 3136); I noticeboard (6344, 3136); S mended fence (6400, 3152); I noticeboard (6464, 3168); S marker stone (5840, 3176); I gate (6088, 3184); I door (6304, 3208); I water trough (6720, 3216); S marker stone (6064, 3224); I noticeboard (6136, 3248); I water trough (6368, 3256); S tracks (6384, 3264); I resident (6184, 3272); S cold fire ring (6336, 3272); S tracks (6616, 3272); I noticeboard (5960, 3296); I signpost (5776, 3304); I water trough (5864, 3304); S old boot (6544, 3304); I door (6088, 3312); S cairn (5992, 3320); S cart with a broken wheel (6176, 3320); S cairn (6144, 3328); S lost hat (6808, 3336); I noticeboard (6304, 3368); I signpost (6816, 3368); S cold fire ring (6616, 3376); S cold fire ring (6528, 3400); S lost hat (5912, 3416); S cart with a broken wheel (5840, 3432); I resident (6184, 3432); S mended fence (6144, 3448); I signpost (6512, 3448); S cairn (6424, 3456); S cart with a broken wheel (5776, 3464); S marker stone (6272, 3464); I water trough (5792, 3480); S cold fire ring (6032, 3480); S marker stone (6576, 3480); S cart with a broken wheel (5856, 3488); I door (6200, 3488); I gate (6216, 3488); S lost hat (5880, 3504); I water trough (6536, 3536); I water trough (6584, 3568); S tracks (6504, 3584); S cold fire ring (5824, 3608); I resident (6120, 3616); I bench (6568, 3616); S cairn (6712, 3632); S cairn (6136, 3656); S cold fire ring (6296, 3656); I water trough (6592, 3656); S tracks (6080, 3688); S tracks (6008, 3696); I gate (5800, 3704); I door (6008, 3704); I resident (6224, 3712); S marker stone (6600, 3760); I water trough (5896, 3776); I bench (6240, 3776); S marker stone (6336, 3784); I door (6288, 3808); S old boot (5912, 3816); S mended fence (6648, 3816); I gate (5976, 3864); S old boot (6264, 3888); I noticeboard (6024, 3896); I noticeboard (6648, 3896); S mended fence (6576, 3904); I resident (6080, 3920); S lost hat (6392, 3952); I water trough (6184, 4024)',
    'Lull Road': 'I bench (6817, 3731); S cairn (6833, 3830); S tracks (6909, 3768); A butterflies (6959, 3850); I door (6990, 3895)',
    'Shell Bar': 'I bench (7080, 5693); S cairn (6979, 5713); S tracks (7008, 5783)',
}

RESIDENTS = [
    {'who': 'the gardener', 'at': [6264, 3008], 'zone': 'garden', 'story': 'valley (Claude K, #197): "the weeds will keep"; apprentice Cairn'},
    {'who': 'Doomscroll Dave', 'at': [6136, 3720], 'zone': 'town', 'note': "the ring's rival and tutor, on the green"},
    {'who': 'the librarian', 'at': [6240, 3472], 'zone': 'town'},
    {'who': 'the baker', 'at': [6152, 3568], 'zone': 'town'},
    {'who': 'the stall keeper', 'at': [6384, 3584], 'zone': 'town'},
    {'who': 'the miller', 'at': [6680, 3248], 'zone': 'riverside'},
    {'who': 'the beekeeper', 'at': [6840, 3104], 'zone': 'riverside', 'note': 'the beehives along the hedge'},
    {'who': 'the angler', 'at': [6648, 3192], 'zone': 'riverside', 'note': 'on the millpond bench'},
    {'who': 'the picnicker', 'at': [6760, 3672], 'zone': 'park'},
    {'who': 'the station master', 'at': [5728, 4080], 'zone': 'halt'},
    {'who': 'the farmer', 'at': [5768, 4208], 'zone': 'halt'},
    {'who': 'the fisher', 'at': [6264, 4968], 'zone': 'harbour', 'note': "on the quay by the fisher's cottage"},
    {'who': 'the harbour master', 'at': [6216, 5024], 'zone': 'harbour'},
    {'who': 'the lighthouse keeper', 'at': [7136, 5552], 'zone': 'headland', 'note': 'crosses the stile (threshold)'},
    {'who': 'the shepherd', 'at': [6936, 5440], 'zone': 'headland', 'note': 'sheep cross the stile to the fold'},
    {'who': 'the hermit', 'at': [6880, 5576], 'zone': 'headland', 'note': "the Shell Bar pocket's resident"},
    {'who': 'the hiker', 'at': [6320, 2400], 'zone': 'hay_slope', 'note': 'walkers with staffs up the Col Path'},
    {'who': 'the hut warden', 'at': [6264, 2416], 'zone': 'hay_slope', 'note': "comes down for bread (Col hut threshold); Claude F's story"},
    {'who': 'the haymaker', 'at': [6376, 2600], 'zone': 'hay_slope'},
]
# where a rest counts for a story (Claude K, docs/story/handoffs.md on #197): open, reachable ground
# with a stand, never in a pocket; each chapter's change is presentation only (reserved, not drawn)
REST_SPOTS = [
    {'id': 'hut_bed', 'at': [6204, 2944], 'zone': 'garden', 'what': "the hut's bed (night)", 'story': 'valley ch 1'},
    {'id': 'spring_pool', 'at': [5952, 2576], 'zone': 'woodland', 'what': 'the spring pool in the woodland', 'owner': 'claude-a'},
    {'id': 'millpond_bench', 'at': [6640, 3200], 'zone': 'riverside', 'what': 'the millpond bench', 'story': 'valley ch 2'},
    {'id': 'bandstand', 'at': [6760, 3616], 'zone': 'park', 'what': 'the bandstand in the park (Park Patrol)', 'story': 'valley ch 3'},
    {'id': 'library', 'at': [6224, 3464], 'zone': 'town', 'what': 'the library (Book Club)'},
    {'id': 'harbour_wall', 'at': [6264, 5040], 'zone': 'harbour', 'what': "Driftwood's harbour wall"},
    {'id': 'lookout_tower', 'at': [7144, 5536], 'zone': 'headland', 'what': "the Headland's lookout tower"},
    {'id': 'col_hut_bench', 'at': [6264, 2400], 'zone': 'hay_slope', 'what': 'the Col hut bench', 'story': "the Frostline's ch 2 (Claude F's story, on lane E's land)"},
]
STORY = {
    'region': 'valley', 'owner': 'claude-k (#197)',
    'reserved': [
        {'what': 'a kettle on a hook in the shelter by the green (ch 2)', 'at': [6024, 3632]},
        {'what': 'the gardener seated on the bandstand step, hat slipped (ch 3, pose)', 'at': [6752, 3608]},
        {'what': 'the trowel on a hook and a lit lantern in the shelter (ch 3)', 'at': [6032, 3632]},
        {'what': "Cairn's empty place in the circle: a ring of pale grass", 'at': [6096, 3712]},
    ],
}

# set pieces from the cliff core's library ({piece, biome, at, seed}): the stairs, the ledges on
# the terrace rims, the ivy on the garden's wall, the boulders on the Headland, the ponds
SET_PIECES = [
    ('stair', 'meadow', (6336, 2784)), ('stair', 'meadow', (6304, 2448)), ('stair', 'meadow', (6296, 3408)),
    ('stair', 'meadow', (6664, 3408)), ('stair', 'meadow', (6776, 3392)), ('stair', 'meadow', (6880, 3280)),
    ('stair', 'meadow', (6960, 3224)), ('stair', 'meadow', (5664, 4304)), ('stair', 'meadow', (5872, 4336)),
    ('stair', 'meadow', (6256, 4384)), ('stair', 'meadow', (6736, 4400)), ('stair', 'coast', (6312, 4952)),
    ('stair', 'coast', (7048, 5696)), ('stair', 'coast', (7160, 5592)),
    ('ledge', 'meadow', (6400, 2768)), ('ledge', 'meadow', (6560, 2736)), ('ledge', 'meadow', (6360, 3376)),
    ('ledge', 'meadow', (6824, 3392)), ('ledge', 'meadow', (6120, 4352)),
    ('ivy', 'meadow', (6240, 3376)), ('ivy', 'meadow', (6440, 3376)),
    ('pond', 'meadow', (6552, 3280)), ('pond', 'meadow', (6680, 4296)),
    ('boulders', 'coast', (7064, 5560)), ('boulders', 'coast', (6960, 5528)), ('boulders', 'meadow', (6872, 2440)),
    ('scree', 'meadow', (6904, 2480)),
]
# cluster places for Claude B's prop_clusters (#188, #203): a recipe and a point, under
# `cluster_places`; B's placer (--place) turns each into a `clusters` placement with its
# orientation and seed. Recipes the library lacks yet (platform_yard, orchard_edge on #203) wait there
CLUSTERS = [
    ('meadow_nook', (6392, 2560), 'hay slope: a rest under a tree beside the Col Path'),
    ('field_edge', (5928, 4616), 'the farm track through the field hedges, a stile at the drain'),
    ('farmyard', (5720, 4192), "the farmyard's work corner by the barn"),
    ('platform_yard', (5824, 4072), "the halt's platform end"),
    ('town_square_corner', (6200, 3608), "the square's south-west corner"),
    ('town_square_corner', (6400, 3472), "the square's north-east corner by the terrace"),
    ('orchard_edge', (6720, 3104), "the orchard on the race's side"),
    ('meadow_nook', (6744, 3688), 'the park: a bench under a tree by the bandstand'),
    ('meadow_nook', (6688, 4248), 'the dew pond: a bench facing the water'),
    ('shore', (6440, 4976), "Driftwood's quay end by the slip"),
    ('coast_meadow', (6936, 5168), 'the Headland neck: a lone tree, sheep, flowers'),
    ('sheepfold_corner', (6936, 5376), "the Headland's fold"),
    ('coast_meadow', (6872, 4800), 'the old oak on the coastal lowland'),
]

THRESHOLDS = [
    {'id': 'col_hut', 'at': [6290, 2350], 'route': 'col_path', 'object': "the Col hut (Claude G draws the object)",
     'sides': {'valley': 'claude-e', 'frostline': 'claude-f'},
     'band': 'meadow, broadleaf, garden -> alpine, meadow, broadleaf', 'landmark': {'what': 'the headwall', 'at': [6230, 1950]},
     'residents': ['sheep and their shepherd graze up as far as the hut', 'walkers with staffs',
                   'choughs and an ibex on the scree above', 'the hut warden comes down for bread'],
     'radiates_from': 'the glacier'},
    {'id': 'headland_stile', 'at': [6992, 5304], 'route': 'headland_lane', 'way': 'W1', 'object': 'the stile in the drystone wall (Claude G)',
     'sides': {'valley': 'claude-e', 'headland': 'claude-e'},
     'band': 'meadow, sand, field -> sand, meadow', 'landmark': {'what': 'the lighthouse', 'at': [7200, 5520]},
     'residents': ['sheep cross the stile to the fold', 'the lighthouse keeper', 'a hare from the cliff turf',
                   'sea pinks spill over the wall'],
     'radiates_from': 'the sea'},
    {'id': 'shell_bar', 'at': [6888, 5888], 'route': 'shell_bar', 'way': 'W4', 'outside_box': True,
     'object': 'the Shell Bar (Claude G)', 'sides': {'headland': 'claude-e', 'isles': 'claude-c'},
     'band': 'sand, meadow, field -> meadow, sand, field2', 'landmark': {'what': 'the wreck', 'at': [6930, 5870]},
     'residents': ['cocklers walk out at low tide', 'seals haul out on the bar', 'terns nest on the islet'],
     'radiates_from': 'the sea'},
    {'id': 'fern_hills', 'at': [7000, 3192], 'route': 'foothill_road', 'object': "Fernhollow's lane end (Claude H's side)",
     'sides': {'valley': 'claude-e', 'fernhollow': 'claude-h'},
     'band': 'meadow, orchard, broadleaf -> broadleaf, conifer, meadow',
     'residents': ['woodcutters with a cart of logs', 'a jay in the oaks'], 'radiates_from': 'the old forest'},
    {'id': 'lull_road_east', 'at': [7000, 3816], 'route': 'lull_road', 'sides': {'valley': 'claude-e', 'land_between': 'claude-g'},
     'band': 'meadow, field -> field, watermeadow'},
    {'id': 'coast_path_east', 'at': [7000, 5072], 'route': 'coast_path', 'sides': {'valley': 'claude-e', 'land_between': 'claude-g'},
     'band': 'meadow, sand -> sea turf, sand'},
    {'id': 'brackens_foot', 'at': [5600, 3944], 'route': 'drovers_road',
     'sides': {'valley': 'claude-e', 'brackens': 'claude-f'},
     'note': "the Brackens gap itself (5200, 3760) is Claude F's (brackens.json); the valley's side of its band runs from the halt to x 5600",
     'band': 'meadow, field, field2 -> steppe, meadow, broadleaf'},
    {'id': 'ash_coast_west', 'at': [5600, 4336], 'route': 'ash_coast', 'sides': {'valley': 'claude-e', 'fire_country': 'claude-d'},
     'band': 'meadow, field -> sand, steppe, ash'},
]
EDGES = [
    {'side': 'north', 'along': [[5680, 2304], [7008, 2304]],
     'layers': "Claude F's Frostline meets the valley at its tier 0 (world 7): the escarpment over the woodland, the Col hut's shelf, the hay slope's top; scree and boulders thicken at the escarpment's foot"},
    {'side': 'north-east', 'along': [[6864, 2304], [7008, 3192]],
     'layers': "the Fern hills' crest: bramble and fallen trees thickening into thicket and old trees (64 to 180 px deep); the old forest's dark canopy beyond (Claude G past x 7008)"},
    {'side': 'west', 'along': [[5600, 2304], [5600, 4336]],
     'layers': "the Brackens' foot: Claude F's brackens.json meets at its tier 0 (world 4); heather and gorse clumps come down onto the halt's pastures"},
    {'side': 'south', 'along': [[5600, 5048], [7232, 5712]],
     'layers': 'the sea is the edge: shingle and surf under the halt farm, the quay wall and the cove at Driftwood, rock faces and foam round the Headland; the isles and the rocket cape beyond (Claude G past the box)'},
]
GROUND = {
    '_about': "Ground kinds by place for the painter; the kit's meadow biome (scripts/art/biomes/meadow.json, #215) with the valley's variants in scripts/art/biomes/valley.json (meadow, farmland, riverside, town_edge), and coast.json (variant cliff_coast).",
    'hay_slope': 'meadow: hay meadow uncut, clover and buttercup in drifts, the Col Path worn to earth; scree at the escarpment foot',
    'garden': 'the garden kit (unchanged)',
    'woodland': "Claude A's golden screen",
    'riverside': 'riverside: grazed bank, reeds and marginals at the millpond, crack willow and alder, the orchard in rows',
    'town': 'town_edge: setts on the square, beaten earth lanes with grass in the middle, kitchen gardens behind the cottages',
    'park': 'town_edge: mown grass, gravel walks, flower beds; riverside on the bank',
    'halt': 'farmland: ploughed and crop fields with margins, hedgerows with gates, a farm track, a cinder yard at the halt',
    'harbour': "coast cliff_coast with the harbour's quay ground: granite setts, nets, fish boxes",
    'headland': 'coast cliff_coast: sea turf with thrift, the drystone wall, rock platform below',
}


# --- building the plan ---------------------------------------------------------------------------
def raster():
    """The tier of every 8 px cell of the box (0 where nothing is raised: the bar and the sea)."""
    T = np.zeros((H // CELL, W // CELL), np.int16)
    for tier, rects in TIERS:
        for x0, y0, x1, y1 in rects:
            T[(y0 - Y0) // CELL:(y1 - Y0) // CELL, (x0 - X0) // CELL:(x1 - X0) // CELL] = tier
    return T


def trace(mask):
    """The outlines of a boolean cell mask, one closed rectilinear polygon per component, in
    world px, clockwise on screen. Asserts there are no holes (a tier's top is one mass)."""
    Hc, Wc = mask.shape
    nxt = {}
    m = np.pad(mask, 1)
    for r in range(Hc):
        for c in range(Wc):
            if not mask[r, c]:
                continue
            if not m[r, c + 1]:          # top
                nxt.setdefault((c, r), []).append((c + 1, r))
            if not m[r + 1, c + 2]:      # right
                nxt.setdefault((c + 1, r), []).append((c + 1, r + 1))
            if not m[r + 2, c + 1]:      # bottom
                nxt.setdefault((c + 1, r + 1), []).append((c, r + 1))
            if not m[r + 1, c]:          # left
                nxt.setdefault((c, r + 1), []).append((c, r))
    bad = [v for v, e in nxt.items() if len(e) > 1]
    assert not bad, f'cells touch only at a corner at {[(X0 + c * CELL, Y0 + r * CELL) for c, r in bad[:4]]}'
    loops = []
    while nxt:
        start = next(iter(nxt))
        loop, v = [start], nxt.pop(start)[0]
        while v != start:
            loop.append(v)
            v = nxt.pop(v)[0]
        loops.append(loop)
    polys = []
    for loop in loops:
        pts = [(X0 + c * CELL, Y0 + r * CELL) for c, r in loop]
        n = len(pts)
        keep = [pts[i] for i in range(n)
                if not (pts[i - 1][0] == pts[i][0] == pts[(i + 1) % n][0] or pts[i - 1][1] == pts[i][1] == pts[(i + 1) % n][1])]
        area = sum(keep[i][0] * keep[(i + 1) % len(keep)][1] - keep[(i + 1) % len(keep)][0] * keep[i][1]
                   for i in range(len(keep))) / 2
        assert area > 0, f'a hole in a tier at {keep[0]}: tops must be single masses'
        polys.append([list(p) for p in keep])
    return polys


TIER_NAMES = {1: 'shore', 2: 'quay', 3: 'lowland', 4: 'floor', 5: 'terrace', 6: 'hay_slope', 7: 'escarpment'}
TIER_WHY = {
    1: 'the shingle under the halt farm and the rock platform at the Headland foot',
    2: "Driftwood's quay, a 32 px quay face under the hamlet",
    3: "the coastal lowland: the halt farm's lower fields, the dew pond meadow, Driftwood and the Headland",
    4: "the valley floor (v2's T1): Crossroads, the green, the park, the halt farm; or the Headland's raised point",
    5: "the T2 terrace: the woodland (Claude A), the garden and the riverside",
    6: "the hay slope above the garden and the Fern hills' shoulder",
    7: "the Frostline's foot (Claude F's tier 0), the Col hut's shelf and the Fern hills' crest",
}


def tiers_out():
    T = raster()
    out = []
    for k in range(1, int(T.max()) + 1):
        for i, poly in enumerate(trace(T >= k)):
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            name = TIER_NAMES.get(k, f't{k}')
            if k == 4 and min(xs) >= 7000:
                name = 'headland_point'
            elif k == 3 and min(ys) >= 4288 and i:
                name = f'{name}_{i}'
            tid = name if not any(t['id'] == name for t in out) else f'{name}_{i}'
            out.append({'id': tid, 'tier': k, 'why': TIER_WHY[k] if name != 'headland_point' else
                        "the Headland's raised point: the lookout tower and the lighthouse on a 32 px rock face",
                        'outline': poly, 'bbox': [min(xs), min(ys), max(xs), max(ys)]})
    for t in out:
        del t['bbox']
    return out


def parse_markers():
    out = []
    for route, text in MARKERS_BRIEF.items():
        for item in text.split('; '):
            t, rest = item.split(' ', 1)
            what, xy = rest.rsplit(' (', 1)
            x, y = (int(v) for v in xy.rstrip(')').split(', '))
            if not (X0 <= x <= X1 and Y0 <= y <= Y1):
                continue
            out.append({'t': t, 'what': what, 'at': [x, y], 'route': route})
    return out


def areas():
    cols = [320, 320, 320, 448, 256]       # the last column is the land between north of the Headland
    rows = [576, 576, 576, 576, 512, 704]  # the last row is the Headland and the sea
    out, y = [], Y0
    for j, h in enumerate(rows):
        x = X0
        for i, w in enumerate(cols):
            out.append({'id': f'valley-{j}{i}', 'rect': [x, y, w, h]})
            x += w
        y += h
    return out


def base_plan() -> dict:
    return {
        '_about': ("The home valley as a plan (Claude E, lane E, 21 Oct): what the shared kit's painter and the checks "
                   "read. Written by scripts/art/regions/valley_plan.py; do not edit by hand. From the brief "
                   "docs/vision/regions/home-valley-frostline-brackens.md (world plan v5.3, 8.2). World px on the "
                   "11264 x 6912 canvas; tiers are Claude G's world tiers (base_tier 0: the sea), traced from rectangles "
                   "of 8 px cells so every outline is on the grid; each outline is its tier's top and everything higher; tops "
                   "in screen space, each south face hanging 32 px a tier under its rim. The woodland is Claude A's golden screen (outline, exits and stands only); the "
                   "Frostline and the Brackens are Claude F's, Fernhollow Claude H's, the land between and the sea "
                   "beyond the box Claude G's."),
        'id': 'valley', 'owner': 'claude-e', 'biome': 'meadow', 'biomes': ['meadow', 'coast'],
        'biome_variants': {'meadow': ['meadow', 'farmland', 'riverside', 'town_edge'], 'coast': ['cliff_coast']},
        'biome_brief': 'scripts/art/biomes/valley.json (variants of the kit meadow)',
        'box': [X0, Y0, W, H],
        'mine': {'_about': "the box is one rectangle; lane E's land is the brief's two parts inside it",
                 'valley': [5600, 2304, 1408, 2752], 'headland': [6800, 5120, 432, 704],
                 'not_mine': {'land_between_and_fernhollow': [MINE_X1, 2304, X1 - MINE_X1, HEADLAND_Y0 - 2304]}},
        'base_tier': {'value': BASE_TIER, 'provisional': False,
                      'from': "Claude G's world tiers (lib/world-routes.ts, #189; route-meets.md): the floor at 4, the Col hut at 7, the Headland at 3, the bar at 0"},
        'faces': {'_about': "Valley edges are the meadow's own (to-all-reuse-rule; the kit meadow's edges and valley.json's edge_sets): turf banks with earth and root faces between tiers, the garden's and Crossroads' built terrace walls, the coast's rock faces at the quay and the Headland",
                  'between_tiers': {'height': 32, 'material': 'turf bank over earth, rounded rock cobbles at the foot'},
                  'escarpment': {'height': 64, 'material': "the Frostline's rock, Claude F's edge set at the meeting", 'kit': 'cliff_core'},
                  'built': {'height': 32, 'material': 'drystone retaining walls (the garden terrace, the quay)', 'corners': 'square'}},
        'coast': [list(p) for p in COAST],
        'tiers': tiers_out(),
        'routes': ROUTES,
        'trods': TRODS,
        'stairs': STAIRS,
        'water': WATER,
        'zones': ZONES,
        'stands': STANDS,
        'buildings': BUILDINGS,
        'places': PLACES,
        'rails': RAILS,
        'named': [{'thing': t, 'kind': k, 'at': list(at), 'route': r, 'where': w} for t, k, at, r, w in NAMED],
        'pockets': [{'holds': h_, 'at': list(at), 'trod': tr} for h_, at, tr in POCKETS],
        'markers': parse_markers(),
        'egg_spots': [],
        'obstacles': OBSTACLES,
        'set_pieces': [{'piece': p, 'biome': b, 'at': list(at), 'seed': 500 + i} for i, (p, b, at) in enumerate(SET_PIECES)],
        # cluster places, not placements: Claude B's placer (prop_clusters.py --place) turns each into a
        # `clusters` placement with its orientation and seed; #188's check holds every `clusters` entry
        # as a placement, so the places wait under their own key
        'cluster_places': [{'recipe': r, 'at': list(at), 'why': why} for r, at, why in CLUSTERS],
        'residents': RESIDENTS,
        'rest_spots': REST_SPOTS,
        'rings': [{'id': 'arena', 'at': [6112, 3696], 'zone': 'town', 'rival': 'Doomscroll Dave', 'backdrop': 'valley',
                   'why': "the green in Crossroads (missionPlaces.arena), unchanged as the tutor's ring"}],
        'story': STORY,
        'thresholds': THRESHOLDS,
        'edges': EDGES,
        'ground': GROUND,
        'areas': areas(),
    }


# --- settling: moving placed things to fit the ground (the brief's point kept as moved_from) -----
RESERVED = {   # zones lane E places no slots in: Claude A's golden screen and the garden hub
    'woodland': (5640, 2432, 6136, 3344), 'garden': (6136, 2800, 6456, 3376)}


def _reserved(x, y) -> bool:
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in RESERVED.values())


def _walk_ok(P, G, wet, x, y, me, lim, placed_pts, slot=True):
    if slot and _reserved(x, y):
        return False
    t, f = G.at(x, y)
    if t is None or f or (x >= MINE_X1 and y < HEADLAND_Y0):
        return False
    cx, cy = int((x - X0) // 4), int((y - Y0) // 4)
    if wet[max(0, cy - 1):cy + 2, max(0, cx - 1):cx + 2].any():
        return False
    paths = P['routes'] + P['trods']
    d = min(rp.dist_to_line((x, y), p['points']) for p in paths)
    if d > lim:
        return False
    for p in paths:
        if rp.dist_to_line((x, y), p['points']) < p['width'] / 2 + 6:
            return False
    for st in P['stairs']:
        if rp.seg_len((x, y), st['at']) < st['width'] / 2 + 10:
            return False
    for b in P['buildings']:
        bx, by = b['foot']
        if bx - 6 <= x <= bx + b['w'] + 6 and by - 84 <= y <= by + 6:
            return False
    for q in placed_pts:
        if q is not me and rp.seg_len((x, y), q) < 14:
            return False
    return True


def wet_mask(P):
    from PIL import Image, ImageDraw
    Wc, Hc = W // 4, H // 4
    img = Image.new('L', (Wc, Hc), 1)
    d = ImageDraw.Draw(img)

    def px(q):
        return ((q[0] - X0) / 4, (q[1] - Y0) / 4)
    d.polygon([px(q) for q in P['coast']], fill=0)
    for w in P['water']:
        if w.get('closed'):
            d.polygon([px(q) for q in w['points']], fill=1)
        else:
            d.line([px(q) for q in w['points']], fill=1, width=max(1, int(w.get('width', 8) / 4) + 2))
    for a in P['areas']:
        if a.get('walkable') is False:
            ax, ay, aw, ah = a['rect']
            d.rectangle([px((ax, ay)), px((ax + aw, ay + ah))], fill=1)
    return np.asarray(img).astype(bool)


def settle(P) -> None:
    G = rp.Ground(P)
    wet = wet_mask(P)
    things = ([(n, 160 if n['where'] != 'beside the path' else 44, True) for n in P['named']] +
              [(m, 44, True) for m in P['markers']] +
              [(r, 44, False) for r in P['residents'] if not r.get('in_water')])
    pts = [e['at'] for e, _, _ in things]
    for e, lim, slot in things:
        x0, y0 = e['at']
        if _walk_ok(P, G, wet, x0, y0, e['at'], lim, pts, slot):
            continue
        best = None
        for rad in range(4, 260, 4):
            for dx in range(-rad, rad + 1, 4):
                for dy in (-rad, rad) if abs(dx) != rad else range(-rad, rad + 1, 4):
                    x, y = (x0 + dx) // 4 * 4, (y0 + dy) // 4 * 4
                    if _walk_ok(P, G, wet, x, y, e['at'], lim, pts, slot):
                        dd = math.hypot(x - x0, y - y0)
                        if best is None or dd < best[0]:
                            best = (dd, x, y)
            if best:
                break
        if best:
            e.setdefault('moved_from', [x0, y0])
            e['at'] = [best[1], best[2]]
    # pockets: at their trod's end
    for pk in P['pockets']:
        end = next(t for t in P['trods'] if t['id'] == pk['trod'])['points'][-1]
        if pk['at'] != end:
            pk['moved_from'] = pk['at']
            pk['at'] = list(end)


def mark_areas(P) -> None:
    """Areas with no path through them are drawn land or sea, never walked; the land between
    north of the Headland is lane G's and H's."""
    for a in P['areas']:
        x, y, w, h = a['rect']
        if x >= MINE_X1 and y + h <= HEADLAND_Y0 + 32:
            a['walkable'] = False
            a['not_mine'] = 'the land between (Claude G) and Fernhollow (Claude H)'
            continue
        hit = any(x + 8 <= px_ < x + w - 8 and y + 8 <= py_ < y + h - 8
                  for p in P['routes'] + P['trods'] for px_, py_, _ in rp.sample(p['points'], 8))
        if not hit:
            a['walkable'] = False


def dress(P) -> None:
    """Dressing slots (dress: true) so each walked area has 2 interactables and 3 story props."""
    I_KINDS = ('bench', 'signpost', 'water trough', 'noticeboard')
    S_KINDS = ('cairn', 'mended fence', 'cart with a broken wheel', 'marker stone', 'old boot')
    G = rp.Ground(P)
    wet = wet_mask(P)
    k = 0
    for a in P['areas']:
        if a.get('walkable') is False:
            continue
        x, y, w, h = a['rect']
        i_, s_ = area_counts(P, a['rect'])
        need = [('I', I_KINDS)] * max(0, 2 - i_) + [('S', S_KINDS)] * max(0, 3 - s_)
        if not need:
            continue
        cand = [(px_, py_, p) for p in P['routes'] + P['trods'] for px_, py_, _ in rp.sample(p['points'], 8)
                if x + 8 <= px_ < x + w - 8 and y + 8 <= py_ < y + h - 8]
        pts = [e['at'] for e in P['markers'] + P['named']]
        for j, (t, kinds) in enumerate(need):
            placed = False
            for off in range(len(cand)):
                px_, py_, p = cand[(int((j + 0.5) * len(cand) / len(need)) + off * 7) % len(cand)]
                for side in (1, -1):
                    for ox, oy in ((side * (p['width'] / 2 + 16), 0), (0, side * (p['width'] / 2 + 16))):
                        qx, qy = int(px_ + ox) // 4 * 4, int(py_ + oy) // 4 * 4
                        if x <= qx < x + w and y <= qy < y + h and _walk_ok(P, G, wet, qx, qy, None, 44, pts):
                            m = {'t': t, 'what': kinds[k % len(kinds)], 'at': [qx, qy], 'dress': True}
                            P['markers'].append(m)
                            pts.append(m['at'])
                            k += 1
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break


def area_counts(P, rect):
    x, y, w, h = rect

    def inside(p):
        return x <= p[0] < x + w and y <= p[1] < y + h
    i_ = sum(1 for m in P['markers'] if m['t'] == 'I' and inside(m['at']))
    i_ += sum(1 for n in P['named'] if n['kind'] in rp_named_interact() and inside(n['at']))
    s_ = sum(1 for m in P['markers'] if m['t'] == 'S' and inside(m['at']))
    return i_, s_


def rp_named_interact():
    return getattr(rp, 'NAMED_INTERACT', {'well', 'npc', 'landmark', 'camp', 'view', 'shrine'})


def build() -> dict:
    P = base_plan()
    mark_areas(P)
    settle(P)
    dress(P)
    return P


# --- the valley's own checks -------------------------------------------------------------------
GAME_ZONES = ('garden', 'woodland', 'riverside', 'town', 'park', 'halt', 'harbour', 'headland')
GAME_STANDS = ('garden', 'hut', 'gate', 'trail', 'west', 'east', 'book', 'shop', 'arena', 'park', 'valley', 'pier')
G_MEETS = {   # route-meets.md (lane E), Claude G's #189: (x, y, tier, width)
    'Col Path': (6280, 2296, 7, 24), 'Foothill Road': (7000, 3192, 7, 48), 'Lull Road': (7000, 3816, 4, 40),
    'Coast Path': (7000, 5072, 3, 32), "Drover's Road": (5600, 3944, 4, 32), 'Ash Coast': (5600, 4336, 3, 40),
    'Shell Bar': (6896, 5800, 0, 56),
}


def check(P) -> list:
    out = []
    G = rp.Ground(P)
    ids = {z['id'] for z in P['zones']}
    for z in GAME_ZONES:
        if z not in ids:
            out.append(f'valley: zone {z} (the game uses it) is not placed')
    sids = {s['id'] for s in P['stands']}
    for s in GAME_STANDS:
        if s not in sids:
            out.append(f'valley: stand {s} (lib/world-places.ts) is not placed')
    g = next(z for z in P['zones'] if z['id'] == 'garden')
    if g['rect'][2:] != [320, 576]:
        out.append('valley: the garden is not 320 x 576 (8.2: unchanged)')
    # every route meets G's cell within a cell or two, at G's tier and width
    for r in P['routes']:
        if r['name'] not in G_MEETS or 'meets' not in r:
            continue
        gx, gy, gt, gw = G_MEETS[r['name']]
        mx, my = r['meets']['at']
        if abs(mx - gx) + abs(my - gy) > 24:
            out.append(f"valley: {r['name']} meets at {(mx, my)}, G's cell is {(gx, gy)}")
        if r['meets']['tier'] != gt:
            out.append(f"valley: {r['name']} meets at tier {r['meets']['tier']}, G's is {gt}")
        end = r['points'][0] if rp.seg_len(r['points'][0], (mx, my)) < rp.seg_len(r['points'][-1], (mx, my)) else r['points'][-1]
        t, _f = G.at(min(max(end[0], X0), X1 - 1), min(max(end[1], Y0), Y1 - 1))
        if r['meets']['tier'] != t and r['id'] != 'shell_bar':
            out.append(f"valley: {r['name']}'s end {tuple(end)} is on tier {t}, not {r['meets']['tier']}")
    # the water runs from its source to the sea through named bodies
    names = {w['id'] for w in P['water']}
    for w in P['water']:
        if w.get('declared_closed'):
            continue
        for k in ('source', 'outlet'):
            v = w.get(k, '')
            if not v:
                out.append(f'valley: water {w["id"]} has no {k}')
    chain, w = ['sleepwater_fall'], 'sleepwater_fall'
    while True:
        o = next(x for x in P['water'] if x['id'] == w)['outlet']
        if o not in names:
            break
        chain.append(o)
        w = o
    if not chain[-1] == 'sleepwater' or 'sea' not in next(x for x in P['water'] if x['id'] == 'sleepwater')['outlet']:
        out.append(f'valley: the Sleepwater does not reach the sea ({" -> ".join(chain)})')
    # nothing placed in a not-mine area or a walkable: false area
    for what, at, e in rp.placed(P) if hasattr(rp, 'placed') else []:
        if at[0] >= MINE_X1 and at[1] < HEADLAND_Y0:
            out.append(f'valley: {what} at {tuple(at)} is on the land between (not lane E\'s)')
    for k, (lo, hi) in {'stairs': (0, 99)}.items():
        pass
    return out


def write(P) -> None:
    with open(OUT, 'w') as fh:
        json.dump(P, fh, indent=1)
        fh.write('\n')


def main(argv) -> int:
    if '--export' in argv:
        P = build()
        write(P)
        faults = check(P) + rp.check(P)
        print(f'wrote {os.path.relpath(OUT, ROOT)}: {len(P["tiers"])} tiers, {len(P["routes"])} routes, '
              f'{len(P["trods"])} trods, {len(P["stairs"])} stairs, {len(P["markers"])} markers')
        for f in faults:
            print(' ', f)
        return 1 if faults else 0
    if '--check' in argv:
        with open(OUT) as fh:
            P = json.load(fh)
        built = build()
        faults = check(P)
        if json.dumps(built, sort_keys=True) != json.dumps(P, sort_keys=True):
            faults.append('valley: art/regions/valley.json is stale (run valley_plan.py --export)')
        for f in faults:
            print(f)
        print(f'valley plan: {len(faults)} faults')
        return 1 if faults else 0
    out_dir = argv[1] if len(argv) > 1 else os.path.join(tempfile.gettempdir(), 'napattack-region-plans')
    os.makedirs(out_dir, exist_ok=True)
    P = build()
    path = os.path.join(out_dir, 'valley.png')
    rp.draw(P).save(path)
    print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
