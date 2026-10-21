"""Bunk, Halcyon Station's sleep-bay robot: three design options (Claude J lane, batch 3).

Main question: the barrel body and the sleeping bag.

    A  Upright barrel, bedroll pack: a tall white barrel with a domed top, a wide visor band
       wrapped round it (two half-lidded lamp eyes), stubby arms, heavy magnetic boots, and
       the sleeping bag a big quilted roll strapped across the top of its back, sticking out
       past both shoulders. Silhouette: a barrel under a crossbar.
    B  Squat capsule, quilt cape: a wide egg-shaped capsule with a round porthole visor and a
       short antenna lamp; the sleeping bag worn as a cape, its top rolled into a thick collar
       round the "neck", the quilted tail flaring past both sides. No legs: ball arms and
       half-dome boots. Silhouette: a bell with a collar.
    C  Hooped barrel, moon visor: a small helmet head with a half-moon visor and ear pods on a
       barrel torso with two panel hoops and the Sleep Cycle dial on the chest; the bag a
       roll strapped low across the back at the hips; segmented arms, piston legs and big
       round disc feet. Silhouette: a robot with a hip bar.

House rules kept: white hull drawn on the full hull ramp (violet shade, lit edge, a sheen
band in the left third, never flat white); hull siblings per plate; panel for machined
parts; void for glass; the bag in path or timber canvas (sky, dusk, berry, brass oilskin
are owned by other folk); lamp for the eyes and neon_cyan only for indicator lights, both
as glow pixels. W is drawn: its geometry is turned round the anchor and every tone is
computed afterwards from the final pixels, so the light stays upper left.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/bunk.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/bunk-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/bunk.json')
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/bunk-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'bunk')

W, H = 64, 72
AX, AY = 32, 66          # foot anchor: soles fill row 65, their outline lands on row 66
SOLE = AY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
GLOWS = ('lamp', 'neon_cyan')


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def mx(d, x):
    """Side views: E (d=1) as authored, W (d=-1) the geometry turned round the anchor
    column. Only geometry turns; tones are computed afterwards from final positions."""
    return x if d >= 0 else 2 * AX - 1 - x


def mxc(d, x):
    return x if d >= 0 else 2 * AX - x


def R(fig, d, x0, y0, x1, y1, knock=0):
    a, b = sorted((mx(d, x0), mx(d, x1)))
    return fig.rect(a, y0, b, y1, knock)


def P(fig, d, pts):
    return fig.poly([(mxc(d, x), y) for x, y in pts])


def E(fig, d, cx, cy, rx, ry):
    return fig.ellipse(mxc(d, cx), cy, rx, ry)


def _rc(mask):
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    return rows, cols


def clamp(t):
    return max(0, min(5, t))


def cyl(fig, mask, fam, base=3, glint=True):
    """A vertical cylinder of white metal (house-style 5, metal): a sheen band in the left
    third (4), the body (3), the shade (2) and the turned-away east edge (1); every
    column's top is a lit plane, every column's foot a dark underside. Bands are measured
    per row, so on a dome they follow the curve instead of stepping across it."""
    mask = set(mask)
    if not mask:
        return mask
    rows, cols = _rc(mask)
    for (x, y) in mask:
        xl, xr = min(rows[y]), max(rows[y])
        f = (x - xl) / max(1, xr - xl)
        t = 4 if f < 0.36 else 3 if f < 0.68 else 2 if f < 0.88 else 1
        if y == min(cols[x]):
            t = 4 if f < 0.68 else 3
        if y == max(cols[x]):
            t = 2 if f < 0.36 else 1
        fig.put(x, y, fam, clamp(t + base - 3))
    if glint:
        y0 = min(rows)
        for y in (y0 + 1, y0 + 2):
            if y in rows:
                xl, xr = min(rows[y]), max(rows[y])
                gx = xl + max(1, round(0.18 * (xr - xl)))
                if (gx, y) in mask and xr - xl >= 4:
                    fig.put(gx, y, fam, clamp(5 + base - 3))
    return mask


def hcyl(fig, mask, fam, base=3):
    """A horizontal roll (the sleeping bag): a lit upper band, the body, a shaded lower band
    and a dark underside per column; the west end a tone up, the east end a tone down."""
    mask = set(mask)
    rows, cols = _rc(mask)
    for (x, y) in mask:
        yt, yb = min(cols[x]), max(cols[x])
        g = (y - yt) / max(1, yb - yt)
        t = 4 if g < 0.3 else 3 if g < 0.66 else 2
        if y == yb:
            t = 1
        if x == min(rows[y]) and t < 4:
            t += 1
        if x == max(rows[y]) and t > 1:
            t -= 1
        fig.put(x, y, fam, clamp(t + base - 3))
    return mask


def pillow(fig, mask, fam, lo=0, base=3):
    """A round part: a lit cap offset to the upper left, a dark crescent at the lower
    right that follows the form."""
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
        if (x, y + 1) not in mask and u > -0.3:
            t = min(t, 1 if u > 0.2 else 2)
        fig.put(x, y, fam, clamp(max(lo, t) + base - 3))
    return mask


def box(fig, mask, fam, glint=True, base=3):
    """A machined part: lit top row and west column, body, shaded east column, dark
    underside, a two-pixel glint at the top left."""
    mask = set(mask)
    if not mask:
        return mask
    rows, cols = _rc(mask)
    for (x, y) in mask:
        t = base
        if x == min(rows[y]) or y == min(cols[x]):
            t = base + 1
        if x == max(rows[y]):
            t = base - 1
        if y == max(cols[x]):
            t = base - 2
        fig.put(x, y, fam, clamp(t))
    if glint:
        y0 = min(rows)
        row = sorted(p for p in mask if p[1] == y0)
        for p in row[1:3]:
            fig.put(p[0], p[1], fam, clamp(base + 2))
    return mask


def cloth(fig, mask, fam, lit=2, dark=2, folds=(), top=True, bottom=True, base=3):
    """Cloth in vertical bands: lit west band, body, shaded east band, a lit top row and a
    dark hem; `folds` are recessed columns with a lit lip to their west."""
    mask = set(mask)
    rows, cols = _rc(mask)
    for (x, y) in mask:
        xl, xr = min(rows[y]), max(rows[y])
        t = base
        if x - xl < lit:
            t = base + 1
        elif xr - x < dark:
            t = base - 1
        if top and y == min(cols[x]) and t >= base:
            t = base + 1
        if bottom and y == max(cols[x]):
            t = base - 2
        fig.put(x, y, fam, clamp(t))
    for fx in folds:
        for (x, y) in mask:
            if x == fx and min(cols[x]) + 1 < y < max(cols[x]):
                fig.put(x, y, fam, base - 1)
                if (x - 1, y) in mask and tone(fig, (x - 1, y)) == base:
                    fig.put(x - 1, y, fam, base + 1)
    return mask


def recolor(fig, mask, fam, dt=0):
    """Swap a plate to a sibling ramp (same tone), optionally a tone off: parts by siblings."""
    for p in mask:
        v = fig.px.get(p)
        if v and isinstance(v[1], int) and v[0] not in GLOWS:
            fig.put(p[0], p[1], fam, clamp(v[1] + dt))


def darken(fig, mask, dt=1, lo=1):
    for p in mask:
        v = fig.px.get(p)
        if v and isinstance(v[1], int) and v[0] not in GLOWS and p not in fig.fixed:
            fig.put(p[0], p[1], v[0], max(lo, v[1] - dt))


def quilt(fig, mask, fam, xs):
    """Quilting stitched round a roll: each stitch column is a recess (a tone down) with a
    puffed lit lip one pixel to its west, so the bag reads as baffles, not stripes."""
    rows, cols = _rc(mask)
    for qx in xs:
        if qx not in cols:
            continue
        yt, yb = min(cols[qx]), max(cols[qx])
        for y in range(yt + 1, yb):
            if fam_at(fig, (qx, y)) and fam_at(fig, (qx, y)).startswith(fam[:4]):
                fig.put(qx, y, fam_at(fig, (qx, y)), max(1, tone(fig, (qx, y)) - 1))
                w = (qx - 1, y)
                if w in mask and fam_at(fig, w) and tone(fig, w) is not None and tone(fig, w) < 4:
                    fig.put(w[0], w[1], fam_at(fig, w), tone(fig, w) + 1)


def baffles(fig, mask, fam, ys):
    """Quilting across a hanging bag: each stitch row a recess (a tone down) with the
    puffed baffle above it lit a tone up, so it reads as a quilt, not as boards."""
    for y in ys:
        for p in sorted(q for q in mask if q[1] == y):
            if fam_at(fig, p) and tone(fig, p) is not None:
                fig.put(p[0], p[1], fam_at(fig, p), max(1, tone(fig, p) - 1))
                u = (p[0], y - 1)
                if u in mask and tone(fig, u) is not None and tone(fig, u) < 4:
                    fig.put(u[0], u[1], fam_at(fig, u), tone(fig, u) + 1)


def glass(fig, mask, keep=None):
    """Visor glass in void: body tone 1, the lower-right crescent tone 0, a stepped sheen
    at the upper left (4 over 3). Glass, never a glow."""
    mask = set(mask)
    if not mask:
        return mask
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 1
        if 0.45 * u + 0.85 * v > 0.6:
            t = 0
        if v < -0.6 and u < 0.2:
            t = 2
        fig.put(x, y, 'void', t)
    order = sorted(mask, key=lambda p: (p[0] + p[1], p[1]))
    a = order[0]
    sheen = [(a[0] + 1, a[1]), (a[0] + 2, a[1]), (a[0] + 1, a[1] + 1)]
    for i, p in enumerate(sheen):
        if p in mask:
            fig.put(p[0], p[1], 'void', 4 if i < 2 else 3)
            if keep is not None:
                keep.add(p)
    return mask


def lamp(fig, keep, pts, fam='lamp'):
    for (x, y, t) in pts:
        fig.glow(x, y, fam, t)
        keep.add((x, y))


def eye_open(x, y):
    """A half-lidded lamp eye, 4 x 2: the flat lid on top, a rounded underside."""
    return [(x, y, 4), (x + 1, y, 5), (x + 2, y, 4), (x + 3, y, 4), (x + 1, y + 1, 3), (x + 2, y + 1, 3)]


def eye_closed(x, y):
    """The slow blink's far end: a closed-eye curve (a U), dimmer."""
    return [(x, y, 3), (x + 3, y, 3), (x, y + 1, 3), (x + 1, y + 1, 3), (x + 2, y + 1, 3), (x + 3, y + 1, 3)]


