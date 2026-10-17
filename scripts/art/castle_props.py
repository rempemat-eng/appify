"""Props for Hearthold Castle on the headland above the harbour (world-atlas.md).

Big dressed ashlar stones lit from the upper left, crenellations seen from above
(the wall walk shows as a lit strip behind the merlons), slate cones on the round
towers, banners in the castle's sleepy violet and gold. The old ruler set fixed
hours for sleep: the bell tower still rings bedtime. Run directly for a sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, WOOD, NAP, GOLD, SLATE, LEAF, RED  # noqa: E402

ASHLAR, IRON = MATERIALS['ashlar'], MATERIALS['iron']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def ashlar(cv: Canvas, x0: int, y0: int, w: int, h: int, seed: int = 0):
    """Large dressed blocks in courses, each lit along its top and left edges."""
    for y in range(y0, y0 + h):
        course = (y - y0) // 6
        off = 7 if course % 2 else 0
        for x in range(x0, x0 + w):
            bx = (x - x0 + off) // 14
            n = noise2(bx, course, 311 + seed)
            base = 3 if n > 0.6 else 2 if n > 0.15 else 4
            cx, cy = (x - x0 + off) % 14, (y - y0) % 6
            c = ASHLAR[base]
            if cy == 5 or cx == 13:
                c = ASHLAR[1]
            elif cy == 0 or cx == 0:
                c = ASHLAR[min(5, base + 1)]
            cv.set(x, y, c)


def crenels(cv: Canvas, x0: int, x1: int, y: int):
    """A battlemented top seen from above: a lit wall walk with merlons standing proud."""
    for x in range(x0, x1):
        for k in range(7):
            cv.set(x, y + k, ASHLAR[4] if k < 2 else ASHLAR[3] if k < 5 else ASHLAR[1])
    for x in range(x0, x1, 8):
        for (mx, my) in rect_set(x, y - 4, 5, 5):
            if mx < x1:
                cv.set(mx, my, ASHLAR[5] if my == y - 4 else ASHLAR[4] if mx < x + 2 else ASHLAR[2])


def banner(cv: Canvas, x: int, y: int, h: int = 22, ramp=NAP, emblem=GOLD):
    """A hanging banner with a swallow-tailed hem and a moon emblem."""
    for yy in range(y, y + h):
        for xx in range(x, x + 9):
            tail = yy > y + h - 4 and (xx - x) in (3, 4, 5) and yy - (y + h - 4) > abs(xx - x - 4) - 1
            if tail:
                continue
            cv.set(xx, yy, ramp[3] if xx < x + 3 else ramp[2] if xx < x + 7 else ramp[1])
    cv.hline(x - 1, y, 11, WOOD[3])
    for (mx, my) in disc(x + 4, y + 8, 2.6):
        cv.set(mx, my, emblem[3])
    for (mx, my) in disc(x + 5, y + 7, 2):
        cv.set(mx, my, ramp[2])


def keep() -> Canvas:
    """The keep, 128 x 120: a battlemented roof walk seen from above with a slate-capped
    stair turret, an ashlar facade with tall arched windows lit warm, two banners, a
    great door under a pointed arch, and broad steps."""
    w, h = 128, 120
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rect_set(6, 10, w - 12, 22):  # the lead roof inside the battlements, in sheets
        cv.set(x, y, SLATE[1] if x % 10 == 0 else SLATE[3] if x % 10 == 1 else SLATE[2])
    crenels(cv, 4, w - 4, 10)
    crenels(cv, 4, w - 4, 30)
    for y in range(10, 37):
        for x in (4, 5, 6, w - 7, w - 6, w - 5):
            cv.set(x, y, ASHLAR[4] if x < 10 else ASHLAR[1])
    for (x, y) in disc(w - 24, 14, 11):  # the stair turret's slate cone, seen from above
        k = (x - (w - 24)) + (y - 14)
        cv.set(x, y, SLATE[4] if k < -6 else SLATE[3] if k < 2 else SLATE[2] if k < 8 else SLATE[1])
    cv.set(w - 24, 14, GOLD[4])
    ashlar(cv, 4, 37, w - 8, h - 49, seed=1)
    detail.overhang_shadow(cv, 4, w - 4, 37, lambda x: 3, k=2, cap=1)
    for wx in (16, w - 30):  # tall arched windows
        win = rect_set(wx, 50, 14, 22) | {(x, y) for (x, y) in disc(wx + 6.5, 50, 7) if y < 50}
        for (x, y) in win:
            cv.set(x, y, '#FFE7A6' if y < 58 else '#F0B85A')
        for (x, y) in win:
            if (x - 1, y) not in win or (x, y - 1) not in win:
                cv.set(x, y, ASHLAR[1])
        cv.vline(wx + 7, 46, 26, ASHLAR[1]); cv.hline(wx, 60, 14, ASHLAR[1])
    for bx in (38, w - 47):
        banner(cv, bx, 42, 26)
    door = rect_set(50, 74, 28, 28) | {(x, y) for y in range(58, 74) for x in range(50, 78) if abs(x - 63.5) < (y - 56) * 0.95}
    for (x, y) in door:
        cv.set(x, y, WOOD[2] if (x - 50) % 5 else WOOD[1])
    for (x, y) in door:
        for (ax, ay) in ((-2, 0), (2, 0), (0, -2), (-1, -1), (1, -1)):
            q = (x + ax, y + ay)
            if q not in door and q[1] < 102:
                cv.set(*q, ASHLAR[4] if q[0] < 64 else ASHLAR[2])
    for y in (80, 92):
        cv.hline(51, y, 26, IRON[2])
    cv.set(70, 86, GOLD[4])
    for k, (x0, wd) in enumerate(((44, 40), (40, 48), (36, 56))):  # the steps
        y = 102 + k * 4
        for yy in range(y, y + 4):
            cv.hline(x0, yy, wd, ASHLAR[4] if yy == y else ASHLAR[2] if yy < y + 3 else ASHLAR[1])
    detail.stones(cv, 2, h - 6, w - 4, 6, ASHLAR, seed=9, course=3)
    return cv


def round_tower(height: int = 96) -> Canvas:
    """A round wall tower, 48 x 96: a slate cone from above, an ashlar drum shaded as a
    cylinder with arrow slits, and a pennant on the cone's tip."""
    w, h = 48, height
    cv = Canvas(w, h, pad=PAD)
    cx = (w - 1) / 2
    for y in range(26, h - 2):
        for x in range(3, w - 3):
            k = (x - 3) / (w - 6)
            course = (y - 26) // 6
            base = 4 if k < 0.2 else 3 if k < 0.5 else 2 if k < 0.8 else 1
            c = ASHLAR[base]
            if (y - 26) % 6 == 5 or (x + course * 5) % 12 == 0:
                c = ASHLAR[max(0, base - 2)]
            cv.set(x, y, c)
    for sy in (44, 70):
        cv.rect(int(cx) - 1, sy, 3, 9, ASHLAR[0])
    for (x, y) in oval(cx, 22, 22, 9):  # the cone's eave
        if y >= 22:
            cv.set(x, y, SLATE[1])
    for y in range(4, 26):
        half = (y - 3) * 0.95
        for x in range(int(cx - half), int(cx + half) + 1):
            k = (x - cx) / max(1, half)
            band = (y - 4) % 4 == 3
            c = SLATE[4] if k < -0.5 else SLATE[3] if k < 0 else SLATE[2] if k < 0.5 else SLATE[1]
            if band:
                c = SLATE[max(0, SLATE.index(c) - 1)]
            cv.set(x, y, c)
    cv.vline(int(cx), 0, 5, WOOD[2])
    for y in range(0, 5):
        cv.hline(int(cx) + 1, y, 6 - y, NAP[3] if y < 2 else NAP[2])
    return cv


