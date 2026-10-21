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


# --- final: reconciled to Matt's 1x master (moss_sheet.png) ------------------------------
# Matt (21 Oct 18:17): the 1x design is the master and every density draws the same design.
# The Mossling's 1x master is his moss_sheet.png: a green mochi under a red-brown mushroom
# cap (clay, lit at the upper left, cream spots), a pale cream rim under the cap, a small
# dark two-leaf sprout on the cap, a dark eye and a blush. This 2x final draws that design
# with more detail; the earlier final (A with B's curled leaf) stays as option A in the
# options sheet. Geometry is the 1x master's x 2 (scripts/art/characters/masters/mossling.py).
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/mossling-final.png')
F_BODY, F_CAP, F_RIM, F_BLUSH, F_GLOW = 'leaf', 'clay', 'plaster', 'berry', 'glowflora'

SPROUT_2X = ((0, 0, 'leaf', 2), (0, -1, 'leaf', 3),
             (-1, -2, 'leaf', 3), (-2, -2, 'leaf', 4), (-2, -3, 'leaf', 4), (-3, -3, 'leaf', 3),
             (1, -2, 'leaf', 3), (2, -2, 'leaf', 2), (2, -3, 'leaf', 3), (3, -3, 'leaf', 2))
SPROUT_P = ((0, 0, 'leaf', 2), (-1, -1, 'leaf', 4), (-2, -2, 'leaf', 3), (-1, -2, 'leaf', 4),
            (1, -1, 'leaf', 3), (1, -2, 'leaf', 3), (2, -2, 'leaf', 2))
SPROUT_NAP = ((0, 0, 'leaf', 2), (-1, 0, 'leaf', 3), (-2, 1, 'leaf', 3), (-3, 1, 'leaf', 2),
                (1, 0, 'leaf', 3), (2, 1, 'leaf', 2))


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


def f_eye(c, x, y, mode):
    """The family eye: 3 x 3 ink with a 2 px glint down its lit (west) column. lid: a heavy
    lid row in the skin's tone 1 (REST); closed: a u; happy: a ^; tight_l/_r: > and <."""
    pts = []
    if mode in ('open', 'lid', 'wide'):
        pts = [(xx, yy, 'ink', 0) for yy in range(y, y + 3) for xx in range(x, x + 3)]
        g0 = y + (1 if mode == 'lid' else 0)
        pts = [p for p in pts if not (p[0] == x and p[1] in (g0, g0 + 1))]
        pts += [(x, g0, F_RIM, 5), (x, g0 + 1, F_RIM, 5)]
        if mode == 'lid':
            pts = [p for p in pts if p[1] != y] + [(x + i, y, F_BODY, 1) for i in range(3)]
            pts = [p for p in pts if p[1] < y + 3]
    elif mode == 'closed':
        pts = [(x, y + 1, 'ink', 0), (x + 1, y + 2, 'ink', 0), (x + 2, y + 1, 'ink', 0)]
    elif mode == 'happy':
        pts = [(x, y + 2, 'ink', 0), (x + 1, y + 1, 'ink', 0), (x + 2, y + 2, 'ink', 0)]
    elif mode == 'tight_l':
        pts = [(x, y, 'ink', 0), (x + 1, y + 1, 'ink', 0), (x + 2, y + 1, 'ink', 0), (x, y + 2, 'ink', 0)]
    elif mode == 'tight_r':
        pts = [(x + 2, y, 'ink', 0), (x + 1, y + 1, 'ink', 0), (x, y + 1, 'ink', 0), (x + 2, y + 2, 'ink', 0)]
    for (xx, yy, fam, t) in pts:
        c.fig.put(xx, yy, fam, t)
        c.keep.add((xx, yy))
    c.marks.setdefault('eyes', []).append([x, y])


