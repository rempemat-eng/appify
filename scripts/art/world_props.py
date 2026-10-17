"""Mission-world props at the step-7 density (docs/vision/coherence-plan.md).

Same rules as the garden (garden_props.py): light from the upper left, clean planes,
material-tinted outlines from style.finalize, colours only from art/materials.json,
and padded canvases so nothing is ever cut off. Sizes are in art pixels against the
32 x 32 companion: buildings are three to four companions tall, doors just taller
than the companion, benches and tables at companion height.
"""
from __future__ import annotations

from garden_props import PAD, canopy, plane, planks, rect_set, stone_blocks
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, RED, ROOF, SLATE, SNOW, STONE, WOOD, WTR
from pixel import Canvas, disc, noise2, oval
import style

BLUE_ROOF = WTR  # the bindery's slate-blue roof uses the water family


def roof_tiles(cv: Canvas, mask, ramp, row: int = 4):
    """Overlapping courses lit from the upper left: a lit lip on each course,
    staggered seams, a dark leading edge on the left and the turning right edge."""
    for (x, y) in mask:
        course = y // row
        seam = (x + (course % 2) * 4) % 8 == 0
        col = ramp[1] if seam else ramp[3] if y % row == 0 else ramp[2]
        if (x - 1, y) not in mask:
            col = ramp[1]
        elif (x + 1, y) not in mask:
            col = ramp[1]
        elif (x, y - 1) not in mask:
            col = ramp[4]
        cv.set(x, y, col)


