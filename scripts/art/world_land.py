"""The land between the regions, the world's edges and the land beyond, as data (lane G).

World plan v5.3, 5.5 (Matt, 20 Oct 15:50: "make sure you hone in on the world boundaries,
they need to be excellent as well"): every edge has three layers drawn as land, never a
line: the fade (walkable ground with clumps thickening outward, 10 to 160 px), the wall
(the ground's own three blockers in uneven patches, 64 to 180 px deep) and, behind it,
the clumps thinning out again over 160 to 400 px into the border proper (the massif, the
dune sea, the fens and the old forest, the sea), drawn hazier, never walked.

This file says, for the whole 11264 x 6912 px canvas at 8 px cells, who draws each layer
and what ground it is. It is the plan; the painting comes after (edge kit, then the land).

Who draws what (crew board, 21 Oct; the region briefs' section 6 gives each region its
own edges):

  - Inside a region's footprint (or the chunk box a lane has declared), the region lane
    draws its walkable land, its fade and its wall, with its biome's own blockers.
  - Lane G draws everything outside the footprints: the walkable land between (the Lull
    plain and the coast to Gullwick, the High Fells' shoulder), the fade and wall where
    that land meets the beyond, and all of the beyond: from a lane's wall (its box edge)
    the thin-out of 160 to 400 px and the border proper to the canvas edge.
  - Where a footprint touches the canvas edge (Sunstone's west and north), the lane draws
    to its wall and lane G the beyond past it; until the lane draws its wall line, the
    provisional line in EDGES stands (the canvas edge itself is never the wall).

The walkable land between is given as polygons (PLAIN, the coast) and as corridors round
the routes where a route crosses land that is otherwise beyond (the High Fells' shoulder).
Every vertex is on the 8 px grid. Lines that should read organic on the ground (the
coast, the walls) get their wobble when painted; here they are the plan.

Run: python3 scripts/art/world_land.py (writes lib/world-land.ts; LAND_PREVIEW=<file.png>
draws the plan). The check is lib/world-land.test.ts (npm run check:world-land).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import worlds  # noqa: E402
import world_routes as wr  # noqa: E402

CELL = 8
W, H = wr.CANVAS[0] // CELL, wr.CANVAS[1] // CELL

# What a cell of lane G's land is.
KINDS = ['lane', 'land', 'fade', 'wall', 'thin', 'beyond', 'sea']
# The ground of lane G's land, by place (plan 5.5 and the region briefs' section 6).
GROUNDS = {
    'meadow': 'the Lull plain: fields, hedgerows, copses and water meadows (river_kit)',
    'coast': 'beach and dunes behind it, driftwood and marram (the coast kit)',
    'heights': 'scree, boulders and crags on the massif (the cliff core, highland)',
    'massif': "the massif's peaks, icefalls and valley glaciers, hazier (the mountain kit)",
    'old-forest': "the old forest: thicket and old trees, then the giant trees' canopy",
    'fens': 'the moss fens: meres and sinkholes, the Glint coming out of them',
    'sea': 'the sea, with far islands on the horizon',
}

# The Lull plain and the coast west of Gullwick: lane G's walkable land (plan 8, the
# brief's section 5). Bounded by the valley (west, open land), the coal hills (north,
# open), Claude I's chunk (east, open), Gullwick (south-east, open) and the coast.
PLAIN = [
    (7000, 3296), (8304, 3296), (8304, 4848), (7648, 4848), (7648, 5176),
    (7592, 5200), (7520, 5224), (7448, 5216), (7376, 5232), (7304, 5224), (7256, 5216),
    (7256, 5104), (7000, 5104),
]
# The coast's edge: the plain's south side between the Headland and Gullwick: a beach
# (fade of dune grass and driftwood, then the sea; no wall: the sea is the edge).
COAST = [(7256, 5216), (7304, 5224), (7376, 5232), (7448, 5216), (7520, 5224), (7592, 5200), (7648, 5176)]

# Corridors: walkable bands round a route where it crosses lane G's land that is otherwise
# beyond. (route, half width of the walkable band, ground of its walls).
CORRIDORS = [
    ('high-fells', 96, 'heights'),
]

# The beyond, by ground: lane G's cells outside every walkable area take the ground of the
# first region here that holds them (boxes in world px).
BEYOND = [
    ('sea', (0, 5100, 11264, 6912)),          # the south: open sea past the coasts and isles
    ('old-forest', (9300, 0, 11264, 2560)),   # the east, north part: the old forest
    ('fens', (9300, 2560, 11264, 3904)),      # the east, south part: the moss fens
    ('massif', (0, 0, 11264, 2400)),          # the north: the massif and its glaciers
    ('heights', (0, 0, 11264, 6912)),         # anything left over (the gap by the Brackens)
]

# Edges: each side of a footprint (or of lane G's land) that meets the beyond. who draws
# the fade and wall, the ground of the wall, and what is seen beyond. 'line' runs with
# the walkable side on its left as you walk it (so the beyond is on the right).
# Provisional lines (a lane has not drawn its wall) are marked.
EDGES = [
    # north: the massif
    {'id': 'sunstone-north', 'by': 'claude-d', 'line': [(0, 1504), (4800, 1504)], 'ground': 'heights',
     'beyond': "the massif's peaks; the Amber and the Willow Run coming out of their gorges",
     'provisional': True, 'why': "inside D's box: D draws its wall where the basin meets the massif; the line is a placeholder"},
    {'id': 'brackens-north', 'by': 'claude-f', 'line': [(4800, 1280), (5600, 1280)], 'ground': 'heights',
     'beyond': "the massif's front", 'provisional': False, 'why': "F's plan (brackens.json edges)"},
    {'id': 'gap-west', 'by': 'claude-f', 'line': [(5600, 1280), (5600, 2296)], 'ground': 'heights',
     'beyond': 'a spur of the massif between the Brackens and the Frostline', 'provisional': True,
     'why': "the strip x 5600-5680 between F's two boxes is lane G's: a spur, never walked"},
    {'id': 'frostline-north', 'by': 'claude-f', 'line': [(5680, 1280), (6800, 1280)], 'ground': 'heights',
     'beyond': "the massif's peaks and glaciers to the top edge", 'provisional': False,
     'why': "F's plan (frostline.json edges); F draws the massif's front inside its box (f-to-g-massif)"},
    {'id': 'shoulder', 'by': 'claude-g', 'line': None, 'ground': 'heights',
     'beyond': 'crags and icefalls above, the drop to the valley head below',
     'provisional': False, 'why': "the High Fells' corridor through lane G's land: fade and wall both sides"},
    {'id': 'coal-hills-north', 'by': 'claude-h', 'line': [(7000, 1704), (9296, 1704)], 'ground': 'heights',
     'beyond': "the massif and the upper Lull's gorge going on north", 'provisional': False,
     'why': "H's brief, section 6 (its box's north side)"},
    # east: the old forest and the fens
    {'id': 'coal-hills-east', 'by': 'claude-h', 'line': [(9296, 1704), (9296, 3296)], 'ground': 'old-forest',
     'beyond': 'the old forest, then the moss fens', 'provisional': False, 'why': "H's brief, section 6"},
    {'id': 'belt-north', 'by': 'claude-i', 'line': [(9296, 3296), (9456, 3296)], 'ground': 'old-forest',
     'beyond': 'the floodplain woods, then the old forest', 'provisional': False,
     'why': "I's brief, section 6 (north of the belt)"},
    {'id': 'belt-east', 'by': 'claude-i', 'line': [(9456, 3296), (9456, 3904)], 'ground': 'fens',
     'beyond': 'the moss fens', 'provisional': False, 'why': "I's chunk box east side north of Neon"},
    {'id': 'neon-north', 'by': 'claude-i', 'line': [(9456, 3904), (11264, 3904)], 'ground': 'fens',
     'beyond': 'the moss fens and the Glint coming out of them', 'provisional': False, 'why': "I's brief, section 6"},
    # south: the sea (no wall: the sea is the edge; surf on the shore, drawn by the shore's owner)
    {'id': 'fire-coast', 'by': 'claude-d', 'line': [(3704, 5848), (0, 5848)], 'ground': 'sea',
     'beyond': 'the sea and the drowned end of the arc', 'provisional': True,
     'why': "D's brief: the sea is the edge; D draws its shore and surf, lane G the open sea past it"},
    {'id': 'valley-coast', 'by': 'claude-e', 'line': [(6800, 5104), (5600, 5104)], 'ground': 'sea',
     'beyond': 'the sea, the isles and the rocket\'s cape', 'provisional': True, 'why': "E's brief, section 6"},
    {'id': 'plain-coast', 'by': 'claude-g', 'line': COAST[::-1], 'ground': 'coast',
     'beyond': 'the sea and the Shell Bar', 'provisional': False,
     'why': 'the plain\'s beach between the Headland and Gullwick (dunes behind the beach, plan 6.1)'},
    {'id': 'gullwick-coast', 'by': 'claude-i', 'line': [(8304, 5448), (7648, 5448)], 'ground': 'sea',
     'beyond': 'the open coast', 'provisional': True, 'why': "Gullwick's box"},
    {'id': 'neon-coast', 'by': 'claude-i', 'line': [(11264, 5896), (9800, 5896)], 'ground': 'sea',
     'beyond': 'the sea and far islands', 'provisional': True, 'why': "I's brief, section 6"},
]

# The layers' depths (plan 5.5): fade walkable 10 to 160 px, wall 64 to 180 px, the
# thin-out 160 to 400 px; each varies along its edge so no stretch is a ribbon.
FADE = (10, 160)
WALL = (64, 180)
THIN = (160, 400)


def _boxes_mask():
    """Owner index per cell: 0 for lane G, else 1 + the footprint's index."""
    own = np.zeros((H, W), np.int16)
    cy, cx = np.mgrid[0:H, 0:W] * CELL + CELL // 2      # a cell belongs where its centre is
    for i, (who, name, (x0, y0, x1, y1)) in reversed(list(enumerate(wr.FOOTPRINTS))):
        own[(cx >= x0) & (cx < x1) & (cy >= y0) & (cy < y1)] = i + 1
    return own


