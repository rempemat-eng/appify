"""The Brackens, painted whole from their plan (Claude F, lane F).

Reads art/regions/brackens.json (the layout, checked by region_plan.py) and paints the region's
box, 800 x 2704 world px, with the moor kit (moor_kit.py) on the river and meadow kit
(river_kit.py), and Claude B's props (valley_props.py) for the named things and the slots:

1. the tier map: each tier outline laid on the 8 px soft grid with its own jogs (benchmark 8:
   no straight edge over 96 px), corners rounded (eastward 1.5), a tier's south rim kept at
   least a face and a cell above the next (so every face is 32 px, never stacked);
2. the ground: heather moor on the ridge and the crest, the gap's short yellowing turf, wet
   flushes, grit; the lip, peat faces between tiers, gritstone on the two bluffs, side bands;
3. the Drover's Road (a drove road: river_kit's track at road width), the trods with frayed
   edges, stone stairs where they change tier;
4. the edges: west, heather and gorse thickening into a gorse and thicket wall; north, grit and
   boulders thickening into the massif's front; walls block, fades do not;
5. growth: gorse, birch in the gills, a few Scots pines, gritstone boulders and tors;
6. story props drawn into the ground (fire rings, a cart, a boot, a hat, tracks, the bell) and
   B's props placed as objects (the sheepfold, the shepherd's hut, the drove well, benches,
   noticeboards, a hurdle, a marker stone, the thicket).

`paint()` returns the arrays; `chunk()` wraps them as a world_canvas.Chunk (registered once
the canvas takes chunks that have no zones, board note f-to-a-1010); `audit()` runs the
world audit's checks on the box directly.

Run: python3 scripts/art/brackens.py [OUT_DIR] [--audit]   (writes brackens.png at 1x, crops
     at 3x and, with --audit, the audit's heat map, to napattack-brackens in the temp folder)
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import moor_kit as mk  # noqa: E402
import region_plan as rp  # noqa: E402
import river_kit as rk  # noqa: E402
from river_kit import IDX, Plot, dilate, erode, fbm, hash01, paste, shift  # noqa: E402

GRID = 8
CELLG = 16        # the tier map's cells: 16 px, so every edge runs at least 16 px (grid-edges)
FACE = 32
PLAN = rp.load('brackens')
X0, Y0, W, H = PLAN['box']
SEED = 4800


def L(pt):
    """World px to the box's own px."""
    return (pt[0] - X0, pt[1] - Y0)


