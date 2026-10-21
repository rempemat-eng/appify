"""Cogsworth, the coal hills, the Narrows and Fernhollow: the region's plan as data.

Lane H (Claude H, taken over from Claude C on 21 Oct; Matt 10:03 and 10:11: build the world
faster with every agent, accurately, on the established rules). The brief is
docs/vision/regions/cogsworth-coal-hills-narrows.md (world plan v5.3, PR #96); this module
turns it into data the region's painter and checks read, so the drawing follows one plan:

- the region (world px on the 11264 x 6912 continent): its footprint, its places with their
  boxes, the named things, secret pockets, markers, obstacles, edges and thresholds of the
  brief, the Narrows gorge and its viaduct, the spoil heaps;
- the town (Cogsworth, 704 x 960, decided) laid out in its own box px: ground kinds and
  tiers as polygons on the 8 px grid, the water (the Cog, the Millrace, the canal and its
  lock, the basin), the streets, stairs and ramps between tiers, bridges, buildings with
  their fronts and doors, the landmarks, the stands (today's ids kept, so missions, rings,
  stops and saves carry over), the areas and the gates where the routes meet the town.

`rasterize()` turns the town into 4 px walk cells: a ground-kind map, the walk, and the tier
map in the audit's code (digits for tiers, `f` a face, `b` a side band, `s` a stair or ramp;
world_audit.py `tier_checks`). Faces are carved south of every higher top at the height the
tiers differ by (12, 16, 32 or 40 px). `check()` holds the plan to the rules a plan can
show (on the grid, inside its box, faces on south edges only and of a legal height, every
tier change a stair or ramp at least 34 px wide, every stand and door reached from the
platform, nothing more than 30 % farther from the platform than the brief's walk times (nearer is no fault: the decided town is denser than the block-out's), the benchmark's density per settlement screen, the brief's counts) and exits non-zero
on a fault. Nothing in the game reads this yet; the painter (next step) does.

    python3 scripts/art/regions/cogsworth_plan.py --check
    python3 scripts/art/regions/cogsworth_plan.py [OUT_DIR]     # block-out pictures + check

Moves from the brief (its coordinates are "to within a cell or two" of a coarser block-out;
"move a thing to fit the ground, not the ground to fit the number"): see MOVED.
"""
from __future__ import annotations

import heapq
import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

GRID = 8      # the soft grid
CELL = 4      # walk cells
FACE = 32     # one tier (verticality.md); the canal sits half a tier (16) down

# --- the region ---------------------------------------------------------------------------
FOOTPRINT = (7000, 1700, 2300, 1600)      # x, y, w, h in world px (brief 1)

TOWN_W, TOWN_H = 704, 960                  # decided (world plan 8.3)
TOWN_ORIGIN = (7624, 1968)                 # centred on the brief's (7980, 2450), on the grid
FERNHOLLOW = {'id': 'fernhollow', 'box': (7000, 2960, 320, 240),   # centre (7160, 3080)
              'why': "timber in the wet woods of the Fern hills' western slope, on the Foothill Road"}

PLACES = [
    {'id': 'cogsworth', 'kind': 'town', 'box': (*TOWN_ORIGIN, TOWN_W, TOWN_H),
     'why': 'coal and iron in the coal hills, the fast Cog for power (the Millrace), the valley floor for a railway out'},
    {'id': 'fernhollow', 'kind': 'hamlet', 'box': FERNHOLLOW['box'], 'why': FERNHOLLOW['why']},
    {'id': 'narrows', 'kind': 'gorge', 'box': (8520, 2160, 640, 920),
     'why': "the Lull's gorge through the coal hills, white with rapids; the Cog joins at its foot"},
    {'id': 'narrows-viaduct', 'kind': 'bridge', 'at': (9032, 2328),
     'why': "the gorge's narrowest point, where the railway (now the maglev) crossed to the east bank; rail only"},
]

# The Narrows: the Lull's course through the gorge, upstream (north-east) to the foot, where
# the Cog comes in (world px). 44 px of white water between walls; the viaduct at the narrows.
GORGE = {'centre': [(9128, 2168), (9064, 2272), (9032, 2328), (9008, 2440), (8984, 2576),
                    (8960, 2752), (8888, 2896), (8760, 2992), (8616, 3048), (8536, 3064)],
         'water_w': 44, 'rim_tiers': (3, 18), 'viaduct': (9032, 2328),
         'note': 'walls in the cliff core\'s highland set (#165), tiers from the geography chunk (P1) when it lands'}
COG_FOOT = (8528, 3064)
MAGLEV = [(8328, 2648), (8520, 2600), (8760, 2480), (8936, 2360), (9032, 2328), (9160, 2304)]  # terminus to the viaduct, on piers

# Spoil heaps (brief 2): the middles of cogsworth_region's spoil pieces (MOVED).
SPOIL = [(7560, 2264), (8184, 1932), (8424, 3124), (7556, 2132), (8404, 2292)]

# Named things (brief 5): id, kind, at (world px: the middle of its set piece in
# cogsworth_region.SET_PIECES, laid beside G's routes), route, where, the sprite or kit piece
NAMED = [
    ('burners-camp', 'camp', (7496, 2824), 'Foothill Road', 'beside the path', 'charcoal_clamp + burners_hut (B, #163)'),
    ('collapsed-adit', 'cave', (7416, 2892), 'Foothill Road', 'a short way off the path', 'cliff core face piece'),
    ('pit-head', 'landmark', (7280, 2964), 'Foothill Road', 'beside the path', 'pit_head (B, #163)'),
    ('windmill', 'landmark', (7168, 3256), 'Foothill Road', 'beside the path', 'windmill (B, #172)'),
    ('loops-view', 'view', (7360, 3104), 'Foothill Road', 'beside the path', 'a terrace edge with a bench'),
    ('eel-camp', 'camp', (7108, 3256), 'Foothill Road', 'beside the path', 'to draw (B queue)'),
    ('tor', 'landmark', (7272, 1788), 'High Fells', 'beside the path', 'cliff core set piece'),
    ('climbers-camp', 'camp', (7340, 1896), 'High Fells', 'a short way off the path', 'to draw (B queue)'),
    ('echo-cave', 'cave', (7596, 1852), 'High Fells', 'beside the path', 'cliff core face piece'),
    ('cairn', 'landmark', (7996, 1924), 'High Fells', 'a short way off the path', 'cairn (B, REWORK)'),
    ('crow-roost', 'wild', (7864, 1912), 'High Fells', 'beside the path', 'a dead pine (forest kit) with crows'),
    ('rail-ruin', 'ruin', (8480, 2736), 'Towpath', 'a short way off the path', 'to draw (B queue)'),
    ('tram-tipple', 'landmark', (8368, 2788), 'Towpath', 'beside the path', 'tram_tipple (B, #163)'),
    ('narrows-lookout', 'view', (8552, 2976), 'Towpath', 'beside the path', 'narrows_lookout (B, #163)'),
]