def _poly_mask(poly):
    from PIL import Image, ImageDraw
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([(x / CELL, y / CELL) for x, y in poly], fill=1)
    return np.asarray(im, bool)


def _route_points(rid):
    r = next(r for r in ROUTES if r['id'] == rid)
    return [(p[0], p[1]) for p in r['points']]


def _corridor_mask(rid, half):
    from PIL import Image, ImageDraw
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    pts = [(x / CELL, y / CELL) for x, y in _route_points(rid)]
    r = half / CELL
    d.line(pts, fill=1, width=int(2 * r))
    for x, y in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=1)
    return np.asarray(im, bool)


def _dist(mask, cap_cells=100):
    """Distance in px from each cell to the nearest True cell: a chamfer distance (steps of
    1 and 1.414 cells, relaxed until settled, capped at cap_cells), numpy only."""
    INF = 1e9
    d = np.where(mask, 0.0, INF)
    r2 = math.sqrt(2.0)
    for _ in range(cap_cells * 2):
        p = np.pad(d, 1, constant_values=INF)
        n = np.minimum.reduce([
            d,
            p[:-2, 1:-1] + 1, p[2:, 1:-1] + 1, p[1:-1, :-2] + 1, p[1:-1, 2:] + 1,
            p[:-2, :-2] + r2, p[:-2, 2:] + r2, p[2:, :-2] + r2, p[2:, 2:] + r2,
        ])
        if np.array_equal(n, d):
            break
        d = n
    return np.minimum(d, cap_cells + 1) * CELL


