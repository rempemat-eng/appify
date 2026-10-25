"""Standing stones at any density, in props.py's manner (Claude B, lane B; lane R 25 Oct 17:08
finding 8: the circle's stones were the lying boulder stretched upright, 78-82 % flat 2 x 2
blocks with 11 colours).

A standing stone is an upright slab seen in the three-quarter view, so it shows three planes:

- the top, a narrow weathered plane seen from above (lit: stone_warm 4, its crown 5);
- the broad face turned to the south-west (stone 3, lit at the upper-left rim, shaded at the
  lower right), with a lit arris where it turns;
- the east side turned from the light (stone_cool 1-2).

On the faces: two or three cracks (a dark line with its lit lip above and to the left),
bedding lines across the grain of the slab (broken, a tone down), pits with a lit rim, cluster
texture so no plane is a flat fill, lichen (pale and yellow-green rosettes in clusters on the
top and the lit face), moss and a darker foot where it meets the ground.

    standing_stone4(d, w, h, seed, fam='stone', lean=0.0) -> (img, (ax, ay), alpha)

w and h are world px, the plan's box (16 x 29, 17 x 29, 15 x 21 in the woodland). Coordinates
inside are props.py's 2x units (s = d / 2 texels a unit), so the stone is one design at every
density: at 3x it gains texels, not a different shape.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from . import raster as pk
from .props import _out, _sprite


def _jit(rng, a):
    return float(rng.uniform(-a, a))


def standing_stone4(d, w=16, h=29, seed=7, fam='stone', lean=None):
    rng = np.random.default_rng(seed)
    if lean is None:                                      # old stones lean a little, each its own way
        lean = float(rng.uniform(-0.07, 0.07))
    W, H = w * 2.0, h * 2.0
    sp = _sprite(d, W + 14, H + 10, (W + 14) / 2, 3)
    g = sp.g
    hw = W / 2
    # the silhouette: a slab narrowing a little upward, a slanted crown higher on one side, chips
    hi_left = rng.random() < 0.5
    peak_x = (-0.25 if hi_left else 0.2) * hw + _jit(rng, hw * 0.1)
    sh_l = -H * (0.93 if hi_left else 0.84) + _jit(rng, 1.5)
    sh_r = -H * (0.84 if hi_left else 0.93) + _jit(rng, 1.5)
    tl = lean * H
    pts = [(-hw - 0.5, 0.0), (-hw * 0.97 + _jit(rng, 0.8), -H * 0.34),
           (-hw * 0.86 + tl * 0.6 + _jit(rng, 0.8), -H * 0.66),
           (-hw * 0.66 + tl, sh_l), (-hw * 0.38 + tl, -H * 0.97 + _jit(rng, 1)),
           (peak_x + tl, -H), (hw * 0.36 + tl, -H * 0.95 + _jit(rng, 1)),
           (hw * 0.68 + tl, sh_r), (hw * 0.84 + tl * 0.6 + _jit(rng, 0.8), -H * 0.6),
           (hw * 0.95 + _jit(rng, 0.8), -H * 0.3), (hw + 0.5, 0.0)]
    body = g.poly(pts)
    for _ in range(2):                                    # chipped edges: bites out of the rim
        k = int(rng.integers(2, len(pts) - 2))
        cx, cy = pts[k]
        body &= ~g.ellipse(cx + _jit(rng, 1.5), cy + _jit(rng, 1.5), rng.uniform(1.6, 2.6), rng.uniform(1.2, 2.0))
    body = pk.round_mask(body, 1)
    Hp, Wp = body.shape
    s = g.s
    ys, xs = np.nonzero(body)
    first = np.full(Wp, 10 ** 6)
    for x in np.unique(xs):
        first[x] = ys[xs == x].min()
    Yp, Xp = np.mgrid[0:Hp, 0:Wp]
    # the planes: the top (a band under the crown edge), the east side (right of a slanted arris)
    cap = max(2, int(round(rng.uniform(3.2, 4.4) * s)))
    top = body & (Yp < first[None, :] + cap)
    edge_top, edge_foot = hw * rng.uniform(0.30, 0.42), hw * rng.uniform(0.40, 0.52)
    arris = edge_foot + (edge_top - edge_foot) * np.clip(-g.Y / H, 0, 1) + tl * np.clip(-g.Y / H, 0, 1)
    side = body & ~top & (g.X > arris)
    front = body & ~top & ~side
    sp.add('front', front, fam, base=3, lo=1, hi=4, z=1, mode='form', k=0.9)
    sp.add('side', side, fam + '_cool', base=2, lo=0, hi=2, z=1.1, flat=True)
    sp.add('top', top, fam + '_warm', base=4, lo=2, hi=5, z=1.2, flat=True)
    # the top: lit at its west end, a tone down towards the east, its back rim a crest
    sp.mark('top', g.X < peak_x - hw * 0.15, 1)
    sp.mark('top', g.X > arris, -1)
    sp.mark('top', Yp >= first[None, :] + cap - max(1, int(round(s))), -1)
    # the side: lighter at its lit arris, darkest at the far edge and the foot
    sp.mark('side', g.X < arris + 1.2, 1)
    # the arris on the face: one lit run where it turns
    ar = ndi.binary_dilation(side, iterations=1) & front
    sp.mark('front', ar & (g.Y < -H * 0.15), 1)
    # facets: the face is two or three chipped planes, not one smooth bulge. The upper-left
    # plane leans to the light (a tone up), a low plane on the east is a recess (a tone down);
    # where a plane meets the one below it, the lower plane's top row catches the light.
    u1, u2 = rng.uniform(0.5, 0.68), rng.uniform(0.62, 0.82)
    cut = -H * u1 + (g.X + hw) / max(1.0, (arris.max() + hw)) * (-H * u2 + H * u1)
    up = front & (g.Y < cut)
    sp.mark('front', up, 1)
    sp.mark('front', up & (g.X < -hw * 0.35 + tl) & (g.Y < -H * 0.62), 1)   # the light's own corner
    rim = ndi.binary_dilation(up, iterations=1) & front & ~up
    sp.mark('front', rim, 1)
    sp.mark('front', ndi.binary_dilation(rim, iterations=1) & front & ~up & ~rim, -1)
    if rng.random() < 0.8:
        cx0 = rng.uniform(-hw * 0.1, hw * 0.25)
        rec = front & (g.X > cx0 + (g.Y + H * 0.08) * 0.35) & (g.Y > -H * rng.uniform(0.28, 0.4))
        sp.mark('front', rec, -1)
        sp.mark('front', ndi.binary_dilation(rec, iterations=1) & front & ~rec, 1)
    # cluster texture: sparse dark grain everywhere, a few lit grains up on the light
    nz = ndi.gaussian_filter(rng.random((Hp, Wp)), max(0.9, 0.85 * s))
    nz = (nz - nz[body].mean()) / (nz[body].std() + 1e-6)
    for nm, hi_, lo_ in (('front', 1.25, -1.15), ('side', 1.6, -1.3), ('top', 1.4, -1.4)):
        sp.mark(nm, (nz > hi_) & (g.Y < -H * 0.45), 1)
        sp.mark(nm, nz < lo_, -1)
    # bedding lines across the slab (broken), a tone down
    for j in range(int(rng.integers(1, 3))):
        y0 = -H * rng.uniform(0.28, 0.72)
        sl = rng.uniform(-0.12, 0.12)
        ln = g.line([(-hw - 2, y0 - sl * hw), (hw + 2, y0 + sl * hw)], 1)
        gaps = ndi.gaussian_filter(rng.random((Hp, Wp)), 1.5 * s) > 0.5
        ln &= ~gaps
        for nm in ('front', 'side'):
            sp.mark(nm, ln, -1)
    # cracks: from a rim inward and down, a dark line with its lit lip above-left
    ncr = 2 + int(rng.random() < 0.6)
    for j in range(ncr):
        on_left = j % 2 == 0
        x0 = (-hw if on_left else rng.uniform(-hw * 0.3, hw * 0.2)) + tl * 0.5
        y0 = -H * rng.uniform(0.45, 0.9)
        pts_c = [(x0, y0)]
        x, y = x0, y0
        for k in range(int(rng.integers(3, 5))):
            x += rng.uniform(1.2, 3.2) * (1 if on_left else rng.choice([-1, 1]))
            y += rng.uniform(1.5, 3.5)
            pts_c.append((x, y))
        ln = g.line(pts_c, 1) & body
        lip = np.zeros_like(ln)
        lip[:-1, :] |= ln[1:, :]
        lip[:, :-1] |= ln[:, 1:]
        lip &= ~ln
        for nm in ('front', 'side', 'top'):
            sp.mark(nm, ln, -2)
            sp.mark(nm, lip, 1)
    # pits: the hollow a tone down, its lower-right wall (turned to the upper-left light) lit
    for _ in range(int(W * H / 140)):
        k = int(rng.integers(0, len(ys)))
        py, px = ys[k], xs[k]
        if not front[py, px]:
            continue
        r = max(1, int(round(0.7 * s)))
        pit = (np.abs(Yp - py) < r) & (np.abs(Xp - px) < r + 1)
        rim = np.roll(np.roll(pit, r, 0), r, 1) & ~pit
        sp.mark('front', pit, -1)
        sp.mark('front', rim, 1)
    # the foot: darker where it meets the ground
    foot = g.Y > -max(2.0, 2.2)
    sp.mark('front', foot, -1)
    sp.mark('side', foot, -1)
    # lichen: rosettes in clusters, on the top and the lit face's upper half
    lich_pale = np.zeros((Hp, Wp), bool)
    lich_yel = np.zeros((Hp, Wp), bool)
    for _ in range(int(rng.integers(2, 4))):
        cx = rng.uniform(-hw * 0.8, hw * 0.2) + tl * 0.7
        cy = -H * rng.uniform(0.55, 0.95)
        for k in range(int(rng.integers(3, 6))):
            m = g.ellipse(cx + _jit(rng, 2.2), cy + _jit(rng, 1.8), rng.uniform(0.9, 1.7), rng.uniform(0.8, 1.4))
            (lich_yel if rng.random() < 0.55 else lich_pale)[...] |= m
    lich_yel &= body & ~side
    lich_pale &= body & ~side & ~lich_yel
    if lich_pale.any():
        sp.add('lichen_pale', lich_pale, 'plaster', base=3, lo=2, hi=4, z=2, flat=True, outline=False, casts=False)
        sp.mark('lichen_pale', lich_pale & ~ndi.binary_erosion(lich_pale) & (g.X < 0), 1)
    if lich_yel.any():
        sp.add('lichen', lich_yel, 'grass_warm', base=4, lo=3, hi=5, z=2.1, flat=True, outline=False, casts=False)
        rim = lich_yel & ~ndi.binary_erosion(lich_yel)
        sp.mark('lichen', rim & (g.X > cx), -1)
        sp.mark('lichen', ndi.binary_erosion(lich_yel, iterations=max(1, int(s))) & (nz > 0), 1)
    # moss on the foot's shaded side and in the lowest crack
    moss = np.zeros((Hp, Wp), bool)
    for _ in range(int(rng.integers(2, 4))):
        mx = rng.uniform(-hw * 0.3, hw * 0.9)
        moss |= g.ellipse(mx, -rng.uniform(0.5, 2.0), rng.uniform(2.0, 4.0), rng.uniform(1.2, 2.2))
    moss &= body
    if moss.any():
        sp.add('moss', moss, 'grass_cool', base=2, lo=1, hi=3, z=2.2, flat=True, outline=False, casts=False)
        sp.mark('moss', moss & ~ndi.binary_erosion(moss) & (g.Y < -1.0), 1)
        sp.mark('moss', g.Y > -1.0, -1)
    return _out(sp)


KINDS = {
    'standing_stone': dict(w=16, h=29),
    'standing_stone_b': dict(w=17, h=29),
    'standing_stone_low': dict(w=15, h=21),
}
