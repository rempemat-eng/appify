"""Furniture for the nap hut's inside (living-world plan W4: the house you decorate).

The garden's rules indoors: warm wood lit from the upper left (the window side), soft
fabric in the nap violet and cream, the hearth's glow, a tinted outline. These are
the pieces a player will later place and move (C12); here they furnish a first room.
Run directly for a contact sheet: python3 scripts/art/home_props.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
from materials import MATERIALS, WOOD, STONE, LEAF, RED, GOLD, NAP  # noqa: E402
from garden_props import keep_foot  # noqa: E402

CREAM, PLASTER, WARM = MATERIALS['cream'], MATERIALS['plaster'], MATERIALS['lamplight']
LAVA = MATERIALS['lava']
CREAM_HI = '#FBF5E6'
PAD = 4
SHADE_IN = (20, 16, 24, 90)  # a piece's contact shade on the floorboards


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def wood_box(cv, x0, y0, w, h, top_h, ramp=WOOD):
    """A wooden piece seen from above at the room's angle: a lit top, a front face."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            top = y < y0 + top_h
            c = (ramp[4] if y == y0 else ramp[3]) if top else (ramp[2] if x < x0 + w - 2 else ramp[1])
            if x == x0 and not top:
                c = ramp[3]
            cv.set(x, y, c)
    cv.hline(x0, y0 + top_h, w, ramp[1])


def _mix(a: str, b: str, t: float) -> str:
    ra = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    rb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02X%02X%02X' % tuple(int(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


