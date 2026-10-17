"""Props for Dust Gulch, the western desert town (world-atlas.md).

The valley's rules under a harder sun: sun-bleached boards, adobe walls, long cast
shadows, cactus shaded as cylinders, everything dusty at its foot.
Run directly for a contact sheet: python3 scripts/art/western_props.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, WOOD, STONE, RED, WTR, GOLD  # noqa: E402

DESERT, CACTUS, ADOBE = (MATERIALS[k] for k in ('desert', 'cactus', 'adobe'))
IRON = MATERIALS['iron']
BLEACHED = ['#4A3328', '#6E5040', '#93725A', '#B39277', '#CDB096', '#E4CCB2']  # sun-bleached boards
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def false_front(width: int = 104, seed: int = 0, sign_ramp=RED, kind: str = 'saloon') -> Canvas:
    """A false-front building, 104 x 92: the tall square facade hides a pitched tin roof
    (its top shows behind), bleached clapboards, a sign board with abstract lettering
    strokes, an upper window, a porch roof on posts that throws a deep shadow, and
    swinging half doors (a saloon) or a shop window (a store)."""
    w, h = width, 92
    cv = Canvas(w, h, pad=PAD)
    # the tin roof behind the facade, seen from above
    for y in range(2, 20):
        for x in range(10, w - 10):
            cv.set(x, y, IRON[3] if (x // 4) % 2 else IRON[2])
        cv.hline(10, 2, w - 20, IRON[4])
    # the facade: stepped top, clapboards
    face = {(x, y) for x in range(4, w - 4) for y in range(14, h - 6)}
    face |= {(x, y) for x in range(14, w - 14) for y in range(8, 14)}
    detail.boards(cv, face, BLEACHED, 3, 8, board=4, seed=seed, grain=0.08)
    for (x, y) in face:
        if (x, y - 1) not in face:
            cv.set(x, y, BLEACHED[5])
            cv.set(x, y + 1, BLEACHED[4])
    cv.hline(4, 13, 10, BLEACHED[1]); cv.hline(w - 14, 13, 10, BLEACHED[1])
    # the sign board
    sx0, sx1, sy0, sy1 = 18, w - 18, 17, 29
    for (x, y) in rect_set(sx0, sy0, sx1 - sx0, sy1 - sy0):
        cv.set(x, y, sign_ramp[2] if y > sy0 else sign_ramp[3])
    cv.hline(sx0, sy1, sx1 - sx0, sign_ramp[0])
    ink = '#F4E6C8'
    for i, x in enumerate(range(sx0 + 4, sx1 - 4, 6)):  # abstract lettering strokes, never words
        stroke = int(noise2(i, seed, 201) * 5)
        if stroke == 0:
            cv.vline(x, 20, 6, ink); cv.vline(x + 3, 20, 6, ink); cv.hline(x, 22, 4, ink)
        elif stroke == 1:
            cv.hline(x, 20, 4, ink); cv.hline(x, 25, 4, ink); cv.vline(x, 20, 6, ink); cv.vline(x + 3, 20, 6, ink)
        elif stroke == 2:
            cv.vline(x + 1, 20, 6, ink); cv.hline(x, 20, 3, ink); cv.hline(x, 25, 3, ink)
        elif stroke == 3:
            cv.vline(x, 20, 6, ink); cv.hline(x, 25, 4, ink)
        else:
            cv.hline(x, 20, 4, ink); cv.vline(x, 20, 3, ink); cv.hline(x, 22, 4, ink); cv.vline(x + 3, 22, 4, ink); cv.hline(x, 25, 4, ink)
    # an upper window with a shutter
    gp.window(cv, w // 2 - 8, 33, 16, 12, shutters=None, sill=True, warm=False)
    # the porch roof and its posts
    py = 50
    for x in range(0, w):
        for y in range(py, py + 5):
            cv.set(x, y, BLEACHED[4] if y == py else BLEACHED[2] if y < py + 4 else BLEACHED[0])
    detail.overhang_shadow(cv, 4, w - 4, py + 5, lambda x: 7, k=2, cap=2)
    for px in (2, w // 3, 2 * w // 3, w - 5):
        gp.post(cv, px, py + 5, h - 4, w=3, ramp=BLEACHED)
    # the ground floor
    dx = w // 2 - 9
    if kind == 'saloon':
        for (x, y) in rect_set(dx, 62, 18, 18):  # swinging half doors over a dark room
            cv.set(x, y, '#2A1C16')
        for half in (0, 9):
            for (x, y) in rect_set(dx + half, 66, 9, 9):
                cv.set(x, y, WOOD[3] if (x - dx) % 3 else WOOD[2])
            cv.hline(dx + half, 66, 9, WOOD[4])
    else:
        for (x, y) in rect_set(dx - 14, 62, 46, 18):
            cv.set(x, y, WTR[3] if y < 66 else WTR[1])
        cv.vline(dx + 9, 62, 18, BLEACHED[2])
        for k in range(4):
            cv.rect(dx - 10 + k * 11, 72, 5, 6, (GOLD, RED, WTR, ADOBE)[k][3])
    # the boardwalk at the foot
    for y in range(h - 6, h):
        for x in range(0, w):
            cv.set(x, y, BLEACHED[3] if (x // 6) % 2 else BLEACHED[2])
    cv.hline(0, h - 6, w, BLEACHED[5])
    return cv


def water_tower() -> Canvas:
    """A wooden water tank on a trestle, 48 x 96, with iron hoops and a spout."""
    w, h = 48, 96
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(24, 8, 21, 6):  # the conical lid, seen from above
        cv.set(x, y, BLEACHED[4] if x < 24 else BLEACHED[2])
    cv.set(24, 2, BLEACHED[5])
    tank = rect_set(4, 8, 40, 34)
    detail.boards(cv, tank, BLEACHED, 3, 8, board=4, vertical=True, x0=4, grain=0.05)
    for x in range(4, 44):
        k = (x - 4) / 40
        for y in range(8, 42):
            if k > 0.62:
                detail.shade(cv, x, y, 1)
            if k < 0.12:
                detail.shade(cv, x, y, -1)
    for hy in (14, 26, 38):
        cv.hline(4, hy, 40, IRON[3]); cv.hline(4, hy + 1, 40, IRON[1])
    for (x, y) in oval(24, 42, 20, 3):
        if y >= 42:
            cv.set(x, y, BLEACHED[1])
    for lx in (8, 20, 28, 40):  # the trestle
        gp.post(cv, lx, 44, h - 2, w=3, ramp=BLEACHED)
    for y0 in (56, 74):
        for t in range(32):
            cv.set(9 + t, y0 + t // 3 % 2, BLEACHED[2])
        for t in range(32):
            cv.set(9 + t, y0 + 10 - (t * 10 // 32), BLEACHED[1])
    cv.rect(40, 30, 6, 3, IRON[2])
    cv.vline(45, 33, 6, IRON[2])
    return cv


def saguaro(tall: bool = True) -> Canvas:
    """A saguaro cactus, 30 x 54 (or 22 x 36): ribbed cylinders lit on the left, arms
    that turn upward, spines picked out on the lit side."""
    w, h = (30, 54) if tall else (22, 36)
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2

    def cyl(x0, y0, y1, r):
        for y in range(y0, y1):
            for x in range(x0 - r, x0 + r + 1):
                k = (x - (x0 - r)) / (2 * r + 1)
                c = CACTUS[4] if k < 0.2 else CACTUS[3] if k < 0.45 else CACTUS[2] if k < 0.75 else CACTUS[1]
                if (x - x0) % 3 == 0 and k > 0.2:
                    c = CACTUS[max(0, CACTUS.index(c) - 1)]
                cv.set(x, y, c)
        for (x, y) in disc(x0, y0, r):
            if y <= y0:
                cv.set(x, y, CACTUS[4] if x < x0 else CACTUS[3])

    cyl(cx, 4, h - 2, 5 if tall else 4)
    if tall:
        cv_arm = [(cx - 11, 14, cx - 11, 30), (cx + 11, 20, cx + 11, 34)]
        for (ax, ay, bx, by) in cv_arm:
            cyl(ax, ay, by, 3)
            for x in range(min(ax, cx), max(ax, cx) + 1):
                for y in range(by - 3, by + 3):
                    cv.set(x, y, CACTUS[2] if y > by else CACTUS[3])
    else:
        cyl(cx + 7, 12, 22, 3)
        for x in range(cx, cx + 8):
            for y in range(19, 24):
                cv.set(x, y, CACTUS[2] if y > 21 else CACTUS[3])
    for y in range(6, h - 4, 4):
        cv.set(cx - 3, y, '#F1E6C0')
    cv.set(cx, 3, RED[3]); cv.set(cx + 1, 2, RED[4])  # a flower on top
    return cv


def tumbleweed() -> Canvas:
    """A tumbleweed, 16 x 14: a tangle of dry twigs."""
    cv = Canvas(16, 14, pad=PAD)
    for k in range(60):
        a = noise2(k, 0, 203) * 2 * math.pi
        r = noise2(k, 1, 203) * 6
        x, y = int(8 + r * math.cos(a)), int(7 + r * math.sin(a) * 0.85)
        cv.set(x, y, DESERT[2] if x + y < 15 else DESERT[0])
        cv.set(x + 1, y, DESERT[1])
    return cv


def wagon() -> Canvas:
    """A covered wagon, 72 x 48: a canvas hood lit on its upper left, wooden bed, big
    spoked wheels."""
    w, h = 72, 48
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(34, 18, 28, 16):
        if y < 26:
            k = (x - 6) / 56
            cv.set(x, y, '#F4ECD8' if k < 0.3 and y < 14 else '#E2D6BC' if k < 0.65 else '#BFB094')
    for hx in (16, 34, 52):
        for y in range(4, 26):
            if cv.get(hx, y)[3]:
                cv.set(hx, y, '#A99C82')
    detail.boards(cv, rect_set(6, 26, 58, 10), WOOD, 2, 26, board=3, seed=4)
    cv.hline(6, 26, 58, WOOD[4])
    for (wx, r) in ((16, 9), (54, 9)):
        for k in range(36):
            a = 2 * math.pi * k / 36
            cv.set(int(wx + r * math.cos(a)), int(38 + r * math.sin(a)), WOOD[1] if math.sin(a) > 0 else WOOD[3])
        for k in range(8):
            a = math.pi * k / 4
            for t in range(1, r):
                cv.set(int(round(wx + math.cos(a) * t)), int(round(38 + math.sin(a) * t)), WOOD[2])
        cv.set(wx, 38, IRON[2])
    cv.hline(64, 32, 8, WOOD[2])
    return cv


def windpump() -> Canvas:
    """A desert windpump, 40 x 88: a lattice tower, a fan of blades and a tail vane."""
    w, h = 40, 88
    cv = Canvas(w, h, pad=PAD)
    for y in range(26, h - 2):
        t = (y - 26) / (h - 28)
        lx, rx = int(16 - t * 10), int(23 + t * 10)
        cv.set(lx, y, IRON[3]); cv.set(rx, y, IRON[1])
        if (y - 26) % 10 == 0:
            for x in range(lx, rx + 1):
                cv.set(x, y, IRON[2])
            for k in range(rx - lx):
                cv.set(lx + k, y + min(9, k * 10 // max(1, rx - lx)), IRON[2])
    for k in range(12):
        a = 2 * math.pi * k / 12
        for t in range(3, 15):
            x, y = int(round(19 + math.cos(a) * t)), int(round(16 + math.sin(a) * t * 0.9))
            cv.set(x, y, '#D8D4C8' if math.cos(a) + math.sin(a) < 0 else '#A9A49A')
    for (x, y) in disc(19, 16, 2.5):
        cv.set(x, y, IRON[1])
    for x in range(22, 38):
        cv.set(x, 17, IRON[2])
    for y in range(12, 22):
        cv.hline(32, y, 6, RED[3] if y < 17 else RED[2])
    return cv


def trough() -> Canvas:
    """A horse trough, 34 x 14: planks round a strip of water."""
    cv = Canvas(34, 14, pad=PAD)
    detail.boards(cv, rect_set(1, 3, 32, 10), BLEACHED, 2, 3, board=3, seed=6)
    for (x, y) in rect_set(4, 4, 26, 4):
        cv.set(x, y, WTR[3] if y == 4 else WTR[2])
    cv.hline(1, 3, 32, BLEACHED[5])
    return cv


def cow_skull() -> Canvas:
    cv = Canvas(18, 10, pad=PAD)
    for (x, y) in oval(9, 5, 3.5, 3.2):
        cv.set(x, y, '#F2EAD8' if x < 9 else '#D8CDB6')
    for side in (-1, 1):
        for t in range(6):
            cv.set(9 + side * (3 + t), 3 - (t // 3), '#E8DEC8')
    cv.set(8, 5, '#3A2A22'); cv.set(10, 5, '#3A2A22')
    return cv


def mine_portal() -> Canvas:
    """The old mine's mouth in a sandstone outcrop, 72 x 56: layered rock lit on the
    left, a timber frame round a dark entrance and cart rails running in."""
    w, h = 72, 56
    cv = Canvas(w, h, pad=PAD)
    rock = oval(36, 34, 35, 20) | oval(22, 26, 18, 16) | oval(52, 28, 17, 14) | oval(38, 20, 14, 10)
    rock = {(x, y) for (x, y) in rock if y > 8 + int(noise2(x // 4, 0, 205) * 6)}
    for (x, y) in rock:
        if y > 52:
            continue
        layer = (y + int(noise2(x // 6, y // 5, 204) * 3)) // 5
        lit = (x - 36) + (y - 30) * 0.6 < -6
        c = ADOBE[4 if lit else 2] if layer % 2 else ADOBE[3 if lit else 1]
        if (x, y - 1) not in rock:
            c = ADOBE[4]
        cv.set(x, y, c)
    for (x, y) in rect_set(24, 26, 24, 26):
        cv.set(x, y, '#1A120E' if y > 28 else '#2A1C16')
    for px in (22, 47):
        gp.post(cv, px, 24, 52, w=3, ramp=WOOD)
    cv.rect(20, 22, 32, 4, WOOD[3]); cv.hline(20, 22, 32, WOOD[4]); cv.hline(20, 25, 32, WOOD[1])
    for y in range(40, 53, 3):  # sleepers and rails into the dark
        cv.hline(28, y, 16, WOOD[2])
    for rx in (30, 41):
        cv.vline(rx, 34, 19, IRON[3])
    return cv


def dry_well() -> Canvas:
    """The town's dry well, 34 x 42: fieldstone ring, a wooden windlass with a frayed
    rope and an empty bucket hung up, cracked mud showing at the bottom."""
    cv = Canvas(34, 42, pad=PAD)
    ring = oval(17, 33, 14, 7)
    for (x, y) in ring:
        cv.set(x, y, ADOBE[3] if x < 17 else ADOBE[1])
    detail.stones(cv, 3, 29, 28, 10, ADOBE, seed=11, course=3)
    for (x, y) in oval(17, 31, 10, 4.2):
        cv.set(x, y, DESERT[1] if (x + y) % 4 else DESERT[0])  # dry, cracked bottom
    for (x0, y0, x1, y1) in ((10, 30, 14, 32), (18, 29, 22, 33), (13, 33, 20, 31)):
        cv.set(x0, y0, DESERT[0]); cv.set(x1, y1, DESERT[0])
    for px in (5, 27):
        gp.post(cv, px, 8, 32, w=3, ramp=BLEACHED)
    for x in range(5, 30):  # the windlass drum
        cv.set(x, 12, BLEACHED[4]); cv.set(x, 13, BLEACHED[2]); cv.set(x, 14, BLEACHED[1])
    for x in range(13, 21):
        cv.set(x, 12, '#C9B48A'); cv.set(x, 13, '#A8936A')
    cv.vline(30, 10, 6, IRON[2]); cv.hline(30, 15, 3, IRON[2])
    for (x, y) in rect_set(24, 17, 6, 6):  # the bucket hung on the post
        cv.set(x, y, WOOD[3] if x < 26 else WOOD[1])
    cv.hline(24, 18, 6, IRON[2]); cv.hline(24, 21, 6, IRON[2])
    cv.vline(17, 15, 4, '#A8936A')  # a frayed end of rope
    cv.set(16, 19, '#A8936A'); cv.set(18, 19, '#A8936A')
    return cv


def keg() -> Canvas:
    """A wooden keg on its side, 18 x 14, with iron hoops."""
    cv = Canvas(18, 14, pad=PAD)
    for (x, y) in oval(9, 7, 8, 6):
        k = (y - 1) / 12
        cv.set(x, y, WOOD[4] if k < 0.25 else WOOD[3] if k < 0.55 else WOOD[2] if k < 0.8 else WOOD[1])
    for hx in (4, 14):
        for y in range(1, 13):
            if cv.get(hx, y)[3]:
                cv.set(hx, y, IRON[3] if y < 6 else IRON[1])
    for (x, y) in oval(2, 7, 2, 5):
        cv.set(x, y, BLEACHED[4] if y < 7 else BLEACHED[3])
    cv.set(2, 7, WOOD[0])
    return cv


def hay_bale() -> Canvas:
    """A square hay bale, 22 x 16, its straws lit on top, two twine bands."""
    cv = Canvas(22, 16, pad=PAD)
    for y in range(2, 16):
        for x in range(1, 21):
            top = y < 6
            n = noise2(x, y, 206)
            c = ('#F2D27A' if n > 0.5 else '#E2BC5E') if top else ('#C99A3C' if n > 0.4 else '#A87E2C')
            cv.set(x, y, c)
    for bx in (6, 15):
        cv.vline(bx, 2, 14, '#7A5A22')
    cv.hline(1, 6, 20, '#8E6A26')
    for x in range(1, 21, 3):
        cv.set(x, 1, '#F2D27A')
    return cv


def dynamite_crate() -> Canvas:
    """A mining crate with red sticks peeking out and a stencilled band, 22 x 18."""
    cv = Canvas(22, 18, pad=PAD)
    detail.boards(cv, rect_set(1, 5, 20, 13), BLEACHED, 2, 5, board=4, seed=7)
    cv.hline(1, 5, 20, BLEACHED[5])
    for x in range(3, 19, 3):
        cv.vline(x, 1, 5, RED[3]); cv.vline(x + 1, 1, 5, RED[2]); cv.set(x, 0, '#E8DEC8')
    cv.hline(1, 11, 20, RED[2])
    return cv


def hitching_rail() -> Canvas:
    """A hitching rail, 44 x 18: two posts and a worn rail."""
    cv = Canvas(44, 18, pad=PAD)
    for px in (3, 38):
        gp.post(cv, px, 4, 18, w=3, ramp=BLEACHED)
    for x in range(1, 43):
        cv.set(x, 5, BLEACHED[4]); cv.set(x, 6, BLEACHED[2]); cv.set(x, 7, BLEACHED[1])
    for x in (16, 17, 26):
        cv.set(x, 6, BLEACHED[3])
    return cv


def poster_board() -> Canvas:
    """A wanted-poster board, 30 x 38: a little shingled cap and pinned posters with an
    abstract portrait (never real text)."""
    cv = Canvas(30, 38, pad=PAD)
    for px in (4, 23):
        gp.post(cv, px, 8, 38, w=3, ramp=BLEACHED)
    detail.boards(cv, rect_set(2, 8, 26, 18), BLEACHED, 2, 8, board=4, vertical=True, x0=2)
    for y in range(3, 8):
        cv.hline(1 + (7 - y) // 2, y, 28 - (7 - y), BLEACHED[4] if y < 6 else BLEACHED[1])
    for (x0, y0) in ((5, 10), (16, 11)):
        for (x, y) in rect_set(x0, y0, 9, 12):
            cv.set(x, y, '#EAD9B2' if y > y0 else '#F4E6C8')
        for (x, y) in disc(x0 + 4, y0 + 5, 2.4):
            cv.set(x, y, '#6E5040')
        cv.hline(x0 + 1, y0 + 9, 7, '#93725A'); cv.hline(x0 + 2, y0 + 1, 5, '#93725A')
    return cv


def corral_rail(length: int = 64) -> Canvas:
    """A run of split-rail corral fence, 64 x 20: rough posts and two sagging rails."""
    cv = Canvas(length, 20, pad=PAD)
    for px in range(1, length, 16):
        gp.post(cv, px, 2, 20, w=3, ramp=BLEACHED)
    for ry in (6, 12):
        for x in range(0, length):
            sag = int(math.sin((x % 16) / 16 * math.pi) * 1.4)
            cv.set(x, ry + sag, BLEACHED[4]); cv.set(x, ry + sag + 1, BLEACHED[2])
    return cv


def corral_side() -> Canvas:
    """The side of a split-rail corral, 12 x 60: posts and rails seen end on."""
    cv = Canvas(12, 60, pad=PAD)
    for y0 in range(0, 60, 15):
        gp.post(cv, 4, y0, y0 + 14, w=3, ramp=BLEACHED)
    for y in range(0, 60):
        cv.set(3, y, BLEACHED[2]); cv.set(8, y, BLEACHED[1])
    return cv


def props() -> dict[str, Canvas]:
    return {
        'saloon': false_front(104, 0, RED, 'saloon'), 'store': false_front(88, 3, WTR, 'store'),
        'water_tower': water_tower(), 'saguaro': saguaro(True), 'saguaro_small': saguaro(False),
        'tumbleweed': tumbleweed(), 'wagon': wagon(), 'windpump': windpump(), 'trough': trough(),
        'cow_skull': cow_skull(), 'mine_portal': mine_portal(), 'dry_well': dry_well(), 'keg': keg(),
        'hay_bale': hay_bale(), 'dynamite_crate': dynamite_crate(), 'hitching_rail': hitching_rail(),
        'poster_board': poster_board(), 'corral_side': corral_side(), 'corral_rail': corral_rail(),
    }


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (224, 181, 131, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/west-props.png'))
    print('sheet', out.size)
