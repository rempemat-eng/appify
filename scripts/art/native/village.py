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


def finish(p: Pic, line=True, keep=None) -> Pic:
    """Tidy the lone pixels, outline the silhouette and tidy once more; `keep` masks texels the tidy
    must leave alone (a nail head's lit texel, XR3-S1)."""
    tidy(p.a, keep=keep)
    if line:
        outline(p.a)
        tidy(p.a, passes=1, keep=keep)
    return p


def nail_lights(a):
    """The lit texel of every nail head nail_head() drew (iron 4 over a dark 2 x 2 head), as a mask for
    finish(keep=...): one texel unlike its four neighbours, which the tidy would otherwise take."""
    lit, dk = code('iron', 4), code('iron', 1)
    m = np.zeros(a.shape, bool)
    m[:-1, :-1] = (a[:-1, :-1] == lit) & (a[:-1, 1:] == dk) & (a[1:, :-1] == dk) & (a[1:, 1:] == dk)
    return m


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


def p_lantern(w, h, seed, lit=False, hd=False):
    """The shard lantern, a street lamp 48 world px tall. Dressed stone plinth courses (lit tops,
    chamfers, dark east sides; `hd`: plinth_hd, its glass lit with the lamp ramp); a flared iron foot and a round post shaded as cylinders (a reflected
    rim, a highlight band, a core shadow) with collars; scroll brackets; a glass cage whose panes
    reflect the sky in diagonal streaks between lit frame bars, with an iron cradle inside (empty, or
    holding the woodland's shard alight); a pyramid cap with a lit west facet and a dark east one."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=50, side=8)
    a, cx, yb = p.a, p.ax, p.ay
    if hd:
        lamp_plinth_hd(a, cx, yb, np.random.default_rng(seed + 11))
    else:
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
        if hd:
            # XR2-L3: no pale shape in the unlit glass: a low dark cradle bowl seen through it, its rim
            # a tone up on the west only
            cb = _rect(a.shape, cx - q(1.4), gy1 - q(2.2), cx + q(1.4), gy1 - q(1.2))
            a[cb] = code('void', 1)
            a[cb & (X < cx) & (Y < gy1 - q(2.2) + 1)] = code('slate_cool', 2)
        else:
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
    if hd and lit:
        lamp_glass(a, cx, yb)
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


def p_sacks_hd(w, h, seed, hd=False):
    """Seed sacks, two on the ground and one lying on them: each a soft volume (lit cap upper left,
    the core shadow low right, a bounce at the rim), burlap weave drawn as a fine cross of tone
    steps, a seam, folds running to the tied neck, the top sack's shadow on those under it."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=12, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    weave = ((X.astype(int) + Y.astype(int)) % 3 == 0) | ((X.astype(int) - Y.astype(int)) % 4 == 0)
    sacks = ((-0.25, 0.0, 1.0), (0.22, 0.0, 0.9), (0.0, -1.0, 0.85))
    for k, (dx, dy, s_) in enumerate(sacks):
        scx, rx, ry = cx + q(w * dx), q(4.2 * s_), q(4.6 * s_)
        scy = yb - q(5 * s_) - (q(4.0 if hd else 5.5) if dy else 0)      # (scale gate: the top sack slumps, about 40 tall)
        nx, ny = (X - scx) / rx, (Y - scy) / ry
        d = nx * nx + ny * ny
        m = d <= 1
        t = 2.8 + 2.4 * lam(nx, ny * 0.8, np.sqrt(np.clip(1 - d, 0, 1))) + 0.6 * (d > 0.82) * (nx > 0.2)
        t = t - 0.6 * weave
        paint(a, m, ('sand_cool', 'sand', 'sand_warm'), t - 0.5)
        fold = m & (np.abs(X - scx - rx * 0.15 - (Y - scy) * 0.25) < 0.7) & (Y > scy - ry * 0.5)
        a[fold] = a[fold] - 1 * ((a[fold] % 8) > 0)
        neck = (np.abs(X - scx) < q(1.3)) & (Y >= scy - ry - q(1.6)) & (Y < scy - ry + 1)
        paint(a, neck, ('sand_cool', 'sand', 'sand_warm'), 3.0 - 1.5 * (X > scx))
        tie = (np.abs(X - scx) < q(1.4)) & (np.abs(Y - (scy - ry)) < 1)
        a[tie] = code('timber_warm', 2)
        if dy:                                                         # its shade on the sacks below
            under = (np.abs(X - scx - q(1)) < rx) & (Y > scy + ry * 0.6) & (Y < scy + ry + q(1.2)) & (a >= 0) & ~m
            a[under] = a[under] - 1 * ((a[under] % 8) > 0)
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


# ------------------------------------------------------------------------------------------------
# density 3: the Crossroads props after the 8 Nov detail audit (docs/reviews/2026-11-08-crossroads-placed.md)
# ------------------------------------------------------------------------------------------------
# Each painter answers its fix list: wood as boards on sibling ramps with grain in short irregular
# streaks, butt joints and nail heads set in them; stone as irregular lumps with a lit crown, a body
# and a dark underside, sibling clusters, chips and cracks with a lit lip; every item drawn as itself
# (a fruit, a lump of coal, a log end), never one stamp on a lattice. No dither, no noise for its own sake.
def _codes(a, m, fam, tt):
    """Write mask m with a family (a name, or per-pixel family indices) and per-pixel tones."""
    tt = np.clip(np.round(np.broadcast_to(np.asarray(tt, float), m.shape)), 0, 5).astype(int)
    fi = np.broadcast_to(np.asarray(FI[fam] if isinstance(fam, str) else fam), m.shape)
    a[m] = (fi * 8 + tt)[m]