def grain(cv: Canvas, ramp=WOOD, seed: int = 0, vertical: bool = False) -> Canvas:
    """Wood grain over a finished piece (to-b-1810: the bar measured on the sprite itself):
    every face drawn in the ramp's middle tones gets the figure of the timber in runs of
    three to five pixels along the grain, a half step lighter where the grain rises to the
    light and a half step darker in the late wood, so a door or a top reads as planks of
    real oak and not as a flat fill. Edges and the lit and dark trims are left alone."""
    p = cv.pad
    hexes = {r.upper(): i for i, r in enumerate(ramp)}
    src = cv.img.copy()
    px = src.load()
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            r, g, b, a = px[x + p, y + p]
            if not a:
                continue
            i = hexes.get('#%02X%02X%02X' % (r, g, b))
            if i is None or i in (0, len(ramp) - 1):
                continue
            u, v = (y, x) if vertical else (x, y)
            n = noise2(u // 4, v, seed + 811)
            if n > 0.8:
                cv.set(x, y, _mix(ramp[i], ramp[i + 1], 0.5))
            elif n < 0.18:
                cv.set(x, y, _mix(ramp[i], ramp[i - 1], 0.5))
            elif noise2(u // 3, v // 2, seed + 812) > 0.9:
                cv.set(x, y, _mix(ramp[i], ramp[i - 1], 0.3))  # a knot's ring
            elif noise2(u // 5, v // 2, seed + 813) > 0.86:
                cv.set(x, y, _mix(ramp[i], '#E8B868', 0.22))  # beeswax polish warming the face
            elif noise2(u // 5, v // 2, seed + 814) > 0.88:
                cv.set(x, y, _mix(ramp[i], '#8A8478', 0.25))  # worn grey where hands and feet rub
    return cv


def bed() -> Canvas:
    """A double bed against the bedroom's back wall at the size guide's bed (44 deep with
    a headboard 16; it was 72 tall, over 36 to 50), 42 x 48 in a 64 x 48 box placed where
    the old one was, so its headboard still stands against the back wall: a panelled headboard with turned posts lit on
    the west, two pillows dented where heads lay, the sheet folded back over a patchwork
    quilt in nap violet and cream with its stitching, the quilt falling into shade down
    its east side, a knitted throw at the foot, the footboard, and its contact shade."""
    w, h = 42, 48
    cv = Canvas(w, h, pad=8)
    for x in range(1, w):
        cv.set(x, h - 1, SHADE_IN)
    for y in range(0, 16):  # the headboard: posts, rail, spindles
        for x in range(0, w):
            post = x < 3 or x >= w - 3
            if y < 3:
                c = WOOD[4] if x < w - 3 else WOOD[3]  # its top rail, lit
                if post and y == 0:
                    c = WOOD[4]
            elif post:
                c = WOOD[3] if x in (0, w - 3) else WOOD[2] if x in (1, w - 2) else WOOD[1]
            elif y >= 13:
                c = WOOD[2]  # the bottom rail
            else:
                c = WOOD[2] if (x - 3) % 5 in (0, 1) else WOOD[0]  # spindles and the dark between
                if (x - 3) % 5 == 0 and y < 6:
                    c = WOOD[3]
            cv.set(x, y, c)
    cv.hline(0, 3, w, WOOD[1])
    for y in range(16, h - 6):  # the bed: pillows, sheet, quilt
        for x in range(2, w - 2):
            east = x >= w - 6
            if y < 24:
                c = CREAM_HI if not east else CREAM[3]
            elif y < 27:
                c = CREAM_HI if y == 24 else CREAM[3] if y == 25 else CREAM[1]  # the sheet folded back
            else:
                patch = ((x - 2) // 6 + 2 * ((y - 27) // 6)) % 5
                c = (NAP[3], CREAM[3], NAP[2], GOLD[3], LEAF[3])[patch]  # scraps of five old dresses
                if (x - 2) % 6 == 0 or (y - 27) % 6 == 0:
                    c = NAP[1]  # the stitching
                if east:
                    c = NAP[1] if c in (NAP[3], NAP[2], CREAM[3]) else GOLD[1] if c == GOLD[3] else LEAF[1] if c == LEAF[3] else NAP[0]
            cv.set(x, y, c)
    for px in (11, 30):  # two pillows, dented where heads lay
        for (x, y) in oval(px, 20, 8, 3.6):
            lit = (x - px) + (y - 20) * 1.6 < 0
            cv.set(x, y, '#FFFFFF' if lit else CREAM_HI if (x - px) < 4 else CREAM[3])
        cv.hline(px - 2, 20, 4, CREAM[3])
        cv.hline(px - 7, 23, 15, CREAM[2])  # the pillow's shade on the sheet
    for y in range(h - 13, h - 7):  # the knitted throw over the foot
        for x in range(4, w - 4):
            c = GOLD[3] if (x // 2 + y) % 2 else GOLD[2]
            if x >= w - 8:
                c = GOLD[1]
            cv.set(x, y, c)
    cv.hline(4, h - 13, w - 8, GOLD[4])
    for y in range(h - 6, h - 1):  # the footboard and its posts
        for x in range(0, w):
            post = x < 3 or x >= w - 3
            c = WOOD[4] if y == h - 6 else (WOOD[3] if post and x in (0, w - 3) else WOOD[2] if x < w - 6 else WOOD[1])
            cv.set(x, y, c)
    grain(cv, seed=1, vertical=True)
    return keep_foot(cv, 64, 48)  # the headboard stays against the wall, the bed reaches less far into the room


def nightstand() -> Canvas:
    """A nightstand at knee height (furniture_low, 10 to 22; it was 28), 16 x 21 re-seated
    in the old 22 x 30 box: its top seen from above with a book on it, a lamp with a warm
    pleated shade on a brass stem, a drawer with a knob, and turned feet."""
    w, h = 16, 21
    cv = Canvas(w, h, pad=8)
    cv.hline(1, h - 1, w - 1, SHADE_IN)
    for y in range(0, 6):  # the lamp's shade, pleated, lit on the west
        half = 2 + y // 2
        for x in range(8 - half, 8 + half):
            c = WARM[3] if x < 7 else WARM[2]
            if (x - 8) % 2 == 0 and y > 1:
                c = WARM[2] if x < 7 else WARM[1]  # the pleats
            cv.set(x, y, c)
    cv.hline(4, 6, 8, WARM[1])
    cv.vline(7, 7, 2, GOLD[3]); cv.vline(8, 7, 2, GOLD[1])
    for y in range(9, 12):  # the top
        for x in range(0, w):
            cv.set(x, y, WOOD[4] if y == 9 else WOOD[3])
    cv.hline(10, 9, 4, RED[3]); cv.hline(10, 10, 4, RED[1])  # a book
    for y in range(12, h - 2):  # the front
        for x in range(0, w):
            c = WOOD[2] if x < w - 2 else WOOD[1]
            if y == 12:
                c = WOOD[1]
            cv.set(x, y, c)
    cv.hline(2, 14, w - 4, WOOD[3]); cv.hline(2, 17, w - 4, WOOD[1])  # the drawer's edges
    cv.hline(7, 15, 2, GOLD[4])  # its knob
    for x in (1, 2, w - 3, w - 2):  # feet
        cv.vline(x, h - 2, 2, WOOD[1])
    grain(cv, seed=2)
    return keep_foot(cv, 22, 30)


def wardrobe() -> Canvas:
    """A wardrobe at the size guide's cupboard height (28 to 38; it was 58), 30 x 38
    re-seated in the old 40 x 60 box: a moulded cornice seen from above, two doors each
    with two raised panels (their top and west edges lit, their bottom and east edges in
    shade), brass knobs and a keyhole, the east side turning away, a plinth on feet."""
    w, h = 30, 38
    cv = Canvas(w, h, pad=8)
    cv.hline(1, h - 1, w - 1, SHADE_IN)
    for y in range(0, 4):  # the cornice
        for x in range(0, w):
            cv.set(x, y, WOOD[4] if y == 0 else WOOD[3] if y == 1 else WOOD[2] if y == 2 else WOOD[0])
    for y in range(4, h - 3):  # the carcass
        for x in range(1, w - 1):
            cv.set(x, y, WOOD[2] if x < w - 3 else WOOD[1])
    cv.vline(14, 4, h - 7, WOOD[0]); cv.vline(15, 4, h - 7, WOOD[3])  # the meeting stiles
    for (dx0, dx1) in ((3, 12), (17, 26)):  # two raised panels per door
        for (py0, py1) in ((6, 17), (20, 31)):
            for y in range(py0, py1 + 1):
                for x in range(dx0, dx1 + 1):
                    edge_l, edge_t = x == dx0, y == py0
                    edge_r, edge_b = x == dx1, y == py1
                    c = WOOD[3] if (edge_l or edge_t) else WOOD[1] if (edge_r or edge_b) else WOOD[2]
                    cv.set(x, y, c)
    cv.hline(11, 18, 2, GOLD[4]); cv.hline(17, 18, 2, GOLD[4])  # the knobs
    cv.vline(13, 21, 2, WOOD[0])  # the keyhole
    for y in range(h - 3, h - 1):  # the plinth
        cv.hline(0, y, w, WOOD[3] if y == h - 3 else WOOD[1])
    for x in (1, 2, w - 3, w - 2):
        cv.set(x, h - 1, WOOD[0])
    grain(cv, seed=3, vertical=True)
    return keep_foot(cv, 40, 60)


def fireplace(flicker: int = 0) -> Canvas:
    """The hearth at the size guide's fireplace (a mantel at 30, the breast above; it was
    57 tall, over 30 to 48), 48 x 44 re-seated in the old 64 x 56 box: a fieldstone
    chimney breast, an oak mantel shelf at 30 with a candle, a little clock and a jar of
    spills on it, the firebox's arch of dressed stones lit on the west, the fire burning
    low on two logs on fire dogs (`flicker` 1 or 2 leans and swells the flames), soot over
    the arch, and the hearthstone flags in front."""
    w, h = 48, 44
    cv = Canvas(w, h, pad=8)
    floor = h - 1
    mantel = floor - 30
    detail.stones(cv, 3, 0, w - 6, floor - 4, STONE, seed=61, course=4)
    for y in range(mantel - 2, mantel + 2):  # the mantel shelf: its top, then its front edge
        for x in range(1, w - 1):
            cv.set(x, y, WOOD[4] if y == mantel - 2 else WOOD[3] if y == mantel - 1 else WOOD[2] if x < w - 4 else WOOD[1])
    cv.hline(1, mantel + 2, w - 2, WOOD[0])
    cv.vline(8, mantel - 7, 5, CREAM_HI); cv.vline(9, mantel - 7, 5, CREAM[3]); cv.set(8, mantel - 8, WARM[3])  # a candle
    for (x, y) in disc(32, mantel - 6, 3.2):  # a little clock
        cv.set(x, y, GOLD[3] if x + y < 32 + mantel - 6 else GOLD[2])
    for (x, y) in disc(32, mantel - 6, 1.6):
        cv.set(x, y, CREAM_HI)
    cv.hline(32, mantel - 6, 2, WOOD[0])
    cv.vline(40, mantel - 6, 4, '#6A8AA8'); cv.vline(41, mantel - 6, 4, '#4A6A88')  # a jar of spills
    cv.hline(40, mantel - 7, 2, WOOD[4])
    cx = w // 2
    arch = {(x, y) for (x, y) in disc(cx, mantel + 10, 10) if y >= mantel + 6} | rect_set(cx - 10, mantel + 10, 20, floor - 4 - mantel - 10)
    fx, fy, sc = ((0, 0, 1.0), (-1, -1, 1.12), (1, 0, 0.92))[flicker]
    for (x, y) in arch:
        d = math.hypot(x - cx - fx, (y - (floor - 7) - fy) * (1.3 if flicker == 1 else 1.0)) / sc
        c = LAVA[5] if d < 2.5 else LAVA[4] if d < 4.5 else LAVA[3] if d < 7 else '#2A1A14' if d < 11 else '#1A1210'
        cv.set(x, y, c)
    for (x, y) in arch:  # the arch's dressed stones, lit on the west
        if (x, y - 1) not in arch or (x - 1, y) not in arch or (x + 1, y) not in arch:
            cv.set(x, y, STONE[4] if x < cx else STONE[1])
    for x in range(cx - 6, cx + 7):
        cv.set(x, mantel + 4, STONE[0])  # soot over the arch
    for (x0) in (cx - 6, cx + 1):  # logs on the fire dogs
        cv.hline(x0, floor - 6, 6, WOOD[2]); cv.hline(x0, floor - 5, 6, WOOD[1])
    cv.vline(cx - 8, floor - 6, 2, MATERIALS['iron'][1]); cv.vline(cx + 7, floor - 6, 2, MATERIALS['iron'][1])
    detail.stones(cv, 0, floor - 3, w, 4, STONE, seed=62, course=2)  # the hearthstone flags
    grain(cv, seed=5)
    return keep_foot(cv, 64, 56)


def armchair() -> Canvas:
    """A deep armchair at the size guide's armchair (seat 7, back 20; it was 35 x 34),
    24 x 23 re-seated in the old 40 x 40 box: a buttoned back in faded red, rolled arms
    lit along their tops, a plump seat cushion, a skirt to the floor and turned feet, a
    cream plaid blanket over the east arm."""
    w, h = 24, 23
    cv = Canvas(w, h, pad=8)
    cv.hline(1, h - 1, w - 1, SHADE_IN)
    for y in range(0, 12):  # the back, rounded at the top
        for x in range(3, w - 3):
            if y < 2 and (x < 5 or x > w - 6):
                continue
            c = RED[3] if x < 11 else RED[2]
            if y == 0:
                c = RED[4] if x < 12 else RED[3]
            cv.set(x, y, c)
    for bx in (6, 10, 14):  # a row of buttons across the back
        cv.hline(bx, 6, 2, RED[1])
    for (ax, lit) in ((0, True), (w - 5, False)):  # the arms
        for y in range(6, h - 3):
            for x in range(ax, ax + 5):
                c = (RED[4] if lit else RED[2]) if y < 8 else (RED[3] if lit else RED[1])
                if x == ax + 4 and lit or x == ax and not lit:
                    c = RED[1] if lit else RED[0]
                cv.set(x, y, c)
    for y in range(12, 16):  # the seat cushion
        for x in range(5, w - 5):
            cv.set(x, y, RED[4] if y == 12 else RED[3] if x < 13 else RED[2])
    cv.hline(5, 16, w - 10, RED[1])
    for y in range(16, h - 2):  # the skirt
        for x in range(1, w - 1):
            cv.set(x, y, RED[2] if x < w - 4 else RED[1])
    for x in (2, 3, w - 4, w - 3):
        cv.vline(x, h - 2, 2, WOOD[1])
    for y in range(6, 16):  # the plaid blanket over the east arm
        for x in range(w - 6, w):
            c = CREAM_HI if (x + y // 2) % 3 else CREAM[2]
            if (y - 6) % 4 == 0:
                c = NAP[2]
            cv.set(x, y, c)
    grain(cv, ramp=RED, seed=9)  # the velvet's nap, brushed this way and that
    return keep_foot(cv, 40, 40)


def pet_bed() -> Canvas:
    """The companion's bed by the fire, 38 x 24: a round woven basket with a soft
    cushion and a small blanket, where naps happen."""
    w, h = 38, 24
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(19, 13, 17, 10):
        k = (x - 2) / 34
        c = WOOD[4] if k < 0.3 else WOOD[3] if k < 0.7 else WOOD[2]
        if (x + y * 2) % 4 == 0:
            c = WOOD[2] if c != WOOD[2] else WOOD[1]  # the weave
        cv.set(x, y, c)
    for (x, y) in oval(19, 12, 13, 7):
        cv.set(x, y, NAP[3] if x + y < 30 else NAP[2])
    for (x, y) in oval(24, 13, 6, 3):
        cv.set(x, y, CREAM_HI if (x + y) % 3 else CREAM[3])
    return cv


def dining_table() -> Canvas:
    """A round kitchen table, 56 x 40, with a checked cloth, a teapot and two cups, and
    two chairs tucked in."""
    w, h = 56, 40
    cv = Canvas(w, h, pad=PAD)
    for (cx) in (8, w - 9):  # chairs
        for y in range(10, 30):
            for x in range(cx - 4, cx + 4):
                cv.set(x, y, WOOD[3] if y < 14 else WOOD[2] if x < cx + 2 else WOOD[1])
    for (x, y) in oval(28, 18, 20, 12):
        check = ((x // 4) + (y // 4)) % 2
        k = (x - 8) / 40 + (y - 6) / 24
        c = ('#E8E0D0' if check else RED[3]) if k < 1.1 else ('#C8C0B0' if check else RED[2])
        cv.set(x, y, c)
    for y in range(30, h - 2):
        cv.hline(26, y, 4, WOOD[1])
    for (x, y) in oval(28, 15, 5, 4):
        cv.set(x, y, '#6A8AA8' if x < 28 else '#4A6A88')
    cv.set(34, 13, '#4A6A88')
    for (mx) in (18, 38):
        for (x, y) in disc(mx, 19, 2):
            cv.set(x, y, CREAM_HI)
        cv.set(mx, 19, WOOD[1])
    return cv


def kitchen() -> Canvas:
    """The kitchen run along the living room's back wall, 104 x 50: a shelf of jars with
    their lids and labels on the wall; a wooden counter, its worktop lit along the front
    edge, with herbs in clay pots, a stone sink with a brass tap and a drip, a chopping
    board with a loaf on it; cupboard doors below with raised panels and knobs; an iron
    stove with its hotplate, the firebox door glowing, a towel on its rail and the kettle
    on the hob."""
    w, h = 104, 50
    cv = Canvas(w, h, pad=PAD)
    IRON_ = MATERIALS['iron']
    for x in range(3, w - 2):
        cv.set(x, h - 1, SHADE_IN)
    cv.hline(4, 12, w - 8, WOOD[3]); cv.hline(4, 13, w - 8, WOOD[1])  # the shelf
    for x in (8, w - 10):  # its brackets
        cv.vline(x, 14, 3, WOOD[1])
    for k in range(10):  # jars: a lid, the glass lit on the west, a label
        jx = 8 + k * 9
        col, dark = ((GOLD[3], GOLD[2]), (RED[3], RED[2]), (LEAF[3], LEAF[2]), (CREAM_HI, CREAM[3]), (NAP[3], NAP[2]))[k % 5]
        for y in range(5, 12):
            for x in range(jx, jx + 5):
                cv.set(x, y, col if x < jx + 3 else dark)
        cv.hline(jx, 4, 5, WOOD[4]); cv.hline(jx, 3, 5, WOOD[3])
        cv.hline(jx + 1, 8, 3, CREAM_HI); cv.hline(jx + 1, 9, 3, CREAM[3])
    for y in range(20, 28):  # the worktop
        for x in range(2, 72):
            cv.set(x, y, WOOD[4] if y == 20 else WOOD[3] if y < 27 else WOOD[2])
    for k in range(3):  # herbs in clay pots
        px = 6 + k * 7
        cv.hline(px, 24, 4, '#C8743E'); cv.hline(px, 25, 4, '#A85A2E')
        for (x, y) in oval(px + 1.5, 22, 2.4, 1.8):
            cv.set(x, y, LEAF[4] if x < px + 2 else LEAF[2])
    for y in range(21, 27):  # the stone sink
        for x in range(34, 52):
            c = STONE[3] if y == 21 or x == 34 else STONE[1] if y == 26 or x == 51 else '#6A8AA8' if y > 23 else STONE[2]
            cv.set(x, y, c)
    cv.vline(42, 17, 4, GOLD[3]); cv.hline(42, 17, 3, GOLD[3]); cv.vline(44, 18, 2, GOLD[2])  # the brass tap
    cv.vline(44, 22, 2, '#C6DDEE')  # a drip
    cv.hline(56, 23, 12, WOOD[4]); cv.hline(56, 24, 12, WOOD[3]); cv.hline(56, 25, 12, WOOD[1])  # a chopping board
    for (x, y) in oval(61, 22, 4, 2):
        cv.set(x, y, '#D8A060' if x < 61 else '#B87E44')  # a loaf on it
    for y in range(28, h - 2):  # the cupboards
        for x in range(2, 72):
            cv.set(x, y, WOOD[2] if x < 70 else WOOD[1])
    for (d0, d1) in ((4, 20), (22, 38), (40, 56), (58, 69)):
        cv.hline(d0, 30, d1 - d0, WOOD[3]); cv.hline(d0, h - 5, d1 - d0, WOOD[1])
        cv.vline(d0, 30, h - 34, WOOD[3]); cv.vline(d1, 30, h - 34, WOOD[1])
        cv.hline(d1 - 3, 36, 2, GOLD[4])
    cv.hline(2, h - 2, 70, WOOD[1])
    for y in range(20, h - 1):  # the stove
        for x in range(74, w - 4):
            c = IRON_[3] if y < 23 else IRON_[2] if x < w - 8 else IRON_[1]
            cv.set(x, y, c)
    cv.hline(76, 21, 10, IRON_[4]); cv.hline(88, 21, 8, IRON_[4])  # the hotplate rings
    for (x, y) in rect_set(80, 33, 16, 9):  # the firebox door, its glow through the grille
        cv.set(x, y, LAVA[3] if (x % 3) and y > 34 else IRON_[1])
    cv.hline(80, 32, 16, IRON_[4])
    cv.hline(76, 29, 22, GOLD[3])  # the towel rail
    for y in range(29, 36):
        cv.hline(84, y, 6, '#E8E0D0' if (y % 3) else RED[3])  # a towel on it
    for (x, y) in oval(86, 16, 6, 4):  # the kettle
        cv.set(x, y, '#C8803A' if x < 86 else '#9A5A28')
    cv.hline(90, 14, 3, '#9A5A28'); cv.hline(84, 12, 5, '#5E3A24')
    grain(cv, seed=8)
    return cv


def bookcase() -> Canvas:
    """A bookcase at the size guide's cupboard height (it was 52, over 28 to 38), 32 x 37
    re-seated in the old 40 x 54 box: its top seen from above with a box of letters, sides
    lit on the west, four shelves of books with their spines in two tones (lit edge and
    body), some leaning, a jar and a little box among them, and a plinth."""
    w, h = 32, 37
    cv = Canvas(w, h, pad=8)
    cv.hline(1, h - 1, w - 1, SHADE_IN)
    for y in range(0, 3):
        cv.hline(0, y, w, WOOD[4] if y == 0 else WOOD[3])
    for y in range(3, h - 2):
        cv.hline(0, y, 2, WOOD[3]); cv.hline(w - 2, y, 2, WOOD[1])
    cols = [(RED[3], RED[2]), (GOLD[3], GOLD[2]), (NAP[3], NAP[2]), (LEAF[3], LEAF[2]), ('#7E9CB8', '#5A7A98'), (CREAM_HI, CREAM[3])]
    for shelf in range(4):
        y0 = 3 + shelf * 8
        for y in range(y0, y0 + 7):
            cv.hline(2, y, w - 4, WOOD[0])  # the shelf's dark back
        x, k = 3, shelf * 2
        while x < w - 4:
            bw = 2 + (k * 7) % 2
            bh = 5 + (k * 5) % 2
            if (shelf, k % 6) in ((1, 3), (3, 1)):  # a jar or a little box in place of books
                cv.hline(x, y0 + 3, 3, '#7E9CB8'); cv.hline(x, y0 + 4, 3, '#7E9CB8'); cv.hline(x, y0 + 5, 3, '#5A7A98')
                cv.hline(x, y0 + 6, 3, '#5A7A98')
                x += 4; k += 1
                continue
            lit, body = cols[k % len(cols)]
            for yy in range(y0 + 7 - bh, y0 + 7):
                cv.set(x, yy, lit)
                for xx in range(x + 1, min(x + bw, w - 3)):
                    cv.set(xx, yy, body)
            x += bw + (1 if k % 5 == 4 else 0)
            k += 1
        cv.hline(2, y0 + 7, w - 4, WOOD[3])  # the shelf's lit front edge
    for y in range(h - 2, h):
        cv.hline(0, y, w, WOOD[2] if y == h - 2 else WOOD[1])
    cv.hline(20, 0, 6, '#7E9CB8'); cv.hline(20, 1, 6, '#5A7A98')  # a box of letters on top
    grain(cv, seed=4, vertical=True)
    return keep_foot(cv, 40, 54)


def plant_tall() -> Canvas:
    """A tall leafy plant in a clay pot, 28 x 46."""
    w, h = 28, 46
    cv = Canvas(w, h, pad=PAD)
    for k in range(9):
        a = math.pi * (0.15 + 0.7 * k / 8)
        for t in range(18):
            x = 14 + math.cos(a) * t * 0.8
            y = 30 - math.sin(a) * t * 1.2 + (t / 18) ** 2 * 6
            for d in (-1, 0, 1):
                cv.set(int(x) + d, int(y), LEAF[4] if d < 0 and t > 4 else LEAF[3] if d == 0 else LEAF[2])
    for y in range(32, h - 2):
        hw = 7 - (y - 32) // 4
        for x in range(14 - hw, 14 + hw):
            cv.set(x, y, '#C8743E' if x < 13 else '#A85A2E')
    cv.hline(6, 32, 16, '#D88A50')
    return cv


def rug_chest() -> Canvas:
    """The painted chest for keepsakes at the size guide's chest (16 to 28 wide; it was
    34), 26 x 18 re-seated in the old 36 x 26 box: a blue lid seen from above with flowers
    painted on it, the front with iron straps and a brass lock plate, a lit lid edge and
    its shade, and little bracket feet."""
    w, h = 26, 18
    BL = ['#2A3A5A', '#3E5478', '#56709A', '#7290BA', '#94B0D4']
    cv = Canvas(w, h, pad=8)
    cv.hline(1, h - 1, w - 1, SHADE_IN)
    for y in range(0, 6):  # the lid
        for x in range(0, w):
            cv.set(x, y, BL[4] if y == 0 else BL[3] if x < w - 3 else BL[2])
    for (fx, c, c2) in ((6, RED[3], RED[2]), (12, GOLD[3], GOLD[2]), (18, CREAM_HI, CREAM[3])):  # painted flowers
        cv.hline(fx, 2, 2, c); cv.hline(fx, 3, 2, c2)
        cv.hline(fx + 2, 3, 2, LEAF[3])
    cv.hline(0, 6, w, BL[1])
    for y in range(7, h - 2):  # the front
        for x in range(0, w):
            cv.set(x, y, BL[2] if x < w - 3 else BL[1])
    IRON_ = MATERIALS['iron']
    for x0 in (3, w - 5):  # iron straps over lid and front
        cv.vline(x0, 0, h - 2, IRON_[2]); cv.vline(x0 + 1, 0, h - 2, IRON_[1])
    cv.hline(11, 8, 4, GOLD[3]); cv.hline(11, 9, 4, GOLD[2]); cv.hline(12, 10, 2, WOOD[0])  # the lock plate
    for x in (1, 2, w - 3, w - 2):
        cv.vline(x, h - 2, 2, BL[0])
    grain(cv, ramp=BL, seed=6)
    return keep_foot(cv, 36, 26)


def window_seat() -> Canvas:
    """A cushioned bench, 64 x 22: violet cushions on a wooden box, a book left open."""
    w, h = 64, 22
    cv = Canvas(w, h, pad=PAD)
    wood_box(cv, 2, 8, w - 4, 12, 3)
    for cx in (14, 32, 50):
        for (x, y) in oval(cx, 7, 9, 4):
            cv.set(x, y, NAP[3] if x < cx else NAP[2])
    for (x, y) in rect_set(36, 4, 10, 4):
        cv.set(x, y, CREAM_HI if x < 41 else CREAM[3])
    cv.vline(41, 4, 4, WOOD[1])
    return cv


def desk() -> Canvas:
    """A writing desk under the bedroom window, 44 x 34: its top seen from above with the
    grain running along it, letters and an open notebook, an inkpot with a pen in it and
    a little lamp lit warm; the front with three drawers and their brass pulls, the legs
    lit on the west, and a round stool tucked in front."""
    w, h = 44, 34
    cv = Canvas(w, h, pad=PAD)
    for x in range(3, w - 1):
        cv.set(x, h - 8, SHADE_IN)
    for y in range(6, 14):  # the top
        for x in range(2, w - 2):
            c = WOOD[4] if y == 6 else WOOD[3]
            if (x * 3 + y * 7) % 23 == 0 or ((y == 9) and x % 9 in (0, 1)):
                c = WOOD[2]  # the grain
            cv.set(x, y, c)
    for (x, y) in rect_set(6, 8, 10, 5):  # letters, one over another
        cv.set(x, y, CREAM_HI if x < 14 else CREAM[3])
    cv.hline(7, 10, 6, CREAM[2]); cv.hline(7, 12, 5, CREAM[2])
    cv.hline(18, 9, 8, CREAM_HI); cv.hline(18, 10, 8, CREAM_HI); cv.hline(18, 11, 8, CREAM[3]); cv.vline(22, 9, 3, CREAM[1])  # an open notebook
    cv.hline(28, 8, 3, '#2E3A48'); cv.hline(28, 9, 3, '#1E2630'); cv.vline(30, 5, 3, CREAM_HI)  # an inkpot and its pen
    for (x, y) in oval(37, 5, 4, 2.6):  # the lamp's shade
        cv.set(x, y, WARM[3] if x < 37 else WARM[2])
    cv.vline(37, 8, 2, GOLD[3]); cv.hline(35, 10, 4, GOLD[2])
    for y in range(14, 24):  # the front and its drawers
        for x in range(2, w - 2):
            cv.set(x, y, WOOD[2] if x < w - 5 else WOOD[1])
    cv.hline(2, 14, w - 4, WOOD[1])
    for (d0, d1) in ((4, 15), (17, 27), (29, 39)):
        cv.hline(d0, 16, d1 - d0, WOOD[3]); cv.hline(d0, 21, d1 - d0, WOOD[1])
        cv.vline(d0, 16, 6, WOOD[3]); cv.vline(d1, 16, 6, WOOD[1])
        cv.hline((d0 + d1) // 2 - 1, 18, 2, GOLD[4])
    for x in (3, 4, w - 5, w - 4):  # legs
        cv.vline(x, 24, 3, WOOD[3] if x < 10 else WOOD[1])
    for (x, y) in oval(22, 29, 6, 2.4):  # the stool's seat, then its legs
        cv.set(x, y, WOOD[4] if y < 29 and x < 22 else WOOD[3] if x < 25 else WOOD[2])
    for x in (18, 26):
        cv.vline(x, 31, 2, WOOD[1])
    grain(cv, seed=7)
    return cv

def coat_rack() -> Canvas:
    """A coat stand by the door, 18 x 42: a turned post with pegs, a scarf and a coat
    hanging from them, and a round foot."""
    w, h = 18, 42
    cv = Canvas(w, h, pad=PAD)
    for y in range(3, h - 3):
        cv.set(8, y, WOOD[3]); cv.set(9, y, WOOD[1])
    for (x, y) in disc(8.5, 2, 1.6):
        cv.set(x, y, WOOD[4])
    for (x0, dx) in ((7, -1), (10, 1)):
        for t in range(4):
            cv.set(x0 + dx * t, 6 - t // 2, WOOD[3])
    for y in range(7, 22):  # a long coat, shaded on its right
        for x in range(3, 9):
            if x < 4 + (y - 7) // 6:
                continue
            cv.set(x, y, '#5A7A8A' if x < 6 else '#3E5A6A')
    cv.hline(5, 7, 3, '#2E4652')
    for y in range(6, 16):  # a scarf
        cv.set(11 + (y > 10), y, RED[3]); cv.set(12 + (y > 10), y, RED[2])
    for (x, y) in oval(8.5, h - 3, 6, 1.8):
        cv.set(x, y, WOOD[3] if x < 9 else WOOD[1])
    return cv


def boots() -> Canvas:
    """A pair of muddy boots on a little mat, 18 x 12."""
    w, h = 18, 12
    cv = Canvas(w, h, pad=PAD)
    cv.rect(1, 8, 16, 3, '#8A6A3E'); cv.hline(1, 8, 16, '#B8945A')
    for bx in (3, 10):
        for y in range(1, 9):
            cv.set(bx, y, '#6E4A2E'); cv.set(bx + 1, y, '#5A3A24'); cv.set(bx + 2, y, '#4A2E1C')
        cv.hline(bx, 8, 5, '#4A2E1C'); cv.hline(bx + 3, 7, 2, '#5A3A24')
        cv.hline(bx, 1, 3, '#8A6040')
    return cv


def side_table() -> Canvas:
    """A small round side table, 22 x 26, with a lamp lit warm and a cup of tea."""
    w, h = 22, 26
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(11, 14, 9, 3):
        cv.set(x, y, WOOD[4] if y < 14 and x < 12 else WOOD[3])
    cv.hline(3, 17, 17, WOOD[1])
    for y in range(18, h - 1):
        cv.set(10, y, WOOD[2]); cv.set(11, y, WOOD[1])
    cv.hline(6, h - 2, 10, WOOD[1])
    for y in range(3, 9):  # the lamp's shade
        for x in range(4 + (8 - y) // 2, 12 - (8 - y) // 2):
            cv.set(x, y, WARM[3] if x < 8 else WARM[2])
    cv.vline(7, 9, 4, GOLD[2]); cv.hline(5, 12, 5, GOLD[3])
    cv.rect(14, 10, 3, 3, CREAM[3]); cv.set(17, 11, CREAM[2]); cv.set(15, 10, '#A8703A')  # tea
    return cv


def watering_can() -> Canvas:
    """A green watering can, 20 x 14, for the sunroom plants."""
    w, h = 20, 14
    cv = Canvas(w, h, pad=PAD)
    GR = ['#2E5A40', '#447A50', '#62995E', '#8CBB76']
    for y in range(5, h - 1):
        for x in range(4, 13):
            cv.set(x, y, GR[3] if x < 6 else GR[2] if x < 11 else GR[1])
    cv.hline(4, 5, 9, GR[3])
    for t in range(6):  # the spout
        cv.set(13 + t, 9 - t // 2, GR[1]); cv.set(13 + t, 10 - t // 2, GR[0])
    cv.hline(18, 6, 2, GR[3])
    for x in range(5, 12):  # the handle
        cv.set(x, 2 + abs(x - 8) // 2, GR[1])
    return cv


def props() -> dict[str, Canvas]:
    return {
        'bed': bed(), 'nightstand': nightstand(), 'wardrobe': wardrobe(), 'fireplace': fireplace(),
        'fireplace_f1': fireplace(1), 'fireplace_f2': fireplace(2), 'armchair': armchair(), 'pet_bed': pet_bed(), 'dining_table': dining_table(), 'kitchen': kitchen(),
        'bookcase': bookcase(), 'plant_tall': plant_tall(), 'keepsake_chest': rug_chest(),
        'window_seat': window_seat(), 'desk': desk(), 'coat_rack': coat_rack(), 'boots': boots(),
        'side_table': side_table(), 'watering_can': watering_can(),
    }


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (126, 117, 123, 255))
    x = pad
    for v in items.values():
        out.alpha_composite(v.img, (x, height - pad - v.h))
        x += v.w + pad
    out.resize((width * 3, height * 3), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else '/tmp/home_props.png')
