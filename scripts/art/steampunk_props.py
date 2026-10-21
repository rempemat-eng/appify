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
ASHLAR = MATERIALS['ashlar']
RUST = ['#3A1E14', '#5E3020', '#84482C', '#A8643C']  # rust and red-oxide primer on old iron
PAD = 4
WARM = MATERIALS['lamplight']


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


def gear(cv: Canvas, cx: float, cy: float, r: float, ramp=BRASS, teeth: int = 8, hub=True, turn: float = 0.0):
    """A gear seen face on: teeth around a lit rim, a dark hub and spokes."""
    body = disc(cx, cy, r)
    for k in range(teeth):
        a = 2 * math.pi * k / teeth + turn
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


def workshop(width: int = 96, sign: str = 'gear', turn: float = 0.0) -> Canvas:
    """A tinkerer's workshop, 96 x 94: a copper roof with an iron chimney, a brick gable
    with a brass gear emblem, brick walls, round warm windows, a riveted iron door,
    a brass pipe down the corner and a stone footing. Its walls stand 40 px round a door
    18 x 32 (the scale table's, verticality.md section 5)."""
    w, h = width, 94
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (w - 1) / 2, 22, 46, 46, 86
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
        gear(cv, ridge, 35, 6, BRASS, teeth=9, turn=turn)  # turning, in the frames
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
    dw, dh = 18, 32
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
    cv.set(dx0 + dw - 5, wall_bottom - 14, BRASS[5])
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
    """The junction's clock tower, 54 x 162, in the same three-quarter view as the
    workshops (art-faults.md, rule 4): a square brick shaft whose front faces the
    square and whose east side turns into shade, a copper spire of four planes (the
    front and east ones seen), a belfry, the clock lit from the upper left, and a
    stone plinth with steps up to the door, its contact shadow on the paving. The door is
    the scale table's (14 x 32, verticality.md section 5), so the shaft runs a storey
    longer under the clock than it did, with a stone string course across it."""
    w, h = 54, 162
    D = 24  # how much longer the shaft runs than before, below the clock
    cv = Canvas(w, h, pad=PAD)
    fx0, fx1, sx1 = 6, 40, 48  # the front face, and the east side's far edge
    cx = (fx0 + fx1 - 1) / 2
    # the spire: front plane and east plane of a square pyramid, a finial on top
    apex = (cx + 4, 2)
    for y in range(4, 36):
        t = (y - 4) / 31
        l, r, e = cx - t * (cx - fx0 + 1), cx + t * (fx1 - cx), cx + 4 + t * (sx1 - cx - 4)
        for x in range(int(l), int(e) + 1):
            front = x <= r
            band = (y - 4) % 6 == 5
            c = (COPPER[3] if x < cx else COPPER[2]) if front else COPPER[1]
            if band:
                c = COPPER[2] if front and x < cx else COPPER[0]
            if abs(x - r) < 1 and not front:
                c = COPPER[4]  # the hip between the two planes catches the light
            cv.set(x, y, c)
    cv.vline(int(apex[0]), 0, 5, BRASS[3]); cv.set(int(apex[0]), 0, BRASS[5]); cv.hline(int(apex[0]) - 1, 2, 3, BRASS[4])
    cv.hline(fx0 - 2, 36, sx1 - fx0 + 4, BRASS[2]); cv.hline(fx0 - 2, 35, fx1 - fx0 + 4, BRASS[4])
    # the shaft: front in brick, east side in shade
    brick_wall(cv, fx0, 37, fx1 - fx0, 80 + D, seed=21)
    for y in range(37, 117 + D):
        for x in range(fx1, sx1):
            k = (y + (x - fx1) * 2) % 5
            cv.set(x, y, BRICK[1] if k else BRICK[0])
        cv.set(fx1, y, BRICK[3])  # the lit corner
    # the belfry openings
    for bx in (12, 26):
        for (x, y) in rect_set(bx, 41, 8, 10) | {(x, y) for (x, y) in disc(bx + 3.5, 41, 4) if y < 41}:
            cv.set(x, y, IRON[0])
        cv.vline(bx + 3, 42, 7, BRASS[3]); cv.set(bx + 3, 49, BRASS[4])
    cv.hline(fx0 - 1, 52, sx1 - fx0 + 1, STONE[4]); cv.hline(fx0 - 1, 53, sx1 - fx0 + 1, STONE[2])
    # the clock
    cy = 69
    for (x, y) in disc(cx, cy, 13):
        cv.set(x, y, BRASS[3] if (x - cx) + (y - cy) < 0 else BRASS[1])
    for (x, y) in disc(cx, cy, 11):
        cv.set(x, y, '#F7EEDC' if (x - cx) + (y - cy) < 4 else '#E3D3B4')
    for k in range(12):
        a = 2 * math.pi * k / 12
        cv.set(int(round(cx + math.cos(a) * 9)), int(round(cy + math.sin(a) * 9)), IRON[1])
    for t in range(1, 7):
        cv.set(int(round(cx + t * 0.15)), cy - t, IRON[0])
    for t in range(1, 6):
        cv.set(int(round(cx + t * 0.8)), int(round(cy + t * 0.5)), IRON[0])
    cv.set(int(cx), cy, BRASS[4])
    for (x, y) in disc(sx1 - 4, cy, 3):  # the clock on the east face, seen edge on
        cv.set(x, y, BRASS[1] if x < sx1 - 5 else '#B8A88C')
    porthole(cv, cx, 95, 5)
    cv.hline(fx0 - 1, 106, sx1 - fx0 + 1, STONE[4]); cv.hline(fx0 - 1, 107, sx1 - fx0 + 1, STONE[2])  # the string course
    pipe_v(cv, fx1 - 4, 56, 116 + D, BRASS)
    detail.overhang_shadow(cv, fx0, fx1, 37, lambda x: 2, k=1, cap=1)
    # the plinth: a stone base with a lit top and a front face, steps to the door
    detail.stones(cv, fx0 - 3, 117 + D, fx1 - fx0 + 6, 9, STONE, seed=23, course=4)
    for y in range(117 + D, 126 + D):
        for x in range(fx1 + 3, sx1 + 3):
            cv.set(x, y, STONE[1] if (x + y) % 4 else STONE[0])
    cv.hline(fx0 - 3, 116 + D, sx1 - fx0 + 6, STONE[4])
    for (x0, y, wd) in ((14, 126 + D, 20), (12, 129 + D, 24), (10, 132 + D, 28)):
        cv.hline(x0, y, wd, STONE[4]); cv.hline(x0, y + 1, wd, STONE[3]); cv.hline(x0, y + 2, wd, STONE[1])
        cv.set(x0 + wd, y + 1, STONE[1]); cv.set(x0 + wd, y + 2, STONE[0])
    dx = int(cx) - 6  # the door, 14 wide and 32 tall to its arch's crown, in a stone surround
    sill = 116 + D
    for (x, y) in rect_set(dx - 2, sill - 27, 18, 27) | {(x, y) for (x, y) in disc(dx + 6.5, sill - 25, 9) if y < sill - 25}:
        cv.set(x, y, STONE[4] if x < cx else STONE[2])
    for (x, y) in rect_set(dx, sill - 25, 14, 25) | {(x, y) for (x, y) in disc(dx + 6.5, sill - 25, 7) if y < sill - 25}:
        c = WOOD[1] if x > cx else WOOD[2]
        if (x - dx) % 4 == 3:
            c = WOOD[0]  # the boards
        cv.set(x, y, c)
    cv.hline(dx, sill - 14, 14, IRON[2])  # its iron straps
    cv.hline(dx, sill - 5, 14, IRON[2])
    cv.set(dx + 11, sill - 11, BRASS[4])
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
    """The airship mast, 160 x 184 (size guide: a mast 64 to 120 wide and 128 to 192 tall
    with a stair or cage lift, a path to its foot; an airship's envelope 32 to 48 across
    and 96 to 160 long; Matt's World Logic answer 7: scenery but reachable). How it is
    built: a square lattice tower of four riveted iron legs on stone pads, tapering from
    28 px at the foot to 12 at the head, girts every storey and X-bracing in every panel
    (the back legs seen behind the front ones, darker); at its head a railed platform and
    the mooring cone, the airship's nose coupled into it so the ship weathervanes
    downwind to the west. A cage lift runs up the tower's front between two guide rails,
    its cage (lattice sides, a lamp inside, the gate folded open) waiting at the foot by
    the path; its rope runs over a sheave at the head down to a steam winch in an iron
    house at the foot, whose chimney and flywheel are seen. The airship: an envelope
    112 x 36 of doped panels between ribs, lit on its upper-left, fins at the tail, the
    gondola slung under it on rigging, its windows lit, a propeller at its stern."""
    w, h = 160, 184
    cv = Canvas(w, h, pad=PAD)
    foot = h - 4
    mc = 126  # the tower's centre line
    head = 34  # the platform's row
    def half(y):  # the tower's half-width at row y
        return 6 + (14 - 6) * (y - head) / (foot - head)
    # the back legs, seen behind the front ones (up and to the right), darker
    for y in range(head + 4, foot - 4):
        for side in (-1, 1):
            x = round(mc + side * half(y)) + 5
            cv.set(x, y - 5, IRON[1])
    for y in range(head + 4, foot - 4, 16):
        for x in range(round(mc - half(y)) + 5, round(mc + half(y)) + 6):
            cv.set(x, y - 5, IRON[1])
    # the front face: girts every storey, an X in each panel, the legs lit on their west side
    girts = list(range(head + 4, foot - 2, 16))
    for i in range(len(girts) - 1):
        ya, yb = girts[i], girts[i + 1]
        for t in range(yb - ya + 1):
            y = ya + t
            l, r = mc - half(y), mc + half(y)
            f = t / (yb - ya)
            xa_, xb_ = round(l + (r - l) * f), round(r - (r - l) * f)
            cv.set(xa_ - 1, y, IRON[3]); cv.set(xa_, y, IRON[3]); cv.set(xa_ + 1, y, IRON[1])  # one diagonal, an angle iron
            cv.set(xb_ + 1, y, IRON[1]); cv.set(xb_, y, IRON[2]); cv.set(xb_ - 1, y, IRON[2])  # and the other
    for y in girts:
        for x in range(round(mc - half(y)), round(mc + half(y)) + 1):
            cv.set(x, y, IRON[3]); cv.set(x, y + 1, IRON[1])
        cv.set(round(mc - half(y)), y, BRASS[3]); cv.set(round(mc + half(y)), y, BRASS[2])  # the gussets
    for y in range(head, foot - 2):  # the legs: riveted angles, red-oxide primer showing where the black has worn
        lx, rx = round(mc - half(y)), round(mc + half(y))
        worn = noise2(y // 3, 0, 1795) > 0.62 and y > head + 30
        cv.set(lx - 2, y, IRON[4] if not worn else RUST[3]); cv.set(lx - 1, y, IRON[3] if not worn else RUST[2]); cv.set(lx, y, IRON[2])
        cv.set(rx, y, IRON[2]); cv.set(rx + 1, y, IRON[1] if not worn else RUST[1]); cv.set(rx + 2, y, IRON[0])
        if y % 12 == 0:
            cv.set(lx - 1, y, BRASS[2]); cv.set(lx - 1, y + 1, BRASS[1])  # rivet heads down the legs
    for (x, y) in rect_set(mc - 13, foot - 40, 7, 5):  # an enamel plate on the leg: its owner and its load
        cv.set(x, y, '#E8E2D0' if 0 < x - (mc - 13) < 6 and 0 < y - (foot - 40) < 4 else '#2E4A7A')
    cv.hline(mc - 12, foot - 38, 5, '#2E4A7A')
    for side in (-1, 1):  # the legs' stone pads
        x0 = round(mc + side * half(foot - 2)) - 3
        for y in range(foot - 3, foot + 2):
            for x in range(x0, x0 + 7):
                c = STONE[4] if y == foot - 3 else STONE[2] if x < x0 + 5 else STONE[1]
                cv.set(x, y, c)
    # the cage lift: two guide rails up the front, the rope, the cage at the foot
    for y in range(head + 2, foot - 2):
        cv.set(mc - 5, y, IRON[4]); cv.set(mc - 4, y, IRON[2]); cv.set(mc + 5, y, IRON[2]); cv.set(mc + 6, y, IRON[0])
        cv.set(mc, y, MATERIALS['rope'][2])
    cg0, cg1 = foot - 24, foot - 2
    for y in range(cg0, cg1):
        for x in range(mc - 6, mc + 7):
            k = y - cg0
            inside = mc - 5 < x < mc + 5 and cg0 + 2 < y < cg1 - 1
            if inside:
                c = WARM[3] if k < 8 else WARM[2]  # the lamp inside lights its floor and back
                if x in (mc - 2, mc + 2) and k > 3:
                    c = IRON[1]  # the back lattice, seen through
                if mc - 3 <= x <= mc - 1 and k >= 9:
                    c = '#3A4258' if k < 16 else '#2A2A34'  # someone riding up, a coat and boots
                if x == mc - 2 and 6 <= k < 9:
                    c = '#E0A882'
            else:
                c = BRASS[4] if y == cg0 else IRON[3] if x == mc - 6 else IRON[1] if x == mc + 6 else IRON[2]
                if y == cg1 - 1:
                    c = WOOD[2]  # the cage's floor sill
            cv.set(x, y, c)
    for y in range(cg0 + 3, cg1 - 1, 3):  # its gate folded open to the west, a stack of lattice
        cv.set(mc - 8, y, IRON[3]); cv.set(mc - 7, y + 1, IRON[2])
    cv.hline(mc - 2, cg0 - 2, 5, BRASS[3]); cv.set(mc, cg0 - 1, IRON[3])  # the rope's shackle on its roof
    # the winch house at the foot, east of the tower: a brick engine house under a
    # corrugated iron roof, its door open on the lit engine and flywheel, a stack for the boiler
    hx0, hy0 = mc + 14, foot - 22
    hw_ = 18
    for y in range(hy0, hy0 + 6):  # the roof: corrugated sheets, lit on top, the gutter in verdigris copper
        k = y - hy0
        for x in range(hx0 - 1 + (5 - k) // 2, hx0 + hw_ + 1):
            c = IRON[4] if k < 2 else IRON[3]
            if ((x - hx0) // 2) % 2:
                c = IRON[3] if k < 2 else IRON[2]  # the corrugations, 2 px a sheet's rib
            if k == 5:
                c = COPPER[3] if x < hx0 + 8 else COPPER[2]
            cv.set(x, y, c)
    for (x, y) in ((hx0 + 9, hy0 + 2), (hx0 + 10, hy0 + 2), (hx0 + 10, hy0 + 3)):
        cv.set(x, y, RUST[2])  # a rust bloom round a roofing bolt
    for y in range(hy0 + 6, foot):  # the walls: brick in courses on a stone plinth
        k = y - (hy0 + 6)
        for x in range(hx0, hx0 + hw_):
            row = k // 3
            n = noise2((x + (row % 2) * 3) // 6, row, 1807)
            c = BRICK[3] if n > 0.4 else BRICK[2]
            if x > hx0 + hw_ - 4:
                c = BRICK[2] if n > 0.4 else BRICK[1]  # the east end in shade
            if k % 3 == 2 or (x + (row % 2) * 3) % 6 == 0:
                c = BRICK[1] if x <= hx0 + hw_ - 4 else BRICK[0]  # the mortar, sooty
            if y >= foot - 3:
                c = ASHLAR[3] if y == foot - 3 else ASHLAR[2] if x < hx0 + hw_ - 3 else ASHLAR[1]  # the plinth
            cv.set(x, y, c)
    dx0, dy0_ = hx0 + 2, hy0 + 8  # the door, open on the engine: the flywheel's rim crossing the lamplight
    for (x, y) in rect_set(dx0, dy0_, 7, foot - 3 - dy0_):
        c = WARM[2] if y < dy0_ + 5 else WARM[1]
        cv.set(x, y, c)
    fx, fy = dx0 + 4, dy0_ + 7
    for (x, y) in disc(fx, fy, 4.6):
        if math.hypot(x - fx, y - fy) > 3.2 and dx0 <= x < dx0 + 7 and y < foot - 3:
            cv.set(x, y, IRON[1] if (x - fx) + (y - fy) > -2 else IRON[3])  # the flywheel's rim, lit by the lamp
    for y in range(dy0_, foot - 3):  # the door leaf folded back, planked and painted red
        cv.set(dx0 - 1, y, '#8A2A22')
    cv.hline(dx0 - 1, dy0_ - 1, 9, ASHLAR[4]); cv.hline(dx0 - 1, dy0_ - 2, 9, ASHLAR[3])  # the stone lintel
    wx0 = hx0 + 11  # a small window, lit, its glazing bar and a stone sill
    for (x, y) in rect_set(wx0, hy0 + 9, 5, 5):
        c = WARM[3] if y < hy0 + 11 else WARM[2]
        if x == wx0 + 2 or y == hy0 + 11:
            c = '#3A2A1A'
        cv.set(x, y, c)
    cv.hline(wx0 - 1, hy0 + 14, 7, ASHLAR[4])
    for y in range(hy0 - 10, hy0 + 2):  # the boiler's stack, brick, sooted at its cap
        for x in range(hx0 + 13, hx0 + 16):
            c = BRICK[3] if x == hx0 + 13 else BRICK[2] if x == hx0 + 14 else BRICK[1]
            if (y - hy0) % 3 == 0:
                c = BRICK[1]
            if y < hy0 - 7:
                c = IRON[2] if x < hx0 + 15 else IRON[0]  # the soot at its cap
            cv.set(x, y, c)
    cv.hline(hx0 + 12, hy0 - 10, 5, IRON[3])
    for (x, y) in oval(hx0 - 4, foot - 2, 4, 2):  # the coal for its boiler, heaped by the door
        n = noise2(x // 2, y, 1806)
        cv.set(x, y, IRON[2] if n > 0.6 else IRON[1] if n > 0.25 else IRON[0])
    for (x, y) in ((hx0 - 6, foot - 3), (hx0 - 5, foot - 3), (hx0 - 3, foot - 4), (hx0 - 2, foot - 4)):
        cv.set(x, y, IRON[3])  # lumps catching the light
    for t in range(14):  # the winch rope from the house up to the tower
        cv.set(hx0 - t, hy0 + 7 - t // 3, MATERIALS['rope'][1])
    for y in range(head + 2, head + 34):  # the top storeys banded red and white, to be seen from the air
        if ((y - head - 2) // 8) % 2 == 0:
            lx, rx = round(mc - half(y)), round(mc + half(y))
            for x in (lx - 2, lx - 1, rx + 1, rx + 2):
                cv.set(x, y, '#E8E2D6' if x < mc else '#B8B0A4')
        else:
            lx, rx = round(mc - half(y)), round(mc + half(y))
            for x in (lx - 2, lx - 1, rx + 1, rx + 2):
                cv.set(x, y, RED[3] if x < mc else RED[1])
    # the head: a railed platform, the mooring cone, a sheave, a lamp
    for x in range(mc - 10, mc + 11):
        cv.set(x, head, IRON[4]); cv.set(x, head + 1, IRON[2]); cv.set(x, head + 2, IRON[1])
        if (x - mc) % 4 == 0:
            for y in range(head - 6, head):
                cv.set(x, y, IRON[3])
    cv.hline(mc - 10, head - 6, 21, IRON[4])
    for y in range(head - 16, head - 1):  # the mooring cone, narrowing up to its cup
        hw = 1 + (y - (head - 16)) // 4
        for x in range(mc - hw, mc + hw + 1):
            cv.set(x, y, IRON[4] if x < mc else IRON[2])
    for (x, y) in disc(mc, head - 18, 2.4):  # the lamp on its top, warm
        cv.set(x, y, '#FFE7A6' if x < mc else '#F0B85A')
    # the airship, its nose in the cone's cup, lying off to the west downwind
    ex, ey, rx, ry = 62, head - 12, 56, 18
    env = oval(ex, ey, rx, ry)
    DOPE = ['#5E4318', '#7A5A22', '#8E6A2C', '#A47C36', '#B88E3E', '#CCA24C', '#D9B25A', '#E8C66A', '#F2D27A']
    for (x, y) in env:
        u, v = (x - ex) / rx, (y - ey) / ry
        k = u * 0.45 + v * 0.9
        i = 8 if k < -0.55 else 6 if k < -0.1 else 4 if k < 0.45 else 2
        gore = (x - ex + 3) // 14
        g = noise2(gore, 0, 1796)
        i += 1 if g > 0.7 else -1 if g < 0.3 else 0  # each gore of doped linen weathered its own way
        gx_ = (x - ex + 3) % 14  # where in its gore: the cloth bellies out between the seams
        if gx_ in (1, 2) and k < 0.3:
            i += 1  # the gore's lit edge where it swells from the seam
        elif gx_ in (12, 13) and k > -0.3:
            i -= 1  # and its shaded edge as it draws back in to the next seam
        if noise2(gore, (y - ey + 40) // 7, 1797) > 0.82 and 3 <= gx_ <= 10 and -0.6 < v < 0.7:
            i -= 1  # a panel let into the gore over a tear, in cloth that has weathered less
        if v > 0.5 and noise2(x // 3, y // 2, 1799) > 0.7:
            i -= 1  # weather stains gathered low on the envelope, where rain runs off
        if 0.62 < v < 0.8 and abs(u) < 0.62:
            i += 2  # the lit belly: light thrown back up from the ground
        KHAKI = ['#3E3A24', '#4E4A30', '#6A6440', '#857E52', '#A09A66', '#BAB47E', '#C8C28A', '#D0CA96', '#DCD6A4']
        c = (KHAKI if noise2(gore, 1, 1805) > 0.62 else DOPE)[max(1, min(8, i))]  # gores renewed in a paler cloth
        rib = abs((x - ex + 3) % 14) < 1
        if rib:
            c = '#7A5A22' if k > -0.55 else '#C49A48'
        elif (y - ey) % 6 == 0 and v < -0.2 and (x + (y // 6) * 3) % 6 < 2:
            c = DOPE[max(0, min(8, i) - 2)]  # the rigging net over its top, a diamond mesh
        if v > 0.82:
            c = '#5E4318'
        if abs(v + 0.25) < 0.04 and u < 0.85:
            c = '#E8C86A' if k < 0 else '#A07A34'  # the girth line the rigging hangs from
        if 0.05 < v < 0.25 and -0.75 < u < 0.7:
            c = RED[3] if k < 0 else RED[2]  # the company's band painted round it
            if abs(v - 0.05) < 0.06 or abs(v - 0.25) < 0.06:
                c = GOLD[3] if k < 0 else GOLD[2]
        cv.set(x, y, c)
    ROPE = MATERIALS['rope']
    for (x, y) in env:  # the cord net over the whole envelope, a diamond mesh, brass rings where it meets the girth
        u, v = (x - ex) / rx, (y - ey) / ry
        if v > 0.8 or u > 0.9:
            continue
        a, b = (x + 2 * y) % 16, (x - 2 * y) % 16
        if a in (0, 1) or b in (0, 1):
            k = u * 0.45 + v * 0.9
            cv.set(x, y, ROPE[3] if k < -0.4 else ROPE[2] if k < 0.3 else ROPE[1])
            if a in (0, 1) and b in (0, 1) and abs(v + 0.25) < 0.12:
                cv.set(x, y, BRASS[4] if k < 0 else BRASS[2])
    for (vx, vy) in ((ex - 20, ey - ry + 2), (ex + 14, ey - ry + 2)):  # gas valves on its back
        for (x, y) in rect_set(vx, vy, 3, 2):
            cv.set(x, y, IRON[3] if y == vy else IRON[1])
        cv.set(vx + 1, vy - 1, BRASS[4])
    for (x, y) in env:
        if (x, y + 1) not in env:
            cv.set(x, y, '#4E3612')
    for t in range(9):  # the nose cap, coupled into the cone
        cv.set(ex + rx - 2 + t // 3, ey - 1 + t % 3, IRON[3] if t % 3 else IRON[4])
    for (fy, d) in ((ey - 10, -1), (ey + 10, 1)):  # the tail fins, in red doped cloth on a frame
        for t in range(10):
            for k in range(12 - t):
                y = fy + d * (t // 2)
                cv.set(ex - rx + 2 + k - t // 2, y, RED[3] if d < 0 else RED[2])
        cv.hline(ex - rx - 2, fy, 14, WOOD[3])
    gx0, gy0 = ex - 18, ey + ry + 6  # the gondola, slung on rigging
    for (x, y) in rect_set(gx0, gy0, 34, 9):
        c = WOOD[4] if y == gy0 else WOOD[3] if y < gy0 + 4 else WOOD[2]
        if y == gy0 + 8:
            c = WOOD[1]
        cv.set(x, y, c)
    for k in range(5):
        porthole(cv, gx0 + 5 + k * 6, gy0 + 4, 2.2)
    for k in range(5):  # the rigging, from the girth line down to the gondola's rail
        x_top = ex - 30 + k * 15
        for t in range(10):
            f = t / 9
            cv.set(round(x_top + (gx0 + 2 + k * 7.5 - x_top) * f), round(ey + 9 + (gy0 - ey - 9) * f), '#6E5A3A')
    for k, bx in enumerate((gx0 + 6, gx0 + 16, gx0 + 26)):  # ballast bags slung under the gondola
        for (x, y) in rect_set(bx, gy0 + 10, 3, 3):
            cv.set(x, y, '#C8B488' if x == bx else '#9A8660')
        cv.set(bx + 1, gy0 + 9, MATERIALS['rope'][1])
    for (nx, d) in ((gx0 - 8, -1), (gx0 + 36, 1)):  # an engine nacelle on an outrigger each side
        cv.hline(min(nx, gx0 + 34) if d > 0 else nx + 4, gy0 + 3, 6, IRON[2])
        for (x, y) in rect_set(nx, gy0 + 1, 6, 5):
            cv.set(x, y, BRASS[4] if y == gy0 + 1 else BRASS[3] if y < gy0 + 4 else BRASS[1])
        cv.set(nx + (0 if d < 0 else 5), gy0 + 3, IRON[0])
    GLYPH = {'C': ('###', '#..', '#..', '#..', '###'), '7': ('###', '..#', '.#.', '.#.', '.#.')}
    for n_, ch in enumerate('C7'):  # the ship's letters stencilled on its side, in white lead
        for r, line in enumerate(GLYPH[ch]):
            for q, on in enumerate(line):
                if on == '#':
                    cv.set(ex - 32 + n_ * 5 + q, ey - 8 + r, '#F2ECDA' if r < 3 else '#D8D0BC')
    for (sx, sy, ln) in ((ex - 20, ey - ry + 4, 6), (ex + 14, ey - ry + 4, 5)):  # streaks run down from the valves
        for t in range(ln):
            cv.set(sx + 1, sy + t, DOPE[2]); cv.set(sx + 2, sy + t, DOPE[3])
    for (fx0, fy0) in ((ex - rx + 8, ey - 5), (ex - rx + 10, ey + 3), (ex - rx + 7, ey + 8)):  # slack folds toward the tail
        for t in range(4):
            cv.set(fx0 + t, fy0 + t // 2, DOPE[2]); cv.set(fx0 + t, fy0 + t // 2 - 1, DOPE[6])
    for y in range(gy0 + 1, gy0 + 8):  # the propeller at its stern (west), a blur caught mid-turn
        cv.set(gx0 - 3, y, '#D8D4C8' if y % 3 else '#8E8A80')
    cv.hline(gx0 - 2, gy0 + 4, 2, IRON[2])
    return cv


def tea_kiosk() -> Canvas:
    """A tea kiosk, 42 x 50, in the three-quarter view: a copper roof whose top and
    front slope are seen, a striped canvas awning over the serving hatch, a brass-
    banded timber booth with its east side in shade, a kettle steaming on the
    counter and a menu slate leaning by the door."""
    w, h = 42, 50
    cv = Canvas(w, h, pad=PAD)
    fx0, fx1, sx1 = 3, 31, 39
    # the roof: a low hip, its top plane lit, its front slope and east slope below
    for y in range(2, 15):
        t = (y - 2) / 12
        l, r, e = 10 - t * 9, 24 + t * 8, 28 + t * 12
        for x in range(int(l), int(e) + 1):
            c = COPPER[3] if y < 6 else (COPPER[2] if x <= r else COPPER[1])
            if y == 14:
                c = COPPER[0]
            cv.set(x, y, c)
    cv.vline(17, 0, 3, BRASS[4])
    # the booth's front and east side
    for y in range(15, 46):
        for x in range(fx0, sx1):
            if x < fx1:
                c = WOOD[3] if (x - fx0) % 6 else WOOD[2]
                if y in (15, 30):
                    c = BRASS[4]
            else:
                c = WOOD[1] if (y // 3) % 2 else WOOD[0]
            cv.set(x, y, c)
        cv.set(fx1, y, WOOD[4])
    for (x, y) in rect_set(8, 19, 18, 9):  # the hatch, warm inside
        cv.set(x, y, WARM[3] if y < 22 else WARM[2])
    # the awning: canvas stripes sloping out over the hatch, its top lit
    for y in range(15, 20):
        for x in range(5 - (y - 15), fx1 + (y - 15) // 2):
            stripe = ((x + (y - 15)) // 4) % 2
            c = ('#E8DCC4' if stripe else RED[3]) if y < 19 else ('#B8AC94' if stripe else RED[1])
            cv.set(x, y, c)
    cv.hline(6, 28, 22, WOOD[4]); cv.hline(6, 29, 22, WOOD[1])  # the counter
    for (x, y) in oval(21, 26, 2.6, 2):
        cv.set(x, y, IRON[3] if x < 21 else IRON[1])
    cv.set(20, 23, SNOW[2]); cv.set(21, 22, SNOW[3]); cv.set(20, 21, SNOW[2])
    for (x, y) in rect_set(33, 36, 6, 10):  # a menu slate leaning on the east side
        cv.set(x, y, IRON[1] if (x, y) != (35, 39) else SNOW[2])
    cv.hline(33, 35, 6, WOOD[3])
    return cv


BOAT_GREEN = ['#12261E', '#1E3E30', '#2C5A44', '#3E7A5A', '#5A9A72']


def narrowboat() -> Canvas:
    """A steam narrowboat moored on the canal, 100 x 34 (size guide: 96 to 144 long, so it
    fits the lock's 104 px chamber), side on and a little from above. How it is built: a
    riveted steel hull, black below the waterline band, bottle green above, a red and gold
    rubbing strake; the open fore-hold with its coal heaped under the crane, cratch boards
    at the bow; the cabin with a planked roof seen from above (a water can, a mop, the
    brass funnel of its steam engine), round portholes in brass, a side hatch, a panel of
    painted flowers; at the stern the brass swan-neck tiller and a coiled rope; rope
    fenders hung over the side; the mooring line from the bow's T-stud up to the quay. It
    rides the water on the renderer's float bob (components/atlas-walk.tsx FLOATS)."""
    w, h = 100, 34
    cv = Canvas(w, h, pad=PAD)
    G = BOAT_GREEN
    hull_top, water = 18, 30
    for x in range(2, w - 2):
        bow = max(0, 14 - x) ** 2 // 18  # the bow sweeps up, the stern rounds off
        stern = max(0, x - (w - 8)) ** 2 // 6
        top = hull_top + bow // 4 + stern // 3
        for y in range(top, water):
            k = y - top
            c = G[3] if k < 2 else G[2] if y < 25 else G[1]
            if y == top:
                c = G[4]  # the gunwale, lit
            if y in (22, 23):
                c = RED[3] if y == 22 else GOLD[3]  # the rubbing strake
            if y >= 27:
                c = '#14141A' if y < 29 else '#0C0C10'  # the black below the waterline band
            if (x - 4) % 9 == 0 and 24 <= y < 27:
                c = G[0]  # the plates' seams
            if (x - 8) % 9 == 0 and y == 25:
                c = G[3]  # a rivet head catching the light
            cv.set(x, y, c)
        cv.set(x, water, '#0C1A16')
    for x in range(12, w - 12, 13):  # rust run down from a rivet, and the hull's scuffs
        for y in range(24, 28):
            cv.set(x, y, RUST[2] if y < 26 else RUST[1])
    for (x, y) in rect_set(18, 19, 10, 3):  # the boat's name panel on the bow, abstract strokes on cream
        cv.set(x, y, '#E8D8B8' if (x + y) % 4 else RED[2])
    cv.hline(18, 18, 10, GOLD[4])
    # the fore-hold: open, its coal heaped high, the cratch's triangle of boards at the bow
    for (x, y) in oval(16, 18, 9, 3.4):
        n = noise2(x, y, 1750)
        cv.set(x, y, IRON[2] if n > 0.7 else IRON[1] if n > 0.3 else IRON[0])
    for t in range(6):
        cv.hline(5 + t, 12 + t, 2, WOOD[4] if t < 2 else WOOD[3])
    cv.vline(5, 12, 7, WOOD[2])
    cx0, cy0 = 10, 8  # a crate on the coal, the canal crane's sling round it (canal_crane)
    for y in range(cy0, cy0 + 10):
        for x in range(cx0, cx0 + 12):
            if y < cy0 + 3:
                c = WOOD[4] if (x - cx0) % 4 else WOOD[3]  # the slatted lid, seen from above
            else:
                c = WOOD[3] if (y - cy0) % 4 else WOOD[1]
                if x in (cx0, cx0 + 11):
                    c = WOOD[2]
                if (x - cx0) == (y - cy0) + 1:
                    c = WOOD[2]  # the brace across its front
            cv.set(x, y, c)
    cv.hline(cx0, cy0 + 3, 12, WOOD[1])
    # the cabin: its side with portholes, a hatch and the painted panel; its roof from above
    c0, c1 = 30, w - 14
    for x in range(c0, c1):
        for y in range(9, hull_top):
            c = G[3] if y < 12 else G[2] if y < 16 else G[1]
            if x == c0:
                c = G[4]
            elif x == c1 - 1:
                c = G[1]
            cv.set(x, y, c)
        for y in (6, 7, 8):  # the planked roof seen from above, a lit edge
            c = WOOD[4] if y == 8 else WOOD[3] if (x // 7 + y) % 2 else WOOD[2]
            cv.set(x, y, c)
        cv.set(x, 9, GOLD[2] if (x // 3) % 2 else GOLD[3])  # the coach line under the roof
    for (p0, p1) in ((32, 56), (67, 77), (87, w - 15)):  # the cabin's panels, lined out in gold and red
        for x in range(p0, p1):
            cv.set(x, 10, GOLD[3]); cv.set(x, 16, RED[2])
        for y in range(10, 17):
            cv.set(p0, y, GOLD[3]); cv.set(p1 - 1, y, RED[2])
    for px in (38, 50, 74):
        porthole(cv, px, 13, 2.4)
    for y in range(11, 17):  # a side hatch, its double doors
        for x in range(57, 66):
            c = G[1] if x in (57, 61, 65) else G[3] if y < 13 else G[2]
            cv.set(x, y, c)
    cv.set(60, 14, BRASS[4]); cv.set(62, 14, BRASS[4])
    for y in range(11, 17):  # the painted panel: a rose and leaves on cream, in clusters
        for x in range(78, 86):
            c = '#E8D8B8' if y in (11, 16) or x in (78, 85) else '#D8C49A'
            if (x - 81.5) ** 2 + (y - 13.5) ** 2 < 3:
                c = RED[3] if y < 14 else RED[2]
            elif (x, y) in ((79, 14), (80, 15), (84, 12), (83, 12)):
                c = '#4A7A3A'
            cv.set(x, y, c)
    for (x, y) in ((34, 5), (35, 5), (34, 4), (35, 4)):  # a water can on the roof
        cv.set(x, y, RED[3] if x == 34 else RED[2])
    cv.set(36, 4, RED[2])
    for t in range(9):  # a mop lying along the roof
        cv.set(64 + t, 6, WOOD[4])
    cv.set(73, 6, '#D8D0C0'); cv.set(74, 6, '#B8B0A0'); cv.set(73, 5, '#D8D0C0')
    for y in range(0, 7):  # the funnel of its steam engine, with a brass band
        for x in range(45, 49):
            c = IRON[3] if x < 47 else IRON[1]
            if y == 2:
                c = BRASS[4] if x < 47 else BRASS[2]
            cv.set(x, y, c)
    cv.hline(44, 0, 6, IRON[4])
    # the stern: a brass swan-neck and the tiller bar, a coil of rope on the counter
    for t in range(7):
        cv.set(w - 10 + t // 3, 16 - t, BRASS[4] if t < 4 else BRASS[3])
    cv.hline(w - 12, 9, 7, WOOD[3]); cv.set(w - 12, 9, WOOD[4])
    for (x, y) in oval(w - 18, 17, 3, 1.4):
        cv.set(x, y, MATERIALS['rope'][3] if (x + y) % 2 else MATERIALS['rope'][1])
    for fx in (24, 52, 70, 88):  # rope fenders over the side
        for y in range(19, 25):
            cv.set(fx, y, MATERIALS['rope'][2] if y % 2 else MATERIALS['rope'][1])
            cv.set(fx + 1, y, MATERIALS['rope'][1])
        cv.set(fx, 18, MATERIALS['rope'][3])
    # the mooring line: from the T-stud on the bow, slack, up to the ring on the quay (north)
    cv.set(9, 17, IRON[4]); cv.set(10, 17, IRON[3])
    for t in range(12):
        cv.set(9 - t // 3, 16 - t, MATERIALS['rope'][3] if t % 3 else MATERIALS['rope'][2])
    return cv


def canal_crane() -> Canvas:
    """A hand-cranked jib crane on the canal's quay, 52 x 90 of which 68 stand over the
    quay and the rest is its chain down to the boat (size guide 24 to 64 by 40 to 72; Matt's World Logic answer 10: the jib turned out over the narrowboat). How it is
    built: a cast-iron post on a dressed-stone pier at the quay's edge, a slewing ring at
    its head, a riveted lattice jib reaching south and a little west out over the water,
    held by a tie rod from the post's finial; a winch with its brass gear and crank on the
    post at hand height, the chain run up the post, over the jib's head sheave and down
    to the hook; the hook let down into the boat's fore-hold, slung round the crate it is lifting (the crate is drawn with the boat). In
    the world's view a reach out toward us is drawn lower on screen: the jib's head stands
    46 px over a point 26 px south of the post's foot, so it is drawn 20 px above the
    foot's row and 22 px west of the post."""
    w, h = 52, 90
    cv = Canvas(w, h, pad=PAD)
    px = 36  # the post's centre
    foot = 66  # the pier's foot on the quay; below it only the chain hangs, down to the boat
    GRANITE_ = ['#3A3A42', '#55555E', '#73737A', '#93918F', '#B4B0A8', '#D2CDC2']
    for y in range(foot - 10, foot + 1):  # the pier: dressed stone from two quarries, coped, its face in shade
        for x in range(px - 8, px + 9):
            k = y - (foot - 10)
            course = (k - 3) // 4
            blk = (x + (course % 2) * 4) // 8
            st = GRANITE_ if noise2(blk, course, 1798) > 0.5 else ASHLAR
            c = st[3] if x < px - 3 else st[2]  # each block lit on the west, a step into shade east
            if k >= 3 and (k - 3) % 4 == 3:
                c = st[1]  # the bed joints
            elif k >= 3 and (x + (course % 2) * 4) % 8 == 0:
                c = st[1]  # the perpends
            elif k >= 3 and (k - 3) % 4 == 0 and x < px + 2:
                c = st[4]  # the blocks' lit top arris
            if k < 3:  # the coping, a slab overhanging the face, lit on top
                c = ASHLAR[5] if k == 0 else ASHLAR[4] if x < px + 4 else ASHLAR[3]
                if k == 2:
                    c = ASHLAR[1]
            if x >= px + 7 and k >= 3:
                c = ASHLAR[1] if x == px + 7 else ASHLAR[0]  # the pier's east side, in shade
            cv.set(x, y, c)
    for (x, y) in ((px - 7, foot - 4), (px - 6, foot - 4), (px - 7, foot - 3), (px - 6, foot - 1),
                   (px - 5, foot - 1), (px + 4, foot - 2), (px + 5, foot - 2), (px + 5, foot - 1)):
        cv.set(x, y, '#3E5A30' if y < foot - 2 else '#2E4426')  # moss in the damp joints at the pier's foot
    for (x, y) in rect_set(px - 5, foot - 12, 11, 2):  # the post's cast base flange, bolted to the coping
        cv.set(x, y, IRON[3] if y == foot - 12 else IRON[1])
    for bx in (px - 4, px + 3):
        cv.set(bx, foot - 12, BRASS[4]); cv.set(bx + 1, foot - 12, BRASS[2])
    top = foot - 52  # the post's head (46 px over the quay plus the pier)
    PAINT = ['#16261E', '#22382C', '#30503C', '#44684E', '#5E8466']  # the canal company's green, on cast iron
    for y in range(top, foot - 12):  # the post, tapering, lit on its west side, its paint worn to the iron
        half = 2 if y < top + 20 else 3
        for x in range(px - half, px + half + 1):
            ramp = IRON if noise2(x // 2, y // 3, 1802) > 0.78 else PAINT
            c = ramp[4] if x == px - half else ramp[3] if x < px else ramp[2] if x == px else ramp[1]
            cv.set(x, y, c)
        if (y - top) % 12 == 6:
            cv.hline(px - half - 1, y, 2 * half + 3, IRON[2])  # the casting's bands
    for (x, y) in disc(px, top - 3, 2):  # the finial
        cv.set(x, y, IRON[4] if x < px else IRON[2])
    cv.hline(px - 4, top, 9, BRASS[3]); cv.hline(px - 4, top + 1, 9, BRASS[1])  # the slewing ring
    jx, jy = px - 22, top + 16  # the jib's head, drawn down-left of the post (rising a little toward it)
    steps = 26
    for t in range(steps + 1):  # the jib: two chords and a lattice between, from the ring to the head
        f = t / steps
        x = round(px - 3 + (jx - (px - 3)) * f)
        yu = round(top + 1 + (jy - 3 - (top + 1)) * f)
        yl = round(top + 6 + (jy - (top + 6)) * f)
        cv.set(x, yu, IRON[4]); cv.set(x, yl, IRON[2])
        if t % 4 == 0:
            for yy in range(yu + 1, yl):
                cv.set(x, yy, IRON[3])
        elif t % 4 == 2:
            cv.set(x, (yu + yl) // 2, IRON[2])
    for t in range(30):  # the tie rod from the finial to the head
        f = t / 29
        cv.set(round(px - 1 + (jx - px + 1) * f), round(top - 3 + (jy - 3 - top + 3) * f), IRON[3])
    for (x, y) in disc(jx, jy - 1, 2):  # the head sheave
        cv.set(x, y, IRON[4] if x <= jx else IRON[1])
    cv.set(jx, jy - 1, BRASS[4])
    for (ry0, rx0) in ((top + 24, px - 2), (top + 38, px)):  # rust where the paint has gone, in patches
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3)):
            cv.set(rx0 + dx, ry0 + dy, RUST[2] if dy < 2 else RUST[1])
    for (x, y) in oval(px - 13, foot - 2, 4, 1.8):  # a coil of rope on the quay by the pier, its turns lit on top
        cv.set(x, y, MATERIALS['rope'][3] if y < foot - 2 else MATERIALS['rope'][1] if x > px - 12 else MATERIALS['rope'][2])
    # the winch, bolted to the post at hand height: two cast side frames, a chain barrel
    # between them, a big spur wheel driven by a pinion on the crank shaft, a ratchet and pawl
    wy0, wy1 = foot - 30, foot - 13
    for y in range(wy0, wy1):  # the side frame facing us, an A of cast iron in the company's green
        k = y - wy0
        x0, x1 = px + 3, px + 8 + k // 3
        for x in range(x0, min(w - 1, x1 + 1)):
            c = PAINT[3] if k < 2 else PAINT[2] if x < x0 + 3 else PAINT[1]
            if x == x1:
                c = PAINT[0]
            if k == 0:
                c = PAINT[4]
            cv.set(x, y, c)
    for (x, y) in ((px + 4, wy0 + 3), (px + 4, wy1 - 3), (px + 9, wy1 - 3)):  # its bolts
        cv.set(x, y, BRASS[3]); cv.set(x + 1, y, BRASS[1])
    for y in range(wy0 + 3, wy0 + 9):  # the chain barrel, wound with chain, between the frames
        for x in range(px + 4, px + 11):
            k = y - (wy0 + 3)
            c = IRON[3] if k < 2 else IRON[2] if k < 4 else IRON[1]
            if (x + y) % 3 == 0:
                c = IRON[4] if k < 3 else IRON[2]  # the chain's links lying round it
            cv.set(x, y, c)
    gx, gy = px + 9, wy0 + 10
    for (x, y) in disc(gx, gy, 5.2):  # the spur wheel: a lit rim, a dark web, four spokes, its teeth
        d = math.hypot(x - gx, y - gy)
        if d > 4.0:
            c = IRON[4] if (x - gx) + (y - gy) < -2 else IRON[3] if (x - gx) + (y - gy) < 3 else IRON[2]
            if round(math.atan2(y - gy, x - gx) / (math.pi / 8)) % 2 == 0 and d > 4.6:
                c = IRON[1]  # the gaps between its teeth
        elif x == gx or y == gy:
            c = IRON[3] if (x - gx) + (y - gy) < 0 else IRON[2]  # the spokes
        else:
            c = PAINT[2] if (x - gx) + (y - gy) < 0 else PAINT[1]
        cv.set(x, y, c)
    for (x, y) in disc(gx, gy, 1.2):
        cv.set(x, y, BRASS[4] if x <= gx and y <= gy else BRASS[2])  # its boss
    for (x, y) in disc(gx - 5, gy + 4, 1.6):  # the pinion on the crank shaft, brass
        cv.set(x, y, BRASS[4] if x < gx - 5 else BRASS[2])
    for t in range(5):  # the crank arm, from the shaft out to the handle
        cv.set(gx - 5 - t, gy + 4 + t // 2, IRON[3]); cv.set(gx - 5 - t, gy + 5 + t // 2, IRON[1])
    for (x, y) in rect_set(gx - 11, gy + 6, 2, 3):
        cv.set(x, y, '#B8382C' if y == gy + 6 else '#8A2A22')  # the crank's red-painted handle, worn by hands
    cv.set(gx - 1, wy0 + 2, IRON[4]); cv.set(gx, wy0 + 2, IRON[4]); cv.set(gx, wy0 + 1, IRON[2])  # the pawl on its ratchet
    for y in range(top + 6, foot - 27):  # the chain up the post, to the barrel, its links two rows long
        cv.set(px + 3, y, IRON[2] if (y // 2) % 2 else IRON[4])
    hook_y = jy + 52  # the hook let down over the fore-hold, its sling round the crate in the boat
    for y in range(jy + 1, hook_y):  # the chain down from the sheave, its links two rows long
        cv.set(jx, y, IRON[1] if (y // 2) % 2 else IRON[3])
    cv.set(jx, hook_y, IRON[4]); cv.set(jx - 1, hook_y + 1, IRON[3]); cv.set(jx + 1, hook_y + 1, IRON[2])
    for t in range(4):  # the sling's two legs, taut, to the crate's corners (the crate is the boat's)
        cv.set(jx - 1 - t, hook_y + 2 + t, MATERIALS['rope'][3])
        cv.set(jx + 1 + t, hook_y + 2 + t, MATERIALS['rope'][2])
    return cv


def foundry() -> Canvas:
    """The foundry, 144 x 108: a long brick hall under a sawtooth roof of copper slopes
    and glazed north lights glowing with the furnace, two tall brick chimneys, a great
    arched doorway open on molten orange, a crucible track and a pile of moulds."""
    w, h = 144, 108
    cv = Canvas(w, h, pad=PAD)
    for k in range(4):  # the sawtooth bays
        x0 = 6 + k * 33
        for x in range(x0, x0 + 33):
            t = (x - x0) / 33
            top = int(30 - t * 16)
            for y in range(top, 46):
                if t > 0.82:
                    c = WARM[3] if (y // 3) % 2 else WARM[2]  # the glazing, lit from inside
                    if (x - x0) % 3 == 0:
                        c = IRON[1]
                else:
                    c = COPPER[3] if t < 0.2 else COPPER[2] if t < 0.6 else COPPER[1]
                    if (x - x0) % 6 == 0:
                        c = COPPER[4]
                cv.set(x, y, c)
            cv.set(x, top, COPPER[4] if t < 0.82 else IRON[2])
    for (cx, top) in ((22, 0), (118, 6)):  # chimneys
        for y in range(top, 40):
            for x in range(cx, cx + 10):
                c = BRICK[4] if x < cx + 2 else BRICK[3] if x < cx + 7 else BRICK[1]
                if (y + (x // 4) * 2) % 4 == 0:
                    c = BRICK[1] if x < cx + 7 else BRICK[0]
                cv.set(x, y, c)
        cv.hline(cx - 1, top, 12, STONE[4]); cv.hline(cx - 1, top + 1, 12, IRON[1])
    brick_wall(cv, 6, 46, w - 12, 52, seed=21)
    cv.hline(6, 46, w - 12, BRASS[4]); cv.hline(6, 47, w - 12, IRON[1])
    for wx in range(14, w - 14, 22):  # tall arched windows, furnace-lit
        if 50 < wx < 92:
            continue
        for (x, y) in rect_set(wx, 56, 8, 20) | {(x, y) for (x, y) in disc(wx + 4, 56, 4) if y < 56}:
            cv.set(x, y, WARM[3] if y < 62 else WARM[2] if y < 70 else '#C2380E')
        cv.vline(wx + 4, 52, 24, IRON[1])
    door = {(x, y) for (x, y) in disc(72, 70, 16) if y < 70} | rect_set(56, 70, 32, 28)
    for (x, y) in door:
        d = abs(x - 72) / 16 + (98 - y) / 50
        c = '#FFE9A0' if d < 0.45 else '#FFB648' if d < 0.75 else '#F2721E' if d < 1.0 else '#C2380E'
        cv.set(x, y, c)
    for (x, y) in door:
        if (x - 1, y) not in door or (x + 1, y) not in door or (x, y - 1) not in door:
            cv.set(x, y, BRICK[4] if x < 72 else BRICK[1])
    for (x, y) in oval(72, 92, 6, 3):  # a crucible pouring
        cv.set(x, y, IRON[1])
    cv.hline(69, 90, 6, '#FFE9A0')
    detail.stones(cv, 4, 98, w - 8, 8, STONE, seed=23, course=4)
    for k, (mx, my) in enumerate(((108, 92), (116, 94), (124, 91))):  # moulds
        for (x, y) in oval(mx, my, 4, 2.5):
            cv.set(x, y, IRON[3] if x < mx else IRON[1])
    return cv


def tube_station() -> Canvas:
    """The atmospheric railway's terminus, 84 x 92: Cogsworth's end of the line from Neon
    Harbour, built the Victorian way (Matt's World Logic answer 11: keep it, detail it).
    How it is built: a round booking hall, its drum of red brick between dressed-stone
    pilasters on a stone plinth, a cornice round its top; over it a cast-iron dome, ribs
    and rings holding glass panes that show the dusk sky high up and the hall's warm light
    lower down, a lantern and finial at its crown. Its door in a stone surround with a
    fanlight and a clock over it, arched windows lit either side, a step down to the
    forecourt. The brass tube the capsules run in leaves from its east side through a
    bolted collar. Its drum stands a storey and more (42 px) round a 14 x 32 door."""
    w, h = 84, 92
    cv = Canvas(w, h, pad=PAD)
    cx, R = 38, 30  # the drum's centre and radius
    dome_top, drum_top, drum_bot = 8, 40, 82
    # the dome: ribs every 8 px, rings every 8, panes between; sky high up, the hall's light low
    for y in range(dome_top, drum_top):
        t = (drum_top - y) / (drum_top - dome_top)
        half = int(math.sqrt(max(0.0, 1 - t ** 2)) * R)
        for x in range(cx - half, cx + half + 1):
            k = (x - cx) / max(1, half)
            rib = round((x - cx) / max(1, half) * 4) != round((x + 1 - cx) / max(1, half) * 4) or (y - dome_top) % 8 == 0
            if rib and (y - dome_top) % 8 == 0:
                c = BRASS[4] if k < -0.3 else BRASS[3] if k < 0.3 else BRASS[1]  # the rings, brass
            elif rib:
                c = IRON[4] if k < -0.3 else IRON[3] if k < 0.3 else IRON[1]  # the ribs, cast iron
            elif t > 0.55:
                SKY = ['#3E5872', '#4A6680', '#6E92A8', '#86AABE', '#9FC2D2', '#B8D6E2']
                pane = noise2(round((x - cx) / max(1, half) * 4), (y - dome_top) // 8, 1792)
                i = 4 if k < -0.2 else 2 if k < 0.4 else 1
                c = SKY[min(5, max(0, i + (1 if pane > 0.66 else -1 if pane < 0.33 else 0)))]  # each pane its own sky
                if (x + y) % 11 == 0 and k < 0:
                    c = '#D8ECF2'  # a glint
            else:
                pane = noise2(round((x - cx) / max(1, half) * 4), (y - dome_top) // 8, 1793)
                c = WARM[3] if k < -0.3 else WARM[2] if k < 0.4 else WARM[1]  # the hall's light through the low panes
                if pane > 0.7 and k < 0.4:
                    c = '#E8B860'  # a pane with a lamp close behind it
                elif pane < 0.2:
                    c = '#C08838'
                if (y - dome_top) % 8 == 7:
                    c = '#A06A28'  # the panes' lower glazing bars
            cv.set(x, y, c)
    for y in range(0, dome_top + 2):  # the lantern and its finial
        hw = 1 if y < 4 else 3
        for x in range(cx - hw, cx + hw + 1):
            c = BRASS[5] if y == 0 else BRASS[4] if x < cx else BRASS[2]
            if 4 <= y < dome_top and abs(x - cx) < 2:
                c = WARM[3]
            cv.set(x, y, c)
    # the cornice over the drum
    for x in range(cx - R - 1, cx + R + 2):
        k = (x - cx) / R
        cv.set(x, drum_top, ASHLAR[5] if k < 0.3 else ASHLAR[3])
        cv.set(x, drum_top + 1, ASHLAR[3] if k < 0.3 else ASHLAR[1])
        cv.set(x, drum_top + 2, ASHLAR[0])
    for (bx, d) in ((cx - 22, 1), (cx + 9, -1)):  # pigeons on the cornice
        cv.set(bx, drum_top - 2, '#8A8E9A'); cv.set(bx + d, drum_top - 2, '#6A6E7A'); cv.set(bx, drum_top - 1, '#5A5E6A'); cv.set(bx + d, drum_top - 1, '#5A5E6A')
        cv.set(bx - d, drum_top - 3, '#9EA2AE')
    # the drum: brick in courses, curving away (lit on its west, darker east), pilasters every 12
    for y in range(drum_top + 3, drum_bot):
        for x in range(cx - R, cx + R + 1):
            k = (x - cx) / R
            shade = 0 if k < -0.6 else 1 if k < 0.1 else 2 if k < 0.65 else 3
            row = (y - drum_top) // 3
            brick = (x + (row % 2) * 3) // 6
            n = noise2(brick, row, 1760)
            ramp = BRICK if n < 0.7 else ['#3A1C14', '#5E2C1E', '#844230', '#A85A40', '#C87A58']  # a hotter-fired brick here and there
            c = ramp[max(0, 4 - shade - (1 if 0.45 < n < 0.7 else 0))]
            if noise2(x // 2, 0, 1761) > 0.85 and y > drum_top + 6:
                c = ramp[max(0, 3 - shade - 1)]  # a soot streak down from the cornice
            if (y - drum_top) % 3 == 0 or (x + (row % 2) * 3) % 6 == 0:
                c = ramp[max(0, 1 - shade // 2)]  # the mortar, dark with soot
            p = (x - cx + 60) % 14
            if p < 3:  # a stone pilaster
                c = ASHLAR[max(1, 4 - shade - (1 if p == 2 else 0))]
                if (y - drum_top) % 6 == 0:
                    c = ASHLAR[max(0, 3 - shade)]
            cv.set(x, y, c)
    for x in range(cx - R, cx + R + 1):  # a string course between the tiers
        k = (x - cx) / R
        cv.set(x, 56, ASHLAR[4] if k < 0.2 else ASHLAR[2]); cv.set(x, 57, ASHLAR[1])
    for (bx, cols) in ((cx - 29, ('#E8DCC0', '#B83A2E')), (cx + 23, ('#D8D4C4', '#2E4A7A'))):  # bills pasted on the drum
        for (x, y) in rect_set(bx, 62, 5, 8):
            c = cols[0] if (y - 62) % 3 else cols[1]
            if x == bx + 4 or y == 69:
                c = '#9A9078'  # its curling edge
            cv.set(x, y, c)
    for lx in (cx - 12, cx + 12):  # gas lamps on brackets either side of the door
        cv.hline(lx - 1, 58, 3, IRON[3])
        for (x, y) in rect_set(lx - 1, 59, 3, 4):
            cv.set(x, y, WARM[3] if y < 61 else WARM[2])
        cv.hline(lx - 1, 63, 3, IRON[1]); cv.set(lx, 57, IRON[4])
    for px in (cx - 19, cx + 17):  # arched windows, lit, a glazing bar, a stone sill
        for y in range(60, 76):
            for x in range(px - 3, px + 4):
                if y < 63 and abs(x - px) > (y - 59):
                    continue
                c = WARM[3] if y < 66 else WARM[2]
                if x == px or y == 68:
                    c = '#3A2A1A'
                cv.set(x, y, c)
        cv.hline(px - 4, 76, 9, ASHLAR[4]); cv.hline(px - 4, 77, 9, ASHLAR[1])
        for (x, y) in ((px - 4, 61), (px + 4, 61), (px, 58)):
            cv.set(x, y, ASHLAR[4])  # the arch's keystone and springers
    for (fx, col) in ((cx - 20, '#3A4258'), (cx + 16, '#5A2A24')):  # someone inside each window, against the lamplight
        for (x, y) in rect_set(fx, 66, 2, 6):
            cv.set(x, y, col)
        cv.set(fx, 64, '#E0A882'); cv.set(fx + 1, 64, '#B07858'); cv.set(fx, 65, '#B07858'); cv.set(fx + 1, 65, '#B07858')
    for px in (cx - 19, cx + 17):  # round windows in the upper tier
        porthole(cv, px, 48, 3.4)
    dy0 = drum_bot - 32
    for (x, y) in rect_set(cx - 9, dy0 - 3, 18, 35):  # the door's stone surround
        cv.set(x, y, ASHLAR[4] if x < cx else ASHLAR[3])
    for (x, y) in rect_set(cx - 7, dy0, 14, 32):  # the door: a fanlight, glazed panels, panels below
        c = '#2C3E4C' if x < cx else '#1E2A34'
        if y < dy0 + 5:
            c = WARM[3] if (x + y) % 3 else '#E8E2D2'
        elif 7 <= y - dy0 < 16 and x not in (cx - 7, cx - 1, cx, cx + 6):
            c = WARM[3] if y - dy0 < 11 else WARM[2]
        elif y - dy0 in (19, 26) and x not in (cx - 7, cx - 1, cx, cx + 6):
            c = '#3E566A'
        cv.set(x, y, c)
    cv.set(cx - 2, dy0 + 19, BRASS[5]); cv.set(cx + 1, dy0 + 19, BRASS[5])  # the handles
    for tx in (cx - 16,):  # a tub of marigolds by the door, in a cast-iron planter
        for (x, y) in rect_set(tx, drum_bot - 5, 6, 5):
            cv.set(x, y, IRON[3] if y == drum_bot - 5 else IRON[2] if x < tx + 4 else IRON[1])
        for (x, y) in ((tx, drum_bot - 7), (tx + 1, drum_bot - 7), (tx + 3, drum_bot - 8), (tx + 4, drum_bot - 8),
                       (tx + 2, drum_bot - 6), (tx + 5, drum_bot - 6)):
            cv.set(x, y, '#F0A020')
        for (x, y) in ((tx + 1, drum_bot - 6), (tx + 2, drum_bot - 7), (tx + 4, drum_bot - 6), (tx + 3, drum_bot - 6)):
            cv.set(x, y, '#3E6438')
        cv.set(tx + 3, drum_bot - 9, '#C86A10'); cv.set(tx + 4, drum_bot - 9, '#C86A10')
    for (x, y) in rect_set(cx + 11, drum_bot - 11, 4, 11):  # a red pillar box by the door, its cap and slot
        c = '#C83A2C' if x < cx + 13 else '#8E2620'
        if y < drum_bot - 9:
            c = '#E25A44' if x < cx + 13 else '#A83226'
        if y == drum_bot - 7:
            c = '#2A1210'
        cv.set(x, y, c)
    for (x, y) in rect_set(cx - 13, dy0 - 3, 4, 3):  # gilt brackets either side of the door
        cv.set(x, y, GOLD[3] if y == dy0 - 3 else GOLD[2])
    for (x, y) in rect_set(cx + 10, dy0 - 3, 4, 3):
        cv.set(x, y, GOLD[3] if y == dy0 - 3 else GOLD[2])
    for (x, y) in disc(cx, dy0 - 8, 3.6):  # the clock over the door
        cv.set(x, y, BRASS[3] if (x - cx) + (y - dy0 + 8) < 0 else BRASS[1])
    for (x, y) in disc(cx, dy0 - 8, 2.4):
        cv.set(x, y, '#F2ECDA')
    cv.set(cx, dy0 - 10, IRON[0]); cv.set(cx, dy0 - 9, IRON[0]); cv.set(cx + 1, dy0 - 8, IRON[0])
    # the tube's collar on the east side, bolted, and the tube going on east
    ty0, ty1 = 56, 72
    for y in range(ty0, ty1):
        for x in range(cx + R - 2, w - 1):
            k = (y - ty0) / (ty1 - ty0)
            c = BRASS[4] if k < 0.2 else BRASS[3] if k < 0.5 else BRASS[2] if k < 0.85 else BRASS[1]
            if (x - cx) % 10 == 0:
                c = IRON[1]
            cv.set(x, y, c)
    for y in range(ty0 - 3, ty1 + 3):  # the collar
        for x in range(cx + R - 3, cx + R + 3):
            c = IRON[3] if x < cx + R else IRON[1]
            if (y - ty0) % 4 == 0 and x == cx + R - 1:
                c = BRASS[5]  # its bolts
            cv.set(x, y, c)
    IVY = ['#1E3422', '#2E4A2E', '#3E6438', '#5A8046']
    for y in range(drum_top + 6, drum_bot):  # ivy up the drum's west side, in leaf clusters
        reach = 4 + int(noise2(y // 3, 1, 1803) * 5)
        for x in range(cx - R, cx - R + reach):
            n = noise2(x // 2, y // 2, 1804)
            if n > 0.35:
                cv.set(x, y, IVY[3] if n > 0.82 else IVY[2] if n > 0.6 else IVY[1] if n > 0.45 else IVY[0])
    detail.stones(cv, cx - R - 2, drum_bot, 2 * R + 5, 6, STONE, seed=29, course=3)
    for (x, y) in rect_set(cx - 10, drum_bot, 20, 3):  # the step before the door
        cv.set(x, y, STONE[4] if y == drum_bot else STONE[2])
    return cv


def atmos_car() -> Canvas:
    """The tube's glazed inspection length by the terminus, 44 x 22 (Matt's World Logic
    answer 11). Why: the capsules run inside the tube, driven by the air pumped out ahead
    of them, so one is never seen riding on top of it; here a length of the tube is glazed
    between brass hoops, and a capsule waiting to leave shows inside, its portholes lit,
    its riveted brass shell lit from the station's side."""
    w, h = 44, 22
    cv = Canvas(w, h, pad=PAD)
    t0, t1 = 3, 19  # the tube's top and bottom rows (it lies 16 px across, as the zone's)
    for x in range(0, w):
        for y in range(t0, t1):
            k = (y - t0) / (t1 - t0)
            c = '#5E7C8A' if k < 0.2 else '#3E5662' if k < 0.6 else '#2C3E48'  # the glass, the dusk in it
            cv.set(x, y, c)
    for (x, y) in oval(22, 11, 16, 5.5):  # the capsule inside
        k = (y - 5) / 11
        c = BRASS[4] if k < 0.3 else BRASS[3] if k < 0.6 else BRASS[2]
        if x % 6 == 0 and k > 0.25:
            c = BRASS[1]
        cv.set(x, y, c)
    for x in range(8, 37):  # a red band round the capsule, lined in gold
        for y in range(13, 15):
            if (x, y) in oval(22, 11, 16, 5.5):
                cv.set(x, y, RED[3] if y == 13 else RED[2])
        if (x, 15) in oval(22, 11, 16, 5.5):
            cv.set(x, 15, GOLD[3])
    for px in (14, 20, 26, 32):
        porthole(cv, px, 10, 1.8)
    for x in range(1, w):  # the trestle's saddle under each hoop, and the glass's reflections
        if x % 11 in (4, 5, 6):
            cv.set(x, t1, IRON[2] if x % 11 == 4 else IRON[1])
    for x in range(3, w, 11):
        for d in range(4):
            cv.set(x + d, t0 + 3 + d, '#7E9CAA'); cv.set(x + d + 1, t0 + 3 + d, '#7E9CAA')  # a streak of light across the curved glass
    for x in range(0, w, 11):  # the hoops holding the glass, flanged and bolted
        for y in range(t0 - 1, t1 + 1):
            cv.set(x, y, BRASS[4] if y < t0 + 4 else BRASS[2])
            cv.set(x + 1, y, BRASS[1])
    for x in range(0, w):  # the glass's sheen along its top, its seam along the bottom
        if x % 11 > 1:
            cv.set(x, t0, '#C8DCE4' if (x // 3) % 2 else '#9AB4C0')
            if (x - 3) % 11 < 4:
                cv.set(x, t0 + 1, '#B0C8D2')
        cv.set(x, t1 - 1, BRASS[1])
    return cv


def automaton() -> Canvas:
    """A clockwork gardener, 26 x 44: a round brass head with one warm eye, a barrel
    body with a key in its back, jointed arms holding a watering can."""
    w, h = 26, 44
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in disc(12, 8, 6):
        cv.set(x, y, BRASS[4] if x + y < 18 else BRASS[2])
    cv.set(14, 8, WARM[3]); cv.set(15, 8, WARM[2])
    for y in range(14, 32):
        for x in range(6, 19):
            k = (x - 6) / 12
            cv.set(x, y, COPPER[3] if k < 0.3 else COPPER[2] if k < 0.75 else COPPER[1])
        if y % 5 == 0:
            cv.hline(6, y, 13, BRASS[3])
    gear(cv, 4, 22, 2.5, BRASS, teeth=6, hub=False)  # the key
    for y in range(32, 42):
        cv.set(9, y, IRON[3]); cv.set(15, y, IRON[2])
    cv.hline(7, 42, 4, IRON[1]); cv.hline(13, 42, 4, IRON[1])
    for t in range(6):  # an arm out to the can
        cv.set(18 + t // 2, 18 + t, IRON[3])
    for (x, y) in rect_set(19, 24, 6, 5):
        cv.set(x, y, '#5A7A8A' if x < 22 else '#3E5A6A')
    cv.set(25, 23, '#5A7A8A'); cv.set(25, 26, SNOW[2])
    return cv


def cloche() -> Canvas:
    """A glass bell cloche over a seedling, 14 x 12, brass knob on top."""
    cv = Canvas(14, 12, pad=PAD)
    for (x, y) in oval(7, 7, 6, 5):
        if y <= 9:
            cv.set(x, y, SNOW[3] if x < 5 and y < 6 else '#9AB8B0' if x < 9 else '#6E8A86')
    cv.set(7, 1, BRASS[4])
    cv.set(6, 7, '#62995E'); cv.set(8, 7, '#447A50'); cv.set(7, 8, '#447A50')
    cv.hline(1, 10, 13, '#3A2A22')
    return cv

SLATE = MATERIALS['slate']
ASHLAR = MATERIALS['ashlar']
TAR = MATERIALS['tar']
BROWN = ['#2A1A16', '#46302A', '#5E4236', '#7A5846', '#98725A']  # a darker, browner brick


def sash(cv: Canvas, x0: int, y0: int, ww: int = 10, wh: int = 14, lit: bool = True, sill=STONE):
    """A sash window in a painted frame: two panes over two, warm or dark glass, a stone
    lintel above and a lit sill below; returns its pixels (proud of the wall)."""
    pts = rect_set(x0 - 1, y0 - 2, ww + 2, wh + 4)
    for (x, y) in rect_set(x0, y0, ww, wh):
        top = y < y0 + wh // 2
        g = (WARM[3] if top else WARM[2]) if lit else (SLATE[2] if top else SLATE[1])
        if x in (x0, x0 + ww - 1) or y in (y0, y0 + wh - 1, y0 + wh // 2) or x == x0 + ww // 2:
            g = '#E8E2D2' if x < x0 + ww // 2 or y == y0 else '#B8B0A0'  # the frame and glazing bars
        cv.set(x, y, g)
    if lit:
        cv.set(x0 + 2, y0 + 2, '#FFF6D8')
    cv.hline(x0 - 1, y0 - 2, ww + 2, sill[4]); cv.hline(x0 - 1, y0 - 1, ww + 2, sill[2])  # the lintel
    cv.hline(x0 - 1, y0 + wh, ww + 2, sill[4]); cv.hline(x0 - 1, y0 + wh + 1, ww + 2, sill[1])  # the sill
    return pts


def panel_door(cv: Canvas, x0: int, y1: int, dw: int = 14, dh: int = 24, paint=None):
    """A panelled front door with a fanlight and a brass knob, a stone step before it;
    returns its pixels."""
    paint = paint or ['#1E2A34', '#2C3E4C', '#3E566A', '#5A7690']
    y0 = y1 - dh
    pts = set()
    for (x, y) in rect_set(x0, y0, dw, dh):
        c = paint[2] if x < x0 + dw // 2 else paint[1]
        if x in (x0, x0 + dw - 1):
            c = paint[0]
        px_, py_ = (x - x0) % (dw // 2), (y - y0 - 6)
        if 1 <= px_ <= dw // 2 - 2 and py_ >= 0 and py_ % 9 in (0, 7):
            c = paint[3] if py_ % 9 == 0 else paint[0]  # the panels' mouldings
        cv.set(x, y, c)
        pts.add((x, y))
    for (x, y) in rect_set(x0, y0, dw, 5):  # the fanlight
        cv.set(x, y, WARM[3] if (x + y) % 3 else '#E8E2D2')
    cv.hline(x0, y0 + 5, dw, '#E8E2D2')
    ky = y0 + dh * 3 // 5  # the knob at a hand's height
    cv.set(x0 + dw - 4, ky, BRASS[5]); cv.set(x0 + dw - 4, ky + 1, BRASS[2])
    cv.hline(x0 - 3, y0 - 2, dw + 6, STONE[4]); cv.hline(x0 - 3, y0 - 1, dw + 6, STONE[2])  # the hood
    for (x, y) in rect_set(x0 - 2, y1, dw + 4, 3):  # the step
        cv.set(x, y, STONE[4] if y == y1 else STONE[2] if y == y1 + 1 else STONE[1])
        pts.add((x, y))
    return pts


def brick_stack(cv: Canvas, x0: int, y0: int, y1: int, w: int = 10, pots: int = 2):
    """A brick chimney stack on a roof, lit on its west face, with a stone cap and pots."""
    for y in range(y0, y1):
        for x in range(x0, x0 + w):
            c = BRICK[4] if x < x0 + 2 else BRICK[3] if x < x0 + w - 3 else BRICK[1]
            if (y - y0 + ((x - x0) // 4) * 2) % 4 == 3:
                c = BRICK[1] if x < x0 + w - 3 else BRICK[0]
            cv.set(x, y, c)
    cv.hline(x0 - 1, y0, w + 2, STONE[4]); cv.hline(x0 - 1, y0 + 1, w + 2, STONE[2])
    for k in range(pots):
        px = x0 + 1 + k * (w // max(1, pots))
        for y in range(y0 - 4, y0):
            cv.set(px, y, '#C27A52'); cv.set(px + 1, y, '#A65E3E'); cv.set(px + 2, y, '#7A4230')
        cv.hline(px, y0 - 5, 3, '#2A1A16')


def townhouse(width: int = 88, storeys: int = 2, roof=None, wall: str = 'brown', door_x: int | None = None,
              shop: bool = False, chimney: int = 1, seed: int = 0) -> Canvas:
    """A Cogsworth house or shop in the three-quarter view, built like the workshops (a
    top-down gable roof, its gable to the front, walls under it) but varied: slate or
    tarred iron roofs, brown brick or dressed ashlar, one or two storeys with a stone
    string course, sash windows with lintels and sills, a panelled door with a fanlight
    and a step, a brick stack with pots, a drainpipe; a shop has a glazed front under a
    striped awning and a signboard.

    Storeys follow the scale table (verticality.md section 5): an upper storey 32 px, the
    ground storey 42 (a shop's 48, room for its awning and signboard over a door), doors
    14 x 32, windows 12 x 16."""
    roof = roof or SLATE
    w = width
    storey = 32
    ground = 48 if shop else 42
    apex_y, eave_y = 20, 42
    wall_top = eave_y
    wall_bottom = wall_top + storey * (storeys - 1) + ground
    h = wall_bottom + 8
    cv = Canvas(w, h, pad=PAD)
    ridge = (w - 1) / 2
    sx = int(ridge + chimney * w * 0.24) - 5
    stack = rect_set(sx, 2, 10, apex_y)
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, roof, hole=stack, seed=91 + seed, moss=None,
                    barge=WOOD if roof is SLATE else IRON)
    brick_stack(cv, sx, 6, 6 + apex_y - 4)
    ramp = ASHLAR if wall == 'ashlar' else BROWN if wall == 'brown' else BRICK
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2),
                     7, w - 8, apex_y, wall_top, ['#B8AE9C', '#CFC6B2', '#E2DACB', '#EEE8DA', '#F6F2E8'], boards=False)
    if wall == 'ashlar':
        detail.stones(cv, 7, wall_top, w - 14, wall_bottom - wall_top, ASHLAR, seed=31 + seed, course=5, base=3)
    else:
        detail.bricks(cv, 7, wall_top, w - 14, wall_bottom - wall_top, ramp, seed=33 + seed, base=3)
    for x in range(7, w - 7):  # soot low on the wall
        for y in range(wall_bottom - 3, wall_bottom):
            detail.shade(cv, x, y, 1)
    proud = set()
    if storeys > 1:  # the string course between the floors
        sy = wall_top + storey
        cv.hline(6, sy, w - 12, STONE[4]); cv.hline(6, sy + 1, w - 12, STONE[2])
        proud |= rect_set(6, sy, w - 12, 2)
    # the gable's round window, and the upper floor's windows
    porthole(cv, ridge, 33, 4, warm=bool(seed % 2))
    proud |= disc(ridge, 33, 4)
    dx = door_x if door_x is not None else int(ridge) - 7
    if storeys > 1:
        n = 3 if w >= 88 else 2
        for k in range(n):
            wx = int(12 + (w - 36) * k / max(1, n - 1))
            proud |= sash(cv, wx, wall_top + 8, 12, 16, lit=(k + seed) % 3 != 1)
    if shop:
        fx0, fx1 = 11, w - 11
        fy0, fy1 = wall_bottom - 34, wall_bottom - 1
        for (x, y) in rect_set(fx0, fy0, fx1 - fx0, fy1 - fy0):  # the glazed shop front
            c = WARM[3] if y < fy0 + 8 else WARM[2]
            if (x - fx0) % 9 == 0 or y in (fy0, fy1 - 1):
                c = '#2C3E4C' if (x - fx0) % 9 == 0 else '#3E566A'
            cv.set(x, y, c)
        for k, gx in enumerate(range(fx0 + 4, fx1 - 4, 9)):  # goods in the window
            if gx < dx - 2 or gx > dx + 16:
                for shelf in (fy1 - 3, fy1 - 14):
                    cv.set(gx, shelf, BRASS[4] if k % 2 else COPPER[3]); cv.set(gx + 1, shelf, BRASS[2])
                    cv.set(gx, shelf - 1, BRASS[3] if k % 2 else COPPER[4])
                cv.hline(gx - 1, fy1 - 12, 4, '#3E566A')  # the shelf
        proud |= rect_set(fx0, fy0, fx1 - fx0, fy1 - fy0)
        ay = fy0 - 6  # the striped awning, a plane sloping out toward us
        for y in range(ay, fy0):
            for x in range(fx0 - 3, fx1 + 3):
                stripe = ((x - fx0) // 5) % 2
                c = ('#C8463A' if stripe else '#F2ECDE') if y < fy0 - 2 else ('#9A3028' if stripe else '#C8C0B0')
                cv.set(x, y, c)
        cv.hline(fx0 - 3, fy0, fx1 - fx0 + 6, '#5A2018')
        proud |= rect_set(fx0 - 3, ay, fx1 - fx0 + 6, 7)
        sy0 = ay - 6  # the signboard over it
        for (x, y) in rect_set(fx0 + 6, sy0, fx1 - fx0 - 12, 5):
            c = '#2C3E4C' if 0 < x - fx0 - 6 < fx1 - fx0 - 13 and 0 < y - sy0 < 4 else BRASS[3]
            if c == '#2C3E4C' and (x // 2) % 3 and y == sy0 + 2:
                c = '#E8D8A8'  # the lettering
            cv.set(x, y, c)
        proud |= rect_set(fx0 + 6, sy0, fx1 - fx0 - 12, 5)
    else:
        for k, wx in enumerate((12, w - 24)):
            if abs(wx - dx) > 15:
                proud |= sash(cv, wx, wall_bottom - 27, 12, 16, lit=(k + seed) % 2 == 0)
    proud |= panel_door(cv, dx, wall_bottom - 1, 14, 32)
    for y in range(wall_top + 1, wall_bottom):  # the drainpipe down the corner
        cv.set(w - 11, y, IRON[3]); cv.set(w - 10, y, IRON[1])
        if y % 9 == 0:
            cv.hline(w - 12, y, 4, IRON[2])
    proud |= rect_set(w - 11, wall_top + 1, 2, wall_bottom - wall_top - 1)
    detail.cast(cv, proud, 1, 1, k=1, on=ramp, reach=2)
    detail.overhang_shadow(cv, 7, w - 7, wall_top, lambda x: 3, k=2, cap=1)
    detail.stones(cv, 5, wall_bottom, w - 10, 8, STONE, seed=37 + seed, course=4)
    return cv


def lock_hut() -> Canvas:
    """The lock-keeper's hut on the towpath by the lock, 44 x 68 (size guide 32 to 48 by
    48 to 72; Matt's World Logic answer 9). One room of brown brick under a slate gable,
    its door toward the lock with a step, a window lit beside it, a stack with a pot (a
    stove inside), the windlass the keeper winds the paddles with hung on a hook by the
    door, a lamp on a bracket over it, a board of tolls, a water butt at the corner."""
    w = 44
    apex_y, eave_y = 12, 28
    wall_top, wall_bottom = eave_y, eave_y + 34
    h = wall_bottom + 6
    cv = Canvas(w, h, pad=PAD)
    ridge = (w - 1) / 2
    sx = int(ridge + w * 0.22) - 3
    stack = rect_set(sx, 0, 7, apex_y + 2)
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, SLATE, hole=stack, seed=95, moss=None, barge=WOOD)
    brick_stack(cv, sx, 4, apex_y + 2, w=7, pots=1)
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2),
                     6, w - 7, apex_y, wall_top, ['#B8AE9C', '#CFC6B2', '#E2DACB', '#EEE8DA', '#F6F2E8'], boards=False)
    detail.bricks(cv, 6, wall_top, w - 12, wall_bottom - wall_top, BROWN, seed=41, base=3)
    for x in range(6, w - 6):  # soot and damp low on the wall
        for y in range(wall_bottom - 3, wall_bottom):
            detail.shade(cv, x, y, 1)
    proud = set()
    porthole(cv, ridge, 21, 2.6, warm=True)  # a round vent in the gable
    proud |= panel_door(cv, 9, wall_bottom - 1, 12, 28, paint=['#1E2A20', '#2C4232', '#3E5C46', '#5A7C62'])
    proud |= sash(cv, 26, wall_bottom - 24, 10, 14, lit=True)
    for (x, y) in ((24, wall_bottom - 18), (24, wall_bottom - 17)):  # the windlass on its hook
        cv.set(x, y, IRON[3])
    for t in range(6):
        cv.set(23 + t // 3, wall_bottom - 16 + t, IRON[2] if t % 2 else IRON[4])
    cv.hline(22, wall_bottom - 11, 4, IRON[2])
    cv.hline(14, wall_top + 2, 6, IRON[2])  # the lamp's bracket over the door, and the lamp
    for (x, y) in rect_set(18, wall_top + 3, 3, 4):
        cv.set(x, y, WARM[3] if y < wall_top + 5 else WARM[2])
    cv.hline(17, wall_top + 2, 5, IRON[1])
    for (x, y) in rect_set(27, wall_top + 3, 9, 6):  # the board of tolls, its lines of figures
        c = '#2A3A30' if 0 < x - 27 < 8 and 0 < y - wall_top - 3 < 5 else WOOD[3]
        if c == '#2A3A30' and (x % 3) and (y - wall_top) % 2 == 0:
            c = '#D8D0B8'
        cv.set(x, y, c)
    proud |= rect_set(27, wall_top + 3, 9, 6)
    for (x, y) in rect_set(w - 9, wall_bottom - 10, 7, 10):  # the water butt, hooped
        c = WOOD[3] if x < w - 6 else WOOD[2]
        if y in (wall_bottom - 8, wall_bottom - 3):
            c = IRON[2]
        if y == wall_bottom - 10:
            c = '#24343A'
        cv.set(x, y, c)
    proud |= rect_set(w - 9, wall_bottom - 10, 7, 10)
    IVY = ['#1E3422', '#2E4A2E', '#3E6438', '#5A8046']
    for y in range(wall_top + 2, wall_bottom):  # ivy up the west corner, in leaf clusters
        reach = 3 + int(noise2(y // 3, 0, 1790) * 4) - max(0, (wall_top + 12 - y) // 3)
        for x in range(6, 6 + max(0, reach)):
            n = noise2(x // 2, y // 2, 1791)
            if n > 0.3:
                cv.set(x, y, IVY[3] if n > 0.8 else IVY[2] if n > 0.55 else IVY[1])
    for (x, y) in rect_set(22, wall_bottom - 4, 4, 4):  # a pot of geraniums by the door
        cv.set(x, y, '#B8603C' if x < 24 else '#8A4428')
    for (x, y) in ((22, wall_bottom - 6), (23, wall_bottom - 7), (25, wall_bottom - 6), (24, wall_bottom - 5)):
        cv.set(x, y, '#D23A30' if (x + y) % 2 else '#3E6438')
    detail.cast(cv, proud, 1, 1, k=1, on=BROWN, reach=2)
    detail.overhang_shadow(cv, 6, w - 6, wall_top, lambda x: 3, k=2, cap=1)
    detail.stones(cv, 4, wall_bottom, w - 8, 6, STONE, seed=43, course=3)
    return cv


def warehouse() -> Canvas:
    """A canal warehouse, 112 x 116: three storeys of brown brick under a long slate roof,
    a column of loft doors over the cart door, a hoist beam out over them with its
    pulley and rope, small barred windows, iron tie-plates, and a painted name band."""
    w = 112
    storey = 22
    apex_y, eave_y = 18, 38
    wall_top, wall_bottom = eave_y, eave_y + 3 * storey + 4
    h = wall_bottom + 8
    cv = Canvas(w, h, pad=PAD)
    ridge = (w - 1) / 2
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, SLATE, seed=97, moss=None, barge=IRON)
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2),
                     7, w - 8, apex_y, wall_top, BROWN, boards=False)
    detail.bricks(cv, 7, apex_y + 4, w - 14, wall_top - apex_y - 4, BROWN, seed=41, base=3)
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, SLATE, seed=97, moss=None, barge=IRON)
    detail.bricks(cv, 7, wall_top, w - 14, wall_bottom - wall_top, BROWN, seed=43, base=3)
    proud = set()
    for (x, y) in rect_set(18, wall_top + 3, w - 36, 6):  # the name band
        c = '#E8DCC0' if 0 < y - wall_top - 3 < 5 else '#2A1A16'
        if c == '#E8DCC0' and y == wall_top + 5 and (x // 2) % 4 and 22 < x < w - 22:
            c = '#3A2A22'
        cv.set(x, y, c)
    proud |= rect_set(18, wall_top + 3, w - 36, 6)
    cx = int(ridge)
    for k in range(3):  # the loft doors, one a floor, the cart door at the bottom
        y0 = wall_top + 12 + k * storey
        dh = 16 if k < 2 else 26
        y0 = y0 if k < 2 else wall_bottom - dh
        for (x, y) in rect_set(cx - 8, y0, 16, dh):
            c = WOOD[3] if (x - cx + 8) % 4 else WOOD[2]
            if x in (cx - 8, cx + 7) or y == y0:
                c = WOOD[1]
            if k < 2 and abs((x - cx) - (y - y0 - 8)) < 1:
                c = WOOD[4]  # the brace
            cv.set(x, y, c)
        cv.hline(cx - 10, y0 - 2, 20, STONE[4]); cv.hline(cx - 10, y0 - 1, 20, STONE[2])
        proud |= rect_set(cx - 10, y0 - 2, 20, dh + 2)
        for wx in (16, 36, w - 46, w - 26):  # small barred windows
            if k < 2 or wx in (16, w - 26):
                wy = y0 + 2 if k < 2 else wall_bottom - 20
                for (x, y) in rect_set(wx, wy, 10, 10):
                    c = (WARM[2] if (k + wx // 20) % 3 == 0 else '#1E2A34') if (x - wx) % 3 else IRON[3]
                    cv.set(x, y, c)
                cv.hline(wx - 1, wy - 1, 12, STONE[4]); cv.hline(wx - 1, wy + 10, 12, STONE[3])
                proud |= rect_set(wx - 1, wy - 1, 12, 12)
    for (tx, ty) in ((10, wall_top + 26), (w - 13, wall_top + 26), (10, wall_top + 48), (w - 13, wall_top + 48)):
        for (x, y) in disc(tx + 1, ty, 2):  # iron tie-plates
            cv.set(x, y, IRON[3] if x <= tx else IRON[1])
    # the hoist: a beam out from the gable over the loft doors, a pulley, rope to a hook
    for y in range(wall_top - 2, wall_top + 2):
        for x in range(cx - 3, cx + 4):
            cv.set(x, y, WOOD[4] if y == wall_top - 2 else WOOD[2])
    for (x, y) in disc(cx, wall_top + 4, 2.5):
        cv.set(x, y, IRON[3] if x < cx else IRON[1])
    for y in range(wall_top + 6, wall_top + 30):
        cv.set(cx + 2, y, MATERIALS['rope'][2])
    cv.set(cx + 1, wall_top + 30, IRON[3]); cv.set(cx + 2, wall_top + 31, IRON[3]); cv.set(cx + 3, wall_top + 30, IRON[3])
    detail.cast(cv, proud, 1, 1, k=1, on=BROWN, reach=2)
    detail.overhang_shadow(cv, 7, w - 7, wall_top, lambda x: 3, k=2, cap=1)
    detail.stones(cv, 5, wall_bottom, w - 10, 8, STONE, seed=45, course=4)
    return cv


def water_tower() -> Canvas:
    """The engine shed's water tower, 52 x 76: a riveted iron tank with a lit lid seen from
    above, on a brick base with an arched doorway, a leather hose swung up on its
    jib, a ladder up the side."""
    w, h = 52, 76
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(26, 10, 22, 7):  # the tank's top: a lid and its rim
        k = ((x - 26) / 22) ** 2 + ((y - 10) / 7) ** 2
        c = IRON[4] if k > 0.75 and (x < 26 or y < 9) else IRON[3] if k > 0.7 else IRON[2] if x < 30 else IRON[1]
        cv.set(x, y, c)
    for (x, y) in oval(24, 9, 5, 2):
        cv.set(x, y, IRON[1])  # the hatch
    for y in range(10, 38):  # the tank's side: a cylinder lit on the left
        for x in range(4, 49):
            if y > 10 + 7 * math.sqrt(max(0.0, 1 - ((x - 26) / 22) ** 2)) - 7 * 0 and y >= 10:
                if y < 10 + int(7 * math.sqrt(max(0.0, 1 - ((x - 26) / 22) ** 2))):
                    continue
                k = (x - 4) / 44
                c = IRON[4] if k < 0.12 else IRON[3] if k < 0.4 else IRON[2] if k < 0.75 else IRON[1]
                if (y - 10) % 9 == 0:
                    c = IRON[1] if k < 0.75 else IRON[0]  # the seams, riveted
                    if x % 3 == 0:
                        c = IRON[4]
                cv.set(x, y, c)
    for x in range(4, 49):  # the tank's curved bottom edge
        yb = 38 + int(3 * math.sqrt(max(0.0, 1 - ((x - 26) / 22) ** 2)))
        for y in range(38, yb):
            cv.set(x, y, IRON[1])
        cv.set(x, yb, IRON[0])
    brick_wall(cv, 8, 41, 37, 27, seed=47)  # the brick base
    for y in range(41, 68):
        cv.set(44, y, BRICK[1]); cv.set(8, y, BRICK[4])
    door = {(x, y) for (x, y) in disc(26, 53, 7) if y < 53} | rect_set(19, 53, 15, 15)
    for (x, y) in door:
        cv.set(x, y, IRON[0] if x > 24 else IRON[1])
    for (x, y) in door:
        if (x, y - 1) not in door:
            cv.set(x, y - 1, STONE[4])
    for y in range(12, 68):  # the ladder up the west side
        cv.set(2, y, IRON[3]); cv.set(6, y, IRON[2])
        if y % 4 == 0:
            cv.hline(2, y, 5, IRON[4])
    for t in range(14):  # the hose on its jib, swung up and lashed
        x, y = 47 + t // 4, 26 + t
        cv.set(x, y, '#3A2A22'); cv.set(x + 1, y, '#5A4232')
    detail.stones(cv, 6, 68, 41, 6, STONE, seed=49, course=3)
    return cv


def signal_box() -> Canvas:
    """The signal box beside the line, 60 x 70: a glazed upper room for the signalman on a
    brick base, a hipped slate roof seen from above, a stove pipe, the lever frame's
    windows lit warm, an outside stair up the east end."""
    w, h = 60, 70
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, 16):  # the hipped roof: front plane and east plane, ridge on top
        t = (y - 2) / 13
        l, r = 22 - t * 18, 34 + t * 18
        for x in range(int(l), int(r) + 1):
            front = l + 4 * t < x < r - 4 * t or True
            c = SLATE[3] if x < 28 else SLATE[2]
            if x > r - 6 * t - 1:
                c = SLATE[1]  # the east hip, in shade
            if (y - 2) % 4 == 3:
                c = SLATE[1] if x < 28 else SLATE[0]
            cv.set(x, y, c)
    cv.hline(21, 2, 14, SLATE[4])
    for y in range(0, 8):  # the stove pipe
        cv.set(40, y, IRON[3]); cv.set(41, y, IRON[1])
    cv.hline(39, 0, 4, IRON[4])
    cv.hline(2, 16, 56, WOOD[4]); cv.hline(2, 17, 56, WOOD[2])  # the eaves board
    for y in range(18, 36):  # the glazed signal room
        for x in range(4, 56):
            c = WOOD[3]
            if 20 <= y < 33 and (x - 4) % 8 not in (0, 7):
                c = WARM[3] if y < 26 else WARM[2]
                if x > 44:
                    c = '#1E2A34' if y < 26 else '#2C3E4C'
            if y == 33:
                c = WOOD[4]
            cv.set(x, y, c)
    for lx in range(10, 42, 5):  # the lever frame inside, seen through the glass
        cv.vline(lx, 27, 5, '#C8463A' if lx % 10 else '#F2ECDE')
    brick_wall(cv, 6, 36, 48, 26, seed=51)
    for (x, y) in rect_set(14, 44, 8, 10):
        cv.set(x, y, '#1E2A34' if (x - 14) % 4 else IRON[3])  # the locking room window
    for k in range(7):  # the outside stair up the east end
        for x in range(46 + k, 56):
            cv.set(x, 60 - k * 4, WOOD[4]); cv.set(x, 61 - k * 4, WOOD[2])
        cv.vline(56, 34, 28, WOOD[1])
    detail.stones(cv, 4, 62, 52, 6, STONE, seed=53, course=3)
    return cv


def locomotive_34() -> Canvas:
    """The engine standing at the platform in the three-quarter view (the
    zones' 'locomotive', 120 x 62). It runs east-west, so we see its long south side and, above
    it, everything that faces up: the boiler's crown catching the light, the stack's
    open mouth and the dome as rounded tops, the running board as a lit ledge the
    length of the engine, the cab's roof as a plane, the tender's coal heaped and seen
    from above. Wheels are round, the near ones whole. (Its shadow is cast by the zone,
    not drawn into the sprite.)"""
    w, h = 120, 62
    cv = Canvas(w, h, pad=PAD)
    D = 7  # how much of each top we see
    # the tender (east, behind the cab): a box with its top full of coal
    tx0, tx1, ty0, ty1 = 96, 118, 22, 46
    for x in range(tx0, tx1):
        for y in range(ty0 - D, ty0):  # its top: the coal heap
            n = noise2(x // 2, y // 2, 61)
            cv.set(x, y, '#1A1A22' if n > 0.55 else '#2E2E38' if n > 0.2 else '#4A4A56')
        for y in range(ty0, ty1):
            k = (y - ty0) / (ty1 - ty0)
            c = '#3E566A' if k < 0.1 else '#2C3E4C' if k < 0.7 else '#1E2A34'
            if x in (tx0, tx1 - 1):
                c = '#1E2A34'
            if (x - tx0) % 7 == 3 and 0.2 < k < 0.8:
                c = BRASS[3]  # the lining
            cv.set(x, y, c)
    cv.hline(tx0, ty0 - D, tx1 - tx0, IRON[3]); cv.hline(tx0, ty0, tx1 - tx0, BRASS[4])
    # the cab: a roof seen as a plane, a front spectacle, a side opening with the crew's lamp
    cx0, cx1 = 74, 98
    for x in range(cx0 - 1, cx1 + 1):
        for y in range(4, 4 + D):
            cv.set(x, y, IRON[4] if y == 4 else IRON[3] if x < 90 else IRON[2])
        cv.set(x, 4 + D, IRON[1])
    for x in range(cx0, cx1):
        for y in range(12, 44):
            c = RED[3] if x < cx0 + 3 else RED[2]
            if 16 <= y < 28 and cx0 + 5 <= x < cx1 - 5:
                c = WARM[3] if y < 21 else WARM[2]  # the side opening, lamplit
            if y == 15 or y == 28:
                c = BRASS[4] if y == 15 else RED[1]
            cv.set(x, y, c)
    cv.vline(cx1 - 1, 12, 32, RED[1])
    # the boiler: a cylinder lying east-west, its crown lit, its belly in shade
    bx0, bx1 = 16, 74
    for x in range(bx0, bx1):
        for y in range(14 - 3, 36):
            k = (y - 11) / 25
            c = IRON[4] if k < 0.12 else IRON[3] if k < 0.35 else IRON[2] if k < 0.7 else IRON[1]
            if (x - bx0) % 14 == 6:
                c = BRASS[5] if k < 0.2 else BRASS[4] if k < 0.5 else BRASS[2]  # the bands
            cv.set(x, y, c)
    for (x, y) in oval(bx0, 23, 5, 12):  # the smokebox's round front, seen a little from the side
        if x <= bx0 + 1:
            cv.set(x, y, IRON[2] if y < 20 else IRON[1])
    cv.set(bx0 - 3, 23, BRASS[4]); cv.set(bx0 - 2, 23, BRASS[2])
    # the stack and its open mouth, the dome, the safety valve
    for y in range(0, 12):
        hw = 5 if y < 3 else 4
        for x in range(28 - hw, 28 + hw + 1):
            cv.set(x, y, IRON[3] if x < 27 else IRON[2] if x < 30 else IRON[1])
    for (x, y) in oval(28, 1, 5, 2):
        cv.set(x, y, '#0E0E14' if abs(x - 28) < 4 else IRON[4])
    for (x, y) in oval(52, 10, 6, 4):
        if y <= 11:
            cv.set(x, y, BRASS[5] if x < 50 and y < 9 else BRASS[4] if x < 54 else BRASS[2])
    cv.set(64, 8, BRASS[4]); cv.set(64, 9, BRASS[3]); cv.set(65, 9, BRASS[2])
    # the running board: a lit ledge the whole length, its edge in shade
    for x in range(8, 98):
        cv.set(x, 36, IRON[4]); cv.set(x, 37, IRON[3]); cv.set(x, 38, '#1E2A34'); cv.set(x, 39, RED[2])
    # the buffer beam, red, and two buffers toward us
    for x in range(6, 12):
        for y in range(36, 44):
            cv.set(x, y, RED[3] if x < 8 else RED[2])
    for by in (38,):
        for x in range(2, 7):
            cv.set(x, by, IRON[4]); cv.set(x, by + 1, IRON[2])
        cv.vline(2, by - 1, 4, IRON[3])
    # the wheels: three drivers, round, red spokes, the coupling rod across them
    for (wx, r) in ((30, 9), (52, 9), (84, 6), (104, 5), (114, 5)):
        cy = 52 - (9 - r) // 1 * 0 + (9 - r)
        for (x, y) in disc(wx, cy, r):
            cv.set(x, y, RED[2] if (x - wx) + (y - cy) < 0 else RED[1])
        for (x, y) in disc(wx, cy, r - 2):
            cv.set(x, y, '#1E1C22')
        for k in range(6):
            a = math.pi * k / 3
            for t in range(1, r - 1):
                cv.set(int(round(wx + math.cos(a) * t)), int(round(cy + math.sin(a) * t)), RED[3])
        cv.set(wx, cy, BRASS[4]); cv.set(wx - 1, cy - 1, BRASS[5])
        for (x, y) in disc(wx, cy, r):
            if (x, y - 1) not in disc(wx, cy, r) and x < wx:
                cv.set(x, y, RED[4])  # the rim's lit top
    cv.hline(30, 54, 23, IRON[4]); cv.hline(30, 55, 23, IRON[2])  # the coupling rod
    return cv


def props() -> dict[str, Canvas]:
    return {
        'workshop': workshop(), **{f'workshop_f{n}': workshop(turn=n * 2 * math.pi / 27) for n in (1, 2)},
        'workshop_round': workshop(80, sign='round'), 'clock_tower': clock_tower(),
        'locomotive': locomotive_34(),
        'house_slate': townhouse(88, 2, SLATE, 'brown', door_x=18, chimney=1, seed=1),
        'shop_ashlar': townhouse(92, 2, TAR, 'ashlar', shop=True, chimney=-1, seed=2),
        'warehouse': warehouse(), 'engine_tank': water_tower(), 'signal_box': signal_box(), 'gas_lamp': gas_lamp(), 'steam_puff': steam_puff(), 'pipe_run': pipe_run(),
        'gear_pile': gear_pile(), 'iron_bench': iron_bench(), 'steamer_trunk': steamer_trunk(),
        'coal_cart': coal_cart(), 'airship_mast': airship_mast(), 'tea_kiosk': tea_kiosk(),
        'narrowboat': narrowboat(), 'canal_crane': canal_crane(), 'lock_hut': lock_hut(), 'foundry': foundry(), 'tube_station': tube_station(),
        'atmos_car': atmos_car(), 'automaton': automaton(), 'cloche': cloche(),
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
