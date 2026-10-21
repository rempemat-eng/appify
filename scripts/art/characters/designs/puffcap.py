"""Puffcap design options (Claude J folk sheets, 21 Oct): what the cap is and how the
body sits under it. Three answers, each drawn S, E, W (W drawn with the light still on
the left, never mirrored) and the S fidget key pose (a sleepy beat).

Run from the repo root:  python3 scripts/art/characters/designs/puffcap.py
Writes docs/vision/characters/designs/puffcap-options.png and puffcap.json, and each
view under CHAR_VIEWS (default .char-views/, git-ignored) for grading.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/puffcap-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/puffcap.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '.char-views')), 'puffcap')

W, H = 56, 60
CX, FOOT = 28, 54          # foot anchor: the outline's lowest row sits on y 54


# --- helpers ---------------------------------------------------------------------------
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FACING = {'S': 0, 'E': 1, 'W': -1, 'F': 0}


def mx(x, f):
    """Place an x for a facing: f = +1 east (as written), -1 west (reflected about the
    anchor). Only geometry is reflected; every part is shaded afterwards with the light
    still at the upper left, so W is drawn, not mirrored."""
    return CX + (x - CX) * (1 if f >= 0 else -1)


def tube(fig, pts):
    """A soft tapering tube along (x, y, r) points: a nightcap's cone, a tail, an arm."""
    out = set()
    for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
        for i in range(11):
            t = i / 10
            out |= fig.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t,
                               r0 + (r1 - r0) * t)
    return out


def round_form(fig, mask, fam, cx, cy, rx, ry, lit=-0.5, dark=0.45, glint=True):
    """A round part: the kit's parts shading, then a lit cap at the upper left and a dark
    crescent at the lower right that follow the ellipse (not a diagonal stair)."""
    mask = set(mask)
    fig.shade(mask, fam, glint=False)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        n = 0.6 * u + 0.8 * v
        r2 = u * u + v * v
        t = fig.px[(x, y)][1]
        if n < lit and r2 > 0.15:
            t = 4
        elif n > dark and r2 > 0.35:
            t = min(t, 2)
        else:
            t = 3 if t != 1 else 1
        fig.put(x, y, fam, t)
    # the underside row is the deepest (a part's dark bottom)
    for (x, y) in mask:
        if (x, y + 1) not in mask and (x + 0.5 - cx) > -rx * 0.55:
            fig.put(x, y, fam, 1)
    if glint:
        best = sorted(mask, key=lambda p: 0.6 * (p[0] - cx) / rx + 0.8 * (p[1] - cy) / ry)
        for p in best[:2]:
            fig.put(p[0], p[1], fam, 5)
    return mask


def edge_form(fig, mask, fam, glint=True):
    """A thin part (a cone, a tail, a nub): lit along its upper left edge, dark along its
    lower right, the underside deepest."""
    mask = set(mask)
    for (x, y) in mask:
        up, left = (x, y - 1) not in mask, (x - 1, y) not in mask
        down, right = (x, y + 1) not in mask, (x + 1, y) not in mask
        t = 3
        if up or left:
            t = 4
        if right and not up:
            t = 2
        if down:
            t = 1 if not left else 2
        fig.put(x, y, fam, t)
    if glint:
        best = sorted(mask, key=lambda p: p[0] + 1.4 * p[1])
        for p in best[:2]:
            fig.put(p[0], p[1], fam, 5)
    return mask


def swap_clusters(fig, mask, sibling, pattern, step, phase=0, min_t=2, max_t=4, dt=0):
    """Texture as 2-4 px clusters that swap to a sibling ramp at the same tone (or dt)."""
    mask = set(mask)
    if not mask:
        return
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    row = 0
    for y in range(min(ys), max(ys) + 1, step[1]):
        off = (row % 2) * (step[0] // 2) + phase
        for x in range(min(xs) - step[0] + off, max(xs) + 1, step[0]):
            pts = [(x + dx, y + dy) for dx, dy in pattern]
            if all(q in mask and q in fig.px for q in pts):
                ts = [fig.px[q][1] for q in pts]
                if all(min_t <= t <= max_t for t in ts):
                    for q, t in zip(pts, ts):
                        fig.put(q[0], q[1], sibling, max(1, min(5, t + dt)))
        row += 1


def despeckle(fig, keep=frozenset(), passes=2):
    """House-style 4: no speckle. A fill pixel unlike all four neighbours takes the most
    common neighbour of its own family (the stair-steps a terminator leaves)."""
    for _ in range(passes):
        ch = {}
        for p, v in fig.px.items():
            if p in keep or v[0] == 'ink' or p in fig.fixed:
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n == v for n in nb):
                continue
            same = [n for n in nb if n and n[0] != 'ink' and sk.family_of(n[0]) == sk.family_of(v[0])]
            pool = same or [n for n in nb if n and n[0] != 'ink']
            if pool:
                ch[p] = max(sorted(set(pool), key=str), key=pool.count)
        if not ch:
            break
        fig.px.update(ch)


def put_on(fig, x, y, fam, tone, on=None):
    """Paint only where the figure already has a fill (of family `on`, if given)."""
    v = fig.px.get((x, y))
    if v and v[0] != 'ink' and (on is None or sk.family_of(v[0]) == on):
        fig.put(x, y, fam, tone)


def eye(fig, x, y, kind, skin):
    """Eyes are 2 x 2 ink so they read at 2 device px. open: a glint at the upper left.
    sleepy: a heavy lid (the skin's tone 1) across the top. shut: a 4 px downward curve.
    squeeze: an upward curve (a yawn)."""
    if kind in ('open', 'sleepy'):
        for dx in (0, 1):
            for dy in (0, 1):
                fig.put(x + dx, y + dy, 'ink', 0)
        if kind == 'open':
            fig.put(x, y, skin, 5)
        else:
            for dx in (-1, 0, 1, 2):
                put_on(fig, x + dx, y - 1, skin, 1)
    elif kind == 'shut':
        fig.put(x - 1, y, 'ink', 0)
        fig.put(x, y + 1, 'ink', 0)
        fig.put(x + 1, y + 1, 'ink', 0)
        fig.put(x + 2, y, 'ink', 0)
    elif kind == 'squeeze':
        fig.put(x - 1, y + 1, 'ink', 0)
        fig.put(x, y, 'ink', 0)
        fig.put(x + 1, y, 'ink', 0)
        fig.put(x + 2, y + 1, 'ink', 0)


def eyes_at(f, cx):
    """Left and right eye x for a facing (the eye pair slides towards the facing)."""
    if f == 0:
        return cx - 4, cx + 2
    if f > 0:
        return cx + 1, cx + 5
    return cx - 6, cx - 2


def cheeks(fig, f, e1, e2, y, skin):
    """Berry blush, two px each, the lit (west) one a tone up; only on the skin."""
    spots = []
    if f == 0:
        spots = [(e1 - 2, 4), (e1 - 1, 4), (e2 + 2, 3), (e2 + 3, 3)]
    elif f > 0:
        spots = [(e2 + 2, 3), (e2 + 3, 3)]
    else:
        spots = [(e1 - 3, 4), (e1 - 2, 4)]
    for x, t in spots:
        put_on(fig, x, y, 'berry', t, on=skin)


