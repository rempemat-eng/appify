"""Tam, the Snow Saddle hut warden's apprentice: three design options (Claude J brief, 21 Oct).

Main question: the rucksack and kettle silhouette against a round marmot body.
  A  Bothy Pack   a huge timber-frame rucksack taller than her head, rolled mat on top,
                  the kettle hung off one post and a lantern off the other
  B  Kettle Cap   a compact berry daypack carried high on her left shoulder, the kettle
                  lashed on top of it so it rides beside her bobble like a second hat
  C  Hut Warden   no pack: a chunky knitted scarf, a long stocking cap with a flopped
                  bobble, and the kettle hung from a belt at her hip

Cell 64 x 72 art px, foot anchor (32, 66), Tam 38 art px tall (bobble to toe).
Every view is drawn from its own geometry and shaded fresh, so the light stays at the
upper left in W as well as E (W is never a mirrored E).

    python3 scripts/art/characters/designs/tam.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(REPO, 'docs/vision/characters/designs/tam-options.png')
OUT_JSON = os.path.join(REPO, 'docs/vision/characters/designs/tam.json')
OUT_FINAL = os.path.join(REPO, 'docs/vision/characters/designs/tam-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.char-views')), 'tam')

W, H = 64, 72
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- a facing-aware canvas --------------------------------------------------------------
class View:
    """Geometry is written for the S or E facing; W redraws the E geometry about the
    cell's centre line and shades every part fresh, so the lit side stays west."""

    def __init__(self, facing: str):
        self.f = sk.Fig(W, H)
        self.facing = facing
        self.m = facing == 'W'
        self.keep = set()

    def X(self, x):
        return 63 - x if self.m else x

    def CX(self, cx):
        return 64 - cx if self.m else cx

    def ell(self, cx, cy, rx, ry):
        return self.f.ellipse(self.CX(cx), cy, rx, ry)

    def rect(self, x0, y0, x1, y1, knock=0):
        a, b = sorted((self.X(x0), self.X(x1)))
        return self.f.rect(a, y0, b, y1, knock)

    def poly(self, pts):
        return self.f.poly([(self.CX(x), y) for x, y in pts])

    def put(self, x, y, fam, t):
        self.f.put(self.X(x), y, fam, t)

    def tone(self, p):
        return self.f.px.get(p)


# --- shading ----------------------------------------------------------------------------
def form_shade(fig, mask, fam, lit=2, dark=2, glint=True, cap=0.35, base=3, deep=True):
    """A round part: body tone 3, a lit cap hugging the upper-left rim (4), a dark crescent
    hugging the lower-right rim (2), the underside row 1, a two-pixel glint (5). The bands
    follow the outline of the form, so the terminator curves with it."""
    mask = set(mask)
    if not mask:
        return
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx = (x0 + x1 + 1) / 2
    wdt = max(1, x1 - x0 + 1)
    tones = {}
    for (x, y) in mask:
        t = base
        near_dr = any((x + i, y + j) not in mask for i, j in ((dark, dark), (dark, 0), (0, dark), (1, 1)))
        near_ul = any((x - i, y - j) not in mask for i, j in ((lit, lit), (lit, 0), (0, lit), (1, 1)))
        if near_ul and (x + 0.5 - cx) < cap * wdt and not (near_dr and (x + 0.5 - cx) > 0):
            t = base + 1
        elif near_dr and (x + 0.5 - cx) > -0.25 * wdt:
            t = base - 1
        elif near_dr and (x, y + 1) not in mask:
            t = base - 1
        if deep and (x, y + 1) not in mask and (x + 0.5 - cx) > -0.3 * wdt:
            t = base - 2
        tones[(x, y)] = t
    for p, t in tones.items():
        fig.put(p[0], p[1], fam, t)
    if glint:
        lits = [p for p, t in tones.items() if t == base + 1]
        if lits:
            p = min(lits, key=lambda q: (q[0] + q[1] * 1.3, q[0]))
            for q in (p, (p[0] + 1, p[1])):
                if q in mask and tones[q] == base + 1:
                    fig.put(q[0], q[1], fam, base + 2)


def fur_tufts(fig, mask, fam, step=(4, 3), phase=0):
    """Fur as clumped tufts: vertical dominoes and small Ls that swap to a sibling at the
    same tone (shape without noise); one in three in the body steps a tone down."""
    mask = set(mask)
    if not mask:
        return
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    row = 0
    k = phase
    for y in range(min(ys) + 1, max(ys), step[1]):
        off = (row % 2) * (step[0] // 2)
        for x in range(min(xs) + 1 + off, max(xs), step[0]):
            shape = [(x, y), (x, y + 1)] if k % 2 == 0 else [(x, y), (x, y + 1), (x + 1, y + 1)]
            k += 1
            cur = [fig.px.get(p) for p in shape]
            if not all(p in mask for p in shape) or any(c is None for c in cur):
                continue
            ts = {c[1] for c in cur}
            fs = {c[0] for c in cur}
            if len(ts) != 1 or fs != {fam}:
                continue
            t = ts.pop()
            if t == 3 and k % 3 == 0:
                nf, nt = fam, 2
            elif t >= 4:
                nf, nt = fam + '_warm', t
            elif t in (2, 3):
                nf, nt = fam + '_cool', t
            else:
                continue
            for p in shape:
                fig.put(p[0], p[1], nf, nt)
        row += 1


def joint(fig, mask, light_tone=2, dark_tone=1):
    """A recess where a part overlaps another: the pixels of the part underneath that
    touch this part step down their own ramp (joints are darker than their parts)."""
    mask = set(mask)
    for (x, y) in mask:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in mask or q not in fig.px:
                continue
            fam, t = fig.px[q]
            if fam.startswith('_') or fam == 'ink' or q in fig.fixed:
                continue
            lower = dx > 0 or dy > 0
            nt = min(t, dark_tone if lower else light_tone)
            fig.px[q] = (fam, nt)


def despeckle(fig, keep=(), rounds=2, glints=True):
    """No speckle: a fill pixel unlike all four neighbours takes the most common of its
    neighbours, unless it is an eye, a glint, a rivet or a glow (kept on purpose)."""
    from collections import Counter
    for _ in range(rounds):
        changes = {}
        for p, c in fig.px.items():
            fam, t = c
            if fam == 'ink' or fam.startswith('_') or p in fig.fixed or p in keep or (glints and t == 5):
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n == c for n in nb) or (not glints and False):
                continue
            if glints and any(n is None for n in nb):
                continue
            nb = [n for n in nb if n is not None]
            nb = [n for n in nb if n[0] != 'ink' and not n[0].startswith('_')]
            if not nb:
                continue
            same = [n for n in nb if sk.family_of(n[0]) == sk.family_of(fam)] or nb
            changes[p] = Counter(same).most_common(1)[0][0]
        if not changes:
            break
        fig.px.update(changes)


def part(v, mask, fam, **kw):
    """Draw a part over what is there: a recess round it, then its own shading."""
    mask = set(mask)
    if kw.pop('recess', True):
        joint(v.f, mask)
    form_shade(v.f, mask, fam, **kw)
    return mask


