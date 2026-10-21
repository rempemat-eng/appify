"""The wayside kit for the rebuilt home valley, wave 1 batch 1 (Claude B; docs/vision/regions/props.md, the
home valley's brief on PR #96; Claude A's to-b-2245): the things a walker meets on every
route, drawn to the newest standard from the first stroke.

- Colours only from the house palette's ramps (art/house-palette.json on PR #121: each
  material a six-tone ramp, 0 the shade into 5 the sun, with warm and cool siblings);
  the copy below is that file's values, so the sprites stay on the palette when it lands.
- Light from the upper left: west faces and tops lit, east faces a step or two down.
- Sizes from the size guide (adult 25 px): bench 28 to 36 long with its seat at 7 and its
  back at 13; a signpost's arms at eye height; a field gate 12 to 22; a trough 8 to 14
  at an animal's mouth; a well's wall 10 to 14 under its winch.
- Each footing spans whole 8 px cells of the soft grid (its lowest rows 8n wide, or one
  or two more with the outline).
- Texture from parts and 2 to 4 px clusters: timber grain as runs that swap between a
  ramp and its siblings, stones laid in courses, never single-pixel noise.
- Every part has a reason: what holds it up, what it is for, who mended it.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval  # noqa: E402
import detail  # noqa: E402

PAD = 12

# The house palette's ramps (art/house-palette.json, PR #121), the materials this wave uses.
H = {
    'timber': ['#2E0A0D', '#50261D', '#70432F', '#8E6242', '#A87C52', '#BA9569'],
    'timber_warm': ['#350F0A', '#572C18', '#774A29', '#966A3D', '#AF854F', '#C29E69'],
    'timber_cool': ['#2F0912', '#4D2220', '#6B3D30', '#865840', '#A0724F', '#B38B64'],
    'bleached': ['#523738', '#74564E', '#957765', '#B4987C', '#CFB38F', '#E6CCA4'],
    'stone': ['#332937', '#514850', '#70676A', '#8E8782', '#ABA194', '#C5B8A4'],
    'stone_warm': ['#3B2F3B', '#5A4E54', '#796E6D', '#988E85', '#B5A897', '#CFC0A8'],
    'stone_cool': ['#2D212F', '#4B3F48', '#695E60', '#877D78', '#A49689', '#BDAE99'],
    'iron': ['#1A132D', '#2E2943', '#424056', '#565868', '#737078', '#8E8583'],
    'iron_warm': ['#1C112F', '#322A47', '#48445D', '#5F5E72', '#7D7682', '#988C8C'],
    'leaf': ['#002B1A', '#194B28', '#3A6B3A', '#5C8A4C', '#83A15A', '#A8B471'],
    'leaf_warm': ['#093213', '#2B5120', '#4B712F', '#6D9041', '#93A751', '#B6BA6D'],
    'grass': ['#234325', '#436333', '#648445', '#86A458', '#ACBC69', '#CFCF84'],
    'earth': ['#261118', '#432B2A', '#5F463D', '#7A6250', '#947B60', '#AA9373'],
    'water': ['#0E2058', '#1E427A', '#336499', '#4C86B4', '#6BA2C2', '#92B8C5'],
    'plaster': ['#7B635D', '#9E8675', '#C0A98D', '#E0CCA6', '#F7DFB3', '#FEF2DC'],
    'slate': ['#1F1A3C', '#38395A', '#535876', '#6E7890', '#8E91A1', '#ACA7AA'],
    'brass': ['#5D2D0A', '#814D15', '#A36E26', '#C2903C', '#DAAD54', '#EFC67A'],
    'berry': ['#34001F', '#630735', '#8E2348', '#B2465A', '#CE6364', '#DD8472'],
    'clay': ['#3E0114', '#681921', '#8C3931', '#AE5A42', '#C8764F', '#D79466'],
}
SHADE = (24, 18, 30, 100)  # a prop's contact shade on the ground


def T(ramp: str, i: int) -> str:
    r = H[ramp]
    return r[max(0, min(len(r) - 1, i))]


def wood(x: int, y: int, i: int, seed: int, along_x: bool = True, family: str = 'timber', run: int = 4) -> str:
    """One pixel of a timber face at tone i: the grain runs along the member in runs of 3
    to 5 pixels, each run from the timber ramp or one of its siblings (warm where the
    heartwood shows, cool in the sapwood), now and then a half step up or down; all on
    the palette."""
    u, v = (x, y) if along_x else (y, x)
    n = noise2(u // run, v, seed + 901)
    fam = family if n < 0.55 else family + '_warm' if n < 0.8 else family + '_cool'
    if family == 'bleached' and fam == 'bleached_cool':
        fam = 'stone_warm'  # oak left out for decades goes silver-grey
    if fam not in H:
        fam = family
    m = noise2(u // run, v, seed + 902)  # on the same runs as the sibling swap, so no run is one pixel
    if m > 0.86:
        i += 1
    elif m < 0.1:
        i -= 1
    return T(fam, i)


def stone_px(x: int, y: int, i: int, seed: int) -> str:
    n = noise2(x // 5, y // 3, seed + 903)  # a stone's worth of one sibling, not a speckle
    fam = 'stone' if n < 0.5 else 'stone_warm' if n < 0.78 else 'stone_cool'
    return T(fam, i)


def post(cv: Canvas, x: int, top: int, foot: int, width: int = 3, seed: int = 0, cap: bool = True, east: int = 2,
         family: str = 'timber'):
    """A squared timber post, lit on its west face, its east face in shade, the grain
    running up it; a weathered top and a darker foot where the damp climbs."""
    for y in range(top, foot):
        for k in range(width):
            i = 4 if k == 0 else 3 if k < width - 1 else east
            if y > foot - 4 and k < width - 1:
                i -= 1  # damp at the foot (the shaded face is dark enough already)
            cv.set(x + k, y, wood(x + k, y, i, seed, along_x=False, family=family))
    if cap:
        cv.hline(x, top, width, T(family, 5))


def plank(cv: Canvas, x0: int, y0: int, w: int, h: int, seed: int = 0, top_lit: bool = True, family: str = 'timber'):
    """A plank or rail seen from the front: its upper arris lit, its face, its lower edge
    in shade; the grain running along it."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            r = y - y0
            i = 5 if (r == 0 and top_lit) else 2 if r == h - 1 else 3 if r < h // 2 + 1 else 2
            if x >= x0 + w - 2 and 0 < r < h - 1:
                i -= 1  # the east end turning away
            cv.set(x, y, wood(x, y, i, seed, family=family))


