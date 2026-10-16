"""Mission worlds for NapAttack: Park Patrol, Book Club town, Mountain Retreat.

Run: python3 scripts/art/worlds.py   (or `npm run art`)
Writes assets/worlds/<id>/*.png and lib/world-maps.ts (objects, walk grid,
exploration route, visitor spot) in native pixels, in the same 192 x 176
format as the home garden so the 2.5D projection works unchanged.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, shade_blob, smooth_noise  # noqa: E402
import garden as g  # noqa: E402  (shared palette and trees keep one art style)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'worlds')
W, H, SCALE, CELL = 192, 176, 6, 4
INK = g.INK
SLATE = ['#3A3F4E', '#565D70', '#767E90', '#9AA2B0', '#C4CAD2']
ROOF = ['#4E2420', '#7A3428', '#A34A36', '#C96A4E', '#E6957A']
SNOW = ['#9FB0C4', '#C2CFDC', '#E2E9F0', '#F7FAFC']
MOSSROCK = ['#4B5548', '#646F5E', '#808C78', '#A2AD97', '#C8D0BC']


# ---- terrain ----------------------------------------------------------------
def thick(points, radius, seed=0):
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 9, seed) - 0.5) * (2.4 if seed else 0)
            pts |= disc(cx, cy, r)
    return {(x, y) for (x, y) in pts if 0 <= x < W and 0 <= y < H}


def grass(cv: Canvas, frame=0, tone=None):
    G = tone or g.G
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 22, 11)
            cv.set(x, y, G[2] if n < 0.55 else G[3])
    for ty in range(0, H, 8):
        for tx in range(0, W, 8):
            if noise2(tx, ty, 3) < 0.45:
                x, y = tx + int(noise2(tx, ty, 4) * 6), ty + int(noise2(tx, ty, 5) * 6)
                sway = 1 if (frame and noise2(tx, ty, 6) < 0.5) else 0
                cv.set(x, y + 2, G[1]); cv.set(x + 2, y + 2, G[1]); cv.set(x + 1, y + 3, G[1])
                cv.set(x + sway, y + 1, G[1]); cv.set(x + 2 + sway, y + 1, G[1])
            elif noise2(tx, ty, 7) < 0.2:
                cv.set(tx + 3, ty + 4, G[4])


def edge(mask, x, y):
    return any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def paint_dirt(cv, mask):
    for (x, y) in mask:
        cv.set(x, y, g.P[2] if smooth_noise(x, y, 6, 40) < 0.62 else g.P[3])
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, g.P[0]); cv.set(x, y + 1, g.P[1])
        elif edge(mask, x, y):
            cv.set(x, y, g.P[1])
        if edge(mask, x, y) and noise2(x, y, 44) < 0.3:
            cv.set(x, y, g.G[3])


def paint_paving(cv, mask, seed=0):
    """Light square paving stones with mortar lines and the odd darker slab."""
    for (x, y) in mask:
        mortar = x % 8 == 0 or y % 6 == 0 or (y // 6) % 2 and (x + 4) % 8 == 0
        slab = (x // 8 + y // 6 + seed) % 7 == 0
        col = '#A9A28F' if mortar else ('#C9C1AA' if slab else '#DCD4BC')
        if not mortar and (x % 8 == 1 or y % 6 == 1):
            col = '#E8E1CB'
        cv.set(x, y, col)
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, '#8C8574')
        elif edge(mask, x, y):
            cv.set(x, y, '#B3AB94')


def paint_cobbles(cv, mask):
    """Rounded cobbles: each cell gets a lit top-left and a dark gap."""
    for (x, y) in mask:
        cx, cy = x % 7, (y + (x // 7) % 2 * 3) % 6
        gap = cx == 0 or cy == 0
        n = noise2(x // 7, (y + (x // 7) % 2 * 3) // 6, 81)
        base = SLATE[3] if n < 0.5 else '#A7A291'
        col = SLATE[1] if gap else (SLATE[4] if (cx <= 2 and cy <= 2) else base)
        cv.set(x, y, col)
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, SLATE[0])


def paint_water(cv, mask, frame=0, center=None):
    bank = set()
    for (x, y) in mask:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                n = (x + dx, y + dy)
                if n not in mask and 0 <= n[0] < W and 0 <= n[1] < H:
                    bank.add(n)
    for (x, y) in bank:
        cv.set(x, y, g.SAND[1] if noise2(x, y, 21) < 0.8 else g.SAND[2])
    for (x, y) in mask:
        col = g.WTR[2]
        if (x, y - 1) not in mask:
            col = g.WTR[0]
        elif (x, y - 2) not in mask:
            col = g.WTR[1]
        cv.set(x, y, col)
    pts = sorted(mask)
    for i in range(0, len(pts), 37):
        x, y = pts[i]
        if (x + 3, y) in mask and (x, y - 2) in mask:
            cv.hline(x + (frame if i % 2 else 0), y, 3, g.WTR[3])
    return bank


def flowerbed(cv, x, y, w, h, seed=0):
    cv.rect(x, y, w, h, g.WOOD[1]); cv.rect(x + 1, y + 1, w - 2, h - 2, '#5A3A26')
    for fy in range(y + 2, y + h - 2, 4):
        for fx in range(x + 2, x + w - 2, 4):
            c = [g.RED[3], '#F2D16B', g.CREAM[3], g.NAP[3]][(fx // 4 + fy // 4 + seed) % 4]
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                cv.set(fx + dx, fy + dy, c)
            cv.set(fx, fy, '#E8A33D')


# ---- props ------------------------------------------------------------------
def fountain() -> Canvas:
    cv = Canvas(40, 34)
    basin = oval(20, 24, 18, 8)
    shade_blob(cv, basin, g.STONE[1], g.STONE[2], g.STONE[3], g.STONE[4])
    for (x, y) in oval(20, 23, 14.5, 5.5):
        cv.set(x, y, g.WTR[2] if y > 21 else g.WTR[3])
    cv.rect(18, 8, 5, 15, g.STONE[3]); cv.vline(18, 8, 15, g.STONE[4]); cv.vline(22, 8, 15, g.STONE[2])
    for (x, y) in oval(20.5, 9, 6, 2.5):
        cv.set(x, y, g.STONE[3] if y < 9 else g.STONE[2])
    for i, (x, y) in enumerate(((20, 1), (20, 3), (19, 5), (21, 5), (16, 7), (25, 7), (14, 11), (27, 11), (13, 15), (28, 15))):
        cv.set(x, y, '#E0EFDF' if i % 2 else '#A1CFD0')
    for x in (12, 16, 24, 28):
        cv.set(x, 21, '#E0EFDF')
    cv.outline(INK)
    return cv


def bench() -> Canvas:
    cv = Canvas(26, 16)
    cv.rect(2, 8, 2, 7, g.WOOD[1]); cv.rect(22, 8, 2, 7, g.WOOD[1])
    for y, c in ((2, g.WOOD[4]), (4, g.WOOD[3]), (8, g.WOOD[4]), (10, g.WOOD[3])):
        cv.hline(1, y, 24, c); cv.hline(1, y + 1, 24, g.WOOD[2])
    cv.rect(1, 1, 2, 9, '#3A3F4E'); cv.rect(23, 1, 2, 9, '#3A3F4E')
    cv.outline(INK)
    return cv


def lamp() -> Canvas:
    cv = Canvas(10, 34)
    cv.rect(4, 8, 2, 24, '#3A3F4E'); cv.vline(4, 8, 24, '#565D70')
    cv.rect(2, 31, 6, 2, '#2E323E')
    cv.rect(2, 2, 6, 6, '#3A3F4E'); cv.rect(3, 3, 4, 4, '#FFE58A'); cv.set(3, 3, '#FFF7D6')
    cv.hline(1, 1, 8, '#2E323E'); cv.set(4, 0, '#2E323E'); cv.set(5, 0, '#2E323E')
    cv.outline(INK)
    return cv


def hedge(w: int) -> Canvas:
    cv = Canvas(w, 14)
    pts = set()
    for x in range(0, w, 6):
        pts |= {(px, py) for (px, py) in disc(x + 3, 6, 4.6) if 0 <= px < w}
    pts |= {(x, y) for x in range(w) for y in range(6, 13)}
    shade_blob(cv, pts, g.LEAF[1], g.LEAF[2], g.LEAF[3], g.LEAF[4])
    for i in range(w // 4):
        x, y = int(noise2(i, 1, w) * (w - 2)), int(2 + noise2(i, 2, w) * 8)
        if (x, y) in pts:
            cv.set(x, y, g.LEAF[1])
    cv.outline(g.LEAF[0])
    return cv


def library() -> Canvas:
    """Grand little library: columns, steps, an open-book sign."""
    w, h = 72, 54
    cv = Canvas(w, h)
    cv.rect(4, 20, 64, 28, '#E2D6BC')
    for x in range(4, 68):
        cv.set(x, 20, '#F1E8D2')
    for x in (10, 22, 46, 58):  # columns
        cv.rect(x, 22, 5, 24, '#F4ECD8'); cv.vline(x, 22, 24, '#FFFFFF'); cv.vline(x + 4, 22, 24, '#C9BC9E')
    for x in (16, 52):  # tall windows
        cv.rect(x - 2, 25, 5, 14, '#3A4A66'); cv.rect(x - 1, 26, 3, 12, '#6E8CB0'); cv.set(x - 1, 26, '#B8D2EA')
    cv.rect(30, 30, 12, 16, '#5A3A26'); cv.rect(31, 31, 10, 15, '#7A5232'); cv.vline(36, 31, 15, '#5A3A26')
    cv.set(34, 38, '#F2D16B'); cv.set(38, 38, '#F2D16B')
    # pediment roof
    for y in range(4, 20):
        span = int((y - 4) * 2.3) + 3
        for x in range(w // 2 - span, w // 2 + span):
            cv.set(x, y, ROOF[2] if (x + y) % 5 else ROOF[1])
        cv.set(w // 2 - span, y, ROOF[0]); cv.set(w // 2 + span - 1, y, ROOF[0])
    cv.hline(0, 19, w, '#C9BC9E'); cv.hline(0, 20, w, '#B3A584')
    # open-book sign in the gable
    for (x, y) in ((32, 12), (33, 11), (34, 11), (35, 12), (36, 12), (37, 11), (38, 11), (39, 12)):
        cv.set(x, y, '#FBF4E4')
    cv.hline(32, 13, 8, '#FBF4E4'); cv.hline(32, 14, 8, '#C9B48E'); cv.vline(36, 11, 4, '#8C7A5E')
    # steps
    for i, y in enumerate((46, 48, 50)):
        cv.rect(26 - i * 2, y, 20 + i * 4, 2, '#CFC5AE' if i % 2 else '#E2D9C2')
    cv.outline(INK)
    return cv


def house(roof=None, sign=None) -> Canvas:
    roof = roof or ROOF
    w, h = 40, 40
    cv = Canvas(w, h)
    cv.rect(4, 18, 32, 20, g.CREAM[2])
    for y in range(20, 38, 4):
        cv.hline(4, y, 32, g.CREAM[1])
    cv.rect(16, 26, 8, 12, g.WOOD[1]); cv.rect(17, 27, 6, 11, g.WOOD[2]); cv.set(22, 32, '#F2D16B')
    for x in (7, 27):
        cv.rect(x, 23, 6, 6, g.WOOD[0]); cv.rect(x + 1, 24, 4, 4, '#9AD3EA'); cv.set(x + 1, 24, '#E4F5FA')
        cv.rect(x, 29, 6, 2, g.WOOD[1]); cv.set(x + 1, 28, g.RED[3]); cv.set(x + 3, 28, '#F2D16B'); cv.set(x + 4, 28, g.RED[3])
    for y in range(3, 19):
        span = int((y - 3) * 1.3) + 5
        for x in range(w // 2 - span, w // 2 + span):
            cv.set(x, y, roof[2] if (x + (y // 3) * 2) % 6 else roof[1])
        cv.set(w // 2 - span, y, roof[0]); cv.set(w // 2 + span - 1, y, roof[0])
    cv.hline(0, 18, w, roof[0])
    if sign:
        cv.rect(12, 14, 16, 5, g.WOOD[3]); cv.hline(14, 16, 12, g.WOOD[1])
    cv.outline(INK)
    return cv


def cafe_table() -> Canvas:
    cv = Canvas(24, 28)
    for y in range(2, 10):  # umbrella
        span = (y - 1) * 1.4 + 2
        for x in range(int(12 - span), int(12 + span)):
            cv.set(x, y, '#5FA35A' if (x // 3) % 2 else g.CREAM[3])
    cv.vline(12, 10, 12, g.STONE[1])
    for (x, y) in oval(12, 21, 7, 2.6):
        cv.set(x, y, g.CREAM[2] if y < 21 else g.CREAM[1])
    cv.rect(3, 20, 3, 7, g.WOOD[2]); cv.rect(18, 20, 3, 7, g.WOOD[2])
    cv.set(10, 20, '#FFF7E6'); cv.set(14, 20, g.RED[3])
    cv.outline(INK)
    return cv


def book_cart() -> Canvas:
    cv = Canvas(26, 20)
    cv.rect(1, 6, 24, 9, g.WOOD[2]); cv.hline(1, 6, 24, g.WOOD[4]); cv.hline(1, 14, 24, g.WOOD[1])
    for i, x in enumerate(range(3, 23, 3)):
        hgt = 5 + (i % 3)
        col = [g.RED[2], '#4C6E9E', '#5FA35A', '#D8AF5E', g.NAP[2]][i % 5]
        cv.rect(x, 6 - hgt + 5, 2, hgt, col); cv.set(x, 6 - hgt + 5, '#FBF4E4')
    for cx in (6, 20):
        for (x, y) in oval(cx, 16.5, 3, 3):
            cv.set(x, y, g.STONE[1] if (x - cx) ** 2 + (y - 16.5) ** 2 > 3 else g.STONE[3])
    cv.outline(INK)
    return cv


def cabin() -> Canvas:
    w, h = 50, 42
    cv = Canvas(w, h)
    for i, y in enumerate(range(18, 39, 3)):  # log walls
        cv.rect(4, y, 42, 3, g.WOOD[3] if i % 2 else g.WOOD[2]); cv.hline(4, y + 2, 42, g.WOOD[1])
        cv.set(3, y + 1, g.WOOD[4]); cv.set(46, y + 1, g.WOOD[4])
    cv.rect(21, 27, 9, 12, g.WOOD[0]); cv.rect(22, 28, 7, 11, g.WOOD[1]); cv.set(27, 33, '#F2D16B')
    cv.rect(8, 24, 7, 6, g.WOOD[0]); cv.rect(9, 25, 5, 4, '#FFE58A'); cv.set(9, 25, '#FFF7D6')
    cv.rect(35, 24, 7, 6, g.WOOD[0]); cv.rect(36, 25, 5, 4, '#FFE58A')
    for y in range(4, 19):  # snowy roof
        span = int((y - 4) * 1.7) + 4
        for x in range(w // 2 - span, w // 2 + span):
            cv.set(x, y, SNOW[3] if y < 8 or (x + y) % 9 == 0 else ('#6E4A30' if (x + y) % 4 else '#5A3A26'))
        cv.set(w // 2 - span, y, SNOW[1]); cv.set(w // 2 + span - 1, y, '#4A3122')
    cv.rect(34, 2, 5, 9, g.STONE[2]); cv.hline(34, 2, 5, g.STONE[4])  # chimney
    cv.outline(INK)
    return cv


def campfire() -> Canvas:
    cv = Canvas(18, 16)
    for (x, y) in oval(9, 12.5, 8, 3):
        cv.set(x, y, g.STONE[2] if (x + y) % 3 else g.STONE[1])
    cv.rect(3, 11, 12, 2, g.WOOD[2]); cv.rect(5, 10, 8, 2, g.WOOD[1])
    flame = [(9, 2), (8, 4), (9, 4), (10, 4), (7, 6), (8, 6), (9, 6), (10, 6), (11, 6), (6, 8), (7, 8), (8, 8), (9, 8), (10, 8), (11, 8), (12, 8),
             (8, 3), (10, 5), (7, 7), (11, 7), (8, 5), (9, 5), (9, 7), (10, 7), (8, 7), (7, 9), (8, 9), (9, 9), (10, 9), (11, 9)]
    for (x, y) in flame:
        cv.set(x, y, '#FFF3BF' if y >= 7 and 8 <= x <= 10 else '#F5B94A' if y >= 5 else '#E5733A')
    cv.outline(INK)
    return cv


def boulder(big=True) -> Canvas:
    w, h = (26, 18) if big else (14, 10)
    cv = Canvas(w, h)
    pts = oval(w / 2, h / 2 + 1, w / 2 - 1, h / 2 - 1.2) | oval(w / 2 - 3, h / 2 + 2, w / 3, h / 2.6)
    pts = {(x, y) for (x, y) in pts if 0 <= x < w and 0 <= y < h}
    shade_blob(cv, pts, MOSSROCK[1], MOSSROCK[2], MOSSROCK[3], MOSSROCK[4])
    for i in range(w // 3):
        x, y = int(noise2(i, 1, w) * w), int(noise2(i, 2, w) * h / 2)
        if (x, y) in pts:
            cv.set(x, y, g.LEAF[3])
    cv.outline(INK)
    return cv


def cairn() -> Canvas:
    cv = Canvas(16, 26)
    y = 24
    for i, (rw, rh) in enumerate(((14, 5), (11, 4), (9, 4), (7, 3), (5, 3))):
        pts = oval(8, y - rh / 2, rw / 2, rh / 2)
        shade_blob(cv, pts, g.STONE[1], g.STONE[2], g.STONE[3], g.STONE[4])
        y -= rh - 1
    cv.vline(8, 1, 6, g.WOOD[1]); cv.rect(9, 1, 5, 3, g.NAP[3]); cv.set(9, 1, g.NAP[4])  # little flag
    cv.outline(INK)
    return cv


def bridge() -> Canvas:
    cv = Canvas(30, 22)
    for i, x in enumerate(range(2, 28, 4)):
        cv.rect(x, 4, 4, 16, g.WOOD[3] if i % 2 else g.WOOD[4]); cv.vline(x + 3, 4, 16, g.WOOD[2])
    cv.rect(0, 2, 30, 2, g.WOOD[1]); cv.rect(0, 19, 30, 2, g.WOOD[1])
    cv.outline(INK)
    return cv


def duck() -> Canvas:
    cv = Canvas(10, 8)
    for (x, y) in oval(5, 5, 4, 2.4):
        cv.set(x, y, '#FBF4E4' if y < 5 else '#D9CFB8')
    for (x, y) in oval(7.5, 2.5, 1.8, 1.8):
        cv.set(x, y, '#3E7D44')
    cv.set(9, 3, '#E8A33D'); cv.set(8, 2, INK)
    cv.outline('#3A4A52')
    return cv


SPRITES = {
    'tree': lambda: g.tree(True), 'tree_small': lambda: g.tree(False), 'tree_autumn': lambda: g.tree(True, True),
    'pine': g.pine, 'bush': g.bush, 'fountain': fountain, 'bench': bench, 'lamp': lamp,
    'hedge': lambda: hedge(60), 'library': library, 'house_red': lambda: house(ROOF),
    'house_blue': lambda: house(['#1E2A44', '#2E3F66', '#45598A', '#6A7FAE', '#9DB0D6'], sign=True),
    'cafe': cafe_table, 'cart': book_cart, 'cabin': cabin, 'campfire': campfire,
    'boulder': lambda: boulder(True), 'stone': lambda: boulder(False), 'cairn': cairn,
    'bridge': bridge, 'duck': duck,
}


# ---- worlds -------------------------------------------------------------------
def world_park(frame):
    cv = Canvas(W, H)
    grass(cv, frame)
    plaza = disc(96, 100, 28)
    paths = thick([(96, 180), (96, 100)], 8) | thick([(-4, 100), (200, 100)], 7) | thick([(96, 100), (96, 30)], 6)
    paint_paving(cv, (plaza | paths) & {(x, y) for x in range(W) for y in range(24, H)})
    pond = {(x, y) for (x, y) in oval(158, 148, 24, 13)}
    water = pond
    paint_water(cv, water, frame)
    for fb in ((20, 120, 30, 12, 0), (20, 66, 30, 12, 1), (140, 60, 32, 12, 2)):
        flowerbed(cv, *fb)
    objects = [
        *[(f'pine-{i}', 'pine', x, -20 + (i % 2) * 4) for i, x in enumerate(range(-8, 196, 15))],
        ('tree-0', 'tree', -12, -16), ('tree-1', 'tree_autumn', 150, -18), ('tree-2', 'tree', 168, 20),
        ('tree-3', 'tree', -10, 140), ('tree-4', 'tree_small', 54, 132),
        ('hedge-l', 'hedge', 6, 30), ('hedge-r', 'hedge', 126, 30),
        ('fountain', 'fountain', 76, 72), ('bench-1', 'bench', 40, 88), ('bench-2', 'bench', 126, 88),
        ('lamp-1', 'lamp', 66, 62), ('lamp-2', 'lamp', 118, 62), ('lamp-3', 'lamp', 66, 118), ('lamp-4', 'lamp', 118, 118),
        ('bush-1', 'bush', 30, 152), ('bush-2', 'bush', 120, 150), ('duck', 'duck', 150, 142),
    ]
    route = [(96, 160), (96, 128), (60, 104), (40, 112), (70, 140), (130, 132), (150, 112), (132, 104), (96, 134)]
    return cv, objects, water, route, (150, 128)


def world_town(frame):
    cv = Canvas(W, H)
    grass(cv, frame)
    street = {(x, y) for x in range(W) for y in range(84, 116)}
    lane = thick([(96, 116), (96, 180)], 9)
    paint_cobbles(cv, street | lane)
    # pavements in front of the buildings
    paint_paving(cv, {(x, y) for x in range(W) for y in range(70, 84)}, seed=2)
    planters = [(10, 128, 22, 10, 1), (160, 128, 22, 10, 3)]
    for fb in planters:
        flowerbed(cv, *fb)
    objects = [
        *[(f'pine-{i}', 'pine', x, -14 + (i % 2) * 4) for i, x in enumerate(range(-8, 196, 15))],
        ('tree-b0', 'tree', 40, -10), ('tree-b1', 'tree_small', 120, -4),
        ('house-l', 'house_red', 2, 32), ('library', 'library', 60, 18), ('house-r', 'house_blue', 150, 32),
        ('lamp-1', 'lamp', 44, 52), ('lamp-2', 'lamp', 140, 52), ('lamp-3', 'lamp', 30, 116), ('lamp-4', 'lamp', 152, 116),
        ('cafe-1', 'cafe', 112, 118), ('cafe-2', 'cafe', 136, 140), ('cart', 'cart', 54, 120),
        ('tree-0', 'tree', -10, 132), ('tree-1', 'tree_small', 64, 142), ('tree-2', 'tree', 168, 140),
        ('bush-1', 'bush', 36, 64), ('bush-2', 'bush', 138, 64),
    ]
    route = [(96, 160), (96, 104), (60, 96), (40, 100), (96, 92), (150, 100), (120, 108), (96, 128)]
    return cv, objects, set(), route, (70, 108)


def world_mountain(frame):
    cv = Canvas(W, H)
    alpine = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
    grass(cv, frame, alpine)
    for y in range(0, 60):  # snowfield at the top
        for x in range(W):
            if y < 34 + int(10 * math.sin(x / 19) + 4 * math.sin(x / 7)):
                cv.set(x, y, SNOW[2] if smooth_noise(x, y, 9, 5) < 0.6 else SNOW[3])
    trail = thick([(70, 180), (74, 150), (110, 124), (100, 96), (66, 80), (86, 52)], 6, seed=3)
    paint_dirt(cv, trail)
    stream = thick([(200, 70), (170, 84), (150, 110), (156, 140), (140, 180)], 5, seed=4)
    paint_water(cv, stream, frame)
    objects = [
        *[(f'pine-{i}', 'pine', x, 22 + (i % 3) * 6) for i, x in enumerate(range(-6, 60, 12))],
        *[(f'pine-r{i}', 'pine', x, 120 + (i % 2) * 8) for i, x in enumerate(range(160, 200, 13))],
        ('cabin', 'cabin', 6, 74), ('campfire', 'campfire', 58, 104), ('cairn', 'cairn', 92, 26),
        ('boulder-1', 'boulder', 116, 60), ('boulder-2', 'boulder', 20, 140), ('stone-1', 'stone', 128, 150),
        ('stone-2', 'stone', 40, 128), ('bridge', 'bridge', 140, 98),
        ('pine-a', 'pine', 110, 140), ('pine-b', 'pine', 86, 146),
    ]
    route = [(74, 164), (90, 136), (110, 122), (100, 98), (70, 112), (66, 84), (86, 60), (96, 54), (80, 76), (100, 104)]
    return cv, objects, stream, route, (98, 60)


WORLDS = {'park': world_park, 'book': world_town, 'mountain': world_mountain}


# ---- horizon backdrops for the 2.5D view -------------------------------------
def sky(cv, horizon, bands):
    for y in range(horizon):
        i = min(len(bands) - 1, int(y / horizon * len(bands)))
        cv.hline(0, y, cv.w, bands[i])


def backdrop(kind) -> Canvas:
    bw, bh, horizon = 216, 150, 80
    cv = Canvas(bw, bh)
    sky(cv, horizon, ['#A9D3E6', '#C3E0EA', '#DCEBE6', '#EEF2DF'])
    if kind == 'mountain':
        for (px, ph, sw) in ((40, 62, 48), (120, 70, 60), (190, 56, 44)):
            for x in range(bw):
                top = horizon - ph + abs(x - px) * ph / sw
                for y in range(int(top), horizon + 2):
                    snow = y < horizon - ph * 0.55 + (x % 5)
                    lit = x < px
                    cv.set(x, y, (SNOW[3] if lit else SNOW[1]) if snow else ('#7D8BA0' if lit else '#5E6B82'))
    elif kind == 'book':
        for i, x in enumerate(range(-4, bw, 18)):
            hgt = 18 + (i * 7) % 16
            for y in range(horizon - hgt, horizon + 2):
                for xx in range(x, x + 16):
                    cv.set(xx, y, '#9FA9B8' if xx < x + 9 else '#8792A4')
            for wy in range(horizon - hgt + 4, horizon - 2, 5):
                for wx in range(x + 3, x + 14, 5):
                    cv.set(wx, wy, '#E9EEF2'); cv.set(wx + 1, wy, '#E9EEF2')
            if i % 3 == 0:
                cv.rect(x + 6, horizon - hgt - 6, 4, 6, '#8792A4')
    for x in range(bw):  # soft hills/treeline join for every world
        h2 = horizon - 4 - int(3 * math.sin(x / 13) + 2 * math.sin(x / 5))
        for y in range(h2, bh):
            cv.set(x, y, '#6E9F6B' if y < horizon + 4 else '#7CAE66')
    return cv


def main():
    worlds = {}
    all_props = {}
    for wid, fn in WORLDS.items():
        os.makedirs(os.path.join(OUT, wid), exist_ok=True)
        cv0, objects, water, route, visitor = fn(0)
        cv1, *_ = fn(1)
        sprites = {}
        for (_id, key, x, y) in objects:
            sprites.setdefault(key, SPRITES[key]())
        for frame, cv in ((0, cv0), (1, cv1)):
            for (_id, key, x, y) in objects:
                s = sprites[key]
                if key not in ('pine', 'hedge'):
                    cv.shadow(x + s.w / 2 + 2, y + s.h - 1, s.w * 0.42, max(2.0, s.h * 0.09))
            cv.save(os.path.join(OUT, wid, f'ground-{frame}.png'), SCALE)
        for key, s in sprites.items():
            all_props[key] = s
        backdrop(wid).save(os.path.join(OUT, wid, 'sky.png'), SCALE)
        # walk grid: not water, not object footprints, inside the scene margins
        blocked = {(x // CELL, y // CELL) for (x, y) in water}
        for (_id, key, x, y) in objects:
            s = sprites[key]
            foot = 12 if s.w > 40 else 5
            for yy in range(y + s.h - foot, y + s.h):
                for xx in range(x + 2, x + s.w - 2):
                    blocked.add((xx // CELL, yy // CELL))
        walk = []
        for r in range(H // CELL):
            row = ''
            for c in range(W // CELL):
                cx, cy = c * CELL + 2, r * CELL + 2
                ok = (c, r) not in blocked and 20 <= cx <= W - 20 and 44 <= cy <= 166
                row += '.' if ok else '#'
            walk.append(row)
        worlds[wid] = {
            'objects': [{'id': i, 'sprite': k, 'x': x, 'y': y, 'w': sprites[k].w, 'h': sprites[k].h} for (i, k, x, y) in objects],
            'walk': walk,
            'route': [{'x': x, 'y': y} for (x, y) in route],
            'visitor': {'x': visitor[0], 'y': visitor[1]},
        }
        prev = Canvas(W, H)
        prev.paste(cv0, 0, 0)
        for (_id, key, x, y) in sorted(objects, key=lambda o: o[3] + sprites[o[1]].h):
            prev.paste(sprites[key], x, y)
        prev.save(f'/tmp/world-{wid}.png', 3)
    os.makedirs(os.path.join(OUT, 'props'), exist_ok=True)
    for key, s in sorted(all_props.items()):
        s.save(os.path.join(OUT, 'props', f'{key}.png'), SCALE)
    # Static image imports (React Native needs literal paths), generated so they never drift.
    ident = lambda k: ''.join(p.capitalize() for p in k.split('_'))
    imp = [f"import prop{ident(k)} from '@/assets/worlds/props/{k}.png';" for k in sorted(all_props)]
    for wid in WORLDS:
        for name in ('ground-0', 'ground-1', 'sky'):
            imp.append(f"import {wid}{ident(name.replace('-', '_'))} from '@/assets/worlds/{wid}/{name}.png';")
    assets = [
        '// Generated by scripts/art/worlds.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        *imp,
        'export const worldProps: Record<string, ImageSourcePropType> = {',
        *[f'  {k}: prop{ident(k)},' for k in sorted(all_props)],
        '};',
        'export const worldImages = {',
        *[f'  {wid}: {{ ground: [{wid}Ground0, {wid}Ground1], sky: {wid}Sky }},' for wid in WORLDS],
        '} as const;',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'world-assets.ts'), 'w') as f:
        f.write('\n'.join(assets))
    ts = [
        '// Generated by scripts/art/worlds.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const WORLD = {{ width: {W}, height: {H}, scale: {SCALE}, cell: {CELL} }} as const;',
        'export type WorldId = "park" | "book" | "mountain";',
        'export type WorldMap = { objects: readonly { id: string; sprite: string; x: number; y: number; w: number; h: number }[]; walk: readonly string[]; route: readonly { x: number; y: number }[]; visitor: { x: number; y: number } };',
        f'export const worldMaps: Record<WorldId, WorldMap> = {json.dumps(worlds)};',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'world-maps.ts'), 'w') as f:
        f.write('\n'.join(ts))
    print('ok', ', '.join(worlds))


if __name__ == '__main__':
    main()
