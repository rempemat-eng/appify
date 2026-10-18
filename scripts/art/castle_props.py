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


def keep() -> Canvas:
    """The keep, 128 x 120: a battlemented roof walk seen from above with a slate-capped
    stair turret, an ashlar facade with tall arched windows lit warm, two banners, a
    great door under a pointed arch, and broad steps."""
    w, h = 128, 120
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rect_set(6, 10, w - 12, 22):  # the lead roof inside the battlements, in sheets
        cv.set(x, y, SLATE[1] if x % 10 == 0 else SLATE[3] if x % 10 == 1 else SLATE[2])
    crenels(cv, 4, w - 4, 10)
    crenels(cv, 4, w - 4, 30)
    for y in range(10, 37):
        for x in (4, 5, 6, w - 7, w - 6, w - 5):
            cv.set(x, y, ASHLAR[4] if x < 10 else ASHLAR[1])
    for (x, y) in disc(w - 24, 14, 11):  # the stair turret's slate cone, seen from above
        k = (x - (w - 24)) + (y - 14)
        cv.set(x, y, SLATE[4] if k < -6 else SLATE[3] if k < 2 else SLATE[2] if k < 8 else SLATE[1])
    cv.set(w - 24, 14, GOLD[4])
    ashlar(cv, 4, 37, w - 8, h - 49, seed=1)
    detail.overhang_shadow(cv, 4, w - 4, 37, lambda x: 3, k=2, cap=1)
    for wx in (16, w - 30):  # tall arched windows
        win = rect_set(wx, 50, 14, 22) | {(x, y) for (x, y) in disc(wx + 6.5, 50, 7) if y < 50}
        for (x, y) in win:
            cv.set(x, y, '#FFE7A6' if y < 58 else '#F0B85A')
        for (x, y) in win:
            if (x - 1, y) not in win or (x, y - 1) not in win:
                cv.set(x, y, ASHLAR[1])
        cv.vline(wx + 7, 46, 26, ASHLAR[1]); cv.hline(wx, 60, 14, ASHLAR[1])
    for bx in (38, w - 47):
        banner(cv, bx, 42, 26)
    door = rect_set(50, 74, 28, 28) | {(x, y) for y in range(58, 74) for x in range(50, 78) if abs(x - 63.5) < (y - 56) * 0.95}
    for (x, y) in door:
        cv.set(x, y, WOOD[2] if (x - 50) % 5 else WOOD[1])
    for (x, y) in door:
        for (ax, ay) in ((-2, 0), (2, 0), (0, -2), (-1, -1), (1, -1)):
            q = (x + ax, y + ay)
            if q not in door and q[1] < 102:
                cv.set(*q, ASHLAR[4] if q[0] < 64 else ASHLAR[2])
    for y in (80, 92):
        cv.hline(51, y, 26, IRON[2])
    cv.set(70, 86, GOLD[4])
    for k, (x0, wd) in enumerate(((44, 40), (40, 48), (36, 56))):  # the steps
        y = 102 + k * 4
        for yy in range(y, y + 4):
            cv.hline(x0, yy, wd, ASHLAR[4] if yy == y else ASHLAR[2] if yy < y + 3 else ASHLAR[1])
    detail.stones(cv, 2, h - 6, w - 4, 6, ASHLAR, seed=9, course=3)
    return cv


def round_tower(height: int = 96) -> Canvas:
    """A round wall tower, 48 x 96: a slate cone from above, an ashlar drum shaded as a
    cylinder with arrow slits, and a pennant on the cone's tip."""
    w, h = 48, height
    cv = Canvas(w, h, pad=PAD)
    cx = (w - 1) / 2
    for y in range(26, h - 2):
        for x in range(3, w - 3):
            k = (x - 3) / (w - 6)
            course = (y - 26) // 6
            base = 4 if k < 0.2 else 3 if k < 0.5 else 2 if k < 0.8 else 1
            c = ASHLAR[base]
            if (y - 26) % 6 == 5 or (x + course * 5) % 12 == 0:
                c = ASHLAR[max(0, base - 2)]
            cv.set(x, y, c)
    for sy in (44, 70):
        cv.rect(int(cx) - 1, sy, 3, 9, ASHLAR[0])
    for (x, y) in oval(cx, 22, 22, 9):  # the cone's eave
        if y >= 22:
            cv.set(x, y, SLATE[1])
    for y in range(4, 26):
        half = (y - 3) * 0.95
        for x in range(int(cx - half), int(cx + half) + 1):
            k = (x - cx) / max(1, half)
            band = (y - 4) % 4 == 3
            c = SLATE[4] if k < -0.5 else SLATE[3] if k < 0 else SLATE[2] if k < 0.5 else SLATE[1]
            if band:
                c = SLATE[max(0, SLATE.index(c) - 1)]
            cv.set(x, y, c)
    cv.vline(int(cx), 0, 5, WOOD[2])
    for y in range(0, 5):
        cv.hline(int(cx) + 1, y, 6 - y, NAP[3] if y < 2 else NAP[2])
    return cv


