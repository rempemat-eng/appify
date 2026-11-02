"""The village kit: a storm-broken valley village drawn natively at any density, in palette
codes only (Crossroads, docs/vision/vertical-slice.md; the valley's forms: dry stone, slate
and thatch, timber frames, painted doors and shutters, art-style.md "the valley and the isles").

Every picture is a code canvas (family * 8 + tone, -1 nothing) closed with the house outline and
cleared of lone pixels, written once to RGBA. Units are world px (`q` makes texels at ctx.D), so
the same building is drawn at every density; Bramble is 74 texels tall at density 3 and a door
is about 1.3 of him.

    building(spec, seed)  -> Built(base, damage, info)   a cottage, the library, the forge or the hut
    prop(kind, w, h, seed) -> Pic                          well, rubble, stall, anvil, lantern ...

A building is drawn once; its damage (missing slates, roof holes, tarps, boards over doors and
windows, scaffolding) is a second picture of the same size and anchor laid over it, so a restore
stage removes it whole (world/conditional.gd) and the building underneath is complete.
Light from the upper left: every piece (a stone, a slate, a plank) has a lit top and west edge
and a dark foot and east edge; the east end of a front is a step darker than the west.
"""
from __future__ import annotations

import inspect
import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import ctx
from .palette import FI, to_rgba

D = ctx.D
HD = D >= 2.5           # density 3 and up (a constant, never switched): callers pass it as `hd` to building() and prop()


def q(v) -> int:
    """World px as whole texels at this density."""
    return int(round(v * D))


def code(fam: str, t: int) -> int:
    return FI[fam] * 8 + int(t)


def tone_of(c):
    return np.asarray(c) % 8


def fam_of(c):
    return np.asarray(c) // 8


STONES = ('stone', 'stone_warm', 'stone_cool')
SLATES = ('slate', 'slate', 'slate_cool')
TIMBER = ('timber', 'timber_warm', 'timber_cool')
NO_EDGE = {'lamp', 'lava', 'glowflora'}          # light sources: no outline round them


# ------------------------------------------------------------------------------------------------
# the canvas
# ------------------------------------------------------------------------------------------------
class Pic:
    """A sprite in codes: W x H texels, its foot (the ground point under it) at (ax, ay)."""

    def __init__(self, W: int, H: int, ax: int, ay: int):
        self.a = np.full((H, W), -1, np.int32)
        self.ax, self.ay = int(ax), int(ay)

    @property
    def W(self):
        return self.a.shape[1]

    @property
    def H(self):
        return self.a.shape[0]

    def rgba(self) -> Image.Image:
        return Image.fromarray(to_rgba(self.a), 'RGBA')

    def alpha(self) -> np.ndarray:
        return self.a >= 0


def _box(a, x0, y0, x1, y1):
    H, W = a.shape
    return max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))


def fill(a, x0, y0, x1, y1, c, where=None):
    x0, y0, x1, y1 = _box(a, x0, y0, x1, y1)
    if x1 <= x0 or y1 <= y0:
        return
    if where is None:
        a[y0:y1, x0:x1] = c
    else:
        sub = a[y0:y1, x0:x1]
        sub[where[y0:y1, x0:x1]] = c


def edges(m):
    """Top, left, bottom and right edge pixels of a mask."""
    up = np.zeros_like(m)
    up[1:] = m[:-1]
    dn = np.zeros_like(m)
    dn[:-1] = m[1:]
    lf = np.zeros_like(m)
    lf[:, 1:] = m[:, :-1]
    rt = np.zeros_like(m)
    rt[:, :-1] = m[:, 1:]
    return m & ~up, m & ~lf, m & ~dn, m & ~rt


def chamfer(h, w, cut):
    m = np.ones((h, w), bool)
    for i in range(min(cut, h)):
        k = cut - i
        m[i, :k] = False
        m[i, max(0, w - k):] = False
        m[h - 1 - i, :k] = False
        m[h - 1 - i, max(0, w - k):] = False
    return m


def shade(m, t, top=1, left=1, bot=-1, right=-1):
    """Tones for a piece lit from the upper left: lit top and west edges, dark foot and east edge."""
    T, L, B, R = edges(m)
    tt = np.full(m.shape, t, int)
    tt[R] += right
    tt[B] += bot
    tt[L & ~B] += left
    tt[T] += top
    return np.clip(tt, 0, 5)


