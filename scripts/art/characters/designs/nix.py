"""Nix, Neon Harbour's 3 a.m. courier android: three design options (Claude J lane, batch 2).

Main question: hood, screen and pack silhouette.

    A  Round-screen hood: a big concrete hood framing a round dark screen-face with a
       crescent (the do-not-disturb moon), a tall slate delivery box on her back that shows
       past both shoulders. Silhouette: a round hood on a tall box.
    B  Antenna hood, sling box: a snug asphalt hood with two antenna bumps, a wide visor
       screen with a "z z" glyph, a cropped jacket on long legs and a slim stencilled
       concrete box slung at her right hip with a neon-pink light strip.
    C  Long parka, TV head: an A-line asphalt parka to the knee, the hood down as a thick
       roll round the neck, a boxy iron TV head with a screen, and the delivery box worn
       on her front, strapped to her chest.

Every option keeps the cast rules: the hood is Nix's alone; the reflective strip is a
snow 4-5 band with a sharp edge (not a glow); the face-screen is dark glass with a small
neon-cyan sleep glyph and a crack (dark with a lit edge); neon only as light sources.

Views: S idle, E idle, W idle (W is drawn, its light computed on its own pixels, never
mirrored pixels) and the S key pose of her fidget. Design sheets are review material;
production frames come from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/nix.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/nix-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/nix.json')
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/nix-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'nix')

W, H = 64, 72
AX, AY = 32, 66          # foot anchor: soles fill row 65, their outline lands on row 66
SOLE = AY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
GLOWS = ('neon_cyan', 'neon_pink')


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def mx(d, x):
    """Pixel column for a side view: E (d=1) as authored, W (d=-1) the geometry turned
    round the anchor column. Only geometry is turned; every tone is painted afterwards
    from the final pixel positions, so W keeps its own upper-left light."""
    return x if d >= 0 else 2 * AX - 1 - x


def mxc(d, x):
    """The same for a continuous coordinate (polygon vertex, ellipse centre)."""
    return x if d >= 0 else 2 * AX - x


def R(fig, d, x0, y0, x1, y1, knock=0):
    a, b = sorted((mx(d, x0), mx(d, x1)))
    return fig.rect(a, y0, b, y1, knock)


def P(fig, d, pts):
    return fig.poly([(mxc(d, x), y) for x, y in pts])


def E(fig, d, cx, cy, rx, ry):
    return fig.ellipse(mxc(d, cx), cy, rx, ry)


def cloth(fig, mask, fam, lit=2, dark=2, folds=(), top=True, bottom=True, base=3):
    """Cloth in vertical bands (house-style 5): a lit west band, the body, a shaded east
    band, a lit top row and a dark hem row. `folds` are x columns of tone 2 (a fold is a
    recess), each with its lit lip one pixel to the west."""
    mask = set(mask)
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
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
        fig.put(x, y, fam, t)
    for fx in folds:
        for (x, y) in mask:
            if x == fx and min(cols[x]) + 1 < y < max(cols[x]):
                fig.put(x, y, fam, base - 1)
                if (x - 1, y) in mask and tone(fig, (x - 1, y)) == base:
                    fig.put(x - 1, y, fam, base + 1)
    return mask


def pillow(fig, mask, fam, lo=0):
    """A round part (a hood, a head): the lit cap is a disc offset to the upper left and
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
        if (u + 0.42) ** 2 + (v + 0.5) ** 2 < 0.42:
            t = 4
        if (u + 0.28) ** 2 + (v + 0.32) ** 2 > 1.05:
            t = 2
        if (x, y + 1) not in mask and u > -0.3:
            t = min(t, 1 if u > 0.2 else 2)
        fig.put(x, y, fam, max(lo, t))


def box(fig, mask, fam, glint=True, base=3):
    """A machined part (house-style 4, metal): lit top row and west column, body, shaded
    east column and a dark underside, a two-pixel glint at the top left."""
    mask = set(mask)
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    for (x, y) in mask:
        t = base
        if x == min(rows[y]) or y == min(cols[x]):
            t = base + 1
        if x == max(rows[y]):
            t = base - 1
        if y == max(cols[x]):
            t = base - 2
        fig.put(x, y, fam, t)
    if glint:
        top = sorted(mask, key=lambda p: (p[1], p[0]))
        y0 = top[0][1]
        row = sorted(p for p in mask if p[1] == y0)
        for p in row[1:3]:
            fig.put(p[0], p[1], fam, base + 2)
    return mask


def strip(fig, mask, rows, fam_cloth):
    """The reflective strip: a snow band (tone 5 then 4 on the lit side, 4 then 3 in the
    shade) with a sharp edge, laid only over the cloth it is sewn to."""
    pts = [p for p in mask if p[1] in rows and fam_at(fig, p) == fam_cloth]
    if not pts:
        return set()
    by_row = {}
    for p in pts:
        by_row.setdefault(p[1], []).append(p[0])
    for y, xs in by_row.items():
        xl, xr = min(xs), max(xs)
        span = max(1, xr - xl)
        first = y == min(rows)
        for x in xs:
            east = (x - xl) / span > 0.72
            t = (4 if east else 5) if first else (3 if east else 4)
            fig.put(x, y, 'snow', t)
    return set(pts)


def glass(fig, mask):
    """Dark screen glass in asphalt: body tone 1, the lower-right crescent tone 0, and a
    two-step reflection at the upper left (3 under 4) - glass, never a glow."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 1
        if 0.55 * u + 0.85 * v > 0.75:
            t = 0
        fig.put(x, y, 'asphalt', t)
    order = sorted(mask, key=lambda p: (p[0] + p[1], p[1]))
    a = order[0]
    # a diagonal sheen: 2 px at the top-left corner, a second pair one step in
    sheen = [(a[0] + 1, a[1]), (a[0] + 1, a[1] + 1), (a[0] + 2, a[1] + 1)]
    for i, p in enumerate(sheen):
        if p in mask:
            fig.put(p[0], p[1], 'asphalt', 4 if i == 0 else 3)
    return mask


def zed(x0, y0, w, h):
    """A "z" for the sleep glyph: a top bar, a diagonal of 1-2 px steps, a bottom bar."""
    pts = [(x0 + i, y0, 0) for i in range(w)] + [(x0 + i, y0 + h - 1, 0) for i in range(w)]
    for k in range(1, h - 1):
        xc = x0 + (w - 1) - round(k * (w - 1) / (h - 1))
        pts += [(xc, y0 + k, 0), (xc + 1, y0 + k, 0)] if w >= 4 else [(xc, y0 + k, 0)]
    return pts


def glyph(fig, pts, keep, t=3):
    """The sleep glyph: neon cyan, a light source on the glass (never outlined)."""
    for (x, y, k) in pts:
        fig.glow(x, y, 'neon_cyan', t)
        keep.add((x, y))


def crack(fig, pts, keep):
    """A crack in the glass: a dark line with a lit edge one pixel to its west."""
    for (x, y) in pts:
        if fam_at(fig, (x, y)) == 'asphalt':
            fig.put(x, y, 'asphalt', 0)
            keep.add((x, y))
        if fam_at(fig, (x - 1, y)) == 'asphalt' and (x - 1, y) not in pts:
            fig.put(x - 1, y, 'asphalt', 3)
            keep.add((x - 1, y))


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour, unless it is a glint, a glyph, a rivet or the crack (`keep`). The tie-break
    is deterministic (batch 2 rule)."""
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


def legs(fig, d, fam, boot, top, xs, w=4, sole=SOLE, toe=1, far_dark=True, boot_h=4):
    """Two legs in trousers with boots. In S (d=0) side by side; in E/W the far leg first,
    a tone back, and the boot toes point the way she faces."""
    for i, x0 in enumerate(xs):
        if d == 0:
            leg = fig.rect(x0, top, x0 + w - 1, sole - boot_h)
            b = fig.rect(x0 - (1 if i == 0 else 0), sole - boot_h + 1, x0 + w - 1 + (1 if i == 1 else 0), sole, 1)
        else:
            leg = R(fig, d, x0, top, x0 + w - 1, sole - boot_h)
            b = R(fig, d, x0 - 1, sole - boot_h + 1, x0 + w - 1 + toe, sole, 1)
        cloth(fig, leg, fam, lit=1, dark=1, top=False, bottom=False)
        box(fig, b, boot, glint=False)
        if d != 0 and i == 0 and far_dark:
            for p in leg | b:
                f = fam_at(fig, p)
                fig.put(p[0], p[1], f, max(1, tone(fig, p) - 1))
        # the sole: one dark row
        for p in b:
            if p[1] == sole:
                fig.put(p[0], p[1], boot, 1)


def hand(fig, x, y, fam='iron', w=3, h=3):
    m = fig.rect(x, y, x + w - 1, y + h - 1, 1 if w >= 4 and h >= 4 else 0)
    box(fig, m, fam, glint=False)
    return m


def sleeve(fig, pts, fam, cuff=None, far=False):
    m = fig.poly(pts)
    cloth(fig, m, fam, lit=1, dark=1, bottom=True)
    if far:
        for p in m:
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    inner_line(fig, m, fam)
    return m


def inner_line(fig, m, fam):
    """The joint between an arm and the body is a recess: the arm's inner column (the
    side towards the anchor) sits at tone 1 below the shoulder, so the sleeve reads apart
    from a jacket of the same cloth."""
    rows = {}
    for (x, y) in m:
        rows.setdefault(y, []).append(x)
    y0 = min(rows)
    for y, xs in rows.items():
        if y < y0 + 2 or y == max(rows):
            continue
        xi = max(xs) if sum(xs) / len(xs) < AX else min(xs)
        fig.put(xi, y, fam, 1)


def arm_shadow(fig, m, body_fam):
    """Side views: the near arm throws a 1 px shadow on the body just east of it."""
    rows = {}
    for (x, y) in m:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        q = (max(xs) + 1, y)
        if fam_at(fig, q) == body_fam and y > min(rows) + 1:
            fig.put(q[0], q[1], body_fam, 1)


