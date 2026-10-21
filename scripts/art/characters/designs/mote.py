"""Mote, a star of Dream Dust in a nightcap: three design options (Claude J lane, batch 3).

Main question: how a star becomes a character.

    A  Plump star: a five-pointed cushion star with the face in the middle, the nightcap
       on the top point, the two side points as stubby arms and the two lower points as
       dangling feet; a lamp core glows under the face.
    B  Dust-ball: a round ball of Dream Dust with four short star rays round it (two as
       hands, two as toes) and a long regolith nightcap trailing over its back to the
       pompom at its heel; the ball glows from inside.
    C  Star-sprite: a star-shaped head (its lower points fall over the shoulders like a
       collar) on a tiny slate nightgown that tapers into a glowing wisp of dust, the cap
       standing up from the head's top point.

Mote floats: every view hovers 6 art px over the foot anchor (the renderer adds the
shadow; none is drawn here). Views: S, E, W idle (W drawn with its own light, not
mirrored pixels) and the S key pose of its fidget. Design sheets are review material;
production frames come from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<scratch>/designs python3 scripts/art/characters/designs/mote.py
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/mote-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/mote.json')
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/mote-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'mote')

W, H = 56, 60
AX, AY = 28, 54          # foot anchor (the ground point under the hovering star)
HOVER = 6
LOW = AY - HOVER         # the lowest outline row (48); the lowest fill row is LOW - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour (deterministic tie-break), unless it is an eye, a glint or a mote (`keep`)."""
    for _ in range(2):
        changes = {}
        for p in sorted(fig.px):
            v = fig.px[p]
            if p in keep or p in fig.fixed or v[0] == 'ink':
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if v[0] in ('_edge', '_lit'):
                # an outline pixel shut in between two parts is a seam, not an edge: it
                # takes the part tone (joints stay dark through the parts' own tones)
                if sum(1 for n in nb if n[0] not in ('ink', '_edge', '_lit')) < 3:
                    continue
            if all(n != v for n in nb):
                pool = [n for n in nb if n[0] not in ('ink', '_edge', '_lit')]
                if not pool:
                    continue
                changes[p] = max(sorted(set(pool), key=str), key=pool.count)
        for p, v in changes.items():
            fig.px[p] = v


def disc(cx, cy, r):
    out = set()
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r and 0 <= x < W and 0 <= y < H:
                out.add((x, y))
    return out


def ell(cx, cy, rx, ry):
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0 and 0 <= x < W and 0 <= y < H:
                out.add((x, y))
    return out


def polar(cx, cy, a, d, sx=1.0):
    r = math.radians(a)
    return cx + sx * d * math.sin(r), cy - d * math.cos(r)


def star(fig, cx, cy, tips, ri, sx=1.0):
    """A plump star: `tips` are (angle clockwise from up, length, tip radius). The points
    are rounded by a disc at each tip and joined by a polygon through the inner radius."""
    tips = sorted(tips)
    pts = []
    m = set()
    for i, (a, L, tr) in enumerate(tips):
        a2 = tips[(i + 1) % len(tips)][0] + (360 if i == len(tips) - 1 else 0)
        pts.append(polar(cx, cy, a, L - tr * 0.6, sx))
        pts.append(polar(cx, cy, (a + a2) / 2, ri, sx))
        tx, ty = polar(cx, cy, a, L - tr, sx)
        m |= disc(tx, ty, tr)
    m |= fig.poly(pts)
    m |= ell(cx, cy, (ri + 0.6) * sx, ri + 0.6)
    return m


def form(fig, mask, fam, cx, cy, R, cap=0.36, cres=1.0, glint=True, sib=True):
    """A soft round form lit from the upper left: a warm lit cap (tone 4) offset to the
    upper left, the body, a cool crescent (2) round the lower right that follows the form,
    undersides 1. Rims facing up or left catch the light; rims facing right sit a tone
    down. Points of a star take the same rule, so the upper-left point is lit and the
    lower-right ones fall into shade."""
    mask = set(mask)
    wf, cf = (fam + '_warm', fam + '_cool') if sib else (fam, fam)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / R, (y + 0.5 - cy) / R
        t = 3
        if (u + 0.36) ** 2 + (v + 0.42) ** 2 < cap:
            t = 4
        if (u + 0.30) ** 2 + (v + 0.36) ** 2 > cres:
            t = 2
        up_open = (x, y - 1) not in mask
        left_open = (x - 1, y) not in mask
        if (up_open or left_open) and t == 3 and (u < 0.35 or up_open and v < -0.2):
            t = 4
        if (x + 1, y) not in mask and t >= 3 and u > 0.1:
            t = 2
        if (x, y + 1) not in mask and v > 0.1:
            t = 1 if u > -0.35 else 2
        f = wf if t >= 4 else cf if t <= 2 else fam
        fig.put(x, y, f, t)
    if glint:
        top = sorted(mask, key=lambda p: ((p[0] - cx) * 0.55 + (p[1] - cy) * 0.85, p))
        for p in top[:2]:
            fig.put(p[0], p[1], wf, 5)
    return mask


def dust(fig, mask, fam, seed=0):
    """Dream Dust in the body: a few 2 px dominoes one sibling over at the same tone
    (shape without value noise), only in the lit and body tones."""
    pts = sorted(mask)
    k = 0
    for i, (x, y) in enumerate(pts):
        if (x * 7 + y * 13 + seed) % 37 == 0 and (x + 1, y) in mask:
            f, t = fig.px.get((x, y), (None, None))
            f2, t2 = fig.px.get((x + 1, y), (None, None))
            if f and t in (3, 4) and t2 == t and sk.family_of(f) == fam:
                nf = fam + '_warm' if t == 3 else fam
                fig.put(x, y, nf, t)
                fig.put(x + 1, y, nf, t)
                k += 1
    return k


def core(fig, cx, cy, rx=2.6, ry=1.8):
    """The star's inner light (a glow, never a lit surface): a pale lamp halo, a bright
    centre. Glows take no outline."""
    m = ell(cx, cy, rx, ry)
    for (x, y) in sorted(m):
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 5 if u * u + v * v < 0.35 else 4
        fig.glow(x, y, 'lamp', t)
    return m


def mote_px(fig, x, y, horiz=True, t=5):
    """One Dream Dust mote: a finite 2 px glint (a glow, unoutlined)."""
    fig.glow(x, y, 'lamp', t)
    if horiz:
        fig.glow(x + 1, y, 'lamp', t - 1)
    else:
        fig.glow(x, y + 1, 'lamp', t - 1)
    return {(x, y), (x + 1, y) if horiz else (x, y + 1)}


def pompom(fig, cx, cy, r, fam):
    m = disc(cx, cy, r)
    form(fig, m, fam, cx, cy, r, cap=0.45, cres=1.05, glint=False)
    # fluff: a lit 2 px tuft at its upper left
    xs = sorted(m)
    fig.put(xs[1][0], xs[1][1], fam + '_warm', 5)
    return m


def cap_cloth(fig, mask, fam, stripe=None, stripes=(), folds=(), lean=1):
    """The nightcap as soft cloth: lit on the upper left (warm, 4), body 3, the lower right
    and the inside of the flop in cool 2, undersides 1; `stripes` are column or row bands
    in a second family on the same tones; `folds` are 2 px recesses (tone 2)."""
    mask = set(mask)
    for (x, y) in sorted(mask):
        up = (x, y - 1) not in mask
        left = (x - 1, y) not in mask
        down = (x, y + 1) not in mask
        right = (x + 1, y) not in mask
        t = 3
        if up or left:
            t = 4
        if right and not up:
            t = 2
        if down:
            t = 1 if not left else 2
        f = fam
        if stripe and any(s(x, y) for s in stripes):
            f = stripe
        sib = f + ('_warm' if t >= 4 else '_cool' if t <= 2 else '')
        fig.put(x, y, sib, t)
    for (fx, fy0, fy1) in folds:
        for y in range(fy0, fy1 + 1):
            if (fx, y) in mask and (fx, y + 1) in mask:
                f = sk.family_of(fig.px[(fx, y)][0])
                fig.put(fx, y, f + '_cool', 2)
    return mask


