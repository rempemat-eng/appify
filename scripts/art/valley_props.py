"""More of the valley: props for the Riverside and the Woodland (world-atlas.md).

Same materials and canopy rules as the garden (garden_props.canopy, style.trunk),
so they read as the garden's neighbours. Run directly for a contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
import style  # noqa: E402
from materials import MATERIALS, WOOD, STONE, LEAF, RED, WTR, PLASTER, GOLD, NAP, SLATE, G, SNOW  # noqa: E402

ROPE, TAR = MATERIALS['rope'], MATERIALS['tar']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def willow() -> Canvas:
    """A weeping willow, 72 x 90: a broad crown whose fronds hang in long lit strands to
    the ground, the trunk glimpsed between them."""
    w, h = 76, 96
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2
    style.trunk(cv, int(cx - 5), 46, h, 10, WOOD)
    shape = gp.canopy(cv, [(cx - 14, 28, 16), (cx + 14, 28, 16), (cx, 21, 17)], LEAF, seed=41)
    for k in range(26):  # hanging fronds
        fx = int(cx - 32 + k * 2.5 + noise2(k, 0, 401) * 2)
        top = 24 + int(abs(fx - cx) * 0.2)
        length = 40 + int(noise2(k, 1, 401) * 26) - int(abs(fx - cx) * 0.3)
        for t in range(length):
            y = top + t
            if y >= h - 2:
                break
            x = fx + int(math.sin(t / 9 + k) * 1.2)
            lit = fx < cx and t < length * 0.7
            cv.set(x, y, LEAF[4] if lit and t % 5 == 0 else LEAF[3] if lit else LEAF[2] if t < length * 0.8 else LEAF[1])
    return cv


def reeds() -> Canvas:
    """A clump of reeds and bulrushes, 24 x 30, standing in the shallows."""
    cv = Canvas(30, 30, pad=PAD)
    for k in range(11):
        x = 5 + k * 2 + int(noise2(k, 0, 402) * 2)
        top = 4 + int(noise2(k, 1, 402) * 10)
        lean = (k - 5) * 0.04
        for y in range(top, 29):
            xx = int(x + (29 - y) * lean)
            cv.set(xx, y, '#9DB25A' if xx < 12 and y < 20 else '#6E8A3E' if y < 24 else '#4A5E2A')
        if k % 3 == 0:
            for y in range(top, top + 5):
                cv.set(int(x + (29 - y) * lean), y, '#6E4A2A' if y < top + 2 else '#4A3020')
    return cv


def water_mill(turn: float = 0.0) -> Canvas:
    """The watermill, 112 x 96 (its wheel `turn` radians round; six frames a 24th of a
    turn apart loop, since paddles and spokes repeat every quarter turn): a stone mill house with a thatched-look tarred roof seen
    from above, a timber upper floor, warm windows, and a big wooden wheel on its east
    wall, seen nearly edge-on because its axle runs into that wall, turning in the race."""
    w, h = 112, 96
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 38.5, 16, 40, 40, 86
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, 75, TAR, seed=77, moss=LEAF)
    gable = gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2), 7, 70,
                             apex_y, wall_top, WOOD, boards=True)
    detail.boards(cv, rect_set(7, wall_top, 64, 18), WOOD, 2, wall_top, board=4, seed=12)
    detail.stones(cv, 7, wall_top + 18, 64, wall_bottom - wall_top - 18, STONE, seed=31, course=5, moss=LEAF)
    for wx in (14, 50):
        gp.window(cv, wx, wall_top + 4, 12, 10, shutters=None, sill=False, warm=True)
    door = rect_set(30, wall_bottom - 22, 16, 22)
    for (x, y) in door:
        cv.set(x, y, WOOD[2] if (x - 30) % 4 else WOOD[1])
    detail.overhang_shadow(cv, 7, 71, wall_top, lambda x: 3, k=2, cap=1)
    _mill_wheel(cv, turn)
    return cv


def _mill_wheel(cv: Canvas, turn: float):
    """The undershot wheel on the mill's east wall, seen nearly edge-on (Claude E, after
    Claude A's review: its axle runs into the east wall, so in the three-quarter view the
    wheel's plane runs north-south and we look along it): two rims and the paddles between
    them make a tall narrow ellipse beside the wall, the near (south) half over the far,
    spokes and an iron hub on its east face, the axle running into the wall. Drawn in 3D and
    projected with the view's foreshortening and a small skew, each surface lit by its
    normal against the light from the upper left, so the turn reads as paddles rising over
    the top and coming down the near side."""
    X0, r, half = 80.0, 18.0, 3.5  # the wheel's mid-plane, radius, half its width along the axle
    sx0, sy0, sq, skew = 0.0, 62.0, 0.5, 0.42
    light = (-0.55, 0.35, 0.76)  # from the upper left (west), a little from the front, above
    toward = (0.0, 0.64, 0.77)  # toward the camera (south and up), for depth
    zbuf = {}

    def put(x, y, z, c):  # a 3D point (x east, y south, z up from the axle) onto the screen
        px, py = int(round(x + skew * y + sx0)), int(round(sy0 + y * sq - z))
        d = y * toward[1] + z * toward[2] + x * 0.001
        if d >= zbuf.get((px, py), -1e9):
            zbuf[(px, py)] = d
            cv.set(px, py, c)

    def tone(n, ramp=WOOD, lo=1):
        k = max(0.0, n[0] * light[0] + n[1] * light[1] + n[2] * light[2])
        return ramp[min(len(ramp) - 1, lo + int(k * (len(ramp) - lo) * 0.999))]

    steps = 220
    # the axle from the wall to the hub, an iron cylinder
    for i in range(0, 41):
        x = 71 + i * (X0 + half + 1 - 71) / 40
        for k in range(12):
            a = 2 * math.pi * k / 12
            n = (0.0, math.cos(a), math.sin(a))
            put(x, 1.6 * math.cos(a), 1.6 * math.sin(a), tone(n, MATERIALS['iron'], 0))
    # the two rims: rings 2 px deep, their outer faces (east and west) and the tread round them
    for side in (-1, 1):
        xf = X0 + side * half
        for i in range(steps * 2):
            a = 2 * math.pi * i / (steps * 2)
            ca, sa = math.cos(a), math.sin(a)
            for t in (r - 2, r - 1.5, r - 1, r - 0.5, r):
                put(xf, t * ca, t * sa, tone((float(side), 0.0, 0.0)) if side > 0 else WOOD[3])
            for dx in (0.0, 0.5, 1.0):
                put(xf - side * dx, r * ca, r * sa, tone((0.0, ca, sa), WOOD, 1))
    # the spokes, eight on each face, to the hub
    for side in (-1, 1):
        xf = X0 + side * (half - 0.5)
        for k in range(8):
            a = 2 * math.pi * k / 8 + 0.2 + turn
            for i in range(0, 60):
                t = 2 + i * (r - 4) / 60
                put(xf, t * math.cos(a), t * math.sin(a), WOOD[2] if side > 0 else WOOD[1])
    # the paddles: boards across between the rims, standing out past them
    for k in range(16):
        a = 2 * math.pi * k / 16 + turn
        ca, sa = math.cos(a), math.sin(a)
        n = (0.0, -sa, ca)  # the board's face, square to its radius
        if n[1] * toward[1] + n[2] * toward[2] < 0:
            n = (0.0, sa, -ca)
        for i in range(0, 17):
            x = X0 - half + i * (2 * half) / 16
            for j in range(0, 11):
                t = r - 2 + j * 0.5
                put(x, t * ca, t * sa, WOOD[1] if i in (0, 16) else tone(n, WOOD, 1) if j < 10 else WOOD[4])
    # the iron hub on the east face, and the strap round it
    for i in range(48):
        a = 2 * math.pi * i / 48
        for t in (0.5, 1.2, 2.0, 2.8):
            put(X0 + half + 0.6, t * math.cos(a), t * math.sin(a), '#727A8A' if t < 1.5 and math.sin(a) > 0 else '#3C404C')


def heron() -> Canvas:
    """A grey heron standing in the shallows, 20 x 30."""
    cv = Canvas(20, 30, pad=PAD)
    for (x, y) in oval(10, 16, 5, 4):
        cv.set(x, y, '#B8C0C8' if x < 10 else '#8A929E')
    for t in range(8):  # the S-curved neck
        cv.set(9 + int(math.sin(t / 2.5) * 2), 12 - t, '#D8DEE4')
    for (x, y) in disc(9, 4, 1.8):
        cv.set(x, y, '#E6EAEE')
    cv.hline(3, 4, 5, GOLD[3])
    cv.set(8, 3, '#2A2D36')
    for lx in (9, 11):
        cv.vline(lx, 20, 9, '#8A6A3E')
    return cv


def lily_pads() -> Canvas:
    """A raft of lily pads with one pale flower, 30 x 16 (a flat decal on the water)."""
    cv = Canvas(30, 16, pad=PAD)
    for (px, py, r) in ((7, 8, 5), (18, 6, 4.5), (24, 11, 3.5), (13, 12, 3)):
        for (x, y) in disc(px, py, r):
            cv.set(x, y, LEAF[3] if (x - px) + (y - py) < 0 else LEAF[2])
        cv.set(int(px + r * 0.5), int(py), LEAF[1])
    for (x, y) in disc(18, 5, 1.8):
        cv.set(x, y, '#F6E6F0' if x < 18 else '#E2B8CC')
    cv.set(18, 5, GOLD[4])
    return cv


def mossy_log() -> Canvas:
    """A fallen log, 56 x 20, its bark lit on top, moss along the back, a cut end with
    rings and a shelf fungus."""
    w, h = 56, 20
    cv = Canvas(w, h, pad=PAD)
    for x in range(6, w - 2):
        for y in range(5, 17):
            k = (y - 5) / 12
            cv.set(x, y, WOOD[3] if k < 0.25 else WOOD[2] if k < 0.6 else WOOD[1])
            if (x * 7 + y * 3) % 11 == 0:
                cv.set(x, y, WOOD[1])
        for y in range(4, 7):
            if noise2(x // 3, y, 403) > 0.35:
                cv.set(x, y, LEAF[3] if y == 4 else LEAF[2])
    for (x, y) in oval(6, 11, 4, 6):
        r = math.hypot(x - 6, (y - 11) * 0.7)
        cv.set(x, y, WOOD[4] if int(r) % 2 else WOOD[3])
    for (x, y) in oval(38, 16, 5, 2):
        cv.set(x, y, '#E8C890' if y < 16 else '#B8945A')
    return cv


def mushroom_ring() -> Canvas:
    """A fairy ring of red-capped toadstools, 40 x 20, white spots lit on the caps."""
    cv = Canvas(40, 20, pad=PAD)
    for k in range(9):
        a = 2 * math.pi * k / 9
        mx, my = int(20 + 16 * math.cos(a)), int(10 + 7 * math.sin(a))
        cv.vline(mx, my, 4, '#EEE6D0')
        for (x, y) in oval(mx, my, 2.6, 1.8):
            if y <= my:
                cv.set(x, y, RED[3] if x < mx else RED[2])
        cv.set(mx - 1, my - 1, '#FFFFFF')
    return cv


def hollow_tree() -> Canvas:
    """An old hollow oak, 70 x 92: a huge gnarled trunk with a dark hollow at its foot
    (something lives in there), roots spreading, a heavy crown of dark leaf masses."""
    w, h = 80, 100
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2
    style.trunk(cv, int(cx - 10), 46, h, 20, WOOD)
    for side in (-1, 1):  # roots
        for t in range(14):
            x = int(cx + side * (10 + t))
            cv.set(x, h - 3 + (t // 6), WOOD[2] if side < 0 else WOOD[1])
            cv.set(x, h - 4 + (t // 6), WOOD[3] if side < 0 else WOOD[2])
    gp.canopy(cv, [(cx - 16, 28, 18), (cx + 16, 30, 18), (cx, 21, 18), (cx, 38, 16)],
              ['#1C2E22', '#2C4630', '#3E6040', '#557A45', '#749A50'], seed=44)
    hollow = {(x, y) for (x, y) in oval(cx, h - 14, 6, 9)}
    for (x, y) in hollow:
        cv.set(x, y, '#1A120E' if y > h - 20 else '#2A1C16')
    for (x, y) in hollow:
        if (x - 1, y) not in hollow or (x, y - 1) not in hollow:
            cv.set(x, y, WOOD[4])
    cv.set(int(cx) - 1, h - 12, GOLD[4]); cv.set(int(cx) + 2, h - 12, GOLD[4])  # two eyes in the dark
    return cv


def fern() -> Canvas:
    """A fern, 26 x 18: arching fronds with paired leaflets, lit along their tops."""
    cv = Canvas(26, 18, pad=PAD)
    for k in range(7):
        a = math.pi * (0.1 + 0.8 * k / 6)
        for t in range(12):
            x = int(13 - math.cos(a) * t)
            y = int(16 - math.sin(a) * t * 0.9 + (t * t) * 0.03)
            cv.set(x, y, LEAF[3] if t % 2 else LEAF[2])
            if t % 2 == 0 and t > 2:
                cv.set(x, y - 1, LEAF[4])
    return cv


def forest_bench() -> Canvas:
    """A hidden bench made from a split log on two stumps, 40 x 20."""
    cv = Canvas(40, 20, pad=PAD)
    for sx in (6, 30):
        for (x, y) in rect_set(sx, 10, 7, 9):
            cv.set(x, y, WOOD[2] if x < sx + 3 else WOOD[1])
        for (x, y) in oval(sx + 3, 10, 3.5, 1.5):
            cv.set(x, y, WOOD[4])
    for x in range(2, 39):
        cv.set(x, 7, WOOD[4]); cv.set(x, 8, WOOD[3]); cv.set(x, 9, WOOD[2]); cv.set(x, 10, WOOD[1])
    return cv


def _cone_roof(cv, cx, apex_y, eave_y, rx, ry, panels, ramp_a, ramp_b, trim):
    """A conical roof (or parasol) in the three-quarter view: its top surface seen from a
    little above, panels radiating from the apex to an elliptical eave, lit on the left,
    a trim along the eave's front arc. Returns the eave's points (for shadows below)."""
    pts = []
    for y in range(apex_y, eave_y + ry + 1):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            # a point lies on the cone's visible surface if it is inside the silhouette
            # made by the apex and the eave ellipse
            ex = (x + 0.5 - cx) / rx
            if abs(ex) > 1:
                continue
            front = eave_y + ry * math.sqrt(1 - ex * ex)  # the eave's front edge at this x
            back = eave_y - ry * math.sqrt(1 - ex * ex)
            t = (y - apex_y) / max(1, back - apex_y) if y < back else 1
            if y < back and abs(x + 0.5 - cx) > rx * t:
                continue
            if y > front:
                continue
            a = math.atan2(y + 0.5 - apex_y, x + 0.5 - cx)  # the seams radiate from the apex
            seg = int(a / (2 * math.pi / panels) + 0.5) % 2
            lit = (x + 0.5 - cx) < -rx * 0.15
            shade = (x + 0.5 - cx) > rx * 0.45
            ramp = ramp_a if seg else ramp_b
            c = ramp[2] if lit else ramp[0] if shade else ramp[1]
            if y >= front - 1.5:
                c = trim[1] if lit else trim[0]  # the eave's trim
            cv.set(x, y, c)
            pts.append((x, y))
    return pts


def bandstand() -> Canvas:
    """The park's bandstand in the three-quarter view, 84 x 80 (Matt, 19 Oct, fault 17: "a
    cage of bars on a slab"): an octagonal stone plinth whose top is seen from above and
    whose front shows its courses, with steps at the front; a boarded floor; slender
    columns, the far ones seen through behind the floor, the near ones in front; a low
    railing open at the steps; and a conical roof seen from a little above in red and
    cream panels, lit on the left, a gilt eave and a finial."""
    w, h = 84, 80
    cv = Canvas(w, h, pad=PAD)
    cx = 42
    IRON = ['#2A2D36', '#3C404C', '#545A68', '#727A8A']
    py, prx, pry = h - 20, 36, 11  # the plinth's top: an ellipse (an octagon rounded at this size)
    eave_y, erx, ery = 30, 38, 10
    cols = [(cx + math.cos(k * math.pi / 4 + math.pi / 8) * (prx - 4), py + math.sin(k * math.pi / 4 + math.pi / 8) * (pry - 2)) for k in range(8)]
    # the far columns first, standing behind the floor
    for (x0, y0) in cols:
        if y0 >= py:
            continue
        top = eave_y + int((y0 - py) / pry * ery * 0.9)
        for y in range(top, int(y0) + 1):
            cv.set(int(x0), y, IRON[1]); cv.set(int(x0) + 1, y, IRON[0])
    # the plinth: its front face of coursed stone, then its top
    for x in range(cx - prx, cx + prx + 1):
        ex = (x + 0.5 - cx) / prx
        if abs(ex) >= 1:
            continue
        front = py + pry * math.sqrt(1 - ex * ex)
        k = (x - (cx - prx)) / (2 * prx)
        for d in range(8):
            y = int(front) + 1 + d
            c = STONE[3] if k < 0.3 else STONE[2] if k < 0.72 else STONE[1]
            if d in (3, 7) or (x + (0 if d < 4 else 4)) % 8 == 0:
                c = STONE[1] if c != STONE[1] else STONE[0]
            cv.set(x, y, c)
        back = py - pry * math.sqrt(1 - ex * ex)
        for y in range(int(back), int(front) + 1):
            edge = y >= front - 1.5 or y <= back + 0.5
            c = STONE[4] if edge and x < cx else STONE[3] if edge else (WOOD[3] if (y - int(back)) % 3 else WOOD[2])
            if not edge and x > cx + 18:
                c = WOOD[2] if (y - int(back)) % 3 else WOOD[1]
            cv.set(x, y, c)
    for k, (x0, wd) in enumerate(((cx - 9, 18), (cx - 11, 22))):  # the steps at the front
        y = h - 10 + k * 3
        cv.hline(x0, y, wd, STONE[4]); cv.hline(x0, y + 1, wd, STONE[3]); cv.hline(x0, y + 2, wd, STONE[1])
    # the railing round the near half, open at the steps
    for x in range(cx - prx + 4, cx + prx - 3):
        ex = (x + 0.5 - cx) / (prx - 3)
        if abs(ex) >= 1 or abs(x + 0.5 - cx) < 10:
            continue
        fy = py + (pry - 2) * math.sqrt(1 - ex * ex)
        cv.set(x, int(fy) - 6, IRON[3] if x < cx else IRON[2])
        if x % 4 == 0:
            for d in range(1, 6):
                cv.set(x, int(fy) - d, IRON[1])
    # the near columns, in front
    for (x0, y0) in cols:
        if y0 < py:
            continue
        top = eave_y + ery - 1
        for y in range(top, int(y0) + 1):
            cv.set(int(x0), y, IRON[3] if x0 < cx else IRON[2]); cv.set(int(x0) + 1, y, IRON[0])
    # the roof
    eave = _cone_roof(cv, cx, 4, eave_y, erx, ery, 14, (RED[2], RED[3], RED[4]),
                      (PLASTER[3], PLASTER[4], PLASTER[5]), (GOLD[1], GOLD[3]))
    for (x, y) in eave:  # its shadow on the columns just below the eave
        if (x, y + 1) not in eave and cv.get(x, y + 2)[3]:
            r, g, b, a = cv.get(x, y + 2)
            cv.set(x, y + 2, (int(r * 0.7), int(g * 0.7), int(b * 0.78), a))
    for (x, y) in disc(cx, 3, 2.2):
        cv.set(x, y, GOLD[4] if x < cx else GOLD[2])
    cv.vline(cx, 0, 2, GOLD[3])
    return cv


def ice_cream_cart() -> Canvas:
    """An ice-cream cart in the three-quarter view, 44 x 40 (Matt, 19 Oct, fault 16: "the
    parasol is a flat top-down ellipse on a side-view cart, with a lamp growing out of
    it"): a pastel box whose glass lid shows the tubs, a striped front, two wheels and a
    push handle; over it a striped parasol seen from a little above, on its pole down into
    the cart."""
    w, h = 44, 40
    cv = Canvas(w, h, pad=PAD)
    MINT = ['#5E9E98', '#94C8C4', '#BFE3E0', '#E2F4F2']
    PINK = ['#C07A94', '#E6A2BA', '#F6C6D8']
    WHITE = ['#C9C4BC', '#E6E2DC', '#FFFFFF']
    # the cart: its lid (top face) and its front
    for y in range(22, 34):
        for x in range(8, 38):
            if y < 26:
                c = '#D8EEF2' if (x + y) % 5 else '#F2FAFC'  # the glass lid
                if y == 22 or x in (8, 37):
                    c = MINT[3] if x < 30 else MINT[1]
            else:
                c = MINT[2] if x < 14 else MINT[1] if x < 34 else MINT[0]
                if y in (28, 29):
                    c = PINK[2] if x < 20 else PINK[1]  # the stripe
                if y == 33:
                    c = MINT[0]
            cv.set(x, y, c)
    for k, col in enumerate(('#F6E2A0', '#F6C6D8', '#8A5A3A', '#C6E6B0')):  # tubs under the glass
        cv.rect(11 + k * 6, 23, 4, 2, col)
    for wx in (13, 33):  # wheels
        for (x, y) in disc(wx, 35, 3.4):
            d = math.hypot(x + 0.5 - wx, y + 0.5 - 35)
            cv.set(x, y, '#2A2D36' if d > 2.4 else '#727A8A' if x < wx else '#545A68')
        cv.set(wx, 35, '#C9C4BC')
    for t in range(9):  # the push handle at the east end
        cv.set(38 + t // 3, 26 - t // 3, '#545A68')
    cv.hline(40, 23, 3, '#3C404C')
    for y in range(12, 22):  # the parasol's pole down into the cart
        cv.set(22, y, '#545A68'); cv.set(23, y, '#2A2D36')
    _cone_roof(cv, 22, 2, 11, 18, 5, 14, PINK, WHITE, (PINK[0], PINK[1]))
    return cv


def snowy_pine() -> Canvas:
    """The garden's pine with snow lying on each tier: every needle pixel open to the
    sky above it carries snow, lit on the left, blue in shade on the right."""
    cv = gp.pine()
    lum = lambda c: c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11  # noqa: E731
    snow = []
    for y in range(-cv.pad + 1, cv.h - 16):
        for x in range(-cv.pad, cv.w + cv.pad):
            c, above = cv.get(x, y), cv.get(x, y - 1)
            # a tier's top: open sky above, or the darker underside of the tier above
            if c[3] and (not above[3] or lum(c) - lum(above) > 34):
                snow.append((x, y))
    for (x, y) in snow:
        lit = x < cv.w / 2
        cv.set(x, y, SNOW[3] if lit else SNOW[1])
        if noise2(x, y, 404) > 0.35 and cv.get(x, y + 1)[3]:
            cv.set(x, y + 1, SNOW[2] if lit else SNOW[0])
    return cv


def frozen_tarn() -> Canvas:
    """A small frozen tarn, 70 x 32 (a flat decal): pale ice with cracks and a dusting
    of snow at its rim, a dark open patch where a spring keeps it from freezing."""
    w, h = 70, 32
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(35, 16, 33, 14):
        cv.set(x, y, SNOW[3] if not oval(35, 16, 30, 12).__contains__((x, y)) else '#BFD6E6' if (x + y) % 5 else '#D8E8F2')
    for k in range(5):
        a = k * 1.3
        for t in range(10):
            x, y = int(35 + math.cos(a) * t * 2.2), int(16 + math.sin(a) * t)
            if (x, y) in oval(35, 16, 29, 11):
                cv.set(x, y, '#8FAABF')
    for (x, y) in oval(48, 12, 5, 2.5):
        cv.set(x, y, WTR[1])
    return cv


def station_house() -> Canvas:
    """The valley's railway halt, 104 x 84: a stone building with a slate roof seen from
    above, a deep canopy over the platform side held on cast brackets, a round clock
    under the gable, a ticket window lit warm and a painted name board (no letters)."""
    w, h = 104, 84
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (w - 1) / 2, 16, 38, 38, 76
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, SLATE, seed=91, moss=LEAF)
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2), 7, w - 8,
                     apex_y, wall_top, PLASTER, boards=False)
    for (x, y) in disc(ridge, 29, 5):  # the clock
        cv.set(x, y, '#F7EEDC' if (x - ridge) + (y - 29) < 3 else '#E3D3B4')
    for (x, y) in disc(ridge, 29, 5):
        if (x - ridge) ** 2 + (y - 29) ** 2 > 16:
            cv.set(x, y, WOOD[1])
    cv.vline(int(ridge), 25, 4, '#2A2D36'); cv.hline(int(ridge), 29, 3, '#2A2D36')
    detail.stones(cv, 7, wall_top, w - 14, wall_bottom - wall_top, STONE, seed=33, course=5, moss=LEAF)
    for (x, y) in rect_set(18, wall_top + 6, w - 36, 6):  # the name board
        cv.set(x, y, '#3E6A4A' if y > wall_top + 6 else '#5E8A62')
    for k in range(9):
        cv.hline(24 + k * 7, wall_top + 8, 4, '#F4E6C8')
    gp.window(cv, 14, wall_top + 16, 14, 12, shutters=None, sill=True, warm=True)
    for (x, y) in rect_set(int(ridge) - 9, wall_bottom - 24, 18, 24):  # the door
        cv.set(x, y, '#3E6A4A' if (x - int(ridge)) % 6 else '#2E5038')
    for (x, y) in rect_set(w - 32, wall_top + 16, 16, 12):  # the ticket window
        cv.set(x, y, '#FFE7A6' if y < wall_top + 20 else '#F0B85A')
    cv.hline(w - 33, wall_top + 28, 18, WOOD[4])
    # the platform canopy along the front, on brackets
    for y in range(wall_top + 2, wall_top + 6):
        for x in range(0, w):
            cv.set(x, y, '#3E6A4A' if y < wall_top + 4 else '#2E5038')
    for x in range(0, w, 6):
        cv.set(x, wall_top + 6, '#3E6A4A')  # a fretted valance
    for bx in (4, w - 6):
        cv.vline(bx, wall_top + 6, 34, '#2A2D36')
    detail.overhang_shadow(cv, 7, w - 7, wall_top + 7, lambda x: 3, k=2, cap=1)
    return cv


def lookout_tower() -> Canvas:
    """The Headland's lookout (Matt's reference, 18 Oct: a stone tower with a timber
    top above the sea), 60 x 120: a square shaft of coursed stone with moss in its lower
    joints and a slit window, a jettied timber watch room on carved brackets with a
    window on the sea, a steep slate roof seen from above with a lantern finial, an oak
    door up two stone steps, and a lean-to log store against its lit side."""
    w, h = 60, 120
    cv = Canvas(w, h, pad=PAD)
    cx = (w - 1) / 2
    # the roof: steep slate planes falling from a short ridge, a lantern on top
    ridge, apex_y, eave_y = cx, 14, 34
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 3, w - 4, SLATE, seed=131, moss=LEAF, lit_base=2, shade_base=1)
    slope = (eave_y - apex_y) / (ridge - 3)
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * slope, 6, w - 7, apex_y, 35, WOOD)
    for (x, y) in disc(cx, 4, 3.2):  # the lantern finial, its glass catching the light
        cv.set(x, y, GOLD[3] if (x - cx) + (y - 4) < 0 else GOLD[2])
    cv.vline(int(cx), 7, 4, WOOD[1])
    # the timber watch room, jettied out over the shaft
    room_top, room_bottom = 35, 64
    gp.planks(cv, 4, room_top, w - 8, room_bottom - room_top, WOOD, step=5, vertical=True, base=2)
    for y in (room_top, room_bottom - 1):  # rails top and bottom
        cv.hline(4, y, w - 8, WOOD[4] if y == room_top else WOOD[0])
    for x in (4, w - 5):  # corner posts
        cv.vline(x, room_top, room_bottom - room_top, WOOD[3] if x == 4 else WOOD[1])
    gp.window(cv, int(cx) - 8, room_top + 7, 16, 13, shutters=None, sill=True)
    detail.overhang_shadow(cv, 5, w - 5, room_top, lambda x: 2, k=2, cap=1)
    # carved brackets under the jetty
    for bx in (10, w - 13):
        for k in range(5):
            cv.hline(bx + k // 2, room_bottom + k, 3 - k // 2, WOOD[1] if k else WOOD[3])
    # the stone shaft, its courses lit on the left, moss low down
    shaft_x0, shaft_x1, shaft_top, shaft_bottom = 12, w - 12, room_bottom, h - 8
    detail.stones(cv, shaft_x0, shaft_top, shaft_x1 - shaft_x0, shaft_bottom - shaft_top, STONE,
                  seed=37, course=6, moss=None)
    for y in range(shaft_top, shaft_bottom):  # the shaft's lit and shaded faces
        cv.set(shaft_x0, y, STONE[4]); cv.set(shaft_x1 - 1, y, STONE[0])
        if (y // 6) % 2 and y > shaft_bottom - 20:
            cv.set(shaft_x0 + 1 + (y % 5), y, LEAF[2])  # moss in the low joints
    detail.overhang_shadow(cv, shaft_x0, shaft_x1, shaft_top, lambda x: 3, k=2, cap=1)
    for y in range(shaft_top + 12, shaft_top + 22):  # a slit window
        cv.set(int(cx), y, '#2A2D36'); cv.set(int(cx) - 1, y, STONE[1])
    # the door: oak boards under a round head, up two steps
    dw, dh = 14, 20
    dx0, dy0 = int(cx) - dw // 2, shaft_bottom - dh
    for y in range(dy0, shaft_bottom):
        for x in range(dx0, dx0 + dw):
            top = y - dy0
            if top < 4 and abs(x + 0.5 - (dx0 + dw / 2)) > (dw / 2) * math.sqrt(max(0, 1 - ((4 - top) / 4) ** 2)):
                continue
            cv.set(x, y, WOOD[2] if (x - dx0) % 4 else WOOD[1])
    cv.set(dx0 + dw - 4, dy0 + 11, GOLD[3])  # the ring handle
    for k, (sx0, sw) in enumerate(((dx0 - 3, dw + 6), (dx0 - 6, dw + 12))):  # the steps
        y0 = shaft_bottom + k * 4
        for y in range(y0, y0 + 4):
            for x in range(sx0, sx0 + sw):
                cv.set(x, y, STONE[4] if y == y0 else STONE[2] if y < y0 + 3 else STONE[0])
    # a log store against the lit side of the shaft: cut ends stacked under a little
    # slanted roof, each end a pale ring in dark bark
    for k in range(5):  # the roof
        cv.hline(0, shaft_bottom - 22 + k, shaft_x0 + 1, WOOD[1] if k == 4 else WOOD[3] if k else WOOD[4])
    for y in range(shaft_bottom - 17, shaft_bottom):
        for x in range(1, shaft_x0):
            cv.set(x, y, WOOD[0])
    for row, n in enumerate((2, 3, 3)):
        for j in range(n):
            ox = 1 + j * 4 - (2 if n == 2 else 0) + (2 if n == 2 else 0)
            oy = shaft_bottom - 5 - row * 4 - (0)
            if n == 2:
                ox = 3 + j * 4
            for (x, y) in disc(ox + 1.5, oy + 1.5, 1.9):
                if 1 <= x < shaft_x0:
                    cv.set(x, y, WOOD[1])
            cv.set(ox + 1, oy + 1, WOOD[4]); cv.set(ox + 2, oy + 1, WOOD[3]); cv.set(ox + 1, oy + 2, WOOD[3])
    return cv


def semaphore() -> Canvas:
    """A railway semaphore signal, 26 x 60: a lattice post, a red arm with a white band
    raised to clear, a lamp, a little ladder."""
    cv = Canvas(26, 60, pad=PAD)
    for y in range(8, 58):
        cv.set(8, y, '#3C404C'); cv.set(9, y, '#727A8A')
        if y % 6 == 0:
            cv.hline(7, y, 4, '#545A68')
    for t in range(12):  # the arm, raised
        x, y = 10 + t, 12 - t // 3
        cv.set(x, y, RED[3]); cv.set(x, y + 1, RED[2])
        if t in (8, 9):
            cv.set(x, y, '#F4F0E6'); cv.set(x, y + 1, '#D8D4C8')
    for (x, y) in disc(9, 6, 2.2):
        cv.set(x, y, '#3C404C')
    cv.set(9, 6, GOLD[4])
    cv.rect(5, 56, 9, 4, STONE[2])
    return cv


BARN_RED = ['#4A1E1A', '#6E2C24', '#8E3A2E', '#B04E3A', '#C86A50']


def barn() -> Canvas:
    """A red barn, 100 x 88: a broad roof of weathered shingles seen from above, red
    vertical boards with white trim, big double doors crossed in white and a hayloft
    door with hay spilling from it."""
    w, h = 100, 88
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = (w - 1) / 2, 12, 40, 40, 82
    gp.topdown_roof(cv, ridge, apex_y, eave_y, 2, w - 3, SLATE, seed=93, moss=LEAF)
    gp.topdown_gable(cv, lambda x: apex_y + abs(x + 0.5 - ridge) * (eave_y - apex_y) / (ridge - 2), 7, w - 8,
                     apex_y, wall_top, BARN_RED, boards=True)
    for (x, y) in rect_set(int(ridge) - 7, 24, 14, 12):  # the hayloft door
        cv.set(x, y, '#2A1A14')
    for (x, y) in oval(ridge, 36, 9, 3):
        if y >= 34:
            cv.set(x, y, '#E2BC5E' if (x + y) % 2 else '#C99A3C')
    for y in range(wall_top, wall_bottom):
        for x in range(7, w - 7):
            c = BARN_RED[3] if (x // 4) % 2 else BARN_RED[2]
            if x % 4 == 0:
                c = BARN_RED[1]
            if x < 10:
                c = BARN_RED[4]
            cv.set(x, y, c)
    for x in range(7, w - 7):
        cv.set(x, wall_top, '#F2EEE6')
    dx0, dw = int(ridge) - 20, 40
    for y in range(wall_top + 10, wall_bottom):  # the double doors, crossed in white
        for x in range(dx0, dx0 + dw):
            c = BARN_RED[2] if x < ridge else BARN_RED[1]
            fx = x - dx0 if x < ridge else x - int(ridge)
            fy = y - wall_top - 10
            if x in (dx0, dx0 + dw - 1, int(ridge)) or y == wall_top + 10 or abs(fx * 32 / 20 - fy) < 1.5 or abs((20 - fx) * 32 / 20 - fy) < 1.5:
                c = '#F2EEE6'
            cv.set(x, y, c)
    for wx in (14, w - 26):
        gp.window(cv, wx, wall_top + 10, 12, 10, shutters=None, sill=False, warm=True)
    detail.overhang_shadow(cv, 7, w - 7, wall_top + 1, lambda x: 3, k=2, cap=1)
    detail.stones(cv, 5, wall_bottom, w - 10, 5, STONE, seed=35, course=3)
    return cv


def scarecrow() -> Canvas:
    """A scarecrow, 32 x 46: a straw hat, a sack face with a stitched smile, a patched
    coat on a crossbar, a crow perched on one arm."""
    w, h = 32, 46
    cv = Canvas(w, h, pad=PAD)
    cv.vline(15, 14, 30, WOOD[2]); cv.vline(16, 14, 30, WOOD[1])
    for x in range(2, 30):
        cv.set(x, 18, WOOD[3]); cv.set(x, 19, WOOD[1])
    for y in range(17, 32):  # the coat
        for x in range(9, 23):
            c = '#4A6A8A' if x < 13 else '#3A5470' if x < 20 else '#2C4058'
            if 14 <= x < 18 and 22 <= y < 26:
                c = RED[3]  # a patch
            cv.set(x, y, c)
    for x in range(3, 9):
        cv.set(x, 20, '#E2BC5E'); cv.set(x + 21, 20, '#E2BC5E')  # straw from the cuffs
    for (x, y) in disc(16, 11, 5):  # the sack head
        cv.set(x, y, '#D8C4A0' if x + y < 26 else '#B89A74')
    cv.set(14, 10, '#2A1E18'); cv.set(18, 10, '#2A1E18')
    cv.hline(14, 13, 5, '#5A3A24')
    for x in range(8, 25):  # the hat
        cv.set(x, 6, '#E2BC5E' if x < 16 else '#C99A3C')
    for y in range(1, 6):
        cv.hline(12, y, 9, '#F2D27A' if y < 3 else '#E2BC5E')
    for (x, y) in oval(27, 15, 3, 2):  # the crow
        cv.set(x, y, '#1E1C22')
    cv.set(29, 14, '#E8A23A'); cv.set(26, 14, '#3A3840')
    return cv


def windmill(turn: float = 0.0) -> Canvas:
    """A tower windmill in the valley's three-quarter view, 64 x 104 (Matt, 19 Oct, fault
    05: "flat tower, thin sails that do not meet the cap, no base or ground contact"): a
    round fieldstone footing, its top seen from above; a whitewashed tower over a stone
    base course, rounded so it is lit on the left and turns into shade on the right; a
    wooden stage round its waist; a door with a step and two small windows; a shingled cap
    seen from a little above with a finial; and four lattice sails with canvas on stocks
    that meet at the hub on the cap's front, `turn` radians round (three frames a sixth of
    a turn apart loop)."""
    w, h = 64, 104
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    CLOTH = ('#F2EEE6', '#DCD4C4')
    # the footing: a low round plinth of fieldstone, its top an ellipse, its front a band
    fy, frx, fry = h - 9, 21, 5
    for x in range(cx - frx, cx + frx + 1):
        dx = (x + 0.5 - cx) / frx
        if abs(dx) >= 1:
            continue
        e = fry * math.sqrt(1 - dx * dx)
        k = (x - (cx - frx)) / (2 * frx)
        for y in range(int(fy - e), int(fy + e) + 1):
            cv.set(x, y, STONE[4] if k < 0.3 and y < fy - e + 2 else STONE[3] if k < 0.6 else STONE[2])
        for d in range(5):
            y = int(fy + e) + 1 + d
            c = STONE[3] if k < 0.3 else STONE[2] if k < 0.72 else STONE[1]
            if d == 2 or (x + (0 if d < 2 else 3)) % 6 == 0:
                c = STONE[1] if c != STONE[1] else STONE[0]  # coursing and joints
            cv.set(x, y, c)
    # the tower: tapering, rounded, a stone base course under whitewash
    top, bottom = 40, fy + 1

    def radius(y):
        return 9 + (y - top) / (bottom - top) * 6

    stage = 70
    for y in range(top, bottom):
        r = radius(y)
        for x in range(int(cx - r), int(cx + r) + 1):
            k = (x + 0.5 - (cx - r)) / (2 * r)
            if y > bottom - 13:  # the base course
                c = STONE[3] if k < 0.25 else STONE[2] if k < 0.62 else STONE[1]
                if (bottom - y) % 4 == 0 or (x + 3 * ((bottom - y) // 4 % 2)) % 6 == 0:
                    c = STONE[1] if c != STONE[1] else STONE[0]
            else:
                c = PLASTER[4] if k < 0.18 else PLASTER[3] if k < 0.5 else PLASTER[2] if k < 0.8 else PLASTER[1]
                if k < 0.5 and noise2(x, y // 3, 941) > 0.93:
                    c = PLASTER[2]  # a weathered streak
            if stage + 2 <= y <= stage + 4:
                c = detail.tone(PLASTER, PLASTER.index(c) - 1) if c in PLASTER else c  # the stage's shadow
            cv.set(x, y, c)
    for (wy, wx) in ((48, cx - 4), (59, cx + 1)):  # two small windows above the stage, deep set
        for y in range(wy, wy + 7):
            for x in range(wx, wx + 5):
                cv.set(x, y, '#2E3A48' if (x, y) != (wx + 1, wy + 1) else '#7E96AE')
        cv.hline(wx - 1, wy - 1, 7, WOOD[3]); cv.hline(wx - 1, wy + 7, 7, WOOD[4])
    door_top = bottom - 15
    for y in range(door_top, bottom - 1):  # the door, arched, in a stone surround
        for x in range(cx - 4, cx + 4):
            if y < door_top + 3 and abs(x + 0.5 - cx) > 4 - (y - door_top + 1):
                continue
            c = WOOD[3] if x < cx - 1 else WOOD[2] if x < cx + 2 else WOOD[1]
            if (x - cx) % 3 == 0:
                c = WOOD[1]
            cv.set(x, y, c)
    cv.set(cx + 2, door_top + 8, GOLD[4])
    for x in range(cx - 6, cx + 6):  # the step on the footing
        cv.set(x, bottom - 1, STONE[4] if x < cx else STONE[3]); cv.set(x, bottom, STONE[2])
    # the stage round the tower's waist: its deck seen from above, a rail on the front
    srx, sry = radius(stage) + 6, 3
    for x in range(int(cx - srx), int(cx + srx) + 1):
        dx = (x + 0.5 - cx) / srx
        if abs(dx) >= 1:
            continue
        e = sry * math.sqrt(1 - dx * dx)
        for y in range(int(stage - e), int(stage + e) + 1):
            if abs(x + 0.5 - cx) < radius(y) - 1 and y < stage:
                continue  # the tower stands through the deck's back half
            cv.set(x, y, WOOD[4] if x < cx - 6 else WOOD[3])
        fy2 = int(stage + e) + 1
        cv.set(x, fy2, WOOD[2]); cv.set(x, fy2 + 1, WOOD[1])
        if x % 4 == 0:  # the rail's posts
            for d in range(1, 5):
                cv.set(x, int(stage + e) - d, WOOD[2])
        cv.set(x, int(stage + e) - 4, WOOD[3])
    # the cap: a shingled dome seen from a little above, its eave and a finial
    cap_top, cap_eave, crx = 24, 42, 13
    pts = set()
    for y in range(cap_top, cap_eave + 1):
        hw = crx * math.sqrt(max(0.0, 1 - ((cap_eave - y) / (cap_eave - cap_top)) ** 2))
        for x in range(int(cx - hw), int(cx + hw) + 1):
            pts.add((x, y))
    detail.shingles(cv, pts, WOOD, 2, cap_top, course=3, width=5, seed=943,
                    offset=lambda x, y: 1 if x < cx - 3 else -1 if x > cx + 4 else 0)
    for x in range(cx - crx - 1, cx + crx + 2):
        cv.set(x, cap_eave + 1, WOOD[1])
        if abs(x - cx) <= radius(top):
            cv.set(x, cap_eave + 2, PLASTER[1])  # the eave's shadow on the tower
    cv.set(cx, cap_top - 2, GOLD[4]); cv.set(cx, cap_top - 1, GOLD[2]); cv.set(cx - 1, cap_top - 1, GOLD[3])
    # the sails: stocks from the hub on the cap's front, lattice frames with canvas
    hx, hy = cx, 36
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2 + turn
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux  # the sail's trailing side
        for t10 in range(0, 330):
            t = t10 / 10
            x, y = hx + ux * t, hy + uy * t
            if t >= 7:
                for side10 in range(10, 75, 4):
                    side = side10 / 10
                    sx, sy = x + px * side, y + py * side
                    frame = side10 >= 70 or side10 <= 14 or t > 32.4 or t < 7.3 or int(t) % 4 == 0
                    cv.set(int(sx), int(sy), WOOD[3] if frame else CLOTH[0] if side < 4.5 else CLOTH[1])
            cv.set(int(x), int(y), WOOD[2])
            cv.set(int(x - px), int(y - py), WOOD[3] if t > 2 else WOOD[2])
    for (x, y) in disc(hx, hy, 3):
        cv.set(x, y, WOOD[1])
    cv.set(hx - 1, hy - 1, WOOD[3])
    return cv


def sheep(facing: int = 1) -> Canvas:
    """A grazing sheep, 26 x 20: a woolly cloud body lit on the upper left, a dark face
    lowered to the grass, thin dark legs."""
    w, h = 26, 20
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(12, 9, 10, 6) | oval(8, 7, 5, 4) | oval(16, 7, 5, 4):
        k = (x - 2) / 20 + (y - 2) / 12
        c = '#FFFFFF' if k < 0.6 else '#EAE6DC' if k < 1.0 else '#C8C2B4'
        if (x * 3 + y * 5) % 7 == 0:
            c = '#D8D2C4' if k < 1 else '#B0A898'  # curls
        cv.set(x if facing > 0 else w - 1 - x, y, c)
    head = oval(22, 12, 3, 3.5)
    for (x, y) in head:
        cv.set(x if facing > 0 else w - 1 - x, y, '#3A3236' if x < 23 else '#2A2226')
    for lx in (6, 9, 15, 18):
        for y in range(14, 19):
            cv.set(lx if facing > 0 else w - 1 - lx, y, '#2A2226')
    return cv


def beehive() -> Canvas:
    """A white wooden beehive on a stand, 22 x 30: stacked boxes, a little roof, bees."""
    w, h = 22, 30
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 8):  # roof
        for x in range(1, w - 1):
            cv.set(x, y, SLATE[3] if x < w // 2 else SLATE[2])
    for k in range(2):
        for y in range(8 + k * 8, 16 + k * 8):
            for x in range(3, w - 3):
                cv.set(x, y, '#F2EEE6' if x < 6 else '#E2DCD0' if x < w - 6 else '#C8C2B4')
        cv.hline(3, 8 + k * 8, w - 6, '#B0A898')
    cv.hline(8, 22, 6, '#3A3236')  # the entrance
    for x in (5, w - 6):
        cv.vline(x, 24, 5, WOOD[2])
    for (bx, by) in ((2, 2), (17, 1), (12, 0)):
        cv.set(bx, by, GOLD[4]); cv.set(bx + 1, by, '#2A2226')
    return cv

MEGALITH = ['#3A3446', '#585068', '#787088', '#9A92A8', '#C2BACC']  # grey-purple standing stone


def standing_stone(seed: int = 0, tall: bool = True) -> Canvas:
    """An old standing stone, 18 x 30 (or 16 x 22): a weathered grey-purple slab, its top
    rounded and a little skewed, lit on its upper-left plane, shaded on its right flank,
    with a moss cap that drips down its face (style.facet_stone, as in the references)."""
    w, h = (18, 30) if tall else (16, 22)
    cv = Canvas(w, h, pad=PAD)
    lean = (noise2(seed, 0, 431) - 0.5) * 0.25
    pts = set()
    for y in range(2, h - 1):
        f = (y - 2) / (h - 3)
        half = (w / 2 - 3) * (0.5 + 0.5 * min(1.0, f * 1.4)) + (1 if y > h - 4 else 0)
        cx = w / 2 + lean * (h - y)
        for x in range(int(cx - half), int(cx + half) + 1):
            if f < 0.18 and ((x - cx) / half) ** 2 + ((0.18 - f) / 0.18) ** 2 > 1:
                continue  # the rounded top
            pts.add((x, y))
    style.facet_stone(cv, pts, MEGALITH, moss=LEAF, seed=seed + 40)
    cv.hline(int(w / 2 - 5), h - 1, 10, MATERIALS['leaf'][1])  # grass at its foot
    return cv


def stump() -> Canvas:
    """An old tree stump, 22 x 18: a lit ring-cut top, bark sides shaded right, roots
    reaching into the moss, and a cluster of small brown mushrooms."""
    w, h = 22, 18
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, h - 2):
        for x in range(4, 18):
            k = (x - 4) / 14
            cv.set(x, y, WOOD[3] if k < 0.3 else WOOD[2] if k < 0.75 else WOOD[1])
            if (x * 3 + y) % 7 == 0:
                cv.set(x, y, WOOD[1])  # bark furrows
    for (x, y) in oval(11, 6, 7, 3):
        d = math.hypot((x - 11) / 7, (y - 6) / 3)
        cv.set(x, y, WOOD[4] if d > 0.8 else '#E2C08A' if int(d * 4) % 2 else '#C8A070')  # rings
    for (x0, dx) in ((4, -1), (17, 1)):
        for t in range(4):
            cv.set(x0 + dx * t, h - 3 + (t > 1), WOOD[2] if dx < 0 else WOOD[1])  # roots
    for (mx, my) in ((16, 13), (18, 15), (14, 15)):
        cv.set(mx, my, '#B8794A'); cv.set(mx + 1, my, '#8E5A36'); cv.set(mx, my + 1, '#E8DCC8')
    return cv


def woodpile() -> Canvas:
    """Split logs stacked against the cabin, 30 x 20, their cut ends lit, a cap of snow."""
    w, h = 30, 20
    cv = Canvas(w, h, pad=PAD)
    for row in range(3):
        for k in range(5 - row):
            cx, cy = 5 + k * 5 + row * 2.5, h - 5 - row * 4.4
            for (x, y) in disc(cx, cy, 2.6):
                d = math.hypot(x - cx, y - cy)
                cv.set(x, y, WOOD[1] if d > 2.1 else '#E2C08A' if d < 1 else '#C8A070')
    for x in range(8, 24):  # snow on top
        cv.set(x, h - 18 + (1 if x in (8, 23) else 0), SNOW[3]); cv.set(x, h - 17, SNOW[2])
    return cv


def sled() -> Canvas:
    """A wooden sled with red runners leaning in the snow, 28 x 14."""
    w, h = 28, 14
    cv = Canvas(w, h, pad=PAD)
    for y in range(3, 8):
        for x in range(4, 24):
            cv.set(x, y, WOOD[4] if y == 3 else WOOD[3] if (x - 4) % 5 else WOOD[1])
    for x in range(3, 25):
        cv.set(x, 10, RED[3] if x < 14 else RED[2])
    cv.set(2, 9, RED[3]); cv.set(2, 8, RED[3]); cv.set(25, 9, RED[2])
    for px in (7, 20):
        cv.vline(px, 8, 2, RED[2])
    return cv


def snowman() -> Canvas:
    """A small snowman, 20 x 30: two snowballs shaded blue on the lower right, coal eyes,
    a carrot nose, a red scarf and twig arms."""
    w, h = 20, 30
    cv = Canvas(w, h, pad=PAD)
    for (cx, cy, r) in ((10, 21, 7), (10, 10, 5)):
        for (x, y) in disc(cx, cy, r):
            k = (x - cx) + (y - cy)
            cv.set(x, y, SNOW[3] if k < -r * 0.4 else SNOW[2] if k < r * 0.5 else SNOW[1])
    cv.set(8, 9, '#1E1917'); cv.set(11, 9, '#1E1917')
    cv.hline(10, 11, 3, '#E8803A')
    cv.hline(5, 15, 10, RED[3]); cv.vline(13, 15, 4, RED[2])
    for t in range(5):
        cv.set(4 - t, 17 - t // 2, WOOD[2]); cv.set(16 + t, 17 - t // 2, WOOD[1])
    return cv


def marmot_rock() -> Canvas:
    """A sun-warmed boulder with a marmot sitting up on it, 28 x 26."""
    import style
    w, h = 28, 26
    cv = Canvas(w, h, pad=PAD)
    pts = {(x, y) for (x, y) in oval(14, 18, 12, 6)}
    style.facet_stone(cv, pts, STONE, moss=LEAF, seed=81)
    FUR = ['#4A3424', '#6E4E34', '#94704A', '#B8946A']
    for (x, y) in oval(13, 9, 5, 5):  # the marmot's round body, sitting up
        cv.set(x, y, FUR[3] if x < 12 else FUR[2] if x < 16 else FUR[1])
    for (x, y) in oval(13, 10, 2.4, 3):
        cv.set(x, y, '#C8A882')  # its pale belly
    for (x, y) in disc(13, 3, 3.2):
        cv.set(x, y, FUR[3] if x < 13 else FUR[2])
    cv.set(11, 3, '#1E1917'); cv.set(15, 3, '#1E1917'); cv.set(13, 5, FUR[0])
    cv.set(10, 0, FUR[2]); cv.set(16, 0, FUR[1])  # little ears
    cv.set(11, 8, FUR[1]); cv.set(15, 8, FUR[1])  # paws held up
    return cv


def cotton_grass() -> Canvas:
    """A tuft of cotton grass from a wet alpine margin, 12 x 14: thin stems with white tufts."""
    cv = Canvas(12, 14, pad=PAD)
    for k, (x, top) in enumerate(((3, 2), (6, 0), (9, 3), (5, 5))):
        cv.vline(x, top + 2, 12 - top, LEAF[3] if k % 2 else LEAF[2])
        cv.set(x, top, '#FFFFFF'); cv.set(x + 1, top + 1, '#E2E9F0'); cv.set(x - 1, top + 1, '#FFFFFF'); cv.set(x, top + 1, '#F7FAFC')
    return cv



# ---- the farm (B6, Claude E's list 6 and 7): hay, pumpkins and dry stone walls --------
# Each sits on its own base, its weight pressing a darker last row into the grass; the
# zone throws the cast shadow from its silhouette (detail.silhouette_shadow), so none is
# painted here, and nothing assumes the time of day.
HAY = ['#5E4418', '#8A6420', '#A87E2C', '#C99A3C', '#E2BC5E', '#F2D27A', '#FBE6A8']
PUMPKIN = ['#6A2E12', '#A44C1A', '#D46E26', '#EE9840', '#FFC97A']
STALK = ['#3E3A1C', '#5E5A2A', '#807A3A']
LICHEN = '#B9B77A'


def _hay(i: int) -> str:
    return HAY[max(0, min(len(HAY) - 1, i))]


def round_bale() -> Canvas:
    """A round bale lying with its end toward the viewer, 20 x 25: the rolled end a spiral
    of straw winding in to a dark core, its rim lit on the upper left and turned from the
    light at the lower right; above it the top of the roll running back, the brightest
    thing on it (it faces the sky), streaked along its length and cinched by two twines;
    flattened where its weight sits."""
    w, h = 20, 25
    cv = Canvas(w, h, pad=PAD)
    r, depth = 8.6, 7
    cx, cy = 9.6, h - r + 0.4
    bottom = h - 1
    face = {(x, y) for (x, y) in disc(cx, cy, r) if y <= bottom}
    roll = set()
    for t in range(depth + 1):
        roll |= {(x, y) for (x, y) in disc(cx, cy - t, r) if y <= bottom}
    for (x, y) in roll - face:  # the top of the roll, running back
        nx = max(-1.0, min(1.0, (x + 0.5 - cx) / r))
        lam = 0.8 * math.sqrt(1 - nx * nx) - 0.6 * nx
        i = 6 if lam > 1.0 else 5 if lam > 0.6 else 4 if lam > 0.15 else 3
        n = noise2(x, y // 3, 611)
        i += -1 if n > 0.72 else 0
        cv.set(x, y, _hay(i))
    for t in (2.5, 5.2):  # two twines round the roll
        for x in range(int(cx - r), int(cx + r) + 1):
            nx = (x + 0.5 - cx) / r
            if abs(nx) >= 1:
                continue
            y = int(round(cy - t - r * math.sqrt(1 - nx * nx)))
            if (x, y) in roll and (x, y) not in face:
                cv.set(x, y, _hay(2 if nx > 0.3 else 3))
    for (x, y) in face:  # the rolled end
        dx, dy = x + 0.5 - cx, y + 0.5 - cy
        d, a = math.hypot(dx, dy), math.atan2(dy, dx)
        f = (-dx * 0.6 - dy * 0.8) / r
        i = 4 if f > 0.5 else 3 if f > -0.1 else 2 if f > -0.55 else 1
        if (d + (a + math.pi) / (2 * math.pi) * 2.3) % 2.3 < 0.85 and d > 1.4:
            i -= 1  # the groove between one turn of the roll and the next
        elif noise2(x, y, 612) > 0.92 and f > 0:
            i += 1  # cut straw ends catching the light
        if d < 1.5:
            i = 1
        if (x, y - 1) not in face and (x, y - 1) in roll:
            i = 2  # the crease where the end turns into the roll, loose straw shading it
        elif any((x + ex, y + ey) not in face for ex, ey in ((1, 0), (-1, 0), (0, 1))):
            i = 4 if dx + dy < -3 else 1 if dx + dy > 1 else i
        cv.set(x, y, _hay(i))
    for x in range(w):  # its weight pressed onto the ground
        if cv.get(x, bottom)[3]:
            cv.set(x, bottom, _hay(1 if x < cx + 3 else 0))
    return cv


def round_bale_side() -> Canvas:
    """A round bale lying across the view, 22 x 20: the curve of the roll seen side on, its
    top facing the sky and lit, rounding over a soft ridge of light into its front in half
    light and its underside in shade; straw running along it, two twines round it, the
    ends' edges rounded only where the roll's curve meets them, flat where it sits."""
    w, h = 22, 20
    cv = Canvas(w, h, pad=PAD)
    x0, x1, top, bottom = 1, 20, 1, h - 1
    rows = bottom - top + 1
    for y in range(top, bottom + 1):
        s = (y - top) / (rows - 1)
        for x in range(x0, x1 + 1):
            cut = 2 if s < 0.06 else 1 if s < 0.16 or s > 0.9 else 0
            if x < x0 + cut or x > x1 - cut:
                continue
            # the top (s < 0.4) faces the sky, the ridge of light where it rounds over,
            # then the front and the underside
            i = 5 if s < 0.38 else 6 if s < 0.47 else 4 if s < 0.62 else 3 if s < 0.8 else 2 if s < 0.92 else 1
            if x >= x1 - 1:
                i -= 1  # the far end's rounded edge, turned from the light
            elif x <= x0 and 0.1 < s < 0.8:
                i += 1  # the near end's edge catching it
            n = noise2(x // 3, y, 613)
            i += -1 if n > 0.74 else 0
            cv.set(x, y, _hay(i))
    for tx in (6, 15):  # the twines, round the roll
        for y in range(top + 1, bottom):
            if cv.get(tx, y)[3]:
                s = (y - top) / (rows - 1)
                cv.set(tx, y, _hay(3 if s < 0.47 else 2 if s < 0.8 else 1))
    for x in range(w):
        if cv.get(x, bottom)[3]:
            cv.set(x, bottom, _hay(0))
    return cv


def haystack() -> Canvas:
    """A haystack, 34 x 30: a rick of loose hay built round a stake, swelling out to its
    eaves and tucked in at its foot, its straw raked down its slopes and lit on the upper
    left; a thatched cap tied over the top with two ropes, a stone weight hanging from each
    rope's end, and the stake standing out of the cap."""
    w, h = 34, 30
    cv = Canvas(w, h, pad=PAD)
    cx, tip, bottom = 16.5, 3, h - 1

    def half(y):
        t = (y - tip) / (bottom - tip)
        if t < 0.72:
            return 15.6 * math.sqrt(max(0.0, 1 - (1 - t / 0.72) ** 2)) ** 0.9
        return 15.6 - (t - 0.72) / 0.28 * 1.6

    def eave(x):
        return tip + 10 + int(math.sin(x / 2.3) * 0.8 + noise2(x, 0, 621) * 1.2)
    rick = set()
    for y in range(tip, bottom + 1):
        hw = half(y) + (noise2(y, 1, 622) - 0.5) * 0.9
        for x in range(int(cx - hw), int(math.ceil(cx + hw))):
            rick.add((x, y))
    for (x, y) in rick:
        t = (y - tip) / (bottom - tip)
        nx = (x + 0.5 - cx) / max(1.0, half(y))
        capped = y < eave(x)
        lam = -0.65 * nx + (0.9 if capped else 0.55) * (1 - t) - 0.15
        if capped:  # the thatch: combed straw running down from the top, a deeper gold
            i = 4 if lam > 0.45 else 3 if lam > 0.05 else 2 if lam > -0.4 else 1
            sx = int(x - (x - cx) * 0.4)
            if noise2(sx, y // 3, 623) > 0.7:
                i -= 1
        else:  # the hay below, raked down the slopes in strands
            i = 5 if lam > 0.5 else 4 if lam > 0.15 else 3 if lam > -0.25 else 2
            sx = int(x - (x - cx) * t * 0.3)
            n = noise2(sx, y // 3, 624)
            i += -1 if n > 0.72 else 1 if n < 0.06 and lam > 0 else 0
            if y == eave(x):
                i = 1  # the cap's overhang shades the hay under it
        cv.set(x, y, _hay(i))
    for y in range(bottom - 1, bottom + 1):  # its foot, pressed and pulled at
        for x in range(w):
            if cv.get(x, y)[3]:
                cv.set(x, y, _hay(1 if y == bottom else 2) if noise2(x, y, 625) < 0.75 else _hay(3))
    for (ex, side) in ((cx - 10, -1), (cx + 9, 1)):  # the ropes over the cap, and their weights
        ey = eave(int(ex))
        for k in range(14):
            t = k / 13
            x = int(round(cx + (ex - cx) * t))
            y = int(round(tip + 1 + (ey - tip - 1) * t + math.sin(t * math.pi) * -1.2))
            cv.set(x, y, ROPE[2] if side < 0 else ROPE[1])
        for y in range(ey, ey + 5):
            cv.set(int(ex), y, ROPE[1])
        for (x, y) in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 1)):  # a stone tied on, hanging
            cv.set(int(ex) + x, ey + 5 + y, STONE[3] if (x, y) == (0, 0) else STONE[2] if y == 0 or x < 0 else STONE[1])
    cv.vline(int(cx), 0, tip + 1, WOOD[2]); cv.vline(int(cx) + 1, 0, tip + 1, WOOD[1])  # the stake
    cv.set(int(cx), 0, WOOD[3])
    return cv


