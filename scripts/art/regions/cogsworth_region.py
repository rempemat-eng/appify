"""Cogsworth's region outside the town: the land's tiers, its water, the routes laid on it and
the set pieces placed on it, as data in world px (resolution independent).

Lane H (Claude H). Matt, 21 Oct (crew board to-all-density): the art moves to a higher
density after a pilot, so until the verdict the lanes work on what carries over unchanged:
layout and composition, routes and thresholds, walk masks, set-piece placement as data, prop
logic. And 11:44 (to-all-grid-2x): outlines follow the cell grid in straight runs along x
or y with rounded corners, direction changes at cell boundaries; the detail lives inside the
shape, not in a meandering outline. This module is that layout for the region the brief
gives lane H (docs/vision/regions/cogsworth-coal-hills-narrows.md): the coal hills, the
Narrows gorge and its viaduct, Fernhollow, the Cog above and below the town, and the
named things, spoil heaps and camps along Claude G's routes. The town inside its box is
cogsworth_plan.py's.

What it holds, on the world's 8 px cells over the footprint (x 7000 to 9304, y 1700 to
3304):

- TIERS: the land's tops as rectangles on the grid, painted lowest first (a tier is a 32 px
  south face; G's tier numbers: the town's street is 7, the Cog in town 6). The massif's
  benches step down to the south-east where the High Fells come down; the Fern hills'
  shoulder carries the Foothill Road over tier 9; the coal hills rise east of the town to
  the Narrows' rims; the Cog's valley and the confluence lie low.
- WATER: the Cog above the town and below it to the confluence, the Lull through the Narrows
  and on south-east, the eel pond at Fernhollow; each a course of cells at its own tier,
  cut into the land (a cut's sides are faces where the land is higher to the north, side
  bands to the west and east).
- ROUTES: Claude G's lines (lib/world-routes.ts, #175), read when the file is there, with a
  copy of their vertices on lane H's land (ROUTES_FALLBACK, from #175 @ef8824f) otherwise;
  each is laid at its tier, so the land under it agrees with it.
- SET PIECES: the named things with the prop or kit piece each needs and its footprint, the
  spoil heaps, the viaduct's piers, Fernhollow's cottages, sawpit and log stores, each a
  footprint of cells it blocks.

`check()` holds it to what a layout can show: every route vertex on land of its own tier
(within a tier-change's run), no route on water except at its crossings, no set piece on a
route, on water or in the town box, each named thing within 64 px of its route, the
gorge's water continuous from the footprint's north edge to the confluence, Fernhollow's
doors on its road, the town's gates on the tiers G gives them. `preview()` draws it.

    python3 scripts/art/regions/cogsworth_region.py --check
    python3 scripts/art/regions/cogsworth_region.py [OUT_DIR]
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cogsworth_plan as plan  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CELL = 8
X0, Y0 = 7000, 1696
W, H = 2304, 1608                         # the footprint on the grid (x 7000 to 9304, y 1696 to 3304)
COLS, ROWS = W // CELL, H // CELL
TOWN_TIER = {0: 6, 1: 6, 2: 7, 3: 8}      # the town plan's local tiers on the world's (the canal is half a tier)

# --- the land's tops (world px rectangles, x0, y0, x1, y1), lowest first ------------------------
BASE_TIER = 5
TIERS = [
    # the Cog's valley and everything above the confluence's lowland
    (6, [(7000, 1696, 9304, 3008), (7000, 3008, 8480, 3304)]),
    # the plain's shelf west of the confluence and the hills' foot
    (7, [(7000, 1696, 9304, 2920), (7000, 2920, 8432, 3304)]),
    # the massif's foot across the north, the coal hills east of the town, the forest interior
    # between the Foothill Road and the High Fells, the Fern hills' shoulder
    (8, [(7000, 1696, 9304, 2008), (8336, 2008, 9304, 2808), (7000, 2008, 7616, 2768), (7104, 2768, 7592, 3304)]),
    (9, [(7000, 1696, 7608, 1920), (7000, 1696, 9304, 1784), (7232, 2904, 7504, 3112), (8400, 2008, 9304, 2752)]),
    (10, [(7000, 1696, 7480, 1864), (7000, 1696, 9304, 1736), (8560, 2072, 9304, 2688)]),
    (11, [(7000, 1696, 7408, 1816)]),
    (12, [(7000, 1696, 7360, 1760)]),
    (13, [(7000, 1696, 7288, 1744)]),
]

# --- water: (id, tier, course of world px points, width) ------------------------------------------
WATER = [
    ('cog-upper', 6, [(7664, 1696), (7664, 1968)], 56),          # off the massif into the town's west side
    ('cog-lower', 5, [(8328, 2904), (8368, 2904), (8368, 3064), (8560, 3064)], 48),
    ('lull-narrows', 4, [(9128, 1696), (9128, 2168), (9064, 2168), (9064, 2328), (9032, 2328), (9032, 2576),
                         (8984, 2576), (8984, 2896), (8888, 2896), (8888, 2992), (8616, 2992), (8616, 3064), (8560, 3064)], 44),
    ('lull-below', 4, [(8560, 3064), (8560, 3120), (8800, 3120), (8800, 3200), (9064, 3200), (9064, 3304)], 72),
    ('eel-pond', 7, [(7040, 3256), (7072, 3256)], 32),
]
GORGE_RIM = 2         # tiers of wall each side of the Lull's cut stand at least this high

# --- the routes on lane H's land (G's #175 @ef8824f, vertices [x, y, width, tier]) ---------------
ROUTES_FALLBACK = {
    'High Fells': [(7232, 1712, 32, 13), (7264, 1728, 32, 13), (7328, 1728, 32, 12), (7360, 1760, 32, 11),
                   (7360, 1816, 32, 11), (7424, 1816, 24, 10), (7480, 1816, 32, 10), (7480, 1880, 32, 9),
                   (7512, 1888, 24, 9), (7576, 1888, 32, 9), (7608, 1920, 32, 8), (7640, 1928, 24, 8),
                   (7672, 1944, 32, 8), (7736, 1944, 24, 8), (7800, 1944, 32, 8), (7824, 1968, 40, 8)],
    'Foothill Road': [(7024, 3192, 48, 7), (7088, 3192, 40, 7), (7136, 3192, 48, 8), (7136, 3144, 48, 8),
                      (7200, 3144, 48, 8), (7232, 3112, 40, 9), (7264, 3080, 48, 9), (7312, 3080, 48, 9),
                      (7312, 3024, 48, 9), (7376, 3024, 40, 9), (7416, 3024, 48, 9), (7416, 2960, 48, 9),
                      (7480, 2960, 48, 9), (7496, 2928, 48, 9), (7496, 2880, 48, 8), (7560, 2880, 48, 8),
                      (7560, 2816, 48, 8), (7592, 2792, 40, 8), (7616, 2760, 40, 7), (7648, 2736, 56, 7),
                      (7712, 2736, 56, 7)],
    'Towpath': [(8328, 2840, 48, 7), (8392, 2840, 40, 7), (8408, 2872, 40, 7), (8408, 2920, 40, 7),
                (8464, 2920, 40, 6), (8464, 2984, 40, 6), (8496, 3016, 32, 5), (8528, 3048, 48, 5),
                (8528, 3112, 40, 5), (8496, 3144, 32, 5), (8480, 3176, 40, 5), (8480, 3240, 32, 5)],
}
CROSSINGS = {'Foothill Road': [(7664, 2736, 80)], 'Towpath': [(8528, 3064, 64)],
             'High Fells': [(7680, 1944, 64)]}   # the High Fells' Cog bridge (W3): asked G to add it (h-to-g-1130)
TIER_CHANGE_RUN = 64  # route px either side of a change where its tier may be either


def load_routes():
    """G's routes on this land: from lib/world-routes.ts when it is in the tree (read with
    node, as world_audit reads generated data), else the copy above."""
    path = os.path.join(ROOT, 'lib', 'world-routes.ts')
    if os.path.exists(path):
        try:
            import subprocess
            code = ("const m = await import('file://' + process.argv[1]); const d = m.worldRoutes ?? m.default?.worldRoutes;"
                    "process.stdout.write(JSON.stringify(d));")
            r = subprocess.run(['node', '--import', 'tsx', '--input-type=module', '-e', code, path],
                               cwd=ROOT, capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and r.stdout:
                out, cross = {}, {}
                for rt in json.loads(r.stdout):
                    if rt['name'] in ROUTES_FALLBACK:
                        out[rt['name']] = [tuple(p) for p in rt['points']]
                        cross[rt['name']] = [(c['at'][0], c['at'][1], c['span']) for c in rt['crossings']]
                if out:
                    return out, cross, 'lib/world-routes.ts'
        except Exception:  # noqa: BLE001 (the copy stands in when node or tsx is missing)
            pass
    return ROUTES_FALLBACK, CROSSINGS, '#175 @ef8824f (copy)'


# --- set pieces: (id, what, prop or kit piece, rect of cells it stands on, world px) ----------------
SET_PIECES = [
    # named things (brief 5), each beside or a short way off its route
    ('burners-camp', 'charcoal burners\' camp', 'charcoal_clamp, burners_hut, cordwood (B #163)', (7464, 2800, 7528, 2848)),
    ('collapsed-adit', 'collapsed adit', 'a face piece of the cliff core', (7400, 2880, 7432, 2904)),
    ('pit-head', 'pit head', 'pit_head (B #163)', (7256, 2936, 7304, 2992)),
    ('windmill', 'windmill', 'windmill (B #172)', (7144, 3232, 7192, 3280)),
    ('loops-view', 'a terrace edge over the loops', 'a bench at the shoulder\'s south rim', (7344, 3096, 7376, 3112)),
    ('eel-camp', 'an eel-catcher\'s camp', 'traps, a smoking rack, a tarp (B queue)', (7088, 3240, 7128, 3272)),
    ('tor', 'a tor', 'a set piece of the cliff core\'s highland rock', (7248, 1768, 7296, 1808)),
    ('climbers-camp', 'fallen climber\'s camp', 'a tarp, a rope, a cold fire (B queue)', (7320, 1880, 7360, 1912)),
    ('echo-cave', 'echo cave', 'a face piece of the cliff core', (7576, 1840, 7616, 1864)),
    ('cairn', 'cairn', 'cairn (B, REWORK)', (7984, 1912, 8008, 1936)),
    ('crow-roost', 'a crow roost in a dead pine', 'a dead pine (forest kit) with crows', (7848, 1896, 7880, 1928)),
    ('rail-ruin', 'rail ruin', 'rails, sleepers, a tipped wagon (B queue)', (8448, 2720, 8512, 2752)),
    ('tram-tipple', 'tram tipple', 'tram_tipple (B #163)', (8344, 2768, 8392, 2808)),
    ('narrows-lookout', 'lookout over the Narrows', 'narrows_lookout (B #163)', (8536, 2960, 8568, 2992)),
    # spoil heaps (brief 2), one with the loop round it above the town
    ('spoil-1', 'spoil heap', 'a heap of shale and coal waste, its foot spread', (7512, 2232, 7608, 2296)),
    ('spoil-2', 'spoil heap (the loop)', 'the spoil heap the loop goes round', (8136, 1904, 8232, 1960)),
    ('spoil-3', 'spoil heap', 'below the riverside, by the tipple', (8392, 3104, 8456, 3144)),
    ('spoil-4', 'spoil heap', 'on the Cog\'s west bank', (7512, 2104, 7600, 2160)),
    ('spoil-5', 'spoil heap', 'on the coal hills', (8360, 2264, 8448, 2320)),
    # the Narrows Viaduct's piers, standing on the gorge's walls and its floor (rail only)
    ('viaduct-pier-w', 'viaduct pier', "the viaduct's piers (B, P4)", (8984, 2312, 9000, 2344)),
    ('viaduct-pier-m', 'viaduct pier', "the viaduct's piers (B, P4)", (9040, 2312, 9056, 2344)),
    ('viaduct-pier-e', 'viaduct pier', "the viaduct's piers (B, P4)", (9096, 2312, 9112, 2344)),
    # Fernhollow: woodcutters' cottages along the Foothill Road, the sawpit and the log stores
    ('fern-cottage-1', 'timber cottage', 'house kits: valley timber front', (7136, 3056, 7184, 3112)),
    ('fern-cottage-2', 'timber cottage', 'house kits: valley timber front', (7208, 3000, 7272, 3048)),
    ('fern-cottage-3', 'timber cottage', 'house kits: valley timber front', (7056, 3112, 7104, 3168)),
    ('fern-sawpit', 'sawpit', 'a pit with its trestle, a log on it, sawdust (B queue)', (7344, 2952, 7384, 2984)),
    ('fern-logs', 'log stores', 'log_store from the house kits, three stacks', (7448, 3048, 7496, 3080)),
]
# The land's cover and its edges in layers (brief 6): (kind, what stands there, rect).
# 'wall': the biome's three blockers in uneven patches, unwalkable; 'fade': walkable ground
# with clumps thickening toward the wall; 'wood': the coal forest's dark conifers, walkable
# under them only where a path runs. G draws what lies beyond the footprint.
COVER = [
    ('wall', 'scree, boulders and crags (the massif)', (7000, 1696, 7208, 1736)),
    ('wall', 'scree, boulders and crags (the massif)', (7376, 1696, 9304, 1736)),   # the High Fells come in between, along the bench
    ('fade', 'scree thinning among heather', (7000, 1736, 9304, 1784)),
    ('wall', 'bramble, fallen trees, then thicket and old trees (the old forest)', (9208, 1784, 9304, 3304)),
    ('fade', 'bramble and birch scrub', (9160, 1784, 9208, 3304)),
    ('wood', 'dark conifers and felled timber (the coal forest)', (7000, 2008, 7480, 2744)),
    ('wood', 'dark conifers on the coal hills', (8616, 1784, 8984, 2552)),
    ('wood', 'conifers on the hills north of the town', (7712, 1784, 8336, 1904)),
    ('wood', "the Fern hills' wet woods round Fernhollow", (7000, 2744, 7104, 3152)),
]
DOORS = {   # Fernhollow's doors: (piece, door x, door y) on the cottage's foot
    'fern-cottage-1': (7160, 3112), 'fern-cottage-2': (7240, 3048), 'fern-cottage-3': (7080, 3168),
}
NEAR = {    # named thing -> its route (brief 5)
    'burners-camp': 'Foothill Road', 'collapsed-adit': 'Foothill Road', 'pit-head': 'Foothill Road',
    'windmill': 'Foothill Road', 'loops-view': 'Foothill Road', 'eel-camp': 'Foothill Road',
    'tor': 'High Fells', 'climbers-camp': 'High Fells', 'echo-cave': 'High Fells', 'cairn': 'High Fells',
    'crow-roost': 'High Fells', 'rail-ruin': 'Towpath', 'tram-tipple': 'Towpath', 'narrows-lookout': 'Towpath',
}
NEAR_PX = {'beside': 96, 'off': 240}   # Manhattan px from the nearest vertex (vertices every 32 px)


# --- rasterizing ---------------------------------------------------------------------------
def _cells(rect):
    x0, y0, x1, y1 = rect
    c0, r0 = max(0, (x0 - X0) // CELL), max(0, (y0 - Y0) // CELL)
    c1, r1 = min(COLS, -(-(x1 - X0) // CELL)), min(ROWS, -(-(y1 - Y0) // CELL))
    return slice(r0, r1), slice(c0, c1)


def _course(points, width):
    """The cells a course covers at a width: a square of the width stamped every 4 px along
    each run (a 45 degree step between two runs stays a step, not a box)."""
    m = np.zeros((ROWS, COLS), bool)
    hw = width // 2
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        n = max(1, int(max(abs(bx - ax), abs(by - ay)) // 4))
        for i in range(n + 1):
            x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            m[_cells((int(x - hw), int(y - hw), int(x + hw), int(y + hw)))] = True
    return m


def land():
    """The region at 8 px cells: tier (int), water (bool), route (route name or ''), town box."""
    tier = np.full((ROWS, COLS), BASE_TIER, int)
    for t, rects in TIERS:
        for r in rects:
            tier[_cells(r)] = t
    # the town: its plan's tiers on the world's
    T = plan.rasterize()['tier']                         # 4 px cells
    tx, ty = plan.TOWN_ORIGIN
    town = np.zeros((ROWS, COLS), bool)
    town[_cells((tx, ty, tx + plan.TOWN_W, ty + plan.TOWN_H))] = True
    t8 = T[::2, ::2]
    r0, c0 = (ty - Y0) // CELL, (tx - X0) // CELL
    sub = tier[r0:r0 + t8.shape[0], c0:c0 + t8.shape[1]]
    sub[:] = np.vectorize(lambda v: TOWN_TIER.get(int(v), 7))(t8[:sub.shape[0], :sub.shape[1]])
    # water cut into the land at its tier; the Lull's gorge keeps its walls standing
    water = np.zeros((ROWS, COLS), bool)
    for wid, t, pts, width in WATER:
        m = _course(pts, width) & ~town
        tier[m] = t
        water |= m
    routes, crossings, source = load_routes()
    route = np.full((ROWS, COLS), '', object)
    for name, pts in routes.items():
        for (ax, ay, aw, at), (bx, by, bw, bt) in zip(pts[:-1], pts[1:]):
            m = _course([(ax, ay), (bx, by)], max(aw, bw)) & ~town
            route[m & (route == '')] = name
    return dict(tier=tier, water=water, town=town, route=route, routes=routes, crossings=crossings, source=source)


def check(L=None, verbose=True) -> list:
    L = L or land()
    faults, notes = [], []
    tier, water, town, route = L['tier'], L['water'], L['town'], L['route']

    def cell(x, y):
        return (y - Y0) // CELL, (x - X0) // CELL

    def inside(x, y):
        return X0 <= x < X0 + W and Y0 <= y < Y0 + H
    for t, rects in TIERS:
        for (x0, y0, x1, y1) in rects:
            if any(v % CELL for v in (x0, y0, x1, y1)):
                faults.append(f'tier {t}: rect {(x0, y0, x1, y1)} is off the grid')
    # each route vertex on land of its own tier (or within a tier change's run), not on water
    for name, pts in L['routes'].items():
        cross = L['crossings'].get(name, [])
        ch = [i for i in range(1, len(pts)) if pts[i][3] != pts[i - 1][3]]
        for i, (x, y, w, t) in enumerate(pts):
            if not inside(x, y):
                continue
            r, c = cell(x, y)
            if town[r, c]:
                continue
            near_change = any(abs(x - pts[j][0]) + abs(y - pts[j][1]) <= TIER_CHANGE_RUN for j in ch)
            on_bridge = any(abs(x - cx) + abs(y - cy) <= span for cx, cy, span in cross)
            if water[r, c] and not on_bridge:
                faults.append(f'{name}: vertex {(x, y)} stands on water')
            if tier[r, c] != t and not near_change and not on_bridge:
                faults.append(f'{name}: vertex {(x, y)} at tier {t} on land of tier {tier[r, c]}')
    # set pieces: on the grid, on land, off routes, out of the town and on the land's top
    blocks = np.zeros(tier.shape, bool)
    for pid, what, piece, rect in SET_PIECES:
        sl = _cells(rect)
        if any(v % CELL for v in rect):
            faults.append(f'{pid}: rect {rect} is off the grid')
        if water[sl].any() and 'pier' not in pid:
            faults.append(f'{pid}: stands in water')
        if (route[sl] != '').any():
            faults.append(f'{pid}: stands on {sorted(set(route[sl][route[sl] != ""]))[0]}')
        if town[sl].any():
            faults.append(f'{pid}: inside the town box')
        if blocks[sl].any():
            faults.append(f'{pid}: overlaps another set piece')
        blocks[sl] = True
        if len(set(tier[sl].ravel().tolist())) > 1 and 'pier' not in pid:
            notes.append(f'{pid}: stands across a tier edge {sorted(set(tier[sl].ravel().tolist()))}')
    # cover: a wall or a wood never closes a route (a path runs on through a wood)
    for kind, what, rect in COVER:
        sl = _cells(rect)
        if any(v % CELL for v in rect):
            faults.append(f'cover {what}: rect {rect} is off the grid')
        if kind == 'wall' and (route[sl] != '').any():
            faults.append(f'a wall ({what}) stands across a route')
    # named things within reach of their route
    for pid, rname in NEAR.items():
        rect = {p[0]: p[3] for p in SET_PIECES}[pid]
        cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
        pts = L['routes'].get(rname, [])
        d = min((abs(cx - x) + abs(cy - y) for x, y, *_ in pts), default=1e9)
        where = 'off' if pid in ('collapsed-adit', 'climbers-camp', 'cairn', 'rail-ruin', 'crow-roost') else 'beside'
        if d > NEAR_PX[where]:
            faults.append(f'{pid}: {d:.0f} px from the {rname} ({where} the path: {NEAR_PX[where]} px at most)')
    # Fernhollow's doors open onto the road (a cell of route within 24 px below the door)
    for pid, (dx, dy) in DOORS.items():
        r, c = cell(dx, dy)
        below = route[r:r + 4, c - 1:c + 2]
        if not (below != '').any():
            notes.append(f'{pid}: its door at {(dx, dy)} needs a path to the road (a garden path, drawn with the hamlet)')
    # the gorge's water runs on from the north edge to the confluence
    lull = _course(WATER[2][2], WATER[2][3])
    if not lull[0].any() or not lull[cell(8560, 3064)]:
        faults.append('the Lull does not run from the north edge to the confluence')
    # the town's gates sit on the tiers G gives them
    for g, (gx, gy), e in plan.TOWN_GATES:
        wx, wy = plan.TOWN_ORIGIN[0] + min(gx, plan.TOWN_W - 1), plan.TOWN_ORIGIN[1] + min(gy, plan.TOWN_H - 1)
        r, c = cell(wx, wy)
        want = {'High Fells': 8, 'Foothill Road': 7, 'Towpath': 7}[g]
        got = tier[min(r, ROWS - 1), min(c, COLS - 1)]
        if got != want:
            faults.append(f'the {g} gate at {(wx, wy)} is on tier {got} (G gives {want})')
    if verbose:
        print(f'cogsworth region: {COLS} x {ROWS} cells; routes from {L["source"]}; '
              f'{len(SET_PIECES)} set pieces; tiers {tier.min()} to {tier.max()}')
        for n in notes:
            print('  note:', n)
        for f in faults:
            print('  FAULT:', f)
        print('cogsworth region:', 'ok' if not faults else f'{len(faults)} fault(s)')
    return faults


def preview(L=None, scale=0.5):
    """The region in its tiers (darker lower), water, routes, the town and the set pieces."""
    L = L or land()
    t = L['tier']
    lo, hi = t.min(), t.max()
    v = ((t - lo) / max(1, hi - lo))
    img = np.zeros((ROWS, COLS, 3), np.uint8)
    img[..., 0] = (70 + 110 * v).astype(np.uint8)
    img[..., 1] = (90 + 100 * v).astype(np.uint8)
    img[..., 2] = (60 + 60 * v).astype(np.uint8)
    face = np.zeros(t.shape, bool)
    face[1:] = t[:-1] > t[1:]
    img[face] = (img[face] * 0.45).astype(np.uint8)
    img[L['water']] = (60, 110, 170)
    img[L['route'] != ''] = (214, 190, 140)
    img[L['town'] & (L['route'] == '')] = (img[L['town'] & (L['route'] == '')] * 0.8 + np.array([60, 20, 20])).astype(np.uint8)
    k = CELL * scale
    pic = Image.fromarray(img).resize((int(COLS * k), int(ROWS * k)), Image.NEAREST)
    d = ImageDraw.Draw(pic)
    for kind, what, (x0, y0, x1, y1) in COVER:
        col = {'wall': (60, 50, 50), 'fade': (140, 120, 90), 'wood': (30, 70, 40)}[kind]
        d.rectangle(((x0 - X0) * scale, (y0 - Y0) * scale, (x1 - X0) * scale - 1, (y1 - Y0) * scale - 1), outline=col, width=2)
    for pid, what, piece, (x0, y0, x1, y1) in SET_PIECES:
        box = ((x0 - X0) * scale, (y0 - Y0) * scale, (x1 - X0) * scale - 1, (y1 - Y0) * scale - 1)
        d.rectangle(box, outline=(255, 220, 80), fill=(120, 60, 40) if 'spoil' in pid else None)
        if 'spoil' not in pid and 'pier' not in pid:
            d.text((box[2] + 2, box[1]), pid, fill=(255, 245, 210))
    for tt in range(lo, hi + 1):
        ys, xs = np.nonzero(t == tt)
        if len(ys):
            i = len(ys) // 2
            d.text((xs[i] * k, ys[i] * k), str(tt), fill=(255, 255, 255))
    return pic


def main(argv):
    if '--check' in argv:
        sys.exit(1 if check() else 0)
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-cogsworth-region')
    os.makedirs(out, exist_ok=True)
    L = land()
    preview(L).save(os.path.join(out, 'region-half.png'))
    print('wrote', out)
    sys.exit(1 if check(L) else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