def cuff(fig, mask, fam):
    """The turned-up cuff: a lit top row, body, a dark bottom row; ribbed every 2 px."""
    mask = set(mask)
    rows = sorted({y for _, y in mask})
    for (x, y) in sorted(mask):
        xs = [p[0] for p in mask if p[1] == y]
        t = 3
        if y == rows[0] or x == min(xs):
            t = 4
        if y == rows[-1] or x == max(xs):
            t = 2
        if y == rows[-1] and x > (min(xs) + max(xs)) / 2:
            t = 1
        f = fam + ('_warm' if t >= 4 else '_cool' if t <= 2 else '')
        fig.put(x, y, f, t)
    return mask


def eye(fig, x, y, keep, h=3, w=2, shape='open', lid_fam='plaster'):
    """An ink eye with a glint at its upper left; 'shut' is a lit lid curve (tone 1 of the
    skin, not ink); 'sleepy' trades the top row for a lid."""
    if shape == 'shut':
        fig.put(x, y + 1, lid_fam + '_cool', 1)
        fig.put(x + 1, y + 1, lid_fam + '_cool', 1)
        if w > 2:
            fig.put(x + 2, y + 1, lid_fam + '_cool', 1)
        keep |= {(x, y + 1), (x + 1, y + 1)}
        return
    if shape == 'happy':
        fig.put(x, y + 1, lid_fam + '_cool', 1)
        fig.put(x + 1, y, lid_fam + '_cool', 1)
        fig.put(x + 2, y + 1, lid_fam + '_cool', 1)
        keep |= {(x, y + 1), (x + 1, y), (x + 2, y + 1)}
        return
    for j in range(h):
        for i in range(w):
            fig.put(x + i, y + j, 'ink', 0)
            keep.add((x + i, y + j))
    if shape == 'sleepy':
        for i in range(w):
            fig.put(x + i, y, lid_fam + '_cool', 2)
    gy = y + (1 if shape == 'sleepy' else 0)
    fig.put(x, gy, 'snow', 5)
    keep.add((x, gy))


def blush(fig, x, y, keep):
    fig.put(x, y, 'berry_warm', 5)
    fig.put(x + 1, y, 'berry_warm', 5)
    keep |= {(x, y), (x + 1, y)}


def finish(fig, keep):
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- the nightcap: a soft tapering tube ----------------------------------------------
def bezier(pts, n=64):
    out = []
    for i in range(n + 1):
        t = i / n
        if len(pts) == 3:
            (a, b, c) = pts
            x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0]
            y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]
        else:
            (a, b, c, d) = pts
            x = (1 - t) ** 3 * a[0] + 3 * (1 - t) ** 2 * t * b[0] + 3 * (1 - t) * t * t * c[0] + t ** 3 * d[0]
            y = (1 - t) ** 3 * a[1] + 3 * (1 - t) ** 2 * t * b[1] + 3 * (1 - t) * t * t * c[1] + t ** 3 * d[1]
        out.append((x, y, t))
    return out


def tube(ctrl, r0, r1, ease=1.0):
    """A cone of cloth along a Bezier axis, radius r0 at the cuff tapering to r1 at the tip.
    Returns {pixel: (t along the axis, u, v)}, (u, v) the pixel's normal off the axis."""
    samples = bezier(ctrl)
    out = {}
    xs = [s[0] for s in samples]
    ys = [s[1] for s in samples]
    for y in range(int(min(ys) - r0) - 1, int(max(ys) + r0) + 2):
        for x in range(int(min(xs) - r0) - 1, int(max(xs) + r0) + 2):
            best = None
            for (sx_, sy_, t) in samples:
                r = r0 + (r1 - r0) * (t ** ease)
                dx, dy = x + 0.5 - sx_, y + 0.5 - sy_
                q = math.hypot(dx, dy) / r
                if q <= 1.0 and (best is None or q < best[0]):
                    best = (q, t, dx / r, dy / r)
            if best and 0 <= x < W and 0 <= y < H:
                out[(x, y)] = best[1:]
    return out


def cap_tube(fig, ctrl, r0, r1, fam, stripe=None, bands=(), ease=1.0, keep_out=frozenset(), floor=None):
    """The cone shaded as a soft cylinder lit from the upper left: the lit side (warm 4),
    the body 3, the side away from the light (cool 2), its far edge 1; stripes are bands
    across the axis in a second family on the same tones. Pixels in `keep_out` stay."""
    tb = tube(ctrl, r0, r1, ease)
    if floor is not None:
        # the cone ends at the cuff: nothing of its first half hangs below the cuff line
        tb = {p: v for p, v in tb.items() if not (p[1] > floor and v[0] < 0.5)}
    for p in sorted(tb):
        if p in keep_out:
            continue
        t, u, v = tb[p]
        n = 0.55 * u + 0.85 * v
        tn = 3
        if n < -0.3:
            tn = 4
        if n > 0.35:
            tn = 2
        if n > 0.8:
            tn = 1
        f = fam
        if stripe and any(a <= t < b for a, b in bands):
            f = stripe
        fig.put(p[0], p[1], f + ('_warm' if tn >= 4 else '_cool' if tn <= 2 else ''), tn)
    # glint: two px on the lit crest near the cuff
    lit = sorted((p for p in tb if p not in keep_out and tb[p][0] < 0.4),
                 key=lambda p: (0.55 * tb[p][1] + 0.85 * tb[p][2], p))
    for p in lit[:2]:
        f = sk.family_of(fig.px[p][0])
        fig.put(p[0], p[1], f + '_warm', 5)
    return set(tb), bezier(ctrl)[-1]


def band(fig, cx, cy, rx, ry, fam):
    """The turned-up cuff, an elliptic band: lit top row and west end, dark bottom row and
    east end, ribbed every 2 px on the body."""
    m = ell(cx, cy, rx, ry)
    rows = {}
    for (x, y) in m:
        rows.setdefault(y, []).append(x)
    top, bot = min(rows), max(rows)
    for (x, y) in sorted(m):
        xl, xr = min(rows[y]), max(rows[y])
        t = 3
        if y == top or x == xl:
            t = 4
        if x == xr or (y == bot and x > cx):
            t = 2
        if y == bot and x > cx + rx * 0.3:
            t = 1
        if t == 3 and (x - int(cx)) % 3 == 2 and y != top:
            t = 2   # rib
        fig.put(x, y, fam + ('_warm' if t >= 4 else '_cool' if t <= 2 else ''), t)
    return m


# =====================================================================================
# A  Plump star
# =====================================================================================
A_CX, A_CY = 28.0, 36.0


def a_star(fig, d, pose='idle'):
    if d == 'S':
        arm = 72 if pose == 'idle' else 54            # side points; raised in the stretch
        tips = [(0, 12.4, 1.9), (arm, 12.8, 2.1), (360 - arm, 12.8, 2.1), (148, 12.5, 2.1), (212, 12.5, 2.1)]
        return star(fig, A_CX, A_CY, tips, 6.4), A_CX
    s = 1 if d == 'E' else -1
    cx = A_CX - s * 0.5
    # turned to the side: the front arm reaches forward, the back arm tucks shorter, the
    # feet trail a little; the face plane bulges forward under the brow (the cheek step)
    tips = [(0, 12.4, 1.9), ((360 + s * 78) % 360, 12.4, 2.1), ((360 - s * 62) % 360, 10.4, 2.0),
            ((360 + s * 154) % 360, 12.2, 2.1), ((360 - s * 140) % 360, 11.6, 2.0)]
    m = star(fig, cx, A_CY, tips, 6.4, 0.88)
    m |= ell(cx + s * 5.2, A_CY + 0.5, 2.6, 3.4)
    return m, cx


def a_cap(fig, d, keep, pose='idle'):
    """Slate nightcap with snow stripes, a snow cuff and pompom, on the top point."""
    if d == 'S':
        if pose == 'yawn':
            cuff_c = (28, 32.0)
            ctrl = [(28, 31), (27.5, 22.5), (37, 21), (40.5, 32)]
        else:
            cuff_c = (28, 26.4)
            ctrl = [(28, 26), (28, 21.8), (36.5, 21.2), (39.5, 29.5)]
        body, tip = cap_tube(fig, ctrl, 4.2, 1.2, 'slate', 'snow', ((0.40, 0.50), (0.74, 0.84)), floor=cuff_c[1])
        band(fig, cuff_c[0], cuff_c[1], 5.2, 1.6, 'snow')
        pompom(fig, tip[0] + 0.5, tip[1] + 1.8, 2.4, 'snow')
        return
    s = 1 if d == 'E' else -1
    c = A_CX - s * 0.5
    ctrl = [(c, 26), (c - s * 0.5, 21.8), (c - s * 9, 21.2), (c - s * 11.5, 29.5)]
    body, tip = cap_tube(fig, ctrl, 4.2, 1.2, 'slate', 'snow', ((0.40, 0.50), (0.74, 0.84)), floor=26.4)
    band(fig, c + s * 0.4, 26.4, 4.8, 1.6, 'snow')
    pompom(fig, tip[0] - s * 0.5, tip[1] + 1.8, 2.4, 'snow')


