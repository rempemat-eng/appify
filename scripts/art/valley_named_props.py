"""The home valley's named things, wave 1 batch 2 (Claude B; docs/vision/regions/props.md
section 3 on PR #96; Claude A's to-b-2245): wayside shrines, beehives, a scarecrow, a hay
barn, a sheepfold, a shepherd's hut, the old oak and trail cairns.

Drawn to the same standard as the wayside kit (wayside_props.py, whose helpers and house
palette ramps this module shares): colours only from the house palette's ramps and
siblings, light from the upper left, footings on whole 8 px cells, sizes from the size
guide (adult 25 px), texture from parts in 2 to 4 px clusters, and every part with a
reason: what holds it up, what it is for, who keeps it.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval  # noqa: E402
import wayside_props as ws  # noqa: E402
from wayside_props import H, PAD, T, clean, plank, post, shade_under, stone_px, tuft, wood  # noqa: E402

# The house palette's ramps this batch adds (art/house-palette.json, PR #121).
H.update({
    'lamp': ['#67450A', '#9B6912', '#CB8D26', '#F0B050', '#F5D49C', '#FFF6E6'],
    'sand': ['#6F4E46', '#926F5A', '#B49271', '#D4B488', '#EFD09C', '#FFEBC8'],
    'sand_warm': ['#765546', '#9A775A', '#BB9A6F', '#DBBD87', '#F8D79C', '#FFF2DB'],
    'sand_cool': ['#684441', '#8C6556', '#AE866C', '#CEA883', '#E9C496', '#FEDEAF'],
    'snow': ['#757390', '#9597B0', '#B6BBCE', '#D6DEEA', '#E6EAEC', '#F5F4EB'],
    'leaf_cool': ['#01211A', '#02432C', '#25633D', '#488250', '#70995D', '#98AC70'],
    'iron_cool': ['#1C122D', '#2D2640', '#3F3A51', '#504F60', '#6D6670', '#877C7A'],
    'earth_warm': ['#271014', '#462D27', '#654A3B', '#826950', '#9C8261', '#B29A75'],
    'water_cool': ['#12164E', '#233771', '#385990', '#507AAB', '#6C95BA', '#8FADBD'],
    'slate_warm': ['#271F45', '#413E64', '#5C5E81', '#787E9C', '#9897AC', '#B6AEB5'],
})


def straw(x: int, y: int, i: int, seed: int) -> str:
    """Straw or hay: stalks in short slanting runs that swap between the sand ramp and its
    warm sibling, a few a step darker where they cross."""
    n = noise2((x + y) // 3, y // 2, seed + 911)
    fam = 'sand' if n < 0.5 else 'sand_warm' if n < 0.85 else 'sand_cool'
    return T(fam, i - (1 if noise2((x - y) // 3, y, seed + 912) > 0.85 else 0))


def stone_block(cv: Canvas, x0: int, y0: int, w: int, h: int, seed: int, top: int = 1, light: int = 4):
    """One squared stone seen a little from above: a lit top band `top` rows deep, its
    face a step down with the west edge lit and the east edge in shade."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if y < y0 + top:
                i = light + 1
            else:
                i = light if x == x0 else light - 2 if x >= x0 + w - 1 else light - 1
            if y == y0 + h - 1 and y >= y0 + top:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, seed))


# ---- wayside shrines -----------------------------------------------------------------

def shrine_post() -> Canvas:
    """A wayside shrine on an oak post (the size guide's shrine, 32 to 56 tall): a little
    gabled box at chest height with a shingled roof and a dark niche, a carved figure in it
    worn smooth, a ledge in front holding a jar of wildflowers someone keeps fresh, a faded
    ribbon tied to the post; the post set in a heap of field stones."""
    w, h = 24, 44
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    cx = 10
    shade_under(cv, 4, 22, foot)
    post(cv, cx, 20, foot - 2, 3, seed=201, cap=False)
    for y in range(9, 21):  # the box: plank sides lit on the west, a dark niche
        for x in range(4, 20):
            if 7 <= x <= 16 and 12 <= y <= 18:
                i = 0 if y < 14 else 1  # the niche, darker at the back and under the roof
                cv.set(x, y, T('timber', i))
            else:
                i = 4 if x < 7 else 3 if x < 17 else 2
                cv.set(x, y, wood(x, y, i, 202, along_x=False))
    for y in range(13, 19):  # the carved figure, pale oak, lit from the west
        half = 1 if y < 15 else 2
        for x in range(12 - half, 12 + half):
            cv.set(x, y, T('bleached', 4 if x < 12 else 3))
    cv.hline(11, 13, 2, T('bleached', 5))  # its head
    for y in range(1, 10):  # the gable roof of shingles, lit on the west slope
        half = 2 + y
        for x in range(12 - half, 12 + half):
            west = x < 12
            if y == 9:
                c = T('timber', 1)  # the eaves' shadow
            elif y % 3 == 2:
                c = T('timber', 2 if west else 1)
            else:
                c = T('timber_warm' if (x + y) % 5 else 'timber', 4 if west else 2)
            cv.set(x, y, c)
    cv.vline(12, 0, 2, T('timber', 5))  # the ridge's finial
    for x in range(3, 21):  # the ledge in front of the niche
        cv.set(x, 20, T('timber', 5 if x < 18 else 4)); cv.set(x, 21, T('timber', 2))
    for y in range(16, 20):  # a jar of wildflowers on the ledge
        cv.hline(15, y, 3, T('water', 4) if y > 17 else T('leaf', 3))
    for (fx, fy, c) in ((14, 15, ('berry', 4)), (15, 15, ('berry', 5)), (17, 14, ('plaster', 5)), (18, 14, ('plaster', 4)), (16, 15, ('leaf', 4))):
        cv.set(fx, fy, T(*c))
    for y in range(23, 29):  # a faded ribbon tied round the post, its tails hanging
        pass
    cv.hline(cx, 24, 3, T('berry', 3)); cv.vline(cx + 3, 24, 4, T('berry', 2)); cv.vline(cx + 4, 25, 3, T('berry', 3))
    for (sx, sy, rx, ry) in ((cx - 3, foot - 2, 3.4, 2.2), (cx + 5, foot - 2, 3.2, 2), (cx + 1, foot - 3, 2.6, 1.8)):
        for (x, y) in oval(sx, sy, rx, ry):  # the stones heaped round its foot
            lit = (x - sx) + (y - sy) * 1.3 < -0.5
            cv.set(x, y, stone_px(x, y, 4 if lit else 3 if x - sx < 1 else 2, 203))
    tuft(cv, 2, foot, 3); tuft(cv, w - 2, foot, 1)
    return cv


