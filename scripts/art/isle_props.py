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
    """The ferry's boathouse on the landing, 76 x 88: a timber shed on stilts at the
    water's edge, a shingled roof, a wide door to the slipway and a lantern. Its walls
    stand a storey and a half (42 px) round a boat door 22 x 34 (verticality.md section 5:
    a door clearly taller than the people walking through it), with a window beside it."""
    w, h = 76, 88
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 37.5, 14, 36, 36, 78
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 3, 72, SLATE, seed=901, moss=JUNGLE)
    topdown_gable(cv, edge_y, 6, 69, apex_y, wall_top, WOOD, boards=True)
    detail.boards(cv, rect_set(6, wall_top, 64, wall_bottom - wall_top), WOOD, 2, wall_top, board=4, seed=902)
    dtop = wall_bottom - 34
    for y in range(dtop, wall_bottom):  # the wide door, open on the dark inside
        for x in range(24, 46):
            cv.set(x, y, WOOD[0] if x > 25 else WOOD[3])
    cv.hline(23, dtop - 1, 24, WOOD[4]); cv.hline(23, dtop - 2, 24, WOOD[1])  # its lintel
    for y in range(dtop + 4, wall_bottom - 2):  # the slipway's rails running in, and a hull in the dark
        cv.set(30, y, WOOD[1]); cv.set(40, y, WOOD[1])
    for (x, y) in oval(35, wall_bottom - 7, 6, 2.5):  # a dinghy's bow in the dark, on the slip
        cv.set(x, y, '#E8E2D2' if y < wall_bottom - 7 else '#9A9284' if x > 36 else '#B8B0A0')
    wx, wy = 55, wall_bottom - 28  # a window, lamplit
    for y in range(wy, wy + 14):
        for x in range(wx, wx + 11):
            c = GOLD[3] if y < wy + 5 else GOLD[2]
            if x in (wx, wx + 10) or y in (wy, wy + 13) or x == wx + 5 or y == wy + 6:
                c = WOOD[4] if x == wx or y == wy else WOOD[1]
            cv.set(x, y, c)
    cv.hline(wx - 1, wy + 14, 13, WOOD[4])  # its sill
    for sx in (8, 22, 48, 66):  # stilts
        for y in range(wall_bottom, h):
            cv.set(sx, y, WOOD[2]); cv.set(sx + 1, y, WOOD[1])
    cv.rect(49, dtop + 2, 4, 6, GOLD[4]); cv.set(50, dtop + 1, MATERIALS['iron'][2])
    detail.overhang_shadow(cv, 6, 70, wall_top, lambda x: 3, k=2, cap=1)
    return cv


def ferry() -> Canvas:
    """The little island ferry from the side, 90 x 40, bow to the left, for the
    side-on ferry journey (journey.py): a white wooden hull with a blue stripe, a cabin
    with round windows and a short funnel. Moored in a zone it is `ferry_moored`."""
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


def ferry_moored() -> Canvas:
    """The little island ferry moored at the pier, 92 x 46, bow to the left, in the same three-quarter view
    as the buildings (art-faults.md, rule 4): the planked deck seen from above inside a
    white gunwale, the hull's side below it with a blue stripe at the waterline, a cabin
    with a lit red roof and round windows in its front, a short funnel."""
    w, h = 92, 46
    cv = Canvas(w, h, pad=PAD)
    cy, sq = 24, 0.5  # the deck's centre line and how far its plan is foreshortened

    def half(x):  # the hull's half-width in plan: a fine bow, a full stern
        t = (x - 3) / 30
        return 14 * math.sqrt(max(0.0, min(1.0, t))) * (1 - max(0.0, (x - 84) / 20))

    deck, side = set(), set()
    for x in range(3, 89):
        hw = half(x) * sq
        if hw < 0.6:
            continue
        top, bot = int(cy - hw), int(cy + hw)
        for y in range(top, bot + 1):
            deck.add((x, y))
        for y in range(bot + 1, bot + 9 - int(max(0, 18 - x) * 0.3)):  # the side below its front edge
            side.add((x, y))
    for (x, y) in side:
        d = y - min(yy for (xx, yy) in side if xx == x)
        c = CREAM[3] if d < 2 else CREAM[2]
        if d in (4, 5):
            c = WTR[2]
        elif d >= 6:
            c = WTR[1] if x < 60 else WTR[0]
        if x > 70 and d < 4:
            c = CREAM[2] if d < 2 else CREAM[1]  # the stern turning out of the light
        cv.set(x, y, c)
    for (x, y) in deck:
        edge = (x, y - 1) not in deck or (x, y + 1) not in deck or (x - 1, y) not in deck or (x + 1, y) not in deck
        if edge:
            cv.set(x, y, CREAM[3] if y < cy else CREAM[2])  # the gunwale
        else:
            cv.set(x, y, WOOD[1] if (y - cy) % 3 == 0 else WOOD[3] if x < 64 else WOOD[2])
    # the cabin: roof (top face) and front face, the left end lit
    x0, x1, roof0, roof1, front1 = 40, 70, 9, 15, 23
    for y in range(roof0, front1):
        for x in range(x0, x1):
            if y < roof1:
                c = RED[4] if y == roof0 or x == x0 else RED[3] if x < x1 - 4 else RED[2]
            else:
                c = CREAM[3] if x < x0 + 3 else CREAM[2] if x < x1 - 2 else CREAM[1]
                if y == front1 - 1:
                    c = WOOD[1]
            cv.set(x, y, c)
    for wx in (46, 54, 62):
        for (x, y) in disc(wx, 19, 2.1):
            cv.set(x, y, '#9FC7E6' if (x - wx) + (y - 19) < 0 else WTR[1])
    for x in range(x0, x1):  # the roof's shadow on the deck behind
        if (x + 2, front1) in deck:
            r, g, b, a = cv.get(x + 2, front1)
            cv.set(x + 2, front1, (int(r * 0.7), int(g * 0.7), int(b * 0.78), a))
    # the funnel: a short cylinder on the roof, lit on its left, dark mouth on top
    for y in range(1, 11):
        for x in range(58, 65):
            cv.set(x, y, RED[4] if x < 60 else RED[3] if x < 63 else RED[2])
    for (x, y) in oval(61, 1.5, 3.4, 1.4):
        cv.set(x, y, MATERIALS['iron'][0] if y > 1 else MATERIALS['iron'][1])
    for x in range(58, 65):
        cv.set(x, 6, '#2E3A48')  # a band round it
    for px in range(10, 86, 9):  # rail posts along the near gunwale
        hw = half(px) * sq
        if hw > 2:
            cv.set(px, int(cy + hw) - 1, WOOD[0])
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