def ivy(cv: Canvas, x: int, y0: int, y1: int, seed: int = 0):
    """Ivy climbing a post from the ground: leaves in pairs of two-pixel clusters either
    side of the stem, lit on their upper west, thinning as it climbs."""
    for y in range(y1, y0, -3):
        side = -1 if (y // 3 + seed) % 2 else 1
        if noise2(x, y, seed + 905) > 0.25 + (y1 - y) * 0.03:
            cv.set(x + side, y, T('leaf', 4)); cv.set(x + side, y + 1, T('leaf', 2))
            cv.set(x + side * 2, y + 1, T('leaf', 3))
        cv.set(x, y + 2, T('leaf', 1))


def shade_under(cv: Canvas, x0: int, x1: int, y: int):
    for x in range(x0, x1):
        cv.set(x, y, SHADE)


def tuft(cv: Canvas, x: int, y: int, kind: int = 0):
    detail.grass_tuft(cv, x, y, kind, H['grass'], 2)


# ---- benches -------------------------------------------------------------------------

def bench_plank(variant: int = 0) -> Canvas:
    """A field-edge bench of oak planks (the size guide's bench: 32 long, the seat 7 above
    the ground, the back 13): two thick seat planks seen from a little above with the gap
    between them, a back rail on two uprights, legs morticed through the seat and pegged,
    a stretcher low between them; the grain along every member, the seat silvered where it
    is sat on, lichen on the north end. Variant 1 carries a brass plaque on its back rail (a
    memorial bench) and a newer, warmer seat plank where one was replaced."""
    w, h = 32, 14
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    for lx in (3, w - 6):  # the legs, back pair then front pair
        post(cv, lx, foot - 8, foot, 3, seed=11 + lx)
    plank(cv, 3, foot - 4, w - 6, 2, seed=12)  # the stretcher
    for ux in (2, w - 5):  # the back's uprights, rising behind the seat
        post(cv, ux, 0, foot - 6, 3, seed=13 + ux)
    plank(cv, 1, 0, w - 2, 3, seed=14)  # the back rail
    for y in range(5, 8):  # the seat: two planks seen from above, the gap dark between them
        for x in range(0, w):
            i = 5 if y == 5 else 4 if y == 6 else 3
            if y == 7:
                i = 1  # the gap
            fam = 'bleached' if 8 <= x <= 23 and y < 7 else 'timber'
            if variant == 1 and y == 8:
                fam = 'timber_warm'
            cv.set(x, y, T(fam, i) if fam == 'bleached' else wood(x, y, i, 15))
    for y in range(8, 10):
        for x in range(0, w):
            fam = 'timber_warm' if variant == 1 else 'timber'
            i = 4 if y == 8 else 2
            if x >= w - 2:
                i -= 1
            cv.set(x, y, wood(x, y, i, 16, family='timber') if fam == 'timber' else T(fam, i))
    for x in range(0, w):
        cv.set(x, 10, T('timber', 1))  # the seat's front edge in its own shade
    for px in (4, w - 5):  # the pegs through the seat, end grain lit
        cv.hline(px, 6, 2, T('timber_warm', 2))
    for (lx, ly) in ((1, 1), (2, 1), (1, 2)):  # lichen on the north end of the back rail
        cv.set(lx, ly, T('leaf_warm', 4))
    if variant == 1:  # the memorial plaque, screwed to the back rail
        cv.hline(13, 0, 6, T('brass', 4)); cv.hline(13, 1, 6, T('brass', 3)); cv.hline(13, 2, 6, T('brass', 1))
        cv.set(13, 1, T('brass', 5)); cv.set(18, 1, T('brass', 2))
    tuft(cv, 0, foot, 3); tuft(cv, w - 1, foot, 1)
    return cv


def bench_stone() -> Canvas:
    """A stone bench at a viewpoint, 32 long: a dressed slab on two blocks, a lower slab set
    upright behind as its back, the seat worn smooth and lighter where people sit, moss in
    the joints and on the back's shaded top, and grass grown up round the blocks."""
    w, h = 32, 14
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    for y in range(0, 6):  # the back slab, its top lit and its face in half light
        for x in range(1, w - 1):
            i = 5 if y == 0 else 4 if y == 1 else 3
            if x >= w - 3:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, 21))
    for x in range(3, w - 3, 7):
        cv.hline(x, 0, 2, T('leaf', 3))  # moss along its top
    for y in range(6, 9):  # the seat slab from above, worn pale in the middle
        for x in range(0, w):
            i = 5 if y == 6 else 4
            if 9 <= x <= 22 and y > 6:
                i = 5
            cv.set(x, y, stone_px(x, y, i, 22))
    for y in range(9, 11):
        for x in range(0, w):
            cv.set(x, y, stone_px(x, y, 3 if y == 9 else 2, 23) if x < w - 2 else T('stone', 1))
    cv.hline(0, 11, w, T('stone', 1))
    for bx in (3, w - 9):  # the two blocks under it, coursed
        for y in range(11, foot):
            for x in range(bx, bx + 6):
                i = 3 if x < bx + 2 else 2 if x < bx + 5 else 1
                cv.set(x, y, stone_px(x, y, i, 24))
    cv.hline(5, 12, 2, T('leaf', 2))
    tuft(cv, 2, foot, 3); tuft(cv, 10, foot, 0); tuft(cv, w - 2, foot, 5)
    return cv