def _step_down(a, m, k=1):
    """Shade what is already drawn under mask m by k tones on its own ramp."""
    m = m & (a >= 0)
    a[m] = np.maximum((a[m] // 8) * 8, a[m] - k)


def nail_head(a, x, y, rust=0):
    """A forged nail set in a board: a dark 2 x 2 head with its upper-left texel lit, and a rust run of
    `rust` texels under it (0: none)."""
    H, W = a.shape
    x, y = int(x), int(y)
    if not (0 <= x < W - 1 and 0 <= y < H - 1):
        return
    a[y:y + 2, x:x + 2] = code('iron', 1)
    a[y, x] = code('iron', 4)
    if rust:
        a[y + 2:min(H, y + 2 + rust), x + 1] = code('fox', 1)


def plank_strip(a, x0, y0, x1, y1, rng, base=3, along='x', joints=(14, 30), nails=True, fams=TIMBER,
                lit=1, dark=1, where=None):
    """Boards laid end to end along a strip: each board on its own sibling ramp, its lit arris on top (on
    the west when the strip runs north-south) and a dark last row, grain as irregular streaks of 2 to 4
    texels (now and then a longer one) along it, a butt joint every 14 to 30 texels (a dark seam, the next
    board's sawn end lit) with a nail head set in the board beside it. Returns the strip's mask."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    L, T = (x1 - x0, y1 - y0) if along == 'x' else (y1 - y0, x1 - x0)
    if L < 2 or T < 1:
        return np.zeros(a.shape, bool)
    tt = np.full((T, L), base, int)
    ff = np.zeros((T, L), int)
    cuts = [0]
    while cuts[-1] < L:
        cuts.append(cuts[-1] + int(rng.integers(joints[0], joints[1] + 1)))
    cuts[-1] = L
    if len(cuts) > 2 and cuts[-1] - cuts[-2] < 8:
        del cuts[-2]
    prev = -1
    for s, e in zip(cuts, cuts[1:]):
        k = int(rng.integers(0, len(fams)))
        k = (k + 1) % len(fams) if k == prev else k
        prev = k
        ff[:, s:e] = FI[fams[k]]
        for _ in range(max(1, (e - s) * max(1, T - 2) // 11)):
            r = int(rng.integers(1, T - 1)) if T >= 3 else int(rng.integers(0, T))
            ln = int(rng.integers(2, 5)) if rng.random() < 0.7 else int(rng.integers(5, 9))
            st = int(rng.integers(s, max(s + 1, e - ln)))
            tt[r, st:min(e, st + ln)] = base - 1 if rng.random() < 0.8 else base + 1
    if lit:
        tt[0, :] = base + lit
    if dark and T >= 3:
        tt[-1, :] = base - dark
    heads = []
    for c in cuts[1:-1]:
        tt[:, c - 1] = base - 2
        tt[:T - 1 if T > 2 else T, c] = base + 1
        heads.append(c - 4 if rng.random() < 0.5 else c + 2)
    if along == 'y':
        tt, ff = tt.T, ff.T
    m = np.zeros(a.shape, bool)
    m[y0:y1, x0:x1] = True
    if where is not None:
        m &= where
    sub = (ff * 8 + np.clip(tt, 0, 5))
    blk_ = a[y0:y1, x0:x1]
    mm = m[y0:y1, x0:x1]
    blk_[mm] = sub[:blk_.shape[0], :blk_.shape[1]][mm]
    if nails and T >= 4:
        r = (T - 2) // 2
        for u in heads:
            if 0 <= u < L - 1:
                nx_, ny_ = (x0 + u, y0 + r) if along == 'x' else (x0 + r, y0 + u)
                if m[ny_, nx_]:
                    nail_head(a, nx_, ny_)
    return m


def lump(a, cx, cy, rx, ry, fam, rng, base=3, chip=True, crack=False, lo=0, hi=5, where=None):
    """A stone lump lit from the upper left: an irregular outline, a lit crown, a body and a dark
    underside in four or five tones, sibling clusters on its face, a chipped corner whose fresh face
    catches the light, sometimes a crack with a lit lower lip. Returns its mask."""
    Y, X = grid(a)
    ang = np.arctan2((Y - cy) / max(ry, 1), (X - cx) / max(rx, 1))
    wob = 1.0 + sum(rng.uniform(-0.09, 0.09) * np.cos(k * ang + rng.uniform(0, 6.3)) for k in (2, 3, 5))
    d2 = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
    m = d2 <= wob ** 2
    m &= Y <= cy + ry * 0.78                                   # it sits on a flattish bed
    if chip:
        # a corner knocked off: a straight cut across the upper west or east shoulder
        sx = -1 if rng.random() < 0.5 else 1
        k = rng.uniform(0.55, 0.75)
        cut = (sx * (X - cx) / rx - (Y - cy) / ry) > (1.0 + k) * 0.92
        m &= ~cut
    if where is not None:
        m &= where
    if not m.any():
        return m
    nx, ny = (X - cx) / rx, (Y - cy) / ry
    nz = np.sqrt(np.clip(1 - np.minimum(d2, 1), 0, 1))
    t = base - 0.3 + 1.7 * lam(nx, ny * 0.9, nz * 0.6)
    t = np.where(ny > 0.4, t - 1.0, t)                          # the underside turning away
    tt = np.clip(np.round(t), lo, hi).astype(int)
    T_, L_, B_, R_ = edges(m)
    tt = np.where(B_ | R_, np.maximum(lo, tt - 1), tt)
    fam_arr = np.full(a.shape, FI[fam])
    # sibling clusters: a few patches of 2 to 4 texels in a sibling family, a tone apart
    base_f = fam.replace('_warm', '').replace('_cool', '')
    sibs = [f for f in (base_f, base_f + '_warm', base_f + '_cool') if f in FI and f != fam]
    area = int(m.sum())
    for _ in range(max(1, area // 45)):
        ys_, xs_ = np.nonzero(m & ~T_ & ~B_)
        if not len(ys_):
            break
        i = int(rng.integers(0, len(ys_)))
        pm = ((X - xs_[i] - 0.5) / rng.uniform(1.0, 2.2)) ** 2 + ((Y - ys_[i] - 0.5) / rng.uniform(0.8, 1.4)) ** 2 <= 1
        pm &= m & ~T_
        fam_arr[pm] = FI[sibs[int(rng.integers(0, len(sibs)))]] if sibs else FI[fam]
        tt[pm] = np.clip(tt[pm] + int(rng.choice([-1, 0, 1])), lo, hi)
    if chip:
        # the chip's fresh face: the texels along the cut, a tone up
        cutface = m & ~ndi.binary_erosion(m, iterations=1) & ((sx * (X - cx) / rx - (Y - cy) / ry) > (1.0 + k) * 0.92 - 0.5)
        tt[cutface] = np.minimum(hi, tt[cutface] + 1)
    tt = np.where(T_ & (tt >= base), np.minimum(hi, tt + 1), tt)
    a[m] = (fam_arr * 8 + tt)[m]
    if crack and rx >= 5:
        y_c = cy + rng.uniform(-0.3, 0.2) * ry
        x_s = cx + rng.uniform(-0.5, -0.1) * rx
        pts = curve(x_s, y_c, x_s + rx * rng.uniform(0.6, 0.9), y_c + rng.uniform(-1.5, 2.5), rng.uniform(-1.2, 1.2), 4)
        cr = np.zeros(a.shape, bool)
        for (ax_, ay_), (bx_, by_) in zip(pts, pts[1:]):
            cr |= seg_mask(a.shape, ax_, ay_, bx_, by_, 0.55)
        cr &= ndi.binary_erosion(m, iterations=1)
        lip = np.roll(cr, 1, axis=0) & ~cr & m
        a[cr] = code(fam, max(lo, 1))
        a[lip] = code(fam, min(hi, base + 1))
    return m


def slate_shard(a, x0, y0, length, rng, fam='slate', where=None):
    """A broken roof slate lying on the heap: a thin plate with its top face (the lit upper edge, the
    body), a dark edge face of 2 texels under it, one end snapped off ragged and a break line across."""
    H, W = a.shape
    Y, X = grid(a)
    tilt = rng.uniform(-0.18, 0.18)
    th = max(3, q(1.1))
    top = Y - (y0 + tilt * (X - x0))
    within = (X >= x0) & (X < x0 + length)
    # the snapped end: a zigzag at the east end
    zz = x0 + length - 1 - (np.abs(((Y - y0) % 4) - 2))
    within &= X < zz + 1
    plate = within & (top >= 0) & (top < th)
    face = within & (top >= th) & (top < th + 2)
    if where is not None:
        plate &= where
        face &= where
    t = int(rng.choice([3, 4]))
    _codes(a, plate, fam, t)
    a[plate & (top < 1)] = code(fam, min(5, t + 1))
    a[plate & (X < x0 + 1)] = code(fam, min(5, t + 1))
    _codes(a, face, fam, 1)
    a[face & (top >= th + 1)] = code(fam, 0)
    # the break line: a crack across the plate, its west lip lit
    bx = x0 + int(length * rng.uniform(0.35, 0.6))
    br = plate & (np.abs(X - (bx + (Y - y0) * 0.6)) < 0.6)
    lip = np.roll(br, -1, axis=1) & plate & ~br
    a[br] = code(fam, 1)
    a[lip] = code(fam, min(5, t + 1))
    return plate | face


def moss_run(a, xa, xb, jy, rng, band=4, cap=2):
    """Moss grown along a joint from xa to xb (XR2-L2, W4): leaf clusters, not a pill. The run breaks
    into clumps of 3 to 7 columns with gaps; each clump's cap rises and falls in steps of two columns
    (1 to cap + 1 texels over the joint), its tops lit on the west in leaf 4 with a lit tip or two, its
    body in leaf 3 and 2 on sibling ramps, a ragged band `band` texels deep under the joint whose last
    row is dark, and now and then a strand hanging a texel or two lower; only over what is drawn."""
    xa, xb = int(xa), int(xb)
    H, W = a.shape
    x = xa
    while x < xb - 2:
        n = min(int(rng.integers(4, 10)), xb - x)
        hs = [int(rng.integers(1, cap + 2)) for _ in range((n + 1) // 2)]
        hang = 0
        for i in range(n):
            xx = x + i
            if not 0 <= xx < W:
                continue
            edge_ = i == 0 or i == n - 1
            ht = max(0, hs[i // 2] - (1 if edge_ else 0))
            bd = max(2, band - (1 if edge_ else 0) + int(rng.integers(-1, 1)))
            if i % 2 == 0:
                hang = 2 if rng.random() < 0.12 else 0
            bd += hang                                                    # a strand hanging lower
            sib = 'leaf_warm' if ((x + i) // 2) % 3 == 0 else 'leaf'
            for y in range(jy - ht, jy + bd):
                if not (0 <= y < H and a[y, x + i] >= 0):
                    continue
                if y == jy - ht:
                    t, f = (4, sib) if (i < n * 0.6) else (3, sib)
                elif y < jy:
                    t, f = 3, sib
                elif y == jy + bd - 1:
                    t, f = 1, 'leaf_cool'
                else:
                    t, f = (2, 'leaf') if (y - jy) % 3 else (2, 'leaf_cool')
                a[y, xx] = code(f, t)
        # a lit tip on the clump's west crest: two texels
        tx = x + int(rng.integers(0, max(1, n // 2)))
        ty = jy - max(0, hs[(tx - x) // 2] - (1 if tx == x else 0))
        if 0 <= ty < H and tx + 1 < W and a[ty, tx] >= 0 and a[ty, tx + 1] >= 0:
            a[ty, tx:tx + 2] = code('leaf_warm', 5)
        x += n + int(rng.integers(1, 4))


def plinth_hd(a, cx, yb, rng, slabs=((7.5, 5, 2.6), (5.2, 4, 2.0)), fam='stone_warm', moss=True):
    """A plinth of dressed stone slabs, lowest first (half-width, height, top depth in world px), each
    drawn as dressed stone (XR2-L1): a top plane in tone 4 on sibling ramps, its back edge a tone down,
    its west and front arris lit; a bevel step under the front arris; the front face in 3 to 4 tones:
    the slab's ashlar blocks (a joint, the next block's edge lit), tooled in sibling clusters of 2 to 5
    texels a tone up on the lit west and down in the east, pocks with a lit lower lip; the east face a
    core shadow between a lit arris and a reflected rim; chips knocked off two corners, each with a lit
    lip; a dark contact row. Moss in clumps (moss_run) in the joint under the upper slab (XR2-L2).
    Returns the top of the plinth (texels)."""
    Y, X = grid(a)
    y_bot = yb + 1
    tops = []
    cum = 0.0
    for i, (hw, ht, td) in enumerate(slabs):
        x0, x1 = cx - q(hw), cx + q(hw)
        cum += ht
        y0 = yb - q(cum)
        side = max(3, q(td) * 2 // 3)
        tdp = q(td)
        m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y_bot)
        # chips: the top slab's top-left corner, and one lower corner of every slab
        chip1 = m & ((X - x0) + (Y - y0) < q(1.0) + 1) if i == len(slabs) - 1 else np.zeros(a.shape, bool)
        cxp = x1 - 1 if rng.random() < 0.5 else x0
        sxp = -1 if cxp > cx else 1
        chip2 = m & (((X - cxp - 0.5) * sxp) + (y_bot - 1 - Y) < 2.5) & ((X - cxp - 0.5) * sxp >= -0.5)
        m &= ~chip1 & ~chip2
        topm = m & (Y < y0 + tdp)
        sidem = m & ~topm & (X >= x1 - side)
        front = m & ~topm & ~sidem
        fy = (Y - y0 - tdp) / max(1, y_bot - y0 - tdp)
        # the top plane: tone 4, sibling clusters at the same tone, the back edge receding a tone down,
        # the west arris and the front arris lit
        sib = ndi.gaussian_filter(rng.random(a.shape), 1.2) > 0.54
        _codes(a, topm, fam, 4)
        a[topm & sib] = code('stone', 4)
        a[topm & (Y < y0 + 1)] = code(fam, 3)
        a[topm & (X < x0 + 1)] = code(fam, 5)
        a[topm & (Y == y0 + tdp - 1) & (X < x1 - side)] = code(fam, 5)            # the lit front arris
        a[topm & (X >= x1 - side)] = code(fam, 3)
        a[topm & (X >= x1 - side) & (sib)] = code('stone_cool', 3)
        # the front face: lit west falling to the east, a bevel row, the lower row turning under
        u = (X - x0) / max(1, x1 - side - x0)
        tf = np.where(u < 0.3, 3.6, np.where(u < 0.75, 3.0, 2.4)) - 0.6 * (fy > 0.75)
        _codes(a, front, fam, tf)
        a[front & (Y == y0 + tdp)] = code(fam, 4)                                  # the bevel step
        a[front & (Y == y0 + tdp) & (u > 0.7)] = code(fam, 3)
        a[front & (X == x0)] = code(fam, 4)
        # tooling: sibling clusters of 2 to 5 texels, up on the lit west, down in the east
        for _ in range(max(4, int(front.sum()) // 22)):
            px, py = rng.uniform(x0 + 2, x1 - side - 2), rng.uniform(y0 + tdp + 2, y_bot - 2)
            pm = front & (((X - px) / rng.uniform(1.2, 2.6)) ** 2 + ((Y - py) / rng.uniform(0.7, 1.2)) ** 2 <= 1)
            if pm.sum() < 2:
                continue
            uu_ = (px - x0) / max(1, x1 - side - x0)
            dt = 1 if (uu_ < 0.45 and rng.random() < 0.7) else (-1 if rng.random() < 0.6 else 0)
            f_ = ('stone', 'stone_cool', fam)[int(rng.integers(0, 3))]
            a[pm] = FI[f_] * 8 + np.clip(tone_of(a[pm]) + dt, 1, 5)
        for _ in range(int(rng.integers(2, 4))):                                   # pocks, their lower lip lit
            px, py = int(rng.uniform(x0 + 2, x1 - side - 3)), int(rng.uniform(y0 + tdp + 2, y_bot - 3))
            pk = front & (np.floor(Y) == py) & (X >= px) & (X < px + 2)
            if pk.sum() == 2:
                a[pk] = code(fam, 1)
                a[np.roll(pk, 1, axis=0) & front] = code(fam, 4)
        # the slab's blocks: a joint or two, the next block's edge lit
        nb = 2 if (x1 - side - x0) > q(10) else 1
        jx_list = sorted(int(x0 + (x1 - side - x0) * (k + 1) / (nb + 1) + rng.uniform(-3, 3)) for k in range(nb))
        for jx in jx_list:
            a[front & (X == jx) & (Y > y0 + tdp)] = code(fam, 1)
            a[front & (X == jx + 1) & (Y > y0 + tdp) & (Y < y_bot - 1)] = code(fam, 4)
        # the east face: a lit arris column, the core shadow, a reflected rim at the far edge
        ex = (X - (x1 - side)) / max(1, side)
        _codes(a, sidem, 'stone_cool', np.where(ex < 0.25, 2.6, np.where(ex < 0.75, 1.0, 1.8)) - 0.4 * (fy > 0.7))
        a[sidem & (Y == y0 + tdp)] = code('stone_cool', 3)
        # the chips' fresh faces: lit where they face up and west, a dark texel where they face east
        for ch in (chip1, chip2):
            if ch.any():
                lipc = m & ndi.binary_dilation(ch, iterations=1)
                a[lipc & (X < cx)] = code(fam, 5)
                a[lipc & (X >= cx)] = code('stone_cool', 3)
        a[m & (Y == y_bot - 1)] = code(fam, 1)
        a[m & (Y == y_bot - 1) & (X >= x1 - side)] = code('stone_cool', 0)
        tops.append((x0, x1, y0))
        y_bot = y0
    if moss and len(tops) > 1:
        # moss in the joint under the upper slab, in clumps (moss_run), never evenly spaced
        ux0, ux1, uy0 = tops[1]
        jy = tops[0][2]
        span = ux1 - ux0
        moss_run(a, ux0 - 3 + rng.uniform(0, span * 0.15), ux1 + 3, jy, rng, band=4, cap=2)
    return tops[-1][2]


def sibling_cells(a, face, rng, y0, y1, x0, x1, fams, share=0.5, step=(4, 5), squash=0.9, maxrun=40, iters=400,
                  keep=None):
    """Break a surface into clusters on sibling ramps at the same tone (XR3-T1, L1): a patchwork of cells
    about step[0] x step[1] texels, each on one of `fams` (shape, no value noise), and then any one-tone
    run over `maxrun` texels, judged as finish() will leave the picture (tidied and outlined), loses one
    of its cells to the next sibling until none is left. `face` is the mask it may recolour; `keep` is
    what finish() will be told to keep."""
    Y, X = grid(a)
    sy_, sx_ = np.mgrid[y0:y1:step[0], x0:x1:step[1]]
    seeds = np.stack([sy_.ravel() + rng.uniform(0, step[0], sy_.size), sx_.ravel() + rng.uniform(0, step[1], sx_.size)], 1)
    d2 = ((Y[..., None] - seeds[:, 0]) / squash) ** 2 + (X[..., None] - seeds[:, 1]) ** 2
    cell = np.argmin(d2, axis=2)
    pick = (rng.random(len(seeds)) < share).astype(int)
    fa = np.array([FI[f] for f in fams])
    for _ in range(iters):
        a[face] = (fa[pick[cell]] * 8 + tone_of(a))[face]
        t_ = tidy(a.copy(), keep=keep)
        a[face] = t_[face]
        outline(t_)
        tidy(t_, passes=1, keep=keep)
        seen = np.isin(fam_of(t_), fa) & (t_ >= 0)
        big = []
        for v in np.unique(t_[seen]):
            lab, k = ndi.label((t_ == v) & seen)
            n_ = np.bincount(lab.ravel())
            n_[0] = 0
            big += [(lab == i) & face for i in np.nonzero(n_ > maxrun)[0]]
        big = [rm for rm in big if rm.any()]
        if not big:
            break
        for rm in big:
            cs = np.bincount(cell[rm], minlength=len(seeds))
            c = int(rng.choice(len(seeds), p=cs / cs.sum()))
            pick[c] = (pick[c] + 1) % len(fams)
    return cell


def moss_clumps(a, jy, spans, rng):
    """Moss in the joint at row jy (XR3-L2): one clump per (x0, x1) span, each its own size: a lit cap
    2 texels deep (leaf 4 and 5 on the west, a lit tip), over a band of 3 to 4 texels whose lower edge is
    ragged (the band's depth changes every one to three columns) and dark; a tuft or two standing proud of
    the cap. Only over what is drawn."""
    H, W = a.shape
    for (xa, xb) in spans:
        xa, xb = int(xa), int(xb)
        n = xb - xa
        crest = [0] * n
        for i in range(n):                                                # the cap's crest, rising to the middle
            e = min(i, n - 1 - i)
            crest[i] = 0 if e == 0 else (1 if e < 2 else 2) + (1 if (e >= 3 and rng.random() < 0.35) else 0)
        depth, i = [], 0
        while len(depth) < n:                                             # the ragged underside
            run = int(rng.integers(1, 4))
            depth += [int(rng.integers(3, 6))] * run
        for i in range(n):
            x = xa + i
            if not 0 <= x < W:
                continue
            edge_ = i == 0 or i == n - 1
            top = jy - crest[i]
            bot = jy + depth[i] - (1 if edge_ else 0)
            for y in range(top, bot):
                if not (0 <= y < H and (a[y, x] >= 0 or y < jy)):           # the cap may stand proud of the stone
                    continue
                k = y - top
                if k == 0:
                    t, f = (5, 'leaf_warm') if i < n * 0.45 else (4, 'leaf')
                elif k == 1:
                    t, f = (4, 'leaf_warm') if i < n * 0.6 else (3, 'leaf')
                elif y == bot - 1:
                    t, f = 1, 'leaf_cool'
                elif y == bot - 2:
                    t, f = 2, 'leaf_cool'
                else:
                    t, f = 3, ('leaf' if (x // 2) % 2 else 'leaf_cool')
                a[y, x] = code(f, t)


def lamp_plinth_hd(a, cx, yb, rng, slabs=((7.5, 5, 2.6), (5.2, 4, 2.0))):
    """The lamp's plinth of dressed stone slabs, lowest first (half-width, height in world px; the third
    figure is kept for the call's shape), each drawn with its volume (XR3-L1): a top plane three rows deep
    in tone 4 on sibling ramps, its back row receding a tone and its front-left arris lit; a one-row bevel
    step under the arris; a lit west end two or three columns wide; the front in three tones (lit west,
    body, shaded east), its blocks parted by joints and tooled in sibling clusters so no one-tone run is
    over 60 texels, its lowest rows turning under; the east end in core shadow; two chips with lit lips;
    a dark contact row. Moss grows in one or two clumps of different sizes in the joint under the upper
    slab, placed unevenly (XR3-L2). Returns the top of the plinth (texels)."""
    Y, X = grid(a)
    y_bot = yb + 1
    tops = []
    cum = 0.0
    for i, (hw, ht, _td) in enumerate(slabs):
        x0, x1 = cx - q(hw), cx + q(hw)
        cum += ht
        y0 = yb - q(cum)
        tdp = 3                                                           # the top plane's depth
        wl = 3 if i == 0 else 2                                           # the lit west end
        side = 4 if i == 0 else 3                                         # the east end, in shadow
        m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y_bot)
        # two chips knocked off the top corners, each a step cut of 3 to 6 texels, one bigger than the other
        chip1 = m & ((X - x0) + (Y - y0) < 1.5 + rng.uniform(0.5, 1.5) + (i == 0))
        chip2 = m & ((x1 - 1 - X) + (Y - y0) < 1.5 + rng.uniform(0.5, 1.5) + (i == 1))
        m &= ~chip1 & ~chip2
        topm = m & (Y < y0 + tdp)
        bev = m & (Y == y0 + tdp)
        west = m & ~topm & ~bev & (X < x0 + wl)
        east = m & ~topm & (X >= x1 - side)
        front = m & ~topm & ~bev & ~west & ~east
        u = (X - x0 - wl) / max(1, x1 - side - x0 - wl)
        fy = (Y - y0 - tdp - 1) / max(1, y_bot - 1 - y0 - tdp - 1)
        # the top plane: tone 4, its back row a tone down, the front arris lit on the west, the east end
        # of the plane turning away
        _codes(a, topm, 'stone_warm', 4)
        a[topm & (Y < y0 + 1)] = code('stone_warm', 3)
        a[topm & (Y == y0 + tdp - 1) & (X < x0 + (x1 - x0) * 0.6)] = code('stone_warm', 5)
        a[topm & (X < x0 + 1) & (Y > y0)] = code('stone_warm', 5)
        a[topm & (X >= x1 - side)] = code('stone_warm', 3)
        a[topm & (X >= x1 - side) & (Y == y0 + tdp - 1)] = code('stone_warm', 4)
        # the bevel step: a row in half shade under the arris, darker over the east end
        _codes(a, bev, 'stone_warm', np.where(X < x1 - side, 3, 2))
        a[bev & (X < x0 + wl)] = code('stone_warm', 4)
        # the lit west end
        _codes(a, west, 'stone_warm', np.where(X < x0 + 1, 5, 4) - (fy > 0.8))
        # the front in three tones, the boundaries stepping by a texel or two from course to course
        jit = (rng.random(a.shape[0]) * 0.08)[:, None]
        tf = np.select([u + jit < 0.34, u + jit < 0.7], [4, 3], 2) - (fy > 0.78)
        _codes(a, front, 'stone_warm', tf)
        # the blocks: a joint or two, the next block's west edge lit
        nb = 2 if (x1 - side - x0) > q(10) else 1
        for k in range(nb):
            jx = int(x0 + wl + (x1 - side - x0 - wl) * (k + 1) / (nb + 1) + rng.uniform(-3, 3))
            jm = front & (X >= jx) & (X < jx + 1) & (Y > y0 + tdp + 1)
            a[jm] = code('stone_cool', 1)
            lit_ = front & (X >= jx + 1) & (X < jx + 2) & (Y > y0 + tdp + 1) & (Y < y_bot - 1)
            a[lit_] = FI['stone_warm'] * 8 + np.minimum(5, tone_of(a[lit_]) + 1)
        # pocks: a dark pair with its lower lip lit, on the lit half
        for _ in range(int(rng.integers(1, 3))):
            px, py = int(rng.uniform(x0 + wl + 2, x0 + (x1 - x0) * 0.55)), int(rng.uniform(y0 + tdp + 3, y_bot - 3))
            pk = front & (np.floor(Y) == py) & (X >= px) & (X < px + 2)
            if pk.sum() == 2:
                t0 = int(tone_of(a[py, px]))
                a[pk] = code('stone_warm', max(1, t0 - 2))
                a[np.roll(pk, 1, axis=0) & front] = code('stone_warm', min(5, t0 + 1))
        # the east end: a lit arris column, the core shadow, a reflected rim at the far edge
        ex = (X - (x1 - side)) / max(1, side)
        _codes(a, east, 'stone_cool', np.where(ex < 0.25, 3, np.where(ex < 0.75, 1, 2)) - 0 * fy)
        a[east & (Y == y0 + tdp)] = code('stone_cool', 2)
        # tooling: the front, the top and the west end on sibling ramps at the same tone
        sibling_cells(a, (front | topm | west) & (fam_of(a) == FI['stone_warm']), rng, y0, y_bot, x0, x1,
                      ('stone_warm', 'stone'), share=0.45, step=(3, 6), maxrun=50)
        # the chips' fresh faces: lit where they face up and west, a dark texel where they face east
        for ch in (chip1, chip2):
            faces_up_w = m & (np.roll(ch, 1, axis=0) | np.roll(ch, 1, axis=1))
            faces_e = m & np.roll(ch, -1, axis=1) & ~faces_up_w
            a[faces_up_w] = code('stone_warm', 5)
            a[faces_e] = code('stone_cool', 2)
        a[m & (Y == y_bot - 1)] = code('stone_warm', 1)
        a[m & (Y == y_bot - 1) & (X >= x1 - side)] = code('stone_cool', 1)
        tops.append((x0, x1, y0, tdp))
        y_bot = y0
    if len(tops) > 1:
        # moss in the joint under the upper slab: one larger clump and maybe a smaller one, uneven
        ux0, ux1, uy0, _ = tops[1]
        jy = tops[0][2] + 1
        n1 = int(rng.integers(8, 12))
        s1 = int(ux0 - 4 + rng.uniform(0, 5))
        spans = [(s1, s1 + n1)]
        if rng.random() < 0.8:
            n2 = int(rng.integers(4, 7))
            s2 = int(ux1 - n2 + rng.uniform(-2, 4))
            spans.append((s2, s2 + n2))
        moss_clumps(a, jy, spans, rng)
    return tops[-1][2]

def lamp_glass(a, cx, yb):
    """Lantern glass lit from inside (house-style 5, Glass): the lamp ramp, lamp 1 along the frame's
    shadow and the top, brightening towards the bottom middle where the shard burns."""
    Y, X = grid(a)
    gy0, gy1 = yb - q(48), yb - q(40)
    halfw = q(4.5) - (gy1 - Y) / max(1, gy1 - gy0) * q(0.8)
    cage = (Y >= gy0) & (Y < gy1) & (np.abs(X - cx) < halfw)
    glass = cage & (fam_of(a) != FI['iron'])
    dx = (X - cx) / q(4.0)
    dy = (gy1 - 1 - Y) / max(1, gy1 - gy0)
    _codes(a, glass, 'lamp', np.clip(5.2 - 2.6 * np.sqrt(dx ** 2 * 0.9 + dy ** 2 * 1.3), 2, 5))
    bars = cage & (fam_of(a) == FI['iron'])
    sh = np.roll(bars, 1, axis=1) & glass                                   # the shadow east of each bar
    a[sh] = code('lamp', 1)
    a[glass & (Y < gy0 + 1)] = code('lamp', 1)
    shard = (np.abs(X - cx) + (gy1 - Y) * 0.45 < q(1.2)) & (Y < gy1) & (Y >= gy1 - q(3.2)) & glass
    a[shard] = code('lamp', 5)


def p_waystone_hd(w, h, seed):
    """The waystone at density 3: the same stone (the lit west face, the mid front, the dark east side,
    the rune cut and glowing) weathered as stone: lichen and weathering in sibling clusters, a few
    cracks with a lit lower lip, the arrises chipped; on a base of dressed stone (plinth_hd) with moss
    in clumps in its joint."""
    rng = np.random.default_rng(seed)
    p = _pic(16, 8, up=36, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    plinth_hd(a, cx, yb, rng, slabs=((9.0, 5, 2.2),), moss=False)
    top, bot = yb - q(35), yb - q(4.5)
    half = lambda yy: q(6.2) - (bot - yy) / max(1, bot - top) * q(1.2)
    front = (Y >= top + q(3)) & (Y < bot) & (np.abs(X - cx) < half(Y))
    cap = ellipse_mask(a.shape, cx, top + q(3.2), q(5.2), q(3.2)) & (Y < top + q(3.2))
    sidef = (Y >= top + q(3)) & (Y < bot) & (X >= cx + half(Y)) & (X < cx + half(Y) + q(2.2))
    # chipped arrises (XR2-W3): notches knocked out of the west edge and the cap's rim
    chips = np.zeros(a.shape, bool)
    for k in range(5):
        if k < 3:
            yy = rng.uniform(top + q(5), bot - q(3))
            ex = cx - half(yy)
        else:
            ex = cx + rng.uniform(-q(4), q(3))
            yy = top + q(0.2)
        r_ = rng.uniform(1.6, 2.6)
        chips |= ((X - ex) / r_) ** 2 + ((Y - yy) / (r_ * 1.2)) ** 2 <= 1
    stone = (front | cap | sidef) & ~chips
    # the face: lit west third, mid body, the east third a tone down, the foot a tone down again
    tt = np.full(a.shape, 3.0)
    tt = np.where(X < cx - q(2), 4.0, tt)
    tt = np.where(X > cx + q(3.2), 2.6, tt)
    tt = np.where(Y > bot - q(4), tt - 0.6, tt)
    _codes(a, front & stone, 'stone', tt)
    _codes(a, cap & stone, 'stone', np.where(X > cx + q(1.5), 3, 4))
    a[cap & stone & (Y < top + q(0.8))] = code('stone', 5)
    _codes(a, sidef & stone, 'stone_cool', np.where(Y > bot - q(6), 1, 2))
    # the fresh faces of the chips: lit where they face up and west, a shade texel on their far side
    rim = stone & ndi.binary_dilation(chips, iterations=1)
    a[rim & (X < cx)] = code('stone', 5)
    a[rim & (X >= cx)] = code('stone_cool', 3)
    face = (front | cap) & stone & ~rim
    # the east side in shade, weathered too: sibling clusters a tone apart, a dark seam low down
    sw = ndi.gaussian_filter(np.random.default_rng(seed + 9).random(a.shape), 1.4) > 0.53
    sd = sidef & stone & sw
    a[sd] = FI['stone_cool'] * 8 + np.clip(tone_of(a[sd]) + np.where(Y[sd] < bot - q(10), 1, -1), 0, 5)
    # weathering (XR2-W1): broad stains on the sibling ramps at the same tone (shape, no grain), then
    # clusters of 3 to 6 texels a tone apart, spread unevenly: denser low and on the north-west
    stain = ndi.gaussian_filter(np.random.default_rng(seed + 7).random(a.shape), 2.2)
    sm_ = face & (stain > 0.515)
    a[sm_] = FI['stone_warm'] * 8 + tone_of(a[sm_])
    sm_ = face & (stain < 0.485)
    a[sm_] = FI['stone_cool'] * 8 + tone_of(a[sm_])
    def blobm(px, py, n, rx, ry):
        m_ = np.zeros(a.shape, bool)
        for _ in range(n):
            ox, oy = px + rng.uniform(-rx, rx), py + rng.uniform(-ry, ry)
            m_ |= ((X - ox) / rng.uniform(0.9, 1.6)) ** 2 + ((Y - oy) / rng.uniform(0.6, 1.1)) ** 2 <= 1
        return m_
    # spalls: shallow scars where a flake came off, their upper edge in shade and the lower lip lit
    for _ in range(int(rng.integers(3, 5))):
        px, py = cx + rng.uniform(-q(4.5), q(3)), rng.uniform(top + q(5), bot - q(5))
        rx_, ry_ = rng.uniform(3, 5.5), rng.uniform(1.8, 3)
        sp = (((X - px) / rx_) ** 2 + ((Y - py) / ry_) ** 2 <= 1) & face
        if sp.sum() < 8:
            continue
        a[sp] = FI['stone'] * 8 + np.clip(tone_of(a[sp]) - 1, 1, 5)
        T_, L_, B_, R_ = edges(sp)
        a[(T_ | L_) & sp] = code('stone_cool', 1)
        a[(B_ & ~L_) & sp] = code('stone', 5)
    for _ in range(30):
        # where: weighted to the lower half and the west
        px = cx + q(5.5) * (2 * rng.random() ** 1.4 - 1) * (1 if rng.random() < 0.35 else -1)
        py = bot - (bot - top - q(4)) * rng.random() ** 1.6
        pm = blobm(px, py, int(rng.integers(2, 4)), 1.4, 0.8) & face
        if pm.sum() < 3:
            continue
        f_ = ('stone_warm', 'stone_cool', 'stone')[int(rng.integers(0, 3))]
        a[pm] = FI[f_] * 8 + np.clip(tone_of(a[pm]) + int(rng.choice([-1, -1, 1])), 1, 5)
    # lichen in two tones: pale grey rosettes and a few yellow crusts, low and on the north-west
    for k in range(int(rng.integers(9, 13))):
        px = cx - q(5) + rng.random() * q(8)
        py = top + q(4) + (bot - top - q(8)) * (0.35 + 0.65 * rng.random() ** 0.7)
        pm = blobm(px, py, int(rng.integers(3, 6)), 1.8, 1.0) & face
        if pm.sum() < 3:
            continue
        if k % 3 == 2:
            a[pm] = code('brass', 3)
            a[pm & (Y < py) & (X < px)] = code('brass', 4)
        else:
            a[pm] = code('leaf_cool', 4)
            a[pm & (Y < py) & (X < px)] = code('leaf_cool', 5)
            a[np.roll(pm, 1, axis=0) & face & ~pm] = code('stone_cool', 2)      # its shade under
    # cracks (XR2-W2): two or three wandering cracks, each a dark line with its lit lip on the west
    for (sx_, sy_, n_) in ((cx - q(4.0), top + q(6), q(9)), (cx + q(3.2), bot - q(13), q(7)),
                           (cx - q(1.5), top + q(1.2), q(4)))[:int(rng.integers(2, 4))]:
        cr = _wander(a, int(sx_ + rng.uniform(-2, 2)), int(sy_), int(n_), rng, front | cap) & stone
        lipk = np.roll(cr, -1, axis=1) & stone & ~cr
        a[lipk] = code('stone', 5)
        a[cr] = code('stone_cool', 1)
    # the rune, as before
    rcy = top + q(15)
    pts = [curve(cx + q(0.3), rcy + q(8), cx - q(0.2), rcy - q(3), q(0.8)),
           curve(cx - q(0.2), rcy - q(0.5), cx - q(3.6), rcy - q(6.5), -q(1.2)),
           curve(cx - q(0.1), rcy + q(1.0), cx + q(3.4), rcy - q(5.0), q(1.4)),
           curve(cx + q(0.2), rcy + q(5.5), cx - q(2.8), rcy + q(8.5), q(0.6)),
           curve(cx + q(0.3), rcy + q(5.0), cx + q(3.0), rcy + q(8.0), -q(0.6)),
           curve(cx - q(3.6), rcy - q(6.5), cx - q(2.0), rcy - q(8.0), -q(0.6), n=3)]
    rune_groove(a, pts, front & stone)
    # moss (XR2-W4): clumps in the joint with the base, denser on the shaded east; a clump on the cap
    x_w, x_e = cx - half(bot) - 2, cx + half(bot) + q(2.2) + 2
    span = x_e - x_w
    moss_run(a, x_w + rng.uniform(0, span * 0.1), x_w + span * rng.uniform(0.35, 0.5), int(bot), rng, band=4, cap=2)
    moss_run(a, x_e - span * rng.uniform(0.25, 0.35), x_e, int(bot), rng, band=3, cap=2)
    moss_run(a, cx - q(4.6), cx - q(0.2), int(top + q(2.0)), rng, band=3, cap=2)
    return finish(p)


def p_rubble_hd(w, h, seed, hd=False):
    """Rubble from a broken wall, from the cottages' own stone: irregular lumps with a lit crown, a body
    and a dark underside, sibling clusters, a chipped corner each, a crack on the larger ones and
    mortar still clinging to a broken face (stone_cool 0 to 1); broken slates and a split beam among
    them. Every piece stays inside the picture with a texel to spare."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=h * 0.9, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    H, W = a.shape
    Y, X = grid(a)
    inside = (X >= 3) & (X < W - 3) & (Y >= 3) & (Y < H - 2)
    n = int(w * h / 22) + 4
    items = sorted((rng.random() ** 0.7, rng.uniform(-0.5, 0.5)) for _ in range(n))
    beams = 0
    for fy, fx in items:
        sw = q(rng.uniform(3, 6.5) * (0.7 + 0.5 * fy))
        sh = q(rng.uniform(2.4, 4.2) * (0.7 + 0.5 * fy))
        hump = (1 - (2 * fx) ** 2) * q(h * 0.55)
        x = cx + fx * q(w)
        y = yb - q(h) * (1 - fy) * 0.5 - hump * (1 - fy) - sh / 2
        x = float(np.clip(x, 4 + sw * 0.66, W - 5 - sw * 0.66))
        y = float(np.clip(y, 4 + sh * 0.66, yb - sh * 0.3))
        r = rng.random()
        before = a >= 0
        if r < 0.22:
            ln = q(rng.uniform(4.5, 7.5))
            x0_ = float(np.clip(x - ln / 2, 4, W - 5 - ln))
            pm = slate_shard(a, x0_, y - 2, ln, rng, ('slate', 'slate', 'slate_cool')[int(rng.integers(0, 3))], where=inside)
        elif r < 0.3 and beams < 2:
            beams += 1
            ln = q(rng.uniform(8, 12))
            ang = rng.uniform(-25, -5)
            ca_, sa_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            bx0 = float(np.clip(x - ln * ca_ / 2, 5, W - 6 - ln * ca_))
            by0 = float(np.clip(y + sh / 2, 5 - ln * sa_, H - 4 - q(1.8)))
            pm = board(a, bx0, by0, ln, q(1.8), ang, 'timber_warm', 3, rng, where=inside)
        else:
            f_ = STONES[int(rng.integers(0, len(STONES)))]
            pm = lump(a, x, y, sw / 2, sh * 0.55, f_, rng, base=int(rng.choice([2, 3, 3])), crack=sw >= q(5),
                      lo=1, where=inside)
            if rng.random() < 0.45:
                # mortar still on a broken face: a crust along its lower west side
                mm = pm & (Y > y + sh * 0.1) & (X < x - sw * 0.05) & ~ndi.binary_erosion(pm, iterations=2)
                a[mm] = code('stone_cool', 1)
                a[mm & np.roll(~pm, -1, axis=0)] = code('stone_cool', 0)
        # occlusion: the texels just under the piece, on what lies behind it, a tone down
        under = np.roll(pm, 1, axis=0) & ~pm & before
        _step_down(a, under, 1)
    return finish(p)


def p_coal_hd(w, h, seed, hd=False):
    """A coal bin: a box of boards (4 to 5 texels, on sibling ramps, with joints and nail heads), its rim
    lit on top with the back board's inner wall behind, heaped inside the rim with coal: near-black
    lumps (slate 0 to 2) lit on their upper left, blue-violet glints in pairs; a few lumps spilled at its
    foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=9, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    H, W = a.shape
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    yf0 = yb - q(5.5)                     # the front board's top
    yback = yf0 - q(4.2)                  # the back board's top
    rim = 2
    # the back board: its lit top, its inner face (lit a little, facing the viewer)
    plank_strip(a, x0, yback, x1, yback + rim, rng, base=4, nails=False)
    plank_strip(a, x0 + rim, yback + rim, x1 - rim, yback + rim + q(1.6), rng, base=3, lit=0, dark=0, nails=False)
    # the side boards' tops, west lit, east in shade
    plank_strip(a, x0, yback, x0 + rim, yf0, rng, base=4, along='y', nails=False, lit=0, dark=0)
    plank_strip(a, x1 - rim, yback, x1, yf0, rng, base=2, along='y', nails=False, lit=0, dark=0)
    # the coal: the bed of the heap (dark between the lumps), then lumps back to front
    hx0, hx1 = x0 + rim, x1 - rim
    hc = (hx0 + hx1) / 2.0
    mound = yf0 - q(7.0) * np.sqrt(np.clip(1 - ((X - hc) / ((hx1 - hx0) / 2.0)) ** 2, 0, 1))
    bed = (X >= hx0) & (X < hx1) & (Y >= mound) & (Y < yf0 + 2)       # heaped above the rim, hiding the back board
    _codes(a, bed, 'slate_cool', 0)
    lumps = []
    for _ in range(140):
        lx = rng.uniform(hx0 + 1, hx1 - 1)
        ly = rng.uniform(yf0 - q(7.0), yf0 + 1)
        top_here = yf0 - q(7.0) * math.sqrt(max(0.0, 1 - ((lx - hc) / ((hx1 - hx0) / 2.0)) ** 2))
        if ly < top_here + 1:
            continue
        lumps.append((ly, lx, rng.uniform(2.6, 4.2)))
    for ly, lx, r_ in sorted(lumps):
        f_ = ('slate_cool', 'soot', 'soot')[int(rng.integers(0, 3))]
        m = lump(a, lx, ly, r_, r_ * 0.8, f_, rng, base=0, chip=False, lo=0, hi=3, where=bed | (a < 0) & (Y < yf0) & (X >= hx0) & (X < hx1))
        if m.sum() >= 6 and rng.random() < 0.45:
            # a glint in a pair on the lit upper-left facet
            ys_, xs_ = np.nonzero(m)
            k = int(np.argmin(xs_ + ys_ * 1.2))
            gx, gy = xs_[k] + 1, ys_[k] + 1
            if gx + 1 < W and m[gy, gx] and m[gy, gx + 1]:
                a[gy, gx] = code('slate', 4)
                a[gy, gx + 1] = code('dusk', 3)
    # the front: three boards of 4 to 5 texels under a lit lip
    rows = [yf0, yf0 + 4, yf0 + 8, yf0 + 13, yb + 1]
    for (r0, r1), base in zip(zip(rows, rows[1:]), (3, 3, 3, 2)):
        plank_strip(a, x0, r0, x1, r1, rng, base=base, lit=1, dark=1, joints=(16, 34))
    a[(Y >= yf0) & (Y < yf0 + 1) & (X >= x0) & (X < x1)] = code('timber_warm', 5)       # the lip
    _step_down(a, (X >= x1 - q(1.2)) & (X < x1) & (Y > yf0) & (Y <= yb), 1)                # the east end in shade
    a[(Y == yb) & (X >= x0) & (X < x1)] = code('timber_cool', 1)
    # lumps spilled at its foot
    for sx_ in (x0 - 3.0, x1 + 1.6, x1 + 3.6):
        lump(a, sx_, yb - 0.6, rng.uniform(1.3, 1.8), 1.3, ('slate', 'soot')[int(rng.integers(0, 2))], rng, base=1,
             chip=False, lo=0, hi=3, where=(a < 0))
    return finish(p)


def p_woodpile_hd(w, h, seed):
    """Split logs stacked end on under a cover board: logs of four sizes and split halves packed against a
    dark back wall (no ground through the stack), each end grain lit on its upper left with one ring arc
    and a radial check, a dark bark rim; a split half's flat face lit along its chord, its bark arc dark;
    the board's lit top and front edge, a stake at each end."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=15, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    sx0, sx1 = x0 + q(1.6), x1 - q(1.6)
    sy0, sy1 = yb - q(13), yb
    back = (X >= sx0) & (X < sx1) & (Y >= sy0) & (Y < sy1)
    _codes(a, back, 'timber_cool', 0)
    for _ in range(int(q(w) * q(13) / 40)):                                # bark of logs further in, here and there
        bm = back & ellipse_mask(a.shape, rng.uniform(sx0, sx1), rng.uniform(sy0, sy1), rng.uniform(1.4, 2.6), 1.2)
        a[bm] = code('timber_cool', 1)
    # pack the ends: four radii, back rows first, rows settling where they fit
    placed = []
    radii = (q(1.7), q(2.0), q(2.4), q(2.8))
    for t_ in range(900):
        r_ = float(radii[int(rng.integers(0, 4)) if t_ > 150 else int(rng.integers(2, 4))])
        ex = rng.uniform(sx0 + r_ - 1, sx1 - r_ + 1)
        ey = rng.uniform(sy0 + r_ * 0.92 - 1, sy1 - r_ * 0.92)
        if all((ex - px) ** 2 + ((ey - py) / 0.92) ** 2 >= (r_ + pr - 2.0) ** 2 for px, py, pr in placed):
            placed.append((ex, ey, r_))
    for ex, ey, r_ in sorted(placed, key=lambda t: t[1]):
        ry = r_ * 0.92
        d2 = ((X - ex) / r_) ** 2 + ((Y - ey) / ry) ** 2
        disc = (d2 <= 1) & back
        half = rng.random() < 0.08
        if half:
            ang = rng.uniform(-0.6, 0.6) - math.pi / 2              # the flat face turned up
            nx, ny = math.cos(ang), math.sin(ang)
            disc &= ((X - ex) * nx + (Y - ey) * ny) <= r_ * 0.15
        if not disc.any():
            continue
        inner = disc & (d2 <= (1 - 1.6 / r_) ** 2)
        bark = disc & ~inner
        # bark: lit on the upper left, dark on the lower right
        bl = lam((X - ex) / r_, (Y - ey) / ry, 0.3)
        _codes(a, bark, 'timber_cool', np.where(bl > 0.25, 2, np.where(bl > -0.2, 1, 0)))
        # end grain: a dome lit from the upper left
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        g = 3.6 + 1.6 * lam((X - ex) / r_, (Y - ey) / ry, nz + 0.4)
        _codes(a, inner, 'timber_warm', np.clip(g, 3, 5))
        # one ring arc (the upper-left half of a ring) and the pith
        rr = np.sqrt(d2)
        arc = inner & (np.abs(rr - rng.uniform(0.45, 0.6)) < 0.75 / r_ * 1.4) & (lam((X - ex), (Y - ey), 0) > -0.2 * r_)
        a[arc] = code('timber_warm', 3)
        a[inner & (rr < 0.22)] = code('timber_warm', 3)
        # a radial check from the heart
        ca = rng.uniform(0, 2 * math.pi)
        ck = seg_mask(a.shape, ex, ey, ex + math.cos(ca) * r_ * 0.75, ey + math.sin(ca) * ry * 0.75, 0.5) & inner
        a[ck] = code('timber', 2)
        if half:
            chord = disc & (np.abs((X - ex) * nx + (Y - ey) * ny - r_ * 0.15) < 1.2)
            a[chord] = code('timber_warm', 5)
    # the cover board and the stakes
    prism(a, x0, yb - q(15), x1, yb - q(13), q(0.8), 'timber_warm', 3, side=q(1))
    plank_strip(a, x0, yb - q(15) + q(0.8), x1, yb - q(13), rng, base=3, lit=1, dark=1, nails=False)
    _step_down(a, (X >= x1 - q(1)) & (X < x1) & (Y >= yb - q(15) + q(0.8)) & (Y < yb - q(13)), 1)
    for sx in (x0, x1 - q(1.6)):
        prism(a, sx, yb - q(14), sx + q(1.6), yb, q(0.6), 'timber', 3, side=q(0.6))
    return finish(p)


def fray_pad(a, pad, rng, keep):
    """Ground laid as a sprite meets the lawn as ground meets ground (eastward-edges 4.1, 5.1): no line,
    its edge frayed in a band of 2 to 3 texels in 1-texel steps with a bite of 3 to 4 every cell or so,
    and dark crumbs of the dirt along it. `pad` is the ground's mask, `keep` what stands on it."""
    Y, X = grid(a)
    alive = a >= 0
    dist = ndi.distance_transform_edt(np.pad(alive, 1, constant_values=False))[1:-1, 1:-1]
    n = ndi.gaussian_filter(rng.random(a.shape), 2.2)
    n = (n - n.min()) / max(1e-6, n.max() - n.min())
    thr = 0.6 + 2.6 * n
    cut = pad & ~keep & (dist <= thr)
    # bites, about one a cell along the edge
    edge_ys, edge_xs = np.nonzero(pad & ~keep & (dist <= 1.5))
    for _ in range(max(1, len(edge_ys) // q(16))):
        i = int(rng.integers(0, len(edge_ys)))
        cut |= pad & ~keep & ellipse_mask(a.shape, edge_xs[i] + 0.5, edge_ys[i] + 0.5, rng.uniform(2.2, 3.4), rng.uniform(2.2, 3.4))
    cut = ndi.binary_closing(cut, iterations=1) & pad & ~keep
    a[cut] = -1
    # no spurs: a pad texel with two or fewer pad neighbours across goes
    for _ in range(2):
        rest = (a >= 0) & pad & ~keep
        P = np.pad(a >= 0, 1)
        nb = P[:-2, 1:-1].astype(int) + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]
        a[rest & (nb <= 1)] = -1
    # crumbs of the dirt's darkest tone along the new edge
    rest = (a >= 0) & pad & ~keep
    rim = rest & ~ndi.binary_erosion(a >= 0, iterations=1)
    ys_, xs_ = np.nonzero(rim)
    for _ in range(len(ys_) // 9):
        i = int(rng.integers(0, len(ys_)))
        y_, x_ = ys_[i], xs_[i]
        a[y_, x_:x_ + 2][(a[y_, x_:x_ + 2] >= 0)] = code('earth_cool', 1)
    return (a >= 0) & pad & ~keep


def finish_on_ground(p: Pic, ground) -> Pic:
    """finish() for a picture that lies partly on the ground: the outline closes what stands up, never
    the ground's own edge (eastward-edges 4.1)."""
    tidy(p.a)
    before = p.a >= 0
    outline(p.a)
    new = (p.a >= 0) & ~before
    solid = before & ~ground
    P = np.pad(solid, 1)
    touch = P[:-2, 1:-1] | P[2:, 1:-1] | P[1:-1, :-2] | P[1:-1, 2:]
    p.a[new & ~touch] = -1
    tidy(p.a, passes=1)
    return p


def seedling(a, sx, sy, v, s):
    """One seedling of three kinds, `s` 0 or 1 a texel larger: its shade on the soil to the east, a
    stem, leaves lit on top."""
    fill(a, sx + 1, sy, sx + 3 + s, sy + 1, code('earth', 1))
    if v == 0:          # two leaves, the east one higher
        fill(a, sx - 2 - s, sy - 2, sx, sy - 1, code('leaf', 4))
        fill(a, sx - 2 - s, sy - 1, sx, sy, code('leaf', 2))
        fill(a, sx + 1, sy - 3, sx + 3 + s, sy - 2, code('leaf', 4))
        fill(a, sx + 1, sy - 2, sx + 3 + s, sy - 1, code('leaf', 3))
        fill(a, sx, sy - 2, sx + 1, sy, code('leaf', 2))
    elif v == 1:        # three leaves: a pair and a young one between, upright
        fill(a, sx - 2, sy - 2, sx, sy - 1, code('leaf', 4))
        fill(a, sx + 1, sy - 2, sx + 3, sy - 1, code('leaf', 3))
        fill(a, sx - 2, sy - 1, sx + 3, sy, code('leaf', 2))
        fill(a, sx, sy - 3 - s, sx + 2, sy - 2, code('leaf', 4))
    else:               # a taller shoot leaning east, one leaf at its tip
        fill(a, sx, sy - 3 - s, sx + 1, sy, code('leaf', 2))
        fill(a, sx + 1, sy - 5 - s, sx + 4, sy - 4 - s, code('leaf', 4))
        fill(a, sx + 1, sy - 4 - s, sx + 4, sy - 3 - s, code('leaf', 3))


def p_beds_hd(w, h, seed, scorched=True):
    """Four raised beds behind the hut, joined by the trodden paths between them (so the plot is one
    piece of ground, frayed where it meets the lawn and never outlined): each frame of boards stood on
    edge, on sibling ramps with grain in short irregular streaks, butt joints and nail heads beside them
    (plank_strip), the top edges lit, the south boards' faces below them, the east boards dark, a stake
    at each corner; the soil lower than the boards, in their shadow along its north and west edges,
    worked into ridges with clods between. Dug over: two beds sown with seedlings of three kinds, each a
    texel off the row. Scorched: ash and soot, charred stalks of two texels lit on the west, embers, and
    the frames burnt: char in clusters on the rail tops and ends with lit cracks, the boards nearest the
    ash blistered and split."""
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
    beds = np.zeros(a.shape, bool)
    bw, bh = (w - 6) / 2, (h - 6) / 2
    th = q(1.2)                                                        # board thickness seen from above
    k = 0
    for j in range(2):
        for i in range(2):
            face_h = q(2.2)                                            # the south board's face
            # the rows' depth chosen so the front row's faces end inside the picture, the path between
            # the rows as wide as before
            gap = q(6) - face_h
            hb = (q(h) + 2 - 2 * face_h - gap) // 2
            bx0 = x0 + q(i * (bw + 6))
            by0 = y0 + j * (hb + face_h + gap)
            bx1, by1 = bx0 + q(bw), by0 + hb
            ix0, iy0, ix1, iy1 = bx0 + th, by0 + th, bx1 - th, by1 - th
            inner = (X >= ix0) & (X < ix1) & (Y >= iy0) & (Y < iy1)
            sf = ('soot', 'ash', 'ash') if scorched else ('earth_cool', 'earth', 'earth_warm')
            ry = (Y - iy0) / max(1.0, q(3.0))
            fr = ry - np.floor(ry)
            ridge = 2.6 + 1.2 * np.cos(fr * 2 * math.pi) * 0.9 - 0.6 * (fr > 0.55)
            if scorched:
                ridge = ridge - 0.8 + 0.6 * (pn > 0.8)
            ridge = ridge - 0.9 * ((fr > 0.55) & (np.sin(X * 0.7 + Y * 1.3) > 0.55))
            paint(a, inner, sf, ridge + 0.35 * np.clip(pn, -1.5, 1.5))
            # the inner face of the north board, standing above the soil
            nf_h = q(1.4)
            plank_strip(a, ix0, iy0, ix1, iy0 + nf_h, rng, base=2, lit=1, dark=0, nails=False,
                        fams=('timber_cool', 'timber', 'timber_cool'))
            nf = inner & (Y < iy0 + nf_h)
            shade_ = inner & ~nf & ((Y < iy0 + q(2.4)) | (X < ix0 + q(1.0)))
            _step_down(a, shade_, 1)
            for _ in range(int(bw * bh / 9)):                          # clods and stones in the soil
                px, py = int(rng.uniform(ix0 + 2, ix1 - 3)), int(rng.uniform(iy0 + q(1.8), iy1 - 2))
                fill(a, px, py, px + 2, py + 1, code(sf[2], 4))
                fill(a, px + 1, py + 1, px + 2, py + 2, code(sf[0], 1))
            # the frame: four boards on edge, their tops lit (the north and west most), the east in shade
            rails = []
            # (a board's top edge shows no nails: they are driven through its face into the stakes)
            rails.append(plank_strip(a, bx0, by0 + th, bx0 + th, by1 - th, rng, base=4, along='y', lit=1, dark=1, nails=False))
            rails.append(plank_strip(a, bx1 - th, by0 + th, bx1, by1 - th, rng, base=3, along='y', lit=0, dark=1, nails=False))
            rails.append(plank_strip(a, bx0, by0, bx1, by0 + th, rng, base=4, lit=1, dark=1, nails=False))
            rails.append(plank_strip(a, bx0, by1 - th, bx1, by1, rng, base=4, lit=1, dark=1, nails=False))
            frame = rails[0] | rails[1] | rails[2] | rails[3]
            # the south board's outer face: two boards, the lower a step darker towards the foot
            plank_strip(a, bx0, by1, bx1, by1 + 4, rng, base=3, lit=1, dark=1)
            plank_strip(a, bx0, by1 + 4, bx1, by1 + face_h, rng, base=2, lit=1, dark=1, nails=False)
            face = (X >= bx0) & (X < bx1) & (Y >= by1) & (Y < by1 + face_h)
            _step_down(a, face & (X >= bx1 - th), 1)
            if scorched:
                # char in clusters on the rail tops, most at the ends; a lit crack through each
                spots = [(bx0 + th / 2, by0 + th / 2), (bx1 - th / 2, by1 - th / 2),
                         (rng.uniform(bx0, bx1), by1 + face_h / 2), (rng.uniform(bx0, bx1), by1 + face_h / 2)]
                for _ in range(7):
                    if rng.random() < 0.5:
                        spots.append((rng.uniform(bx0, bx1), rng.choice([by0 + th / 2, by1 - th / 2])))
                    else:
                        spots.append((rng.choice([bx0 + th / 2, bx1 - th / 2]), rng.uniform(by0, by1)))
                for (ccx, ccy) in spots:
                    cm = np.zeros(a.shape, bool)
                    for _ in range(int(rng.integers(2, 5))):
                        ox, oy = rng.uniform(-3.5, 3.5), rng.uniform(-1.5, 1.5)
                        cm |= ellipse_mask(a.shape, ccx + ox, ccy + oy, rng.uniform(1.6, 3.4), rng.uniform(1.2, 2.2))
                    cm &= frame | face
                    core = cm & ndi.binary_erosion(cm, iterations=1)
                    _codes(a, cm, 'timber_cool', 1)
                    _codes(a, core, 'timber_cool', 0)
                    ys_, xs_ = np.nonzero(core)
                    if len(ys_) >= 3:
                        t_ = int(rng.integers(0, len(ys_)))
                        cy_, cx_ = ys_[t_], xs_[t_]
                        horiz = abs(ccy - by0 - th / 2) < 1 or abs(ccy - by1 + th / 2) < 1
                        ln = int(rng.integers(2, 5))
                        crk = (np.abs(Y - cy_ - 0.5) < 0.6) & (X >= cx_) & (X < cx_ + ln) if horiz else \
                              (np.abs(X - cx_ - 0.5) < 0.6) & (Y >= cy_) & (Y < cy_ + ln)
                        a[crk & cm] = code('ash', 4)
                # the boards nearest the ash blistered and split: on the inner arris of the rails
                inner_arris = frame & ndi.binary_dilation(inner, iterations=1) & ~inner
                ys_, xs_ = np.nonzero(inner_arris)
                for _ in range(5):
                    t_ = int(rng.integers(0, len(ys_)))
                    by_, bx_ = ys_[t_], xs_[t_]
                    a[by_ - 1:by_ + 1, bx_:bx_ + 2] = code('timber_cool', 1)          # a blister: lit cap, dark foot
                    a[by_ - 1, bx_] = code('timber', 4)
                for _ in range(2):
                    # a split along the north rail: a dark line with its lit lip over it
                    sx_ = int(rng.uniform(bx0 + q(2), bx1 - q(6)))
                    ln = int(rng.integers(q(1.6), q(3.2)))
                    sy_ = int(by0 + th - 2)
                    a[sy_, sx_:sx_ + ln] = code('timber_cool', 0)
                    a[sy_ - 1, sx_ + 1:sx_ + ln - 1] = code('timber', 4)
            # stakes at the corners: a square post with a lit top and west face
            for sx_ in (bx0 - 1, bx1 - q(1.4) + 1):
                st = (X >= sx_) & (X < sx_ + q(1.4)) & (Y >= by0 - q(2.4)) & (Y < by1 + face_h)
                paint(a, st, ('timber_cool', 'timber', 'timber_warm'), np.where(Y < by0 - q(1.6), 4.4,
                      np.where(X < sx_ + q(0.7), 3.4, 2.0)))
                beds |= st
            beds |= ((X >= bx0) & (X < bx1) & (Y >= by0) & (Y < by1 + face_h))
            # what grows (or what is left)
            if scorched:
                for _ in range(7):                                     # charred stalks: two texels, lit on the west
                    sx, sy = int(rng.uniform(ix0 + 3, ix1 - 4)), int(rng.uniform(iy0 + q(3.5), iy1 - 1))
                    hgt = q(rng.uniform(1.6, 3.2))
                    lean = int(rng.integers(0, 2))
                    fill(a, sx, sy - hgt + 2, sx + 1, sy, code('soot', 3))
                    fill(a, sx + 1, sy - hgt + 2, sx + 2, sy, code('soot', 1))
                    fill(a, sx + lean, sy - hgt, sx + lean + 1, sy - hgt + 2, code('soot', 3))
                    fill(a, sx + lean + 1, sy - hgt, sx + lean + 2, sy - hgt + 2, code('soot', 1))
                    fill(a, sx + 2, sy - 1, sx + 4, sy, code('soot', 0))  # its shade on the ash
                for _ in range(3):                                     # embers
                    ex, ey = int(rng.uniform(ix0 + 2, ix1 - 3)), int(rng.uniform(iy0 + q(2.5), iy1 - 2))
                    fill(a, ex, ey, ex + 2, ey + 2, code('fox', 3))
                    fill(a, ex, ey, ex + 1, ey + 1, code('lamp', 4))
                    fill(a, ex + 1, ey + 2, ex + 3, ey + 3, code('soot', 0))
            elif k in (1, 2):
                for yy in np.arange(iy0 + q(3.2), iy1 - 1, q(3.0)):
                    for xx in np.arange(ix0 + q(1.6), ix1 - q(1.6), q(3.4)):
                        if rng.random() < 0.06:
                            continue                                   # a gap where one failed
                        sx, sy = int(xx + rng.integers(-1, 2)), int(yy + rng.integers(-1, 2))
                        seedling(a, sx, min(sy, int(iy1) - 2), int(rng.integers(0, 3)), int(rng.integers(0, 2)))
            k += 1
    pad = plot & ~beds
    fray_pad(a, pad, rng, beds)
    return finish_on_ground(p, plot & ~beds)


def _wander(a, x, y, n, rng, within, down=True):
    """A hairline crack wandering from (x, y) for n texels, mostly down (or across), a texel aside now
    and then: its mask."""
    m = np.zeros(a.shape, bool)
    H, W = a.shape
    for _ in range(n):
        if 0 <= int(y) < H and 0 <= int(x) < W:
            m[int(y), int(x)] = True
        if down:
            y += 1
            x += int(rng.choice([-1, 0, 0, 1]))
        else:
            x += 1
            y += int(rng.choice([-1, 0, 0, 1]))
    return m & within


PLANTINGS = ('geranium', 'daisy', 'lavender', 'marigold', 'ivy', 'herbs')


def p_flower_tub_hd(w, h, seed):
    """A terracotta trough (XR2-T1..T5): a rolled rim (its top lit, a dark band under it); seen over the
    front lip, the far inner wall lit over a soil band two texels deep with clods; the body shaded as a
    vessel, lit on the west, its body tone, falling to the shade on the east with a reflected rim, the
    belly turning under at the foot; the clay pitted (pockets with a lit lower lip), a hairline crack
    with its lit lip, lime bloom in irregular pale clusters under the rim (a different spread on every
    tub); the foot a dark row, no corner block. Each tub has its own planting (geraniums, daisies,
    lavender, marigolds, trailing ivy or herbs) in leaf clumps of scalloped lobes, lit tips, dark
    pockets between them, in three or four greens."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=11, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    ytop = yb - q(8.2)
    depth = q(3.0)
    yf = ytop + depth                                                   # where the front face begins
    clay = ('clay_cool', 'clay', 'clay')
    # the silhouette: the rim full width, the body tapering a texel to the foot, its corners rounded
    inset = np.where(Y >= yf + 2, np.floor((Y - yf - 2) / max(1, yb - yf - 2) * 1.9), 0)
    body = (X >= x0 + inset) & (X < x1 - inset) & (Y >= ytop) & (Y < yb)
    body &= ~(((X < x0 + 1) | (X >= x1 - 1)) & ((Y < ytop + 1) | (Y >= yb - 1)))
    body &= ~(((X < x0 + 1 + inset) | (X >= x1 - 1 - inset)) & (Y >= yb - 1))
    top = body & (Y < yf)
    front = body & ~top
    u = (X - x0) / max(1, x1 - x0)
    fy = (Y - yf) / max(1, yb - yf)
    crng = np.random.default_rng(seed + 101)                            # the clay's own draws (the planting keeps rng's)
    # XR3-T1: the body as a fired-clay vessel. The light falls across a bellied form: the lit west, the
    # body tone and the shade on the east meet along curves that bow out at the belly, so each boundary
    # steps two or three texels at a time down the face (never a straight vertical edge); a soft lit
    # patch sits on the upper west of the belly; the belly turns under at the foot in a band that
    # deepens towards the east; no tone 0 anywhere on the body (XR3-T3)
    bow = 0.17 * np.clip(1.0 - ((fy - 0.42) * 1.9) ** 2, -0.4, 1.0)
    uc = u - bow
    t = np.select([uc < 0.27, uc < 0.52, uc < 0.78], [4, 3, 2], 1).astype(float)
    t = np.where((uc >= 0.95) & (fy > 0.15) & (fy < 0.8), 2, t)          # the reflected rim
    hl = ((u - 0.15) / 0.075) ** 2 + ((fy - 0.40) / 0.26) ** 2 <= 1.0
    t = np.where(hl, 5, t)                                                # the soft lit patch on the belly
    turn = (yb - 1 - Y) < (1.6 + 2.6 * u)                                 # the belly turning under, deeper east
    t = np.where(turn & (Y < yb - 1), np.maximum(1, t - 1), t)
    t = np.where(Y >= yb - 1, np.where(u < 0.42, 3, 1), t)              # the base row: a reflected light fading in 2 tones
    # XR3-T1: the shade under the rolled rim, three rows deep on the east thinning to one on the west
    # (in 2 to 3 texel steps), a tone down on the west and two on the east: no ruled line
    sd = np.where(u < 0.22, 0, np.where(u < 0.5, 2, 4)) + (crng.random(a.shape[1]) < 0.3)[None, :] * (u > 0.5)
    shade = (Y >= yf + 1) & ((Y - yf - 1) < sd)
    t = np.where(shade, np.maximum(1, t - np.where((u > 0.5) & (Y < yf + 2), 2, 1)), t)
    t = np.where(shade & (u < 0.12), np.maximum(t, 3), t)
    t = np.where(Y < yf + 1, np.where(u < 0.8, 5, 4), t)                 # the roll's lower face, still in the light
    _codes(a, front, 'clay', t)
    a[front & (Y >= yb - 1)] = FI['clay_cool'] * 8 + t[front & (Y >= yb - 1)].astype(int)
    # the rim seen from above: the back rim's top lit, the far inner wall lit over the soil, the front lip
    paint(a, top, clay, 4.0 - 0.9 * u)
    a[top & (Y < ytop + 1)] = code('clay', 5)
    a[top & (Y < ytop + 1) & (u > 0.75)] = code('clay', 4)
    wall = top & (Y >= ytop + 1) & (Y < ytop + 3) & (X >= x0 + 2) & (X < x1 - 2)
    _codes(a, wall, 'clay', np.where(u > 0.72, 3, np.where(Y < ytop + 2, 5, 4)))   # XR3-T4: the far inner wall, lit
    # XR3-T4: the soil, a band two texels deep (its top row lit a step) with clods lit on top
    soil = top & (Y >= ytop + 3) & (Y < ytop + 5) & (X >= x0 + 2) & (X < x1 - 2)
    _codes(a, soil, 'earth_cool', np.where(Y < ytop + 4, 4, 3) - (u > 0.7))
    for _ in range(int(rng.integers(4, 7))):                                     # clods, lit on top
        cx_ = int(rng.uniform(x0 + 3, x1 - 5))
        cm = soil & (X >= cx_) & (X < cx_ + int(rng.integers(2, 4)))
        a[cm & (Y < ytop + 4)] = code('earth', 4)
        a[cm & (Y >= ytop + 4)] = code('earth', 3)
    a[soil & (np.roll(soil, -1, axis=1) == 0)] = code('earth_cool', 1)          # the soil's shade at the east wall
    lip = top & (Y >= ytop + 5)
    paint(a, lip, clay, 5.0 - 1.2 * (u > 0.78))
    a[lip & (X < x0 + 1)] = code('clay', 4)
    # the clay fired unevenly (XR3-T1): a patchwork of clusters of 12 to 30 texels, each on the clay or its
    # cool sibling at the same tone (shape, no value noise); then any one-tone run still over 40 texels is
    # broken by turning one of its clusters to the sibling
    # (the lip and the far wall too: the rolled rim is fired clay as well)
    face = (front | lip | wall) & np.isin(fam_of(a), [FI['clay'], FI['clay_cool']])
    sy_, sx_ = np.mgrid[ytop:yb:4, x0:x1:5]
    seeds = np.stack([sy_.ravel() + crng.uniform(0, 4, sy_.size), sx_.ravel() + crng.uniform(0, 5, sx_.size)], 1)
    d2 = ((Y[..., None] - seeds[:, 0]) / 0.9) ** 2 + (X[..., None] - seeds[:, 1]) ** 2
    cell = np.argmin(d2, axis=2)
    cool = crng.random(len(seeds)) < 0.6
    def sib_of(c):
        return cool[c]
    def break_runs(face):
        for _ in range(400):
            a[face] = (np.where(sib_of(cell), FI['clay_cool'], FI['clay']) * 8 + tone_of(a))[face]
            t_ = tidy(a.copy())                                           # judged as finish() will leave it
            a[face] = t_[face]
            outline(t_)
            tidy(t_, passes=1)
            seen = np.isin(fam_of(t_), [FI['clay'], FI['clay_cool']]) & (t_ >= 0)
            big = []
            for v in np.unique(t_[seen]):
                lab, k = ndi.label((t_ == v) & seen)
                n_ = np.bincount(lab.ravel())
                n_[0] = 0
                big += [(lab == i) & face for i in np.nonzero(n_ > 40)[0]]
            big = [rm for rm in big if rm.any()]
            if not big:
                return
            for rm in big:                                                # turn one of each long run's clusters
                cs = np.bincount(cell[rm], minlength=len(seeds))
                c = int(crng.choice(len(seeds), p=cs / cs.sum()))
                cool[c] = ~cool[c]
    break_runs(face)
    plain = a.copy()
    # clay pits: a dark pocket of two texels, its lower lip lit
    for _ in range(int(rng.integers(2, 4))):
        px, py = int(rng.uniform(x0 + 3, x0 + (x1 - x0) * 0.6)), int(rng.uniform(yf + 3, yb - 3))
        pm_ = front & (np.floor(Y) == py) & (X >= px) & (X < px + 2)
        t0 = int(tone_of(a[py, px]))
        if pm_.sum() == 2 and t0 >= 3:                    # on the lit half only
            a[pm_] = code('clay_cool', t0 - 1)
            a[np.roll(pm_, 1, axis=0) & front] = code('clay', min(5, t0 + 1))
    # a hairline crack from the rim down, its west lip lit
    cxk = int(rng.uniform(x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.8))
    cr = _wander(a, cxk, yf + 1, int(rng.integers(6, 11)), rng, front)
    lipk = np.roll(cr, -1, axis=1) & front & ~cr
    a[lipk] = np.minimum(a[lipk] + 1, (a[lipk] // 8) * 8 + 5)
    a[cr] = code('clay_cool', 1)
    # XR3-T2: lime bloom as ragged pale clusters of 2 to 4 texels, wandering along under the rim and down
    # one side, each tub its own: where the water wept over the lip. No bar, no drips.
    nb = int(rng.integers(1, 3))
    side_ = 'w' if crng.random() < 0.5 else 'e'
    shapes = (((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (1, 1)),
              ((0, 0), (1, 0), (2, 0)), ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1)))
    spots = []
    for _ in range(nb):
        bx_ = int(rng.uniform(x0 + 2, x1 - 12))
        bw_ = int(rng.integers(5, 11))
        x = bx_
        for k in range(0, bw_, 2):
            dep = int(rng.integers(1, 4)) if 0 < k < bw_ - 2 else 1
            if crng.random() < 0.55:
                spots.append((x, yf + 1 + dep + int(crng.integers(0, 2))))
            x += int(crng.integers(2, 5))
    sx0 = x0 + 1 if side_ == 'w' else x1 - 4
    yy = yf + 3
    while yy < yb - 4 and crng.random() < 0.82:                             # down one side, thinning
        spots.append((sx0 + int(crng.integers(0, 3)), yy))
        yy += int(crng.integers(2, 5))
    for (bx, by) in spots:
        for (dx, dy) in shapes[int(crng.integers(0, len(shapes)))]:
            if 0 <= by + dy < a.shape[0] and front[by + dy, bx + dx]:
                t0 = int(tone_of(a[by + dy, bx + dx]))
                if t0 >= 2:                                                 # pale crust, near the clay's own value
                    a[by + dy, bx + dx] = code('plaster', 1 if t0 >= 4 else 0)
    break_runs(face & (a == plain))                                      # again, round the pits, crack and bloom
    # the planting (XR2-T5): its own kind on every tub
    kind = PLANTINGS[(seed + seed // 6 + seed // 50) % len(PLANTINGS)]
    greens = {'geranium': ('leaf_cool', 'leaf', 'leaf_warm'), 'daisy': ('leaf_cool', 'leaf', 'leaf'),
              'lavender': ('leaf_cool', 'leaf_cool', 'leaf'), 'marigold': ('leaf_cool', 'leaf_warm', 'leaf_warm'),
              'ivy': ('leaf_cool', 'leaf_cool', 'leaf'), 'herbs': ('leaf_cool', 'leaf', 'leaf_warm')}[kind]
    nclump = int(rng.integers(4, 7))
    xs = x0 + q(1.0) + (x1 - x0 - q(2.0)) * (np.arange(nclump) + rng.uniform(0.25, 0.75, nclump)) / nclump
    leafm = np.zeros(a.shape, bool)
    for lx in xs:
        ly = ytop + 1.0 - rng.uniform(0, 4.0)
        r = q(rng.uniform(1.6, 2.3))
        # a clump of scalloped lobes: three to five small domes, the higher ones behind
        lobes = [(lx + rng.uniform(-r * 0.9, r * 0.9), ly + rng.uniform(-r * 0.6, r * 0.5), rng.uniform(2.6, 3.8))
                 for _ in range(int(rng.integers(3, 5)))]
        for (ox, oy, rr) in sorted(lobes, key=lambda o: o[1]):
            d = ((X - ox) / rr) ** 2 + ((Y - oy) / (rr * 0.85)) ** 2
            m = (d <= 1) & (Y < yf + 1)
            nx_, ny_ = (X - ox) / rr, (Y - oy) / rr
            tl = 2.0 + 2.4 * lam(nx_, ny_ * 0.8, np.sqrt(np.clip(1 - d, 0, 1)))
            tl = np.where((ny_ > 0.35) & (d > 0.45), 1.0, tl)              # its dark lower edge
            paint(a, m, greens, tl)
            # the pocket where this lobe tucks under its neighbours: dark
            pk = m & leafm & (d > 0.75) & (ny_ < 0)
            a[pk] = code('leaf_cool', 1)
            leafm |= m
        # a lit leaf tip or two, pointing down off the lit lobes
        for _ in range(2):
            tx_, ty_ = int(lx + rng.uniform(-r, r * 0.3)), int(ly - rng.uniform(0, r * 0.6))
            if leafm[ty_, tx_] and leafm[ty_, tx_ + 1]:
                a[ty_, tx_:tx_ + 2] = code(greens[2], 5 if greens[2] != 'leaf_cool' else 4)
    if kind == 'ivy':
        # trailing over the front lip: strands of leaves, 2 texels wide, lit on the west
        for _ in range(int(rng.integers(2, 4))):
            sx_ = int(rng.uniform(x0 + 2, x1 - 4))
            ln = int(rng.integers(4, 9))
            for k in range(ln):
                yy = int(yf - 2 + k)
                xx = sx_ + (k // 3) % 2
                if 0 <= yy < a.shape[0]:
                    a[yy, xx] = code('leaf', 3)
                    a[yy, xx + 1] = code('leaf_cool', 2)
                    leafm[yy, xx:xx + 2] = True
    # the leaves' shade on the rim and the soil below them
    sh = np.roll(leafm, 1, axis=0) & ~leafm & top
    sh |= np.roll(sh, 1, axis=0) & top & ~leafm & (Y >= ytop + 5)
    _step_down(a, sh, 2)
    # the flowers of the kind, each with a lit and a shaded texel
    ys_, xs_ = np.nonzero(leafm & (Y < yf - 1))
    if len(ys_):
        n_fl = {'geranium': 4, 'daisy': 7, 'lavender': 5, 'marigold': 6, 'ivy': 2, 'herbs': 3}[kind]
        for _ in range(n_fl + int(rng.integers(0, 3))):
            i = int(rng.integers(0, len(ys_)))
            fx, fy_ = int(xs_[i]), int(ys_[i]) - 1
            if kind == 'geranium':                                       # a round head of red florets
                fill(a, fx, fy_, fx + 3, fy_ + 2, code('berry', 4))
                fill(a, fx, fy_, fx + 2, fy_ + 1, code('berry', 5))
                fill(a, fx + 1, fy_ + 2, fx + 3, fy_ + 3, code('berry', 2))
            elif kind == 'daisy':                                        # white petals round a yellow eye
                fill(a, fx, fy_, fx + 2, fy_ + 2, code('plaster', 5))
                fill(a, fx + 1, fy_ + 1, fx + 2, fy_ + 2, code('brass', 4))
                fill(a, fx, fy_ + 2, fx + 2, fy_ + 3, code('plaster', 2))
            elif kind == 'lavender':                                     # spikes rising out of the clump
                fill(a, fx, fy_ - 3, fx + 1, fy_ + 1, code('dusk', 4))
                fill(a, fx + 1, fy_ - 2, fx + 2, fy_ + 1, code('dusk', 2))
                fill(a, fx, fy_ - 3, fx + 1, fy_ - 2, code('dusk', 5))
            elif kind == 'marigold':
                fill(a, fx, fy_, fx + 2, fy_ + 2, code('fox', 4))
                fill(a, fx, fy_, fx + 1, fy_ + 1, code('brass', 5))
                fill(a, fx + 1, fy_ + 1, fx + 2, fy_ + 2, code('fox', 2))
            elif kind == 'ivy':
                fill(a, fx, fy_, fx + 2, fy_ + 1, code('plaster', 4))
                fill(a, fx, fy_ + 1, fx + 2, fy_ + 2, code('plaster', 2))
            else:                                                        # herbs: pale flower heads
                fill(a, fx, fy_, fx + 2, fy_ + 1, code('dusk', 5))
                fill(a, fx, fy_ + 1, fx + 2, fy_ + 2, code('berry', 3))
    return finish(p)


# straw in levels 0 (deepest) to 6 (the glint), each with a sibling a strand can take (XR2-H2)
STRAW = ((('timber_warm', 1), ('brass', 1)), (('brass', 1), ('brass_warm', 1)), (('brass', 2), ('brass_warm', 2)),
         (('brass_warm', 3), ('brass', 3)), (('brass', 4), ('brass_warm', 4)), (('brass', 5), ('brass_warm', 5)),
         (('sand_warm', 4), ('sand_warm', 5)))


def _straw(a, m, lv, alt):
    """Write straw levels lv (float, 0 to 6) under mask m, a strand's sibling where alt."""
    li = np.clip(np.round(lv), 0, 6).astype(int)
    for k, ((f0, t0), (f1, t1)) in enumerate(STRAW):
        mk = m & (li == k)
        a[mk & ~alt] = code(f0, t0)
        a[mk & alt] = code(f1, t1)


def p_hay_hd(w, h, seed):
    """A hay bale lying east-west (XR2-H1..H4, the Eastward 17 bale at x1.37): a pillowed volume, its
    top lit and rounding over the front arris in a lit band two or three rows deep, the front falling
    to the shade under it, the corners knocked off two steps; the straw in strand clusters of two or
    three texels in three or four tones of the straw ramp (lit strands over their own shade, in drifts,
    along the bale on the top and the front, in horizontal layers on the front), a few strands breaking
    the silhouette; the east end a cut face (stalk ends in tufts, a core shadow, a lit arris where it
    meets the front); two twines pressed in (a groove with a lit lip of bulging straw beside it) over
    the top, turning over the arris and down the front; straw in tufts at the foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    ytop = yb - q(h + 8)
    edge_y = ytop + q(h)
    side = q(3)
    xe = x1 - side                                                      # where the cut east end begins
    # the silhouette: each flake of the bale (a slice 6 to 9 texels wide) pillows a texel up or not,
    # the corners knocked off two steps (3, 2, 1), the ends bulging a texel at mid height
    cuts = [x0]
    while cuts[-1] < x1:
        cuts.append(cuts[-1] + int(rng.integers(6, 10)))
    cuts[-1] = x1
    lift = np.zeros(a.shape)
    for s_, e_ in zip(cuts, cuts[1:]):
        lift[(X >= s_) & (X < e_)] = int(rng.random() < 0.5)
    body = (X >= x0) & (X < x1) & (Y >= ytop + 1 - lift) & (Y < yb)
    for (ccx, ccy, sx, sy) in ((x0, ytop, 1, 1), (x1 - 1, ytop, -1, 1), (x0, yb - 1, 1, -1), (x1 - 1, yb - 1, -1, -1)):
        dx_, dy_ = (X - ccx - 0.5) * sx, (Y - ccy - 0.5) * sy
        body &= ~((dx_ >= 0) & (dy_ >= 0) & (dx_ + dy_ < 3))
    # the shoulder where the top rounds into the front: the ends pulled in a texel there
    body &= ~(((X < x0 + 1) | (X >= x1 - 1)) & (np.abs(Y - edge_y) < 2))
    bulge = (((X >= x0 - 1) & (X < x0)) | ((X >= x1) & (X < x1 + 1))) & (Y > edge_y + 5) & (Y < yb - 5)
    body |= bulge
    top = body & (Y < edge_y)
    east = body & ~top & (X >= xe)
    front = body & ~top & ~east
    u = (X - x0) / max(1, x1 - x0)
    # the form in straw levels (XR2-H1): the top lit, its back rim catching the light, the last three
    # columns turning away east; the arris a lit band over three rows, the front rounding down from it
    lv = np.zeros(a.shape)
    yt = Y - ytop
    lv = np.where(top, 4.1 - 0.7 * u, lv)
    lv = np.where(top & (yt < 2.5), lv + 0.5, lv)
    lv = np.where(top & (Y >= edge_y - 3), 5.0 - 0.5 * u, lv)            # the lit band at the arris
    lv = np.where(top & (Y >= edge_y - 1), 4.6 - 0.6 * u, lv)
    lv = np.where(top & (X >= x1 - 3), lv - 0.8 - 0.4 * (X - x1 + 3), lv)  # the top turning away east
    fy = (Y - edge_y) / max(1, yb - edge_y)
    lv = np.where(front, 3.3 - 0.6 * u - 1.0 * fy, lv)
    lv = np.where(front & (Y < edge_y + 2), 4.0 - 0.6 * u, lv)            # the shoulder still in the light
    lv = np.where(front & (Y >= yb - 3), 1.3, lv)                          # the belly turning under
    lv = np.where(front & (X < x0 + 2), lv + 0.6, lv)                      # the west end's lit rim
    lv = np.where(body & (Y >= yb - 1), 0.4, lv)                           # the dark foot
    # the east end (XR2-H3): a lit arris where it meets the front, then its core in shade, a reflected
    # rim at the far side
    ex = (X - xe) / max(1, side)
    lv = np.where(east, 1.6 - 0.9 * np.sin(np.clip(ex, 0, 1) * np.pi) + 0.2 * (ex > 0.8), lv)
    lv = np.where(east & (X < xe + 1), 2.8, lv)
    lv = np.where(east & (Y < edge_y + 2), lv + 0.8, lv)
    # horizontal layers on the front: the bale's compressed courses, every 3 or 4 rows a course of its
    # own tone, its edge broken in 2 to 3 texel clusters
    yy = int(edge_y) + 2
    while yy < yb - 3:
        hgt = int(rng.integers(3, 5))
        d_ = rng.choice([-0.5, 0.0, 0.4])
        band = front & (Y >= yy) & (Y < yy + hgt)
        lv = np.where(band, lv + d_, lv)
        # the course's under-edge: a dark seam broken into runs of 2 to 6
        x = x0
        while x < xe:
            ln = int(rng.integers(2, 7))
            if rng.random() < 0.7:
                sm = front & (np.floor(Y) == yy + hgt - 1) & (X >= x) & (X < x + ln)
                lv = np.where(sm, lv - 1.0, lv)
            x += ln + int(rng.integers(1, 4))
        yy += hgt
    # each flake a shade apart on the top, the pillowed ones a touch brighter (no ruled seams)
    for s_, e_ in zip(cuts, cuts[1:]):
        fm = top & (X >= s_) & (X < e_)
        lv = np.where(fm, lv + rng.uniform(-0.3, 0.2) + 0.25 * lift, lv)
    # sibling patches of 3 to 8 texels (the straw's own colour drifting), never single texels
    alt = ndi.gaussian_filter(rng.random(a.shape), 1.6) > 0.51
    # straw strands (XR2-H2): clumps of two or three strands, each 2 to 4 texels along the bale, a lit
    # strand over its own shade, denser in drifts
    drift = ndi.gaussian_filter(rng.random(a.shape), 3.0)
    drift = (drift - drift.min()) / max(1e-6, np.ptp(drift))
    for _ in range(int(w * 10)):
        sx, sy = int(rng.uniform(x0, x1)), int(rng.uniform(ytop, yb - 1))
        if not body[sy, sx] or rng.random() > 0.35 + 0.9 * drift[sy, sx]:
            continue
        on_east = east[sy, sx]
        lit_ = rng.random() < 0.6
        for k in range(int(rng.integers(1, 4))):
            ln = int(rng.integers(2, 4)) if not on_east else 2
            ox = sx + int(rng.integers(-1, 2)) * k
            oy = sy + k * (1 if not on_east else 2)
            if on_east:
                sm = (np.floor(X) >= ox) & (np.floor(X) < ox + 1) & (np.floor(Y) >= oy) & (np.floor(Y) < oy + 2) & east
            else:
                sm = (np.floor(Y) == oy) & (X >= ox) & (X < ox + ln) & body & ~east
            if sm.sum() < 2:
                continue
            dv = (1.0 if lit_ else -1.0) * (0.7 if on_east else 1.0)
            lv = np.where(sm, lv + dv, lv)
            alt |= sm & (rng.random() < 0.5)
            if lit_ and not on_east:
                sh = np.roll(sm, 1, axis=0) & body & ~sm & ~east
                lv = np.where(sh, lv - 0.9, lv)
    # glints: a few strands at the arris band and on the top's west catch the sun
    for _ in range(int(w * 0.4)):
        gx, gy = int(rng.uniform(x0 + 2, x1 - 8)), int(rng.uniform(ytop + 1, edge_y))
        sm = (np.floor(Y) == gy) & (X >= gx) & (X < gx + 2) & top
        if sm.sum() == 2 and lv[gy, gx] >= 4.0:
            lv = np.where(sm, 6.0, lv)
    # the cut stalk ends on the east end: tufts of two texels, the lit ends over a dark pocket
    for _ in range(int(rng.integers(9, 13))):
        tx_, ty_ = int(rng.uniform(xe + 1, x1 - 1)), int(rng.uniform(edge_y + 2, yb - 3))
        tm = east & (np.floor(Y) == ty_) & (X >= tx_) & (X < tx_ + 2)
        if tm.sum() == 2:
            lv = np.where(tm, 2.6 if rng.random() < 0.7 else 3.2, lv)
            lv = np.where(np.roll(tm, 1, axis=0) & east, 0.2, lv)
            alt |= tm & (rng.random() < 0.5)
    _straw(a, body, lv, alt)
    # strands breaking the silhouette: over the back rim, off the east end and the west end
    for _ in range(int(rng.integers(4, 7))):
        sx = int(rng.uniform(x0 + 4, x1 - 4))
        ys_ = int(ytop + 1 - lift[int(ytop) + 2, sx])
        ln = int(rng.integers(1, 3))
        m_ = (X >= sx) & (X < sx + 1 + int(rng.random() < 0.4)) & (Y >= ys_ - ln) & (Y < ys_)
        _straw(a, m_, np.full(a.shape, 4.0 if sx < cx else 3.0), np.zeros(a.shape, bool))
    for _ in range(int(rng.integers(2, 4))):
        sy = int(rng.uniform(edge_y + 3, yb - 4))
        m_ = (Y >= sy) & (Y < sy + 1) & (X >= x1 + (1 if bulge[sy, x1] else 0)) & (X < x1 + 2 + (1 if bulge[sy, x1] else 0))
        _straw(a, m_, np.full(a.shape, 1.0), np.zeros(a.shape, bool))
    for _ in range(int(rng.integers(1, 3))):
        sy = int(rng.uniform(edge_y + 3, yb - 4))
        m_ = (Y >= sy) & (Y < sy + 1) & (X >= x0 - 3) & (X < x0) & (a < 0)
        _straw(a, m_, np.full(a.shape, 3.0), np.zeros(a.shape, bool))
    # the twines (XR2-H4): each pressed into the straw, a groove a texel deep with the straw bulging
    # over it in a lit lip one texel west and its shade east; over the top, brightest where it turns
    # over the arris, down the front in shade; the silhouette dips where it pulls the straw in
    for tx in (x0 + q(w * 0.28), x1 - q(w * 0.36)):
        tx = int(tx)
        wob = np.where(Y < edge_y, 0, 1)                                    # it shifts a texel over the arris
        tw = body & (X >= tx + wob) & (X < tx + wob + 2)
        tt_ = np.where(Y < edge_y - 3, 4, np.where(Y < edge_y + 1, 5, 3))
        tt_ = np.where(Y >= yb - 4, 2, tt_)
        _codes(a, tw, 'timber_warm', tt_)
        a[tw & (X >= tx + wob + 1)] = np.where(Y < edge_y + 1, code('timber_warm', 3), code('timber_warm', 2))[tw & (X >= tx + wob + 1)]
        lipm = body & (X >= tx + wob - 1) & (X < tx + wob) & ~tw
        groove = body & (X >= tx + wob + 2) & (X < tx + wob + 3)
        _straw(a, lipm, np.where(Y < edge_y + 3, 5.0, 3.6), np.zeros(a.shape, bool))
        _straw(a, groove, np.where(Y < edge_y, 1.6, 0.6), np.zeros(a.shape, bool))
        # the straw pulled in at the back rim and the foot: the silhouette dips a texel
        a[(Y < ytop + 2 - lift) & (X >= tx) & (X < tx + 2)] = -1
    # straw in tufts at the foot, lit on the west
    for _ in range(int(rng.integers(3, 6))):
        tx = rng.uniform(x0 - q(1.5), x1 + q(0.6))
        tw_ = int(rng.integers(3, 6))
        tuft = (np.abs(X - tx) < tw_ / 2) & (Y >= yb - 2 - (tw_ / 2 - np.abs(X - tx)) * 0.8) & (Y < yb + 1)
        tuft &= (a < 0) | (Y >= yb - 1)
        tl = np.where(Y >= yb, 1.6, 3.4)
        tl = np.where(X < tx, tl + 1.0, tl)
        _straw(a, tuft, tl, (X.astype(int) % 2) == 0)
    return finish(p)


def grained_front_board(a, m, fam, t, rng):
    """XR4-S2: a board standing on end in the stall's counter front, grained in three tones of its ramp: a
    lit west arris column (t + 1), the body (t) with grain lines (t - 1) that wander down it, break and
    end, a lit ridge (t + 1) beside part of some of them, now and then a knot the grain bends round, the
    foot darkened by splash in a ragged edge, and the dark joint (t - 2) down its east side. Draws over
    mask m (the board's own mask) and returns the mask of its body (no arris, no joint)."""
    ys, xs = np.nonzero(m)
    if not len(ys):
        return m
    bx0, bx1, by0, by1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
    Wb, Hb = bx1 - bx0, by1 - by0
    tt = np.full((Hb, Wb), float(t))
    knot = None
    if Wb >= 7 and rng.random() < 0.55:
        knot = (rng.uniform(Hb * 0.3, Hb * 0.7), rng.uniform(2.6, Wb - 3.6))
    nl = max(2, (Wb - 2) // 3)
    for k in range(nl):
        xc = 1.4 + (k + rng.uniform(0.3, 0.7)) * (Wb - 2.8) / nl
        r0 = int(rng.integers(0, max(1, Hb // 4)))
        r1 = min(Hb, r0 + int(rng.integers(Hb // 2, Hb + 1)))
        ph, amp, per = rng.uniform(0, 2 * np.pi), rng.uniform(0.5, 1.3), rng.uniform(10, 18)
        rid0 = int(rng.uniform(r0, r1))                                  # the lit ridge along part of it
        rid1 = rid0 + int(rng.integers(4, 10)) if rng.random() < 0.7 else rid0
        on, r = True, r0
        while r < r1:
            run = int(rng.integers(5, 13)) if on else int(rng.integers(2, 4))
            for rr in range(r, min(r1, r + run)):
                if not on:
                    continue
                x = xc + amp * np.sin(2 * np.pi * rr / per + ph)
                if knot is not None:                                     # the grain parts round the knot
                    dy, dx = rr - knot[0], x - knot[1]
                    if abs(dy) < 4.5:
                        x += (1 if dx >= 0 else -1) * max(0.0, 2.4 - abs(dx)) * (1 - abs(dy) / 4.5)
                xi = int(round(x))
                if 1 <= xi < Wb - 1:
                    tt[rr, xi] = t - 1
                    if rid0 <= rr < rid1 and xi - 1 >= 1 and tt[rr, xi - 1] == t:
                        tt[rr, xi - 1] = t + 1
            r += run
            on = not on
    if knot is not None:
        ky, kx = knot
        Yl, Xl = np.mgrid[0:Hb, 0:Wb] + 0.5
        dk = ((Xl - kx) / 1.7) ** 2 + ((Yl - ky) / 1.3) ** 2
        tt = np.where(dk <= 1.0, t - 1, tt)
        tt = np.where(dk <= 0.3, t - 2, tt)
        tt = np.where((dk > 1.0) & (dk <= 2.0) & (Xl > kx) & (Yl > ky), t + 1, tt)   # its lip catching light
    for c in range(1, Wb - 1):                                           # splash at the foot, a ragged edge
        dep = int(rng.integers(2, 5)) if c == 1 or rng.random() < 0.45 else dep
        tt[Hb - dep:, c] = np.minimum(tt[Hb - dep:, c], t - 1)
    tt[:, 0] = t + 1
    tt[:, Wb - 1] = t - 2
    ff = np.full((Hb, Wb), FI[fam])
    ff[:, Wb - 1] = FI['timber_cool'] if t - 2 > 0 else FI['timber']    # the joint in the cool shade (XR5-S4:
    #                                                                  its deepest step is timber's, one tone)
    sub = m[by0:by1, bx0:bx1]
    blk_ = a[by0:by1, bx0:bx1]
    blk_[sub] = (ff * 8 + np.clip(tt, 0, 5).astype(int))[sub]
    body = np.zeros(a.shape, bool)
    body[by0:by1, bx0 + 1:bx1 - 1] = sub[:, 1:-1]
    return body


def p_stall_hd(w, h, seed, hd=False):
    """Moss's stall at density 3: the counter of sawn boards on trestles and the posts as before; the
    produce as single round items heaped above the crate rims (each lit on its cap, dark under, a glint);
    the awning a canvas with a top plane rising back and its valance in folds (each panel 4, 3, 2, 1
    across, folding and creased, XR4-S4), its shade on what lies under it a ramp step; the counter-front
    boards and the posts grained (XR4-S2); a framed slate with a chalk plum and its price (XR4-S1); a
    burlap sack slumped at the foot, tied with twine (XR4-S3)."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=36, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    grng = np.random.default_rng(seed + 47)                                   # XR4-S2's own draw: the rest keep theirs
    for xx, t in ((x0, 3), (x1 - q(2.2), 2)):
        beam(a, xx, yb - q(38), xx + q(2.2), yb, rng, 'timber', t, hd=hd)
        # XR4-S2: the post's face grained as the boards are: lines a tone down that wander and break,
        # a lit ridge beside part of one
        k_ = max(1, int(round(q(2.2) * 0.3)))
        yy_ = int(yb - q(38) + grng.integers(2, 8))
        while yy_ < yb - 2:
            ln = int(grng.integers(6, 13))
            gx_ = xx + k_ + int(grng.integers(0, 2))                         # in the face, clear of the shaded side
            seg = (X >= gx_) & (X < gx_ + 1) & (Y >= yy_) & (Y < min(yb - 2, yy_ + ln)) & (a == code('timber', t))
            a[seg] = code('timber', t - 1)
            if grng.random() < 0.4:
                rid = np.roll(seg, -1, axis=1) & (a == code('timber', t))
                a[rid] = code('timber', t + 1)
            yy_ += ln + int(grng.integers(3, 7))
    xx = x0 + q(2.2)
    fronts = []
    while xx < x1 - q(2.2):
        bw = q(rng.uniform(3, 4.2))
        bfam = ('timber', 'timber_warm', 'timber_cool')[int(rng.integers(0, 3))]
        bt = int(rng.choice([2, 3, 3]))
        bm = board(a.copy(), xx, yb - q(1), q(12), bw - 1, -90, bfam, bt, rng)  # its outline (the draw kept)
        fronts.append((grained_front_board(a, bm, bfam, bt, grng), bfam))
        # XR2-S3: nail heads (a lit texel each) at the joint, into the rails behind, the rust varied
        for ny_ in (yb - q(11), yb - q(3.2)):
            rust_ = int(rng.integers(0, 4))
            behind_sack = xx + 1 < x0 + q(3) + q(3.4) + 1 and ny_ > yb - q(3.6) - q(3.4) - q(1.8)
            if not behind_sack:                                           # XR3-S1: none half hidden, its light lost
                nail_head(a, xx + 1, ny_, rust=rust_)
        xx += bw
    cy0, cy1, ctop = yb - q(16.5), yb - q(13), q(1.8)
    prism(a, x0, cy0, x1, cy1, ctop, 'timber_warm', 3, side=q(1))
    # XR2-S4: the counter's top and its front band as sawn boards (sibling ramps, grain in streaks of 2 to
    # 4 texels, butt joints, nail heads beside them), a dark under-lip row and its shade on the boards
    yt0, yf0 = int(round(cy0)), int(round(cy0)) + ctop
    plank_strip(a, x0 + 1, yt0 + 1, x1 - q(1), yf0, rng, base=4, joints=(26, 44), nails=False,
                fams=('timber_warm', 'timber', 'timber_warm'), lit=1, dark=0)
    plank_strip(a, x0 + 1, yf0 + 1, x1 - q(1), int(round(cy1)) - 1, rng, base=3, joints=(22, 40),
                fams=('timber_warm', 'timber', 'timber_warm'), lit=0, dark=1)
    lipr = _rect(a.shape, x0, int(round(cy1)) - 1, x1 - q(1), int(round(cy1))) & (a >= 0)
    a[lipr] = code('timber_warm', 1)
    _step_down(a, _rect(a.shape, x0 + 1, int(round(cy1)), x1 - q(1), int(round(cy1)) + 1), 1)
    # crates of produce: the back of each crate, the heap, then its front slats
    xx = x0 + q(2)
    kinds = (('fox', 3.3, 'apple'), ('leaf', 4.0, 'cabbage'), ('berry', 2.9, 'plum'), ('brass', 3.1, 'pear'))
    for k, (fam, r0, kind) in enumerate(kinds):
        cw = q(w / 4.6)
        rim_y = yb - q(19.5)
        items = []
        nf_ = 3 if kind == 'cabbage' else 4
        for row, n in ((0, nf_ - 1), (1, nf_)):                           # the back row heaped up, the front row
            for j in range(n):
                fx = xx + q(0.6) + (j + (0.5 if row == 0 else 0.0) + 0.5) * (cw - q(1.2)) / nf_ + rng.uniform(-0.7, 0.7)
                rise = 1.5 * (1 - abs((fx - xx - cw / 2) / (cw / 2)))
                fy = rim_y + (0.3 if row else -r0 * 1.1) - rise + rng.uniform(-0.5, 0.5)
                items.append((fy, fx, r0 * rng.uniform(0.9, 1.05)))
        for fy, fx, r in sorted(items):
            d = ((X - fx) / r) ** 2 + ((Y - fy) / (r * 0.9)) ** 2
            m = d <= 1
            nx_, ny_ = (X - fx) / r, (Y - fy) / r
            t = 2.6 + 2.0 * lam(nx_, ny_, np.sqrt(np.clip(1 - d, 0, 1)) * 0.7)
            t = np.where(ny_ > 0.5, np.minimum(t, 1.6), t)
            T_, L_, B_, R_ = edges(m)
            t = np.where(B_ | (R_ & (ny_ > -0.3)), 0.6, t)                   # its dark underside, parting it from the next
            paint(a, m, (fam + '_cool' if fam + '_cool' in FI else fam, fam, fam), t)
            if kind == 'cabbage':
                a[m & (np.abs(X - fx - (Y - fy) * 0.3) < 0.6) & (Y > fy - r * 0.5)] = code('leaf', 2)
            elif kind in ('apple', 'pear'):
                a[m & (np.abs(X - fx) < 0.6) & (Y < fy - r * 0.55)] = code('timber', 2)      # the stalk
            gx, gy = int(fx - r * 0.45), int(fy - r * 0.45)
            if m[gy, gx] and m[gy, gx + 1]:
                a[gy, gx:gx + 2] = code(fam, 5)                                     # the glint
        board(a, xx, rim_y, cw, q(1.8), 0, 'timber', 3, rng, split=False, grain=False)
        board(a, xx, rim_y + q(1.9), cw, q(1.6), 0, 'timber_warm', 2, rng, split=False, grain=False)
        xx += cw + q(1.5)
    # the awning: a top plane rising back over a valance of folds, a scalloped hem
    ay0, ay1 = yb - q(42), yb - q(33)
    tp = ay0 + q(3.2)                                                        # where the top plane meets the valance
    am = (X >= x0 - q(2)) & (X < x1 + q(2)) & (Y >= ay0) & (Y < ay1)
    hem = (Y >= ay1) & (Y < ay1 + q(2.4)) & (X >= x0 - q(2)) & (X < x1 + q(2)) & \
        ((((X - x0) % q(4)) - q(2)) ** 2 / q(2) ** 2 + ((Y - ay1) / q(2.4)) ** 2 <= 1)
    m = am | hem
    stripe = ((X - x0 + q(2)) // q(4)).astype(int) % 2
    us = ((X - x0 + q(2)) % q(4)) / q(4)
    # XR5-S2, S3: each stripe's hanging face is cloth hung in a long fold. Across the fold, west to east: a
    # lit ridge, one column of mid tone, then the deep tone, one column wide, on some stripes two toward the
    # hem; it runs unbroken from under the lit fold-over to the scallop and steps at most a column, once.
    # The stripe's west column is lit and its last 3 columns are the darkest step of its ramp for the full
    # drop. The folds differ stripe to stripe (where they stand, step and widen), and stand where the 2 x 2
    # art grid keeps each part whole (a ridge and its mid column in one cell, the deep strip clear of the
    # east band by a column of body). Per stripe: (east band width, folds), each fold (ridge column at the
    # top, [(row, step)], the row it widens from or None).
    FOLDS = {0: (3, [(5, [], None)]), 1: (3, [(5, [], None)]), 2: (3, [(5, [(9, -1)], 14)]),
             3: (3, [(4, [(8, 1)], None)]), 4: (3, [(4, [(6, 1)], None)]), 5: (3, [(5, [(13, -1)], None)]),
             6: (3, [(5, [(14, -1)], 17)]), 7: (3, [(5, [], None)]), 8: (3, [(4, [(11, 1)], None)]),
             9: (3, [(5, [(10, -1)], 16)])}
    W4 = q(4)
    sid = ((X - x0 + q(2)) // W4).astype(int)
    col = ((X - x0 + q(2)) % W4).astype(int)
    kk = (Y - (tp + 1)).astype(int)
    fold = np.full(a.shape, 3.0)                                                   # the cloth's body
    deep = np.zeros(a.shape, bool)
    for s_, (eb, folds) in FOLDS.items():
        on = sid == s_
        fold[on & (col == 0)] = 4.0                                                # its west edge, lit
        fold[on & (col >= W4 - eb)] = 1.0                                          # the east band, darkest
        deep |= on & (col >= W4 - eb)
        for r0, drifts, wrow in folds:
            rk = r0 + sum(np.where(kk >= dk, dd, 0) for dk, dd in drifts)          # the ridge column by row
            rp = r0 + sum(np.where(kk - 1 >= dk, dd, 0) for dk, dd in drifts)      # and on the row above
            wide = (kk >= wrow) if wrow is not None else np.zeros(a.shape, bool)
            fold[on & (col == rk)] = 4.0
            fold[on & (col == rk + 1)] = 2.0
            # the deep strip, and where the fold steps a column, both columns for that row, so it never breaks
            dm = on & (((col >= np.minimum(rk, rp) + 2) & (col <= np.maximum(rk, rp) + 2)) | (wide & (col == rk + 3)))
            fold[dm] = 1.0
            deep |= dm
    gath = tp + 3 + ((X.astype(int) + sid) % 3 == 0)                                  # the gathered top, lit
    fold = np.where((Y >= tp + 1) & (Y < gath) & ~deep, np.minimum(5, fold + 1), fold)
    # XR2-S2: the top plane in 2 to 3 tones: each stripe's canvas folds over its rib (lit on the west,
    # shading east), the plane rising back a tone darker at its far edge, lit at its front
    ftop = np.select([us < 0.3, us < 0.78], [5.0, 4.0], 3.0)
    rise = np.where((Y - ay0) < (tp - ay0) * 0.4, -1.0, 0.0)
    tt = np.where(Y < tp, np.clip(ftop + rise, 2, 5), fold)
    tt = np.where(Y < ay0 + 1, 3.0, tt)                                         # its far edge, rising back
    tt = np.where((Y >= tp) & (Y < tp + 1), 5.0, tt)                            # the fold-over at the front edge
    hem_d = (((X - x0) % q(4)) - q(2)) ** 2 / q(2) ** 2 + ((Y - ay1) / q(2.4)) ** 2
    rim = m & (Y >= ay1) & (hem_d > 0.55)
    tt = np.where(rim & (tt > 2), tt - 1, tt)                                    # the hem's turned edge (a fold's mid
    #                                                                            and deep columns keep their steps)
    tt = np.clip(tt, 1, 5)
    a[m & (stripe == 0)] = FI['plaster'] * 8 + tt[m & (stripe == 0)].astype(int)
    # XR5-S1: the cream's deep fold keeps the ramp's warmth and chroma (plaster_fold 3, #aa8a5c: L 59, C 30,
    # h 78), never the grey-taupe plaster 1, which read as a stain and as the wall behind
    a[m & (stripe == 0) & (Y >= tp + 1) & (tt <= 1)] = code('plaster_fold', 3)
    a[m & (stripe == 1)] = FI['berry'] * 8 + tt[m & (stripe == 1)].astype(int)
    under = _rect(a.shape, x0, ay1 + q(2.4), x1, ay1 + q(4)) & (a >= 0)
    _step_down(a, under, 1)
    # the price board: a frame of timber round a slate, chalk in broken strokes
    bx0, bx1, by0, by1 = x1 - q(8), x1 - q(1), yb - q(10), yb
    prism(a, bx0, by0, bx1, by1, q(1), 'timber', 3, side=q(1))
    inb = (X >= bx0 + 2) & (X < bx1 - q(1) - 1) & (Y >= by0 + q(1) + 1) & (Y < by1 - 2)
    _codes(a, inb, 'slate', 1)
    a[inb & (Y < by0 + q(1) + 2)] = code('slate', 0)
    a[inb & (X < bx0 + 3)] = code('slate', 0)
    # XR4-S1: the board reads at 1x as a plum and its price: the slate is 15 texels across, too narrow for
    # a word with a true N and a four-column M, so the fruit is drawn in coloured chalk (a round plum lit
    # on its upper left, its cleft and its dark east side, a chalk glint, the stalk and a leaf), and under
    # it the price in fresh chalk, digits 3 wide and 5 tall, underlined in the dimmer chalk; a texel's
    # margin to the frame all round. Over the slate's gaps, the haze of a wiped line in smears.
    crng = np.random.default_rng(seed + 31)
    ix0, ix1 = bx0 + 3, bx1 - q(1) - 1                                       # the slate's inner columns
    iy0 = by0 + q(1) + 3
    GL = {'3': ('###', '..#', '.##', '..#', '###'), 'd': ('..#', '..#', '###', '#.#', '###')}
    pcx, pcy = (ix0 + ix1) / 2 - 0.5, iy0 + 4.6                              # the plum
    haze = inb & (X >= ix0) & (X < ix1) & (((Y >= iy0 + 10) & (Y < iy0 + 12)) | ((Y >= iy0 + 18) & (Y < iy0 + 20)))
    for _ in range(int(crng.integers(4, 7))):                         # smeared along the gaps
        hx, hy = int(crng.uniform(ix0, ix1 - 3)), int(crng.choice([iy0 + 10, iy0 + 18]))
        hm = haze & (np.floor(Y) == hy) & (X >= hx) & (X < hx + int(crng.integers(3, 7)))
        hm |= haze & (np.floor(Y) == hy + 1) & (X >= hx + 1) & (X < hx + int(crng.integers(3, 6)))
        a[hm] = code('slate', 2)
    pr = ((X - pcx) / 3.7) ** 2 + ((Y - pcy) / 3.5) ** 2
    plum = inb & (pr <= 1.0)
    pnx, pny = (X - pcx) / 3.7, (Y - pcy) / 3.5
    pt = 2.2 + 1.6 * lam(pnx, pny, np.sqrt(np.clip(1 - pr, 0, 1)))
    paint(a, plum, ('berry_cool', 'berry', 'berry'), pt, 1, 4)              # as the crate's plums
    cleft = plum & (np.abs(X - pcx - 0.9 - (Y - pcy) * 0.25) < 0.5) & (Y < pcy + 2.4)
    a[cleft] = code('berry', 1)
    a[plum & (np.abs(X - (pcx - 1.4)) < 1.0) & (np.abs(Y - (pcy - 1.6)) < 0.5)] = code('plaster', 5)  # the glint
    a[inb & (np.abs(X - pcx - 0.5) < 0.5) & (Y >= pcy - 5.5) & (Y < pcy - 3.4)] = code('timber', 4)   # the stalk
    leaf_ = inb & (((X - pcx - 2.6) / 1.9) ** 2 + ((Y - pcy + 4.6) / 1.0) ** 2 <= 1.0) & ~plum
    a[leaf_] = code('leaf', 4)
    a[leaf_ & (X > pcx + 3.0)] = code('leaf', 3)

    def write(word, x, y, tone, drop=0.0):
        for ch in word:
            g = GL[ch]
            for dy, row in enumerate(g):
                for dx, c in enumerate(row):
                    if c == '#' and crng.random() >= drop and inb[y + dy, x + dx]:
                        a[y + dy, x + dx] = code('plaster', tone)
            x += len(g[0]) + 1
    py_ = iy0 + 12
    px_ = int(round((ix0 + ix1) / 2 - 3.5))
    write('3d', px_, py_, 5)
    ul = inb & (Y >= py_ + 7) & (Y < py_ + 8) & (X >= px_ - 1) & (X < px_ + 8) & (((X.astype(int) - px_) % 5) != 3)
    a[ul] = code('plaster', 3)
    # the slate itself not one flat field: patches on its cool sibling at the same tone, the chalk dust
    # settled unevenly
    field = inb & (a == code('slate', 1))
    sibling_cells(a, field, crng, int(by0), int(by1), int(bx0), int(bx1), ('slate', 'slate_cool'), share=0.4,
                  step=(4, 4), maxrun=40, keep=inb)
    # XR4-S3: the sack in burlap: a mid tan (sand, its lit cap no higher than tone 3, well under the
    # awning's cream), slumped on the ground (narrow shoulders, its belly wide and low, leaning a little
    # east, a flat base), the weave in staggered 2-texel dashes that wrap with the form, two folds running
    # down from the gathered neck, the neck tied with twine (two turns, a knot and a hanging end), the
    # gathered ears above it, and a contact shadow under its base
    sx, ytop, ybase = x0 + q(3), yb - q(6.0), yb - 1
    # it keeps the old sack's outline where nothing stood behind it, so the stall's silhouette, and with it
    # the ground's shadow and contact shade, stay as they are
    sy0, r0 = yb - q(3.6), q(3.4)
    env = (((X - sx) / r0) ** 2 + ((Y - sy0) / r0) ** 2 <= 1) & (Y > sy0 - r0 * 0.75)
    env |= (np.abs(X - sx) < q(1.4)) & (Y >= sy0 - r0 - q(0.8)) & (Y < sy0 - r0 * 0.7)
    env |= (np.abs(X - sx) < q(1.9)) & (Y >= sy0 - r0 - q(1.8)) & (Y < sy0 - r0 - q(0.8)) & \
        (((X.astype(int) // 2) % 2 == 0) | (Y >= sy0 - r0 - q(1.4)))
    env |= (np.abs(X - sx) < q(1.6)) & (np.abs(Y - (sy0 - r0 - q(0.6))) < 1)
    a_before_sack = a.copy()
    Hs = ybase - ytop
    fy = np.clip((Y - ytop) / Hs, 0, 1)
    hw = np.where(fy < 0.72, 4.6 + 5.6 * np.sin(np.clip(fy / 0.72, 0, 1) * np.pi / 2),
                  10.2 - 3.2 * np.clip((fy - 0.86) / 0.14, 0, 1) ** 2)
    scx = sx + 0.9 * fy
    sm = (Y >= ytop) & (Y < ybase) & (np.abs(X - scx) <= hw)
    snx = (X - scx) / np.maximum(hw, 1)
    sny = fy * 1.6 - 0.9
    snz = np.sqrt(np.clip(1 - snx ** 2, 0, 1))
    st = 1.5 + 1.6 * lam(snx, sny, snz)
    st = np.where(fy > 0.82, st - 0.7 * (fy - 0.82) / 0.18, st)                     # turning under at the slump
    weave = (((X.astype(int) // 2) + (Y.astype(int) // 2)) % 2 == 0) & (Y.astype(int) % 2 == 0)
    st = np.where(weave & (st > 1.5), st - 1.0, st)
    for fx_ in (-0.35, 0.3):                                                        # folds from the neck
        fold = (np.abs(snx - fx_ * (0.4 + 0.6 * fy)) < 0.1) & (fy < 0.75)
        st = np.where(fold, st - 1.0, st)
    stc = np.clip(np.round(st), 0, 3).astype(int)
    sfam = np.where(stc >= 3, FI['sand_warm'], np.where(stc <= 1, FI['sand_cool'], FI['sand']))
    a[sm] = (sfam * 8 + stc)[sm]
    a[sm & (Y >= ybase - 1)] = code('sand_cool', 0)                                 # its base on the ground
    sack_body = sm & (Y < ybase - 1)
    _, _, _, sR = edges(sm)
    a[sR & (X > scx) & (Y < ybase - 1)] = code('sand_cool', 0)                    # its east flank parts it from the boards
    # the contact shadow: under the base and spreading east over the foot of the boards
    cs = (Y >= ybase - 2) & (Y < ybase + 1) & (X >= sx - 6) & (X < sx + 14) & ~sm & (a >= 0)
    _step_down(a, cs, 2)
    under = (Y >= ybase) & (Y < ybase + 1) & (np.abs(X - sx - 1.5) < 7.5) & (a < 0)       # the foot row keeps its line
    a[under] = code('earth_cool', 1)
    # the neck, gathered: narrow, lit on the west, its gathers as dark dashes
    nk = (Y >= ytop - 3) & (Y < ytop) & (np.abs(X - sx) < 3.4)
    nkt = np.where(X < sx - 0.5, 3, 2) - ((X.astype(int) % 2 == 1) & (Y.astype(int) % 2 == 0))
    a[nk] = (np.where(nkt >= 3, FI['sand_warm'], np.where(nkt <= 1, FI['sand_cool'], FI['sand'])) * 8 + nkt)[nk]
    # the ears above the tie, splayed and ragged
    ear = (Y >= ytop - 6) & (Y < ytop - 3) & (np.abs(X - sx) < 2.8 + (ytop - 3 - Y) * 0.6)
    ear &= ~((Y < ytop - 4) & (np.abs(X - sx) < 1.0 + (ytop - 4 - Y)))           # a dip between two ears
    eart = np.where(X < sx - 0.5, 3, 2) - (np.abs(X - sx) < 1.6)
    a[ear] = (np.where(eart >= 3, FI['sand_warm'], np.where(eart <= 1, FI['sand_cool'], FI['sand'])) * 8 + eart)[ear]
    # the twine: two turns round the neck, a knot on the east and its end hanging down the body
    for ty_ in (ytop - 3, ytop - 2):
        tw_ = (np.floor(Y) == ty_) & (np.abs(X - sx) < 3.6)
        a[tw_] = code('timber_warm', 2)
        a[tw_ & (X < sx - 0.5)] = code('timber_warm', 4)
    kn_ = (Y >= ytop - 4) & (Y < ytop - 1) & (X >= sx + 3) & (X < sx + 5)
    a[kn_] = code('timber_warm', 3)
    a[kn_ & (X >= sx + 4) & (Y >= ytop - 3)] = code('timber_warm', 1)
    end_ = (X >= sx + 4) & (X < sx + 5) & (Y >= ytop - 1) & (Y < ytop + 3)
    a[end_] = code('timber_warm', 2)
    allowed = (a_before_sack >= 0) | env
    a[~allowed] = a_before_sack[~allowed]
    left = env & (a < 0)                                                   # what the old outline held and the sack does not
    a[left & (Y >= ybase - 3)] = code('earth_cool', 1)                    # the contact shadow
    a[left & (Y < ybase - 3) & (X < sx)] = code('sand_warm', 3)
    a[left & (Y < ybase - 3) & (X >= sx)] = code('sand', 2)
    sack_body &= a != code('earth_cool', 1)
    # XR4-S2: each front board's body in streaks on its own ramp and one sibling at the same tone (heart
    # and sap wood), long along the grain, until no one-tone run in it is over 50 texels as finish()
    # leaves the picture
    keep = nail_lights(a) | inb
    # the burlap's colour varies in patches (sand and its siblings at the same tone), as the slate's does
    for fams_, tone_ in ((('sand', 'sand_cool'), 2), (('sand_warm', 'sand'), 3)):
        face = sack_body & (tone_of(a) == tone_) & np.isin(fam_of(a), [FI[f] for f in fams_])
        if face.any():
            sibling_cells(a, face, grng, int(ytop), int(ybase), int(sx - 12), int(sx + 13), fams_, share=0.4,
                          step=(4, 4), maxrun=50, keep=keep)
    SIB = {'timber': ('timber_cool', 'timber_warm'), 'timber_warm': ('timber', 'timber_cool'),
           'timber_cool': ('timber', 'timber_warm')}
    for body, bfam in fronts:
        face = body & np.isin(fam_of(a), [FI[bfam]]) & (a >= 0)
        if face.any():
            ys_, xs_ = np.nonzero(face)
            sibling_cells(a, face, grng, int(ys_.min()), int(ys_.max()) + 1, int(xs_.min()), int(xs_.max()) + 1,
                          (bfam,) + SIB[bfam], share=0.3, step=(8, 3), squash=2.4, maxrun=50, keep=keep)
    # XR3-S1: the nail heads keep their lit texel; XR3-S2: the chalk keeps its strokes (the tidy would
    # fill a letter's one-texel counter and take a stroke's lone end)
    finish(p, keep=keep)
    # XR5-S4: one outline tone where the sack and the deep cream meet the air: the sand ramps' edge tone
    # (#3d2d30) and plaster_fold's are drawn in plaster's (#413438), which the stall's cloth already uses
    a = p.a
    edge_fams = [FI[f] for f in ('sand', 'sand_warm', 'sand_cool', 'plaster_fold')]
    a[(a >= 0) & (a % 8 >= 6) & np.isin(a // 8, edge_fams)] = code('plaster', 6)
    # XR5-S1: and no plaster 1 left inside the hanging faces (a lit outline texel in a scallop's notch)
    a[(Y >= tp + 1) & (Y < ay1 + q(1.6)) & (X >= x0 - q(2)) & (a == code('plaster', 1))] = code('plaster', 6)
    return p



def p_cart_hd(w, h, seed, hd=False):
    """The handcart left in the square at density 3 (the fix queue, never independently reviewed):
    a bed of sawn boards seen from above the front (its floor's top plane lit, the side boards laid
    end to end with butt joints and nails, the east end turned away), one iron-tyred wheel on the near
    side (felloe in six jointed segments, six spokes lit on their upper west, an iron-banded hub), its
    two shafts resting on the setts to the west with a crossbar at their tips, a burlap sack and a small
    crate on the bed, each throwing its shade on what lies under it, and occlusion where the parts meet."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=18, side=7)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    # the shafts, far one first (higher, a tone down), resting on the ground west of the bed
    for (ya, yb_, t, th) in ((yb - q(12.0), yb - q(4.2), 2, 3), (yb - q(10.0), yb - q(1.4), 3, 4)):
        xa, xe = x0 + q(3), x0 - q(6.4)
        sm = seg_mask(a.shape, xa, ya, xe, yb_, th / 2.0)
        T_, Lf, B_, R_ = edges(sm)
        _codes(a, sm, 'timber', t)
        a[sm & T_] = code('timber_warm', t + 1)
        a[sm & B_] = code('timber_cool', max(0, t - 2))
        # the shaft's worn grip at its tip
        tip = sm & (X < xe + q(1.6))
        a[tip & ~B_] = code('timber_warm', t + (1 if t < 3 else 0))
    # the crossbar between the tips
    cb = seg_mask(a.shape, x0 - q(5.4), yb - q(4.6), x0 - q(5.0), yb - q(1.6), 1.5)
    _codes(a, cb, 'timber', 2)
    a[cb & edges(cb)[1]] = code('timber', 3)
    # the bed: its floor's top plane over the side boards
    top_y0, top_y1 = yb - q(16.5), yb - q(14.2)
    side_y0, side_y1 = top_y1, yb - q(8.0)
    fl = (X >= x0) & (X < x1) & (Y >= top_y0) & (Y < top_y1)
    # floor boards running front to back, seen from above: each its sibling, the joints dark
    bxs = _bundles_x(x0, x1, rng)
    for i, (ba, bb) in enumerate(bxs):
        m = fl & (X >= ba) & (X < bb)
        fam = TIMBER[int(rng.integers(0, 3))]
        _codes(a, m, fam, 4 - ((ba - x0) / max(1, x1 - x0) > 0.7))
        a[m & (np.floor(X) == ba)] = code('timber', 1)
    a[fl & (np.floor(Y) == top_y0)] = code('timber_warm', 5)                 # the back rail's lit top
    a[fl & (np.floor(Y) == top_y1 - 1)] = code('timber', 2)                  # its front arris turning over
    # the side boards: two courses laid end to end, butt joints and nails (plank_strip)
    mid = (side_y0 + side_y1) // 2
    plank_strip(a, x0, side_y0, x1 - q(1.4), mid, rng, base=3, joints=(16, 30))
    plank_strip(a, x0, mid, x1 - q(1.4), side_y1, rng, base=3, joints=(14, 26), lit=0)
    a[(X >= x0) & (X < x1 - q(1.4)) & (np.floor(Y) == mid)] = code('timber', 1)   # the lap between them
    # the east end of the bed turned away from the light
    ee = (X >= x1 - q(1.4)) & (X < x1) & (Y >= side_y0) & (Y < side_y1)
    _codes(a, ee, 'timber_cool', 1)
    a[ee & (np.floor(X) == x1 - q(1.4))] = code('timber_cool', 2)
    # the frame's corner irons, a lit texel on each
    for ix in (x0, x1 - q(1.4) - 4):
        a[(X >= ix) & (X < ix + 4) & (Y >= side_y0 + 1) & (Y < side_y0 + 5)] = code('iron', 1)
        a[(np.floor(X) == ix) & (np.floor(Y) == side_y0 + 1)] = code('iron', 4)
    # the underside: the bed's shadow on the shafts and the ground under it
    us = (X >= x0 + 2) & (X < x1) & (Y >= side_y1) & (Y < side_y1 + 2) & (a >= 0)
    _step_down(a, us, 1)
    # the load: a burlap sack lying on the bed (west) and a small crate (east)
    scx, scy, rx, ry = x0 + q(w * 0.3), top_y0 - q(2.4), q(4.4), q(3.0)
    nx_, ny_ = (X - scx) / rx, (Y - scy) / ry
    d = nx_ * nx_ + ny_ * ny_
    sm = (d <= 1) & (Y < top_y1 - 1)
    weave = (((X.astype(int) // 2) + (Y.astype(int) // 2)) % 2 == 0) & (Y.astype(int) % 2 == 0)
    st = 2.0 + 1.8 * lam(nx_, ny_ * 0.8, np.sqrt(np.clip(1 - d, 0, 1)))
    st = np.where(np.abs(nx_ - 0.25 - ny_ * 0.3) < 0.09, st - 1.0, st)        # a fold
    stc = np.clip(np.round(st), 0, 4).astype(int)
    sfam = np.where(stc >= 3, FI['sand_warm'], np.where(stc <= 1, FI['sand_cool'], FI['sand']))
    # the weave as a sibling a step cooler at the same tone (texture without speckle)
    sfam = np.where(weave & (sfam == FI['sand_warm']), FI['sand'], np.where(weave & (sfam == FI['sand']), FI['sand_cool'], sfam))
    a[sm] = (sfam * 8 + stc)[sm]
    # its tied neck lying west, the twine turned twice
    nk = (X >= scx - rx - q(2.0)) & (X < scx - rx + 2) & (np.abs(Y - scy - 1) < q(1.1))
    _codes(a, nk & (a >= -1), 'sand', 2)
    a[nk & (Y < scy)] = code('sand_warm', 3)
    for tx in (scx - rx - 1, scx - rx + 1):
        a[(np.floor(X) == int(tx)) & (np.abs(Y - scy - 1) < q(1.1))] = code('timber_warm', 2)
    # its shade on the floor boards east and under it
    sh = (VO_shift(sm, 2, 3) | VO_shift(sm, 3, 0)) & ~sm & fl
    _step_down(a, sh, 1)
    # the crate: boards on its front, its lid lit, its east side in shade, a corner iron
    cx0, cx1 = x1 - q(9.5), x1 - q(2.4)
    ctop, cbot = top_y0 - q(6.4), top_y1 - 1
    top_m, front_m, east_m = box_hd(a, cx0, cx1, ctop, cbot, q(1.6), ('timber_cool', 'timber', 'timber_warm'), base=3.0)
    for k, yy in enumerate(range(int(ctop + q(1.6)) + q(1.6), int(cbot), q(1.6))):
        a[front_m & (np.floor(Y) == yy)] = code('timber', 1)
        a[front_m & (np.floor(Y) == yy + 1) & (X < cx0 + (cx1 - cx0) * 0.6)] = code('timber_warm', 4)
    a[top_m & (np.floor(X) == int((cx0 + cx1) / 2))] = code('timber', 2)    # the lid's two boards
    a[top_m & (np.floor(X) == int((cx0 + cx1) / 2) + 1)] = code('timber_warm', 5)
    for yy in range(int(ctop + q(1.6)) + 3, int(cbot) - 1, 4):                 # the east side's boards
        a[east_m & (np.floor(Y) == yy)] = code('timber_cool', 0)
        a[east_m & (np.floor(Y) == yy + 1)] = code('timber_cool', 2)
    a[(np.floor(X) >= cx1 - q(1.4)) & (np.floor(X) < cx1) & (np.floor(Y) == int(ctop + q(1.6))) & east_m] = code('iron', 3)
    nail_head(a, cx0 + 2, ctop + q(1.6) + 2)
    nail_head(a, cx1 - q(1.4) - 4, ctop + q(1.6) + 2)
    csh = (VO_shift(top_m | front_m | east_m, 2, 3)) & ~(top_m | front_m | east_m) & fl
    _step_down(a, csh, 1)
    # the wheel on the near side: iron tyre, felloe segments, spokes, the hub
    wc = (cx + q(w * 0.14), yb - q(6.2))
    R = q(6.2)
    dx, dy = X - wc[0], Y - wc[1]
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    upl = (dx + dy) < 0                                                      # the upper-left half, lit
    tyre = (r <= R) & (r > R - q(0.9))
    fel = (r <= R - q(0.9)) & (r > R - q(2.3))
    a[tyre] = code('iron', 2)
    a[tyre & upl] = code('iron', 3)
    a[tyre & ((dx + dy) < -R * 0.9) & (r > R - 1.5)] = code('iron', 5)
    a[tyre & ((dx + dy) > R * 0.7)] = code('iron', 1)
    a[fel] = code('timber', 3)
    a[fel & upl & (r > R - q(1.4))] = code('timber_warm', 4)
    a[fel & ~upl] = code('timber', 2)
    a[fel & ((dx + dy) > R * 0.8)] = code('timber_cool', 1)
    seg = np.floor((ang + math.pi) / (math.pi / 3)).astype(int)
    a[fel & ~upl & (seg % 2 == 0)] = code('timber_cool', 2)                 # the segments, each its own piece
    a[tyre & ((dx + dy) > R * 0.7) & (seg % 2 == 1)] = code('iron', 2)
    for k in range(6):                                                       # the felloe's joints
        aj = k * math.pi / 3 + math.pi / 6
        a[fel & (np.abs(((ang - aj + math.pi) % (2 * math.pi)) - math.pi) < 0.5 / max(1.0, r.mean() * 0.0 + R - q(1.6)))] = code('timber_cool', 0)
    inner = r <= R - q(2.3)
    a[inner & (a >= 0) & ~tyre & ~fel] = -1
    hub_r = q(1.7)
    for k in range(6):
        aa = k * math.pi / 3 + 0.25
        ex, ey = wc[0] + math.cos(aa) * (R - q(2.0)), wc[1] + math.sin(aa) * (R - q(2.0))
        spm = seg_mask(a.shape, wc[0], wc[1], ex, ey, 1.4) & inner
        lit = math.cos(aa) * -0.6 + math.sin(aa) * -0.4
        _codes(a, spm, 'timber', 3 if lit > 0.1 else 2)
        T_, Lf, B_, R_ = edges(spm)
        a[spm & (T_ | Lf)] = code('timber_warm', 4)
        a[spm & (B_ | R_)] = code('timber_cool', 1)
    # the ground seen between the spokes is left open; the spokes' meeting at the hub
    hub = r <= hub_r
    a[hub] = code('timber', 2)
    a[hub & upl] = code('timber_warm', 3)
    band = (r <= hub_r) & (r > hub_r - 1.5)
    a[band] = code('iron', 2)
    a[band & upl] = code('iron', 4)
    a[r <= 1.6] = code('iron', 1)
    a[(np.floor(X) == int(wc[0]) - 1) & (np.floor(Y) == int(wc[1]) - 1)] = code('iron', 5)
    # the axle's shade on the bed behind the wheel's top
    wsh = VO_shift(tyre | fel, 0, 2) & ~(tyre | fel | inner) & (Y >= side_y0) & (Y < side_y1) & (a >= 0)
    _step_down(a, wsh, 1)
    return finish(p, keep=nail_lights(a))


def _bundles_x(x0, x1, rng):
    out, x = [], int(x0)
    while x < x1:
        w_ = int(rng.integers(q(2.6), q(3.6) + 1))
        out.append((x, min(int(x1), x + w_)))
        x += w_
    if len(out) > 1 and out[-1][1] - out[-1][0] < q(1.5):
        out[-2] = (out[-2][0], out[-1][1])
        out.pop()
    return out


def VO_shift(m, dy, dx):
    from .volume import _shift
    return _shift(m, dy, dx)


SHARD_LANTERN_STONE = 1113      # one pedestal for both states: the stone never re-rolls when the shard comes home


def p_shard_lantern(w, h, seed, lit=False):
    """The shard lantern (Matt, 13 Nov: "why would i defend a lantern that's so odd"): not street
    furniture but the thing the town was built round, as its lines say ("an iron lantern beside the well,
    older than the town, with a dozen empty cradles"). A plinth of two worn slabs with moss in the joint; a
    stone pedestal of three faces (lit west, front, shaded east) with a base and a capital and a channel
    cut down its front to a small cup at its foot; a brass collar and an iron bowl with a slot over the
    channel; a housing four times the glass of a street lamp: heavy corner posts, an arched head, and
    inside it a floor plate and an iron tree carrying brass cradles (a cup on the stem, one on each arm,
    two more hanging on rods from the head), a ring of cups round an empty middle; a hipped cap of iron
    plates in three planes (lit west, front, shaded east) with hip ribs, standing seams, a riveted eave
    and a brass finial.
    Empty, the glass is dark: the cap's shade at its top, the far posts seen through it, one glint at its
    upper left, and nothing bright where the shard belongs. With the woodland's shard home (`lit`), the
    great shard stands in the middle cradle in the shard's own colours (the dusk ramp of the Undercroft's
    shard round a small pale core), its light fills the glass, tints the frame's inner faces and runs
    down the channel ("light runs down the iron") to pool in the cup, and the other cradles stay empty
    against it: there are more to bring.
    Both states are one picture apart from the glass, the frame's inner faces and the light in the
    channel (the stone is drawn from one fixed seed, not the prop's), so nothing jumps when they swap.
    It keeps inside the lamp's size class (scripts/review/sizes.json: 52 x 178 texels at most)."""
    srng = np.random.default_rng(SHARD_LANTERN_STONE)
    p = _pic(w, h, up=54, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    dxc = X + 0.5 - cx                                      # east of the middle, in texels
    xm = int(cx)                                            # the first column east of the middle
    keep = np.zeros(a.shape, bool)                          # single texels the tidy must leave: rivets, glints

    def band(y0, y1, hw):
        return (Y >= y0) & (Y < y1) & (np.abs(dxc) < hw)

    def put(y, x0, x1, fam, t):
        a[y, x0:x1] = code(fam, t)

    # --- the plinth: two slabs, the lower as wide as the cap's eave -----------------------------------
    top = lamp_plinth_hd(a, cx, yb, np.random.default_rng(SHARD_LANTERN_STONE + 11),
                         slabs=((8.3, 4.0, 2.6), (6.6, 3.6, 2.0)))
    # --- the pedestal: base, shaft of three faces, capital --------------------------------------------
    ped_b = top + 2                                         # it stands on the slab's top plane
    ped_t = ped_b - 28
    shaft = band(ped_t + 4, ped_b - 3, 11)
    west, east = shaft & (dxc < -5), shaft & (dxc >= 5)
    _codes(a, shaft, 'stone_warm', 3)
    _codes(a, west, 'stone_warm', np.where(dxc < -10, 5, 4))
    _codes(a, east, 'stone_cool', np.where(dxc >= 10, 2, 1))        # its far rim catches the square's light
    a[shaft & (dxc >= 5) & (dxc < 6)] = code('stone_cool', 0)       # the arris between front and east
    a[shaft & (dxc >= -5) & (dxc < -4)] = code('stone_warm', 4)     # the front's lit arris
    jy = ped_t + 15                                                 # two drums: a joint, the lower one's lip lit
    a[shaft & (Y == jy)] = code('stone_cool', 1)
    a[shaft & (Y == jy) & (dxc >= 5)] = code('stone_cool', 0)       # the joint carried across the east face
    lip = shaft & (Y == jy + 1) & (dxc < 5)
    a[lip] = FI['stone_warm'] * 8 + np.minimum(5, tone_of(a[lip]) + 1)
    a[shaft & (Y == jy + 1) & (dxc >= 6) & (dxc < 10)] = code('stone_cool', 2)
    sibling_cells(a, shaft & (fam_of(a) == FI['stone_warm']) & (Y != jy), srng, ped_t + 4, ped_b - 3, cx - 11, cx + 11,
                  ('stone_warm', 'stone'), share=0.4, step=(4, 5), maxrun=40)
    # a spall off the east face's lower drum, and a tooling mark on its upper one
    for (sx_, sy_, n_, t_) in ((xm + 7, jy + 5, 2, 0), (xm + 8, jy + 6, 2, 0), (xm + 6, ped_t + 8, 3, 2)):
        put(sy_, sx_, sx_ + n_, 'stone_cool', t_)
    base = band(ped_b - 3, ped_b, 13)
    _codes(a, base, 'stone_warm', np.where(Y == ped_b - 3, 5, np.where(Y == ped_b - 2, 3, 2)) - (dxc >= 6))
    a[base & (dxc >= 9)] = code('stone_cool', 1)
    cap_ = band(ped_t, ped_t + 4, 14)
    _codes(a, cap_, 'stone_warm', np.select([Y == ped_t, Y == ped_t + 1, Y == ped_t + 2], [5, 4, 3], 2) - (dxc >= 6))
    a[cap_ & (dxc >= 10)] = code('stone_cool', 1)
    a[cap_ & (Y == ped_t) & (dxc >= 6)] = code('stone_warm', 4)
    _step_down(a, band(ped_t + 4, ped_t + 6, 11) & (dxc < 5), 1)   # the capital's shade on the shaft
    _step_down(a, band(ped_b, ped_b + 1, 14) & (dxc > -9), 1)      # the pedestal's contact on the slab
    # --- the iron bowl on its brass collar, and the housing's foot ring ---------------------------------
    bowl_t = ped_t - 9
    f = np.clip((ped_t - Y) / 9.0, 0, 1)
    hw_b = 12.0 + 9.0 * f ** 0.6
    bowl = (Y >= bowl_t) & (Y < ped_t) & (np.abs(dxc) < hw_b)
    _codes(a, bowl, 'iron', cyl_tones(dxc / np.maximum(1, hw_b), 3) - (Y >= ped_t - 2))
    collar = bowl & (Y >= ped_t - 2)                                 # the smith's band where iron sits on stone
    ub = dxc / np.maximum(1, hw_b)
    _codes(a, collar, 'brass', np.select([ub < -0.3, ub < 0.35], [5, 4], 2) - 2 * (Y == ped_t - 1))
    ring_b = bowl_t
    ring_t = ring_b - 4
    gy1, gy0 = ring_t, ring_t - 60                                   # the glass: bottom and top rows
    top_t = gy0 - 4
    for (r0, r1) in ((ring_t, ring_b), (top_t, gy0)):
        rg = band(r0, r1, 21)
        _codes(a, rg, 'iron', np.select([Y == r0, Y == r1 - 1], [5, 1], 3) - (dxc >= 8))
    # --- the channel: a slot in the bowl, a groove down the stone to a cup at the foot -------------------
    # its west wall in shade, its floor, its east lip lit; the same cut in both states, and with the shard
    # home the light runs in it, brightest under the housing and stepping down the dusk ramp to the cup
    ch_t, ch_b = bowl_t, ped_b - 3
    rows = np.arange(ch_t, ch_b)
    glow = np.select([rows < ch_t + 3, rows < ped_t + 4, rows < ped_t + 10, rows < ped_t + 20], [9, 5, 4, 3], 2)
    for y_, g_ in zip(rows, glow):
        stone_row = y_ >= ped_t
        if y_ == jy:                                                 # the course joint breaks it
            continue
        if stone_row:
            a[y_, xm - 2] = code('stone_cool', 0)
            a[y_, xm] = code('stone_warm', 5 if y_ < jy else 4)
        elif y_ < ped_t - 2:
            a[y_, xm] = code('iron', 4)
        if lit:
            a[y_, xm - 1] = code('snow', 4) if g_ == 9 else code('dusk', g_)
        else:
            a[y_, xm - 1] = code('stone_cool', 1) if stone_row else code('iron', 0)
    cup_y = ped_b - 3                                                # the cup the channel empties into
    if lit:
        put(cup_y, xm - 2, xm + 2, 'dusk', 2)
        put(cup_y, xm - 1, xm + 1, 'dusk', 4)
        put(cup_y + 1, xm - 2, xm + 2, 'dusk', 2)
    else:
        for y_ in (cup_y, cup_y + 1):
            put(y_, xm - 2, xm - 1, 'stone_cool', 0)
            put(y_, xm - 1, xm + 1, 'stone_cool', 1)
            put(y_, xm + 1, xm + 2, 'stone_warm', 5)
    put(cup_y + 2, xm - 2, xm + 2, 'stone_cool', 0)
    # --- the housing: corner posts, the arched head, the glass -------------------------------------------
    for sx, bt in ((-1, 3), (1, 2)):
        post = (Y >= gy0) & (Y < gy1) & (dxc * sx >= 16) & (dxc * sx < 20)
        u = (dxc - sx * 18.0) / 2.0
        _codes(a, post, 'iron', cyl_tones(u, bt))
    pane = (Y >= gy0) & (Y < gy1) & (np.abs(dxc) < 16)
    arch = gy0 + 9.0 * (np.abs(dxc) / 16.0) ** 2.2                   # the head: a low arch between the posts
    head = pane & (Y < arch)
    _codes(a, head, 'iron', np.where(dxc < 0, 3, 2))
    soffit = head & (Y >= arch - 1.2)
    a[soffit & (dxc < 0)] = code('iron', 1)                          # the arch's underside, in shade
    a[soffit & (dxc >= 0)] = code('iron', 4)                         # ... and where it faces the light
    glass = pane & ~head
    px0, px1 = xm - 16, xm + 16                                      # the pane's columns
    inside = np.zeros(a.shape, bool)                                 # what stands inside, in front of the far glass

    def metal(m, hi, mid, lo):
        """Wrought iron inside the glass: its west and top edges lit, its east and underside dark."""
        m = m & glass
        w_, n_ = m & ~np.roll(m, 1, axis=1), m & ~np.roll(m, 1, axis=0)
        e_, s_ = m & ~np.roll(m, -1, axis=1), m & ~np.roll(m, -1, axis=0)
        a[m] = code('iron', mid)
        a[e_ | s_] = code('iron', lo)
        a[w_ | n_] = code('iron', hi)
        inside[m] = True

    def cradle(x0, yr, wd, deep, hollow):
        """A cradle: a shallow brass cup seen a little from above, x0 its west column, yr its far rim's
        row, wd wide, its body `deep` rows: the far rim, the hollow between the rims (empty: the dark of
        the glass), the lit near rim, the body turning under, a dark underside."""
        k = 1 if lit else 0
        put(yr, x0 + 1, x0 + wd - 1, 'brass', 3 + k)
        put(yr + 1, x0, x0 + wd, 'brass', 3 + k)
        put(yr + 1, x0, x0 + 1, 'brass', 5)
        put(yr + 1, x0 + 1, x0 + 2, 'brass', 4)
        a[yr + 1, x0 + 2:x0 + wd - 2] = hollow
        put(yr + 2, x0, x0 + wd, 'brass', 4 + k)
        put(yr + 2, x0, x0 + 2, 'brass', 5)
        put(yr + 2, x0 + wd - 2, x0 + wd, 'brass', 3 + k)
        for j in range(deep):
            xa, xb = x0 + 1 + j, x0 + wd - 1 - j
            put(yr + 3 + j, xa, xb, 'brass', 2 + k)
            put(yr + 3 + j, xa, xa + max(2, (xb - xa) * 2 // 5), 'brass', 3 + k)
        xa, xb = x0 + 1 + deep, x0 + wd - 1 - deep
        put(yr + 3 + deep, xa, xb, 'brass', 1 + k)
        inside[yr:yr + 4 + deep, x0:x0 + wd] |= a[yr:yr + 4 + deep, x0:x0 + wd] // 8 == FI['brass']
        inside[yr + 1, x0 + 2:x0 + wd - 2] = True

    # where things stand: the floor plate, the tree, the five cups (a ring round the empty middle)
    plate_y = gy1 - 6
    mid_x, mid_y, mid_w = xm - 6, gy1 - 21, 12                       # the middle cradle, on the stem
    side_y, side_w = gy1 - 28, 9                                     # one on each arm
    up_y, up_w = gy1 - 40, 7                                         # two hanging on rods from the head
    wx_side, wx_up = xm - 14, xm - 12
    ex_side, ex_up = 2 * xm - wx_side - side_w, 2 * xm - wx_up - up_w
    tones = (3, 1, 0) if lit else (4, 3, 1)                          # against the shard's light the iron is a shape
    if lit:
        _codes(a, glass, 'dusk', 2)
    else:
        # the empty glass: the cap's shade under the head, then the far side of the housing through it,
        # lighter towards the floor, in broad bands a tone apart that fall the way the glint does
        v = (Y - gy0) - 0.6 * dxc                                   # the shade falls east, as the light does
        bi = np.select([(Y < arch + 4) | (v < 9), v < 20, v < 31, v < 42], [0, 1, 2, 3], 4)
        bg = np.array([code('void', 1), code('slate_cool', 1), code('slate', 1), code('slate_cool', 2), code('slate', 2)])
        a[glass] = bg[bi][glass]
        # the far posts and the far arch, a tone up from what lies behind them
        far = np.array([code('slate_cool', 1), code('slate_cool', 2), code('slate_cool', 2), code('slate', 2), code('slate_cool', 3)])
        for bx in (px0 + 2, px1 - 4):
            fp = glass & (X >= bx) & (X < bx + 2) & (Y >= arch + 3)
            a[fp] = far[bi][fp]
        back = glass & (Y >= arch + 2) & (Y < arch + 3.2) & (np.abs(dxc) < 13)
        a[back] = code('slate_cool', 1)
        # sibling clusters (slate for slate_cool and the other way, the same tone), so no band is one flat run
        swap = {FI['slate']: FI['slate_cool'], FI['slate_cool']: FI['slate']}
        for (sx_, sy_, n_) in ((xm - 6, gy0 + 15, 3), (xm - 5, gy0 + 16, 3), (xm + 4, gy0 + 13, 4), (xm + 5, gy0 + 14, 2),
                               (xm - 3, gy0 + 27, 3), (xm - 2, gy0 + 28, 3), (xm + 7, gy0 + 31, 3), (xm + 6, gy0 + 32, 3), (xm + 2, gy0 + 23, 4), (xm + 3, gy0 + 24, 2),
                               (xm - 7, gy0 + 35, 3), (xm - 6, gy0 + 36, 3), (xm + 1, gy0 + 34, 4), (xm + 2, gy0 + 35, 3),
                               (xm - 2, gy0 + 47, 4), (xm - 1, gy0 + 48, 3), (xm + 6, gy0 + 50, 3), (xm + 6, gy0 + 51, 2)):
            for x_ in range(sx_, sx_ + n_):
                c_ = int(a[sy_, x_])
                if c_ // 8 in swap:
                    a[sy_, x_] = swap[c_ // 8] * 8 + c_ % 8
        a[glass & (dxc >= 14)] = code('void', 1)                     # the east post's shade inside
        a[glass & (Y == gy1 - 1) & (dxc < 14)] = code('slate', 1)    # the sill's lip
    # the floor plate: an iron disc, its far rim catching the light
    plate = glass & ellipse_mask(a.shape, cx, plate_y + 2.5, 10.5, 2.6)
    _codes(a, plate, 'iron', 2)
    a[plate & ~np.roll(plate, 1, axis=0)] = code('dusk', 4) if lit else code('iron', 4)
    a[plate & ~np.roll(plate, -1, axis=0)] = code('iron', 1)
    inside |= plate
    # the tree: a stem from the plate to the middle cup, an arm bending up to each side cup, collars
    # where the arms leave the stem and where the stem stands on the plate; the rods from the head
    stem = (X >= xm - 2) & (X < xm + 2) & (Y >= mid_y + 5) & (Y < plate_y + 1)
    arms = np.zeros(a.shape, bool)
    for sx in (-1, 1):
        ax_ = cx + sx * 9.5
        arms |= seg_mask(a.shape, cx + sx * 2.0, plate_y - 2.5, ax_, plate_y - 7.5, 1.5)
        arms |= (np.abs(X + 0.5 - ax_) < 1.5) & (Y >= side_y + 5) & (Y < plate_y - 7)
    metal(stem | arms, *tones)
    for (cy_, hw_) in ((plate_y - 4, 3), (plate_y - 1, 3)):         # the collars: a lit band over a dark one
        put(cy_, xm - hw_, xm + hw_, 'iron', tones[0])
        put(cy_ + 1, xm - hw_, xm + hw_, 'iron', tones[2])
        inside[cy_:cy_ + 2, xm - hw_:xm + hw_] = True
    for rx in (wx_up + up_w // 2, ex_up + up_w // 2):
        rod = glass & (X == rx) & (Y < up_y + 1)
        a[rod] = code('iron', tones[1])
        a[np.roll(rod, 1, axis=1) & glass] = code('iron', tones[2])
        inside |= rod | (np.roll(rod, 1, axis=1) & glass)
    hollow = code('dusk', 1) if lit else code('void', 1)
    cradle(wx_up, up_y, up_w, 1, hollow)
    cradle(ex_up, up_y, up_w, 1, hollow)
    cradle(wx_side, side_y, side_w, 2, hollow)
    cradle(ex_side, side_y, side_w, 2, hollow)
    if not lit:
        cradle(mid_x, mid_y, mid_w, 2, hollow)
        # one glint on the pane, at its upper left, in two-texel steps; nothing bright where the shard belongs
        for i in range(4):
            gx, gy_ = px0 + 5 - i, gy0 + 10 + 2 * i
            a[gy_:gy_ + 2, gx:gx + 2] = code('slate', 4 if i < 2 else 3)
    else:
        # the great shard in the middle cradle: a violet crystal of three faces and a point, with a small
        # pale core where the faces meet, standing in the cup (the near rim is drawn over its foot)
        sy0, sy1 = mid_y - 29, mid_y + 2
        fy = (Y + 0.5 - sy0) / (sy1 - sy0)
        hw_s = np.select([fy < 0.28, fy < 0.8], [0.8 + 4.8 * (fy / 0.28), 5.6], 5.6 - 3.0 * (fy - 0.8) / 0.2)
        lean = (0.5 - fy) * 3.0                                       # it leans a little east, as it fell
        sh = glass & (fy >= 0) & (fy < 1) & (np.abs(dxc - lean) < hw_s)
        us = (dxc - lean) / np.maximum(0.8, hw_s)
        a[sh] = code('dusk', 4)                                       # the front face
        a[sh & (us < -0.3)] = code('dusk', 5)                         # the face towards the light
        a[sh & (us >= 0.42)] = code('dusk', 3)                        # the east face, turning away
        a[sh & (fy < 0.28) & (us >= -0.05)] = code('dusk', 3)         # the point's east facet
        a[sh & (fy < 0.28) & (us < -0.05)] = code('dusk', 5)
        a[sh & (fy > 0.84)] = code('dusk', 3)                         # its foot, down in the cradle
        a[sh & (fy > 0.84) & (us < -0.3)] = code('dusk', 4)
        ridge = sh & (np.abs(us + 0.3) < 0.2)                         # the heart: the ridge between the faces
        a[ridge & (fy > 0.2) & (fy < 0.7)] = code('snow', 3)
        a[ridge & (fy > 0.28) & (fy < 0.6)] = code('snow', 5)
        a[sh & (us < -0.3) & ~ridge & (fy > 0.28) & (fy < 0.84)] = code('snow', 2)   # the west face, pale with it
        a[sh & ~ndi.binary_erosion(sh) & (us >= 0.42)] = code('dusk', 2)   # its own edge, where it turns from the eye
        # its light on the glass: nearest the crystal brightest, the frame's shade at the top and east
        dist = ndi.distance_transform_edt(~sh)
        halo = glass & ~sh & ~inside
        _codes(a, halo, 'dusk', np.select([dist < 3, dist < 6, dist < 12], [5, 4, 3], 2))
        # the light comes off the crystal's faces in rays: broad wedges a step apart, on the cool sibling,
        # so the glass is lit glass and not a flat violet
        ang = np.arctan2(Y + 0.5 - (sy0 + sy1) / 2.0, dxc - 0.0)
        ray = (np.floor((ang + math.pi) / (math.pi / 7.0)).astype(int) % 2 == 0)
        far = halo & (dist >= 6)
        a[far & ray] = FI['dusk_cool'] * 8 + np.clip(tone_of(a[far & ray]) - 1, 1, 5)
        a[halo & (Y < arch + 3)] = code('dusk', 1)
        a[halo & (dxc >= 14)] = code('dusk_cool', 1)
        a[halo & (dxc < -14) & (Y > arch + 6)] = code('dusk', 3)        # the west pane's edge, lit from inside
        for (gx, gy_) in ((xm - 12, gy0 + 27), (xm + 6, gy0 + 13), (xm + 11, gy0 + 27)):   # glints in pairs
            if halo[gy_, gx] and halo[gy_, gx + 1]:
                put(gy_, gx, gx + 2, 'snow', 4)
        stood = a.copy()
        cradle(mid_x, mid_y, mid_w, 2, hollow)
        a[sh & (Y <= mid_y + 1)] = stood[sh & (Y <= mid_y + 1)]      # it stands in the cup, in front of the far rim
        # the shard's light on the housing: the posts' inner faces, the arch's underside, the sill's top
        a[(Y >= arch + 2) & (Y < gy1) & (X == px0 - 1)] = code('dusk', 4)
        a[(Y >= arch + 2) & (Y < gy1) & (X == px1)] = code('dusk', 2)
        a[soffit & (Y >= arch - 1.2)] = code('dusk', 2)
        a[(Y == gy1) & (np.abs(dxc) < 16)] = code('dusk', 3)
    # --- the cap: iron plates in three planes, hipped; ribs, seams, a riveted eave; a brass finial --------
    roof_b = top_t
    roof_t = roof_b - 27
    eave_t = roof_b - 4
    fr = np.clip((Y + 0.5 - roof_t) / 27.0, 0, 1)
    hw_r = 3.0 + 22.0 * fr ** 1.7
    xf = 1.5 + 7.0 * fr                                              # the front plane's half-width
    roof = (Y >= roof_t) & (Y < roof_b) & (np.abs(dxc) < hw_r)
    planes = roof & (Y < eave_t)
    pw, pf, pe = planes & (dxc <= -xf), planes & (np.abs(dxc) < xf), planes & (dxc >= xf)
    _codes(a, pw, 'iron', 4)
    _codes(a, pf, 'iron', 3)
    _codes(a, pe, 'iron', 2)
    # the plates: one lap across all three planes (a dark line, a lit line under it)
    lap = roof_t + 12
    _step_down(a, planes & (Y == lap), 2)
    lapl = planes & (Y == lap + 1)
    a[lapl] = (a[lapl] // 8) * 8 + np.minimum(5, tone_of(a[lapl]) + 1)
    # standing seams on the front plane, running to the finial: a lit side and a shade side
    for sgn in (-1, 0, 1):
        sx_ = np.floor(cx - 0.5 + sgn * xf * 0.3).astype(int)
        seam = pf & (X == sx_) & ((Y > lap + 1) if sgn else ((Y > roof_t + 4) & (Y < lap)))
        a[seam] = code('iron', 4)
        a[np.roll(seam, 1, axis=1) & pf] = code('iron', 1)
    # the upper east plate turns further from the light
    a[pe & (Y < lap)] = code('iron', 1)
    # the hips: a lit rib on the west one with its shade on the front plane, a dark rib on the east one
    # with a lit line beside it
    wrib = planes & (np.floor(cx - xf).astype(int) == X)
    erib = planes & (np.floor(cx + xf).astype(int) == X)
    a[wrib] = code('iron', 5)
    a[np.roll(wrib, 1, axis=1) & pf & ~wrib] = code('iron', 2)
    a[erib] = code('iron', 0)
    a[np.roll(erib, -1, axis=1) & pf & ~erib] = code('iron', 4)
    # a sheen at each plate's upper left
    for (sx_, sy_, t_) in ((xm - 11, roof_t + 15, 5), (xm + 7, roof_t + 15, 3)):
        a[sy_:sy_ + 2, sx_:sx_ + 2] = code('iron', t_)
    # soot under the finial's collar, rust where the east eave holds the wet: clusters, one tone each
    for (sx_, sy_, n_, fam_, t_) in ((xm, roof_t + 2, 2, 'iron', 1), (xm - 1, roof_t + 3, 3, 'iron', 1), (xm, roof_t + 4, 2, 'iron', 1),
                                     (xm + 15, eave_t - 3, 2, 'brass', 1), (xm + 15, eave_t - 2, 3, 'brass', 1), (xm + 17, eave_t - 1, 3, 'brass', 1),
                                     (xm - 17, eave_t - 1, 3, 'brass', 1), (xm - 16, eave_t - 2, 2, 'brass', 1)):
        row = a[sy_, sx_:sx_ + n_]
        row[row >= 0] = code(fam_, t_)
    # the eave: a rolled edge (a lit line, the band, its underside) with a row of rivets
    eave = roof & (Y >= eave_t)
    ew, ee = eave & (dxc <= -8.5), eave & (dxc >= 8.5)
    ef = eave & ~ew & ~ee
    for m_, (t0, t1, t2) in ((ew, (5, 3, 2)), (ef, (4, 2, 1)), (ee, (3, 2, 1))):
        _codes(a, m_, 'iron', np.select([Y == eave_t, Y < roof_b - 1], [t0, t1], t2))
    a[eave & (X == xm - 9) & (Y > eave_t)] = code('iron', 5)        # the hips' corners on the band
    a[eave & (X == xm + 8) & (Y > eave_t)] = code('iron', 0)
    for rx, t_ in ((xm - 21, 5), (xm - 13, 5), (xm - 5, 4), (xm + 4, 4), (xm + 12, 4), (xm + 20, 4)):
        a[roof_b - 2, rx] = code('iron', t_)                        # a lit head over its shadow
        a[roof_b - 1, rx] = code('iron', 0)
        keep[roof_b - 2:roof_b, rx] = True
    _step_down(a, band(top_t, top_t + 2, 21), 1)                    # the eave's shade on the head ring
    for sx, t in ((-1, 3), (1, 2)):                                 # a bracket under each eave corner
        br = seg_mask(a.shape, cx + sx * 20.5, gy0 + 9, cx + sx * 23.5, top_t + 1, 1.3) & (a < 0)
        a[br] = code('iron', t)
    neck = band(roof_t - 3, roof_t, 2)
    _codes(a, neck, 'iron', np.where(dxc < 0, 4, 2))
    ball = ellipse_mask(a.shape, cx, roof_t - 6.5, 3.6, 3.6)
    _codes(a, ball, 'brass', np.where((dxc < 0) & (Y < roof_t - 6), 5, np.where((dxc >= 1) | (Y >= roof_t - 4), 2, 4)))
    spike = (Y >= roof_t - 18) & (Y < roof_t - 10) & (dxc >= -1) & (dxc < 1)
    a[spike & (dxc < 0)] = code('iron', 4)
    a[spike & (dxc >= 0)] = code('iron', 2)
    # --- close the silhouette --------------------------------------------------------------------------
    # finish()'s last tidy takes an outline texel on a 45 degree slope for a lone pixel, which left the
    # cap's slopes open; so the outline is kept here, and above the housing its east side is closed in
    # the edge tone (an east edge is never broken to the lit tone)
    keep |= (a >= 0) & (fam_of(a) == FI['snow'])
    if not lit:
        keep |= (a == code('slate', 4)) | (a == code('slate', 3))
    tidy(a, keep=keep)
    body = a >= 0
    outline(a)
    line = (a >= 0) & ~body
    a[line & (Y < gy0 + 10) & (dxc > 0) & (tone_of(a) == 1)] = code('iron', 6)
    a[line & (Y < roof_t) & (dxc > 0) & (fam_of(a) == FI['brass'])] = code('brass', 6)
    tidy(a, passes=1, keep=keep | line)
    return p


PROPS_HD = {
    'barrel': p_barrel_hd,
    'cart': p_cart_hd,
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
    # the 8 Nov detail audit's fixes (docs/reviews/2026-11-08-crossroads-placed.md)
    'rubble': p_rubble_hd,
    'coal': p_coal_hd,
    'woodpile': p_woodpile_hd,
    'stall': p_stall_hd,
    'waystone': p_waystone_hd,
    # the shard lantern (13 Nov): the housing that holds the shards, no longer a street lamp
    'lantern': lambda w, h, s: p_shard_lantern(w, h, s, lit=False),
    'lantern_lit': lambda w, h, s: p_shard_lantern(w, h, s, lit=True),
}