def _pumpkin(cv: Canvas, cx: float, base: int, w: float, h: float, ribs: int, seed: int):
    """One pumpkin sitting on the ground: a squat round of ribs that run from the stalk's
    dimple to its foot, each rib a small bulge lit on its left, the grooves between them
    following the round; lit from the upper left, a short curled stalk."""
    rx, ry = w / 2, h / 2
    cy = base - ry + 1.2
    pts = {(x, y) for (x, y) in oval(cx, cy, rx, ry) if y <= base}
    phase = noise2(seed, 0, 631)
    for (x, y) in pts:
        nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        lam = -0.55 * nx - 0.6 * ny + 0.62 * nz
        ring = math.sqrt(max(0.05, 1 - ny * ny))
        theta = math.asin(max(-1.0, min(1.0, nx / ring)))
        k = (theta / math.pi * ribs + phase) % 1
        if k < 0.13:
            lam -= 0.38  # a groove
        elif k < 0.42:
            lam += 0.14  # the rib's lit side
        elif k > 0.8:
            lam -= 0.12
        i = 4 if lam > 0.92 else 3 if lam > 0.5 else 2 if lam > 0.12 else 1 if lam > -0.3 else 0
        if ny < -0.72 and abs(nx) < 0.3:
            i = max(1, i - 1)  # the dimple round the stalk
        if y == base:
            i = min(i, 1)
        cv.set(x, y, PUMPKIN[i])
    top = min(y for (_, y) in pts)
    sx = int(cx)
    cv.set(sx, top, STALK[1]); cv.set(sx, top - 1, STALK[2]); cv.set(sx + 1, top - 1, STALK[1])
    if w > 9:
        cv.set(sx + 1, top - 2, STALK[1]); cv.set(sx + 2, top - 2, STALK[0])


