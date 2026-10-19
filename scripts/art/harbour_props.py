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
from materials import MATERIALS, WOOD, STONE, RED, WTR, PLASTER, SLATE, GOLD, LEAF  # noqa: E402

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
    """A fisher's cottage, `width` x 74 (plus a lean-to `shed` px wide on its east side): a
    steep roof of tarred boards seen from above with a whitewashed chimney, thick
    whitewashed walls with small deep windows, a painted door (`door`, a colour ramp),
    painted `shutters` or none, a little timber `porch` over the door or none, a net hung
    to dry on the wall (`net`: 'left', 'right' or none) and stone footings. The variants
    keep Driftwood's four houses from being one sprite (rule 8; Claude A's review, 19 Oct)."""
    door = door or WTR
    house = width
    w, h = width + shed, 74
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (house - 1) / 2, 18, 40, 40, 66
    if shed:  # the lean-to first: the house's roof overlaps its top
        sx0 = house - 6
        for y in range(28, wall_bottom):
            for x in range(sx0, w - 2):
                if y < 44:  # its single slope of tarred boards, falling east
                    c = TAR[3] if (x - sx0) % 5 else TAR[2]
                    if y == 28:
                        c = TAR[4]
                    if x >= w - 4:
                        c = TAR[1]
                elif x < w - 3:  # its plank wall, open at the front where the nets hang
                    c = WOOD[2] if (x - sx0) % 4 else WOOD[1]
                    if y > 50 and sx0 + 6 < x < w - 7:
                        c = '#3E332C' if (x + y) % 5 else '#4A3D34'  # the open front, dim inside
                else:
                    c = WOOD[1]
                cv.set(x, y, c)
        for x in range(sx0, w - 2):
            cv.set(x, 44, TAR[1])  # the eave's shadow line
        for t in range(12):  # a net hanging in the open front
            for k in range(6):
                x, y = sx0 + 8 + k * 2 + (t % 2), 52 + t
                if x < w - 7 and (x + y) % 3 == 0:
                    cv.set(x, y, ROPE[-1] if t < 6 else ROPE[-2])
        for t in range(22):  # two oars leaning on the wall
            for (ox, col) in ((w - 6, WOOD[4]), (w - 9, WOOD[3])):
                x, y = ox + t // 6, 44 + t
                cv.set(x, y, col)
            if t > 17:
                cv.set(w - 6 + t // 6 - 1, 44 + t, WOOD[3])
    chim = rect_set(12, 6, 10, 14)
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, house - 3, TAR, hole=chim, seed=71 + seed, moss=None)
    for (x, y) in rect_set(12, 6, 10, 14):
        cv.set(x, y, PLASTER[4] if x < 16 else PLASTER[3])
    cv.rect(11, 5, 12, 3, PLASTER[5]); cv.rect(14, 6, 6, 2, '#2A2420')
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2), 7, house - 8,
                     apex_y, wall_top, PLASTER, boards=False)
    for (x, y) in rect_set(7, wall_top, house - 14, wall_bottom - wall_top):  # whitewash over rough stone
        n = noise2(x // 2, y // 2, 281 + seed)
        cv.set(x, y, PLASTER[5] if n > 0.55 else PLASTER[4])
        if noise2(x, y, 282 + seed) > 0.94:
            cv.set(x, y, PLASTER[2])  # a chip showing the stone
    proud = set()
    dx = int(ridge) - 7
    for (x, y) in rect_set(dx, wall_bottom - 20, 14, 20):  # the painted door, its boards
        cv.set(x, y, door[2] if (x - dx) % 4 else door[1])
    cv.hline(dx, wall_bottom - 20, 14, door[3]); cv.set(dx + 11, wall_bottom - 10, GOLD[4])
    proud |= rect_set(dx - 1, wall_bottom - 21, 16, 1)
    for wx in (13, house - 25):
        gp.window(cv, wx, wall_top + 6, 12, 10, shutters=shutters, sill=True, warm=seed % 2 == 0)
    if net:  # a net drying on the wall: a diamond mesh of rope
        nx = house - 22 if net == 'right' else 10
        for k in range(10):
            for t in range(8):
                x, y = nx + (k + t) % 10 + (t // 2), wall_top + 2 + t
                if 7 < x < house - 7 and (x + y) % 3 == 0:
                    cv.set(x, y, ROPE[2])
    detail.cast(cv, proud, 1, 1, k=1, on=PLASTER, reach=2)
    detail.overhang_shadow(cv, 7, house - 7, wall_top, lambda x: 3, k=2, cap=1)
    if porch:  # a little porch: a pitched canopy seen from above, on two posts
        px0, px1, py = dx - 4, dx + 18, wall_bottom - 27
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
    return cv


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


def net_rack() -> Canvas:
    """Nets drying on a rack of poles, 52 x 40: rope mesh sagging between posts, floats."""
    w, h = 52, 40
    cv = Canvas(w, h, pad=PAD)
    for px in (2, 25, 48):
        gp.post(cv, px, 4, h - 1, w=3, ramp=WOOD)
    cv.hline(2, 5, 49, WOOD[3])
    for seg in ((4, 25), (27, 48)):
        for x in range(seg[0], seg[1]):
            sag = int(math.sin((x - seg[0]) / (seg[1] - seg[0]) * math.pi) * 6)
            for y in range(6, 24 + sag):
                if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                    cv.set(x, y, ROPE[2] if y < 14 else ROPE[1])
            if (x - seg[0]) % 5 == 2:
                for (fx, fy) in disc(x, 24 + sag, 1.5):
                    cv.set(fx, fy, RED[3] if fx <= x else RED[2])
    return cv


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


def fish_stall() -> Canvas:
    """The fish market stall, 76 x 56: a blue and white canvas awning from above, a
    sloping counter of ice with fish laid in rows, a scale and a chalk price board
    (marks only, no words)."""
    w, h = 76, 56
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 20):
        for x in range(2, w - 2):
            stripe = (x // 8) % 2
            c = (WTR[2] if stripe else SAILCLOTH[4]) if y < 16 else (WTR[1] if stripe else SAILCLOTH[2])
            cv.set(x, y, c)
    for x in range(2, w - 2):
        cv.set(x, 20 + (x // 4) % 2, WTR[1] if (x // 8) % 2 else SAILCLOTH[1])
    for px in (4, w - 7):
        gp.post(cv, px, 20, h - 2, w=3, ramp=WOOD)
    for y in range(26, 40):  # ice
        for x in range(6, w - 6):
            cv.set(x, y, '#E6F2F6' if (x + y) % 4 else '#C6DDEE')
    for row, y in enumerate((28, 33)):
        for x in range(9, w - 12, 9):
            for t in range(7):
                cv.set(x + t, y + (1 if t in (0, 6) else 0), '#9AA8B8' if t < 5 else '#6E7E92')
            cv.set(x, y, '#2A2D36')
            cv.set(x + 6, y - 1, '#6E7E92'); cv.set(x + 6, y + 2, '#6E7E92')
    detail.boards(cv, rect_set(6, 40, w - 12, 12), WOOD, 2, 40, board=4, vertical=True, x0=6)
    cv.hline(6, 40, w - 12, WOOD[4])
    for (x, y) in rect_set(w - 20, 22, 12, 6):
        cv.set(x, y, '#2A2D36')
    cv.hline(w - 18, 24, 8, '#E6E2D0'); cv.hline(w - 18, 26, 5, '#E6E2D0')
    return cv


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


def washing_line() -> Canvas:
    """A washing line in a cottage yard, 52 x 34, in the three-quarter view (Matt, 19 Oct,
    fault 08: "the sheets are flat squares and the posts are uneven"): two even posts
    with crosstrees, set in the ground, the line sagging between them, and on it a sheet
    with folds and a hem, a shirt with its sleeves hanging, a striped towel and a pair of
    socks, each pegged, lit on the left and shaded where it folds."""
    w, h = 52, 34
    cv = Canvas(w, h, pad=PAD)
    for px in (3, 47):  # the posts, the same height, with crosstrees
        for y in range(5, h):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
        cv.hline(px - 2, 5, 6, WOOD[4]); cv.hline(px - 2, 6, 6, WOOD[2])
        cv.set(px - 1, h - 1, WOOD[1]); cv.set(px + 2, h - 1, WOOD[1])  # where it goes into the ground

    def line_y(x):
        return 6 + int(round(4 * math.sin(math.pi * (x - 5) / 42)))

    for x in range(5, 47):
        cv.set(x, line_y(x), ROPE[3])

    def hang(x0, x1, length, ramp, kind):
        for x in range(x0, x1):
            top = line_y(x) + 1
            hem = top + length + (1 if (x - x0) % 5 == 2 else 0)
            for y in range(top, hem):
                fold = (x - x0) % 4
                c = ramp[2] if fold == 0 else ramp[4] if fold == 1 else ramp[3]
                if kind == 'stripe' and (y - top) in (3, 4):
                    c = RED[3]
                if x == x1 - 1:
                    c = ramp[1]  # its shaded edge
                cv.set(x, y, c)
            cv.set(x, hem, ramp[1])  # the hem
        for x in (x0, x1 - 1):
            cv.set(x, line_y(x), WOOD[4])  # pegs

    SHEET = ['#8A8478', '#B8B0A0', '#DCD6C8', '#F0EBE0', '#FBF8F2']
    hang(8, 21, 16, SHEET, 'plain')
    for x in range(24, 32):  # the shirt: its body, collar and sleeves hanging
        top = line_y(x) + 1
        for y in range(top, top + 11):
            cv.set(x, y, RED[4] if x < 26 else RED[3] if x < 30 else RED[2])
        cv.set(x, top + 11, RED[1])
    for (sx, lit) in ((23, True), (32, False)):
        top = line_y(sx) + 2
        for y in range(top, top + 7):
            cv.set(sx, y, RED[3] if lit else RED[2])
    cv.set(27, line_y(27) + 1, '#F0EBE0'); cv.set(28, line_y(28) + 1, '#F0EBE0')  # the collar
    for y in (4, 6, 8):
        cv.set(28, line_y(28) + y, '#F0EBE0')  # buttons
    hang(34, 40, 9, WTR[:1] + WTR[:4] if len(WTR) < 5 else WTR, 'stripe')
    for (sx, col) in ((42, GOLD), (44, GOLD)):  # a pair of socks
        top = line_y(sx) + 1
        for y in range(top, top + 6):
            cv.set(sx, y, col[3]); cv.set(sx + 1, y, col[2])
        cv.set(sx + 2, top + 5, col[2]); cv.set(sx + 2, top + 6, col[1])
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
        'upturned_boat': upturned_boat(), 'washing_line': washing_line(), 'buoy': buoy(),
        'harbour_ferry': harbour_ferry(), 'pier_ladder': pier_ladder(),
        'deck_chair': deck_chair(RED), 'deck_chair_b': deck_chair(WTR), 'driftwood': driftwood(), 'sailboat': sailboat(),
    }


if __name__ == '__main__':
    # by day, at night and on a second ground (prop_sheet.py; SHEET_GROUND picks it)
    import prop_sheet
    size = prop_sheet.sheet(props(), os.environ.get('SHEET', '/tmp/harbour-props.png'),
                            second=os.environ.get('SHEET_GROUND', 'sand'))
    print('sheet', size)