POCKETS = [   # holds, clearing at (world px), off the route
    ('a story detail: a buried bell', (7632, 1792), 'High Fells'),
    ('a view down a gorge', (7176, 1968), 'High Fells'),
    ('a resident fishing', (7712, 3080), 'Foothill Road'),
    ('a story detail: a buried bell', (7208, 2784), 'Foothill Road'),
    ('a view down a gorge', (8016, 2904), 'Towpath'),
]
RESERVED = [('hermits-tarn', (7048, 1720))]

OBSTACLES = [   # what, at (world px), route, how it is passed
    ('thicket', (7120, 3280), 'Foothill Road', 'side path at a Y 300 px before, round the far side'),
    ('thicket', (7408, 1968), 'High Fells', 'side path at a Y 300 px before, round the far side'),
    ('spoil heap', (8184, 1936), 'loop', 'a loop round it on the bench above the town, closer on its south side'),
]

THRESHOLDS = [
    {'id': 'millrace-cutting', 'at': (7648, 2744), 'route': 'Foothill Road', 'sides': ('G', 'H'),
     'band': ('broadleaf, garden, meadow', 'garden, meadow, broadleaf'), 'landmark': "Cogsworth's chimneys",
     'residents': ['miners up to the pits', 'a coal cart down', 'woodcutters with a timber wagon', 'crows over the cut']},
    {'id': 'cog-foot', 'at': COG_FOOT, 'route': 'Towpath', 'sides': ('H', 'H'),
     'band': ('broadleaf, garden, meadow', 'meadow, watermeadow, broadleaf'), 'landmark': 'the Narrows gorge',
     'residents': ['a barge horse and its bargee', 'coal barges going down', 'a heron at the confluence', 'anglers walking up']},
]

EDGES = [
    ('north', 'scree and boulders thickening into crags', 'the massif and the upper Lull gorge going on north'),
    ('east', 'bramble and fallen trees thickening into thicket and old trees', 'the old forest, then the moss fens'),
    ('interior', 'thicket and felled timber in the coal forest', 'dark conifers and spoil heaps, hazier'),
]

# Markers along the routes and in Fernhollow, as the brief places them (world px). Each is a
# slot: the named thing or another of its type that fits the ground. The town's slots are
# laid out with the town below (TOWN_SLOTS), so the brief's 18 Cogsworth markers are kept as
# slots of the same kinds there.
MARKERS = {
    'fernhollow': [('I', 'noticeboard', (7184, 2912)), ('S', 'marker stone', (7168, 2920)), ('S', 'cart with a broken wheel', (7216, 2944)),
                   ('I', 'signpost', (7208, 2976)), ('S', 'marker stone', (7224, 3000)), ('I', 'door', (7232, 3000)),
                   ('S', 'cairn', (7304, 3032)), ('I', 'gate', (7184, 3040)), ('S', 'mended fence', (7248, 3048)),
                   ('S', 'tracks', (7304, 3048)), ('I', 'water trough', (7240, 3072)), ('I', 'gate', (7200, 3088)),
                   ('S', 'marker stone', (7224, 3088)), ('I', 'water trough', (7288, 3112)), ('S', 'marker stone', (7200, 3168)),
                   ('I', 'gate', (7032, 3176))],
    'Foothill Road': [('S', 'cold fire ring', (7005, 3203)), ('S', 'marker stone', (7052, 3139)), ('I', 'bench', (7107, 3206)),
                      ('S', 'cart with a broken wheel', (7162, 3122)), ('A', 'hares', (7242, 3173)), ('I', 'noticeboard', (7230, 3072)),
                      ('S', 'mended fence', (7326, 3086)), ('S', 'old boot', (7321, 2988)), ('A', 'moths', (7409, 3031)),
                      ('I', 'bench', (7437, 2937)), ('S', 'lost hat', (7525, 2982)), ('S', 'cart with a broken wheel', (7503, 2890)),
                      ('I', 'noticeboard', (7598, 2872)), ('S', 'tracks', (7551, 2793)), ('A', 'moths', (7631, 2770)),
                      ('I', 'gate', (7616, 2672)), ('S', 'cold fire ring', (7713, 2702)), ('S', 'marker stone', (7702, 2587)),
                      ('A', 'moths', (7816, 2651)), ('I', 'noticeboard', (7776, 2541)), ('S', 'cairn', (7817, 2487)),
                      ('S', 'tracks', (7881, 2445))],
    'High Fells': [('S', 'lost hat', (7125, 1710)), ('I', 'noticeboard', (7238, 1771)), ('A', 'choughs', (7344, 1788)),
                   ('I', 'gate', (7429, 1744)), ('S', 'cold fire ring', (7412, 1843)), ('S', 'marker stone', (7457, 1877)),
                   ('A', 'choughs', (7533, 1889)), ('I', 'noticeboard', (7579, 1898)), ('S', 'cairn', (7599, 1972)),
                   ('S', 'tracks', (7664, 1985)), ('I', 'gate', (7668, 2059)), ('S', 'old boot', (7685, 2094)),
                   ('A', 'choughs', (7772, 2133)), ('I', 'resident', (7778, 2187)), ('S', 'lost hat', (7792, 2234)),
                   ('S', 'cart with a broken wheel', (7829, 2248)), ('A', 'moths', (7818, 2379)), ('I', 'gate', (7918, 2328))],
    'Towpath': [('I', 'bench', (8080, 2585)), ('S', 'cairn', (8162, 2616)), ('S', 'tracks', (8145, 2656)), ('A', 'moths', (8196, 2686)),
                ('I', 'door', (8246, 2722)), ('S', 'cold fire ring', (8196, 2825)), ('S', 'marker stone', (8234, 2867)),
                ('I', 'bench', (8237, 2928)), ('S', 'cart with a broken wheel', (8352, 2923)), ('A', 'moths', (8363, 3020)),
                ('I', 'noticeboard', (8433, 2952)), ('S', 'mended fence', (8504, 2962)), ('S', 'old boot', (8585, 3032)),
                ('A', 'moths', (8481, 3082)), ('I', 'bench', (8528, 3164)), ('S', 'lost hat', (8432, 3189)),
                ('S', 'cart with a broken wheel', (8501, 3261))],
}
BRIEF_TOWN_MARKERS = 18   # the brief's Cogsworth slots, re-laid in TOWN_SLOTS

