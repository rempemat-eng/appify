"""The undercroft kit: an old stone vault under the valley, drawn natively at any density in palette
codes only (the Undercroft, docs/vision/vertical-slice.md beat 6; game/data/plans/undercroft.json).

The house rules indoors: light still falls from the upper left on every block, plinth and lip, so
forms read; on top of that the torches throw warm pools and the skylight shaft a cool one, and the
corners far from both sink a step. Walls are blocks on the 8 px soft grid (eastward-edges.md 1 and
2): a top (the soil and coping over the vault, a lit lip where it breaks to the face) and a south
face 40 world px tall (a cliff-height face, 2.1: at least 1.3 people) built as a blind arcade:
cornice, voussoired arches over shaded recesses, pilasters with imposts, a plinth with a dark
foot. The oak's roots split some bays (cracks, a displaced block, rootlets) and run on over the
floor. Floors are flagstones in 8 px courses (Eastward's tile, 1.1) with lit arrises, joints,
chips, cracks and moss in the damp joints.

    python3 -m scripts.art.native.undercroft --plan game/data/plans/undercroft.json --density 3 \\
        --out game/zones/undercroft/art --preview DIR

writes <out>/ground.png, one picture per object (props, the torch sheet, the seal, the plate and
lever in both states, Cairn's alcove, the channel lit) and <out>/../kit.json with every object's
foot, offset, condition, collision box and kind; game/tools/gen_undercroft.py writes the scene.
Units: plan positions are world px; pictures and kit.json are texels (world px x density).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import ctx  # noqa: E402

INPUTS = ('undercroft.py', 'village.py', 'palette.py', 'ctx.py')
STONES = ('stone', 'stone_warm', 'stone_cool')
CAIRN = os.path.join(ROOT, 'game', 'assets', 'characters', 'cairn', 'sheets', 'defeat_S.png')
TORCH_FRAMES = 4


def input_hash(plan_path: str, density: float) -> str:
    h = hashlib.sha256(('density %g\n' % density).encode())
    files = [os.path.join(HERE, f) for f in INPUTS] + [plan_path, CAIRN, os.path.join(ROOT, 'art', 'house-palette.json')]
    for f in files:
        h.update(os.path.relpath(f, ROOT).encode() + b'\0')
        h.update(open(f, 'rb').read())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------
# painters (need ctx configured: they read the density through village.q)
# ------------------------------------------------------------------------------------------------
def _v():
    from scripts.art.native import village as V
    return V


def line_mask(shape, pts, r=0.6):
    V = _v()
    m = np.zeros(shape, bool)
    for (a, b), (c, d) in zip(pts, pts[1:]):
        m |= V.seg_mask(shape, a, b, c, d, r)
    return m


def flagstones(cv, x0, y0, x1, y1, rng, where):
    """Flagstones on the 8 px soft grid (Eastward's tile, eastward-edges.md 1.1): square slabs and
    slabs of two or four cells, each its own tone and sibling, a lit top and west arris, a dark
    foot and east edge, thin dark joints; some chipped, cracked or worn hollow. Returns the slab
    id of every texel (0 for joints), so light can fall slab by slab."""
    V = _v()
    q, code = V.q, V.code
    sub = np.zeros(cv.shape, bool)
    sub[y0:y1, x0:x1] = True
    where = where & sub
    ids = np.zeros(cv.shape, np.int32)
    V.fill(cv, x0, y0, x1, y1, code('stone_cool', 0), where)
    c = q(8)
    nx, ny = (x1 - x0 + c - 1) // c, (y1 - y0 + c - 1) // c
    used = np.zeros((ny, nx), bool)
    sid = 0
    for j in range(ny):
        for i in range(nx):
            if used[j, i]:
                continue
            opts = [(1, 1)] * 4 + [(2, 1)] * 3 + [(1, 2)] * 2 + [(2, 2)] * 2
            cw, chh = opts[int(rng.integers(0, len(opts)))]
            if i + cw > nx or used[j, i:i + cw].any():
                cw = 1
            if j + chh > ny or used[j:j + chh, i:i + cw].any():
                chh = 1
            used[j:j + chh, i:i + cw] = True
            sx0, sy0 = x0 + i * c + 1, y0 + j * c + 1
            sx1, sy1 = min(x1, x0 + (i + cw) * c), min(y1, y0 + (j + chh) * c)
            if sx1 - sx0 < 4 or sy1 - sy0 < 4:
                continue
            sid += 1
            fam = str(rng.choice(['stone', 'stone', 'stone_warm', 'stone_warm', 'stone_cool']))
            t = 1 + int(rng.choice([0, 0, 0, 0, 0, 0, 0, 1]))
            m = np.zeros(cv.shape, bool)
            m[sy0:sy1, sx0:sx1] = V.chamfer(sy1 - sy0, sx1 - sx0, 1)
            m &= where
            ids[m] = sid
            V.blk(cv, sx0, sy0, sx1, sy1, fam, t, cut=1, where=where)
            r = rng.random()
            cx = int(rng.integers(sx0 + 3, max(sx0 + 4, sx1 - 3)))
            cy = int(rng.integers(sy0 + 3, max(sy0 + 4, sy1 - 4)))
            if r < 0.2:            # a crack: a dark line with a lit lower lip
                pts = [(cx, cy)]
                for _ in range(3):
                    pts.append((pts[-1][0] + int(rng.integers(-q(3), q(3) + 1)), pts[-1][1] + int(rng.integers(1, q(2)))))
                lm = line_mask(cv.shape, pts, 0.6) & m
                lip = np.roll(lm, 1, 0) & ~lm & m
                cv[lip] = code(fam, min(5, t + 1))
                cv[lm] = code(fam, max(0, t - 2))
            elif r < 0.5:           # chips: pairs of dark texels with a lit rim above
                for _k in range(int(rng.integers(1, 4))):
                    px = int(rng.integers(sx0 + 2, max(sx0 + 3, sx1 - 3)))
                    py = int(rng.integers(sy0 + 3, max(sy0 + 4, sy1 - 3)))
                    V.fill(cv, px, py, px + 2, py + 2, code(fam, max(0, t - 1)), m)
                    V.fill(cv, px, py - 1, px + 2, py, code(fam, min(5, t + 1)), m)
            elif r < 0.6:           # worn hollow: a smooth lighter patch
                hm = V.ellipse_mask(cv.shape, cx, cy, q(2.6), q(1.6)) & m
                tt = (cv[hm] % 8)
                cv[hm] = np.where(tt < 6, (cv[hm] // 8) * 8 + np.minimum(5, tt + 1), cv[hm])
    return ids


def mottle(cv, mask, rng, sigma=2.4, sib_share=0.12):
    """Stone grain inside the pieces of a surface: soft clusters a tone lighter or darker and patches
    on a sibling ramp (warm or cool), never smaller than two texels, so a slab or block reads as worn
    stone and not as a flat fill (art-style.md: Eastward's detail per patch)."""
    from .palette import sib
    H, W = cv.shape
    n1 = ndi.gaussian_filter(rng.random((H, W)), sigma)
    n1 = (n1 - n1.mean()) / (n1.std() + 1e-9)
    n2 = ndi.gaussian_filter(rng.random((H, W)), sigma * 2.2)
    n2 = (n2 - n2.mean()) / (n2.std() + 1e-9)
    t = cv % 8
    ok = mask & (cv >= 0) & (t >= 1) & (t <= 4)
    dn = ok & (n1 < -1.45)
    up = ok & (n1 > 1.6) & (t <= 3)
    cv[dn] = cv[dn] - 1
    cv[up] = cv[up] + 1
    thr = np.quantile(n2[ok], 1 - sib_share) if ok.any() else 9
    sw = ok & (n2 > thr)
    cv[sw] = sib(cv[sw], 'warm' if rng.random() < 0.5 else 'cool')
    sw2 = ok & (n2 < -thr)
    cv[sw2] = sib(cv[sw2], 'cool')


def cut_block(a, x0, y0, x1, y1, top, fam, t, rng=None, bevel=1, grain=True):
    """A dressed stone block seen like everything in the world (3/4 from above, light upper left):
    a top face `top` texels deep a tone lighter with a lit back arris, a bevel catching the light
    along the front edge, the front face shading down to a dark foot, the east end a step darker,
    and stone grain in both faces. x0..x1, y0..y1 is the whole drawn block in texels."""
    V = _v()
    code = V.code
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    yt = y0 + int(top)
    if yt > y0:
        V.blk(a, x0, y0, x1, yt, fam, min(5, t + 1), cut=1, top=1, left=1, bot=0, right=-1)
    V.blk(a, x0, yt, x1, y1, fam, t, cut=1, top=0, left=1, bot=-1, right=-1)
    for k in range(bevel):
        V.fill(a, x0 + 1, yt + k, x1 - 1, yt + k + 1, code(fam, min(5, t + 2) if k == 0 else min(5, t + 1)))
    V.fill(a, x0 + 1, y1 - 2, x1 - 1, y1 - 1, code(fam, max(0, t - 1)))
    V.fill(a, x1 - max(2, (x1 - x0) // 6), yt + bevel, x1 - 1, y1 - 2, code(fam, max(0, t - 1)))
    if grain and rng is not None and (x1 - x0) * (y1 - y0) > 60:
        m = np.zeros(a.shape, bool)
        m[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = True
        mottle(a, m, rng, sigma=1.3, sib_share=0.1)


def masonry(cv, x0, y0, x1, y1, rng, where, base=2, course=5.0, length=(8, 14), east_dark=True):
    """Dressed wall stone in courses, every block lit on its top and west arris."""
    V = _v()
    q, code = V.q, V.code
    V.fill(cv, x0, y0, x1, y1, code('stone_cool', 0), where)
    y, k = y1, 0
    while y > y0 + 1:
        h = q(course)
        yt = max(y0, y - h)
        x = x0 - (q(length[0] / 2) if k % 2 else 0) - int(rng.integers(0, q(3)))
        while x < x1:
            L = q(rng.uniform(*length))
            t = base + int(rng.choice([-1, 0, 0, 0, 1]))
            if east_dark and x > x0 + 0.72 * (x1 - x0) and rng.random() < 0.5:
                t -= 1
            sx0, sx1 = max(x, x0), min(x + L - 1, x1)
            if sx1 - sx0 >= 3:
                V.blk(cv, sx0, yt, sx1, y - 1, STONES[int(rng.integers(0, 3))], max(0, t), cut=1, where=where)
            x += L
        y = yt
        k += 1


def root(cv, pts, r0, r1, where, rng, fam='earth_warm', base=2, lets=4):
    """A root along pts tapering r0 to r1 texels, lit on its west side, with thin rootlets."""
    V = _v()
    n = len(pts) - 1
    m = np.zeros(cv.shape, bool)
    for i, ((a, b), (c, d)) in enumerate(zip(pts, pts[1:])):
        ra = r0 + (r1 - r0) * i / n
        m |= V.seg_mask(cv.shape, a, b, c, d, ra)
    m &= where
    for _ in range(lets):
        i = int(rng.integers(0, len(pts)))
        x, y = pts[i]
        side = 1 if rng.random() < 0.5 else -1
        L = V.q(rng.uniform(4, 9))
        tip = (x + side * L, y + V.q(rng.uniform(2, 6)))
        mid = ((x + tip[0]) / 2, y + V.q(1) * side * 0.3)
        lm = line_mask(cv.shape, [(x, y), mid, tip], 0.7) & where & ~m
        cv[lm] = V.code(fam, base - 1)
    tt = V.shade(m, base, top=0, left=1, bot=0, right=-1)
    cv[m] = V.FI[fam] * 8 + tt[m]
    # bark: short darker strokes along the root
    ys, xs = np.nonzero(m)
    for k in range(0, len(ys), 23):
        if rng.random() < 0.5:
            cv[ys[k]:ys[k] + 2, xs[k]] = V.code(fam, max(0, base - 1))
    return m


# ------------------------------------------------------------------------------------------------
# walls: tops and faces
# ------------------------------------------------------------------------------------------------
def wall_top(cv, x0, y0, x1, y1, rng, where):
    """The soil and rubble over the vault seen from above: dark, stony, root-veined."""
    V = _v()
    V.rubble(cv, x0, y0, x1, y1, rng, fams=('stone_cool', 'stone_cool', 'stone'), base=1, course=(3.0, 4.4),
             length=(4, 9), moss=0.04, east_dark=False, where=where, mortar=('earth_cool', 0))
    for _ in range(max(1, (x1 - x0) * (y1 - y0) // 12000)):
        ax = int(rng.integers(x0, max(x0 + 1, x1)))
        ay = int(rng.integers(y0, max(y0 + 1, y1)))
        pts = [(ax, ay)]
        for _k in range(4):
            pts.append((pts[-1][0] + int(rng.integers(-V.q(6), V.q(6))), pts[-1][1] + int(rng.integers(-V.q(3), V.q(4)))))
        root(cv, pts, V.q(0.9), V.q(0.5), where, rng, base=1, lets=1)


def wall_face(cv, x0, y0, x1, y1, rng, where, roots=(), arcade=True):
    """A south face of the vault: cornice, blind arcade (pilasters, voussoired arches over shaded
    recesses), plinth and a dark foot. x0..x1, y0..y1 in texels."""
    V = _v()
    q, code = V.q, V.code
    masonry(cv, x0, y0, x1, y1, rng, where, base=2)
    corn, plin = q(3), q(5)
    # the plinth: a course of big blocks, lit top arris, a dark foot row
    masonry(cv, x0, y1 - plin, x1, y1, rng, where, base=2, course=5, length=(12, 18))
    V.fill(cv, x0, y1 - plin, x1, y1 - plin + 1, code('stone', 4), where)
    V.fill(cv, x0, y1 - 2, x1, y1, code('stone_cool', 0), where)
    if arcade and x1 - x0 >= q(40):
        bay, pil = q(48), q(8)
        n = max(1, int(round((x1 - x0) / bay)))
        bw = (x1 - x0) / n
        for i in range(n):
            bx0 = int(x0 + i * bw)
            bx1 = int(x0 + (i + 1) * bw)
            # the pilaster at the bay's west end
            px0, px1 = bx0, bx0 + pil
            pm = np.zeros(cv.shape, bool)
            pm[y0 + corn:y1 - plin, px0:px1] = True
            pm &= where
            masonry(cv, px0, y0 + corn, px1, y1 - plin, rng, pm, base=3, course=4.5, length=(8, 8.1), east_dark=False)
            cv[y0 + corn:y1 - plin, px0:px0 + 1][pm[y0 + corn:y1 - plin, px0:px0 + 1]] = code('stone', 4)
            cv[y0 + corn:y1 - plin, px1 - 1:px1][pm[y0 + corn:y1 - plin, px1 - 1:px1]] = code('stone_cool', 1)
            # the recess under the arch
            rx0, rx1 = px1 + q(2), bx1 - q(2) if i < n - 1 else bx1 - pil - q(2)
            if rx1 - rx0 < q(10):
                continue
            rad = (rx1 - rx0) / 2
            cx = (rx0 + rx1) / 2
            spring = y0 + corn + q(3) + rad
            Y, X = np.mgrid[0:cv.shape[0], 0:cv.shape[1]] + 0.5
            rec = (((X - cx) ** 2 + (Y - spring) ** 2 <= rad * rad) & (Y < spring)) | \
                  ((X >= rx0) & (X < rx1) & (Y >= spring) & (Y < y1 - plin))
            rec &= where
            V.rubble(cv, rx0, y0, rx1, y1 - plin, rng, fams=STONES, base=1, course=(2.6, 3.6), length=(4, 7),
                     moss=0.25, east_dark=False, where=rec, mortar=('stone_cool', 0))
            # shade: the west jamb and the arch soffit throw shadow into the recess
            sh = rec & ((X < rx0 + q(3)) | ((X - cx) ** 2 + (Y - spring) ** 2 >= (rad - q(3)) ** 2) & (Y < spring + q(2)))
            cv[sh] = V.FI['stone_cool'] * 8 + np.maximum(0, cv[sh] % 8 - 1)
            # the voussoirs: a ring of wedge blocks, lit on the upper left
            ring = ((X - cx) ** 2 + (Y - spring) ** 2 < (rad + q(3)) ** 2) & ~rec & (Y < spring) & where
            ring &= (X >= rx0 - q(3)) & (X < rx1 + q(3))
            ang = np.degrees(np.arctan2(Y - spring, X - cx))       # -180 west .. -90 top .. 0 east
            seg = np.floor((ang + 180) / 20).astype(int)
            joint = np.abs(((ang + 180) % 20) - 0) < (60 / max(rad, 1))
            t = np.where(ang < -90, 4, 3)
            cv[ring] = (V.FI['stone'] * 8 + t)[ring]
            cv[ring & (seg % 2 == 1)] = V.FI['stone_warm'] * 8 + t[ring & (seg % 2 == 1)]
            cv[ring & joint] = code('stone_cool', 1)
            # imposts: the springing blocks, lit on top
            for ix in (rx0 - q(3), rx1):
                V.blk(cv, ix, int(spring) - q(1), ix + q(3), int(spring) + q(2), 'stone', 4, cut=0, where=where)
    # the cornice: a lit lip, then the shadow under it
    V.fill(cv, x0, y0, x1, y0 + corn, code('stone', 3), where)
    V.fill(cv, x0, y0, x1, y0 + 2, code('stone', 4), where)
    V.fill(cv, x0, y0 + corn, x1, y0 + corn + 1, code('stone_cool', 0), where)
    V.fill(cv, x0, y0 + corn + 1, x1, y0 + corn + 2, code('stone_cool', 1), where)
    for k in range(x0, x1, q(10)):
        V.fill(cv, k, y0 + 2, k + 1, y0 + corn, code('stone', 2), where)
    # moss along the foot, in clusters
    for _ in range((x1 - x0) // q(9)):
        mx = int(rng.integers(x0, x1))
        V.fill(cv, mx, y1 - plin - 2, mx + int(rng.integers(3, 8)), y1 - plin, code('leaf_cool', int(rng.integers(1, 3))), where)
    mottle(cv, where & ndi.binary_erosion(where, iterations=1), rng, sigma=1.8, sib_share=0.1)
    for rx in roots:
        split_root(cv, rx, y0, y1, rng, where)


def split_root(cv, x, y0, y1, rng, where):
    """One of the oak's roots coming through the vault: down the face from the cornice, the masonry
    beside it cracked and a block pushed out, then over the plinth onto the floor."""
    V = _v()
    q, code = V.q, V.code
    pts = [(x, y0 - q(2))]
    y = y0
    while y < y1 + q(6):
        y += q(6)
        pts.append((pts[-1][0] + int(rng.integers(-q(2.5), q(2.5) + 1)), y))
    # cracks either side
    for side in (-1, 1):
        cy = y0 + q(rng.uniform(8, 22))
        cpts = [(pts[2][0] + side * q(2), cy)]
        for _ in range(4):
            cpts.append((cpts[-1][0] + side * q(rng.uniform(2, 4)), cpts[-1][1] + q(rng.uniform(-1.5, 2.5))))
        m = line_mask(cv.shape, cpts, 0.6) & where
        lip = np.roll(m, 1, 0) & ~m & where
        cv[lip] = code('stone', 3)
        cv[m] = code('stone_cool', 0)
    # a block pushed out of the wall, lit and casting a shade below
    bx = pts[3][0] + q(4)
    by = y0 + q(14)
    V.blk(cv, bx, by, bx + q(9), by + q(5), 'stone', 3, cut=1, where=where)
    V.fill(cv, bx + 1, by + q(5), bx + q(9), by + q(6), code('stone_cool', 0), where)
    allm = where.copy()
    allm[y1:y1 + q(8)] = True
    root(cv, pts, q(3.6), q(1.6), allm, rng, base=2, lets=7)


# ------------------------------------------------------------------------------------------------
# props (each a Pic: its foot at (ax, ay))
# ------------------------------------------------------------------------------------------------
def p_rubble(w, h, seed):
    """Fallen vault stones: dressed blocks of several sizes, each with its top, bevel and front,
    piled back to front (the big ones at the foot, a split block leaning on them), chips and grit
    round the heap."""
    V = _v()
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=h * 1.1, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    items = []
    n = max(4, int(w * h / 40))
    for k in range(n):
        fx = rng.uniform(-0.5, 0.5)
        fy = rng.random() ** 0.6
        items.append((fy, fx))
    items.sort()
    for fy, fx in items:
        bw = q(rng.uniform(4, 8.5) * (0.7 + 0.5 * fy))
        bh = q(rng.uniform(2.6, 4.2) * (0.7 + 0.4 * fy))
        top = max(3, int(bh * rng.uniform(0.35, 0.55)))
        hump = (1 - (2 * fx) ** 2) * q(h * 0.6)
        x = int(cx + fx * q(w) - bw / 2)
        y = int(yb - q(h) * (1 - fy) * 0.55 - hump * (1 - fy) - bh)
        cut_block(a, x, y, x + bw, y + bh, top, str(rng.choice(['stone', 'stone_warm', 'stone_cool'])),
                  int(rng.choice([2, 3, 3])), rng)
    for _ in range(int(w / 2)):
        x = cx + int(rng.integers(-q(w / 2) - q(3), q(w / 2) + q(3)))
        y = yb - int(rng.integers(0, q(2.5)))
        V.blk(a, x, y - 2, x + int(rng.integers(3, 6)), y + 1, 'stone', int(rng.choice([2, 3])), cut=0)
    return V.finish(p)


def p_roots(w, h, seed):
    """Roots come down through the vault and lie over the floor: thick runners from one knot,
    sinuous and tapering, over clods of spilled soil and a few fallen stones."""
    V = _v()
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=6, side=10)
    a, cx, yb = p.a, p.ax, p.ay
    for _ in range(int(w / 2.5)):
        sx = cx + q(rng.uniform(-w / 2, w / 2))
        sy = yb - q(rng.uniform(0.5, h * 0.8))
        V.blob(a, V.ellipse_mask(a.shape, sx, sy, q(rng.uniform(1.4, 2.6)), q(rng.uniform(0.9, 1.5))), 'earth_cool',
               int(rng.choice([1, 2, 2])))
    for _ in range(int(w / 6)):
        sx = cx + q(rng.uniform(-w / 2.4, w / 2.4))
        sy = yb - q(rng.uniform(0.5, h * 0.7))
        V.blk(a, sx, sy, sx + q(rng.uniform(2, 3.4)), sy + q(rng.uniform(1.4, 2.2)), 'stone_cool', int(rng.choice([2, 3])), cut=1)
    allm = np.ones(a.shape, bool)
    knot = (cx + q(rng.uniform(-2, 2)), yb - q(h * 0.75))
    for k in range(4):
        ang = (-0.15, 0.25, 0.85, 1.15)[k] * math.pi + rng.uniform(-0.15, 0.15)
        pts = [knot]
        L = w * (0.55 if k in (0, 3) else 0.35)
        for i in range(1, 6):
            t = i / 5
            wob = math.sin(t * 5 + k) * q(1.6)
            pts.append((knot[0] + math.cos(ang) * q(L) * t, knot[1] + math.sin(ang) * q(h * 0.5) * t + wob))
        root(a, pts, q(2.4 if k in (0, 3) else 1.8), q(0.8), allm, rng, base=2 + (k % 2), lets=3)
    return V.finish(p)


def p_urn(w, h, seed):
    """A clay storage jar: a swelling body thrown on the wheel (form-shaded, lit upper left), a
    rolled rim round a dark mouth, two lug handles, a painted band, a chip knocked out of the
    shoulder showing the paler clay inside."""
    from scripts.art.native import raster as R
    V = _v()
    s = ctx.D / 3.0
    W, H = int(round(48 * s)), int(round(60 * s))
    sp = R.Sprite(W, H, s, W / 2 / s * s, (H - 4 * s))
    g = sp.g
    sp.add('body', g.ellipse(0, -18, 15, 17) | g.rrect(-7, -38, 7, -28, 2), 'clay', base=3, z=0)
    sp.add('rim', g.ellipse(0, -39, 9.5, 3.6), 'clay', base=4, z=1, k=0.8)
    sp.add('mouth', g.ellipse(0, -39.5, 6.5, 2.0), 'soot', base=1, z=2, fixed=1, outline=False)
    for sx in (-1, 1):
        sp.add('lug%d' % sx, g.capsule(sx * 9, -33, sx * 14, -28, 2.4, 2.0), 'clay', base=3, z=-0.5, k=0.8)
    band = (g.ellipse(0, -18, 15.2, 17.2) & (g.Y > -24) & (g.Y < -20.5))
    sp.add('band', band, 'clay_cool', base=2, z=0.5, k=0.8)
    sp.add('chip', g.poly([(5, -30), (10, -27), (7, -24)]), 'sand', base=4, z=0.6, k=0.6)
    sp.add('foot', g.ellipse(0, -1.5, 9, 2.5), 'clay_cool', base=2, z=-0.2)
    img = sp.render()
    p = V.Pic(W, H, W // 2, H - int(round(4 * s)) - 1)
    from .palette import code_of, FI
    arr = np.asarray(img)
    for y, x in zip(*np.nonzero(arr[..., 3] > 0)):
        e = code_of(arr[y, x, :3])
        if e == 'ink':
            p.a[y, x] = FI['soot'] * 8 + 0
        elif e is not None:
            p.a[y, x] = FI[e[0]] * 8 + int(e[1])
    return p


def p_stump(w, h, seed):
    """A broken pillar of the old vault: a fluted drum with a jagged, lit break and a fallen piece."""
    V = _v()
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=26, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    r = q(w / 2) - q(1)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    top = yb - q(22) + (np.sin((X - cx) / q(2.2)) * q(1.4) + (X - cx) * 0.25).astype(int)
    shaft = (np.abs(X - cx) <= r) & (Y >= top) & (Y <= yb - q(2))
    u = (X - cx + r) / (2 * r)
    t = np.where(u < 0.3, 4, np.where(u > 0.75, 2, 3))
    flute = (((X - cx) // q(2.2)) % 2 == 0)
    t = t - flute.astype(int) * (u > 0.2)
    a[shaft] = (V.FI['stone'] * 8 + np.clip(t, 1, 5))[shaft]
    brk = shaft & (Y < top + q(1.6))
    a[brk] = V.code('stone_warm', 4)
    base = V.ellipse_mask(a.shape, cx, yb - q(2), r + q(2), q(3))
    V.blob(a, base & ~shaft, 'stone', 2)
    for k in range(3):
        fx = cx + r + q(2) + k * q(2.5)
        V.blk(a, fx, yb - q(4) + int(rng.integers(0, 3)), fx + q(3), yb - q(1), 'stone', 3 - (k % 2), cut=1)
    return V.finish(p)


def p_shard(w, h, seed):
    """The woodland's great shard: a long six-sided crystal of the moon, driven into the floor at a
    slant, its facets pale blue to white; a light source (no outline)."""
    V = _v()
    q = V.q
    p = V._pic(w, h, up=30, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    tip = (cx + q(7), yb - q(30))
    root_l, root_r = (cx - q(4), yb - q(2)), (cx + q(3), yb)
    body = np.zeros(a.shape, bool)
    from scripts.art.native.raster import Grid
    g = Grid(a.shape[1], a.shape[0], 1.0, 0, 0)
    body = g.poly([root_l, (cx - q(3), yb - q(18)), tip, (cx + q(5), yb - q(14)), root_r])
    lit = g.poly([root_l, (cx - q(3), yb - q(18)), tip, (cx, yb - q(4))])
    a[body] = V.code('sky', 3)
    a[lit] = V.code('sky', 4)
    core = g.poly([(cx - q(1), yb - q(5)), (cx - q(1.5), yb - q(16)), tip, (cx + q(0.5), yb - q(10))])
    a[core] = V.code('sky', 5)
    edge = line_mask(a.shape, [(cx + q(0.2), yb - q(3)), tip], 0.6) & body
    a[edge] = V.code('sky_cool', 3)
    a[body & ~lit & (np.mgrid[0:a.shape[0], 0:a.shape[1]][1] > cx + q(3))] = V.code('sky_cool', 3)
    # a smaller splinter beside it
    s2 = g.poly([(cx - q(8), yb), (cx - q(9), yb - q(8)), (cx - q(6), yb - q(1))])
    a[s2] = V.code('sky', 4)
    V.tidy(a)
    return p


def p_torch(frame, seed):
    """A wall torch: an iron bracket on the face, a cup of pitch and its flame. Four drawings of the
    flame (it leans and lifts) for a finite flicker; the bracket never moves. The canvas's foot is
    the cup; the flame is a light source (no outline)."""
    V = _v()
    q, code = V.q, V.code
    W, H = q(10), q(22)
    p = V.Pic(W, H, W // 2, H - q(6))
    a, cx, cy = p.a, p.ax, p.ay
    V.blk(a, cx - q(1.8), cy + q(2.2), cx + q(1.8), cy + q(6.4), 'iron', 2, cut=1)    # the plate on the wall
    for ry in (2.9, 5.2):
        V.fill(a, cx - q(1.1), cy + q(ry), cx - q(1.1) + 2, cy + q(ry) + 2, code('iron', 4))   # rivets into the joint
        V.fill(a, cx + q(0.6), cy + q(ry), cx + q(0.6) + 2, cy + q(ry) + 2, code('iron', 4))
    V.bar(a, cx, cy + q(3.6), cx, cy + q(0.6), q(0.6), 'iron', 3)                      # the arm out from the wall
    V.bar(a, cx, cy + q(3.0), cx + q(1.2), cy + q(1.2), q(0.45), 'iron', 2)            # its strut
    cup = V.ellipse_mask(a.shape, cx, cy - q(0.4), q(2.4), q(1.6)) & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] >= cy - q(1.4))
    V.blob(a, cup, 'iron', 3)
    for bx in (-1.4, 0.6):                                                              # the basket's straps
        V.fill(a, cx + q(bx), cy - q(1.3), cx + q(bx) + 2, cy + q(0.9), code('iron', 1))
    V.fill(a, cx - q(2.4), cy - q(1.4), cx + q(2.4), cy - q(1.4) + 2, code('iron', 4))  # the lit rim
    a[V.ellipse_mask(a.shape, cx, cy - q(1.9), q(1.9), q(0.6))] = code('soot', 1)       # pitch in the cup
    V.outline(a)
    lean = (0, 1, 0, -1)[frame % 4]
    hgt = (9.0, 10.5, 8.0, 10.0)[frame % 4]
    base_y = cy - q(2)
    outer = np.zeros(a.shape, bool)
    mid = np.zeros(a.shape, bool)
    inner = np.zeros(a.shape, bool)
    for i in range(10):
        t = i / 9
        r = q(2.6) * (1 - t) ** 0.8 + 0.6
        x = cx + lean * q(1.4) * t * t
        y = base_y - q(hgt) * t
        outer |= V.ellipse_mask(a.shape, x, y, r, r)
        if t < 0.7:
            mid |= V.ellipse_mask(a.shape, x, y, r * 0.66, r * 0.66)
        if t < 0.4:
            inner |= V.ellipse_mask(a.shape, x, y, r * 0.38, r * 0.5)
    a[outer] = code('lava', 3)
    a[mid] = code('lamp', 4)
    a[inner] = code('lamp', 5)
    if frame % 2 == 0:
        sx = cx + (q(2) if frame == 0 else -q(2))
        V.fill(a, sx, base_y - q(hgt) - q(2), sx + 2, base_y - q(hgt) - q(2) + 2, code('lamp', 5))
    V.tidy(a)
    return p


def sigil(a, cx, cy, r, lit):
    """The starfall sigil carved in stone: a ring and a four-pointed star; glowing while it holds."""
    V = _v()
    q, code = V.q, V.code
    ring = V.ellipse_mask(a.shape, cx, cy, r, r * 0.8) & ~V.ellipse_mask(a.shape, cx, cy, r - 2, r * 0.8 - 2)
    star = line_mask(a.shape, [(cx, cy - r * 0.7), (cx, cy + r * 0.7)], 0.7) | \
        line_mask(a.shape, [(cx - r * 0.7, cy), (cx + r * 0.7, cy)], 0.7)
    star |= V.ellipse_mask(a.shape, cx, cy, q(1.2), q(1.0))
    m = ring | star
    if lit:
        a[m] = code('sky', 4)
        a[m & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] < cy)] = code('sky', 5)
    else:
        a[m] = code('stone_cool', 1)
        lip = np.roll(m, 1, 0) & ~m & (a >= 0)
        a[lip] = code('stone', 4)
    return m


def p_seal(w, h, height, sealed=True):
    """The sealed slab: a block of dressed stone plugging the passage, `height` world px tall, seen
    like every wall: its top (the sigil carved in it, glowing while it holds, a lit lip at its south
    edge) and its south face (two courses and a plinth with a dark foot)."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(5)
    W, H = q(w) + 6, q(h) + q(height) + 6
    p = V.Pic(W, H, W // 2, H - 4)
    a = p.a
    x0, x1 = 3, W - 3
    ytop, yface, yb = 3, 3 + q(h), H - 3
    # the top: three long slabs end to end, the middle one with the sigil
    for k, (s0, s1) in enumerate(((ytop, ytop + (yface - ytop) // 3), (ytop + (yface - ytop) // 3, ytop + 2 * (yface - ytop) // 3),
                                  (ytop + 2 * (yface - ytop) // 3, yface))):
        cut_block(a, x0, s0, x1, s1 - 1, (s1 - s0) - q(2), 'stone_warm' if k != 1 else 'stone', 2, rng)
    V.fill(a, x0, ytop, x1, yface, code('stone_cool', 0), a < 0)
    sigil(a, (x0 + x1) / 2, (ytop + yface) / 2, q(5.5), sealed)
    V.fill(a, x0, yface - 2, x1, yface, code('stone', 4))                 # the lit lip
    m = np.zeros(a.shape, bool)
    m[yface:yb, x0:x1] = True
    masonry(a, x0, yface, x1, yb, rng, m, base=2, course=6, length=(7, 9), east_dark=False)
    V.fill(a, x0, yface, x1, yface + 1, code('stone_cool', 0))
    V.fill(a, x0, yb - q(5), x1, yb - q(5) + 1, code('stone', 3))
    V.fill(a, x0, yb - 2, x1, yb, code('stone_cool', 0))
    V.fill(a, x1 - 2, yface, x1, yb, code('stone_cool', 1))
    return V.finish(p)


def p_seal_sunk(w, h):
    """The slab sunk flush with the floor: its top only, the sigil gone dark."""
    V = _v()
    q = V.q
    W, H = q(w) + 4, q(h) + 4
    p = V.Pic(W, H, W // 2, H - 2)
    a = p.a
    for k in range(3):
        cut_block(a, 2, 2 + k * (H - 4) // 3, W - 2, 2 + (k + 1) * (H - 4) // 3 - 1, (H - 4) // 3 - 3,
                  'stone_warm' if k != 1 else 'stone', 2, np.random.default_rng(k))
    sigil(a, W / 2, H / 2, q(5.5), False)
    return V.finish(p)


def p_plate(w, h, pressed):
    """The pressure plate: a square slab set in a frame of narrow stones, the sigil carved in a sunk
    panel. Raised two world px it shows a bevel and its front; pressed, it sits flush, its edge in
    the frame's shadow, and the sigil glows."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(13)
    up = 0 if pressed else 2
    W, H = q(w + 4) + 6, q(h + 4 + up) + 6
    p = V.Pic(W, H, W // 2, H - 3)
    a = p.a
    x0, y0, x1, y1 = 3, 3 + q(up), W - 3, H - 3
    for (fx0, fy0, fx1, fy1) in ((x0, y0, x1, y0 + q(2)), (x0, y1 - q(2), x1, y1), (x0, y0, x0 + q(2), y1), (x1 - q(2), y0, x1, y1)):
        V.blk(a, fx0, fy0, fx1, fy1, 'stone_cool', 2, cut=1)
    ix0, iy0, ix1, iy1 = x0 + q(2), y0 + q(2), x1 - q(2), y1 - q(2)
    if pressed:
        V.fill(a, ix0, iy0, ix1, iy0 + 2, code('soot', 1))
        cut_block(a, ix0, iy0 + 2, ix1, iy1, iy1 - iy0 - 3, 'stone_warm', 2, rng, bevel=0)
    else:
        cut_block(a, ix0, iy0 - q(up), ix1, iy1, iy1 - iy0 - q(up) + q(0.5), 'stone_warm', 2, rng)
    cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2 - (0 if pressed else q(up))
    pan = np.zeros(a.shape, bool)
    pan[int(cy - q(4)):int(cy + q(4)), int(cx - q(4)):int(cx + q(4))] = True
    a[pan] = code('stone_warm', 1)
    a[pan & ~np.roll(pan, -1, 0)] = code('stone_warm', 3)        # the panel's lit lower lip
    star = line_mask(a.shape, [(cx, cy - q(3.4)), (cx, cy + q(3.4))], 0.7) | line_mask(a.shape, [(cx - q(3.4), cy), (cx + q(3.4), cy)], 0.7)
    star |= V.ellipse_mask(a.shape, cx, cy, q(1.2), q(1.2))
    a[star & pan] = code('sky', 4) if pressed else code('soot', 1)
    return V.finish(p)


def p_lever(pulled):
    """The lever: a dressed stone post (top, bevel, front, a carved slot in its top), an iron pivot
    plate bolted to its face with four rivets, an iron arm through the slot and a wooden grip bound
    with two iron bands; pulled, the arm lies down to the east."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(11)
    W, H = q(18), q(24)
    p = V.Pic(W, H, W // 2, H - 3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(4), cx + q(4)
    cut_block(a, x0, yb - q(12), x1, yb, q(3.5), 'stone', 3, rng)
    V.fill(a, cx - q(0.8), yb - q(11.2), cx + q(0.8), yb - q(9.4), code('soot', 0))       # the slot
    V.fill(a, cx - q(0.8), yb - q(9.4), cx + q(0.8), yb - q(9.4) + 1, code('stone', 4))
    V.blk(a, cx - q(2.4), yb - q(8), cx + q(2.4), yb - q(3.6), 'iron', 2, cut=1)          # the pivot plate
    for dx in (-1.6, 1.2):
        for dy in (7.2, 4.6):
            V.fill(a, cx + q(dx), yb - q(dy), cx + q(dx) + 2, yb - q(dy) + 2, code('iron', 4))
    if pulled:
        arm = (cx, yb - q(10.4), cx + q(7), yb - q(6.5))
    else:
        arm = (cx, yb - q(10.4), cx - q(2.6), yb - q(19))
    V.bar(a, arm[0], arm[1], arm[2], arm[3], q(0.8), 'iron', 3)
    gx, gy = arm[2], arm[3]
    dx, dy = (gx - arm[0]), (gy - arm[1])
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    V.bar(a, gx - ux * q(1), gy - uy * q(1), gx + ux * q(2.6), gy + uy * q(2.6), q(1.3), 'timber', 3)
    for t_ in (0.0, 1.6):
        bx, by = gx + ux * q(t_), gy + uy * q(t_)
        V.bar(a, bx - uy * q(1.3), by + ux * q(1.3), bx + uy * q(1.3), by - ux * q(1.3), 0.8, 'iron', 2)
    return V.finish(p)


def p_channel(pts, lit):
    """The carved channel from the plate to the slab, as an overlay: glowing once the plate is down."""
    V = _v()
    q, code = V.q, V.code
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    W, H = q(x1 - x0) + 6, q(4) + 6
    p = V.Pic(W, H, 3, H // 2)
    a = p.a
    V.fill(a, 3, H // 2 - q(1), W - 3, H // 2 + q(1), code('sky', 4 if lit else 1))
    V.fill(a, 3, H // 2 - 1, W - 3, H // 2 + 1, code('sky', 5 if lit else 2))
    for k in range(3 + q(6), W - 3, q(10)):
        a[H // 2 - q(1) - 1:H // 2 + q(1) + 1, k:k + 2] = code('sky', 5 if lit else 2)
    return p


def p_cairn_alcove(seed):
    """Cairn asleep in the wall: his slumped drawing (the cast's last defeat frame) brought onto the
    house ramps a step into shade, half sunk behind the masonry and earth that grew over his legs."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native import palette as PAL
    rng = np.random.default_rng(seed)
    src = np.asarray(Image.open(CAIRN).convert('RGBA'))[:, -160:]
    ys, xs = np.nonzero(src[..., 3] > 0)
    src = src[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    fam_for = {}
    names = ['stone', 'stone_cool', 'leaf', 'leaf_cool', 'lamp', 'brass', 'void', 'soot']
    pal = [(f, t, np.array(PAL.rgb(f, t), float)) for f in names for t in range(6)]
    h, w = src.shape[:2]
    scale = ctx.D / 3.0
    sh, sw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    if (sh, sw) != (h, w):
        src = np.asarray(Image.fromarray(src, 'RGBA').resize((sw, sh), Image.NEAREST))
    pad = q(4)
    W, H = sw + 2 * pad, sh + pad
    p = V.Pic(W, H, W // 2, H - 1)
    a = p.a
    for y in range(sh):
        for x in range(sw):
            px = src[y, x]
            if px[3] == 0:
                continue
            key = tuple(int(v) for v in px[:3])
            if key not in fam_for:
                c = np.array(key, float)
                f, t, _ = min(pal, key=lambda e: ((e[2] - c) ** 2).sum())
                fam_for[key] = V.code(f, max(0, t - 2) if f not in ('lamp', 'brass') else 1)
            a[y, x + pad] = fam_for[key]
    # half sunk: masonry and earth over his lower third
    cover = int(sh * 0.36)
    yb = H - 1
    m = np.zeros(a.shape, bool)
    m[yb - cover:yb + 1, :] = True
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    m &= (Y >= yb - cover + (np.sin(X / q(3)) * q(1.5)).astype(int))
    V.rubble(a, 0, yb - cover - q(2), W, yb + 1, rng, fams=STONES, base=2, course=(2.6, 3.6), length=(4, 8), moss=0.5,
             east_dark=True, where=m, mortar=('earth_cool', 1))
    turf = m & ~np.roll(m, q(1.5), 0)
    a[turf] = code('leaf_cool', 2)
    return V.finish(p)


PROPS = {'rubble': p_rubble, 'roots': p_roots, 'urn': p_urn, 'stump': p_stump, 'shard': p_shard}


# ------------------------------------------------------------------------------------------------
# the zone
# ------------------------------------------------------------------------------------------------
def build(plan: dict, out_dir: str, preview: str | None = None) -> dict:
    V = _v()
    from scripts.art.native.palette import FI, sib, step, to_rgba
    q, code = V.q, V.code
    D = ctx.D
    bx, by, bw, bh = plan['box']
    W, H = q(bw), q(bh)
    rng = np.random.default_rng(plan.get('art', {}).get('seed', 31))
    YY, XX = np.mgrid[0:H, 0:W]
    WX, WY = (XX + 0.5) / D, (YY + 0.5) / D

    def rmask(r):
        x, y, w, h = r
        return (WX >= x) & (WX < x + w) & (WY >= y) & (WY < y + h)

    cv = np.full((H, W), -1, np.int32)
    cap = np.zeros((H, W), bool)
    face = np.zeros((H, W), bool)
    for wl in plan['walls']:
        x, y, w, h = wl['rect']
        f = wl.get('face', 0)
        cap |= rmask([x, y, w, h - f])
        if f:
            face |= rmask([x, y + h - f, w, f])
    stair = rmask(plan['stair']['rect']) if plan.get('stair') else np.zeros((H, W), bool)
    floor = ~cap & ~face & ~stair

    # --- the floor ---------------------------------------------------------------------------
    slab = flagstones(cv, 0, 0, W, H, rng, floor)
    inner = (slab > 0) & ndi.binary_erosion(slab > 0, iterations=2)
    mottle(cv, inner, rng)
    # spilled soil and moss in the damp joints under the root bays and along the walls' feet
    near_wall = ndi.binary_dilation(cap | face, iterations=q(10)) & floor
    joint = floor & (cv // 8 == FI['stone_cool']) & (cv % 8 == 1)
    nb = ndi.binary_dilation(slab_any := (cv // 8 != FI['stone_cool']) & floor, iterations=1)
    damp = joint & near_wall & nb & (ndi.gaussian_filter(rng.random((H, W)), q(1.5)) > 0.62)
    damp = ndi.binary_opening(damp, structure=np.ones((1, 2))) | ndi.binary_opening(damp, structure=np.ones((2, 1)))
    cv[damp] = code('leaf_cool', 2)

    # --- the stair up to the hatch -----------------------------------------------------------
    if plan.get('stair'):
        sx, sy, sw, sh = plan['stair']['rect']
        n = 4
        for i in range(n):
            x0 = q(sx + sw * i / n)
            x1 = q(sx + sw * (i + 1) / n)
            t = 4 - i
            V.fill(cv, x0, q(sy), x1, q(sy + sh), code('stone_warm', t))
            V.fill(cv, x0, q(sy), x0 + 2, q(sy + sh), code('stone_warm', min(5, t + 1)))    # the lit nosing
            V.fill(cv, x1 - q(1), q(sy), x1, q(sy + sh), code('stone_warm', max(0, t - 2)))  # the riser in shade
            V.fill(cv, x0, q(sy + sh) - q(2), x1, q(sy + sh), code('stone_cool', max(0, t - 2)))

    # --- wall tops and faces -----------------------------------------------------------------
    for wl in plan['walls']:
        x, y, w, h = wl['rect']
        f = wl.get('face', 0)
        tm = rmask([x, y, w, h - f])
        wall_top(cv, q(x), q(y), q(x + w), q(y + h - f), rng, tm)
        if f:
            fm = rmask([x, y + h - f, w, f])
            wall_face(cv, q(x), q(y + h - f), q(x + w), q(y + h), rng, fm, roots=[q(r) for r in wl.get('roots', [])],
                      arcade=w >= 40)
            if wl.get('alcove'):
                ax = q(wl['alcove'])
                ay0, ay1 = q(y + h - f) + q(4), q(y + h) - q(1)
                rad = q(14)
                al = ((((WX * D - ax) ** 2 + (WY * D - (ay0 + rad)) ** 2) <= rad * rad) & (WY * D < ay0 + rad)) | \
                     ((np.abs(WX * D - ax) < rad) & (WY * D >= ay0 + rad) & (WY * D < ay1))
                al &= fm
                V.rubble(cv, ax - rad, ay0, ax + rad, ay1, rng, fams=STONES, base=0, course=(2.4, 3.2), length=(3, 6),
                         moss=0.3, east_dark=False, where=al, mortar=('void', 0))
                rim = ndi.binary_dilation(al, iterations=q(2)) & ~al & fm
                cv[rim & (WX * D < ax)] = code('stone', 4)
                cv[rim & (WX * D >= ax)] = code('stone', 2)
        sk = wl.get('skylight')
        if sk:
            hx, hy, hw, hh = sk
            u = (WX - hx) / hw
            half = hh / 2 * np.sin(np.clip(u, 0, 1) * math.pi) ** 0.8 + np.sin(WX * 0.45) * 0.9
            hole = (u >= 0) & (u <= 1) & (np.abs(WY - hy - hh / 2) < half) & tm
            lip = ndi.binary_dilation(hole, iterations=q(1.5)) & ~hole & tm
            cv[lip] = code('earth', 1)
            cv[lip & (WY < hy + hh / 2)] = code('grass_cool', 2)
            cv[hole] = code('sky', 4)
            cv[hole & ndi.binary_erosion(hole, iterations=q(1.5))] = code('sky', 5)
            for k in range(5):
                rx = q(hx + hw * (0.15 + 0.17 * k))
                ry = q(hy + hh / 2)
                lm = line_mask(cv.shape, [(rx, ry), (rx + q(1) * (k % 2 * 2 - 1), ry + q(3 + k % 3))], 0.7) & tm
                cv[lm] = code('earth_warm', 2)

    # the lip where a top breaks to a face or the floor: lit rim, then a dark line outside it
    top_edge = cap & ~np.roll(cap, -1, 0)                  # bottom row of a top
    west_edge = cap & ~np.roll(cap, 1, 1) & (XX > 0)        # west side (lit)
    east_edge = cap & ~np.roll(cap, -1, 1) & (XX < W - 1)   # east side (in shade)
    north_edge = cap & ~np.roll(cap, 1, 0) & (YY > 0)
    lip = ndi.binary_dilation(top_edge | north_edge, iterations=1, structure=np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]])) & cap
    cv[lip] = code('stone', 4)
    wrim = ndi.binary_dilation(west_edge, structure=np.array([[0, 0, 0], [0, 1, 1], [0, 0, 0]])) & cap
    erim = ndi.binary_dilation(east_edge, structure=np.array([[0, 0, 0], [1, 1, 0], [0, 0, 0]])) & cap
    cv[wrim] = code('stone', 3)
    cv[erim] = code('stone_cool', 1)
    rim = lip | wrim | erim
    outer = ndi.binary_dilation(cap | face, iterations=1) & ~(cap | face) & ~stair
    cv[outer] = V.FI['stone'] * 8 + 6
    # contact shade on the floor: under the faces and east of the tops (light from the upper left)
    foot = np.zeros((H, W), bool)
    fb = face & ~np.roll(face, -1, 0)
    for k in range(1, q(3) + 1):
        foot |= np.roll(fb, k, 0)
    east_sh = np.zeros((H, W), bool)
    for k in range(1, q(4) + 1):
        east_sh |= np.roll(east_edge, k, 1)
    sel = (foot | east_sh) & floor & ~outer
    cv[sel] = step(cv[sel], -1)

    # --- the plate's channel, carved (its glow is an overlay) -------------------------------
    pz = plan.get('puzzle', {})
    if pz.get('channel'):
        (x0, y0), (x1, y1) = pz['channel'][0], pz['channel'][-1]
        ch = (WX >= x0) & (WX < x1) & (np.abs(WY - y0) < 1.4)
        cv[ch] = code('stone_cool', 0)
        cv[ch & (np.abs(WY - y0 - 1.4) < 1 / D)] = code('stone', 3)

    # --- the shard's crater ----------------------------------------------------------------------
    objects = []
    pics = {}

    def add_pic(name, img):
        pics[name] = img
        return name

    for pr in plan.get('props', []):
        if pr['kind'] == 'shard':
            x, y = pr['at']
            e = ((WX - x) / 14) ** 2 + ((WY - y) / 8) ** 2
            cr = (e < 1) & floor
            cv[cr] = step(cv[cr], -1)
            for k in range(6):
                ang = k * math.pi / 3 + 0.4
                pts = [(q(x), q(y))]
                for s in range(1, 4):
                    pts.append((q(x + math.cos(ang) * 6 * s), q(y + math.sin(ang) * 3.4 * s) + int(rng.integers(-2, 3))))
                m = line_mask(cv.shape, pts, 0.6) & floor
                cv[m] = code('stone_cool', 0)

    # --- light: the torches' warm pools, the shaft's cool pool, the hatch's daylight, the dark ---
    lightv = np.full((H, W), -1, int)
    nz = (ndi.gaussian_filter(rng.random((H, W)), q(2.5)) - 0.5) * 0.5
    warm = np.zeros((H, W), bool)
    cool = np.zeros((H, W), bool)
    for tx, ty in plan.get('torches', []):
        dfl = np.hypot((WX - tx) / 44, (WY - ty - 18) / 30)        # the floor below
        dfa = np.hypot((WX - tx) / 18, (WY - ty + 26) / 16)        # the face round the bracket
        d = np.minimum(dfl, dfa)
        d = d + nz
        lightv = np.maximum(lightv, np.where(dfa < 0.5, 2, np.where(d < 0.8, 1, np.where(d < 1.5, 0, -1))))
        warm |= d < 1.1
    sk = plan.get('skylight')
    if sk:
        sx, sy = sk['at']
        d = np.hypot((WX - sx) / sk['rx'], (WY - sy) / sk['ry']) + nz
        # the beam crosses the face too: from the hole in the vault down to the pool
        hole = [w for w in plan['walls'] if w.get('skylight')][0]['skylight']
        hx = hole[0] + hole[2] / 2
        tcol = (WY - hole[1]) / max(1, sy - hole[1])
        beam = (np.abs(WX - (hx + (sx - hx) * tcol)) < 14 + 6 * tcol) & (tcol > 0.1) & (tcol < 0.9) & face
        lightv = np.maximum(lightv, np.where(d < 0.5, 2, np.where(d < 1.0, 1, np.where(d < 1.6, 0, -1))))
        lightv[beam] = np.maximum(lightv[beam], 1)
        cool |= (d < 1.0) | beam
    if plan.get('stair'):
        sx, sy, sw, sh = plan['stair']['rect']
        d = np.hypot((WX - sx - sw) / 40, (WY - sy - sh / 2) / 24)
        lightv = np.maximum(lightv, np.where(d < 0.5, 1, np.where(d < 1.2, 0, -1)))
    lightv[stair] = 0
    lightv = np.clip(ndi.median_filter(lightv, size=5), -1, 2)
    # on the floor, light falls slab by slab (each slab takes the light at its middle)
    n = int(slab.max())
    if n:
        per = np.round(ndi.median(lightv, labels=slab, index=np.arange(1, n + 1))).astype(int)
        per = np.concatenate([[0], per])
        on = slab > 0
        lightv[on] = per[slab[on]]
        jt = floor & ~on
        lightv[jt] = np.minimum(lightv[jt], 0)
    lightv[cap] = -2                         # the vault's tops never catch the light ...
    lightv[rim] = 0                          # ... but their lips keep the house lit edge
    edge_tone = (cv % 8 >= 6) | (cv < 0)
    for lv in (-2, -1, 1, 2):
        sel = (lightv == lv) & ~edge_tone
        cv[sel] = step(cv[sel], lv)
    sel = warm & ~edge_tone & ~cool & np.isin(cv // 8, [FI[s] for s in STONES])
    cv[sel] = sib(cv[sel], 'warm')
    sel = cool & ~edge_tone & np.isin(cv // 8, [FI[s] for s in STONES])
    cv[sel] = sib(cv[sel], 'cool')

    # --- objects ---------------------------------------------------------------------------------
    for k, pr in enumerate(plan.get('props', [])):
        w, h = pr.get('size', [12, 8])
        pic = PROPS[pr['kind']](w, h, seed=100 + k)
        x, y = pr['at']
        objects.append(dict(id=pr['id'], kind=pr['kind'], png=add_pic(pr['id'], pic.rgba()), foot=(q(x), q(y)),
                            anchor=(pic.ax, pic.ay), alpha=pic.alpha(), cond=pr.get('if'),
                            solid=[x - w / 2, y - h, w, h] if pr.get('solid') else None))
    frames = [p_torch(i, 7) for i in range(TORCH_FRAMES)]
    fw = frames[0].W
    sheet = Image.new('RGBA', (fw * TORCH_FRAMES, frames[0].H))
    for i, fr in enumerate(frames):
        sheet.paste(fr.rgba(), (i * fw, 0))
    add_pic('torch', sheet)
    for i, (tx, ty) in enumerate(plan.get('torches', [])):
        objects.append(dict(id='torch_%d' % (i + 1), kind='torch', png='torch', foot=(q(tx), q(ty)),
                            anchor=(frames[0].ax, frames[0].ay), lift=q(24), frames=TORCH_FRAMES, alpha=None, cond=None,
                            solid=None))
    for wl in plan['walls']:
        if wl.get('alcove'):
            x, y, w, h = wl['rect']
            pic = p_cairn_alcove(9)
            objects.append(dict(id='cairn_alcove', kind='cairn', png=add_pic('cairn_alcove', pic.rgba()),
                                foot=(q(wl['alcove']), q(y + h) - q(1)), anchor=(pic.ax, pic.ay), alpha=None, cond=None,
                                solid=None))
    if pz:
        pl = pz['plate']
        x, y = pl['at']
        w, h = pl['size']
        flag = {'flags': [pl['flag']]}
        nflag = {'not_flags': [pl['flag']]}
        for pressed, cond in ((False, nflag), (True, flag)):
            pic = p_plate(w, h, pressed)
            nm = 'plate_down' if pressed else 'plate_up'
            objects.append(dict(id=nm, kind='floor', png=add_pic(nm, pic.rgba()), foot=(q(x), q(y + h / 2)),
                                anchor=(pic.ax, pic.ay), alpha=None, cond=cond, solid=None))
        pic = p_channel(pz['channel'], True)
        objects.append(dict(id='channel_lit', kind='floor', png=add_pic('channel_lit', pic.rgba()),
                            foot=(q(pz['channel'][0][0]), q(pz['channel'][0][1])), anchor=(pic.ax, pic.ay), alpha=None,
                            cond=flag, solid=None))
        lv = pz['lever']
        open_ = {'flags': [lv['flag']]}
        shut = {'not_flags': [lv['flag']]}
        x, y = lv['at']
        for pulled, cond in ((False, shut), (True, open_)):
            pic = p_lever(pulled)
            nm = 'lever_down' if pulled else 'lever_up'
            objects.append(dict(id=nm, kind='lever', png=add_pic(nm, pic.rgba()), foot=(q(x), q(y)),
                                anchor=(pic.ax, pic.ay), alpha=None, cond=cond, solid=[x - 3, y - 4, 6, 4]))
        sl = pz['seal']
        x, y, w, h = sl['rect']
        pic = p_seal(w, h, sl['height'], True)
        objects.append(dict(id='seal_slab', kind='seal', png=add_pic('seal_slab', pic.rgba()), foot=(q(x + w / 2), q(y + h)),
                            anchor=(pic.ax, pic.ay), alpha=None, cond=shut, solid=[x, y, w, h]))
        pic = p_seal_sunk(w, h)
        objects.append(dict(id='seal_sunk', kind='floor', png=add_pic('seal_sunk', pic.rgba()),
                            foot=(q(x + w / 2), q(y + h)), anchor=(pic.ax, pic.ay), alpha=None, cond=open_, solid=None))

    # contact shadows under the standing props
    for o in objects:
        if o['kind'] in ('rubble', 'roots', 'urn', 'stump', 'lever', 'seal'):
            fx, fy = o['foot']
            w = (o['solid'][2] if o.get('solid') else 10) * D
            e = ((XX - fx - q(2)) / (w / 2 + q(3))) ** 2 + ((YY - fy + q(1)) / q(4)) ** 2
            sel = (e < 1) & floor & ~edge_tone
            cv[sel] = step(cv[sel], -1)
    V.tidy(cv, passes=2, keep=(cv % 8 >= 6))
    ground = Image.fromarray(to_rgba(cv), 'RGBA').convert('RGB')

    # --- write ---------------------------------------------------------------------------------
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith('.png') and f != 'ground.png' and f[:-4] not in pics:
            os.remove(os.path.join(out_dir, f))
    ground.save(os.path.join(out_dir, 'ground.png'), optimize=True)
    for name, img in pics.items():
        img.save(os.path.join(out_dir, name + '.png'), optimize=True)
    doc = dict(zone=plan['id'], kit='undercroft', density=D, size=[W, H], inputs=plan.get('_inputs'),
               kit_drawn=sorted(n + '.png' for n in pics), objects=[])
    for o in objects:
        e = dict(id=o['id'], kind=o['kind'], png=o['png'] + '.png', foot=[int(o['foot'][0]), int(o['foot'][1])],
                 offset=[-int(o['anchor'][0]), -int(o['anchor'][1]) - int(o.get('lift', 0))], cond=o.get('cond'),
                 solid=o.get('solid'))
        if o.get('frames'):
            e['frames'] = o['frames']
        doc['objects'].append(e)
    json.dump(doc, open(os.path.join(os.path.dirname(out_dir.rstrip('/')), 'kit.json'), 'w'), indent=1)

    if preview:
        os.makedirs(preview, exist_ok=True)
        img = ground.convert('RGBA')
        for o in sorted(objects, key=lambda o: (o['kind'] != 'floor', o['foot'][1])):
            c = o.get('cond') or {}
            if c.get('flags'):
                continue
            pic = pics[o['png']]
            if o.get('frames'):
                pic = pic.crop((0, 0, pic.width // o['frames'], pic.height))
            X = int(o['foot'][0] - o['anchor'][0])
            Y = int(o['foot'][1] - o['anchor'][1] - o.get('lift', 0))
            img.alpha_composite(pic, (max(0, X), max(0, Y)))
        img.convert('RGB').save(os.path.join(preview, plan['id'] + '.png'))
    return dict(zone=plan['id'], size=[W, H], objects=len(objects), pictures=len(pics))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--density', type=float, default=3.0)
    ap.add_argument('--out', required=True)
    ap.add_argument('--preview', default=None)
    a = ap.parse_args(argv)
    plan = json.load(open(a.plan))
    ctx.configure(a.density, {}, plan)
    plan['_inputs'] = input_hash(os.path.abspath(a.plan), a.density)
    print(json.dumps(build(plan, a.out, a.preview)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
