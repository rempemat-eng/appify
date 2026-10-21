"""Roamling design options (Claude J design sheets, 21 Oct).

The Roamling, the ROAM family Grassling (species RAT): a starter familiar that follows
the folk a step behind, naps curled against them, rides the shoulder in fights, and sets
the type (ROAM) and the rested special (SECOND WIND). Today's sprite (scripts/art/pets.py,
`roamling`) is a leaf-green rat with leaf ears, a curled vine tail and a head sprout. The
redesign keeps the rat, the leafy ears and the vine tail as ideas, moves the fur to path,
earth or timber (not Mossling green) and puts the grass in the accents.

Cell 32 x 32 art px, foot anchor (16, 28), about 24 art px tall. The shoulder perch is a
16 art px redraw in a 24 x 24 cell, foot (12, 22). The question: ears, tail and grassy
features of a small roaming critter.

    A  Field mouse: big round ears lined with grass, a long stem tail with a leaf sprig
    B  Scruffy vole: a grass-tuft crest and forelock, small round ears, a tasselled stub tail
    C  Hedge hare: tall round-tipped ears with a leaf clipped to each, pale eye rings, a puff

Every view is drawn in its own facing: W places the parts on the other side, and each part
is shaded after placement with the light from the upper left, so the lit side stays west.

Run from the repo root:
    CHAR_VIEWS=<scratch>/designs python3 scripts/art/characters/designs/roamling.py
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(REPO, 'docs/vision/characters/designs/roamling-options.png')
OUT_JSON = os.path.join(REPO, 'docs/vision/characters/designs/roamling.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(REPO, '.char-views')), 'roamling')

CELL, FOOT = 32, (16, 28)
PCELL, PFOOT = 24, (12, 22)


# --- painting helpers --------------------------------------------------------------------
class P:
    """A Fig plus a facing. Design coordinates are drawn facing east (or front for S); in W
    every centre is re-placed on the other side before the mask is made, and shading runs
    on the placed mask, so the light stays upper left."""

    def __init__(self, view: str, size: int = CELL):
        self.f = sk.Fig(size, size)
        self.n = size
        self.flip = view == 'W'
        self.keep = set()
        self.glows = []   # light pixels, laid after the cleanup so nothing copies them

    def X(self, x):
        return self.n - 1 - x if self.flip else x

    def EX(self, x, w):
        """The left pixel of a w-wide face feature placed at design x."""
        return self.n - x - w if self.flip else x

    def CX(self, cx):
        return self.n - cx if self.flip else cx

    def ell(self, cx, cy, rx, ry, rot=0.0, dy=0):
        cx = self.CX(cx)
        rot = -rot if self.flip else rot
        c, s = math.cos(rot), math.sin(rot)
        out = set()
        cy = cy + dy
        r = max(rx, ry) + 1
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                ddx, ddy = x + 0.5 - cx, y + 0.5 - cy
                u = (ddx * c + ddy * s) / rx
                v = (-ddx * s + ddy * c) / ry
                if u * u + v * v <= 1.0 and self.f.inside(x, y):
                    out.add((x, y))
        return out

    def poly(self, pts, dy=0):
        return self.f.poly([(self.CX(x), y + dy) for x, y in pts])

    def stroke(self, pts, r=1.0, dy=0):
        out = set()
        for (xa, ya), (xb, yb) in zip(pts, pts[1:] or pts):
            n = max(int(max(abs(xb - xa), abs(yb - ya)) * 3), 1)
            for i in range(n + 1):
                out |= self.ell(xa + (xb - xa) * i / n, ya + (yb - ya) * i / n, r, r, dy=dy)
        return out

    def put(self, x, y, fam, tone, keep=False):
        self.f.put(self.X(x), y, fam, tone)
        if keep:
            self.keep.add((self.X(x), y))


def bbox(mask):
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    return min(xs), min(ys), max(xs), max(ys)


def ball(f, mask, fam, glint=True, lift=0.0):
    """A round part: a lit cap at the upper left (a circle, so the terminator follows the
    form), a body, a dark crescent at the lower right and an underside row, all one hard
    step apart. Lit tones lean warm, the deepest cool (the fur's own siblings)."""
    mask = set(mask)
    if not mask:
        return
    x0, y0, x1, y1 = bbox(mask)
    cx, cy = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2
    rx, ry = max(1.0, (x1 - x0 + 1) / 2), max(1.0, (y1 - y0 + 1) / 2)
    for (x, y) in mask:
        u = (x + 0.5 - cx) / rx
        v = (y + 0.5 - cy) / ry
        t = 3
        if (u + 0.32) ** 2 + (v + 0.4) ** 2 < 0.40 + lift:
            t = 4
        d = (u + 0.45) ** 2 + (v + 0.3) ** 2
        if d > 1.1:
            t = 2
        if d > 1.45 and v > 0.35 and (x, y + 1) not in mask:
            t = 1
        name = fam + '_warm' if t >= 4 else fam + '_cool' if t <= 1 else fam
        f.put(x, y, name, t)
    if glint and len(mask) > 12:
        top = sorted(mask, key=lambda p: ((p[0] + 0.5 - cx) / rx + 0.5) ** 2 + ((p[1] + 0.5 - cy) / ry + 0.55) ** 2)
        for p in top[:2]:
            f.put(p[0], p[1], fam + '_warm', 5)


def darken(f, mask, by=1):
    for q in mask:
        if q in f.px:
            fam, t = f.px[q]
            f.px[q] = (fam, max(1, t - by))


def occlude(f, front, back):
    """A joint: back-part pixels just below or right of a front part go a tone darker."""
    front, back = set(front), set(back)
    for (x, y) in front:
        for dx, dy in ((0, 1), (1, 0)):
            q = (x + dx, y + dy)
            if q not in front and q in back and q in f.px:
                fam, t = f.px[q]
                if fam != 'ink':
                    f.px[q] = (fam, max(1, min(t, 2)))


def limb(f, mask, fam):
    """A stem or leg: lit left column, body, dark right column and last row."""
    mask = set(mask)
    for (x, y) in mask:
        t = 3
        if (x - 1, y) not in mask or (x, y - 1) not in mask:
            t = 4
        if (x + 1, y) not in mask:
            t = 2
        if (x, y + 1) not in mask and (x + 1, y) not in mask:
            t = 1
        f.put(x, y, fam + ('_warm' if t >= 4 else ''), t)


def concave(f, mask, fam):
    """The inside of an ear: the rim shades the upper left, light pools lower right."""
    mask = set(mask)
    if not mask:
        return
    x0, y0, x1, y1 = bbox(mask)
    cx, cy = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2
    for (x, y) in mask:
        n = (x + 0.5 - cx) + (y + 0.5 - cy)
        edge = (x - 1, y) not in mask or (x, y - 1) not in mask
        t = 2 if edge else 3
        f.put(x, y, fam + ('_cool' if t == 2 else ''), t)


def leaf(p, cx, cy, rx, ry, rot, fam='leaf', dy=0):
    """A small leaf: shaded as a ball, a midrib a tone down along the long axis."""
    m = p.ell(cx, cy, rx, ry, rot, dy=dy)
    ball(p.f, m, fam, glint=False)
    rr = -rot if p.flip else rot
    ccx = p.CX(cx)
    for k in range(-int(max(rx, ry)) + 1, int(max(rx, ry))):
        if rx >= ry:
            q = (int(ccx + k * math.cos(rr)), int(cy + dy + k * math.sin(rr)))
        else:
            q = (int(ccx - k * math.sin(rr)), int(cy + dy + k * math.cos(rr)))
        if q in m:
            _, t = p.f.px[q]
            p.f.px[q] = (fam + '_cool', max(1, t - 1))
    return m


def blade(p, base, tip, w=1.6, fam='grass', tone_shift=0, dy=0):
    """A grass blade: a tapered wedge from a base of width 2w to a point."""
    (bx, by), (tx, ty) = base, tip
    ang = math.atan2(ty - by, tx - bx)
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(bx + nx * w, by + ny * w), (tx, ty), (bx - nx * w, by - ny * w)]
    m = p.poly(pts, dy=dy) | p.ell(tx, ty, 0.6, 0.6, dy=dy)
    limb(p.f, m, fam)
    if tone_shift:
        darken(p.f, m, tone_shift)
    return m


def eye(p, x, y, w=3, h=4, state='open'):
    """Eyes in view coordinates (never mirrored): ink, a glint at the upper left, a small
    second catchlight lower right. Closed: a lid curve. Happy: an arch."""
    f = p.f
    if state == 'open':
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                f.put(xx, yy, 'ink', 0)
        f.put(x, y, 'plaster_warm', 5)
        p.keep.add((x, y))
        if w >= 3 and h >= 4:
            f.put(x + 1, y, 'plaster_warm', 5)
            p.keep.add((x + 1, y))
    elif state == 'closed':
        for xx in range(x - 1, x + w):
            f.put(xx, y + h - 1, 'ink', 0)
    elif state == 'happy':  # an arch: a two-pixel crown on two short legs
        f.put(x, y + 1, 'ink', 0); f.put(x + 1, y + 1, 'ink', 0)
        f.put(x - 1, y + 2, 'ink', 0); f.put(x - 1, y + 3, 'ink', 0)
        f.put(x + 2, y + 2, 'ink', 0); f.put(x + 2, y + 3, 'ink', 0)


def despeckle(fig, keep, passes=2):
    """A fill pixel unlike all four neighbours takes the colour most neighbours share;
    ties break deterministically. Ink and kept pixels (glints, the nose) stay."""
    for _ in range(passes):
        changes = {}
        for (x, y), v in sorted(fig.px.items()):
            if v[0] == 'ink' or (x, y) in keep or (x, y) in fig.fixed:
                continue
            nb = [fig.px.get((x + dx, y + dy)) for dx, dy in sk.N4]
            if sum(n is None for n in nb) > 2:
                continue
            pool = [n for n in nb if n is not None and n[0] != 'ink']
            if not pool or v in pool:
                continue
            changes[(x, y)] = max(sorted(set(pool), key=str), key=pool.count)
        if not changes:
            break
        fig.px.update(changes)


