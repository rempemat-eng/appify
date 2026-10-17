"""Props for Cogsworth Junction, the steampunk railway town (world-atlas.md).

Drawn with the same rules as the valley (detail.py and the hut's steep top-down
roofs): brick walls in soot-red courses, verdigris copper roofs, brass trim and pipes
with lit bands, iron that shows a cool highlight, round windows, warm light inside.
Run directly for a contact sheet: python3 scripts/art/steampunk_props.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, WOOD, STONE, GOLD, NAP, RED, SNOW  # noqa: E402

BRASS, COPPER, IRON, BRICK = (MATERIALS[k] for k in ('brass', 'copper', 'iron', 'brick'))
PAD = 4
WARM = ['#5A3A1E', '#B8782E', '#F0B85A', '#FFE7A6']


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def brick_wall(cv: Canvas, x0: int, y0: int, w: int, h: int, seed: int = 0):
    detail.bricks(cv, x0, y0, w, h, BRICK, seed=seed, base=3)
    for x in range(x0, x0 + w):  # soot gathers low on the wall
        for y in range(y0 + h - 3, y0 + h):
            detail.shade(cv, x, y, 1)


def pipe_v(cv: Canvas, x: int, y0: int, y1: int, ramp=BRASS, w: int = 3):
    """A vertical pipe: lit left edge, dark right, a banded joint every ten pixels."""
    for y in range(y0, y1):
        cv.set(x, y, ramp[4]); cv.set(x + 1, y, ramp[3])
        if w > 2:
            cv.set(x + 2, y, ramp[1])
        if (y - y0) % 10 == 4:
            cv.hline(x - 1, y, w + 2, ramp[2]); cv.set(x - 1, y, ramp[4])


def pipe_h(cv: Canvas, x0: int, x1: int, y: int, ramp=BRASS):
    """A horizontal pipe: lit top, dark underside, flanged joints."""
    for x in range(x0, x1):
        cv.set(x, y, ramp[4]); cv.set(x, y + 1, ramp[3]); cv.set(x, y + 2, ramp[1])
        if (x - x0) % 12 == 6:
            cv.vline(x, y - 1, 5, ramp[2]); cv.set(x, y - 1, ramp[5] if len(ramp) > 5 else ramp[4])


def gear(cv: Canvas, cx: float, cy: float, r: float, ramp=BRASS, teeth: int = 8, hub=True):
    """A gear seen face on: teeth around a lit rim, a dark hub and spokes."""
    body = disc(cx, cy, r)
    for k in range(teeth):
        a = 2 * math.pi * k / teeth
        body |= disc(cx + math.cos(a) * (r + 1.2), cy + math.sin(a) * (r + 1.2), 1.3)
    for (x, y) in body:
        lit = (x - cx) + (y - cy) < 0
        cv.set(x, y, ramp[4] if lit else ramp[2])
    for (x, y) in disc(cx, cy, r - 2):
        cv.set(x, y, ramp[3] if (x - cx) + (y - cy) < 0 else ramp[1])
    if hub:
        for (x, y) in disc(cx, cy, max(1, r / 3)):
            cv.set(x, y, ramp[0])
        cv.set(int(cx) - 1, int(cy) - 1, ramp[4])


def porthole(cv: Canvas, cx: float, cy: float, r: float, warm: bool = True):
    """A round window in a brass ring, glass warm with lamplight, a glint at top left."""
    for (x, y) in disc(cx, cy, r):
        cv.set(x, y, BRASS[3] if (x - cx) + (y - cy) < 0 else BRASS[1])
    for (x, y) in disc(cx, cy, r - 1.6):
        top = y < cy - 1
        cv.set(x, y, (WARM[3] if top else WARM[2]) if warm else (SNOW[1] if top else IRON[1]))
    cv.set(int(cx - r / 2), int(cy - r / 2), '#FFFFFF')


def copper_roof(cv: Canvas, ridge: float, apex_y: int, eave_y: int, left_x: int, right_x: int, hole=frozenset(), seed=81):
    """A verdigris copper roof in the shared top-down roof rule, with standing seams."""
    left, right, edge_y = gp.topdown_roof(cv, ridge, apex_y, eave_y, left_x, right_x, COPPER, hole=hole,
                                          seed=seed, moss=None, barge=BRASS)
    for (x, y) in left | right:
        if (x - int(ridge)) % 5 == 0:
            detail.shade(cv, x, y, -1)  # the seams catch the light
    return left, right, edge_y


def workshop(width: int = 96, sign: str = 'gear') -> Canvas:
    """A tinkerer's workshop, 96 x 86: a copper roof with an iron chimney, a brick gable
    with a brass gear emblem, brick walls, round warm windows, a riveted iron door,
    a brass pipe down the corner and a stone footing."""
    w, h = width, 86
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (w - 1) / 2, 22, 46, 46, 78
    chim = rect_set(w - 26, 6, 9, 16)
    left, right, edge_y = copper_roof(cv, ridge, apex_y, eave_y, 2, w - 3, hole=chim)
    for y in range(6, 24):  # an iron chimney with a cowl
        for x in range(w - 26, w - 17):
            cv.set(x, y, IRON[3] if x < w - 23 else IRON[2] if x < w - 19 else IRON[1])
        if y % 6 == 0:
            cv.hline(w - 27, y, 11, IRON[1])
    cv.rect(w - 28, 4, 13, 3, IRON[3]); cv.hline(w - 28, 4, 13, IRON[4]); cv.rect(w - 24, 5, 5, 1, IRON[0])
    gable = gp.topdown_gable(cv, edge_y, 7, w - 8, apex_y, wall_top, BRICK, boards=False)
    detail.bricks(cv, 7, apex_y, w - 14, wall_top - apex_y, BRICK, seed=3, base=3)
    for x in range(0, w):
        for y in range(0, wall_top):
            if (x, y) not in gable and cv.get(x, y)[:3] == tuple(int(BRICK[3][k:k + 2], 16) for k in (1, 3, 5)):
                pass
    # re-lay the roof over the bricks the helper spilled above the gable line
    left, right, edge_y = copper_roof(cv, ridge, apex_y, eave_y, 2, w - 3, hole=chim)
    if sign == 'gear':
        gear(cv, ridge, 35, 6, BRASS, teeth=9)
    else:
        porthole(cv, ridge, 35, 5)
    brick_wall(cv, 7, wall_top, w - 14, wall_bottom - wall_top, seed=5)
    proud = set()
    for x0 in (7, w - 10):  # iron corner straps with rivets
        for y in range(wall_top - 2, wall_bottom):
            cv.set(x0, y, IRON[3]); cv.set(x0 + 1, y, IRON[2]); cv.set(x0 + 2, y, IRON[1])
            if y % 5 == 0:
                cv.set(x0 + 1, y, BRASS[4])
            proud |= {(x0 + i, y) for i in range(3)}
    dw, dh = 18, 26
    dx0 = int(ridge - dw / 2)
    door = {(x, y) for (x, y) in disc(dx0 + dw / 2, wall_bottom - dh + dw / 2, dw / 2) if y < wall_bottom}
    door |= rect_set(dx0, wall_bottom - dh + dw // 2, dw, dh - dw // 2)
    for (x, y) in door:
        cv.set(x, y, IRON[2] if x < dx0 + dw / 2 else IRON[1])
    for (x, y) in door:
        if (x - 1, y) not in door or (x, y - 1) not in door:
            cv.set(x, y, IRON[3])
    for y in range(wall_bottom - dh + 6, wall_bottom, 6):
        for x in range(dx0 + 2, dx0 + dw - 1, 4):
            cv.set(x, y, BRASS[4])
    cv.set(dx0 + dw - 5, wall_bottom - 12, BRASS[5])
    for (x, y) in door:  # the brick arch round the door
        for ax, ay in ((-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0), (0, -2)):
            if (x + ax, y + ay) not in door and y + ay < wall_bottom:
                cv.set(x + ax, y + ay, BRICK[4] if x + ax < ridge else BRICK[2])
                proud.add((x + ax, y + ay))
    for wx in (20, w - 21):
        porthole(cv, wx, wall_top + 13, 6)
        proud |= disc(wx, wall_top + 13, 6)
    pipe_v(cv, w - 15, wall_top + 2, wall_bottom, BRASS)
    proud |= rect_set(w - 15, wall_top + 2, 3, wall_bottom - wall_top - 2)
    detail.cast(cv, proud, 1, 1, k=1, on=BRICK, reach=2)
    detail.overhang_shadow(cv, 7, w - 7, wall_top, lambda x: 3, k=2, cap=1)
    detail.stones(cv, 5, wall_bottom, w - 10, 8, STONE, seed=17, course=4)
    return cv


def clock_tower() -> Canvas:
    """The junction's clock tower, 48 x 132: a copper spire seen from above, a belfry,
    a big clock face lit from the upper left with brass hands, a brick shaft with a
    round window, and a stone base with steps."""
    w, h = 48, 132
    cv = Canvas(w, h, pad=PAD)
    cx = (w - 1) / 2
    # the spire: a pyramid roof seen steeply from above, two planes and a finial
    for y in range(4, 34):
        half = 2 + (y - 4) * 0.72
        for x in range(int(cx - half), int(cx + half) + 1):
            lit = x < cx
            band = (y - 4) % 6 == 5
            c = COPPER[3 if lit else 1]
            if band:
                c = COPPER[2 if lit else 0]
            if abs(x - cx) < 1:
                c = COPPER[4]
            cv.set(x, y, c)
    cv.vline(int(cx), 0, 5, BRASS[3]); cv.set(int(cx), 0, BRASS[5]); cv.hline(int(cx) - 1, 2, 3, BRASS[4])
    cv.hline(int(cx - 24), 34, 48, BRASS[2]); cv.hline(int(cx - 24), 33, 48, BRASS[4])
    # the belfry
    brick_wall(cv, 6, 35, 36, 14, seed=21)
    for bx in (12, 26):
        for (x, y) in rect_set(bx, 38, 10, 10) | {(x, y) for (x, y) in disc(bx + 4.5, 38, 5) if y < 38}:
            cv.set(x, y, IRON[0])
        cv.vline(bx + 4, 39, 7, BRASS[3]); cv.set(bx + 4, 46, BRASS[4])
    cv.hline(5, 49, 38, STONE[4]); cv.hline(5, 50, 38, STONE[2])
    # the clock
    brick_wall(cv, 6, 51, 36, 66, seed=22)
    for (x, y) in disc(cx, 66, 13):
        cv.set(x, y, BRASS[3] if (x - cx) + (y - 66) < 0 else BRASS[1])
    for (x, y) in disc(cx, 66, 11):
        cv.set(x, y, '#F7EEDC' if (x - cx) + (y - 66) < 4 else '#E3D3B4')
    for k in range(12):
        a = 2 * math.pi * k / 12
        cv.set(int(round(cx + math.cos(a) * 9)), int(round(66 + math.sin(a) * 9)), IRON[1])
    for t in range(1, 7):
        cv.set(int(round(cx + t * 0.15)), 66 - t, IRON[0])  # the minute hand, near twelve
    for t in range(1, 6):
        cv.set(int(round(cx + t * 0.8)), int(round(66 + t * 0.5)), IRON[0])  # the hour hand
    cv.set(int(cx), 66, BRASS[4])
    porthole(cv, cx, 92, 5)
    for (x, y) in rect_set(int(cx) - 1, 82, 3, 3):
        cv.set(x, y, IRON[1])
    pipe_v(cv, 36, 54, 118, BRASS)
    detail.overhang_shadow(cv, 6, 42, 51, lambda x: 2, k=1, cap=1)
    # the base and steps
    detail.stones(cv, 3, 116, 42, 10, STONE, seed=23, course=4)
    for (x0, y, wd) in ((13, 126, 22), (11, 129, 26)):
        cv.hline(x0, y, wd, STONE[4]); cv.hline(x0, y + 1, wd, STONE[3]); cv.hline(x0, y + 2, wd, STONE[1])
    dx = int(cx) - 6
    for (x, y) in rect_set(dx, 106, 12, 10) | {(x, y) for (x, y) in disc(dx + 5.5, 106, 6) if y < 106}:
        cv.set(x, y, WOOD[1] if x > cx else WOOD[2])
    return cv


def locomotive() -> Canvas:
    """A little steam engine on the rails, 104 x 50, side on and seen a little from
    above: a dark iron boiler with brass bands, a tall stack, a red cab with a warm
    window, red spoked wheels and a cowcatcher."""
    w, h = 104, 50
    cv = Canvas(w, h, pad=PAD)
    # the boiler, a cylinder lit along its top
    for x in range(18, 74):
        for y in range(16, 36):
            k = y - 16
            c = IRON[4] if k < 3 else IRON[3] if k < 8 else IRON[2] if k < 14 else IRON[1]
            cv.set(x, y, c)
        if (x - 18) % 14 == 4:
            for y in range(15, 37):
                cv.set(x, y, BRASS[4] if y < 20 else BRASS[3] if y < 30 else BRASS[1])
    for (x, y) in oval(18, 26, 4, 10):  # the smokebox door
        cv.set(x, y, IRON[2] if x < 17 else IRON[1])
    porthole(cv, 15, 26, 3, warm=False)
    # the stack and the dome
    for y in range(2, 17):
        hw = 4 if y > 6 else 6
        for x in range(28 - hw, 28 + hw + 1):
            cv.set(x, y, IRON[3] if x < 27 else IRON[1])
    cv.hline(22, 2, 13, IRON[4])
    for (x, y) in oval(52, 15, 5, 4):
        if y <= 15:
            cv.set(x, y, BRASS[4] if x < 52 else BRASS[2])
    # the cab
    for x in range(72, 98):
        for y in range(8, 38):
            cv.set(x, y, RED[3] if x < 76 else RED[2] if y > 12 else RED[4])
    cv.rect(70, 5, 30, 4, IRON[3]); cv.hline(70, 5, 30, IRON[4]); cv.hline(70, 8, 30, IRON[1])
    for (x, y) in rect_set(78, 14, 14, 10):
        cv.set(x, y, WARM[3] if y < 18 else WARM[2])
    cv.rect(77, 13, 16, 1, BRASS[4]); cv.vline(85, 14, 10, BRASS[2])
    # the frame, wheels and cowcatcher
    cv.rect(8, 36, 92, 4, IRON[1]); cv.hline(8, 36, 92, IRON[3])
    for (wx, r) in ((30, 8), (52, 8), (86, 6)):
        for (x, y) in disc(wx, 42, r):
            cv.set(x, y, RED[2] if (x - wx) + (y - 42) < 0 else RED[1])
        for (x, y) in disc(wx, 42, r - 2):
            cv.set(x, y, IRON[1])
        for k in range(6):
            a = math.pi * k / 3
            for t in range(1, r - 1):
                cv.set(int(round(wx + math.cos(a) * t)), int(round(42 + math.sin(a) * t)), RED[3])
        cv.set(wx, 42, BRASS[4])
    cv.hline(30, 41, 23, IRON[3])  # the coupling rod
    for i in range(7):
        cv.vline(2 + i * 2, 38 + i // 3, 10 - i, IRON[3] if i % 2 else IRON[2])
    return cv


def gas_lamp() -> Canvas:
    """A brass gas lamp, 16 x 48: an iron post with a ring, a glass lantern lit warm."""
    cv = Canvas(16, 48, pad=PAD)
    for y in range(16, 46):
        cv.set(7, y, IRON[3]); cv.set(8, y, IRON[2]); cv.set(9, y, IRON[1])
    cv.rect(5, 44, 7, 3, IRON[2]); cv.hline(5, 44, 7, IRON[3])
    for (x, y) in oval(8, 26, 3, 1.4):
        cv.set(x, y, BRASS[3])
    for y in range(4, 15):
        for x in range(4, 13):
            cv.set(x, y, WARM[3] if x < 8 and y < 10 else WARM[2])
    cv.rect(3, 2, 11, 2, BRASS[3]); cv.hline(3, 2, 11, BRASS[4]); cv.set(8, 0, BRASS[4]); cv.set(8, 1, BRASS[3])
    cv.rect(3, 15, 11, 2, BRASS[2]); cv.vline(3, 4, 11, BRASS[2]); cv.vline(13, 4, 11, BRASS[1]); cv.vline(8, 4, 11, BRASS[2])
    return cv


def steam_puff(size: int = 22) -> Canvas:
    """A puff of steam: soft overlapping balls lit from the upper left."""
    cv = Canvas(size, size, pad=PAD)
    for (bx, by, r) in ((size * 0.35, size * 0.6, size * 0.28), (size * 0.6, size * 0.45, size * 0.3), (size * 0.45, size * 0.3, size * 0.22)):
        for (x, y) in disc(bx, by, r):
            cv.set(x, y, SNOW[3] if (x - bx) + (y - by) < -1 else SNOW[2] if (x - bx) + (y - by) < 2 else SNOW[1])
    return cv


def pipe_run(length: int = 64) -> Canvas:
    """Pipes along the ground with a valve wheel, 64 x 18."""
    cv = Canvas(length, 18, pad=PAD)
    pipe_h(cv, 0, length, 8, BRASS)
    pipe_h(cv, 0, length, 13, IRON + [IRON[4]])
    for vx in (length // 3, 2 * length // 3):
        cv.vline(vx, 3, 6, IRON[2])
        for (x, y) in disc(vx, 3, 3):
            if (x - vx) ** 2 + (y - 3) ** 2 >= 4:
                cv.set(x, y, RED[3] if x < vx else RED[2])
    return cv


def gear_pile() -> Canvas:
    """Spare gears leaning on a crate, 28 x 24."""
    cv = Canvas(28, 24, pad=PAD)
    crate = gp.crate()
    cv.paste(crate, 10, 6)
    gear(cv, 8, 15, 6, BRASS, teeth=8)
    gear(cv, 17, 9, 4, COPPER, teeth=6)
    return cv


def iron_bench() -> Canvas:
    """A cast-iron station bench, 44 x 26: scrolled iron ends, wooden slats lit on top."""
    cv = Canvas(44, 26, pad=PAD)
    for ex in (3, 38):
        for y in range(4, 26):
            cv.set(ex, y, IRON[3]); cv.set(ex + 1, y, IRON[2]); cv.set(ex + 2, y, IRON[1])
        for (x, y) in disc(ex + 1, 5, 2.2):
            cv.set(x, y, IRON[3] if x <= ex + 1 else IRON[1])
        for (x, y) in disc(ex + 1, 23, 2):
            cv.set(x, y, IRON[2])
    for sy in (6, 9, 12):  # the back
        cv.hline(5, sy, 33, WOOD[4] if sy == 6 else WOOD[3]); cv.hline(5, sy + 1, 33, WOOD[1])
    for sy in (15, 18):  # the seat
        cv.hline(2, sy, 40, WOOD[4]); cv.hline(2, sy + 1, 40, WOOD[2])
    return cv


def steamer_trunk() -> Canvas:
    """A travelling trunk, 26 x 18: leather over wood, brass corners, two straps."""
    cv = Canvas(26, 18, pad=PAD)
    for y in range(3, 18):
        for x in range(1, 25):
            cv.set(x, y, '#7A3E2A' if y > 6 else '#9A5236')
    cv.hline(1, 3, 24, '#B8693F'); cv.hline(1, 7, 24, '#4A2618')
    for sx in (7, 18):
        cv.vline(sx, 3, 15, '#3A2A1E'); cv.set(sx, 9, BRASS[4])
    for (cx, cy) in ((1, 3), (24, 3), (1, 17), (24, 17)):
        cv.set(cx, cy, BRASS[4])
    cv.rect(11, 8, 4, 3, BRASS[3])
    return cv


def coal_cart() -> Canvas:
    """A little coal tub on rail wheels, 28 x 20, heaped with lit lumps."""
    cv = Canvas(28, 20, pad=PAD)
    for y in range(6, 16):
        inset = (y - 6) // 4
        for x in range(2 + inset, 26 - inset):
            cv.set(x, y, IRON[3] if x < 6 else IRON[2] if x < 22 else IRON[1])
    cv.hline(2, 6, 24, IRON[4])
    for k in range(18):
        x, y = 4 + int(noise2(k, 0, 161) * 20), 2 + int(noise2(k, 1, 161) * 5)
        cv.set(x, y, '#3A3A44'); cv.set(x + 1, y, '#1E1E26'); cv.set(x, y - 1, '#6A6A78')
    for wx in (7, 21):
        for (x, y) in disc(wx, 17, 2.6):
            cv.set(x, y, RED[2] if x < wx else RED[1])
        cv.set(wx, 17, BRASS[4])
    return cv


def airship_mast() -> Canvas:
    """The airship mast, 96 x 128: an iron lattice tower with a lit lamp, and a small
    airship moored to it, its envelope a lit ochre cigar with panel seams, a gondola
    with warm windows and a turning propeller."""
    w, h = 104, 132
    cv = Canvas(w, h, pad=PAD)
    # the envelope, seen from above and a little from the side
    env = oval(46, 30, 42, 17)
    for (x, y) in env:
        k = ((x - 46) / 42) * 0.6 + ((y - 30) / 17) * 0.8
        c = '#F2D27A' if k < -0.55 else '#D9B25A' if k < -0.1 else '#B88E3E' if k < 0.45 else '#8E6A2C'
        if (x - 4) % 12 == 0:
            c = '#7A5A22'
        cv.set(x, y, c)
    for (x, y) in env:
        if (x, y + 1) not in env:
            cv.set(x, y, '#5E4318')
    for fx, fy in ((86, 22), (86, 38)):  # tail fins
        for t in range(6):
            cv.hline(fx, fy - t // 2 + (t if fy > 30 else 0) // 3, 8 - t, RED[3] if t < 3 else RED[2])
    # the gondola under it
    for (x, y) in rect_set(30, 48, 28, 10):
        cv.set(x, y, WOOD[3] if y < 51 else WOOD[2])
    cv.hline(30, 48, 28, WOOD[4])
    for gx in (34, 42, 50):
        porthole(cv, gx, 53, 2.6)
    for t in range(4):
        cv.set(34 + t * 7, 47 - t % 2, IRON[2])
    for (x, y) in rect_set(58, 50, 2, 6):
        cv.set(x, y, IRON[2])
    cv.vline(61, 47, 12, '#D8D4C8')  # the propeller, caught mid-turn
    # the mast: a tapering lattice tower on the right with a lamp on top
    mx = 76
    for y in range(40, h - 2):
        t = (y - 40) / (h - 42)
        lx, rx = int(mx - 2 - t * 8), int(mx + 2 + t * 8)
        cv.set(lx, y, IRON[3]); cv.set(rx, y, IRON[1])
        if (y - 40) % 12 == 0 and y < h - 14:
            cv.hline(lx, y, rx - lx + 1, IRON[2])
            for k in range(rx - lx):
                cv.set(lx + k, y + min(11, k * 12 // max(1, rx - lx)), IRON[2])
    for (x, y) in disc(mx, 38, 3):
        cv.set(x, y, '#FFE7A6' if x < mx else '#F0B85A')
    cv.hline(60, 40, mx - 60, IRON[2])  # the mooring line
    cv.rect(mx - 12, h - 4, 25, 4, STONE[3]); cv.hline(mx - 12, h - 4, 25, STONE[4])
    return cv


def tea_kiosk() -> Canvas:
    """A brass tea kiosk, 40 x 46: an onion dome of copper seen from above, a round
    brass body with a warm hatch, a kettle steaming on the counter."""
    cv = Canvas(40, 46, pad=PAD)
    for y in range(2, 18):
        half = min(17, 3 + (y - 2) * 2) if y < 10 else 17 - (y - 10) // 3
        for x in range(20 - half, 20 + half + 1):
            cv.set(x, y, COPPER[3] if x < 18 else COPPER[1] if x > 25 else COPPER[2])
    cv.vline(20, 0, 3, BRASS[4])
    for y in range(18, 44):
        for x in range(4, 36):
            k = (x - 4) / 32
            cv.set(x, y, BRASS[4] if k < 0.15 else BRASS[3] if k < 0.5 else BRASS[2] if k < 0.85 else BRASS[1])
    cv.hline(3, 18, 34, BRASS[5]); cv.hline(3, 19, 34, IRON[1])
    for (x, y) in rect_set(10, 23, 20, 10):
        cv.set(x, y, WARM[3] if y < 26 else WARM[2])
    cv.hline(8, 33, 24, WOOD[4]); cv.hline(8, 34, 24, WOOD[2])
    for (x, y) in oval(25, 31, 3, 2.2):
        cv.set(x, y, IRON[3] if x < 25 else IRON[1])
    cv.set(22, 28, SNOW[2]); cv.set(23, 27, SNOW[3]); cv.set(22, 26, SNOW[2])
    return cv


def props() -> dict[str, Canvas]:
    return {
        'workshop': workshop(), 'workshop_round': workshop(80, sign='round'), 'clock_tower': clock_tower(),
        'locomotive': locomotive(), 'gas_lamp': gas_lamp(), 'steam_puff': steam_puff(), 'pipe_run': pipe_run(),
        'gear_pile': gear_pile(), 'iron_bench': iron_bench(), 'steamer_trunk': steamer_trunk(),
        'coal_cart': coal_cart(), 'airship_mast': airship_mast(), 'tea_kiosk': tea_kiosk(),
    }


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (126, 117, 123, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/steam-props.png'))
    print('sheet', out.size)