def shrine_stone() -> Canvas:
    """A stone wayside shrine at a crossing: a squared plinth of two courses, a niche block
    with an arched recess and a small stone figure, a pitched stone cap with moss on its
    north side, and in front a kneeling stone worn hollow and a little cairn of pebbles
    people leave as they pass."""
    w, h = 32, 40
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 2, 30, foot)
    stone_block(cv, 6, 27, 18, 6, 211, top=1, light=4)  # the plinth's lower course
    stone_block(cv, 8, 22, 14, 5, 212, top=1, light=4)  # its upper course
    stone_block(cv, 9, 9, 12, 13, 213, top=0, light=4)  # the niche block
    for y in range(11, 20):  # the arched recess, dark
        half = 3 if y > 12 else 2 if y == 12 else 1
        for x in range(15 - half, 15 + half):
            cv.set(x, y, T('stone', 0) if y < 15 else T('stone', 1))
    for y in range(14, 20):  # the figure in it
        cv.hline(14, y, 2, T('stone_warm', 5 if y < 16 else 4))
    cv.set(14, 13, T('stone_warm', 5)); cv.set(15, 13, T('stone_warm', 4))
    for y in range(3, 10):  # the pitched cap, its west slope lit
        half = 1 + (y - 3) * 7 // 6
        for x in range(15 - half, 15 + half):
            cv.set(x, y, stone_px(x, y, 5 if x < 15 and y < 9 else 4 if x < 15 else 2, 214))
        cv.set(15 - half, y, T('stone', 2)) if y == 9 else None
    cv.hline(7, 9, 16, T('stone', 1))  # the cap's drip edge throwing its shadow
    for (mx, my) in ((17, 5), (18, 6), (19, 7), (18, 7), (20, 8)):  # moss on the cap's north-east slope
        cv.set(mx, my, T('leaf', 3 if my < 7 else 2))
    stone_block(cv, 10, 34, 10, 3, 215, top=1, light=4)  # the kneeling stone, worn hollow
    cv.hline(13, 34, 4, T('stone_warm', 3))
    for (px, py, c) in ((24, foot - 2, 4), (25, foot - 2, 3), (26, foot - 2, 2), (24, foot - 3, 5), (25, foot - 3, 4), (25, foot - 4, 4)):
        cv.set(px, py, T('stone_warm', c))  # pebbles left by walkers
    for (fx, fy) in ((10, 21), (11, 21)):  # a posy laid on the plinth
        cv.set(fx, fy, T('berry', 4))
    cv.set(12, 21, T('leaf', 3)); cv.set(9, 21, T('plaster', 5))
    tuft(cv, 3, foot, 3); tuft(cv, 21, foot, 0); tuft(cv, w - 2, foot, 5)
    return cv


# ---- beehives -------------------------------------------------------------------------