def settle(fig, keep):
    """After the outline: an interior fill pixel unlike all four neighbours (a crumb on a
    thin stem, a gap between parts) joins its neighbours, outline tones included."""
    for _ in range(3):
        changes = {}
        for (x, y), v in sorted(fig.px.items()):
            if v[0] == 'ink' or (x, y) in keep or (x, y) in fig.fixed:
                continue
            nb = [fig.px.get((x + dx, y + dy)) for dx, dy in sk.N4]
            if any(n is None for n in nb):
                continue
            pool = [n for n in nb if n[0] not in ('ink', 'glowflora')]
            if not pool or v in pool:
                continue
            same = [n for n in pool if n[0] not in ('_edge', '_lit')]
            changes[(x, y)] = max(sorted(set(same or pool), key=str), key=(same or pool).count)
        if not changes:
            break
        fig.px.update(changes)


def finish(p):
    despeckle(p.f, p.keep, passes=3)
    for (x, y) in p.glows:
        if all((x + dx, y + dy) in p.f.px for dx, dy in sk.N4):   # inside, never on the rim
            p.f.glow(x, y, 'glowflora', 4)
    p.f.outline()
    if getattr(p, 'thin_edges', False):   # blades and leaf tips are too thin for a lit break
        for q, v in list(p.f.px.items()):
            if v[0] == '_lit' and sk.family_of(v[1]) in ('grass', 'leaf'):
                p.f.px[q] = ('_edge', v[1])
    settle(p.f, p.keep)
    return p.f.image()


def nose(p, x, y, w=2):
    for k in range(w):
        p.put(x + k, y, 'clay', 3, keep=True)


def perch_core(p, fur, foot_fam, belly_fam='plaster'):
    """The perch body: a three-quarter sit turned toward the facing, so both eyes show at
    16 px. Returns (body, head)."""
    f = p.f
    body = p.ell(12, 18.8, 4.6, 3.4)
    ball(f, body, fur, glint=False)
    belly = p.ell(13, 19.8, 2.6, 2.2) & body
    ball(f, belly, belly_fam, glint=False)
    for m in (p.ell(10.2, 21.7, 1.7, 0.9), p.ell(14.6, 21.7, 1.7, 0.9)):
        ball(f, m, foot_fam, glint=False)
        darken(f, m, 1)
    head = p.ell(12.6, 13.0, 5.4, 4.5)
    return body, head


def perch_face(p, head_fam, rings=False):
    f = p.f
    mz = p.ell(13.6, 15.2, 2.3, 1.3)
    ball(f, mz, 'plaster', glint=False)
    exs = (10, 15)
    if rings:
        for ex in exs:
            for q in p.f.rect(p.EX(ex, 2) - 1, 10, p.EX(ex, 2) + 2, 14, knock=1):
                f.put(q[0], q[1], 'plaster' + ('_warm' if q[1] < 12 else ''), 4 if q[1] < 12 else 3)
    for ex in exs:
        eye(p, p.EX(ex, 2), 11, 2, 3)
    for x in (13, 14):
        p.put(x, 14, 'clay', 3, keep=True)


# =========================================================================================
# Option A: field mouse. Path fur, plaster muzzle and belly, big round ears lined with
# grass, a long grass stem tail that ends in a two-leaf sprig, a sprout on the crown.
# =========================================================================================
FUR_A = 'path'


def a_tail_S(p, dy=0, up=0):
    f = p.f
    m = p.stroke([(21.5, 26 + dy), (25, 25.5 + dy), (27, 22.5 + dy - up), (27.2, 18 + dy - up),
                  (26, 14.5 + dy - up)], r=0.95)
    limb(f, m, 'grass')
    leaf(p, 25.0, 12.0 + dy - up, 1.5, 2.8, -0.45, 'leaf')
    leaf(p, 28.0, 15.0 + dy - up, 2.2, 1.2, 0.55, 'grass')


def a_S(pose='idle'):
    p = P('S')
    f = p.f
    dy = -2 if pose == 'hop' else 0
    a_tail_S(p, dy=dy, up=3 if pose == 'hop' else 0)
    # feet: planted, or dangling below in the hop
    if pose == 'hop':
        legs = p.stroke([(12.5, 25 + dy), (12, 26.5)], r=1.1) | p.stroke([(19.5, 25 + dy), (20, 26.5)], r=1.1)
        ball(f, legs, FUR_A, glint=False)
        feet = [p.ell(11.8, 27.2, 2.0, 1.2), p.ell(20.2, 27.2, 2.0, 1.2)]
    else:
        feet = [p.ell(12.3, 27.5, 2.5, 1.4), p.ell(19.7, 27.5, 2.5, 1.4)]
    for m in feet:
        ball(f, m, 'plaster', glint=False)
        darken(f, m, 1)
    body = p.ell(16, 23 + dy, 6.6, 5.3 + (0.4 if pose == 'hop' else 0))
    ball(f, body, FUR_A)
    belly = p.ell(16, 24.4 + dy, 3.7, 3.4) & body
    ball(f, belly, 'plaster', glint=False)
    # chest tuft: belly fur combs up into the body in a little notch
    for (x, y) in ((15, 21 + dy), (16, 21 + dy), (16, 20 + dy)):
        f.put(x, y, 'plaster', 3)
    for m in feet:
        occlude(f, m, body)
    # forepaws held at the chest
    paws = p.ell(13.3, 22.2 + dy, 1.4, 1.2) | p.ell(18.7, 22.2 + dy, 1.4, 1.2)
    ball(f, paws, 'plaster', glint=False)
    occlude(f, paws, body | belly)
    # ears behind the head: big rounds, grass-lined
    ey_ = 8.4 + dy
    spread = 0.6 if pose == 'hop' else 0
    for cx, icx in ((8.6 - spread, 9.4 - spread), (23.4 + spread, 22.6 + spread)):
        ear = p.ell(cx, ey_, 4.3, 4.3, -0.3 if cx < 16 else 0.3) if pose == 'hop' else p.ell(cx, ey_, 4.3, 4.3)
        ball(f, ear, FUR_A, glint=cx < 16)
        concave(f, p.ell(icx, ey_ + 0.8, 2.5, 2.7), 'grass')
    head = p.ell(16, 14.6 + dy, 7.6, 6.4)
    cheeks = p.poly([(9.5, 14.5 + dy), (6.8, 18.6 + dy), (10.5, 18.5 + dy)]) | \
        p.poly([(22.5, 14.5 + dy), (25.2, 18.6 + dy), (21.5, 18.5 + dy)])
    ball(f, head | cheeks, FUR_A)
    occlude(f, head, body)
    # cheek fluff: a tuft a tone down at each jaw
    for (x, y, t) in ((8, 17, 3), (9, 18, 3), (23, 17, 2), (22, 18, 2)):
        f.put(x, y + dy, FUR_A, t)
    muzzle = p.ell(16, 18.2 + dy, 3.3, 2.2)
    ball(f, muzzle, 'plaster', glint=False)
    # crown sprout (the growth slot)
    sx = 16
    for y in (6, 7):
        p.put(sx, y + dy, 'grass', 3)
    for (x, y, fam, t) in ((13, 5, 'grass_warm', 4), (14, 5, 'grass_warm', 4), (15, 6, 'grass', 3),
                           (17, 5, 'grass', 2), (18, 5, 'grass', 2), (18, 4, 'grass', 3)):
        p.put(x, y + dy, fam, t)
    st = 'happy' if pose == 'hop' else 'open'
    eye(p, 11, 12 + dy, 3, 4, st)
    eye(p, 18, 12 + dy, 3, 4, st)
    nose(p, 15, 16 + dy)
    if pose == 'hop':
        f.put(15, 18 + dy, 'ink', 0); f.put(16, 18 + dy, 'ink', 0)
        f.put(15, 19 + dy, 'clay', 3); f.put(16, 19 + dy, 'clay', 2)
    else:
        f.put(15, 18 + dy, 'plaster_cool', 1); f.put(16, 18 + dy, 'plaster_cool', 1)
    return finish(p)


def a_side(view):
    p = P(view)
    f = p.f
    # tail: a long stem behind, rising, a leaf sprig at the tip
    m = p.stroke([(8, 24), (4.6, 23), (3, 19.5), (3.4, 15.5), (5.4, 12.6)], r=0.95)
    limb(f, m, 'grass')
    leaf(p, 6.8, 11.2, 2.7, 1.4, -0.55, 'leaf')
    leaf(p, 2.4, 14.2, 1.2, 2.0, 0.3, 'grass')
    # far ear and far feet (a tone down: in the body's shade)
    far_ear = p.ell(20.4, 6.4, 3.4, 3.6)
    ball(f, far_ear, FUR_A, glint=False)
    darken(f, far_ear, 1)
    for m in (p.ell(21.4, 27.6, 1.9, 1.2), p.ell(13.6, 27.6, 2.2, 1.2)):
        ball(f, m, 'plaster', glint=False)
        darken(f, m, 1)
    body = p.ell(14.6, 22.6, 7.2, 5.2)
    ball(f, body, FUR_A)
    belly = p.ell(17.4, 24.8, 4.0, 3.0) & body
    ball(f, belly, 'plaster', glint=False)
    haunch = p.ell(10.6, 23.8, 3.6, 3.7)
    ball(f, haunch, FUR_A, glint=False)
    occlude(f, haunch, body)
    hind = p.ell(11.6, 27.5, 3.1, 1.4)
    ball(f, hind, 'plaster', glint=False)
    occlude(f, hind, haunch)
    leg = p.stroke([(19.2, 24.5), (19.3, 26.5)], r=0.9)
    ball(f, leg, FUR_A, glint=False)
    fore = p.ell(19.8, 27.6, 2.0, 1.2)
    ball(f, fore, 'plaster', glint=False)
    paw = p.ell(21.2, 22.4, 1.4, 1.2)
    ball(f, paw, 'plaster', glint=False)
    occlude(f, paw, body | belly)
    head = p.ell(20, 14.4, 6.6, 6.0) | p.ell(25.0, 16.8, 3.4, 2.6)
    cheek = p.poly([(15, 16.5), (13.0, 20.2), (16.6, 19.6)])
    ball(f, head | cheek, FUR_A)
    occlude(f, head, body)
    muzzle = p.ell(25.6, 18.0, 2.7, 1.6) & head
    ball(f, muzzle, 'plaster', glint=False)
    if not p.flip:  # the muzzle faces east, away from the light
        darken(f, muzzle, 1)
    # near ear on top, grass-lined facing forward
    ear = p.ell(15.4, 7.2, 4.0, 4.2)
    ball(f, ear, FUR_A)
    concave(f, p.ell(16.4, 7.8, 2.2, 2.7), 'grass')
    occlude(f, ear, head)
    # crown sprout, front of the crown
    for (x, y, fam, t) in ((22, 8, 'grass', 3), (22, 7, 'grass', 3), (21, 6, 'grass_warm', 4), (20, 6, 'grass_warm', 4),
                           (23, 6, 'grass', 2), (24, 5, 'grass', 2), (23, 5, 'grass', 3)):
        p.put(x, y, fam, t)
    ex = 21 if not p.flip else 31 - 23
    eye(p, ex, 12, 3, 4)
    for (x, y, fam, t) in ((28, 16, 'clay', 3), (27, 16, 'clay', 3), (28, 15, 'clay', 3)):
        p.put(x, y, fam, t, keep=True)
    return finish(p)


