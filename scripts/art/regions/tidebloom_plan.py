"""The Tidebloom Isles and the Shell Bar: the region's plan as data (art/regions/tidebloom.json).

Lane C (Claude C, 21 Oct). Matt 10:03: build the world faster, accurately, on the rules;
to-all-kit-freeze (12:20): lanes stop extending their own painters and write their regions as
plans in Claude F's schema (docs/vision/region-plans.md), which the shared kit will paint.
The brief is docs/vision/regions/tidebloom-isles.md (world plan v5.3, PR #96).

The main isle follows the block-out (docs/vision/research/blockout/blockout-v52.json): a ring
round a drowned crater, the lagoon, breached to the south, about 1360 x 830 world px between
x 6000-7360 and y 6024-6856. The brief also names a decided island of 704 x 1152 (today's
four zones); it cannot stand in this box (5800 to 6912 is 1112 tall) and the block-out's
coast, the Shell Bar route (lane G, lib/world-routes.ts) and the ferry all meet the ring, so
the plan keeps the block-out's ring and lays the decided island's places on it in the same
order of walk time from the pier (see `places` and the open point in `_about`).

Tiers, in the brief's order (section 4): the landing, the lagoon's shores, the west arm and
Black-sand Cove at sea level (0); the rainforest across the north body and down the east body
(1); the headwaters on the east body (2); the old crater's rim with its pool on top (3). Faces
only on south edges (32 px a tier); every tier change on the paths is a stair 40 wide (no
ramps, eastward-edges 6.3). Outlines are on the grid in straight runs along x or y with a
jog of 8 px at most every 96 px (to-all-grid-2x; benchmark 8).

Beyond F's schema the plan carries, for the lanes that read it: `areas` (F's screens, #194),
`set_pieces` (the cliff core's library in the coast biome, the isle's landmarks proposed),
`clusters` and `cluster_slots` (Claude B's recipes, #188), `rest_spots`, `story` and `ring`
(Claude K's handoffs, #197: the naturalist's story, the quiet place with no ring), and the
`coast` it checks itself against (isle_faults), since F's check has no coast yet.

    python3 scripts/art/regions/tidebloom_plan.py           # write art/regions/tidebloom.json
    python3 scripts/art/region_plan.py --check              # hold it to the rules
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'art'))
import region_plan as rp  # noqa: E402

GRID = 8
BOX = [3696, 5792, 6112, 1120]          # the brief's x 3700-9800, y 5800-6912, snapped to the grid and 32 px cells


def jogged(x0, y0, x1, y1, seed=0, step=88, depth=8):
    """A rectangle on the grid as a rectilinear outline whose every side jogs 8 px in or out
    at most every 96 px, so no edge runs straight across a screen (benchmark 8) while the
    plan keeps to the grid's straight runs (to-all-grid-2x)."""
    def side(a, b, fixed, horizontal, sgn, s):
        pts = []
        n = max(1, (abs(b - a) + step - 1) // step)
        L = (b - a) / n
        out = 0
        for i in range(n):
            u0 = a + round(i * L / GRID) * GRID
            u1 = b if i == n - 1 else a + round((i + 1) * L / GRID) * GRID
            out = depth * sgn if (i + s) % 2 == 1 and n > 1 else 0
            if horizontal:
                pts += [[u0, fixed + out], [u1, fixed + out]]
            else:
                pts += [[fixed + out, u0], [fixed + out, u1]]
        return pts
    pts = []
    pts += side(x0, x1, y0, True, -1, seed)            # north, west to east
    pts += side(y0, y1, x1, False, 1, seed + 1)        # east, north to south
    pts += side(x1, x0, y1, True, 1, seed)             # south, east to west
    pts += side(y1, y0, x0, False, -1, seed + 1)       # west, south to north
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return out


def union_outline(rects, seed=0):
    """The rectilinear outline of a union of rectangles (each on the grid), traced on 8 px
    cells, with the 8 px jogs of `jogged` on runs over 96 px."""
    xs = [r[0] for r in rects] + [r[2] for r in rects]
    ys = [r[1] for r in rects] + [r[3] for r in rects]
    X0, Y0, X1, Y1 = min(xs) - 16, min(ys) - 16, max(xs) + 16, max(ys) + 16
    W, H = (X1 - X0) // GRID, (Y1 - Y0) // GRID
    m = np.zeros((H, W), bool)
    for (a, b, c, d) in rects:
        m[(b - Y0) // GRID:(d - Y0) // GRID, (a - X0) // GRID:(c - X0) // GRID] = True
    # jogs: along every boundary run longer than 12 cells, push a 1-cell notch or tab every 11
    for _ in range(1):
        e = m.copy()
        for y in range(1, H - 1):
            run = 0
            for x in range(W):
                top = m[y, x] and not m[y - 1, x]
                run = run + 1 if top else 0
                if top and run % 11 == 6:
                    e[y, x] = e[y, x - 1] = e[y, x - 2] = (seed + x) % 2 == 0
        for x in range(1, W - 1):
            run = 0
            for y in range(H):
                lft = m[y, x] and not m[y, x - 1]
                run = run + 1 if lft else 0
                if lft and run % 11 == 6:
                    e[y, x] = e[y - 1, x] = e[y - 2, x] = (seed + y) % 2 == 0
        m = e
    return trace(m, X0, Y0)


def trace(m, X0, Y0):
    """The outer boundary of the largest blob of a cell mask as a rectilinear polygon of grid
    points (world px), clockwise, without collinear points."""
    H, W = m.shape
    pad = np.zeros((H + 2, W + 2), bool)
    pad[1:-1, 1:-1] = m
    # edges between cells, as directed segments with the inside on the right
    edges = {}
    for y in range(H + 2):
        for x in range(W + 2):
            if not pad[y, x]:
                continue
            if not pad[y - 1, x] if y > 0 else True:
                edges[(x, y)] = (x + 1, y)
            if not pad[y + 1, x] if y < H + 1 else True:
                edges[(x + 1, y + 1)] = (x, y + 1)
            if not pad[y, x - 1] if x > 0 else True:
                edges[(x, y + 1)] = (x, y)
            if not pad[y, x + 1] if x < W + 1 else True:
                edges[(x + 1, y)] = (x + 1, y + 1)
    start = min(edges)
    pts, p = [start], edges[start]
    while p != start:
        pts.append(p)
        p = edges[p]
    out = []
    for i, q in enumerate(pts):
        a, c = pts[i - 1], pts[(i + 1) % len(pts)]
        if (a[0] == q[0] == c[0]) or (a[1] == q[1] == c[1]):
            continue
        out.append([X0 + (q[0] - 1) * GRID, Y0 + (q[1] - 1) * GRID])
    return out


def shell_bar_land():
    """The Shell Bar as land at low tide (so its markers, cocklers and the wreck stand on land, not in
    the sea, for #203's and #206's placement and reach checks): every 8 px cell within 48 px of
    lane G's line, and the islet the bar runs over, traced on the grid."""
    X0, Y0, X1, Y1 = 6600, BOX[1], 7080, 6120
    W, H = (X1 - X0) // GRID, (Y1 - Y0) // GRID
    m = np.zeros((H, W), bool)
    for r in range(H):
        for c in range(W):
            x, y = X0 + c * GRID + 4, Y0 + r * GRID + 4
            if rp.dist_to_line((x, y), SHELL_BAR) <= 48 or (6800 <= x < 6976 and 5816 <= y < 5976):
                m[r, c] = True
    return trace(m, X0 - GRID, Y0 - GRID)


def coast():
    """The main isle's coast from the block-out's tier grid (sea is -1), on 16 px cells (two
    grid cells: the coast steps in whole pairs, as Eastward's tile pairs), with the lagoon
    and its breach inside the outline."""
    from scipy import ndimage
    d = json.load(open(os.path.join(ROOT, 'docs', 'vision', 'research', 'blockout', 'blockout-v52.json')))
    G = np.array([[v for v, n in zip(r[0::2], r[1::2]) for _ in range(n)] for r in d['tiers']['rows']], np.int16)
    lab, _n = ndimage.label(G >= 0)
    isle = lab == lab[6200 // 8, 6400 // 8]
    c16 = isle[::2, ::2] | isle[1::2, ::2]                   # 16 px cells, either half land
    big = np.zeros(isle.shape, bool)
    big[::2, ::2] = big[1::2, ::2] = big[::2, 1::2] = big[1::2, 1::2] = c16
    big = ndimage.binary_opening(big, np.ones((3, 3)))       # no one-cell spurs or notches
    ys, xs = np.nonzero(big)
    y0, x0 = ys.min() - 2, xs.min() - 2
    sub = big[y0:ys.max() + 3, x0:xs.max() + 3]
    return trace(sub, x0 * GRID, y0 * GRID)


# --- the tiers (screen space: a raised top as seen, its south face hanging under its rim) ---------
# Masses with depth (to-all-volume, Matt 21 Oct 13:37): each tier is a union of blocks whose
# south rims sit at different rows, so its face steps forward in outcrops and back in recesses
# by whole cells (16 px, two grid cells at 1x, one cell at 2x), never one even band. A block
# is (x0, y0, x1, y1), its y1 the south rim. Stairs, falls and paths keep to the rims they meet.
RAINFOREST = [
    (6624, 6136, 6688, 6232),             # the west end, stepped back (a recess over the landing)
    (6688, 6136, 6800, 6248),             # the lagoon stair and the lower fall's lip
    (6800, 6136, 6896, 6232),             # a recess under the giant tree's canopy
    (6896, 6136, 7136, 6248),
    (6976, 6200, 7064, 6440),             # down the east body: the cove stair's face
    (7064, 6200, 7152, 6456),             # an outcrop of basalt over the cove
    (7152, 6200, 7224, 6440),             # the stream's fall into the cove
]
HEADWATERS = [
    (7008, 6176, 7056, 6360),
    (7056, 6176, 7136, 6368),             # a shallow outcrop between the two stairs
    (7136, 6176, 7192, 6360),
]
CRATER_RIM = [(7056, 6184, 7168, 6248)]

# --- the paths (axis runs, as the grid ruling wants them) -------------------------------------
SHELL_BAR = [[7000, 5792], [6968, 5792], [6936, 5792], [6904, 5792], [6896, 5792], [6896, 5824], [6896, 5856],
             [6896, 5888], [6896, 5920], [6896, 5952], [6896, 5960], [6864, 5960], [6832, 5960], [6808, 5960],
             [6808, 5992], [6808, 6024], [6808, 6032], [6776, 6032], [6744, 6032], [6720, 6032], [6720, 6064],
             [6720, 6080], [6704, 6080]]          # lane G's line inside the box (lib/world-routes.ts, shell-bar)
TRODS = [
    {'id': 'landing_way', 'why': "from the Shell Bar's landfall round the rainforest's west end down to Lagoon Landing",
     'width': 32, 'points': [[6704, 6080], [6600, 6080], [6600, 6176], [6576, 6176], [6576, 6272]]},
    {'id': 'isle_loop', 'why': "the isle's loop (plan 8.4, check 18): along the lagoon's north and east shores to "
                              "Black-sand Cove, up the east body to the headwaters, back across the rainforest past "
                              "the giant tree and down to the lagoon",
     'width': 24, 'points': [[6576, 6272], [6576, 6296], [6688, 6296], [6688, 6288], [6800, 6288], [6800, 6296],
                             [6952, 6296], [6952, 6400], [6944, 6400], [6944, 6488], [7024, 6488], [7024, 6344],
                             [7104, 6344], [7168, 6344], [7168, 6424], [7080, 6424], [6992, 6424], [6992, 6312],
                             [6992, 6200], [6880, 6200], [6880, 6176], [6736, 6176], [6736, 6288]]},
    {'id': 'west_arm', 'why': 'down the west arm, under the palms, to the turtle beach on its outer shore',
     'width': 24, 'dead_end': 'view', 'points': [[6576, 6272], [6448, 6272], [6448, 6440], [6400, 6440],
                                                  [6400, 6600], [6368, 6600], [6368, 6640]]},
    {'id': 'crater_spur', 'why': "up the crater's rim to the pool: a view over the isle and the lagoon (a pocket)",
     'width': 24, 'dead_end': 'view', 'points': [[7104, 6344], [7104, 6280], [7096, 6280], [7096, 6216]]},
    {'id': 'tree_pocket', 'why': 'a few steps off the loop to a bench under the giant tree (a pocket)',
     'width': 24, 'dead_end': 'bench', 'points': [[6840, 6176], [6840, 6152], [6904, 6152]]},
    {'id': 'sea_cave', 'why': "along the cove's black sand to the sea cave in the basalt arm (a pocket's story detail)",
     'width': 24, 'dead_end': 'story', 'points': [[6944, 6488], [6944, 6568], [6888, 6568], [6888, 6664]]},
]
STAIRS = [
    {'id': 'cove_stair', 'on': 'isle_loop', 'at': [7024, 6456], 'from_tier': 0, 'to_tier': 1, 'width': 48, 'kind': 'basalt'},
    {'id': 'headwaters_stair', 'on': 'isle_loop', 'at': [7024, 6376], 'from_tier': 1, 'to_tier': 2, 'width': 48, 'kind': 'basalt'},
    {'id': 'rim_stair', 'on': 'crater_spur', 'at': [7104, 6264], 'from_tier': 2, 'to_tier': 3, 'width': 48, 'kind': 'basalt'},
    {'id': 'fern_stair', 'on': 'isle_loop', 'at': [7168, 6376], 'from_tier': 2, 'to_tier': 1, 'width': 48, 'kind': 'timber'},
    {'id': 'lagoon_stair', 'on': 'isle_loop', 'at': [6736, 6264], 'from_tier': 1, 'to_tier': 0, 'width': 48, 'kind': 'timber'},
]
WATER = [
    {'id': 'crater_pool', 'kind': 'pool', 'closed': True, 'tier': 3,
     'points': [[7120, 6192], [7152, 6192], [7152, 6200], [7160, 6200], [7160, 6224], [7152, 6224], [7152, 6232],
                [7120, 6232], [7120, 6224], [7112, 6224], [7112, 6200], [7120, 6200]],
     'source': {'from': 'rain on the crater rim'}, 'outlet': {'to': 'crater_stream', 'at': [7144, 6216]},
     'why': "rain held in the old crater's cup on the rim"},
    {'id': 'crater_stream', 'kind': 'stream', 'width': 16,
     'points': [[7144, 6216], [7144, 6280], [7192, 6280], [7192, 6392], [7192, 6472], [7200, 6472], [7200, 6600]],
     'falls': [[7144, 6248, 32], [7192, 6360, 32], [7192, 6440, 32]],
     'source': {'from': 'crater_pool', 'at': [7144, 6216]}, 'outlet': {'to': 'the sea at Black-sand Cove', 'at': [7200, 6600]},
     'why': "the pool spills south over the rim (the upper fall), across the headwaters and down the east body's faces "
            'into Black-sand Cove and the sea'},
    {'id': 'rainforest_stream', 'kind': 'stream', 'width': 16,
     'points': [[6784, 6152], [6784, 6248], [6784, 6312]], 'falls': [[6784, 6248, 32]],
     'source': {'from': 'a spring (set piece)', 'at': [6784, 6152]}, 'outlet': {'to': 'the lagoon', 'at': [6784, 6312]},
     'why': "a spring under the rainforest's canopy: the lower fall drops it into the lagoon a few steps from the landing"},
]
CROSSINGS = [
    {'kind': 'footbridge', 'at': [6784, 6290], 'over': 'rainforest_stream', 'on': 'isle_loop', 'span': 24},
    {'kind': 'stepping_stones', 'at': [6784, 6176], 'over': 'rainforest_stream', 'on': 'isle_loop', 'span': 24},
]
STRUCTURES = [
    {'kind': 'pier', 'from': [6496, 6304], 'to': [6496, 6416], 'width': 32,
     'why': "the ferry from Driftwood (W4) comes in through the breach and ties up in the lagoon's calm"},
    {'kind': 'boathouse', 'at': [6640, 6328], 'why': 'at the lagoon\'s edge, its boat doors over the water, a slipway (#134)'},
]
PLACES = [   # the decided island's places, by walk time from the pier (brief 5)
    {'id': 'lagoon_landing', 'kind': 'hamlet', 'at': [6560, 6256], 'why': "the isle's one hamlet round the pier, sheltered by the crater ring"},
    {'id': 'lagoon_pier', 'kind': 'stop', 'at': [6496, 6304], 'walk_s': 0, 'moved_from': [6480, 6150]},
    {'id': 'boathouse', 'kind': 'landmark', 'at': [6640, 6328], 'walk_s': 5},
    {'id': 'lower_fall', 'kind': 'waterfall', 'at': [6784, 6256], 'walk_s': 10},
    {'id': 'turtle_beach', 'kind': 'beach', 'at': [6368, 6648], 'walk_s': 16, 'why': "the west arm's outer shore: turtles come ashore to lay"},
    {'id': 'sea_cave', 'kind': 'cave', 'at': [6880, 6680], 'walk_s': 18, 'why': 'the sea has hollowed the basalt arm'},
    {'id': 'giant_tree', 'kind': 'tree', 'at': [6904, 6152], 'walk_s': 20, 'why': "the rainforest's oldest tree, on the crater's fertile ash"},
    {'id': 'rain_shelter', 'kind': 'shelter', 'at': [7064, 6328], 'walk_s': 27},
    {'id': 'upper_fall', 'kind': 'waterfall', 'at': [7144, 6256], 'walk_s': 27},
    {'id': 'crater_pool', 'kind': 'pool', 'at': [7136, 6212], 'walk_s': 28},
    {'id': 'black_sand_cove', 'kind': 'cove', 'at': [7040, 6520], 'why': 'basalt from the crater weathered to black sand, the basalt arm and the sea stack'},
    {'id': 'sea_stack', 'kind': 'landmark', 'at': [7232, 6640], 'why': 'a basalt column the sea cut off the arm'},
    {'id': 'old_volcano', 'kind': 'landmark', 'at': [7112, 6216],
     'why': "the isle is an old volcano of the arc, long cold: its crater rim (T3) holds the pool, its breached "
            "caldera is the lagoon, its basalt makes the cove's black sand (the live volcano is the fire country's)"},
    {'id': 'shell_bar_islet', 'kind': 'islet', 'at': [6880, 5904], 'why': 'the Shell Bar runs over it: tide pools, terns nesting'},
]
POCKETS = [
    {'holds': "a view from the crater pool's rim over the isle and the lagoon", 'at': [7096, 6216], 'trod': 'crater_spur'},
    {'holds': 'a bench under the giant tree', 'at': [6904, 6152], 'trod': 'tree_pocket'},
    {'holds': 'a story detail in the sea cave: a smuggler\'s old lamp and a carved tally', 'at': [6888, 6664], 'trod': 'sea_cave'},
]
EGG_SPOTS = [{'what': 'the wreck on the Shell Bar', 'at': [6930, 5870], 'keep_clear_r': 32}]
MARKERS = [   # brief 5 (the block-out's slots); moved to fit the ground by region_plan.fix, keeping moved_from
    ('S', 'old boot', (6472, 6096)), ('S', 'cold fire ring', (6584, 6104)), ('I', 'resident', (6488, 6120)),
    ('S', 'lost hat', (6544, 6120)), ('S', 'cold fire ring', (6648, 6128)), ('I', 'resident', (6512, 6144)),
    ('S', 'marker stone', (6552, 6160)), ('I', 'bench', (6456, 6176)), ('S', 'cairn', (6440, 6208)),
    ('I', 'water trough', (6680, 6208)), ('I', 'noticeboard', (6696, 6216)), ('I', 'resident', (6552, 6232)),
    ('I', 'water trough', (6568, 6264)), ('I', 'door', (6672, 6264)), ('S', 'cairn', (6464, 6280)),
    ('S', 'mended fence', (6480, 6280)),
    ('A', 'terns', (6951, 5828)), ('I', 'door', (6856, 5848)), ('S', 'cold fire ring', (6871, 5894)),
    ('S', 'marker stone', (6826, 5927)), ('I', 'bench', (6827, 6023)), ('S', 'cart with a broken wheel', (6790, 6056)),
    ('A', 'terns', (6696, 6033)),
    ('A', 'turtles', (6388, 6640)), ('A', 'turtle hatchlings at dusk', (6344, 6624)),
]
MOVED_BY_HAND = {('door', (6856, 5848)): (6906, 5855)}   # off the wreck's egg spot

# --- the screens (Claude F's `areas`, #194): whole 32 px audit cells of the box over the walked
# land, three 384 px columns by three rows; a screen with no path in it is drawn, never walked
AREA_COLS = (6320, 6704, 7088)
AREA_ROWS = ((5792, 352), (6144, 384), (6528, 384))
# dressing the screens up to 2 interactables and 3 story props each (check 1), in the isles' own
# things rather than the moor's cairns: the rule is F's `dress`, the kinds are ours
# (by tier: the shore's things at sea level, the forest's on the raised ground)
DRESS_I = {0: ('driftwood bench', 'water butt', 'signpost'), 1: ('log bench', 'water butt', 'signpost')}
DRESS_S = {0: ('shell cairn', 'glass float', 'lobster pot', 'beached canoe'),
           1: ('carved post', 'mossy stone', 'fallen frond heap', 'old rope swing')}

# --- the cliff core's pieces (library: stair, ledge, path, spring, pond, snow_corner, boulders,
# scree, ivy), in the coast biome; the isle's own landmarks are proposed for the library
SET_PIECES = [
    {'piece': 'spring', 'at': [6784, 6152], 'why': "the rainforest stream's source under the canopy"},
    {'piece': 'pond', 'at': [7136, 6208], 'why': "the crater pool in the old volcano's cup"},
    {'piece': 'boulders', 'at': [7112, 6528], 'why': "basalt boulders at the foot of the east body's outcrop"},
    {'piece': 'boulders', 'at': [6312, 6680], 'why': "the turtle beach's west end: rocks the turtles haul past"},
    {'piece': 'scree', 'at': [7080, 6296], 'why': 'ash and basalt grit at the foot of the crater rim'},
    {'piece': 'ledge', 'at': [7216, 6464], 'why': 'a wet basalt ledge beside the cove fall'},
    {'piece': 'sea_stack', 'at': [7232, 6640], 'proposed': True, 'why': 'a basalt column the sea cut off the arm'},
    {'piece': 'sea_cave', 'at': [6880, 6680], 'proposed': True, 'why': "the cave mouth in the basalt arm's south face"},
    {'piece': 'basalt_columns', 'at': [6984, 6584], 'proposed': True, 'why': "the basalt arm's columns over Black-sand Cove"},
    {'piece': 'giant_tree', 'at': [6904, 6144], 'proposed': True, 'why': "the rainforest's oldest tree, its buttress roots over the path"},
    {'piece': 'crater_lip', 'at': [7112, 6192], 'proposed': True, 'why': "the old volcano's rim: a ring of weathered basalt round the pool"},
]

# --- where Claude B's prop clusters go (#188, scripts/art/prop_clusters.json). `shore` is the one
# recipe on #188; the four isle recipes are on #203 (proposed until it lands)
CLUSTER_SLOTS = [
    {'recipe': 'shore', 'near': [6440, 6312], 'why': "the landing's beach by the pier: a boat drawn up, nets drying"},
    {'recipe': 'shore', 'near': [6976, 6520], 'why': "Black-sand Cove's head: a fisher's corner on the black sand"},
    {'recipe': 'turtle_beach', 'proposed': True, 'near': [6400, 6640],
     'why': "the turtle beach kept clear above the tideline: a ring of shells round a nest, a warden's tally post, no boat"},
    {'recipe': 'lagoon_hamlet', 'proposed': True, 'near': [6528, 6200],
     'why': "Lagoon Landing's yard: the packing shed's door, crates of fruit, a hammock between two palms"},
    {'recipe': 'rainforest_clearing', 'proposed': True, 'near': [6872, 6184],
     'why': "under the giant tree: a mossy log, tree ferns, a naturalist's specimen table"},
    {'recipe': 'headwaters_shelter', 'proposed': True, 'near': [7064, 6320],
     'why': 'the rain shelter: a thatched roof on four posts, a rail, a bench, a water butt under the eave'},
]
# Every slot's placement comes from #203's placer, which keeps boats and nets by water
# (b-to-c-isles, 14:55). #188's rules (a shore's front within 48 px of a path) refuse the two shore
# placements and #188 does not know the isle recipes, so `clusters` stays empty until #203 lands;
# then the placements move into it (re-run `--place` on main to confirm).
CLUSTERS = []
PLACED_ON_203 = {
    'shore@landing': {'at': [6464, 6336], 'orient': 's', 'mirror': False, 'seed': 0},
    'shore@cove': {'at': [6944, 6576], 'orient': 's', 'mirror': False, 'seed': 0},
    'turtle_beach': {'at': [6376, 6616], 'orient': 'w', 'mirror': True, 'seed': 0},
    'lagoon_hamlet': {'at': [6384, 6224], 'orient': 's', 'mirror': False, 'seed': 0},
    'rainforest_clearing': {'at': [6800, 6112], 'orient': 's', 'mirror': True, 'seed': 0},
    'headwaters_shelter': {'at': [7024, 6296], 'orient': 's', 'mirror': False, 'seed': 0},
}

# --- rest spots and the story (Claude K's handoffs, #197: the naturalist, "an inch a year",
# apprentice Tuff). Each spot is open, reachable ground beside a path with a stand where the
# folk lies down; the chapter changes are reserved here and not drawn until Matt says yes
REST_SPOTS = [
    {'id': 'landing_hammock', 'what': 'a hammock at Lagoon Landing', 'at': [6536, 6216], 'stand': [6548, 6232],
     'night': True, 'chapter': 1, 'outing': 'A DAY ON THE ISLE'},
    {'id': 'rain_shelter', 'what': 'the rain shelter at the headwaters', 'at': [7064, 6312], 'stand': [7076, 6320],
     'chapter': 2},
    {'id': 'cove_sand', 'what': 'the black sand of the cove', 'at': [7048, 6528], 'stand': [7040, 6520], 'chapter': 3},
]
STORY = {
    'resident': 'naturalist', 'story': 'an inch a year', 'apprentice': 'Tuff', 'source': 'docs/story/handoffs.md (#197)',
    'chapters': [
        {'n': 1, 'at': 'landing_hammock', 'change': None},
        {'n': 2, 'at': 'rain_shelter', 'change': "the naturalist's notebook hangs open to dry on the shelter's rail, pages fanned",
         'reserve': [7056, 6304]},
        {'n': 3, 'at': 'cove_sand', 'change': 'the naturalist lies on the black sand by a smooth dent where the boulder '
                                             'used to sit, notebook shut, pencil behind her ear', 'reserve': [7060, 6536]},
    ],
    'draw': False,
}
RING = {'none': True, 'why': 'the Tidebloom Isles stay the quiet place with no ring (cast.md; no fight here, no rival)'}


def areas() -> list:
    """The screens over the walked land (F's `areas`), walkable when a path runs through them."""
    paths = SHELL_BAR_PATHS()
    out = []
    for r, (y, h) in enumerate(AREA_ROWS):
        for c, x in enumerate(AREA_COLS):
            walked = any(x <= px < x + 384 and y <= py < y + h for q in paths for px, py, _ in rp.sample(q, 8))
            a = {'id': f'tidebloom-{r}{c}', 'rect': [x, y, 384, h]}
            if not walked:
                a['walkable'] = False
            out.append(a)
    return out


def SHELL_BAR_PATHS():
    return [[tuple(p[:2]) for p in SHELL_BAR]] + [[tuple(p) for p in t['points']] for t in TRODS]


def count(p, rect, t):
    x, y, w, h = rect
    return sum(1 for m in p['markers'] if m['t'] == t and x <= m['at'][0] < x + w and y <= m['at'][1] < y + h)


def on_land(p, pt) -> bool:
    return any(isinstance(v, list) and inside_poly(pt, v) for v in p['coast'].values())


def in_water(p, pt, margin=6) -> bool:
    for w in p['water']:
        if w.get('closed'):
            if inside_poly(pt, w['points']) or rp.dist_to_line(pt, w['points'] + w['points'][:1]) < margin:
                return True
        elif rp.dist_to_line(pt, w['points']) <= w.get('width', 16) / 2 + margin:
            return True
    return False


def dress(p) -> list:
    """F's dressing rule (#194 `dress`) in the isles' own things: each walkable screen gets up to
    2 interactables and 3 story props, spread along its paths and set off to their side."""
    paths = p['routes'] + p['trods']
    G = rp.Ground(p)
    added, k = [], 0
    for a in p['areas']:
        if a.get('walkable') is False:
            continue
        x, y, w, h = a['rect']
        pts = [(px, py, q) for q in paths for px, py, _ in rp.sample(q["points"], 8)
               if x + 16 <= px < x + w - 16 and y + 16 <= py < y + h - 16]
        need = [('I', DRESS_I)] * max(0, 2 - count(p, a['rect'], 'I')) + \
               [('S', DRESS_S)] * max(0, 3 - count(p, a['rect'], 'S'))
        for j, (t, kinds) in enumerate(need):
            if not pts:
                break
            i0 = int((j + 0.5) * len(pts) / len(need))
            at = None
            for di in range(len(pts)):          # the nearest sample whose side is dry land
                px, py, q = pts[(i0 + di) % len(pts)]
                for side in ((1, -1) if (j + k) % 2 else (-1, 1)):
                    c = [int(px + side * (q['width'] / 2 + 16)) // 4 * 4, int(py) // 4 * 4]
                    ct, cf = G.at(*c)
                    if ct is not None and not cf and on_land(p, c) and not in_water(p, c, 10):
                        at = c
                        break
                if at:
                    break
            if not at:
                continue
            tier = G.at(*at)[0] or 0
            what = kinds[min(tier, 1)][k % len(kinds[min(tier, 1)])]
            p['markers'].append({'t': t, 'what': what, 'at': at, 'dress': True})
            added.append((a['id'], what, tuple(at)))
            k += 1
    return added


def inside_poly(pt, poly) -> bool:
    x, y = pt
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def isle_faults(p) -> list:
    """What Claude F's check cannot see yet (the schema has no coast): the isle's tiers, trods,
    stairs, rest spots and stands lie on the main isle's land, and every rest spot is open
    ground beside a path (#197: reachable, not in a pocket), on its tier, off the path itself.
    Also every screen with a path has its 2 interactables and 3 story props (check 1)."""
    land = p['coast']['main_isle']
    out = []
    G = rp.Ground(p)
    for t in p['tiers']:
        for q in t['outline']:
            if not inside_poly(q, land):
                out.append(f"tier {t['id']} point {tuple(q)} is in the sea")
    for tr in p['trods']:
        for q in (v[:2] for v in rp.sample(tr["points"], 8)):
            if not inside_poly(q, land):
                out.append(f"trod {tr['id']} runs into the sea at {tuple(int(v) for v in q)}")
                break
    for st in p['stairs']:
        if not inside_poly(st['at'], land):
            out.append(f"stair {st['id']} is in the sea")
    paths = p['routes'] + p['trods']
    for r in p['rest_spots']:
        for key in ('at', 'stand'):
            q = r[key]
            if not on_land(p, q):
                out.append(f"rest spot {r['id']} {key} is in the sea")
            tier, face = G.at(*q)
            if tier is None or face:
                out.append(f"rest spot {r['id']} {key} {tuple(q)} is not on walkable ground")
        d = [(rp.dist_to_line(r['stand'], q['points']), q) for q in paths]
        dd, q = min(d, key=lambda v: v[0])
        if dd < q['width'] / 2 + 4:
            out.append(f"rest spot {r['id']}'s stand is on the path {q['id']}")
        if dd > rp.BESIDE + 16:
            out.append(f"rest spot {r['id']}'s stand is {dd:.0f} px from any path (not beside one)")
        if any(pk.get('trod') == q['id'] for pk in p['pockets']):
            out.append(f"rest spot {r['id']} is in a pocket ({q['id']})")
    for m in p['markers'] + p['residents']:
        what = m.get('what') or m.get('who')
        if not on_land(p, m['at']):
            out.append(f"{what} at {tuple(m['at'])} stands in the sea")
        elif in_water(p, m['at'], 2):
            out.append(f"{what} at {tuple(m['at'])} stands in water")
    for a in p['areas']:
        if a.get('walkable') is not False and (count(p, a['rect'], 'I') < 2 or count(p, a['rect'], 'S') < 3):
            out.append(f"screen {a['id']}: {count(p, a['rect'], 'I')} interactables, {count(p, a['rect'], 'S')} story props")
    return out


def slot_key(c) -> str:
    if c['recipe'] != 'shore':
        return c['recipe']
    return 'shore@cove' if c['near'][0] > 6800 else 'shore@landing'


def plan() -> dict:
    p = {
        '_about': ("The Tidebloom Isles and the Shell Bar as a plan (Claude C, lane C, 21 Oct), in Claude F's schema "
                   '(docs/vision/region-plans.md), written by scripts/art/regions/tidebloom_plan.py. From the brief '
                   'docs/vision/regions/tidebloom-isles.md (PR #96, v5.3) and the block-out (#187). World px on the '
                   '11264 x 6912 canvas; tier outlines in SCREEN space. P1 (Claude A, a-to-c-196): the block-out sets the region\'s '
                   'position and outer extent, and the brief\'s decided island of 704 x 1152 '
                   'fits inside the block-out\'s ring rather than the reverse. So the ring round the lagoon stands, where '
                   "the Shell Bar route, the ferry and the coast meet it, and the decided island's places lie on it in the "
                   'same order of walk time from the pier (5 to 28 s). Nothing essential is lost: every place, the loop, '
                   'the tiers T0 to T3 and the pocket trods are kept; only the island\'s outline is the ring\'s, not a '
                   '704 x 1152 oblong.'),
        'id': 'tidebloom',
        'owner': 'claude-c',
        'biome': 'coast',
        'biomes': ['coast'],
        'biome_variant': "isles (scripts/art/biomes/coast.json, variants.isles): white and black sand, palms, "
                         'rainforest on ash; its tier faces are the proposed coast_isle edge set',
        'box': BOX,
        'base_tier': {'value': 0, 'provisional': True,
                      'from': "lane G's Shell Bar at tier 0 (lib/world-routes.ts); sea level, so the isle's beaches are 0"},
        'coast': {'main_isle': coast(), 'shell_bar': shell_bar_land(), 'why': "the block-out's ring, on 16 px steps; the lagoon is the notch through the breach",
                  'lagoon': "the drowned crater inside the ring's notch, breached to the south (x 6740-6830): "
                            'sheltered water for the ferry'},
        'tiers': [
            {'id': 'rainforest', 'tier': 1, 'why': "the crater ring's north and east bodies: rainforest on the old ash",
             'outline': union_outline(RAINFOREST, 1)},
            {'id': 'headwaters', 'tier': 2, 'why': 'the east body rises to the headwaters under the crater rim',
             'outline': union_outline(HEADWATERS, 2)},
            {'id': 'crater_rim', 'tier': 3, 'why': "the old volcano's crater rim, the isle's top, its pool held in the cup",
             'outline': union_outline(CRATER_RIM, 3)},
        ],
        'faces': {'_about': "Coast biome faces (to-all-reuse-rule): the isle's own basalt and ash banks under turf and "
                            'rainforest, 32 px a tier, south faces only; sea cliffs where a tier meets the sea, on the '
                            'cliff core when it lands (to-all-kit-freeze).',
                  'between_tiers': {'height': 32, 'material': 'ash and basalt under rainforest', 'edge_set': 'coast_isle (proposed)'},
                  'corners': 'rounded by the kit (the outline turns at cell corners; eastward-edges 1.6)',
                  'masses': 'each tier is a union of blocks whose south rims step 16 px in or out (to-all-volume 1)',
                  'sea_cliffs': {'height': '32 to 96', 'material': 'basalt', 'kit': 'cliff_core'}},
        'water': WATER,
        'crossings': CROSSINGS,
        'structures': STRUCTURES,
        'routes': [{'id': 'shell_bar', 'kind': 'bar', 'width': 48,
                    'owner_note': "lane G's route (lib/world-routes.ts, shell-bar), painted here to G's line; widths 40 to 56 along it",
                    'points': SHELL_BAR, 'widths': [[6896, 5888, 56], [6808, 6000, 56], [6720, 6064, 40]]}],
        'trods': TRODS,
        'stairs': STAIRS,
        'places': PLACES,
        'named': [],
        'pockets': POCKETS,
        'egg_spots': EGG_SPOTS,
        'markers': [dict({'t': t, 'what': w, 'at': list(a)},
                         **({'moved_from': list(MOVED_BY_HAND[(w, a)])} if (w, a) in MOVED_BY_HAND else {}))
                    for (t, w, a) in MARKERS],
        'obstacles': [],
        'set_pieces': [dict({'piece': sp['piece'], 'biome': 'coast', 'at': sp['at'], 'seed': i + 1},
                            **({'proposed': True} if sp.get('proposed') else {}), why=sp['why'])
                       for i, sp in enumerate(SET_PIECES)]
                     + [{'piece': 'stair', 'biome': 'coast', 'at': [st['at'][0] // GRID * GRID, st['at'][1] // GRID * GRID],
                         'seed': 20 + i, 'stair': st['id']} for i, st in enumerate(STAIRS)],
        'areas': areas(),
        'clusters': CLUSTERS,
        'cluster_slots': [dict(c, placement_203=PLACED_ON_203[slot_key(c)]) for c in CLUSTER_SLOTS],
        'rest_spots': REST_SPOTS,
        'story': STORY,
        'ring': RING,
        'edges': [{'side': 'all round', 'layers': 'none: the sea is the edge, surf on every shore; rocks and driftwood on '
                                                 'the beaches; past the box, the open sea is lane G\'s (g-to-all-edges 4)',
                   'beyond': 'the seven other isles on the horizon, drawn and never walked: about (5250, 6250), '
                             '(4050, 6120), (7850, 6450), (8700, 6650), (4650, 6650), (9600, 6500)'}],
        'thresholds': [{'id': 'shell_bar', 'at': [6888, 5888], 'route': 'shell_bar',
                        'sides': {'headland': 'claude-e', 'isles': 'claude-c'},
                        'band': 'sand, meadow, field -> meadow, sand, field2',
                        'landmark': {'what': 'the wreck', 'at': [6930, 5870]},
                        'residents': ['cocklers walking out at low tide', 'seals hauled out on the bar',
                                      'terns nesting on the islet'], 'radiates_from': 'the sea'}],
        'residents': [{'who': 'ferryman', 'at': [6520, 6296], 'note': 'at the pier'},
                      {'who': 'boatwoman', 'at': [6664, 6312], 'note': 'at the boathouse'},
                      {'who': 'naturalist', 'at': [6856, 6152], 'note': "under the giant tree; the isles' resident "
                                                                      '(the story "an inch a year")', 'resident': True},
                      {'who': 'turtles', 'at': [6388, 6640], 'note': 'come ashore on the turtle beach to lay; hatchlings run for the sea at dusk'},
                      {'who': 'beachcomber', 'at': [6368, 6664], 'note': 'on the turtle beach'},
                      {'who': 'cocklers', 'at': [6864, 5944], 'note': 'on the Shell Bar at low tide'}],
        'ground': {'_about': "Ground kinds by place, for the painter (the isles' own palette: lagoon teal, white and "
                             'black sand, rainforest greens; house-style accents lagoon and basalt).',
                   'shell_bar': 'wet rippled sand, shell banks, tide pools on the islet, terns\' scrapes',
                   'landing': 'pale coral sand and short turf round the pier, boats drawn up, nets drying',
                   'west_arm': 'white sand under coconut palms and pandanus, sea grape, the turtle beach\'s open sand',
                   'rainforest': 'dark loam under the canopy, ferns, roots, monstera, banana and tree ferns, moss on stones',
                   'headwaters': 'tree ferns and moss on basalt, the stream in rock pools',
                   'crater_rim': 'basalt and ash with moss and low shrubs, the pool in its cup',
                   'black_sand_cove': 'black basalt sand, the basalt arm\'s columns, rock pools, the sea stack'},
    }
    return p


def main(argv) -> int:
    p = plan()
    for _ in range(4):        # dress, settle, and dress again where settling moved a thing off its screen
        for area, what, at in dress(p):
            print(f'dressed {area} with a {what} at {at}')
        for what, a, b in rp.fix(p):
            print(f'moved {what} from {a} to {b}')
    path = os.path.join(ROOT, 'art', 'regions', 'tidebloom.json')
    with open(path, 'w') as fh:
        json.dump(p, fh, indent=1, default=int)
        fh.write('\n')
    faults = rp.check(p) + isle_faults(p)
    print(rp.summary(p))
    for f in faults:
        print('FAULT', f)
    print('wrote', path)
    return 1 if faults else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
