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
import garden_meadow as meadow  # noqa: E402
import style  # noqa: E402
import garden_props as props  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'garden')
os.makedirs(OUT, exist_ok=True)

W, H = meadow.W, meadow.H  # native map: the clearing at the top, the meadow below
TOP = meadow.TOP  # forest band above y = 0
# Exported at 4x: one image pixel per device pixel on a 3x phone (the shared grid is
# 4 device pixels per art pixel there), and a quarter of the memory a 6x export needed.
SCALE = 4

# ---- palette -------------------------------------------------------------
from materials import G, P, WTR, SAND, WOOD, STONE, LEAF, NAP, RED, CREAM, GOLD, INK, PLASTER, SOIL  # noqa: E402


# ---- terrain masks (native pixels) ----------------------------------------
def thick_path(points, radius, wobble_seed):
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 13, wobble_seed) - 0.5) * 3.2
            pts |= disc(cx, cy, r)
    return pts


PX = meadow.PATH_X
PLAZA = (PX, 184)
# Paths are at least 36 wide (a companion fits with room on both sides).
PATH = thick_path([(PX, 300), (PX - 1, 262), (PX + 1, 222), PLAZA], 18.5, 1)
HUT_LINE = [(PX - 12, 180), (118, 158), (84, 136), (68, 126)]
HUT_BRANCH = thick_path(HUT_LINE, 13.5, 2)
PATH |= HUT_BRANCH  # to the nap hut
PATH |= thick_path([(PX + 12, 178), (206, 156), (244, 132), (262, 116)], 13.5, 3)  # to Moss's stall
PATH |= thick_path([(PX + 4, 170), (168, 128), (172, 92)], 9.5, 4)  # a quiet reading corner
# the trail on up through the treeline to the Snowy Ridge (world-atlas.md)
RIDGE_X = 206  # between the reading nook and Moss's stall
PATH |= thick_path([(172, 92), (200, 84), (206, 40), (RIDGE_X, -16)], 9.5, 4)
# a footpath on past the stall, under the little tree's crown, out of the garden's east
# side to the Riverside's lane from the mill: 8 px wide (rows 112-119) where it crosses
# x 319, square to the edge, so the Riverside's lane meets it at the same row and width
PATH |= thick_path([(256, 116), (276, 114), (296, 116)], 4.4, 5)
PATH |= {(x, y) for x in range(292, W + 12) for y in range(112, 120)}
PATH |= disc(PLAZA[0], PLAZA[1], 27)  # the plaza at the fork
PATH |= meadow.meadow_path(thick_path)  # down across the bridge, through the meadow
# The hut's own path, which can be laid with flagstones (coherence plan, B1): its branch
# from where it leaves the plaza and the main path up to the hut's step.
HUT_PAVING = HUT_BRANCH - thick_path([(PX, 300), (PX - 1, 262), (PX + 1, 222), PLAZA], 18.5, 1) \
    - disc(PLAZA[0], PLAZA[1], 27)
HUT_PATHS = ('earth', 'flagstones')


def flagstones(cv: Canvas, seed: int = 11):
    """Flagstones laid up the middle of the hut's path, from the plaza to the step: a
    strip of irregular flat slabs (crazy paving: each pixel belongs to its nearest slab
    centre, two across, staggered) parted by thin packed-earth seams. Each slab is lit
    along its top and left edges and darker along the bottom and right, with the odd
    pale fleck and moss in a seam; earth shows either side of the strip."""
    line = [(68, 119), (84, 136), (118, 158), (PX - 12, 180)]
    segs = []
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        segs.append((x0, y0, (x1 - x0) / length, (y1 - y0) / length, length))
    centres = []
    k = 0
    for (x0, y0, ux, uy, length) in segs:
        d = 0.0
        while d < length:
            cx, cy = x0 + ux * d, y0 + uy * d
            for side in (-1, 1):
                off = side * 3.6 + (1.6 if k % 2 else -1.6)  # every other course steps over
                jx = (noise2(k, side + 3, seed) - 0.5) * 2
                jy = (noise2(k, side + 9, seed) - 0.5) * 2
                centres.append((cx - uy * off + jx, cy + ux * off + jy))
            k += 1
            d += 7.0

    def across(x, y):  # distance from the path's middle line
        best = 1e9
        for (x0, y0, ux, uy, length) in segs:
            t = max(0.0, min(length, (x - x0) * ux + (y - y0) * uy))
            best = min(best, math.hypot(x - x0 - ux * t, y - y0 - uy * t))
        return best

    strip = {(x, y) for (x, y) in HUT_PAVING if across(x + 0.5, y + 0.5) <= 7.2 + noise2(x, y, seed) * 1.4}
    cell = {}
    for (x, y) in strip:
        cell[(x, y)] = min(range(len(centres)),
                           key=lambda i: (x + 0.5 - centres[i][0]) ** 2 + (y + 0.5 - centres[i][1]) ** 2)
    # the paving ends slab by slab where the branch meets the main path, not on a cut line
    whole = {i for i, (cx, cy) in enumerate(centres)
             if all((int(cx) + ax, int(cy) + ay) in HUT_PAVING for ax in (-4, 0, 4) for ay in (-4, 0, 4))}
    strip = {p for p in strip if cell[p] in whole}
    cell = {p: cell[p] for p in strip}
    # seams: where the slab to the right or below is another one; the strip's edge is a seam too
    seam = {(x, y) for (x, y) in strip
            if any(cell.get((x + ax, y + ay), -1) != cell[(x, y)] for ax, ay in ((1, 0), (0, 1)))}
    for (x, y) in strip:
        if (x, y) in seam:
            cv.set(x, y, P[1] if noise2(x, y, seed + 5) > 0.06 else LEAF[2])
            continue
        c = cell[(x, y)]
        lit = cell.get((x - 1, y)) != c or cell.get((x, y - 1)) != c or (x - 1, y) in seam or (x, y - 1) in seam
        dark = (x + 1, y + 1) in seam or (x, y + 1) in seam
        n = noise2(x, y, seed + 3)
        tone = 4 if lit and not dark else 2 if dark else 3
        if tone == 3 and n < 0.10:
            tone = 2
        elif tone == 3 and n > 0.95:
            tone = 4
        cv.set(x, y, STONE[tone])