def a_face(fig, d, keep, pose='idle', cx=A_CX):
    y = int(A_CY) - 3
    if d == 'S':
        if pose != 'yawn':
            eye(fig, 23, y, keep, shape='sleepy')
            eye(fig, 31, y, keep, shape='sleepy')
            blush(fig, 21, y + 4, keep)
            blush(fig, 33, y + 4, keep)
            for p in ((26, y + 4), (27, y + 5), (28, y + 5), (29, y + 4)):
                fig.put(p[0], p[1], 'plaster_cool', 1)
                keep.add(p)
        else:
            # the yawn: a tall round mouth; the eyes are under the slipped cap
            mouth = [(26, y + 3), (27, y + 3), (28, y + 3)]
            mouth += [(x, y + 4) for x in range(25, 30)] + [(x, y + 5) for x in range(25, 30)]
            mouth += [(26, y + 6), (27, y + 6), (28, y + 6)]
            for p in mouth:
                fig.put(p[0], p[1], 'ink', 0)
                keep.add(p)
            fig.put(26, y + 6, 'berry', 3)
            fig.put(27, y + 6, 'berry', 3)
            blush(fig, 21, y + 4, keep)
            blush(fig, 33, y + 4, keep)
        return
    s = 1 if d == 'E' else -1
    ex = int(cx + s * 3.5) - (0 if s > 0 else 1)
    eye(fig, ex, y, keep, shape='sleepy')
    fx = int(cx - s * 2.5)
    for yy in (y + 1, y + 2):
        fig.put(fx, yy, 'ink', 0)
        keep.add((fx, yy))
    blush(fig, int(cx + s * 3.5) - (0 if s > 0 else 1), y + 4, keep)
    mx = int(cx + s * 6.5) - (1 if s > 0 else 0)
    for p in ((mx, y + 4), (mx - s, y + 5)):
        fig.put(p[0], p[1], 'plaster_cool', 1)
        keep.add(p)


def sparkle(fig, cx, cy):
    """The inner light (lamp), a 2 x 2 heart glowing through the belly: bright over warm."""
    pts = {(cx, cy): 5, (cx + 1, cy): 5, (cx, cy + 1): 4, (cx + 1, cy + 1): 4}
    for p, t in pts.items():
        fig.glow(p[0], p[1], 'lamp', t)
    return set(pts)


def option_a(view):
    fig = sk.Fig(W, H)
    keep = set()
    d = 'S' if view in ('S', 'Sf') else view
    pose = 'yawn' if view == 'Sf' else 'idle'
    body, cx = a_star(fig, d, pose)
    form(fig, body, 'plaster', cx, A_CY, 13.0)
    dust(fig, body, 'plaster', seed=3)
    keep |= sparkle(fig, int(cx) - 1 + (0 if d == 'S' else (1 if d == 'E' else -1)), int(A_CY) + 4)
    a_cap(fig, d, keep, pose)
    a_face(fig, d, keep, pose, cx)
    if view == 'Sf':
        keep |= mote_px(fig, 12, 26)
        keep |= mote_px(fig, 45, 40, horiz=False)
    finish(fig, keep)
    return fig


# =====================================================================================
# B  Dust-ball with a trailing cap
# =====================================================================================
B_CX, B_CY, B_R = 28.0, 37.5, 8.6


def b_ball(fig, d, pose='idle'):
    rays = [(70, 13.2, 1.5), (290, 13.2, 1.5), (144, 11.8, 1.5), (216, 11.8, 1.5)]
    sx = 1.0
    cx = B_CX
    if d in ('E', 'W'):
        s = 1 if d == 'E' else -1
        cx = B_CX - s * 0.5
        rays = [((360 + s * 80) % 360, 13.0, 1.5), ((360 - s * 64) % 360, 11.4, 1.4),
                ((360 + s * 152) % 360, 11.8, 1.5), ((360 - s * 156) % 360, 11.2, 1.4)]
        sx = 0.94
    if pose == 'twinkle':
        rays = [(56, 13.6, 1.5), (304, 13.6, 1.5), (144, 11.8, 1.5), (216, 11.8, 1.5)]
    m = ell(cx, B_CY, B_R * sx, B_R)
    for (a, L, tr) in rays:
        base = [polar(cx, B_CY, a - 26, B_R - 1.5, sx), polar(cx, B_CY, a + 26, B_R - 1.5, sx),
                polar(cx, B_CY, a, L - tr * 0.5, sx)]
        m |= fig.poly(base)
        tx, ty = polar(cx, B_CY, a, L - tr, sx)
        m |= disc(tx, ty, tr)
    if d in ('E', 'W'):
        m |= ell(cx + s * 6.4, B_CY + 0.8, 2.4, 3.0)    # cheek step
    return m, cx


def b_cap(fig, d, keep, pose='idle', dy=0):
    """A long snow nightcap with regolith stripes: the cuff on the crown, the cone up over
    the back, trailing down to a regolith pompom by the heel (the comet tail)."""
    bands = ((0.30, 0.38), (0.52, 0.60), (0.74, 0.82))
    if d == 'S':
        ctrl = [(28, 30 + dy), (29, 21.6 + dy), (42, 21.6 + dy), (42, 41 + dy)]
        body, tip = cap_tube(fig, ctrl, 4.6, 1.2, 'snow', 'regolith', bands, floor=30.2 + dy)
        band(fig, 28, 30.2 + dy, 6.6, 1.7, 'regolith')
        pompom(fig, tip[0], tip[1] + 2.0, 2.3, 'regolith')
        return
    s = 1 if d == 'E' else -1
    c = B_CX - s * 0.5
    ctrl = [(c + s * 0.5, 30), (c - s * 1.5, 21.4), (c - s * 13, 21.0), (c - s * 17, 35)]
    body, tip = cap_tube(fig, ctrl, 4.6, 1.2, 'snow', 'regolith', bands, floor=30.2)
    return tip


def b_cuff_side(fig, d):
    s = 1 if d == 'E' else -1
    band(fig, B_CX + s * 0.5, 30.2, 6.2, 1.7, 'regolith')


def b_face(fig, d, keep, pose='idle', cx=B_CX, dy=0):
    y = 34 + dy
    if d == 'S':
        if pose == 'twinkle':
            eye(fig, 22, y, keep, shape='happy')
            eye(fig, 31, y, keep, shape='happy')
            mouth = ((26, y + 5), (27, y + 6), (28, y + 6), (29, y + 5))
        else:
            eye(fig, 23, y, keep, h=3)
            eye(fig, 31, y, keep, h=3)
            mouth = ((27, y + 5), (28, y + 5))
        blush(fig, 21, y + 4, keep)
        blush(fig, 33, y + 4, keep)
        for p in mouth:
            fig.put(p[0], p[1], 'plaster_cool', 1)
            keep.add(p)
        return
    s = 1 if d == 'E' else -1
    ex = int(cx + s * 4) - (0 if s > 0 else 1)
    eye(fig, ex, y, keep, h=3)
    fx = int(cx - s * 2)
    for yy in (y + 1, y + 2):
        fig.put(fx, yy, 'ink', 0)
        keep.add((fx, yy))
    blush(fig, int(cx + s * 4) - (0 if s > 0 else 1), y + 4, keep)
    mx = int(cx + s * 7) - (1 if s > 0 else 0)
    fig.put(mx, y + 5, 'plaster_cool', 1)
    fig.put(mx - s, y + 5, 'plaster_cool', 1)
    keep |= {(mx, y + 5), (mx - s, y + 5)}