def a_perch(view):
    p = P(view, PCELL)
    f = p.f
    m = p.stroke([(8, 20.5), (5, 20), (3.6, 17), (4.4, 14)], r=0.8)
    limb(f, m, 'grass')
    leaf(p, 5.4, 12.2, 2.0, 1.1, -0.6, 'leaf')
    for cx, cy, r in ((8.0, 8.8, 2.9), (17.0, 8.4, 2.6)):
        ear = p.ell(cx, cy, r, r)
        ball(f, ear, FUR_A, glint=False)
        concave(f, p.ell(cx + (0.6 if cx < 12 else -0.5), cy + 0.5, r - 1.3, r - 1.1), 'grass')
    body, head = perch_core(p, FUR_A, 'plaster')
    ball(f, head, FUR_A)
    occlude(f, head, body)
    for (x, y, fam, t) in ((12, 8, 'grass', 3), (12, 7, 'grass', 3), (10, 6, 'grass_warm', 4), (11, 6, 'grass_warm', 4),
                           (13, 6, 'grass', 2), (14, 6, 'grass', 2)):
        p.put(x, y, fam, t)
    perch_face(p, FUR_A)
    return finish(p)


def a_nap():
    p = P('S')
    f = p.f
    body = p.ell(17, 23.6, 9.4, 5.0)
    ball(f, body, FUR_A)
    # back fur: tufts combed along the curl, a tone down
    for (x, y) in ((18, 20), (19, 20), (22, 21), (23, 21), (14, 20)):
        if (x, y) in body:
            fam, t = f.px[(x, y)]
            f.put(x, y, FUR_A + '_cool', max(1, t - 1))
    ears = p.ell(8.0, 17.8, 2.8, 2.1, -0.3) | p.ell(14.2, 17.6, 2.6, 2.0, 0.3)
    ball(f, ears, FUR_A, glint=False)
    concave(f, p.ell(8.4, 18.0, 1.4, 1.0) | p.ell(13.8, 17.9, 1.4, 1.0), 'grass')
    head = p.ell(11.2, 22.2, 5.8, 4.8)
    ball(f, head, FUR_A)
    occlude(f, head, body)
    mz = p.ell(11.2, 24.6, 2.4, 1.5)
    ball(f, mz, 'plaster', glint=False)
    # the stem tail arcs up over the back, the leaf sprig laid by the ears like a blanket corner
    m = p.stroke([(25.8, 25.0), (26.4, 21.4), (24.0, 18.6), (19.4, 17.8)], r=0.9)
    limb(f, m, 'grass')
    leaf(p, 17.0, 17.4, 2.6, 1.3, 0.2, 'leaf')
    eye(p, 7, 21, 3, 2, 'closed')
    eye(p, 13, 21, 3, 2, 'closed')
    nose(p, 10, 23)
    return finish(p)


# =========================================================================================
# Option B: scruffy vole. Earth fur, a big grass-tuft crest with a forelock, small round
# ears tucked at the sides, scruffy cheek tufts, a short thick tail with a grass tassel.
# =========================================================================================
FUR_B = 'earth'


def b_crest(p, top, forward=False, dy=0):
    """The grass tuft: five blades fanning from the crown, back ones darker, a forelock."""
    cx = 16
    if forward:  # side view: blades sweep back (west in E), the forelock falls forward
        specs = [((19.5, top + 2), (12.0, top - 3.5), 1), ((20, top + 2), (14.0, top - 5.5), 1),
                 ((20.5, top + 2), (17.2, top - 6.5), 0), ((21, top + 2), (20.5, top - 5.0), 0),
                 ((21.5, top + 2.5), (24.8, top + 0.5), 1)]
    else:
        specs = [((cx - 1, top + 2), (cx - 6.5, top - 2.5), 1), ((cx + 1, top + 2), (cx + 6, top - 3.5), 1),
                 ((cx - 0.5, top + 2), (cx - 3.5, top - 5.5), 0), ((cx + 0.5, top + 2), (cx + 2.5, top - 6.0), 0),
                 ((cx, top + 2.5), (cx - 4.5, top + 2.8), 0)]
    m = set()
    for base, tip, back in specs:
        m |= blade(p, base, tip, 1.5, 'grass', tone_shift=back, dy=dy)
    return m


def b_S(pose='idle'):
    p = P('S')
    f = p.f
    dy = -2 if pose == 'hop' else 0
    # tail: a short thick stub to the right with a three-blade grass tassel
    up = 3 if pose == 'hop' else 0
    tail = p.stroke([(21.5, 26 + dy), (25, 24.6 + dy - up / 2)], r=1.4)
    ball(f, tail, FUR_B, glint=False)
    for tip in ((27.5, 20.5 + dy - up), (29.2, 23.2 + dy - up), (28.8, 26.0 + dy - up)):
        blade(p, (25.6, 24.4 + dy - up / 2), tip, 1.2, 'grass')
    if pose == 'hop':
        legs = p.stroke([(12, 25 + dy), (11.5, 26.5)], r=1.2) | p.stroke([(20, 25 + dy), (20.5, 26.5)], r=1.2)
        ball(f, legs, FUR_B, glint=False)
        feet = [p.ell(11.2, 27.3, 2.2, 1.2), p.ell(20.8, 27.3, 2.2, 1.2)]
    else:
        feet = [p.ell(11.6, 27.6, 2.6, 1.3), p.ell(20.4, 27.6, 2.6, 1.3)]
    for m in feet:
        ball(f, m, 'timber', glint=False)
    body = p.ell(16, 23.2 + dy, 7.7, 5.4)
    ball(f, body, FUR_B)
    belly = p.ell(16, 24.8 + dy, 4.3, 3.4) & body
    ball(f, belly, 'plaster', glint=False)
    for m in feet:
        occlude(f, m, body)
    # scruffy belly edge: two notches of fur into the cream
    for (x, y) in ((13, 22), (18, 22), (14, 22)):
        f.put(x, y + dy, FUR_B, 3)
    # small round ears at the sides of the head
    for cx in (9.0, 23.0):
        ear = p.ell(cx, 11.6 + dy - (1 if pose == 'hop' else 0), 3.0, 3.0)
        ball(f, ear, FUR_B, glint=False)
        concave(f, p.ell(cx + (0.6 if cx < 16 else -0.6), 12.2 + dy - (1 if pose == 'hop' else 0), 1.6, 1.7), 'grass')
    head = p.ell(16, 15.8 + dy, 7.0, 6.0)
    cheeks = p.poly([(10, 15 + dy), (6.2, 19.6 + dy), (8.6, 19.2 + dy), (7.8, 21 + dy), (11, 20 + dy)]) | \
        p.poly([(22, 15 + dy), (25.8, 19.6 + dy), (23.4, 19.2 + dy), (24.2, 21 + dy), (21, 20 + dy)])
    ball(f, head | cheeks, FUR_B)
    occlude(f, head, body)
    # cheek tufts as clumps: a lit clump on the west jaw, a shaded one east
    for (x, y, t) in ((8, 18, 4), (9, 18, 4), (8, 19, 3), (23, 18, 2), (22, 18, 2), (23, 19, 1)):
        f.put(x, y + dy, FUR_B + ('_warm' if t == 4 else ''), t)
    muzzle = p.ell(16, 18.8 + dy, 3.3, 2.1)
    ball(f, muzzle, 'plaster', glint=False)
    b_crest(p, 9 + dy)
    st = 'happy' if pose == 'hop' else 'open'
    eye(p, 11, 13 + dy, 3, 3, st) if st == 'happy' else eye(p, 11, 13 + dy, 3, 4, st)
    eye(p, 18, 13 + dy, 3, 3, st) if st == 'happy' else eye(p, 18, 13 + dy, 3, 4, st)
    nose(p, 15, 17 + dy)
    if pose == 'hop':
        f.put(15, 19 + dy, 'ink', 0); f.put(16, 19 + dy, 'ink', 0)
        f.put(15, 20 + dy, 'clay', 3); f.put(16, 20 + dy, 'clay', 2)
    else:
        f.put(15, 19 + dy, 'plaster_cool', 1); f.put(16, 19 + dy, 'plaster_cool', 1)
    return finish(p)


