"""Mission-world props at the step-7 density (docs/vision/coherence-plan.md).

Same rules as the garden (garden_props.py): light from the upper left, the material
detail and depth rules of scripts/art/detail.py (coherence plan, 6c), material-tinted
outlines from style.finalize, colours only from art/materials.json, and padded
canvases so nothing is ever cut off. Sizes are in art pixels against the
32 x 32 companion: buildings are three to four companions tall, doors just taller
than the companion, benches and tables at companion height.
"""
from __future__ import annotations

import detail
from garden_props import PAD, canopy, plane, planks, post, rect_set, stone_blocks
from garden_props import window as shuttered_window
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, PLASTER, RED, ROOF, SLATE, SNOW, STONE, WOOD, WTR
from pixel import Canvas, disc, noise2, oval
import style

BLUE_ROOF = WTR  # the bindery's slate-blue roof uses the water family


def gable_roof(cv: Canvas, mask, ramp, apex_x: float, y0: int, seed: int = 0):
    """A pitched roof seen from the front: shingles lit on the left plane and a step
    darker on the right, a ridge line, and lit and shaded verges along the slopes."""
    left = {(x, y) for (x, y) in mask if x < apex_x}
    right = set(mask) - left
    detail.shingles(cv, left, ramp, 3, y0, seed=seed)
    detail.shingles(cv, right, ramp, 2, y0, seed=seed + 1)
    for (x, y) in left:
        if (x - 1, y) not in mask:
            cv.set(x, y, ramp[4]); cv.set(x + 1, y, ramp[3])
    for (x, y) in right:
        if (x + 1, y) not in mask:
            cv.set(x, y, ramp[0]); cv.set(x - 1, y, ramp[1])
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, ramp[4] if x < apex_x else ramp[3])


def window(cv: Canvas, x, y, w, h, warm: bool = False):
    """A window in the shared style (garden_props.window), without shutters."""
    shuttered_window(cv, x, y, w, h, shutters=None, warm=warm)


def fountain() -> Canvas:
    """The park fountain, 56 x 48: a basin of dressed stone whose rim shows its lit top
    and whose outer wall turns from the light, water shaded under the far rim, a round
    pillar, an upper bowl and a two-tier spray."""
    cv = Canvas(56, 48, pad=PAD)
    outer = oval(28, 36, 26, 10)
    for (x, y) in outer:  # the basin's outer wall, stone blocks, darker to the right
        k = 2 if x < 34 else 1
        cv.set(x, y, STONE[k + (1 if x < 14 else 0)])
        if (x - 3) % 9 == 0 and y > 36:
            cv.set(x, y, STONE[0])
    for (x, y) in oval(28, 33.5, 26, 8.5):  # the rim's top surface, lit
        nx = (x + 0.5 - 28) / 26
        cv.set(x, y, STONE[4] if nx < -0.2 else STONE[3])
    water = oval(28, 33.5, 22, 6.2)
    for (x, y) in water:
        far = (x, y - 2) not in water
        cv.set(x, y, WTR[1] if far else WTR[2] if y < 35 else WTR[3])
    cv.hline(12, 34, 5, WTR[4]); cv.hline(36, 37, 6, WTR[4]); cv.set(20, 36, WTR[4])
    for x in range(4, 53):  # the rim's lip over the wall
        for y in range(36, 46):
            if (x, y) in outer and (x, y - 1) not in outer | oval(28, 33.5, 26, 8.5):
                cv.set(x, y, STONE[1])
    # a round pillar and the upper bowl
    for y in range(14, 35):
        for i, t in enumerate((3, 4, 4, 3, 2, 2, 1)):
            cv.set(25 + i, y, STONE[t])
    for (x, y) in oval(28.5, 14, 9, 3.6):
        cv.set(x, y, STONE[4] if x < 26 else STONE[3] if y < 14 else STONE[2])
    for (x, y) in oval(28.5, 13.5, 6, 2):
        cv.set(x, y, WTR[3])
    cv.hline(20, 17, 17, STONE[1])  # the bowl's shadow on the pillar
    spray = [(28, 2), (28, 4), (27, 6), (29, 6), (24, 9), (33, 9), (21, 13), (36, 13), (19, 18), (38, 18)]
    for i, (x, y) in enumerate(spray):
        cv.set(x, y, WTR[4] if i % 2 else PLASTER[5])
        cv.set(x, y + 1, WTR[3])
    for x in (15, 22, 34, 41):
        cv.set(x, 32, PLASTER[5])
    cv.set(12, 40, RED[4]); cv.set(13, 40, RED[3])  # a fallen petal
    return cv


