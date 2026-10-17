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
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, RED, SAND, STONE, WOOD, WTR
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
def hut() -> Canvas:
    """The nap hut, 104 x 92: a lavender shingle roof with a timber gable, plaster
    walls, a round-topped door (16 x 28) and a stone foundation."""
    w, h = 104, 92
    cv = Canvas(w, h, pad=PAD)
    apex_x, apex_y, eave = 51.5, 18, 46

    def gable(x, y):
        if y < apex_y or y > eave:
            return False
        half = (y - apex_y) * (32 / (eave - apex_y))
        return abs(x + 0.5 - apex_x) <= half

    # chimney behind the right slope
    for y in range(0, 20):
        for x in range(72, 82):
            cv.set(x, y, STONE[3] if x == 72 else STONE[1] if x == 81 else STONE[2])
    for y in (5, 11, 17):
        cv.hline(73, y, 8, STONE[1])
    cv.rect(71, 0, 12, 3, STONE[3]); cv.hline(71, 0, 12, STONE[4]); cv.hline(71, 2, 12, STONE[1])
    cv.rect(74, 1, 6, 1, '#2A2628')

    # roof: two planes of staggered shingles; the lit left plane is one step lighter
    for y in range(4, eave + 1):
        inset = 12 - (y - 4) * 12 / (eave - 4)
        for x in range(w):
            if x < inset or x > w - 1 - inset or gable(x, y):
                continue
            if 71 <= x <= 82 and y < 20 and x > apex_x:
                continue  # the chimney stands in front of this patch
            left = x < apex_x
            body, seam, lit = (NAP[3], NAP[2], NAP[4]) if left else (NAP[2], NAP[1], NAP[3])
            row = (y - 4) % 5
            joint = (x + ((y - 4) // 5) * 4) % 8 == 0
            col = body
            if row == 4 or joint:
                col = seam
            elif row == 0 and (x + ((y - 4) // 5) * 4) % 8 in (1, 2):
                col = lit
            cv.set(x, y, col)
    # ridge cap running back from the gable apex
    for y in range(3, apex_y + 1):
        cv.hline(49, y, 5, WOOD[2]); cv.set(49, y, WOOD[4]); cv.set(50, y, WOOD[3]); cv.set(53, y, WOOD[1])
    cv.hline(49, 3, 5, WOOD[4])
    # gable end: vertical timber boards, a round vent and a crescent sign
    for y in range(apex_y, eave + 1):
        for x in range(w):
            if gable(x, y):
                pos = (x - 20) % 5
                cv.set(x, y, WOOD[3] if pos == 0 else WOOD[1] if pos == 4 else WOOD[2])
    for (x, y) in disc(apex_x, 33, 5.2):
        cv.set(x, y, WOOD[0])
    for (x, y) in disc(apex_x, 33, 4.0):
        cv.set(x, y, '#2E2A3D')
    for (x, y) in disc(apex_x - 0.6, 32.6, 2.6) - disc(apex_x + 0.8, 31.8, 2.2):
        cv.set(x, y, GOLD[3])
    # fascia boards along the gable and the eave beam
    for y in range(apex_y, eave + 1):
        half = (y - apex_y) * (32 / (eave - apex_y))
        lx, rx = int(apex_x - half) - 1, int(apex_x + half) + 1
        cv.set(lx, y, WOOD[4]); cv.set(lx - 1, y, WOOD[3])
        cv.set(rx, y, WOOD[2]); cv.set(rx + 1, y, WOOD[1])
    for x in range(0, w):
        if cv.get(x, eave)[3]:
            cv.set(x, eave, WOOD[1])
            cv.set(x, eave - 1, WOOD[3] if x < apex_x else WOOD[2])

    # walls: one plaster plane under a flat eave shadow, timber corners and sill
    wall_top, wall_bottom = eave + 1, 82
    plane(cv, rect_set(8, wall_top, 88, wall_bottom - wall_top), CREAM, 2, dark_edge=False)
    for x in range(8, 96):
        for y in range(wall_top, wall_top + 3):
            cv.set(x, y, CREAM[1] if y < wall_top + 2 else CREAM[2])
    for x in range(90, 96):  # the side wall turning away from the light
        for y in range(wall_top + 3, wall_bottom):
            cv.set(x, y, CREAM[1])
    for x0, ramp_i in ((8, 3), (89, 2)):
        for y in range(wall_top, wall_bottom):
            cv.set(x0, y, WOOD[ramp_i + 1]); cv.set(x0 + 1, y, WOOD[ramp_i]); cv.set(x0 + 2, y, WOOD[ramp_i - 1])
    cv.hline(8, wall_bottom - 2, 88, WOOD[2]); cv.hline(8, wall_bottom - 1, 88, WOOD[1])

    # door: 16 x 28, round top, stone arch frame, planks lit from the left
    dx0, dy0, dw, dh = 44, 54, 16, 28
    door = {(x, y) for (x, y) in disc(dx0 + dw / 2, dy0 + dw / 2, dw / 2) if y < dy0 + dh}
    door |= rect_set(dx0, dy0 + dw // 2, dw, dh - dw // 2)
    arch = set()
    for (x, y) in door:
        for ax, ay in ((-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1), (-2, 0), (2, 0), (0, -2)):
            if (x + ax, y + ay) not in door:
                arch.add((x + ax, y + ay))
    for (x, y) in arch:
        if y < dy0 + dh:
            cv.set(x, y, STONE[3] if x < dx0 + dw / 2 else STONE[2])
            if (x + y) % 5 == 0:
                cv.set(x, y, STONE[1])
    for (x, y) in door:
        pos = (x - dx0) % 4
        col = WOOD[3] if pos == 0 else WOOD[1] if pos == 3 else WOOD[2]
        cv.set(x, y, col)
    cv.hline(dx0, dy0 + 14, dw, WOOD[1]); cv.hline(dx0, dy0 + 22, dw, WOOD[1])
    cv.set(dx0 + 12, dy0 + 17, GOLD[4]); cv.set(dx0 + 12, dy0 + 18, GOLD[2])

    # windows with deep sills; a flower box under the right one
    for wx in (18, 70):
        cv.rect(wx, 57, 16, 14, WOOD[1])
        cv.rect(wx + 2, 59, 12, 10, '#2E3A4E')
        for (x, y) in rect_set(wx + 2, 59, 12, 10):
            if x - wx - 2 + y - 59 < 5:
                cv.set(x, y, WTR[3] if x - wx - 2 + y - 59 < 3 else WTR[2])
        cv.vline(wx + 7, 59, 10, WOOD[2]); cv.hline(wx + 2, 63, 12, WOOD[2])
        cv.hline(wx, 57, 16, WOOD[3])
        cv.rect(wx - 1, 71, 18, 2, WOOD[3]); cv.hline(wx - 1, 72, 18, WOOD[1])
    cv.rect(69, 73, 18, 4, WOOD[2]); cv.hline(69, 73, 18, WOOD[3]); cv.hline(69, 76, 18, WOOD[1])
    for i, x in enumerate(range(70, 86, 3)):
        petal = (RED[3], GOLD[3], NAP[4], RED[3], CREAM[3], NAP[3])[i]
        cv.set(x, 71, LEAF[3]); cv.set(x + 1, 71, LEAF[2])
        cv.set(x, 70, petal); cv.set(x + 1, 70, petal); cv.set(x, 69, petal)
    # ivy climbing the lit corner
    for (ix, iy) in ((11, 52), (12, 56), (11, 60), (12, 64), (11, 68), (12, 72)):
        cv.vline(ix, iy, 4, LEAF[1]); cv.set(ix + 1, iy, LEAF[3]); cv.set(ix + 1, iy + 1, LEAF[4])
        cv.set(ix - 1, iy + 2, LEAF[2])

    # foundation course and a doormat at the step
    stone_blocks(cv, 6, wall_bottom, 92, 6)
    cv.rect(42, 88, 20, 4, NAP[2]); cv.hline(42, 88, 20, NAP[3]); cv.hline(42, 91, 20, NAP[1])
    cv.hline(44, 89, 16, NAP[4])
    return cv


# ---- Moss's stall ----------------------------------------------------------
def stall() -> Canvas:
    """Moss's hat stall, 88 x 72: a striped awning over a shelf of hats and a planked
    counter at companion height."""
    w, h = 88, 72
    cv = Canvas(w, h, pad=PAD)
    # posts: cylinders lit from the left
    for x in (4, 80):
        for y in range(16, 68):
            cv.set(x, y, WOOD[4]); cv.set(x + 1, y, WOOD[3]); cv.set(x + 2, y, WOOD[2]); cv.set(x + 3, y, WOOD[1])
    # the shaded recess under the awning, with a back shelf of hats
    for y in range(28, 46):
        cv.hline(8, y, 72, WOOD[0] if y < 34 else '#4A2F25')
    cv.hline(8, 44, 72, WOOD[2]); cv.hline(8, 45, 72, WOOD[1])
    # a cap, a top hat, a straw hat, a crown and a beanie, each in its own material
    for (x, y) in oval(18, 42, 7, 3) | rect_set(12, 37, 12, 5):
        cv.set(x, y, WTR[2] if y < 41 else WTR[1])
    cv.hline(12, 37, 10, WTR[3]); cv.hline(14, 43, 12, WTR[1])
    for y in range(30, 43):
        cv.hline(30, y, 9, STONE[1] if y < 41 else STONE[0])
    cv.vline(30, 30, 11, STONE[2]); cv.hline(30, 38, 9, RED[2]); cv.hline(27, 43, 15, STONE[0])
    for (x, y) in oval(51, 41, 8, 3):
        cv.set(x, y, SAND[2] if y < 41 else SAND[1])
    for (x, y) in oval(51, 38, 4, 3):
        cv.set(x, y, SAND[2] if x < 51 else SAND[1])
    cv.hline(47, 39, 9, RED[3])
    for i, x in enumerate(range(62, 71)):
        top = 34 if i % 4 == 0 else 36
        cv.vline(x, top, 43 - top, GOLD[3] if x < 67 else GOLD[2])
    cv.hline(62, 43, 9, GOLD[1]); cv.set(62, 34, GOLD[4]); cv.set(66, 39, RED[3])
    # counter: lit top surface, planked front, dark base
    cv.rect(2, 46, 84, 3, WOOD[4]); cv.hline(2, 48, 84, WOOD[3])
    planks(cv, 2, 49, 84, 17, WOOD, step=8, vertical=True, base=2)
    for x in range(78, 86):
        for y in range(49, 66):
            cv.set(x, y, WOOD[1] if (x - 2) % 8 != 7 else WOOD[0])
    cv.hline(2, 66, 84, WOOD[0]); cv.hline(2, 65, 84, WOOD[1])
    # ledger and a potted seedling on the counter
    cv.rect(52, 44, 12, 3, NAP[1]); cv.hline(53, 44, 10, CREAM[3]); cv.vline(58, 44, 2, CREAM[1])
    cv.rect(16, 42, 6, 5, RED[2]); cv.hline(16, 42, 6, RED[3]); cv.vline(21, 43, 4, RED[1])
    cv.set(18, 40, LEAF[3]); cv.set(19, 39, LEAF[4]); cv.set(17, 41, LEAF[2]); cv.set(20, 41, LEAF[2])
    # bolts of fabric by the base
    for (bx, ramp) in ((8, NAP), (66, WTR)):
        cv.rect(bx, 67, 14, 4, ramp[2]); cv.hline(bx, 67, 14, ramp[3]); cv.hline(bx, 70, 14, ramp[1])
    # awning: a lit top slope and a front valance of folded stripes, scalloped hem
    for y in range(8, 29):
        for x in range(0, w):
            stripe = (x // 8) % 2 == 0
            fold = x % 8
            ramp = LEAF if stripe else CREAM
            hi = len(ramp) - 1
            if y < 15:
                col = ramp[min(hi, 3)] if fold < 7 else ramp[2]
            else:
                col = ramp[min(hi, 3)] if fold == 0 else ramp[1] if fold == 7 else ramp[2]
            cv.set(x, y, col)
    cv.hline(0, 8, w, LEAF[1]); cv.hline(0, 15, w, LEAF[1])
    for x in range(0, w):
        fold = x % 8
        stripe = (x // 8) % 2 == 0
        ramp = LEAF if stripe else CREAM
        if fold in (2, 3, 4, 5):
            cv.set(x, 29, ramp[2])
            if fold in (3, 4):
                cv.set(x, 30, ramp[1])
    # hanging sign with a little hat
    cv.rect(30, 0, 28, 8, WOOD[3]); cv.hline(30, 0, 28, WOOD[4]); cv.hline(30, 7, 28, WOOD[1])
    cv.vline(57, 1, 6, WOOD[2])
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
def reading_nook() -> Canvas:
    """The reading bench, 44 x 28: slatted back, a lavender cushion, books and a mug."""
    w, h = 44, 28
    cv = Canvas(w, h, pad=PAD)
    # back rest: two posts and three slats
    for x in (3, 38):
        plane(cv, rect_set(x, 1, 3, 18), WOOD, 2)
    for y in (2, 6, 10):
        plane(cv, rect_set(2, y, 40, 3), WOOD, 3)
    # seat: lit top plane over a shaded front edge, then the legs
    plane(cv, rect_set(1, 14, 42, 5), WOOD, 3)
    cv.hline(1, 19, 42, WOOD[1]); cv.hline(1, 20, 42, WOOD[0])
    for x in (3, 37):
        plane(cv, rect_set(x, 21, 4, 7), WOOD, 2)
    # cushion
    plane(cv, rect_set(6, 12, 18, 5), NAP, 3)
    cv.set(14, 13, NAP[2]); cv.set(15, 14, NAP[2])
    # a stack of two books and a warm mug
    plane(cv, rect_set(27, 13, 10, 3), RED, 3)
    plane(cv, rect_set(28, 10, 9, 3), WTR, 3)
    cv.hline(28, 11, 8, CREAM[3]); cv.hline(27, 14, 9, CREAM[3])
    plane(cv, rect_set(32, 6, 4, 4), CREAM, 2)
    cv.set(36, 7, CREAM[1]); cv.set(37, 8, CREAM[1])
    cv.set(33, 4, CREAM[3]); cv.set(34, 3, CREAM[3])
    return cv


def lantern() -> Canvas:
    """A leaf lantern on a bent post, 14 x 40: taller than the companion."""
    w, h = 14, 40
    cv = Canvas(w, h, pad=PAD)
    plane(cv, rect_set(2, 6, 3, 33), WOOD, 2)
    cv.hline(1, 39, 5, WOOD[1])
    cv.hline(3, 5, 7, WOOD[3]); cv.hline(3, 6, 7, WOOD[1]); cv.vline(9, 7, 3, WOOD[2])
    # glass housing with a warm glow, a leaf cap and a base ring
    plane(cv, rect_set(6, 10, 7, 12), WOOD, 1, lit_edge=False)
    for (x, y) in rect_set(7, 11, 5, 10):
        cv.set(x, y, GOLD[3] if x < 9 else GOLD[2])
    cv.vline(7, 11, 9, GOLD[4]); cv.set(8, 12, CREAM[3])
    cv.hline(5, 9, 9, LEAF[2]); cv.hline(6, 8, 7, LEAF[3]); cv.hline(7, 7, 5, LEAF[4])
    cv.hline(6, 22, 7, WOOD[2]); cv.hline(7, 23, 5, WOOD[1])
    # a living sprig below the housing
    cv.set(1, 30, LEAF[2]); cv.set(0, 29, LEAF[3]); cv.set(5, 33, LEAF[2]); cv.set(6, 32, LEAF[3])
    return cv


def mailbox() -> Canvas:
    """A red mailbox on a post, 18 x 32, with its flag up and a postcard peeking out."""
    w, h = 18, 32
    cv = Canvas(w, h, pad=PAD)
    plane(cv, rect_set(7, 15, 4, 16), WOOD, 2)
    cv.hline(5, 31, 8, WOOD[1])
    body = rect_set(1, 4, 15, 12) | rect_set(2, 2, 13, 2) | rect_set(3, 1, 11, 1)
    plane(cv, body, RED, 3)
    cv.hline(3, 8, 11, RED[1])  # the lid's seam
    plane(cv, rect_set(4, 11, 9, 3), CREAM, 2)
    cv.hline(5, 11, 6, CREAM[3]); cv.set(7, 12, RED[2]); cv.set(8, 12, NAP[3])
    plane(cv, rect_set(16, 3, 1, 8), GOLD, 2, lit_edge=False)
    plane(cv, rect_set(16, 2, 2, 3), GOLD, 3)
    return cv


def signpost() -> Canvas:
    """Two arrow boards on a post, 28 x 36: to the missions and back home."""
    w, h = 28, 36
    cv = Canvas(w, h, pad=PAD)
    plane(cv, rect_set(12, 6, 4, 29), WOOD, 2)
    cv.hline(10, 35, 8, WOOD[1])
    for (y, left) in ((2, False), (14, True)):
        board = rect_set(3, y, 22, 8)
        tip = [(25, y + 1), (25, y + 2), (25, y + 3), (25, y + 4), (25, y + 5), (25, y + 6),
               (26, y + 2), (26, y + 3), (26, y + 4), (26, y + 5), (27, y + 3), (27, y + 4)]
        if left:
            board = rect_set(3, y, 22, 8)
            tip = [(27 - x, yy) for (x, yy) in tip]
        board |= set(tip)
        plane(cv, board, WOOD, 3)
        cv.hline(7, y + 3, 6, WOOD[1]); cv.hline(14, y + 3, 5, WOOD[1]); cv.hline(7, y + 5, 9, WOOD[1])
        cv.set(5 if not left else 22, y + 2, STONE[3])
        cv.hline(12, y + 8, 4, WOOD[0])  # the board's shadow on the post
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
    plane(cv, rect_set(9, 12, 4, 15), WOOD, 2)
    cv.hline(7, 27, 8, WOOD[1])
    plane(cv, rect_set(1, 2, 20, 11), WOOD, 3)
    cv.vline(5, 5, 6, LEAF[2]); cv.set(4, 6, LEAF[3]); cv.set(6, 7, LEAF[3]); cv.set(4, 9, LEAF[4])
    cv.set(5, 4, RED[3]); cv.set(4, 4, RED[4]); cv.set(6, 4, RED[3]); cv.set(5, 3, RED[4])
    cv.hline(9, 5, 9, WOOD[1]); cv.hline(9, 8, 7, WOOD[1])
    cv.hline(9, 13, 4, WOOD[0])
    return cv


def fence_h(length: int) -> Canvas:
    """A split-rail fence segment, 18 tall, posts every 10 pixels."""
    h = 18
    cv = Canvas(length, h, pad=PAD)
    plane(cv, rect_set(0, 5, length, 3), WOOD, 3)
    plane(cv, rect_set(0, 11, length, 3), WOOD, 3)
    for x in range(1, length - 4, 10):
        plane(cv, rect_set(x, 1, 5, 16), WOOD, 3)
        cv.hline(x, 1, 5, WOOD[4])
    for x in (16, length - 24):
        cv.vline(x, 7, 9, LEAF[1])
        for dx, y in ((-1, 8), (1, 10), (-1, 12), (1, 14)):
            cv.hline(x + dx, y, 2, LEAF[2]); cv.set(x + dx, y - 1, LEAF[3])
        cv.set(x + 1, 6, NAP[4])
    return cv


def gate() -> Canvas:
    """The garden gate, 48 x 44: stone pillars, an arched beam and the arena's pennant."""
    w, h = 48, 44
    cv = Canvas(w, h, pad=PAD)
    for x in (2, 39):
        plane(cv, rect_set(x, 10, 7, 33), STONE, 2)
        for y in range(14, 42, 7):
            cv.hline(x, y, 7, STONE[1])
        plane(cv, rect_set(x - 1, 6, 9, 5), STONE, 3)
    for x in range(6, 42):
        y = 3 + int(((x - 23.5) / 18) ** 2 * 5)
        cv.set(x, y, WOOD[4]); cv.set(x, y + 1, WOOD[3]); cv.set(x, y + 2, WOOD[2]); cv.set(x, y + 3, WOOD[1])
    pennant = rect_set(18, 8, 12, 12) | {(x, y) for y in range(20, 24) for x in range(18 + (y - 20) * 2 - 1, 30 - (y - 20) * 2 + 1) if 18 <= x < 30}
    plane(cv, pennant, RED, 2)
    for i in range(6):
        cv.set(21 + i, 11 + i, CREAM[3]); cv.set(26 - i, 11 + i, CREAM[3])
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
    """The bridge deck (a flat decal): planks across the stream between two rails."""
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, h - 2):
        for x in range(5, w - 5):
            pos = y % 4
            col = WOOD[3] if pos == 0 else WOOD[1] if pos == 3 else WOOD[2]
            if x == 5:
                col = WOOD[4] if pos != 3 else WOOD[2]
            cv.set(x, y, col)
    for y in range(4, h - 3, 8):
        cv.set(9, y, WOOD[0]); cv.set(w - 10, y + 1, WOOD[0])
    for x0 in (1, w - 5):
        plane(cv, rect_set(x0, 0, 4, h), WOOD, 2)
        for py in (0, h // 2 - 2, h - 4):
            plane(cv, rect_set(x0 - 1, py, 6, 4), WOOD, 3)
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
