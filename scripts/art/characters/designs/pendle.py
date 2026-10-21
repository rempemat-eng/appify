"""Pendle, the brass station automaton of Cogsworth: three design options (Claude J lane).

Main question: the automaton's build.

    A  Longcase: a grandfather-clock body in verdigris copper on short legs. The dial sits in
       a square hood as the head, the trunk carries a long glass door with the pendulum.
    B  Station master: a slender figure in soot-black riveted plates cut like a frock coat,
       long thin limbs, a big round clock head; a small brass-rimmed porthole in the waist.
    C  Engine barrel: a barrel-chested brass boiler body with copper hoops and a big round
       porthole belly, a small round head-dial, stout soot limbs.

All three share the clock recipe: a pale plaster dial, ink ticks at 12, 3, 6 and 9, two ink
hands set at a minute to two (the minute hand on the 12 a minute short), and the two winding
holes of a real dial doubling as eyes. The conductor's cap is soot with a band and badge.

Views: S idle, E idle, W idle (W is drawn with its own light, never mirrored pixels) and
the S key pose of its fidget. Design sheets are review material; production frames come
from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/pendle.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/pendle-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/pendle.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'pendle')

W, H = 64, 72
AX, AY = 32, 66          # foot anchor: soles fill row 65, their outline lands on row 66
SOLE = AY - 1
TOP = AY - 52            # 52 art px tall: the cap's crown starts on row 14
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def _extents(mask):
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    return ({y: (min(v), max(v)) for y, v in rows.items()}, {x: (min(v), max(v)) for x, v in cols.items()})


def plate(fig, mask, fam, sheen=0.5, glint=True, edges=True):
    """A machined metal plate (house-style 5, metal): square corners, a lit top row and
    left column, the body, a shaded right column and a dark bottom row, and a slow sheen
    lighter at the upper left. The glint is two pixels on the top row's left end."""
    mask = set(mask)
    if not mask:
        return mask
    rows, cols = _extents(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    tall = max(ys) - min(ys) + 1 >= 4
    wide = max(xs) - min(xs) + 1 >= 4
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 3
        if 0.55 * u + 0.85 * v < -sheen:
            t = 4
        if edges:
            if wide and x == rows[y][1]:
                t = 2
            if tall and x == rows[y][0]:
                t = 4
            if y == cols[x][0]:
                t = 4
            if tall and y == cols[x][1]:
                t = 1
        fig.put(x, y, fam, t)
    if glint:
        y0 = min(ys)
        row = sorted(x for (x, y) in mask if y == y0)
        for x in row[:2]:
            fig.put(x, y0, fam, 5)
    return mask


def cyl(fig, mask, fam, horizontal=False):
    """A pipe or limb: a highlight band in the left third, dark at the right (top/bottom
    for a horizontal pipe)."""
    mask = set(mask)
    rows, cols = _extents(mask)
    for (x, y) in mask:
        if horizontal:
            a, b = cols[x]
            i, n = y - a, b - a + 1
        else:
            a, b = rows[y]
            i, n = x - a, b - a + 1
        if n == 1:
            t = 3
        elif n == 2:
            t = (4, 2)[i]
        elif n == 3:
            t = (4, 3, 2)[i]
        else:
            t = 3
            if i == n // 3 or (n >= 6 and i == n // 3 - 1):
                t = 4
            if i == 0:
                t = 3
            if i >= n - max(1, n // 4):
                t = 2
            if i == n - 1:
                t = 1
        fig.put(x, y, fam, t)
    return mask


def ball(fig, mask, fam, glint=True):
    """A round part: the lit cap a disc offset to the upper left and the dark crescent the
    outside of a larger offset disc, so the terminator follows the form."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 3
        if (u + 0.42) ** 2 + (v + 0.5) ** 2 < 0.36:
            t = 4
        if (u + 0.3) ** 2 + (v + 0.34) ** 2 > 1.05:
            t = 2
        if (x, y + 1) not in mask and u > -0.3:
            t = min(t, 1 if u > 0.15 else 2)
        fig.put(x, y, fam, t)
    if glint and len(mask) >= 9:
        lit = sorted((p for p in mask if tone(fig, p) == 4), key=lambda p: (p[0] - cx) / rx + (p[1] - cy) / ry)
        for p in lit[:2]:
            fig.put(p[0], p[1], fam, 5)
    return mask


def ring_shade(fig, mask, fam, cx, cy, r):
    """A bezel ring: lit round the upper left, shaded round the lower right, by angle."""
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
        n = 0.55 * u + 0.85 * v
        t = 3
        if n < -0.3:
            t = 4
        if n > 0.35:
            t = 2
        if n > 0.8:
            t = 1
        fig.put(x, y, fam, t)
    lit = sorted(mask, key=lambda p: 0.55 * (p[0] + 0.5 - cx) + 0.85 * (p[1] + 0.5 - cy))
    for p in lit[:2]:
        fig.put(p[0], p[1], fam, 5)


def seam_h(fig, x0, x1, y, fam):
    """A horizontal seam: a dark line with a lit line under it (only on that plate)."""
    for x in range(min(x0, x1), max(x0, x1) + 1):
        if fam_at(fig, (x, y)) == fam:
            fig.put(x, y, fam, 1)
        if fam_at(fig, (x, y + 1)) == fam and tone(fig, (x, y + 1)) not in (1,):
            fig.put(x, y + 1, fam, 4)


def seam_v(fig, x, y0, y1, fam):
    """A vertical seam: dark, with the lit west lip of the next plate east of it."""
    for y in range(min(y0, y1), max(y0, y1) + 1):
        if fam_at(fig, (x, y)) == fam:
            fig.put(x, y, fam, 1)


def rivet(fig, x, y, fam, keep, t=5):
    """A rivet: a lit head over its own shadow."""
    fig.put(x, y, fam, t)
    fig.put(x, y + 1, fam, 1)
    keep |= {(x, y), (x, y + 1)}


def glass(fig, mask, keep, swing=0, bob_r=1.6, rod_fam='brass', day=True):
    """The belly window (house-style 5, glass by day): slate 1 at the top, 2 below, one
    diagonal glint in two-pixel steps at the upper left; the brass pendulum hangs inside,
    its rod one pixel, its bob a lit round, `swing` pixels off the plumb line."""
    mask = set(mask)
    rows, cols = _extents(mask)
    ys = [p[1] for p in mask]
    xs = [p[0] for p in mask]
    y0, y1 = min(ys), max(ys)
    x0, x1 = min(xs), max(xs)
    for (x, y) in mask:
        t = 1 if y - y0 < max(2, (y1 - y0 + 1) // 3) else 2
        if x == rows[y][0] and t == 2:
            t = 1                      # the frame's shadow down the west side
        fig.put(x, y, 'slate', t)
    # glint: two-pixel vertical steps rising to the right, upper left of the pane
    gx, gy = x0 + 1, y0 + max(3, (y1 - y0) // 3 + 1)
    for k in range(3):
        for j in range(2):
            p = (gx + k, gy - 2 * k - j)
            if p in mask and p[1] > y0:
                fig.put(p[0], p[1], 'slate', 4)
    # pendulum: pivot at the top centre
    px = (x0 + x1) // 2
    length = y1 - y0 - 3
    bob_c = None
    for i in range(length):
        y = y0 + i
        x = px + round(swing * i / max(1, length))
        if (x, y) in mask:
            fig.put(x, y, rod_fam, 3 if i < 2 else 4)
        bob_c = (x, y)
    bx, by = bob_c
    bob = {p for p in fig.ellipse(bx + 0.5, by + 1.0, bob_r, bob_r) if p in mask}
    ball(fig, bob, rod_fam, glint=len(bob) >= 9)
    if len(bob) < 9:
        fig.put(min(bob)[0], min(p[1] for p in bob), rod_fam, 5)
    return mask


def frame_recess(fig, mask, fam):
    """The one-pixel frame round a pane: shadow on its top and west (the recess), lit on
    its lower and east lip (the edge faces the light)."""
    ring = set()
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            q = (x + dx, y + dy)
            if q not in mask:
                ring.add(q)
    for (x, y) in ring:
        if fam_at(fig, (x, y)) is None:
            continue
        top = (x, y + 1) in mask or (x + 1, y) in mask or (x + 1, y + 1) in mask
        fig.put(x, y, fam, 1 if top and not ((x, y - 1) in mask or (x - 1, y) in mask) else 4)
    return ring


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour, unless it is an eye, a glint, a hand, a tick or a rivet (`keep`). The
    tie-break is deterministic: max(sorted(set(pool), key=str), key=pool.count)."""
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


# --- the clock head ----------------------------------------------------------------------
def dial_front(fig, cx, cy, rf, bezel, keep, eyes='open', minute='up', look=0):
    """The station dial seen front on. cx is the pixel column of the hub. A bezel two
    pixels wide, a pale plaster face lit by its glass, ink ticks, two ink hands at a
    minute to two, and the winding holes as eyes (ink, a plaster glint)."""
    fc = cx + 0.5
    outer = fig.ellipse(fc, cy + 0.5, rf + 2, rf + 2)
    face = fig.ellipse(fc, cy + 0.5, rf, rf)
    ring_shade(fig, outer - face, bezel, fc, cy + 0.5, rf + 2)
    # face: tone 4, the bezel's shadow a crescent on its upper left, a tone 3 lower rim
    for (x, y) in face:
        t = 4
        u, v = (x + 0.5 - fc) / rf, (y + 0.5 - cy - 0.5) / rf
        if (u + 0.18) ** 2 + (v + 0.22) ** 2 > 0.95 and u + v < 0:
            t = 3
        if (u - 0.1) ** 2 + (v - 0.1) ** 2 > 0.92 and u + v > 0.4:
            t = 3
        fig.put(x, y, 'plaster', t)
    # the cover glass glint: two pixels at the upper left of the face
    for p in ((cx - rf + 3, cy - rf + 3), (cx - rf + 4, cy - rf + 3)):
        if p in face:
            fig.put(p[0], p[1], 'plaster', 5)
            keep.add(p)
    ink = []
    # ticks: 12 and 6 vertical pairs, 3 and 9 horizontal pairs
    ink += [(cx, cy - rf + 1), (cx, cy - rf + 2), (cx, cy + rf - 2), (cx, cy + rf - 1)]
    ink += [(cx - rf + 1, cy), (cx - rf + 2, cy), (cx + rf - 2, cy), (cx + rf - 1, cy)]
    # hands: the minute hand up to the 12 (a minute short), the hour hand towards two
    if minute == 'up':
        ink += [(cx, cy - k) for k in range(0, rf - 3)]
    elif minute == 'back':     # nudged back: leaning to the 11
        ink += [(cx, cy), (cx, cy - 1), (cx - 1, cy - 1), (cx - 1, cy - 2), (cx - 2, cy - 2), (cx - 2, cy - 3)]
    ink += [(cx + 1, cy), (cx + 1, cy - 1), (cx + 2, cy - 1), (cx + 2, cy - 2)]
    # eyes: the winding holes, below the hub either side, 2 px wide and up to 3 tall
    exs = (cx - 4, cx + 3) if rf >= 8 else (cx - 3, cx + 2)
    ey = cy + (1 if rf >= 8 else 2) + look
    eh = 3 if rf >= 7 else 2
    if eyes == 'open':
        for ex in exs:
            ink += [(ex + i, ey + j) for i in range(2) for j in range(eh)]
    elif eyes == 'shut':
        for ex in exs:
            ink += [(ex, ey + 1), (ex + 1, ey + 1)]
    for p in ink:
        if p in face:
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
    if eyes == 'open':
        for ex in exs:
            fig.put(ex, ey, 'plaster', 5)
            keep.add((ex, ey))
    return outer


def dial_side(fig, d, hx, cy, rf, bezel, keep, case_fam=None):
    """The dial in three-quarter view (d=1 faces E, d=-1 faces W). The drum of the clock
    case shows behind; the face is a foreshortened oval forward of it. Lighting is computed
    from the masks (upper left), so W is drawn, never mirrored."""
    case_fam = case_fam or bezel
    drum = fig.ellipse(hx - d * 2 + 0.5, cy + 0.5, rf * 0.8 + 1, rf + 2)
    ball(fig, drum, case_fam + '_cool', glint=False)
    fcx = hx + d * 1.5 + 0.5
    rx = rf * 0.72
    outer = fig.ellipse(fcx, cy + 0.5, rx + 1.6, rf + 2)
    face = fig.ellipse(fcx + d * 0.4, cy + 0.5, rx, rf)
    ring_shade(fig, outer - face, bezel, fcx, cy + 0.5, rf + 2)
    xs = sorted({x for x, y in face})
    for (x, y) in face:
        u, v = (x + 0.5 - fcx) / rx, (y + 0.5 - cy - 0.5) / rf
        t = 4 if d == -1 else 3
        if d == 1 and u < -0.4 and v < 0.3:
            t = 4                      # the west rim of the face catches the light
        if u * u + v * v > 0.8 and u + v > 0.5:
            t = 3 if d == -1 else 2
        fig.put(x, y, 'plaster', t)
    mid = xs[len(xs) // 2]
    ink = [(mid, cy - rf + 1), (mid, cy - rf + 2), (mid, cy + rf - 2), (mid, cy + rf - 1)]
    ink += [(mid, cy - k) for k in range(0, rf - 3)]
    ink += [(mid + 1, cy - 1), (mid + 2, cy - 1)]
    ey = cy + (1 if rf >= 8 else 2)
    eh = 3 if rf >= 7 else 2
    near = mid + d * 2
    far = mid - d * 3 if d == 1 else mid - d * 2
    eye = [(near + d * i, ey + j) for i in range(2) for j in range(eh)] + [(far, ey + j) for j in range(eh)]
    for p in ink + eye:
        if p in face:
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
    g = (min(near, near + d), ey)
    fig.put(g[0], g[1], 'plaster', 5)
    keep.add(g)
    # a winding square on the drum's side: the key the tinkerer turns
    kx = hx - d * 4
    for p in ((kx, cy), (kx, cy + 1)):
        fig.put(p[0], p[1], bezel, 4 if d == -1 else 2)
    return outer | drum


def cap_front(fig, cx, top, keep, band='brass', w=7, crown_h=4, tilt=0):
    """The conductor's cap from the front: a flat soot crown, a band with a brass badge, and
    the peak seen from above, lit on its top plane and dark beneath."""
    crown = fig.rect(cx - w + tilt, top, cx + w + tilt, top + crown_h - 1)
    plate(fig, crown, 'soot', sheen=0.3)
    # crown top a touch wider, the folds of the crown as two shaded columns
    for x in (cx - 3 + tilt, cx + 4 + tilt):
        for y in range(top + 1, top + crown_h):
            if fam_at(fig, (x, y)) == 'soot' and tone(fig, (x, y)) == 3:
                fig.put(x, y, 'soot', 2)
    bandm = fig.rect(cx - w + 1 + tilt, top + crown_h, cx + w - 1 + tilt, top + crown_h + 1)
    plate(fig, bandm, band, sheen=0.2, glint=False)
    for (x, y) in bandm:
        if y == top + crown_h + 1:
            fig.put(x, y, band, 2)
    # badge: a lit brass oval on the crown front
    for p, t in (((cx - 1 + tilt, top + 1), 5), ((cx + tilt, top + 1), 4), ((cx + 1 + tilt, top + 1), 3),
                 ((cx - 1 + tilt, top + 2), 4), ((cx + tilt, top + 2), 3), ((cx + 1 + tilt, top + 2), 2)):
        fig.put(p[0], p[1], 'brass', t)
    peak = fig.rect(cx - w + tilt, top + crown_h + 2, cx + w + tilt, top + crown_h + 3, knock=1)
    for (x, y) in peak:
        t = 4 if y == top + crown_h + 2 else 1
        if y == top + crown_h + 2 and x > cx + w // 2 + tilt:
            t = 3
        fig.put(x, y, 'soot', t)
    return crown | bandm | peak


def cap_side(fig, d, cx, top, keep, band='brass', w=6, crown_h=4):
    """The cap in profile: the crown, the band, and the peak jutting forward with its lit
    top plane and its dark underside (the brow step of the face)."""
    crown = fig.rect(cx - w, top, cx + w, top + crown_h - 1)
    plate(fig, crown, 'soot', sheen=0.3)
    bandm = fig.rect(cx - w, top + crown_h, cx + w, top + crown_h + 1)
    plate(fig, bandm, band, sheen=0.2, glint=False)
    for (x, y) in bandm:
        if y == top + crown_h + 1:
            fig.put(x, y, band, 2)
    bx = cx + d * (w - 2)
    for p, t in (((bx, top + 1), 4), ((bx + 1, top + 1), 3), ((bx, top + 2), 3), ((bx + 1, top + 2), 2)):
        fig.put(p[0], p[1], 'brass', t)
    # peak: from the band's front, 4 px forward, two rows
    x0, x1 = (cx + w - 2, cx + w + 4) if d == 1 else (cx - w - 4, cx - w + 2)
    for x in range(x0, x1 + 1):
        fig.put(x, top + crown_h + 2, 'soot', 4 if d == -1 or x < cx + w else 3)
        if (d == 1 and x < x1) or (d == -1 and x > x0):
            fig.put(x, top + crown_h + 3, 'soot', 1)
    return crown


def limb(fig, a, b, fam, w=2, far=False):
    """A jointed limb as a pipe from a to b (w px wide), the far one a tone back."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    m = set()
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        for k in range(w):
            m.add((x + k, y))
    cyl(fig, m, fam)
    if far:
        for p in m:
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    return m


def mitt(fig, x0, y0, fam, w=3, h=3, far=False):
    m = fig.rect(x0, y0, x0 + w - 1, y0 + h - 1, knock=1 if w >= 4 else 0)
    plate(fig, m, fam, sheen=0.4, glint=False)
    if far:
        for p in m:
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    return m


def boot(fig, x0, y0, fam, w=5, h=2, far=False, toe=0):
    m = fig.rect(x0, y0, x0 + w - 1, y0 + h - 1)
    plate(fig, m, fam, sheen=0.4, glint=not far)
    for x in range(x0, x0 + w):
        fig.put(x, y0 + h - 1, fam, 1)
    if far:
        for p in m:
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    return m


def pocket_watch(fig, x, y, keep, chain_to=None):
    """A pocket watch held up: a brass case, a plaster face with one ink hand pair."""
    if chain_to:
        fig.line([chain_to, (x + 2, y + 4)], 'brass', 2)
    case = fig.ellipse(x + 2.5, y + 2.5, 2.6, 2.6)
    ball(fig, case, 'brass', glint=False)
    fig.put(x + 2, y - 1, 'brass', 4)          # the crown
    fig.put(x + 2, y, 'brass', 3)
    for p in ((x + 2, y + 2), (x + 2, y + 1), (x + 3, y + 2)):
        fig.put(p[0], p[1], 'plaster', 4)
    fig.put(x + 1, y + 2, 'plaster', 5)
    fig.put(x + 2, y + 3, 'ink', 0)
    keep |= {(x + 2, y + 2), (x + 2, y + 1), (x + 3, y + 2), (x + 1, y + 2), (x + 2, y + 3), (x + 2, y - 1)}
    return case


def mitt_c(fig, x0, y0, far=False):
    """Option C's fist: a soot mitt under a copper cuff, so it reads on the brass barrel."""
    m = mitt(fig, x0, y0, 'soot', w=5, h=4, far=far)
    for x in range(x0, x0 + 5):
        fig.put(x, y0, 'copper', 4 if x < x0 + 2 else 3 if x < x0 + 4 else 2)
        if far:
            fig.put(x, y0, 'copper', 2)
    return m


def finish(fig, keep):
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


def M(d):
    """Mirror geometry about the anchor column (shading is recomputed from the masks)."""
    return lambda x: AX + d * (x - AX)


def R(fig, d, x0, y0, x1, y1, knock=0):
    u = M(d)
    a, b = sorted((u(x0), u(x1)))
    return fig.rect(a, y0, b, y1, knock)


# --- option A: the longcase ------------------------------------------------------------
def option_a(view):
    fig = sk.Fig(W, H)
    keep = set()
    body, trim = 'copper', 'brass'
    if view in ('S', 'Sf'):
        # legs and boots
        for x0 in (26, 36):
            limb(fig, (x0, 61), (x0, 63), 'soot', w=3)
            fig.put(x0 + 1, 61, 'brass', 2)     # the knee joint: a dark brass collar
            fig.put(x0, 61, 'brass', 3)
            fig.put(x0 + 2, 61, 'brass', 1)
        boot(fig, 24, 64, 'brass', w=6)
        boot(fig, 35, 64, 'brass', w=6)
        # arms behind the trunk edge
        lh = (21, 50)
        rh = (41, 50)
        limb(fig, (22, 42), (lh[0] + 1, lh[1]), 'soot', w=2)
        if view != 'Sf':
            limb(fig, (41, 42), (rh[0], rh[1]), 'soot', w=2)
        # plinth and trunk
        plinth = fig.rect(23, 56, 41, 60)
        plate(fig, plinth, body + '_cool', sheen=0.6)
        seam_v(fig, 32, 57, 59, body + '_cool')
        trunk = fig.rect(25, 41, 39, 55)
        plate(fig, trunk, body, sheen=0.55)
        ledge = fig.rect(24, 55, 40, 55)
        plate(fig, ledge, trim, glint=False)
        for x in range(24, 41):
            fig.put(x, 55, trim, 4 if x < 33 else 3)
        # the glass door and its pendulum
        pane = fig.rect(28, 43, 36, 53, knock=1)
        glass(fig, pane, keep, swing=(0 if view == 'Sf' else 1), bob_r=2.1)
        frame_recess(fig, pane, trim)
        for (x, y) in ((26, 43), (38, 43), (26, 52), (38, 52)):
            rivet(fig, x, y, body, keep)
        for (x, y) in ((25, 57), (39, 57)):
            rivet(fig, x, y, body + '_cool', keep)
        # hood (the head): a square case round the dial, a moulding under it
        hood = fig.rect(21, 21, 43, 39)
        plate(fig, hood, body, sheen=0.5)
        mould = fig.rect(20, 39, 44, 40)
        plate(fig, mould, trim, glint=False)
        for x in range(20, 45):
            fig.put(x, 39, trim, 4 if x < 36 else 3)
            fig.put(x, 40, trim, 1)
        for (x, y) in ((22, 22), (42, 22), (22, 37), (42, 37)):
            rivet(fig, x, y, body, keep, t=4)
        dial_front(fig, 32, 30, 7, trim, keep)
        # shoulders: brass pivots at the top of each arm
        for sx in (22, 41):
            j = fig.rect(sx, 41, sx + 1, 42)
            for (x, y) in j:
                fig.put(x, y, trim, 4 if (x, y) == (sx, 41) else 2)
        mitt(fig, lh[0] - 0, lh[1] + 1, trim)
        if view == 'Sf':
            # the pendulum has stopped: the near arm comes across the trunk and a brass
            # finger taps the glass beside the still bob
            limb(fig, (41, 42), (42, 46), 'soot', w=2)
            fore = fig.rect(37, 46, 42, 47)
            cyl(fig, fore, 'soot', horizontal=True)
            mitt(fig, 35, 45, trim, w=3, h=3)
            fig.put(34, 46, trim, 4)            # the tapping finger on the glass
            fig.put(33, 46, trim, 4)
            keep |= {(33, 46), (34, 46)}
        else:
            mitt(fig, rh[0], rh[1] + 1, trim)
        cap_front(fig, 32, TOP, keep, band=trim)
    else:
        d = 1 if view == 'E' else -1
        u = M(d)
        # far leg, far arm
        limb(fig, (min(u(31), u(33)), 61), (min(u(31), u(33)), 63), 'soot', w=3, far=True)
        boot(fig, min(u(29), u(35)) + (1 if d == 1 else -1) , 64, 'brass', w=6, far=True)
        limb(fig, (u(28) if d == 1 else u(28) - 1, 42), (u(26) if d == 1 else u(26) - 1, 50), 'soot', w=2, far=True)
        mitt(fig, (u(26) if d == 1 else u(26) - 2), 51, trim, far=True)
        # plinth, trunk (narrower in profile: the case is deeper than it looks)
        plate(fig, R(fig, d, 26, 56, 39, 60), body + '_cool', sheen=0.6)
        trunk = R(fig, d, 27, 41, 37, 55)
        plate(fig, trunk, body, sheen=0.55)
        for x in range(min(u(26), u(39)), max(u(26), u(39)) + 1):
            fig.put(x, 55, trim, 4 if x < 33 else 3)
        # the door's front edge: a slot of glass and the bob seen through it
        slot = R(fig, d, 35, 43, 37, 53)
        glass(fig, slot, keep, swing=0, bob_r=1.2)
        frame_recess(fig, slot, trim)
        seam_v(fig, min(u(31), u(31)), 42, 54, body)
        for y in (44, 51):
            rivet(fig, u(29), y, body, keep)
        rivet(fig, u(28), 57, body + '_cool', keep)
        # hood in profile with the dial drum set into its front
        hood = R(fig, d, 24, 21, 40, 39)
        plate(fig, hood, body, sheen=0.5)
        mould = R(fig, d, 23, 39, 41, 40)
        plate(fig, mould, trim, glint=False)
        for x in range(min(u(23), u(41)), max(u(23), u(41)) + 1):
            fig.put(x, 39, trim, 4 if x < 36 else 3)
            fig.put(x, 40, trim, 1)
        rivet(fig, u(26), 23, body, keep, t=4)
        rivet(fig, u(26), 36, body, keep, t=4)
        dial_side(fig, d, u(33), 30, 7, trim, keep, case_fam=body)
        # near leg, near arm
        nx = min(u(33), u(35))
        limb(fig, (nx, 61), (nx, 63), 'soot', w=3)
        boot(fig, nx - 1 + (1 if d == 1 else -1), 64, 'brass', w=6)
        sh = u(32)
        j = fig.rect(sh, 41, sh + 1, 42)
        plate(fig, j, trim, glint=False)
        limb(fig, (sh, 43), (sh + d * 2, 50), 'soot', w=2)
        mitt(fig, sh + d * 2 - (0 if d == 1 else 1), 51, trim)
        cap_side(fig, d, u(32), TOP, keep, band=trim, w=7)
    return finish(fig, keep)


# --- option B: the station master ------------------------------------------------------
def option_b(view):
    fig = sk.Fig(W, H)
    keep = set()
    body, trim = 'soot', 'brass'
    cyh = 31
    if view in ('S', 'Sf'):
        # legs: long thin pipes, brass knees, brass-capped boots
        for x0 in (29, 35):
            limb(fig, (x0, 57), (x0, 62), 'iron', w=2)
            fig.put(x0, 60, trim, 3)
            fig.put(x0 + 1, 60, trim, 2)
        boot(fig, 27, 63, 'soot', w=5, h=3)
        boot(fig, 34, 63, 'soot', w=5, h=3)
        for x in (27, 28, 34, 35):
            fig.put(x, 63, trim, 4 if x in (27, 34) else 3)
        # arms
        limb(fig, (23, 44), (22, 54), 'iron', w=2)
        if view == 'Sf':
            # right arm raised: the pocket watch held up beside the dial, then the other
            # hand nudges the minute hand back
            limb(fig, (41, 44), (44, 40), 'iron', w=2)
            limb(fig, (44, 40), (44, 35), 'iron', w=2)
        else:
            limb(fig, (41, 44), (42, 54), 'iron', w=2)
        # torso: a frock coat of plates, the waist pinched, the skirt flared
        coat = fig.poly([(24, 42), (41, 42), (39, 50), (38, 50), (41, 58), (24, 58), (27, 50), (26, 50)])
        coat |= fig.rect(25, 42, 39, 44)
        plate(fig, coat, body, sheen=0.55)
        # lapels: two brass-edged plates in a V
        for k in range(5):
            fig.put(30 - k // 2 + 0, 43 + k, body, 4)
            fig.put(35 + k // 2, 43 + k, body, 2)
        seam_h(fig, 24, 41, 50, body)
        belt = fig.rect(27, 50, 38, 50)
        for (x, y) in belt:
            fig.put(x, y, trim, 4 if x < 33 else 3)
        fig.put(32, 50, trim, 5)
        fig.put(33, 50, trim, 5)
        seam_v(fig, 32, 52, 57, body)
        for y in (53, 56):
            rivet(fig, 30, y, trim, keep, t=4)
            rivet(fig, 35, y, trim, keep, t=4)
        # the porthole: a small brass-rimmed window in the chest
        rim = fig.ellipse(32.5, 46.5, 3.6, 3.6)
        pane = fig.ellipse(32.5, 46.5, 2.4, 2.4)
        ring_shade(fig, rim - pane, trim, 32.5, 46.5, 3.6)
        glass(fig, pane, keep, swing=(2 if view == 'Sf' else 0), bob_r=1.0)
        # shoulders: brass epaulettes
        for (x0, x1) in ((22, 26), (38, 42)):
            ep = fig.rect(x0, 42, x1, 43, knock=1)
            plate(fig, ep, trim, glint=True)
            for x in range(x0, x1 + 1):
                if (x, 43) in ep:
                    fig.put(x, 43, trim, 2)
        mitt(fig, 21, 55, trim)
        neck = fig.rect(31, 40, 33, 41)
        cyl(fig, neck, 'iron')
        dial_front(fig, 32, cyh, 8, trim, keep, minute=('back' if view == 'Sf' else 'up'))
        if view == 'Sf':
            mitt(fig, 43, 32, trim, w=3, h=3)
            pocket_watch(fig, 44, 27, keep)
        else:
            mitt(fig, 41, 55, trim)
        cap_front(fig, 32, TOP, keep, band=trim, w=7, crown_h=5)
    else:
        d = 1 if view == 'E' else -1
        u = M(d)
        # far leg and arm
        fx = min(u(33), u(34))
        limb(fig, (fx, 57), (fx, 62), 'iron', w=2, far=True)
        boot(fig, fx - (0 if d == 1 else 2), 63, 'soot', w=5, h=3, far=True)
        limb(fig, (u(29) - (0 if d == 1 else 1), 44), (u(27) - (0 if d == 1 else 1), 54), 'iron', w=2, far=True)
        mitt(fig, u(27) - (0 if d == 1 else 2), 55, trim, far=True)
        # near leg
        nx = min(u(31), u(32))
        limb(fig, (nx, 57), (nx, 62), 'iron', w=2)
        fig.put(nx, 60, trim, 3)
        fig.put(nx + 1, 60, trim, 2)
        boot(fig, nx - (0 if d == 1 else 2), 63, 'soot', w=5, h=3)
        tx = nx + (3 if d == 1 else -1)
        fig.put(tx, 63, trim, 4)
        fig.put(tx + 1, 63, trim, 3)
        # torso in profile: chest forward, tails behind
        pts = [(26, 42), (38, 42), (37, 50), (36, 50), (38, 58), (25, 58), (28, 50), (27, 50)]
        pts = [(u(x), y) for x, y in pts]
        coat = fig.poly(pts) | R(fig, d, 27, 42, 37, 44)
        tails = fig.poly([(u(28), 51), (u(24), 58), (u(28), 58)])
        coat |= tails
        plate(fig, coat, body, sheen=0.55)
        seam_h(fig, u(24), u(38), 50, body)
        for x in range(min(u(28), u(36)), max(u(28), u(36)) + 1):
            fig.put(x, 50, trim, 4 if x < 33 else 3)
        rivet(fig, u(35), 53, trim, keep, t=4)
        rivet(fig, u(35), 56, trim, keep, t=4)
        rim = fig.ellipse(u(35) + 0.5, 46.5, 2.2, 3.4)
        pane = fig.ellipse(u(35) + 0.5, 46.5, 1.1, 2.3)
        ring_shade(fig, rim - pane, trim, u(35) + 0.5, 46.5, 3.0)
        for (x, y) in pane:
            fig.put(x, y, 'slate', 1 if y < 46 else 2)
        fig.put(min(x for x, y in pane), 47, trim, 4)
        neck = R(fig, d, 31, 40, 33, 41)
        cyl(fig, neck, 'iron')
        dial_side(fig, d, u(32), cyh, 8, trim, keep, case_fam=trim)
        # near arm and epaulette
        sh = u(31) - (0 if d == 1 else 1)
        ep = fig.rect(sh - 1, 42, sh + 2, 43)
        plate(fig, ep, trim)
        limb(fig, (sh, 44), (sh + d, 54), 'iron', w=2)
        mitt(fig, sh + d - (0 if d == 1 else 1), 55, trim)
        cap_side(fig, d, u(32), TOP, keep, band=trim, w=6, crown_h=5)
    return finish(fig, keep)


# --- option C: the engine barrel -------------------------------------------------------
def hoop(fig, mask, y0, y1, fam):
    """A copper hoop round the barrel: a band following the barrel's width, lit on its top
    row, dark on its bottom, shaded east."""
    rows, _ = _extents(mask)
    for y in range(y0, y1 + 1):
        if y not in rows:
            continue
        a, b = rows[y]
        for x in range(a, b + 1):
            t = 3
            if y == y0:
                t = 4
            if y == y1:
                t = 1
            if x >= b - 1 and y != y0:
                t = min(t, 2)
            if x == a and y != y1:
                t = 4
            fig.put(x, y, fam, t)


def option_c(view):
    fig = sk.Fig(W, H)
    keep = set()
    body, trim = 'brass', 'copper'
    cyh = 28
    if view in ('S', 'Sf'):
        for x0 in (25, 36):
            limb(fig, (x0, 57), (x0, 61), 'soot', w=4)
        boot(fig, 23, 62, 'soot', w=8, h=4)
        boot(fig, 34, 62, 'soot', w=8, h=4)
        for x in range(23, 31):
            fig.put(x, 62, trim, 4 if x < 26 else 3)
        for x in range(34, 42):
            fig.put(x, 62, trim, 4 if x < 37 else 3)
        # arms: stout pipes from ball shoulders
        limb(fig, (16, 42), (16, 51), 'soot', w=3)
        if view == 'Sf':
            limb(fig, (47, 42), (46, 36), 'soot', w=3)
        else:
            limb(fig, (47, 42), (47, 51), 'soot', w=3)
        barrel = fig.ellipse(32.5, 46.5, 13, 11)
        ball(fig, barrel, body, glint=True)
        for (x, y) in barrel:   # a barrel is a cylinder: keep the side bands vertical
            u = (x + 0.5 - 32.5) / 13
            if u < -0.62 and tone(fig, (x, y)) in (2, 3):
                fig.put(x, y, body, 3 if y > 50 else 4)
        hoop(fig, barrel, 38, 39, trim)
        hoop(fig, barrel, 54, 55, trim)
        # boiler plate seams and rivets
        seam_v(fig, 22, 41, 52, body)
        seam_v(fig, 43, 41, 52, body)
        for (x, y) in ((24, 42), (24, 50), (41, 42), (41, 50), (32, 41)):
            rivet(fig, x, y, body, keep, t=5 if x < 32 else 4)
        rim = fig.ellipse(32.5, 47.5, 6.6, 6.6)
        pane = fig.ellipse(32.5, 47.5, 4.6, 4.6)
        ring_shade(fig, rim - pane, trim, 32.5, 47.5, 6.6)
        glass(fig, pane, keep, swing=(-2 if view == 'Sf' else 1), bob_r=1.7)
        for (x, y) in ((27, 43), (38, 43), (27, 51), (38, 51)):
            fig.put(x, y, trim, 5 if x < 32 else 4)
            keep.add((x, y))
        for sx in (14, 45):
            sh = fig.ellipse(sx + 2.5, 41.5, 3, 3)
            ball(fig, sh, trim, glint=True)
        mitt_c(fig, 15, 52)
        # collar and the small round head-dial
        collar = fig.rect(28, 34, 37, 36, knock=1)
        plate(fig, collar, trim, glint=False)
        dial_front(fig, 32, cyh, 6, body, keep, minute='back' if view == 'Sf' else 'up')
        if view == 'Sf':
            mitt_c(fig, 45, 32)
            pocket_watch(fig, 46, 27, keep, chain_to=(40, 42))
        else:
            mitt_c(fig, 46, 52)
        cap_front(fig, 32, TOP + 1, keep, band=trim, w=6, crown_h=3)
        # a little steam whistle on the crown, stubby: an engine's voice
    else:
        d = 1 if view == 'E' else -1
        u = M(d)
        fx = min(u(34), u(37))
        limb(fig, (fx, 57), (fx, 61), 'soot', w=4, far=True)
        boot(fig, fx - (0 if d == 1 else 3), 62, 'soot', w=7, h=4, far=True)
        limb(fig, (u(25) - (0 if d == 1 else 2), 42), (u(24) - (0 if d == 1 else 2), 51), 'soot', w=3, far=True)
        mitt_c(fig, u(24) - (1 if d == 1 else 3), 52, far=True)
        nx = min(u(29), u(32))
        limb(fig, (nx, 57), (nx, 61), 'soot', w=4)
        boot(fig, nx - (0 if d == 1 else 3), 62, 'soot', w=8, h=4)
        tx = nx + (4 if d == 1 else -4)
        for x in range(min(tx, tx + d * 3), max(tx, tx + d * 3) + 1):
            fig.put(x, 62, trim, 3)
        fig.put(min(tx, tx + d * 3), 62, trim, 4)
        barrel = fig.ellipse(u(32) + 0.5, 46.5, 11.5, 11)
        ball(fig, barrel, body, glint=True)
        hoop(fig, barrel, 38, 39, trim)
        hoop(fig, barrel, 54, 55, trim)
        seam_v(fig, u(28), 41, 52, body)
        rivet(fig, u(26), 43, body, keep)
        rivet(fig, u(26), 50, body, keep)
        # the porthole seen at an angle on the front of the barrel
        pc = u(39) + 0.5
        rim = fig.ellipse(pc, 47.5, 3.6, 6.4)
        pane = fig.ellipse(pc + d * 0.4, 47.5, 2.2, 4.6)
        ring_shade(fig, rim - pane, trim, pc, 47.5, 5.5)
        glass(fig, pane, keep, swing=0, bob_r=1.1)
        collar = R(fig, d, 28, 34, 37, 36, knock=1)
        plate(fig, collar, trim, glint=False)
        dial_side(fig, d, u(32), cyh, 6, body, keep, case_fam=body)
        sh = u(30) - (1 if d == 1 else 1)
        shm = fig.ellipse(sh + 0.5, 43.5, 2.6, 2.6)
        ball(fig, shm, trim)
        # the near arm hangs a little forward of the plumb, elbow soft, mitt at the hoop
        limb(fig, (sh - 2, 46), (sh - 2 + d * 2, 50), 'soot', w=4)
        for k in range(3):
            fig.put(sh - 1 + d * 2 + k, 47, 'soot', (3, 2, 1)[k])   # the elbow joint, a recess
        mitt_c(fig, sh - 2 + d * 2, 51)
        cap_side(fig, d, u(32), TOP + 1, keep, band=trim, w=5, crown_h=3)
    return finish(fig, keep)


VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Longcase: a grandfather-clock body in verdigris copper on short legs',
        question='The build is a longcase clock walking: the dial in a square hood is the head, the trunk '
                 'carries a long glass door with the pendulum, a plinth, short soot legs.',
        fn=option_a, palette=['copper', 'brass', 'plaster', 'slate', 'soot'],
        pose='Upright and patient as a clock on a landing, arms at its sides; it never hurries.',
        parts=[
            'boots x2 (brass plates): layer 1; foot; short 6-frame shuffle, a hop lifts the whole case 4 rig px',
            'legs x2 (soot pipes, brass knee collars): layer 1; hip; 2 to 3 px of travel, far leg a tone back',
            'plinth (copper_cool plate, brass ledge): layer 2; hip; squash 1 px on landing, sits flat in nap',
            'trunk (copper plates, rivets) with the glass door: layer 3; hip; breath = the case rises 1 px',
            'pendulum (brass rod and bob behind slate glass): layer 2.5; chest; swings 1 px a beat, stops in nap',
            'arms x2 (soot pipes, brass pivots, brass mitts): layer 2 far / 4 near; chest; walk swing, wind-up, guard',
            'hood with the dial (copper case, brass bezel, plaster face, ink hands and eyes): layer 5; chest; '
            'tilts 1 px in fidget, hands move in cast (the card set "on the clock")',
            'conductor\'s cap (soot, brass band and badge): layer 6; head; doffed in cheer',
        ],
        notes=[
            'Works: the tallest, squarest silhouette in the cast; nobody else is a box. Verdigris copper is ours '
            'alone (no folk owns it) and reads as old station metal against the brass trim.',
            'Risk: the short legs make the walk a shuffle and the fight poses stiff; the hood is wider than the '
            'trunk so arms must swing outside it. A long head-to-body plate could read as furniture.',
            'Compared with Eastward 05 at about the same height: John (chunky parts, 4 tones a material) and the '
            'riveted portable cabins (plates with square corners, a lit top lip, rivets as lit heads).',
        ]),
    dict(
        label='B', name='Station master: slender riveted soot coat, long limbs, a big round clock head',
        question='The build is a station master: a big round dial head on a thin neck, a coat of soot plates '
                 'pinched at the waist and flared at the tails, a small porthole in the chest.',
        fn=option_b, palette=['soot', 'brass', 'plaster', 'slate', 'iron'],
        pose='Tall and correct, chin (dial) up, hands at the seams of its coat, waiting for the whistle.',
        parts=[
            'boots x2 (soot, brass toe caps): layer 1; foot; long 6-frame stride',
            'legs x2 (iron pipes, brass knees): layer 1; hip; far a tone back',
            'coat tails (soot plates): layer 2; hip; swing a frame behind the stride, flare in hop',
            'coat body (soot plates, brass lapel line, belt, rivets) with the chest porthole: layer 3; hip; breath',
            'pendulum (brass, small, behind the porthole): layer 2.5; chest; ticks 1 px',
            'epaulettes x2 (brass): layer 4; chest; lift on guard and cheer',
            'arms x2 (iron pipes, brass mitts): layer 2 far / 5 near; chest; long swing, strike, cast with the watch',
            'pocket watch (brass, plaster face): layer 5; hand; out in fidget and cast',
            'head dial (brass bezel, plaster face, ink hands and eyes): layer 6; chest (neck); tilts, the minute '
            'hand moves in fidget',
            'conductor\'s cap (soot, brass band and badge): layer 7; head',
        ],
        notes=[
            'Works: the clearest clock: the head is a full station dial, big enough to read the hands at 2 px. '
            'A lollipop silhouette no other folk has; the fidget (watch up, minute hand nudged back) tells its story.',
            'Risk: soot coat and slate glass sit close in value, so the porthole needs its brass rim; thin limbs '
            'at 2 px are 2 px wide and only read on the light ground. Close to a human in silhouette.',
            'Compared with Eastward 05 at about the same height: John\'s dark jacket (lit left band, dark right, '
            'few large parts) and the cabin rivets; the dial treated like their round signs (rim lit upper left).',
        ]),
    dict(
        label='C', name='Engine barrel: a brass boiler body with copper hoops and a big porthole belly',
        question='The build is an engine: a barrel chest of brass boiler plate, copper hoops, a big round '
                 'porthole showing the pendulum, a small round head-dial, stout soot limbs.',
        fn=option_c, palette=['brass', 'copper', 'soot', 'plaster', 'slate'],
        pose='Stout and steady, weight low, fists loose: a shunting engine idling at the platform.',
        parts=[
            'boots x2 (soot, copper toe caps): layer 1; foot; heavy 6-frame stomp',
            'legs x2 (soot pipes, 4 px): layer 1; hip; far a tone back',
            'barrel (brass boiler plates, copper hoops, rivets) with the porthole: layer 3; hip; breath 1 px, '
            'squash on hop',
            'pendulum (brass behind slate glass): layer 2.5; chest; swings in the porthole, stops in nap',
            'shoulders x2 (copper balls) and arms (soot pipes, soot mitts under copper cuffs): layer 2 far / 4 near; chest; '
            'big swing, punch strike, guard behind crossed mitts',
            'pocket watch on a chain (brass): layer 4; chest to hand; out in fidget and cast',
            'head dial (brass bezel, plaster face): layer 5; chest (copper collar); tilt and look',
            'conductor\'s cap (soot, copper band): layer 6; head',
        ],
        notes=[
            'Works: the biggest belly window, so the pendulum is the first thing you see; the heavy round mass '
            'reads at 2 px and is warm brass where Bunk is a white barrel.',
            'Risk: the head-dial is small (11 px face), so the hands and eyes crowd; a round body is close to '
            'Tally\'s round cardigan in silhouette (the arms and boots must carry the difference).',
            'Compared with Eastward 05 at about the same height: the round cabin lamps and tanks (a lit cap at '
            'the upper left, a dark crescent) and John\'s proportion of head to body.',
        ]),
]


# --- the final: B, the station master, with grafts ----------------------------------------
# Grafts: C's copper ball shoulders (the perch) and porthole belly; A's verdigris copper as the
# coat's accent (a riveted chest panel, copper limbs). Brass is trim only: the bezel, the
# porthole rim, the buttons, the toe caps, the cap badge and band, the pendulum.
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/pendle-final.png')
F_CY = 31            # the dial's hub row (idle)
F_RF = 8             # the dial face radius; the bezel is two more


def face_v2(fig, face, cx, cy, rf, side=0):
    """A flat white needs a lit and a shaded edge (craft top fix): plaster 4 body, a lit
    tone 5 rim at the upper left, a two-step shaded crescent at the lower right (3, then 2
    at the very edge). `side` 1 or -1 is a dial turned E or W: E faces away from the light."""
    rx = max(1.0, (max(x for x, y in face) - min(x for x, y in face) + 1) / 2)
    ry = rf
    for (x, y) in face:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        edge = any((x + dx, y + dy) not in face for dx, dy in N4)
        t = 4 if side != 1 else (3 if u < 0.1 else 2)
        r2 = u * u + v * v
        if u + v > 0.35 and r2 > 0.62:
            t = 3 if side != 1 else 2
        if u + v > 0.5 and edge:
            t = 2
        if edge and u + v < -0.35:
            t = 5 if side != 1 else 4
        fig.put(x, y, 'plaster', t)


def f_dial_front(fig, cx, cy, keep, eyes='open', minute='up', rf=F_RF):
    fc = cx + 0.5
    outer = fig.ellipse(fc, cy + 0.5, rf + 2, rf + 2)
    face = fig.ellipse(fc, cy + 0.5, rf, rf)
    ring_shade(fig, outer - face, 'brass', fc, cy + 0.5, rf + 2)
    face_v2(fig, face, fc, cy + 0.5, rf)
    for p in ((cx - rf + 3, cy - rf + 4), (cx - rf + 4, cy - rf + 3)):   # the cover glass glint
        fig.put(p[0], p[1], 'plaster', 5)
        keep.add(p)
    ink = [(cx, cy - rf + 1), (cx, cy - rf + 2), (cx, cy + rf - 2), (cx, cy + rf - 1),
           (cx - rf + 1, cy), (cx - rf + 2, cy), (cx + rf - 2, cy), (cx + rf - 1, cy)]
    if minute == 'up':
        ink += [(cx, cy - k) for k in range(0, rf - 3)]
    else:   # nudged back towards the 11
        ink += [(cx, cy), (cx, cy - 1), (cx - 1, cy - 1), (cx - 1, cy - 2), (cx - 2, cy - 2), (cx - 2, cy - 3)]
    ink += [(cx + 1, cy), (cx + 1, cy - 1), (cx + 2, cy - 1), (cx + 2, cy - 2)]
    exs = (cx - 4, cx + 3)
    ey = cy + 1
    if eyes == 'open':
        for ex in exs:
            ink += [(ex + i, ey + j) for i in range(2) for j in range(3)]
    elif eyes == 'shut':
        for ex in exs:
            ink += [(ex - 1, ey + 2), (ex, ey + 2), (ex + 1, ey + 2), (ex + 2, ey + 2)]
    elif eyes == 'happy':
        for ex in exs:
            ink += [(ex - 1, ey + 2), (ex, ey + 1), (ex + 1, ey + 1), (ex + 2, ey + 2)]
    for p in ink:
        if p in face:
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
    if eyes == 'open':
        for ex in exs:
            fig.put(ex, ey, 'plaster', 5)
            keep.add((ex, ey))
    return outer


def f_dial_side(fig, d, hx, cy, keep, eyes='open', rf=F_RF):
    """Three-quarter dial: the brass drum behind, the bezel and face stepped forward of it
    (the face step), the drum's rounded back as the 'skull', the cap's peak as the brow."""
    drum = fig.ellipse(hx - d * 2 + 0.5, cy + 0.5, rf * 0.8 + 1, rf + 2)
    ball(fig, drum, 'brass_cool', glint=False)
    # the drum's back rim: a lit band on the upper left where the case turns
    for (x, y) in drum:
        u = (x + 0.5 - (hx - d * 2 + 0.5)) / (rf * 0.8 + 1)
        v = (y + 0.5 - cy - 0.5) / (rf + 2)
        if 0.55 * u + 0.85 * v < -0.3:
            fig.put(x, y, 'brass_cool', 4)
        elif u < -0.55 and v < 0.6:
            fig.put(x, y, 'brass_cool', 4 if v < 0.2 else 3)
    fcx = hx + d * 1.5 + 0.5
    rx = rf * 0.72
    outer = fig.ellipse(fcx, cy + 0.5, rx + 1.6, rf + 2)
    face = fig.ellipse(fcx + d * 0.4, cy + 0.5, rx, rf)
    ring_shade(fig, outer - face, 'brass', fcx, cy + 0.5, rf + 2)
    face_v2(fig, face, fcx + d * 0.4, cy + 0.5, rf, side=d)
    xs = sorted({x for x, y in face})
    mid = xs[len(xs) // 2]
    ink = [(mid, cy - rf + 1), (mid, cy - rf + 2), (mid, cy + rf - 2), (mid, cy + rf - 1)]
    ink += [(mid, cy - k) for k in range(0, rf - 3)]
    ink += [(mid + 1, cy - 1), (mid + 2, cy - 1)]
    near = mid + d * 2
    far = mid - d * 3 if d == 1 else mid + 2
    ey = cy + 1
    if eyes == 'open':
        eye = [(near + d * i, ey + j) for i in range(2) for j in range(3)] + [(far, ey + j) for j in range(3)]
    elif eyes == 'shut':
        eye = [(near + d * i, ey + 2) for i in range(-1, 3)] + [(far, ey + 2)]
    else:   # happy arcs
        eye = [(near - d, ey + 2), (near, ey + 1), (near + d, ey + 1), (near + 2 * d, ey + 2), (far, ey + 1)]
    for p in ink + eye:
        if p in face:
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
    if eyes == 'open':
        g = (min(near, near + d), ey)
        fig.put(g[0], g[1], 'plaster', 5)
        keep.add(g)
    # the winding key on the drum's side
    kx = hx - d * 5
    fig.put(kx, cy, 'brass', 4)
    fig.put(kx, cy + 1, 'brass', 2)
    keep |= {(kx, cy), (kx, cy + 1)}
    return outer | drum


def soot_coat(fig, mask, warm_rows=None):
    """Soot plates with their full five tones (so the dark coat never turns muddy): a lit
    top and west lip (4), a second lit column (4 on the upper half), the body (3), a shaded
    east band two px wide (2), the bottom row (1), a two-pixel glint (5)."""
    plate(fig, mask, 'soot', sheen=0.45)
    rows, cols = _extents(mask)
    for (x, y) in mask:
        a, b = rows[y]
        t = tone(fig, (x, y))
        if x == a + 1 and t == 3:
            fig.put(x, y, 'soot', 4)
        if b - x == 1 and t == 3:
            fig.put(x, y, 'soot', 2)
    if warm_rows:
        for (x, y) in mask:
            if warm_rows[0] <= y <= warm_rows[1]:
                fig.put(x, y, 'soot_warm', tone(fig, (x, y)))


def thick(fig, a, b, fam, far=False):
    """A 3 px limb (production: 2 px limbs thin out in strike): 3 x 3 stamps along a to b,
    shaded as a pipe across its run (vertical runs lit west, horizontal runs lit on top)."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    m = set()
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                m.add((x + dx, y + dy))
    cyl(fig, m, fam, horizontal=abs(x1 - x0) > abs(y1 - y0))
    if far:
        for p in m:
            fig.put(p[0], p[1], fam, max(1, tone(fig, p) - 1))
    return m


def arm(fig, sh, hand, far=False, watch=False, keep=None):
    """A coat sleeve (soot_cool, so it parts from the soot coat by hue as well as by its
    lit band), a copper cuff ring, a copper mitt."""
    (sx, sy), (hx, hy) = sh, hand
    ex, ey = (sx + hx) // 2, (sy + hy) // 2 + 1
    a = thick(fig, (sx, sy), (ex, ey), 'soot_cool', far)
    b = thick(fig, (ex, ey), (hx, hy), 'soot_cool', far)
    for (x, y) in a & b:                 # the elbow crease: a tone down
        fig.put(x, y, 'soot_cool', max(1, tone(fig, (x, y)) - 1))
    # cuff: the two stamps nearest the hand in copper
    n = max(abs(hx - ex), abs(hy - ey), 1)
    for i in (n - 2, n - 1):
        cx_ = round(ex + (hx - ex) * i / n)
        cy_ = round(ey + (hy - ey) * i / n)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (cx_ + dx, cy_ + dy) in b:
                    t = tone(fig, (cx_ + dx, cy_ + dy))
                    fig.put(cx_ + dx, cy_ + dy, 'copper', min(5, t + (0 if far else 1)))
    m = fig.rect(hx - 2, hy - 1, hx + 1, hy + 2, knock=1)
    plate(fig, m, 'copper', sheen=0.3, glint=not far)
    if far:
        for p in m:
            fig.put(p[0], p[1], 'copper', max(1, tone(fig, p) - 1))
    if watch:
        pocket_watch(fig, hx - 2, hy - 7, keep)


def f_boot(fig, x0, y0, d, far=False):
    """A soot boot, 5 wide, toe forward (d) with a brass toe cap; d=0 faces S."""
    m = fig.rect(x0, y0, x0 + 4, y0 + 2)
    plate(fig, m, 'soot', sheen=0.4, glint=not far)
    for x in range(x0, x0 + 5):
        fig.put(x, y0 + 2, 'soot', 1)
    if d == 0:
        caps = [(x0 + 1, y0), (x0 + 2, y0), (x0 + 3, y0)]
    else:
        tx = x0 + 3 if d == 1 else x0
        caps = [(tx, y0), (tx + 1, y0), (tx, y0 + 1), (tx + 1, y0 + 1)]
    for i, (x, y) in enumerate(sorted(caps)):
        fig.put(x, y, 'brass', (4 if i == 0 else 3) - (1 if far else 0))
    if far:
        for p in m:
            if fam_at(fig, p) == 'soot':
                fig.put(p[0], p[1], 'soot', max(1, tone(fig, p) - 1))
    return m


def copper_ball(fig, cx, cy, r=2.8, far=False):
    m = fig.ellipse(cx, cy, r, r)
    ball(fig, m, 'copper', glint=not far)
    if far:
        for p in m:
            fig.put(p[0], p[1], 'copper', max(1, tone(fig, p) - 1))
    return m


def mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = fig.ellipse(cx, base - 5, 7.5, 5.5)
        ball(fig, body, 'leaf', glint=False)
        for x in (cx - 3, cx + 1):
            fig.put(x, base - 6, 'ink', 0)
            fig.put(x + 1, base - 6, 'ink', 0)
        for (x, y, t) in ((cx + 4, base - 11, 4), (cx + 5, base - 11, 4), (cx + 6, base - 10, 3), (cx + 5, base - 12, 4)):
            fig.put(x, y, 'leaf_warm', t)
        return keep
    body = fig.ellipse(cx, base - 9, 8, 9)
    ball(fig, body, 'leaf', glint=False)
    rows, _ = _extents(body)
    for y, (a, b) in rows.items():       # a lit west rim down to the belly (sky light)
        if y < base - 3:
            fig.put(a, y, 'leaf', 4)
            fig.put(a + 1, y, 'leaf', 4)
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


def chest_panel_front(fig, keep, x0=28, x1=36, y0=44, y1=56, swing=0):
    """The verdigris chest panel (from A), riveted, with the porthole belly (from C)."""
    panel = fig.rect(x0, y0, x1, y1)
    plate(fig, panel, 'copper', sheen=0.5)
    for y in range(y0, y1 + 1):          # the panel sits in a recess: dark seam either side
        if fam_at(fig, (x0 - 1, y)) == 'soot':
            fig.put(x0 - 1, y, 'soot', 1)
    for (x, y) in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 2), (x1 - 1, y1 - 2)):
        rivet(fig, x, y, 'copper', keep)
    cx, cy = (x0 + x1 + 1) / 2, (y0 + y1 + 1) / 2 + 0.5
    rim = fig.ellipse(cx, cy, 4.4, 4.4)
    pane = fig.ellipse(cx, cy, 3.2, 3.2)
    ring_shade(fig, rim - pane, 'brass', cx, cy, 4.4)
    glass(fig, pane, keep, swing=swing, bob_r=1.3)
    return panel


def final_front(view):
    fig = sk.Fig(W, H)
    keep = set()
    fid = view == 'Sf'
    # legs and boots
    for x0 in (29, 36):
        thick(fig, (x0, 59), (x0, 62), 'copper')
        for dx in (-1, 0, 1):
            fig.put(x0 + dx, 60, 'soot', (3, 2, 1)[dx + 1])      # knee collar
    f_boot(fig, 26, 63, 0)
    f_boot(fig, 34, 63, 0)
    # coat
    coat = fig.poly([(24, 43), (41, 43), (39, 51), (42, 59), (23, 59), (26, 51)])
    soot_coat(fig, coat, warm_rows=(51, 58))
    seam_h(fig, 23, 42, 50, 'soot')
    for x in range(23, 43):              # the skirt is a second plate: its top lip is lit
        if fam_at(fig, (x, 51)) == 'soot_warm' and tone(fig, (x, 51)) in (2, 3):
            fig.put(x, 51, 'soot_warm', 4)
    seam_v(fig, 32, 57, 58, 'soot_warm')
    for (x, y) in ((25, 46), (25, 49), (39, 46), (39, 49)):
        fig.put(x, y, 'brass', 4 if x < 32 else 3)
        fig.put(x, y + 1, 'soot', 1)
        keep |= {(x, y), (x, y + 1)}
    chest_panel_front(fig, keep, swing=(2 if fid else 0))
    neck = fig.rect(30, 41, 34, 42)
    cyl(fig, neck, 'soot')
    # arms: soot sleeves from copper ball shoulders
    arm(fig, (22, 47), (22, 56))
    if fid:
        arm(fig, (43, 46), (45, 34), watch=True, keep=keep)
    else:
        arm(fig, (42, 47), (42, 56))
    copper_ball(fig, 23.0, 44.5)
    copper_ball(fig, 42.0, 44.5)
    f_dial_front(fig, 32, F_CY, keep, minute=('back' if fid else 'up'))
    cap_front(fig, 32, TOP + 2, keep, band='brass', w=7, crown_h=4)
    return finish(fig, keep)


POSES = {
    #          body u/y  head u/y  legs       near hand    far hand     eyes     watch
    'idle':   (0, 0,     0, 0,    'stand',   (1, 56),     (-2, 55),    'open',  False),
    'ready':  (0, 1,     1, 0,    'wide',    (7, 47),     (-5, 51),    'open',  False),
    'strike': (3, 1,     4, 1,    'lunge',   (16, 45),    (-6, 53),    'open',  False),
    'cast':   (0, 0,     -1, -1,  'wide',    (13, 31),    (4, 49),     'open',  True),
    'hit':    (-3, 0,    -4, -1,  'stumble', (-1, 41),    (-7, 44),    'shut',  False),
    'sit':    (0, 6,     1, 0,    'sit',     (6, 58),     (4, 58),     'open',  False),
    'cheer':  (0, -4,    0, -1,   'jump',    (13, 31),    (-10, 22),   'happy', False),
}


def final_side(d, pose, familiar=False):
    bx, by, hx, hy, legs, near, far, eyes, watch = POSES[pose]
    fig = sk.Fig(W, H)
    keep = set()
    cx = AX + d * bx
    U = lambda u: cx + d * u   # noqa: E731  (forward is +u in either facing)

    def RU(u0, y0, u1, y1, knock=0):
        a, b = sorted((U(u0), U(u1)))
        return fig.rect(a, y0, b, y1, knock)

    perch = None
    if familiar:
        # the far shoulder, away from the foe: x smaller in E, larger in W. The copper ball
        # stands proud of the coat's back, clear of the dial drum.
        perch = (U(-7), 41 + by)
        mossling(fig, U(-15), 43 + by, d, keep)
    hip = 58 + by
    # far arm, far shoulder (a tone back)
    if far:
        arm(fig, (U(-2), 46 + by), (U(far[0]), far[1] + (by if pose not in ('cheer', 'cast') else 0)), far=True)
    # legs
    if legs == 'stand':
        lg = [((-2, hip), (-2, SOLE - 3)), ((2, hip), (2, SOLE - 3))]
    elif legs == 'wide':
        lg = [((-2, hip), (-5, SOLE - 3)), ((2, hip), (4, SOLE - 3))]
    elif legs == 'lunge':
        lg = [((-2, hip), (-8, SOLE - 3)), ((2, hip), (7, SOLE - 3))]
    elif legs == 'stumble':
        lg = [((-2, hip), (-6, SOLE - 3)), ((2, hip), (5, SOLE - 5))]
    elif legs == 'sit':
        lg = [((1, hip - 2), (9, hip - 1)), ((3, hip - 1), (11, hip))]
    else:   # jump: legs tucked
        lg = [((-2, hip), (-3, hip + 3)), ((2, hip), (3, hip + 3))]
    for i, (a, b) in enumerate(lg):
        # the leading leg is the far one (a tone back), the trailing leg the near one
        thick(fig, (U(a[0]), a[1]), (U(b[0]), b[1]), 'copper', far=(i == 1))
        bxp, byp = U(b[0]), b[1] + 1
        if legs == 'sit':
            byp = b[1] - 3
        f_boot(fig, bxp - (1 if d == 1 else 3), byp, d, far=(i == 1))
    # coat in profile: chest forward, tails flared behind
    chest = RU(-5, 43 + by, 5, 50 + by)
    skirt = fig.poly([(U(-5), 51 + by), (U(5), 51 + by), (U(6), 58 + by), (U(-8), 58 + by)])
    coat = chest | skirt
    soot_coat(fig, coat, warm_rows=(51 + by, 58 + by))
    seam_h(fig, U(-8), U(6), 50 + by, 'soot')
    for (x, y) in skirt:
        if y == 51 + by and fam_at(fig, (x, y)) == 'soot_warm' and tone(fig, (x, y)) in (2, 3):
            fig.put(x, y, 'soot_warm', 4)
    # the copper chest panel and porthole on the front, foreshortened
    panel = RU(2, 44 + by, 5, 56 + by)
    plate(fig, panel, 'copper', sheen=0.5)
    if d == 1:   # the front faces E, away from the light: a tone down (east faces 1 to 2)
        for p in panel:
            fig.put(p[0], p[1], 'copper', max(1, tone(fig, p) - 1))
    rivet(fig, U(3), 45 + by, 'copper', keep)
    rivet(fig, U(3), 54 + by, 'copper', keep)
    pc = U(4) + 0.5
    rim = fig.ellipse(pc, 50.5 + by, 2.2, 4.2)
    pane = fig.ellipse(pc, 50.5 + by, 1.2, 3.0)
    ring_shade(fig, rim - pane, 'brass', pc, 50.5 + by, 3.5)
    for (x, y) in pane:
        fig.put(x, y, 'slate', 1 if y < 50 + by else 2)
    bob = (min(x for x, y in pane), 51 + by)
    fig.put(bob[0], bob[1], 'brass', 4)
    fig.put(bob[0], bob[1] + 1, 'brass', 3)
    for y in (46, 49):     # buttons down the coat's front edge
        fig.put(U(1), y + by, 'brass', 4 if d == -1 else 3)
        fig.put(U(1), y + by + 1, 'soot', 1)
        keep |= {(U(1), y + by), (U(1), y + by + 1)}
    if familiar:   # the far copper shoulder, proud of the coat's back: the perch
        copper_ball(fig, U(-7) + 0.5, 44.5 + by, r=3.0)
    neck = RU(-1, 40 + by, 1, 42 + by)
    cyl(fig, neck, 'soot')
    hcy = F_CY + by + hy
    f_dial_side(fig, d, U(hx), hcy, keep, eyes=eyes)
    cap_side(fig, d, U(hx), hcy - 15, keep, band='brass', w=6, crown_h=4)
    # near shoulder and arm last
    copper_ball(fig, U(0) + 0.5, 44.5 + by)
    hand = (U(near[0]), near[1] + (by if pose not in ('cheer', 'cast', 'hit') else 0))
    arm(fig, (U(0), 47 + by), hand, watch=watch, keep=keep)
    return finish(fig, keep), perch


def final_nap():
    """Nap, facing S: sat down with its knees drawn up, arms round them, the dial resting on
    its knees with the eyes shut, the cap tipped forward; the Mossling curled at its side."""
    fig = sk.Fig(W, H)
    keep = set()
    mossling(fig, 49, SOLE + 1, 1, keep, curled=True)
    # the coat pooled round it
    mound = fig.poly([(18, 65), (20, 52), (24, 47), (40, 47), (44, 52), (45, 65)])
    soot_coat(fig, mound, warm_rows=(58, 65))
    seam_h(fig, 18, 45, 57, 'soot')
    copper_ball(fig, 20.5, 50.5)
    copper_ball(fig, 43.5, 50.5)
    # boots side by side in front, toes to us
    f_boot(fig, 24, 62, 0)
    f_boot(fig, 34, 62, 0)
    # knees drawn up under the coat: two soot_warm caps, a crease between
    for kx in (27.5, 37.5):
        k = fig.ellipse(kx, 56.5, 4.2, 3.4)
        ball(fig, k, 'soot_warm', glint=False)
    # arms round the knees, mitts clasped in front
    arm(fig, (20, 53), (30, 61))
    arm(fig, (43, 53), (35, 61))
    # the dial head sunk forward onto the knees, eyes shut, minute hand still
    f_dial_front(fig, 32, 43, keep, eyes='shut', rf=7)
    cap_front(fig, 32, 30, keep, band='brass', w=7, crown_h=4, tilt=0)
    return finish(fig, keep)


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
    label='B final', name='Station master (final): soot coat with a verdigris panel, copper ball shoulders, porthole belly',
    chosen='B',
    grafts=[
        'From C: copper ball shoulders (the far one is the familiar\'s perch, standing proud of the coat\'s back, '
        'clear of the dial) in place of the thin brass epaulettes.',
        'From C: the porthole belly, now 9 px with a brass rim, the pendulum bob visible inside.',
        'From A: verdigris copper as the coat\'s accent: a riveted chest panel holding the porthole, copper limbs '
        'with soot joint collars, copper mitts.',
        'Brass as trim only: the bezel, the porthole rim, buttons, toe caps, the cap badge and band, the pendulum.',
        'Fixes: soot drawn in five tones (lit lip, second lit column, body, two-px shade band, seams; warm sibling '
        'for the skirt plate); the dial face lit on its upper-left rim and shaded in a two-step crescent at the '
        'lower right; limbs 3 px; the E profile keeps a lit drum rim so W-E stays positive.',
    ],
    palette=['soot', 'copper', 'brass', 'plaster', 'slate'],
    pose='Tall and correct, dial up, hands at the seams of its coat, waiting for the whistle a minute late.',
    parts=[
        'familiar perch: the far copper ball shoulder (E: x smaller, W: x larger), behind the dial drum; layer 0; chest',
        'far leg (copper pipe, soot knee collar) and far boot (soot, brass toe cap), a tone back: layer 1; hip; all facings',
        'far arm (copper, soot elbow, copper mitt), a tone back: layer 1; chest; all facings',
        'coat skirt (soot_warm plate, centre seam): layer 2; hip; flares a frame behind the stride, pools in nap',
        'coat body (soot plates, brass buttons): layer 3; hip; breath 1 px',
        'chest panel (copper, four rivets) with the porthole (brass rim, slate glass, brass pendulum): layer 3.5; '
        'chest; the bob swings 1 px a beat, stops in nap; foreshortened to the front edge in E/W',
        'near leg and boot: layer 4; hip; 6-frame stride, forward in sit',
        'head dial (brass bezel, brass_cool drum, plaster face, ink ticks, hands and eyes): layer 5; chest (soot neck); '
        'the minute hand moves in fidget and cast; the eyes shut in hit and nap, arc in cheer',
        'conductor\'s cap (soot crown, brass band and badge, soot peak as the brow): layer 6; head; all facings',
        'near shoulder (copper ball) and near arm (copper, soot elbow, copper mitt): layer 7; chest; swing, strike, guard',
        'pocket watch (brass case, plaster face): layer 7.5; near hand; out in fidget and cast',
    ],
    notes=[
        'Compared side by side with Eastward 05 at the same height: John\'s dark jacket (a lit west band, a dark '
        'east band, few large parts) for the soot coat, and the riveted portable cabins for the copper panel and rivets.',
        'Works: the big cream dial and the lollipop silhouette are unlike every other folk (and unlike Nix\'s cyan '
        'visor); the copper ball shoulders give a fixed perch clear of the head and match front and profile.',
        'Risk: the big dial still crowds the familiar in profile; the Mossling sits back on the far ball, half '
        'behind the drum. The hands must be redrawn, never rotated, per frame.',
        'Open for the art director: whether the cap should doff in cheer, and the familiar\'s final size on the ball.',
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
        ok &= all(g.values())
        print(f"final {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'] + ['leaf (stand-in familiar only)'][:0], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Pendle final (folk 8, Cogsworth): B, the station master, with grafts', [entry], OUT_FINAL,
                    note='52 art px, cell 64 x 72, foot (32, 66). World S/E/W, fidget, nap; fight E and W with the '
                         'stand-in Mossling on the far copper shoulder.')
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
            g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.06,
                     colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
            ok &= all(g.values())
            print(f"{o['label']} {cap:9s} on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet("Pendle (folk 8, Cogsworth): the automaton's build", OPTIONS, OUT_PNG,
                    note='52 art px, cell 64 x 72, foot (32, 66). Views: S, E, W idle and the S fidget key pose.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='pendle', height_art_px=52, cell=[W, H], foot=[AX, AY],
                       question="The automaton's build: longcase, station master or engine barrel.",
                       options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