def pandanus() -> Canvas:
    """A screwpine of the sandy coasts, 44 x 58: a slim ringed trunk standing on a cone
    of stilt roots, a ragged crown of long strap leaves that droop at their tips."""
    w, h = 44, 58
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    bark = ['#4A3E34', '#6E6052', '#948470', '#B4A48C']
    for y in range(22, h - 10):  # the trunk, ringed with old leaf scars
        lean = int((y - 22) * 0.12)
        for dx in range(-2, 2):
            c = bark[2] if dx < 0 else bark[1]
            if y % 4 == 0:
                c = bark[0] if dx >= 0 else bark[1]
            cv.set(cx + dx + lean, y, c)
    base = cx + int((h - 32) * 0.12)
    for k in range(-3, 4):  # stilt roots splaying into the sand
        if k == 0:
            continue
        for t in range(12):
            x = base + int(k * t * 0.55)
            y = h - 12 + t
            cv.set(x, y, bark[3] if k < 0 else bark[1])
            if t % 4 == 0:
                cv.set(x, y, bark[0])
    order = sorted(range(14), key=lambda k: math.sin(2 * math.pi * k / 14))  # back to front
    for k in order:
        a = 2 * math.pi * k / 14 + 0.3
        lit = math.cos(a) < 0.2 and math.sin(a) < 0.6
        L = 15 + int(noise2(k, 3, 41) * 6)
        for t in range(L):
            x = cx + math.cos(a) * t
            y = 20 + math.sin(a) * t * 0.5 + (t * t) * 0.035  # drooping at the tip
            c = JUNGLE[4] if lit and t % 5 == 0 else JUNGLE[3] if lit else JUNGLE[2] if math.sin(a) > 0 else JUNGLE[1]
            cv.set(int(x), int(y), c)
            cv.set(int(x), int(y) + 1, JUNGLE[1] if not lit else JUNGLE[2])
    for (x, y) in disc(cx, 20, 2.4):
        cv.set(x, y, JUNGLE[1])
    for (fx, fy) in ((cx - 3, 24), (cx + 2, 25)):  # a hanging fruit, like a pine cone
        for (x, y) in disc(fx, fy, 2.2):
            cv.set(x, y, GOLD[3] if (x - fx) + (y - fy) < 0 else GOLD[2])
    return cv


def banana() -> Canvas:
    """A clump of wild banana, 40 x 48: two green stems and broad paddle leaves, one of
    them torn by the wind, a flower bud hanging purple under the crown."""
    w, h = 40, 48
    cv = Canvas(w, h, pad=PAD)
    for sx in (17, 23):  # the stems
        for y in range(24, h):
            cv.set(sx, y, JUNGLE[3] if sx == 17 else JUNGLE[2])
            cv.set(sx + 1, y, JUNGLE[2] if sx == 17 else JUNGLE[1])
    leaves = [(-1, 16, 17, -0.7), (1, 18, 18, -0.4), (-1, 26, 15, 0.45), (1, 27, 15, 0.6), (0, 16, 12, -1.2)]
    for k, (side, ly, L, tilt) in enumerate(leaves):
        x0 = 20
        for t in range(L):
            x = x0 + side * t if side else x0 + int(t * 0.2)
            y = ly + int(t * tilt * 0.6) - (0 if side else t)
            half = 5.2 * math.sin(math.pi * (t + 1) / (L + 1)) + 0.6
            for d in range(-int(half), int(half) + 1):
                if k == 2 and d > 0 and t % 3 == 0:
                    continue  # the torn leaf
                lit = d < 0
                cv.set(int(x), int(y + d), JUNGLE[4] if lit and abs(d) == int(half) else JUNGLE[3] if lit else JUNGLE[2])
            cv.set(int(x), int(y), JUNGLE[1])  # the midrib
    for (x, y) in oval(25, 34, 2, 3):  # the bud
        cv.set(x, y, '#6A3A5A' if x < 25 else '#4A2A44')
    return cv