def eye_side(d, x, y):
    """A profile eye, 3 x 2, heavier towards the front."""
    pts = [(x, y, 4), (x + 1, y, 5), (x + 2, y, 4), (x + 1, y + 1, 3), (x + 2, y + 1, 3)]
    return [(mx(d, px), py, t) for px, py, t in pts]


def zz(x, y):
    """A small 'z' glyph, 3 x 3, for the sleeping blink."""
    return [(x, y, 3), (x + 1, y, 3), (x + 2, y, 3), (x + 1, y + 1, 3), (x, y + 2, 3), (x + 1, y + 2, 3),
            (x + 2, y + 2, 3)]


def seam_row(fig, mask, y, lit_below=True):
    """A plate seam round a barrel: a dark line (2 tones down) with a lit line under it."""
    for p in sorted(mask):
        if p[1] == y and tone(fig, p) is not None:
            fig.put(p[0], p[1], fam_at(fig, p), max(1, tone(fig, p) - 2))
            q = (p[0], y + 1)
            if lit_below and q in mask and tone(fig, q) is not None and tone(fig, q) <= 3:
                fig.put(q[0], q[1], fam_at(fig, q), min(4, tone(fig, q) + 1))


def slot(fig, pts):
    """A vent slot: the slot a recess two tones down, its lower lip a tone up."""
    for p in pts:
        if tone(fig, p) is not None:
            fig.put(p[0], p[1], fam_at(fig, p), max(0, tone(fig, p) - 2))
    for p in pts:
        q = (p[0], p[1] + 1)
        if q not in pts and tone(fig, q) is not None and fam_at(fig, q) not in GLOWS:
            fig.put(q[0], q[1], fam_at(fig, q), min(4, tone(fig, q) + 1))


def band(fig, mask, rows, fam, keep=None, rivets=()):
    """A panel hoop round a barrel: the barrel's tones moved to the panel ramp, the lower
    row a tone down, and riveted heads (lit over dark)."""
    pts = {p for p in mask if p[1] in rows}
    recolor(fig, pts, fam)
    for p in pts:
        if p[1] == max(rows):
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    for (x, y) in rivets:
        if (x, y) in pts:
            fig.put(x, y, fam, 4)
            if keep is not None:
                keep.add((x, y))
    return pts


def spiral(fig, cx, cy, r, fam, lining=None, d=1):
    """A bag roll seen end on: a round end lit at the upper left, the rolled layers as a
    recessed ring, the core a dark 2 x 2 hole. `lining` shows the inner layer's colour."""
    outer = E(fig, d, cx, cy, r, r)
    pillow(fig, outer, fam)
    ring = E(fig, d, cx + 0.3, cy + 0.3, r - 1.6, r - 1.6)
    inner = E(fig, d, cx + 0.3, cy + 0.3, r - 3.0, r - 3.0)
    for p in ring - inner:
        fig.put(p[0], p[1], lining or fam, 1 if lining is None else 2)
    pillow(fig, inner, fam, base=3)
    c = (round(mxc(d, cx + 0.3) - 0.5), round(cy))
    for p in (c, (c[0] + 1, c[1])):
        if p in outer:
            fig.put(p[0], p[1], fam, 1)
    return outer


def arm_shadow(fig, m, body_fams):
    """Side views: the near arm throws a 1 px shadow on the body just east of it."""
    rows, _ = _rc(m)
    for y, xs in rows.items():
        q = (max(xs) + 1, y)
        if fam_at(fig, q) in body_fams and y > min(rows) + 1:
            fig.put(q[0], q[1], fam_at(fig, q), max(1, tone(fig, q) - 1))


def arm_gap(fig, m, body_fams):
    """Side views: the joint between the near arm and the body is a recess, so the body
    pixel just west of the arm drops a tone (light from the upper left)."""
    rows, _ = _rc(m)
    for y, xs in rows.items():
        q = (min(xs) - 1, y)
        if fam_at(fig, q) in body_fams and y > min(rows) + 1:
            fig.put(q[0], q[1], fam_at(fig, q), max(1, tone(fig, q) - 2))


def despeckle(fig, keep):
    """No speckle: a pixel unlike all four neighbours takes its most common neighbour,
    unless it is a glint, an eye, a light or a rivet (`keep`). Deterministic tie-break."""
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
                pool = [n for n in nb if n[0] not in ('ink', '_edge', '_lit') + GLOWS]
                if not pool:
                    continue
                changes[p] = max(sorted(set(pool), key=str), key=pool.count)
        for p, v in changes.items():
            fig.px[p] = v


def boot(fig, mask, keep, light=None, d=0):
    """A magnetic boot: a heavy panel block, the magnet plate a dark void sole row, and a
    neon_cyan lock light on its face."""
    box(fig, mask, 'panel', glint=True)
    rows, cols = _rc(mask)
    yb = max(rows)
    for p in mask:
        if p[1] == yb:
            fig.put(p[0], p[1], 'void', 1)
        elif p[1] == yb - 1:
            fig.put(p[0], p[1], 'panel', max(1, tone(fig, p) - 1))
    if light:
        lamp(fig, keep, [(light[0], light[1], 3), (light[0] + 1, light[1], 2)], 'neon_cyan')


# =====================================================================================
# Option A: upright barrel, visor band, bedroll across the top of the back
# =====================================================================================
A_BAG = 'path'


def a_body_mask(fig, d=0):
    if d == 0:
        dome = {p for p in fig.ellipse(31.5, 33, 11, 8) if p[1] <= 33}
        return dome | fig.rect(21, 32, 42, 57, 2)
    dome = {p for p in E(fig, d, 31.5, 33, 10, 8) if p[1] <= 33}
    return dome | R(fig, d, 22, 32, 41, 57, 2)


