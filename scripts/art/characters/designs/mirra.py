"""Mirra, the gecko water-diviner of Sunstone: three design options (Claude J lane, batch 2).

Main question: gecko, hat and the dowsing rod's silhouette.

    A  Sun-hat diviner: a wide, flat woven sun hat with a chin cord, an adobe gecko in a
       linen smock, a long Y-rod held forward in both hands, a small flask at the hip.
    B  Cone-hat pilgrim: a conical woven hat, a cactus-green gecko in an adobe wrap, a short
       forked twig in one hand and a big water flask at the belly.
    C  Dune traveller: bare-headed sand gecko in a long bleached duster and an adobe scarf,
       the flat sun hat hung on her back and the Y-rod slung on a strap, its fork over her
       shoulder; the big flask at the front of her belt.

Views: S idle, E idle, W idle (W is drawn with its own light, never mirrored pixels: the
side views share geometry through a facing transform and are shaded after it, so the lit
side stays on the left) and the S key pose of her fidget. Design sheets are review
material; production frames come from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<scratch>/designs python3 scripts/art/characters/designs/mirra.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/mirra-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/mirra.json')
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/mirra-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'mirra')

W, H = 64, 72
AX, AY = 32, 66          # foot anchor: soles fill row 65, their outline lands on row 66
SOLE = AY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def darken(fig, p, by=1, floor=1):
    t = tone(fig, p)
    if t is not None and fam_at(fig, p) != 'ink':
        fig.put(p[0], p[1], fam_at(fig, p), max(floor, t - by))


def cloth(fig, mask, fam, lit=2, dark=2, folds=(), top=True, bottom=True):
    """Cloth in vertical bands (house-style 5): a lit west band, the body, a shaded east
    band, a lit top row and a dark hem row. `folds` are x columns of tone 2 (a recess)."""
    mask = set(mask)
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    for (x, y) in mask:
        xl, xr = min(rows[y]), max(rows[y])
        t = 3
        if x - xl < lit:
            t = 4
        elif xr - x < dark:
            t = 2
        if top and y == min(cols[x]) and t >= 3:
            t = 4
        if bottom and y == max(cols[x]):
            t = 1
        fig.put(x, y, fam, t)
    for fx in folds:
        for (x, y) in mask:
            if x == fx and min(cols[x]) + 1 < y < max(cols[x]):
                fig.put(x, y, fam, 2)
    return mask


def pillow(fig, mask, fam, cap=0.42, rim=1.05):
    """A round part (a head, a flask): the lit cap is a disc offset to the upper left and
    the dark crescent the outside of a larger offset disc, so the terminator follows the
    form instead of stepping across it in a straight diagonal."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 3
        if (u + 0.42) ** 2 + (v + 0.5) ** 2 < cap:
            t = 4
        if (u + 0.28) ** 2 + (v + 0.32) ** 2 > rim:
            t = 2
        if (x, y + 1) not in mask and u > -0.3:
            t = min(t, 1 if u > 0.2 else 2)
        fig.put(x, y, fam, t)
    return mask


def edge_shade(fig, mask, fam, base=3):
    """A small chunky part (a limb, a foot, a tail): lit top row and west column, the
    body, a shaded east column and a dark underside."""
    mask = set(mask)
    for (x, y) in mask:
        t = base
        if (x - 1, y) not in mask or (x, y - 1) not in mask:
            t = base + 1
        if (x + 1, y) not in mask:
            t = base - 1
        if (x, y + 1) not in mask:
            t = base - 2 if (x - 1, y) in mask else base - 1
        fig.put(x, y, fam, max(1, t))
    return mask


def disc_path(fig, pts, r0, r1, step=0.5):
    """Mask of a tapering tube along a polyline: discs of radius r0 to r1."""
    samples = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step))
        for i in range(n):
            samples.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n))
    samples.append(pts[-1])
    m = set()
    for i, (x, y) in enumerate(samples):
        r = r0 + (r1 - r0) * i / max(1, len(samples) - 1)
        m |= fig.ellipse(x, y, r, r)
    return m, samples


