"""Draws NapAttack's top-down garden (GBA/DS-era overworld style).

Run:  python3 scripts/art/garden.py
Outputs PNGs (6x nearest-neighbour) into assets/garden/ plus lib/garden-map.ts with
object positions, hotspots and the walkable grid, all in native pixels.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, shade_blob, smooth_noise  # noqa: E402
from garden_decor import reading_nook, watering_can, frog  # noqa: E402
import garden_meadow as meadow  # noqa: E402
import style  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'garden')
os.makedirs(OUT, exist_ok=True)

W, H = meadow.W, meadow.H  # native map: the clearing (y 0-176) plus the meadow below
TOP = meadow.TOP  # forest band above y = 0
SCALE = 6

# ---- palette -------------------------------------------------------------
from materials import G, P, WTR, SAND, WOOD, STONE, LEAF, NAP, RED, CREAM, INK  # noqa: E402


# ---- terrain masks (native pixels) ----------------------------------------
def thick_path(points, radius, wobble_seed):
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 9, wobble_seed) - 0.5) * 3.2
            pts |= disc(cx, cy, r)
    return pts


PATH = thick_path([(96, 180), (96, 150), (92, 128), (96, 104), (96, 92)], 9.5, 1)
PATH |= thick_path([(96, 96), (80, 86), (60, 80), (44, 76)], 7.5, 2)    # to the nap hut
PATH |= thick_path([(98, 94), (118, 86), (140, 82), (152, 80)], 7.5, 3)  # to Moss's stall
PATH |= thick_path([(98, 88), (104, 78), (106, 67)], 3.5, 4)  # a quiet reading corner
PATH |= disc(96, 98, 13)  # little plaza at the fork
PATH |= meadow.meadow_path(thick_path)  # down across the bridge, through the meadow

POND_C = (42, 132)
POND = {(x, y) for (x, y) in oval(POND_C[0], POND_C[1], 27, 16)
        if ((x + 0.5 - POND_C[0]) / 27) ** 2 + ((y + 0.5 - POND_C[1]) / 16) ** 2
        <= 1 - (smooth_noise(x, y, 7, 5) - 0.5) * 0.35}
BANK = set()
for (x, y) in POND:
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if (x + dx, y + dy) not in POND:
                BANK.add((x + dx, y + dy))

FLOWER_BEDS = [(126, 112, 34, 14), (148, 140, 22, 10)]  # x, y, w, h (dark soil beds)


def draw_terrain(frame: int) -> Canvas:
    cv = Canvas(W, H)
    phase = frame % 4
    # Broad, close-valued grass masses with clean edges (no speckle), so the
    # tufts and props carry the texture, as in the references.
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 18, 11)
            cv.set(x, y, G[3] if n > 0.64 else G[2])
    # Tufts: dark roots and light tips, clustered toward the edges and props.
    for ty in range(0, H, 7):
        for tx in range(0, W, 7):
            x = tx + int(noise2(tx, ty, 4) * 7)
            y = ty + int(noise2(tx, ty, 5) * 7)
            clearing = ((x - 100) / 36) ** 2 + ((y - 92) / 30) ** 2 < 1
            edge = min(x, W - x, y, H - y) < 22
            cluster = smooth_noise(x, y, 25, 63) > 0.57
            density = 0.08 if clearing else 0.5 if edge else 0.34 if cluster else 0.14
            if noise2(tx, ty, 3) < density:
                # a gentle two-pose sway held for two water frames
                grass_phase = (phase // 2 + int(noise2(tx, ty, 64) * 2)) % 2
                sway = 1 if (grass_phase and noise2(tx, ty, 6) < 0.25) else 0
                tall = 3 if noise2(tx, ty, 8) < 0.35 else 2
                style.tuft(cv, x, y + 2, G[1], G[4], tall)
                if sway:
                    cv.set(x + 1, y + 1 - (tall > 2), G[4])
            elif noise2(tx, ty, 7) < 0.1:
                cv.set(x, y, '#E9E4CF')  # a tiny white flower
                cv.set(x, y + 1, G[1])

    # pond bank (sand) then water
    for (x, y) in BANK:
        if 0 <= x < W and 0 <= y < H:
            cv.set(x, y, SAND[1] if noise2(x, y, 21) < 0.8 else SAND[2])
    for (x, y) in BANK:
        if (x, y + 1) not in BANK and (x, y + 1) not in POND:
            cv.set(x, y, SAND[0])
        if (x, y - 1) not in BANK and (x, y - 1) not in POND:
            cv.set(x, y - 1, G[1])  # turf lip over the bank
    for (x, y) in POND:
        depth = ((x + 0.5 - POND_C[0]) / 27) ** 2 + ((y + 0.5 - POND_C[1]) / 16) ** 2
        col = WTR[1] if depth < 0.35 else WTR[2]
        if (x, y - 1) not in POND:
            col = WTR[0]  # dark lip under the far bank
        elif (x, y - 2) not in POND:
            col = WTR[1]
        cv.set(x, y, col)
    # Four-frame, one-pixel ripple loops. Each little arc advances on its own
    # phase, so the pond breathes without the banks or lily pads sliding about.
    # Color and arc length ease around the cycle instead of blinking on/off.
    for i in range(14):
        rx = POND_C[0] - 20 + int(noise2(i, 1, 30) * 40)
        ry = POND_C[1] - 8 + int(noise2(i, 2, 30) * 16)
        ripple_phase = (phase + i) % 4
        dx, dy = ((0, 0), (1, 0), (1, 1), (0, 1))[ripple_phase]
        length = (3, 4, 3, 2)[ripple_phase]
        col = WTR[3] if ripple_phase in (0, 1, 2) else '#85BABF'
        for step in range(length):
            if (rx + dx + step, ry + dy) in POND:
                cv.set(rx + dx + step, ry + dy, col)
        if i % 4 == 0 and ripple_phase in (1, 2) and (rx + dx + 1, ry + dy) in POND:
            cv.set(rx + dx + 1, ry + dy, WTR[4])
    # Lily pads have a cut edge, a central vein and different sizes. The larger
    # low pad leaves a clear perch for the pond's shy resident.
    for (lx, ly) in ((30, 128), (52, 138), (46, 124), (34, 132)):
        for (x, y) in oval(lx, ly, 3.5, 2.5):
            cv.set(x, y, LEAF[3] if y < ly else LEAF[2])
        cv.set(lx + 1, ly - 1, WTR[2])
        cv.set(lx, ly - 2, LEAF[4])
        cv.hline(lx - 2, ly, 3, LEAF[1])
        cv.set(lx - 1, ly - 1, LEAF[4])
    cv.set(52, 136, RED[4]); cv.set(53, 136, RED[3])  # tiny water flower
    # Reeds make the bank belong to the water; retain an open viewing edge.
    for rx, ry in ((19, 128), (24, 120), (59, 125), (57, 146)):
        cv.vline(rx, ry - 4, 5, LEAF[1])
        cv.vline(rx + 2, ry - 3, 4, LEAF[2])
        cv.set(rx - 1, ry - 4, LEAF[3])
        cv.set(rx + 1, ry - 1, LEAF[3])
    # Cattails and a few visible flat bank stones distinguish the wet margin
    # from the trimmed flower garden. These are low ground details, not walls.
    for rx, ry in ((19, 125), (60, 123), (58, 145)):
        cv.vline(rx, ry - 5, 6, LEAF[1])
        cv.vline(rx, ry - 7, 3, WOOD[1])
        cv.set(rx - 1, ry - 7, WOOD[3])
    for sx, sy in ((15, 136), (28, 149), (57, 115)):
        cv.hline(sx, sy, 5, STONE[1])
        cv.hline(sx + 1, sy - 1, 3, STONE[3])
        cv.set(sx + 1, sy - 2, STONE[4])

    meadow.draw_stream(cv, phase)

    # Paths sit lower than the turf. Packed dirt with clean lighter patches and
    # small dark specks; where the turf above drops onto the path it leaves a
    # dark lip and a shadow line, and the turf edge facing up catches the light.
    dirt = PATH - meadow.STREAM
    for (x, y) in dirt:
        if not (0 <= x < W and 0 <= y < H):
            continue
        n = smooth_noise(x, y, 7, 40)
        cv.set(x, y, P[3] if n > 0.7 else P[2])
    for i in range(160):
        x = int(noise2(i, 0, 50) * W)
        y = int(noise2(i, 1, 50) * H)
        if (x, y) in dirt and (x + 1, y) in dirt and (x, y + 1) in dirt:
            cv.set(x, y, P[1])
            if i % 3 == 0:
                cv.set(x + 1, y, P[1])
            if i % 5 == 0:
                cv.set(x, y - 1, P[4])
    for (x, y) in dirt:
        if not (0 <= x < W and 0 <= y < H):
            continue
        above = (x, y - 1) not in PATH
        if above:
            # scalloped turf: every few pixels the lip hangs one pixel lower
            hang = (x // 3 + int(noise2(x // 3, y, 45) * 2)) % 3 == 0
            if hang and (x, y + 1) in dirt:
                cv.set(x, y, G[1])
                cv.set(x, y + 1, P[0])
                if (x, y + 2) in dirt:
                    cv.set(x, y + 2, P[1])
            else:
                cv.set(x, y, P[0])
                if (x, y + 1) in dirt:
                    cv.set(x, y + 1, P[1])
        elif (x - 1, y) not in PATH or (x + 1, y) not in PATH:
            side = -1 if (x - 1, y) not in PATH else 1
            if (y // 3 + int(noise2(x, y // 3, 46) * 2)) % 3 == 0:
                cv.set(x, y, G[2])  # a turf bump reaching onto the path
                if (x - side, y) in dirt:
                    cv.set(x - side, y, P[1])
            else:
                cv.set(x, y, P[1])
        elif (x, y + 1) not in PATH:
            cv.set(x, y, P[1])
    for (x, y) in dirt:
        if (x, y - 1) not in PATH and 0 <= y - 1 < H:
            cv.set(x, y - 1, G[1])  # the turf's dark lip
        if (x, y + 1) not in PATH and (x, y + 1) not in meadow.STREAM and y + 1 < H:
            cv.set(x, y + 1, G[3])  # the lit edge of the turf below
            if (x, y + 2) not in PATH and y + 2 < H:
                cv.set(x, y + 2, G[3] if (x + y) % 3 else G[2])

    # footprints of a small creature along the main path
    for i, y in enumerate(range(116, 168, 9)):
        x = 92 + (4 if i % 2 else 0)
        cv.set(x, y, P[1]); cv.set(x + 1, y, P[1]); cv.set(x, y + 1, P[1])

    meadow.draw_beds(cv)
    meadow.draw_lower_details(cv, PATH)

    # Raised beds have a lit rim, a shaded front face and individual plants.
    for bi, (bx, by, bw, bh) in enumerate(FLOWER_BEDS):
        cv.rect(bx, by, bw, bh, WOOD[1])
        cv.rect(bx + 1, by + 1, bw - 2, bh - 2, '#5A3A26')
        cv.hline(bx + 1, by, bw - 2, WOOD[3])
        cv.hline(bx, by + bh - 1, bw, WOOD[0])
        cv.hline(bx + 1, by + bh, bw - 1, G[1])
        for sx in range(bx + 3, bx + bw - 2, 7):
            cv.set(sx, by + bh - 2, WOOD[3])  # cut ends / worn planter lip
            cv.set(sx + 1, by + 2, '#75492D')
        for fy in range(by + 3, by + bh - 2, 6):
            for fx in range(bx + 3, bx + bw - 3, 6):
                kind = ((fx - bx - 3) // 6 + (fy - by - 3) // 6 + bi) % 3
                petals = [RED[3], CREAM[3], NAP[3]][kind]
                stem = LEAF[2]
                cv.vline(fx, fy + 1, 3, stem)
                cv.set(fx + 1, fy + 2, LEAF[3]); cv.set(fx - 1, fy + 3, LEAF[1])
                if kind == 0:  # a cupped coral tulip, with a darker petal fold
                    cv.hline(fx - 1, fy, 3, petals)
                    cv.set(fx - 1, fy - 1, RED[4]); cv.set(fx + 1, fy - 1, RED[3])
                    cv.set(fx, fy + 1, RED[2]); cv.set(fx - 1, fy + 2, LEAF[3])
                elif kind == 1:  # chamomile has a warm centre and four cream rays
                    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                        cv.set(fx + dx, fy + dy, petals)
                    cv.set(fx, fy, '#E8A33D')
                else:  # a small lavender spike, shorter petals at the crown
                    cv.vline(fx, fy - 2, 4, NAP[2])
                    cv.set(fx, fy - 2, NAP[4])
                    cv.hline(fx - 1, fy, 3, NAP[3]); cv.set(fx - 1, fy - 1, NAP[4])
    # A pair of hand-painted crop markers gives the beds a cared-for history.
    for mx, my, petal in ((157, 112, RED[3]), (166, 140, NAP[3])):
        cv.vline(mx, my - 3, 5, WOOD[1])
        cv.rect(mx - 2, my - 5, 5, 3, CREAM[2])
        cv.hline(mx - 2, my - 5, 5, CREAM[3])
        cv.set(mx, my - 4, petal)
    # wildflower clusters in the grass
    for i in range(26):
        x = int(noise2(i, 3, 60) * (W - 8)) + 4
        y = int(noise2(i, 4, 60) * (H - 30)) + 24
        if (x, y) in PATH or (x, y) in POND or (x, y) in BANK:
            continue
        col = [CREAM[3], '#F2D16B', NAP[4], RED[4]][i % 4]
        cv.set(x, y, col); cv.set(x + 2, y + 1, col); cv.set(x + 1, y + 2, col)
        cv.set(x + 1, y + 1, '#E8A33D' if col != '#F2D16B' else RED[2])
    # The perimeter is richer than the clearing: ferns under the trees, a few
    # fallen leaves and tiny mushroom families. All stay low to the ground.
    for fx, fy in ((5, 36), (76, 30), (181, 70), (179, 151), (11, 154), (61, 155)):
        cv.vline(fx, fy - 4, 6, LEAF[1])
        for dx, dy in ((-3, -2), (-2, -4), (-1, -5), (1, -4), (2, -2), (3, 0)):
            cv.hline(fx + dx, fy + dy, 2, LEAF[2])
            cv.set(fx + dx, fy + dy - 1, LEAF[3])
        cv.set(fx, fy - 5, LEAF[4])
    for mx, my in ((20, 106), (177, 91), (122, 153)):
        for dx, dy, size in ((0, 0, 3), (4, 2, 2)):
            cv.vline(mx + dx, my + dy - 2, 3, CREAM[2])
            cv.hline(mx + dx - 1, my + dy - 3, size, RED[2])
            cv.hline(mx + dx - 1, my + dy - 4, size, RED[3])
            cv.set(mx + dx - 1, my + dy - 4, CREAM[3])
    for lx, ly in ((14, 145), (68, 34), (181, 111), (136, 154), (9, 60)):
        cv.hline(lx, ly, 3, WOOD[2]); cv.set(lx + 1, ly - 1, WOOD[3])
        cv.set(lx + 3, ly + 1, WOOD[1])
    return cv


# ---- objects (drawn on their own canvases, anchored at the base) ----------
def leaf_bundle(cv: Canvas, cx: float, cy: float, r: float, ramp, solid: set):
    """One ball of leaves: dark crescent bottom-right, light top-left, small highlight,
    plus a scatter of leaf-shaped notches so it reads as foliage, not a pillow."""
    pts = {(x, y) for (x, y) in disc(cx, cy, r) if 0 <= x < cv.w and 0 <= y < cv.h}
    for (x, y) in pts:
        dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
        lit = -dx * 0.55 - dy * 0.85
        if lit > 0.55:
            # Leaf-sized highlights, not a diagonal checker across every lobe.
            col = ramp[4] if smooth_noise(x, y, 3, int(cx + cy * 7)) > 0.56 else ramp[3]
        elif lit > 0.05:
            col = ramp[3]
        elif lit > -0.45:
            col = ramp[2]
        else:
            col = ramp[1]
        cv.set(x, y, col)
    # leaf notches along the lower rim (little "v" bites of the darker tone)
    for a in range(20, 170, 28):
        x = int(cx + math.cos(math.radians(a)) * (r - 1))
        y = int(cy + math.sin(math.radians(a)) * (r - 1))
        cv.set(x, y, ramp[0]); cv.set(x - 1, y - 1, ramp[1])
    solid |= pts


PINE = ['#1F2E2A', '#2F4A3C', '#46664B', '#5E8253', '#86A766']
AUTUMN = ['#4A2A22', '#7A4030', '#A8623E', '#CB8650', '#E8B575']


def tree(big: bool = True, autumn: bool = False) -> Canvas:
    """Round broadleaf: a clean shaded canopy of leaf clumps over a flared trunk."""
    w, h = (36, 46) if big else (26, 34)
    cv = Canvas(w, h)
    ramp = AUTUMN if autumn else LEAF
    cx = w / 2
    tw = 6 if big else 4
    tx = int(cx - tw / 2)
    ty = h - (19 if big else 14)
    style.trunk(cv, tx, ty - 4, h, tw, WOOD)
    crx, cry = (15.0, 13.5) if big else (10.8, 9.6)
    ccy = cry + 2.5
    canopy = style.leafy(cv, cx, ccy, crx, cry, ramp, r=2.7 if big else 2.2, seed=9 if autumn else 2 + big)
    style.trunk(cv, tx, ty, h, tw, WOOD, canopy)
    if not autumn and big:  # a few ripe apples on the lit side
        for fx, fy in ((cx - 9, 9), (cx + 4, 6), (cx - 4, 15), (cx + 8, 14)):
            fx, fy = int(fx), int(fy)
            cv.rect(fx, fy, 2, 2, RED[2]); cv.set(fx, fy, RED[4]); cv.set(fx + 1, fy + 1, RED[1])
    if autumn:
        # the copper tree keeps its weathered birdhouse
        cv.vline(25, 20, 9, WOOD[0])
        cv.rect(21, 24, 9, 9, WOOD[2])
        cv.rect(21, 24, 7, 8, WOOD[3])
        cv.hline(21, 24, 7, WOOD[4])
        for x, y in ((20, 24), (21, 23), (22, 22), (23, 21), (24, 20), (25, 21), (26, 22), (27, 23), (28, 24)):
            cv.hline(x, y, 2, NAP[1])
            cv.set(x, y - 1, NAP[3])
        cv.rect(24, 26, 3, 3, WOOD[0]); cv.set(24, 26, INK)
        cv.hline(23, 30, 6, WOOD[1]); cv.set(23, 29, WOOD[4])
    cv.outline(INK)
    return cv


def pine() -> Canvas:
    """Tiered conifer: cone-shaded tiers, light clumps on the lit flank, dark hems."""
    w, h = 22, 40
    cv = Canvas(w, h)
    cx = w / 2 - 0.5
    style.trunk(cv, int(cx) - 1, h - 10, h, 3, WOOD)
    tiers = ((1, 10, 4.0), (7, 11, 6.5), (14, 12, 8.6), (22, 11, 10.4))
    for t, (ty, th, half) in enumerate(tiers):
        tier = {}
        for y in range(ty, ty + th):
            frac = (y - ty + 1) / th
            span = half * (0.3 + 0.7 * frac)
            for x in range(int(cx - span), int(cx + span) + 2):
                if not (0 <= x < w):
                    continue
                if y == ty + th - 1 and (x + t) % 3 == 0:
                    continue  # sawtooth hem
                side = (x + 0.5 - cx) / max(1.0, span)
                lv = -0.8 * side - 0.5 * (frac - 0.4)
                tier[(x, y)] = 3 if lv > 0.45 else 2 if lv > -0.05 else 1 if lv > -0.6 else 0
        for (x, y), tone in tier.items():
            cv.set(x, y, PINE[tone])
        # hem: the tier's lowest pixels sit in their own shade
        for (x, y), tone in tier.items():
            if (x, y + 1) not in tier:
                cv.set(x, y, PINE[max(0, tone - 1)])
        # needle clumps on the lit flank: small light caps with a dark lip
        for k in range(3 + t):
            yy = ty + 2 + int(noise2(k, t, 61) * max(1, th - 4))
            span = half * (0.3 + 0.7 * (yy - ty + 1) / th)
            xx = int(cx - span * (0.25 + 0.55 * noise2(k, t, 62)))
            if (xx, yy) in tier and (xx + 2, yy) in tier and tier[(xx, yy)] >= 2:
                cv.hline(xx, yy, 2, PINE[4])
                cv.set(xx + 2, yy, PINE[3])
                cv.hline(xx, yy + 1, 3, PINE[1])
    cv.set(int(cx), 0, PINE[3])
    cv.outline(INK)
    return cv


def bush() -> Canvas:
    """A round shrub of leaf clumps with its stems peeking out below."""
    w, h = 22, 18
    cv = Canvas(w, h)
    for x in (6, 10, 14):
        cv.rect(x, h - 3, 3, 2, WOOD[1]); cv.set(x, h - 3, WOOD[2])
    style.leafy(cv, w / 2, 8.5, 8.8, 6.6, LEAF, r=2.2, seed=5)
    for x, y in ((7, 5), (13, 4)):  # small cream blossoms on the lit side
        cv.set(x, y, CREAM[3]); cv.set(x + 1, y + 1, '#E2C76B')
    cv.outline(INK)
    return cv


def nap_hut() -> Canvas:
    """The nap hut: a gabled lavender roof over plaster and timber, round door."""
    w, h = 50, 46
    cv = Canvas(w, h)
    apex_x, apex_y, eave = 24.5, 12, 22

    def gable(x, y):  # the front triangle under the roof's apex
        if y < apex_y or y > eave + 1:
            return False
        half = (y - apex_y) * (15.5 / (eave + 1 - apex_y))
        return abs(x + 0.5 - apex_x) <= half

    # walls: plaster with timber posts and a beam under the eaves
    cv.rect(4, 22, 42, 18, CREAM[2])
    for y in range(22, 40):
        for x in range(4, 46):
            if x >= 36:
                cv.set(x, y, CREAM[1])  # the wall turning away from the light
    for x in (4, 5, 44, 45):
        cv.vline(x, 22, 18, WOOD[2] if x in (4, 44) else WOOD[1])
    cv.vline(4, 22, 18, WOOD[3])
    cv.hline(4, 24, 42, WOOD[1]); cv.hline(4, 25, 42, CREAM[0])  # eave shadow
    cv.hline(4, 38, 42, WOOD[1])
    # stone foundation blocks
    for i, x in enumerate(range(2, 48, 6)):
        cv.rect(x, 39, 5, 5, STONE[2 if i % 2 else 3])
        cv.hline(x, 39, 5, STONE[4]); cv.vline(x + 4, 40, 4, STONE[1]); cv.hline(x, 43, 5, STONE[1])
    # gable triangle in timber, with a round vent and the moon sign
    for y in range(apex_y, eave + 2):
        for x in range(w):
            if gable(x, y):
                cv.set(x, y, WOOD[3] if (x // 3) % 2 == 0 else WOOD[2])
    for (x, y) in disc(24.5, 18, 2.6):
        cv.set(x, y, '#2E2A3D')
    cv.set(23, 17, '#7A6FA6'); cv.set(24, 17, '#B9B0DD')
    # roof planes with shingle rows: lit left slope, shaded right slope
    for y in range(0, eave + 1):
        for x in range(w):
            outer_l = 6 - y * 6 / eave
            outer_r = w - 1 - (6 - y * 6 / eave)
            if x < outer_l or x > outer_r or gable(x, y):
                continue
            left = x < apex_x
            body, rim, lit = (NAP[3], NAP[2], NAP[4]) if left else (NAP[2], NAP[1], NAP[3])
            row = y % 3
            joint = (x + (y // 3) * 3) % 6 == 0
            col = body
            if row == 2:
                col = rim
            elif joint:
                col = rim
            elif row == 0 and (x + (y // 3) * 3) % 6 == 1:
                col = lit
            cv.set(x, y, col)
    # timber: ridge beam, fascia along the gable and the eaves
    for y in range(0, apex_y + 1):
        cv.hline(23, y, 3, WOOD[2]); cv.set(23, y, WOOD[4]); cv.set(25, y, WOOD[1])
    for y in range(apex_y, eave + 2):
        half = (y - apex_y) * (15.5 / (eave + 1 - apex_y))
        lx, rx = int(apex_x - half) - 1, int(apex_x + half)
        cv.set(lx, y, WOOD[3]); cv.set(lx - 1, y, WOOD[2])
        cv.set(rx + 1, y, WOOD[2]); cv.set(rx + 2, y, WOOD[1])
    for x in range(0, w):
        if cv.get(x, eave)[3]:
            cv.set(x, eave, WOOD[1]); cv.set(x, eave - 1, WOOD[3] if x < apex_x else WOOD[2])
    # chimney on the shaded slope
    cv.rect(35, 0, 6, 9, STONE[2]); cv.vline(35, 0, 9, STONE[3]); cv.vline(40, 0, 9, STONE[1])
    cv.hline(34, 0, 8, STONE[3]); cv.rect(36, 1, 4, 1, '#2A2628')
    cv.hline(35, 4, 6, STONE[1]); cv.set(37, 6, STONE[1])
    # door: rounded top, stone arch frame, planks lit from the left
    door = {(x, y) for (x, y) in disc(24.5, 31.5, 5.2) if y <= 38} | {(x, y) for x in range(20, 30) for y in range(31, 39)}
    frame = set()
    for (x, y) in door:
        for dx, dy in ((1, 0), (-1, 0), (0, -1), (1, -1), (-1, -1)):
            if (x + dx, y + dy) not in door:
                frame.add((x + dx, y + dy))
    for (x, y) in frame:
        if y <= 38:
            cv.set(x, y, STONE[3] if x < 25 else STONE[2])
    for (x, y) in door:
        col = WOOD[2] if (x - 20) % 3 else WOOD[1]
        if x == 20 or x == 21:
            col = WOOD[3]
        cv.set(x, y, col)
    cv.set(27, 34, CREAM[3]); cv.set(27, 35, '#E2C76B')  # brass latch
    # window with a flower box
    cv.rect(34, 27, 8, 7, WOOD[1]); cv.rect(35, 28, 6, 5, '#2E3A4E')
    cv.set(35, 28, '#9DB7D2'); cv.set(36, 28, '#C9DCEA'); cv.set(35, 29, '#9DB7D2')
    cv.vline(38, 28, 5, WOOD[1])
    cv.rect(33, 34, 10, 2, WOOD[2]); cv.hline(33, 34, 10, WOOD[3])
    for i, x in enumerate(range(34, 42, 2)):
        cv.set(x, 33, [RED[3], '#E2C76B', NAP[4], RED[3]][i]); cv.set(x + 1, 33, LEAF[3])
    # ivy on the lit corner
    for ix, iy in ((6, 27), (7, 30), (6, 33), (7, 36)):
        cv.vline(ix, iy, 3, LEAF[1]); cv.set(ix + 1, iy, LEAF[3]); cv.set(ix + 1, iy + 1, LEAF[4])
    # doormat
    cv.rect(21, 44, 8, 2, NAP[1]); cv.hline(22, 44, 6, NAP[3])
    cv.outline(INK)
    return cv


def bed() -> Canvas:
    """Stitched pillow and a folded lavender blanket, rather than a food dish."""
    cv = Canvas(22, 12)
    rim = oval(11, 6.5, 10.5, 5.5)
    shade_blob(cv, rim, NAP[1], NAP[2], NAP[3], NAP[4])
    for (x, y) in oval(11, 7, 7.5, 3.5):
        cv.set(x, y, CREAM[1] if y > 8 else CREAM[2])
    for (x, y) in oval(8, 6, 3, 1.6):
        cv.set(x, y, CREAM[3])
    cv.rect(11, 5, 7, 4, NAP[3])
    cv.hline(11, 5, 7, NAP[4]); cv.hline(11, 8, 7, NAP[2])
    cv.rect(13, 6, 3, 2, RED[4])  # one repaired fabric patch
    for x, y in ((3, 5), (5, 9), (8, 10), (17, 9)):
        cv.set(x, y, NAP[4])
    cv.outline(INK)
    return cv


def mailbox() -> Canvas:
    cv = Canvas(12, 22)
    cv.rect(5, 10, 2, 11, WOOD[2]); cv.vline(5, 10, 11, WOOD[1])
    body = {(x, y) for x in range(1, 11) for y in range(3, 11)} | {(x, y) for x in range(2, 10) for y in range(1, 3)}
    shade_blob(cv, body, RED[1], RED[2], RED[3], RED[4])
    cv.rect(3, 6, 6, 1, RED[0])
    cv.hline(3, 3, 5, RED[4]); cv.set(3, 4, RED[3])
    cv.rect(3, 8, 5, 2, CREAM[2]); cv.hline(4, 8, 3, CREAM[3])
    cv.set(5, 9, RED[1])  # a postcard peeking through the open lip
    cv.set(6, 15, WOOD[3]); cv.set(6, 18, WOOD[0])
    cv.rect(10, 2, 1, 5, '#F2D16B'); cv.rect(10, 2, 2, 2, '#F2D16B')  # flag up
    cv.outline(INK)
    return cv


def signpost() -> Canvas:
    cv = Canvas(20, 24)
    cv.rect(9, 8, 3, 15, WOOD[2]); cv.vline(9, 8, 15, WOOD[1]); cv.vline(11, 8, 15, WOOD[3])
    # two arrow boards
    for (y, flip) in ((3, False), (10, True)):
        board = {(x, y + dy) for x in range(2, 18) for dy in range(4)}
        tip = [(18, y + 1), (18, y + 2), (19, y + 1)] if not flip else [(1, y + 1), (1, y + 2), (0, y + 2)]
        board |= set(tip)
        for (x, yy) in board:
            cv.set(x, yy, WOOD[4] if yy == y else WOOD[3])
        cv.hline(4, y + 2, 9, WOOD[1])
    cv.outline(INK)
    return cv


def stall() -> Canvas:
    """Moss the merchant's hat stall: striped awning, counter, hats on display."""
    w, h = 46, 40
    cv = Canvas(w, h)
    cv.rect(3, 12, 2, 26, WOOD[1]); cv.rect(41, 12, 2, 26, WOOD[1])
    cv.rect(5, 14, 36, 10, WOOD[0])  # shaded recess beneath the canopy
    # counter
    cv.rect(2, 24, 42, 13, WOOD[3])
    for x in range(2, 44, 6):
        cv.vline(x, 26, 11, WOOD[2])
    cv.hline(2, 24, 42, WOOD[4]); cv.hline(2, 25, 42, WOOD[2]); cv.hline(2, 36, 42, WOOD[1])
    for x, y in ((6, 31), (30, 29), (37, 34)):
        cv.hline(x, y, 3, WOOD[1]); cv.set(x + 1, y - 1, WOOD[4])
    for x in (4, 41):
        cv.set(x, 26, CREAM[1]); cv.set(x, 35, WOOD[0])
    # hats on counter
    cv.rect(8, 20, 7, 4, '#4C6E9E'); cv.rect(7, 23, 10, 1, '#36507A')          # cap
    cv.hline(9, 20, 4, '#7C9BC1')
    cv.rect(20, 17, 6, 6, '#3A3333'); cv.rect(18, 22, 10, 2, '#2A2421')       # top hat
    cv.hline(20, 21, 6, RED[2])
    for i, x in enumerate(range(31, 39)):                                     # crown
        cv.rect(x, 20, 1, 4 if i % 3 else 3, '#E8C24A')
    cv.hline(31, 23, 8, '#C99A2E')
    # Hanging seed packets, a shopkeeper's ledger and two rolled fabric bolts.
    for x, y, flower in ((7, 16, RED[3]), (35, 16, NAP[3])):
        cv.vline(x + 1, 14, 3, WOOD[3])
        cv.rect(x, y, 4, 4, CREAM[2]); cv.hline(x, y, 4, CREAM[3])
        cv.set(x + 1, y + 1, flower); cv.set(x + 2, y + 2, LEAF[2])
    cv.rect(28, 24, 7, 2, NAP[0]); cv.hline(29, 24, 5, CREAM[2])
    cv.hline(6, 37, 8, NAP[1]); cv.hline(7, 36, 6, NAP[3])
    cv.hline(31, 37, 9, '#39738A'); cv.hline(32, 36, 7, '#A1CFD0')
    # awning: green/cream stripes with scalloped edge
    for y in range(4, 14):
        for x in range(0, w):
            col = '#5FA35A' if (x // 5) % 2 == 0 else CREAM[3]
            if y < 6:
                col = '#3E7D44' if (x // 5) % 2 == 0 else CREAM[2]
            elif x % 5 == 4:
                col = '#4C8A50' if (x // 5) % 2 == 0 else CREAM[2]
            elif y in (7, 8) and x % 5 == 0:
                col = '#80BC6C' if (x // 5) % 2 == 0 else '#FFF9E8'
            cv.set(x, y, col)
    for x in range(0, w):
        if x % 5 in (1, 2, 3):
            cv.set(x, 14, '#5FA35A' if (x // 5) % 2 == 0 else CREAM[3])
            cv.set(x, 15, '#3E7D44' if (x // 5) % 2 == 0 else CREAM[1])
    cv.hline(0, 4, w, '#2E6538')
    # little sign
    cv.rect(16, 0, 14, 5, WOOD[3])
    cv.hline(17, 0, 12, WOOD[4])
    cv.rect(21, 1, 4, 2, NAP[1]); cv.hline(19, 3, 8, NAP[0])  # hat-shaped shop sign
    cv.outline(INK)
    return cv


def bowl() -> Canvas:
    cv = Canvas(12, 7)
    for (x, y) in oval(6, 3.5, 5.5, 3):
        cv.set(x, y, RED[2] if y > 3 else RED[3])
    for (x, y) in oval(6, 2.6, 4, 1.4):
        cv.set(x, y, '#E8C27A' if (x + y) % 2 else '#C9973F')  # seeds
    cv.outline(INK)
    return cv


def leaf_lantern() -> Canvas:
    """A warm seed-glass lantern hanging from a bent garden branch."""
    cv = Canvas(12, 26)
    cv.rect(2, 5, 3, 19, WOOD[2]); cv.vline(2, 6, 18, WOOD[1])
    cv.set(3, 4, WOOD[3]); cv.hline(4, 3, 5, WOOD[3])
    cv.set(8, 4, WOOD[2]); cv.vline(9, 5, 3, WOOD[1])
    cv.rect(6, 9, 5, 8, WOOD[0])
    cv.rect(7, 10, 3, 6, '#D6A456')
    cv.vline(7, 10, 5, '#F4D58C'); cv.set(8, 11, CREAM[3])
    cv.hline(6, 17, 5, WOOD[2])
    cv.hline(5, 8, 7, LEAF[1]); cv.hline(6, 7, 5, LEAF[2])
    cv.hline(7, 6, 3, LEAF[3]); cv.set(7, 7, LEAF[4])
    cv.set(1, 24, WOOD[1]); cv.hline(2, 24, 5, WOOD[1])
    cv.set(3, 12, WOOD[4]); cv.set(3, 13, WOOD[1])
    cv.set(4, 19, WOOD[0]); cv.set(3, 20, WOOD[3])
    cv.hline(7, 16, 3, '#99713E')
    cv.set(9, 12, '#B7833D'); cv.set(8, 14, '#F4D58C')
    # A living branch sprouts below the hand-made glass housing.
    cv.set(1, 20, LEAF[2]); cv.set(0, 19, LEAF[3])
    cv.set(1, 18, LEAF[4]); cv.set(4, 22, LEAF[2]); cv.set(5, 21, LEAF[3])
    cv.outline(INK)
    return cv


def gate() -> Canvas:
    """Arched wooden gate at the bottom: the way out to the Arena."""
    w, h = 36, 30
    cv = Canvas(w, h)
    for x in (2, 31):
        cv.rect(x, 6, 4, 23, STONE[2]); cv.vline(x, 6, 23, STONE[1]); cv.vline(x + 3, 6, 23, STONE[3])
        cv.rect(x - 1, 4, 6, 3, STONE[3]); cv.hline(x - 1, 4, 6, STONE[4])
    for x in range(4, 33):  # arch beam
        y = 2 + int(((x - 18) / 15) ** 2 * 4)
        cv.rect(x, y, 1, 3, WOOD[3]); cv.set(x, y, WOOD[4])
    # little pennant with crossed swords
    cv.rect(16, 6, 5, 6, RED[2]); cv.set(18, 12, RED[2])
    cv.set(17, 8, CREAM[3]); cv.set(19, 8, CREAM[3]); cv.set(18, 9, CREAM[3]); cv.set(17, 10, CREAM[3]); cv.set(19, 10, CREAM[3])
    cv.outline(INK)
    return cv


def fence_h(length: int) -> Canvas:
    cv = Canvas(length, 13)
    cv.hline(0, 4, length, WOOD[3]); cv.hline(0, 5, length, WOOD[2])
    cv.hline(0, 8, length, WOOD[3]); cv.hline(0, 9, length, WOOD[2])
    for x in range(1, length - 2, 6):
        cv.rect(x, 1, 4, 11, WOOD[3]); cv.vline(x, 1, 11, WOOD[4]); cv.vline(x + 3, 1, 11, WOOD[2])
        cv.hline(x, 1, 4, WOOD[4]); cv.set(x, 1, WOOD[2])
    # Two climbing stems soften the fence without obscuring the entrance.
    for x in (12, length - 19):
        cv.vline(x, 5, 7, LEAF[1])
        for dx, y in ((-1, 6), (1, 8), (-1, 10)):
            cv.hline(x + dx, y, 2, LEAF[2]); cv.set(x + dx, y - 1, LEAF[3])
        cv.set(x + 1, 5, NAP[4])
    cv.outline(INK)
    return cv


def rock(n: int) -> Canvas:
    """A chunky field stone: lit top, shaded flank, a crack, moss on the mossy one."""
    cv = Canvas(14, 11)
    pts = {(x, y) for (x, y) in (oval(7, 6, 6, 4.2) | oval(5, 6.5, 4, 3.5)) if 0 <= x < 14 and 0 <= y < 11}
    style.facet_stone(cv, pts, STONE, moss=LEAF if n else None, seed=n + 2, outline=None)
    cv.outline(INK)
    return cv


# ---- compose -------------------------------------------------------------
# Objects are listed with their base (feet) point; the app depth-sorts them by y.
OBJECTS = [
    # id, sprite, x(left), y(top), interactive action or None
    ('pine-0', 'pine', -8, -22, None),
    ('pine-1', 'pine', 7, -18, None),
    ('pine-2', 'pine', 22, -22, None),
    ('pine-3', 'pine', 37, -18, None),
    ('pine-4', 'pine', 52, -22, None),
    ('pine-5', 'pine', 67, -18, None),
    ('pine-6', 'pine', 82, -22, None),
    ('pine-7', 'pine', 97, -18, None),
    ('pine-8', 'pine', 112, -22, None),
    ('pine-9', 'pine', 127, -18, None),
    ('pine-10', 'pine', 142, -22, None),
    ('pine-11', 'pine', 157, -18, None),
    ('pine-12', 'pine', 172, -22, None),
    ('pine-13', 'pine', 187, -18, None),
    ('tree-0', 'tree', -12, -18, None),
    ('tree-1', 'tree_small', 20, -22, None),
    ('tree-2', 'tree', 52, -24, None),
    ('tree-3', 'tree_small', 118, -24, None),
    ('tree-4', 'tree_autumn', 142, -20, None),
    ('tree-5', 'tree', 170, -14, None),
    ('tree-6', 'tree_small', 176, 20, None),
    ('hut', 'hut', 14, 30, 'nap'),
    ('bed', 'bed', 62, 66, 'nap'),
    ('mailbox', 'mailbox', 6, 74, 'mail'),
    ('stall', 'stall', 132, 40, 'shop'),
    ('reading-nook', 'reading_nook', 92, 40, 'read'),
    ('lantern', 'lantern', 118, 62, 'lantern'),
    ('watering-can', 'watering_can', 172, 100, 'water'),
    ('signpost', 'signpost', 112, 94, 'missions'),
    ('bowl', 'bowl', 74, 92, 'feed'),
    ('bush-1', 'bush', 172, 120, None),
    ('bush-2', 'bush', 4, 96, None),
    ('rock-1', 'rock0', 126, 150, None),
    ('rock-2', 'rock1', 70, 140, None),
    # the forest behind the HUD: a back row of pines
    *[(f'pine-back-{i}', 'pine', -14 + i * 15, -44 + (i % 2) * 6, None) for i in range(15)],
    # the lower garden: stream, bridge, meadow, orchard edge and the gate out
    ('bridge', 'bridge', meadow.BRIDGE[0], meadow.BRIDGE[1], None),
    ('meadow-sign', 'meadow_sign', 104, 230, 'meadow'),
    ('tree-7', 'tree', -14, 168, None),
    ('tree-8', 'tree_small', 172, 160, None),
    ('bush-3', 'bush', 2, 226, None),
    ('bush-4', 'bush', 174, 222, None),
    ('tree-9', 'tree_autumn', 162, 300, None),
    ('rock-3', 'rock0', 84, 236, None),
    ('rock-4', 'rock1', 4, 322, None),
    ('bush-5', 'bush', 46, 322, None),
    ('bush-6', 'bush', 128, 322, None),
    ('fence-l', 'fence_l', 0, meadow.FENCE_Y, None),
    ('fence-r', 'fence_r', 114, meadow.FENCE_Y, None),
    ('gate', 'gate', meadow.GATE_X, meadow.GATE_Y, 'arena'),
    ('tree-10', 'tree', -10, 344, None),
    ('tree-11', 'tree', 166, 346, None),
    ('pine-low-0', 'pine', 30, 352, None),
    ('pine-low-1', 'pine', 136, 354, None),
]


def bake_shadows(terrain: Canvas, sprites: dict):
    """Hard cast shadows (light from the upper left), plus forest shade dithered
    in from the treeline. Shadows multiply the ground so they work on any surface."""
    for (_id, key, x, y, _a) in OBJECTS:
        s = sprites[key]
        if key in ('bridge',):
            continue
        foot = y + s.h
        if key in ('tree', 'tree_small', 'tree_autumn'):
            style.cast_shadow(terrain, x + s.w / 2 + 3, foot - 1, s.w * 0.5, 4.5)
        elif key == 'pine':
            style.cast_shadow(terrain, x + s.w / 2 + 2, foot, s.w * 0.45, 3.2)
        elif key == 'bush':
            style.cast_shadow(terrain, x + s.w / 2 + 2, foot - 1, s.w * 0.55, 3.2)
        elif key.startswith('fence'):
            for xx in range(x + 1, x + s.w):
                style.darken(terrain, xx, foot)
                style.darken(terrain, xx, foot + 1)
        elif key in ('hut', 'stall'):
            for yy in range(foot - 3, foot + 3):
                for xx in range(x + 3, x + s.w + 2):
                    style.darken(terrain, xx, yy)
        else:
            style.cast_shadow(terrain, x + s.w / 2 + 2.5, foot, max(3.5, s.w * 0.5), max(2.2, s.h * 0.12))
    # shade under the canopy along the top of the clearing
    for row, strength in ((0, 1.0), (1, 0.75), (2, 0.75), (3, 0.5), (4, 0.5), (5, 0.25), (6, 0.25)):
        style.dither_dark(terrain, 0, row, W, 1, strength, style.FOREST_DARK)


def main():
    sprites = {
        'tree': tree(True), 'tree_small': tree(False), 'tree_autumn': tree(True, True), 'pine': pine(),
        'hut': nap_hut(), 'bed': bed(), 'mailbox': mailbox(), 'stall': stall(),
        'signpost': signpost(), 'bowl': bowl(), 'bush': bush(), 'rock0': rock(0), 'rock1': rock(1),
        'fence_l': fence_h(80), 'fence_r': fence_h(78), 'gate': gate(),
        'reading_nook': reading_nook(), 'watering_can': watering_can(), 'lantern': leaf_lantern(),
        'frog': frog(),
        'bridge': meadow.bridge(), 'meadow_sign': meadow.meadow_sign(),
    }
    growth = meadow.growth_sprites()
    growth_dir = os.path.join(OUT, 'growth')
    os.makedirs(growth_dir, exist_ok=True)
    for key, g in growth.items():
        g.save(os.path.join(growth_dir, f'{key}.png'), SCALE)
    meadow.draw_top_band().save(os.path.join(OUT, 'ground-top.png'), SCALE)
    for frame in range(4):
        terrain = draw_terrain(frame)
        bake_shadows(terrain, sprites)
        terrain.save(os.path.join(OUT, f'ground-{frame}.png'), SCALE)
    for key, s in sprites.items():
        s.save(os.path.join(OUT, f'{key}.png'), SCALE)

    # walkable grid at 4px cells: grass/path, not water, not under object footprints
    cell = 4
    cols, rows = W // cell, H // cell
    blocked = set()
    for (x, y) in POND:
        blocked.add((x // cell, y // cell))
    bx, by, bw, bh = meadow.BRIDGE
    for (x, y) in meadow.STREAM | meadow.STREAM_BANK:
        if not (bx + 5 <= x < bx + bw - 5):  # only the bridge deck crosses the water
            blocked.add((x // cell, y // cell))
    for (px, py) in meadow.PLOTS:
        for yy in range(py, py + meadow.PLOT_H):
            for xx in range(px, px + meadow.PLOT_W):
                blocked.add((xx // cell, yy // cell))
    for (_id, key, x, y, _a) in OBJECTS:
        s = sprites[key]
        if key == 'bridge' or y + s.h <= 0:
            continue
        foot_h = 6 if key not in ('hut', 'stall') else 14
        for yy in range(y + s.h - foot_h, y + s.h):
            for xx in range(x + 2, x + s.w - 2):
                blocked.add((xx // cell, yy // cell))
    walk = []
    for r in range(rows):
        row = ''
        for c in range(cols):
            # keep off the top tree line and out of the lower fence
            edge = r < 7 or r * cell >= meadow.FENCE_Y - 2
            row += '.' if ((c, r) not in blocked and not edge) else '#'
        walk.append(row)
    # Keep only cells the companion can reach from home (same bounds and moves
    # as lib/garden-path.ts: 8 directions, no corner cutting).
    def ok(c, r):
        x, y = c * cell + cell / 2, r * cell + cell / 2
        return (0 <= r < rows and 0 <= c < cols and walk[r][c] == '.'
                and 20 <= x <= W - 20 and 40 <= y <= meadow.FENCE_Y - 4)
    start = (96 // cell, 112 // cell)
    reached = {start}
    queue = [start]
    while queue:
        c, r = queue.pop()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            n = (c + dc, r + dr)
            if n in reached or not ok(*n):
                continue
            if dc and dr and (not ok(c + dc, r) or not ok(c, r + dr)):
                continue
            reached.add(n)
            queue.append(n)
    walk = [''.join('.' if (ch == '.' and (not ok(c, r) or (c, r) in reached)) else '#'
                    for c, ch in enumerate(line)) for r, line in enumerate(walk)]

    hotspots = {
        'nap': {'x': 73, 'y': 82, 'label': 'nap in your bed'},
        'mail': {'x': 22, 'y': 98, 'label': 'check your postcards'},
        'shop': {'x': 154, 'y': 86, 'label': "visit Moss's hat stall"},
        'missions': {'x': 112, 'y': 122, 'label': 'read the signpost to missions'},
        'feed': {'x': 92, 'y': 102, 'label': 'fill the food bowl'},
        'arena': {'x': 96, 'y': meadow.FENCE_Y - 6, 'label': 'head out the gate to the arena'},
        'meadow': {'x': 100, 'y': 258, 'label': 'see what is growing in the meadow'},
        'pond': {'x': 72, 'y': 126, 'label': 'look into the pond'},
        'read': {'x': 84, 'y': 70, 'label': 'settle into the reading nook'},
        'water': {'x': 166, 'y': 114, 'label': 'water the flower beds'},
        'lantern': {'x': 130, 'y': 88, 'label': 'tend the leaf lantern'},
    }
    sizes = {k: [v.w, v.h] for k, v in sprites.items()}
    ts = [
        '// Generated by scripts/art/garden.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const GARDEN = {{ width: {W}, height: {H}, top: {TOP}, scale: {SCALE}, cell: {cell}, fenceY: {meadow.FENCE_Y} }} as const;',
        f'export const gardenPlots = {json.dumps([{"id": f"plot-{i}", "x": x, "y": y, "w": meadow.PLOT_W, "h": meadow.PLOT_H, "kind": k} for i, ((x, y), k) in enumerate(zip(meadow.PLOTS, meadow.PLOT_KINDS))], indent=2)} as const;',
        f'export const gardenOrchard = {json.dumps([{"id": f"orchard-{i}", "x": x, "y": y} for i, (x, y) in enumerate(meadow.ORCHARD)], indent=2)} as const;',
        f'export const growthSpriteSizes = {json.dumps({k: [v.w, v.h] for k, v in growth.items()}, indent=2)} as const;',
        f'export const gardenObjects = {json.dumps([{"id": i, "sprite": k, "x": x, "y": y, "w": sizes[k][0], "h": sizes[k][1], "action": a} for (i, k, x, y, a) in OBJECTS], indent=2)} as const;',
        f'export const gardenHotspots = {json.dumps(hotspots, indent=2)} as const;',
        f'export const gardenWalk: readonly string[] = {json.dumps(walk, indent=2)};',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'garden-map.ts'), 'w') as f:
        f.write('\n'.join(ts))

    # Static imports for the meadow's growth stages (bundlers need literal paths).
    names = sorted(growth)
    camel = lambda k: ''.join(part.capitalize() if i else part for i, part in enumerate(k.split('_')))  # noqa: E731
    lines = ['// Generated by scripts/art/garden.py. Do not edit by hand.', '/* eslint-disable */',
             "import type { ImageSourcePropType } from 'react-native';"]
    lines += [f"import {camel(k)} from '@/assets/garden/growth/{k}.png';" for k in names]
    lines.append('export const growthImages: Record<string, ImageSourcePropType> = {')
    lines += [f'  {k}: {camel(k)},' for k in names]
    lines.append('};')
    lines.append('')
    with open(os.path.join(ROOT, 'lib', 'garden-growth-assets.ts'), 'w') as f:
        f.write('\n'.join(lines))

    # preview composite for review
    prev = Canvas(W, H + TOP)
    prev.paste(meadow.draw_top_band(), 0, 0)
    ground = draw_terrain(0)
    bake_shadows(ground, sprites)
    prev.paste(ground, 0, TOP)
    for (_id, key, x, y, _a) in sorted(OBJECTS, key=lambda o: o[3] + sprites[o[1]].h):
        prev.paste(sprites[key], x, y + TOP)
    # preview the meadow fully grown
    for (x, y), k in zip(meadow.PLOTS, meadow.PLOT_KINDS):
        prev.paste(growth[f'plot_{k}_4'], x, y - 10 + TOP)
    for i, (x, y) in enumerate(meadow.ORCHARD):
        t = growth[f'orchard_{[4, 2, 1][i]}']
        prev.paste(t, x - t.w // 2, y - t.h + TOP)
    prev.save('/tmp/garden-preview.png', 3)
    print('ok', W, H, len(sprites), 'sprites')


if __name__ == '__main__':
    main()
