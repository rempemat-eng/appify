"""Props for Driftwood Harbour on the valley's coast (world-atlas.md).

Still the valley's materials and light (it is walkable from Crossroads Town), but the
coast's own things: whitewashed cottages with tarred roofs, a striped lighthouse, boats,
nets, pots and the fish market. Run directly for a contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import G, MATERIALS, WOOD, STONE, RED, WTR, PLASTER, SLATE, GOLD, LEAF  # noqa: E402

TAR = MATERIALS['tar']  # tarred roof boards
SAILCLOTH = MATERIALS['sailcloth']
ROPE = MATERIALS['rope']
PAD = 4
# How these props meet the ground (zones.py registers them with the world lint):
PLACEMENT = {'harbour_ferry': 'floating', 'pier_ladder': 'supported'}


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def cottage(width: int = 80, seed: int = 0, door=None, shutters=None, porch: bool = False,
            shed: int = 0, net: str = 'right') -> Canvas:
    """A fisher's cottage at the scale table's size (verticality.md 5: a 25 px adult, walls
    44 to the eaves, a 32 x 14 door, 16 x 12 windows, about 96 to the ridge), `width` wide
    (plus a lean-to `shed` px wide on its east side): a steep roof of tarred boards seen
    from above with a whitewashed chimney, thick whitewashed walls over rough stone with
    quoins at the corners, damp low down and streaks under the sills, small deep windows
    under stone lintels, a painted plank door (`door`, a colour ramp) with strap hinges
    and a step, painted `shutters` or none, a little timber `porch` over the door or none,
    a net hung to dry on the wall (`net`: 'left', 'right' or none), a downpipe, a wall
    lantern and stone footings. The foot stays where the old 74 px cottage stood
    (keep_foot), so the zones place it unchanged; it rises 22 px higher."""
    door = door or WTR
    house = width
    w, h = width + shed, 96
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (house - 1) / 2, 16, 44, 44, 88
    if shed:  # the lean-to first: the house's roof overlaps its top
        sx0 = house - 6
        roof0, roof1 = wall_bottom - 40, wall_bottom - 24
        for y in range(roof0, wall_bottom):
            for x in range(sx0, w - 2):
                if y < roof1:  # its single slope of tarred boards, falling east
                    c = TAR[3] if (x - sx0) % 5 else TAR[2]
                    if y == roof0:
                        c = TAR[4]
                    if x >= w - 4:
                        c = TAR[1]
                elif x < w - 3:  # its plank wall, open at the front where the nets hang
                    c = WOOD[2] if (x - sx0) % 4 else WOOD[1]
                    if y > roof1 + 4 and sx0 + 6 < x < w - 7:
                        c = '#3E332C' if (x + y) % 5 else '#4A3D34'  # the open front, dim inside
                else:
                    c = WOOD[1]
                cv.set(x, y, c)
        for x in range(sx0, w - 2):
            cv.set(x, roof1, TAR[1]); cv.set(x, roof1 + 1, WOOD[0])  # the eave's shadow line
        for t in range(14):  # a net hanging in the open front
            for k in range(6):
                x, y = sx0 + 8 + k * 2 + (t % 2), roof1 + 6 + t
                if x < w - 7 and (x + y) % 3 == 0:
                    cv.set(x, y, ROPE[-1] if t < 7 else ROPE[-2])
        for t in range(26):  # two oars leaning on the wall
            for (ox, col) in ((w - 6, WOOD[4]), (w - 9, WOOD[3])):
                x, y = ox + t // 7, roof1 + t - 2
                cv.set(x, y, col)
            if t > 21:
                cv.set(w - 6 + t // 7 - 1, roof1 + t - 2, WOOD[3])
    chim = rect_set(12, 4, 10, 14)
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, house - 3, TAR, hole=chim, seed=71 + seed, moss=None)
    for (x, y) in chim:
        cv.set(x, y, PLASTER[4] if x < 16 else PLASTER[3])
    cv.rect(11, 3, 12, 3, PLASTER[5]); cv.rect(14, 4, 6, 2, '#2A2420')
    gable = gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2), 7,
                             house - 8, apex_y, wall_top, PLASTER, boards=False)
    for (x, y) in gable:  # the gable's whitewash, rough like the walls, a step darker right of the ridge
        if (x, y - 1) in gable and (x, y - 2) in gable and noise2(x // 2, y // 2, 284 + seed) > 0.6:
            cv.set(x, y, PLASTER[4] if x < ridge else PLASTER[2])
    lx0, ly0 = int(ridge) - 3, apex_y + 12  # a small loft hatch under the ridge
    for (x, y) in rect_set(lx0, ly0, 7, 8):
        cv.set(x, y, WOOD[2] if (x - lx0) % 3 else WOOD[1])
    cv.hline(lx0 - 1, ly0 - 1, 9, STONE[4]); cv.hline(lx0, ly0 + 8, 7, STONE[2]); cv.set(lx0 + 5, ly0 + 4, SLATE[3])
    detail.recess(cv, rect_set(lx0, ly0, 7, 8), depth=1, k=1)
    wall = rect_set(7, wall_top, house - 14, wall_bottom - wall_top)
    for (x, y) in wall:  # whitewash over rough stone, damp rising from the footing
        n = noise2(x // 2, y // 2, 281 + seed)
        c = PLASTER[5] if n > 0.55 else PLASTER[4]
        damp = wall_bottom - y
        if damp < 5 or (damp < 9 and noise2(x // 3, y // 2, 283 + seed) > 0.45):
            c = PLASTER[3] if damp > 2 or (x + y) % 3 else PLASTER[2]
        cv.set(x, y, c)
        if noise2(x, y, 282 + seed) > 0.95:
            cv.set(x, y, PLASTER[2])  # a chip showing the stone
            cv.set(x + 1, y, PLASTER[3])
    for x0, lit in ((7, True), (house - 11, False)):  # quoins: dressed stones at the corners
        for i, y in enumerate(range(wall_top + 1, wall_bottom - 1, 5)):
            qw = 4 if i % 2 == 0 else 3
            qx = x0 if lit else x0 + 4 - qw
            for yy in range(y, min(y + 4, wall_bottom)):
                for xx in range(qx, qx + qw):
                    cv.set(xx, yy, STONE[3] if lit else STONE[2])
                cv.set(qx + (0 if lit else qw - 1), yy, STONE[4] if lit else STONE[1])
            cv.hline(qx, y, qw, STONE[4] if lit else STONE[3])
    proud = set()
    dx = int(ridge) - 7
    dtop = wall_bottom - 32
    for (x, y) in rect_set(dx - 2, dtop - 3, 18, 3):  # the stone lintel
        cv.set(x, y, STONE[4] if y == dtop - 3 else STONE[3] if x < dx + 12 else STONE[2])
    cv.set(dx + 6, dtop - 2, STONE[1]); cv.set(dx + 7, dtop - 2, STONE[1])  # the keystone's joints
    proud |= rect_set(dx - 2, dtop - 3, 18, 3)
    for (x, y) in rect_set(dx, dtop, 14, 32):  # the painted door, its boards
        k = (x - dx) % 4
        cv.set(x, y, door[3] if k == 1 else door[2] if k else door[1])
    detail.recess(cv, rect_set(dx, dtop, 14, 32), depth=2, k=1)
    for (x, y) in rect_set(dx + 4, dtop + 5, 6, 5):  # a small light in the door
        cv.set(x, y, WTR[2] if y < dtop + 7 else WTR[1])
    cv.rect(dx + 3, dtop + 4, 8, 1, door[4]); cv.set(dx + 5, dtop + 6, WTR[4])
    for hy in (dtop + 6, dtop + 24):  # strap hinges
        cv.hline(dx + 1, hy, 7, SLATE[1]); cv.set(dx + 1, hy, SLATE[3]); cv.set(dx + 7, hy, SLATE[2])
    cv.set(dx + 11, dtop + 17, GOLD[4]); cv.set(dx + 11, dtop + 18, GOLD[2])  # the latch
    cv.rect(dx - 2, wall_bottom, 18, 2, STONE[3]); cv.hline(dx - 2, wall_bottom, 18, STONE[4])  # the step
    for wx in (14, house - 26):
        wy = wall_top + 8
        gp.window(cv, wx, wy, 12, 16, shutters=shutters, sill=True, warm=seed % 2 == 0)
        for (x, y) in rect_set(wx - 1, wy - 3, 14, 3):  # its lintel
            cv.set(x, y, STONE[4] if y == wy - 3 else STONE[3] if x < wx + 9 else STONE[2])
        proud |= rect_set(wx - 1, wy - 3, 14, 3)
        for sx in range(wx + 1, wx + 11, 3):  # rain streaks under the sill
            for yy in range(wy + 19, wy + 19 + 3 + (sx * 7 + seed) % 5):
                if cv.get(sx, yy)[:3] != (0, 0, 0):
                    cv.set(sx, yy, PLASTER[3])
    if net:  # a net drying on the wall: a diamond mesh of rope, hung from two pegs
        nx = house - 22 if net == 'right' else 10
        for k in range(12):
            for t in range(11):
                x, y = nx + (k + t) % 12 + (t // 2) - 1, wall_top + 3 + t
                if 7 < x < house - 7 and (x + y) % 3 == 0 and not (wall_top + 8 <= y and (14 <= x < 26 or house - 26 <= x < house - 14)):
                    cv.set(x, y, ROPE[2] if t % 3 else ROPE[3])
        for px in (nx, nx + 11):
            cv.set(px, wall_top + 2, WOOD[1])
        cv.set(nx + 6, wall_top + 13, '#C8B060'); cv.set(nx + 2, wall_top + 12, '#C8B060')  # cork floats
    # a downpipe at the corner away from the light, and a wall lantern by the door
    pipe_x = house - 9 if not shed else 8
    for y in range(wall_top + 1, wall_bottom):
        cv.set(pipe_x, y, SLATE[2]); cv.set(pipe_x + 1, y, SLATE[1])
        if (y - wall_top) % 11 == 0:
            cv.set(pipe_x, y, SLATE[3]); cv.set(pipe_x + 1, y, SLATE[2]); cv.set(pipe_x - 1, y, SLATE[1])
    cv.hline(pipe_x - 1, wall_bottom - 1, 3, SLATE[2])
    proud |= {(pipe_x, y) for y in range(wall_top + 1, wall_bottom)} | {(pipe_x + 1, y) for y in range(wall_top + 1, wall_bottom)}
    lx = dx + 17 if not porch else dx - 9
    cv.hline(lx - 1, dtop + 2, 3, SLATE[1])  # the bracket
    cv.vline(lx, dtop + 3, 1, SLATE[1])
    cv.rect(lx - 1, dtop + 4, 3, 4, GOLD[3]); cv.set(lx - 1, dtop + 4, GOLD[4]); cv.hline(lx - 1, dtop + 8, 3, SLATE[1])
    cv.hline(lx - 1, dtop + 3, 3, SLATE[2])
    proud |= rect_set(lx - 1, dtop + 2, 3, 7)
    detail.cast(cv, proud, 1, 1, k=1, on=PLASTER, reach=2)
    detail.overhang_shadow(cv, 7, house - 7, wall_top, lambda x: 3, k=2, cap=1)
    if porch:  # a little porch: a pitched canopy seen from above, on two posts
        px0, px1, py = dx - 4, dx + 18, wall_bottom - 43
        mid = (px0 + px1 - 1) / 2
        for y in range(py, py + 7):
            half = 5 + (y - py) * 1.1  # the canopy widens from its ridge to its eave
            for x in range(int(mid - half), int(mid + half) + 1):
                c = TAR[4] if x < mid else TAR[2]
                if y == py:
                    c = TAR[4]
                elif (x + y) % 4 == 0:
                    c = TAR[3] if x < mid else TAR[1]  # its boards
                cv.set(x, y, c)
            cv.set(int(mid), y, TAR[3])  # the ridge
        for x in range(px0 - 2, px1 + 2):
            cv.set(x, py + 7, WOOD[3]); cv.set(x, py + 8, WOOD[1])  # the fascia board
            cv.set(x, py + 9, PLASTER[2])  # its shadow on the wall
        for x in (px0, px1 - 1):  # the posts down to the step
            for y in range(py + 9, wall_bottom + 2):
                cv.set(x, y, WOOD[4] if x < dx else WOOD[2]); cv.set(x + 1, y, WOOD[1])
        for x in range(px0 - 1, px1 + 1):
            cv.set(x, wall_bottom + 2, STONE[4]); cv.set(x, wall_bottom + 3, STONE[2])  # the step
    detail.stones(cv, 5, wall_bottom, house - 10, 8, STONE, seed=19 + seed, course=4, moss=LEAF)
    return gp.keep_foot(cv, w, 74, dx=0)


def lighthouse() -> Canvas:
    """The lighthouse on the west point's rocks, 44 x 140, in the valley's three-quarter
    view (Claude E, fault 10: a plain round plinth to stand on a rock drawn in the ground).
    A round plinth of coursed stone, its top seen from a little above; a tapering tower in
    red and white bands that curve round it, shaded as a cylinder lit from the left, with
    an arched door over a step and two small windows; a gallery deck with its rail running
    round behind and in front of the glazed lantern room, the lamp lit (its light is
    declared in atlas-walk.tsx LAMPS, at the same place as before); a domed cap and a vane."""
    w, h = 44, 140
    cv = Canvas(w, h, pad=PAD)
    cx = 21.5
    fs = 0.42  # how much of a round top the camera sees

    def arc(r, dx):
        return r * fs * math.sqrt(max(0.0, 1 - (dx / r) ** 2))

    def cyl(k, ramp, lo):
        """A cylinder's tone lit from the left: k is 0 at its left edge, 1 at its right."""
        return ramp[lo + 2] if k < 0.16 else ramp[lo + 1] if k < 0.45 else ramp[lo] if k < 0.8 else ramp[lo - 1]
    # the plinth: a drum of coursed stone, its top a ring of flags round the tower's foot
    R, PH = 18, 8
    bot = h - 1 - R * fs  # the plinth's bottom ellipse's centre
    top = bot - PH
    for x in range(int(cx - R), int(cx + R) + 1):
        dx = x + 0.5 - cx
        if abs(dx) > R:
            continue
        k = (dx + R) / (2 * R)
        y0, y1 = int(round(top + arc(R, dx))), int(round(bot + arc(R, dx)))
        for y in range(y0, y1 + 1):
            z = y - y0
            course = z // 3
            joint = z % 3 == 2 or int(dx + R + course * 3) % 7 == 0
            c = STONE[1] if joint else cyl(k, STONE, 2) if k < 0.8 else STONE[1]
            cv.set(x, y, STONE[0] if y == y1 else c)
        for y in range(int(round(top - arc(R, dx))), y0):  # the top, seen from above
            c = STONE[4] if k < 0.5 else STONE[3]
            if (int(dx + 40) * 3 + int(y)) % 9 == 0:
                c = STONE[2]  # the joints between the flags
            cv.set(x, y, c)
        cv.set(x, y0, STONE[4] if k < 0.7 else STONE[3])  # the lit front edge of the top
    # the tower: a tapering cylinder, its bands curving round it
    base_r, top_r, ty = 11.5, 7.5, 36
    foot_y = top  # the tower's foot ellipse's centre, on the plinth's top
    for y in range(ty, int(foot_y + arc(base_r, 0)) + 1):
        t = min(1.0, (y - ty) / (foot_y - ty))
        r = top_r + (base_r - top_r) * t
        for x in range(int(cx - r), int(cx + r) + 1):
            dx = x + 0.5 - cx
            if abs(dx) > r or y > foot_y + arc(base_r, dx):
                continue
            k = (dx + r) / (2 * r)
            v = foot_y - (y - arc(r, dx))  # height up the tower, along its surface
            band = int(v // 14) % 2
            ramp, lo = (RED, 2) if band else (PLASTER, 3)
            c = cyl(k, ramp, lo)
            if y >= foot_y + arc(base_r, dx) - 1:
                c = ramp[lo - 1]  # where it stands on the plinth
            cv.set(x, y, c)
    # the door at its foot: arched, planked, over a step on the plinth's top
    dy1 = int(foot_y + arc(base_r, 0))
    for y in range(dy1 - 11, dy1 + 1):
        for x in range(int(cx) - 3, int(cx) + 3):
            arch = y == dy1 - 11 and x in (int(cx) - 3, int(cx) + 2)
            if arch:
                continue
            c = WOOD[1] if x == int(cx) + 2 or y == dy1 - 10 else WOOD[2] if (x - int(cx)) % 2 else WOOD[3]
            cv.set(x, y, c)
    cv.set(int(cx) + 1, dy1 - 5, GOLD[3])  # the latch
    for x in range(int(cx) - 4, int(cx) + 4):
        cv.set(x, dy1 + 1, STONE[4]); cv.set(x, dy1 + 2, STONE[2])  # the step
    for (wy, r) in ((62, 9.0), (90, 10.2)):  # two small windows, deep in the wall
        for y in range(wy, wy + 6):
            for x in range(int(cx) - 1, int(cx) + 2):
                cv.set(x, y + (1 if x != int(cx) else 0), '#2A2D36' if y > wy else '#3C404C')
        cv.hline(int(cx) - 1, wy + 7, 3, PLASTER[4])
    # the gallery: its deck seen from a little above, a rail round it
    GR, gy = 13.5, 33
    rail = []
    for x in range(int(cx - GR), int(cx + GR) + 1):
        dx = x + 0.5 - cx
        if abs(dx) > GR:
            continue
        a = arc(GR, dx)
        for y in range(int(round(gy - a)), int(round(gy + a)) + 1):
            cv.set(x, y, STONE[3] if (dx + GR) / (2 * GR) < 0.5 else STONE[2])  # the deck
        cv.set(x, int(round(gy + a)) + 1, TAR[2]); cv.set(x, int(round(gy + a)) + 2, TAR[1])  # its edge
        rail.append((x, dx, a))
    for (x, dx, a) in rail:  # the rail behind the lantern room
        cv.set(x, int(round(gy - a)) - 4, TAR[2])
        if int(dx + GR) % 3 == 0:
            cv.vline(x, int(round(gy - a)) - 3, 3, TAR[1])
    # the lantern room: glazing bars spaced round the drum, the lamp lit inside
    LR, l0, l1 = 7.5, 12, 29
    for y in range(l0, l1 + 1):
        for x in range(int(cx - LR), int(cx + LR) + 1):
            dx = x + 0.5 - cx
            if abs(dx) > LR:
                continue
            k = (dx + LR) / (2 * LR)
            ang = math.asin(max(-1.0, min(1.0, dx / LR)))
            bar = abs(((ang / math.pi * 8) % 1) - 0.5) > 0.4
            if y in (l0, l1):
                c = TAR[2]
            elif bar:
                c = TAR[1]
            else:
                c = '#C9DCE8' if k < 0.3 and y < 20 else '#9FB8C9' if k < 0.6 else '#7790A3'
            cv.set(x, y, c)
    for (x, y) in disc(cx, 20.5, 3.2):  # the lamp
        cv.set(x, y, '#FFFBE0' if (x - cx) + (y - 20.5) < 0 else '#FFE9A0')
    for (x, dx, a) in rail:  # the rail in front
        yy = int(round(gy + a)) - 4
        cv.set(x, yy, TAR[3] if dx < 0 else TAR[2])
        if int(dx + GR) % 3 == 0:
            cv.vline(x, yy + 1, 3, TAR[1])
    # the cap: a dome over a rim, lit on its left, a ball and the vane on top
    CR = 9.0
    for x in range(int(cx - CR), int(cx + CR) + 1):
        dx = x + 0.5 - cx
        if abs(dx) > CR:
            continue
        k = (dx + CR) / (2 * CR)
        a = arc(CR, dx)
        cv.set(x, int(round(l0 + a * 0.4)), TAR[1])  # the rim's shadow on the glass
        hgt = 7 * math.sqrt(max(0.0, 1 - (dx / CR) ** 2))
        for y in range(int(round(l0 - 1 - hgt)), int(round(l0 + a * 0.4))):
            c = TAR[4] if k < 0.3 and y < l0 - 2 else TAR[3] if k < 0.6 else TAR[2] if k < 0.85 else TAR[1]
            cv.set(x, y, c)
    for (x, y) in disc(cx, 3.5, 1.6):
        cv.set(x, y, GOLD[3] if x < cx else GOLD[2])
    cv.vline(int(cx), 0, 3, TAR[2]); cv.hline(int(cx) - 3, 1, 7, GOLD[3])
    return cv


def fishing_boat(length: int = 64, hull=WTR) -> Canvas:
    """A small fishing boat at its mooring, 64 x 30, seen from above: a planked hull
    lit along its port side, a little wheelhouse, a stub mast, coiled rope and a float."""
    w, h = length, 30
    cv = Canvas(w, h, pad=PAD)
    body = set()
    for x in range(2, w - 2):
        t = (x - 2) / (w - 4)
        half = (8 + 2.5 * min(1.0, t * 8)) if t < 0.58 else 10.5 * (1 - ((t - 0.58) / 0.42) ** 1.7)  # blunt stern, pointed bow
        for y in range(int(15 - half), int(15 + half) + 1):
            body.add((x, y))
    for (x, y) in body:
        edge = (x, y - 1) not in body or (x, y + 1) not in body or (x - 1, y) not in body or (x + 1, y) not in body
        if edge:
            cv.set(x, y, hull[3] if y < 15 else hull[1])
        else:
            cv.set(x, y, WOOD[3] if (y % 3) else WOOD[2])
    for (x, y) in body:
        inner = all((x + dx, y + dy) in body for dx in (-2, 2) for dy in (-2, 2))
        if not inner and not ((x, y - 1) not in body or (x, y + 1) not in body):
            cv.set(x, y, hull[2])
    for (x, y) in rect_set(int(w * 0.55), 9, 12, 12):  # the wheelhouse roof
        cv.set(x, y, PLASTER[5] if y < 12 else PLASTER[3])
    cv.rect(int(w * 0.55) + 2, 18, 8, 2, '#3E5468')
    for (x, y) in disc(int(w * 0.3), 15, 2):
        cv.set(x, y, WOOD[1])
    for k in range(10):  # a coil of rope
        a = k * 0.7
        cv.set(int(w * 0.2 + math.cos(a) * 3), int(15 + math.sin(a) * 3), ROPE[2])
    for (x, y) in disc(int(w * 0.4), 7, 1.8):
        cv.set(x, y, RED[3] if x < w * 0.4 else RED[2])
    return cv


CORK = ['#6A4A2A', '#9A7046', '#C49A62', '#E0BE86']


def net_rack() -> Canvas:
    """Nets drying on a rack (B8: the old checker read as cloth), 44 wide and 28 tall,
    about a man's height: two posts and a rail, the nets thrown over it in loose drapes
    that hang in swags of open diamond mesh (each strand a line, the ground showing
    through, darker where the folds bunch), a line of cork floats along the head rope on
    the rail and lead weights along the foot rope at each swag's lowest point, a heap of
    net on the ground with a float or two, contact shadows. Re-seated in the old 52 x 40
    box (keep_foot)."""
    w, h = 44, 28
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    for px in (2, 39):
        for y in range(2, h):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[2]); cv.set(px + 2, y, WOOD[1])
        cv.hline(px - 1, foot, 5, SHADE_A)
    cv.hline(1, 3, 42, WOOD[4]); cv.hline(1, 4, 42, WOOD[2])  # the rail
    swags = ((5, 21, 13), (20, 38, 16))  # x0, x1, depth at the lowest point
    for (x0, x1, depth) in swags:
        for x in range(x0, x1):
            t = (x - x0) / (x1 - x0)
            bottom = 5 + int(depth * math.sin(math.pi * t) ** 0.8) + (1 if (x * 7) % 5 == 0 else 0)
            fold = int(t * 7) % 2  # the drape falls in folds: lit and shaded bands
            for y in range(5, bottom + 1):
                # the drape's body, darker in each fold, with the diamond mesh drawn over it
                # in lit strands that loosen as they hang
                bunch = abs(t - 0.5) > 0.38  # the folds bunch at each end of a swag
                base = 0 if bunch or fold else 1
                c = ROPE[base]
                d1 = (x + y + int(t * 3)) % 4 == 0
                d2 = (x - y) % 4 == 0
                if d1 or d2:
                    c = ROPE[min(len(ROPE) - 1, base + 2 + (1 if y < 10 and not fold else 0))]
                cv.set(x, y, c)
            cv.set(x, bottom, ROPE[0])  # the foot rope
        low = x0 + (x1 - x0) // 2
        lb = 5 + depth
        cv.set(low, lb + 1, SLATE[1]); cv.set(low + 1, lb + 1, SLATE[2])  # a lead weight
    for x in range(4, 39, 4):  # cork floats along the head rope
        cv.set(x, 5, CORK[3]); cv.set(x + 1, 5, CORK[2]); cv.set(x, 6, CORK[1])
    for (fx, fy) in ((10, foot - 2), (31, foot - 1)):  # a heap of net on the ground, floats in it
        for (x, y) in oval(fx, fy, 5, 2):
            cv.set(x, y, ROPE[2] if (x + y) % 3 == 0 else ROPE[1] if y <= fy else ROPE[0])
        cv.set(fx + 2, fy - 1, CORK[3]); cv.set(fx - 3, fy, RED[3])
    return gp.keep_foot(cv, 52, 39)