def _leaf(cv: Canvas, cx: int, cy: int, flip: int = 1):
    """A broad pumpkin leaf lying on the ground, three rounded lobes, lit on its upper left,
    its veins running out from the stalk."""
    lobes = [(cx - 2 * flip, cy), (cx, cy - 1), (cx + 2 * flip, cy)]
    pts = set()
    for (lx, ly) in lobes:
        pts |= disc(lx + 0.5, ly + 0.5, 1.7)
    for (x, y) in pts:
        lam = -(x - cx) / 3.5 - (y - cy) / 2.0
        cv.set(x, y, LEAF[4] if lam > 0.8 else LEAF[3] if lam > -0.3 else LEAF[2])
    for (lx, ly) in lobes:
        cv.set(lx, ly, LEAF[2])  # the veins
    cv.set(cx, cy + 1, LEAF[1])


def pumpkins() -> Canvas:
    """Three pumpkins on their vine, 32 x 22: a big one in front, a smaller one behind it to
    the right and a little one beside it, each sitting on the ground on its flattened foot,
    the vine running between them under broad leaves, a curled tendril."""
    w, h = 32, 22
    cv = Canvas(w, h, pad=PAD)
    for x in range(6, 28):  # the vine, along the ground between them
        y = 16 + int(math.sin(x / 4.1) * 1.4)
        cv.set(x, y, LEAF[2])
    for (lx, ly, f) in ((5, 15, 1), (18, 13, -1), (28, 15, -1)):
        _leaf(cv, lx, ly, f)
    for (tx, ty) in ((27, 10), (28, 9), (29, 9), (30, 10), (29, 11)):  # a tendril's curl
        cv.set(tx, ty, LEAF[3])
    _pumpkin(cv, 22.5, 15, 10, 8, 5, seed=3)
    _pumpkin(cv, 11.5, h - 2, 15, 11, 6, seed=1)
    _pumpkin(cv, 26, h - 1, 6.5, 5, 4, seed=7)
    _leaf(cv, 19, h - 2, 1)  # a leaf in front, at the big one's foot
    return cv


