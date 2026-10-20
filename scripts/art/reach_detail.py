"""Surface detail at Eastward's level for Sunstone Reach and space (D13).

Matt, 20 Oct: "Eastward level of detail ... has to be reached" (art-style.md). The shared
ramps hold five or six tones a material; Eastward's wood fronts carry 20 to 27 tones in a
16 x 16 px patch at our character height (detail_bar.py), its stone footings 13 to 24 and
its machinery 24 to 26. A surface reaches that by being made of many small parts, each
with its own colour and its own light: boards of several weathered woods, stones of
several rocks, panels of several metals, and on each part a lit edge, a shadow edge,
grain or chips, and wear in clusters where hands, weather and feet touch.

These painters work in RGB, deriving every tone from a part's base colour by the same
hue-shifted rule as the shared ramps (darker leans cool and purple, lighter leans warm
and yellow), so the parts stay one family. Detail comes in clusters of two or more pixels
(art-style.md: no speckle); the lone pixels are the nail and rivet heads, as in the
references. Light comes from the upper left: a part's top and left edges are lit, its
bottom and right edges dark, and a surface darkens a little towards its east end.

- planks(): boards in rows with staggered butt joints, grain runs, knots, nails with rust
  under them, gaps, splits, sun-bleaching strongest high up, dust and grime at the foot.
- courses(): stones in courses of varied length and rock, lit top-left, dark bottom-right,
  in deep mortar, with chips, cracks, moss in the shade and lichen.
- panels(): metal plates with seams (a dark line and a lit one beside it), rivet rows,
  scuffs, grime and rust streaks in clusters, the odd stencilled band.
- shadow_band(): the shadow an overhang throws on any of these (they are off the ramps, so
  detail.overhang_shadow would skip them).
"""
from __future__ import annotations

import random

from pixel import Canvas, noise2, smooth_noise

WARM = (255, 236, 186)     # the sun's tint for lit tones
COOL = (58, 46, 84)        # the sky's tint for shadows
DUST = (200, 160, 112)     # desert dust at a wall's foot
INSIDE = (38, 26, 24)      # the dark seen through a gap


def rgb(c) -> tuple[int, int, int]:
    if isinstance(c, str):
        c = c.lstrip('#')
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    return tuple(int(v) for v in c[:3])


def mix(a, b, t: float) -> tuple[int, int, int]:
    a, b = rgb(a), rgb(b)
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def step(c, k: float) -> tuple[int, int, int]:
    """k tones lighter (k > 0, toward warm light) or darker (k < 0, toward cool shade)."""
    c = rgb(c)
    if k >= 0:
        return mix(c, WARM, min(0.85, 0.16 * k))
    f = 0.84 ** (-k)
    d = tuple(v * f for v in c)
    return mix(d, COOL, min(0.5, 0.07 * -k))


def put(cv: Canvas, x: int, y: int, c):
    cv.set(x, y, (*rgb(c), 255))


def _bands(pts):
    ys = sorted({y for (_x, y) in pts})
    xs = sorted({x for (x, _y) in pts})
    return xs[0], xs[-1], ys[0], ys[-1]