def f_marks(c, pts):
    """Face marks (blush, mouth), only where the body already is: never past the silhouette."""
    for (xx, yy, fam, t) in pts:
        if (xx, yy) not in c.fig.px or c.fig.px[(xx, yy)][0] != F_BODY:
            continue
        c.fig.put(xx, yy, fam, t)
        c.keep.add((xx, yy))


def body_mask(c, cx, cy, rx, ry, p=2.5):
    """The mochi: a soft superellipse, squarer than a ball, wide under the cap."""
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = abs(x + 0.5 - cx) / rx, abs(y + 0.5 - cy) / ry
            if u ** p + v ** p <= 1.0 and c.fig.inside(x, y):
                out.add((x, y))
    return out


def cap(c, cx, base, rx, h, rim=2, rot=0.0):
    """The mushroom cap: a low dome (clay) lit at the upper left with two cream spots, on a
    pale rim (plaster) with a lit left end and a shaded right end; rot tips it."""
    fig = c.fig
    ca, sa = math.cos(rot), math.sin(rot)
    dome, band = set(), set()
    for y in range(int(base - h - rx * abs(sa)) - 3, int(base + rim + rx * abs(sa)) + 3):
        for x in range(int(cx - rx) - 3, int(cx + rx) + 4):
            px, py = x + 0.5 - cx, y + 0.5 - base
            u = px * ca + py * sa
            v = -px * sa + py * ca
            if v < 0 and (u / rx) ** 2 + (v / h) ** 2 <= 1.0:
                dome.add((x, y, u, v))
            elif 0 <= v < rim and abs(u) <= rx - 0.4 - 0.5 * v:
                band.add((x, y, u, v))
    for (x, y, u, v) in dome:
        t = tone_of(light_of(u / rx * 1.05, (v / h) * 0.9 + 0.15), (0.83, 0.5, 0.12))
        if u / rx > 0.78 and v > -h * 0.45:
            t = min(t, 1)
        fig.put(x, y, F_CAP, t)
    # cream spots (plaster), upper left: a big one and a small one
    for (sx, sy, srx, sry) in ((-0.18, -0.62, 0.17, 0.2), (-0.55, -0.3, 0.15, 0.18), (0.32, -0.42, 0.09, 0.14)):
        for (x, y, u, v) in dome:
            if ((u / rx - sx) / srx) ** 2 + ((v / h - sy) / sry) ** 2 <= 1.0:
                lit = (u / rx - sx) < 0 and (v / h - sy) < 0
                fig.put(x, y, F_RIM, 5 if lit else 4 if sx < 0.2 else 3)
    for (x, y, u, v) in band:
        r = u / rx
        if v < 1:
            t = 4 if r < -0.55 else 3 if r < 0.35 else 2
        else:
            t = 3 if r < -0.55 else 2 if r < 0.55 else 1
        fig.put(x, y, F_RIM, t)
    return {(x, y) for x, y, _, _ in dome}, {(x, y) for x, y, _, _ in band}


def under_shadow(c, band, body, d):
    """The shadow the cap throws on the mochi: one row of leaf 1 under the rim, deepening
    to leaf 0 under the far (east) end, where the master has its ink notch."""
    fig = c.fig
    xs = sorted({x for x, _ in band})
    for (x, y) in band:
        q = (x, y + 1)
        if q in body and q not in band:
            fig.put(q[0], q[1], F_BODY, 0 if x >= xs[-1] - 2 else 1 if x > xs[0] + 1 else 2)
    # the deep notch down the east side under the cap (the master's ink column)
    by0 = max(y for _, y in band) + 1
    for (x, y) in body:
        if x in (xs[-1] - 2, xs[-1] - 3) and by0 <= y < by0 + (5 if not c.perch else 3) and (x + 1, y) in body:
            fig.put(x, y, F_BODY, 0)