# Where things moved from the brief, and why.
MOVED = [
    ('Cogsworth platform stop', (7960, 2420), 'the platform on the town\'s north edge (box y 104 to 136)',
     'the plan puts the platform on the north edge (8.3) and the terminus 30 s away; the brief\'s point is the block-out town\'s centre'),
    ('named things', 'the brief\'s points', 'NAMED (the middles of cogsworth_region.SET_PIECES)',
     'the brief\'s points came from the block-out\'s routes and its smaller town; each now stands beside or a short way off '
     'Claude G\'s line for its route (#175), off the road, out of the water and out of the town: the crow roost, the cairn '
     'and the echo cave up on the bench and its face where the High Fells come down, the burners\' camp and the collapsed '
     'adit beside the Foothill Road on the Fern hills\' shoulder, the rail ruin and the tram tipple on the coal hills\' '
     'foot by the Towpath, the lookout above the Cog foot'),
    ('spoil heaps', 'the brief\'s five', 'SPOIL (the middles of cogsworth_region\'s spoil pieces)',
     'three stood in the decided town or the Cog; all five now stand on the hills round it, one above the town with the loop'),
    ('route markers inside the town box', '20 of the High Fells, Foothill Road and Towpath markers', 'the town\'s slots (TOWN_SLOTS)',
     'the block-out\'s routes ran on into a smaller town; inside the decided town they are town slots of the same kinds'),
    ('the routes\' ends', 'High Fells (7920, 2390), Foothill Road (7900, 2480), Towpath (8040, 2560)', 'the town\'s gates (TOWN_GATES)',
     'the routes end at the town\'s edge, where Claude G\'s routes meet it (agreed on the board)'),
]


# --- the town, in its box px ----------------------------------------------------------------
# Tiers (the audit's digits): 0 the Cog, 1 the Millrace and the canal (16 px above the Cog... 16
# below the street), 2 the street level, 3 the coal-hill bench and Gasworks Hill (one tier up).
TIER_PX = {0: -32, 1: -16, 2: 0, 3: 32}