def option_a(view):
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    if view in ('S', 'Sf'):
        # the bedroll behind, across the top of the back (layer 0)
        roll = fig.rect(19, 22, 44, 30) | fig.ellipse(19.5, 26.5, 3.8, 4.6) | fig.ellipse(44.5, 26.5, 3.8, 4.6)
        hcyl(fig, roll, A_BAG)
        quilt(fig, roll, A_BAG, (21, 26, 38, 43))
        recolor(fig, {p for p in roll if p[0] >= 40}, 'path_cool')
        for x0 in (18, 44):                         # the two straps cinching the roll
            box(fig, fig.rect(x0, 22, x0 + 1, 30) & roll, 'panel', glint=False)
        # legs and boots
        for x0 in (25, 35):
            box(fig, fig.rect(x0, 57, x0 + 3, 60), 'panel', glint=False)
        boot(fig, fig.rect(20, 60, 30, 65, 2), keep, light=(23, 62))
        boot(fig, fig.rect(33, 60, 43, 65, 2), keep, light=(36, 62))
        # the barrel
        body = a_body_mask(fig)
        cyl(fig, body, 'hull')
        recolor(fig, {p for p in body if p[1] <= 32}, 'hull_warm')
        recolor(fig, {p for p in body if p[1] >= 52}, 'hull_cool')
        seam_row(fig, body, 33)
        # visor band wrapped round the barrel, a recess under the dome's rim
        vis = fig.rect(22, 34, 41, 39)
        glass(fig, vis, keep)
        for x in range(22, 42):                     # the sill under the visor catches light
            p = (x, 40)
            fig.put(x, 40, fam_at(fig, p), 4 if x < 36 else 3)
        if fid:
            lamp(fig, keep, eye_closed(25, 37) + eye_closed(34, 37))
        else:
            lamp(fig, keep, eye_open(25, 36) + eye_open(35, 36))
        # chest: a vertical plate seam, vent slots, an indicator pair
        for y in range(42, 50):
            fig.put(37, y, fam_at(fig, (37, y)), max(1, tone(fig, (37, y)) - 1))
            fig.put(36, y, fam_at(fig, (36, y)), min(4, tone(fig, (36, y)) + 1))
        for y in (43, 45, 47):
            slot(fig, [(x, y) for x in range(39, 42)])
        lamp(fig, keep, [(25, 43, 4), (26, 43, 3)], 'lamp')
        lamp(fig, keep, [(28, 43, 3)], 'neon_cyan')
        band(fig, body, (50, 51), 'panel', keep, rivets=((24, 50), (30, 50), (36, 50)))
        # straps over the dome's shoulders to clips above the visor
        for x0 in (23, 39):
            m = fig.rect(x0, 27, x0 + 1, 32) & body
            box(fig, m, 'panel', glint=False)
            fig.put(x0, 32, 'panel', 4)
            keep.add((x0, 32))
        # stubby arms
        for side, (sx, ax0) in enumerate(((19, 16), (44, 43))):
            up = fig.rect(ax0, 42, ax0 + 4, 49, 1)
            cyl(fig, up, 'hull_warm', glint=False)
            sh = fig.ellipse(sx + 0.5, 42, 2.6, 2.6)
            pillow(fig, sh, 'panel')
            hd = fig.rect(ax0, 50, ax0 + 4, 53, 1)
            box(fig, hd, 'panel', glint=False)
            fig.put(ax0 + 2, 53, 'panel', 1)        # the mitten's split
            if side == 1:
                darken(fig, up | sh | hd)
        if fid:
            # the slow blink lands on the sleeping glyph: closed eyes and a lit z on the visor
            lamp(fig, keep, zz(38, 34))
    else:
        d = 1 if view == 'E' else -1
        roll = spiral(fig, 23, 28, 6.4, A_BAG, lining='path_cool', d=d)
        darken(fig, {p for p in roll if p[1] > 30}, 0)
        box(fig, R(fig, d, 27, 59, 35, 61) , 'panel', glint=False)
        far = R(fig, d, 24, 61, 35, 65, 2)
        boot(fig, far, keep)
        darken(fig, far)
        box(fig, R(fig, d, 29, 57, 33, 60), 'panel', glint=False)
        boot(fig, R(fig, d, 27, 60, 40, 65, 2), keep, light=(mx(d, 37) if d == 1 else mx(d, 38), 62))
        body = a_body_mask(fig, d)
        cyl(fig, body, 'hull')
        recolor(fig, {p for p in body if p[1] <= 32}, 'hull_warm')
        recolor(fig, {p for p in body if p[1] >= 52}, 'hull_cool')
        seam_row(fig, body, 33)
        vis = R(fig, d, 30, 34, 40, 39)
        glass(fig, vis, keep)
        for x in range(30, 41):
            fig.put(mx(d, x), 40, fam_at(fig, (mx(d, x), 40)), 4)
        lamp(fig, keep, eye_side(d, 36, 36))
        for y in (43, 45, 47):
            slot(fig, [(mx(d, x), y) for x in range(36, 40)])
        lamp(fig, keep, [(mx(d, 33), 43, 3)], 'neon_cyan')
        band(fig, body, (50, 51), 'panel', keep, rivets=((mx(d, 25), 50), (mx(d, 35), 50)))
        # the shoulder strap from the roll over the dome
        st = R(fig, d, 26, 26, 27, 33) & body
        box(fig, st, 'panel', glint=False)
        sh = E(fig, d, 31.5, 42, 2.6, 2.6)
        up = R(fig, d, 30, 43, 33, 50, 1)
        cyl(fig, up, 'hull_warm', glint=False)
        pillow(fig, sh, 'panel')
        arm_shadow(fig, up, ('hull', 'hull_cool', 'panel'))
        arm_gap(fig, up, ('hull', 'hull_cool', 'panel'))
        hd = R(fig, d, 30, 50, 33, 53, 1)
        box(fig, hd, 'panel', glint=False)
    fig.outline()
    despeckle(fig, keep)
    return fig


# =====================================================================================
# Option B: squat capsule, porthole visor, the bag worn as a cape with a rolled collar
# =====================================================================================
B_BAG = 'path'


def b_body_mask(fig, d=0):
    if d == 0:
        dome = {p for p in fig.ellipse(31.5, 39, 13, 13) if p[1] <= 39}
        return dome | fig.rect(19, 38, 44, 58, 3)
    dome = {p for p in E(fig, d, 31.5, 39, 11.5, 13) if p[1] <= 39}
    return dome | R(fig, d, 20, 38, 43, 58, 3)


def option_b(view):
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    if view in ('S', 'Sf'):
        # the cape behind, flaring past both sides (layer 0)
        cape = fig.poly([(19, 42), (45, 42), (50, 61), (14, 61)])
        cloth(fig, cape, B_BAG, lit=2, dark=3)
        baffles(fig, cape, B_BAG, (49, 55))
        for x in range(14, 51, 4):                   # scalloped quilt hem
            if (x, 60) in cape:
                fig.put(x, 60, B_BAG, 1)
        boot(fig, fig.rect(20, 58, 30, 65, 3), keep, light=(23, 61))
        boot(fig, fig.rect(33, 58, 43, 65, 3), keep, light=(36, 61))
        body = b_body_mask(fig)
        cyl(fig, body, 'hull')
        recolor(fig, {p for p in body if p[1] >= 51}, 'hull_cool')
        seam_row(fig, body, 50)
        # antenna and its lamp
        for y in (24, 25):
            fig.put(31, y, 'panel', 3)
            fig.put(32, y, 'panel', 1)
        lamp(fig, keep, [(31, 22, 5), (32, 22, 4), (31, 23, 4), (32, 23, 3)], 'lamp')
        # porthole visor: a panel bezel ring with rivets, void glass
        ring = fig.ellipse(31.5, 33.5, 7.2, 7.0)
        glassm = fig.ellipse(31.5, 33.5, 5.4, 5.2)
        pillow(fig, ring - glassm, 'panel')
        for p in ring - glassm:
            if p[0] > 31 and p[1] > 33:
                fig.put(p[0], p[1], 'panel', min(tone(fig, p), 2))
        for (x, y) in ((31, 27), (25, 33), (38, 33), (31, 40)):
            if (x, y) in ring:
                fig.put(x, y, 'panel', 4 if x < 32 and y < 34 else 3)
                keep.add((x, y))
        glass(fig, glassm, keep)
        if fid:
            lamp(fig, keep, eye_closed(27, 33) + eye_closed(33, 33))
        else:
            lamp(fig, keep, eye_open(27, 33) + eye_open(33, 33))
        # the collar: the bag's top rolled round the neck
        col = fig.rect(17, 41, 46, 46, 2)
        hcyl(fig, col, B_BAG)
        quilt(fig, col, B_BAG, (22, 28, 34, 40))
        recolor(fig, {p for p in col if p[0] >= 41}, 'path_warm')
        # chest hatch: a recessed panel with a handle and an indicator
        hatch = fig.rect(27, 52, 36, 56, 1)
        box(fig, hatch, 'panel')
        for x in range(29, 34):
            fig.put(x, 54, 'panel', 1)
        lamp(fig, keep, [(23, 48, 3), (24, 48, 2)], 'neon_cyan')
        # ball arms
        if not fid:
            for side, cx in enumerate((16.5, 46.5)):
                a = fig.ellipse(cx, 50, 3.2, 4.2)
                pillow(fig, a, 'hull_warm')
                cl = fig.rect(round(cx) - 2, 54, round(cx) + 1, 55)
                box(fig, cl, 'panel', glint=False)
                if side:
                    darken(fig, a | cl)
        else:
            # snuggle: the cape pulled round the front, both claws holding its edge
            wrap = fig.poly([(18, 47), (45, 47), (48, 60), (15, 60)])
            for x in range(15, 49, 5):                  # a scalloped hem
                for q in ((x, 59), (x + 1, 59)):
                    wrap.discard(q)
            cloth(fig, wrap, B_BAG, lit=2, dark=3, folds=(24, 33, 40))
            turn = {p for p in wrap if p[1] in (47, 48)}
            cloth(fig, turn, 'plaster', lit=3, dark=3, bottom=False)
            for p in turn:
                if p[1] == 48:
                    fig.put(p[0], p[1], 'plaster', max(1, tone(fig, p) - 1))
            for x in range(17, 47, 4):
                if (x, 58) in wrap:
                    fig.put(x, 58, B_BAG, 1)
            for cx in (24, 38):
                cl = fig.rect(cx - 2, 46, cx + 1, 48, 1)
                box(fig, cl, 'panel', glint=False)
    else:
        d = 1 if view == 'E' else -1
        cape = P(fig, d, [(19, 41), (26, 41), (25, 61), (13, 61), (15, 50)])
        cloth(fig, cape, B_BAG, lit=2, dark=2)
        baffles(fig, cape, B_BAG, (49, 55))
        far = R(fig, d, 22, 59, 34, 65, 3)
        boot(fig, far, keep)
        darken(fig, far)
        boot(fig, R(fig, d, 27, 58, 41, 65, 3), keep, light=(mx(d, 37) if d == 1 else mx(d, 38), 61))
        body = b_body_mask(fig, d)
        cyl(fig, body, 'hull')
        recolor(fig, {p for p in body if p[1] >= 51}, 'hull_cool')
        seam_row(fig, body, 50)
        for y in (24, 25):
            fig.put(mx(d, 31), y, 'panel', 3 if d == 1 else 2)
            fig.put(mx(d, 32), y, 'panel', 2 if d == 1 else 3)
        lx = min(mx(d, 31), mx(d, 32))
        lamp(fig, keep, [(lx, 22, 5), (lx + 1, 22, 4), (lx, 23, 4), (lx + 1, 23, 3)], 'lamp')
        ring = E(fig, d, 39.5, 33.5, 3.4, 6.6)
        glassm = E(fig, d, 40.0, 33.5, 2.0, 5.0)
        pillow(fig, ring - glassm, 'panel')
        glass(fig, glassm, keep)
        gx = min(p[0] for p in glassm)
        lamp(fig, keep, [(gx + (1 if d == 1 else 0), 33, 4), (gx + (2 if d == 1 else 1), 33, 5),
                         (gx + (1 if d == 1 else 1), 34, 3)])
        col = R(fig, d, 18, 41, 44, 46, 2)
        hcyl(fig, col, B_BAG)
        quilt(fig, col, B_BAG, sorted(mx(d, x) for x in (24, 31, 38)))
        lamp(fig, keep, [(mx(d, 41), 49, 3)], 'neon_cyan')
        a = E(fig, d, 30.5, 51, 3.2, 4.2)
        pillow(fig, a, 'hull_warm')
        arm_shadow(fig, a, ('hull', 'hull_cool'))
        arm_gap(fig, a, ('hull', 'hull_cool'))
        box(fig, R(fig, d, 29, 55, 32, 56), 'panel', glint=False)
    fig.outline()
    despeckle(fig, keep)
    return fig


