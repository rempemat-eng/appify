"""Draws the three Grasslings (3 growth stages each) and their hats at 32x32.

Run: python3 scripts/art/pets.py
Writes lib/pet-sprites.ts (palette-indexed rows) and /tmp/pets-preview.png.

Technique: parts are ellipses shaded as little spheres (light from the top-left),
with 5-6 tone hue-shifted ramps, ordered dithering on band edges, a reflected
rim light, selective outlines (softer on the lit side) and a 1px occlusion line
where a front part overlaps a back part.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
S = 32
LIGHT = (-0.55, -0.7, 0.55)
_l = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _l for v in LIGHT)
BAYER = [[0, 2], [3, 1]]

# ramps: [outline, deep, shadow, base, light, highlight]
LEAF = ['#1D3A2E', '#2C5B3C', '#3B7A46', '#57A055', '#86C46C', '#C4E59B']
LEAF_B = ['#1B3330', '#264D3D', '#336946', '#4A8A4E', '#6FAE60', '#A5D489']  # back parts
CAP = ['#47181C', '#73272A', '#A23A36', '#CC5A47', '#EA8C6C', '#FFD0B4']
STONE = ['#26283A', '#454A60', '#646B80', '#8A919D', '#B5BBB8', '#E3E4D8']
MOSS = ['#22402E', '#3A6A3C', '#56904A', '#79B05B', '#A6D27A', '#D3EDA6']
GOLD = ['#5A3D14', '#8E6420', '#C18F2E', '#E3B64A', '#F5D97A', '#FFF3BF']
PETAL = ['#5C2440', '#8C3A5E', '#C25C82', '#E58BA7', '#F7BCCB', '#FFE6EC']
BUD = ['#3A2550', '#5A3A7A', '#7D58A6', '#A383CB', '#C9B3E6', '#EEE4FA']
INK = '#1B1922'
WHITE = '#FFFDF4'
BLUSH = '#F09A8C'


THRESH = [0.86, 0.62, 0.30, 0.02]


def band(t: float, x: int, y: int) -> int:
    """Ramp index 5..1 for a light value; checker-dither only within 0.035 of a threshold."""
    for i, th in enumerate(THRESH):
        if t > th:
            idx = 5 - i
            if t - th < 0.035 and (x + y) % 2 == 0:
                idx -= 1  # just above a boundary: borrow the darker tone on a checker
            return idx
    return 1


class Sprite:
    def __init__(self):
        self.c = {}      # (x, y) -> color
        self.part = {}   # (x, y) -> part id (for occlusion lines)

    def put(self, x, y, col, part=None):
        if 0 <= x < S and 0 <= y < S:
            self.c[(x, y)] = col
            if part is not None:
                self.part[(x, y)] = part


def ell_pts(cx, cy, rx, ry, rot=0.0):
    ca, sa = math.cos(rot), math.sin(rot)
    out = []
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = (dx * ca + dy * sa) / rx
            v = (-dx * sa + dy * ca) / ry
            if u * u + v * v <= 1:
                out.append((x, y, u, v))
    return out


def shade(sp: Sprite, cx, cy, rx, ry, ramp, part, rot=0.0, flat=0.0, outline=True, rim=True):
    """Shade an ellipse like a sphere. flat>0 flattens the normal (squashy bodies)."""
    pts = ell_pts(cx, cy, rx, ry, rot)
    mine = {(x, y) for (x, y, _, _) in pts}
    for (x, y, u, v) in pts:
        nz = math.sqrt(max(0.0, 1 - u * u - v * v)) + flat
        n = (u, v, nz)
        ln = math.sqrt(sum(a * a for a in n)) or 1
        d = sum(a * b for a, b in zip(n, LIGHT)) / ln
        col = ramp[band(d, x, y)]
        # reflected light along the lower-right rim
        if rim and u > 0.35 and v > 0.45 and u * u + v * v > 0.72:
            col = ramp[2]
        sp.put(x, y, col, part)
    if outline:
        for (x, y) in mine:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in mine and n not in sp.c:
                    lit = dx < 0 or dy < 0
                    sp.put(n[0], n[1], ramp[1] if lit else ramp[0])
    return mine


def occlusion(sp: Sprite, front: set, back_part, col):
    """1px darker line on the back part where the front part covers it (depth)."""
    for (x, y) in front:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in front and sp.part.get(n) == back_part:
                sp.put(n[0], n[1], col)


def outline_all(sp: Sprite):
    """Final silhouette outline: dark ink-green below/right, softer above/left."""
    filled = set(sp.c)
    for (x, y) in list(filled):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in filled and 0 <= n[0] < S and 0 <= n[1] < S:
                sp.put(n[0], n[1], '#2A2A2E' if (dx > 0 or dy > 0) else '#3B3F3A')


def eye(sp: Sprite, x, y, state, size=2):
    """Open eyes: 2x3 ink with a white catchlight; closed: a soft arc; grumpy adds a brow."""
    if state in ('closed', 'grumpy-closed'):
        sp.put(x - 1, y + 1, INK); sp.put(x, y + 2, INK); sp.put(x + 1, y + 2, INK); sp.put(x + 2, y + 1, INK)
    else:
        for yy in range(y, y + 3):
            for xx in range(x, x + size):
                sp.put(xx, yy, INK)
        sp.put(x, y, WHITE)
        sp.put(x + size - 1, y + 2, '#3A3550')
    if state.startswith('grumpy'):
        sp.put(x - 1, y - 2, INK); sp.put(x, y - 1, INK); sp.put(x + 1, y - 1, INK)


def sprout(sp: Sprite, x, y, stage):
    """Growth on top of the head: two leaves -> leaves + bud -> leaves + bloom."""
    stem_h = 2 if stage == 1 else 5 if stage == 2 else 6
    for i in range(stem_h):
        sp.put(x, y - i, LEAF[2] if i % 2 else LEAF[3])
    top = y - stem_h
    # leaves
    for (dx, dy, c) in ((-1, 0, LEAF[4]), (-2, 0, LEAF[3]), (-3, -1, LEAF[3]), (-2, -1, LEAF[5]),
                        (1, 1, LEAF[3]), (2, 1, LEAF[2]), (3, 0, LEAF[2]), (2, 0, LEAF[4])):
        sp.put(x + dx, y - 1 + dy - (0 if stage == 1 else 1), c)
    if stage == 2:
        for (dx, dy, c) in ((0, 0, BUD[3]), (-1, 0, BUD[4]), (1, 0, BUD[2]), (0, -1, BUD[4]),
                            (0, 1, BUD[2]), (-1, -1, BUD[5]), (1, -1, BUD[3])):
            sp.put(x + dx, top + dy - 1, c)
        sp.put(x - 1, top + 1, LEAF[3]); sp.put(x + 1, top + 1, LEAF[2])
    if stage == 3:
        for (dx, dy) in ((0, -2), (-2, 0), (2, 0), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1), (-2, -1), (2, -1), (-1, -2), (1, -2), (-2, 1), (2, 1), (-1, 2), (1, 2)):
            lit = dx + dy < 0
            sp.put(x + dx, top + dy - 1, PETAL[4] if lit else PETAL[3] if dx + dy == 0 else PETAL[2])
        sp.put(x - 1, top - 3, PETAL[5]); sp.put(x - 3, top - 1, PETAL[1]); sp.put(x + 3, top - 1, PETAL[1]); sp.put(x, top + 2, PETAL[1])
        sp.put(x, top - 1, GOLD[4]); sp.put(x - 1, top - 1, GOLD[5]); sp.put(x + 1, top - 1, GOLD[3]); sp.put(x, top, GOLD[3])


# ---- species ---------------------------------------------------------------
def mossling(stage, state):
    sp = Sprite()
    # back foot, body (squashy mochi), front foot
    shade(sp, 11.5, 28.2, 3.2, 1.9, LEAF_B, 'foot', outline=False)
    body = shade(sp, 16, 21.5, 11.2 + (stage - 1) * 0.4, 7.6, LEAF, 'body', flat=0.25)
    for (fx) in (21.5,):
        f = shade(sp, fx, 28.4, 3.4, 1.9, LEAF, 'foot2', outline=False)
    occlusion(sp, f, 'body', LEAF[1])
    # moss speckles on the lit shoulder
    for (x, y) in ((9, 17), (12, 15), (8, 20), (14, 16), (11, 18)):
        sp.put(x, y, LEAF[5] if (x + y) % 2 else LEAF[4])
    # mushroom cap hat-of-nature, tilted on the head
    cap_pts = {(x, y) for (x, y, u, v) in ell_pts(15.5, 11.2, 9.2, 5.6) if v < 0.42}
    for (x, y) in cap_pts:
        u, v = (x + 0.5 - 15.5) / 9.2, (y + 0.5 - 11.2) / 5.6
        nz = math.sqrt(max(0.0, 1 - u * u - v * v)) + 0.1
        d = (u * LIGHT[0] + v * LIGHT[1] + nz * LIGHT[2]) / math.sqrt(u * u + v * v + nz * nz)
        sp.put(x, y, CAP[band(d, x, y)], 'cap')
    # gill band under the brim (cream), shadowed toward the right
    brim_y = max(y for (_, y) in cap_pts) + 1
    for x in range(8, 24):
        if (x, brim_y - 1) in cap_pts:
            sp.put(x, brim_y, '#F3E3C2' if x < 15 else '#D9C29A' if x < 20 else '#B8A27C', 'gill')
    for x in range(10, 22, 2):
        sp.put(x, brim_y, '#C9B08A')
    # three soft cream spots (shaded), not a strawberry pattern
    blob3 = [(1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (1, 2), (2, 2)]
    blob2 = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for (sx, sy, shape) in ((10, 8, blob3), (16, 6, blob3), (20, 10, blob2), (13, 12, blob2)):
        for (dx, dy) in shape:
            if (sx + dx, sy + dy) in cap_pts:
                sp.put(sx + dx, sy + dy, '#FFF4E0' if dx + dy < 2 else '#E8D2B8')
    for (x, y) in list(cap_pts):
        for dx, dy in ((1, 0), (-1, 0), (0, -1)):
            n = (x + dx, y + dy)
            if n not in cap_pts and n not in sp.c:
                sp.put(n[0], n[1], CAP[0] if dx > 0 else CAP[1])
    occlusion(sp, cap_pts | {(x, brim_y) for x in range(8, 24)}, 'body', LEAF[1])
    # face (REST identity: soft, half-lidded)
    ey = 20
    eye(sp, 17, ey, state)
    eye(sp, 23, ey, state)
    sp.put(16, ey + 4, BLUSH); sp.put(26, ey + 4, BLUSH); sp.put(25, ey + 4, BLUSH)
    mouth = '#3A2A2A'
    sp.put(20, ey + 4, mouth); sp.put(21, ey + 5, mouth); sp.put(22, ey + 4, mouth)
    if state.startswith('grumpy'):
        sp.put(21, ey + 4, mouth); sp.put(20, ey + 5, mouth); sp.put(22, ey + 5, mouth); sp.put(21, ey + 5, LEAF[3])
    sprout(sp, 9, 7, stage)
    outline_all(sp)
    return sp, (19, 6), (17, 20)  # hat anchor (center x, bottom y), eye line (x, y)


def roamling(stage, state):
    sp = Sprite()
    # vine tail (curl) behind
    for i, (x, y) in enumerate(((5, 22), (4, 21), (3, 20), (3, 19), (4, 18), (5, 18), (6, 19), (6, 20), (5, 20))):
        sp.put(x, y, LEAF[2] if i % 3 else LEAF[3])
    sp.put(2, 21, LEAF[4]); sp.put(2, 22, LEAF[3]); sp.put(7, 23, LEAF[2]); sp.put(6, 23, LEAF[2])
    # back legs (darker), body, front legs
    for lx in (10, 21):
        for y in range(23, 29):
            sp.put(lx, y, LEAF_B[2]); sp.put(lx + 1, y, LEAF_B[1])
        sp.put(lx - 1, 28, LEAF_B[2])
    body = shade(sp, 15.5, 21.5, 8.4, 5.4, LEAF, 'body', flat=0.1)
    for lx in (13, 23):
        for y in range(24, 29):
            sp.put(lx, y, LEAF[3] if y < 26 else LEAF[2]); sp.put(lx + 1, y, LEAF[2])
        sp.put(lx + 2, 28, LEAF[2]); sp.put(lx, 28, LEAF[1])
    # head
    ears = set()
    ears |= shade(sp, 15.6, 9.2, 2.6, 6.2, LEAF_B, 'ear', rot=-0.45, flat=0.2)
    ears |= shade(sp, 24.8, 8.6, 2.6, 6.4, LEAF, 'ear2', rot=0.42, flat=0.2)
    for i in range(5):  # leaf veins
        sp.put(round(16.7 - i * 0.45), 12 - i, LEAF_B[1])
        sp.put(round(23.8 + i * 0.42), 12 - i, LEAF[2])
    head = shade(sp, 21, 16.4, 6.6, 5.6, LEAF, 'head', flat=0.15)
    occlusion(sp, head, 'body', LEAF[1])
    occlusion(sp, head, 'ear', LEAF_B[0])
    occlusion(sp, head, 'ear2', LEAF[1])
    # snout/muzzle lighter patch + nose
    for (x, y) in ((24, 18), (25, 18), (26, 18), (25, 19), (24, 19), (26, 17)):
        sp.put(x, y, LEAF[4])
    sp.put(27, 18, '#2B2A2E'); sp.put(27, 17, '#4A4450')
    ey = 14
    eye(sp, 18, ey, state)
    eye(sp, 22, ey, state)
    sp.put(17, ey + 4, BLUSH); sp.put(22, ey + 4, BLUSH)
    sp.put(23, ey + 6, '#3A2A2A'); sp.put(24, ey + 6, '#3A2A2A')
    if state.startswith('grumpy'):
        sp.put(23, ey + 6, '#3A2A2A'); sp.put(22, ey + 7, '#3A2A2A'); sp.put(25, ey + 7, '#3A2A2A')
    sprout(sp, 12, 12, stage)
    outline_all(sp)
    return sp, (21, 11), (19, 14)


def pebbling(stage, state):
    sp = Sprite()
    # reading lamp growing from the back
    stem = [(6, 20), (5, 19), (4, 18), (4, 17), (4, 16), (4, 15), (4, 14), (5, 13), (5, 12), (6, 11), (7, 10)]
    for i, (x, y) in enumerate(stem):
        sp.put(x, y, LEAF[3] if i % 2 else LEAF[2]); sp.put(x + 1, y, LEAF[1])
    shade_cone(sp)
    # feet
    shade(sp, 11, 28.6, 3.1, 1.7, STONE, 'foot', outline=False)
    shade(sp, 22, 28.6, 3.1, 1.7, STONE, 'foot2', outline=False)
    # rounded stone body: superellipse shading
    body = set()
    cx, cy, rx, ry = 16.5, 20, 11, 8.6
    for y in range(S):
        for x in range(S):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if abs(u) ** 3.2 + abs(v) ** 3.2 <= 1:
                body.add((x, y))
                nz = math.sqrt(max(0.0, 1 - min(1, u * u * 0.8 + v * v * 0.8))) + 0.15
                d = (u * LIGHT[0] + v * LIGHT[1] + nz * LIGHT[2]) / math.sqrt(u * u + v * v + nz * nz)
                col = STONE[band(d, x, y)]
                if u > 0.5 and v > 0.5:
                    col = STONE[2]
                sp.put(x, y, col, 'body')
    # stone speckles and a crack
    for (x, y, c) in ((10, 22, STONE[2]), (13, 25, STONE[2]), (24, 16, STONE[4]), (8, 18, STONE[4]), (26, 23, STONE[1]), (19, 26, STONE[2])):
        sp.put(x, y, c)
    sp.put(25, 19, STONE[1]); sp.put(26, 20, STONE[1]); sp.put(26, 21, STONE[1])
    # moss cap on top (where growth sprouts)
    moss = set()
    for (x, y, u, v) in ell_pts(16.5, 12.6, 8.5, 2.8):
        if v < 0.5 and (x, y) in body | {(x, y + 1)}:
            t = -u * 0.5 - v
            sp.put(x, y, MOSS[4] if t > 0.4 else MOSS[3] if t > -0.3 else MOSS[2], 'moss')
            moss.add((x, y))
    for x in range(9, 25, 3):
        sp.put(x, 14 + (x % 2), MOSS[2])
    # round glasses + eyes
    ey = 18
    for gx in (13, 21):
        for (dx, dy) in ((0, -1), (1, -1), (2, -1), (-1, 0), (3, 0), (-1, 1), (3, 1), (-1, 2), (3, 2), (0, 3), (1, 3), (2, 3)):
            sp.put(gx + dx, ey + dy, GOLD[1])
        sp.put(gx, ey - 1, GOLD[4])
    sp.put(17, ey, GOLD[1]); sp.put(18, ey, GOLD[1]); sp.put(19, ey, GOLD[1])
    for gx in (13, 21):
        for (dx, dy) in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)):
            sp.put(gx + dx, ey + dy, '#DDE9EC' if (dx + dy) < 2 else '#B9C8CF')
        if state in ('closed', 'grumpy-closed'):
            sp.put(gx, ey + 1, INK); sp.put(gx + 1, ey + 2, INK); sp.put(gx + 2, ey + 1, INK)
        else:
            sp.put(gx + 1, ey + 1, INK); sp.put(gx + 1, ey + 2, INK); sp.put(gx + 2, ey + 1, INK); sp.put(gx + 2, ey + 2, '#3A3550')
        if state.startswith('grumpy'):
            sp.put(gx, ey - 2, INK); sp.put(gx + 1, ey - 2, INK); sp.put(gx + 2, ey - 3 if gx < 20 else ey - 2, INK)
    sp.put(12, ey + 5, BLUSH); sp.put(25, ey + 5, BLUSH)
    sp.put(18, ey + 6, '#2E2B33'); sp.put(19, ey + 6, '#2E2B33')
    if state.startswith('grumpy'):
        sp.put(17, ey + 7, '#2E2B33'); sp.put(20, ey + 7, '#2E2B33')
    sprout(sp, 22, 11, stage)
    outline_all(sp)
    return sp, (16, 11), (13, 18)


def shade_cone(sp: Sprite):
    """Little glowing reading lamp on the stem."""
    # small bell-shaped lamp hanging forward from the stem tip
    rows = [(8, 9, 2), (7, 9, 4), (6, 8, 6)]  # (y, x0, width)
    for (y, x0, w) in rows:
        for x in range(x0, x0 + w):
            sp.put(x, y, GOLD[4] if x < x0 + w // 2 else GOLD[2])
    for x in range(8, 16):
        sp.put(x, 9, GOLD[1])
    sp.put(10, 10, '#FFF3BF'); sp.put(11, 10, '#FFF3BF'); sp.put(12, 10, '#FFE58A'); sp.put(11, 11, '#FFF7D6')
    sp.put(9, 6, GOLD[5])



# ---- visitors + Doomscroll Dave --------------------------------------------
TERRA = ['#4A1E16', '#7A3420', '#A84E2E', '#CF7446', '#EAA06B', '#FBD3A6']
CREAMR = ['#5B4630', '#8C7354', '#B89E78', '#DCC6A0', '#F1E3C4', '#FFF7E6']
NIGHTR = ['#121427', '#1F2442', '#2F3760', '#45507F', '#6A77A6', '#A9B4D6']
BURR = ['#3D2A12', '#6A4A1E', '#9A7230', '#C79B45', '#E6C474', '#FFF0B8']
WEED = ['#1E2228', '#353C45', '#525B63', '#737D80', '#9AA39F', '#CDD3C8']


def feet(sp, xs, y, ramp):
    for x in xs:
        shade(sp, x, y, 2.6, 1.6, ramp, 'feet', outline=False)


def face(sp, x1, x2, y, state, mouth=True):
    eye(sp, x1, y, state)
    eye(sp, x2, y, state)
    sp.put(x1 - 1, y + 4, BLUSH); sp.put(x2 + 2, y + 4, BLUSH)
    if mouth:
        m = (x1 + x2) // 2 + 1
        sp.put(m, y + 4, '#3A2A2A'); sp.put(m + 1, y + 4, '#3A2A2A')


def v_dozebud(state):
    sp = Sprite()
    for (lx, rot) in ((10, -0.9), (22, 0.9)):
        shade(sp, lx, 27.5, 4.2, 1.8, LEAF, 'leaf', rot=rot * 0.3, outline=False)
    shade(sp, 16, 21, 9, 7.6, CREAMR, 'body', flat=0.2)
    bud = shade(sp, 16, 12.5, 6.2, 5.2, TERRA, 'bud', flat=0.1)
    for y in range(4, 8):
        sp.put(16, y, TERRA[3] if y > 5 else TERRA[4]); sp.put(17, y, TERRA[2])
    for y in (9, 11, 13):  # petal seams
        sp.put(13, y, TERRA[1]); sp.put(19, y + 1, TERRA[1])
    occlusion(sp, bud, 'body', CREAMR[1])
    face(sp, 12, 19, 19, 'closed' if state == 'open' else state)  # always drowsy
    outline_all(sp)
    return sp, (16, 7), (12, 19)


def v_mosspuff(state):
    sp = Sprite()
    for (x, y, r) in ((9, 17, 5.2), (16, 11.5, 5.6), (23, 16, 5.2), (24.5, 23, 4.6), (8, 23.5, 4.6), (16, 26, 4.4)):
        shade(sp, x, y, r, r, MOSS, 'puff')
    body = shade(sp, 16, 20, 8.2, 6.4, LEAF, 'body', flat=0.2)
    occlusion(sp, body, 'puff', MOSS[1])
    for (x, y) in ((13, 10), (21, 14), (7, 16), (25, 21)):
        sp.put(x, y, MOSS[5])
    face(sp, 12, 19, 18, state)
    outline_all(sp)
    return sp, (16, 7), (12, 18)


def v_lullapine(state):
    sp = Sprite()
    feet(sp, (12, 20), 28.6, CREAMR)
    cone = set()
    for row in range(16):
        half = 2 + row * 0.62
        cy = 9 + row
        for x in range(int(16 - half), int(16 + half) + 1):
            scale_row = (row // 3) % 2
            t = (16 - x) / max(1, half) * 0.5 + 0.3 - row * 0.02
            ramp = BURR if scale_row else ['#3A2414', '#5E3A1E', '#83552C', '#A8723C', '#C99257', '#E8BD86']
            sp.put(x, cy, ramp[4] if t > 0.55 else ramp[3] if t > 0.15 else ramp[2], 'cone')
            cone.add((x, cy))
        if row % 3 == 2:
            for x in range(int(16 - half), int(16 + half) + 1, 2):
                sp.put(x, cy, '#4A2E18')
    # night cap with pompom
    for row in range(6):
        for x in range(13 - row // 2, 21 + row // 3):
            sp.put(x, 3 + row, NIGHTR[3] if x < 16 else NIGHTR[2])
    for x in range(11, 23):
        sp.put(x, 9, CREAMR[4] if x < 17 else CREAMR[3])
    shade(sp, 23, 4, 2.2, 2.2, CREAMR, 'pom', outline=False)
    face(sp, 12, 18, 16, state)
    outline_all(sp)
    return sp, (16, 4), (12, 16)


def v_trailhop(state):
    sp = Sprite()
    shade(sp, 9, 26.5, 5, 2.8, LEAF_B, 'leg')
    shade(sp, 24, 26.5, 5, 2.8, LEAF_B, 'leg2')
    body = shade(sp, 16.5, 21, 10, 6.6, LEAF, 'body', flat=0.2)
    for (ex) in (10.5, 22.5):
        shade(sp, ex, 14.8, 3.8, 3.6, LEAF, 'eyebump')
    # belly
    for (x, y, u, v) in ell_pts(16.5, 23.5, 6, 3):
        sp.put(x, y, CREAMR[4] if v < 0 else CREAMR[3])
    for y in range(7, 13):
        sp.put(16, y, LEAF[3]); sp.put(17, y, LEAF[2])
    for (dx, dy, c) in ((-1, 0, LEAF[4]), (-2, 0, LEAF[3]), (-3, -1, LEAF[4]), (1, 1, LEAF[3]), (2, 1, LEAF[2]), (3, 0, LEAF[2])):
        sp.put(16 + dx, 8 + dy, c)
    eye(sp, 10, 14, state)
    eye(sp, 22, 14, state)
    for x in range(13, 21):
        sp.put(x, 21, '#2B3B2A' if x not in (13, 20) else LEAF[1])
    sp.put(9, 19, BLUSH); sp.put(24, 19, BLUSH)
    outline_all(sp)
    return sp, (16, 8), (10, 14)


def v_burrbound(state):
    sp = Sprite()
    feet(sp, (11, 22), 28.5, ['#2E2214', '#4E3A22', '#6E5434', '#8E7048', '#AE8E62', '#CFB088'])
    body = shade(sp, 16.5, 19, 10, 9.4, BURR, 'body', flat=0.1)
    for a in range(0, 360, 30):  # spines
        r1, r2 = 9.6, 12.4
        for k in range(3):
            rr = r1 + (r2 - r1) * k / 2
            x = int(16.5 + math.cos(math.radians(a)) * rr)
            y = int(19 + math.sin(math.radians(a)) * rr * 0.95)
            if y < 27:
                sp.put(x, y, BURR[1] if k == 2 else BURR[2])
    for (x, y) in ((11, 14), (20, 12), (23, 20), (10, 22), (16, 25)):
        sp.put(x, y, BURR[1]); sp.put(x + 1, y, BURR[4])
    face(sp, 12, 19, 17, state)
    outline_all(sp)
    return sp, (16, 7), (12, 17)


def v_skyfern(state):
    sp = Sprite()
    feet(sp, (13, 19), 28.8, LEAF_B)
    for y in range(10, 27):
        sp.put(15, y, LEAF[2]); sp.put(16, y, LEAF[3])
    for i, y in enumerate(range(11, 22, 3)):  # fern fronds
        for k in range(5 - i // 2):
            sp.put(14 - k, y - k // 2, LEAF[4] if k % 2 else LEAF[3])
            sp.put(17 + k, y - k // 2, LEAF[3] if k % 2 else LEAF[2])
    shade(sp, 15.5, 23, 6, 5.4, LEAF, 'body', flat=0.2)
    face(sp, 12, 17, 21, state, mouth=False)
    sp.put(15, 25, '#3A2A2A'); sp.put(16, 25, '#3A2A2A')
    # kite on a string
    for y in range(6, 17):
        sp.put(25, y, '#5A4632')
    kite = [(26, 1), (25, 2), (26, 2), (27, 2), (24, 3), (25, 3), (26, 3), (27, 3), (28, 3), (25, 4), (26, 4), (27, 4), (26, 5)]
    for (x, y) in kite:
        sp.put(x, y, GOLD[4] if x <= 26 and y <= 3 else TERRA[3])
    sp.put(26, 6, TERRA[2]); sp.put(27, 7, GOLD[3])
    outline_all(sp)
    return sp, (16, 11), (12, 21)


def v_inkling(state):
    sp = Sprite()
    feet(sp, (12, 21), 28.6, NIGHTR)
    pts = set()
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - 16, y + 0.5 - 21
            if dy < 0:
                ok = abs(dx) <= 8.5 * (1 + dy / 14) and dy > -14
            else:
                ok = dx * dx / 72 + dy * dy / 49 <= 1
            if ok:
                pts.add((x, y))
                u, v = dx / 8.5, dy / 7.5
                nz = math.sqrt(max(0.0, 1 - min(1, u * u * 0.9 + v * v * 0.6))) + 0.1
                d = (u * LIGHT[0] + v * LIGHT[1] + nz * LIGHT[2]) / math.sqrt(u * u + v * v + nz * nz)
                sp.put(x, y, NIGHTR[band(d, x, y)], 'body')
    sp.put(12, 13, NIGHTR[5]); sp.put(12, 14, NIGHTR[5]); sp.put(13, 12, NIGHTR[4])
    for y in range(4, 8):
        sp.put(16, y, LEAF[3])
    sp.put(17, 5, LEAF[4]); sp.put(18, 5, LEAF[3]); sp.put(19, 6, LEAF[2])
    eye(sp, 12, 20, state)
    eye(sp, 19, 20, state)
    for (x, y) in ((12, 20), (13, 21), (19, 20), (20, 21)):
        if sp.c.get((x, y)) == INK:
            sp.put(x, y, '#F2F0E6')
    sp.put(16, 25, '#0B0C18'); sp.put(17, 25, '#0B0C18')
    outline_all(sp)
    return sp, (16, 9), (12, 20)


def v_pagemoth(state):
    sp = Sprite()
    for (wx, rot) in ((8, 0.25), (24, -0.25)):
        w = shade(sp, wx, 16, 7, 9.4, CREAMR, 'wing', rot=rot, flat=0.3)
        for y in range(10, 24, 3):  # text lines
            for x in range(wx - 4, wx + 4):
                if (x, y) in w and (x + y) % 5:
                    sp.put(x, y, CREAMR[2])
    body = shade(sp, 16, 20, 4.2, 8.6, BURR, 'body', flat=0.2)
    for y in (16, 19, 22, 25):
        for x in range(13, 20):
            if (x, y) in body:
                sp.put(x, y, BURR[2])
    for (ax, dx) in ((13, -1), (19, 1)):
        for i in range(6):
            sp.put(ax + (dx * i) // 3, 11 - i, '#3A2A1E')
        sp.put(ax + dx * 2, 5, LEAF[3]); sp.put(ax + dx * 2 + dx, 5, LEAF[4])
    eye(sp, 14, 15, state, size=1)
    eye(sp, 18, 15, state, size=1)
    outline_all(sp)
    return sp, (16, 10), (13, 15)


def v_lanternroot(state):
    sp = Sprite()
    feet(sp, (10, 17), 28.8, ['#2E1E14', '#4E3424', '#6E4C34', '#8E6648', '#AE8462', '#CFA886'])
    body = shade(sp, 13, 21.5, 7.4, 7, ['#3A2416', '#5E3C24', '#835834', '#A87648', '#C99A66', '#E8C394'], 'body', flat=0.2)
    for (x, y) in ((9, 19), (11, 24), (15, 26), (16, 18)):
        sp.put(x, y, '#5E3C24')
    for (dx, dy, c) in ((0, 0, LEAF[3]), (-1, -1, LEAF[4]), (-2, -2, LEAF[4]), (1, -1, LEAF[2]), (2, -2, LEAF[3]), (0, -1, LEAF[2])):
        sp.put(12 + dx, 14 + dy, c)
    eye(sp, 9, 19, state)
    eye(sp, 15, 19, state)
    sp.put(12, 24, '#3A2A2A'); sp.put(13, 24, '#3A2A2A')
    # arm holding a lantern on a pole
    for x in range(19, 23):
        sp.put(x, 22, '#835834')
    for y in range(11, 18):
        sp.put(25, y, '#3A3030')
    for y in range(17, 27):
        for x in range(22, 29):
            edge = x in (22, 28) or y in (17, 26)
            glow = GOLD[5] if (x, y) in ((24, 20), (25, 20), (24, 21)) else GOLD[4] if x < 25 else GOLD[3]
            sp.put(x, y, '#3A3030' if edge else glow)
    for x in range(21, 30):
        sp.put(x, 16, '#5A4A44')
    for (x, y) in ((29, 13), (20, 14), (30, 21)):
        sp.put(x, y, GOLD[5])
    outline_all(sp)
    return sp, (13, 13), (9, 19)


def v_dave(state):
    sp = Sprite()
    # thorny weed silhouette
    blob = shade(sp, 16.5, 19.5, 9.4, 8.2, WEED, 'body', flat=0.15)
    # thorny leaves radiating outward (drawn after the body so they read on top)
    for i, a in enumerate(range(-160, 200, 26)):
        ang = math.radians(a)
        length = 6 + (i % 3) * 2
        for k in range(length):
            r = 8.2 + k
            x = round(16.5 + math.cos(ang) * r * 1.08)
            y = round(19.5 + math.sin(ang) * r * 0.92)
            if y > 27:
                break
            width_col = WEED[3] if k < length * 0.4 else WEED[2] if k < length * 0.8 else WEED[1]
            sp.put(x, y, width_col)
            if k < length * 0.5:
                sp.put(x + (1 if math.cos(ang) < 0 else -1), y, WEED[2])
        tx = round(16.5 + math.cos(ang) * (8.2 + length) * 1.08)
        ty = round(19.5 + math.sin(ang) * (8.2 + length) * 0.92)
        if ty <= 27:
            sp.put(tx, ty, '#7C3B3B')  # little red thorn tips
    # phone-screen face
    for y in range(13, 25):
        for x in range(11, 23):
            sp.put(x, y, '#141821')
    for y in range(14, 24):
        for x in range(12, 22):
            sp.put(x, y, '#5FC2DA' if (x - 12) + (y - 14) < 9 else '#3FA0BC')
    sp.put(12, 14, '#BFF1FA'); sp.put(13, 14, '#BFF1FA'); sp.put(12, 15, '#BFF1FA')
    if state in ('closed', 'grumpy-closed'):
        for x in (14, 15, 18, 19):
            sp.put(x, 18, '#141821')
    else:
        for (x, y) in ((14, 17), (15, 17), (14, 18), (15, 18), (18, 17), (19, 17), (18, 18), (19, 18)):
            sp.put(x, y, '#141821')
    for x in range(15, 19):
        sp.put(x, 20, '#141821')
    sp.put(14, 21, '#141821'); sp.put(19, 21, '#141821')  # frown (corners down)
    sp.put(13, 16, '#141821'); sp.put(14, 16, '#141821'); sp.put(19, 16, '#141821'); sp.put(20, 16, '#141821')  # sulky brows
    # notification dot
    sp.put(22, 12, '#E2574C'); sp.put(23, 12, '#E2574C'); sp.put(22, 11, '#F08A80')
    outline_all(sp)
    return sp, (16, 6), (14, 17)


VISITORS = {'dozebud': v_dozebud, 'mosspuff': v_mosspuff, 'lullapine': v_lullapine,
            'trailhop': v_trailhop, 'burrbound': v_burrbound, 'skyfern': v_skyfern,
            'inkling': v_inkling, 'pagemoth': v_pagemoth, 'lanternroot': v_lanternroot,
            'dave': v_dave}


SPECIES = {'BLOB': mossling, 'RAT': roamling, 'CUBE': pebbling}
STATES = ['open', 'closed', 'grumpy', 'grumpy-closed']


# ---- hats (drawn once, centred on the head anchor) -------------------------
def hat_cap():
    sp = Sprite()
    for (x, y, u, v) in ell_pts(8, 5, 6.5, 4.2):
        if v < 0.35:
            t = -u * 0.5 - v
            sp.put(x, y, '#9DB8DE' if t > 0.6 else '#6F92C4' if t > 0 else '#4D6FA0')
    for x in range(8, 17):
        sp.put(x, 6, '#3F5C8A'); sp.put(x, 7, '#2D4468')
    sp.put(8, 1, '#E8EEF8')
    return sp, 7


def hat_top():
    sp = Sprite()
    for y in range(0, 8):
        for x in range(4, 13):
            sp.put(x, y, '#4B4550' if x < 6 else '#2F2B33' if x < 11 else '#1E1B22')
    for x in range(4, 13):
        sp.put(x, 6, '#B44A3E'); sp.put(x, 5, '#8E3A33')
    for x in range(1, 16):
        sp.put(x, 8, '#2F2B33'); sp.put(x, 9, '#1E1B22')
    sp.put(5, 1, '#6E6875')
    return sp, 9


def hat_crown():
    sp = Sprite()
    for x in range(2, 15):
        for y in range(4, 8):
            sp.put(x, y, '#F2CF5B' if y == 4 else '#D9AE3A' if x < 10 else '#B98E2A')
    for (px, h) in ((2, 3), (5, 4), (8, 5), (11, 4), (14, 3)):
        for i in range(h):
            sp.put(px, 4 - i, '#F2CF5B' if i == h - 1 else '#D9AE3A')
    sp.put(8, 6, '#C2453B'); sp.put(5, 6, '#4FA3C8'); sp.put(11, 6, '#4FA3C8')
    sp.put(8, 0, '#FFF3BF')
    return sp, 7


HATS = {'CAP': hat_cap, 'TOP HAT': hat_top, 'CROWN': hat_crown}


def encode(sp: Sprite, w, h, palette: list):
    rows = []
    for y in range(h):
        row = ''
        for x in range(w):
            col = sp.c.get((x, y))
            if col is None:
                row += '.'
            else:
                if col not in palette:
                    palette.append(col)
                row += IDX[palette.index(col)]
        rows.append(row)
    return rows


IDX = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!$%&*+-/:;<=>?@^_~' + ''.join(chr(c) for c in range(0xC0, 0x100))


def main():
    palette: list = []
    out = {}
    sheet = Image.new('RGBA', (S * 12 + 13, S * 3 + 4 + 16), (226, 234, 214, 255))
    for si, (key, fn) in enumerate(SPECIES.items()):
        out[key] = {}
        for stage in (1, 2, 3):
            entry = {}
            for state in STATES:
                sp, hat_anchor, eyes = fn(stage, state)
                entry[state] = encode(sp, S, S, palette)
                if True:
                    col = (stage - 1) * 4 + STATES.index(state)
                    for (x, y), c in sp.c.items():
                        sheet.putpixel((1 + col * (S + 1) + x, 1 + si * (S + 1) + y), tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
            entry['hat'] = list(hat_anchor)
            entry['eyes'] = list(eyes)
            out[key][stage] = entry
    vis = {}
    vsheet = Image.new('RGBA', ((S + 1) * 10 + 1, (S + 1) * 2 + 1), (226, 234, 214, 255))
    for vi, (key, fn) in enumerate(VISITORS.items()):
        entry = {}
        for si, state in enumerate(('open', 'closed')):
            sp, hat_anchor, eyes = fn(state)
            entry[state] = encode(sp, S, S, palette)
            for (x, y), c in sp.c.items():
                vsheet.putpixel((1 + vi * (S + 1) + x, 1 + si * (S + 1) + y), tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
        entry['hat'] = list(hat_anchor)
        entry['eyes'] = list(eyes)
        vis[key] = entry
    vsheet.resize((vsheet.width * 6, vsheet.height * 6), Image.NEAREST).save('/tmp/visitors-preview.png')
    hats = {}
    for name, fn in HATS.items():
        sp, bottom = fn()
        hats[name] = {'rows': encode(sp, 17, bottom + 1, palette), 'bottom': bottom}
    if len(palette) > len(IDX):
        raise SystemExit(f'palette too large: {len(palette)}')
    import json
    ts = [
        '// Generated by scripts/art/pets.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const PET_INDEX = {json.dumps(IDX, ensure_ascii=False)};',
        f'export const petPalette: readonly string[] = {json.dumps(palette)};',
        'export type SpriteState = "open" | "closed" | "grumpy" | "grumpy-closed";',
        'export type PetSprite = Record<SpriteState, readonly string[]> & { hat: readonly number[]; eyes: readonly number[] };',
        f'export const petSprites: Record<"BLOB" | "RAT" | "CUBE", Record<1 | 2 | 3, PetSprite>> = {json.dumps(out, ensure_ascii=False)};',
        'export type VisitorSprite = { open: readonly string[]; closed: readonly string[]; hat: readonly number[]; eyes: readonly number[] };',
        f'export const visitorSprites: Record<string, VisitorSprite> = {json.dumps(vis, ensure_ascii=False)};',
        f'export const hatSprites: Record<string, {{ rows: readonly string[]; bottom: number }}> = {json.dumps(hats, ensure_ascii=False)};',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'pet-sprites.ts'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ts))
    sheet.resize((sheet.width * 6, sheet.height * 6), Image.NEAREST).save('/tmp/pets-preview.png')
    print('ok palette', len(palette))


if __name__ == '__main__':
    main()