def put(a, x0, y0, m, fam, tones, where=None):
    """Write a local mask m with per-pixel tones (or one tone) at (x0, y0)."""
    h, w = m.shape
    X0, Y0, X1, Y1 = _box(a, x0, y0, x0 + w, y0 + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    sm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    if where is not None:
        sm = sm & where[Y0:Y1, X0:X1]
    tt = tones if np.ndim(tones) == 0 else tones[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    sub = a[Y0:Y1, X0:X1]
    if np.ndim(fam) == 0:
        val = FI[fam] * 8 + tt
    else:
        val = np.vectorize(lambda f: FI[f])(fam[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]) * 8 + tt
    if np.ndim(val) == 0:
        sub[sm] = val
    else:
        sub[sm] = val[sm]


def blk(a, x0, y0, x1, y1, fam, t, cut=1, top=1, left=1, bot=-1, right=-1, where=None, hd=False):
    """A block (stone, slate, plank, board) with chamfered corners, lit from the upper left."""
    w, h = int(x1 - x0), int(y1 - y0)
    if w < 1 or h < 1:
        return
    m = chamfer(h, w, cut if (w > 2 * cut and h > 2 * cut) else 0)
    tt = shade(m, t, top, left, bot, right)
    if hd and h >= 5 and w >= 5 and bot < 0 and t >= 4:
        # a bright block (a quoin, a lintel, a sill) keeps its brightness on its top and arris
        # and its body a step down, so it still has a face that turns
        top, t = top + (t - 3), 3
        tt = shade(m, t, top, left, bot, right)
    if hd and h >= 5 and w >= 5 and bot < 0:
        # density 3: a block has a top face, a front and an underside: the row under the lit top
        # still catches some light, the row over the foot falls into its own shade
        T_, _, B_, _ = edges(m)
        up2 = np.zeros_like(T_)
        up2[1:] = T_[:-1]
        tt = np.where(up2 & m & ~B_, np.minimum(5, t + 1), tt)
        rows_ = np.arange(h)[:, None] * np.ones((1, w), int)
        low3 = (rows_ >= h - max(1, h // 3)) & m & ~B_
        tt = np.where(low3 & (tt == t), t - 1, tt)                  # the face turning under
        tt = np.where(B_, np.maximum(0, t - 2), tt)
        tt = np.clip(tt, 0, 5)
    put(a, int(x0), int(y0), m, fam, tt, where)


def seg_mask(shape, x0, y0, x1, y1, r):
    """A capsule from (x0, y0) to (x1, y1), radius r texels, on a canvas of `shape`."""
    H, W = shape
    bx0, bx1 = int(max(0, min(x0, x1) - r - 1)), int(min(W, max(x0, x1) + r + 2))
    by0, by1 = int(max(0, min(y0, y1) - r - 1)), int(min(H, max(y0, y1) + r + 2))
    m = np.zeros(shape, bool)
    if bx1 <= bx0 or by1 <= by0:
        return m
    Y, X = np.mgrid[by0:by1, bx0:bx1] + 0.5
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1e-9
    t = np.clip(((X - x0) * dx + (Y - y0) * dy) / L2, 0, 1)
    m[by0:by1, bx0:bx1] = (X - x0 - t * dx) ** 2 + (Y - y0 - t * dy) ** 2 <= r * r
    return m


def bar(a, x0, y0, x1, y1, r, fam, t, where=None):
    """A pole, board or rope between two points, shaded as one piece."""
    m = seg_mask(a.shape, x0, y0, x1, y1, r)
    if where is not None:
        m &= where
    tt = shade(m, t)
    a[m] = FI[fam] * 8 + tt[m]
    return m


def ellipse_mask(shape, cx, cy, rx, ry):
    H, W = shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    return ((X - cx) / max(rx, 0.5)) ** 2 + ((Y - cy) / max(ry, 0.5)) ** 2 <= 1.0


def blob(a, m, fam, t, **kw):
    tt = shade(m, t, **kw)
    a[m] = FI[fam] * 8 + tt[m]


def outline(a, keep_lit=True):
    """Close the silhouette: one texel in the edge tone of the material it closes (tone 1 of that
    material on the lit top and west sides). Light sources get no outline."""
    m = a >= 0
    out = np.full(a.shape, -1, np.int32)
    H, W = a.shape
    for dy, dx, lit in ((1, 0, False), (-1, 0, True), (0, 1, False), (0, -1, True)):
        # the neighbour inside the shape is at (y - dy, x - dx) seen from the outline pixel
        src = np.full(a.shape, -1, np.int32)
        ys = slice(max(0, dy), H + min(0, dy))
        yd = slice(max(0, -dy), H + min(0, -dy))
        xs = slice(max(0, dx), W + min(0, dx))
        xd = slice(max(0, -dx), W + min(0, -dx))
        src[ys, xs] = a[yd, xd]
        cand = (~m) & (src >= 0) & (out < 0)
        if not cand.any():
            continue
        f = src // 8
        val = np.where(lit and keep_lit, f * 8 + 1, f * 8 + 6)
        for nf in NO_EDGE:
            if nf in FI:
                cand &= f != FI[nf]
        out[cand] = val[cand]
    a[out >= 0] = out[out >= 0]
    return a


def tidy(a, passes=2, keep=None):
    """No lone pixels: a pixel unlike all four neighbours takes its most common neighbour."""
    for _ in range(passes):
        P = np.pad(a, 1, constant_values=-2)
        nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
        lone = (a >= 0) & (a != nb[0]) & (a != nb[1]) & (a != nb[2]) & (a != nb[3])
        if keep is not None:
            lone &= ~keep
        ys, xs = np.nonzero(lone)
        for y, x in zip(ys, xs):
            v = [int(c) for c in nb[:, y, x] if c >= 0]
            if v:
                a[y, x] = max(set(v), key=v.count)
    return a


def finish(p: Pic, line=True) -> Pic:
    tidy(p.a)
    if line:
        outline(p.a)
        tidy(p.a, passes=1)
    return p


# ------------------------------------------------------------------------------------------------
# surfaces
# ------------------------------------------------------------------------------------------------
def rubble(a, x0, y0, x1, y1, rng, fams=STONES, base=3, course=(2.4, 3.8), length=(3.5, 8.5),
           moss=0.18, east_dark=True, where=None, mortar=('stone', 1), hd=False):
    """Dry stone in courses: every stone its own tone and sibling, lit on its top and west edges,
    dark joints between; moss in some lower joints; the east third a step darker."""
    fill(a, x0, y0, x1, y1, code(*mortar), where)
    y = y1
    k = 0
    while y > y0 + 1:
        h = max(3, q(rng.uniform(*course)))
        yt = max(y0, y - h)
        x = x0 - int(rng.integers(0, max(1, q(length[1]))))
        while x < x1:
            L = max(4, q(rng.uniform(*length)))
            t = base + int(rng.choice([-1, 0, 0, 0, 1]))
            if east_dark and x > x0 + 0.66 * (x1 - x0) and rng.random() < 0.6:
                t -= 1
            sx0, sx1 = max(x, x0), min(x + L - 1, x1)
            if sx1 - sx0 >= 2:
                blk(a, sx0, yt, sx1, y - 1, fams[int(rng.integers(0, len(fams)))], t,
                    cut=1 if h < q(3.5) else 2, where=where, hd=hd)
                if moss and y > y1 - (y1 - y0) * 0.45 and rng.random() < moss:
                    mx = int(rng.integers(sx0, max(sx0 + 1, sx1 - 2)))
                    mw = int(rng.integers(2, 5))
                    fill(a, mx, yt, mx + mw, yt + 2, code('leaf', 3 + int(rng.integers(0, 2))), where)
            x += L
        y = yt
        k += 1


def ashlar(a, x0, y0, x1, y1, rng, base=3, course=4.0, length=(7, 11), where=None, hd=False):
    """Dressed stone: even courses, long blocks, fine joints, a lit arris on each block."""
    fill(a, x0, y0, x1, y1, code('ashlar', 1), where)
    y = y1
    k = 0
    while y > y0 + 1:
        h = q(course)
        yt = max(y0, y - h)
        x = x0 - (q(length[0] / 2) if k % 2 else 0)
        while x < x1:
            L = q(rng.uniform(*length))
            t = base + int(rng.choice([-1, 0, 0, 1]))
            if x > x0 + 0.7 * (x1 - x0) and rng.random() < 0.5:
                t -= 1
            sx0, sx1 = max(x, x0), min(x + L - 1, x1)
            if sx1 - sx0 >= 2:
                fa_ = ('ashlar', 'ashlar_warm', 'ashlar')[int(rng.integers(0, 3))]
                blk(a, sx0, yt, sx1, y - 1, fa_, min(t, 3) if hd else t, cut=1, where=where, hd=hd)
                if hd:
                    # the mason's tooling: short diagonal strokes across the dressed face
                    for _ in range(max(1, (sx1 - sx0) // q(3))):
                        tx = int(rng.integers(sx0 + 2, max(sx0 + 3, sx1 - 2)))
                        ty = int(rng.integers(yt + 2, max(yt + 3, y - 3)))
                        fill(a, tx, ty, tx + 1, ty + 1, code(fa_, max(0, min(t, 3) - 1)), where)
                        fill(a, tx + 1, ty + 1, tx + 2, ty + 2, code(fa_, max(0, min(t, 3) - 1)), where)
            x += L
        y = yt
        k += 1


def planks(a, x0, y0, x1, y1, rng, fams=TIMBER, base=3, width=3.0, vertical=True, grain=True, where=None, hd=False):
    """Boards side by side with dark seams; each board its own tone, grain dashes and a knot."""
    fill(a, x0, y0, x1, y1, code(fams[0], 1), where)
    if vertical:
        x = x0
        while x < x1:
            w = max(3, q(width * rng.uniform(0.85, 1.15)))
            t = base + int(rng.choice([-1, 0, 0, 1]))
            f = fams[int(rng.integers(0, len(fams)))]
            blk(a, x, y0, min(x + w - 1, x1), y1, f, t, cut=0, top=0, where=where, hd=hd)
            if grain:
                for _ in range(max(1, (y1 - y0) // q(3 if hd else 6))):
                    gx = int(rng.integers(x + 1, max(x + 2, x + w - 2)))
                    gy = int(rng.integers(y0, max(y0 + 1, y1 - 4)))
                    fill(a, gx, gy, gx + 1, gy + q(rng.uniform(2, 4)), code(f, max(0, t - 1)), where)
                    if hd and rng.random() < 0.5:
                        fill(a, gx + 1, gy + 1, gx + 2, gy + q(rng.uniform(1, 2.5)), code(f, min(5, t + 1)), where)
            x += w
    else:
        y = y0
        while y < y1:
            h = max(3, q(width * rng.uniform(0.85, 1.15)))
            t = base + int(rng.choice([-1, 0, 0, 1]))
            f = fams[int(rng.integers(0, len(fams)))]
            blk(a, x0, y, x1, min(y + h - 1, y1), f, t, cut=0, left=0, where=where, hd=hd)
            if grain:
                for _ in range(max(1, (x1 - x0) // q(7))):
                    gy = int(rng.integers(y + 1, max(y + 2, y + h - 2)))
                    gx = int(rng.integers(x0, max(x0 + 1, x1 - 6)))
                    fill(a, gx, gy, gx + q(rng.uniform(2, 5)), gy + 1, code(f, max(0, t - 1)), where)
            y += h


def beam(a, x0, y0, x1, y1, rng, fam='timber', t=2, where=None, hd=False):
    """A timber beam or post: lit top and west, dark foot, grain dashes along its length. At
    density 3 a squared timber in three planes: a lit top (or west) face, the front, the shaded
    underside (or east face), its ends showing their grain, checks along it."""
    w, h = x1 - x0, y1 - y0
    if hd and min(w, h) >= 4:
        H_, W_ = a.shape
        Y, X = np.mgrid[0:H_, 0:W_]
        m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
        if where is not None:
            m &= where
        tt = np.full(a.shape, t, int)
        if w >= h:
            k = max(1, int(round(h * 0.3)))
            tt[(Y < y0 + k)] = t + 1
            tt[Y == int(y0)] = t + 2
            tt[Y >= y1 - max(1, int(round(h * 0.25)))] = t - 1
            tt[Y == int(y1) - 1] = t - 2
            tt[(X < x0 + q(0.7)) & (Y > y0)] = t + 1               # the west end's grain, lit
            tt[(X >= x1 - q(0.7)) & (Y > y0)] = t - 1
        else:
            k = max(1, int(round(w * 0.3)))
            tt[X < x0 + k] = t + 1
            tt[X == int(x0)] = t + 2
            tt[X >= x1 - max(1, int(round(w * 0.3)))] = t - 1
            tt[X == int(x1) - 1] = t - 2
            tt[(Y < y0 + q(0.7))] = np.minimum(tt[(Y < y0 + q(0.7))] + 1, 5)
        a[m] = FI[fam] * 8 + np.clip(tt, 0, 5)[m]
        # checks and grain along it, a tone down, broken
        n = max(1, max(w, h) // q(6))
        for _ in range(n):
            if w >= h:
                gx = int(rng.integers(x0 + 1, max(x0 + 2, x1 - q(3))))
                gy = int(rng.integers(y0 + max(1, h // 3), max(y0 + max(1, h // 3) + 1, y1 - 1)))
                fill(a, gx, gy, gx + q(rng.uniform(1.5, 4)), gy + 1, code(fam, max(0, t - 1)), m)
            else:
                gx = int(rng.integers(x0 + max(1, w // 3), max(x0 + max(1, w // 3) + 1, x1 - 1)))
                gy = int(rng.integers(y0 + 1, max(y0 + 2, y1 - q(3))))
                fill(a, gx, gy, gx + 1, gy + q(rng.uniform(1.5, 4)), code(fam, max(0, t - 1)), m)
        return
    blk(a, x0, y0, x1, y1, fam, t, cut=0, where=where, hd=hd)
    if w >= h:
        for _ in range(max(1, w // q(8))):
            gx = int(rng.integers(x0 + 1, max(x0 + 2, x1 - 4)))
            gy = int(rng.integers(y0 + 1, max(y0 + 2, y1 - 1)))
            fill(a, gx, gy, gx + q(rng.uniform(1.5, 3)), gy + 1, code(fam, max(0, t - 1)), where)
    else:
        for _ in range(max(1, h // q(8))):
            gy = int(rng.integers(y0 + 1, max(y0 + 2, y1 - 4)))
            gx = int(rng.integers(x0 + 1, max(x0 + 2, x1 - 1)))
            fill(a, gx, gy, gx + 1, gy + q(rng.uniform(1.5, 3)), code(fam, max(0, t - 1)), where)


def plaster(a, x0, y0, x1, y1, rng, fam='plaster', base=3, where=None, hd=False):
    """Lime plaster: a calm body, a shade band under the beam above, damp in the lower third,
    a few patches where it has fallen and the stone shows."""
    fill(a, x0, y0, x1, y1, code(fam, base), where)
    fill(a, x0, y0, x1, y0 + max(2, q(1.2)), code(fam, base - 1), where)
    h = y1 - y0
    for _ in range(max(1, (x1 - x0) * h // (q(14) * q(10)))):
        cx = rng.uniform(x0, x1)
        cy = rng.uniform(y0 + h * 0.55, y1)
        m = ellipse_mask(a.shape, cx, cy, q(rng.uniform(2, 4)), q(rng.uniform(1.2, 2.2)))
        m &= _rect(a.shape, x0, y0, x1, y1)
        if where is not None:
            m &= where
        a[m] = code(fam + '_warm' if fam == 'plaster' else fam, base - 1)
    if (x1 - x0) > q(10) and rng.random() < 0.7:
        cx = rng.uniform(x0 + q(3), x1 - q(6))
        cy = rng.uniform(y0 + q(3), y1 - q(5))
        pw, ph = q(rng.uniform(4, 6)), q(rng.uniform(2.5, 3.5))
        rubble(a, int(cx), int(cy), int(cx) + pw, int(cy) + ph, rng, base=2, course=(1.6, 2.0), length=(2.5, 4),
               moss=0, east_dark=False, where=where, hd=hd)


def _rect(shape, x0, y0, x1, y1):
    m = np.zeros(shape, bool)
    H, W = shape
    m[max(0, int(y0)):min(H, int(y1)), max(0, int(x0)):min(W, int(x1))] = True
    return m


# ------------------------------------------------------------------------------------------------
# pieces with faces: sawn boards, nails, blocks seen from above the front
# ------------------------------------------------------------------------------------------------
def board(a, x0, y0, length, th, ang, fam, t, rng, split=True, grain=True, where=None):
    """A sawn plank from (x0, y0) along `ang` degrees, `length` and `th` texels: square ends (the cut
    end grain a tone up at the start, a tone down at the far end), a lit top arris, a dark lower
    arris, grain lines along it, sometimes a split running in from one end. Returns its mask."""
    H, W = a.shape
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pad = int(length + th + 4)
    bx0, by0 = max(0, int(x0 - pad)), max(0, int(y0 - pad))
    bx1, by1 = min(W, int(x0 + pad)), min(H, int(y0 + pad))
    Y, X = np.mgrid[by0:by1, bx0:bx1] + 0.5
    u = (X - x0) * c + (Y - y0) * s
    v = -(X - x0) * s + (Y - y0) * c
    m = (u >= 0) & (u < length) & (v >= 0) & (v < th)
    if where is not None:
        m &= where[by0:by1, bx0:bx1]
    tt = np.full(m.shape, t, int)
    if grain:
        for _ in range(max(1, int(th // 3))):
            vg = rng.uniform(1.5, max(1.6, th - 1.5))
            run = ((u // max(4, length / rng.uniform(2, 4))).astype(int) % 3) != 0
            tt[(np.abs(v - vg) < 0.5) & run] = t - 1
        kn = rng.uniform(length * 0.2, length * 0.8)
        tt[((u - kn) ** 2 / 4.0 + (v - th / 2) ** 2) < 1.2] = t - 2
    tt[v < 1] = t + 1
    tt[v >= th - 1] = t - 1
    tt[u < 1.2] = t + 1
    tt[u >= length - 1.2] = t - 1
    if split:
        tt[(np.abs(v - th * rng.uniform(0.35, 0.65)) < 0.5) & (u > length - rng.uniform(length * 0.12, length * 0.25))] = t - 2
    tt = np.clip(tt, 0, 5)
    sub = a[by0:by1, bx0:bx1]
    sub[m] = FI[fam] * 8 + tt[m]
    full = np.zeros(a.shape, bool)
    full[by0:by1, bx0:bx1] = m
    return full


def nail(a, x, y, rust=True, rng=None):
    """A forged nail: a square head, lit on its upper left, and a rust streak run down below it."""
    k = max(2, q(0.9))
    fill(a, x, y, x + k, y + k, code('iron', 1))
    fill(a, x, y, x + k - 1, y + 1, code('iron', 4))
    fill(a, x, y, x + 1, y + k - 1, code('iron', 4))
    if rust:
        L_ = q(1.2) + (int(rng.integers(0, q(1.5))) if rng is not None else 0)
        fill(a, x + k // 2, y + k, x + k // 2 + 1, y + k + L_, code('fox', 2))
        fill(a, x + k // 2, y + k, x + k // 2 + 1, y + k + max(1, L_ // 2), code('fox', 1))


def sack(a, cx, cy, rx, ry, fam='plaster_warm'):
    """A filled sack as a volume: lit on its upper left, a core shadow down its lower right, a
    reflected rim, a tied neck with its folds."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    m = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1
    d = ((X - cx) / rx) * 0.7 + ((Y - cy) / ry) * 0.7
    tt = np.select([d < -0.55, d < -0.1, d < 0.45, d < 0.85], [5, 4, 3, 2], 3)
    a[m] = FI[fam] * 8 + tt[m]
    a[m & (np.abs(X - cx - rx * 0.15) < 1) & (Y > cy - ry * 0.2)] = code(fam, 2)          # a fold
    fill(a, int(cx - q(1.3)), int(cy - ry - q(1.6)), int(cx + q(1.3)), int(cy - ry + 1), code(fam, 3))
    fill(a, int(cx - q(1.3)), int(cy - ry - q(0.4)), int(cx + q(1.3)), int(cy - ry + 1), code('timber_warm', 2))


def cyl_tones(u, base=3):
    """Tones across a cylinder lit from the upper left (u from -1 at the west edge to 1 at the east):
    a reflected rim, the highlight band, the body, the core shadow, the reflected light."""
    return np.select([u < -0.8, u < -0.25, u < 0.25, u < 0.75], [base, base + 2, base, base - 2], base - 1)


def stone_chunk(a, x0, y0, w, h, fam, t, rng):
    """A rough stone as a volume: a lit top face (its upper third), a mid front, a dark east flank, a
    chamfered outline."""
    if w < 3 or h < 3:
        return
    m = chamfer(h, w, 2 if (w > 6 and h > 6) else 1)
    tt = np.full(m.shape, t, int)
    topn = max(1, h // 3)
    tt[:topn, :] = t + 1
    tt[:, int(w * 0.72):] = t - 1
    tt[:topn, int(w * 0.72):] = t
    tt[-1, :] = t - 2
    T_, L_, _, _ = edges(m)
    tt[T_] = t + 2
    put(a, int(x0), int(y0), m, fam, np.clip(tt, 0, 5))


def rune_groove(a, pts_list, within, r=None):
    """A rune cut into stone along curves: a groove glowing softly, its upper lip in shade and its lower
    lip catching the light."""
    r = r or max(1.2, q(0.45))
    g = np.zeros(a.shape, bool)
    for pts in pts_list:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            g |= seg_mask(a.shape, x0, y0, x1, y1, r)
    g &= within
    up_lip = np.roll(g, -1, axis=0) & ~g & within
    lo_lip = np.roll(g, 1, axis=0) & ~g & within
    a[g] = code('sky', 3)
    core = g & np.roll(g, 1, axis=0) & np.roll(g, -1, axis=0) & np.roll(g, 1, axis=1) & np.roll(g, -1, axis=1)
    a[core] = code('sky', 4)
    a[up_lip] = code('stone', 1)
    a[lo_lip] = code('stone', 5)


def curve(x0, y0, x1, y1, bend, n=8):
    """Points along a gentle arc from (x0, y0) to (x1, y1), bowed sideways by `bend` texels."""
    out = []
    for k in range(n + 1):
        t = k / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        dx, dy = y1 - y0, -(x1 - x0)
        L_ = math.hypot(dx, dy) or 1
        b = bend * 4 * t * (1 - t)
        out.append((x + dx / L_ * b, y + dy / L_ * b))
    return out


def prism(a, x0, y0, x1, y1, top, fam, t=3, side=0, bevel=True, where=None):
    """A block seen from above the front, three planes: the top face lit (`top` texels deep, its
    front arris chamfered and catching the light), the front face in mid tone with a lit west arris,
    the east side face in shade (its top corner cut on the diagonal), a dark contact row at the foot."""
    if x1 <= x0 or y1 <= y0:
        return
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    if where is not None:
        m &= where
    topm = m & (Y < y0 + top)
    front = m & ~topm
    a[topm] = code(fam, min(5, t + 1))
    a[topm & (Y == y0)] = code(fam, min(5, t + 2))
    a[front] = code(fam, t)
    if bevel:
        a[m & (Y == y0 + top)] = code(fam, min(5, t + 2))
        a[front & (X == x0)] = code(fam, min(5, t + 1))
    if side:
        sm = m & (X >= x1 - side) & ((X - (x1 - side)) >= (Y - y0) * 0 + (y0 + top - Y))
        a[sm & ~topm] = code(fam, max(0, t - 2))
        a[sm & topm & ((X - (x1 - side)) > (y0 + top - Y))] = code(fam, max(0, t - 1))
        a[m & (X == x1 - side) & ~topm] = code(fam, max(0, t - 3))     # the shade where the faces meet
    a[m & (Y == y1 - 1)] = code(fam, max(0, t - 2))


# ------------------------------------------------------------------------------------------------
# roofs
# ------------------------------------------------------------------------------------------------
def roof_mask(shape, x0, x1, y_ridge, y_eave, hip=0.0, round_=0):
    """The roof plane seen from the south: a rectangle (gable) or a trapezoid (hip, the ridge
    shortened by `hip` texels each side)."""
    H, W = shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    f = np.clip((y_eave - Y) / max(1, (y_eave - y_ridge)), 0, 1)
    l = x0 + hip * f
    r = x1 - hip * f
    m = (Y >= y_ridge) & (Y < y_eave) & (X >= l) & (X < r)
    if round_:
        m = ndi.binary_opening(m, structure=np.ones((round_, round_), bool)) | (m & (Y > y_ridge + round_))
    return m


def slate_roof(a, m, x0, x1, y_ridge, y_eave, rng, row=3.2, width=(4.2, 6.4), fams=SLATES, moss=0.06, patch=0.05, hip=0, hd=False):
    """Slates in overlapping rows: each slate its own tone, its butt (lower edge) lit, the shade of
    the row above across its head, dark joints; west lighter than east; moss on a few butts."""
    fill(a, x0, y_ridge, x1, y_eave, code('slate', 1), m)
    rh = max(4, q(row))
    nrows = int(math.ceil((y_eave - y_ridge) / rh))
    y = y_eave
    k = 0
    span = max(1, x1 - x0)
    while y > y_ridge:
        yt = y - rh
        x = x0 - (q(width[0] / 2) if k % 2 else 0) - int(rng.integers(0, 3))
        while x < x1:
            w = max(5, q(rng.uniform(*width)))
            fx = (x - x0) / span
            t = 3 if rng.random() > fx * 1.1 - 0.1 else 2
            if k >= nrows - 2:
                t += 1                      # the rows under the ridge catch the light
            if rng.random() < 0.1:
                t += int(rng.choice([-1, 1]))
            f = fams[int(rng.integers(0, len(fams)))]
            if rng.random() < patch:
                f = fams[0] + '_warm' if fams[0] + '_warm' in FI else f   # a replaced slate
            sm = chamfer(rh - 1, w - 1, 1)
            tt = np.full(sm.shape, t, int)
            tt[-1, :] = t + 1                    # the butt catches the light
            tt[:max(1, rh // 4), :] = t - 1      # the row above shades its head
            if hd:
                # density 3: a slate is a thin plate tilted to the sky: its lower part a step
                # brighter than its head, its butt's arris brightest, the west edge lit
                t = min(t, 3)
                fc_ = (y_eave - (yt + rh / 2)) / max(1, y_eave - y_ridge)
                if hip and x + w / 2 < x0 + hip * fc_:
                    t = 3                             # the west hip slope, turned to the light
                tt[:, :] = t
                lo_ = max(2, rh // 3 + 1)
                tt[lo_:-1, :] = t + 1
                ww_ = sm.shape[1]
                tt[lo_:-1, :max(1, int(ww_ * 0.22))] = min(5, t + 2)       # its west end turned to the light
                tt[lo_:-1, int(ww_ * 0.78):] = t                            # its east end turning away
                sc_ = rng.random(tt.shape) < 0.08                           # the riven face's grain
                tt[sc_ & (np.arange(tt.shape[0])[:, None] >= lo_)] -= 1
                tt[-1, :] = min(5, t + 2)
                tt[:max(1, rh // 4), :] = t - 1
                tt[1:-1, 0] = np.maximum(tt[1:-1, 0], t + 1)
            tt[:, -1] -= 1
            tt = np.clip(tt, 0, 5)
            put(a, x, yt, sm, f, tt, m)
            if moss and k < 4 and rng.random() < moss:
                mx = x + int(rng.integers(0, max(1, w - 4)))
                fill(a, mx, y - 3, mx + int(rng.integers(3, 6)), y - 1, code('leaf', 3), m)
                fill(a, mx + 1, y - 4, mx + 3, y - 3, code('leaf', 4), m)
            x += w
        y = yt
        k += 1
    # the ridge: capping tiles, lit on top
    rc = max(3, q(2.2))
    x = x0
    while x < x1:
        w = q(5)
        blk(a, x, y_ridge, min(x + w - 1, x1), y_ridge + rc, 'clay', 2 if (x - x0) / span > 0.6 else 3, cut=1, where=m, hd=hd)
        x += w


def thatch_roof(a, m, x0, x1, y_ridge, y_eave, rng, fam='sand'):
    """Thatch in courses: straw laid in vertical strands (two-texel stripes a tone apart), each
    course's wavy foot lit and the course below it shaded there; the east third weathered a step
    darker; a thick eave with a dark underside; a ridge roll held by crossed spars."""
    H, W = a.shape
    fill(a, x0, y_ridge, x1, y_eave, code(fam, 2), m)
    ch = max(6, q(6.0))
    span = max(1, x1 - x0)
    y = y_eave
    k = 0
    # strands: each pair of columns its own tone step, run down the whole roof (a few change per
    # course), so the straw reads as long vertical stems, never as weave
    pat = np.repeat(rng.choice([-1, 0, 0, 0, 1], size=W // 2 + 2), 2)[:W + 2]
    warm = np.repeat(rng.random(W // 4 + 2) < 0.2, 4)[:W + 2]
    while y > y_ridge - ch:
        flip = np.repeat(rng.random(W // 2 + 2) < 0.15, 2)[:W + 2]
        pat = np.where(flip, np.repeat(rng.choice([-1, 0, 1], size=W // 2 + 2), 2)[:W + 2], pat)
        wav = np.repeat(rng.integers(-q(0.7), q(0.7) + 1, size=W // max(2, q(3)) + 2), max(2, q(3)))[:W]
        for x in range(max(0, int(x0)), min(W, int(x1))):
            fx = (x - x0) / span
            base = 3 if fx < 0.62 else 2
            foot = y + wav[x]
            for yy in range(foot - ch, foot):
                if not (0 <= yy < H) or not m[yy, x]:
                    continue
                t = base + pat[x]
                if yy == foot - 1:
                    t = base + 1               # the course's foot catches the light
                elif yy == foot - ch:
                    t = base - 1               # in the shade of the course above
                a[yy, x] = code(fam + '_warm' if warm[x] else fam, int(np.clip(t, 0, 5)))
        y -= ch
        k += 1
    # the eave: a thick rolled edge, dark beneath
    em = m & ~np.roll(m, -q(3), axis=0)
    a[em] = code(fam, 2)
    a[em & ~np.roll(m, -q(1.6), axis=0)] = code(fam, 1)
    a[em & ~np.roll(m, -1, axis=0)] = code(fam + '_cool', 0)
    # the ridge roll
    rr = max(6, q(4.5))
    rm_ = m & _rect(a.shape, x0, y_ridge, x1, y_ridge + rr)
    a[rm_] = code(fam, 4)
    a[rm_ & _rect(a.shape, x0, y_ridge + rr - 2, x1, y_ridge + rr)] = code(fam, 1)
    a[rm_ & _rect(a.shape, x0 + span * 0.62, 0, x1, H)] = code(fam, 3)
    sp = q(6)
    for x in range(int(x0) + sp // 2, int(x1) - 2, sp):
        bar(a, x - q(1.5), y_ridge + rr - 1, x + q(1.5), y_ridge + 1, max(0.8, D * 0.4), 'timber', 2, where=m)


def shingle_roof(a, m, x0, x1, y_ridge, y_eave, rng, hd=False):
    """Cedar shingles: like slates but warm timber, shorter rows."""
    slate_roof(a, m, x0, x1, y_ridge, y_eave, rng, row=2.8, width=(3.4, 5.0), fams=('timber_warm', 'timber', 'timber_cool'),
               moss=0.1, hd=hd)


def hip_planes(a, x0, x1, y_ridge, y_eave, hip, cap='clay', hd=False):
    """A hipped roof's end slopes: the west one turned to the light a tone up, the east one a
    tone down, a capped hip line from each eave corner to the ridge's end."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    f = np.clip((y_eave - Y) / max(1, (y_eave - y_ridge)), 0, 1)
    inside = (Y >= y_ridge) & (Y < y_eave) & (a >= 0)
    west = inside & (X < x0 + hip * f)
    east = inside & (X >= x1 - hip * f)
    if hd:
        east &= Y < y_eave - q(3.2)                # the eave's own thickness keeps its light
    for m, d in ((west, 1), (east, -1)):
        t = a[m] % 8
        ok = t < 6
        if hd and d > 0:
            continue                          # density 3: slate_roof lights the west hip slate by slate
        if hd:
            ok &= t >= 2                          # nothing in the shaded slope goes to black
        v = a[m]
        v[ok] = (v[ok] // 8) * 8 + np.clip(t[ok] + d, 0, 5)
        a[m] = v
    for side in (-1, 1):
        xa = x0 if side < 0 else x1
        xb = x0 + hip if side < 0 else x1 - hip
        bar(a, xa, y_eave - 1, xb, y_ridge + 2, max(1.2, D * 0.7), cap, 3 if side < 0 else 2, where=a >= 0)


def fascia(a, x0, x1, y, rng, fam='timber', hd=False):
    """The eave board along the roof's foot, and the shade it throws on the wall below."""
    beam(a, x0, y, x1, y + max(3, q(1.8)), rng, fam, 2, hd=hd)


# ------------------------------------------------------------------------------------------------
# openings and fittings
# ------------------------------------------------------------------------------------------------
def door(a, cx, yb, w, h, paint, rng, frame='stone', arch=False, open_=False, hd=False):
    """A plank door in its surround: a stone or timber frame with a lintel, ledged boards in the
    house's paint (dark seams), iron strap hinges and a latch, a worn step."""
    W2, Hd = q(w), q(h)
    x0, x1 = int(cx - W2 / 2), int(cx + W2 / 2)
    y0 = yb - Hd
    fr = max(3, q(2.2))
    # surround
    if frame == 'stone':
        k = 0
        y = yb
        while y > y0 - fr:
            hh = q(rng.uniform(4, 6.5))
            for (sx0, sx1) in ((x0 - fr - (q(1.2) if k % 2 else 0), x0), (x1, x1 + fr + (q(1.2) if k % 2 == 0 else 0))):
                blk(a, sx0, max(y0 - fr, y - hh), sx1 - 1, y - 1, STONES[k % 3], 3 if sx0 < cx else 2, cut=1, hd=hd)
            y -= hh
            k += 1
        blk(a, x0 - fr - q(1), y0 - fr - q(1), x1 + fr + q(1), y0, 'stone_warm', 4, cut=1, hd=hd)
    else:
        beam(a, x0 - fr, y0, x0, yb, rng, 'timber', 2, hd=hd)
        beam(a, x1, y0, x1 + fr, yb, rng, 'timber', 2, hd=hd)
        beam(a, x0 - fr - q(1.5), y0 - fr, x1 + fr + q(1.5), y0, rng, 'timber', 3, hd=hd)
    lm = _rect(a.shape, x0, y0, x1, yb)
    if arch:
        r = (x1 - x0) / 2
        Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
        lm &= ~((Y < y0 + r) & (((X - cx) / r) ** 2 + ((Y - y0 - r) / r) ** 2 > 1))
    if open_:
        fill(a, x0, y0, x1, yb, code('soot', 1), lm)
        fill(a, x0, yb - q(3), x1, yb, code('soot', 2), lm)
        return
    planks(a, x0, y0, x1, yb, rng, fams=(paint, paint, paint if hd else (paint + '_cool' if paint + '_cool' in FI else paint)), base=3,
           width=w / 4.0, grain=True, where=lm, hd=hd)
    # ledges and a brace
    for yy in (y0 + q(5), yb - q(8)):
        blk(a, x0 + 1, yy, x1 - 1, yy + q(2), paint, 4, cut=0, where=lm, hd=hd)
    # hinges and latch
    for yy in (y0 + q(5.5), yb - q(7.5)):
        fill(a, x0, yy, x0 + q(w * 0.45), yy + max(2, q(0.9)), code('iron', 2), lm)
        fill(a, x0, yy, x0 + q(w * 0.45), yy + 1, code('iron', 3), lm)
    lx, ly = x1 - q(3.2), y0 + Hd // 2
    blk(a, lx, ly, lx + max(3, q(1.6)), ly + max(3, q(1.6)), 'brass', 4, cut=0, hd=hd)
    if hd:
        # the door is set back in the wall's thickness: the reveal's shadow over its head and down
        # its west side, a lit sliver of the east reveal, the threshold worn at the middle
        Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        _step(a, lm & (Y >= yb - q(3.5)) & (Y < yb - q(1.6)), +1)       # light thrown up off the step
        _step(a, lm & (Y < y0 + q(1.6)), -2)
        _step(a, lm & (X < x0 + 2) & (Y >= y0 + q(1.6)), -1)
        fill(a, x1 - 1, y0 + q(1.6), x1, yb, code('stone_warm', 4) if frame == 'stone' else code('timber', 3))
    # the step
    blk(a, x0 - fr, yb - max(3, q(1.6)), x1 + fr, yb + 1, 'stone_warm', 3, cut=1, hd=hd)


def window(a, cx, yt, w, h, paint, rng, lit=False, shutters=True, box=False, frame_fam=None, cols=2, rows=2,
           sill='stone', lintel='timber', hd=False):
    """A window set in its wall: a lintel, a painted frame lit on its top and west side, panes
    that reflect the sky above and show the dark room below (a curtain, a lamp when lit), a sill
    with the shade it throws, shutters and a flower box when the house has them."""
    Wx, Hx = q(w), q(h)
    x0, x1 = int(cx - Wx / 2), int(cx + Wx / 2)
    y0, y1 = int(yt), int(yt + Hx)
    ff = frame_fam or paint
    fr = max(2, q(1.0))
    # lintel
    if lintel == 'timber':
        beam(a, x0 - q(2), y0 - q(2.4), x1 + q(2), y0, rng, 'timber', 2, hd=hd)
    else:
        blk(a, x0 - q(2), y0 - q(2.6), x1 + q(2), y0, 'stone_warm', 4, cut=1, hd=hd)
    # frame and panes
    blk(a, x0, y0, x1, y1, ff, 4, cut=0, hd=hd)
    gw = (x1 - x0 - fr * (cols + 1)) / cols
    gh = (y1 - y0 - fr * (rows + 1)) / rows
    for i in range(cols):
        for j in range(rows):
            gx0 = int(round(x0 + fr + i * (gw + fr)))
            gy0 = int(round(y0 + fr + j * (gh + fr)))
            gx1, gy1 = int(round(gx0 + gw)), int(round(gy0 + gh))
            pm = _rect(a.shape, gx0, gy0, gx1, gy1)
            if lit:
                fill(a, gx0, gy0, gx1, gy1, code('lamp', 3), pm)
                fill(a, gx0, gy0, gx1, gy0 + max(2, (gy1 - gy0) // 3), code('lamp', 4), pm)
                fill(a, gx0, gy1 - 2, gx1, gy1, code('lamp', 2), pm)
            elif hd:
                # density 3: the glass shows the room behind it, dark and deeper at the foot,
                # and the sky over the street reflected in a soft diagonal sheen from the upper
                # west corner (four steps of it), the bar's shadow along the pane's top and west
                Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
                u = ((X - gx0) / max(1, gx1 - gx0) + (Y - gy0) / max(1, gy1 - gy0)) / 2
                fill(a, gx0, gy0, gx1, gy1, code('slate_cool', 1), pm)
                fill(a, gx0, gy1 - max(2, (gy1 - gy0) // 3), gx1, gy1, code('void', 1), pm)
                a[pm & (u < 0.62) & (u >= 0.42)] = code('slate_cool', 2)
                a[pm & (u < 0.42) & (u >= 0.26)] = code('sky', 2)
                a[pm & (u < 0.26) & (u >= 0.12)] = code('sky', 3)
                a[pm & (u < 0.12)] = code('sky', 4)
                gl = pm & (np.abs(u - 0.5) < 0.03) & (X > gx0 + (gx1 - gx0) * 0.35)
                a[gl] = code('sky', 3)                                        # a glint on the far sheen
                a[pm & (Y < gy0 + 1)] = code('void', 1)
                a[pm & (X < gx0 + 1) & (Y >= gy0 + 1)] = code('slate_cool', 0)
            else:
                fill(a, gx0, gy0, gx1, gy1, code('slate_cool', 1), pm)
                fill(a, gx0, gy1 - max(2, (gy1 - gy0) // 3), gx1, gy1, code('void', 1), pm)
                # the sky in the glass: a diagonal band from the top west corner
                Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
                band = pm & ((X - gx0) + (Y - gy0) < (gx1 - gx0) * 0.8) & ((X - gx0) + (Y - gy0) > (gx1 - gx0) * 0.25)
                a[band] = code('sky', 3)
                a[pm & ((X - gx0) + (Y - gy0) <= (gx1 - gx0) * 0.25)] = code('sky', 4)
            if j == 0 and i == 0 and not lit:
                # a curtain drawn in the west pane
                fill(a, gx0, gy0, gx0 + max(2, (gx1 - gx0) // 3), gy1, code('berry', 3), pm)
                fill(a, gx0 + max(2, (gx1 - gx0) // 3) - 1, gy0, gx0 + max(2, (gx1 - gx0) // 3), gy1, code('berry', 2), pm)
    # the reveal: the wall's depth shades the top and west of the opening; light on the bars
    fill(a, x0 + fr, y0 + fr, x1 - fr, y0 + fr + max(2, q(0.8)), code('void', 1))
    fill(a, x0 + fr, y0 + fr, x0 + fr + max(2, q(0.7)), y1 - fr, code('void', 1))
    fill(a, x0, y0, x1, y0 + 1, code(ff, 5))
    fill(a, x0, y0, x0 + 1, y1, code(ff, 5))
    fill(a, x1 - 1, y0, x1, y1, code(ff, 2))
    # sill and its shade
    if sill:
        prism(a, x0 - q(1.6), y1, x1 + q(1.6), y1 + max(4, q(2.4)), max(2, q(1.0)), 'stone_warm', 3, side=q(1.2))
        sy = y1 + max(3, q(2.0))
        m = _rect(a.shape, x0 - q(1), sy, x1 + q(1), sy + max(2, q(1.0)))
        a[m & (a >= 0)] = np.clip(a[m & (a >= 0)] - 1, (a[m & (a >= 0)] // 8) * 8, None)
    if shutters:
        sw = q(w * 0.42)
        for side_, (sx0, sx1) in enumerate(((x0 - fr - sw, x0 - fr), (x1 + fr, x1 + fr + sw))):
            xx = sx0
            while xx < sx1:
                bw = min(q(w * 0.21), sx1 - xx)
                if bw > 2:
                    board(a, xx, y1, y1 - y0, bw - 1, -90, paint, 3 if side_ == 0 else 2, rng, split=False)
                xx += bw
            for ly in (y0 + q(1.5), y1 - q(3)):
                board(a, sx0, ly, sx1 - sx0, q(1.5), 0, paint, 4 if side_ == 0 else 3, rng, split=False, grain=False)
            board(a, sx0 + 1, y1 - q(2), int(math.hypot(sx1 - sx0 - 2, y1 - y0 - q(4))), q(1.2),
                  -math.degrees(math.atan2(y1 - y0 - q(4), sx1 - sx0 - 2)), paint, 4, rng, split=False, grain=False)
            hx = sx1 - 1 if side_ == 0 else sx0
            for ly in (y0 + q(2), y1 - q(2.6)):
                fill(a, min(hx, hx + (q(2) if side_ else -q(2))), ly, max(hx, hx + (q(2) if side_ else -q(2))) + 1, ly + 2, code('iron', 1))
    if hd and shutters:
        sw_ = q(w * 0.42)
        for (sx0, sx1) in ((x0 - fr - sw_, x0 - fr), (x1 + fr, x1 + fr + sw_)):
            Ys, Xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
            sm_ = (Xs >= sx0) & (Xs < sx1) & (Ys >= y0) & (Ys < y1)
            _step(a, sm_ & (Ys < y0 + q(2.5)), +1)
            _step(a, sm_ & (Ys >= y1 - q(2.5)), -1)
            _step(a, sm_ & (Xs >= sx1 - q(1.0)) & (sx0 > x0), -1)
    if box and hd:
        # a planter box of two boards, nailed to end posts, standing on brackets, its own shadow
        # on the wall below it
        by0 = y1 + max(3, q(2.0))
        bh = q(3.5)
        for k_ in range(2):
            board(a, x0 - q(1), by0 + k_ * bh // 2, x1 - x0 + q(2), bh // 2, 0, 'timber', 3 - k_, rng, split=k_ == 1)
        for ex_ in (x0 - q(1), x1 + q(1) - q(1.2)):
            beam(a, ex_, by0 - 1, ex_ + q(1.2), by0 + bh, rng, 'timber_cool', 2, hd=hd)
        Ys, Xs = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        _step(a, (Xs >= x0) & (Xs < x1 + q(1.6)) & (Ys >= by0 + bh) & (Ys < by0 + bh + q(1.2)), -1)
        for k in range(int((x1 - x0) / q(2.6)) + 1):
            fx = x0 + k * q(2.6) + int(rng.integers(-1, 2))
            blob(a, ellipse_mask(a.shape, fx + q(1.2), by0 - q(0.4), q(1.6), q(1.4)), 'leaf', 3 + (k % 2))
            if k % 2 == 0:
                fill(a, fx + 1, by0 - q(1.6), fx + 3, by0 - q(1.6) + 2, code(('berry', 'brass', 'dusk')[k % 3], 4))
    elif box:
        by0 = y1 + max(3, q(2.0))
        blk(a, x0 - q(1), by0, x1 + q(1), by0 + q(3.5), 'timber', 3, cut=1, hd=hd)
        for k in range(int((x1 - x0) / q(2.6)) + 1):
            fx = x0 + k * q(2.6) + int(rng.integers(-1, 2))
            blob(a, ellipse_mask(a.shape, fx + q(1.2), by0 - q(0.4), q(1.6), q(1.4)), 'leaf', 3 + (k % 2))
            if k % 2 == 0:
                fill(a, fx + 1, by0 - q(1.6), fx + 3, by0 - q(1.6) + 2, code(('berry', 'brass', 'dusk')[k % 3], 4))


def chimney(a, x0, x1, y_top, y_bot, rng, pot=True, hd=False):
    """A stone stack: courses, a lit cap slab, soot round the flue, a clay pot."""
    rubble(a, x0, y_top, x1, y_bot, rng, base=3, course=(2.2, 3.0), length=(3, 6), moss=0.0, hd=hd)
    blk(a, x0 - q(1), y_top - q(2.2), x1 + q(1), y_top, 'stone_warm', 4, cut=1, hd=hd)
    fill(a, x0, y_top, x1, y_top + q(2.5), code('soot', 2), a >= 0)
    if pot:
        cx = (x0 + x1) // 2
        blk(a, cx - q(2), y_top - q(5.5), cx + q(2), y_top - q(2.2), 'clay', 3, cut=1, hd=hd)
        fill(a, cx - q(1.2), y_top - q(5.5), cx + q(1.2), y_top - q(4.6), code('soot', 0))


def sign(a, x, y, kind, rng, fam='timber', hd=False):
    """A hanging sign on an iron bracket: a board with the trade's mark (bread, leaf, book)."""
    bar(a, x, y, x + q(9), y, max(1, q(0.6)), 'iron', 2)
    bar(a, x + q(1), y + q(4), x + q(5), y, max(1, q(0.5)), 'iron', 2)
    bx0, by0 = x + q(2), y + q(2)
    for k in (0, 1):
        fill(a, bx0 + q(1) + k * q(5), y, bx0 + q(1) + k * q(5) + 1, by0, code('iron', 1))
    blk(a, bx0, by0, bx0 + q(8), by0 + q(7), fam, 3, cut=1, hd=hd)
    cx, cy = bx0 + q(4), by0 + q(3.5)
    if kind == 'bread':
        blob(a, ellipse_mask(a.shape, cx, cy, q(2.6), q(1.6)), 'brass', 4)
        for k in (-1, 0, 1):
            fill(a, cx + k * q(1.2), cy - q(0.6), cx + k * q(1.2) + 1, cy + q(0.6), code('brass', 2))
    elif kind == 'leaf':
        blob(a, ellipse_mask(a.shape, cx, cy, q(1.6), q(2.4)), 'leaf', 4)
        fill(a, cx, cy - q(2), cx + 1, cy + q(2.4), code('leaf', 2))
    elif kind == 'book':
        blk(a, cx - q(2.4), cy - q(1.8), cx, cy + q(1.8), 'berry', 3, cut=0, hd=hd)
        blk(a, cx, cy - q(1.8), cx + q(2.4), cy + q(1.8), 'berry', 4, cut=0, hd=hd)
        fill(a, cx, cy - q(1.8), cx + 1, cy + q(1.8), code('plaster', 5))
    elif kind == 'hammer':
        bar(a, cx - q(2), cy + q(2), cx + q(1.5), cy - q(1.5), max(1, q(0.5)), 'timber_warm', 4)
        blk(a, cx, cy - q(2.6), cx + q(2.6), cy - q(0.8), 'iron', 4, cut=0, hd=hd)


# ------------------------------------------------------------------------------------------------
# buildings
# ------------------------------------------------------------------------------------------------
@dataclass
class Built:
    base: Pic
    damage: Pic | None
    info: dict = field(default_factory=dict)


def building(spec: dict, seed: int = 0, hd=False) -> Built:
    """A building from its look (plan data): w x depth world px footprint, a front wall wall_h
    tall, a roof roof_h tall over it. Keys: kind (cottage, terrace, library, forge, hut), wall
    (stone, frame, ashlar, boards), roof (slate, thatch, shingle), hip, paint (a house family), door
    (x from the west end, world px; 'open' for the forge mouth), windows ([x, ...]), lit, chimney
    ([x, ...]), sign ([x, kind]), units (a terrace: [[x0, x1, paint], ...]), damage (a list of
    what the storm did: holes, tarp, boards, scaffold, slates, crack).

    hd (density 3 and up): the buildings are drawn by `houses.building` to Eastward's level of
    detail (the roof as a plane with thickness, the walls with material and form, recessed
    openings, the trades' own things); the density 2 drawing below stays as the pilot golden has it."""
    if hd:
        from . import houses
        return houses.building(spec, seed)
    rng = np.random.default_rng(seed)
    w, dep = spec['w'], spec['depth']
    wall_h = spec.get('wall_h', 40)
    roof_h = spec.get('roof_h', round(dep * 0.55 + 10))
    ov = spec.get('overhang', 3)
    chim = max([spec.get('chimney_h', 14)] if spec.get('chimney') else [0])
    pad = 3
    W = q(w + 2 * ov) + 2 * pad
    H = q(wall_h + roof_h + chim + 4) + 2 * pad
    L = pad + q(ov)                  # the wall's west end
    R = L + q(w)                     # its east end
    B = H - pad - 1                  # the ground line (the foot)
    p = Pic(W, H, (L + R) // 2, B)
    a = p.a
    y_e = B - q(wall_h)              # the eave line
    y_r = y_e - q(roof_h)            # the ridge line
    info = dict(L=L, R=R, B=B, y_e=y_e, y_r=y_r, W=W, H=H)

    # the front wall -------------------------------------------------------------------------
    wall = spec.get('wall', 'stone')
    plinth = q(spec.get('plinth', 5))
    if wall == 'stone':
        rubble(a, L, y_e, R, B, rng, hd=hd)
    elif wall == 'ashlar':
        ashlar(a, L, y_e, R, B, rng, hd=hd)
        rubble(a, L, B - plinth, R, B, rng, base=2, course=(2.4, 2.8), length=(5, 9), moss=0.25, hd=hd)
    elif wall == 'boards':
        planks(a, L, y_e, R, B - plinth, rng, base=3, width=3.2, vertical=False, hd=hd)
        rubble(a, L, B - plinth, R, B, rng, base=3, course=(2.2, 2.8), length=(4, 7), hd=hd)
    else:   # frame: a stone ground course, timber framing, plaster panels
        sill_y = B - q(spec.get('frame_rail', 17))
        rubble(a, L, sill_y, R, B, rng, hd=hd)
        plaster(a, L, y_e, R, sill_y, rng, hd=hd)
        posts = sorted(set([L, R - q(3)] + [L + q(x) for x in spec.get('posts', [])]))
        beam(a, L, sill_y - q(2.4), R, sill_y, rng, 'timber', 2, hd=hd)
        for x in posts:
            beam(a, x, y_e, x + q(3), sill_y, rng, 'timber', 2 if x > (L + R) / 2 else 3, hd=hd)
        for (xa, xb) in zip(posts, posts[1:]):
            if xb - xa > q(12) and rng.random() < 0.6:
                bar(a, xa + q(3), sill_y - q(2.4), xb, y_e + q(2), max(1, q(1.1)), 'timber', 2,
                    where=_rect(a.shape, xa + q(3), y_e, xb, sill_y))
    if spec.get('quoins', wall in ('stone', 'frame')):
        y = B
        k = 0
        while y > y_e:
            hh = q(rng.uniform(4.5, 6.0))
            ww = q(6.5 if k % 2 == 0 else 4.5)
            blk(a, L, max(y_e, y - hh), L + ww, y - 1, 'stone_warm', 4, cut=1, hd=hd)
            blk(a, R - ww, max(y_e, y - hh), R, y - 1, 'stone_warm', 2, cut=1, hd=hd)
            y -= hh
            k += 1
    # the shade under the eave
    if hd:
        wall_form(a, spec, L, R, B, y_e, wall, rng, hd=hd)
    else:
        m = _rect(a.shape, L, y_e, R, y_e + q(3))
        sel = m & (a >= 0)
        a[sel] = np.maximum((a[sel] // 8) * 8, a[sel] - 1)

    # openings ----------------------------------------------------------------------------------
    paint = spec.get('paint', 'sky')
    units = spec.get('units') or [[0, w, paint]]
    for (ux0, ux1, upaint) in units:
        for wx in spec.get('windows', []):
            if ux0 <= wx < ux1:
                window(a, L + q(wx), B - q(spec.get('win_top', 31)), spec.get('win_w', 13), spec.get('win_h', 13), upaint, rng,
                       lit=spec.get('lit', False), shutters=spec.get('shutters', True), box=spec.get('box', False),
                       lintel='stone' if wall == 'ashlar' else 'timber', hd=hd)
    doors = spec.get('doors', [[spec['door'], paint]] if 'door' in spec else [])
    for (dx, dpaint) in doors:
        if spec.get('kind') == 'forge':
            continue
        door(a, L + q(dx), B, spec.get('door_w', 16), spec.get('door_h', 26 if HD else 31), dpaint, rng,
             frame='stone' if wall in ('stone', 'ashlar') else 'timber', arch=spec.get('arch', False), hd=hd)
    if spec.get('kind') == 'forge':
        mouth(a, L + q(spec['door']), B, spec.get('mouth_w', 30), spec.get('mouth_h', 27), rng, hd=hd)
        info['mouth'] = (L + q(spec['door']), B, q(spec.get('mouth_w', 30)), q(spec.get('mouth_h', 27)))
    if spec.get('sign'):
        sx, kind = spec['sign']
        sign(a, L + q(sx), y_e + q(5), kind, rng, hd=hd)

    # the roof ----------------------------------------------------------------------------------
    hip = q(spec.get('hip', 0))
    rx0, rx1 = L - q(ov), R + q(ov)
    rm = roof_mask(a.shape, rx0, rx1, y_r, y_e + q(1.5), round_=q(2) if hip else 0)
    roof = spec.get('roof', 'slate')
    a[rm] = -1
    if roof == 'thatch':
        rx0, rx1 = rx0 - q(1.5), rx1 + q(1.5)
        rm = roof_mask(a.shape, rx0, rx1, y_r, y_e + q(4), round_=q(6))
        thatch_roof(a, rm, rx0, rx1, y_r, y_e + q(4), rng)
        if hip:
            hip_planes(a, rx0, rx1, y_r + q(4), y_e + q(4), hip, cap='sand', hd=hd)
    elif roof == 'shingle':
        shingle_roof(a, rm, rx0, rx1, y_r, y_e + q(1.5), rng, hd=hd)
        fascia(a, rx0, rx1, y_e, rng, hd=hd)
        if hip:
            hip_planes(a, rx0, rx1, y_r + q(2), y_e + q(1.5), hip, hd=hd)
    else:
        slate_roof(a, rm, rx0, rx1, y_r, y_e + q(1.5), rng, hip=hip if hd else 0, hd=hd)
        if hip:
            hip_planes(a, rx0, rx1, y_r + q(2), y_e + q(1.5), hip, hd=hd)
        fascia(a, rx0, rx1, y_e, rng, hd=hd)
    if not hip and roof != 'thatch':
        # barge boards down the gable ends
        for xx, t in ((rx0, 3), (rx1 - q(2), 2)):
            beam(a, xx, y_r, xx + q(2), y_e + q(3), rng, 'timber', t, hd=hd)
    info['roof'] = rm
    info['rx'] = (rx0, rx1)
    if hd:
        roof_form(a, rm, rx0, rx1, y_r, y_e, roof)
        if roof != 'thatch':
            gutter(a, spec, rx0, rx1, L, R, B, y_e, rng)
    for cx in spec.get('chimney', []) or []:
        cw = q(spec.get('chimney_w', 9))
        x0 = L + q(cx) - cw // 2
        chimney(a, x0, x0 + cw, y_r - q(chim), y_r + q(roof_h * 0.45), rng, hd=hd)
        if hd:
            chimney_form(a, rm, x0, x0 + cw, y_r - q(chim), y_r + q(roof_h * 0.45))
    finish(p)

    # the damage --------------------------------------------------------------------------------
    dmg = None
    if spec.get('damage'):
        dmg = Pic(W, H, p.ax, p.ay)
        damage(dmg.a, a, spec, info, rng, hd=hd)
        finish(dmg)
        if not dmg.alpha().any():
            dmg = None
    return Built(p, dmg, info)


def _step(a, m, d):
    """Move the tones under mask m by d steps, each within its own family's ramp (0..5)."""
    sel = m & (a >= 0) & (a % 8 <= 5)
    a[sel] = (a[sel] // 8) * 8 + np.clip(a[sel] % 8 + d, 0, 5)


def wall_form(a, spec, L, R, B, y_e, wall, rng, hd=False):
    """Density 3: the front wall as a lit plane with depth round it. The eave's cast shadow across
    its top (deep near the eave, softer below, its lower edge stepping with the courses), the
    corner turning away from the light a step darker down the east end, damp and occlusion at the
    foot, and a foundation course standing proud of the wall with its top lit."""
    H_, W_ = a.shape
    Y, X = np.mgrid[0:H_, 0:W_]
    inwall = (X >= L) & (X < R) & (Y >= y_e) & (Y < B)
    _step(a, inwall & (Y < y_e + q(5.0)), -1)
    _step(a, inwall & (Y < y_e + q(2.2)), -1)
    _step(a, inwall & (X >= R - q(3.0)), -1)                       # the corner turning away
    _step(a, inwall & (X < L + q(1.0)), +1)                        # the west arris catching the light
    # the foundation course, a little wider than the wall, large stones, its top a lit ledge and the
    # wall's foot in the ledge's angle a tone down
    fh = q(spec.get('found_h', 3.6))
    fx0, fx1 = L - q(0.8), R + q(0.8)
    rubble(a, fx0, B - fh, fx1, B, rng, fams=('stone_cool', 'stone', 'stone_cool'), base=2, course=(3.4, 4.0),
           length=(6, 10), moss=0.35, east_dark=True, hd=hd)
    fill(a, fx0, B - fh, fx1, B - fh + 1, code('stone_warm', 5))
    fill(a, fx0, B - fh + 1, fx1, B - fh + 2, code('stone_warm', 4))
    fill(a, fx1 - q(0.8), B - fh, fx1, B, code('stone_cool', 1))
    _step(a, inwall & (Y >= B - fh - q(1.2)) & (Y < B - fh), -1)


def roof_form(a, rm, rx0, rx1, y_r, y_e, roof):
    """Density 3: the roof as a plane in the light, with thickness at its edges: the plane a step
    lighter towards the ridge on the west, its lowest courses a step down; the eave's front edge
    (the slates' or thatch's thickness) a lit lip over a dark underside."""
    H_, W_ = a.shape
    Y, X = np.mgrid[0:H_, 0:W_]
    span = max(1, rx1 - rx0)
    f = (Y - y_r) / max(1, y_e - y_r)                               # 0 at the ridge, 1 at the eave
    fx = (X - rx0) / span
    # the light falls off the plane piece by piece (slate by slate, or course by course of
    # straw), not in a hard-edged block: each piece's place in the plane plus a little scatter
    if roof == 'thatch':
        ch, cw = q(6.0), q(2.0)
    else:
        ch, cw = q(3.2), q(5.0)
    r = np.floor((Y - y_r) / max(1, ch)).astype(int)
    c = np.floor((X - rx0 + (r % 2) * cw / 2) / max(1, cw)).astype(int)
    hsh = ((r * 73856093) ^ (c * 19349663)) & 0xffff
    jit = (hsh % 1000) / 1000.0 - 0.5
    v = f * 0.9 + fx * 0.8 + 0.35 * jit
    if roof == 'thatch':                                          # (slates are lit piece by piece)
        _step(a, rm & (v < 0.55) & (a % 8 <= 3), +1)
    _step(a, rm & (f > 0.8) & (v > 1.25) & (a % 8 >= 2), -1)
    if roof == 'thatch':
        return
    ys = np.nonzero(rm.any(1))[0]
    yb = ys.max()
    lip = rm & (Y >= yb - 1)
    a[lip & (Y == yb - 1)] = code('slate', 4)
    a[lip & (Y == yb)] = code('slate_cool', 1)


def gutter(a, spec, rx0, rx1, L, R, B, y_e, rng):
    """Density 3: a half-round iron gutter hung under the eave on brackets (its lip lit, its belly
    in shade), the cast shadow it and the eave throw on the wall below, and a downpipe from it to
    the ground on the end of the front clear of the door and windows (a lit west side, a dark east
    side, its clips, a shoe turned out over a splash stone)."""
    H_, W_ = a.shape
    Y, X = np.mgrid[0:H_, 0:W_]
    gy0 = y_e + q(1.8)
    gh = max(4, q(1.7))
    gx0, gx1 = rx0 + q(1.2), rx1 - q(1.2)
    gm = (X >= gx0) & (X < gx1) & (Y >= gy0) & (Y < gy0 + gh)
    rel = Y - gy0
    tt = np.select([rel < 1, rel < 2, rel < gh - 1], [4, 3, 2], 1)
    a[gm] = FI['iron'] * 8 + tt[gm]
    for bx in np.arange(gx0 + q(3), gx1 - q(2), q(11)):
        fill(a, bx, gy0 - 1, bx + max(2, q(0.7)), gy0 + gh, code('iron', 1))
    _step(a, (X >= gx0 + q(1.0)) & (X < gx1) & (Y >= gy0 + gh) & (Y < gy0 + gh + q(1.0)), -1)
    # the downpipe: on the side with more clear wall
    busy = [spec.get('door')] if isinstance(spec.get('door'), (int, float)) else []
    busy += [d[0] for d in spec.get('doors', [])]
    busy += list(spec.get('windows', []))
    w = spec['w']
    cand = [(min([abs(2.5 - b) for b in busy] or [99]), L + q(1.2)), (min([abs(w - 2.5 - b) for b in busy] or [99]), R - q(3.2))]
    clear, px = max(cand)
    need = max(spec.get('door_w', 16), spec.get('win_w', 13)) / 2 + 3.5
    if clear < need:
        return
    pw = max(4, q(1.6))
    top, bot = gy0 + gh - 1, B - q(1.4)
    pm = (X >= px) & (X < px + pw) & (Y >= top) & (Y < bot)
    u = X - px
    tt = np.select([u < 1, u < pw - 2, u < pw - 1], [4, 3, 2], 1)
    a[pm] = FI['iron'] * 8 + tt[pm]
    for cy in np.arange(top + q(6), bot - q(3), q(9)):
        fill(a, px - 1, cy, px + pw + 1, cy + max(2, q(0.7)), code('iron', 1))
        fill(a, px - 1, cy, px + pw + 1, cy + 1, code('iron', 3))
    _step(a, (X >= px + pw) & (X < px + pw + q(0.8)) & (Y >= top) & (Y < bot), -1)   # its shadow on the wall
    out = -1 if px < (L + R) / 2 else 1
    sx0 = px - q(1.6) if out < 0 else px
    fill(a, sx0, bot - 1, sx0 + pw + q(1.6), bot + max(2, q(0.8)), code('iron', 2))
    fill(a, sx0, bot - 1, sx0 + pw + q(1.6), bot, code('iron', 4))
    prism(a, sx0 - q(0.6), B - q(1.2), sx0 + pw + q(2.2), B + 1, max(1, q(0.5)), 'stone_warm', 3, side=1)


def chimney_form(a, rm, x0, x1, y_top, y_bot):
    """Density 3: the stack as a block: its west face lit, its east face turned away, lead flashing
    where it meets the slates, its shadow cast down the roof to the east."""
    H_, W_ = a.shape
    Y, X = np.mgrid[0:H_, 0:W_]
    st = (X >= x0) & (X < x1) & (Y >= y_top) & (Y < y_bot)
    _step(a, st & (X >= x1 - q(2.2)), -1)
    _step(a, st & (X < x0 + q(1.0)), +1)
    fl = (X >= x0 - q(0.8)) & (X < x1 + q(0.8)) & (Y >= y_bot - q(1.2)) & (Y < y_bot) & rm
    a[fl] = code('slate_cool', 3)
    a[fl & (Y == y_bot - q(1.2))] = code('slate_cool', 4)
    _step(a, rm & (X >= x1 + q(0.8)) & (X < x1 + q(4.0)) & (Y >= y_top + q(4)) & (Y < y_bot + q(3)) & ~st, -1)


def mouth(a, cx, yb, w, h, rng, hd=False):
    """The forge's mouth: a wide opening under an oak lintel, the hearth inside (brick, a hood,
    the bellows' nozzle), its floor of cinders."""
    W2, Hh = q(w), q(h)
    x0, x1 = int(cx - W2 / 2), int(cx + W2 / 2)
    y0 = yb - Hh
    fill(a, x0, y0, x1, yb, code('soot', 1))
    fill(a, x0, y0, x1, y0 + q(4), code('soot', 0))
    # the hearth at the back: a brick block with a hood above
    hx0, hx1 = x0 + q(w * 0.28), x1 - q(w * 0.18)
    if hd:
        # density 3: the hearth's bricks in their courses, each lit on its top arris, sooted
        # towards the fire bed, in dark mortar
        rubble(a, hx0, yb - q(11), hx1, yb - q(1), rng, fams=('clay', 'clay_warm' if 'clay_warm' in FI else 'clay', 'clay_cool'),
               base=3, course=(2.2, 2.4), length=(4.0, 5.5), moss=0, east_dark=True, mortar=('soot', 1), hd=hd)
        Yh, Xh = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        _step(a, (Xh >= hx0) & (Xh < hx1) & (Yh >= yb - q(4)) & (Yh < yb - q(1)) & (a // 8 != FI['soot']), -1)
    else:
        rubble(a, hx0, yb - q(11), hx1, yb - q(1), rng, fams=('clay', 'clay', 'clay_cool'), base=2, course=(2.0, 2.2),
               length=(3, 4.5), moss=0, east_dark=False, hd=hd)
    hood = _rect(a.shape, hx0 - q(1), y0 + q(4), hx1 + q(1), yb - q(14))
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    hood &= np.abs(X - (hx0 + hx1) / 2) < (hx1 - hx0) / 2 * (0.45 + 0.55 * (Y - y0) / max(1, Hh * 0.5))
    a[hood] = code('iron', 1)
    a[hood & (X < (hx0 + hx1) / 2 - q(2))] = code('iron', 2)
    # the bellows on the west side
    if hd:
        # the bellows as a volume: two boards with the leather between them gathered in pleats, lit
        # on the upper left, the nozzle iron
        bcx, bcy, brx, bry = x0 + q(5), yb - q(8), q(3.5), q(2.4)
        Yb, Xb = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
        bm = ellipse_mask(a.shape, bcx, bcy, brx, bry)
        dd = ((Xb - bcx) / brx + (Yb - bcy) / bry) * 0.7
        a[bm] = FI['timber_cool'] * 8 + np.select([dd < -0.5, dd < 0.1, dd < 0.6], [4, 3, 2], 1)[bm]
        pleat = bm & (np.abs(((Xb - bcx) / q(0.9)) % 2 - 1) < 0.25) & (np.abs(Yb - bcy) < bry * 0.55)
        a[pleat] = code('timber_cool', 1)
        a[bm & (Yb < bcy - bry * 0.55)] = code('timber', 3)
        a[bm & (Yb < bcy - bry * 0.8)] = code('timber', 4)
    else:
        blob(a, ellipse_mask(a.shape, x0 + q(5), yb - q(8), q(3.5), q(2.4)), 'timber_cool', 2)
    fill(a, x0 + q(8), yb - q(8.5), hx0, yb - q(7.5), code('iron', 2))
    fill(a, x0, yb - q(1.6), x1, yb, code('soot', 2))
    # posts and the lintel
    beam(a, x0 - q(3), y0, x0, yb, rng, 'timber', 3, hd=hd)
    beam(a, x1, y0, x1 + q(3), yb, rng, 'timber', 2, hd=hd)
    beam(a, x0 - q(4.5), y0 - q(3.5), x1 + q(4.5), y0, rng, 'timber', 3, hd=hd)


def damage(d, base, spec, info, rng, hd=False):
    """What the storm did, drawn over the building in its own picture: holes torn in the roof
    (rafters and battens over the dark loft, broken slates round the edge), slates gone here and
    there, a tarp weighted with stones, boards nailed over doors and windows, scaffolding, a crack."""
    L, R, B, y_e, y_r = info['L'], info['R'], info['B'], info['y_e'], info['y_r']
    rm = info['roof']
    rx0, rx1 = info['rx']
    order = {'slates': 0, 'crack': 1, 'hole': 2, 'tarp': 3, 'boards': 4, 'scaffold': 5}
    toks = sorted(spec['damage'], key=lambda t: order.get(t[0] if isinstance(t, list) else t, 9))
    for tok in toks:
        kind = tok[0] if isinstance(tok, list) else tok
        args = tok[1:] if isinstance(tok, list) else []
        if kind == 'hole':
            cx = L + q(args[0]) if args else int(rng.uniform(L + q(8), R - q(8)))
            rw = q(args[1]) if len(args) > 1 else q(14)
            rh = q(args[2]) if len(args) > 2 else int((y_e - y_r) * 0.5)
            cy = y_r + (y_e - y_r) * 0.45
            m = ellipse_mask(d.shape, cx, cy, rw / 2, rh / 2)
            # a ragged edge on the soft grid: bites of whole slates
            for _ in range(6):
                bx = cx + rng.uniform(-rw / 2, rw / 2)
                by = cy + rng.uniform(-rh / 2, rh / 2)
                m |= _rect(d.shape, bx - q(2.5), by - q(1.6), bx + q(2.5), by + q(1.6))
            m &= rm
            m &= ~_rect(d.shape, 0, y_r, d.shape[1], y_r + q(3))       # the ridge holds
            d[m] = code('void', 0)
            ys, xs = np.nonzero(m)
            if not len(ys):
                continue
            if hd:
                # density 3: the loft is dark at the back and catches a little of the daylight
                # falling in under the upper rim; rafters at a carpenter's uneven spacing, some
                # battens snapped, some gone, each a squared timber with its lit top
                Yh, Xh = np.mgrid[0:d.shape[0], 0:d.shape[1]]
                d[m & (Yh > ys.min() + (ys.max() - ys.min()) * 0.55)] = code('void', 1)
                lo_ = m & (Yh > ys.min() + (ys.max() - ys.min()) * 0.78)
                d[lo_ & (rng.random(d.shape) < 0.35)] = code('void', 2)          # dust in the light on the loft floor
                xx = xs.min() + q(rng.uniform(1.0, 2.5))
                while xx < xs.max():
                    rwid = max(3, q(rng.uniform(1.2, 1.6)))
                    beam(d, xx, ys.min(), xx + rwid, ys.max() + 1, rng, 'timber', 2, where=m, hd=hd)
                    _step(d, m & (Xh >= xx + rwid) & (Xh < xx + rwid + q(0.6)), -1)
                    xx += q(rng.uniform(5.0, 7.5))
                yy = ys.min() + q(rng.uniform(1.5, 2.5))
                while yy < ys.max() - 1:
                    bh_ = max(3, q(rng.uniform(0.8, 1.1)))
                    if rng.random() < 0.75:
                        bx0 = xs.min() + (q(rng.uniform(0, 4)) if rng.random() < 0.5 else 0)
                        bx1 = xs.max() + 1 - (q(rng.uniform(2, 6)) if rng.random() < 0.5 else 0)
                        bm_ = m & (Yh >= yy) & (Yh < yy + bh_) & (Xh >= bx0) & (Xh < bx1)
                        d[bm_] = code('timber_cool', 2)
                        d[bm_ & (Yh == yy)] = code('timber_cool', 4)
                        d[bm_ & (Yh == yy + bh_ - 1)] = code('timber_cool', 1)
                        d[bm_ & ((Xh == bx1 - 1) | (Xh == bx0))] = code('timber_warm', 4)   # a snapped end, raw
                    yy += q(rng.uniform(3.6, 5.4))
            else:
                # battens across, rafters down
                for yy in range(ys.min() + q(2), ys.max(), q(4.5)):
                    fill(d, xs.min(), yy, xs.max() + 1, yy + max(2, q(0.8)), code('timber_cool', 2), m)
                for xx in range(xs.min() + q(2), xs.max(), q(6)):
                    fill(d, xx, ys.min(), xx + max(3, q(1.4)), ys.max() + 1, code('timber', 2), m)
                    fill(d, xx, ys.min(), xx + 1, ys.max() + 1, code('timber', 3), m)
            # broken slates hanging round the rim
            rim = ndi.binary_dilation(m, iterations=q(1.5)) & ~m & rm
            ry, rx = np.nonzero(rim)
            for k in rng.choice(len(ry), size=min(len(ry), 9), replace=False):
                blk(d, rx[k] - q(2), ry[k] - q(1.2), rx[k] + q(2), ry[k] + q(1.4), 'slate', int(rng.choice([2, 4])), cut=1, hd=hd)
        elif kind == 'slates':
            n = args[0] if args else 6
            for _ in range(n):
                cx = rng.uniform(rx0 + q(4), rx1 - q(6))
                cy = rng.uniform(y_r + q(5), y_e - q(3))
                if hd:
                    # one to three slates gone from a row, staggered: the batten across the gap
                    # (lit top, shaded under), the dark loft behind, the next slate's butt above
                    # throwing its shadow in, a broken corner left hanging
                    wn = q(rng.choice([4.5, 5.5, 9.5, 11.0]))
                    hn = q(rng.uniform(2.6, 3.4))
                    m = _rect(d.shape, cx, cy, cx + wn, cy + hn) & rm
                    if rng.random() < 0.5:
                        m |= _rect(d.shape, cx + q(2.5), cy - q(3.0), cx + q(2.5) + q(5), cy) & rm
                    d[m] = code('void', 1)
                    Ys, Xs = np.mgrid[0:d.shape[0], 0:d.shape[1]]
                    d[m & (Ys < cy + q(1.0))] = code('void', 0)
                    by_ = int(cy + hn * rng.uniform(0.4, 0.6))
                    bt = m & (Ys >= by_) & (Ys < by_ + max(3, q(1.0)))
                    d[bt] = code('timber_cool', 2)
                    d[bt & (Ys == by_)] = code('timber_cool', 4)
                    d[bt & (Ys == by_ + max(3, q(1.0)) - 1)] = code('timber_cool', 1)
                    if rng.random() < 0.6:
                        kx = int(cx + wn * rng.uniform(0.2, 0.7))
                        blk(d, kx, int(cy + hn - q(1.6)), kx + q(2.4), int(cy + hn), 'slate', 3, cut=1, hd=hd)
                else:
                    m = _rect(d.shape, cx, cy, cx + q(5), cy + q(3)) & rm
                    d[m] = code('void', 1)
                    fill(d, int(cx), int(cy), int(cx) + q(5), int(cy) + 2, code('timber_cool', 1), m)
        elif kind == 'tarp':
            x0 = L + q(args[0]) if args else L + q(4)
            x1 = L + q(args[1]) if len(args) > 1 else x0 + q(22)
            fam = args[2] if len(args) > 2 else 'sand'
            yt = y_r + q(2)
            yb = y_e + q(1)
            Y, X = np.mgrid[0:d.shape[0], 0:d.shape[1]] + 0.5
            sag = q(1.5) * np.sin((X - x0) / max(1, x1 - x0) * math.pi * 2)
            m = (X >= x0) & (X < x1) & (Y >= yt + sag * 0.3) & (Y < yb + np.abs(sag) * 0.4) & (rm | (Y >= y_e))
            tt = np.full(d.shape, 3, int)
            if hd:
                # density 3: the cloth drapes from where the ropes hold it: soft creases fanning
                # down from each rope, a lit ridge on the west side of each crease and its shade
                # on the east, the folds at uneven spacing
                cr = np.zeros(d.shape)
                for k_ in range(int((x1 - x0) / q(4)) + 2):
                    fx_ = x0 + q(rng.uniform(2.5, 5.0)) * k_ + q(rng.uniform(-1, 1))
                    lean = rng.uniform(-0.25, 0.25)
                    cr += np.exp(-((X - fx_ - (Y - yt) * lean) / q(1.4)) ** 2)
                g = np.gradient(cr, axis=1)
                tt = np.where(g > 0.12, 4, np.where(g < -0.12, 2, 3))
                tt[(cr > 1.2)] = 4
                tt[(Y - yt) < q(1.2)] = 4
                tt[X > x0 + (x1 - x0) * 0.75] -= 1
            else:
                fold = ((X - x0) * 0.6 + (Y - yt)) % q(9)
                tt[fold < q(2)] = 4
                tt[(fold >= q(4.5)) & (fold < q(6))] = 2
                tt[X > x0 + (x1 - x0) * 0.7] -= 1
            T_, L_, B_, R_ = edges(m)
            tt[B_] = 1
            tt[T_] = 4
            if hd:
                # the cloth's own wear: a stitched seam across it, a hem along its foot, two
                # weather stains, grommets at the top where the ropes are tied
                sy_ = yt + (yb - yt) * rng.uniform(0.4, 0.6)
                seam = m & (np.abs(Y - sy_ - 0.8 * np.sin(X / q(3))) < 0.6)
                tt[seam] = tt[seam] - 1
                stitch = m & (np.abs(Y - sy_ - 0.8 * np.sin(X / q(3)) - 1.5) < 0.5) & ((X // 2) % 2 == 0)
                tt[stitch] = tt[stitch] + 1
                hem = m & (Y >= yb + np.abs(sag) * 0.4 - q(1.6)) & ~B_
                tt[hem] = np.maximum(tt[hem], 3)
                for _ in range(2):
                    sx_, sy2 = rng.uniform(x0 + q(3), x1 - q(3)), rng.uniform(yt + q(3), yb - q(3))
                    st_ = m & (((X - sx_) / q(2.4)) ** 2 + ((Y - sy2) / q(1.6)) ** 2 < 1) & (rng.random(d.shape) < 0.7)
                    tt[st_] = tt[st_] - 1
                for gx_ in (x0 + q(3), x1 - q(3)):
                    gm = m & (np.abs(X - gx_ - q(1)) < q(0.7)) & (np.abs(Y - yt - q(2)) < q(0.7))
                    tt[gm] = 5
            tt = np.clip(tt, 0, 5)
            d[m] = FI[fam] * 8 + tt[m]
            # ropes to the eave and stones holding the foot
            for xx in (x0 + q(3), x1 - q(3)):
                # (at density 3 the ropes run down over the cloth to the weights at the eave, none
                # left dangling under it)
                bar(d, xx, yt + q(2), xx + q(2), (yb - q(1)) if hd else yb + q(4), max(0.8, D * 0.35), 'timber_warm', 3)
            for xx in range(int(x0) + q(2), int(x1) - q(3), q(7)):
                blk(d, xx, yb - q(2.5), xx + q(4), yb + q(0.5), 'stone', 3, cut=1, hd=hd)
        elif kind == 'boards':
            # sawn planks nailed across a door or a window, into its frame: [x, y_top, w, h] in world px
            x, yt_, ww, hh = args
            x0, x1 = L + q(x - ww / 2) - q(2.4), L + q(x + ww / 2) + q(2.4)
            y0, y1 = B - q(yt_), B - q(yt_) + q(hh)
            yy = y0 + q(0.6)
            k = 0
            while yy < y1 - q(2):
                th = q(rng.uniform(2.4, 3.6))
                ang = rng.uniform(-3.5, 3.5)
                over = q(rng.uniform(0, 1.6))
                L_ = (x1 - x0) + over
                xs_ = x0 - int(rng.integers(0, q(1.2) + 1))
                fam = ('timber_warm', 'timber', 'timber_cool')[k % 3]
                board(d, xs_, yy, L_, th, ang, fam, int(rng.choice([3, 3, 4, 2])), rng)
                dy = math.tan(math.radians(ang))
                for nx in (xs_ + q(1.2), xs_ + L_ - q(2.4)):
                    ny = yy + (nx - xs_) * dy + th / 2 - q(0.5)
                    nail(d, int(nx), int(ny), rng=rng)
                yy += th + int(rng.integers(1, q(1.4) + 1))
                k += 1
            # the brace, nailed at both ends and where it crosses
            dx_, dy_ = (x1 - q(2)) - (x0 + q(2)), (y0 + q(2)) - (y1 - q(3))
            Lb = math.hypot(dx_, dy_)
            board(d, x0 + q(2), y1 - q(3), Lb, q(2.6), math.degrees(math.atan2(dy_, dx_)), 'timber_warm', 4, rng)
            for f in (0.08, 0.5, 0.9):
                nail(d, int(x0 + q(2) + dx_ * f + q(0.6)), int(y1 - q(3) + dy_ * f + q(0.4)), rng=rng)
        elif kind == 'scaffold':
            x0 = L + q(args[0]) if args else L + q(4)
            x1 = L + q(args[1]) if len(args) > 1 else x0 + q(20)
            top = y_e - q(args[2]) if len(args) > 2 else y_e - q(8)
            r = max(1.5, q(1.1))
            for xx in (x0, x1):
                bar(d, xx, top, xx, B - 1, r, 'timber_warm', 3)
            mid = (top + B) // 2 + q(4)
            for yy in (top + q(4), mid):
                bar(d, x0 - q(2), yy, x1 + q(2), yy, r * 0.9, 'timber', 2)
                for xx in (x0, x1):
                    fill(d, xx - 2, yy - 2, xx + 3, yy + 2, code('sand', 2))
                    fill(d, xx - 2, yy - 2, xx + 3, yy - 1, code('sand', 3))
            blk(d, x0 - q(3), mid - q(3), x1 + q(3), mid - q(0.5), 'timber_warm', 4, cut=0, hd=hd)
            bar(d, x0, mid, x1, top + q(4), r * 0.8, 'timber_cool', 3)
            # a ladder leaning on the deck
            lx = x1 + q(3)
            bar(d, lx, B - 1, lx - q(4), mid - q(5), r * 0.7, 'timber', 3)
            bar(d, lx + q(4), B - 1, lx, mid - q(5), r * 0.7, 'timber', 2)
            for yy in range(mid, B - q(2), q(4)):
                f = (yy - (mid - q(5))) / max(1, (B - 1 - (mid - q(5))))
                xa = lx - q(4) + f * q(4)
                fill(d, int(xa), yy, int(xa) + q(4), yy + max(2, q(0.7)), code('timber', 3))
        elif kind == 'crack':
            x = L + q(args[0]) if args else (L + R) // 2
            y = y_e + q(4)
            m = np.zeros(d.shape, bool)
            while y < B - q(8):
                nx = x + int(rng.integers(-q(2), q(2) + 1))
                ny = y + q(rng.uniform(2, 4))
                m |= seg_mask(d.shape, x, y, nx, ny, max(0.7, D * 0.35))
                x, y = nx, ny
            m &= base >= 0
            d[m] = code('stone', 0)


# ------------------------------------------------------------------------------------------------
# props
# ------------------------------------------------------------------------------------------------
def _pic(w, h, up=0, side=0):
    """A canvas for a prop w x h world px (its footprint) standing `up` world px tall."""
    pad = 3
    W = q(w + 2 * side) + 2 * pad
    H = q(h + up) + 2 * pad
    return Pic(W, H, W // 2, H - pad - 1)


def stones_heap(a, cx, yb, w, h, rng, n=None, fams=STONES, slates=True, planks_=True, hd=False):
    """A heap of fallen stones, broken slates and a split board, back to front: each stone a volume
    (lit top, mid front, dark east flank), each slate a thin plate with its lit face and dark edge,
    bigger stones at the foot."""
    n = n or int(w * h / 22) + 4
    items = sorted((rng.random() ** 0.7, rng.uniform(-0.5, 0.5)) for _ in range(n))
    for fy, fx in items:
        sw = q(rng.uniform(3, 6.5) * (0.7 + 0.5 * fy))
        sh = q(rng.uniform(2.4, 4.2) * (0.7 + 0.5 * fy))
        hump = (1 - (2 * fx) ** 2) * q(h * 0.55)
        x = int(cx + fx * q(w) - sw / 2)
        y = int(yb - q(h) * (1 - fy) * 0.5 - hump * (1 - fy) - sh)
        r = rng.random()
        if slates and r < 0.25:
            ty = y + sh // 2
            blk(a, x, ty, x + sw, ty + max(3, q(1.2)), 'slate', int(rng.choice([3, 4])), cut=1, bot=0, hd=hd)
            fill(a, x + 1, ty + max(3, q(1.2)), x + sw, ty + max(3, q(1.2)) + 1, code('slate', 1))
        elif planks_ and r < 0.32:
            board(a, x - q(3), y + sh, q(rng.uniform(8, 12)), q(1.8), rng.uniform(-25, -5), 'timber_warm', 3, rng)
        else:
            stone_chunk(a, x, y, sw, sh, fams[int(rng.integers(0, len(fams)))], int(rng.choice([3, 3, 4])), rng)


def p_rubble(w, h, seed, hd=False):
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=h * 0.9, side=2)
    stones_heap(p.a, p.ax, p.ay, w, h, rng, hd=hd)
    return finish(p)


def p_well(w, h, seed, choked=False, hd=False):
    """The square's well, a volume in the three-quarter view. The coping: an elliptical ring of
    dressed stones whose top surface is lit from the upper left (stones lighter and wider there,
    darker toward the lower right), with a shaded front face under it; the curb below, a cylinder of
    courses lit down its west side, dark down its east, shaded under the coping's lip. The shaft
    opening shows its sunlit back wall going dark with depth, the front inner wall in shadow, and the
    water deep down: small and dark with a waterline ring and a narrow glint. Two square posts stand
    on the coping (lit west faces, shaded east), carrying a round axle with the rope wound on it, an
    iron crank, the rope down to a hooped bucket over the opening, and a slate hood whose underside
    is in shade. Choked: rubble heaped in the shaft, the hood fallen across the coping."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=6 if choked else 40, side=8)
    a, cx, yb = p.a, p.ax, p.ay
    Hh, Ww = a.shape
    Y, X = np.mgrid[0:Hh, 0:Ww] + 0.5
    rx = q(w / 2)
    ry = int(rx * 0.5)
    th = q(2.4)                                   # the coping's front face
    cy = yb - ry - q(8)                           # the coping's centre
    irx, iry = rx - q(3.8), ry - q(2.8)
    E = lambda ccx, ccy, ax_, ay_: ((X - ccx) / ax_) ** 2 + ((Y - ccy) / ay_) ** 2 <= 1
    outer, inner = E(cx, cy, rx, ry), E(cx, cy, irx, iry)
    u = np.clip((X - cx) / rx, -1, 1)
    # the curb: a cylinder of courses down to the ground
    ground_arc = (yb - 1 - ry) + ry * np.sqrt(np.clip(1 - u ** 2, 0, 1))
    curb = (np.abs(X - cx) < rx) & (Y >= cy) & (Y < ground_arc)
    tmp = np.full(a.shape, -1, np.int32)
    rubble(tmp, cx - rx, cy, cx + rx, yb, rng, base=3, course=(2.6, 3.2), length=(3.2, 5.0), moss=0.3, east_dark=False, hd=hd)
    a[curb & (tmp >= 0)] = tmp[curb & (tmp >= 0)]
    for lo, hi, d in ((-1.1, -0.55, 1), (0.35, 0.7, -1), (0.7, 1.1, -2)):
        sel = curb & (u >= lo) & (u < hi) & (a >= 0) & (a % 8 < 6)
        a[sel] = np.clip(a[sel] % 8 + d, 0, 5) + (a[sel] // 8) * 8
    # the coping's front face, then its top ring
    face = E(cx, cy + th, rx, ry) & ~outer & (Y > cy)
    tt = np.where(u < -0.5, 4, np.where(u > 0.45, 2, 3))
    a[face] = FI['stone_warm'] * 8 + tt[face]
    lip = curb & ~face & ~outer & E(cx, cy + th + q(1.2), rx, ry)
    sel = lip & (a >= 0) & (a % 8 < 6)
    a[sel] = np.clip(a[sel] % 8 - 1, 0, 5) + (a[sel] // 8) * 8          # shade under the lip
    ring = outer & ~inner
    ang = np.arctan2((Y - cy) / ry, (X - cx) / rx)
    light = np.cos(ang - math.radians(-135))                             # 1 at the upper left
    tt = np.clip(np.round(3.6 + 1.2 * light), 2, 5).astype(int)
    a[ring] = FI['stone_warm'] * 8 + tt[ring]
    nst = 11
    pos = (ang + math.pi) / (2 * math.pi) * nst
    jw = 0.05 + 0.04 * (1 - light)                                       # joints tighter to the lit side
    joint = ring & (np.abs(pos - np.round(pos)) < jw)
    a[joint] = np.where(light[joint] > 0, code('stone_warm', 2), code('stone', 1))
    a[ring & ~E(cx, cy, rx - 1, ry - 1) & (Y < cy)] = code('stone_warm', 5)  # the lit outer arris
    if D >= 2.5:
        # density 3: the coping's dressed top is tooled: pits and short chisel strokes a tone down in
        # its lit stones, chips on the arris
        lit_ = ring & (a % 8 >= 4) & (a // 8 == FI['stone_warm'])
        tool = lit_ & (((X.astype(int) * 3 + Y.astype(int) * 5) % 7 == 0) | (np.random.default_rng(seed + 991).random(a.shape) < 0.08))
        tool = (tool | np.roll(tool, 1, axis=1)) & lit_            # strokes two texels long (they survive the tidy)
        a[tool] = a[tool] - 1
    # the shaft: lit back wall, darkening; the front inner wall in shadow; the water deep down
    a[inner] = code('void', 0)
    top_i = cy - iry
    back = inner & (Y < top_i + iry * 0.75)
    depth = np.clip((Y - top_i) / max(1, iry * 0.75), 0, 1)
    tt = np.clip(np.round(4.2 - 4.0 * depth), 0, 5).astype(int)
    a[back] = FI['stone'] * 8 + tt[back]
    courses = back & (((Y - top_i) % q(2.2)) < 1)
    a[courses] = FI['stone'] * 8 + np.clip(tt[courses] - 1, 0, 5)
    a[inner & (Y >= top_i + iry * 0.75)] = code('void', 0)
    frontin = inner & ~E(cx, cy - q(1.2), irx, iry)
    a[frontin] = code('void', 1)
    wcx, wcy, wrx, wry = cx + q(0.4), cy + iry * 0.2, irx * 0.42, max(3, iry * 0.26)
    if choked:
        stones_heap(a, cx, cy + iry, w * 0.75, h * 0.6, rng, n=16, hd=hd)
        # the hood came down with the storm: its posts snapped across the coping, its slates in the shaft
        board(a, cx - rx - q(4), cy + q(1), q(w + 6), q(2.6), -16, 'timber', 3, rng)
        board(a, cx - q(2), cy + q(3), q(w * 0.7), q(2.4), 12, 'timber', 2, rng)
        board(a, cx + q(1), cy - q(2), q(w * 0.5), q(1.8), -40, 'timber_cool', 3, rng)
        for _ in range(7):
            sx_, sy_ = cx + q(rng.uniform(-w * 0.35, w * 0.35)), cy + q(rng.uniform(-2, 3))
            fam_, t_ = ('slate', 'slate_cool')[int(rng.integers(0, 2))], int(rng.choice([2, 3, 4]))
            blk(a, int(sx_), int(sy_), int(sx_) + q(3.6), int(sy_) + q(1.6), fam_, t_, cut=1, hd=hd)
            if hd:
                # a slate tipped into the shaft: its broken underside in shade, a lit chip on the upper edge
                x0_, x1_, y1_ = int(sx_) + 1, int(sx_) + q(3.6) - 1, int(sy_) + q(1.6)
                a[_rect(a.shape, x0_, y1_ - 1, x1_, y1_)] = code(fam_, max(0, t_ - 2))
                cx_ = int(rng.integers(x0_, max(x0_ + 1, x1_ - 2)))
                a[_rect(a.shape, cx_, int(sy_) + 1, cx_ + 2, int(sy_) + 2)] = code(fam_, min(5, t_ + 1))
        return finish(p)
    water = E(wcx, wcy, wrx, wry)
    a[water] = code('water_cool', 0)
    wl = water & ~E(wcx, wcy + 1, wrx, wry) 
    a[wl] = code('water', 3)
    a[water & (np.abs(Y - (wcy - wry * 0.2)) < 1) & (X > wcx - wrx * 0.6) & (X < wcx - wrx * 0.1)] = code('sky', 4)
    # posts on the coping
    top_y = cy - q(27)
    for sx in (-1, 1):
        px0 = int(cx + sx * (rx - q(2.2)) - q(1.4))
        pw = q(2.8)
        a[_rect(a.shape, px0, top_y, px0 + pw, cy + 2)] = code('timber', 3)
        a[_rect(a.shape, px0, top_y, px0 + pw // 3, cy + 2)] = code('timber', 4)
        a[_rect(a.shape, px0 + pw - pw // 3, top_y, px0 + pw, cy + 2)] = code('timber', 2)
        for _ in range(2):
            gy = int(rng.integers(top_y + q(2), cy - q(3)))
            fill(a, px0 + pw // 2, gy, px0 + pw // 2 + 1, gy + q(2), code('timber', 2))
        prism(a, px0 - q(0.6), cy - q(0.6), px0 + pw + q(0.6), cy + q(1.2), 2, 'iron', 2, side=2)
    # the axle with the rope wound on it, the crank
    ay_ = top_y + q(8)
    ax0, ax1 = cx - rx + q(1), cx + rx - q(1)
    a[_rect(a.shape, ax0, ay_ - q(1.2), ax1, ay_ + q(1.2))] = code('timber_cool', 3)
    a[_rect(a.shape, ax0, ay_ - q(1.2), ax1, ay_ - q(0.4))] = code('timber_cool', 4)
    a[_rect(a.shape, ax0, ay_ + q(0.6), ax1, ay_ + q(1.2))] = code('timber_cool', 1)
    for k in range(6):
        rxk = cx - q(4.5) + k * q(1.5)
        a[_rect(a.shape, rxk, ay_ - q(1.7), rxk + q(1.0), ay_ + q(1.7))] = code('sand', 4 if k % 2 else 3)
    kx = cx + rx + q(0.4)
    bar(a, kx - q(1), ay_, kx + q(3), ay_, max(1.3, q(0.6)), 'iron', 3)
    bar(a, kx + q(3), ay_, kx + q(3), ay_ + q(5), max(1.3, q(0.6)), 'iron', 2)
    bar(a, kx + q(3), ay_ + q(5), kx + q(6), ay_ + q(5), max(1.5, q(0.8)), 'timber_warm', 3)
    # the rope down to the bucket, the bucket over the opening
    bcx, bby = cx, cy - q(3)
    btop = bby - q(5)
    a[_rect(a.shape, bcx, ay_ + q(1.7), bcx + 2, btop - q(2.6))] = code('sand', 3)
    a[_rect(a.shape, bcx + 1, ay_ + q(1.7), bcx + 2, btop - q(2.6))] = code('sand', 2)
    bar(a, bcx - q(2.6), btop + 1, bcx + 1, btop - q(2.6), max(1.0, q(0.4)), 'iron', 3)
    bar(a, bcx + 1, btop - q(2.6), bcx + q(2.8), btop + 1, max(1.0, q(0.4)), 'iron', 2)
    bk = (Y >= btop) & (Y < bby) & (np.abs(X - bcx - 1) < q(2.8) - (Y - btop) / max(1, bby - btop) * q(0.6))
    ub = (X - bcx - 1) / q(2.8)
    tt = np.where(ub < -0.35, 4, np.where(ub > 0.4, 2, 3))
    a[bk] = FI['timber_warm'] * 8 + tt[bk]
    for yy in (btop + q(1), bby - q(1.6)):
        a[bk & (Y >= yy) & (Y < yy + q(0.8))] = code('iron', 2)
        a[bk & (Y >= yy) & (Y < yy + q(0.8)) & (ub < -0.3)] = code('iron', 4)
    rimm = E(bcx + 1, btop, q(2.8), q(1.0))
    a[rimm] = code('timber_warm', 4)
    a[E(bcx + 1, btop + 1, q(2.0), q(0.6))] = code('void', 1)
    # the hood: a slate roof, its underside in shade between the posts
    hx0, hx1 = cx - rx - q(4), cx + rx + q(4)
    rh_ = 6.0 if hd else 10.0                 # (scale gate, 26 Oct: a lower hood, so the well stands 1.9 A at most)
    hm = roof_mask(a.shape, hx0, hx1, top_y - q(rh_), top_y + q(1.5))
    slate_roof(a, hm, hx0, hx1, top_y - q(rh_), top_y + q(1.5), rng, row=2.6, width=(3.4, 5.0), moss=0.15, hd=hd)
    if not hd:
        fascia(a, hx0, hx1, top_y, rng, hd=hd)           # (density 3: the slates' own butts make the hood's eave)
    for xx, t in ((hx0, 3), (hx1 - q(1.6), 2)):
        beam(a, xx, top_y - q(rh_), xx + q(1.6), top_y + q(2.4), rng, 'timber', t, hd=hd)
    under = _rect(a.shape, cx - rx + q(1), top_y + q(2.4), cx + rx - q(1), top_y + q(3.6)) & (a >= 0)
    a[under] = code('timber_cool', 1)
    return finish(p)


def p_lantern(w, h, seed, lit=False):
    """The shard lantern, a street lamp 48 world px tall. Dressed stone plinth courses (lit tops,
    chamfers, dark east sides); a flared iron foot and a round post shaded as cylinders (a reflected
    rim, a highlight band, a core shadow) with collars; scroll brackets; a glass cage whose panes
    reflect the sky in diagonal streaks between lit frame bars, with an iron cradle inside (empty, or
    holding the woodland's shard alight); a pyramid cap with a lit west facet and a dark east one."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=50, side=8)
    a, cx, yb = p.a, p.ax, p.ay
    prism(a, cx - q(7.5), yb - q(5), cx + q(7.5), yb + 1, q(2.6), 'stone_warm', 3, side=q(2.6))
    prism(a, cx - q(5.2), yb - q(9), cx + q(5.2), yb - q(5), q(2.0), 'stone_warm', 3, side=q(2.0))
    fill(a, cx - q(7.5), yb - q(5), cx - q(6.2), yb - q(3.8), code('stone', 2))
    for k in range(3):
        mx = cx - q(6.5) + k * q(4.8)
        fill(a, mx, yb - q(1.2), mx + q(1.4), yb, code('leaf', 3))
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    ft, fb = yb - q(15), yb - q(9)
    hw = q(1.8) + (Y - ft) / max(1, fb - ft) * q(2.0)
    foot = (Y >= ft) & (Y < fb) & (np.abs(X - cx) < hw)
    a[foot] = FI['iron'] * 8 + np.clip(cyl_tones((X - cx) / np.maximum(1, hw), 3), 0, 5)[foot]
    ao = _rect(a.shape, cx - q(4), fb, cx + q(4.5), fb + 2) & (a >= 0)
    a[ao] = np.maximum((a[ao] // 8) * 8, a[ao] - 2)
    hp = q(1.5) - (ft - Y) / max(1, q(26)) * q(0.4)
    post = (Y >= yb - q(38)) & (Y < ft) & (np.abs(X - cx) < hp)
    a[post] = FI['iron'] * 8 + np.clip(cyl_tones((X - cx) / np.maximum(1, hp), 3), 0, 5)[post]
    for yy in (ft - q(1.4), yb - q(25), yb - q(37)):
        col = (Y >= yy) & (Y < yy + q(1.5)) & (np.abs(X - cx) < q(2.4))
        a[col] = FI['iron'] * 8 + np.clip(cyl_tones((X - cx) / q(2.4), 3), 0, 5)[col]
        a[col & (Y < yy + 1)] = code('iron', 5)
    for sx in (-1, 1):
        bar(a, cx + sx * q(1.2), yb - q(36), cx + sx * q(4.6), yb - q(39.5), max(1.0, q(0.5)), 'iron', 3 if sx < 0 else 2)
        blob(a, ellipse_mask(a.shape, cx + sx * q(4.6), yb - q(36.8), q(1.1), q(1.1)), 'iron', 2)
    gx0, gx1 = cx - q(4.5), cx + q(4.5)
    gy0, gy1 = yb - q(48), yb - q(40)
    prism(a, gx0 - q(1.2), gy1, gx1 + q(1.2), gy1 + q(1.8), q(0.7), 'iron', 3, side=q(1))
    halfw = q(4.5) - (gy1 - Y) / max(1, gy1 - gy0) * q(0.8)
    cage = (Y >= gy0) & (Y < gy1) & (np.abs(X - cx) < halfw)
    if lit:
        a[cage] = code('sky', 4)
        a[cage & (Y < gy0 + q(2))] = code('sky', 5)
        blob(a, ellipse_mask(a.shape, cx, (gy0 + gy1) / 2 + q(0.5), q(1.8), q(2.8)), 'snow', 5, top=0, left=0, bot=0, right=0)
    else:
        a[cage] = code('slate_cool', 1)
        a[cage & (X > cx + q(1.5))] = code('void', 1)
        # the empty cradle inside
        a[_rect(a.shape, cx - q(1.2), gy1 - q(3), cx + q(1.2), gy1 - q(2.4))] = code('iron', 2)
        bar(a, cx - q(1.2), gy1 - q(3), cx - q(1.8), gy1 - q(5), max(1.0, q(0.35)), 'iron', 2)
        bar(a, cx + q(1.2), gy1 - q(3), cx + q(1.8), gy1 - q(5), max(1.0, q(0.35)), 'iron', 1)
    # reflections: diagonal streaks of sky on each pane
    streak = cage & (np.abs(((X - gx0) + (Y - gy0) * 0.8) % q(5.5) - q(1.2)) < 1.0) & (X < cx + q(2))
    a[streak] = code('sky', 3 if not lit else 5)
    for xx in (cx - q(4.2), cx - 1, cx + q(3.4)):
        bars = cage & (X >= xx) & (X < xx + max(2, q(0.7)))
        a[bars] = code('iron', 2)
        a[bars & (X < xx + 1)] = code('iron', 4)
    # the cap: four facets, the west one lit
    capy0, capy1 = gy0 - q(5.5), gy0
    cap = (Y >= capy0) & (Y < capy1) & (np.abs(X - cx) < q(6) * (Y - capy0) / q(5.5))
    a[cap] = code('iron', 3)
    a[cap & (X < cx - q(0.4)) & (Y < capy1 - q(1.2))] = code('iron', 4)
    a[cap & (X < cx - q(2)) & (Y < capy1 - q(1.2)) & (Y > capy0 + q(2))] = code('iron', 5)
    a[cap & (X > cx + q(0.8))] = code('iron', 2)
    a[cap & (Y >= capy1 - q(1.2))] = code('iron', 2)
    a[cap & (Y >= capy1 - q(1.2)) & (X < cx)] = code('iron', 3)
    blob(a, ellipse_mask(a.shape, cx, capy0 - q(0.8), q(1.1), q(1.1)), 'iron', 4)
    return finish(p)


def p_stall(w, h, seed, hd=False):
    """Moss's stall: a counter of sawn boards on trestles, crates of what the valley still grows
    (each fruit lit, the crate's slats in front), a striped awning on two poles with its hem
    scalloped and its shade on the counter, a slate board of prices, a sack at the foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=36, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    for xx, t in ((x0, 3), (x1 - q(2.2), 2)):
        beam(a, xx, yb - q(38), xx + q(2.2), yb, rng, 'timber', t, hd=hd)
    # counter front: vertical boards with gaps and nails
    xx = x0 + q(2.2)
    while xx < x1 - q(2.2):
        bw = q(rng.uniform(3, 4.2))
        board(a, xx, yb - q(1), q(12), bw - 1, -90, ('timber', 'timber_warm', 'timber_cool')[int(rng.integers(0, 3))],
              int(rng.choice([2, 3, 3])), rng)
        nail(a, xx + bw // 2 - 1, yb - q(11), rng=rng)
        xx += bw
    prism(a, x0, yb - q(16.5), x1, yb - q(13), q(1.8), 'timber_warm', 3, side=q(1))
    # crates of produce
    xx = x0 + q(2)
    for k, (fam, t) in enumerate((('fox', 3), ('leaf', 3), ('berry', 3), ('brass', 4))):
        cw = q(w / 4.6)
        for yy in range(4):
            for j in range(4):
                fx = xx + q(1.2) + j * (cw - q(2.4)) // 3 + (q(0.8) if yy % 2 else 0)
                fy = yb - q(21.5) + yy * q(1.0) - q(1.2)
                m = ellipse_mask(a.shape, fx, fy, q(1.3), q(1.1))
                a[m] = code(fam, t)
                a[m & ellipse_mask(a.shape, fx - q(0.4), fy - q(0.4), q(0.6), q(0.5))] = code(fam, min(5, t + 2))
        board(a, xx, yb - q(19.5), cw, q(1.8), 0, 'timber', 3, rng, split=False, grain=False)
        board(a, xx, yb - q(17.6), cw, q(1.6), 0, 'timber_warm', 2, rng, split=False, grain=False)
        xx += cw + q(1.5)
    # the awning: stripes, a scalloped hem, its shade on the counter
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    ay0, ay1 = yb - q(42), yb - q(33)
    am = (X >= x0 - q(2)) & (X < x1 + q(2)) & (Y >= ay0) & (Y < ay1)
    hem = (Y >= ay1) & (Y < ay1 + q(2.4)) & (X >= x0 - q(2)) & (X < x1 + q(2)) & \
        ((((X - x0) % q(4)) - q(2)) ** 2 / q(2) ** 2 + ((Y - ay1) / q(2.4)) ** 2 <= 1)
    m = am | hem
    stripe = ((X - x0 + q(2)) // q(4)).astype(int) % 2
    tt = np.where(stripe == 0, 4, 3)
    tt = np.where(Y < ay0 + q(1.5), tt + 1, tt)
    tt = np.where((Y >= ay1 - q(1.5)) & (Y < ay1), tt - 1, tt)
    tt = np.where((((X - x0) % q(4)) < 1), tt - 1, tt)       # the folds between the stripes
    if D >= 2.5:
        # density 3: each panel a shallow fold of canvas, lit on its west half, a tone down at its
        # east edge, sagging a little at the middle of its run (the canvas hangs between the poles)
        us = ((X - x0 + q(2)) % q(4)) / q(4)
        tt = tt + np.where((us > 0.15) & (us < 0.45), 1, 0) - np.where(us > 0.8, 1, 0)
        tt = tt - np.where((Y > ay0 + (ay1 - ay0) * 0.55) & (np.abs(X - (x0 + x1) / 2) < (x1 - x0) * 0.3), 1, 0)
    tt = np.clip(tt, 0, 5)
    a[m & (stripe == 0)] = FI['plaster'] * 8 + tt[m & (stripe == 0)]
    a[m & (stripe == 1)] = FI['berry'] * 8 + tt[m & (stripe == 1)]
    under = _rect(a.shape, x0, ay1 + q(2.4), x1, ay1 + q(4)) & (a >= 0)
    a[under] = np.maximum((a[under] // 8) * 8, a[under] - 1)
    # the price board and a sack
    prism(a, x1 - q(8), yb - q(10), x1 - q(1), yb, q(1), 'slate', 1, side=q(1))
    for ly in (yb - q(8), yb - q(5.5), yb - q(3)):
        fill(a, x1 - q(6.5), ly, x1 - q(3) - int(rng.integers(0, q(1.5))), ly + 2, code('plaster', 5))
    sack(a, x0 + q(3), yb - q(3.6), q(3.4), q(3.4))
    return finish(p)


def p_anvil(w, h, seed):
    """The anvil on its block: a pointed horn, a flat face with a polished steel highlight, the heel
    with its hardy hole, a waisted body and splayed feet; the block an oak round with its rings on
    top, its bark split down the sides."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=16, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    # the block: bark sides, the top with rings
    bt, bb = yb - q(9), yb
    side_m = (np.abs(X - cx) < q(5.5)) & (Y >= bt) & (Y < bb)
    tt = np.full(a.shape, 2)
    tt[X < cx - q(2.5)] = 3
    tt[X > cx + q(3)] = 1
    tt[side_m & ((((X - cx) / max(1, q(1.6))).astype(int)) % 3 == 0)] -= 1   # bark fissures
    a[side_m] = FI['timber_cool'] * 8 + np.clip(tt[side_m], 0, 5)
    topm = ellipse_mask(a.shape, cx, bt, q(5.5), q(2))
    a[topm] = code('timber_warm', 4)
    for r in (0.7, 0.4):
        ringm = topm & ~ellipse_mask(a.shape, cx, bt, q(5.5) * r, q(2) * r) & ellipse_mask(a.shape, cx, bt, q(5.5) * r + 1, q(2) * r + 0.6)
        a[ringm] = code('timber_warm', 3)
    fill(a, cx - 1, bt - 1, cx + 1, bt + 1, code('timber', 2))
    # the anvil: feet, waist, body, face, horn, heel
    feet = (Y >= yb - q(12.5)) & (Y < yb - q(10.5)) & (np.abs(X - cx) < q(4.2))
    waist = (Y >= yb - q(15)) & (Y < yb - q(12.5)) & (np.abs(X - cx) < q(2.2) + (Y - (yb - q(15))) / q(2.5) * q(1.2))
    body = (Y >= yb - q(17.5)) & (Y < yb - q(15)) & (X > cx - q(5)) & (X < cx + q(5.5))
    horn = (Y >= yb - q(17.5)) & (Y < yb - q(15.4)) & (X <= cx - q(5)) & (X > cx - q(10)) & \
        (Y > yb - q(17.5) + (cx - q(5) - X) / q(5) * q(1.4))
    m = feet | waist | body | horn
    tt = np.full(a.shape, 2)
    tt[X < cx - q(1)] = 3
    tt[X > cx + q(3)] = 1
    a[m] = FI['iron'] * 8 + tt[m]
    face = body & (Y < yb - q(16.3))
    a[face] = code('iron', 4)
    a[face & (Y < yb - q(17.1))] = code('iron', 5)                       # the polished top plane
    a[face & (X > cx + q(4))] = code('iron', 3)
    hv = np.clip((Y - (yb - q(17.5))) / q(2.1), 0, 1)
    a[horn] = FI['iron'] * 8 + np.select([hv < 0.3, hv < 0.65], [4, 3], 1)[horn]   # the horn round, lit on top
    tip = ellipse_mask(a.shape, cx - q(10), yb - q(15.9), q(0.9), q(0.7))
    a[tip] = code('iron', 3)
    fill(a, cx + q(3.5), yb - q(17.5), cx + q(4.5), yb - q(16.8), code('iron', 0))   # the hardy hole
    return finish(p)


def p_fire(w, h, seed, hd=False):
    """The forge lit: a bed of coals in the hearth, flames licking up, sparks over them. A light
    source: no outline."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10)
    a, cx, yb = p.a, p.ax, p.ay
    fill(a, cx - q(w / 2), yb - q(3), cx + q(w / 2), yb, code('lava', 1))
    for k in range(int(w / 2.2)):
        x = cx - q(w / 2) + k * q(2.2) + int(rng.integers(0, 2))
        blk(a, x, yb - q(4.5), x + q(2.2), yb - q(2), 'lava', int(rng.choice([2, 3, 3])), cut=1, hd=hd)
    for k in range(5):
        fx = cx + q((k - 2) * w / 6) + int(rng.integers(-1, 2))
        fh = q(rng.uniform(5, 10)) * (1.25 if k == 2 else 1.0)
        lean = q(rng.uniform(-1.2, 1.6))
        base_y = yb - q(3)
        outer = np.zeros(a.shape, bool)
        inner = np.zeros(a.shape, bool)
        n = 8
        for i in range(n):
            tt = i / (n - 1)
            r = q(2.0) * (1 - tt) ** 0.9 + 0.6
            outer |= ellipse_mask(a.shape, fx + lean * tt * tt, base_y - fh * tt, r, r)
            if tt < 0.6:
                inner |= ellipse_mask(a.shape, fx + lean * tt * tt, base_y - fh * tt, r * 0.55, r * 0.55)
        a[outer] = code('lava', 3)
        a[inner] = code('lamp', 4)
        a[inner & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] > base_y - q(1.5))] = code('lamp', 5)
    for _ in range(3):
        x = cx + int(rng.integers(-q(w / 2), q(w / 2)))
        y = yb - q(rng.uniform(10, 14))
        fill(a, x, y, x + 2, y + 2, code('lamp', 5))
    tidy(a)
    return p


def p_smoke(w, h, seed, hd=False):
    """Smoke from the crater: three puffs rising and leaning east, lit on their west sides."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=48 if hd else 34, side=26 if hd else 4)   # (hd: room for the billows rising and leaning east, never cut flat)
    a, cx, yb = p.a, p.ax, p.ay
    if hd:
        from . import houses      # the building lead's redraw (houses.smoke_column)
        return houses.smoke_column(p, rng)
    for k in range(6):
        y = yb - q(4 + k * 6)
        x = cx + q(k * 1.6) + int(rng.integers(-2, 3))
        r = q(4 + k * 0.9)
        m = ellipse_mask(a.shape, x, y, r, r * 0.8)
        blob(a, m & (a < 0), 'ash', 4 if k > 2 else 3)
        a[m & ellipse_mask(a.shape, x - r * 0.35, y - r * 0.3, r * 0.5, r * 0.4)] = code('ash', 5)
    return finish(p)


def p_beds(w, h, seed, scorched=True):
    """Four raised beds behind the hut: board frames as volumes (lit tops, front faces, dark east
    ends, corner stakes), soil in ridged rows lit on their north slopes. Scorched: ash, cinders and
    black stalks. Dug over: dark tilled earth; two sown with the valley's seed."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=6, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, y0 = cx - q(w / 2), yb - q(h)
    bw, bh = (w - 6) / 2, (h - 6) / 2
    k = 0
    for j in range(2):
        for i in range(2):
            bx0 = x0 + q(i * (bw + 6))
            by0 = y0 + q(j * (bh + 6))
            bx1, by1 = bx0 + q(bw), by0 + q(bh)
            prism(a, bx0, by0, bx1, by1 + q(2.4), q(bh) - q(0.6), 'timber', 3, side=q(1.2))
            ix0, iy0, ix1, iy1 = bx0 + q(1.4), by0 + q(1.4), bx1 - q(2.4), by1 - q(0.6)
            soil, lit, dark = (('soot', 2), ('ash', 3), ('soot', 1)) if scorched else (('earth', 2), ('earth', 3), ('earth', 1))
            a[_rect(a.shape, ix0, iy0, ix1, iy1)] = code(*soil)
            a[_rect(a.shape, ix0, iy0, ix1, iy0 + q(1))] = code(*dark)
            for yy in range(iy0 + q(1.6), iy1 - 1, q(3.2)):
                a[_rect(a.shape, ix0, yy, ix1, yy + 2)] = code(*lit)
                a[_rect(a.shape, ix0, yy + 2, ix1, yy + 3)] = code(*dark)
            if scorched:
                for _ in range(6):
                    sx = int(rng.integers(ix0 + 2, ix1 - 3))
                    sy = int(rng.integers(iy0 + q(3), iy1 - 1))
                    fill(a, sx, sy - q(3), sx + 2, sy, code('soot', 0))
                    if rng.random() < 0.5:
                        fill(a, sx + 2, sy - q(3), sx + 4, sy - q(2.4), code('soot', 0))
                for _ in range(3):
                    sx = int(rng.integers(ix0 + 2, ix1 - 3))
                    sy = int(rng.integers(iy0 + 2, iy1 - 2))
                    fill(a, sx, sy, sx + 2, sy + 2, code('fox', 3))
                    fill(a, sx, sy, sx + 1, sy + 1, code('lamp', 4))
            elif k in (1, 2):
                for yy in range(iy0 + q(2.4), iy1 - 2, q(3.2)):
                    for xx in range(ix0 + q(2), ix1 - q(2), q(4)):
                        blob(a, ellipse_mask(a.shape, xx, yy, q(1.2), q(1.0)), 'leaf', 4)
            for sx_ in (bx0, bx1 - q(1.2)):
                prism(a, sx_, by0 - q(1.4), sx_ + q(1.2), by0 + q(1.6), q(0.5), 'timber', 2, side=0)
            k += 1
    return finish(p)


def p_notice_board(w, h, seed, hd=False):
    """The notice board: two square posts (lit west faces), a panel of boards with its thickness along
    the top edge, notices pinned on it (each with a pin, a curled lit corner and its shade), under a
    little slate hood with a fascia and a shaded underside."""
    rng = np.random.default_rng(seed)
    p = _pic(22, 6, up=36, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    for xx in (cx - q(10), cx + q(8)):
        prism(a, xx, yb - q(31), xx + q(2.4), yb, q(0.8), 'timber', 3, side=q(0.9))
        if D >= 2.5:     # grain and checks running down the posts, the east face's included
            for gx in (xx + q(0.9), xx + q(2.0)):
                for _ in range(4):
                    gy = int(rng.uniform(yb - q(30), yb - q(3)))
                    fill(a, int(gx), gy, int(gx) + 1, gy + q(rng.uniform(1.5, 3.5)), code('timber', 0 if gx > xx + q(1.6) else 2))
    bx0, bx1, by0, by1 = cx - q(9), cx + q(9), yb - q(28), yb - q(14)
    a[_rect(a.shape, bx0, by0, bx1, by1)] = code('timber', 1 if D < 2.5 else 0)
    yy = by0
    while yy < by1:
        th = min(q(rng.uniform(2.6, 3.4)), by1 - yy)
        if th > 2:
            board(a, bx0, yy, bx1 - bx0, th - 1, 0, ('timber', 'timber_warm')[int(rng.integers(0, 2))], 3, rng)
        yy += th
    prism(a, bx0 - q(0.6), by0 - q(1.6), bx1 + q(0.6), by0, q(0.6), 'timber_warm', 4, side=q(0.8))
    for (nx, ny, nw, nh, t) in ((1, 2, 6, 7, 5), (8.5, 1.5, 5, 5, 4), (10, 7.5, 6, 5, 4), (2.5, 9.5, 5, 3, 3)):
        x, y = bx0 + q(nx), by0 + q(ny)
        sh = _rect(a.shape, x + 2, y + 2, x + q(nw) + 2, y + q(nh) + 2) & (a >= 0)
        a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - 1)
        blk(a, x, y, x + q(nw), y + q(nh), 'plaster', t, cut=0, hd=hd)
        if D >= 2.5:
            # density 3: the paper bows off the board: lit at its upper left, a tone down to its lower
            # right, a crease across it and its fibres
            Yp, Xp = np.mgrid[0:a.shape[0], 0:a.shape[1]]
            pm = (Xp >= x + 1) & (Xp < x + q(nw) - 1) & (Yp >= y + 1) & (Yp < y + q(nh) - 1)
            g = ((Xp - x) / max(1, q(nw)) + (Yp - y) / max(1, q(nh)))
            a[pm & (g > 0.85)] = code('plaster', max(1, t - 1))
            a[pm & (g > 1.35)] = code('plaster', max(1, t - 2))
            a[pm & (g < 0.35)] = code('plaster', 5)
            cy0 = y + q(nh) * rng.uniform(0.35, 0.6)
            a[pm & (np.abs(Yp - cy0 - (Xp - x) * 0.08) < 0.6)] = code('plaster', max(1, t - 1))
            fib = pm & (rng.random(a.shape) < 0.06)
            a[fib] = code('plaster', max(1, t - 1))
        for ly in range(y + q(1.6), y + q(nh) - 2, q(1.6)):
            fill(a, x + q(1), ly, x + q(nw) - q(1.2) - int(rng.integers(0, q(1.5))), ly + 1, code('dusk', 2))
        cx_ = x + q(nw) - q(1.4)
        cy_ = y + q(nh) - q(1.4)
        for i in range(q(1.4)):
            fill(a, cx_ + i, cy_ + q(1.4) - 1 - i, cx_ + q(1.4), cy_ + q(1.4) - i, code('plaster', min(5, t + 1)))
        fill(a, x + q(nw / 2), y, x + q(nw / 2) + 2, y + 2, code('berry', 3))
        fill(a, x + q(nw / 2), y, x + q(nw / 2) + 1, y + 1, code('berry', 5))
    hm = roof_mask(a.shape, bx0 - q(3), bx1 + q(3), by0 - q(7.5), by0 - q(1), hip=q(2))
    slate_roof(a, hm, bx0 - q(3), bx1 + q(3), by0 - q(7.5), by0 - q(1), rng, row=2.4, width=(3, 4.4), moss=0.2, hd=hd)
    fascia(a, bx0 - q(3), bx1 + q(3), by0 - q(2.2), rng, hd=hd)
    if D >= 2.5:     # density 3: the fascia board's lit top arris, its grain, the shaded east end
        Yf, Xf = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        fb = (Yf >= by0 - q(2.2)) & (Yf < by0 - q(2.2) + q(1.6)) & (Xf >= bx0 - q(3)) & (Xf < bx1 + q(3)) & (a >= 0)
        fb &= (a // 8 == FI['timber']) | (a // 8 == FI['timber_warm']) | (a // 8 == FI['timber_cool'])
        a[fb & (Yf == by0 - q(2.2))] = code('timber_warm', 5)
        a[fb & ((Xf + 2 * Yf) % 7 == 0) & (Yf > by0 - q(2.2))] = code('timber', 1)
        a[fb & (Xf >= bx1 + q(1.6))] = code('timber_cool', 1)
        # the ridge tiles: each a half round, lit on its west, its east side in shade
        clay = (a // 8 == FI['clay']) & (a % 8 < 6)
        for yy in range(max(0, by0 - q(9)), by0 - q(3)):
            row = clay[yy]
            xs_ = np.nonzero(row)[0]
            if not len(xs_):
                continue
            runs = np.split(xs_, np.nonzero(np.diff(xs_) > 1)[0] + 1)
            for run in runs:
                if len(run) < 4:
                    continue
                n_ = len(run)
                for j, xx in enumerate(run):
                    u_ = j / (n_ - 1)
                    t_ = a[yy, xx] % 8
                    a[yy, xx] = FI['clay'] * 8 + int(np.clip(t_ + (1 if u_ < 0.3 else -1 if u_ > 0.72 else 0), 0, 5))
        # the papers' own lit corner only in the brightest tone
        for (nx, ny, nw, nh, t) in ((1, 2, 6, 7, 5), (8.5, 1.5, 5, 5, 4), (10, 7.5, 6, 5, 4), (2.5, 9.5, 5, 3, 3)):
            x, y = bx0 + q(nx), by0 + q(ny)
            pm = (Xf >= x + 1) & (Xf < x + q(nw) - 1) & (Yf >= y + 1) & (Yf < y + q(nh) - 1) & (a == code('plaster', 5))
            g = (Xf - x) / max(1, q(nw)) + (Yf - y) / max(1, q(nh))
            a[pm & (g > 0.45)] = code('plaster', 4)
    return finish(p)


def p_waystone(w, h, seed):
    """The waystone: a standing stone dressed with a chisel, its front face lit on the west and
    tooled in short diagonal strokes, its east side in shade, worn chips at the arrises, a weathered
    cap; moss and lichen at its foot and in the tooling; the crossroads rune cut deep (a ring and a
    cross, the cut's upper wall in shade, its lower wall lit) and glowing softly in the groove."""
    rng = np.random.default_rng(seed)
    p = _pic(16, 8, up=36, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    # the plinth
    prism(a, cx - q(9), yb - q(5), cx + q(9), yb + 1, q(2.2), 'stone_warm', 3, side=q(2.4))
    # the stone: a front face tapering up to a rounded cap, an east side face
    top, bot = yb - q(35), yb - q(4.5)
    half = lambda yy: q(6.2) - (bot - yy) / max(1, bot - top) * q(1.2)
    front = (Y >= top + q(3)) & (Y < bot) & (np.abs(X - cx) < half(Y))
    cap = ellipse_mask(a.shape, cx, top + q(3.2), q(5.2), q(3.2)) & (Y < top + q(3.2))
    sidef = (Y >= top + q(3)) & (Y < bot) & (X >= cx + half(Y)) & (X < cx + half(Y) + q(2.2))
    tt = np.full(a.shape, 3)
    tt[X < cx - q(2)] = 4
    tool = (((X + Y * 0.9) // max(2, q(1.4))).astype(int) % 3 == 0) & (((Y // q(2.2)).astype(int)) % 2 == 0)
    tt[front & tool] -= 1
    a[front] = FI['stone'] * 8 + np.clip(tt[front], 0, 5)
    a[cap] = code('stone', 4)
    a[cap & (X > cx + q(1.5))] = code('stone', 3)
    a[sidef] = code('stone_cool', 2)
    a[sidef & (Y > bot - q(6))] = code('stone_cool', 1)
    # worn chips on the arrises
    for _ in range(5):
        yy = rng.uniform(top + q(5), bot - q(3))
        sx = cx - half(yy) if rng.random() < 0.5 else cx + half(yy) - q(1)
        fill(a, int(sx), int(yy), int(sx) + q(1.2), int(yy) + q(1.4), code('stone', 2))
    # the rune: forked paths cut into the face (a stem, two branches reaching up, two roots, a hook),
    # glowing softly in the groove, its upper lip in shade and its lower lip lit
    rcy = top + q(15)
    pts = [curve(cx + q(0.3), rcy + q(8), cx - q(0.2), rcy - q(3), q(0.8)),
           curve(cx - q(0.2), rcy - q(0.5), cx - q(3.6), rcy - q(6.5), -q(1.2)),
           curve(cx - q(0.1), rcy + q(1.0), cx + q(3.4), rcy - q(5.0), q(1.4)),
           curve(cx + q(0.2), rcy + q(5.5), cx - q(2.8), rcy + q(8.5), q(0.6)),
           curve(cx + q(0.3), rcy + q(5.0), cx + q(3.0), rcy + q(8.0), -q(0.6)),
           curve(cx - q(3.6), rcy - q(6.5), cx - q(2.0), rcy - q(8.0), -q(0.6), n=3)]
    rune_groove(a, pts, front)
    # moss and lichen
    for _ in range(5):
        mx = cx + rng.uniform(-q(6), q(5))
        blob(a, ellipse_mask(a.shape, mx, bot - q(rng.uniform(0.5, 3)), q(rng.uniform(1.4, 2.4)), q(1.2)) & (front | sidef),
             'leaf', 3)
    blob(a, ellipse_mask(a.shape, cx - q(2), top + q(1.4), q(2.4), q(1.2)) & cap, 'leaf', 4)
    return finish(p)


def p_crate(w, h, seed, stack=1):
    """Crates of sawn boards: a lit top face of slats, a front of boards with a gap between each,
    corner battens, a diagonal brace, nails, a stencilled mark; stacked, the upper one smaller and
    turned."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=13 * stack, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    for s_ in range(stack):
        bw = q(w) - s_ * q(2.5)
        x0 = cx - bw // 2 + s_ * q(1)
        y1 = yb - s_ * q(12)
        y0 = y1 - q(9)
        tp = q(3)
        fill(a, x0, y0 - tp, x0 + bw, y0, code('timber', 1))
        k = 0
        xx = x0
        while xx < x0 + bw:
            sw = min(q(rng.uniform(2.6, 3.4)), x0 + bw - xx)
            if sw > 2:
                board(a, xx, y0 - 1, tp, sw - 1, -90, 'timber_warm', 4, rng, split=False, grain=False)
            xx += sw
        fill(a, x0, y0, x0 + bw, y1, code('timber', 1))
        yy = y0
        while yy < y1:
            sh = min(q(rng.uniform(2.4, 3.2)), y1 - yy)
            if sh > 2:
                board(a, x0, yy, bw, sh - 1, 0, ('timber', 'timber_warm')[int(rng.integers(0, 2))], int(rng.choice([2, 3])), rng)
            yy += sh
        for bx_, t in ((x0, 3), (x0 + bw - q(2), 2)):
            board(a, bx_ + q(2), y0, y1 - y0, q(2), 90, 'timber_cool', t, rng, split=False, grain=False)
        board(a, x0 + q(2), y1 - q(1.5), int(math.hypot(bw - q(4), y1 - y0 - q(3))), q(1.8),
              -math.degrees(math.atan2(y1 - y0 - q(3), bw - q(4))), 'timber_cool', 3, rng, split=False, grain=False)
        for nx, ny in ((x0 + 1, y0 + 1), (x0 + bw - q(2) + 1, y0 + 1), (x0 + 1, y1 - q(2)), (x0 + bw - q(2) + 1, y1 - q(2))):
            nail(a, nx, ny, rust=False)
        if s_ == 0:
            fill(a, x0 + bw // 2 - q(1.5), y0 + q(3.2), x0 + bw // 2 + q(1.5), y0 + q(4), code('soot', 2))
    return finish(p)


def p_barrel(w, h, seed):
    """A barrel: staves with grain, bulging at the belly (lit down the west, dark down the east), two
    iron hoops with a highlight and rivets, a lid of three boards inside its chime rim."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=15, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    r = q(w / 2)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    top, bot = yb - q(15), yb
    f = np.clip((Y - top) / max(1, bot - top), 0, 1)
    half = r * (0.84 + 0.16 * np.sin(f * math.pi))
    m = (np.abs(X - cx) < half) & (Y >= top) & (Y < bot)
    u = (X - cx) / np.maximum(1, half)                    # -1 .. 1 across the belly
    tt = np.where(u < -0.45, 4, np.where(u > 0.5, 2, 3))
    tt = np.where(u > 0.8, 1, tt)
    stave = ((u + 1) * 3.5).astype(int)
    tt = tt + np.where(stave % 2 == 0, 0, -1) * (np.abs(u) < 0.8)
    a[m] = FI['timber'] * 8 + np.clip(tt[m], 0, 5)
    belly = m & (u > -0.6) & (u < -0.38) & (f > 0.2) & (f < 0.8)
    a[belly] = code('timber', 5)                                        # the bulge catches the light
    seam = m & (np.abs(((u + 1) * 3.5) - np.round((u + 1) * 3.5)) < 0.08)
    a[seam] = code('timber', 1)
    for _ in range(6):
        gx = cx + rng.uniform(-r * 0.7, r * 0.6)
        gy = rng.uniform(top + q(3), bot - q(4))
        fill(a, int(gx), int(gy), int(gx) + 1, int(gy) + q(2), code('timber', 2))
    for hy in (top + q(3), bot - q(4)):
        hm = m & (Y >= hy) & (Y < hy + q(1.4))
        a[hm] = code('iron', 2)
        a[hm & (u < -0.3)] = code('iron', 3)
        a[hm & (Y < hy + 1) & (u < 0)] = code('iron', 5)
        for ux in (-0.55, 0.05, 0.6):
            rx_ = int(cx + ux * r)
            fill(a, rx_, int(hy + q(0.4)), rx_ + 2, int(hy + q(0.4)) + 2, code('iron', 4 if ux < 0.5 else 1))
    lid = ellipse_mask(a.shape, cx, top, r * 0.86, q(2.4))
    a[lid] = code('timber_cool', 2)
    inner = ellipse_mask(a.shape, cx, top + q(0.3), r * 0.7, q(1.7))
    a[inner] = code('timber_warm', 4)
    for k in (-1, 0, 1):
        a[inner & (np.abs(X - (cx + k * r * 0.3 + r * 0.15)) < 0.6)] = code('timber_warm', 2)    # the lid's planks
    a[inner & (X > cx + r * 0.4)] = code('timber_warm', 3)
    a[lid & ~ellipse_mask(a.shape, cx, top, r * 0.86 - 1, q(2.4) - 1) & (Y < top) & (X < cx)] = code('timber_cool', 4)
    return finish(p)


def p_trough(w, h, seed, hd=False):
    """The quench trough: a stone tank whose coping is a lit top plane on all four sides (the back and
    end rims narrow, the front rim wide, its front face below in mid tone, the east end in shade);
    inside, the far wall lit above the waterline, the water darkening with depth toward the front,
    a band of sky reflected across it and the near wall's shade along its front edge."""
    rng = np.random.default_rng(seed)
    p = _pic(max(w, 26) if hd else w, h, up=9, side=2)
    # (scale gate, 26 Oct: lower and longer, about 36 art px tall and 80 wide, its stone base two
    # courses: 0.6 m high, 1.5 m long)
    o = 3.0 if hd else 0.0
    w = max(w, 26) if hd else w
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    top = yb - q(h + 8 - (4.0 if hd else 0.0))
    rubble(a, x0, yb - q(7.5 - o), x1, yb, rng, base=3, course=(2.4, 3.4), length=(4, 7), moss=0.35, hd=hd)
    fill(a, x1 - q(1.8), yb - q(7.5 - o), x1, yb, code('stone', 1))                    # the east end in shade
    # the coping: four lit rims round the opening, the front rim's face below it
    a[_rect(a.shape, x0, top, x1, yb - q(7.5 - o))] = code('stone_warm', 4)
    a[_rect(a.shape, x0, top, x1, top + 1)] = code('stone_warm', 5)
    a[_rect(a.shape, x0, top, x0 + 1, yb - q(7.5 - o))] = code('stone_warm', 5)
    a[_rect(a.shape, x0, yb - q(9.5 - o), x1, yb - q(7.5 - o))] = code('stone_warm', 3)      # the front rim's face
    a[_rect(a.shape, x1 - q(1.8), top, x1, yb - q(7.5 - o))] = code('stone_warm', 3)
    for jx in range(x0 + q(6), x1 - q(2), q(7)):
        a[_rect(a.shape, jx, top, jx + 1, yb - q(9.5 - o))] = code('stone', 2)
    ix0, ix1, iy0, iy1 = x0 + q(1.8), x1 - q(3.4), top + q(1.4), yb - q(11.6 - o)
    # inside: the far wall lit, the waterline, water darkening toward the front, a sky band
    wall_h = q(1.6)
    if D >= 2.5:     # density 3: the front rim narrower, so the tank's water shows its depth
        iy1, wall_h = yb - q(10.0 - o), q(1.0)
        a[_rect(a.shape, x0, yb - q(10.0 - o), x1, yb - q(9.5 - o))] = code('stone_warm', 4)
    a[_rect(a.shape, ix0, iy0, ix1, iy0 + wall_h)] = code('stone', 4)
    a[_rect(a.shape, ix0, iy0 + wall_h, ix1, iy0 + wall_h + 1)] = code('water', 4)
    wy0 = iy0 + wall_h + 1
    for k, yy in enumerate(range(wy0, iy1)):
        f = (yy - wy0) / max(1, iy1 - wy0)
        if D >= 2.5:     # density 3: the far wall's light in the water at the back, deep at the front
            a[_rect(a.shape, ix0, yy, ix1, yy + 1)] = code(*(('water', 4) if f < 0.2 else ('water', 3) if f < 0.4 else
                                                             ('water', 2) if f < 0.7 else ('water_cool', 1)))
        else:
            a[_rect(a.shape, ix0, yy, ix1, yy + 1)] = code('water' if f < 0.45 else 'water_cool', 2 if f < 0.45 else 1)
    a[_rect(a.shape, ix0 + q(2), wy0 + q(1.4), ix1 - q(5), wy0 + q(1.4) + 2)] = code('sky', 4)
    a[_rect(a.shape, ix0 + q(6), wy0 + q(2.6), ix1 - q(2), wy0 + q(2.6) + 1)] = code('sky', 3)
    a[_rect(a.shape, ix0, iy0, ix0 + q(1.0), iy1)] = code('stone', 2)                # the west wall inside
    a[_rect(a.shape, ix0, iy1 - 1, ix1, iy1)] = code('water_cool', 0)                # the near wall's shade
    if D >= 2.5:
        # density 3: the water moves and the walls show where it stands: a green-dark algae line along
        # the far wall at the waterline (ragged), ripple arcs lit on their upper side, a drip ring under
        # where the smith dips the iron, the near rim's reflection a band of dark
        Yt, Xt = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        wl = iy0 + wall_h
        rag = (np.sin(Xt * 0.9) + np.sin(Xt * 0.37 + 1.0)) > 0.4
        a[(Xt >= ix0) & (Xt < ix1) & ((Yt == wl - 1) & rag | (Yt == wl - 2) & rag & (np.sin(Xt * 1.7) > 0.6))] = code('leaf', 1)
        for _ in range(5):
            rx0 = int(rng.uniform(ix0 + 2, ix1 - q(3)))
            ry0 = int(wy0 + rng.integers(0, max(1, iy1 - wy0 - 1)))
            ln = q(rng.uniform(1.2, 2.6))
            a[(Yt == ry0) & (Xt >= rx0) & (Xt < rx0 + ln)] = code('sky', 3)
            a[(Yt == ry0 + 1) & (Xt >= rx0 + 1) & (Xt < rx0 + ln + 1)] = code('water_cool', 1)
        dcx, dcy = int(ix0 + (ix1 - ix0) * 0.7), int(wy0 + (iy1 - wy0) * 0.5)
        ring_ = (np.abs(np.hypot((Xt - dcx) / 1.8, Yt - dcy) - q(1.0)) < 0.7)
        a[ring_ & (Xt >= ix0) & (Xt < ix1) & (Yt >= wy0) & (Yt < iy1)] = code('water', 4)
    return finish(p)


def p_coal(w, h, seed, hd=False):
    """A coal bin: a box of boards (lit top edge, shaded east end) heaped with coal, each lump with a
    glint on its upper left."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=9, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    stones_heap(a, cx, yb - q(4), w * 0.85, h * 0.8, rng, n=20 if D < 2.5 else 34, fams=('soot', 'soot', 'iron'),
                slates=False, planks_=False, hd=hd)
    if D >= 2.5:     # density 3: glints on the coal's facets, dust between the lumps
        for _ in range(16):
            gx, gy = int(cx + rng.uniform(-0.4, 0.4) * q(w)), int(yb - q(rng.uniform(3, 9)))
            if 0 <= gy < a.shape[0] - 1 and 0 <= gx < a.shape[1] - 2 and a[gy, gx] >= 0:
                a[gy, gx:gx + 2] = code('iron', 5)
                a[gy + 1, gx + 1] = code('soot', 0)
    prism(a, x0, yb - q(5.5), x1, yb, q(1.2), 'timber', 3, side=q(1.4))
    for xx in range(x0 + q(3), x1 - q(2), q(5)):
        fill(a, xx, yb - q(4), xx + 1, yb - 1, code('timber', 1))
    if D >= 2.5:     # density 3: the bin's end grain and the boards' worn foot
        Yc, Xc = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        endg = (Xc >= x1 - q(1.4)) & (Yc >= yb - q(4.3)) & (Yc < yb - 1) & ((Xc + Yc // 3) % 3 == 0) & (a >= 0)
        a[endg] = code('timber_cool', 0)
        endl = (Xc >= x1 - q(1.4)) & (Xc < x1 - q(1.4) + 1) & (Yc >= yb - q(4.3)) & (Yc < yb - 1)
        a[endl] = code('timber', 2)
        footr = (Yc == yb - 1) & (Xc >= x0) & (Xc < x1) & ((Xc // 3) % 2 == 0)
        a[footr] = code('timber', 2)
    return finish(p)


def p_woodpile(w, h, seed):
    """Split logs stacked end on under a cover board: each end a volume of rings (a pale heart, a
    darker ring, the bark round it), the split faces lit, dark gaps between the logs, the board's
    lit top and front edge, a stake at each end."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=15, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    r = q(2.4)
    for row in range(3):
        n = int(w / 5) - (row % 2)
        for k in range(n):
            x = x0 + q(3) + (q(2.4) if row % 2 else 0) + k * q(5)
            y = yb - q(2.6) - row * q(4.3)
            bark = ellipse_mask(a.shape, x, y, r, r * 0.92)
            a[bark] = code('timber_cool', 1)
            a[bark & ellipse_mask(a.shape, x - 1, y - 1, r - 1, r * 0.92 - 1)] = code('timber_cool', 2)
            end = ellipse_mask(a.shape, x - 1, y - 1, r - 2, r * 0.92 - 2)
            a[end] = code('timber_warm', 4)
            ring_ = end & ~ellipse_mask(a.shape, x - 1, y - 1, r * 0.55, r * 0.5) & ellipse_mask(a.shape, x - 1, y - 1, r * 0.55 + 1, r * 0.5 + 1)
            a[ring_] = code('timber_warm', 3)
            a[end & ~ellipse_mask(a.shape, x - 1.5, y - 1.5, r - 3, r * 0.92 - 3)] = code('timber_warm', 3)
            a[end & ellipse_mask(a.shape, x - 1.5, y - 1.5, r * 0.25, r * 0.25)] = code('timber_warm', 5)
            if rng.random() < 0.4:
                fill(a, int(x - 1), int(y - r + 2), int(x), int(y), code('timber_warm', 2))     # a check
    prism(a, x0, yb - q(15), x1, yb - q(13), q(0.8), 'timber_warm', 3, side=q(1))
    for sx in (x0, x1 - q(1.6)):
        prism(a, sx, yb - q(14), sx + q(1.6), yb, q(0.6), 'timber', 3, side=q(0.6))
    return finish(p)


def p_grindstone(w, h, seed):
    """A treadle grindstone: the sandstone wheel side on with its edge face (thickness) to the east and
    a highlight band on its upper west rim, the axle through bearing blocks on the frame, a crank, the
    treadle and its connecting rod up to the crank pin, a water pot hung on a bracket dripping on the
    wheel."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=20, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    for lx, t in ((cx - q(6), 3), (cx + q(5), 2)):
        bar(a, lx - q(1.6), yb - 1, lx, yb - q(9), max(1.4, q(0.8)), 'timber', t)
        bar(a, lx + q(1.6), yb - 1, lx, yb - q(9), max(1.4, q(0.8)), 'timber', t - 1)
    prism(a, cx - q(8), yb - q(10.5), cx + q(8), yb - q(8.5), q(0.7), 'timber_warm', 3, side=q(0.8))
    # treadle on the ground, rod to the crank
    board(a, cx - q(7), yb - q(2.4), q(12), q(1.8), -6, 'timber', 3, rng, split=False)
    wcx, wcy, R = cx - q(0.5), yb - q(14), q(5.5)
    pin = (wcx + q(7.5), wcy + q(2.5))
    bar(a, cx + q(4), yb - q(3), pin[0], pin[1], max(1.0, q(0.45)), 'iron', 2)
    # the wheel: edge face first, then the face, then its highlight band
    edge_ = ellipse_mask(a.shape, wcx + q(1.4), wcy, R, R)
    a[edge_] = code('stone_warm', 2)
    a[edge_ & (Y > wcy + R * 0.4)] = code('stone_warm', 1)
    face = ellipse_mask(a.shape, wcx, wcy, R, R)
    d = ((X - wcx) + (Y - wcy)) / (R * 1.41)
    tt = np.select([d < -0.55, d < 0.2, d < 0.7], [5, 4, 3], 2)
    a[face] = FI['stone_warm'] * 8 + tt[face]
    a[face & ~ellipse_mask(a.shape, wcx, wcy, R - 1, R - 1) & (d < -0.2)] = code('stone_warm', 5)
    if D >= 2.5:
        # density 3: the sandstone's grit and the rings the grinding has worn into the face, the hub
        # shadowed where the axle meets it
        rr_ = np.hypot(X - wcx, Y - wcy) / R
        wear = face & ((np.abs(rr_ - 0.55) < 0.05) | (np.abs(rr_ - 0.78) < 0.04))
        a[wear] = a[wear] - 1 * ((a[wear] % 8) > 1)
        grit = face & (rng.random(a.shape) < 0.12) & (a % 8 >= 3)
        a[grit] = a[grit] - 1
        lit2 = face & (rng.random(a.shape) < 0.05) & (a % 8 <= 4) & (d < 0.2)
        a[lit2] = a[lit2] + 1
    for _ in range(4):
        gx, gy = wcx + rng.uniform(-R * 0.5, R * 0.3), wcy + rng.uniform(-R * 0.5, R * 0.4)
        fill(a, int(gx), int(gy), int(gx) + 2, int(gy) + 1, code('stone_warm', 3))
    # axle through bearings, the crank and its pin
    a[_rect(a.shape, wcx - q(8), wcy - 1, wcx + q(7.5), wcy + 2)] = code('iron', 2)
    a[_rect(a.shape, wcx - q(8), wcy - 1, wcx + q(7.5), wcy)] = code('iron', 4)
    for bx_ in (cx - q(7.4), cx + q(4.6)):
        prism(a, bx_, wcy - q(1.4), bx_ + q(2.6), wcy + q(1.8), q(0.6), 'timber_cool', 3, side=q(0.8))
        bar(a, bx_ + q(1.3), wcy + q(1.8), bx_ + q(1.3), yb - q(10.5), max(1.2, q(0.6)), 'timber', 2)
    blob(a, ellipse_mask(a.shape, wcx, wcy, q(1.1), q(1.1)), 'iron', 3)
    bar(a, wcx + q(7.5), wcy, pin[0], pin[1], max(1.0, q(0.5)), 'iron', 3)
    blob(a, ellipse_mask(a.shape, pin[0], pin[1], q(0.8), q(0.8)), 'iron', 4)
    # the water pot on its bracket, dripping
    bx_, by_ = cx - q(7.4) + q(1.3), wcy - R - q(4)
    bar(a, bx_, wcy - q(1.4), bx_, by_, max(1.0, q(0.45)), 'iron', 2)
    bar(a, bx_, by_, wcx - q(1), by_, max(1.0, q(0.45)), 'iron', 3)
    pot = ellipse_mask(a.shape, wcx - q(1), by_ + q(1.8), q(1.8), q(1.6))
    up_ = (X - (wcx - q(1))) / q(1.8)
    a[pot] = FI['clay'] * 8 + np.clip(cyl_tones(up_, 3), 0, 5)[pot]
    a[_rect(a.shape, wcx - q(1), by_ + q(3.4), wcx - q(1) + 1, wcy - R + 1)] = code('water', 4)
    return finish(p)


def p_hay(w, h, seed):
    """A hay bale as a block: a lit top face of straw, a mid front face, the cut east end in shade,
    twine bands over the top and down the front, loose straws."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    prism(a, x0, yb - q(h + 8), x1, yb, q(h), 'sand', 3, side=q(3))
    for _ in range(int(w * 2)):
        sx = int(rng.integers(x0 + 2, x1 - q(3) - 1))
        sy = int(rng.integers(yb - q(h + 7), yb - 3))
        t = 4 if sy < yb - q(8) else 2
        fill(a, sx, sy, sx + 1, sy + q(1.4), code('sand', t))
    for xx in (x0 + q(w * 0.3), x1 - q(w * 0.35)):
        fill(a, xx, yb - q(h + 8), xx + 2, yb, code('timber_warm', 2))
    return finish(p)


def p_bench(w, h, seed):
    """A bench: a backrest of two rails on posts, the seat of three planks seen from above with a gap
    between each, the seat's thickness along its front with the shade it throws, end grain at both
    ends; timber trestle legs, each two splayed legs with a brace, lit on the west."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=22, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    # backrest: two posts and two rails standing behind the seat, the ground showing between
    for px in (x0 + q(2), x1 - q(4.4)):
        prism(a, px, yb - q(21.5), px + q(2.4), yb - q(12), q(0.8), 'timber', 3, side=q(0.8))
    for ry in (yb - q(21), yb - q(18)):
        board(a, x0 + q(0.5), ry, x1 - x0 - q(1), q(1.8), 0, 'timber_warm', 4, rng, split=False)
        sh = _rect(a.shape, x0 + q(0.5), ry + q(1.8), x1 - q(0.5), ry + q(1.8) + 2) & (a >= 0)
        a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - 1)
    # legs: trestles
    for lx in (x0 + q(4), x1 - q(4)):
        for sx in (-1, 1):
            bar(a, lx + sx * q(2.8), yb - 1, lx + sx * q(0.8), yb - q(8), max(1.4, q(0.8)), 'timber', 3 if sx < 0 else 2)
        bar(a, lx - q(2.2), yb - q(3.5), lx + q(2.2), yb - q(3.5), max(1.2, q(0.6)), 'timber_cool', 2)
    # the seat
    yy = yb - q(12.5)
    a[_rect(a.shape, x0, yy, x1, yy + 3 * q(1.6) + 2)] = code('timber', 0)
    for k in range(3):
        th = q(1.6)
        board(a, x0, yy, x1 - x0, th - 1, 0, ('timber_warm', 'timber_warm', 'timber')[k], (5, 4, 4)[k], rng, split=k == 1)
        yy += th + 1
    a[_rect(a.shape, x0, yy - 1, x1, yy + q(1.8))] = code('timber', 2)
    a[_rect(a.shape, x0, yy + q(1.8) - 1, x1, yy + q(1.8))] = code('timber', 1)
    sh = _rect(a.shape, x0, yy + q(1.8), x1, yy + q(3)) & (a >= 0)
    a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - 2)
    for ex, t in ((x0, 4), (x1 - q(1.4), 2)):
        a[_rect(a.shape, ex, yb - q(12.5), ex + q(1.4), yy + q(1.8))] = code('plaster_warm', t)
        a[_rect(a.shape, ex, yb - q(11.5), ex + q(1.4), yb - q(11.5) + 1)] = code('timber_warm', 2)
    return finish(p)


def p_fence(w, h, seed, rail_only=False):
    """A post and rail fence, w world px long: square posts with lit west faces, shaded east sides and
    weathered caps, two sawn rails nailed to them with their thickness showing."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=15, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    n = max(2, int(round(w / 16)) + 1)
    xs = [int(x0 + (x1 - x0 - q(3)) * k / (n - 1)) for k in range(n)]
    for k, xx in enumerate(xs):
        prism(a, xx, yb - q(15), xx + q(3), yb, q(1.4), 'timber', 3, side=q(1.1))
    for yy in (yb - q(12), yb - q(6)):
        board(a, x0 - q(1), yy + int(rng.integers(-1, 2)), x1 - x0 + q(2), q(1.8), 0, 'timber_warm', 3, rng)
        sh = _rect(a.shape, x0, yy + q(1.8), x1, yy + q(2.4)) & (a >= 0)
        a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - 1)
        for xx in xs:
            nail(a, xx + q(1), yy + 2, rng=rng)
    return finish(p)

def p_flower_tub(w, h, seed):
    """A clay planter as a volume: a rim with a lit top face round the soil, a mid front, a dark east
    side, plants spilling over it with flowers lit on top."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=11, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    prism(a, x0, yb - q(7), x1, yb, q(2.2), 'clay', 3, side=q(1.6))
    fill(a, x0 + q(1.2), yb - q(6.6), x1 - q(1.2), yb - q(5.6), code('earth', 1))
    for k in range(5):
        x = x0 + q(1.5) + k * q((w - 3) / 4)
        m = ellipse_mask(a.shape, x, yb - q(8), q(2.2), q(2.4))
        blob(a, m, 'leaf', 3 + k % 2)
        if k % 2 == 0:
            fill(a, x - 1, yb - q(10), x + 2, yb - q(10) + 3, code(('berry', 'brass', 'dusk')[k % 3], 4))
            fill(a, x - 1, yb - q(10), x + 1, yb - q(10) + 1, code(('berry', 'brass', 'dusk')[k % 3], 5))
    return finish(p)


def p_sacks(w, h, seed):
    """Seed sacks, two on the ground and one on top, each a lit volume with its neck tied."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=12, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    for dx, dy, s_ in ((-0.25, 0, 1.0), (0.22, 0, 0.9), (0.0, -1, 0.85)):
        sack(a, cx + q(w * dx), yb - q(5 * s_) - (q(5.5) if dy else 0), q(4.2 * s_), q(4.6 * s_))
    return finish(p)
def p_debris(w, h, seed, hd=False):
    """Storm litter on the flags: broken slates lying flat (each a thin plate, its face lit, its broken
    edge dark), a snapped batten with its splintered end, twigs with a few leaves."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=3, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    for _ in range(int(w * h / 30) + 3):
        x = cx + q(rng.uniform(-w / 2, w / 2))
        y = yb - q(rng.uniform(0, h))
        r = rng.random()
        if r < 0.5:
            sw, sh = q(rng.uniform(3, 5.5)), max(3, q(rng.uniform(1.4, 2.2)))
            fam = ('slate', 'slate_cool')[int(rng.integers(0, 2))]
            blk(a, x, y, x + sw, y + sh, fam, int(rng.choice([3, 4])), cut=1, bot=0, hd=hd)
            fill(a, x + 1, y + sh, x + sw, y + sh + 1, code(fam, 1))
            if rng.random() < 0.5:
                fill(a, x + sw - 2, y, x + sw, y + 2, code(fam, 1))           # a broken corner
        elif r < 0.65:
            board(a, x, y, q(rng.uniform(7, 11)), q(1.4), rng.uniform(-20, 20), 'timber_warm', 3, rng)
        else:
            x2, y2 = x + q(rng.uniform(4, 7)), y + q(rng.uniform(-2.5, 2.5))
            bar(a, x, y, x2, y2, max(1.0, D * 0.35), 'timber_cool', 2)
            for k in range(2):
                lx, ly = x + (x2 - x) * (0.4 + 0.4 * k), y + (y2 - y) * (0.4 + 0.4 * k) - q(0.8)
                m = ellipse_mask(a.shape, lx, ly, q(1.1), q(0.8))
                fam = ('leaf', 'brass')[int(rng.integers(0, 2))]
                a[m] = code(fam, 3)
                a[m & ellipse_mask(a.shape, lx - 1, ly - 1, q(0.6), q(0.4))] = code(fam, 4)
    if hd:
        # the litter lies in the house light too: the pieces toward the east end of the heap a
        # step into the shade of the rest, the west ones catching it
        Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        xs_ = np.nonzero((a >= 0).any(0))[0]
        if len(xs_):
            x0_, x1_ = xs_.min(), xs_.max()
            _step(a, (X > x0_ + 0.62 * (x1_ - x0_)) & (a % 8 >= 2), -1)
            _step(a, (X < x0_ + 0.3 * (x1_ - x0_)) & (a % 8 <= 3), +1)
    return finish(p)

def p_cart(w, h, seed):
    """The same parked handcart: at density 3 the shafts lap into the underframe, a bearing
    carries the axle, and the bed, end boards and wheel have separate material planes. Wear
    follows joints and handholds; the existing load, canvas and ground anchor stay in place.
    Lower densities retain their original drawing below."""
    if D >= 2.5:
        rng = np.random.default_rng(seed)
        p = _pic(w, h, up=18, side=7)
        a, cx, yb = p.a, p.ax, p.ay
        Y, X = grid(a)
        x0, x1 = cx - q(w / 2), cx + q(w / 2)
        wc = (cx + q(w * 0.12), yb - q(6))
        R = q(6)

        # Shafts are continuous timbers, not detached diagonal marks. Their inner ends
        # continue behind the front boards and lap into the cross rail.
        for dy in (0, q(3)):
            sy = yb - q(1.5) - dy
            board(a, x0 - q(6), sy, q(16), q(1.6), -38,
                  'timber', 3, rng, split=False)
            bar(a, x0 - q(5.8), sy + 2, x0 - q(4.3), sy - q(1),
                1.0, 'timber_warm', 3)
        board(a, x0 + q(1), yb - q(8), x1 - x0 - q(2), q(2.2),
              0, 'timber_cool', 2, rng, split=False)
        bar(a, x0 + q(1), yb - q(7), wc[0], yb - q(12),
            q(0.8), 'timber', 2)
        bar(a, x0 + q(3), wc[1], wc[0] + q(1), wc[1],
            q(0.8), 'iron', 1)
        bar(a, x0 + q(3), wc[1] - 1, wc[0], wc[1] - 1,
            1.0, 'iron', 3)

        # Back rail, exposed floor, front boards, dark east end and the underside.
        # Board grain stays inside its actual face; no texture over every plane.
        box_hd(a, x0, x1, yb - q(18), yb - q(16), q(0.8),
               ('timber_cool', 'timber', 'timber_warm'), base=2.8, side=q(1.5))
        top, front, east = box_hd(a, x0, x1, yb - q(16.5), yb - q(8), q(4),
                                   ('timber_cool', 'timber', 'timber_warm'), base=2.8, side=q(2))
        for k in range(3):
            board(a, x0 + 1, yb - q(16) + k * q(1.2), x1 - x0 - 2,
                  q(1.1), 0, 'timber', 3, rng, split=False, where=top)
            board(a, x0 + 1, yb - q(12.4) + k * q(1.5), x1 - x0 - 2,
                  q(1.4), 0, 'timber_warm' if k == 1 else 'timber', 3,
                  rng, split=(k == 2), where=front)
        fill(a, x0, yb - q(8) - 2, x1, yb - q(8), code('timber_cool', 0))
        # End grain at the narrow side, with interrupted checks rather than bright stripes.
        for yy in (yb - q(11), yb - q(9.5)):
            fill(a, x1 - q(1.6), yy, x1 - 1, yy + 1, code('timber', 1), where=east)

        # Corner stiles reach the cross rail. Iron straps and paired fasteners explain
        # the join; only the top edge of each strap catches light.
        for xx in (x0 + 1, x1 - q(1.5)):
            box_hd(a, xx, xx + q(1.2), yb - q(17), yb - q(7), q(0.7),
                   ('timber_cool', 'timber', 'timber_warm'), base=2.6, side=1)
            fill(a, xx, yb - q(13.5), xx + q(1.2), yb - q(12.5), code('iron', 1))
            fill(a, xx, yb - q(13.5), xx + q(1.2) - 1, yb - q(13.5) + 1, code('iron', 3))
            for yy in (yb - q(16), yb - q(10)):
                nail(a, xx, yy, rust=False)
        board(a, x0, yb - q(16.5), x1 - x0, q(1.4), 0,
              'timber_warm', 3, rng, split=False, grain=False)
        for xx, yy, ln in ((x0 + q(2), yb - q(16.5), q(2)),
                           (x1 - q(5), yb - q(12.4), q(1.2))):
            fill(a, xx, yy, xx + ln, yy + 1, code('timber_warm', 4))
            fill(a, xx + ln - 2, yy + 1, xx + ln, yy + 2, code('timber', 2))

        # Keep the old sack/crate load in its original position. Shade only this
        # local sack; shared sack() and every other caller remain unchanged.
        scx, scy = x0 + q(w * 0.35), yb - q(19.5)
        rx, ry = q(4.2), q(3.4)
        sack(a, scx, scy, rx, ry, fam='sand')
        nx, ny = (X - scx) / rx, (Y - scy) / ry
        d = nx * nx + ny * ny
        cloth = d <= 1
        paint(a, cloth, ('sand_cool', 'sand', 'sand_warm'),
              2.2 + 1.8 * lam(nx, ny * 0.8, np.sqrt(np.clip(1 - d, 0, 1))), lo=1, hi=4)
        seam = cloth & (np.abs(nx - 0.35 - ny * 0.15) < 0.06) & (ny > -0.6)
        _step(a, seam, -1)
        bar(a, scx - q(1), scy - ry + 1, scx - q(2), scy - q(0.5),
            0.8, 'sand', 2, where=cloth)
        prism(a, x1 - q(9), yb - q(22), x1 - q(2), yb - q(16.5),
              q(1.6), 'timber', 3, side=q(1))
        bar(a, x1 - q(8), yb - q(17.2), x1 - q(3.2), yb - q(20.7),
            1.0, 'timber_warm', 2)
        for xx in (x1 - q(8), x1 - q(3.5)):
            nail(a, xx, yb - q(18), rust=False)

        # A visible bearing joins the axle to the underframe, behind the near wheel.
        box_hd(a, wc[0] - q(1.8), wc[0] + q(1.8), wc[1] - q(2.8), wc[1] + q(1),
               q(0.7), 'iron', base=2.0, side=q(0.7))
        radial = np.sqrt((X - wc[0]) ** 2 + (Y - wc[1]) ** 2)
        tyre = (radial <= R) & (radial > R - q(1))
        felloe = (radial <= R - q(1)) & (radial > R - q(2.2))
        paint(a, felloe, ('timber_cool', 'timber', 'timber_warm'),
              2.5 - 0.7 * (X - wc[0]) / R - 0.6 * (Y - wc[1]) / R)
        paint(a, tyre, 'iron', 1.6 - 0.9 * (X - wc[0]) / R - 0.8 * (Y - wc[1]) / R)
        # Six load-bearing spokes meet six wooden felloe joints, not a solid wheel disk.
        for k in range(6):
            ang = k * math.pi / 3
            ex, ey = math.cos(ang), math.sin(ang)
            joint = seg_mask(a.shape, wc[0] + ex * (R - q(2.3)), wc[1] + ey * (R - q(2.3)),
                             wc[0] + ex * (R - q(0.9)), wc[1] + ey * (R - q(0.9)), 0.6)
            _step(a, joint & felloe, -1)
            bar(a, wc[0], wc[1], wc[0] + ex * (R - q(2)), wc[1] + ey * (R - q(2)),
                max(1.2, q(0.5)), 'timber_warm', 3)
        blob(a, ellipse_mask(a.shape, wc[0], wc[1], q(2), q(2)), 'timber', 2)
        blob(a, ellipse_mask(a.shape, wc[0], wc[1], q(1.2), q(1.2)), 'iron', 2)
        fill(a, wc[0] - 1, wc[1] - 2, wc[0] + 1, wc[1], code('iron', 4))
        fill(a, wc[0] - 1, wc[1] + 1, wc[0] + 2, wc[1] + 2, code('iron', 0))
        return finish(p)

    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=18, side=7)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    for dy in (0, q(3)):
        board(a, x0 - q(6), yb - q(1.5) - dy, q(13), q(1.6), -38, 'timber', 3, rng, split=False)
    fill(a, x0, yb - q(15), x1, yb - q(8), code('timber', 1))
    yy = yb - q(15)
    while yy < yb - q(8):
        board(a, x0, yy, x1 - x0, q(2.0), 0, ('timber', 'timber_warm')[int(rng.integers(0, 2))], 3, rng)
        yy += q(2.4)
    board(a, x0, yb - q(16.5), x1 - x0, q(1.6), 0, 'timber_warm', 4, rng, split=False)
    for nx in (x0 + q(1), x1 - q(2)):
        nail(a, nx, yb - q(14), rng=rng)
    sack(a, x0 + q(w * 0.35), yb - q(19.5), q(4.2), q(3.4))
    prism(a, x1 - q(9), yb - q(22), x1 - q(2), yb - q(16.5), q(1.6), 'timber', 3, side=q(1))
    wc = (cx + q(w * 0.12), yb - q(6))
    R = q(6)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    tyre = ellipse_mask(a.shape, wc[0], wc[1], R, R) & ~ellipse_mask(a.shape, wc[0], wc[1], R - q(1), R - q(1))
    felloe = ellipse_mask(a.shape, wc[0], wc[1], R - q(1), R - q(1)) & ~ellipse_mask(a.shape, wc[0], wc[1], R - q(2.2), R - q(2.2))
    a[felloe] = code('timber', 3)
    a[felloe & (X > wc[0] + q(1))] = code('timber', 2)
    a[tyre] = code('iron', 2)
    a[tyre & (Y < wc[1]) & (X < wc[0])] = code('iron', 4)
    for k in range(6):
        ang = k * math.pi / 3
        bar(a, wc[0], wc[1], wc[0] + math.cos(ang) * (R - q(2)), wc[1] + math.sin(ang) * (R - q(2)), max(1.2, q(0.5)),
            'timber_warm', 3)
    blob(a, ellipse_mask(a.shape, wc[0], wc[1], q(1.6), q(1.6)), 'iron', 3)
    return finish(p)


PROPS = {
    'debris': p_debris,
    'cart': p_cart,
    'rubble': p_rubble,
    'well': lambda w, h, s, hd=False: p_well(w, h, s, choked=False, hd=hd),
    'well_choked': lambda w, h, s, hd=False: p_well(w, h, s, choked=True, hd=hd),
    'lantern': lambda w, h, s: p_lantern(w, h, s, lit=False),
    'lantern_lit': lambda w, h, s: p_lantern(w, h, s, lit=True),
    'stall': p_stall,
    'anvil': p_anvil,
    'glow': p_fire,
    'smoke': p_smoke,
    'beds': lambda w, h, s: p_beds(w, h, s, scorched=True),
    'beds_dug': lambda w, h, s: p_beds(w, h, s, scorched=False),
    'notice_board': p_notice_board,
    'waystone': p_waystone,
    'crate': p_crate,
    'crates': lambda w, h, s: p_crate(w, h, s, stack=2),
    'barrel': p_barrel,
    'trough': p_trough,
    'coal': p_coal,
    'woodpile': p_woodpile,
    'grindstone': p_grindstone,
    'hay': p_hay,
    'bench': p_bench,
    'fence': p_fence,
    'flower_tub': p_flower_tub,
    'sacks': p_sacks,
}


def prop(kind: str, w: float, h: float, seed: int = 0, hd: bool = False) -> Pic:
    """A prop picture. `hd` (explicit, never a module switch) turns on the fix-queue-2 forms of the
    painters that have them; the caller decides, so the output never depends on what ran before."""
    fn = PROPS_HD[kind] if (D >= 2.5 and kind in PROPS_HD) else PROPS[kind]
    if 'hd' in inspect.signature(fn).parameters:
        return fn(w, h, seed, hd=hd)
    return fn(w, h, seed)


# ------------------------------------------------------------------------------------------------
# density 3 and up: props drawn as forms (26 Oct, the fix queue)
# ------------------------------------------------------------------------------------------------
# Matt, 26 Oct: "make sure you get the 3d effect right every time". These painters shade each part
# from its form's normal against the house light (upper left and above: a lit top and face, a form
# shadow, a bounce at the shaded rim), lay the material's structure on top as tone steps (staves and
# hoops, grain and nails, burlap, stalks), give thin parts their thickness, put occlusion where
# parts meet and a contact shade at the foot. Density 2 keeps the painters above.
LIGHT = (-0.55, -0.30, 0.78)           # towards the light: west, north, up (axes east, south, up)


def lam(nx, ny, nz):
    """Light on a normal (east, south, up): -1 .. 1."""
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


def paint(a, m, fams, t, lo=0, hi=5):
    """Write mask m with float tones t (rounded, clipped) in a family name or a per-pixel array of
    names (warm where lit and cool in shade when given a (cool, body, warm) triple)."""
    tt = np.clip(np.round(np.broadcast_to(np.asarray(t, float), m.shape)), lo, hi).astype(int)
    if isinstance(fams, tuple):
        cool, body, warm = fams
        fa = np.where(tt >= 4, FI[warm], np.where(tt <= 1, FI[cool], FI[body]))
    else:
        fa = np.full(m.shape, FI[fams])
    a[m] = (fa * 8 + tt)[m]


def grid(a):
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    return Y, X


def upright(a, cx, top, bot, half, fams, base=2.6, k=2.6, seams=0, rng=None, bulge=0.0, z=None, hd=False):
    """An upright round body (a barrel, a block, a tub) between rows top and bot, its half width
    `half(f)` at f = 0 (top) .. 1 (bottom): cylinder light across it (a highlight band left of
    centre, the core shadow right of it, a bounce at the east rim), `seams` staves or bark seams
    that wrap with the form (dark seams, a lit lip west of each), occlusion at the foot. Returns
    (mask, u, f)."""
    Y, X = grid(a)
    f = np.clip((Y - top) / max(1, bot - top), 0, 1)
    hw = half(f)
    u = (X - cx) / np.maximum(1, hw)
    m = (np.abs(u) <= 1) & (Y >= top) & (Y < bot)
    nzs = np.sqrt(np.clip(1 - u * u, 0, 1))
    if hd:
        # density 3: the normal of a round body seen from the front (east, south, up): across it
        # (u, toward the viewer sqrt(1 - u^2)), tilted up a little at a bulge; the brightest band
        # falls left of centre, not on the west rim
        I = lam(u, -nzs * 0.35 + 0.0, nzs * 0.9 + bulge * np.cos(f * math.pi) * 0.3)
    else:
        I = lam(u * nzs ** 0 * 1.0, nzs * 0.9, bulge * np.cos(f * math.pi) + 0.12)
    t = base + k * I + np.where(u > 0.84, 0.7, 0)
    if seams:
        ang = np.arcsin(np.clip(u, -1, 1))
        step_ = math.pi / seams
        ph = (ang + math.pi / 2) / step_
        fr = ph - np.floor(ph)
        wid = 0.5 / np.maximum(1.0, hw * nzs * step_)               # one texel wide on the form
        seam = (fr < wid) & (np.abs(u) < 0.97)
        lip = (fr >= wid) & (fr < wid + 1.0 / np.maximum(1.0, hw * nzs * step_)) & (u < 0.3)
        t = t - 1.5 * seam + 0.6 * lip
        if rng is not None:
            sid = np.floor(ph).astype(int)
            jit = rng.uniform(-0.45, 0.45, seams + 3)
            t = t + jit[np.clip(sid, 0, seams + 2)]
    t = t - np.where(Y >= bot - q(0.8), 1.0, 0)
    paint(a, m, fams, t)
    return m, u, f


def ellipse_top(a, cx, cy, rx, ry, fams, base=4.0, rim=None):
    """A top seen from above: a lit plane, a little darker to the lower right; with `rim` (texels)
    a raised rim round a recessed face: the rim's top lit (brighter on its far side), the face's
    NW edge in the rim's shadow and a lit sliver of the inner wall along its SE edge. Returns
    (top, face, shadow, lit wall) masks."""
    Y, X = grid(a)
    def ell(ox, oy, k):
        return ((X - cx - ox) / (rx * k)) ** 2 + ((Y - cy - oy) / (ry * k)) ** 2 <= 1
    du, dv = (X - cx) / rx, (Y - cy) / ry
    m = ell(0, 0, 1.0)
    t = base + 0.5 * np.clip(-(du + dv) * 0.7, 0, 1) - 0.9 * np.clip((du + dv) * 0.7, 0, 1)
    paint(a, m, fams, t)
    if not rim:
        return m, None, None, None
    k = 1 - rim / max(1.0, ry) * 0.5
    inner = ell(0, 0.4, k)
    ring = m & ~inner
    paint(a, ring, fams, np.where(dv < 0, base + 0.7, base) - 0.7 * (du > 0.45))
    sh = inner & ~ell(1.6, 1.0, k)
    lw = inner & ~ell(-1.0, -0.8, k) & ~sh
    return m, inner, sh, lw


def p_barrel_hd(w, h, seed, hd=False):
    """A barrel: seven staves bulging at the belly, lit down the west with the core shadow east of
    centre and a bounce at the rim, every seam dark with a lit lip; two iron hoops standing proud
    (lit top edge, rivets, their shadow on the wood below); the chime round the head, the head's
    boards recessed inside it with the rim's shadow on their NW edge."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=15, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    # (scale gate, 26 Oct: a barrel reaches a person's belt, 0.42 to 0.62 A: about 40 art px tall
    # and 28 wide, 0.9 by 0.6 m)
    r = q(min(w, 8.6) / 2)
    top, bot = yb - q(11.6), yb
    half = lambda f: r * (0.84 + 0.16 * np.sin(f * math.pi))
    m, u, f = upright(a, cx, top, bot, half, ('timber_cool', 'timber', 'timber_warm'), base=2.7, seams=7, rng=rng, bulge=0.25, hd=hd)
    Y, X = grid(a)
    # grain: short dashes along the staves
    for _ in range(int(w * 0.9)):
        gx = cx + rng.uniform(-0.75, 0.65) * r
        gy = rng.uniform(top + q(2.5), bot - q(2.5))
        sel = m & (np.abs(X - gx) < 0.6) & (Y >= gy) & (Y < gy + q(rng.uniform(1.2, 2.6)))
        a[sel] = a[sel] - 1 * ((a[sel] % 8) > 0)
    # hoops
    for hy in (top + q(2.0), bot - q(3.4)):
        hm = m & (Y >= hy) & (Y < hy + q(1.4))
        nzs = np.sqrt(np.clip(1 - u * u, 0, 1))
        paint(a, hm, ('iron', 'iron', 'iron'), 2.4 + 2.4 * lam(u, nzs, 0.1) + 1.2 * (Y < hy + 1))
        below = m & (Y >= hy + q(1.4)) & (Y < hy + q(1.4) + 2)
        a[below] = a[below] - 1 * ((a[below] % 8) > 0)
        for ux in (-0.62, -0.05, 0.55):
            rx_ = int(cx + ux * half(np.clip((hy - top) / (bot - top), 0, 1)))
            fill(a, rx_, int(hy + q(0.4)), rx_ + 2, int(hy + q(0.4)) + 2, code('iron', 5 if ux < 0 else 1))
    # the head: the chime (stave ends) round a recessed head of three boards
    hm, inner, sh, lw = ellipse_top(a, cx, top, r * 0.86, q(1.9), ('timber_cool', 'timber', 'timber_warm'), base=3.6, rim=q(0.8))
    Y, X = grid(a)
    for k in range(3):
        bx0 = cx - r * 0.7 + k * r * 0.48
        board_m = inner & (X >= bx0) & (X < bx0 + r * 0.48)
        paint(a, board_m, 'timber_warm', (3.2, 2.8, 3.0)[k] - 0.6 * (X > cx + r * 0.4))
        a[inner & (np.abs(X - bx0) < 0.6)] = code('timber', 1)
    a[sh] = code('timber', 1)
    a[lw & ~sh] = code('timber_warm', 4)
    return finish(p)


def p_anvil_hd(w, h, seed, hd=False):
    """The anvil on its oak block, as forms: the block an upright round (lit west, core shadow, bark
    seams, the sawn top with rings and checks, the anvil's shadow on it); the anvil's face a polished
    top plane with its hardy and pritchel holes, the thickness of the face below it, the east heel
    in shade; the horn a cone lit along its upper west side; a waisted body and splayed feet; a
    hammer resting on the block's top and a pair of tongs leaning against it; scale on the block."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=17, side=7)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    # tongs leaning against the block's west side (behind it)
    for dx in (-0.5, 0.5):
        bar(a, cx - q(7.5) + q(dx), yb - 1, cx - q(4.6) + q(dx) * 0.6, yb - q(8), max(1.0, q(0.42)), 'iron', 2 if dx > 0 else 3)
    # the block (scale gate, 26 Oct: the anvil's face at a smith's hip, about 42 art px in all)
    bt = yb - q(5.6)
    R = q(5.6)
    upright(a, cx, bt, yb, lambda f: R * (1 + 0.06 * f), ('timber_cool', 'timber', 'timber_warm'), base=2.5, seams=9, rng=rng, hd=hd)
    tm, _i, _s, _l = ellipse_top(a, cx, bt, R, q(2.1), ('timber_warm', 'plaster_warm', 'plaster'), base=3.4)
    du, dv = (X - cx) / R, (Y - bt) / q(2.1)
    rr = np.sqrt(du * du + dv * dv)
    for rk in (0.35, 0.62, 0.86):
        a[tm & (np.abs(rr - rk) < 0.07)] = code('plaster_warm', 2)
    a[tm & (rr > 0.92) & (dv > -0.2)] = code('timber', 2)                     # bark rim
    # the anvil's shadow on the block's top (east and down of its feet)
    shm = tm & (np.abs(X - cx - q(1.2)) < q(4.6)) & (Y > bt - q(0.6))
    a[shm] = np.maximum((a[shm] // 8) * 8, a[shm] - 2)
    # scale flakes on the block's top
    for _ in range(5):
        sx, sy = cx + rng.uniform(-0.8, 0.8) * R, bt + rng.uniform(-0.5, 0.6) * q(2.1)
        fill(a, int(sx), int(sy), int(sx) + 2, int(sy) + 1, code('iron', 1))
    # feet and waist
    feet = (Y >= bt - q(2.6)) & (Y < bt - q(0.4)) & (np.abs(X - cx) < q(4.4) - (bt - q(0.4) - Y) * 0.35)
    paint(a, feet, 'iron', 2.2 + 2.2 * np.clip(-(X - cx) / q(4.4), -1, 1) + 1.0 * (Y < bt - q(2.2)))
    wy0, wy1 = bt - q(5.2), bt - q(2.6)
    wf = np.clip((Y - wy0) / max(1, wy1 - wy0), 0, 1)
    whw = q(2.0) + wf * q(1.4)
    uw = (X - cx) / np.maximum(1, whw)
    waist = (np.abs(uw) <= 1) & (Y >= wy0) & (Y < wy1)
    paint(a, waist, 'iron', 2.6 + 3.2 * lam(uw, np.sqrt(np.clip(1 - uw * uw, 0, 1)), 0.1) + 0.8 * ((uw > -0.6) & (uw < -0.3)))
    # the body: face (top plane), its front thickness, the heel's east end in shade
    fy0, fy1, ft = bt - q(8.2), bt - q(5.2), q(1.6)
    fx0, fx1 = cx - q(5.2), cx + q(5.8)
    face = (Y >= fy0) & (Y < fy0 + ft) & (X >= fx0) & (X < fx1)
    front = (Y >= fy0 + ft) & (Y < fy1) & (X >= fx0 + 1) & (X < fx1 - 1)
    paint(a, front, 'iron', 2.2 - 0.9 * ((X - fx0) / (fx1 - fx0)) + 0.8 * (Y < fy0 + ft + 1))
    paint(a, face, 'iron', 4.6 - 1.2 * ((X - fx0) / (fx1 - fx0)) + 0.5 * (Y < fy0 + 1))
    a[face & (Y >= fy0 + 1) & (Y < fy0 + 2) & (X > fx0 + q(1)) & (X < cx + q(2))] = code('snow', 5)   # the polished glint
    east = (X >= fx1 - q(1.4)) & (X < fx1) & (Y >= fy0) & (Y < fy1)
    paint(a, east, 'iron', 1.0 + (Y < fy0 + ft))
    fill(a, cx + q(3.3), fy0 + q(0.4), cx + q(4.3), fy0 + q(1.2), code('soot', 0))          # hardy hole
    fill(a, cx + q(1.9), fy0 + q(0.6), cx + q(2.4), fy0 + q(1.0) + 1, code('soot', 0))      # pritchel hole
    # the horn: a cone pointing west, lit on its upper west side
    hx0, hx1 = cx - q(10.5), fx0 + 1
    hl = (X - hx0) / max(1, hx1 - hx0)
    hr = q(1.6) * np.clip(hl, 0, 1) ** 0.8 + 0.6
    hcy = fy0 + q(1.6) + (1 - hl) * q(0.6)
    vv = (Y - hcy) / np.maximum(0.6, hr)
    horn = (X >= hx0) & (X < hx1) & (np.abs(vv) <= 1)
    paint(a, horn, 'iron', 2.3 + 2.4 * lam(-0.3, vv * 0.5, -vv) + 0.4 * (hl < 0.25))
    # the hammer on the block's top: an ash handle lit along its top, the iron head
    hy = bt + q(0.6)
    bar(a, cx + q(0.5), hy, cx + q(5.4), hy - q(0.4), max(1.0, q(0.45)), 'timber_warm', 4)
    head = (X >= cx - q(0.8)) & (X < cx + q(1.2)) & (Y >= hy - q(1.6)) & (Y < hy + q(0.7))
    paint(a, head, 'iron', 3.4 - 1.6 * ((X - (cx - q(0.8))) / q(2.0)) + 0.8 * (Y < hy - q(1.0)))
    return finish(p)




def p_beds_hd(w, h, seed, scorched=True):
    """Four raised beds behind the hut, joined by the trodden paths between them (so the plot is one
    piece of ground): each frame of two boards stood on edge, their top edges lit (the thickness of
    the wood), the south board's face in mid tone with grain and nail heads, the north board's inner
    face showing above the soil in its own shade, the east boards dark, a stake at each corner; the
    soil lower than the boards, in the boards' shadow along its north and west edges, worked into
    ridges lit on their north slopes with clods between. Dug over: two beds sown with rows of
    seedlings (two leaves each, lit on top, a speck of shade under). Scorched: ash and soot, charred
    stalks, embers, the boards' tops burnt black in places."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=6, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, y0 = cx - q(w / 2), yb - q(h)
    # the plot's ground: trodden earth under and between the beds
    plot = (X >= x0 - q(1)) & (X < x0 + q(w) + q(1)) & (Y >= y0 - q(1)) & (Y < yb)
    soilf = ('earth_cool', 'earth', 'earth_warm')
    pn = ndi.gaussian_filter(rng.random(a.shape), 1.6)
    pn = (pn - pn.mean()) / max(1e-6, pn.std())
    paint(a, plot, soilf, 3.0 + 0.5 * np.clip(pn, -1.5, 1.5))
    for _ in range(int(w * h / 18)):                                   # trodden pebbles and clods
        px, py = int(rng.uniform(x0, x0 + q(w))), int(rng.uniform(y0, yb - 2))
        fill(a, px, py, px + 2, py + 1, code('earth_warm', 4))
        fill(a, px + 1, py + 1, px + 3, py + 2, code('earth', 1))
    bw, bh = (w - 6) / 2, (h - 6) / 2
    th = q(1.2)                                                        # board thickness seen from above
    k = 0
    for j in range(2):
        for i in range(2):
            bx0 = x0 + q(i * (bw + 6))
            by0 = y0 + q(j * (bh + 6))
            bx1, by1 = bx0 + q(bw), by0 + q(bh)
            face_h = q(2.2)                                            # the south board's face
            # the soil: lower than the frame, the frame's shadow on its north and west edges
            ix0, iy0, ix1, iy1 = bx0 + th, by0 + th, bx1 - th, by1 - th
            inner = (X >= ix0) & (X < ix1) & (Y >= iy0) & (Y < iy1)
            if scorched:
                sf = ('soot', 'ash', 'ash')
            else:
                sf = ('earth_cool', 'earth', 'earth_warm')
            ry = (Y - iy0) / max(1.0, q(3.0))
            fr = ry - np.floor(ry)
            ridge = 2.6 + 1.2 * np.cos(fr * 2 * math.pi) * 0.9 - 0.6 * (fr > 0.55)
            if scorched:
                ridge = ridge - 0.8 + 0.6 * (pn > 0.8)
            # the furrows' bottoms broken by clods and deeper hollows
            ridge = ridge - 0.9 * ((fr > 0.55) & (np.sin(X * 0.7 + Y * 1.3) > 0.55))
            paint(a, inner, sf, ridge + 0.35 * np.clip(pn, -1.5, 1.5))
            # the inner face of the north board, standing above the soil
            nf = inner & (Y < iy0 + q(1.4))
            paint(a, nf, ('timber_cool', 'timber', 'timber_warm'), 2.2 + 0.8 * (Y < iy0 + 1)
                  - 1.2 * ((np.sin(X * 0.55 + j * 2.1 + i) > 0.82) & (Y >= iy0 + 1)))       # grain and checks
            shade_ = inner & ~nf & ((Y < iy0 + q(2.4)) | (X < ix0 + q(1.0)))
            a[shade_] = np.maximum((a[shade_] // 8) * 8, a[shade_] - 1)
            # clods and stones in the soil, lit on their upper left
            for _ in range(int(bw * bh / 9)):
                px, py = int(rng.uniform(ix0 + 2, ix1 - 3)), int(rng.uniform(iy0 + q(1.8), iy1 - 2))
                fill(a, px, py, px + 2, py + 1, code(sf[2], 4))
                fill(a, px + 1, py + 1, px + 2, py + 2, code(sf[0], 1))
            # the frame: top edges of the four boards (lit, lighter on the north and west boards)
            frame = ((X >= bx0) & (X < bx1) & (Y >= by0) & (Y < by1)) & ~inner
            ft = np.where(Y < by0 + th, 4.2, np.where(X < bx0 + th, 4.0, np.where(X >= bx1 - th, 2.6, 3.4)))
            paint(a, frame, ('timber_cool', 'timber', 'timber_warm'), ft + 0.4 * (np.sin(X * 0.9 + Y * 0.3) > 0.7))
            # the south board's outer face below its top edge, the east board's end in shade
            face = (X >= bx0) & (X < bx1) & (Y >= by1) & (Y < by1 + face_h)
            paint(a, face, ('timber_cool', 'timber', 'timber_warm'), 2.8 - 1.4 * (X >= bx1 - th) + 0.7 * (Y < by1 + 1)
                  - 0.9 * (Y >= by1 + face_h - 1))
            seam = face & (np.abs(Y - (by1 + face_h / 2)) < 0.6)
            a[seam] = code('timber', 1)
            for gx in range(int(bx0 + q(2)), int(bx1 - q(2)), q(4)):
                fill(a, gx, int(by1 + q(0.5)), gx + 2, int(by1 + q(0.5)) + 2, code('iron', 4))
                fill(a, gx + 1, int(by1 + q(0.5)) + 1, gx + 2, int(by1 + q(0.5)) + 2, code('iron', 1))
            if scorched:
                for _ in range(2):                                     # charred spots on the board tops, ragged
                    cxp, cyp = rng.uniform(bx0, bx1), rng.choice([by0 + th / 2, by1 - th / 2])
                    burnt = frame & (((X - cxp) / q(rng.uniform(1.4, 2.6))) ** 2 + ((Y - cyp) / q(0.8)) ** 2
                                     + 0.35 * np.sin(X * 1.7) < 1)
                    a[burnt] = np.where(a[burnt] % 8 >= 3, code('soot', 2), code('soot', 1))
            # stakes at the corners: a square post with a lit top and west face
            for sx_ in (bx0 - 1, bx1 - q(1.4) + 1):
                st = (X >= sx_) & (X < sx_ + q(1.4)) & (Y >= by0 - q(2.4)) & (Y < by1 + face_h)
                paint(a, st, ('timber_cool', 'timber', 'timber_warm'), np.where(Y < by0 - q(1.6), 4.4,
                      np.where(X < sx_ + q(0.7), 3.4, 2.0)))
            # what grows (or what is left)
            if scorched:
                for _ in range(7):                                     # charred stalks, lit on the west
                    sx, sy = int(rng.uniform(ix0 + 3, ix1 - 3)), int(rng.uniform(iy0 + q(3.5), iy1 - 1))
                    hgt = q(rng.uniform(1.6, 3.2))
                    fill(a, sx, sy - hgt, sx + 1, sy, code('soot', 2))
                    fill(a, sx + 1, sy - hgt + 1, sx + 2, sy, code('soot', 0))
                    if rng.random() < 0.5:
                        fill(a, sx + 2, sy - hgt, sx + 4, sy - hgt + 1, code('soot', 0))
                for _ in range(3):                                     # embers
                    ex, ey = int(rng.uniform(ix0 + 2, ix1 - 3)), int(rng.uniform(iy0 + q(2.5), iy1 - 2))
                    fill(a, ex, ey, ex + 2, ey + 2, code('fox', 3))
                    fill(a, ex, ey, ex + 1, ey + 1, code('lamp', 4))
                    fill(a, ex + 1, ey + 2, ex + 3, ey + 3, code('soot', 0))
            elif k in (1, 2):
                for yy in np.arange(iy0 + q(3.2), iy1 - 1, q(3.0)):
                    for xx in np.arange(ix0 + q(1.6), ix1 - q(1.6), q(3.4)):
                        sx, sy = int(xx + rng.uniform(-1, 1)), int(yy)
                        fill(a, sx + 1, sy, sx + 3, sy + 1, code('earth', 1))            # its shade on the soil
                        fill(a, sx - 2, sy - 2, sx, sy - 1, code('leaf', 4))              # west leaf, lit
                        fill(a, sx - 2, sy - 1, sx, sy, code('leaf', 2))
                        fill(a, sx + 1, sy - 3, sx + 3, sy - 2, code('leaf', 4))          # east leaf, higher
                        fill(a, sx + 1, sy - 2, sx + 3, sy - 1, code('leaf', 3))
                        fill(a, sx, sy - 2, sx + 1, sy, code('leaf', 2))                  # the stem
            k += 1
    return finish(p)


def box_hd(a, x0, x1, ytop, ybot, depth, fams, rng=None, base=3.0, side=None):
    """A block from above the front: a lit top plane `depth` texels deep (its back edge brightest,
    its front arris catching the light), the front face below in mid tone darkening to the foot
    (occlusion), the east end face in shade. Returns (top, front, east) masks."""
    Y, X = grid(a)
    side = side if side is not None else max(2, q(1.4))
    box = (X >= x0) & (X < x1) & (Y >= ytop) & (Y < ybot)
    top = box & (Y < ytop + depth)
    east = box & ~top & (X >= x1 - side)
    front = box & ~top & ~east
    fy = (Y - ytop - depth) / max(1, ybot - ytop - depth)
    paint(a, top, fams, base + 1.2 - 0.5 * (X - x0) / max(1, x1 - x0) + 0.6 * (np.floor(Y) == ytop + depth - 1))
    paint(a, front, fams, base - 0.1 - 0.8 * fy + 0.5 * (X < x0 + 1))
    paint(a, east, fams, base - 1.5 - 0.6 * fy)
    return top, front, east


def flower_clump(a, cx, cy, r, rng, petal):
    """Leaves in a small dome (lit cap, dark tuck under) and flowers on it, each a few petals of one
    colour with a lit petal on the upper left and a centre."""
    Y, X = grid(a)
    for k in range(5):
        lx, ly = cx + rng.uniform(-r, r), cy + rng.uniform(-r * 0.5, r * 0.4)
        lr = r * rng.uniform(0.45, 0.7)
        d = ((X - lx) / lr) ** 2 + ((Y - ly) / (lr * 0.8)) ** 2
        m = d <= 1
        nx, ny = (X - lx) / lr, (Y - ly) / lr
        paint(a, m, ('leaf', 'leaf', 'leaf_warm'), 2.6 + 2.2 * lam(nx, ny * 0.7, np.sqrt(np.clip(1 - d, 0, 1))))
    for k in range(int(rng.integers(2, 4))):
        fx, fy = int(cx + rng.uniform(-r * 0.8, r * 0.8)), int(cy - rng.uniform(0, r * 0.6))
        # a flower of four texels by three: the petals lit on the upper left, a two-texel centre
        for (dy, dx, c) in ((0, 0, (petal, 5)), (0, 1, (petal, 5)), (0, 2, (petal, 5)), (1, 0, (petal, 5)),
                            (1, 1, ('brass_warm', 4)), (1, 2, ('brass_warm', 4)), (1, 3, (petal, 3)),
                            (2, 1, (petal, 3)), (2, 2, (petal, 3)), (2, 3, (petal, 3))):
            fill(a, fx + dx - 1, fy + dy - 1, fx + dx, fy + dy, code(*c))


def p_flower_tub_hd(w, h, seed):
    """A clay planter as a volume: its rim a lit band round the soil (the back rim's inner face in
    shade, the front rim's top catching the light), the front face with a moulded band and the
    clay's mottle, the east end in shade, a dark foot; flowers spilling over it."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=11, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    ytop = yb - q(8.2)
    top, front, east = box_hd(a, x0, x1, ytop, yb, q(3.0), ('clay_cool', 'clay', 'clay'), base=3.0)
    # the opening: soil inside the rim, the back rim's inner face shaded
    rim = q(0.9)
    soil = top & (X >= x0 + rim) & (X < x1 - rim) & (Y >= ytop + rim) & (Y < ytop + q(3.0) - rim)
    paint(a, soil, ('earth_cool', 'earth', 'earth_warm'), 1.6 + 0.8 * (np.sin(X * 1.3 + Y) > 0.4))
    a[soil & (Y < ytop + rim + 1)] = code('clay_cool', 2)
    # the moulded band and the clay's mottle on the face, chips on the arris
    band = front & (Y >= ytop + q(3.6)) & (Y < ytop + q(4.4))
    a[band] = a[band] + 1 * ((a[band] % 8) < 5)
    a[front & (np.floor(Y) == int(ytop + q(4.4)))] = code('clay', 1)
    mott = (front | east) & (ndi.gaussian_filter(rng.random(a.shape), 1.0) > 0.56)
    a[mott] = a[mott] - 1 * ((a[mott] % 8) > 1)
    for _ in range(3):
        chx = int(rng.uniform(x0 + 2, x1 - q(2)))
        fill(a, chx, int(ytop + q(3.0)), chx + 2, int(ytop + q(3.0)) + 1, code('clay', 5))
    a[(front | east) & (Y >= yb - 1)] = code('clay_cool', 1)
    for k in range(4):
        flower_clump(a, x0 + q(2) + k * (x1 - x0 - q(4)) / 3, ytop + q(0.8), q(2.0), rng,
                     ('berry', 'brass', 'plaster', 'berry')[(seed + k) % 4])
    return finish(p)


def p_hay_hd(w, h, seed):
    """A hay bale: a lit top of straw laid along it in strokes, the front face showing the cut stalk
    ends in a darker stipple of clusters, the east end in shade, two twine bands round it, loose
    straws on the ground."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    ytop = yb - q(h + 8)
    top, front, east = box_hd(a, x0, x1, ytop, yb, q(h), ('sand_cool', 'sand', 'sand_warm'), base=2.4, side=q(3))
    for _ in range(int(w * h * 2.4)):                                  # straws along the top
        sx, sy = int(rng.uniform(x0 + 1, x1 - q(3))), int(rng.uniform(ytop + 1, ytop + q(h) - 1))
        ln = q(rng.uniform(1.2, 3.0))
        sel = top & (np.floor(Y) == sy) & (X >= sx) & (X < sx + ln)
        a[sel] = code(('sand_warm', 'sand', 'sand')[int(rng.integers(0, 3))], int(rng.choice([1, 2, 4, 5])))
    for _ in range(int(w * 5)):                                        # cut ends on the face
        sx, sy = int(rng.uniform(x0 + 1, x1 - q(3))), int(rng.uniform(ytop + q(h) + 1, yb - 2))
        fill(a, sx, sy, sx + 2, sy + 1, code('sand', 2))
        fill(a, sx, sy - 1, sx + 1, sy, code('sand_warm', 4))
    for _ in range(int(h * 3)):                                        # the east end: compressed layers
        sy = int(rng.uniform(ytop + q(h), yb - 1))
        sel = east & (np.floor(Y) == sy) & (X > x1 - q(3) + int(rng.integers(0, 3)))
        a[sel] = code('sand_cool', 1)
    for xx in (x0 + q(w * 0.28), x1 - q(w * 0.34)):                    # twine round it
        tw = (X >= xx) & (X < xx + 2) & (top | front)
        a[tw] = code('timber_warm', 2)
        a[tw & (np.floor(X) == int(xx))] = code('timber_warm', 4)
    for _ in range(6):                                                 # loose straws at the foot
        sx = int(rng.uniform(x0 - q(2), x1 + q(1)))
        fill(a, sx, yb - 1, sx + q(rng.uniform(1, 2.4)), yb, code('sand_warm', 4))
    return finish(p)


def p_sacks_hd(w, h, seed, hd=False):
    """The existing three-sack group: slumped shoulders, gathered mouths and stitched seams.
    Folds converge on each tie; broad cloth planes stay quiet, with short weave clusters only
    beside the seam. Overlap shade belongs to the sacks below, never to empty ground."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=12, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    sacks = ((-0.25, 0.0, 1.0), (0.22, 0.0, 0.9), (0.0, -1.0, 0.85))
    for k, (dx, dy, s_) in enumerate(sacks):
        scx, rx, ry = cx + q(w * dx), q(4.2 * s_), q(4.6 * s_)
        scy = yb - q(5 * s_) - (q(4.0 if hd else 5.5) if dy else 0)      # (scale gate: the top sack slumps, about 40 tall)
        ny = (Y - scy) / ry
        # Narrow the shoulders inside the old radii; the weighted lower body stays broad.
        nx = (X - scx) / (rx * (1 - 0.12 * np.clip(-ny, 0, 1)))
        d = nx * nx + ny * ny
        m = d <= 1
        # Contact shade is clipped to already occupied cloth, offset down/east from this bag.
        contact = ellipse_mask(a.shape, scx + 1, scy + 2, rx + 1, ry + 1) & ~m & (a >= 0) & (Y > scy)
        _step(a, contact, -1)
        t = 2.2 + 1.8 * lam(nx, ny * 0.8, np.sqrt(np.clip(1 - d, 0, 1)))
        t -= 0.5 * (ny > 0.65)                         # the compressed, weighted foot
        paint(a, m, ('sand_cool', 'sand', 'sand_warm'), t, lo=1, hi=4)
        # Three shallow gathers: dark trough and short raised lip, not stripe texture.
        for reach in (-0.55, 0.12, 0.55):
            fx = scx + rx * reach * np.clip((ny + 1) / 1.4, 0, 1)
            fold = m & (np.abs(X - fx) < 0.65) & (ny > -0.8) & (ny < 0.25)
            lip = m & (X >= fx - 1.8) & (X < fx - 0.65) & (ny > -0.55) & (ny < -0.05)
            _step(a, fold, -1)
            _step(a, lip & (a % 8 < 4), 1)
        seam_x = scx + rx * (0.38 + 0.1 * ny * ny)
        seam = m & (np.abs(X - seam_x) < 0.65) & (ny > -0.45) & (ny < 0.78)
        _step(a, seam, -1)
        # Paired stitches and a few weave runs are attached to the seam, never a full lattice.
        for f in (-0.25, 0.05, 0.35, 0.6):
            sy = int(scy + ry * f)
            sx = int(scx + rx * (0.38 + 0.1 * f * f))
            fill(a, sx - 2, sy, sx, sy + 1, code('sand', 3), where=m)
            fill(a, sx - 2, sy + 1, sx - 1, sy + 2, code('sand', 2), where=m)
        for _ in range(2):
            sy = int(scy + ry * rng.uniform(0.1, 0.55))
            sx = int(scx - rx * rng.uniform(0.15, 0.45))
            fill(a, sx, sy, sx + 2, sy + 1, code('sand', 2), where=m)
            fill(a, sx, sy + 1, sx + 1, sy + 2, code('sand', 3), where=m)
        neck = (np.abs(X - scx) < q(1.3)) & (Y >= scy - ry - q(1.6)) & (Y < scy - ry + 1)
        paint(a, neck, ('sand_cool', 'sand', 'sand_warm'), 2.8 - 1.2 * (X > scx))
        _step(a, neck & (np.abs(X - scx + 1) < 0.6), -1)
        tie = (np.abs(X - scx) < q(1.4)) & (np.abs(Y - (scy - ry)) < 1)
        a[tie] = code('timber', 1)
        a[tie & (Y < scy - ry)] = code('timber_warm', 3)
        blob(a, ellipse_mask(a.shape, scx + 1, scy - ry, 1.5, 1), 'timber_warm', 2)
        bar(a, scx, scy - ry + 1, scx - 2, scy - ry + 4, 0.8, 'timber', 2, where=m)
    return finish(p)


def p_bench_hd(w, h, seed):
    """A bench at a person's scale (the size guide: the seat knee high, 7 world px, the back 13), as
    a joined frame (#288 review S4): square legs (a lit west face, a dark east face), the back posts
    running down behind the seat into the rear legs, a stretcher between the front legs, the seat
    of three planks seen from above with a gap between, its front edge showing its thickness and
    the shade under it, the west end grain lit and the east end cap in shade, a contact shade at
    each foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=13, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    tf = ('timber_cool', 'timber', 'timber_warm')
    lw = q(1.6)                                                        # a leg's width
    lf = max(1, q(0.55))                                               # its lit west face

    def leg(px, top, bot, base):
        m = (X >= px) & (X < px + lw) & (Y >= top) & (Y < bot)
        t = np.where(X < px + lf, base + 1.2, np.where(X >= px + lw - lf, base - 1.0, base))
        paint(a, m, tf, t - 0.8 * (Y >= bot - q(0.6)))
        foot = (X >= px - 1) & (X < px + lw + 1) & (Y >= bot) & (Y < bot + 1) & (a < 0)
        a[foot] = code('earth_cool', 1)                                # contact shade
    yseat = yb - q(8.4)
    ysb = yseat + 3 * q(1.3) + q(1.2)                                  # the seat's underside
    pxs = (x0 + q(1.6), x1 - q(1.6) - lw)
    for px in pxs:                                                     # rear legs (in the seat's shade)
        leg(px + q(0.6), ysb, yb - q(1.4), 1.8)
    for px in pxs:                                                     # back posts
        post = (X >= px + q(0.6)) & (X < px + q(0.6) + lw) & (Y >= yb - q(13)) & (Y < yseat)
        paint(a, post, tf, np.where(X < px + q(0.6) + lf, 4.0, np.where(X >= px + q(0.6) + lw - lf, 2.0, 3.0))
              + 0.6 * (Y < yb - q(12.4)))
    for ry_ in (yb - q(12.6), yb - q(10.2)):                           # back rails
        board(a, x0 + q(0.5), ry_, x1 - x0 - q(1), q(1.6), 0, 'timber_warm', 4, rng, split=False)
        a[(X >= x1 - q(1.0)) & (X < x1 - q(0.5)) & (Y >= ry_) & (Y < ry_ + q(1.6))] = code('timber_cool', 1)
        sh = (X >= x0) & (X < x1) & (Y >= ry_ + q(1.6)) & (Y < ry_ + q(1.6) + 2) & (a >= 0)
        a[sh] = a[sh] - 1 * ((a[sh] % 8) > 0)
    yy = yseat                                                         # the seat: three planks from above
    a[(X >= x0) & (X < x1) & (Y >= yy) & (Y < yy + 3 * q(1.3) + 2)] = code('timber', 0)
    for k in range(3):
        th = q(1.3)
        board(a, x0, yy, x1 - x0, th - 1, 0, ('timber_warm', 'timber_warm', 'timber')[k], (5, 4, 4)[k], rng, split=k == 1)
        yy += th
    edge = (X >= x0) & (X < x1) & (Y >= yy) & (Y < yy + q(1.2))
    paint(a, edge, tf, 2.6 + 0.8 * (Y < yy + 1))
    # the end grain: lit at the west end, the east end cap in shade (its far arris a touch lighter)
    ew = q(1.0)
    endw = (X >= x0) & (X < x0 + ew) & (Y >= yseat) & (Y < yy + q(1.2))
    paint(a, endw, ('timber_warm', 'timber_warm', 'timber_warm'), 4.6 - 0.8 * (Y >= yy))
    ende = (X >= x1 - ew) & (X < x1) & (Y >= yseat) & (Y < yy + q(1.2))
    paint(a, ende, tf, 1.2 + 0.6 * (Y < yseat + 1))
    # the shade under the seat, then the front legs and the stretcher between them
    sh = (X >= x0) & (X < x1) & (Y >= yy + q(1.2)) & (Y < yy + q(2.2)) & (a >= 0)
    a[sh] = a[sh] - 2 * ((a[sh] % 8) > 1)
    for px in pxs:
        leg(px - q(0.3), yy + q(1.2), yb, 2.8)
    sy = yb - q(2.6)
    st = (X >= pxs[0] + lw - q(0.3)) & (X < pxs[1] - q(0.3)) & (Y >= sy) & (Y < sy + q(1.0))
    paint(a, st, tf, np.where(Y < sy + 1, 3.6, 2.4))
    ss = (X >= pxs[0] + lw - q(0.3)) & (X < pxs[1] - q(0.3)) & (Y >= sy + q(1.0)) & (Y < sy + q(1.0) + 1) & (a >= 0)
    a[ss] = a[ss] - 1 * ((a[ss] % 8) > 0)
    # the story of use: nail heads where each plank crosses a leg (a dark head, its lit west
    # side), pegs through the back rails into the posts, grain down the legs, two seat patches
    # worn pale and a dark knock on the front edge
    yk = yseat
    for k in range(3):
        for px in pxs:
            nx_ = int(px + lw / 2)
            fill(a, nx_, int(yk + 1), nx_ + 2, int(yk + 2), code('iron', 1))
            fill(a, nx_, int(yk + 1), nx_ + 1, int(yk + 2), code('iron', 3))
        yk += q(1.3)
    for ry_ in (yb - q(12.6), yb - q(10.2)):
        for px in pxs:
            gx = int(px + q(0.6) + lw / 2 - 1)
            fill(a, gx, int(ry_ + 1), gx + 2, int(ry_ + 3), code('timber_cool', 2))
            fill(a, gx, int(ry_ + 1), gx + 1, int(ry_ + 2), code('timber_warm', 5))
    for px in pxs:
        for gx in (px - q(0.3) + lf + 1, px - q(0.3) + lw - lf - 2):
            gy = int(yy + q(1.2) + rng.integers(1, 4))
            fill(a, int(gx), gy, int(gx) + 1, gy + int(rng.integers(3, 6)), code('timber_cool', 2))
    for sx_ in (x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.66):
        wm = ((X - sx_) / q(2.6)) ** 2 + ((Y - yseat - q(1.6)) / q(1.2)) ** 2 <= 1
        wm &= (a % 8 >= 3) & (a % 8 <= 4) & (rng.random(a.shape) < 0.55)
        a[wm] = a[wm] + 1
    kx = int(x0 + (x1 - x0) * rng.uniform(0.4, 0.6))
    fill(a, kx, int(yy), kx + 3, int(yy + 2), code('timber_cool', 1))
    fill(a, kx, int(yy), kx + 1, int(yy + 1), code('timber_warm', 4))
    return finish(p)


def p_grindstone_hd(w, h, seed):
    """A treadle grindstone with its wheel edge on (#288 review S3: a wheel drawn face on with the
    axle across its face cannot turn): the axle runs east to west through bearing blocks on the
    trestle, the sandstone wheel hangs between them as a thick disc seen across its tread, the tread
    a horizontal cylinder (its top arc lit, the lower curve falling into shade, a bounce at the
    foot), the wheel's west face a narrow lit ellipse with the hub boss and the iron collar, the
    crank on the east end, the treadle and its rod, the water pot dripping on the tread."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=20, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    tf = ('timber_cool', 'timber', 'timber_warm')
    # the trestle: splayed legs, square in section (a lit west face, a dark east face)
    for lx in (cx - q(6), cx + q(5)):
        for sx in (-1, 1):
            bar(a, lx + sx * q(1.6), yb - 1, lx, yb - q(9), max(1.4, q(0.8)), 'timber', 3 if sx < 0 else 2)
    prism(a, cx - q(8), yb - q(10.5), cx + q(8), yb - q(8.5), q(0.7), 'timber_warm', 3, side=q(0.8))
    board(a, cx - q(7), yb - q(2.4), q(12), q(1.8), -6, 'timber', 3, rng, split=False)
    wcx, wcy, R = cx - q(0.5), yb - q(14), q(5.5)
    T = q(3.6)                                   # the tread's width (the wheel's thickness)
    fw = q(1.3)                                  # the west face's half width (seen a little from the west)
    tx0 = wcx - T / 2 + fw * 0.5
    tx1 = tx0 + T
    # contact shade on the trestle under the wheel
    cs = (X >= tx0 - fw) & (X < tx1 + 1) & (Y >= wcy + R) & (Y < wcy + R + q(0.8)) & (a >= 0)
    a[cs] = a[cs] - 1 * ((a[cs] % 8) > 0)
    # the axle behind the wheel, through both bearings
    a[_rect(a.shape, wcx - q(8), wcy - 1, wcx + q(7.5), wcy + 2)] = code('iron', 2)
    a[_rect(a.shape, wcx - q(8), wcy - 1, wcx + q(7.5), wcy)] = code('iron', 4)
    # the tread: rounded at top and bottom (the disc's silhouette across its rim), a horizontal
    # cylinder in the light
    v = (Y - wcy) / R
    tread = (X >= tx0) & (X < tx1) & (np.abs(v) <= 1)
    cz = np.sqrt(np.clip(1 - v * v, 0, 1))
    ex_ = (X - tx0) / max(1, T)                  # across the tread: its arrises catch / lose light
    I = lam(0.0, cz * 0.95 - 0.0, -v * 0.95)
    t = 2.8 + 2.7 * I + 0.5 * (ex_ < 0.18) - 0.6 * (ex_ > 0.82) + 0.6 * (v > 0.82)
    paint(a, tread, ('stone_cool', 'stone_warm', 'stone_warm'), t, lo=1, hi=5)
    # grit and the wear of the tool: a polished lit band across the upper tread, pits
    pit = tread & (rng.random(a.shape) < 0.14) & (a % 8 >= 2)
    a[pit] = a[pit] - 1
    pol = tread & (np.abs(v + 0.45) < 0.06) & (a % 8 <= 4)
    a[pol] = a[pol] + 1
    # the west face: a narrow ellipse, lit (it faces the light), its rim chamfer brighter, the hub
    face = ((X - tx0) / fw) ** 2 + v ** 2 <= 1
    face &= X < tx0 + 0.5
    rr_ = np.hypot((X - tx0) / fw, v)
    paint(a, face, ('stone_cool', 'stone_warm', 'stone_warm'), 3.6 + 0.8 * (rr_ > 0.82) - 0.7 * (v > 0.55)
          + 0.4 * (v < -0.5), lo=1, hi=5)
    ring = face & (np.abs(rr_ - 0.6) < 0.08)
    a[ring] = a[ring] - 1
    hub = ((X - tx0) / (fw * 0.55)) ** 2 + ((Y - wcy) / q(1.3)) ** 2 <= 1
    blob(a, hub, 'iron', 3)
    a[hub & (Y < wcy - q(0.4))] = code('iron', 4)
    a[hub & (Y > wcy + q(0.5))] = code('iron', 1)
    # the bearing blocks and their uprights, the crank on the east end of the axle
    for bx_ in (cx - q(7.4), cx + q(4.6)):
        prism(a, bx_, wcy - q(1.4), bx_ + q(2.6), wcy + q(1.8), q(0.6), 'timber_cool', 3, side=q(0.8))
        bar(a, bx_ + q(1.3), wcy + q(1.8), bx_ + q(1.3), yb - q(10.5), max(1.2, q(0.6)), 'timber', 2)
    pin = (wcx + q(7.5), wcy + q(2.5))
    bar(a, cx + q(4), yb - q(3), pin[0], pin[1], max(1.0, q(0.45)), 'iron', 2)
    bar(a, wcx + q(7.5), wcy, pin[0], pin[1], max(1.0, q(0.5)), 'iron', 3)
    blob(a, ellipse_mask(a.shape, pin[0], pin[1], q(0.8), q(0.8)), 'iron', 4)
    # the water pot on its bracket over the tread, dripping on it
    bx_, by_ = cx - q(7.4) + q(1.3), wcy - R - q(4)
    bar(a, bx_, wcy - q(1.4), bx_, by_, max(1.0, q(0.45)), 'iron', 2)
    px_ = (tx0 + tx1) / 2
    bar(a, bx_, by_, px_, by_, max(1.0, q(0.45)), 'iron', 3)
    pot = ellipse_mask(a.shape, px_, by_ + q(1.8), q(1.8), q(1.6))
    up_ = (X - px_) / q(1.8)
    a[pot] = FI['clay'] * 8 + np.clip(cyl_tones(up_, 3), 0, 5)[pot]
    a[_rect(a.shape, px_, by_ + q(3.4), px_ + 1, wcy - R + 1)] = code('water', 4)
    wet = tread & (v < -0.7) & (np.abs(X - px_) < q(0.9))
    a[wet] = code('stone_cool', 2)
    return finish(p)


def p_bench_side_hd(w, h, seed, facing='east'):
    """The house bench turned side on (Matt, 26 Oct: benches face the well), its sitter looking
    `facing` (east or west): in our oblique view a plane running north to south shows only its
    top, so the seat is three planks seen from above running north to south, the back a narrow
    rail standing up along the far side (its top arris lit), the posts rising above the seat at
    each end, and only the south end shows its height: the seat's end grain, the two south legs
    and the stretcher between them. Lit from the west whichever way it faces."""
    rng = np.random.default_rng(seed)
    L, dep = 18.0, 6.0                                                 # world px: length (north-south), depth
    p = _pic(dep, L, up=13, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    tf = ('timber_cool', 'timber', 'timber_warm')
    x0, x1 = cx - q(dep / 2), cx + q(dep / 2)
    bw = q(1.4)                                                        # the back rail's width
    back_w = facing == 'east'                                          # the back on the west side
    bx0 = x0 if back_w else x1 - bw
    sx0, sx1 = (x0 + bw - 1, x1) if back_w else (x0, x1 - bw + 1)     # the seat under the back's foot
    yN = yb - q(L)
    zs, zb = q(7), q(13)
    ys0, ys1 = yN - zs, yb - zs                                        # the seat's top plane on screen
    th = q(1.2)                                                        # the seat's thickness
    lw = q(1.5)

    def leg(px, top, base):
        m = (X >= px) & (X < px + lw) & (Y >= top) & (Y < yb)
        t = np.where(X < px + max(1, q(0.5)), base + 1.2, np.where(X >= px + lw - max(1, q(0.5)), base - 1.0, base))
        paint(a, m, tf, t - 0.8 * (Y >= yb - q(0.6)))
    # the far (north) post shows above the seat; the back rail runs along the seat's far side
    post = (X >= bx0) & (X < bx0 + bw)
    paint(a, post & (Y >= yN - zb) & (Y < ys0 + 1), tf, np.where(X < bx0 + 1, 4.0, 2.6))
    # the seat: three planks from above, a dark gap between, the end grain lit at the south end
    a[(X >= sx0) & (X < sx1) & (Y >= ys0) & (Y < ys1)] = code('timber', 0)
    pw = (sx1 - sx0) / 3.0
    for k in range(3):
        px0 = int(round(sx0 + k * pw))
        px1 = int(round(sx0 + (k + 1) * pw)) - (1 if k < 2 else 0)
        m = (X >= px0) & (X < px1) & (Y >= ys0) & (Y < ys1)
        base = (5.0, 4.4, 4.0)[k] if back_w else (4.6, 4.2, 3.6)[k]
        t = np.full(a.shape, base)
        t = np.where(X == px0, base + 0.6, t)                          # a lit west arris
        t = np.where(X == px1 - 1, base - 1.2, t)
        t = np.where(Y < ys0 + 2, base + 0.4, t)                       # the sawn north end
        # grain: short runs along the plank
        gr = (np.abs(X - (px0 + px1) / 2.0) < 0.6) & ((((Y - ys0) // max(4, q(3))) + k) % 3 == 0)
        t = np.where(gr, t - 1.0, t)
        paint(a, m, ('timber_warm', 'timber_warm', 'timber_warm') if k == (0 if back_w else 2) else tf, t)
    # the seat's south end: its end grain (lit) and the shade under it
    endm = (X >= sx0) & (X < sx1) & (Y >= ys1) & (Y < ys1 + th)
    paint(a, endm, tf, np.where(Y < ys1 + 1, 3.8, 3.0) + 0.6 * (X < sx0 + q(1.0)))
    # the back rail: its top seen from above along the far side, the rear post running down to the
    # ground at the south end (the back stands in front of nothing: it shows as one upright band)
    rail = post & (Y >= yN - zb) & (Y < ys1 - (zb - zs) + q(1.6))
    paint(a, rail, tf, np.where(X < bx0 + 1, 4.4, np.where(X >= bx0 + bw - 1, 2.2, 3.4)))
    a[rail & (Y >= yN - zb) & (Y < yN - zb + 1)] = code('timber_warm', 5)
    for ry in (yN - zb + q(2.4), ys1 - (zb - zs) - q(1.2)):            # pegs where the rails meet the posts
        fill(a, bx0 + bw // 2 - 1, int(ry), bx0 + bw // 2 + 1, int(ry) + 2, code('timber_cool', 2))
    rpost = post & (Y >= ys1 - (zb - zs)) & (Y < yb)
    paint(a, rpost, tf, np.where(X < bx0 + 1, 3.8, 2.4) - 0.8 * (Y >= yb - q(0.6)))
    # the front south leg under the seat's outer edge, then the stretcher to the rear post
    fx = sx1 - lw if back_w else sx0
    leg(fx, ys1 + th, 2.8)
    sy = yb - q(2.6)
    lo, hi = (bx0 + bw, fx) if back_w else (fx + lw, bx0)
    st = (X >= lo) & (X < hi) & (Y >= sy) & (Y < sy + q(1.0))
    paint(a, st, tf, np.where(Y < sy + 1, 3.6, 2.4))
    sh = (X >= sx0) & (X < sx1) & (Y >= ys1 + th) & (Y < ys1 + th + q(1.0)) & (a >= 0)
    a[sh] = a[sh] - 2 * ((a[sh] % 8) > 1)
    for px in (fx, bx0):                                               # contact shade at the south feet
        foot = (X >= px - 1) & (X < px + lw + 1) & (Y >= yb) & (Y < yb + 1) & (a < 0)
        a[foot] = code('earth_cool', 1)
    # the story of use: nail heads where the planks cross the end bearers, a seat patch worn pale
    for yk in (ys0 + q(1.6), ys1 - q(1.8)):
        for k in range(3):
            nx_ = int(sx0 + (k + 0.5) * pw)
            fill(a, nx_, int(yk), nx_ + 2, int(yk) + 2, code('iron', 1))
            fill(a, nx_, int(yk), nx_ + 1, int(yk) + 1, code('iron', 3))
    sx_ = (sx0 + sx1) / 2.0
    for sy_ in (ys0 + (ys1 - ys0) * 0.32, ys0 + (ys1 - ys0) * 0.68):
        wm = ((X - sx_) / q(1.4)) ** 2 + ((Y - sy_) / q(2.6)) ** 2 <= 1
        wm &= (a % 8 >= 3) & (a % 8 <= 4) & (rng.random(a.shape) < 0.55) & (Y >= ys0) & (Y < ys1)
        a[wm] = a[wm] + 1
    return finish(p)


PROPS_HD = {
    'barrel': p_barrel_hd,
    'anvil': p_anvil_hd,
    'beds': lambda w, h, s: p_beds_hd(w, h, s, scorched=True),
    'beds_dug': lambda w, h, s: p_beds_hd(w, h, s, scorched=False),
    'flower_tub': p_flower_tub_hd,
    'hay': p_hay_hd,
    'sacks': p_sacks_hd,
    'bench': p_bench_hd,
    'bench_side_e': lambda w, h, s: p_bench_side_hd(w, h, s, facing='east'),
    'bench_side_w': lambda w, h, s: p_bench_side_hd(w, h, s, facing='west'),
    'grindstone': p_grindstone_hd,
}