def _wobble(seed, n=4096):
    """A smooth depth factor in [0, 1] along a coordinate: no stretch is a ribbon."""
    t = np.arange(n, dtype=float)
    v = np.zeros(n)
    for k, (lam, amp) in enumerate(((600, 0.5), (260, 0.3), (110, 0.2))):
        ph = wr._hash(seed, 'wob', k) * 2 * math.pi
        v += amp * np.sin(2 * math.pi * t / lam + ph)
    return (v - v.min()) / (v.max() - v.min())


def build():
    own = _boxes_mask()
    g = own == 0
    walk = np.zeros((H, W), bool)
    plain = _poly_mask(PLAIN)
    # one cell more, so no sliver of beyond is left between the plain and a lane's box
    plain |= np.pad(plain, 1)[2:, 1:-1] | np.pad(plain, 1)[:-2, 1:-1] | np.pad(plain, 1)[1:-1, 2:] | np.pad(plain, 1)[1:-1, :-2]
    walk |= plain
    for rid, half, _ in CORRIDORS:
        walk |= _corridor_mask(rid, half)
    walk &= g
    kind = np.zeros((H, W), np.int8)   # 0 lane
    yy, xx = np.mgrid[0:H, 0:W]
    ground = np.full((H, W), -1, np.int8)
    names = list(GROUNDS)
    # the beyond's ground by place
    for gname, (x0, y0, x1, y1) in reversed(BEYOND):
        m = (xx * CELL >= x0) & (xx * CELL < x1) & (yy * CELL >= y0) & (yy * CELL < y1)
        ground[m] = names.index(gname)
    ground[walk] = names.index('meadow')
    ground[walk & _corridor_mask('high-fells', 96)] = names.index('heights')
    sea = g & (ground == names.index('sea')) & ~walk
    # distances, measured with varying depth along the edge
    d_walk = _dist(walk, (WALL[1] + THIN[1]) // CELL + 2)   # outward from lane G's walkable land
    d_lane = _dist(own > 0, THIN[1] // CELL + 2)            # outward from a lane's box (its wall)
    wob = _wobble('g-edges')
    along = ((xx * CELL + yy * CELL) // 2) % len(wob)
    fwob = wob[along]
    wall_depth = WALL[0] + (WALL[1] - WALL[0]) * fwob
    thin_depth = THIN[0] + (THIN[1] - THIN[0]) * wob[(along + 1300) % len(wob)]
    # inward from the walkable land's border: the fade (walkable)
    d_in = _dist(~walk, FADE[1] // CELL + 2)
    fade_depth = FADE[0] + (FADE[1] - FADE[0]) * wob[(along + 700) % len(wob)]
    K = {k: i for i, k in enumerate(KINDS)}
    kind[g] = K['beyond']
    # lane G's own walkable land and its fade (only where it borders the beyond, not where
    # it meets a lane's land as open ground)
    beyond_side = g & ~walk
    near_beyond = _dist(beyond_side, FADE[1] // CELL + 2) <= FADE[1] + CELL
    kind[walk] = K['land']
    kind[walk & near_beyond & (d_in <= fade_depth)] = K['fade']
    # the wall round lane G's land, then the thin-out behind it
    wall_g = beyond_side & (d_walk <= wall_depth)
    thin_g = beyond_side & (d_walk > wall_depth) & (d_walk <= wall_depth + thin_depth)
    # behind a lane's wall: the thin-out from its box edge
    thin_lane = beyond_side & (d_lane <= thin_depth) & ~wall_g
    kind[thin_g | thin_lane] = K['thin']
    kind[wall_g] = K['wall']
    # the sea: open water, no wall; the coast's beach is the plain's fade
    kind[sea & ~walk] = K['sea']
    # the wall and the thin-out under the massif are its heights (scree, boulders, crags);
    # the massif proper (peaks, icefalls, glaciers) starts behind them
    ground[((kind == K['wall']) | (kind == K['thin'])) & (ground == names.index('massif'))] = names.index('heights')
    return own, kind, ground, walk


ROUTES = None


def export(own, kind, ground, walk):
    names = list(GROUNDS)
    counts = {k: int((kind[own == 0] == i).sum()) for i, k in enumerate(KINDS) if k != 'lane'}
    by_ground = {g: int(((ground == i) & (own == 0)).sum()) for i, g in enumerate(names)}
    # run-length rows of lane G's kind and ground, for the painter and the check
    def rle_rows(a):
        rows = []
        for y in range(a.shape[0]):
            r = a[y]
            out = []
            x = 0
            while x < len(r):
                j = x
                while j + 1 < len(r) and r[j + 1] == r[x]:
                    j += 1
                out.append(f'{int(r[x]) + 1}x{j - x + 1}' if j > x else f'{int(r[x]) + 1}')
                x = j + 1
            rows.append('.'.join(out))
        return rows
    body = {
        'cell': CELL, 'size': [W, H], 'kinds': KINDS, 'grounds': names,
        'groundsAbout': GROUNDS,
        'plain': [list(p) for p in PLAIN], 'coast': [list(p) for p in COAST],
        'corridors': [{'route': r, 'half': h, 'ground': g} for r, h, g in CORRIDORS],
        'edges': [{**e, 'line': [list(p) for p in e['line']] if e['line'] else None} for e in EDGES],
        'layers': {'fade': list(FADE), 'wall': list(WALL), 'thin': list(THIN)},
        'cells': counts, 'groundCells': by_ground,
        'kindRows': rle_rows(kind), 'groundRows': rle_rows(ground),
    }
    js = lambda v: json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    lines = [
        '/**',
        " * The land between the regions, the world's edges and the land beyond: who draws",
        ' * each layer and what ground it is (lane G). Generated by scripts/art/world_land.py;',
        ' * do not edit by hand. Cells are 8 px on the v5.3 canvas. Rows are run-length:',
        " * 'v' or 'vxN' (value v, N times), joined by '.', where v - 1 indexes kinds or",
        ' * grounds (0 for a lane\'s cell in groundRows). Not read by the game yet.',
        ' */',
        '',
        'export interface LandEdge { id: string; by: string; line: [number, number][] | null; ground: string; beyond: string; provisional: boolean; why: string }',
        f'export const worldLand = {js(body)};',
        '',
    ]
    path = os.path.join(worlds.ROOT, 'lib', 'world-land.ts')
    with open(path, 'w') as f:
        f.write('\n'.join(lines))
    try:
        subprocess.run(['npx', 'oxfmt', '--write', path], cwd=worlds.ROOT, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print('world_land: oxfmt skipped:', e)
    return counts


def preview(own, kind, ground, path):
    from PIL import Image, ImageDraw
    colours = {
        'meadow': (120, 160, 70), 'coast': (215, 196, 140), 'heights': (130, 120, 110),
        'massif': (190, 200, 215), 'old-forest': (40, 75, 50), 'fens': (90, 110, 80), 'sea': (50, 90, 140),
    }
    names = list(GROUNDS)
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (24, 26, 34)
    lane_cols = {'claude-c': (40, 70, 80), 'claude-d': (90, 70, 40), 'claude-e': (50, 80, 45),
                 'claude-f': (85, 90, 110), 'claude-h': (75, 55, 45), 'claude-i': (50, 60, 100)}
    for i, (who, _, _) in enumerate(wr.FOOTPRINTS):
        img[own == i + 1] = lane_cols[who]
    K = {k: i for i, k in enumerate(KINDS)}
    for gi, gname in enumerate(names):
        base = np.array(colours[gname])
        for k, f in (('land', 1.0), ('fade', 0.85), ('wall', 0.55), ('thin', 0.75), ('beyond', 0.95), ('sea', 1.0)):
            m = (own == 0) & (ground == gi) & (kind == K[k])
            c = base * f if k != 'beyond' else base * 0.6 + np.array((120, 120, 130)) * 0.4
            img[m] = np.clip(c, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    for r in ROUTES:
        d.line([(p[0] / CELL, p[1] / CELL) for p in r['points']], fill=(240, 220, 120), width=1)
    for e in EDGES:
        if e['line']:
            col = (255, 120, 120) if e['provisional'] else (255, 255, 255)
            d.line([(x / CELL, y / CELL) for x, y in e['line']], fill=col, width=1)
    im.save(path)


def main():
    global ROUTES
    ROUTES, _ = wr.build()
    own, kind, ground, walk = build()
    counts = export(own, kind, ground, walk)
    if os.environ.get('LAND_PREVIEW'):
        preview(own, kind, ground, os.environ['LAND_PREVIEW'])
    print('world_land:', ', '.join(f'{k} {v}' for k, v in counts.items()), 'cells of lane G')


if __name__ == '__main__':
    main()