def bird_of_paradise() -> Canvas:
    """A clump of bird-of-paradise, 30 x 26: stiff blue-green leaves and three flowers,
    orange crests on beaked purple bracts."""
    cv = Canvas(30, 26, pad=PAD)
    BG = ['#1E3A34', '#2E5A4E', '#4A7E6A', '#7AAE90']
    for k, (a, L) in enumerate(((-1.9, 14), (-1.3, 16), (-0.9, 12), (-2.3, 12), (-1.6, 18))):
        for t in range(L):
            x, y = 15 + math.cos(a) * t, 24 + math.sin(a) * t
            for d in (-1, 0, 1):
                cv.set(int(x) + d, int(y), BG[3] if d < 0 and t % 2 else BG[2] if d <= 0 else BG[1])
    for (fx, fy) in ((8, 8), (20, 5), (24, 12)):
        for t in range(6):  # the beak
            cv.set(fx + t, fy + 2, '#5A3A6A' if t < 4 else '#3A2A4A')
        for t in range(4):  # the crest
            cv.set(fx + 1 + t, fy + 1 - t // 2, RED[4] if t % 2 else GOLD[4])
            cv.set(fx + 1 + t, fy - t // 2, GOLD[3])
        cv.set(fx + 4, fy + 1, '#4A6AB8')  # a blue tongue
    return cv


def crab() -> Canvas:
    """A small red crab on the sand, 12 x 8, claws raised."""
    cv = Canvas(12, 8, pad=PAD)
    for (x, y) in oval(6, 4.5, 3.5, 2.4):
        cv.set(x, y, RED[4] if y < 4 else RED[3])
    for (x, y) in ((1, 2), (2, 1), (10, 2), (9, 1)):
        cv.set(x, y, RED[4])
    for (x, y) in ((1, 6), (2, 7), (10, 6), (9, 7), (3, 7), (8, 7)):
        cv.set(x, y, RED[2])
    cv.set(5, 3, '#1E1917'); cv.set(7, 3, '#1E1917')
    return cv


def rain_shelter() -> Canvas:
    """A walkers' rain shelter on the upland, 60 x 56: four timber posts under a
    shingled roof, a plank bench inside, a water jug on it. Modest and made here, not
    borrowed from anyone's temple or resort."""
    w, h = 60, 56
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y = 29.5, 6, 26
    topdown_roof(cv, ridge, apex_y, eave_y, 2, 58, SLATE, seed=911, moss=JUNGLE)
    for y in range(eave_y + 1, h - 4):  # the dark under the roof
        for x in range(6, 54):
            cv.set(x, y, WOOD[0] if y < eave_y + 5 else '#2A3A2A')
    for x in range(10, 50):  # the bench
        for y in range(h - 16, h - 12):
            cv.set(x, y, WOOD[4] if y == h - 16 else WOOD[3] if (x % 6) else WOOD[1])
        cv.set(x, h - 12, WOOD[1])
    for lx in (14, 44):
        for y in range(h - 12, h - 7):
            cv.set(lx, y, WOOD[1])
    for (x, y) in oval(38, h - 19, 2.5, 3):  # a water jug
        cv.set(x, y, '#B86A44' if x < 38 else '#8A4A30')
    for px_ in (4, 54):  # posts, lit on their left
        for y in range(eave_y - 2, h - 2):
            cv.set(px_, y, WOOD[3]); cv.set(px_ + 1, y, WOOD[2]); cv.set(px_ + 2, y, WOOD[1])
        cv.rect(px_ - 1, h - 3, 5, 2, STONE[2])  # its stone footing
    detail.overhang_shadow(cv, 6, 54, eave_y + 1, lambda x: 3, k=2, cap=1)
    return cv


def props() -> dict[str, Canvas]:
    return {
        'jungle_tree': jungle_tree(), 'tree_fern': tree_fern(), 'monstera': monstera(), 'hibiscus': hibiscus(),
        'boathouse': boathouse(), 'island_ferry': ferry_moored(), 'canoe': canoe(), 'black_rock': black_rock(True),
        'black_rock_small': black_rock(False), 'sea_turtle': sea_turtle(),
        'pandanus': pandanus(), 'banana': banana(), 'bird_of_paradise': bird_of_paradise(), 'crab': crab(),
        'rain_shelter': rain_shelter(),
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
