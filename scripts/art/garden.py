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
from garden_decor import reading_nook, watering_can  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'garden')
os.makedirs(OUT, exist_ok=True)

W, H = 192, 176  # native map size (12 x 11 tiles of 16px)
SCALE = 6

# ---- palette -------------------------------------------------------------
G = ['#315C3B', '#5E9256', '#73A85E', '#7CAE66', '#A9CD83']  # grass dark -> light
P = ['#795C3D', '#B28D5F', '#C8A878', '#D4B789', '#E7D3A5']  # path edge -> light
WTR = ['#284C5E', '#39738A', '#62A3B1', '#A1CFD0', '#E0EFDF']  # water
SAND = ['#B89660', '#D8BC85', '#EAD5A3']
WOOD = ['#4A3122', '#6E4A30', '#93673F', '#B98A57', '#D9AE78']
STONE = ['#4B4E52', '#6F7478', '#959A9C', '#BFC3BF', '#E3E4DC']
LEAF = ['#1F4B2E', '#2F6A3A', '#47894A', '#66A85A', '#93C978']
NAP = ['#3E3466', '#5C4E8F', '#7D6BB5', '#A797D6', '#CFC4EC']  # brand lavender
RED = ['#5E2A22', '#8E3F31', '#B95A45', '#DB8366', '#F2B79B']
CREAM = ['#8C7A5E', '#C9B48E', '#E9DCBC', '#FBF4E4']
INK = '#2A2421'


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
    # Broad, close-valued grass masses. Detail gathers near the garden's edges,
    # leaving the companion's clearing quieter than the plants and buildings.
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 22, 11)
            base = G[2] if n < 0.62 else G[3]
            cv.set(x, y, base)
    # Jittered clusters, rather than a visible lawn of repeated tile marks.
    for ty in range(0, H, 8):
        for tx in range(0, W, 8):
            x = tx + int(noise2(tx, ty, 4) * 8)
            y = ty + int(noise2(tx, ty, 5) * 8)
            clearing = ((x - 100) / 36) ** 2 + ((y - 92) / 30) ** 2 < 1
            edge = min(x, W - x, y, H - y) < 22
            cluster = smooth_noise(x, y, 25, 63) > 0.57
            density = 0.06 if clearing else 0.42 if edge else 0.28 if cluster else 0.10
            if noise2(tx, ty, 3) < density:
                sway = 1 if (frame and noise2(tx, ty, 6) < 0.5) else 0
                cv.set(x, y + 2, G[1]); cv.set(x + 2, y + 2, G[1])
                cv.set(x + 1, y + 3, G[1])
                cv.set(x + sway, y + 1, G[1]); cv.set(x + 2 + sway, y + 1, G[1])
                cv.set(x + 1 + sway, y + 1, G[4]) if noise2(x, y, 9) < 0.4 else None
            elif edge and noise2(tx, ty, 7) < 0.15:
                cv.set(x, y, G[4])

    # pond bank (sand) then water
    for (x, y) in BANK:
        if 0 <= x < W and 0 <= y < H:
            cv.set(x, y, SAND[1] if noise2(x, y, 21) < 0.8 else SAND[2])
    for (x, y) in BANK:
        if (x, y + 1) not in BANK and (x, y + 1) not in POND:
            cv.set(x, y, SAND[0])
    for (x, y) in POND:
        depth = ((x + 0.5 - POND_C[0]) / 27) ** 2 + ((y + 0.5 - POND_C[1]) / 16) ** 2
        col = WTR[1] if depth < 0.35 else WTR[2]
        if (x, y - 1) not in POND:
            col = WTR[0]  # dark lip under the far bank
        elif (x, y - 2) not in POND:
            col = WTR[1]
        cv.set(x, y, col)
    # water ripples (animated)
    for i in range(14):
        rx = POND_C[0] - 20 + int(noise2(i, 1, 30) * 40)
        ry = POND_C[1] - 8 + int(noise2(i, 2, 30) * 16) + (1 if frame and i % 2 else 0)
        if (rx, ry) in POND and (rx + 3, ry) in POND:
            cv.hline(rx + (frame if i % 3 else 0), ry, 3, WTR[3])
            if i % 4 == 0:
                cv.set(rx + 1, ry, WTR[4])
    # lily pads
    for (lx, ly) in ((30, 128), (52, 138), (46, 124)):
        for (x, y) in oval(lx, ly, 3.5, 2.5):
            cv.set(x, y, LEAF[3] if y < ly else LEAF[2])
        cv.set(lx + 1, ly - 1, WTR[2])
        cv.set(lx, ly - 2, LEAF[4])
    cv.set(52, 136, RED[4]); cv.set(53, 136, RED[3])  # tiny water flower
    # Reeds make the bank belong to the water; retain an open viewing edge.
    for rx, ry in ((19, 128), (24, 120), (59, 125), (57, 146)):
        cv.vline(rx, ry - 4, 5, LEAF[1])
        cv.vline(rx + 2, ry - 3, 4, LEAF[2])
        cv.set(rx - 1, ry - 4, LEAF[3])
        cv.set(rx + 1, ry - 1, LEAF[3])

    # path: dirt with dark rim, grass overhang and pebbles
    for (x, y) in PATH:
        if not (0 <= x < W and 0 <= y < H):
            continue
        n = smooth_noise(x, y, 6, 40)
        col = P[2] if n < 0.74 else P[3]
        cv.set(x, y, col)
    for (x, y) in PATH:
        edge_up = (x, y - 1) not in PATH
        edge = any((x + dx, y + dy) not in PATH for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge_up:
            cv.set(x, y, P[0])
            cv.set(x, y + 1, P[1])
        elif edge:
            cv.set(x, y, P[1])
    # grass overhang: little blades poking into the dirt along the edges
    for (x, y) in PATH:
        for dx, dy in ((0, -1), (1, 0), (-1, 0)):
            if (x + dx, y + dy) not in PATH and noise2(x, y, 44) < 0.33:
                cv.set(x, y, G[3]); cv.set(x, y + 1, G[2]) if (x, y + 1) in PATH and dy == -1 else None
    for i in range(40):
        x = 70 + int(noise2(i, 0, 50) * 90)
        y = 70 + int(noise2(i, 1, 50) * 100)
        if (x, y) in PATH and (x + 1, y) in PATH and (x, y - 1) in PATH:
            cv.set(x, y, P[1]); cv.set(x + 1, y, P[0] if i % 3 == 0 else P[1])
            cv.set(x, y - 1, P[4])
    # footprints of a small creature along the main path
    for i, y in enumerate(range(116, 168, 9)):
        x = 92 + (4 if i % 2 else 0)
        cv.set(x, y, P[1]); cv.set(x + 1, y, P[1]); cv.set(x, y + 1, P[1])

    # Raised beds have a lit rim, a shaded front face and individual plants.
    for bi, (bx, by, bw, bh) in enumerate(FLOWER_BEDS):
        cv.rect(bx, by, bw, bh, WOOD[1])
        cv.rect(bx + 1, by + 1, bw - 2, bh - 2, '#5A3A26')
        cv.hline(bx + 1, by, bw - 2, WOOD[3])
        cv.hline(bx, by + bh - 1, bw, WOOD[0])
        cv.hline(bx + 1, by + bh, bw - 1, G[1])
        for fy in range(by + 3, by + bh - 2, 6):
            for fx in range(bx + 3, bx + bw - 3, 6):
                petals = [RED[3], '#F2D16B', CREAM[3], NAP[3]][(fx // 5 + fy // 5 + bi) % 4]
                stem = LEAF[2]
                cv.vline(fx, fy + 1, 3, stem)
                cv.set(fx + 1, fy + 2, LEAF[3]); cv.set(fx - 1, fy + 3, LEAF[1])
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    cv.set(fx + dx, fy + dy, petals)
                cv.set(fx, fy, '#E8A33D')
                cv.set(fx, fy - 1, CREAM[3] if petals != CREAM[3] else NAP[4])
    # wildflower clusters in the grass
    for i in range(26):
        x = int(noise2(i, 3, 60) * (W - 8)) + 4
        y = int(noise2(i, 4, 60) * (H - 30)) + 24
        if (x, y) in PATH or (x, y) in POND or (x, y) in BANK:
            continue
        col = [CREAM[3], '#F2D16B', NAP[4], RED[4]][i % 4]
        cv.set(x, y, col); cv.set(x + 2, y + 1, col); cv.set(x + 1, y + 2, col)
        cv.set(x + 1, y + 1, '#E8A33D' if col != '#F2D16B' else RED[2])
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


def tree(big: bool = True, autumn: bool = False) -> Canvas:
    w, h = (36, 46) if big else (26, 34)
    cv = Canvas(w, h)
    ramp = ['#5A2F18', '#8C4520', '#BF6A2B', '#E3964A', '#F6C774'] if autumn else LEAF
    cx = w / 2
    # trunk with bark stripes and roots
    tw = 6 if big else 4
    tx = int(cx - tw / 2)
    cv.rect(tx, h - 13, tw, 11, WOOD[2])
    cv.vline(tx, h - 13, 11, WOOD[1]); cv.vline(tx + tw - 1, h - 13, 11, WOOD[3])
    for y in range(h - 11, h - 3, 3):
        cv.set(tx + tw // 2, y, WOOD[1])
    cv.set(tx - 1, h - 3, WOOD[1]); cv.set(tx - 2, h - 2, WOOD[1]); cv.set(tx + tw, h - 3, WOOD[1]); cv.set(tx + tw + 1, h - 2, WOOD[1])
    # canopy: back row of bundles, then front row overlapping (3/4 view)
    r = 7.5 if big else 5.5
    solid: set = set()
    top = r + 1
    rows = [
        [(cx, top, r)],
        [(cx - r * 0.95, top + r * 0.75, r), (cx + r * 0.95, top + r * 0.75, r)],
        [(cx - r * 1.35, top + r * 1.6, r * 0.9), (cx, top + r * 1.45, r), (cx + r * 1.35, top + r * 1.6, r * 0.9)],
    ]
    for row in rows:
        for (bx, by, br) in row:
            leaf_bundle(cv, bx, by, br, ramp, solid)
    # A branch fork connects the canopy to its trunk.
    cv.set(tx + 1, h - 15, WOOD[1]); cv.set(tx, h - 16, WOOD[1])
    cv.set(tx + tw - 2, h - 15, WOOD[2]); cv.set(tx + tw - 1, h - 16, WOOD[2])
    # canopy underside shadow onto trunk
    for x in range(tx, tx + tw):
        cv.set(x, h - 13, WOOD[0])
    if not autumn and big:
        for (fx, fy) in ((cx - 7, top + 4), (cx + 6, top + 9), (cx - 2, top + 13)):
            cv.set(int(fx), int(fy), RED[2]); cv.set(int(fx) + 1, int(fy), RED[3]); cv.set(int(fx), int(fy) - 1, RED[4])
    cv.outline(ramp[0])
    return cv


def pine() -> Canvas:
    w, h = 22, 40
    cv = Canvas(w, h)
    cx = w // 2
    cv.rect(cx - 2, h - 8, 4, 7, WOOD[2]); cv.vline(cx - 2, h - 8, 7, WOOD[1])
    ramp = ['#173B2A', '#22543A', '#2F6E45', '#468A52', '#6CAE6A']
    solid = set()
    for tier, (ty, half) in enumerate(((4, 4), (11, 7), (19, 9), (27, 10.5))):
        for y in range(ty, ty + 10):
            span = half * (y - ty + 2) / 11
            for x in range(int(cx - span), int(cx + span) + 1):
                if 0 <= x < w and y < h - 6:
                    side = (x - cx) / max(1, span)
                    col = ramp[3] if side < -0.25 else ramp[2] if side < 0.45 else ramp[1]
                    if y == ty + 9 or (y == ty + 8 and x % 3 == 0):
                        col = ramp[1]
                    if side < -0.55 and (x + y) % 3 == 0:
                        col = ramp[4]
                    cv.set(x, y, col)
                    solid.add((x, y))
    cv.set(cx, 2, ramp[3]); cv.set(cx, 3, ramp[3])
    cv.outline(ramp[0])
    return cv


def bush() -> Canvas:
    cv = Canvas(18, 14)
    pts = disc(6, 8, 5.5) | disc(11, 7, 6) | disc(9, 10, 4.5)
    pts = {(x, y) for (x, y) in pts if 0 <= x < 18 and 0 <= y < 14}
    shade_blob(cv, pts, LEAF[1], LEAF[2], LEAF[3], LEAF[4])
    cv.set(6, 6, '#F2D16B'); cv.set(12, 5, CREAM[3]); cv.set(10, 9, '#F2D16B')
    cv.outline(LEAF[0])
    return cv


def nap_hut() -> Canvas:
    """Little lavender-roofed hut with a round door and a pillow bed out front."""
    w, h = 50, 46
    cv = Canvas(w, h)
    # walls (planks)
    cv.rect(6, 20, 38, 20, WOOD[3])
    for y in range(22, 40, 4):
        cv.hline(6, y, 38, WOOD[2])
    for x in (6, 43):
        cv.vline(x, 20, 20, WOOD[1])
    # Narrow shaded return and grain knots give the timber wall thickness.
    cv.rect(41, 23, 3, 16, WOOD[2])
    cv.vline(43, 23, 16, WOOD[1])
    for x, y in ((10, 27), (15, 35), (33, 37)):
        cv.hline(x, y, 3, WOOD[2]); cv.set(x + 1, y - 1, WOOD[4])
    cv.hline(6, 39, 38, WOOD[1])
    # foundation stones
    for i, x in enumerate(range(5, 46, 5)):
        cv.rect(x, 40, 4, 3, STONE[2 if i % 2 else 3])
        cv.hline(x, 42, 4, STONE[1])
    # roof (lavender shingles), overhanging
    for y in range(4, 22):
        span = int((y - 4) * 1.45) + 8
        x0 = w // 2 - span
        for x in range(x0, w // 2 + span):
            row = (y - 4) // 3
            col = NAP[2] if (x + row * 2) % 6 else NAP[1]
            if y % 3 == 0:
                col = NAP[1]
            if x < w // 2 - span + 2:
                col = NAP[0]
            cv.set(x, y, col)
        cv.set(x0 - 1, y, NAP[0]); cv.set(w // 2 + span, y, NAP[0])
    for x in range(w // 2 - 7, w // 2 + 8):  # ridge highlight
        cv.set(x, 4, NAP[4])
    for y in range(5, 20, 3):
        cv.set(w // 2 - 1 + (y % 2), y, NAP[3])
    cv.hline(0, 21, w, NAP[0])
    cv.hline(2, 22, w - 4, NAP[1])  # visible thickness beneath the shingles
    # round door
    door = {(x, y) for (x, y) in disc(25, 31, 6.5) if y <= 39} | {(x, y) for x in range(19, 32) for y in range(31, 40)}
    for (x, y) in door:
        col = WOOD[1] if x % 4 else WOOD[0]
        cv.set(x, y, WOOD[0] if y < 29 else col)
    for (x, y) in door:
        if any((x + dx, y + dy) not in door for dx, dy in ((1, 0), (-1, 0), (0, -1))):
            cv.set(x, y, WOOD[0])
    # A little leaf latch is a recurring garden-made detail.
    cv.set(29, 34, LEAF[3]); cv.set(30, 33, LEAF[4]); cv.set(30, 34, LEAF[2])
    # crescent moon sign above door
    for (x, y) in disc(25, 15, 3):
        if (x - 26.4) ** 2 + (y - 14.2) ** 2 > 6:
            cv.set(x, y, '#F6E7A8')
    # eave shadow on the wall under the roof
    cv.hline(6, 22, 38, WOOD[1]); cv.hline(6, 23, 38, WOOD[2])
    # window flower box
    cv.rect(33, 32, 10, 3, WOOD[1]); cv.set(34, 31, RED[3]); cv.set(36, 31, '#F2D16B'); cv.set(38, 31, RED[3]); cv.set(40, 31, NAP[4])
    cv.set(35, 31, LEAF[3]); cv.set(37, 31, LEAF[3]); cv.set(39, 31, LEAF[3])
    # little window
    cv.rect(35, 25, 6, 6, WOOD[0]); cv.rect(36, 26, 4, 4, '#9AD3EA'); cv.set(36, 26, '#E4F5FA')
    cv.vline(38, 26, 4, WOOD[0])
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
    # hats on counter
    cv.rect(8, 20, 7, 4, '#4C6E9E'); cv.rect(7, 23, 10, 1, '#36507A')          # cap
    cv.hline(9, 20, 4, '#7C9BC1')
    cv.rect(20, 17, 6, 6, '#3A3333'); cv.rect(18, 22, 10, 2, '#2A2421')       # top hat
    cv.hline(20, 21, 6, RED[2])
    for i, x in enumerate(range(31, 39)):                                     # crown
        cv.rect(x, 20, 1, 4 if i % 3 else 3, '#E8C24A')
    cv.hline(31, 23, 8, '#C99A2E')
    # awning: green/cream stripes with scalloped edge
    for y in range(4, 14):
        for x in range(0, w):
            col = '#5FA35A' if (x // 5) % 2 == 0 else CREAM[3]
            if y < 6:
                col = '#3E7D44' if (x // 5) % 2 == 0 else CREAM[2]
            elif x % 5 == 4:
                col = '#4C8A50' if (x // 5) % 2 == 0 else CREAM[2]
            cv.set(x, y, col)
    for x in range(0, w):
        if x % 5 in (1, 2, 3):
            cv.set(x, 14, '#5FA35A' if (x // 5) % 2 == 0 else CREAM[3])
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
    cv = Canvas(12, 9)
    pts = oval(6, 5, 5.5, 3.8) | oval(4, 5.5, 3.5, 3)
    shade_blob(cv, {(x, y) for (x, y) in pts if 0 <= x < 12 and 0 <= y < 9}, STONE[1], STONE[2], STONE[3], STONE[4])
    if n:
        cv.set(7, 6, LEAF[3]); cv.set(8, 6, LEAF[2])
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
    ('reading-nook', 'reading_nook', 92, 40, None),
    ('lantern', 'lantern', 118, 62, None),
    ('watering-can', 'watering_can', 172, 100, None),
    ('signpost', 'signpost', 112, 94, 'missions'),
    ('bowl', 'bowl', 74, 92, 'feed'),
    ('bush-1', 'bush', 172, 120, None),
    ('bush-2', 'bush', 4, 96, None),
    ('rock-1', 'rock0', 126, 150, None),
    ('rock-2', 'rock1', 70, 140, None),
    ('fence-l', 'fence_l', 0, 162, None),
    ('fence-r', 'fence_r', 114, 162, None),
    ('gate', 'gate', 78, 147, 'arena'),
]


def main():
    sprites = {
        'tree': tree(True), 'tree_small': tree(False), 'tree_autumn': tree(True, True), 'pine': pine(),
        'hut': nap_hut(), 'bed': bed(), 'mailbox': mailbox(), 'stall': stall(),
        'signpost': signpost(), 'bowl': bowl(), 'bush': bush(), 'rock0': rock(0), 'rock1': rock(1),
        'fence_l': fence_h(80), 'fence_r': fence_h(78), 'gate': gate(),
        'reading_nook': reading_nook(), 'watering_can': watering_can(), 'lantern': leaf_lantern(),
    }
    for frame in (0, 1):
        terrain = draw_terrain(frame)
        # bake soft shadows for every object into the terrain
        for (_id, key, x, y, _a) in OBJECTS:
            s = sprites[key]
            if key.startswith('fence') or key == 'pine':
                continue
            terrain.shadow(x + s.w / 2 + 2, y + s.h - 1, s.w * 0.42, max(2.0, s.h * 0.09))
        terrain.save(os.path.join(OUT, f'ground-{frame}.png'), SCALE)
    for key, s in sprites.items():
        s.save(os.path.join(OUT, f'{key}.png'), SCALE)

    # walkable grid at 4px cells: grass/path, not water, not under object footprints
    cell = 4
    cols, rows = W // cell, H // cell
    blocked = set()
    for (x, y) in POND:
        blocked.add((x // cell, y // cell))
    for (_id, key, x, y, _a) in OBJECTS:
        s = sprites[key]
        foot_h = 6 if key not in ('hut', 'stall') else 14
        for yy in range(y + s.h - foot_h, y + s.h):
            for xx in range(x + 2, x + s.w - 2):
                blocked.add((xx // cell, yy // cell))
    walk = []
    for r in range(rows):
        row = ''
        for c in range(cols):
            edge = r < 7 or r >= rows - 4  # keep off the top tree line and bottom fence
            row += '.' if ((c, r) not in blocked and not edge) else '#'
        walk.append(row)

    hotspots = {
        'nap': {'x': 73, 'y': 82, 'label': 'nap in your bed'},
        'mail': {'x': 22, 'y': 98, 'label': 'check your postcards'},
        'shop': {'x': 154, 'y': 86, 'label': "visit Moss's hat stall"},
        'missions': {'x': 112, 'y': 122, 'label': 'read the signpost to missions'},
        'feed': {'x': 92, 'y': 102, 'label': 'fill the food bowl'},
        'arena': {'x': 96, 'y': 140, 'label': 'head out the gate to the arena'},
        'pond': {'x': 72, 'y': 126, 'label': 'look into the pond'},
    }
    sizes = {k: [v.w, v.h] for k, v in sprites.items()}
    ts = [
        '// Generated by scripts/art/garden.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const GARDEN = {{ width: {W}, height: {H}, scale: {SCALE}, cell: {cell} }} as const;',
        f'export const gardenObjects = {json.dumps([{"id": i, "sprite": k, "x": x, "y": y, "w": sizes[k][0], "h": sizes[k][1], "action": a} for (i, k, x, y, a) in OBJECTS], indent=2)} as const;',
        f'export const gardenHotspots = {json.dumps(hotspots, indent=2)} as const;',
        f'export const gardenWalk: readonly string[] = {json.dumps(walk, indent=2)};',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'garden-map.ts'), 'w') as f:
        f.write('\n'.join(ts))

    # preview composite for review
    prev = draw_terrain(0)
    for (_id, key, x, y, _a) in sorted(OBJECTS, key=lambda o: o[3] + sprites[o[1]].h):
        prev.paste(sprites[key], x, y)
    prev.save('/tmp/garden-preview.png', 4)
    print('ok', W, H, len(sprites), 'sprites')


if __name__ == '__main__':
    main()
