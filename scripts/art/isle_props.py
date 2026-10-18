"""Props for the Tidebloom Isles (world-atlas.md, "The connected world"; Matt, 18 Oct
19:07, following Codex's drawing): a dormant volcanic island off Driftwood Harbour,
its rainforest, the waterfall at the headwaters, the lagoon with its ferry landing and a
black-sand cove. Wet, deep green and warm; natural, not borrowed from anyone's culture.

Same rules as every prop (art-style.md): light from the upper left, canopies as a few
big leaf masses (garden_props.canopy), materials from materials.py. Run directly for a
contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import style  # noqa: E402
from garden_props import PAD, canopy, plane, rect_set, topdown_gable, topdown_roof  # noqa: E402
from materials import MATERIALS, WOOD, STONE, GOLD, RED, WTR, SLATE  # noqa: E402

# the rainforest's leaves: deeper and bluer than the valley's, with a wet bright top
JUNGLE = ['#14301F', '#1F4A2C', '#2E6638', '#4A8A44', '#7DB85A']
BASALT = MATERIALS['basalt']
CREAM = MATERIALS['cream']


def jungle_tree() -> Canvas:
    """A rainforest giant, 84 x 112: a broad, layered crown of leaf masses over a pale
    trunk with buttress roots flaring at its foot and a vine hanging down."""
    w, h = 84, 112
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2
    tw = 11
    tx = int(cx - tw / 2)
    bark = ['#4A3E34', '#6E6052', '#948470', '#B4A48C', '#CFC2A8']
    style.trunk(cv, tx, 40, h, tw, bark)
    for side in (-1, 1):  # buttress roots: thin flared fins out from the foot
        for k in range(12):
            y = h - 12 + k
            x0 = int(cx + side * (tw / 2 + k * k * 0.06))
            for x in range(min(int(cx), x0), max(int(cx), x0) + 1):
                if abs(x - cx) > tw / 2 - 1:
                    cv.set(x, y, bark[3] if side < 0 else bark[1])
    # an emergent's crown: wide and layered, broader than it is tall
    lobes = [(cx - 28, 30, 14), (cx + 28, 28, 14), (cx - 12, 20, 16), (cx + 12, 18, 16), (cx - 26, 44, 12),
             (cx + 26, 44, 12), (cx, 34, 17)]
    shape = canopy(cv, lobes, JUNGLE, seed=31, clumps=True)
    style.trunk(cv, tx, 52, h, tw, bark, shape)
    for t in range(40):  # a vine hanging from the crown on the lit side
        x = int(cx - 20 + math.sin(t / 6) * 2)
        y = 56 + t
        if y < h - 8 and not (tx <= x < tx + tw):
            cv.set(x, y, JUNGLE[3] if t % 4 else JUNGLE[4])
    return cv


def tree_fern() -> Canvas:
    """A tree fern, 44 x 58: a slim furred trunk and a crown of long arching fronds."""
    w, h = 44, 58
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(20, h):
        for dx in range(-2, 3):
            c = WOOD[2] if dx < 0 else WOOD[1]
            if (y + dx) % 3 == 0:
                c = WOOD[3] if dx < 0 else WOOD[0]
            cv.set(cx + dx, y, c)
    # fronds radiate all round the crown (seen from above and the side): a rosette of
    # long feathered leaves, the back ones darker, the lit front ones bright
    order = sorted(range(12), key=lambda k: math.sin(2 * math.pi * k / 12))  # back to front
    for k in order:
        a = 2 * math.pi * k / 12 + 0.2
        front = math.sin(a) > 0
        for t in range(20):
            x = cx + math.cos(a) * t
            y = 18 + math.sin(a) * t * 0.45 + (t * t) * 0.02
            lit = math.cos(a) < 0.3
            c = (JUNGLE[4] if t % 3 == 0 else JUNGLE[3]) if lit and front else JUNGLE[2] if front or lit else JUNGLE[1]
            cv.set(int(x), int(y), c)
            if 3 < t < 18:  # the leaflets either side of the midrib
                px, py = -math.sin(a), math.cos(a) * 0.45
                for side in (-1, 1):
                    cv.set(int(x + px * side * 1.6), int(y + py * side * 1.6 + 0.5), JUNGLE[2] if lit else JUNGLE[1])
    for (x, y) in disc(cx, 18, 2.2):
        cv.set(x, y, JUNGLE[1])
    return cv


def monstera() -> Canvas:
    """A clump of big split leaves, 40 x 30, glossy on their upper sides."""
    cv = Canvas(40, 30, pad=PAD)
    for (lx, ly, r, a) in ((12, 16, 9, -0.5), (27, 14, 10, 0.4), (20, 20, 9, 0.0), (8, 23, 7, -0.9), (32, 23, 7, 0.9)):
        leaf = oval(lx, ly, r, r * 0.7)
        for (x, y) in leaf:
            # the leaf's splits: thin gaps radiating from its middle
            ang = math.atan2(y - ly, x - lx)
            if int((ang + math.pi) * 5) % 4 == 0 and math.hypot(x - lx, y - ly) > r * 0.5:
                continue
            lit = (x - lx) + (y - ly) < 0
            cv.set(x, y, JUNGLE[4] if lit and (x + y) % 5 == 0 else JUNGLE[3] if lit else JUNGLE[2])
        cv.set(lx, ly, JUNGLE[1])
    return cv


def hibiscus() -> Canvas:
    """A flowering shrub, 34 x 28: a dark bush with big red flowers, gold at their hearts."""
    cv = Canvas(34, 28, pad=PAD)
    canopy(cv, [(10, 16, 9), (24, 15, 9), (17, 10, 9)], JUNGLE, seed=33)
    for (fx, fy) in ((8, 10), (20, 6), (26, 14), (13, 18), (22, 20)):
        for (x, y) in disc(fx, fy, 2.2):
            cv.set(x, y, RED[4] if (x - fx) + (y - fy) < 0 else RED[3])
        cv.set(fx, fy, GOLD[4])
    return cv


def boathouse() -> Canvas:
    """The ferry's boathouse on the landing, 76 x 70: a timber shed on stilts at the
    water's edge, a shingled roof, a wide door to the slipway and a lantern."""
    w, h = 76, 70
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 37.5, 14, 36, 36, 60
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 3, 72, SLATE, seed=901, moss=JUNGLE)
    topdown_gable(cv, edge_y, 6, 69, apex_y, wall_top, WOOD, boards=True)
    detail.boards(cv, rect_set(6, wall_top, 64, wall_bottom - wall_top), WOOD, 2, wall_top, board=4, seed=902)
    for y in range(44, wall_bottom):  # the wide door, open on the dark inside
        for x in range(24, 46):
            cv.set(x, y, WOOD[0] if x > 25 else WOOD[3])
    for sx in (8, 22, 48, 66):  # stilts
        for y in range(wall_bottom, h):
            cv.set(sx, y, WOOD[2]); cv.set(sx + 1, y, WOOD[1])
    cv.rect(52, 44, 4, 6, GOLD[4]); cv.set(53, 43, MATERIALS['iron'][2])
    detail.overhang_shadow(cv, 6, 70, wall_top, lambda x: 3, k=2, cap=1)
    return cv


