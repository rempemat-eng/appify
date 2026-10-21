"""Bramble design options (Claude J design sheets, 21 Oct).

Bramble, fox-folk forester: a short bow and a sky-blue cape, a starter. 48 art px tall
in a 64 x 72 cell, foot anchor (32, 66). The question: how much fox and how much folk,
and how the cape and bow make the silhouette.

    A  Shoulder capelet, bow slung on the back   (folk first: a ranger in a capelet)
    B  Hooded travelling cape, bow in hand        (cloak first: a hooded triangle with ears)
    C  One-shoulder mantle, quiver, the big brush (fox first: the tail is the signature)

Every view is drawn in its own facing. W is built in its own coordinates (near and far
sides swap: the bow hand and the mantle shoulder are near in W and far in E), and every
part is shaded after placement with the light from the upper left, so the lit side stays
on the west in both facings.

Run from the repo root: python3 scripts/art/characters/designs/bramble.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(REPO, 'docs/vision/characters/designs/bramble-options.png')
OUT_JSON = os.path.join(REPO, 'docs/vision/characters/designs/bramble.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.char-views')), 'bramble')

W, H = 64, 72
FOOT = (32, 66)


# --- painting helpers (on top of the kit) ------------------------------------------------
class P:
    """A Fig plus a facing: `x()` maps design coordinates (drawn facing east) into the
    view. For W the east-facing layout is re-placed on the other side and the near/far
    parts are chosen by the caller; shading always runs after placement, so the light
    stays upper left."""

    def __init__(self, view: str):
        self.f = sk.Fig(W, H)
        self.view = view
        self.flip = view == 'W'
        self.ox = 0   # a whole-part shift in design x (lean, knockback); 0 for the options

    def x(self, x):
        x = x + self.ox
        return 63 - x if self.flip else x

    def pts(self, pts):
        return [(self.x(px) + (1 if self.flip else 0), py) for px, py in pts]

    def poly(self, pts):
        return self.f.poly(self.pts(pts))

    def ell(self, cx, cy, rx, ry):
        cx = cx + self.ox
        return self.f.ellipse(64 - cx if self.flip else cx, cy, rx, ry)

    def rect(self, x0, y0, x1, y1, knock=0):
        x0, x1 = x0 + self.ox, x1 + self.ox
        if self.flip:
            x0, x1 = 63 - x1, 63 - x0
        return self.f.rect(x0, y0, x1, y1, knock)

    def put(self, x, y, fam, tone):
        self.f.put(self.x(x), y, fam, tone)

    def tone_at(self, p):
        v = self.f.px.get(p)
        return v


def bbox(mask):
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    return min(xs), min(ys), max(xs), max(ys)


def fur(fig, mask, fam='clay', tuft=True, soft=0.05):
    """Fur: parts shading, then clumped tufts as warm/cool sibling dominoes at the same
    tone (shape without value noise), a few lit tufts on the upper left."""
    mask = set(mask)
    if not mask:
        return
    fig.shade(mask, fam, soft=soft)
    if not tuft:
        return
    x0, y0, x1, y1 = bbox(mask)
    row = 0
    for y in range(y0 + 1, y1, 3):
        off = (row % 2) * 2
        for x in range(x0 + off, x1, 4):
            pts = [(x, y), (x + 1, y), (x, y + 1)]
            if not all(p in mask for p in pts):
                continue
            t = fig.px[(x, y)][1]
            if not all(fig.px[p][1] == t for p in pts):
                continue
            sib = fam + ('_warm' if t >= 4 else '_cool' if t <= 2 else ('_warm' if (x + y) % 2 else '_cool'))
            for p in pts:
                fig.put(p[0], p[1], sib, t)
        row += 1


def cloth(fig, mask, fam='sky', fold=3, lit_frac=0.25, flip=False):
    """Cloth folds as vertical bands: lit (4), body (3), shaded (2), deep (1); a lit rim
    along the top, a darker scalloped hem. Bands follow the light: west lit, east deep."""
    mask = set(mask)
    if not mask:
        return
    x0, y0, x1, y1 = bbox(mask)
    w = max(1, x1 - x0 + 1)
    for (x, y) in mask:
        f = (x - x0 + 0.5) / w
        base = 4 if f < lit_frac else 3 if f < 0.58 else 2 if f < 0.84 else 1
        # folds open downward from the shoulder: alternate bands a tone down
        depth = y - y0
        band = (x - x0 + (1 if depth > 6 else 0)) // fold
        if depth > 2 and band % 2 == 1 and base in (3, 4):
            base -= 1
        if (x, y - 1) not in mask:
            base = min(5 if f < 0.3 else 4, base + 1)
        elif (x, y + 1) not in mask:
            base = max(1, base - 1)
        fam_s = fam + '_warm' if base >= 4 else fam + '_cool' if base <= 1 else fam
        fig.put(x, y, fam_s, base)


def thick_line(p, pts, fam, tone, width=2):
    """A line two pixels wide (horizontal dominoes), so a diagonal strap or a bow limb
    reads as clusters, never a speckle staircase."""
    f = p.f
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(abs(xb - xa), abs(yb - ya), 1)
        for i in range(n + 1):
            x = round(xa + (xb - xa) * i / n)
            y = round(ya + (yb - ya) * i / n)
            for k in range(width):
                p.put(x + k, y, fam, tone)


def shade_limb(fig, mask, fam, light=True):
    """A small cylinder (an arm, a leg, a bow limb): lit left column, body, dark right
    column, a dark last row; joints come from the darker part placed beside it."""
    mask = set(mask)
    for (x, y) in mask:
        left = (x - 1, y) not in mask
        right = (x + 1, y) not in mask
        bottom = (x, y + 1) not in mask
        t = 3
        if left and light:
            t = 4
        if right:
            t = 2
        if bottom:
            t = 1 if not left else 2
        fig.put(x, y, fam, t)


def despeckle(fig, keep=(), passes=2):
    """The painter's cleanup before the outline: a fill pixel unlike all four neighbours
    takes the colour most of its neighbours share (or the darker one), unless it is ink
    (an eye, a nose) or a pixel placed on purpose (a glint, a buckle) listed in `keep`.
    This trims the stair-step crumbs a shading pass leaves on a diagonal terminator."""
    keep = set(keep)
    for _ in range(passes):
        changes = {}
        for (x, y), v in fig.px.items():
            if v[0] == 'ink' or (x, y) in keep or (x, y) in fig.fixed:
                continue
            nb = [fig.px.get((x + dx, y + dy)) for dx, dy in sk.N4]
            if any(n is None for n in nb) and sum(n is None for n in nb) > 2:
                continue
            nb = [n for n in nb if n is not None and n[0] != 'ink']
            if not nb or any(n == v for n in nb):
                continue
            counts = {}
            for n in nb:
                counts[n] = counts.get(n, 0) + 1
            best = max(counts.items(), key=lambda kv: (kv[1], -kv[0][1]))[0]
            changes[(x, y)] = best
        if not changes:
            break
        fig.px.update(changes)


# --- parts shared by the options --------------------------------------------------------
def fox_head_S(p, top=24, ear_h=6, ear_w=7, ruff=3, look=0, eyes='open', tilt=0):
    """The fox head from the front: a wide cranium, cheek ruffs that flare out, tall ears
    with dark backs and cream fluff, a white mask under the eyes, a dark nose."""
    f = p.f
    cy = top + 7
    head = f.ellipse(32, cy, 8.5, 7.2)
    # cheek ruffs: tufts that flare sideways (the fox's front silhouette)
    rl = f.poly([(25, cy - 1), (24 - ruff, cy + 5), (27, cy + 6.5)])
    rr = f.poly([(39, cy - 1), (40 + ruff, cy + 5), (37, cy + 6.5)])
    # ears: big triangles; tilt leans them (an ear turned to listen)
    el = f.poly([(23, cy - 2), (24 - tilt, cy - 2 - ear_h - 4), (24 + ear_w - 1, cy - 4)])
    er = f.poly([(41, cy - 2), (40 + tilt, cy - 2 - ear_h - 4), (41 - ear_w + 1, cy - 4)])
    for e in (el, er):
        fur(f, e, 'clay', tuft=False)
    # dark ear backs at the tip (fox ears are black-tipped)
    for e in (el, er):
        ys = sorted({q[1] for q in e})
        for q in e:
            if q[1] <= ys[0] + 2:
                f.put(q[0], q[1], 'timber_cool', 1 if q[1] > ys[0] else 2)
    # inner ear fluff (cream, shaded)
    il = f.poly([(25, cy - 3), (25 - tilt + 0.5, cy - ear_h - 2), (28.5, cy - 4)])
    ir = f.poly([(39, cy - 3), (39 + tilt - 0.5, cy - ear_h - 2), (35.5, cy - 4)])
    for q in il:
        f.put(q[0], q[1], 'plaster', 2)
    for q in ir:
        f.put(q[0], q[1], 'plaster', 1)
    for q in list(il)[:0]:
        pass
    fur(f, head, 'clay')
    fur(f, rl | rr, 'clay', tuft=False)
    # white mask: cheeks and muzzle under the eyes
    mask = f.ellipse(32, cy + 4.6, 6.6, 3.3) | f.poly([(25, cy + 2), (27, cy + 6.5), (24 - ruff + 1, cy + 5)]) \
        | f.poly([(39, cy + 2), (37, cy + 6.5), (40 + ruff - 1, cy + 5)])
    mask &= (head | rl | rr)
    for (x, y) in mask:
        t = 4 if x < 30 and y < cy + 5 else 3
        if x > 35:
            t = 2
        if (x, y + 1) not in (head | rl | rr) or y >= cy + 6:
            t = 2 if x < 33 else 1
        f.put(x, y, 'plaster', t)
    # bridge of the nose: a clay wedge between the eyes, down to the nose
    for y in range(cy, cy + 4):
        hw = 2 if y < cy + 2 else 1
        for x in range(32 - hw, 32 + hw):
            t = 3 if x < 32 else 2
            f.put(x, y, 'clay', t)
    # nose
    f.put(31, cy + 4, 'ink', 0)
    f.put(32, cy + 4, 'ink', 0)
    f.put(31, cy + 3, 'clay', 1)
    f.put(32, cy + 3, 'clay', 1)
    # mouth: a small shaded line under the nose
    f.put(31, cy + 6, 'plaster', 1)
    f.put(32, cy + 6, 'plaster', 1)
    # brow: a dark clay crease above each eye (gives the face its expression)
    for x in (26, 27, 28):
        f.put(x, cy - 2, 'clay', 2)
    for x in (35, 36, 37):
        f.put(x, cy - 2, 'clay', 1)
    # eyes
    ex = (27, 35)
    for i, x0 in enumerate(ex):
        x0 += look
        if eyes == 'closed':
            f.put(x0, cy, 'ink', 0)
            f.put(x0 + 1, cy, 'ink', 0)
            f.put(x0, cy - 1, 'clay', 2)
            f.put(x0 + 1, cy - 1, 'clay', 2)
        elif eyes == 'squint':
            f.put(x0, cy, 'ink', 0)
            f.put(x0 + 1, cy, 'ink', 0)
            f.put(x0 + (0 if i == 0 else 1), cy + 1, 'ink', 0)
        else:
            for dx in (0, 1):
                for dy in (-1, 0, 1):
                    f.put(x0 + dx, cy + dy, 'ink', 0)
            f.put(x0, cy - 1, 'plaster', 5)   # glint, upper left
    return head | rl | rr | el | er


def fox_head_side(p, top=24, ear_h=6, eyes='open', snout_up=0, look_up=False):
    """The fox head in profile, built facing east and placed for E or W: a round cranium,
    a long tapered snout, a white jaw and cheek, one tall near ear with the far ear
    peeking behind it, a cheek ruff sweeping back."""
    f = p.f
    cy = top + 7
    su = snout_up
    # far ear (behind)
    far = p.poly([(31, cy - 3), (34, cy - 3 - ear_h - 3), (37, cy - 2)])
    for q in far:
        f.put(q[0], q[1], 'clay', 2 if p.flip else 1)   # in W the far ear faces the light
    ys = sorted({q[1] for q in far})
    for q in far:
        if q[1] <= ys[0] + 1:
            f.put(q[0], q[1], 'timber_cool', (1 if q[1] > ys[0] else 2) if p.flip else (0 if q[1] > ys[0] else 1))
    head = p.ell(30, cy, 7.2, 6.8)
    snout = p.poly([(33, cy - 2 - su * 0.4), (42, cy + 1 - su), (43, cy + 3.5 - su), (34, cy + 5)])
    ruff = p.poly([(24, cy + 1), (21, cy + 6), (28, cy + 5)])
    fur(f, head | snout, 'clay')
    fur(f, ruff, 'clay', tuft=False)
    # white jaw and cheek
    jaw = p.poly([(28, cy + 2.5), (35, cy + 3), (43, cy + 3 - su), (42, cy + 4 - su), (34, cy + 6.5), (27, cy + 6)]) & (head | snout | ruff)
    jaw |= p.poly([(22, cy + 5), (25, cy + 2), (28, cy + 5.5)]) & ruff
    for (x, y) in jaw:
        below = (x, y + 1) not in (head | snout | ruff | jaw)
        t = 3 if not below else 1
        if y <= cy + 3 - su and t == 3:
            t = 4
        f.put(x, y, 'plaster', t)
    # nose at the tip
    nx = 42
    ny = round(cy + 2 - su)
    for dx in (0, 1):
        p.put(nx + dx, ny, 'ink', 0)
    p.put(nx + 1, ny + 1, 'ink', 0)
    p.put(nx, ny - 1, 'clay', 2)
    # near ear
    ear = p.poly([(25, cy - 3), (28, cy - 3 - ear_h - 4), (32, cy - 4)])
    fur(f, ear, 'clay', tuft=False)
    ys = sorted({q[1] for q in ear})
    for q in ear:
        if q[1] <= ys[0] + 2:
            f.put(q[0], q[1], 'timber_cool', 1 if q[1] > ys[0] else 2)
    inner = p.poly([(27, cy - 4), (28.5, cy - 2 - ear_h - 2), (30.5, cy - 4)])
    for q in inner:
        f.put(q[0], q[1], 'plaster', 2)
    # brow and eye
    ex, ey = 34, cy - 1
    if eyes == 'closed':
        p.put(ex, ey + 1, 'ink', 0)
        p.put(ex + 1, ey + 1, 'ink', 0)
        p.put(ex, ey, 'clay', 2)
        p.put(ex + 1, ey, 'clay', 2)
    else:
        for dy in (0, 1):
            p.put(ex, ey + dy, 'ink', 0)
            p.put(ex + 1, ey + dy, 'ink', 0)
        p.put(ex + (1 if p.flip else 0), ey, 'plaster', 5)
        for dx in (-1, 0, 1, 2):
            p.put(ex + dx, ey - 1, 'clay', 2)
    return head | snout | ruff | ear | far


def legs_S(p, fam='timber', sock='timber_cool', spread=0, shift=0):
    f = p.f
    left = f.rect(27 - spread, 54, 30 - spread, 61)
    right = f.rect(33 + spread, 54, 36 + spread, 61)
    shade_limb(f, left, fam)
    shade_limb(f, right, fam)
    # dark fox stockings and paw-boots
    for q in left | right:
        if q[1] >= 58:
            f.put(q[0], q[1], sock, f.px[q][1] - 1 if f.px[q][1] > 1 else 1)
    fl = f.rect(26 - spread, 62, 30 - spread, 65, knock=1)
    fr = f.rect(33 + spread, 62, 37 + spread, 65, knock=1)
    shade_limb(f, fl, sock)
    shade_limb(f, fr, sock)
    for q in fl | fr:
        if q[1] == 62:
            f.put(q[0], q[1], sock, 3 if q[0] < 32 else 2)
    return left | right | fl | fr


def legs_side(p, step=0, fam='timber', sock='timber_cool'):
    """Profile legs, facing east: the far leg a tone darker behind the near one."""
    f = p.f
    far = p.rect(28 - step, 54, 31 - step, 61)
    farf = p.rect(28 - step, 62, 33 - step, 65, knock=1)
    for q in far | farf:
        f.put(q[0], q[1], sock if q[1] >= 58 else fam, 1)
    for q in far:
        if q[1] < 58:
            f.put(q[0], q[1], fam, 2)
    near = p.rect(31 + step, 54, 34 + step, 61)
    nearf = p.rect(31 + step, 62, 36 + step, 65, knock=1)
    shade_limb(f, near, fam)
    for q in near:
        if q[1] >= 58:
            f.put(q[0], q[1], sock, max(1, f.px[q][1] - 1))
    shade_limb(f, nearf, sock)
    for q in nearf:
        if q[1] == 62:
            f.put(q[0], q[1], sock, 3)
    return far | farf | near | nearf


def tail_S(p, size=1.0, side=1, up=0):
    """The brush seen from the front: it sweeps out from behind the hip on one side and
    curls up, its white tip at the outer end."""
    f = p.f
    s = size
    cx = 32 + side * (12 * s)
    pts = [(32 + side * 5, 58), (32 + side * 9 * s, 50 - up), (cx + side * 3 * s, 44 - 4 * s - up),
           (cx + side * 6 * s, 47 - up), (cx + side * 5 * s, 56), (32 + side * 9, 62)]
    body = f.poly(pts)
    fur(f, body, 'clay')
    tip = f.ellipse(cx + side * 3.8 * s, 46.5 - 3.2 * s - up, 3.4 * s, 3.4 * s) & body
    for (x, y) in tip:
        t = 4 if (x, y - 1) not in body or (x - 1, y) not in body else 3
        if (x, y + 1) not in tip and y > 46.5 - 3.2 * s - up:
            t = 2
        f.put(x, y, 'plaster', t)
    return body


def tail_side(p, size=1.0, lift=0):
    """The brush in profile, facing east: it leaves the hip, sweeps back and up; the
    white tip at the top."""
    f = p.f
    s = size
    pts = [(30, 52), (24 - 3 * s, 54), (18 - 6 * s, 50 - lift), (16 - 6 * s, 43 - 4 * s - lift),
           (19 - 5 * s, 39 - 6 * s - lift), (23 - 3 * s, 43 - 3 * s - lift), (25, 48), (30, 48)]
    body = p.poly(pts)
    fur(f, body, 'clay')
    tc = (18.5 - 5.5 * s, 42 - 5 * s - lift)
    tip = p.ell(tc[0], tc[1], 3.4 * s, 3.4 * s) & body
    for (x, y) in tip:
        t = 4 if (x, y - 1) not in body else 3
        if p.flip:
            t -= 1   # on the east side in W: the tip turns from the light
        if (x, y + 1) not in tip:
            t = 2
        f.put(x, y, 'plaster', t)
    return body


# --- option A: shoulder capelet, bow on the back -----------------------------------------
def opt_a(view, pose='idle'):
    p = P(view)
    f = p.f
    if view == 'S':
        fid = pose == 'fidget'
        # bow on the back: upper limb over the right shoulder, lower limb at the left hip
        if not fid:
            thick_line(p, [(44, 31), (42, 36), (36, 44), (26, 52), (21, 57), (20, 59)], 'timber', 3)
            for (x, y) in [(44, 31), (45, 31), (20, 59), (21, 59)]:
                f.put(x, y, 'timber', 4 if y < 40 else 2)
        tail_S(p, size=0.9, side=1)
        legs_S(p)
        # jerkin with a flared hem
        torso = f.rect(25, 38, 38, 52, knock=1) | f.poly([(24, 49), (40, 49), (41, 55), (23, 55)])
        cloth(f, torso, 'timber', fold=3, lit_frac=0.22)
        # belt
        for x in range(24, 41):
            if (x, 50) in torso:
                f.put(x, 50, 'timber_cool', 1)
                f.put(x, 51, 'timber_cool', 2 if x < 33 else 1)
        f.put(30, 50, 'brass', 4); f.put(31, 50, 'brass', 4); f.put(30, 51, 'brass', 3); f.put(31, 51, 'brass', 2)
        # chest fluff
        chest = f.poly([(27.5, 38), (36.5, 38), (32, 46)])
        for (x, y) in chest:
            f.put(x, y, 'plaster', 4 if x < 31 else 3 if x < 34 else 2)
        # arms below the capelet
        if fid:
            la = f.rect(19, 43, 23, 49)
            shade_limb(f, la, 'clay')
            ra = f.poly([(39, 43), (42, 44), (36, 50), (33, 49)])
            shade_limb(f, ra, 'clay')
        else:
            la = f.rect(21, 44, 24, 51)
            ra = f.rect(39, 44, 42, 51)
            shade_limb(f, la, 'clay')
            shade_limb(f, ra, 'clay')
            for q in f.rect(21, 51, 24, 53, knock=1) | f.rect(39, 51, 42, 53, knock=1):
                f.put(q[0], q[1], 'timber_cool', 2 if q[0] in (21, 39) else 1)
        # capelet: a short poncho over the shoulders, open at the front, toggled at the neck
        cape = f.poly([(25, 37), (38, 37), (43, 41), (45, 47), (18, 47), (20, 41)])
        cape -= f.poly([(30.5, 37), (33.5, 37), (35.5, 47), (28.5, 47)])
        # scalloped hem: knock out every third pixel on the bottom row
        for x in range(17, 47):
            if (x, 46) in cape and x % 4 == 1:
                cape.discard((x, 46))
        cloth(f, cape, 'sky', fold=3, lit_frac=0.3)
        # the cape's front edges catch the light on the west, fall to shade on the east
        f.put(30, 38, 'timber', 4); f.put(31, 38, 'timber', 4); f.put(32, 38, 'timber', 2); f.put(33, 38, 'timber', 2)
        if fid:
            # bow held up on the left, right paw plucking the string
            bow = [(21, 33), (19, 37), (18, 43), (18, 49), (19, 55), (21, 58)]
            thick_line(p, bow, 'timber', 3)
            for (x, y) in bow[:2]:
                f.put(x, y, 'timber', 4)
            for y in range(34, 58):
                f.put(23 if y < 46 else 23, y, 'plaster', 4 if y < 46 else 3)
            # pluck: the string bends to the paw
            for y in (45, 46, 47):
                f.put(24, y, 'plaster', 4)
                f.put(23, y, 'clay', 2) if False else None
            grip = f.rect(18, 45, 21, 48, knock=1)
            shade_limb(f, grip, 'timber_cool')
            paw = f.rect(24, 46, 27, 49, knock=1)
            shade_limb(f, paw, 'timber_cool')
        fox_head_S(p, top=24, look=-1 if fid else 0, eyes='squint' if fid else 'open', tilt=1 if fid else 0)
    else:
        flip = view == 'W'
        # bow on the back: a tall arc behind the shoulders
        thick_line(p, [(25, 31), (23, 37), (22, 44), (23, 51), (25, 57)], 'timber', 3)
        p.put(25, 31, 'timber', 4)
        tail_side(p, size=0.9)
        legs_side(p)
        torso = p.rect(27, 38, 36, 52, knock=1) | p.poly([(26, 49), (38, 49), (39, 55), (25, 55)])
        cloth(f, torso, 'timber', fold=3, lit_frac=0.25)
        for q in torso:
            if q[1] in (50, 51):
                f.put(q[0], q[1], 'timber_cool', 1 if q[1] == 50 else 2)
        # chest fluff at the front
        chest = p.poly([(33, 38), (38, 38), (37, 44), (34, 45)])
        for q in chest:
            f.put(q[0], q[1], 'plaster', 3 if not flip else 4)
        arm = p.rect(31, 42, 34, 51)
        shade_limb(f, arm, 'clay')
        paw = p.rect(31, 51, 34, 53, knock=1)
        for q in paw:
            f.put(q[0], q[1], 'timber_cool', 2)
        cape = p.poly([(26, 37), (36, 37), (40, 42), (40, 46), (22, 48), (23, 41)])
        for x in range(20, 44):
            if x % 4 == 1:
                cape.discard((p.x(x), 47))
        cloth(f, cape, 'sky', fold=3, lit_frac=0.3)
        # the strap of the bow crossing the cape front
        p.put(37, 38, 'timber', 2); p.put(38, 39, 'timber', 2)
        fox_head_side(p, top=24)
    despeckle(f, getattr(p, 'keep', ()))
    f.outline()
    return f.image()


# --- option B: hooded travelling cape, bow in hand ----------------------------------------
def hood_S(f, top, fid=False):
    """The hood thrown back over the shoulders, its rim framing the ruff: a lit roll."""
    hood = f.poly([(21, top + 11), (43, top + 11), (45, top + 16), (19, top + 16)])
    return hood


def opt_b(view, pose='idle'):
    p = P(view)
    f = p.f
    fid = pose == 'fidget'
    if view == 'S':
        # long cape behind the body, to the calves
        back = f.poly([(24, 37), (40, 37), (46, 50), (47, 60), (17, 60), (18, 50)])
        hem = set()
        for x in range(16, 49):
            if (x, 59) in back and x % 5 in (0, 1):
                hem.add((x, 60))
        cloth(f, back | hem, 'sky', fold=3, lit_frac=0.26)
        # tail tip peeks under the hem on the right
        tail = f.poly([(38, 60), (45, 58), (50, 53), (53, 50), (54, 55), (51, 61), (45, 64), (39, 63)])
        fur(f, tail, 'clay', tuft=False)
        for q in f.ellipse(52.5, 52, 2.8, 3.2) & tail:
            f.put(q[0], q[1], 'plaster', 4 if q[1] < 52 else 3 if q[1] < 54 else 2)
        legs_S(p, fam='earth', sock='timber_cool')
        # tunic (leaf green under the cape: it shows only at the front opening)
        torso = f.rect(26, 39, 37, 54, knock=1)
        cloth(f, torso, 'earth', fold=3)
        for q in torso:
            if q[1] == 50:
                f.put(q[0], q[1], 'timber_cool', 1)
            if q[1] == 51:
                f.put(q[0], q[1], 'timber', 2)
        chest = f.poly([(28.5, 39), (35.5, 39), (32, 45)])
        for (x, y) in chest:
            f.put(x, y, 'plaster', 4 if x < 31 else 3 if x < 33 else 2)
        # cape fronts: hang from the shoulders, open in the middle
        lf = f.poly([(25, 38), (29, 38), (28, 58), (19, 59), (20, 46)])
        rf = f.poly([(35, 38), (39, 38), (44, 46), (45, 59), (36, 58)])
        cloth(f, lf, 'sky', fold=3, lit_frac=0.35)
        cloth(f, rf, 'sky', fold=3, lit_frac=0.05)
        for q in rf:
            if (q[0] - 1, q[1]) not in rf:
                f.put(q[0], q[1], 'sky', 3)   # the inner edge turns to the light
        # bow in the left hand (viewer's right is the cape; the bow is on the viewer's left)
        if fid:
            # shading the eyes: right paw up to the brow; bow lowered in the left hand
            bow = [(13, 47), (14, 52), (16, 57), (19, 61)]
            thick_line(p, [(15, 41)] + bow, 'timber', 3)
            for y in range(42, 61):
                f.put(19 + (y - 42) // 10, y, 'plaster', 3) if False else None
            hand = f.rect(15, 47, 18, 50, knock=1)
            shade_limb(f, hand, 'timber_cool')
            pass
        else:
            bow = [(17, 33), (15, 37), (14, 43), (14, 49), (15, 55), (17, 59)]
            thick_line(p, bow, 'timber', 3)
            for (x, y) in bow[:2]:
                f.put(x, y, 'timber', 4)
                f.put(x + 1, y, 'timber', 4)
            for (x, y) in [(18, 33), (17, 59), (18, 59)]:
                f.put(x, y, 'timber', 2)
            for y in range(34, 59):
                f.put(19, y, 'plaster', 4 if y < 46 else 3)
            hand = f.rect(15, 45, 18, 48, knock=1)
            shade_limb(f, hand, 'timber_cool')
        # hood up: a sky cowl round the head, ears through slits
        top = 24
        cy = top + 7
        hood = f.ellipse(32, cy + 1.5, 11.6, 10.4) | f.poly([(27, cy - 7), (37, cy - 7), (32, cy - 11)])
        hood |= f.poly([(21, cy + 2), (43, cy + 2), (42, cy + 9), (22, cy + 9)])
        hood |= f.poly([(26, cy + 8), (38, cy + 8), (40, 40), (24, 40)])
        cloth(f, hood, 'sky', fold=4, lit_frac=0.3)
        head = fox_head_S(p, top=top + 1, ruff=1, ear_h=7,
                          look=-1 if fid else 0, eyes='squint' if fid else 'open', tilt=0)
        # the hood's rim framing the face: a lit roll on the west, a dark fold on the east
        rim = (f.ellipse(32, cy + 2.6, 9.6, 8.3) - f.ellipse(32, cy + 2.8, 7.8, 6.9)) & hood
        rim -= head
        for (x, y) in rim:
            f.put(x, y, 'sky_warm' if x < 32 else 'sky', 4 if x < 30 else 3 if x < 35 else 2)
        if fid:
            # paw shading the eyes, resting on the brow
            arm = f.poly([(39, 43), (44, 42), (46, 34), (43, 28), (40, 29), (42, 35)])
            cloth(f, arm, 'sky', fold=2, lit_frac=0.4)
            for (x, y) in arm:
                if (x - 1, y) not in arm or (x, y + 1) not in arm:
                    f.put(x, y, 'sky', 1)   # the sleeve's underside: a dark seam against the hood
            pw = f.rect(32, 26, 42, 28, knock=1)
            shade_limb(f, pw, 'timber_cool')
            for x in range(33, 42):
                f.put(x, 26, 'timber_cool', 4 if x < 36 else 3)
            for x in (35, 38):
                f.put(x, 28, 'timber_cool', 1)   # finger gaps
    else:
        flip = view == 'W'
        # bow: in the left hand, so far in E (behind the body) and near in W (in front)
        def draw_bow(front):
            arc = [(37, 33), (39, 37), (40, 43), (40, 49), (39, 55), (37, 59)]
            thick_line(p, arc, 'timber', 3 if front else 2)
            if front:
                # the near limb's west face takes the light
                for (ax, ay), (bx, by) in zip(arc, arc[1:]):
                    n = max(abs(bx - ax), abs(by - ay), 1)
                    for i in range(n + 1):
                        x = round(ax + (bx - ax) * i / n)
                        y = round(ay + (by - ay) * i / n)
                        p.put(x + 1, y, 'timber', 4)
            p.put(37, 33, 'timber', 4)
            for y in range(34, 59):
                p.put(36, y, 'plaster', 3 if front else 2)
        if not flip:
            draw_bow(False)
        back = p.poly([(25, 37), (34, 37), (36, 48), (36, 60), (18, 61), (19, 48)])
        for x in range(16, 40):
            if x % 5 in (0, 1) and (p.x(x), 60) in back:
                back.add((p.x(x), 61))
        cloth(f, back, 'sky', fold=3, lit_frac=0.3)
        tail = p.poly([(25, 60), (18, 61), (13, 59), (10, 55), (13, 53), (17, 57), (25, 56)])
        fur(f, tail, 'clay', tuft=False)
        for q in p.ell(11.5, 55, 2.6, 2.6) & tail:
            f.put(q[0], q[1], 'plaster', (4 if q[1] < 55 else 3) - (1 if p.flip else 0))
        legs_side(p, fam='earth')
        torso = p.rect(29, 39, 37, 54, knock=1)
        cloth(f, torso, 'earth')
        for q in torso:
            if q[1] == 50:
                f.put(q[0], q[1], 'timber_cool', 1)
        chest = p.poly([(34, 39), (38, 39), (37, 44), (35, 45)])
        for q in chest:
            f.put(q[0], q[1], 'plaster', 3)
        if flip:
            draw_bow(True)
            hand = p.rect(35, 45, 38, 48, knock=1)
            shade_limb(f, hand, 'timber_cool')
        top = 24
        cy = top + 7
        hood = p.ell(29, cy + 1, 10, 9.4) | p.poly([(21, cy + 4), (34, cy + 6), (34, 40), (22, 42)])
        cloth(f, hood, 'sky', fold=4, lit_frac=0.3)
        fox_head_side(p, top=top + 1, ear_h=7)
        # hood rim behind the cheek
        rim = p.poly([(27, cy - 4), (30, cy - 5), (27, cy + 7), (25, cy + 6)]) & hood
        for q in rim:
            if f.px.get(q, ('', 0))[0].startswith('sky'):
                f.put(q[0], q[1], 'sky', 2)
    despeckle(f, getattr(p, 'keep', ()))
    f.outline()
    return f.image()


# --- option C: one-shoulder mantle, quiver, the big brush ---------------------------------
def opt_c(view, pose='idle'):
    p = P(view)
    f = p.f
    fid = pose == 'fidget'
    if view == 'S':
        # quiver on the back: fletching over the left shoulder
        q = f.rect(17, 30, 22, 44, knock=1)
        for (x, y) in [(18, 27), (19, 27), (19, 26), (20, 26), (21, 28), (22, 28), (21, 27)]:
            pass
        quiver = f.poly([(16, 31), (20, 28), (27, 42), (23, 45)])
        cloth(f, quiver, 'timber', fold=2, lit_frac=0.3)
        for i, (fx, fy) in enumerate([(13, 23), (16, 21), (19, 23)]):
            fam = 'sky' if i != 1 else 'plaster'
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)):
                f.put(fx + dx, fy + dy, fam, (4 if dx == 0 else 3) - (1 if dy == 2 else 0))
            for k in range(3, 7):
                f.put(fx + 1 + k // 3, fy + k, 'timber', 3); f.put(fx + 2 + k // 3, fy + k, 'timber', 2)
        # the big brush: up behind the right shoulder, as tall as the head
        up = 6 if fid else 0
        tail = f.poly([(36, 58), (44, 54), (50, 46), (51, 36 - up), (48, 29 - up), (44, 31 - up),
                       (46, 39 - up), (42, 48), (35, 52)])
        fur(f, tail, 'clay')
        tip = f.ellipse(48, 32 - up, 3.8, 4.4) & tail
        for (x, y) in tip:
            t = 4 if (x, y - 1) not in tail or (x - 1, y) not in tail else 3
            if x >= 50 or (x, y + 1) not in tip:
                t = 2
            f.put(x, y, 'plaster', t)
        # lower fox legs: shorts, dark stockings, digitigrade paws
        legs_S(p, fam='clay', sock='timber_cool')
        torso = f.rect(26, 39, 37, 53, knock=1) | f.poly([(25, 49), (38, 49), (39, 55), (24, 55)])
        cloth(f, torso, 'leaf', fold=3, lit_frac=0.25)
        for q in torso:
            if q[1] == 50:
                f.put(q[0], q[1], 'timber_cool', 1)
        # cream chest, wide: more fox than folk
        chest = f.poly([(27.5, 39), (36.5, 39), (34, 47), (30, 47)])
        for (x, y) in chest:
            f.put(x, y, 'plaster', 4 if x < 31 else 3 if x < 34 else 2)
        # quiver strap across the chest
        thick_line(p, [(37, 39), (33, 43), (27, 49)], 'timber_cool', 2)
        # arms
        la = f.rect(22, 41, 25, 50)
        shade_limb(f, la, 'clay')
        for qq in f.rect(22, 50, 25, 52, knock=1):
            f.put(qq[0], qq[1], 'timber_cool', 2)
        ra = f.rect(38, 42, 41, 50)
        shade_limb(f, ra, 'clay')
        for qq in f.rect(38, 50, 41, 52, knock=1):
            f.put(qq[0], qq[1], 'timber_cool', 1)
        # mantle over the left shoulder only (viewer's left): it hangs to the hip in a point
        mantle = f.poly([(19, 40), (24, 37), (31, 37), (38, 41), (37, 44), (30, 43), (26, 48), (24, 53), (20, 50), (18, 44)])
        cloth(f, mantle, 'sky', fold=3, lit_frac=0.3)
        # brooch where it fastens on the chest
        f.put(32, 40, 'timber', 4); f.put(33, 40, 'timber', 3); f.put(32, 41, 'timber', 3); f.put(33, 41, 'timber', 2)
        # short bow in the right paw, held low
        bow = [(42, 41), (44, 45), (44, 51), (42, 55)]
        thick_line(p, bow, 'timber', 3)
        p.put(42, 41, 'timber', 4)
        for y in range(42, 55):
            f.put(41, y, 'plaster', 3)
        fox_head_S(p, top=24, ear_h=7, ear_w=7, ruff=3, eyes='closed' if fid else 'open', tilt=-1 if fid else 0)
        if fid:
            # sniffing: muzzle tipped up shows as the nose lifted and a sniff tuft
            f.put(31, 34, 'ink', 0); f.put(32, 34, 'ink', 0)
    else:
        flip = view == 'W'
        # tail: the big brush sweeping up behind
        pts = [(30, 54), (22, 54), (15, 47), (13, 37), (16, 28), (21, 27), (19, 35), (21, 44), (27, 48), (31, 48)]
        tail = p.poly(pts)
        fur(f, tail, 'clay')
        tip = p.ell(17.5, 31, 4.2, 4.6) & tail
        for q in tip:
            t = (4 if (q[0], q[1] - 1) not in tail else 3) - (1 if flip else 0)
            if (q[0], q[1] + 1) not in tip:
                t = 2
            f.put(q[0], q[1], 'plaster', t)
        # quiver on the back, fletching up behind the head
        quiver = p.poly([(25, 35), (28, 34), (30, 46), (27, 47)])
        cloth(f, quiver, 'timber', fold=2)
        for i, (fx, fy) in enumerate([(22, 30), (25, 28)]):
            fam = 'sky' if i == 0 else 'plaster'
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)):
                p.put(fx + dx, fy + dy, fam, (4 if dx == (1 if p.flip else 0) else 3) - (1 if dy == 2 else 0))
            p.put(fx + 1, fy + 3, 'timber', 2); p.put(fx + 2, fy + 3, 'timber', 2)
        legs_side(p, fam='clay')
        torso = p.rect(28, 39, 36, 53, knock=1) | p.poly([(27, 49), (37, 49), (38, 55), (26, 55)])
        cloth(f, torso, 'leaf', lit_frac=0.3)
        for q in torso:
            if q[1] == 50:
                f.put(q[0], q[1], 'timber_cool', 1)
        chest = p.poly([(33, 39), (38, 39), (37, 45), (34, 46)])
        for q in chest:
            f.put(q[0], q[1], 'plaster', 3)
        arm = p.rect(31, 42, 34, 51)
        shade_limb(f, arm, 'clay')
        for q in p.rect(31, 51, 34, 53, knock=1):
            f.put(q[0], q[1], 'timber_cool', 2)
        # mantle on the left shoulder: far in E (a sliver at the back), near in W (over the arm)
        if flip:
            mantle = p.poly([(27, 38), (35, 38), (37, 44), (33, 50), (29, 47), (27, 43)])
            cloth(f, mantle, 'sky', lit_frac=0.35)
        else:
            mantle = p.poly([(25, 38), (29, 38), (28, 46), (25, 49)])
            cloth(f, mantle, 'sky', lit_frac=0.4)
        # short bow in the right paw: near in E, far (behind) in W
        if not flip:
            thick_line(p, [(35, 43), (38, 46), (38, 51), (36, 55)], 'timber', 3)
            for y in range(44, 55):
                p.put(35, y, 'plaster', 3)
        fox_head_side(p, top=24, ear_h=7)
    despeckle(f, getattr(p, 'keep', ()))
    f.outline()
    return f.image()


# --- sheet -------------------------------------------------------------------------------
OPTIONS = [
    dict(label='A', name='Capelet ranger: short shoulder cape, bow slung on the back', fn=opt_a,
         question='Folk first: an upright ranger whose fox reads from ears, ruff and a mid-size brush; '
                  'the capelet widens the shoulders and the bow tips frame the body diagonally.',
         palette=['clay', 'plaster', 'sky', 'timber', 'brass'],
         pose='Weight even, paws loose at the sides, ears up: a calm guide who has walked every path.',
         fidget='Checks the bowstring: bow brought round to the left, a paw plucks the string, ears tilt, eyes narrow.',
         parts=[
             'bow (timber, back layer 0, slung; changes S/E/W, attaches back; swaps to hand in fight wind-up/strike)',
             'tail (clay+plaster tip, layer 1, swings opposite the hips in walk; S/E/W; attaches hip)',
             'far leg / near leg (timber + timber_cool stocking, layer 2; walk 6-frame swing; attach hip)',
             'jerkin with belt (timber, brass buckle, layer 3; breath 1 rig px; attaches hip)',
             'arms + paws (clay, timber_cool paw, layer 4; walk swing, guard, cheer up; attach chest)',
             'capelet (sky, layer 5; lags 1 frame in walk, flips up on react hop; attaches chest)',
             'head (clay + plaster mask, layer 6; nap curl tucks it; attaches chest)',
             'ears (clay, timber_cool tips, layer 7; flick in blink/fidget, flatten on hit; attach head)'],
         notes=['Reads as a person first: the capelet makes a clear triangle at the shoulders and the bow tips poke out on the diagonal.',
                'Risk: the brush is mid-size and the bow mostly hides behind the body; at 2 device px the fox rests on the ears and ruff.',
                'Compared with Eastward (eastward-04 market: John, Sam, the stall keepers) at 48 px: theirs use 3-4 tones a material, big flat clothing planes, 2 px eyes.']),
    dict(label='B', name='Hooded traveller: long hooded cape, bow carried in the hand', fn=opt_b,
         question='Cloak first: a sky hooded cape makes one big blue triangle; the fox shows as ears through the hood, '
                  'the muzzle, and a tail tip under the hem; the bow is a tall arc at the side.',
         palette=['sky', 'clay', 'plaster', 'timber', 'earth'],
         pose='Bow held upright at the side like a staff, hood up: a quiet scout on the edge of the trees.',
         fidget='Shades the eyes: lowers the bow, lifts a paw to the brow and squints along the path.',
         parts=[
             'cape back panel (sky, layer 0, sways 1 rig px behind the walk; S/E/W; attaches chest)',
             'tail tip (clay+plaster, layer 1, flicks under the hem; attaches hip)',
             'legs (earth breeches, timber_cool stockings, layer 2; walk swing; attach hip)',
             'tunic (earth, layer 3; attaches hip)',
             'bow (timber + plaster string, layer 4 in W/S, layer 0 in E (far hand); attaches hand)',
             'cape fronts (sky, layer 5; part on walk, fold round the body in nap curl; attach chest)',
             'hood (sky, layer 6; falls back on cheer and react hop; attaches head)',
             'head + ears (clay, plaster mask, layer 7; ears through the hood slits; attach head)'],
         notes=['The strongest blue mass of the three: it reads against grass at a glance and gives the most distinct silhouette in the cast.',
                'Risk: the cloak hides arms and legs, so walk and fight poses lose readable limbs; the fox depends on the ears alone from behind.',
                'Compared with Eastward eastward-04 (Sam\'s long white hair as one mass, the robed stall keeper): one big shape, 3-4 bands, limbs only at the hem.']),
    dict(label='C', name='Fox scout: one-shoulder mantle, quiver, the big brush', fn=opt_c,
         question='Fox first: the brush rises as high as the head on one side and the quiver fletching on the other, '
                  'so the silhouette is a fox from any distance; a sky mantle over one shoulder.',
         palette=['clay', 'plaster', 'sky', 'leaf', 'timber'],
         pose='Head up, short bow loose in one paw, brush high: alert and light on its feet.',
         fidget='Sniffs the wind: eyes shut, muzzle lifted, the brush rises and flicks.',
         parts=[
             'quiver + fletching (timber, sky and plaster fletch, layer 0; attaches back)',
             'tail (clay, plaster tip, layer 1; the signature: sways in idle, counter-swings in walk, wraps in nap; attaches hip)',
             'legs (clay shins, timber_cool stockings, layer 2; walk swing; attach hip)',
             'tunic (leaf, layer 3; attaches hip)',
             'arms (clay, layer 4; attach chest)',
             'mantle (sky, layer 5, on the left shoulder; near in W, far in E; attaches chest)',
             'short bow (timber + plaster string, layer 6 in E/S, layer 0 in W; attaches hand)',
             'head + ears (clay, plaster mask, layer 7; attach head)'],
         notes=['The tail makes this the most fox: two values give ears, cheek ruffs and a brush taller than the shoulders.',
                'Risk: the sky mantle is smallest here and the leaf tunic sits close to grass; the tail adds width that crowds the familiar.',
                'Compared with Eastward eastward-04 at the same height: one strong shape (Sam\'s hair, John\'s pack) outweighs interior detail at 2 device px.']),
]

VIEWS = [('S idle', 'S', 'idle'), ('E idle', 'E', 'idle'), ('W idle', 'W', 'idle'), ('S fidget', 'S', 'fidget')]


# --- final: A, the capelet ranger, with the graders' grafts --------------------------------
# Chosen 21 Oct (revision round): A, because it keeps the limbs free for the walk and fight
# rig and hoods belong to Nix. Grafts: from B a longer, fuller capelet with a back panel to
# the hip (open at the front); from C a taller white-tipped brush (one layer, tip at mid
# back). The bow is one slung part (limb on the back, string across the chest, upper limb
# over the LEFT shoulder) and comes to the LEFT hand only for wind-up, strike and cast.

def fur_dir(fig, mask, fam='clay', soft=0.05, flow=0):
    """Fur as directional tufts: parts shading, then 3 px hooks (two along the row, one
    falling outward under them) one tone down on the body and shade bands, and lit hooks
    a sibling warmer on the lit band. They point away from the part's middle, so the fur
    combs outward and down along the form. `flow` biases the comb (-1 west, +1 east)."""
    mask = set(mask)
    if not mask:
        return
    fig.shade(mask, fam, soft=soft)
    x0, y0, x1, y1 = bbox(mask)
    mid = (x0 + x1) / 2
    row = 0
    for y in range(y0 + 2, y1 - 1, 4):
        off = (row % 2) * 3
        for x in range(x0 + 1 + off, x1, 6):
            d = flow or (-1 if x < mid else 1)
            pts = [(x, y), (x + d, y), (x + 2 * d, y + 1)] if d else [(x, y), (x + 1, y), (x + 1, y + 1)]
            pts = [(x, y), (x + d, y), (x + d, y + 1)]
            if not all(p in mask and (p[0], p[1] + 1) in mask for p in pts):
                continue
            t = fig.px[(x, y)][1]
            if t >= 5 or not all(fig.px[p][0].startswith(fam) for p in pts):
                continue
            if t >= 4:
                c = (fam + '_warm', 4)
            else:
                c = (fam + '_cool' if t <= 2 else fam, max(1, t - 1))
            for p in pts:
                fig.put(p[0], p[1], *c)
        row += 1


def stroke(p, pts, r=1.6):
    """A thick polyline mask (a limb): discs of radius r stamped along it."""
    out = set()
    for (xa, ya), (xb, yb) in zip(pts, pts[1:] or pts):
        n = max(int(max(abs(xb - xa), abs(yb - ya)) * 2), 1)
        for i in range(n + 1):
            out |= p.ell(xa + (xb - xa) * i / n + 0.5, ya + (yb - ya) * i / n + 0.5, r, r)
    return out


def limb(p, pts, fam='clay', paw='timber_cool', far=False, r=1.6):
    """An arm: fur sleeve shaded as a small cylinder, a dark paw at the end. A far limb sits
    a tone down (it is in the body's shade)."""
    f = p.f
    arm = stroke(p, pts, r)
    pw = stroke(p, [pts[-1]], r + 0.3)
    arm -= pw
    f.shade(arm, fam, glint=False)
    f.shade(pw, paw, glint=False)
    if far:
        for q in arm | pw:
            fam_q, t = f.px[q]
            f.put(q[0], q[1], fam_q, max(1, t - 1))
    return arm | pw


def mossling(fig, cx, by, curled=False, asleep=False):
    """The stand-in familiar: a 24 art px Mossling, a round leaf-green blob with two ink eyes
    and a sprout. (cx, by) is its perch anchor: the middle of its base, in cell px."""
    if curled:
        body = fig.ellipse(cx, by - 6, 8, 6)
    else:
        body = fig.ellipse(cx, by - 8.5, 9.5, 8.5)
    fig.shade(body, 'leaf')
    top = min(q[1] for q in body)
    # moss tufts on the crown: grass clusters
    for dx in (-4, 1):
        for q in ((cx + dx, top + 2), (cx + dx + 1, top + 2), (cx + dx, top + 3)):
            fig.put(int(q[0]), q[1], 'grass', 4)
    # sprout: a stem and two leaves
    sx = int(cx)
    if curled:
        for k in range(3):
            fig.put(sx + k, top - 1 + (k // 2), 'grass', 3)
        fig.put(sx + 3, top, 'grass', 4); fig.put(sx + 3, top + 1, 'grass', 3); fig.put(sx + 4, top + 1, 'grass', 2)
    else:
        for y in range(top - 4, top):
            fig.put(sx, y, 'grass', 3)
            fig.put(sx - 1, y, 'grass', 4)
        for (x, y, t) in ((sx - 4, top - 6, 4), (sx - 3, top - 6, 4), (sx - 2, top - 5, 3), (sx - 3, top - 5, 3),
                          (sx + 1, top - 6, 3), (sx + 2, top - 6, 3), (sx + 1, top - 5, 2), (sx + 2, top - 7, 3)):
            fig.put(x, y, 'grass', t)
    ey = by - (6 if curled else 9)
    for ex in (int(cx) - 4, int(cx) + 2):
        if asleep:
            fig.put(ex, ey, 'ink', 0); fig.put(ex + 1, ey, 'ink', 0)
        else:
            fig.put(ex, ey - 1, 'ink', 0); fig.put(ex, ey, 'ink', 0)
            fig.put(ex + 1, ey - 1, 'ink', 0); fig.put(ex + 1, ey, 'ink', 0)
            fig.put(ex, ey - 1, 'leaf', 5)
    return body


def head_side_final(p, top=24, ears='up', eyes='open', mouth=False):
    """The profile head as a form: a round cranium, a brow over the eye, a cheek ruff that
    sweeps back, a stepped snout with a white jaw, the ears tall and black-tipped (or laid
    flat back on a hit). Built facing east; W places it on the other side and swaps which
    ear is near, so the lit planes stay upper left."""
    f = p.f
    cy = top + 7
    if ears == 'up':
        far = p.poly([(31, cy - 3), (34, cy - 3 - 9), (37, cy - 2)])
        for q in far:
            f.put(q[0], q[1], 'clay', 2 if p.flip else 1)
        ys = sorted({q[1] for q in far})
        for q in far:
            if q[1] <= ys[0] + 1:
                f.put(q[0], q[1], 'timber_cool', 1 if p.flip else 0)
    head = p.ell(30, cy, 7.2, 6.8)
    snout = p.poly([(33, cy - 2), (42, cy + 1), (43, cy + 3.5), (34, cy + 5)])
    ruff = p.poly([(24, cy + 1), (20, cy + 6), (28, cy + 5)])
    fur_dir(f, head | snout, 'clay', flow=-1)
    f.shade(ruff, 'clay', glint=False)
    # the snout's top plane steps down from the brow: a lit ridge then the body tone
    for x in range(35, 42):
        y = round(cy - 1 + (x - 35) * 2 / 7)
        q = (p.x(x), y)
        if q in snout:
            f.put(q[0], q[1], 'clay', 4)
    jaw = p.poly([(28, cy + 2.5), (35, cy + 3), (43, cy + 3), (42, cy + 4), (34, cy + 6.5), (27, cy + 6)]) & (head | snout | ruff)
    jaw |= p.poly([(21, cy + 5), (25, cy + 2), (28, cy + 5.5)]) & ruff
    for (x, y) in jaw:
        below = (x, y + 1) not in (head | snout | ruff | jaw)
        t = 1 if below else 4 if y <= cy + 3 else 3
        f.put(x, y, 'plaster', t)
    # cheek: a shade crescent behind the jaw where the cranium turns under
    for (x, y) in head:
        dxs = (x - p.x(30)) * (-1 if p.flip else 1)
        if y >= cy + 3 and -3 <= dxs <= 1 and f.px[(x, y)][0].startswith('clay'):
            f.put(x, y, 'clay', 2)
    # nose
    ny = cy + 2
    p.put(42, ny, 'ink', 0); p.put(43, ny, 'ink', 0); p.put(43, ny + 1, 'ink', 0)
    p.put(41, ny - 1, 'clay', 2)
    if mouth:
        for x in (37, 38, 39):
            p.put(x, cy + 4, 'ink', 0)
        p.put(38, cy + 5, 'clay', 1); p.put(39, cy + 5, 'clay', 1)
    # near ear
    if ears == 'up':
        ear = p.poly([(25, cy - 3), (28, cy - 13), (32, cy - 4)])
        inner = p.poly([(27, cy - 4), (28.5, cy - 10), (30.5, cy - 4)])
    else:   # laid flat back on a hit
        ear = p.poly([(28, cy - 6), (17, cy - 8), (27, cy - 2)])
        inner = p.poly([(26, cy - 5), (20, cy - 7), (26, cy - 4)])
    f.shade(ear, 'clay', glint=False)
    ys = sorted({q[1] for q in ear})
    xs_tip = sorted(ear, key=lambda q: q[0] * (1 if p.flip else -1))
    tipset = set(xs_tip[:5]) if ears != 'up' else {q for q in ear if q[1] <= ys[0] + 2}
    for q in tipset:
        f.put(q[0], q[1], 'timber_cool', 2 if q[1] == ys[0] else 1)
    for q in inner - tipset:
        f.put(q[0], q[1], 'plaster', 2)
    # brow ridge and eye
    ex, ey = 34, cy - 1
    for dx in (-1, 0, 1, 2):
        p.put(ex + dx, ey - 1, 'clay', 2)
    if eyes == 'open':
        for dy in (0, 1):
            p.put(ex, ey + dy, 'ink', 0); p.put(ex + 1, ey + dy, 'ink', 0)
        p.put(ex + (1 if p.flip else 0), ey, 'plaster', 5)
    elif eyes == 'happy':   # an upturned arc
        p.put(ex - 1, ey + 1, 'ink', 0); p.put(ex, ey, 'ink', 0); p.put(ex + 1, ey, 'ink', 0); p.put(ex + 2, ey + 1, 'ink', 0)
    elif eyes == 'squeeze':  # shut tight on a hit: a > shape
        p.put(ex, ey, 'ink', 0); p.put(ex + 1, ey + 1, 'ink', 0); p.put(ex, ey + 2, 'ink', 0)
    else:                   # closed, resting
        p.put(ex, ey + 1, 'ink', 0); p.put(ex + 1, ey + 1, 'ink', 0)
    return head | snout | ruff | ear


def tail_final_side(p, base=(30, 52), lift=0):
    """The brush in profile, one layer: from the hip back and up, the white tip at mid back."""
    bx, by = base
    dy = by - 52
    pts = [(bx, by), (23, 54 + dy), (16, 50 + dy - lift), (12, 43 + dy - lift), (13, 36 + dy - lift),
           (17, 33 + dy - lift), (20, 37 + dy - lift), (20, 43 + dy - lift), (25, 48 + dy), (bx, 48 + dy)]
    body = p.poly(pts)
    fur_dir(p.f, body, 'clay', flow=-1)
    tip = p.ell(15.5, 36.5 + dy - lift, 3.9, 4.1) & body
    for q in tip:
        t = 4 if (q[0], q[1] - 1) not in body else 3
        if p.flip:
            t -= 1
        if (q[0], q[1] + 1) not in tip:
            t = 2
        p.f.put(q[0], q[1], 'plaster', t)
    return body


def bow_on_back_side(p, dy=0, lean=0):
    """The slung bow seen from the side: an arc down the back. Its upper limb crosses the
    left shoulder, so it is near (lit) in W and far (a tone down) in E."""
    f = p.f
    up = [(25 + lean, 31 + dy), (23 + lean, 37 + dy), (22 + lean // 2, 44 + dy)]
    lo = [(22 + lean // 2, 44 + dy), (23, 51 + dy), (25, 57 + dy)]
    thick_line(p, up, 'timber', 3 if p.flip else 2)
    thick_line(p, lo, 'timber', 2 if p.flip else 3)
    p.put(25 + lean, 31 + dy, 'timber', 4 if p.flip else 3)
    p.put(26 + lean, 31 + dy, 'timber', 3 if p.flip else 2)


def bow_in_hand(p, g, mode='loosed', nock=None):
    """The bow in the left hand, upright, the belly towards the foe (east). mode 'loosed':
    the string straight and the arrow gone; 'drawn': the string pulled back to `nock`, an
    arrow on it pointing east."""
    gx, gy = g
    arc = [(gx - 2, gy - 12), (gx, gy - 8), (gx + 1, gy - 3), (gx + 1, gy + 3), (gx, gy + 8), (gx - 2, gy + 12)]
    thick_line(p, arc, 'timber', 3)
    for (x, y) in arc[:2]:
        p.put(x + (1 if p.flip else 0), y, 'timber', 4)
    top, bot = (gx - 2, gy - 12), (gx - 2, gy + 12)
    if mode == 'loosed':
        for y in range(top[1] + 1, bot[1]):
            p.put(gx - 3, y, 'plaster', 3)
    else:
        nx, ny = nock
        thick_line(p, [top, (nx, ny)], 'plaster', 3, width=1 if False else 2)
        thick_line(p, [(nx, ny), bot], 'plaster', 2)
        for x in range(nx, gx + 6):
            p.put(x, ny, 'timber', 3)
        p.put(gx + 6, ny, 'plaster', 4); p.put(gx + 7, ny, 'plaster', 3)
        p.put(nx, ny - 1, 'sky', 4); p.put(nx + 1, ny - 1, 'sky', 4)   # fletching
        p.put(nx, ny + 1, 'sky', 2); p.put(nx + 1, ny + 1, 'sky', 2)


SIDE_POSES = {
    #          ox  dy lean legs   near arm (design pts, from the shoulder)       far arm               bow       ears  eyes     cape swing
    'idle':   dict(ox=0, dy=0, lean=0, legs='stand', near=[(0, 0), (0, 6), (0, 11)], far=[(0, 0), (-1, 6), (-1, 10)],
                   bow='back', ears='up', eyes='open', swing=0),
    'ready':  dict(ox=0, dy=1, lean=1, legs='wide', near=[(0, 0), (2, 5), (5, 7)], far=[(0, 0), (3, 4), (6, 5)],
                   bow='back', ears='up', eyes='open', swing=-1),
    'strike': dict(ox=0, dy=1, lean=2, legs='wide', near=[(0, 0), (-4, 0), (-8, -3)], far=[(0, 0), (7, -1), (13, -1)],
                   bow='loosed', ears='up', eyes='open', swing=-2),
    'cast':   dict(ox=0, dy=0, lean=0, legs='wide', near=[(0, 0), (3, -3), (5, -5)], far=[(0, 0), (7, -2), (12, -2)],
                   bow='drawn', ears='up', eyes='open', swing=0),
    'hit':    dict(ox=-3, dy=1, lean=-3, legs='stagger', near=[(0, 0), (-4, 3), (-7, 2)], far=[(0, 0), (3, -2), (6, -5)],
                   bow='back', ears='flat', eyes='squeeze', swing=3),
    'sit':    dict(ox=0, dy=8, lean=0, legs='sit', near=[(0, 0), (2, 5), (5, 8)], far=[(0, 0), (1, 5), (3, 8)],
                   bow='back', ears='up', eyes='closed', swing=0),
    'cheer':  dict(ox=0, dy=-1, lean=0, legs='stand', near=[(0, 0), (11, -3), (14, -16)], far=[(0, 0), (9, -4), (11, -18)],
                   bow='back', ears='up', eyes='happy', swing=-1, mouth=True),
}


def legs_final_side(p, mode):
    f = p.f
    sock = 'timber_cool'
    if mode == 'stand':
        return legs_side(p)
    if mode in ('wide', 'stagger'):
        if mode == 'wide':
            far_pts, near_pts = [(30, 55), (27, 62)], [(33, 55), (37, 62)]
            far_ft, near_ft = (25, 62, 30, 65), (35, 62, 40, 65)
        else:
            far_pts, near_pts = [(28, 55), (25, 62)], [(31, 55), (33, 62)]
            far_ft, near_ft = (23, 62, 28, 65), (31, 62, 36, 65)
        fl = stroke(p, far_pts, 1.9)
        f.shade(fl, 'timber', glint=False)
        for q in fl:
            f.put(q[0], q[1], sock if q[1] >= 59 else 'timber', 1 if q[1] >= 59 else 2)
        ff = p.rect(*far_ft, knock=1)
        for q in ff:
            f.put(q[0], q[1], sock, 1)
        nl = stroke(p, near_pts, 1.9)
        f.shade(nl, 'timber', glint=False)
        for q in nl:
            if q[1] >= 59:
                f.put(q[0], q[1], sock, max(1, f.px[q][1] - 1))
        nf = p.rect(*near_ft, knock=1)
        f.shade(nf, sock, glint=False)
        return fl | ff | nl | nf
    # sit: legs out in front along the ground, feet up
    far = p.rect(31, 59, 41, 62, knock=1)
    for q in far:
        f.put(q[0], q[1], sock if p.x(39) == q[0] or abs(q[0] - p.x(40)) <= 1 else 'timber', 1)
    farf = p.rect(41, 57, 43, 61, knock=1)
    for q in farf:
        f.put(q[0], q[1], sock, 1)
    near = p.rect(30, 61, 40, 65, knock=1)
    f.shade(near, 'timber', glint=False)
    nf = p.rect(40, 58, 43, 65, knock=1)
    f.shade(nf, sock, glint=False)
    return far | farf | near | nf


def final_side(view, pose):
    cfg = SIDE_POSES[pose]
    p = P(view)
    f = p.f
    ox, dy, lean = cfg['ox'], cfg['dy'], cfg['lean']
    sit = cfg['legs'] == 'sit'
    hip = 54 + (7 if sit else 0)
    p.ox = ox + lean
    # back layers: the slung bow, then the brush
    if cfg['bow'] == 'back':
        bow_on_back_side(p, dy=dy)
    p.ox = ox
    if sit:
        tb = p.poly([(30, 60), (20, 63), (12, 62), (8, 58), (11, 55), (16, 59), (24, 58), (30, 57)])
        fur_dir(f, tb, 'clay', flow=-1)
        for q in p.ell(9.5, 57.5, 2.8, 2.6) & tb:
            f.put(q[0], q[1], 'plaster', (4 if q[1] < 57 else 3) - (1 if p.flip else 0))
    else:
        tail_final_side(p, lift=2 if pose == 'cheer' else -1 if pose == 'hit' else 0)
    sh = (32, 41 + dy)
    # the far arm (the LEFT arm in E: it holds the bow; the RIGHT arm in W: it draws)
    p.ox = ox + lean
    bow_far = cfg['bow'] in ('loosed', 'drawn') and not p.flip
    far_pts = [(sh[0] + a, sh[1] + b) for a, b in cfg['far']]
    near_pts = [(sh[0] + a, sh[1] + b) for a, b in cfg['near']]
    if p.flip and cfg['bow'] in ('loosed', 'drawn'):
        # in W the bow hand (left) is the near arm: swap the arm plans
        far_pts, near_pts = near_pts, far_pts
    limb(p, far_pts, far=True)
    if bow_far:
        g = far_pts[-1]
        bow_in_hand(p, (g[0] + 1, g[1]), cfg['bow'], nock=(near_pts[-1][0] + 1, near_pts[-1][1]))
    p.ox = ox
    legs_final_side(p, cfg['legs'])
    # jerkin: shoulders lean with the body, the hem stays over the hips
    L = lean
    torso = p.poly([(27 + L, 38 + dy), (37 + L, 38 + dy), (38, hip - 1), (26, hip - 1)]) \
        | p.poly([(26, hip - 5), (38, hip - 5), (39, hip + 1), (25, hip + 1)])
    cloth(f, torso, 'timber', fold=3, lit_frac=0.25)
    for q in torso:
        if q[1] == hip - 4:
            f.put(q[0], q[1], 'timber_cool', 1)
        elif q[1] == hip - 3:
            f.put(q[0], q[1], 'timber_cool', 2)
    p.put(36, hip - 4, 'brass', 4); p.put(36, hip - 3, 'brass', 2)
    chest = p.poly([(33 + L, 38 + dy), (38 + L, 38 + dy), (37 + L, 44 + dy), (34 + L, 45 + dy)])
    for q in chest:
        f.put(q[0], q[1], 'plaster', 4 if p.flip else 3)
    # the bowstring across the chest (slung): a short run at the front
    if cfg['bow'] == 'back':
        for k in range(5):
            p.put(37 + L - (k + 1) // 3, 40 + dy + k, 'plaster', 2)
    # capelet with the back panel to the hip (open at the front), swinging with `swing`
    sw = cfg['swing']
    cape = p.poly([(27 + L, 37 + dy), (35 + L, 37 + dy), (38 + L, 41 + dy), (39 + L, 47 + dy), (34 + L, 48 + dy),
                   (31 + sw, 50 + dy), (28 + sw, hip), (21 + sw, hip + 1), (20 + sw, 49 + dy), (23 + L, 41 + dy)])
    for x in range(14, 44):
        if x % 4 == 1:
            cape.discard((p.x(x), hip + 1))
    cloth(f, cape, 'sky', fold=3, lit_frac=0.3)
    # a toggle at the throat
    p.put(37 + L, 38 + dy, 'timber', 3); p.put(37 + L, 39 + dy, 'timber', 2)
    # the familiar on the shoulder away from the foe (the back shoulder)
    perch = None
    if pose != 'idle':
        p.ox = ox + lean
        px_ = p.x(21) + (1 if p.flip else 0)
        perch = (px_, 39 + dy)
        mossling(f, px_, 39 + dy, asleep=pose == 'sit')
    p.ox = ox + lean
    head_side_final(p, top=24 + dy, ears=cfg['ears'], eyes=cfg['eyes'], mouth=cfg.get('mouth', False))
    # the near arm last (in W with the bow in it)
    limb(p, near_pts)
    if p.flip and cfg['bow'] in ('loosed', 'drawn'):
        g = near_pts[-1]
        bow_in_hand(p, (g[0] + 1, g[1]), cfg['bow'], nock=(far_pts[-1][0] + 1, far_pts[-1][1]))
    p.ox = 0
    despeckle(f, getattr(p, 'keep', ()))
    f.outline()
    return f.image(), perch


def final_S(pose='idle'):
    """Front view: the longer capelet over a back panel that flares to the hip at the
    sides, the taller brush on the viewer's right, the bowstring across the chest."""
    p = P('S')
    f = p.f
    fid = pose == 'fidget'
    # slung bow: upper limb over the left shoulder (viewer's right), lower at the right hip
    thick_line(p, [(44, 30), (43, 34), (41, 37)], 'timber', 3)
    f.put(44, 30, 'timber', 4); f.put(45, 30, 'timber', 3)
    thick_line(p, [(23, 54), (21, 57), (19, 59)], 'timber', 2)
    f.put(19, 59, 'timber', 3)
    # the brush: one layer, tip at mid back
    tail = f.poly([(37, 60), (44, 58), (49, 52), (51, 45), (50, 39), (46, 36), (44, 39), (46, 45), (43, 51), (37, 55)])
    fur_dir(f, tail, 'clay', flow=1)
    for (x, y) in f.ellipse(47.5, 39.5, 3.6, 3.8) & tail:
        t = 4 if (x - 1, y) not in tail or (x, y - 1) not in tail else 3
        if x >= 50 or (x, y + 1) not in tail or y >= 42:
            t = 2
        f.put(x, y, 'plaster', t)
    # back panel of the capelet, flaring past the arms to the hip
    back = f.poly([(22, 42), (42, 42), (46, 52), (45, 55), (19, 55), (18, 52)])
    for x in range(16, 48):
        if (x, 54) in back and x % 4 == 1:
            back.discard((x, 54))
    cloth(f, back, 'sky', fold=3, lit_frac=0.3)
    for q in back:
        f.put(q[0], q[1], f.px[q][0], max(1, f.px[q][1] - 1))   # the inside of the cape, in its own shade
    legs_S(p)
    torso = f.rect(25, 38, 38, 52, knock=1) | f.poly([(24, 49), (40, 49), (41, 55), (23, 55)])
    cloth(f, torso, 'timber', fold=3, lit_frac=0.22)
    for x in range(23, 42):
        if (x, 50) in torso:
            f.put(x, 50, 'timber_cool', 1)
            f.put(x, 51, 'timber_cool', 2 if x < 33 else 1)
    f.put(30, 50, 'brass', 4); f.put(31, 50, 'brass', 4); f.put(30, 51, 'brass', 3); f.put(31, 51, 'brass', 2)
    # a pouch on the left hip
    pouch = f.rect(35, 51, 38, 54, knock=1)
    f.shade(pouch, 'timber_warm', glint=False)
    chest = f.poly([(27.5, 38), (36.5, 38), (32, 46)])
    for (x, y) in chest:
        f.put(x, y, 'plaster', 4 if x < 31 else 3 if x < 34 else 2)
    # arms below the capelet
    if fid:
        la = stroke(p, [(22.5, 45), (24, 49), (27, 50)], 1.6)
        f.shade(la, 'clay', glint=False)
    else:
        la = f.rect(21, 46, 24, 52)
        shade_limb(f, la, 'clay')
        for q in f.rect(21, 52, 24, 54, knock=1):
            f.put(q[0], q[1], 'timber_cool', 3 if q[0] == 21 else 2)
    ra = f.rect(39, 46, 42, 52)
    shade_limb(f, ra, 'clay')
    for q in f.rect(39, 52, 42, 54, knock=1):
        f.put(q[0], q[1], 'timber_cool', 2 if q[0] == 39 else 1)
    # capelet: fuller, to the elbows, open at the front
    cape = f.poly([(25, 37), (38, 37), (43, 40), (46, 48), (17, 48), (20, 40)])
    cape -= f.poly([(30.5, 37), (33.5, 37), (36, 48), (28, 48)])
    for x in range(15, 49):
        if (x, 47) in cape and x % 4 == 1:
            cape.discard((x, 47))
    cloth(f, cape, 'sky', fold=3, lit_frac=0.3)
    # the bowstring across the chest, from the left shoulder to the right hip
    if fid:
        thick_line(p, [(36, 39), (33, 43)], 'plaster', 3)
        thick_line(p, [(33, 43), (27, 49)], 'plaster', 4)   # hooked out by the paw: it catches the light
        pw = f.rect(25, 48, 28, 51, knock=1)
        f.shade(pw, 'timber_cool', glint=False)
        f.put(25, 48, 'timber_cool', 4); f.put(26, 48, 'timber_cool', 4)
    else:
        thick_line(p, [(36, 39), (32, 44), (28, 48)], 'plaster', 3)
    f.put(30, 38, 'timber', 4); f.put(31, 38, 'timber', 4); f.put(32, 38, 'timber', 2); f.put(33, 38, 'timber', 2)
    fox_head_S_final(p, top=24, fid=fid)
    despeckle(f)
    f.outline()
    return f.image()


def fox_head_S_final(p, top=24, fid=False):
    """The front head with the directional fur (the options' head, re-furred)."""
    f = p.f
    fox_head_S(p, top=top, look=-1 if fid else 0, eyes='squint' if fid else 'open', tilt=1 if fid else 0)
    cy = top + 7
    head = f.ellipse(32, cy, 8.5, 7.2)
    # comb the crown: hooks outward from the middle, one tone down, only on clay
    for (x, y) in [(25, cy - 4), (28, cy - 6), (35, cy - 6), (38, cy - 4), (24, cy - 1), (39, cy - 1)]:
        d = -1 if x < 32 else 1
        pts = [(x, y), (x + d, y), (x + d, y + 1)]
        if all(q in head and f.px[q][0].startswith('clay') for q in pts):
            t = f.px[(x, y)][1]
            for q in pts:
                f.put(q[0], q[1], 'clay_cool' if t <= 3 else 'clay_warm', max(2, t - 1) if t <= 3 else 4)
    if fid:
        # eyes look down-left at the string
        pass


def final_nap():
    """nap_c, facing S: curled in a ball, the capelet over the back like a blanket, the
    brush wrapped round the front with its white tip under the chin, the familiar curled
    against the right side."""
    p = P('S')
    f = p.f
    body = f.ellipse(31, 56, 14, 8.5)
    fur_dir(f, body, 'clay')
    # the capelet over the back
    cape = f.ellipse(32, 55, 13, 7.5) & {(x, y) for x in range(64) for y in range(46, 57)}
    for x in range(10, 50):
        if x % 4 == 1:
            cape.discard((x, 56))
    cloth(f, cape, 'sky', fold=3, lit_frac=0.3)
    # the slung bow tip peeking over the back
    thick_line(p, [(41, 48), (44, 50), (46, 53)], 'timber', 3)
    # head resting low on the left, on the paws
    head = f.ellipse(23.5, 58.5, 7.6, 5.8)
    el = f.poly([(16, 57), (16, 48), (22, 54)])
    er = f.poly([(25, 54), (30, 48), (31, 57)])
    for e in (el, er):
        f.shade(e, 'clay', glint=False)
        ys = min(q[1] for q in e)
        for q in e:
            if q[1] <= ys + 1:
                f.put(q[0], q[1], 'timber_cool', 1)
    fur_dir(f, head, 'clay')
    mask = f.ellipse(24, 61, 5.5, 2.8) & head
    for (x, y) in mask:
        f.put(x, y, 'plaster', 4 if x < 22 else 3 if x < 26 else 2)
    f.put(23, 60, 'ink', 0); f.put(24, 60, 'ink', 0)
    for ex in (19, 26):   # closed eyes: a soft downturned line each
        f.put(ex, 57, 'ink', 0); f.put(ex + 1, 58, 'ink', 0) if ex < 23 else f.put(ex + 1, 57, 'ink', 0)
        f.put(ex + 1, 57, 'ink', 0)
    # paws under the chin
    for q in f.rect(18, 63, 21, 65, knock=1) | f.rect(26, 63, 29, 65, knock=1):
        f.put(q[0], q[1], 'timber_cool', 3 if q[0] in (18, 26) else 2)
    # the brush wrapped round the front
    tail = f.poly([(45, 55), (47, 62), (41, 66), (29, 66), (28, 62), (37, 62)])
    fur_dir(f, tail, 'clay', flow=-1)
    for q in f.ellipse(30, 64, 3.6, 2.6) & tail:
        f.put(q[0], q[1], 'plaster', 4 if q[1] < 64 else 3)
    # the familiar curled against the right side
    mossling(f, 51, 66, curled=True, asleep=True)
    despeckle(f)
    f.outline()
    return f.image()


FINAL_VIEWS = [('S idle', lambda: (final_S('idle'), None)),
               ('E idle', lambda: final_side('E', 'idle')),
               ('W idle', lambda: final_side('W', 'idle')),
               ('S fidget', lambda: (final_S('fidget'), None)),
               ('nap S', lambda: (final_nap(), None)),
               ('E ready', lambda: final_side('E', 'ready')),
               ('E strike', lambda: final_side('E', 'strike')),
               ('E cast', lambda: final_side('E', 'cast')),
               ('E hit', lambda: final_side('E', 'hit')),
               ('E sit', lambda: final_side('E', 'sit')),
               ('E cheer', lambda: final_side('E', 'cheer')),
               ('W ready', lambda: final_side('W', 'ready')),
               ('W strike', lambda: final_side('W', 'strike'))]

FINAL = dict(
    chosen='A',
    name='A final: capelet ranger',
    grafts=['From B: a longer, fuller capelet with a back panel to the hip (S, E and W), open at the front; it swings with the pose.',
            'From C: a taller, white-tipped brush, one layer, tip at mid back (not head height), clear of the familiar following 14 px behind.',
            'The bow stays one slung part (limb on the back, string across the chest, upper limb over the left shoulder) and comes to the left hand only for wind-up, strike and cast.'],
    palette=['clay', 'plaster', 'sky', 'timber', 'brass'],
    pose='Weight even, paws loose, ears up: a calm guide who has walked every path. Fidget: hooks the slung bowstring with a paw and checks it, ears tilted, eyes narrowed.',
    parts=[
        'bow (timber + plaster string; layer 0 slung on the back, upper limb over the LEFT shoulder; anchor back; changes S/E/W (near in W, far in E); to the LEFT hand (anchor hand) only in wind-up, strike, cast)',
        'brush (clay, plaster tip; layer 1; anchor hip; S/E/W; one layer, counter-swings in walk, lifts on cheer, droops on hit, wraps the front in nap)',
        'capelet back panel (sky; layer 2; anchor chest; S/E/W; to the hip, lags 1 frame in walk, flies on hit)',
        'far leg / near leg (timber breeches, timber_cool stockings and paws; layer 3; anchor hip; S/E/W; walk 6-frame swing, wide stance in fights, out front in sit)',
        'jerkin with belt and pouch (timber, brass buckle; layer 4; anchor hip; S/E/W; breath 1 rig px)',
        'far arm (clay, timber_cool paw; layer 5 behind the jerkin; anchor chest; E/W; the LEFT (bow) arm in E)',
        'capelet front (sky, timber toggle; layer 6; anchor chest; S/E/W; open at the front)',
        'familiar perch (Mossling; layer 7; anchor perch on the back shoulder: left in E, right in W)',
        'head (clay, plaster mask, ink eyes and nose; layer 8; anchor chest; S/E/W; nap tucks it on the paws)',
        'ears (clay, timber_cool tips, plaster fluff; layer 9; anchor head; flick in blink, tilt in fidget, flat on hit)',
        'near arm (clay, timber_cool paw; layer 10; anchor chest; E/W; the LEFT (bow) arm in W)'],
    notes=['Silhouette: the capelet makes a wide blue shoulder and hip shape, the ears and the white-tipped brush say fox at 2 device px; the limbs stay free for the rig.',
           'Fur is combed in 3 px hooks that point out and down from each part; cloth in vertical fold bands; W is placed in its own coordinates with the near/far parts swapped (bow hand, bow limb, perch shoulder).',
           'Compared with Eastward eastward-04 (John, Sam and the two stall keepers) cropped and scaled to 48 px: their 3-4 tones a material, flat cloth planes and 2 px eyes; ours match the tone count, with clustered fur instead of their flat hair masses.'],
)


def final():
    views, nums, perches = [], {}, {}
    ok_all = True
    for cap, fn in FINAL_VIEWS:
        im, perch = fn()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, f"final-{cap.replace(' ', '-')}.png"))
        m = sk.measure(im)
        nums[cap] = {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}
        a = im.getchannel('A').getbbox()
        nums[cap]['bbox'] = list(a)
        if perch:
            perches[cap] = list(perch)
        ok = (m['on_house'] >= 0.999 and m['west_east'] > 0 and m['isolated'] <= 0.04
              and m['colours'] <= 64 and m.get('outline_dark', 0) >= 0.95)
        ok_all &= ok
        print(f"final {cap:9s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:3d}  "
              f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  h {a[3] - a[1]:2d}  {'ok' if ok else 'MISS'}")
    opt = dict(label='A', name=FINAL['name'], views=views, parts=FINAL['parts'], palette=FINAL['palette'],
               pose=FINAL['pose'], notes=FINAL['grafts'] + FINAL['notes'])
    sk.design_sheet('Bramble final: A, the capelet ranger', [opt], OUT_FINAL,
                    note='48 art px, cell 64 x 72, foot (32, 66). Fight poses carry the stand-in Mossling on the perch. Claude J, 21 Oct.')
    block = dict(FINAL)
    block.update(perch_anchor={k: v for k, v in perches.items()}, numbers=nums,
                 eastward_compared=['eastward-04: John, Sam, the fishmonger and the stall keepers'])
    return block, ok_all


OUT_FINAL = os.path.join(REPO, 'docs/vision/characters/designs/bramble-final.png')


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    opts = []
    data = {'id': 'bramble', 'cell': [W, H], 'foot': list(FOOT), 'height_art_px': 48,
            'question': 'How much fox and how much folk, and how the cape and bow make the silhouette.',
            'options': []}
    ok_all = True
    for o in OPTIONS:
        views = []
        nums = {}
        for cap, v, pose in VIEWS:
            im = o['fn'](v, pose)
            views.append((cap, im))
            im.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(im)
            nums[cap] = {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}
            ok = (m['on_house'] >= 0.999 and m['west_east'] > 0 and m['isolated'] <= 0.06
                  and m['colours'] <= 64 and m.get('outline_dark', 0) >= 0.95)
            ok_all &= ok
            print(f"{o['label']} {cap:9s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:3d}  "
                  f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  {'ok' if ok else 'MISS'}")
        opts.append(dict(label=o['label'], name=o['name'], views=views, parts=o['parts'], palette=o['palette'],
                         pose=o['pose'] + ' Fidget: ' + o['fidget'], notes=o['notes']))
        data['options'].append(dict(label=o['label'], name=o['name'], question_answered=o['question'],
                                    parts=o['parts'], palette=o['palette'], pose=o['pose'], fidget=o['fidget'],
                                    notes=o['notes'], numbers=nums))
    sk.design_sheet('Bramble: how much fox, how much folk; cape and bow in the silhouette', opts, OUT_PNG,
                    note='Fox-folk forester, 48 art px, cell 64 x 72, foot (32, 66). Claude J design options, 21 Oct.')
    block, ok_final = final()
    data['final'] = block
    with open(OUT_JSON, 'w') as fh:
        json.dump(data, fh, indent=2)
    print('gates', 'all pass' if ok_all else 'MISS', '| final', 'all pass' if ok_final else 'MISS')


if __name__ == '__main__':
    main()