def spore(fig, x, y, horiz=True, tone=4):
    """A drifting spore: a 2 px glow (a light source, never outlined)."""
    fig.glow(x, y, 'glowflora', tone)
    fig.glow(x + (1 if horiz else 0), y + (0 if horiz else 1), 'glowflora', tone - 1)


def feet(fig, f, spread=3.5, y=52.2, fam='earth'):
    """Two root-nub feet, lit on top. In E/W the far foot sits a pixel higher (behind)."""
    if f == 0:
        pts = [(CX - spread, y), (CX + spread, y)]
    else:
        pts = [(mx(CX + 2.5, f), y - 0.8), (mx(CX - 2.0, f), y)]
    for fx, fy in pts:
        m = fig.ellipse(fx, fy, 2.7, 1.8)
        edge_form(fig, m, fam, glint=False)


def arm(fig, x, y, fam, rx=2.0, ry=2.7):
    """An arm nub over the body: the body just right of and below it is a joint, a
    tone darker than either part (house-style 4)."""
    m = fig.ellipse(x, y, rx, ry)
    for (px_, py_) in m:
        for q in ((px_ + 1, py_), (px_, py_ + 1)):
            if q not in m and q in fig.px and fig.px[q][0] != 'ink':
                fam_q, t = fig.px[q]
                fig.put(q[0], q[1], fam_q, max(1, min(t, 2)))
    edge_form(fig, m, fam, glint=False)
    return m


# --- option A: the cap is the nightcap ------------------------------------------------
def opt_a(view):
    """The mushroom's own cap is a felt nightcap: a dome that runs up into a cone, the
    tip flopping over with a pompom; its rolled margin is the cuff; face on the stem."""
    fig = sk.Fig(W, H)
    f, fid = FACING[view], view == 'F'
    up = 1 if fid else 0                       # the yawn stretches it a pixel taller
    feet(fig, f, spread=3.2)
    sy, srx, sry = 45.6 - up * 0.5, 7.0, 7.4 + up * 0.5
    stem = fig.ellipse(CX, sy, srx, sry)
    round_form(fig, stem, 'plaster', CX, sy, srx, sry, lit=-0.45, dark=0.4)
    swap_clusters(fig, stem, 'plaster_cool', [(0, 0), (0, 1), (0, 2)], (4, 6), phase=1, min_t=2, max_t=3)
    top = min(p[1] for p in stem)
    # arms (nubs); the yawn throws both up in a stretch
    if fid:
        arms = [(CX - 9.0, top + 2.5), (CX + 9.0, top + 2.5)]
    elif f == 0:
        arms = [(CX - 7.6, 46.5), (CX + 7.6, 46.5)]
    else:
        arms = [(mx(CX + 0.5, f), 47.5)]
    for ax, ay in arms:
        arm(fig, ax, ay, 'plaster_warm')
    # gills: two rows of radiating lines under the rim, narrower than the cap
    gtop = top - 2
    for y in (gtop, gtop + 1):
        for x in range(CX - 9 + (y - gtop), CX + 9 - (y - gtop)):
            fig.put(x, y, 'dusk_cool', 1 if (x - CX) % 3 else 0)
    # cap dome, its rolled margin (the cuff), and the cone flopping over
    dcy = gtop - 4.0
    DRX, DRY = 10.6, 8.2
    dome = {p for p in fig.ellipse(CX, dcy, DRX, DRY) if p[1] <= gtop - 1}
    if fid:
        cone_pts = [(CX - 1, dcy - 2, 4.4), (CX + 0, dcy - 6, 3.2), (CX + 1, dcy - 9, 2.4),
                    (CX + 2, dcy - 11.5, 1.8)]
        pom = (CX + 2.5, dcy - 13.5)
    else:
        # the tip always flops to the lit west: over the shoulder in S, behind the head in
        # E, and forward over the brow in W (a sleepy fringe), so no view lights the east
        raw = [(CX + 1, dcy - 4, 4.4), (CX - 2.5, dcy - 7.0, 3.4), (CX - 7, dcy - 7.6, 2.8),
               (CX - 11, dcy - 5.5, 2.3), (CX - 13.4, dcy - 1.8, 1.9), (CX - 14.2, dcy + 2.2, 1.5)]
        if f < 0:   # facing west the flop is shorter, hanging just past the brow
            raw = [(CX + 1, dcy - 4, 4.4), (CX - 2.5, dcy - 7.0, 3.4), (CX - 7, dcy - 7.4, 2.8),
                   (CX - 10.5, dcy - 5.0, 2.3), (CX - 12.2, dcy - 1.5, 1.9), (CX - 12.6, dcy + 2.0, 1.5)]
        g = 1
        cone_pts = [(mx(x, g), y, r) for x, y, r in raw]
        pom = (cone_pts[-1][0], dcy + 4.2)
    cone = tube(fig, cone_pts) - dome
    round_form(fig, dome, 'dusk', CX, dcy, DRX, DRY, lit=-0.4, dark=0.35, glint=False)
    swap_clusters(fig, dome, 'dusk_warm', [(0, 0), (1, 0)], (5, 2), min_t=3, max_t=4)
    swap_clusters(fig, dome, 'dusk_cool', [(0, 0), (1, 0), (1, 1)], (6, 3), phase=2, min_t=2, max_t=3)
    edge_form(fig, cone, 'dusk', glint=False)
    # where the cone leaves the dome, a fold (a recess a tone down)
    for (x, y) in cone:
        if (x, y + 1) in dome:
            fig.put(x, y, 'dusk_cool', 2)
    # the cuff: two rows, lit lip on top, the curl under it; lit to the west
    rim_rows = (gtop - 2, gtop - 1)
    for x in range(CX - 12, CX + 13):
        for k, y in enumerate(rim_rows):
            if (x, y) in dome:
                t = 4 if x < CX - 3 else 3 if x < CX + 6 else 2
                fig.put(x, y, 'dusk_warm', t - k)
    pm = fig.ellipse(pom[0], pom[1], 2.6, 2.6)
    round_form(fig, pm, 'plaster_warm', pom[0], pom[1], 2.6, 2.6, lit=-0.3, dark=0.5)
    if pom[0] > CX + 6:  # hanging behind, on the shaded east: the whole ball a tone down
        for q in pm:
            fam_q, t = fig.px[q]
            fig.put(q[0], q[1], 'plaster_cool', max(1, t - 1))
    despeckle(fig)
    # the face, in the cap's shade: the top row under the gills a tone down
    for x in range(CX - 7, CX + 8):
        if (x, top) in stem:
            fig.put(x, top, 'plaster', 2)
    ey = top + 2
    e1, e2 = eyes_at(f, CX)
    if fid:
        eye(fig, e1, ey, 'squeeze', 'plaster')
        eye(fig, e2, ey, 'squeeze', 'plaster')
        for (x, y) in fig.rect(CX - 2, ey + 3, CX + 1, ey + 6, knock=1):
            fig.put(x, y, 'ink', 0)
        fig.put(CX - 1, ey + 6, 'berry', 3)
        fig.put(CX, ey + 6, 'berry', 2)
    else:
        eye(fig, e1, ey, 'sleepy', 'plaster')
        eye(fig, e2, ey, 'sleepy', 'plaster')
        m0 = CX - 1 if f == 0 else (e2 - 1 if f > 0 else e1 + 1)
        fig.put(m0, ey + 4, 'plaster', 1)
        fig.put(m0 + 1, ey + 4, 'plaster', 1)
    cheeks(fig, f, e1, e2, ey + 3, 'plaster')
    fig.outline()
    if fid:
        spore(fig, CX - 11, ey - 3)
        spore(fig, CX + 10, ey - 6, horiz=False)
    return fig.image()


