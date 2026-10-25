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
    # sill and its shade
    if sill:
        blk(a, x0 - q(1.6), y1, x1 + q(1.6), y1 + max(3, q(2.0)), 'stone_warm', 4, cut=1)
        sy = y1 + max(3, q(2.0))
        m = _rect(a.shape, x0 - q(1), sy, x1 + q(1), sy + max(2, q(1.0)))
        a[m & (a >= 0)] = np.clip(a[m & (a >= 0)] - 1, (a[m & (a >= 0)] // 8) * 8, None)
    if shutters:
        sw = q(w * 0.42)
        for (sx0, sx1) in ((x0 - fr - sw, x0 - fr), (x1 + fr, x1 + fr + sw)):
            planks(a, sx0, y0, sx1, y1, rng, fams=(paint, paint), base=3, width=w * 0.21, grain=False)
            blk(a, sx0, y0 + (y1 - y0) // 2 - 1, sx1, y0 + (y1 - y0) // 2 + max(2, q(1)), paint, 4, cut=0)
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
            # over a door or a window: [x, y_top, w, h] in world px from the west end and the ground
            x, yt_, ww, hh = args
            x0, x1 = L + q(x - ww / 2), L + q(x + ww / 2)
            y0, y1 = B - q(yt_), B - q(yt_) + q(hh)
            n = max(2, int(hh / 5))
            for k in range(n):
                yy = y0 + int((y1 - y0) * (k + 0.5) / n)
                dy = int(rng.integers(-q(1.5), q(1.5) + 1))
                bar(d, x0 - q(1.5), yy - dy, x1 + q(1.5), yy + dy, q(1.6), ('timber_warm', 'timber')[k % 2], 3)
                for nx in (x0, x1 - 2):
                    fill(d, nx, yy - dy * (1 if nx == x0 else -1) - 1, nx + 2, yy - dy * (1 if nx == x0 else -1) + 1,
                         code('iron', 1))
            bar(d, x0, y1 - q(2), x1, y0 + q(2), q(1.4), 'timber_cool', 3)
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
    """The square's well: a round dry-stone curb, a timber frame with a slate hood and a winch,
    a bucket on its rope. Choked: rubble heaped over the curb, the hood fallen."""
    rng = np.random.default_rng(seed)
    up = 6 if choked else 34
    p = _pic(w, h, up=up + 4, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    rx, ry = q(w / 2), q(h * 0.45)
    cy = yb - ry - q(5)
    # the curb: a ring of stones seen from above the front, its wall below
    ring = ellipse_mask(a.shape, cx, cy, rx, ry)
    wall_m = _rect(a.shape, cx - rx, cy, cx + rx, yb - q(1)) | ring
    wall_m &= ~(ellipse_mask(a.shape, cx, yb - q(1) - ry, rx, ry) == 0) | (_rect(a.shape, 0, 0, a.shape[1], cy))
    front = _rect(a.shape, cx - rx, cy, cx + rx + 1, yb) & (ellipse_mask(a.shape, cx, yb - ry, rx, ry) |
                                                             _rect(a.shape, cx - rx, cy, cx + rx + 1, yb - ry))
    rubble(a, cx - rx, cy, cx + rx, yb, rng, base=3, course=(2.6, 3.4), length=(3.5, 6), where=front, moss=0.3)
    top = ring & ~ellipse_mask(a.shape, cx, cy, rx - q(3), ry - q(2.2))
    rubble(a, cx - rx, cy - ry, cx + rx, cy + ry, rng, base=4, course=(2.0, 2.6), length=(3, 5), where=top, moss=0,
           east_dark=False)
    inner = ellipse_mask(a.shape, cx, cy, rx - q(3), ry - q(2.2))
    a[inner] = code('void', 0)
    if choked:
        stones_heap(a, cx, cy + ry, w * 0.95, h * 0.9, rng, n=16)
        bar(a, cx - rx - q(3), cy + q(2), cx + rx * 0.4, cy - q(7), q(1.3), 'timber_warm', 3)
        bar(a, cx + rx * 0.2, cy + q(3), cx + rx + q(4), cy - q(2), q(1.2), 'timber', 2)
        return finish(p)
    a[inner & _rect(a.shape, 0, cy + ry * 0.2, a.shape[1], a.shape[0])] = code('water_cool', 1)
    # posts, the winch and the hood
    top_y = cy - q(30)
    for sx, t in ((-1, 3), (1, 2)):
        x = cx + sx * (rx - q(2))
        beam(a, x - q(1.2), top_y, x + q(1.2), cy + q(1), rng, 'timber', t)
    bar(a, cx - rx + q(1), top_y + q(10), cx + rx - q(1), top_y + q(10), q(1.3), 'timber_cool', 3)
    fill(a, cx - q(2), top_y + q(10), cx + q(2), top_y + q(10) + 1, code('sand', 3))
    rope_x = cx + q(1)
    fill(a, rope_x, top_y + q(11), rope_x + 1, cy - q(4), code('sand', 2))
    blk(a, rope_x - q(2.4), cy - q(8), rope_x + q(2.6), cy - q(3), 'timber_warm', 3, cut=1)
    fill(a, rope_x - q(2.4), cy - q(6), rope_x + q(2.6), cy - q(5.2), code('iron', 2))
    hm = roof_mask(a.shape, cx - rx - q(4), cx + rx + q(4), top_y - q(9), top_y + q(1), hip=q(5))
    slate_roof(a, hm, cx - rx - q(4), cx + rx + q(4), top_y - q(9), top_y + q(1), rng, row=2.6, width=(3.4, 5.0), moss=0.15)
    return finish(p)


def p_lantern(w, h, seed, lit=False):
    """The shard lantern: a tall iron post on a stone foot, a glass cage on top with a slate hood.
    Lit, the woodland's shard glows pale blue in it."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=58, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    blk(a, cx - q(5), yb - q(5), cx + q(5), yb + 1, 'stone_warm', 3, cut=2)
    blk(a, cx - q(3.5), yb - q(8), cx + q(3.5), yb - q(5), 'stone', 4, cut=1)
    beam(a, cx - q(1.4), yb - q(46), cx + q(1.4), yb - q(8), rng, 'iron', 3)
    for yy in (yb - q(20), yb - q(34)):
        blk(a, cx - q(2.2), yy, cx + q(2.2), yy + q(1.6), 'iron', 4, cut=0)
    gx0, gx1 = cx - q(5), cx + q(5)
    gy0, gy1 = yb - q(58), yb - q(46)
    blk(a, gx0 - q(1), gy1, gx1 + q(1), gy1 + q(2), 'iron', 3, cut=1)
    if lit:
        fill(a, gx0, gy0, gx1, gy1, code('sky', 4))
        blob(a, ellipse_mask(a.shape, cx, (gy0 + gy1) / 2, q(2.2), q(3.6)), 'snow', 5, top=0, left=0, bot=0, right=0)
        fill(a, gx0, gy0, gx1, gy0 + q(2), code('sky', 5))
    else:
        fill(a, gx0, gy0, gx1, gy1, code('slate_cool', 1))
        fill(a, gx0, gy0, gx0 + q(3), gy1, code('slate', 3))
        fill(a, gx0 + q(3), gy0, gx0 + q(4), gy1, code('slate', 2))
    for xx in (gx0, cx - 1, gx1 - q(1)):
        fill(a, xx, gy0, xx + max(2, q(1)), gy1, code('iron', 2))
    hm = roof_mask(a.shape, gx0 - q(2.5), gx1 + q(2.5), gy0 - q(5), gy0 + q(0.5), hip=q(4))
    a[hm] = code('iron', 3)
    a[hm & _rect(a.shape, 0, 0, cx, a.shape[0])] = code('iron', 4)
    fill(a, cx - q(1), gy0 - q(7), cx + q(1), gy0 - q(4.5), code('iron', 3))
    return finish(p)


def p_stall(w, h, seed):
    """Moss's stall: a trestle counter of boards with crates of what the valley still grows,
    a striped awning on two poles, a slate board with the day's prices."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=34, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    # poles
    for xx, t in ((x0, 3), (x1 - q(2), 2)):
        beam(a, xx, yb - q(36), xx + q(2), yb, rng, 'timber', t)
    # counter: front boards, top
    planks(a, x0 + q(2), yb - q(13), x1 - q(2), yb - q(1), rng, base=3, width=3.0)
    blk(a, x0, yb - q(16), x1, yb - q(13), 'timber_warm', 4, cut=1)
    # crates on the counter with produce
    xx = x0 + q(2)
    for k, (fam, t) in enumerate((('fox', 3), ('leaf', 3), ('berry', 3), ('brass', 4))):
        cw = q(w / 4.6)
        blk(a, xx, yb - q(21), xx + cw, yb - q(16), 'timber', 3, cut=0)
        for j in range(4):
            ex = xx + q(1.5) + j * (cw - q(3)) // 3
            blob(a, ellipse_mask(a.shape, ex, yb - q(21.5), q(1.6), q(1.4)), fam, t)
        xx += cw + q(1.5)
    # the awning: stripes, a scalloped hem
    ay0, ay1 = yb - q(40), yb - q(31)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    am = (X >= x0 - q(2)) & (X < x1 + q(2)) & (Y >= ay0 + (1 - (X - x0) / max(1, x1 - x0)) * 0) & (Y < ay1)
    hem = (Y >= ay1) & (Y < ay1 + q(2.2)) & (X >= x0 - q(2)) & (X < x1 + q(2)) & (((X - x0) % q(5)) < q(3.4))
    m = am | hem
    stripe = ((X - x0) // q(4)).astype(int) % 2
    tt = np.where(stripe == 0, 4, 3)
    fam = np.where(stripe == 0, 'plaster', 'berry')
    tt = np.where(Y < ay0 + q(2), tt + 1, tt)
    tt = np.where(Y >= ay1 - q(1.5), tt - 1, tt)
    tt = np.clip(tt, 0, 5)
    sel = m
    a[sel & (fam == 'plaster')] = FI['plaster'] * 8 + tt[sel & (fam == 'plaster')]
    a[sel & (fam == 'berry')] = FI['berry'] * 8 + tt[sel & (fam == 'berry')]
    # the price board leaning at the foot
    blk(a, x1 - q(8), yb - q(9), x1 - q(1), yb, 'slate', 1, cut=1)
    fill(a, x1 - q(6.5), yb - q(7), x1 - q(3), yb - q(6.3), code('plaster', 5))
    fill(a, x1 - q(6.5), yb - q(4.6), x1 - q(2.5), yb - q(3.9), code('plaster', 5))
    return finish(p)


def p_anvil(w, h, seed):
    """The anvil on its oak block: a horned iron body, lit along its face."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=14, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    blk(a, cx - q(5), yb - q(9), cx + q(5), yb, 'timber_cool', 3, cut=2)
    fill(a, cx - q(5), yb - q(9), cx + q(5), yb - q(8), code('timber_warm', 4))
    m = _rect(a.shape, cx - q(3), yb - q(13), cx + q(3), yb - q(9))
    m |= _rect(a.shape, cx - q(7), yb - q(16), cx + q(6), yb - q(13))
    m |= seg_mask(a.shape, cx - q(7), yb - q(14.5), cx - q(11), yb - q(14), q(1.4))
    tt = shade(m, 2)
    tt[_rect(a.shape, cx - q(7), yb - q(16), cx + q(6), yb - q(15)) & m] = 4
    a[m] = FI['iron'] * 8 + tt[m]
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
    """The waystone: a tall dressed stone with a carved rune and lichen, on a low plinth."""
    rng = np.random.default_rng(seed)
    p = _pic(16, 8, up=34, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    blk(a, cx - q(9), yb - q(5), cx + q(9), yb + 1, 'stone_warm', 3, cut=2)
    m = _rect(a.shape, cx - q(6), yb - q(34), cx + q(6), yb - q(4))
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    m &= ~((Y < yb - q(29)) & (np.abs(X - cx) > q(6) - (Y - (yb - q(34))) * 0.9))
    tt = shade(m, 3)
    tt[m & (X > cx + q(2.5))] -= 1
    tt[m & (X < cx - q(4))] += 1
    a[m] = FI['stone'] * 8 + np.clip(tt[m], 0, 5)
    # the rune
    for (x0, y0, x1, y1) in ((0, -28, 0, -14), (-3, -24, 0, -20), (3, -20, 0, -17), (-3, -16, 0, -14)):
        mm = seg_mask(a.shape, cx + q(x0), yb + q(y0), cx + q(x1), yb + q(y1), max(1, q(0.6)))
        a[mm] = code('sky', 3)
    for _ in range(4):
        lx = int(rng.integers(cx - q(5), cx + q(4)))
        ly = int(rng.integers(yb - q(30), yb - q(8)))
        fill(a, lx, ly, lx + q(2), ly + q(1.3), code('grass', 4))
    return finish(p)


def p_crate(w, h, seed, stack=1):
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=12 * stack, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    for s in range(stack):
        bw = q(w) - s * q(3)
        x0 = cx - bw // 2 + s * q(1)
        y1 = yb - s * q(11)
        y0 = y1 - q(11)
        planks(a, x0, y0, x0 + bw, y1, rng, base=3, width=2.6, vertical=False, grain=False)
        for xx in (x0, x0 + bw - q(2)):
            fill(a, xx, y0, xx + q(2), y1, code('timber', 2 if xx > x0 else 3))
        fill(a, x0, y0, x0 + bw, y0 + q(2.6), code('timber_warm', 4))
        fill(a, x0, y0 + q(2.6), x0 + bw, y0 + q(2.6) + 1, code('timber', 1))
    return finish(p)


def p_barrel(w, h, seed):
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=13, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    r = q(w / 2)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    m = (np.abs(X - cx) < r * (0.86 + 0.14 * np.sin(np.clip((yb - Y) / max(1, q(15)), 0, 1) * math.pi))) & (Y >= yb - q(15)) & (Y < yb)
    tt = np.full(a.shape, 3)
    tt[X < cx - r * 0.4] = 4
    tt[X > cx + r * 0.45] = 2
    a[m] = FI['timber'] * 8 + tt[m]
    for yy in (yb - q(13), yb - q(4)):
        mm = m & (Y >= yy) & (Y < yy + q(1.4))
        a[mm] = code('iron', 2)
        a[mm & (X < cx - r * 0.3)] = code('iron', 3)
    top = ellipse_mask(a.shape, cx, yb - q(15), r * 0.92, q(2.2))
    a[top] = code('timber_warm', 4)
    a[top & ellipse_mask(a.shape, cx + q(0.6), yb - q(14.6), r * 0.6, q(1.2))] = code('timber_warm', 3)
    return finish(p)


def p_trough(w, h, seed):
    """The quench trough: a stone tank of dark water by the anvil."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=7, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    rubble(a, x0, yb - q(8), x1, yb, rng, base=3, course=(2.6, 4), length=(4, 7), moss=0.3)
    blk(a, x0, yb - q(h + 8), x1, yb - q(7), 'stone_warm', 4, cut=2)
    fill(a, x0 + q(2), yb - q(h + 6), x1 - q(2), yb - q(9), code('water_cool', 1))
    fill(a, x0 + q(2), yb - q(h + 6), x1 - q(2), yb - q(h + 5), code('water', 0))
    fill(a, x0 + q(4), yb - q(h + 3), x0 + q(9), yb - q(h + 2.3), code('water', 3))
    return finish(p)


def p_coal(w, h, seed):
    """A coal heap in a board bin."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=8, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    stones_heap(a, cx, yb - q(2), w * 0.9, h * 0.8, rng, n=18, fams=('soot', 'soot', 'iron'), slates=False, planks_=False)
    planks(a, x0, yb - q(5), x1, yb, rng, base=3, width=2.5, vertical=False, grain=False)
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
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=13, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    for xx in (cx - q(6), cx + q(4)):
        beam(a, xx, yb - q(7), xx + q(2), yb, rng, 'timber', 3 if xx < cx else 2)
    beam(a, cx - q(7), yb - q(8), cx + q(7), yb - q(6), rng, 'timber', 3)
    m = ellipse_mask(a.shape, cx, yb - q(10), q(5), q(5))
    a[m] = code('stone_warm', 3)
    a[m & ellipse_mask(a.shape, cx - q(1), yb - q(11), q(3.5), q(3.5))] = code('stone_warm', 4)
    fill(a, cx - 1, yb - q(11), cx + 1, yb - q(9), code('iron', 1))
    return finish(p)


def p_hay(w, h, seed):
    """A hay bale on the hay slope: lit straw, twine bands."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    blk(a, x0, yb - q(h + 8), x1, yb, 'sand', 3, cut=2)
    fill(a, x0 + 2, yb - q(h + 8) + 1, x1 - 2, yb - q(8), code('sand', 4))
    for _ in range(int(w * 1.5)):
        sx = int(rng.integers(x0 + 2, x1 - 2))
        sy = int(rng.integers(yb - q(h + 7), yb - 3))
        fill(a, sx, sy, sx + 1, sy + q(1.6), code('sand', 2 if sy > yb - q(8) else 3))
    for xx in (x0 + q(w * 0.3), x1 - q(w * 0.3)):
        fill(a, xx, yb - q(h + 8), xx + 2, yb, code('timber_warm', 2))
    return finish(p)


def p_bench(w, h, seed):
    """A plank bench on two stone legs."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=8, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    for xx in (x0 + q(2), x1 - q(6)):
        blk(a, xx, yb - q(6), xx + q(4), yb, 'stone', 3 if xx < cx else 2, cut=1)
    blk(a, x0, yb - q(9), x1, yb - q(6), 'timber_warm', 4, cut=1)
    blk(a, x0, yb - q(6), x1, yb - q(5), 'timber', 2, cut=0)
    return finish(p)


def p_fence(w, h, seed, rail_only=False):
    """A post and rail fence, w world px long: split posts with caps, two rails."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=14, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    n = max(2, int(round(w / 16)) + 1)
    for yy in (yb - q(11), yb - q(5)):
        bar(a, x0, yy, x1, yy + int(rng.integers(-1, 2)), q(1.0), 'timber', 3)
    for k in range(n):
        xx = int(x0 + (x1 - x0 - q(3)) * k / (n - 1))
        beam(a, xx, yb - q(14), xx + q(3), yb, rng, 'timber', 3 if k < n / 2 else 2)
        fill(a, xx, yb - q(14), xx + q(3), yb - q(13), code('timber_warm', 4))
    return finish(p)


def p_flower_tub(w, h, seed):
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    blk(a, cx - q(w / 2), yb - q(6), cx + q(w / 2), yb, 'clay', 3, cut=1)
    fill(a, cx - q(w / 2), yb - q(6), cx + q(w / 2), yb - q(5), code('clay', 4))
    for k in range(5):
        x = cx - q(w / 2) + q(1.5) + k * q((w - 3) / 4)
        blob(a, ellipse_mask(a.shape, x, yb - q(8), q(2.2), q(2.4)), 'leaf', 3 + k % 2)
        if k % 2 == 0:
            fill(a, x - 1, yb - q(10), x + 2, yb - q(10) + 3, code(('berry', 'brass', 'dusk')[k % 3], 4))
    return finish(p)


def p_sacks(w, h, seed):
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=10, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    for k, (dx, s) in enumerate(((-0.25, 1.0), (0.22, 0.9), (0.0, 0.8))):
        x = cx + q(w * dx)
        y = yb - q(5 * s) - (q(6) if k == 2 else 0)
        m = ellipse_mask(a.shape, x, y, q(4.2 * s), q(5 * s))
        blob(a, m, 'plaster_warm', 3)
        fill(a, x - q(1.5), y - q(5 * s), x + q(1.5), y - q(4 * s), code('timber_warm', 2))
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
    """A handcart left in the square when the village ran: a plank bed on two spoked wheels, its
    shafts on the ground, a sack and a crate still on it."""
    rng = np.random.default_rng(seed)
    p = _pic(w, h, up=16, side=6)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    # shafts resting on the ground to the west
    for dy in (0, q(3)):
        bar(a, x0 - q(5), yb - q(1) - dy, x0 + q(6), yb - q(9) - dy, max(1.2, q(0.8)), 'timber', 3)
    planks(a, x0, yb - q(14), x1, yb - q(8), rng, base=3, width=2.4, vertical=False, grain=False)
    blk(a, x0, yb - q(15), x1, yb - q(13.6), 'timber_warm', 4, cut=0)
    for xx in (x0 + q(1), x1 - q(2.5)):
        fill(a, xx, yb - q(19), xx + q(1.5), yb - q(14), code('timber', 2))
    blob(a, ellipse_mask(a.shape, x0 + q(w * 0.35), yb - q(17), q(4), q(3.4)), 'plaster_warm', 3)
    blk(a, x1 - q(9), yb - q(21), x1 - q(2), yb - q(14), 'timber', 3, cut=0)
    # the wheel (we see one, side on)
    wc = (cx + q(w * 0.1), yb - q(5.5))
    ring_ = ellipse_mask(a.shape, wc[0], wc[1], q(5.5), q(5.5)) & ~ellipse_mask(a.shape, wc[0], wc[1], q(4.2), q(4.2))
    a[ring_] = code('timber_cool', 2)
    a[ring_ & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] < wc[1])] = code('timber', 3)
    for ang in (0.0, 0.5 * math.pi):
        dx, dy = math.cos(ang) * q(4.2), math.sin(ang) * q(4.2)
        bar(a, wc[0] - dx, wc[1] - dy, wc[0] + dx, wc[1] + dy, max(1.2, D * 0.4), 'timber', 2)
    blob(a, ellipse_mask(a.shape, wc[0], wc[1], q(1.2), q(1.2)), 'iron', 3)
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
