"""Furniture for the nap hut's inside (living-world plan W4: the house you decorate).

The garden's rules indoors: warm wood lit from the upper left (the window side), soft
fabric in the nap violet and cream, the hearth's glow, a tinted outline. These are
the pieces a player will later place and move (C12); here they furnish a first room.
Run directly for a contact sheet: python3 scripts/art/home_props.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
from materials import MATERIALS, WOOD, STONE, LEAF, RED, GOLD, NAP  # noqa: E402

CREAM, PLASTER, WARM = MATERIALS['cream'], MATERIALS['plaster'], MATERIALS['lamplight']
LAVA = MATERIALS['lava']
CREAM_HI = '#FBF5E6'
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def wood_box(cv, x0, y0, w, h, top_h, ramp=WOOD):
    """A wooden piece seen from above at the room's angle: a lit top, a front face."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            top = y < y0 + top_h
            c = (ramp[4] if y == y0 else ramp[3]) if top else (ramp[2] if x < x0 + w - 2 else ramp[1])
            if x == x0 and not top:
                c = ramp[3]
            cv.set(x, y, c)
    cv.hline(x0, y0 + top_h, w, ramp[1])


def bed() -> Canvas:
    """A big wooden bed, 64 x 70: a carved headboard, two plump pillows, a patchwork
    quilt in nap violet and cream folded back, a knitted throw at its foot."""
    w, h = 64, 70
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 0, w - 4, 14, 4)
    for x in range(8, w - 8, 8):
        cv.vline(x, 6, 6, WOOD[1])
    for y in range(14, h - 4):  # the mattress and quilt
        for x in range(4, w - 4):
            if y < 28:
                c = CREAM_HI if x < w // 2 - 2 else CREAM[3]
            else:
                patch = ((x - 4) // 9 + (y - 28) // 9) % 3
                c = (NAP[3], CREAM[3], NAP[2])[patch]
                if (x - 4) % 9 == 0 or (y - 28) % 9 == 0:
                    c = NAP[1]  # the stitching
            if x > w - 8:
                c = NAP[1] if y >= 28 else CREAM[2]
            cv.set(x, y, c)
    for (px) in (17, 45):  # pillows
        for (x, y) in oval(px, 20, 10, 5):
            cv.set(x, y, '#FFFFFF' if x + y < px + 18 else CREAM_HI)
    for x in range(4, w - 4):  # the quilt's folded edge
        cv.set(x, 28, CREAM_HI); cv.set(x, 29, NAP[2])
    for y in range(h - 16, h - 6):  # a throw over the foot
        for x in range(6, w - 6):
            cv.set(x, y, GOLD[3] if (x + y) % 4 < 2 else GOLD[2])
    wood_box(cv, 2, h - 6, w - 4, 6, 2)
    return cv


def nightstand() -> Canvas:
    """A little nightstand, 22 x 30, with a lamp glowing warm and a book."""
    cv = Canvas(22, 30, pad=PAD)
    wood_box(cv, 2, 14, 18, 14, 4)
    cv.hline(8, 22, 6, WOOD[4])
    for (x, y) in oval(11, 6, 6, 4):
        cv.set(x, y, WARM[3] if y < 6 else WARM[2])
    cv.vline(11, 10, 4, GOLD[2])
    cv.hline(4, 15, 6, RED[3]); cv.hline(4, 16, 6, RED[2])
    return cv


def wardrobe() -> Canvas:
    """A tall wardrobe, 40 x 60: two panelled doors with brass knobs, a carved crown."""
    w, h = 40, 60
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 2, w - 4, h - 4, 5)
    for x0 in (6, w // 2 + 1):  # panels
        for y in range(12, h - 8):
            cv.set(x0, y, WOOD[1]); cv.set(x0 + w // 2 - 8, y, WOOD[3])
        cv.hline(x0, 12, w // 2 - 7, WOOD[1]); cv.hline(x0, h - 8, w // 2 - 7, WOOD[3])
    cv.set(w // 2 - 2, 32, GOLD[4]); cv.set(w // 2 + 2, 32, GOLD[4])
    cv.vline(w // 2, 7, h - 11, WOOD[0])
    return cv


def fireplace() -> Canvas:
    """The hearth, 64 x 56: a fieldstone chimney breast, a wooden mantel with a candle
    and a little clock, the fire burning low and orange inside the arch."""
    w, h = 64, 56
    cv = Canvas(w, h, pad=PAD)
    detail.stones(cv, 4, 0, w - 8, h - 4, STONE, seed=61, course=5)
    wood_box(cv, 2, 16, w - 4, 6, 2)
    arch = {(x, y) for (x, y) in disc(w // 2, 34, 13) if y >= 30} | rect_set(w // 2 - 13, 34, 26, 18)
    for (x, y) in arch:
        d = math.hypot(x - w // 2, y - 48)
        c = LAVA[5] if d < 3 else LAVA[4] if d < 6 else LAVA[3] if d < 9 else '#2A1A14' if d < 14 else '#1A1210'
        cv.set(x, y, c)
    for (x, y) in arch:
        if (x, y - 1) not in arch or (x - 1, y) not in arch or (x + 1, y) not in arch:
            cv.set(x, y, STONE[4] if x < w // 2 else STONE[1])
    for (x0) in (w // 2 - 7, w // 2 + 2):  # logs
        cv.hline(x0, 50, 6, WOOD[2]); cv.hline(x0, 51, 6, WOOD[1])
    cv.vline(10, 10, 6, CREAM_HI); cv.set(10, 9, WARM[3])  # a candle
    for (x, y) in disc(50, 12, 3):
        cv.set(x, y, GOLD[3] if x + y < 62 else GOLD[2])
    cv.set(50, 12, WOOD[0])
    detail.stones(cv, 0, h - 6, w, 6, STONE, seed=62, course=3)  # the hearthstone
    return cv


def armchair() -> Canvas:
    """A deep armchair, 40 x 40, in faded red with a cushion and a folded blanket."""
    w, h = 40, 40
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(20, 14, 16, 10):  # the back
        cv.set(x, y, RED[3] if x + y < 30 else RED[2])
    for (ax) in (4, w - 10):  # arms
        for y in range(14, h - 6):
            for x in range(ax, ax + 6):
                cv.set(x, y, RED[3] if x < ax + 3 else RED[1])
    for y in range(18, h - 6):  # the seat
        for x in range(10, w - 10):
            cv.set(x, y, RED[4] if y < 22 else RED[2])
    for (x, y) in oval(20, 22, 8, 4):
        cv.set(x, y, CREAM_HI if x < 20 else CREAM[3])
    for y in range(h - 6, h - 2):
        cv.set(6, y, WOOD[1]); cv.set(w - 7, y, WOOD[1])
    return cv


def pet_bed() -> Canvas:
    """The companion's bed by the fire, 38 x 24: a round woven basket with a soft
    cushion and a small blanket, where naps happen."""
    w, h = 38, 24
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(19, 13, 17, 10):
        k = (x - 2) / 34
        c = WOOD[4] if k < 0.3 else WOOD[3] if k < 0.7 else WOOD[2]
        if (x + y * 2) % 4 == 0:
            c = WOOD[2] if c != WOOD[2] else WOOD[1]  # the weave
        cv.set(x, y, c)
    for (x, y) in oval(19, 12, 13, 7):
        cv.set(x, y, NAP[3] if x + y < 30 else NAP[2])
    for (x, y) in oval(24, 13, 6, 3):
        cv.set(x, y, CREAM_HI if (x + y) % 3 else CREAM[3])
    return cv


def dining_table() -> Canvas:
    """A round kitchen table, 56 x 40, with a checked cloth, a teapot and two cups, and
    two chairs tucked in."""
    w, h = 56, 40
    cv = Canvas(w, h, pad=PAD)
    for (cx) in (8, w - 9):  # chairs
        for y in range(10, 30):
            for x in range(cx - 4, cx + 4):
                cv.set(x, y, WOOD[3] if y < 14 else WOOD[2] if x < cx + 2 else WOOD[1])
    for (x, y) in oval(28, 18, 20, 12):
        check = ((x // 4) + (y // 4)) % 2
        k = (x - 8) / 40 + (y - 6) / 24
        c = ('#E8E0D0' if check else RED[3]) if k < 1.1 else ('#C8C0B0' if check else RED[2])
        cv.set(x, y, c)
    for y in range(30, h - 2):
        cv.hline(26, y, 4, WOOD[1])
    for (x, y) in oval(28, 15, 5, 4):
        cv.set(x, y, '#6A8AA8' if x < 28 else '#4A6A88')
    cv.set(34, 13, '#4A6A88')
    for (mx) in (18, 38):
        for (x, y) in disc(mx, 19, 2):
            cv.set(x, y, CREAM_HI)
        cv.set(mx, 19, WOOD[1])
    return cv


def kitchen() -> Canvas:
    """The kitchen run along a wall, 104 x 50: a wooden counter with a stone sink and a
    window-box of herbs, an iron stove with a kettle, shelves of jars above."""
    w, h = 104, 50
    cv = Canvas(w, h, pad=PAD)
    for y in range(0, 14):  # the shelf of jars on the wall
        for x in range(4, w - 4):
            if y in (12, 13):
                cv.set(x, y, WOOD[3] if y == 12 else WOOD[1])
    for k in range(10):
        jx = 8 + k * 9
        col = (GOLD[3], RED[3], LEAF[3], CREAM_HI, NAP[3])[k % 5]
        for y in range(4, 12):
            for x in range(jx, jx + 5):
                cv.set(x, y, col if x < jx + 3 else MATERIALS['wood'][2] if y < 5 else col)
        cv.hline(jx, 3, 5, WOOD[4])
    wood_box(cv, 2, 20, 70, 28, 8)  # the counter
    for (x, y) in rect_set(36, 22, 18, 5):  # the sink
        cv.set(x, y, STONE[3] if y == 22 else STONE[2])
    cv.hline(38, 24, 14, '#6A8AA8')
    for k in range(4):  # herbs
        for (x, y) in disc(10 + k * 6, 22, 2.4):
            cv.set(x, y, LEAF[4] if x + y < 32 + k * 6 else LEAF[2])
    for y in range(22, 48):  # the stove
        for x in range(74, w - 4):
            c = MATERIALS['iron'][3] if y < 26 else MATERIALS['iron'][2] if x < w - 8 else MATERIALS['iron'][1]
            cv.set(x, y, c)
    for (x, y) in rect_set(80, 34, 16, 10):
        cv.set(x, y, LAVA[3] if (x + y) % 3 else LAVA[2])  # the firebox glow
    cv.hline(80, 33, 16, MATERIALS['iron'][4])
    for (x, y) in oval(86, 19, 6, 4):  # the kettle
        cv.set(x, y, '#C8803A' if x < 86 else '#9A5A28')
    cv.set(92, 17, '#9A5A28'); cv.hline(84, 15, 5, '#5E3A24')
    return cv


def bookcase() -> Canvas:
    """A wooden bookcase, 40 x 54: three shelves of books, a plant and a keepsake box."""
    w, h = 40, 54
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 2, w - 4, h - 4, 4)
    cols = [RED[3], GOLD[3], NAP[3], LEAF[3], '#6A8AA8', CREAM_HI, RED[2], NAP[2]]
    for shelf in range(3):
        y0 = 9 + shelf * 14
        for y in range(y0, y0 + 11):
            for x in range(5, w - 5):
                cv.set(x, y, WOOD[0])
        x, k = 6, shelf * 3
        while x < w - 7:
            bw = 2 + (k * 7) % 3
            bh = 8 + (k * 5) % 3
            for yy in range(y0 + 11 - bh, y0 + 11):
                for xx in range(x, min(x + bw, w - 6)):
                    cv.set(xx, yy, cols[k % len(cols)] if xx > x else WOOD[1])
            x += bw + (2 if k % 4 == 3 else 1)
            k += 1
        cv.hline(4, y0 + 11, w - 8, WOOD[3])
    for (x, y) in disc(30, 7, 3):
        cv.set(x, y, LEAF[4] if x + y < 37 else LEAF[2])
    return cv


def plant_tall() -> Canvas:
    """A tall leafy plant in a clay pot, 28 x 46."""
    w, h = 28, 46
    cv = Canvas(w, h, pad=PAD)
    for k in range(9):
        a = math.pi * (0.15 + 0.7 * k / 8)
        for t in range(18):
            x = 14 + math.cos(a) * t * 0.8
            y = 30 - math.sin(a) * t * 1.2 + (t / 18) ** 2 * 6
            for d in (-1, 0, 1):
                cv.set(int(x) + d, int(y), LEAF[4] if d < 0 and t > 4 else LEAF[3] if d == 0 else LEAF[2])
    for y in range(32, h - 2):
        hw = 7 - (y - 32) // 4
        for x in range(14 - hw, 14 + hw):
            cv.set(x, y, '#C8743E' if x < 13 else '#A85A2E')
    cv.hline(6, 32, 16, '#D88A50')
    return cv


def rug_chest() -> Canvas:
    """A painted chest for keepsakes, 36 x 26: flowers on its lid, iron bands."""
    w, h = 36, 26
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 4, w - 4, h - 6, 8, ramp=['#2A3A5A', '#3E5478', '#56709A', '#7290BA', '#94B0D4'])
    for (fx, c) in ((10, RED[3]), (18, GOLD[3]), (26, CREAM_HI)):
        for (x, y) in disc(fx, 8, 1.8):
            cv.set(x, y, c)
    for x0 in (6, w - 8):
        cv.vline(x0, 4, h - 6, MATERIALS['iron'][2])
    cv.set(w // 2, 15, GOLD[4])
    return cv


def window_seat() -> Canvas:
    """A cushioned bench, 64 x 22: violet cushions on a wooden box, a book left open."""
    w, h = 64, 22
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 8, w - 4, 12, 3)
    for cx in (14, 32, 50):
        for (x, y) in oval(cx, 7, 9, 4):
            cv.set(x, y, NAP[3] if x < cx else NAP[2])
    for (x, y) in rect_set(36, 4, 10, 4):
        cv.set(x, y, CREAM_HI if x < 41 else CREAM[3])
    cv.vline(41, 4, 4, WOOD[1])
    return cv


def desk() -> Canvas:
    """A writing desk, 44 x 34: letters and a pot of pens, a little lamp, a stool."""
    w, h = 44, 34
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 6, w - 4, 20, 8)
    for (x, y) in rect_set(8, 8, 10, 6):
        cv.set(x, y, CREAM_HI if (x + y) % 5 else CREAM[2])
    for (x, y) in rect_set(26, 6, 4, 5):
        cv.set(x, y, '#6A8AA8')
    cv.set(27, 4, RED[3]); cv.set(29, 3, GOLD[3])
    for (x, y) in oval(36, 4, 4, 3):
        cv.set(x, y, WARM[3] if y < 4 else WARM[2])
    for (x, y) in oval(22, 30, 6, 3):
        cv.set(x, y, WOOD[3] if x < 22 else WOOD[2])
    return cv

def props() -> dict[str, Canvas]:
    return {
        'bed': bed(), 'nightstand': nightstand(), 'wardrobe': wardrobe(), 'fireplace': fireplace(),
        'armchair': armchair(), 'pet_bed': pet_bed(), 'dining_table': dining_table(), 'kitchen': kitchen(),
        'bookcase': bookcase(), 'plant_tall': plant_tall(), 'keepsake_chest': rug_chest(),
        'window_seat': window_seat(), 'desk': desk(),
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
    for v in items.values():
        out.alpha_composite(v.img, (x, height - pad - v.h))
        x += v.w + pad
    out.resize((width * 3, height * 3), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else '/tmp/home_props.png')
