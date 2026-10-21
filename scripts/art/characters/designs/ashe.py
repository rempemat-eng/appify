"""Ashe, drake-folk knight of Hearthold: three design options (Claude J lane, batch 2).

Main question: how much armour and how much dragon.

    A  Dented plate: a full harness of dented iron, the visor raised on a horned helm to
       show the drake snout, small wings folded behind the pauldrons, the tail out from
       under the tassets with its last third gone ash grey.
    B  Half-plate drake: a breastplate and one big pauldron over a quilted ashlar gambeson,
       bare scaly arms (one forearm greying), a bare horned head with swept-back horns and
       a long tail with a banked ember at its tip.
    C  Hearth squire: a wide-brimmed iron kettle hat, a quilted ash surcoat with a small
       gorget and spaulders, a big brass bell at the belt and a short tail curled up behind
       with a glowing tip.

Views: S idle, E idle, W idle (W is drawn with its own light from the upper left, never
mirrored pixels) and the S key pose of each option's fidget. Design sheets are review
material; production frames come from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/ashe.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/ashe-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/ashe.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'ashe')

W, H = 64, 72
AX, AY = 32, 66          # foot anchor: soles fill row 65, their outline lands on row 66
SOLE = AY - 1
TOP = SOLE - 51          # 52 art px tall: the highest pixel sits on row 14
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def base(f):
    return sk.family_of(f) if f else f


class Pen:
    """A figure plus a facing. Coordinates are local (the character faces +x in profile);
    d = -1 maps them across the anchor for the W view. Only geometry is mapped: every
    shading pass runs afterwards on screen pixels, so the light stays at the upper left."""

    def __init__(self, d=1):
        self.fig = sk.Fig(W, H)
        self.d = d
        self.keep = set()

    def X(self, x):
        return x if self.d >= 0 else 2 * AX - 1 - x

    def m(self, mask):
        return {(self.X(x), y) for (x, y) in mask}

    def ell(self, cx, cy, rx, ry):
        return self.m(self.fig.ellipse(cx, cy, rx, ry))

    def rect(self, x0, y0, x1, y1, knock=0):
        return self.m(self.fig.rect(x0, y0, x1, y1, knock))

    def poly(self, pts):
        return self.m(self.fig.poly(pts))

    def put(self, x, y, fam, t, keep=False):
        x, y = int(round(x)), int(round(y))
        self.fig.put(self.X(x), y, fam, t)
        if keep:
            self.keep.add((self.X(x), y))

    def glow(self, x, y, t=3):
        x, y = int(round(x)), int(round(y))
        self.fig.glow(self.X(x), y, 'lava', t)
        self.keep.add((self.X(x), y))

    def tube(self, pts, radii):
        """A tapering tube along a polyline (a tail, a horn): the union of discs."""
        out = set()
        for (x0, y0), (x1, y1), (r0, r1) in zip(pts, pts[1:], zip(radii, radii[1:])):
            n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * 2))
            for i in range(n + 1):
                t = i / n
                cx, cy, r = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t
                out |= self.fig.ellipse(cx, cy, max(0.7, r), max(0.7, r))
        return self.m(out)


def extents(mask):
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    return ({y: (min(v), max(v)) for y, v in rows.items()}, {x: (min(v), max(v)) for x, v in cols.items()})


def pillow(fig, mask, fam, lift=0, glint=False):
    """A round part (a head, a pauldron, a bell): the lit cap is a disc offset to the upper
    left and the dark crescent the outside of a larger offset disc, so the terminator
    follows the form instead of stepping across it in a straight diagonal."""
    mask = set(mask)
    if not mask:
        return mask
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 3
        if (u + 0.42) ** 2 + (v + 0.5) ** 2 < 0.42:
            t = 4
        if (u + 0.28) ** 2 + (v + 0.32) ** 2 > 1.05:
            t = 2
        if (x, y + 1) not in mask and (u > -0.3):
            t = min(t, 1 if u > 0.2 else 2)
        fig.put(x, y, fam, max(0, min(5, t + lift)))
    if glint:
        top = sorted(mask, key=lambda p: ((p[0] - cx) / rx * 0.55 + (p[1] - cy) / ry * 0.85, p[0], p[1]))
        best = top[0]
        for q in (best, (best[0] + 1, best[1])):
            if q in mask:
                fig.put(q[0], q[1], fam, 5)
    return mask


def plate(fig, mask, fam, lift=0, glint=True, sheen=True):
    """Metal plate (house-style 5): square shoulders, a lit top row and west column, a slow
    sheen at the upper left, a shaded east band two pixels wide and a dark last row."""
    mask = set(mask)
    if not mask:
        return mask
    rows, cols = extents(mask)
    for (x, y) in mask:
        xl, xr = rows[y]
        yt, yb = cols[x]
        wdt = xr - xl + 1
        t = 3
        # a highlight band in the left third (a pipe, a greave, a lame seen end on)
        if sheen and 0 < x - xl <= max(1, wdt // 3):
            t = 4
        if x == xl and wdt > 3:
            t = 3
        if xr - x < (2 if wdt > 4 else 1):
            t = 2
        if y == yt and t >= 3:
            t = 4
        if y == yb and yb - yt >= 2:
            t = min(t, 2) if x - xl < wdt // 2 else 1
        fig.put(x, y, fam, max(0, min(5, t + lift)))
    if glint:
        tl = sorted(mask, key=lambda p: (p[0] + p[1], p[0]))[0]
        tl = (tl[0] + 1, tl[1])
        for q in (tl, (tl[0], tl[1] + 1)):
            if q in mask:
                fig.put(q[0], q[1], fam, 5)
    return mask


def cloth(fig, mask, fam, lit=2, dark=2, folds=(), lift=0, top=True, bottom=True):
    """Cloth in vertical bands: a lit west band, the body, a shaded east band, a lit top
    row and a dark hem row. `folds` are x columns of tone 2 with a lit lip to the west."""
    mask = set(mask)
    rows, cols = extents(mask)
    for (x, y) in mask:
        xl, xr = rows[y]
        t = 3
        if x - xl < lit:
            t = 4
        elif xr - x < dark:
            t = 2
        if top and y == cols[x][0] and t >= 3:
            t = 4
        if bottom and y == cols[x][1]:
            t = 1
        fig.put(x, y, fam, max(0, min(5, t + lift)))
    for fx in folds:
        for (x, y) in mask:
            if x == fx and cols[x][0] + 1 < y < cols[x][1]:
                fig.put(x, y, fam, max(1, 2 + lift))
    return mask


def quilt(fig, mask, fam, step=4, y0=0):
    """Quilting: a stitched channel every `step` rows (tone 2) with the puffed row under it
    lit (tone 4 on the west half), so the gambeson reads as stuffed bands, not stripes."""
    rows, _ = extents(mask)
    for (x, y) in mask:
        if fam_at(fig, (x, y)) is None or base(fam_at(fig, (x, y))) != base(fam):
            continue
        r = (y - y0) % step
        xl, xr = rows[y]
        t = tone(fig, (x, y))
        if r == 0 and xl < x < xr:
            fig.put(x, y, fam, max(1, min(t, 3) - 1))
        elif r == 1 and xl < x < (xl + xr) / 2 and t == 3:
            fig.put(x, y, fam, 4)


def scales(fig, mask, fams=('clay', 'ash'), step=3):
    """Scales as staggered two-pixel scallops a tone down (a scale's shaded lower edge),
    the row above each lit on the west half: rows of small overlapping plates."""
    rows, _ = extents(mask)
    for (x, y) in sorted(mask):
        f = fam_at(fig, (x, y))
        if f is None or base(f) not in fams:
            continue
        t = tone(fig, (x, y))
        if t is None or t < 2 or t > 4:
            continue
        r = y % step
        off = ((y // step) % 2) * 2
        if r == 0 and (x + off) % 4 in (1, 2):
            fig.put(x, y, f, t - 1)


def grey(fig, mask, frm='clay', to='ash'):
    """Embers going grey as she rests: the scale family turns to ash at the same tone."""
    for p in mask:
        f = fam_at(fig, p)
        if f and base(f) == frm:
            suffix = f[len(frm):]
            fig.put(p[0], p[1], to + suffix, tone(fig, p))


def dent(pen, x, y, fam, w=3):
    """A dent: a dark upper crescent (the inner wall facing away from the light) over a lit
    lower lip (the inner wall facing up into it)."""
    for i in range(w):
        pen.put(x + i, y, fam, 1)
    pen.put(x - 1, y + 1, fam, 2)
    for i in range(w):
        pen.put(x + i, y + 1, fam, 4)


def rivet(pen, x, y, fam='brass'):
    pen.put(x, y, fam, 5, keep=True)
    pen.put(x, y + 1, fam, 1, keep=True)


def bell(pen, cx, top, big=False, tilt=0):
    """The bedtime bell: a domed crown, a flared lip, a dark mouth and a clapper."""
    if big:
        rows = [(-1, 1), (-2, 2), (-2, 2), (-3, 2), (-3, 3), (-3, 3), (-4, 4)]
    else:
        rows = [(-1, 1), (-2, 1), (-2, 2), (-2, 2), (-3, 3)]
    m = set()
    for j, (a, b) in enumerate(rows):
        for x in range(cx + a + (tilt if j < 2 else 0), cx + b + 1 + (tilt if j < 2 else 0)):
            m.add((x, top + j))
    m = pen.m(m)
    pillow(pen.fig, m, 'brass')
    rr, _ = extents(m)
    for y, (xl, xr) in rr.items():
        if y == top + len(rows) - 1:
            for x in range(xl, xr + 1):
                pen.fig.put(x, y, 'brass', 2)
            pen.fig.put(xl, y, 'brass', 3)
            pen.fig.put(xr, y, 'brass', 1)
    # a waist band one row above the lip
    yb = top + len(rows) - 3
    xl, xr = rr[yb]
    for x in range(xl + 1, xr):
        pen.fig.put(x, yb, 'brass', max(1, tone(pen.fig, (x, yb)) - 1))
    # the glint, two pixels at the crown's upper left
    xl, _ = rr[top + 1]
    pen.fig.put(xl, top + 1, 'brass', 5)
    pen.fig.put(xl, top + 2, 'brass', 5)
    pen.keep |= {(xl, top + 1), (xl, top + 2)}
    # clapper under the mouth
    pen.put(cx, top + len(rows), 'brass', 1, keep=True)
    pen.put(cx + 1 if pen.d >= 0 else cx - 1, top + len(rows), 'brass', 0, keep=True)
    return m


def despeckle(fig, keep):
    """No speckle: a pixel unlike all four neighbours takes its most common neighbour,
    unless it is an eye, a glint, a rivet or an ember (`keep`). Ties break by a fixed
    order so the output is byte-identical across runs."""
    for _ in range(2):
        changes = {}
        for p in sorted(fig.px):
            v = fig.px[p]
            if p in keep or p in fig.fixed or v[0] in ('ink', '_edge', '_lit'):
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if all(n != v for n in nb):
                pool = [n for n in nb if n[0] not in ('ink', '_edge', '_lit')]
                if not pool:
                    continue
                same = [n for n in pool if base(n[0]) == base(v[0])]
                if same:
                    pool = same
                changes[p] = max(sorted(set(pool), key=str), key=pool.count)
        for p, v in changes.items():
            fig.px[p] = v


def finish(pen):
    pen.fig.outline()
    despeckle(pen.fig, pen.keep)
    return pen.fig


# --- shared drake parts ------------------------------------------------------------------
def eyes_front(pen, y, xl=27, xr=35, mode='open', fam='clay'):
    """Drake eyes: ink 2 x 3 with a brass glint (an ember catch-light), a brow above in the
    scale's own tone 1. 'shut' draws contented arcs, 'down' a lowered lid, 'squint' a slit."""
    for ex in (xl, xr):
        if mode == 'open':
            for dy in range(3):
                pen.put(ex, y + dy, 'ink', 0)
                pen.put(ex + 1, y + dy, 'ink', 0)
            pen.put(ex, y, 'brass', 5, keep=True)
        elif mode == 'down':
            for dy in (1, 2):
                pen.put(ex, y + dy, 'ink', 0)
                pen.put(ex + 1, y + dy, 'ink', 0)
            pen.put(ex, y, fam, 1, keep=True)
            pen.put(ex + 1, y, fam, 1, keep=True)
        elif mode == 'squint':
            pen.put(ex, y + 1, 'ink', 0)
            pen.put(ex + 1, y + 1, 'ink', 0)
            pen.put(ex + (2 if ex == xl else -1), y + 1, 'ink', 0)
        else:  # shut: a smiling arc
            pen.put(ex, y + 1, 'ink', 0)
            pen.put(ex + 1, y + 1, 'ink', 0)
            pen.put(ex - 1 if ex == xl else ex + 2, y + 2, 'ink', 0)
            pen.put(ex + 2 if ex == xl else ex - 1, y + 2, fam, 2)
        # brow: a short ridge sloping down to the snout (a determined knight)
        if ex == xl:
            pen.put(ex - 1, y - 2, fam, 2)
            pen.put(ex, y - 1, fam, 1)
            pen.put(ex + 1, y - 1, fam, 1)
            pen.put(ex + 2, y - 1, fam, 2)
        else:
            pen.put(ex - 1, y - 1, fam, 2)
            pen.put(ex, y - 1, fam, 1)
            pen.put(ex + 1, y - 1, fam, 1)
            pen.put(ex + 2, y - 2, fam, 2)


def muzzle_front(pen, cy, dx=0, fam='clay', w=4.6, h=3.0):
    """The snout seen from the front: a rounded block, its top row lit, the east third a
    tone down, two nostril slits, the mouth as a tone-1 line turning up at each end."""
    cx = 31.5 + dx
    m = pen.ell(cx, cy, w, h)
    top = {}
    for (x, y) in m:
        top[x] = min(top.get(x, 99), y)
    for (x, y) in m:
        nt = 4 if y == top[x] else 3
        if x > cx + 1.5:
            nt -= 1
        if y == max(q[1] for q in m if q[0] == x):
            nt = min(nt, 2)
        pen.fig.put(x, y, fam, nt)
    yt = min(p[1] for p in m)
    for x, t in ((29, 0), (34, 0), (30, 0), (33, 0)):
        pen.put(x + dx, yt + 1, fam, t, keep=True)
    yb = max(p[1] for p in m)
    for x in range(29, 35):
        pen.put(x + dx, yb - 1, fam, 1)
    pen.put(28 + dx, yb - 2, fam, 1)
    pen.put(35 + dx, yb - 2, fam, 1)
    return m


def eye_side(pen, x, y, mode='open', fam='clay'):
    """Profile eye: ink 2 x 3 under a brow ridge (the step from skull to snout, lit on
    top), the glint on its lit side."""
    if mode == 'open':
        for dy in range(3):
            pen.put(x, y + dy, 'ink', 0)
            pen.put(x + 1, y + dy, 'ink', 0)
        pen.put(x + 1 if pen.d < 0 else x, y, 'brass', 5, keep=True)
    else:
        pen.put(x, y + 1, 'ink', 0)
        pen.put(x + 1, y + 1, 'ink', 0)
    for i in range(-1, 4):
        pen.put(x + i, y - 1, fam, 1 if i >= 0 else 2)
    for i in range(0, 4):
        pen.put(x + i, y - 2, fam, 4)


def snout_side(pen, x0, y0, x1, y1, fam='clay'):
    """Profile snout: its top plane lit, a lit bridge, the jaw seam in tone 1 rising to a
    smile at the back, a nostril nick near the tip, the chin a shaded underside."""
    m = pen.rect(x0, y0, x1, y1, knock=2)
    for (sx, y) in m:
        t = 3
        if y <= y0 + 1:
            t = 4
        if y >= y1 - 1:
            t = 2
        if y == y1:
            t = 1
        pen.fig.put(sx, y, fam, t)
    for x in range(x0 + 1, x1):
        pen.put(x, y1 - 2, fam, 1)
    pen.put(x0, y1 - 3, fam, 1)
    pen.put(x1 - 1, y0 + 1, fam, 0, keep=True)
    pen.put(x1 - 2, y0 + 1, fam, 1, keep=True)
    return m


def tail(pen, pts, radii, fam='clay', grey_from=None, ember=None):
    """The tail as a tapering tube with scale rows; `grey_from` turns everything past that
    local x to ash (the embers greying), `ember` is one banked glow between the scales."""
    m = pen.tube(pts, radii)
    pillow(pen.fig, m, fam)
    # the top ridge: a lit row along the upper edge of each column
    cols = {}
    for (x, y) in m:
        cols[x] = min(cols.get(x, 99), y)
    for x, y in cols.items():
        t = tone(pen.fig, (x, y))
        if t is not None and t < 4 and (x, y + 1) in m:
            pen.fig.put(x, y, fam, t + 1)
    scales(pen.fig, m)
    if grey_from is not None:
        sgn = 1 if pts[-1][0] > grey_from else -1
        sel = {p for p in m if (p[0] - pen.X(grey_from)) * sgn * (1 if pen.d >= 0 else -1) >= 0}
        grey(pen.fig, sel)
    if ember is not None:
        pen.glow(ember[0], ember[1], 3)
    return m


def greave(pen, x0, y0, x1, y1, fam, lift=0):
    """A greave or vambrace: a short cylinder, highlight band in its left third."""
    return plate(pen.fig, pen.rect(x0, y0, x1, y1), fam, lift=lift, glint=False)


# --- option A: dented plate, visor up, wings folded ---------------------------------------
def a_front(pose='idle'):
    pen = Pen(1)
    f = pen.fig
    fid = pose == 'fidget'
    sh = -2 if fid else 0         # the rolled (screen-left) shoulder rises
    tilt = -1 if fid else 0       # and the head leans to it
    # wings folded behind the pauldrons (back layer)
    for s in (-1, 1):
        lift = sh if s < 0 else 0
        pts = [(23, 37), (18, 29), (15, 26), (15, 31), (17, 36), (20, 40)]
        bone = [(16, 27), (17, 28), (17, 29), (18, 30)]
        crease = [(17, 33), (18, 34)]
        if s > 0:
            pts = [(63 - x, y) for x, y in pts]
            bone = [(63 - x, y) for x, y in bone]
            crease = [(63 - x, y) for x, y in crease]
        wing = pen.poly([(x, y + lift) for x, y in pts])
        pillow(f, wing, 'clay_cool', lift=-1)
        for (x, y) in bone:
            f.put(x, y + lift, 'ash', 4 if s < 0 else 3)
        for (x, y) in crease:
            f.put(x, y + lift, 'clay_cool', 0)
    # tail behind the legs, out to screen right, curling up at its grey end
    tail(pen, [(37, 54), (41, 58), (45, 60), (49, 60), (52, 58), (53, 54), (51, 52)],
         [3.0, 2.6, 2.1, 1.7, 1.3, 1.0, 0.7], grey_from=48, ember=(42, 58))
    # legs: cuisses, knee cops, greaves, sabatons
    for x0 in (26, 33):
        greave(pen, x0, 53, x0 + 4, 56, 'slate')
        pillow(f, pen.rect(x0, 56, x0 + 4, 58, knock=1), 'slate_warm', glint=False)
        greave(pen, x0, 59, x0 + 4, 61, 'slate_cool')
        sab = pen.rect(x0 - 1, 62, x0 + 5, 65, knock=1)
        plate(f, sab, 'iron', glint=False)
    # tassets: one broad lame over a narrower one, each side
    for x0, x1 in ((23, 31), (32, 40)):
        plate(f, pen.rect(x0 + 1, 51, x1 - 1, 53, knock=1), 'iron', glint=False)
        plate(f, pen.rect(x0, 48, x1, 50, knock=1), 'slate_warm', glint=False)
    plate(f, pen.rect(24, 46, 39, 47), 'iron', glint=False, sheen=False, lift=-1)
    for x in (31, 32):
        f.put(x, 46, 'brass', 4 if x == 31 else 3)
        f.put(x, 47, 'brass', 2)
    # cuirass with a centre ridge and two dents
    cu = pen.poly([(25, 34), (39, 34), (41, 40), (39, 46), (25, 46), (23, 40)])
    pillow(f, cu, 'slate', glint=True)
    for y in range(36, 45):
        f.put(31, y, 'slate', 4)
        f.put(32, y, 'slate', 2)
    dent(pen, 27, 40, 'slate')
    dent(pen, 35, 37, 'slate', w=2)
    # arms: vambrace, couter, vambrace, gauntlet (the rolled arm rides up with its shoulder)
    for s, x0 in ((-1, 18), (1, 40)):
        lift = sh if s < 0 else 0
        greave(pen, x0 + 1, 41 + lift, x0 + 5, 44 + lift, 'slate')
        pillow(f, pen.rect(x0, 44 + lift, x0 + 5, 46 + lift, knock=1), 'iron', glint=False)
        greave(pen, x0 + 1, 47 + lift, x0 + 5, 49 + lift, 'slate_cool')
        g = pen.rect(x0, 50 + lift, x0 + 5, 53 + lift, knock=1)
        pillow(f, g, 'iron')
        for x in range(x0 + 1, x0 + 5):
            if x % 2 == 0:
                f.put(x, 52 + lift, 'iron', 1)       # finger seams
    # the bedtime bell at the belt front, her left
    for y in (48, 49):
        f.put(37, y, 'iron', 1)
    bell(pen, 37, 50)
    # pauldrons: domed, a lower lame, a dent and a rivet each
    for s, cx in ((-1, 22.5), (1, 41.5)):
        lift = sh if s < 0 else 0
        lame = pen.ell(cx, 41.5 + lift, 5.4, 2.2)
        plate(f, lame, 'slate_cool', glint=False)
        p = pen.ell(cx, 37 + lift, 6.2, 4.4)
        pillow(f, p, 'slate', glint=True)
        dent(pen, int(cx) - 1, 38 + lift, 'slate', w=2)
        rivet(pen, int(cx) + (3 if s < 0 else -3), 35 + lift)
    # gorget
    plate(f, pen.rect(27 + tilt, 31, 36 + tilt, 34), 'iron', glint=False)
    # helm: a round sallet with cheek plates, horns through the crown, the visor raised
    hx = 31.5 + tilt
    for s in (-1, 1):
        pts = [(23, 21), (26, 19), (23, 16), (20, 14), (21, 17)]
        if s > 0:
            pts = [(63 - x, y) for x, y in pts]
        horn = pen.poly([(x + tilt, y) for x, y in pts])
        pillow(f, horn, 'ash', lift=1 if s < 0 else 0)
    helm = pen.ell(hx, 24, 9.2, 8.6)
    pillow(f, helm, 'slate', glint=False)
    face = pen.rect(25 + tilt, 21, 38 + tilt, 31, knock=3)
    pillow(f, face, 'clay')
    for y in range(22, 31):    # the helm's inner rim shades the face's west edge
        if (25 + tilt, y) in face:
            f.put(25 + tilt, y, 'clay', 2)
    scales(f, {p for p in face if p[1] < 24})
    eyes_front(pen, 24, 27 + tilt, 35 + tilt, mode='shut' if fid else 'open')
    muzzle_front(pen, 28.5, dx=tilt, w=4.4, h=2.6)
    dent(pen, 39 + tilt, 27, 'slate', w=1)
    # the raised visor, a plate across the brow with its slit, pivots at the temples
    vis = pen.rect(24 + tilt, 16, 39 + tilt, 20, knock=2)
    plate(f, vis, 'slate_warm', glint=True)
    for x in range(26 + tilt, 38 + tilt):
        f.put(x, 18, 'slate_warm', 0 if x % 3 else 2)
    rivet(pen, 23 + tilt, 22)
    rivet(pen, 40 + tilt, 22)
    if fid:  # the clink: two brass flecks off the rolled pauldron (a finite effect)
        for (x, y) in ((13, 31), (14, 30), (12, 35), (13, 36)):
            pen.put(x, y, 'brass', 5, keep=True)
    return finish(pen)


def a_side(d):
    pen = Pen(d)
    f = pen.fig
    # far wing behind, near wing over the back
    for k, (dx, lift) in enumerate(((2, -1), (0, 0))):
        pts = [(28 + dx, 35), (22 + dx, 27), (18 + dx, 26), (19 + dx, 30), (21 + dx, 35), (25 + dx, 41)]
        w = pen.poly(pts)
        pillow(f, w, 'clay_cool', lift=lift - 1)
        for (x, y) in ((19 + dx, 27), (20 + dx, 28), (21 + dx, 29), (22 + dx, 30)):
            pen.put(x, y, 'ash', 3 + lift)
        pen.put(21 + dx, 33, 'clay_cool', 0)
        pen.put(22 + dx, 34, 'clay_cool', 0)
    # tail out behind, down to the ground and curling up at its grey end
    tail(pen, [(27, 50), (23, 56), (19, 60), (14, 62), (10, 61), (8, 58), (9, 55)],
         [3.0, 2.6, 2.1, 1.7, 1.3, 1.0, 0.7], grey_from=14, ember=(22, 57))
    # far leg (a tone back), then near leg
    for x0, lift in ((29, -1), (32, 0)):
        greave(pen, x0, 53, x0 + 4, 56, 'slate', lift=lift)
        pillow(f, pen.rect(x0 + 1, 56, x0 + 5, 58, knock=1), 'slate_warm', lift=lift)
        greave(pen, x0, 59, x0 + 4, 61, 'slate_cool', lift=lift)
        plate(f, pen.rect(x0, 62, x0 + 7, 65, knock=1), 'iron', lift=lift, glint=False)
    # tassets
    plate(f, pen.rect(27, 51, 37, 53, knock=1), 'iron', glint=False)
    plate(f, pen.rect(26, 48, 38, 50, knock=1), 'slate_warm', glint=False)
    plate(f, pen.rect(26, 46, 38, 47), 'iron', glint=False, sheen=False, lift=-1)
    # far gauntlet peeking ahead of the chest
    pillow(f, pen.rect(37, 45, 40, 48, knock=1), 'iron', lift=-1)
    # cuirass in profile: the chest bulges forward
    cu = pen.poly([(27, 33), (37, 33), (40, 38), (39, 45), (37, 47), (27, 47), (26, 40)])
    pillow(f, cu, 'slate', glint=True)
    dent(pen, 35, 40, 'slate', w=2)
    # the bell at the belt front
    pen.put(39, 48, 'iron', 1)
    pen.put(39, 49, 'iron', 1)
    bell(pen, 39, 50)
    # near arm hanging, pauldron over it
    greave(pen, 30, 40, 34, 43, 'slate')
    pillow(f, pen.rect(29, 43, 34, 45, knock=1), 'iron')
    greave(pen, 30, 46, 34, 48, 'slate_cool')
    pillow(f, pen.rect(29, 49, 35, 52, knock=1), 'iron')
    pen.put(31, 51, 'iron', 1)
    pen.put(33, 51, 'iron', 1)
    plate(f, pen.ell(31.5, 41.5, 5.2, 2.0), 'slate_cool', glint=False)
    pa = pen.ell(31.5, 37, 6.0, 4.4)
    pillow(f, pa, 'slate', glint=True)
    dent(pen, 29, 37, 'slate')
    # gorget
    plate(f, pen.rect(28, 31, 36, 34), 'iron', glint=False)
    # horn swept back through the helm's crown
    horn = pen.poly([(28, 19), (25, 15), (21, 14), (23, 16), (26, 21)])
    pillow(f, horn, 'ash', lift=1)
    helm = pen.ell(31, 24, 8.4, 8.6)
    pillow(f, helm, 'slate', glint=False)
    # neck guard flaring at the back of the helm
    plate(f, pen.rect(23, 28, 27, 31, knock=1), 'slate_cool', glint=False)
    # face opening at the front, the snout out past the helm
    face = pen.rect(34, 21, 39, 31, knock=2)
    pillow(f, face, 'clay')
    snout_side(pen, 36, 25, 44, 31)
    eye_side(pen, 35, 23)
    # raised visor over the brow, pivot rivet at the temple
    vis = pen.poly([(28, 16), (38, 17), (41, 20), (40, 21), (29, 20)])
    plate(f, vis, 'slate_warm')
    for x in range(32, 40):
        pen.put(x, 18, 'slate_warm', 0 if x % 3 else 2)
    rivet(pen, 30, 22)
    dent(pen, 26, 24, 'slate', w=2)
    return finish(pen)


# --- option B: half-plate over a quilted gambeson, bare scaly arms ------------------------
def b_horn_front(pen, s):
    pts = [(26, 21), (24, 17), (21, 14), (19, 14), (19, 17), (21, 21), (23, 24)]
    ridge = [(22, 18), (21, 16)]
    if s > 0:
        pts = [(63 - x, y) for x, y in pts]
        ridge = [(63 - x, y) for x, y in ridge]
    horn = pen.poly(pts)
    pillow(pen.fig, horn, 'ash', lift=1 if s < 0 else 0)
    for (x, y) in ridge:
        pen.fig.put(x, y, 'ash', 2 if s < 0 else 1)


def b_front(pose='idle'):
    pen = Pen(1)
    f = pen.fig
    fid = pose == 'fidget'
    # tail behind, long, an ember banked in its tip
    tail(pen, [(36, 53), (41, 58), (46, 61), (51, 62), (55, 61), (57, 58)], [3.4, 3.0, 2.5, 2.0, 1.6, 1.2],
         ember=(57, 58))
    pen.glow(56, 59, 2)
    # legs: quilted breeches into slate greaves and boots
    for x0 in (26, 33):
        cloth(f, pen.rect(x0, 52, x0 + 4, 57), 'ashlar_cool', lit=1, dark=1, top=False)
        greave(pen, x0 - 1, 58, x0 + 5, 61, 'slate')
        plate(f, pen.rect(x0 - 1, 62, x0 + 5, 65, knock=1), 'slate_cool', glint=False, lift=-1)
    # the gambeson, long to mid-thigh, quilted
    gam = pen.poly([(24, 34), (39, 34), (41, 46), (43, 53), (20, 53), (22, 46)])
    cloth(f, gam, 'ashlar', lit=3, dark=3, folds=(27, 36))
    quilt(f, gam, 'ashlar', step=4, y0=48)
    # belt and bell
    plate(f, pen.rect(23, 46, 40, 47), 'ash', glint=False, sheen=False, lift=-1)
    for (x, y, t) in ((31, 46, 4), (32, 46, 3), (31, 47, 2), (32, 47, 1)):
        f.put(x, y, 'brass', t)
    pen.put(37, 48, 'ash', 1)
    bell(pen, 37, 49)
    # breastplate (half-plate)
    cu = pen.poly([(25, 34), (38, 34), (40, 39), (38, 45), (25, 45), (23, 39)])
    pillow(f, cu, 'slate', glint=True)
    for y in range(36, 44):
        f.put(31, y, 'slate', 4)
        f.put(32, y, 'slate', 2)
    dent(pen, 26, 40, 'slate')
    rivet(pen, 25, 36)
    rivet(pen, 38, 36)
    # bare scaly arms, thick: the screen-left (her right) raised to fan in the fidget
    for s, x0 in ((-1, 18), (1, 40)):
        if s < 0 and fid:
            up = pen.poly([(18, 37), (24, 36), (24, 41), (19, 42)])
            fore = pen.poly([(16, 30), (21, 29), (23, 38), (18, 39)])
            pillow(f, up, 'clay')
            pillow(f, fore, 'clay')
            scales(f, up | fore)
            greave(pen, 17, 33, 21, 36, 'slate_cool')
            hand = pen.ell(18.5, 28, 2.8, 2.4)
            pillow(f, hand, 'clay', lift=1)
            for (x, y) in ((16, 26), (18, 25), (20, 26)):
                f.put(x, y, 'ash', 4)
            continue
        arm = pen.rect(x0, 37, x0 + 5, 47, knock=1)
        pillow(f, arm, 'clay')
        scales(f, arm)
        greave(pen, x0, 44, x0 + 5, 47, 'slate_cool')
        hand = pen.ell(x0 + 3, 50, 3.0, 2.6)
        pillow(f, hand, 'clay')
        for x in range(x0 + 1, x0 + 6, 2):
            f.put(x, 52, 'ash', 3)      # claws
        if s > 0:
            grey(f, pen.rect(x0, 38, x0 + 5, 43))   # the greying patch, her left upper arm
    # one big pauldron on her left (screen right) with a lame
    plate(f, pen.ell(42, 41.5, 5.0, 2.0), 'slate_cool', glint=False)
    pa = pen.ell(42, 36.5, 6.6, 4.6)
    pillow(f, pa, 'slate', glint=True)
    dent(pen, 40, 37, 'slate')
    rivet(pen, 45, 34)
    # a strap over the bare right shoulder
    for y in range(33, 37):
        f.put(25, y, 'ash', 2)
        f.put(26, y, 'ash', 1)
    # neck and head
    pillow(f, pen.rect(28, 30, 35, 34), 'clay', lift=-1)
    for s in (-1, 1):
        b_horn_front(pen, s)
    head = pen.ell(31.5, 24, 8.4, 7.4)
    pillow(f, head, 'clay')
    scales(f, {p for p in head if p[1] < 23})
    for s in (-1, 1):   # cheek frills
        pts = [(24, 25), (20, 27), (24, 29)]
        if s > 0:
            pts = [(63 - x, y) for x, y in pts]
        pillow(f, pen.poly(pts), 'clay_warm', lift=0 if s < 0 else -1)
    eyes_front(pen, 23, mode='squint' if fid else 'open')
    for x in (25, 26):
        f.put(x, 27, 'clay', 4)
    muzzle_front(pen, 28.5, w=5.0, h=3.0)
    if fid:   # the smoke puff she blows and fans away (an effect, finite)
        for (cx, cy, rx, ry) in ((15.5, 19.5, 2.4, 1.9), (11.5, 21.5, 2.6, 2.1), (13.5, 24, 1.7, 1.4)):
            pillow(f, pen.ell(cx, cy, rx, ry), 'ash', lift=2)
    return finish(pen)


def b_side(d):
    pen = Pen(d)
    f = pen.fig
    tail(pen, [(27, 51), (23, 57), (18, 61), (12, 62), (8, 61), (6, 57)], [3.6, 3.2, 2.6, 2.1, 1.7, 1.2],
         ember=(7, 59))
    pen.glow(7, 58, 2)
    # far arm behind (a tone back)
    pillow(f, pen.rect(36, 38, 39, 46, knock=1), 'clay', lift=-1)
    for x0, lift in ((28, -1), (32, 0)):
        cloth(f, pen.rect(x0, 52, x0 + 4, 57), 'ashlar_cool', lit=1, dark=1, top=False, lift=lift)
        greave(pen, x0, 58, x0 + 5, 61, 'slate', lift=lift)
        plate(f, pen.rect(x0, 62, x0 + 7, 65, knock=1), 'slate_cool', lift=lift - 1, glint=False)
    gam = pen.poly([(26, 34), (37, 34), (39, 46), (40, 53), (24, 53), (25, 46)])
    cloth(f, gam, 'ashlar', lit=3, dark=3, folds=(30,))
    quilt(f, gam, 'ashlar', step=4, y0=48)
    plate(f, pen.rect(25, 46, 39, 47), 'ash', glint=False, sheen=False, lift=-1)
    pen.put(39, 48, 'ash', 1)
    bell(pen, 39, 49)
    cu = pen.poly([(27, 34), (36, 34), (40, 38), (39, 44), (27, 45), (26, 39)])
    pillow(f, cu, 'slate', glint=True)
    dent(pen, 33, 40, 'slate')
    # near arm: in E her left (pauldron, greying); in W her right (bare, strapped)
    arm = pen.rect(29, 37, 34, 47, knock=1)
    pillow(f, arm, 'clay')
    scales(f, arm)
    greave(pen, 29, 44, 34, 47, 'slate_cool')
    pillow(f, pen.ell(32, 50, 3.0, 2.6), 'clay')
    pen.put(32, 52, 'ash', 3)
    pen.put(34, 52, 'ash', 3)
    if d > 0:
        grey(f, pen.rect(29, 38, 34, 43))
        plate(f, pen.ell(31.5, 41.5, 5.0, 2.0), 'slate_cool', glint=False)
        pillow(f, pen.ell(31.5, 36.5, 6.4, 4.6), 'slate', glint=True)
        dent(pen, 29, 37, 'slate')
    else:
        pillow(f, pen.ell(25, 35, 3.0, 3.0), 'slate', lift=-1)   # the far pauldron behind the neck
        for y in range(33, 38):
            pen.put(31, y, 'ash', 2)
            pen.put(32, y, 'ash', 1)
    # neck, horns, head
    pillow(f, pen.rect(28, 29, 34, 34), 'clay', lift=-1)
    pillow(f, pen.poly([(26, 20), (21, 18), (18, 19), (22, 21), (25, 24)]), 'ash', lift=-1)   # far horn
    horn = pen.poly([(30, 19), (26, 15), (21, 14), (19, 15), (22, 17), (25, 20), (27, 23)])
    pillow(f, horn, 'ash', lift=1)
    head = pen.ell(31, 24, 7.4, 7.2)
    pillow(f, head, 'clay')
    scales(f, {p for p in head if (p[0] - pen.X(33)) * d < 0})
    for (x, y) in ((24, 21), (23, 23), (23, 25)):    # spines down the back of the skull
        pen.put(x, y, 'clay', 2)
        pen.put(x - 1, y, 'clay', 1)
    snout_side(pen, 35, 23, 43, 30)
    eye_side(pen, 34, 22)
    pillow(f, pen.poly([(29, 26), (25, 29), (30, 30)]), 'clay_warm', lift=-1)
    return finish(pen)


# --- option C: hearth squire, kettle hat, big bell -----------------------------------------
def c_front(pose='idle'):
    pen = Pen(1)
    f = pen.fig
    fid = pose == 'fidget'
    # the tail curls up behind the hip, a banked ember at its tip
    tail(pen, [(36, 52), (42, 54), (46, 50), (46, 45), (44, 42)], [3.0, 2.8, 2.4, 1.9, 1.3])
    pen.glow(44, 42, 4)
    pen.glow(45, 43, 3)
    # legs: ash breeches, timber boots with a turned cuff
    for x0 in (26, 33):
        cloth(f, pen.rect(x0, 53, x0 + 4, 58), 'ash', lit=1, dark=1, top=False, lift=-1)
        cloth(f, pen.rect(x0 - 1, 59, x0 + 5, 65, knock=1), 'timber', lit=2, dark=2)
        for x in range(x0 - 1, x0 + 6):
            pen.put(x, 61, 'timber', 1)
    # surcoat: quilted ash, belted, a hearth badge
    sc = pen.poly([(25, 35), (38, 35), (40, 45), (42, 54), (21, 54), (23, 45)])
    cloth(f, sc, 'ash', lit=3, dark=3, folds=(28, 35))
    quilt(f, sc, 'ash', step=4, y0=49)
    pillow(f, pen.rect(29, 38, 34, 42, knock=1), 'clay', lift=1)
    for (x, y, t) in ((31, 39, 4), (32, 39, 4), (31, 40, 2), (32, 40, 2)):
        pen.put(x, y, 'brass', t)
    plate(f, pen.rect(23, 46, 40, 47), 'timber', glint=False, sheen=False)
    # arms: scaly clay, iron vambraces; her right reaches across to the bell in the fidget
    for s, x0 in ((-1, 19), (1, 39)):
        if s < 0 and fid:
            up = pen.poly([(20, 37), (25, 37), (27, 44), (23, 45)])
            pillow(f, up, 'clay')
            scales(f, up)
            plate(f, pen.poly([(23, 43), (28, 42), (31, 47), (27, 48)]), 'iron', glint=False)
            continue
        arm = pen.rect(x0, 37, x0 + 4, 46, knock=1)
        pillow(f, arm, 'clay')
        scales(f, arm)
        greave(pen, x0, 43, x0 + 4, 47, 'iron')
        pillow(f, pen.ell(x0 + 2, 49.5, 2.6, 2.3), 'clay')
        if s > 0:
            grey(f, pen.rect(x0, 37, x0 + 4, 42))
    # the big bell, at the belt front on her left
    for y in (48, 49):
        pen.put(35, y, 'timber', 2 if y == 48 else 1)
    bell(pen, 35, 50, big=True)
    if fid:   # her hand laid on the bell to quiet it
        pillow(f, pen.ell(32.5, 50.5, 2.6, 2.3), 'clay', lift=1)
    # spaulders and gorget, small
    for s, cx in ((-1, 23.5), (1, 40.5)):
        pillow(f, pen.ell(cx, 37, 4.4, 3.2), 'iron', glint=(s < 0), lift=1)
        if s > 0:
            dent(pen, 39, 37, 'iron', w=2)
    plate(f, pen.rect(27, 32, 36, 35, knock=1), 'iron', glint=False)
    # head: big and round, a short snout, stubby horns out through the hat
    head = pen.ell(31.5, 26.5, 8.4, 6.6)
    pillow(f, head, 'clay')
    scales(f, {p for p in head if p[1] > 27 and (p[0] < 27 or p[0] > 36)})
    eyes_front(pen, 24, mode='down' if fid else 'open')
    for x in (25, 26):
        f.put(x, 28, 'clay', 4)
    muzzle_front(pen, 29.5, w=4.4, h=2.6)
    for s in (-1, 1):
        pts = [(25, 18), (21, 15), (20, 16), (24, 20)]
        if s > 0:
            pts = [(63 - x, y) for x, y in pts]
        pillow(f, pen.poly(pts), 'ash', lift=1 if s < 0 else 0)
    # kettle hat: a low domed crown and a wide brim that throws a hard shadow on the brow
    crown = pen.ell(31.5, 18, 6.6, 4.2)
    pillow(f, crown, 'iron', glint=True, lift=1)
    brim = pen.poly([(18, 20), (46, 20), (45, 22), (19, 22)])
    plate(f, brim, 'iron', glint=False)
    for x in range(19, 45):
        pen.put(x, 20, 'iron', 4 if x < 32 else 3)
    for x in range(24, 40):
        if (x, 22) in head:
            pen.put(x, 22, 'clay', 1)          # the brim's shadow on the brow
    dent(pen, 33, 16, 'iron', w=2)
    rivet(pen, 27, 18)
    rivet(pen, 36, 18)
    return finish(pen)


def c_side(d):
    pen = Pen(d)
    f = pen.fig
    tail(pen, [(26, 52), (20, 53), (16, 49), (17, 44), (20, 42)], [3.0, 2.8, 2.4, 1.8, 1.2])
    pen.glow(20, 42, 4)
    pen.glow(21, 43, 3)
    pillow(f, pen.rect(35, 38, 38, 46, knock=1), 'clay', lift=-1)
    for x0, lift in ((28, -1), (32, 0)):
        cloth(f, pen.rect(x0, 53, x0 + 4, 58), 'ash', lit=1, dark=1, top=False, lift=lift - 1)
        cloth(f, pen.rect(x0, 59, x0 + 6, 65, knock=1), 'timber', lit=2, dark=2, lift=lift)
        for x in range(x0, x0 + 7):
            pen.put(x, 61, 'timber', 1)
    sc = pen.poly([(26, 35), (37, 35), (39, 45), (41, 54), (23, 54), (25, 45)])
    cloth(f, sc, 'ash', lit=3, dark=3, folds=(31,))
    quilt(f, sc, 'ash', step=4, y0=49)
    plate(f, pen.rect(25, 46, 39, 47), 'timber', glint=False, sheen=False)
    pen.put(38, 48, 'timber', 2)
    pen.put(38, 49, 'timber', 1)
    bell(pen, 38, 50, big=True)
    arm = pen.rect(29, 37, 33, 46, knock=1)
    pillow(f, arm, 'clay')
    scales(f, arm)
    greave(pen, 29, 43, 33, 47, 'iron')
    pillow(f, pen.ell(31, 49.5, 2.6, 2.3), 'clay')
    if d > 0:
        grey(f, pen.rect(29, 37, 33, 42))
    pillow(f, pen.ell(31, 37, 4.6, 3.2), 'iron', glint=True, lift=1)
    dent(pen, 30, 37, 'iron', w=2)
    plate(f, pen.rect(28, 32, 36, 35, knock=1), 'iron', glint=False)
    head = pen.ell(31, 26.5, 7.6, 6.6)
    pillow(f, head, 'clay')
    scales(f, {p for p in head if (p[0] - pen.X(32)) * d < 0 and p[1] > 24})
    snout_side(pen, 35, 25, 42, 31)
    eye_side(pen, 34, 24)
    pillow(f, pen.poly([(27, 18), (22, 15), (21, 16), (25, 21)]), 'ash', lift=1)
    crown = pen.ell(30.5, 18, 6.4, 4.2)
    pillow(f, crown, 'iron', glint=True, lift=1)
    brim = pen.poly([(18, 20), (45, 19), (45, 21), (18, 22)])
    plate(f, brim, 'iron', glint=False)
    for x in range(34, 42):
        p = (pen.X(x), 22)
        if fam_at(f, p) and base(fam_at(f, p)) == 'clay':
            pen.put(x, 22, 'clay', 1)
    dent(pen, 31, 16, 'iron', w=2)
    rivet(pen, 27, 18)
    return finish(pen)


# --- the options ----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))


def runner(front, side):
    def fn(v):
        if v == 'S':
            return front('idle')
        if v == 'Sf':
            return front('fidget')
        return side(1 if v == 'E' else -1)
    return fn


OPTIONS = [
    dict(label='A', name='Dented plate: visor up, wings folded, grey-tipped tail',
         question='Mostly armour: a full harness, the dragon only at the snout, horns, wings and tail.',
         fn=runner(a_front, a_side),
         palette=['slate', 'iron', 'clay', 'ash', 'brass'],
         pose='Square and planted, gauntlets loose at her sides, chin up under the raised visor: '
              'the night watch nobody has to remind. Fidget: rolls her left shoulder, eyes shut, plates clink.',
         parts=[
             'wings (clay_cool membrane, ash bone): layer 0; back; folded behind the pauldrons in S, '
             'one shape over the back in E/W; flick open 2 px on react and cheer',
             'tail (clay scales, last third ash, one lava ember): layer 1; hip; behind the legs, '
             'sways a frame behind the walk, curls round her in the nap',
             'far leg / near leg (slate cuisse, slate_warm knee cop, slate_cool greave, iron sabaton): layers 2/4; hip; 6-frame walk',
             'tassets (slate_warm over iron, two lames a side) and belt (iron): layer 5; hip; squash on hop',
             'cuirass (slate, centre ridge, two dents): layer 6; hip; breath 1 px',
             'bell (brass, small) on an iron strap: layer 7; belt front, her left, in every facing; '
             'swings a frame behind; tolls at three heat (cast)',
             'arms (slate vambraces, iron couter and gauntlet): layer 8; chest; swing, guard, wind-up',
             'pauldrons (slate dome, slate_cool lame, dent, brass rivet): layer 9; chest; ride up in the fidget and guard',
             'head (slate sallet with a raised slate_warm visor, ash horns, clay drake face): layer 10; chest; '
             'visor drops for guard (visor part), eyes blink in the face opening',
         ],
         notes=[
             'Works: the most knightly silhouette (domed shoulders, horned helm, wings over the shoulders); '
             'reads as armour first at 2 device px.',
             'Risk: little dragon shows (snout, horns, tail), and an all-metal body is cold beside the warm '
             'folk; the wings add a part to every frame.',
             'Compared with Eastward 05 at the same height (John, Sam, the townsfolk): one dark outline, '
             'a lit cap and dark crescent per part, 4 to 5 tones a material, 2 x 3 eyes with a glint.',
         ]),
    dict(label='B', name='Half-plate drake: breastplate and one pauldron, bare scaly arms, big horns',
         question='Half and half: a breastplate over a quilted gambeson, the dragon in the head, arms and tail.',
         fn=runner(b_front, b_side),
         palette=['clay', 'slate', 'ashlar', 'ash', 'brass'],
         pose='A bruiser at ease, arms hanging heavy, weight back on her heels, horns high. '
              'Fidget: blows a tiny smoke puff and fans it away with a clawed hand.',
         parts=[
             'tail (clay scales, lava ember at the tip, 2 px glow): layer 0; hip; long, '
             'sways behind the walk, wraps the nap; the ember dims as heat drops',
             'far arm (clay, a tone back): layer 1; chest; swings opposite the near leg',
             'legs (ashlar_cool breeches, slate greaves and boots): layers 2/3; hip; 6-frame walk',
             'gambeson (ashlar, quilted, to mid-thigh): layer 4; hip; the hem sways a frame behind',
             'belt (ash) and bell (brass): layer 5; belt front, her left; swings, tolls on cast',
             'breastplate (slate, ridge, dent, brass rivets): layer 6; chest; breath 1 px',
             'near arm (bare clay scales, slate bracer, ash claws; her left upper arm greying to ash): layer 7; '
             'chest; swing, haymaker strike, fan in the fidget',
             'pauldron (slate, her left shoulder only, one lame): layer 8; chest; braces in guard',
             'head (clay, swept ash horns, cheek frills, spine crest): layer 9; chest; '
             'smoke puff spawns at the snout (hand anchor for the fidget)',
         ],
         notes=[
             'Works: the most dragon for a 52 px knight: big horns and frills make a silhouette no other '
             'folk has, the bare arms say Bruiser, the one pauldron gives a lopsided read.',
             'Risk: clay scales sit near Bramble\'s fox in hue; the ashlar gambeson and slate keep the mass '
             'grey-cool, and the horns must stay inside the 64 px cell in every pose.',
             'Compared with Eastward 05 (John\'s bulk and backpack read as one block with a lit edge).',
         ]),
    dict(label='C', name='Hearth squire: kettle hat, quilted surcoat, big belt bell, ember-tipped tail',
         question='Least armour: a squire\'s light kit, a big round drake head under a wide iron brim.',
         fn=runner(c_front, c_side),
         palette=['clay', 'ash', 'iron', 'brass', 'timber'],
         pose='Earnest and a little sleepy, feet together, the bell kept still with a glance. '
              'Fidget: lays a hand on the big bell to quiet it, eyes lowered.',
         parts=[
             'tail (clay scales, curled up behind the hip, lava ember tip): layer 0; hip; '
             'the tip bobs on the breath and lights brighter with heat',
             'far arm (clay, a tone back): layer 1; chest',
             'legs (ash breeches, timber boots with cuffs): layers 2/3; hip; 6-frame walk',
             'surcoat (ash, quilted, clay hearth badge): layer 4; hip; hem sways',
             'belt (timber) and big bell (brass, 9 px): layer 5; belt front, her left; '
             'swings wide on the walk, the hand rests on it in the fidget',
             'near arm (clay scales, iron vambrace; her left upper arm greying): layer 6; chest',
             'spaulders and gorget (iron, small, one dent): layer 7; chest',
             'head (big round clay drake head, stubby ash horns): layer 8; chest',
             'kettle hat (iron crown, wide iron brim with a hard shadow on the brow): layer 9; head; '
             'tips back on cheer, down over the eyes in the nap',
         ],
         notes=[
             'Works: the wide brim is a shape nobody else owns and reads instantly; the big bell is her '
             'signature at any size; cosiest of the three.',
             'Risk: least knight and least Bruiser; the brim crowds the familiar perch on the shoulder.',
             'Compared with Eastward 05 (Sam: a big head over a small body, hair as lobes; the brim shadow '
             'follows Eastward\'s hard shadow under hat brims).',
         ]),
]


# --- the final: B, the half-plate drake, with grafts ----------------------------------------
# Scales move off Bramble's fox orange: deep ember red-brown, clay tones 1 to 3 lead (tone 4
# only on a lit snout ridge and the knuckles), the greying patch in ash. The big brass bell is
# C's (9 x 7, a lit rim), the dents A's (a dark upper crescent over a lit lower lip). The tail
# is short and curls up beside her legs, its ember tip at most 10 art px behind her heel. Her
# one pauldron (her left shoulder) sits at the back of the shoulders in profile: in a fight it
# is on the shoulder away from the foe, the familiar's perch ledge.
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/ashe-final.png')
MAX_TAIL_BEHIND = 10


def scale_fill(fig, mask, fam='clay', lift=0, tex=True):
    """Ember scales: the round-part shading one tone down (tones 1 to 3 lead), never 0,
    then scale rows as staggered two-pixel scallops (left off the face, where they mottle)."""
    mask = set(mask)
    pillow(fig, mask, fam, lift=lift - 1)
    for p in mask:
        t = tone(fig, p)
        if t is not None and t < 1:
            fig.put(p[0], p[1], fam, 1)
    if tex:
        scales(fig, mask)
    return mask


def occlude(fig, mask):
    """A limb in front of the body darkens the body one tone along its edge: the contact
    shadow that keeps an arm from floating as a patch on the belly."""
    ring = set()
    for (x, y) in mask:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in mask and q in fig.px and q not in fig.fixed:
                ring.add(q)
    for q in sorted(ring):
        v = fig.px[q]
        if isinstance(v[1], int) and v[0] != 'ink' and v[1] >= 2:
            fig.px[q] = (v[0], v[1] - 1)


def f_tail(pen, pts, radii, ember_t=4, lift=0):
    m = pen.tube(pts, radii)
    pen.fig.tail = m
    scale_fill(pen.fig, m, lift=lift)
    cols = {}
    for (x, y) in m:
        cols[x] = min(cols.get(x, 99), y)
    for x, y in sorted(cols.items()):
        t = tone(pen.fig, (x, y))
        if t is not None and t < 3 and (x, y + 1) in m:
            pen.fig.put(x, y, 'clay', t + 1)     # the lit ridge along the top of the tail
    ex, ey = pts[-1]
    pen.glow(ex, ey, ember_t)
    pen.glow(ex - 1 if pen.d >= 0 else ex + 1, ey + 1, max(1, ember_t - 1))
    return m


def f_limb(pen, pts, r, fam, lift=0, bracer=None, shadow=False):
    """An arm or leg as a tube; `bracer` is (family, start, end) as fractions of the last
    segment: a slate bracer or greave over it."""
    m = pen.tube(pts, [r] * len(pts))
    if shadow:
        occlude(pen.fig, m)
    if fam == 'clay':
        scale_fill(pen.fig, m, lift=lift)
    else:
        cloth(pen.fig, m, fam, lit=1, dark=1, lift=lift, top=False)
    if bracer:
        bf, a, b = bracer
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        p0 = (x0 + (x1 - x0) * a, y0 + (y1 - y0) * a)
        p1 = (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)
        bm = pen.tube([p0, p1], [r + 0.4, r + 0.4])
        plate(pen.fig, bm, bf, lift=lift, glint=False)
    return m


def f_fist(pen, x, y, lift=0, claws=True, d=1):
    m = pen.ell(x, y, 2.7, 2.4)
    scale_fill(pen.fig, m, lift=lift + 1)
    if claws:
        yb = max(p[1] for p in m)
        for dx in (0, 2):
            pen.put(round(x) - 1 + dx, yb, 'ash', 4)
    return m


def f_boot(pen, x, lift=0, sit=False, y=SOLE):
    if sit:   # toes up, the sole facing forward
        m = pen.rect(x - 1, y - 5, x + 2, y, knock=1)
    else:
        m = pen.rect(x - 3, y - 3, x + 4, y, knock=1)
    plate(pen.fig, m, 'slate_cool', lift=lift - 1, glint=False)
    return m


def f_bell(pen, cx, top):
    """C's big bell, 9 x 7 with a lit rim and a waist band."""
    pen.put(cx, top - 1, 'ash', 1)
    return bell(pen, cx, top, big=True)


def f_dent(pen, x, y, fam='slate', w=4):
    """A's dent, larger: a dark upper crescent with turned-down tips, a lit lower lip."""
    for i in range(w):
        pen.put(x + i, y, fam, 1)
    pen.put(x - 1, y + 1, fam, 2)
    pen.put(x + w, y + 1, fam, 2)
    for i in range(w):
        pen.put(x + i, y + 1, fam, 4)


def mossling(pen, cx, bottom, curled=False, eyes='open'):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    f = pen.fig
    cx = int(cx + 0.5)
    if curled:
        body = pen.ell(cx, bottom - 6, 8, 6)
        pillow(f, body, 'grass', glint=True)
        for dx in (-3, 2):
            pen.put(cx + dx, bottom - 6, 'ink', 0)
            pen.put(cx + dx + 1, bottom - 6, 'ink', 0)
            pen.put(cx + dx - 1 if dx < 0 else cx + dx + 2, bottom - 7, 'ink', 0)
        stem = [(cx, bottom - 12), (cx, bottom - 13), (cx + 1, bottom - 14)]
    else:
        body = pen.ell(cx, bottom - 9.5, 9, 9.5)
        pillow(f, body, 'grass', glint=True)
        ey = bottom - 12
        for ex in (cx - 3, cx + 1):
            for dy in range(3):
                pen.put(ex, ey + dy, 'ink', 0)
                pen.put(ex + 1, ey + dy, 'ink', 0)
        stem = [(cx, bottom - 19), (cx, bottom - 20), (cx, bottom - 21)]
    for (x, y) in stem:
        pen.put(x, y, 'leaf', 2)
        pen.put(x + 1, y, 'leaf', 1)
    top = stem[-1][1]
    leaf_l = pen.poly([(cx - 4, top - 2), (cx, top), (cx - 1, top + 2), (cx - 4, top)])
    leaf_r = pen.poly([(cx + 2, top), (cx + 6, top - 2), (cx + 6, top), (cx + 2, top + 2)])
    pillow(f, leaf_l, 'leaf', lift=1)
    pillow(f, leaf_r, 'leaf')
    return body


def fb_head_front(pen, f, fid=False, hy=0):
    for s in (-1, 1):
        pts = [(26, 21), (24, 17), (21, 14), (19, 14), (19, 17), (21, 21), (23, 24)]
        ridge = [(22, 18), (21, 16)]
        if s > 0:
            pts = [(63 - x, y) for x, y in pts]
            ridge = [(63 - x, y) for x, y in ridge]
        horn = pen.poly([(x, y + hy) for x, y in pts])
        pillow(f, horn, 'ash', lift=1 if s < 0 else 0)
        for (x, y) in ridge:
            f.put(x, y + hy, 'ash', 2 if s < 0 else 1)
    head = pen.ell(31.5, 24 + hy, 8.4, 7.4)
    scale_fill(f, head, tex=False)
    for s in (-1, 1):   # cheek frills, lit on the west one
        pts = [(24, 25), (20, 27), (24, 29)]
        if s > 0:
            pts = [(63 - x, y) for x, y in pts]
        scale_fill(f, pen.poly([(x, y + hy) for x, y in pts]), lift=1 if s < 0 else 0)
    # brow plates: a lit ridge over each eye (the head's top plane)
    for x in range(25, 30):
        f.put(x, 20 + hy, 'clay', 3)
    for x in range(34, 38):
        f.put(x, 20 + hy, 'clay', 2)
    eyes_front(pen, 23 + hy, mode='squint' if fid else 'open')
    for x in (25, 26):
        f.put(x, 27 + hy, 'clay', 3)        # lit cheek
    m = muzzle_front(pen, 28.5 + hy, w=5.0, h=3.0)
    for (x, y) in m:   # the snout one tone down too, its top ridge lit at tone 3 to 4
        t = tone(f, (x, y))
        if t is not None and base(fam_at(f, (x, y))) == 'clay' and t >= 2:
            f.put(x, y, 'clay', t - 1 if t < 4 else 3)
    yt = min(p[1] for p in m)
    for x in range(29, 33):
        f.put(x, yt, 'clay', 4)
    return head


def fb_front(pose='idle'):
    pen = Pen(1)
    f = pen.fig
    fid = pose == 'fidget'
    # the tail curls up beside her left leg (screen right), the ember at its tip
    f_tail(pen, [(36, 54), (41, 57), (45, 55), (46, 51), (44, 48)], [3.0, 2.6, 2.2, 1.7, 1.2])
    for x0 in (26, 33):
        cloth(f, pen.rect(x0, 52, x0 + 4, 57), 'ashlar_cool', lit=1, dark=1, top=False)
        greave(pen, x0 - 1, 58, x0 + 5, 61, 'slate')
        plate(f, pen.rect(x0 - 1, 62, x0 + 5, 65, knock=1), 'slate_cool', glint=False, lift=-1)
    gam = pen.poly([(24, 34), (39, 34), (41, 46), (43, 53), (20, 53), (22, 46)])
    cloth(f, gam, 'ashlar', lit=3, dark=3, folds=(27, 36))
    quilt(f, gam, 'ashlar', step=4, y0=48)
    plate(f, pen.rect(23, 46, 40, 47), 'ash', glint=False, sheen=False, lift=-1)
    for (x, y, t) in ((31, 46, 4), (32, 46, 4), (31, 47, 2), (32, 47, 2)):
        f.put(x, y, 'brass', t)
    cu = pen.poly([(25, 34), (38, 34), (40, 39), (38, 45), (25, 45), (23, 39)])
    pillow(f, cu, 'slate', glint=True)
    for y in range(36, 44):
        f.put(31, y, 'slate', 4)
        f.put(32, y, 'slate', 2)
    f_dent(pen, 25, 40)
    rivet(pen, 25, 36)
    rivet(pen, 38, 36)
    # arms: her right (screen left) bare and strapped; her left greying under the pauldron
    for s, x0 in ((-1, 18), (1, 40)):
        if s < 0 and fid:
            up = pen.poly([(18, 37), (24, 36), (24, 41), (19, 42)])
            fore = pen.poly([(16, 30), (21, 29), (23, 38), (18, 39)])
            scale_fill(f, up)
            scale_fill(f, fore)
            greave(pen, 17, 33, 21, 36, 'slate_cool')
            f_fist(pen, 18.5, 28, claws=False)
            for (x, y) in ((16, 26), (18, 25), (20, 26)):
                pen.put(x, y, 'ash', 4, keep=True)
            continue
        arm = pen.rect(x0, 37, x0 + 5, 47, knock=1)
        scale_fill(f, arm)
        greave(pen, x0, 44, x0 + 5, 47, 'slate_cool')
        f_fist(pen, x0 + 3, 50)
        if s > 0:
            grey(f, pen.rect(x0, 38, x0 + 5, 43))
    # the big bell at the belt front, her left
    f_bell(pen, 36, 49)
    # the pauldron on her left shoulder (screen right), a flat-topped ledge with a lame
    plate(f, pen.ell(42, 41.5, 5.2, 2.0), 'slate_cool', glint=False)
    pa = pen.ell(42, 36.5, 6.6, 4.6)
    pillow(f, pa, 'slate', glint=True)
    for x in range(38, 47):
        if (x, 32) in pa:
            f.put(x, 32, 'slate', 4)
    f_dent(pen, 40, 37, w=3)
    rivet(pen, 45, 39)
    for y in range(33, 37):    # the strap over the bare right shoulder
        f.put(25, y, 'ash', 2)
        f.put(26, y, 'ash', 1)
    scale_fill(f, pen.rect(28, 30, 35, 34), lift=-1)
    fb_head_front(pen, f, fid=fid)
    if fid:   # the smoke puff she blows and fans away (a finite effect)
        for (cx, cy, rx, ry) in ((15.5, 19.5, 2.4, 1.9), (11.5, 21.5, 2.6, 2.1), (13.5, 24, 1.7, 1.4)):
            pillow(f, pen.ell(cx, cy, rx, ry), 'ash', lift=2)
    return finish(pen)


# Side poses, local coordinates (she faces +x). sh: shoulder; el, hd: elbow, hand.
POSES = {
    'idle':   dict(bx=0, by=0, hx=0, hy=0, eyes='open',
                   near=((31, 38), (31, 44), (32, 49)), far=((34, 38), (35, 44), (36, 48)),
                   legs=(((33, 52), (33, 57), (34, 61)), ((30, 52), (30, 57), (30, 61)))),
    'ready':  dict(bx=0, by=1, hx=1, hy=1, eyes='open',
                   near=((31, 38), (33, 44), (38, 42)), far=((34, 38), (37, 43), (40, 40)),
                   legs=(((33, 52), (35, 57), (37, 61)), ((30, 52), (29, 57), (27, 61)))),
    'strike': dict(bx=2, by=1, hx=2, hy=1, eyes='squint',
                   near=((32, 38), (38, 39), (45, 38)), far=((32, 38), (29, 43), (27, 46)),
                   legs=(((33, 52), (37, 57), (40, 61)), ((30, 52), (28, 57), (25, 61)))),
    'cast':   dict(bx=0, by=0, hx=0, hy=-1, eyes='open', breath=True,
                   near=((31, 38), (34, 43), (38, 40)), far=((34, 38), (37, 42), (40, 38)),
                   legs=(((33, 52), (34, 57), (35, 61)), ((30, 52), (29, 57), (28, 61)))),
    'hit':    dict(bx=-2, by=1, hx=-2, hy=0, eyes='squint',
                   near=((30, 38), (31, 43), (35, 41)), far=((33, 38), (35, 42), (38, 39)),
                   legs=(((32, 52), (34, 57), (35, 61)), ((29, 52), (28, 57), (28, 61)))),
    'cheer':  dict(bx=0, by=-1, hx=0, hy=-1, eyes='shut', arm_over=True,
                   near=((31, 38), (37, 32), (41, 22)), far=((34, 38), (40, 31), (45, 21)),
                   legs=(((33, 52), (34, 57), (34, 61)), ((30, 52), (29, 57), (29, 61)))),
    'sit':    dict(bx=0, by=8, hx=0, hy=0, eyes='squint', sit=True,
                   near=((31, 46), (33, 52), (37, 55)), far=((34, 46), (36, 51), (39, 54)),
                   legs=(((33, 60), (37, 59), (41, 63)), ((30, 60), (35, 60), (38, 63)))),
}


def fb_side(d, pose='idle', fight=False):
    P = POSES[pose]
    pen = Pen(d)
    f = pen.fig
    bx, by, hx, hy = P['bx'], P['by'], P['hx'] + P['bx'], P['hy'] + P['by']
    sit = P.get('sit', False)
    # tail: short, curled up beside the legs, ember at the tip
    tp = [(27, 51), (23, 55), (21, 53), (20, 49), (22, 46), (24, 45)]
    if sit:
        tp = [(27, 59), (24, 62), (21, 61), (20, 58), (22, 56), (24, 56)]
    f_tail(pen, [(x + (max(bx, 0) if not sit else 0), y + (by if not sit else 0)) for x, y in tp],
           [3.0, 2.5, 2.1, 1.7, 1.3, 1.0], lift=1 if d > 0 else 0)   # on the lit west side in E
    # far arm (behind the body, a tone back): in E her left (greying), in W her right
    sh, el, hd = P['far']
    f_limb(pen, [(sh[0] + bx, sh[1] + by), (el[0] + bx, el[1] + by), (hd[0] + bx, hd[1] + by)], 2.4, 'clay',
           lift=-1, bracer=('ash', 0.5, 0.85))
    f_fist(pen, hd[0] + bx, hd[1] + by, lift=-1, claws=False)
    if d > 0:
        grey(f, pen.tube([(sh[0] + bx, sh[1] + by), (el[0] + bx, el[1] + by)], [2.4, 2.4]))
    def legs():   # far then near
        for k, (hip, knee, ank) in enumerate(reversed(P['legs'])):
            lift = -1 if k == 0 else 0
            f_limb(pen, [hip, knee], 2.4, 'ashlar_cool', lift=lift, shadow=sit)
            g = pen.tube([knee, ank], [2.6, 2.6])
            plate(f, g, 'slate', lift=lift, glint=False)
            f_boot(pen, ank[0] + (0 if sit else 1), lift=lift, sit=sit, y=SOLE if not sit else min(SOLE, ank[1] + 2))

    if not sit:
        legs()
    # gambeson, belt, breastplate
    gam = pen.poly([(26 + bx, 34 + by), (37 + bx, 34 + by), (39 + bx, 46 + by), (40 + bx, 53 + by),
                    (24 + bx, 53 + by), (25 + bx, 46 + by)])
    cloth(f, gam, 'ashlar', lit=3, dark=3, folds=(pen.X(30 + bx),))
    quilt(f, gam, 'ashlar', step=4, y0=48 + by)
    plate(f, pen.rect(25 + bx, 46 + by, 39 + bx, 47 + by), 'ash', glint=False, sheen=False, lift=-1)
    cu = pen.poly([(27 + bx, 34 + by), (36 + bx, 34 + by), (40 + bx, 38 + by), (39 + bx, 44 + by),
                   (27 + bx, 45 + by), (26 + bx, 39 + by)])
    pillow(f, cu, 'slate', glint=True)
    f_dent(pen, 33 + bx, 40 + by, w=3)
    if sit:      # sitting: the thighs come forward over the gambeson's hem
        legs()
    f_bell(pen, 39 + bx, 49 + by)
    # the pauldron at the back of the shoulders (her left): the familiar's ledge
    pcx, pcy = 25.5 + bx, 36.5 + by
    perch = None
    if fight:
        perch = (pen.X(round(pcx)), round(pcy - 4.5))
        mossling(pen, pcx - 6, round(pcy - 3))
    plate(f, pen.ell(pcx, pcy + 4.6, 4.6, 1.8), 'slate_cool', lift=0 if d < 0 else -1, glint=False)
    pa = pen.ell(pcx, pcy, 5.4, 4.4)
    pillow(f, pa, 'slate', lift=0 if d < 0 else -1, glint=(d < 0))
    for x in range(-3, 3):
        p = (pen.X(round(pcx) + x), round(pcy - 4))
        if p in pa:
            f.put(p[0], p[1], 'slate', 4 if d < 0 else 3)
    f_dent(pen, round(pcx) - 1, round(pcy) + 1, w=3)
    def near_arm():
        sh, el, hd = P['near']
        cap = pen.ell(sh[0] + bx + 0.5, sh[1] + by + 0.5, 3.4, 3.2)    # the round shoulder
        occlude(f, cap)
        scale_fill(f, cap, lift=1, tex=False)
        near = f_limb(pen, [(sh[0] + bx, sh[1] + by + 1), (el[0] + bx, el[1] + by), (hd[0] + bx, hd[1] + by)], 2.9,
                      'clay', bracer=('ash', 0.5, 0.85), shadow=True)
        for (x, y) in sorted(cap):
            if (x, y) in near and y <= min(q[1] for q in cap) + 2:
                f.put(x, y, 'clay', 3)
        f_fist(pen, hd[0] + bx, hd[1] + by)
        if d < 0:
            grey(f, pen.tube([(sh[0] + bx, sh[1] + by + 1), (el[0] + bx, el[1] + by)], [2.6, 2.6]) | cap)
        else:
            for y in range(34 + by, 39 + by):   # the strap over her bare right shoulder
                pen.put(30 + bx, y, 'ash', 2)
                pen.put(31 + bx, y, 'ash', 1)

    if not P.get('arm_over'):
        near_arm()
    # neck, horns, head
    scale_fill(f, pen.rect(28 + hx, 29 + hy, 34 + hx, 34 + by), lift=-1)
    pillow(f, pen.poly([(26 + hx, 20 + hy), (21 + hx, 18 + hy), (18 + hx, 19 + hy), (22 + hx, 21 + hy),
                        (25 + hx, 24 + hy)]), 'ash', lift=-1)
    horn = pen.poly([(30 + hx, 19 + hy), (26 + hx, 15 + hy), (21 + hx, 14 + hy), (19 + hx, 15 + hy),
                     (22 + hx, 17 + hy), (25 + hx, 20 + hy), (27 + hx, 23 + hy)])
    pillow(f, horn, 'ash', lift=1)
    head = pen.ell(31 + hx, 24 + hy, 7.4, 7.2)
    scale_fill(f, head, tex=False)
    for (x, y) in ((24, 21), (23, 23), (23, 25)):    # spines down the back of the skull
        pen.put(x + hx, y + hy, 'clay', 1)
        pen.put(x - 1 + hx, y + hy, 'clay', 2)
    # the snout step: a lit bridge over a darker jaw, the brow ridge above the eye
    snout_side(pen, 35 + hx, 23 + hy, 43 + hx, 30 + hy)
    for (x, y) in list(pen.rect(35 + hx, 23 + hy, 43 + hx, 30 + hy, knock=2)):
        t = tone(f, (x, y))
        if t is not None and base(fam_at(f, (x, y))) == 'clay' and t >= 2:
            f.put(x, y, 'clay', t - 1)
    for x in range(36, 42):
        pen.put(x + hx, 23 + hy, 'clay', 4)
    eye_side(pen, 34 + hx, 22 + hy, mode='open' if P['eyes'] == 'open' else 'shut')
    if P['eyes'] == 'shut':      # a happy arc
        pen.put(34 + hx, 22 + hy, 'ink', 0)
        pen.put(35 + hx, 22 + hy, 'ink', 0)
    for (x, y) in ((31, 26), (32, 26), (31, 27)):    # the cheek, lit, under the eye
        pen.put(x + hx, y + hy, 'clay', 3)
    scale_fill(f, pen.poly([(29 + hx, 26 + hy), (25 + hx, 29 + hy), (30 + hx, 30 + hy)]), lift=-1)
    if P.get('arm_over'):   # cheer: the near fist raised in front of the head
        near_arm()
    if P.get('breath'):   # cast: an ember breath at the snout (glow pixels only)
        for (x, y, t) in ((44, 25, 4), (45, 24, 3), (45, 26, 3), (46, 25, 2), (47, 24, 1)):
            pen.glow(x + hx, y + hy, t)
    return finish(pen), perch


def fb_nap():
    pen = Pen(-1)     # laid out so the familiar curls on the lit west side
    f = pen.fig
    # boots tucked at the right, the familiar curled against her back
    plate(f, pen.rect(41, 60, 47, 64, knock=1), 'slate_cool', lift=-1, glint=False)
    mossling(pen, 49, SOLE, curled=True)
    # the curled body: the quilted gambeson round her back, the pauldron on top
    body = pen.ell(33, 58, 11.5, 6.8)
    cloth(f, body, 'ashlar', lit=3, dark=3, folds=(30, 37))
    quilt(f, body, 'ashlar', step=4, y0=54)
    pa = pen.ell(36, 52.5, 5.4, 3.6)
    pillow(f, pa, 'slate', glint=True)
    f_dent(pen, 34, 53, w=3)
    # the tail round the front, its ember banked low
    f_tail(pen, [(42, 63), (35, 64), (28, 64), (23, 63)], [2.4, 2.2, 1.8, 1.2], ember_t=2)
    # the bell resting on the ground in front of her
    f_bell(pen, 31, 57)
    # head resting on a forearm at the left, eyes shut, a horn swept back
    f_limb(pen, [(16, 63), (25, 62)], 2.2, 'clay')
    pillow(f, pen.poly([(22, 52), (26, 48), (29, 47), (27, 50), (24, 54)]), 'ash', lift=1)
    head = pen.ell(20, 57, 6.2, 5.2)
    scale_fill(f, head, tex=False)
    snout_side(pen, 11, 56, 17, 61)
    pen.fig.px = {p: v for p, v in pen.fig.px.items()}
    for x in range(12, 17):
        pen.put(x, 56, 'clay', 3)
    pen.put(18, 57, 'ink', 0)
    pen.put(19, 57, 'ink', 0)
    pen.put(17, 56, 'ink', 0)
    pen.put(17, 55, 'clay', 1)
    pen.put(18, 55, 'clay', 1)
    pen.put(19, 55, 'clay', 2)
    pen.put(20, 55, 'clay', 2)
    return finish(pen)


def tail_behind(fig, d):
    """Art px from her heel to the tail's back end (the follower walks there)."""
    xs = [p[0] for p in fig.tail]
    heel = AX - 4 if d > 0 else AX + 3
    back = min(xs) if d > 0 else max(xs)
    return (heel - back) * (1 if d > 0 else -1)


FINAL_VIEWS = (
    ('S idle', lambda: (fb_front('idle'), None)),
    ('E idle', lambda: fb_side(1, 'idle')),
    ('W idle', lambda: fb_side(-1, 'idle')),
    ('S fidget', lambda: (fb_front('fidget'), None)),
    ('nap S', lambda: (fb_nap(), None)),
    ('E ready', lambda: fb_side(1, 'ready', True)),
    ('E strike', lambda: fb_side(1, 'strike', True)),
    ('E cast', lambda: fb_side(1, 'cast', True)),
    ('E hit', lambda: fb_side(1, 'hit', True)),
    ('E sit', lambda: fb_side(1, 'sit', True)),
    ('E cheer', lambda: fb_side(1, 'cheer', True)),
    ('W ready', lambda: fb_side(-1, 'ready', True)),
    ('W strike', lambda: fb_side(-1, 'strike', True)),
)

FINAL = dict(
    label='B final', chosen='B',
    name='Half-plate drake (final): ember scales, one pauldron as the perch, the big bedtime bell',
    grafts=[
        'From C: the big brass bell (9 x 7 art px, lit rim, waist band, clapper) at the belt front on her '
        'left, the same anchor and layer in every facing; it reads at game scale.',
        'From A: dents drawn as dents, a dark upper crescent with turned-down tips over a lit lower lip, '
        'one or two a plate, never mottling.',
        'Scales moved off Bramble\'s fox orange: deep ember red-brown, clay tones 1 to 3 leading (4 only on '
        'the snout ridge and knuckles), the greying patch in ash on her left upper arm.',
        'Tail cut short and curled up beside her legs, ember tip; never more than 10 art px behind her heel.',
        'The one pauldron (her left shoulder) sits at the back of the shoulders in profile, a flat lit ledge: '
        'in fights it is the shoulder away from the foe and the familiar perches on it.',
    ],
    palette=['clay', 'slate', 'ashlar', 'ash', 'brass'],
    pose='A bruiser at ease, arms hanging heavy, weight back on her heels, horns high; she fights with '
         'her fists and breathes a banked ember to cast. Fidget: a tiny smoke puff, fanned away.',
    parts=[
        'tail (clay ember scales, lava glow tip 2 px): layer 0; hip; curls up beside the legs in every facing '
        '(S: screen right; E/W: behind the heel, at most 10 px back); bobs a frame behind the breath; '
        'round the front in the nap; the tip dims as heat drops',
        'far arm (clay, a tone back, slate_cool bracer): layer 1; chest; E: her left (greying), W: her right',
        'far leg / near leg (ashlar_cool breeches, slate greave, slate_cool boot): layers 2/3; hip; '
        '6-frame walk, lunge in strike, forward in sit',
        'gambeson (ashlar, quilted channels, to mid-thigh): layer 4; hip; hem sways a frame behind',
        'belt (ash) and big bell (brass 9 x 7): layer 5; belt front, her left, all facings; swings a frame '
        'behind, rings on the third heat (cast)',
        'breastplate (slate, ridge, one dent, brass rivets): layer 6; chest; breath 1 px',
        'familiar (stand-in Mossling, 24 px): layer 6.5; perched on the pauldron ledge in fight poses',
        'pauldron (slate, her left shoulder only, lame, dent): layer 7; chest; S: screen right; E: far, '
        'back of the shoulders; W: near, back of the shoulders; the perch ledge (flat lit top)',
        'near arm (bare clay scales, round shoulder, slate_cool bracer, fist with ash claws): layer 8; chest; '
        'E: her right with an ash strap over the bare shoulder, W: her left (greying); haymaker, guard, fan',
        'head (clay, swept ash horns, brow ridge, cheek frill, snout step, spine crest): layer 9; chest; '
        'ember breath spawns at the snout tip (cast), smoke puff (fidget)',
    ],
    notes=[
        'Compared side by side with Eastward 05 at the same character height (John, Sam and the townsfolk '
        'by the trailers): one dark outline per material, a lit cap and dark crescent per part, 4 to 5 '
        'tones a material, 2 x 3 eyes with a glint, John\'s bulk read as one block with a lit edge.',
        'Ember red-brown scales against cool slate and pale ashlar keep her apart from Bramble\'s orange '
        'fox; horns, frills and the single pauldron make a silhouette no other folk has.',
        'The perch is the pauldron at the back of the shoulders; the 24 px stand-in Mossling covers the '
        'back horn in fights (the familiar size is still open for Matt).',
        'Open: whether the cast should ring the bell (her mechanic) rather than breathe an ember; '
        'the scale texture on bare arms is the costliest layer per frame.',
    ],
)


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


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
        extra = ''
        if cap.split()[0] in ('E', 'W'):
            tb = tail_behind(fig, 1 if cap[0] == 'E' else -1)
            g['tail'] = tb <= MAX_TAIL_BEHIND
            extra = f'  tail behind heel {tb:2d}'
        ok &= all(g.values())
        print(f"final {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"{extra}  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Ashe final (folk 10, the fire country): B, the half-plate drake, with grafts', [entry],
                    OUT_FINAL, note='52 art px, cell 64 x 72, foot (32, 66). World S/E/W, fidget, nap; fight E and W '
                                    'with the stand-in Mossling on the pauldron ledge (away from the foe).')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], pose=FINAL['pose'], perch_anchor=perches, measure=nums,
                notes=FINAL['notes'], _ok=ok)


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
            a = im.getchannel('A')
            ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
            print(f"{o['label']} {cap:9s} h {ys[-1] - ys[0] + 1:2d}  on house {100*m['on_house']:5.1f}%  "
                  f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('Ashe (folk 10, the fire country): how much armour, how much dragon', OPTIONS, OUT_PNG,
                    note='52 art px, cell 64 x 72, foot (32, 66). Views: S, E, W idle and the S fidget key pose. '
                         'Accents: ash, ashlar; lava as glow pixels only.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as fh:
        json.dump(dict(id='ashe', height_art_px=52, cell=[W, H], foot=[AX, AY],
                       question='How much armour and how much dragon.', options=out, final=final), fh, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