def b_side(view):
    p = P(view)
    f = p.f
    tail = p.stroke([(8, 24.6), (4.4, 23.6)], r=1.4)
    ball(f, tail, FUR_B, glint=False, lift=0.5)
    for tip in ((1.4, 20.2), (0.8, 23.4), (1.8, 26.4)):
        blade(p, (4.0, 23.6), tip, 1.2, 'grass')
    for m in (p.ell(21.6, 27.6, 2.0, 1.2), p.ell(13.6, 27.6, 2.2, 1.2)):
        ball(f, m, 'timber', glint=False)
        darken(f, m, 1)
    far_ear = p.ell(19.2, 10.6, 2.4, 2.4)
    ball(f, far_ear, FUR_B, glint=False)
    darken(f, far_ear, 1)
    body = p.ell(14.4, 22.8, 7.9, 5.4)
    ball(f, body, FUR_B)
    belly = p.ell(17.4, 25.0, 4.2, 3.0) & body
    ball(f, belly, 'plaster', glint=False)
    haunch = p.ell(10.4, 24.0, 3.8, 3.6)
    ball(f, haunch, FUR_B, glint=False)
    occlude(f, haunch, body)
    hind = p.ell(11.4, 27.6, 3.2, 1.3)
    ball(f, hind, 'timber', glint=False)
    fore = p.ell(20.0, 27.6, 2.1, 1.3)
    ball(f, fore, 'timber', glint=False)
    head = p.ell(20.4, 15.6, 6.4, 5.8) | p.ell(25.2, 17.6, 3.0, 2.4)
    cheek = p.poly([(15.2, 16.6), (12.2, 20.6), (14.2, 20.0), (13.8, 21.6), (16.8, 20.2)])
    ball(f, head | cheek, FUR_B)
    occlude(f, head, body)
    muzzle = p.ell(25.6, 18.8, 2.5, 1.5) & head
    ball(f, muzzle, 'plaster', glint=False)
    if not p.flip:  # the muzzle faces east, away from the light
        darken(f, muzzle, 1)
    ear = p.ell(16.4, 12.0, 2.8, 2.8)
    ball(f, ear, FUR_B, glint=False)
    concave(f, p.ell(17.0, 12.4, 1.5, 1.7), 'grass')
    occlude(f, ear, head)
    b_crest(p, 9, forward=True)
    ex = 21 if not p.flip else 31 - 23
    eye(p, ex, 13, 3, 4)
    for (x, y, fam, t) in ((28, 17, 'clay', 3), (27, 17, 'clay', 3), (28, 16, 'clay', 3)):
        p.put(x, y, fam, t, keep=True)
    return finish(p)


def b_perch(view):
    p = P(view, PCELL)
    f = p.f
    tail = p.stroke([(8, 20.4), (5.4, 19.6)], r=1.1)
    ball(f, tail, FUR_B, glint=False, lift=0.5)
    for tip in ((2.6, 16.8), (2.2, 19.8)):
        blade(p, (5.2, 19.4), tip, 1.0, 'grass')
    for cx in (7.8, 17.4):
        ear = p.ell(cx, 10.8, 1.9, 1.9)
        ball(f, ear, FUR_B, glint=False)
    body, head = perch_core(p, FUR_B, 'timber')
    cheeks = p.poly([(8.6, 13.5), (6.2, 16.4), (9.4, 16.2)]) | p.poly([(16.8, 13.5), (19.0, 16.2), (16.0, 16.4)])
    ball(f, head | cheeks, FUR_B)
    occlude(f, head, body)
    for base, tip, back in (((12, 9.4), (7.4, 5.6), 1), ((12.6, 9.4), (10.4, 4.6), 0),
                            ((13.2, 9.4), (14.4, 4.8), 0), ((13.8, 9.6), (17.4, 6.6), 1)):
        blade(p, base, tip, 1.2, 'grass', tone_shift=back)
    perch_face(p, FUR_B)
    return finish(p)


def b_nap():
    p = P('S')
    f = p.f
    tail = p.stroke([(25, 26.2), (27.4, 25.4)], r=1.3)
    ball(f, tail, FUR_B, glint=False)
    body = p.ell(17, 23.4, 9.6, 5.2)
    ball(f, body, FUR_B)
    for (x, y) in ((19, 20), (20, 20), (23, 21), (24, 21), (15, 20)):
        if (x, y) in body:
            fam, t = f.px[(x, y)]
            f.put(x, y, FUR_B + '_cool', max(1, t - 1))
    # the tassel tucked over the front like a blanket
    for tip in ((19.0, 27.4), (21.6, 28.2), (24.0, 27.8)):
        blade(p, (27.2, 25.6), tip, 1.2, 'grass', tone_shift=1)
    head = p.ell(11.0, 22.4, 6.0, 4.8)
    ball(f, head, FUR_B)
    occlude(f, head, body)
    ears = p.ell(6.4, 20.0, 1.9, 1.9) | p.ell(15.6, 19.6, 1.9, 1.9)
    ball(f, ears, FUR_B, glint=False)
    mz = p.ell(11.0, 24.8, 2.4, 1.5)
    ball(f, mz, 'plaster', glint=False)
    # crest flops over sideways in sleep
    for base, tip, back in (((10, 18.6), (4.4, 16.4), 1), ((11, 18.4), (7.0, 14.6), 0),
                            ((12, 18.4), (11.2, 14.0), 0), ((12.6, 18.6), (15.6, 15.6), 1)):
        blade(p, base, tip, 1.4, 'grass', tone_shift=back)
    eye(p, 7, 21, 3, 2, 'closed')
    eye(p, 13, 21, 3, 2, 'closed')
    nose(p, 10, 23)
    return finish(p)


# =========================================================================================
# Option C: hedge hare. Timber fur, plaster eye rings, muzzle and belly, tall round-tipped
# ears each with a leaf clipped at the base, long hind feet, a cotton puff tail.
# =========================================================================================
FUR_C = 'timber'


def c_ears_S(p, dy=0, hop=False):
    f = p.f
    lean = 0.34 if hop else 0.22
    for cx, rot in ((12.4, -lean), (19.6, lean)):
        ear = p.ell(cx + (-0.6 if hop and cx < 16 else 0.6 if hop else 0), 7.6 + dy + (1 if hop else 0), 2.5, 5.0, rot)
        ball(f, ear, FUR_C, glint=cx < 16)
        inner = p.ell(cx + (0.3 if cx < 16 else -0.3) + (-0.6 if hop and cx < 16 else 0.6 if hop else 0), 8.0 + dy + (1 if hop else 0), 1.1, 3.4, rot)
        concave(f, inner, 'plaster')
    # a leaf clipped at the outer base of each ear, pointing out and up
    leaf(p, 8.6, 10.0 + dy, 2.9, 1.3, -0.5, 'leaf')
    leaf(p, 23.4, 10.0 + dy, 2.9, 1.3, 0.5, 'leaf')


def c_S(pose='idle'):
    p = P('S')
    f = p.f
    dy = -2 if pose == 'hop' else 0
    puff = p.ell(22.6, 25.2 + dy, 2.0, 2.0)
    ball(f, puff, 'plaster', glint=False)
    if pose == 'hop':
        legs = p.stroke([(12.6, 25 + dy), (11.6, 26.4)], r=1.2) | p.stroke([(19.4, 25 + dy), (20.4, 26.4)], r=1.2)
        ball(f, legs, FUR_C, glint=False)
        feet = [p.ell(10.8, 27.4, 2.6, 1.2), p.ell(21.2, 27.4, 2.6, 1.2)]
    else:
        feet = [p.ell(11.8, 27.6, 3.0, 1.3), p.ell(20.2, 27.6, 3.0, 1.3)]
    for m in feet:
        ball(f, m, 'plaster', glint=False)
        darken(f, m, 1)
    body = p.ell(16, 23.4 + dy, 5.6, 5.0)
    ball(f, body, FUR_C)
    belly = p.ell(16, 24.2 + dy, 3.0, 3.6) & body
    ball(f, belly, 'plaster', glint=False)
    for m in feet:
        occlude(f, m, body)
    # front legs straight down in front of the belly
    if pose != 'hop':
        fl = p.stroke([(14.2, 22.6), (14.0, 26.6)], r=0.95) | p.stroke([(17.8, 22.6), (18.0, 26.6)], r=0.95)
        limb(f, fl, FUR_C)
    c_ears_S(p, dy, hop=pose == 'hop')
    head = p.ell(16, 15.8 + dy, 6.6, 5.6)
    cheeks = p.poly([(10.5, 15.5 + dy), (8.2, 19.2 + dy), (11.5, 19.4 + dy)]) | \
        p.poly([(21.5, 15.5 + dy), (23.8, 19.2 + dy), (20.5, 19.4 + dy)])
    ball(f, head | cheeks, FUR_C)
    occlude(f, head, body)
    # pale eye rings
    for x0 in (10, 17):
        ring = p.f.rect(x0, 12 + dy, x0 + 4, 17 + dy, knock=1)
        for q in ring:
            t = 4 if q[0] < 16 and q[1] < 14 + dy else 3 if q[0] < 16 else 2
            f.put(q[0], q[1], 'plaster' + ('_warm' if t == 4 else ''), t)
    muzzle = p.ell(16, 19.2 + dy, 2.7, 1.8)
    ball(f, muzzle, 'plaster', glint=False)
    st = 'happy' if pose == 'hop' else 'open'
    eye(p, 11, 13 + dy, 3, 4, st)
    eye(p, 18, 13 + dy, 3, 4, st)
    nose(p, 15, 18 + dy)
    if pose == 'hop':
        f.put(15, 20 + dy, 'ink', 0); f.put(16, 20 + dy, 'ink', 0)
    else:
        f.put(15, 19 + dy, 'plaster_cool', 1); f.put(16, 19 + dy, 'plaster_cool', 1)
    return finish(p)


def c_side(view):
    p = P(view)
    f = p.f
    far_ear = p.ell(17.6, 6.8, 2.1, 4.8, -0.35)
    ball(f, far_ear, FUR_C, glint=False)
    darken(f, far_ear, 1)
    for m in (p.ell(21.4, 27.6, 1.9, 1.2), p.ell(13.4, 27.6, 3.2, 1.2)):
        ball(f, m, 'plaster', glint=False)
        darken(f, m, 1)
    puff = p.ell(7.0, 22.4, 2.2, 2.2)
    ball(f, puff, 'plaster', glint=False)
    body = p.ell(14.2, 22.8, 6.6, 5.0, -0.25)
    ball(f, body, FUR_C)
    occlude(f, body, puff)
    belly = p.ell(17.0, 24.6, 3.6, 3.2) & body
    ball(f, belly, 'plaster', glint=False)
    haunch = p.ell(10.8, 24.0, 3.4, 3.8)
    ball(f, haunch, FUR_C, glint=False)
    occlude(f, haunch, body)
    hind = p.ell(12.0, 27.6, 4.2, 1.3)
    ball(f, hind, 'plaster', glint=False)
    fl = p.stroke([(19.2, 22.8), (19.4, 26.6)], r=0.95)
    limb(f, fl, FUR_C)
    fore = p.ell(20.0, 27.6, 1.9, 1.2)
    ball(f, fore, 'plaster', glint=False)
    head = p.ell(19.6, 15.0, 5.8, 5.2) | p.ell(24.0, 17.0, 2.8, 2.3)
    cheek = p.poly([(15.0, 16.4), (13.4, 19.8), (16.6, 19.6)])
    ball(f, head | cheek, FUR_C)
    occlude(f, head, body)
    muzzle = p.ell(24.4, 18.2, 2.2, 1.4) & head
    ball(f, muzzle, 'plaster', glint=False)
    if not p.flip:  # the muzzle faces east, away from the light
        darken(f, muzzle, 1)
    ear = p.ell(15.0, 7.0, 2.4, 5.0, -0.45)
    ball(f, ear, FUR_C)
    concave(f, p.ell(15.4, 7.4, 1.1, 3.4, -0.45), 'plaster')
    occlude(f, ear, head)
    leaf(p, 11.6, 10.4, 2.9, 1.3, 0.45, 'leaf')
    ex = 20 if not p.flip else 31 - 22
    for q in p.f.rect(ex - 1, 11, ex + 3, 16, knock=1):
        t = 4 if q[1] < 13 else 3
        f.put(q[0], q[1], 'plaster' + ('_warm' if t == 4 else ''), t)
    eye(p, ex, 12, 3, 4)
    for (x, y, fam, t) in ((26, 16, 'clay', 3), (25, 16, 'clay', 3), (26, 15, 'clay', 3)):
        p.put(x, y, fam, t, keep=True)
    return finish(p)