# Dry stone walls are built here as a ground plan raised to a height: each piece is a
# footprint on the ground, the wall's body stands on it, and a coping of stones set on
# edge stands on the body, inset from its sides. Faces that look toward the viewer are
# drawn; everything else is hidden behind them, as it would be (one camera, world-rules
# 2a). The stones of every face and top are laid by a jittered Voronoi, so no two are
# alike and no joint runs on along a line.
WALL_H = 6


def _stone_at(u: float, v: float, su: float, sv: float, seed: int):
    """The stone a point of a face or top lies in: its id, how close the point is to a
    joint (px) and its offset from the stone's middle, from sites about su x sv apart,
    each course shifted so the joints never line up."""
    k = su / sv
    best = []
    gv = int(math.floor(v / sv))
    for j in range(gv - 1, gv + 2):
        off = noise2(j, 0, seed) * su
        gu = int(math.floor((u - off) / su))
        for i in range(gu - 1, gu + 2):
            pu = (i + 0.25 + noise2(i, j, seed + 1) * 0.5) * su + off
            pv = (j + 0.25 + noise2(i, j, seed + 2) * 0.5) * sv
            best.append((math.hypot(u - pu, (v - pv) * k), (i, j), u - pu, v - pv))
    best.sort()
    # the gap to the next stone, in screen pixels whichever way that stone lies (the
    # sites are measured stretched across v, so a bed joint would come out too thin)
    a, b = best[0], best[1]
    du, dv = b[2] - a[2], b[3] - a[3]
    n = math.hypot(du, dv) or 1.0
    stretch = math.hypot(du / n, dv / n * k)
    return a[1], (b[0] - a[0]) / stretch, a[2], a[3]


