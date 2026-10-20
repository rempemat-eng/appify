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
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
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


# ---- firs (art-faults A2: Fir Hollow's old wood) --------------------------------------------
# A second conifer beside the garden's pine, so a clump mixes shapes, drawn at Eastward's level
# of detail (its pines in shots 13, 22 and 37 at our scale): tiers of rounded needle clumps,
# each clump lit on its upper-left rim, a mid body with needle dashes, a dark underside that
# reads as the gap to the tier below, ragged drooping tips; the clumps' hues vary a little
# (teal, olive) so a crown is not one green; the east flank sits in shade. Four shapes and
# sizes: an old broad fir (~4 adults), an old narrow one with a broken top, a young fir (~2)
# and a sapling, each with a snowy variant for the upper slope (snow resting on each clump).
FIR = ['#101B1D', '#18292A', '#203A33', '#2B4D3D', '#3A6347', '#4D7A51', '#67955E', '#8BB271', '#B1CD8B']
FIR_TEAL = ['#0F1C20', '#172C2F', '#1F3D3A', '#295047', '#36665A', '#477D69', '#5F9878', '#83B58C', '#A9D0A2']
FIR_OLIVE = ['#141C18', '#1F2B22', '#2C3D2C', '#3B5034', '#4F663C', '#668045', '#839C52', '#A6B868', '#C8D488']