def thick(fig, a, b, w=4):
    """A limb as a filled quad of width w from point a to point b."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    n = max(1e-6, (dx * dx + dy * dy) ** 0.5)
    px, py = -dy / n * w / 2, dx / n * w / 2
    return fig.poly([(x0 + px, y0 + py), (x1 + px, y1 + py), (x1 - px, y1 - py), (x0 - px, y0 - py)])


def logo(fig, x, y, keep, fam='neon_pink'):
    """The courier's logo: a small neon-pink moon-and-arrow, 3 x 2, lit from inside."""
    for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1)):
        fig.glow(x + dx, y + dy, fam, 3)
        keep.add((x + dx, y + dy))


def stencil(fig, mask_pts, fam, keep):
    """Stencilled lettering on a box: short 2 px dashes a tone down."""
    for (x, y) in mask_pts:
        if fam_at(fig, (x, y)) == fam:
            fig.put(x, y, fam, max(1, tone(fig, (x, y)) - 1))


# =====================================================================================
# Option A: round-screen hood, tall slate box
# =====================================================================================
A_HOOD, A_JACKET, A_TROUSER, A_PACK, A_METAL = 'concrete', 'concrete', 'asphalt', 'slate', 'iron'


def a_pack_s(fig):
    m = fig.rect(19, 23, 44, 47, 2)
    box(fig, m, A_PACK)
    # the lid seam shows at the top corners: a dark line with a lit row under it
    for x in range(19, 45):
        if (x, 27) in m:
            fig.put(x, 27, A_PACK, 1)
            if (x, 28) in m:
                fig.put(x, 28, A_PACK, 4 if x < 32 else 3)


def a_hood_s(fig, keep, dy=0, tilt=0, fid=False):
    cx, cy = 32 + tilt, 28 + dy
    drape = fig.poly([(23 + tilt, 31 + dy), (41 + tilt, 31 + dy), (41 + tilt, 37), (23 + tilt, 37)])
    hood = fig.ellipse(cx, cy, 10.4, 9.6) | drape
    pillow(fig, hood, A_HOOD)
    # the drape over the shoulders is cloth: vertical bands, a fold either side of the chin
    cloth(fig, {p for p in drape if p[1] >= 34 + dy}, A_HOOD, lit=2, dark=3, folds=(27 + tilt, 37 + tilt), top=False)
    # the opening: a recessed rim (hood lining in shade), then the round screen
    rim = fig.ellipse(cx, cy + 1, 7.9, 7.0)
    for p in rim:
        fig.put(p[0], p[1], A_HOOD, 1)
    # the hood's own lip catches the light on its upper-left arc
    for p in rim:
        q_out = [(p[0] + dx, p[1] + dy2) for dx, dy2 in N4 if (p[0] + dx, p[1] + dy2) not in rim]
        if q_out and p[0] < cx + 1 and p[1] < cy + 1:
            for q in q_out:
                if q in hood:
                    fig.put(q[0], q[1], A_HOOD, 4)
        if q_out and p[0] > cx + 2 and p[1] > cy:
            for q in q_out:
                if q in hood:
                    fig.put(q[0], q[1], A_HOOD, 2)
    scr = fig.ellipse(cx + 0.5, cy + 1.5, 6.8, 6.0)
    glass(fig, scr)
    # the screen bezel: a thin iron ring where the glass meets the lining (top and left lit)
    for p in sorted(rim - scr):
        if any(q in scr for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1), (p[0] - 1, p[1]), (p[0], p[1] - 1))):
            up_left = p[0] <= cx and p[1] <= cy + 1
            fig.put(p[0], p[1], A_METAL, 3 if up_left else 1)
    # the glyph: the do-not-disturb crescent, opening to the right; fidget: brighter + z
    gx, gy = round(cx) - 2, round(cy) - 1
    pts = [(gx + 1, gy, 1), (gx + 2, gy, 0), (gx, gy + 1, 0), (gx, gy + 2, 0), (gx + 1, gy + 3, 0), (gx + 2, gy + 3, 1)]
    glyph(fig, pts, keep, t=3 if not fid else 4)
    if fid:
        glyph(fig, [(gx + 4, gy - 1, 0), (gx + 5, gy - 1, 0), (gx + 5, gy, 0), (gx + 4, gy + 1, 0), (gx + 5, gy + 1, 0)],
              keep, t=2)
    # drawstrings: two cords from the hood's chin with iron toggles
    for side, xx in ((-1, round(cx) - 3), (1, round(cx) + 3)):
        for yy in range(round(cy) + 8, round(cy) + 11):
            fig.put(xx, yy, 'snow', 2 if side < 0 else 1)
        fig.put(xx, round(cy) + 11, A_METAL, 4 if side < 0 else 3)
        fig.put(xx, round(cy) + 12, A_METAL, 2 if side < 0 else 1)
        keep |= {(xx, round(cy) + 11), (xx, round(cy) + 12)}
    crack(fig, [(round(cx) + 4, round(cy) - 2), (round(cx) + 4, round(cy) - 1), (round(cx) + 3, round(cy)),
                (round(cx) + 3, round(cy) + 1), (round(cx) + 2, round(cy) + 2)], keep)
    return hood


def a_torso_s(fig, keep, fid=False):
    body = fig.poly([(24.5, 34), (39.5, 34), (40.5, 50), (23.5, 50)])
    cloth(fig, body, A_JACKET, lit=2, dark=3, folds=(28, 36))
    # the zip: a dark seam with a lit lip to its west, an iron pull
    for y in range(36, 50):
        fig.put(32, y, A_JACKET, 1)
        fig.put(31, y, A_JACKET, 4 if y < 44 else 3)
    strip(fig, body, (45, 46), A_JACKET)
    for y in (45, 46):
        fig.put(32, y, A_JACKET, 1)
    fig.put(33, 38, A_METAL, 4)
    fig.put(33, 39, A_METAL, 2)
    keep |= {(33, 38), (33, 39)}
    # hip pockets: a flap (lit lip over its shadow) either side of the zip
    for (x0, x1) in ((26, 29), (35, 38)):
        for x in range(x0, x1 + 1):
            fig.put(x, 47, A_JACKET, 4 if x < 32 else 3)
            fig.put(x, 48, A_JACKET, 1)
    # pack straps from the shoulders: slate webbing, 2 px, lit west column
    for (x0, x1) in ((26, 27), (37, 38)):
        for y in range(35, 44):
            fig.put(x0, y, A_PACK, 2 if x0 > 32 else 3)
            fig.put(x1, y, A_PACK, 1 if x0 > 32 else 2)
        fig.put(x0, 41, A_METAL, 4 if x0 < 32 else 3)
        fig.put(x1, 41, A_METAL, 2 if x0 < 32 else 1)
        keep |= {(x0, 41), (x1, 41)}
    return body


def a_arms_s(fig, keep, fid=False):
    m = sleeve(fig, [(19, 35), (25, 35), (25, 51), (19.5, 51)], A_JACKET) if not fid else None
    if not fid:
        strip(fig, m, (40, 41), A_JACKET)
        hand(fig, 20, 51, w=4)
    m2 = sleeve(fig, [(39, 35), (45, 35), (44.5, 51), (39, 51)], A_JACKET, far=True)
    strip(fig, m2, (40, 41), A_JACKET)
    hand(fig, 40, 51, w=4)