def wall_run(length: int = 96) -> Canvas:
    """A run of curtain wall, 96 x 44: battlements from above, then the ashlar face with
    a drip of moss at its foot."""
    cv = Canvas(length, 44, pad=PAD)
    crenels(cv, 0, length, 6)
    ashlar(cv, 0, 13, length, 29, seed=3)
    detail.overhang_shadow(cv, 0, length, 13, lambda x: 2, k=1, cap=1)
    for x in range(0, length):
        if noise2(x // 3, 0, 312) > 0.5:
            cv.set(x, 41, LEAF[2]); cv.set(x, 40, LEAF[1] if x % 2 else ASHLAR[2])
    return cv


def gatehouse() -> Canvas:
    """The gatehouse, 120 x 92: two drum towers flanking a gate arch with the portcullis
    raised, battlements between them and a banner over the arch."""
    w, h = 120, 92
    cv = Canvas(w, h, pad=PAD)
    crenels(cv, 24, 96, 20)
    ashlar(cv, 24, 27, 72, h - 31, seed=5)
    arch = rect_set(46, 54, 28, 34) | {(x, y) for (x, y) in disc(60, 54, 14) if y < 54}
    for (x, y) in arch:
        cv.set(x, y, '#2A2420' if y > 60 else '#3A3230')
    for x in range(47, 74, 4):  # the raised portcullis teeth
        cv.vline(x, 41, 8, IRON[2]); cv.set(x, 48, IRON[4])
    cv.hline(46, 44, 28, IRON[1])
    for (x, y) in arch:
        for (ax, ay) in ((-2, 0), (2, 0), (0, -2)):
            q = (x + ax, y + ay)
            if q not in arch and q[1] < 88:
                cv.set(*q, ASHLAR[4] if q[0] < 60 else ASHLAR[2])
    banner(cv, 56, 28, 12)
    for tx in (0, w - 48):
        tw = round_tower(80)
        for y in range(tw.h):
            for x in range(tw.w):
                c = tw.get(x, y)
                if c[3]:
                    cv.set(tx + x, h - 82 + y, c)
    return cv


def bell_tower() -> Canvas:
    """The bedtime bell tower, 44 x 120: a square ashlar shaft, an open belfry with a
    bronze bell, a pyramidal slate roof seen from above and a moon weathervane."""
    w, h = 44, 120
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, 30):
        half = 2 + (y - 6) * 0.85
        for x in range(int(22 - half), int(22 + half) + 1):
            cv.set(x, y, SLATE[3] if x < 21 else SLATE[1] if x > 23 else SLATE[4])
    for (mx, my) in disc(22, 3, 2.4):
        cv.set(mx, my, GOLD[4])
    for (mx, my) in disc(23, 2, 1.8):
        cv.set(mx, my, (0, 0, 0, 0))
    ashlar(cv, 4, 30, 36, h - 34, seed=7)
    for (x, y) in rect_set(10, 34, 24, 22):  # the open belfry
        cv.set(x, y, '#2A2420')
    for (x, y) in oval(22, 46, 7, 9):
        if y > 38:
            cv.set(x, y, '#C99A3C' if x < 20 else '#9E6C26' if x < 26 else '#6E4718')
    cv.hline(14, 54, 17, '#6E4718'); cv.set(22, 55, '#3E2812')
    cv.hline(9, 33, 26, WOOD[3])
    for y in (68, 92):
        cv.rect(20, y, 4, 10, ASHLAR[0])
    door = rect_set(16, h - 20, 12, 16)
    for (x, y) in door:
        cv.set(x, y, WOOD[2] if x < 22 else WOOD[1])
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
    """A straw training dummy on a post with a wooden shield, 26 x 40."""
    cv = Canvas(26, 40, pad=PAD)
    gp.post(cv, 12, 18, 40, w=3, ramp=WOOD)
    for (x, y) in oval(13, 14, 7, 9):
        cv.set(x, y, '#E2BC5E' if x < 12 else '#C99A3C' if x < 16 else '#A87E2C')
    for (x, y) in disc(13, 4, 4):
        cv.set(x, y, '#E2BC5E' if x < 13 else '#C99A3C')
    cv.hline(5, 14, 17, '#7A5A22')
    for (x, y) in oval(20, 22, 4, 5):
        cv.set(x, y, RED[3] if x < 20 else RED[2])
    cv.vline(20, 18, 9, GOLD[3])
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


def props() -> dict[str, Canvas]:
    return {
        'keep': keep(), 'round_tower': round_tower(), 'wall_run': wall_run(), 'gatehouse': gatehouse(),
        'bell_tower': bell_tower(), 'herb_bed': herb_bed(), 'training_dummy': training_dummy(),
        'castle_well': castle_well(), 'archery_butt': archery_butt(), 'weapon_rack': weapon_rack(),
        'stone_bench': stone_bench(), 'banner_pole': banner_pole(),
        'banner_pole_f1': banner_pole(1), 'banner_pole_f2': banner_pole(2),
        'dragon': dragon(0), 'dragon_f1': dragon(1), 'dragon_f2': dragon(2),
    }


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
