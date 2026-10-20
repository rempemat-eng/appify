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
from garden_props import despeckle, keep_foot as gp_keep_foot
from garden_props import LEAF_SUN, G
from garden_props import PAD, arched_door, canopy, plane, planks, post, rect_set, stone_blocks, topdown_gable, topdown_roof
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


def _slat(cv: Canvas, x0: int, y: int, length: int, top: bool, seed: int, vertical: bool = False):
    """One timber slat with grain: a lit face (top) or a darker edge, a streak of grain
    now and then, and a nail head near each end."""
    for i in range(length):
        x, yy = (x0, y + i) if vertical else (x0 + i, y)
        c = WOOD[4] if top else WOOD[2]
        if noise2(i // 3, y + x0, seed) > 0.72:
            c = WOOD[3] if top else WOOD[1]  # grain
        cv.set(x, yy, c)
    for i in (2, length - 3):
        x, yy = (x0, y + i) if vertical else (x0 + i, y)
        cv.set(x, yy, SLATE[1])


SHADE = (20, 26, 22, 96)  # a contact shadow under a seat, laid over whatever ground it stands on


def bench(facing: str = 'south') -> Canvas:
    """A park bench at the scale table's size (verticality.md 5: seat 7, back 13, length 32),
    timber slats with grain and nail heads on cast-iron ends, a contact shadow under the
    seat. facing 'south' looks at the camera; 'east' or 'west' turns it side-on to face a
    view (its length runs up the screen, foreshortened to 20 px, the back on the far side).
    Each is re-seated in the old 44 x 28 box (keep_foot), so its foot stays put."""
    if facing == 'south':
        cv = Canvas(32, 14, pad=PAD)
        for y in (0, 3):  # the back: two rails between the iron back posts
            _slat(cv, 2, y, 28, True, 31 + y)
            _slat(cv, 2, y + 1, 28, False, 41 + y)
        for y, top in ((5, True), (6, True), (7, False)):  # the seat seen from above, its front edge
            _slat(cv, 1, y, 30, top, 51 + y)
        cv.hline(1, 6, 30, WOOD[3]); cv.hline(1, 8, 30, WOOD[1])
        for x in range(2, 30):  # a contact shadow under the seat
            for y in (12, 13):
                cv.set(x, y, SHADE)
        for x0 in (1, 28):  # cast-iron ends: back post, arm scroll, front leg, foot
            lit = x0 == 1
            for y in range(0, 14):
                if y < 5:
                    cv.set(x0 + 1, y, SLATE[3] if lit else SLATE[2])
                elif y == 5:
                    cv.hline(x0, y, 3, SLATE[4] if lit else SLATE[3])  # the arm
                else:
                    cv.set(x0, y, SLATE[3] if lit else SLATE[1]); cv.set(x0 + 2, y, SLATE[2] if lit else SLATE[0])
            cv.set(x0 + 1, 9, SLATE[1]); cv.set(x0 + 1, 10, SLATE[2])  # the stretcher between the legs
            cv.hline(x0 - 1, 13, 5, SLATE[1])
        return gp_keep_foot(cv, 44, 27)
    # side-on: the bench runs up the screen (32 foreshortened to 20), so the seat shows as a
    # strip of slats seen from above, the back as a thin rail rising on the far side, and the
    # near cast-iron end faces the camera in profile: back post, arm scroll, seat, front leg
    flip = facing == 'west'
    cv = Canvas(12, 34, pad=PAD)
    for y in range(28, 34):  # the contact shadow under the seat, east of the frame
        for x in range(4, 11):
            cv.set(x, y, SHADE)
    for y in range(13, 28):
        for x in (9, 10):
            cv.set(x, y, SHADE)
    for i, x in enumerate(range(4, 10)):  # the seat seen from above, slats running its length
        _slat(cv, x, 6, 20, i % 2 == 0, 61 + i, vertical=True)
    cv.hline(4, 6, 6, WOOD[4])
    cv.hline(4, 26, 6, WOOD[2]); cv.hline(4, 27, 6, WOOD[1])  # the near end's edge
    for i, x in enumerate((2, 3)):  # the back's rail, standing up behind the seat
        _slat(cv, x, 0, 21, i == 0, 71 + i, vertical=True)
    for y in (4, 12):
        cv.set(1, y, SLATE[3]); cv.set(1, y + 1, SLATE[2])  # the back's far stays
    for y in range(20, 34):  # the near iron end in profile
        cv.set(1 + (y > 27), y, SLATE[3])  # the back post, kinking back at the seat
    for x in range(1, 10):
        cv.set(x, 22, SLATE[4] if x < 5 else SLATE[3])  # the arm
    cv.set(10, 22, SLATE[2]); cv.set(10, 23, SLATE[2]); cv.set(9, 24, SLATE[1])  # its scroll
    for y in range(24, 34):
        cv.set(9, y, SLATE[2])  # the front leg
        if y > 28:
            cv.set(10, y, SLATE[0])
    for x in range(2, 10, 2):
        cv.set(x, 30, SLATE[1])  # the stretcher
    cv.hline(0, 33, 4, SLATE[1]); cv.hline(8, 33, 4, SLATE[1])  # the feet
    if flip:
        out = Canvas(12, 34, pad=PAD)
        src = cv.img.load(); p = cv.pad
        for y in range(cv.h + 2 * p):
            for x in range(cv.w + 2 * p):
                c = src[x, y]
                if c[3]:
                    out.set(cv.w - 1 - (x - p), y - p, c)
        cv = out
    return gp_keep_foot(cv, 44, 27)


def lamp() -> Canvas:
    """A street lamp at the scale table's size (verticality.md 5: 56 tall): a fluted iron
    post on a stepped plinth, a collar and a ladder bar under the lantern, a glowing
    lantern with its frame, and a cap that shows its top. The lantern keeps its place at
    the sprite's top (the renderer's light, LAMPS.lamp, is measured from there); the post
    reaches 12 px further down, re-seated in the old 14 x 44 box (keep_foot)."""
    cv = Canvas(14, 56, pad=PAD)
    post(cv, 6, 12, 50, w=3, ramp=SLATE)
    for y in range(16, 48, 4):
        cv.set(7, y, SLATE[2])  # the post's fluting
    cv.rect(5, 19, 5, 2, SLATE[3]); cv.hline(5, 19, 5, SLATE[4]); cv.hline(5, 21, 5, SLATE[1])  # a collar
    cv.hline(2, 14, 11, SLATE[2]); cv.set(2, 15, SLATE[1]); cv.set(12, 15, SLATE[1])  # the ladder bar
    cv.rect(4, 47, 7, 3, SLATE[2]); cv.hline(4, 47, 7, SLATE[4]); cv.vline(10, 47, 3, SLATE[0])
    cv.rect(3, 50, 9, 3, SLATE[2]); cv.hline(3, 50, 9, SLATE[3]); cv.hline(3, 52, 9, SLATE[1])
    cv.rect(2, 53, 11, 3, STONE[2]); cv.hline(2, 53, 11, STONE[4]); cv.hline(2, 55, 11, STONE[1])  # the stone plinth
    cv.rect(2, 2, 11, 10, SLATE[1]); cv.vline(2, 2, 10, SLATE[2])
    for (x, y) in rect_set(4, 4, 7, 6):
        d = abs(x - 6.5) + abs(y - 7)
        cv.set(x, y, GOLD[4] if d < 2 else GOLD[3] if d < 4 else GOLD[2])
    cv.vline(7, 4, 6, SLATE[0]); cv.set(5, 5, PLASTER[5])
    cv.hline(1, 1, 13, SLATE[2]); cv.hline(1, 2, 13, SLATE[0]); cv.hline(4, 0, 7, SLATE[3])
    cv.hline(3, 12, 9, SLATE[1])
    return gp_keep_foot(cv, 14, 42)


def _leaf_cluster(x: int, y: int, su: float, sv: float, seed: int):
    """Which clump of leaves a point lies in (a jittered grid of sites about su x sv apart,
    each row shifted, so no clump lines up with the next) and where in it: returns the
    clump's id and the point's offset from its middle."""
    best = None
    gy = int(y // sv)
    for j in (gy - 1, gy, gy + 1):
        off = noise2(j, 1, seed) * su
        gx = int((x - off) // su)
        for i in (gx - 1, gx, gx + 1):
            px = (i + 0.2 + noise2(i, j, seed + 1) * 0.6) * su + off
            py = (j + 0.2 + noise2(i, j, seed + 2) * 0.6) * sv
            d = (x - px) ** 2 + ((y - py) * su / sv) ** 2
            if best is None or d < best[0]:
                best = (d, (i, j), x - px, y - py)
    return best[1], best[2], best[3]


def hedge(w: int) -> Canvas:
    """A clipped hedge, w x 22: a flat clipped top of leaf clumps lit from the upper left,
    a front face of clumps in four tones that darkens toward the foot, dark pockets where
    the twigs show through, rounded ends (the west end lit, the east end turned from the
    light, verticality.md 4f), a few blossoms, and grass growing against its dark foot."""
    cv = Canvas(w, 22, pad=PAD)
    top0, face0, foot = 1, 8, 21

    def inside(x, y):
        r = 3  # the rounded ends
        if x < r:
            return (r - x) ** 2 + max(0, top0 + r - y) ** 2 <= r * r + 1 or y >= top0 + r
        if x > w - 1 - r:
            return (x - (w - 1 - r)) ** 2 + max(0, top0 + r - y) ** 2 <= r * r + 1 or y >= top0 + r
        return True

    for y in range(top0, foot + 1):
        for x in range(w):
            if not inside(x, y):
                continue
            on_top = y < face0
            cid, dx, dy = _leaf_cluster(x, y, 4.2 if on_top else 3.6, 2.4 if on_top else 3.0, 811 if on_top else 812)
            lam = -dx * 0.5 - dy * 0.6  # lit on each clump's upper left
            t = (3 if on_top else 2) + (1 if lam > 0.9 else -1 if lam < -0.9 else 0)
            if noise2(*cid, 813) > 0.8:
                t += 1  # a clump that catches more sun
            if not on_top:
                t -= (y - face0) // 5  # darker toward the foot
                if noise2(*cid, 814) > 0.88 and lam < 0:
                    t = 0  # a pocket where the twigs show
            if x < 2:
                t += 1  # the lit west end
            elif x > w - 3:
                t -= 1  # the east end, turned from the light
            c = LEAF[max(0, min(4, t))]
            if t >= 4 and on_top:
                c = LEAF_SUN.get(LEAF[4], LEAF[4]) if noise2(x, y, 815) > 0.55 else LEAF[4]
            cv.set(x, y, c)
    for x in range(1, w - 1):  # the crease where the clipped top meets the face
        if noise2(x, 0, 816) > 0.35:
            cv.set(x, face0, LEAF[1])
    for x in range(w):  # the dark foot, with grass against it
        cv.set(x, foot, LEAF[0]); cv.set(x, foot - 1, LEAF[0] if noise2(x, 2, 817) > 0.4 else LEAF[1])
        if noise2(x, 3, 818) > 0.7:
            cv.set(x, foot, G[3]); cv.set(x, foot - 1, G[4] if x % 2 else G[3])
    for k in range(w // 14):  # a few blossoms on the face
        bx = 4 + int(noise2(k, 4, 819) * (w - 8))
        by = face0 + 2 + int(noise2(k, 5, 819) * 6)
        cv.set(bx, by, PLASTER[5]); cv.set(bx + 1, by, PLASTER[4] if k % 2 else RED[4])
    return cv


def library() -> Canvas:
    """The little library, 128 x 100, in the steep top-down view: a tiled roof seen from
    above over a plaster pediment with the open-book sign, round columns that cast
    shadows on the ashlar wall, tall windows, a recessed double door and steps that show
    their treads and risers."""
    w, h = 128, 100
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 63.5, 24, 50, 50, 86
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 1, 126, ROOF, seed=41, moss=None)
    gable = topdown_gable(cv, edge_y, 6, 121, apex_y, wall_top, PLASTER, boards=False)
    cv.rect(52, 34, 24, 12, WOOD[1]); cv.hline(52, 34, 24, WOOD[3]); cv.vline(52, 34, 12, WOOD[3])
    for (x, y) in rect_set(54, 36, 20, 8):
        cv.set(x, y, PLASTER[5] if x < 64 else PLASTER[4])
    cv.vline(64, 36, 8, PLASTER[1]); cv.vline(65, 42, 6, NAP[3])  # the lilac bookmark
    for x in range(56, 63, 2):
        cv.set(x, 39, PLASTER[2])
    for x in range(67, 73, 2):
        cv.set(x, 39, PLASTER[1])
    detail.stones(cv, 6, wall_top, 116, wall_bottom - wall_top, PLASTER, seed=3, course=6, base=4)
    for x in range(112, 122):
        for y in range(wall_top, wall_bottom):
            detail.shade(cv, x, y, 1)
    detail.stones(cv, 4, wall_bottom, 120, 5, STONE, seed=4, course=3, moss=LEAF)
    for x in (24, 92):
        window(cv, x + 2, 55, 10, 22)
    door = rect_set(54, 58, 20, 28)
    cv.rect(52, 56, 24, 2, PLASTER[5]); cv.vline(52, 56, 30, PLASTER[5]); cv.vline(75, 56, 30, PLASTER[2])
    detail.boards(cv, door, WOOD, 2, 58, board=4, vertical=True, x0=54, joints=False, grain=0.05)
    for x0 in (56, 65):
        for py in (62, 74):
            cv.rect(x0 + 1, py, 6, 8, WOOD[3]); cv.hline(x0 + 1, py, 6, WOOD[4]); cv.vline(x0 + 1, py, 8, WOOD[4])
            cv.hline(x0 + 1, py + 7, 6, WOOD[1]); cv.vline(x0 + 6, py + 1, 7, WOOD[1])
    cv.vline(63, 58, 28, WOOD[0])
    cv.set(62, 72, GOLD[4]); cv.set(66, 72, GOLD[4])
    detail.recess(cv, door, depth=2, k=1)
    cols = set()
    for x in (16, 36, 82, 102):
        for y in range(53, 83):
            for i, t in enumerate((4, 5, 5, 4, 4, 3, 3, 2, 1)):
                cv.set(x + i, y, PLASTER[t])
            cols |= {(x + i, y) for i in range(9)}
        for cy in (50, 83):
            cv.rect(x - 2, cy, 13, 3, PLASTER[4]); cv.hline(x - 2, cy, 13, PLASTER[5])
            cv.hline(x - 2, cy + 2, 13, PLASTER[2]); cv.set(x + 10, cy + 1, PLASTER[3])
            cols |= rect_set(x - 2, cy, 13, 3)
    detail.cast(cv, cols, 1, 1, k=2, on=PLASTER, reach=3)
    detail.overhang_shadow(cv, 6, 122, wall_top, lambda x: 3 + (x - 6) // 40, k=2, cap=2)
    for i, y in enumerate((88, 92, 96)):
        x0, sw = 50 - i * 4, 28 + i * 8
        cv.rect(x0, y, sw, 2, STONE[4]); cv.rect(x0, y + 2, sw, 2, STONE[2])
        cv.vline(x0 + sw - 1, y, 4, STONE[1])
    cv.set(44, 99, LEAF[2]); cv.set(43, 98, LEAF[3])
    return cv


def house(roof=None, sign: bool = False) -> Canvas:
    """A town house at the scale table's size (verticality.md 5: walls 44 to the eaves, a
    32 px door, 16 x 12 windows, about 96 to the ridge), 80 wide, in the steep top-down
    view (the hut's rule): a slate roof seen from above, a board gable with a round vent
    (or the bindery's book plaque), painted siding in the overhang's shadow between corner
    boards, a recessed arched door on a stone step with a boot scraper, windows with
    flower boxes, a lamp bracket, a stone chimney showing its cap and a fieldstone
    footing. Its foot stays where the old 76 px house stood (keep_foot)."""
    roof = roof or ROOF
    w, h = 80, 98
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 39.5, 18, 46, 46, 90
    chim = rect_set(56, 6, 9, 13)
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 2, 77, roof, hole=chim,
                                       offset=lambda x, y: -1 if 65 <= x <= 68 and 8 <= y <= 22 else 0,
                                       seed=51 if sign else 53)
    detail.stones(cv, 56, 10, 9, 9, STONE, seed=54, course=3)
    cv.vline(56, 10, 9, STONE[3]); cv.vline(64, 10, 9, STONE[1])
    cv.rect(55, 6, 11, 4, STONE[3]); cv.hline(55, 6, 11, STONE[4]); cv.rect(58, 7, 5, 2, NAP[0])
    gable = topdown_gable(cv, edge_y, 7, 72, apex_y, wall_top, WOOD if not sign else PLASTER, boards=not sign)
    if sign:  # the bindery: a little book plaque in the gable
        cv.rect(30, 30, 20, 9, WOOD[2]); cv.hline(30, 30, 20, WOOD[4]); cv.hline(30, 38, 20, WOOD[1])
        cv.rect(33, 32, 14, 5, PLASTER[5]); cv.vline(40, 32, 5, PLASTER[2]); cv.vline(43, 36, 3, NAP[3])
        for (x, y) in gable:
            if (x, y - 2) in gable and noise2(x // 2, y // 2, 61) > 0.62 and not (29 <= x <= 50 and 29 <= y <= 39):
                cv.set(x, y, PLASTER[3] if x < ridge else PLASTER[2])
    else:
        for (x, y) in disc(ridge, 34, 3.4):
            cv.set(x, y, WOOD[4] if x + y < ridge + 33 else WOOD[1])
        for (x, y) in disc(ridge, 34, 2.3):
            cv.set(x, y, WTR[2] if x < ridge else WTR[1])
    detail.boards(cv, rect_set(7, wall_top, 66, wall_bottom - wall_top), PLASTER, 4, wall_top, seed=11, joints=False)
    for (x, y) in rect_set(10, wall_bottom - 5, 60, 5):  # rain splash and grime above the footing
        if noise2(x // 2, y, 62) > 0.4 + (wall_bottom - y) * 0.08:
            detail.shade(cv, x, y, 1)
    proud = set()
    for x0 in (7, 70):
        for y in range(wall_top - 4, wall_bottom):
            if (x0, y) in gable or y >= wall_top:
                cv.set(x0, y, WOOD[3]); cv.set(x0 + 1, y, WOOD[4]); cv.set(x0 + 2, y, WOOD[2] if x0 == 7 else WOOD[1])
                proud |= {(x0 + i, y) for i in range(3)}
    for y in range(wall_top + 2, wall_bottom - 1):  # a downpipe beside the east corner board
        cv.set(68, y, SLATE[2]); cv.set(69, y, SLATE[1])
        if (y - wall_top) % 12 == 3:
            cv.hline(67, y, 3, SLATE[3])
        proud |= {(68, y), (69, y)}
    proud |= arched_door(cv, 32, wall_bottom - 32, 16, 32)
    cv.rect(29, wall_bottom, 22, 2, STONE[3]); cv.hline(29, wall_bottom, 22, STONE[4])  # the step
    cv.hline(52, wall_bottom - 3, 3, SLATE[1]); cv.set(52, wall_bottom - 2, SLATE[2]); cv.set(54, wall_bottom - 2, SLATE[0])  # boot scraper
    lx = 25  # a lamp on a bracket left of the door
    cv.hline(lx, wall_bottom - 30, 4, SLATE[1]); cv.set(lx + 3, wall_bottom - 29, SLATE[1])
    cv.rect(lx + 2, wall_bottom - 28, 3, 4, GOLD[3]); cv.set(lx + 2, wall_bottom - 28, GOLD[4])
    cv.hline(lx + 2, wall_bottom - 29, 3, SLATE[2]); cv.hline(lx + 2, wall_bottom - 24, 3, SLATE[1])
    proud |= rect_set(lx, wall_bottom - 30, 5, 7)
    family = NAP if sign else RED
    for wx in (13, 55):
        wy = wall_top + 8
        shuttered_window(cv, wx, wy, 12, 16, shutters=None, warm=sign, sill=False)
        cv.rect(wx - 1, wy - 2, 14, 2, WOOD[3]); cv.hline(wx - 1, wy - 2, 14, WOOD[4])  # the head trim
        by = wy + 16
        cv.rect(wx - 1, by, 14, 3, WOOD[2]); cv.hline(wx - 1, by, 14, WOOD[4]); cv.hline(wx - 1, by + 2, 14, WOOD[1])
        for i, x in enumerate(range(wx, wx + 12, 3)):
            cv.set(x, by - 1, LEAF[3]); cv.set(x + 1, by - 1, LEAF[2])
            cv.set(x, by - 2, family[3] if i % 2 else GOLD[3]); cv.set(x + 1, by - 2, family[4])
            cv.set(x + 1, by + 3, LEAF[2] if i % 2 else LEAF[1])  # trailing leaves
        proud |= rect_set(wx - 1, by, 14, 3) | rect_set(wx - 1, wy - 2, 14, 2)
    detail.cast(cv, proud, 1, 1, k=2, on=PLASTER, reach=2)
    detail.overhang_shadow(cv, 7, 73, wall_top, lambda x: (4 if x < 13 or x > 66 else 2) + (x - 7) // 40, k=2, cap=1)
    detail.stones(cv, 5, wall_bottom, 70, 6, STONE, seed=13, course=3, moss=LEAF)
    return gp_keep_foot(cv, 80, 76)


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


# Snow ramps for roofs, darkest first: in sun (lilac-blue creases up to warm white crests
# and a glint) and in cool shade. Each step is far enough from the next to stay its own
# tone on screen.
SNOW_SUN = ['#8494B4', '#98A8C6', '#ACBCD6', '#BECCE2', '#D0DCEC', '#E0E8F2', '#ECF1F6', '#F6F4EE', '#FFFFFF']
SNOW_COOL = ['#526080', '#617092', '#7282A4', '#8292B4', '#92A2C2', '#A2B2CE', '#B2C2DA', '#C4D2E4']
# the same steps a little lilac: every other pillow takes these, as drifts catch the sky
SNOW_SUN_B = ['#8C8CB0', '#A0A0C4', '#B4B4D4', '#C6C8E0', '#D6DAEA', '#E4E8F4', '#EEF0FA', '#F8F8FC', '#FFFFFF']
SNOW_COOL_B = ['#5A5A84', '#6A6A96', '#7A7CA8', '#8A8EB8', '#9A9EC6', '#AAB0D2', '#BAC0DE', '#CACEEA']
# and a third family: warm cream where the low sun lies on a drift, sea-green in the shade
SNOW_SUN_C = ['#9098A8', '#A4ACBA', '#B8BEC8', '#CACED4', '#DCDEDE', '#E8E8E2', '#F2F0E6', '#FCF8EC', '#FFFFFF']
SNOW_COOL_C = ['#4E6478', '#5E768A', '#6E889C', '#7E98AA', '#8EA8B8', '#9EB6C4', '#AEC4D0', '#C0D2DC']


def snow_pillows(cv: Canvas, pts, ramp, ridge: float, slope: float, seed: int = 0, ramp_b=None, ramp_c=None,
                 bias: float = 0.62, pillow: float = 1.0):
    """Snow lying on a roof plane seen steeply from above, as pillows drifted along the
    plane's courses rather than one flat fill: the plane is split into small rounded cells
    (jittered seeds, longer along the courses than down the slope), each shaded as a soft
    mound lit on its upper left (so its tone runs through the ramp from a lit crest to a
    blue-lilac crease where it meets the next pillow), each pillow a step lighter or darker
    than its neighbours, and a glint on the odd crest. Every tone comes in clusters, never
    single pixels."""
    n = len(ramp)
    seeds = []
    for iu in range(-1, 30):
        for js in range(-1, 20):
            u = (iu * 5 + 2 * (js % 2) + int(noise2(iu, js, seed) * 3)) * pillow
            s = (js * 4 + int(noise2(iu, js, seed + 1) * 2)) * pillow
            seeds.append((u, s, iu, js))

    for (x, y) in pts:
        u = abs(x + 0.5 - ridge)
        s = y - u * slope
        near = sorted(((du / 3.0) ** 2 + (ds / 2.4) ** 2, du, ds, iu, js)
                      for (su, ss, iu, js) in seeds
                      for du, ds in ((u - su, s - ss),) if abs(du) < 9 and abs(ds) < 8)
        if not near:
            continue
        d0, du, ds, iu, js = near[0]
        gap = near[1][0] - d0 if len(near) > 1 else 9
        sx = -du if x < ridge else du  # screen offset from the pillow's centre
        lit = -(sx / 3.0 + (ds + du * slope) / 2.4) - 0.35 * d0  # a mound: crest lit, flanks fall away
        t = (n - 2) * bias + lit * 1.5 + (noise2(iu, js, seed + 3) - 0.5) * 2.6
        if gap < 0.35 and lit < 0.3:
            t = min(t, 1.4 if gap > 0.12 else 0.4)  # the crease under a pillow's shaded side
        t = int(max(0, min(n - 2, round(t))))
        if t >= n - 3 and lit > 0.9 and noise2(iu, js, seed + 2) > 0.55:
            t = n - 1  # a glint on a crest
        pick = noise2(iu, js, seed + 4)
        r = ramp_c if ramp_c and pick > 0.67 else ramp_b if ramp_b and pick > 0.34 else ramp
        cv.set(x, y, r[min(t, len(r) - 1)])
    for _ in range(2):  # no lone pixels: one that differs from all four neighbours takes the
        for (x, y) in sorted(pts):  # commonest of them (detail comes in clusters)
            c = cv.get(x, y)
            ns = [cv.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in pts]
            if len(ns) >= 3 and all(v != c for v in ns):
                cv.set(x, y, max(ns, key=ns.count))


def cabin() -> Canvas:
    """The mountain cabin, 100 x 86, in the steep top-down view: a shingled roof under
    snow seen from above, a board gable, round logs with ringed ends at the corners,
    warm windows, a recessed door and snow drifted against the front."""
    w, h = 100, 86
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 49.5, 22, 50, 50, 80
    chim = rect_set(66, 6, 10, 16)
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 3, 96, WOOD, hole=chim, seed=61, moss=None)
    slope = (eave_y - apex_y) / (ridge - 3)
    # B2 (Matt, 19 Oct 22:40: the roof's snow was one flat white) and Claude A, 20 Oct
    # 03:50 (the planes still had large flat areas and faint icicles): the snow lies in
    # pillows drifted along the roof's courses, each lit on its upper left with a cool
    # crease where it meets the next (snow_pillows); the left plane in warm white sun, the
    # right in blue-grey shade; shingles show along the ridge, at the verges and in a few
    # thin patches where the snow has slid; a line of bird tracks crosses the sunlit plane;
    # at the front a thick rounded lip over a dark drip edge with icicles hanging from it;
    # the chimney's cool shadow on the snow.
    snowy = {(x, y) for (x, y) in left | right
             if abs(x + 0.5 - ridge) >= 2.5 and 4 < x < 95
             and 2 + abs(x + 0.5 - ridge) * slope <= y <= edge_y(x) - 2}
    thin = {(x, y) for (x, y) in snowy  # where the snow has slid: the shingles show through
            if noise2(int(x + 0.5 - ridge) // 7, int(y - abs(x + 0.5 - ridge) * slope) // 4, 67) > 0.93
            and edge_y(x) - y > 6}
    snow_pillows(cv, {p for p in snowy if p[0] < ridge} - thin, SNOW_SUN, ridge, slope, seed=68, ramp_b=SNOW_SUN_B, ramp_c=SNOW_SUN_C,
                 bias=0.68, pillow=0.85)
    snow_pillows(cv, {p for p in snowy if p[0] > ridge} - thin, SNOW_COOL, ridge, slope, seed=69, ramp_b=SNOW_COOL_B, ramp_c=SNOW_COOL_C,
                 bias=0.74)
    for (x, y) in thin:  # a thin crust on the exposed shingles' upper edges
        if (x, y - 1) in snowy and (x, y - 1) not in thin:
            cv.set(x, y, SNOW_SUN[4] if x < ridge else SNOW_COOL[4])
    for (x, y) in sorted(snowy):  # the lip of snow over the front verge, rounded and thick
        d = edge_y(x) - 2 - y
        if d < 3 and (x, y) not in thin:
            r = SNOW_SUN if x < ridge else SNOW_COOL
            cv.set(x, y, r[-2] if d == 2 else r[-4] if d == 1 else r[2])
    for i in range(7):  # a bird's tracks across the sunlit plane, in pairs
        tx, ty = 14 + i * 4, int(16 + i * 4 * slope * 0.35) + 6
        if (tx, ty) in snowy and (tx + 1, ty + 1) in snowy:
            cv.set(tx, ty, SNOW_SUN[2]); cv.set(tx + 1, ty + 1, SNOW_SUN[2])
    detail.stones(cv, 66, 10, 10, 12, STONE, seed=63, course=3)
    cv.vline(66, 10, 12, STONE[3]); cv.vline(75, 10, 12, STONE[1])
    cv.rect(65, 6, 12, 4, SNOW[2]); cv.hline(65, 5, 12, SNOW[3]); cv.hline(66, 4, 10, SNOW[3]); cv.rect(68, 7, 6, 2, NAP[0])  # its snow cap
    for x in range(77, 83):  # the chimney's cool shadow on the snow, down and to the right
        for y in range(12, 24):
            if (x, y) in right and cv.get(x, y)[:3] != (0, 0, 0):
                detail.shade(cv, x, y, 1)
    topdown_gable(cv, edge_y, 8, 91, apex_y, wall_top, WOOD)
    for x in range(5, 95):  # the drip edge under the lip, and icicles
        if abs(x + 0.5 - ridge) < 2.5:
            continue
        ey = int(edge_y(x)) - 2
        cv.set(x, ey + 1, SNOW_COOL[1] if x > ridge else SNOW[1])  # the lip hangs over the barge
        cv.set(x, ey + 2, SNOW_COOL[0] if x > ridge else SNOW[0])
        if noise2(x // 2, 3, 66) > 0.72 and x % 2 == 0:
            n = 2 + int(noise2(x, 4, 66) * 4)
            for k in range(n):
                cv.set(x, ey + 4 + k, '#F7FAFC' if k == 0 else '#C8DCEC' if k < n - 1 else '#9FB8D0')
                if k < n - 2:
                    cv.set(x + 1, ey + 4 + k, '#9FB8D0' if x < ridge else '#7E8EA6')
    for i, y in enumerate(range(wall_top, wall_bottom, 5)):
        for x in range(8, 92):
            for r, t in enumerate((4, 3, 3, 2, 1)):
                if y + r >= wall_bottom:
                    continue
                tt = t - (1 if x > 84 else 0)
                if r == 2 and noise2(x // 3, y, 51) < 0.08:
                    tt -= 1
                cv.set(x, y + r, WOOD[max(0, tt)])
        for x in (5, 92):
            for (lx, ly) in disc(x + 1.5, y + 2.5, 2.6):
                cv.set(lx, ly, WOOD[4] if lx + ly < x + y + 3.5 else WOOD[3])
            cv.set(x + 1, y + 2, WOOD[1]); cv.set(x + 2, y + 2, WOOD[2])
    arched_door(cv, 42, 48, 16, 32, porthole=False)  # 32 px, the scale table's door
    window(cv, 16, 56, 16, 12, warm=True)
    window(cv, 68, 56, 16, 12, warm=True)
    detail.overhang_shadow(cv, 8, 92, wall_top, lambda x: 3 + (x - 8) // 30, k=2, cap=1)
    for (x, y) in oval(50, 83, 46, 3.5):
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


LICHEN = ['#8E9A4E', '#B8C070', '#D8A050']  # grey-green and yellow lichen, an orange crust


def _cairn_stone(cv: Canvas, cx: float, base: int, rw: float, rh: float, seed: int):
    """One flat field stone in a cairn, seen a little from above: an irregular slab (its
    outline nudged per column), its top face lit, its front a step down, its east end in
    shade and its underside dark where it beds on the stone below; a crack, and lichen in
    clusters of two on its top."""
    pts = set()
    for x in range(int(cx - rw), int(cx + rw) + 1):
        u = (x + 0.5 - cx) / rw
        if abs(u) > 1:
            continue
        hh = rh * (1 - u * u) ** 0.35
        top = base - hh - int(noise2(x // 2, seed, 401) * 1.6)
        for y in range(int(round(top)), base + 1):
            pts.add((x, y))
    if not pts:
        return set()
    ys = [y for _, y in pts]
    y0 = min(ys)
    for (x, y) in pts:
        u = (x + 0.5 - cx) / rw
        col_top = min(yy for (xx, yy) in pts if xx == x)
        d = y - col_top
        if d <= 1:
            t = 4 if u < 0.2 and d == 0 else 3  # the top face, lit
        elif y >= base:
            t = 0  # bedded on the stone below
        else:
            t = 2 if u < 0.45 else 1  # the front, its east end in shade
        if u > 0.75 and d > 1:
            t = max(0, t - 1)
        if 0 < t < 4 and y < base:  # the stone's grain: blotches two pixels across, a tone up or down
            m = noise2((x + seed) // 2, y // 2, 404)
            t += 1 if m > 0.78 and t < 3 else -1 if m < 0.2 else 0
        cv.set(x, y, STONE[t])
    cx_i = int(cx + rw * 0.2)
    if (cx_i, base - 1) in pts and (cx_i + 1, base - 2) in pts:  # a crack in the front
        cv.set(cx_i, base - 1, STONE[1]); cv.set(cx_i + 1, base - 2, STONE[1])
    for i in range(3):  # lichen on the top face and front, in pairs
        lx = int(cx - rw * 0.6 + noise2(i, seed, 402) * rw)
        col = [yy for (xx, yy) in pts if xx == lx]
        if col and (lx + 1, min(col)) in pts:
            c = LICHEN[int(noise2(i, seed, 403) * 3)]
            cv.set(lx, min(col), c); cv.set(lx + 1, min(col), c)
    return pts


def cairn(variant: str = 'a') -> Canvas:
    """A trail cairn (it was a cone of identical slabs), 20 x 34: field stones of three
    sizes stacked by walkers, each a different slab lying a little askew (_cairn_stone),
    lit on its top and shaded at its east end, dark where it beds on the one below, with
    lichen on the older, lower stones; a weathered ribbon on a stick wedged in the top as
    the trail's marker, and loose stones at its foot. Variant 'b' is a younger, lower
    cairn of four stones and no ribbon, for a side path."""
    cv = Canvas(20, 34, pad=PAD)
    foot = 32
    if variant == 'b':
        layers = ((10, 8.5, 3.5), (9.5, 6, 3), (11, 4.5, 2.5), (10, 3, 2))
    else:
        layers = ((10, 9.5, 3.5), (8.5, 7.5, 3), (11.5, 6.5, 3), (9, 5, 2.5), (11, 4, 2.5), (10, 2.5, 2))
    for x in range(1, 20):  # its contact shade
        cv.set(x, foot + 1, (20, 26, 22, 110))
    y = foot
    for i, (cx, rw, rh) in enumerate(layers):
        _cairn_stone(cv, cx, y, rw, rh, seed=i * 7 + (3 if variant == 'b' else 0))
        y -= int(rh) + 1
    top = y + 1
    for (px, py, r) in ((2, foot, 1.5), (17, foot, 1.2), (15, foot + 1, 1)):  # loose stones at the foot
        for (x, yy) in disc(px, py - 0.5, r):
            cv.set(x, yy, STONE[3] if x < px else STONE[2])
    for (gx, kind) in ((0, 3), (5, 0), (13, 5), (19, 1)):  # grass grown up round its foot
        detail.grass_tuft(cv, gx, foot, kind, MATERIALS['grass'], 2)
    for (mx, my) in ((4, foot - 1), (6, foot - 2), (16, foot - 1)):  # moss on the bottom stone
        cv.set(mx, my, LEAF[2]); cv.set(mx + 1, my, LEAF[3] if mx < 10 else LEAF[1])
    if variant != 'b':  # the marker: a stick wedged in the top, a faded ribbon on it
        for yy in range(top - 7, top + 1):
            cv.set(11, yy, WOOD[3] if yy < top - 1 else WOOD[2])
        cv.set(12, top - 7, NAP[3]); cv.set(13, top - 7, NAP[3]); cv.set(14, top - 6, NAP[2])
        cv.set(12, top - 6, NAP[2]); cv.set(13, top - 6, NAP[1]); cv.set(15, top - 5, NAP[1])
    return despeckle(cv)


# A mallard drake facing east on the water, drawn pixel by pixel at its true size (about
# a third of a 25 px adult's height). g/G/h the bottle-green head and its sheen, y/Y the
# bill, e the eye, w the white collar, c/C the chestnut breast, b/B/d the grey flank lit
# to shade, W the folded wing, p the blue speculum, k/K the black tail and its curl, R the
# dark water hugging the waterline, r the lit rings of the wake.
DUCK_ROWS = (
    '.........GG.....',
    '........gGhG....',
    '........ggeGyy..',
    '........gggYyyy.',
    '..K.....www.....',
    '.kKbbbbbbCCc....',
    '.kkbWWWbbbCCc...',
    '.kdbWpWWbbbcc...',
    '..ddBBBBBBdcc...',
    '...RRRRRRRRRR...',
    'rr..........rr..',
    '..rrr....rrr....',
)
DUCK_INKS = {
    'g': LEAF[0], 'G': LEAF[1], 'h': MATERIALS['copper'][3], 'y': GOLD[3], 'Y': GOLD[2],
    'e': '#141018', 'w': CREAM[3], 'c': WOOD[1], 'C': WOOD[2], 'b': STONE[4], 'B': STONE[3],
    'd': STONE[2], 'W': CREAM[0], 'p': NAP[2], 'k': SLATE[0], 'K': STONE[1],
    'R': (44, 60, 88, 150), 'r': (198, 221, 238, 150),
}


def duck() -> Canvas:
    """The park's duck (A9: it was a white blob): a mallard drake at its true size, about
    a third of an adult's height, sitting on the water facing east, drawn pixel by pixel
    (DUCK_ROWS): a bottle-green head with a sheen on its crown, a yellow bill, the white
    collar, a chestnut breast, grey flanks lit from the upper left, the folded wing with
    its blue speculum, a black tail with its curl, the dark water along its waterline and
    the lit rings of its wake behind it. Re-seated in the old 14 x 10 box (keep_foot);
    Claude A's animal frames paddle and preen it."""
    cv = Canvas(16, len(DUCK_ROWS), pad=PAD)
    for y, row in enumerate(DUCK_ROWS):
        for x, ch in enumerate(row):
            if ch != '.':
                cv.set(x, y, DUCK_INKS[ch])
    return gp_keep_foot(cv, 14, 10)


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
        'pine': gp.pine(), 'bush': gp.bush(), 'fountain': fountain(), 'bench': bench(), 'bench_east': bench('east'), 'bench_west': bench('west'), 'lamp': lamp(),
        'hedge': hedge(96), 'library': library(), 'house_red': house(ROOF),
        'house_blue': house(BLUE_ROOF, sign=True), 'cafe': cafe_table(), 'cart': book_cart(),
        'cabin': cabin(), 'campfire': campfire(), 'boulder': boulder(True), 'stone': boulder(False),
        'cairn': cairn(), 'cairn_b': cairn('b'), 'duck': duck(),
        'crate': gp.crate(), 'barrel': gp.barrel(), 'potted_plant': gp.potted_plant(), 'sack': gp.sack(),
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