# =====================================================================================
# Option C: helmet head with a half-moon visor, hooped barrel, dial, hip roll
# =====================================================================================
C_BAG = 'path'


def c_visor(fig, d=0):
    if d == 0:
        return {p for p in fig.ellipse(31.5, 28.5, 7.2, 6.2) if p[1] >= 29}
    return {p for p in E(fig, d, 38.5, 28.5, 4.2, 6.2) if p[1] >= 29}


def option_c(view):
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    if view in ('S', 'Sf'):
        # the bag roll strapped low across the back (layer 0)
        if not fid:
            roll = fig.rect(14, 45, 49, 52, 3)
        else:
            roll = fig.rect(21, 45, 49, 52, 3)
        hcyl(fig, roll, C_BAG)
        quilt(fig, roll, C_BAG, (19, 25, 39, 45))
        recolor(fig, {p for p in roll if p[0] >= 42}, 'path_cool')
        for x0 in (17, 45):
            if (x0, 48) in roll:
                box(fig, fig.rect(x0, 45, x0 + 1, 52) & roll, 'panel', glint=False)
        for x0 in (25, 35):
            box(fig, fig.rect(x0, 57, x0 + 3, 61), 'panel', glint=False)
        boot(fig, fig.rect(19, 61, 30, 65, 3), keep, light=(22, 63))
        boot(fig, fig.rect(33, 61, 44, 65, 3), keep, light=(36, 63))
        torso = fig.rect(22, 40, 41, 57, 2)
        cyl(fig, torso, 'hull')
        band(fig, torso, (40, 41), 'panel', keep, rivets=((25, 40), (31, 40), (37, 40)))
        band(fig, torso, (55, 56), 'panel', keep, rivets=((25, 55), (31, 55), (37, 55)))
        recolor(fig, {p for p in torso if 42 <= p[1] <= 47 and p[0] < 32}, 'hull_warm')
        # the Sleep Cycle dial: bezel, void face, a lamp sector (the deep stage) and a needle
        bez = fig.ellipse(31.5, 48.5, 5.0, 5.0)
        face = fig.ellipse(31.5, 48.5, 3.6, 3.6)
        pillow(fig, bez - face, 'panel')
        for p in face:
            fig.put(p[0], p[1], 'void', 1 if p[0] >= 32 else 2)
        # the deep stage lit: the left half of the face a lamp sector, the needle at twelve
        lamp(fig, keep, [(p[0], p[1], 3 if p[1] < 49 else 2) for p in sorted(face) if p[0] <= 30], 'lamp')
        for p in ((31, 46), (31, 47), (31, 48)):
            fig.put(p[0], p[1], 'hull', 4)
            keep.add(p)
        # neck
        box(fig, fig.rect(27, 38, 36, 39), 'panel', glint=False)
        # head: a rounded helmet, ear pods, the half-moon visor under a brow
        head = fig.rect(23, 22, 40, 37, 4)
        cyl(fig, head, 'hull_warm')
        for x in range(25, 39):
            if (x, 28) in head:
                fig.put(x, 28, 'hull_warm', max(1, tone(fig, (x, 28)) - 2))
        vis = c_visor(fig)
        glass(fig, vis, keep)
        if fid:
            lamp(fig, keep, [(26, 32, 3), (27, 32, 4), (28, 32, 4), (27, 33, 3),
                             (33, 32, 3), (34, 32, 4), (35, 32, 4), (34, 33, 3)])
        else:
            lamp(fig, keep, eye_open(26, 30) + eye_open(33, 30))
        for cx in (21.5, 41.5):
            pod = fig.ellipse(cx, 31, 2.2, 3.4)
            pillow(fig, pod, 'panel')
            if cx > 32:
                darken(fig, pod)
        # segmented arms
        for side, ax0 in enumerate((17, 42)):
            if fid and side == 0:
                continue
            sh = fig.ellipse(ax0 + 2.5, 43, 2.6, 2.6)
            up = fig.rect(ax0, 44, ax0 + 4, 49, 1)
            cyl(fig, up, 'hull', glint=False)
            el = fig.rect(ax0, 50, ax0 + 4, 50)
            box(fig, el, 'panel', glint=False)
            lo = fig.rect(ax0, 51, ax0 + 4, 54, 1)
            cyl(fig, lo, 'hull_cool', glint=False)
            hd = fig.rect(ax0, 55, ax0 + 4, 57, 1)
            box(fig, hd, 'panel', glint=False)
            pillow(fig, sh, 'panel')
            if side:
                darken(fig, up | el | lo | hd | sh)
        if fid:
            # the unrolled end: a quilted flap hanging from the hand, plaster lining out
            flap = fig.poly([(12, 45), (21, 46), (22, 61), (11, 62)])
            cloth(fig, flap, 'plaster', lit=2, dark=2, folds=(17,))
            baffles(fig, flap, 'plaster', (53,))
            rows, _ = _rc(flap)
            rim = {p for p in flap if p[0] in (min(rows[p[1]]), max(rows[p[1]])) or p[1] == max(rows)}
            cloth(fig, rim, C_BAG, lit=1, dark=1, top=False)
            sh = fig.ellipse(19.5, 43, 2.6, 2.6)
            up = fig.rect(17, 40, 21, 44, 1)
            cyl(fig, up, 'hull', glint=False)
            pillow(fig, sh, 'panel')
            hd = fig.rect(14, 43, 18, 46, 1)
            box(fig, hd, 'panel', glint=False)
    else:
        d = 1 if view == 'E' else -1
        roll = spiral(fig, 21, 49, 5.2, C_BAG, lining='plaster', d=d)
        box(fig, R(fig, d, 29, 57, 33, 61), 'panel', glint=False)
        far = R(fig, d, 22, 62, 35, 65, 2)
        boot(fig, far, keep)
        darken(fig, far)
        boot(fig, R(fig, d, 25, 61, 41, 65, 3), keep, light=(mx(d, 37) if d == 1 else mx(d, 38), 63))
        torso = R(fig, d, 23, 40, 40, 57, 2)
        cyl(fig, torso, 'hull')
        band(fig, torso, (40, 41), 'panel', keep, rivets=((mx(d, 27), 40), (mx(d, 34), 40)))
        band(fig, torso, (55, 56), 'panel', keep, rivets=((mx(d, 27), 55), (mx(d, 34), 55)))
        dial = R(fig, d, 40, 45, 41, 52)
        box(fig, dial, 'hull_cool', glint=False)
        box(fig, R(fig, d, 27, 38, 36, 39), 'panel', glint=False)
        head = R(fig, d, 24, 22, 41, 37, 4)
        cyl(fig, head, 'hull_warm')
        for x in range(33, 41):
            p = (mx(d, x), 28)
            if p in head:
                fig.put(p[0], 28, 'hull_warm', max(1, tone(fig, p) - 2))
        vis = c_visor(fig, d) & head
        glass(fig, vis, keep)
        lamp(fig, keep, eye_side(d, 37, 30))
        pod = E(fig, d, 29.5, 31, 2.6, 3.6)
        pillow(fig, pod, 'panel')
        sh = E(fig, d, 31.5, 43, 2.6, 2.6)
        up = R(fig, d, 30, 44, 33, 49, 1)
        cyl(fig, up, 'hull', glint=False)
        box(fig, R(fig, d, 30, 50, 33, 50), 'panel', glint=False)
        lo = R(fig, d, 30, 51, 33, 54, 1)
        cyl(fig, lo, 'hull_cool', glint=False)
        hd = R(fig, d, 30, 55, 33, 57, 1)
        box(fig, hd, 'panel', glint=False)
        pillow(fig, sh, 'panel')
        arm_shadow(fig, up | lo, ('hull', 'hull_cool', 'hull_warm'))
        arm_gap(fig, up | lo, ('hull', 'hull_cool', 'hull_warm'))
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Upright barrel: domed white barrel, visor band, bedroll across the top of the back',
        question='A tall white barrel with a wrap-round visor band; the sleeping bag is a big quilted roll strapped '
                 'across the top of its back, showing past both shoulders and end-on (its spiral) in profile.',
        fn=option_a, palette=['hull', 'panel', 'void', 'path'],
        pose='Upright and patient as a night-light, arms at its sides: on call for whoever cannot sleep.',
        parts=[
            'bedroll (path, quilted baffles, two panel straps; spiral end in E/W): layer 0; back; '
            'bobs 1 px a frame late on walk and hop, becomes the pillow in nap',
            'boots x2 (panel, void magnet sole, cyan lock light): layer 1; foot; 6-frame clomp, lock light on at contact',
            'legs x2 (panel pistons): layer 1; hip; short swing, tucked in hop and sit',
            'barrel (hull_warm dome, hull body, hull_cool skirt, panel hoop): layer 2; hip; breath 1 px squash',
            'visor band (void glass, lamp eyes): layer 3; chest; eyes swap per state (half-lid, closed + z, ! hit)',
            'chest (seam, vent slots, lamp + cyan lights): layer 3; chest; lights pulse in cast',
            'arms x2 (hull_warm, panel shoulder ball and mitten): layer 4; chest; swing, wind-up, strike, guard',
        ],
        notes=[
            'Works: the crossbar roll over a plain barrel is unlike any folk; the spiral end reads as "sleeping bag".',
            'The slow blink is a lamp eye going from half-lid to a closed U and a small z on the visor.',
            'Risk: very symmetric and static; the stubby arms limit strike poses, so fights lean on the boots.',
            'Compared with Eastward 05: the white caravans and kiosks (pale plates, violet seams, lit upper-left rims).',
        ]),
    dict(
        label='B', name='Squat capsule: porthole visor, antenna lamp, the bag worn as a cape with a rolled collar',
        question='A wide egg-shaped capsule with a round porthole visor; the sleeping bag worn as a cape whose top '
                 'is rolled into a thick collar, its quilted tail flaring past both sides.',
        fn=option_b, palette=['hull', 'panel', 'void', 'path', 'plaster'],
        pose='Squat and snug, wrapped up like it is always a little cold on the station.',
        parts=[
            'cape (path quilt baffles, plaster lining turned down in the snuggle, scalloped hem): layer 0; chest (collar); sways 1 px late, wraps the body in nap',
            'boots x2 (panel half-domes, void magnet sole, cyan light): layer 1; foot; waddle walk, no legs',
            'capsule (hull dome, hull_cool skirt, seam, chest hatch): layer 2; hip; breath 1 px',
            'porthole (panel bezel with 4 rivets, void glass, lamp eyes): layer 3; head; eyes swap per state',
            'antenna (panel stalk, lamp tip): layer 3; head; springs back on hop and hit',
            'collar roll (path and path_warm, quilted): layer 4; chest; the perch for the familiar',
            'ball arms x2 (hull_warm, panel claws): layer 5; chest; swing, punch, hold the cape in guard',
        ],
        notes=[
            'Works: a bell shape with a collar is the cosiest read; the snuggle fidget is pure Bunk.',
            'Risk: the porthole + antenna lean towards a generic toy robot; no legs makes the 6-frame walk a waddle.',
            'The cape tail must not read as a skirt: hem scallops and quilt folds carry it.',
            'Compared with Eastward 05: the white port-a-cabins (round port, bezel rivets) and the quilted jackets.',
        ]),
    dict(
        label='C', name='Hooped barrel: helmet head with a half-moon visor, Sleep Cycle dial, bag roll at the hips',
        question='A helmet head with a half-moon visor on a barrel torso with two panel hoops and the Sleep Cycle '
                 'dial on the chest; the sleeping bag a roll strapped low across the back at the hips.',
        fn=option_c, palette=['hull', 'panel', 'void', 'path', 'plaster'],
        pose='Neat and attentive, head up and the dial showing: it keeps everyone\'s sleep on schedule.',
        parts=[
            'bag roll (path, quilted, plaster lining at the spiral end): layer 0; hip (back); '
            'unrolls as a flap in the fidget, spreads under it in nap',
            'disc feet x2 (panel, void magnet sole, cyan light): layer 1; foot; heavy flat clomp',
            'legs x2 (panel pistons): layer 1; hip; 6-frame swing',
            'barrel torso (hull, two panel hoops with rivets): layer 2; hip; breath 1 px',
            'dial (panel bezel, void face, lamp sector, needle): layer 3; chest; sector shows deep/dream stage',
            'head (hull_warm helmet, brow, half-moon visor, lamp eyes, panel ear pods): layer 4; chest; '
            'tilts 1 px in idle, nods in the blink',
            'arms x2 (hull + hull_cool segments, panel elbow and hand): layer 5; chest; full swing, strike, cast',
        ],
        notes=[
            'Works: the most rig-friendly (separate head, real arms and legs) and the dial puts the mechanic on the body.',
            'Risk: head + body + limbs is the most generic robot shape, closest to Pendle and Nix in outline.',
            'The barrel reads from the hoops; the bag at the hips is less visible from the front.',
            'Compared with Eastward 05: the trailer\'s white panels and its banded hoops/rails at the same height.',
        ]),
]


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


