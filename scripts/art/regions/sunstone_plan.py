"""Sunstone Reach and the fire country, laid out as data (Claude D, lane D, 21 Oct).

Writes two region plans in Claude F's schema (scripts/art/region_plan.py, PR #174):
`art/regions/sunstone.json` (the steppe west of the Brackens gap, the Rift, the Sunstone basin:
box x 0-4800, y 0-4320) and `art/regions/fire-country.json` (Mount Ember, Hearthold, the forge,
Cinder Springs, Cinderwick and the Ash Coast: box x 0-5600, y 4000-5856). The brief is
docs/vision/regions/sunstone-basin-fire-country.md (world plan v5.3, PR #96); its named things,
pockets, markers and egg spots are read from it here, not copied by hand.

Routes are Claude G's (lib/world-routes.ts, PR #175): their lines, widths, tiers and tier
changes, side paths and pockets, read from lib/world-routes.ts when it is on the branch and
otherwise from the snapshot taken at #175 @ef8824f (sunstone_routes.json beside this file).
Tiers are G's absolute world tiers (base_tier 0): a tier is a 32 px south face; the plan's
outlines are in screen space, as F's schema has them.

Matt's direction (21 Oct): Eastward's soft grid, cleanliness, atmosphere from grouped props,
in our own palette per terrain; the art moves to about 2x density after his pilot verdict, so
this is resolution-independent work in world px (to-all-density). Outlines follow the 8 px
cell grid in straight runs along x or y, direction changes at cell boundaries, rounded corners
drawn by the painter (to-all-grid-2x, eastward-edges.md 1). No ramps (eastward-edges 6.3).

How the ground is made, so a reader can change it:
1. A designed height field on 8 px cells: the basin plateau rising to the massif in the north
   and falling east to the Rift and south to the salt lake; the Rift's gorge with benches; the
   Amber's canyon below the Dust Gulch fan; mesas; the volcano's cone with its upper cone never
   walked, the two flows, the coastal shelf and the sea. Places are laid as explicit terraces.
2. Smoothed onto the soft grid (a 3 x 3 cell median, then runs of at least two cells).
3. Every route and trod corridor is set to its own tier, and the ground north of it is held
   low enough that no face hangs over the path (a stair is the only way through a face).
4. Each tier is traced to outlines on the cell grid (holes joined to their outline by a slit,
   so one polygon carries them), and the result is rasterised back and compared cell for cell.

Run:
    python3 scripts/art/regions/sunstone_plan.py            write both plans
    python3 scripts/art/regions/sunstone_plan.py --check    rebuild and compare with the files
                                                            (exits non-zero if they differ)
    python3 scripts/art/regions/sunstone_plan.py --draw OUT  also draw the tier map and the plan
                                                            (F's region_plan.draw when present)
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
BRIEF = os.path.join(ROOT, 'docs', 'vision', 'regions', 'sunstone-basin-fire-country.md')
ROUTES_TS = os.path.join(ROOT, 'lib', 'world-routes.ts')
ROUTES_SNAPSHOT = os.path.join(HERE, 'sunstone_routes.json')
OUT = os.path.join(ROOT, 'art', 'regions')

C = 8                                  # the world's cell (world px)
FACE = 32                              # one tier's south face
W_ALL, H_ALL = 5600, 5856              # the field covers both boxes
NX, NY = W_ALL // C, H_ALL // C
BOXES = {
    'sunstone': [0, 0, 4800, 4320],
    'fire-country': [0, 4000, 5600, 1856],
}
SPLIT_Y = 4160                         # a thing in both boxes belongs to the basin above this
MY_ROUTES = ('drovers-road', 'lode-track', 'canyon-road', 'forge-stair', 'ember-way', 'ash-coast')
ROUTE_NAMES = {"Drover's Road": 'drovers-road', 'Lode Track': 'lode-track', 'Canyon Road': 'canyon-road',
               'Forge Stair': 'forge-stair', 'Ember Way': 'ember-way', 'Ash Coast': 'ash-coast'}
SNAPSHOT_AT = '#175 @ef8824f (claude-g/routes)'


# --- inputs --------------------------------------------------------------------------------

def _ts_to_json(src: str) -> str:
    """The generated TS literal (G's lib/world-routes.ts) as JSON: quote keys, turn single-
    quoted strings into JSON strings, drop trailing commas and `as const`."""
    out, i, n = [], 0, len(src)
    while i < n:
        ch = src[i]
        if ch in '\'"':
            j, buf = i + 1, []
            while src[j] != ch:
                if src[j] == '\\':
                    buf.append(src[j + 1])
                    j += 2
                    continue
                buf.append(src[j])
                j += 1
            out.append(json.dumps(''.join(buf)))
            i = j + 1
            continue
        m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\s*:', src[i:])
        if m and (not out or out[-1].rstrip()[-1:] in '{,'):
            out.append(json.dumps(m.group(1)) + ':')
            i += m.end()
            continue
        out.append(ch)
        i += 1
    text = ''.join(out)
    text = re.sub(r'\bas const\b', '', text)
    text = re.sub(r',(\s*[\]}])', r'\1', text)
    return text


def _ts_export(src: str, name: str):
    m = re.search(r'export const ' + name + r'(?::[^=]*)?=\s*', src)
    if not m:
        return None
    i = m.end()
    opener = src[i]
    closer = {'[': ']', '{': '}'}[opener]
    depth, j, q = 0, i, None
    while True:
        ch = src[j]
        if q:
            if ch == '\\':
                j += 2
                continue
            if ch == q:
                q = None
        elif ch in '\'"':
            q = ch
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                break
        j += 1
    return json.loads(_ts_to_json(src[i:j + 1]))


def load_routes() -> dict:
    """G's routes on lane D's land, thresholds and meeting cells: from lib/world-routes.ts when
    present, else the snapshot. Refreshes the snapshot when the TS is there."""
    if os.path.exists(ROUTES_TS):
        src = open(ROUTES_TS).read()
        routes = [r for r in _ts_export(src, 'worldRoutes') if r['id'] in MY_ROUTES]
        th = [t for t in _ts_export(src, 'worldThresholds') if 'claude-d' in t['sides']]
        meets = [m for m in _ts_export(src, 'worldRouteMeets') if 'claude-d' in (m['from'], m['to'])]
        stops = _ts_export(src, 'routeStops')
        data = {'source': 'lib/world-routes.ts', 'routes': routes, 'thresholds': th, 'meets': meets,
                'stops': {k: v for k, v in stops.items() if v['at'][0] < 5600 and v['at'][1] < 6000}}
        with open(ROUTES_SNAPSHOT, 'w') as fh:
            json.dump(data, fh, indent=1)
            fh.write('\n')
        return data
    with open(ROUTES_SNAPSHOT) as fh:
        return json.load(fh)


def parse_brief() -> dict:
    """The brief's section 5: named things, pockets, markers by place, egg spots."""
    text = open(BRIEF).read()
    named = []
    for m in re.finditer(r'^\| ([^|]+?)\s+\| (\w+)\s+\| \((\d+), (\d+)\)\s+\| ([^|]+?)\s+\| ([^|]+?)\s+\|$', text, re.M):
        thing, kind, x, y, route, where = m.groups()
        if route.strip() in ROUTE_NAMES:
            named.append({'thing': thing.strip(), 'kind': kind, 'at': [int(x), int(y)],
                          'route': route.strip(), 'where': where.strip()})
    pockets = []
    sec = text.split('**Secret pockets**')[1].split('**Markers')[0]
    for m in re.finditer(r'^\| ([^|]+?)\s+\| \((\d+), (\d+)\)\s+\| ([^|]+?)\s+\|$', sec, re.M):
        holds, x, y, route = m.groups()
        pockets.append({'holds': holds.strip(), 'at': [int(x), int(y)], 'route': route.strip()})
    markers = []
    sec = text.split('**Markers for the art**')[1].split('**Easter-egg')[0]
    for m in re.finditer(r'^- _([^_]+)_: (.+)$', sec, re.M):
        place, items = m.groups()
        for it in re.finditer(r'([ISA]) ([a-z \']+?) \((\d+), (\d+)\)', items):
            t, what, x, y = it.groups()
            markers.append({'t': t, 'what': what.strip(), 'at': [int(x), int(y)], 'place': place})
    eggs = []
    sec = text.split('**Easter-egg spots')[1].split('## 6')[0]
    for m in re.finditer(r'([a-z ]+?) \((\d+), (\d+)\)', sec.split(':', 1)[1]):
        eggs.append({'what': m.group(1).strip(), 'at': [int(m.group(2)), int(m.group(3))]})
    return {'named': named, 'pockets': pockets, 'markers': markers, 'eggs': eggs}


# --- geometry ------------------------------------------------------------------------------

def seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy), t


def line_dist(p, pts):
    return min(seg_dist(p, a, b)[0] for a, b in zip(pts, pts[1:]))


