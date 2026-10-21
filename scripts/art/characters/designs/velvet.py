"""Velvet design options (Claude J folk sheets, 21 Oct).

Velvet, moth-folk keeper of the Driftwood lighthouse: dusk wings worn as a cloak and a
shuttered lamp that "keeps the night dark for the sleepers". 46 art px tall, cell 64 x 72,
foot anchor (32, 66). Main question: how the wings work as a cloak and where the
shuttered lamp lives.

    A  Hooded wing-cloak: wings folded round her into a hood, plumes out of the hood,
       the lamp held low in both paws in the cloak's parting.
    B  Eye-spot capelet and crook: bare fluffy head, a short scalloped cape of wing lobes
       with eye-spots, the lamp hung from a tall crook pole.
    C  Ruff and swallowtail coat: a high fur ruff, wings closed into a long belted coat
       that ends in two luna-moth tails, the lamp hung at the hip.

Every view is drawn in E space and mirrored as geometry for W, then shaded afresh with
the light from the upper left, so W keeps its lit side on the left (never a mirrored image).

    python3 scripts/art/characters/designs/velvet.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
import style_lint  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_DIR = os.path.join(ROOT, 'docs', 'vision', 'characters', 'designs')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.char-views')), 'velvet')

W_, H_ = 64, 72
N4 = sk.N4


# --- drawing helpers -------------------------------------------------------------------
class D:
    """One view being drawn. Masks are given in E space (or S space) and mirrored for W."""

    def __init__(self, facing: str):
        self.f = sk.Fig(W_, H_)
        self.w = facing == 'W'
        self.keep: set = set()

    def m(self, mask):
        return {(64 - x, y) for x, y in mask} if self.w else set(mask)

    def X(self, x):
        return 64 - x if self.w else x

    def ell(self, cx, cy, rx, ry):
        return self.m(self.f.ellipse(cx, cy, rx, ry))

    def poly(self, pts):
        return self.m(self.f.poly(pts))

    def rect(self, x0, y0, x1, y1, knock=0):
        return self.m(self.f.rect(x0, y0, x1, y1, knock))

    def part(self, mask, fam, soft=0.0, deep=True, glint=None):
        """Shade a screen-space mask; glint is a 2 px horizontal pair at its top-left."""
        self.f.shade(mask, fam, glint=False, deep=deep, soft=soft)
        if glint:
            gx, gy = glint
            gx = self.X(gx) - (1 if self.w else 0)
            for p in ((gx, gy), (gx + 1, gy)):
                if p in mask:
                    self.f.put(p[0], p[1], fam, 5)
                    self.keep.add(p)
        return mask

    def put(self, x, y, fam, tone, keep=False):
        x = self.X(x)
        self.f.put(x, y, fam, tone)
        if keep:
            self.keep.add((x, y))

    def glow(self, x, y, tone):
        self.f.glow(self.X(x), y, 'lamp', tone)

    def tone_at(self, p):
        v = self.f.px.get(p)
        return v

    def recolor(self, mask, fam, fn):
        """Repaint pixels of `mask` that already belong to `fam`'s family via fn(tone)."""
        base = sk.family_of(fam)
        for p in mask:
            v = self.f.px.get(p)
            if v and v[0] not in ('ink',) and sk.family_of(v[0]) == base and not str(v[0]).startswith('_'):
                self.f.px[p] = (v[0], max(0, min(5, fn(v[1], p))))


def folds(d: D, mask, cols, y0, y1, fam):
    """Cloth folds as vertical bands: a dark 1 px crease with a lit ridge on its left.
    cols are in E space; the lit ridge is always on the screen-left."""
    for c in cols:
        x = d.X(c)
        for y in range(y0, y1 + 1):
            p = (x, y)
            if p in mask and d.f.px.get(p, ('', 0))[0] == fam:
                t = d.f.px[p][1]
                d.f.px[p] = (fam, max(1, t - 1) if t >= 2 else t)
                q = (x - 1, y)
                if q in mask and d.f.px.get(q, ('', 0))[0] == fam and d.f.px[q][1] in (2, 3):
                    d.f.px[q] = (fam, d.f.px[q][1] + 1)


def tufts(d: D, mask, fam, dark=True, lit=True, step=(4, 3)):
    """Fur as clumped tufts: small V clusters, dark on the shaded body, light on the lit cap."""
    mask = set(mask)
    if dark:
        sub = {p for p in mask if d.f.px.get(p, ('', 0)) == (fam, 3) and
               (p[0] + 1, p[1]) in mask and (p[0], p[1] + 1) in mask}
        d.f.clusters(sub, fam, 2, [(0, 0), (1, 1)], step)
    if lit:
        sub = {p for p in mask if d.f.px.get(p, ('', 0)) in ((fam, 3), (fam, 4))}
        d.f.clusters(sub, fam, 4, [(0, 0), (1, 0)], (step[0] + 1, step[1] + 1))


def ring_inside(d: D, mask, fam, tone, side='top'):
    """A row of one tone along the inside top (or bottom) edge of a mask."""
    for (x, y) in mask:
        if side == 'top' and (x, y - 1) not in mask:
            d.f.px[(x, y)] = (fam, tone)
        if side == 'bottom' and (x, y + 1) not in mask:
            d.f.px[(x, y)] = (fam, tone)


def seam(d: D, inner, outer, fam):
    """A dark interior line where one part sits against another (never ink): the outer
    part's pixels touching the inner part drop to tone 1 (tone 2 on the lit upper left)."""
    cx = sum(p[0] for p in inner) / len(inner)
    cy = sum(p[1] for p in inner) / len(inner)
    for (x, y) in outer:
        if (x, y) in inner:
            continue
        if any((x + dx, y + dy) in inner for dx, dy in N4):
            lit = (x < cx - 2 and y < cy) or y < cy - 4
            d.f.px[(x, y)] = (fam, 2 if lit else 1)


def despeckle(fig: sk.Fig, keep: set):
    for _ in range(3):
        changed = 0
        for p, (fam, t) in list(fig.px.items()):
            if p in keep or fam == 'ink' or p in fig.fixed or str(fam).startswith('_'):
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n == (fam, t) for n in nb):
                continue
            same = [n[1] for n in nb if n and n[0] == fam]
            if not same:
                continue
            tone = Counter(same).most_common(1)[0][0]
            fig.px[p] = (fam, tone)
            changed += 1
        if not changed:
            break


def eye(d: D, x, y, h=4, closed=False, lidfam='plaster'):
    """A big round moth eye, 3 wide and 4 tall with the corners off, ink with a
    one-pixel glint on its upper left. x is the eye's left column in E space."""
    if closed:
        for dx in range(4):
            d.put(x + dx, y + 2, 'ink', 0)
            d.put(x + dx, y + 1, lidfam, 2)
        return
    shape = [(1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3)]
    for dx, dy in shape:
        d.put(x + dx, y + dy, 'ink', 0)
    gx = min(d.X(x + 1), d.X(x + 2))
    d.f.put(gx, y + 1, 'snow', 5)
    d.keep.add((gx, y + 1))