def option_b(view):
    fig = sk.Fig(W, H)
    keep = set()
    d = 'S' if view in ('S', 'Sf') else view
    pose = 'twinkle' if view == 'Sf' else 'idle'
    dy = -1 if pose == 'twinkle' else 0
    tip = None
    if d != 'S':
        tip = b_cap(fig, d, keep, pose)          # the trailing cap passes behind the ball
    body, cx = b_ball(fig, d, pose)
    if dy:
        body = {(x, y + dy) for (x, y) in body}
    cy = B_CY + dy
    form(fig, body, 'plaster', cx, cy, B_R + 1.5)
    dust(fig, body, 'plaster', seed=5)
    core(fig, cx + (0 if d == 'S' else (1.5 if d == 'E' else -1.5)), cy + 5.6, 2.6, 1.5)
    if d == 'S':
        b_cap(fig, d, keep, pose, dy)
    else:
        b_cuff_side(fig, d)
        s = 1 if d == 'E' else -1
        pompom(fig, tip[0], tip[1] + 2.0, 2.3, 'regolith')
    b_face(fig, d, keep, pose, cx, dy)
    if pose == 'twinkle':
        # the glint that travels round its points, caught on the west ray's tip (the
        # star's own light, so a glow), and two motes shed below
        tx, ty = polar(cx, cy, 304, 11.6)
        keep |= mote_px(fig, int(tx), int(ty), horiz=False)
        keep |= mote_px(fig, 17, 48)
        keep |= mote_px(fig, 37, 50, horiz=False)
    finish(fig, keep)
    return fig


# =====================================================================================
# C  Star-sprite: a star head on a tiny nightgown, tapering into a dust wisp
# =====================================================================================
C_CX, C_CY = 28.0, 31.5


def c_head(fig, d, pose='idle'):
    if d == 'S':
        tips = [(0, 10.6, 1.5), (76, 12.6, 1.3), (284, 12.6, 1.3), (140, 10.6, 1.3), (220, 10.6, 1.3)]
        return star(fig, C_CX, C_CY, tips, 5.8), C_CX
    s = 1 if d == 'E' else -1
    cx = C_CX - s * 0.5
    tips = [(0, 10.6, 1.5), ((360 + s * 82) % 360, 12.2, 1.3), ((360 - s * 70) % 360, 10.0, 1.3),
            ((360 + s * 142) % 360, 10.2, 1.3), ((360 - s * 140) % 360, 9.4, 1.3)]
    m = star(fig, cx, C_CY, tips, 6.0, 0.9)
    m |= ell(cx + s * 4.8, C_CY + 0.6, 2.2, 2.8)
    return m, cx


def c_gown(fig, d, keep):
    """A tiny slate nightgown, flared, its hem scalloped, with one fold."""
    s = 0 if d == 'S' else (1 if d == 'E' else -1)
    c = C_CX - 0.5 - s * 0.5
    g = fig.poly([(c - 3, 36), (c + 4, 36), (c + 6, 44), (c - 5, 44)])
    g |= fig.rect(int(c - 3), 36, int(c + 4), 38)
    for x in range(int(c - 5), int(c + 6) + 1):           # scalloped hem
        if (x - int(c)) % 3 == 1:
            g.discard((x, 43))
    for (x, y) in sorted(g):
        xs = [p[0] for p in g if p[1] == y]
        t = 3
        if x - min(xs) < 2:
            t = 4
        elif max(xs) - x < 2:
            t = 2
        if (x, y + 1) not in g:
            t = 1 if x > c - 2 else 2
        if x == int(c + 1) and 38 < y < 42:
            t = 2                                            # one fold, a recess
        if x == int(c) and 38 < y < 42 and t == 3:
            t = 4                                            # its lit lip
        f = 'slate' + ('_warm' if t >= 4 else '_cool' if t <= 2 else '')
        fig.put(x, y, f, t)
    return g


def c_wisp(fig, d, keep):
    """The dust wisp under the hem: plaster dust thinning to a curl (outlined like the
    body), its heart glowing (lamp) just under the hem."""
    s = 0 if d == 'S' else (1 if d == 'E' else -1)
    k = -s if s else 1
    c = int(C_CX)
    pts = {}
    for x in range(c - 3, c + 3):
        pts[(x, 44)] = 3
    for x in range(c - 2, c + 2):
        pts[(x + (0 if s == 0 else 0), 45)] = 3
    for x in range(c - 1 + k, c + 1 + k):
        pts[(x, 46)] = 2
    pts[(c + 2 * k, 47)] = 2
    pts[(c + 2 * k + (1 if k > 0 else -1), 47)] = 1
    for p, t in sorted(pts.items()):
        lit = (p[0] - 1, p[1]) not in pts
        tn = 4 if lit and t == 3 else t
        fig.put(p[0], p[1], 'plaster' + ('_warm' if tn >= 4 else '_cool' if tn <= 2 else ''), tn)
    for p in ((c - 1, 44), (c, 44)):
        fig.glow(p[0], p[1], 'lamp', 5)
    for p in ((c - 1, 45), (c, 45)):
        fig.glow(p[0], p[1], 'lamp', 4)
    keep |= {(c - 1, 44), (c, 44), (c - 1, 45), (c, 45)}
    return set(pts)


def cloth_small(fig, mask, fam, darker=0):
    for (x, y) in sorted(mask):
        t = 3 - darker
        if (x, y - 1) not in mask or (x - 1, y) not in mask:
            t = 4 - darker
        if (x, y + 1) not in mask or (x + 1, y) not in mask:
            t = 2 - (1 if darker else 0)
        f = fam + ('_warm' if t >= 4 else '_cool' if t <= 2 else '')
        fig.put(x, y, f, max(1, t))


def c_arms(fig, d, keep, pose='idle', cx=C_CX):
    """Sleeves (slate) with round star-stuff mitts (plaster)."""
    if d == 'S':
        if pose == 'pull':
            # the right mitt up at the pompom, tugging it like a lamp's pull cord
            sl = fig.poly([(31, 37), (33, 36), (36.5, 32), (38.5, 33), (35, 39), (32, 39.5)])
            cloth_small(fig, sl, 'slate')
            form(fig, disc(37.8, 31.0, 1.8), 'plaster', 37.8, 31, 2, glint=False)
            sl2 = fig.poly([(25, 37), (22, 39), (21, 41), (23, 42), (26, 39)])
            cloth_small(fig, sl2, 'slate')
            form(fig, disc(21.5, 42.0, 1.7), 'plaster', 21.5, 42, 2, glint=False)
            return
        for side in (-1, 1):
            x0 = C_CX + side * 3.5
            sl = fig.poly([(x0, 36.5), (x0 + side * 3, 38), (x0 + side * 3.5, 41), (x0 + side * 1.5, 41), (x0, 39)])
            cloth_small(fig, sl, 'slate', darker=1 if side > 0 else 0)
            mx = x0 + side * 2.6
            form(fig, disc(mx, 42, 1.7), 'plaster', mx, 42, 2, glint=False)
        return
    s = 1 if d == 'E' else -1
    x0 = cx + s * 1.5
    sl = fig.poly([(x0, 36.5), (x0 + s * 4, 38), (x0 + s * 5.5, 40), (x0 + s * 3.5, 41), (x0, 39.5)])
    cloth_small(fig, sl, 'slate')
    mx = x0 + s * 5.0
    form(fig, disc(mx, 41.2, 1.5), 'plaster', mx, 41.2, 2, glint=False)


def c_cap(fig, d, keep, pose='idle', cx=C_CX):
    """A snow nightcap with slate stripes, a slate cuff and pompom: it stands up off the top
    point and curls back over (in the fidget it is pulled down like a lamp cord)."""
    bands = ((0.38, 0.52), (0.74, 0.86))
    if d == 'S':
        ctrl = [(28, 25), (28.5, 22.4), (33, 20.4), (37.5, 22.2)] if pose != 'pull' else \
            [(28, 25), (28.5, 22.3), (36, 22.5), (37.5, 29.5)]
        body, tip = cap_tube(fig, ctrl, 3.7, 1.1, 'snow', 'slate', bands, floor=25.4)
        band(fig, 28, 25.4, 4.6, 1.4, 'slate')
        pompom(fig, tip[0] + 0.3, tip[1] + 1.6, 2.0, 'slate')
        return
    s = 1 if d == 'E' else -1
    ctrl = [(cx, 25), (cx - s * 0.5, 22.4), (cx - s * 5, 20.4), (cx - s * 9.5, 22.2)]
    body, tip = cap_tube(fig, ctrl, 3.7, 1.1, 'snow', 'slate', bands, floor=25.4)
    band(fig, cx + s * 0.3, 25.4, 4.4, 1.4, 'slate')
    pompom(fig, tip[0] - s * 0.3, tip[1] + 1.6, 2.0, 'slate')


