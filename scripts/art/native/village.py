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

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import ctx
from .palette import FI, to_rgba

D = ctx.D


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


def blk(a, x0, y0, x1, y1, fam, t, cut=1, top=1, left=1, bot=-1, right=-1, where=None):
    """A block (stone, slate, plank, board) with chamfered corners, lit from the upper left."""
    w, h = int(x1 - x0), int(y1 - y0)
    if w < 1 or h < 1:
        return
    m = chamfer(h, w, cut if (w > 2 * cut and h > 2 * cut) else 0)
    put(a, int(x0), int(y0), m, fam, shade(m, t, top, left, bot, right), where)


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
           moss=0.18, east_dark=True, where=None, mortar=('stone', 1)):
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
                    cut=1 if h < q(3.5) else 2, where=where)
                if moss and y > y1 - (y1 - y0) * 0.45 and rng.random() < moss:
                    mx = int(rng.integers(sx0, max(sx0 + 1, sx1 - 2)))
                    mw = int(rng.integers(2, 5))
                    fill(a, mx, yt, mx + mw, yt + 2, code('leaf', 3 + int(rng.integers(0, 2))), where)
            x += L
        y = yt
        k += 1


def ashlar(a, x0, y0, x1, y1, rng, base=3, course=4.0, length=(7, 11), where=None):
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
                blk(a, sx0, yt, sx1, y - 1, ('ashlar', 'ashlar_warm', 'ashlar')[int(rng.integers(0, 3))], t, cut=1,
                    where=where)
            x += L
        y = yt
        k += 1