# =====================================================================================
# FINAL (revision round, 21 Oct): option A, the upright barrel, with grafts.
#   - from C: the Sleep Cycle dial on a chest hatch: a panel bezel, the deep half lit lamp,
#     the dream half dark glass with its tick, a needle; it reads at 2 device px.
#   - from B: the bag pulled round the front as the nap's sit-down; the cyan boot lights.
#   - fix: the barrel shaded as one cylinder (warm lit band in the left third with a sheen
#     streak, body, violet hull_cool shade at the right); seams, visor band and hoop curve
#     round the barrel (the ring dips at the front, seen from above). No vertical split.
#   - fix: the roll sits lower, behind the shoulders, its spiral end crossed by a strap and
#     buckle, plaster lining in the spiral: a roll, never an ear.
#   - profiles as forms: the dome's rim is a brow over the visor, the visor glass steps a
#     pixel proud, a lit sill under it as the chin step, a shaded cheek behind the glass.
# =====================================================================================
import math  # noqa: E402

F_BAG = 'path'
TOP, BOT = 24, 57          # barrel top and bottom rows at rest


def barrel_rows(cx, top, hw, lean=0.0, dome_h=9, height=33):
    """Row spans of the barrel: a dome cap, straight sides, knocked bottom corners; `lean`
    shears it (px at the top relative to the bottom)."""
    bot = top + height
    rows = {}
    for y in range(top, bot + 1):
        c = cx + lean * (bot - y) / height
        if y < top + dome_h:
            v = (top + dome_h - y - 0.5) / dome_h
            w = hw * math.sqrt(max(0.0, 1 - v * v)) + 0.4
        else:
            w = hw
        if y == bot:
            w = hw - 1.6
        elif y == bot - 1:
            w = hw - 0.6
        rows[y] = (int(round(c - w)), int(round(c + w)) - 1, c, w)
    return rows


def rows_mask(rows):
    return {(x, y) for y, (xl, xr, _, _) in rows.items() for x in range(xl, xr + 1)}


def hull_cyl(fig, rows, keep, sheen=True):
    """One cylinder of white hull: a warm lit band in the left third (hull_warm 4) with a
    sheen streak (5), the body (hull 3), the turn into shade (hull_cool 3, then 2) and the
    violet east edge (hull_cool 1); the dome's top plane lit, the underside dark."""
    mask = rows_mask(rows)
    ys = sorted(rows)
    for (x, y) in mask:
        xl, xr = rows[y][0], rows[y][1]
        f = (x - xl + 0.5) / max(1, xr - xl + 1)
        if f < 0.34:
            fam, t = 'hull_warm', 4
        elif f < 0.6:
            fam, t = 'hull', 3
        elif f < 0.76:
            fam, t = 'hull_cool', 3
        elif f < 0.9:
            fam, t = 'hull_cool', 2
        else:
            fam, t = 'hull_cool', 1
        top_here = (x, y - 1) not in mask
        if top_here and f < 0.76:
            fam, t = ('hull_warm', 4) if f < 0.5 else ('hull', 4)
        if (x, y + 1) not in mask:
            fam, t = ('hull_cool', 2) if f < 0.34 else ('hull_cool', 1)
        fig.put(x, y, fam, t)
    if sheen:
        for y in ys[2:-4]:
            xl, xr = rows[y][0], rows[y][1]
            gx = xl + max(1, int(round(0.2 * (xr - xl))))
            if (gx, y) in mask:
                fig.put(gx, y, 'hull_warm', 5)
    return mask


def ring_y(rows, y0, x, depth=1.3):
    """The row a ring round the barrel crosses column x: it dips at the front."""
    xl, xr, c, w = rows[y0]
    u = (x + 0.5 - c) / max(1.0, w)
    return y0 + int(round(depth * math.sqrt(max(0.0, 1 - u * u))))