def c_face(fig, d, keep, pose='idle', cx=C_CX):
    y = 30
    if d == 'S':
        shape = 'shut' if pose == 'pull' else 'open'
        eye(fig, 24, y, keep, shape=shape)
        eye(fig, 30, y, keep, shape=shape)
        blush(fig, 22, y + 4, keep)
        blush(fig, 32, y + 4, keep)
        mouth = ((27, y + 5), (28, y + 5)) if pose != 'pull' else ((26, y + 4), (27, y + 5), (28, y + 5), (29, y + 4))
        for p in mouth:
            fig.put(p[0], p[1], 'plaster_cool', 1)
            keep.add(p)
        return
    s = 1 if d == 'E' else -1
    ex = int(cx + s * 3) - (0 if s > 0 else 1)
    eye(fig, ex, y, keep)
    fx = int(cx - s * 2)
    for yy in (y + 1, y + 2):
        fig.put(fx, yy, 'ink', 0)
        keep.add((fx, yy))
    blush(fig, int(cx + s * 3) - (0 if s > 0 else 1), y + 4, keep)
    mx = int(cx + s * 5.8) - (1 if s > 0 else 0)
    fig.put(mx, y + 4, 'plaster_cool', 1)
    fig.put(mx - s, y + 4, 'plaster_cool', 1)
    keep |= {(mx, y + 4), (mx - s, y + 4)}


def option_c(view):
    fig = sk.Fig(W, H)
    keep = set()
    d = 'S' if view in ('S', 'Sf') else view
    pose = 'pull' if view == 'Sf' else 'idle'
    c_wisp(fig, d, keep)
    c_gown(fig, d, keep)
    head, cx = c_head(fig, d, pose)
    form(fig, head, 'plaster', cx, C_CY, 11.0)
    dust(fig, head, 'plaster', seed=1)
    c_arms(fig, d, keep, pose, cx)
    c_cap(fig, d, keep, pose, cx)
    c_face(fig, d, keep, pose, cx)
    if pose == 'pull':
        keep |= mote_px(fig, 15, 37, horiz=False)
        keep |= mote_px(fig, 34, 47)
    finish(fig, keep)
    return fig


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Plump star: five cushion points, face in the middle, cap on the top point',
        question='The star itself is the body: side points are stubby arms, lower points dangling feet, '
                 'the face in the middle and the nightcap on the top point.',
        fn=option_a, palette=['plaster', 'slate', 'snow', 'berry'], glow='lamp',
        pose='Drifts half-asleep with its arms out like a starfish floating on its back, lids low.',
        parts=[
            'cap (slate, snow stripes, snow cuff): layer 4; head (top point); flops away from the facing, droops over the eyes in the yawn and nap',
            'pompom (snow): layer 5; cap tip; swings a frame late in walk and hop',
            'star body (plaster, sibling dust): layer 2; hover point (6 px over the foot); bobs 1 px a beat in idle and walk',
            'arm points x2 (plaster): layer 1 (far) / 3 (near); body; swing in the walk, raised in cast and cheer, crossed for guard',
            'foot points x2 (plaster): layer 1; body; dangle and kick in the 6-frame float-walk, tuck in hop and nap',
            'core glow (lamp): layer 3; body; dims to tone 4 in nap and lights out, flares in cast',
            'face (ink eyes, berry blush): layer 3; body; blink, sleepy lids, yawn mouth',
        ],
        notes=[
            'Works: a true five-pointed silhouette nobody in the cast has; it reads as a star at 2 px before any detail.',
            'Risk: side views are a squeezed star, so the profile leans on the cheek step and one eye; the arm points',
            'cannot hold props (fine: the Wildcard borrows the familiar\'s special, it carries nothing).',
            'Compared with Eastward 05 (Sam, the small white-haired girl, about this height): big head mass, 2 x 3 eyes.',
        ]),
    dict(
        label='B', name='Dust-ball: a round glowing ball, four short rays, a long cap trailing to the heel',
        question='A ball of Dream Dust is the star: four short rays (two hands, two toes) round it, '
                 'and the long nightcap makes the comet tail.',
        fn=option_b, palette=['plaster', 'regolith', 'snow', 'berry'], glow='lamp',
        pose='Round and contented, bobbing like a lantern, the long cap trailing behind like a comet.',
        parts=[
            'long cap (snow, regolith stripes and cuff): layer 0 behind the ball in E/W, 4 over the crown in S; head; trails a frame behind every move, wraps round in nap',
            'pompom (regolith): layer 0/4; cap tip; swings at the heel, bounces on hop',
            'ball body (plaster, sibling dust): layer 2; hover point; squash and stretch 1 px in hop and hit',
            'hand rays x2 (plaster): layer 1/3; ball rim; wave in walk, thrust in strike, raised in cheer',
            'toe rays x2 (plaster): layer 1; ball rim; paddle in the float-walk, tuck in nap',
            'core glow (lamp): layer 3; ball; the twinkle and the cast spawn from it',
            'face (ink eyes, berry blush): layer 3; ball; happy shut eyes in the twinkle',
        ],
        notes=[
            'Works: the comma of ball plus trailing cap is unique and the cap is a free secondary motion in every state.',
            'Risk: a round body nears Puffcap\'s and Tuff\'s mass; the rays and the long cap must stay big enough to read.',
            'The cap\'s stripes, cuff and pompom are regolith (moon ground), tying Lumen to its last folk.',
            'Compared with Eastward 05 (Sam): a rounded mass with a lit cap and a dark crescent at this size.',
        ]),
    dict(
        label='C', name='Star-sprite: a star head on a tiny slate nightgown, a dust wisp with a glowing heart for legs',
        question='A star-shaped head on a tiny body: the head\'s lower points fall over the shoulders, '
                 'the gown thins into a trail of dust.',
        fn=option_c, palette=['plaster', 'slate', 'snow', 'berry'], glow='lamp',
        pose='A small sleepy sprite in its nightgown, mitts folded, ready to pull the cord on the lights.',
        parts=[
            'cap (snow, slate stripes, slate cuff and pompom): layer 5; head (top point); curls back, the pompom is a pull cord in lights out',
            'star head (plaster): layer 4; neck; tilts 1 px in idle, nods in nap',
            'gown (slate, scalloped hem, one fold): layer 2; hover point; hem sways a frame late in walk',
            'sleeves x2 (slate) with mitts (plaster): layer 1 (far) / 3 (near); shoulder; swing, wind-up, cast, guard',
            'dust wisp (plaster dust, lamp-glow heart under the hem): layer 0; hem; curls behind the walk, sheds motes in cheer and lights out',
            'face (ink eyes, berry blush): layer 4; head; shut eyes in lights out',
        ],
        notes=[
            'Works: the most humanlike, so every fight pose has arms and a body to act with; the star head is the read.',
            'Risk: a star head over a dark gown is busier at 2 px than A; the head points must not read as ears.',
            'The wisp\'s heart is the inner light (lamp glow), the dust round it an outlined plaster form.',
            'Compared with Eastward 05 (Sam and the two kids): a body under a big head, a 3-tone gown with one fold.',
        ]),
]


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return (ys[0], ys[-1]) if ys else (0, 0)


# =====================================================================================
# FINAL (revision round, 21 Oct): option A, the plump star, with grafts.
#   - it glows: a stepped lamp core on the belly (tone 2 out to a near-white centre), a
#     warm plaster tone-5 rim along the lit upper-left points, real form shading.
#   - from C: a dust wisp under the feet (the float-walk is a bob and a wisp sway).
#   - from B: the long cap trailing behind like a comet in E and W (shorter in fights).
#   - E and W turn the star: the near arm and near foot overlap the body, the far arm and
#     far foot sit behind it, one eye, a brow and a cheek step on the face side.
#   - no shoulder perch: in fights the familiar floats beside Mote at head height, on
#     the side away from the foe; the anchor is recorded per pose.
# =====================================================================================
F_CX, F_CY, F_R = 28.0, 35.0, 11.6


def rot_pt(p, o, deg):
    r = math.radians(deg)
    dx, dy = p[0] - o[0], p[1] - o[1]
    return (o[0] + dx * math.cos(r) - dy * math.sin(r), o[1] + dx * math.sin(r) + dy * math.cos(r))


