"""The village's buildings at density 3 and up (`village.building(spec, seed, hd=True)` lands here).

Eastward's level of detail in our house style (art-style.md, house-style.md): every wall, slate,
board and stone is a small pillow lit from the upper left, and the building as a whole reads as a
solid in the light:

- the roof is a plane with thickness: slates (or straw) in courses, the plane lighter towards the
  ridge and the west, a ridge of capping tiles, hips turned to and from the light, verges and a
  fascia with their own lit arris, the eave hanging over the wall and throwing a shadow band on it;
- the walls have their material (rubble in courses, dressed ashlar, timber framing over lime
  plaster, lapped boards) and form: lit at the west arris, darker down towards the ground and
  round the east corner, a foundation course standing proud with its lit ledge, weeds at the foot;
- windows sit in the wall's depth (lintel, shaded head and west reveal, lit east reveal, painted
  frame, glass with the sky in its upper west and the room behind it, a sill with its drip shadow),
  doors are set back in a frame on a threshold step with hinges and a latch;
- chimneys are stacks with a cap, pots, flashing, soot and their shadow on the roof;
- every trade shows itself: the bakery's oven stack, loaves and flour, the forge's mouth, hood
  and tools, the library's shelves through the glass, the herbalist's drying herbs and jars.

The damage overlay (holes with torn slate courses, snapped rafters and battens over a dark loft,
scorch, slipped and fallen slates, boarded openings, tarps, scaffolding, cracks) is a second
picture of the same size and anchor, so a restore removes it whole.

Sizes are world px (`q` makes texels); the canvas, its foot and its wall line are the same as
`village.building`'s, so the plan's looks, the scale gate's door measure and the scene's anchors
hold. Detail comes in clusters of two texels or more (`finish` removes lone texels).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from . import village as V
from .palette import FI

q, code, fill, put, edges, chamfer = V.q, V.code, V.fill, V.put, V.edges, V.chamfer
STONES = ('stone', 'stone_warm', 'stone_cool')


# ------------------------------------------------------------------------------------------------
# small tools
# ------------------------------------------------------------------------------------------------
def grid(a):
    H, W = a.shape
    return np.mgrid[0:H, 0:W]


def rect(a, x0, y0, x1, y1):
    return V._rect(a.shape, x0, y0, x1, y1)


def step(a, m, d, lo=0, hi=5):
    """Move tones under m by d along each family's own ramp."""
    sel = m & (a >= 0) & (a % 8 <= 5)
    a[sel] = (a[sel] // 8) * 8 + np.clip(a[sel] % 8 + d, lo, hi)


def hsh(*v):
    h = 0
    for x in v:
        h = (h * 1000003) ^ (int(x) * 2654435761)
    return ((h >> 7) & 0xffff) / 65535.0


def pillow(m, t, rng, lit_top=2, flecks=1, under=2, east=1, slate=False):
    """Tones for one piece (a stone, a block, a slate) lit from the upper left: the top arris and
    the row under it lit, the west edge lit, the east edge and the row over the foot turning away,
    the foot dark; a fleck or two of the material's grain in two-texel clusters. A slate is the
    other way up: its head lies in the shade of the course above, its butt catches the light."""
    h, w = m.shape
    T, Lf, Bm, Rt = edges(m)
    up2 = np.zeros_like(T)
    up2[1:] = T[:-1]
    dn2 = np.zeros_like(Bm)
    dn2[:-1] = Bm[1:]
    cols = np.arange(w)[None, :].repeat(h, 0)
    rows = np.arange(h)[:, None].repeat(w, 1)
    tt = np.full(m.shape, t, int)
    if slate:
        head = rows < max(1, h // 3)
        tt[head] = t - 1
        tt[Lf & ~head] = t + 1
        tt[dn2 & m] = t + 1
        tt[Bm] = t + 2
        tt[Bm & (cols > w * 0.75)] = t + 1
        tt[Rt & ~Bm] = t - 1
    else:
        tt[up2 & m & (cols < w * 0.7)] = t + 1
        tt[Lf] = t + 1
        tt[T] = t + lit_top
        tt[T & (cols > w * 0.72)] = t + max(0, lit_top - 1)
        tt[dn2 & m & ~T & (cols > w * 0.35)] = t - 1
        tt[Rt & ~T] = t - east
        tt[Bm] = t - under
    for _ in range(flecks):
        if h >= 5 and w >= 6:
            fy = int(rng.integers(2, h - 2))
            fx = int(rng.integers(1, w - 3))
            d = int(rng.choice([-1, -1, 1]))
            ln = int(rng.integers(2, 4))
            sl = (fy, slice(fx, min(w - 1, fx + ln)))
            tt[sl] = np.where(m[sl], t + d, tt[sl])
    return np.clip(tt, 0, 5)


def irregular(h, w, rng, cut=1):
    """A piece's outline: corners knocked off, one of them a little more."""
    m = chamfer(h, w, cut if (w > 2 * cut + 1 and h > 2 * cut + 1) else 0)
    if h >= 6 and w >= 7 and rng.random() < 0.5:
        k = int(rng.integers(0, 4))
        ys = 0 if k < 2 else h - 1
        xs = 0 if k % 2 == 0 else w - 1
        for d in range(cut + 1):
            yy = ys + (d if ys == 0 else -d)
            for e in range(cut + 1 - d):
                xx = xs + (e if xs == 0 else -e)
                m[yy, xx] = False
    return m


def break_runs(a, rng, longest):
    """No ruler lines: a long ledge, arris, gutter lip or fascia row of one code is broken where
    its pieces meet (a joint a tone down with a lit texel after it) every few world px, as the
    real thing is made of lengths, never one stroke."""
    H_, W_ = a.shape
    for y in range(H_):
        row = a[y]
        x = 0
        while x < W_:
            c = row[x]
            x1 = x
            while x1 < W_ and row[x1] == c:
                x1 += 1
            if c >= 0 and c % 8 <= 6 and x1 - x > longest:
                if c % 8 == 6:
                    c = (c // 8) * 8 + 0          # an edge row: its joints step up from the edge's dark
                k = x + int(rng.integers(q(4), q(9)))
                while k < x1 - 3:
                    t = c % 8
                    # two steps, so the joint survives the review's 16-level quantising
                    row[k:k + 2] = (c // 8) * 8 + (t - 2 if t >= 2 else t + 2)
                    if 1 <= t <= 4:
                        row[k + 2] = (c // 8) * 8 + min(5, t + 1)
                    k += int(rng.integers(q(5), q(11)))
            x = x1


# ------------------------------------------------------------------------------------------------
# walls
# ------------------------------------------------------------------------------------------------
def wall_tone(fx, fy, rng, top=3):
    """A piece's body tone by where it sits on the front: lit high on the west, darker down
    towards the ground and round the east corner, the odd piece a step off."""
    t = top
    if fy > 0.66 + 0.18 * rng.random():
        t -= 1
    if fx > 0.84 + 0.1 * rng.random():
        t -= 1
    r = rng.random()
    if r < 0.12:
        t += 1
    elif r < 0.24:
        t -= 1
    return int(np.clip(t, 1, 4))


def rubble_wall(a, x0, y0, x1, y1, rng, fams=STONES, course=(2.4, 3.4), length=(3.2, 6.2), top=3, moss=0.22,
                where=None, mortar=('stone_cool', 1), span=None):
    """Dry-laid stone in rough courses: each stone its own sibling and tone by its place on the
    wall, a pillow with a lit top arris and a dark foot, flecks of grain; dark recessed joints with
    moss in the lower ones."""
    fill(a, x0, y0, x1, y1, code(*mortar), where)
    sx0_, sx1_, sy0_, sy1_ = span or (x0, x1, y0, y1)
    y = y1
    while y > y0 + 1:
        h = max(5, q(rng.uniform(*course)))
        yt = max(y0, y - h)
        x = x0 - int(rng.integers(0, q(length[1])))
        while x < x1:
            L = max(5, q(rng.uniform(*length)))
            a0, a1 = max(x, x0), min(x + L - 1, x1)
            hh = y - 1 - yt
            if a1 - a0 >= 3 and hh >= 2:
                fx = ((a0 + a1) / 2 - sx0_) / max(1, sx1_ - sx0_)
                fy = ((yt + y) / 2 - sy0_) / max(1, sy1_ - sy0_)
                t = wall_tone(fx, fy, rng, top)
                m = irregular(hh, a1 - a0, rng, cut=1 if hh < 8 else 2)
                f = fams[int(rng.integers(0, len(fams)))]
                put(a, a0, yt, m, f, pillow(m, t, rng, flecks=2 + int(rng.random() < 0.5)), where)
                if moss and fy > 0.55 and rng.random() < moss:
                    mx = int(rng.integers(a0, max(a0 + 1, a1 - 3)))
                    mw = int(rng.integers(3, 6))
                    fill(a, mx, y - 2, mx + mw, y, code('leaf', 2), where)
                    fill(a, mx + 1, y - 3, mx + mw - 1, y - 2, code('leaf', 3), where)
            x += L
        y = yt


def ashlar_wall(a, x0, y0, x1, y1, rng, course=3.6, length=(5.5, 9.0), where=None, span=None):
    """Dressed stone: even courses, long blocks in bond with fine joints, a lit arris on each, the
    mason's tooling across the face, weathering darker towards the foot and the east corner."""
    fill(a, x0, y0, x1, y1, code('ashlar_warm', 1), where)
    sx0_, sx1_, sy0_, sy1_ = span or (x0, x1, y0, y1)
    y = y1
    k = 0
    while y > y0 + 1:
        h = q(course)
        yt = max(y0, y - h)
        x = x0 - (q(length[0] / 2) if k % 2 else 0) - int(rng.integers(0, 3))
        while x < x1:
            L = q(rng.uniform(*length))
            a0, a1 = max(x, x0), min(x + L - 1, x1)
            hh = y - 1 - yt
            if a1 - a0 >= 4 and hh >= 3:
                fx = ((a0 + a1) / 2 - sx0_) / max(1, sx1_ - sx0_)
                fy = ((yt + y) / 2 - sy0_) / max(1, sy1_ - sy0_)
                t = wall_tone(fx, fy, rng, 3)
                f = ('ashlar', 'ashlar_warm', 'ashlar', 'stone_warm')[int(rng.integers(0, 4))]
                m = chamfer(hh, a1 - a0, 1)
                tt = pillow(m, t, rng, lit_top=2, flecks=0, under=2)
                # tooling: short diagonal strokes a tone down, in pairs
                for _ in range(max(2, (a1 - a0) // q(1.4))):
                    tx = int(rng.integers(2, max(3, a1 - a0 - 3)))
                    ty = int(rng.integers(2, max(3, hh - 3)))
                    for d in range(2):
                        if ty + d < hh - 1 and tx + d < a1 - a0 - 1:
                            tt[ty + d, tx + d] = max(0, t - 1)
                            if tx + d + 1 < a1 - a0 - 1:
                                tt[ty + d, tx + d + 1] = max(0, t - 1)
                for _ in range(int(rng.integers(0, 3))):     # a chipped arris
                    cxp = int(rng.choice([1, max(1, a1 - a0 - 3)]))
                    cyp = int(rng.choice([1, max(1, hh - 3)]))
                    tt[cyp:cyp + 2, cxp:cxp + 2] = max(0, t - 1) if cyp > 1 else min(5, t + 1)
                if rng.random() < 0.25:                    # lichen in a soft rosette
                    ly, lx = int(rng.integers(2, max(3, hh - 3))), int(rng.integers(2, max(3, a1 - a0 - 5)))
                    tt[ly:ly + 2, lx:lx + 3] = t - 1
                if rng.random() < 0.18:                # a weathered block, its face spalled
                    sy, sx = int(rng.integers(2, max(3, hh - 3))), int(rng.integers(2, max(3, a1 - a0 - 5)))
                    tt[sy:sy + 2, sx:sx + 4] = max(0, t - 1)
                    tt[sy + 2:sy + 3, sx:sx + 4] = min(5, t + 1)
                put(a, a0, yt, m, f, tt, where)
            x += L
        y = yt
        k += 1


def board_wall(a, x0, y0, x1, y1, rng, fams=('timber', 'timber_warm', 'timber_cool'), lap=3.2, span=None):
    """Lapped weatherboards: each board a tone by its place, in the shade of the board above at
    its head, its lower arris lit over the dark line of the lap; grain, knots, butt joints with
    nail heads on the studs."""
    sx0_, sx1_, sy0_, sy1_ = span or (x0, x1, y0, y1)
    y = y0
    studs = list(range(int(x0) + q(rng.uniform(4, 9)), int(x1) - 2, q(12)))
    while y < y1:
        h = max(6, q(lap * rng.uniform(0.9, 1.1)))
        yb = min(y1, y + h)
        x = x0
        while x < x1:
            L = q(rng.uniform(16, 30))
            a0, a1 = x, min(x1, x + L)
            fx = ((a0 + a1) / 2 - sx0_) / max(1, sx1_ - sx0_)
            fy = ((y + yb) / 2 - sy0_) / max(1, sy1_ - sy0_)
            t = wall_tone(fx, fy, rng, 3)
            f = fams[int(rng.integers(0, len(fams)))]
            m = np.ones((yb - y, a1 - a0), bool)
            hh, ww = m.shape
            tt = np.full(m.shape, t, int)
            tt[:2, :] = t - 1                       # the head, in the lap's shade
            if hh > 4:
                tt[-2, :] = t + 1                   # the lower arris lit
            tt[-1, :] = t - 2                       # the lap's dark line
            tt[:, 0] = np.minimum(tt[:, 0], t - 1)  # the butt joint
            for _ in range(max(1, ww // q(5))):
                gy = int(rng.integers(2, max(3, hh - 2)))
                gx = int(rng.integers(1, max(2, ww - 6)))
                tt[gy, gx:gx + int(rng.integers(3, 8))] = t - 1
            if rng.random() < 0.35 and ww > 10 and hh > 5:
                kx, ky = int(rng.integers(3, ww - 4)), int(rng.integers(2, hh - 3))
                tt[ky:ky + 2, kx:kx + 2] = t - 2
                tt[ky, kx] = t - 1
            put(a, a0, y, m, f, np.clip(tt, 0, 5))
            x = a1
        for sx in studs:
            if y + 2 < yb - 2:
                fill(a, sx, y + 2, sx + 2, y + 4, code('iron', 1))
                fill(a, sx, y + 2, sx + 1, y + 3, code('iron', 3))
        y = yb


def plaster_panel(a, x0, y0, x1, y1, rng, fam='plaster', top=3, span=None):
    """Lime plaster in a frame's panel: a calm body in two close tones laid in trowel drifts,
    shaded by the timbers round it (the beam above, the post to the west), damp and darker in its
    lower third, a hairline crack and the odd patch where it has fallen and the stone shows."""
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    sx0_, sx1_, sy0_, sy1_ = span or (x0, x1, y0, y1)
    Y, X = grid(a)
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    fx = (X - sx0_) / max(1, sx1_ - sx0_)
    fy = (Y - sy0_) / max(1, sy1_ - sy0_)
    tt = np.full(a.shape, top, int)
    # trowel drifts: soft horizontal lenses a tone up or down, clustered
    for _ in range(max(2, (x1 - x0) * (y1 - y0) // 90)):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        rx, ry = rng.uniform(3, 8), rng.uniform(1.0, 2.2)
        lm = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2) <= 1
        tt[lm] += int(rng.choice([-1, 1, 1]))
    tt[(fy > 0.72) & ((X * 7 + Y * 3) % 11 < 7)] -= 1          # damp creeping up from the sill
    tt[fx > 0.86] -= 1
    tt[Y < y0 + 2] -= 1                                          # the beam's shade
    tt[(X < x0 + 2)] -= 1                                        # the post's shade to the east of it
    tt = np.clip(tt, 1, 5)
    fams = np.where(((X // 9 + Y // 7) % 5 == 0), FI[fam + '_warm'] if fam + '_warm' in FI else FI[fam], FI[fam])
    a[m] = (fams * 8 + tt)[m]
    # a hairline crack from a corner, a tone down, with its lit lower lip
    if rng.random() < 0.7 and (x1 - x0) > q(8):
        cx, cy = x0 + 3, y0 + 3
        if rng.random() < 0.5:
            cx = x1 - 4
        for _ in range(int(rng.integers(4, 8))):
            nx = cx + int(rng.integers(0, 3)) * (1 if cx < (x0 + x1) / 2 else -1)
            ny = cy + int(rng.integers(1, 3))
            cm = V.seg_mask(a.shape, cx, cy, nx, ny, 0.6) & m
            step(a, cm, -2)
            cx, cy = nx, ny
    # a fallen patch: lath or stone behind it, its rim lit at the foot
    if rng.random() < 0.55 and (x1 - x0) > q(9) and (y1 - y0) > q(7):
        px, py = rng.uniform(x0 + q(2), x1 - q(6)), rng.uniform(y0 + q(3), y1 - q(5))
        pw, ph = q(rng.uniform(3.5, 5.5)), q(rng.uniform(2.2, 3.2))
        pm = (((X - px - pw / 2) / (pw / 2)) ** 2 + ((Y - py - ph / 2) / (ph / 2)) ** 2 <= 1) & m
        if pm.sum() > 12:
            rubble_wall(a, int(px), int(py), int(px + pw), int(py + ph), rng, course=(1.4, 1.8), length=(2.0, 3.2),
                        top=3, moss=0, where=pm, mortar=('stone_cool', 2))
            T_, _, B_, _ = edges(pm)
            a[T_] = code(fam, 1)
            a[B_ & ~T_] = code(fam, 5)


def timber(a, x0, y0, x1, y1, rng, fam='timber', t=2, pegs=()):
    """A squared oak timber in a frame: lit on its west (or top) face, dark on the east (or under),
    checks and grain along it, oak pegs where it is jointed."""
    V.beam(a, int(x0), int(y0), int(x1), int(y1), rng, fam, t, hd=True)
    for (px, py) in pegs:
        fill(a, px, py, px + 2, py + 2, code(fam, max(0, t - 1)))
        fill(a, px, py, px + 1, py + 1, code(fam, min(5, t + 2)))


def frame_wall(a, spec, L, R, B, y_e, rng, span):
    """A timber frame on a stone ground course: posts, a sill beam, a wall plate under the eave,
    braces in the wide bays, plaster panels between, the pegs at the joints."""
    sill_y = B - q(spec.get('frame_rail', 17))
    rubble_wall(a, L, sill_y, R, B, rng, course=(2.6, 3.4), length=(3.6, 6.4), top=3, span=span)
    pw = q(2.6)
    posts = sorted(set([L, R - pw] + [L + q(x) for x in spec.get('posts', [])]))
    plate = q(2.4)
    # panels first, timbers over them
    for (xa, xb) in zip(posts, posts[1:]):
        plaster_panel(a, xa + pw, y_e + plate, xb, sill_y - q(2.4), rng, span=span)
    timber(a, L, sill_y - q(2.6), R, sill_y, rng, 'timber', 3)
    timber(a, L, y_e, R, y_e + plate, rng, 'timber', 3)
    for (xa, xb) in zip(posts, posts[1:]):
        if xb - xa > q(18):
            # a brace from the sill up to the plate, as long as the bay allows
            bx0, by0 = xa + pw, sill_y - q(2.6)
            bx1, by1 = xa + pw + min(q(12), (xb - xa - pw) * 0.6), y_e + plate + q(1)
            bm = V.seg_mask(a.shape, bx0, by0, bx1, by1, q(0.9)) & rect(a, xa + pw, y_e + plate, xb, sill_y - q(2.6))
            T_, Lf, B_, R_ = edges(bm)
            Y, X = grid(a)
            a[bm] = code('timber', 3)
            a[bm & (((X + Y) // 5) % 3 == 0)] = code('timber', 2)          # the grain along it
            a[bm & (T_ | Lf)] = code('timber', 4)
            a[bm & (B_ | R_)] = code('timber', 1)
            step(a, ndi.binary_dilation(bm, iterations=2) & ~bm & (X > bx0) & rect(a, xa + pw, y_e + plate, xb, sill_y - q(2.6)), -1)
    for i, x in enumerate(posts):
        t = 3
        timber(a, x, y_e + plate, x + pw, sill_y - q(2.6), rng, 'timber', t,
               pegs=[(x + 3, y_e + plate + 3), (x + 3, sill_y - q(2.6) - 5)])
    return sill_y


def quoins(a, L, R, B, y_e, rng, top=4):
    """Long and short dressed corner stones up both ends, the west lit, the east turned away."""
    y = B
    k = 0
    while y > y_e:
        hh = q(rng.uniform(4.2, 5.4))
        ww = q(6.0 if k % 2 == 0 else 4.0)
        for (xa, xb, t) in ((L, L + ww, 3), (R - ww, R, 2)):
            h_ = min(hh, y - y_e) - 1
            if h_ >= 3:
                m = chamfer(h_, xb - xa, 1)
                put(a, xa, y - 1 - h_, m, ('stone_warm', 'stone')[k % 2], pillow(m, t, rng, flecks=1))
        y -= hh
        k += 1


def wall_light(a, L, R, B, y_e, fh):
    """The front as one lit plane with depth round it: the west arris catching the light, the
    east corner turning away, the foot darker in the damp and the angle of the plinth."""
    Y, X = grid(a)
    inwall = (X >= L) & (X < R) & (Y >= y_e) & (Y < B - fh)
    step(a, inwall & (X < L + 2) & (Y > y_e + q(4)), +1)
    step(a, inwall & (X >= R - q(1.2)), -1)
    step(a, inwall & (Y >= B - fh - q(1.4)), -1)


def plinth(a, L, R, B, rng, fh):
    """The foundation course, a texel proud of the wall each side: big stones, its top a lit
    ledge, its foot in the ground's shade."""
    fx0, fx1 = L - 2, R + 2
    rubble_wall(a, fx0, B - fh, fx1, B, rng, fams=('stone_cool', 'stone', 'stone_cool'), course=(3.4, 4.0),
                length=(5.5, 9.0), top=2, moss=0.4, span=(fx0, fx1, B - fh - q(20), B))
    fill(a, fx0, B - fh, fx1, B - fh + 1, code('stone_warm', 5))
    fill(a, fx0 + 1, B - fh + 1, fx1, B - fh + 2, code('stone_warm', 4))
    fill(a, fx0, B - fh, fx0 + 1, B, code('stone_warm', 3))
    fill(a, fx1 - 2, B - fh + 1, fx1, B, code('stone_cool', 1))
    Y, X = grid(a)
    step(a, (X >= fx0) & (X < fx1) & (Y >= B - 2) & (Y < B + 1), -1)
    a[(X >= fx0) & (X < fx1) & (Y == B)] = code('stone_cool', 0)


def foot_weeds(a, L, R, B, busy, rng):
    """Grass and weeds grown up over the foundation's foot (eastward-edges 3.2), never across a
    doorway: each tuft a few blades, dark at the root, lit at the tip."""
    x = L - 2 + int(rng.integers(0, q(3)))
    while x < R:
        w = int(rng.integers(5, 10))
        if not any(b0 - 3 <= x + w and x <= b1 + 3 for (b0, b1) in busy):
            hgt = int(rng.integers(4, 9))
            for k in range(0, w, 2):
                bh = max(3, hgt - abs(k - w // 2) - int(rng.integers(0, 3)))
                lean = int(rng.choice([-1, 0, 0, 1]))
                for j in range(bh):
                    xx = x + k + (lean if j > bh * 0.6 else 0)
                    yy = B - j
                    t = 1 if j < 2 else (2 if j < bh * 0.6 else 4)
                    fill(a, xx, yy, xx + 2 - (j > bh - 2), yy + 1, code('leaf' if k % 4 else 'grass', t))
            if rng.random() < 0.25:
                fill(a, x + w // 2, B - hgt - 1, x + w // 2 + 2, B - hgt + 1, code(('brass', 'berry', 'sky')[int(rng.integers(0, 3))], 4))
        x += w + int(rng.integers(q(3), q(9)))


# ------------------------------------------------------------------------------------------------
# roofs
# ------------------------------------------------------------------------------------------------
def slate_roof(a, rm, rx0, rx1, y_r, y_eave, rng, hip=0, row=3.2, width=(3.4, 5.2), fams=('slate', 'slate', 'slate_cool'),
               moss=0.07, lichen=0.06, top=3):
    """Slates in overlapping courses: each slate a pillow the other way up (its head in the shade of
    the course above, its butt lit), its own sibling and tone by its place on the plane (lighter
    towards the ridge and the west, the hips turned to and from the light), riven grain, lichen
    and moss on a few; dark joints between."""
    fill(a, rx0, y_r, rx1, y_eave, code('slate_cool', 0), rm)
    rh = max(6, q(row))
    span = max(1, rx1 - rx0)
    y = y_eave
    k = 0
    while y > y_r:
        yt = y - rh
        fy = ((yt + y) / 2 - y_r) / max(1, y_eave - y_r)          # 0 ridge, 1 eave
        x = rx0 - int(rng.integers(0, q(width[0]))) - (q(width[0] / 2) if k % 2 else 0)
        while x < rx1:
            w = max(7, q(rng.uniform(*width)))
            cxs = x + w / 2
            fx = (cxs - rx0) / span
            f_ = np.clip((y_eave - (yt + y) / 2) / max(1, y_eave - y_r), 0, 1)
            # the plane in the light: brightest under the ridge on the west, falling off down the
            # slope and to the east, each slate stepping on its own (never a hard band)
            v = 0.95 * fy + 0.75 * fx + 0.55 * (hsh(k, x, 1) - 0.5)
            t = top + (0 if hip else 1) if v < 0.35 else (top if v < 0.9 else (top - 1 if v < 1.35 else top - 2))
            r = hsh(k, x, 3)
            if r < 0.08:
                t += 1
            elif r < 0.16:
                t -= 1
            if hip:
                if cxs < rx0 + hip * f_:
                    t = 4 + (r < 0.3)                            # the west hip, turned to the light
                elif cxs > rx1 - hip * f_:
                    t = 1 + (r < 0.4)                            # the east hip, turned away
            t = int(np.clip(t, 1, 4))
            f = fams[int(rng.integers(0, len(fams)))]
            if rng.random() < 0.05:
                f = 'slate_warm'                                 # a slate replaced since
            m = V.chamfer(rh - 1, w - 1, 1)
            tt = pillow(m, t, rng, flecks=2 + int(rng.random() < 0.6), slate=True)
            put(a, x, yt, m, f, tt, rm)
            if lichen and rng.random() < lichen:
                # a lichen rosette on the slate's face: a soft grey-green patch, its rim a tone up
                lx, ly = x + int(rng.integers(2, max(3, w - 7))), yt + int(rng.integers(rh // 3, max(rh // 3 + 1, rh - 5)))
                fill(a, lx, ly, lx + 5, ly + 3, code('grass_cool', 2), rm)
                fill(a, lx + 1, ly, lx + 4, ly + 1, code('grass_cool', 3), rm)
            if moss and fy > 0.6 and rng.random() < moss:
                mx = x + int(rng.integers(0, max(1, w - 6)))
                fill(a, mx, y - 3, mx + int(rng.integers(4, 7)), y - 1, code('leaf', 2), rm)
                fill(a, mx + 1, y - 4, mx + 4, y - 3, code('leaf', 3), rm)
                fill(a, mx + 1, y - 4, mx + 3, y - 3, code('leaf', 4), rm)
            x += w
        y = yt
        k += 1


def thatch_roof(a, rm, rx0, rx1, y_r, y_eave, rng, fam='sand', hip=0):
    """Long straw in courses: strands two texels wide, each its own tone, running down the slope;
    each course's foot a wavy lit edge over the shade of the next; weathered greyer and darker to
    the east and towards the eave, moss in the lowest course; hips turned to and from the light."""
    H, W = a.shape
    Y, X = grid(a)
    fill(a, rx0, y_r, rx1, y_eave, code(fam, 1), rm)
    ch = q(5.0)
    span = max(1, rx1 - rx0)
    pat = rng.choice([-1, 0, 0, 1], size=W)
    fams = np.where(np.repeat(rng.random(W // 3 + 2) < 0.25, 3)[:W], FI[fam + '_warm'], FI[fam])
    fams = np.where(np.repeat(rng.random(W // 5 + 2) < 0.12, 5)[:W], FI[fam + '_cool'], fams)
    y = y_eave
    k = 0
    tt = np.full(a.shape, 2, int)
    while y > y_r - ch:
        flip = rng.random(W) < 0.3
        pat = np.where(flip, rng.choice([-1, 0, 1], size=W), pat)
        wav = np.repeat(rng.integers(-2, 3, size=W // 4 + 2), 4)[:W]
        foot = y + wav[None, :]
        inc = (Y < foot) & (Y >= foot - ch)
        fxv = (X - rx0) / span
        fyv = (Y - y_r) / max(1, y_eave - y_r)
        base = 3 - (fxv > 0.62) - ((fyv > 0.8) & ((X // 2) % 3 == 0)) + (fyv < 0.18)
        # each stem broken along its length: a second tone from a random point down
        brk = (foot - rng.integers(2, max(3, ch - 1), size=W)[None, :])
        alt = rng.choice([-1, 1], size=W)[None, :]
        t_ = base + pat[None, :] + np.where((Y > brk) & ((np.arange(W)[None, :] % 3) == 0), alt, 0)
        # dark gaps between the bundles
        t_ = np.where((((np.arange(W)[None, :] + k * 3) % 7) == 0) & (Y > foot - ch + 2), base - 1, t_)
        t_ = np.where(Y == foot - 1, base + 1, t_)
        t_ = np.where(Y == foot - 2, np.maximum(t_, base), t_)
        t_ = np.where(Y == foot - ch, base - 1, t_)
        t_ = np.where(Y == foot - ch + 1, np.minimum(t_, base), t_)
        tt = np.where(inc, t_, tt)
        y -= ch
        k += 1
    if hip:
        f_ = np.clip((y_eave - Y) / max(1, y_eave - y_r), 0, 1)
        west = X < rx0 + hip * f_
        east = X >= rx1 - hip * f_
        tt = np.where(west, tt + 1, tt)
        tt = np.where(east, tt - 1, tt)
        # the hip's turn: a soft crease along the line
        crease = (np.abs(X - (rx0 + hip * f_)) < 1.5) | (np.abs(X - (rx1 - hip * f_)) < 1.5)
        tt = np.where(crease & rm, tt - 1, tt)
    tt = np.clip(tt, 0, 5)
    a[rm] = (fams[None, :].repeat(H, 0) * 8 + tt)[rm]
    # moss in the lowest course, in drifts
    for _ in range(max(2, span // q(14))):
        mx = int(rng.uniform(rx0 + 4, rx1 - 10))
        mw = int(rng.integers(5, 11))
        mm = rm & (X >= mx) & (X < mx + mw) & (Y >= y_eave - q(3.4)) & (Y < y_eave - q(1.6)) & ((X + Y) % 3 != 0)
        a[mm] = code('leaf', 2) + ((X[mm] // 2) % 2)


def thatch_eave(a, rm, rx0, rx1, y_eave, rng, fam='sand'):
    """The thatch's thick rolled eave: cut straw ends lit at the lip, the underside dark, a hazel
    ligger pinned along the lowest course."""
    Y, X = grid(a)
    thick = q(2.6)
    em = rm & (Y >= y_eave - thick)
    rel = Y - (y_eave - thick)
    tt = np.select([rel < 1, rel < 3, rel < thick - 2], [4, 3, 2], 1)
    tt = tt + (((X // 2) % 3) == 0) * -1
    a[em] = FI[fam] * 8 + np.clip(tt, 0, 5)[em]
    lig = rm & (Y >= y_eave - thick - q(1.8)) & (Y < y_eave - thick - q(0.8))
    a[lig] = code('timber_warm', 3)
    a[lig & (Y == y_eave - thick - q(1.8))] = code('timber_warm', 4)
    for x in range(int(rx0) + q(3), int(rx1) - 3, q(5)):
        sm = V.seg_mask(a.shape, x, y_eave - thick - q(1.8), x + q(2), y_eave - thick - q(0.6), 0.8) & rm
        a[sm] = code('timber', 2)


def thatch_ridge(a, rm, x0, x1, y_r, rng, fam='sand'):
    """The ridge roll: a thick bolster of straw with a patterned block-cut edge and crossed spars."""
    Y, X = grid(a)
    rr = q(4.4)
    m = rm & (Y >= y_r) & (Y < y_r + rr) & (X >= x0) & (X < x1)
    rel = Y - y_r
    tt = np.select([rel < 1, rel < q(1.5), rel < rr - 3], [5, 4, 3], 2)
    tt = np.where(X > x0 + (x1 - x0) * 0.65, tt - 1, tt)
    a[m] = FI[fam + '_warm'] * 8 + np.clip(tt, 0, 5)[m]
    # the block-cut lower edge: scallops
    sc = q(4)
    for x in range(int(x0), int(x1), sc):
        sm = rm & V.ellipse_mask(a.shape, x + sc / 2, y_r + rr, sc / 2, q(1.4)) & (Y >= y_r + rr - 1)
        a[sm] = code(fam + '_warm', 2)
        a[sm & (Y >= y_r + rr + q(0.8))] = code(fam + '_warm', 1)
    for x in range(int(x0) + q(3), int(x1) - q(3), q(6)):
        for d in (1, -1):
            sm = V.seg_mask(a.shape, x - q(1.6) * d, y_r + rr - 2, x + q(1.6) * d, y_r + 2, 0.8) & m
            a[sm] = code('timber', 3 if d > 0 else 2)


def ridge_tiles(a, rm, x0, x1, y_r, rng, fam='clay'):
    """Half-round capping tiles along the ridge: each lit across its crown, dark under its round,
    its west end lapping over the last one."""
    rc = q(2.4)
    x = x0
    k = 0
    while x < x1:
        w = q(4.4) + int(rng.integers(-1, 2))
        xa, xb = int(x), int(min(x + w, x1))
        if xb - xa >= 3:
            m = np.ones((rc, xb - xa), bool)
            m[0, 0] = m[0, -1] = False
            fx = (x - x0) / max(1, x1 - x0)
            t = 3 if fx < 0.6 else 2
            tt = np.full(m.shape, t, int)
            tt[0, :] = t + 2
            tt[1, :] = t + 1
            tt[-1, :] = t - 2
            tt[-2, :] = np.minimum(tt[-2, :], t - 1) if rc > 4 else tt[-2, :]
            tt[:, 0] = np.minimum(tt[:, 0] + 1, 5)
            tt[:, -1] = t - 2
            if rng.random() < 0.2:
                tt[1:3, 2:4] = t - 1                           # a chip in the glaze
            put(a, xa, y_r, m, fam if rng.random() > 0.2 else 'clay_cool', np.clip(tt, 0, 5), rm)
        x += w
        k += 1
    # the course under the ridge lies in its shade
    Y, X = grid(a)
    step(a, rm & (Y >= y_r + rc) & (Y < y_r + rc + 2) & (X >= x0) & (X < x1), -1)


def hip_lines(a, rm, rx0, rx1, y_r, y_eave, hip, fam='clay'):
    """Capping tiles down each hip from the ridge's end to the eave's corner."""
    for side in (-1, 1):
        xa = rx0 if side < 0 else rx1
        xb = rx0 + hip if side < 0 else rx1 - hip
        n = 6
        for k in range(n):
            f0, f1 = k / n, (k + 1) / n
            p0 = (xb + (xa - xb) * f0, y_r + (y_eave - y_r) * f0)
            p1 = (xb + (xa - xb) * f1, y_r + (y_eave - y_r) * f1)
            m = V.seg_mask(a.shape, p0[0], p0[1], p1[0], p1[1], q(1.0)) & rm
            T_, Lf, B_, R_ = edges(m)
            t = 3 if side < 0 else 2
            a[m] = code(fam, t)
            a[m & (T_ | (Lf if side < 0 else T_))] = code(fam, t + 1)
            a[m & (B_ | R_)] = code(fam, max(0, t - 2))
            jm = V.seg_mask(a.shape, p1[0], p1[1], p1[0] + 0.01, p1[1] + 0.01, q(0.75)) & m
            a[jm & B_] = code(fam, max(0, t - 2))


def verges(a, rx0, rx1, y_r, y_eave, rng):
    """A gable's verge: the roof's edge thickness and the barge board on each end, the west lit,
    the east in shade, a small finial where they meet the ridge."""
    bw = q(2.0)
    for (xa, t) in ((rx0, 3), (rx1 - bw, 2)):
        V.beam(a, xa, y_r - 1, xa + bw, y_eave + q(1.2), rng, 'timber', t, hd=True)
        # the slates' cut ends a sliver inside the board
        fill(a, xa + (bw if t == 3 else -2), y_r + q(2.4), xa + (bw + 2 if t == 3 else 0), y_eave, code('slate_cool', 1 if t == 2 else 3))
        fill(a, xa, y_r - q(1.6), xa + bw, y_r, code('timber', t + 1))
        fill(a, xa + 1, y_r - q(1.6) - 2, xa + bw - 1, y_r - q(1.6), code('timber', t))


def fascia_gutter(a, rx0, rx1, y_e, rng, gutter=True):
    """The eave's front: the slates' last course seen edge on (a lit lip over the dark of the
    underside), the fascia board, and on slate a half-round iron gutter on its brackets."""
    Y, X = grid(a)
    fh = q(2.2)
    # the eave course doubled, seen edge on: its lit arris, the slates' thickness under it
    a[(X >= rx0) & (X < rx1) & (Y == y_e - 3)] = code('slate', 5)
    a[(X >= rx0) & (X < rx1) & (Y >= y_e - 2) & (Y < y_e)] = code('slate_cool', 2)
    a[(X >= rx0) & (X < rx1) & (Y == y_e - 1)] = code('slate_cool', 1)
    V.beam(a, rx0, y_e, rx1, y_e + fh, rng, 'timber', 2, hd=True)
    # the fascia's boards butt-jointed along it, each joint with its nails
    x = rx0 + q(rng.uniform(6, 12))
    while x < rx1 - q(3):
        a[(X == x) & (Y > y_e) & (Y < y_e + fh - 1)] = code('timber', 0)
        a[(X == x + 1) & (Y > y_e) & (Y < y_e + fh - 1)] = code('timber', 3)
        fill(a, x - 3, y_e + 2, x - 1, y_e + 4, code('iron', 2))
        fill(a, x + 2, y_e + 2, x + 4, y_e + 4, code('iron', 2))
        x += q(rng.uniform(12, 20))
    # the soffit's dark under the fascia where it overhangs the gable ends
    a[(X >= rx0) & (X < rx1) & (Y == y_e + fh - 1)] = code('timber_cool', 0)
    if not gutter:
        return y_e + fh
    gy = y_e + fh
    gh = q(1.4)
    gx0, gx1 = rx0 + 2, rx1 - 2
    gm = (X >= gx0) & (X < gx1) & (Y >= gy) & (Y < gy + gh)
    rel = Y - gy
    tt = np.select([rel < 1, rel < 2, rel < gh - 1], [4, 3, 2], 1)
    a[gm] = FI['iron'] * 8 + tt[gm]
    # rust where the joints weep, brackets every few feet
    for bx in range(int(gx0) + q(4), int(gx1) - q(2), q(10)):
        fill(a, bx, gy - 1, bx + 2, gy + gh, code('iron', 1))
        fill(a, bx, gy - 1, bx + 1, gy, code('iron', 4))
    for _ in range(max(1, (rx1 - rx0) // q(30))):
        rx = int(rng.uniform(gx0 + 6, gx1 - 6))
        fill(a, rx, gy + 1, rx + 3, gy + gh - 1, code('fox', 2))
    return gy + gh


def eave_shadow(a, L, R, y_top, depth, rng, course_break=True):
    """The shadow the eave throws on the wall below it: two steps down under the eave, one step
    below that, its lower edge broken where the stones and boards stand proud of it."""
    Y, X = grid(a)
    inw = (X >= L) & (X < R)
    d1 = q(2.0)
    # (the deep part steps only what is still light, so nothing in the shade collapses to one tone)
    step(a, inw & (Y >= y_top) & (Y < y_top + d1) & (a % 8 >= 3), -1)
    edge = np.zeros(a.shape[1], int) + y_top + depth
    if course_break:
        k = 0
        x = L
        while x < R:
            w = int(rng.integers(4, 12))
            edge[x:x + w] = y_top + depth + int(rng.integers(-2, 3))
            x += w
            k += 1
    # the shadow leans down to the east (the light from the upper left)
    edge = edge + ((np.arange(a.shape[1]) - L) / max(1, R - L) * q(1.2)).astype(int)
    step(a, inw & (Y >= y_top) & (Y < edge[None, :]) & (a % 8 >= 1), -1, lo=0)


def chimney(a, rm, x0, x1, y_top, y_bot, rng, wide=False, soot=1.0, fam=STONES):
    """A stack: rubble courses lit on the west face, the east third turned away, a projecting cap
    slab (its top lit, a shadow line under it), clay pots with dark flues, soot from the top down,
    lead flashing where it meets the roof and its shadow thrown down the slates to the east."""
    Y, X = grid(a)
    rubble_wall(a, x0, y_top, x1, y_bot, rng, fams=fam, course=(2.0, 2.6), length=(2.4, 4.4), top=3, moss=0,
                span=(x0, x1, y_top - q(4), y_bot + q(10)))
    st = (X >= x0) & (X < x1) & (Y >= y_top) & (Y < y_bot)
    step(a, st & (X >= x1 - max(3, (x1 - x0) // 3)), -1)
    step(a, st & (X < x0 + 2), +1)
    # soot: whole stones darkened near the top, thinning down
    sm = st & (Y < y_top + q(3.5) * soot) & ((X // 3 + Y // 3) % 4 != 0)
    step(a, sm, -1)
    sm2 = st & (Y < y_top + q(1.6))
    step(a, sm2, -1)
    # flashing
    fl = (X >= x0 - 2) & (X < x1 + 2) & (Y >= y_bot - q(1.4)) & (Y < y_bot + 1) & (rm | st)
    a[fl] = code('slate_cool', 3)
    a[fl & (Y == y_bot - q(1.4))] = code('slate_cool', 4)
    a[fl & (Y == y_bot)] = code('slate_cool', 1)
    # its shadow down the slates to the east
    sh = rm & ~st & ~fl & (X >= x1) & (X < x1 + q(4.4) + (Y - y_top) * 0.25) & (Y >= y_top + q(3)) & (Y < y_bot + q(5))
    step(a, sh, -1, lo=0)
    step(a, sh & (X < x1 + q(2.2)) & (Y < y_bot), -1, lo=0)
    # the cap: a slab wider than the stack, seen from above the front
    cy0, cy1 = y_top - q(2.2), y_top
    V.prism(a, x0 - q(1), cy0, x1 + q(1), cy1, q(1.2), 'stone_warm', 3, side=q(1.0))
    step(a, (X >= x0) & (X < x1) & (Y >= cy1) & (Y < cy1 + 2), -1)
    # pots
    n = 2 if wide else 1
    cw = x1 - x0
    for i in range(n):
        cx = x0 + cw * (i + 1) / (n + 1)
        pw = q(3.0)
        ph = q(3.6) + (q(0.8) if i == 1 else 0)
        px0, py0 = int(cx - pw / 2), cy0 - ph
        u = (X - cx) / (pw / 2)
        pm = (X >= px0) & (X < px0 + pw) & (Y >= py0) & (Y < cy0)
        tt = V.cyl_tones(u, 3)
        a[pm] = FI['clay'] * 8 + np.clip(tt, 0, 5)[pm]
        a[pm & (Y == py0 + 1)] = code('clay', 4)
        a[pm & (Y >= cy0 - 2)] = code('clay', 1)
        # the flue's dark mouth, sooted rim
        fm = (X >= px0 + 2) & (X < px0 + pw - 2) & (Y >= py0) & (Y < py0 + 2)
        a[fm] = code('soot', 0)
        a[(X >= px0) & (X < px0 + pw) & (Y == py0 - 1)] = code('soot', 2)
        a[(X >= px0 + 1) & (X < px0 + pw - 1) & (Y == py0 - 2)] = code('soot', 1)


# ------------------------------------------------------------------------------------------------
# openings
# ------------------------------------------------------------------------------------------------
def interior(a, pm, gx0, gy0, gx1, gy1, kind, rng):
    """What shows through the lower half of a pane: shelves of books, loaves on a board, jars
    and hanging bunches, a jug and a pot on a sill; dark round it."""
    Y, X = grid(a)
    if kind == 'books':
        for sy in (gy0 + (gy1 - gy0) * 0.42, gy0 + (gy1 - gy0) * 0.72):
            sy = int(sy)
            x = gx0 + 1
            while x < gx1 - 1:
                bw = int(rng.integers(2, 4))
                bh = int(rng.integers(4, 7))
                f = ('berry', 'sky', 'brass', 'leaf', 'dusk', 'clay')[int(rng.integers(0, 6))]
                bm = pm & (X >= x) & (X < x + bw) & (Y >= sy - bh) & (Y < sy)
                a[bm] = code(f, 2)
                a[bm & (X == x)] = code(f, 3)
                a[bm & (Y == sy - bh + 1)] = code('brass', 3) if rng.random() < 0.5 else code(f, 1)
                x += bw + (1 if rng.random() < 0.2 else 0)
            a[pm & (Y >= sy) & (Y < sy + 2)] = code('timber', 2)
            a[pm & (Y == sy)] = code('timber', 3)
    elif kind == 'bread':
        sy = int(gy0 + (gy1 - gy0) * 0.72)
        a[pm & (Y >= sy) & (Y < sy + 2)] = code('timber', 2)
        a[pm & (Y == sy)] = code('timber_warm', 4)
        x = gx0 + 2
        while x < gx1 - 4:
            lw = int(rng.integers(5, 8))
            lm = pm & V.ellipse_mask(a.shape, x + lw / 2, sy, lw / 2, 3.4) & (Y < sy)
            a[lm] = code('clay', 3)
            a[lm & (Y < sy - 2) & (X < x + lw * 0.6)] = code('clay', 4)
            a[lm & (X >= x + lw - 2)] = code('clay', 2)
            a[lm & (Y == sy - 2) & ((X - x) % 3 == 1)] = code('clay', 1)
            x += lw + 1
    elif kind == 'jars':
        sy = int(gy0 + (gy1 - gy0) * 0.75)
        a[pm & (Y >= sy) & (Y < sy + 2)] = code('timber', 2)
        x = gx0 + 2
        while x < gx1 - 3:
            jw = int(rng.integers(3, 5))
            jh = int(rng.integers(5, 8))
            f = ('leaf', 'dusk', 'brass', 'sky')[int(rng.integers(0, 4))]
            jm = pm & (X >= x) & (X < x + jw) & (Y >= sy - jh) & (Y < sy)
            a[jm] = code(f, 2)
            a[jm & (X == x)] = code(f, 4)
            a[jm & (Y < sy - jh + 2)] = code('timber_warm', 3)
            x += jw + 2
        for hx in range(int(gx0) + 3, int(gx1) - 2, 6):
            hm = pm & (X >= hx) & (X < hx + 3) & (Y >= gy0 + 2) & (Y < gy0 + 7)
            a[hm] = code('leaf', 2)
            a[hm & (X == hx)] = code('leaf', 3)
    elif kind == 'home':
        sy = int(gy0 + (gy1 - gy0) * 0.78)
        a[pm & (Y >= sy) & (Y < sy + 2)] = code('timber', 2)
        jx = gx0 + 3
        jm = pm & (X >= jx) & (X < jx + 4) & (Y >= sy - 6) & (Y < sy)
        a[jm] = code('sky', 3)
        a[jm & (X == jx)] = code('sky', 4)
        a[jm & (Y == sy - 6)] = code('sky', 2)
        pm2 = pm & V.ellipse_mask(a.shape, gx1 - 5, sy - 3, 3, 3) & (Y < sy)
        a[pm2] = code('clay', 3)
        a[pm2 & (X >= gx1 - 5)] = code('clay', 2)
        lm = pm & V.ellipse_mask(a.shape, gx1 - 5, sy - 7, 3, 2.4)
        a[lm & (a // 8 != FI['clay'])] = code('leaf', 3)


def window(a, cx, yt, w, h, paint, rng, wall='stone', shutters=True, box=False, lit=False, inside='home', cols=2, rows=2):
    """A casement set in the wall's depth: a lintel over it, the head and west reveal in shade
    and the east reveal lit, a painted frame and glazing bars lit on their upper west arrises,
    glass reflecting the sky in its upper west and showing the room in its lower part, a sill
    projecting with its drip shadow, shutters on strap hinges and a planter on brackets."""
    Wx, Hx = q(w), q(h)
    x0, x1 = int(cx - Wx / 2), int(cx + Wx / 2)
    y0, y1 = int(yt), int(yt + Hx)
    Y, X = grid(a)
    dep = q(1.2)
    # the wall's depth round the opening
    a[(X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)] = code('soot', 1)
    rv_top = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y0 + dep)
    rv_w = (X >= x0) & (X < x0 + dep) & (Y >= y0) & (Y < y1)
    rv_e = (X >= x1 - dep + 1) & (X < x1) & (Y >= y0 + dep) & (Y < y1)
    rf = 'plaster' if wall == 'frame' else ('ashlar' if wall == 'ashlar' else 'stone_warm')
    a[rv_top] = code(rf, 1)
    a[rv_w] = code(rf, 1)
    a[rv_w & (Y > y0 + dep)] = code(rf, 2)
    a[rv_e] = code(rf, 4)
    a[rv_e & (X == x1 - 1)] = code(rf, 3)
    # the frame and its panes
    fx0, fy0, fx1, fy1 = x0 + dep, y0 + dep, x1 - dep + 1, y1
    fr = 2
    fm = (X >= fx0) & (X < fx1) & (Y >= fy0) & (Y < fy1)
    a[fm] = code(paint, 3)
    gw = (fx1 - fx0 - fr * (cols + 1)) / cols
    gh = (fy1 - fy0 - fr * (rows + 1)) / rows
    panes = []
    for i in range(cols):
        for j in range(rows):
            gx0 = int(round(fx0 + fr + i * (gw + fr)))
            gy0 = int(round(fy0 + fr + j * (gh + fr)))
            gx1, gy1 = int(round(gx0 + gw)), int(round(gy0 + gh))
            panes.append((i, j, gx0, gy0, gx1, gy1))
    big = (X >= fx0 + fr) & (X < fx1 - fr) & (Y >= fy0 + fr) & (Y < fy1 - fr)
    # the room behind the glass (one scene across all panes, the bars over it)
    a[big] = code('void', 1)
    a[big & (Y >= fy0 + (fy1 - fy0) * 0.55)] = code('void', 2)
    if lit:
        a[big] = code('lamp', 3)
        a[big & (Y < fy0 + (fy1 - fy0) * 0.4)] = code('lamp', 4)
    else:
        interior(a, big, fx0 + fr, fy0 + fr, fx1 - fr, fy1 - fr, inside, rng)
        # the sky on the glass: a sheen from the upper west corner in steps, over the room
        u = ((X - fx0) / max(1, fx1 - fx0) + (Y - fy0) / max(1, fy1 - fy0) * 1.3) / 2.3
        a[big & (u < 0.36) & (u >= 0.26)] = code('slate_cool', 2)
        a[big & (u < 0.26) & (u >= 0.16)] = code('sky', 2)
        a[big & (u < 0.16) & (u >= 0.08)] = code('sky', 3)
        a[big & (u < 0.08)] = code('sky', 4)
        # a glint in two-texel steps on the far pane
        gl = big & (np.abs((X - fx0) - (Y - fy0) * 0.6 - (fx1 - fx0) * 0.62) < 1.0) & (Y < fy0 + (fy1 - fy0) * 0.45)
        a[gl] = code('sky', 4)
        # a curtain drawn in the west, its folds
        cw_ = max(3, int((fx1 - fx0) * 0.2))
        cm = big & (X < fx0 + fr + cw_)
        a[cm] = code('berry', 3)
        a[cm & ((X - fx0) % 3 == 0)] = code('berry', 2)
        a[cm & (Y < fy0 + fr + 2)] = code('berry', 4)
    # the bars over the glass, lit on their upper west arrises
    for (i, j, gx0, gy0, gx1, gy1) in panes:
        pass
    bars = fm & ~((X >= fx0 + fr) & (X < fx1 - fr) & (Y >= fy0 + fr) & (Y < fy1 - fr))
    for i in range(1, cols):
        bx = int(round(fx0 + fr + i * (gw + fr) - fr))
        bars |= (X >= bx) & (X < bx + fr) & (Y >= fy0) & (Y < fy1)
    for j in range(1, rows):
        by = int(round(fy0 + fr + j * (gh + fr) - fr))
        bars |= (X >= fx0) & (X < fx1) & (Y >= by) & (Y < by + fr)
    a[bars] = code(paint, 3)
    T_, Lf, B_, R_ = edges(bars)
    a[bars & (T_ | Lf)] = code(paint, 4)
    a[bars & (B_ | R_)] = code(paint, 2)
    # the head's shadow across the top of the glass
    step(a, big & (Y < fy0 + fr + 2), -1)
    # the lintel
    if wall in ('stone', 'ashlar'):
        lw0, lw1 = x0 - q(1.6), x1 + q(1.6)
        k = 0
        x = lw0
        n = max(3, (lw1 - lw0) // q(3.4))
        for i in range(n):
            xa = int(lw0 + (lw1 - lw0) * i / n)
            xb = int(lw0 + (lw1 - lw0) * (i + 1 / 1) / n) - 1
            m = chamfer(q(2.6), xb - xa, 1)
            put(a, xa, y0 - q(2.6), m, 'stone_warm' if i % 2 else 'stone', pillow(m, 3 if i < n * 0.7 else 2, rng, flecks=0))
    else:
        V.beam(a, x0 - q(2), y0 - q(2.4), x1 + q(2), y0, rng, 'timber', 3, hd=True)
        for px_ in (x0 - q(1.2), x1 + q(0.6)):                   # its pegs into the posts
            fill(a, px_, y0 - q(1.6), px_ + 2, y0 - q(1.6) + 2, code('timber', 1))
    # the sill: a stone ledge seen from above the front, its shadow on the wall under it
    V.prism(a, x0 - q(1.4), y1, x1 + q(1.4), y1 + q(1.8), 2, 'stone_warm', 3, side=q(1.0))
    step(a, (X >= x0 - q(0.8)) & (X < x1 + q(1.8)) & (Y >= y1 + q(1.8)) & (Y < y1 + q(1.8) + 3), -1)
    busy = [(x0 - q(1.6), x1 + q(1.6))]
    if shutters:
        sw = int(Wx * 0.45)
        for side, (sx0, sx1) in enumerate(((x0 - sw - 1, x0 - 1), (x1 + 1, x1 + sw + 1))):
            # boards, a ledge top and bottom, a brace between, hinges into the reveal
            xx = sx0
            k = 0
            while xx < sx1:
                bw = min(max(4, sw // 2), sx1 - xx)
                t = (3 if side == 0 else 2) + (1 if k == 0 else 0)
                m = np.ones((y1 - y0, bw), bool)
                tt = np.full(m.shape, t, int)
                tt[:, -1] = t - 2
                tt[:, 0] = min(5, t + 1)
                tt[0, :] = min(5, t + 1)
                tt[-1, :] = t - 2
                for _ in range(2 if bw >= 3 else 0):
                    gy = int(rng.integers(2, max(3, y1 - y0 - 6)))
                    tt[gy:gy + int(rng.integers(3, 6)), int(rng.integers(1, max(2, bw - 1)))] = t - 1
                put(a, xx, y0, m, paint, np.clip(tt, 0, 5))
                xx += bw
                k += 1
            for ly in (y0 + q(1.6), y1 - q(2.8)):
                m = np.ones((q(1.2), sx1 - sx0), bool)
                put(a, sx0, ly, m, paint, pillow(m, 3 if side == 0 else 2, rng, flecks=0, lit_top=1))
            bm = V.seg_mask(a.shape, sx0 + 2, y1 - q(2.8), sx1 - 2, y0 + q(2.8), 1.4) & rect(a, sx0, y0 + q(2.8), sx1, y1 - q(2.8))
            a[bm] = code(paint, 3 if side == 0 else 2)
            a[bm & (Y < y1 - q(2.8) - 1) & ~np.roll(bm, 1, axis=0)] = code(paint, 4)
            hx = sx1 if side == 0 else sx0 - q(2)
            for ly in (y0 + q(1.9), y1 - q(2.5)):
                fill(a, hx - (q(3) if side == 0 else 0), ly, hx + (0 if side == 0 else q(3)) + q(2), ly + 2, code('iron', 1))
                fill(a, hx - (q(3) if side == 0 else 0), ly, hx + (0 if side == 0 else q(3)) + q(2), ly + 1, code('iron', 3))
            # its shade on the wall to the east of it
            step(a, (X >= sx1) & (X < sx1 + 2) & (Y >= y0 + 2) & (Y < y1 + 1) & ~((X >= x0) & (X < x1)), -1)
        busy = [(x0 - sw - q(1.6), x1 + sw + q(1.6))]
    if box:
        by0 = y1 + q(1.8)
        bh = q(3.2)
        bx0, bx1 = x0 - q(1), x1 + q(1)
        # plants first (they rise over the box's back), the box over their stems
        k = 0
        x = bx0 + 2
        while x < bx1 - 3:
            r = rng.uniform(2.4, 3.6)
            m = V.ellipse_mask(a.shape, x + r, by0 - r * 0.4, r, r * 0.85)
            nz = ((X - x - r) / r * -0.6 + (Y - by0 + r * 0.4) / r * -0.8)
            tt = np.where(nz > 0.35, 4, np.where(nz > -0.2, 3, 2))
            a[m] = (FI['leaf'] * 8 + tt)[m]
            if k % 2 == 0:
                f = ('berry', 'brass', 'dusk', 'sky')[int(rng.integers(0, 4))]
                fill(a, int(x + r - 1), int(by0 - r * 1.1), int(x + r + 1), int(by0 - r * 1.1) + 2, code(f, 4))
                fill(a, int(x + r + 1), int(by0 - r * 0.9), int(x + r + 2), int(by0 - r * 0.9) + 2, code(f, 3))
            x += int(r * 1.6)
            k += 1
        for kk in range(2):
            m = np.ones((bh // 2, bx1 - bx0), bool)
            put(a, bx0, by0 + kk * (bh // 2), m, 'timber', pillow(m, 3 - kk, rng, flecks=2, lit_top=1, under=1))
        for ex in (bx0, bx1 - q(1.2)):
            V.beam(a, ex, by0 - 1, ex + q(1.2), by0 + bh + q(1.6), rng, 'timber_cool', 2, hd=True)
        step(a, (X >= bx0 + 2) & (X < bx1 + 2) & (Y >= by0 + bh) & (Y < by0 + bh + q(1.0)), -1)
    return busy


def door(a, cx, B, w, h, paint, rng, wall='stone', arch=False):
    """A ledged door in its frame, set back in the wall: a stone or timber surround and lintel,
    the reveal's shade over its head and down its west side, a lit sliver of the east reveal;
    boards with dark grooves and grain, ledges and a brace, strap hinges with their nails, a ring
    latch at a hand's height, a kick-worn foot; a threshold step proud of the wall."""
    W2, Hd = q(w), q(h)
    x0, x1 = int(cx - W2 / 2), int(cx + W2 / 2)
    y0 = B - Hd
    Y, X = grid(a)
    fr = q(2.2)
    if wall in ('stone', 'ashlar'):
        y = B
        k = 0
        while y > y0 - fr:
            hh = q(rng.uniform(4.2, 6.0))
            for (sx0, sx1, t) in ((x0 - fr - (q(1.2) if k % 2 else 0), x0, 3), (x1, x1 + fr + (q(1.2) if k % 2 == 0 else 0), 2)):
                h_ = min(hh, y - (y0 - fr)) - 1
                if h_ >= 3:
                    m = chamfer(h_, sx1 - sx0, 1)
                    put(a, sx0, y - 1 - h_, m, STONES[k % 3] if wall == 'stone' else 'ashlar', pillow(m, t, rng, flecks=1))
            y -= hh
            k += 1
        if not arch:
            m = chamfer(q(3.0), x1 - x0 + 2 * fr + q(2), 1)
            put(a, x0 - fr - q(1), y0 - fr - q(1.6), m, 'stone_warm', pillow(m, 3, rng, flecks=2))
    else:
        V.beam(a, x0 - fr, y0, x0, B, rng, 'timber', 3, hd=True)
        V.beam(a, x1, y0, x1 + fr, B, rng, 'timber', 2, hd=True)
        V.beam(a, x0 - fr - q(1.5), y0 - fr, x1 + fr + q(1.5), y0, rng, 'timber', 3, hd=True)
    lm = (X >= x0) & (X < x1) & (Y >= y0) & (Y < B)
    if arch:
        r = (x1 - x0) / 2
        ar = (Y < y0 + r) & ((((X + 0.5 - cx) / r) ** 2 + ((Y + 0.5 - y0 - r) / r) ** 2) > 1)
        lm &= ~ar
        # voussoirs round the arch
        for k in range(7):
            a0_ = math.pi * (1 - k / 7)
            a1_ = math.pi * (1 - (k + 1) / 7)
            th = np.arctan2(-(Y + 0.5 - y0 - r), X + 0.5 - cx)
            rr_ = np.hypot(X + 0.5 - cx, Y + 0.5 - y0 - r)
            vm = (rr_ >= r) & (rr_ < r + fr + q(0.6)) & (th <= a0_) & (th > a1_) & (Y < y0 + r + 1)
            if vm.any():
                gap = vm & (np.abs(th - a1_) < 0.06)
                a[vm] = code('ashlar_warm' if k % 2 else 'stone_warm', 4 if k < 4 else 3)
                a[vm & (rr_ >= r + fr - 1)] = code('stone_warm', 2)
                a[vm & (rr_ < r + 1)] = code('stone_warm', 5 if k < 4 else 3)
                a[gap] = code('stone_cool', 1)
    # boards
    nb = max(3, int(round(w / 4.0)))
    bwid = (x1 - x0) / nb
    for i in range(nb):
        xa, xb = int(x0 + i * bwid), int(x0 + (i + 1) * bwid)
        t = 3 if i < nb * 0.6 else 2
        bm = lm & (X >= xa) & (X < xb)
        a[bm] = code(paint, t)
        a[bm & (X == xa)] = code(paint, t + 1)
        a[bm & (X == xb - 1)] = code(paint, 1)
        for _ in range(3):
            gx = int(rng.integers(xa + 2, max(xa + 3, xb - 2)))
            gy = int(rng.integers(y0 + 3, B - q(6)))
            a[lm & (X == gx) & (Y >= gy) & (Y < gy + q(rng.uniform(2, 4)))] = code(paint, t - 1)
    # ledges and a brace (the leaf's own paint, standing proud)
    for yy in (y0 + q(4.5), B - q(7.5)):
        m = lm & (Y >= yy) & (Y < yy + q(1.8))
        a[m] = code(paint, 3)
        a[m & (Y == yy)] = code(paint, 4)
        a[m & (Y == yy + q(1.8) - 1)] = code(paint, 1)
        step(a, lm & (Y == yy + q(1.8)), -1)
    bm = V.seg_mask(a.shape, x0 + 2, B - q(7.5), x1 - 3, y0 + q(6.3), q(0.8)) & lm & (Y > y0 + q(6.3)) & (Y < B - q(7.5))
    a[bm] = code(paint, 3)
    T_, Lf, B_, R_ = edges(bm)
    a[bm & (T_ | Lf)] = code(paint, 4)
    a[bm & (B_ | R_)] = code(paint, 1)
    # the reveal: shade over the head and down the west, a lit sliver of the east reveal
    step(a, lm & (Y < y0 + q(1.4)), -2)
    step(a, lm & (X < x0 + q(1.0)) & (Y >= y0 + q(1.4)), -1)
    fill(a, x1 - 1, y0 + q(1.4), x1, B, code('stone_warm', 4) if wall in ('stone', 'ashlar') else code('timber', 4))
    # strap hinges with their nails, the ring latch and its plate
    for yy in (y0 + q(5.0), B - q(7.0)):
        hm = lm & (X >= x0) & (X < x0 + int(W2 * 0.5)) & (Y >= yy) & (Y < yy + 3)
        hm &= (X < x0 + int(W2 * 0.5) - (Y - yy))
        a[hm] = code('iron', 2)
        a[hm & (Y == yy)] = code('iron', 4)
        for nx in range(x0 + 3, x0 + int(W2 * 0.45), q(2.6)):
            fill(a, nx, yy + 1, nx + 2, yy + 2, code('iron', 5))
    lx, ly = x1 - q(3.4), B - int(Hd * 0.56)
    fill(a, lx - 1, ly - 2, lx + q(1.6) + 1, ly + q(2.0), code('iron', 1))
    fill(a, lx, ly - 1, lx + q(1.6), ly + q(1.6), code('brass', 3))
    fill(a, lx, ly - 1, lx + q(1.0), ly, code('brass', 5))
    fill(a, lx + q(1.6) - 1, ly, lx + q(1.6), ly + q(1.6), code('brass', 2))
    # the foot worn by boots: paint scuffed back a step, a lighter kick
    km = lm & (Y >= B - q(4.0)) & (Y < B - q(1.8)) & ((X + Y) % 4 < 2) & (X > x0 + 2) & (X < x1 - 3)
    step(a, km, +1)
    # the threshold step
    V.prism(a, x0 - fr, B - q(2.0), x1 + fr, B + 1, 2, 'stone_warm', 3, side=q(1.0))
    wm = (X >= cx - q(3)) & (X < cx + q(3)) & (Y == B - q(2.0) + 1)
    a[wm] = code('stone_warm', 3)
    return (x0 - fr - q(1.2), x1 + fr + q(1.2))


def forge_mouth(a, cx, B, w, h, rng):
    """The forge's mouth: an oak lintel on posts over a wide opening; inside, the hearth's brick
    block with its iron hood rising into the dark, the bellows on the west, tongs and hammers
    hung on the back wall, a cinder floor."""
    W2, Hh = q(w), q(h)
    x0, x1 = int(cx - W2 / 2), int(cx + W2 / 2)
    y0 = B - Hh
    Y, X = grid(a)
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < B)
    a[m] = code('soot', 1)
    a[m & (Y < y0 + q(5))] = code('soot', 0)
    # the back wall's courses, barely lit
    for yy in range(y0 + q(6), B - q(2), q(2.6)):
        a[m & (Y == yy) & ((X // q(3)) % 2 == 0)] = code('soot', 2)
    # hearth block
    hx0, hx1 = x0 + int(W2 * 0.3), x1 - int(W2 * 0.16)
    rubble_wall(a, hx0, B - q(11), hx1, B - q(1), rng, fams=('clay', 'clay', 'clay_cool'), course=(2.0, 2.4),
                length=(3.4, 5.0), top=2, moss=0, mortar=('soot', 1), span=(hx0, hx1, B - q(14), B))
    step(a, (X >= hx0) & (X < hx1) & (Y >= B - q(4)) & (Y < B - q(1)), -1)
    fill(a, hx0, B - q(11), hx1, B - q(10.2), code('stone_warm', 4))
    # the hood: a sheet-iron funnel, lit on its west face, a riveted rim
    hc = (hx0 + hx1) / 2
    hm = (Y >= y0 + q(3)) & (Y < B - q(13)) & (np.abs(X + 0.5 - hc) < (hx1 - hx0) / 2 * (0.4 + 0.6 * (Y - y0) / max(1, Hh * 0.55)))
    hm &= m
    rel = (X + 0.5 - hc) / ((hx1 - hx0) / 2)
    tt = np.select([rel < -0.75, rel < -0.35, rel < 0.1, rel < 0.5], [4, 3, 2, 1], 1)
    # riveted plates: a seam every few texels down the funnel, its upper lip lit, rivets along it
    seam = ((Y - y0) % q(3.0) == 0)
    tt = np.where(seam, tt - 1, tt)
    tt = np.where(((Y - y0) % q(3.0) == 1) & (rel < 0.3), tt + 1, tt)
    tt = np.where(seam & ((X % 5) == 0), 4, tt)
    # soot streaks run up from the fire
    tt = np.where(((X // 2) % 4 == 1) & (rel > -0.4) & (Y > y0 + q(6)), tt - 1, tt)
    a[hm] = FI['iron'] * 8 + np.clip(tt, 0, 5)[hm]
    rim = hm & ~np.roll(hm, -2, axis=0)
    a[rim] = code('iron', 3)
    a[rim & ((X % 4) == 0)] = code('iron', 5)
    T_, Lf, _, R_ = edges(hm)
    a[hm & Lf & ~rim] = code('iron', 4)
    a[hm & R_ & ~rim] = code('iron', 0)
    # bellows
    bcx, bcy, brx, bry = x0 + q(5), B - q(8), q(3.4), q(2.4)
    bm = V.ellipse_mask(a.shape, bcx, bcy, brx, bry)
    dd = ((X - bcx) / brx + (Y - bcy) / bry) * 0.7
    a[bm] = FI['timber_cool'] * 8 + np.select([dd < -0.5, dd < 0.1, dd < 0.6], [4, 3, 2], 1)[bm]
    a[bm & (np.abs(((X - bcx) / q(0.9)) % 2 - 1) < 0.3) & (np.abs(Y - bcy) < bry * 0.5)] = code('timber_cool', 1)
    a[bm & (Y < bcy - bry * 0.6)] = code('timber', 4)
    fill(a, x0 + q(8), B - q(8.5), hx0, B - q(7.6), code('iron', 2))
    # tongs and a hammer hung on the back wall, east of the hearth
    tx = hx1 + q(1.2)
    if tx < x1 - q(2):
        for d in (0, 3):
            fill(a, tx + d, y0 + q(7), tx + d + 1, y0 + q(15), code('iron', 2))
        fill(a, tx - 1, y0 + q(6.5), tx + 5, y0 + q(7.2), code('iron', 3))
    # cinders on the floor
    fm = m & (Y >= B - q(1.6))
    a[fm] = code('soot', 2)
    a[fm & ((X * 5 + Y * 3) % 7 < 2)] = code('ash', 2)
    # posts and the lintel
    V.beam(a, x0 - q(3), y0, x0, B, rng, 'timber', 3, hd=True)
    V.beam(a, x1, y0, x1 + q(3), B, rng, 'timber', 2, hd=True)
    V.beam(a, x0 - q(4.5), y0 - q(3.5), x1 + q(4.5), y0, rng, 'timber', 3, hd=True)
    step(a, m & (Y < y0 + q(1.6)), -1)
    # a horseshoe nailed over the lintel for luck
    hsx = int(cx)
    hs = V.ellipse_mask(a.shape, hsx, y0 - q(5.4), q(1.6), q(1.8)) & ~V.ellipse_mask(a.shape, hsx, y0 - q(5.4), q(0.8), q(1.0))
    hs &= Y > y0 - q(6.2)
    a[hs] = code('iron', 3)
    a[hs & (X < hsx)] = code('iron', 4)
    return (x0 - q(4.5), x1 + q(4.5))


def hanging_sign(a, x, y, kind, rng):
    """A board on a wrought bracket from the wall: its edges lit and shaded as a thick board, the
    trade's mark painted on it in three tones, two chains."""
    Y, X = grid(a)
    V.bar(a, x, y, x + q(10), y, max(1.2, q(0.5)), 'iron', 2)
    V.bar(a, x + q(1), y + q(4), x + q(6), y, max(1, q(0.4)), 'iron', 2)
    fill(a, x - 1, y - q(1.6), x + 2, y + q(4.6), code('iron', 1))        # the wall plate
    fill(a, x - 1, y - q(1.6), x, y + q(4.6), code('iron', 3))
    bx0, by0 = x + q(2), y + q(2.4)
    for k in (0, 1):
        cx_ = bx0 + q(1) + k * q(5.6)
        for yy in range(y + 1, by0, 3):
            fill(a, cx_, yy, cx_ + 2, yy + 2, code('iron', 2 + (yy // 3) % 2))
    bw, bh = q(8.4), q(7.0)
    m = chamfer(bh, bw, 1)
    tt = pillow(m, 3, rng, flecks=2, lit_top=1)
    put(a, bx0, by0, m, 'timber', tt)
    # a painted border
    inner = np.zeros((bh, bw), bool)
    inner[2:-2, 2:-2] = True
    ring = inner & ~ndi.binary_erosion(inner)
    put(a, bx0, by0, ring, 'brass', 2)
    cx, cy = bx0 + bw / 2, by0 + bh / 2
    if kind == 'bread':
        lm = V.ellipse_mask(a.shape, cx, cy, q(2.4), q(1.5))
        a[lm] = code('brass_warm', 3)
        a[lm & (Y < cy - 1)] = code('brass_warm', 4)
        a[lm & (X > cx + q(1.2))] = code('brass_warm', 2)
        for k in (-1, 0, 1):
            fill(a, cx + k * q(1.2) - 1, cy - q(0.9), cx + k * q(1.2) + 1, cy - q(0.9) + 2, code('brass_warm', 2))
    elif kind == 'leaf':
        lm = V.ellipse_mask(a.shape, cx, cy, q(1.6), q(2.4))
        a[lm] = code('leaf', 3)
        a[lm & (X < cx)] = code('leaf', 4)
        a[lm & (X > cx + q(0.8))] = code('leaf', 2)
        fill(a, cx - 1, cy - q(2), cx + 1, cy + q(2.4), code('leaf', 1))
    elif kind == 'book':
        fill(a, cx - q(2.4), cy - q(1.8), cx, cy + q(1.8), code('berry', 3))
        fill(a, cx, cy - q(1.8), cx + q(2.4), cy + q(1.8), code('berry', 2))
        fill(a, cx - q(2.4), cy - q(1.8), cx + q(2.4), cy - q(1.8) + 2, code('berry', 4))
        fill(a, cx - 1, cy - q(1.8), cx + 1, cy + q(1.8), code('plaster', 5))
        fill(a, cx - q(2.0), cy + q(1.8) - 2, cx + q(2.0), cy + q(1.8), code('plaster', 4))
    elif kind == 'hammer':
        V.bar(a, cx - q(2), cy + q(2), cx + q(1.2), cy - q(1.2), max(1, q(0.5)), 'timber_warm', 4)
        fill(a, cx - q(0.4), cy - q(2.6), cx + q(2.6), cy - q(0.8), code('iron', 3))
        fill(a, cx - q(0.4), cy - q(2.6), cx + q(2.6), cy - q(2.6) + 2, code('iron', 4))
        fill(a, cx + q(2.0), cy - q(2.6), cx + q(2.6), cy - q(0.8), code('iron', 2))
    # its shadow on the wall behind and below
    step(a, (X >= bx0 + q(1)) & (X < bx0 + bw + q(1.2)) & (Y >= by0 + bh) & (Y < by0 + bh + q(1.2)) & (a // 8 != FI['timber']), -1)


def herb_bundles(a, x0, x1, y, rng):
    """Bunches of herbs hung upside down from a pole under the eave to dry: each tied at the
    stems with twine, its leaves a cluster of three tones, lavender and yarrow among the green."""
    Y, X = grid(a)
    V.beam(a, x0, y, x1, y + q(1.0), rng, 'timber', 2, hd=True)
    x = x0 + q(2)
    k = 0
    while x < x1 - q(3):
        L = q(rng.uniform(4.0, 6.0))
        fam = ('leaf', 'leaf_warm', 'dusk', 'leaf_cool', 'brass')[k % 5]
        fill(a, x + 1, y + q(1.0), x + 3, y + q(1.0) + q(1.4), code('sand', 3))     # twine
        fill(a, x, y + q(1.0) + q(1.4), x + 4, y + q(1.0) + q(1.4) + 2, code('sand_warm', 2))
        cm = V.ellipse_mask(a.shape, x + 2, y + q(1.0) + q(1.4) + L / 2 + 1, q(1.5), L / 2)
        nz = (X - x - 2) / q(1.5) * 0.7 + (Y - y - L / 2) / (L / 2) * 0.3
        tt = np.where(nz < -0.3, 4, np.where(nz < 0.35, 3, 2))
        a[cm] = (FI[fam] * 8 + tt)[cm]
        tips = cm & ((X + Y) % 3 == 0) & (Y > y + q(1.0) + q(1.4) + L * 0.5)
        a[tips] = code(fam, 2)
        x += q(rng.uniform(4.2, 6.0))
        k += 1


def climber(a, x, y_top, B, rng, flowers='berry'):
    """A climbing rose from the foot up the wall: a stem in short runs, leaf clusters along it,
    blooms in pairs."""
    Y, X = grid(a)
    cx, cy = x, B - q(2)
    while cy > y_top:
        nx, ny = cx + int(rng.integers(-q(1.2), q(1.2) + 1)), cy - q(rng.uniform(2.4, 3.6))
        sm = V.seg_mask(a.shape, cx, cy, nx, ny, 0.8)
        a[sm] = code('timber_cool', 2)
        for s in (-1, 1):
            if rng.random() < 0.8:
                lx, ly = nx + s * q(rng.uniform(1.0, 2.2)), ny + q(rng.uniform(-0.6, 0.8))
                lm = V.ellipse_mask(a.shape, lx, ly, q(1.4), q(1.0))
                nz = (X - lx) * -0.6 + (Y - ly) * -0.8
                a[lm] = (FI['leaf'] * 8 + np.where(nz > 1, 4, np.where(nz > -1, 3, 2)))[lm]
                if rng.random() < 0.35:
                    fill(a, lx - 1, ly - 2, lx + 1, ly, code(flowers, 4))
                    fill(a, lx + 1, ly - 1, lx + 2, ly + 1, code(flowers, 3))
        cx, cy = nx, ny


def sack(a, cx, B, rng):
    """A flour sack slumped against the wall by the door, its neck tied, flour dusted on it."""
    V.sack(a, cx, B - q(3.2), q(3.0), q(3.4), 'plaster_warm')
    Y, X = grid(a)
    fill(a, cx - q(1.6), B - q(3.6), cx + q(1.0), B - q(3.0), code('plaster', 5))
    step(a, (X >= cx + q(2.6)) & (X < cx + q(4.0)) & (Y >= B - q(2.6)) & (Y < B), -1)


def downpipe(a, x, top, B, rng):
    """An iron downpipe from the gutter to a shoe over a splash stone: lit west side, dark east,
    clips into the wall, its shade beside it."""
    Y, X = grid(a)
    pw = q(1.6)
    pm = (X >= x) & (X < x + pw) & (Y >= top) & (Y < B - q(1.4))
    u = X - x
    tt = np.select([u < 1, u < pw - 2, u < pw - 1], [4, 3, 2], 1)
    a[pm] = FI['iron'] * 8 + tt[pm]
    for cy in range(top + q(6), B - q(4), q(9)):
        fill(a, x - 1, cy, x + pw + 1, cy + 2, code('iron', 1))
        fill(a, x - 1, cy, x + pw + 1, cy + 1, code('iron', 3))
    step(a, (X >= x + pw) & (X < x + pw + 2) & (Y >= top) & (Y < B - q(1.4)), -1)
    fill(a, x - 2, B - q(1.4) - 1, x + pw + 3, B - q(1.4) + 2, code('iron', 2))
    fill(a, x - 2, B - q(1.4) - 1, x + pw + 3, B - q(1.4), code('iron', 4))
    V.prism(a, x - q(1.2), B - q(1.2), x + pw + q(1.6), B + 1, 1, 'stone_warm', 3, side=1)


# ------------------------------------------------------------------------------------------------
# the building
# ------------------------------------------------------------------------------------------------
TRADE = {'bread': 'bakery', 'leaf': 'herbalist', 'book': 'library', 'hammer': 'smithy'}
INSIDE = {'bakery': 'bread', 'herbalist': 'jars', 'library': 'books'}


def building(spec: dict, seed: int = 0) -> 'V.Built':
    rng = np.random.default_rng(seed)
    w, dep = spec['w'], spec['depth']
    wall_h = spec.get('wall_h', 40)
    roof_h = spec.get('roof_h', round(dep * 0.55 + 10))
    ov = spec.get('overhang', 3)
    chim = max([spec.get('chimney_h', 14)] if spec.get('chimney') else [0])
    pad = 3
    W = q(w + 2 * ov) + 2 * pad
    H = q(wall_h + roof_h + chim + 4) + 2 * pad
    L = pad + q(ov)
    R = L + q(w)
    B = H - pad - 1
    p = V.Pic(W, H, (L + R) // 2, B)
    a = p.a
    y_e = B - q(wall_h)
    y_r = y_e - q(roof_h)
    info = dict(L=L, R=R, B=B, y_e=y_e, y_r=y_r, W=W, H=H)
    trade = TRADE.get((spec.get('sign') or [None, None])[1]) or spec.get('kind')
    span = (L, R, y_e, B)

    # walls ---------------------------------------------------------------------------------------
    wall = spec.get('wall', 'stone')
    fh = q(spec.get('found_h', 4.0))
    if wall == 'stone':
        rubble_wall(a, L, y_e, R, B - fh, rng, span=span)
    elif wall == 'ashlar':
        ashlar_wall(a, L, y_e, R, B - fh, rng, span=span)
    elif wall == 'boards':
        board_wall(a, L, y_e, R, B - fh, rng, span=span)
        for (xa, xb, t) in ((L, L + q(2.6), 3), (R - q(2.6), R, 2)):
            timber(a, xa, y_e, xb, B - fh, rng, 'timber', t)
    else:
        frame_wall(a, spec, L, R, B - fh + q(0.5), y_e, rng, span)
    if spec.get('quoins', wall == 'stone'):
        quoins(a, L, R, B - fh, y_e, rng)
    wall_light(a, L, R, B, y_e, fh)
    plinth(a, L, R, B, rng, fh)

    # openings ------------------------------------------------------------------------------------
    paint = spec.get('paint', 'sky')
    units = spec.get('units') or [[0, w, paint]]
    busy = []
    inside = INSIDE.get(trade, 'home')
    for (ux0, ux1, upaint) in units:
        for wx in spec.get('windows', []):
            if ux0 <= wx < ux1:
                busy += window(a, L + q(wx), B - q(spec.get('win_top', 31)), spec.get('win_w', 13), spec.get('win_h', 13),
                               upaint, rng, wall=wall, shutters=spec.get('shutters', True), box=spec.get('box', False),
                               lit=spec.get('lit', False), inside=inside)
    doors = spec.get('doors', [[spec['door'], paint]] if 'door' in spec else [])
    if spec.get('kind') == 'forge':
        busy.append(forge_mouth(a, L + q(spec['door']), B, spec.get('mouth_w', 30), spec.get('mouth_h', 27), rng))
        info['mouth'] = (L + q(spec['door']), B, q(spec.get('mouth_w', 30)), q(spec.get('mouth_h', 27)))
    else:
        for (dx, dpaint) in doors:
            busy.append(door(a, L + q(dx), B, spec.get('door_w', 16), spec.get('door_h', 26), dpaint, rng, wall=wall,
                             arch=spec.get('arch', False)))

    # the trade's own things on the front
    if trade == 'bakery' and doors:
        dx = L + q(doors[0][0])
        sx = dx - q(spec.get('door_w', 16) / 2) - q(4.6)
        if not any(b0 <= sx + q(3) and sx - q(3) <= b1 for (b0, b1) in busy[:-1]):
            sack(a, sx, B, rng)
    if trade == 'smithy':
        # a quench trough's iron hoops and a rack of bar stock leaning by the mouth
        pass
    if wall == 'frame' and trade not in ('herbalist',) and spec.get('kind') == 'cottage':
        # a climbing rose up whichever end of the front is clear of the door and windows
        for cxr in (L + q(3.5),):
            if not any(b0 - q(2) <= cxr <= b1 + q(2) for (b0, b1) in busy):
                climber(a, cxr, y_e + q(10), B - fh, rng)
                break
    if trade == 'library':
        # ivy up the old stone at the west end, and the library's brass plate by its door
        climber(a, L + q(3.0), y_e + q(6), B - fh, rng, flowers='leaf_cool')
        climber(a, L + q(7.0), y_e + q(16), B - fh, rng, flowers='leaf_cool')
        if doors:
            px = L + q(doors[0][0]) + q(spec.get('door_w', 16) / 2) + q(4.0)
            m = chamfer(q(3.4), q(4.6), 1)
            put(a, px, B - q(19), m, 'brass', pillow(m, 3, rng, flecks=0))
            for k in range(3):
                fill(a, px + 3, B - q(19) + 3 + k * 3, px + q(4.6) - 3, B - q(19) + 4 + k * 3, code('brass', 1))

    # the roof ------------------------------------------------------------------------------------
    hip = q(spec.get('hip', 0))
    rx0, rx1 = L - q(ov), R + q(ov)
    roof = spec.get('roof', 'slate')
    if roof == 'thatch':
        rx0, rx1 = rx0 - q(1.5), rx1 + q(1.5)
        y_eave = y_e + q(4)
        rm = V.roof_mask(a.shape, rx0, rx1, y_r, y_eave, hip=hip, round_=q(5))
        a[rm] = -1
        thatch_roof(a, rm, rx0, rx1, y_r, y_eave, rng, hip=hip)
        thatch_ridge(a, rm, rx0 + hip, rx1 - hip, y_r, rng)
        thatch_eave(a, rm, rx0, rx1, y_eave, rng)
        eave_shadow(a, L, R, y_eave, q(4.4), rng)
        if trade == 'herbalist':
            herb_bundles(a, L + q(4), R - q(26), y_eave + q(0.6), rng)
    else:
        y_eave = y_e + q(0.5)
        rm = V.roof_mask(a.shape, rx0, rx1, y_r, y_eave, hip=hip)
        a[rm] = -1
        fams = ('timber_warm', 'timber', 'timber_cool') if roof == 'shingle' else ('slate', 'slate', 'slate_cool')
        slate_roof(a, rm, rx0, rx1, y_r, y_eave, rng, hip=hip, fams=fams,
                   row=2.8 if roof == 'shingle' else 3.2, width=(3.0, 4.6) if roof == 'shingle' else (3.4, 5.2))
        ridge_tiles(a, rm, rx0 + hip, rx1 - hip, y_r, rng)
        if hip:
            hip_lines(a, rm, rx0, rx1, y_r, y_eave, hip)
        else:
            verges(a, rx0, rx1, y_r, y_eave, rng)
        gb = fascia_gutter(a, rx0, rx1, y_eave, rng, gutter=True)
        eave_shadow(a, L, R, gb, q(4.4), rng)
        # a downpipe on the end of the front with the most clear wall
        cands = [(L + q(1.2), min([abs(L + q(1.2) - (b0 + b1) / 2) - (b1 - b0) / 2 for (b0, b1) in busy] or [99])),
                 (R - q(3.0), min([abs(R - q(3.0) - (b0 + b1) / 2) - (b1 - b0) / 2 for (b0, b1) in busy] or [99]))]
        px, clear = max(cands, key=lambda c: c[1])
        if clear > q(2):
            downpipe(a, int(px), gb - 1, B, rng)
            busy.append((px - q(2), px + q(3)))
    info['roof'] = rm
    info['rx'] = (rx0, rx1)
    info['y_eave'] = y_eave
    for cx in spec.get('chimney', []) or []:
        cw = q(spec.get('chimney_w', 9))
        x0 = L + q(cx) - cw // 2
        wide = trade in ('bakery', 'smithy') or cw >= q(12)
        chimney(a, rm, x0, x0 + cw, y_r - q(chim), y_r + q(roof_h * 0.45), rng, wide=wide,
                soot=1.8 if trade in ('bakery', 'smithy') else 1.0)
    if spec.get('sign'):
        sx, kind = spec['sign']
        hanging_sign(a, L + q(sx), y_eave + q(4.5), kind, rng)
    foot_weeds(a, L, R, B, busy, rng)
    break_runs(a, rng, q(14))
    V.finish(p)
    break_runs(a, rng, q(14))          # the outline's long rows too (the plinth's foot, a thatch's crown)

    # the damage ----------------------------------------------------------------------------------
    dmg = None
    if spec.get('damage'):
        dmg = V.Pic(W, H, p.ax, p.ay)
        damage(dmg.a, a, spec, info, rng)
        V.finish(dmg)
        if not dmg.alpha().any():
            dmg = None
    return V.Built(p, dmg, info)


# ------------------------------------------------------------------------------------------------
# damage
# ------------------------------------------------------------------------------------------------
def scorch(d, base, cx, cy, rx, ry, rng, within):
    """Soot blown out round a hole or an opening: the material under it darkened in drifts of whole
    pieces, densest at the rim and thinning outwards (drawn as the base's own codes stepped down)."""
    Y, X = grid(d)
    r = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
    blot = np.zeros(d.shape, bool)
    for _ in range(9):
        bx, by = cx + rng.uniform(-rx, rx), cy + rng.uniform(-ry * 0.9, ry * 0.3)
        blot |= (((X - bx) / (rx * rng.uniform(0.25, 0.45))) ** 2 + ((Y - by) / (ry * rng.uniform(0.2, 0.4))) ** 2) <= 1
    m = within & (base >= 0) & (base % 8 <= 5) & (d < 0) & (r < 1) & blot
    v = base[m]
    fam = v // 8
    t = v % 8
    rr = r[m]
    dd = np.where(rr < 0.45, 2, 1)
    d[m] = fam * 8 + np.clip(t - dd, 0, 5)
    core = m & (r < 0.3) & ((X // 2 + Y // 2) % 3 == 0)
    d[core] = code('soot', 1)


def roof_hole(d, base, info, cxw, rw, rh, rng):
    """A hole torn through the slates, its edge the ragged line of whole slates broken off course
    by course; inside, the dark of the loft with daylight on its floor, rafters running down the
    slope (one snapped and hanging), battens across (some snapped, splintered ends), broken slates
    hanging askew over the lower rim, scorch round it."""
    rm = info['roof']
    y_r, y_e = info['y_r'], info['y_eave']
    Y, X = grid(d)
    cy = y_r + (y_e - y_r) * 0.5
    rowh = q(3.2)
    # the torn outline, course by course: each course's gap its own width, the edges on slate joints
    m = np.zeros(d.shape, bool)
    yy = int(cy - rh / 2)
    while yy < cy + rh / 2:
        f = (yy + rowh / 2 - cy) / (rh / 2)
        half = rw / 2 * math.sqrt(max(0.0, 1 - f * f)) if abs(f) < 1 else 0
        if half > q(1.5):
            la = cxw - half + rng.integers(-q(1.6), q(1.6) + 1)
            lb = cxw + half + rng.integers(-q(1.6), q(1.6) + 1)
            m |= (X >= la) & (X < lb) & (Y >= yy) & (Y < yy + rowh)
            # a slate snapped across: a triangular bite into the course above
            for _b in range(int(rng.integers(1, 3))):
                bx = rng.uniform(la, lb)
                m |= (Y >= yy - q(1.6)) & (Y < yy) & (np.abs(X - bx) < (Y - (yy - q(1.6))) * 0.9 + 1)
        yy += rowh
    m &= rm & (Y > y_r + q(3))
    if m.sum() < 20:
        return
    ys, xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    # the loft: darkest under the upper rim, the floor below catching the light that falls in
    d[m] = code('void', 0)
    fl = m & (Y > top + (bot - top) * 0.5)
    d[fl] = code('void', 1)
    lit = m & (Y > top + (bot - top) * 0.72) & (X < xs.min() + (xs.max() - xs.min()) * 0.7)
    d[lit] = code('timber_cool', 1)
    d[lit & ((X + Y) % 5 < 2)] = code('timber_cool', 2)
    # rafters down the slope at a carpenter's spacing: squared timbers lit on the west face
    rx_ = xs.min() + q(rng.uniform(1.0, 2.0)) + int((xs.max() - xs.min()) * rng.uniform(0.05, 0.25))
    k = 0
    while rx_ < xs.max() - q(1) and k < 2:
        rwid = q(1.4)
        snapped = True
        # one rafter snapped short near the upper rim, the other broken lower down
        ybot = int(top + (bot - top) * (rng.uniform(0.15, 0.3) if k == 0 else rng.uniform(0.5, 0.7)))
        rmask = m & (X >= rx_) & (X < rx_ + rwid) & (Y < ybot)
        d[rmask] = code('timber', 2)
        d[rmask & (X == rx_)] = code('timber', 4)
        d[rmask & (X == rx_ + 1)] = code('timber', 3)
        d[rmask & (X == rx_ + rwid - 1)] = code('timber', 1)
        step(d, m & (X >= rx_ + rwid) & (X < rx_ + rwid + 2) & (Y < ybot), -1, lo=0)
        if snapped:
            # the broken end hangs down into the loft at an angle, splintered
            ex, ey = rx_ + q(rng.uniform(2.0, 3.5)), ybot + q(rng.uniform(3.0, 5.0))
            sm = V.seg_mask(d.shape, rx_ + rwid / 2, ybot, ex, ey, rwid / 2) & m
            d[sm] = code('timber', 2)
            T_, Lf, _, _ = edges(sm)
            d[sm & (T_ | Lf)] = code('timber', 4)
            fill(d, ex - 2, ey - 1, ex + 1, ey + 1, code('timber_warm', 4))
            fill(d, rx_, ybot - 1, rx_ + rwid, ybot + 1, code('timber_warm', 4))
        rx_ += q(rng.uniform(9.0, 12.0))
        k += 1
    # battens across, on the slate courses: only stubs left at the edges of the hole, snapped and
    # sagging into it at uneven angles (never a whole lattice across the opening)
    by_ = top + q(rng.uniform(1.0, 2.0))
    while by_ < bot - 2:
        row = m & (Y >= by_) & (Y < by_ + 3)
        if row.any():
            rxs = np.nonzero(row.any(0))[0]
            for side in (0, 1):
                if rng.random() < 0.35:
                    continue
                L_ = q(rng.uniform(2.5, 6.0))
                ang = rng.uniform(8, 28)
                if side == 0:
                    sm = V.board(d, rxs.min() - 1, by_, L_, 3, ang, 'timber_cool', 3, rng, split=False, grain=False, where=m)
                else:
                    sm = V.board(d, rxs.max() + 1, by_ + 3, L_, 3, 180 + ang, 'timber_cool', 2, rng, split=False, grain=False, where=m)
                ys_, xs_ = np.nonzero(sm)
                if len(xs_):
                    k_ = np.argmax(xs_) if side == 0 else np.argmin(xs_)
                    fill(d, xs_[k_] - 1, ys_[k_] - 1, xs_[k_] + 1, ys_[k_] + 1, code('timber_warm', 4))
        by_ += rowh
    # the rim: the slates round it cracked, a few hanging askew over the lower edge
    rim = ndi.binary_dilation(m, iterations=2) & ~m & rm
    d[rim & (base >= 0)] = code('slate_cool', 0)
    for _ in range(int(rng.integers(3, 6))):
        hx = int(rng.uniform(xs.min() + 3, xs.max() - 6))
        hy = int(bot - q(rng.uniform(0.4, 1.6)))
        ang = rng.uniform(-35, -10) if rng.random() < 0.5 else rng.uniform(10, 35)
        V.board(d, hx, hy - q(2.6), q(rng.uniform(3.2, 4.6)), q(2.2), ang + 90 if False else ang, 'slate', 3, rng, split=True, grain=False)
    for _ in range(int(rng.integers(2, 4))):
        hx = int(rng.uniform(xs.min(), xs.max()))
        hy = int(top - q(rng.uniform(0.2, 0.8)))
        V.board(d, hx, hy, q(rng.uniform(2.6, 3.8)), q(1.8), rng.uniform(-12, 12), 'slate_cool', 2, rng, split=True, grain=False)
    scorch(d, base, (xs.min() + xs.max()) / 2, (top + bot) / 2, (xs.max() - xs.min()) * 0.95, (bot - top) * 1.15, rng,
           rm & ~m)


def missing_slates(d, base, info, n, rng):
    """Slates gone from the courses: the batten across the gap (lit top, shaded under), the dark
    loft behind, the next slate's butt above throwing its shadow in, a broken corner hanging;
    a few slipped slates lying askew lower down the plane."""
    rm = info['roof']
    rx0, rx1 = info['rx']
    y_r, y_e = info['y_r'], info['y_eave']
    Y, X = grid(d)
    rowh = q(3.2)
    for _ in range(n):
        cx = int(rng.uniform(rx0 + q(4), rx1 - q(10)))
        row = int(rng.integers(1, max(2, (y_e - y_r) // rowh - 1)))
        cy = y_e - row * rowh
        wn = q(rng.choice([4.4, 4.8, 9.2]))
        m = rm & (X >= cx) & (X < cx + wn) & (Y >= cy) & (Y < cy + rowh - 1)
        if rng.random() < 0.4:
            m |= rm & (X >= cx + q(2.4)) & (X < cx + q(2.4) + q(4.6)) & (Y >= cy - rowh) & (Y < cy - 1)
        if not m.any():
            continue
        d[m] = code('void', 1)
        d[m & (Y < cy + q(1.0))] = code('void', 0)
        by_ = cy + rowh // 2
        bt = m & (Y >= by_) & (Y < by_ + 3)
        d[bt] = code('timber_cool', 2)
        d[bt & (Y == by_)] = code('timber_cool', 4)
        d[bt & (Y == by_ + 2)] = code('timber_cool', 0)
        if rng.random() < 0.6:
            kx = int(cx + wn * rng.uniform(0.2, 0.6))
            V.board(d, kx, cy + rowh - q(1.6) - 2, q(2.6), q(1.6), rng.uniform(-25, 25), 'slate', 3, rng, split=False, grain=False)
        # the slate that slipped, lying askew further down
        if rng.random() < 0.6:
            sx, sy = cx + q(rng.uniform(-2, 4)), min(y_e - q(2.6), cy + rowh * rng.integers(1, 3))
            V.board(d, sx, sy, q(rng.uniform(3.6, 4.8)), q(2.4), rng.uniform(-30, 30), 'slate', 3, rng, split=True, grain=False)


def fallen_slates(d, info, rng, n=5, x_range=None):
    """Slates fallen to the foot of the wall and broken there: shards lying flat, lit on top."""
    L, R, B = info['L'], info['R'], info['B']
    xa, xb = x_range or (L, R)
    for _ in range(n):
        sx = int(rng.uniform(xa + q(2), xb - q(4)))
        sy = int(B - q(rng.uniform(0.4, 1.4)))
        V.board(d, sx, sy, q(rng.uniform(2.0, 3.6)), q(1.2), rng.uniform(-20, 20), ('slate', 'slate_cool')[int(rng.integers(0, 2))],
                int(rng.choice([2, 3, 4])), rng, split=False, grain=False)


def boards_over(d, info, x, yt_, ww, hh, rng):
    """Sawn planks nailed across an opening into its frame, the gaps between them showing the
    broken dark behind (shards of glass caught in it), a brace across, forged nails with rust."""
    L, B = info['L'], info['B']
    x0, x1 = L + q(x - ww / 2) - q(2.4), L + q(x + ww / 2) + q(2.4)
    y0, y1 = B - q(yt_), B - q(yt_) + q(hh)
    Y, X = grid(d)
    op = (X >= L + q(x - ww / 2)) & (X < L + q(x + ww / 2)) & (Y >= y0) & (Y < y1 - q(2.5))
    d[op] = code('void', 0)
    d[op & ((X - Y) % 7 == 0) & (Y < y0 + (y1 - y0) * 0.5)] = code('sky', 2)
    yy = y0 + q(0.6)
    k = 0
    while yy < y1 - q(2):
        th = q(rng.uniform(2.6, 3.6))
        ang = rng.uniform(-4, 4)
        over = q(rng.uniform(0, 1.6))
        L_ = (x1 - x0) + over
        xs_ = x0 - int(rng.integers(0, q(1.2) + 1))
        fam = ('timber_warm', 'timber', 'timber_cool')[k % 3]
        V.board(d, xs_, yy, L_, th, ang, fam, int(rng.choice([3, 3, 4, 2])), rng)
        dy = math.tan(math.radians(ang))
        for nx in (xs_ + q(1.2), xs_ + L_ - q(2.4)):
            ny = yy + (nx - xs_) * dy + th / 2 - q(0.5)
            V.nail(d, int(nx), int(ny), rng=rng)
        # the plank's shadow on what lies below it
        sm = (X >= xs_) & (X < xs_ + L_) & (Y >= yy + th) & (Y < yy + th + 2) & (d >= 0) & (d // 8 != FI['iron'])
        step(d, sm, -1)
        yy += th + int(rng.integers(2, q(1.6) + 2))
        k += 1
    dx_, dy_ = (x1 - q(2)) - (x0 + q(2)), (y0 + q(2)) - (y1 - q(3))
    Lb = math.hypot(dx_, dy_)
    V.board(d, x0 + q(2), y1 - q(3), Lb, q(2.6), math.degrees(math.atan2(dy_, dx_)), 'timber_warm', 4, rng)
    for f in (0.08, 0.5, 0.9):
        V.nail(d, int(x0 + q(2) + dx_ * f + q(0.6)), int(y1 - q(3) + dy_ * f + q(0.4)), rng=rng)


def damage(d, base, spec, info, rng):
    L, R, B, y_e, y_r = info['L'], info['R'], info['B'], info['y_e'], info['y_r']
    rx0, rx1 = info['rx']
    order = {'slates': 0, 'crack': 1, 'hole': 2, 'tarp': 3, 'boards': 4, 'scaffold': 5}
    toks = sorted(spec['damage'], key=lambda t: order.get(t[0] if isinstance(t, list) else t, 9))
    slate = spec.get('roof', 'slate') != 'thatch'
    for tok in toks:
        kind = tok[0] if isinstance(tok, list) else tok
        args = tok[1:] if isinstance(tok, list) else []
        if kind == 'hole':
            cx = L + q(args[0]) if args else int(rng.uniform(L + q(8), R - q(8)))
            rw = q(args[1]) if len(args) > 1 else q(14)
            rh = q(args[2]) if len(args) > 2 else int((y_e - y_r) * 0.5)
            if slate:
                roof_hole(d, base, info, cx, rw, rh, rng)
            else:
                thatch_hole(d, base, info, cx, rw, rh, rng)
            fallen_slates(d, info, rng, n=4 if slate else 0, x_range=(cx - rw, cx + rw))
            if not slate:
                straw_heap(d, info, cx, rng)
        elif kind == 'slates':
            n = args[0] if args else 6
            if slate:
                missing_slates(d, base, info, n, rng)
                fallen_slates(d, info, rng, n=3)
        elif kind == 'tarp':
            V.damage(d, base, dict(spec, damage=[tok]), info, rng, hd=True)
        elif kind == 'boards':
            boards_over(d, info, *args, rng)
        elif kind == 'scaffold':
            V.damage(d, base, dict(spec, damage=[tok]), info, rng, hd=True)
        elif kind == 'crack':
            x = L + q(args[0]) if args else (L + R) // 2
            y = y_e + q(4)
            m = np.zeros(d.shape, bool)
            while y < B - q(8):
                nx = x + int(rng.integers(-q(1.6), q(1.6) + 1))
                ny = y + q(rng.uniform(2, 4))
                m |= V.seg_mask(d.shape, x, y, nx, ny, 0.6)
                x, y = nx, ny
            # a crack runs through the masonry and the plaster, never across the timbers
            okf = np.isin(base // 8, [FI[f] for f in ('stone', 'stone_warm', 'stone_cool', 'plaster', 'plaster_warm', 'ashlar', 'ashlar_warm')])
            m &= (base >= 0) & okf
            v = base[m]
            d[m] = (v // 8) * 8 + np.clip(v % 8 - 3, 0, 5)
            lip = np.roll(m, 1, axis=0) & ~m & (base >= 0) & okf
            v = base[lip]
            d[lip] = (v // 8) * 8 + np.clip(v % 8 + 1, 0, 5)


def thatch_hole(d, base, info, cxw, rw, rh, rng):
    """A hole torn in the thatch: a ragged gap wider at the top where the straw was ripped
    away, its rim a fringe of broken straw ends hanging down over the dark of the loft; one rafter
    snapped and hanging at an angle, stubs of the hazel battens, the straw blackened round it."""
    rm = info['roof']
    y_r, y_e = info['y_r'], info['y_eave']
    Y, X = grid(d)
    cy = y_r + (y_e - y_r) * 0.45
    # the gap: lobes torn out along the courses, never a round opening
    m = np.zeros(d.shape, bool)
    for k in range(6):
        bx = cxw + rng.uniform(-rw * 0.3, rw * 0.3)
        by = cy + rng.uniform(-rh * 0.25, rh * 0.25)
        m |= V.ellipse_mask(d.shape, bx, by, q(rng.uniform(2.6, 4.2)), q(rng.uniform(1.6, 2.4)))
    m = ndi.binary_closing(m, iterations=4)
    m &= rm & (Y > y_r + q(5))
    lab, n = ndi.label(m)
    if n > 1:
        m = lab == (1 + int(np.argmax(np.bincount(lab.ravel())[1:])))
    if m.sum() < 20:
        return
    ys, xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    d[m] = code('void', 0)
    d[m & (Y > top + (bot - top) * 0.55)] = code('void', 1)
    # one rafter, snapped, its broken end swung down and east
    rx_ = int(xs.min() + (xs.max() - xs.min()) * rng.uniform(0.2, 0.4))
    yb = int(top + (bot - top) * 0.45)
    rmask = m & (X >= rx_) & (X < rx_ + q(1.4)) & (Y < yb)
    d[rmask] = code('timber', 2)
    d[rmask & (X == rx_)] = code('timber', 4)
    sm = V.seg_mask(d.shape, rx_ + 2, yb, rx_ + q(4.0), yb + q(3.4), 2.0) & m
    d[sm] = code('timber', 2)
    T_, Lf, _, _ = edges(sm)
    d[sm & (T_ | Lf)] = code('timber', 4)
    fill(d, rx_, yb - 1, rx_ + q(1.4), yb + 1, code('timber_warm', 4))
    # batten stubs from the sides, sagging
    for by_ in (top + (bot - top) * 0.3, top + (bot - top) * 0.68):
        rows = np.nonzero((m & (Y >= int(by_)) & (Y < int(by_) + 3)).any(0))[0]
        if len(rows):
            V.board(d, rows.min() - 1, int(by_), q(rng.uniform(2.5, 4.5)), 3, rng.uniform(10, 25), 'timber_cool', 3, rng,
                    split=False, grain=False, where=m)
            V.board(d, rows.max() + 1, int(by_) + 3, q(rng.uniform(2.0, 3.5)), 3, 180 + rng.uniform(10, 25), 'timber_cool', 2, rng,
                    split=False, grain=False, where=m)
    # the fringe: broken straw ends hanging from the upper rim down into the dark, and sticking
    # up from the lower rim, in two-texel strands
    colsx = range(int(xs.min()), int(xs.max()) + 1, 2)
    for x in colsx:
        col = np.nonzero(m[:, x])[0]
        if not len(col):
            continue
        L_ = int(rng.integers(2, 7))
        t = int(rng.choice([2, 3, 3, 4]))
        fill(d, x, col.min(), x + 2, col.min() + L_, code('sand', t))
        fill(d, x, col.min() + L_ - 1, x + 2, col.min() + L_, code('sand', max(1, t - 2)))
        if rng.random() < 0.6:
            L2 = int(rng.integers(2, 5))
            fill(d, x, col.max() - L2 + 1, x + 2, col.max() + 1, code('sand', t))
    scorch(d, base, (xs.min() + xs.max()) / 2, (top + bot) / 2, (xs.max() - xs.min()) * 0.75, (bot - top) * 0.9, rng, rm & ~m)


def straw_heap(d, info, cx, rng):
    """Torn straw fallen to the foot of the wall below the hole."""
    B = info['B']
    Y, X = grid(d)
    for k in range(int(rng.integers(4, 7))):
        sx = int(cx + rng.uniform(-q(6), q(6)))
        sm = V.seg_mask(d.shape, sx, B - 1, sx + q(rng.uniform(-2.5, 2.5)), B - q(rng.uniform(1.0, 2.2)), 0.9)
        d[sm] = code('sand', int(rng.choice([2, 3, 4])))


# ------------------------------------------------------------------------------------------------
# the crater's smoke
# ------------------------------------------------------------------------------------------------
def smoke_column(p, rng):
    """Smoke rising from the crater (village.p_smoke at density 3): a soft column of billows
    leaning east as it climbs, each billow a cluster of round puffs shaded as volumes (lit on the
    upper west, a sooty core shadow low on the east), the lower ones dark and dense with soot,
    the upper ones paler and thinner; the puffs nearer the ground roll over the ones above them
    with a lit crown against the darker smoke behind. Smoke has no ink outline: its edge is its
    own shaded tone, and the column thins out at the top into small trailing puffs."""
    a, cx, yb = p.a, p.ax, p.ay
    H_, W_ = a.shape
    Y, X = np.mgrid[0:H_, 0:W_] + 0.5
    puffs = []
    n = 10
    for k in range(n):
        f = k / (n - 1)
        y = yb - q(2.5 + k * 4.4)
        x = cx + q(0.13 * k * k + 0.5 * k) + rng.uniform(-2, 2)
        R = q(3.2 + 2.6 * math.sin(f * math.pi * 0.85) + 0.6 * f)
        if k == n - 1:
            R = q(3.6)
        for j in range(int(rng.integers(3, 5))):
            px = x + rng.uniform(-0.5, 0.5) * R
            py = y + rng.uniform(-0.3, 0.3) * R
            r = R * rng.uniform(0.5, 0.78)
            puffs.append((k, f, px, py, r))
    # the highest drawn first, so the lower (nearer the source) puffs roll over them
    for (k, f, px, py, r) in sorted(puffs, key=lambda t: t[3]):
        dx, dy = (X - px) / r, (Y - py) / (r * 0.86)
        d2 = dx * dx + dy * dy
        m = d2 <= 1
        if not m.any():
            continue
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        I = V.lam(dx, dy, nz)
        # tone: dense sooty smoke low down, paler ash high up
        v = np.clip(0.45 + 0.95 * (I - 0.4), 0, 1)
        t = -0.2 + 4.4 * v + 0.9 * f
        rim = (d2 > 0.62)
        t = np.where(rim & (I > 0.25), t + 0.8, t)          # the lit rim on the upper west
        t = np.where(rim & (I < -0.1), t - 0.8, t)          # the turned-away edge low on the east
        # under its crown the puff behind is in this one's shade (where it overlaps smoke already drawn)
        behind = m & (a >= 0) & (d2 > 0.7) & (dy < -0.3)
        tt = np.clip(np.round(t), 1, 5).astype(int)
        # low in the column the smoke is thick with soot: its shade in the soot ramp, its light in ash
        sooty = (tt <= 3) if f < 0.3 else ((tt <= 2) if f < 0.65 else (tt <= 1))
        fam = np.where(sooty, FI['soot'], FI['ash'])
        tt = np.where(sooty, np.clip(tt + 2, 2, 5), tt)
        a[m] = (fam * 8 + tt)[m]
        a[behind] = np.where(a[behind] % 8 > 1, a[behind] - 1, a[behind])
        # curls inside the billow: short arcs a tone up on its lit side, a tone down in its shade
        for _ in range(2):
            ax_, ay_ = px + rng.uniform(-0.4, 0.2) * r, py + rng.uniform(-0.4, 0.2) * r
            cr = r * rng.uniform(0.25, 0.4)
            ring = m & (np.abs(np.hypot(X - ax_, (Y - ay_) / 0.86) - cr) < 0.9) & (Y < ay_ + cr * 0.2)
            a[ring] = np.where(a[ring] % 8 < 5, a[ring] + 1, a[ring])
    return V.finish(p, line=False)
