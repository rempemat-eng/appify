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
    """The junction's clock tower, 54 x 138, in the same three-quarter view as the
    workshops (art-faults.md, rule 4): a square brick shaft whose front faces the
    square and whose east side turns into shade, a copper spire of four planes (the
    front and east ones seen), a belfry, the clock lit from the upper left, and a
    stone plinth with steps up to the door, its contact shadow on the paving."""
    w, h = 54, 138
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
    brick_wall(cv, fx0, 37, fx1 - fx0, 80, seed=21)
    for y in range(37, 117):
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
    pipe_v(cv, fx1 - 4, 56, 116, BRASS)
    detail.overhang_shadow(cv, fx0, fx1, 37, lambda x: 2, k=1, cap=1)
    # the plinth: a stone base with a lit top and a front face, steps to the door
    detail.stones(cv, fx0 - 3, 117, fx1 - fx0 + 6, 9, STONE, seed=23, course=4)
    for y in range(117, 126):
        for x in range(fx1 + 3, sx1 + 3):
            cv.set(x, y, STONE[1] if (x + y) % 4 else STONE[0])
    cv.hline(fx0 - 3, 116, sx1 - fx0 + 6, STONE[4])
    for (x0, y, wd) in ((14, 126, 20), (12, 129, 24), (10, 132, 28)):
        cv.hline(x0, y, wd, STONE[4]); cv.hline(x0, y + 1, wd, STONE[3]); cv.hline(x0, y + 2, wd, STONE[1])
        cv.set(x0 + wd, y + 1, STONE[1]); cv.set(x0 + wd, y + 2, STONE[0])
    dx = int(cx) - 5
    for (x, y) in rect_set(dx, 106, 11, 11) | {(x, y) for (x, y) in disc(dx + 5, 106, 5.5) if y < 106}:
        cv.set(x, y, WOOD[1] if x > cx else WOOD[2])
    cv.set(dx + 8, 111, BRASS[4])
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



