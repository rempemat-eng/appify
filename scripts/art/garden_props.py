"""Garden props at the step-6 density (docs/vision/coherence-plan.md).

Sizes follow the proportions table, in art pixels, against a 32 x 32 companion that
stands about 26 pixels tall: the hut is three and a half companions tall, its door
just taller than the companion, trees tower over it, bushes and rocks stay below it.

Shading rules: light from the upper left; each surface is a clean plane of one or
two tones (no dither noise); edges catching the light get one lighter row, edges
turning away one darker; cast shadows are baked into the ground by garden.py; every
silhouette gets a material-tinted outline from style.close_outline afterwards.
Colours come only from the canonical ramps in art/materials.json.
"""
from __future__ import annotations

import math

import style
import detail
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, PLASTER, RED, SAND, SLATE, STONE, WOOD, WTR
from pixel import Canvas, disc, noise2, oval

G = MATERIALS['grass']
# Working room around every prop: art may stray past its nominal box and is kept
# (style.finalize trims it and records the offset), so nothing is ever cut off.
PAD = 16
PATH = MATERIALS['path']
PINE = ['#1F2E2A', '#2F4A3C', '#46664B', '#5E8253', '#86A766']
AUTUMN = ['#4A2A22', '#7A4030', '#A8623E', '#CB8650', '#E8B575']


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def canopy(cv: Canvas, lobes, ramp, seed: int = 0) -> set:
    """Foliage as a few large leaf masses (Matt's references): each lobe is shaded as a
    sphere lit from the upper left in clean bands, a lobe in front casts a dark rim on
    the one behind it, the silhouette is scalloped by small leaf bumps, and a sparse
    scatter of leaf ticks gives texture without noise. Lobes are listed back to front."""
    shape = set()
    owner = {}
    for i, (cx, cy, r) in enumerate(lobes):
        pts = set(disc(cx, cy, r))
        # leaf bumps around the lobe's upper and side rim
        n = max(6, int(2 * math.pi * r / 3.2))
        for k in range(n):
            a = 2 * math.pi * (k + 0.4 * noise2(k, seed + i, 7)) / n
            bx, by = cx + r * 0.94 * math.cos(a), cy + r * 0.94 * math.sin(a)
            if math.sin(a) > 0.55:
                continue
            pts |= set(disc(bx, by, 1.9))
        for p in pts:
            owner[p] = i
        shape |= pts
    for (x, y) in shape:
        cx, cy, r = lobes[owner[(x, y)]]
        nx, ny = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
        nz = math.sqrt(max(0.0, 1 - min(1.0, nx * nx + ny * ny)))
        lv = -0.55 * nx - 0.75 * ny + 0.4 * nz
        tone = 4 if lv > 0.82 else 3 if lv > 0.3 else 2 if lv > -0.25 else 1
        cv.set(x, y, ramp[tone])
    # a front lobe darkens the rim of the lobe behind it, which separates the masses
    for (x, y) in shape:
        i = owner[(x, y)]
        for dx, dy in ((0, -1), (-1, 0), (1, 0)):
            n = (x + dx, y + dy)
            if n in owner and owner[n] > i and dy <= 0:
                cv.set(x, y, ramp[1])
                break
    # leaf ticks: a light mark over a dark one, only on lit and mid tones
    xs = [x for x, _ in shape]
    ys = [y for _, y in shape]
    for k in range(len(shape) // 26):
        x = min(xs) + int(noise2(k, seed, 31) * (max(xs) - min(xs) + 1))
        y = min(ys) + int(noise2(k, seed, 32) * (max(ys) - min(ys) + 1))
        if (x, y) in shape and (x + 1, y + 1) in shape and owner.get((x, y)) == owner.get((x + 1, y + 1)):
            cur = cv.get(x, y)
            if cur[:3] in (tuple(int(ramp[3][i:i + 2], 16) for i in (1, 3, 5)),
                           tuple(int(ramp[2][i:i + 2], 16) for i in (1, 3, 5))):
                cv.set(x, y, ramp[4] if cur[:3] == tuple(int(ramp[3][i:i + 2], 16) for i in (1, 3, 5)) else ramp[3])
                cv.set(x + 1, y + 1, ramp[1] if cur[:3] != tuple(int(ramp[3][i:i + 2], 16) for i in (1, 3, 5)) else ramp[2])
    return shape


def plane(cv: Canvas, pts, ramp, base: int, lit_edge: bool = True, dark_edge: bool = True):
    """A clean plane: one tone, a lit top/left edge row and a shaded bottom/right row."""
    pts = set(pts)
    top = len(ramp) - 1
    for (x, y) in pts:
        tone = base
        if dark_edge and ((x + 1, y) not in pts or (x, y + 1) not in pts):
            tone = base - 1
        if lit_edge and ((x - 1, y) not in pts or (x, y - 1) not in pts):
            tone = base + 1
        cv.set(x, y, ramp[max(0, min(top, tone))])


def planks(cv: Canvas, x0, y0, w, h, ramp, step=4, vertical=True, base=2):
    """Boards with a lit left/top edge and a dark seam, and a knot here and there."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            k = (x - x0) if vertical else (y - y0)
            pos = k % step
            col = ramp[base]
            if pos == 0:
                col = ramp[min(len(ramp) - 1, base + 1)]
            elif pos == step - 1:
                col = ramp[max(0, base - 1)]
            cv.set(x, y, col)
    for i in range(0, w * h // 90):
        kx = x0 + int(noise2(i, x0, 11) * (w - 2)) + 1
        ky = y0 + int(noise2(i, y0, 12) * (h - 2)) + 1
        cv.set(kx, ky, ramp[max(0, base - 1)])


def stone_blocks(cv: Canvas, x0, y0, w, h, block=8):
    """A course of dressed stones: lit top edge, shaded right edge, alternating tones."""
    for i, x in enumerate(range(x0, x0 + w, block)):
        bw = min(block, x0 + w - x)
        base = 3 if i % 2 else 2
        for yy in range(y0, y0 + h):
            for xx in range(x, x + bw):
                col = STONE[base]
                if yy == y0:
                    col = STONE[base + 1]
                elif xx == x + bw - 1 or yy == y0 + h - 1:
                    col = STONE[base - 1]
                cv.set(xx, yy, col)


# ---- the nap hut -----------------------------------------------------------
def window(cv: Canvas, x: int, y: int, w: int = 16, h: int = 14, shutters=NAP, curtain=PLASTER,
           sill: bool = True):
    """A deep window: a trim lit on its top and left, glass that reflects the sky at the
    top and darkens toward the room, a curtain valance and tied-back curtains, glazing
    bars, a glint, painted slatted shutters and a sill that casts its shadow."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            cv.set(xx, yy, WOOD[2])
    cv.hline(x, y, w, WOOD[4]); cv.vline(x, y, h, WOOD[3])
    cv.hline(x + 1, y + h - 1, w - 1, WOOD[1]); cv.vline(x + w - 1, y + 1, h - 1, WOOD[1])
    gx, gy, gw, gh = x + 2, y + 2, w - 4, h - 4
    glass = rect_set(gx, gy, gw, gh)
    for (xx, yy) in glass:
        k = yy - gy
        cv.set(xx, yy, WTR[2] if k < 2 else WTR[1] if k < gh - 3 else WTR[0])
    # a scalloped valance and curtains tied back two thirds of the way down
    for xx in range(gx, gx + gw):
        cv.set(xx, gy, curtain[4] if (xx - gx) % 2 == 0 else curtain[3])
    tie = gy + (gh * 2) // 3
    for yy in range(gy + 1, gy + gh):
        reach = 1 if yy == tie else 2
        for i in range(reach):
            cv.set(gx + i, yy, curtain[4] if i == 0 else curtain[3])
            cv.set(gx + gw - 1 - i, yy, curtain[3] if i == 0 else curtain[2])
    cv.set(gx + 1, tie, RED[3]); cv.set(gx + gw - 2, tie, RED[2])
    # glazing bars
    mx, my = gx + gw // 2, gy + gh // 2
    cv.vline(mx, gy + 1, gh - 1, WOOD[2]); cv.hline(gx + 2, my, gw - 4, WOOD[2])
    cv.set(mx, my, WOOD[3])
    # glints: a short diagonal in each upper pane
    for px in (gx + 4, mx + 3):
        cv.set(px, gy + 2, WTR[4]); cv.set(px - 1, gy + 3, WTR[3])
    detail.recess(cv, glass, depth=1, k=1)
    if shutters:
        for sx, lit in ((x - 4, True), (x + w, False)):
            for yy in range(y, y + h):
                for i in range(4):
                    slat = shutters[3] if (yy - y) % 2 == 0 else shutters[2]
                    if i == 0:
                        slat = shutters[4] if lit else shutters[2]
                    elif i == 3:
                        slat = shutters[1]
                    cv.set(sx + i, yy, slat)
            cv.hline(sx, y, 4, shutters[4] if lit else shutters[3])
            cv.hline(sx, y + h - 1, 4, shutters[1])
    if sill:
        cv.hline(x - 1, y + h, w + 2, WOOD[4]); cv.hline(x - 1, y + h + 1, w + 2, WOOD[1])
        detail.overhang_shadow(cv, x, x + w + 2, y + h + 2, lambda xx: 1 if xx < x + 4 else 2, k=2)


def hut() -> Canvas:
    """The nap hut, 104 x 92: a shingled lavender roof with a timber gable, painted
    siding under the eave's shadow, deep windows with shutters, a recessed round-topped
    door (16 x 28) and a stone foundation (coherence plan, 6c: material detail)."""
    w, h = 104, 92
    cv = Canvas(w, h, pad=PAD)
    apex_x, apex_y, eave = 51.5, 18, 46

    def half(y):
        return (y - apex_y) * (32 / (eave - apex_y))

    def gable(x, y):
        return apex_y <= y <= eave and abs(x + 0.5 - apex_x) <= half(y)

    # chimney behind the right slope: fieldstone with a slab cap
    detail.bricks(cv, 72, 3, 10, 18, MATERIALS['roof'], seed=7)
    cv.vline(72, 3, 18, MATERIALS['roof'][3]); cv.vline(81, 3, 18, MATERIALS['roof'][1])
    cv.rect(70, 0, 14, 3, STONE[3]); cv.hline(70, 0, 14, STONE[4]); cv.hline(70, 2, 14, STONE[1])
    cv.rect(74, 1, 6, 1, NAP[0])
    detail.overhang_shadow(cv, 72, 82, 3, 1)

    # roof: two shingled planes; the lit left plane is a step lighter. The front gable
    # and the chimney cast shadows to their right onto the right-hand plane.
    def roof_shadow(x, y):
        right_edge = apex_x + (half(y) if y >= apex_y else 2.5)
        if 0 <= x - right_edge < (6 if y >= apex_y else 4):
            return -1
        if 82 <= x <= 85 and y < 22:
            return -1
        return 0

    left, right = set(), set()
    for y in range(5, eave):
        inset = 12 - (y - 4) * 12 / (eave - 4)
        for x in range(w):
            if x < inset or x > w - 1 - inset or gable(x, y):
                continue
            if 71 <= x <= 82 and y < 20 and x > apex_x:
                continue  # the chimney stands in front of this patch
            (left if x < apex_x else right).add((x, y))
    detail.shingles(cv, left, NAP, 3, 5, seed=1)
    detail.shingles(cv, right, NAP, 2, 5, seed=2, offset=roof_shadow)
    # verges: the roof's thickness along its sloping ends, lit on the left
    for (x, y) in left:
        if (x - 1, y) not in left:
            cv.set(x, y, NAP[4]); cv.set(x + 1, y, NAP[3])
    for (x, y) in right:
        if (x + 1, y) not in right and x > 82:
            cv.set(x, y, NAP[0]); cv.set(x - 1, y, NAP[1])
    # ridge caps: the main ridge along the top, the gable's ridge running back to it
    for x in range(12, w - 12):
        if 71 <= x <= 82:
            continue
        cv.set(x, 4, NAP[4] if x < apex_x else NAP[3]); cv.set(x, 3, NAP[2])
    for y in range(3, apex_y + 1):
        cv.set(49, y, WOOD[4]); cv.set(50, y, WOOD[3]); cv.set(51, y, WOOD[3])
        cv.set(52, y, WOOD[2]); cv.set(53, y, WOOD[1])
    cv.hline(49, 3, 5, WOOD[4])

    # gable end: vertical boards, shaded under the bargeboards
    gpts = {(x, y) for y in range(apex_y, eave) for x in range(w) if gable(x, y)}
    detail.boards(cv, gpts, WOOD, 2, apex_y, board=5, seed=3, vertical=True, x0=20, joints=False, grain=0.04)
    for (x, y) in gpts:
        if (x, y - 1) not in gpts or (x, y - 2) not in gpts or (x - 1, y - 2) not in gpts:
            detail.shade(cv, x, y, 1)
    # a round vent with the crescent sign, set into a lit frame
    for (x, y) in disc(apex_x, 32, 5.4):
        cv.set(x, y, WOOD[4] if x + y < apex_x + 32 - 1 else WOOD[1])
    for (x, y) in disc(apex_x, 32, 4.2):
        cv.set(x, y, NAP[0])
    for (x, y) in disc(apex_x - 0.6, 31.6, 2.7) - disc(apex_x + 0.9, 30.8, 2.3):
        cv.set(x, y, GOLD[3] if y < 32 else GOLD[2])
    cv.set(int(apex_x) - 2, 31, GOLD[4])
    # bargeboards along the gable, lit on the left, with a finial at the apex
    for y in range(apex_y - 1, eave + 1):
        hh = max(0.0, half(y))
        lx, rx = int(apex_x - hh) - 1, int(apex_x + hh) + 1
        cv.set(lx, y, WOOD[3]); cv.set(lx - 1, y, WOOD[4]); cv.set(lx - 2, y, WOOD[3])
        cv.set(rx, y, WOOD[2]); cv.set(rx + 1, y, WOOD[2]); cv.set(rx + 2, y, WOOD[1])
    cv.vline(51, apex_y - 5, 4, WOOD[3]); cv.set(52, apex_y - 5, WOOD[2]); cv.set(51, apex_y - 6, WOOD[4])
    # the eave: a fascia board under the shingle tips
    for x in range(0, w):
        if cv.get(x, eave - 1)[3]:
            cv.set(x, eave, WOOD[1])
            cv.set(x, eave - 1, WOOD[3] if x < apex_x else WOOD[2])

    # walls: painted siding; the receding side wall a step darker; the eave's shadow
    # falls across the top, deeper to the right; the foot darkens where it meets stone.
    wall_top, wall_bottom = eave + 1, 82
    detail.boards(cv, rect_set(8, wall_top, 82, wall_bottom - wall_top), PLASTER, 4, wall_top, seed=4, joints=False)
    detail.boards(cv, rect_set(90, wall_top, 6, wall_bottom - wall_top), PLASTER, 3, wall_top, seed=5, joints=False)
    posts = set()
    for x0 in (8, 87):  # round timber corner posts: a lit stripe, a dark far side
        for y in range(wall_top, wall_bottom):
            cv.set(x0, y, WOOD[3]); cv.set(x0 + 1, y, WOOD[4]); cv.set(x0 + 2, y, WOOD[2] if x0 == 8 else WOOD[1])
            posts |= {(x0, y), (x0 + 1, y), (x0 + 2, y)}

    # door: 16 x 28, round top, set in a stone arch; the arch shades its top and left
    dx0, dy0, dw, dh = 44, 54, 16, 28
    door = {(x, y) for (x, y) in disc(dx0 + dw / 2, dy0 + dw / 2, dw / 2) if y < dy0 + dh}
    door |= rect_set(dx0, dy0 + dw // 2, dw, dh - dw // 2)
    arch = set()
    for (x, y) in door:
        for ax, ay in ((-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1), (-2, 0), (2, 0), (0, -2), (-2, -1), (2, -1)):
            if (x + ax, y + ay) not in door and y + ay < dy0 + dh:
                arch.add((x + ax, y + ay))
    for (x, y) in arch:  # voussoirs: alternate tones, lit toward the upper left
        k = int(((x - dx0 - dw / 2) * 0.9 + (y - dy0) * 0.6) // 3)
        base = 3 if k % 2 else 2
        if x > dx0 + dw / 2 + 1:
            base -= 1
        cv.set(x, y, STONE[base])
    for (x, y) in arch:
        if (x - 1, y) not in arch and (x, y - 1) not in arch:
            cv.set(x, y, STONE[4])
    detail.boards(cv, door, WOOD, 3, dy0, board=4, seed=6, vertical=True, x0=dx0, joints=False, grain=0.06)
    for sy in (dy0 + 13, dy0 + 23):  # iron straps with rivets
        cv.hline(dx0 + 1, sy, 9, SLATE[1]); cv.hline(dx0 + 1, sy - 1, 9, SLATE[2])
        cv.set(dx0 + 3, sy - 1, SLATE[4]); cv.set(dx0 + 7, sy - 1, SLATE[4])
    for (x, y) in disc(dx0 + dw / 2, dy0 + 7, 2.8):  # a little round light
        cv.set(x, y, WOOD[1])
    for (x, y) in disc(dx0 + dw / 2, dy0 + 7, 1.9):
        cv.set(x, y, WTR[2])
    cv.set(dx0 + 7, dy0 + 6, WTR[4])
    detail.recess(cv, door, depth=2, k=1)
    cv.set(dx0 + 12, dy0 + 17, GOLD[4]); cv.set(dx0 + 12, dy0 + 18, GOLD[2]); cv.set(dx0 + 13, dy0 + 18, GOLD[1])

    # windows with shutters; a flower box under the right one
    window(cv, 18, 57)
    window(cv, 70, 57, sill=False)
    detail.boards(cv, rect_set(68, 71, 20, 5), WOOD, 2, 71, board=5, seed=8)
    cv.hline(68, 71, 20, WOOD[4]); cv.hline(68, 75, 20, WOOD[1])
    detail.overhang_shadow(cv, 69, 89, 76, lambda xx: 1 if xx < 73 else 2)
    blooms = (RED[3], GOLD[3], NAP[4], RED[4], PLASTER[5], NAP[3])
    for i, x in enumerate(range(69, 87, 3)):
        cv.set(x, 70, LEAF[2]); cv.set(x + 1, 70, LEAF[3]); cv.set(x + 2, 70, LEAF[1])
        cv.set(x + 1, 69, LEAF[4])
        petal = blooms[i % len(blooms)]
        cv.set(x, 68, petal); cv.set(x + 1, 68, petal); cv.set(x, 67, petal)
        cv.set(x + 1, 67, PLASTER[5] if petal != PLASTER[5] else GOLD[3])
    for x in (70, 76, 83):  # trailing leaves over the box front
        cv.set(x, 72, LEAF[3]); cv.set(x, 73, LEAF[2]); cv.set(x + 1, 74, LEAF[2])

    # whatever stands proud of the siding casts a shadow on it, down and to the right
    proud = posts | arch
    for wx in (18, 70):
        proud |= rect_set(wx - 4, 57, 4, 14) | rect_set(wx + 16, 57, 4, 14)  # shutters
    proud |= rect_set(17, 71, 18, 2) | rect_set(68, 71, 20, 5)  # sill, flower box
    detail.cast(cv, proud, 1, 1, k=2, on=PLASTER, reach=2)

    # the eave's shadow on the siding (after the windows, so it falls across them too)
    detail.overhang_shadow(cv, 8, 96, wall_top, lambda x: 4 + (x - 8) // 22, k=2, cap=1)
    for x in range(8, 96):
        detail.shade(cv, x, wall_bottom - 1, 1)

    # ivy climbing the lit corner
    for (ix, iy) in ((10, 50), (12, 54), (10, 58), (12, 62), (10, 66), (12, 70), (11, 75)):
        cv.vline(ix + 1, iy, 4, LEAF[1])
        cv.set(ix, iy, LEAF[4]); cv.set(ix + 1, iy, LEAF[3]); cv.set(ix, iy + 1, LEAF[3])
        cv.set(ix + 2, iy + 2, LEAF[2]); cv.set(ix + 2, iy + 1, LEAF[3])

    # foundation of fieldstones, a step at the door and a mat
    detail.stones(cv, 6, wall_bottom, 92, 7, STONE, seed=9, course=4, moss=LEAF)
    cv.rect(41, wall_bottom, 22, 3, STONE[3]); cv.hline(41, wall_bottom, 22, STONE[4])
    cv.hline(41, wall_bottom + 2, 22, STONE[1])
    cv.rect(43, 89, 18, 3, NAP[2]); cv.hline(43, 89, 18, NAP[3]); cv.hline(43, 91, 18, NAP[1])
    for x in range(44, 60, 2):
        cv.set(x, 90, NAP[4])
    return cv


# ---- Moss's stall ----------------------------------------------------------
def stall() -> Canvas:
    """Moss's hat stall, 88 x 72: a striped awning with rounded folds over a deep, shaded
    recess with a shelf of hats, and a planked counter at companion height whose top
    shows its thickness (coherence plan, 6c)."""
    w, h = 88, 72
    cv = Canvas(w, h, pad=PAD)
    # the recess under the awning: a back wall of dark boards, darkest under the awning
    detail.boards(cv, rect_set(8, 28, 72, 18), WOOD, 1, 28, board=6, vertical=True, x0=8, joints=False)
    for x in range(8, 80):
        for y in range(28, 35):
            detail.shade(cv, x, y, 2 if y < 32 else 1)
    cv.hline(8, 44, 72, WOOD[3]); cv.hline(8, 45, 72, WOOD[1])  # the shelf, lit along its edge
    # a cap, a top hat, a straw hat, a crown, each in its own material
    for (x, y) in oval(18, 42, 7, 3) | rect_set(12, 37, 12, 5):
        cv.set(x, y, WTR[2] if y < 41 else WTR[1])
    cv.hline(12, 37, 10, WTR[3]); cv.set(12, 38, WTR[4]); cv.hline(14, 43, 12, WTR[1])
    for y in range(30, 43):
        cv.hline(30, y, 9, STONE[1] if y < 41 else STONE[0])
    cv.vline(30, 30, 11, STONE[2]); cv.vline(31, 31, 8, STONE[3]); cv.hline(30, 38, 9, RED[2])
    cv.hline(27, 43, 15, STONE[0]); cv.hline(28, 42, 13, STONE[1])
    for (x, y) in oval(51, 41, 8, 3):
        cv.set(x, y, SAND[2] if y < 41 else SAND[1])
    for (x, y) in oval(51, 38, 4, 3):
        cv.set(x, y, SAND[2] if x < 51 else SAND[1])
    cv.set(49, 36, CREAM[3]); cv.hline(47, 39, 9, RED[3]); cv.hline(47, 40, 9, RED[1])
    for i, x in enumerate(range(62, 71)):
        top = 34 if i % 4 == 0 else 36
        cv.vline(x, top, 43 - top, GOLD[4] if x < 64 else GOLD[3] if x < 68 else GOLD[2])
    cv.hline(62, 43, 9, GOLD[1]); cv.set(62, 34, GOLD[4]); cv.set(66, 39, RED[3]); cv.set(66, 38, RED[4])
    # posts: round, lit from the left, standing in front of the recess
    posts = set()
    for x in (4, 80):
        for y in range(16, 68):
            cv.set(x, y, WOOD[3]); cv.set(x + 1, y, WOOD[4]); cv.set(x + 2, y, WOOD[2]); cv.set(x + 3, y, WOOD[1])
            posts |= {(x + i, y) for i in range(4)}
    detail.cast(cv, posts, 1, 1, k=1, on=WOOD, reach=2)
    # counter: a lit top that shows its thickness, a planked front shaded under the lip
    cv.rect(2, 46, 84, 2, WOOD[4]); cv.hline(2, 48, 84, WOOD[3]); cv.hline(2, 49, 84, WOOD[2])
    cv.set(2, 46, WOOD[3])
    detail.boards(cv, rect_set(2, 50, 84, 16), WOOD, 2, 50, board=7, vertical=True, x0=2, grain=0.05, joints=False)
    for x in range(2, 86):
        detail.shade(cv, x, 50, 2); detail.shade(cv, x, 51, 1)
    for x in range(76, 86):
        for y in range(52, 66):
            detail.shade(cv, x, y, 1)  # the counter's end turns from the light
    cv.hline(2, 66, 84, WOOD[0]); cv.hline(2, 65, 84, WOOD[1])
    # ledger and a potted seedling on the counter
    cv.rect(52, 44, 12, 3, NAP[1]); cv.hline(53, 44, 10, CREAM[3]); cv.vline(58, 44, 2, CREAM[1])
    cv.rect(16, 42, 6, 5, RED[2]); cv.hline(16, 42, 6, RED[3]); cv.vline(21, 43, 4, RED[1]); cv.set(16, 43, RED[4])
    cv.set(18, 40, LEAF[3]); cv.set(19, 39, LEAF[4]); cv.set(17, 41, LEAF[2]); cv.set(20, 41, LEAF[2])
    # bolts of fabric by the base, rolled: lit along the top
    for (bx, ramp) in ((8, NAP), (66, WTR)):
        cv.rect(bx, 67, 14, 4, ramp[2]); cv.hline(bx, 67, 14, ramp[4]); cv.hline(bx, 68, 14, ramp[3])
        cv.hline(bx, 70, 14, ramp[1]); cv.vline(bx, 67, 4, ramp[1]); cv.set(bx, 68, ramp[2])
    # awning: a lit top slope, then a valance of rounded folds (each stripe lit on its
    # left, shaded on its right) with a scalloped hem, casting a deep shadow below
    for y in range(8, 29):
        for x in range(0, w):
            stripe = (x // 8) % 2 == 0
            f = x % 8
            ramp = LEAF if stripe else PLASTER
            top = len(ramp) - 1
            if y < 15:
                t = top if f in (1, 2) and y < 11 else top - 1 if f < 6 else top - 2
            else:
                t = top - 1 if f in (1, 2) else top - 2 if f in (0, 3, 4) else top - 3
                if y > 25:
                    t -= 1
            cv.set(x, y, ramp[max(0, t)])
    cv.hline(0, 8, w, LEAF[1]); cv.hline(0, 15, w, LEAF[1])
    for x in range(0, w):
        cv.set(x, 9, LEAF[4] if (x // 8) % 2 == 0 else PLASTER[5])
    for x in range(0, w):
        f = x % 8
        stripe = (x // 8) % 2 == 0
        ramp = LEAF if stripe else PLASTER
        top = len(ramp) - 1
        if 1 <= f <= 6:
            cv.set(x, 29, ramp[top - 2] if f < 4 else ramp[top - 3])
        if 2 <= f <= 5:
            cv.set(x, 30, ramp[top - 3])
    # hanging sign with a little hat
    cv.rect(30, 0, 28, 8, WOOD[3]); cv.hline(30, 0, 28, WOOD[4]); cv.hline(30, 7, 28, WOOD[1])
    cv.vline(30, 0, 8, WOOD[4]); cv.vline(57, 1, 6, WOOD[2])
    cv.rect(39, 2, 10, 3, NAP[3]); cv.hline(37, 5, 14, NAP[1]); cv.hline(39, 2, 10, NAP[4])
    return cv


# ---- trees -------------------------------------------------------------------
def tree(big: bool = True, autumn: bool = False) -> Canvas:
    """A round broadleaf: 64 x 88 (or 48 x 64), a canopy of a few big leaf masses over
    a flared trunk."""
    w, h = (64, 88) if big else (48, 64)
    cv = Canvas(w, h, pad=PAD)
    ramp = AUTUMN if autumn else LEAF
    cx = w / 2
    tw = 10 if big else 7
    tx = int(cx - tw / 2)
    trunk_top = h - (34 if big else 24)
    style.trunk(cv, tx, trunk_top - 6, h, tw, WOOD)
    k = 1.0 if big else 0.74
    lobes = [(cx + 11 * k, 20 * k, 15 * k), (cx - 12 * k, 22 * k, 15 * k), (cx + 2 * k, 13 * k, 15 * k),
             (cx - 9 * k, 36 * k, 14 * k), (cx + 10 * k, 37 * k, 14 * k), (cx, 30 * k, 14 * k)]
    shape = canopy(cv, lobes, ramp, seed=9 if autumn else 2 + big)
    style.trunk(cv, tx, trunk_top, h, tw, WOOD, shape)
    if not autumn and big:  # ripe apples on the lit side
        for fx, fy in ((cx - 18, 18), (cx + 6, 9), (cx - 8, 31), (cx + 16, 27), (cx - 3, 18)):
            fx, fy = int(fx), int(fy)
            cv.rect(fx, fy, 3, 3, RED[2]); cv.set(fx, fy, RED[4]); cv.set(fx + 1, fy, RED[3])
            cv.set(fx + 2, fy + 2, RED[1]); cv.set(fx + 1, fy - 1, LEAF[1])
    if autumn:  # the copper tree keeps its weathered birdhouse, nailed to the trunk
        bx, by = tx - 2, h - 30
        plane(cv, rect_set(bx, by + 4, 13, 11), WOOD, 3)
        for i in range(8):
            cv.hline(bx - 1 + i, by + 4 - i // 2 - 1, 15 - 2 * i, NAP[2] if i else NAP[1])
        for i in range(0, 8, 2):
            cv.hline(bx - 1 + i, by + 4 - i // 2 - 1, 2, NAP[3])
        for (x, y) in disc(bx + 6.5, by + 9, 2.2):
            cv.set(x, y, WOOD[0])
        cv.hline(bx + 4, by + 13, 6, WOOD[1]); cv.set(bx + 4, by + 12, WOOD[4])
    return cv


def pine() -> Canvas:
    """A tiered conifer, 36 x 76: cone-shaded tiers with light clumps on the lit flank."""
    w, h = 36, 76
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2 - 0.5
    style.trunk(cv, int(cx) - 2, h - 16, h, 5, WOOD)
    tiers = ((1, 14, 6.0), (10, 16, 9.5), (20, 17, 12.5), (31, 17, 15.0), (42, 18, 17.0))
    for t, (ty, th, half) in enumerate(tiers):
        tier = {}
        for y in range(ty, ty + th):
            frac = (y - ty + 1) / th
            span = half * (0.28 + 0.72 * frac)
            for x in range(int(cx - span), int(cx + span) + 2):
                if not (0 <= x < w):
                    continue
                if y == ty + th - 1 and (x + t) % 4 == 0:
                    continue  # sawtooth hem
                side = (x + 0.5 - cx) / max(1.0, span)
                lv = -0.8 * side - 0.5 * (frac - 0.4)
                tier[(x, y)] = 3 if lv > 0.45 else 2 if lv > -0.05 else 1 if lv > -0.6 else 0
        for (x, y), tone in tier.items():
            cv.set(x, y, PINE[tone])
        for (x, y), tone in tier.items():
            if (x, y + 1) not in tier:
                cv.set(x, y, PINE[max(0, tone - 1)])
        for k in range(3 + t):
            yy = ty + 3 + int(noise2(k, t, 61) * max(1, th - 6))
            span = half * (0.28 + 0.72 * (yy - ty + 1) / th)
            xx = int(cx - span * (0.2 + 0.6 * noise2(k, t, 62)))
            if (xx, yy) in tier and (xx + 3, yy) in tier and tier[(xx, yy)] >= 2:
                cv.hline(xx, yy, 3, PINE[4])
                cv.set(xx + 3, yy, PINE[3])
                cv.hline(xx, yy + 1, 4, PINE[1])
    cv.set(int(cx), 0, PINE[3])
    return cv


def bush() -> Canvas:
    """A round shrub, 32 x 24, below companion height; stems peek out underneath."""
    w, h = 32, 24
    cv = Canvas(w, h, pad=PAD)
    for x in (9, 14, 19):
        cv.rect(x, h - 4, 3, 3, WOOD[1]); cv.set(x, h - 4, WOOD[2])
    canopy(cv, [(10, 10, 8), (22, 10, 8), (16, 8, 8), (16, 13, 7.5)], LEAF, seed=5)
    for x, y in ((9, 6), (18, 4), (13, 12)):
        cv.set(x, y, CREAM[3]); cv.set(x + 1, y + 1, GOLD[3])
    return cv


def rock(n: int) -> Canvas:
    """A field stone, 20 x 14: faceted planes, moss on the second one."""
    cv = Canvas(20, 14, pad=PAD)
    pts = {(x, y) for (x, y) in (oval(10.5, 7.5, 8.6, 5.6) | oval(7, 8.5, 5.6, 4.6))
           if 0 <= x < 20 and 0 <= y < 14}
    style.facet_stone(cv, pts, STONE, moss=LEAF if n else None, seed=n + 2, outline=None)
    return cv


# ---- small props -------------------------------------------------------------
def post(cv: Canvas, x: int, y0: int, y1: int, w: int = 3, ramp=WOOD, cap: bool = True):
    """A round post: a lit stripe left of centre, the far side dark, a lit cap on top."""
    for y in range(y0, y1):
        for i in range(w):
            t = 3 if i == 0 else 4 if i == 1 else 2 if i < w - 1 else 1
            cv.set(x + i, y, ramp[t])
    if cap:
        cv.hline(x, y0, w, ramp[4]); cv.set(x + w - 1, y0, ramp[3])


def reading_nook() -> Canvas:
    """The reading bench, 44 x 28: slats that show their lit tops and darker fronts, the
    backrest's shadow across the seat, a plump cushion, books and a warm mug."""
    w, h = 44, 28
    cv = Canvas(w, h, pad=PAD)
    for x in (3, 38):
        post(cv, x, 1, 19)
    for y in (2, 6, 10):  # backrest slats: a lit top, a face, a dark underside
        cv.hline(2, y, 40, WOOD[4]); cv.hline(2, y + 1, 40, WOOD[3]); cv.hline(2, y + 2, 40, WOOD[1])
        cv.set(2, y, WOOD[3])
    # seat: three planks seen from above, then its front edge and the legs
    for y in range(13, 19):
        for x in range(1, 43):
            r = (y - 13) % 2
            cv.set(x, y, WOOD[4] if r == 0 and y < 17 else WOOD[3] if r == 0 else WOOD[2])
    for x in range(1, 43):
        detail.shade(cv, x, 13, 1); detail.shade(cv, x + 1, 14, 1)  # the backrest's shadow
    cv.hline(1, 19, 42, WOOD[2]); cv.hline(1, 20, 42, WOOD[0])
    for x in (3, 37):
        post(cv, x, 21, 28, w=4, cap=False)
        cv.hline(x, 21, 4, WOOD[1])  # shaded under the seat
    # cushion: puffed, lit on its upper left, with a button
    for (x, y) in oval(15, 14, 9, 3.2):
        nx, ny = (x + 0.5 - 15) / 9, (y + 0.5 - 14) / 3.2
        lit = -0.6 * nx - 0.8 * ny
        cv.set(x, y, NAP[4] if lit > 0.5 else NAP[3] if lit > -0.3 else NAP[2])
    cv.set(15, 14, NAP[1]); cv.set(14, 13, NAP[4])
    for x in range(7, 24):
        detail.shade(cv, x, 17, 1)  # the cushion's shadow on the seat
    # two books (spines, page edges) and a mug with a curl of steam
    cv.rect(27, 13, 10, 3, RED[2]); cv.hline(27, 13, 10, RED[3]); cv.vline(27, 13, 3, RED[4])
    cv.hline(28, 14, 8, PLASTER[5]); cv.hline(28, 15, 8, RED[1])
    cv.rect(28, 10, 9, 3, WTR[2]); cv.hline(28, 10, 9, WTR[3]); cv.vline(28, 10, 3, WTR[4])
    cv.hline(29, 11, 7, PLASTER[5]); cv.hline(29, 12, 7, WTR[1])
    cv.rect(32, 5, 4, 5, PLASTER[4]); cv.vline(32, 5, 5, PLASTER[5]); cv.vline(35, 5, 5, PLASTER[2])
    cv.hline(32, 5, 4, PLASTER[3]); cv.hline(33, 5, 2, WOOD[1])
    cv.set(36, 6, PLASTER[3]); cv.set(37, 7, PLASTER[2]); cv.set(36, 8, PLASTER[2])
    cv.set(33, 3, PLASTER[5]); cv.set(34, 2, PLASTER[4]); cv.set(33, 1, PLASTER[5])
    return cv


def lantern() -> Canvas:
    """A leaf lantern on a bent post, 14 x 40: taller than the companion."""
    w, h = 14, 40
    cv = Canvas(w, h, pad=PAD)
    post(cv, 2, 6, 39)
    cv.hline(1, 39, 5, WOOD[1])
    cv.hline(3, 5, 7, WOOD[4]); cv.hline(3, 6, 7, WOOD[2]); cv.hline(3, 7, 7, WOOD[1]); cv.vline(9, 7, 3, WOOD[2])
    # glass housing with a warm glow: brightest at the flame, darker toward the frame
    cv.rect(6, 10, 7, 12, WOOD[1]); cv.vline(6, 10, 12, WOOD[2])
    for (x, y) in rect_set(7, 11, 5, 10):
        d = abs(x - 9) + abs(y - 16) * 0.6
        cv.set(x, y, GOLD[4] if d < 1.5 else GOLD[3] if d < 3.2 else GOLD[2])
    cv.vline(7, 11, 9, GOLD[4]); cv.set(9, 16, PLASTER[5])
    cv.vline(9, 11, 10, WOOD[1])  # the glazing bar
    cv.hline(5, 9, 9, LEAF[2]); cv.hline(6, 8, 7, LEAF[3]); cv.hline(7, 7, 5, LEAF[4]); cv.set(5, 9, LEAF[3])
    cv.hline(6, 22, 7, WOOD[3]); cv.hline(7, 23, 5, WOOD[1])
    cv.set(1, 30, LEAF[2]); cv.set(0, 29, LEAF[3]); cv.set(5, 33, LEAF[2]); cv.set(6, 32, LEAF[3])
    return cv


def mailbox() -> Canvas:
    """A red mailbox on a post, 18 x 32: a rounded tin box lit along its left, a door
    in a frame, the flag up and a postcard peeking out."""
    w, h = 18, 32
    cv = Canvas(w, h, pad=PAD)
    post(cv, 7, 15, 31, w=4)
    cv.hline(5, 31, 8, WOOD[1])
    body = rect_set(1, 4, 15, 12) | rect_set(2, 2, 13, 2) | rect_set(3, 1, 11, 1)
    for (x, y) in body:
        t = 4 if x in (2, 3) else 3 if x < 9 else 2 if x < 14 else 1
        if y >= 14:
            t -= 1
        cv.set(x, y, RED[max(0, t)])
    cv.hline(3, 1, 11, RED[4]); cv.hline(2, 2, 3, RED[4])
    cv.hline(1, 8, 15, RED[1]); cv.hline(1, 9, 15, RED[3])  # the lid's seam
    cv.rect(4, 11, 9, 3, PLASTER[4]); cv.hline(4, 11, 9, PLASTER[5]); cv.hline(4, 13, 9, PLASTER[2])
    cv.set(7, 12, RED[2]); cv.set(8, 12, NAP[3])
    cv.vline(16, 3, 8, GOLD[2]); cv.rect(16, 2, 2, 3, GOLD[3]); cv.set(16, 2, GOLD[4])
    detail.cast(cv, rect_set(1, 4, 15, 12), 1, 1, k=1, on=WOOD, reach=2)
    return cv


def arrow_board(cv: Canvas, y: int, left: bool):
    """A plank arrow: lit top edge, grain, a darker bottom edge showing its thickness,
    nail heads, and its shadow on the post below."""
    board = rect_set(3, y, 22, 8)
    tip = [(25, y + 1), (25, y + 2), (25, y + 3), (25, y + 4), (25, y + 5), (25, y + 6),
           (26, y + 2), (26, y + 3), (26, y + 4), (26, y + 5), (27, y + 3), (27, y + 4)]
    if left:
        tip = [(27 - x, yy) for (x, yy) in tip]
    board |= set(tip)
    detail.boards(cv, board, WOOD, 3, y, board=4, seed=y, joints=False, grain=0.08)
    for (x, yy) in board:
        if (x, yy - 1) not in board:
            cv.set(x, yy, WOOD[4])
        elif (x, yy + 1) not in board:
            cv.set(x, yy, WOOD[1])
    cv.hline(8, y + 3, 5, WOOD[1]); cv.hline(14, y + 3, 4, WOOD[1]); cv.hline(8, y + 5, 8, WOOD[1])
    nx = 5 if not left else 22
    cv.set(nx, y + 2, STONE[4]); cv.set(nx, y + 3, STONE[1])


def signpost() -> Canvas:
    """Two arrow boards on a post, 28 x 36: to the missions and back home."""
    w, h = 28, 36
    cv = Canvas(w, h, pad=PAD)
    post(cv, 12, 6, 35, w=4)
    cv.hline(10, 35, 8, WOOD[1])
    for (y, left) in ((2, False), (14, True)):
        arrow_board(cv, y, left)
        cv.hline(12, y + 8, 4, WOOD[0]); cv.hline(13, y + 9, 3, WOOD[1])  # its shadow on the post
    return cv


def watering_can() -> Canvas:
    """A painted watering can, 18 x 14."""
    w, h = 18, 14
    cv = Canvas(w, h, pad=PAD)
    body = rect_set(3, 5, 9, 8) | rect_set(4, 4, 7, 1)
    plane(cv, body, WTR, 3)
    for i in range(5):
        cv.set(12 + i, 7 - i // 2, WTR[2]); cv.set(12 + i, 8 - i // 2, WTR[1])
    cv.rect(16, 3, 2, 3, WTR[3]); cv.set(17, 3, WTR[4])
    for (x, y) in ((4, 3), (5, 2), (6, 1), (7, 1), (8, 1), (9, 2), (10, 3)):
        cv.set(x, y, STONE[2])
    cv.hline(4, 9, 7, WTR[4])
    return cv


def bowl() -> Canvas:
    """The food bowl, 18 x 10, heaped with seeds."""
    w, h = 18, 10
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(9, 5.5, 8.5, 4.4):
        cv.set(x, y, RED[3] if y < 6 else RED[2])
    for x in range(2, 16):
        cv.set(x, 9, RED[1])
    for (x, y) in oval(9, 4, 6.4, 2.2):
        cv.set(x, y, GOLD[3] if (x * 3 + y) % 4 else GOLD[2])
    cv.set(6, 3, GOLD[4]); cv.set(10, 2, GOLD[4])
    return cv


def bed() -> Canvas:
    """The nap cushion by the hut, 30 x 16: a raised lavender rim around a soft well,
    a cream pillow and a folded blanket."""
    w, h = 30, 16
    cv = Canvas(w, h, pad=PAD)
    rim = oval(15, 8.5, 14.5, 7.4)
    well = oval(15, 8.2, 11.0, 4.6)
    for (x, y) in rim:
        nx = (x + 0.5 - 15) / 14.5
        ny = (y + 0.5 - 8.5) / 7.4
        cv.set(x, y, NAP[4] if -0.6 * nx - 0.8 * ny > 0.55 else NAP[3] if ny < 0.45 else NAP[2])
    for (x, y) in well:
        cv.set(x, y, NAP[1] if y < 7 else NAP[2])
    plane(cv, oval(9, 8.4, 4.2, 2.6), CREAM, 2)
    plane(cv, rect_set(15, 7, 10, 5), CREAM, 2)
    cv.hline(15, 9, 10, NAP[3]); cv.hline(15, 10, 10, NAP[3])
    cv.rect(19, 7, 3, 2, RED[4])  # a mended patch
    return cv


def meadow_sign() -> Canvas:
    """The meadow's hand-painted sign, 22 x 28."""
    w, h = 22, 28
    cv = Canvas(w, h, pad=PAD)
    post(cv, 9, 12, 27, w=4)
    cv.hline(7, 27, 8, WOOD[1])
    board = rect_set(1, 2, 20, 11)
    detail.boards(cv, board, WOOD, 3, 2, board=4, seed=5, joints=False, grain=0.06)
    cv.hline(1, 2, 20, WOOD[4]); cv.vline(1, 2, 11, WOOD[4]); cv.hline(1, 12, 20, WOOD[1]); cv.vline(20, 3, 10, WOOD[2])
    cv.vline(5, 5, 6, LEAF[2]); cv.set(4, 6, LEAF[3]); cv.set(6, 7, LEAF[3]); cv.set(4, 9, LEAF[4])
    cv.set(5, 4, RED[3]); cv.set(4, 4, RED[4]); cv.set(6, 4, RED[3]); cv.set(5, 3, RED[4])
    cv.hline(9, 5, 9, WOOD[1]); cv.hline(9, 8, 7, WOOD[1])
    cv.hline(9, 13, 4, WOOD[0]); cv.hline(10, 14, 3, WOOD[1])
    return cv


def fence_h(length: int) -> Canvas:
    """A split-rail fence segment, 18 tall: round posts every 10 pixels with lit caps,
    rails that show a lit top and a dark underside, and the rails' shadows on the posts."""
    h = 18
    cv = Canvas(length, h, pad=PAD)
    for ry in (5, 11):
        cv.hline(0, ry, length, WOOD[4]); cv.hline(0, ry + 1, length, WOOD[3]); cv.hline(0, ry + 2, length, WOOD[1])
        for x in range(0, length, 7):
            cv.set(x + 3, ry + 1, WOOD[2])  # grain
    for x in range(1, length - 4, 10):
        for y in range(1, 17):
            for i in range(5):
                t = 3 if i == 0 else 4 if i == 1 else 3 if i == 2 else 2 if i == 3 else 1
                cv.set(x + i, y, WOOD[t])
        cv.hline(x, 1, 5, WOOD[4]); cv.set(x + 4, 1, WOOD[3]); cv.hline(x + 1, 2, 3, WOOD[2])  # cut top
        for ry in (8, 14):
            cv.hline(x + 1, ry, 4, WOOD[1])  # the rail's shadow on the post
        cv.hline(x, 16, 5, WOOD[1])
    for x in (16, length - 24):
        cv.vline(x, 7, 9, LEAF[1])
        for dx, y in ((-1, 8), (1, 10), (-1, 12), (1, 14)):
            cv.hline(x + dx, y, 2, LEAF[2]); cv.set(x + dx, y - 1, LEAF[3])
        cv.set(x + 1, 6, NAP[4])
    return cv


def gate() -> Canvas:
    """The garden gate, 48 x 44: fieldstone pillars with capstones that show their tops,
    an arched beam with a lit upper face, and the arena's pennant in soft folds."""
    w, h = 48, 44
    cv = Canvas(w, h, pad=PAD)
    for x in (2, 39):
        detail.stones(cv, x, 11, 7, 32, STONE, seed=x, course=4)
        detail.shade_set(cv, {(xx, yy) for xx in (x + 5,) for yy in range(11, 43)}, 1)
        cv.vline(x, 11, 32, STONE[3]); cv.vline(x + 6, 11, 32, STONE[1])
        cv.rect(x - 1, 6, 9, 5, STONE[3])
        cv.hline(x - 1, 6, 9, STONE[4]); cv.hline(x - 1, 7, 9, STONE[4]); cv.set(x + 7, 7, STONE[3])
        cv.hline(x - 1, 9, 9, STONE[2]); cv.hline(x - 1, 10, 9, STONE[1])
        cv.hline(x, 11, 7, STONE[0])  # the capstone's shadow on the pillar
    for x in range(6, 42):
        y = 3 + int(((x - 23.5) / 18) ** 2 * 5)
        cv.set(x, y, WOOD[4]); cv.set(x, y + 1, WOOD[4] if x < 24 else WOOD[3]); cv.set(x, y + 2, WOOD[2]); cv.set(x, y + 3, WOOD[1])
    pennant = rect_set(18, 8, 12, 12) | {(x, y) for y in range(20, 24) for x in range(18 + (y - 20) * 2 - 1, 30 - (y - 20) * 2 + 1) if 18 <= x < 30}
    for (x, y) in pennant:
        f = (x - 18) % 6
        t = 3 if f in (1, 2) else 2 if f in (0, 3) else 1
        cv.set(x, y, RED[t])
    cv.hline(18, 8, 12, RED[4])
    for i in range(6):
        cv.set(21 + i, 11 + i, PLASTER[5]); cv.set(26 - i, 11 + i, PLASTER[4])
    cv.vline(23, 6, 3, WOOD[1]); cv.vline(24, 6, 3, WOOD[1])
    return cv


def frog() -> Canvas:
    """The pond's shy resident, 12 x 9."""
    cv = Canvas(12, 9, pad=PAD)
    for (x, y) in oval(6, 5.5, 5.4, 3.2):
        cv.set(x, y, LEAF[3] if y < 5 else LEAF[2])
    for ex in (3, 8):
        for (x, y) in disc(ex + 0.5, 2.5, 1.6):
            cv.set(x, y, LEAF[3])
        cv.set(ex, 2, CREAM[3]); cv.set(ex + 1, 2, STONE[0])
    cv.hline(4, 6, 4, LEAF[1]); cv.set(1, 7, LEAF[2]); cv.set(10, 7, LEAF[2])
    return cv


def bridge(w: int, h: int) -> Canvas:
    """The bridge deck (a flat decal): planks across the stream with dark gaps, lit top
    edges, grain and nail heads; side beams that show a lit top and a darker inner face;
    capped posts; and the deck's thickness showing at its southern end."""
    cv = Canvas(w, h, pad=PAD)
    deck = rect_set(5, 2, w - 10, h - 4)
    for (x, y) in deck:
        pi, r = divmod(y - 2, 4)
        t = 2 + (1 if noise2(pi, 1, 41) > 0.8 else -1 if noise2(pi, 2, 41) < 0.15 else 0)
        if r == 3:
            t = 0  # the gap between planks
        elif r == 0:
            t += 1
        elif noise2(x // 4, y, 42) < 0.06:
            t -= 1
        cv.set(x, y, WOOD[max(0, min(4, t))])
    for y in range(3, h - 3, 4):
        for nx in (8, w - 9):
            cv.set(nx, y, STONE[4]); cv.set(nx, y + 1, WOOD[1])
    for x in range(5, w - 5):
        cv.set(x, h - 2, WOOD[1]); cv.set(x, h - 1, WOOD[0])  # the deck's southern edge
    for x0, lit in ((1, True), (w - 5, False)):
        for y in range(0, h):
            cv.set(x0, y, WOOD[3] if lit else WOOD[2]); cv.set(x0 + 1, y, WOOD[4] if lit else WOOD[3])
            cv.set(x0 + 2, y, WOOD[3] if lit else WOOD[2]); cv.set(x0 + 3, y, WOOD[1])
        for py in (0, h // 2 - 2, h - 4):
            cv.rect(x0 - 1, py, 6, 4, WOOD[3]); cv.hline(x0 - 1, py, 6, WOOD[4]); cv.hline(x0 - 1, py + 1, 6, WOOD[4])
            cv.set(x0 + 4, py, WOOD[3]); cv.hline(x0 - 1, py + 3, 6, WOOD[1])
    for y in range(2, h - 2):  # the beams' shadow on the deck
        detail.shade(cv, 5, y, 1)
    return cv


def props() -> dict[str, Canvas]:
    return {
        'tree': tree(True), 'tree_small': tree(False), 'tree_autumn': tree(True, True),
        'pine': pine(), 'hut': hut(), 'bed': bed(), 'mailbox': mailbox(), 'stall': stall(),
        'signpost': signpost(), 'bowl': bowl(), 'bush': bush(), 'rock0': rock(0), 'rock1': rock(1),
        'gate': gate(), 'reading_nook': reading_nook(), 'watering_can': watering_can(),
        'lantern': lantern(), 'frog': frog(), 'meadow_sign': meadow_sign(),
    }


if __name__ == '__main__':
    import os
    from PIL import Image
    sheet_items = props()
    sheet_items = {k: style.finalize(v, name=k) for k, v in sheet_items.items()}
    pad = 6
    width = sum(v.w for v in sheet_items.values()) + pad * (len(sheet_items) + 1)
    height = max(v.h for v in sheet_items.values()) + 2 * pad + 40
    out = Image.new('RGBA', (width, height), tuple(int(G[2][i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    x = pad
    # a companion-sized marker (32 x 26) for scale
    for key, cv in sheet_items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    path = os.environ.get('SHEET', '/tmp/props.png')
    out.save(path)
    print('sheet', path, out.size)