def planks(cv: Canvas, pts, woods, seed: int = 0, board: int = 4, foot: int | None = None,
           bleach=(222, 210, 190), bleach_top: float = 0.45, nails: bool = True,
           gaps: float = 0.12, vertical: bool = False, light_x: float = 0.10,
           length=(16, 34)):
    """Weathered boards over `pts`. `woods` are the base colours the boards are cut from
    (each board picks one, with a small value change of its own). Rows run along x (or
    along y with `vertical`). `foot` is the row the wall stands on (dust and grime rise
    from it). Sun-bleaching fades the boards toward `bleach`, most at the top."""
    pts = set(pts)
    if not pts:
        return
    x0, x1, y0, y1 = _bands(pts)
    rng = random.Random(seed * 7919 + 13)
    span_a = (x0, x1) if not vertical else (y0, y1)
    rows = {}

    def row(bi):
        if bi not in rows:
            r = random.Random(seed * 1009 + bi * 31 + 7)
            cuts, a = [], span_a[0] - r.randint(0, 14)
            while a <= span_a[1]:
                ln = r.randint(*length)
                cuts.append((a, a + ln, r.randrange(len(woods)), r.uniform(-0.4, 0.4),
                             r.random() < 0.55, r.random() < gaps, r.random() < 0.35,
                             r.randint(3, ln - 3) if ln > 7 else 3, r.random()))
                a += ln
            rows[bi] = cuts
        return rows[bi]

    H = max(1, y1 - y0)
    W = max(1, x1 - x0)
    for (x, y) in pts:
        along, across = (x, y - y0) if not vertical else (y, x - x0)
        bi, r = divmod(across, board)
        cuts = row(bi)
        b = next((c for c in cuts if c[0] <= along < c[1]), cuts[-1])
        a0, a1, fam, val, knot, gap, split, kpos, bl = b
        base = rgb(woods[fam])
        # sun-bleaching: strongest high up, in soft patches, and per board
        hb = (1 - (y - y0) / H) * bleach_top + (smooth_noise(x, y, 9, seed + 3) - 0.5) * 0.35 + bl * 0.25
        c0 = mix(base, bleach, max(0.0, hb) * 0.75)
        c0 = step(c0, val - light_x * 4 * ((x - x0) / W - 0.3))  # the east end a little darker
        c = c0
        pos = along - a0
        inner = 0 < r < board - 1
        if r == 0:
            c = step(c0, -2)            # the shadow under the board above
        elif r == 1:
            c = step(c0, 1.2)           # the board's lit top edge
        elif r == board - 1 and board > 3:
            c = step(c0, -0.6)
        if inner or r == board - 1:
            # grain: runs a few pixels long along the board
            g = noise2((along + r * 3) // 5, bi * 5 + r, seed + 11)
            if g < 0.26:
                c = step(c0, -0.9)
            elif g > 0.88:
                c = step(c0, 0.7)
        if pos == 0 and r > 0:
            c = step(c0, -3)            # the butt joint
        elif pos == 1 and r > 0:
            c = step(c0, 1.4)           # its lit edge
        if nails and pos in (2, a1 - a0 - 2) and r == 2 % board:
            c = (64, 56, 62)            # a nail head
        if nails and pos in (2, a1 - a0 - 2) and r == 3 % board and board > 3:
            c = (124, 78, 54)           # rust run under it
        if knot and pos in (kpos, kpos + 1) and r == board // 2:
            c = step(c0, -2.4)          # a knot
        if knot and pos in (kpos - 1, kpos + 2) and r == board // 2:
            c = step(c0, -1.2)
        if gap and r == board - 1 and kpos <= pos < kpos + 4:
            c = INSIDE                  # a gap between boards, the dark inside showing
        if split and r == board // 2 and (a1 - a0 - 5) <= pos < (a1 - a0 - 2):
            c = step(c0, -2)            # a split running in from the board's end
        if foot is not None and foot - y < 12:
            # dust blown up the wall, in clusters, and grime splashed at the very foot
            n = smooth_noise(x, y, 4, seed + 21)
            k = (12 - (foot - y)) / 12
            if n < 0.25 + 0.45 * k:
                c = mix(c, DUST, 0.35 + 0.25 * k)
            if foot - y < 3 and noise2(x // 2, y, seed + 23) < 0.35:
                c = step(mix(c, DUST, 0.3), -1.5)
        put(cv, x, y, c)


def courses(cv: Canvas, pts, rocks, seed: int = 0, course: int = 5, mortar=None,
            moss=((66, 92, 52), (98, 126, 66)), moss_rate: float = 0.18,
            lichen=(196, 168, 92), foot: int | None = None, min_len: int = 5, max_len: int = 11,
            light_x: float = 0.10):
    """Dressed stones in courses over `pts`. Each stone picks a rock from `rocks`, is lit
    on its top and left edges and dark on its bottom and right, and sits in mortar a
    shade under the rock. Some stones carry a chipped corner, a crack, moss on their top
    in the lower and shaded courses, or a lichen spot."""
    pts = set(pts)
    if not pts:
        return
    x0, x1, y0, y1 = _bands(pts)
    W, H = max(1, x1 - x0), max(1, y1 - y0)
    rows = {}

    def row(ci):
        if ci not in rows:
            r = random.Random(seed * 2003 + ci * 17 + 5)
            cuts, a = [], x0 - r.randint(0, 6)
            while a <= x1:
                ln = r.randint(min_len, max_len)
                cuts.append((a, a + ln, r.randrange(len(rocks)), r.uniform(-0.7, 0.7),
                             r.random(), r.random(), r.random(), r.randint(1, max(1, ln - 3))))
                a += ln
            rows[ci] = cuts
        return rows[ci]

    for (x, y) in pts:
        ci, r = divmod(y - y0, course)
        st = row(ci)
        s = next((c for c in st if c[0] <= x < c[1]), st[-1])
        a0, a1, rock, val, chip, crack, mossy, cpos = s
        base = rgb(rocks[rock])
        mort = rgb(mortar) if mortar else step(base, -2.6)
        c0 = step(base, val - light_x * 4 * ((x - x0) / W - 0.3) + 0.6 * (smooth_noise(x, y, 6, seed) - 0.5))
        c = c0
        p, ln = x - a0, a1 - a0
        last_r = course - 1
        if r == last_r or p == ln - 1:
            c = mort
        elif (r == 0 and p == 0) or (r == last_r - 1 and p == ln - 2):
            c = mort                      # rounded corners
        elif r == 0 or p == 0:
            c = step(c0, 1.3)             # lit top and left edges
        elif r == last_r - 1 or p == ln - 2:
            c = step(c0, -1.3)            # shaded bottom and right edges
        elif r == 1 and p == 1:
            c = step(c0, 2)               # the brightest corner
        if chip < 0.22 and r in (0, 1) and p in (ln - 3, ln - 2):
            c = step(c0, -2.2) if r == 1 else mort      # a chipped corner
        if crack < 0.2 and 0 < r < last_r - 1 and p == cpos + (r % 2):
            c = step(c0, -2.4)            # a hairline crack
        lower = (y - y0) / H
        if mossy < moss_rate * (0.6 + lower) and r in (0, 1) and 1 <= p <= min(ln - 2, 4 + int(mossy * 10)):
            c = moss[1] if r == 0 else moss[0]          # moss on the stone's top
        elif mossy > 0.93 and 1 <= r <= 2 and cpos <= p <= cpos + 1:
            c = lichen
        if foot is not None and foot - y < 8:
            n = smooth_noise(x, y, 4, seed + 31)
            if n < 0.25 + 0.06 * (8 - (foot - y)):
                c = mix(c, DUST, 0.35)
        put(cv, x, y, c)


def panels(cv: Canvas, pts, metals, seed: int = 0, pw: int = 12, ph: int = 9,
           rivets: bool = True, grime=(70, 58, 52), rust=(138, 82, 52), scuffs: float = 0.25,
           stripe=None, foot: int | None = None, light_x: float = 0.12, stagger: bool = True):
    """Metal plates over `pts`, `pw` x `ph`, staggered row to row. Each plate picks a metal
    from `metals`; the seams are a dark line with a lit line after it; rivets run along the
    seams, each a lit head with its shadow; scuffs are short lit scratches; grime gathers
    in clusters low on a plate and round the rivets, and rust runs down from a few."""
    pts = set(pts)
    if not pts:
        return
    x0, x1, y0, y1 = _bands(pts)
    W, H = max(1, x1 - x0), max(1, y1 - y0)
    for (x, y) in pts:
        ri, r = divmod(y - y0, ph)
        off = (pw // 2 if ri % 2 else 0) if stagger else 0
        pi, p = divmod(x - x0 + off, pw)
        rr = random.Random(seed * 4001 + ri * 97 + pi * 13)
        metal, val, scuff, grim, rst = rr.randrange(len(metals)), rr.uniform(-0.5, 0.5), rr.random(), rr.random(), rr.random()
        sx, sy = rr.randint(2, max(2, pw - 5)), rr.randint(2, max(2, ph - 3))
        c0 = step(rgb(metals[metal]), val - light_x * 4 * ((x - x0) / W - 0.3) + 0.4 * (1 - r / ph) - 0.2)
        c = c0
        if r == 0 or p == 0:
            c = step(c0, -2.4)            # the seam
        elif r == 1 or p == 1:
            c = step(c0, 1.3)             # its lit lip
        elif r == ph - 1 or p == pw - 1:
            c = step(c0, -0.9)
        if rivets and r == 2 and (p - 3) % 4 == 0 and 2 < p < pw - 1:
            c = step(c0, 2.2)             # a rivet head
        if rivets and r == 3 and (p - 3) % 4 == 0 and 2 < p < pw - 1:
            c = step(c0, -1.8)            # its shadow
        if scuff < scuffs and r == sy and sx <= p < sx + 3:
            c = step(c0, 1.6)             # a scuff
        if grim < 0.45 and r >= ph - 3 and 2 <= p < pw - 2 and noise2(x // 2, y, seed + 5) < 0.6:
            c = mix(c, grime, 0.45)       # grime gathered low on the plate
        if rst < 0.18 and r >= 4 and p == 3 + 4 * int(rst * 10 % 2):
            c = mix(c, rust, 0.55 if r < ph - 2 else 0.35)    # rust run down from a rivet
        if stripe and r in stripe[1] and ri == stripe[0]:
            c = mix(c, stripe[2], 0.75)
        if foot is not None and foot - y < 6:
            c = mix(c, grime, 0.25 + 0.05 * (6 - (foot - y)))
        put(cv, x, y, c)


def shadow_band(cv: Canvas, x0: int, x1: int, y: int, depth, k: float = 2.0):
    """The band an overhang throws on the wall below it: `depth(x)` rows (deeper to the
    east, where the light falls), darkest in its first row. Works on any colour."""
    for x in range(x0, x1):
        d = depth(x) if callable(depth) else depth
        for i in range(d):
            c = cv.get(x, y + i)
            if not c[3]:
                continue
            put(cv, x, y + i, step(c, -(k + (0.8 if i == 0 else 0)) * (1 - 0.35 * i / max(1, d))))


def darken(cv: Canvas, pts, k: float = 1.0):
    for (x, y) in pts:
        c = cv.get(x, y)
        if c[3]:
            put(cv, x, y, step(c, -k))