POND_C, POND_R = (70, 214), (44, 24)
# The overlay box the pond's animation is cut to; components/atlas-walk.tsx and the world
# lint place it at these numbers, so the pond and its bank stay inside it.
POND_BOX = (22, 186, 96, 56)


POND_RECT = (30, 194, 110, 234, 9)  # x0, y0, x1, y1, corner radius: on the soft grid (verticality.md 4f)


def _pond_reach(x: float, y: float) -> float:
    """How far inside the pond's rounded rectangle (x, y) lies, in px (negative outside),
    the edge roughened within about 2 px so it reads as a natural bank on a made shape
    (Matt, 19 Oct 22:40, B11: not an ellipse with an even rim). The south-east corner,
    where it spills, reaches a little further and lies lower."""
    x0, y0, x1, y1, r = POND_RECT
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    d = r - math.hypot(x - cx, y - cy) if (cx != x and cy != y) else min(x - x0, x1 - x, y - y0, y1 - y)
    d += (smooth_noise(x, y, 6, 5) - 0.5) * 3.2
    if x > 82 and y > 222:
        d += 1.2  # the spill
    return d


POND = {(x, y) for y in range(POND_RECT[1] - 3, POND_RECT[3] + 4) for x in range(POND_RECT[0] - 3, POND_RECT[2] + 4)
        if _pond_reach(x + 0.5, y + 0.5) >= 0}
BANK = set()
for (x, y) in POND:
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if (x + dx, y + dy) not in POND and dx * dx + dy * dy <= (2.2 + noise2(x + dx, y + dy, 6) * 1.4) ** 2:
                BANK.add((x + dx, y + dy))
assert all(POND_BOX[0] < x < POND_BOX[0] + POND_BOX[2] - 1 and POND_BOX[1] < y < POND_BOX[1] + POND_BOX[3] - 1
           for (x, y) in POND | BANK), 'the pond outgrew its overlay box'