def planks(a, x0, y0, x1, y1, rng, fams=TIMBER, base=3, width=3.0, vertical=True, grain=True, where=None):
    """Boards side by side with dark seams; each board its own tone, grain dashes and a knot."""
    fill(a, x0, y0, x1, y1, code(fams[0], 1), where)
    if vertical:
        x = x0
        while x < x1:
            w = max(3, q(width * rng.uniform(0.85, 1.15)))
            t = base + int(rng.choice([-1, 0, 0, 1]))
            f = fams[int(rng.integers(0, len(fams)))]
            blk(a, x, y0, min(x + w - 1, x1), y1, f, t, cut=0, top=0, where=where)
            if grain:
                for _ in range(max(1, (y1 - y0) // q(6))):
                    gx = int(rng.integers(x + 1, max(x + 2, x + w - 2)))
                    gy = int(rng.integers(y0, max(y0 + 1, y1 - 4)))
                    fill(a, gx, gy, gx + 1, gy + q(rng.uniform(2, 4)), code(f, max(0, t - 1)), where)
            x += w
    else:
        y = y0
        while y < y1:
            h = max(3, q(width * rng.uniform(0.85, 1.15)))
            t = base + int(rng.choice([-1, 0, 0, 1]))
            f = fams[int(rng.integers(0, len(fams)))]
            blk(a, x0, y, x1, min(y + h - 1, y1), f, t, cut=0, left=0, where=where)
            if grain:
                for _ in range(max(1, (x1 - x0) // q(7))):
                    gy = int(rng.integers(y + 1, max(y + 2, y + h - 2)))
                    gx = int(rng.integers(x0, max(x0 + 1, x1 - 6)))
                    fill(a, gx, gy, gx + q(rng.uniform(2, 5)), gy + 1, code(f, max(0, t - 1)), where)
            y += h


def beam(a, x0, y0, x1, y1, rng, fam='timber', t=2, where=None):
    """A timber beam or post: lit top and west, dark foot, grain dashes along its length."""
    blk(a, x0, y0, x1, y1, fam, t, cut=0, where=where)
    w, h = x1 - x0, y1 - y0
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


def plaster(a, x0, y0, x1, y1, rng, fam='plaster', base=3, where=None):
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
               moss=0, east_dark=False, where=where)


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


def slate_roof(a, m, x0, x1, y_ridge, y_eave, rng, row=3.2, width=(4.2, 6.4), fams=SLATES, moss=0.06, patch=0.05):
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
        blk(a, x, y_ridge, min(x + w - 1, x1), y_ridge + rc, 'clay', 2 if (x - x0) / span > 0.6 else 3, cut=1, where=m)
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


def shingle_roof(a, m, x0, x1, y_ridge, y_eave, rng):
    """Cedar shingles: like slates but warm timber, shorter rows."""
    slate_roof(a, m, x0, x1, y_ridge, y_eave, rng, row=2.8, width=(3.4, 5.0), fams=('timber_warm', 'timber', 'timber_cool'),
               moss=0.1)


def hip_planes(a, x0, x1, y_ridge, y_eave, hip, cap='clay'):
    """A hipped roof's end slopes: the west one turned to the light a tone up, the east one a
    tone down, a capped hip line from each eave corner to the ridge's end."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    f = np.clip((y_eave - Y) / max(1, (y_eave - y_ridge)), 0, 1)
    inside = (Y >= y_ridge) & (Y < y_eave) & (a >= 0)
    west = inside & (X < x0 + hip * f)
    east = inside & (X >= x1 - hip * f)
    for m, d in ((west, 1), (east, -1)):
        t = a[m] % 8
        ok = t < 6
        v = a[m]
        v[ok] = (v[ok] // 8) * 8 + np.clip(t[ok] + d, 0, 5)
        a[m] = v
    for side in (-1, 1):
        xa = x0 if side < 0 else x1
        xb = x0 + hip if side < 0 else x1 - hip
        bar(a, xa, y_eave - 1, xb, y_ridge + 2, max(1.2, D * 0.7), cap, 3 if side < 0 else 2, where=a >= 0)


def fascia(a, x0, x1, y, rng, fam='timber'):
    """The eave board along the roof's foot, and the shade it throws on the wall below."""
    beam(a, x0, y, x1, y + max(3, q(1.8)), rng, fam, 2)


# ------------------------------------------------------------------------------------------------
# openings and fittings
# ------------------------------------------------------------------------------------------------
def door(a, cx, yb, w, h, paint, rng, frame='stone', arch=False, open_=False):
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
                blk(a, sx0, max(y0 - fr, y - hh), sx1 - 1, y - 1, STONES[k % 3], 3 if sx0 < cx else 2, cut=1)
            y -= hh
            k += 1
        blk(a, x0 - fr - q(1), y0 - fr - q(1), x1 + fr + q(1), y0, 'stone_warm', 4, cut=1)
    else:
        beam(a, x0 - fr, y0, x0, yb, rng, 'timber', 2)
        beam(a, x1, y0, x1 + fr, yb, rng, 'timber', 2)
        beam(a, x0 - fr - q(1.5), y0 - fr, x1 + fr + q(1.5), y0, rng, 'timber', 3)
    lm = _rect(a.shape, x0, y0, x1, yb)
    if arch:
        r = (x1 - x0) / 2
        Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
        lm &= ~((Y < y0 + r) & (((X - cx) / r) ** 2 + ((Y - y0 - r) / r) ** 2 > 1))
    if open_:
        fill(a, x0, y0, x1, yb, code('soot', 1), lm)
        fill(a, x0, yb - q(3), x1, yb, code('soot', 2), lm)
        return
    planks(a, x0, y0, x1, yb, rng, fams=(paint, paint, paint + '_cool' if paint + '_cool' in FI else paint), base=3,
           width=w / 4.0, grain=True, where=lm)
    # ledges and a brace
    for yy in (y0 + q(5), yb - q(8)):
        blk(a, x0 + 1, yy, x1 - 1, yy + q(2), paint, 4, cut=0, where=lm)
    # hinges and latch
    for yy in (y0 + q(5.5), yb - q(7.5)):
        fill(a, x0, yy, x0 + q(w * 0.45), yy + max(2, q(0.9)), code('iron', 2), lm)
        fill(a, x0, yy, x0 + q(w * 0.45), yy + 1, code('iron', 3), lm)
    lx, ly = x1 - q(3.2), y0 + Hd // 2
    blk(a, lx, ly, lx + max(3, q(1.6)), ly + max(3, q(1.6)), 'brass', 4, cut=0)
    # the step
    blk(a, x0 - fr, yb - max(3, q(1.6)), x1 + fr, yb + 1, 'stone_warm', 3, cut=1)


def window(a, cx, yt, w, h, paint, rng, lit=False, shutters=True, box=False, frame_fam=None, cols=2, rows=2,
           sill='stone', lintel='timber'):
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
        beam(a, x0 - q(2), y0 - q(2.4), x1 + q(2), y0, rng, 'timber', 2)
    else:
        blk(a, x0 - q(2), y0 - q(2.6), x1 + q(2), y0, 'stone_warm', 4, cut=1)
    # frame and panes
    blk(a, x0, y0, x1, y1, ff, 4, cut=0)
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
    if box:
        by0 = y1 + max(3, q(2.0))
        blk(a, x0 - q(1), by0, x1 + q(1), by0 + q(3.5), 'timber', 3, cut=1)
        for k in range(int((x1 - x0) / q(2.6)) + 1):
            fx = x0 + k * q(2.6) + int(rng.integers(-1, 2))
            blob(a, ellipse_mask(a.shape, fx + q(1.2), by0 - q(0.4), q(1.6), q(1.4)), 'leaf', 3 + (k % 2))
            if k % 2 == 0:
                fill(a, fx + 1, by0 - q(1.6), fx + 3, by0 - q(1.6) + 2, code(('berry', 'brass', 'dusk')[k % 3], 4))


def chimney(a, x0, x1, y_top, y_bot, rng, pot=True):
    """A stone stack: courses, a lit cap slab, soot round the flue, a clay pot."""
    rubble(a, x0, y_top, x1, y_bot, rng, base=3, course=(2.2, 3.0), length=(3, 6), moss=0.0)
    blk(a, x0 - q(1), y_top - q(2.2), x1 + q(1), y_top, 'stone_warm', 4, cut=1)
    fill(a, x0, y_top, x1, y_top + q(2.5), code('soot', 2), a >= 0)
    if pot:
        cx = (x0 + x1) // 2
        blk(a, cx - q(2), y_top - q(5.5), cx + q(2), y_top - q(2.2), 'clay', 3, cut=1)
        fill(a, cx - q(1.2), y_top - q(5.5), cx + q(1.2), y_top - q(4.6), code('soot', 0))


def sign(a, x, y, kind, rng, fam='timber'):
    """A hanging sign on an iron bracket: a board with the trade's mark (bread, leaf, book)."""
    bar(a, x, y, x + q(9), y, max(1, q(0.6)), 'iron', 2)
    bar(a, x + q(1), y + q(4), x + q(5), y, max(1, q(0.5)), 'iron', 2)
    bx0, by0 = x + q(2), y + q(2)
    for k in (0, 1):
        fill(a, bx0 + q(1) + k * q(5), y, bx0 + q(1) + k * q(5) + 1, by0, code('iron', 1))
    blk(a, bx0, by0, bx0 + q(8), by0 + q(7), fam, 3, cut=1)
    cx, cy = bx0 + q(4), by0 + q(3.5)
    if kind == 'bread':
        blob(a, ellipse_mask(a.shape, cx, cy, q(2.6), q(1.6)), 'brass', 4)
        for k in (-1, 0, 1):
            fill(a, cx + k * q(1.2), cy - q(0.6), cx + k * q(1.2) + 1, cy + q(0.6), code('brass', 2))
    elif kind == 'leaf':
        blob(a, ellipse_mask(a.shape, cx, cy, q(1.6), q(2.4)), 'leaf', 4)
        fill(a, cx, cy - q(2), cx + 1, cy + q(2.4), code('leaf', 2))
    elif kind == 'book':
        blk(a, cx - q(2.4), cy - q(1.8), cx, cy + q(1.8), 'berry', 3, cut=0)
        blk(a, cx, cy - q(1.8), cx + q(2.4), cy + q(1.8), 'berry', 4, cut=0)
        fill(a, cx, cy - q(1.8), cx + 1, cy + q(1.8), code('plaster', 5))
    elif kind == 'hammer':
        bar(a, cx - q(2), cy + q(2), cx + q(1.5), cy - q(1.5), max(1, q(0.5)), 'timber_warm', 4)
        blk(a, cx, cy - q(2.6), cx + q(2.6), cy - q(0.8), 'iron', 4, cut=0)


# ------------------------------------------------------------------------------------------------
# buildings
# ------------------------------------------------------------------------------------------------
@dataclass
class Built:
    base: Pic
    damage: Pic | None
    info: dict = field(default_factory=dict)


def building(spec: dict, seed: int = 0) -> Built:
    """A building from its look (plan data): w x depth world px footprint, a front wall wall_h
    tall, a roof roof_h tall over it. Keys: kind (cottage, terrace, library, forge, hut), wall
    (stone, frame, ashlar, boards), roof (slate, thatch, shingle), hip, paint (a house family), door
    (x from the west end, world px; 'open' for the forge mouth), windows ([x, ...]), lit, chimney
    ([x, ...]), sign ([x, kind]), units (a terrace: [[x0, x1, paint], ...]), damage (a list of
    what the storm did: holes, tarp, boards, scaffold, slates, crack)."""
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
        rubble(a, L, y_e, R, B, rng)
    elif wall == 'ashlar':
        ashlar(a, L, y_e, R, B, rng)
        rubble(a, L, B - plinth, R, B, rng, base=2, course=(2.4, 2.8), length=(5, 9), moss=0.25)
    elif wall == 'boards':
        planks(a, L, y_e, R, B - plinth, rng, base=3, width=3.2, vertical=False)
        rubble(a, L, B - plinth, R, B, rng, base=3, course=(2.2, 2.8), length=(4, 7))
    else:   # frame: a stone ground course, timber framing, plaster panels
        sill_y = B - q(spec.get('frame_rail', 17))
        rubble(a, L, sill_y, R, B, rng)
        plaster(a, L, y_e, R, sill_y, rng)
        posts = sorted(set([L, R - q(3)] + [L + q(x) for x in spec.get('posts', [])]))
        beam(a, L, sill_y - q(2.4), R, sill_y, rng, 'timber', 2)
        for x in posts:
            beam(a, x, y_e, x + q(3), sill_y, rng, 'timber', 2 if x > (L + R) / 2 else 3)
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
            blk(a, L, max(y_e, y - hh), L + ww, y - 1, 'stone_warm', 4, cut=1)
            blk(a, R - ww, max(y_e, y - hh), R, y - 1, 'stone_warm', 2, cut=1)
            y -= hh
            k += 1
    # the shade under the eave
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
                       lintel='stone' if wall == 'ashlar' else 'timber')
    doors = spec.get('doors', [[spec['door'], paint]] if 'door' in spec else [])
    for (dx, dpaint) in doors:
        if spec.get('kind') == 'forge':
            continue
        door(a, L + q(dx), B, spec.get('door_w', 16), spec.get('door_h', 31), dpaint, rng,
             frame='stone' if wall in ('stone', 'ashlar') else 'timber', arch=spec.get('arch', False))
    if spec.get('kind') == 'forge':
        mouth(a, L + q(spec['door']), B, spec.get('mouth_w', 30), spec.get('mouth_h', 27), rng)
        info['mouth'] = (L + q(spec['door']), B, q(spec.get('mouth_w', 30)), q(spec.get('mouth_h', 27)))
    if spec.get('sign'):
        sx, kind = spec['sign']
        sign(a, L + q(sx), y_e + q(5), kind, rng)

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
            hip_planes(a, rx0, rx1, y_r + q(4), y_e + q(4), hip, cap='sand')
    elif roof == 'shingle':
        shingle_roof(a, rm, rx0, rx1, y_r, y_e + q(1.5), rng)
        fascia(a, rx0, rx1, y_e, rng)
        if hip:
            hip_planes(a, rx0, rx1, y_r + q(2), y_e + q(1.5), hip)
    else:
        slate_roof(a, rm, rx0, rx1, y_r, y_e + q(1.5), rng)
        if hip:
            hip_planes(a, rx0, rx1, y_r + q(2), y_e + q(1.5), hip)
        fascia(a, rx0, rx1, y_e, rng)
    if not hip and roof != 'thatch':
        # barge boards down the gable ends
        for xx, t in ((rx0, 3), (rx1 - q(2), 2)):
            beam(a, xx, y_r, xx + q(2), y_e + q(3), rng, 'timber', t)
    info['roof'] = rm
    info['rx'] = (rx0, rx1)
    for cx in spec.get('chimney', []) or []:
        cw = q(spec.get('chimney_w', 9))
        x0 = L + q(cx) - cw // 2
        chimney(a, x0, x0 + cw, y_r - q(chim), y_r + q(roof_h * 0.45), rng)
    finish(p)

    # the damage --------------------------------------------------------------------------------
    dmg = None
    if spec.get('damage'):
        dmg = Pic(W, H, p.ax, p.ay)
        damage(dmg.a, a, spec, info, rng)
        finish(dmg)
        if not dmg.alpha().any():
            dmg = None
    return Built(p, dmg, info)


def mouth(a, cx, yb, w, h, rng):
    """The forge's mouth: a wide opening under an oak lintel, the hearth inside (brick, a hood,
    the bellows' nozzle), its floor of cinders."""
    W2, Hh = q(w), q(h)
    x0, x1 = int(cx - W2 / 2), int(cx + W2 / 2)
    y0 = yb - Hh
    fill(a, x0, y0, x1, yb, code('soot', 1))
    fill(a, x0, y0, x1, y0 + q(4), code('soot', 0))
    # the hearth at the back: a brick block with a hood above
    hx0, hx1 = x0 + q(w * 0.28), x1 - q(w * 0.18)
    rubble(a, hx0, yb - q(11), hx1, yb - q(1), rng, fams=('clay', 'clay', 'clay_cool'), base=2, course=(2.0, 2.2),
           length=(3, 4.5), moss=0, east_dark=False)
    hood = _rect(a.shape, hx0 - q(1), y0 + q(4), hx1 + q(1), yb - q(14))
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    hood &= np.abs(X - (hx0 + hx1) / 2) < (hx1 - hx0) / 2 * (0.45 + 0.55 * (Y - y0) / max(1, Hh * 0.5))
    a[hood] = code('iron', 1)
    a[hood & (X < (hx0 + hx1) / 2 - q(2))] = code('iron', 2)
    # the bellows on the west side
    blob(a, ellipse_mask(a.shape, x0 + q(5), yb - q(8), q(3.5), q(2.4)), 'timber_cool', 2)
    fill(a, x0 + q(8), yb - q(8.5), hx0, yb - q(7.5), code('iron', 2))
    fill(a, x0, yb - q(1.6), x1, yb, code('soot', 2))
    # posts and the lintel
    beam(a, x0 - q(3), y0, x0, yb, rng, 'timber', 3)
    beam(a, x1, y0, x1 + q(3), yb, rng, 'timber', 2)
    beam(a, x0 - q(4.5), y0 - q(3.5), x1 + q(4.5), y0, rng, 'timber', 3)


def damage(d, base, spec, info, rng):
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
                blk(d, rx[k] - q(2), ry[k] - q(1.2), rx[k] + q(2), ry[k] + q(1.4), 'slate', int(rng.choice([2, 4])), cut=1)
        elif kind == 'slates':
            n = args[0] if args else 6
            for _ in range(n):
                cx = rng.uniform(rx0 + q(4), rx1 - q(6))
                cy = rng.uniform(y_r + q(5), y_e - q(3))
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
            fold = ((X - x0) * 0.6 + (Y - yt)) % q(9)
            tt[fold < q(2)] = 4
            tt[(fold >= q(4.5)) & (fold < q(6))] = 2
            tt[X > x0 + (x1 - x0) * 0.7] -= 1
            T_, L_, B_, R_ = edges(m)
            tt[B_] = 1
            tt[T_] = 4
            tt = np.clip(tt, 0, 5)
            d[m] = FI[fam] * 8 + tt[m]
            # ropes to the eave and stones holding the foot
            for xx in (x0 + q(3), x1 - q(3)):
                bar(d, xx, yt + q(2), xx + q(2), yb + q(4), max(0.8, D * 0.35), 'timber_warm', 3)
            for xx in range(int(x0) + q(2), int(x1) - q(3), q(7)):
                blk(d, xx, yb - q(2.5), xx + q(4), yb + q(0.5), 'stone', 3, cut=1)
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
            blk(d, x0 - q(3), mid - q(3), x1 + q(3), mid - q(0.5), 'timber_warm', 4, cut=0)
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


def stones_heap(a, cx, yb, w, h, rng, n=None, fams=STONES, slates=True, planks_=True):
    """A heap of fallen stones, broken slates and a split board, back to front, lit from the upper
    left; bigger stones at the foot."""
    n = n or int(w * h / 22) + 4
    items = []
    for _ in range(n):
        fx = rng.uniform(-0.5, 0.5)
        fy = rng.random() ** 0.7
        items.append((fy, fx))
    items.sort()
    for fy, fx in items:
        sw = q(rng.uniform(3, 6.5) * (0.7 + 0.5 * fy))
        sh = q(rng.uniform(2.2, 4) * (0.7 + 0.5 * fy))
        hump = (1 - (2 * fx) ** 2) * q(h * 0.55)
        x = int(cx + fx * q(w) - sw / 2)
        y = int(yb - q(h) * (1 - fy) * 0.5 - hump * (1 - fy) - sh)
        r = rng.random()
        if slates and r < 0.25:
            blk(a, x, y + sh // 2, x + sw, y + sh // 2 + max(3, q(1.4)), 'slate', int(rng.choice([2, 3, 4])), cut=1)
        elif planks_ and r < 0.32:
            bar(a, x - q(4), y + sh, x + sw + q(3), y, q(1.2), 'timber_warm', 3)
        else:
            blk(a, x, y, x + sw, y + sh, fams[int(rng.integers(0, 3))], int(rng.choice([2, 3, 3, 4])), cut=2 if sw > 8 else 1)


def p_rubble(w, h, seed):
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=h * 0.9, side=2)
    stones_heap(p.a, p.ax, p.ay, w, h, rng)
    return finish(p)


def p_well(w, h, seed, choked=False):
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
    rubble(tmp, cx - rx, cy, cx + rx, yb, rng, base=3, course=(2.6, 3.2), length=(3.2, 5.0), moss=0.3, east_dark=False)
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
        stones_heap(a, cx, cy + iry, w * 0.75, h * 0.6, rng, n=16)
        # the hood came down with the storm: its posts snapped across the coping, its slates in the shaft
        board(a, cx - rx - q(4), cy + q(1), q(w + 6), q(2.6), -16, 'timber', 3, rng)
        board(a, cx - q(2), cy + q(3), q(w * 0.7), q(2.4), 12, 'timber', 2, rng)
        board(a, cx + q(1), cy - q(2), q(w * 0.5), q(1.8), -40, 'timber_cool', 3, rng)
        for _ in range(7):
            sx_, sy_ = cx + q(rng.uniform(-w * 0.35, w * 0.35)), cy + q(rng.uniform(-2, 3))
            blk(a, int(sx_), int(sy_), int(sx_) + q(3.6), int(sy_) + q(1.6), ('slate', 'slate_cool')[int(rng.integers(0, 2))],
                int(rng.choice([2, 3, 4])), cut=1)
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
    hm = roof_mask(a.shape, hx0, hx1, top_y - q(10), top_y + q(1.5))
    slate_roof(a, hm, hx0, hx1, top_y - q(10), top_y + q(1.5), rng, row=2.6, width=(3.4, 5.0), moss=0.15)
    fascia(a, hx0, hx1, top_y, rng)
    for xx, t in ((hx0, 3), (hx1 - q(1.6), 2)):
        beam(a, xx, top_y - q(10), xx + q(1.6), top_y + q(2.4), rng, 'timber', t)
    under = _rect(a.shape, cx - rx + q(1), top_y + q(2.4), cx + rx - q(1), top_y + q(3.6)) & (a >= 0)
    a[under] = code('timber_cool', 1)
    return finish(p)


def p_lantern(w, h, seed, lit=False):
    """The shard lantern: a street lamp 48 world px tall (about 1.9 people): a two-step plinth of
    dressed stone (lit top faces, bevelled arrises, shaded east sides, a chipped corner), a fluted
    iron foot, a tapering post with collars, scroll brackets under a glass cage with four frame bars,
    a pointed cap and a finial. Lit, the woodland's shard glows pale blue in the cage."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=50, side=8)
    a, cx, yb = p.a, p.ax, p.ay
    prism(a, cx - q(7.5), yb - q(5), cx + q(7.5), yb + 1, q(2.6), 'stone_warm', 3, side=q(2.6))
    prism(a, cx - q(5.2), yb - q(9), cx + q(5.2), yb - q(5), q(2.0), 'stone_warm', 3, side=q(2.0))
    fill(a, cx - q(7), yb - q(4.5), cx - q(5.6), yb - q(3.4), code('stone', 2))      # a chipped corner
    for k in range(3):
        mx = cx - q(6) + k * q(4.5)
        fill(a, mx, yb - q(1.2), mx + q(1.4), yb, code('leaf', 3))
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    ft, fb = yb - q(15), yb - q(8)
    foot = (Y >= ft) & (Y < fb) & (np.abs(X - cx) < q(1.8) + (Y - ft) / max(1, fb - ft) * q(2.0))
    hw = q(1.8) + (Y - ft) / max(1, fb - ft) * q(2.0)
    uf = (X - cx) / np.maximum(1, hw)
    tt = np.select([uf < -0.75, uf < -0.25, uf < 0.35, uf < 0.8], [3, 4, 2, 1], 2)   # rim, highlight, body, core, reflected
    a[foot] = FI['iron'] * 8 + tt[foot]
    a[foot & (Y >= fb - q(0.8))] = code('iron', 1)
    blk(a, cx - q(2.6), ft - q(1.4), cx + q(2.6), ft, 'iron', 3, cut=0)
    ao = _rect(a.shape, cx - q(4), fb, cx + q(4.5), fb + 2) & (a >= 0)
    a[ao] = np.maximum((a[ao] // 8) * 8, a[ao] - 2)          # occlusion where the foot meets the stone
    post = (Y >= yb - q(38)) & (Y < ft - q(1.4)) & (np.abs(X - cx) < q(1.5) - (ft - Y) / max(1, q(26)) * q(0.4))
    tt = np.full(a.shape, 2)
    tt[X < cx - q(0.4)] = 4
    tt[X > cx + q(0.7)] = 1
    a[post] = FI['iron'] * 8 + tt[post]
    for yy in (yb - q(25), yb - q(37)):
        blk(a, cx - q(2.2), yy, cx + q(2.2), yy + q(1.5), 'iron', 3, cut=0)
    for sx in (-1, 1):
        bar(a, cx + sx * q(1.2), yb - q(36), cx + sx * q(4.6), yb - q(39.5), max(1.0, q(0.5)), 'iron', 3 if sx < 0 else 2)
        blob(a, ellipse_mask(a.shape, cx + sx * q(4.6), yb - q(36.8), q(1.1), q(1.1)), 'iron', 2)
    gx0, gx1 = cx - q(4.5), cx + q(4.5)
    gy0, gy1 = yb - q(48), yb - q(40)
    blk(a, gx0 - q(1.2), gy1, gx1 + q(1.2), gy1 + q(1.6), 'iron', 3, cut=1)
    cage = (Y >= gy0) & (Y < gy1) & (np.abs(X - cx) < q(4.5) - (gy1 - Y) / max(1, gy1 - gy0) * q(0.8))
    if lit:
        a[cage] = code('sky', 4)
        a[cage & (Y < gy0 + q(2))] = code('sky', 5)
        blob(a, ellipse_mask(a.shape, cx, (gy0 + gy1) / 2 + q(0.5), q(1.8), q(2.8)), 'snow', 5, top=0, left=0, bot=0, right=0)
    else:
        a[cage] = code('slate_cool', 1)
        a[cage & (X < cx - q(1.5))] = code('slate', 3)
        a[cage & (X >= cx - q(1.5)) & (X < cx - q(0.8))] = code('slate', 2)
    for xx in (cx - q(4.0), cx - 1, cx + q(3.4)):
        a[cage & (X >= xx) & (X < xx + max(2, q(0.7)))] = code('iron', 2)
    cap = (Y >= gy0 - q(5)) & (Y < gy0) & (np.abs(X - cx) < q(6) * (Y - (gy0 - q(5.5))) / q(5.5))
    a[cap] = code('iron', 3)
    a[cap & (X < cx - q(0.6))] = code('iron', 4)
    a[cap & (Y >= gy0 - q(1))] = code('iron', 2)
    blob(a, ellipse_mask(a.shape, cx, gy0 - q(6.2), q(1.1), q(1.1)), 'iron', 3)
    return finish(p)


def p_stall(w, h, seed):
    """Moss's stall: a counter of sawn boards on trestles, crates of what the valley still grows
    (each fruit lit, the crate's slats in front), a striped awning on two poles with its hem
    scalloped and its shade on the counter, a slate board of prices, a sack at the foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=36, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    for xx, t in ((x0, 3), (x1 - q(2.2), 2)):
        beam(a, xx, yb - q(38), xx + q(2.2), yb, rng, 'timber', t)
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
    face = body & (Y < yb - q(16.8))
    a[face] = code('iron', 4)
    a[face & (X > cx - q(3)) & (X < cx + q(1))] = code('iron', 5)       # the polished face
    a[horn & (Y < yb - q(16.8))] = code('iron', 4)
    fill(a, cx + q(3.5), yb - q(17.5), cx + q(4.5), yb - q(16.8), code('iron', 0))   # the hardy hole
    return finish(p)


def p_fire(w, h, seed):
    """The forge lit: a bed of coals in the hearth, flames licking up, sparks over them. A light
    source: no outline."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10)
    a, cx, yb = p.a, p.ax, p.ay
    fill(a, cx - q(w / 2), yb - q(3), cx + q(w / 2), yb, code('lava', 1))
    for k in range(int(w / 2.2)):
        x = cx - q(w / 2) + k * q(2.2) + int(rng.integers(0, 2))
        blk(a, x, yb - q(4.5), x + q(2.2), yb - q(2), 'lava', int(rng.choice([2, 3, 3])), cut=1)
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


def p_smoke(w, h, seed):
    """Smoke from the crater: three puffs rising and leaning east, lit on their west sides."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=34, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    for k in range(6):
        y = yb - q(4 + k * 6)
        x = cx + q(k * 1.6) + int(rng.integers(-2, 3))
        r = q(4 + k * 0.9)
        m = ellipse_mask(a.shape, x, y, r, r * 0.8)
        blob(a, m & (a < 0), 'ash', 4 if k > 2 else 3)
        a[m & ellipse_mask(a.shape, x - r * 0.35, y - r * 0.3, r * 0.5, r * 0.4)] = code('ash', 5)
    return finish(p)


def p_beds(w, h, seed, scorched=True):
    """Four raised beds behind the hut: board edges, soil in rows. Scorched: ash and cinders, black
    stalks. Dug over: dark tilled earth; two of them sown with the valley's seed."""
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
            blk(a, bx0, by0, bx1, by1 + q(2), 'timber', 3, cut=1)
            ix0, iy0, ix1, iy1 = bx0 + q(1.6), by0 + q(1.6), bx1 - q(1.6), by1
            if scorched:
                fill(a, ix0, iy0, ix1, iy1, code('soot', 2))
                for yy in range(iy0 + q(2), iy1 - 1, q(3.5)):
                    fill(a, ix0, yy, ix1, yy + 2, code('ash', 2))
                for _ in range(5):
                    sx = int(rng.integers(ix0 + 2, ix1 - 3))
                    sy = int(rng.integers(iy0 + q(3), iy1 - 1))
                    fill(a, sx, sy - q(3), sx + 2, sy, code('soot', 0))
                    if rng.random() < 0.5:
                        fill(a, sx + 2, sy - q(3), sx + 4, sy - q(2), code('soot', 0))
                for _ in range(3):
                    sx = int(rng.integers(ix0 + 2, ix1 - 3))
                    sy = int(rng.integers(iy0 + 2, iy1 - 2))
                    fill(a, sx, sy, sx + 2, sy + 2, code('fox', 3))
            else:
                fill(a, ix0, iy0, ix1, iy1, code('earth', 2))
                for yy in range(iy0 + q(1.5), iy1 - 1, q(3.5)):
                    fill(a, ix0, yy, ix1, yy + 2, code('earth', 3))
                    fill(a, ix0, yy + 2, ix1, yy + 3, code('earth', 1))
                if k in (1, 2):
                    for yy in range(iy0 + q(2.5), iy1 - 2, q(3.5)):
                        for xx in range(ix0 + q(2), ix1 - q(2), q(4)):
                            blob(a, ellipse_mask(a.shape, xx, yy, q(1.2), q(1.0)), 'leaf', 4)
            k += 1
    return finish(p)


def p_notice_board(w, h, seed):
    """The notice board: two posts, a boarded panel under a little slate hood, notices pinned on it
    (one fresh, the rest rain-stained)."""
    rng = np.random.default_rng(seed)
    p = _pic(22, 6, up=34, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    for xx, t in ((cx - q(10), 3), (cx + q(8), 2)):
        beam(a, xx, yb - q(30), xx + q(2.2), yb, rng, 'timber', t)
    bx0, bx1, by0, by1 = cx - q(9), cx + q(9), yb - q(28), yb - q(14)
    planks(a, bx0, by0, bx1, by1, rng, base=3, width=3.0, vertical=False)
    for (nx, ny, nw, nh, t) in ((1, 2, 6, 7, 5), (8.5, 1.5, 5, 5, 4), (10, 7.5, 6, 5, 4), (2.5, 9.5, 5, 3, 3)):
        x, y = bx0 + q(nx), by0 + q(ny)
        blk(a, x, y, x + q(nw), y + q(nh), 'plaster', t, cut=0)
        for ly in range(y + q(1.6), y + q(nh) - 2, q(1.6)):
            fill(a, x + q(1), ly, x + q(nw) - q(1.2), ly + 1, code('dusk', 2))
        fill(a, x + q(nw / 2), y, x + q(nw / 2) + 2, y + 2, code('berry', 3))
    hm = roof_mask(a.shape, bx0 - q(3), bx1 + q(3), by0 - q(6), by0 + q(0.5), hip=q(2))
    slate_roof(a, hm, bx0 - q(3), bx1 + q(3), by0 - q(6), by0 + q(0.5), rng, row=2.4, width=(3, 4.4), moss=0.2)
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
    # the rune: a ring and a cross, cut and glowing
    rcy = top + q(15)
    groove = np.zeros(a.shape, bool)
    ring = ellipse_mask(a.shape, cx, rcy, q(3.4), q(3.4)) & ~ellipse_mask(a.shape, cx, rcy, q(2.4), q(2.4))
    groove |= ring
    groove |= seg_mask(a.shape, cx, rcy - q(6), cx, rcy + q(7), max(1.4, q(0.5)))
    groove |= seg_mask(a.shape, cx - q(4.5), rcy, cx + q(4.5), rcy, max(1.4, q(0.5)))
    groove &= front
    wall_up = groove & ~np.roll(groove, 1, axis=0)
    wall_lo = groove & ~np.roll(groove, -1, axis=0)
    a[groove] = code('sky', 3)
    a[groove & ellipse_mask(a.shape, cx, rcy, q(2), q(2))] = code('sky', 4)
    a[wall_up] = code('stone', 1)
    a[wall_lo] = code('stone', 5)
    halo = ndi.binary_dilation(groove, iterations=1) & ~groove & front
    a[halo] = code('stone_cool', 4)
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
    for k in (-1, 1):
        a[inner & (np.abs(X - (cx + k * r * 0.24)) < 0.6)] = code('timber_warm', 2)
    a[inner & (X > cx + r * 0.35)] = code('timber_warm', 3)
    return finish(p)


def p_trough(w, h, seed):
    """The quench trough: a stone tank with a dressed coping (lit top face, shaded front), the inner
    back wall in shade, dark water with a pale waterline against the wall and the sky's glint."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=8, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    rubble(a, x0, yb - q(7), x1, yb, rng, base=3, course=(2.4, 3.4), length=(4, 7), moss=0.35)
    top = yb - q(h + 7)
    prism(a, x0, top, x1, yb - q(6), q(2.0), 'stone_warm', 3, side=q(1.6))
    ix0, ix1, iy0, iy1 = x0 + q(2.2), x1 - q(3.4), top + q(2.0), yb - q(8.2)
    fill(a, ix0, iy0, ix1, iy1, code('stone', 2))
    fill(a, ix0, iy0, ix1, iy0 + q(1.6), code('stone', 1))                 # the back wall in shade
    fill(a, ix0, iy0 + q(1.6), ix1, iy1, code('water_cool', 1))
    fill(a, ix0, iy0 + q(1.6), ix1, iy0 + q(1.6) + 1, code('water', 4))   # the waterline
    fill(a, ix0, iy0 + q(1.6) + 1, ix0 + q(1.2), iy1, code('water', 0))    # the west wall's shade
    fill(a, ix0 + q(4), iy0 + q(3.2), ix0 + q(8), iy0 + q(3.2) + 2, code('sky', 4))
    fill(a, ix0 + q(9), iy0 + q(4.4), ix0 + q(11), iy0 + q(4.4) + 2, code('sky', 3))
    return finish(p)


def p_coal(w, h, seed):
    """A coal bin: a box of boards (lit top edge, shaded east end) heaped with coal, each lump with a
    glint on its upper left."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=9, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    stones_heap(a, cx, yb - q(4), w * 0.85, h * 0.8, rng, n=20, fams=('soot', 'soot', 'iron'), slates=False, planks_=False)
    prism(a, x0, yb - q(5.5), x1, yb, q(1.2), 'timber', 3, side=q(1.4))
    for xx in range(x0 + q(3), x1 - q(2), q(5)):
        fill(a, xx, yb - q(4), xx + 1, yb - 1, code('timber', 1))
    return finish(p)


def p_woodpile(w, h, seed):
    """Split logs stacked end-on under a board: the cut ends lit, bark between."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=12, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0 = cx - q(w / 2)
    r = q(2.4)
    for row in range(3):
        n = int(w / 5) - row
        for k in range(n):
            x = x0 + q(2.5) + row * q(2.5) + k * q(5)
            y = yb - q(2.5) - row * q(4.3)
            m = ellipse_mask(a.shape, x, y, r, r * 0.9)
            a[m] = code('timber_cool', 2)
            a[m & ellipse_mask(a.shape, x - 1, y - 1, r - 2, r * 0.9 - 2)] = code('plaster_warm', 3 if rng.random() < 0.6 else 2)
    return finish(p)


def p_grindstone(w, h, seed):
    """A treadle grindstone: a sandstone wheel seen side on (its worn edge band, a lit face), an iron
    axle with a crank, a timber frame on splayed legs, a treadle near the ground with its rod up to
    the crank, a drip can over the wheel."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=18, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    # frame: two splayed legs each side, a rail
    for lx, t in ((cx - q(6), 3), (cx + q(5), 2)):
        bar(a, lx - q(1.5), yb - 1, lx, yb - q(9), max(1.4, q(0.8)), 'timber', t)
        bar(a, lx + q(1.5), yb - 1, lx, yb - q(9), max(1.4, q(0.8)), 'timber', t - 1)
    board(a, cx - q(8), yb - q(10), q(16), q(2), 0, 'timber_warm', 3, rng, split=False)
    # the treadle and its rod
    board(a, cx - q(7), yb - q(2.2), q(12), q(1.6), -6, 'timber', 3, rng, split=False, grain=False)
    bar(a, cx + q(4), yb - q(3), cx + q(6.5), yb - q(12), max(1.0, q(0.4)), 'iron', 2)
    # the wheel
    wcx, wcy, R = cx, yb - q(13), q(5.5)
    rim = ellipse_mask(a.shape, wcx, wcy, R, R)
    a[rim] = code('stone_warm', 3)
    face = ellipse_mask(a.shape, wcx - q(0.6), wcy - q(0.4), R - q(1.2), R - q(1.2))
    a[face] = code('stone_warm', 4)
    a[face & ellipse_mask(a.shape, wcx - q(2), wcy - q(2), q(2.4), q(2))] = code('stone_warm', 5)
    edge_band = rim & ~ellipse_mask(a.shape, wcx - q(0.4), wcy - q(0.3), R - 1, R - 1)
    a[edge_band] = code('stone', 2)
    # axle and crank
    fill(a, wcx - q(8), wcy - 1, wcx + q(7), wcy + 1, code('iron', 2))
    blob(a, ellipse_mask(a.shape, wcx, wcy, q(1.2), q(1.2)), 'iron', 3)
    bar(a, wcx + q(7), wcy, wcx + q(7), wcy + q(2.5), max(1.0, q(0.5)), 'iron', 3)
    # the drip can over the wheel
    prism(a, wcx - q(2), wcy - R - q(5), wcx + q(1.5), wcy - R - q(1.5), q(0.8), 'iron', 3, side=q(0.8))
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
    """A bench as a volume: the seat seen from above (three boards running its length, their top
    faces lit, a dark gap between each, end grain at the west end), the seat's front edge in shade
    showing its thickness, the shade it throws on the legs; two dressed stone legs, each with a lit
    top, a mid front face and a dark east side."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    for lx in (x0 + q(2), x1 - q(7.5)):
        prism(a, lx, yb - q(7), lx + q(5.5), yb, q(1.4), 'stone', 3, side=q(1.6))
    yy = yb - q(13)
    a[_rect(a.shape, x0, yy, x1, yy + 3 * q(1.5) + 2)] = code('timber', 1)      # the gaps between the boards
    for k in range(3):
        th = q(1.5)
        board(a, x0, yy, x1 - x0, th, 0, ('timber_warm', 'timber_warm', 'timber')[k], (5, 4, 4)[k], rng, split=k == 1)
        a[_rect(a.shape, x0, yy + th - 1, x1, yy + th)] = code(('timber_warm', 'timber_warm', 'timber')[k], (4, 4, 3)[k])
        yy += th + 1
    a[_rect(a.shape, x0, yy - 1, x1, yy + q(1.6))] = code('timber', 2)                 # the edge's thickness
    a[_rect(a.shape, x0, yy + q(1.6) - 1, x1, yy + q(1.6))] = code('timber', 1)
    sh = _rect(a.shape, x0, yy + q(1.6), x1, yy + q(2.6)) & (a >= 0)
    a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - 2)                                     # its shade on the legs
    a[_rect(a.shape, x0, yb - q(13), x0 + q(1.2), yy + q(1.6))] = code('plaster_warm', 3)   # end grain
    a[_rect(a.shape, x1 - q(1.2), yb - q(13), x1, yy + q(1.6))] = code('timber', 1)
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
def p_debris(w, h, seed):
    """Storm litter on the flags: broken slates, a snapped batten, twigs and leaves."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=2, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    for _ in range(int(w * h / 30) + 3):
        x = cx + q(rng.uniform(-w / 2, w / 2))
        y = yb - q(rng.uniform(0, h))
        r = rng.random()
        if r < 0.45:
            blk(a, x, y, x + q(rng.uniform(3, 5)), y + max(3, q(1.6)), ('slate', 'slate_cool')[int(rng.integers(0, 2))],
                int(rng.choice([2, 3, 4])), cut=1)
        elif r < 0.6:
            bar(a, x, y, x + q(rng.uniform(6, 10)), y + q(rng.uniform(-2, 2)), max(1, q(0.7)), 'timber_warm', 3)
        elif r < 0.8:
            bar(a, x, y, x + q(rng.uniform(3, 6)), y + q(rng.uniform(-3, 3)), max(1.0, D * 0.35), 'timber_cool', 2)
        else:
            blob(a, ellipse_mask(a.shape, x, y, q(1.4), q(1.0)), ('leaf', 'brass', 'fox')[int(rng.integers(0, 3))], 3)
    return finish(p)


def p_cart(w, h, seed):
    """A handcart left in the square when the village ran: a bed of boards with side rails and nails,
    its shafts on the ground, a sack and a crate on it, one iron-tyred wheel side on with hub and six
    spokes."""
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
    'well': lambda w, h, s: p_well(w, h, s, choked=False),
    'well_choked': lambda w, h, s: p_well(w, h, s, choked=True),
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


def prop(kind: str, w: float, h: float, seed: int = 0) -> Pic:
    return PROPS[kind](w, h, seed)