def ferry() -> Canvas:
    """The little island ferry, 90 x 40, bow to the left: a white wooden hull with a
    blue stripe, a cabin with round windows and a short funnel."""
    w, h = 90, 40
    cv = Canvas(w, h, pad=PAD)
    hull = set()
    for y in range(22, 36):
        t = (y - 22) / 13
        x0 = int(4 + t * 10 + (1 - t) * 0)
        x1 = int(86 - t * 4)
        for x in range(x0, x1):
            hull.add((x, y))
    for (x, y) in hull:
        c = CREAM[3] if y < 28 else CREAM[2]
        if y in (28, 29):
            c = WTR[2]
        if y > 32:
            c = WTR[0]
        cv.set(x, y, c)
    for x in range(4, 86):
        cv.set(x, 22, WOOD[3])  # the rail
    for y in range(8, 22):  # the cabin
        for x in range(30, 72):
            c = CREAM[3] if x < 34 else CREAM[2]
            if y == 8:
                c = RED[3]
            cv.set(x, y, c)
    for wx in (38, 48, 58):
        for (x, y) in disc(wx, 14, 2.6):
            cv.set(x, y, '#9FC7E6' if (x - wx) + (y - 14) < 0 else WTR[1])
    for y in range(0, 8):  # the funnel
        for x in range(60, 66):
            cv.set(x, y, RED[3] if y > 2 else MATERIALS['iron'][1])
    return cv