def bench() -> Canvas:
    """A park bench, 44 x 28: slats that show a lit top and a darker face between round
    cast-iron ends."""
    cv = Canvas(44, 28, pad=PAD)
    for y in (2, 7):
        cv.hline(2, y, 40, WOOD[4]); cv.hline(2, y + 1, 40, WOOD[3]); cv.hline(2, y + 2, 40, WOOD[2])
        cv.hline(2, y + 3, 40, WOOD[1])
    for y in range(14, 19):
        cv.hline(1, y, 42, WOOD[4] if y % 2 == 0 else WOOD[3])
    for x in range(1, 43):
        detail.shade(cv, x, 14, 1)
    cv.hline(1, 19, 42, WOOD[2]); cv.hline(1, 20, 42, WOOD[0])
    for x in (1, 39):
        post(cv, x, 1, 27, w=4, ramp=SLATE)
    cv.hline(12, 4, 4, WOOD[1]); cv.hline(26, 16, 5, WOOD[2])
    return cv


def lamp() -> Canvas:
    """A street lamp, 14 x 44: a round iron post, a glowing lantern with its frame and a
    cap that shows its top."""
    cv = Canvas(14, 44, pad=PAD)
    post(cv, 6, 12, 41, w=3, ramp=SLATE)
    cv.rect(3, 40, 9, 3, SLATE[2]); cv.hline(3, 40, 9, SLATE[4]); cv.hline(3, 42, 9, SLATE[0])
    cv.rect(2, 2, 11, 10, SLATE[1]); cv.vline(2, 2, 10, SLATE[2])
    for (x, y) in rect_set(4, 4, 7, 6):
        d = abs(x - 6.5) + abs(y - 7)
        cv.set(x, y, GOLD[4] if d < 2 else GOLD[3] if d < 4 else GOLD[2])
    cv.vline(7, 4, 6, SLATE[0]); cv.set(5, 5, PLASTER[5])
    cv.hline(1, 1, 13, SLATE[2]); cv.hline(1, 2, 13, SLATE[0]); cv.hline(4, 0, 7, SLATE[3])
    cv.hline(3, 12, 9, SLATE[1])
    return cv


def hedge(w: int) -> Canvas:
    """A clipped hedge, w x 22: a row of leaf masses on a flat shaded body."""
    cv = Canvas(w, 22, pad=PAD)
    plane(cv, rect_set(0, 9, w, 12), LEAF, 2)
    canopy(cv, [(x, 9, 7.6) for x in range(5, w - 3, 9)], LEAF, seed=w)
    cv.hline(0, 20, w, LEAF[1])
    return cv