def c_perch(view):
    p = P(view, PCELL)
    f = p.f
    puff = p.ell(7.4, 19.8, 1.7, 1.7)
    ball(f, puff, 'plaster', glint=False)
    for cx, rot in ((10.2, -0.22), (15.0, 0.25)):
        ear = p.ell(cx, 7.0, 1.8, 3.5, rot)
        ball(f, ear, FUR_C, glint=cx < 12)
        concave(f, p.ell(cx + (0.2 if cx < 12 else -0.2), 7.6, 0.8, 2.4, rot), 'plaster')
    leaf(p, 7.4, 9.4, 2.2, 1.0, -0.5, 'leaf')
    leaf(p, 17.8, 9.2, 2.0, 1.0, 0.5, 'leaf')
    body, head = perch_core(p, FUR_C, 'plaster')
    ball(f, head, FUR_C)
    occlude(f, head, body)
    perch_face(p, FUR_C, rings=True)
    return finish(p)


def c_nap():
    p = P('S')
    f = p.f
    body = p.ell(17.4, 23.8, 9.0, 4.8)
    ball(f, body, FUR_C)
    puff = p.ell(25.4, 24.6, 2.0, 2.0)
    ball(f, puff, 'plaster', glint=False)
    for (x, y) in ((19, 20), (20, 20), (22, 21), (23, 21)):
        if (x, y) in body:
            fam, t = f.px[(x, y)]
            f.put(x, y, FUR_C + '_cool', max(1, t - 1))
    # ears laid flat along the back
    ears = p.ell(17.0, 19.6, 5.0, 1.6, 0.12) | p.ell(18.0, 21.0, 4.6, 1.4, 0.12)
    ball(f, ears, FUR_C, glint=False)
    darken(f, p.ell(18.0, 21.0, 4.6, 1.4, 0.12), 1)
    leaf(p, 22.6, 19.0, 2.4, 1.1, -0.3, 'leaf')
    head = p.ell(10.8, 22.6, 5.4, 4.6)
    ball(f, head, FUR_C)
    occlude(f, head, body)
    feet = p.ell(12.4, 27.6, 4.4, 1.2)
    ball(f, feet, 'plaster', glint=False)
    mz = p.ell(10.8, 25.0, 2.2, 1.4)
    ball(f, mz, 'plaster', glint=False)
    for x0 in (6, 11):
        for q in p.f.rect(x0, 20, x0 + 3, 23, knock=1):
            f.put(q[0], q[1], 'plaster', 3 if q[0] < 12 else 2)
    eye(p, 7, 20, 2, 3, 'closed')
    eye(p, 12, 20, 2, 3, 'closed')
    nose(p, 10, 24)
    return finish(p)


# --- sheet -------------------------------------------------------------------------------
VIEWS = ['S idle', 'E idle', 'W idle', 'S hop', 'S nap', 'E perch', 'W perch']


def views_for(S, side, perch, nap):
    return {'S idle': lambda: S('idle'), 'E idle': lambda: side('E'), 'W idle': lambda: side('W'),
            'S hop': lambda: S('hop'), 'S nap': nap, 'E perch': lambda: perch('E'), 'W perch': lambda: perch('W')}


OPTIONS = [
    dict(label='A', name='Field mouse: big round grass-lined ears, a long stem tail with a leaf sprig',
         fns=views_for(a_S, a_side, a_perch, a_nap),
         question='Ears and tail carry the Grassling: two big round ears lined with grass (round, never fox-pointed) '
                  'and a long thin grass stem for a tail that rises behind and ends in a two-leaf sprig.',
         palette=['path', 'plaster', 'grass', 'leaf', 'clay'],
         pose='Sits up, forepaws at the chest, ears wide: listening for where you go next.',
         fidget='Hop: springs up, ears flared, tail flicked high, a grin.',
         parts=[
             'tail stem + leaf sprig (grass, leaf; layer 0; behind in E/W, beside in S; sways, lags in hop, arcs over the back in nap; hip)',
             'far ear (path, grass lining; layer 1; E/W only, a tone down; head)',
             'far feet (plaster, a tone down; layer 2; walk alternates with the near feet; hip)',
             'body + belly (path, plaster; layer 3; breath 1 px, squash on land, stretch in the air; foot)',
             'haunch + near feet (path, plaster; layer 4; tuck in the hop, fold under in nap; hip)',
             'forepaws (plaster; layer 5; at the chest in idle, out for cheer and guard; chest)',
             'head + muzzle (path, plaster, clay nose; layer 6; rests on the paws in nap; chest)',
             'near ears (path, grass lining; layer 7; flare in the hop, fold flat in nap and hit; head)',
             'crown sprout (grass; layer 8; the growth slot for stages 2 and 3; head)',
             'perch: 16 px redraw, a three-quarter sit (both eyes show), stem tail curled up behind; the folk\'s shoulder'],
         notes=['Closest to today\'s Roamling (leaf ears, vine tail, sprout) moved onto path fur: tan reads off grass, green stays in lining and tail.',
                'Risk: the 2 px stem tail can thin out on grass at game scale (the leaf sprig carries it); big ears crowd the folk\'s head on the perch.',
                'Eastward eastward-04, Sam (about 18 art px) and John: one big shape (hair, pack), 2 px eyes, 3-4 tones. Ours: ears, 3x4 eyes, 4-5 tones.']),
    dict(label='B', name='Scruffy vole: a grass-tuft crest with a forelock, small round ears, a tasselled stub tail',
         fns=views_for(b_S, b_side, b_perch, b_nap),
         question='The grass grows on the head: a five-blade tuft fans up from the crown with a forelock over the brow, '
                  'ears are small rounds at the sides, cheeks scruffy, the tail a thick stub with a grass tassel.',
         palette=['earth', 'plaster', 'grass', 'timber', 'clay'],
         pose='Low and wide, feet planted, crest up: a scrappy rambler who has slept in every hedge.',
         fidget='Hop: crest swept back, tassel up, a toothy grin.',
         parts=[
             'tail stub + grass tassel (earth, grass; layer 0; tassel flicks in idle, trails in hop, tucks over the front in nap; hip)',
             'far ear + far feet (earth, timber; layer 1, a tone down; E/W only; head / hip)',
             'body + belly (earth, plaster; layer 2; breath 1 px, squash on land; foot)',
             'haunch + near feet (earth, timber; layer 3; walk tucks; hip)',
             'head + cheek tufts + muzzle (earth, plaster, clay nose; layer 4; chest)',
             'near ears (earth, grass lining; layer 5; perk on react, flat on hit; head)',
             'crest (grass, 5 blades, back two a tone down, forelock in front; layer 6; sways, sweeps back, flops in nap; growth slot; head)',
             'perch: 16 px redraw, three-quarter sit, a four-blade crest, the tassel out behind; the folk\'s shoulder'],
         notes=['The most distinct silhouette: a spiky crown no folk or familiar has; earth fur is darkest, far from Mossling green.',
                'Risk: earth fur sits near the timber feet and tree shade on grass; swaying blades need care in the rig so they never read as noise.',
                'Eastward eastward-04, Sam\'s hair and the spiky blue-haired stall keeper: a spiky top in 4-5 blades reads at game scale; strands would not.']),
    dict(label='C', name='Hedge hare: tall round-tipped ears with a leaf on each, pale eye rings, a cotton puff',
         fns=views_for(c_S, c_side, c_perch, c_nap),
         question='Tall ears, round at the tip (not pointed), each with a leaf clipped at its base like a hat feather; '
                  'a lean upright body on long hind feet, pale rings round big eyes, a plaster puff for a tail.',
         palette=['timber', 'plaster', 'leaf', 'clay'],
         pose='Upright and lean on long feet, ears high, leaves out: a scout already looking down the road.',
         fidget='Hop: a long spring, ears out, leaves flapping, a grin.',
         parts=[
             'puff tail (plaster; layer 0; bobs on every hop; hip)',
             'far ear (timber, plaster lining; layer 1, a tone down; E/W only; head)',
             'far feet (plaster, a tone down; layer 2; hip)',
             'body + belly (timber, plaster; layer 3; breath 1 px, stretches long in the hop; foot)',
             'haunch + long hind feet (timber, plaster; layer 4; the hop walk pushes off them; hip)',
             'front legs (timber; layer 5; straight down in idle, tucked in the air; chest)',
             'head + eye rings + muzzle (timber, plaster, clay nose; layer 6; chest)',
             'near ears (timber, plaster lining; layer 7; sweep back in the hop, lie along the back in nap; head)',
             'ear leaves (leaf; layer 8; one per ear base, flap a frame behind the ear; growth buds here; ear)',
             'perch: 16 px redraw, three-quarter sit, both ears and leaves up, eye rings kept; the folk\'s shoulder'],
         notes=['Leaves on the ears are two green flags at any distance; the eye rings give the clearest eyes of the three on dark fur.',
                'Risk: ears push it to about 26 art px and toward a rabbit, away from the RAT species; timber is the darkest fur at game scale.',
                'Eastward eastward-04 at Sam\'s height: faces rely on a light skin mask round 2 px eyes; the eye ring does that job on dark fur.']),
]