def canoe() -> Canvas:
    """A dugout canoe drawn up on the sand, 52 x 14, a paddle across it."""
    cv = Canvas(52, 14, pad=PAD)
    for (x, y) in oval(26, 7, 25, 5):
        inside = ((x - 26) / 22) ** 2 + ((y - 6) / 3) ** 2 < 1
        cv.set(x, y, WOOD[1] if inside else WOOD[3] if y < 7 else WOOD[2])
    for t in range(30):
        cv.set(12 + t, 4 + t // 10, WOOD[4])
    for (x, y) in oval(43, 7, 4, 2):
        cv.set(x, y, WOOD[3])
    return cv


def black_rock(big: bool = True) -> Canvas:
    """A rounded boulder of dark volcanic rock (40 x 26, or 22 x 14), wet on its shadowed side."""
    w, h = (40, 26) if big else (22, 14)
    cv = Canvas(w, h, pad=PAD)
    pts = oval(w / 2, h / 2 + 1, w / 2 - 1, h / 2 - 1.4) | oval(w / 2 - 5, h / 2 + 2, w / 3, h / 2.6)
    pts = {(x, y) for (x, y) in pts if 0 <= x < w and 0 <= y < h}
    style.facet_stone(cv, pts, BASALT, seed=w + 7, outline=None)
    return cv


def sea_turtle() -> Canvas:
    """A green sea turtle resting on the sand, 30 x 22, head toward the sea."""
    cv = Canvas(30, 22, pad=PAD)
    shell = oval(15, 11, 10, 7)
    SHELL = ['#3A4A2A', '#5A6A38', '#7A8A4A', '#A0A868']
    for (fx, fy) in ((6, 6), (24, 6), (7, 17), (23, 17)):  # flippers
        for (x, y) in oval(fx, fy, 4, 2):
            cv.set(x, y, '#6E7E5A')
    for (x, y) in shell:
        cell = (int((x - 15) / 4) + int((y - 11) / 3)) % 2
        lit = (x - 15) + (y - 11) < 0
        cv.set(x, y, SHELL[3] if lit and cell else SHELL[2] if lit else SHELL[1] if cell else SHELL[0])
    for (x, y) in oval(15, 2, 3, 2.4):  # the head
        cv.set(x, y, '#8E9E6E' if x < 15 else '#6E7E5A')
    cv.set(14, 1, MATERIALS['iron'][0])
    return cv


def props() -> dict[str, Canvas]:
    return {
        'jungle_tree': jungle_tree(), 'tree_fern': tree_fern(), 'monstera': monstera(), 'hibiscus': hibiscus(),
        'boathouse': boathouse(), 'island_ferry': ferry(), 'canoe': canoe(), 'black_rock': black_rock(True),
        'black_rock_small': black_rock(False), 'sea_turtle': sea_turtle(),
    }


if __name__ == '__main__':
    from PIL import Image
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (214, 196, 150, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((width * 4, height * 4), Image.NEAREST)
    out.save(os.environ.get('ISLE_PREVIEW', '/tmp/isle-props.png'))
    print('ok', list(items))
