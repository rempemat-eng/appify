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


def water_mill() -> Canvas:
    """The watermill, 112 x 96: a stone mill house with a thatched-look tarred roof seen
    from above, a timber upper floor, warm windows, and a big wooden wheel on its east
    side with buckets, turning in the race."""
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
    # the wheel, side on: two rims joined by paddles, spokes to an iron hub
    wcx, wcy, r = 92, 62, 18
    for k in range(96):
        a = 2 * math.pi * k / 96
        for t in (r, r - 1, r - 2):
            lit = math.sin(a) < 0 and math.cos(a) < 0.3
            cv.set(int(round(wcx + t * math.cos(a))), int(round(wcy + t * math.sin(a))),
                   WOOD[4] if lit and t == r else WOOD[3] if lit else WOOD[1] if t == r else WOOD[2])
    for k in range(16):  # paddles standing out past the rim
        a = 2 * math.pi * k / 16
        for t in range(r - 2, r + 4):
            for o in (0, 1):
                x = int(round(wcx + t * math.cos(a) - o * math.sin(a)))
                y = int(round(wcy + t * math.sin(a) + o * math.cos(a)))
                cv.set(x, y, WOOD[3] if o == 0 else WOOD[1])
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        for t in range(3, r - 2):
            cv.set(int(round(wcx + t * math.cos(a))), int(round(wcy + t * math.sin(a))), WOOD[2])
    for (x, y) in disc(wcx, wcy, 3.2):
        cv.set(x, y, '#727A8A' if x < wcx else '#3C404C')
    return cv


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


def bandstand() -> Canvas:
    """The park's bandstand, 84 x 80: an octagonal roof seen from above in alternating
    red and cream panels with a gilded finial, slender iron columns, a railing, and a
    stone plinth with steps."""
    w, h = 84, 80
    cv = Canvas(w, h, pad=PAD)
    cx, cy = 42, 22
    for y in range(2, 40):
        for x in range(4, w - 4):
            dx, dy = x - cx, (y - cy) * 1.9
            r = math.hypot(dx, dy)
            if r > 38:
                continue
            a = math.atan2(dy, dx)
            seg = int((a + math.pi) / (2 * math.pi) * 8) % 2
            lit = dx + dy < 0
            c = (RED[3] if lit else RED[2]) if seg else (PLASTER[5] if lit else PLASTER[3])
            if r > 35:
                c = GOLD[3] if lit else GOLD[1]
            cv.set(x, y, c)
    for (x, y) in disc(cx, cy - 1, 2.4):
        cv.set(x, y, GOLD[4])
    cv.vline(cx, cy - 8, 6, GOLD[3])
    for k, colx in enumerate((10, 26, 42, 58, 74)):  # columns
        for y in range(38, 64):
            cv.set(colx, y, '#3C404C'); cv.set(colx + 1, y, '#727A8A' if k < 2 else '#545A68')
    for y in (50, 52):  # the railing
        cv.hline(8, y, w - 16, '#545A68')
    for x in range(10, w - 10, 4):
        cv.vline(x, 50, 10, '#3C404C')
    detail.stones(cv, 4, 62, w - 8, 12, STONE, seed=61, course=4)
    for k, (x0, wd) in enumerate(((30, 24), (26, 32))):
        y = 74 + k * 3
        cv.hline(x0, y, wd, STONE[4]); cv.hline(x0, y + 1, wd, STONE[3]); cv.hline(x0, y + 2, wd, STONE[1])
    return cv


def ice_cream_cart() -> Canvas:
    """An ice cream cart, 44 x 40: a striped parasol from above, a pastel box on two
    wheels with tubs showing through the glass lid."""
    cv = Canvas(44, 40, pad=PAD)
    for (x, y) in oval(22, 10, 18, 9):
        a = math.atan2(y - 10, x - 22)
        seg = int((a + math.pi) / (2 * math.pi) * 10) % 2
        cv.set(x, y, ('#F6C6D8' if seg else '#FFFFFF') if (x - 22) + (y - 10) < 4 else ('#D89AB0' if seg else '#E6E2DC'))
    cv.vline(22, 18, 6, '#545A68')
    for (x, y) in rect_set(6, 22, 32, 12):
        cv.set(x, y, '#BFE3E0' if y < 25 else '#94C8C4')
    for k, c in enumerate(('#F6E2A0', '#F6C6D8', '#8A5A3A', '#C6E6B0')):
        cv.rect(9 + k * 7, 23, 5, 2, c)
    for wx in (12, 32):
        for (x, y) in disc(wx, 36, 3):
            cv.set(x, y, '#3C404C' if x < wx else '#2A2D36')
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