def gate(m):
    return (m['on_house'] >= 0.999 and m['west_east'] > 0 and m['isolated'] <= 0.04
            and m['colours'] <= 64 and m.get('outline_dark', 0) >= 0.95)


# =========================================================================================
# Final (revision round, 21 Oct): C made into a jerboa. A hopping desert rodent: big ROUND
# mouse ears lined with grass (from A), a three-blade grass crest on the crown as the
# head-top growth (from B, the family mark), long hind feet and the hop (C), path fur with a
# plaster belly and face, a thin 2 px tail that curls up and grows a two-leaf tuft.
# Family marks shared with the Mossling and Pebbling: one crown growth anchor, 3 x 3 ink
# eyes with a 2 px glint in the west column, a pale belly, feet filling row 27 (perch 21).
# =========================================================================================
FUR = 'path'


def eye3(p, x, y, state='open'):
    """The family eye in view coordinates: 3 x 3 ink, the glint the west column's top two
    rows. lid: the top row is fur (a calm half-lid). tight: a 3 x 2 squint. happy: an
    arch. closed: a lid line."""
    f = p.f
    if state in ('open', 'wide'):
        for yy in range(y, y + 3):
            for xx in range(x, x + 3):
                f.put(xx, yy, 'ink', 0)
        for yy in (y, y + 1):
            f.put(x, yy, 'plaster_warm', 5)
            p.keep.add((x, yy))
    elif state == 'tight':
        for yy in (y + 1, y + 2):
            for xx in range(x, x + 3):
                f.put(xx, yy, 'ink', 0)
        f.put(x, y + 1, 'plaster_warm', 5)
        f.put(x + 1, y + 1, 'plaster_warm', 5)
        p.keep |= {(x, y + 1), (x + 1, y + 1)}
    elif state == 'happy':
        f.put(x, y, 'ink', 0); f.put(x + 1, y, 'ink', 0); f.put(x + 2, y, 'ink', 0)
        f.put(x - 1, y + 1, 'ink', 0); f.put(x - 1, y + 2, 'ink', 0)
        f.put(x + 3, y + 1, 'ink', 0); f.put(x + 3, y + 2, 'ink', 0)
    elif state == 'closed':
        for xx in range(x - 1, x + 3):
            f.put(xx, y + 2, 'ink', 0)


def grown_leaf(p, base, tip, w, fam='leaf', dy=0):
    """A leaf grown from a stem: the blade swells from the stem end to a round point, and
    the stem runs on into it as the midrib (a tone down), so it reads attached."""
    (bx, by), (tx, ty) = base, tip
    by, ty = by + dy, ty + dy
    ang = math.atan2(ty - by, tx - bx)
    nx, ny = -math.sin(ang), math.cos(ang)
    mx, my = bx + (tx - bx) * 0.45, by + (ty - by) * 0.45
    pts = [(bx, by), (mx + nx * w, my + ny * w), (tx, ty), (mx - nx * w, my - ny * w)]
    m = p.poly(pts) | p.ell(tx, ty, 0.6, 0.6) | p.ell(mx, my, w * 0.8, w * 0.8)
    ball(p.f, m, fam, glint=False, lift=0.2)
    n = int(max(abs(tx - bx), abs(ty - by)) * 2)
    for i in range(1, n):
        q = (int(p.CX(bx + (tx - bx) * i / n) - (0.5 if p.flip else 0)), int(by + (ty - by) * i / n))
        if q in m and i < n - 1:
            _, t = p.f.px[q]
            p.f.px[q] = (fam + '_cool', max(1, min(t, 2)))
    return m


def crest(p, cx, cy, h=4.0, lean=0.0, glow=False, scale=1.0):
    """Three grass blades grown from the crown joint (cx, cy): the middle one tallest, the
    back one a tone down; a fur tuft covers the roots. Returns the growth anchor."""
    out = set()
    s = scale
    specs = [((cx - 0.8 * s, cy), (cx - 3.0 * s + lean, cy - h * 0.78), 1),
             ((cx + 0.8 * s, cy), (cx + 3.0 * s + lean, cy - h * 0.72), 0),
             ((cx, cy), (cx + 0.2 + lean * 1.2, cy - h), 0)]
    tips = []
    for base, tip, back in specs:
        out |= blade(p, base, tip, 1.35 * s, 'grass', tone_shift=back)
        tips.append(tip)
    if glow:
        for tx, ty in tips:
            x, y = int(p.CX(tx) - (0.5 if p.flip else 0)), int(ty)
            p.glows.append((x, y))
    return out


def tail_curl(p, pts, leaves, r=0.95, dy=0, glow=False, lift=0.4):
    """The thin tail: a 2 px stem shaded as a limb, a node at the tip, two grown leaves."""
    pts = [(x, y + dy) for x, y in pts]
    m = p.stroke(pts, r=r)
    ball(p.f, m, FUR, glint=False, lift=lift)
    tip = pts[-1]
    for (tx, ty, w) in leaves:
        lm = grown_leaf(p, tip, (tx, ty + dy), w, 'grass')
        if glow:
            x, y = int(p.CX(tx) - (0.5 if p.flip else 0)), int(ty + dy)
            for q in ((x, y), (x, y + 1)):
                if q in lm:
                    p.glows.append(q)
    return m


def fur_hooks(p, mask, spots):
    """Directional fur: 3 px hooks a tone down that comb along the form (dx = -1 / +1)."""
    f = p.f
    for (x, y, d) in spots:
        x = p.X(x)
        d = -d if p.flip else d
        pts = [(x, y), (x + d, y), (x + d, y + 1)]
        if all(q in mask and q in f.px and f.px[q][0].startswith(FUR) for q in pts):
            t = f.px[(x, y)][1]
            if t >= 4:
                c = (FUR + '_warm', 4)
            else:
                c = (FUR + '_cool' if t <= 2 else FUR, max(1, t - 1))
            for q in pts:
                f.put(q[0], q[1], *c)


# --- world: S ------------------------------------------------------------------------------
S_POSES = {
    #          lift squash feet     ears    eyes     mouth  paws    tail   crest
    'idle':  dict(dy=0, sq=0.0, feet='stand', ears='up', eyes='open', mouth=False, paws='chest', tail=0, lean=0.0),
    'hop 1': dict(dy=1, sq=0.7, feet='splay', ears='back', eyes='open', mouth=False, paws='chest', tail=-1, lean=0.0),
    'hop 2': dict(dy=-1, sq=-0.5, feet='push', ears='up', eyes='open', mouth=False, paws='chest', tail=1, lean=-0.6),
    'hop 3': dict(dy=-2, sq=-0.3, feet='dangle', ears='flare', eyes='happy', mouth=True, paws='chest', tail=2, lean=-0.9),
    'hop 4': dict(dy=1, sq=0.9, feet='splay', ears='back', eyes='tight', mouth=False, paws='chest', tail=-1, lean=0.6),
    'react': dict(dy=-1, sq=-0.4, feet='stand', ears='flare', eyes='wide', mouth=True, paws='up', tail=2, lean=0.0),
}


def j_S(pose='idle'):
    p = P('S')
    p.thin_edges = True
    f = p.f
    k = S_POSES[pose]
    dy, sq = k['dy'], k['sq']
    up = k['tail']
    # tail: out to the east, curling up; two leaves grow from the tip
    tail_curl(p, [(20.5, 25.4), (23.6, 25.6 - up * 0.3), (26.0, 23.8 - up * 0.6), (26.6, 21.0 - up),
                  (25.6, 18.6 - up)], [(23.4, 14.8 - up, 1.5), (28.0, 15.8 - up, 1.4)], dy=dy if dy < 0 else 0)
    # long hind feet seen from the front, and the haunches above them
    fx = {'stand': (12.2, 19.8), 'splay': (11.2, 20.8), 'push': (12.6, 19.4), 'dangle': (13.2, 18.8)}[k['feet']]
    fy = {'stand': 26.5, 'splay': 26.6, 'push': 26.2, 'dangle': 25.0}[k['feet']]
    feet = [p.ell(fx[0], fy, 2.2, 1.5), p.ell(fx[1], fy, 2.2, 1.5)]
    for m in feet:
        ball(f, m, 'plaster', glint=False)
        darken(f, m, 1)
    body_cy = 22.4 + dy + sq * 0.6
    haunch = p.ell(11.8, 23.6 + dy + sq * 0.5, 2.8 + sq * 0.3, 3.1 - sq * 0.3) | \
        p.ell(20.2, 23.6 + dy + sq * 0.5, 2.8 + sq * 0.3, 3.1 - sq * 0.3)
    ball(f, haunch, FUR, glint=False)
    if k['feet'] in ('push', 'dangle'):
        shin = p.stroke([(12.2, 25.0 + dy), (fx[0], fy - 0.6)], r=1.1) | p.stroke([(19.8, 25.0 + dy), (fx[1], fy - 0.6)], r=1.1)
        ball(f, shin, FUR, glint=False)
    body = p.ell(16, body_cy, 5.2 + sq * 0.6, 4.8 - sq)
    ball(f, body, FUR)
    occlude(f, body, haunch)
    belly = p.ell(16, body_cy + 1.0, 3.0 + sq * 0.4, 3.3 - sq * 0.6) & body
    ball(f, belly, 'plaster', glint=False)
    for m in feet:
        occlude(f, m, haunch | body)
    fur_hooks(p, body, [(12, int(body_cy) - 2, -1), (19, int(body_cy) - 2, 1)])
    # forepaws: held at the chest, or flung up in react
    if k['paws'] == 'up':
        paws = p.ell(10.0, 17.0 + dy, 1.3, 1.3) | p.ell(22.0, 17.0 + dy, 1.3, 1.3)
    else:
        paws = p.ell(14.2, 20.6 + dy + sq * 0.5, 1.3, 1.1) | p.ell(17.8, 20.6 + dy + sq * 0.5, 1.3, 1.1)
    # ears: big rounds behind the head, lined with grass
    ex = {'up': (9.2, 22.8, 8.8), 'back': (9.8, 22.2, 9.8), 'flare': (8.4, 23.6, 8.2)}[k['ears']]
    for cx in (ex[0], ex[1]):
        ear = p.ell(cx, ex[2] + dy, 3.8, 3.8 if k['ears'] != 'back' else 3.3)
        ball(f, ear, FUR, glint=cx < 16)
        concave(f, p.ell(cx + (0.6 if cx < 16 else -0.6), ex[2] + dy + 0.6, 2.3, 2.3 if k['ears'] != 'back' else 1.9), 'grass')
    head = p.ell(16, 14.4 + dy + sq * 0.4, 6.8 + sq * 0.3, 5.8 - sq * 0.2)
    cheeks = p.poly([(10.4, 14.8 + dy), (8.0, 18.2 + dy), (11.2, 18.6 + dy)]) | \
        p.poly([(21.6, 14.8 + dy), (24.0, 18.2 + dy), (20.8, 18.6 + dy)])
    ball(f, head | cheeks, FUR)
    occlude(f, head, body)
    fur_hooks(p, head | cheeks, [(9, 16 + dy, -1), (22, 16 + dy, 1)])
    ball(f, paws, 'plaster', glint=False)
    occlude(f, paws, body | belly | head)
    mz = p.ell(16, 17.6 + dy + sq * 0.4, 3.0, 2.0)
    ball(f, mz, 'plaster', glint=False)
    ga = (16.0, 9.0 + dy + sq * 0.4)
    crest(p, ga[0], ga[1], h=5.2 - sq, lean=k['lean'])
    # crown tuft over the roots of the crest
    for (x, y, t) in ((15, int(ga[1]) + 1, 4), (16, int(ga[1]) + 1, 4)):
        f.put(x, y, FUR + ('_warm' if t == 4 else ''), t)
    ey = 13 + dy + (1 if sq > 0.5 else 0)
    eye3(p, 11, ey, k['eyes'])
    eye3(p, 18, ey, k['eyes'])
    ny = 16 + dy + (1 if sq > 0.5 else 0)
    for x in (15, 16):
        p.put(x, ny, 'clay', 3, keep=True)
    if k['mouth']:
        f.put(15, ny + 2, 'ink', 0); f.put(16, ny + 2, 'ink', 0)
        f.put(15, ny + 3, 'clay', 3); f.put(16, ny + 3, 'clay', 3)
    else:
        f.put(15, ny + 2, 'plaster_cool', 1); f.put(16, ny + 2, 'plaster_cool', 1)
    return finish(p), (int(ga[0]), int(round(ga[1])))