def beehive(variant: int = 0) -> Canvas:
    """A hive at the orchard's edge (the size guide's beehive, hip high, 10 to 16 wide):
    variant 0 a white tiered hive on legs, each lift's lip lit along its top, a gabled roof,
    the entrance slot over a landing board, its paint flaking to grey timber; variant 1 a
    straw skep in coils bound with split bramble, on a stone slab under a little thatched
    hackle against the rain; variant 2 a painted box hive on two bricks with a stone on the
    lid to keep the wind from lifting it."""
    if variant == 0:
        w, h = 16, 22
        cv = Canvas(w, h, pad=PAD)
        foot = h - 1
        shade_under(cv, 1, 16, foot)
        for lx in (2, 11):  # the legs, each on a flat stone against the damp
            cv.vline(lx, 16, 4, T('timber', 3)); cv.vline(lx + 1, 16, 4, T('timber', 2))
            cv.hline(lx - 1, 20, 4, T('stone', 4)); cv.set(lx + 2, 20, T('stone', 2))
        cv.hline(0, 15, 16, T('timber', 4)); cv.hline(0, 16, 16, T('timber', 2))  # the floor and landing board
        for (y0, y1) in ((9, 15), (4, 9)):  # two lifts, each wider at its lip
            for y in range(y0, y1):
                for x in range(1, 15):
                    i = 5 if y == y0 else 4 if x < 4 else 3 if x < 12 else 2
                    fam = 'snow'
                    if noise2(x // 3, y // 2, 221) > 0.78 and y > y0:
                        fam, i = 'bleached', 3  # paint flaked off
                    cv.set(x, y, T(fam, i))
            cv.hline(0, y0, 16, T('snow', 5)); cv.set(15, y0, T('snow', 3))
        cv.hline(5, 14, 6, T('timber', 0))  # the entrance slot
        for y in range(0, 4):  # the gabled roof, its eaves flush with the lifts' lips
            half = 3 + y * 2
            for x in range(max(0, 8 - half), min(16, 8 + half)):
                cv.set(x, y, T('slate', 4 if x < 8 else 2))
        cv.hline(0, 4, 16, T('slate', 1))
        cv.hline(3, 2, 2, T('leaf_warm', 4)); cv.hline(12, 3, 2, T('leaf_warm', 3))  # lichen on the roof
        cv.hline(6, 15, 2, T('lamp', 3)); cv.hline(9, 16, 2, T('lamp', 2))  # bees on the board
        cv.hline(2, 10, 3, T('brass', 4)); cv.hline(2, 11, 3, T('brass', 2))  # the hive's number plate
        for hy in (6, 12):  # a handhold cut in each lift
            cv.hline(9, hy, 3, T('snow', 1))
        for y in (5, 6, 7):  # the beekeeper's record card pinned to the top lift
            cv.hline(3, y, 3, T('plaster', 4 if y < 7 else 3))
        cv.hline(7, 1, 2, T('slate', 1))  # the vent under the roof's gable
        for x in range(1, 15):  # grass grown up between the legs
            if x % 3:
                cv.set(x, 20, T('grass', 3 if x < 8 else 2)); cv.set(x, 19, T('grass', 4)) if x % 4 == 1 else None
        for (x, y, c) in ((9, 0, 5), (10, 0, 4), (8, 1, 4), (9, 1, 3), (10, 1, 3), (11, 1, 2)):
            cv.set(x, y, T('stone_warm', c))  # a stone on the roof against the wind
        return cv
    if variant == 1:
        w, h = 16, 18
        cv = Canvas(w, h, pad=PAD)
        foot = h - 1
        shade_under(cv, 1, 16, foot)
        for y in range(foot - 4, foot):  # the stone slab on its rough plinth
            for x in range(1 if y < foot - 1 else 2, 15 if y < foot - 1 else 14):
                cv.set(x, y, stone_px(x, y, 5 if y == foot - 4 else 4 if x < 6 else 3, 222))
        for (x, y) in oval(8, 9, 6.2, 5.5):  # the skep: coils of straw
            if y > foot - 5:
                continue
            band = (y - 3) // 3
            lit = (x - 8) + (y - 9) * 0.8 < 0
            i = 5 if lit and (y - 3) % 3 == 0 else 4 if lit else 3 if x < 12 else 2
            rr = ((x + 0.5 - 8) / 6.2) ** 2 + ((y + 0.5 - 9) / 5.5) ** 2
            if (y - 3) % 3 == 2 and rr < 0.7:
                i = max(1, i - 2)  # the groove under each coil (the rim keeps its own edge)
            if rr > 0.75 or y >= 12:
                i = max(i, 3)  # the rim and the foot stay a step above the outline
            if (x + band * 3) % 6 == 0 and (y - 3) % 3 == 1:
                cv.set(x, y, T('earth_warm', 2)); continue  # a bramble binding
            cv.set(x, y, straw(x, y, i, 223 + band))
        for x in range(2, 14):  # the skep's flared foot coil, sitting on the slab
            cv.set(x, foot - 5, straw(x, foot - 5, 4 if x < 7 else 3, 226))
        for x in range(6, 10):  # the entrance at its foot
            cv.set(x, foot - 5, T('earth', 0))
        for (x, y) in oval(8, 3, 4, 2):  # the hackle: a little straw cap over the crown
            cv.set(x, y, straw(x, y, 5 if x < 8 else 3, 224))
        return cv
    w, h = 16, 20
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, 16, foot)
    for bx in (2, 10):  # two bricks it stands on
        for y in range(foot - 3, foot):
            cv.hline(bx, y, 4, T('clay', 4 if y == foot - 3 else 3 if bx == 2 else 2))
    for y in range(4, foot - 3):  # the box: painted boards, lit on the west, the joints between boxes
        for x in range(1, 15):
            i = 4 if x < 4 else 3 if x < 12 else 2
            if y in (4, 10):
                i = 5  # each box's top edge
            if y in (9, 15):
                i = 1  # the joint
            cv.set(x, y, T('water_cool', i))
    cv.hline(5, 14, 6, T('slate', 0))  # the entrance
    cv.hline(5, 14, 2, T('timber', 4))  # the entrance block, half closed for the cold
    for hy in (6, 12):  # the handholds on each box
        cv.hline(9, hy, 3, T('water_cool', 1))
    for x in range(1, 15):  # the queen excluder's rim between the boxes
        cv.set(x, 9, T('iron', 3 if x < 10 else 2))
    for y in range(4, foot - 3):  # a ratchet strap round the hive against the wind
        cv.set(6, y, T('slate', 2 if y % 5 else 4)); cv.set(7, y, T('slate', 1))
    for y in range(0, 3):  # a jar feeder of syrup upturned on the crown board
        cv.hline(11, y, 3, T('lamp', 4 if y == 0 else 3) if y < 2 else T('lamp', 2))
    cv.hline(0, 3, 16, T('iron', 4)); cv.hline(0, 4, 16, T('iron', 2))  # the metal roof
    for y in range(0, 3):  # the stone on the lid
        cv.hline(5 - y // 2, y, 6 + y, stone_px(6, y, 4 if y == 0 else 3, 225))
    cv.hline(5, 0, 3, T('stone', 5))
    return cv


# ---- the scarecrow --------------------------------------------------------------------

def scarecrow() -> Canvas:
    """A scarecrow in the field (about a person's height with its arms out): an ash pole
    with a cross-spar, an old tweed coat buttoned over a straw belly and sagging at the
    pockets, straw spilling from the cuffs and the neck, a sacking head with a stitched
    face, a battered felt hat; a strip of rag tied to one sleeve to flap, a crow sitting
    on the other arm unconcerned, the pole's foot packed with stones."""
    w, h = 32, 40
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    cx = 15
    shade_under(cv, 10, 22, foot)
    post(cv, cx, 12, foot - 1, 2, seed=231, cap=False)
    for x in range(3, 29):  # the cross-spar
        cv.set(x, 14, wood(x, 14, 4, 232)); cv.set(x, 15, wood(x, 15, 2, 232))
    for y in range(13, 30):  # the coat: tweed, lit on the west, its skirts flaring
        half = 6 if y < 24 else 6 + (y - 24) // 2
        for x in range(cx + 1 - half, cx + 1 + half):
            k = (x - (cx + 1 - half)) / (2 * half)
            i = 4 if k < 0.25 else 3 if k < 0.65 else 2
            if (x + y) % 4 == 0 and i > 2:
                i -= 1  # the tweed's weave, in diagonal ribs
            cv.set(x, y, T('earth_warm', i))
    for y in range(14, 19):  # the sleeves along the spar
        for x in list(range(4, cx - 4)) + list(range(cx + 7, 28)):
            i = 4 if y == 14 else 3 if y < 17 else 2
            cv.set(x, y, T('earth_warm', i))
    cv.vline(cx + 1, 17, 12, T('earth_warm', 1))  # the coat's front edge
    for by in (19, 23):  # its buttons
        cv.set(cx + 2, by, T('brass', 3))
    cv.hline(cx - 4, 25, 4, T('earth_warm', 1)); cv.hline(cx + 4, 25, 3, T('earth_warm', 1))  # sagging pockets
    for (sx, sy) in ((2, 15), (2, 16), (3, 17), (28, 15), (29, 16), (28, 17), (cx - 1, 30), (cx + 2, 30), (cx, 31)):
        cv.set(sx, sy, straw(sx, sy, 4, 233))  # straw at the cuffs and the hem
    for (x, y) in oval(cx + 1, 9, 4, 4):  # the sacking head
        lit = (x - cx - 1) + (y - 9) < 0
        cv.set(x, y, T('sand_cool', 4 if lit else 3) if (x + y) % 3 else T('sand_cool', 3 if lit else 2))
    cv.hline(cx - 1, 9, 2, T('earth', 1)); cv.hline(cx + 2, 9, 2, T('earth', 1))  # stitched eyes
    cv.hline(cx, 11, 3, T('earth', 2))  # the stitched mouth
    for x in range(cx - 2, cx + 5):  # straw at the neck
        cv.set(x, 13, straw(x, 13, 5 if x < cx + 1 else 3, 234))
    for y in range(2, 7):  # the battered felt hat: a crown with a dent, a floppy brim
        half = 3 if y < 6 else 6
        for x in range(cx + 1 - half, cx + 1 + half):
            i = 3 if x < cx + 1 else 2
            if y == 6:
                i = 3 if x < cx + 2 else 1
            cv.set(x, y + (1 if (y == 6 and x > cx + 4) else 0), T('slate_warm', i))
    cv.hline(cx, 2, 2, T('slate_warm', 4)); cv.hline(cx - 2, 5, 6, T('berry', 2))  # the dent lit, a hatband
    for k in range(5):  # a rag tied to the west sleeve, lifting in the wind
        cv.hline(5 - k // 2, 19 + k, 2, T('plaster', 4 if k < 3 else 3))
    for (x, y, c) in ((24, 12, 2), (25, 12, 2), (26, 12, 1), (24, 13, 1), (25, 13, 1), (23, 12, 3), (27, 11, 1), (24, 11, 2)):
        cv.set(x, y, T('slate', c))  # a crow on the east arm
    cv.set(23, 11, T('brass', 4))  # its beak
    for (sx, sy, rx, ry) in ((cx - 2, foot - 1, 2.6, 1.6), (cx + 3, foot - 1, 2.4, 1.5)):
        for (x, y) in oval(sx, sy, rx, ry):  # stones packed round the pole's foot
            cv.set(x, y, stone_px(x, y, 4 if x < sx else 2, 235))
    tuft(cv, cx - 6, foot, 3); tuft(cv, cx + 7, foot, 5)
    return cv


# ---- cairns ---------------------------------------------------------------------------

def cairn(size: int = 1) -> Canvas:
    """A trail cairn (the size guide's cairn, at most a person's height): rounded field
    stones piled in rough courses, big ones at the foot and smaller ones up the pile, each
    lit on its top and west face with a dark crack where it sits on the next, lichen on the
    old ones and a pale capstone a walker has added. Size 0 a knee-high marker, 1 the trail
    cairn at a fork, 2 a tall pile with a flat stone stood on end at its top."""
    w, h = {0: (16, 14), 1: (24, 20), 2: (24, 26)}[size]
    per = 9 if size == 0 else 7  # stones per course: a marker is a few big stones
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    cx = w / 2
    stones = []
    y = foot - 1
    half = (w - 4) / 2
    k = 0
    while half >= 2.5 and y > 4:  # rough courses from the ground up
        rh = 2.6 if half > 5 else 2.2
        n = max(1, int(half * 2 / per))
        x = cx - half + (0.8 if k % 2 else 0)
        step = half * 2 / n
        for j in range(n):
            rx = step / 2 + 0.3 + noise2(j, k, 241 + size) * 0.8
            stones.append((x + step / 2, y - rh + 0.5 + noise2(k, j, 242) * 0.6, rx, rh, j + k * 7))
            x += step
        y -= int(rh * 2) - 1
        half -= 1.6 if size == 0 else 1.9
        k += 1
    if size == 0:  # a marker is three big stones and a cap
        stones = [(4.5, foot - 3.0, 3.6, 2.8, 1), (11.0, foot - 3.0, 3.6, 2.8, 2), (8.0, foot - 7.4, 3.4, 2.6, 3)]
    for (sx, sy, rx, ry, seed) in stones:  # each stone rounded, its top and west lit, its foot in shade
        for (x, y) in oval(sx, sy, rx, ry):
            u, v = (x + 0.5 - sx) / rx, (y + 0.5 - sy) / ry
            if v > 0.62:
                c = T('stone', 1)  # the crack where it sits
            else:
                i = 5 if u + v < -0.6 else 4 if u + v < 0.1 else 2 if rx < 3.2 else 3 if u + v < 0.7 else 2
                n = noise2(seed, 3, 243 + size)
                c = T('stone' if n < 0.45 else 'stone_warm' if n < 0.75 else 'stone_cool', i)  # one stone, one sibling
            cv.set(x, y, c)
        n = noise2(int(sx), int(sy), 244 + size)
        if n > 0.62 and rx > 2.5:
            cv.hline(int(sx - 1), int(sy - ry + 1), 2, T('leaf_warm', 4))  # lichen on an old stone
        elif n < 0.2 and rx > 2.5:
            cv.hline(int(sx), int(sy - ry + 1), 2, T('sand_warm', 4))  # a yellow lichen on another
    top = min(int(s[1] - s[3]) for s in stones)
    if size == 2:  # a flat stone stood on end at the top
        for yy in range(top - 4, top + 1):
            cv.hline(int(cx) - 1, yy, 2, stone_px(int(cx), yy, 5 if yy == top - 4 else 4, 245))
            cv.set(int(cx) + 1, yy, T('stone', 2))
    else:  # a pale capstone a walker added
        cv.hline(int(cx) - 2, top - 1, 4, T('stone_warm', 5)); cv.hline(int(cx) - 2, top, 4, T('stone_warm', 3))
    if size:
        tuft(cv, 1, foot, 3); tuft(cv, w - 2, foot, 1)
    return cv


# ---- the sheepfold --------------------------------------------------------------------

def sheepfold() -> Canvas:
    """A drystone sheepfold on the hill pasture, 72 wide: a round pen seen from a little
    above, its wall (the size guide's low wall, 14 high) of coursed field stone with a
    coping of stones on edge, the far wall's inner face lit, the near wall's outer face in
    half light, a gap on the west side closed by a timber hurdle tied to a post, the turf
    inside cropped short and darker, trodden bare at the gap, a stone water trough inside
    against the far wall, nettles where the sheep don't graze."""
    w, h = 72, 56
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    cx, cy = 36, 29
    rx, ry = 33, 20
    shade_under(cv, 4, w - 2, foot)
    wall = 13  # the wall's face: 14 high with its coping (the size guide's low wall)
    for (x, y) in oval(cx, cy, rx - 3, ry - 3):  # the turf inside, cropped and in the wall's shade at the back
        v = (y + 0.5 - cy) / (ry - 3)
        i = 2 if v < -0.35 else 3
        if noise2(x // 3, y // 2, 251) > 0.72:
            i += 1
        cv.set(x, y, T('grass', i))
    for x in range(cx - rx + 5, cx + rx - 4):  # the far wall's inner face, lit on the west half
        top = cy - int(math.sqrt(max(0.0, 1 - ((x + 0.5 - cx) / rx) ** 2)) * ry) + 2
        for y in range(top, top + wall - 3):
            course = (y - top) // 3
            joint = (y - top) % 3 == 2 or (x + course * 4) % 6 == 0
            if y >= cy + 2:
                break
            cv.set(x, y, stone_px(x, y, 1 if joint else 3 if x < cx else 4 if x < cx + 20 else 3, 252))
    for x in range(3, w - 3):  # the ring of coping stones on edge, seen from above
        u = (x + 0.5 - cx) / rx
        if abs(u) >= 1:
            continue
        dy = math.sqrt(1 - u * u) * ry
        for yy in (int(cy - dy), int(cy - dy) + 1, int(cy + dy) - wall - 1, int(cy + dy) - wall):
            lit = yy < cy and x < cx + 10 or yy > cy and x < cx - 10
            c = stone_px(x, yy, 5 if lit else 4, 253)
            if x % 3 == 2:
                c = T('stone', 2)  # the gap between two coping stones
            cv.set(x, yy, c)
        for y in range(int(cy + dy) - wall + 1, int(cy + dy)):  # the near wall's outer face, coursed
            r = y - (int(cy + dy) - wall + 1)
            course = r // 3
            joint = r % 3 == 2 or (x + course * 5) % 7 == 0
            i = 1 if joint else 4 if x < 18 else 3 if x < 54 else 2
            if r >= wall - 3 and not joint:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, 254))
    for x in range(3, 13):  # the gap on the west, the turf trodden bare
        for y in range(cy - 2, cy + 9):
            if cv.get(x, y)[3]:
                cv.set(x, y, T('earth', 3 if (x + y) % 5 else 2))
    for k in range(9):  # the hurdle across the gap: woven hazel between two staves
        x = 4 + k
        for y in range(cy + 1, cy + 9):
            c = T('timber_warm', 4 if (y + k) % 3 else 2) if (y - cy) % 3 else T('timber_warm', 3)
            cv.set(x, y, c)
    for y in range(cy - 2, cy + 10):
        cv.set(3, y, T('timber', 4)); cv.set(13, y, T('timber', 2))
    for y in range(17, 21):  # a stone trough inside against the far wall
        for x in range(40, 50):
            cv.set(x, y, stone_px(x, y, 5 if y == 17 else 3 if x < 48 else 2, 255))
    cv.hline(41, 18, 7, T('water', 2))
    for (nx, ny) in ((58, 20), (59, 20), (58, 21), (60, 21), (59, 22)):  # nettles in the north-east lee
        cv.set(nx, ny, T('leaf_cool', 3 if ny < 21 else 2))
    tuft(cv, 2, foot, 3); tuft(cv, 30, foot, 0); tuft(cv, w - 3, foot, 5)
    return cv


# ---- the shepherd's hut ---------------------------------------------------------------

def shepherds_hut() -> Canvas:
    """A shepherd's hut on its cast-iron wheels, 56 long (the size guide's shed: a door of
    30 under a low roof): a timber body of painted weatherboards on a chassis, a curved
    roof of corrugated iron rolled over the ends, a stable door at the east end up three
    steps, a small window with its curtain, a stovepipe through the roof with its rain cap,
    the drawbar resting on a block, the wheels spoked and lit on their west rims; the
    paint worn at the corners and moss along the roof's lower edge."""
    w, h = 56, 52
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 2, w, foot)
    body_top, body_bot = 14, 40
    x0, x1 = 6, 46
    for y in range(body_top, body_bot):  # the weatherboards, painted, each board's lower edge in shade
        for x in range(x0, x1):
            r = (y - body_top) % 4
            i = 4 if r == 0 else 3 if r < 3 else 2
            if x >= x1 - 3:
                i -= 1
            if x < x0 + 2:
                i += 1 if i < 5 else 0
            fam = 'leaf_cool' if noise2(x // 6, (y - body_top) // 4, 265) < 0.6 else 'leaf'  # repainted a board at a time
            if (x < x0 + 2 or x >= x1 - 2) and noise2(x, y // 2, 261) > 0.6:
                fam, i = 'timber', 3  # paint worn back to timber at the corners
            cv.set(x, y, T(fam, i))
    for y in range(body_top - 8, body_top + 1):  # the curved roof: corrugations running down it
        k = body_top - y
        inset = int((k / 8) ** 2 * 6)
        for x in range(x0 - 3 + inset, x1 + 3 - inset):
            corr = (x // 2) % 2
            i = (4 if corr else 3) if x < 34 else (3 if corr else 2)
            if y == body_top:
                i = 1  # the eaves
            if k == 7:
                i = min(5, i + 1)  # the crown of the roof catching the sky
            if (x // 2) % 2 == 0 and noise2(x // 2, 0, 262) > 0.75 and y > body_top - 5:
                cv.set(x, y, T('clay', 3 if x < 34 else 2)); continue  # rust running down a corrugation
            cv.set(x, y, T('iron' if noise2(x // 8, 0, 266) < 0.6 else 'iron_warm', i))  # each sheet weathered its own way
    for x in range(x0 - 2, x1 + 2):  # moss along the roof's lower edge
        if noise2(x // 2, 0, 263) > 0.55:
            cv.set(x, body_top - 1, T('leaf', 3))
    for y in range(body_top + 3, body_top + 14):  # the window: four panes, the sky in the upper west one, a curtain drawn to the east
        for x in range(11, 23):
            frame = y in (body_top + 3, body_top + 13, body_top + 8) or x in (11, 22, 16)
            if frame:
                c = T('plaster', 5 if (x == 11 or y == body_top + 3) else 4 if x < 20 else 3)
            elif x > 18:
                c = T('clay', 4 if y < body_top + 8 else 3) if x < 21 else T('clay', 2)
            elif y < body_top + 6 and x < 15:
                c = T('water', 5)
            else:
                c = T('water', 2 if y < body_top + 8 else 1)
            cv.set(x, y, c)
    cv.hline(10, body_top + 14, 14, T('plaster', 3))  # the sill
    for y in range(body_top + 2, body_bot):  # the stable door at the east end, in two leaves
        for x in range(36, 43):
            i = 4 if x == 36 else 1 if x == 42 or y == body_top + 14 else 3
            cv.set(x, y, T('slate_warm', i))
    cv.hline(41, body_top + 16, 1, T('brass', 4)); cv.set(41, body_top + 17, T('brass', 2))
    for (x, y) in oval(4, body_top + 12, 3.2, 4.4):  # a tin bath hung on the west end wall
        if x >= x0 - 1:
            continue
        cv.set(x, y, T('iron', 5 if x < 3 and y < body_top + 12 else 4 if x < 4 else 2))
    for (hx, hy) in ((38, body_top + 5), (39, body_top + 4), (40, body_top + 5), (38, body_top + 6), (40, body_top + 6)):
        cv.set(hx, hy, T('iron', 4 if hy < body_top + 6 else 2))  # a horseshoe nailed over the door for luck
    for k in range(3):  # the steps up to it
        cv.hline(40 + k * 2, body_bot + k * 3, 8, T('timber', 5)); cv.hline(40 + k * 2, body_bot + k * 3 + 1, 8, T('timber', 2))
    for y in range(body_top - 14, body_top - 4):  # the stovepipe and its rain cap
        cv.set(25, y, T('iron', 4)); cv.set(26, y, T('iron', 2))
    cv.hline(23, body_top - 15, 6, T('iron', 4)); cv.hline(23, body_top - 14, 6, T('iron', 1))
    for x in range(x0, x1):  # the chassis beam under the body
        cv.set(x, body_bot, T('timber', 2)); cv.set(x, body_bot + 1, T('timber', 1))
    for wx in (12, 36):  # the iron wheels, spoked, the west rim lit
        for (x, y) in oval(wx, body_bot + 5, 5.5, 5.5):
            r = math.hypot(x + 0.5 - wx, y + 0.5 - body_bot - 5)
            ang = math.atan2(y + 0.5 - body_bot - 5, x + 0.5 - wx)
            if r > 4.2:
                cv.set(x, y, T('iron', 4 if x < wx else 2))  # the iron tyre
            elif r < 1.5:
                cv.set(x, y, T('clay', 4 if x < wx else 2))  # the hub in red oxide
            elif abs(math.sin(ang * 3)) < 0.28:
                cv.set(x, y, T('clay', 3 if x < wx else 1))  # spokes in red oxide
    for k in range(10):  # the drawbar resting on a block
        cv.set(k, body_bot + 2 + k // 4, T('timber', 4)); cv.set(k, body_bot + 3 + k // 4, T('timber', 2))
    for y in range(body_bot + 4, body_bot + 7):
        cv.hline(0, y, 4, T('timber', 4 if y == body_bot + 4 else 2))  # a sawn block under it
    for (lx, ly) in ((18, body_bot + 6), (22, body_bot + 6), (26, body_bot + 6), (20, body_bot + 3), (24, body_bot + 3)):
        for (x, y) in oval(lx, ly, 2.2, 1.8):  # split logs stacked under the hut, their end grain lit
            cv.set(x, y, T('timber', 5 if x < lx and y < ly else 4 if x < lx + 1 else 2))
        cv.set(lx, ly, T('timber', 2))
    for y in range(body_top + 3, body_top + 7):  # a hurricane lamp hung by the door
        cv.hline(34, y, 2, T('brass', 4 if y == body_top + 3 else 3) if y in (body_top + 3, body_top + 6) else T('lamp', 4))
    cv.set(34, body_top + 2, T('iron', 3))
    for x in range(x0 - 1, x1 + 1):  # the roof's ridge cap
        if x0 + 4 < x < x1 - 4:
            cv.set(x, body_top - 8, T('iron', 5 if x < 30 else 4))
    tuft(cv, 6, foot, 3); tuft(cv, 24, foot, 0); tuft(cv, w - 2, foot, 5)
    return cv


# ---- the hay barn ---------------------------------------------------------------------

def _is_back(c) -> bool:
    return '#%02X%02X%02X' % c[:3] in (H['earth'][0], H['earth_warm'][0])


def hay_barn() -> Canvas:
    """An open-sided Dutch hay barn, 112 long (the size guide's barn, a tall single volume):
    four bays between timber posts on stone pads, a curved roof of corrugated iron on
    trusses, its ridge high so a loaded wain fits under; square bales of hay stacked in
    the bays to different heights (the west bay nearly empty, the middle ones full, a few
    bales tumbled), the stack's faces lit on the west, loose hay on the floor, a ladder
    against the stack and a pitchfork leaning on a post."""
    w, h = 112, 96
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 2, w, foot)
    eaves, ridge = 30, 8
    bays = [4, 30, 56, 82, 108]
    floor = foot - 2
    for x in range(2, w - 2):  # the floor of the barn, beaten earth under loose hay
        for y in range(floor - 1, foot):
            cv.set(x, y, T('earth', 3 if y < foot - 1 else 2))
    for x in range(6, w - 6):  # the back of the barn: deepest under the roof, the weatherboarded back wall catching light low down
        for y in range(eaves, floor - 1):
            d = (y - eaves) / (floor - 1 - eaves)
            i = 0 if d < 0.12 else 1 if d < 0.4 else 2 if d < 0.75 else 3
            fam = 'earth' if noise2(x // 5, (y - eaves) // 4, 287) < 0.6 else 'earth_warm'
            if (y - eaves) % 4 == 3 and i > 0:
                i -= 1  # the joint under each back board
            cv.set(x, y, T(fam, i))
    stacks = [(0, 4), (1, 9), (2, 8), (3, 1)]  # rows of bales in each bay: the east bay fed out first
    for (bi, n) in stacks:  # the bales: each 12 long and 6 tall, laid in a bond, lit on the west and on top
        bx0, bx1 = bays[bi] + 3, bays[bi + 1]
        for r in range(n):
            y1 = floor - 1 - r * 6
            y0 = y1 - 6
            if y0 < eaves + 1:
                break
            off = 6 if r % 2 else 0
            for x in range(bx0, bx1):
                for y in range(y0, y1):
                    bale = (x - bx0 + off) // 12
                    u = (x - bx0 + off) % 12
                    top = y == y0
                    i = 5 if top else 4 if u < 3 else 3 if u < 10 else 2
                    if u == 11 or y == y1 - 1:
                        i = 2 if top else 1  # the joint between bales
                    elif u in (3, 8) and not top:
                        i -= 1  # the twine round each bale, sunk into the hay
                    cv.set(x, y, straw(x, y, i, 271 + bale + r * 5))
    tarp_top = floor - 1 - 9 * 6
    for x in range(bays[1] + 3, bays[2] + 12):  # a tarpaulin over the top of the fullest stack against drips, roped down
        drop = 3 + (2 if x > bays[2] + 4 else 0) + (1 if (x // 6) % 2 else 0)
        for y in range(tarp_top, tarp_top + drop):
            i = 4 if y == tarp_top else 3 if x < bays[2] else 2
            if (x - bays[1]) % 9 == 0:
                i -= 1  # a fold
            cv.set(x, y, T('slate_warm', i))
        if (x - bays[1]) % 12 == 5:
            cv.vline(x, tarp_top + drop, 4, T('sand_cool', 2))  # a rope tying it down
    for x in range(6, w - 6):  # light through the gap between the roof and the back wall's top
        if cv.get(x, eaves + 2)[:3] != (0, 0, 0) and (x // 3) % 2 == 0 and noise2(x // 3, 0, 288) > 0.5:
            if _is_back(cv.get(x, eaves + 2)):
                cv.set(x, eaves + 2, T('sky', 3) if 'sky' in H else T('snow', 2))
    for (nx, ny, c) in ((60, eaves + 2, 4), (61, eaves + 2, 3), (62, eaves + 2, 3), (60, eaves + 3, 3), (61, eaves + 3, 2), (62, eaves + 3, 1)):
        cv.set(nx, ny, T('earth_warm', c))  # a swallows' nest of mud under the eaves beam
    for (bx, by) in ((88, floor - 6), (97, floor - 5)):  # bales tumbled in the east bay as it was fed out
        for x in range(bx, bx + 8):
            for y in range(by, by + 5):
                cv.set(x, y, straw(x, y, 5 if y == by else 4 if x < bx + 2 else 3, 279))
        cv.hline(bx, by + 4, 8, T('sand', 1))
    for x in range(4, w - 4):  # loose hay along the floor
        if noise2(x // 2, 0, 280) > 0.45:
            cv.set(x, floor - 1, straw(x, floor - 1, 4, 281))
    for px in bays[1:-1]:  # the back row of posts, seen through the open bays in the barn's shade
        for y in range(eaves + 2, floor - 1):
            if cv.get(px + 6, y)[:3] in ((0x5F, 0x46, 0x3D), (0x43, 0x2B, 0x2A)):
                cv.hline(px + 6, y, 2, T('timber', 1))
    for x in range(6, w - 6):  # daylight under the back eaves, the field beyond
        for y in (floor - 3, floor - 2):
            if cv.get(x, y)[:3] in ((0x5F, 0x46, 0x3D),):
                cv.set(x, y, T('grass', 2 if y == floor - 3 else 3))
    for px in bays:  # the posts on their stone pads, lit on the west
        post(cv, px, eaves, floor, 3, seed=282 + px)
        for y in (floor, floor + 1):
            cv.hline(px - 1, y, 5, stone_px(px, y, 4 if y == floor else 2, 283))
    for x in range(0, w):  # the eaves beam
        cv.set(x, eaves, T('timber', 4)); cv.set(x, eaves + 1, T('timber', 2))
    for px in bays:  # knee braces from each post up to the beam
        for k in range(6):
            if px + 3 + k < w:
                cv.set(px + 3 + k, eaves + 7 - k, T('timber', 3)); cv.set(px + 3 + k, eaves + 8 - k, T('timber', 1))
            if px - 1 - k >= 0:
                cv.set(px - 1 - k, eaves + 7 - k, T('timber', 4)); cv.set(px - 1 - k, eaves + 8 - k, T('timber', 2))
    for y in range(ridge, eaves):  # the curved roof, corrugations down it, the west end lit
        k = (y - ridge) / (eaves - ridge)
        inset = int((1 - k) ** 2 * 6)
        for x in range(inset, w - inset):
            corr = (x // 2) % 2
            i = (4 if corr else 3) if x < w * 0.6 else (3 if corr else 2)
            if y == ridge:
                i = 5 if x < w * 0.6 else 4  # the ridge catches the sky
            if y >= eaves - 2:
                i -= 1
            n = noise2(x // 8, (y - ridge) // 7, 286)  # each sheet of iron weathered its own way
            fam = 'iron' if n < 0.5 else 'iron_warm' if n < 0.78 else 'iron_cool'
            if (x // 2) % 2 == 0 and noise2(x // 2, 0, 284) > 0.72 and y > ridge + 3 + int(noise2(x // 2, 1, 285) * 8):
                cv.set(x, y, T('clay', 3 if x < w * 0.6 else 2)); continue  # rust running down a corrugation
            cv.set(x, y, T(fam, i))
        if (y - ridge) % 7 == 6:
            for x in range(inset, w - inset):
                if (x // 2) % 2 == 0:
                    cv.set(x, y, T('iron', 1))  # the lap between two rows of sheets
    for k in range(18):  # a ladder against the middle stack
        y = floor - 2 - k * 2
        x = 66 + k // 4
        if y < eaves + 4:
            break
        cv.hline(x, y, 6, T('timber', 4))
    for y in range(eaves + 6, floor - 1):
        cv.set(66 + (floor - y) // 9, y, T('timber', 3)); cv.set(71 + (floor - y) // 9, y, T('timber', 2))
    for (x, y) in oval(13, floor - 9, 7.5, 7.5):  # an old cartwheel leaning against the west post, spoked, its iron tyre
        r = math.hypot(x + 0.5 - 13, y + 0.5 - floor + 9)
        ang = math.atan2(y + 0.5 - floor + 9, x + 0.5 - 13)
        if r > 6.3:
            cv.set(x, y, T('iron', 4 if x < 13 else 2))
        elif r > 5.2:
            cv.set(x, y, T('timber', 4 if x < 13 else 2))  # the felloes
        elif r < 1.8:
            cv.set(x, y, T('timber', 3 if x < 13 else 1))  # the hub
        elif abs(math.sin(ang * 4)) < 0.3:
            cv.set(x, y, T('timber_warm', 4 if x < 13 else 2))  # spokes
    for k in range(20):  # a pitchfork leaning on the east post
        cv.set(104 - k // 6, floor - 2 - k, T('bleached', 4))
    cv.hline(99, floor - 23, 4, T('iron', 4)); cv.set(99, floor - 22, T('iron', 3)); cv.set(102, floor - 22, T('iron', 3))
    tuft(cv, 1, foot, 3); tuft(cv, 40, foot, 0); tuft(cv, w - 2, foot, 5)
    return cv


# ---- the old oak ----------------------------------------------------------------------

_LEAF_AT = {}


def _leaf_index(c) -> tuple | None:
    if not _LEAF_AT:
        for fam in ('leaf', 'leaf_warm', 'leaf_cool'):
            for i, hx in enumerate(H[fam]):
                _LEAF_AT[tuple(int(hx[k:k + 2], 16) for k in (1, 3, 5))] = i
    return _LEAF_AT.get(tuple(c[:3]))


CLUMP = ('.##.', '####', '####', '.##.')


def leaf_clumps(cv: Canvas, shape, seed: int = 0):
    """Leaf clusters over a crown's lobes, as Eastward's trees are built: clumps four wide
    on a staggered, jittered grid, each lit along its top and west, shaded along its
    underside, from the lobe's own tone at that spot, some clumps in the warm or cool
    sibling so the crown holds sun-struck and shaded leaves; the lobes' banding stays
    underneath and reads through the gaps."""
    pts = set(shape)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for gy in range(min(ys), max(ys), 3):
        row = (gy - min(ys)) // 3
        for gx in range(min(xs) + (row % 2) * 2, max(xs), 4):
            jx = int(noise2(gx, gy, seed) * 2)
            jy = int(noise2(gy, gx, seed + 1) * 2)
            ox, oy = gx + jx, gy + jy
            if (ox + 1, oy + 1) not in pts:
                continue
            base = _leaf_index(cv.get(ox + 1, oy + 1))
            if base is None:
                continue
            n = noise2(ox // 5, oy // 4, seed + 2)
            fam = 'leaf' if n < 0.55 else 'leaf_warm' if n < 0.8 else 'leaf_cool'
            for r, line in enumerate(CLUMP):
                for c, ch in enumerate(line):
                    x, y = ox + c, oy + r
                    if ch != '#' or (x, y) not in pts:
                        continue
                    i = base + (1 if r == 0 or (r == 1 and c == 0) else -1 if r == 3 or (r == 2 and c == 3) else 0)
                    cv.set(x, y, T(fam, max(0, min(5, i))))

def old_oak() -> Canvas:
    """The valley's old oak (the size guide's veteran tree, the place's landmark): a short
    massive trunk split by a hollow you could stand in, its bark in deep plates lit on the
    west, buttress roots spreading into the turf; a broad low crown of rounded lobes, each
    lobe lit on its upper west and shaded below, darker where lobes overlap, sky holes
    through it, and two stag-headed dead limbs breaking out of the top, bleached grey; a
    bracket fungus on the trunk and lichen on the north side."""
    w, h = 112, 112
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    cx = 54
    shade_under(cv, 8, w - 4, foot)
    for (x, y) in oval(cx + 4, foot - 2, 40, 4):  # the crown's shadow on the turf under it
        cv.set(x, y, (24, 18, 30, 70))
    for y in range(58, foot):  # the trunk, flaring to its roots
        t = (y - 58) / (foot - 58)
        half = 9 + int(t ** 2.2 * 14)
        for x in range(cx - half, cx + half + 1):
            u = (x - (cx - half)) / (2 * half)
            i = 4 if u < 0.22 else 3 if u < 0.5 else 2 if u < 0.8 else 1
            plate = noise2((x - cx) // 2, y // 4, 291)
            if plate > 0.7:
                i -= 1  # the fissures between bark plates
            elif plate < 0.15 and i < 4:
                i += 1  # a plate's lit edge
            cv.set(x, y, T('earth_warm', max(0, i)))
    for y in range(82, foot - 4):  # the hollow: a pointed split, dark inside, its west lip lit
        half = min(4, 1 + (y - 82) // 3)
        sx = cx + 2 + (y - 82) // 8
        for x in range(sx - half, sx + half):
            cv.set(x, y, T('earth', 0) if y > 86 else T('earth', 1))
        cv.hline(sx - half - 2, y, 2, T('earth_warm', 5 if y % 3 else 4))
    for (fx, fy) in ((cx - 7, 70), (cx - 6, 70), (cx - 5, 70), (cx - 6, 71)):  # a bracket fungus
        cv.set(fx, fy, T('sand_warm', 4 if fy == 70 else 2))
    for y in range(60, 74, 3):  # lichen on the north-east side
        cv.hline(cx + 6, y, 2, T('leaf_cool', 4))
    for (sx, ex, dy) in ((cx - 20, cx - 10, 0), (cx + 20, cx + 10, 0)):  # buttress roots into the turf
        for k in range(abs(ex - sx)):
            x = sx + (k if ex > sx else -k)
            y = foot - 3 + k * 2 // max(1, abs(ex - sx))
            cv.set(x, y - 1, T('earth_warm', 4 if x < cx else 2)); cv.set(x, y, T('earth_warm', 2 if x < cx else 1))
    for (x0, y0, x1, y1) in ((cx - 4, 60, cx - 28, 34), (cx + 4, 60, cx + 30, 36), (cx, 60, cx + 4, 22)):  # the main limbs
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n):
            x = x0 + (x1 - x0) * k // n
            y = y0 + (y1 - y0) * k // n
            for d in range(-2, 3):
                cv.set(x + d, y, T('earth_warm', 4 if d < 0 else 2))
    lobes = [(cx - 30, 40, 16, 12), (cx - 12, 30, 18, 14), (cx + 12, 28, 18, 14), (cx + 32, 42, 16, 12),
             (cx - 20, 18, 14, 11), (cx + 4, 12, 16, 11), (cx + 24, 18, 13, 10), (cx - 40, 52, 11, 8),
             (cx + 44, 54, 10, 7), (cx - 2, 46, 20, 10), (cx + 20, 50, 14, 8), (cx - 22, 52, 14, 8)]
    import garden_props as gp
    circles = [(lx, ly, (rx + ry) // 2) for (lx, ly, rx, ry) in lobes]  # back to front: the high lobes behind
    circles.sort(key=lambda c: c[1])
    shape = gp.canopy(cv, circles, H['leaf'], seed=294, clumps=True)  # the house's foliage: lobes, rims, leaf bumps
    leaf_clumps(cv, shape, seed=295)
    for k in range(22):  # a low limb reaching out to the lit side under the crown, gnarled
        x = cx - 8 - k
        y = 68 - k // 2 - (1 if k % 7 == 3 else 0)
        t = 3 if k < 12 else 2
        for d in range(t):
            cv.set(x, y + d, T('earth_warm', 4 if d == 0 else 3 if d < t - 1 else 1))
    for (hx, hy) in ((cx - 8, 40), (cx + 18, 38), (cx - 26, 30)):  # sky holes through the crown
        for (x, y) in oval(hx, hy, 2.2, 1.6):
            cv.set(x, y, (0, 0, 0, 0))
    for (x0, y0, pts) in ((cx - 6, 8, ((-4, -5), (-7, -3), (2, -6))), (cx + 16, 10, ((3, -5), (6, -2)))):  # stag-headed dead limbs
        for (dx, dy) in pts:
            n = max(abs(dx), abs(dy))
            for k in range(n + 1):
                x, y = x0 + dx * k // n, y0 + dy * k // n
                cv.set(x, y, T('bleached', 4)); cv.set(x + 1, y, T('bleached', 2))
        cv.vline(x0, y0, 6, T('bleached', 3)); cv.vline(x0 + 1, y0, 6, T('bleached', 2))
    tuft(cv, 14, foot, 3); tuft(cv, 30, foot, 0); tuft(cv, 80, foot, 5); tuft(cv, 96, foot, 1)
    return cv


def props() -> dict[str, Canvas]:
    return {k: clean(cv) for k, cv in _props().items()}


def _props() -> dict[str, Canvas]:
    return {
        'shrine_post': shrine_post(), 'shrine_stone': shrine_stone(),
        'beehive_tiered': beehive(0), 'beehive_skep': beehive(1), 'beehive_box': beehive(2),
        'scarecrow_coat': scarecrow(),
        'cairn_marker': cairn(0), 'cairn_trail': cairn(1), 'cairn_tall': cairn(2),
        'sheepfold': sheepfold(), 'shepherds_hut': shepherds_hut(), 'hay_barn': hay_barn(), 'old_oak': old_oak(),
    }