def wall_run(length: int = 96) -> Canvas:
    """A run of curtain wall, 96 x 44: battlements from above, then the ashlar face with
    a drip of moss at its foot."""
    cv = Canvas(length, 44, pad=PAD)
    crenels(cv, 0, length, 6)
    ashlar(cv, 0, 13, length, 29, seed=3)
    detail.overhang_shadow(cv, 0, length, 13, lambda x: 2, k=1, cap=1)
    for x in range(0, length):
        if noise2(x // 3, 0, 312) > 0.5:
            cv.set(x, 41, LEAF[2]); cv.set(x, 40, LEAF[1] if x % 2 else ASHLAR[2])
    return cv


def gatehouse() -> Canvas:
    """The gatehouse, 120 x 92: two drum towers flanking a gate arch with the portcullis
    raised, battlements between them and a banner over the arch."""
    w, h = 120, 92
    cv = Canvas(w, h, pad=PAD)
    crenels(cv, 24, 96, 20)
    ashlar(cv, 24, 27, 72, h - 31, seed=5)
    arch = rect_set(46, 54, 28, 34) | {(x, y) for (x, y) in disc(60, 54, 14) if y < 54}
    for (x, y) in arch:
        cv.set(x, y, '#2A2420' if y > 60 else '#3A3230')
    for x in range(47, 74, 4):  # the raised portcullis teeth
        cv.vline(x, 41, 8, IRON[2]); cv.set(x, 48, IRON[4])
    cv.hline(46, 44, 28, IRON[1])
    for (x, y) in arch:
        for (ax, ay) in ((-2, 0), (2, 0), (0, -2)):
            q = (x + ax, y + ay)
            if q not in arch and q[1] < 88:
                cv.set(*q, ASHLAR[4] if q[0] < 60 else ASHLAR[2])
    banner(cv, 56, 28, 12)
    for tx in (0, w - 48):
        tw = round_tower(80)
        for y in range(tw.h):
            for x in range(tw.w):
                c = tw.get(x, y)
                if c[3]:
                    cv.set(tx + x, h - 82 + y, c)
    return cv


def bell_tower() -> Canvas:
    """The bedtime bell tower, 44 x 120: a square ashlar shaft, an open belfry with a
    bronze bell, a pyramidal slate roof seen from above and a moon weathervane."""
    w, h = 44, 120
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, 30):
        half = 2 + (y - 6) * 0.85
        for x in range(int(22 - half), int(22 + half) + 1):
            cv.set(x, y, SLATE[3] if x < 21 else SLATE[1] if x > 23 else SLATE[4])
    for (mx, my) in disc(22, 3, 2.4):
        cv.set(mx, my, GOLD[4])
    for (mx, my) in disc(23, 2, 1.8):
        cv.set(mx, my, (0, 0, 0, 0))
    ashlar(cv, 4, 30, 36, h - 34, seed=7)
    for (x, y) in rect_set(10, 34, 24, 22):  # the open belfry
        cv.set(x, y, '#2A2420')
    for (x, y) in oval(22, 46, 7, 9):
        if y > 38:
            cv.set(x, y, '#C99A3C' if x < 20 else '#9E6C26' if x < 26 else '#6E4718')
    cv.hline(14, 54, 17, '#6E4718'); cv.set(22, 55, '#3E2812')
    cv.hline(9, 33, 26, WOOD[3])
    for y in (68, 92):
        cv.rect(20, y, 4, 10, ASHLAR[0])
    door = rect_set(16, h - 20, 12, 16)
    for (x, y) in door:
        cv.set(x, y, WOOD[2] if x < 22 else WOOD[1])
    return cv


