"""Props for the Frostline Highlands (world-atlas.md, "The connected world"; Matt, 18 Oct
19:07): the high country above the Ridge cabin. A stone bothy where walkers shelter,
a brass viewing scope at the High Lookout, a trail post at each fork, a windsock on
the saddle, an ibex on a rock, ice at a lake's edge and a frozen fall.

Same rules as the valley's props (art-style.md): light from the upper left, stone and
snow from materials.py, snow lying on whatever faces the sky. Run directly for a
contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import style  # noqa: E402
from garden_props import PAD, rect_set, topdown_gable, topdown_roof  # noqa: E402
from materials import MATERIALS, WOOD, STONE, SNOW, GOLD, RED, NAP, SLATE  # noqa: E402

BRASS = MATERIALS['brass']
ICE = ['#7C9CB8', '#A6C2D8', '#C8DCEA', '#E6F0F7']


def bothy() -> Canvas:
    """A stone bothy, 84 x 74: a low shelter of rough-laid stone under a slate roof with
    snow on it, one small warm window, a plank door and a chimney; snow drifted against
    the gable end. Anyone may rest in it; it asks nothing."""
    w, h = 84, 74
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 41.5, 16, 40, 40, 70
    chim = rect_set(58, 4, 9, 14)
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 3, 80, SLATE, hole=chim, seed=811, moss=None)
    slope = (eave_y - apex_y) / (ridge - 3)
    for (x, y) in left | right:  # snow on the upper roof, rounded over its lower edge
        top = 1 + abs(x + 0.5 - ridge) * slope
        depth = 11 + int(noise2(x // 4, 2, 812) * 4)
        if y < top + depth:
            c = SNOW[3] if x < ridge else SNOW[2]
            if y + 1 >= top + depth:
                c = SNOW[1]
            cv.set(x, y, c)
    detail.stones(cv, 58, 8, 9, 10, STONE, seed=813, course=3)
    cv.rect(57, 4, 11, 4, SNOW[2]); cv.hline(57, 4, 11, SNOW[3])
    topdown_gable(cv, edge_y, 6, 77, apex_y, wall_top, STONE)
    detail.stones(cv, 6, wall_top, 72, wall_bottom - wall_top, STONE, seed=814, course=5)
    # the door: weathered planks in a stone frame, an iron latch
    for y in range(48, wall_bottom):
        for x in range(34, 48):
            c = WOOD[2] if (x - 34) % 4 else WOOD[1]
            if x == 34:
                c = WOOD[3]
            cv.set(x, y, c)
    cv.hline(33, 47, 16, STONE[4])
    cv.set(45, 58, MATERIALS['iron'][2])
    # one small window, warm inside
    for y in range(50, 58):
        for x in range(14, 24):
            edge = x in (14, 23) or y in (50, 57)
            cv.set(x, y, STONE[1] if edge else GOLD[3] if (x + y) % 3 else GOLD[4])
    cv.vline(18, 51, 6, WOOD[1])
    detail.overhang_shadow(cv, 6, 78, wall_top, lambda x: 3, k=2, cap=1)
    for (x, y) in oval(64, 70, 18, 4):  # a drift against the east end
        cv.set(x, y, SNOW[3] if y < 70 else SNOW[1])
    for (x, y) in oval(16, 71, 12, 3):
        cv.set(x, y, SNOW[2])
    return cv


def telescope() -> Canvas:
    """A coin-free brass viewing scope on a stone plinth, 22 x 36, tilted to the north."""
    cv = Canvas(22, 36, pad=PAD)
    for y in range(22, 36):  # the plinth, its top under snow
        for x in range(5, 17):
            cv.set(x, y, STONE[3] if x < 9 else STONE[2] if x < 15 else STONE[1])
    cv.hline(4, 22, 14, SNOW[3]); cv.hline(4, 23, 14, SNOW[2])
    for y in range(14, 22):
        cv.set(10, y, BRASS[3]); cv.set(11, y, BRASS[1])
    # the tube: up and to the right, the eyepiece low on the left, a lens catching sky
    for t in range(17):
        x, y = 4 + t, 15 - int(t * 0.55)
        for d in range(3):
            c = BRASS[4] if d == 0 else BRASS[3] if d == 1 else BRASS[1]
            cv.set(x, y + d, c)
    for d in range(4):
        cv.set(21, 5 + d, '#9FC7E6' if d < 2 else BRASS[2])
    cv.set(3, 15, BRASS[1]); cv.set(3, 16, BRASS[1])
    return cv


def trail_post() -> Canvas:
    """A trail post, 26 x 34: a weathered pole with two pointing boards, snow on the cap
    and on each board's top edge."""
    cv = Canvas(26, 34, pad=PAD)
    for y in range(3, 34):
        cv.set(12, y, WOOD[3]); cv.set(13, y, WOOD[1])
    for (y0, left) in ((8, False), (16, True)):
        x0 = 2 if left else 13
        for y in range(y0, y0 + 5):
            for x in range(x0, x0 + 11):
                tip = (x == x0 and left) or (x == x0 + 10 and not left)
                if tip and y in (y0, y0 + 4):
                    continue
                cv.set(x, y, WOOD[3] if y == y0 + 1 else WOOD[2] if y < y0 + 4 else WOOD[1])
        cv.hline(x0 + 1, y0, 9, SNOW[3])
        cv.hline(x0 + 3, y0 + 2, 5, WOOD[0])  # a carved name, too small to read
    for (x, y) in oval(12.5, 3, 2.5, 1.6):
        cv.set(x, y, SNOW[3])
    for (x, y) in oval(13, 33, 6, 1.6):
        cv.set(x, y, SNOW[2])
    return cv