def locomotive_parked() -> Canvas:
    """The engine standing at the platform in the three-quarter view (the zones' key
    'locomotive'): the side-on engine (which the journey draws) with its roofs seen from above, the cab's top and
    the boiler's crown catching the light, and its wheels on the rails."""
    cv = locomotive()
    for x in range(70, 100):  # the cab roof, its top surface
        for y in range(1, 5):
            cv.set(x, y, IRON[4] if y == 1 else IRON[3] if x < 92 else IRON[2])
    for x in range(20, 72):  # the boiler's crown, a lit band along the top
        cv.set(x, 15, IRON[4] if x % 14 else BRASS[5])
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
    """The airship mast, 104 x 168: a tall iron lattice tower with a lit lamp, and a
    small airship moored to its top by a line, riding high in the air (its shadow
    falls on the ground beside the mast, drawn by the zone): a lit ochre envelope with
    panel seams, a gondola with warm windows and a turning propeller."""
    w, h = 104, 168
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
        if (y - 40) % 14 == 0 and y < h - 14:
            cv.hline(lx, y, rx - lx + 1, IRON[2])
            for k in range(rx - lx):
                cv.set(lx + k, y + min(13, k * 14 // max(1, rx - lx)), IRON[2])
    for (x, y) in disc(mx, 38, 3):
        cv.set(x, y, '#FFE7A6' if x < mx else '#F0B85A')
    cv.hline(60, 40, mx - 60, IRON[2])  # the mooring line
    cv.rect(mx - 12, h - 4, 25, 4, STONE[3]); cv.hline(mx - 12, h - 4, 25, STONE[4])
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
    """A steam narrowboat moored on the canal, 112 x 34, side on and a little from
    above: a long bottle-green hull with a red and gold rubbing strake, a cabin roof
    with a brass funnel (its steam comes from the zone's life layer), round warm
    portholes, a painted panel of abstract flowers, coal heaped in the open bow, a
    tiller at the stern and a coil of rope."""
    w, h = 112, 34
    cv = Canvas(w, h, pad=PAD)
    for x in range(4, w - 4):
        bow = max(0, 18 - x) ** 2 // 30 + max(0, x - (w - 10)) ** 2 // 10
        for y in range(18 + bow // 3, 30):
            c = BOAT_GREEN[3] if y < 21 else BOAT_GREEN[2] if y < 26 else BOAT_GREEN[1]
            if y in (22, 23):
                c = RED[3] if y == 22 else GOLD[3]
            cv.set(x, y, c)
        cv.set(x, 30, BOAT_GREEN[0])
    for x in range(30, w - 16):  # the cabin
        for y in range(8, 18):
            c = BOAT_GREEN[4] if y < 10 else BOAT_GREEN[3] if y < 14 else BOAT_GREEN[2]
            cv.set(x, y, c)
        cv.set(x, 8, WOOD[4] if x % 2 else WOOD[3])  # the planked roof's edge
    for px in range(40, w - 22, 14):
        porthole(cv, px, 13, 2.6)
    for y in range(10, 17):  # the painted panel
        for x in range(78, 92):
            c = RED[3] if (x - 85) ** 2 + (y - 13) ** 2 < 6 else GOLD[3] if (x + y) % 5 == 0 else '#E8D8B8'
            cv.set(x, y, c)
    for y in range(0, 9):  # the funnel
        for x in range(46, 51):
            cv.set(x, y, BRASS[4] if x < 48 else BRASS[2])
    cv.hline(45, 0, 7, BRASS[5])
    for (x, y) in oval(14, 18, 8, 3):  # coal in the bow
        cv.set(x, y, IRON[1] if (x + y) % 2 else IRON[0])
    for t in range(10):  # the tiller
        cv.set(w - 10 + t // 2, 16 - t // 2, WOOD[3])
    for (x, y) in oval(w - 22, 17, 3, 1.5):
        cv.set(x, y, MATERIALS['rope'][2] if (x + y) % 2 else MATERIALS['rope'][3])
    return cv


def canal_crane() -> Canvas:
    """A hand-cranked iron jib crane on a brick plinth, 52 x 66: a lattice jib swung out
    over the water with a hook and a crate on its chain, a geared winch drum lit in
    brass."""
    w, h = 52, 66
    cv = Canvas(w, h, pad=PAD)
    brick_wall(cv, 4, 50, 22, 14, seed=12)
    cv.hline(4, 50, 22, STONE[4])
    for y in range(14, 50):  # the post
        for x in range(12, 18):
            cv.set(x, y, IRON[4] if x == 12 else IRON[3] if x < 15 else IRON[1])
    for t in range(36):  # the jib, a lattice out to the right
        x = 15 + t
        top, bot = 12 + t // 6, 18 - t // 8
        cv.set(x, top, IRON[4]); cv.set(x, top + 1, IRON[2])
        if t < 30:
            cv.set(x, bot + t // 3, IRON[2])
        if t % 6 == 0:
            for k in range(bot + t // 3 - top):
                cv.set(x + k // 3, top + k, IRON[2])
    for y in range(20, 40):
        cv.set(48, y, IRON[1])
    for (x, y) in rect_set(43, 40, 11, 9):
        cv.set(x, y, WOOD[4] if y == 40 else WOOD[3] if x < 47 else WOOD[2])
    cv.vline(48, 41, 7, WOOD[1])
    gear(cv, 20, 34, 5, BRASS, teeth=8)
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
    """The atmospheric railway's terminus, 80 x 70: Cogsworth's end of the maglev from
    Neon Harbour, built the Cogsworth way. A glass-and-brass dome over a round booking
    hall, ribbed in brass, warm inside; the brass tube leaves from its east side."""
    w, h = 80, 70
    cv = Canvas(w, h, pad=PAD)
    cx = 38
    for y in range(4, 36):  # the dome
        half = int(math.sqrt(max(0, 1 - ((36 - y) / 32) ** 2)) * 30)
        for x in range(cx - half, cx + half + 1):
            rib = (x - cx) % 8 == 0 or (y - 4) % 9 == 0
            k = (x - cx) / max(1, half)
            c = BRASS[3] if rib and k < 0 else BRASS[1] if rib else (WARM[3] if k < -0.5 else WARM[2] if k < 0.3 else WARM[1])
            if not rib and y < 12:
                c = SNOW[2] if k < 0 else SNOW[1]  # the glass catches the sky near the top
            cv.set(x, y, c)
    cv.vline(cx, 0, 5, BRASS[4]); cv.set(cx, 0, BRASS[5])
    for y in range(36, 62):  # the drum wall
        for x in range(cx - 30, cx + 31):
            k = (x - cx) / 30
            c = BRASS[4] if k < -0.7 else BRASS[3] if k < 0 else BRASS[2] if k < 0.7 else BRASS[1]
            if y in (36, 37):
                c = BRASS[5] if y == 36 else IRON[1]
            cv.set(x, y, c)
    for px in (cx - 18, cx + 18):
        porthole(cv, px, 46, 4)
    for (x, y) in rect_set(cx - 7, 44, 14, 18):  # the door
        cv.set(x, y, IRON[2] if x < cx else IRON[1])
    cv.hline(cx - 8, 43, 16, BRASS[5])
    for y in range(40, 56):  # the tube leaving east
        for x in range(cx + 30, w - 1):
            k = (y - 40) / 16
            cv.set(x, y, BRASS[4] if k < 0.2 else BRASS[3] if k < 0.5 else BRASS[2] if k < 0.85 else BRASS[1])
            if (x - cx) % 10 == 0:
                cv.set(x, y, IRON[1])  # its flanges
    detail.stones(cv, cx - 32, 62, 64, 6, STONE, seed=29, course=3)
    return cv


def atmos_car() -> Canvas:
    """A capsule car on the atmospheric line, 64 x 26: a riveted brass shell with
    portholes, riding on top of its tube."""
    w, h = 64, 26
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(32, 12, 29, 9):
        k = (y - 3) / 18
        c = BRASS[5] if k < 0.15 else BRASS[4] if k < 0.4 else BRASS[3] if k < 0.7 else BRASS[2]
        if (x % 9 == 0) and k > 0.2:
            c = BRASS[1]
        cv.set(x, y, c)
    for px in range(14, 56, 9):
        porthole(cv, px, 11, 2.4)
    for x in range(6, 58):
        cv.set(x, 21, IRON[1]); cv.set(x, 22, IRON[2] if x % 4 else IRON[3])
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

def props() -> dict[str, Canvas]:
    return {
        'workshop': workshop(), **{f'workshop_f{n}': workshop(turn=n * 2 * math.pi / 27) for n in (1, 2)},
        'workshop_round': workshop(80, sign='round'), 'clock_tower': clock_tower(),
        'locomotive': locomotive_parked(), 'gas_lamp': gas_lamp(), 'steam_puff': steam_puff(), 'pipe_run': pipe_run(),
        'gear_pile': gear_pile(), 'iron_bench': iron_bench(), 'steamer_trunk': steamer_trunk(),
        'coal_cart': coal_cart(), 'airship_mast': airship_mast(), 'tea_kiosk': tea_kiosk(),
        'narrowboat': narrowboat(), 'canal_crane': canal_crane(), 'foundry': foundry(), 'tube_station': tube_station(),
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