def herb_bed() -> Canvas:
    """A raised stone bed of castle herbs, 48 x 22: lavender, sage and chamomile in rows."""
    w, h = 48, 22
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rect_set(1, 4, w - 2, 16):
        cv.set(x, y, ASHLAR[3] if y < 7 else ASHLAR[2] if x < 4 or x > w - 5 or y > 16 else '#5A3826')
    cv.hline(1, 4, w - 2, ASHLAR[5])
    for i, x in enumerate(range(6, w - 6, 5)):
        kind = i % 3
        for (px, py) in disc(x, 10, 2.4):
            if kind == 0:
                cv.set(px, py, NAP[3] if (px + py) % 2 else NAP[2])  # lavender
            elif kind == 1:
                cv.set(px, py, '#8FA88A' if py < 10 else '#6E8A6A')  # sage
            else:
                cv.set(px, py, LEAF[3] if (px + py) % 3 else '#F4F0DC')  # chamomile
        cv.set(x, 13, LEAF[1])
    return cv


def training_dummy() -> Canvas:
    """A straw training dummy on a post with a wooden shield, 26 x 40."""
    cv = Canvas(26, 40, pad=PAD)
    gp.post(cv, 12, 18, 40, w=3, ramp=WOOD)
    for (x, y) in oval(13, 14, 7, 9):
        cv.set(x, y, '#E2BC5E' if x < 12 else '#C99A3C' if x < 16 else '#A87E2C')
    for (x, y) in disc(13, 4, 4):
        cv.set(x, y, '#E2BC5E' if x < 13 else '#C99A3C')
    cv.hline(5, 14, 17, '#7A5A22')
    for (x, y) in oval(20, 22, 4, 5):
        cv.set(x, y, RED[3] if x < 20 else RED[2])
    cv.vline(20, 18, 9, GOLD[3])
    return cv


def props() -> dict[str, Canvas]:
    return {
        'keep': keep(), 'round_tower': round_tower(), 'wall_run': wall_run(), 'gatehouse': gatehouse(),
        'bell_tower': bell_tower(), 'herb_bed': herb_bed(), 'training_dummy': training_dummy(),
    }


if __name__ == '__main__':
    from PIL import Image
    import style
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
    out.save(os.environ.get('SHEET', '/tmp/castle-props.png'))
    print('sheet', out.size)
