"""The Mossling, the REST family Grassling (species BLOB): three design options (Claude J lane).

The most common starter familiar. It follows the folk a step behind, naps curled against
them, rides the shoulder in fights and carries the type (REST) and the rested special
(SLEEP IT OFF: heal and guard). Today's sprite (scripts/art/pets.py `mossling`) is a
round green mochi with a sprout and a mushroom cap; the cap now belongs to Puffcap, so
the redesign keeps the round mossy blob with a sprout and drops the cap.

Main question: the blob's form and its moss.

    A  Tuft-back mochi: a tall round ball on two foot nubs, moss as separate clumped tufts
       crowning the head and running down the back, a two-leaf sprout, a plaster belly.
    B  Teardrop with a moss cap: a footless teardrop that bounces, its point growing one
       big curled leaf, moss as a thick thatched cap with a dripping fringe, a sand belly.
    C  Moss-cloak pebble: a wide flat pebble on stubby feet, moss as a shaggy cloak over
       the crown and down both sides to the feet, a bent seedling sprout, a sand face.

Views (familiar rules, batch 3): S idle, E idle, W idle, S hop (airborne), S nap (curled),
and the 16 px perch sprite E and W (redrawn small, not scaled). Cell 32 x 32, foot (16, 28);
perch cell 24 x 24, foot (12, 22). W is drawn with the same light, never mirrored pixels.

Run from the repo root:
    CHAR_VIEWS=<scratch>/designs python3 scripts/art/characters/designs/mossling.py
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/mossling-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/mossling.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'mossling')

W, H = 32, 32
FX, FY = 16, 28          # foot anchor: the soles fill row 27, their outline lands on row 28
PW, PH = 24, 24
PFX, PFY = 12, 22        # perch foot anchor
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_l = (-0.5, -0.62, 0.6)
_n = math.sqrt(sum(c * c for c in _l))
LIGHT = tuple(c / _n for c in _l)   # upper left, a little toward the viewer


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
class Ctx:
    """Where a view is drawn: foot anchor, scale (1 world, 2/3 perch) and facing d
    (0 south, 1 east, -1 west). Offsets are art px from the foot, before scale."""

    def __init__(self, view):
        self.view = view
        self.perch = view in ('Ep', 'Wp')
        if self.perch:
            self.fig = sk.Fig(PW, PH)
            self.fx, self.fy, self.s = PFX, PFY, 16 / 24
        else:
            self.fig = sk.Fig(W, H)
            self.fx, self.fy, self.s = FX, FY, 1.0
        self.d = {'S': 0, 'hop': 0, 'nap': 0, 'E': 1, 'Ep': 1, 'W': -1, 'Wp': -1}[view]
        self.keep = set()

    def X(self, dx):
        return self.fx + dx * self.s

    def Y(self, dy):
        return self.fy + dy * self.s

    def ell(self, dx, dy, rx, ry):
        return self.fig.ellipse(self.X(dx), self.Y(dy), rx * self.s, ry * self.s)

    def poly(self, pts):
        return self.fig.poly([(self.X(a), self.Y(b)) for a, b in pts])

    def at(self, dx, dy):
        return (int(math.floor(self.X(dx))), int(math.floor(self.Y(dy))))


def light_of(u, v):
    r2 = u * u + v * v
    if r2 > 1:
        k = 1 / math.sqrt(r2)
        u, v, r2 = u * k, v * k, 1.0
    nz = math.sqrt(max(0.0, 1 - r2))
    return u * LIGHT[0] + v * LIGHT[1] + nz * LIGHT[2]


def tone_of(dl, cuts=(0.80, 0.42, 0.02)):
    return 4 if dl > cuts[0] else 3 if dl > cuts[1] else 2 if dl > cuts[2] else 1


def ball(c, mask, fam, cx, cy, rx, ry, ry_top=None, glint=True, cuts=(0.80, 0.42, 0.02), lo=1):
    """Round-form shading: a lit cap at the upper left, the body, a dark crescent at the
    lower right that follows the form, the underside row tone 1, a two-pixel glint."""
    fig = c.fig
    mask = set(mask)
    ry_top = ry_top or ry
    best = []
    for (x, y) in mask:
        u = (x + 0.5 - cx) / rx
        v = (y + 0.5 - cy) / (ry_top if y + 0.5 < cy else ry)
        dl = light_of(u, v)
        t = max(lo, tone_of(dl, cuts))
        if (x, y + 1) not in mask and v > 0.2:
            t = min(t, 1 if lo <= 1 else lo)
        fig.put(x, y, fam, t)
        best.append((-dl, x, y))
    if glint and best:
        best.sort()
        x0, y0 = best[0][1], best[0][2]
        fig.put(x0, y0, fam, 5)
        nb = (x0 + 1, y0) if (x0 + 1, y0) in mask else (x0, y0 + 1)
        fig.put(nb[0], nb[1], fam, 5)
        c.keep |= {(x0, y0), nb}
    return mask


TUFT = ((1, 0, 1), (2, 0, 1), (0, 1, 1), (1, 1, 0), (2, 1, 0), (3, 1, -1), (1, 2, -1), (2, 2, -1))
TUFT_W = ((0, 0, 1), (1, 0, 1), (0, 1, 0), (1, 1, 0), (2, 1, -1), (1, 2, -1))
TUFT_S = ((0, 0, 1), (1, 0, 1), (0, 1, 0), (1, 1, 0), (2, 1, -1))


def grow(mask, n=1):
    out = set(mask)
    for _ in range(n):
        out |= {(x + dx, y + dy) for (x, y) in out for dx, dy in N4}
    return out


def scatter(c, mask, step=(4, 3), seed=0):
    """Clump anchors through a mask, staggered and jittered so the moss never lines up into
    rows (rows would read as knit, which is Tam's)."""
    ys = sorted({y for _, y in mask})
    out = []
    for row, y0 in enumerate(range(ys[0], ys[-1], step[1])):
        xs = sorted(x for x, yy in mask if yy == y0) or [0]
        x = xs[0] - 1 + (row % 2) * (step[0] // 2) + (row * 3 + seed) % 2
        while x < xs[-1] - 1:
            j = ((x * 7 + y0 * 13 + seed) % 3) - 1
            out.append(((x - c.fx) / c.s, (y0 + j - c.fy) / c.s))
            x += step[0] + ((x * 5 + y0 + seed) % 2)
        if not out:
            continue
    return out


def tufts(c, anchors, fam, cx, cy, rx, ry, small=False, crevice=True, clip=None, lift=0):
    """Moss as clumped tufts (2-4 px clusters): each clump has a lit top, a body and a
    dark lower right, its tone set by where it sits on the round form, and a dark
    crevice under it. Drawn top to bottom, so nearer clumps overlap the ones behind."""
    fig = c.fig
    seen = set()
    for (dx, dy) in sorted(anchors, key=lambda a: (a[1], a[0])):
        ax, ay = c.at(dx, dy)
        if (ax, ay) in seen:
            continue
        seen.add((ax, ay))
        shape = TUFT_S if (small or c.perch) else (TUFT if (ax * 3 + ay) % 3 else TUFT_W)
        u = (ax + 1.5 - cx) / rx
        v = (ay + 1.5 - cy) / ry
        base = max(2, min(4, tone_of(light_of(u, v)) + lift))
        for (ox, oy, k) in shape:
            p = (ax + ox, ay + oy)
            if clip is not None and p not in clip:
                continue
            fig.put(p[0], p[1], fam, max(1, min(4, base + k)))
        if crevice:
            w = 2 if shape is not TUFT else 3
            for ox in range(w):
                p = (ax + ox + (1 if shape is TUFT else 0), ay + (3 if shape is TUFT else 2))
                if p in fig.px and fig.px[p][0] != fam and fig.px[p][0] != 'ink' and (clip is None or p in clip):
                    fig.put(p[0], p[1], fam, max(1, base - 2))


def leaf(c, dx, dy, rx, ry, rot, fam, vein=True):
    """A small leaf as a rotated ellipse: lit upper left half, a dark midrib, a darker tip."""
    fig = c.fig
    cx, cy = c.X(dx), c.Y(dy)
    rx, ry = rx * c.s, ry * c.s
    m = set()
    ca, sa = math.cos(rot), math.sin(rot)
    for y in range(int(cy - rx) - 2, int(cy + rx) + 3):
        for x in range(int(cx - rx) - 2, int(cx + rx) + 3):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u = (px * ca + py * sa) / rx
            v = (-px * sa + py * ca) / ry
            if u * u + v * v <= 1.0 and fig.inside(x, y):
                m.add((x, y))
                t = 4 if v < -0.05 else 3
                if u > 0.55:
                    t -= 1
                if vein and abs(v) < 0.22 and -0.6 < u < 0.5 and rx > 2.5:
                    t = 2
                fig.put(x, y, fam, t)
    return m


def eye(c, x, y, w, h, glint_fam, shape='open'):
    fig = c.fig
    if shape == 'closed':
        pts = [(x - 1, y + h - 2), (x, y + h - 1), (x + 1, y + h - 1), (x + 2, y + h - 2)] if w >= 2 else \
              [(x - 1, y + h - 2), (x, y + h - 1), (x + 1, y + h - 2)]
        for p in pts:
            fig.put(p[0], p[1], 'ink', 0)
            c.keep.add(p)
        return
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            fig.put(xx, yy, 'ink', 0)
            c.keep.add((xx, yy))
    fig.put(x, y, glint_fam, 5)
    if h >= 3 and w >= 2:
        fig.put(x + w - 1, y + h - 1, glint_fam, 2)   # a soft lower catchlight: a wet eye


def put_keep(c, x, y, fam, t):
    c.fig.put(x, y, fam, t)
    c.keep.add((x, y))


def despeckle(c):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour, unless it is an eye, a glint or a face mark (`keep`). Deterministic."""
    fig = c.fig
    for _ in range(2):
        changes = {}
        for p in sorted(fig.px):
            v = fig.px[p]
            if p in c.keep or v[0] in ('ink', '_edge', '_lit'):
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if all(n != v for n in nb):
                pool = [n for n in nb if n[0] not in ('ink', '_edge', '_lit')]
                if not pool:
                    continue
                changes[p] = max(sorted(set(pool), key=str), key=pool.count)
        for p, v in changes.items():
            fig.px[p] = v


def finish(c):
    despeckle(c)
    c.fig.outline()
    despeckle(c)      # again with the outline in place, so edge pixels are judged too
    return c.fig


def face_marks(c, ex_l, ex_r, ey, w, h, mouth_x, mouth_y, skin, blush=True, mouth='smile'):
    """Blush under the outer eye corners and a small mouth in the skin's own tone 0."""
    if blush:
        for (bx, by) in ex_l + ex_r:
            put_keep(c, bx, by, 'berry_warm', 4)
            put_keep(c, bx + 1, by, 'berry_warm', 4)
    if mouth == 'smile':
        put_keep(c, mouth_x, mouth_y, skin, 1)
        put_keep(c, mouth_x + 1, mouth_y, skin, 1)
    elif mouth == 'open':
        put_keep(c, mouth_x, mouth_y, 'ink', 0)
        put_keep(c, mouth_x + 1, mouth_y, 'ink', 0)
        put_keep(c, mouth_x, mouth_y + 1, 'berry_warm', 3)
        put_keep(c, mouth_x + 1, mouth_y + 1, 'berry_warm', 2)
    elif mouth == 'side':
        put_keep(c, mouth_x, mouth_y, skin, 1)


# --- option A: the tuft-back mochi ----------------------------------------------------
A_BODY, A_MOSS, A_BELLY, A_SPROUT = 'leaf_warm', 'leaf_cool', 'plaster', 'grass_warm'


SPROUT_BIG = {   # (dx, dy, tone) from the joint at the stem's top: two leaves rising in a V
    'west': ((-5, -4, 4), (-4, -4, 4), (-5, -3, 3), (-4, -3, 4), (-3, -3, 4), (-4, -2, 3), (-3, -2, 4),
             (-2, -2, 3), (-3, -1, 2), (-2, -1, 3), (-1, -1, 3)),
    'east': ((3, -3, 3), (4, -3, 3), (2, -2, 3), (3, -2, 3), (4, -2, 2), (1, -1, 3), (2, -1, 2), (3, -1, 2)),
}
SPROUT_SMALL = {
    'west': ((-3, -2, 4), (-2, -2, 4), (-3, -1, 3), (-2, -1, 4), (-1, -1, 3)),
    'east': ((2, -2, 3), (3, -2, 3), (1, -1, 3), (2, -1, 2)),
}
SPROUT_DROOP = {
    'west': ((-1, 0, 3), (-2, 0, 4), (-3, 0, 4), (-4, 1, 3), (-2, 1, 3), (-3, 1, 3), (-4, 2, 2), (-5, 2, 2)),
    'east': ((1, 0, 3), (2, 0, 3), (2, 1, 2), (3, 1, 2), (3, 2, 1)),
}


def seedling(c, x, y, fam, stem=3, lean=0, droop=False):
    """Two-leaf sprout, pixel by pixel: the stem rises `stem` px from the body top (x, y);
    a bigger lit leaf to the west, a smaller shaded one to the east. The same sprout in
    every facing (it is a round stem: its light stays upper left)."""
    fig = c.fig
    for i in range(stem):
        fig.put(x + (lean if i == stem - 1 else 0), y - i, fam, 2 if i == 0 else 3)
    jx, jy = x + lean, y - stem + 1
    data = SPROUT_DROOP if droop else (SPROUT_SMALL if c.perch else SPROUT_BIG)
    for side in ('west', 'east'):
        for (dx, dy, t) in data[side]:
            fig.put(jx + dx, jy + dy, fam, t)
    fig.put(jx, jy, fam, 3)
    return jx, jy


def clump(c, dx, dy, rx, ry, fam, under, glob, clip=None, crevice=True):
    """A moss clump: a small mound shaded on its own (lit cap upper left, dark lower
    right), dimmed one step when it sits on the body's shadow side, with a tone-1
    crevice of the skin under it so it reads as a tuft standing on the skin."""
    fig = c.fig
    cx, cy = c.X(dx), c.Y(dy)
    RX, RY = max(1.3, rx * c.s), max(1.2, ry * c.s)
    m = fig.ellipse(cx, cy, RX, RY)
    if clip is not None:
        m &= clip
    gu, gv = (cx - glob[0]) / glob[2], (cy - glob[1]) / glob[3]
    gl = light_of(gu, gv)
    dim = 1 if gl < 0.35 else -1 if gl > 0.72 else 0
    for (x, y) in m:
        u, v = (x + 0.5 - cx) / RX, (y + 0.5 - cy) / RY
        t = tone_of(light_of(u, v), (0.75, 0.3, -0.2)) - dim
        if (x, y + 1) not in m and v > 0.3:
            t = min(t, 2)
        fig.put(x, y, fam, max(1, min(4, t)))
    if crevice == 'inner':      # clumps inside one moss mass: a tone-1 gap under each mound
        for (x, y) in m:
            q = (x, y + 1)
            if q not in m and q in clip and abs(x + 0.5 - cx) < RX * 0.7:
                fig.put(q[0], q[1], fam, 1)
        return m
    for (x, y) in (m if crevice else ()):
        q = (x, y + 1)
        if q not in m and q in fig.px and fig.px[q][0] not in (fam, 'ink') and (x + 0.5 - cx) > -RX * 0.6:
            fig.put(q[0], q[1], under, 1)
    return m


def option_a(view):
    c = Ctx(view)
    fig, d = c.fig, c.d
    if view == 'nap':
        cx, cy, rx, ry = c.X(0), c.Y(-6), 11.5, 6.4
        body = fig.ellipse(cx, cy, rx, ry)
        ball(c, body, A_BODY, cx, cy, rx, ry)
        belly = fig.ellipse(cx + 1.5, cy + 2.2, 6.5, 3.6) & body
        ball(c, belly, A_BELLY, cx, cy, rx, ry, glint=False, lo=2)
        for (xx, yy, a_, b_) in ((-6.5, -10.0, 2.8, 2.0), (-1.4, -11.3, 3.0, 2.1), (3.8, -10.6, 2.6, 2.0),
                                 (-10.2, -6.4, 2.0, 2.3)):
            clump(c, xx, yy, a_, b_, A_MOSS, A_BODY, (cx, cy, rx, ry))
        # face tucked low on the right, eyes shut, a sleepy smile
        eye(c, 14, 22, 2, 2, A_BELLY, 'closed')
        eye(c, 20, 22, 2, 2, A_BELLY, 'closed')
        face_marks(c, [(12, 24)], [(21, 24)], 22, 2, 2, 17, 24, A_BODY, mouth='side')
        t = c.at(-4, -12)
        seedling(c, t[0], t[1] + 1, A_SPROUT, stem=2, droop=True)
        return finish(c)
    hop = view == 'hop'
    lift = 3 if hop else 0
    sx_, sy_ = (0.94, 1.05) if hop else (1.0, 1.0)
    bx, by = 0, -9.6 - lift
    rx, ry = 10 * sx_, 8.8 * sy_
    if c.perch:
        rx, ry = 10.6, 9.6
        by = -9.8
    # feet: two nubs (far one darker behind in side views); tucked up in the hop
    if d == 0:
        feet = [(-5, -1.3 - (lift - 1 if hop else 0)), (5, -1.3 - (lift - 1 if hop else 0))]
    else:
        feet = [(-3.5 * d, -1.4), (4 * d, -1.2)]
    for i, (fxo, fyo) in enumerate(feet):
        m = c.ell(fxo, fyo, 3.0, 1.8)
        far = d != 0 and i == 0
        ball(c, m, 'leaf' if far else A_BODY, c.X(fxo), c.Y(fyo), 3 * c.s, 1.8 * c.s, glint=False)
    cx, cy = c.X(bx), c.Y(by)
    body = c.ell(bx, by, rx, ry)
    RX, RY = rx * c.s, ry * c.s
    ball(c, body, A_BODY, cx, cy, RX, RY, cuts=(0.87, 0.48, 0.12))
    # belly: plaster, forward in side views
    belly = (c.ell(0, by + 4.6, 5.8, 4.4) if d == 0 else c.ell(2.6 * d, by + 5.6, 4.0, 3.3)) & body
    ball(c, belly, A_BELLY, cx, cy, RX, RY, glint=False, lo=2,
         cuts=(0.80, 0.42, 0.02) if d == 0 else (0.8, 0.42, 0.1))
    # moss tufts: a crown on the head, clumps down the back
    # moss: separate clumps, a crown over the head and a row down the back
    if d == 0:
        cl = [(-5, -7.4, 3.0, 2.2), (0.6, -8.3, 3.2, 2.3), (5.6, -6.6, 2.6, 2.0),
              (-8.7, -2.6, 2.0, 2.4), (8.7, -2.4, 1.8, 2.2)]
    else:
        cl = [(xx * d, yy, a_, b_) for xx, yy, a_, b_ in
              ((-1.2, -8.3, 3.1, 2.3), (3.8, -7.4, 2.3, 1.9), (-6.0, -6.0, 2.8, 2.3),
               (-9.0, -1.6, 2.2, 2.6), (-8.0, 3.3, 2.0, 2.0))]
    if c.perch:
        cl = [(xx, yy, max(a_, 3.4), max(b_, 3.0)) for xx, yy, a_, b_ in (cl[:2] + cl[2:3] if d else cl[:3])]
    for (xx, yy, a_, b_) in cl:
        clump(c, xx, by + yy, a_, b_, A_MOSS, A_BODY, (cx, cy, RX, RY))
    # face
    ew, eh = (2, 3) if not c.perch else (2, 2)
    eyy = int(round(c.Y(by + 1.0))) - (1 if c.perch else 0)
    mshape = 'open' if hop else 'smile'
    if d == 0:
        ex1, ex2 = int(cx) - 5, int(cx) + 3
        eye(c, ex1, eyy, ew, eh, A_BELLY)
        eye(c, ex2, eyy, ew, eh, A_BELLY)
        face_marks(c, [(ex1 - 1, eyy + eh)], [(ex2 + 1, eyy + eh)], eyy, ew, eh, int(cx) - 1, eyy + eh, A_BODY,
                   mouth=mshape)
    else:
        near = int(cx) + (3 if d > 0 else -5) if not c.perch else int(cx) + (2 if d > 0 else -4)
        far = near + (5 if d > 0 else -2) if not c.perch else near + (4 if d > 0 else -2)
        eye(c, near, eyy, ew, eh, A_BELLY)
        bxl = near - 1 if d > 0 else near + ew - 1
        put_keep(c, bxl, eyy + eh, 'berry_warm', 4)
        put_keep(c, bxl + 1, eyy + eh, 'berry_warm', 4)
        mx = near + (3 if d > 0 else -2) if not c.perch else near + (2 if d > 0 else -1)
        put_keep(c, mx, eyy + eh, A_BODY, 1)
    top = c.at(-0.5 if d == 0 else -1.5 * d, by - ry)
    seedling(c, top[0], top[1] + 1, A_SPROUT, stem=3 if not c.perch else 2)
    return finish(c)


# --- option B: the teardrop with a moss cap -------------------------------------------
B_BODY, B_MOSS, B_BELLY, B_LEAF = 'leaf', 'grass_cool', 'sand', 'leaf_warm'


CURL_BIG = (   # (dx, dy, tone) from the stem top, leaning west: a broad blade, its tip rolled
    (-6, -6, 3), (-5, -6, 4), (-4, -6, 4),
    (-7, -5, 3), (-6, -5, 1), (-5, -5, 3), (-4, -5, 4), (-3, -5, 4), (-2, -5, 4),
    (-7, -4, 2), (-6, -4, 2), (-5, -4, 4), (-4, -4, 4), (-3, -4, 4), (-2, -4, 4), (-1, -4, 3),
    (-6, -3, 2), (-5, -3, 3), (-4, -3, 3), (-3, -3, 3), (-2, -3, 3), (-1, -3, 3), (0, -3, 2),
    (-4, -2, 2), (-3, -2, 2), (-2, -2, 3), (-1, -2, 3), (0, -2, 2),
    (-1, -1, 2), (0, -1, 3),
)
CURL_SMALL = (
    (-4, -4, 3), (-3, -4, 4), (-2, -4, 4),
    (-5, -3, 3), (-4, -3, 1), (-3, -3, 4), (-2, -3, 4), (-1, -3, 3),
    (-4, -2, 2), (-3, -2, 3), (-2, -2, 3), (-1, -2, 3), (0, -2, 2),
    (-1, -1, 2), (0, -1, 3),
)


def b_curl_leaf(c, base, d):
    """One big curled leaf from the teardrop's point: a broad blade leaning back over the
    head (west for S and E, east for W), its tip rolled into a curl. Lit along its top
    edge, so the light stays upper left in every facing."""
    fig = c.fig
    sx, sy = base
    lean = -1 if d >= 0 else 1
    fig.put(sx, sy, B_LEAF, 2)
    for (dx, dy, t) in (CURL_SMALL if c.perch else CURL_BIG):
        fig.put(sx - dx * lean, sy + dy, B_LEAF, t)


def b_body_mask(c, by, rx, ry, tip_h, tip_dx=0):
    cx, cy = c.X(0), c.Y(by)
    m = c.ell(0, by, rx, ry)
    # the point: a soft cone from the shoulders up to the tip
    top = by - ry - tip_h
    m |= c.poly([(-rx * 0.72, by - ry * 0.55), (tip_dx - 0.9, top), (tip_dx + 0.9, top),
                 (rx * 0.72, by - ry * 0.55), (0, by)])
    return m, cx, cy


def b_cap(c, body, cx, cy, RX, RY, top_ry, hem_y, d):
    """The moss cap: everything above a dripping hem, shaded as one form, thatched with
    small overlapping clumps, and a tone-1 crevice of skin under its hem."""
    fig = c.fig
    cap = set()
    for (x, y) in body:
        k = (x - int(cx) + 40) % 4
        drip = 1 if k in (1, 2) else 0
        back = -0.22 * d * (x + 0.5 - cx)   # lower over the back in side views
        if y + 0.5 < hem_y + drip + back:
            cap.add((x, y))
    ball(c, cap, B_MOSS, cx, cy, RX, RY, ry_top=top_ry, glint=False, cuts=(0.9, 0.6, 0.2))
    for (ax, ay) in scatter(c, cap, step=(5, 4), seed=3):
        clump(c, ax + 1.6, ay + 1.4, 2.4, 2.0, B_MOSS, B_MOSS, (cx, cy, RX, top_ry), clip=cap, crevice='inner')
    for (x, y) in sorted(cap):
        if (x, y + 1) in body and (x, y + 1) not in cap:
            fig.put(x, y + 1, B_BODY, 1 if x + 0.5 > cx - RX * 0.3 else 2)
    return cap


def option_b(view):
    c = Ctx(view)
    d = c.d
    if view == 'nap':
        # settled low, the point sagging back west, the big leaf laid over it as a blanket
        rx, ry, by, tip_h = 11.0, 6.2, -6.4, 2.6
        body, cx, cy = b_body_mask(c, by, rx, ry, tip_h, -4.0)
        ball(c, body, B_BODY, cx, cy, rx, ry, ry_top=ry + tip_h)
        belly = c.ell(1.0, by + 3.0, 6.6, 3.2) & body
        ball(c, belly, B_BELLY, cx, cy, rx, ry, glint=False, lo=2)
        b_cap(c, body, cx, cy, rx, ry, ry + tip_h, c.Y(by - 0.6), 0)
        leaf(c, 3.0, -11.6, 7.6, 2.3, 0.2, B_LEAF)
        ey = int(c.Y(by + 0.6))
        eye(c, int(cx) - 4, ey, 2, 2, B_BELLY, 'closed')
        eye(c, int(cx) + 2, ey, 2, 2, B_BELLY, 'closed')
        put_keep(c, int(cx), ey + 3, B_BODY, 1)
        put_keep(c, int(cx) - 6, ey + 2, 'berry_warm', 4)
        put_keep(c, int(cx) + 5, ey + 2, 'berry_warm', 4)
        return finish(c)
    hop = view == 'hop'
    lift = 2 if hop else 0
    rx, ry = (9.2, 7.6) if not hop else (8.6, 8.0)
    by = -8.2 - lift
    tip_h = 2.6
    if c.perch:
        rx, ry, by, tip_h = 9.8, 8.8, -9.2, 3.6
    tip_dx = -1.2 * d
    body, cx, cy = b_body_mask(c, by, rx, ry, tip_h, tip_dx)
    RX, RY = rx * c.s, ry * c.s
    TOP = (ry + tip_h) * c.s
    ball(c, body, B_BODY, cx, cy, RX, RY, ry_top=TOP, cuts=(0.80, 0.48, 0.12))
    belly = (c.ell(0, by + 4.6, 5.4, 3.8) if d == 0 else c.ell(2.8 * d, by + 4.8, 4.0, 3.3)) & body
    ball(c, belly, B_BELLY, cx, cy, RX, RY, glint=False, lo=2)
    b_cap(c, body, cx, cy, RX, RY, TOP, c.Y(by - ry * 0.3) - 1, d)
    # face: big eyes just under the cap
    ew, eh = (3, 3) if not c.perch else (2, 2)
    eyy = int(round(c.Y(by - 0.4))) + (1 if c.perch else 0)
    mshape = 'open' if hop else 'smile'
    if d == 0:
        ex1, ex2 = int(cx) - 6, int(cx) + 3
        eye(c, ex1, eyy, ew, eh, B_BELLY)
        eye(c, ex2, eyy, ew, eh, B_BELLY)
        face_marks(c, [(ex1 - 1, eyy + eh)], [(ex2 + 2, eyy + eh)], eyy, ew, eh, int(cx) - 1, eyy + eh, B_BODY,
                   mouth=mshape)
    else:
        near = int(cx) + (2 if d > 0 else -2 - ew) if not c.perch else int(cx) + (2 if d > 0 else -4)
        eye(c, near, eyy, ew, eh, B_BELLY)
        bxl = near - 1 if d > 0 else near + ew - 1
        put_keep(c, bxl, eyy + eh, 'berry_warm', 4)
        put_keep(c, bxl + 1, eyy + eh, 'berry_warm', 4)
        mx = near + (ew + 1 if d > 0 else -2) if not c.perch else near + (2 if d > 0 else -1)
        put_keep(c, mx, eyy + eh, B_BODY, 1)
    tip = c.at(tip_dx, by - ry - tip_h)
    b_curl_leaf(c, (tip[0], tip[1]), d)
    return finish(c)


# --- option C: the moss-cloak pebble --------------------------------------------------
C_BODY, C_MOSS, C_MOSS2, C_SPROUT, C_FEET = 'sand', 'leaf_cool', 'leaf', 'grass_warm', 'earth'


def c_sprout(c, base, bend=1, droop=False):
    """A seedling still wearing its seed coat: the two-leaf sprout on a taller stem with a
    small sand husk caught on the joint (the coat is what tells it from option A)."""
    x, y = base
    jx, jy = seedling(c, x, y + 1, C_SPROUT, stem=(4 if not c.perch else 3) if not droop else 2,
                      lean=0 if droop else bend, droop=droop)
    if droop:
        return
    fig = c.fig
    for (dx, dy, t) in ((-6, -5, 4), (-5, -5, 4), (-6, -4, 3), (-5, -4, 3), (-4, -4, 2)) if not c.perch else \
            ((-4, -3, 4), (-3, -3, 3), (-4, -2, 3)):
        fig.put(jx + dx, jy + dy, C_BODY, t)


def c_cloak(c, body, cx, cy, RX, RY, d, low, mound_top):
    """The moss cloak: a mound over the crown and a mantle down both sides (the back in
    side views) to `low`, its hem a fringe of hanging tufts."""
    fig = c.fig
    cloak = set()
    for (x, y) in body:
        u = (x + 0.5 - cx) / RX
        # how far down the cloak reaches at this column: the crown in front, low at the sides
        if d == 0:
            reach = cy - RY * 0.35 + (abs(u) ** 2.2) * (low - (cy - RY * 0.35))
        else:
            ub = -u * d  # 1 at the back
            reach = cy - RY * 0.35 + max(0.0, (ub + 0.35) / 1.35) ** 1.4 * (low - (cy - RY * 0.35))
        k = (x - int(cx) + 40) % 3
        if y + 0.5 < reach + (1.2 if k == 1 else 0):
            cloak.add((x, y))
    # the mound above the body top, a little wider than the crown
    mound = fig.ellipse(cx - 0.6 * d, mound_top + 3.2 * c.s, RX * 0.78, 3.6 * c.s)
    mound = {p for p in mound if p[1] + 0.5 < cy}
    # side flare: the mantle stands 1 px proud of the pebble at the shoulders
    flare = set()
    for (x, y) in cloak:
        for side in (-1, 1):
            q = (x + side, y)
            if q not in body and y > cy - RY * 0.5 and (d == 0 or side == -d):
                flare.add(q)
    cl = cloak | mound | flare
    ball(c, cl, C_MOSS, cx, cy - 1.5 * c.s, RX + 1, RY + 3.5 * c.s, glint=False)
    # clumps: rows of tufts across the cloak
    for (ax, ay) in scatter(c, cl, step=(5, 4), seed=1):
        clump(c, ax + 1.6, ay + 1.4, 2.4, 2.0, C_MOSS, C_MOSS, (cx, cy - 1.5 * c.s, RX + 1, RY + 3.5 * c.s),
              clip=cl, crevice='inner')
    # the hem fringe: lighter moss tips in the second green hanging just under the edge
    for (x, y) in sorted(cl):
        below = (x, y + 1)
        if below in body and below not in cl and (x - int(cx) + 40) % 3 == 1:
            fig.put(x, y + 1, C_MOSS2, 2)
    return cl


def option_c(view):
    c = Ctx(view)
    fig, d = c.fig, c.d
    if view == 'nap':
        # the cloak pulled right over: a mossy mound with the face peeking out at the front
        cx, cy, rx, ry = c.X(0), c.Y(-5.5), 12.0, 5.8
        body = fig.ellipse(cx, cy, rx, ry)
        ball(c, body, C_BODY, cx, cy, rx, ry)
        cl = {p for p in body if not ((p[0] + 0.5 - (cx + 2)) / 6.5) ** 2 + ((p[1] + 0.5 - (cy + 3.2)) / 3.5) ** 2 <= 1}
        cl |= fig.ellipse(cx - 0.5, cy - 4.2, 9.5, 3.2)
        ball(c, cl, C_MOSS, cx, cy - 2, rx + 1, ry + 3, glint=False)
        for (ax, ay) in scatter(c, cl, step=(5, 4), seed=1):
            clump(c, ax + 1.6, ay + 1.4, 2.4, 2.0, C_MOSS, C_MOSS, (cx, cy - 2, rx + 1, ry + 3),
                  clip=cl, crevice='inner')
        eye(c, 15, 22, 2, 2, C_BODY, 'closed')
        eye(c, 20, 22, 2, 2, C_BODY, 'closed')
        put_keep(c, 18, 25, C_BODY, 1)
        put_keep(c, 23, 24, 'berry_warm', 4)
        c_sprout(c, c.at(-2, -13.5), droop=True)
        return finish(c)
    hop = view == 'hop'
    lift = 2 if hop else 0
    rx, ry = (11.0, 6.8) if not hop else (10.4, 7.3)
    by = -8.4 - lift
    if c.perch:
        rx, ry, by = 11.6, 7.8, -9.0
    # stubby feet: far one darker; in the hop they dangle
    if d == 0:
        feet = [(-5.5, -1.6 - (lift - 1.5 if hop else 0)), (5.5, -1.6 - (lift - 1.5 if hop else 0))]
    else:
        feet = [(-4 * d, -1.6), (4.5 * d, -1.5)]
    for i, (fxo, fyo) in enumerate(feet):
        m = c.ell(fxo, fyo, 2.6, 2.0)
        far = d != 0 and i == 0
        ball(c, m, 'earth_cool' if far else C_FEET, c.X(fxo), c.Y(fyo), 2.6 * c.s, 2.0 * c.s, glint=False)
        # two toe splits on the near feet
        if not far and not c.perch:
            xs = sorted({x for x, _ in m})
            yb = max(y for _, y in m)
            fig.put(xs[len(xs) // 2], yb, C_FEET, 1)
    body = c.ell(0, by, rx, ry)
    cx, cy = c.X(0), c.Y(by)
    RX, RY = rx * c.s, ry * c.s
    ball(c, body, C_BODY, cx, cy, RX, RY, cuts=(0.88, 0.5, 0.12))
    low = c.Y(by + ry * (0.62 if not hop else 0.5))
    c_cloak(c, body, cx, cy, RX, RY, d, low, c.Y(by - ry - 2.4))
    # face on the pale pebble below the cloak's crown
    ew, eh = (2, 3) if not c.perch else (2, 2)
    eyy = int(round(c.Y(by - 0.2)))
    mshape = 'open' if hop else 'smile'
    if d == 0:
        ex1, ex2 = int(cx) - 5, int(cx) + 3
        eye(c, ex1, eyy, ew, eh, C_BODY)
        eye(c, ex2, eyy, ew, eh, C_BODY)
        face_marks(c, [(ex1 - 1, eyy + eh)], [(ex2 + 1, eyy + eh)], eyy, ew, eh, int(cx) - 1, eyy + eh, C_BODY,
                   mouth=mshape)
    else:
        near = int(cx) + (4 if d > 0 else -6) if not c.perch else int(cx) + (3 if d > 0 else -5)
        far = near + (5 if d > 0 else -2) if not c.perch else near + (4 if d > 0 else -2)
        eye(c, near, eyy, ew, eh, C_BODY)
        bxl = near - 1 if d > 0 else near + ew - 1
        put_keep(c, bxl, eyy + eh, 'berry_warm', 4)
        put_keep(c, bxl + 1, eyy + eh, 'berry_warm', 4)
        mx = near + (3 if d > 0 else -2) if not c.perch else near + (2 if d > 0 else -1)
        put_keep(c, mx, eyy + eh, C_BODY, 1)
    c_sprout(c, c.at(-0.5 * d, by - ry - 2.6), bend=1 if d >= 0 else -1)
    return finish(c)


# --- sheet ------------------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('hop', 'S hop'), ('nap', 'S nap'),
         ('Ep', 'E perch'), ('Wp', 'W perch'))

OPTIONS = [
    dict(label='A', name='Tuft-back mochi', fn=option_a,
         question='Form and moss: a tall round ball on two foot nubs; moss as separate clumped tufts that crown the '
                  'head and run down the back; a two-leaf sprout.',
         palette=['leaf_warm', 'leaf_cool', 'plaster', 'grass_warm', 'berry_warm'],
         pose='Content and a little wobbly: it sits up straight on its nubs, eyes wide, waiting a step behind.',
         parts=[
             'far foot nub: leaf, layer 1, anchor foot; E/W only (S: both nubs layer 2)',
             'near foot nub: leaf_warm, layer 2, anchor foot; swings in the 6-frame walk, tucks in hop',
             'body ball: leaf_warm, layer 3, anchor hip; breath squashes 1 px, hop stretches 8%',
             'belly: plaster, layer 4, anchor hip; slides forward in E/W',
             'moss tufts (back clumps): leaf_cool, layer 5, anchor hip; move back in E/W, ruffle 1 px on land',
             'face (ink eyes 2x3 with glints, blush, mouth): layer 6, anchor head; S/E/W, closed in nap',
             'moss crown tufts: leaf_cool, layer 7, anchor head; S/E/W',
             'sprout (stem + two leaves): grass_warm, layer 8, anchor head; leans back in walk, droops in nap, '
             'perks up on cheer and on SLEEP IT OFF',
         ],
         notes=['Works: the closest to the sprite players know (round green mochi, sprout) minus Puffcap\'s cap; '
                'the tufts break the silhouette so it never reads as a plain ball.',
                'Risk: a green ball on green grass; the plaster belly and the dark leaf_cool tufts carry the read, '
                'and the tuft crown must stay chunky at 2 device px.',
                'Compared with Eastward-04 (Sam scaled to 24 px, about 3 tones a material, 2 px eyes) and the '
                'clumped tufts of its yard grass.']),
    dict(label='B', name='Teardrop with a moss cap', fn=option_b,
         question='Form and moss: a footless teardrop whose point grows one big curled leaf; moss as a thick '
                  'thatched cap with a dripping hem.',
         palette=['leaf', 'grass_cool', 'sand', 'leaf_warm', 'berry_warm'],
         pose='Bouncy and curious: no feet, it travels by hops, and the curled leaf bobs a beat behind it.',
         parts=[
             'body teardrop: leaf, layer 1, anchor hip; walk is a 6-frame hop (squash, stretch, land)',
             'belly: sand, layer 2, anchor hip; forward in E/W',
             'moss cap with drip hem: grass_cool, layer 3, anchor head; lower over the back in E/W',
             'face (ink eyes 3x3 with glints, blush, mouth): layer 4, anchor head; S/E/W',
             'curled leaf (stem, blade, curl): leaf_warm, layer 5, anchor head (the point); leans back from '
             'the facing, lags a frame in the hop',
             'nap: the leaf laid over the back as a blanket (same part, nap key)',
         ],
         notes=['Works: the biggest eyes and the most distinct shape (a drop with a leaf), and the leaf as a '
                'blanket makes the nap read as REST at a glance.',
                'Risk: footless means the walk is all hop, and the cap plus leaf is tall: the leaf must not '
                'echo Puffcap\'s cap or read as Mote\'s floppy nightcap.',
                'Compared with Eastward-04 (Sam at the same height): the cap uses its thatched-awning clusters.']),
    dict(label='C', name='Moss-cloak pebble', fn=option_c,
         question='Form and moss: a wide flat pebble on stubby feet; moss as a shaggy cloak over the crown and down '
                  'both sides; a bent seedling sprout still wearing its seed coat.',
         palette=['sand', 'leaf_cool', 'earth', 'grass_warm', 'berry_warm'],
         pose='Sleepy and steady: low and wide on its stubby feet, it shuffles, and the cloak sways after it.',
         parts=[
             'far foot: earth_cool, layer 1, anchor foot; E/W only',
             'near feet: earth, layer 2, anchor foot; shuffle in the 6-frame walk, dangle in hop',
             'pebble body: sand, layer 3, anchor hip; breath squashes 1 px',
             'face (ink eyes 2x3 with glints, blush, mouth): layer 4, anchor head; S/E/W',
             'moss cloak + crown mound + hem fringe: leaf_cool, leaf, layer 5, anchor head; covers the back in E/W, '
             'sways 1 frame late, pulls over as a blanket in nap',
             'seedling (bent stem, two leaves, seed coat): grass_warm, sand, layer 6, anchor head; bend flips with '
             'the facing',
         ],
         notes=['Works: the pale pebble face reads hardest against grass; the cloak gives a shaggy, sleepy shape '
                'that no folk shares.',
                'Risk: the cloak could read as a hood (Nix owns the hood); it must stay a moss mantle with a '
                'fringe, never a fabric edge. Less like the sprite players know.',
                'Compared with Eastward-04 (Sam at 24 px): the fringe uses its hair-tuft clusters.']),
]


# --- final: A, the tuft-back mochi, with B's curled leaf and big eyes --------------------
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/mossling-final.png')
F_BODY, F_MOSS, F_BELLY, F_LEAF, F_BLUSH, F_GLOW = 'leaf_warm', 'leaf_cool', 'plaster', 'grass_warm', 'berry_warm', \
    'glowflora'

# the curled leaf, (dx, dy, tone) from the joint on the crown, leaning west (back in S and E)
LEAF_W = ((-6, -6, 3), (-5, -6, 4), (-4, -6, 4),
          (-7, -5, 3), (-6, -5, 1), (-5, -5, 3), (-4, -5, 4), (-3, -5, 4), (-2, -5, 4),
          (-7, -4, 2), (-6, -4, 2), (-5, -4, 4), (-4, -4, 4), (-3, -4, 4), (-2, -4, 4), (-1, -4, 3),
          (-6, -3, 2), (-5, -3, 3), (-4, -3, 3), (-3, -3, 3), (-2, -3, 3), (-1, -3, 3), (0, -3, 2),
          (-4, -2, 2), (-3, -2, 2), (-2, -2, 3), (-1, -2, 3), (0, -2, 2),
          (-1, -1, 2), (0, -1, 3))
LEAF_W_FLAT = ((-6, -3, 3), (-5, -3, 4), (-4, -3, 4), (-3, -3, 4),
               (-7, -2, 3), (-6, -2, 1), (-5, -2, 3), (-4, -2, 4), (-3, -2, 4), (-2, -2, 4), (-1, -2, 3),
               (-6, -1, 2), (-5, -1, 2), (-4, -1, 3), (-3, -1, 3), (-2, -1, 3), (-1, -1, 3), (0, -1, 2))
# the perch leaf: the same curl, curled back and down so the sprite stays 16 px
LEAF_P = ((-4, -3, 3), (-3, -3, 4), (-2, -3, 4),
          (-5, -2, 3), (-4, -2, 1), (-3, -2, 3), (-2, -2, 4), (-1, -2, 4),
          (-5, -1, 2), (-4, -1, 2), (-3, -1, 3), (-2, -1, 3), (-1, -1, 3), (0, -1, 3))
LEAF_P_FLAT = ((-5, -2, 3), (-4, -2, 4), (-3, -2, 4), (-2, -2, 4),
               (-6, -1, 3), (-5, -1, 1), (-4, -1, 3), (-3, -1, 3), (-2, -1, 3), (-1, -1, 3), (0, -1, 2))


class FCtx(Ctx):
    def __init__(self, perch, d):
        self.view = 'final'
        self.perch = perch
        self.fig = sk.Fig(PW, PH) if perch else sk.Fig(W, H)
        self.fx, self.fy = (PFX, PFY) if perch else (FX, FY)
        self.s = 1.0
        self.d = d
        self.keep = set()
        self.marks = {}


def f_leaf(c, joint, lean, data):
    """The curled leaf on the head-top growth anchor. `lean` -1 leans it west, +1 east;
    tones run by row (lit along the top), so the light stays upper left either way."""
    jx, jy = joint
    for (dx, dy, t) in data:
        c.fig.put(jx + dx * (-lean), jy + dy, F_LEAF, t)
    c.fig.put(jx, jy, F_LEAF, 2)


def f_eye(c, x, y, mode, skin=F_BODY):
    """The family eye: a 3 x 3 ink block with a 2 px glint down its lit (west) column.
    lid: the top row is a heavy lid in the skin's tone 1 (REST, drowsy); closed: a u;
    happy: a ^; tight_l / tight_r: > and < (clinging on)."""
    fig = c.fig
    pts = []
    if mode in ('open', 'lid', 'wide'):
        for yy in range(y, y + 3):
            for xx in range(x, x + 3):
                pts.append((xx, yy, 'ink', 0))
        if mode == 'lid':
            pts = [p for p in pts if p[1] != y]
            pts += [(x, y, skin, 1), (x + 1, y, skin, 1), (x + 2, y, skin, 1)]
            pts += [(x, y + 1, F_BELLY, 5), (x, y + 2, F_BELLY, 5)]
            pts.remove((x, y + 1, 'ink', 0))
            pts.remove((x, y + 2, 'ink', 0))
        else:
            pts += [(x, y, F_BELLY, 5), (x, y + 1, F_BELLY, 5)]
            pts.remove((x, y, 'ink', 0))
            pts.remove((x, y + 1, 'ink', 0))
    elif mode == 'closed':
        pts = [(x, y + 1, 'ink', 0), (x + 1, y + 2, 'ink', 0), (x + 2, y + 1, 'ink', 0)]
    elif mode == 'happy':
        pts = [(x, y + 2, 'ink', 0), (x + 1, y + 1, 'ink', 0), (x + 2, y + 2, 'ink', 0)]
    elif mode == 'tight_l':
        pts = [(x, y, 'ink', 0), (x + 1, y + 1, 'ink', 0), (x + 2, y + 1, 'ink', 0), (x, y + 2, 'ink', 0)]
    elif mode == 'tight_r':
        pts = [(x + 2, y, 'ink', 0), (x + 1, y + 1, 'ink', 0), (x, y + 1, 'ink', 0), (x + 2, y + 2, 'ink', 0)]
    for (xx, yy, fam, t) in pts:
        fig.put(xx, yy, fam, t)
        c.keep.add((xx, yy))
    c.marks.setdefault('eyes', []).append([x, y])


def f_mouth(c, x, y, mode):
    if mode == 'smile':
        pts = [(x, y, F_BODY, 1), (x + 1, y, F_BODY, 1)]
    elif mode == 'o':
        pts = [(x, y, 'ink', 0), (x + 1, y, 'ink', 0), (x, y + 1, F_BLUSH, 2), (x + 1, y + 1, F_BLUSH, 2)]
    elif mode == 'open':
        pts = [(x, y, 'ink', 0), (x + 1, y, 'ink', 0), (x, y + 1, F_BLUSH, 3), (x + 1, y + 1, F_BLUSH, 3)]
    else:   # 'dot': one sleepy corner
        pts = [(x, y, F_BODY, 1)]
    for (xx, yy, fam, t) in pts:
        c.fig.put(xx, yy, fam, t)
        c.keep.add((xx, yy))


def f_blush(c, x, y):
    for xx in (x, x + 1):
        c.fig.put(xx, y, F_BLUSH, 4)
        c.keep.add((xx, y))


def mochi(c, sq=(1.0, 1.0), lift=0.0, eyes='lid', mouth='smile', leaf='back', feet='stand', look=0):
    """The Mossling, one pose. World: about 24 px with the leaf; perch: a 16 px redraw.
    sq squashes (x, y); lift raises it off the foot line; leaf is back, up, flat, shield,
    or none; feet are stand, tuck or splay."""
    d, P = c.d, c.perch
    rx0, ry0 = (7.2, 5.0) if P else (9.6, 7.2)
    rx, ry = rx0 * sq[0], ry0 * sq[1]
    by = -(ry + (0.8 if P else 1.0)) - lift
    cx, cy = c.X(0), c.Y(by)
    # feet: two nubs on the foot line (the family's shared foot line); far one darker in E/W
    fr = (1.9, 1.2) if P else (2.6, 1.6)
    if feet == 'tuck':
        fy = by + ry * 0.82
        fpos = [(-3.2, fy), (3.2, fy)] if d == 0 else [(-2.4 * d, fy), (2.8 * d, fy + 0.2)]
    else:
        spread = 1.25 if feet == 'splay' else 1.0
        fy = -fr[1] + 0.4 - (0.2 if P else 0)
        k = 3.3 if P else 4.6
        fpos = [(-k * spread, fy), (k * spread, fy)] if d == 0 else [(-0.7 * k * d, fy - 0.1), (0.75 * k * d, fy)]
    for i, (fxo, fyo) in enumerate(fpos):
        m = c.ell(fxo, fyo, *fr)
        far = d != 0 and i == 0
        ball(c, m, 'leaf' if far else F_BODY, c.X(fxo), c.Y(fyo), fr[0], fr[1], glint=False)
    # body, with the cheek / face step in profile (a lit bump that carries the face forward)
    body = c.ell(0, by, rx, ry)
    if d:
        body |= c.ell(rx * 0.8 * d, by + ry * 0.22, 2.2 if P else 2.8, 1.9 if P else 2.5)
    ball(c, body, F_BODY, cx, cy, rx, ry, cuts=(0.87, 0.48, 0.12))
    # pale belly: a tone lighter than the options; kept off the east edge in profile
    if d == 0:
        belly = c.ell(0, by + ry * 0.48, rx * 0.58, ry * 0.56) & body
    else:
        belly = c.ell((0.6 if P else 1.4) * d, by + ry * 0.55, rx * 0.40, ry * 0.44) & body
    ball(c, belly, F_BELLY, cx, cy, rx, ry, glint=False, lo=3, cuts=(0.85, 0.3, -1))
    # moss: rounded clumps, a crown and a row down the back; a brow clump over the eye in profile
    sx, sy = rx / 10.0, ry / 8.8
    if d == 0:
        cl = [(-5.6, -7.0, 3.0, 2.2), (5.8, -6.6, 2.6, 2.0), (-8.6, -2.4, 2.0, 2.4), (8.6, -2.2, 1.8, 2.2)]
    else:
        cl = [(-5.0, -7.2, 3.0, 2.3), (-8.6, -2.6, 2.4, 2.6), (-7.4, 3.0, 2.0, 2.0), (4.2, -6.0, 2.6, 1.8)]
        cl = [(xx * d, yy, a_, b_) for xx, yy, a_, b_ in cl]
    if P:
        cl = [cl[0], cl[1]] if d == 0 else [cl[0], cl[1]]
        cl = [(xx, yy, max(a_ * 0.75, 2.0), max(b_ * 0.75, 1.7)) for xx, yy, a_, b_ in cl]
    for (xx, yy, a_, b_) in cl:
        clump(c, xx * sx, by + yy * sy, a_, b_, F_MOSS, F_BODY, (cx, cy, rx, ry))
    # face
    if d == 0:
        ey = int(round(cy)) - 1
        lx, rxx = int(cx) - 5, int(cx) + 2
        if eyes in ('tight',):
            f_eye(c, lx, ey, 'tight_l')
            f_eye(c, rxx, ey, 'tight_r')
        else:
            f_eye(c, lx, ey, eyes)
            f_eye(c, rxx, ey, eyes)
        f_blush(c, lx - 1, ey + 3)
        f_blush(c, rxx + 2, ey + 3)
        f_mouth(c, int(cx) - 1, ey + 3, mouth)
    else:
        ey = int(round(cy)) - 1
        ex = int(cx) + (1 if P else 2) if d > 0 else int(cx) - (4 if P else 5)
        f_eye(c, ex, ey, {'tight': 'tight_r' if d > 0 else 'tight_l'}.get(eyes, eyes))
        f_blush(c, ex if d > 0 else ex + 1, ey + 3)
        mx = int(round(cx + rx * 0.8 * d)) + (0 if d > 0 else -1)
        f_mouth(c, mx if mouth in ('smile', 'dot') else mx - (1 if d > 0 else 0), ey + 3,
                mouth if mouth != 'smile' else 'dot')
    # the head-top growth anchor: the stem joint on the crown
    colx = int(round(cx - 0.5 - (2.4 if P else 0.8) * d))
    top = min(y for (x, y) in body if x == colx)
    joint = (colx, top - 1)
    c.marks['growth'] = list(joint)
    lean = 1 if d < 0 else -1
    if leaf == 'shield':
        # SLEEP IT OFF: the leaf swung forward and down over the front, a guard
        m = leaf_shape(c, cx + rx * 0.3 * d, cy + ry * 0.05, 3.6 if P else 4.6, 2.0 if P else 2.5, 1.25 * d)
        return body, m
    if leaf != 'none':
        if P:
            data = LEAF_P_FLAT if leaf == 'flat' else LEAF_P
        else:
            data = LEAF_W_FLAT if leaf == 'flat' else LEAF_W
            if leaf == 'up':
                c.fig.put(joint[0], joint[1], F_LEAF, 2)
                joint = (joint[0], joint[1] - 1)
        f_leaf(c, joint, lean, data)
    return body, None


def leaf_shape(c, cx, cy, rx, ry, rot):
    """A leaf as a rotated ellipse with a midrib (the shield and the blanket)."""
    fig = c.fig
    m = set()
    ca, sa = math.cos(rot), math.sin(rot)
    for y in range(int(cy - rx) - 2, int(cy + rx) + 3):
        for x in range(int(cx - rx) - 2, int(cx + rx) + 3):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u = (px * ca + py * sa) / rx
            v = (-px * sa + py * ca) / ry
            if u * u + v * v <= 1.0 and fig.inside(x, y):
                m.add((x, y))
    for (x, y) in m:
        u = (x + 0.5 - cx) / rx
        v = (y + 0.5 - cy) / ry
        t = tone_of(light_of(u * 0.8, v * 0.8), (0.8, 0.45, 0.05))
        fig.put(x, y, F_LEAF, max(2, t))
    # midrib along the long axis, tone 2, and its dark lower edge
    for i in range(-int(rx) + 1, int(rx)):
        p = (int(round(cx + i * ca)), int(round(cy + i * sa)))
        if p in m:
            fig.put(p[0], p[1], F_LEAF, 2)
    return m


def f_sparkles(c, pts):
    """Healing motes for SLEEP IT OFF: 2 px glowflora clusters inside the silhouette,
    finite (the special's frames only), off under reduced motion."""
    for (x, y) in pts:
        for p in ((x, y), (x + 1, y)):
            if p in c.fig.px:
                c.fig.glow(p[0], p[1], F_GLOW, 4)
                c.keep.add(p)


def final_world(kind):
    d = {'S': 0, 'E': 1, 'W': -1}.get(kind, 0)
    c = FCtx(False, d)
    if kind in ('S', 'E', 'W'):
        mochi(c, eyes='lid')
    elif kind == 'hop1':       # crouch: squash, splayed nubs, the leaf pressed flat
        mochi(c, sq=(1.1, 0.84), eyes='lid', leaf='flat', feet='splay')
    elif kind == 'hop2':       # rise: stretch, nubs trailing
        mochi(c, sq=(0.94, 1.06), lift=1.0, eyes='open', feet='tuck')
    elif kind == 'hop3':       # airborne: round, tucked, the leaf lifting
        mochi(c, sq=(0.98, 1.0), lift=2.0, eyes='open', mouth='o', feet='tuck')
    elif kind == 'hop4':       # land: a heavy squash held a frame, eyes sinking back to the lid
        mochi(c, sq=(1.12, 0.82), eyes='closed', leaf='flat', feet='splay', mouth='dot')
    elif kind == 'react':      # roused: eyes wide, the leaf up, a little stretch
        mochi(c, sq=(0.96, 1.04), eyes='wide', mouth='o', leaf='up')
    return finish(c), c.marks


def final_nap():
    c = FCtx(False, 0)
    fig = c.fig
    cx, cy, rx, ry = c.X(0.5), c.Y(-6.2), 11.0, 5.8
    body = fig.ellipse(cx, cy, rx, ry)
    ball(c, body, F_BODY, cx, cy, rx, ry, cuts=(0.87, 0.48, 0.12))
    belly = fig.ellipse(cx - 0.5, cy + 2.4, 6.2, 3.2) & body
    ball(c, belly, F_BELLY, cx, cy, rx, ry, glint=False, lo=3, cuts=(0.85, 0.3, -1))
    for (xx, yy, a_, b_) in ((-9.6, -7.4, 2.2, 2.2), (8.6, -6.6, 2.0, 2.0)):
        clump(c, xx, yy, a_, b_, F_MOSS, F_BODY, (cx, cy, rx, ry))
    # the curled leaf laid over the back as a blanket, its curl at the west end
    m = leaf_shape(c, cx + 0.5, cy - 4.4, 8.2, 2.5, 0.08)
    lx = min(x for x, _ in m)
    ly = min(y for x, y in m if x == lx)
    for (dx, dy, t) in ((0, -1, 3), (1, -1, 4), (-1, 0, 3), (0, 0, 1), (-1, 1, 2), (0, 1, 2)):
        fig.put(lx + dx, ly + dy, F_LEAF, t)
    c.marks['growth'] = [int(cx) - 2, int(cy - 6)]
    ey = int(round(cy)) + 0
    f_eye(c, int(cx) - 5, ey, 'closed')
    f_eye(c, int(cx) + 1, ey, 'closed')
    f_blush(c, int(cx) - 7, ey + 2)
    f_blush(c, int(cx) + 4, ey + 2)
    f_mouth(c, int(cx) - 1, ey + 3, 'dot')
    return finish(c), c.marks


def final_perch(kind, d):
    c = FCtx(True, d)
    if kind == 'perch':        # sitting on the shoulder, turned to the foe, drowsy but watching
        mochi(c, eyes='lid')
    elif kind == 'cling':      # the folk is hit: flattened, holding on, eyes screwed shut
        mochi(c, sq=(1.12, 0.8), eyes='tight', leaf='flat', feet='splay', mouth='dot')
    elif kind == 'cheer':      # a win: a stretch up, happy eyes, the leaf raised
        mochi(c, sq=(0.96, 1.04), eyes='happy', mouth='open', leaf='back')
    elif kind == 'special':    # SLEEP IT OFF: eyes shut, the leaf swung over as a guard, healing motes
        body, shield = mochi(c, eyes='closed', mouth='dot', leaf='shield')
        xs = sorted({x for x, _ in body})
        cyy = sum(y for _, y in body) / len(body)
        f_sparkles(c, [(xs[2], int(cyy) - 3), (xs[len(xs) // 2], int(cyy) + 3)])
    return finish(c), c.marks


FINAL_VIEWS = (
    ('S idle', lambda: final_world('S')), ('E idle', lambda: final_world('E')),
    ('W idle', lambda: final_world('W')),
    ('hop 1', lambda: final_world('hop1')), ('hop 2', lambda: final_world('hop2')),
    ('hop 3', lambda: final_world('hop3')), ('hop 4', lambda: final_world('hop4')),
    ('S react', lambda: final_world('react')), ('S nap', final_nap),
) + tuple((f'{f} {k}', (lambda k=k, d=d: final_perch(k, d)))
          for f, d in (('E', 1), ('W', -1)) for k in ('perch', 'cling', 'cheer', 'special'))

FINAL = dict(
    label='A final', name='Tuft-back mochi with the curled leaf (final)', chosen='A',
    grafts=['B: the single curled leaf is the head-top growth (one leaf, stiff, curled; the nap blanket and '
            'the SLEEP IT OFF guard)',
            'B: the biggest eyes, standardised to the family eye: 3 x 3 ink with a 2 px glint',
            'C (graders): the REST temperament: half-lidded idle eyes, a heavy settle after each hop'],
    palette=['leaf_warm', 'leaf_cool', 'grass_warm', 'plaster', 'berry_warm'],   # + glowflora on the special
    pose='Drowsy and loyal: it sits heavy on its nubs with half-closed eyes, hops only when it has to and '
         'settles slowly, like a sleepy child following a step behind.',
    parts=[
        'feet (two nubs): leaf_warm, near; leaf, far; layer 1 (far) / 2 (near); anchor foot; S both, E/W far '
        'one behind; splay on crouch and land, tuck in the air (family foot line: the nubs sit on row 27)',
        'body ball + cheek step: leaf_warm, layer 3, anchor hip; the cheek bump leads in E/W; breath squashes 1 px',
        'pale belly: plaster (tones 3-5), layer 4, anchor hip; S centre, E/W forward but 4 px off the front edge',
        'moss clumps: leaf_cool, layer 5, anchor hip (back) and head (crown, brow); crown + back in E/W, crown + '
        'shoulders in S; fixed per facing (no per-frame repaint), ride the squash',
        'face block: eyes (ink 3 x 3 with a 2 px plaster glint: lid / open / wide / closed / happy / tight), '
        'blush (berry_warm), mouth; layer 6, anchor head; S/E/W',
        'head-top growth: the curled leaf on the crown joint (growthAnchor), grass_warm, layer 7, anchor head; '
        'leans back from the facing; flat (crouch, land, cling), up (rise, react, cheer), blanket (nap), '
        'shield (special)',
        'special effect: glowflora motes, 2 px, inside the silhouette, layer 8; finite, none under reduced motion',
    ],
    notes=[
        'Walk is the spec\'s 4-frame hop (crouch, rise, air, land); the land squash holds a second frame and the '
        'lid comes back down, so it reads REST, not bouncy ROAM.',
        'Growth stages (rig variants of the same poses): 1 the curled leaf; 2 a second, smaller leaf at the '
        'joint; 3 a bud opening at the curl. The joint never moves.',
        'Perch: a 16 px redraw, the leaf curled back and down to clear small folk; it turns to the foe (E and W). '
        'perchAnchor is the foot line centre (12, 22).',
        'Moss: round leaf_cool mounds on a warm leaf_warm skin, never on grey stone (Cairn) and never in rows '
        '(Tam\'s knit). The leaf is fresh grass_warm, stiff and curled, not a floppy cap (Mote).',
        'Open for Matt: cling and special sit at 14 px (squashed / leaf lowered as a guard); react is 26 px with '
        'the leaf raised. The idle and the perch are on target (24 and 16).',
        'Compared with Eastward-04 (Sam scaled to 24 px): her 2-3 px hair clumps for the moss, 3-4 tones a '
        'material, a dark per-material outline and a glinting eye block.',
    ],
)


def build_final():
    os.makedirs(SCRATCH, exist_ok=True)
    views, nums, marks, ok = [], {}, {}, True
    for cap, fn in FINAL_VIEWS:
        fig, mk = fn()
        im = fig.image()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        print(f"final {cap:10s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
              f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        marks[cap] = mk
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Mossling final: A, the tuft-back mochi, with B\'s curled leaf and eyes', [entry], OUT_FINAL,
                    note='About 24 art px, cell 32 x 32, foot (16, 28). Idles, the 4-frame hop, react, nap; perch '
                         'states at 16 px in 24 x 24, foot (12, 22).')
    growth = {k: v.get('growth') for k, v in marks.items()}
    eyes = {k: v.get('eyes') for k, v in marks.items()}
    perch_anchor = {k: [PFX, PFY] for k in marks if k[2:] in ('perch', 'cling', 'cheer', 'special')}
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], pose=FINAL['pose'],
                growthAnchor=growth,
                eyeBlocks=dict(size=[3, 3], glint='2 px, the west column, top two rows (plaster 5)',
                               topLeft=eyes),
                footLine=dict(world=[FX, FY - 1], perch=[PFX, PFY - 1],
                              note='nubs fill the row above the anchor; the outline lands on the anchor row'),
                perchAnchor=perch_anchor, measure=nums, notes=FINAL['notes'], _ok=ok)


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    out = []
    ok = True
    for o in OPTIONS:
        o['views'] = []
        nums = {}
        for v, cap in VIEWS:
            im = o['fn'](v).image()
            o['views'].append((cap, im))
            im.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(im)
            g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.06,
                     colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
            ok &= all(g.values())
            print(f"{o['label']} {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  "
                  f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
            nums[cap]['height_px'] = height(im)
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('Mossling (REST familiar, BLOB): the blob\'s form and its moss', OPTIONS, OUT_PNG,
                    note='About 24 art px, cell 32 x 32, foot (16, 28); perch 16 px in 24 x 24, foot (12, 22). '
                         'Views: S, E, W idle, S hop, S nap, E and W perch.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='mossling', kind='familiar', species='BLOB', family='REST', height_art_px=24,
                       cell=[W, H], foot=[FX, FY], perch_cell=[PW, PH], perch_foot=[PFX, PFY],
                       question='The blob\'s form and its moss: keep the round mossy blob with a sprout players '
                                'know, at the new density, reading on grass and apart from Puffcap and Tam.',
                       options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