# --- option B: a pale mushroom head in a separate floppy nightcap ----------------------
def opt_b(view):
    """A tan button-mushroom head (the face on it) in a knitted sock cap whose tail flops
    over and hangs; the mushroom's ring is a frilled collar on a slim pale stem."""
    fig = sk.Fig(W, H)
    f, fid = FACING[view], view == 'F'
    feet(fig, f, spread=2.8)
    sy, srx, sry = 47.8, 4.8, 5.4
    stem = fig.ellipse(CX, sy, srx, sry)
    round_form(fig, stem, 'plaster', CX, sy, srx, sry, lit=-0.4, dark=0.35, glint=False)
    # arms from under the frill
    if f == 0:
        arms = [(CX - 6.2, 47.8), (CX + 6.2, 47.8)]
    else:
        arms = [(mx(CX + 0.5, f), 48.3)]
    if fid:
        arms = arms[:1]
    for ax, ay in arms:
        arm(fig, ax, ay, 'plaster', 1.9, 2.5)
    # the ring: a frilled skirt, scalloped lobes lit to the west
    ring = fig.ellipse(CX, 43.6, 7.6, 2.2)
    edge_form(fig, ring, 'plaster_warm', glint=False)
    hem = max(p[1] for p in ring)
    for x in range(CX - 8, CX + 9):
        if (x, hem) in ring and (x - CX) % 3 == 1:
            fig.put(x, hem, 'plaster_warm', 1 if x >= CX else 2)
            if (x, hem - 1) in ring:
                fig.put(x, hem - 1, 'plaster_warm', 2)
    # head: a tan button cap, round, the face on its lower half; gills under its lip
    hx, hy, hrx, hry = CX, 35.0, 10.2, 7.4
    head = {p for p in fig.ellipse(hx, hy, hrx, hry) if p[1] <= 41}
    round_form(fig, head, 'sand', hx, hy, hrx, hry, lit=-0.45, dark=0.35, glint=False)
    for x in range(CX - 9, CX + 10):
        if (x, 41) in head:
            fig.put(x, 41, 'sand_cool', 1 if (x - CX) % 3 else 0)
            if (x, 40) in head:
                fig.put(x, 40, 'sand', 2 if x < CX + 5 else 1)
    # the sock cap: crown over the top of the head, cuff, a long tail flopping over
    tilt = 1 if fid else 0
    ccx, ccy = CX + tilt, 32.2 + tilt
    crown = {p for p in fig.ellipse(ccx, ccy, 10.6, 7.6) if p[1] <= ccy - 0.5 + 0}
    raw = [(CX + 2, ccy - 5, 4.0), (CX + 7, ccy - 7.2, 3.2), (CX + 11.5, ccy - 5.5, 2.6),
           (CX + 14.2, ccy - 1.8, 2.1), (CX + 15.0, ccy + 2.6, 1.7)]
    g = -1 if f > 0 else 1
    if fid:
        raw = [(x + 1, y + 1, r) for x, y, r in raw]
    tail = tube(fig, [(mx(x, g), y, r) for x, y, r in raw]) - crown
    pom = (mx(CX + 15.0 + (1 if fid else 0), g), ccy + 4.8 + (1 if fid else 0))
    round_form(fig, crown, 'dusk', ccx, ccy, 10.6, 7.6, lit=-0.4, dark=0.3, glint=False)
    edge_form(fig, tail, 'dusk', glint=False)
    # knit: rows of 2 px loops in the cool sibling; the tail in wide stripes
    swap_clusters(fig, crown, 'dusk_cool', [(0, 0), (1, 0)], (4, 2), min_t=2, max_t=4)
    for (x, y) in tail:
        if (y // 3) % 2 == 0:
            t = fig.px[(x, y)][1]
            fig.put(x, y, 'dusk_cool', max(1, t - 1))
    # the cuff: two ribbed rows, lit to the west
    cy0 = max(p[1] for p in crown)
    for x in range(CX - 12, CX + 13):
        for k, y in enumerate((cy0 - 1, cy0)):
            if (x, y) in crown:
                t = 4 if x < CX - 3 else 3 if x < CX + 5 else 2
                t -= k
                if ((x - CX) // 2) % 2 == 0:
                    t = max(1, t - 1)          # 2 px ribs
                fig.put(x, y, 'dusk_warm', t)
    pm = fig.ellipse(pom[0], pom[1], 2.6, 2.6)
    round_form(fig, pm, 'plaster_warm', pom[0], pom[1], 2.6, 2.6, lit=-0.3, dark=0.5)
    ey = 35 + tilt
    e1, e2 = eyes_at(f, CX)
    if fid:
        # the paw rubbing the right eye, a forearm reaching up from the body
        fore = tube(fig, [(CX + 6.5, 46, 1.7), (CX + 4.5, 41.5, 1.7)])
        edge_form(fig, fore - head, 'plaster', glint=False)
        paw = fig.ellipse(e2 + 1, ey + 1.0, 2.5, 2.3)
        for (x, y) in paw:
            for q in ((x, y + 1), (x + 1, y)):
                if q not in paw and q in head:
                    fig.put(q[0], q[1], 'sand', 1)     # its shadow on the cheek
        edge_form(fig, paw, 'plaster', glint=False)
    despeckle(fig)
    # face on the head
    if fid:
        eye(fig, e1, ey, 'sleepy', 'sand')
        fig.put(CX - 2, ey + 4, 'ink', 0)
        fig.put(CX - 1, ey + 4, 'ink', 0)
        fig.put(CX - 2, ey + 5, 'sand', 1)
        fig.put(CX - 1, ey + 5, 'sand', 1)
        cheeks(fig, 0, e1, e2, ey + 3, 'sand')
    else:
        eye(fig, e1, ey, 'open', 'sand')
        eye(fig, e2, ey, 'open', 'sand')
        m0 = CX - 1 if f == 0 else (e2 - 1 if f > 0 else e1 + 1)
        fig.put(m0, ey + 4, 'sand', 1)
        fig.put(m0 + 1, ey + 4, 'sand', 1)
        cheeks(fig, f, e1, e2, ey + 3, 'sand')
    fig.outline()
    return fig.image()


# --- option C: a stout stem under a wide flat quilted cap (a mat to nap on) ------------
def opt_c(view):
    """A stout pale stem under a wide flat violet cap, padded and quilted like a futon
    with a rolled border and piping; gills under the front edge; a spore drifting."""
    fig = sk.Fig(W, H)
    f, fid = FACING[view], view == 'F'
    nod = 2 if fid else 0                       # nodding off: the cap sinks forward
    feet(fig, f, spread=4.4)
    sy, srx, sry = 46.0 + nod * 0.4, 8.6, 7.2 - nod * 0.4
    stem = fig.ellipse(CX, sy, srx, sry)
    round_form(fig, stem, 'plaster', CX, sy, srx, sry, lit=-0.45, dark=0.4)
    swap_clusters(fig, stem, 'plaster_cool', [(0, 0), (0, 1), (0, 2)], (4, 6), phase=1, min_t=2, max_t=3)
    top = min(p[1] for p in stem)
    if f == 0:
        arms = [(CX - 9.3, 47.5), (CX + 9.3, 47.5)]
    else:
        arms = [(mx(CX + 1.0, f), 48.0)]
    for ax, ay in arms:
        arm(fig, ax, ay, 'plaster_warm', 2.1, 2.7)
    # the cap: a wide flat disc seen from above, its underside (gills) under the front
    ccx, ccy, crx, cry = CX, top - 9.5 + nod, 17.0, 7.4
    disc = fig.ellipse(ccx, ccy, crx, cry)
    under = fig.ellipse(ccx, ccy + 2.8, crx - 1.5, cry - 0.6)
    gills = {p for p in under if p not in disc and p[1] <= top + 1}
    for (x, y) in gills:
        fig.put(x, y, 'dusk_cool', 1 if (x - CX) % 3 else 0)
    for x in range(CX - 6, CX + 7):       # the neck: gills run down into the stem
        for y in range(int(ccy + cry) - 1, top + 1):
            if (x, y) not in disc and (x, y) not in fig.px:
                fig.put(x, y, 'dusk_cool', 1 if (x - CX) % 3 else 0)
    round_form(fig, disc, 'dusk', ccx, ccy, crx, cry, lit=-0.35, dark=0.4, glint=False)

    def rad(x, y):
        u, v = (x + 0.5 - ccx) / crx, (y + 0.5 - ccy) / cry
        return (u * u + v * v) ** 0.5

    # padded bolster round the rim (warm sibling) and the seam inside it
    for (x, y) in disc:
        r, t = rad(x, y), fig.px[(x, y)][1]
        if r > 0.83:
            fig.put(x, y, 'dusk_warm', t)
        elif r > 0.73:
            fig.put(x, y, 'dusk_cool', max(1, min(t, 3) - 1))

    # quilting: diamond seams at slope 1/2 (runs of 2 px), each pillow lit on its top row
    # and dark on its bottom row; a tuft (dimple) where seams cross
    def seam(x, y):
        dx, dy = x - int(ccx), y - int(ccy)
        return (dx + 2 * dy) % 16 in (0, 1) or (dx - 2 * dy) % 16 in (14, 15)

    field = {p for p in disc if rad(*p) <= 0.73}
    for (x, y) in field:
        t = fig.px[(x, y)][1]
        if seam(x, y):
            fig.put(x, y, 'dusk_cool', max(1, min(t, 3) - 1))
        elif seam(x, y - 1) and rad(x, y - 1) <= 0.73:
            fig.put(x, y, 'dusk_warm', min(4, t + 1))
        elif seam(x, y + 1) and rad(x, y + 1) <= 0.73:
            fig.put(x, y, 'dusk', max(1, t - 1))
    # piping round the front lip
    for (x, y) in disc:
        if (x, y + 1) not in disc and abs(x + 0.5 - ccx) < crx - 4:
            t = 4 if x < ccx - 6 else 3 if x < ccx + 6 else 2
            fig.put(x, y, 'plaster_warm', t)
    despeckle(fig)
    for dx, dy in ((0, 0), (8, -4), (-8, -4), (8, 4), (-8, 4)):   # tufts where seams cross
        bx, by = int(ccx) + dx, int(ccy) + dy
        if (bx, by) in field and (bx + 1, by + 1) in field:
            for (x, y), t in (((bx, by), 1), ((bx + 1, by), 1), ((bx, by + 1), 4), ((bx + 1, by + 1), 3)):
                fig.put(x, y, 'dusk_cool' if t < 3 else 'dusk_warm', t)
    # face on the stem, in the cap's shade
    for x in range(CX - 8, CX + 9):
        if (x, top) in stem:
            fig.put(x, top, 'plaster', 1)
        if (x, top + 1) in stem:
            fig.put(x, top + 1, 'plaster', 2)
    ey = top + 3
    e1, e2 = eyes_at(f, CX)
    if fid:
        eye(fig, e1, ey, 'shut', 'plaster')
        eye(fig, e2, ey, 'shut', 'plaster')
        for (x, y) in ((CX - 1, ey + 4), (CX, ey + 4), (CX - 1, ey + 5), (CX, ey + 5)):
            fig.put(x, y, 'ink', 0)
    else:
        eye(fig, e1, ey, 'sleepy', 'plaster')
        eye(fig, e2, ey, 'sleepy', 'plaster')
        m0 = CX - 1 if f == 0 else (e2 - 1 if f > 0 else e1 + 1)
        fig.put(m0, ey + 4, 'plaster', 1)
        fig.put(m0 + 1, ey + 4, 'plaster', 1)
    cheeks(fig, f, e1, e2, ey + 3, 'plaster')
    fig.outline()
    if fid:
        spore(fig, CX - 15, top + 2)
        spore(fig, CX + 14, top + 4, horiz=False)
        spore(fig, CX - 12, top + 7, tone=3)
    else:
        spore(fig, mx(CX - 14, -1 if f > 0 else 1), top + 3, tone=3)
    return fig.image()


OPTIONS = [
    {
        'label': 'A', 'name': 'The cap is the nightcap', 'draw': opt_a,
        'question': "The mushroom's own cap is the nightcap: a soft violet felt dome whose crown runs up into a drooping tip with a pale pompom; its rolled margin is the cuff; the face sits on the pale stem in the cap's shade.",
        'palette': ['dusk', 'plaster', 'earth', 'berry'],
        'pose': 'Stands with its cap tipped a little forward and the tip hanging over one shoulder: already half asleep, perfectly content.',
        'parts': [
            'feet x2: earth, layer 1 (back), all facings (E/W far foot a px behind), attach foot',
            'stem body: plaster, layer 2, all facings, attach hip (breath squashes 1 px)',
            'near/far arm nubs: plaster_warm, layer 3 (far arm hidden E/W), all facings, attach chest',
            'face (eyes ink, cheeks berry, mouth): layer 4, S/E/W (none N), attach head',
            'gill band: dusk_cool, layer 4, S/E/W, attach head',
            'cap dome + rolled cuff: dusk, dusk_warm, layer 5, all facings, attach head',
            'cone tip: dusk, layer 6, always flops west (over the shoulder in S, behind in E, over the brow in W), attach head; swings 1 frame late in walk',
            'pompom: plaster_warm, layer 7, all facings, attach tip (secondary motion, settles last)',
        ],
        'notes': [
            'Works: one shape for cap and hat, so the silhouette is a single soft teardrop with a tail; the tip and pompom give walk and hop a follow-through.',
            'Risk: cone and pompom echo Mote (a star in a nightcap); here the cap is a dome on a stem with gills, the cuff is its own margin. The side arm is faint in E/W.',
            'Compared with Eastward-04 (Sam and the stall keepers, scaled to 34 px): head a third to half, 2 px eyes, 4 tones a material.',
        ],
    },
    {
        'label': 'B', 'name': 'Button head in a sock cap', 'draw': opt_b,
        'question': 'A tan button-mushroom head (the face on its lower half) wearing a separate knitted violet sock cap whose long tail flops over and hangs to one side; the mushroom ring is a frilled collar.',
        'palette': ['dusk', 'sand', 'plaster', 'earth', 'berry'],
        'pose': 'Wide awake eyes under a cap pulled down snug: a child sent to bed who is not sleepy yet.',
        'parts': [
            'feet x2: earth, layer 1, all facings, attach foot',
            'stem body: plaster, layer 2, all facings, attach hip',
            'ring collar (frill): plaster_warm, layer 3, all facings, attach chest (flutters on hop)',
            'arm nubs: plaster, layer 4, all facings, attach chest (one rubs an eye in the fidget)',
            'button head + gill lip: sand, sand_cool, layer 5, all facings, attach head (face S/E/W)',
            'sock cap crown + cuff: dusk, dusk_warm, layer 6, all facings, attach head',
            'tail (knit stripes): dusk, dusk_cool, layer 7, hangs E in S, flops behind in E/W',
            'pompom: plaster_warm, layer 8, attach tail end (swings, settles last)',
        ],
        'notes': [
            'Works: hat and head are separate, so the cap can slip, be pulled down for nap, or be tugged in fight cheer.',
            'Risk: a mushroom wearing a hat reads as a costume, closer to a generic toadstool kid; five families.',
            'Compared with Eastward-04 (Sam: a big pale hair mass over a small body) at the same height.',
        ],
    },
    {
        'label': 'C', 'name': 'Mat cap', 'draw': opt_c,
        'question': 'A stout pale stem under a wide flat violet cap quilted like a sleeping mat, piped round the rim; gills show under the front edge and a spore drifts from them.',
        'palette': ['dusk', 'plaster', 'earth', 'berry'],
        'glows': ['glowflora'],
        'pose': 'Squat and patient under its own bed, eyes heavy: it carries the soft spot with it.',
        'parts': [
            'feet x2: earth, layer 1, all facings, attach foot',
            'stout stem: plaster (+ cool fibres), layer 2, all facings, attach hip',
            'arm nubs: plaster_warm, layer 3, all facings, attach chest',
            'face: ink, berry, layer 4, S/E/W, attach head',
            'gills: dusk_cool, layer 5, S/E/W, attach head',
            'mat cap (quilt, piping, tuft button): dusk, dusk_warm, dusk_cool, plaster_warm, layer 6, all facings, attach head; tilts as a unit',
            'spores: glowflora glow, layer 7, effect (finite, reduced motion: none)',
        ],
        'notes': [
            'Works: the widest silhouette in the cast (a T), and the ritual and nap read at once: it lies down and the cap is the mat.',
            'Risk: the wide cap hides the arms in the S view at game scale and crowds props; quilting is fine detail.',
            'Compared with Eastward-04 stall awnings (quilted cloth, seams) and Sam for face scale.',
        ],
    },
]

VIEWS = [('S idle', 'S'), ('E idle', 'E'), ('W idle', 'W'), ('S fidget', 'F')]


# --- final: option C, the mat cap (revision round, 21 Oct) ------------------------------
# Small-folk cell raised to 56 x 72 for Puffcap: the familiar perches ON the flat cap top
# (24 art px over a cap that tops out 34 px above the foot), so the cell grows upwards.
import math  # noqa: E402

FW, FH = 56, 72
FFOOT = 66                      # foot anchor (28, 66): the outline's lowest row
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/puffcap-final.png')

CAP = dict(rx=14.5, ry=6.6)     # narrower than the round-1 disc (17): a mat, not a plate


def rot_ellipse(fig, cx, cy, rx, ry, ang):
    out = set()
    c, s = math.cos(ang), math.sin(ang)
    R = int(max(rx, ry)) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u, v = dx * c + dy * s, -dx * s + dy * c
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0 and fig.inside(x, y):
                out.add((x, y))
    return out


def limb(fig, a, b, fam='plaster_warm', r=2.0, body=None):
    """An arm nub as a short tube from shoulder a to hand b; the body next to it is the
    joint (a tone darker), the hand a round end lit at its upper left."""
    m = tube(fig, [(a[0], a[1], r * 0.85), (b[0], b[1], r)])
    for (x, y) in m:
        for q in ((x + 1, y), (x, y + 1)):
            if q not in m and q in fig.px and fig.px[q][0] != 'ink' and (body is None or q in body):
                fq, t = fig.px[q]
                fig.put(q[0], q[1], fq, max(1, min(t, 2)))
    edge_form(fig, m, fam, glint=False)
    return m


def mossling(fig, x, yb, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = fig.ellipse(x, yb - 5.0, 8.0, 5.0)
        round_form(fig, body, 'leaf', x, yb - 5.0, 8.0, 5.0, lit=-0.4, dark=0.4)
        swap_clusters(fig, body, 'leaf_warm', [(0, 0), (1, 0), (0, 1)], (4, 3), min_t=3, max_t=4)
        sprout_y = yb - 10
    else:
        body = fig.ellipse(x, yb - 8.0, 8.5, 8.0)
        round_form(fig, body, 'leaf', x, yb - 8.0, 8.5, 8.0, lit=-0.4, dark=0.4)
        swap_clusters(fig, body, 'leaf_warm', [(0, 0), (1, 0), (0, 1)], (4, 3), min_t=3, max_t=4)
        sprout_y = yb - 16
    for y in range(sprout_y - 3, sprout_y + 1):
        fig.put(x, y, 'grass', 3 if y < sprout_y else 2)
        fig.put(x + 1, y, 'grass', 2 if y < sprout_y else 1)
    lf = fig.ellipse(x - 2.0, sprout_y - 4.5, 2.6, 1.6)
    rf = fig.ellipse(x + 3.5, sprout_y - 3.5, 2.6, 1.6)
    edge_form(fig, lf, 'grass')
    edge_form(fig, rf, 'grass', glint=False)
    return body


def mossling_face(fig, x, yb, curled=False):
    if curled:
        ey = yb - 6
        for ex in (x - 4, x + 2):
            fig.put(ex, ey, 'ink', 0)
            fig.put(ex + 1, ey, 'ink', 0)
    else:
        ey = yb - 10
        for ex in (x - 4, x + 2):
            for dx in (0, 1):
                for dy in (0, 1):
                    fig.put(ex + dx, ey + dy, 'ink', 0)
            fig.put(ex, ey, 'leaf', 5)


def mat_cap(fig, ccx, ccy, ang, top_limit):
    """The cap: a padded, quilted mat in light dusk (tones 3 to 5 lead). A few bold diamond
    seams (2 rows thick) meet at tufts; the bolster rim is the cool sibling; plaster piping
    on the front lip; a lit gill fringe under it."""
    rx, ry = CAP['rx'], CAP['ry']
    c, s = math.cos(ang), math.sin(ang)
    disc = rot_ellipse(fig, ccx, ccy, rx, ry, ang)
    under = rot_ellipse(fig, ccx - s * 2.6, ccy + c * 2.6, rx - 1.6, ry - 0.8, ang)
    gills = {p for p in under if p not in disc and p[1] <= top_limit + 1}
    for (x, y) in gills:
        lip = (x, y - 1) in disc
        fig.put(x, y, 'dusk_cool', 3 if lip and x < ccx + 4 else 2 if lip else (1 if (x - int(ccx)) % 3 else 0))

    def loc(x, y):
        dx, dy = x + 0.5 - ccx, y + 0.5 - ccy
        return dx * c + dy * s, -dx * s + dy * c

    # light dusk: body 4, lit cap 5 at the upper left, the lower right 3, the underside 2
    for (x, y) in disc:
        u, v = (x + 0.5 - ccx) / rx, (y + 0.5 - ccy) / ry
        n = 0.6 * u + 0.8 * v
        t = 5 if n < -0.62 else 3 if n > 0.42 else 4
        fig.put(x, y, 'dusk_warm', t)
    for (x, y) in disc:
        if (x, y + 1) not in disc:
            fig.put(x, y, 'dusk_warm', 2 if x > ccx - 4 else 3)

    def rad(x, y):
        lu, lv = loc(x, y)
        return ((lu / rx) ** 2 + (lv / ry) ** 2) ** 0.5

    for (x, y) in disc:                       # the bolster round the rim
        r = rad(x, y)
        t = fig.px[(x, y)][1]
        if 0.80 < r <= 0.87 and t >= 3:
            fig.put(x, y, 'dusk', t - 1)          # its seam, a recess
        elif r > 0.87 and (x, y + 1) in disc:
            fig.put(x, y, 'dusk', t)

    # quilting: one bold diamond pillow in the middle, a half pillow each side; seams two
    # px thick in dusk 3 (a recess), tufts at the four points, the pillows' upper-left lit
    pts = [(-8.5, 0.0), (0.0, -3.6), (8.5, 0.0), (0.0, 3.6)]
    segs = [(pts[i], pts[(i + 1) % 4]) for i in range(4)] + [((-8.5, 0.0), (-13.0, 0.0)),
                                                              ((8.5, 0.0), (13.0, 0.0))]

    def dist(px_, py_, a_, b_):
        (x0, y0), (x1, y1) = a_, b_
        vx, vy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((px_ - x0) * vx + (py_ - y0) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px_ - x0 - t * vx, (py_ - y0 - t * vy) * 1.6)

    field = {p for p in disc if rad(*p) <= 0.80}
    seams = set()
    for (x, y) in field:
        lu, lv = loc(x, y)
        if min(dist(lu, lv, a_, b_) for a_, b_ in segs) <= 1.05:
            seams.add((x, y))
    for (x, y) in field:
        t = fig.px[(x, y)][1]
        if (x, y) in seams:
            fig.put(x, y, 'dusk', 3 if t >= 4 else 2)
        elif (x, y - 1) in seams and t >= 4:
            fig.put(x, y, 'dusk_warm', 5)         # a pillow's lit lip under the seam
        elif (x, y + 1) in seams and t <= 4:
            fig.put(x, y, 'dusk_warm', 3)         # its shaded bottom row
    for tx, ty in pts:                         # tufts: a 2 x 2 dimple, dark over lit
        best = min(field, key=lambda p: (loc(*p)[0] - tx) ** 2 + (loc(*p)[1] - ty) ** 2)
        x, y = best
        fig.put(x, y, 'dusk_cool', 1)
        fig.put(x + 1, y, 'dusk_cool', 1)
        fig.put(x, y + 1, 'dusk_cool', 2)
        fig.put(x + 1, y + 1, 'dusk_cool', 2)
    for (x, y) in disc:                       # piping on the front lip
        lu, lv = loc(x, y)
        if (x, y + 1) not in disc and abs(lu) < rx - 3.5:
            t = 4 if lu < -5 else 3 if lu < 5 else 2
            fig.put(x, y, 'plaster_warm', t)
    return disc


# Poses are written facing east (forward = +x); W reflects the geometry about the anchor and
# is shaded again with the light still at the upper left. S poses give both arms.
POSES = {
    'S idle':    dict(f=0),
    'E idle':    dict(f=1),
    'W idle':    dict(f=-1),
    'S fidget':  dict(f=0, nod=2, eyes='shut', mouth='o', arms='droop',
                      spores=[(-13, -2, 4), (12, 0, 4), (-10, 3, 3)]),
    'E ready':   dict(f=1, dy=1, eyes='open', arms=[((3, -1), (8, 0)), ((-2, -1), (-6, 2))], fam=-5),
    'E strike':  dict(f=1, bdx=3, cdx=3, cdy=1, ang=0.14, eyes='open', mouth='line',
                      arms=[((3, -1), (13, -2)), ((-2, 0), (-8, 2))], fam=-5,
                      spores=[(15, -4, 4), (16, 0, 4)]),
    'E cast':    dict(f=1, eyes='shut', mouth='o',
                      arms=[((3, -2), (9, -5)), ((1, -1), (7, -3))], fam=-5,
                      spores=[(12, -6, 4), (15, -2, 4), (13, 2, 3)]),
    'E hit':     dict(f=1, bdx=-2, cdx=-4, cdy=-1, ang=-0.16, eyes='squeeze', mouth='o',
                      arms=[((1, -1), (-4, -6)), ((-2, 0), (-8, -2))], fam=-5),
    'E sit':     dict(f=1, sit=True, dy=3, cdy=4, eyes='shut', arms=[((2, 0), (6, 2))], fam=-5),
    'E cheer':   dict(f=1, hop=4, eyes='squeeze', mouth='open',
                      arms=[((3, -2), (11, -7)), ((-3, -2), (-11, -7))], arms_front=True, fam=-5),
    'W ready':   dict(f=-1, dy=1, eyes='open', arms=[((3, -1), (8, 0)), ((-2, -1), (-6, 2))], fam=-5),
    'W strike':  dict(f=-1, bdx=3, cdx=3, cdy=1, ang=0.14, eyes='open', mouth='line',
                      arms=[((3, -1), (13, -2)), ((-2, 0), (-8, 2))], fam=-5,
                      spores=[(15, -4, 4), (16, 0, 4)]),
}

PERCH = {}


def puff_final(name):
    P = POSES[name]
    f = P['f']
    g = 1 if f >= 0 else -1
    fig = sk.Fig(FW, FH)
    lift = P.get('hop', 0)
    bdx, dy = P.get('bdx', 0), P.get('dy', 0) - lift
    X = lambda lx: CX + g * (bdx + lx)          # noqa: E731  (body-local x, forward +)
    nod = P.get('nod', 0)
    # feet
    fy = FFOOT - 1.8 - lift
    if P.get('sit'):
        fpts = [(X(5), FFOOT - 1.8), (X(9), FFOOT - 2.3)]
    elif f == 0:
        fpts = [(CX - 4.4, fy), (CX + 4.4, fy)]
    else:
        fpts = [(X(-2.5), fy - 0.8), (X(2.5), fy)]
    for fx_, fy_ in fpts:
        edge_form(fig, fig.ellipse(fx_, fy_, 2.8, 1.8), 'earth', glint=False)
    # stem
    sry = 8.4 - nod * 0.4 - (1.2 if P.get('sit') else 0)
    scy = FFOOT - 2.6 - sry + dy * (0 if P.get('sit') else 1) + nod * 0.4
    if P.get('sit'):
        scy = FFOOT - 1.5 - sry
    scx = X(0) if f else CX
    srx = 9.0
    # far arm behind the body
    arms = P.get('arms')
    if arms == 'droop' or (arms is None and f == 0):
        drop = 2 if arms == 'droop' else 0
        arms_s = [((-6, -1), (-10.5, 2 + drop)), ((6, -1), (10.5, 2 + drop))]
    else:
        arms_s = None
    if arms is None and f != 0:
        arms = [((1, 0), (3, 3)), ((-1, 0), (-3, 3))]
    if f != 0 and len(arms) > 1 and not P.get('arms_front'):
        (a, b) = arms[1]
        limb(fig, (X(a[0]), scy + a[1]), (X(b[0]), scy + b[1]))
    stem = fig.ellipse(scx, scy, srx, sry)
    # profile: the face side is a step (cheek and muzzle bulge), lit from the upper left
    cheek = set()
    if f != 0:
        cheek = fig.ellipse(X(6.8), scy - 0.5, 3.4, 3.2)
        stem |= cheek
    round_form(fig, stem, 'plaster', scx, scy, srx, sry, lit=-0.45, dark=0.4)
    swap_clusters(fig, stem, 'plaster_cool', [(0, 0), (0, 1), (0, 2)], (4, 6), phase=1, min_t=2, max_t=3)
    if cheek:
        for (x, y) in cheek:
            if (x, y) not in fig.ellipse(scx, scy, srx, sry):
                up = (x, y - 1) not in stem
                fig.put(x, y, 'plaster', 4 if up and g > 0 and x < X(7) else 4 if g < 0 and x < X(6) - 0 else 3)
        # the step under the cheek (a recess back to the body)
        for (x, y) in cheek:
            if (x, y + 1) not in cheek and (x, y + 1) in stem:
                fig.put(x, y + 1, 'plaster', 2)
    top = min(p[1] for p in stem)
    if arms_s and f == 0:
        for a, b in arms_s:
            limb(fig, (CX + a[0], scy + a[1]), (CX + b[0], scy + b[1]), body=stem)
    elif f != 0 and not P.get('arms_front'):
        a, b = arms[0]
        limb(fig, (X(a[0]), scy + a[1]), (X(b[0]), scy + b[1]), body=stem)
    # the neck (gills run down into the stem) and the cap
    ccx = (X(0) if f else CX) + g * P.get('cdx', 0)
    ccy = top - 6.0 - 0.6 + P.get('cdy', 0) + (nod if nod else 0)
    for x in range(int(scx) - 6, int(scx) + 7):
        for y in range(int(ccy + CAP['ry']) - 1, top + 1):
            if (x, y) not in fig.px:
                fig.put(x, y, 'dusk_cool', 1 if (x - CX) % 3 else 0)
    disc = mat_cap(fig, ccx, ccy, g * P.get('ang', 0.0), top)
    if P.get('arms_front'):
        for a, b in arms:
            limb(fig, (X(a[0]), scy + a[1]), (X(b[0]), scy + b[1]))
    # the familiar on the flat cap top, at the shoulder away from the foe
    fam_xy = None
    if P.get('fam') is not None:
        px_ = int(round(ccx + g * P['fam']))
        col = [y for (x, y) in disc if x == px_]
        yb = min(col) + 2 if col else int(ccy - CAP['ry']) + 2
        mbody = mossling(fig, px_, yb)
        for (x, y) in disc:                    # contact shade on the cap under it
            if (x, y - 1) in mbody and (x, y) not in mbody:
                fig.put(x, y, 'dusk', 2)
        fam_xy = [px_, yb]
    despeckle(fig)
    # face: brow in the cap's shade, big 2 x 2 eyes under a heavy lid, cheeks, mouth
    for x in range(int(scx) - 9, int(scx) + 10):
        if (x, top) in stem and (x, top) not in cheek:
            fig.put(x, top, 'plaster', 1)
        if (x, top + 1) in stem and (x, top + 1) not in cheek:
            fig.put(x, top + 1, 'plaster', 2)
    ey = top + 3
    kind = P.get('eyes', 'sleepy')
    if f == 0:
        eps = [CX - 5, CX + 3]
    else:
        eps = [X(4) if g > 0 else X(4) - 1]
    for ex in eps:
        eye(fig, ex, ey, kind, 'plaster')
    if f != 0:
        # brow ridge over the eye, lit on top; the far eye shows as a lid sliver
        fx = X(7) if g > 0 else X(7) - 1
        fig.put(fx, ey, 'ink', 0)
        fig.put(fx, ey + 1, 'ink', 0)
    mo = P.get('mouth', 'small')
    mx0 = CX - 1 if f == 0 else (X(6) if g > 0 else X(6) - 1)
    my = ey + 4
    if mo == 'small':
        fig.put(mx0, my, 'plaster', 1)
        fig.put(mx0 + 1, my, 'plaster', 1)
    elif mo == 'line':
        for k in range(3):
            fig.put(mx0 - (1 if g > 0 else 0) + k, my, 'plaster', 0)
    elif mo == 'o':
        for (x, y) in ((mx0, my), (mx0 + 1, my), (mx0, my + 1), (mx0 + 1, my + 1)):
            fig.put(x, y, 'ink', 0)
    elif mo == 'open':
        for (x, y) in fig.rect(mx0 - 1, my - 1, mx0 + 2, my + 2, knock=1):
            fig.put(x, y, 'ink', 0)
        fig.put(mx0, my + 2, 'berry', 3)
        fig.put(mx0 + 1, my + 2, 'berry', 2)
    if f == 0:
        for x, t in ((CX - 8, 4), (CX - 7, 4), (CX + 6, 3), (CX + 7, 3)):
            put_on(fig, x, ey + 3, 'berry', t, on='plaster')
    else:
        bx = X(5) if g > 0 else X(5) - 1
        put_on(fig, bx, ey + 3, 'berry', 3 if g > 0 else 4, on='plaster')
        put_on(fig, bx - g, ey + 3, 'berry', 3 if g > 0 else 4, on='plaster')
    if fam_xy:
        mossling_face(fig, *fam_xy)
    fig.outline()
    for sx_, sy_, t in P.get('spores', []):
        spore(fig, int(X(sx_) if f else CX + sx_), int(scy + sy_), horiz=(sy_ % 2 == 0), tone=t)
    if fam_xy:
        PERCH[name] = fam_xy
    return fig.image()


def puff_nap():
    """nap_c: lying on its side under the tipped cap like a blanket, the face peeking out
    at the west end, the familiar curled up on top of the cap."""
    fig = sk.Fig(FW, FH)
    by = FFOOT - 5.0
    body = fig.ellipse(CX - 4, by, 11.0, 4.8)
    round_form(fig, body, 'plaster', CX - 4, by, 11.0, 4.8, lit=-0.45, dark=0.4)
    swap_clusters(fig, body, 'plaster_cool', [(0, 0), (1, 0), (2, 0)], (6, 3), phase=1, min_t=2, max_t=3)
    # feet poke out at the east end
    for fx_, fy_ in ((CX + 7.5, FFOOT - 2.4), (CX + 8.5, FFOOT - 5.4)):
        edge_form(fig, fig.ellipse(fx_, fy_, 2.2, 1.6), 'earth', glint=False)
    # the cap pulled over as a blanket (tipped on edge, its quilted top towards us)
    cx_, cy_ = CX + 6.0, by - 3.0
    disc = mat_cap(fig, cx_, cy_, -0.08, 99)
    # a hand holding the blanket's edge
    limb(fig, (CX - 6, by + 1), (CX - 4.5, by - 3), body=body)
    fx = int(cx_) + 3
    col = [y for (x, y) in disc if x == fx]
    yb = min(col) + 2
    mb = mossling(fig, fx, yb, curled=True)
    for (x, y) in disc:
        if (x, y - 1) in mb and (x, y) not in mb:
            fig.put(x, y, 'dusk', 2)
    despeckle(fig)
    # face at the west end: shut eyes, a cheek, a tiny open mouth
    eye(fig, CX - 12, int(by) - 1, 'shut', 'plaster')
    put_on(fig, CX - 13, int(by) + 1, 'berry', 4, on='plaster')
    put_on(fig, CX - 12, int(by) + 1, 'berry', 4, on='plaster')
    fig.put(CX - 10, int(by) + 2, 'plaster', 1)
    fig.put(CX - 9, int(by) + 2, 'plaster', 1)
    mossling_face(fig, fx, yb, curled=True)
    fig.outline()
    PERCH['nap S'] = [fx, yb]
    return fig.image()


FINAL_VIEWS = ['S idle', 'E idle', 'W idle', 'S fidget', 'nap S', 'E ready', 'E strike', 'E cast',
               'E hit', 'E sit', 'E cheer', 'W ready', 'W strike']

FINAL = {
    'label': 'C final', 'name': 'Mat cap (final)', 'chosen': 'C',
    'grafts': [
        'From B: a bigger, clearer face (2 x 2 eyes under a heavy lid, 8 px apart in S; a brow in the cap shade) and, in profile, a cheek and muzzle step lit from the upper left',
        'From B: arm nubs that reach past the stem and show below the brim in S and in every fight pose',
        'From the graders: quilting as a few bold diamond seams (2 rows thick) meeting at 2 x 2 tufts, no fine lines; a lit gill fringe under the brim; stem fibres as cool vertical streaks',
        'Cast-wide: cap in light dusk (dusk_warm, tones 3 to 5 lead), narrower (29 px) so it reads as a mat, not a plate',
        'Perch on the cap top; small-folk cell for Puffcap raised to 56 x 72 (foot 28, 66)',
    ],
    'palette': ['dusk', 'plaster', 'earth', 'berry'],
    'glows': ['glowflora (spores: finite, off under reduced motion)'],
    'familiar_standin': ['leaf', 'grass'],
    'pose': 'Squat and patient under its own bed, eyes heavy: it carries the soft spot with it, and its friend rides on top.',
    'parts': [
        'feet x2: earth, layer 1, anchor foot; S side by side, E/W far foot a px higher; sit: both forward',
        'far arm: plaster_warm, layer 2 (behind the stem), anchor chest; E/W only',
        'stem body + fibres: plaster, plaster_cool, layer 3, anchor hip; breath squashes 1 px',
        'cheek/muzzle step: plaster, layer 4, anchor head; E/W only (on the facing side)',
        'near arm (S: both): plaster_warm, layer 5, anchor chest; cheer: in front of the brim',
        'face (eyes ink, lid, brow, cheeks berry, mouth): layer 6, anchor head; S/E/W, none in N',
        'gill fringe + neck: dusk_cool, layer 7, anchor head; S/E/W',
        'mat cap (quilt, tufts, bolster, piping): dusk_warm, dusk, dusk_cool, plaster_warm, layer 8, anchor head; one rigid part that tilts (strike forward, hit back) and sinks (nod, sit); nap: pulled over as a blanket',
        'familiar perch: on the cap top at its back half (E: x smaller, W: x larger), layer 9, rides the cap',
        'spores: glowflora glow, layer 10, effect (fidget, cast, strike impact); finite, none under reduced motion',
    ],
    'notes': [
        'Cell: Puffcap needs 56 x 72 (foot 28, 66), not 56 x 60: the familiar sits on the flat cap top, which is 34 px above the foot.',
        'Compared side by side with Eastward-04 (Sam, the fishmonger, scaled to the same height): head mass a third to half, 2 px eyes with a glint, 4-5 tones a material, quilted awnings for the cap seams.',
        'Risk: raised arms meet the brim, so cast keeps the hands forward under it and cheer draws the arms in front of the brim.',
        'Open: the spores are the only effect; the select screen should check the cap against Velvet (deep dusk) side by side.',
    ],
}


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    sheet_opts, data = [], []
    for o in OPTIONS:
        views, nums = [], {}
        for cap, v in VIEWS:
            im = o['draw'](v)
            views.append((cap, im))
            im.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(im)
            nums[cap] = {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}
            print(f"{o['label']} {cap:9s} on house {100 * m['on_house']:.0f}%  W-E {m['west_east']:+.1f}  "
                  f"lone {100 * m['isolated']:.1f}%  colours {m['colours']}  "
                  f"outline dark {100 * m.get('outline_dark', 0):.0f}%")
        sheet_opts.append({k: o[k] for k in ('label', 'name', 'parts', 'palette', 'pose', 'notes')}
                          | {'views': views})
        data.append({k: o[k] for k in ('label', 'name', 'question', 'parts', 'palette', 'pose', 'notes')}
                    | {'glows': o.get('glows', []), 'measure': nums})
    sk.design_sheet('Puffcap (puffcap): what the cap is and how the body sits under it', sheet_opts, OUT_PNG,
                    note='Starter, Soother (Drowsy). 34 art px, cell 56 x 60, foot (28, 54). Light upper left in every view.')
    # the final sheet (option C, revision round)
    fviews, fnums = [], {}
    for v in FINAL_VIEWS:
        im = puff_nap() if v == 'nap S' else puff_final(v)
        fviews.append((v, im))
        im.save(os.path.join(SCRATCH, f"final-{v.replace(' ', '-')}.png"))
        m = sk.measure(im)
        fnums[v] = {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}
        a = im.getchannel('A').getbbox()
        fnums[v]['bbox'] = list(a)
        print(f"final {v:9s} on house {100 * m['on_house']:.0f}%  W-E {m['west_east']:+.1f}  "
              f"lone {100 * m['isolated']:.1f}%  colours {m['colours']}  "
              f"outline dark {100 * m.get('outline_dark', 0):.0f}%  bbox {a}")
    sk.design_sheet('Puffcap final: C, the mat cap', [
        {'label': FINAL['label'], 'name': FINAL['name'], 'views': fviews, 'parts': FINAL['parts'],
         'palette': FINAL['palette'], 'pose': FINAL['pose'], 'notes': FINAL['notes']}], OUT_FINAL,
        note='Cell 56 x 72, foot (28, 66): the familiar (stand-in Mossling) perches on the cap top. Light upper left in every view.')
    final = {k: FINAL[k] for k in ('chosen', 'grafts', 'parts', 'palette', 'glows', 'familiar_standin',
                                    'pose', 'notes')}
    final.update({'cell': [FW, FH], 'foot': [CX, FFOOT], 'height_art_px': 34,
                  'perch': {k: v for k, v in PERCH.items()}, 'measure': fnums})
    with open(OUT_JSON, 'w') as fh:
        json.dump({'id': 'puffcap', 'height_art_px': 34, 'cell': [W, H], 'foot': [CX, FOOT],
                   'options': data, 'final': final}, fh, indent=2)
    print('wrote', OUT_PNG, OUT_FINAL)


if __name__ == '__main__':
    main()