def f_roll_front(fig, keep, top=22, x0=15, x1=48):
    """S: the bedroll behind the shoulders, round-ended, quilted, two straps with buckles."""
    h = 9
    roll = fig.rect(x0 + 3, top, x1 - 3, top + h - 1) | fig.ellipse(x0 + 3.5, top + h / 2, 3.8, h / 2) | \
        fig.ellipse(x1 - 3.5 + 1, top + h / 2, 3.8, h / 2)
    hcyl(fig, roll, F_BAG)
    quilt(fig, roll, F_BAG, (x0 + 3, x0 + 8, x1 - 9, x1 - 4))
    recolor(fig, {p for p in roll if p[0] >= x1 - 7}, 'path_cool')
    for sx in (x0 + 5, x1 - 5):
        st = fig.rect(sx, top, sx + 1, top + h - 1) & roll
        box(fig, st, 'panel', glint=False)
        fig.put(sx, top + 4, 'panel', 4)
        fig.put(sx + 1, top + 4, 'panel', 2)
        fig.put(sx, top + 5, 'panel', 1)
        fig.put(sx + 1, top + 5, 'panel', 1)
    return roll


def f_roll_end(fig, keep, cx, cy, r=5.4):
    """E/W: the roll seen end on, low behind the shoulders: a quilted spiral with the
    plaster lining in it, a panel strap across it and a buckle, so it reads as a roll."""
    outer = fig.rect(int(round(cx - r)), int(round(cy - r)) + 1, int(round(cx + r)) - 1, int(round(cy + r)) - 1, 3)
    pillow(fig, outer, F_BAG)
    ring = fig.ellipse(cx + 0.3, cy + 0.3, r - 1.6, r - 1.7)
    inner = fig.ellipse(cx + 0.3, cy + 0.3, r - 3.0, r - 3.1)
    for p in ring - inner:
        fig.put(p[0], p[1], 'plaster', 3 if p[0] < cx and p[1] < cy + 1 else 2)
    pillow(fig, inner, F_BAG)
    c = (int(round(cx)), int(round(cy)))
    fig.put(c[0], c[1], F_BAG, 1)
    fig.put(c[0] - 1, c[1], F_BAG, 1)
    # the strap: a 2 px panel band across the end, the buckle a lit 2 x 3 block on it
    sx = int(round(cx)) - 1
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in (sx, sx + 1):
            if (x, y) in outer:
                fig.put(x, y, 'panel', 3 if x == sx else 2)
    by = int(round(cy)) + 1
    for (x, y, t) in ((sx - 1, by - 1, 4), (sx, by - 1, 4), (sx + 1, by - 1, 3), (sx + 2, by - 1, 2),
                      (sx - 1, by, 3), (sx, by, 1), (sx + 1, by, 1), (sx + 2, by, 1),
                      (sx - 1, by + 1, 2), (sx, by + 1, 2), (sx + 1, by + 1, 2), (sx + 2, by + 1, 1)):
        fig.put(x, y, 'panel', t)
    keep.add((sx, by))
    return outer


def f_dial(fig, keep, cx, cy, stage='deep', bright=False):
    """The Sleep Cycle dial: a panel bezel (lit upper left, dark lower right), the deep
    half (left) lit lamp, the dream half dark glass with a pale tick, the needle at twelve.
    In the dream stage the halves swap."""
    bez = fig.ellipse(cx, cy, 4.7, 4.7)
    face = fig.ellipse(cx, cy, 3.3, 3.3)
    pillow(fig, bez - face, 'panel')
    for p in sorted(face):
        left = p[0] < cx - 0.5
        lit = left if stage == 'deep' else not left
        if lit:
            t = 4 if p[1] < cy - 0.5 else 3
            if bright:
                t += 1
            fig.glow(p[0], p[1], 'lamp', min(5, t))
            keep.add(p)
        else:
            fig.put(p[0], p[1], 'void', 2 if p[1] < cy - 0.5 else 1)
    nx = int(math.floor(cx - 0.5)) + 1
    for y in range(int(round(cy - 3.3)), int(round(cy)) + 1):
        if (nx, y) in face:
            fig.put(nx, y, 'hull_warm', 4)
            fig.fixed.discard((nx, y))
            keep.add((nx, y))
    return bez


def mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = fig.ellipse(cx, base - 5, 7.5, 5.5)
        pillow(fig, body, 'leaf')
        for x in (cx - 3, cx + 1):
            fig.put(x, base - 6, 'ink', 0)
            fig.put(x + 1, base - 6, 'ink', 0)
        for (x, y, t) in ((cx + 4, base - 11, 4), (cx + 5, base - 11, 4), (cx + 5, base - 10, 3), (cx + 5, base - 12, 4)):
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


EYES = {
    # (dx, dy, tone) for one eye, 4 wide, origin at its top left
    'open': [(0, 0, 4), (1, 0, 5), (2, 0, 4), (3, 0, 4), (1, 1, 3), (2, 1, 3)],
    'closed': [(0, 0, 3), (3, 0, 3), (0, 1, 3), (1, 1, 3), (2, 1, 3), (3, 1, 3)],
    'happy': [(1, 0, 4), (2, 0, 4), (0, 1, 3), (3, 1, 3), (0, 0, 3), (3, 0, 3)],
    'focus': [(0, 0, 4), (1, 0, 5), (2, 0, 4), (3, 0, 4)],
    'wide': [(0, 0, 4), (1, 0, 5), (2, 0, 5), (3, 0, 4), (0, 1, 3), (1, 1, 4), (2, 1, 4), (3, 1, 3)],
    'squeeze': [(0, 0, 4), (1, 0, 4), (2, 1, 4), (1, 1, 3), (0, 2, 4), (1, 2, 4)],
}


def put_eye(fig, keep, x, y, kind, flip=False):
    pts = EYES[kind]
    w = max(p[0] for p in pts)
    lamp(fig, keep, [(x + (w - dx if flip else dx), y + dy, t) for dx, dy, t in pts])


def final_front(view):
    """S idle and S fidget."""
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    f_roll_front(fig, keep)
    for x0 in (25, 35):
        box(fig, fig.rect(x0, 57, x0 + 3, 60), 'panel', glint=False)
    boot(fig, fig.rect(20, 60, 30, 65, 2), keep, light=(23, 62))
    boot(fig, fig.rect(33, 60, 43, 65, 2), keep, light=(36, 62))
    rows = barrel_rows(31.5, TOP, 11)
    body = hull_cyl(fig, rows, keep)
    # the dome's rim: a curved seam, the visor band under it, a lit sill
    yr = TOP + 9
    for x in range(rows[yr][0], rows[yr][1] + 1):
        ys = ring_y(rows, yr, x)
        fig.put(x, ys, fam_at(fig, (x, ys)), max(1, tone(fig, (x, ys)) - 2))
        vis = fig.rect(x, ys + 1, x, ys + 5) & body
        if rows[yr][0] < x < rows[yr][1]:
            glass_col = vis
            for p in glass_col:
                fig.put(p[0], p[1], 'void', 1)
            sill = (x, ys + 6)
            if sill in body:
                fig.put(x, ys + 6, fam_at(fig, sill), 4 if x < 37 else 3)
    vmask = {p for p in body if fam_at(fig, p) == 'void'}
    glass(fig, vmask, keep)
    if fid:
        put_eye(fig, keep, 25, 37, 'closed')
        put_eye(fig, keep, 33, 37, 'closed')
        lamp(fig, keep, zz(38, 35))
    else:
        put_eye(fig, keep, 25, 36, 'open')
        put_eye(fig, keep, 35, 36, 'open')
    # the chest hatch: a recessed frame (dark line, lit line inside at top and left)
    hx0, hy0, hx1, hy1 = 25, 43, 38, 52
    for x in range(hx0, hx1 + 1):
        for y in (hy0, hy1):
            fig.put(x, y, fam_at(fig, (x, y)), max(1, tone(fig, (x, y)) - 2))
        if x < hx1:
            fig.put(x, hy0 + 1, fam_at(fig, (x, hy0 + 1)), min(5, tone(fig, (x, hy0 + 1)) + 1))
    for y in range(hy0, hy1 + 1):
        for x in (hx0, hx1):
            fig.put(x, y, fam_at(fig, (x, y)), max(1, tone(fig, (x, y)) - 2))
    f_dial(fig, keep, 31.5, 47.5, stage='deep' if not fid else 'dream')
    lamp(fig, keep, [(23, 45, 3)], 'neon_cyan')
    # the belly hoop, curving round the front, with rivets
    for x in range(rows[53][0], rows[53][1] + 1):
        y = ring_y(rows, 53, x, 1.0)
        for yy in (y, y + 1):
            if (x, yy) in body:
                fig.put(x, yy, 'panel', max(1, min(4, tone(fig, (x, yy)) - (0 if yy == y else 1))))
    for x in (24, 31, 38):
        y = ring_y(rows, 53, x, 1.0)
        fig.put(x, y, 'panel', 5 if x < 32 else 4)
        keep.add((x, y))
    # shoulder straps from the roll over the dome to clips on the rim
    for x0 in (23, 39):
        m = {p for p in fig.rect(x0, 25, x0 + 1, 32) if p in body}
        box(fig, m, 'panel', glint=False)
    # arms: shoulder ball, a warm hull arm, a panel mitten; the east arm a tone back
    for side, ax0 in enumerate((16, 43)):
        up = fig.rect(ax0, 43, ax0 + 4, 50, 1)
        cyl(fig, up, 'hull_warm', glint=False)
        sh = fig.ellipse(ax0 + 3.5 if side == 0 else ax0 + 1.5, 43, 2.6, 2.6)
        pillow(fig, sh, 'panel')
        hd = fig.rect(ax0, 50, ax0 + 4, 53, 1)
        box(fig, hd, 'panel', glint=False)
        fig.put(ax0 + 2, 53, 'panel', 1)
        if side == 1:
            recolor(fig, up, 'hull_cool', -1)
            darken(fig, sh | hd)
    fig.outline()
    despeckle(fig, keep)
    return fig