def jog(points, step=72, depth=8, seed=0, closed=True):
    """Break every edge longer than 96 px with a jog of `depth` px every `step` px or so, on
    the grid, where a wall buttresses or a wharf has its bays (a choice of the drawing since
    Matt's 11:44 grid ruling, no longer a rule). Deterministic. Axis-aligned edges only."""
    out = []
    n = len(points)
    for i in range(n if closed else n - 1):
        (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
        out.append((x0, y0))
        L = abs(x1 - x0) + abs(y1 - y0)
        if L <= 96 or (x0 != x1 and y0 != y1):
            continue
        k = max(2, round(L / step))
        seg = L / k
        horiz = y0 == y1
        sgn = 1 if (x1 > x0 or y1 > y0) else -1
        for j in range(1, k):
            t = int(round(j * seg / GRID)) * GRID
            d = depth if (j + seed) % 2 else -depth
            if horiz:
                x = x0 + sgn * t
                yy = y0 if j % 2 else y0 + d
                prev = out[-1]
                out += [(x, prev[1]), (x, yy)]
            else:
                y = y0 + sgn * t
                xx = x0 if j % 2 else x0 + d
                prev = out[-1]
                out += [(prev[0], y), (xx, y)]
        last = out[-1]
        if horiz and last[1] != y0:
            out.append((x1 - sgn * GRID * 2, last[1]))
            out.append((x1 - sgn * GRID * 2, y0))
        if not horiz and last[0] != x0:
            out.append((last[0], y1 - sgn * GRID * 2))
            out.append((x0, y1 - sgn * GRID * 2))
    return out


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# Ground, drawn in order (later over earlier): (id, kind, tier, polygon, walkable). Kinds are
# the painter's: which kit draws it. A higher tier's polygon is its top; its face is carved
# south of it by rasterize().
GROUND = [
    # the Cog, down the west side and east along the south (river_kit `river`, fast and dark)
    ('cog-bed', 'cog', 0, rect(0, 0, 704, 960), False),   # under everything: no cell is left without ground
    ('cog', 'cog', 0, [(0, 0), (72, 0), (80, 64), (72, 136), (80, 216), (72, 304), (80, 392), (72, 480),
                       (80, 568), (72, 656), (80, 744), (88, 808), (104, 872), (152, 912), (232, 904),
                       (320, 912), (408, 904), (496, 912), (584, 904), (672, 912), (704, 904), (704, 960), (0, 960)], False),
    # the town's bench, on the Cog's east bank
    ('street-level', 'cinder', 2, [(80, 0), (704, 0), (704, 904), (672, 912), (584, 904), (496, 912), (408, 904),
                                   (320, 912), (232, 904), (152, 912), (104, 872), (88, 808), (80, 744), (72, 656),
                                   (80, 568), (72, 480), (80, 392), (72, 304), (80, 216), (72, 136), (80, 64)], True),
    # the coal-hill bench above the rails, joining Gasworks Hill (one tier up); conifers, heath
    ('bench', 'heath', 3, [(96, 0), (704, 0), (704, 496), (688, 496), (688, 488), (632, 488), (632, 496),
                           (576, 496), (576, 488), (560, 488), (560, 424), (568, 424), (568, 360), (560, 360),
                           (560, 296), (544, 296), (544, 288),
                           (504, 288), (504, 296), (472, 296), (472, 224), (480, 224), (480, 136), (560, 136), (560, 40),
                           (480, 40), (480, 32), (400, 32), (400, 40), (312, 40), (312, 32), (240, 32),
                           (240, 40), (152, 40), (152, 32), (104, 32)], True),
    # Gasworks Hill: the gasworks' yard and lanes on the hill top
    ('gasworks-yard', 'yard', 3, jog(rect(568, 152, 696, 480), seed=1), True),
    ('hill-lane', 'setts', 3, jog(rect(480, 152, 568, 288), seed=2), True),
    # the railway: ballast and rails from the west over the Cog to the buffers at the hill
    ('rails', 'rails', 2, rect(80, 72, 560, 104), False),
    ('platform', 'platform', 2, rect(176, 104, 560, 136), True),
    # the station square under the clock tower (village square 240 x 176, setts)
    ('square', 'setts', 2, jog(rect(232, 200, 472, 376), seed=3), True),
    ('square-east', 'setts', 2, rect(472, 296, 560, 376), True),
    # Workshop Street and Main Street (48 px), the wharf street along the canal's north bank
    ('workshop-street', 'setts', 2, rect(184, 136, 232, 496), True),
    ('main-street', 'setts', 2, rect(336, 376, 384, 856), True),
    ('wharf', 'flags', 2, jog(rect(120, 496, 704, 544), seed=4), True),
    # the Millrace: a leat off the Cog through the mills and back (river_kit `race`)
    ('millrace', 'race', 1, [(80, 136), (112, 136), (120, 200), (112, 296), (120, 392), (112, 456), (96, 488), (80, 488)], False),
    # the canal, half a tier down across the middle, its lock at the Cog, the basin east
    ('canal', 'canal', 1, jog(rect(168, 544, 568, 600), seed=5, depth=8), False),
    ('basin', 'canal', 1, [(568, 544), (648, 544), (656, 560), (648, 616), (568, 616)], False),
    ('lock', 'lock', 0, rect(80, 544, 168, 600), False),
    # the south bank: the towpath, the Foothill lane in from the Millrace bridge, the riverside
    ('towpath', 'towpath', 2, jog(rect(96, 600, 704, 624), seed=6), True),
    ('foothill-lane', 'setts', 2, jog(rect(80, 752, 336, 784), seed=7), True),
    ('riverside', 'quay', 2, [*jog([(96, 840), (704, 840)], seed=11, closed=False), (704, 840), (704, 904), (672, 912), (584, 904), (496, 912), (408, 904),
                                  (320, 912), (232, 904), (152, 912), (104, 872)], True),
    ('foundry-yard', 'yard', 2, jog(rect(112, 632, 304, 752), seed=8), True),
    ('allotments', 'allotment', 2, jog(rect(112, 792, 328, 840), seed=9), True),
    ('terminus-forecourt', 'setts', 2, jog(rect(392, 752, 704, 800), seed=10), True),
    ('pump-yard', 'yard', 2, rect(392, 800, 480, 840), True),
]

# Buildings: (id, env, kind, picture rect (x0, top, x1, foot) in box px, front side, doors as
# (x, y) at the foot). The camera looks north, so every front faces south and stands on its
# foot line; the rect is the picture's screen box (roof and wall above the foot), so what
# stands north of a building is behind it. Fronts from house_kits.py (#121) in Cogsworth's
# brick and iron; the station, mills, foundry, works and terminus are wider fronts built
# from the same kit's pieces (cogsworth_town.py).
BUILDINGS = [
    ('station', 'cogsworth', 'station', (440, 100, 560, 200), 's', [(472, 200), (528, 200)]),
    ('engine-shed', 'cogsworth', 'shed', (96, 68, 168, 136), 's', [(132, 136)]),
    ('mill-1', 'cogsworth', 'mill', (120, 152, 184, 264), 's', [(152, 264)]),
    ('mill-2', 'cogsworth', 'mill', (120, 288, 184, 400), 's', [(152, 400)]),
    ('workshop-row-1', 'cogsworth', 'workshops', (232, 388, 336, 488), 's', [(256, 488), (308, 488)]),
    ('workshop-row-2', 'cogsworth', 'workshops', (384, 376, 472, 488), 's', [(452, 488)]),
    ('warehouse', 'cogsworth', 'warehouse', (472, 388, 560, 488), 's', [(516, 488)]),
    ('gasholder', 'cogsworth', 'gasholder', (584, 232, 696, 344), None, []),
    ('retort-house', 'cogsworth', 'works', (576, 392, 688, 472), 's', [(612, 472)]),
    ('foundry', 'cogsworth', 'foundry', (112, 640, 256, 752), 's', [(160, 752), (216, 752)]),
    ('row-south', 'cogsworth', 'workshops', (384, 640, 464, 752), 's', [(424, 752)]),
    ('terminus', 'cogsworth', 'terminus', (480, 652, 688, 752), 's', [(544, 752), (624, 752)]),
    ('pump-house', 'cogsworth', 'pump', (400, 760, 472, 840), 's', [(436, 840)]),
    ('allotment-shed', 'cogsworth', 'hut', (288, 772, 320, 840), None, []),
]

# Landmarks and set pieces that are props (B's lane draws them; the brief and #172 name them).
LANDMARKS = [
    ('clock-tower', 'clock_tower', (344, 232, 368, 272), 'the square\'s landmark, seen from the platform and up Main Street'),
    ('airship-mast', 'airship_mast', (600, 64, 640, 152), 'on the hill (the airship leaves the square); a stair up its tower'),
    ('ring', 'ring_floor', (248, 296, 328, 360), 'the sparring ring on an earth floor in the square\'s west part'),
    ('canal-crane', 'canal_crane', (448, 520, 472, 544), 'a crane on the wharf, its jib over the water'),
    ('humpback-bridge', 'bridge', (336, 536, 384, 608), 'Main Street over the canal, a humpback in brick'),
    ('swing-bridge', 'bridge', (512, 536, 544, 608), 'a swing footbridge to the basin\'s wharf'),
    ('lock-gates', 'lock_gates', (80, 552, 168, 600), 'mitre gates, balance beams, the step in the water level'),
    ('millrace-bridge', 'bridge', (0, 752, 80, 784), 'the Foothill Road over the Cog (W3, the Millrace landslip, is Claude G\'s object)'),
    ('rail-bridge', 'bridge', (0, 72, 80, 104), 'the railway over the Cog; rail only'),
    ('level-crossing', 'crossing', (184, 72, 224, 104), 'the High Fells path over the rails to the platform'),
    ('buffers', 'buffers', (552, 72, 560, 104), 'the line ends at the hill'),
    ('waterwheels', 'mill_wheel', (104, 168, 120, 432), 'three wheels in the Millrace (B: the Millrace wheel)'),
    ('maglev-viaduct', 'maglev_pier', (688, 664, 704, 696), 'the maglev leaves the terminus east on piers, over the riverside'),
]

# Railings and walls that stop a walker on one tier (rects): the platform's edge over the
# station square, with the way down beside the station.
RAILINGS = [
    ('platform-railing', (232, 136, 424, 140)),
]

# Stairs and ramps between tiers: (id, kind, rect across the face band (x0, y0, x1, y1),
# lower tier, upper tier). Stairs at least 34 px open (we use 40), top flush with the
# upper floor, bottom on the path. No ramps: changes of level are stairs (eastward-edges.md 6.3).
STAIRS = [
    ('fells-stair', 'stair', (184, 40, 224, 72), 2, 3),     # the High Fells down to the crossing
    ('hill-stair', 'stair', (504, 288, 544, 320), 2, 3),    # the square up Gasworks Hill
    ('hill-steps', 'stair', (624, 488, 664, 520), 2, 3),    # up from the wharf (no ramps: eastward-edges.md 6.3)
    ('wharf-steps', 'stair', (216, 536, 256, 568), 1, 2),   # water steps down to the canal (to the boats; not walked)
]

# Bridges: walkable decks over water at the given tier (rect).
BRIDGES = [
    ('humpback-bridge', (336, 536, 384, 608), 2),
    ('swing-bridge', (512, 536, 544, 608), 2),
    ('millrace-bridge', (0, 752, 80, 784), 2),
    ('mill-bridges', (80, 136, 120, 160), 2),       # Workshop Street's head over the leat
    ('lock-bridge', (168, 544, 184, 600), 2),       # over the upper gate (a footway on the gate)
]

# Gates where routes meet the town: (route, box px on the edge, which edge). Claude G posts
# the exact cells; these are the town's side of them.
TOWN_GATES = [
    ('High Fells', (200, 0), 'n'),
    ('Foothill Road', (0, 768), 'w'),
    ('Towpath', (704, 872), 'e'),
]

# Stands (today's ids kept; lib/world-places.ts, lib/world-ways.ts, resident routes).
STANDS = {
    # today's junction zone
    'junction:platform': (352, 120), 'junction:tower': (352, 300), 'junction:ring': (288, 328),
    'junction:workshop': (208, 320), 'junction:canal': (360, 512),
    # today's canal zone
    'canal:junction': (360, 392), 'canal:bridge': (360, 572), 'canal:boat': (264, 528),
    'canal:lock': (184, 528), 'canal:foundry': (200, 768), 'canal:terminus': (584, 776),
    'canal:allotments': (216, 816),
    # the plan's new ground (world-ways plannedZones: hill, terminus)
    'hill:gasholder': (600, 368), 'hill:mast': (620, 168), 'terminus:pump-house': (436, 848),
}

# Areas (the names, the map, saves, the ways): today's zone ids plus the planned hill and
# terminus (lib/world-ways.ts plannedZones), on the world audit's 32 px cells.
AREAS = [
    {'id': 'junction', 'kind': 'zone', 'rect': (0, 0, 480, 512)},
    {'id': 'hill', 'kind': 'zone', 'rect': (480, 0, 224, 512)},
    {'id': 'canal', 'kind': 'zone', 'rect': (0, 512, 384, 448)},
    {'id': 'terminus', 'kind': 'zone', 'rect': (384, 512, 320, 448)},
]

# The town's interactable (I) and story (S) slots (benchmark 1: 6 to 10 of each a settlement
# screen; the town is about 3.7 screens, so 23 to 37 of each). Doors count as I. The kits'
# own dressing (barrels, crates, lamps on fronts) comes on top and is not counted.
TOWN_SLOTS = [
    # the platform and the station
    ('I', 'departure board', (400, 128)), ('I', 'bench', (240, 128)), ('S', 'luggage on a trolley', (480, 128)),
    ('S', 'a sand-caked goods wagon (W5)', (520, 88)), ('S', 'coal in the engine shed', (128, 160)),
    ('I', 'water crane', (200, 128)), ('S', 'tracks', (300, 96)),
    # the square
    ('I', 'noticeboard', (448, 216)), ('I', 'bench', (264, 216)), ('I', 'water trough', (440, 352)),
    ('S', 'a lost hat', (312, 368)), ('S', 'pigeons on the clock\'s plinth', (384, 264)), ('I', 'tea kiosk', (424, 312)),
    ('S', 'a cart of gears', (536, 352)), ('I', 'signpost', (512, 336)),
    # Workshop Street and the mills
    ('S', 'a sack hoist at the mill door', (192, 224)), ('S', 'grain spilled by the mill', (200, 288)),
    ('I', 'a tinker\'s bench', (216, 432)), ('S', 'an old boot', (200, 472)), ('S', 'a mended fence on the leat', (96, 360)),
    # the hill
    ('I', 'the mast\'s stair', (620, 160)), ('S', 'coke heaps', (640, 440)), ('S', 'gas pipes and a valve wheel', (576, 232)),
    ('I', 'a lookout bench over the town', (528, 232)), ('S', 'a cairn on the bench', (440, 16)), ('S', 'tracks of a coke cart', (600, 480)),
    # the wharf, canal and lock
    ('I', 'lock beam', (128, 544)), ('S', 'a moored narrowboat', (256, 576)), ('S', 'coal on the wharf', (488, 528)),
    ('I', 'bollard and rope', (304, 544)), ('S', 'a fisherman\'s stool', (432, 616)), ('I', 'bench', (560, 528)),
    # the south half
    ('S', 'castings stacked in the yard', (272, 664)), ('I', 'water trough', (304, 744)), ('S', 'a cart with a broken wheel', (96, 776)),
    ('I', 'gate to the allotments', (240, 788)), ('S', 'a scarecrow', (152, 816)), ('S', 'a mended fence', (320, 792)),
    ('I', 'noticeboard', (488, 760)), ('I', 'ticket gate', (584, 760)), ('S', 'tracks', (640, 792)),
    ('I', 'bench on the riverside', (512, 856)), ('S', 'eel traps on the bank', (256, 872)), ('S', 'a cold stove by the pump house', (488, 816)),
]


LANDMARK_IDS = {'station', 'clock-tower', 'gasholder', 'airship-mast', 'foundry', 'terminus', 'lock-gates', 'humpback-bridge'}


def placements() -> list:
    """The town's buildings and set pieces as placement data in world px (Claude A, a-to-h-
    chunks: buildings are baked into the chunk's ground, and this list is what the audit reads
    for density and landmarks): kind, box (x0, y0, x1, y1), foot (x, y) and whether it is a
    landmark."""
    ox, oy = TOWN_ORIGIN
    out = []
    for bid, env, kind, (x0, top, x1, foot), side, doors in BUILDINGS:
        out.append({'id': bid, 'kind': kind, 'box': [x0 + ox, top + oy, x1 + ox, foot + oy],
                    'foot': [(x0 + x1) // 2 + ox, foot + oy], 'doors': [[dx + ox, dy + oy] for dx, dy in doors],
                    'landmark': bid in LANDMARK_IDS})
    for lid, sprite, (x0, y0, x1, y1), why in LANDMARKS:
        out.append({'id': lid, 'kind': sprite, 'box': [x0 + ox, y0 + oy, x1 + ox, y1 + oy],
                    'foot': [(x0 + x1) // 2 + ox, y1 + oy], 'landmark': lid in LANDMARK_IDS, 'why': why})
    return out


# --- rasterizing ----------------------------------------------------------------------------
KIND_IDS = {}


def _kid(kind):
    return KIND_IDS.setdefault(kind, len(KIND_IDS) + 1)


def _poly_mask(poly, w, h, cell=CELL):
    """Cells whose centre lies inside the polygon (drawn at 1 px, sampled at the centres, so
    PIL's inclusive edges never shift a boundary that sits on the grid)."""
    img = Image.new('L', (w, h), 0)
    ImageDraw.Draw(img).polygon(poly, fill=1)
    return np.array(img, bool)[cell // 2::cell, cell // 2::cell]


def _rect_mask(r, w, h, cell=CELL):
    m = np.zeros((h // cell, w // cell), bool)
    x0, y0, x1, y1 = r
    m[y0 // cell:y1 // cell, x0 // cell:x1 // cell] = True
    return m


def rasterize():
    """The town in 4 px cells: kind (int, KIND_IDS), tier (int), walk (bool), the tier map
    in the audit's code (str rows) and the face, band and stair masks."""
    W, H = TOWN_W // CELL, TOWN_H // CELL
    kind = np.zeros((H, W), int)
    tier = np.full((H, W), -1, int)
    walk = np.zeros((H, W), bool)
    for gid, k, t, poly, wk in GROUND:
        m = _poly_mask(poly, TOWN_W, TOWN_H)
        kind[m], tier[m], walk[m] = _kid(k), t, wk
    # buildings block
    bmask = np.zeros_like(walk)
    for bid, env, k, r, front, doors in BUILDINGS:
        m = _rect_mask(r, TOWN_W, TOWN_H)
        kind[m] = _kid('building')
        walk[m] = False
        bmask |= m
    for rid, r in RAILINGS:
        walk[_rect_mask(r, TOWN_W, TOWN_H)] = False
    # bridges: walkable decks
    for bid, r, t in BRIDGES:
        m = _rect_mask(r, TOWN_W, TOWN_H)
        kind[m], tier[m], walk[m] = _kid('bridge'), t, True
    # faces: south of every higher top, as tall as the step, carved from what lies below
    face = np.zeros_like(walk)
    band = np.zeros_like(walk)
    t0 = tier.copy()
    bridge = np.isin(kind, [_kid('bridge')])
    for y in range(H - 1):
        for x in range(W):
            a, b = t0[y, x], t0[y + 1, x]
            if a > b >= 0 and not bridge[y + 1, x]:   # a bridge's south side shows its arch face
                hpx = TIER_PX[a] - TIER_PX[b]
                n = hpx // CELL
                for yy in range(y + 1, min(H, y + 1 + n)):
                    if t0[yy, x] >= a or bridge[yy, x]:
                        break
                    face[yy, x] = True
    # side bands: where tiers meet west or east (5 px: one cell on the higher side)
    for y in range(H):
        for x in range(W - 1):
            a, b = t0[y, x], t0[y, x + 1]
            if a != b and a >= 0 and b >= 0 and not face[y, x] and not face[y, x + 1]:
                hi = x if a > b else x + 1
                if not bridge[y, hi]:
                    band[y, hi] = True
    # a bridge's deck meets the water's tier at its parapets: unwalkable, coded as a band
    for y in range(H):
        for x in range(W):
            if bridge[y, x]:
                for nx in (x - 1, x + 1):
                    if 0 <= nx < W and not bridge[y, nx] and t0[y, nx] >= 0 and t0[y, nx] != t0[y, x]:
                        band[y, x] = True
    stair = np.zeros_like(walk)
    for sid, sk, r, lo, hi in STAIRS:
        m = _rect_mask(r, TOWN_W, TOWN_H)
        stair |= m & (face | (walk & (tier == hi)))
    walk &= ~face | stair
    walk &= ~band
    walk[stair] = True
    # back edges: a lower top north of a higher one meets it at a rail, not a step
    for y in range(H - 1):
        for x in range(W):
            if walk[y, x] and walk[y + 1, x] and t0[y, x] >= 0 and t0[y + 1, x] > t0[y, x] \
                    and not stair[y, x] and not stair[y + 1, x] and not face[y + 1, x]:
                walk[y + 1, x] = False   # the higher top's back rim (a railing or a wall)
    code = np.full((H, W), ord('0'), np.uint8)
    code[tier >= 0] = (ord('0') + tier[tier >= 0]).astype(np.uint8)
    code[face] = ord('f')
    code[band] = ord('b')
    code[stair] = ord('s')
    rows = [''.join(map(chr, r)) for r in code]
    return {'kind': kind, 'tier': tier, 'walk': walk, 'face': face, 'band': band, 'stair': stair,
            'buildings': bmask, 'tiers': rows}


def audit_tiers(R) -> list:
    """The world audit's tier rules (world_audit.py tier_checks) run on the plan's tier map,
    so the painted chunk starts from a map the audit passes."""
    t = np.array([[ord(c) for c in r] for r in R['tiers']], np.uint8)
    digit = (t >= ord('0')) & (t <= ord('9'))
    face, stair = t == ord('f'), t == ord('s')
    val = np.where(digit, t.astype(int) - ord('0'), -1)
    wk = R['walk']
    out = []
    for a, b in (((slice(None, -1), slice(None)), (slice(1, None), slice(None))),
                 ((slice(None), slice(None, -1)), (slice(None), slice(1, None)))):
        bad = digit[a] & digit[b] & wk[a] & wk[b] & (val[a] != val[b])
        out += [f'tier-step at box ({x * CELL}, {y * CELL})' for y, x in zip(*np.nonzero(bad))]
    H = t.shape[0]
    for x in range(t.shape[1]):
        y = 0
        while y < H:
            if face[y, x] and (y == 0 or not face[y - 1, x]):
                y1 = y
                while y1 < H and face[y1, x]:
                    y1 += 1
                above = val[y - 1, x] if y > 0 else -1
                below = val[y1, x] if y1 < H else -1
                if above >= 0 and below >= 0 and above <= below:
                    out.append(f'north-face at box ({x * CELL}, {y * CELL})')
                y = y1
            else:
                y += 1
    a, b = digit[:-1] & digit[1:], val[:-1] > val[1:]
    out += [f'a tier drops south with no face at box ({x * CELL}, {y * CELL})' for y, x in zip(*np.nonzero(a & b))]
    a, b = digit[:, :-1] & digit[:, 1:], val[:, :-1] != val[:, 1:]
    out += [f'side-band missing at box ({x * CELL}, {y * CELL})' for y, x in zip(*np.nonzero(a & b))]
    for y in range(H):
        x = 0
        while x < t.shape[1]:
            if stair[y, x]:
                x1 = x
                while x1 < t.shape[1] and stair[y, x1]:
                    x1 += 1
                if x1 - x < 8:
                    out.append(f'a stair {(x1 - x) * CELL} px wide at box ({x * CELL}, {y * CELL})')
                x = x1
            else:
                x += 1
    return out


def dist_from(walk, start):
    """Walk distance (px) from a box px point over the walk cells, 8-connected."""
    H, W = walk.shape
    sx, sy = start[0] // CELL, start[1] // CELL
    D = np.full((H, W), np.inf)
    if not walk[sy, sx]:
        return D
    D[sy, sx] = 0
    pq = [(0.0, sx, sy)]
    steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while pq:
        d, x, y = heapq.heappop(pq)
        if d > D[y, x]:
            continue
        for dx, dy, c in steps:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and walk[ny, nx]:
                if dx and dy and not (walk[y, nx] and walk[ny, x]):
                    continue
                nd = d + c * CELL
                if nd < D[ny, nx]:
                    D[ny, nx] = nd
                    heapq.heappush(pq, (nd, nx, ny))
    return D


def _near(D, p, r=2):
    x, y = p[0] // CELL, p[1] // CELL
    sl = D[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1]
    return float(sl.min()) if sl.size else math.inf


# The brief's walk times from the platform (8.3), seconds at 40 px/s, and where each is.
WALK_TIMES = [('the clock tower', 'junction:tower', 7.8), ('the gasholder', 'hill:gasholder', 10.3),
              ('the airship mast', 'hill:mast', 13.2), ('the lock', 'canal:lock', 18.1),
              ('the foundry', 'canal:foundry', 21.8), ('the allotments', 'canal:allotments', 22.7),
              ('the pump house', 'terminus:pump-house', 26.0), ('the maglev terminus', 'canal:terminus', 29.5)]
SPEED = 40


def _segments(poly):
    n = len(poly)
    for i in range(n):
        yield poly[i], poly[(i + 1) % n]


def check(R=None, verbose=True) -> list:
    R = R or rasterize()
    faults, notes = [], []
    fx, fy, fw, fh = FOOTPRINT
    inside = lambda p: fx <= p[0] < fx + fw and fy <= p[1] < fy + fh

    # the grid and the boxes
    for nm, (x, y) in (('town origin', TOWN_ORIGIN), ('fernhollow', FERNHOLLOW['box'][:2])):
        if x % GRID or y % GRID:
            faults.append(f'{nm} {x, y} is off the {GRID} px grid')
    for pl in PLACES:
        b = pl.get('box')
        if b and not (inside(b[:2]) and inside((b[0] + b[2] - 1, b[1] + b[3] - 1))):
            faults.append(f"{pl['id']}: box {b} leaves the region's footprint")
    for gid, k, t, poly, wk in GROUND:
        for x, y in poly:
            if x % GRID or y % GRID or not (0 <= x <= TOWN_W and 0 <= y <= TOWN_H):
                faults.append(f'ground {gid}: point {x, y} off the grid or outside the town box')
        for (x0, y0), (x1, y1) in _segments(poly):
            L = abs(x1 - x0) + abs(y1 - y0)
            on_box = (x0 == x1 and x0 in (0, TOWN_W)) or (y0 == y1 and y0 in (0, TOWN_H))
            # Matt, 21 Oct 11:44 (to-all-grid-2x): outlines run straight along the grid, as
            # Eastward's do; the old rule against straight runs over 96 px is withdrawn, so a
            # long run is only reported
            if L > 96 and (x0 == x1 or y0 == y1) and not on_box and verbose and os.environ.get('PLAN_RUNS'):
                notes.append(f'ground {gid} ({k}): a {L} px straight edge')
    for b in BUILDINGS:
        x0, top, x1, foot = b[3]
        if x0 % GRID or x1 % GRID or foot % GRID:
            faults.append(f'building {b[0]}: its foot line {x0, x1, foot} is off the grid (the picture\'s top may be anywhere)')
    for nm, kind_, at, route, where, sprite in NAMED:
        if not inside(at):
            faults.append(f'named thing {nm} at {at} is outside the footprint')
    tx, ty = TOWN_ORIGIN
    absorbed = [(k, what, at) for k, pts in MARKERS.items() if k != 'fernhollow' for kk, what, at in pts
                if tx <= at[0] < tx + TOWN_W and ty <= at[1] < ty + TOWN_H]
    if absorbed:
        notes.append(f'{len(absorbed)} route markers lie inside the town box; they are laid as town slots')
    for nm, kind_, at, route, where, sprite in NAMED:
        if tx <= at[0] < tx + TOWN_W and ty <= at[1] < ty + TOWN_H:
            faults.append(f'named thing {nm} at {at} is inside the town box (the routes end at its gates)')
    for p in SPOIL:
        if tx - 24 <= p[0] < tx + TOWN_W + 24 and ty - 24 <= p[1] < ty + TOWN_H + 24:
            faults.append(f'spoil heap at {p} is in the town')
    for k, pts in MARKERS.items():
        for kk, what, at in pts:
            if not inside(at):
                notes.append(f'{k} marker {what} at {at} lies outside the footprint (on the route chunk)')

    # faces and tiers (the audit's rules, on the plan)
    t, face = R['tier'], R['face']
    H, W = t.shape
    for x in range(W):
        y = 0
        while y < H:
            if face[y, x]:
                y1 = y
                while y1 < H and face[y1, x]:
                    y1 += 1
                above = t[y - 1, x] if y > 0 else -1
                hpx = (y1 - y) * CELL
                # the face may end where something stands in front of it (a bridge, the box)
                if hpx not in (12, 16, 32, 40) and y1 < H and not R['buildings'][y1, x] and R['kind'][y1, x] != KIND_IDS.get('bridge'):
                    below = t[y1, x]
                    if below >= 0 and above >= 0 and TIER_PX[above] - TIER_PX[below] == hpx:
                        pass
                    else:
                        faults.append(f'face at box ({x * CELL}, {y * CELL}) is {hpx} px (12, 16, 32 or 40)')
                y = y1
            else:
                y += 1
    walk, stair = R['walk'], R['stair']
    digit = t >= 0
    for (sa, sb) in (((slice(None, -1), slice(None)), (slice(1, None), slice(None))),
                     ((slice(None), slice(None, -1)), (slice(None), slice(1, None)))):
        bad = digit[sa] & digit[sb] & walk[sa] & walk[sb] & (t[sa] != t[sb]) & ~stair[sa] & ~stair[sb]
        for y, x in list(zip(*np.nonzero(bad)))[:5]:
            faults.append(f'walkable cells on two tiers meet with no stair or ramp at box ({x * CELL}, {y * CELL})')
    for sid, sk, r, lo, hi in STAIRS:
        w = r[2] - r[0]
        if w < 34:
            faults.append(f'{sid}: {w} px open (34 or more)')
        if sk == 'ramp' and (r[2] - r[0]) < 3 * (TIER_PX[hi] - TIER_PX[lo]):
            faults.append(f'{sid}: a ramp {r[2] - r[0]} px long for a {TIER_PX[hi] - TIER_PX[lo]} px rise (1 in 3)')

    tf = audit_tiers(R)
    for f in tf[:12]:
        faults.append('audit (tiers): ' + f)
    if len(tf) > 12:
        faults.append(f'audit (tiers): {len(tf) - 12} more')

    # everything reached from the platform, and the brief's walk times
    D = dist_from(walk, STANDS['junction:platform'])
    for nm, p in STANDS.items():
        if not walk[p[1] // CELL, p[0] // CELL]:
            faults.append(f'stand {nm} at {p} is not on walkable ground')
        elif not np.isfinite(_near(D, p, 0)):
            faults.append(f'stand {nm} at {p} is not reached from the platform')
    for b in BUILDINGS:
        for dx, dy in b[5]:
            off = {'s': (0, 4), 'n': (0, -4), 'e': (4, 0), 'w': (-4, 0)}[b[4]]
            q = (dx + off[0], dy + off[1])
            if not np.isfinite(_near(D, q, 1)):
                faults.append(f'door of {b[0]} at {(dx, dy)} has no path to it')
    for g, p, edge in TOWN_GATES:
        q = (min(p[0], TOWN_W - CELL), min(p[1], TOWN_H - CELL))
        if not np.isfinite(_near(D, q, 2)):
            faults.append(f'the {g} gate at {p} is not reached from the platform')
    times = []
    for what, st, s in WALK_TIMES:
        d = _near(D, STANDS[st], 0)
        got = d / SPEED
        times.append((what, s, got))
        if not np.isfinite(got) or got > 1.3 * s:
            faults.append(f'{what}: {got:.1f} s from the platform (brief {s} s; no more than 30 % farther)')

    # the benchmark's density on the town (check 1) and the brief's counts
    screens = TOWN_W * TOWN_H / (320 * 576)
    doors = sum(len(b[5]) for b in BUILDINGS)
    n_i = sum(1 for k, _, _ in TOWN_SLOTS if k == 'I') + doors
    n_s = sum(1 for k, _, _ in TOWN_SLOTS if k == 'S')
    for lab, n in (('interactables', n_i), ('story props', n_s)):
        if n < 6 * screens:
            faults.append(f'the town has {n} {lab} for {screens:.1f} screens (6 a screen: {math.ceil(6 * screens)})')
    for k, x, p in TOWN_SLOTS:
        if not (0 <= p[0] < TOWN_W and 0 <= p[1] < TOWN_H):
            faults.append(f'slot {x} at {p} is outside the town box')
    for a in AREAS:
        if any(v % 32 for v in a['rect']):
            faults.append(f"area {a['id']} {a['rect']} is off the audit's 32 px cells")
    if len(NAMED) != 14:
        faults.append(f'{len(NAMED)} named things (the brief: 14)')
    if len(POCKETS) != 5:
        faults.append(f'{len(POCKETS)} secret pockets (the brief: 5)')
    route_markers = sum(len(v) for v in MARKERS.values())
    if route_markers + BRIEF_TOWN_MARKERS != 91:
        faults.append(f'{route_markers + BRIEF_TOWN_MARKERS} markers (the brief: 91)')
    if verbose:
        print(f'cogsworth plan: town {TOWN_W} x {TOWN_H} at {TOWN_ORIGIN}, {screens:.1f} screens; '
              f'{n_i} interactables ({doors} doors), {n_s} story props in town')
        for what, s, got in times:
            print(f'  platform to {what}: {got:5.1f} s (brief {s})')
        for n in notes:
            print('  note:', n)
        for f in faults:
            print('  FAULT:', f)
        print('cogsworth plan:', 'ok' if not faults else f'{len(faults)} fault(s)')
    return faults


# --- pictures -------------------------------------------------------------------------------
COLOURS = {
    'cog': (52, 92, 132), 'race': (70, 118, 150), 'canal': (64, 104, 128), 'lock': (40, 78, 112),
    'cinder': (118, 104, 92), 'heath': (78, 104, 62), 'yard': (128, 112, 98), 'setts': (156, 146, 132),
    'flags': (176, 168, 152), 'rails': (92, 80, 72), 'platform': (186, 172, 146), 'towpath': (150, 120, 92), 'quay': (140, 136, 128),
    'allotment': (110, 132, 70), 'building': (150, 74, 58), 'bridge': (170, 110, 80),
}


def blockout(R=None, scale=1):
    R = R or rasterize()
    inv = {v: k for k, v in KIND_IDS.items()}
    H, W = R['kind'].shape
    img = np.zeros((H, W, 3), np.uint8)
    for kid, nm in inv.items():
        img[R['kind'] == kid] = COLOURS.get(nm, (200, 0, 200))
    t = R['tier']
    img = (img.astype(float) * (0.82 + 0.06 * np.clip(t, 0, 3))[..., None]).clip(0, 255).astype(np.uint8)
    img[R['face']] = (img[R['face']] * 0.55).astype(np.uint8)
    img[R['band']] = (img[R['band']] * 0.7).astype(np.uint8)
    img[R['stair']] = (214, 196, 120)
    pic = Image.fromarray(img).resize((W * CELL * scale, H * CELL * scale), Image.NEAREST)
    d = ImageDraw.Draw(pic)
    s = scale
    for lid, sprite, (x0, y0, x1, y1), why in LANDMARKS:
        d.rectangle((x0 * s, y0 * s, x1 * s - 1, y1 * s - 1), outline=(250, 220, 90))
    for nm, (x, y) in STANDS.items():
        d.ellipse(((x - 3) * s, (y - 3) * s, (x + 3) * s, (y + 3) * s), fill=(255, 255, 255))
        d.text(((x + 4) * s, (y - 4) * s), nm.split(':')[1], fill=(255, 255, 255))
    for k, what, (x, y) in TOWN_SLOTS:
        c = (120, 230, 255) if k == 'I' else (255, 150, 200)
        d.rectangle(((x - 2) * s, (y - 2) * s, (x + 2) * s, (y + 2) * s), fill=c)
    for b in BUILDINGS:
        x0, y0, x1, y1 = b[3]
        d.text(((x0 + 2) * s, (y0 + 2) * s), b[0], fill=(255, 235, 210))
        for dx, dy in b[5]:
            d.rectangle(((dx - 3) * s, (dy - 2) * s, (dx + 3) * s, dy * s), fill=(40, 20, 10))
    for g, (x, y), e in TOWN_GATES:
        d.rectangle(((x - 6) * s, (y - 6) * s, (x + 6) * s, (y + 6) * s), outline=(255, 80, 80), width=2)
        d.text(((x + 8) * s, (y + 2) * s), g, fill=(255, 120, 120))
    return pic


def region_map(scale=0.25):
    """The region at a quarter: footprint, places, gorge, maglev, spoil, named things, pockets."""
    fx, fy, fw, fh = FOOTPRINT
    W, H = int(fw * scale), int(fh * scale)
    pic = Image.new('RGB', (W, H), (88, 108, 70))
    d = ImageDraw.Draw(pic)
    P = lambda p: ((p[0] - fx) * scale, (p[1] - fy) * scale)
    d.line([P(p) for p in GORGE['centre']], fill=(60, 50, 44), width=int(140 * scale))
    d.line([P(p) for p in GORGE['centre']], fill=(200, 230, 240), width=max(2, int(44 * scale)))
    d.line([P(p) for p in MAGLEV], fill=(230, 230, 250), width=2)
    for pl in PLACES:
        if 'box' in pl:
            x, y, w, h = pl['box']
            d.rectangle((*P((x, y)), *P((x + w, y + h))), outline=(250, 230, 120), width=2)
            d.text(P((x + 8, y + 8)), pl['id'], fill=(255, 255, 255))
    small = blockout().resize((int(TOWN_W * scale), int(TOWN_H * scale)), Image.NEAREST)
    pic.paste(small, tuple(int(v) for v in P(TOWN_ORIGIN)))
    for p in SPOIL:
        x, y = P(p)
        d.ellipse((x - 10, y - 7, x + 10, y + 7), fill=(30, 30, 34))
    for nm, k, at, *_ in NAMED:
        x, y = P(at)
        d.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(255, 210, 60))
        d.text((x + 4, y - 4), nm, fill=(255, 240, 180))
    for what, at, route in POCKETS:
        x, y = P(at)
        d.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(255, 120, 255), width=2)
    for k, pts in MARKERS.items():
        for kk, what, at in pts:
            x, y = P(at)
            d.point((x, y), fill=(120, 230, 255) if kk == 'I' else (255, 150, 200) if kk == 'S' else (255, 255, 255))
    return pic


def tier_rows():
    """The town's tier map rows (4 px cells), for the painter's Chunk.tiers."""
    return rasterize()['tiers']


def main(argv):
    if '--check' in argv:
        sys.exit(1 if check() else 0)
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-cogsworth-plan')
    os.makedirs(out, exist_ok=True)
    R = rasterize()
    blockout(R, 2).save(os.path.join(out, 'town-blockout-2x.png'))
    region_map().save(os.path.join(out, 'region-quarter.png'))
    with open(os.path.join(out, 'town-tiers.txt'), 'w') as f:
        f.write('\n'.join(R['tiers']) + '\n')
    print('wrote', out)
    sys.exit(1 if check(R) else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