def _stone_px(sid, joint: float, du: float, dv: float, su: float, sv: float, base: int, seed: int) -> str:
    """One pixel of a dry stone: the stone's own tone, lit on its upper left and turned
    from the light at its lower right, dark in the joints (no mortar), now and then a
    fleck of lichen on a lit top."""
    if joint < 1.05:
        return STONE[0] if noise2(*sid, seed + 3) > 0.35 else STONE[1]
    t = base + (1 if noise2(*sid, seed + 4) > 0.7 else -1 if noise2(*sid, seed + 4) < 0.2 else 0)
    lam = -du / su * 1.6 + dv / sv * 1.8
    t += 1 if lam > 0.42 else -1 if lam < -0.5 else 0
    if lam > 0.5 and noise2(sid[0], sid[1], seed + 5) > 0.82 and noise2(int(du * 7), int(dv * 7), seed + 6) > 0.6:
        return LICHEN
    return STONE[max(1, min(4, t))]


def _drystone(cv: Canvas, body: set, coping: dict, dirs: dict, seed: int):
    """Raise a dry stone wall on `body` (ground pixels), WALL_H high, with its coping on
    the `coping` pixels (each pixel's height above the body); `dirs` gives the way the
    wall runs at each pixel ('ew' or 'ns'), which way its coping stones lie across."""
    ys = sorted({y for (_, y) in body})
    for y in ys:
        for x in sorted(x for (x, yy) in body if yy == y):
            if (x, y + 1) not in body:  # a face toward the viewer
                for z in range(WALL_H):
                    sid, j, du, dv = _stone_at(x, z, 7.5, 3.3, seed)
                    c = _stone_px(sid, j, du, dv, 7.5, 3.3, 2, seed)
                    if z == 0:
                        c = STONE[1] if c not in (STONE[0], STONE[1]) else STONE[0]  # where it meets the ground
                    cv.set(x, y - z, c)
            if (x, y) not in coping:  # the body's top, a ledge either side of the coping
                sid, j, du, dv = _stone_at(x, y, 6.0, 2.6, seed + 10)
                cv.set(x, y - WALL_H, _stone_px(sid, j, du, -dv, 6.0, 2.6, 3, seed + 10))
        for x in sorted(x for (x, yy) in coping if yy == y):
            hc, ns = coping[(x, y)], dirs.get((x, y)) == 'ns'
            su, sv = (8.0, 3.4) if ns else (3.4, 6.0)
            if (x, y + 1) not in coping:  # the coping stones' edges toward the viewer
                for z in range(hc):
                    sid, j, du, dv = _stone_at(x, z + WALL_H, 3.4, 9.0, seed + 20)
                    c = _stone_px(sid, j, du, dv, 3.4, 9.0, 3, seed + 20)
                    cv.set(x, y - WALL_H - z, c)
            sid, j, du, dv = _stone_at(x, y, su, sv, seed + 30)
            cv.set(x, y - WALL_H - hc, _stone_px(sid, j, du, -dv, su, sv, 4, seed + 30))