def mochi2(c, sq=(1.0, 1.0), lift=0.0, eyes='lid', mouth='none', cap_mode='on', feet='stand', sprout='up'):
    """One pose of the master's design at 2x. World: rim at rows 12-13, the body 14-25, feet
    26-27 (the foot line), cap dome 6-11, sprout 2-5. Perch (16 px): the same, smaller."""
    fig, d, P = c.fig, c.d, c.perch
    cx = c.fx + (1.0 if not P else 1.0)
    rx0, ry0 = (11.0, 7.0) if not P else (7.0, 4.0)
    rx, ry = rx0 * sq[0], ry0 * sq[1]
    foot_h = 2 if not P else 1
    cy = c.fy - foot_h - ry - lift
    # feet: two nubs on the foot line; the far one darker in E/W, tucked in the air
    if not P:
        if feet == 'tuck':
            fpos = [(-3.6, cy + ry - 0.6), (3.6, cy + ry - 0.6)]
        else:
            k = 1.25 if feet == 'splay' else 1.0
            fpos = [(-5.5 * k, c.fy - 1.6), (4.5 * k, c.fy - 1.6)] if d == 0 else \
                [(-5.0 * d, c.fy - 1.6), (3.0 * d, c.fy - 1.5)]
        for i, (fxo, fyo) in enumerate(fpos):
            m = fig.ellipse(cx + fxo, fyo, 2.3, 1.6)
            far = d != 0 and i == 0
            ball(c, m, F_BODY, cx + fxo, fyo, 2.3, 1.6, glint=False, cuts=(0.9, 0.6, 0.3) if far else (0.8, 0.45, 0.1))
    body = body_mask(c, cx, cy, rx, ry)
    if d and not P:
        body |= fig.ellipse(cx + rx * 0.82 * d, cy + ry * 0.25, 2.4, 2.6)
    ball(c, body, F_BODY, cx, cy, rx, ry * 1.1, cuts=(0.85, 0.42, 0.06))
    # the pale front: leaf 4 to 5 on the lit lower front, as the master's lit belly
    if d == 0:
        belly = fig.ellipse(cx - 1.0, cy + ry * 0.35, rx * 0.5, ry * 0.5) & body
    else:
        belly = fig.ellipse(cx + 0.5 * d - 1.0, cy + ry * 0.35, rx * 0.42, ry * 0.5) & body
    for (x, y) in belly:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        fig.put(x, y, F_BODY, 5 if u < -0.4 and v < 0.25 else 4)
    # moss: a few darker leaf clusters on the lower back (texture the master has as dark bands)
    if not P:
        for (mx, my) in (((-7.5 if d >= 0 else 5.5), 2.6), ((-3.0 if d >= 0 else 1.5), 4.6)):
            for (ox, oy, t) in ((0, 0, 2), (1, 0, 2), (2, 0, 1), (1, 1, 1)):
                p = (int(cx + mx) + ox, int(cy + my) + oy)
                if p in body and fig.px[p][1] >= 2:
                    fig.put(p[0], p[1], F_BODY, t)
    # cap
    top_body = min(y for _, y in body)
    base = float(top_body)
    crx, ch = (11.3, 6.2) if not P else (7.4, 3.4)
    rot = 0.0
    if cap_mode == 'tipped':            # pulled down and forward over the eyes (nap, special)
        base += 3.0 if not P else 2.0
        rot = 0.12 * (d or 1) * (-1 if d < 0 else 1) if d else 0.1
    elif cap_mode == 'pressed':         # cling: squashed down on the head
        base += 1.0
        ch *= 0.85
    elif cap_mode == 'back':            # cheer: tipped back off the brow
        rot = -0.18 * (d or 1)
    elif cap_mode == 'lift':            # react: jumps up a pixel
        base -= 1.0
    dome, band = cap(c, cx, base, crx, ch, rim=2, rot=rot)
    under_shadow(c, band, body, d)
    # face, under the rim
    ey = int(base) + 3
    if cap_mode == 'tipped':
        eyes = 'hidden'
    if eyes != 'hidden':
        if d == 0:
            lx, rxx = int(cx) - 6, int(cx) + 3
            f_eye(c, lx, ey, 'tight_l' if eyes == 'tight' else eyes)
            f_eye(c, rxx, ey, 'tight_r' if eyes == 'tight' else eyes)
        else:
            ex = int(cx) - 1 if d > 0 else int(cx) - 2
            if P:
                ex = int(cx) + (0 if d > 0 else -3)
            f_eye(c, ex, ey, ('tight_r' if d > 0 else 'tight_l') if eyes == 'tight' else eyes)
    # blush: behind and below the eye in profile (as the master), outside both eyes in S
    by_ = ey + 3
    if d == 0:
        f_marks(c, [(int(cx) - 8, by_, F_BLUSH, 4), (int(cx) - 7, by_, F_BLUSH, 4),
                    (int(cx) + 6, by_, F_BLUSH, 4), (int(cx) + 7, by_, F_BLUSH, 4)])
    else:
        bx = int(cx) - (6 if not P else 4) if d > 0 else int(cx) + (4 if not P else 2)
        f_marks(c, [(bx, by_, F_BLUSH, 4), (bx + 1, by_, F_BLUSH, 4)] +
                ([(bx + 2, by_, F_BLUSH, 3)] if not P and d > 0 else [(bx - 1, by_, F_BLUSH, 3)] if not P else []))
    if mouth != 'none':
        mx = int(cx) - 1 if d == 0 else int(cx) + (3 if d > 0 else -4)
        my = by_ - (0 if not P else 0)
        if mouth == 'o':
            f_marks(c, [(mx, my, 'ink', 0), (mx + 1, my, 'ink', 0), (mx, my + 1, F_BLUSH, 2), (mx + 1, my + 1, F_BLUSH, 2)])
        elif mouth == 'open':
            f_marks(c, [(mx, my, 'ink', 0), (mx + 1, my, 'ink', 0), (mx, my + 1, F_BLUSH, 3), (mx + 1, my + 1, F_BLUSH, 3)])
        else:
            f_marks(c, [(mx, my, F_BODY, 1), (mx + 1, my, F_BODY, 1)])
    # sprout: the head-top growth anchor on the cap's crown
    jx = int(cx) - 1 if not P else int(cx) - 1
    col = [y for x, y in dome if x == jx] or [int(base - ch)]
    joint = (jx, min(col) - 1)
    c.marks['growth'] = list(joint)
    data = SPROUT_NAP if sprout == 'droop' else (SPROUT_P if P else SPROUT_2X)
    for (dx, dy, fam, t) in data:
        fig.put(joint[0] + dx, joint[1] + dy, fam, t)
    return body, dome


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
        mochi2(c, eyes='lid')
    elif kind == 'hop1':       # crouch: squash, splayed nubs, the cap pressed down
        mochi2(c, sq=(1.06, 0.8), eyes='lid', feet='splay', cap_mode='pressed')
    elif kind == 'hop2':       # rise: a stretch, nubs trailing
        mochi2(c, sq=(0.95, 1.0), lift=0.5, eyes='open', feet='tuck')
    elif kind == 'hop3':       # airborne: round and tucked
        mochi2(c, sq=(0.98, 0.9), lift=1.2, eyes='open', mouth='o', feet='tuck')
    elif kind == 'hop4':       # land: a heavy squash held a frame, the lid sinking back
        mochi2(c, sq=(1.08, 0.78), eyes='closed', feet='splay', cap_mode='pressed', mouth='dot')
    elif kind == 'react':      # roused: eyes wide, the cap jumps a pixel
        mochi2(c, sq=(0.97, 0.96), eyes='wide', mouth='o', cap_mode='lift')
    return finish(c), c.marks