# --- world: E / W ---------------------------------------------------------------------------
def j_side(view):
    p = P(view)
    p.thin_edges = True
    f = p.f
    tail_curl(p, [(9.6, 24.6), (7.0, 25.4), (5.2, 23.8), (4.9, 20.8), (6.0, 18.0)],
              [(4.0, 14.0, 1.5), (8.8, 14.8, 1.4)])
    far_ear = p.ell(19.4, 7.8, 3.0, 3.3)
    ball(f, far_ear, FUR, glint=False)
    darken(f, far_ear, 1)
    far_foot = p.ell(16.2, 26.6, 3.4, 1.2)
    ball(f, far_foot, 'plaster', glint=False)
    darken(f, far_foot, 1)
    body = p.ell(14.4, 21.8, 5.2, 4.8, -0.35)
    ball(f, body, FUR)
    belly = p.ell(16.8, 23.0, 2.8, 3.4) & body
    ball(f, belly, 'plaster', glint=False)
    haunch = p.ell(12.0, 23.2, 3.4, 3.8)
    ball(f, haunch, FUR, glint=False)
    occlude(f, haunch, body)
    fur_hooks(p, haunch, [(10, 21, -1), (12, 24, 1)])
    foot = p.ell(14.0, 26.6, 4.6, 1.3)
    ball(f, foot, 'plaster', glint=False)
    occlude(f, foot, haunch)
    head = p.ell(19.6, 13.8, 6.0, 5.4) | p.ell(24.4, 16.0, 2.8, 2.1)
    cheek = p.poly([(15.0, 15.4), (13.4, 19.0), (17.0, 18.8)])
    ball(f, head | cheek, FUR)
    occlude(f, head, body)
    fur_hooks(p, head | cheek, [(14, 17, -1)])
    # the face step: a brow over the eye, a crease where the snout leaves the cheek
    for (x, y, fam, t) in ((21, 10, FUR + '_warm', 4), (22, 10, FUR + '_warm', 4), (23, 10, FUR, 3),
                           (22, 16, FUR, 2), (22, 17, FUR, 2)):
        p.put(x, y, fam, t)
    mz = p.ell(24.8, 17.4, 2.4, 1.2) & head
    ball(f, mz, 'plaster', glint=False)
    if not p.flip:
        darken(f, mz, 1)
    paw = p.ell(20.0, 21.0, 1.3, 1.2)
    ball(f, paw, 'plaster', glint=False)
    occlude(f, paw, body | belly)
    ear = p.ell(15.8, 7.8, 3.6, 3.8)
    ball(f, ear, FUR)
    concave(f, p.ell(16.6, 8.2, 2.2, 2.6), 'grass')
    occlude(f, ear, head)
    ga = (20.0, 8.8)
    crest(p, ga[0], ga[1], h=5.0, lean=-0.8)
    for (x, y, t) in ((19, 9, 4), (20, 9, 4)):
        p.put(x, y, FUR + ('_warm' if t == 4 else ''), t)
    eye3(p, p.EX(21, 3), 12, 'open')
    for (x, y) in ((26, 15), (27, 15)):
        p.put(x, y, 'clay', 3, keep=True)
    p.put(24, 18, 'plaster_cool', 1)
    p.put(25, 18, 'plaster_cool', 1)
    return finish(p), (int(p.CX(ga[0]) - (1 if p.flip else 0)), int(ga[1]))


def j_nap():
    p = P('S')
    p.thin_edges = True
    f = p.f
    body = p.ell(17.0, 23.2, 8.8, 4.6)
    ball(f, body, FUR)
    fur_hooks(p, body, [(19, 20, 1), (23, 21, 1), (15, 20, -1)])
    foot = p.ell(20.6, 26.6, 4.0, 1.2)
    ball(f, foot, 'plaster', glint=False)
    darken(f, foot, 1)
    # the tail wraps the front from the east; its leaf tuft lies by the chin
    tail_curl(p, [(25.0, 25.6), (22.0, 27.0), (16.0, 27.2), (10.4, 26.8)], [(7.2, 25.4, 1.1), (8.6, 24.0, 1.0)])
    ears = p.ell(7.6, 18.8, 2.8, 2.0, -0.35) | p.ell(14.4, 18.4, 2.8, 2.0, 0.35)
    ball(f, ears, FUR, glint=False)
    concave(f, p.ell(8.0, 19.0, 1.5, 1.0, -0.35) | p.ell(14.0, 18.7, 1.5, 1.0, 0.35), 'grass')
    head = p.ell(11.2, 21.8, 5.6, 4.6)
    ball(f, head, FUR)
    occlude(f, head, body)
    mz = p.ell(11.2, 24.2, 2.4, 1.4)
    ball(f, mz, 'plaster', glint=False)
    ga = (11.0, 17.6)
    crest(p, ga[0], ga[1], h=3.2, lean=2.4)   # flopped sideways in sleep
    eye3(p, 8, 19, 'closed')
    eye3(p, 13, 19, 'closed')
    for x in (10, 11):
        p.put(x, 23, 'clay', 3, keep=True)
    return finish(p), (int(ga[0]), int(ga[1]))


# --- perch: 16 px, profile turned to the foe --------------------------------------------------
PERCH_POSES = {
    'perch':   dict(dy=0, sq=0.0, ears='up', eyes='open', mouth=False, paw='chest', tail=0, lean=-0.4, glow=False),
    'cling':   dict(dy=2, sq=0.8, ears='flat', eyes='tight', mouth=False, paw='grip', tail=1, lean=-1.4, glow=False),
    'cheer':   dict(dy=0, sq=-0.2, ears='up', eyes='happy', mouth=True, paw='up', tail=2, lean=0.4, glow=False),
    'special': dict(dy=0, sq=-0.3, ears='up', eyes='happy', mouth=False, paw='chest', tail=1, lean=0.0, glow=True),
}