def _fir(w: int, h: int, trunk_h: int, layers: int, trunk_w: int, seed: int, narrow: float = 1.0,
         broken: bool = False) -> Canvas:
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2 - 0.5 + (noise2(seed, 1, 970) - 0.5) * 1.5
    crown_b = h - trunk_h + 2          # the lowest tier's tips hide the trunk's top
    tx = int(round(cx - trunk_w / 2 + 0.5))
    style.trunk(cv, tx, crown_b - 6, h, trunk_w, WOOD)
    hw_max = (w / 2 - 2) * narrow
    top = 4 if broken else 1
    span_y = crown_b - top - 2
    clumps = []                        # (cx, cy, rx, ry, tier, ramp)
    for i in range(layers):            # tier i from the top
        f = (i + 0.6) / layers
        ty = top + int(span_y * f ** 1.08)
        hw = max(1.8, hw_max * (0.06 + 0.94 * f ** 0.95) + (noise2(i, seed, 971) - 0.5) * 2.0)
        ry = max(1.8, min(4.2, span_y / layers * 0.78))
        n = max(1, int(round(2 * hw / 8.0)))
        for k in range(n):
            u = (k + 0.5) / n * 2 - 1 if n > 1 else 0.0          # -1 west .. 1 east
            u += (noise2(k, i, seed + 978) - 0.5) * 0.25 / n
            ccx = cx + u * (hw - 2.5)
            rx = max(2.2, min(7.0, hw / n * 1.15 + 0.8)) * (0.85 + 0.3 * noise2(k, i, seed + 979))
            ccy = ty + abs(u) ** 1.4 * ry * 0.8                   # the outer sprays droop
            r = noise2(k, i, seed + 980)
            ramp = FIR_TEAL if r < 0.16 else FIR_OLIVE if r > 0.95 else FIR
            sgn = 0 if n == 1 or abs(u) < 0.2 else (1 if u > 0 else -1)
            clumps.append((ccx, ccy, rx, ry * (0.9 + 0.25 * noise2(k, i, seed + 981)), i, ramp, abs(u), sgn))
    # the tip: a narrow spire of two little clumps (or a broken top: a bare snag)
    if broken:
        for y in range(0, top + 2):
            cv.set(int(cx), y, WOOD[2] if y % 3 else WOOD[1])
        cv.set(int(cx) + 1, 1, WOOD[1])
    else:
        clumps.insert(0, (cx, top + 1.5, 1.4, 2.4, -1, FIR, 0, 0))
    # draw from the back: the centre of each tier first, then outward, lower tiers over upper
    order = sorted(clumps, key=lambda c: (c[4], c[6]))
    for (ccx, ccy, rx, ry, i, R, au, sgn) in order:
        px = []
        for y in range(int(ccy - ry) - 3, int(ccy + ry) + 6):
            for x in range(int(ccx - rx) - 1, int(ccx + rx) + 2):
                dx = (x + 0.5 - ccx) / rx
                # a spray of needles sweeping down and out from the trunk (the centre sprays sag
                # at both ends), so each tier reads as a shelf of branches, not a ball
                bend = 0.9 * dx * sgn if sgn else 0.5 * dx * dx
                dy = (y + 0.5 - ccy) / ry - bend * (rx / ry) * 0.35
                rough = (noise2(x, y, seed + 982) - 0.5) * 0.35
                if dy > 0:                                         # ragged, drooping tips below
                    tip = noise2(x, i, seed + 983) > 0.55
                    if dx * dx + (dy / (1.5 if tip else 1.0)) ** 2 > 1 + rough:
                        continue
                elif dx * dx + dy * dy > 1 + rough:
                    continue
                elif dx * dx + dy * dy > 0.62 and (x + int(ccy)) % 4 == 0 and dy < 0.2:
                    continue                                      # needle tips: a serrated top edge
                if 0 <= x < w and y >= 0:
                    px.append((x, y, dx, dy))
        S_ = set((x, y) for (x, y, _a, _b) in px)
        east = (ccx - cx) / max(1.0, hw_max)                      # the crown's east flank in shade
        for (x, y, dx, dy) in px:
            lv = -0.55 * dx - 0.75 * dy - 0.45 * east + 0.1 - 0.08 * max(0, i) / max(1, layers)
            lv += (smooth_noise(x, y, 3, seed + 984) - 0.5) * 0.3
            t = 6 if lv > 0.7 else 4 if lv > -0.05 else 3 if lv > -0.45 else 1   # four broad bands: dense crowns stay clean
            if (x, y + 1) not in S_ or dy > 0.7:
                t = min(t, 2) if dy > 0.3 else t                  # the underside: dark, the gap below
                if (x, y + 1) not in S_:
                    t = 1 if dx > -0.3 else 2
            if (x, y - 1) not in S_ and dx < 0.35 and dy < 0:
                t = 7 if east < 0.2 else 6                        # the lit rim, upper left
                if dx < -0.35 and noise2(x // 2, y, seed + 985) > 0.5:
                    t = 8
            cv.set(x, y, R[t])
        # needle dashes in the body: a lit stroke over a dark one, two px each, sloping down
        for k in range(int(rx * ry / 2.0)):
            x = int(ccx - rx * 0.6 + noise2(k, i, seed + 986) * rx * 1.1)
            y = int(ccy - ry * 0.2 + noise2(k, i, seed + 987) * ry * 0.8)
            if (x, y) in S_ and (x + 1, y + 1) in S_ and (x, y + 2) in S_:
                lit = x < ccx
                c = R[6] if lit and east < 0.3 else R[5] if lit else R[3]
                cv.set(x, y, c); cv.set(x + 1, y, c)
                cv.set(x, y + 1, R[2]); cv.set(x + 1, y + 1, R[2])
    return cv


def _snowed(cv: Canvas, trunk_h: int) -> Canvas:
    """Snow lying on every shelf top open to the sky (as valley_props.snowy_pine): lit on
    the west, blue in shade on the east, a second row where the shelf is deep."""
    lum = lambda c: c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11  # noqa: E731
    snow = []
    for y in range(-cv.pad + 1, cv.h - trunk_h):
        for x in range(-cv.pad, cv.w + cv.pad):
            c, above = cv.get(x, y), cv.get(x, y - 1)
            if c[3] and (not above[3] or lum(c) - lum(above) > 30):
                snow.append((x, y))
    for (x, y) in snow:
        lit = x < cv.w / 2
        cv.set(x, y, SNOW[3] if lit else SNOW[1])
        if noise2(x, y, 978) > 0.4 and cv.get(x, y + 1)[3]:
            cv.set(x, y + 1, SNOW[2] if lit else SNOW[0])
    return cv


def fir_old() -> Canvas:
    """An old fir, 46 x 102: broad, nine tiers of needle clumps, a trunk with root flare."""
    return _fir(46, 102, 16, 9, 6, 1)


def fir_tall() -> Canvas:
    """An old fir, 38 x 108: narrow, ten tiers, its top broken off to a bare snag."""
    return _fir(38, 108, 15, 10, 5, 4, narrow=0.88, broken=True)


def fir_young() -> Canvas:
    """A young fir, 30 x 60: six tiers, still dense to the ground."""
    return _fir(30, 60, 9, 6, 4, 2)


def fir_sapling() -> Canvas:
    """A fir sapling, 16 x 28, about knee to shoulder height on an adult."""
    return _fir(16, 28, 5, 4, 2, 3)


def props() -> dict[str, Canvas]:
    return {
        'bothy': bothy(), 'telescope': telescope(), 'trail_post': trail_post(),
        'windsock': windsock(), 'ibex': ibex(),
        'fir_old': fir_old(), 'fir_tall': fir_tall(), 'fir_young': fir_young(), 'fir_sapling': fir_sapling(),
        'fir_old_snow': _snowed(fir_old(), 16), 'fir_tall_snow': _snowed(fir_tall(), 15),
        'fir_young_snow': _snowed(fir_young(), 9),
        'fir_sapling_snow': _snowed(fir_sapling(), 5),
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