def f_form(fig, mask, fam, cx, cy, R, rim=True, darker=0, glint=True, lit=0.36, cres=1.0, east1=False):
    """Form shading for the final star: a warm lit cap at the upper left, a cool crescent
    at the lower right that follows the form, undersides 1, and (rim) a warm tone-5 line
    along the lit up- and left-facing edges of the upper-left half: the star's own light
    catching its points."""
    mask = set(mask)
    for (x, y) in sorted(mask):
        u, v = (x + 0.5 - cx) / R, (y + 0.5 - cy) / R
        t = 3
        if (u + 0.36) ** 2 + (v + 0.42) ** 2 < lit:
            t = 4
        if (u + 0.30) ** 2 + (v + 0.36) ** 2 > cres:
            t = 2
        up_open = (x, y - 1) not in mask
        left_open = (x - 1, y) not in mask
        if (up_open or left_open) and t == 3 and (u < 0.35 or (up_open and v < -0.2)):
            t = 4
        if rim and (up_open or left_open) and t == 4 and u + v < -0.25:
            t = 5
        if (x + 1, y) not in mask and t >= 3 and u > 0.1:
            t = 2
        if east1 and t <= 3 and u > 0.3 and ((x + 1, y) not in mask or (x + 2, y) not in mask):
            t = 1            # the east face turned from the light
        if (x, y + 1) not in mask and v > 0.1:
            t = 1 if u > -0.35 else 2
        t = max(1, t - darker) if t < 5 or darker else t
        f = fam + '_warm' if t >= 4 else fam + '_cool' if t <= 2 else fam
        fig.put(x, y, f, t)
    if glint and not darker:
        top = sorted(mask, key=lambda p: ((p[0] - cx) * 0.55 + (p[1] - cy) * 0.85, p))
        for p in top[:2]:
            fig.put(p[0], p[1], fam + '_warm', 5)
    return mask


def cone(cx, cy, a, L, tr, base_r=5.0, half=24, sx=1.0):
    """A star point: a cone from radius base_r out to a rounded tip at length L."""
    pts = [polar(cx, cy, a - half, base_r, sx), polar(cx, cy, a + half, base_r, sx),
           polar(cx, cy, a, L - tr * 0.5, sx)]
    m = sk.Fig(W, H).poly(pts)
    tx, ty = polar(cx, cy, a, L - tr, sx)
    return m | disc(tx, ty, tr)


CORE = {'normal': ('..33..', '.3443.', '235532', '234432', '..33..'),
        'dim': ('.2332.', '.2332.'),
        'flare': ('..44..', '.3443.', '335533', '335533', '.3443.', '..44..')}


def f_core(fig, cx, cy, level, keep):
    """The inner light (lamp glow only), stepped from tone 2 out to a near-white centre.
    It dims in the nap and flares in the cast: the state reads with no extra body frames."""
    rows = CORE[level]
    x0 = int(round(cx)) - 3
    y0 = int(round(cy))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != '.':
                fig.glow(x0 + i, y0 + j, 'lamp', int(ch))
                keep.add((x0 + i, y0 + j))


def f_wisp(fig, cx, top, sway, keep, curl=False, mote=True):
    """The dust wisp under the feet (from C): Dream Dust as an outlined plaster tail, lit
    on its west column, cool on its east one, swaying back by `sway`, and one glowing mote
    pair at its heart."""
    rows = [(0, -2, 0), (1, -1, 0), (2, -1, 0), (3, 0, 1), (4, 1, 2)]
    if curl:
        rows = [(0, -1, 0), (1, 0, 1), (2, 1, 3)]
    m = {}
    for k, (dy, a, b) in enumerate(rows):
        off = int(round(sway * k / 3.0))
        for x in range(int(cx) + a + off, int(cx) + b + off + 1):
            m[(x, top + dy)] = k
    for (x, y) in sorted(m):
        # dust, not a limb: one pale warm tone (4), its last row a tone down
        t = 3 if (x, y + 1) not in m and (x, y - 1) in m and m[(x, y)] >= 3 else 4
        fig.put(x, y, 'plaster_warm', t)
    # a mote trails off the wisp's tip (a finite glint, unoutlined)
    tx, ty = max(m, key=lambda p: (p[1], p[0] * (1 if sway >= 0 else -1)))
    if mote and not curl:
        keep |= mote_px(fig, tx + (2 if sway >= 0 else -3), ty + 1)
    return set(m)