def final_nap():
    """Curled low and wide; the cap tips forward like a hat over the eyes, the sprout droops."""
    c = FCtx(False, 0)
    fig = c.fig
    cx, cy, rx, ry = c.fx + 1.0, c.fy - 5.0, 12.0, 4.6
    body = body_mask(c, cx, cy, rx, ry, p=2.2)
    ball(c, body, F_BODY, cx, cy, rx, ry * 1.1, cuts=(0.85, 0.42, 0.06))
    belly = fig.ellipse(cx - 1.0, cy + ry * 0.4, rx * 0.5, ry * 0.45) & body
    for (x, y) in belly:
        fig.put(x, y, F_BODY, 4)
    top = min(y for _, y in body)
    dome, band = cap(c, cx - 0.5, top + 4.0, 11.6, 5.6, rim=2, rot=0.07)
    under_shadow(c, band, body, 0)
    yb = max(y for _, y in band) + 2
    f_marks(c, [(int(cx) - 7, yb, F_BLUSH, 4), (int(cx) - 6, yb, F_BLUSH, 4),
                (int(cx) + 5, yb, F_BLUSH, 4), (int(cx) + 6, yb, F_BLUSH, 4),
                (int(cx) - 1, yb + 1, F_BODY, 1), (int(cx), yb + 1, F_BODY, 1)])
    jx = int(cx) - 1
    joint = (jx, min(y for x, y in dome if x == jx) - 1)
    c.marks['growth'] = list(joint)
    for (dx, dy, fam, t) in SPROUT_NAP:
        fig.put(joint[0] + dx, joint[1] + dy, fam, t)
    return finish(c), c.marks


