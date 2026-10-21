"""The Lull belt, Lullford and the delta, painted as one chunk of the world canvas (Claude I).

From the region plan (scripts/art/regions/neon_delta.json, built from the brief
docs/vision/regions/neon-harbour-delta.md, world plan v5.3) with the house kits: the river
and meadow kit (river_kit.py: pasture, hay meadow, sand, reeds, willows, tracks, hedgerows,
bank faces, coping) and the house kits (house_kits.py: the valley's cottage fronts for
Lullford). Nothing in the game reads this chunk yet: world_canvas.build_all builds only
today's zone regions at their placeholder origins, so the chunk is painted standalone at its
v5.3 world origin and audited directly (`--audit`), and is registered with the build once
non-zone chunks can enter it.

The soft grid (docs/vision/eastward-edges.md, world-audit.md). Everything that decides where
you can walk is laid out on the 8 px grid: water, reed beds, carr and hedges block in whole
cells, and every boundary between kinds of ground runs at least 16 px before it steps
(`soft_snap`), so a curve is a staircase of runs two cells or longer and every long run lies
on an 8 px line. The drawing sits on that layout and softens it: rounded outer corners
(radius 2 to 3), chamfered inner corners, a rim that wobbles 1 px, a turf lip a tone darker,
a dark under-lip and foot on north banks, a light waterline under still water. Layout on the
grid, never in the texture (eastward-edges 1.3).

Run:
    python3 scripts/art/regions/lull_delta.py [OUT_DIR]          paint, write previews
    python3 scripts/art/regions/lull_delta.py --audit [OUT_DIR]  paint, then the world audit's
                                                                checks on the chunk
    python3 scripts/art/regions/lull_delta.py --check            the plan's own checks only
OUT_DIR defaults to napattack-lull-delta in the system temp folder (never the repository).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(ART, '..', '..'))
sys.path.insert(0, ART)
import river_kit as rk  # noqa: E402
from river_kit import IDX, Plot, dilate, erode, shift, hash01, fbm, vnoise  # noqa: E402

PLAN_PATH = os.path.join(ROOT, 'art', 'regions', 'lull-delta.json')
BRIEF_PATH = os.path.join(HERE, 'neon_delta.json')
GRID = 8


def load_plan(path: str = PLAN_PATH) -> dict:
    """The chunk's plan (art/regions/lull-delta.json, Claude F's region-plan schema) read into
    what the painter uses: the box, the water by id (the delta's arms together), every route
    and trod by id, Lullford's town and bridge."""
    with open(path) as f:
        P = json.load(f)
    W = {w['id']: w for w in P['water']}
    W['delta_arms'] = {'arms': [dict(w, id=w['id'][4:]) for w in P['water'] if w['kind'] == 'distributary']}
    sea = W['sea']
    W['sea'] = dict(sea, front=sea['points'][:-2])
    places = {p['id']: p for p in P['places']}
    town, br = places['lullford'], places['lullford_bridge']
    y = br['at'][1]
    return dict(P, plan=P, water=W, chunks={'lull-delta': {'box': P['box']}},
                routes={r['id']: r for r in P['routes'] + P['trods']},
                lullford={'town': {'rect': town['rect']},
                          'bridge': {'from': [br['span'][0], y], 'to': [br['span'][1], y], 'deck': 24,
                                     'island': br['island']}})


# --- working in windows (the kit's pieces allocate whole-canvas arrays; a chunk is millions of px) --

def window(p: Plot, x0: int, y0: int, x1: int, y1: int) -> Plot:
    """A view of part of a plot: the kit's pieces paint into it and the plot changes with it.
    Coordinates (p.x, p.y) stay the plot's own, so noise and hashes run on across windows."""
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(p.w, x1), min(p.h, y1)
    q = Plot.__new__(Plot)
    q.w, q.h = x1 - x0, y1 - y0
    for a in ('f', 't', 'wet', 'solid', 'walk', 'crossing', 'x', 'y'):
        setattr(q, a, getattr(p, a)[y0:y1, x0:x1])
    q.origin = (x0, y0)
    return q


def tiled(p: Plot, fn, m, *args, size=256, **kw):
    """Run a kit piece fn(plot, mask, ...) over the plot window by window."""
    m = np.asarray(m, bool)
    for y0 in range(0, p.h, size):
        for x0 in range(0, p.w, size):
            sub = m[y0:y0 + size, x0:x0 + size]
            if sub.any():
                fn(window(p, x0, y0, x0 + size, y0 + size), sub, *args, **kw)


def paste(p: Plot, sp, x, y, outline=True, shadow=None, block=None):
    """river_kit.paste in a window round the sprite (same result, a fraction of the work)."""
    x0, y0 = x - sp.fx - 3, y - sp.fy - 3
    q = window(p, x0, y0, x0 + sp.w + 6, y0 + sp.h + 6)
    if q.w <= 0 or q.h <= 0:
        return
    qx, qy = q.origin
    rk.paste(q, sp, x - qx, y - qy, outline=outline, shadow=shadow, block=block)


# --- the soft grid ----------------------------------------------------------------------------

def soft_snap(m: np.ndarray, cell: int = 2 * GRID) -> np.ndarray:
    """A mask laid out on the soft grid: decided per `cell` px (two 8 px grid cells) by
    majority, so every edge lies on an 8 px line and every boundary runs at least two grid
    cells (16 px) before it steps: a curve becomes a staircase of runs two cells or longer,
    as the audit's grid checks want (world-audit.md, `grid-edges`, `rim-on-grid`). Tried
    first: 8 px cells with the one-cell runs repaired cell by cell, which ate whole reaches
    of river where repairs cascaded; whole 16 px cells cannot leave a short run."""
    h, w = m.shape
    H, W = -(-h // cell), -(-w // cell)
    pad = np.zeros((H * cell, W * cell), bool)
    pad[:h, :w] = m
    c = pad.reshape(H, cell, W, cell).mean((1, 3)) >= 0.5
    return np.repeat(np.repeat(c, cell, 0), cell, 1)[:h, :w]


def _runs_1d(b: np.ndarray):
    """(row, start, length) of every run of True along the last axis."""
    out = []
    for r in range(b.shape[0]):
        row = np.concatenate([[False], b[r], [False]])
        d = np.diff(row.astype(np.int8))
        st, en = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        out += [(r, a, e - a) for a, e in zip(st.tolist(), en.tolist())]
    return out


def jog(m: np.ndarray, cell: int = 2 * GRID, longest: int = 6, passes: int = 6) -> np.ndarray:
    """No straight edge longer than `longest` cells (96 px; benchmark check 8, the audit's
    straight-run): in the middle of every longer run of a grid-laid mask's edge, one cell
    is given back to the other side, a 16 px jog, as a bank, a reed bed or a wood edge
    would wander."""
    h, w = m.shape
    c = m[::cell, ::cell].copy()
    for _ in range(passes):
        hit = False
        for axis in (0, 1):
            a = c if axis == 0 else c.T
            b = a[:-1] != a[1:]
            for r, st, ln in _runs_1d(b):
                if ln <= longest:
                    continue
                hit = True
                for k in range(st + ln // 2, st + ln - 1, longest)[:1] or [st + ln // 2]:
                    # give back the cell on the True side, so the mask only shrinks
                    if a[r, k]:
                        a[r, k] = False
                    else:
                        a[r + 1, k] = False
        if not hit:
            break
    return np.repeat(np.repeat(c, cell, 0), cell, 1)[:h, :w]


def bands(m: np.ndarray, cell: int = 2 * GRID, open_land: np.ndarray | None = None) -> np.ndarray:
    """Blocked ground the audit would read as a face of a height the soft grid does not have
    (a band 48 or 64 px tall with walkable ground above and below: world-audit `face-height`
    allows 12, 16, 32 and 40): such a band is carried down to 80 px where the land below is
    free, else cut back to 32."""
    h, w = m.shape
    c = m[::cell, ::cell].copy()
    free = np.ones_like(c) if open_land is None else open_land[::cell, ::cell]
    H = c.shape[0]
    for x, st, ln in _runs_1d(c.T):
        if ln not in (3, 4) or st == 0 or st + ln >= H:
            continue
        need = 5 - ln
        if st + ln + need <= H and free[st + ln:st + ln + need, x].all():
            c[st + ln:st + ln + need, x] = True
        else:
            c[st + 2:st + ln, x] = False
    return np.repeat(np.repeat(c, cell, 0), cell, 1)[:h, :w]


def short_runs(m: np.ndarray, cell: int = GRID) -> int:
    """How many boundary runs shorter than two cells the mask still has (0 on the soft grid)."""
    h, w = m.shape
    c = m[::cell, ::cell]
    n = 0
    for a in (c, c.T):
        b = a[:-1] != a[1:]
        left = np.zeros_like(b)
        left[:, 1:] = b[:, :-1]
        right = np.zeros_like(b)
        right[:, :-1] = b[:, 1:]
        n += int((b & ~left & ~right).sum())
    return n


def soften(p: Plot, plan: np.ndarray, seed: int):
    """The drawn edge of a grid-laid mask: True pixels of `plan` that the drawing gives back
    to the land (outer corners rounded, radius 2 to 3, and a 1 px wobble along the rim) and
    land pixels it takes (inner corners chamfered 1 to 2). Returns the drawn mask."""
    m = plan.copy()
    # outer corners: a plan pixel with land on two orthogonal sides within r
    for r in (1, 2):
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            corner = m & ~shift(plan, dx * r, 0, True) & ~shift(plan, 0, dy * r, True)
            m &= ~(corner & (hash01(p.x // 8, p.y // 8, seed + r) < 0.85))
    # inner corners: land with plan on two orthogonal sides gets a 1 px chamfer
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        m |= ~plan & shift(plan, dx, 0, False) & shift(plan, 0, dy, False)
    # a 1 px wobble on long runs: runs of 1 to 10 px nudged in or out
    rim = m & ~erode(m, 1)
    nudge = hash01(p.x // 3 + p.y // 3 * 7, 0, seed + 9)
    m &= ~(rim & (nudge < 0.18))
    out = ~m & dilate(m, 1) & ~dilate(~plan, 1)
    m |= out & (nudge > 0.86)
    return m


# --- reading the plan into the chunk's own pixels ---------------------------------------------

class Region:
    """The chunk's canvas and the plan's geometry in its pixels (box px = world - origin)."""

    def __init__(self, plan: dict, chunk: str = 'lull-delta', crop: tuple | None = None):
        self.plan = plan
        bx, by, bw, bh = plan['chunks'][chunk]['box']
        self.id = chunk
        self.world = (bx, by, bw, bh)
        if crop:   # a window of the chunk, world px (x, y, w, h) on the 8 px grid, for quick looks
            cx, cy, cw, chh = crop
            bx, by, bw, bh = cx, cy, cw, chh
        self.ox, self.oy, self.w, self.h = bx, by, bw, bh
        self.p = Plot(bw, bh, 'grass', 3)

    def pts(self, pts):
        return [(x - self.ox, y - self.oy) for (x, y) in pts]

    def xy(self, pt):
        return pt[0] - self.ox, pt[1] - self.oy


def polyline_mask(R: Region, pts, half: float) -> np.ndarray:
    """Pixels within `half` px of a polyline (box px)."""
    p = R.p
    m = np.zeros((R.h, R.w), bool)
    P = rk.spline(pts, 2.0)
    r = int(half) + 2
    for (cx, cy) in P:
        x0, x1 = max(0, int(cx - r)), min(R.w, int(cx + r) + 1)
        y0, y1 = max(0, int(cy - r)), min(R.h, int(cy + r) + 1)
        if x0 >= x1 or y0 >= y1:
            continue
        dd = (p.x[y0:y1, x0:x1] + 0.5 - cx) ** 2 + (p.y[y0:y1, x0:x1] + 0.5 - cy) ** 2
        m[y0:y1, x0:x1] |= dd <= half * half
    return m


# --- the water ---------------------------------------------------------------------------------

def channel_plan(R: Region, pts, width, seed, bar=True, wob=1.0):
    """A channel's water plan before the grid: as river_kit.river lays it (near-constant
    width, the bank wobbling, a point bar narrowing the water on the inside of each bend).
    Returns (Channel, plan, bar mask, cut-bank height per pixel)."""
    p = R.p
    ch = rk.Channel(p, pts, reach=int(width // 2 + 30))
    hw = width / 2
    bend = ch.bend(0.010)
    w = ((fbm(ch.s, 0 * ch.s, 9, seed) - 0.5) * 4 + (fbm(ch.s, 5 + 0 * ch.s, 4, seed + 1) - 0.5) * 2) * wob
    barw = np.where(~ch.outer, bend * hw * 0.45, 0) if bar else 0 * bend
    edge = hw + w
    plan = ch.near & (np.abs(ch.n) < edge - barw)
    barm = ch.near & ~ch.outer & ~plan & (np.abs(ch.n) < edge + 4 + barw * 0.5) & (barw > 2)
    hb = np.where(ch.outer, 2 + np.round(5 * bend), np.where(bend > 0.25, 1, 3)).astype(int)
    return ch, plan, barm, hb


def flow_dirs(chs, shape):
    """For each pixel the flow direction of the nearest channel (for the current's streaks)."""
    best = np.full(shape, 1e9)
    tx = np.ones(shape)
    ty = np.zeros(shape)
    n = np.zeros(shape)
    s = np.zeros(shape)
    for ch in chs:
        d = np.where(ch.near, np.abs(ch.n), 1e9)
        sel = d < best
        best[sel] = d[sel]
        tx[sel], ty[sel], n[sel], s[sel] = ch.tx[sel], ch.ty[sel], ch.n[sel], ch.s[sel]
    return tx, ty, n, s, best


DASH = (('water_warm', 1), ('water_cool', 1), ('water', 1), ('water_warm', 0), ('water_cool', -1), ('water', -1),
        ('water_warm', 2), ('water_cool', 0), ('water_warm', -1), ('water_cool', 2), ('water', 2), ('lagoon', 0))


def dashes(p: Plot, m, seed, density=1.0, rows=2, seg=8, lmin=4, lspan=5):
    """The surface of wide water as Eastward draws it: ripples as short horizontal strokes,
    4 to 8 px, on every other row in segments of 8 px, each stroke one of twelve sibling
    and tone shifts of what lies under it, taken in turn (not at random) so every 16 px patch
    holds about a dozen tones in two dozen calm shapes, with no lone pixels. Tuned against the
    detail bar's water baseline (tones 13.4, shapes 21.3, dressing 16.8, cluster 7.8)."""
    on_row = (p.y % rows) == 0
    off = (hash01(p.y, 0, seed) * seg).astype(int)
    u = (p.x + off) // seg
    pos = (p.x + off) % seg
    ln = lmin + (hash01(u, p.y, seed + 1) * lspan).astype(int)
    pick = (u * 5 + (p.y // rows) * 3) % len(DASH)
    d = m & on_row & (hash01(u, p.y, seed + 3) < density) & (pos < ln)
    d &= shift(m, 1, 0, False) & shift(m, -1, 0, False)
    for i, (fam, dt) in enumerate(DASH):
        sel = d & (pick == i)
        p.f[sel] = IDX[fam]
        p.t[sel] = np.clip(p.t[sel] + dt, 1, 5)


def depth_map(m: np.ndarray, cap: int = 40) -> np.ndarray:
    """Px from each water pixel to the nearest bank (by repeated erosion, capped)."""
    d = np.zeros(m.shape, np.int16)
    cur = m.copy()
    k = 0
    while cur.any() and k < cap:
        k += 1
        d[cur] = k
        cur = erode(cur, 1)
    return d


def paint_water(R: Region, plan: np.ndarray, hb: np.ndarray, chs, seed: int, still: np.ndarray | None = None,
                soft: np.ndarray | None = None):
    """Water laid on the grid (`plan`, already snapped) and drawn: north banks show their
    face (earth clods, turf lip, roots, a dark wet foot) `hb` px tall, side bands 2 px, the
    south bank a darker lip with the water dark beneath it; the water in depth bands from the
    curved banks (shallow along the drawn edge), ripples as short strokes (`dashes`), the odd
    floating leaf and glint, a light waterline under each north face. Returns (water, face)."""
    p = R.p
    drawn = soften(p, plan, seed)
    rows = np.arange(p.h)[:, None]
    hbx = np.clip(hb, 1, 9)
    src = np.clip(rows - hbx, 0, p.h - 1)
    wet_src = np.take_along_axis(drawn, src, axis=0)
    water = drawn & wet_src
    face = drawn & ~wet_src
    land = ~drawn
    west_land = shift(land, 1, 0, False) | shift(land, 2, 0, False)
    east_land = shift(land, -1, 0, False) | shift(land, -2, 0, False)
    side = water & (west_land | east_land) & (hbx >= 3)
    face |= side
    water &= ~side
    j = np.zeros(p.f.shape, int)
    run = np.zeros(p.w, int)
    for y in range(p.h):
        run = np.where(face[y], run + 1, 0)
        j[y] = run - 1
    j = np.where(side, np.minimum(j, 1), j)
    rk._bank_face(p, face, j, np.maximum(hbx, 2), seed + 20, east_facing=west_land & side)
    # depth: from the channel's own (curved) banks, so the bands curve inside the grid-laid
    # edge, and shallow along the drawn edge itself; the thalweg wanders
    edge_d = depth_map(water, 6)
    dep = depth_map(soft if soft is not None else water, 40).astype(float)
    dep += 8 * (fbm(p.x, p.y, 40, seed + 1) - 0.5)
    tone = np.where(dep > 14, 2, 3)
    tone = np.where(edge_d <= 2, 4, np.where(edge_d <= 4, 3, tone))
    p.f[water], p.t[water] = IDX['water'], tone[water]
    dashes(p, water, seed + 8)
    leaf = water & (edge_d <= 8) & (hash01(p.x // 2, p.y // 2, seed + 10) < 0.006)
    p.f[leaf], p.t[leaf] = IDX['leaf'], 3
    # the south (near) bank: the land's lip a tone darker, the water dark under it
    lip = land & shift(water, 0, 1, False)
    p.step(lip, -1)
    under = water & shift(land, 0, -1, False)
    p.step(under | (water & shift(under, 0, -1, False)), -1, lo=1)
    # a 1 px light waterline under a north face (eastward-edges 5.3)
    wl = water & shift(face, 0, 1, False)
    p.f[wl], p.t[wl] = IDX['water_warm'], 4
    rk.despeckle(p, water)
    p.wet |= water
    p.walk &= ~drawn
    return water, face


# --- the ground ---------------------------------------------------------------------------------

def field_cells(R: Region, m: np.ndarray, size=(176, 136), seed=0):
    """Split land into irregular fields along a warped grid: (label array, count)."""
    p = R.p
    wx = p.x + 30 * (fbm(p.x, p.y, 120, seed) - 0.5)
    wy = p.y + 30 * (fbm(p.x + 999, p.y, 120, seed + 1) - 0.5)
    lab = (np.floor(wy / size[1]).astype(int) * 997 + np.floor((wx + (np.floor(wy / size[1]) % 2) * size[0] / 2) / size[0]).astype(int))
    return np.where(m, lab, -1)


def paint(plan: dict | None = None, crop: tuple | None = None, seed: int = 7, log=print):
    plan = plan or load_plan()
    t0 = time.time()
    R = Region(plan, crop=crop)
    p = R.p
    W = plan['water']
    every = np.ones((R.h, R.w), bool)

    # 1. the sea and the delta's front
    fx = [q[0] - R.ox for q in W['sea']['front']]
    fy = [q[1] - R.oy for q in W['sea']['front']]
    front = np.interp(p.x, fx, fy) + 10 * (fbm(p.x, 0 * p.x, 60, seed) - 0.5)
    sea = p.y > front
    flats = ~sea & (p.y > front - W['sea']['mudflats'] - 24 * fbm(p.x, p.y, 50, seed + 1))
    # 2. the channels
    chs, plans, bars, hbs = [], [], [], []
    lull = channel_plan(R, R.pts(W['lull']['points']), W['lull']['width'], seed + 10, bar=True)
    chs.append(lull[0]); plans.append(lull[1]); bars.append(lull[2]); hbs.append(lull[3])
    for i, arm in enumerate(W['delta_arms']['arms']):
        c = channel_plan(R, R.pts(arm['points']), arm['width'], seed + 20 + i, bar=arm['width'] > 40, wob=0.8)
        chs.append(c[0]); plans.append(c[1]); bars.append(c[2])
        hbs.append(np.where(c[0].outer, 3, 2).astype(int))
    ox1 = channel_plan(R, R.pts(W['fresh_oxbow']['points']), W['fresh_oxbow']['width'], seed + 40, bar=False)
    silted = polyline_mask(R, R.pts(W['silted_oxbow']['points']), W['silted_oxbow']['width'] / 2)
    hb = np.full(p.f.shape, 2, int)
    for c, h_ in zip(chs, hbs):
        hb = np.where(c.near, np.maximum(hb, np.where(np.abs(c.n) < 200, h_, 2)), hb)
    river_plan = np.zeros(p.f.shape, bool)
    for pl in plans:
        river_plan |= pl
    river_plan |= ox1[1]
    river_plan &= ~flats | dilate(river_plan & ~flats, 2)
    log(f'  channels laid in {time.time() - t0:.1f} s')

    # 3. the ground, by what grows there
    near_river = dilate(river_plan, 40)
    wm = near_river & ~river_plan
    carr_t = np.clip(((p.x + R.ox) - 9290 + 40 * (fbm(p.x, p.y, 70, seed + 2) - 0.5)) / 120.0, 0, 1) * \
        np.clip((4180 - (p.y + R.oy)) / 200.0, 0, 1)
    delta_line = 4620 + 70 * (fbm(p.x, 0 * p.x, 90, seed + 16) - 0.5) + 40 * np.sin((p.x + R.ox) / 61.0)
    delta_zone = (p.y + R.oy > delta_line) & ~sea
    west_plain = (p.x + R.ox < 8880) & ~delta_zone & ~sea
    dunes = (p.x + R.ox < 8600) & ~sea & (p.y > front - 150 - 40 * fbm(p.x, p.y, 40, seed + 3))
    tiled(p, rk.pasture, every, seed + 1)
    meadows = field_cells(R, west_plain & ~near_river, (200, 150), seed + 4)
    hay = np.zeros(p.f.shape, bool)
    for k in np.unique(meadows[meadows >= 0]):
        if hash01(int(k), 0, seed + 5) < 0.45:
            hay |= meadows == k
    tiled(p, rk.hay_meadow, hay, seed + 6)
    t = time.time()
    # water meadows: the pasture greener and wetter near the river, rushes and marigolds
    p.sib(wm & (fbm(p.x, p.y, 18, seed + 6) > 0.55), 'cool')
    # the delta: marsh between the arms, reed beds, mudflats, dunes behind the beach
    marsh = delta_zone & ~river_plan & ~flats & ~dunes
    p.sib(marsh, 'cool')
    p.step(marsh & (fbm(p.x, p.y, 10, seed + 7) > 0.6), -1, lo=2)
    tiled(p, rk.sand, flats & ~dunes, None, seed + 8)
    p.sib(flats & ~dunes, 'cool')
    p.step(flats & (fbm(p.x, p.y, 16, seed + 9) > 0.55), -1, lo=2)
    tiled(p, rk.sand, dunes, None, seed + 10)
    tiled(p, rk.wood_floor, carr_t > 0.35, seed + 11)
    land = ~river_plan & ~sea
    tiled(p, rk.texture, land & ~flats & ~dunes & ~hay, seed + 14, swaps=0.05, ups=0.02, downs=0.025)
    shore = (flats | dunes) & land
    tiled(p, rk.texture, shore, seed + 17, swaps=0.14, ups=0.05, downs=0.06)
    tiled(p, rk.pebbles, shore & (fbm(p.x, p.y, 14, seed + 18) > 0.45), seed + 19, 0.03)
    wrack = shore & (np.abs(p.y - (front - 18 - 10 * fbm(p.x, 0 * p.x, 30, seed + 20))) < 1.5) & \
        (hash01(p.x // 4, 0, seed + 21) < 0.7)
    p.f[wrack], p.t[wrack] = IDX['leaf_cool'], 1
    tiled(p, rk.texture, marsh, seed + 22, swaps=0.12, ups=0.04, downs=0.05)
    log(f'  ground in {time.time() - t:.1f} s')

    # 4. reed beds (block, in whole cells): the inner delta and the silted oxbow
    reed_t = fbm(p.x, p.y, 70, seed + 12)
    reedbed = (marsh & (reed_t > 0.48) & ~dilate(river_plan, 6)) | (silted & ~river_plan)
    # 5. the Lull Cut (a canal on the grid) and the paths
    cut = W['lull_cut']
    cut_ch = rk.Channel(p, R.pts(cut['points']), reach=cut['width'] // 2 + 30)
    cut_plan = soft_snap(cut_ch.near & (np.abs(cut_ch.n) < cut['width'] / 2))
    routes = plan['routes']
    path_masks = {}
    for name in ('lull_road', 'delta_road', 'towpath', 'coast_path'):
        r = routes[name]
        path_masks[name] = polyline_mask(R, R.pts(r['points']), r['width'] / 2)
    roads = np.zeros(p.f.shape, bool)
    for m in path_masks.values():
        roads |= m
    board = np.zeros(p.f.shape, bool)
    trods = [n for n, r in routes.items() if n not in path_masks]
    for name in trods:
        if name == 'boardwalk':
            board |= polyline_mask(R, R.pts(routes[name]['points']), routes[name]['width'] / 2)
        else:
            roads |= polyline_mask(R, R.pts(routes[name]['points']), routes[name]['width'] / 2)
    br = plan['lullford']['bridge']
    bx0, by0 = R.xy(br['from'])
    bx1, _ = R.xy(br['to'])
    deck = (p.x >= bx0 - 8) & (p.x < bx1 + 8) & (np.abs(p.y - by0) <= br['deck'] // 2)
    reedbed &= ~dilate(roads | board | cut_plan, 10)

    # 6. lay everything that blocks on the grid
    ix, iy, iw, ih = br['island']
    ix, iy = R.xy((ix, iy))
    island = (p.x >= ix) & (p.x < ix + iw) & (p.y >= iy) & (p.y < iy + ih)
    island = soft_snap(dilate(island, 2) & (fbm(p.x, p.y, 9, seed + 17) < 0.9))
    river_plan &= ~island
    deck_plan = soft_snap(deck)
    water_plan = soft_snap((river_plan | sea) & ~deck_plan) & ~deck_plan
    water_plan = jog(water_plan)
    water_plan &= ~deck_plan
    reed_plan = bands(jog(soft_snap(reedbed) & ~water_plan), open_land=~water_plan)
    carr_plan = bands(jog(soft_snap((carr_t > 0.7) & ~roads) & ~water_plan), open_land=~water_plan)
    log(f'  grid laid in {time.time() - t0:.1f} s; short runs: water {short_runs(water_plan)}, '
        f'reeds {short_runs(reed_plan)}, carr {short_runs(carr_plan)}')

    # 7. draw: bars, water, canal, sea's surf, paths
    barm = np.zeros(p.f.shape, bool)
    for b in bars:
        barm |= b
    barm &= ~water_plan & ~flats
    if barm.any():
        tiled(p, rk.sand, barm, None, seed + 13)
    still = dilate(ox1[1], 2)
    sea_plan = soft_snap(sea)
    river_water = water_plan & ~sea_plan
    paint_water(R, river_water, hb, chs + [ox1[0]], seed + 30, still=still, soft=river_plan & river_water)
    sea_m = water_plan & sea_plan
    paint_sea(R, sea_m, seed + 40)
    paint_canal(R, cut_ch, cut_plan, seed + 50)
    for i, name in enumerate(('lull_road', 'towpath', 'coast_path', 'delta_road') + tuple(t for t in trods if t != 'boardwalk')):
        r = routes[name]
        if len(r['points']) < 2:
            continue
        tr = rk.track(p, R.pts(r['points']), r['width'], seed + 60 + i, puddles=3 if name == 'lull_road' else 1)
        if name == 'lull_road':   # the old road: bare and wide, no grass crown, cobbled near the bridge
            c = tr.mask & (np.abs(tr.n) < 5) & ~p.wet
            rk.base(p, c, 'path', seed + 66, scale=6, light=0.66)
            rk.texture(p, c, seed + 67, swaps=0.10, ups=0.02, downs=0.03)
            rk.pebbles(p, c, seed + 68, 0.02)
        path_masks[name] = tr.mask
    roads = np.zeros(p.f.shape, bool)
    for m in path_masks.values():
        roads |= m
    fray(R, roads & ~water_plan & ~cut_plan, seed + 63)
    paint_boardwalk(R, board & ~water_plan, seed + 64)
    paint_bridge(R, br, seed + 70)
    log(f'  water and paths drawn in {time.time() - t0:.1f} s')

    # 8. what stands: reeds, carr, willows and alders on the banks, Lullford's houses
    paint_reedbeds(R, reed_plan, seed + 80)
    paint_carr(R, carr_plan, carr_t, seed + 90)
    bank_trees(R, water_plan | cut_plan, roads | board, seed + 100)
    town = paint_lullford(R, plan, seed + 110)
    rk.despeckle(p)
    log(f'  standing things in {time.time() - t0:.1f} s')

    # 9. the walk and the terrain, from the layout (never from the drawing)
    blocked_plan = reed_plan | carr_plan | town['blocked'] | soft_snap(cut_plan)
    walk = ~(water_plan | blocked_plan)
    walk |= deck_plan
    path_plan = soft_snap(roads | board) & walk
    R.water_plan, R.blocked_plan, R.walk_px, R.path_plan = water_plan | cut_plan, blocked_plan, walk, path_plan
    R.reed_plan = reed_plan
    R.town = town
    R.stands = {}
    log(f'painted {R.id} {R.w} x {R.h} in {time.time() - t0:.1f} s')
    return R


def paint_sea(R: Region, m, seed):
    """Open sea off the delta: deepening away from the shore in broad bands, the surface in
    ripple strokes like the river's (`dashes`), long swell lines lit on top, the surf where
    the water meets the flats (white only where waves break)."""
    p = R.p
    dep = depth_map(m, 60).astype(float) + 10 * (fbm(p.x, p.y, 50, seed + 2) - 0.5)
    tone = np.where(dep > 14, 2, 3)
    p.f[m], p.t[m] = IDX['water'], tone[m]   # one body ramp: its cool sibling breaks the ripples into specks
    dashes(p, m, seed + 3)
    edge_d = depth_map(m, 4)
    surf = m & (edge_d <= 2) & (hash01(p.x // 3, p.y // 2, seed + 1) < 0.75)
    p.f[surf], p.t[surf] = IDX['water_warm'], 5
    rk.despeckle(p, m)
    p.wet |= m
    p.walk &= ~m


def paint_canal(R: Region, ch, plan, seed):
    """The Lull Cut on the grid: still water between dressed stone copings, the north edge's
    coursed face showing (river_kit's coping and stone bank face), the towpath beside it."""
    p = R.p
    cope = dilate(plan, 3) & ~plan
    water, face, j, west = rk._sunken(p, plan, 6)
    rk.coping(p, cope, seed)
    rk._bank_face(p, face, j, 6, seed + 1, stone=True, east_facing=west)
    m = water
    sibn = fbm(ch.s / 4.0, ch.n, 8, seed + 2)
    fam = np.where(sibn < 0.3, IDX['water_warm'], np.where(sibn > 0.7, IDX['water_cool'], IDX['water']))
    k = np.where(depth_map(m, 12) > 6, 2, 3)
    p.f[m], p.t[m] = fam[m], k[m]
    dashes(p, m, seed + 4, seg=7, lmin=3)
    under = m & shift(cope, 0, -1, False)
    p.step(under | (m & shift(under, 0, -1, False)), -1, lo=1)
    wl = m & shift(face, 0, 1, False)
    p.f[wl], p.t[wl] = IDX['water_warm'], 4
    rk.despeckle(p, m)
    p.wet |= water
    p.walk &= ~plan


def fray(R: Region, m, seed):
    """Grass to path, Eastward 5.1: a frayed band 2 to 3 px in 1 px steps, a tuft or a bite
    3 to 4 px about every 16 px, dark crumbs along it, no line and no dither."""
    p = R.p
    edge_in = m & ~erode(m, 2)
    bite = edge_in & (hash01(p.x // 16, p.y // 16, seed) < 0.5) & (hash01(p.x, p.y, seed + 1) < 0.5)
    tuft_zone = ~m & dilate(m, 3)
    tuft = tuft_zone & (hash01(p.x // 16 + 3, p.y // 16, seed + 2) < 0.45) & (hash01(p.x // 2, p.y // 2, seed + 3) < 0.45)
    p.f[tuft & shift(m, 0, 0, False)] = IDX['grass']
    gr = m & ~erode(m, 1) & (hash01(p.x, p.y, seed + 4) < 0.35)
    p.f[gr], p.t[gr] = IDX['grass'], 3
    p.f[bite & ~gr], p.t[bite & ~gr] = IDX['grass'], 2
    crumbs = m & ~erode(m, 3) & erode(m, 1) & (hash01(p.x // 2, p.y // 2, seed + 5) < 0.12)
    p.t[crumbs & p.fam('path')] = 1


def paint_boardwalk(R: Region, m, seed):
    """A boardwalk across the marsh: planks across the way 3 px wide, lit fronts, a dark gap,
    posts every 16 px at each side."""
    p = R.p
    if not m.any():
        return
    core = erode(m, 1)
    plank = (p.x + p.y) // 3
    pick = hash01(plank, 0, seed)
    fam = np.where(pick < 0.3, IDX['timber_warm'], np.where(pick > 0.7, IDX['timber_cool'], IDX['timber']))
    k = np.where((p.x + p.y) % 3 == 0, 4, np.where((p.x + p.y) % 3 == 2, 2, 3))
    p.f[core], p.t[core] = fam[core], k[core]
    rim = m & ~core
    p.f[rim], p.t[rim] = IDX['timber_cool'], 1
    post = rim & ((p.x + p.y) % 16 < 2)
    p.f[post], p.t[post] = IDX['timber'], 2
    p.walk |= m


def paint_bridge(R: Region, br, seed):
    """Lullford Bridge: a stone deck on arches from the west bank to the island, an iron
    swing span over the navigation channel to the east bank; parapets on both sides, lit on
    top; the deck's south face with its arches over the water."""
    p = R.p
    x0, y = R.xy(br['from'])
    x1, _ = R.xy(br['to'])
    hd = br['deck'] // 2
    if not (0 <= y < R.h):
        return
    deck = (p.x >= x0) & (p.x < x1) & (np.abs(p.y - y) < hd)
    span_x0 = x1 - 44
    stone = deck & (p.x < span_x0)
    iron = deck & (p.x >= span_x0)
    # setts on the stone deck
    u, v = (p.x + (p.y // 4) * 3) // 6, p.y // 4
    pick = hash01(u, v, seed)
    fam = np.where(pick < 0.3, IDX['stone_warm'], np.where(pick > 0.7, IDX['stone_cool'], IDX['stone']))
    k = np.where(p.y % 4 == 0, 2, np.where((p.x + (p.y // 4) * 3) % 6 == 0, 2, 3))
    p.f[stone], p.t[stone] = fam[stone], k[stone]
    # iron plates with rivets on the swing span
    k2 = np.where((p.x - span_x0) % 11 == 0, 1, np.where(p.y % 6 == 0, 2, 3))
    p.f[iron], p.t[iron] = IDX['iron'], k2[iron]
    riv = iron & ((p.x - span_x0) % 11 == 2) & (p.y % 6 == 3)
    p.t[riv] = 4
    # parapets: 3 px each side, lit on top
    for side in (-1, 1):
        py = y + side * (hd - 2)
        par = (p.x >= x0) & (p.x < x1) & (np.abs(p.y - py) <= 1)
        p.f[par & stone] = IDX['stone']
        p.f[par & iron] = IDX['iron']
        p.t[par] = 3
        p.t[par & (p.y == py - 1)] = 4
        p.t[par & (p.y == py + 1)] = 2
    # the south face over the water: 8 px of masonry, an arch every 32 px
    face = (p.x >= x0) & (p.x < span_x0) & (p.y >= y + hd) & (p.y < y + hd + 8)
    ax = (p.x - x0) % 32
    arch = face & (ax > 6) & (ax < 26) & ((p.y - (y + hd)) > 2 + np.abs(ax - 16) // 4)
    p.f[face], p.t[face] = IDX['stone_cool'], 2
    p.t[face & ((p.y - (y + hd)) == 0)] = 3
    p.f[arch], p.t[arch] = IDX['water_cool'], 1
    gfa = (p.x >= span_x0) & (p.x < x1) & (p.y >= y + hd) & (p.y < y + hd + 4)
    p.f[gfa], p.t[gfa] = IDX['iron'], 1
    p.wet &= ~(deck | face)
    p.walk |= deck
    p.solid |= face


def paint_reedbeds(R: Region, m, seed):
    """Reed beds that block in whole cells: wet ground with standing water between, the reed
    clumps of the kit standing densely in it (taller to the middle), the odd bulrush."""
    p = R.p
    if not m.any():
        return
    p.f[m] = IDX['grass_cool']
    p.t[m] = 2
    pools = m & (fbm(p.x, p.y, 9, seed) > 0.62) & erode(m, 3)
    p.f[pools], p.t[pools] = IDX['water_cool'], 2
    rk.stamp(p, m & ~pools, 0.12, seed + 1, rk.BLADES, dt=1)
    pts = rk._scatter(m & ~pools, 70, seed + 2, margin=2)
    for i, (x, y) in enumerate(pts):
        sp, sh = rk.reeds('mace' if hash01(x, y, seed + 3) < 0.25 else 'reed', seed + i, 4 + i % 3)
        paste(p, sp, x, y, shadow=sh)


def paint_carr(R: Region, m, t, seed):
    """Willow carr thickening into thicket at the belt's north-east edge (the fade and the
    wall of brief 6): willows and alders on wet wood floor, brambles under them."""
    p = R.p
    if not m.any():
        return
    pts = rk._scatter(m, 900, seed, margin=6)
    for i, (x, y) in enumerate(sorted(pts, key=lambda q: q[1])):
        pick = hash01(x, y, seed + 1)
        if pick < 0.45:
            sp, sh = rk.willow(i % 2, seed + i)
        elif pick < 0.8:
            sp, sh = rk.alder(seed + i)
        else:
            sp, sh = rk.shrub('bramble', seed + i)
        paste(p, sp, x, y, shadow=sh)
    fade = (t > 0.35) & ~m & ~p.solid
    for i, (x, y) in enumerate(rk._scatter(fade, 2600, seed + 2, margin=6)):
        sp, sh = rk.shrub('bramble' if i % 2 else 'hawthorn', seed + i)
        paste(p, sp, x, y, shadow=sh)


def bank_trees(R: Region, water, paths, seed):
    """Willows and alders standing at the water, never on a path, not in a row."""
    p = R.p
    bank = dilate(water, 14) & ~dilate(water, 6) & ~dilate(paths, 10) & ~p.solid & ~p.wet
    pts = rk._scatter(bank, 5200, seed, margin=12)
    for i, (x, y) in enumerate(sorted(pts, key=lambda q: q[1])):
        mk = rk.willow if hash01(x, y, seed + 1) < 0.5 else rk.alder
        sp, sh = mk(i % 2, seed + i) if mk is rk.willow else mk(seed + i)
        paste(p, sp, x, y, shadow=sh)


def kit_sprite(img: Image.Image) -> rk.Sprite:
    """A house-kit picture (house palette RGBA) as a river-kit sprite (ramp and tone)."""
    a = np.asarray(img.convert('RGBA'))
    h, w = a.shape[:2]
    sp = rk.Sprite(w, h, w // 2, h - 1)
    flat = rk.COL.reshape(-1, 3).astype(int)
    keys = {tuple(c): i for i, c in enumerate(flat.tolist())}
    for y, x in zip(*np.nonzero(a[..., 3] > 0)):
        c = tuple(int(v) for v in a[y, x, :3])
        i = keys.get(c)
        if i is None:
            i = int(np.argmin(((flat - np.array(c)) ** 2).sum(1)))
        sp.f[y, x], sp.t[y, x] = divmod(i, 7)
        sp.m[y, x] = True
    return sp


def paint_lullford(R: Region, plan: dict, seed):
    """Lullford's buildings where the plan stands them (plan 'buildings': a foot line and a
    width each): fronts of the valley house kit, variants and colourways picked by
    house_kits.street so no two neighbours match, each casting its shade east. Each blocks its
    whole footprint in grid cells, so nothing walks hidden behind it. Returns {'blocked': mask}."""
    import house_kits as hk
    p = R.p
    blocked = np.zeros(p.f.shape, bool)
    bl = plan.get('buildings', [])
    order = hk.street('valley', max(1, len(bl)), seed)
    for i, b in enumerate(bl):
        v, cw = order[i % len(order)]
        cv = hk.front('valley', v, cw)
        img = cv.img
        if b['w'] < img.width - 8:   # a small building (the toll house): the front cut down to its width
            img = img.resize((b['w'], int(img.height * b['w'] / img.width)), Image.NEAREST)
        sp = kit_sprite(img)
        fx, fy = R.xy(b['foot'])
        x0 = fx
        if not (-sp.w < x0 < R.w and 0 < fy < R.h + sp.h):
            continue
        sh = np.zeros(sp.m.shape, bool)
        sh[:, 4:] = sp.m[:, :-4]
        paste(p, sp, x0 + sp.w // 2, fy, outline=False, shadow=sh & ~sp.m)
        bm = np.zeros(p.f.shape, bool)
        bm[max(0, fy - sp.h + 8):max(0, fy), max(0, x0 + 2):max(0, x0 + sp.w - 2)] = True
        blocked |= bm
    return {'blocked': bands(jog(soft_snap(blocked))) if blocked.any() else blocked}


# --- outputs ------------------------------------------------------------------------------------

def terrain_rows(R: Region) -> np.ndarray:
    """The terrain code per 4 px walk cell, from the layout: water, blocked, path, ground."""
    c = 4
    H, Wd = R.h // c, R.w // c

    def maj(m):
        return m[:H * c, :Wd * c].reshape(H, c, Wd, c).mean((1, 3)) >= 0.5
    t = np.full((H, Wd), '.', '<U1')
    t[maj(R.path_plan)] = '='
    t[maj(R.blocked_plan & ~R.water_plan)] = '^'
    t[maj(R.water_plan & ~R.walk_px)] = '~'
    return t


def audit(R: Region, out: str | None = None, log=print):
    """The world audit's checks (scripts/art/world_audit.py) on the painted chunk directly:
    its ground, terrain and walk as a Region, areas from the plan's boxes."""
    import world_audit as wa
    img = R.p.image().convert('RGBA')
    A_R = wa.Region(R.id, 'continent', R.w, R.h, (R.ox, R.oy))
    A_R.ground[:] = np.asarray(img)
    t = terrain_rows(R)
    A_R.terrain[:] = np.vectorize(lambda ch: wa.CODES.get(ch, 0))(t)
    c = 4
    A_R.walk[:] = R.walk_px[:R.h // c * c, :R.w // c * c].reshape(R.h // c, c, R.w // c, c).mean((1, 3)) >= 0.5
    for aid, (x, y, w, h) in areas(R).items():
        A_R.add_place(wa.Place(aid, 'area', R.id, 'lull_delta', (x, y, w, h)))
    ctx = wa.make_context(ROOT, None)
    ctx['source'] = 'world'
    ctx['root'] = ROOT
    A = wa.Audit(A_R, ctx).run({})
    w = A.worst
    art = w != wa.NA
    res = {'cells': int(art.sum()), 'green': int((w == wa.PASS).sum()), 'amber': int((w == wa.AMBER).sum()),
           'red': int((w == wa.RED).sum()), 'checks': {}}
    for ck in wa.CHECK_IDS:
        s = A.status[ck]
        res['checks'][ck] = {'measured': int((s != wa.NA).sum()), 'red': int((s == wa.RED).sum()),
                             'amber': int((s == wa.AMBER).sum())}
    from collections import Counter
    res['why'] = Counter(f"{ck}: {v.split(':')[0][:48]}" for (ck, cy, cx), v in A.why.items()
                         if A.status[ck][cy, cx] == wa.RED).most_common(20)
    if out:
        os.makedirs(out, exist_ok=True)
        wa.heat(A).save(os.path.join(out, f'{R.id}-audit.png'))
        wa.heat(A, drawn=True).save(os.path.join(out, f'{R.id}-audit-drawn.png'))
    log(f"audit: {res['cells']} cells, {res['green']} green, {res['amber']} amber, {res['red']} red")
    for ck, v in res['checks'].items():
        if v['measured']:
            log(f"  {ck:14s} measured {v['measured']:5d}  red {v['red']:5d}  amber {v['amber']:5d}")
    for k, n in res['why']:
        log(f'  {n:5d}  {k}')
    return res


def areas(R: Region) -> dict:
    """The chunk's named areas (box px), from the plan's boxes, cut to the canvas."""
    out = {}
    world = {
        'lull-belt': (8304, 3296, 1152, 800),
        'lullford': (8304, 4096, 800, 480),
        'canal-embankment': (9104, 4096, 352, 480),
        'lull-delta': (8304, 4576, 1152, 1312),
    }
    for k, (x, y, w, h) in world.items():
        x0, y0 = max(x, R.ox), max(y, R.oy)
        x1, y1 = min(x + w, R.ox + R.w), min(y + h, R.oy + R.h)
        if x1 > x0 and y1 > y0:
            out[k] = (x0 - R.ox, y0 - R.oy, x1 - x0, y1 - y0)
    return out


def previews(R: Region, out: str):
    os.makedirs(out, exist_ok=True)
    img = R.p.image()
    img.save(os.path.join(out, f'{R.id}.png'))
    small = img.resize((R.w // 4, R.h // 4), Image.BOX)
    small.save(os.path.join(out, f'{R.id}-quarter.png'))
    # phone-sized views (360 px wide at 1x, so 320 x 576 art px is one screen) at 2x
    views = {'lullford-bridge': (8760, 4120), 'belt-bends': (8960, 3420), 'delta-apex': (8840, 4460),
             'delta-front': (8840, 5180), 'canal': (9150, 4380), 'oxbow': (9136, 3700)}
    for k, (x, y) in views.items():
        x0, y0 = x - R.ox, y - R.oy
        if 0 <= x0 and 0 <= y0 and x0 + 320 <= R.w and y0 + 576 <= R.h:
            img.crop((x0, y0, x0 + 320, y0 + 576)).resize((640, 1152), Image.NEAREST).save(
                os.path.join(out, f'view-{k}.png'))
    # the layout: water, blocked, paths
    lay = np.zeros((R.h, R.w, 3), np.uint8)
    lay[:] = (120, 170, 90)
    lay[R.path_plan] = (200, 170, 110)
    lay[R.blocked_plan] = (60, 90, 50)
    lay[R.water_plan] = (60, 110, 190)
    Image.fromarray(lay).resize((R.w // 2, R.h // 2), Image.NEAREST).save(os.path.join(out, f'{R.id}-layout.png'))


def check_plan(plan: dict) -> list:
    """The plan's own contract. The full check is Claude F's region_plan.py (npm run
    check:region-plans, #174) when it is in the tree; this keeps what the painter relies on:
    the box in whole audit cells on the 8 px grid, the water and the routes it paints."""
    bad = []
    x0, y0, w, h = plan['box']
    if x0 % GRID or y0 % GRID or w % 32 or h % 32:
        bad.append(f'box {plan["box"]} is not whole 32 px cells on the {GRID} px grid')
    for k in ('lull', 'fresh_oxbow', 'silted_oxbow', 'lull_cut', 'sea'):
        if k not in plan['water']:
            bad.append(f'no water {k}')
    for k in ('lull_road', 'towpath', 'coast_path', 'delta_road'):
        if k not in plan['routes']:
            bad.append(f'no route {k}')
    try:
        import region_plan
    except ImportError:
        return bad
    return bad + region_plan.check(plan['plan'])


def main(argv):
    if '--check' in argv:
        bad = check_plan(load_plan())
        for b in bad:
            print('lull_delta plan:', b)
        print('lull_delta plan: ok' if not bad else f'lull_delta plan: {len(bad)} faults')
        return 1 if bad else 0
    args = [a for a in argv if not a.startswith('--')]
    out = args[0] if args else os.path.join(tempfile.gettempdir(), 'napattack-lull-delta')
    crop = None
    for a in argv:
        if a.startswith('--crop='):
            crop = tuple(int(v) for v in a.split('=', 1)[1].split(','))
    plan = load_plan()
    bad = check_plan(plan)
    if bad:
        print('\n'.join(bad))
        return 1
    R = paint(plan, crop=crop)
    previews(R, out)
    if '--audit' in argv:
        audit(R, out)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