# ---- signposts -----------------------------------------------------------------------

def _finger(cv: Canvas, x0: int, y0: int, length: int, east: bool, seed: int, paint: str = 'plaster'):
    """A finger arm on a signpost: a painted board with a pointed end, its lettering shown
    as two dark strokes (no words), its top edge lit; the paint worn back to timber at the
    tip where the weather hits."""
    for k in range(length):
        x = x0 + k if east else x0 - k
        tip = k >= length - 3
        for r in range(4):
            if tip and (r == 0 or r == 3) and k == length - 1:
                continue
            if tip and k == length - 1 and r in (1, 2):
                c = T('timber', 2)
            else:
                i = 5 if r == 0 else 4 if r < 3 else 2
                c = T(paint, i) if not (tip and noise2(k, r, seed) > 0.5) else wood(x, r, 3, seed)
            cv.set(x, y0 + r, c)
    for k in range(3, length - 4, 4):  # the lettering, two dark strokes per word
        x = x0 + k if east else x0 - k - 2
        cv.hline(x, y0 + 1, 2, T('slate', 1)); cv.hline(x, y0 + 2, 2, T('slate', 2))


def signpost(variant: int = 0) -> Canvas:
    """A fingerpost at a junction (size guide: the board at eye height, 28 to 44 tall):
    a squared oak post set in a small cairn of field stones, its finial; variant 0 two
    arms (east and west), variant 1 three arms and a little gabled cap over the top, variant
    2 an old leaning post with one arm and a tin waymark disc, mended with a lashed splint."""
    w, h = 32, 38
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    cx = 15
    shade_under(cv, 9, 26, foot)
    lean = 1 if variant == 2 else 0
    for y in range(4, foot - 3):  # the post
        off = lean * (foot - y) // 18
        for k in range(3):
            i = 4 if k == 0 else 3 if k == 1 else 2
            cv.set(cx + k + off, y, wood(cx + k, y, i, 31 + variant, along_x=False))
    if variant == 1:  # the cap: a little gable of two boards
        for k in range(5):
            cv.hline(cx - 2 + k // 2 - 1, 3 - k // 2, 7 - k, T('timber', 4 if k < 3 else 3))
        cv.hline(cx - 3, 4, 9, T('timber', 1))
    else:  # a turned finial
        cv.hline(cx, 3, 3, T('timber', 4)); cv.hline(cx + 1, 2, 1, T('timber', 5)); cv.hline(cx, 4, 3, T('timber', 2))
    arms = {0: ((9, True, 'plaster'), (14, False, 'plaster')),
            1: ((8, False, 'plaster'), (13, True, 'plaster'), (18, False, 'plaster')),
            2: ((10, True, 'bleached'),)}[variant]
    if variant == 2:  # the stub of an arm snapped off in a gale, its broken end splintered
        for k in range(4):
            x = cx - 1 - k + (foot - 15) // 18
            cv.set(x, 15, T('bleached', 5)); cv.set(x, 16, T('bleached', 4)); cv.set(x, 17, T('bleached', 2))
        cv.set(cx - 5 + (foot - 15) // 18, 16, T('timber', 2))
    for (ay, east, paint) in arms:
        if east:
            _finger(cv, cx + 3, ay, 12, True, 33 + ay, paint)
        else:
            _finger(cv, cx - 1, ay, 12, False, 34 + ay, paint)
    if variant == 2:
        for (x, y) in oval(cx + 1 + (foot - 19) // 18, 19, 1.8, 1.8):  # a tin waymark disc at eye height, rusting at its rim
            cv.set(x, y, T('slate', 4) if x <= cx + 2 else T('clay', 3))
        for y in (27, 29):  # the splint lashed to the cracked post
            cv.hline(cx - 1, y, 5, T('earth', 4))
        cv.vline(cx - 1, 25, 7, T('timber', 2))
    for (sx, sy, rx, ry) in ((cx - 2, foot - 2, 3.2, 2.2), (cx + 4, foot - 2, 3, 2), (cx + 1, foot - 4, 2.6, 1.8)):
        for (x, y) in oval(sx, sy, rx, ry):  # the cairn of field stones the post is set in
            lit = (x - sx) + (y - sy) * 1.3 < -0.5
            cv.set(x, y, stone_px(x, y, 4 if lit else 3 if x - sx < 1 else 2, 35))
    for (ay, east, paint) in arms:  # each arm's iron bolt through the post
        cv.hline(cx + 1 + lean * (foot - ay) // 18, ay + 1, 1, T('iron', 4)); cv.hline(cx + 1 + lean * (foot - ay) // 18, ay + 2, 1, T('iron', 2))
    for (lx, ly) in ((cx, 18), (cx, 19), (cx + 1, 19), (cx + 1, 26), (cx + 2, 26)):  # lichen on the weather side
        cv.set(lx + lean * (foot - ly) // 18, ly, T('leaf', 4) if ly < 20 else T('leaf', 3))
    cv.hline(cx - 4, foot - 3, 2, T('leaf', 3))
    tuft(cv, cx - 6, foot, 3); tuft(cv, cx + 8, foot, 1)
    return cv


# ---- gates and the stile --------------------------------------------------------------

def field_gate(variant: int = 0) -> Canvas:
    """A four-bar field gate between its posts, 40 wide (the size guide's gate, 12 to 22
    tall): a heavy hanging post on the west with two iron hinges, a slimmer latch post on
    the east with the latch and its chain, the gate's four rails, air between them, and its diagonal brace
    running up from the hinge foot (as a real gate is braced, so it does not sag), the
    rails' tops lit; the grass worn where the gate swings. Variant 1 is an older gate of
    bleached timber with a sag mended by a wire to the post top and a missing top rail end."""
    w, h = 40, 22
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    fam = 'bleached' if variant == 1 else 'timber'
    post(cv, 0, 0, foot, 4, seed=41, family=fam)  # the hanging post
    post(cv, w - 3, 2, foot, 3, seed=42, family=fam)  # the latch post
    for i, ry in enumerate((1, 7, 13, 18)):  # the four rails: a lit top and a shaded underside, the field seen between
        x1 = w - 3 if not (variant == 1 and i == 0) else w - 9
        for y in (ry, ry + 1):
            for x in range(4, x1):
                t = 5 if y == ry else 2
                if i == 0 and y == ry + 1:
                    t = 3  # the top rail is the stoutest
                cv.set(x, y, wood(x, y, t, 43 + i, family=fam, run=6))  # long members, long runs of grain
    for k in range(30):  # the diagonal brace from the hinge foot up to the far top rail
        x = 5 + k
        y = 18 - int(k * 17 / 30)
        cv.set(x, y, T(fam, 4))
        cv.set(x, y + 1, T(fam, 2))
    cv.vline(4, 1, 19, T(fam, 4)); cv.vline(5, 1, 19, T(fam, 2))  # the gate's own heel stile
    cv.vline(w - 5, 1, 19, T(fam, 3)); cv.vline(w - 4, 1, 19, T(fam, 1))  # its head stile
    for hy in (4, 15):  # the hinges
        cv.hline(1, hy, 5, T('iron', 2)); cv.hline(2, hy - 1, 2, T('iron', 4))
    cv.hline(w - 6, 9, 4, T('iron', 4)); cv.hline(w - 6, 10, 4, T('iron', 2))  # the latch
    for k in range(3):  # its chain looped over the post
        cv.set(w - 2, 11 + k, T('iron', 3 if k % 2 else 1))
    for hy in (4, 15):  # rust run down from each hinge
        cv.vline(2, hy + 1, 2, T('clay', 2))
    cv.hline(w - 10, 1, 4, T(fam, 5) if fam == 'bleached' else T('timber_warm', 5))  # the top rail rubbed pale where hands lift it
    for (lx, ly) in ((9, 7), (10, 7), (11, 7), (22, 13), (23, 13), (24, 13)) if variant == 1 else ():  # lichen on the old rails
        cv.set(lx, ly, T('leaf', 4))
    if variant == 1:  # a wire from the hanging post's top to the head stile holds the sag
        for k in range(32):
            cv.set(3 + k, 1 + int(k * 3 / 32), T('iron', 3))
    for x in range(6, w - 4):  # grass worn where the gate swings
        if noise2(x // 3, 0, 48) > 0.4:
            cv.set(x, foot, T('earth', 3))
    for (mx, my) in ((0, foot - 2), (1, foot - 2), (0, foot - 3), (w - 3, foot - 2), (w - 2, foot - 2)):  # moss at the posts' damp feet
        cv.set(mx, my, T('leaf', 2 if mx else 3))
    for (dx, dy, c) in ((w - 6, foot - 1, 3), (w - 5, foot - 1, 4), (w - 6, foot - 2, 4), (w - 7, foot - 1, 2)):  # a dock plant by the latch post
        cv.set(dx, dy, T('leaf_warm', c))
    tuft(cv, 1, foot, 3); tuft(cv, w - 1, foot, 5)
    return cv


def stile() -> Canvas:
    """A step stile over a drystone wall, 32 wide: the wall in coursed field stone with its
    coping laid on edge, and two flat through-stones sticking out of its face as steps (as
    the Headland's walls are crossed), a timber post beside them to steady a hand, the
    steps worn pale and the turf trodden bare at their foot."""
    w, h = 32, 22
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 0, w, foot)
    wall_top = 6
    for y in range(wall_top, foot):  # the wall: coursed stones, darker low down
        course = (y - wall_top) // 3
        off = (course * 5) % 7
        for x in range(0, w):
            joint = (y - wall_top) % 3 == 2 or (x + off) % 7 == 0
            i = 1 if joint else (4 if (y - wall_top) % 3 == 0 and x < w - 8 else 3 if x < w - 6 else 2)
            if y > foot - 4 and not joint:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, 51))
    for x in range(0, w):  # the coping, stones on edge
        for y in (wall_top - 2, wall_top - 1):
            cv.set(x, y, stone_px(x, y, 4 if y == wall_top - 2 and x % 3 else 2, 52))
        if x % 3 == 2:
            cv.set(x, wall_top - 2, T('stone', 1))
    for (sx, sy) in ((11, 14), (15, 9)):  # the through-stones: steps out of the wall's face
        for y in range(sy, sy + 3):
            for x in range(sx, sx + 7):
                cv.set(x, y, stone_px(x, y, 5 if y == sy else 3 if y == sy + 1 else 1, 53))
        cv.hline(sx + 2, sy, 3, T('stone_warm', 5))  # worn pale where boots tread
    post(cv, 23, 0, foot, 3, seed=54)  # the hand post
    cv.hline(10, foot, 10, T('earth', 3))  # the turf trodden bare at the foot of the steps
    for (mx, my) in ((2, 8), (3, 8), (27, 12), (28, 12), (6, 17)):  # moss and lichen on the stones
        cv.set(mx, my, T('leaf', 3))
    tuft(cv, 0, foot, 3); tuft(cv, 8, foot, 0); tuft(cv, w - 2, foot, 5)
    return cv


def squeeze_stile() -> Canvas:
    """A squeeze stile in a drystone wall, 32 wide: two tall slabs of stone set on end
    leave a gap a walker can turn through and a sheep cannot, narrower at the foot than at
    the hip (as the valley's walls are crossed where a gate would be left open); the wall
    either side in coursed field stone under its coping, the slabs' west faces lit, the
    gap's floor worn to bare earth and a polished patch on the slabs where hands grip."""
    w, h = 32, 20
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 0, w, foot)
    wall_top = 7
    gap = {y: (15 - (y - 3) // 6, 17 + (y - 3) // 6) for y in range(3, foot)}  # the V between the slabs
    for y in range(wall_top, foot):  # the wall either side
        course = (y - wall_top) // 4
        off = (course * 5) % 9
        for x in range(0, w):
            if 10 <= x <= 22:
                continue
            joint = (y - wall_top) % 4 == 3 or (x + off) % 9 == 0
            i = 1 if joint else (4 if (y - wall_top) % 4 == 0 and x < w - 6 else 3 if x < w - 4 else 2)
            if y > foot - 4 and not joint:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, 151))
    for x in range(0, w):  # the coping, stones on edge
        if 10 <= x <= 22:
            continue
        for y in (wall_top - 2, wall_top - 1):
            cv.set(x, y, stone_px(x, y, 4 if y == wall_top - 2 and x % 3 else 2, 152))
        if x % 3 == 2:
            cv.set(x, wall_top - 2, T('stone', 1))
    for y in range(3, foot):  # the two slabs on end, each lit on its west face
        g0, g1 = gap[y]
        for x in range(10, g0):
            k = x - 10
            i = 5 if k == 0 or y == 3 else 4 if k < 2 else 3 if x < g0 - 1 else 2
            if y > foot - 3:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, 153))
        for x in range(g1, 23):
            k = x - g1
            i = 4 if k == 0 or y == 3 else 3 if x < 21 else 2
            if y > foot - 3:
                i -= 1
            cv.set(x, y, stone_px(x, y, i, 154))
    cv.hline(gap[9][0] - 3, 9, 2, T('stone_warm', 5)); cv.hline(gap[9][1], 9, 2, T('stone_warm', 4))  # worn smooth by hands
    cv.hline(14, foot, 5, T('earth', 3))  # the gap's floor trodden bare
    for (mx, my) in ((2, 9), (3, 9), (26, 13), (27, 13), (11, 15), (11, 16)):  # moss and lichen
        cv.set(mx, my, T('leaf', 3))
    tuft(cv, 0, foot, 3); tuft(cv, 8, foot, 0); tuft(cv, w - 2, foot, 5)
    return cv


