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
from materials import MATERIALS, WOOD, STONE, LEAF, RED, WTR, PLASTER, GOLD, NAP, SLATE, G  # noqa: E402

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


def props() -> dict[str, Canvas]:
    return {
        'willow': willow(), 'reeds': reeds(), 'water_mill': water_mill(), 'heron': heron(), 'lily_pads': lily_pads(),
        'mossy_log': mossy_log(), 'mushroom_ring': mushroom_ring(), 'hollow_tree': hollow_tree(), 'fern': fern(),
        'forest_bench': forest_bench(), 'bandstand': bandstand(), 'ice_cream_cart': ice_cream_cart(),
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