def f_band(fig, cx, cy, rx, ry, fam, rot=0.0):
    """The cuff, an elliptic rib band turned with the top point."""
    m = set()
    r = math.radians(rot)
    for y in range(int(cy - rx) - 1, int(cy + rx) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * math.cos(r) + dy * math.sin(r)
            v = -dx * math.sin(r) + dy * math.cos(r)
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                m.add((x, y))
    for (x, y) in sorted(m):
        t = 3
        if (x, y - 1) not in m or (x - 1, y) not in m:
            t = 4
        if (x + 1, y) not in m:
            t = 2
        if (x, y + 1) not in m:
            t = 1 if x > cx else 2
        if t == 3 and (x - int(cx)) % 3 == 2:
            t = 2
        fig.put(x, y, fam + ('_warm' if t >= 4 else '_cool' if t <= 2 else ''), t)
    return m


def f_cap(fig, s, cx, cy, top_a, mode, keep):
    """The slate nightcap (snow stripes, cuff and pompom) on the top point. s is 0 (S),
    1 (E) or -1 (W); mode: 'front', 'yawn', 'long' (the comet tail of E/W idle), 'short'
    (fights, clear of the familiar), 'flung' (hit), 'nap'."""
    kx, ky = polar(cx, cy, top_a, F_R - 2.6)
    if mode == 'front':
        ctrl = [(0, 0), (0, -4.2), (8.5, -4.8), (11.5, 3.5)]
    elif mode == 'yawn':
        ky += 6
        ctrl = [(0, 0), (-0.5, -8.5), (9, -10), (12.5, 1)]
    elif mode == 'nap':
        ctrl = [(0, 0), (-1, -4), (-8, -4), (-10, 4)]
    elif mode == 'long':
        ctrl = [(0, 0), (-s * 1.5, -5.5), (-s * 12, -5.8), (-s * 15.5, 4.5)]
    elif mode == 'short':
        ctrl = [(0, 0), (-s * 1.0, -5.6), (-s * 7, -7.2), (-s * 10, -3.5)]
    else:  # flung: the tail whips up behind
        ctrl = [(0, 0), (-s * 1, -5), (-s * 8, -9), (-s * 12, -5)]
    ctrl = [rot_pt((kx + dx, ky + dy), (kx, ky), top_a if mode not in ('yawn', 'nap', 'front') else 0)
            for dx, dy in ctrl]
    body, tip = cap_tube(fig, ctrl, 4.2, 1.2, 'slate', 'snow', ((0.40, 0.50), (0.74, 0.84)), floor=ky + 0.4)
    f_band(fig, kx + s * 0.3, ky + 0.4, 5.2 if s == 0 else 4.8, 1.6, 'snow',
           rot=top_a if mode not in ('yawn', 'nap', 'front') else 0)
    pompom(fig, tip[0] - s * 0.4, tip[1] + 1.8, 2.4, 'snow')


def f_eye(fig, x, y, shape, keep, s=0):
    if shape in ('sleepy', 'open', 'fierce'):
        for j in range(3):
            for i in range(2):
                fig.put(x + i, y + j, 'ink', 0)
                keep.add((x + i, y + j))
        if shape == 'sleepy':
            fig.put(x, y, 'plaster_cool', 2)
            fig.put(x + 1, y, 'plaster_cool', 2)
            fig.put(x, y + 1, 'snow', 5)
        elif shape == 'fierce':
            # a flat brow line cuts the top, slanting down to the front
            fig.put(x, y, 'plaster_cool', 1)
            fig.put(x + 1, y, 'plaster_cool', 1)
            fig.put(x + (0 if s >= 0 else 1), y + 1, 'snow', 5)
        else:
            fig.put(x, y, 'snow', 5)
    elif shape == 'shut':
        for i in range(3):
            fig.put(x + i - (1 if s < 0 else 0), y + 1 + (1 if i == 1 else 0), 'plaster_cool', 1)
            keep.add((x + i - (1 if s < 0 else 0), y + 1 + (1 if i == 1 else 0)))
    elif shape == 'happy':
        for (i, j) in ((0, 2), (1, 1), (2, 2)):
            fig.put(x + i - (1 if s < 0 else 0), y + j, 'plaster_cool', 1)
            keep.add((x + i - (1 if s < 0 else 0), y + j))
    elif shape == 'wince':
        for (i, j) in ((0, 0), (1, 1), (0, 2)) if s >= 0 else ((1, 0), (0, 1), (1, 2)):
            fig.put(x + i, y + j, 'ink', 0)
            keep.add((x + i, y + j))


def f_mouth(fig, pts, keep, fam=('plaster_cool', 1)):
    for p in pts:
        fig.put(p[0], p[1], fam[0], fam[1])
        keep.add(p)


def f_blush(fig, x, y, keep):
    fig.put(x, y, 'berry_warm', 5)
    fig.put(x + 1, y, 'berry_warm', 5)
    keep |= {(x, y), (x + 1, y)}


def f_mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar at 16 art px (Mote's own perch scale): a round leaf-green blob,
    two ink eyes turned to the foe, a two-leaf sprout. It floats beside Mote."""
    if curled:
        body = ell(cx, base - 4, 6.0, 4.2)
        f_form(fig, body, 'leaf', cx, base - 4, 6.0, rim=False, glint=False)
        for x in (cx - 3, cx + 1):
            fig.put(x, base - 4, 'leaf_cool', 1)
            fig.put(x + 1, base - 4, 'leaf_cool', 1)
        for (x, y, t) in ((cx + 2, base - 9, 4), (cx + 3, base - 9, 3), (cx + 3, base - 10, 4), (cx + 4, base - 10, 3)):
            fig.put(x, y, 'leaf_warm' if t >= 4 else 'leaf', t)
        return
    body = ell(cx, base - 6, 6.5, 6.0)
    f_form(fig, body, 'leaf', cx, base - 6, 6.5, rim=False, glint=False, lit=0.7, cres=1.25)
    ey = base - 8
    for ex in ((cx, cx + 3) if d == 1 else (cx - 4, cx - 1)):
        fig.put(ex, ey, 'ink', 0)
        fig.put(ex, ey + 1, 'ink', 0)
        keep |= {(ex, ey), (ex, ey + 1)}
    fig.put(ex - 3 if d == 1 else ex - 3, ey, 'snow', 5) if False else None
    top = base - 12
    fig.put(cx, top, 'leaf_cool', 2)
    fig.put(cx, top - 1, 'leaf_cool', 2)
    for (x, y, t) in ((cx - 1, top - 2, 4), (cx - 2, top - 2, 4), (cx - 2, top - 3, 4),
                      (cx + 1, top - 2, 3), (cx + 2, top - 2, 2), (cx + 2, top - 3, 3)):
        fig.put(x, y, 'leaf_warm' if t >= 4 else 'leaf' if t == 3 else 'leaf_cool', t)


# --- the turned star (E and W) and the front star (S) --------------------------------
POSES = {
    #          rot  dx  dy  far arm (a, L)   near arm (a, L)  far foot  near foot   eyes      core      cap      sway
    'idle':   (0, 0, 0, (100, 11.8), (264, 12.0), (160, 10.8), (204, 11.6), 'sleepy', 'normal', 'long', -1),
    'ready':  (8, 0, 0, (80, 12.4), (290, 11.6), (164, 10.8), (206, 11.4), 'open', 'normal', 'short', -2),
    'strike': (18, 3, 0, (92, 13.8), (268, 10.6), (172, 10.4), (214, 11.2), 'fierce', 'normal', 'short', -3),
    'cast':   (-4, 0, -1, (60, 14.0), (298, 13.0), (160, 10.8), (200, 11.4), 'shut', 'flare', 'short', -1),
    'hit':    (-16, -3, 0, (122, 10.2), (250, 11.2), (150, 10.8), (196, 11.4), 'wince', 'dim', 'flung', 1),
    'sit':    (-4, 0, 3, (118, 10.8), (262, 10.8), (138, 10.6), (176, 11.0), 'sleepy', 'normal', 'short', 0),
    'cheer':  (0, 0, -2, (52, 14.2), (304, 13.4), (162, 10.8), (198, 11.4), 'happy', 'normal', 'short', -1),
}


def f_side(fig, s, pose, keep):
    rot, dx, dy, far_arm, near_arm, far_foot, near_foot, eyes, level, capmode, sway = POSES[pose]
    cx, cy = F_CX + dx - s * 0.5, F_CY + dy
    A = lambda a: (s * (a + rot)) % 360  # noqa: E731
    # behind: the far arm and the far foot, a tone down
    far = cone(cx, cy, A(far_arm[0]), far_arm[1], 1.9, sx=0.85) | cone(cx, cy, A(far_foot[0]), far_foot[1], 1.9)
    if capmode == 'long' or capmode == 'short' or capmode == 'flung':
        pass
    f_form(fig, far, 'plaster', cx, cy, F_R, darker=1, rim=False)
    # the body: a plump lens, the top point, the near foot, a brow and a cheek step
    body = ell(cx, cy + 0.5, 7.0, 8.0)
    body |= cone(cx, cy, A(4), F_R, 1.8, base_r=4.5, half=30)
    body |= cone(cx, cy, A(near_foot[0]), near_foot[1], 2.0, base_r=4.5, half=26)
    bx, by = rot_pt((cx + s * 5.0, cy - 3.6), (cx, cy), s * rot)
    body |= ell(bx, by, 2.2, 1.8)                               # brow
    kx, ky = rot_pt((cx + s * 5.8, cy + 1.0), (cx, cy), s * rot)
    body |= ell(kx, ky, 2.4, 2.6)                               # cheek
    wisp_top = int(round(cy + 7.6))
    wisp = f_wisp(fig, cx - s * 0.5, wisp_top, -s * abs(sway) if sway else 0, keep, curl=(pose == 'sit'),
                  mote=(pose == 'idle'))
    f_form(fig, body, 'plaster', cx, cy, F_R, cres=0.74, east1=True)
    # the near arm overlaps the body, lit on its own upper left, its shadow on the body
    na = cone(cx, cy, A(near_arm[0]), near_arm[1], 2.0, base_r=5.0, half=22, sx=0.85)
    acx, acy = polar(cx, cy, A(near_arm[0]), near_arm[1] * 0.55)
    f_form(fig, na, 'plaster', acx - 1.5, acy - 1.5, 6.0, glint=False)
    # the joint: where the near arm lies over the body, its lower and east edge is a
    # recess a tone darker than both
    for (x, y) in sorted(na):
        if any(q in body and q not in na for q in ((x + 1, y), (x, y + 1))) and tone(fig, (x, y)) and tone(fig, (x, y)) < 5:
            fig.put(x, y, 'plaster_cool', 2)
    # face: one eye under the brow, blush on the cheek, the mouth at the front
    ex, ey = rot_pt((cx + s * 3.2, cy - 4.0), (cx, cy), s * rot)
    ex = int(round(ex)) - (1 if s < 0 else 0)
    ey = int(round(ey))
    f_eye(fig, ex, ey, eyes, keep, s)
    bx2, by2 = rot_pt((cx + s * 4.2, cy + 0.2), (cx, cy), s * rot)
    f_blush(fig, int(round(bx2)) - (1 if s < 0 else 0), int(round(by2)), keep)
    mx, my = rot_pt((cx + s * 6.4, cy + 1.6), (cx, cy), s * rot)
    mx, my = int(round(mx)), int(round(my))
    if eyes == 'wince':
        f_mouth(fig, [(mx - s, my), (mx - s, my + 1)], keep, ('ink', 0))
    elif eyes in ('happy',):
        f_mouth(fig, [(mx - s, my), (mx - 2 * s, my + 1), (mx - s, my + 1)], keep, ('ink', 0))
    else:
        f_mouth(fig, [(mx - s, my), (mx - 2 * s, my + 1)], keep)
    ccx, ccy = rot_pt((cx + s * 1.0, cy + 1.8), (cx, cy), s * rot)
    f_core(fig, ccx, ccy, level, keep)
    f_cap(fig, s, cx, cy, A(4), capmode, keep)
    return cx, cy, body | far | na | wisp


def f_front(fig, pose, keep):
    cx, cy = F_CX, F_CY
    rot = 0
    arm, leg, L = 72, 144, 1.0
    eyes, level, capmode = 'sleepy', 'normal', 'front'
    if pose == 'yawn':
        arm = 54
        eyes, capmode = None, 'yawn'
    if pose == 'nap':
        cy, rot, L = 41.5, 28, 0.86
        eyes, level, capmode = 'shut', 'dim', 'nap'
    tips = [(rot, F_R * L, 1.8), (rot + arm, 12.8 * L, 2.0), (rot + 360 - arm, 12.8 * L, 2.0),
            (rot + leg, 11.6 * L, 2.0), (rot + 360 - leg, 11.6 * L, 2.0)]
    tips = [((a % 360), l, r) for a, l, r in tips]
    body = star(fig, cx, cy, tips, 6.0 * (0.95 if pose == 'nap' else 1.0))
    if pose != 'nap':
        f_wisp(fig, cx, int(cy + 7.6), 1 if pose == 'yawn' else 0, keep, mote=(pose == 'idle'))
    f_form(fig, body, 'plaster', cx, cy, F_R * L)
    ey = int(cy) - 4
    if pose == 'idle':
        f_eye(fig, 23, ey, 'sleepy', keep)
        f_eye(fig, 31, ey, 'sleepy', keep)
        f_mouth(fig, [(27, ey + 4), (28, ey + 4)], keep)
    elif pose == 'yawn':
        mouth = [(26, ey + 3), (27, ey + 3), (25, ey + 4), (26, ey + 4), (27, ey + 4), (28, ey + 4),
                 (25, ey + 5), (26, ey + 5), (27, ey + 5), (28, ey + 5), (26, ey + 6), (27, ey + 6)]
        f_mouth(fig, mouth, keep, ('ink', 0))
        fig.put(26, ey + 6, 'berry', 3)
        fig.put(27, ey + 6, 'berry', 3)
    else:
        ex, ey2 = rot_pt((cx - 4.5, cy - 2.5), (cx, cy), rot)
        f_eye(fig, int(ex), int(ey2), 'shut', keep)
        ex, ey2 = rot_pt((cx + 3.5, cy - 2.5), (cx, cy), rot)
        f_eye(fig, int(ex), int(ey2), 'shut', keep)
    if pose != 'nap':
        f_blush(fig, 21, ey + 3, keep)
        f_blush(fig, 33, ey + 3, keep)
        f_core(fig, cx, cy + 2, level, keep)
    else:
        bx, by = rot_pt((cx - 6, cy + 1), (cx, cy), rot)
        f_blush(fig, int(bx), int(by), keep)
        ccx, ccy = rot_pt((cx, cy + 2), (cx, cy), rot)
        f_core(fig, ccx, ccy, level, keep)
    f_cap(fig, 0, cx, cy, rot if pose == 'nap' else 0, capmode, keep)
    return body


def final_view(view):
    """Returns (fig, perch anchor or None)."""
    fig = sk.Fig(W, H)
    keep = set()
    perch = None
    if view == 'S idle':
        f_front(fig, 'idle', keep)
    elif view == 'S fidget':
        f_front(fig, 'yawn', keep)
        keep |= mote_px(fig, 12, 27)
    elif view == 'nap S':
        f_front(fig, 'nap', keep)
        f_mossling(fig, 44, 51, 1, keep, curled=True)
    else:
        d, pose = view.split()
        s = 1 if d == 'E' else -1
        cx, cy, _ = f_side(fig, s, pose, keep)
        if pose == 'strike':
            tx, ty = polar(cx, cy, (s * (92 + 18)) % 360, 13.8)
            keep |= mote_px(fig, int(round(tx)) + (1 if s > 0 else -2), int(round(ty)) - 1, horiz=False)
        if pose == 'cast':
            keep |= mote_px(fig, int(cx + s * 12), 22)
            keep |= mote_px(fig, int(cx + s * 9), 17, horiz=False)
        if pose == 'cheer':
            keep |= mote_px(fig, int(cx - s * 2), 15)
        if pose != 'idle':
            # the familiar floats beside Mote at head height, on the side away from the foe
            fx = 9 if s > 0 else W - 10
            base = int(cy) + 1
            f_mossling(fig, fx, base, s, keep)
            perch = (fx, base)
    finish(fig, keep)
    return fig, perch


FINAL_VIEWS = ('S idle', 'E idle', 'W idle', 'S fidget', 'nap S', 'E ready', 'E strike', 'E cast', 'E hit',
               'E sit', 'E cheer', 'W ready', 'W strike')

FINAL = dict(
    label='A final', chosen='A',
    name='Plump star that glows: lamp core, warm rim, a dust wisp, the comet cap in E/W',
    grafts=[
        'From C: the dust wisp under the feet (outlined plaster dust with a glow at its heart): the float-walk is a 1 px bob and a wisp sway, and the fight poses stand on it.',
        'From B: the long cap trailing like a comet behind the head in E and W idle; in fights it trails short, clear of the familiar.',
        'Fixes: a stepped lamp core on the belly (tone 2 out to a near-white centre), a warm plaster tone-5 rim on the lit points, turned side views, and the familiar floating beside Mote instead of on a shoulder.',
    ],
    palette=['plaster', 'slate', 'snow', 'berry', 'leaf'],
    glow='lamp',
    pose='Drifts half-asleep with its points out like a starfish floating on its back, lids low, its heart-light '
         'glowing; in a fight it leans in with the far point and lets the familiar bob beside it.',
    parts=[
        'cap (slate, snow stripes, snow cuff): layer 6; head anchor on the top point; changes in S/E/W (front flop in S, comet tail in E/W idle, short tail in fights, flung on hit, droops over the eyes in yawn and nap)',
        'pompom (snow): layer 6; cap tip; swings a frame late in walk, hop and strike',
        'far arm point (plaster, a tone down): layer 1; body; E/W only (hidden in S); reaches forward in ready, thrusts in strike, up in cast and cheer',
        'far foot point (plaster, a tone down): layer 1; body; E/W only; trails in strike, forward in sit',
        'dust wisp (plaster dust, lamp mote): layer 2; hover point (6 px over the foot anchor); sways back in walk and strike, curls under in sit, absent in nap',
        'star body with top point and near foot (plaster, warm rim): layer 3; hover point; bobs 1 px a beat; leans with the pose (rot)',
        'core glow (lamp, 6 x 5 stepped): layer 4; body; normal, dim (hit, nap), flare (cast)',
        'near arm point (plaster, own form, a darker joint where it lies over the body): layer 5; body; S: the side points; E/W: the back point in front of the body, swings back in strike, up in cast and cheer',
        'face (ink eye(s), berry blush, brow and cheek step in E/W): layer 5; body; sleepy, open, fierce, shut, happy, wince',
        'familiar (stand-in Mossling, 16 px, leaf): floats beside Mote at head height on the side away from the foe; perch anchor per fight pose; curled against Mote in the nap',
    ],
    notes=[
        'Compared with Eastward 05 at Mote\'s height (Sam, the small white-haired girl, and the two kids): a big',
        'head mass, 2 x 3 ink eyes with a glint, 3 to 4 tones a material, a dark closed outline, and a lit rim on hair.',
        'Cast: the only star silhouette; plaster stays warm and the lamp core makes it a light, apart from Puffcap\'s cream.',
        'Open: the 16 px familiar floats beside Mote (no shoulder); the fight layout needs this anchor per frame.',
    ],
)


def build_final():
    views, nums, perches, ok = [], {}, {}, True
    for cap in FINAL_VIEWS:
        fig, perch = final_view(cap)
        im = fig.image()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        top, bot = height(im)
        print(f"final {cap:9s} rows {top}-{bot} ({bot - top + 1})  on house {100*m['on_house']:5.1f}%  "
              f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
              f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['rows'] = [top, bot]
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Mote final (folk 14, Lumen): A, the plump star, with grafts', [entry], OUT_FINAL,
                    note='30 art px, cell 56 x 60, foot (28, 54), hovering 6 px. Fight poses carry the stand-in '
                         'Mossling (16 px) floating beside Mote, away from the foe; glow: lamp.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], glow=FINAL['glow'], pose=FINAL['pose'], perch_anchor=perches,
                perch_note='[x, y] in cell px: the familiar\'s foot point, floating beside Mote at head height '
                           'on the side away from the foe (no shoulder perch).',
                measure=nums, notes=FINAL['notes'], _ok=ok)


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
            top, bot = height(im)
            print(f"{o['label']} {cap:9s} rows {top}-{bot} ({bot - top + 1})  on house {100*m['on_house']:5.1f}%  "
                  f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
            nums[cap]['rows'] = [top, bot]
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('Mote (folk 14, Lumen): how a star becomes a character', OPTIONS, OUT_PNG,
                    note='30 art px, cell 56 x 60, foot (28, 54), hovering 6 px over it (the renderer adds the '
                         'shadow). Views: S, E, W idle and the S fidget key pose.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='mote', height_art_px=30, cell=[W, H], foot=[AX, AY], hover_art_px=HOVER,
                       question='How a star becomes a character.', options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