def windsock() -> Canvas:
    """A windsock on a pole, 34 x 44, its striped sock streaming east on the saddle's wind."""
    cv = Canvas(34, 44, pad=PAD)
    for y in range(4, 44):
        cv.set(5, y, MATERIALS['iron'][3]); cv.set(6, y, MATERIALS['iron'][1])
    cv.rect(4, 3, 4, 2, MATERIALS['iron'][4])
    for t in range(26):
        x = 7 + t
        sag = int(t * t * 0.006)
        half = 4.5 - t * 0.09
        for dy in range(-int(half), int(half) + 1):
            y = 8 + sag + dy
            stripe = (t // 5) % 2
            c = RED[3] if stripe else '#F3E9D2'
            if dy == -int(half):
                c = RED[4] if stripe else '#FFFFFF'
            elif dy == int(half):
                c = RED[1] if stripe else '#BFAA86'
            cv.set(x, y, c)
    for (x, y) in oval(6, 43, 5, 1.4):
        cv.set(x, y, SNOW[2])
    return cv


def ibex() -> Canvas:
    """An ibex standing on a rock, 40 x 40, looking west: a stocky grey-brown goat with
    long ridged horns swept back, lit on its left."""
    cv = Canvas(40, 40, pad=PAD)
    rock = oval(20, 33, 17, 7) | oval(14, 34, 10, 6)
    rock = {(x, y) for (x, y) in rock if 0 <= y < 40}
    style.facet_stone(cv, rock, STONE, seed=821, outline=None)
    for (x, y) in rock:
        if (x, y - 1) not in rock:
            cv.set(x, y, SNOW[3])
    COAT = ['#4A3E34', '#6B5A4A', '#8C7762', '#AE977E']
    body = oval(21, 19, 9, 5)
    for (x, y) in body:
        cv.set(x, y, COAT[3] if y < 17 and x < 22 else COAT[2] if y < 21 else COAT[1])
    for (lx, top) in ((14, 22), (17, 22), (25, 22), (28, 22)):  # legs to the rock
        for y in range(top, 29):
            cv.set(lx, y, COAT[1] if lx > 20 else COAT[2])
    head = oval(11, 14, 3.6, 3)
    for (x, y) in head:
        cv.set(x, y, COAT[3] if x < 11 else COAT[2])
    for (x, y) in ((13, 16), (14, 17), (15, 17)):
        cv.set(x, y, COAT[2])  # the neck
    cv.set(9, 14, MATERIALS['iron'][0])
    cv.set(8, 17, COAT[0]); cv.set(9, 18, COAT[0])  # the beard
    for t in range(12):  # the horns: up and swept back in a long arc, ridged
        a = t / 11
        x, y = 12 + int(a * 9), 11 - int(math.sin(a * math.pi * 0.8) * 7)
        c = '#C9B48E' if t % 3 else '#8F7A58'
        cv.set(x, y, c); cv.set(x + 1, y, '#A8936C')
    return cv


def props() -> dict[str, Canvas]:
    return {
        'bothy': bothy(), 'telescope': telescope(), 'trail_post': trail_post(),
        'windsock': windsock(), 'ibex': ibex(),
    }


if __name__ == '__main__':
    from PIL import Image
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (226, 233, 240, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((width * 5, height * 5), Image.NEAREST)
    out.save(os.environ.get('FROST_PREVIEW', '/tmp/frost-props.png'))
    print('ok', list(items))