def window(cv: Canvas, x, y, w, h, warm: bool = False):
    """A recessed window: timber frame, glazing with one highlight, a mullion and a sill."""
    plane(cv, rect_set(x, y, w, h), WOOD, 1, lit_edge=False)
    glass = rect_set(x + 2, y + 2, w - 4, h - 4)
    for (gx, gy) in glass:
        d = (gx - x - 2) + (gy - y - 2)
        cv.set(gx, gy, (GOLD[4] if d < 3 else GOLD[3]) if warm else (WTR[4] if d < 3 else WTR[2] if d > 6 else WTR[3]))
    cv.vline(x + w // 2, y + 2, h - 4, WOOD[2])
    if h >= 12:
        cv.hline(x + 2, y + h // 2, w - 4, WOOD[2])
    plane(cv, rect_set(x - 1, y + h, w + 2, 2), WOOD, 3)


def fountain() -> Canvas:
    """The park fountain, 56 x 48: a carved basin, a pillar and a two-tier spray."""
    cv = Canvas(56, 48, pad=PAD)
    basin = oval(28, 36, 26, 10)
    for (x, y) in basin:
        nx, ny = (x + 0.5 - 28) / 26, (y + 0.5 - 36) / 10
        lit = -0.6 * nx - 0.8 * ny
        cv.set(x, y, STONE[4] if lit > 0.75 else STONE[3] if lit > 0.1 else STONE[2] if lit > -0.6 else STONE[1])
    for (x, y) in oval(28, 34.5, 21, 6.5):
        cv.set(x, y, WTR[3] if y < 33 else WTR[2])
    cv.hline(13, 33, 6, WTR[4]); cv.hline(34, 36, 7, WTR[4])
    for x in (8, 18, 38, 48):  # carved joints on the rim
        cv.vline(x, 39 if x in (8, 48) else 42, 3, STONE[1])
    plane(cv, rect_set(25, 14, 7, 21), STONE, 3)
    cv.hline(25, 26, 7, STONE[2])
    for (x, y) in oval(28.5, 14, 9, 3.6):
        cv.set(x, y, STONE[3] if y < 14 else STONE[2])
    for (x, y) in oval(28.5, 13.5, 6, 2):
        cv.set(x, y, WTR[3])
    spray = [(28, 2), (28, 4), (27, 6), (29, 6), (24, 9), (33, 9), (21, 13), (36, 13), (19, 18), (38, 18)]
    for i, (x, y) in enumerate(spray):
        cv.set(x, y, WTR[4] if i % 2 else CREAM[3])
        cv.set(x, y + 1, WTR[3])
    for x in (15, 22, 34, 41):
        cv.set(x, 32, CREAM[3])
    cv.set(12, 38, RED[4]); cv.set(13, 38, RED[3])  # a fallen petal
    return cv


def bench() -> Canvas:
    """A park bench, 44 x 28: wooden slats between cast-iron ends."""
    cv = Canvas(44, 28, pad=PAD)
    for y in (2, 7):
        plane(cv, rect_set(2, y, 40, 4), WOOD, 3)
    plane(cv, rect_set(1, 14, 42, 5), WOOD, 3)
    cv.hline(1, 19, 42, WOOD[1])
    for x in (1, 39):
        plane(cv, rect_set(x, 1, 4, 26), SLATE, 1)
        cv.set(x + 1, 2, SLATE[3])
    cv.hline(12, 4, 4, WOOD[1]); cv.hline(26, 16, 5, WOOD[2])
    return cv


def lamp() -> Canvas:
    """A street lamp, 14 x 44: taller than the companion, a warm lantern on top."""
    cv = Canvas(14, 44, pad=PAD)
    plane(cv, rect_set(6, 12, 3, 30), SLATE, 1)
    plane(cv, rect_set(3, 40, 9, 3), SLATE, 1)
    plane(cv, rect_set(2, 2, 11, 10), SLATE, 0, lit_edge=False)
    for (x, y) in rect_set(4, 4, 7, 6):
        cv.set(x, y, GOLD[4] if x < 7 else GOLD[3])
    cv.vline(7, 4, 6, SLATE[0])
    cv.hline(1, 1, 13, SLATE[0]); cv.hline(4, 0, 7, SLATE[1])
    return cv


def hedge(w: int) -> Canvas:
    """A clipped hedge, w x 22: a row of leaf masses on a flat shaded body."""
    cv = Canvas(w, 22, pad=PAD)
    plane(cv, rect_set(0, 9, w, 12), LEAF, 2)
    canopy(cv, [(x, 9, 7.6) for x in range(5, w - 3, 9)], LEAF, seed=w)
    cv.hline(0, 20, w, LEAF[1])
    return cv


def library() -> Canvas:
    """The little library, 128 x 100: a tiled pediment over four columns, tall
    windows, a double door and three steps."""
    w, h = 128, 100
    cv = Canvas(w, h, pad=PAD)
    # facade: plaster plane with a flat cast shadow under the cornice
    plane(cv, rect_set(8, 38, 112, 50), CREAM, 2, dark_edge=False)
    for x in range(8, 120):
        cv.set(x, 38, CREAM[0]); cv.set(x, 39, CREAM[1]); cv.set(x, 40, CREAM[1])
    for x in range(110, 120):
        for y in range(41, 88):
            cv.set(x, y, CREAM[1])
    stone_blocks(cv, 6, 86, 116, 6, block=10)
    # columns: lit left flank, shaded right flank, capital and base
    for x in (16, 36, 82, 102):
        for y in range(42, 84):
            cv.set(x, y, CREAM[3]); cv.set(x + 1, y, CREAM[3])
            for xx in range(x + 2, x + 7):
                cv.set(xx, y, CREAM[2])
            cv.set(x + 7, y, CREAM[1]); cv.set(x + 8, y, CREAM[1])
        plane(cv, rect_set(x - 2, 40, 13, 3), CREAM, 2)
        plane(cv, rect_set(x - 2, 83, 13, 3), CREAM, 2)
    for x in (24, 92):
        window(cv, x + 2, 48, 10, 24)
    # double door with panels and brass handles
    plane(cv, rect_set(54, 56, 20, 30), WOOD, 1, lit_edge=False)
    for x0 in (56, 65):
        planks(cv, x0, 58, 8, 28, WOOD, step=4, vertical=True, base=2)
        plane(cv, rect_set(x0 + 1, 61, 6, 8), WOOD, 3)
        plane(cv, rect_set(x0 + 1, 73, 6, 8), WOOD, 3)
    cv.set(62, 72, GOLD[4]); cv.set(66, 72, GOLD[4])
    # pediment: tiled roof planes and a gable with the open-book sign
    roof = set()
    for y in range(2, 38):
        span = int((y - 2) * 1.72) + 4
        for x in range(w // 2 - span, w // 2 + span):
            roof.add((x, y))
    roof_tiles(cv, roof, ROOF)
    gable = set()
    for y in range(12, 36):
        span = int((y - 12) * 1.55)
        for x in range(w // 2 - span, w // 2 + span):
            gable.add((x, y))
    plane(cv, gable, CREAM, 2)
    plane(cv, rect_set(52, 22, 24, 12), WOOD, 1, lit_edge=False)
    for (x, y) in rect_set(54, 24, 20, 8):
        cv.set(x, y, CREAM[3] if x < 64 else CREAM[2])
    cv.vline(64, 24, 8, CREAM[0]); cv.vline(65, 30, 6, NAP[3])  # the lilac bookmark
    for x in range(56, 63, 2):
        cv.set(x, 27, CREAM[1])
    for x in range(67, 73, 2):
        cv.set(x, 27, CREAM[0])
    plane(cv, rect_set(0, 35, w, 4), CREAM, 2)
    # steps
    for i, y in enumerate((88, 92, 96)):
        plane(cv, rect_set(50 - i * 4, y, 28 + i * 8, 4), STONE, 3 if i % 2 == 0 else 2)
    cv.set(44, 99, LEAF[2]); cv.set(43, 98, LEAF[3])
    return cv


def house(roof=None, sign: bool = False) -> Canvas:
    """A town house, 80 x 76: a tiled gable roof, plaster walls, a door just taller
    than the companion, two windows with flower boxes."""
    roof = roof or ROOF
    w, h = 80, 76
    cv = Canvas(w, h, pad=PAD)
    plane(cv, rect_set(6, 34, 68, 36), CREAM, 2, dark_edge=False)
    for x in range(6, 74):
        cv.set(x, 34, CREAM[0]); cv.set(x, 35, CREAM[1])
    for x in range(68, 74):
        for y in range(36, 70):
            cv.set(x, y, CREAM[1])
    stone_blocks(cv, 4, 68, 72, 6, block=9)
    # door: 16 x 28
    plane(cv, rect_set(31, 40, 18, 30), WOOD, 1, lit_edge=False)
    planks(cv, 32, 42, 16, 28, WOOD, step=4, vertical=True, base=2)
    cv.set(45, 56, GOLD[4]); cv.set(45, 57, GOLD[2])
    for wx in (12, 54):
        window(cv, wx, 42, 14, 14, warm=sign)
        plane(cv, rect_set(wx - 1, 58, 16, 4), WOOD, 2)
        family = NAP if sign else RED
        for i, x in enumerate(range(wx, wx + 14, 3)):
            cv.set(x, 57, LEAF[3]); cv.set(x + 1, 57, LEAF[2])
            cv.set(x, 56, family[3] if i % 2 else GOLD[3]); cv.set(x + 1, 56, family[4])
    mask = set()
    for y in range(2, 35):
        span = int((y - 2) * 1.2) + 6
        for x in range(w // 2 - span, w // 2 + span):
            mask.add((x, y))
    roof_tiles(cv, mask, roof)
    plane(cv, rect_set(54, 0, 8, 14), STONE, 2)  # chimney
    plane(cv, rect_set(53, 0, 10, 3), STONE, 3)
    if sign:  # the bindery: a little book plaque under the eaves
        plane(cv, rect_set(30, 24, 20, 9), WOOD, 2)
        plane(cv, rect_set(33, 26, 14, 5), CREAM, 3)
        cv.vline(40, 26, 5, CREAM[0]); cv.vline(43, 30, 3, NAP[3])
    else:  # a folded curtain in the lived-in house
        cv.vline(15, 44, 6, RED[3]); cv.set(16, 49, RED[4])
    return cv


def cafe_table() -> Canvas:
    """A café table, 32 x 38: a striped umbrella over a round table and two chairs."""
    cv = Canvas(32, 38, pad=PAD)
    for y in range(2, 14):
        span = (y - 1) * 1.25 + 2
        for x in range(int(16 - span), int(16 + span)):
            stripe = (x // 4) % 2
            ramp = LEAF if stripe else CREAM
            cv.set(x, y, ramp[3] if y < 11 else ramp[1])
    cv.hline(1, 13, 30, WOOD[1])
    cv.set(15, 1, WOOD[4]); cv.set(16, 1, WOOD[2])
    plane(cv, rect_set(15, 14, 2, 14), SLATE, 2)
    for (x, y) in oval(16, 28, 10, 3.4):
        cv.set(x, y, CREAM[3] if y < 28 else CREAM[2])
    for x in (2, 25):  # chairs
        plane(cv, rect_set(x, 24, 5, 13), WOOD, 2)
        plane(cv, rect_set(x - 1, 30, 7, 3), WOOD, 3)
    plane(cv, rect_set(10, 24, 4, 4), CREAM, 3)  # a cup
    cv.set(14, 25, CREAM[1])
    plane(cv, rect_set(18, 25, 5, 3), RED, 3)  # a slice of cake
    return cv


def book_cart() -> Canvas:
    """A wooden book cart, 36 x 28, with a row of books and two wheels."""
    cv = Canvas(36, 28, pad=PAD)
    spines = [RED, WTR, LEAF, GOLD, NAP, RED, WTR, GOLD]
    for i, x in enumerate(range(3, 33, 4)):
        hgt = 9 + (i % 3) * 2
        plane(cv, rect_set(x, 12 - hgt + 4, 3, hgt), spines[i], 3)
        cv.set(x, 16 - hgt, CREAM[3])
    plane(cv, rect_set(1, 14, 34, 7), WOOD, 3)
    planks(cv, 2, 16, 32, 4, WOOD, step=8, vertical=True, base=2)
    for cx in (8, 28):
        for (x, y) in disc(cx, 23.5, 4):
            cv.set(x, y, SLATE[3] if (x - cx) + (y - 23.5) < -1 else SLATE[1])
        cv.set(cx, 23, WOOD[1])
    return cv


def cabin() -> Canvas:
    """The mountain cabin, 100 x 86: stacked logs under a snowy roof, warm windows."""
    w, h = 100, 86
    cv = Canvas(w, h, pad=PAD)
    for i, y in enumerate(range(38, 80, 5)):  # log courses with rounded ends
        plane(cv, rect_set(8, y, 84, 5), WOOD, 3 if i % 2 else 2)
        for x in (5, 92):
            for (lx, ly) in disc(x + 1.5, y + 2.5, 2.6):
                cv.set(lx, ly, WOOD[4] if lx < x + 1.5 else WOOD[2])
            cv.set(x + 1, y + 2, WOOD[1])
    plane(cv, rect_set(41, 52, 18, 28), WOOD, 0, lit_edge=False)
    planks(cv, 42, 53, 16, 27, WOOD, step=4, vertical=True, base=1)
    cv.set(55, 66, GOLD[4])
    window(cv, 16, 50, 16, 14, warm=True)
    window(cv, 68, 50, 16, 14, warm=True)
    roof = set()
    for y in range(4, 40):
        span = int((y - 4) * 1.42) + 6
        for x in range(w // 2 - span, w // 2 + span):
            roof.add((x, y))
    for (x, y) in roof:
        snowline = 18 + (x // 7) % 3 * 2 + (3 if 60 < x < 72 else 0)
        if y < snowline:
            col = SNOW[3] if (x, y - 1) in roof else SNOW[2]
            if x > w // 2 + 4:
                col = SNOW[2]
        elif y == snowline:
            col = SNOW[0]
        else:
            col = WOOD[3] if y % 4 == 0 else WOOD[1] if x > w // 2 else WOOD[2]
        cv.set(x, y, col)
    plane(cv, rect_set(66, 0, 10, 20), STONE, 2)
    plane(cv, rect_set(65, 0, 12, 3), SNOW, 2)
    for (x, y) in oval(50, 83, 46, 3.5):  # snow drifted against the front
        cv.set(x, y, SNOW[3] if y < 83 else SNOW[1])
    return cv


def campfire() -> Canvas:
    """A campfire, 26 x 22: a stone ring, crossed logs and a three-tone flame."""
    cv = Canvas(26, 22, pad=PAD)
    for (x, y) in oval(13, 17, 12, 4.4):
        cv.set(x, y, STONE[3] if (x + y) % 4 else STONE[1])
    for (x, y) in oval(13, 16.5, 8, 2.6):
        cv.set(x, y, STONE[0])
    plane(cv, rect_set(4, 14, 18, 3), WOOD, 2)
    plane(cv, rect_set(7, 12, 12, 3), WOOD, 3)
    flame = set()
    for y in range(1, 14):
        half = min(5.5, (y - 1) * 0.55 + 0.5)
        for x in range(int(13 - half), int(13 + half) + 1):
            flame.add((x, y))
    for (x, y) in flame:
        core = abs(x - 13) < 2 and y > 7
        cv.set(x, y, GOLD[4] if core else GOLD[3] if y > 5 else RED[3])
    return cv


def boulder(big: bool = True) -> Canvas:
    """A moss-capped boulder (36 x 26) or a field stone (20 x 14)."""
    w, h = (36, 26) if big else (20, 14)
    cv = Canvas(w, h, pad=PAD)
    pts = oval(w / 2, h / 2 + 1, w / 2 - 1, h / 2 - 1.4) | oval(w / 2 - 4, h / 2 + 2, w / 3, h / 2.6)
    pts = {(x, y) for (x, y) in pts if 0 <= x < w and 0 <= y < h}
    style.facet_stone(cv, pts, STONE, moss=LEAF if big else None, seed=w, outline=None)
    return cv


def cairn() -> Canvas:
    """A trail cairn, 20 x 34: stacked stones and a little lilac flag."""
    cv = Canvas(20, 34, pad=PAD)
    y = 32
    for (rw, rh) in ((18, 6), (14, 5), (11, 5), (8, 4), (6, 4)):
        stone = oval(10, y - rh / 2, rw / 2, rh / 2)
        for (x, yy) in stone:
            nx = (x + 0.5 - 10) / (rw / 2)
            ny = (yy + 0.5 - (y - rh / 2)) / (rh / 2)
            cv.set(x, yy, STONE[4] if -0.6 * nx - 0.8 * ny > 0.6 else STONE[3] if ny < 0.3 else STONE[2])
        y -= rh - 1
    plane(cv, rect_set(10, 2, 1, 10), WOOD, 1)
    plane(cv, rect_set(11, 2, 6, 4), NAP, 3)
    return cv


def duck() -> Canvas:
    """The park's duck, 14 x 10."""
    cv = Canvas(14, 10, pad=PAD)
    for (x, y) in oval(6.5, 6.5, 5.5, 3):
        cv.set(x, y, CREAM[3] if y < 6 else CREAM[2])
    for (x, y) in disc(10.5, 3, 2.3):
        cv.set(x, y, LEAF[2] if y < 3 else LEAF[1])
    cv.set(13, 3, GOLD[3]); cv.set(11, 2, STONE[0])
    cv.hline(3, 6, 4, CREAM[1])
    return cv


def bridge(w: int, h: int) -> Canvas:
    """A plank bridge (a flat decal) across a stream: planks across, rails along."""
    cv = Canvas(w, h, pad=PAD)
    planks(cv, 0, 5, w, h - 10, WOOD, step=5, vertical=True, base=2)
    for y0 in (1, h - 5):
        plane(cv, rect_set(0, y0, w, 4), WOOD, 2)
        for px in (0, w // 2 - 2, w - 5):
            plane(cv, rect_set(px, y0 - 1, 5, 6), WOOD, 3)
    return cv


def props() -> dict[str, Canvas]:
    import garden_props as gp
    return {
        'tree': gp.tree(True), 'tree_small': gp.tree(False), 'tree_autumn': gp.tree(True, True),
        'pine': gp.pine(), 'bush': gp.bush(), 'fountain': fountain(), 'bench': bench(), 'lamp': lamp(),
        'hedge': hedge(96), 'library': library(), 'house_red': house(ROOF),
        'house_blue': house(BLUE_ROOF, sign=True), 'cafe': cafe_table(), 'cart': book_cart(),
        'cabin': cabin(), 'campfire': campfire(), 'boulder': boulder(True), 'stone': boulder(False),
        'cairn': cairn(), 'duck': duck(),
    }


if __name__ == '__main__':
    import os
    from PIL import Image
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    G = MATERIALS['grass']
    out = Image.new('RGBA', (width, height), tuple(int(G[2][i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/world-props.png'))
    print('sheet', out.size)