def j_perch(view, pose='perch'):
    """The shoulder perch, a true 16 px redraw in profile turned to the foe: one big round
    ear behind the head, the crest at the front of the crown, the tail curled low behind
    with its two leaves, the long foot on the foot line (row 21)."""
    p = P(view, PCELL)
    p.thin_edges = True
    f = p.f
    k = PERCH_POSES[pose]
    dy, sq, up = k['dy'], k['sq'], k['tail']
    cling = pose == 'cling'
    hx = 1 if cling else 0
    tail_curl(p, [(7.6, 19.8), (5.4, 20.2), (4.2, 18.4), (4.6, 16.2 - up * 0.6)],
              [(3.4, 13.2 - up, 1.1), (6.6, 13.6 - up, 1.0)], r=0.8, glow=k['glow'], lift=0.9)
    body = p.ell(11.6, 18.4 + dy * 0.4, 4.0 + sq * 0.8, 3.4 - sq * 0.8)
    ball(f, body, FUR)
    belly = p.ell(13.2, 19.2 + dy * 0.4, 2.2, 2.2 - sq * 0.6) & body
    ball(f, belly, 'plaster', glint=False)
    foot = p.ell(13.8, 21.0, 3.2, 0.9)
    ball(f, foot, 'plaster', glint=False)
    occlude(f, foot, body)
    if not p.flip:   # belly and foot face the foe (east), away from the light
        darken(f, belly | foot, 1)
    head = p.ell(13.0 + hx, 12.4 + dy, 4.6, 4.0) | p.ell(17.0 + hx, 13.6 + dy, 2.0, 1.5)
    if k['ears'] == 'flat':
        # clinging: the ear lies flat back along the crown, its furred back up, over the head
        ball(f, head, FUR)
        occlude(f, head, body)
        ear = p.ell(10.4 + hx, 10.6 + dy, 3.4, 1.4, -0.12)
        ball(f, ear, FUR, glint=True)
        occlude(f, ear, head)
        if not p.flip:
            darken(f, belly | foot | p.ell(17.6, 20.2, 1.3, 1.0), 1)
    else:
        ear = p.ell(9.6, 8.8 + dy, 2.7, 2.7)
        ball(f, ear, FUR, glint=True)
        concave(f, p.ell(10.2, 9.2 + dy, 1.6, 1.6), 'grass')
        ball(f, head, FUR)
        occlude(f, head, body)
        occlude(f, head, ear)
    mz = p.ell(17.4 + hx, 14.4 + dy, 1.5, 0.8) & head
    ball(f, mz, 'plaster', glint=False)
    if not p.flip:
        darken(f, mz, 2 if cling else 1)   # clinging, the snout tucks down into its own shade
    ga = (14.2 + hx, 8.8 + dy)
    crest(p, ga[0], ga[1], h=3.0, lean=k['lean'] - 0.6, glow=k['glow'], scale=0.8)
    for (x, y, fam, t) in ((14, 10, FUR + '_warm', 4), (15, 10, FUR + '_warm', 4)):
        p.put(x + hx, y + dy, fam, t)
    if k['paw'] == 'up':
        paw = p.ell(18.0, 10.0, 1.2, 1.2)
    elif k['paw'] == 'grip':
        paw = p.ell(17.6, 20.2, 1.3, 1.0)
    else:
        paw = p.ell(15.6, 17.8 + dy * 0.4, 1.1, 1.0)
    ball(f, paw, 'plaster', glint=False)
    if not p.flip:
        darken(f, paw, 2 if cling else 1)
        if cling:   # pressed into the folk's shoulder: the foot sits in the paw's shadow
            darken(f, foot, 1)
    if k['glow']:   # SECOND WIND: a breath of light in the chest (inside the silhouette, finite)
        for q in ((11, 17), (12, 17), (11, 18), (12, 18)):
            p.glows.append((p.X(q[0]), q[1]))
    eye3(p, p.EX(14 + hx, 3), 11 + dy, k['eyes'])
    p.put(19 + hx, 13 + dy, 'clay', 3, keep=True)
    p.put(19 + hx, 12 + dy, 'clay', 3, keep=True)
    if k['mouth']:
        p.put(17 + hx, 15 + dy, 'ink', 0)
        p.put(16 + hx, 15 + dy, 'ink', 0)
    return finish(p), (int(p.CX(ga[0]) - (1 if p.flip else 0)), int(ga[1]))


FINAL_VIEWS = (
    [('S idle', lambda: j_S('idle')), ('E idle', lambda: j_side('E')), ('W idle', lambda: j_side('W'))]
    + [(f'hop {i}', (lambda i=i: j_S(f'hop {i}'))) for i in (1, 2, 3, 4)]
    + [('S react', lambda: j_S('react')), ('S nap', j_nap)]
    + [(f'{v} {s}', (lambda v=v, s=s: j_perch(v, s))) for v in ('E', 'W') for s in ('perch', 'cling', 'cheer', 'special')]
)

FINAL = dict(
    chosen='C',
    name='Jerboa rambler: round grass-lined ears, a three-blade crest, long feet, a curling leaf tail (final)',
    grafts=[
        'Coordinator: C made into a jerboa (a hopping desert rodent, RAT species): C\'s long hind feet and the hop kept; '
        'the tall rabbit ears replaced by big ROUND mouse ears.',
        'From A: grass-lined inner ears (green that belongs to the creature).',
        'From B: a small three-blade grass crest on the crown: the head-top growth, the family mark.',
        'Fixes: the clipped ear leaves are gone; the leaves now grow from the tail tip (stem runs on as the midrib); '
        'path fur with a plaster belly and face; family eyes 3 x 3 ink with a 2 px glint; 24 px idle, 16 px perch.',
    ],
    parts=[
        'tail (path, a 2 px stem; layer 0; anchor hip; curls up behind in E/W, out east and up in S, wraps the front in nap; '
        'one painted curve per state, never past x 2 / x 29)',
        'tail leaf tuft (grass, two leaves grown from the tip, the stem runs on as the midrib; child of the tail tip; lags a frame on the hop)',
        'far ear + far foot (path / plaster, a tone down; layer 1; E/W only; anchor head / foot)',
        'body + pale belly (path, plaster; layer 2; anchor hip; squash on crouch and land, stretch on rise; breath 1 px)',
        'haunches + long hind feet (path, plaster; layer 3; anchor foot; the family foot line: feet fill row 27, perch row 21; '
        'splay (crouch, land), push (rise), dangle (air))',
        'head + cheek tufts + face step (path; brow, cheek, snout in E/W; layer 4; anchor chest)',
        'face block (eyes 3 x 3 ink, glint 2 px in the west column: open / wide / happy / tight / closed; '
        'plaster muzzle, clay nose; layer 5; anchor head; S/E/W)',
        'ears (path, grass lining; layer 6; anchor head; up, back (crouch/land), flare (air/react), folded (nap), flat (cling))',
        'forepaws (plaster; layer 7; anchor chest; at the chest, flung up in react and cheer, gripping in cling)',
        'head-top growth: the three-blade crest (grass, back blade a tone down; layer 8; growthAnchor the crown joint; '
        'leans against the motion, flops in nap, stands tall in special)',
        'special effect (SECOND WIND): a 2 x 2 glowflora breath in the chest, inside the silhouette; finite, none under reduced motion',
    ],
    palette=['path', 'plaster', 'grass', 'clay'],
    glow='glowflora (the SECOND WIND breath only)',
    pose='A step behind and already up on its toes: big ears turning, tail curled like a question, ready to bound after you.',
    notes=[
        'Walk: the spec\'s 4-frame hop (crouch, rise, air, land), long feet push and dangle; ears and crest lag the motion.',
        'Growth stages (rig variants of the same poses): 1 three short blades; 2 longer blades and a third leaf on the tail tip; '
        '3 a seed head on the middle blade. The crown joint never moves.',
        'Perch: a 16 px redraw in profile, turned to the foe; the ears shrink and the crest is 3 px so it clears small folk; '
        'perchAnchor is the foot line centre (12, 22).',
        'Kept apart: round ears and a thin leafy tail (not Bramble\'s pointed ears or brush); path fur, not Mossling green.',
        'Compared with Eastward-04 at the same height (Sam about 18 art px, John, the market cats): one big shape '
        '(ears here, hair there), a glinting eye block, 3 to 4 tones a material, per-material outline.',
    ],
)

OUT_FINAL = os.path.join(REPO, 'docs/vision/characters/designs/roamling-final.png')


def final():
    views, nums, anchors, eyes = [], {}, {}, {}
    ok_all = True
    for cap, fn in FINAL_VIEWS:
        im, ga = fn()
        views.append((cap, im))
        anchors[cap] = list(ga)
        im.save(os.path.join(SCRATCH, f"final-{cap.replace(' ', '-')}.png"))
        m = sk.measure(im)
        nums[cap] = {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}
        a = im.getchannel('A').getbbox()
        nums[cap]['bbox'] = list(a)
        nums[cap]['height_px'] = a[3] - a[1] - 2   # without the outline rows
        ok = gate(m)
        ok_all &= ok
        print(f"final {cap:10s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:3d}  "
              f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  h {a[3] - a[1] - 2:2d}  "
              f"x {a[0]}-{a[2]}  {'ok' if ok else 'MISS'}")
    opt = dict(label='C', name='final: ' + FINAL['name'], views=views, parts=FINAL['parts'], palette=FINAL['palette'],
               pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Roamling final: C as a jerboa, with A\'s grass ears and B\'s crest', [opt], OUT_FINAL,
                    note='About 24 art px, cell 32 x 32, foot (16, 28). Idles, the 4-frame hop, react, nap; '
                         'perch states at 16 px in 24 x 24, foot (12, 22). Claude J, 21 Oct.')
    block = dict(FINAL)
    block.update(
        growthAnchor=anchors,
        eyeBlocks={'size': [3, 3], 'glint': '2 px, the west column, top two rows (plaster 5)'},
        footLine={'world': [16, 27], 'perch': [12, 21],
                  'note': 'feet fill the row above the anchor; the outline lands on the anchor row'},
        perchAnchor={cap: list(PFOOT) for cap, _ in FINAL_VIEWS if cap[0] in 'EW' and 'idle' not in cap},
        measure=nums,
        eastward_compared=['eastward-04: Sam, John and the market cats, at the familiar\'s height'])
    return block, ok_all


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    opts = []
    data = {'id': 'roamling', 'kind': 'familiar', 'cell': [CELL, CELL], 'foot': list(FOOT), 'height_art_px': 24,
            'perch_cell': [PCELL, PCELL], 'perch_foot': list(PFOOT), 'perch_height_art_px': 16,
            'question': 'The small roaming critter\'s ears, tail and grassy features.',
            'options': []}
    ok_all = True
    for o in OPTIONS:
        views = []
        nums = {}
        for cap in VIEWS:
            im = o['fns'][cap]()
            views.append((cap, im))
            im.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(im)
            nums[cap] = {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}
            ok = gate(m)
            ok_all &= ok
            print(f"{o['label']} {cap:8s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:3d}  "
                  f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  {'ok' if ok else 'MISS'}")
        opts.append(dict(label=o['label'], name=o['name'], views=views, parts=o['parts'], palette=o['palette'],
                         pose=o['pose'] + ' Fidget: ' + o['fidget'], notes=o['notes']))
        data['options'].append(dict(label=o['label'], name=o['name'], question_answered=o['question'],
                                    parts=o['parts'], palette=o['palette'], pose=o['pose'], fidget=o['fidget'],
                                    notes=o['notes'], numbers=nums))
    sk.design_sheet('Roamling: ears, tail and grassy features of the ROAM familiar', opts, OUT_PNG,
                    note='ROAM Grassling (RAT), 24 art px in a 32 x 32 cell, foot (16, 28); perch 16 px in 24 x 24, '
                         'foot (12, 22). Claude J design options, 21 Oct.')
    block, ok_final = final()
    data['final'] = block
    with open(OUT_JSON, 'w') as fh:
        json.dump(data, fh, indent=2)
    print('gates', 'all pass' if ok_all else 'MISS', '| final', 'all pass' if ok_final else 'MISS')


if __name__ == '__main__':
    main()