def library() -> Canvas:
    """The little library, 128 x 100: a shingled pediment over round columns that cast
    shadows on the ashlar wall, tall windows, a recessed double door and steps that show
    their treads and risers."""
    w, h = 128, 100
    cv = Canvas(w, h, pad=PAD)
    wall = rect_set(8, 38, 112, 48)
    detail.stones(cv, 8, 38, 112, 48, PLASTER, seed=3, course=6, base=4)
    for x in range(110, 120):
        for y in range(38, 86):
            detail.shade(cv, x, y, 1)  # the side turning from the light
    detail.stones(cv, 6, 86, 116, 6, STONE, seed=4, course=3, moss=LEAF)
    for x in (24, 92):
        window(cv, x + 2, 48, 10, 24)
    # recessed double door with panels and brass handles
    door = rect_set(54, 56, 20, 30)
    cv.rect(52, 54, 24, 2, PLASTER[5]); cv.vline(52, 54, 32, PLASTER[5]); cv.vline(75, 54, 32, PLASTER[2])
    detail.boards(cv, door, WOOD, 2, 56, board=4, vertical=True, x0=54, joints=False, grain=0.05)
    for x0 in (56, 65):
        for py in (61, 73):
            cv.rect(x0 + 1, py, 6, 8, WOOD[3]); cv.hline(x0 + 1, py, 6, WOOD[4]); cv.vline(x0 + 1, py, 8, WOOD[4])
            cv.hline(x0 + 1, py + 7, 6, WOOD[1]); cv.vline(x0 + 6, py + 1, 7, WOOD[1])
    cv.vline(63, 56, 30, WOOD[0])
    cv.set(62, 72, GOLD[4]); cv.set(66, 72, GOLD[4])
    detail.recess(cv, door, depth=2, k=1)
    # round columns with capitals and bases, casting shadows on the wall
    cols = set()
    for x in (16, 36, 82, 102):
        for y in range(43, 83):
            for i, t in enumerate((4, 5, 5, 4, 4, 3, 3, 2, 1)):
                cv.set(x + i, y, PLASTER[t])
            cols |= {(x + i, y) for i in range(9)}
        for (cy, top) in ((40, True), (83, False)):
            cv.rect(x - 2, cy, 13, 3, PLASTER[4]); cv.hline(x - 2, cy, 13, PLASTER[5])
            cv.hline(x - 2, cy + 2, 13, PLASTER[2]); cv.set(x + 10, cy + 1, PLASTER[3])
            cols |= rect_set(x - 2, cy, 13, 3)
    detail.cast(cv, cols, 1, 1, k=2, on=PLASTER, reach=3)
    # the cornice: a lit top, a face and a deep shadow on the wall below it
    cv.rect(0, 35, w, 4, PLASTER[4]); cv.hline(0, 35, w, PLASTER[5]); cv.hline(0, 38, w, PLASTER[2])
    detail.overhang_shadow(cv, 8, 120, 39, lambda x: 2 + (x - 8) // 40, k=2, cap=2)
    # pediment: shingled planes and a tympanum with the open-book sign
    roof = set()
    for y in range(2, 35):
        span = int((y - 2) * 1.72) + 4
        for x in range(w // 2 - span, w // 2 + span):
            roof.add((x, y))
    gable_roof(cv, roof, ROOF, w / 2, 2, seed=5)
    gable = set()
    for y in range(12, 35):
        span = int((y - 12) * 1.55)
        for x in range(w // 2 - span, w // 2 + span):
            gable.add((x, y))
    for (x, y) in gable:
        cv.set(x, y, PLASTER[4] if x < w // 2 else PLASTER[3])
    for (x, y) in gable:  # the raking cornice shades the tympanum below it
        if (x, y - 1) not in gable or (x, y - 2) not in gable:
            detail.shade(cv, x, y, 2)
    cv.rect(52, 22, 24, 12, WOOD[1]); cv.hline(52, 22, 24, WOOD[3]); cv.vline(52, 22, 12, WOOD[3])
    for (x, y) in rect_set(54, 24, 20, 8):
        cv.set(x, y, PLASTER[5] if x < 64 else PLASTER[4])
    cv.vline(64, 24, 8, PLASTER[1]); cv.vline(65, 30, 6, NAP[3])  # the lilac bookmark
    for x in range(56, 63, 2):
        cv.set(x, 27, PLASTER[2])
    for x in range(67, 73, 2):
        cv.set(x, 27, PLASTER[1])
    # steps: each tread lit, each riser a step darker
    for i, y in enumerate((88, 92, 96)):
        x0, sw = 50 - i * 4, 28 + i * 8
        cv.rect(x0, y, sw, 2, STONE[4]); cv.rect(x0, y + 2, sw, 2, STONE[2])
        cv.vline(x0 + sw - 1, y, 4, STONE[1])
    cv.set(44, 99, LEAF[2]); cv.set(43, 98, LEAF[3])
    return cv


def house(roof=None, sign: bool = False) -> Canvas:
    """A town house, 80 x 76: a shingled gable roof over painted siding in the eave's
    shadow, a brick chimney, a recessed door just taller than the companion, windows
    with shutters and flower boxes, and a fieldstone footing."""
    roof = roof or ROOF
    w, h = 80, 76
    cv = Canvas(w, h, pad=PAD)
    detail.bricks(cv, 54, 0, 8, 14, ROOF if roof is not ROOF else STONE, seed=w)
    cv.rect(53, 0, 10, 2, STONE[3]); cv.hline(53, 0, 10, STONE[4])
    detail.boards(cv, rect_set(6, 34, 62, 36), PLASTER, 4, 34, seed=11, joints=False)
    detail.boards(cv, rect_set(68, 34, 6, 36), PLASTER, 3, 34, seed=12, joints=False)
    detail.stones(cv, 4, 68, 72, 6, STONE, seed=13, course=3, moss=LEAF)
    # door: a frame proud of the wall, the door recessed inside it
    door = rect_set(32, 42, 16, 26)
    cv.rect(30, 40, 20, 28, WOOD[2]); cv.hline(30, 40, 20, WOOD[4]); cv.vline(30, 40, 28, WOOD[3])
    cv.vline(49, 41, 27, WOOD[1])
    detail.boards(cv, door, WOOD, 3 if not sign else 2, 42, board=4, vertical=True, x0=32, joints=False, grain=0.05)
    detail.recess(cv, door, depth=2, k=1)
    cv.set(45, 56, GOLD[4]); cv.set(45, 57, GOLD[2])
    proud = rect_set(30, 40, 20, 28)
    family = NAP if sign else RED
    for wx in (12, 54):
        shuttered_window(cv, wx, 42, 14, 14, shutters=None if sign else NAP, warm=sign, sill=False)
        cv.rect(wx - 1, 56, 16, 4, WOOD[2]); cv.hline(wx - 1, 56, 16, WOOD[4]); cv.hline(wx - 1, 59, 16, WOOD[1])
        for i, x in enumerate(range(wx, wx + 14, 3)):
            cv.set(x, 55, LEAF[3]); cv.set(x + 1, 55, LEAF[2])
            cv.set(x, 54, family[3] if i % 2 else GOLD[3]); cv.set(x + 1, 54, family[4])
        proud |= rect_set(wx - 1, 56, 16, 4)
        if not sign:
            proud |= rect_set(wx - 4, 42, 4, 14) | rect_set(wx + 14, 42, 4, 14)
    detail.cast(cv, proud, 1, 1, k=2, on=PLASTER, reach=2)
    mask = set()
    for y in range(2, 35):
        span = int((y - 2) * 1.2) + 6
        for x in range(w // 2 - span, w // 2 + span):
            mask.add((x, y))
    mask -= {(x, y) for x in range(53, 63) for y in range(0, 14) if x > w // 2}
    gable_roof(cv, mask, roof, w / 2, 2, seed=7 if sign else 9)
    for x in range(0, w):  # the eave and its shadow on the siding
        if cv.get(x, 34)[3] and (x, 33) in mask:
            pass
    detail.overhang_shadow(cv, 6, 74, 34, lambda x: 3 + (x - 6) // 24, k=2, cap=1)
    if sign:  # the bindery: a little book plaque under the eaves
        cv.rect(30, 24, 20, 9, WOOD[2]); cv.hline(30, 24, 20, WOOD[4]); cv.hline(30, 32, 20, WOOD[1])
        cv.rect(33, 26, 14, 5, PLASTER[5]); cv.vline(40, 26, 5, PLASTER[2]); cv.vline(43, 30, 3, NAP[3])
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
    """The mountain cabin, 100 x 86: round logs (a lit top, a dark underside) with ringed
    ends at the corners, a snowy roof over wooden shingles, warm windows, a recessed door
    and snow drifted against the front."""
    w, h = 100, 86
    cv = Canvas(w, h, pad=PAD)
    for i, y in enumerate(range(38, 80, 5)):
        for x in range(8, 92):
            for r, t in enumerate((4, 3, 3, 2, 1)):
                tt = t - (1 if x > 84 else 0)
                if r == 2 and noise2(x // 3, y, 51) < 0.08:
                    tt -= 1
                cv.set(x, y + r, WOOD[max(0, tt)])
        for x in (5, 92):  # log ends with rings, lit toward the upper left
            for (lx, ly) in disc(x + 1.5, y + 2.5, 2.6):
                cv.set(lx, ly, WOOD[4] if lx + ly < x + y + 3.5 else WOOD[3])
            cv.set(x + 1, y + 2, WOOD[1]); cv.set(x + 2, y + 2, WOOD[2])
    door = rect_set(42, 53, 16, 27)
    cv.rect(40, 51, 20, 29, WOOD[1]); cv.hline(40, 51, 20, WOOD[3]); cv.vline(40, 51, 29, WOOD[2])
    detail.boards(cv, door, WOOD, 2, 53, board=4, vertical=True, x0=42, joints=False, grain=0.06)
    detail.recess(cv, door, depth=2, k=1)
    cv.set(55, 66, GOLD[4])
    window(cv, 16, 50, 16, 14, warm=True)
    window(cv, 68, 50, 16, 14, warm=True)
    roof = set()
    for y in range(4, 40):
        span = int((y - 4) * 1.42) + 6
        for x in range(w // 2 - span, w // 2 + span):
            roof.add((x, y))
    roof -= {(x, y) for x in range(66, 76) for y in range(0, 20)}
    snow = {(x, y) for (x, y) in roof if y < 18 + (x // 7) % 3 * 2 + (3 if 60 < x < 72 else 0)}
    gable_roof(cv, roof - snow, WOOD, w / 2, 4, seed=21)
    for (x, y) in snow:
        lit = x < w // 2
        col = SNOW[3] if lit else SNOW[2]
        if (x, y + 1) not in snow:
            col = SNOW[1]  # the snow's lower edge, rounded over the shingles
        elif (x, y - 1) not in snow:
            col = SNOW[3]
        cv.set(x, y, col)
    for (x, y) in roof - snow:
        if (x, y - 1) in snow:
            detail.shade(cv, x, y, 2)  # the snow's shadow on the shingles
    detail.stones(cv, 66, 2, 10, 18, STONE, seed=22, course=3)
    cv.vline(66, 2, 18, STONE[3])
    cv.rect(65, 0, 12, 3, SNOW[2]); cv.hline(65, 0, 12, SNOW[3])
    detail.overhang_shadow(cv, 8, 92, 38, lambda x: 2 + (x - 8) // 30, k=2, cap=1)
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