def lobster_pots() -> Canvas:
    """Three lobster pots stacked by a coil of rope, 34 x 24."""
    cv = Canvas(34, 24, pad=PAD)
    for (bx, by) in ((2, 10), (16, 10), (9, 1)):
        for (x, y) in rect_set(bx, by, 14, 12):
            top = y < by + 3
            cv.set(x, y, (WOOD[4] if top else WOOD[2]) if (x - bx) % 4 == 0 or top or y == by + 11 else '#2A2420')
        for x in range(bx, bx + 14, 2):
            cv.vline(x, by + 3, 8, ROPE[1])
    return cv


def _fish(cv: Canvas, x: int, y: int, kind: int, flip: bool = False):
    """A fish 8 px long lying on ice, lit along its back: 0 a mackerel (striped back),
    1 a red bream, 2 a silver herring. Its tail forks, its eye is a dark dot."""
    back, belly, mark = (('#4E7A86', '#C8D4D8', '#24414E'), ('#C0503C', '#E8A890', '#8A3028'),
                         ('#8A9AAC', '#DCE4EA', '#5E6E82'))[kind]
    for t in range(7):
        xx = x + (6 - t if flip else t)
        thick = 0 if t in (0, 6) else 1
        cv.set(xx, y, back if t < 6 else mark)
        if thick:
            cv.set(xx, y + 1, belly)
        if kind == 0 and t % 2 and 0 < t < 6:
            cv.set(xx, y, mark)  # the mackerel's bars
    tx = x - 1 if flip else x + 7
    cv.set(tx, y - 1, mark); cv.set(tx, y + 1, mark)  # the forked tail
    cv.set(x + (5 if flip else 1), y, '#1E2028')  # the eye