def final_perch(kind, d):
    c = FCtx(True, d)
    if kind == 'perch':        # on the shoulder, turned to the foe, drowsy but watching
        mochi2(c, eyes='lid')
    elif kind == 'cling':      # the folk is hit: flattened, cap pressed down, eyes screwed shut
        mochi2(c, sq=(1.1, 0.8), eyes='tight', cap_mode='pressed')
    elif kind == 'cheer':      # a win: a stretch, happy eyes, the cap tipped back
        mochi2(c, sq=(0.96, 1.08), eyes='happy', mouth='open', cap_mode='back')
    elif kind == 'special':    # SLEEP IT OFF: the cap pulled down over the eyes as a guard, healing motes
        body, dome = mochi2(c, cap_mode='tipped')
        xs = sorted({x for x, _ in body})
        ys = sorted({y for _, y in body})
        f_sparkles(c, [(xs[2], ys[-2]), (xs[-4], ys[-3])])
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
    label='Master final', name='The capped mochi: Matt\'s 1x master at 2x (final)', chosen='Matt\'s 1x master',
    reconciled='reconciled to Matt\'s 1x master (moss_sheet.png)',
    grafts=['From the family rig: 3 x 3 ink eyes with a 2 px glint (half-lidded in idle: REST)',
            'From the family rig: the head-top growth anchor (the two-leaf sprout, on the cap\'s crown)',
            'From the family rig: the foot line (two nubs) and the 4-frame hop',
            'From the graders: a heavy settle after each hop, so it reads REST, not bouncy ROAM'],
    palette=['leaf', 'clay', 'plaster', 'berry'],   # + glowflora on the special only
    pose='Drowsy and loyal: it sits heavy under its cap with half-closed eyes, hops only when it has to and '
         'settles slowly, like a sleepy child following a step behind.',
    parts=[
        'feet (two nubs): leaf, layer 1 (far) / 2 (near), anchor foot; E/W far nub darker; splay on crouch '
        'and land, tuck in the air (the family foot line: nubs fill rows 26-27, outline on 28)',
        'mochi body + cheek step: leaf, layer 3, anchor hip; the cheek leads in E/W; breath squashes 1 px',
        'pale front: leaf tones 4-5 on the lit lower front, layer 4, anchor hip (the master keeps the belly '
        'green: its pale part is the lit front, not a plaster patch)',
        'moss clusters: leaf 1-2 on the lower back, layer 4, anchor hip; fixed per facing',
        'face: 3 x 3 ink eyes (lid / open / wide / closed / happy / tight) with a 2 px plaster glint, berry '
        'blush behind and below the eye in profile, an optional mouth; layer 5, anchor head',
        'cap shadow: leaf 0-1 under the rim and the deep notch down the east side, layer 6, anchor head',
        'mushroom cap: clay dome (lit upper left, dark lower right) with plaster spots, on a plaster rim; '
        'layer 7, anchor head; one rigid part that presses (crouch, land, cling), lifts (react), tips back '
        '(cheer) and tips forward over the eyes (nap, special)',
        'head-top growth: the two-leaf sprout on the cap\'s crown joint (growthAnchor), leaf, layer 8, anchor '
        'head (rides the cap); droops in the nap',
        'special effect: glowflora motes, 2 px, inside the silhouette, layer 9; finite, none under reduced motion',
    ],
    notes=[
        'Reconciled to Matt\'s 1x master (moss_sheet.png): the same cap, colours and proportions; '
        'more detail at 2x. The earlier final (A with B\'s curled leaf) stays as option A in mossling-options.png.',
        'Size: the master is 15 px at 1x with its sprout (cap and body 12), so the 2x idle is 28 px: the '
        'body and cap are the familiar\'s 24 px; the sprout sits above them, as on the master.',
        'Walk: the spec\'s 4-frame hop (crouch, rise, air, land); the land squash holds a second frame and '
        'the lid comes back down, so it reads REST, not ROAM.',
        'Growth stages (rig variants of the same poses): 1 the two-leaf sprout; 2 a third leaf and a bud; '
        '3 the bud opens on the cap. The joint never moves.',
        'Perch: a 16 px redraw turned to the foe; perchAnchor is the foot line centre (12, 22).',
        'Compared with Matt\'s moss_sheet.png at 8x (same cap tones clay 1-4, plaster rim, leaf body) and '
        'with Eastward-04 (Sam at 24 px) for tones a material and the eye block.',
    ],
)