def _coping(body: set, dirs: dict, seed: int) -> dict:
    """The coping stands on the body inset a pixel from each side, a little ragged in
    height, stone by stone (2 or 3 px)."""
    out = {}
    for (x, y) in body:
        ns = dirs.get((x, y)) == 'ns'
        inner = all((x + dx, y + dy) in body for dx, dy in (((1, 0), (-1, 0)) if ns else ((0, 1), (0, -1))))
        if ns:
            inner = inner and (x, y + 1) in body
        else:
            inner = inner and (x - 1, y) in body and (x + 1, y) in body
        if inner:
            sid = _stone_at(x, y, *((8.0, 3.4) if ns else (3.4, 6.0)), seed + 30)[0]
            out[(x, y)] = 2 + (noise2(*sid, seed + 40) > 0.55)
    return out


def drystone_wall(length: int = 64) -> Canvas:
    """A dry stone field wall running across the view, 64 x 14: its face of rounded stones
    of every size laid without mortar, dark in the joints and lit on their upper left, a
    ledge along its top and a ragged coping of stones set on edge."""
    w, h = length, 14
    cv = Canvas(w, h, pad=PAD)
    body = {(x, y) for x in range(w) for y in range(h - 4, h)}
    dirs = {p: 'ew' for p in body}
    _drystone(cv, body, _coping(body, dirs, 71), dirs, 71)
    return cv