def fish_stall() -> Canvas:
    """The fish market stall at the scale table's size (verticality.md 5: 48 wide, the
    counter 13 above the ground, the canopy's top 40): a blue and white canvas awning seen
    from above, a counter of crushed ice sloping toward the buyer with mackerel, bream and
    herring laid head to tail, a hanging scale, a chalk price board (marks only, no words),
    a planked front with a drip of meltwater and a fish box at its foot. It is re-seated in
    the old 76 x 56 box (keep_foot), so its foot stays where it was."""
    w, h = 48, 48
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    ctop = foot - 13
    for px in (1, 44):  # posts
        for y in range(18, foot):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[4]); cv.set(px + 2, y, WOOD[1])
    for y in range(20, ctop):  # the dim back of the stall under the awning
        for x in range(4, 44):
            cv.set(x, y, WOOD[1] if (x - 4) % 5 else WOOD[0])
    for y in range(ctop - 8, ctop + 2):  # the ice, sloping toward the buyer
        for x in range(2, 46):
            n = noise2(x, y, 331)
            cv.set(x, y, '#F0F8FA' if n > 0.7 else '#DCEBF2' if n > 0.3 else '#BCD4E2')
    cv.hline(2, ctop - 9, 44, WOOD[4]); cv.hline(2, ctop + 2, 44, WOOD[4]); cv.hline(2, ctop + 3, 44, WOOD[2])
    for row, y in enumerate((ctop - 6, ctop - 2)):
        for i, x in enumerate(range(5 + row * 4, 40, 10)):
            _fish(cv, x, y, (i + row) % 3, flip=bool((i + row) % 2))
    cv.set(40, ctop - 6, '#6AA050'); cv.set(41, ctop - 7, '#6AA050'); cv.set(41, ctop - 6, '#8AC06A')  # parsley
    detail.boards(cv, rect_set(2, ctop + 4, 44, foot - ctop - 4), WOOD, 2, ctop + 4, board=5, vertical=True, x0=2,
                  grain=0.06, joints=False)
    for x in range(2, 46):
        detail.shade(cv, x, ctop + 4, 2)
    for y in range(ctop + 5, foot - 1, 3):  # meltwater dripping down one board
        cv.set(23, y, '#9EC4D6')
    cv.hline(2, foot, 44, WOOD[0])
    # a fish box at the foot, a hanging scale and the price board
    cv.rect(33, foot - 5, 12, 5, WOOD[2]); cv.hline(33, foot - 5, 12, WOOD[4]); cv.vline(44, foot - 4, 4, WOOD[0])
    cv.hline(34, foot - 6, 10, '#DCEBF2'); _fish(cv, 35, foot - 7, 2)
    cv.vline(10, 20, 4, SLATE[2]); cv.rect(8, 24, 5, 3, SLATE[3]); cv.hline(8, 24, 5, SLATE[4]); cv.set(10, 25, RED[3])
    cv.hline(7, 28, 7, SLATE[2]); cv.set(7, 27, SLATE[2]); cv.set(13, 27, SLATE[2])  # the scale's pan
    for (x, y) in rect_set(30, 20, 11, 7):
        cv.set(x, y, '#2A2D36')
    cv.rect(29, 19, 13, 1, WOOD[3]); cv.hline(32, 22, 6, '#E6E2D0'); cv.hline(32, 24, 4, '#E6E2D0')
    gp.awning(cv, -1, 50, 7, 10, 3, WTR, SAILCLOTH)
    return gp.keep_foot(cv, 76, 55)