def nearest_on(p, pts):
    """The nearest point on a polyline, its segment index and the segment's direction."""
    best = None
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d, t = seg_dist(p, a, b)
        if best is None or d < best[0]:
            best = (d, i, (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (b[0] - a[0], b[1] - a[1]))
    return best


def length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def cells_xy():
    ys, xs = np.mgrid[0:NY, 0:NX]
    return xs * C + C / 2, ys * C + C / 2


XS, YS = cells_xy()


def dist_field(pts, mask_box=None):
    """Distance (px) from every cell centre to a polyline."""
    d = np.full((NY, NX), 1e9)
    for a, b in zip(pts, pts[1:]):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1.0
        t = np.clip(((XS - ax) * dx + (YS - ay) * dy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(XS - ax - t * dx, YS - ay - t * dy))
    return d


def poly_mask(poly):
    img = Image.new('L', (NX, NY), 0)
    ImageDraw.Draw(img).polygon([(x / C, y / C) for x, y in poly], fill=1)
    return np.asarray(img).astype(bool)


def rect_mask(x, y, w, h):
    return (XS >= x) & (XS < x + w) & (YS >= y) & (YS < y + h)


def rounded_rect(x, y, w, h, r=16):
    """A rectangle on the grid with its corners cut one cell (the painter rounds them)."""
    return [[x + r, y], [x + w - r, y], [x + w, y + r], [x + w, y + h - r], [x + w - r, y + h], [x + r, y + h],
            [x, y + h - r], [x, y + r]]


def snap(v, g=C):
    return int(round(v / g)) * g


# --- the land ------------------------------------------------------------------------------

# The Rift: from its gorge out of the massif, round the Heather spur's tip, east into the bay
# below it, west round the Fold spur, under Drover's bridge (4320, 3440) and the viaduct (4290,
# 3720), then round the arc's last hills to the ferry (4176, 5240) and its mouth (4250, 5380).
# It crosses a route only at the bridge and the ferry.
RIFT = [[4640, 1440], [4688, 1680], [4600, 1888], [4384, 2032], [4320, 2256], [4480, 2448], [4688, 2560],
        [4720, 2768], [4584, 2944], [4352, 3072], [4296, 3232], [4320, 3440], [4296, 3720], [4128, 3920],
        [4064, 4176], [4176, 4432], [4392, 4624], [4384, 4856], [4224, 5016], [4176, 5240], [4232, 5400],
        [4256, 5560]]
RIFT_BAYS = [((4600, 2560), 200), ((4352, 2080), 150), ((4160, 4280), 180)]   # wide green floors
# The Rift's tributaries from the Brackens (F's land; their last reach is here) and the
# Sedgeburn from the piedmont to the west.
TRIBS = [
    {'id': 'heather_burn', 'points': [[4800, 1960], [4720, 2000], [4600, 1984]], 'why': 'from the Heather spur (F)'},
    {'id': 'brackens_beck', 'points': [[4800, 2896], [4752, 2928], [4640, 2944]], 'why': 'from the Brackens (F)'},
    {'id': 'sedgeburn', 'points': [[3712, 4096], [3880, 4064], [4040, 4120], [4096, 4176]],
     'why': 'from the piedmont west of the Rift'},
]

# The Amber: out of its gorge in the massif, down the fan past Dust Gulch's west side, over
# the canyon head as falls west of the stairs, across the Canyon Road at the Amber ford
# (2720, 2960), round the mesa in its canyon, and into the salt lake.
AMBER = [[2584, 1440], [2600, 1696], [2536, 1952], [2448, 2192], [2440, 2440], [2520, 2624], [2664, 2736],
         [2720, 2848], [2720, 2960], [2784, 3016], [2880, 3072], [2904, 3208], [2856, 3352], [2840, 3520],
         [2880, 3696]]
AMBER_FALLS = [[2672, 2744], [2704, 2800]]
# The Willow Run: out of the massif east of the Lode, into its gravel fan where it sinks, up
# again at Palm Spring's pool, across the Drover's Road at the ford (3392, 2776), and into the
# Amber in the canyon.
WILLOW_UPPER = [[3720, 1440], [3696, 1696], [3608, 1936], [3568, 2120]]       # sinks at the end
WILLOW_LOWER = [[3456, 2696], [3392, 2776], [3320, 2880], [3176, 2968], [3040, 3040], [2904, 3160]]
PALM_POOL = rounded_rect(3424, 2640, 88, 56, 8)
SALT_LAKE = [[2672, 3696], [2800, 3672], [3024, 3664], [3216, 3696], [3296, 3768], [3280, 3880], [3160, 3952],
             [2944, 3968], [2752, 3944], [2656, 3864], [2640, 3768]]

# Mount Ember. The crater (a lava lake in a crag rim) and the upper cone are never walked; the
# forge stands on the caldera's south lip; Hearthold on its rock below, between the flows.
CRATER = (2470, 4560)
OLD_FLOW = [[2312, 4792], [2176, 4920], [2104, 5120], [2048, 5360], [1976, 5600], [1928, 5856]]
OLD_FLOW_W = 112
YOUNG_VENT = (2832, 4992)
YOUNG_FISSURE = [[2744, 4920], [2832, 4992]]
YOUNG_FLOW = [[2848, 5024], [2944, 5184], [3064, 5344], [3200, 5464], [3304, 5560], [3296, 5704], [3288, 5856]]
YOUNG_FLOW_W = 128
YOUNG_LOBES = [[[3064, 5344], [3176, 5304], [3232, 5336]], [[2944, 5184], [2880, 5272]]]
PARASITIC_CONES = [(2184, 4248, 40), (2648, 4232, 48), (2896, 4472, 36)]
CINDER_RISE = [[2176, 3840], [2272, 3832], [2400, 3880], [2520, 3928]]

# The coast of the fire country (the sea is the edge): the shore line, west to east. Lane G
# draws the open sea past it (g-to-all-edges 4).
COAST = [[0, 5824], [600, 5800], [1200, 5816], [1752, 5800], [1928, 5856], [2192, 5848], [2440, 5800],
         [2600, 5736], [2760, 5712], [2928, 5744], [3096, 5800], [3288, 5856], [3520, 5792], [3704, 5720],
         [3920, 5608], [4120, 5480], [4256, 5560], [4400, 5440], [4640, 5336], [4880, 5264], [5120, 5216],
         [5376, 5160], [5600, 5112]]

# The world's edges inside lane D's boxes: where the walk stops (the line is the wall's inner
# edge; the fade lies inside it, lane G's thin-out and beyond outside it). North: scree and
# boulders thickening into crags where the basin meets the massif, notched where the rivers
# come out of their gorges. West: tussocks and low dunes thickening into a dune wall with
# thorn scrub; the dune sea beyond.
NORTH_WALL = [[0, 1472], [512, 1472], [512, 1504], [1216, 1504], [1216, 1472], [1856, 1472], [1856, 1504],
              [2496, 1504], [2496, 1440], [2672, 1440], [2672, 1504], [2880, 1504], [2880, 1592], [3200, 1592],
              [3200, 1504], [3632, 1504], [3632, 1440], [3792, 1440], [3792, 1504], [4544, 1504], [4544, 1440],
              [4736, 1440], [4736, 1504], [4800, 1504]]
WEST_WALL = [[640, 1472], [640, 2048], [608, 2048], [608, 2560], [656, 2560], [656, 3200], [608, 3200],
             [608, 3776], [672, 3776], [672, 4400], [640, 4400], [640, 5160], [720, 5160], [720, 5816]]


def wall_y(x, line=NORTH_WALL):
    """The north wall's line (y) at x: the step line is piecewise constant on the grid."""
    best = line[0][1]
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        if ax <= x <= bx and ay == by:
            best = ay
    return best


def wall_x(y, line=WEST_WALL):
    best = line[0][0]
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        if ay <= y <= by and ax == bx:
            best = ax
    return best


# Places laid as explicit terraces (tier, rect). Each place's rect is its walkable ground;
# its buildings and yards are laid on it by the house kits.
PLACES = {
    'the-lode': {'name': 'the Lode', 'kind': 'mine', 'rect': [2920, 1600, 264, 176], 'tier': 10,
                 'why': 'iron and copper in the massif foothills, reached by a mule track'},
    'dust-gulch': {'name': 'Dust Gulch', 'kind': 'frontier', 'rect': [2488, 2264, 544, 320], 'tier': 8,
                   'why': 'where the Amber leaves the mountains: water, the mine above, the railhead'},
    'palm-spring': {'name': 'Palm Spring', 'kind': 'oasis', 'rect': [3328, 2632, 304, 216], 'tier': None,
                    'why': 'the Willow Run sinks into the gravel and comes up again here: the first water'},
    'hearthold': {'name': 'Hearthold', 'kind': 'hilltown', 'rect': [2280, 4920, 400, 400], 'tier': None,
                  'why': "a rock between two lava flows below the crater: the volcano's only defensible ground"},
    'ember-forge': {'name': 'the Ember forge', 'kind': 'forge', 'rect': [2352, 4776, 232, 136], 'tier': 15,
                    'why': "the crater's heat at the caldera lip; ore comes down from the Lode by cart"},
    'cinder-springs': {'name': 'Cinder Springs', 'kind': 'springs', 'rect': [2120, 5304, 216, 216], 'tier': None,
                       'why': "hot springs where the sea seeps into the volcano's warm flank"},
    'cinderwick': {'name': 'Cinderwick', 'kind': 'hamlet', 'rect': [2592, 5536, 336, 168], 'tier': None,
                   'why': 'a black-sand cove between the flows: charcoal and fish'},
}

# Mesas on the plateau and in the canyon: flat tops 32 to 96 px above the plateau, banded
# canyon faces, reached by ladder as lookouts (brief 4). (x, y, w, h, tiers up)
MESAS = [
    (2488, 3016, 128, 144, 3, 'canyon mesa', 'the Amber bends round it'),
    (1440, 2160, 256, 176, 2, 'west mesa', 'on the skyline from Dust Gulch'),
    (1832, 3216, 208, 144, 3, 'twin mesa', 'between the canyon and the dunes'),
    (1976, 2696, 144, 112, 2, 'little mesa', 'a lookout over the canyon rim'),
    (3640, 3312, 192, 128, 2, 'scrub mesa', 'seen from the Drover\'s Road above the ravine'),
    (4008, 2232, 192, 144, 2, 'rift mesa', 'the Rift goes round it'),
    (3184, 3352, 160, 112, 2, 'salt mesa', 'over the salt lake from the north'),
]


def ortho(pts, run=64):
    """A line on the soft grid: every diagonal stretch becomes a staircase of straight runs
    along x and y, each about `run` px, turning at cell boundaries (to-all-grid-2x)."""
    out = [[snap(pts[0][0]), snap(pts[0][1])]]
    for a, b in zip(pts, pts[1:]):
        ax, ay = out[-1]
        bx, by = snap(b[0]), snap(b[1])
        dx, dy = bx - ax, by - ay
        n = max(1, int(round(max(abs(dx), abs(dy)) / run)))
        for i in range(1, n + 1):
            x = snap(ax + dx * i / n)
            y = snap(ay + dy * i / n)
            px, py = out[-1]
            if abs(dx) >= abs(dy):
                out += [[x, py], [x, y]]
            else:
                out += [[px, y], [x, y]]
    clean = []
    for p in out:
        if not clean or clean[-1] != p:
            clean.append(p)
    return clean


def steps_y(y, at, tiers):
    """A tier that changes only at whole lines of y (horizontal rims)."""
    return np.select([y < a for a in at], tiers[:-1], tiers[-1])


def plateau():
    """The basin before the cuts, laid in rectangles: the plateau rising north to the massif
    in bands of whole rows, the land falling east to the Rift in bands of whole columns
    (contours along x and y only, never diagonal), the salt lake's pan in nested rectangles,
    and the coastal shelf in the south-east stepping down to the sea."""
    north = steps_y(YS, [1760, 2016, 2272], [11, 10, 9, 8])
    east = np.select([XS < 3296, XS < 3712, XS < 4128, XS < 4544], [8, 7, 6, 5], 4)
    T = np.where(YS < 2272, north, np.minimum(north, east)).astype(float)
    T = np.where((YS >= 2272) | (XS >= 3296), np.minimum(T, east), T)
    # the lake's pan: nested rectangles round the salt lake, 4 at the pan, a tier a 112 px ring
    lx0, ly0, lx1, ly1 = 2640, 3664, 3296, 3968
    ring = np.maximum.reduce([lx0 - XS, XS - lx1, (ly0 - YS) * 1.0, YS - ly1])
    T = np.minimum(T, 4 + np.ceil(np.maximum(ring, 0) / 112))
    # the coastal shelf in the south-east: 2 by the shore, a tier each 192 px inland
    cy = np.interp(XS, [p[0] for p in COAST], [p[1] for p in COAST])
    shelf = 2 + np.floor(np.clip(cy - 224 - YS, 0, None) / 192)
    T = np.where((YS > 3904) & (XS > 3104), np.minimum(T, shelf), T)
    return T


def cone(T):
    """Mount Ember in nested rounded rectangles (the painter rounds the corners): the upper
    cone round the crater, never walked; flanks gentle to the north and west (a tier each
    about 200 px, the Canyon Road's climb) and steep to the sea between the flows (a tier each
    about 56 px, the Ember Way's descent)."""
    dx, dy = XS - CRATER[0], YS - CRATER[1]
    r = np.maximum(np.abs(dx), np.abs(dy) * 1.1)
    seaward = (dy > 200) & (XS > 2160) & (XS < 3200)
    per = np.where(seaward, 56, 208)
    flank = np.where(r <= 296, 16 + (296 - r) // 48,
                     np.where(r <= 472, 12 + (472 - r) // 56, 12 - (r - 472) // per))
    w = r < 1400
    return np.where(w & (flank > T) | (r <= 472), flank, np.where(w, np.maximum(T, flank), T))


def blockify(T, k):
    """Each k x k block of cells takes the block's median: rims run in whole blocks."""
    H, W = T.shape
    B = T[:H - H % k, :W - W % k].reshape(H // k, k, W // k, k)
    med = np.median(B.transpose(0, 2, 1, 3).reshape(H // k, W // k, k * k), axis=2).astype(int)
    out = T.copy()
    out[:H - H % k, :W - W % k] = med.repeat(k, 0).repeat(k, 1)
    return out


RIFT_G = ortho(RIFT, 96)
AMBER_G = ortho(AMBER, 64)
WILLOW_UPPER_G = ortho(WILLOW_UPPER, 64)
WILLOW_LOWER_G = ortho(WILLOW_LOWER, 64)
OLD_FLOW_G = ortho(OLD_FLOW, 64)
YOUNG_FLOW_G = ortho(YOUNG_FLOW, 64)
CANYON_FLOOR = [[2800, 2880], [2744, 2880], [2744, 2960], [2680, 2960], [2680, 3216], [2616, 3216],
                [2616, 3304], [2560, 3304], [2560, 3520], [2504, 3520], [2504, 3600], [2448, 3600],
                [2448, 3704], [2392, 3704], [2392, 3784]]


def build_field(R):
    """The designed field (int tiers): the plateau and the cone in 32 px blocks, then the cuts
    (the Rift, the canyon, the lake, the mesas, the massif, the sea, the flows) in 16 px."""
    T = cone(plateau())
    # the coastal shelf east of the young flow stays low (the dead forest's coastal woods)
    cy = np.interp(XS, [p[0] for p in COAST], [p[1] for p in COAST])
    shelf = 2 + np.floor(np.clip(cy - 224 - YS, 0, None) / 192)
    T = np.where((YS > 3904) & (XS > 3104), np.minimum(T, shelf), T)
    T = blockify(np.floor(T).astype(int), 4)
    # the Rift: river and floor, benches in the bays, walls stepping up to the plateau
    dr = dist_field(RIFT_G)
    floor = steps_y(YS, [2208, 3008, 4608], [5, 4, 3, 2])
    half = np.full((NY, NX), 56.0)
    for (bx, by), rad in RIFT_BAYS:
        half = np.maximum(half, rad - np.maximum(np.abs(XS - bx), np.abs(YS - by)) * 0.6)
    T = np.where(dr < half, np.minimum(T, floor), T)
    T = np.where((dr >= half) & (dr < half + 80), np.minimum(T, floor + 1), T)
    T = np.where((dr >= half + 80) & (dr < half + 176), np.minimum(T, floor + 2), T)
    # the Amber's canyon: the floor at the Canyon Road's tiers, banded walls up to the fan
    dc = np.minimum(dist_field(CANYON_FLOOR), dist_field(AMBER_G[9:]))
    T = np.where(dc < 128, np.minimum(T, np.where(YS < 3264, 5, 6)), T)
    T = np.where((dc >= 128) & (dc < 208), np.minimum(T, np.where(YS < 3264, 6, 7)), T)
    # the canyon head: the fan's edge drops three tiers south of y 2712 (the stairs at x 2800)
    head = (YS >= 2712) & (YS < 2896) & (XS > 2560) & (XS < 2960)
    T = np.where(head, np.minimum(T, 7 - ((YS - 2712) // 88).astype(int)), T)
    # the salt lake: a white pan at tier 4
    T[poly_mask(ortho(SALT_LAKE + SALT_LAKE[:1], 48))] = 4
    # mesas
    for x, y, w, h, up, *_ in MESAS:
        m = rect_mask(x, y, w, h)
        base = int(np.median(T[m]))
        T[m] = base + up
    T = blockify(T, 2)
    # the massif north of the wall line: crags (the wall, 13) then lane G's beyond (14)
    wy = np.array([wall_y(x) for x in range(0, W_ALL, C)])[None, :].repeat(NY, 0)
    T = np.where(YS < wy, np.where(YS < wy - 176, 14, 13), T)
    # the sea and the beach
    cy = np.array([snap(v, 16) for v in np.interp(np.arange(0, W_ALL, C) + 4, [p[0] for p in COAST],
                                                  [p[1] for p in COAST])])[None, :].repeat(NY, 0)
    T = np.where(YS >= cy, 0, T)
    T = np.where((YS < cy) & (YS >= cy - 48), np.minimum(T, 1), T)
    # the old flow: crusted rubble in the chasm it cut, a tier below the flank, never walked
    do = dist_field(OLD_FLOW_G)
    T = np.where((do < OLD_FLOW_W / 2) & (YS < cy - 48), T - 1, T)
    return T


def terraces(T):
    """The places' own ground, on top of the field."""
    T = T.copy()

    def put(rect, tier):
        T[rect_mask(*rect)] = tier
    put(PLACES['the-lode']['rect'], 10)
    put(PLACES['dust-gulch']['rect'], 8)
    put([2488, 2160, 544, 104], 8)                       # the orchards and the platform's yard
    put(PLACES['ember-forge']['rect'], 15)
    # Palm Spring: the oasis on the pool's terrace (7); its orchards step down east to the road (6)
    put([3320, 2624, 320, 256], 7)
    # Hearthold: stepped streets from the forge stair's foot (12) down to the south-west gate
    # (9), the keep above the town on its own crag (13)
    put([2280, 4920, 400, 192], 12)
    put([2520, 4920, 160, 104], 13)
    put([2280, 5112, 400, 72], 11)
    put([2280, 5184, 120, 64], 10)
    put([2400, 5184, 280, 136], 11)
    put([2280, 5248, 120, 72], 9)
    # Cinder Springs: three pool terraces on the warm flank
    put([2120, 5304, 216, 96], 8)
    put([2120, 5400, 136, 120], 7)
    # Cinderwick: the hamlet on two steps over its black-sand cove
    put([2592, 5536, 160, 168], 2)
    put([2752, 5536, 176, 168], 3)
    return T


def soft_grid(T):
    """A 3 x 3 cell median, then every straight run at least two cells: no 8 px jaggies."""
    from numpy.lib.stride_tricks import sliding_window_view as sw
    P = np.pad(T, 1, mode='edge')
    T = np.median(sw(P, (3, 3)).reshape(NY, NX, 9), axis=2).astype(int)
    for _ in range(2):
        # a lone cell row or column between two equal neighbours takes their tier
        up, dn = np.roll(T, 1, 0), np.roll(T, -1, 0)
        T = np.where((up == dn) & (T != up), up, T)
        lf, rt = np.roll(T, 1, 1), np.roll(T, -1, 1)
        T = np.where((lf == rt) & (T != lf), lf, T)
    return T


def route_tier_at(route, x, y):
    """The tier of a route at a point: its nearest vertex's."""
    best = None
    for p in route['points']:
        d = math.hypot(p[0] - x, p[1] - y)
        if best is None or d < best[0]:
            best = (d, p[3])
    return best[1]


def tier_along(w):
    """A way's tier as a function of distance along it: its first vertex's tier, then each of
    lane G's changes at its boundary. A stair that climbs north cuts a south face, so the
    higher tier's rim lies 16 px north of the stair's point (the face is centred on it); a
    change that climbs south, or one on an east-west leg, meets at the point itself."""
    pts = w['points']
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

    def s_of(p):
        d, i, q, _ = nearest_on(p, pts)
        return cum[i] + math.hypot(q[0] - pts[i][0], q[1] - pts[i][1])
    bounds = []
    for ch in w.get('changes', []):
        if not mine(ch['at']):
            continue
        d, i, q, (dx, dy) = nearest_on(ch['at'], pts)
        at = list(ch['at'])
        if abs(dy) > abs(dx) and ((dy < 0) == (ch['to'] > ch['from'])):
            at[1] -= 16
        bounds.append((s_of(at), ch['to']))
    bounds.sort()
    first = pts[0][2]
    return s_of, bounds, first


def corridors(T, ways, changes):
    """Set each way's corridor to its tier, then hold the ground north of it low enough that
    no face hangs over it (a face is 32 px a tier, F's Ground); near a tier change the stair
    takes the face."""
    T = T.copy()
    own = np.full((NY, NX), -1)
    for w in ways:
        pts = w['points']
        half = w['width'] / 2 + 8
        idx = np.argwhere(dist_field(pts) <= half)
        if w.get('changes') is not None:
            s_of, bounds, first = tier_along(w)
        tiers = [p[2] for p in pts]
        vx = np.array([p[0] for p in pts], float)
        vy = np.array([p[1] for p in pts], float)
        for r, c in idx:
            x, y = c * C + C / 2, r * C + C / 2
            if w.get('changes') is not None:
                sc = s_of((x, y))
                t = first
                for sb, tt in bounds:
                    if sc >= sb:
                        t = tt
            else:
                t = tiers[int(np.argmin((vx - x) ** 2 + (vy - y) ** 2))]
            if own[r, c] < 0 or w.get('route'):
                T[r, c] = t
                own[r, c] = t
    near_change = np.zeros((NY, NX), bool)
    for ch in changes:
        near_change |= np.hypot(XS - ch[0], YS - ch[1]) < 12
    # hold the ground north of every corridor cell: a cell d px north of a path cell of tier t
    # may stand at most t + floor((d - 8) / 32) (8: F's polygons fill one 4 px row more)
    for c in range(NX):
        col = own[:, c]
        for r in np.nonzero(col >= 0)[0]:
            if near_change[r, c]:
                continue
            t = col[r]
            for k in range(1, 64):
                rr = r - k
                if rr < 0:
                    break
                if own[rr, c] >= 0 or near_change[rr, c]:
                    continue
                cap = t + (k * C - 8) // FACE
                if T[rr, c] > cap:
                    T[rr, c] = cap
    return T, own


# --- tracing tiers to outlines ---------------------------------------------------------------

def trace(mask):
    """The outline of a cell mask with no holes, as one ring of grid corners (world px from
    the mask's origin), clockwise on screen, collinear points dropped."""
    nxt = {}
    m = np.pad(mask, 1)
    for r, c in np.argwhere(mask):
        R, K = r + 1, c + 1
        if not m[R - 1, K]:
            nxt[(c, r)] = (c + 1, r)
        if not m[R, K + 1]:
            nxt[(c + 1, r)] = nxt.get((c + 1, r)) or (c + 1, r + 1)
        if not m[R + 1, K]:
            nxt[(c + 1, r + 1)] = nxt.get((c + 1, r + 1)) or (c, r + 1)
        if not m[R, K - 1]:
            nxt[(c, r + 1)] = nxt.get((c, r + 1)) or (c, r)
    start = min(nxt, key=lambda p: (p[1], p[0]))
    ring, cur = [start], nxt[start]
    while cur != start:
        ring.append(cur)
        cur = nxt[cur]
    simp = []
    n = len(ring)
    for i in range(n):
        a, b, c2 = ring[i - 1], ring[i], ring[(i + 1) % n]
        if (b[0] - a[0]) * (c2[1] - b[1]) - (b[1] - a[1]) * (c2[0] - b[0]) != 0:
            simp.append([int(b[0]) * C, int(b[1]) * C])
    return simp


def holeless(comp):
    """Split a connected cell mask into parts with no holes and no corner-only contacts:
    cut north-south through the middle of a hole until none is left."""
    from scipy import ndimage
    parts, todo = [], [comp]
    while todo:
        m = todo.pop()
        holes, nh = ndimage.label(~m)
        inner = [k for k in range(1, nh + 1)
                 if not (np.any(holes[0] == k) or np.any(holes[-1] == k) or np.any(holes[:, 0] == k)
                         or np.any(holes[:, -1] == k))]
        # a pinch (two cells meeting only at a corner) splits a ring trace badly: cut there too
        pinch = (m[:-1, :-1] & m[1:, 1:] & ~m[:-1, 1:] & ~m[1:, :-1]) | \
                (m[:-1, 1:] & m[1:, :-1] & ~m[:-1, :-1] & ~m[1:, 1:])
        if not inner and not pinch.any():
            parts.append(m)
            continue
        if inner:
            cols = np.nonzero((holes == inner[0]).any(0))[0]
            cut = int(cols[len(cols) // 2])
        else:
            cut = int(np.argwhere(pinch)[0][1]) + 1
        left, right = m.copy(), m.copy()
        left[:, cut:] = False
        right[:, :cut] = False
        for half in (left, right):
            lab, n = ndimage.label(half)
            todo += [lab == k for k in range(1, n + 1)]
    return parts


def tier_outlines(T, box, why):
    """Every tier of the box as outlines: for each tier t above the box's lowest, the
    outlines of the ground at t or higher (F's Ground lays them in order, taking the max)."""
    from scipy import ndimage
    x0, y0, w, h = box
    sub = T[y0 // C:(y0 + h) // C, x0 // C:(x0 + w) // C]
    lo = int(sub.min())
    out = [{'id': f't{lo}', 'tier': lo, 'why': why.get(lo, 'the lowest ground in the box'),
            'outline': [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]]}]
    for t in range(lo + 1, int(sub.max()) + 1):
        lab, n = ndimage.label(sub >= t)
        k = 0
        for j in range(1, n + 1):
            for part in holeless(lab == j):
                k += 1
                ring = [[int(x + x0), int(y + y0)] for x, y in trace(part)]
                out.append({'id': f't{t}_{k}', 'tier': t, 'why': why.get(t, 'the upper cone, never walked'),
                            'outline': ring})
    return out


def raster(tiers, box, full=False):
    """The tiers as F's Ground lays them (4 px pixels, PIL polygons, max), sampled at each
    8 px cell's inner quarter so PIL's filled outline row does not count (or all of it)."""
    x0, y0, w, h = box
    W4, H4 = w // 4, h // 4
    out = np.zeros((H4, W4), int)
    for t in sorted(tiers, key=lambda t: t['tier']):
        img = Image.new('L', (W4, H4), 0)
        ImageDraw.Draw(img).polygon([((x - x0) / 4, (y - y0) / 4) for x, y in t['outline']], fill=1)
        m = np.asarray(img).astype(bool)
        out[m] = np.maximum(out[m], t['tier'])
    return out if full else out[1::2, 1::2]


def f_ground(T):
    """What F's check will see (its Ground at 4 px over each plan's traced tiers), over
    both boxes: the tier and whether it is a face, at 4 px."""
    tier4 = np.zeros((H_ALL // 4, W_ALL // 4), int)
    face4 = np.zeros_like(tier4, bool)
    outlines = {}
    for pid in ('fire-country', 'sunstone'):
        x0, y0, w, h = BOXES[pid]
        tiers = tier_outlines(T, BOXES[pid], TIER_WHY)
        outlines[pid] = tiers
        t4 = raster(tiers, BOXES[pid], full=True)
        f4 = np.zeros_like(t4, bool)
        top = int(t4.max() - t4.min())
        for d in range(1, top * FACE // 4 + 1):
            up = np.vstack([t4[:1].repeat(d, 0), t4[:-d]])
            f4 |= (up - t4) * FACE > (d - 1) * 4
        ys = slice(y0 // 4, (y0 + h) // 4)
        xs = slice(x0 // 4, (x0 + w) // 4)
        if pid == 'sunstone':
            keep = np.ones_like(t4, bool)
        else:
            yy = (np.arange(t4.shape[0])[:, None] * 4 + y0).repeat(t4.shape[1], 1)
            xx = (np.arange(t4.shape[1])[None, :] * 4 + x0).repeat(t4.shape[0], 0)
            keep = ~((yy < SPLIT_Y) & (xx < 4800))
        tier4[ys, xs] = np.where(keep, t4, tier4[ys, xs])
        face4[ys, xs] = np.where(keep, f4, face4[ys, xs])
    return tier4, face4, outlines


# --- the ways ------------------------------------------------------------------------------

def clip_route(pts, box):
    """The part of an axis-aligned route inside a box, cut at the box's edges (on the grid)."""
    x0, y0, w, h = box
    x1, y1 = x0 + w, y0 + h

    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    def cut(a, b):
        # the point where a -> b crosses the box edge (axis-aligned segments only)
        for t in np.linspace(0, 1, 257):
            q = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
            if inside(q) != inside(a):
                return [snap(q[0]), snap(q[1])] + list(a[2:])
        return list(b)
    parts, cur = [], []
    for i, p in enumerate(pts):
        if inside(p):
            if not cur and i > 0:
                cur.append(cut(pts[i - 1], p)[:2] + list(p[2:]))
            cur.append(list(p))
        elif cur:
            cur.append(cut(pts[i - 1], p)[:2] + list(pts[i - 1][2:]))
            parts.append(cur)
            cur = []
    if cur:
        parts.append(cur)
    return [q for q in parts if len(q) >= 2]


def dedupe(pts):
    out = []
    for p in pts:
        if not out or out[-1][:2] != p[:2]:
            out.append(p)
    # drop points in the middle of a straight run
    simp = [out[0]]
    for i in range(1, len(out) - 1):
        a, b, c = simp[-1], out[i], out[i + 1]
        straight = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) == 0
        if not straight or b[2:] != a[2:]:
            simp.append(b)
    simp.append(out[-1])
    return simp


DEAD_END = {'a view down a gorge': 'view', 'a view over the land': 'view', 'a resident fishing': 'resident',
            'a story detail: initials cut in a stone': 'story', 'a bench under a tree': 'bench',
            'a story detail: an old grave': 'story', 'a hermit at a fire': 'resident'}

# Lane D's own ways: the settlements' streets and lanes, and the trods to things the brief
# puts off the routes. [id, width, points, why]
STREETS = [
    ['gulch_main_street', 40, [[2512, 2424], [2704, 2424], [2704, 2416], [2896, 2416], [2896, 2424], [3008, 2424]],
     "Dust Gulch's one street of false fronts, east to west along the fan"],
    ['gulch_cross_street', 32, [[2832, 2328], [2832, 2416], [2832, 2560]],
     'from the Lode Track down past the street to the canyon head'],
    ['gulch_platform_lane', 32, [[2832, 2368], [2904, 2368], [2904, 2344]], "to the desert line's platform"],
    ['gulch_drove_lane', 32, [[2864, 2472], [2864, 2416]], "the Drover's Road's end onto the street"],
    ['gulch_orchard_lane', 24, [[2512, 2416], [2512, 2200], [2632, 2200]], 'up the orchards along the Amber'],
    ['palm_orchard_lane', 32, [[3480, 2864], [3480, 2760], [3600, 2760]],
     "from the road past the pool to the water-seller's awning"],
    ['lode_yard', 32, [[2936, 1688], [3024, 1688], [3168, 1688]], 'the mine yard along the face'],
    ['hearthold_gate_street', 40, [[2440, 5080], [2472, 5080], [2472, 5120]],
     "from the west gate to the forge stair's foot and down to the Ember Way"],
    ['hearthold_keep_street', 32, [[2472, 5064], [2600, 5064], [2600, 4992]], 'up to the keep above the town'],
    ['hearthold_market_row', 32, [[2472, 5144], [2640, 5144], [2640, 5256]], 'the market row and the east wall walk'],
    ['forge_yard', 32, [[2392, 4872], [2464, 4872], [2560, 4872]], 'the forge yard on the caldera lip'],
    ['springs_upper', 32, [[2256, 5360], [2144, 5360]], 'along the upper pools'],
    ['springs_lower', 32, [[2256, 5456], [2152, 5456]], 'along the lower pools'],
    ['cinderwick_lane', 32, [[2704, 5616], [2760, 5616], [2760, 5664], [2904, 5664]],
     "the hamlet's lane above the black sand, from the Ember Way to the Ash Coast's end"],
]


def mine(p):
    """Inside lane D's land (either box)."""
    return (p[0] <= 4800 and p[1] <= 4320) or (p[0] <= 5600 and 4000 <= p[1] <= 5856)


def ways_for(R):
    """Every route (G's) and trod (G's side paths and pockets, then lane D's streets)."""
    routes, trods = [], []
    for r in R['routes']:
        routes.append({'id': r['id'], 'name': r['name'], 'route': True,
                       'points': [[p[0], p[1], p[3], p[2]] for p in r['points'] if mine(p)],
                       'changes': r['changes'], 'crossings': r['crossings']})
        for sp in r['sidePaths']:
            if not mine(sp['at']):
                continue
            sp = dict(sp, points=[[min(x, 4800) if y < 4000 else x, y] for x, y in sp['points']])
            trods.append({'id': f"{r['id']}_round_{sp['obstacle']}", 'width': sp['width'],
                          'points': [list(p) for p in sp['points']], 'obstacle': sp['obstacle'],
                          'obstacle_at': sp['at'], 'route_id': r['id'],
                          'why': f"round the far side of the {sp['obstacle']} (brief 7; lane G's side path)"})
        for pk in r['pockets']:
            if not mine(pk['clearing']):
                continue
            # a pocket path that strays into lane F's box (the view down a gorge goes to x 4808)
            # is held on lane D's side of x 4800
            pk = dict(pk, points=[[min(x, 4800) if y < 4000 else x, y] for x, y in pk['points']])
            trods.append({'id': f"{r['id']}_pocket_{pk['clearing'][0]}_{pk['clearing'][1]}", 'width': pk['width'],
                          'points': [list(p) for p in pk['points']], 'holds': pk['holds'],
                          'clearing': pk['clearing'], 'dead_end': DEAD_END[pk['holds']], 'route_id': r['id'],
                          'why': f"a secret pocket: {pk['holds']} (lane G's pocket path)"})
    for sid, w, pts, why in STREETS:
        trods.append({'id': sid, 'width': w, 'points': pts, 'why': why})
    return routes, trods


# --- placing things ------------------------------------------------------------------------

class Ground:
    def __init__(self, T, blocked, ways, face4):
        self.T = T
        self.face4 = face4
        self.blocked = blocked
        self.ways = ways
        self.bb = [(min(p[0] for p in w['points']) - 200, min(p[1] for p in w['points']) - 200,
                    max(p[0] for p in w['points']) + 200, max(p[1] for p in w['points']) + 200) for w in ways]
        self.taken = []

    def cell(self, x, y):
        c, r = int(x // C), int(y // C)
        if not (0 <= r < NY and 0 <= c < NX):
            return None
        return r, c

    def ok(self, x, y, near, lim, lo=0, clear=16, box=None):
        rc = self.cell(x, y)
        if rc is None or self.blocked[rc]:
            return False
        if box and not (box[0] + 8 <= x <= box[0] + box[2] - 8 and box[1] + 8 <= y <= box[1] + box[3] - 8):
            return False
        # also clear of faces a few px away (the thing's base must sit on the top, not the lip)
        for dx, dy in ((0, 0), (0, 8), (8, 0), (-8, 0), (0, -8), (4, 4), (-4, -4), (4, -4), (-4, 4)):
            q = self.cell(x + dx, y + dy)
            r4, c4 = int((y + dy) // 4), int((x + dx) // 4)
            if q is None or self.blocked[q] or not (0 <= r4 < self.face4.shape[0] and 0 <= c4 < self.face4.shape[1]) \
                    or self.face4[r4, c4]:
                return False
        dmin = 1e9
        for w, (bx0, by0, bx1, by1) in zip(self.ways, self.bb):
            if not (bx0 <= x <= bx1 and by0 <= y <= by1):
                continue
            d = line_dist((x, y), w['points'])
            if d < w['width'] / 2 + 8:
                return False
            dmin = min(dmin, d)
        for st in STAIRS_AT:
            if math.hypot(st[0] - x, st[1] - y) < st[2] / 2 + 12:
                return False
        if near is not None:
            dn = line_dist((x, y), near)
            if dn > lim or dn < lo:
                return False
        elif dmin > lim:
            return False
        return all(math.hypot(x - a, y - b) >= clear for a, b in self.taken)

    def place(self, at, near=None, lim=48, lo=0, box=None, rect=None, clear=16):
        """The nearest spot to `at` (on 4 px) that keeps every rule; inside `rect` if given."""
        x0, y0 = at
        if near is not None:
            d, i, q, _ = nearest_on(at, near)
            if d > lim:
                x0, y0 = q
        best = None
        for rad in range(0, 400, 4):
            ring = []
            for dx in range(-rad, rad + 1, 4):
                for dy in (-rad, rad) if abs(dx) != rad else range(-rad, rad + 1, 4):
                    ring.append((dx, dy))
            for dx, dy in ring:
                x, y = snap(x0 + dx, 4), snap(y0 + dy, 4)
                if rect and not (rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]):
                    continue
                if self.ok(x, y, near, lim, lo, clear, box):
                    d = math.hypot(x - at[0], y - at[1])
                    if best is None or d < best[0]:
                        best = (d, [x, y])
            if best and best[0] <= rad:
                break
        if best:
            self.taken.append(tuple(best[1]))
            return best[1]
        return None


STAIRS_AT = []      # (x, y, width): filled while the plans are built


# --- the plans -----------------------------------------------------------------------------

TIER_WHY = {
    0: 'the sea', 1: 'the beach: black sand, surf', 2: "the coast's lowest shelf, the Rift's mouth and floor",
    3: 'the coastal shelf (green, windward), the Rift floor in its gorge', 4: 'the salt lake, the steppe by the Brackens',
    5: "the Amber canyon's floor, the steppe west of the Rift", 6: 'the scrub, the canyon foot',
    7: 'Palm Spring, the scrub below the fan', 8: "Dust Gulch's fan and the desert plateau",
    9: 'the foothills, the Lode Track', 10: "the Lode's bench; the flanks", 11: "the volcano's west flank, Hearthold's lower town",
    12: "Hearthold's upper town", 13: "the keep's crag; the massif's crags (the wall, never walked)",
    14: "lane G's beyond (the massif's peaks), never walked",
    15: 'the forge on the caldera lip',
}


def build(R, brief):
    routes, trods = ways_for(R)
    STAIRS_AT.clear()
    changes = [c['at'] for r in routes for c in r['changes']]
    # 1. the designed field, the places, the soft grid
    T = terraces(build_field(R))
    T = soft_grid(T)
    T = terraces(T)
    # 2. routes, then trods, set to their tiers with the ground north of them held low
    T, own = corridors(T, [dict(width=max(p[3] for p in r['points']), points=[p[:3] for p in r['points']], route=True,
                                changes=r['changes']) for r in routes], changes)
    trod_ways = []
    for t in trods:
        pts = [[p[0], p[1], int(T[min(NY - 1, int(p[1] // C)), min(NX - 1, int(p[0] // C))])] for p in t['points']]
        trod_ways.append(dict(width=t['width'], points=pts))
    # a trod keeps the ground it lies on (its corridor takes the tier at each vertex) unless a
    # route already owns the cell
    T2, own2 = corridors(T, trod_ways, changes)
    T = np.where(own >= 0, T, T2)
    return T, routes, trods


WATER_W = {'rift': 40, 'amber': 24, 'willow_run': 16, 'heather_burn': 12, 'brackens_beck': 12, 'sedgeburn': 16}

AREAS = [
    # [id, name, kind, today's zone it keeps or replaces (None: new ground), rect]
    ['the-lode', 'the Lode', 'place', None, [2912, 1568, 288, 224]],
    ['gulch', 'Dust Gulch', 'place', 'gulch', [2464, 2144, 576, 448]],
    ['oasis', 'Palm Spring', 'place', 'oasis', [3296, 2624, 352, 288]],
    ['steppe', "the steppe west of the Brackens gap", 'route', None, [4448, 3232, 352, 416]],
    ['rift', "the Rift and Drover's bridge", 'route', None, [3968, 2944, 480, 832]],
    ['scrub', 'the scrub and the mesas', 'route', None, [3040, 2464, 928, 704]],
    ['canyon', 'the Amber canyon', 'route', None, [2368, 2592, 640, 1024]],
    ['salt-lake', 'the salt lake', 'route', None, [2560, 3616, 768, 416]],
    ['dunes', 'the dune sea edge', 'edge', None, [640, 1504, 640, 2816]],
    ['scorch', 'the ash fields and the Cinder Rise', 'route', 'scorch', [1888, 3616, 640, 704]],
    ['flank', "the volcano's west flank", 'route', None, [1888, 4320, 448, 576]],
    ['caldera', 'the Ember forge and the cart bay', 'place', 'caldera', [2336, 4768, 256, 160]],
    ['hearthold', 'Hearthold', 'place', 'hearthold', [2272, 4928, 416, 416]],
    ['springs', 'Cinder Springs', 'place', 'springs', [2080, 5280, 256, 256]],
    ['cinderwick', 'Cinderwick', 'place', None, [2560, 5536, 384, 192]],
    ['dead-forest', 'the dead forest and the crust causeway', 'route', None, [2944, 5216, 832, 480]],
    ['rift-mouth', "the Rift's mouth and the ferry", 'route', None, [3776, 5056, 704, 384]],
    ['ash-coast', "the Ash Coast's green shelf", 'route', None, [4480, 4288, 1120, 928]],
]

# Prop clusters (Claude B's library, a-to-b-clusters: recipes per biome; lane D names the
# places and the recipe each needs). [recipe, near (x, y), members by prop key, light, why]
CLUSTERS = [
    ['steppe camp', (4060, 3560), ['tent', 'cold fire ring', 'saddle', 'water skins', 'bunchgrass'], 'fire glow at dusk',
     'the caravan camp a short way off the Drover\'s Road'],
    ['sheepfold corner', (4440, 3480), ['drystone fold', 'hurdle', 'trough', 'sheep', 'bunchgrass'], None,
     'the far folds the flock goes on to over the bridge'],
    ['windpump stop', (4078, 3159), ['wind pump', 'stone trough', 'bench', 'sage'], None, 'the wind pump on the road'],
    ['oasis nook', (3500, 2720), ['date palms', 'bench', 'water-seller\'s awning', 'jars', 'reeds'], 'shade pool under the palms',
     "Palm Spring's pool"],
    ['orchard edge', (3600, 2800), ['fruit trees', 'channel', 'ladder', 'baskets'], None, "Palm Spring's orchards on their channels"],
    ['frontier street corner', (2800, 2392), ['false front', 'boardwalk', 'barrels', 'hitching rail', 'lantern'],
     'lantern at night', "Dust Gulch's street"],
    ['platform yard', (2930, 2360), ['water crane', 'buffer', 'crates', 'signal'], 'signal lamp', 'the desert line\'s terminus'],
    ['mine yard', (3080, 1660), ['ore tubs', 'rail stub', 'timber props', 'lamp', 'rubble'], 'lamp at the mine mouth', 'the Lode\'s yard'],
    ['canyon shade', (2660, 2930), ['rock arch', 'boulders', 'bench', 'creosote'], 'shade under the arch',
     'the rock arch at the canyon floor'],
    ['salt shore', (2640, 3660), ['salt crust', 'bleached snag', 'cairn', 'tracks'], None, "the salt lake's west shore"],
    ['ash field', (2240, 3940), ['ash drift', 'fireweed', 'basalt stumps', 'lizard rock'], None, 'the Cinder Rise'],
    ['fumarole field', (2207, 4185), ['fumarole', 'steam', 'sulphur crust', 'sample bags'], 'steam lit by low sun',
     "the sulphur-gatherer's camp"],
    ['forge yard', (2430, 4850), ['anvil', 'quench trough', 'ore cart', 'coal heap', 'bench'], 'forge glow', 'the Ember forge'],
    ['castle street', (2560, 5150), ['market stall', 'banner', 'barrels', 'bench', 'lantern'], 'lanterns', "Hearthold's market row"],
    ['springs bath', (2200, 5420), ['stone pool rim', 'towels on a rail', 'bench', 'steam'], 'steam', 'Cinder Springs'],
    ['black-sand shore', (2820, 5690), ['upturned boat', 'nets on poles', 'charcoal sacks', 'driftwood'], None, "Cinderwick's cove"],
    ['dead-forest glade', (3500, 5480), ['charred snags', 'fireweed', 'goats', 'black sand'], None,
     'the dead forest the young flow ran through'],
    ['ferry landing', (4220, 5200), ['landing stage', 'rope post', 'bench', 'ferryman\'s hut'], 'lamp on the post', 'the Rift ferry'],
    ['coast meadow', (5000, 4700), ['lone tree', 'sheep', 'stile', 'flowers'], None, "the Ash Coast's green shelf"],
]


def biome_at(x, y):
    """Which cliff-core biome a set piece at (x, y) belongs to (to-all-reuse-rule: never a
    recolour across biomes; ash is not built yet)."""
    for pid in ('hearthold', 'ember-forge'):
        rx, ry, rw, rh = PLACES[pid]['rect']
        if rx - 16 <= x <= rx + rw + 16 and ry - 16 <= y <= ry + rh + 16:
            return 'city'
    if y > 3800 and max(abs(x - CRATER[0]), abs(y - CRATER[1])) < 1300 and x < 3104:
        return 'ash'
    if y > 4400 and x >= 3104:
        return 'coast'
    if line_dist((x, y), RIFT_G) < 200:
        return 'meadow' if any(math.hypot(x - bx, y - by) < r for (bx, by), r in RIFT_BAYS) else 'canyon'
    return 'canyon'


def blocked_mask(T):
    b = np.zeros((NY, NX), bool)
    for pts, w in ((RIFT_G, 40), (AMBER_G, 24), (WILLOW_UPPER_G, 16), (WILLOW_LOWER_G, 16)):
        b |= dist_field(pts) < w / 2 + 8
    for t in TRIBS:
        b |= dist_field(t['points']) < 16
    b |= poly_mask(ortho(SALT_LAKE + SALT_LAKE[:1], 48)) | poly_mask(PALM_POOL)
    b |= dist_field(OLD_FLOW_G) < OLD_FLOW_W / 2 + 8
    b |= dist_field(YOUNG_FLOW_G) < YOUNG_FLOW_W / 2 + 8
    b |= np.maximum(np.abs(XS - CRATER[0]), np.abs(YS - CRATER[1]) * 1.1) <= 200
    fx, fy, fw, fh = PLACES['ember-forge']['rect']
    b |= (T >= 16) & ~rect_mask(fx, fy, fw, fh)
    b |= T <= 0
    b |= (dist_field(DESERT_LINE) < 16) | (dist_field(MINE_CART) < 16)
    wy = np.array([wall_y(x) for x in range(0, W_ALL, C)])[None, :].repeat(NY, 0)
    b |= YS < wy
    wx = np.array([wall_x(y) for y in range(0, H_ALL, C)])[:, None].repeat(NX, 1)
    b |= XS < wx
    return b


def auto_stairs(tier4, face4, way):
    """Where a trod crosses from one tier to another (walked as F's check walks it, faces
    skipped): a stair on it, in the middle of the face, at least 40 px open. On an east-west
    leg it is a round-end (a stair needs a south face)."""
    out = []
    pts = way['points']
    prev, face_from = None, None
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L // 4))
        for i in range(n + 1):
            x = a[0] + (b[0] - a[0]) * i / n
            y = a[1] + (b[1] - a[1]) * i / n
            r4, c4 = min(tier4.shape[0] - 1, int(y // 4)), min(tier4.shape[1] - 1, int(x // 4))
            if face4[r4, c4]:
                if face_from is None:
                    face_from = (x, y)
                continue
            t = int(tier4[r4, c4])
            if face_from is not None and (prev is None or t == prev[2]):
                # it passes through a face and comes out on the same tier (it leaves its route at
                # the route's stair): a stair on it there too, from the tier up to the face's top
                sx, sy = face_from
                top = int(tier4[max(0, int(sy // 4) - 10):int(sy // 4), int(sx // 4)].max(initial=t))
                out.append({'id': f"{way['id']}_stair_{len(out) + 1}", 'on': way['id'],
                            'at': [snap((x + sx) / 2, 4), snap((y + sy) / 2, 4)], 'from_tier': t, 'to_tier': max(top, t + 1),
                            'width': max(40, way['width'] + 8), 'kind': 'stair',
                            'why': "where it leaves its route on the route's stair"})
            if prev is not None and t != prev[2]:
                sx, sy = face_from if face_from else (prev[0], prev[1])
                mx, my = snap((x + sx) / 2, 4), snap((y + sy) / 2, 4)
                ew = abs(b[0] - a[0]) > abs(b[1] - a[1])
                out.append({'id': f"{way['id']}_stair_{len(out) + 1}", 'on': way['id'], 'at': [mx, my],
                            'from_tier': prev[2], 'to_tier': t, 'width': max(40, way['width'] + 8),
                            'kind': 'round-end' if ew else 'stair'})
            face_from = None
            prev = (x, y, t)
    return out


def leg_of(pts, at):
    d, i, q, (dx, dy) = nearest_on(at, pts)
    return 'ew' if abs(dx) > abs(dy) else 'ns'


def make_plans(T, routes, trods, R, brief):
    blocked = blocked_mask(T)
    tier4, face4, outlines = f_ground(T)
    all_ways = [dict(id=r['id'], width=max(p[3] for p in r['points']), points=[p[:2] for p in r['points']])
                for r in routes] + [dict(id=t['id'], width=t['width'], points=t['points']) for t in trods]
    G = Ground(T, blocked, all_ways, face4)
    # the stairs: G's tier changes (kind as G gives it), then lane D's on its own trods
    stairs, asks = [], []
    for r in routes:
        pts = [p[:2] for p in r['points']]
        for k, ch in enumerate(r['changes']):
            if not mine(ch['at']):
                continue
            w = max(p[3] for p in r['points'] if math.hypot(p[0] - ch['at'][0], p[1] - ch['at'][1]) < 80)
            st = {'id': f"{r['id']}_{ch['kind']}_{k + 1}", 'on': r['id'], 'at': list(ch['at']),
                  'from_tier': ch['from'], 'to_tier': ch['to'], 'width': max(40, w), 'kind': ch['kind'],
                  'from_lane_g': True}
            leg = leg_of(pts, ch['at'])
            d, i, q, (dx, dy) = nearest_on(ch['at'], pts)
            up_south = leg == 'ns' and ((dy > 0) == (ch['to'] > ch['from']))
            if ch['kind'] == 'stair' and leg == 'ew':
                asks.append(f"{r['name']} {ch['from']}>{ch['to']} at {tuple(ch['at'])}: a stair on an east-west leg "
                            '(a stair cuts a south face); a north-south leg or a round-end?')
            if up_south and ch['kind'] in ('stair', 'round-end'):
                asks.append(f"{r['name']} {ch['from']}>{ch['to']} at {tuple(ch['at'])}: climbs southward, so the "
                            'rim it crosses is a north edge (no face to cut); a round-end on an east-west leg?')
            stairs.append(st)
    for t in trods:
        stairs += auto_stairs(tier4, face4, t)
    STAIRS_AT.extend((s['at'][0], s['at'][1], s['width']) for s in stairs)
    eggs = [{'what': e['what'], 'at': e['at'], 'keep_clear_r': 32} for e in brief['eggs']]
    for e in eggs:
        G.taken += [(e['at'][0] + dx, e['at'][1] + dy) for dx in (-24, 0, 24) for dy in (-24, 0, 24)]
    route_line = {r['id']: [p[:2] for p in r['points']] for r in routes}

    def which_box(p):
        return 'sunstone' if (p[1] < SPLIT_Y and p[0] <= 4800) else 'fire-country'

    named = []
    for n in brief['named']:
        rid = ROUTE_NAMES[n['route']]
        if rid == 'drovers-road' and n['at'][0] > 4800:
            continue
        off = n['where'] != 'beside the path'
        at = G.place(n['at'], route_line[rid], lim=150 if off else 44, lo=56 if off else 0,
                     box=BOXES[which_box(n['at'])])
        item = dict(n)
        if at is None:
            item['unplaced'] = True
        elif at != n['at']:
            item['at'], item['moved_from'] = at, n['at']
        named.append(item)
    pockets = []
    for t in trods:
        if 'holds' in t:
            end = t['points'][-1]
            pockets.append({'holds': t['holds'], 'at': [snap(end[0], 4), snap(end[1], 4)], 'trod': t['id'],
                            'clearing': t['clearing'], 'from_lane_g': True})
            G.taken.append(tuple(end))
    markers = []
    settle = {'Cinder Springs': 'cinder-springs', 'Cinderwick': 'cinderwick', 'Dust Gulch': 'dust-gulch',
              'Ember forge': 'ember-forge', 'Hearthold': 'hearthold', 'Palm Spring': 'palm-spring', 'the Lode': 'the-lode'}
    for m in brief['markers']:
        item = {'t': m['t'], 'what': m['what'], 'at': m['at'], 'place': m['place']}
        if m['place'] in ROUTE_NAMES:
            rid = ROUTE_NAMES[m['place']]
            if rid == 'drovers-road' and m['at'][0] > 4800:
                continue
            at = G.place(m['at'], route_line[rid], lim=44, box=BOXES[which_box(m['at'])], clear=12)
        else:
            rx, ry, rw, rh = PLACES[settle[m['place']]]['rect']
            at = G.place(m['at'], None, lim=44, rect=[rx - 32, ry - 32, rw + 64, rh + 64],
                         box=BOXES[which_box(m['at'])], clear=12)
        if at is None:
            item['unplaced'] = True
        elif at != m['at']:
            item['at'], item['moved_from'] = at, m['at']
        markers.append(item)
    clusters = []
    for k, (recipe, near, members, light, why) in enumerate(CLUSTERS):
        at = G.place(list(near), None, lim=120, clear=24)
        c = {'recipe': recipe, 'at': at or list(near), 'members': members, 'seed': 1000 + k, 'why': why}
        if light:
            c['light'] = light
        if at is None:
            c['unplaced'] = True
        clusters.append(c)
    return dict(stairs=stairs, asks=asks, eggs=eggs, named=named, pockets=pockets, markers=markers,
                clusters=clusters, G=G, which_box=which_box, outlines=outlines)


# The desert line: in from the halt south of the road, over the Rift on its viaduct, north up
# the gorge's west rim (one level crossing with the Drover's Road), west above Palm Spring to
# the platform. The mine cart: from the Lode down east of the town (crossing the desert line
# and, once, the road and the Willow Run), past the salt lake's east shore, to the tunnel portal
# on the north flank; the tunnel runs under the rim to the cart bay.
DESERT_LINE = [[4800, 3768], [4296, 3720], [4184, 3720], [4184, 2560], [3296, 2560], [3296, 2368], [2960, 2368]]
MINE_CART = [[3040, 1640], [3240, 1640], [3240, 2480], [3272, 2480], [3272, 3296], [3400, 3296], [3400, 4096],
             [2896, 4096], [2896, 4416]]
TUNNEL = [[2896, 4416], [2632, 4664], [2472, 4900]]

GROUND = {
    '_about': "Ground kinds by place, for the painter, in the dry kit's terms (#137) on the house ramps per "
              'terrain (house-style.md): big calm fields of one tone with a few large soft blotches, tufts and '
              'stones clumped by rule, never speckle (to-all-clean).',
    'steppe': 'short yellowing grass in wide fields, bunchgrass clumps, the odd single tree, drystone folds',
    'rift': "banded ochre and red gorge walls; the green strip's meadow and willows in the bays and at the confluences",
    'scrub': 'hardpan and gravel with sage and creosote in clumps, saguaro and barrel cacti alone, mesas on the skyline',
    'oasis': 'date palms over a stone-rimmed pool, orchards on channels, reeds, the water-seller\'s awning',
    'gulch': 'packed dust street, boardwalks, false fronts, orchards along the Amber, the platform\'s cinders',
    'lode': 'spoil and rubble on a bench under the massif face, timber props, ore tubs on a rail stub',
    'canyon': 'a gravel floor and the Amber\'s wash between red and buff walls in bands; shade, boulders at the feet',
    'salt-lake': 'a white salt pan with polygon crust, a pale shore of gravel, bleached snags',
    'dunes': 'low dunes and tussocks thickening west into the dune wall with thorn scrub',
    'ash': 'grey ash over the scrub thinning north (dithered nowhere: blotches), drifts, fireweed, basalt stumps',
    'flows': 'the old flow: crusted rubble grown over with fireweed and lava-stone scrub; the young flow: black '
             'crust with glowing seams, steaming at the toe',
    'hearthold': 'castle stone streets in steps, the curtain wall, the keep on its crag',
    'forge': 'basalt yard on the caldera lip, coal heaps, the crater\'s glow behind the rim',
    'springs': 'stone-rimmed hot pools in terraces, warm wet basalt, ferns in the steam',
    'cinderwick': 'black sand, nets on poles, charcoal clamps, a few huts above the cove',
    'coast': "the green windward shelf: meadow and coastal woods, then snags among fireweed in the dead forest; "
             'black sand below the flows',
}


def in_box(p, box, pad=0):
    x0, y0, w, h = box
    return x0 - pad <= p[0] <= x0 + w + pad and y0 - pad <= p[1] <= y0 + h + pad


def poly_in_box(pts, box):
    return any(in_box(p, box) for p in pts)


def crossings(a_pts, b_pts):
    """Points where two axis-aligned polylines cross."""
    out = []
    for p, q in zip(a_pts, a_pts[1:]):
        for r, s in zip(b_pts, b_pts[1:]):
            d = (q[0] - p[0]) * (s[1] - r[1]) - (q[1] - p[1]) * (s[0] - r[0])
            if d == 0:
                continue
            t = ((r[0] - p[0]) * (s[1] - r[1]) - (r[1] - p[1]) * (s[0] - r[0])) / d
            u = ((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0])) / d
            if 0 <= t <= 1 and 0 <= u <= 1:
                x = [snap(p[0] + (q[0] - p[0]) * t), snap(p[1] + (q[1] - p[1]) * t)]
                if x not in out:
                    out.append(x)
    return out


def emit(T, routes, trods, R, P):
    G = P['G']
    plans = {}
    rail_desert = DESERT_LINE
    rail_mine = MINE_CART
    for pid, box in BOXES.items():
        own = (lambda p, pid=pid: P['which_box'](p) == pid)
        x0, y0, w, h = box
        # routes, clipped to the box, in F's shape (points, width, widths), with G's tiers
        rts = []
        for r in routes:
            for k, part in enumerate(clip_route(r['points'], box)):
                part = dedupe(part)
                width = max(set(p[3] for p in part), key=lambda v: sum(1 for p in part if p[3] == v))
                rts.append({'id': r['id'] if k == 0 else f"{r['id']}_{k + 1}", 'name': r['name'], 'kind': 'route',
                            'width': width, 'owner_note': f"lane G's line, widths and tiers (lib/world-routes.ts, "
                                                         f"{SNAPSHOT_AT}); lane D paints it inside the box",
                            'points': [p[:2] for p in part],
                            'widths': [[p[0], p[1], p[3]] for p in part if p[3] != width],
                            'tiers': [[p[0], p[1], p[2]] for i, p in enumerate(part) if i == 0 or p[2] != part[i - 1][2]],
                            'crossings': [c for c in r['crossings'] if in_box(c['at'], box)]})
        trs = []
        for t in trods:
            if not all(in_box(p, box) for p in t['points']):
                continue
            if pid == 'sunstone' and all(p[1] >= SPLIT_Y for p in t['points']):
                continue
            if pid == 'fire-country' and all(p[1] < SPLIT_Y for p in t['points']) and all(p[0] <= 4800 for p in t['points']):
                continue
            item = {k: v for k, v in t.items() if k in ('id', 'width', 'points', 'why', 'dead_end')}
            if t.get('route_id'):
                item['from_lane_g'] = True
            trs.append(item)
        trod_ids = {t['id'] for t in trs}
        path_ids = trod_ids | {r['id'] for r in rts}
        stairs = [s for s in P['stairs'] if in_box(s['at'], box) and s['on'] in path_ids]
        tiers = P['outlines'][pid]
        back = raster(tiers, box)
        sub = T[y0 // C:(y0 + h) // C, x0 // C:(x0 + w) // C]
        bad = int((back != sub).sum())
        if bad:
            raise SystemExit(f'{pid}: the traced tiers differ from the field in {bad} cells')
        water = []
        for wid, pts in (('rift', RIFT_G), ('amber', AMBER_G), ('willow_run_upper', WILLOW_UPPER_G),
                         ('willow_run_lower', WILLOW_LOWER_G)):
            if poly_in_box(pts, box):
                water.append({'id': wid, 'kind': 'river', 'width': WATER_W.get(wid.split('_upper')[0].split('_lower')[0], 16),
                              'points': pts})
        for t in TRIBS:
            if poly_in_box(t['points'], box):
                water.append({'id': t['id'], 'kind': 'stream', 'width': WATER_W[t['id']], 'points': ortho(t['points'], 48),
                              'why': t['why']})
        if pid == 'sunstone':
            water[1]['falls'] = AMBER_FALLS
            water[1]['why'] = 'snowmelt out of the massif, down its fan past Dust Gulch, over the canyon head, into the salt lake'
            water += [
                {'id': 'palm_pool', 'kind': 'pool', 'closed': True, 'points': PALM_POOL,
                 'why': 'the Willow Run comes up out of its gravel'},
                {'id': 'salt_lake', 'kind': 'salt pan', 'closed': True, 'points': ortho(SALT_LAKE + SALT_LAKE[:1], 48),
                 'why': 'where the Amber ends at the arc\'s foot: a white pan, wet only after a storm'},
                {'id': 'palm_channels', 'kind': 'channel', 'width': 8,
                 'points': [[3512, 2696], [3600, 2696], [3600, 2840]], 'why': 'orchard channels, a step across'},
                {'id': 'gulch_channels', 'kind': 'channel', 'width': 8,
                 'points': [[2456, 2224], [2560, 2224], [2560, 2280]], 'why': 'orchard channels off the Amber'},
            ]
            water[3]['why'] = 'sinks into its gravel fan here'
        else:
            water += [
                {'id': 'hot_pools', 'kind': 'pools', 'closed': True, 'points': rounded_rect(2160, 5328, 64, 32, 8),
                 'why': 'the upper pool'},
                {'id': 'hot_pools_lower', 'kind': 'pools', 'closed': True, 'points': rounded_rect(2168, 5424, 56, 24, 8),
                 'why': 'the lower pool'},
                {'id': 'sea', 'kind': 'sea', 'points': COAST,
                 'why': 'the shore line; lane G draws the open sea past it (g-to-all-edges 4)'},
            ]
        lava = []
        if pid == 'fire-country':
            lava = [
                {'id': 'crater', 'kind': 'crater', 'at': list(CRATER), 'r': 200,
                 'why': 'a lava lake in a crag rim; never walked'},
                {'id': 'old_flow', 'kind': 'old flow', 'width': OLD_FLOW_W, 'points': OLD_FLOW_G,
                 'why': "out of the summit crater's south-west breach: crusted rubble in the chasm it cut, edges "
                        'grown over; the chasm bridge crosses it (world plan 4.7)'},
                {'id': 'young_flow', 'kind': 'young flow', 'width': YOUNG_FLOW_W, 'points': YOUNG_FLOW_G,
                 'lobes': YOUNG_LOBES, 'vent': list(YOUNG_VENT), 'fissure': YOUNG_FISSURE,
                 'why': 'from a flank vent 500 px down the south-east side (a short fissure, a spatter cone glowing '
                        'in its throat) to its steaming toe at the sea; the crust causeway crosses it'},
                {'id': 'parasitic_cones', 'kind': 'cones', 'points': [[x, y] for x, y, _ in PARASITIC_CONES],
                 'why': 'on the north flank, with the fumarole field'},
            ]
        if pid == 'sunstone':
            lava = [{'id': 'cinder_rise', 'kind': 'ridge', 'points': CINDER_RISE,
                     'why': 'a low lava-stone ridge the Canyon Road cuts through (the reveal)'}]
        places = []
        for k, pl in PLACES.items():
            if in_box(pl['rect'][:2], box) and own(pl['rect'][:2]):
                x, y, ww, hh = pl['rect']
                places.append({'id': k, 'kind': pl['kind'], 'name': pl['name'], 'at': [x + ww // 2, y + hh // 2],
                               'rect': pl['rect'], 'why': pl['why']})
        areas = [{'id': a, 'name': n, 'kind': k, 'zone': z, 'rect': r} for a, n, k, z, r in AREAS
                 if own([r[0] + r[2] // 2, r[1] + r[3] // 2])]
        named = [n for n in P['named'] if own(n.get('moved_from', n['at'])) and in_box(n['at'], box)]
        pockets = [pk for pk in P['pockets'] if pk['trod'] in trod_ids]
        markers = [m for m in P['markers'] if own(m.get('moved_from', m['at'])) and in_box(m['at'], box)
                   and not m.get('unplaced')]
        eggs = [e for e in P['eggs'] if own(e['at'])]
        obstacles = [{'kind': t['obstacle'], 'at': t['obstacle_at'], 'passed_by': t['id'],
                      'why': "brief 7: a side path off the road at a Y, round the far side, back at a Y (lane G)"}
                     for t in trods if t.get('obstacle') and t['id'] in trod_ids]
        ruins = [{'what': 'a collapsed bridge', 'at': at, 'beside': f, 'why': 'brief 7: beside the ford, a ruin, not a way'}
                 for at, f in (([2672, 2984], 'the Amber ford'), ([3400, 2800], 'the Willow Run ford')) if own(at)]
        set_pieces = []
        for k, st in enumerate(stairs):
            set_pieces.append({'piece': 'stair', 'biome': biome_at(*st['at']), 'at': [snap(st['at'][0]), snap(st['at'][1])],
                               'seed': 100 + k, 'for': st['id']})
        if pid == 'sunstone':
            for k, (x, y, ww, hh, up, name, why) in enumerate(MESAS):
                set_pieces.append({'piece': 'ledge', 'biome': 'canyon', 'at': [x, y + hh], 'seed': 300 + k,
                                   'for': name, 'why': why})
                set_pieces.append({'piece': 'scree', 'biome': 'canyon', 'at': [x + ww // 2, y + hh + 32 * up],
                                   'seed': 320 + k, 'for': name})
            for k, (x, y) in enumerate(((2560, 2944), (2512, 3392), (2896, 3000), (2808, 3456))):
                set_pieces.append({'piece': 'scree', 'biome': 'canyon', 'at': [x, y], 'seed': 340 + k,
                                   'for': 'the Amber canyon walls'})
            for k, x in enumerate(range(304, 4800, 640)):
                set_pieces.append({'piece': 'scree', 'biome': 'canyon', 'at': [x, snap(wall_y(x))], 'seed': 360 + k,
                                   'for': 'the massif\'s foot (the wall layer)'})
        else:
            for k, (x, y, rad) in enumerate(PARASITIC_CONES):
                set_pieces.append({'piece': 'cinder_cone', 'biome': 'ash', 'at': [snap(x), snap(y)], 'seed': 400 + k,
                                   'pending': 'the ash biome is not built in the cliff core yet'})
            for k, (x, y, pc) in enumerate(((2832, 4992, 'spatter_cone'), (2207, 4185, 'fumarole'), (2457, 5500, 'fumarole'),
                                             (2836, 5685, 'fumarole'), (2800, 4296, 'steam_cave'))):
                set_pieces.append({'piece': pc, 'biome': 'ash', 'at': [snap(x), snap(y)], 'seed': 420 + k,
                                   'pending': 'the ash biome is not built in the cliff core yet'})
            for k, (x, y) in enumerate(((5168, 4816), (4256, 5048), (3888, 5384))):
                set_pieces.append({'piece': 'boulders', 'biome': 'coast', 'at': [x, y], 'seed': 440 + k,
                                   'for': 'the Ash Coast\'s boulders and the shelf\'s edge'})
        set_pieces = [sp for sp in set_pieces if in_box(sp['at'], box)]
        thresholds = [{'id': t['id'], 'at': t['at'], 'route': t['route'], 'sides': {'both': 'claude-d'},
                       'object_by': t['objectBy'], 'object': t['object'], 'band': t['band'],
                       'landmark': {'what': t['landmark'], 'at': t['landmarkAt']},
                       'residents': t['residents'].split('; '), 'radiates_from': t['radiatesFrom']}
                      for t in R['thresholds'] if in_box(t['at'], box) and own(t['at'])]
        meets = [m for m in R['meets'] if in_box(m['at'], box)]
        if pid == 'sunstone':
            edges = [
                {'side': 'north', 'line': NORTH_WALL, 'fade': 'scree and boulders thickening over 10 to 160 px',
                 'wall': 'crags 64 to 180 px deep north of the line (tier 13), notched where the Amber, the Willow '
                         'Run and the Rift come out of their gorges',
                 'beyond': "lane G: the massif's peaks (tier 14 here stands for it)",
                 'note': 'replaces the provisional line at y 1504 (g-to-all-edges 3)'},
                {'side': 'west', 'line': WEST_WALL, 'fade': 'scrub tussocks and low dunes thickening eastward-in',
                 'wall': 'a dune wall with thorn scrub, 64 to 180 px deep, west of the line',
                 'beyond': "lane G: the dune sea, its dust haze thickening westward, a far caravan route"},
                {'side': 'interior', 'between': 'the Amber, the Willow Run and the Rift',
                 'layers': 'thorn scrub and boulders in uneven patches, thinning out again behind; the basin\'s '
                           'scrub and mesas beyond, hazier (brief 6); land over about 470 px from a way is drawn, not walked'},
            ]
        else:
            edges = [
                {'side': 'south', 'line': COAST, 'layers': 'none on the cliffs: the sea is the edge, with surf; black '
                                                           'sand at Cinderwick and below the flows',
                 'beyond': 'lane G: the open sea and the drowned end of the arc'},
                {'side': 'west', 'line': [p for p in WEST_WALL if p[1] >= 4000],
                 'layers': 'the dune wall comes down to the sea cliffs; scrub and old flows west of the old flow '
                           'are drawn, not walked'},
            ]
        rest = []
        for n in named:
            if n['kind'] in ('view', 'well', 'camp', 'shrine') and not n.get('unplaced'):
                rest.append({'at': n['at'], 'kind': n['kind'], 'why': f"{n['thing']} ({n['route']})"})
        for pk in pockets:
            if pk['holds'] in ('a bench under a tree', 'a view down a gorge', 'a view over the land'):
                rest.append({'at': pk['at'], 'kind': 'pocket', 'why': pk['holds']})
        seen = set()
        for m in markers:
            if m['place'] in PLACE_OF and m['what'] == 'bench' and m['place'] not in seen:
                seen.add(m['place'])
                rest.append({'at': m['at'], 'kind': 'bench', 'why': f"a bench in {m['place']}"})
        for k, r in enumerate(rest):
            r['id'] = f'rest_{k + 1}'
        rings, stops, rails = [], [], []
        if pid == 'fire-country':
            at = G.place([2520, 4840], None, lim=48, clear=24, rect=PLACES['ember-forge']['rect'])
            rings.append({'id': 'caldera-ring', 'zone': 'caldera', 'at': at, 'backdrop': 'lava',
                          'why': "today's sparring ring in the caldera (lib/world-places.ts rings) moves to the forge "
                                 'yard on the lip; the game reads it once the area replaces the zone'})
            stops.append({'id': 'lava', 'name': 'the forge cart bay', 'at': [2472, 4904], 'zone': 'caldera',
                          'stand': 'tunnel', 'why': "the mine cart's lower end, out of its tunnel under the rim"})
            rails.append({'id': 'mine_cart_tunnel', 'kind': 'mine cart', 'points': TUNNEL, 'tunnel': True,
                          'why': 'under the caldera rim to the cart bay; never walked'})
            rails.append({'id': 'mine_cart', 'kind': 'mine cart', 'points': [[2896, 4000]] + [p for p in rail_mine if p[1] > 4000],
                          'opens': 'after W6', 'why': 'the Lode down past the salt lake to the tunnel portal on the north flank'})
        else:
            stops.append({'id': 'west', 'name': 'Dust Gulch platform', 'at': [2904, 2336], 'zone': 'gulch',
                          'stand': 'platform', 'why': "the desert line's terminus, with a water crane and a buffer"})
            stops.append({'id': 'lode-mine-mouth', 'name': 'the Lode mine mouth', 'at': [3040, 1648],
                          'opens': 'after W6', 'why': "the mine cart's top"})
            rails.append({'id': 'desert_line', 'kind': 'railway', 'points': rail_desert, 'opens': 'W5',
                          'viaduct': [4296, 3720],
                          'why': 'from the valley halt over the Rift on its viaduct to Dust Gulch'})
            rails.append({'id': 'mine_cart', 'kind': 'mine cart', 'points': rail_mine[:-1] + [[2896, 4320]],
                          'opens': 'after W6', 'why': 'from the Lode past the salt lake toward the forge'})
        for rl in rails:
            rl['crossings'] = [{'with': r['id'], 'at': x} for r in rts for x in crossings(rl['points'], r['points'])]
            rl['crossings'] += [{'with': w['id'], 'at': x} for w in water if w.get('kind') in ('river', 'stream')
                                for x in crossings(rl['points'], w['points'])]
        residents = []
        for t in thresholds:
            for who in t['residents']:
                residents.append({'who': who, 'near': t['id'], 'at': t['at']})
        for pk in pockets:
            if pk['holds'] in ('a resident fishing', 'a hermit at a fire'):
                residents.append({'who': pk['holds'][2:], 'at': pk['at'], 'note': 'the pocket\'s resident'})
        for m in markers:
            if m['what'] == 'resident':
                residents.append({'who': f"a resident of {m['place']}", 'at': m['at']})
        clusters = [c for c in P['clusters'] if own(c['at']) and in_box(c['at'], box)]
        plan = {
            '_about': ("Sunstone Reach (the steppe west of the Brackens gap, the Rift, the Sunstone basin)"
                       if pid == 'sunstone' else "The fire country (Mount Ember, Hearthold, the forge, Cinder Springs, "
                                                 "Cinderwick, the Ash Coast)")
            + " as a plan (Claude D, lane D, 21 Oct), in Claude F's region-plan schema (scripts/art/region_plan.py, "
              "#174), written by scripts/art/regions/sunstone_plan.py from the brief "
              "docs/vision/regions/sunstone-basin-fire-country.md (v5.3) and lane G's routes. World px on the "
              "11264 x 6912 canvas. Tiers are lane G's absolute world tiers (base_tier 0), outlines in screen space "
              "on the 8 px grid in straight runs (the painter rounds the corners: eastward-edges 1.5); a tier is a "
              "32 px south face, west and east ends are side bands. Resolution-independent: the art density "
              "(about 2x, pending Matt's verdict) does not move anything here.",
            'id': pid, 'owner': 'claude-d',
            'biome': 'canyon' if pid == 'sunstone' else 'ash',
            'biomes': ['canyon', 'meadow', 'city', 'ash'] if pid == 'sunstone' else ['ash', 'canyon', 'coast', 'city', 'meadow'],
            'box': box,
            'base_tier': {'value': 0, 'provisional': False,
                          'from': f"lane G's world tiers (lib/world-routes.ts, {SNAPSHOT_AT})"},
            'faces': {
                '_about': "Each biome draws its own edges (to-all-reuse-rule) on the shared grammar (eastward-edges.md). "
                          "The cliff core's canyon set (#165) is 40 px; these plans keep lane G's 32 px tier, so the "
                          'canyon set needs a 32 px face or the tier map is read at 40 (asked of Claude A).',
                'between_tiers': {'height': 32, 'material': 'banded ochre and red slabs (canyon)' if pid == 'sunstone'
                                  else 'basalt and cinder (ash, not built yet); castle stone in Hearthold (city)'},
                'massif': {'material': 'crags', 'kit': 'cliff_core (highland family, the massif is lane F and G\'s)'},
            },
            'tiers': tiers,
            'routes': rts, 'trods': trs, 'stairs': stairs, 'water': water, 'lava': lava,
            'places': places, 'areas': areas, 'stops': stops, 'rails': rails, 'rings': rings, 'rest_spots': rest,
            'named': named, 'pockets': pockets, 'egg_spots': eggs, 'markers': markers, 'obstacles': obstacles,
            'ruins': ruins, 'set_pieces': set_pieces, 'clusters': clusters, 'edges': edges, 'thresholds': thresholds,
            'meets': meets, 'residents': residents, 'ground': GROUND,
            'overrides': OVERRIDES if pid == 'sunstone' else [],
            'open': {'asks_of_lane_g': [a for a in P['asks'] if any(in_box(_pt(a), box) for _ in (0,))],
                     'notes': OPEN_NOTES},
        }
        unplaced = [x for x in P['named'] + P['markers'] if x.get('unplaced') and own(x['at'])]
        if unplaced:
            plan['open']['unplaced'] = unplaced
        plans[pid] = plan
    return plans


def _pt(ask):
    m = re.search(r'\((\d+), (\d+)\)', ask)
    return [int(m.group(1)), int(m.group(2))]


PLACE_OF = {'Cinder Springs', 'Cinderwick', 'Dust Gulch', 'Ember forge', 'Hearthold', 'Palm Spring', 'the Lode'}

OVERRIDES = [{
    'id': 'dust-gulch-lava-distance',
    'what': "today's Dust Gulch zone: the town's head and tower stand 60 to 140 px from the Scorched Pass lava "
            '(review 21 Oct 07:53, finding 1)',
    'status': 'OVERRIDE until the continent rebuild',
    'why': 'it breaks no play (walkable; nobody stands on lava); a look-patch on an old zone is ruled out '
           '(to-all-no-old-assets, to-all-old-zone-patches); this plan puts the gulch in the desert on the Amber\'s '
           'fan, about 2400 px from the nearest lava (the old flow), so the rebuild fixes it',
    'by': 'Claude A, a-to-d-override (21 Oct 13:10)',
}]

OPEN_NOTES = [
    "The routes' long straight runs (up to 416 px on the Drover's Road) follow Matt's grid ruling (21 Oct 11:44, "
    "to-all-grid-2x); region_plan.py's check 16 (240 px) predates it.",
    "The brief puts the desert line's viaduct 'upstream' of Drover's bridge but at (4290, 3720), downstream; the "
    'plan keeps the coordinates.',
    'The fire country: v5.3 4.7 is followed (the chasm bridge crosses the old flow from the summit\'s south-west '
    "breach; the crust causeway the young flow from the south-east vent); table 5.2's 'young west flow' is read as that.",
    "Hearthold's stepped streets are laid as six terraces (9 to 13) with the routes' stairs and lane D's streets; "
    'the brief\'s 24 stairs come with the castle kit.',
    'Set pieces of the ash biome wait for its edge set in the cliff core (not built yet).',
]


def main(argv):
    R = load_routes()
    brief = parse_brief()
    T, routes, trods = build(R, brief)
    P = make_plans(T, routes, trods, R, brief)
    plans = emit(T, routes, trods, R, P)
    check = '--check' in argv
    differ = False
    written = []
    for pid, plan in plans.items():
        path = os.path.join(OUT, f'{pid}.json')
        plan = json.loads(json.dumps(plan))
        if check:
            if not os.path.exists(path) or json.load(open(path)) != plan:
                print(f'{pid}: differs from {os.path.relpath(path, ROOT)}')
                differ = True
        else:
            os.makedirs(OUT, exist_ok=True)
            with open(path, 'w') as fh:
                json.dump(plan, fh, indent=2)
                fh.write('\n')
            written.append(path)
        print(f"{pid}: {len(plan['tiers'])} tier outlines, {len(plan['routes'])} routes, {len(plan['trods'])} trods, "
              f"{len(plan['stairs'])} stairs, {len(plan['named'])} named, {len(plan['pockets'])} pockets, "
              f"{len(plan['markers'])} markers, {len(plan['set_pieces'])} set pieces, {len(plan['clusters'])} clusters")
    fmt = os.path.join(ROOT, 'node_modules', '.bin', 'oxfmt')
    if written and os.path.exists(fmt):
        # the repository's formatter (npm run format); --check compares the data, not the text
        import subprocess
        subprocess.run([fmt, '--write'] + written, cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    for a in P['asks']:
        print('ask of lane G:', a)
    if '--draw' in argv:
        out = argv[argv.index('--draw') + 1]
        os.makedirs(out, exist_ok=True)
        sys.path.insert(0, os.path.dirname(HERE))
        try:
            import region_plan as rp
            for pid, plan in plans.items():
                rp.draw(plan).save(os.path.join(out, f'{pid}.png'))
        except ImportError:
            print('region_plan.py (#174) not on this branch: no drawing')
    return 1 if differ else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