def _depth_map(region: set) -> dict:
    """Each water pixel's distance in from the rim (4-neighbour steps), so the deep water
    follows the pond's own shape rather than a smaller ellipse inside it."""
    from collections import deque
    dist, q = {}, deque()
    for (x, y) in region:
        if any((x + dx, y + dy) not in region for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            dist[(x, y)] = 1
            q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p in region and p not in dist:
                dist[p] = dist[(x, y)] + 1
                q.append(p)
    return dist


POND_DEPTH = _depth_map(POND)


def _rill_points():
    """The pond's overflow: a trickle from its south rim, down the slope between the pond and
    the main path, through a notch in the stream's stone bluff into the stream (still water
    needs an outlet; art-faults.md rule 7). Returns the rill's water and its banks."""
    pts = [(90, 230), (94, 239), (91, 248), (85, 256), (87, 265), (95, 273), (94, 283), (92, 296)]
    water = set()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for k in range(0, 41):
            t = k / 40
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            wob = (smooth_noise(0, y, 5, 31) - 0.5) * 1.6
            wide = 2 if abs(y - 256) < 4 or abs(y - 273) < 3 else 1  # it pools a little on the bends
            for dx in range(-1, wide + 1):
                if dx == wide and y < 280 and noise2(int(x), int(y), 32) < 0.35:
                    continue  # it narrows here and there
                water.add((int(round(x + wob)) + dx, int(round(y))))
    water = {(x, y) for (x, y) in water if (x, y) not in POND and y < meadow.STREAM_TOP.get(x, 999)}
    banks = {(x + dx, y + dy) for (x, y) in water for dx in (-1, 1) for dy in (-1, 0, 1)} - water - POND - BANK
    return water, banks


RILL, RILL_BANK = _rill_points()

# Raised flower planters# Raised flower planters beside the stall path (decorative, watered by the can).
FLOWER_BEDS = [(222, 142, 46, 18), (222, 168, 46, 18)]  # x, y, w, h: a matched pair by the lantern
LILY_PADS = [(44, 208), (49, 212), (40, 213), (52, 205), (96, 220), (100, 216)]  # in two clusters, the frog on the first
FROG_PAD = LILY_PADS[0]


def draw_terrain(frame: int, hut_path: str = 'earth') -> Canvas:
    cv = Canvas(W, H)
    phase = frame % 4
    # Broad, close-valued grass masses with soft, dithered edges, then many small
    # tufts of blades (dark roots, lit tips) in a few shapes, denser toward the edges
    # and around props, sparse in the trodden clearing (coherence plan, 6c).
    import detail
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 30, 11)
            light = n > 0.66 or (n > 0.62 and (x + y) % 2 == 0) or (n > 0.6 and (x + 2 * y) % 4 == 0)
            cv.set(x, y, G[3] if light else G[2])
    for ty in range(0, H, 6):
        for tx in range(0, W, 6):
            x = tx + int(noise2(tx, ty, 4) * 6)
            y = ty + int(noise2(tx, ty, 5) * 6)
            clearing = ((x - PLAZA[0]) / 70) ** 2 + ((y - PLAZA[1] + 40) / 70) ** 2 < 1
            edge = min(x, W - x, y, H - y) < 26
            cluster = smooth_noise(x, y, 34, 63) > 0.58
            density = 0.05 if clearing else 0.5 if edge else 0.36 if cluster else 0.14
            if noise2(tx, ty, 3) < density:
                ground = 3 if cv.get(x, y)[:3] == tuple(int(G[3][k:k + 2], 16) for k in (1, 3, 5)) else 2
                kind = int(noise2(tx, ty, 8) * 6) if not clearing else 3
                detail.grass_tuft(cv, x, y, kind, G, ground)
            elif noise2(tx, ty, 7) < 0.07:
                cv.set(x, y, '#E9E4CF')  # a tiny white flower
                cv.set(x, y + 1, G[1])
            elif noise2(tx, ty, 9) < 0.05:  # clover: three leaves, lit on the left
                cv.set(x, y, G[4]); cv.set(x + 1, y, G[3]); cv.set(x, y + 1, G[3]); cv.set(x + 1, y + 1, G[1])

    # The pond's bank, by side (B11): damp earth and mud on the low south side, a chain of
    # rounded stones along the west shore doubled at the corner, a mossy boulder pile at the
    # north-west corner, grass coming down to the water on the east (the viewing edge);
    # the far north bank shows its earth face in the water drawing below.
    for (x, y) in BANK:
        if not (0 <= x < W and 0 <= y < H):
            continue
        south = y > POND_C[1] + 6
        west = x < POND_C[0] - 30
        c = SOIL[2] if south and noise2(x, y, 21) < 0.7 else P[1] if noise2(x, y, 22) < 0.6 else G[1]
        if west or (x < 46 and y < 200):
            c = STONE[2] if noise2(x // 2, y // 2, 23) > 0.35 else STONE[1]
        elif x > POND_C[0] + 30 and not south:
            c = G[2] if noise2(x, y, 24) > 0.3 else G[1]
        cv.set(x, y, c)
    for (x, y) in BANK:
        if (x, y - 1) not in BANK and (x, y - 1) not in POND and 0 <= x < W:
            cv.set(x, y - 1, G[1])  # turf lip over the bank
    for (sx, sy, big) in ((27, 200, True), (31, 195, False), (26, 207, False), (27, 214, False), (26, 221, False),
                          (29, 228, False), (36, 192, False)):  # the stone chain and the corner pile
        for (x, y) in oval(sx, sy, 3.2 if big else 2.2, 2.2 if big else 1.6):
            lit = (x - sx) + (y - sy) < -0.5
            cv.set(x, y, STONE[4] if lit else STONE[3] if (x - sx) + (y - sy) < 1 else STONE[1])
        if big:
            cv.set(sx - 1, sy - 2, LEAF[3]); cv.set(sx, sy - 2, LEAF[2]); cv.set(sx + 1, sy - 2, LEAF[3])  # moss
    for (x, y) in POND:
        dd = POND_DEPTH[(x, y)]
        col = WTR[1] if dd > 7 or (dd == 7 and (x + y) % 2) else WTR[2]  # deep water follows the rim
        # Looking down into the pond, the far bank shows its earth face above the
        # water, and the water under it lies in its shadow (coherence plan, 6c).
        k = next((i for i in range(5) if (x, y - i - 1) not in POND), 5)
        if k == 0:
            col = P[1]
        elif k in (1, 2):
            col = P[0] if (x // 3 + k) % 4 else P[1]
        elif k == 3:
            col = WTR[0]
        elif k == 4:
            col = WTR[1]
        cv.set(x, y, col)
    # Four-frame, one-pixel ripple loops. Each little arc advances on its own
    # phase, so the pond breathes without the banks or lily pads sliding about.
    # Color and arc length ease around the cycle instead of blinking on/off.
    for i in range(18):
        rx = POND_C[0] - 32 + int(noise2(i, 1, 30) * 64)
        ry = POND_C[1] - 12 + int(noise2(i, 2, 30) * 24)
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
    for (lx, ly) in LILY_PADS:
        for (x, y) in oval(lx, ly, 4.5, 3):
            cv.set(x, y, LEAF[3] if y < ly else LEAF[2])
        cv.set(lx + 1, ly - 1, WTR[2])
        cv.set(lx, ly - 2, LEAF[4])
        cv.hline(lx - 2, ly, 3, LEAF[1])
        cv.set(lx - 1, ly - 1, LEAF[4])
    cv.set(LILY_PADS[1][0], LILY_PADS[1][1] - 2, RED[4]); cv.set(LILY_PADS[1][0] + 1, LILY_PADS[1][1] - 2, RED[3])  # a water flower
    # Reeds make the bank belong to the water: they grow in clumps along the shaded side
    # (the south and east rim, away from the light), thinning out round to the west and
    # leaving the viewing edge east of the pond and the outlet open.
    rim = sorted((x, y) for (x, y) in POND if any((x + dx, y + dy) not in POND for dx, dy in ((1, 0), (0, 1))))
    clumps = []
    for (x, y) in rim:
        a = math.degrees(math.atan2((y - POND_C[1]) / POND_R[1], (x - POND_C[0]) / POND_R[0]))
        if not (-25 <= a <= 150):
            continue
        if x > 104 and abs(y - 214) < 9 or 84 <= x <= 97 and y > 226:
            continue  # the viewing edge and the outlet
        if all(abs(x - cx) + abs(y - cy) > 9 for (cx, cy) in clumps) and noise2(x, y, 41) < (0.5 if a < 110 else 0.2):
            clumps.append((x, y))
    for ci, (cx, cy) in enumerate(clumps):
        for b in range(3 + ci % 3):
            bx = cx - 2 + b * 2 - (ci % 2)
            hgt = 5 + int(noise2(bx, cy, 42) * 5)
            lean = 1 if noise2(bx, cy, 43) > 0.6 else 0
            for k in range(hgt):
                x = bx + (lean if k > hgt * 0.6 else 0)
                cv.set(x, cy - k, LEAF[3] if (b == 0 and k > 1) else LEAF[2] if k > hgt // 2 else LEAF[1])
            if b % 2 == 0 and hgt > 7:  # a cattail head on the taller stems
                top = cy - hgt
                cv.set(bx, top, WOOD[3]); cv.set(bx, top + 1, WOOD[2]); cv.set(bx, top + 2, WOOD[1])
        cv.hline(cx - 2, cy + 1, 6, WTR[0])  # their shade on the water
    for sx, sy in ((24, 220), (46, 240), (96, 192)):
        cv.hline(sx, sy, 5, STONE[1])
        cv.hline(sx + 1, sy - 1, 3, STONE[3])
        cv.set(sx + 1, sy - 2, STONE[4])

    meadow.draw_stream(cv, phase)
    # The pond's overflow trickling down to the stream: wet earth banks with a turf lip,
    # the water lit on its left, a few pebbles in its bed, and a little fall where it
    # drops through a notch in the bluff, foaming where it meets the stream.
    for (x, y) in RILL_BANK:
        if 0 <= y < H and (x, y) not in meadow.STREAM:
            shaded = (x - 1, y) in RILL  # the east bank faces away from the light
            cv.set(x, y, P[0] if shaded else P[2] if (x + 1, y) in RILL else P[1])
            if shaded and (x + 1, y) not in RILL_BANK and noise2(x, y, 33) < 0.6:
                cv.set(x + 1, y, G[1])  # the turf lip over the shaded bank
    for (x, y) in sorted(RILL):
        fall = y >= meadow.STREAM_TOP.get(x, 999) - meadow.BLUFF_H.get(x, 0) - 1
        left, right = (x - 1, y) not in RILL, (x + 1, y) not in RILL
        if fall:
            c = WTR[4] if (x + y) % 3 == 0 else WTR[3] if left else WTR[2]
        else:
            c = WTR[3] if left else WTR[1] if right else WTR[2]
            if (y * 7 + x) % 11 == 0 and not left and not right:
                c = WTR[4]  # a glint where it runs over a stone
        cv.set(x, y, c)
    for (x, y) in sorted(RILL):
        if (x, y + 1) not in RILL and (x, y + 1) in meadow.STREAM:
            cv.set(x, y + 1, WTR[4]); cv.set(x - 1, y + 2, WTR[3]); cv.set(x + 1, y + 2, WTR[3])  # foam below the fall
    for (x, y) in sorted(RILL):  # where the rill drops through the earth bank: a stone lip
        if y == meadow.STREAM_TOP.get(x, 999) - meadow.BLUFF_H.get(x, 0) + 1:
            for dx in (-3, -2, 2, 3):
                cv.set(x + dx, y - 1, STONE[4] if dx < 0 else STONE[3]); cv.set(x + dx, y, STONE[2] if dx < 0 else STONE[1])
                cv.set(x + dx, y + 1, STONE[1] if dx < 0 else STONE[0])
            cv.hline(x - 1, y + 1, 3, STONE[3])  # the flat lip stone the water pours over
    for (sx, sy) in ((87, 235), (96, 236)):  # the stones the pond spills between
        cv.hline(sx, sy, 3, STONE[2]); cv.set(sx, sy - 1, STONE[4]); cv.set(sx + 1, sy - 1, STONE[3]); cv.set(sx + 2, sy, STONE[1])
    for (px, py) in ((92, 247), (88, 266)):
        if (px, py) in RILL:
            cv.set(px, py, STONE[3]); cv.set(px + 1, py, STONE[1])

    # Paths sit lower than the turf. Packed dirt with clean lighter patches and
    # small dark specks; where the turf above drops onto the path it leaves a
    # dark lip and a shadow line, and the turf edge facing up catches the light.
    dirt = PATH - meadow.STREAM
    for (x, y) in dirt:
        if not (0 <= x < W and 0 <= y < H):
            continue
        n = smooth_noise(x, y, 7, 40)
        cv.set(x, y, P[4] if n > 0.7 else P[3])  # sandy packed earth, paler where worn
    for i in range(260):
        x = int(noise2(i, 0, 50) * W)
        y = int(noise2(i, 1, 50) * H)
        if (x, y) in dirt and (x + 1, y) in dirt and (x, y + 1) in dirt:
            cv.set(x, y, P[1])
            if i % 3 == 0:
                cv.set(x + 1, y, P[1])
            if i % 5 == 0:
                cv.set(x, y - 1, P[4])
    if hut_path == 'flagstones':
        flagstones(cv)
    # Ragged turf breaks onto the path in lit teeth with shade beneath (detail.py).
    import detail as _edge
    bridge = {(x, y) for (x, y) in dirt if BX0 <= x < BX1 and BY0 <= y < BY1} if 'BX0' in globals() else set()
    # The main path runs on past the bottom edge into Crossroads Town (world-atlas.md,
    # seamless travel), so the border itself gets no turf edge: rows below the map count.
    # The same at the top: the path carries on up into the ridge's trail (the top band and
    # the Snowy Ridge), so rows above the map count too and no turf lip crosses it at y 0.
    top_rows = {(x, y) for (x, y0) in dirt if y0 == 0 for y in range(-12, 0)}
    _edge.grass_edge(cv, {(x, y) for (x, y) in dirt if 0 <= y} | top_rows, G, P, keep=bridge, seed=7)
    for (x, y) in dirt:
        if (x, y + 1) not in PATH and (x, y + 1) not in meadow.STREAM and 0 <= y + 1 < H:
            cv.set(x, y + 1, G[3])  # the lit edge of the turf below the path

    # footprints of a small creature along the main path
    for i, y in enumerate(range(212, 280, 10)):
        x = PX - 4 + (6 if i % 2 else 0)
        cv.set(x, y, P[1]); cv.set(x + 1, y, P[1]); cv.set(x, y + 1, P[1])

    meadow.draw_beds(cv)
    meadow.draw_lower_details(cv, PATH)

    # The flower planters by the lantern: the same raised timber beds as the meadow's,
    # planted with tulips, chamomile and lavender in rows.
    for bi, (bx, by, bw, bh) in enumerate(FLOWER_BEDS):
        meadow.flower_planter(cv, bx, by, bw, bh, seed=bi)
    # A pair of hand-painted crop markers gives the beds a cared-for history.
    for mx, my, petal in ((FLOWER_BEDS[0][0] + FLOWER_BEDS[0][2] - 9, FLOWER_BEDS[0][1] + 4, RED[3]), (FLOWER_BEDS[1][0] + FLOWER_BEDS[1][2] - 9, FLOWER_BEDS[1][1] + 4, NAP[3])):
        cv.vline(mx, my - 3, 5, WOOD[1])
        cv.rect(mx - 2, my - 5, 5, 3, CREAM[2])
        cv.hline(mx - 2, my - 5, 5, CREAM[3])
        cv.set(mx, my - 4, petal)
    # wildflower clusters in the grass
    for i in range(30):
        x = int(noise2(i, 3, 60) * (W - 8)) + 4
        y = int(noise2(i, 4, 60) * (meadow.STREAM_Y - 60)) + 30
        if (x, y) in PATH or (x, y) in POND or (x, y) in BANK:
            continue
        col = [CREAM[3], '#F2D16B', NAP[4], RED[4]][i % 4]
        cv.set(x, y, col); cv.set(x + 2, y + 1, col); cv.set(x + 1, y + 2, col)
        cv.set(x + 1, y + 1, '#E8A33D' if col != '#F2D16B' else RED[2])
    # The perimeter is richer than the clearing: ferns under the trees, a few
    # fallen leaves and tiny mushroom families. All stay low to the ground.
    for fx, fy in ((8, 40), (130, 34), (310, 122), (300, 262), (14, 180), (118, 262)):
        cv.vline(fx, fy - 4, 6, LEAF[1])
        for dx, dy in ((-3, -2), (-2, -4), (-1, -5), (1, -4), (2, -2), (3, 0)):
            cv.hline(fx + dx, fy + dy, 2, LEAF[2])
            cv.set(fx + dx, fy + dy - 1, LEAF[3])
        cv.set(fx, fy - 5, LEAF[4])
    for mx, my in ((22, 168), (212, 72), (196, 260)):
        for dx, dy, size in ((0, 0, 3), (4, 2, 2)):
            cv.vline(mx + dx, my + dy - 2, 3, CREAM[2])
            cv.hline(mx + dx - 1, my + dy - 3, size, RED[2])
            cv.hline(mx + dx - 1, my + dy - 4, size, RED[3])
            cv.set(mx + dx - 1, my + dy - 4, CREAM[3])
    for lx, ly in ((20, 250), (138, 40), (300, 160), (230, 262), (12, 70)):
        cv.hline(lx, ly, 3, WOOD[2]); cv.set(lx + 1, ly - 1, WOOD[3])
        cv.set(lx + 3, ly + 1, WOOD[1])
    return cv


# ---- compose -------------------------------------------------------------
# Objects are listed with their top-left and action; the app depth-sorts them by
# their foot (y + h). Positions follow the proportions table (coherence plan).
OBJECTS = [
    # the forest along the top edge, behind the HUD
    # (two pines stand back to let the ridge trail through the trees)
    *[(f'pine-{i}', 'pine', x, y, None) for i, (x, y) in meadow.TREELINE.items()],
    # (no broadleaf trees in the band: the ridge's edge here is pines and open meadow)
    # the clearing
    ('hut', 'hut', 16, 28, 'nap'),
    ('bed', 'bed', 128, 98, 'nap'),
    ('mailbox', 'mailbox', 2, 92, 'mail'),
    ('stall', 'stall', 218, 30, 'shop'),
    ('reading-nook', 'reading_nook', 150, 46, 'read'),
    ('lantern', 'lantern', 198, 96, 'lantern'),
    ('signpost', 'signpost', 182, 150, 'missions'),
    ('bowl', 'bowl', 100, 128, 'feed'),
    # clutter against the hut and the stall (Matt's references)
    ('pot-1', 'potted_plant', 44, 106, None),
    ('pot-2', 'potted_plant', 82, 107, None),
    ('barrel-1', 'barrel', 118, 102, None),
    ('crate-1', 'crate', 202, 86, None),
    ('sack-1', 'sack', 206, 76, None),
    ('barrel-2', 'barrel', 304, 84, None),
    ('watering-can', 'watering_can', 290, 188, 'water'),
    ('tree-6', 'tree_small', 284, 108, None),
    ('tree-7', 'tree', -30, 186, None),
    ('bush-1', 'bush', 0, 146, None),
    ('bush-2', 'bush', 290, 240, None),
    ('bush-3', 'bush', 120, 256, None),
    ('rock-1', 'rock0', 128, 184, None),
    ('rock-2', 'rock1', 210, 246, None),
    # the meadow below the stream
    ('meadow-sign', 'meadow_sign', 178, 334, 'meadow'),
    ('rock-3', 'rock0', 98, 488, None),
    ('rock-4', 'rock1', 296, 496, None),
    ('bush-4', 'bush', 6, 476, None),
    ('bush-5', 'bush', 232, 488, None),
    ('fence-l', 'fence_l', 0, meadow.FENCE_Y, None),
    ('fence-r', 'fence_r', meadow.GATE_X + meadow.GATE_W, meadow.FENCE_Y, None),
    ('gate', 'gate', meadow.GATE_X, meadow.GATE_Y, 'arena'),
    ('tree-8', 'tree', -32, 428, None),  # B9: off the fence line, inside it
    ('tree-9', 'tree_small', 280, 446, None),  # B9: inside the fence by its east strainer, off its line
    # (B9: the two low pines that stood on the fence line came out; the meadow stays open to the fence)
]

# Where the companion stands for each place, and named points the app draws from.
HOTSPOTS = {
    'nap': {'x': 143, 'y': 124, 'label': 'nap in your bed'},
    'mail': {'x': 26, 'y': 136, 'label': 'check your postcards'},
    'shop': {'x': 262, 'y': 120, 'label': "visit Moss's hat stall"},
    'missions': {'x': 196, 'y': 198, 'label': 'read the signpost to missions'},
    'feed': {'x': 110, 'y': 148, 'label': 'fill the food bowl'},
    'arena': {'x': meadow.PATH_X, 'y': meadow.FENCE_Y - 6, 'label': 'head out of the gate into the valley'},
    'meadow': {'x': 186, 'y': 380, 'label': 'see what is growing in the meadow'},
    'pond': {'x': 124, 'y': 214, 'label': 'look into the pond'},
    'read': {'x': 172, 'y': 88, 'label': 'settle into the reading nook'},
    'water': {'x': 286, 'y': 214, 'label': 'water the flower beds'},
    'lantern': {'x': 214, 'y': 146, 'label': 'tend the leaf lantern'},
}


def flower_points():
    """Where the decorative planters' flowers stand (the watering reaction's drops)."""
    out = []
    for (bx, by, bw, bh) in FLOWER_BEDS:
        for fy in range(by + 4, by + bh - 3, 7):
            for fx in range(bx + 4, bx + bw - 4, 7):
                out.append({'x': fx, 'y': fy})
    return out


ANCHORS = {
    'start': {'x': meadow.PATH_X, 'y': 196},
    'bed': {'x': 143, 'y': 110},
    'chimney': {'x': 16 + 75, 'y': 28 + 9},  # the top-down hut's chimney cap
    'book': {'x': 150 + 32, 'y': 46 + 11},
    'frogPad': {'x': FROG_PAD[0], 'y': FROG_PAD[1]},
    'pondRipple': {'x': POND_C[0] - 26, 'y': POND_C[1] + 2},
    'pond': {'x': POND_C[0] - POND_R[0], 'y': POND_C[1] - POND_R[1], 'w': 2 * POND_R[0], 'h': 2 * POND_R[1]},
    'butterflies': {'x': 252, 'y': 150},
    'fireflies': {'x': 30, 'y': 60, 'w': 240, 'h': 200},
    'companionSpots': [{'x': 120, 'y': 258}, {'x': 250, 'y': 214}, {'x': 40, 'y': 256}],
    'keepsakes': {
        'rest': {'x': 166, 'y': 112},
        'read': {'x': 200, 'y': 68},
        'move': {'x': 234, 'y': 206},
        'create': {'x': 40, 'y': 140},
    },
    'flowers': flower_points(),
    # Night light (coherence plan, 6c): warm pools on the ground and glows on glass,
    # drawn by light_pool() and shown after dark (the lantern only while it is lit).
    'lights': [
        {'id': 'lantern-pool', 'kind': 'lantern', 'x': 183, 'y': 124, 'w': 44, 'h': 22},
        {'id': 'lantern-halo', 'kind': 'lantern', 'x': 199, 'y': 102, 'w': 18, 'h': 18},
        {'id': 'hut-pool', 'kind': 'night', 'x': 30, 'y': 112, 'w': 76, 'h': 18},
        {'id': 'hut-window-l', 'kind': 'night', 'x': 36, 'y': 82, 'w': 14, 'h': 16},
        {'id': 'hut-window-r', 'kind': 'night', 'x': 86, 'y': 82, 'w': 14, 'h': 16},
        {'id': 'stall-glow', 'kind': 'night', 'x': 224, 'y': 56, 'w': 76, 'h': 22},
        {'id': 'stall-pool', 'kind': 'night', 'x': 218, 'y': 98, 'w': 88, 'h': 16},
    ],
}


def light_pool(w: int, h: int) -> Canvas:
    """A warm pool of light as three crisp, stepped bands (no smooth gradient, so it
    stays on the pixel grid): brightest at the centre, fading to the edge."""
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            d = ((x + 0.5 - w / 2) / (w / 2)) ** 2 + ((y + 0.5 - h / 2) / (h / 2)) ** 2
            if d <= 1:
                a = 150 if d < 0.25 else 100 if d < 0.6 else 55
                if 0.55 < d < 0.62 and (x + y) % 2:
                    a = 55
                cv.set(x, y, (255, 214, 122, a))
    return cv


def bake_shadows(terrain: Canvas, sprites: dict):
    """Cast shadows (coherence plan, 6c): every standing object throws its own silhouette
    down and to the right (light from the upper left), so height reads from the ground.
    All shadows are one tone, merged so they never stack; then contact shade where each
    object meets the ground, and forest shade along the treeline."""
    import detail
    shade = set()
    for (_id, key, x, y, _a) in OBJECTS:
        s = sprites[key]
        if _id.startswith(('pine-', 'tree-')) and y + s.oy + s.h < 34:
            continue  # the treeline's shade is its crowns' lobes below (crown_shade), not flat smears
        shade |= detail.silhouette_shadow(s, x + s.ox, y + s.oy)
    for (sx, sy) in shade:
        style.darken(terrain, sx, sy)
    # Contact shade: the ground darkens along each base, two pixels deep under the
    # lit side, so props sit in the grass rather than on it.
    for (_id, key, x, y, _a) in OBJECTS:
        s = sprites[key]
        foot = y + s.oy + s.h
        for xx in range(s.w):
            if s.get(xx, s.h - 1)[3]:
                style.darken(terrain, x + s.ox + xx, foot)
                style.darken(terrain, x + s.ox + xx + 1, foot + 1)
    # The forest's shade spills into the clearing: the ridge's forest floor runs on across
    # the seam and thins out (garden_meadow.forest_edge_shade, the ridge's own field), and
    # each pine of the treeline casts its lobe (garden_meadow.crown_shade), raggedly,
    # never in ruled rows.
    for y in range(0, 28):
        for x in range(W):
            if (x, y) in PATH:  # the path is only dappled where it runs on from the ridge's trail
                if meadow.trail_dapple(x, y):
                    style.darken(terrain, x, y, (0.85, 0.86, 0.9))
                continue
            e, k = meadow.forest_edge_shade(x, y), meadow.crown_shade(x, y)
            if e > 0.12 or k > 0.62 or (k > 0.38 and (x + y) % 2 == 0) or (k > 0.22 and (x + 2 * y) % 4 == 0):
                style.darken(terrain, x, y)
            if e > 0.55:
                style.darken(terrain, x, y, (0.78, 0.8, 0.84))


# The hut's outside as the player chooses it (lib/decor.ts, HutLook): the door's paint
# and what sits under both windows. hut.png is the default look; the rest are variants
# beside it, all the same size and placement, so only the image changes.
HUT_BOXES = {'none': 'sill', 'flowers': 'flowers', 'herbs': 'herbs'}
HUT_DEFAULT = ('oak', 'flowers')


def hut_look(door: str, boxes: str) -> Canvas:
    return props.hut(door, (HUT_BOXES[boxes], HUT_BOXES[boxes]))


def main():
    sprites = props.props()
    sprites['hut'] = hut_look(*HUT_DEFAULT)
    sprites['fence_l'] = props.fence_h(meadow.GATE_X, strainer='w')  # B9: each run ends on a braced post
    sprites['fence_r'] = props.fence_h(W - meadow.GATE_X - meadow.GATE_W, strainer='e')
    # Flat, walkable things (the bridge deck) are part of the ground, not objects:
    # baked into every ground frame, characters always draw on top of them.
    bx, by, bw, bh = meadow.BRIDGE
    deck = style.finalize(props.bridge(bw, bh), name='bridge')
    flat = [(deck, bx + deck.ox, by + deck.oy)]
    # The sprite contract: complete tinted outlines, trimmed to the art, never cut off.
    sprites = {key: style.finalize(s, name=key) for key, s in sprites.items()}
    growth = {key: style.finalize(g, keep_size=True, name=key) for key, g in meadow.growth_sprites().items()}
    # Objects are listed at their nominal boxes; place each trimmed sprite by its offset.
    global OBJECTS
    OBJECTS = [(i, k, x + sprites[k].ox, y + sprites[k].oy, a) for (i, k, x, y, a) in OBJECTS]
    # Nothing may stick out above the forest band at the top of the map.
    for (i, k, x, y, _a) in OBJECTS:
        assert y >= -TOP, f'{i} reaches {-y} px above the map; the top band is {TOP}'
    growth_dir = os.path.join(OUT, 'growth')
    os.makedirs(growth_dir, exist_ok=True)
    for old in os.listdir(growth_dir):
        os.remove(os.path.join(growth_dir, old))
    for key, g in growth.items():
        g.save(os.path.join(growth_dir, f'{key}.png'), SCALE)
    meadow.draw_top_band().save(os.path.join(OUT, 'ground-top.png'), SCALE)
    frames = []
    for frame in range(4):
        terrain = draw_terrain(frame)
        for (decal, fx, fy) in flat:
            terrain.paste(decal, fx, fy)
        bake_shadows(terrain, sprites)
        frames.append(terrain)
    for old in os.listdir(OUT):
        if old.startswith(('ground-', 'water-')) and old != 'ground-top.png':
            os.remove(os.path.join(OUT, old))
    frames[0].save(os.path.join(OUT, 'ground.png'), SCALE)
    # Only the water moves: each water body gets four small overlay frames cropped
    # from the full frames, so the result looks exactly as before.
    def bbox(points, pad=1):
        xs = [x for x, y in points if 0 <= x < W and 0 <= y < H]
        ys = [y for x, y in points if 0 <= x < W and 0 <= y < H]
        x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
        x1, y1 = min(W - 1, max(xs) + pad), min(H - 1, max(ys) + pad)
        return (x0, y0, x1 - x0 + 1, y1 - y0 + 1)
    water = {'stream': bbox(meadow.STREAM | meadow.STREAM_BANK), 'pond': POND_BOX}
    inside = lambda x, y: any(rx <= x < rx + rw and ry <= y < ry + rh for (rx, ry, rw, rh) in water.values())  # noqa: E731
    for y in range(H):
        for x in range(W):
            base = frames[0].get(x, y)
            if any(f.get(x, y) != base for f in frames[1:]):
                assert inside(x, y), f'ground animates outside the water at {x},{y}'
    for name, (rx, ry, rw, rh) in water.items():
        for i, f in enumerate(frames):
            crop = Canvas(rw, rh)
            for y in range(rh):
                for x in range(rw):
                    crop.px[x, y] = f.get(rx + x, ry + y)
            crop.save(os.path.join(OUT, f'water-{name}-{i}.png'), SCALE)
    for key, s in sprites.items():
        s.save(os.path.join(OUT, f'{key}.png'), SCALE)
    # The hut's other looks: every door with every window planting, trimmed exactly as the
    # default (the choices stay inside its silhouette, so its shadow and footprint hold).
    hut_dir = os.path.join(OUT, 'hut')
    os.makedirs(hut_dir, exist_ok=True)
    for old in os.listdir(hut_dir):
        os.remove(os.path.join(hut_dir, old))
    base = sprites['hut']
    hut_keys = []
    for door in props.HUT_DOORS:
        for boxes in HUT_BOXES:
            hut_keys.append(f'{door}-{boxes}')
            if (door, boxes) == HUT_DEFAULT:
                continue
            v = style.finalize(hut_look(door, boxes), name='hut')
            assert (v.w, v.h, v.ox, v.oy) == (base.w, base.h, base.ox, base.oy), f'hut {door}-{boxes} moved'
            v.save(os.path.join(hut_dir, f'{door}-{boxes}.png'), SCALE)
    # The hut's path laid with flagstones: the ground drawn with them, shadows baked the
    # same way, kept as an overlay of just the pixels that differ from the earth path.
    paved = draw_terrain(0, 'flagstones')
    for (decal, fx, fy) in flat:
        paved.paste(decal, fx, fy)
    bake_shadows(paved, sprites)
    changed = [(x, y) for y in range(H) for x in range(W) if paved.get(x, y) != frames[0].get(x, y)]
    assert changed and all(p in HUT_PAVING for p in changed), 'flagstones strayed off the hut path'
    px0, py0 = min(x for x, _ in changed), min(y for _, y in changed)
    px1, py1 = max(x for x, _ in changed), max(y for _, y in changed)
    overlay = Canvas(px1 - px0 + 1, py1 - py0 + 1)
    for (x, y) in changed:
        overlay.px[x - px0, y - py0] = paved.get(x, y)
    overlay.save(os.path.join(OUT, 'path-flagstones.png'), SCALE)
    hut_paths = {'flagstones': {'x': px0, 'y': py0, 'w': px1 - px0 + 1, 'h': py1 - py0 + 1}}
    for light in ANCHORS['lights']:
        light_pool(light['w'], light['h']).save(os.path.join(OUT, f"light-{light['id']}.png"), SCALE)

    # walkable grid at 4px cells: grass/path, not water, not under object footprints
    cell = 4
    cols, rows = W // cell, H // cell
    blocked = set()
    for (x, y) in POND | RILL:
        blocked.add((x // cell, y // cell))
    for (x, y) in meadow.STREAM | meadow.STREAM_BANK | meadow.BLUFF:
        if not (bx + 6 <= x < bx + bw - 6):  # only the bridge deck crosses the water
            blocked.add((x // cell, y // cell))
    for (px, py) in meadow.PLOTS:
        for yy in range(py, py + meadow.PLOT_H):
            for xx in range(px, px + meadow.PLOT_W):
                blocked.add((xx // cell, yy // cell))
    for (fx, fy, fw, fh) in FLOWER_BEDS:
        for yy in range(fy, fy + fh):
            for xx in range(fx, fx + fw):
                blocked.add((xx // cell, yy // cell))
    for (_id, key, x, y, _a) in OBJECTS:
        s = sprites[key]
        if y + s.h <= 0:
            continue
        foot_h = 22 if key in ('hut', 'stall') else 10 if key in ('tree', 'tree_small', 'tree_autumn', 'pine') else 7
        for yy in range(y + s.h - foot_h, y + s.h):
            for xx in range(x + 3, x + s.w - 3):
                blocked.add((xx // cell, yy // cell))
    walk = []
    for r in range(rows):
        row = ''
        for c in range(cols):
            edge = r * cell < 40 or r * cell >= meadow.FENCE_Y - 2
            row += '.' if ((c, r) not in blocked and not edge) else '#'
        walk.append(row)
    # Keep only cells the companion can reach from home (same bounds and moves
    # as lib/garden-path.ts: 8 directions, no corner cutting).
    def ok(c, r):
        x, y = c * cell + cell / 2, r * cell + cell / 2
        return (0 <= r < rows and 0 <= c < cols and walk[r][c] == '.'
                and 16 <= x <= W - 16 and 48 <= y <= meadow.FENCE_Y - 4)
    start = (ANCHORS['start']['x'] // cell, ANCHORS['start']['y'] // cell)
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
    for name, spot in list(HOTSPOTS.items()) + [('start', ANCHORS['start'])] + [
            (f'companion spot {i}', p) for i, p in enumerate(ANCHORS['companionSpots'])]:
        c, r = int(spot['x']) // cell, int(spot['y']) // cell
        assert walk[r][c] == '.', f'{name} hotspot is not walkable'

    sizes = {k: [v.w, v.h] for k, v in sprites.items()}
    ts = [
        '// Generated by scripts/art/garden.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const GARDEN = {{ width: {W}, height: {H}, top: {TOP}, scale: {SCALE}, cell: {cell}, fenceY: {meadow.FENCE_Y} }} as const;',
        f'export const gardenPlots = {json.dumps([{"id": f"plot-{i}", "x": x, "y": y, "w": meadow.PLOT_W, "h": meadow.PLOT_H, "kind": k} for i, ((x, y), k) in enumerate(zip(meadow.PLOTS, meadow.PLOT_KINDS))], indent=2)} as const;',
        f'export const gardenOrchard = {json.dumps([{"id": f"orchard-{i}", "x": x, "y": y} for i, (x, y) in enumerate(meadow.ORCHARD)], indent=2)} as const;',
        f'export const growthSpriteSizes = {json.dumps({k: [v.w, v.h] for k, v in growth.items()}, indent=2)} as const;',
        f'export const gardenObjects = {json.dumps([{"id": i, "sprite": k, "x": x, "y": y, "w": sizes[k][0], "h": sizes[k][1], "action": a} for (i, k, x, y, a) in OBJECTS], indent=2)} as const;',
        '/** Flat, walkable decals baked into the ground layer (characters always draw above them). */',
        f'export const gardenFlat = {json.dumps([{"id": "bridge", "x": bx, "y": by, "w": bw, "h": bh}], indent=2)} as const;',
        '/** Animated water overlays (four frames each) on the still ground image. */',
        f'export const gardenWater = {json.dumps([{"id": k, "x": v[0], "y": v[1], "w": v[2], "h": v[3]} for k, v in water.items()], indent=2)} as const;',
        '/** Where the hut path\'s other surfaces lie over the earth path (overlays on the ground). */',
        f'export const gardenHutPaths = {json.dumps(hut_paths, indent=2)} as const;',
        f'export const gardenHotspots = {json.dumps(HOTSPOTS, indent=2)} as const;',
        '/** Named points in the garden: home, the bed, effects and keepsake places. */',
        f'export const gardenAnchors = {json.dumps(ANCHORS, indent=2)} as const;',
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

    # Static imports for the hut's looks and its path's surfaces.
    hut_var = lambda k: 'hut' + ''.join(part.capitalize() for part in k.split('-'))  # noqa: E731
    lines = ['// Generated by scripts/art/garden.py. Do not edit by hand.', '/* eslint-disable */',
             "import type { ImageSourcePropType } from 'react-native';",
             "import hut from '@/assets/garden/hut.png';",
             "import pathFlagstones from '@/assets/garden/path-flagstones.png';"]
    lines += [f"import {hut_var(k)} from '@/assets/garden/hut/{k}.png';"
              for k in hut_keys if k != '-'.join(HUT_DEFAULT)]
    lines.append('/** The hut drawn with each door and window planting, by `door-boxes`. */')
    lines.append('export const hutImages: Record<string, ImageSourcePropType> = {')
    lines += [f"  '{k}': {'hut' if k == '-'.join(HUT_DEFAULT) else hut_var(k)}," for k in hut_keys]
    lines.append('};')
    lines.append('/** The hut path\'s surfaces drawn over the earth (none for the earth itself). */')
    lines.append('export const hutPathImages: Record<string, ImageSourcePropType> = {')
    lines.append('  flagstones: pathFlagstones,')
    lines.append('};')
    lines.append('')
    with open(os.path.join(ROOT, 'lib', 'garden-hut-assets.ts'), 'w') as f:
        f.write('\n'.join(lines))

    # preview composite for review
    prev = Canvas(W, H + TOP)
    prev.paste(meadow.draw_top_band(), 0, 0)
    ground = draw_terrain(0)
    for (decal, fx, fy) in flat:
        ground.paste(decal, fx, fy)
    bake_shadows(ground, sprites)
    prev.paste(ground, 0, TOP)
    # GARDEN_PREVIEW_STAGE=empty shows a new player's meadow; otherwise it is in bloom
    grown = os.environ.get('GARDEN_PREVIEW_STAGE') != 'empty'
    for (x, y), k in zip(meadow.PLOTS, meadow.PLOT_KINDS):
        if grown:
            g = growth[f'plot_{k}_4']
            prev.paste(g, x, y - (g.h - meadow.PLOT_H) + TOP)
    for i, (x, y) in enumerate(meadow.ORCHARD):
        if grown:
            t = growth[f'orchard_{[4, 2, 1][i]}']
            prev.paste(t, x - t.w // 2, y - t.h + TOP)
    for (_id, key, x, y, _a) in sorted(OBJECTS, key=lambda o: o[3] + sprites[o[1]].h):
        prev.paste(sprites[key], x + sprites[key].ox, y + sprites[key].oy + TOP)
    prev.save(os.environ.get('GARDEN_PREVIEW', '/tmp/garden-preview.png'), 2)
    print('ok', W, H, len(sprites), 'sprites')


if __name__ == '__main__':
    main()