def bollard() -> Canvas:
    """An iron bollard with a mooring rope, 14 x 16."""
    cv = Canvas(14, 16, pad=PAD)
    for y in range(5, 15):
        for x in range(4, 10):
            cv.set(x, y, '#545A68' if x < 6 else '#3C404C' if x < 8 else '#2A2D36')
    for (x, y) in oval(7, 5, 4, 2):
        cv.set(x, y, '#727A8A' if x < 7 else '#545A68')
    for x in range(0, 6):
        cv.set(x, 9 + x // 3, ROPE[2])
    return cv


def anchor() -> Canvas:
    """An old anchor lying on the quay where it was set down, in the three-quarter view,
    34 x 20 (Matt, 19 Oct, fault 09: "pinned flat on a wall with no reason or mounting"):
    the shank lies east-west from its ring to the crown, the stock lies across it near
    the ring (foreshortened, being on the ground), one arm curls up off the stones toward
    us with its fluke, the other rests behind; rust at the flukes and the crown, and a few
    turns of chain trailing from the ring."""
    IRON = ['#24272F', '#363A46', '#4E5462', '#6C7484', '#8E96A6']
    RUST = ['#5A2E1E', '#8A4A2A', '#B0683A']
    cv = Canvas(34, 20, pad=PAD)
    for (cx, cy, wide) in ((3, 14, True), (6, 16, False), (9, 17, True), (13, 17, False), (16, 16, True)):
        for (x, y) in oval(cx, cy, 2 if wide else 1, 1 if wide else 1.5):  # the chain's links
            ring = abs(((x + 0.5 - cx) / (2 if wide else 1)) ** 2 + ((y + 0.5 - cy) / (1 if wide else 1.5)) ** 2 - 0.6) < 0.5
            if ring:
                cv.set(x, y, IRON[3] if y <= cy else IRON[1])
    for (x, y) in oval(6, 10, 3, 2):  # the ring, lying flat
        if ((x + 0.5 - 6) / 3) ** 2 + ((y + 0.5 - 10) / 2) ** 2 > 0.35:
            cv.set(x, y, IRON[4] if x < 6 and y < 10 else IRON[2])
    for x in range(9, 28):  # the shank: its top lit, its side in shade
        cv.set(x, 9, IRON[4] if x < 14 else IRON[3]); cv.set(x, 10, IRON[2]); cv.set(x, 11, IRON[1])
    for y in range(4, 16):  # the stock across it, foreshortened, ball ends
        cv.set(11, y, IRON[3] if y < 9 else IRON[2]); cv.set(12, y, IRON[1])
    for (x, y) in ((11, 3), (12, 3), (11, 16), (12, 16)):
        cv.set(x, y, IRON[3] if y < 9 else IRON[1])
    for t in range(9):  # the back arm, resting behind, curving away
        x, y = 27 + int(t * 0.6), 9 - int(t * 0.65)
        cv.set(x, y, IRON[2]); cv.set(x + 1, y, IRON[1])
    for (x, y) in ((32, 2), (31, 3), (32, 3), (33, 3), (32, 4)):
        cv.set(x, y, RUST[1])  # its fluke
    for t in range(9):  # the front arm, curling up off the quay toward us
        x, y = 27 + int(t * 0.7), 11 + int(t * 0.55)
        cv.set(x, y, IRON[3]); cv.set(x, y + 1, IRON[1])
    for (x, y) in ((31, 15), (32, 15), (33, 16), (31, 16), (32, 16), (32, 17), (31, 17)):
        cv.set(x, y, RUST[2] if y == 15 else RUST[1])  # its fluke, broad and rusted
    for (x, y) in ((26, 9), (27, 10), (26, 11), (28, 10)):
        cv.set(x, y, RUST[1])  # the crown, rusted
    return cv


def upturned_boat() -> Canvas:
    """A rowing boat turned keel-up on the beach for tarring, 50 x 22, on two trestles."""
    w, h = 50, 22
    cv = Canvas(w, h, pad=PAD)
    for x in range(3, w - 3):
        t = (x - 3) / (w - 6)
        half = 7 * math.sin(math.pi * min(1, t * 1.1)) if t < 0.9 else 7 * math.sin(math.pi * 0.99) * (1 - (t - 0.9) * 8)
        for y in range(int(11 - half), int(11 + half) + 1):
            k = (y - (11 - half)) / (2 * half + 1)
            cv.set(x, y, TAR[3] if k < 0.25 else TAR[2] if k < 0.6 else TAR[1])
        cv.set(x, 11, TAR[4])  # the keel
    for tx in (12, 36):
        cv.vline(tx, 15, 7, WOOD[2]); cv.vline(tx + 1, 15, 7, WOOD[1])
    return cv


SHEET = ['#8A8478', '#B8B0A0', '#DCD6C8', '#F0EBE0', '#FBF8F2']
DENIM = ['#28324A', '#3A4A6A', '#506690', '#6A82AC', '#90A6C8']
WICKER = ['#5A3E26', '#7E5A36', '#A47A48', '#C49A62', '#DCBC84']
SHADE_A = (14, 18, 40, 84)  # a contact shadow over whatever ground it stands on


def washing_line(wall: bool = False) -> Canvas:
    """A washing line in a cottage's own yard, 54 wide (Matt, 19 Oct 22:40: "think about
    where clothes would be hung up to dry"; B8): the line strung from a T-post with a
    crosstree (east) to a second post, or with `wall` to an iron hook on the house's wall
    (west end, so it stands with that end against a cottage's east wall), sagging under
    its load and held up in the middle by a forked prop pole; on it, pegged, a sheet with
    folds that billow at the hem, a shirt with its sleeves hanging and a collar, a pair of
    trousers, a striped towel and socks, each lit on its left and shaded where it folds;
    a wicker basket of folded washing on the ground below, contact shadows."""
    w, h = 54, 34
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    posts = [49] if wall else [3, 49]
    for px in posts:  # T-posts with crosstrees, set in the ground
        for y in range(4, h):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
            if noise2(px, y // 3, 461) > 0.8:
                cv.set(px, y, WOOD[2])  # grain
        cv.hline(px - 3, 4, 8, WOOD[4]); cv.hline(px - 3, 5, 8, WOOD[2])
        cv.set(px - 3, 6, WOOD[1]); cv.set(px + 4, 6, WOOD[1])
        cv.hline(px - 1, foot, 5, SHADE_A); cv.set(px - 1, foot, G[1]); cv.set(px + 2, foot, G[2])  # tufts at its foot
    x_a = 1 if wall else 5
    if wall:  # the iron hook in the wall, its plate lit
        cv.set(0, 5, SLATE[3]); cv.set(0, 6, SLATE[1]); cv.set(1, 6, SLATE[2]); cv.set(1, 7, SLATE[1])
    span = 49 - x_a

    def line_y(x):
        return 6 + int(round(5 * math.sin(math.pi * (x - x_a) / span)))

    mid = x_a + span // 2
    for x in range(x_a, 49):
        cv.set(x, line_y(x), ROPE[3] if x < mid else ROPE[2])
    for k in range(foot - line_y(mid) + 1):  # the forked prop pole, leaning a little
        x = mid + 2 - k // 9
        y = foot - k
        cv.set(x, y, WOOD[3]); cv.set(x + 1, y, WOOD[1])
    cv.set(mid, line_y(mid) - 1, WOOD[3]); cv.set(mid + 3, line_y(mid) - 1, WOOD[2])  # its fork
    cv.hline(mid, foot, 4, SHADE_A)

    def peg(x):
        cv.set(x, line_y(x) - 1, WOOD[4]); cv.set(x, line_y(x), WOOD[2])

    def hang(x0, x1, length, ramp, stripe=None, billow=True):
        for x in range(x0, x1):
            top = line_y(x) + 1
            wave = int(round(math.sin((x - x0) * 1.3) * 1.2)) if billow else 0
            hem = top + length + wave
            for y in range(top, hem):
                fold = (x - x0 + (y - top) // 6) % 4
                c = ramp[2] if fold == 0 else ramp[4] if fold == 1 else ramp[3]
                if stripe and (y - top) in (3, 4, 8):
                    c = stripe[3] if fold else stripe[2]
                if x == x1 - 1:
                    c = ramp[1]  # its shaded edge
                cv.set(x, y, c)
            cv.set(x, hem, ramp[1])  # the hem
        peg(x0); peg(x1 - 1)

    x = x_a + 4
    hang(x, x + 13, 15, SHEET)  # the sheet
    x += 15
    for xx in range(x + 1, x + 8):  # the shirt: body, shoulders, collar, sleeves, folds
        top = line_y(xx) + 1
        for y in range(top, top + 10):
            c = RED[4] if xx < x + 3 else RED[3] if xx < x + 6 else RED[2]
            if (xx - x) == 4 and y > top + 2:
                c = RED[2]  # the placket's fold
            cv.set(xx, y, c)
        cv.set(xx, top + 10, RED[1])
    for (sx, lit) in ((x, True), (x + 8, False)):
        top = line_y(sx) + 2
        for y in range(top, top + 7):
            cv.set(sx, y, RED[3] if lit else RED[1])
    cv.set(x + 3, line_y(x + 3) + 1, SHEET[4]); cv.set(x + 5, line_y(x + 5) + 1, SHEET[4])  # the collar
    for y in (4, 6, 8):
        cv.set(x + 4, line_y(x + 4) + y, SHEET[4])  # buttons
    peg(x + 1); peg(x + 7)
    x += 10
    for leg, xx0 in enumerate((x, x + 3)):  # the trousers, hung by their hems, two legs
        for xx in range(xx0, xx0 + 3):
            top = line_y(xx) + 1
            for y in range(top, top + 12):
                cv.set(xx, y, DENIM[3] if xx == xx0 and leg == 0 else DENIM[2] if xx < xx0 + 2 else DENIM[1])
        peg(xx0)
    for xx in range(x, x + 6):
        cv.set(xx, line_y(xx) + 12, DENIM[0])  # the waistband
    x += 8
    if x + 6 < 47:
        hang(x, x + 5, 8, WTR, stripe=GOLD, billow=False)  # a striped towel
        x += 6
    for (sx, col) in ((x, GOLD), (x + 3, RED)):  # a pair of socks
        if sx + 2 >= 48:
            break
        top = line_y(sx) + 1
        for y in range(top, top + 5):
            cv.set(sx, y, col[3]); cv.set(sx + 1, y, col[2])
        cv.set(sx + 2, top + 4, col[2]); cv.set(sx + 2, top + 5, col[1])
    # the wicker basket of folded washing on the ground, toward the post
    bx, by = 36, foot - 6
    for xx in range(bx - 1, bx + 12):
        cv.set(xx, foot, SHADE_A)
    for yy in range(by + 2, foot):
        for xx in range(bx, bx + 11):
            t = 3 if xx < bx + 3 else 2 if xx < bx + 8 else 1
            if (xx + yy) % 2 == 0:
                t -= 1  # the weave
            cv.set(xx, yy, WICKER[max(0, t)])
    cv.hline(bx, by + 2, 11, WICKER[4]); cv.hline(bx, by + 1, 11, WICKER[3])  # the rim
    for xx in range(bx + 1, bx + 10):  # folded washing in it
        cv.set(xx, by, SHEET[4] if xx < bx + 5 else DENIM[3] if xx < bx + 8 else RED[3])
        cv.set(xx, by + 1, SHEET[3] if xx < bx + 5 else DENIM[2] if xx < bx + 8 else RED[2])
    return cv


def harbour_ferry() -> Canvas:
    """The ferry to the Tidebloom Isles at Driftwood's pier, 128 x 55, bow to the left, in
    the three-quarter view (art-faults.md rule 4) at a ferry's size, twice a fishing boat's
    length: the planked deck seen from above inside its bulwarks, the hull's near side below
    it lit toward the bow (white topsides with a rubbing strake, portholes, a navy stripe and
    a red boot-top at the level waterline, the stem raked and the sheer rising forward),
    fenders hung on the pier side, a saloon with a red roof and a row of windows, a door
    opening onto the gangway, the wheelhouse on top forward with its mast and masthead
    lamp, a red funnel with a black top, benches on the open after deck, bitts and a
    windlass on the foredeck, and the bow and stern lines and the gangway down to the pier
    along the near side. Its foot is the waterline (the bottom row), so the zone's cast
    shadow and the water lint start there. The windows declare their panes for night."""
    w, h = 128, 55
    # The zone places the ferry by the old 92 x 46 ferry's box (valley_zones.harbour, at
    # (137, 362)); the sprite contract lets art reach past its nominal box (placement adds
    # the trimmed offset), so the hull is drawn 37 px west and 12 px up of that box and
    # lies along the pier head with its waterline on the head's edge, with no re-placing.
    box = Canvas(92, 46, pad=44)
    cv = _Offset(box, -37, -12)
    IRON, HULL_W = MATERIALS['iron'], PLASTER
    cy, sq, wl = 34, 0.8, h - 1  # the deck's centre line, the plan's foreshortening, the waterline row

    def half(x):  # the hull's half-beam in plan: a fine bow, full amidships, a rounded stern
        t = (x - 3) / 38
        b = 12.5 * math.sqrt(max(0.0, min(1.0, t)))
        if x > 110:
            b *= math.sqrt(max(0.0, 1 - ((x - 110) / 15) ** 2))
        return b

    def sheer(x):  # the deck rises toward the bow
        return -round(3.4 * max(0.0, (44 - x) / 41))

    deck, side, near = set(), set(), {}
    for x in range(3, 126):
        hw = half(x) * sq
        if hw < 0.6:
            continue
        top, bot = int(round(cy - hw)) + sheer(x), int(round(cy + hw)) + sheer(x)
        for y in range(top, bot + 1):
            deck.add((x, y))
        near[x] = bot
        foot = wl if x >= 10 else bot + 1 + int((wl - bot - 1) * (x - 3) / 7)  # the raked stem
        for y in range(bot + 1, foot + 1):
            side.add((x, y))
    # the hull's near side: lit toward the bow, turning out of the light at the stern
    for (x, y) in side:
        d = y - near[x] - 1
        lit = 2 if x < 30 else 1 if x < 92 else 0
        if d == 0:
            c = WOOD[3] if x < 92 else WOOD[2]  # the rubbing strake
        elif y == wl:
            c = '#22304A'  # the waterline, wet and dark
        elif y >= wl - 2:
            c = RED[2] if lit else RED[1]  # the boot-top
        elif y >= wl - 4:
            c = TAR[2] if lit == 2 else TAR[1] if lit else TAR[0]  # the stripe
        else:
            c = HULL_W[3 + lit] if d > 1 else HULL_W[5] if lit else HULL_W[4]
            if d > 1 and d % 3 == 0:
                c = HULL_W[2 + lit]  # the plank seams of the topsides
        if x >= 120:
            c = shade_hex(c, 0.78)  # the stern's rounding
        cv.set(x, y, c)
    for x in range(4, 10):  # the stem post, lit
        if x in near:
            cv.set(x, near[x] + 1, WOOD[4])
    for px in range(34, 100, 9):  # portholes: brass rims, glass catching the sky
        py = near[px] + 4
        cv.set(px, py, '#9FC7E6'); cv.set(px + 1, py, WTR[1]); cv.set(px, py + 1, WTR[1]); cv.set(px + 1, py + 1, WTR[0])
        cv.set(px - 1, py, GOLD[2]); cv.set(px + 2, py + 1, GOLD[1])
    # the hawse pipe at the bow, rust running from it, the chain going in
    ax, ay = 13, near[13] + 2
    cv.set(ax, ay, IRON[0]); cv.set(ax + 1, ay, IRON[1]); cv.set(ax, ay + 1, IRON[1])
    for k in range(2, 5):
        cv.set(ax + (k % 2), ay + k, RED[1] if k < 4 else HULL_W[2])
    # the deck: planks fore and aft, caulked seams, lit at the bow
    for (x, y) in deck:
        e_far = (x, y - 1) not in deck
        e_near = (x, y + 1) not in deck
        if e_far:
            c = WOOD[4] if x < 60 else WOOD[3]  # the far bulwark's cap rail
        elif (x, y - 2) not in deck:
            c = HULL_W[3] if x < 60 else HULL_W[2]  # the far bulwark's inner face
        elif e_near:
            c = WOOD[4] if x < 60 else WOOD[3]  # the near cap rail
        else:
            c = WOOD[2] if (y - cy) % 2 == 0 else (WOOD[4] if x < 34 else WOOD[3])
            if (y - cy) % 2 == 0 and (x * 7 + y * 3) % 23 == 0:
                c = WOOD[1]  # a butt joint
        cv.set(x, y, c)

    def P(x, py, z):  # a point in plan (x, py across the beam) at height z, to the screen
        return int(round(cy + py * sq - z))

    # the foredeck: two bitts, a windlass and a coil of rope by the hatch
    for bx in (18, 30):
        by = P(bx, 3, 0)
        cv.set(bx, by - 2, IRON[3]); cv.set(bx, by - 1, IRON[2]); cv.set(bx + 1, by - 1, IRON[1]); cv.set(bx + 1, by - 2, IRON[2])
    for x in range(22, 27):
        cv.set(x, P(x, -1, 2), IRON[3] if x < 24 else IRON[2]); cv.set(x, P(x, -1, 1), IRON[1])
    cv.set(21, P(21, -1, 2), IRON[2]); cv.set(27, P(27, -1, 2), IRON[1])
    for k in range(12):
        a = k * 0.55
        cv.set(int(round(30 + math.cos(a) * 2.6)), int(round(P(30, -3, 0) + math.sin(a) * 1.4)), ROPE[3] if k % 3 else ROPE[1])
    # the saloon: roof (top face) and front face, the left end lit
    sx0, sx1, sh, shw = 36, 98, 10, 8  # its plan, height and half-depth
    roof0, roof1 = P(0, -shw, sh), P(0, shw, sh)
    front0, front1 = roof1 + 1, P(0, shw, 0)
    for y in range(roof0, front1 + 1):
        for x in range(sx0, sx1):
            if y <= roof1:
                c = RED[4] if (y == roof0 or x == sx0) else RED[3] if x < sx1 - 6 else RED[2]
                if y == roof1:
                    c = RED[1]  # the roof's front eave
            else:
                c = HULL_W[5] if x < sx0 + 2 else HULL_W[4] if x < sx1 - 3 else HULL_W[3]
                if y == front0:
                    c = HULL_W[2]  # the eave's shadow on the face
                if y == front1:
                    c = WOOD[1]  # the coaming where it meets the deck
            cv.set(x, y, c)
    for x in range(sx0 + 3, sx1 - 2, 4):  # the roof's seams
        for y in range(roof0 + 1, roof1):
            if (x + y) % 2:
                cv.set(x, y, RED[3] if x < sx1 - 6 else RED[1])
    wy = front0 + 2
    panes = []
    for wx in list(range(sx0 + 8, 80, 7)):  # the saloon windows
        for yy in range(wy, wy + 4):
            for xx in range(wx, wx + 5):
                k = yy - wy
                c = '#B8D6EE' if (k == 0 and xx < wx + 3) else WTR[2] if k < 2 else WTR[1]
                cv.set(xx, yy, c)
        cv.hline(wx, wy + 4, 5, HULL_W[2])  # the sill's shadow
        cv.set(wx + 4, wy, WTR[1])
        panes.append((wx, wy, 5, 4))
    # a life ring by the forward end of the saloon
    for (x, y) in disc(sx0 + 4, wy + 2, 2.4):
        if (x - (sx0 + 4)) ** 2 + (y - (wy + 2)) ** 2 > 1.2:
            cv.set(x, y, RED[3] if (x + y) % 3 else HULL_W[5])
    # the door onto the gangway: planked, a brass knob, a step
    dx0 = 84
    for y in range(wy - 1, front1):
        for x in range(dx0, dx0 + 5):
            cv.set(x, y, WOOD[3] if x == dx0 else WOOD[2] if (x - dx0) % 2 else WOOD[1])
    cv.set(dx0 + 3, wy + 3, GOLD[3])
    cv.hline(dx0 - 1, wy - 2, 7, HULL_W[2])
    # the wheelhouse on the saloon's forward end: roof, a face of windows, the helmsman's lamp
    hx0, hx1, hh, hhw = 40, 58, 9, 4
    hroof0, hroof1 = P(0, -hhw, sh + hh), P(0, hhw, sh + hh)
    hface1 = P(0, hhw, sh)
    for y in range(hroof0, hface1 + 1):
        for x in range(hx0, hx1):
            if y <= hroof1:
                c = HULL_W[5] if (y == hroof0 or x == hx0) else HULL_W[4] if x < hx1 - 3 else HULL_W[3]
                if y == hroof1:
                    c = HULL_W[2]
            else:
                c = HULL_W[4] if x < hx0 + 2 else HULL_W[3] if x < hx1 - 2 else HULL_W[2]
            cv.set(x, y, c)
    hy = hroof1 + 2
    for wx in (hx0 + 2, hx0 + 7, hx0 + 12):
        for yy in range(hy, hy + 3):
            for xx in range(wx, wx + 4):
                cv.set(xx, yy, '#B8D6EE' if (yy == hy and xx < wx + 2) else WTR[2] if yy == hy else WTR[1])
        panes.append((wx, hy, 4, 3))
    cv.hline(hx0, hface1, hx1 - hx0, HULL_W[1])  # the wheelhouse's shadow on the saloon roof
    cv.hline(hx0 + 1, hface1 + 1, hx1 - hx0, RED[1])
    # the mast behind the wheelhouse: a masthead lamp and a pennant
    mx = 55
    for y in range(1, hroof0 + 1):
        cv.set(mx, y, WOOD[3]); cv.set(mx + 1, y, WOOD[1])
    cv.hline(mx - 3, 6, 8, WOOD[2])  # the yard
    cv.set(mx, 0, GOLD[4]); cv.set(mx + 1, 0, GOLD[3])  # the masthead lamp
    for k in range(5):
        cv.set(mx + 2 + k, 2 + k // 3, RED[3] if k < 3 else RED[2])
    panes.append((mx, 0, 2, 1))
    # the funnel: a cylinder on the roof, lit left, a company band, a black top with its mouth
    fx0, fx1, fz0, fz1 = 70, 78, sh, sh + 15
    base, top = P(0, 0, fz0), P(0, 0, fz1)
    for y in range(top, base + 1):
        for x in range(fx0, fx1):
            k = x - fx0
            c = RED[4] if k < 2 else RED[3] if k < 5 else RED[2] if k < 7 else RED[1]
            if y < top + 3:
                c = IRON[3] if k < 2 else IRON[2] if k < 5 else IRON[1]
            elif y in (top + 6, top + 7):
                c = HULL_W[5] if k < 3 else HULL_W[4] if k < 6 else HULL_W[3]
            cv.set(x, y, c)
    for (x, y) in oval(fx0 + 4, top, 4, 1.3):
        cv.set(x, y, IRON[0] if y >= top else IRON[2])
    cv.set(fx0 + 1, top - 1, IRON[4])
    for x in range(fx0, fx1 + 1):  # the funnel's shadow on the roof behind it
        if cv.get(x + 2, base + 1)[3]:
            cv.set(x + 2, base + 1, RED[1])
    # the after deck: benches against the far bulwark, a bollard pair, the ensign staff
    for bx0 in (100, 110):
        by = P(bx0, -6, 0)
        cv.hline(bx0, by, 7, WOOD[4]); cv.hline(bx0, by + 1, 7, WOOD[2])
        cv.set(bx0, by + 2, WOOD[1]); cv.set(bx0 + 6, by + 2, WOOD[1])
    for bx in (112, 117):
        by = P(bx, 4, 0)
        cv.set(bx, by - 1, IRON[3]); cv.set(bx, by, IRON[1]); cv.set(bx + 1, by - 1, IRON[2]); cv.set(bx + 1, by, IRON[0])
    ex = 122
    ey = P(ex, 0, 0)
    for y in range(ey - 12, ey):
        cv.set(ex, y, WOOD[2])
    for y in range(ey - 12, ey - 7):
        for x in range(ex + 1, ex + 5):
            cv.set(x, y, WTR[2] if y < ey - 9 else RED[3])
    # the near rail: white stanchions and a top rail, open at the gangway
    gate = range(dx0 - 1, dx0 + 7)
    for x in range(8, 121):
        if x not in near or x in gate:
            continue
        ry = near[x]
        cv.set(x, ry - 3, HULL_W[5] if x < 60 else HULL_W[4])
        if x % 5 == 0:
            cv.set(x, ry - 2, HULL_W[4]); cv.set(x, ry - 1, HULL_W[3])
    # fenders on the pier side: short rope-covered bolsters on lanyards over the strake
    for fx in (26, 52, 68, 102, 112):
        y0 = near[fx] + 1
        cv.set(fx, y0, ROPE[1]); cv.set(fx, y0 + 1, ROPE[1])
        for (x, y) in oval(fx + 0.5, y0 + 4.5, 1.6, 2.6):
            cv.set(x, y, ROPE[3] if x <= fx and y < y0 + 5 else ROPE[2] if x <= fx else ROPE[1])
        cv.set(fx + 1, y0 + 7, ROPE[0])
    # the gangway: a cleated plank from the door down to the pier, with a rope handrail
    g0, g1 = near[dx0] - 1, wl
    for y in range(g0, g1 + 1):
        t = (y - g0) / (g1 - g0)
        x = int(round(dx0 + t * 9))
        for k in range(5):
            cv.set(x + k, y, WOOD[4] if k == 0 else WOOD[3] if k < 4 else WOOD[1])
        if (y - g0) % 3 == 1:
            cv.hline(x + 1, y, 3, WOOD[2])  # a cleat
        hy2 = y - 4
        if hy2 >= g0 - 3:
            cv.set(x + 5, hy2, ROPE[2])
    # the mooring lines down to the pier: a bow spring and a stern line, sagging a little
    for (x0, x1) in ((19, 40), (116, 108)):
        y0 = P(x0, 3, 1)
        for k in range(0, 101):
            t = k / 100
            x = int(round(x0 + (x1 - x0) * t))
            y = int(round(y0 + (wl - y0) * t + math.sin(t * math.pi) * 2))
            if not cv.get(x, y)[3] or (x, y) in side:
                cv.set(x, y, ROPE[1] if (x, y) in side else ROPE[2])
    gp.WINDOWS.extend((box, (x - 37, y - 12, pw, ph)) for (x, y, pw, ph) in panes)
    return box


class _Offset:
    """Draws onto a canvas shifted by (dx, dy), so a prop can be drawn in its own frame."""

    def __init__(self, cv: Canvas, dx: int, dy: int):
        self.cv, self.dx, self.dy = cv, dx, dy

    def set(self, x, y, c):
        self.cv.set(x + self.dx, y + self.dy, c)

    def get(self, x, y):
        return self.cv.get(x + self.dx, y + self.dy)

    def hline(self, x, y, w, c):
        self.cv.hline(x + self.dx, y + self.dy, w, c)


def shade_hex(c: str, k: float) -> str:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02X%02X%02X' % (int(r * k), int(g * k), int(b * k))


def pier_ladder() -> Canvas:
    """A ladder down from a jetty's end into the water, 10 x 24, in the three-quarter view
    (art-faults.md rule 5: a jetty ends at a boat or a ladder): two wooden rails lit on the
    left with rungs between, iron straps at the top where it is bolted to the jetty's edge,
    weed on the rungs just above the waterline, the lower rungs dim and green under the
    water, and small ripples where the rails go in."""
    w, h = 10, 24
    cv = Canvas(w, h, pad=PAD)
    IRON = MATERIALS['iron']
    water = 15  # the waterline
    under = ('#3E5A4A', '#2E4438', '#24362C')
    for y in range(h):
        for (x, lit) in ((1, True), (7, False)):
            if y > water:
                c, edge = (under[0] if lit else under[1]), under[2]
            elif y > water - 4:
                c = LEAF[2] if (x + y) % 2 else (WOOD[2] if lit else WOOD[1])  # weed at the tide line
                edge = WOOD[1]
            else:
                c, edge = (WOOD[3] if lit else WOOD[2]), WOOD[1]
            cv.set(x, y, c); cv.set(x + 1, y, edge)
    for y in range(3, h - 1, 4):  # the rungs
        for x in range(3, 7):
            above = y <= water
            cv.set(x, y, WOOD[4] if above else under[0]); cv.set(x, y + 1, WOOD[1] if above else under[2])
    for x in (1, 2, 7, 8):  # iron straps where it is bolted to the jetty's edge
        cv.set(x, 0, IRON[3]); cv.set(x, 1, IRON[1])
    for x in (0, 3, 6, 9):  # small ripples round the rails at the waterline
        cv.set(x, water + 1, WTR[4] if x in (0, 6) else WTR[3])
    return cv


def buoy() -> Canvas:
    """A mooring buoy bobbing in the basin, 14 x 12, red with a white band."""
    cv = Canvas(14, 12, pad=PAD)
    for (x, y) in oval(7, 6, 5, 4):
        cv.set(x, y, RED[3] if x < 7 else RED[2])
    for x in range(2, 13):
        if cv.get(x, 6)[3]:
            cv.set(x, 6, PLASTER[5])
    cv.vline(7, 0, 3, TAR[2])
    return cv


def deck_chair(stripe=RED) -> Canvas:
    """A striped deck chair on the sand, 20 x 18: canvas slung in a wooden frame."""
    w, h = 20, 18
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, 13):  # the canvas, sloping back
        for x in range(4 + (y < 4), 16 - (y < 4)):
            band = (x // 3) % 2
            c = (stripe[3] if band else '#F2EEE6') if y < 9 else (stripe[2] if band else '#D8D2C6')
            cv.set(x, y, c)
    for (x0, x1) in ((3, 2), (16, 17)):  # the frame
        for t in range(14):
            cv.set(x0 + (x1 - x0) * t // 13, 2 + t, WOOD[3] if x0 < 10 else WOOD[2])
    cv.hline(3, 12, 14, WOOD[2]); cv.hline(3, 13, 14, WOOD[1])
    return cv


def driftwood() -> Canvas:
    """A bleached driftwood branch half in the sand, 34 x 12."""
    w, h = 34, 12
    cv = Canvas(w, h, pad=PAD)
    BONE = ['#6E625A', '#9A8E82', '#C2B8AA', '#E2DACE']
    for x in range(2, w - 4):
        y = 6 + int(math.sin(x / 6) * 1.5)
        cv.set(x, y - 1, BONE[3]); cv.set(x, y, BONE[2]); cv.set(x, y + 1, BONE[1])
    for (x0, dx, n) in ((10, 1, 6), (22, 1, 5)):  # snapped side branches
        for t in range(n):
            cv.set(x0 + dx * t, 5 - t // 2, BONE[2]); cv.set(x0 + dx * t, 6 - t // 2, BONE[1])
    cv.hline(4, 9, 20, '#C8A878')  # sand drifted along its foot
    return cv


def sailboat() -> Canvas:
    """A small sailboat out past the breakwater, 40 x 52: a white hull lit on its port
    side, a mast and a cream sail bellied by the wind, its shadow on the water."""
    w, h = 40, 52
    cv = Canvas(w, h, pad=PAD)
    hull = set()
    for x in range(4, w - 4):
        t = (x - 4) / (w - 8)
        half = 5 * (1 - abs(t - 0.4) ** 1.6 * 1.6) if t < 0.95 else 1
        for y in range(int(h - 10 - half), int(h - 10 + half) + 1):
            hull.add((x, y))
    for (x, y) in hull:
        cv.set(x, y, PLASTER[5] if y < h - 10 else PLASTER[3])
        if (x, y + 1) not in hull:
            cv.set(x, y, WTR[1])
    cv.hline(8, h - 10, w - 18, WOOD[3])  # the deck
    for y in range(4, h - 11):
        cv.set(18, y, WOOD[1])
    for y in range(6, h - 14):  # the sail, bellied out to the right
        span = int((y - 6) * 0.42 + 2 + math.sin((y - 6) / (h - 20) * math.pi) * 3)
        for x in range(19, 19 + span):
            cv.set(x, y, SAILCLOTH[4] if x < 19 + span - 3 else SAILCLOTH[3])
    cv.hline(19, h - 14, 16, WOOD[2])  # the boom
    for x in range(6, w - 4, 3):
        cv.set(x, h - 3, '#E6EEF6')  # its wake
    return cv


def props() -> dict[str, Canvas]:
    return {
        'cottage': cottage(80, 0), 'cottage_b': cottage(72, 1, door=RED, shutters=LEAF, net=''),
        'cottage_c': cottage(80, 2, door=LEAF, porch=True, net='left'),
        'cottage_d': cottage(76, 3, door=GOLD, shutters=WTR, shed=20, net=''), 'lighthouse': lighthouse(),
        'boat_blue': fishing_boat(64, WTR), 'boat_red': fishing_boat(56, RED), 'net_rack': net_rack(),
        'lobster_pots': lobster_pots(), 'fish_stall': fish_stall(), 'bollard': bollard(), 'anchor': anchor(),
        'upturned_boat': upturned_boat(), 'washing_line': washing_line(), 'washing_line_wall': washing_line(wall=True), 'buoy': buoy(),
        'harbour_ferry': harbour_ferry(), 'pier_ladder': pier_ladder(),
        'deck_chair': deck_chair(RED), 'deck_chair_b': deck_chair(WTR), 'driftwood': driftwood(), 'sailboat': sailboat(),
    }


if __name__ == '__main__':
    # by day, at night and on a second ground (prop_sheet.py; SHEET_GROUND picks it)
    import prop_sheet
    size = prop_sheet.sheet(props(), os.environ.get('SHEET', '/tmp/harbour-props.png'),
                            second=os.environ.get('SHEET_GROUND', 'sand'))
    print('sheet', size)
