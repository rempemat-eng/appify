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
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, WOOD  # noqa: E402

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


def forge() -> Canvas:
    """A smithy built into the rock, 96 x 80: a slab roof of iron plates seen from above,
    a stone face with a glowing furnace mouth, an anvil, a quench trough, bellows and a
    chimney trailing ember sparks."""
    w, h = 96, 80
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, 28):  # iron plate roof
        for x in range(4, w - 4):
            plate = (x // 12 + y // 8) % 2
            cv.set(x, y, IRON[3] if plate else IRON[2])
            if x % 12 == 0 or y % 8 == 0:
                cv.set(x, y, IRON[1])
            if x % 12 == 2 and y % 8 == 2:
                cv.set(x, y, IRON[4])  # rivets
    cv.hline(4, 6, w - 8, IRON[4]); cv.hline(4, 28, w - 8, IRON[0])
    for y in range(0, 14):  # the chimney
        for x in range(70, 80):
            cv.set(x, y, BASALT[3] if x < 74 else BASALT[2])
    cv.rect(69, 0, 12, 2, BASALT[4])
    for (sx, sy) in ((74, -2), (78, -5), (71, -7)):
        cv.set(sx, sy + 8, LAVA[4])
    detail.stones(cv, 4, 28, w - 8, 44, BASALT, seed=31, course=5, base=2)
    detail.overhang_shadow(cv, 4, w - 4, 29, lambda x: 4, k=2, cap=2)
    mouth = {(x, y) for (x, y) in disc(30, 52, 13) if y >= 46} | rect_set(17, 52, 27, 18)
    for (x, y) in mouth:
        d = math.hypot(x - 30, y - 58)
        cv.set(x, y, LAVA[5] if d < 4 else LAVA[4] if d < 8 else LAVA[3] if d < 11 else LAVA[2])
    for (x, y) in mouth:
        for (ax, ay) in ((-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0), (0, -2)):
            q = (x + ax, y + ay)
            if q not in mouth and ay <= 0:
                cv.set(*q, ASH[3] if q[0] < 30 else ASH[1])
    for (x, y) in rect_set(4, 66, w - 8, 6):  # the glow spills on the floor stones
        if (x + y) % 2 == 0 and abs(x - 30) < 22:
            cv.set(x, y, LAVA[2])
    # the anvil and quench trough
    for (x, y) in rect_set(56, 52, 18, 5):
        cv.set(x, y, IRON[4] if y == 52 else IRON[2])
    cv.rect(61, 57, 8, 8, IRON[1]); cv.rect(58, 64, 14, 3, IRON[2])
    for (x, y) in rect_set(78, 58, 14, 8):
        cv.set(x, y, WOOD[2] if y > 59 else WOOD[4])
    cv.hline(80, 59, 10, '#3E5468')
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


def ember_shrine() -> Canvas:
    """A shrine of stacked basalt with a brazier on top, 30 x 50: the keeper's warning
    to rest before you burn out."""
    cv = Canvas(30, 50, pad=PAD)
    for k, (y0, wd) in enumerate(((38, 26), (28, 20), (20, 14))):
        for y in range(y0, y0 + 10):
            for x in range(15 - wd // 2, 15 + wd // 2):
                cv.set(x, y, BASALT[3] if y == y0 else BASALT[2] if x < 15 else BASALT[1])
    for (x, y) in oval(15, 18, 7, 2.5):
        cv.set(x, y, IRON[3] if y < 18 else IRON[1])
    for (x, y) in oval(15, 12, 4, 6):
        if y < 18:
            d = abs(x - 15) + (y - 12) * 0.3
            cv.set(x, y, LAVA[5] if d < 1.2 else LAVA[4] if d < 2.5 else LAVA[3])
    return cv


CHAR = ['#1A1412', '#2A201C', '#3E302A', '#58443A', '#76604E']  # charred cedar
LANTERN = ['#7A3A12', '#C2621E', '#F2A048', '#FFE0A0']


def bathhouse() -> Canvas:
    """The bathhouse, 108 x 86: a low hall of charred cedar boards (dark, burnt to keep
    them sound) under a broad roof of basalt slates seen from above, a wide eave with
    lanterns hanging warm, sliding screens glowing, a deck of boards out front with
    buckets and a stack of folded towels. The calm end of the fire country."""
    w, h = 108, 86
    cv = Canvas(w, h, pad=PAD)
    ridge = (w - 1) / 2
    for y in range(4, 40):  # the slate roof: a hipped slope, lit on the upper left
        inset = max(0, 18 - y) * 2
        for x in range(2 + inset, w - 2 - inset):
            left = x < ridge
            row = (y - 4) // 4
            c = BASALT[3] if left else BASALT[2]
            if y < 12:
                c = BASALT[4] if left else BASALT[3]
            if (x + row * 3) % 7 == 0 or (y - 4) % 4 == 0:
                c = BASALT[1]
            cv.set(x, y, c)
    cv.hline(2, 40, w - 4, BASALT[4]); cv.hline(2, 41, w - 4, BASALT[0])
    for y in range(42, 72):  # the charred board wall
        for x in range(8, w - 8):
            c = CHAR[2] if (x // 5) % 2 else CHAR[1]
            if x % 5 == 0:
                c = CHAR[0]
            if (x * 3 + y) % 23 == 0:
                c = CHAR[3]  # the char's silvery sheen
            cv.set(x, y, c)
    for y in range(42, 46):  # the eave's shadow
        for x in range(8, w - 8):
            if (x + y) % 2 or y < 44:
                cv.set(x, y, CHAR[0])
    for sx in (16, 40, 68, 90):  # sliding screens, warm behind a lattice
        if sx == 40:
            continue
        for y in range(48, 68):
            for x in range(sx, sx + 14 if sx != 68 else sx + 16):
                lat = (x - sx) % 5 == 0 or (y - 48) % 5 == 0
                cv.set(x, y, CHAR[3] if lat else LANTERN[3] if y < 56 else LANTERN[2])
    for y in range(48, 72):  # the open door, steam within
        for x in range(42, 62):
            cv.set(x, y, '#2E2624' if (x + y) % 3 else '#4A403C')
    for (lx) in (12, 34, 74, 96):  # lanterns on the eave
        for (x, y) in oval(lx, 47, 3, 4):
            cv.set(x, y, LANTERN[3] if x < lx else LANTERN[2] if y < 49 else LANTERN[1])
        cv.set(lx, 42, CHAR[0]); cv.set(lx, 51, LANTERN[0])
    for y in range(72, 84):  # the deck
        for x in range(4, w - 4):
            c = WOOD[3] if (y - 72) % 4 else WOOD[1]
            if y == 72:
                c = WOOD[4]
            cv.set(x, y, c)
    for (bx) in (14, 22):  # buckets
        for (x, y) in oval(bx, 76, 3, 2.5):
            cv.set(x, y, WOOD[4] if x < bx else WOOD[2])
        cv.hline(bx - 3, 75, 7, IRON[3])
    for k in range(4):  # folded towels
        cv.hline(84, 80 - k * 2, 12, '#F2EEE6' if k % 2 else '#D8D2C6')
        cv.hline(84, 79 - k * 2, 12, '#C8A0A0' if k == 3 else '#F2EEE6')
    return cv


def fireweed(tall: bool = True) -> Canvas:
    """Fireweed, 20 x 30 (or 16 x 22): the first plant back on burnt ground, tall stems
    of pink-magenta flower spikes over narrow leaves."""
    w, h = (20, 30) if tall else (16, 22)
    cv = Canvas(w, h, pad=PAD)
    PINKS = ['#7A2A5A', '#B0407E', '#D86AA2', '#F2A0C8']
    for k in range(4 if tall else 3):
        bx = 3 + k * 4
        top = 2 + (k * 7) % 6
        for y in range(top, h - 1):
            cv.set(bx + (1 if y > h - 8 and k % 2 else 0), y, '#447A50' if y > top + 8 else '#62995E')
        for y in range(top, top + 9):
            if (y + k) % 2 == 0:
                cv.set(bx - 1, y, PINKS[3] if y < top + 3 else PINKS[2])
                cv.set(bx + 1, y, PINKS[1])
            else:
                cv.set(bx, y, PINKS[2])
        for y in range(top + 11, h - 2, 4):  # narrow leaves
            cv.set(bx - 1, y, '#2E5A40'); cv.set(bx + 1, y + 1, '#447A50')
    return cv


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

def props() -> dict[str, Canvas]:
    return {
        'basalt_columns': basalt_columns(5, 0), 'basalt_columns_low': basalt_columns(3, 7), 'forge': forge(),
        'obsidian': obsidian_rock(True), 'obsidian_small': obsidian_rock(False), 'cooling_vent': cooling_vent(),
        'basalt_bridge': basalt_bridge(), 'ember_shrine': ember_shrine(),
        'bathhouse': bathhouse(), 'fireweed': fireweed(True), 'fireweed_small': fireweed(False),
        'stone_lantern': stone_lantern(),
    }


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