def tube(fig, pts, r0, r1, fam, bands=0):
    """A limb or tail. `bands` > 0 draws gecko tail bands that many px long, a tone down."""
    m, samples = disc_path(fig, pts, r0, r1)
    edge_shade(fig, m, fam)
    if bands:
        for p in m:
            k = min(range(len(samples)), key=lambda i: (samples[i][0] - p[0] - 0.5) ** 2 + (samples[i][1] - p[1] - 0.5) ** 2)
            dist = k * 0.5
            if int(dist // bands) % 2 == 1 and dist > 2:
                darken(fig, p, 1)
    return m


def weave(fig, mask, fam, phase=0):
    """Woven straw as rows of 2 px dashes a tone down, staggered row to row (a plait,
    not a grid), only on rows of one parity."""
    for (x, y) in sorted(mask):
        if (y + phase) % 2 == 0 and (x + (y // 2) % 2 * 2) % 4 in (0, 1) and fam_at(fig, (x, y)) == fam:
            t = tone(fig, (x, y))
            if t is not None and t >= 3:
                fig.put(x, y, fam, t - 1)


def rod_line(fig, a, b, fam='timber'):
    """A wand two pixels thick. Near level or near upright: a lit line (tone 4) and its
    shaded side (tone 2). On a slant: lit pairs stepping along it (tone 3), so the stair
    reads as one rod and no step is a lone pixel; the outline gives its dark side."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    n = max(dx, dy, 1)
    pts = [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]
    steep = dy > dx
    slant = min(dx, dy) * 3 > max(dx, dy)
    if not slant:
        for (x, y) in pts:
            fig.put(x, y, fam, 4)
        for (x, y) in pts:
            q = (x + 1, y) if steep else (x, y + 1)
            if q not in pts:
                fig.put(q[0], q[1], fam, 2)
        return
    for (x, y) in pts:
        fig.put(x, y, fam, 3)
        q = (x, y + 1) if steep else (x + 1, y)
        fig.put(q[0], q[1], fam, 3)


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour, unless it is an eye, a glint, a nail or a rivet (`keep`). The tie-break is
    deterministic, so the script gives byte-identical output across runs."""
    for _ in range(2):
        changes = {}
        for p in sorted(fig.px):
            v = fig.px[p]
            if p in keep or v[0] in ('ink', '_edge', '_lit'):
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


class Face:
    """Facing transform: side views are written in E coordinates; W runs them through
    d = -1. Shading is applied to the transformed masks, so light stays upper left."""

    def __init__(self, d, du=0):
        self.d, self.du = d, du    # du: a shift forward (in her facing), in art px

    def x(self, x):            # a pixel column
        return (x if self.d == 1 else 2 * AX - x) + self.d * self.du

    def c(self, x):            # a continuous coordinate (ellipse centre, polygon vertex)
        return (x if self.d == 1 else 2 * AX + 1 - x) + self.d * self.du

    def p(self, pt):
        return (self.x(pt[0]), pt[1])

    def pc(self, pt):
        return (self.c(pt[0]), pt[1])

    def rect(self, fig, x0, y0, x1, y1, knock=0):
        a, b = sorted((self.x(x0), self.x(x1)))
        return fig.rect(a, y0, b, y1, knock)


# --- shared gecko parts ------------------------------------------------------------------
class Opt:
    def __init__(self, label, skin, glint, spot_fam=None):
        self.label, self.skin, self.glint = label, skin, glint
        self.spot = spot_fam or skin


def eye(fig, x, y, glint_fam, keep, shape='open'):
    """A gecko eye, 3 x 3 ink (big and lidless), the glint at its upper left. 'closed' is
    a lid line; 'wide' adds a pale ring row under it."""
    if shape == 'closed':
        for i in range(3):
            fig.put(x + i, y + 1, 'ink', 0)
        fig.put(x, y + 2, 'ink', 0)
        fig.put(x + 2, y + 2, 'ink', 0)
        return
    for j in range(3):
        for i in range(3):
            fig.put(x + i, y + j, 'ink', 0)
    fig.put(x, y, glint_fam, 5)
    keep.add((x, y))
    if shape == 'down':     # a lid over the top row: she watches the ground
        for i in range(3):
            fig.put(x + i, y, fig_skin(fig, x + i, y - 1), 2)


def fig_skin(fig, x, y):
    return fam_at(fig, (x, y)) or 'adobe'


def head_front(fig, o, keep, cy=38, eyes='open', brim=True, tilt=0, spots=True, smile_dy=0):
    """A gecko head from the front: broad cheeks at the back, the snout narrowing to a
    rounded chin, the eyes set in bumps on the sides (a frog's sit on top: Puddle's), a
    long smile across the snout."""
    cx = 32 + tilt
    # bare-headed, the crown rises a little over the eye bumps (no lumps on top)
    skull = fig.ellipse(cx + 0.5, cy - 0.5, 7.0, 4.6) if brim else fig.ellipse(cx + 0.5, cy - 0.9, 6.6, 5.2)
    snout = fig.ellipse(cx + 0.5, cy + 1.6, 5.4, 3.4)
    bumps = fig.ellipse(cx - 5.7, cy - 1.2, 2.6, 2.4) | fig.ellipse(cx + 6.7, cy - 1.2, 2.6, 2.4)
    head = skull | snout | bumps
    pillow(fig, head, o.skin, cap=0.5)
    for (bx, lit) in ((cx - 6, 4), (cx + 6, 3)):   # each eye bump is its own small form: a lit lid
        fig.put(bx - 1, cy - 4, o.skin, lit)
        fig.put(bx, cy - 4, o.skin, lit)
        fig.put(bx + 1, cy - 4, o.skin, lit)
    if spots:   # gecko spots: 2 px clusters a tone down, on the brow and cheeks
        sp = [(cx - 2, cy - 3), (cx + 2, cy - 2), (cx - 6, cy + 2), (cx + 7, cy + 1)]
        if not brim:   # a bare crown shows the leopard spots on top of the head
            sp += [(cx - 3, cy - 5), (cx + 3, cy - 5), (cx, cy - 4)]
        for (sx, sy) in sp:
            for q in ((sx, sy), (sx + 1, sy)):
                if q in head:
                    darken(fig, q, 1, 2)
    # the smile: long, ends turned up into the cheeks; a pale throat under it
    sm = (cy + 3 if brim else cy + 2) + smile_dy
    for x in range(cx - 2, cx + 4):
        if (x, sm + 1) in head:
            fig.put(x, sm + 1, o.skin, 4 if x < cx + 2 else 3)
        fig.put(x, sm, o.skin, 1)
    fig.put(cx - 3, sm - 1, o.skin, 1)
    fig.put(cx + 4, sm - 1, o.skin, 1)
    # nostrils
    fig.put(cx - 1, sm - 2, o.skin, 2)
    fig.put(cx + 2, sm - 2, o.skin, 2)
    ey = cy - 2 if brim else cy - 1
    eye(fig, cx - 7 + (0 if brim else 1), ey, o.glint, keep, eyes)
    eye(fig, cx + 6 - (0 if brim else 1), ey, o.glint, keep, eyes)
    if brim:    # the hard shadow under a brim (as Eastward's hats): one row
        top = min(y for x, y in head)
        for (x, y) in head:
            if y <= top + 1 and fam_at(fig, (x, y)) == o.skin:
                fig.put(x, y, o.skin, 2)
    return head


def head_side(fig, f, o, keep, cy=38, eyes='open', brim=True, look=0):
    """E-written profile: a round skull, a long flat snout sloping to a rounded tip, the
    eye bump as the brow, a cheek step under the eye and the smile running back under it."""
    sk_ = fig.ellipse(f.c(32.0), cy, 5.6, 5.0)
    sn = fig.ellipse(f.c(37.8), cy + 1.7 + look, 5.2, 2.8)
    bump = fig.ellipse(f.c(34.5), cy - 1.8, 2.7, 2.5)
    head = sk_ | sn | bump
    pillow(fig, head, o.skin, cap=0.5)
    # snout step: a shaded notch where the brow drops to the snout
    fig.put(f.x(37), cy - 1 + look, o.skin, 2)
    fig.put(f.x(38), cy - 1 + look, o.skin, 2)
    # cheek: a short shaded crescent under the eye
    for x in (32, 33, 34):
        fig.put(f.x(x), cy + 2, o.skin, 2)
    tip = max(x for x, y in sn) if f.d == 1 else min(x for x, y in sn)
    for k in range(1, 9):
        fig.put(tip - f.d * k, cy + 3 + look, o.skin, 1)
    fig.put(tip - f.d * 9, cy + 2 + look, o.skin, 1)
    fig.put(tip - f.d * 1, cy + 1 + look, o.skin, 1)     # nostril
    for (sx, sy) in ((28, cy - 2), (29, cy + 2)):
        for q in (f.p((sx, sy)), f.p((sx + 1, sy))):
            if q in head:
                darken(fig, q, 1, 2)
    ex = f.x(33) if f.d == 1 else f.x(35)
    eye(fig, ex, cy - 3, o.glint, keep, eyes)
    if brim:
        top = min(y for x, y in head)
        for (x, y) in head:
            if y <= top + 1 and fam_at(fig, (x, y)) == o.skin:
                fig.put(x, y, o.skin, 2)
    return head


def feet_front(fig, o, xs=(25, 34), lift=None):
    """Splayed gecko feet with round toe pads: three toes, each a 2 px pad."""
    for i, x0 in enumerate(xs):
        dy = -2 if lift == i else 0
        m = fig.rect(x0, 62 + dy, x0 + 4, 64 + dy, knock=1)
        for tx in (x0 - 1, x0 + 2, x0 + 5):
            m |= {(tx, 65 + dy), (tx + 1, 65 + dy)} if tx != x0 + 2 else {(tx, 65 + dy)}
        m |= {(x0 + 2, 65 + dy)}
        edge_shade(fig, m, o.skin)
        for (x, y) in m:          # the toe pads: one even tone, the middle toe as its foot
            if y == 65 + dy:
                fig.put(x, y, o.skin, 2)
        fig.put(x0 + 2, 65 + dy, o.skin, tone(fig, (x0 + 2, 64 + dy)))


def feet_side(fig, f, o, x_far=31, x_near=26, far_dark=True):
    for k, x0 in enumerate((x_far, x_near)):
        m = f.rect(fig, x0, 62, x0 + 4, 64, knock=1)
        m |= {f.p((x0 + 4, 65)), f.p((x0 + 5, 65)), f.p((x0 + 6, 65)), f.p((x0, 65)), f.p((x0 + 1, 65))}
        m |= {f.p((x0 + 5, 64))}
        edge_shade(fig, m, o.skin)
        if k == 0 and far_dark:
            for p in m:
                darken(fig, p, 1)


def legs_front(fig, o, xs=(27, 35), top=57, lift=None):
    for i, x0 in enumerate(xs):
        dy = -2 if lift == i else 0
        edge_shade(fig, fig.rect(x0, top, x0 + 2, 62 + dy), o.skin)


def legs_side(fig, f, o, x_far=32, x_near=27, top=57):
    for k, x0 in enumerate((x_far, x_near)):
        m = f.rect(fig, x0, top, x0 + 2, 62)
        edge_shade(fig, m, o.skin)
        if k == 0:
            for p in m:
                darken(fig, p, 1)


# --- hats --------------------------------------------------------------------------------
def flat_hat(fig, cx, y, fam='bleached', band='water', rx=12.5, keep=None):
    """A wide, flat woven sun hat seen from above: the brim's top is lit, its far rim a
    tone down, its front lip and underside dark; a low crown with a band."""
    brim = fig.ellipse(cx, y, rx, 2.7)
    by = {}
    for (x, yy) in brim:
        by.setdefault(x, []).append(yy)
    xs = [p[0] for p in brim]
    x0, x1 = min(xs), max(xs)
    for (x, yy) in brim:
        u = (x - x0) / max(1, x1 - x0)
        t = 4 if u < 0.42 else 3 if u < 0.8 else 2
        if yy == max(by[x]):
            t = 2 if u < 0.5 else 1
        elif yy == min(by[x]) and t > 3:
            t = 4
        fig.put(x, yy, fam, t)
    weave(fig, {p for p in brim if p[1] < max(by[p[0]])}, fam, phase=1)
    crown = fig.ellipse(cx, y - 3.3, 5.2, 3.4)
    pillow(fig, crown, fam)
    weave(fig, {p for p in crown if p[1] < y - 3}, fam)
    for (x, yy) in crown:
        if yy in (int(y - 1), int(y)) and (x, yy) in crown:
            fig.put(x, yy, band, 3 if x < cx - 1 else 2)
    if keep is not None:
        lx = min(p[0] for p in crown if p[1] == int(y - 1))
        fig.put(lx + 1, int(y - 1), band, 5)
        keep.add((lx + 1, int(y - 1)))
    return brim | crown


def cone_hat(fig, cx, y, fam='sand', rx=12, h=10, tip='timber'):
    """A conical woven hat: two planes (the west lit, the east in shade) with radial
    plaits, a rolled rim, a knot at the tip."""
    cone = fig.poly([(cx, y - h), (cx + rx + 0.5, y + 0.6), (cx - rx - 0.5, y + 0.6)])
    rim = fig.ellipse(cx, y + 0.5, rx + 0.5, 1.8)
    m = cone | rim
    for (x, yy) in m:
        u = x + 0.5 - cx
        t = 4 if u < -2 else 3 if u < 3 else 2
        fig.put(x, yy, fam, t)
    # radial plaits: lines from the tip to the rim, a tone down
    for k in (-8, -4, 0, 4, 8):
        fig.line([(int(cx), int(y - h + 2)), (int(cx + k * 1.15), int(y))], fam, 2)
    for (x, yy) in m:          # the plaits on the lit plane stay light
        if fam_at(fig, (x, yy)) == fam and tone(fig, (x, yy)) == 2 and x + 0.5 - cx < -2:
            fig.put(x, yy, fam, 3)
    rows = {}
    for (x, yy) in m:
        rows.setdefault(x, []).append(yy)
    for (x, yy) in m:          # rolled rim: underside dark, top lit on the west
        if yy == max(rows[x]):
            fig.put(x, yy, fam, 1)
        elif yy == max(rows[x]) - 1:
            fig.put(x, yy, fam, 4 if x + 0.5 - cx < 0 else 2)
    fig.fill(fig.rect(int(cx) - 1, int(y - h), int(cx), int(y - h)), tip, 3)
    fig.put(int(cx) - 1, int(y - h), tip, 4)
    return m


def flask(fig, cx, cy, rx=2.6, ry=3.2, keep=None, cork='timber'):
    """A gourd water flask (water family): a round belly, a narrow neck, a cork, and a
    two-pixel glint on the belly's lit cap."""
    body = fig.ellipse(cx, cy, rx, ry)
    top = min(p[1] for p in body)
    neck = fig.rect(int(cx) - 1, top - 2, int(cx), top)
    pillow(fig, body, 'water', cap=0.38)
    edge_shade(fig, neck, 'water')
    fig.put(int(cx) - 1, top - 3, cork, 4)
    fig.put(int(cx), top - 3, cork, 2)
    gx = min(p[0] for p in body if p[1] == top + 1) + 1
    fig.put(gx, top + 1, 'water', 5)
    fig.put(gx, top + 2, 'water', 5)
    if keep is not None:
        keep |= {(gx, top + 1), (gx, top + 2)}
    return body | neck


def hand(fig, x, y, fam):
    """A gecko hand: a 3 x 2 pad, lit at the top left."""
    return edge_shade(fig, fig.rect(x, y, x + 2, y + 1), fam)


# =====================================================================================
# Option A: sun-hat diviner
# =====================================================================================
A = Opt('A', 'adobe', 'bleached')
A_HAT = 'bleached_warm'


def a_smock_front(fig, hem=57):
    body = fig.poly([(26, 43.5), (39, 43.5), (41.5, hem + 1), (23.5, hem + 1)])
    cloth(fig, body, 'plaster', lit=2, dark=3, folds=(28, 36))
    for (x, y) in body:          # the woven water-blue hem band, two rows
        if y >= hem - 1:
            fig.put(x, y, 'water', 3 if y == hem - 1 else 2)
            if x <= 25:
                fig.put(x, y, 'water', 4 if y == hem - 1 else 3)
    fig.put(32, 44, 'plaster', 1)
    fig.put(32, 45, 'plaster', 1)
    return body


def a_sleeves_front(fig):
    for m in (fig.poly([(23.5, 44), (27.5, 44), (27.5, 48.5), (22.5, 48.5)]),
              fig.poly([(37.5, 44), (41.5, 44), (42.5, 48.5), (37.5, 48.5)])):
        cloth(fig, m, 'plaster', lit=1, dark=1)


def a_chin_cord(fig, cy):
    """The chin cord: from under the brim behind the cheeks, a loop under the chin."""
    for (x, y) in ((27, cy + 5), (28, cy + 6), (29, cy + 6), (30, cy + 6), (31, cy + 6), (32, cy + 6),
                   (33, cy + 6), (34, cy + 6), (35, cy + 6), (36, cy + 5)):
        fig.put(x, y, 'timber', 2)


def option_a(view):
    o = A
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        tube(fig, [(38, 59), (43, 61), (47, 60), (49, 57), (48, 54), (46, 54)], 2.4, 1.1, o.skin, bands=3)
        legs_front(fig, o)
        feet_front(fig, o, xs=(25, 34))
        a_smock_front(fig)
        flask(fig, 42, 55, 2.2, 2.6, keep)
        cy = 38 if not fid else 39
        if not fid:
            # hands together at her belly round the fork; the stem points out ahead of
            # her, up and to her right, so the Y reads outside the body
            tube(fig, [(25, 45), (26, 49), (29, 51)], 1.7, 1.5, o.skin)
            tube(fig, [(39, 45), (38, 49), (35, 51)], 1.7, 1.5, o.skin)
            a_sleeves_front(fig)
            rod_line(fig, (30, 50), (27, 48))
            rod_line(fig, (34, 51), (27, 48))
            rod_line(fig, (27, 48), (17, 42))
            hand(fig, 28, 50, o.skin)
            hand(fig, 33, 50, o.skin)
        else:
            # the rod dips: the stem swings down to the ground; she leans to follow it
            tube(fig, [(25, 45), (26, 50), (28, 53)], 1.7, 1.5, o.skin)
            tube(fig, [(39, 45), (38, 50), (34, 53)], 1.7, 1.5, o.skin)
            a_sleeves_front(fig)
            rod_line(fig, (29, 53), (26, 55))
            rod_line(fig, (33, 54), (26, 55))
            rod_line(fig, (26, 55), (19, 62))
            hand(fig, 27, 52, o.skin)
            hand(fig, 32, 52, o.skin)
        head_front(fig, o, keep, cy=cy, eyes='down' if fid else 'open')
        a_chin_cord(fig, cy)
        flat_hat(fig, 32.5, cy - 7, fam=A_HAT, keep=keep, rx=14)
    else:
        f = Face(1 if view == 'E' else -1)
        tail = tube(fig, [f.pc((27, 56)), f.pc((22, 59)), f.pc((18, 58)), f.pc((16, 55)), f.pc((17, 52)), f.pc((19, 52))],
             2.4, 1.1, o.skin, bands=3)
        if f.d == -1:     # in W the tail sweeps behind her on the shaded east flank
            for p in tail:
                darken(fig, p, 1)
        legs_side(fig, f, o)
        feet_side(fig, f, o, x_far=32, x_near=26)
        m = tube(fig, [f.pc((36, 47)), f.pc((39, 50)), f.pc((41, 50))], 1.4, 1.3, o.skin)
        for p in m:
            darken(fig, p, 1)
        body = fig.poly([f.pc((27, 43.5)), f.pc((37.5, 43.5)), f.pc((39.5, 58)), f.pc((25, 58))])
        cloth(fig, body, 'plaster', lit=2, dark=3, folds=(f.x(30), f.x(35)))
        for (x, y) in body:
            if y >= 56:
                fig.put(x, y, 'water', 3 if y == 56 else 2)
        if f.d == 1:      # the flask rides her left hip: near in E, hidden in W
            flask(fig, f.c(29.5), 54, 2.2, 2.6, keep)
        # the near arm: sleeve cap, forearm out level, hand under the fork
        tube(fig, [f.pc((32, 47)), f.pc((34, 51)), f.pc((40, 52))], 1.4, 1.3, o.skin)
        sl = fig.poly([f.pc((29.5, 44)), f.pc((34.5, 44)), f.pc((35.5, 49)), f.pc((30.5, 49))])
        cloth(fig, sl, 'plaster', lit=1, dark=1)
        hand(fig, f.x(40) if f.d == 1 else f.x(42), 51, o.skin)
        # the long Y-rod: the fork arms from the hands to the crotch, the stem forward
        rod_line(fig, f.p((42, 50)), f.p((46, 50)))
        rod_line(fig, f.p((42, 52)), f.p((46, 51)))
        rod_line(fig, f.p((46, 50)), f.p((57, 46)))
        head_side(fig, f, o, keep)
        flat_hat(fig, f.c(33), 31, fam=A_HAT, keep=keep, rx=14)
        fig.line([f.p((29, 35)), f.p((30, 42))], 'timber', 2)     # the chin cord
    fig.outline()
    despeckle(fig, keep)
    return fig


# =====================================================================================
# Option B: cone-hat pilgrim
# =====================================================================================
B = Opt('B', 'cactus', 'sand')


def b_wrap_front(fig, hem=57):
    body = fig.poly([(26, 43.5), (38.5, 43.5), (40.5, hem + 1), (24, hem + 1)])
    cloth(fig, body, 'adobe', lit=2, dark=3, folds=(29, 35))
    # the wrap's diagonal overlap and a sand sash
    fig.line([(28, 44), (35, 51)], 'adobe', 2)
    fig.line([(29, 44), (36, 51)], 'adobe', 4)
    for (x, y) in body:
        if y in (51, 52):
            fig.put(x, y, 'sand', 3 if y == 51 else 2)
            if x < 27:
                fig.put(x, y, 'sand', 4 if y == 51 else 3)
    return body


def b_twig(fig, base, tips, fam='timber'):
    """A short forked twig: a two-pixel grip, a knot at the fork, lit tips."""
    fx, fy = base[0], base[1] - 3
    rod_line(fig, base, (fx, fy), fam)
    for t in tips:
        fig.line([(fx, fy), t], fam, 4)
    fig.put(fx, fy, fam, 2)


def option_b(view):
    o = B
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        tube(fig, [(26, 59), (21, 61), (17, 60), (16, 57), (17, 55), (19, 55)], 2.3, 1.0, o.skin, bands=3)
        legs_front(fig, o)
        feet_front(fig, o)
        b_wrap_front(fig)
        if not fid:
            fig.line([(27, 44), (37, 51)], 'timber', 2)     # the flask strap
            flask(fig, 38, 55.5, 3.2, 3.4, keep)
            # her right arm (the viewer's left) out and up: the twig held forward, fork up
            tube(fig, [(25, 45), (23, 48), (22, 49)], 1.5, 1.3, o.skin)
            hand(fig, 20, 48, o.skin)
            b_twig(fig, (21, 48), [(18, 42), (24, 42)])
            tube(fig, [(39, 45), (41, 49), (42, 52)], 1.5, 1.3, o.skin)
            hand(fig, 41, 52, o.skin)
            head_front(fig, o, keep)
        else:
            # one slow sip: the flask up to her mouth in her left hand, eyes shut
            b_twig(fig, (24, 56), [(21, 51), (25, 50)])
            tube(fig, [(25, 45), (24, 51), (24, 55)], 1.5, 1.3, o.skin)
            hand(fig, 23, 55, o.skin)
            head_front(fig, o, keep, cy=37, eyes='closed')
            fig.line([(27, 44), (33, 46)], 'timber', 2)
            flask(fig, 35, 44.5, 3.0, 3.2, keep)
            tube(fig, [(40, 45), (40, 48), (38, 47)], 1.5, 1.3, o.skin)
            hand(fig, 37, 45, o.skin)
        cone_hat(fig, 32.5, 33 if not fid else 32, h=9)
    else:
        f = Face(1 if view == 'E' else -1)
        tail = tube(fig, [f.pc((27, 57)), f.pc((22, 60)), f.pc((18, 59)), f.pc((16, 56)), f.pc((17, 53)), f.pc((19, 53))],
             2.3, 1.0, o.skin, bands=3)
        if f.d == -1:     # in W the tail sweeps behind her on the shaded east flank
            for p in tail:
                darken(fig, p, 1)
        legs_side(fig, f, o)
        feet_side(fig, f, o, x_far=32, x_near=26)

        def twig_arm(dark):
            # her right arm: the far arm in E, the near one in W; the twig held forward
            m = tube(fig, [f.pc((34, 46)), f.pc((38, 49)), f.pc((41, 49))], 1.5, 1.3, o.skin)
            h = f.rect(fig, 40, 48, 42, 49)
            edge_shade(fig, h, o.skin)
            if dark:
                for p in m | h:
                    darken(fig, p, 1)
            b_twig(fig, f.p((41, 48)), [f.p((39, 42)), f.p((44, 42))])
        if f.d == 1:
            twig_arm(True)
        else:   # her left arm is the far one in W: it hangs behind, a tone back
            m = tube(fig, [f.pc((31, 46)), f.pc((30, 51))], 1.4, 1.2, o.skin)
            for p in m:
                darken(fig, p, 1)
        body = fig.poly([f.pc((27, 43.5)), f.pc((37.5, 43.5)), f.pc((39.5, 58)), f.pc((25, 58))])
        cloth(fig, body, 'adobe', lit=2, dark=3, folds=(f.x(31),))
        for (x, y) in body:
            if y in (51, 52):
                fig.put(x, y, 'sand', 3 if y == 51 else 2)
        # the big flask rides her belly on its strap: at the front in every facing
        fig.line([f.p((30, 44)), f.p((37, 51))], 'timber', 2)
        flask(fig, f.c(38.5), 55, 3.2, 3.4, keep)
        if f.d == -1:
            twig_arm(False)
        else:   # her left arm hangs, the hand on the flask
            tube(fig, [f.pc((31, 46)), f.pc((32, 51)), f.pc((34, 53))], 1.4, 1.3, o.skin)
            hand(fig, f.x(34), 53, o.skin)
        head_side(fig, f, o, keep)
        cone_hat(fig, f.c(33), 33, h=9)
    fig.outline()
    despeckle(fig, keep)
    return fig


# =====================================================================================
# Option C: dune traveller (lanky, bare-headed; the hat on her back)
# =====================================================================================
C = Opt('C', 'sand_cool', 'bleached')
C_COAT = 'earth'
C_ROD = 'earth'
C_HAT = 'bleached'


def c_coat_front(fig, top=39, hem=62):
    coat = fig.poly([(26.5, top - 0.5), (38, top - 0.5), (42, hem + 1), (23, hem + 1)])
    cloth(fig, coat, C_COAT, lit=2, dark=3, folds=(27, 37))
    for y in range(top + 6, hem + 1):     # the front opening of the duster
        fig.put(32, y, C_COAT, 1)
        fig.put(33, y, C_COAT, 2)
    for x in range(23, 43):               # belt
        if (x, 48) in coat:
            fig.put(x, 48, 'adobe', 3 if x < 28 else 2)
    return coat


def option_c(view):
    o = C
    fig = sk.Fig(W, H)
    keep = set()
    hy = 30            # head centre: she is lanky, the head carries no hat
    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        # back layer: the hat on her back (its brim shows round her), the rod on its strap
        hat = fig.ellipse(22.5, 51, 7.0, 6.5)     # the hat hung behind her right hip
        pillow(fig, hat, C_HAT, cap=0.3)
        weave(fig, hat, C_HAT)
        for (x, y) in fig.ellipse(21.5, 50.5, 3.4, 2.8):   # the crown's hollow, seen from behind
            fig.put(x, y, C_HAT, 2 if x < 21 else 1)
        fig.line([(25, 41), (23, 46)], 'adobe', 2)          # its cord from the scarf
        if not fid:
            rod_line(fig, (24, 58), (40, 33), C_ROD)
            rod_line(fig, (40, 33), (46, 27), C_ROD)
            rod_line(fig, (39, 33), (42, 24), C_ROD)
        else:   # the fork twitches and dips forward; she steadies the strap
            rod_line(fig, (24, 58), (40, 34), C_ROD)
            rod_line(fig, (40, 34), (47, 31), C_ROD)
            rod_line(fig, (40, 34), (45, 28), C_ROD)
        tube(fig, [(38, 60), (43, 62), (47, 61), (48, 58), (47, 56), (45, 56)], 2.3, 1.0, o.skin, bands=3)
        legs_front(fig, o, top=60)
        feet_front(fig, o)
        c_coat_front(fig)
        fig.line([(27, 49), (37, 40)], 'adobe', 2)       # the rod strap
        flask(fig, 37, 53.5, 2.8, 3.2, keep)
        if not fid:
            tube(fig, [(25, 41), (24, 47), (24, 50)], 1.5, 1.3, C_COAT)
            hand(fig, 23, 50, o.skin)
            tube(fig, [(39, 41), (40, 47), (40, 50)], 1.5, 1.3, C_COAT)
            hand(fig, 39, 50, o.skin)
        else:   # her left hand up at the strap by the shoulder
            tube(fig, [(25, 41), (24, 47), (24, 50)], 1.5, 1.3, C_COAT)
            hand(fig, 23, 50, o.skin)
            tube(fig, [(39, 41), (42, 43), (42, 39)], 1.5, 1.3, C_COAT)
            hand(fig, 41, 37, o.skin)
        head_front(fig, o, keep, cy=hy + (1 if fid else 0), brim=False, tilt=1 if fid else 0,
                   eyes='open')
        # the scarf: a thick wrap at the neck and its tail down her left front
        scarf = fig.ellipse(32.5, 38.3, 6.5, 2.0) | fig.poly([(27, 38.5), (30, 38.5), (29.5, 45), (26.5, 45)])
        cloth(fig, scarf, 'adobe', lit=2, dark=2)
        for x in range(28, 38, 3):
            fig.put(x, 38, 'adobe', 2)
            fig.put(x + 1, 38, 'adobe', 2)
    else:
        f = Face(1 if view == 'E' else -1)
        rod_line(fig, f.p((36, 60)), f.p((27, 33)), C_ROD)
        rod_line(fig, f.p((27, 33)), f.p((22, 27)), C_ROD)
        rod_line(fig, f.p((27, 33)), f.p((25, 24)), C_ROD)
        hat = fig.ellipse(f.c(24.5), 46, 2.8, 8.5)       # the hat on her back, edge on
        pillow(fig, hat, C_HAT, cap=0.3)
        weave(fig, hat, C_HAT)
        if f.d == -1:     # her back is the east flank in W: the hat sits in shade
            for p in hat:
                darken(fig, p, 1)
        tail = tube(fig, [f.pc((27, 59)), f.pc((22, 61)), f.pc((18, 60)), f.pc((16, 57)), f.pc((17, 55)), f.pc((19, 55))],
             2.3, 1.0, o.skin, bands=3)
        if f.d == -1:     # in W the tail sweeps behind her on the shaded east flank
            for p in tail:
                darken(fig, p, 1)
        legs_side(fig, f, o, top=60)
        feet_side(fig, f, o, x_far=32, x_near=26)
        m = tube(fig, [f.pc((35, 41)), f.pc((37, 46)), f.pc((38, 49))], 1.4, 1.2, C_COAT)
        for p in m:
            darken(fig, p, 1)
        coat = fig.poly([f.pc((27, 38.5)), f.pc((37.5, 38.5)), f.pc((40, 63)), f.pc((25, 63))])
        cloth(fig, coat, C_COAT, lit=2, dark=3, folds=(f.x(30),))
        for x in range(24, 42):
            q = f.p((x, 48))
            if q in coat:
                fig.put(q[0], q[1], 'adobe', 2)
        flask(fig, f.c(38.5), 53.5, 2.8, 3.2, keep)
        tube(fig, [f.pc((31, 41)), f.pc((31, 46)), f.pc((32, 49))], 1.5, 1.3, C_COAT)
        hand(fig, f.x(31) if f.d == 1 else f.x(33), 49, o.skin)
        head_side(fig, f, o, keep, cy=hy, brim=False)
        scarf = fig.ellipse(f.c(32), 37.5, 5.5, 2.2) | fig.poly([f.pc((27, 37)), f.pc((29, 37)), f.pc((25, 44)), f.pc((23, 43))])
        cloth(fig, scarf, 'adobe', lit=2, dark=2)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Sun-hat diviner: wide flat woven hat, linen smock, long Y-rod held forward',
        question='A wide, flat woven sun hat with a chin cord; the long Y-rod held forward in both hands.',
        fn=option_a, palette=['adobe', 'bleached', 'plaster', 'timber', 'water'],
        pose='Stands quite still, rod held out level in both hands, listening with her whole body for water.',
        parts=[
            'tail (adobe, banded): layer 0; hip; curls behind, sways 1 px against the walk, wraps her in the nap',
            'legs x2 (adobe) and splayed feet with toe pads: layer 1; hip; 6-frame walk, tuck in hop and nap',
            'smock (plaster, vertical folds, water hem band): layer 2; hip; breath 1 px, hem swings a frame late',
            'flask (water, timber cork): layer 3; her left hip; near in E, behind her in W; poured in cast',
            'sleeves and forearms x2 (plaster caps, adobe arms): layer 2 far / 4 near; chest; swing, wind-up, guard',
            'Y-rod (timber): layer 5, always in front; both hands; level in idle and walk, dips in fidget, swung as a strike, raised in cheer',
            'head (adobe, eye bumps, smile): layer 6; chest; tilts down in fidget, droops in nap',
            'sun hat (bleached weave, water band, timber chin cord): layer 7; head; lifts on hop, tips over her face in nap',
        ],
        notes=[
            'Works: the widest, flattest top in the cast (28 px brim), and the rod is the only long level line out front.',
            'Risk: the rod doubles her width in E/W and in walk frames; at the S view it must angle out to read.',
            'Brim kept flat and on her head, a band and weave rows, so it reads as a sun hat, not Puddle\'s sou\'wester.',
            'Compared with eastward-05 (the townsfolk at this height): one hard shadow row under the brim, 3 px eyes, 4 tones a garment.',
        ]),
    dict(
        label='B', name='Cone-hat pilgrim: conical woven hat, adobe wrap, forked twig and a big flask',
        question='A conical woven hat; a short forked twig in one hand; a big water flask at the belly.',
        fn=option_b, palette=['cactus', 'sand', 'adobe', 'timber', 'water'],
        pose='Small and patient under her cone, twig raised like a question, the full flask held close.',
        parts=[
            'tail (cactus, banded): layer 0; hip; curls behind, the tip flicks in react and cheer',
            'legs x2 (cactus) and splayed feet with toe pads: layer 1; hip; 6-frame walk, tuck in hop and nap',
            'wrap (adobe, crossover fold, sand sash): layer 2; hip; breath 1 px',
            'flask strap (timber): layer 3; chest; carries the flask in every facing',
            'big flask (water, two-pixel glint, timber cork): layer 4, at the front in every facing; belly strap; lifted to sip in fidget, poured in cast',
            'arms x2 (cactus): far arm layer 1, near arm layer 5; chest; swing, wind-up, guard',
            'forked twig (timber): in her right hand (far in E, near in W); hand; twitches in idle, points in cast, a switch in strike',
            'head (cactus, eye bumps, smile): layer 6; chest; tips back to sip',
            'cone hat (sand, radial plaits, rolled rim, timber knot): layer 7; head; bobs on hop, covers her face in nap',
        ],
        notes=[
            'Works: the cone is the only triangle-topped silhouette in the cast; the big blue flask is Seep at a glance.',
            'Risk: cactus green sits near Puddle\'s and Tam\'s leaf greens; the twig is small at 2 device px.',
            'The flask is centred on the belly so it keeps one anchor and layer in all facings.',
            'Compared with eastward-05: a woven hat drawn as two planes, the shade side a tone down, with a dark rim row.',
        ]),
    dict(
        label='C', name='Dune traveller: long duster and scarf, hat on her back, rod slung over the shoulder',
        question='Bare-headed; the flat sun hat hangs on her back and the Y-rod rides a strap, fork over the shoulder.',
        fn=option_c, palette=['sand', 'earth', 'adobe', 'bleached', 'water'],
        pose='Tall and unhurried, a long way from home and in no rush; the rod waits on her back until it twitches.',
        parts=[
            'Y-rod (earth): layer 0, on her back; strap over her left shoulder; the fork twitches in fidget, comes to both hands for cast and strike',
            'sun hat (bleached weave): layer 0, on her back; cord from the neck; swings a frame late in walk, a pillow in nap',
            'tail (sand, banded): layer 1; hip; curls out under the coat',
            'legs x2 (sand) and feet with toe pads: layer 1; hip; mostly hidden: the walk reads from the coat hem',
            'duster (earth, vertical folds, adobe belt, front opening): layer 2; chest; the hem sways in walk and hit',
            'flask (water, glint): layer 3; belt front; same in every facing; poured in cast',
            'sleeves x2 (earth) with sand hands: far 1 tone back; chest; swing, guard, steadying the strap in fidget',
            'head (sand, leopard spots, eye bumps, smile): layer 5; chest',
            'scarf (adobe, wrap and a tail at her right front): layer 6; chest; the tail flutters in hit and cheer',
        ],
        notes=[
            'Works: the only lanky, bare-headed folk; the dark duster gives the strongest two-value read of the three.',
            'Risk: no hat on her head loses the wide-hat cue; from the front the hat on her back reads as a pack.',
            'Rod on her back keeps the hands free for the rig, but the dowsing reads only when it comes off her back.',
            'Compared with eastward-05: the long coat as vertical fold bands with a 1 px placket, and the bare head with 3 px eyes.',
        ]),
]


# =====================================================================================
# FINAL (revision round, 21 Oct): option B, the cone-hat pilgrim, with grafts.
#   - skin from cactus green to warm sand (clear of Puddle, Tam and the green familiar);
#     the cone moves to bleached straw so hat, skin and wrap sit on three values.
#   - B's big front flask stays her signature (one anchor, the belly strap, front layer).
#   - from C: the tail curled tight against her legs, about 8 px behind the heel.
#   - from A: the forked Y-rod, only in strike and cast; idle carries the short twig.
#   - from C (craft): the wrap in vertical fold bands with a scalloped hem, 4 tones.
#   - fixes: two solid feet under the wrap (no toe clusters that read as four legs);
#     the cone narrowed to 19 px so the back-shoulder perch stays clear.
# =====================================================================================
FN = Opt('final', 'sand', 'bleached')
F_WRAP = 'adobe'
F_HAT = 'bleached'
F_SASH = 'bleached'


def f_wrap(fig, mask, folds):
    """The wrap: vertical fold bands (4 tones), a scalloped hem (2 px lobes)."""
    cloth(fig, mask, F_WRAP, lit=2, dark=3, folds=folds)
    rows = {}
    for (x, y) in mask:
        rows.setdefault(x, []).append(y)
    for x, ys in rows.items():
        b = max(ys)
        if (x // 2) % 2 == 1 and len(ys) > 3:     # every other 2 px lobe rides a row higher
            fig.px.pop((x, b), None)
            fig.put(x, b - 1, F_WRAP, 1)


def f_feet_front(fig, xs=(25, 34), dy=0):
    """Two solid gecko feet, each one rounded pad 5 px wide: a lit top-left toe pad, the
    toes only as a shaded front row, so they never read as extra legs."""
    for x0 in xs:
        m = fig.rect(x0, 63 + dy, x0 + 4, 65 + dy, knock=1)
        edge_shade(fig, m, FN.skin)
        for x in range(x0 + 1, x0 + 4):
            fig.put(x, 65 + dy, FN.skin, 2)
        fig.put(x0, 63 + dy, FN.skin, 4) if (x0, 63 + dy) in m else None
        fig.put(x0 + 1, 63 + dy, FN.skin, 4)


def f_tail_front(fig, side=1):
    """The tail curled tight round her ankle on her left (screen right)."""
    return tube(fig, [(37, 57), (41, 58), (43, 60.5), (42, 63), (39.5, 63)], 2.0, 1.1, FN.skin, bands=3)


def f_twig(fig, hand, d=1, up=True):
    """The short forked twig held upright in the hand: a 2 px grip, a knot, two tips."""
    hx, hy = hand
    b_twig(fig, (hx, hy), [(hx - 2, hy - 7), (hx + 2, hy - 7)])


def f_rod(fig, f, hand, mode):
    """The Y-rod (from A), only for strike and cast. strike: held by the stem, the fork
    forward like a switch; cast: raised, the fork up, two water drops at the tips."""
    hx, hy = hand
    if mode == 'strike':
        tip = (hx + f.d * 6, hy - 1)
        rod_line(fig, (hx - f.d * 2, hy + 1), tip)
        rod_line(fig, tip, (tip[0] + f.d * 5, tip[1] - 3))
        rod_line(fig, tip, (tip[0] + f.d * 5, tip[1] + 2))
        return []
    top = (hx, hy - 7)
    rod_line(fig, (hx, hy + 1), top)
    a, b = (hx - 3, hy - 11), (hx + 3, hy - 11)
    fig.line([top, a], 'timber', 4)
    fig.line([top, b], 'timber', 4)
    drops = []
    for (x, y) in (a, b):
        fig.put(x, y - 2, 'water', 4)
        fig.put(x, y - 3, 'water', 5)
        drops += [(x, y - 2), (x, y - 3)]
    return drops


def mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = fig.ellipse(cx, base - 5, 7.5, 5.5)
        pillow(fig, body, 'leaf')
        for x in (cx - 3, cx + 1):
            fig.put(x, base - 6, 'ink', 0)
            fig.put(x + 1, base - 6, 'ink', 0)
        for (x, y, t) in ((cx + 4, base - 11, 4), (cx + 5, base - 11, 4), (cx + 6, base - 10, 3), (cx + 5, base - 12, 4)):
            fig.put(x, y, 'leaf_warm', t)
        return keep
    body = fig.ellipse(cx, base - 9, 8, 9)
    pillow(fig, body, 'leaf')
    ey = base - 11
    for ex in ((cx, cx + 4) if d == 1 else (cx - 5, cx - 1)):
        for (x, y) in ((ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)):
            fig.put(x, y, 'ink', 0)
    top = base - 18
    fig.put(cx, top, 'leaf_warm', 3)
    fig.put(cx, top - 1, 'leaf_warm', 3)
    for (x, y, t) in ((cx - 1, top - 2, 4), (cx - 2, top - 2, 4), (cx - 2, top - 3, 4),
                      (cx + 1, top - 2, 3), (cx + 2, top - 2, 2), (cx + 2, top - 3, 3)):
        fig.put(x, y, 'leaf_warm', t)
    return keep


def final_front(view):
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    f_tail_front(fig)
    for x0 in (27, 34):
        edge_shade(fig, fig.rect(x0, 57, x0 + 2, 63), FN.skin)
    f_feet_front(fig, xs=(25, 33))
    body = fig.poly([(26, 43.5), (38.5, 43.5), (40.5, 58), (24, 58)])
    f_wrap(fig, body, folds=(29, 32, 36))
    fig.line([(28, 44), (35, 51)], F_WRAP, 1)        # the wrap's crossover
    fig.line([(29, 44), (36, 51)], F_WRAP, 4)
    for (x, y) in sorted(body):
        if y in (50, 51):
            fig.put(x, y, F_SASH, (4 if x < 28 else 3) if y == 50 else 2)
    if not fid:
        fig.line([(27, 44), (37, 51)], 'timber', 2)     # the flask strap
        flask(fig, 37.5, 55, 3.2, 3.4, keep)
        tube(fig, [(25, 45), (23, 48), (22, 50)], 1.5, 1.3, FN.skin)        # right arm, twig hand
        f_twig(fig, (21, 49))
        hand(fig, 20, 49, FN.skin)
        tube(fig, [(39, 45), (41, 49), (41, 52)], 1.5, 1.3, FN.skin)        # left hand on the flask
        hand(fig, 40, 52, FN.skin)
        head_front(fig, FN, keep, cy=38, smile_dy=-1)
        cone_hat(fig, 32.5, 33, fam=F_HAT, rx=9, h=9)
    else:   # one slow sip: the flask up to her mouth in her left hand, eyes shut, twig low
        f_twig(fig, (24, 57))
        tube(fig, [(25, 45), (24, 51), (24, 56)], 1.5, 1.3, FN.skin)
        hand(fig, 23, 56, FN.skin)
        head_front(fig, FN, keep, cy=37, eyes='closed', smile_dy=-1)
        fig.line([(27, 44), (33, 46)], 'timber', 2)
        flask(fig, 35, 44.5, 3.0, 3.2, keep)
        tube(fig, [(40, 45), (40, 48), (38, 47)], 1.5, 1.3, FN.skin)
        hand(fig, 37, 45, FN.skin)
        cone_hat(fig, 32.5, 32, fam=F_HAT, rx=9, h=8)
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


POSES = {
    #          body u/y  head u/y  legs       right hand   left hand   eyes      prop
    'idle':   (0, 0,     0, 0,    'stand',   (7, 49),     (5, 53),    'open',   'twig'),
    'ready':  (0, 1,     1, 0,    'wide',    (8, 47),     (6, 50),    'open',   'twig'),
    'strike': (3, 1,     3, 1,    'lunge',   (11, 47),    (4, 51),    'open',   'strike'),
    'cast':   (0, 0,     -1, -1,  'wide',    (12, 41),    (6, 52),    'open',   'cast'),
    'hit':    (-3, 0,    -4, -1,  'stumble', (3, 44),     (1, 46),    'closed', 'twig'),
    'sit':    (0, 6,     1, 0,    'sit',     (7, 54),     (5, 55),    'down',   'twig'),
    'cheer':  (0, -4,    0, -1,   'jump',    (6, 35),     (-3, 36),   'closed', 'twig'),
}


def final_side(d, pose, familiar=False):
    bu, by, hu, hy, legs, rh, lh, eyes, prop = POSES[pose]
    fig = sk.Fig(W, H)
    keep = set()
    f = Face(d, bu)                 # the body
    fh = Face(d, bu + hu)           # the head
    U = lambda u: f.x(AX + u)       # noqa: E731  (forward is +u in either facing)
    perch = None
    if familiar:   # the back shoulder, away from the foe; drawn first, behind her
        perch = (U(-7), 44 + by)
        mossling(fig, U(-14), perch[1] + 1, d, keep)
    hip = 57 + by
    # the tail curled tight behind the heel (from C)
    tail = tube(fig, [f.pc((AX - 5, hip)), f.pc((AX - 8, hip + 3)), f.pc((AX - 9, 62)),
                      f.pc((AX - 7, 64)), f.pc((AX - 5, 64))] if legs != 'sit' else
                [f.pc((AX - 5, hip + 1)), f.pc((AX - 9, hip + 3)), f.pc((AX - 9, hip + 6)), f.pc((AX - 6, hip + 7))],
                2.0, 1.1, FN.skin, bands=3)
    if d == -1:
        for p in tail:
            darken(fig, p, 1)
    lg = {'stand': [((-2, hip), (-2, 63)), ((1, hip), (1, 63))],
          'wide': [((-2, hip), (-4, 63)), ((1, hip), (3, 63))],
          'lunge': [((-2, hip), (-7, 63)), ((2, hip), (6, 63))],
          'stumble': [((-2, hip), (-5, 63)), ((1, hip), (4, 61))],
          'sit': [((0, hip - 2), (6, hip - 1)), ((2, hip - 1), (8, hip))],
          'jump': [((-2, hip), (-3, hip + 4)), ((1, hip), (3, hip + 4))]}[legs]

    def leg(i, a, b):
        m = tube(fig, [(U(a[0]), a[1]), (U(b[0]), b[1])], 1.5, 1.4, FN.skin)
        ft = fig.rect(min(U(b[0] - 1), U(b[0] + 3)), b[1] + 1, max(U(b[0] - 1), U(b[0] + 3)), b[1] + 2, knock=1) \
            if legs != 'sit' else fig.rect(min(U(b[0]), U(b[0] + 1)), b[1] - 2, max(U(b[0]), U(b[0] + 1)), b[1] + 1)
        edge_shade(fig, ft, FN.skin)
        if i == 0:
            for p in m | ft:
                darken(fig, p, 1)
    if legs != 'sit':
        for i, (a, b) in enumerate(lg):
            leg(i, a, b)

    def arm(hand_u, far):
        hx, hyy = U(hand_u[0]), hand_u[1] + (by if pose not in ('cast', 'cheer') else 0)
        m = tube(fig, [(U(0), 46 + by), ((U(0) + hx) / 2, (46 + by + hyy) / 2 + 1), (hx, hyy)], 1.5, 1.3, FN.skin)
        hm = fig.rect(hx - 1, hyy - 1, hx + 1, hyy)
        edge_shade(fig, hm, FN.skin)
        if far:
            for p in m | hm:
                darken(fig, p, 1)
        return (hx, hyy)
    # her right hand holds the twig or the rod: the far hand in E, the near one in W
    right_far = d == 1
    drops = []

    def right():
        h = arm(rh, right_far)
        if prop == 'twig':
            f_twig(fig, (h[0], h[1] - 1))
        else:
            drops.extend(f_rod(fig, f, h, prop))
    if right_far:
        right()
    else:
        arm(lh, True)
    body = fig.poly([f.pc((AX - 5, 43.5 + by)), f.pc((AX + 5.5, 43.5 + by)),
                     f.pc((AX + 7, 58.5 + by)), f.pc((AX - 6.5, 58.5 + by))])
    f_wrap(fig, body, folds=(f.x(AX - 2), f.x(AX + 2)))
    for (x, y) in sorted(body):
        if y in (50 + by, 51 + by):
            fig.put(x, y, F_SASH, 3 if y == 50 + by else 2)
    fig.line([f.p((AX - 2, 44 + by)), f.p((AX + 5, 51 + by))], 'timber', 2)
    flask(fig, f.c(AX + 6.5), 54.5 + by, 3.0, 3.3, keep)
    if legs == 'sit':
        for i, (a, b) in enumerate(lg):
            leg(i, a, b)
    head_side(fig, fh, FN, keep, cy=38 + by + hy, eyes=eyes, look=1 if pose == 'strike' else 0)
    cone_hat(fig, fh.c(AX + 1), 33 + by + hy, fam=F_HAT, rx=9, h=9)
    if right_far:
        arm(lh, False)
    else:
        right()
    keep |= set(drops)
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig, perch


def final_nap():
    """nap_c, facing S: curled on her side in the wrap, the cone tipped over her eyes,
    the tail wrapped round the front, the flask hugged; the familiar curled at her back."""
    fig = sk.Fig(W, H)
    keep = set()
    mossling(fig, 46, SOLE + 1, 1, keep, curled=True)
    wrap = fig.ellipse(33, 58.5, 11.5, 6.5)
    cloth(fig, wrap, F_WRAP, lit=2, dark=3, folds=(31, 37))
    for (x, y) in sorted(wrap):
        if x in (34, 35):
            fig.put(x, y, F_SASH, 3 if x == 34 else 2)
    flask(fig, 30, 60, 2.6, 2.8, keep)
    # the tail wraps round the front of the curl
    tube(fig, [(43, 63), (36, 65), (28, 65), (23, 63)], 2.0, 1.2, FN.skin, bands=3)
    # head resting at the left, cheek on her hands, eyes shut under the tipped cone
    head = fig.ellipse(21.5, 59, 5.0, 4.0) | fig.ellipse(17.5, 60.5, 3.6, 2.6)
    pillow(fig, head, FN.skin, cap=0.5)
    for x in (18, 19, 20):
        fig.put(x, 62, FN.skin, 1)
    for x in (20, 21, 22):
        fig.put(x, 59, 'ink', 0)
    fig.put(20, 60, 'ink', 0)
    fig.put(22, 60, 'ink', 0)
    hand(fig, 24, 62, FN.skin)
    cone = cone_hat(fig, 24.5, 56, fam=F_HAT, rx=8, h=7)
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


FINAL_VIEWS = (
    ('S idle', lambda: (final_front('S'), None)),
    ('E idle', lambda: final_side(1, 'idle')),
    ('W idle', lambda: final_side(-1, 'idle')),
    ('S fidget', lambda: (final_front('Sf'), None)),
    ('nap S', lambda: (final_nap(), None)),
    ('E ready', lambda: final_side(1, 'ready', True)),
    ('E strike', lambda: final_side(1, 'strike', True)),
    ('E cast', lambda: final_side(1, 'cast', True)),
    ('E hit', lambda: final_side(1, 'hit', True)),
    ('E sit', lambda: final_side(1, 'sit', True)),
    ('E cheer', lambda: final_side(1, 'cheer', True)),
    ('W ready', lambda: final_side(-1, 'ready', True)),
    ('W strike', lambda: final_side(-1, 'strike', True)),
)

FINAL = dict(
    label='B final', name='Cone-hat pilgrim (final): sand gecko, adobe wrap, big front flask, twig and Y-rod',
    chosen='B',
    grafts=[
        'Skin moved from cactus green to warm sand (clear of Puddle, Tam and the green familiar); the cone moved '
        'from sand to bleached straw so skin, hat and wrap sit on three values.',
        'Kept from B: the big front flask on its belly strap, her Seep signature, one anchor and the front layer in every facing.',
        'From C: the tail curled tight round her heel (about 9 px behind it in E/W, at her ankle in S), clear of the '
        'familiar walking 28 px behind.',
        'From A: the forked Y-rod as the strike and cast prop, in her right hand only in those poses (strike: held by '
        'the stem, the fork forward as a switch; cast: raised, fork up, two water drops); in idle it is the short twig.',
        'From C (craft): the wrap in vertical fold bands (4 tones) with a scalloped hem.',
        'Fixes: two solid rounded feet under the wrap, no toe clusters; the cone narrowed from 25 to 19 px so the '
        'back-shoulder perch and the familiar\'s eyes stay clear.',
    ],
    palette=['sand', 'adobe', 'bleached', 'timber', 'water', 'leaf'],
    pose='Small and patient under her cone, a twig raised like a question, the full flask held close; '
         'she sips slowly when idle and pours, never guards, in a fight.',
    parts=[
        'familiar perch: back shoulder (E: x smaller, W: x larger), behind her and the cone; layer 0; chest',
        'tail (sand, banded): layer 1; hip; curled at the heel in every facing, tip flicks on react and cheer, wraps the front in nap',
        'far leg / far arm (sand, a tone back): layer 2; hip / chest; all facings',
        'right hand prop, twig or Y-rod (timber): her RIGHT hand in every facing (far in E, near in W, screen left in S); '
        'twig in idle/walk/ready/hit/sit/cheer, Y-rod in strike and cast',
        'near leg with a solid foot (sand): layer 3; hip; 6-frame walk, tuck in hop, forward in sit',
        'wrap (adobe, fold bands, scalloped hem, crossover, bleached sash): layer 4; hip; breath 1 px, hem sways a frame late',
        'flask strap (timber) and big flask (water, 2 px glint, timber cork): layer 5, front in every facing; belly strap; '
        'lifted to sip in fidget, tipped to pour in cast',
        'head (sand, eye bumps, smile, brow, cheek and snout step in profile): layer 6; chest; tips back to sip, droops in nap',
        'cone hat (bleached, radial plaits, rolled rim, timber knot; 19 px wide): layer 7; head; bobs on hop, tips over her eyes in nap',
        'near arm (sand): layer 8; chest; swing, guard, reach',
    ],
    notes=[
        'Compared side by side with eastward-05 at the same character height: the townsfolk there (the curly-haired '
        'woman, the bearded man in the green coat): 3 px eyes with a glint, 4 tones a garment, cloth as vertical bands.',
        'Works: the cone is the only triangle-topped folk; the blue flask is Seep at a glance; sand skin keeps the green '
        'Mossling readable on her shoulder.',
        'Risk: the twig is small at 2 device px; the dowsing read leans on the Y-rod in strike and cast.',
        'Palette: leaf is the stand-in familiar only.',
        'Open for the art director: whether the cast should end with the flask poured (a water arc effect) or with the '
        'rod\'s drops alone; and whether the twig should be drawn longer in walk frames.',
    ],
)


def build_final():
    views, nums, perches, ok = [], {}, {}, True
    for cap, fn in FINAL_VIEWS:
        fig, perch = fn()
        im = fig.image()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        print(f"final {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Mirra final (folk 9, Sunstone): B, the cone-hat pilgrim, with grafts', [entry], OUT_FINAL,
                    note='44 art px, cell 64 x 72, foot (32, 66). World S/E/W, fidget, nap; fight E and W with the '
                         'stand-in Mossling on the back shoulder.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], pose=FINAL['pose'], perch_anchor=perches, measure=nums,
                notes=FINAL['notes'], _ok=ok)


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
            g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                     colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
            ok &= all(g.values())
            print(f"{o['label']} {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
            nums[cap]['height_px'] = height(im)
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('Mirra (folk 9, Sunstone): gecko, hat and the dowsing rod\'s silhouette', OPTIONS, OUT_PNG,
                    note='44 art px, cell 64 x 72, foot (32, 66). Views: S, E, W idle and the S fidget key pose.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='mirra', height_art_px=44, cell=[W, H], foot=[AX, AY],
                       question='Gecko, hat and the dowsing rod\'s silhouette.', options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
