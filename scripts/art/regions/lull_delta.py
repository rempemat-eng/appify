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

PLAN_PATH = os.path.join(HERE, 'neon_delta.json')
GRID = 8


def load_plan(path: str = PLAN_PATH) -> dict:
    with open(path) as f:
        return json.load(f)


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


def paint_water(R: Region, plan: np.ndarray, hb: np.ndarray, chs, seed: int, still: np.ndarray | None = None):
    """Water laid on the grid (`plan`, already snapped) and drawn: north banks show their
    face (earth clods, turf lip, roots, a dark wet foot) `hb` px tall, side bands 2 px, the
    south bank a darker lip with the water dark beneath it; the water in depth bands from the
    banks, sibling patches along the flow, streaks of current, glints; still water (oxbows)
    calm with a light waterline. Returns (water, face)."""
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
    tx, ty, n, s, _d = flow_dirs(chs, p.f.shape)
    dep = depth_map(water, 30)
    tone = np.where(dep > 18, 1, np.where(dep > 8, 2, np.where(dep > 3, 3, 4)))
    tone = np.where((dep > 3) & (fbm(p.x, p.y, 14, seed + 1) > 0.62), tone + 1, tone)
    sibn = fbm(s / 3.0, n * 1.2, 7, seed + 2)
    fam = np.where(sibn < 0.33, IDX['water_warm'], np.where(sibn > 0.68, IDX['water_cool'], IDX['water']))
    p.f[water], p.t[water] = fam[water], np.clip(tone, 1, 4)[water]
    run_w = water if still is None else water & ~still
    lane = np.floor((n + 400) / 3).astype(int)
    on = hash01(lane, 0, seed + 3) < 0.5
    per = 24 + (hash01(lane, 1, seed + 4) * 16).astype(int)
    pos = (s.astype(int) + (hash01(lane, 2, seed + 5) * 40).astype(int)) % per
    ln = 3 + (hash01(lane, 3, seed + 6) * 3).astype(int)
    centre = np.abs(n - (lane * 3 - 400 + 1.5)) < 0.75
    streak = run_w & on & centre & (pos < ln) & (p.t <= 3)
    p.step(shift(streak, 0, 1, False) & run_w & ~streak, -1, lo=1)
    p.step(streak, 1)
    g = water & (hash01(p.x // 2, p.y, seed + 7) < 0.010) & (p.t <= 2) & ~streak
    gg = g | (shift(g, 1, 0, False) & water)
    p.f[gg], p.t[gg] = IDX['water_warm'], 4
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
    delta_zone = (p.y + R.oy > 4560) & ~sea
    west_plain = (p.x + R.ox < 8880) & (p.y + R.oy < 4560)
    dunes = (p.x + R.ox < 8600) & ~sea & (p.y > front - 150 - 40 * fbm(p.x, p.y, 40, seed + 3))
    rk.pasture(p, every, seed + 1)
    meadows = field_cells(R, west_plain & ~near_river, (200, 150), seed + 4)
    for k in np.unique(meadows[meadows >= 0])[:400]:
        m = meadows == k
        pick = hash01(int(k), 0, seed + 5)
        if pick < 0.45:
            rk.hay_meadow(p, m, seed + int(k) % 97)
    t = time.time()
    # water meadows: the pasture greener and wetter near the river, rushes and marigolds
    p.sib(wm & (fbm(p.x, p.y, 18, seed + 6) > 0.55), 'cool')
    # the delta: marsh between the arms, reed beds, mudflats, dunes behind the beach
    marsh = delta_zone & ~river_plan & ~flats & ~dunes
    p.sib(marsh, 'cool')
    p.step(marsh & (fbm(p.x, p.y, 10, seed + 7) > 0.6), -1, lo=2)
    rk.sand(p, flats & ~dunes, None, seed + 8)
    p.sib(flats & ~dunes, 'cool')
    p.step(flats & (fbm(p.x, p.y, 16, seed + 9) > 0.55), -1, lo=2)
    rk.sand(p, dunes, None, seed + 10)
    rk.wood_floor(p, carr_t > 0.35, seed + 11)
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
    board = polyline_mask(R, R.pts(routes['boardwalk']['points']), routes['boardwalk']['width'] / 2)
    roads = np.zeros(p.f.shape, bool)
    for m in path_masks.values():
        roads |= m
    br = plan['lullford']['bridge']
    bx0, by0 = R.xy(br['from'])
    bx1, _ = R.xy(br['to'])
    deck = (p.x >= bx0 - 8) & (p.x < bx1 + 8) & (np.abs(p.y - by0) <= br['deck'] // 2)
    reedbed &= ~dilate(roads | board | cut_plan, 10)

    # 6. lay everything that blocks on the grid
    deck_plan = soft_snap(deck)
    water_plan = soft_snap((river_plan | sea) & ~deck_plan) & ~deck_plan
    reed_plan = soft_snap(reedbed) & ~water_plan
    carr_plan = soft_snap((carr_t > 0.7) & ~roads) & ~water_plan
    log(f'  grid laid in {time.time() - t0:.1f} s; short runs: water {short_runs(water_plan)}, '
        f'reeds {short_runs(reed_plan)}, carr {short_runs(carr_plan)}')

    # 7. draw: bars, water, canal, sea's surf, paths
    barm = np.zeros(p.f.shape, bool)
    for b in bars:
        barm |= b
    barm &= ~water_plan & ~flats
    if barm.any():
        rk.sand(p, barm, None, seed + 13)
    still = dilate(ox1[1], 2)
    sea_plan = soft_snap(sea)
    river_water = water_plan & ~sea_plan
    paint_water(R, river_water, hb, chs + [ox1[0]], seed + 30, still=still)
    sea_m = water_plan & sea_plan
    paint_sea(R, sea_m, seed + 40)
    paint_canal(R, cut_ch, cut_plan, seed + 50)
    for name, m in path_masks.items():
        rk.base(p, m & ~water_plan & ~cut_plan, 'path', seed + 60, scale=6, light=0.66)
        rk.texture(p, m & ~water_plan & ~cut_plan, seed + 61, swaps=0.12, ups=0.03, downs=0.02)
        rk.pebbles(p, m & ~water_plan, seed + 62, 0.012)
    fray(R, roads & ~water_plan & ~cut_plan, seed + 63)
    paint_boardwalk(R, board & ~water_plan, seed + 64)
    paint_bridge(R, br, seed + 70)
    log(f'  water and paths drawn in {time.time() - t0:.1f} s')

    # 8. what stands: reeds, carr, willows and alders on the banks, Lullford's houses
    paint_reedbeds(R, reed_plan, seed + 80)
    paint_carr(R, carr_plan, carr_t, seed + 90)
    bank_trees(R, water_plan | cut_plan, roads | board, seed + 100)
    town = paint_lullford(R, plan['lullford'], roads, seed + 110)
    rk.despeckle(p)
    log(f'  standing things in {time.time() - t0:.1f} s')

    # 9. the walk and the terrain, from the layout (never from the drawing)
    blocked_plan = reed_plan | carr_plan | town['blocked'] | soft_snap(cut_plan)
    walk = ~(water_plan | blocked_plan)
    walk |= deck_plan
    path_plan = soft_snap(roads | board) & walk
    R.water_plan, R.blocked_plan, R.walk_px, R.path_plan = water_plan | cut_plan, blocked_plan, walk, path_plan
    R.town = town
    R.stands = {}
    log(f'painted {R.id} {R.w} x {R.h} in {time.time() - t0:.1f} s')
    return R


def paint_sea(R: Region, m, seed):
    """Open sea off the delta: deepening away from the shore in calm bands, swell lines, the
    surf where the water meets the flats (white only where waves break)."""
    p = R.p
    dep = depth_map(m, 60)
    tone = np.where(dep > 40, 1, np.where(dep > 16, 2, np.where(dep > 5, 3, 4)))
    fam = np.where(fbm(p.x, p.y, 30, seed) < 0.4, IDX['water_cool'], IDX['water'])
    p.f[m], p.t[m] = fam[m], tone[m]
    swell = m & (((p.y + 6 * np.sin(p.x / 37.0)).astype(int) % 23) == 0) & (hash01(p.x // 5, p.y, seed) < 0.6) & (dep > 6)
    p.step(swell, 1)
    p.step(shift(swell, 0, 1, False) & m, -1, lo=1)
    surf = m & (dep <= 2) & (hash01(p.x // 3, 0, seed + 1) < 0.7)
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
        rk.paste(p, sp, x, y, shadow=sh)


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
        rk.paste(p, sp, x, y, shadow=sh)
    fade = (t > 0.35) & ~m & ~p.solid
    for i, (x, y) in enumerate(rk._scatter(fade, 2600, seed + 2, margin=6)):
        sp, sh = rk.shrub('bramble' if i % 2 else 'hawthorn', seed + i)
        rk.paste(p, sp, x, y, shadow=sh)


def bank_trees(R: Region, water, paths, seed):
    """Willows and alders standing at the water, never on a path, not in a row."""
    p = R.p
    bank = dilate(water, 14) & ~dilate(water, 6) & ~dilate(paths, 10) & ~p.solid & ~p.wet
    pts = rk._scatter(bank, 5200, seed, margin=12)
    for i, (x, y) in enumerate(sorted(pts, key=lambda q: q[1])):
        mk = rk.willow if hash01(x, y, seed + 1) < 0.5 else rk.alder
        sp, sh = mk(i % 2, seed + i) if mk is rk.willow else mk(seed + i)
        rk.paste(p, sp, x, y, shadow=sh)


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


def paint_lullford(R: Region, spec, roads, seed):
    """Lullford on the west bank: cottages of the valley kit (stone variants and colourways
    picked by house_kits.street, so no two neighbours match) in rows along the Lull Road and
    the lane to the bridge, gardens behind with a wall, the street cobbled at the bridge foot.
    Each house blocks its whole footprint in grid cells. Returns {'blocked': mask}."""
    import house_kits as hk
    p = R.p
    blocked = np.zeros(p.f.shape, bool)
    tx, ty, tw, th = spec['town']['rect']
    tx, ty = tx - R.ox, ty - R.oy
    if tx + tw < 0 or ty + th < 0 or tx > R.w or ty > R.h:
        return {'blocked': blocked}
    road = roads
    order = hk.street('valley', 12, seed)
    # plots north of the road (fronts facing the road, south) along the town's width
    slots = []
    for i in range(6):
        x = tx + 16 + i * 72
        yroad = None
        col = road[:, int(np.clip(x + 35, 0, R.w - 1))]
        ys = np.nonzero(col[int(max(0, ty)):int(min(R.h, ty + th))])[0]
        if len(ys):
            yroad = int(ys[0] + max(0, ty))
        if yroad is None:
            continue
        slots.append((x, yroad - 6))
    for i, (x, yb) in enumerate(slots):
        v, cw = order[i % len(order)]
        cv = hk.front('valley', v, cw)
        sp = kit_sprite(cv.img)
        foot = (x + sp.w // 2, yb)
        sh = np.zeros(sp.m.shape, bool)
        sh[:, 4:] = sp.m[:, :-4]
        rk.paste(p, sp, foot[0], foot[1], outline=False, shadow=sh & ~sp.m)
        x0, y0 = foot[0] - sp.w // 2, yb - sp.h + 1
        b = np.zeros(p.f.shape, bool)
        b[max(0, y0 + 8):max(0, yb - 1), max(0, x0 + 2):max(0, x0 + sp.w - 2)] = True
        blocked |= b
    return {'blocked': soft_snap(blocked) if blocked.any() else blocked}


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
    """The plan's own contract: boxes and chunks on the 8 px grid, chunks not overlapping, every
    route exit on its chunk's edge, every named thing, pocket and marker with a point."""
    bad = []
    for k, c in list(plan['boxes'].items()) + list(plan['chunks'].items()):
        if any(v % GRID for v in c['box']):
            bad.append(f'{k}: box off the {GRID} px grid {c["box"]}')
    ch = plan['chunks']['lull-delta']['box']
    for name, r in plan['routes'].items():
        if name.startswith('_'):
            continue
        for e in r.get('exits', []):
            x, y = e['at']
            on = (x in (ch[0], ch[0] + ch[2]) and ch[1] <= y <= ch[1] + ch[3]) or \
                 (y in (ch[1], ch[1] + ch[3]) and ch[0] <= x <= ch[0] + ch[2])
            if not on:
                bad.append(f'{name}: exit {e["at"]} is not on the chunk edge')
    n = {'interactable': 0, 'story': 0, 'ambient': 0}
    for m in plan['markers']:
        n[m['type']] += 1
    if (len(plan['named']), len(plan['pockets']), sum(n.values())) != (18, 7, 217):
        bad.append(f'brief counts changed: {len(plan["named"])} named, {len(plan["pockets"])} pockets, {n}')
    return bad


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