def drystone_wall_ns(length: int = 40) -> Canvas:
    """A dry stone wall running away from the viewer, 10 x 50: from the camera its long top
    with the coping stones laid across it, and its end's face toward the viewer."""
    w, h = 10, length + 10
    cv = Canvas(w, h, pad=PAD)
    body = {(x, y) for x in range(1, 9) for y in range(10, h)}
    dirs = {p: 'ns' for p in body}
    _drystone(cv, body, _coping(body, dirs, 72), dirs, 72)
    return cv


def drystone_corner(side: str = 'w') -> Canvas:
    """A dry stone wall's corner, 36 x 40: a run across the view turning toward the viewer
    at its west end (side 'w') or its east end ('e'), the coping running round the turn,
    the two ways of laying its stones meeting at the corner."""
    w, h = 36, 40
    cv = Canvas(w, h, pad=PAD)
    r0 = 10
    arm = range(0, 8) if side == 'w' else range(w - 8, w)
    body = {(x, y) for x in range(w) for y in range(r0, r0 + 4)} | {(x, y) for x in arm for y in range(r0, h)}
    dirs = {(x, y): 'ns' if y >= r0 + 4 else 'ew' for (x, y) in body}
    _drystone(cv, body, _coping(body, dirs, 73 if side == 'w' else 74), dirs, 73 if side == 'w' else 74)
    return cv