FPOSES = {
    #          bx  by  lean  legs (far du, near du, near lift)  near hand (du, dy)  far hand    eyes
    'idle':   (0, 0, 0.0, (-2, 2, 0, 'stand'), (0, 10), None, 'open'),
    'ready':  (0, 1, 1.5, (-5, 4, 0, 'stand'), (6, 3), (3, 5), 'open'),
    'strike': (3, 1, 3.0, (-8, 7, 0, 'stand'), (18, 0), (-9, 7), 'focus'),
    'cast':   (0, 0, -1.0, (-4, 4, 0, 'stand'), (9, -11), (3, 6), 'wide'),
    'hit':    (-3, 0, -3.0, (-7, 4, 2, 'stand'), (5, -6), (-7, -3), 'squeeze'),
    'sit':    (-2, 6, 0.0, (8, 11, 0, 'sit'), (4, 8), None, 'closed'),
    'cheer':  (0, -5, 0.0, (-2, 3, 4, 'tuck'), (7, -15), (-5, -15), 'happy'),
}


def limb(fig, a, b, w, fam, far=False, piston=False):
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    n = max(1e-6, (dx * dx + dy * dy) ** 0.5)
    px, py = -dy / n * w / 2, dx / n * w / 2
    m = fig.poly([(x0 + px, y0 + py), (x1 + px, y1 + py), (x1 - px, y1 - py), (x0 - px, y0 - py)])
    pillow(fig, m, fam)
    if piston:
        # the telescoping forearm: its middle third is panel, a seam each end
        for p in m:
            t = ((p[0] + 0.5 - x0) * dx + (p[1] + 0.5 - y0) * dy) / (n * n)
            if 0.38 < t < 0.7:
                fig.put(p[0], p[1], 'panel', tone(fig, p))
    if far:
        darken(fig, m)
    return m


def arm_edge(fig, arm, body):
    """An arm over the barrel of the same white: the barrel just round it is a recess,
    dark (hull_cool 1) east and below the arm, a tone down west of it."""
    for (x, y) in sorted(arm):
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in arm or q not in body or fam_at(fig, q) not in ('hull', 'hull_warm', 'hull_cool'):
                continue
            if dx == 1 or dy == 1:
                fig.put(q[0], q[1], 'hull_cool', 1)
            else:
                fig.put(q[0], q[1], fam_at(fig, q), max(2, tone(fig, q) - 1))


def final_side(d, pose, familiar=False):
    bx, by, lean, legs, near, far, eyes = FPOSES[pose]
    fig = sk.Fig(W, H)
    keep = set()
    cx = AX + d * bx
    top, bot = TOP + by, BOT + by
    hw = 10
    rows = barrel_rows(cx, top, hw, lean * d)

    def U(y, u):
        """Column at row y, u in body half-widths along the facing (+1 the front)."""
        xl, xr, c, w = rows[y]
        return int(math.floor(c + d * u * w))

    # the roll, end on, low behind the shoulders (layer 0)
    ry = top + 3
    rcx = rows[ry + 6][2] - d * (hw + 0.5)
    perch = None
    roll = f_roll_end(fig, keep, rcx, ry, 5.6)
    if familiar:
        rtop = min(p[1] for p in roll)
        perch = (int(round(rcx)), rtop)
        mossling(fig, int(round(rcx - d * 1)), rtop + 2, d, keep)
    # far arm, far leg (a tone back)
    sh_y = top + 18
    sh = (U(sh_y, -0.15), sh_y)
    if far:
        hand_far = (sh[0] + d * far[0], sh[1] + far[1])
        limb(fig, sh, hand_far, 4, 'hull_warm', far=True)
        hm = fig.rect(int(hand_far[0]) - 2, int(hand_far[1]) - 1, int(hand_far[0]) + 1, int(hand_far[1]) + 2, 1)
        box(fig, hm, 'panel', glint=False)
        darken(fig, hm)
    fdu, ndu, lift, lg = legs
    hipx = rows[bot][2]

    def leg_and_boot(du, is_far, lift_px):
        if lg == 'sit':
            fx = int(round(hipx + d * du))
            limb(fig, (hipx + d * 2, bot - 1), (fx, bot - 1), 4, 'panel', far=is_far)
            bt = fig.rect(min(fx, fx + d * 4), bot - 6, max(fx, fx + d * 4), bot + 1, 1)
            box(fig, bt, 'panel', glint=False)
            for p in bt:
                if p[0] == (max(q[0] for q in bt) if d == 1 else min(q[0] for q in bt)):
                    fig.put(p[0], p[1], 'void', 1)
            if is_far:
                darken(fig, bt)
            else:
                lamp(fig, keep, [(min(fx, fx + d * 4) + 2, bot - 4, 3)], 'neon_cyan')
            return
        sole = SOLE - lift_px if lg != 'tuck' else bot + 6 - (0 if is_far else 1)
        fx = hipx + d * du
        limb(fig, (hipx + d * (du / 3.0), bot), (fx, sole - 4), 4, 'panel', far=is_far)
        a, b = sorted((int(round(fx - d * 4)), int(round(fx + d * 6))))
        bt = fig.rect(a, sole - 4, b, sole, 2)
        boot(fig, bt, keep, light=None if is_far else (int(round(fx + d * 2)) - (1 if d == -1 else 0), sole - 2))
        if is_far:
            darken(fig, bt)

    if lg != 'sit':
        leg_and_boot(fdu, True, 0)
    body = hull_cyl(fig, rows, keep)
    if lg != 'sit':
        leg_and_boot(ndu, False, lift)
    # dome rim: the brow over the visor, a pixel proud at the front
    ys = top + 9
    xs_row = range(rows[ys][0], rows[ys][1] + 1)
    for x in xs_row:
        fig.put(x, ys, fam_at(fig, (x, ys)), max(1, tone(fig, (x, ys)) - 2))
    fx0 = rows[ys][1] + 1 if d == 1 else rows[ys][0] - 1
    # the visor band from just behind the middle to the front, its glass a pixel proud
    vis = set()
    for y in range(ys + 1, ys + 7):
        xl, xr, c, w = rows[y]
        a, b = sorted((int(round(c - d * 0.15 * w)), (xr + 1) if d == 1 else (xl - 1)))
        for x in range(a, b + 1):
            vis.add((x, y))
    glass(fig, vis, keep)
    # brow lip over the proud glass, lit on top; the sill under it, lit: the chin step
    brow_x = rows[ys][1] + 1 if d == 1 else rows[ys][0] - 1
    fig.put(brow_x, ys, 'hull', 4 if d == -1 else 3)
    for y in (ys + 7,):
        xl, xr, c, w = rows[y]
        a, b = sorted((int(round(c - d * 0.15 * w)), (xr + 1) if d == 1 else (xl - 1)))
        for x in range(a, b + 1):
            fig.put(x, y, 'hull_warm' if x < c else 'hull', 4)
    # the cheek: the band's back end turns into shade
    for y in range(ys + 1, ys + 7):
        bxk = min(p[0] for p in vis if p[1] == y) if d == 1 else max(p[0] for p in vis if p[1] == y)
        q = (bxk - d, y)
        if q in body:
            fig.put(q[0], q[1], 'hull_cool', 2)
    # the eye, towards the front
    ey = ys + 3 if eyes != 'squeeze' else ys + 2
    exf = rows[ey][1] - 4 if d == 1 else rows[ey][0] + 1
    put_eye(fig, keep, exf, ey, eyes, flip=(d == -1))
    # the dial seen edge on: a panel bezel standing proud at the front, its lit rim
    dy0 = top + 19
    for y in range(dy0, dy0 + 8):
        xl, xr, c, w = rows[y]
        edge = xr if d == 1 else xl
        out = edge + d
        fig.put(edge, y, 'panel', 3 if y < dy0 + 4 else 2)
        if dy0 < y < dy0 + 7:
            fig.put(out, y, 'panel', 4 if (y < dy0 + 4 and d == -1) else 2 if y > dy0 + 4 else 3)
    for y in (dy0 + 2, dy0 + 3, dy0 + 4):
        xl, xr, c, w = rows[y]
        p = ((xr - 1) if d == 1 else (xl + 1), y)
        fig.glow(p[0], p[1], 'lamp', 4 if pose == 'cast' else 3)
        keep.add(p)
    # the belly hoop, with rivets
    hy = top + 29
    for x in range(rows[hy][0], rows[hy][1] + 1):
        for yy in (hy, hy + 1):
            fig.put(x, yy, 'panel', max(1, min(4, tone(fig, (x, yy)) - (0 if yy == hy else 1))))
    for u in (-0.5, 0.4):
        x = int(round(rows[hy][2] + d * u * hw))
        fig.put(x, hy, 'panel', 5 if x < rows[hy][2] else 4)
        keep.add((x, hy))
    # shoulder strap from the roll over the dome
    for y in range(top + 3, top + 9):
        xl, xr, c, w = rows[y]
        x = int(round(c - d * 0.55 * w))
        for xx in (x, x + 1):
            if (xx, y) in body:
                fig.put(xx, y, 'panel', 3 if xx == min(x, x + 1) else 2)
    if lg == 'sit':
        for du, f in ((legs[0], True), (legs[1], False)):
            leg_and_boot(du, f, 0)
    # near arm: shoulder ball, warm hull arm (telescoping in the strike), panel mitten
    hand_near = (sh[0] + d * near[0], sh[1] + near[1])
    arm = limb(fig, sh, hand_near, 4, 'hull_warm', piston=(pose == 'strike'))
    arm_edge(fig, arm, body)
    pillow(fig, fig.ellipse(sh[0] + 0.5, sh[1], 2.6, 2.6), 'panel')
    hx, hy2 = int(round(hand_near[0])), int(round(hand_near[1]))
    hm = fig.rect(hx - 2, hy2 - 1, hx + 1, hy2 + 2, 1)
    box(fig, hm, 'panel', glint=False)
    if pose == 'cast':
        # the deep stage released: two lamp motes rise from the raised mitten
        for (ox, oy) in ((d * 3, -4), (-d * 1, -6)):
            lamp(fig, keep, [(hx + ox, hy2 + oy, 4), (hx + ox + 1, hy2 + oy, 3)])
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig, perch