# --- 1. the tier map ----------------------------------------------------------------------------
def jitter_outline(outline, seed, step=48, amp=16):
    """An outline laid on 16 px cells with a jog at least every `step` px: each edge resampled
    every 48 px, every point snapped to 16 px and pushed 16 px in or out where it would
    otherwise line up with the point before (benchmark 8: no edge straight past 96 px).
    Points on the box's edge stay on it."""
    pts = [L(p) for p in outline]
    out = []
    n = len(pts)
    flip = 1

    def q(v):
        return int(round(v / CELLG)) * CELLG
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        Lseg = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(round(Lseg / step)))
        vertical = abs(b[1] - a[1]) >= abs(b[0] - a[0])
        on_edge = (a[0] == b[0] and a[0] in (0, W)) or (a[1] == b[1] and a[1] in (0, H))
        for s_ in range(k):
            t = s_ / k
            x, y = q(a[0] + (b[0] - a[0]) * t), q(a[1] + (b[1] - a[1]) * t)
            if out and not on_edge:
                px, py = out[-1]
                if vertical and x == px and abs(y - py) >= CELLG:
                    flip = -flip if hash01(x // 8, y // 8, seed) < 0.7 else flip
                    x += flip * amp
                elif not vertical and y == py and abs(x - px) >= CELLG:
                    flip = -flip if hash01(x // 8, y // 8, seed) < 0.7 else flip
                    y += flip * amp
            out.append((min(max(x, 0), W), min(max(y, 0), H)))
    return orthogonal(out, seed)


def orthogonal(pts, seed):
    """Every edge turned into a horizontal and a vertical run (Eastward's cliffs are stacks of
    rectangles in plan, eastward-edges 1.5): a slope becomes steps whose treads are south
    rims with a face and whose risers are side bands, never a diagonal of stacked faces."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        out.append(a)
        if a[0] != b[0] and a[1] != b[1]:
            first_h = hash01(a[0] // 8, a[1] // 8, seed + 77) < 0.5
            out.append((b[0], a[1]) if first_h else (a[0], b[1]))
    return notch(merge(out), seed)


def merge(pts):
    """Drop repeated points and points in the middle of a straight run."""
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]
    out = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        if (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
            continue
        out.append(b)
    return out


def notch(pts, seed, longest=96, piece=64, d=16):
    """Break every axis-aligned run longer than `longest` into pieces of about `piece` px that
    step 16 px out and back (benchmark 8), alternating sides by a hash."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        out.append(a)
        Lx, Ly = b[0] - a[0], b[1] - a[1]
        L_ = abs(Lx) + abs(Ly)
        if L_ <= longest or (Lx and Ly):
            continue
        on_edge = (Lx == 0 and a[0] in (0, W)) or (Ly == 0 and a[1] in (0, H))
        if on_edge:
            continue
        k = int(round(L_ / piece))
        k += k % 2 == 0          # odd: out, back, out ... back, so the run ends where it began
        sgn = 1 if hash01(a[0] // 8, a[1] // 8, seed + 5) < 0.5 else -1
        ux, uy = (np.sign(Lx), np.sign(Ly))
        nx, ny = -uy * sgn * d, ux * sgn * d
        for j in range(1, k):
            t = round(L_ * j / k / CELLG) * CELLG
            px, py = a[0] + ux * t, a[1] + uy * t
            o0 = (j - 1) % 2
            o1 = j % 2
            out.append((int(px + nx * o0), int(py + ny * o0)))
            out.append((int(px + nx * o1), int(py + ny * o1)))
    return out


def tier_cells(seed=SEED):
    """The screen tier map on 8 px cells, and which cells belong to a rock (bluff) tier."""
    cw, ch = W // CELLG, H // CELLG
    T = np.zeros((ch, cw), np.int16)
    rock = np.zeros((ch, cw), bool)
    for i, t in enumerate(sorted(PLAN['tiers'], key=lambda t: t['tier'])):
        img = Image.new('L', (cw, ch), 0)
        poly = [(x / CELLG - 0.5, y / CELLG - 0.5) for x, y in jitter_outline(t['outline'], seed + i)]
        ImageDraw.Draw(img).polygon(poly, fill=1)
        m = np.asarray(img).astype(bool)
        T[m] = np.maximum(T[m], t['tier'])
        if t.get('face') == 'rock':
            rock |= m
    # every rim keeps a face and a cell of lower ground under it before the next drop, and
    # every tier is at least two cells wide (no slivers): erode what breaks the rule
    k = FACE // CELLG + 1
    for _ in range(40):
        bad = np.zeros_like(T, bool)
        for r in range(ch - 1):
            rim = T[r] > T[r + 1]
            for d in range(2, k + 1):
                if r + d >= ch:
                    break
                bad[r] |= rim & (T[r + d] < T[r + 1])
        left, right = np.roll(T, 1, 1), np.roll(T, -1, 1)
        sliver = (T > left) & (T > right)
        up, down = np.roll(T, 1, 0), np.roll(T, -1, 0)
        sliver |= (T > up) & (T > down)
        bad |= sliver
        if not bad.any():
            break
        T[bad] = np.maximum(T[bad] - 1, 0)
    return T, rock & (T >= 1)


def tier_px(T8):
    """The tier map at 1 px: cells upsampled, outer corners rounded (radius 3) and inner
    corners chamfered (1 to 2), as eastward-edges 1.5 measures them."""
    T = np.repeat(np.repeat(T8, CELLG, 0), CELLG, 1)
    out = np.zeros_like(T)
    for t in range(1, int(T.max()) + 1):
        m = T >= t
        m = dilate(erode(m, 3), 3) | (m & erode(m, 1))     # round outer corners (open)
        m = erode(dilate(m, 2), 2) & (T >= t - 1)           # fill inner corners a little (close)
        out += m.astype(np.int16)
    return np.minimum(out, T + 0)


# --- 2. to 6. painting --------------------------------------------------------------------------
class Painted:
    pass


def _poly_mask(outline, shape):
    img = Image.new('L', (shape[1], shape[0]), 0)
    ImageDraw.Draw(img).polygon([L(p) for p in outline], fill=1)
    return np.asarray(img).astype(bool)


def paint(seed=SEED) -> Painted:
    import time
    t0 = time.time()

    def tick(what):
        if os.environ.get('BRACKENS_TIMING'):
            print(f'  {what}: {time.time() - t0:.1f} s', flush=True)
    p = Plot(W, H)
    T8, rock8 = tier_cells(seed)
    T = tier_px(T8)
    rockpx = np.repeat(np.repeat(rock8, CELLG, 0), CELLG, 1)
    tick('face, depth, height,')
    face, depth, height, upper = mk.face_depth(T)
    top = ~face
    # ground on the tops
    crest = top & (T >= 2) & ~rockpx
    ridge = top & (T == 1)
    floor = top & (T == 0)
    mk.run_windowed(p, floor, lambda q, m: mk.turf(q, m, seed + 1, yellow=0.55))
    westish = np.clip((p.x - 200) / 500.0, 0, 1)      # yellower towards the steppe in the west
    dry = floor & (fbm(p.x, p.y, 40, seed + 2) > 0.35 + 0.4 * westish)
    p.f[dry] = np.where(hash01(p.x // 3, p.y // 2, seed + 3) < 0.5, IDX['sand_warm'], IDX['grass_warm'])[dry]
    # the sheep's walks: short turf along the trods and the road, the heather standing back
    near_path = np.zeros((H, W), bool)
    for r in PLAN['routes'] + PLAN['trods']:
        d, _ = mk.polyline_dist(p, [L(q) for q in r['points']], 48)
        near_path |= d < r['width'] / 2 + 10 + 18 * fbm(p.x, p.y, 23, seed + 4)
    mk.run_windowed(p, ridge & ~near_path, lambda q, m: mk.moor(q, m, seed + 10, heather=0.5, bracken=0.34, grit=0.04))
    mk.run_windowed(p, (crest | (top & rockpx)) & ~near_path,
                    lambda q, m: mk.moor(q, m, seed + 20, heather=0.68, bracken=0.06, grit=0.16))
    mk.run_windowed(p, (ridge | crest) & near_path, lambda q, m: mk.turf(q, m, seed + 25, yellow=0.2))
    wet = (ridge | crest) & (fbm(p.x, p.y, 70, seed + 30) > 0.78) & (T < 3) & ~near_path
    mk.run_windowed(p, wet, lambda q, m: mk.flush(q, m, seed + 31))
    # lip, faces, side bands
    tick('rimrow = top & shift')
    rimrow = top & shift(face, 0, -1, False)
    mk.lip(p, rimrow, seed + 40)
    # a face is rock where the tier above its rim is a bluff
    yy = np.clip(p.y - depth - 1, 0, H - 1)
    rockface = face & rockpx[yy, p.x]
    mk.grit_face(p, rockface, depth, height, seed + 41)
    east_facing = np.zeros_like(face)
    mk.peat_face(p, face & ~rockface, depth, height, seed + 42, east=east_facing)
    band, band_f = mk.side_bands(p, T, face, rockpx, seed + 43)
    walk = top & ~band
    # paths
    tick('path_mask = np.zeros')
    path_mask = np.zeros((H, W), bool)
    stairs_mask = np.zeros((H, W), bool)
    for r in PLAN['routes']:
        x0, y0, ch = mk.in_box(p, [L(q) for q in r['points']], 48,
                               lambda win, pts: rk.track(win, pts, width=r['width'], seed=seed + 50, puddles=3))
        path_mask[y0:y0 + ch.mask.shape[0], x0:x0 + ch.mask.shape[1]] |= ch.mask
    for i, t in enumerate(PLAN['trods']):
        def one(win, pts, i=i, t=t):
            gm = (top & ~band)[win.y0:win.y0 + win.h, win.x0:win.x0 + win.w]
            return mk.trod(win, pts, t['width'], seed + 60 + i, ground_mask=gm)
        x0, y0, m = mk.in_box(p, [L(q) for q in t['points']], 32, one)
        path_mask[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] |= m
    for i, st in enumerate(PLAN['stairs']):
        x, y = L(st['at'])
        col = face[:, x]
        ys = np.nonzero(col[max(0, y - 48):y + 48])[0]
        if not len(ys):
            continue
        y_top, y_bot = max(0, y - 48) + ys[0], max(0, y - 48) + ys[-1]
        sm = mk.stair(p, (x // 8) * 8, y_top - 2, y_bot + 1, st['width'], seed + 70 + i)
        stairs_mask |= sm
    tick('walk |= stairs_mask')
    walk |= stairs_mask
    walk &= ~(face & ~stairs_mask)
    # edges: walls and fades
    taken = dilate(path_mask | stairs_mask, 6) | dilate(face, 2) | band
    wall, fade = edge_masks(p, T, seed + 80)
    walk &= ~wall
    tick('grow(p, wall')
    blockers = grow(p, wall, fade, top & ~band, taken, T, seed + 90)
    walk &= ~blockers
    # no lone pixels where growth overlaps (house rule 4): glints (tone 5) stay
    mk.run_windowed(p, ~face, lambda q, m: rk.despeckle(q, m, passes=3))
    tick('objs, decal_feet')
    objs, decal_feet = place_things(p, top & ~band, taken, seed + 120)
    for (_id, key, x, y, w, h) in objs:
        # the foot band on 16 px cells: the middle two thirds of the sprite, its last 16 px
        fx, fy = x + w // 2, y + h - 2
        bx0, bx1 = ((fx - w // 3) // 16) * 16, -(-(fx + w // 3) // 16) * 16
        by = ((fy - 4) // 16) * 16
        walk[by:by + 16, max(0, bx0):bx1] = False
    out = Painted()
    out.p, out.T, out.T8, out.face, out.band, out.walk = p, T, T8, face, band, walk & p.walk | (walk & path_mask)
    out.walk = walk
    out.stairs, out.path, out.objects, out.wall = stairs_mask, path_mask, objs, wall
    out.band_f = band_f
    return out


def edge_masks(p: Plot, T, seed):
    """The west and north borders in their three layers (plan 5.5): a wall 64 to 180 px deep
    of the moor's own blockers, a fade of thinning clumps 160 px beyond it. Returns (wall,
    fade strength 0..1)."""
    y, x = p.y, p.x
    q = 16                                                # walls lie on 16 px cells (grid-edges)
    yq, xq = (y // q) * q, (x // q) * q
    wl = (72 + 108 * fbm(0 * xq, yq // 48 * 48, 90, seed)) // q * q   # the west wall's depth by 48 px rows
    wl = wl + q * ((yq // 48) % 3 - 1)                                 # a jog every row band (benchmark 8)
    west_on = (y < L((0, 3392))[1]) & (T >= 1)
    beyond = L((0, PLAN.get('north_beyond', {}).get('to_y', Y0)))[1]
    nwall = (beyond - 60 + 120 * fbm(xq // 48 * 48, 0 * yq, 80, seed + 1)) // q * q   # the north wall's foot
    nwall = nwall + q * ((xq // 48) % 3 - 1)
    wall = (west_on & (xq < wl)) | (yq < nwall)
    dw = np.where(west_on, x - wl, 999)
    dn = y - nwall
    d = np.minimum(dw, dn)
    fade = np.clip(1 - d / 160.0, 0, 1) * (d >= 0)
    return wall, fade


def grow(p: Plot, wall, fade, ground, taken, T, seed):
    """Gorse and thicket packed into the west wall, grit and boulders into the north one,
    clumps thinning through the fade, and the moor's own growth scattered over the rest."""
    taken = taken.copy()
    blockers = np.zeros(taken.shape, bool)
    y, x = p.y, p.x

    def put(maker, xx, yy, s, block=True):
        nonlocal taken
        sp, sh = maker(s)
        full, x0, y0 = mk.paste_at(p, sp, xx, yy, shadow=sh)
        h_, w_ = full.shape
        taken[y0:y0 + h_, x0:x0 + w_] |= dilate(full, 2)
        if block:                                   # its foot: one 16 px cell (grid-edges)
            bx, by = (xx // 16) * 16, ((yy - 4) // 16) * 16
            blockers[by:by + 16, bx:bx + 16] = True
    west = wall & (x < 260)
    north = wall & ~west
    # the walls: blockers every 12 to 16 px in uneven patches, never three alike in a row
    makers_w = [lambda s: mk.gorse(s, 2), lambda s: mk.gorse(s, 1), lambda s: rk.shrub('bramble', s),
                lambda s: mk.gorse(s, 0), lambda s: mk.gritstone(1, s)]
    makers_n = [lambda s: mk.gritstone(2, s), lambda s: mk.gritstone(1, s), lambda s: mk.gorse(s, 1),
                lambda s: mk.gritstone(0, s)]
    for region, makers, every, sd in ((west, makers_w, 300, seed), (north, makers_n, 300, seed + 1)):
        last = []
        for (xx, yy) in rk._scatter(region, every, sd, margin=0):
            if taken[yy, xx]:
                continue
            k = int(hash01(xx, yy, sd + 2) * len(makers))
            if len(last) >= 2 and last[-1] == last[-2] == k:
                k = (k + 1) % len(makers)
            last.append(k)
            put(makers[k], xx, yy, sd + xx * 7 + yy)
    # the fades: the same clumps thinning out
    for (xx, yy) in rk._scatter(ground & ~wall & (fade > 0), 520, seed + 3):
        if taken[yy, xx] or hash01(xx, yy, seed + 4) > fade[yy, xx]:
            continue
        put(makers_w[int(hash01(xx, yy, seed + 5) * 3)] if x[0, xx] < 300 else makers_n[int(hash01(xx, yy, seed + 5) * 4)],
            xx, yy, seed + xx + yy * 3)
    # the moor's growth: gorse on the flanks, birches in the gills on the east flank, a few
    # Scots pines, gritstone on the crest
    open_ = ground & ~wall & (fade == 0)
    flank = open_ & (T == 1)
    for (xx, yy) in rk._scatter(flank, 5200, seed + 6):
        if not taken[yy, xx]:
            put(lambda s: mk.gorse(s, int(hash01(s, 0, 1) * 3)), xx, yy, seed + xx * 3 + yy)
    gill = open_ & (x > 640) & (T == 1)
    for (xx, yy) in rk._scatter(gill, 9000, seed + 7):
        if not taken[yy, xx]:
            put(lambda s: rk.birch(s), xx, yy, seed + xx + yy)
    for (xx, yy) in rk._scatter(open_ & (T >= 1), 60000, seed + 8):
        if not taken[yy, xx]:
            put(lambda s: mk.scots_pine(s, 0.9 + 0.2 * hash01(s, 1, 2)), xx, yy, seed + xx + 2 * yy)
    for (xx, yy) in rk._scatter(open_ & (T >= 2), 11000, seed + 9):
        if not taken[yy, xx]:
            put(lambda s: mk.gritstone(int(hash01(s, 3, 4) * 3), s), xx, yy, seed + 3 * xx + yy)
    return blockers


SLOT_SPRITES = {
    'bench': ['bench_stone', 'bench_oak'],
    'noticeboard': ['noticeboard_roofed', 'noticeboard_box'],
    'mended fence': ['wattle_hurdle', 'wattle_hurdle_low'],
    'marker stone': ['standing_stone_low'],
    'cairn': ['cairn_trail', 'cairn_tall'],
    'standing stone': ['standing_stone'],
    'offering stone': ['offering_stone'],
    'signpost': ['signpost_old'],
    'water trough': ['trough_stone'],
}
NAMED_SPRITES = {
    'sheepfold': 'sheepfold',
    "shepherd's hut": 'shepherds_hut',
    'drove well': 'well_open',
    'a broken sheepfold': 'drystone_wall_short',
}
DECALS = {
    'cart with a broken wheel': mk.cart_wreck,
    'old boot': mk.boot,
    'lost hat': mk.hat,
    'cold fire ring': mk.fire_ring,
}


def sprite_map():
    import valley_props
    return valley_props.props()


def place_things(p: Plot, ground, taken, seed):
    """B's props as objects (top-left in box px, as zones place them) and the small story
    props drawn into the ground. Returns (objects, decal feet)."""
    sprites = sprite_map()
    objs = []
    feet = []

    def obj(oid, key, at):
        cv = sprites[key]
        w, h = cv.img.width, cv.img.height
        fx, fy = L(at)
        objs.append((oid, key, int(fx - w // 2), int(fy - h + 2), w, h))
    for n in PLAN['named']:
        key = NAMED_SPRITES.get(n['thing'])
        if key:
            obj('brackens:' + key, key, n['at'])
    count = {}
    for m in PLAN['markers']:
        if m.get('outside_box'):
            continue
        what = m['what']
        count[what] = count.get(what, 0) + 1
        if what in SLOT_SPRITES:
            opts = SLOT_SPRITES[what]
            obj(f'brackens:{what.replace(" ", "_")}_{count[what]}', opts[count[what] % len(opts)], m['at'])
        elif what in DECALS:
            sp, sh = DECALS[what]()
            x, y = L(m['at'])
            mk.paste_at(p, sp, x, y, outline=False, shadow=sh)
            feet.append((x, y))
        elif what == 'tracks':
            x, y = L(m['at'])
            win = mk.Window(p, max(0, x - 14), max(0, y - 8), min(W, x + 14), min(H, y + 8))
            mk.hoofprints(win, ground[win.y0:win.y0 + win.h, win.x0:win.x0 + win.w], seed + x)
    for o in PLAN['obstacles']:
        if o['kind'] == 'thicket':
            obj('brackens:thicket', 'thicket_big', o['at'])
    for pk in PLAN['pockets']:
        x, y = L(pk['at'])
        if 'bell' in pk['holds']:
            sp, _ = mk.bell()
            mk.paste_at(p, sp, x, y, outline=False)
        else:
            sp, _ = mk.fire_ring(lit=True)
            mk.paste_at(p, sp, x, y, outline=False)
        feet.append((x, y))
    return objs, feet


# --- the tier rows, the chunk and the audit ------------------------------------------------------
def tier_rows(P: Painted):
    """One character per 4 px cell: a digit for the tier, 'f' a face or side band, 's' a stair."""
    c = 4
    ny, nx = H // c, W // c

    def share(m):
        return m.reshape(ny, c, nx, c).mean((1, 3))
    fs = share(P.face | getattr(P, 'band_f', P.band))
    ss = share(P.stairs)
    t = np.round(P.T.reshape(ny, c, nx, c).mean((1, 3))).astype(int)
    rows = []
    for r in range(ny):
        rows.append(''.join('s' if ss[r, q] >= 0.5 else 'f' if fs[r, q] >= 0.5 else str(t[r, q]) for q in range(nx)))
    return rows


def chunk(P: Painted | None = None):
    import world_canvas as wc
    P = P or paint()
    ch = wc.Chunk('brackens', W, H, plane='continent', origin=(X0, Y0))
    ch.ground = P.p.image().convert('RGBA')
    ch.objects = [(oid, key, x, y) for (oid, key, x, y, w, h) in P.objects]
    ys, xs = np.nonzero(~P.walk)
    ch.blocked = set(zip(xs.tolist(), ys.tolist()))
    ch.water = set()
    ch.tiers = tier_rows(P)
    ch.areas = [{'id': a['id'], 'kind': 'zone', 'rect': tuple(v - o for v, o in zip(a['rect'], (X0, Y0, 0, 0)))}
                for a in PLAN['areas'] if a.get('walkable', True)]
    return ch


def audit(P: Painted, out: str | None = None, ledger: str | None = None):
    """The world audit's checks on the box (scripts/art/world_audit.py), with B's sprites
    written to a scratch folder so the sprite checks can read them. Returns the Audit."""
    import world_audit as wa
    R = wa.Region('brackens', 'continent', W, H, (X0, Y0))
    R.ground = np.asarray(P.p.image().convert('RGBA')).copy()
    c = wa.WALK
    ny, nx = H // c, W // c
    blocked = (~P.walk).reshape(ny, c, nx, c).mean((1, 3)) >= 0.5
    R.terrain = np.where(blocked, wa.WALL, wa.GROUND).astype(np.uint8)
    R.walk = ~blocked
    R.tiers = np.array([[ord(ch) for ch in row] for row in tier_rows(P)], np.uint8)
    tmp = os.path.join(out or tempfile.gettempdir(), 'brackens-sprites')
    os.makedirs(tmp, exist_ok=True)
    sprites = sprite_map()
    for (oid, key, x, y, w, h) in P.objects:
        png = os.path.join(tmp, f'{key}.png')
        if not os.path.exists(png):
            im = sprites[key].img
            im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(png)
        R.props.append({'id': oid, 'sprite': key, 'x': x, 'y': y, 'w': w, 'h': h, 'png': png, 'place': -1,
                        'overhead': False, 'source': 'world'})
    for a in PLAN['areas']:
        if a.get('walkable', True):
            x, y, w, h = a['rect']
            R.add_place(wa.Place(a['id'], 'area', 'brackens', 'brackens', (x - X0, y - Y0, w, h)))
    for pr in R.props:
        fx, fy = pr['x'] + pr['w'] // 2, pr['y'] + pr['h'] - 2
        pr['place'] = next((i for i, pl in enumerate(R.places) if pl.rect[0] <= fx < pl.rect[0] + pl.rect[2]
                            and pl.rect[1] <= fy < pl.rect[1] + pl.rect[3]), -1)
    ctx = wa.make_context(ROOT, ledger)
    ctx['source'] = 'world'
    ctx['root'] = ROOT
    A = wa.Audit(R, ctx).run()
    return A, R


def summary(A) -> str:
    import world_audit as wa
    art = A.worst != wa.NA
    n = int(art.sum())
    g = int((A.worst == wa.PASS)[art].sum())
    red = int((A.worst == wa.RED)[art].sum())
    lines = [f'brackens audit: {n} cells, {100 * g / max(1, n):.1f} % green, {red} red, {n - g - red} amber']
    for c in wa.CHECK_IDS:
        st = A.status[c]
        meas = int(((st != wa.NA) & art).sum())
        r = int(((st == wa.RED) & art).sum())
        a = int(((st == wa.AMBER) & art).sum())
        if r or a:
            lines.append(f'  {c:13s} measured {meas:5d}  red {r:5d}  amber {a:5d}')
    return '\n'.join(lines)


def main(argv) -> int:
    args = [a for a in argv if not a.startswith('--')]
    out = args[0] if args else os.path.join(tempfile.gettempdir(), 'napattack-brackens')
    os.makedirs(out, exist_ok=True)
    import pickle
    cache = os.path.join(out, 'painted.pkl')
    if '--cached' in argv and os.path.exists(cache):
        with open(cache, 'rb') as fh:
            P = pickle.load(fh)
    else:
        P = paint()
        with open(cache, 'wb') as fh:
            pickle.dump(P, fh)
    img = P.p.image()
    sprites = sprite_map()
    comp = img.convert('RGBA')
    for (oid, key, x, y, w, h) in sorted(P.objects, key=lambda o: o[3] + o[5]):
        comp.alpha_composite(sprites[key].img, (x, y))
    comp.save(os.path.join(out, 'brackens.png'))
    for name, (x, y) in (('gap', (232, 2240)), ('well', (160, 1900)), ('flank', (480, 900)), ('north', (240, 60))):
        comp.crop((x, y, x + 320, y + 288)).resize((960, 864), Image.NEAREST).save(os.path.join(out, f'crop-{name}-3x.png'))
    print(f'brackens: {len(P.objects)} objects, walkable {P.walk.mean() * 100:.0f} %')
    if '--audit' in argv:
        A, R = audit(P, out)
        print(summary(A))
        import collections
        import json
        import re as _re
        import world_audit as wa
        wa.heat(A).save(os.path.join(out, 'audit-heat.png'))
        why = collections.Counter()
        for (c, cy, cx), w in A.why.items():
            if A.status[c][cy, cx] > wa.PASS:
                why[(c, _re.sub(r'[0-9.]+', '#', w)[:90])] += 1
        with open(os.path.join(out, 'audit-why.json'), 'w') as fh:
            json.dump([[c, w, n] for (c, w), n in why.most_common(60)], fh, indent=0)
        cells = [[c, int(cx) * 32, int(cy) * 32, w] for (c, cy, cx), w in A.why.items() if A.status[c][cy, cx] > wa.PASS
                 and c not in ('density', 'landmark')]
        with open(os.path.join(out, 'audit-cells.json'), 'w') as fh:
            json.dump(cells, fh)
        for f in A.findings[:40]:
            print('  finding', f)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