def build_final():
    os.makedirs(SCRATCH, exist_ok=True)
    views, nums, marks, ok = [], {}, {}, True
    for cap_, fn in FINAL_VIEWS:
        fig, mk = fn()
        im = fig.image()
        views.append((cap_, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap_.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        print(f"final {cap_:10s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
              f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap_] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap_]['height_px'] = height(im)
        marks[cap_] = mk
    # the master's views under the names the 1x master compares against
    for cap_, name in (('S idle', 'S-idle'), ('E idle', 'E-idle'), ('W idle', 'W-idle'),
                       ('E perch', 'E-perch'), ('W perch', 'W-perch')):
        dict(views)[cap_].save(os.path.join(SCRATCH, f'final-{name}.png'))
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Mossling final: Matt\'s 1x master (the capped mochi) drawn at 2x', [entry], OUT_FINAL,
                    note='Reconciled to Matt\'s 1x master (moss_sheet.png). Cell 32 x 32, foot (16, 28); perch '
                         'states at 16 px in 24 x 24, foot (12, 22).')
    growth = {k: v.get('growth') for k, v in marks.items()}
    eyes = {k: v.get('eyes') for k, v in marks.items()}
    perch_anchor = {k: [PFX, PFY] for k in marks if k[2:] in ('perch', 'cling', 'cheer', 'special')}
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], reconciled=FINAL['reconciled'],
                grafts=FINAL['grafts'], parts=FINAL['parts'], palette=FINAL['palette'], pose=FINAL['pose'],
                growthAnchor=growth,
                eyeBlocks=dict(size=[3, 3], glint='2 px, the west column (plaster 5)', topLeft=eyes),
                footLine=dict(world=[FX, FY - 1], perch=[PFX, PFY - 1],
                              note='nubs fill the rows above the anchor; the outline lands on the anchor row'),
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