def west_lit(d: D, mask, width=2, east=1):
    """West faces 3 to 4, east faces 1 to 2: lift the first `width` px of each row of a
    part from tone 3 to 4 and drop the last `east` px from 3 to 2 (screen space)."""
    rows = {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        xs.sort()
        for x in xs[:width]:
            v = d.f.px.get((x, y))
            if v and v[0] != 'ink' and v[1] == 3:
                d.f.px[(x, y)] = (v[0], 4)
        for x in xs[-east:] if east else []:
            v = d.f.px.get((x, y))
            if v and v[0] != 'ink' and v[1] == 3:
                d.f.px[(x, y)] = (v[0], 2)


def profile_shade(d: D, mask, width=2):
    """In E and W the face's forward planes face the side: the last `width` px of each
    row (screen east) step down to tone 2 at most, the first stays lit."""
    rows = {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        xs.sort()
        for x in xs[-width:]:
            v = d.f.px.get((x, y))
            if v and v[0] != 'ink' and v[1] >= 3:
                d.f.px[(x, y)] = (v[0], 2)


def line4(a, b):
    """A 4-connected line (no diagonal-only steps, so a shaft is never a row of specks)."""
    (x0, y0), (x1, y1) = a, b
    pts = [(x0, y0)]
    n = max(abs(x1 - x0), abs(y1 - y0))
    px, py = x0, y0
    for i in range(1, n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        if x != px and y != py:
            pts.append((x, py))
        pts.append((x, y))
        px, py = x, y
    return pts


def lantern(d: D, cx, top, glow_len=3, glow_tone=3, cap='brass', body='iron'):
    """A shuttered lamp, 7 wide: finial, cap, louvred iron body with a 1 px glowing slit,
    base. cx is its centre column (E space). Returns the bottom row."""
    x0, x1 = cx - 3, cx + 3
    fin = d.rect(cx - 1, top, cx + 1, top + 1, knock=1)
    d.part(fin, cap)
    capm = d.rect(x0, top + 2, x1, top + 3, knock=1)
    d.part(capm, cap, glint=(x0 + 1, top + 2))
    bod = d.rect(x0 + 0, top + 4, x1, top + 10)
    d.part(bod, body, soft=0.1)
    # louvres: shutter slats as dark rows with a lit lip above
    for yy in (top + 6, top + 8):
        for xx in range(x0 + 1, x1):
            p = (d.X(xx), yy)
            if p in bod:
                d.f.px[p] = (body, 1)
    for yy in (top + 5, top + 7, top + 9):
        for xx in range(x0 + 1, x1):
            p = (d.X(xx), yy)
            if p in bod and d.f.px[p][1] >= 2:
                d.f.px[p] = (body, min(4, d.f.px[p][1] + 1) if xx < cx else d.f.px[p][1])
    # the shutter is nearly closed: a sliver of light
    if glow_len:
        g0 = top + 7 - glow_len // 2
        for yy in range(g0, g0 + glow_len):
            d.glow(cx, yy, glow_tone)
    base = d.rect(x0, top + 11, x1, top + 12, knock=1)
    d.part(base, cap)
    return top + 12


def plume(d: D, pts, fam='plaster', stem=None):
    """A feathery (bipectinate) antenna: a slim stalk from the head, then a leaf-shaped
    vane up to 2 px either side of a darker shaft, the upper edge notched into barbs.
    Upper (lit) vane tone 4, lower vane 3, shaft 2; the tip curls outward and down."""
    import math
    base = ((pts[0][0] + pts[-1][0]) // 2, (pts[0][1] + pts[-1][1]) // 2)
    tip = ((pts[2][0] + pts[3][0]) // 2, pts[2][1])
    shaft = line4(base, tip)
    n = len(shaft)
    steep = abs(tip[1] - base[1]) > abs(tip[0] - base[0])
    vane = {}
    for i, (x, y) in enumerate(shaft):
        t = i / max(1, n - 1)
        if t <= 0.22:
            continue
        up = (x - 1, y) if steep else (x, y - 1)
        dn = (x + 1, y) if steep else (x, y + 1)
        vane.setdefault(up, 4)
        if t < 0.9:
            vane.setdefault(dn, 3)
        # comb teeth: barbs stand out every other pixel on both edges; the outline
        # fills the notches between them, so the antenna reads as a feather, not an ear
        if 0.3 < t < 0.9 and i % 2 == 0:
            vane.setdefault((x - 2, y) if steep else (x, y - 2), 4)
            if t < 0.8:
                vane.setdefault((x + 2, y) if steep else (x, y + 2), 3)
    for (x, y), t in vane.items():
        d.put(x, y, fam, t)
    for i, (x, y) in enumerate(shaft):
        d.put(x, y, fam, 2 if i / max(1, n - 1) > 0.18 else 1)
    tx, ty = tip
    sx = 1 if tx > base[0] else -1
    d.put(tx + sx, ty, fam, 2)
    d.put(tx + sx, ty + 1, fam, 2)
    return set(shaft) | set(vane)


def feather(d: D, base, tip, fam='plaster'):
    return plume(d, [base, base, tip, tip, base], fam)


def finish(d: D):
    despeckle(d.f, d.keep)
    d.f.outline()
    return d.f.image()


# --- option A: hooded wing-cloak, lamp held low in both paws ---------------------------
def a_south(fidget=False):
    d = D('S')
    # feet
    for x0 in (27, 34):
        d.part(d.rect(x0, 63, x0 + 3, 66, knock=1), 'iron')
    # plumes behind the hood
    # cloak: the folded wings, a bell from the shoulders to a scalloped hem
    cloak = d.poly([(24, 37), (41, 37), (44, 47), (46, 57), (46, 64), (19, 64), (19, 57), (21, 47)])
    cloak -= {(x, 63) for x in range(19, 47) if (x - 19) % 5 == 2}
    cloak -= {(x, 62) for x in range(19, 47) if (x - 19) % 5 == 2 and x in (19, 46)}
    d.part(cloak, 'dusk', soft=0.15)
    west_lit(d, cloak, 2, 1)
    folds(d, cloak, (23, 27, 38, 42), 44, 62, 'dusk')
    # the wing margin: a pale scalloped band above the hem (dusk_warm)
    for x in range(20, 46):
        yb = 59 + (1 if (x - 19) % 5 in (1, 2, 3) else 0)
        for yy in (yb, yb + 1):
            if (x, yy) in cloak:
                d.f.px[(x, yy)] = ('dusk_warm', 4 if x < 33 else 3)
    # the wings part at the front where the paws come out: a deep lining
    if fidget:
        part_m = d.ell(32.5, 47.5, 6.5, 6) & cloak
    else:
        part_m = d.ell(32.5, 55.5, 7, 6.5) & cloak
    for p in part_m:
        d.f.px[p] = ('dusk_cool', 1 if p[0] < 33 else 0)
    ring_inside(d, part_m, 'dusk_cool', 2, 'top')
    # overlap seam: the left wing lies over the right
    seam_top, seam_bot = (37, 41) if fidget else (40, 49)
    for y in range(seam_top + 1, seam_bot + 1):
        d.f.px[(32, y)] = ('dusk', 4)
        d.f.px[(33, y)] = ('dusk', 1)
    for y in range(62 if not fidget else 54, 64):
        if (32, y) in cloak:
            d.f.px[(32, y)] = ('dusk', 4)
            d.f.px[(33, y)] = ('dusk', 1)
    if fidget:
        for y in range(54, 62):
            d.f.px[(32, y)] = ('dusk', 4)
            d.f.px[(33, y)] = ('dusk', 1)
    # hood: the wings' upper lobes drawn up round the head
    hood = d.ell(32.5, 31, 10.5, 8.5) | d.poly([(29, 24), (36, 24), (32.5, 22)])
    d.part(hood, 'dusk', soft=0.1, glint=(26, 25))
    west_lit(d, hood, 2, 1)
    face = d.ell(32.5, 32.5, 6.5, 6)
    rim = {(x, y) for (x, y) in hood if any((x + dx, y + dy) in face for dx in (-1, 0, 1) for dy in (-1, 0, 1))} - face
    for (x, y) in rim:
        d.f.px[(x, y)] = ('dusk', 4 if (x < 31 or y < 28) else 2)
    d.part(face, 'plaster', soft=0.25)
    ring_inside(d, face, 'plaster', 2, 'top')       # the hood's shadow on the brow
    for (x, y) in face:
        if (x, y - 1) in face and (x, y - 2) not in face and x > 30:
            d.f.px[(x, y)] = ('plaster', 2)
    # chin fluff spilling over the cloak
    fluff = d.ell(32.5, 39.5, 5, 2.5) | d.rect(29, 41, 30, 42) | d.rect(34, 41, 35, 42)
    d.part(fluff, 'plaster', soft=0.2)
    tufts(d, fluff, 'plaster', lit=False, step=(3, 2))
    # eyes
    eye(d, 27, 32, closed=fidget)
    eye(d, 35, 32, closed=fidget)
    # plumes rise from the brow and arch out over the hood
    sl = 2 if fidget else 0
    feather(d, (30, 28), (23, 21 + sl))
    feather(d, (35, 28), (42, 21 + sl))
    # lamp and paws
    if fidget:
        lantern(d, 32, 42, glow_len=1, glow_tone=2)
        # right paw on the finial, turning the shutter down; left paw under the base
        d.part(d.ell(35.5, 42.5, 2, 1.8), 'plaster', soft=0.2)
        d.part(d.ell(29, 53.5, 2.2, 1.6), 'plaster', soft=0.2)
    else:
        lantern(d, 32, 49)
        d.part(d.ell(28, 56, 2, 2), 'plaster', soft=0.2)
        d.part(d.ell(37, 56, 2, 2), 'plaster', soft=0.2)
    return finish(d)


def a_side(facing):
    d = D(facing)
    # feet: back foot, then front foot a step ahead
    d.part(d.rect(27, 63, 30, 66, knock=1), 'iron')
    d.part(d.rect(34, 63, 38, 66, knock=1), 'iron')
    # far plume behind the hood
    # cloak bell, the trailing wing sweeping back
    cloak = d.poly([(26, 37), (39, 37), (42, 47), (43, 57), (42, 64), (19, 64), (20, 57), (23, 46)])
    cloak -= d.m({(x, 63) for x in range(19, 43) if (x - 19) % 5 == 2})
    d.part(cloak, 'dusk', soft=0.15)
    west_lit(d, cloak, 3, 1)
    folds(d, cloak, (24, 28, 32), 44, 62, 'dusk')
    for x in range(19, 43):
        yb = 59 + (1 if (x - 19) % 5 in (1, 2, 3) else 0)
        for yy in (yb, yb + 1):
            p = (d.X(x), yy)
            if p in cloak:
                d.f.px[p] = ('dusk_warm', 4 if p[0] < 31 else 3)
    part_m = d.ell(39.5, 55.5, 4, 6) & cloak
    for p in part_m:
        d.f.px[p] = ('dusk_cool', 1)
    ring_inside(d, part_m, 'dusk_cool', 2, 'top')
    # hood with a wing-tip point trailing back
    hood = d.ell(32, 31, 9.5, 8.5) | d.poly([(26, 26), (19, 33), (21, 35), (27, 36)])
    d.part(hood, 'dusk', soft=0.1, glint=(26, 25))
    west_lit(d, hood, 4, 0)
    feather(d, (35, 27), (30, 21), 'plaster_cool')   # far plume, over the hood's crown
    face = d.ell(37.5, 32.5, 4.5, 5.5)
    face |= d.ell(41, 35, 1.6, 1.6)   # fluffy cheek forward
    face &= d.m({(x, y) for x in range(0, 43) for y in range(0, 72)})
    rim = {(x, y) for (x, y) in hood if any((x + dx, y + dy) in face for dx in (-1, 0, 1) for dy in (-1, 0, 1))} - face
    for p in rim:
        d.f.px[p] = ('dusk', 4 if p[1] < 28 or (not d.w and False) else 2)
    d.part(face, 'plaster', soft=0.25)
    ring_inside(d, face, 'plaster', 2, 'top')
    profile_shade(d, face, 2)
    fluff = d.ell(37, 39.5, 4, 2.5) | d.rect(36, 41, 37, 42)
    d.part(fluff, 'plaster', soft=0.2)
    tufts(d, fluff, 'plaster', lit=False, step=(3, 2))
    eye(d, 38, 31)
    # near plume over the hood
    feather(d, (37, 27), (43, 21))
    # lamp low in front, held in both paws
    lantern(d, 41, 49)
    d.part(d.ell(37.5, 56, 2, 2), 'plaster', soft=0.2)
    return finish(d)


# --- option B: eye-spot capelet, lamp on a crook pole ----------------------------------
def b_south(fidget=False):
    d = D('S')
    # legs and feet
    for x0 in (28, 35):
        d.part(d.rect(x0 + 1, 61, x0 + 2, 63), 'iron')
        d.part(d.rect(x0, 63, x0 + 3, 66, knock=1), 'iron')
    # robe: the moth's body in a long dusk_cool shift
    robe = d.poly([(27, 41), (38, 41), (40, 51), (42, 62), (23, 62), (25, 51)])
    d.part(robe, 'dusk_cool', soft=0.1)
    west_lit(d, robe, 2, 1)
    folds(d, robe, (27, 31, 35, 39), 50, 61, 'dusk_cool')
    # capelet: fore and hind wing lobes over each shoulder
    if fidget:
        lobes = [((22, 40.5, 8.5, 6), (24, 48.5, 6, 4)), ((43, 41.5, 7, 5.5), (41, 48.5, 5, 3.5))]
    else:
        lobes = [((26, 43.5, 6.5, 6.5), (27, 50, 4.5, 3.5)), ((39, 43.5, 6.5, 6.5), (38, 50, 4.5, 3.5))]
    for side, (fore, hind) in enumerate(lobes):
        hm = d.ell(*hind) & {(x, y) for x in range(64) for y in range(38, 72)}
        d.part(hm, 'dusk_warm', soft=0.1)
        fm = d.ell(*fore) & {(x, y) for x in range(64) for y in range(37, 72)}
        d.part(fm, 'dusk', soft=0.1, glint=(fore[0] - 3, int(fore[1] - fore[3]) + 2) if side == 0 else None)
        # the wing margin: a scalloped pale rim along the bottom of the forewing
        ring_inside(d, fm, 'dusk_warm', 4 if side == 0 else 3, 'bottom')
        # eye-spot: a cream ring round a deep dusk pupil
        sx, sy = fore[0] + (-1 if side == 0 else 1), fore[1] + 0.5
        spot = d.ell(sx, sy, 2.2, 2.2)
        for p in spot:
            d.f.px[p] = ('plaster', 4 if p[0] < sx else 3)
        for p in d.ell(sx, sy, 1.1, 1.1):
            d.f.px[p] = ('dusk', 0)
    # ruff collar
    ruff = d.ell(32.5, 38.5, 8.5, 3) | d.rect(25, 40, 26, 41) | d.rect(29, 41, 30, 42) \
        | d.rect(34, 41, 35, 42) | d.rect(38, 40, 39, 41)
    d.part(ruff, 'plaster', soft=0.2)
    tufts(d, ruff, 'plaster', lit=False, step=(3, 2))
    # head: a round fluffy cream head with a crown tuft
    head = d.ell(32.5, 30, 7.5, 7.5)
    d.part(head, 'plaster', soft=0.15, glint=(28, 24))
    tufts(d, head, 'plaster', lit=False, step=(4, 3))
    # plumes: dusk feathers sweeping up and out from the crown
    feather(d, (30, 25), (23, 21), 'dusk_warm')
    feather(d, (35, 25), (42, 21), 'dusk_warm')
    eye(d, 27, 29, closed=fidget)
    eye(d, 34, 29, closed=fidget)
    d.put(31, 35, 'plaster', 2)
    d.put(32, 35, 'plaster', 2)
    # crook (in her left paw): a timber pole with the shuttered lamp hung from its hook
    pole = d.rect(46, 25, 47, 66)
    hook = d.rect(46, 22, 49, 23) | d.rect(50, 23, 51, 25) | d.rect(46, 24, 47, 24)
    d.part(pole, 'timber', soft=0.1)
    d.part(hook, 'timber', glint=(46, 22))
    for y in (34, 35, 52, 53):   # lashing rings round the pole
        d.put(46, y, 'timber', 2)
        d.put(47, y, 'timber', 1)
    d.part(d.rect(51, 26, 51, 27), 'brass')
    lantern(d, 51, 28, glow_len=1 if fidget else 3, glow_tone=2 if fidget else 3)
    d.part(d.rect(44, 45, 48, 48, knock=1), 'plaster', soft=0.2)   # paw on the pole
    if fidget:
        d.part(d.rect(15, 42, 18, 45, knock=1), 'plaster', soft=0.2)  # paw smoothing the wing
    else:
        d.part(d.rect(29, 46, 32, 48, knock=1), 'plaster', soft=0.2)  # paw at rest on the shift
    return finish(d)


def b_side(facing):
    d = D(facing)
    d.part(d.rect(29, 61, 30, 63), 'iron')
    d.part(d.rect(35, 61, 36, 63), 'iron')
    d.part(d.rect(27, 63, 30, 66, knock=1), 'iron')
    d.part(d.rect(34, 63, 38, 66, knock=1), 'iron')
    # far wing lobe peeking behind
    d.part(d.ell(24, 45, 4, 5.5), 'dusk_cool', soft=0.1)
    robe = d.poly([(28, 41), (37, 41), (39, 51), (41, 62), (24, 62), (26, 51)])
    d.part(robe, 'dusk_cool', soft=0.1)
    west_lit(d, robe, 2, 1)
    folds(d, robe, (28, 32, 36), 50, 61, 'dusk_cool')
    hm = d.ell(29, 50, 5, 3.5)
    d.part(hm, 'dusk_warm', soft=0.1)
    fm = d.ell(31, 44, 7, 6.5) & {(x, y) for x in range(64) for y in range(37, 72)}
    d.part(fm, 'dusk', soft=0.1, glint=(27, 39))
    west_lit(d, fm, 2, 1)
    ring_inside(d, fm, 'dusk_warm', 4, 'bottom')
    for p in d.ell(30, 44.5, 2.2, 2.2):
        d.f.px[p] = ('plaster', 4 if p[0] < 30 + (1 if d.w else 0) else 3)
    for p in d.ell(30, 44.5, 1.1, 1.1):
        d.f.px[p] = ('dusk', 0)
    ruff = d.ell(33.5, 38.5, 7, 3) | d.rect(30, 40, 31, 41) | d.rect(35, 40, 36, 41) | d.rect(39, 39, 40, 40)
    d.part(ruff, 'plaster', soft=0.2)
    tufts(d, ruff, 'plaster', lit=False, step=(3, 2))
    feather(d, (32, 25), (27, 21), 'dusk_cool')
    head = d.ell(33.5, 30, 7.5, 7.5) | d.ell(40.5, 33, 1.8, 2)
    d.part(head, 'plaster', soft=0.15, glint=(29, 24))
    profile_shade(d, head, 2)
    tufts(d, head, 'plaster', lit=False, step=(4, 3))
    feather(d, (36, 25), (42, 21), 'dusk_warm')
    eye(d, 37, 29)
    if not d.w:
        # E: crook held forward in the near paw; the lamp hangs ahead at face height
        pole = d.rect(45, 25, 46, 66)
        hook = d.rect(45, 22, 48, 23) | d.rect(49, 23, 50, 25) | d.rect(45, 24, 46, 24)
        lamp_x, paw = 50, d.rect(43, 45, 47, 48, knock=1)
    else:
        # W: the crook is in her left paw, now the near side, planted at the hip; its
        # hook turns back so the shuttered lamp trails behind her and the way ahead stays dark
        pole = d.rect(23, 25, 24, 66)
        hook = d.rect(20, 22, 24, 23) | d.rect(18, 23, 19, 25)
        lamp_x, paw = 18, d.rect(21, 45, 25, 48, knock=1)
    d.part(pole, 'timber', soft=0.1)
    d.part(hook, 'timber', glint=(46, 22) if not d.w else (23, 22))
    px0 = min(x for x, _ in pole)
    for y in (34, 35, 52, 53):
        d.f.put(px0, y, 'timber', 2)
        d.f.put(px0 + 1, y, 'timber', 1)
    d.part(d.rect(lamp_x, 26, lamp_x, 27), 'brass')
    lantern(d, lamp_x, 28)
    d.part(paw, 'plaster', soft=0.2)
    return finish(d)


# --- option C: high ruff, wings closed into a long swallowtail coat, lamp at the hip --
def c_south(fidget=False):
    d = D('S')
    for x0 in (28, 33):
        d.part(d.rect(x0, 63, x0 + 3, 66, knock=1), 'iron')
    # swallowtails: the hindwings' tails trail to the ground either side
    d.part(d.poly([(23, 55), (29, 62), (20, 67), (20, 64)]), 'dusk_warm', soft=0.1)
    d.part(d.poly([(42, 55), (36, 62), (45, 67), (45, 64)]), 'dusk_warm', soft=0.1)
    coat = d.poly([(26, 40), (39, 40), (41, 51), (42, 63), (23, 63), (24, 51)])
    d.part(coat, 'dusk', soft=0.15)
    west_lit(d, coat, 2, 1)
    folds(d, coat, (26, 29, 37, 40), 50, 62, 'dusk')
    # front edges: the two wing margins meet down the middle, pale chevrons on each
    for y in range(41, 63):
        d.f.px[(32, y)] = ('dusk', 0 if y > 49 else 1)
        if (y - 41) % 4 in (0, 1):
            d.f.px[(30, y)] = ('dusk_warm', 4)
            d.f.px[(31, y)] = ('dusk_warm', 4)
            d.f.px[(33, y)] = ('dusk_warm', 3)
            d.f.px[(34, y)] = ('dusk_warm', 3)
    # belt
    for x in range(24, 42):
        if (x, 48) in coat:
            d.f.px[(x, 48)] = ('brass', 3 if x < 33 else 2)
            d.f.px[(x, 49)] = ('brass', 1)
    for p in ((31, 48), (32, 48), (31, 49), (32, 49)):
        d.f.px[p] = ('brass', 4 if p[1] == 48 else 3)
    # high collar standing behind the head
    collar = d.ell(32.5, 33, 10.5, 6.5)
    d.part(collar, 'snow_cool', soft=0.1)
    for p in collar:      # the collar's inside, behind the head, sits in shade
        if d.f.px[p][1] >= 3:
            d.f.px[p] = ('snow_cool', d.f.px[p][1] - 1)
    tufts(d, collar, 'snow_cool', lit=False, step=(3, 2))
    hy = 31 if fidget else 30
    head = d.ell(32.5, hy, 6.5, 6.5)
    d.part(head, 'plaster', soft=0.15, glint=(28, hy - 5))
    seam(d, head, collar, 'snow_cool')
    eye(d, 27, hy - 1, closed=fidget)
    eye(d, 34, hy - 1, closed=fidget)
    sl = 2 if fidget else 0
    feather(d, (30, hy - 4), (23, 21 + sl))
    feather(d, (35, hy - 4), (42, 21 + sl))
    # front ruff: a big scalloped fur collar
    ruff = d.ell(32.5, 39.5, 11.5, 3.5)
    for x in range(21, 45, 4):
        ruff |= d.rect(x + 1, 42, x + 2, 43)
    d.part(ruff, 'snow', soft=0.2, glint=(23, 37))
    west_lit(d, ruff, 2, 1)
    tufts(d, ruff, 'snow', lit=False, step=(3, 2))
    for (x, y) in head:   # the chin's shadow on the ruff
        for yy in (y + 1, y + 2):
            if (x, yy) in ruff and (x, yy) not in head:
                d.f.px[(x, yy)] = ('snow', 1 if yy == y + 1 else 2)
    if fidget:
        # both paws raise the lamp to the chest and close the shutter
        lantern(d, 32, 43, glow_len=1, glow_tone=2)
        d.part(d.ell(28.5, 49.5, 2, 1.8), 'plaster', soft=0.2)
        d.part(d.ell(35.5, 44.5, 2, 1.8), 'plaster', soft=0.2)
    else:
        # lamp hung at the hip on a short brass chain
        d.part(d.rect(23, 49, 23, 50), 'brass')
        lantern(d, 23, 51)
        d.part(d.ell(37.5, 50.5, 2, 1.8), 'plaster', soft=0.2)
        d.part(d.ell(26.5, 47.5, 2, 1.8), 'plaster', soft=0.2)
    return finish(d)


def c_side(facing):
    d = D(facing)
    d.part(d.rect(27, 63, 30, 66, knock=1), 'iron')
    d.part(d.rect(34, 63, 38, 66, knock=1), 'iron')
    d.part(d.poly([(26, 54), (31, 62), (18, 67), (18, 64)]), 'dusk_warm', soft=0.1)
    coat = d.poly([(27, 40), (38, 40), (40, 51), (41, 63), (23, 63), (24, 51)])
    d.part(coat, 'dusk', soft=0.15)
    west_lit(d, coat, 3, 1)
    folds(d, coat, (27, 31), 50, 62, 'dusk')
    for y in range(41, 63):
        p = (d.X(37), y)
        if p in coat:
            d.f.px[p] = ('dusk', 1)
        if (y - 41) % 4 in (0, 1):
            for xx in (38, 39):
                q = (d.X(xx), y)
                if q in coat:
                    d.f.px[q] = ('dusk_warm', 3)
    d.part(d.poly([(38, 56), (42, 67), (37, 64)]), 'dusk_warm', soft=0.1)
    for x in range(23, 42):
        p = (d.X(x), 48)
        if p in coat:
            d.f.px[p] = ('brass', 3 if p[0] < 32 else 2)
            d.f.px[(p[0], 49)] = ('brass', 1)
    collar = d.ell(30.5, 33, 8.5, 6.5)
    d.part(collar, 'snow_cool', soft=0.1)
    west_lit(d, collar, 2, 0)
    tufts(d, collar, 'snow_cool', lit=False, step=(3, 2))
    feather(d, (32, 26), (27, 21), 'plaster_cool')
    head = d.ell(34, 30, 6.5, 6.5)
    d.part(head, 'plaster', soft=0.15, glint=(30, 25))
    profile_shade(d, head, 2)
    seam(d, head, collar, 'snow_cool')
    eye(d, 36, 29)
    feather(d, (36, 26), (42, 21))
    ruff = d.ell(33, 39.5, 9.5, 3.5)
    for x in range(24, 43, 4):
        ruff |= d.rect(x + 1, 42, x + 2, 43)
    d.part(ruff, 'snow', soft=0.2, glint=(26, 37))
    west_lit(d, ruff, 3, 1)
    tufts(d, ruff, 'snow', lit=False, step=(3, 2))
    for (x, y) in head:
        for yy in (y + 1, y + 2):
            if (x, yy) in ruff and (x, yy) not in head:
                d.f.px[(x, yy)] = ('snow', 1 if yy == y + 1 else 2)
    d.part(d.rect(34, 49, 34, 50), 'brass')
    lantern(d, 34, 51)
    d.part(d.ell(38.5, 50.5, 2, 1.8), 'plaster', soft=0.2)
    return finish(d)


# --- the sheet -------------------------------------------------------------------------
OPTIONS = [
    {
        'label': 'A', 'name': 'Hooded wing-cloak, lamp held low',
        'question': 'Wings folded round her into a hooded cloak with the plumes out of the hood; '
                    'the shuttered lamp is held low in both paws where the wings part.',
        'views': [('S idle', a_south), ('E idle', lambda: a_side('E')),
                  ('W idle', lambda: a_side('W')), ('S fidget', lambda: a_south(True))],
        'palette': ['dusk', 'plaster', 'iron', 'brass', 'lamp'],
        'pose': 'Still and hushed, lamp carried low like a candle at a bedside; she never hurries.',
        'parts': [
            'feet: iron, layer 1, change S/E/W, attach foot (walk swings them under the hem)',
            'plume far: plaster_cool, layer 6, E/W only (over the hood crown), attach head',
            'cloak (folded wings): dusk + dusk_warm margin, layer 3, S/E/W, attach chest; hem sways in walk, wraps her in nap',
            'cloak parting/lining: dusk_cool, layer 4, S/E/W, attach chest (opens wider for cast)',
            'hood: dusk, layer 5, S/E/W, attach head (falls back for victory)',
            'face: plaster, layer 6, S/E/W, attach head; eyes ink (blink/sleep anchor)',
            'chin fluff: plaster, layer 7, S/E/W, attach chest (breath lifts it 1 px)',
            'plume near: plaster, layer 8, S/E/W, attach head (droops for nap, perks for react)',
            'paws: plaster, layer 9, S/E/W, attach hand (strike = lamp swung out, guard = lamp raised)',
            'lamp: iron + brass + lamp glow, layer 10, S/E/W, attach hand (glow slit 3 px, 1 px when dimmed)',
        ],
        'notes': [
            'Works: the calmest read, a dark bell with two pale plumes; the lamp glints low where the wings part.',
            'Risk: closest to a generic hooded mage; the arms live inside the cloak so walk swing is only paws and hem.',
            "Compared with Eastward's John (eastward-02, scaled to 46 px): 4 tones a material, cloth in fold bands, dark gaps at joints.",
        ],
    },
    {
        'label': 'B', 'name': 'Eye-spot capelet, lamp on a crook',
        'question': 'Wings as a short scalloped capelet of fore and hind lobes with eye-spots; '
                    'the shuttered lamp hangs from a tall crook pole at head height.',
        'views': [('S idle', b_south), ('E idle', lambda: b_side('E')),
                  ('W idle', lambda: b_side('W')), ('S fidget', lambda: b_south(True))],
        'palette': ['dusk', 'plaster', 'timber', 'iron', 'brass', 'lamp'],
        'pose': 'A night-watch keeper leaning on her crook, lamp hung high but shuttered, head round and sleepy.',
        'parts': [
            'legs and feet: iron, layer 1, S/E/W, attach foot',
            'far wing lobe: dusk_cool, layer 2, E/W only, attach back',
            'shift (body): dusk_cool, layer 3, S/E/W, attach hip; folds swing in walk',
            'hind lobes: dusk_warm, layer 4, S/E/W, attach back',
            'fore lobes with eye-spots: dusk + plaster spot, layer 5, S/E/W, attach back (open wide for cast and cheer)',
            'ruff: plaster, layer 6, S/E/W, attach chest',
            'head: plaster, layer 7, S/E/W, attach head; eyes ink',
            'plumes: dusk_warm, layer 8, S/E/W, attach head',
            'crook pole and hook: timber, layer 9, S/E/W, attach hand (left paw: S right of her, E ahead, W at the hip with the lamp trailing; planted in walk, swung for strike)',
            'lamp: iron + brass + lamp glow, layer 10, attach crook tip (sways 1 px after a step)',
            'paws: plaster, layer 11, S/E/W, attach hand',
        ],
        'notes': [
            'Works: the most distinct silhouette (a crook and hung lamp beside her), and the eye-spots read at game scale.',
            'Risk: the crook widens the cell (x 15 to 55), must be redrawn in every fight pose, and swaps sides between E and W; the head is a plain blob.',
            'Compared with John and the station folk in eastward-02/05 at 46 px: prop outlines a tone darker than the hand holding them.',
        ],
    },
    {
        'label': 'C', 'name': 'Ruff and swallowtail coat, lamp at the hip',
        'question': 'A high fur ruff collar, wings closed like a long belted coat ending in two '
                    'luna-moth tails; the shuttered lamp hangs at the hip on a short chain.',
        'views': [('S idle', c_south), ('E idle', lambda: c_side('E')),
                  ('W idle', lambda: c_side('W')), ('S fidget', lambda: c_south(True))],
        'palette': ['dusk', 'plaster', 'snow', 'iron', 'brass', 'lamp'],
        'pose': 'Upright and gentle, a lamplighter off duty: paw resting on the lamp at her hip, chin sunk in the ruff.',
        'parts': [
            'feet: iron, layer 1, S/E/W, attach foot',
            'swallowtails: dusk_warm, layer 2, S/E/W, attach hip (trail and swing in walk)',
            'coat (closed wings): dusk with dusk_warm chevron margins, layer 3, S/E/W, attach chest',
            'belt: brass, layer 4, S/E/W, attach hip',
            'collar back: snow_cool, layer 5, S/E/W, attach chest',
            'plumes: plaster, layer 6, S/E/W, attach head',
            'head: plaster, layer 7, S/E/W, attach head; eyes ink',
            'ruff front: snow, layer 8, S/E/W, attach chest (puffs on breath); the chin throws a tone-1 shadow on it',
            'lamp and chain: iron + brass + lamp glow, layer 9, S/E/W, attach hip (lifted to hand for cast)',
            'paws: plaster, layer 10, S/E/W, attach hand',
        ],
        'notes': [
            'Works: the ruff makes her the softest, most moth-like shape; the tails give a unique hem in walk.',
            'Risk: snow ruff against plaster face needs the seam and chin shadow to stay apart; the hip lamp is small at game scale.',
            "Compared with eastward-02's John at 46 px: our ruff tufts are 2 to 3 px clumps like his hair, no single-pixel noise.",
        ],
    },
]


# =======================================================================================
# FINAL (revision round): C, ruff and swallowtail coat, with A's closed-wing nap and
# B's eye-spots moved low onto the coat tails. Deep dusk leads the coat (tones 1 to 3),
# the ruff is snow, the lamp hangs at her RIGHT hip in every facing (S: screen left,
# E: the near side, W: the far side, behind the coat), and the familiar perches on the
# shoulder away from the foe.
# =======================================================================================
def deep(d: D, mask, west=2):
    """Deep dusk: drop a shaded part one tone (tones 1 to 3 lead), then lift its first
    `west` px a row back up one tone so the west face still reads lit."""
    for p in mask:
        v = d.f.px.get(p)
        if v and v[0] != 'ink' and not str(v[0]).startswith('_'):
            t = v[1]
            d.f.px[p] = (v[0], max(1, t - 1) if t > 0 else 0)
    rows = {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        xs.sort()
        for x in xs[:west]:
            v = d.f.px.get((x, y))
            if v and v[0] != 'ink' and v[1] in (1, 2):
                d.f.px[(x, y)] = (v[0], v[1] + 1)


def antenna(d: D, path, fam='plaster', side=-1):
    """A combed, swept-back moth antenna: a 1 px shaft along `path` (E space), with
    2 px barbs every other pixel hanging below the arch (or outward on the rising
    stalk). The outline fills the notches, so it reads as a feather, not an ear."""
    shaft = []
    for a, b in zip(path, path[1:]):
        seg = line4(a, b)
        shaft += seg if not shaft else seg[1:]
    for i, (x, y) in enumerate(shaft):
        d.put(x, y, fam, 2 if i < 2 else (4 if i < len(shaft) // 2 else 3))
    for i in range(3, len(shaft) - 1, 2):
        x, y = shaft[i]
        px_, py_ = shaft[i - 1]
        if px_ == x:      # rising stalk: barbs point outward
            pts = [(x + side, y), (x + 2 * side, y)]
        else:             # the arch: barbs hang below
            pts = [(x, y + 1), (x, y + 2)]
        for q in pts:
            d.put(q[0], q[1], fam, 2)


def snow_ruff(d: D, mask):
    """The snow ruff: whiter and fluffier than fleece. Shaded snow (4 leads), fur as
    downward 1 x 2 strokes following the fall of the fur, dark in the shaded half."""
    d.part(mask, 'snow', soft=0.25)
    xs = [p[0] for p in mask]
    cx = (min(xs) + max(xs)) / 2
    top = {p for p in mask if d.f.px[p] == ('snow', 4) and (p[0], p[1] + 1) in mask}
    d.f.clusters(top, 'snow', 3, [(0, 0), (0, 1)], (3, 3))
    low = {p for p in mask if d.f.px[p] in (('snow', 3), ('snow', 2)) and p[0] > cx}
    d.f.clusters(low, 'snow', 2, [(0, 0), (0, 1)], (3, 3))


def tail_spot(d: D, cx, cy):
    """B's eye-spot, faint and low on a coat tail: a dusk_warm ring round a dim cream eye."""
    for (x, y) in d.rect(cx - 1, cy - 1, cx + 2, cy + 2, knock=1):
        if (x, y) in d.f.px and d.f.px[(x, y)][0] in ('dusk_warm', 'dusk'):
            d.f.px[(x, y)] = ('dusk_warm', 3)
    for (x, y) in d.rect(cx, cy, cx + 1, cy + 1):
        if (x, y) in d.f.px:
            d.f.px[(x, y)] = ('plaster_cool', 1)


def mossling(d: D, cx, bottom, curled=False):
    """Stand-in familiar (about 24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    ry = 6.5 if curled else 8.5
    body = d.ell(cx, bottom - ry, 9 if not curled else 9, ry)
    d.part(body, 'grass', soft=0.15, glint=(cx - 6, int(bottom - 2 * ry) + 2))
    for p in body:                 # a fresh grass green: tones 2 to 4 lead
        v = d.f.px[p]
        if v[0] == 'grass' and v[1] < 4:
            d.f.px[p] = ('grass', v[1] + 1)
    west_lit(d, body, 3, 0)
    profile_shade(d, body, 2)
    tufts(d, body, 'grass', lit=False, step=(4, 3))
    top = int(bottom - 2 * ry)
    stem = d.rect(cx, top - 3, cx, top)
    d.part(stem, 'grass', deep=False)
    d.part(d.rect(cx + 1, top - 5, cx + 3, top - 4, knock=0), 'grass', deep=False)
    d.part(d.rect(cx, top - 4, cx, top - 4), 'grass', deep=False)
    ey = int(bottom - ry) - (1 if curled else 2)
    for ex in (cx - 4, cx + 2):
        if curled:
            d.put(ex, ey + 1, 'ink', 0)
            d.put(ex + 1, ey + 1, 'ink', 0)
        else:
            for q in ((ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)):
                d.put(q[0], q[1], 'ink', 0)


def arm(d: D, sh, paw, fam='dusk'):
    """A wing-sleeve from the shoulder to the paw: a 3 px stroke in deep dusk, a cream paw."""
    (x0, y0), (x1, y1) = sh, paw
    m = set()
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        cx, cy = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        m |= d.ell(cx + 0.5, cy + 0.5, 1.6, 1.6)
    d.part(m, fam, soft=0.1)
    deep(d, m, 1)
    d.part(d.ell(x1 + 0.5, y1 + 0.5, 2, 1.8), 'plaster', soft=0.2)
    return m


def head_s(d: D, cx, cy, closed=False):
    """S head as a form: a lit brow over big dark eyes, a small muzzle step, cheek tufts."""
    head = d.ell(cx, cy, 6.8, 6.3)
    d.part(head, 'plaster', soft=0.15, glint=(int(cx) - 5, int(cy) - 5))
    y0 = int(cy) - 3
    for x in range(int(cx) - 5, int(cx) + 6):       # brow: a lit plane over the eyes
        if (x, y0) in head:
            d.f.px[(x, y0)] = ('plaster', 4 if x < cx + 2 else 3)
    for x in list(range(int(cx) - 5, int(cx) - 1)) + list(range(int(cx) + 2, int(cx) + 6)):
        if (x, y0 + 1) in head:
            d.f.px[(x, y0 + 1)] = ('plaster', 2)  # the brow's shade on the eyes
    eye(d, int(cx) - 5, y0 + 2, closed=closed)
    eye(d, int(cx) + 2, y0 + 2, closed=closed)
    mx = int(cx) - 1
    for x in range(mx, mx + 3):                     # muzzle: a small step, lit top, shaded base
        d.f.px[(x, y0 + 6)] = ('plaster', 4 if x < mx + 2 else 3)
        d.f.px[(x, y0 + 7)] = ('plaster', 2)
    for x in range(mx - 1, mx + 4):                 # chin shadow
        if (x, y0 + 9) in head:
            d.f.px[(x, y0 + 9)] = ('plaster', 1 if x > mx else 2)
    for q in ((int(cx) - 6, y0 + 6), (int(cx) - 5, y0 + 6), (int(cx) - 6, y0 + 7)):
        if q in head:
            d.f.px[q] = ('plaster', 4)              # lit cheek tuft
    for q in ((int(cx) + 5, y0 + 6), (int(cx) + 6, y0 + 6), (int(cx) + 6, y0 + 7)):
        if q in head:
            d.f.px[q] = ('plaster', 2)              # shaded cheek tuft
    return head


def head_side(d: D, cx, cy, closed=False):
    """Profile head as a form (E space, facing +x): round skull, a brow ridge over a big
    moth eye, a muzzle step at the front, a cheek tuft, the chin's shadow."""
    head = d.ell(cx, cy, 6.5, 6.3) | d.rect(int(cx) + 6, int(cy) + 1, int(cx) + 7, int(cy) + 3)
    d.part(head, 'plaster', soft=0.15, glint=(int(cx) - 4, int(cy) - 5))
    profile_shade(d, head, 2)
    hx, hy = int(cx), int(cy)
    for x in range(hx + 1, hx + 7):                  # brow ridge, lit, with shade under it
        p = (d.X(x), hy - 3)
        if p in head:
            d.f.px[p] = ('plaster', 4)
        q = (d.X(x), hy - 2)
        if q in head:
            d.f.px[q] = ('plaster', 2)
    eye(d, hx + 2, hy - 1, closed=closed)
    for x, t in ((hx + 6, 4), (hx + 7, 3)):           # muzzle step
        d.put(x, hy + 1, 'plaster', t)
        d.put(x, hy + 2, 'plaster', 3)
        d.put(x, hy + 3, 'plaster', 2)
    for x in range(hx + 3, hx + 8):                   # chin shadow under the muzzle
        p = (d.X(x), hy + 4)
        if p in head:
            d.f.px[p] = ('plaster', 1)
    for q in ((hx, hy + 3), (hx + 1, hy + 3), (hx, hy + 4)):   # cheek tuft
        p = (d.X(q[0]), q[1])
        if p in head:
            d.f.px[p] = ('plaster', 4)
    for q in ((hx - 5, hy - 1), (hx - 5, hy), (hx - 4, hy + 1)):  # nape fur, lit west
        p = (d.X(q[0]), q[1])
        if p in head:
            d.f.px[p] = ('plaster', 4)
    return head


def coat_side(d: D, dy=0, hx=0, flare=0):
    top = 40 + dy
    tail = d.poly([(25, 56), (30, 62), (17 - flare, 66 - flare), (17 - flare, 64 - flare)])
    d.part(tail, 'dusk_warm', soft=0.1)
    deep(d, tail, 2)
    tail_spot(d, 21 - flare, 63 - flare)
    return tail, top


def coat_body_side(d: D, top, hx=0):
    coat = d.poly([(27 + hx // 2, top), (38 + hx // 2, top), (40, 51), (41, 63), (24, 63), (25, 51)])
    d.part(coat, 'dusk', soft=0.15)
    deep(d, coat, 3)
    folds(d, coat, (28, 32), 50, 62, 'dusk')
    for y in range(top + 1, 63):                     # the wing's front margin: chevrons
        p = (d.X(37), y)
        if p in coat:
            d.f.px[p] = ('dusk', 1)
        if (y - top) % 4 in (0, 1):
            for xx in (38, 39):
                q = (d.X(xx), y)
                if q in coat:   # the margin catches the light when it faces west
                    d.f.px[q] = ('dusk_warm', 3 if d.w else 2)
    front_tail = d.poly([(38, 57), (42, 66), (37, 64)])
    d.part(front_tail, 'dusk_warm', soft=0.1)
    deep(d, front_tail, 1)
    for x in range(23, 42):                          # brass belt
        p = (d.X(x), 48)
        if p in coat:
            d.f.px[p] = ('brass', 3 if p[0] < 32 else 2)
            d.f.px[(p[0], 49)] = ('brass', 1)
    return coat


def side_view(facing, pose='idle'):
    """E/W views and fight keys. E space faces +x; W mirrors the geometry and is shaded
    afresh. The lamp is on her right hip: the near side in E, the far side in W."""
    d = D(facing)
    P = {
        'idle':   dict(dy=0, hx=0, closed=False, near=None, far=None, lamp='hip', fam=None, wf=None, wb=None, ant=0),
        'ready':  dict(dy=1, hx=1, closed=False, near=(42, 46), far=None, lamp='hip', fam=True, wf=None, wb=None, ant=0),
        'strike': dict(dy=1, hx=2, closed=False, near=(52, 44), far=None, lamp='hip', fam=True,
                       wf=[(37, 41), (53, 39), (56, 46), (51, 55), (39, 56)], wb=None, ant=1),
        'cast':   dict(dy=0, hx=0, closed=False, near=(44, 41), far=None, lamp='hand', fam=True, wf=None,
                       wb=[(27, 41), (16, 37), (15, 47), (24, 53)], ant=-1),
        'hit':    dict(dy=1, hx=-2, closed=True, near=(38, 43), far=None, lamp='hip', fam=True, wf=None, wb=None, ant=2),
        'cheer':  dict(dy=-1, hx=0, closed=True, near=(45, 30), far=(27, 28), lamp='hip', fam=True,
                       wf=[(38, 41), (50, 35), (52, 45), (42, 53)], wb=[(27, 41), (15, 35), (13, 45), (23, 53)], ant=-1),
    }[pose]
    dy, hx = P['dy'], P['hx']
    near_lamp = not d.w
    # feet
    d.part(d.rect(27, 63, 30, 66, knock=1), 'iron')
    d.part(d.rect(34 + (2 if pose == 'strike' else 0), 63, 38 + (2 if pose == 'strike' else 0), 66, knock=1), 'iron')
    tail, top = coat_side(d, dy, hx, flare=2 if pose in ('hit', 'cheer') else 0)
    # the lamp on the far hip (W) hangs behind the coat, peeking past its back edge
    if P['lamp'] == 'hip' and not near_lamp:
        d.part(d.rect(23, 49, 23, 50), 'brass')
        lantern(d, 22, 51, glow_len=0)
    if P['wb']:
        wb = d.poly(P['wb'])          # the opened wing shows its lit upper face
        d.part(wb, 'dusk_warm', soft=0.1)
        west_lit(d, wb, 3, 0)
        ring_inside(d, wb, 'dusk_warm', 3, 'bottom')
    if P['far']:
        arm(d, (31 + hx, 42 + dy), P['far'])
    coat = coat_body_side(d, top, hx)
    # collar standing behind the head
    collar = d.ell(31 + hx, 35.5 + dy, 7.5, 4.5)
    d.part(collar, 'snow_cool', soft=0.1)
    tufts(d, collar, 'snow_cool', lit=False, step=(3, 2))
    profile_shade(d, collar, 3)
    perch = None
    if P['fam']:
        perch = (20 + hx, 38 + dy)
        mossling(d, perch[0], perch[1])
    antenna(d, [(36 + hx, 25 + dy), (36 + hx, 22 + dy), (35 + hx, 21 + dy), (31 + hx, 21 + dy),
                (28 + hx, 22 + dy + P['ant']), (26 + hx, 24 + dy + P['ant'])], 'plaster_cool', side=1)
    head = head_side(d, 34 + hx, 30.5 + dy, closed=P['closed'])
    antenna(d, [(34 + hx, 25 + dy), (34 + hx, 22 + dy), (33 + hx, 21 + dy), (29 + hx, 21 + dy),
                (26 + hx, 22 + dy + P['ant']), (24 + hx, 24 + dy + P['ant']), (23 + hx, 26 + dy + P['ant'])],
            'plaster', side=-1)
    ruff = d.ell(33 + hx, 39.5 + dy, 9.5, 3.5)
    for x in range(24, 43, 3):
        ruff |= d.rect(x + hx, 42 + dy, x + 1 + hx, 43 + dy)
    snow_ruff(d, ruff)
    profile_shade(d, ruff, 2)
    for (x, y) in head:                               # the chin's shadow on the ruff, every facing
        if (x, y + 1) in ruff and (x, y + 1) not in head:
            d.f.px[(x, y + 1)] = ('snow', 2)
    if P['wf']:
        wf = d.poly(P['wf'])
        d.part(wf, 'dusk_warm', soft=0.1)
        deep(d, wf, 2)
        ring_inside(d, wf, 'dusk_warm', 3, 'bottom')
        folds(d, wf, (43, 48), 40, 55, 'dusk_warm')
    if P['lamp'] == 'hip' and near_lamp:
        d.part(d.rect(31, 49, 31, 50), 'brass')
        lantern(d, 31, 51, glow_len=2, glow_tone=2)
    if P['near']:
        arm(d, (36 + hx, 42 + dy), P['near'])
        if P['lamp'] == 'hand':
            lantern(d, P['near'][0] + 1, P['near'][1] + 2, glow_len=2, glow_tone=3)
            d.part(d.ell(P['near'][0] + 1.5, P['near'][1] + 1.5, 2, 1.6), 'plaster', soft=0.2)
    else:
        d.part(d.ell(38.5, 50.5, 2, 1.8), 'plaster', soft=0.2)
    img = finish(d)
    if perch and d.w:
        perch = (64 - perch[0], perch[1])
    return img, perch


def sit_side(facing):
    d = D(facing)
    tail = d.poly([(24, 60), (29, 64), (16, 66), (16, 64)])
    d.part(tail, 'dusk_warm', soft=0.1)
    deep(d, tail, 2)
    tail_spot(d, 20, 64)
    if d.w:
        d.part(d.rect(21, 52, 21, 53), 'brass')
        lantern(d, 21, 54, glow_len=0)
    coat = d.poly([(27, 47), (38, 47), (42, 56), (44, 65), (21, 65), (23, 56)])
    d.part(coat, 'dusk', soft=0.15)
    deep(d, coat, 3)
    folds(d, coat, (28, 33), 54, 64, 'dusk')
    for x in range(22, 43):
        p = (d.X(x), 55)
        if p in coat:
            d.f.px[p] = ('brass', 3 if p[0] < 32 else 2)
            d.f.px[(p[0], 56)] = ('brass', 1)
    d.part(d.rect(42, 63, 46, 66, knock=1), 'iron')     # feet out in front
    collar = d.ell(31, 42.5, 7.5, 4.5)
    d.part(collar, 'snow_cool', soft=0.1)
    tufts(d, collar, 'snow_cool', lit=False, step=(3, 2))
    profile_shade(d, collar, 3)
    perch = (20, 45)
    mossling(d, *perch)
    antenna(d, [(36, 32), (36, 29), (35, 28), (31, 28), (28, 30), (26, 32)], 'plaster_cool', side=1)
    head = head_side(d, 34, 37.5, closed=True)
    antenna(d, [(34, 32), (34, 29), (33, 28), (29, 28), (26, 30), (24, 32), (23, 34)], 'plaster', side=-1)
    ruff = d.ell(33, 46.5, 9.5, 3.5)
    for x in range(24, 43, 3):
        ruff |= d.rect(x, 49, x + 1, 50)
    snow_ruff(d, ruff)
    for (x, y) in head:
        if (x, y + 1) in ruff and (x, y + 1) not in head:
            d.f.px[(x, y + 1)] = ('snow', 2)
    if not d.w:
        d.part(d.rect(30, 52, 30, 53), 'brass')
        lantern(d, 30, 54, glow_len=1, glow_tone=2)
    d.part(d.ell(40.5, 56.5, 2, 1.8), 'plaster', soft=0.2)
    img = finish(d)
    if d.w:
        perch = (64 - perch[0], perch[1])
    return img, perch


def south_final(fidget=False):
    d = D('S')
    for x0 in (28, 33):
        d.part(d.rect(x0, 63, x0 + 3, 66, knock=1), 'iron')
    for pts, spot in (([(23, 55), (29, 62), (20, 66), (20, 64)], (21, 63)),
                      ([(42, 55), (36, 62), (45, 66), (45, 64)], (42, 63))):
        t = d.poly(pts)
        d.part(t, 'dusk_warm', soft=0.1)
        deep(d, t, 2)
        tail_spot(d, *spot)
    coat = d.poly([(26, 40), (39, 40), (41, 51), (42, 63), (23, 63), (24, 51)])
    d.part(coat, 'dusk', soft=0.15)
    deep(d, coat, 3)
    folds(d, coat, (26, 29, 37, 40), 50, 62, 'dusk')
    for y in range(41, 63):                           # the closed wings' margins meet down the front
        d.f.px[(32, y)] = ('dusk', 0)
        if (y - 41) % 4 in (0, 1):
            d.f.px[(30, y)] = ('dusk_warm', 3)
            d.f.px[(31, y)] = ('dusk_warm', 3)
            d.f.px[(33, y)] = ('dusk_warm', 2)
            d.f.px[(34, y)] = ('dusk_warm', 2)
    for x in range(24, 42):
        if (x, 48) in coat:
            d.f.px[(x, 48)] = ('brass', 3 if x < 33 else 2)
            d.f.px[(x, 49)] = ('brass', 1)
    for p in ((31, 48), (32, 48), (31, 49), (32, 49)):
        d.f.px[p] = ('brass', 4 if p[1] == 48 else 3)
    collar = d.ell(32.5, 35.5, 10, 4.5)
    d.part(collar, 'snow_cool', soft=0.1)
    tufts(d, collar, 'snow_cool', lit=False, step=(3, 2))
    hy = 31.5 if fidget else 30.5
    head = head_s(d, 32.5, hy, closed=fidget)
    lo = 1 if fidget else 0
    antenna(d, [(30, 25), (30, 22), (29, 21), (25, 21), (22, 22 + lo), (20, 24 + lo), (19, 26 + lo)], 'plaster', side=-1)
    antenna(d, [(35, 25), (35, 22), (36, 21), (40, 21), (43, 22 + lo), (45, 24 + lo), (46, 26 + lo)], 'plaster', side=1)
    ruff = d.ell(32.5, 39.5, 11.5, 3.5)
    for x in range(21, 45, 3):
        ruff |= d.rect(x + 1, 42, x + 2, 43)
    snow_ruff(d, ruff)
    for (x, y) in head:
        if (x, y + 1) in ruff and (x, y + 1) not in head:
            d.f.px[(x, y + 1)] = ('snow', 2)
    if fidget:
        lantern(d, 32, 43, glow_len=1, glow_tone=2)
        d.part(d.ell(28.5, 49.5, 2, 1.8), 'plaster', soft=0.2)
        d.part(d.ell(35.5, 44.5, 2, 1.8), 'plaster', soft=0.2)
    else:
        d.part(d.rect(22, 49, 22, 50), 'brass')
        lantern(d, 22, 51, glow_len=2, glow_tone=2)
        d.part(d.ell(37.5, 50.5, 2, 1.8), 'plaster', soft=0.2)
        d.part(d.ell(25.5, 47.5, 2, 1.8), 'plaster', soft=0.2)
    return finish(d)


def nap_south():
    """A's closed-wing wrap: the coat-wings fold round her as one bell; she sleeps sitting
    inside it, antennae laid back, the shut lamp set down at her right side, the familiar
    curled against her."""
    d = D('S')
    bell = d.poly([(24, 45), (41, 45), (45, 54), (47, 64), (18, 64), (20, 54)])
    d.part(bell, 'dusk', soft=0.15)
    deep(d, bell, 3)
    folds(d, bell, (24, 28, 38, 42), 52, 63, 'dusk')
    for y in range(46, 64):                           # the right wing wraps over the left
        x = 34 - (y - 46) // 4
        d.f.px[(x, y)] = ('dusk', 0)
        if (x + 1, y) in bell:
            d.f.px[(x + 1, y)] = ('dusk_warm', 2)
        if (x - 1, y) in bell:
            d.f.px[(x - 1, y)] = ('dusk_warm', 3)
    for x in range(19, 47):                           # wing margin at the hem
        if (x, 62) in bell and (x - 19) % 5 in (0, 1, 2):
            d.f.px[(x, 62)] = ('dusk_warm', 3 if x < 33 else 2)
    collar = d.ell(32.5, 42, 9.5, 4)
    d.part(collar, 'snow_cool', soft=0.1)
    tufts(d, collar, 'snow_cool', lit=False, step=(3, 2))
    head = head_s(d, 32.5, 37.5, closed=True)
    antenna(d, [(29, 32), (27, 31), (23, 31), (21, 33), (20, 35)], 'plaster', side=-1)
    antenna(d, [(36, 32), (38, 31), (42, 31), (44, 33), (45, 35)], 'plaster', side=1)
    ruff = d.ell(32.5, 45.5, 10.5, 3)
    for x in range(23, 43, 3):
        ruff |= d.rect(x + 1, 48, x + 2, 49)
    snow_ruff(d, ruff)
    for (x, y) in head:
        if (x, y + 1) in ruff and (x, y + 1) not in head:
            d.f.px[(x, y + 1)] = ('snow', 2)
    west_lit(d, bell, 3, 0)
    d.part(d.rect(24, 51, 24, 52), 'brass')
    lantern(d, 24, 53, glow_len=0)
    mossling(d, 17, 66, curled=True)
    return finish(d)


FINAL_PARTS = [
    'feet: iron, layer 1, anchor foot, S/E/W (sit: thrust forward)',
    'back swallowtail with faint eye-spot: dusk_warm deep + plaster_cool eye, layer 2, anchor hip, S/E/W (flares 2 px in hit and cheer)',
    'lamp on her right hip (far side in W): iron + brass, lamp glow 2 px tone 2 at most, layer 3 in W (behind the coat), layer 9 in S/E; anchor hip; to the hand only for cast and the fidget',
    'back wing flare: dusk_warm deep, layer 4, anchor back, E/W only (cast, cheer)',
    'far arm-sleeve: dusk deep + plaster paw, layer 5, anchor hand, E/W (cheer)',
    'coat (closed forewings): dusk, tones 1 to 3 lead, chevron margin dusk_warm, brass belt, front swallowtail; layer 6, anchor chest/hip, S/E/W',
    'collar back: snow_cool deep, layer 7, anchor chest, S/E/W',
    'familiar perch: on the collar shelf, shoulder away from the foe; layer 7.5 (behind the head)',
    'far antenna: plaster_cool, layer 8, anchor head, E/W',
    'head: plaster, brow, big ink eyes, muzzle step, cheek tufts; layer 8, anchor head (eyes anchor for blink/sleep), S/E/W',
    'near antennae: plaster, combed and swept back, layer 9, anchor head, S/E/W (laid back in nap, flung back in hit)',
    'ruff front: snow, downward fur strokes, chin shadow tone 2 in every facing, layer 10, anchor chest, S/E/W',
    'front wing flare: dusk_warm deep, layer 11, anchor chest, E/W (strike: the wing buffet at full reach)',
    'near arm-sleeve and paw: dusk deep + plaster, layer 12, anchor hand, S/E/W',
]

FINAL_NOTES = [
    'Grafts: A\'s closed-wing wrap for the nap (one bell); B\'s eye-spots, faint and only on the coat tails.',
    'Deep dusk (tones 1 to 3) leads the coat so she reads apart from Puffcap\'s light dusk; the ruff is snow with downward 1 x 2 fur strokes.',
    'Lamp fixed to her right hip: S screen-left, E near side, W far side behind the coat; it reaches the paw only for cast and the fidget.',
    'Compared by eye at 46 px with John and Sam in eastward-02 (head a third of the height, 4 to 5 tones a material, dark joints, clumped hair).',
]


def final_views():
    out = [('S idle', south_final(), None), ('E idle', *side_view('E', 'idle')),
           ('W idle', *side_view('W', 'idle')), ('S fidget', south_final(True), None),
           ('nap S', nap_south(), None)]
    for pose, cap in (('ready', 'E ready'), ('strike', 'E strike'), ('cast', 'E cast'), ('hit', 'E hit')):
        out.append((cap, *side_view('E', pose)))
    out.append(('E sit', *sit_side('E')))
    out.append(('E cheer', *side_view('E', 'cheer')))
    out.append(('W ready', *side_view('W', 'ready')))
    out.append(('W strike', *side_view('W', 'strike')))
    return out


def final_gates(m):
    return (m['on_house'] >= 0.999 and m['west_east'] > 0 and m['isolated'] <= 0.04
            and m['colours'] <= 64 and m.get('outline_dark', 0) >= 0.95)


def gates(m):
    ok = (m['on_house'] >= 0.999 and m['west_east'] > 0 and m['isolated'] <= 0.06
          and m['colours'] <= 64 and m.get('outline_dark', 0) >= 0.95)
    return ok


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    sheet_opts, record = [], {'id': 'velvet', 'name': 'Velvet', 'height_art_px': 46,
                              'cell': [64, 72], 'anchor': [32, 66],
                              'question': 'How the wings work as a cloak and where the shuttered lamp lives',
                              'options': []}
    all_ok = True
    for opt in OPTIONS:
        views = []
        rec = {k: opt[k] for k in ('label', 'name', 'question', 'parts', 'palette', 'pose', 'notes')}
        rec['views'] = {}
        for cap, fn in opt['views']:
            im = fn()
            views.append((cap, im))
            m = sk.measure(im)
            ok = gates(m)
            all_ok &= ok
            slug = cap.replace(' ', '-')
            im.save(os.path.join(SCRATCH, f"{opt['label']}-{slug}.png"))
            keep = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
            keep['pass'] = ok
            keep['misses'] = style_lint.misses(m)
            rec['views'][cap] = keep
            print(f"{opt['label']} {cap:9s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  {'PASS' if ok else 'FAIL'} {style_lint.misses(m)}")
        record['options'].append(rec)
        sheet_opts.append({**opt, 'views': views, 'palette': [f for f in opt['palette'] if f in sk.EDGES]})
    sk.design_sheet('Velvet: wings as a cloak, and where the shuttered lamp lives', sheet_opts,
                    os.path.join(OUT_DIR, 'velvet-options.png'),
                    note='Moth-folk keeper of the Driftwood lighthouse, 46 art px, cell 64 x 72, foot (32, 66). '
                         'Glow is a sliver only (fig.glow).')
    print('options:', 'all gates pass' if all_ok else 'SOME GATES FAIL')
    # --- final ---
    fin_ok = True
    views, nums, perches = [], {}, {}
    for cap, im, perch in final_views():
        views.append((cap, im))
        m = sk.measure(im)
        ok = final_gates(m)
        fin_ok &= ok
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        keep = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}
        keep['pass'] = ok
        keep['misses'] = style_lint.misses(m)
        nums[cap] = keep
        if perch:
            perches[cap] = list(perch)
        print(f"final {cap:9s} on house {100 * m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100 * m['isolated']:4.1f}%  colours {m['colours']:2d}  "
              f"outline dark {100 * m.get('outline_dark', 0):5.1f}%  {'PASS' if ok else 'FAIL'}")
    pal = ['dusk', 'snow', 'plaster', 'iron', 'brass']
    entry = {'label': 'C final', 'name': 'Ruff and swallowtail coat, lamp at the right hip',
             'views': views, 'parts': FINAL_PARTS, 'palette': pal,
             'pose': 'Upright and hushed, chin sunk in her snow ruff, a paw on the shuttered lamp at her hip.',
             'notes': FINAL_NOTES}
    sk.design_sheet('Velvet final: C with A\'s nap wrap and B\'s tail eye-spots', [entry],
                    os.path.join(OUT_DIR, 'velvet-final.png'),
                    note='46 art px, cell 64 x 72, foot (32, 66). Familiar: a stand-in Mossling on the shoulder away from the foe.')
    record['final'] = {
        'chosen': 'C', 'name': entry['name'],
        'grafts': ['A: the closed-wing wrap for the nap (one bell silhouette)',
                   'B: faint wing eye-spots, only low on the coat tails'],
        'parts': FINAL_PARTS, 'palette': pal + ['lamp (glow, 2 px sliver at most)', 'grass (stand-in familiar only)'],
        'pose': entry['pose'], 'perch_anchor': perches, 'views': nums, 'notes': FINAL_NOTES,
        'eastward_compared': ['John (eastward-02)', 'Sam (eastward-02)'],
    }
    with open(os.path.join(OUT_DIR, 'velvet.json'), 'w') as fh:
        json.dump(record, fh, indent=2)
    print('final:', 'all gates pass' if fin_ok else 'SOME GATES FAIL')


if __name__ == '__main__':
    main()
