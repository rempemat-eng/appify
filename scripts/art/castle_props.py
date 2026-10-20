"""Props for Hearthold Castle on the headland above the harbour (world-atlas.md).

Big dressed ashlar stones lit from the upper left, crenellations seen from above
(the wall walk shows as a lit strip behind the merlons), slate cones on the round
towers, banners in the castle's sleepy violet and gold. The old ruler set fixed
hours for sleep: the bell tower still rings bedtime. Run directly for a sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import reach_detail as rd  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, WOOD, NAP, GOLD, SLATE, LEAF, RED  # noqa: E402

ASHLAR, IRON = MATERIALS['ashlar'], MATERIALS['iron']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def ashlar(cv: Canvas, x0: int, y0: int, w: int, h: int, seed: int = 0):
    """Large dressed blocks in courses, each lit along its top and left edges."""
    for y in range(y0, y0 + h):
        course = (y - y0) // 6
        off = 7 if course % 2 else 0
        for x in range(x0, x0 + w):
            bx = (x - x0 + off) // 14
            n = noise2(bx, course, 311 + seed)
            base = 3 if n > 0.6 else 2 if n > 0.15 else 4
            cx, cy = (x - x0 + off) % 14, (y - y0) % 6
            c = ASHLAR[base]
            if cy == 5 or cx == 13:
                c = ASHLAR[1]
            elif cy == 0 or cx == 0:
                c = ASHLAR[min(5, base + 1)]
            cv.set(x, y, c)


def crenels(cv: Canvas, x0: int, x1: int, y: int):
    """A battlemented top seen from above: a lit wall walk with merlons standing proud."""
    for x in range(x0, x1):
        for k in range(7):
            cv.set(x, y + k, ASHLAR[4] if k < 2 else ASHLAR[3] if k < 5 else ASHLAR[1])
    for x in range(x0, x1, 8):
        for (mx, my) in rect_set(x, y - 4, 5, 5):
            if mx < x1:
                cv.set(mx, my, ASHLAR[5] if my == y - 4 else ASHLAR[4] if mx < x + 2 else ASHLAR[2])


def banner(cv: Canvas, x: int, y: int, h: int = 22, ramp=NAP, emblem=GOLD):
    """A hanging banner with a swallow-tailed hem and a moon emblem."""
    for yy in range(y, y + h):
        for xx in range(x, x + 9):
            tail = yy > y + h - 4 and (xx - x) in (3, 4, 5) and yy - (y + h - 4) > abs(xx - x - 4) - 1
            if tail:
                continue
            cv.set(xx, yy, ramp[3] if xx < x + 3 else ramp[2] if xx < x + 7 else ramp[1])
    cv.hline(x - 1, y, 11, WOOD[3])
    for (mx, my) in disc(x + 4, y + 8, 2.6):
        cv.set(mx, my, emblem[3])
    for (mx, my) in disc(x + 5, y + 7, 2):
        cv.set(mx, my, ramp[2])


# Hearthold's materials at the detail Matt set (19 Oct: a stone tower with a timber
# storey, as "the level of detail and realism the castle should have"): dressed stone
# laid in irregular courses, every block its own tone, lit along its top and left
# and chipped here and there; slate roofs in single overlapping tiles; oak with grain,
# beam ends and pegs. Cool shade, warm light, from the upper left.
def _shade(cv: Canvas, x: int, y: int, mul=(0.72, 0.7, 0.78)):
    """A hard shadow on what is already drawn (works on padded sprite canvases)."""
    r, g, b, a = cv.get(x, y)
    if a:
        cv.set(x, y, (int(r * mul[0]), int(g * mul[1]), int(b * mul[2]), a))


STONE_R = ['#4A4850', '#6C6869', '#918A82', '#B0A899', '#CBC2AE', '#E2DAC6']
MORTAR = '#6A6461'
SLATE_R = ['#3A3438', '#575052', '#766C69', '#948880', '#B1A496', '#CBBDAC']
OAK = ['#3A261C', '#5A3B28', '#7C5434', '#9C6E44', '#BC8C5A', '#D6AC78']
GLASS = ['#2C3440', '#46566A', '#F2B65A', '#FFDC92', '#FFF0C4']


ROCKS = ((206, 178, 140), (124, 134, 156), (150, 150, 120), (176, 150, 150), None)


def _weather(c, x: int, y: int, xa: int, xb: int, ya: int, yb: int, k: int, j: int, seed: int,
             low: float):
    """A block's own rock and its weather (D13, Eastward's level of detail): each block
    leans to one of several rocks (warm sandstone, blue-grey, green-grey, rose, the plain
    ashlar); moss creeps along the tops of blocks low on a wall and in its shade, lichen
    spots a few, and a hairline crack runs down the odd one."""
    if c == MORTAR:
        return c
    rock = ROCKS[int(noise2(k, j + 91, seed) * len(ROCKS))]
    out = rd.mix(c, rock, 0.22) if rock else rd.rgb(c)
    m = noise2(k, j + 93, seed)
    if m < 0.08 + 0.2 * low and y in (ya, ya + 1) and xa + 1 <= x < min(xb - 1, xa + 3 + int(m * 30)):
        out = (98, 124, 66) if y == ya else (64, 88, 54)          # moss on the block's top
    elif m > 0.94 and y == ya + 2 and xa + 2 <= x <= xa + 3:
        out = (198, 172, 96)                                       # a lichen spot
    if 0.5 < m < 0.6 and xb - xa >= 8 and ya < y < yb - 1 and x == xa + 3 + (y - ya) // 2:
        out = rd.step(out, -2.2)                                   # a hairline crack
    return (*out, 255)


def masonry(cv: Canvas, pts, seed: int = 0, light=None, course=(4, 6), block=(6, 12), soot: int = 0):
    """Lay dressed stone over `pts`: courses of varying height, blocks of varying
    length, each block its own tone. `light(x, y)` (-2..2) shades the wall as a form
    (a drum lit on its left, a face darker toward its foot); every block is lit along
    its top and left, the joints are dark, an odd corner is chipped. `soot`: the bottom
    rows darkened by heat (Hearthold stands in lava)."""
    if not pts:
        return
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    y, k = y0, 0
    while y < y1:
        ch = course[0] + int(noise2(k, 0, seed) * (course[1] - course[0] + 1))
        ya, yb = y, min(y + ch, y1)
        x, j = x0 - int(noise2(k, 1, seed) * block[1]), 0
        while x < x1:
            bw = block[0] + int(noise2(k, j + 2, seed) * (block[1] - block[0] + 1))
            xa, xb = x, x + bw
            t = noise2(k, j + 61, seed)
            tone = 4 if t > 0.86 else 3 if t > 0.35 else 2
            for yy in range(ya, yb):
                for xx in range(max(xa, x0), min(xb, x1)):
                    if (xx, yy) not in pts:
                        continue
                    lt = light(xx, yy) if light else 0
                    base = max(1, min(4, tone + round(lt)))
                    c = STONE_R[base]
                    if yy == yb - 1 or xx == xb - 1:
                        c = MORTAR if base > 2 else STONE_R[max(0, base - 2)]
                    elif yy == ya or xx == xa:
                        c = STONE_R[min(5, base + 1)]
                    elif noise2((xx - xa) // 3, yy, seed + 7 + j) > 0.96:
                        c = STONE_R[max(1, base - 1)]  # the grain of the stone, in short runs
                    if t > 0.8 and (xx, yy) in ((xb - 2, ya), (xb - 3, ya), (xb - 2, ya + 1)):
                        c = STONE_R[max(0, base - 1)]  # a chipped corner
                    if soot and yy >= y1 - soot and rd.smooth_noise(xx, yy, 3, seed + 5) < 0.55:
                        c = STONE_R[max(0, STONE_R.index(c) - 1)] if c in STONE_R else c
                    c = _weather(c, xx, yy, xa, xb, ya, yb, k, j, seed, (yy - y0) / max(1, y1 - y0))
                    cv.set(xx, yy, c)
            x, j = xb, j + 1
        y, k = yb, k + 1


def slates(cv: Canvas, pts, seed: int = 0, light=None, row: int = 4, tile=(5, 8), ridge_y=None):
    """Roof slates over `pts`, in rows that overlap downward: each slate its own tone,
    lit along its top and left, the shadow of the row above along its top edge, a
    dark lower lip where it overhangs the next row."""
    if not pts:
        return
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    for (x, y) in pts:
        r = (y - y0) // row
        ry = (y - y0) % row
        off = (r * 3 + int(noise2(r, 0, seed) * 4)) % 8
        tw = tile[0] + int(noise2(r, (x + off) // 7, seed + 1) * (tile[1] - tile[0] + 1))
        u = (x + off) // tw
        ux = (x + off) % tw
        t = noise2(r, u, seed + 2)
        tone = 3 if t > 0.6 else 2 if t > 0.15 else 4
        lt = light(x, y) if light else 0
        base = max(1, min(4, tone + round(lt)))
        c = SLATE_R[base]
        if ry == row - 1:
            c = SLATE_R[max(0, base - 1)] if ux else SLATE_R[max(0, base - 2)]  # the lower lip
        elif ry == 0:
            c = SLATE_R[max(1, base - 1)]  # the shadow of the row above
        elif ux == 0:
            c = SLATE_R[max(0, base - 2)]  # the gap between two slates
        elif ux == 1 or ry == 1:
            c = SLATE_R[min(5, base + 1)]
        cv.set(x, y, c)


def drum(cv: Canvas, x0: int, y0: int, w: int, h: int, seed: int, slits=(), soot: int = 5):
    """A round tower's drum: stone shaded as a cylinder (lit a third of the way from
    its left, falling dark on the right), its foot curved to the ground, arrow slits
    with lit sills."""
    cx = x0 + (w - 1) / 2
    pts = set()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            sag = 3 * (1 - ((x - cx) / (w / 2)) ** 2)  # the foot curves round the drum
            if y < y0 + h - 3 + sag:
                pts.add((x, y))

    def light(x, y):
        k = (x - x0) / max(1, w - 1)
        return 1.2 - 3.4 * abs(k - 0.28) if k < 0.28 else 1.2 - 3.6 * (k - 0.28)
    masonry(cv, pts, seed, light, course=(4, 6), block=(6, 11), soot=soot)
    for (sx, sy) in slits:
        cv.rect(sx, sy, 2, 8, '#1C1820'); cv.set(sx - 1, sy, STONE_R[1]); cv.hline(sx - 1, sy + 8, 4, STONE_R[4])
    return pts


def cone(cv: Canvas, cx: float, top: int, base: int, half: float, seed: int, finial=True):
    """A conical slate roof: slates in rows that curve round the cone, narrowing toward
    the tip, lit on the left; a deep eave with its shadow on the wall below."""
    pts = set()
    for y in range(top, base + 3):
        hw = half * min(1, (y - top + 1) / max(1, base - top))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            if y > base and abs(x - cx) > hw * (1 - (y - base) * 0.25):
                continue
            pts.add((x, y))
    for (x, y) in pts:
        hw = max(1, half * min(1, (y - top + 1) / max(1, base - top)))
        k = max(-1, min(1, (x - cx) / hw))
        ang = math.asin(k)
        v = (y - top) + 2.2 * (1 - k * k) * (y - top) / max(1, base - top) * 2  # rows bow downward
        r = int(v // 3)
        ry = v % 3
        n = 5 + r  # more slates round the cone lower down
        u = int((ang / math.pi + 0.5) * n + (0.5 if r % 2 else 0))
        t = noise2(r, u, seed)
        lit = -k * 1.6 + 0.4
        base_t = max(1, min(4, (3 if t > 0.55 else 2) + round(lit)))
        c = SLATE_R[base_t]
        if ry >= 2.2:
            c = SLATE_R[max(0, base_t - 2)]
        elif ry < 0.8:
            c = SLATE_R[min(5, base_t + 1)]
        elif int((ang / math.pi + 0.5) * n * 4) % 4 == 0:
            c = SLATE_R[max(0, base_t - 1)]
        if y >= base:
            c = SLATE_R[0] if y > base else SLATE_R[1]  # the eave's underside
        cv.set(x, y, c)
    if finial:
        cv.vline(int(cx), top - 5, 6, IRON[2]); cv.set(int(cx), top - 6, GOLD[4])
    return pts


def battlements(cv: Canvas, x0: int, x1: int, y: int, seed: int = 0):
    """A battlemented parapet in three-quarter view: the merlons' lit tops, their front
    faces in coursed stone, dark embrasures between, and the wall walk's shadow."""
    for x in range(x0, x1):
        cv.set(x, y + 6, STONE_R[1]); cv.set(x, y + 7, MORTAR)
    k = 0
    for mx in range(x0, x1, 9):
        mw = min(6, x1 - mx)
        cv.hline(mx, y, mw, STONE_R[5]); cv.hline(mx, y + 1, mw, STONE_R[4])
        masonry(cv, rect_set(mx, y + 2, mw, 5), seed + k, lambda xx, yy: 0.4 if xx < mx + 2 else -0.4,
                course=(3, 3), block=(3, 6))
        for ex in range(mx + mw, min(mx + 9, x1)):
            cv.set(ex, y + 4, STONE_R[1]); cv.set(ex, y + 5, STONE_R[1])
        k += 1


