"""Props for the Ember Caldera, the lava fields under the volcano (world-atlas.md).

Light here comes from below as much as from the sky: basalt is dark and cool, lit
on its upper left by the sky and on its lower edges by the lava's glow; everything
hot steps up the lava ramp toward white at its core. Run directly for a sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import reach_detail as rd  # noqa: E402
import garden_props as gp  # noqa: E402
import reach_house as rh  # noqa: E402
from reach_house import T, part, rect, step, frame  # noqa: E402
import style_sheet as ss  # noqa: E402
from style_sheet import boards, roof_rows  # noqa: E402
from materials import MATERIALS  # noqa: E402

LAVA, BASALT, ASH, IRON = (MATERIALS[k] for k in ('lava', 'basalt', 'ash', 'iron'))
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def hex_top(cv: Canvas, cx: float, cy: float, r: float, lit: int = 3):
    """The flat top of a basalt column, a hexagon seen from above, lit at upper left."""
    pts = set()
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            dx, dy = abs(x - cx), abs(y - cy)
            if dy <= r * 0.87 and dx <= r - dy * 0.577:
                pts.add((x, y))
    for (x, y) in pts:
        k = (x - cx) + (y - cy)
        cv.set(x, y, BASALT[lit + 1] if k < -r * 0.6 else BASALT[lit] if k < r * 0.3 else BASALT[lit - 1])
    for (x, y) in pts:
        if (x, y + 1) not in pts or (x + 1, y) not in pts:
            cv.set(x, y, BASALT[0])
    return pts


def basalt_columns(n: int = 5, seed: int = 0) -> Canvas:
    """A cluster of hexagonal basalt columns of different heights, 60 x 64: each column
    shows two faces (the left lit by the sky, the right in shade) split by a dark edge,
    horizontal joints every few pixels, a lit hexagonal top, and lava glow at the feet."""
    w, h = 60, 64
    cv = Canvas(w, h, pad=PAD)
    cols = []
    for k in range(n):
        cx = 10 + int(noise2(k, 0, 251 + seed) * 40)
        top = 8 + int(noise2(k, 1, 251 + seed) * 28)
        cols.append((top, cx))
    for top, cx in sorted(cols, key=lambda c: (c[1] * 0.2 + c[0])):
        r = 9
        joint0 = int(noise2(cx, top, 252) * 6)
        for y in range(top, h - 2):
            for x in range(int(cx - r + 1), int(cx + r)):
                k = (x - cx) / r
                c = BASALT[3] if k < -0.45 else BASALT[2] if k < 0.05 else BASALT[1]
                if -0.12 < k < 0.05:
                    c = BASALT[0]  # the edge between two faces
                if (y - top + joint0) % 9 == 0:
                    c = BASALT[0] if k > -0.45 else BASALT[1]  # a column joint
                elif (y - top + joint0) % 9 == 1 and k < -0.45:
                    c = BASALT[4]
                if y > h - 9 and (x + y) % 2 == 0:
                    c = LAVA[1] if y < h - 5 else LAVA[2]  # glow from the lava below
                cv.set(x, y, c)
        hex_top(cv, cx, top, r)
    return cv


def _column(cv: Canvas, cx: float, top: int, foot: int, r: float, seed: int, glow: bool, broken: bool = False):
    """One hexagonal basalt column standing from `foot` up to `top`, seen in the three-
    quarter view: its top a hexagon foreshortened to the same angle as everything else
    (a vertex left and right, a flat edge front and back), three vertical faces below it
    (the left lit by the sky, the front mid, the right in shade) split by dark arrises,
    joints across it at the column's own spacing, each joint's lower block lit along its
    top edge, the top cracked across and chipped when `broken`, weathering streaks down
    the front, and at the foot either the lava's glow (`glow`) or grit banked against it."""
    spacing = 7 + int(noise2(seed, 0, 256) * 5)
    joint0 = int(noise2(seed, 1, 256) * spacing)
    tilt = (noise2(seed, 2, 256) - 0.5) * 0.8  # joints are not quite level
    fs = 0.42 * r  # the top's half depth, foreshortened

    def edge(x):  # where the top's front edges meet the faces
        d = abs(x - cx)
        return top + fs if d <= r * 0.5 else top + fs * (r - d) / (r * 0.5)
    for x in range(int(cx - r + 1), int(cx + r)):
        k = (x - cx) / r
        for y in range(int(edge(x + 0.5)), foot + 1):
            c = BASALT[3] if k < -0.5 else BASALT[2] if k < 0.46 else BASALT[1]
            if -0.58 < k <= -0.48 or 0.44 < k < 0.56:
                c = BASALT[0] if k > 0 else BASALT[1]  # the arrises between faces
            j = (y - top + joint0 + int(k * tilt * r)) % spacing
            if j == 0:
                c = BASALT[0] if k > -0.5 else BASALT[1]  # a joint
            elif j == 1 and k < 0.44:
                c = BASALT[4] if k < -0.5 else BASALT[3]  # the lit top edge of the block below it
            if -0.4 < k < 0.36 and noise2(x, (y - top) // 3, seed + 3) > 0.92:
                c = BASALT[1]  # a weathering streak down the front
            if glow and y > foot - 3:
                c = LAVA[1] if k < 0.46 else BASALT[0]  # the lava's glow on its foot
            elif glow and y == foot - 3 and k < 0.46:
                c = LAVA[0]
            elif not glow and y > foot - 2:
                c = BASALT[1] if k < 0.46 else BASALT[0]  # grit banked at its foot
            cv.set(x, y, c)
    pts = set()
    for y in range(int(top - fs), int(top + fs) + 1):
        for x in range(int(cx - r + 1), int(cx + r)):
            d = abs(x + 0.5 - cx)
            half = fs if d <= r * 0.5 else fs * (r - d) / (r * 0.5)
            if abs(y + 0.5 - top) <= half:
                pts.add((x, y))
    for (x, y) in pts:
        u = (x - cx) / r + (y - top) / max(1, fs) * 0.5
        c = BASALT[4] if u < -0.35 else BASALT[3] if u < 0.35 else BASALT[2]
        if (x, y - 1) not in pts and x < cx + r * 0.3:
            c = BASALT[4]  # the back edges catch the sky
        elif (x, y + 1) not in pts:
            c = BASALT[2] if x < cx - r * 0.5 else BASALT[1]  # the front arrises
        cv.set(x, y, c)
    if broken:  # a crack across the top and a chipped corner
        for t in range(int(r * 1.4)):
            x = int(cx - r * 0.7 + t)
            y = int(top - fs * 0.6 + t * fs / r + noise2(t, seed, 257) * 1.2)
            if (x, y) in pts:
                cv.set(x, y, BASALT[0])
        for (x, y) in pts:
            if x > cx + r * 0.25 and y < top - fs * 0.1:
                cv.set(x, y, BASALT[1] if (x + y) % 2 else BASALT[2])
    return pts


def basalt_formation(cols, w: int, h: int, seed: int = 0, glow: bool = False) -> Canvas:
    """A group of basalt columns, each (cx, top, foot, r, broken): drawn from the back
    (highest foot) forward, so nearer columns overlap the ones behind them, with rubble
    of fallen drums at the front."""
    cv = Canvas(w, h, pad=PAD)
    for i, (cx, top, foot, r, broken) in sorted(enumerate(cols), key=lambda c: (c[1][2], c[1][0])):
        _column(cv, cx, top, foot, r, seed * 31 + i, glow, broken)
    for i in range(3 + seed % 3):  # drums fallen from the tops, lying at the front
        fx = 4 + int(noise2(i, seed, 258) * (w - 10))
        fy = h - 3 - int(noise2(i, seed, 259) * 3)
        rr = 2 + noise2(i, seed, 260) * 2
        for (x, y) in oval(fx, fy, rr + 1, rr * 0.7):
            if 0 <= x < w and 0 <= y < h and not cv.get(x, y)[3]:
                cv.set(x, y, BASALT[3] if (x - fx) + (y - fy) < -1 else BASALT[2] if x < fx + 1 else BASALT[1])
    return cv


def basalt_columns(n: int = 5, seed: int = 0, glow: bool = False) -> Canvas:
    """A cluster of hexagonal basalt columns of different heights and girths, 60 x 64,
    standing where lava cooled slowly (`glow`: lit from below, for one standing in lava)."""
    w, h = 60, 64
    cols = []
    for k in range(n):
        cx = 10 + int(noise2(k, 0, 251 + seed) * 40)
        top = 8 + int(noise2(k, 1, 251 + seed) * 28)
        r = 7 + noise2(k, 3, 251 + seed) * 3.5
        foot = h - 2 - int(noise2(k, 4, 251 + seed) * 5)
        cols.append((cx, top, foot, r, noise2(k, 5, 251 + seed) > 0.75))
    return basalt_formation(cols, w, h, seed, glow=glow)


def basalt_steps() -> Canvas:
    """A stepped causeway of basalt, 88 x 70, the way cooled flows crack on a slope:
    columns rising from short stumps at the front left to tall ones at the back right,
    their hexagonal tops making a honeycomb of steps."""
    cols = []
    for k in range(11):
        row, i = divmod(k, 4)
        cx = 10 + i * 17 + row * 9 + int(noise2(k, 0, 261) * 4)
        foot = 66 - row * 7
        height = 6 + i * 6 + row * 7 + int(noise2(k, 1, 261) * 5)
        cols.append((cx, foot - height, foot, 8 + noise2(k, 2, 261) * 1.5, k in (2, 7)))
    return basalt_formation(cols, 88, 70, 3)


def basalt_stack() -> Canvas:
    """Three tall columns packed together with a shorter broken one in front, 40 x 88:
    a stack left standing where the cliff round it fell away."""
    return basalt_formation([(10, 16, 82, 8, False), (24, 9, 78, 9, False), (31, 28, 85, 7.5, False),
                             (16, 54, 86, 7, True)], 40, 88, 5)


def basalt_stumps(seed: int = 0) -> Canvas:
    """Short broken columns in a loose group, 48 x 30: what is left of an outcrop the
    weather has taken down, the tops cracked and chipped, drums lying round them."""
    cols = []
    for k in range(4):
        cx = 7 + k * 11 + int(noise2(k, 0, 262 + seed) * 4)
        foot = 26 - int(noise2(k, 1, 262 + seed) * 6)
        top = foot - 7 - int(noise2(k, 2, 262 + seed) * 9)
        cols.append((cx, top, foot, 6 + noise2(k, 3, 262 + seed) * 2.5, k != 1))
    return basalt_formation(cols, 48, 30, 7 + seed)


def basalt_fallen() -> Canvas:
    """A column lying on its side, 54 x 20, broken into drums at its joints: its lit top
    face, the shaded front face, the hexagonal end toward the light, sunk a little into
    the ash it fell on."""
    w, h = 54, 20
    cv = Canvas(w, h, pad=PAD)
    x0, x1, yt = 8, 50, 5
    for x in range(x0, x1):
        drum = (x - x0) // 9
        dy = int(noise2(drum, 0, 263) * 2)  # each drum settled a little differently
        for y in range(yt + dy, yt + dy + 12):
            k = (y - yt - dy) / 12
            c = BASALT[3] if k < 0.4 else BASALT[2] if k < 0.75 else BASALT[1]
            if k < 0.1:
                c = BASALT[4]
            if (x - x0) % 9 == 0:
                c = BASALT[0]  # the joint between two drums
            elif (x - x0) % 9 == 1 and k < 0.75:
                c = BASALT[4] if k < 0.4 else BASALT[3]
            cv.set(x, y, c)
    for (x, y) in oval(x0, yt + 6, 4, 6.5):  # the end, a hexagon seen edge-on, toward the light
        cv.set(x, y, BASALT[4] if y < yt + 4 else BASALT[3] if y < yt + 9 else BASALT[2])
    for x in range(x0 - 3, x1 + 1):  # ash heaped against its foot
        cv.set(x, yt + 13 + (x % 3 == 0), ASH[2])
        cv.set(x, yt + 14, ASH[1])
    return cv


def forge() -> Canvas:
    """The smithy, 96 x 80, in Hearthold's material kit (sunstone-comparison.md, "still
    to do": the forge as made as the castle): a slate roof pitched toward the viewer, its
    ridge lit and its eaves throwing a shadow on the wall; a chimney stack of dressed
    stone at the east end, sooted at the top, where the embers rise; a wall of coursed
    stone, every block its own tone and blackened round the furnace; the furnace mouth
    under an arch of voussoirs, white at its heart, its glow spilling on the floor; a
    leather bellows beside it; and to the east an open bay under an oak lean-to on two
    posts: the anvil on its stump, a quench trough of dark water and a rack of tongs and
    hammers. The anchors stay where the ember sources expect them (chimney top at x 75,
    the furnace at 30, 44)."""
    import castle_props as csp
    w, h = 96, 80
    cv = Canvas(w, h, pad=PAD)
    ST, SL, OAK = csp.STONE_R, csp.SLATE_R, csp.OAK
    # the wall: coursed stone, sooted toward the furnace and the foot
    wall = rect_set(4, 26, w - 8, 44)
    csp.masonry(cv, wall, seed=231, light=lambda x, y: -0.6 * max(0, 1 - math.hypot(x - 30, y - 50) / 26) - (0.5 if x > 60 else 0),
                course=(4, 6), block=(6, 11), soot=4)
    # the roof: slates pitched toward the viewer, lighter toward the ridge and the west
    roof = {(x, y) for y in range(6, 27) for x in range(3 + (26 - y) // 7, w - 3 - (26 - y) // 7)}
    csp.slates(cv, roof, seed=232, row=3, tile=(4, 6),
               light=lambda x, y: (-0.6 if y < 12 else -1.4) + (0.3 if x < 40 else -0.4 if x > 70 else 0))
    for y in range(8, 26):  # the verges: the roof's sloping ends, a lit barge stone on the west
        xl, xr = 3 + (26 - y) // 7, w - 4 - (26 - y) // 7
        cv.set(xl, y, SL[4]); cv.set(xr, y, SL[0])
    for x in range(6, w - 6):  # the ridge, its capping lit
        cv.set(x, 6, SL[5] if x < 60 else SL[4]); cv.set(x, 7, SL[3])
    for x in range(3, w - 3):  # the eaves' lip, and their shadow on the wall
        cv.set(x, 25, SL[1]); cv.set(x, 26, SL[0])
    rd.shadow_band(cv, 4, w - 4, 27, lambda x: 3, k=2)   # the masonry is off the ramps (D13)
    # the chimney stack at the east end, standing through the roof
    stack = rect_set(70, 0, 11, 20)
    csp.masonry(cv, stack, seed=233, light=lambda x, y: 1 if x < 73 else -1 if x > 78 else 0, course=(3, 4), block=(4, 6))
    for x in range(69, 82):
        cv.set(x, 0, ST[5] if x < 76 else ST[3]); cv.set(x, 1, ST[1])  # its cap stone
    for (x, y) in rect_set(72, 2, 7, 3):  # soot round the flue's mouth
        if (x + y) % 2 == 0:
            cv.set(x, y, '#2A2628')
    for x in range(71, 81):
        cv.set(x, 20, SL[0])  # flashing where the stack meets the slates
    # the furnace (review 19 Oct: not a square block of glow): a round-headed opening
    # under an arch of wedge-shaped voussoirs with a keystone, between dressed jambs on a
    # stone sill; inside it is dark with soot, and the fire is a bed of coals at the back
    # with flames licking up from it, white only at their heart; the fire's light touches
    # the arch's inner edge and the sill, nothing more
    acx, acy, ar = 30, 52, 8
    opening = {(x, y) for (x, y) in disc(acx, acy, ar) if y < acy} | rect_set(acx - ar, acy, 2 * ar + 1, 14)
    ring = {(x, y) for (x, y) in disc(acx, acy, ar + 4.5) if y < acy + 1} - opening
    for (x, y) in ring:
        a = math.atan2(acy - y, x - acx)  # 0 east, pi west
        k = int(a / (math.pi / 7))  # seven voussoirs
        edge = abs(a / (math.pi / 7) - round(a / (math.pi / 7))) < 0.09
        c = ST[1] if edge else (ST[5] if k == 3 else ST[4] if x < acx - 2 else ST[3] if x < acx + 3 else ST[2])
        if math.hypot(x - acx, y - acy) > ar + 3.6:
            c = ST[1]  # the joint round the arch
        cv.set(x, y, c)
    for (x, y) in rect_set(acx - ar - 4, acy, 4, 14) | rect_set(acx + ar + 1, acy, 4, 14):  # the jambs
        west = x < acx
        c = ST[4] if west else ST[2]
        if (y - acy) % 5 == 4:
            c = ST[1]
        cv.set(x, y, c)
    for (x, y) in opening:  # the soot-dark mouth, warmer toward the fire
        d = acy + 13 - y
        cv.set(x, y, '#1A1012' if d > 8 else '#2E1A16' if d > 4 else '#4A2418')
    for x in range(acx - ar, acx + ar + 1):  # the bed of coals at the back
        for y in range(acy + 10, acy + 14):
            n = noise2(x, y, 235)
            cv.set(x, y, LAVA[4] if n > 0.75 else LAVA[3] if n > 0.4 else LAVA[2] if n > 0.15 else BASALT[1])
    for (fx, fh) in ((acx - 3, 5), (acx, 8), (acx + 3, 6), (acx + 6, 3), (acx - 6, 3)):  # flames licking up
        for t in range(fh):
            y = acy + 10 - t
            cv.set(fx, y, LAVA[5] if t < fh // 3 and fh > 5 else LAVA[4] if t < fh * 2 // 3 else LAVA[3])
            if t < fh // 2:
                cv.set(fx + 1, y, LAVA[3])
    for (x, y) in ring:  # the fire's light on the arch's inner edge, lower down only
        if y > acy - 5 and any((x + dx, y + dy) in opening for dx, dy in ((1, 0), (-1, 0), (0, 1))):
            cv.set(x, y, '#C88A5A')
    for x in range(acx - ar - 5, acx + ar + 6):  # the sill, lit along its top, the glow on its lip
        cv.set(x, acy + 14, ST[5] if x < acx + 6 else ST[4]); cv.set(x, acy + 15, ST[2])
        if acx - ar <= x <= acx + ar:
            cv.set(x, acy + 14, '#E8B070' if x % 2 else ST[5])
    # the bellows, leather between two oak boards, its nozzle into the furnace's side
    for (x, y) in oval(8, 60, 4, 6):
        cv.set(x, y, '#6A4632' if x < 8 else '#4E3426')
    for y in range(55, 66, 3):
        cv.hline(5, y, 7, '#3A261C')
    cv.vline(8, 66, 3, OAK[3]); cv.hline(9, 60, 6, IRON[2])
    # the floor in front: flags, scorched dark before the furnace where sparks fall, a few
    # embers lying on it (review 19 Oct: no checkered spill)
    for (x, y) in rect_set(4, 68, w - 8, 6):
        sx = (x + (y // 3) % 2 * 4) // 8
        c = ST[2] if noise2(sx, y // 3, 234) > 0.4 else ST[1]
        if (x + (y // 3) % 2 * 4) % 8 == 0 or y % 3 == 0:
            c = MATERIALS['ash'][0]
        if math.hypot((x - 30) / 16, (y - 70) / 4) < 1 and noise2(x // 2, y, 236) > 0.25:
            c = BASALT[1] if c != MATERIALS['ash'][0] else BASALT[0]  # the scorch
        cv.set(x, y, c)
    for (ex, ey) in ((24, 70), (33, 72), (38, 69), (19, 72), (42, 72)):
        cv.set(ex, ey, LAVA[3])
    cv.set(33, 71, LAVA[4])
    for x in range(4, w - 4):
        cv.set(x, 74, BASALT[0])  # the step's shadow on the ash
    # the open bay: an oak lean-to on two posts, its shade on the wall
    for x in range(54, w - 3):  # its roof of planks, seen from above, sloping down from the wall
        for y in range(29, 37):
            c = OAK[4] if y < 31 else OAK[3]
            if (x - 54) % 5 == 0:
                c = OAK[1]  # the gap between two planks
            elif (x - 54) % 5 == 1:
                c = OAK[5] if y < 33 else OAK[4]  # each plank's lit edge
            cv.set(x, y, c)
        cv.set(x, 28, SL[1])  # where it meets the wall, under the eaves
        for y in range(37, 41):  # the beam's face below the planks' ends
            cv.set(x, y, OAK[3] if y == 37 else OAK[2] if y < 39 else OAK[1])
    for x in range(55, w - 4):
        for y in range(41, 45):
            rd.darken(cv, [(x, y)], 1.2 if y > 42 else 2.2)
    for px in (56, w - 8):
        for y in range(41, 70):
            cv.set(px, y, OAK[4]); cv.set(px + 1, y, OAK[3]); cv.set(px + 2, y, OAK[1])
    # a rack of tongs and hammers on the wall under the lean-to
    cv.hline(62, 46, 22, OAK[2]); cv.hline(62, 47, 22, OAK[0])
    for k, tx in enumerate(range(64, 84, 4)):
        L = 7 + (k % 2) * 3
        cv.vline(tx, 48, L, IRON[3]); cv.set(tx + 1, 48, IRON[1])
        if k % 2:
            cv.hline(tx - 1, 48 + L, 3, IRON[2])  # a hammer's head
        else:
            cv.set(tx - 1, 48 + L, IRON[2]); cv.set(tx + 1, 48 + L, IRON[2])  # the tongs' jaws
    # the anvil on its stump
    for (x, y) in oval(66, 66, 6, 3):
        cv.set(x, y, OAK[3] if y < 66 else OAK[1])
    for y in range(62, 66):
        cv.hline(62, y, 9, OAK[2] if y > 62 else OAK[4])
    cv.hline(58, 57, 15, IRON[4]); cv.hline(58, 58, 15, IRON[3]); cv.hline(57, 57, 2, IRON[3])  # the face and horn
    for y in range(59, 62):
        cv.hline(62, y, 7, IRON[2] if y < 61 else IRON[1])
    cv.set(59, 57, IRON[5] if len(IRON) > 5 else IRON[4])
    # the quench trough, dark water with a glint
    for (x, y) in rect_set(76, 60, 14, 8):
        edge = x in (76, 89) or y in (60, 67)
        cv.set(x, y, OAK[4] if (edge and (y == 60 or x == 76)) else OAK[1] if edge else '#2E4458')
    cv.hline(78, 62, 3, '#6C8CA4')
    return cv


def obsidian_rock(big: bool = True) -> Canvas:
    """A cluster of obsidian shards, 30 x 26 (or 18 x 16): each shard a glassy black
    blade with a bright sky glint down its lit edge, a violet sheen across the middle
    and a red rim of reflected lava glow at its foot."""
    w, h = (30, 26) if big else (18, 16)
    cv = Canvas(w, h, pad=PAD)
    shards = ((0.3, 0.1, 0.22), (0.62, 0.0, 0.2), (0.82, 0.35, 0.16), (0.15, 0.45, 0.15)) if big else ((0.4, 0.05, 0.3), (0.75, 0.35, 0.2))
    for (fx, ft, fw) in shards:
        cx, tip, half = fx * w, int(ft * h) + 1, fw * w
        for y in range(tip, h - 1):
            t = (y - tip) / max(1, h - 2 - tip)
            hw = max(1, half * t)
            for x in range(int(cx - hw), int(cx + hw) + 1):
                k = (x - (cx - hw)) / (2 * hw + 1)
                c = BASALT[2] if k < 0.45 else BASALT[1]
                if 0.35 < k < 0.5 and 0.3 < t < 0.7:
                    c = '#4A3E6A'
                if k < 0.12:
                    c = '#B8C2E6' if t < 0.5 else '#7A86B0'
                if y >= h - 3:
                    c = LAVA[1] if k > 0.3 else LAVA[2]
                cv.set(x, y, c)
    return cv


def cooling_vent() -> Canvas:
    """A cone of cooled crust round a vent, 30 x 22, with a glowing throat and a wisp."""
    cv = Canvas(30, 22, pad=PAD)
    cone = oval(15, 15, 13, 6)
    for (x, y) in cone:
        cv.set(x, y, ASH[3] if (x - 15) + (y - 15) * 2 < -4 else ASH[2] if x < 18 else ASH[1])
    for (x, y) in oval(15, 13, 4, 2):
        cv.set(x, y, LAVA[4] if y < 13 else LAVA[3])
    for (bx, by, r) in ((15, 7, 3), (17, 3, 2.2)):
        for (x, y) in disc(bx, by, r):
            cv.set(x, y, ASH[4] if x < bx else ASH[3])
    return cv


def basalt_bridge(length: int = 64) -> Canvas:
    """A basalt slab bridge over a lava channel, 64 x 26: dressed slabs lit on top, its
    underside glowing from the lava below."""
    cv = Canvas(length, 26, pad=PAD)
    for y in range(6, 18):
        for x in range(0, length):
            slab = (x // 10) % 2
            cv.set(x, y, BASALT[4] if y == 6 else (BASALT[3] if slab else BASALT[2]))
            if x % 10 == 0:
                cv.set(x, y, BASALT[0])
    for x in range(0, length):
        cv.set(x, 18, BASALT[1]); cv.set(x, 19, LAVA[2]); cv.set(x, 20, LAVA[1])
    for px in (2, length - 6):
        for y in range(2, 8):
            cv.hline(px, y, 4, BASALT[3] if y < 4 else BASALT[2])
    return cv


def _hex_column(cv: Canvas, cx: int, top: int, foot: int, r: int, seed: int, chipped: bool = False):
    """A basalt column cut from the flow, on the house ramps: a hexagonal prism seen from
    the south and above. Its lit hexagonal top (tone 4, a tone 5 glint at its upper left),
    the west face to the light (3), the south face (2 to 3), the east face in shade (1),
    hard edges between faces, and the flow's cooling joints across it every few pixels."""
    x0, x1 = cx - r, cx + r
    cap = max(2, r // 2)
    for y in range(top + cap, foot):                       # the faces
        for x in range(x0, x1 + 1):
            u = (x - x0) / max(1, x1 - x0)
            k = 4 if u < 0.3 else 2 if u < 0.72 else 1
            if (y - top + seed) % 7 == 0 and 0 < x - x0 < 2 * r:
                k = max(0, k - 1)                           # a cooling joint across the column
            cv.set(x, y, T(('basalt', 'basalt_warm', 'basalt_cool')[seed % 3], k))
        cv.set(x0 + round(0.3 * 2 * r), y, T('basalt', 5))  # the lit arris between west and south faces
    for y in range(top, top + cap + 1):                    # the hexagonal top
        d = abs(y - (top + cap / 2)) / (cap / 2 + 0.5)
        inset = round(d * r * 0.4)
        for x in range(x0 + inset, x1 - inset + 1):
            cv.set(x, y, T('basalt', 5 if x < cx + 1 else 4))
    cv.set(x0 + 1, top + cap // 2, T('basalt', 5)); cv.set(x0 + 2, top + cap // 2, T('basalt', 5))
    if chipped:                                            # a corner broken off the top, the break in shade
        for (x, y) in ((x1, top), (x1, top + 1), (x1 - 1, top), (x1, top + 2)):
            cv.set(x, y, (0, 0, 0, 0))
        cv.set(x1 - 1, top + 1, T('basalt', 1)); cv.set(x1, top + 3, T('basalt', 1))


def ember_shrine() -> Canvas:
    """The ember shrine, 30 x 50 (asset ledger 20 Oct: redrawn on the house ramps, its foot
    3 whole cells): the keeper's warning to rest before you burn out, built of what the
    caldera gives. Three basalt columns cut from the flow: a tall one in the middle carrying
    an iron brazier on three legs, its embers banked under ash with a low flame (the glow
    has no outline and lights the night tint as before), and two shorter ones either side
    holding offerings (a clay cup, a folded paper weighed with a pebble). A straw rope with
    paper tags sags between the short columns across the tall one's front; a flame mark is
    cut in the tall column's face and the heat has sooted the stone under the bowl. Swept
    ash round the foot, and an iron poker leaning on the east column."""
    w, h = 30, 50
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rh.ellipse(15, 46.5, 11.0, 2.8):        # the swept ash bed the columns stand in
        cv.set(x, y, T('ash', 2 if y > 46 else 3 if smooth_noise(x, y, 3, 4361) < 0.6 else 4))
    _hex_column(cv, 6, 32, 47, 2, 1)                       # the west column, shorter
    _hex_column(cv, 24, 30, 47, 2, 2, chipped=True)        # the east one, chipped
    _hex_column(cv, 15, 17, 48, 5, 0)                      # the tall middle column
    for x in range(11, 20):                                # soot under the bowl on the column's front
        for y in range(21, 25):
            if smooth_noise(x, y, 2, 4366) < 0.62 - (y - 21) * 0.12:
                cv.set(x, y, T('soot', 1))
    for (x, y) in ((15, 27), (14, 28), (15, 28), (16, 28), (14, 29), (15, 29), (16, 29), (15, 30), (15, 31)):
        cv.set(x, y, T('basalt', 0))                        # the flame mark cut in its face
    cv.set(15, 28, T('lava', 2)); cv.set(15, 29, T('lava', 2))   # embers' light caught in the cut
    cv.hline(14, 32, 3, T('basalt', 4))                    # the cut's lit lower lip
    for (lx, ly0) in ((11, 14), (15, 15), (19, 14)):       # the brazier: a shallow iron bowl on three legs
        for y in range(ly0, 18):
            cv.set(lx, y, T('iron', 3 if lx < 15 else 1))
    for (x, y) in rh.ellipse(15, 13, 7, 2.6):
        cv.set(x, y, T('iron', 4 if y < 12 else 3 if x < 13 else 2 if x < 18 else 1))
    for (x, y) in rh.ellipse(15, 12, 5, 1.6):             # the banked embers under grey ash
        n = smooth_noise(x, y, 1.5, 4365)
        cv.set(x, y, T('ash', 4) if n > 0.7 else T('lava', 4 if n < 0.35 else 3))
    for (x, y, k) in ((14, 9, 3), (15, 8, 3), (15, 9, 4), (16, 9, 3), (15, 7, 2), (14, 10, 3), (16, 10, 3), (15, 10, 5)):
        cv.set(x, y, T('lava', k))                         # a low flame
    for (x, y) in ((8, 13), (22, 13)):                     # the rim's ring handles
        cv.set(x, y, T('iron', 4 if x < 15 else 2)); cv.set(x, y + 1, T('iron', 1))
    for (x, y) in rect(5, 30, 3, 2):                       # a clay cup on the west column, its rim lit
        cv.set(x, y, T('clay', 3 if x < 6 else 2))
    cv.hline(5, 29, 3, T('clay', 4))
    for (x, y) in rect(21, 27, 4, 2):                      # a folded paper weighed with a pebble on the east one
        cv.set(x, y, T('plaster', 5 if y == 27 else 4))
    cv.set(22, 26, T('ash', 4)); cv.set(23, 26, T('ash', 3))
    for x in range(8, 23):                                 # the straw rope sagging across the front
        t = (x - 8) / 14
        y = int(round(35 + 16 * t * (1 - t)))
        cv.set(x, y, T('sand', 4 if x % 3 else 3)); cv.set(x, y + 1, T('sand', 2))
        if x in (11, 15, 19):                              # paper tags folded in zigzags
            for d in range(4):
                cv.set(x + (d % 2), y + 2 + d, T('plaster', 5 if d % 2 == 0 else 3))
    for (px, py) in ((10, 44), (12, 45), (18, 45), (20, 44)):   # pebbles left at the foot, each a visitor's
        cv.set(px, py, T('stone', 4)); cv.set(px + 1, py, T('stone', 2)); cv.set(px, py - 1, T('stone', 3))
    for ty in (36, 39, 42):                                # tally marks scratched in the tall column by the keepers
        cv.hline(12, ty, 2, T('basalt', 4)); cv.hline(17, ty, 2, T('basalt', 0))
    for k in range(11):                                    # the poker leaning on the east column, its tip in the ash
        cv.set(28 - k // 4, 33 + k, T('iron', 4 if k < 3 else 2))
    return rh.finish(cv, keep=[(15, 10)])


CHAR = ['#1A1412', '#2A201C', '#3E302A', '#58443A', '#76604E']  # charred cedar
LANTERN = ['#7A3A12', '#C2621E', '#F2A048', '#FFE0A0']


def bathhouse() -> Canvas:
    """The bathhouse at Cinder Springs, 102 x 88 (asset ledger 20 Oct: redrawn on the house
    ramps, its foot 13 whole cells; prop audit ADJUST "door 28" now 32, "steam from a roof
    vent" now a louvred vent on the ridge for the steam to rise from). A low hall of charred
    cedar boards (burnt dark to keep them sound, a silver sheen on the char) between timber
    posts, on a basalt plinth, under a hipped roof of basalt slates seen from above, its
    west hip lit and its east hip in shade, a ridge of round caps. Paper screens glow warm
    from the lamps inside; the doorway is curtained with a split cloth printed with the
    springs' sign, steam drifting in the dark behind it; paper lanterns hang on cords from
    the eave. A boardwalk deck out front with buckets and a stack of folded towels."""
    w, h = 102, 88
    cv = Canvas(w, h, pad=PAD)
    ridge_y, eave_y = 12, 42                      # the roof: from the ridge down to the eave
    wall0, wall1 = eave_y + 3, 74                  # the wall below the eave, to the plinth
    deck_y = 76
    rx0, rx1 = 24, w - 25                          # the ridge's ends
    roof = set()
    for y in range(ridge_y, eave_y + 1):
        t = (y - ridge_y) / (eave_y - ridge_y)
        xl, xr = round(rx0 - t * (rx0 - 0)), round(rx1 + t * (w - 1 - rx1))
        for x in range(xl, xr + 1):
            roof.add((x, y))
    roof_rows(cv, 0, ridge_y, w, eave_y - ridge_y + 1, 'basalt', 3, row=5, tile=(6, 8), seed=161, clip=roof,
              moss=True)                           # moss in the slates' lower corners: the steam keeps them damp
    for y in range(ridge_y, eave_y + 1):
        t = (y - ridge_y) / (eave_y - ridge_y)
        hw = round(rx0 - rx0 * t * 0.55)           # the west hip's line, leaning out from the ridge's end
        he = round(rx1 + (w - 1 - rx1) * t * 0.55)
        for x in range(0, hw):
            if (x, y) in roof:
                step(cv, x, y, 1)                  # the west hip faces the light
        for x in range(he + 1, w):
            if (x, y) in roof:
                step(cv, x, y, -1)                 # the east hip turns away from it
        if (hw, y) in roof:
            cv.set(hw, y, T('basalt', 5)); cv.set(hw + 1, y, T('basalt', 2))   # the hip's capping, lit on its west
        if (he, y) in roof:
            cv.set(he, y, T('basalt', 4)); cv.set(he + 1, y, T('basalt', 1))
    for x in range(rx0, rx1 + 1):                  # the ridge: a row of round caps
        j = (x - rx0) % 4
        cv.set(x, ridge_y - 1, T('basalt', 4 if j < 2 else 3) if j != 3 else T('basalt', 2))
        cv.set(x, ridge_y, T('basalt', 2 if j != 3 else 1))
    vx0, vx1 = w // 2 - 7, w // 2 + 7              # the louvred vent on the ridge, where the steam goes out
    for y in range(ridge_y - 8, ridge_y - 1):
        for x in range(vx0, vx1):
            louvre = (y - (ridge_y - 8)) % 2 == 1 and 2 <= y - (ridge_y - 8) < 6
            k = 4 if x == vx0 else 2 if x == vx1 - 1 else 3
            cv.set(x, y, T('earth_cool', 0) if louvre and vx0 < x < vx1 - 1 else T('timber_cool', k))
    for x in range(vx0 - 2, vx1 + 2):              # its little roof of slates
        cv.set(x, ridge_y - 10, T('basalt', 4 if x < w // 2 else 3)); cv.set(x, ridge_y - 9, T('basalt', 2))
    for x in range(0, w):                          # the fascia board along the eave
        cv.set(x, eave_y + 1, T('timber_cool', 3)); cv.set(x, eave_y + 2, T('timber_cool', 1))
    wall = rect(3, wall0, w - 6, wall1 - wall0)
    char = lambda bi, si: (('soot', 'soot_warm', 'soot_cool')[int(noise2(bi, si, 162) * 3)],
                           2 + (1 if noise2(bi, si, 163) > 0.8 else 0))
    boards(cv, 3, wall0, w - 6, wall1 - wall0, char, board=4, seed=164, nails=False, grain=0.0)
    ss.grain(cv, wall, 0.07, 165, shapes=rh.H_GRAIN, lit=lambda x, y: 0.8, swap=0.5, up=0.5, down=0.1)   # the char's silver sheen
    rh.overhang(cv, 3, w - 3, wall0, 4)
    posts = (3, 27, 41, 59, 73, w - 6)
    bays = [(7, 27, 'screen'), (31, 41, 'screen'), (44, 58, 'door'), (63, 73, 'screen'), (77, w - 6, 'screen')]
    for (bx0, bx1, kind) in bays:
        top, bot = wall0 + 5, wall1 - 1
        if kind == 'door':                         # the doorway, 32 tall, a split curtain over steam
            dy = wall1 - 32
            for (x, y) in rect(bx0, dy, bx1 - bx0, 32):
                cv.set(x, y, T('earth_cool', 0 if y > dy + 3 else 1))
            for (x, y) in rect(bx0, wall1 - 5, bx1 - bx0, 5):   # the wet stone floor inside, the lamps on it
                cv.set(x, y, T('basalt', 1 if (x + (y % 2) * 3) % 6 else 0))
            for (x, y) in ((bx0 + 3, wall1 - 3), (bx0 + 9, wall1 - 2)):
                cv.set(x, y, T('lamp', 2)); cv.set(x + 1, y, T('lamp', 2))
            for i, wx in enumerate((bx0 + 3, bx0 + 7, bx0 + 11)):   # wisps of steam rising past the curtain
                for yy in range(dy + 13, wall1 - 6):
                    xx = wx + round(1.3 * math.sin((yy + i * 5) / 3.0))
                    if bx0 <= xx < bx1 - 1 and (yy + i * 2) % 9 < 6:
                        cv.set(xx, yy, T('ash', 3 if yy < dy + 20 else 2)); cv.set(xx + 1, yy, T('ash', 2 if yy < dy + 20 else 1))
            for (x, y) in rect(bx0, dy, bx1 - bx0, 13):   # the curtain in three panels, the sign across them
                panel = (x - bx0) * 3 // (bx1 - bx0)
                f = (x - bx0) % ((bx1 - bx0) // 3 + 1)
                k = 4 if f == 0 else 3 if f < 3 else 2
                if (x - bx0) * 3 % (bx1 - bx0) < 3 and x > bx0 and y > dy + 3:
                    cv.set(x, y, T('earth_cool', 0)); continue   # the splits between panels
                cv.set(x, y, T(('dusk', 'dusk_warm', 'dusk')[panel], k if y < dy + 12 else k - 1))
            cx = (bx0 + bx1) // 2                    # the sign: three wavy lines of rising steam, in brass
            for i, sx in enumerate((cx - 3, cx, cx + 3)):
                for yy in range(dy + 3, dy + 9):
                    cv.set(sx + (1 if (yy + i) % 4 < 2 else 0), yy, T('brass', 4 if yy < dy + 5 else 3))
            for x in range(bx0 - 1, bx1 + 1):        # the lintel and the sill
                cv.set(x, dy - 1, T('timber_cool', 4)); cv.set(x, dy - 2, T('timber_cool', 2))
            continue
        frame(cv, bx0, top, bx1 - bx0, bot - top, 'timber_cool', 3, t=1)   # a paper screen lit from inside
        sx0, sy0, sw, sh = bx0 + 1, top + 1, bx1 - bx0 - 2, bot - top - 2
        for (x, y) in rect(sx0, sy0, sw, sh):     # brighter low in the middle, nearer the lamps
            fy = (y - sy0) / max(1, sh - 1)
            mid = abs(x + 0.5 - (sx0 + sw / 2)) < sw * 0.3
            cv.set(x, y, T('lamp', 2 if fy < 0.12 else 3 if fy < 0.45 else 4 if not (mid and fy > 0.7) else 5))
        if bx0 in (7, 77):                        # someone inside, a shadow thrown on the paper by the lamp
            fx = sx0 + (5 if bx0 == 7 else sw - 9)
            for (x, y) in rh.ellipse(fx + 2.5, sy0 + 7.5, 2.2, 2.4) | rect(fx, sy0 + 10, 5, sh - 10) | rect(fx + 5 if bx0 == 7 else fx - 2, sy0 + 12, 2, 6):
                if sx0 <= x < sx0 + sw and sy0 <= y < sy0 + sh:
                    cv.set(x, y, T('lamp', 1 if (x - fx) > 1 else 2))
        if bx0 == 63:                             # a shelf of tubs and a hanging dipper behind the paper
            cv.hline(sx0, sy0 + 13, sw, T('lamp', 1))
            for tx in range(sx0 + 1, sx0 + sw - 2, 4):
                for (x, y) in rect(tx, sy0 + 10, 3, 3):
                    cv.set(x, y, T('lamp', 2))
        for x in range(sx0, sx0 + sw, 4):           # the lattice: bars lit on top and west, the light glowing through
            for y in range(sy0, sy0 + sh):
                if x > sx0:
                    cv.set(x, y, T('timber_cool', 3 if (y - sy0) % 6 < 3 else 2))
        for y in range(sy0 + 5, sy0 + sh, 6):
            cv.hline(sx0, y, sw, T('timber_cool', 2))
        for (cx, cy) in ((sx0 + 1 + 4 * int(noise2(bx0, 1, 169) * (sw // 4)), sy0 + 6 + 6 * int(noise2(bx0, 2, 169) * 2)),):
            for (x, y) in rect(cx, cy, 3, 5):        # a pane of newer paper where one was mended, whiter
                if rh.tone_at(cv, x, y) and rh.tone_at(cv, x, y)[0] == 'lamp':
                    cv.set(x, y, T('plaster', 5 if y < cy + 2 else 4))
        gp.WINDOWS.append((cv, (sx0, sy0, sw, sh)))   # it glows at night too (zoneWindows)
    for px in posts:                               # posts from the plinth to the fascia, unbroken
        rh.cylinder(cv, px, eave_y + 3, 3, wall1 - eave_y - 3, 'timber_cool', 3)
    for (x, y) in rect(1, wall1, w - 2, deck_y - wall1):   # the basalt plinth in courses
        cv.set(x, y, T('basalt', 2))
    ss.courses(cv, 1, wall1, w - 2, deck_y - wall1, lambda ci, si: (('basalt', 'basalt_warm', 'basalt_cool')[si % 3], 3),
               course=3, lengths=(6, 11), seam=T('basalt', 1), seed=168)
    for x in range(0, w):                          # the deck: boards across, lit nosing, worn ends
        for y in range(deck_y, h - 1):
            cv.set(x, y, T(('timber', 'timber_warm')[(x // 7) % 2], 4 if y == deck_y else 3 if y < h - 2 else 2))
        if x % 7 == 0:
            for y in range(deck_y + 1, h - 1):
                cv.set(x, y, T('timber', 1))
        cv.set(x, h - 1, T('timber', 1))
    for lx in (16, 35, 67, 86):                    # paper lanterns on cords from the eave, glowing
        cv.set(lx, eave_y + 3, T('timber_cool', 1)); cv.set(lx, eave_y + 4, T('timber_cool', 1))
        for (x, y) in rh.ellipse(lx + 0.5, eave_y + 8.5, 2.6, 3.4):
            cv.set(x, y, T('lamp', 5 if x < lx and y < eave_y + 8 else 4 if x <= lx else 3))
        cv.hline(lx - 1, eave_y + 5, 3, T('clay', 2)); cv.hline(lx - 1, eave_y + 12, 3, T('clay', 2))
    for bx in (13, 21):                            # buckets on the deck, iron-hooped
        part(cv, bx, deck_y - 3, 6, 6, 'timber_warm', 3)
        cv.hline(bx, deck_y - 1, 6, T('iron', 2)); cv.set(bx + 1, deck_y - 1, T('iron', 4))
        cv.hline(bx + 1, deck_y - 3, 4, T('timber_warm', 1))
    for k in range(4):                             # a stack of folded towels
        y = deck_y + 1 - k * 2
        cv.hline(83, y, 12, T('plaster', 4 if k % 2 else 5)); cv.hline(83, y + 1, 12, T('plaster', 2 if k % 2 else 3))
        cv.set(83, y, T('berry', 3)); cv.set(83, y + 1, T('berry', 2))
    return rh.finish(cv)


def fireweed(tall: bool = True) -> Canvas:
    """Fireweed, 20 x 30 (or 16 x 22): the first plant back on burnt ground (asset ledger
    20 Oct: redrawn on the house ramps, no speckle). A clump of slim stems from one root,
    each with narrow leaves angled up in pairs of pixels and a flower spike at its top:
    open magenta flowers below, closed buds paler and smaller towards the tip, seed pods
    reddening under the flowers on the oldest stem. Lit on the west, the east side of each
    spike and leaf a tone down; leaves on the west of a stem catch the light."""
    w, h = (20, 30) if tall else (16, 22)
    cv = Canvas(w, h, pad=PAD)
    stems = [(4, 4, -0.10), (8, 1, -0.03), (12, 3, 0.05), (15, 7, 0.12)] if tall else \
            [(4, 3, -0.08), (8, 1, 0.0), (11, 5, 0.10)]
    root = (w // 2, h - 1)
    for i, (sx, top, lean) in enumerate(stems):
        def at(y):
            return int(round(sx + lean * (h - 1 - y) * 0.0 + (root[0] - sx) * ((y - top) / (h - 1 - top)) ** 2))
        spike = 7 if tall else 6
        for y in range(top + spike - 1, h):                     # the stem, reddish low down as fireweed is
            x = at(y)
            cv.set(x, y, T('cactus' if y < h - 6 else 'clay_cool', 3))
        for y in range(top + spike + 1, h - 3, 3):              # leaves angled up, each two pixels long
            x = at(y)
            if (y // 3 + i) % 2 == 0:                           # west of the stem, in the light
                cv.set(x - 1, y, T('leaf', 4)); cv.set(x - 2, y, T('leaf', 4))
            else:
                cv.set(x + 1, y, T('leaf', 3)); cv.set(x + 2, y, T('leaf', 3))
        x = at(top + spike)
        for y in range(top, top + spike):                        # the spike: two pixels wide, lit on its west
            u = (y - top) / spike
            r = (y - top) // 2                                   # flowers come in pairs of rows
            if u < 0.3:                                          # buds at the tip, pale
                cv.set(x, y, T('dusk_warm', 5))
                if y > top:
                    cv.set(x + 1, y, T('dusk_warm', 4))
            else:                                                # open flowers lower down
                cv.set(x, y, T('berry_cool', 5 if r % 2 else 4))
                cv.set(x + 1, y, T('berry_cool', 3))
                if (r + i) % 2 == 0:
                    cv.set(x - 1, y, T('dusk_warm', 5))          # a flower turned to the light
        if i == 1 and tall:                                      # seed pods reddening under the oldest stem's flowers
            cv.set(x + 1, top + spike, T('clay', 3)); cv.set(x + 1, top + spike + 1, T('clay', 3))
    for x in range(root[0] - 2, root[0] + 3):                    # the root's crown in the ash
        cv.set(x, h - 1, T('clay_cool', 3 if x > root[0] else 4))
    return rh.finish(cv)


def stone_lantern() -> Canvas:
    """A basalt lantern, 16 x 26: a hexagonal cap, a lit window, a column and a foot."""
    cv = Canvas(16, 26, pad=PAD)
    hex_top(cv, 8, 4, 6, lit=3)
    for y in range(7, 14):
        for x in range(3, 13):
            cv.set(x, y, BASALT[3] if x < 6 else BASALT[2] if x < 11 else BASALT[1])
    for (x, y) in rect_set(5, 8, 6, 4):
        cv.set(x, y, LANTERN[3] if y < 10 else LANTERN[2])
    for y in range(14, 22):
        for x in range(6, 10):
            cv.set(x, y, BASALT[3] if x < 7 else BASALT[2])
    for y in range(22, 25):
        cv.hline(3, y, 10, BASALT[3] if y == 22 else BASALT[1])
    return cv


def scree(big: bool = True, seed: int = 0) -> Canvas:
    """Fallen basalt boulders, 30 x 20 (or 20 x 14): three or four chunky blocks, each
    with a lit top plane, a mid front and a dark right flank (style.facet_stone), the
    small ones tucked in front of the big one, and grit spilled round their feet."""
    import style
    w, h = (30, 20) if big else (20, 14)
    cv = Canvas(w, h, pad=PAD)
    blocks = ((0.42, 0.42, 0.34, 0.5), (0.16, 0.7, 0.2, 0.3), (0.74, 0.74, 0.22, 0.3), (0.5, 0.86, 0.14, 0.18)) if big \
        else ((0.4, 0.45, 0.38, 0.55), (0.78, 0.76, 0.22, 0.3), (0.14, 0.8, 0.16, 0.24))
    for k, (fx, fy, fw, fh) in enumerate(blocks):
        cx, cy, rx, ry = fx * w, fy * h, fw * w, fh * h
        pts = set()
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                # a squarish rounded block, chipped at one corner
                d = max(abs(x - cx) / rx, abs(y - cy) / ry) * 0.6 + math.hypot((x - cx) / rx, (y - cy) / ry) * 0.4
                if d <= 1 and not (x - cx > rx * 0.5 and y - cy < -ry * 0.4 and noise2(k, seed, 254) > 0.4):
                    pts.add((x, y))
        style.facet_stone(cv, pts, BASALT, seed=seed * 7 + k)
    for i in range(5):  # grit round the feet
        gx = 2 + int(noise2(i, seed, 255) * (w - 4))
        cv.set(gx, h - 1, BASALT[2]); cv.set(gx + 1, h - 1, BASALT[1])
    return cv


def charred_snag(seed: int = 0) -> Canvas:
    """A tree the lava burned and left standing, 24 x 40: a split black trunk lit grey on
    its left flank, two bare limbs, bark checked into squares like charcoal, and one
    crack still glowing near the foot."""
    w, h = 24, 40
    cv = Canvas(w, h, pad=PAD)
    CHAR = ['#141014', '#241C1E', '#3A3032', '#5A4C4C', '#7E6E6A']
    cx = 12
    for y in range(8, h - 1):
        half = 3 + (1 if y > h - 9 else 0) + (1 if y > h - 4 else 0)
        for x in range(cx - half, cx + half + 1):
            k = (x - (cx - half)) / (2 * half)
            c = CHAR[3] if k < 0.3 else CHAR[2] if k < 0.7 else CHAR[1]
            if (y // 3 + x // 2) % 2 == 0 and 0.2 < k < 0.8 and y % 3 == 0:
                c = CHAR[0]  # charcoal checking
            cv.set(x, y, c)
        if y < 14:  # the split top
            cv.set(cx, y, CHAR[0])
    for (x0, y0, dx, n) in ((cx - 3, 20, -1, 9), (cx + 3, 15, 1, 8), (cx - 1, 9, -1, 5)):
        for t in range(n):  # bare limbs reaching up and out, 2 px thick, lit on top
            x, y = x0 + dx * t, y0 - int(t * 0.8)
            cv.set(x, y, CHAR[3] if dx < 0 else CHAR[2]); cv.set(x, y + 1, CHAR[1])
            if t < n - 3:
                cv.set(x, y + 2, CHAR[1])
        tx, ty = x0 + dx * (n - 1), y0 - int((n - 1) * 0.8)
        cv.set(tx + dx, ty - 1, CHAR[2]); cv.set(tx, ty - 2, CHAR[2])  # a forked twig at the end
    for y in range(h - 9, h - 4):  # the crack still glowing
        cv.set(cx + 1 + (y % 2), y, LAVA[3] if y == h - 7 else LAVA[2])
    cv.hline(cx - 6, h - 1, 13, ASH[1])
    return cv


def _ore_tub() -> Canvas:
    import western_props
    return western_props.ore_tub()


def _budget(items: dict) -> dict:
    """Every sprite held to the house colour budget (rd.limit_colours)."""
    return {k: rd.limit_colours(v) for k, v in items.items()}


def props() -> dict[str, Canvas]:
    return _budget({
        'basalt_columns': basalt_columns(5, 0), 'basalt_columns_low': basalt_columns(3, 7),
        'basalt_columns_b': basalt_columns(4, 13), 'basalt_steps': basalt_steps(), 'basalt_stack': basalt_stack(),
        'basalt_stumps': basalt_stumps(0), 'basalt_stumps_b': basalt_stumps(5), 'basalt_fallen': basalt_fallen(),
        'forge': forge(),
        'obsidian': obsidian_rock(True), 'obsidian_small': obsidian_rock(False), 'cooling_vent': cooling_vent(),
        'basalt_bridge': basalt_bridge(), 'ember_shrine': ember_shrine(),
        'bathhouse': bathhouse(), 'fireweed': fireweed(True), 'fireweed_small': fireweed(False),
        'stone_lantern': stone_lantern(), 'scree': scree(True, 0), 'scree_small': scree(False, 3),
        'scree_b': scree(True, 5), 'charred_snag': charred_snag(),
        'ore_tub': _ore_tub(),  # the mine line's tub, the same as Dust Gulch's
    })


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (60, 54, 52, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/caldera-props.png'))
    print('sheet', out.size)