def drystone_gatepost() -> Canvas:
    """A gatepost where a dry stone wall ends at a gap, 10 x 26: a pier of big squared
    quoins taller than the wall, laid long and short in turn, a flat capstone over it
    with its front edge in half light, and the iron pins a gate hangs on. Placed with its
    foot a pixel below the wall's, it stands in front of the wall's end."""
    w, h = 10, 26
    cv = Canvas(w, h, pad=PAD)
    x0, x1, ph = 2, 8, 17
    foot = h - 1
    for x in range(x0, x1):  # the pier's face: courses of quoins, long and short in turn
        for z in range(ph):
            course = z // 4
            split = x0 + (2 if course % 2 else 4)
            joint = z % 4 == 3 or x == split
            if joint:
                c = STONE[1] if noise2(x, z, 741) > 0.3 else STONE[0]
            else:  # each quoin lit along its top and left, turned from the light at its right
                left = x0 if x < split else split + 1
                c = STONE[4] if x == left or z % 4 == 2 else STONE[3]
                if x == x1 - 1:
                    c = STONE[2]  # the pier's corner, turning away from the light
                if noise2(x, z, 742) > 0.92:
                    c = STONE[2]  # a pit in the stone
            cv.set(x, foot - z, STONE[1] if z == 0 else c)
    top = foot - ph
    for x in range(x0 - 1, x1 + 1):  # the capstone's front edge
        cv.set(x, top, STONE[2]); cv.set(x, top - 1, STONE[3])
    for y in range(top - 5, top - 1):  # its top, overhanging the pier all round
        for x in range(x0 - 1, x1 + 1):
            c = STONE[4] if x < x1 - 1 and y > top - 5 else STONE[3]
            if x == x0 + 3 and y > top - 4:
                c = STONE[2]  # where two slabs meet
            cv.set(x, y, c)
    cv.set(x1, top - 1, STONE[1]); cv.set(x1, top, STONE[1])
    for py in (foot - 3, foot - 11):  # the gate's iron pins
        cv.set(x1 - 1, py, '#2A2D36'); cv.set(x1, py, '#3C404C'); cv.set(x1 - 1, py - 1, '#545A68')
    return cv


def props() -> dict[str, Canvas]:
    return {
        'barn': barn(), 'haystack': haystack(), 'round_bale': round_bale(), 'round_bale_side': round_bale_side(), 'scarecrow': scarecrow(), 'windmill': windmill(),
        'windmill_f1': windmill(math.pi / 6), 'windmill_f2': windmill(math.pi / 3),
        'pumpkins': pumpkins(), 'sheep': sheep(1), 'sheep_left': sheep(-1), 'beehive': beehive(),
        'willow': willow(), 'reeds': reeds(), 'water_mill': water_mill(),
        **{f'water_mill_f{n}': water_mill(n * math.pi / 24) for n in range(1, 6)}, 'heron': heron(), 'lily_pads': lily_pads(),
        'mossy_log': mossy_log(), 'mushroom_ring': mushroom_ring(), 'hollow_tree': hollow_tree(), 'fern': fern(),
        'forest_bench': forest_bench(), 'bandstand': bandstand(), 'ice_cream_cart': ice_cream_cart(),
        'snowy_pine': snowy_pine(), 'frozen_tarn': frozen_tarn(), 'station_house': station_house(),
        'semaphore': semaphore(), 'standing_stone': standing_stone(0, True), 'standing_stone_b': standing_stone(3, True),
        'standing_stone_low': standing_stone(6, False), 'stump': stump(), 'woodpile': woodpile(), 'sled': sled(),
        'snowman': snowman(), 'drystone_wall': drystone_wall(64), 'drystone_wall_short': drystone_wall(32),
        'drystone_wall_ns': drystone_wall_ns(40), 'drystone_corner_w': drystone_corner('w'), 'drystone_corner_e': drystone_corner('e'),
        'drystone_gatepost': drystone_gatepost(), 'marmot_rock': marmot_rock(), 'cotton_grass': cotton_grass(),
        'lookout_tower': lookout_tower(),
    }


if __name__ == '__main__':
    # by day, at night and on a second ground (prop_sheet.py; SHEET_GROUND picks it)
    import prop_sheet
    size = prop_sheet.sheet(props(), os.environ.get('SHEET', '/tmp/valley-props.png'),
                            second=os.environ.get('SHEET_GROUND', 'snow'))
    print('sheet', size)