def knit_rows(fig, mask, fam, phase=0):
    """Knit as rows of 2 px loops: every other row a run of loops a tone down."""
    mask = set(mask)
    ys = sorted({p[1] for p in mask})
    for i, y in enumerate(ys):
        if (i + phase) % 2:
            continue
        xs = sorted(p[0] for p in mask if p[1] == y)
        off = (i // 2) % 2
        for x in range(xs[0] + 1 + off, xs[-1], 3):
            pair = [(x, y), (x + 1, y)]
            if all(p in mask for p in pair):
                for p in pair:
                    f, t = fig.px[p]
                    if f.startswith(fam):
                        fig.put(p[0], p[1], fam + '_cool', max(1, t - 1))


def ribs(fig, mask, fam):
    """Cuff ribbing: 2 px vertical ribs alternating with a recessed rib a tone down."""
    for (x, y) in mask:
        if (x // 2) % 2:
            f, t = fig.px[(x, y)]
            fig.put(x, y, fam + '_cool', max(1, t - 1))


# --- props ------------------------------------------------------------------------------
def kettle(v, x, y, spout=1, tilt=0, hook=True):
    """A dented iron kettle, 9 x 8, body top-left at (x, y). spout +1 points east in the
    view's own geometry. tilt lifts the back for pouring."""
    body = v.ell(x + 4.5, y + 4.6 - tilt * 0.3, 4.2, 3.4) | v.rect(x + 1, y + 4, x + 8, y + 7, knock=1)
    if tilt:
        pts = [(x + 0.5, y + 3.5 - tilt), (x + 8.5, y + 2.5), (x + 9, y + 7.5), (x + 1.5, y + 8.5)]
        if spout < 0:   # lift the back, which is east when the spout points west
            pts = [(2 * x + 9.5 - px, py) for px, py in pts]
        body = v.poly(pts) | v.ell(x + 4.6, y + 5.2, 4.0, 3.2)
    sp_x = x + 9 if spout > 0 else x - 2
    spout_m = v.poly([(sp_x - (0.5 if spout > 0 else -2.5), y + 4.5), (sp_x + (3 if spout > 0 else -1), y + 2 + (tilt and 2)),
                      (sp_x + (3.5 if spout > 0 else -1.5), y + 3 + (tilt and 2)), (sp_x + (0.5 if spout > 0 else 1.5), y + 6.5)])
    lid = v.rect(x + 3, y + 1, x + 6, y + 2)
    knob = v.rect(x + 4, y, x + 5, y)
    part(v, spout_m, 'iron', glint=False, lit=1, dark=1)
    part(v, body, 'iron', lit=3, dark=2)
    part(v, lid, 'iron', glint=False, lit=1, dark=1)
    part(v, knob, 'iron_warm', glint=False, lit=1, dark=1, deep=False)
    # the dent: a pressed-in pocket on the shaded side, lit on its lower lip
    dx = x + 6 if not v.m else x + 6
    for p, t in (((dx, y + 4), 1), ((dx + 1, y + 4), 1), ((dx, y + 5), 4), ((dx + 1, y + 5), 3)):
        v.put(p[0], p[1], 'iron', t)
    # a soot-dark base band
    for xx in range(x + 2, x + 8):
        if v.tone((v.X(xx), y + 7)):
            v.put(xx, y + 7, 'iron_cool', 1)
    if hook:
        # the bail handle arching over the lid
        for p in ((x + 2, y + 1), (x + 2, y), (x + 3, y - 1), (x + 4, y - 1), (x + 5, y - 1), (x + 6, y - 1),
                  (x + 7, y), (x + 7, y + 1)):
            if (v.X(p[0]), p[1]) not in v.f.px:
                v.put(p[0], p[1], 'iron', 2)


def lantern(v, x, y):
    """A small hut lantern, 5 x 8, lit: an iron cap and base, lamp glass between."""
    cap = v.rect(x, y + 1, x + 4, y + 2, knock=1)
    base = v.rect(x, y + 7, x + 4, y + 8)
    ring = [(x + 1, y), (x + 2, y - 1), (x + 3, y)]
    for p in ring:
        v.put(p[0], p[1], 'iron', 2)
    part(v, cap, 'iron', glint=False, lit=1, dark=1)
    part(v, base, 'iron', glint=False, lit=1, dark=1)
    for yy in range(y + 3, y + 7):
        v.put(x, yy, 'iron', 2 if not v.m else 2)
        v.put(x + 4, yy, 'iron', 1)
        for xx, t in ((x + 1, 3), (x + 2, 5 if yy in (y + 4, y + 5) else 4), (x + 3, 3)):
            v.f.glow(v.X(xx), yy, 'lamp', t)


def mat_side(v, x0, x1, y):
    """A rolled sleeping mat lying across, seen from the side: rows lit to dark, ends
    rounded, two timber ties."""
    m = v.rect(x0, y, x1, y + 4, knock=1)
    joint(v.f, m)
    for (x, yy) in m:
        t = {0: 4, 1: 4, 2: 3, 3: 2, 4: 1}[yy - y]
        v.f.put(x, yy, 'plaster_cool', t)
    for xx in (min(v.X(x0), v.X(x1)) + 1, ):
        v.f.put(xx, y + 1, 'plaster_cool', 5)
        v.f.put(xx + 1, y + 1, 'plaster_cool', 5)
    # roll seams as 2 px creases along it
    for xx in range(x0 + 4, x1 - 2, 6):
        v.put(xx, y + 2, 'plaster_cool', 2)
        v.put(xx + 1, y + 2, 'plaster_cool', 2)
    for tx in (x0 + 5, x1 - 5):
        for yy in range(y, y + 5):
            v.put(tx, yy, 'timber', 1 if yy > y else 2)


def mat_end(v, cx, cy, r=3.2, fam='plaster_cool', base=3):
    """The same mat seen end on: a disc with its rolled spiral."""
    m = v.ell(cx, cy, r, r)
    part(v, m, fam, lit=1, dark=1, base=base, glint=base >= 3)
    c = (int(v.CX(cx) - 0.5), int(cy - 0.5))
    for p, t in ((c, 1), ((c[0] + 1, c[1]), 2), ((c[0], c[1] + 1), 2)):
        v.f.put(p[0], p[1], fam, t)


def cup(v, x, y, fam='plaster'):
    """An enamel mug, 5 x 4: a dark rim inside, a handle stub east."""
    m = v.rect(x, y, x + 4, y + 3, knock=0)
    part(v, m, fam, glint=False, lit=1, dark=1)
    for xx in range(x + 1, x + 4):
        v.put(xx, y, fam, 1)
    v.put(x + 5, y + 1, fam, 2)
    v.put(x + 5, y + 2, fam, 1)


def steam(v, pts):
    """Steam as two-pixel wisps; particles, so never outlined."""
    for (x, y, t) in pts:
        for p in ((x, y), (x, y - 1)):
            v.f.glow(v.X(p[0]), p[1], 'plaster_warm', t)


# --- the marmot -------------------------------------------------------------------------
def legs_S(v, fur):
    for cx in (27.6, 36.4):
        m = v.ell(cx, 62.8, 3.3, 2.9)
        part(v, m, fur + '_cool', lit=1, dark=1, glint=False)
        # toes: two recesses on the foot's front
        x = int(cx - 0.5)
        v.f.put(x - 1, 64, fur + '_cool', 1)
        v.f.put(x + 1, 64, fur + '_cool', 1)


def legs_side(v, fur, stride=0):
    back = v.ell(29.0 - stride, 62.8, 3.0, 2.8)
    part(v, back, fur + '_cool', lit=2, dark=1, glint=False)
    front = v.ell(34.6 + stride, 62.8, 3.4, 2.9) | v.rect(35, 64, 38, 65)
    part(v, front, fur + '_cool', lit=1, dark=1, glint=False)
    v.put(37, 64, fur + '_cool', 1)


def torso_S(v, fur, wide=0.0):
    m = v.ell(32, 54.6, 10.4 + wide, 8.3)
    # a fur fringe at the hips: notches in the silhouette, not noise
    for x in (23, 41):
        m.discard((x, 61))
    part(v, m, fur, lit=2, dark=2, recess=False)
    # a paler belly: a soft oval a sibling up, read as fur, not a patch
    belly = v.ell(32, 57.2, 5.2, 4.2)
    for p in belly:
        f, t = v.f.px[p]
        if t >= 2:
            v.f.put(p[0], p[1], fur + '_warm', min(4, t + 1) if t == 3 else t)
    fur_tufts(v.f, m, fur)
    return m


def torso_side(v, fur):
    m = v.ell(31.6, 54.6, 9.6, 8.3)
    m.discard((v.X(23), 61))
    part(v, m, fur, lit=2, dark=2, recess=False)
    belly = v.ell(37.0, 56.6, 3.6, 4.4)
    for p in belly:
        if p in m:
            f, t = v.f.px[p]
            if t >= 2:
                v.f.put(p[0], p[1], fur + '_warm', t)   # paler fur, but the east face stays in shade
    fur_tufts(v.f, m, fur, phase=1)
    return m


def tail_side(v, fur):
    m = v.ell(22.6, 58.4, 3.0, 3.6) | v.ell(21.4, 61.0, 2.4, 2.0)
    part(v, m, fur + '_cool', lit=1, dark=1, glint=False)
    # a dark tip, as a marmot's
    for p in ((21, 62), (22, 62), (20, 62)):
        v.put(p[0], p[1], fur + '_cool', 1)


def arm(v, fur, cx, cy, rx=2.7, ry=5.2, paw=True):
    m = v.ell(cx, cy, rx, ry)
    part(v, m, fur, lit=1, dark=1, glint=False)
    if paw:
        ys = max(p[1] for p in m)
        for p in m:
            if p[1] >= ys - 1:
                f, t = v.f.px[p]
                v.f.put(p[0], p[1], fur + '_cool', min(t, 2))
    return m


def arm_side(v, fur, swing=0):
    """The near arm in profile: a short sleeve-less fur limb angled a little forward,
    the paw a darker mitten at its tip."""
    m = v.poly([(31.0, 49.0), (35.0, 49.0), (37.5 + swing, 57.5), (34.0 + swing, 58.5)]) | v.ell(35.6 + swing, 57.2, 2.2, 1.8)
    part(v, m, fur, lit=1, dark=1, glint=False)
    for p in m:
        if p[1] >= 57:
            f, t = v.f.px[p]
            v.f.put(p[0], p[1], fur + '_cool', min(t, 2))
    return m


def head_S(v, fur, hat, hat_kind='bobble', eyes='open', cheeks=0.0, hat_low=0):
    # ears under the hat's cuff
    for ecx in (23.4, 40.6):
        e = v.ell(ecx, 40.4, 2.4, 2.2)
        part(v, e, fur, lit=1, dark=1, glint=False)
        v.f.put(int(ecx - 0.5), 41, fur + '_cool', 1)
    head = v.ell(32, 43.0, 9.6, 6.6) | v.ell(26.0, 45.6, 4.2 + cheeks, 3.0) | v.ell(38.0, 45.6, 4.2 + cheeks, 3.0)
    part(v, head, fur, lit=2, dark=2)
    fur_tufts(v.f, head, fur, step=(5, 3), phase=1)
    # cheek tufts at the jowls: two-pixel notches of the darker sibling
    for p in ((22, 46), (22, 47), (41, 46), (41, 47)):
        if p in head:
            v.f.put(p[0], p[1], fur + '_cool', 2)
    # the pale muzzle
    muz = v.ell(32, 46.6, 4.6, 2.8)
    part(v, muz, 'plaster', lit=1, dark=1, glint=False, recess=False)
    # a dark brow band across the eyes, as a marmot's mask
    for x in (26, 27, 28, 29, 34, 35, 36, 37):
        v.f.put(x, 41, fur + '_cool', 2)
    if eyes == 'open':
        for ex in (27, 35):
            for p in ((ex, 42), (ex + 1, 42), (ex, 43), (ex + 1, 43)):
                v.f.put(p[0], p[1], 'ink', 0)
            v.f.put(ex, 42, 'plaster', 5)
    elif eyes == 'shut':
        for ex in (27, 35):
            for p in ((ex - 1, 43), (ex, 42), (ex + 1, 42), (ex + 2, 43)):
                v.f.put(p[0], p[1], fur + '_cool', 0)
    # nose, mouth, buck teeth
    for p in ((31, 44), (32, 44)):
        v.f.put(p[0], p[1], 'ink', 0)
    v.f.put(31, 45, fur + '_cool', 1)
    v.f.put(32, 45, fur + '_cool', 1)
    for p in ((30, 46), (33, 46)):
        v.f.put(p[0], p[1], 'plaster', 1)
    v.f.put(31, 47, 'plaster', 5)
    v.f.put(32, 47, 'plaster', 4)
    v.f.put(31, 48, 'plaster', 2)
    v.f.put(32, 48, 'plaster', 2)
    if hat_kind == 'bobble':
        bobble_hat_S(v, hat, low=hat_low)
    else:
        stocking_hat_S(v, hat)
    return head


def bobble_hat_S(v, hat, low=0):
    dome = {p for p in v.ell(32, 37.6 + low, 9.4, 6.4) if p[1] <= 37 + low}
    cuff = v.rect(22, 37 + low, 42, 40 + low, knock=1)
    bob = v.ell(32, 30.6 + low, 2.9, 2.7)
    part(v, dome, hat, lit=2, dark=2)
    knit_rows(v.f, dome, hat)
    part(v, cuff, hat, lit=1, dark=1, glint=False)
    ribs(v.f, cuff, hat)
    part(v, bob, 'plaster', lit=1, dark=1)
    v.f.put(31, 30 + low, 'plaster_warm', 3)
    v.f.put(32, 30 + low, 'plaster_warm', 3)


def stocking_hat_S(v, hat):
    """A long stocking cap whose tail flops to her right (west) with the bobble at her ear."""
    dome = {p for p in v.ell(32.4, 38.0, 9.2, 6.6) if p[1] <= 37}
    tail = v.poly([(24, 33.5), (31, 31.5), (24.5, 36.5), (20.5, 38.5), (19.5, 36.5)])
    cuff = v.rect(22, 37, 42, 40, knock=1)
    bob = v.ell(18.6, 39.8, 2.7, 2.6)
    part(v, tail, hat, lit=1, dark=1, glint=False)
    part(v, dome, hat, lit=2, dark=2)
    knit_rows(v.f, dome | tail, hat)
    part(v, cuff, hat, lit=1, dark=1, glint=False)
    ribs(v.f, cuff, hat)
    part(v, bob, 'plaster', lit=1, dark=1)


def head_side(v, fur, hat, hat_kind='bobble'):
    e = v.ell(27.4, 40.8, 2.3, 2.2)
    part(v, e, fur, lit=1, dark=1, glint=False)
    v.put(27, 41, fur + '_cool', 1)
    head = v.ell(33.0, 43.0, 8.6, 6.6) | v.ell(35.6, 45.8, 4.6, 3.0)
    part(v, head, fur, lit=2, dark=2)
    fur_tufts(v.f, head, fur, step=(5, 3), phase=0)
    muz = v.ell(40.4, 45.8, 3.8, 2.7)
    part(v, muz, 'plaster', lit=1, dark=2, glint=False, base=2)
    for x in (35, 36, 37, 38):
        v.put(x, 41, fur + '_cool', 2)
    ex = 37
    exs = sorted((v.X(ex), v.X(ex + 1)))
    for x in exs:
        for y in (42, 43):
            v.f.put(x, y, 'ink', 0)
    v.f.put(exs[0], 42, 'plaster', 5)
    # nose at the snout's tip, mouth and one buck tooth
    v.put(43, 44, 'ink', 0)
    v.put(44, 44, 'ink', 0)
    v.put(43, 45, fur + '_cool', 1)
    v.put(41, 46, 'plaster', 1)
    v.put(42, 46, 'plaster', 1)
    v.put(42, 47, 'plaster', 5)
    v.put(41, 47, 'plaster', 2)
    if hat_kind == 'bobble':
        dome = {p for p in v.ell(32.6, 37.6, 9.0, 6.4) if p[1] <= 37}
        cuff = v.rect(24, 37, 41, 40, knock=1)
        bob = v.ell(30.6, 30.8, 2.9, 2.7)
        part(v, dome, hat, lit=2, dark=2)
        knit_rows(v.f, dome, hat)
        part(v, cuff, hat, lit=1, dark=1, glint=False)
        ribs(v.f, cuff, hat)
        part(v, bob, 'plaster', lit=1, dark=2, base=2)
    else:
        dome = {p for p in v.ell(32.6, 38.0, 9.0, 6.6) if p[1] <= 37}
        tail = v.poly([(28, 33), (33, 31.6), (25, 37.5), (20.5, 40.0), (20.0, 37.6)])
        cuff = v.rect(24, 37, 41, 40, knock=1)
        bob = v.ell(19.4, 41.4, 2.7, 2.6)
        part(v, tail, hat, lit=1, dark=1, glint=False)
        part(v, dome, hat, lit=2, dark=2)
        knit_rows(v.f, dome | tail, hat)
        part(v, cuff, hat, lit=1, dark=1, glint=False)
        ribs(v.f, cuff, hat)
        part(v, bob, 'plaster', lit=1, dark=1)
    return head


def straps_S(v, fam):
    for x in (26, 37):
        m = v.rect(x, 48, x + 1, 57)
        for (xx, y) in m:
            v.f.put(xx, y, fam, 3 if xx == x else 1)
        v.f.put(x, 58, fam, 1)
        v.f.put(x + 1, 58, fam, 1)
    for x in range(28, 37):
        v.f.put(x, 52, fam, 2)
    v.f.put(32, 52, 'iron', 4)


# --- the options ------------------------------------------------------------------------
def opt_a(view, fidget=False):
    """Bothy Pack: fur earth, muzzle plaster, berry knit, iron kettle and lantern, timber pack."""
    fur, hat, pack = 'earth', 'berry', 'timber'
    v = View(view)
    if view == 'S':
        # frame posts, the bag between them, the rolled mat across the top
        bag = v.rect(21, 26, 43, 47, knock=2)
        part(v, bag, pack + '_cool', lit=2, dark=2, recess=False)
        flap = v.rect(22, 26, 42, 30, knock=2)
        part(v, flap, pack + '_warm', lit=1, dark=1, glint=False)
        for x in range(23, 42, 4):
            v.put(x, 31, pack, 1)
        for px in (18, 45):
            post = v.rect(px, 24, px + 1, 50)
            for (x, y) in post:
                v.f.put(x, y, pack, 3 if x == px else 1)
            v.f.put(px, 24, pack, 4)
        mat_side(v, 16, 47, 21)
        # the lantern hangs off her right post, the kettle off her left
        lantern(v, 12, 40)
        v.put(17, 38, 'iron', 2)
        v.put(16, 39, 'iron', 2)
        if not fidget:
            kettle(v, 47, 40, spout=1)
            for y in (37, 38):
                v.put(46, y, 'iron', 2)
            v.put(47, 39, 'iron', 2)
        legs_S(v, fur)
        torso_S(v, fur)
        straps_S(v, pack)
        if fidget:
            # her right paw lifts the kettle and tips it towards the mug in her left
            # her left paw unhooks the kettle and tips it over the mug in her right
            head_S(v, fur, hat, eyes='shut')
            arm(v, fur, 22.4, 56.0, 2.7, 4.0)
            cup(v, 19, 57, fam='berry')
            arm(v, fur, 40.6, 51.6, 2.7, 4.6)
            kettle(v, 28, 49, spout=-1, tilt=2, hook=False)
            for y in (55, 56):               # the pour, a thin lit stream into the mug
                v.f.glow(22, y, 'plaster_warm', 4)
            steam(v, [(19, 55, 5), (20, 53, 4)])
        else:
            arm(v, fur, 22.6, 54.2)
            arm(v, fur, 41.4, 54.2)
            head_S(v, fur, hat, eyes='open')
    else:
        # E geometry (W redraws it): the pack rides on her back, to the west
        bag = v.rect(14, 28, 25, 53, knock=2)
        part(v, bag, pack + '_warm', lit=3, dark=2, recess=False)
        flap = v.rect(14, 28, 25, 32, knock=2)
        part(v, flap, pack + '_warm', lit=3, dark=1, glint=False)
        pocket = v.rect(15, 40, 21, 48, knock=1)
        part(v, pocket, pack, lit=1, dark=1, glint=False)
        for y in range(29, 54, 5):
            v.put(25, y, pack, 1)
        post = v.rect(25, 25, 26, 55)
        for (x, y) in post:
            v.f.put(x, y, pack, 3 if x == min(v.X(25), v.X(26)) else 1)
        mat_end(v, 19.6, 24.4, 3.4)
        if view == 'W':
            kettle(v, 13, 43, spout=-1)  # her left side (the kettle's) faces us looking west
            for y in (40, 41, 42):
                v.put(17, y, 'iron', 2)
        if view == 'E':
            lantern(v, 15, 42)           # her right side (the lantern's) faces us looking east
            v.put(17, 40, 'iron', 2)
        tail_side(v, fur)
        legs_side(v, fur)
        torso_side(v, fur)
        # the near strap over her shoulder
        for y in range(47, 58):
            v.put(28, y, pack, 2)
            v.put(29, y, pack, 3 if y < 52 else 2)
        arm_side(v, fur)
        head_side(v, fur, hat)
    despeckle(v.f, v.keep)
    v.f.outline()
    return v.f.image()


def opt_b(view, fidget=False):
    """Kettle Cap: fur timber, muzzle plaster, sky knit, iron kettle, berry daypack."""
    fur, hat, pack = 'timber', 'sky', 'berry'
    v = View(view)
    if view == 'S':
        # the daypack rides high behind her left shoulder, the kettle lashed on top
        bag = v.rect(35, 37, 46, 55, knock=3)
        part(v, bag, pack, lit=2, dark=2, recess=False)
        for y in range(40, 54, 4):
            v.put(45, y, pack + '_cool', 1)
        kettle(v, 37, 29, spout=1)
        # the lashing: two cord loops over the kettle's base
        for x in (38, 44):
            for y in (35, 36):
                v.put(x, y, pack + '_cool', 1)
        legs_S(v, fur)
        torso_S(v, fur, wide=0.4)
        straps_S(v, pack)
        if fidget:
            # both paws up, pulling the cuff down over her ears and eyes
            head_S(v, fur, hat, eyes='open', hat_low=3)
            for cx in (22.6, 41.4):
                arm(v, fur, cx, 45.6, 2.7, 4.6)
        else:
            arm(v, fur, 22.6, 54.2)
            arm(v, fur, 41.4, 54.2)
            head_S(v, fur, hat)
    else:
        bag = v.rect(16, 36, 26, 55, knock=3)
        part(v, bag, pack + '_warm', lit=3, dark=2, recess=False)
        pocket = v.rect(16, 45, 21, 52, knock=1)
        part(v, pocket, pack + '_warm', lit=1, dark=1, glint=False)
        kettle(v, 15, 28, spout=-1)
        for x in (16, 22):
            for y in (34, 35):
                v.put(x, y, pack + '_cool', 1)
        tail_side(v, fur)
        legs_side(v, fur)
        torso_side(v, fur)
        for y in range(46, 58):
            v.put(28, y, pack, 2)
            v.put(29, y, pack, 3 if y < 52 else 2)
        arm_side(v, fur)
        head_side(v, fur, hat)
    despeckle(v.f, v.keep)
    v.f.outline()
    return v.f.image()


def scarf_S(v, knit, stripe):
    collar = v.ell(32, 49.6, 10.2, 3.0)
    part(v, collar, knit, lit=1, dark=1)
    knit_rows(v.f, collar, knit, phase=1)
    tail = v.rect(24, 50, 28, 59, knock=1)
    part(v, tail, knit, lit=1, dark=1, glint=False)
    for y in (53, 54, 57):
        for x in range(25, 28):
            v.f.put(x, y, stripe, 4 if x < 26 else 3)
    for x in (24, 26, 28):
        v.f.put(x, 60, knit, 2)
        v.f.put(x, 61, knit + '_cool', 1)
    return collar | tail


def scarf_side(v, knit, stripe, flutter=0):
    collar = v.ell(32.4, 49.6, 8.4, 3.0)
    part(v, collar, knit, lit=1, dark=1)
    knit_rows(v.f, collar, knit, phase=1)
    tail = v.poly([(23.5, 47.5), (27, 48.5), (22, 55.5 - flutter), (18.5, 54.5 - flutter)])
    part(v, tail, knit, lit=1, dark=1, glint=False)
    for p in ((22, 51), (23, 51), (21, 53), (22, 53)):
        v.put(p[0], p[1], stripe, 3)


def opt_c(view, fidget=False):
    """Hut Warden: fur path, muzzle plaster, berry scarf with sky stripes, sky stocking cap, iron kettle."""
    fur, knit, stripe = 'path', 'berry', 'sky'
    v = View(view)
    if view == 'S':
        legs_S(v, fur)
        torso_S(v, fur, wide=0.6)
        # a belt with the kettle hung at her left hip
        for x in range(23, 42):
            if (x, 58) in v.f.px:
                v.f.put(x, 58, 'iron_cool', 2)
                v.f.put(x, 59, 'iron_cool', 1)
        v.put(33, 58, 'iron', 4)
        if not fidget:
            kettle(v, 40, 55, spout=1)
            arm(v, fur, 22.4, 54.2)
            arm(v, fur, 41.6, 53.0, 2.6, 4.4)
        else:
            kettle(v, 40, 55, spout=1)
        scarf_S(v, knit, stripe)
        if fidget:
            head_S(v, fur, stripe, hat_kind='stocking', eyes='shut', cheeks=0.6)
            arm(v, fur, 26.6, 52.4, 2.6, 3.6)
            arm(v, fur, 37.4, 52.4, 2.6, 3.6)
            cup(v, 29, 50, fam='sky')
            steam(v, [(36, 48, 5), (38, 46, 4), (37, 44, 5)])   # blown aside, past her cheek
        else:
            head_S(v, fur, stripe, hat_kind='stocking')
    else:
        tail_side(v, fur)
        legs_side(v, fur)
        torso_side(v, fur)
        for x in range(22, 42):
            p = (v.X(x), 58)
            if p in v.f.px:
                v.f.put(p[0], 58, 'iron_cool', 2)
                v.f.put(p[0], 59, 'iron_cool', 1)
        if view == 'E':
            kettle(v, 24, 55, spout=1)
        scarf_side(v, knit, stripe)
        arm_side(v, fur)
        head_side(v, fur, stripe, hat_kind='stocking')
        if view == 'W':
            kettle(v, 24, 55, spout=1)
    despeckle(v.f, v.keep)
    v.f.outline()
    return v.f.image()


OPTIONS = [
    {
        'label': 'A', 'name': 'Bothy Pack (a timber-frame rucksack taller than her head)',
        'question': 'The pack is the silhouette: a square frame with the rolled mat as a roof over a round marmot, the kettle on one post and a lit lantern on the other, so she reads as a walking hut.',
        'draw': opt_a,
        'palette': ['earth', 'plaster', 'berry', 'iron', 'timber'],
        'pose': 'Feet planted under a load twice her size and smiling about it; the fidget unhooks the kettle and pours a cup for whoever is near.',
        'parts': [
            'mat: plaster_cool, layer 0 (back), changes S/E/W (side roll vs end disc), on back (pack top)',
            'pack frame + bag + flap: timber, layer 1, changes S/E/W, on back (chest anchor, bobs 1 px late in walk)',
            'lantern: iron + lamp glow, layer 2, on her right post: shows in S and E, hidden in W; swings 1 px after each step',
            'kettle: iron, layer 2, on her left post: shows in S and W, hidden in E; to her left paw in fidget and cast',
            'tail: earth_cool, layer 3, E/W only, on hip (flicks in walk and hit)',
            'legs x2: earth_cool, layer 4, all facings, on foot (6-frame walk swing, tuck in nap)',
            'torso + belly: earth, layer 5, all facings, on hip (breath 1 px)',
            'straps + chest strap: timber, layer 6, S (two) / E-W (near one), on chest',
            'arms x2: earth, paws earth_cool, layer 7, on chest (swing in walk; wind-up/strike/guard/cheer)',
            'ears x2: earth, layer 8, under hat cuff, on head',
            'head + cheeks + muzzle + face: earth/plaster/ink, layer 9, all facings, on head (blink, sleep eyes)',
            'bobble hat (dome, cuff, bobble): berry + plaster bobble, layer 10, on head (bobble lags in hop)',
        ],
        'notes': [
            'Works: the only folk with a roofline; the frame reads at 2 device px as "she carries the hut".',
            'Risk: 40 px wide with the mat, the widest folk; the pack must stay on in nap (she naps against it) and the fight poses need it trimmed.',
            'Compared: Eastward-04 market crop (John, Sam, Masao, 28-34 art px): John\'s pack is a few big 3-4 tone shapes with one strap line; matched that, kept the frame posts 2 px.',
        ],
    },
    {
        'label': 'B', 'name': 'Kettle Cap (a daypack with the kettle riding on top)',
        'question': 'A compact pack carried high on her left shoulder, the kettle lashed on top so it rides beside the bobble like a second hat: a two-bump crown, lopsided on purpose.',
        'draw': opt_b,
        'palette': ['timber', 'plaster', 'sky', 'iron', 'berry'],
        'pose': 'Round, a little lopsided under the kettle, chin up; the fidget pulls the sky cuff down over her ears and eyes against the cold.',
        'parts': [
            'daypack: berry, layer 0, changes S (behind left shoulder) / E-W (on back), on back',
            'kettle: iron, layer 1, rides on the pack top (back anchor, wobbles 1 px after a hop), to hand in cast',
            'tail: timber_cool, layer 2, E/W only, on hip',
            'legs x2: timber_cool, layer 3, all facings, on foot',
            'torso + belly: timber, layer 4, on hip (breath)',
            'straps + chest strap: berry, layer 5, on chest',
            'arms x2: timber, paws timber_cool, layer 6, on chest (raised to the cuff in fidget)',
            'ears x2: timber, layer 7, on head',
            'head + muzzle + face: timber/plaster/ink, layer 8, on head',
            'bobble hat: sky, plaster bobble, layer 9, on head (cuff slides 3 px in fidget)',
        ],
        'notes': [
            'Works: two bumps at the top (bobble, kettle) are her own crown; the kettle stays in view in every facing.',
            'Risk: the asymmetry makes S lopsided and the kettle could read as a second head at 2 device px.',
            'Compared: Eastward-04 (John carries a satchel high and slung, a single big lit shape): same economy.',
        ],
    },
    {
        'label': 'C', 'name': 'Hut Warden (scarf, stocking cap, kettle at the hip)',
        'question': 'No pack: a thick berry scarf makes broad shoulders, a long stocking cap flops its bobble to one side, and the kettle hangs from a belt at her hip, so she reads low and wide like a hut stove.',
        'draw': opt_c,
        'palette': ['path', 'plaster', 'berry', 'sky', 'iron'],
        'pose': 'Settled and low, scarf up to the chin; the fidget lifts an enamel mug in both paws and blows on it, eyes shut.',
        'parts': [
            'tail: path_cool, layer 0, E/W only, on hip',
            'legs x2: path_cool, layer 1, all facings, on foot',
            'torso + belly: path, layer 2, on hip (breath)',
            'belt: iron_cool, layer 3, on hip',
            'kettle: iron, layer 4 (S, E) / 6 (W, the far hip shown in front of the near arm), on hip; swings opposite the walk',
            'scarf collar + tail: berry with sky stripes, layer 5, changes S/E/W, on chest (tail trails in walk and hit)',
            'arms x2: path, paws path_cool, layer 6, on chest (hold the mug in fidget and cast)',
            'ears x2: path, layer 7, on head',
            'head + muzzle + face: path/plaster/ink, layer 8, on head (puffed cheeks in fidget)',
            'stocking cap + flopped bobble: sky, plaster bobble, layer 9, on head (bobble swings in walk)',
        ],
        'notes': [
            'Works: the warmest read, and the lightest rig (no pack to re-time); the flopped bobble is her mark.',
            'Risk: without a pack she loses the "carries the bothy" idea and nears Tally (knit, small, round).',
            'Compared: Eastward-04 Masao (scarf-like collar, big round face): collar as one 3-tone band, not stripes everywhere.',
        ],
    },
]

VIEWS = [('S idle', 'S', False), ('E idle', 'E', False), ('W idle', 'W', False), ('S fidget', 'S', True)]


def gates(m):
    return {
        'on_house': m.get('on_house', 0) >= 0.999,
        'west_east': m.get('west_east', 0) > 0,
        'lone': m.get('isolated', 1) <= 0.06,
        'colours': m.get('colours', 999) <= 64,
        'outline_dark': m.get('outline_dark', 0) >= 0.95,
    }


# =======================================================================================
# Final: "Bothy Keeper" (revision round, 21 Oct). Chosen C, without the hut-warden name or
# the stocking cap: a short leaf-green knit bobble beanie with ear flaps (rib columns) and a
# leaf-green chunky scarf. Grafts from A: a low rolled mat strapped across the small of her
# back, and the dented iron kettle at her left hip with a lit sheen.
#
# Fixed anchors (every facing, every pose):
#   kettle   her LEFT hip, at the back: S viewer's right, behind the body in E (far side),
#            in front of the body in W (near side)
#   mat      across the small of her back: both ends show in S, its end disc in E and W
#   scarf    collar at the chest; its tail hangs on her RIGHT chest: S viewer's left, in
#            front in E (near side), hidden behind her in W
#   familiar the shoulder away from the foe: E pose west (x smaller), W pose east
# =======================================================================================
FUR, KNIT, MUZ, METAL, STRAP = 'path', 'leaf', 'plaster', 'iron', 'timber'
FAM = 'grass'   # the stand-in Mossling


def ribbed(fig, mask, fam, phase=0):
    """Knit as rib columns: 2 px columns alternating with a recessed column a tone down,
    over the part's own form shading (never a checker)."""
    for (x, y) in mask:
        if ((x + phase) // 2) % 2:
            f, t = fig.px[(x, y)]
            if sk.family_of(f) == fam:
                fig.put(x, y, fam, max(1, t - 1))


def fur_clumps(fig, mask, fam, phase=0):
    """Fur as directional tufts that follow the form: 3 px downward strokes (a vertical
    domino with a foot that leans away from the light), one tone down in the body, the
    sibling at the same tone on the lit cap. Never single dots."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    if not xs:
        return
    cx = (min(xs) + max(xs) + 1) / 2
    row = 0
    for y in range(min(ys) + 2, max(ys) - 1, 4):
        off = (row + phase) % 2 * 3
        for x in range(min(xs) + 2 + off, max(xs) - 1, 6):
            lean = 1 if x + 0.5 >= cx else -1
            shape = [(x, y), (x, y + 1), (x + lean, y + 1)]
            cur = [fig.px.get(p) for p in shape]
            if any(c is None or c[0] != fam for c in cur):
                continue
            t = cur[0][1]
            if any(c[1] != t for c in cur) or t < 2:
                continue
            nt = t - 1 if t in (3, 2) else t
            nf = fam if t in (3, 2) else fam + '_warm'
            for p in shape:
                fig.put(p[0], p[1], nf, nt)
        row += 1


def limb(v, x0, y0, x1, y1, w=2.4):
    """A fur limb from shoulder (x0, y0) to paw (x1, y1), as a quad of half-width w."""
    import math
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / n * w, dx / n * w
    return v.poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])


def arm_to(v, x0, y0, x1, y1, far=False, w=2.4):
    """An arm with its paw: the far arm in the cool sibling a tone down (it is in the
    body's shade), the paw a darker mitten."""
    fam = FUR + '_cool' if far else FUR
    m = limb(v, x0, y0, x1, y1, w) | v.ell(x1 + 0.5, y1 + 0.5, 2.3, 2.1)
    part(v, m, fam, lit=1, dark=1, glint=False, base=2 if far else 3)
    paw = v.ell(x1 + 0.5, y1 + 0.5, 2.0, 1.8)
    for p in paw:
        if p in m:
            f, t = v.f.px[p]
            v.f.put(p[0], p[1], FUR + '_cool', min(t, 2))
    return m


def kettle_hip(v, x, y):
    """The dented iron kettle hung from the belt by its bail: 9 x 7 with a lit sheen."""
    kettle(v, x, y, spout=1)


def mossling(v, cx, by, curled=False):
    """Stand-in familiar: a round leaf-green blob with a sprout and two ink eyes, 24 art px
    tall standing (sprout included); feet centre at (cx, by)."""
    if curled:
        body = v.ell(cx, by - 4.4, 6.4, 4.6)
        part(v, body, FAM, lit=2, dark=2)
        sprout = v.ell(cx - 4.4, by - 8.4, 2.0, 1.2)
        part(v, sprout, FAM + '_warm', glint=False, lit=1, dark=1, deep=False)
        for dx in (-3, -2, 1, 2):
            v.put(int(cx) + dx, by - 5, FAM, 1)
        return
    body = v.ell(cx, by - 8.6, 7.4, 8.6)
    part(v, body, FAM, lit=2, dark=2)
    stalk = v.rect(int(cx), by - 20, int(cx), by - 17)
    for (x, y) in stalk:
        v.f.put(x, y, FAM, 2)
    for lx, ly in ((cx - 2.2, by - 20.8), (cx + 2.4, by - 21.6)):
        leaf_m = v.ell(lx, ly, 2.4, 1.4)
        part(v, leaf_m, FAM + '_warm', glint=False, lit=1, dark=1, deep=False, recess=False)
    ex = int(cx - 0.5)
    for e in (ex - 3, ex + 2):
        v.put(e, by - 11, 'ink', 0)
        v.put(e, by - 10, 'ink', 0)
    v.put(ex - 3, by - 11, 'plaster', 5) if not v.m else v.put(ex + 2, by - 11, 'plaster', 5)
    v.keep.update({(v.X(ex - 3), by - 11), (v.X(ex + 2), by - 11)})


# --- S facing ---------------------------------------------------------------------------
def beanie_S(v, oy=0, low=0):
    bob = v.ell(32, 32.3 + oy, 2.8, 2.6)
    dome = {p for p in v.ell(32, 38.2 + oy, 9.4, 6.0) if p[1] <= 37 + oy}
    cuff = v.rect(22, 37 + oy + low, 42, 40 + oy + low, knock=1)
    flaps = [v.rect(21, 39 + oy + low, 24, 46 + oy, knock=1), v.rect(40, 39 + oy + low, 43, 46 + oy, knock=1)]
    part(v, dome, KNIT, lit=2, dark=2)
    ribbed(v.f, dome, KNIT)
    for fl in flaps:
        part(v, fl, KNIT, lit=1, dark=1, glint=False)
        ribbed(v.f, fl, KNIT, phase=1)
    part(v, cuff, KNIT, lit=1, dark=1, glint=False)
    ribbed(v.f, cuff, KNIT, phase=1)
    for x in range(22, 43):     # the cuff's fold: a recessed row under the dome
        if (x, 37 + oy + low) in v.f.px and v.f.px[(x, 37 + oy + low)][0] == KNIT:
            v.f.put(x, 37 + oy + low, KNIT, 2)
    part(v, bob, MUZ, lit=1, dark=1)
    # flap ties: two short cords under each flap
    for x in (22, 42):
        v.f.put(x, 47 + oy, KNIT, 1)
        v.f.put(x, 48 + oy, KNIT, 1)


def face_S(v, oy=0, eyes='open', cheeks=0.0):
    head = v.ell(32, 43.0 + oy, 9.4, 6.4) | v.ell(26.2, 45.6 + oy, 4.2 + cheeks, 3.0) | \
        v.ell(37.8, 45.6 + oy, 4.2 + cheeks, 3.0)
    part(v, head, FUR, lit=2, dark=2)
    fur_clumps(v.f, head, FUR, phase=1)
    muz = v.ell(32, 46.6 + oy, 4.6, 2.8)
    part(v, muz, MUZ, lit=1, dark=1, glint=False)
    # brows: a lit ridge over each eye, the socket a tone down beneath
    for x in (26, 27, 28, 29, 34, 35, 36, 37):
        v.f.put(x, 41 + oy, FUR, 4 if x < 32 else 3)
    for ex in (27, 35):
        if eyes == 'open':
            for p in ((ex, 42), (ex + 1, 42), (ex, 43), (ex + 1, 43)):
                v.f.put(p[0], p[1] + oy, 'ink', 0)
            v.f.put(ex, 42 + oy, MUZ, 5)
            v.keep.add((ex, 42 + oy))
        else:   # shut: a soft downward arc
            for p in ((ex - 1, 42), (ex, 43), (ex + 1, 43), (ex + 2, 42)):
                v.f.put(p[0], p[1] + oy, 'ink', 0)
    for p in ((31, 44), (32, 44)):
        v.f.put(p[0], p[1] + oy, 'ink', 0)
    for p in ((31, 45), (32, 45)):
        v.f.put(p[0], p[1] + oy, MUZ, 2)
    for p in ((30, 46), (33, 46)):
        v.f.put(p[0], p[1] + oy, MUZ, 1)
    v.f.put(31, 47 + oy, MUZ, 5)
    v.f.put(32, 47 + oy, MUZ, 4)
    v.keep.update({(31, 47 + oy), (32, 47 + oy)})
    return head


MAT = 'plaster_cool'   # a felt roll


def mat_S(v, y=55):
    """The rolled felt mat across the small of her back: its two ends show past her hips."""
    m = v.rect(15, y, 49, y + 4, knock=1)
    for (x, yy) in m:
        v.f.put(x, yy, MAT, {0: 3, 1: 3, 2: 2, 3: 2, 4: 1}[yy - y])
    for xx in (15, 49):  # the rolled end: a darker face with its spiral turn
        for yy in range(y + 1, y + 4):
            if (xx, yy) in v.f.px:
                v.f.put(xx, yy, MAT, 1)
    v.f.put(16, y + 2, MAT, 0)
    v.f.put(16, y + 3, MAT, 0)
    for tx in (18, 46):
        for yy in range(y, y + 5):
            v.f.put(tx, yy, STRAP, 2 if yy == y else 1)


def belt_S(v, y=58):
    for x in range(21, 44):
        if (x, y) in v.f.px:
            v.f.put(x, y, STRAP, 3 if x < 30 else 2)
            if (x, y + 1) in v.f.px:
                v.f.put(x, y + 1, STRAP, 1)
    v.f.put(32, y, METAL, 4)
    v.f.put(33, y, METAL, 3)


def scarf_final_S(v, oy=0):
    collar = v.ell(32, 49.4 + oy, 10.6, 2.9)
    part(v, collar, KNIT, lit=1, dark=1)
    ribbed(v.f, collar, KNIT)
    tail = v.rect(24, 50 + oy, 28, 58 + oy, knock=1)
    part(v, tail, KNIT, lit=1, dark=1, glint=False)
    for y in range(51 + oy, 58 + oy):   # chunky rows of 2 px loops down the tail
        if (y - oy) % 2:
            for x in (25, 26):
                f, t = v.f.px[(x, y)]
                v.f.put(x, y, KNIT, max(1, t - 1))
    for x in (24, 25, 27, 28):
        v.f.put(x, 59 + oy, KNIT, 2)


def tam_S(fidget=False):
    v = View('S')
    mat_S(v)
    legs_S(v, FUR)
    torso = v.ell(32, 54.6, 10.8, 8.3)
    part(v, torso, FUR, lit=2, dark=2, recess=False)
    belly = v.ell(32, 57.4, 5.2, 4.0)
    for p in belly:
        f, t = v.f.px[p]
        if f == FUR and t == 3:
            v.f.put(p[0], p[1], FUR + '_warm', 4)
    fur_clumps(v.f, torso, FUR)
    belt_S(v)
    # the kettle on its bail from the belt at her left hip
    kettle_hip(v, 41, 57)
    if fidget:
        face_S(v, eyes='shut', cheeks=0.6)
        beanie_S(v)
        scarf_final_S(v)
        arm_to(v, 24.0, 50.0, 28.0, 52.0)
        arm_to(v, 40.0, 50.0, 36.0, 52.0)
        cup(v, 29, 49, fam=METAL)
        for (x, y, t) in ((36, 47, 5), (38, 45, 5), (37, 43, 5)):   # steam, blown aside
            for q in ((x, y), (x, y - 1)):
                v.f.glow(q[0], q[1], MUZ, t)
    else:
        scarf_final_S(v)
        arm_to(v, 22.4, 50.0, 20.8, 57.4)
        arm_to(v, 41.6, 50.0, 43.2, 57.4)
        face_S(v)
        beanie_S(v)
    despeckle(v.f, v.keep, rounds=3, glints=False)
    v.f.outline()
    return v


# --- side facings (E geometry; W redraws it) -------------------------------------------
POSES = {
    #          body dx, dy, head dx, dy, legs (back, front), near arm, far arm, eyes, perch
    'idle':   dict(dx=0, dy=0, hx=0, hy=0, legs=((29.0, 62.8), (34.6, 62.8)),
                   near=(32.6, 49.6, 34.6, 58.0), far=None, eyes='open'),
    'ready':  dict(dx=0, dy=1, hx=0, hy=0, legs=((27.4, 62.8), (36.6, 62.8)),
                   near=(33.0, 50.0, 38.4, 54.0), far=(31.0, 49.6, 36.6, 52.4), eyes='open'),
    'strike': dict(dx=2, dy=1, hx=1, hy=0, legs=((25.6, 62.8), (38.4, 62.8)),
                   near=(34.6, 50.0, 47.0, 50.4), far=(31.0, 50.0, 26.0, 55.4), eyes='open'),
    'cast':   dict(dx=0, dy=0, hx=0, hy=0, legs=((28.4, 62.8), (35.4, 62.8)),
                   near=(33.4, 50.0, 41.0, 47.0), far=(31.4, 49.4, 39.6, 45.0), eyes='open', glow=True),
    'hit':    dict(dx=-2, dy=0, hx=-1, hy=1, legs=((27.4, 62.8), (33.6, 62.2)),
                   near=(30.0, 49.6, 25.4, 54.4), far=(30.0, 49.0, 35.0, 46.0), eyes='squeeze'),
    'sit':    dict(dx=0, dy=3, hx=0, hy=0, legs='sit',
                   near=(32.6, 52.0, 37.0, 59.0), far=None, eyes='shut'),
    'cheer':  dict(dx=0, dy=-2, hx=0, hy=0, legs=((29.4, 61.2), (34.6, 61.2)),
                   near=(33.0, 48.0, 36.4, 38.0), far=(31.0, 47.6, 28.6, 38.4), eyes='happy'),
}


def face_side(v, ox, oy, eyes):
    """The profile as forms: skull, a cheek jowl, a snout that steps forward, a lit brow."""
    head = v.ell(33.0 + ox, 43.0 + oy, 8.4, 6.4)
    part(v, head, FUR, lit=2, dark=2)
    fur_clumps(v.f, head, FUR)
    cheek = v.ell(35.0 + ox, 46.4 + oy, 4.0, 2.7)
    part(v, cheek, FUR, lit=1, dark=1, glint=False)
    snout = v.ell(40.6 + ox, 45.4 + oy, 3.6, 2.5)
    part(v, snout, MUZ, lit=1, dark=2, glint=False)
    jaw = v.ell(40.0 + ox, 47.6 + oy, 2.4, 1.2)
    part(v, jaw, MUZ, lit=1, dark=1, glint=False, base=2, recess=False)
    # the brow: a lit ridge stepping out over the eye
    for x in (35, 36, 37, 38, 39):
        v.put(x + ox, 41 + oy, FUR, 4)
    v.put(39 + ox, 42 + oy, FUR, 2)
    e0 = 37 + ox
    xs = sorted((v.X(e0), v.X(e0 + 1)))
    if eyes == 'open':
        for x in xs:
            for y in (42, 43):
                v.f.put(x, y + oy, 'ink', 0)
        v.f.put(xs[0], 42 + oy, MUZ, 5)
        v.keep.add((xs[0], 42 + oy))
    elif eyes == 'happy':      # ^
        v.put(e0, 43 + oy, 'ink', 0)
        v.put(e0 + 1, 42 + oy, 'ink', 0)
        v.put(e0 + 2, 43 + oy, 'ink', 0)
    elif eyes == 'squeeze':    # >
        v.put(e0, 42 + oy, 'ink', 0)
        v.put(e0 + 1, 43 + oy, 'ink', 0)
        v.put(e0, 44 + oy, 'ink', 0)
    else:                      # shut, a soft arc
        v.put(e0 - 1, 42 + oy, 'ink', 0)
        v.put(e0, 43 + oy, 'ink', 0)
        v.put(e0 + 1, 43 + oy, 'ink', 0)
    v.put(43 + ox, 44 + oy, 'ink', 0)
    v.put(44 + ox, 44 + oy, 'ink', 0)
    v.put(41 + ox, 46 + oy, MUZ, 1)
    v.put(42 + ox, 46 + oy, MUZ, 1)
    v.put(42 + ox, 47 + oy, MUZ, 5)
    v.keep.add((v.X(42 + ox), 47 + oy))
    return head


def beanie_side(v, ox, oy):
    bob = v.ell(31.6 + ox, 32.3 + oy, 2.8, 2.6)
    dome = {p for p in v.ell(32.6 + ox, 38.2 + oy, 8.8, 6.0) if p[1] <= 37 + oy}
    cuff = v.rect(24 + ox, 37 + oy, 41 + ox, 40 + oy, knock=1)
    flap = v.rect(27 + ox, 39 + oy, 31 + ox, 46 + oy, knock=1)
    part(v, dome, KNIT, lit=2, dark=2)
    ribbed(v.f, dome, KNIT)
    part(v, flap, KNIT, lit=1, dark=1, glint=False)
    ribbed(v.f, flap, KNIT, phase=1)
    part(v, cuff, KNIT, lit=1, dark=1, glint=False)
    ribbed(v.f, cuff, KNIT, phase=1)
    for x in range(24 + ox, 42 + ox):
        p = (v.X(x), 37 + oy)
        if p in v.f.px and v.f.px[p][0] == KNIT:
            v.f.put(p[0], p[1], KNIT, 2)
    v.put(29 + ox, 47 + oy, KNIT, 1)
    v.put(29 + ox, 48 + oy, KNIT, 1)
    part(v, bob, MUZ, lit=1, dark=2, base=3)


def tam_side(facing, pose='idle'):
    P = POSES[pose]
    v = View(facing)
    dx, dy = P['dx'], P['dy']
    hx, hy = dx + P['hx'], dy + P['hy']
    fight = pose != 'idle'
    perch = None
    # the familiar sits on the shoulder away from the foe (west in E geometry), behind her
    if fight:
        perch = (int(round(22.6 + dx)), 48 + dy)
        mossling(v, 22.6 + dx, 48 + dy)
    # far side first: in E the kettle (her left hip) is behind her
    if facing == 'E':
        kettle_hip(v, 15 + dx, min(56 + dy, 57))
    if P.get('far'):
        x0, y0, x1, y1 = P['far']
        arm_to(v, x0 + dx, y0 + dy, x1 + dx, y1 + dy, far=True)
    # tail and the mat's end disc at the small of her back
    tail = v.ell(22.6 + dx, 59.4 + dy, 2.8, 3.2) | v.ell(21.6 + dx, 62.0 + dy, 2.2, 1.8)
    if pose == 'sit':
        tail = v.ell(21.6 + dx, 62.6, 3.2, 2.2)
    part(v, tail, FUR + '_cool', lit=1, dark=1, glint=False)
    # legs
    if P['legs'] == 'sit':
        for lx, base in ((35.6, 2), (37.4, 3)):
            m = v.ell(lx, 63.6, 3.6, 2.2)
            part(v, m, FUR + '_cool', lit=1, dark=1, glint=False, base=base)
    else:
        (bx, by), (fx, fy) = P['legs']
        back = v.ell(bx, by + min(0, dy), 3.0, 2.8)
        part(v, back, FUR + '_cool', lit=2, dark=1, glint=False)
        front = v.ell(fx, fy + min(0, dy), 3.3, 2.9) | v.rect(int(fx), int(fy + min(0, dy)) + 1, int(fx) + 3, int(fy + min(0, dy)) + 2)
        part(v, front, FUR + '_cool', lit=1, dark=1, glint=False)
    torso = v.ell(31.6 + dx, 54.6 + dy, 9.6, 8.3)
    if pose == 'sit':
        torso = v.ell(31.6 + dx, 57.4, 9.8, 7.4)
    part(v, torso, FUR, lit=2, dark=2, recess=False)
    belly = v.ell(37.0 + dx, 56.6 + dy, 3.6, 4.4)
    for p in belly:
        if p in torso and v.f.px[p][0] == FUR:
            v.f.put(p[0], p[1], FUR + '_warm', v.f.px[p][1])
    fur_clumps(v.f, torso, FUR, phase=1)
    # the mat, end on, strapped across the small of her back
    mat_end(v, 21.4 + dx, 55.4 + dy, 3.2, fam=MAT, base=2)
    for y in range(52 + dy, 59 + dy):
        v.put(23 + dx, y, STRAP, 1)
    # belt
    by_ = 58 + dy if pose != 'sit' else 59 + dy - 2
    for x in range(20 + dx, 42 + dx):
        p = (v.X(x), by_)
        if p in v.f.px and v.f.px[p][0].startswith(FUR):
            v.f.put(p[0], by_, STRAP, 2)
            q = (p[0], by_ + 1)
            if q in v.f.px and v.f.px[q][0].startswith(FUR):
                v.f.put(q[0], q[1], STRAP, 1)
    # near side: in W the kettle (her left hip) hangs in front
    if facing == 'W':
        kettle_hip(v, 15 + dx, min(56 + dy, 57))
    # scarf collar; its tail hangs on her right chest, the near side only in E
    collar = v.ell(32.6 + dx, 49.6 + dy, 8.6, 2.9)
    part(v, collar, KNIT, lit=1, dark=1)
    ribbed(v.f, collar, KNIT)
    if facing == 'E':
        sway = {'strike': -2, 'hit': 2, 'cheer': -1}.get(pose, 0)
        tail_s = v.poly([(33.5 + dx, 50.5 + dy), (37.5 + dx, 50.5 + dy), (37.5 + dx + sway, 57.5 + dy),
                         (33.5 + dx + sway, 57.5 + dy)])
        part(v, tail_s, KNIT, lit=1, dark=1, glint=False)
        for y in range(52 + dy, 57 + dy, 2):
            v.put(35 + dx + (sway if y > 54 + dy else 0), y, KNIT, 1)
            v.put(36 + dx + (sway if y > 54 + dy else 0), y, KNIT, 1)
    face_side(v, hx, hy, P['eyes'])
    beanie_side(v, hx, hy)
    x0, y0, x1, y1 = P['near']
    arm_to(v, x0 + dx, y0 + dy, x1 + dx, y1 + dy)
    if P.get('glow'):
        # Warmth gathered in her paws: a small lamp glow, a light source
        for (x, y, t) in ((44, 45, 5), (45, 45, 4), (44, 44, 4), (45, 46, 3), (44, 46, 4), (43, 45, 3)):
            v.f.glow(v.X(x + dx), y + dy, 'lamp', t)
    despeckle(v.f, v.keep, rounds=3, glints=False)
    v.f.outline()
    if perch and v.m:
        perch = (63 - perch[0], perch[1])
    v.perch = perch
    return v


def tam_nap():
    """nap_c: curled up facing S, the mat as her pillow, the familiar curled at her belly."""
    v = View('S')
    # the mat unrolled a little under her head
    mat = v.rect(13, 60, 30, 64, knock=1)
    for (x, y) in mat:
        v.f.put(x, y, MUZ + '_cool', {60: 4, 61: 3, 62: 3, 63: 2, 64: 1}[y])
    body = v.ell(33.6, 58.6, 12.4, 7.0)
    part(v, body, FUR, lit=2, dark=2, recess=False)
    fur_clumps(v.f, body, FUR)
    tail = v.ell(44.6, 62.4, 4.4, 2.6)
    part(v, tail, FUR + '_cool', lit=1, dark=1, glint=False)
    paw = v.ell(30.6, 63.2, 3.0, 1.8)
    part(v, paw, FUR + '_cool', lit=1, dark=1, glint=False)
    # the kettle at her left hip, now on the far side of the curl, peeking above her back
    # (layer under the body would hide it: it lies against her hip, lid up)
    belt = [(x, 56) for x in range(27, 44)]
    for p in belt:
        if p in v.f.px:
            v.f.put(p[0], p[1], STRAP, 2)
    # head down on the mat, eyes shut, hat on
    head = v.ell(22.6, 57.6, 7.4, 5.4) | v.ell(23.6, 60.2, 4.0, 2.4)
    part(v, head, FUR, lit=2, dark=2)
    muz = v.ell(22.6, 60.4, 3.6, 2.0)
    part(v, muz, MUZ, lit=1, dark=1, glint=False)
    for p in ((19, 57), (20, 58), (21, 58), (24, 57), (25, 58), (26, 58)):
        pass
    for ex in (18, 25):
        v.f.put(ex, 57, 'ink', 0)
        v.f.put(ex + 1, 58, 'ink', 0)
        v.f.put(ex + 2, 58, 'ink', 0)
    v.f.put(22, 59, 'ink', 0)
    v.f.put(23, 59, 'ink', 0)
    dome = {p for p in v.ell(22.6, 54.6, 7.6, 4.8) if p[1] <= 54}
    cuff = v.rect(15, 54, 30, 56, knock=1)
    part(v, dome, KNIT, lit=2, dark=2)
    ribbed(v.f, dome, KNIT)
    part(v, cuff, KNIT, lit=1, dark=1, glint=False)
    ribbed(v.f, cuff, KNIT, phase=1)
    bob = v.ell(21.6, 49.6, 2.6, 2.4)
    part(v, bob, MUZ, lit=1, dark=1)
    scarf = v.ell(31.0, 59.6, 3.0, 4.4)
    part(v, scarf, KNIT, lit=1, dark=1, glint=False)
    ribbed(v.f, scarf, KNIT)
    # the familiar curled against her belly
    mossling(v, 37.6, 66, curled=True)
    despeckle(v.f, v.keep, rounds=3, glints=False)
    v.f.outline()
    return v


FINAL = {
    'label': 'C final', 'name': 'Bothy Keeper (knit beanie with ear flaps, scarf, kettle at the hip, mat at the back)',
    'chosen': 'C',
    'grafts': ['from A: a low rolled sleeping mat strapped across the small of her back (says "she carries the bothy" without blocking the shoulder perch)',
               'from A: the dented iron kettle with a lit sheen, hung at her left hip'],
    'dropped': ['the hut-warden name (the Frostline\'s ring rival)', 'the stocking cap with a flopped bobble (Puffcap/Mote)', 'sky knit (Bramble\'s accent)'],
    'palette': ['path', 'plaster', 'leaf', 'iron', 'timber'],
    'pose': 'Stout, square on her feet, scarf to the chin: dependable. The fidget lifts a tin mug in both paws and blows across it, eyes shut.',
    'parts': [
        'familiar perch: grass Mossling (stand-in), layer 0 in fight poses, on chest (the shoulder away from the foe)',
        'kettle: iron, anchor left hip (belt, back); layer 1 in E (far side, behind), 9 in W (near side, front), 3 in S (viewer right)',
        'far arm: path_cool, layer 2, on chest (E/W fight poses only)',
        'tail: path_cool, layer 3, on hip (E/W; wraps in nap)',
        'legs x2: path_cool, layer 4, on foot (S, E, W; sit pushes them forward)',
        'mat: plaster_cool (felt) + timber ties, layer 0 in S (behind, both ends) / 6 in E-W (end disc on her back), anchor hip-back; pillow in nap',
        'torso + belly: path / path_warm, layer 5, on hip (breath 1 px)',
        'belt: timber, layer 7, on hip (kettle hangs from it)',
        'scarf collar: leaf ribs, layer 8, on chest; tail: leaf, her right chest (S viewer left, E front, W hidden), sways in strike/hit',
        'head + cheek + snout + brow: path / plaster / ink, layer 10, on head (blink, shut, happy, squeeze eyes)',
        'beanie dome + cuff + ear flaps + bobble: leaf ribs, plaster bobble, layer 11, on head (bobble lags 1 px in hop)',
        'near arm: path, paw path_cool, layer 12, on chest (ready, strike reach, cast, hit, cheer)',
    ],
    'notes': [
        'Works: round, low and stout; the green beanie with flaps plus the scarf is her own knit set; the kettle and mat say "keeper of the bothy" from every side.',
        'Fixed anchors: kettle left hip, scarf tail right chest, mat small of back, so W shows the kettle and hides the tail, E the reverse.',
        'Risk: the Mossling (24 px) on a 38 px folk is large; it sits behind her head on the back shoulder and the perch anchor is recorded per pose.',
        'Compared: Eastward-04 crop (John, Sam, Masao at 28-34 art px): Masao\'s round head and collar, John\'s low slung kit as a few big 3-4 tone shapes.',
        'Nap: the mat unrolls as her pillow and the kettle lies against her far hip (hidden by the curl); the Mossling curls at her belly.',
    ],
}

FINAL_VIEWS = [
    ('S idle', lambda: tam_S()), ('E idle', lambda: tam_side('E')), ('W idle', lambda: tam_side('W')),
    ('S fidget', lambda: tam_S(True)), ('nap S', lambda: tam_nap()),
    ('E ready', lambda: tam_side('E', 'ready')), ('E strike', lambda: tam_side('E', 'strike')),
    ('E cast', lambda: tam_side('E', 'cast')), ('E hit', lambda: tam_side('E', 'hit')),
    ('E sit', lambda: tam_side('E', 'sit')), ('E cheer', lambda: tam_side('E', 'cheer')),
    ('W ready', lambda: tam_side('W', 'ready')), ('W strike', lambda: tam_side('W', 'strike')),
]


def gates_final(m):
    g = gates(m)
    g['lone'] = m.get('isolated', 1) <= 0.04
    return g


def final():
    views, stats, perches = [], {}, {}
    ok = True
    for cap, fn in FINAL_VIEWS:
        v = fn()
        img = v.f.image()
        views.append((cap, img))
        img.save(os.path.join(SCRATCH, f"final-{cap.replace(' ', '-')}.png"))
        m = sk.measure(img)
        bb = img.getbbox()
        g = gates_final(m)
        ok &= all(g.values())
        st = {k: (round(x, 4) if isinstance(x, float) else x) for k, x in m.items()}
        st['bbox'] = list(bb)
        st['height_px'] = bb[3] - bb[1]
        stats[cap] = st
        if getattr(v, 'perch', None):
            perches[cap] = list(v.perch)
        print(f"final {cap:9s} on_house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:3d}  outline_dark "
              f"{100 * m.get('outline_dark', 0):5.1f}%  h {bb[3] - bb[1]}  bbox {bb}  "
              f"{'PASS' if all(g.values()) else 'FAIL ' + str([k for k, x in g.items() if not x])}")
    opt = {k: FINAL[k] for k in ('label', 'name', 'parts', 'palette', 'pose', 'notes')}
    opt['views'] = views
    sk.design_sheet('Tam, the Bothy Keeper (final): knit beanie, scarf, kettle at the hip, mat at the back',
                    [opt], OUT_FINAL,
                    note='38 art px tall (bbox incl. outline), cell 64 x 72, foot (32, 66). W drawn, not mirrored. '
                         'Familiar: stand-in 24 px Mossling on the shoulder away from the foe.')
    with open(OUT_JSON) as fh:
        data = json.load(fh)
    data['final'] = {k: FINAL[k] for k in ('label', 'name', 'chosen', 'grafts', 'dropped', 'parts', 'palette',
                                           'pose', 'notes')} | {'perch_anchor': perches, 'measure': stats}
    with open(OUT_JSON, 'w') as fh:
        json.dump(data, fh, indent=2)
    print('final: all gates pass' if ok else 'final: SOME GATES FAIL')
    print(OUT_FINAL)


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    sheet_opts = []
    data = {'id': 'tam', 'name': 'Tam', 'cell': [64, 72], 'anchor': [32, 66], 'height_art_px': 38,
            'question': 'the rucksack and kettle silhouette against a round marmot body', 'options': []}
    ok_all = True
    for opt in OPTIONS:
        views = []
        stats = {}
        for cap, facing, fid in VIEWS:
            img = opt['draw'](facing, fid)
            views.append((cap, img))
            img.save(os.path.join(SCRATCH, f"{opt['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(img)
            g = gates(m)
            ok_all &= all(g.values())
            stats[cap] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
            print(f"{opt['label']} {cap:9s} on_house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:3d}  "
                  f"outline_dark {100 * m.get('outline_dark', 0):5.1f}%  {'PASS' if all(g.values()) else 'FAIL ' + str([k for k, x in g.items() if not x])}")
        sheet_opts.append({k: opt[k] for k in ('label', 'name', 'parts', 'palette', 'pose', 'notes')} | {'views': views})
        data['options'].append({k: opt[k] for k in ('label', 'name', 'question', 'parts', 'palette', 'pose', 'notes')}
                               | {'measure': stats})
    sk.design_sheet('Tam, marmot-folk of the Frostline: rucksack and kettle against a round body',
                    sheet_opts, OUT_PNG,
                    note='38 art px tall, cell 64 x 72, foot (32, 66). W drawn, not mirrored. Game scale row: 2 device px a texel.')
    with open(OUT_JSON, 'w') as fh:
        json.dump(data, fh, indent=2)
    print('all gates pass' if ok_all else 'SOME GATES FAIL')
    print(OUT_PNG)
    final()


if __name__ == '__main__':
    main()