def option_a(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        a_pack_s(fig)
        legs(fig, 0, A_TROUSER, A_METAL, 51, (26, 34), w=4)
        a_torso_s(fig, keep, fid)
        a_arms_s(fig, keep, fid)
        a_hood_s(fig, keep, dy=0, tilt=(1 if fid else 0), fid=fid)
        if fid:
            # her right hand comes up to tap the side of the screen: elbow out, two fingers on the bezel
            m = thick(fig, (22, 37), (18, 43), 5) | thick(fig, (18, 43), (23, 32), 4)
            cloth(fig, m, A_JACKET, lit=1, dark=1, bottom=False)
            strip(fig, m, (39, 40), A_JACKET)
            hand(fig, 22, 28, w=4, h=4)
            # two fingers on the bezel
            fig.put(26, 29, A_METAL, 4)
            fig.put(26, 30, A_METAL, 2)
            keep |= {(26, 29), (26, 30)}
    else:
        d = 1 if view == 'E' else -1
        # the pack, on her back (E: left of her, W: right of her)
        pk = R(fig, d, 17, 23, 28, 48, 2)
        box(fig, pk, A_PACK)
        for y in range(24, 50):          # its lid seam and a stencilled panel on the side
            for x in range(17, 29):
                p = (mx(d, x), y)
                if p in pk and y == 27:
                    fig.put(p[0], p[1], A_PACK, 1)
        for y in (28,):
            for x in range(18, 28):
                p = (mx(d, x), y)
                if p in pk:
                    fig.put(p[0], p[1], A_PACK, 4 if p[0] < min(q[0] for q in pk) + 7 else 3)
        # stencil bars and the pink logo on the side face
        for (x, y) in ((20, 34), (21, 34), (23, 34), (24, 34), (20, 37), (21, 37), (22, 37)):
            p = (mx(d, x), y)
            fig.put(p[0], p[1], A_PACK, 2)
        lx = min(mx(d, 20), mx(d, 22))
        logo(fig, lx, 42, keep)
        if d == -1:   # W: the box's visible face is its south-east side, a tone into the shade
            for p in pk:
                if fam_at(fig, p) == A_PACK and p not in fig.fixed:
                    fig.put(p[0], p[1], A_PACK, max(1, tone(fig, p) - 1))
        legs(fig, d, A_TROUSER, A_METAL, 51, (28, 32), w=4, toe=2)
        body = P(fig, d, [(26.5, 34), (38.5, 34), (39.5, 50), (26, 50)])
        cloth(fig, body, A_JACKET, lit=2, dark=3)
        fx = mx(d, 38)
        for y in range(36, 50):
            fig.put(fx, y, A_JACKET, 1 if d == 1 else 2)
        strip(fig, body, (45, 46), A_JACKET)
        # a strap over the shoulder to the pack
        for y in range(35, 45):
            for x in (28, 29):
                p = (mx(d, x), y)
                fig.put(p[0], p[1], A_PACK, 3 if p[0] == min(mx(d, 28), mx(d, 29)) else 2)
        # near arm hanging, a touch forward
        arm = P(fig, d, [(29.5, 35), (35, 35), (35.5, 51), (30, 51)])
        cloth(fig, arm, A_JACKET, lit=1, dark=1, bottom=True)
        arm_shadow(fig, arm, A_JACKET)
        strip(fig, arm, (40, 41), A_JACKET)
        hand(fig, min(mx(d, 31), mx(d, 33)), 51)
        # the hood in profile: a big round hood, deeper at the back, the screen a lens at the front
        hood = E(fig, d, 30.5, 28, 10, 9.6) | P(fig, d, [(22.5, 31), (38, 31), (37.5, 37), (24, 37)])
        pillow(fig, hood, A_HOOD)
        cloth(fig, {p for p in hood if p[1] >= 35}, A_HOOD, lit=2, dark=3, top=False)
        lens = E(fig, d, 38.4, 29.5, 3.8, 6.2)
        lining = E(fig, d, 37.4, 29.3, 4.8, 7.2) & hood
        for p in lining:
            fig.put(p[0], p[1], A_HOOD, 1)
        for p in lining:      # the lip: lit above (top arc), shaded under the chin
            up = (p[0], p[1] - 1)
            if up in hood and up not in lining:
                fig.put(up[0], up[1], A_HOOD, 4)
        # the hood's centre seam runs from the brow over the crown to the nape: a recess
        # (tone 2) with a lit lip (tone 4) on its upper-left side
        seam = [(36, 19), (34, 18), (32, 18), (30, 18), (28, 19), (26, 20), (24, 22), (22, 25), (21, 28)]
        for (x, y) in seam:
            p = (mx(d, x), y)
            if p in hood:
                fig.put(p[0], p[1], A_HOOD, 2)
                if (p[0], p[1] - 1) in hood:
                    fig.put(p[0], p[1] - 1, A_HOOD, 4 if p[0] < AX + 4 else 3)
        scr = lens
        glass(fig, scr)
        # the screen bulges a pixel past the hood (the face step); bezel on its back edge
        for p in sorted(scr):
            back = (p[0] - d, p[1])
            if back not in scr and back in lining:
                fig.put(back[0], back[1], A_METAL, 3 if p[1] < 29 else 1)
        sx0 = min(p[0] for p in scr)
        sx1 = max(p[0] for p in scr)
        gx = sx0 + 1 if d == 1 else sx1 - 2
        # a crescent seen at a slant: it opens to the right in every facing, as on the S screen
        pts = [(gx + 1, 27, 1), (gx, 28, 0), (gx, 29, 0), (gx + 1, 30, 1)]
        glyph(fig, pts, keep, t=3)
        if d == 1:
            crack(fig, [(sx1 - 1, 26), (sx1 - 1, 27), (sx1 - 2, 28)], keep)
        else:
            crack(fig, [(sx0 + 3, 26), (sx0 + 3, 27), (sx0 + 2, 28)], keep)
    fig.outline()
    despeckle(fig, keep)
    return fig


# =====================================================================================
# Option B: snug antenna hood, visor screen, cropped jacket, sling box with a light strip
# =====================================================================================
B_HOOD, B_JACKET, B_TROUSER, B_BOX, B_METAL = 'asphalt', 'asphalt', 'slate', 'concrete', 'iron'


def b_hood(fig, keep, d, dy=0, look=0, fid=False):
    """d=0: front. The hood is snug (a 19 px head), two antenna bumps pushed up under the
    cloth, a wide visor screen."""
    if d == 0:
        cx, cy = 32, 29 + dy
        hood = fig.ellipse(cx, cy, 9.6, 9.2) | fig.poly([(23.5, 31 + dy), (40.5, 31 + dy), (40, 37), (24, 37)])
        for bx in (25, 37):     # antenna bumps: 3 wide, 3 tall, rounded
            hood |= fig.rect(bx, cy - 11, bx + 2, cy - 8, 1) | fig.rect(bx, cy - 10, bx + 2, cy - 8)
        shell = fig.ellipse(cx, cy, 9.6, 9.2)
        pillow(fig, hood, B_HOOD, lo=1)
        pillow(fig, shell, B_HOOD, lo=1)
        for bx in (25, 37):     # each bump its own small part: lit top-left, shaded east
            fig.put(bx, cy - 10, B_HOOD, 4)
            fig.put(bx + 1, cy - 11, B_HOOD, 4 if bx < 32 else 3)
            fig.put(bx + 2, cy - 10, B_HOOD, 2)
            fig.put(bx + 1, cy - 10, B_HOOD, 3)
            fig.put(bx + 2, cy - 9, B_HOOD, 2)
            keep |= {(bx + 1, cy - 11)}
        cloth(fig, {p for p in hood if p[1] >= 34}, B_HOOD, lit=2, dark=3, top=False)
        # the visor: a rounded rectangle of glass in an iron bezel
        bez = fig.rect(24, cy - 4 + look, 40, cy + 4 + look, 2)
        box(fig, bez, B_METAL, glint=False)
        scr = fig.rect(25, cy - 3 + look, 39, cy + 3 + look, 2)
        glass(fig, scr)
        # glyph: "z z" small and large
        g = cy - 1 + look
        zz = zed(26, cy + look - 1, 4, 4) + zed(32, cy + look - 3, 5, 5)
        glyph(fig, zz, keep, t=3)
        crack(fig, [(37, cy - 3 + look), (36, cy - 2 + look), (36, cy - 1 + look), (35, cy + look)], keep)
        return hood
    cx, cy = mxc(d, 31), 29 + dy
    hood = E(fig, d, 31, cy, 9.2, 9.2) | P(fig, d, [(23.5, 31 + dy), (38, 31 + dy), (37.5, 37), (25, 37)])
    bx = 27                    # in profile the two bumps line up: the near one shows, the far one a step back
    hood |= R(fig, d, bx, cy - 11, bx + 2, cy - 8, 1) | R(fig, d, bx, cy - 10, bx + 2, cy - 8)
    pillow(fig, hood, B_HOOD, lo=1)
    lo_x = min(mx(d, bx), mx(d, bx + 2))
    fig.put(lo_x, cy - 10, B_HOOD, 4)
    fig.put(lo_x + 1, cy - 11, B_HOOD, 4)
    fig.put(lo_x + 2, cy - 10, B_HOOD, 2)
    fig.put(lo_x + 1, cy - 10, B_HOOD, 3)
    keep.add((lo_x + 1, cy - 11))
    cloth(fig, {p for p in hood if p[1] >= 34}, B_HOOD, lit=2, dark=3, top=False)
    # the visor wraps the front: a lens 6 wide in an iron bezel, stepping a pixel proud
    bez = R(fig, d, 33, cy - 4, 41, cy + 4, 2)
    box(fig, bez, B_METAL, glint=False)
    scr = R(fig, d, 34, cy - 3, 41, cy + 3, 2)
    glass(fig, scr)
    sx0, sx1 = min(p[0] for p in scr), max(p[0] for p in scr)
    gx = sx0 + 2 if d == 1 else sx0 + 1
    g = cy
    glyph(fig, zed(gx, g - 2, 4, 4), keep, t=3)
    if d == 1:
        crack(fig, [(sx1 - 1, cy - 3), (sx1 - 2, cy - 2)], keep)
    else:
        crack(fig, [(sx0 + 2, cy - 3), (sx0 + 1, cy - 2)], keep)
    # the cheek step: the hood's side face in shade just behind the bezel
    for y in range(cy - 3, cy + 4):
        p = (mx(d, 32), y)
        if p in hood and fam_at(fig, p) == B_HOOD:
            fig.put(p[0], p[1], B_HOOD, 2)
    return hood


def b_sling(fig, d, keep, x0, y0, far=False):
    """The slim stencilled concrete box, 7 x 12, on its hip; a pink light strip down its
    outer edge and a small logo."""
    m = fig.rect(x0, y0, x0 + 6, y0 + 11, 1)
    box(fig, m, B_BOX)
    # lid seam
    for x in range(x0, x0 + 7):
        if (x, y0 + 3) in m:
            fig.put(x, y0 + 3, B_BOX, 1)
            fig.put(x, y0 + 4, B_BOX, 4 if x < x0 + 4 else 3)
    # stencil dashes
    for (x, y) in ((x0 + 2, y0 + 7), (x0 + 3, y0 + 7), (x0 + 2, y0 + 9), (x0 + 3, y0 + 9), (x0 + 4, y0 + 9)):
        fig.put(x, y, B_BOX, 2)
    if far:
        for p in m:
            fig.put(p[0], p[1], B_BOX, max(1, tone(fig, p) - 1))
    else:
        sx = x0 + 5
        for y in range(y0 + 5, y0 + 10):
            fig.glow(sx, y, 'neon_pink', 4 if y < y0 + 7 else 3)
            keep.add((sx, y))
        logo(fig, x0 + 1, y0 + 1, keep)
    return m


def option_b(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        legs(fig, 0, B_TROUSER, B_METAL, 46, (27, 33), w=4, boot_h=5)
        body = fig.poly([(24.5, 36), (39.5, 36), (40.5, 47), (23.5, 47)])
        cloth(fig, body, B_JACKET, lit=2, dark=3, folds=(28, 36), base=3)
        for y in range(37, 47):
            fig.put(32, y, B_JACKET, 1)
            fig.put(31, y, B_JACKET, 4)
        strip(fig, body, (42, 43), B_JACKET)
        fig.put(32, 42, B_JACKET, 1)
        fig.put(32, 43, B_JACKET, 1)
        # a ribbed waistband: two rows a tone apart
        for x in range(24, 41):
            if (x, 46) in body:
                fig.put(x, 46, B_JACKET, 2 if (x // 2) % 2 else 1)
        # the sling strap: from her left shoulder (screen right) down across to the box at her right hip
        st = thick(fig, (39.5, 36), (26.5, 47.5), 2.6)
        for p in st:
            if p in body:
                fig.put(p[0], p[1], B_BOX, 3 if p[0] + p[1] < 75 else 2)
        fig.put(33, 41, B_METAL, 4)
        fig.put(34, 41, B_METAL, 2)
        keep |= {(33, 41), (34, 41)}
        # arms
        if not fid:
            b_sling(fig, 0, keep, 16, 48)
            m = sleeve(fig, [(21, 37), (25, 37), (24.5, 49), (20.5, 49)], B_JACKET)
            strip(fig, m, (45, 46), B_JACKET)
            hand(fig, 21, 49)
            m2 = sleeve(fig, [(39, 37), (43, 37), (43.5, 49), (39.5, 49)], B_JACKET, far=True)
            strip(fig, m2, (45, 46), B_JACKET)
            hand(fig, 40, 49)
            b_hood(fig, keep, 0)
        else:
            # checks the parcel list on her left wrist: forearm across the chest, head bowed
            b_sling(fig, 0, keep, 16, 48)
            m = sleeve(fig, [(21, 37), (25, 37), (24.5, 49), (20.5, 49)], B_JACKET)
            strip(fig, m, (45, 46), B_JACKET)
            hand(fig, 21, 49)
            m2 = thick(fig, (41, 38), (41, 44), 4) | thick(fig, (42, 44), (30, 43), 4)
            cloth(fig, m2, B_JACKET, lit=1, dark=1, bottom=True)
            for p in m2:
                fig.put(p[0], p[1], B_JACKET, max(1, tone(fig, p) - 1) if p[1] > 44 else tone(fig, p))
            # the wrist screen: 4 x 2 of glass with a cyan list (two lit rows)
            ws = fig.rect(31, 41, 35, 43)
            box(fig, ws, B_METAL, glint=False)
            for x in (32, 33, 34):
                fig.glow(x, 42, 'neon_cyan', 4 if x < 34 else 3)
                keep.add((x, 42))
            hand(fig, 28, 41, w=3, h=3)
            b_hood(fig, keep, 0, dy=1, look=1, fid=True)
    else:
        d = 1 if view == 'E' else -1
        if d == -1:              # W: the box rides her right hip, the far side, behind her
            b_sling(fig, d, keep, mx(d, 22) - 6, 44, far=True)
        legs(fig, d, B_TROUSER, B_METAL, 46, (28, 32), w=4, toe=2, boot_h=5)
        body = P(fig, d, [(26.5, 36), (37.5, 36), (38.5, 47), (25.5, 47)])
        cloth(fig, body, B_JACKET, lit=2, dark=3)
        fx = mx(d, 37)
        for y in range(37, 47):
            fig.put(fx, y, B_JACKET, 1 if d == 1 else 2)
        strip(fig, body, (42, 43), B_JACKET)
        for x in range(20, 44):
            p = (x, 46)
            if p in body:
                fig.put(x, 46, B_JACKET, 2 if (x // 2) % 2 else 1)
        # the strap over the near shoulder
        for y in range(36, 46):
            p = (mx(d, 31 + (y - 36) // 4), y)
            fig.put(p[0], p[1], B_BOX, 3 if d == -1 else 2)
        arm = P(fig, d, [(29.5, 37), (33.5, 37), (34, 49), (30, 49)])
        cloth(fig, arm, B_JACKET, lit=1, dark=1, bottom=True)
        arm_shadow(fig, arm, B_JACKET)
        strip(fig, arm, (45, 46), B_JACKET)
        hand(fig, min(mx(d, 30), mx(d, 32)), 49)
        if d == 1:               # E: the box rides her right hip, the near side, in front of the hip
            b_sling(fig, d, keep, 25, 45)
        b_hood(fig, keep, d)
    fig.outline()
    despeckle(fig, keep)
    return fig


# =====================================================================================
# Option C: long parka with the hood down, TV head, box worn on the front
# =====================================================================================
C_PARKA, C_TV, C_BOX = 'asphalt', 'iron', 'concrete'


def c_tv(fig, keep, d, dy=0, fid=False):
    """A boxy TV head: an iron casing with knocked corners, a deep bezel, the glass, and
    the hood down as a thick roll round the neck behind it."""
    if d == 0:
        roll = fig.ellipse(32, 35 + dy, 11, 4)
        pillow(fig, roll, C_PARKA, lo=1)
        for x in range(21, 44):             # the roll's quilting: three puffs a side, dark seams
            if x in (25, 29, 35, 39) and (x, 35 + dy) in roll:
                fig.put(x, 35 + dy, C_PARKA, 1)
                fig.put(x, 36 + dy, C_PARKA, 1)
        case = fig.rect(22, 17 + dy, 42, 33 + dy, 3)
        box(fig, case, C_TV)
        # the side planes: the casing is deep, its top lit and its east side in shade
        for y in range(18 + dy, 33 + dy):
            for x in (41, 42):
                if (x, y) in case:
                    fig.put(x, y, C_TV, 2 if x == 41 else 1)
        for x in range(23, 42):
            fig.put(x, 18 + dy, C_TV, 4)
        # a rivet at each corner of the bezel
        for (x, y) in ((24, 19 + dy), (39, 19 + dy), (24, 31 + dy), (39, 31 + dy)):
            fig.put(x, y, C_TV, 4)
            fig.put(x, y + 1, C_TV, 1)
            keep |= {(x, y), (x, y + 1)}
        bez = fig.rect(24, 20 + dy, 39, 30 + dy, 2)
        for p in bez:
            fig.put(p[0], p[1], C_TV, 1)
        scr = fig.rect(25, 21 + dy, 39, 30 + dy, 2)
        glass(fig, scr)
        # a lit lip on the bezel's lower edge (the recess's floor catches the light)
        for x in range(26, 39):
            fig.put(x, 30 + dy, C_TV, 3)
        g = 24 + dy
        if not fid:
            # two closed, sleepy eye-arcs: the sleep glyph as a face
            glyph(fig, [(27, g + 1, 0), (28, g + 2, 0), (29, g + 2, 0), (30, g + 1, 0),
                        (34, g + 1, 0), (35, g + 2, 0), (36, g + 2, 0), (37, g + 1, 0)], keep, t=3)
        else:
            # the set flips: a rolling bar, then the big crescent
            glyph(fig, [(27, g + 3, 0), (28, g + 3, 0), (29, g + 3, 0), (30, g + 3, 0), (31, g + 3, 0),
                        (32, g + 3, 0), (33, g + 3, 0), (34, g + 3, 0), (35, g + 3, 0), (36, g + 3, 0),
                        (37, g + 3, 0)], keep, t=1)
            glyph(fig, [(31, g - 2, 1), (32, g - 2, 1), (30, g - 1, 0), (30, g, 0), (30, g + 1, 0),
                        (31, g + 2, 1), (32, g + 2, 1)], keep, t=3)
        crack(fig, [(37, 21 + dy), (36, 22 + dy), (36, 23 + dy), (35, 24 + dy)], keep)
        return case
    roll = E(fig, d, 29, 35 + dy, 9, 4)
    pillow(fig, roll, C_PARKA, lo=1)
    # the hood down: a soft lump hanging at her back
    lump = E(fig, d, 22.5, 37 + dy, 4.5, 5)
    cloth(fig, lump, C_PARKA, lit=1, dark=2)
    case = R(fig, d, 24, 17 + dy, 41, 33 + dy, 3)
    box(fig, case, C_TV)
    for x in range(min(mx(d, 25), mx(d, 40)), max(mx(d, 25), mx(d, 40)) + 1):
        fig.put(x, 18 + dy, C_TV, 4)
    # the side of the set is a plane in shade, the screen face a plane turned towards her front
    for y in range(19 + dy, 33 + dy):
        for x in range(24, 34):
            p = (mx(d, x), y)
            if p in case and fam_at(fig, p) == C_TV and tone(fig, p) == 3:
                fig.put(p[0], p[1], C_TV, 2 if d == 1 else 3)
    # vents on the side: three 2 px slots
    for y in (23, 26, 29):
        for x in (27, 28, 29):
            p = (mx(d, x), y + dy)
            fig.put(p[0], p[1], C_TV, 1)
    bez = R(fig, d, 35, 20 + dy, 41, 30 + dy, 1)
    for p in bez:
        fig.put(p[0], p[1], C_TV, 1)
    scr = R(fig, d, 36, 21 + dy, 41, 29 + dy, 1)
    glass(fig, scr)
    sx0, sx1 = min(p[0] for p in scr), max(p[0] for p in scr)
    gx = sx0 + 2 if d == 1 else sx0 + 1
    g = 24 + dy
    glyph(fig, [(gx, g + 1, 0), (gx + 1, g + 2, 0), (gx + 2, g + 1, 0)], keep, t=3)
    glyph(fig, [(gx + 1, g - 2, 1), (gx, g - 1, 0)], keep, t=2)
    if d == 1:
        crack(fig, [(sx1 - 1, 22 + dy), (sx1 - 1, 23 + dy), (sx1 - 2, 24 + dy)], keep)
    else:
        crack(fig, [(sx0 + 3, 22 + dy), (sx0 + 3, 23 + dy), (sx0 + 2, 24 + dy)], keep)
    return case


def c_box(fig, keep, x0, y0, w=12, h=10, side=0):
    """The delivery box worn on her front: concrete, stencilled, a pink logo."""
    m = fig.rect(x0, y0, x0 + w - 1, y0 + h - 1, 1)
    box(fig, m, C_BOX)
    for x in range(x0, x0 + w):           # the lid flap seam
        if (x, y0 + 2) in m:
            fig.put(x, y0 + 2, C_BOX, 1)
            fig.put(x, y0 + 3, C_BOX, 4 if x < x0 + w // 2 else 3)
    for (dx, dy) in ((2, 6), (3, 6), (5, 6), (6, 6), (2, 8), (3, 8), (4, 8)):
        if (x0 + dx, y0 + dy) in m and dx < w - 1:
            fig.put(x0 + dx, y0 + dy, C_BOX, 2)
    if w >= 9:
        logo(fig, x0 + w - 5, y0 + 5, keep)
    return m


def option_c(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        fid = view == 'Sf'
        legs(fig, 0, 'asphalt', C_TV, 58, (27, 33), w=4, boot_h=4)
        parka = fig.poly([(23.5, 35), (40.5, 35), (45, 60), (19, 60)])
        cloth(fig, parka, C_PARKA, lit=2, dark=3, folds=(24, 30, 35, 40))
        # front opening and the reflective band at the hem and chest
        for y in range(44, 60):
            fig.put(32, y, C_PARKA, 1)
            fig.put(31, y, C_PARKA, 4 if y < 52 else 3)
        strip(fig, parka, (55, 56), C_PARKA)
        fig.put(32, 55, C_PARKA, 1)
        fig.put(32, 56, C_PARKA, 1)
        # the box worn on the front: straps round her neck (concrete webbing)
        for y in range(36, 41):
            for x in (26, 37):
                fig.put(x, y, C_BOX, 3 if x < 32 else 2)
        c_box(fig, keep, 26, 40, w=12, h=10)
        if not fid:
            m = sleeve(fig, [(19, 36), (24, 36), (22.5, 52), (17.5, 52)], C_PARKA)
            strip(fig, m, (48, 49), C_PARKA)
            hand(fig, 18, 52)
            m2 = sleeve(fig, [(40, 36), (45, 36), (46.5, 52), (41.5, 52)], C_PARKA, far=True)
            strip(fig, m2, (48, 49), C_PARKA)
            hand(fig, 42, 52)
            c_tv(fig, keep, 0, dy=1)
        else:
            m2 = sleeve(fig, [(40, 36), (45, 36), (46.5, 52), (41.5, 52)], C_PARKA, far=True)
            strip(fig, m2, (48, 49), C_PARKA)
            hand(fig, 42, 52)
            c_tv(fig, keep, 0, dy=2, fid=True)
            # she gives the set a smack on top: her right arm up, the hand flat on the casing
            m = thick(fig, (21, 37), (16, 30), 5) | thick(fig, (16, 30), (21, 20), 4)
            cloth(fig, m, C_PARKA, lit=1, dark=1, bottom=False)
            strip(fig, m, (32, 33), C_PARKA)
            hand(fig, 20, 17, w=5, h=3)
    else:
        d = 1 if view == 'E' else -1
        legs(fig, d, 'asphalt', C_TV, 58, (28, 32), w=4, toe=2, boot_h=4)
        parka = P(fig, d, [(25.5, 35), (37.5, 35), (40.5, 60), (22, 60)])
        cloth(fig, parka, C_PARKA, lit=2, dark=3, folds=(mx(d, 28),))
        strip(fig, parka, (55, 56), C_PARKA)
        for y in range(36, 41):
            p = (mx(d, 34), y)
            fig.put(p[0], p[1], C_BOX, 2 if d == 1 else 3)
        # the box on her front stands proud of the parka: its side is the face we see
        bx = mx(d, 35) if d == 1 else mx(d, 41)
        c_box(fig, keep, bx, 40, w=7, h=10)
        arm = P(fig, d, [(28.5, 36), (33.5, 36), (32, 52), (27, 52)])
        cloth(fig, arm, C_PARKA, lit=1, dark=1, bottom=True)
        arm_shadow(fig, arm, C_PARKA)
        strip(fig, arm, (48, 49), C_PARKA)
        hand(fig, min(mx(d, 28), mx(d, 30)), 52)
        c_tv(fig, keep, d, dy=1)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Round-screen hood: big concrete hood, round screen-face, tall slate box on the back',
        question='A big hood frames a round screen-face (the do-not-disturb crescent); the pack is a tall slate box '
                 'that shows past both shoulders.',
        fn=option_a, palette=['concrete', 'asphalt', 'slate', 'snow', 'iron'],
        pose='Square and unhurried, hands loose, the box riding high: the last courier on the 3 a.m. round.',
        parts=[
            'delivery box (slate, lid seam, stencil, neon-pink logo): layer 0 (back); back; bobs 1 px a step late, '
            'stays on her back in nap (she curls against it)',
            'legs x2 (asphalt trousers, iron boots): layer 1; hip; 6-frame swing, tuck in hop and nap, forward in sit',
            'jacket torso (concrete bands, zip, snow strip, slate straps): layer 2; hip; breath 1 px',
            'far sleeve (concrete, a tone back, iron hand): layer 1 (E/W), 3 (S); chest; swing, guard',
            'hood (concrete, lit lip, shaded lining): layer 4; chest; drapes 1 px late on hop, '
            'falls forward over the screen in nap',
            'face-screen (asphalt glass, iron bezel, cyan glyph, crack): layer 5; head; glyph swaps per state '
            '(crescent idle, ! hit, ^ ^ cheer, z nap)',
            'near sleeve (concrete, strip, iron hand): layer 6; chest; swing, wind-up, strike, cast, tap in fidget',
        ],
        notes=[
            'Works: a round hood on a tall box is a silhouette no other folk has; the crescent is the DND icon.',
            'Screen: dark asphalt glass with a stepped upper-left sheen; the crack is dark with a lit west edge.',
            'Risk: concrete hood and jacket are one value; the strip and box edges carry the read at 2 px.',
            'Compared with Eastward 05: John\'s backpack (one big block, lit top edge) and jacket folds in 3 bands.',
        ]),
    dict(
        label='B', name='Antenna hood: snug asphalt hood with two bumps, visor screen, sling box at the hip',
        question='A snug cropped hood with two antenna bumps and a wide visor screen ("z z"); the pack is a slim '
                 'stencilled box slung at her right hip with a pink light strip.',
        fn=option_b, palette=['asphalt', 'slate', 'concrete', 'snow', 'iron'],
        pose='Leggy and alert, bumps up, weight ready to go: she has one more drop before dawn.',
        parts=[
            'sling box (concrete, stencil, pink strip and logo): layer 0 in W (far hip), 4 in S/E; hip (right); '
            'swings a frame behind on walk, bumps on hop',
            'legs x2 (slate trousers, tall iron boots): layer 1; hip; long 6-frame stride',
            'cropped jacket (asphalt bands, zip, rib waistband, snow strip, concrete strap): layer 2; hip; breath 1 px',
            'far sleeve (asphalt, a tone back): layer 1/3; chest; swing, guard',
            'hood with antenna bumps (asphalt): layer 5; chest; bumps twitch on hit and cheer (antenna = ears)',
            'visor (iron bezel, asphalt glass, cyan "z z", crack): layer 6; head',
            'near sleeve + wrist screen (asphalt, iron, cyan list): layer 7; chest; swing, strike, cast, fidget check',
        ],
        notes=[
            'Works: bumps make a cat-eared hood that reads at 2 px; long legs and a high crop set her apart. '
            'The "z Z" is 4-5 px tall (a 3 px z reads as an I).',
            'Wrist screen gives the fidget (checks the parcel list) and a natural cast pose.',
            'Risk: an asphalt hood and jacket at night go very dark: the strip and the visor must carry it.',
            'Compared with Eastward 05: John and the woman in teal (2-3 tone sleeves, a clear hem row).',
        ]),
    dict(
        label='C', name='Long parka, TV head: hood down as a roll, iron TV head, box worn on the front',
        question='A long reflective parka with the hood down as a thick roll; a boxy TV-shaped head; the delivery '
                 'box worn on her front.',
        fn=option_c, palette=['asphalt', 'iron', 'concrete', 'snow'],
        pose='Patient, boxy and a little old-fashioned, parcel held to her chest like something precious.',
        parts=[
            'hood (asphalt, down: a quilted roll and a lump at the back): layer 0 (lump), 3 (roll); chest',
            'legs x2 (asphalt, iron boots): layer 1; hip; short steps under the hem',
            'parka (asphalt bands, open front, snow hem band): layer 2; hip; the hem sways 1 px after each step',
            'delivery box on the chest (concrete, stencil, pink logo, neck straps): layer 4; chest; '
            'bobs with breath, held in both arms in the nap',
            'TV head (iron casing, rivets, side vents, asphalt glass, cyan closed-eye arcs, crack): layer 5; chest; '
            'tilts in idle, flips its picture in the fidget',
            'sleeves x2 (asphalt, strip, iron hands): layer 1/6; chest; swing, smack, strike, cast',
        ],
        notes=[
            'Works: a square head over a bell parka is the most unlike the soft folk; the closed-eye arcs read at 2 px.',
            'Risk: the hood down is the least hood-like; a 21 px TV is heavy and close to Bunk\'s robot look.',
            'The box on the front blocks the chest in fights; strikes must come from the side.',
            'Compared with Eastward 05: the woman in the purple cardigan (placket, a hem row) for the parka.',
        ]),
]


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


# =====================================================================================
# FINAL (revision round, 21 Oct): option B, the antenna hood, with grafts.
#   - from A: a glyph for each state on the visor (crescent idle, "z Z" nap, ring cast,
#     X hit, heart cheer, chevron strike), one layer of cheap expression.
#   - from A: the delivery box bigger and more readable, still slim at the hip: a lit top
#     edge, a lid seam, a stencil and the small pink logo, on ONE anchor (the back of the
#     right hip) and ONE layer (0, behind the body) in every facing, so the perch stays clear.
#   - from C (craft): the crack across the visor, and fold bands on the jacket.
#   - reflective strips with a lit edge and a shaded edge; the dark jacket in the full
#     asphalt ramp (1 to 5) with a concrete yoke and rib, so it never goes muddy.
#   - profiles as forms: a hood brow over the visor, the visor stepping proud, a chin step.
# =====================================================================================
F_HOOD, F_JACKET, F_YOKE, F_TROUSER, F_METAL, F_BOX = 'asphalt', 'asphalt', 'concrete', 'slate', 'iron', 'concrete'

GLYPHS = {
    'crescent': ('.XX', 'X..', 'X..', '.XX'),
    'z': ('XXXX', '..XX', '.XX.', 'XXXX'),
    'Z': ('XXXXX', '...XX', '..XX.', '.XX..', 'XXXXX'),
    'ring': ('.XX.', 'X..X', 'X..X', '.XX.'),
    'x': ('X..X', '.XX.', '.XX.', 'X..X'),
    'heart': ('XX.XX', 'XXXXX', '.XXX.', '..X..'),
    'chevron': ('XX..', '.XX.', '..XX', '.XX.', 'XX..'),
}


def put_glyph(fig, name, x0, y0, keep, t=3, flip=False):
    rows = GLYPHS[name]
    w = len(rows[0])
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == 'X':
                x = x0 + (w - 1 - i if flip else i)
                fig.glow(x, y0 + j, 'neon_cyan', t)
                keep.add((x, y0 + j))


def strip2(fig, mask, rows, fam_cloth):
    """Reflective strip, final: two rows of snow with a lit top edge (5, then 4 towards the
    east) and a shaded lower edge (3, then 2), the east end a further step into shade, so
    the band turns with the form instead of lying on it as a flat white bar."""
    pts = [p for p in mask if p[1] in rows and fam_at(fig, p) == fam_cloth]
    by_row = {}
    for p in pts:
        by_row.setdefault(p[1], []).append(p[0])
    for y, xs in by_row.items():
        xl, xr = min(xs), max(xs)
        span = max(1, xr - xl)
        first = y == min(rows)
        for x in xs:
            f = (x - xl) / span
            if first:
                t = 5 if f < 0.5 else 4
            else:
                t = 3 if f < 0.5 else 2
            if x == xr and span >= 3:
                t -= 1
            fig.put(x, y, 'snow', max(1, t))
    return set(pts)


def limb(fig, a, b, fam, w=4, far=False, band=None, cuff=None):
    """A sleeve or a leg as a thick segment, shaded as cloth; `band` = (t0, t1) along it
    gets the reflective strip; `cuff` = t0 gets a concrete rib cuff to the end. Where it
    lies over the same cloth, the arm throws a 1 px shadow (tone 1) on its east and lower
    side and a recess (tone 2) on its west, so the joint reads as a joint."""
    m = thick(fig, a, b, w) | fig.ellipse(a[0], a[1], w / 2, w / 2)
    under = {}
    for (x, y) in m:
        for q, t in (((x + 1, y), 1), ((x, y + 1), 1), ((x - 1, y), 2)):
            if q not in m and fam_at(fig, q) in (fam, F_YOKE) and isinstance(tone(fig, q), int):
                under[q] = min(t, under.get(q, 9))
    for q in sorted(under):
        fig.put(q[0], q[1], fam_at(fig, q), under[q])
    cloth(fig, m, fam, lit=1, dark=1, bottom=False)
    (x0, y0), (x1, y1) = a, b
    L2 = max(1e-6, (x1 - x0) ** 2 + (y1 - y0) ** 2)
    rows = {}
    for p in m:
        t = ((p[0] + 0.5 - x0) * (x1 - x0) + (p[1] + 0.5 - y0) * (y1 - y0)) / L2
        rows[p] = t
    if band:
        bp = [p for p, t in rows.items() if band[0] <= t < band[1]]
        bt = [p for p, t in rows.items() if band[0] <= t < (band[0] + band[1]) / 2]
        for p in bp:
            lit_side = p in bt
            west = p[0] <= (x0 + x1) / 2
            fig.put(p[0], p[1], 'snow', (5 if west else 4) if lit_side else (3 if west else 2))
    if cuff is not None:
        for p, t in rows.items():
            if t >= cuff:
                fig.put(p[0], p[1], F_YOKE, 2 if (p[0] + p[1]) % 2 else 1)
    if far:
        for p in m:
            f = fam_at(fig, p)
            if f in (fam, F_YOKE):
                fig.put(p[0], p[1], f, max(1, tone(fig, p) - 1))
    return m


def f_box(fig, x0, y0, w, h, keep, face=True):
    """The delivery box, slim and upright: concrete, a lit top edge and glint, a lid seam
    with its lit lip, two 2 px stencil dashes and the small pink logo; a pink light strip
    on its outer edge (a light source)."""
    m = fig.rect(x0, y0, x0 + w - 1, y0 + h - 1, 1)
    box(fig, m, F_BOX)
    for x in range(x0 + 1, x0 + w - 1):
        fig.put(x, y0 + 3, F_BOX, 1)
        fig.put(x, y0 + 4, F_BOX, 4 if x < x0 + w // 2 + 1 else 3)
    if face:
        for (dx, dy) in ((2, 8), (3, 8), (5, 8), (2, 10), (3, 10), (4, 10)):
            if dx < w - 2:
                fig.put(x0 + dx, y0 + dy, F_BOX, 2)
        logo(fig, x0 + 2, y0 + 5, keep)
        for y in range(y0 + 6, y0 + h - 2):
            fig.glow(x0 + w - 2, y, 'neon_pink', 3)
            keep.add((x0 + w - 2, y))
    return m


def f_hood_front(fig, keep, dy=0, look=0, glyph_name='crescent'):
    cx, cy = 32, 29 + dy
    shell = fig.ellipse(cx, cy, 9.6, 9.2)
    drape = fig.poly([(23.5, 31 + dy), (40.5, 31 + dy), (40, 37), (24, 37)])
    bumps = set()
    for bx in (25, 37):
        bumps |= fig.rect(bx, cy - 11, bx + 2, cy - 8, 1) | fig.rect(bx, cy - 10, bx + 2, cy - 8)
    pillow(fig, shell | drape, F_HOOD, lo=1)
    pillow(fig, shell, F_HOOD, lo=1)
    for bx in (25, 37):
        for (x, y) in sorted(bumps):
            if bx <= x <= bx + 2:
                t = 4 if x == bx else 3 if x == bx + 1 else 2
                if bx > 32:
                    t -= 1
                fig.put(x, y, F_HOOD, t)
        fig.put(bx + 1, cy - 11, F_HOOD, 5 if bx < 32 else 4)
        keep.add((bx + 1, cy - 11))
    # the hood's top-left glint and a seam over the crown (recess with a lit lip)
    for x in (27, 28):
        fig.put(x, cy - 8, F_HOOD, 5)
    for y in range(cy - 9, cy - 4):
        fig.put(32, y, F_HOOD, 2)
        fig.put(31, y, F_HOOD, 4)
    cloth(fig, {p for p in drape if p[1] >= 34 + dy}, F_HOOD, lit=2, dark=3, folds=(28, 36), top=False)
    # the brow: the hood's lip overhangs the visor (lit top row, its shadow on the bezel)
    for x in range(24, 41):
        fig.put(x, cy - 5 + look, F_HOOD, 4 if x < 33 else 3)
    bez = fig.rect(24, cy - 4 + look, 40, cy + 4 + look, 2)
    box(fig, bez, F_METAL, glint=False)
    for x in range(25, 40):
        fig.put(x, cy - 4 + look, F_METAL, 1)        # the brow's shadow
    scr = fig.rect(25, cy - 3 + look, 39, cy + 3 + look, 2)
    glass(fig, scr)
    g = cy - 2 + look
    if glyph_name == 'zZ':
        put_glyph(fig, 'z', 26, g, keep)
        put_glyph(fig, 'Z', 32, g - 1, keep)
    elif glyph_name == 'list':
        put_glyph(fig, 'crescent', 30, g, keep, t=2)
    else:
        put_glyph(fig, glyph_name, 31 if len(GLYPHS[glyph_name][0]) <= 3 else 30, g, keep)
    crack(fig, [(38, cy - 3 + look), (37, cy - 2 + look), (37, cy - 1 + look), (36, cy + look),
                (36, cy + 1 + look)], keep)
    # the chin step: the hood tucks in a pixel under the bezel, in shade
    for x in range(26, 39):
        fig.put(x, cy + 5 + look, F_HOOD, 1)
    return shell


def f_torso_front(fig, keep, top=36, hem=47):
    body = fig.poly([(24.5, top), (39.5, top), (40.5, hem), (23.5, hem)])
    cloth(fig, body, F_JACKET, lit=2, dark=3, folds=(28, 36))
    # the yoke: concrete over the shoulders, its lower seam a dark row
    for (x, y) in sorted(body):
        if y <= top + 1:
            fig.put(x, y, F_YOKE, 4 if x < 30 else 3 if x < 37 else 2)
        elif y == top + 2:
            fig.put(x, y, F_JACKET, 1)
    fig.put(26, top, F_YOKE, 5)
    fig.put(27, top, F_YOKE, 5)
    for y in range(top + 2, hem):
        fig.put(32, y, F_JACKET, 1)
        fig.put(31, y, F_JACKET, 4 if y < 42 else 3)
    strip2(fig, body, (42, 43), F_JACKET)
    fig.put(32, 42, F_JACKET, 1)
    fig.put(32, 43, F_JACKET, 1)
    for x in range(23, 42):
        if (x, hem - 1) in body:
            fig.put(x, hem - 1, F_YOKE, 2 if (x // 2) % 2 else 1)
    # the sling strap, left shoulder to the box at the back of her right hip
    st = thick(fig, (39.5, top), (25.5, hem + 0.5), 2.6)
    for p in st:
        if p in body:
            fig.put(p[0], p[1], F_BOX, 3 if p[0] + p[1] < 75 else 2)
    fig.put(33, 41, F_METAL, 4)
    fig.put(34, 41, F_METAL, 2)
    keep |= {(33, 41), (34, 41)}
    return body


def final_front(view):
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    # the box: back of her right hip (screen left in S), layer 0
    f_box(fig, 12, 43, 8, 14, keep)
    legs(fig, 0, F_TROUSER, F_METAL, 46, (27, 33), w=4, boot_h=5)
    for x0 in (27, 33):                 # knee pads: a concrete 2-row plate on each knee
        for x in range(x0, x0 + 4):
            fig.put(x, 54, F_YOKE, 4 if x == x0 else 3 if x < x0 + 3 else 2)
            fig.put(x, 55, F_YOKE, 2 if x < x0 + 3 else 1)
    f_torso_front(fig, keep)
    limb(fig, (21.5, 38.5), (20.5, 48.5), F_JACKET, band=(0.5, 0.72), cuff=0.86)
    hand(fig, 19, 48)
    if not fid:
        limb(fig, (42.5, 38.5), (43.5, 48.5), F_JACKET, far=True, band=(0.5, 0.72), cuff=0.86)
        hand(fig, 42, 48)
        f_hood_front(fig, keep)
    else:
        # checks the parcel list on her left wrist, then lays it face-down: forearm across
        # the chest, the wrist screen lit, head bowed to it, the visor dimmed
        limb(fig, (42.5, 38.5), (42, 43), F_JACKET, far=True)
        limb(fig, (42, 43), (31, 42.5), F_JACKET, cuff=0.8)
        ws = fig.rect(31, 40, 35, 43)
        box(fig, ws, F_METAL, glint=False)
        for y in (41, 42):
            for x in (32, 33, 34):
                if y == 41 or x < 34:
                    fig.glow(x, y, 'neon_cyan', 4 if y == 41 else 3)
                    keep.add((x, y))
        hand(fig, 28, 41)
        f_hood_front(fig, keep, dy=1, look=1, glyph_name='list')
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


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


def f_hood_side(fig, keep, d, hx, cy, glyph_name, bump_lift=0):
    """Profile as a form: a round hood with one antenna bump, the hood's brow overhanging
    a visor that steps a pixel proud of the face, a cheek plane in shade behind the bezel
    and a chin step under it."""
    U = lambda u: hx + d * u   # noqa: E731
    hood = fig.ellipse(hx - d * 0.5, cy, 9.2, 9.2) | fig.poly(
        [(U(-7.5), cy + 2), (U(6.5), cy + 2), (U(6), cy + 8), (U(-6), cy + 8)])
    bx0 = U(-4)
    bump = fig.rect(round(min(bx0, U(-2))), cy - 11 - bump_lift, round(min(bx0, U(-2))) + 2, cy - 8, 1) | \
        fig.rect(round(min(bx0, U(-2))), cy - 10 - bump_lift, round(min(bx0, U(-2))) + 2, cy - 8)
    pillow(fig, hood, F_HOOD, lo=1)
    lx = min(p[0] for p in bump)
    for (x, y) in sorted(bump):
        fig.put(x, y, F_HOOD, 4 if x == lx else 3 if x == lx + 1 else 2)
    fig.put(lx + 1, min(p[1] for p in bump), F_HOOD, 5)
    keep.add((lx + 1, min(p[1] for p in bump)))
    cloth(fig, {p for p in hood if p[1] >= cy + 5}, F_HOOD, lit=2, dark=3, top=False)
    # a seam over the crown from the brow to the nape: recess with a lit lip above it
    for k in range(-3, 6):
        x = round(U(-k))
        y = cy - 8 + abs(k) // 2 + (2 if k > 3 else 0)
        if (x, y) in hood and (x, y - 1) in hood:
            fig.put(x, y, F_HOOD, 2)
            fig.put(x, y - 1, F_HOOD, 4 if x < AX + 2 else 3)
    # the cheek: the side plane just behind the bezel, in shade
    for y in range(cy - 3, cy + 4):
        p = (round(U(1)), y)
        if p in hood:
            fig.put(p[0], p[1], F_HOOD, 2)
    # the visor: iron bezel, glass, stepping a pixel past the hood's front
    a, b = sorted((round(U(2)), round(U(10))))
    bez = fig.rect(a, cy - 4, b, cy + 4, 2)
    box(fig, bez, F_METAL, glint=False)
    a2, b2 = sorted((round(U(3)), round(U(10))))
    scr = fig.rect(a2, cy - 3, b2, cy + 3, 2)
    glass(fig, scr)
    # the brow over it: the hood's lip, lit on top, throwing a shadow on the bezel's top row
    for u in range(1, 10):
        x = round(U(u))
        fig.put(x, cy - 5, F_HOOD, 4 if u < 7 else 3)
        if (x, cy - 4) in bez:
            fig.put(x, cy - 4, F_METAL, 1)
    # the chin step under the bezel
    for u in range(1, 8):
        fig.put(round(U(u)), cy + 5, F_HOOD, 1)
    sx0, sx1 = min(p[0] for p in scr), max(p[0] for p in scr)
    gw = len(GLYPHS['Z' if glyph_name == 'zZ' else glyph_name][0])
    gx = sx0 + max(1, (sx1 - sx0 + 1 - gw) // 2)
    if glyph_name == 'zZ':
        put_glyph(fig, 'Z', gx, cy - 2, keep)
    else:
        put_glyph(fig, glyph_name, gx, cy - 2, keep, flip=(glyph_name == 'chevron' and d == -1))
    if d == 1:
        crack(fig, [(sx1 - 1, cy - 3), (sx1 - 1, cy - 2), (sx1 - 2, cy - 1)], keep)
    else:
        crack(fig, [(sx0 + 2, cy - 3), (sx0 + 2, cy - 2), (sx0 + 1, cy - 1)], keep)
    return hood


FPOSES = {
    #          body x/y  head x/y  legs       near hand    far hand     glyph
    'idle':   (0, 0,    0, 0,    'stand',   (1, 48),     None,        'crescent'),
    'ready':  (0, 1,    1, 0,    'wide',    (6, 42),     (4, 43),     'crescent'),
    'strike': (3, 1,    5, 2,    'lunge',   (15, 38),    (-6, 44),    'chevron'),
    'cast':   (0, 0,    -1, -1,  'wide',    (11, 37),    (3, 44),     'ring'),
    'hit':    (-3, 0,   -5, -1,  'stumble', (4, 38),     (-3, 39),    'x'),
    'sit':    (-2, 13,  1, 0,    'sit',     (7, 46),     (5, 46),     'z'),
    'cheer':  (0, -4,   0, -1,   'jump',    (12, 30),    (-5, 18),    'heart'),
}


def final_side(d, pose, familiar=False):
    bx, by, hx, hy, lg, near, far, gname = FPOSES[pose]
    fig = sk.Fig(W, H)
    keep = set()
    cx = AX + d * bx
    U = lambda u: cx + d * u   # noqa: E731
    perch = None
    if familiar:
        # the back shoulder, away from the foe: x smaller in E, larger in W
        perch = (round(U(-5)), 37 + by)
        mossling(fig, round(U(-10)), perch[1] + 1, d, keep)
    hip = 46 + by
    # the box at the back of her right hip: layer 0 in every facing
    bxa, bxb = sorted((round(U(-6)), round(U(-14))))
    bm = f_box(fig, bxa, min(hip - 5, SOLE - 13), bxb - bxa + 1, 14, keep, face=True)
    if d == -1:   # W: her right hip is the far side, so the box sits a tone back in her shadow
        for p in bm:
            if p not in fig.fixed and fam_at(fig, p) == F_BOX:
                fig.put(p[0], p[1], F_BOX, max(1, tone(fig, p) - 1))
    # far arm and far leg first, a tone back
    if far:
        limb(fig, (U(-1), 38.5 + by), (U(far[0]), far[1] + (by if pose not in ('cheer', 'cast') else 0)),
             F_JACKET, far=True, band=(0.5, 0.72), cuff=0.86)
    if lg == 'stand':
        L = [((-2, hip), (-2, SOLE - 4)), ((2, hip), (2, SOLE - 4))]
    elif lg == 'wide':
        L = [((-2, hip), (-5, SOLE - 4)), ((2, hip), (4, SOLE - 4))]
    elif lg == 'lunge':
        L = [((-2, hip), (-8, SOLE - 4)), ((2, hip), (7, SOLE - 4))]
    elif lg == 'stumble':
        L = [((-2, hip), (-7, SOLE - 4)), ((2, hip), (5, SOLE - 6))]
    elif lg == 'sit':
        L = [((0, hip), (9, hip + 2)), ((2, hip + 1), (11, hip + 2))]
    else:
        L = [((-2, hip), (-4, hip + 7)), ((2, hip), (3, hip + 8))]
    feet = []

    def leg(i, a, b):
        m = limb(fig, (U(a[0]), a[1]), (U(b[0]), b[1]), F_TROUSER, far=(i == 0))
        # knee pad halfway down
        kx, ky = (U(a[0]) + U(b[0])) / 2, (a[1] + b[1]) / 2
        for p in fig.rect(round(kx) - 1, round(ky), round(kx) + 1, round(ky) + 1):
            if p in m:
                fig.put(p[0], p[1], F_YOKE, (4 if p[1] == round(ky) else 2) - (1 if i == 0 else 0))
        # the boot: toe the way she faces
        fx, fy = round(U(b[0])), round(b[1])
        if lg == 'sit':
            bt = fig.rect(min(fx, fx + d * 3), fy - 3, max(fx, fx + d * 3), fy + 1, 1)
        else:
            bt = fig.rect(min(fx - d * 2, fx + d * 4), fy, max(fx - d * 2, fx + d * 4), fy + 4, 1)
        box(fig, bt, F_METAL, glint=False)
        for p in bt:
            if p[1] == max(q[1] for q in bt if q[0] == p[0]):
                fig.put(p[0], p[1], F_METAL, 1)
        if i == 0:
            for p in bt:
                fig.put(p[0], p[1], F_METAL, max(1, tone(fig, p) - 1))
        feet.append(bt)

    if lg != 'sit':
        for i, (a, b) in enumerate(L):
            leg(i, a, b)
    # the torso: jacket with a concrete yoke, fold bands, strip, rib waistband
    top = 36 + by
    body = fig.poly([(U(-5.5), top), (U(5.5), top), (U(6), hip + 1), (U(-6), hip + 1)])
    cloth(fig, body, F_JACKET, lit=2, dark=3, folds=(round(U(-2)), round(U(2))))
    for (x, y) in sorted(body):
        if y <= top + 1:
            fig.put(x, y, F_YOKE, 4 if x < AX + d * bx else 3)
        elif y == top + 2:
            fig.put(x, y, F_JACKET, 1)
    fx = round(U(5))
    for y in range(top + 3, hip + 1):
        fig.put(fx, y, F_JACKET, 1 if d == 1 else 2)
    strip2(fig, body, (42 + by, 43 + by), F_JACKET)
    for (x, y) in sorted(body):
        if y == hip:
            fig.put(x, y, F_YOKE, 2 if (x // 2) % 2 else 1)
    # the sling strap: in E it crosses her front from the far shoulder to the near hip at
    # the back; in W it runs down her back from the near shoulder to the far hip
    s0, s1 = ((U(4), top), (U(-5), hip)) if d == 1 else ((U(-1), top), (U(-5.5), hip - 2))
    for p in thick(fig, s0, s1, 2.4):
        if p in body:
            fig.put(p[0], p[1], F_BOX, 3 if d == -1 else 2)
    if lg == 'sit':
        for i, (a, b) in enumerate(L):
            leg(i, a, b)
    f_hood_side(fig, keep, d, round(U(hx)), 29 + by + hy, gname,
                bump_lift=1 if pose in ('hit', 'cheer') else 0)
    hand_xy = (U(near[0]), near[1] + (by if pose not in ('cheer', 'cast') else 0))
    limb(fig, (U(0), 38.5 + by), hand_xy, F_JACKET, band=(0.5, 0.72), cuff=0.86)
    hx0, hy0 = round(hand_xy[0]) - 1, round(hand_xy[1]) - 1
    if pose == 'cast':
        # the wrist screen held up, lit; a cyan ring of light leaves it
        ws = fig.rect(hx0 - 1, hy0 + 3, hx0 + 2, hy0 + 5)
        box(fig, ws, F_METAL, glint=False)
        for x in (hx0, hx0 + 1):
            fig.glow(x, hy0 + 4, 'neon_cyan', 4)
            keep.add((x, hy0 + 4))
        put_glyph(fig, 'ring', round(U(12)) - (0 if d == 1 else 3), hy0 - 6, keep, t=4)
    hand(fig, hx0, hy0)
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig, perch


def final_nap():
    """Curled on her side facing S, head on the box at the left, knees drawn up at the
    right, the familiar curled in the crook by her visor; the visor shows "z Z"."""
    fig = sk.Fig(W, H)
    keep = set()
    f_box(fig, 13, 56, 10, 10, keep, face=False)        # the box on its side, her pillow
    mossling(fig, 9, SOLE + 1, 1, keep, curled=True)
    # body: the jacket curled, her back a long round to the upper right
    body = fig.ellipse(36, 58.5, 10.5, 6.5)
    cloth(fig, body, F_JACKET, lit=2, dark=3, folds=(31, 37))
    for (x, y) in sorted(body):
        if y <= 53:
            fig.put(x, y, F_YOKE, 4 if x < 36 else 3)
    strip2(fig, body, (58, 59), F_JACKET)
    # knees drawn up at the front, boots tucked under at the right
    knees = fig.ellipse(42, 62, 6.5, 3.6)
    cloth(fig, knees, F_TROUSER, lit=2, dark=2)
    for x in range(40, 43):
        fig.put(x, 60, F_YOKE, 4 if x == 40 else 3)
        fig.put(x, 61, F_YOKE, 2)
    bt = fig.rect(46, 61, 51, 65, 1)
    box(fig, bt, F_METAL, glint=False)
    for x in range(46, 52):
        fig.put(x, 65, F_METAL, 1)
    # her near arm folded under the visor, hand at her chin
    limb(fig, (30, 58), (26, 63), F_JACKET, cuff=0.7)
    hand(fig, 24, 62)
    # the hood lying on the box, bumps flopped to the left, visor turned to us
    cx, cy = 23, 52
    hood = fig.ellipse(cx, cy, 8.4, 7.6)
    for bx in (16, 27):
        hood |= fig.rect(bx, cy - 9, bx + 2, cy - 6, 1) | fig.rect(bx, cy - 8, bx + 2, cy - 6)
    pillow(fig, hood, F_HOOD, lo=1)
    for x in (19, 20):
        fig.put(x, cy - 6, F_HOOD, 5)
    for bx in (16, 27):
        for y in range(cy - 9, cy - 5):
            for x in range(bx, bx + 3):
                if (x, y) in hood:
                    fig.put(x, y, F_HOOD, (4 if x == bx else 3 if x == bx + 1 else 2) - (1 if bx > 20 else 0))
    for x in range(16, 31):
        fig.put(x, cy - 4, F_HOOD, 4 if x < 24 else 3)
    bez = fig.rect(16, cy - 3, 30, cy + 4, 2)
    box(fig, bez, F_METAL, glint=False)
    for x in range(17, 30):
        fig.put(x, cy - 3, F_METAL, 1)
    scr = fig.rect(17, cy - 2, 29, cy + 4, 2)
    glass(fig, scr)
    put_glyph(fig, 'z', 18, cy, keep, t=2)
    put_glyph(fig, 'Z', 23, cy - 1, keep, t=3)
    crack(fig, [(28, cy - 2), (28, cy - 1), (27, cy)], keep)
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
    label='B final', name='Antenna hood (final): snug bumped hood, glyph visor, slim box at the back of the hip',
    chosen='B',
    grafts=[
        'From A: a visor glyph per state: crescent (idle, ready), chevron (strike), ring (cast), X (hit), '
        'z (sit), heart (cheer), "z Z" (nap); the fidget dims it while she reads her wrist.',
        'From A: the delivery box bigger (8-9 x 14) and readable: lit top edge and glint, lid seam, stencil, '
        'pink logo and a pink light strip; slim at the back of the right hip, one anchor and layer 0 in every facing.',
        'From C (craft): the crack across the visor in every view, and fold bands on the jacket.',
        'Fix: reflective strips with a lit top edge (snow 5-4) and a shaded lower edge (snow 3-2), the east end a step down.',
        'Fix: the asphalt jacket in its full ramp (1 to 5) with a concrete yoke, rib waistband, rib cuffs and knee pads.',
    ],
    palette=['asphalt', 'concrete', 'slate', 'snow', 'iron'],
    pose='Leggy and alert, bumps up, weight ready to go: one more drop before dawn.',
    parts=[
        'familiar perch: back shoulder (E: x smaller, W: x larger), behind the hood; layer -1; chest',
        'delivery box (concrete, lid seam, stencil, pink logo and light strip): layer 0; back of the right hip; '
        'all facings the same anchor (S: screen left, E/W: behind the hip); swings a frame late on walk',
        'far leg / far sleeve (slate / asphalt, a tone back, concrete knee pad and cuff): layer 1; hip / chest',
        'near leg (slate, concrete knee pad, iron boot): layer 2; hip; long 6-frame stride, forward in sit, tucked in cheer',
        'jacket (asphalt bands and folds, concrete yoke and rib, snow strip, sling strap): layer 3; hip; breath 1 px',
        'hood with antenna bumps (asphalt, crown seam, brow over the visor, chin step): layer 4; chest; '
        'bumps lift 1 px on hit and cheer',
        'visor (iron bezel, asphalt glass, crack, cyan glyph per state): layer 5; head; glyph swaps on state change',
        'near sleeve + wrist screen (asphalt, snow band, concrete cuff, iron hand): layer 6; chest; '
        'swing, strike (full reach), cast (wrist up, a cyan ring), fidget check',
    ],
    notes=[
        'Compared side by side with Eastward 05 at the same height: John (jacket in 3 fold bands, one big pack block '
        'with a lit top edge), the woman in teal and the woman in the purple cardigan (sleeves and hem rows).',
        'Works: cat-eared hood and lit visor read at 2 px day or night; long legs give a clear stride; the box '
        'never blocks the perch.',
        'Night: asphalt is dark; the yoke, strips, knee pads, visor and box carry the read. Keep Pendle\'s coat '
        'lighter than hers (cast clash).',
        'Open: the bumps edge towards animal ears; they stay square-topped (antennae), never pointed.',
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
    sk.design_sheet('Nix final (folk 12, Neon Harbour): B, the antenna hood, with grafts', [entry], OUT_FINAL,
                    note='50 art px, cell 64 x 72, foot (32, 66). World S/E/W, fidget, nap; fight E and W with the '
                         'stand-in Mossling on the back shoulder. Visor glyph per state.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], glows=['neon_cyan', 'neon_pink'], pose=FINAL['pose'],
                glyphs={'idle': 'crescent', 'ready': 'crescent', 'strike': 'chevron', 'cast': 'ring', 'hit': 'x',
                        'sit': 'z', 'cheer': 'heart', 'nap': 'z Z', 'fidget': 'dim crescent'},
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
                        palette=o['palette'], glows=['neon_cyan', 'neon_pink'], pose=o['pose'], notes=o['notes'],
                        measure=nums))
    sk.design_sheet('Nix (folk 12, Neon Harbour): hood, screen and pack silhouette', OPTIONS, OUT_PNG,
                    note='50 art px, cell 64 x 72, foot (32, 66). Views: S, E, W idle and the S fidget key pose. '
                         'Glows (neon cyan glyph, neon pink logo) are light sources only.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='nix', height_art_px=50, cell=[W, H], foot=[AX, AY],
                       question='Hood, screen and pack silhouette.',
                       options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