# ---- troughs -------------------------------------------------------------------------

def trough(variant: int = 0) -> Canvas:
    """A water trough at the track side (size guide 24 to 40 long, 8 to 14 tall at an
    animal's mouth): variant 0 a hewn stone trough, its rim lit, the water inside darker
    under the rim with a glint and a fallen leaf, green weed at the waterline, a spout
    feeding it; variant 1 a timber trough of planks held by iron bands on a pair of
    sleepers; variant 2 a half barrel by a spring pipe, its staves and hoops, moss on it.
    Each spills a little at the low end into a muddy hoof-trodden patch."""
    w = {0: 32, 1: 32, 2: 24}[variant]
    h = 14
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    if variant == 2:  # a half barrel: an oval rim seen from a little above, bellied staves, two hoops
        cx, rx = w // 2 + 1, 9
        for y in range(5, foot):
            half = rx + (1 if 7 <= y <= 10 else 0)
            for x in range(cx - half, cx + half):
                k = (x - (cx - half)) / (2 * half)
                i = 4 if k < 0.22 else 3 if k < 0.55 else 2 if k < 0.82 else 1
                if (x - cx) % 3 == 0 and 0.1 < k < 0.9:
                    i = max(1, i - 1)  # the joint between two staves
                if y >= foot - 2 and k > 0.1:
                    i = max(1, i - 1)  # the foot dark where it stands wet
                cv.set(x, y, T('timber', i))
            if y in (6, 10):  # the iron hoops, lit on the west
                for x in range(cx - half, cx + half):
                    k = (x - (cx - half)) / (2 * half)
                    cv.set(x, y, T('iron', 4 if k < 0.3 else 3 if k < 0.7 else 2))
        for (x, y) in oval(cx, 4, rx, 2.2):  # the rim's end grain and the water inside it
            r = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - 4) / 2.2) ** 2
            cv.set(x, y, T('timber', 5 if x < cx else 4) if r > 0.55 else T('water', 2 if y <= 4 else 1))
        cv.hline(cx - 4, 4, 2, T('water', 4))  # the sky in it
        for k in range(6):  # the spring pipe running in from the west, and its trickle
            cv.set(k, 1, T('iron', 4)); cv.set(k, 2, T('iron', 2))
        cv.vline(5, 3, 2, T('water', 4))
        cv.hline(cx + 5, 8, 2, T('leaf', 2)); cv.hline(cx + 6, 9, 2, T('leaf', 3))  # moss on the shaded staves
    else:
        top = 4
        for y in range(top, foot - 1):
            for x in range(0, w):
                r = y - top
                if variant == 0:
                    i = 5 if r == 0 else 4 if r == 1 and x < w - 3 else 3 if x < w - 4 else 2
                    if r >= 5:
                        i -= 1
                    cv.set(x, y, stone_px(x, y, i, 72))
                else:
                    i = 5 if r == 0 else 3 if r % 3 else 1  # planks, with their joints
                    if x >= w - 3:
                        i -= 1
                    cv.set(x, y, wood(x, y, i, 73))
        for y in (top - 1, top):  # the water within the rim, darker under the near lip
            for x in range(2, w - 2):
                cv.set(x, y, T('water', 2 if y == top - 1 else 1))
        cv.hline(4, top - 1, 4, T('water', 4))  # the sky in it
        cv.hline(0, top - 2, w, T('stone', 5) if variant == 0 else T('timber', 5))  # the far rim
        cv.hline(w - 9, top - 1, 2, T('clay', 4))  # a fallen leaf afloat
        if variant == 0:
            cv.hline(2, top + 1, w - 4, T('leaf', 2))  # weed at the waterline inside the lip
            for k in range(4):  # the spout feeding it, and the water falling in
                cv.set(1 + k, 0, T('iron', 4)); cv.set(1 + k, 1, T('iron', 2))
            cv.vline(5, 1, 2, T('water', 4))
        else:
            for bx in (5, w - 7):  # the iron bands, and the sleepers it stands on
                cv.vline(bx, top, foot - top - 1, T('iron', 3)); cv.vline(bx + 1, top, foot - top - 1, T('iron', 1))
            cv.hline(2, foot - 1, 6, T('timber', 2)); cv.hline(w - 8, foot - 1, 6, T('timber', 2))
    for x in range(w - 6, w + 2):  # the spill at the low end, a muddy hoof-trodden patch
        cv.set(x, foot, T('earth', 2) if x % 3 else T('water', 2))
    tuft(cv, 0, foot, 3)
    return cv