def keep() -> Canvas:
    """The keep, 128 x 120, in the three-quarter view: a tall slate roof with a stone
    chimney and dormers, a parapet with merlons, the stone hall below with two arched
    windows lit warm behind their mullions, two banners, a great oak door under a little
    slate-roofed porch on posts, and steps down to the yard with a barrel beside them."""
    w, h = 128, 120
    cv = Canvas(w, h, pad=PAD)
    # the roof: one long plane rising away from us, hipped at both ends
    roof = {(x, y) for y in range(6, 34) for x in range(6 + (34 - y) // 3, w - 6 - (34 - y) // 3)}
    slates(cv, roof, 3, lambda x, y: 0.6 - (x - 6) / (w - 12) * 1.4 + (0.6 if y < 10 else 0))
    cv.hline(16, 5, w - 32, SLATE_R[5]); cv.hline(16, 6, w - 32, SLATE_R[4])  # the ridge
    for (cx0, cw) in ((24, 10), (w - 40, 10)):  # dormers
        dpts = rect_set(cx0, 18, cw, 9)
        masonry(cv, dpts, 31 + cx0, lambda x, y: 0.5, course=(3, 3), block=(4, 5))
        cv.rect(cx0 + 3, 21, cw - 6, 5, GLASS[2]); cv.hline(cx0 + 3, 21, cw - 6, GLASS[3]); cv.vline(cx0 + cw // 2, 21, 5, OAK[1])
        for yy in range(14, 19):
            hw = (yy - 13) * 1.1
            for xx in range(int(cx0 + cw / 2 - hw - 1), int(cx0 + cw / 2 + hw + 1)):
                cv.set(xx, yy, SLATE_R[4] if xx < cx0 + cw / 2 else SLATE_R[2])
    chim = rect_set(w - 30, 0, 9, 14)  # the chimney, off the ridge
    masonry(cv, chim, 41, lambda x, y: 0.8 if x < w - 26 else -0.6, course=(3, 4), block=(4, 6))
    cv.hline(w - 31, 0, 11, STONE_R[5]); cv.rect(w - 28, 1, 5, 2, '#1C1820')
    battlements(cv, 3, w - 3, 31, 5)
    cv.hline(3, 39, w - 6, MORTAR)
    # the hall's face, darker toward the foot, soot at the base
    face = rect_set(4, 40, w - 8, h - 50)
    masonry(cv, face, 11, lambda x, y: 0.7 - (x - 4) / (w - 8) * 0.9 - max(0, y - 90) / 20, soot=5)
    for x in range(4, w - 4):  # the parapet's shadow on the face
        _shade(cv, x, 40); _shade(cv, x, 41) if x % 2 else None
    for wx in (14, w - 32):  # tall arched windows in dressed surrounds, warm behind the panes
        win = rect_set(wx, 52, 18, 22) | {(x, y) for (x, y) in disc(wx + 8.5, 52, 9) if y < 52}
        ring = set()
        for (x, y) in win:
            for (ax, ay) in ((-2, 0), (2, 0), (0, -2), (-1, -2), (1, -2), (0, 2)):
                q = (x + ax, y + ay)
                if q not in win:
                    ring.add(q)
        for (x, y) in ring:
            cv.set(x, y, STONE_R[5] if x < wx + 9 and y < 60 else STONE_R[3])
        for (x, y) in win:
            c = GLASS[3] if (x - wx) < 7 else GLASS[2]
            if y > 66:
                c = GLASS[2]
            if (x - wx) % 6 == 5 or (y - 44) % 7 == 6:
                c = OAK[1]  # the leading and the mullions
            cv.set(x, y, c)
        cv.hline(wx - 2, 75, 22, STONE_R[5]); cv.hline(wx - 2, 76, 22, STONE_R[2])  # the sill
    for bx in (40, w - 49):
        banner(cv, bx, 44, 12)  # whole above the porch roof with 2 px clear (Matt, 20 Oct 10:15; Claude A 11:05)
    # the great door, under a porch roof on two oak posts
    door = rect_set(52, 76, 24, 26) | {(x, y) for y in range(66, 76) for x in range(52, 76) if abs(x - 63.5) < (y - 64) * 1.25}
    for (x, y) in door:
        c = OAK[2] if (x - 52) % 6 else OAK[1]
        if (x - 52) % 6 == 1:
            c = OAK[3]
        if noise2(x, y, 77) > 0.9:
            c = OAK[1]  # grain
        cv.set(x, y, c)
    for y in (82, 94):
        cv.hline(53, y, 22, IRON[1]); cv.hline(53, y - 1, 22, IRON[3])
    cv.set(71, 88, GOLD[4]); cv.set(71, 89, GOLD[2])
    for (x, y) in door:
        for (ax, ay) in ((-2, 0), (2, 0), (0, -2)):
            q = (x + ax, y + ay)
            if q not in door and q[1] < 102:
                cv.set(*q, STONE_R[5] if q[0] < 64 else STONE_R[3])
    porch = {(x, y) for y in range(58, 68) for x in range(44 - (y - 58) // 2, 84 + (y - 58) // 2)}
    slates(cv, porch, 17, lambda x, y: 0.5 - (x - 40) / 50, row=3, tile=(4, 6))
    cv.hline(40, 68, 48, OAK[1]); cv.hline(40, 69, 48, OAK[0])
    for px in (44, 81):
        gp.post(cv, px, 69, 102, w=3, ramp=OAK)
    for k, (x0, wd) in enumerate(((46, 36), (42, 44), (38, 52))):  # the steps, each tread lit
        y = 102 + k * 4
        masonry(cv, rect_set(x0, y, wd, 4), 90 + k, lambda xx, yy: 0.8 if yy == y else -0.4, course=(4, 4), block=(7, 11))
        cv.hline(x0, y, wd, STONE_R[5])
    # a barrel by the steps
    for (x, y) in oval(100, 106, 6, 7):
        k2 = (x - 94) / 12
        cv.set(x, y, OAK[4] if k2 < 0.3 else OAK[3] if k2 < 0.6 else OAK[1])
    for yy in (101, 106, 111):
        cv.hline(95, yy, 11, IRON[2])
    for (x, y) in oval(100, 100, 5, 2):
        cv.set(x, y, OAK[2])
    return cv


def round_tower(height: int = 96) -> Canvas:
    """A round wall tower, 48 x 96: a drum of coursed stone shaded as a cylinder, arrow
    slits, a timber hoarding gallery under a conical slate roof with a pennant."""
    w, h = 48, height
    cv = Canvas(w, h, pad=PAD)
    cx = (w - 1) / 2
    drum(cv, 3, 30, w - 6, h - 30, 13 + height, slits=((int(cx), 44), (int(cx) - 8, 64)))
    for x in range(3, w - 3):  # the hoarding: oak boards on beam ends, under the cone
        for y in range(25, 31):
            k = (x - 3) / (w - 7)
            c = OAK[4] if k < 0.25 else OAK[3] if k < 0.55 else OAK[2] if k < 0.8 else OAK[1]
            if (x - 3) % 5 == 0:
                c = OAK[1]
            cv.set(x, y, c)
        if (x - 4) % 7 == 0:  # beam ends below it
            cv.set(x, 31, OAK[3]); cv.set(x, 32, OAK[1]); cv.set(x + 1, 31, OAK[2])
        _shade(cv, x, 31) if (x - 4) % 7 else None
    cone(cv, cx, 8, 25, 24, 23 + height)
    for y in range(3, 7):  # the pennant
        cv.hline(int(cx) + 1, y, 8 - y, NAP[3] if y < 5 else NAP[2])
    return cv


def wall_run(length: int = 96) -> Canvas:
    """A run of curtain wall, 96 x 44: merlons along the walk, the face in coursed
    stone with two arrow slits, soot at its foot where the lava's heat reaches."""
    cv = Canvas(length, 44, pad=PAD)
    battlements(cv, 0, length, 4, 51)
    face = rect_set(0, 12, length, 30)
    masonry(cv, face, 53, lambda x, y: 0.4 - x / length * 0.6 - max(0, y - 34) / 10, soot=4)
    for x in range(length):
        _shade(cv, x, 12)
    for sx in (length // 3, 2 * length // 3):
        cv.rect(sx, 20, 2, 9, '#1C1820'); cv.hline(sx - 1, 29, 4, STONE_R[4])
    return cv


def postern() -> Canvas:
    """The postern in the north curtain wall, 28 x 56: a short gate tower standing a
    course of merlons above the wall run on either side (so its foot meets theirs), with
    merlons along its top, coursed stone, a round arch in dressed voussoirs over a
    passage you walk through, 16 x 32 at the people's scale (verticality.md 5: a single
    door 32 tall for an adult of 25), the lava's glow showing at its far end, the oak door
    swung back against the west reveal (iron straps, a ring), and a lantern on an iron
    bracket beside it, lit."""
    w, h = 28, 56
    cv = Canvas(w, h, pad=PAD)
    battlements(cv, 0, w, 4, 57)
    masonry(cv, rect_set(0, 12, w, 42), 59, lambda x, y: 0.3 - x / w * 0.5 - max(0, y - 46) / 10, soot=4)
    for x in range(w):
        _shade(cv, x, 12)
    # the way in from the north (review 20 Oct 15:53, finding 4: the bridge read as
    # landing on the battlements): where the postern bridge meets the tower its two
    # parapets rise on as the passage's piers, 4 px above the merlons, and between them
    # the bridge runs on into the dark of the passage under the wall walk, under a
    # raised portcullis whose iron teeth hang from the passage's head. The passage
    # comes out at the arch on the yard side below, on the same level.
    ASH = MATERIALS['ash']
    for y in range(0, 12):
        for a in range(24):
            x = 4 + a
            if a < 4 or a >= 20:  # the piers, coursed, lit on the west and shaded on the east
                west = a < 4
                c = ([STONE_R[1], STONE_R[5], STONE_R[4], STONE_R[2]][a] if west
                     else [STONE_R[4], STONE_R[3], STONE_R[2], STONE_R[1]][a - 20])
                if y < 2:
                    c = (STONE_R[5] if y == 0 else STONE_R[4]) if west else (STONE_R[4] if y == 0 else STONE_R[3])
                elif y % 4 == 1 and a not in (0, 23):
                    c = MORTAR
                cv.set(x, y, c)
            elif y >= 4:  # the passage: flags going into the dark
                c = ['#3A2C2A', '#2A1E20', '#241A1C', '#1C1418', '#1C1418', '#1C1418', '#241A1C', '#2A1E20'][y - 4]
                if y == 11 and a % 4 == 1:
                    c = ASH[1]  # a flag's lit edge, far in, where the yard's light reaches
                if y == 4:
                    c = IRON[2] if a % 3 else IRON[3]  # the portcullis's bottom rail
                elif y in (5, 6) and a % 3 == 0:
                    c = IRON[2] if y == 5 else IRON[1]  # its teeth
                cv.set(x, y, c)
    ax0, ax1, spring = 8, 24, 32  # the opening: its sides, and where the arch springs
    cxa, ra = (ax0 + ax1 - 1) / 2, (ax1 - ax0) / 2
    arch = {(x, y) for x in range(ax0, ax1) for y in range(16, h)
            if y >= spring or (x + 0.5 - cxa) ** 2 + ((y - spring) * 1.0) ** 2 <= ra ** 2}
    for (x, y) in arch:
        c = '#1C1418' if y < h - 6 else '#2A1E20'  # the passage, its floor a little lighter
        if y < spring + 5:
            g = (spring + 5 - y) / 9 + 0.25 * (1 - abs(x + 0.5 - cxa) / ra)
            c = '#7A3418' if g > 0.75 else '#5A2414' if g > 0.45 else '#3A1C18' if g > 0.2 else c  # the lava's glow from the far end
        cv.set(x, y, c)
    for (x, y) in arch:  # the voussoirs: wedge stones round the arch, alternately lit
        for (ax, ay) in ((-2, 0), (2, 0), (0, -2), (-1, -2), (1, -2)):
            q = (x + ax, y + ay)
            if q not in arch and 0 <= q[0] < w and 14 <= q[1] < spring + 2:
                v = int((math.atan2(q[1] - spring, q[0] - cxa) + math.pi) * 3)
                lit = q[0] < cxa
                cv.set(*q, (STONE_R[5] if v % 2 else STONE_R[4]) if lit else (STONE_R[3] if v % 2 else STONE_R[2]))
    for y in range(spring - 1, h - 1):  # the door, swung back against the west reveal
        for k in range(3):
            c = OAK[4 - k] if (y // 5) % 2 else OAK[3 - k]
            if noise2(k, y // 3, 67) < 0.25:
                c = rd.step(c, -0.8)  # the oak's grain
            if (y - spring) % 9 == 3:
                c = IRON[3] if k < 2 else IRON[1]  # an iron strap
            elif (y - spring) % 9 == 4:
                c = rd.mix(c, (128, 74, 48), 0.5) if k < 2 else c  # rust bled under it
            rd.put(cv, ax0 + k, y, c)
    cv.set(ax0 + 2, spring + 9, IRON[4]); cv.set(ax0 + 2, spring + 10, IRON[2])  # its ring
    for x in range(ax0 + 3, ax1):  # the threshold, worn
        cv.set(x, h - 2, STONE_R[3] if x % 4 else STONE_R[2])
    # the lantern on its bracket, east of the arch: an iron arm, a cage of glass, a glow
    cv.hline(ax1 + 1, 29, 3, IRON[2]); cv.set(ax1 + 1, 30, IRON[1])
    cv.vline(ax1 + 2, 30, 1, IRON[1])
    for y in range(31, 37):
        for x in range(ax1 + 1, ax1 + 4):
            c = GLASS_L[3] if x == ax1 + 2 and 32 <= y <= 34 else GLASS_L[2]
            if y in (31, 36):
                c = IRON[1]
            cv.set(x, y, c)
    cv.set(ax1 + 2, 37, IRON[2])
    for (x, y) in ((ax1, 34), (ax1 + 4, 33), (ax1 + 4, 35), (ax1 + 2, 38)):  # its light on the stone round it
        r, g, b, a = cv.get(x, y)
        if a:
            cv.set(x, y, (min(255, r + 40), min(255, g + 24), b, a))
    return cv


GLASS_L = ['#2C3440', '#7A3A12', '#F2A048', '#FFE0A0']


def gatehouse() -> Canvas:
    """The gatehouse, 120 x 92: two drum towers with timber hoardings and slate cones
    flanking a battlemented gate, a pointed arch in dressed voussoirs, the portcullis
    raised (its iron teeth showing), the gate leaves folded back and a banner over it."""
    w, h = 120, 92
    cv = Canvas(w, h, pad=PAD)
    battlements(cv, 24, 96, 20, 61)
    face = rect_set(24, 28, 72, h - 31)
    masonry(cv, face, 63, lambda x, y: 0.3 - (x - 24) / 72 * 0.5, soot=4)
    arch = rect_set(46, 56, 28, 33) | {(x, y) for y in range(42, 56) for x in range(46, 74) if abs(x - 59.5) < (y - 40) * 1.0}
    for (x, y) in arch:
        cv.set(x, y, '#241E22' if y > 60 else '#342A2C')
    for x in range(47, 74, 4):  # the raised portcullis teeth
        cv.vline(x, 43, 7, IRON[2]); cv.set(x, 49, IRON[4])
    cv.hline(46, 46, 28, IRON[1])
    for (x, y) in arch:  # the voussoirs round the arch
        for (ax, ay) in ((-3, 0), (3, 0), (0, -3), (-2, -2), (2, -2)):
            q = (x + ax, y + ay)
            if q not in arch and q[1] < 88:
                v = int(math.atan2(q[1] - 56, q[0] - 59.5) * 4)
                cv.set(*q, STONE_R[5] if q[0] < 60 and v % 2 else STONE_R[4] if q[0] < 60 else STONE_R[3] if v % 2 else STONE_R[2])
    for (gx, d) in ((46, 1), (73, -1)):  # the gate leaves, folded back against the passage
        for y in range(60, 88):
            for k in range(3):
                cv.set(gx + d * k, y, OAK[3 - k] if (y // 4) % 2 else OAK[2 - k // 2])
    banner(cv, 56, 25, 13)  # hung from the parapet, whole above the arch's voussoirs (Matt, 20 Oct 10:15)
    for tx in (0, w - 48):
        tw = round_tower(80)
        for y in range(-tw.pad, tw.h):
            for x in range(tw.w):
                c = tw.get(x, y)
                if c[3]:
                    cv.set(tx + x, h - 82 + y, c)
    return cv


def bell_tower() -> Canvas:
    """The bedtime bell tower, 44 x 120: a square stone shaft, a timber belfry jettied
    out on beam ends with louvred openings and the bronze bell inside, a pyramidal
    slate roof with a moon weathervane, and a little oak door at its foot."""
    w, h = 44, 120
    cv = Canvas(w, h, pad=PAD)
    roof = {(x, y) for y in range(6, 30) for x in range(int(22 - 2 - (y - 6) * 0.95), int(22 + 2 + (y - 6) * 0.95) + 1)}
    slates(cv, roof, 71, lambda x, y: 1.0 if x < 21 else -0.8, row=3, tile=(3, 5))
    cv.vline(22, 0, 7, IRON[2])
    for (mx, my) in disc(22, 1, 2.4):
        cv.set(mx, my, GOLD[4])
    for (mx, my) in disc(23, 0, 1.8):
        cv.set(mx, my, (0, 0, 0, 0))
    cv.hline(0, 30, w, SLATE_R[0]); cv.hline(0, 31, w, OAK[0])  # the eave
    # the belfry: oak frame, boards, louvres, the bell
    for y in range(32, 58):
        for x in range(1, w - 1):
            k = (x - 1) / (w - 3)
            c = OAK[4] if k < 0.3 else OAK[3] if k < 0.65 else OAK[2]
            if (x - 1) % 4 == 0:
                c = OAK[1]
            cv.set(x, y, c)
    for px in (1, w // 2 - 1, w - 4):
        gp.post(cv, px, 32, 58, w=3, ramp=OAK)
    cv.hline(1, 32, w - 2, OAK[5]); cv.hline(1, 57, w - 2, OAK[0])
    for (ox_, ow) in ((6, 12), (25, 12)):  # the louvred openings, and the bell behind
        cv.rect(ox_, 36, ow, 18, '#221A1C')
        for y in range(37, 53, 3):
            cv.hline(ox_, y, ow, OAK[2]); cv.hline(ox_, y + 1, ow, OAK[0])
    for (x, y) in oval(22, 46, 6, 7):
        if y > 40:
            cv.set(x, y, '#D8A848' if x < 20 else '#A87428' if x < 25 else '#6E4718')
    for x in range(2, w - 2, 5):  # beam ends under the jetty
        cv.set(x, 58, OAK[4]); cv.set(x + 1, 58, OAK[2]); cv.set(x, 59, OAK[1])
    shaft = rect_set(4, 59, w - 8, h - 61)
    masonry(cv, shaft, 73, lambda x, y: 0.8 - (x - 4) / (w - 8) * 1.4, course=(4, 5), block=(5, 9), soot=5)
    for x in range(4, w - 4):
        _shade(cv, x, 59); _shade(cv, x, 60)
    cv.rect(20, 72, 3, 9, '#1C1820'); cv.hline(19, 81, 5, STONE_R[4])
    door = rect_set(15, h - 21, 14, 18) | {(x, y) for y in range(h - 25, h - 21) for x in range(15, 29) if abs(x - 21.5) < (y - (h - 26)) * 2.2}
    for (x, y) in door:
        cv.set(x, y, OAK[3] if x < 19 else OAK[2] if (x - 15) % 4 else OAK[1])
    for (x, y) in door:
        for (ax, ay) in ((-1, 0), (1, 0), (0, -1)):
            q = (x + ax, y + ay)
            if q not in door and q[1] < h - 3:
                cv.set(*q, STONE_R[5] if q[0] < 22 else STONE_R[3])
    cv.hline(20, h - 12, 3, IRON[3])
    return cv


def herb_bed() -> Canvas:
    """A raised stone bed of castle herbs, 48 x 22: lavender, sage and chamomile in rows."""
    w, h = 48, 22
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rect_set(1, 4, w - 2, 16):
        cv.set(x, y, ASHLAR[3] if y < 7 else ASHLAR[2] if x < 4 or x > w - 5 or y > 16 else '#5A3826')
    cv.hline(1, 4, w - 2, ASHLAR[5])
    for i, x in enumerate(range(6, w - 6, 5)):
        kind = i % 3
        for (px, py) in disc(x, 10, 2.4):
            if kind == 0:
                cv.set(px, py, NAP[3] if (px + py) % 2 else NAP[2])  # lavender
            elif kind == 1:
                cv.set(px, py, '#8FA88A' if py < 10 else '#6E8A6A')  # sage
            else:
                cv.set(px, py, LEAF[3] if (px + py) % 3 else '#F4F0DC')  # chamomile
        cv.set(x, 13, LEAF[1])
    return cv


def training_dummy() -> Canvas:
    """A practice dummy, 26 x 40: a burlap sack stuffed with straw, tied at the waist
    with twine, on a post with a crossbar for arms (straw sticking out of the sleeves)
    and a battered wooden shield; a sack head with a painted face-guard line."""
    BURLAP = ['#5E4A30', '#7E6440', '#A08254', '#BFA06C', '#D8BC88']
    cv = Canvas(26, 40, pad=PAD)
    gp.post(cv, 12, 18, 40, w=3, ramp=WOOD)
    cv.rect(2, 12, 22, 3, WOOD[2]); cv.hline(2, 12, 22, WOOD[4]); cv.hline(2, 14, 22, WOOD[1])  # the arms
    for (sx, d) in ((2, -1), (23, 1)):  # straw out of the sleeves
        for k in range(3):
            cv.set(sx + d * k, 11 + k, '#E2BC5E' if k % 2 else '#C99A3C')
            cv.set(sx + d * k, 15 - k, '#C99A3C')
    for (x, y) in oval(13, 18, 6, 8):  # the stuffed sack
        lit = (x - 13) + (y - 18) * 0.7 < -2
        c = BURLAP[3] if lit else BURLAP[2] if x < 17 else BURLAP[1]
        if (x * 3 + y * 5) % 11 == 0:
            c = BURLAP[4] if lit else BURLAP[3]  # the weave catching the light
        cv.set(x, y, c)
    cv.hline(8, 20, 11, '#7A5A22'); cv.set(9, 21, '#7A5A22')  # twine at the waist
    for (x, y) in disc(13, 6, 4):  # the head, a smaller sack tied at the neck
        cv.set(x, y, BURLAP[4] if x < 12 and y < 6 else BURLAP[3] if x < 15 else BURLAP[2])
    cv.hline(10, 6, 7, RED[2])  # the painted guard line where a helm's slit would be
    cv.hline(11, 10, 5, '#7A5A22')
    for (x, y) in oval(20, 24, 4, 5):  # the shield, dented
        cv.set(x, y, RED[3] if x < 20 else RED[2])
    cv.vline(20, 20, 9, GOLD[3]); cv.set(18, 23, RED[1])
    return cv


def castle_well() -> Canvas:
    """The courtyard well, 30 x 34: a round curb of dressed blocks lit upper left, dark
    water inside, a timber frame with a slate hood, a windlass and a bucket."""
    w, h = 30, 34
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(15, 26, 12, 6):  # the curb, seen from above and in front
        d = math.hypot((x - 15) / 12, (y - 26) / 6)
        if d < 0.62:
            cv.set(x, y, '#16243A' if y < 26 else '#22344E')  # the water, deep
        else:
            k = (x - 3) / 24
            c = ASHLAR[4] if y < 24 and k < 0.6 else ASHLAR[3] if k < 0.7 else ASHLAR[2]
            if (x + (y // 3) * 3) % 6 == 0:
                c = ASHLAR[1]
            cv.set(x, y, c)
    for y in range(26, h - 1):  # its front face
        for x in range(4, 27):
            if ((x - 15) / 12) ** 2 + ((y - 26) / 6) ** 2 > 1 and y > 28:
                continue
            if y > 27:
                k = (x - 4) / 22
                cv.set(x, y, ASHLAR[3] if k < 0.35 else ASHLAR[2] if k < 0.75 else ASHLAR[1])
                if (y - 28) % 3 == 2 or (x + (y // 3) % 2 * 3) % 6 == 0:
                    cv.set(x, y, ASHLAR[1])
    for px in (5, 24):  # the posts
        for y in range(6, 26):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
    for y in range(2, 9):  # the slate hood
        for x in range(2 + (8 - y) // 2, w - 2 - (8 - y) // 2):
            cv.set(x, y, SLATE[3] if x < 15 else SLATE[2])
        cv.set(15, y, SLATE[4])
    cv.hline(3, 9, w - 6, SLATE[1])
    cv.hline(6, 14, 18, WOOD[2]); cv.hline(6, 13, 18, WOOD[3])  # the windlass
    cv.vline(15, 15, 6, '#5E3D2E')
    cv.rect(13, 20, 5, 4, WOOD[2]); cv.hline(13, 20, 5, IRON[3])  # the bucket
    return cv


def archery_butt() -> Canvas:
    """A straw archery butt on a wooden easel, 26 x 34: painted rings, two arrows in it."""
    w, h = 26, 34
    cv = Canvas(w, h, pad=PAD)
    for (x0, x1) in ((6, 3), (20, 23)):
        for t in range(14):
            cv.set(x0 + (x1 - x0) * t // 13, 20 + t, WOOD[3] if x0 < 13 else WOOD[2])
    for (x, y) in disc(13, 14, 10):
        d = math.hypot(x - 13, y - 14)
        c = '#E8DCC8' if d > 8.5 else RED[3] if d > 6 else '#F2EEE6' if d > 4 else '#3E6A8A' if d > 2 else GOLD[4]
        if x > 17 and d > 8.5:
            c = '#C8B898'
        if d > 9.3:
            c = '#C99A3C' if x < 14 else '#A87E2C'  # the straw rim
        cv.set(x, y, c)
    for (ax, ay) in ((10, 11), (16, 17)):
        for t in range(5):
            cv.set(ax - t, ay - t // 2, WOOD[4])
        cv.set(ax - 5, ay - 3, '#F2EEE6'); cv.set(ax - 6, ay - 3, '#F2EEE6')
    return cv


def weapon_rack() -> Canvas:
    """A rack of wooden practice swords and round shields, 36 x 30, for the dummies."""
    w, h = 36, 30
    cv = Canvas(w, h, pad=PAD)
    for px in (3, 31):
        for y in range(8, h - 1):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
    cv.hline(3, 9, 30, WOOD[4]); cv.hline(3, 10, 30, WOOD[2]); cv.hline(3, h - 6, 30, WOOD[2])
    for k in range(4):  # practice swords
        x = 8 + k * 5
        for y in range(4, h - 5):
            cv.set(x, y, WOOD[4] if y < 16 else WOOD[2])
        cv.hline(x - 2, 16, 5, '#5E3D2E')
    for (cx, col) in ((29, NAP), (8, RED)):  # shields leaning at the ends
        for (x, y) in oval(cx, h - 8, 5, 6):
            cv.set(x, y, col[3] if x < cx else col[2])
        cv.set(cx, h - 8, GOLD[4])
    return cv


def stone_bench() -> Canvas:
    """A plain stone bench, 34 x 14: a lit slab on two blocks."""
    w, h = 34, 14
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, 7):
        for x in range(2, w - 2):
            cv.set(x, y, ASHLAR[4] if y < 4 else ASHLAR[3] if x < w - 6 else ASHLAR[2])
    cv.hline(2, 7, w - 4, ASHLAR[1])
    for bx in (5, w - 11):
        for y in range(8, h - 1):
            for x in range(bx, bx + 6):
                cv.set(x, y, ASHLAR[3] if x < bx + 2 else ASHLAR[2] if x < bx + 5 else ASHLAR[1])
    return cv


def banner_pole(wave: int = 0) -> Canvas:
    """A tall pole flying the castle's violet and gold pennant, 18 x 48; `wave` (0 to 2)
    ripples the cloth for the frames it flutters through."""
    w, h = 18, 48
    cv = Canvas(w, h, pad=PAD)
    for y in range(3, h - 1):
        cv.set(4, y, WOOD[3]); cv.set(5, y, WOOD[1])
    for (x, y) in disc(5, 3, 1.5):
        cv.set(x, y, GOLD[4])
    for y in range(6, 22):  # the pennant, tapering
        for x in range(6, 6 + max(2, 11 - abs(y - 10) // 1 if y > 10 else 11)):
            if x > 6 + (22 - y) * 0.75:
                continue
            c = NAP[3] if y < 10 else NAP[2]
            if y in (8, 9):
                c = GOLD[3]
            ripple = round(math.sin((x - 6) / 2.2 + wave * 2.1) * (x - 6) / 8) if wave else 0
            cv.set(x, y + ripple, c)
    return cv


# The castle's dragon (Matt, 18 Oct: "perhaps with a dragon flying around"; his
# reference: a night-blue dragon with pale wings curled round a tower). Scenery only.
DRAGON = ['#141526', '#1F2440', '#2E3660', '#48528A', '#6E7BB8']
MEMBRANE = ['#6A5A48', '#9C8668', '#C9B48E', '#E3D2AE']
HORN = '#E8DFC8'


def _dragon_body(cv: Canvas, cx: float, cy: float, facing: int = 1):
    """Body, neck, head and tail seen from above and a little behind, lit from the upper
    left: night-blue scales with a paler belly line, horns and a gold eye."""
    body = set(oval(cx, cy, 10, 5.5))
    for (x, y) in body:
        lv = -0.55 * (x - cx) / 10 - 0.85 * (y - cy) / 5.5
        cv.set(x, y, DRAGON[4] if lv > 0.55 else DRAGON[3] if lv > 0.0 else DRAGON[2] if lv > -0.6 else DRAGON[1])
    for x in range(int(cx) - 7, int(cx) + 8):  # the pale belly under the lit flank
        cv.set(x, int(cy) + 4, MEMBRANE[2] if x % 3 else MEMBRANE[1])
    # the neck and head, forward and up
    hx, hy = cx + 15 * facing, cy - 5
    for t in range(12):  # the neck rises in a curve from the shoulders to the head
        f = t / 11
        nx = cx + (7 + 8 * f) * facing
        ny = cy - 1 - 4 * math.sin(f * math.pi / 2) - (1 - f) * 0.5
        for (x, y) in disc(nx, ny, 3.0 - f * 1.1):
            cv.set(x, y, DRAGON[4] if y < ny - 1 else DRAGON[3] if y < ny + 0.5 else DRAGON[2])
    for (x, y) in oval(hx, hy, 4.5, 3.2):
        cv.set(x, y, DRAGON[4] if y < hy - 0.5 else DRAGON[3])
    for k in range(4):  # the snout
        cv.set(int(hx + (4 + k) * facing), int(hy) + (1 if k > 1 else 0), DRAGON[3] if k < 3 else DRAGON[2])
    cv.set(int(hx + 1 * facing), int(hy) - 1, '#F2C14E')  # the eye
    for k in range(4):  # two swept horns
        cv.set(int(hx - (2 + k) * facing), int(hy) - 3 - k // 2, HORN)
        cv.set(int(hx - (1 + k) * facing), int(hy) - 2 - k // 2, MEMBRANE[2] if k < 2 else HORN)
    # the tail: shrinking scales curling back
    for t in range(17):
        tx = cx - (9 + t * 1.25) * facing
        ty = cy + 1 + math.sin(t / 3.2) * 3
        for (x, y) in disc(tx, ty, max(1.0, 3.0 - t * 0.13)):
            cv.set(x, y, DRAGON[3] if y < ty - 0.5 else DRAGON[2] if y < ty + 0.5 else DRAGON[1])
    ex, ey = cx - (9 + 17 * 1.25) * facing, cy + 1 + math.sin(17 / 3.2) * 3
    for (x, y) in _poly([(ex + facing, ey), (ex - 3 * facing, ey - 2.5), (ex - 4 * facing, ey + 0.5), (ex - 2 * facing, ey + 2.5)]):
        cv.set(x, y, MEMBRANE[2])  # the spade at its tip


def _poly(points) -> set:
    """The pixels inside a polygon (even-odd scanline fill)."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    out = set()
    for y in range(int(min(ys)), int(max(ys)) + 1):
        cy = y + 0.5
        cross = []
        for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
            if (ay <= cy < by) or (by <= cy < ay):
                cross.append(ax + (cy - ay) * (bx - ax) / (by - ay))
        cross.sort()
        for a, b in zip(cross[::2], cross[1::2]):
            for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                out.add((x, y))
    return out


def _wing(cv: Canvas, shoulder, wrist, tips, trail, near: bool):
    """A bat wing: the arm from the shoulder to the wrist (the leading edge), three
    finger bones fanning from the wrist to the tips, and the skin stretched from the
    tips back to the body (`trail`), scalloped in between each pair of fingers. Pale and
    lit on the near wing, a step darker on the far one."""
    outline = [shoulder, wrist, *tips, trail]
    skin = _poly(outline)
    # scallops: bite a soft curve out of the trailing edge between neighbouring tips
    edge = [*tips, trail]
    for (ax, ay), (bx, by) in zip(edge, edge[1:]):
        mx, my = (ax + bx) / 2, (ay + by) / 2
        # push the bite toward the wing's inside
        ix, iy = (wrist[0] + shoulder[0]) / 2, (wrist[1] + shoulder[1]) / 2
        dx, dy = mx - ix, my - iy
        n = math.hypot(dx, dy) or 1
        r = math.hypot(bx - ax, by - ay) * 0.36
        skin -= set(disc(mx + dx / n * r * 0.55, my + dy / n * r * 0.55, r))
    for (x, y) in skin:
        lit = (x + y) % 4 != 0
        cv.set(x, y, (MEMBRANE[3] if lit else MEMBRANE[2]) if near else (MEMBRANE[2] if lit else MEMBRANE[1]))
    bone = DRAGON[3] if near else DRAGON[2]
    for (a, b) in [(shoulder, wrist), *[(wrist, t) for t in tips]]:
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
        for i in range(n + 1):
            cv.set(int(round(a[0] + (b[0] - a[0]) * i / n)), int(round(a[1] + (b[1] - a[1]) * i / n)), bone)
    cv.set(int(wrist[0]), int(wrist[1]), HORN)  # the wrist claw
    return skin


def dragon(phase: int = 0) -> Canvas:
    """The dragon: perched on the keep, wings folded, head up (phase 0, 56 x 30), or in
    flight with its wings up (1) or down (2), 64 x 44, facing right."""
    if phase == 0:
        cv = Canvas(56, 30, pad=PAD)
        _wing(cv, (30, 16), (26, 6), [(16, 8), (14, 13), (18, 17)], (28, 19), near=False)  # folded, far
        _dragon_body(cv, 32, 19, facing=1)
        _wing(cv, (33, 17), (28, 8), [(19, 11), (18, 16), (23, 20)], (31, 21), near=True)  # folded, near
        return cv
    cv = Canvas(64, 44, pad=PAD)
    if phase == 1:  # wings raised high
        _wing(cv, (28, 19), (24, 6), [(10, 2), (8, 9), (13, 14)], (24, 19), near=False)
        _dragon_body(cv, 32, 23, facing=1)
        _wing(cv, (34, 20), (38, 4), [(26, 1), (22, 7), (26, 13)], (32, 20), near=True)
    else:  # wings swept down
        _wing(cv, (28, 22), (22, 33), [(10, 40), (9, 33), (14, 28)], (24, 24), near=False)
        _dragon_body(cv, 32, 21, facing=1)
        _wing(cv, (34, 24), (36, 37), [(26, 43), (21, 38), (25, 31)], (32, 26), near=True)
    return cv


def _budget(items: dict) -> dict:
    """Every sprite held to the house colour budget (rd.limit_colours)."""
    return {k: rd.limit_colours(v) for k, v in items.items()}


def props() -> dict[str, Canvas]:
    return _budget({
        'keep': keep(), 'round_tower': round_tower(), 'wall_run': wall_run(), 'gatehouse': gatehouse(),
        'postern': postern(),
        'bell_tower': bell_tower(), 'herb_bed': herb_bed(), 'training_dummy': training_dummy(),
        'castle_well': castle_well(), 'archery_butt': archery_butt(), 'weapon_rack': weapon_rack(),
        'stone_bench': stone_bench(), 'banner_pole': banner_pole(),
        'banner_pole_f1': banner_pole(1), 'banner_pole_f2': banner_pole(2),
        'dragon': dragon(0), 'dragon_f1': dragon(1), 'dragon_f2': dragon(2),
    })


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (126, 159, 80, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/castle-props.png'))
    print('sheet', out.size)