def final_nap():
    """The nap's sit-down (from B): sat on the floor facing S, the bag unrolled and pulled
    round its front up to the visor, the lining turned down, boot toes out under the hem,
    eyes closed, a lamp z; the familiar curled against its right side."""
    fig = sk.Fig(W, H)
    keep = set()
    by = 8
    rows = barrel_rows(31.5, TOP + by, 11, height=33)
    hull_cyl(fig, rows, keep)
    body = rows_mask(rows)
    y31 = TOP + by + 9
    for x in range(rows[y31][0], rows[y31][1] + 1):
        ys = ring_y(rows, y31, x)
        fig.put(x, ys, fam_at(fig, (x, ys)), max(1, tone(fig, (x, ys)) - 2))
        if rows[y31][0] < x < rows[y31][1]:
            for p in fig.rect(x, ys + 1, x, ys + 5) & body:
                fig.put(p[0], p[1], 'void', 1)
    vmask = {p for p in body if fam_at(fig, p) == 'void'}
    glass(fig, vmask, keep)
    ey = min(p[1] for p in vmask) + 2
    put_eye(fig, keep, 25, ey, 'closed')
    put_eye(fig, keep, 34, ey, 'closed')
    lamp(fig, keep, zz(39, ey - 6) + [(36 + 6, ey - 10, 3), (37 + 6, ey - 10, 3), (37 + 6, ey - 9, 3),
                                        (36 + 6, ey - 8, 3), (37 + 6, ey - 8, 3)])
    # the bag pulled round: a quilted path wrap from the visor's sill to the floor
    wy = max(p[1] for p in vmask) + 1
    wrap = (fig.rect(17, wy, 46, 60, 3) | fig.ellipse(31.5, 59.5, 17.5, 6.2)) - fig.rect(0, 66, 63, 71)
    pillow(fig, wrap, F_BAG)
    for x in range(14, 51):                       # baffles curving round the front
        for y0 in (wy + 6, wy + 11, wy + 16):
            c = (x + 0.5 - 31.5) / 17.5
            y = y0 + int(round(2.2 * math.sqrt(max(0.0, 1 - c * c))))
            if (x, y) in wrap and (x, y + 1) in wrap:
                fig.put(x, y, fam_at(fig, (x, y)), max(1, tone(fig, (x, y)) - 1))
                if (x, y - 1) in wrap and tone(fig, (x, y - 1)) < 4:
                    fig.put(x, y - 1, F_BAG, tone(fig, (x, y - 1)) + 1)
    turn = {p for p in wrap if p[1] in (wy, wy + 1, wy + 2)}
    cloth(fig, turn, 'plaster', lit=3, dark=3, bottom=False)
    for p in turn:
        if p[1] == wy + 2:
            fig.put(p[0], p[1], 'plaster', max(1, tone(fig, p) - 2))
    recolor(fig, {p for p in wrap if p[0] >= 44 and p[1] > wy + 2}, 'path_cool')
    # the mittens holding the edge
    for cx in (22, 40):
        box(fig, fig.rect(cx - 2, wy, cx + 1, wy + 3, 1), 'panel', glint=False)
    # boot toes out from under the hem
    for x0 in (22, 35):
        bt = fig.rect(x0, 62, x0 + 7, 65, 1)
        boot(fig, bt, keep, light=(x0 + 2, 63))
    mossling(fig, 54, SOLE + 1, -1, keep, curled=True)
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
    label='A final', name='Upright barrel (final): one white cylinder, curved visor band, dial hatch, bedroll shelf',
    chosen='A',
    grafts=[
        'From C: the Sleep Cycle dial on a recessed chest hatch: panel bezel, deep half lit lamp, dream half dark glass, '
        'needle at twelve; the halves swap in the dream stage (the fidget shows it), it brightens in a cast.',
        'From B: the bag pulled round the front as the nap sit-down (lining turned down, mittens holding the edge, boot '
        'toes out under the hem); the cyan boot lock lights in every view.',
        'Fix: one cylinder: warm lit band (hull_warm 4) with a sheen streak (5) in the left third, hull 3, then hull_cool '
        '3, 2 and a violet east edge 1; no vertical chest seam; dome rim, visor band and hoop curve round the front.',
        'Fix: the roll sits lower, behind the shoulders (top at the dome\'s third row); end on it is a quilted spiral '
        'with plaster lining, crossed by a panel strap and buckle: a roll, not an ear.',
        'Fix: profiles as forms: the dome rim a brow, the visor glass a pixel proud, a lit sill as the chin step, the '
        'band\'s back end in shade as the cheek.',
    ],
    palette=['hull', 'panel', 'void', 'path', 'plaster'],
    pose='Upright and patient as a night-light, arms at its sides: on call for whoever cannot sleep.',
    parts=[
        'familiar perch: on top of the bedroll, the side away from the foe (E: x smaller, W: x larger); layer -1; back',
        'bedroll (path quilt, path_cool end, plaster lining, panel straps and buckles): layer 0; back (shoulders); '
        'S: crossbar behind the shoulders; E/W: end on behind the dome; same anchor and layer every facing; '
        'unrolls round the front in the nap',
        'far leg + boot / far arm (panel, hull_warm, a tone back): layer 1; hip / chest; E/W',
        'barrel (one cylinder: hull_warm lit band and sheen, hull, hull_cool shade; curved rim seam, panel hoop): '
        'layer 2; hip; leans with the pose (shear), breath 1 px squash',
        'visor band (void glass, lamp eyes per state: open, closed + z, focus, wide, squeeze, happy): layer 3; head '
        '(dome); the slow blink is the signature',
        'chest hatch + Sleep Cycle dial (panel bezel, lamp/void halves, needle): layer 3; chest; stage swaps, '
        'brightens in cast; edge-on bezel proud of the front in E/W',
        'near leg + magnetic boot (panel piston, panel boot, void magnet sole, cyan lock light): layer 4; hip; '
        '6-frame clomp, tucked in cheer, forward in sit',
        'near arm (panel shoulder ball, hull_warm arm, panel mitten; the forearm telescopes in the strike): layer 5; '
        'chest; swing, wind-up, strike at full reach, cast up, guard',
    ],
    notes=[
        'Compared side by side with Eastward 05 at the same height: the white caravans and kiosks (one pale cylinder '
        'or plate lit in a band, violet seams, lit upper-left rims) and the quilted jackets of the townsfolk.',
        'Works: a barrel under a bedroll crossbar is unlike every folk; the familiar sits on the roll as a shelf, '
        'clear of the visor, in every fight pose.',
        'Risk: a rigid barrel; poses come from lean, the telescoping arm and the boots. The nap is a sit-down, not a '
        'lying barrel (cheaper and keeps the visor blink visible).',
        'Open for Matt: amber lamp eyes, never cyan glyphs (Nix owns those); the familiar\'s size on the roll.',
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
    sk.design_sheet('Bunk final (folk 13, Halcyon Station): A, the upright barrel, with grafts', [entry], OUT_FINAL,
                    note='44 art px, cell 64 x 72, foot (32, 66). World S/E/W, fidget, nap; fight E and W with the '
                         'stand-in Mossling on the bedroll. Lamp eyes per state, cyan boot lights.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], glows=['lamp', 'neon_cyan'], pose=FINAL['pose'],
                eyes={k: v[6] for k, v in FPOSES.items()} | {'fidget': 'closed + z', 'nap': 'closed + z Z'},
                perch_anchor=perches, measure=nums, notes=FINAL['notes'], _ok=ok)


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
                        palette=o['palette'], glows=['lamp', 'neon_cyan'], pose=o['pose'], notes=o['notes'],
                        measure=nums))
    sk.design_sheet('Bunk (folk 13, Halcyon Station): barrel body and the sleeping bag', OPTIONS, OUT_PNG,
                    note='44 art px, cell 64 x 72, foot (32, 66). Views: S, E, W idle and the S fidget key pose. '
                         'Glows (lamp eyes, neon cyan lock lights) are light sources only.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='bunk', height_art_px=44, cell=[W, H], foot=[AX, AY],
                       question='Barrel body and the sleeping bag.', options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