# ---- noticeboards --------------------------------------------------------------------

def noticeboard(variant: int = 0) -> Canvas:
    """A village noticeboard (the size guide's sign: the board at eye height): a framed
    board on two posts with notices pinned to it, each a sheet with dark lines of writing
    (no words), a red one for a fair, a lost-cat bill, a curled corner; variant 0 under a
    little shingled roof against the rain, variant 1 a plain board with a box of leaflets
    on its post, variant 2 an old board with a glazed door and its brass lock."""
    w, h = 32, 36
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 4, 28, foot)
    for px in (5, 24):  # the posts: up under the roof, or capped just above a plain board
        post(cv, px, 6 if variant == 0 else 8, foot, 3, seed=81 + px)
    bx0, by0, bx1, by1 = 3, 9, 29, 25
    for y in range(by0, by1):  # the frame and the cork-brown board
        for x in range(bx0, bx1):
            frame = x in (bx0, bx0 + 1, bx1 - 2, bx1 - 1) or y in (by0, by0 + 1, by1 - 2, by1 - 1)
            if frame:
                i = 4 if (x < bx0 + 2 or y < by0 + 2) else 2
                cv.set(x, y, wood(x, y, i, 82))
            else:
                n = noise2(x // 2, y, 83)  # cork, its grain in short runs, darker under the frame's lip
                c = T('earth', 4) if n > 0.78 else T('earth', 3) if n > 0.3 else T('earth', 2)
                if y == by0 + 2:
                    c = T('earth', 1)
                cv.set(x, y, c)
    notices = ((6, 12, 7, 8, 'plaster'), (14, 11, 6, 6, 'berry'), (21, 12, 6, 9, 'plaster_cool'),
               (14, 18, 6, 5, 'plaster'))
    for (nx, ny, nw, nh, paper) in notices:
        ramp = 'plaster' if paper == 'plaster_cool' else paper
        for y in range(ny, ny + nh):
            for x in range(nx, nx + nw):
                i = 5 if x < nx + nw - 1 else 3
                if y == ny + nh - 1:
                    i -= 1  # the sheet's lower edge lifting off the board
                if paper == 'berry':
                    i = 4 if x < nx + nw - 1 else 3
                cv.set(x, y, T(ramp, i))
        cv.hline(nx + 1, ny + nh, nw, T('earth', 1))  # its shadow on the cork
        for ly in range(ny + 2, ny + nh - 1, 2):  # its lines of writing
            cv.hline(nx + 1, ly, nw - 3, T('slate', 2) if paper != 'berry' else T('plaster', 5))
        cv.hline(nx + nw // 2 - 1, ny, 2, T('brass', 4))  # a pin
    for y in range(19, 23):  # a walks map pinned low on the west: fields, a river, a path
        for x in range(6, 12):
            cv.set(x, y, T('leaf', 4) if (x + y) % 5 < 2 else T('grass', 4) if x < 11 else T('grass', 3))
        cv.set(9, y, T('water', 4) if y % 2 else T('water', 3))
    cv.hline(6, 19, 6, T('plaster', 5)); cv.hline(7, 23, 5, T('earth', 1))
    for y in range(18, 22):  # a photograph of a lost cat, its grey and white
        cv.hline(22, y, 4, T('slate', 3) if y < 20 else T('plaster', 4))
    cv.hline(23, 18, 2, T('slate', 1)); cv.hline(22, 22, 4, T('earth', 1))
    cv.set(26, 20, T('plaster', 2)); cv.set(25, 20, T('plaster', 3))  # a curled corner
    if variant == 0:  # the shingled roof on its brackets: three courses, butt joints staggered
        for y in range(2, 9):
            half = 15 - (8 - y) // 2
            course = (y - 3) // 3
            for x in range(16 - half, 16 + half):
                if y == 2:
                    c = T('timber', 5)  # the ridge board
                elif y == 8:
                    c = T('timber', 1)  # the eaves' shadow
                elif (y - 3) % 3 == 2:
                    c = T('timber', 2 if x < 25 else 1)  # the shadow under each course's butts
                elif (x + course * 3) % 7 == 0:
                    c = T('timber', 2)  # a joint between shingles
                else:
                    c = T('timber' if noise2((x + course * 3) // 7, course, 84) < 0.6 else 'timber_warm', 4 if x < 20 else 3)
                cv.set(x, y, c)
        for (mx, my) in ((22, 3), (23, 3), (22, 4), (8, 7), (9, 7)):  # moss where the roof stays damp
            cv.set(mx, my, T('leaf', 3 if my < 5 else 2))
        for bx in (6, 25):  # the brackets under the eaves
            cv.set(bx, 9, T('timber', 2)); cv.set(bx + 1, 9, T('timber', 2))
    if variant:  # the parish's name rail over a plain board, painted green, its letters cream
        for x in range(7, 25):
            cv.set(x, 6, T('leaf', 4) if x < 22 else T('leaf', 3)); cv.set(x, 7, T('leaf', 2)); cv.set(x, 8, T('leaf', 1))
        for x in range(9, 23, 4):
            cv.hline(x, 7, 2, T('plaster', 5) if x < 20 else T('plaster', 4))
    if variant == 0:  # the roof's shadow falls across the top of the board and its notices
        shadow = {T(r, i): T(r, max(0, i - 1)) for r in ('earth', 'plaster', 'berry', 'brass', 'slate') for i in range(6)}
        for y in (by0 + 2, by0 + 3):
            for x in range(bx0 + 2, bx1 - 2):
                c = cv.get(x, y)
                hx = '#%02X%02X%02X' % c[:3]
                if hx in shadow:
                    cv.set(x, y, shadow[hx])
    elif variant == 1:  # a leaflet box on the east post
        for y in range(27, 32):
            for x in range(27, 31):
                cv.set(x, y, T('clay', 4 if y == 27 else 3) if x < 30 else T('clay', 2))
        cv.hline(27, 26, 4, T('plaster', 5))
    else:  # a glazed door over the board, its glass catching the sky, a brass lock
        for x in range(bx0 + 2, bx1 - 2):
            cv.set(x, by0 + 2, T('water', 5))
            if (x - bx0) % 9 == 0:
                for y in range(by0 + 2, by1 - 2):
                    cv.set(x, y, T('timber', 4))  # the glazing bars, lit
        cv.hline(bx1 - 4, 17, 2, T('brass', 4))
    if variant == 1:
        ivy(cv, 5, by1 + 1, foot - 1, seed=85)  # ivy up the west post of the plain board
    tuft(cv, 4, foot, 3); tuft(cv, 27, foot, 1)
    return cv


# ---- the well ------------------------------------------------------------------------

def well(variant: int = 0) -> Canvas:
    """The village well (size guide: a wall 10 to 14 high, a roof or winch on posts, 24 to
    34 wide): a round wall of coursed stone seen from a little above, its rim of dressed
    coping lit on the north-west, the dark shaft inside with water far down catching a
    glint; two posts carrying the winch drum, its iron crank and the rope down to a bucket
    hung on the rim; variant 0 under a pitched roof of shingles, variant 1 open, with an
    iron hoop overhead and a pail on the ground beside it. Moss in the lower courses where
    water splashes, and a trodden flag at the side where people stand."""
    w, h = 32, 40
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    cx = w // 2
    shade_under(cv, 2, w - 1, foot)
    wall_top = foot - 12
    for y in range(wall_top, foot):  # the round wall, coursed, lit on the west
        for x in range(2, w - 2):
            u = (x - 2) / (w - 5)
            course = (y - wall_top) // 4
            joint = (y - wall_top) % 4 == 3 or (x + course * 4) % 8 == 0
            i = 4 if u < 0.25 else 3 if u < 0.6 else 2 if u < 0.85 else 1
            if joint:
                i = max(0, i - 2)
            if y > foot - 4 and noise2(x // 2, y, 91) > 0.55:
                cv.set(x, y, T('leaf', 2 if u > 0.5 else 3)); continue
            cv.set(x, y, stone_px(x, y, i, 92))
    for (x, y) in oval(cx, wall_top - 1, (w - 4) / 2, 4):  # the coping ring from above, and the shaft
        r = math.hypot((x + 0.5 - cx) / ((w - 4) / 2), (y + 0.5 - wall_top + 1) / 4)
        if r > 0.62:
            lit = (x - cx) + (y - wall_top + 1) * 2 < 0
            cv.set(x, y, T('stone_warm' if lit else 'stone', 5 if lit else 3))  # dressed, so even
        else:
            cv.set(x, y, T('slate', 0) if r > 0.3 else T('water', 1))
    cv.hline(cx - 2, wall_top - 1, 2, T('water', 4))  # the glint far down
    for px in (3, w - 6):  # the two posts
        post(cv, px, 6, wall_top + 1, 3, seed=94 + px)
    for x in range(5, w - 5):  # the winch drum with rope wound on it
        cv.set(x, 11, T('timber', 4)); cv.set(x, 12, T('earth', 4) if x % 2 else T('earth', 3)); cv.set(x, 13, T('timber', 1))
    for k in range(4):  # the iron crank on the east post
        cv.set(w - 3, 12 + k, T('iron', 3))
    cv.hline(w - 3, 16, 3, T('iron', 4))
    cv.vline(cx + 3, 14, wall_top - 15, T('earth', 4))  # the rope down to the bucket on the rim
    for y in range(wall_top - 3, wall_top + 1):  # the bucket, staves and a hoop
        cv.hline(cx + 1, y, 5, T('timber', 3 if y < wall_top else 2) if y != wall_top - 2 else T('iron', 3))
    if variant == 0:  # a pitched roof of shingles on the posts
        for y in range(0, 7):
            half = 4 + y * 2
            for x in range(cx - half, cx + half):
                c = T('timber' if noise2(x // 3, y, 96) < 0.6 else 'timber_warm', 4 if x < cx else 2)  # shingles, warm and plain
                if y % 2 == 1:
                    c = T('timber', 3 if x < cx else 1)
                cv.set(x, y, c)
        cv.vline(cx, 0, 7, T('timber', 5))
    else:  # an iron hoop overhead, and a pail on the ground beside the well
        for k in range(w - 10):
            x = 5 + k
            y = 6 - int(math.sin(k / (w - 11) * math.pi) * 5)
            cv.set(x, y, T('iron', 3))
        for y in range(foot - 4, foot):
            cv.hline(w - 4, y, 4, T('iron', 4 if y == foot - 4 else 2))
    cv.hline(4, foot, 8, T('stone', 4))  # a trodden flag at the side where people stand
    tuft(cv, 1, foot, 3); tuft(cv, w - 2, foot, 1)
    return cv


def clean(cv: Canvas, keep=frozenset()) -> Canvas:
    """Detail comes in clusters (art-style.md): a pixel unlike every drawn neighbour takes
    the commonest of theirs, edge pixels included once two neighbours are drawn, so the
    outline that finalize adds never leaves a single-pixel fleck against it."""
    p = cv.pad
    for _ in range(3):
        changed = []
        for y in range(-p, cv.h + p):
            for x in range(-p, cv.w + p):
                c = cv.get(x, y)
                if not c[3] or (x, y) in keep:
                    continue
                ns = [cv.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                ns = [n for n in ns if n[3]]
                if len(ns) >= 2 and all(n != c for n in ns):
                    changed.append((x, y, max(ns, key=ns.count)))
        for (x, y, c) in changed:
            cv.set(x, y, c)
        if not changed:
            break
    return cv


def props() -> dict[str, Canvas]:
    return {k: clean(cv) for k, cv in _props().items()}


def _props() -> dict[str, Canvas]:
    return {
        'bench_oak': bench_plank(0), 'bench_memorial': bench_plank(1), 'bench_stone': bench_stone(),
        'signpost_two': signpost(0), 'signpost_three': signpost(1), 'signpost_old': signpost(2),
        'field_gate_oak': field_gate(0), 'field_gate_old': field_gate(1), 'squeeze_stile': squeeze_stile(),
        'stile_step': stile(),
        'trough_stone': trough(0), 'trough_timber': trough(1), 'trough_barrel': trough(2),
        'noticeboard_roofed': noticeboard(0), 'noticeboard_box': noticeboard(1), 'noticeboard_glazed': noticeboard(2),
        'well_roofed': well(0), 'well_open': well(1),
    }


if __name__ == '__main__':
    # by day, at night and on a second ground (prop_sheet.py; SHEET_GROUND picks it)
    import prop_sheet
    size = prop_sheet.sheet(props(), os.environ.get('SHEET', '/tmp/wayside-props.png'),
                            second=os.environ.get('SHEET_GROUND', 'snow'))
    print('sheet', size)