def haystack() -> Canvas:
    """A round haystack, 34 x 30, lit gold on the upper left, a few loose wisps."""
    w, h = 34, 30
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(17, 17, 15, 12) | oval(17, 9, 9, 7):
        k = (x - 2) / 30 + (y - 2) / 26
        c = '#F2D27A' if k < 0.6 else '#E2BC5E' if k < 1.0 else '#C99A3C' if k < 1.35 else '#A87E2C'
        if (x * 3 + y * 5) % 11 == 0:
            c = '#A87E2C' if k < 1 else '#8A6420'
        cv.set(x, y, c)
    for (x, y) in ((3, 26), (30, 25), (8, 28)):
        cv.hline(x, y, 3, '#E2BC5E')
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


def windmill() -> Canvas:
    """A valley windmill, 64 x 104: a tapering white tower of plaster with a little
    door and window, a boat-shaped cap, and four lattice sails turning (drawn still)."""
    w, h = 64, 104
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(34, h - 2):
        t = (y - 34) / (h - 36)
        hw = int(10 + t * 8)
        for x in range(cx - hw, cx + hw):
            k = (x - (cx - hw)) / (2 * hw)
            c = PLASTER[4] if k < 0.25 else PLASTER[3] if k < 0.6 else PLASTER[2] if k < 0.85 else PLASTER[1]
            cv.set(x, y, c)
    for (x, y) in rect_set(cx - 4, h - 16, 8, 14):
        cv.set(x, y, WOOD[2] if x < cx else WOOD[1])
    gp.window(cv, cx - 4, 58, 8, 8, shutters=None, sill=False, warm=True)
    for y in range(24, 36):  # the cap
        hw = 12 - abs(y - 30)
        for x in range(cx - 12, cx + 12):
            cv.set(x, y, SLATE[3] if x < cx else SLATE[2])
    for k in range(4):  # the sails
        a = math.pi / 4 + k * math.pi / 2
        for t in range(4, 30):
            bx, by = cx + math.cos(a) * t, 30 + math.sin(a) * t
            cv.set(int(bx), int(by), WOOD[1])
            if t > 8:
                for side in range(1, 6):
                    px = bx + math.cos(a + math.pi / 2) * side
                    py = by + math.sin(a + math.pi / 2) * side
                    lattice = side % 2 == 0 or t % 3 == 0
                    cv.set(int(px), int(py), WOOD[3] if lattice else '#F2EEE6')
    for (x, y) in disc(cx, 30, 2.5):
        cv.set(x, y, WOOD[1])
    return cv


def pumpkins() -> Canvas:
    """Pumpkins on a vine, 30 x 14, lit on their upper left, curling green tendrils."""
    cv = Canvas(30, 14, pad=PAD)
    for x in range(2, 28):
        cv.set(x, 10 + int(math.sin(x / 3) * 1.5), '#447A50')
    for (px, py, r) in ((7, 8, 4), (19, 9, 5), (26, 7, 2.6)):
        for (x, y) in oval(px, py, r, r * 0.8):
            k = (x - px + r) / (2 * r)
            c = '#F2A048' if k < 0.35 else '#E07A28' if k < 0.7 else '#B85A1A'
            if (x - px) % 3 == 0 and k > 0.2:
                c = '#B85A1A' if c != '#B85A1A' else '#8A4010'
            cv.set(x, y, c)
        cv.set(px, int(py - r * 0.8), '#5A7A3A')
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


def props() -> dict[str, Canvas]:
    return {
        'barn': barn(), 'haystack': haystack(), 'scarecrow': scarecrow(), 'windmill': windmill(),
        'pumpkins': pumpkins(), 'sheep': sheep(1), 'sheep_left': sheep(-1), 'beehive': beehive(),
        'willow': willow(), 'reeds': reeds(), 'water_mill': water_mill(), 'heron': heron(), 'lily_pads': lily_pads(),
        'mossy_log': mossy_log(), 'mushroom_ring': mushroom_ring(), 'hollow_tree': hollow_tree(), 'fern': fern(),
        'forest_bench': forest_bench(), 'bandstand': bandstand(), 'ice_cream_cart': ice_cream_cart(),
        'snowy_pine': snowy_pine(), 'frozen_tarn': frozen_tarn(), 'station_house': station_house(),
        'semaphore': semaphore(), 'standing_stone': standing_stone(0, True), 'standing_stone_b': standing_stone(3, True),
        'standing_stone_low': standing_stone(6, False), 'stump': stump(),
    }


if __name__ == '__main__':
    from PIL import Image
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
    out.save(os.environ.get('SHEET', '/tmp/valley-props.png'))
    print('sheet', out.size)
