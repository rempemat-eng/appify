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
BLEACHED = MATERIALS['bleached']  # sun-bleached boards
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def false_front(width: int = 104, seed: int = 0, sign_ramp=RED, kind: str = 'saloon') -> Canvas:
    """A false-front building, 104 x 92: the tall square facade hides a pitched tin roof
    (its top shows behind), bleached clapboards, a sign board with a pictogram
    (a mug or a sack), an upper window, a porch roof on posts that throws a deep shadow, and
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
    # a pictogram, not lettering (letters at this size read as nonsense words): a frothy
    # mug for the saloon, a tied sack for the store, with small diamonds either side
    mx = (sx0 + sx1) // 2
    if kind == 'saloon':
        for y in range(21, 28):
            cv.hline(mx - 4, y, 7, '#E8B04A' if y > 22 else ink)  # the mug, its froth on top
        cv.hline(mx - 4, 20, 7, ink); cv.set(mx - 3, 19, ink); cv.set(mx, 19, ink)
        cv.vline(mx + 3, 22, 4, ink); cv.vline(mx + 4, 22, 4, ink); cv.set(mx + 4, 22, sign_ramp[2]); cv.set(mx + 4, 25, sign_ramp[2])
        cv.vline(mx - 2, 23, 4, '#C8862A')
    else:
        for (x, y) in oval(mx, 24, 4.5, 3.6):
            cv.set(x, y, ink if x < mx + 1 else '#D8C8A0')  # the sack
        cv.hline(mx - 2, 20, 5, ink); cv.hline(mx - 1, 21, 3, '#C8862A')  # its tied neck
    for dx in (-14, -9, 9, 14):
        if sx0 + 2 < mx + dx < sx1 - 2:
            x = mx + dx
            cv.set(x, 22, ink); cv.set(x - 1, 23, ink); cv.set(x + 1, 23, ink); cv.set(x, 24, ink)
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


def palm(tall: bool = True) -> Canvas:
    """A date palm, 56 x 84 (or 48 x 64): a ringed, gently curved trunk lit on the left,
    a crown of long arching fronds lit on their upper faces, and a cluster of dates."""
    w, h = (56, 84) if tall else (48, 64)
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    top = 22 if tall else 18
    for y in range(top, h - 1):
        bend = int(math.sin((y - top) / (h - top) * 2.2) * 3)
        for dx in range(-3, 3):
            x = cx + bend + dx
            c = WOOD[3] if dx < -1 else WOOD[2] if dx < 1 else WOOD[1]
            if (y - top) % 4 == 0:
                c = WOOD[1] if dx > -2 else WOOD[2]  # the rings
            cv.set(x, y, c)
    for k in range(12):  # fronds arching out and down from the crown
        a = math.pi * (-0.05 + 1.1 * k / 11)
        length = (24 if tall else 19) + (k % 2) * 3
        for t in range(length):
            x = cx + math.cos(a) * t * (1 if k % 2 else 0.95)
            y = top + 6 - math.sin(a) * t * 0.85 + (t / length) ** 2 * 12
            for side in (-1, 1):  # leaflets either side of the rib
                lx, ly = int(x + side * 0.5), int(y + side * 1.2 + (1 if t % 3 == 0 else 0))
                cv.set(lx, ly, CACTUS[3] if side < 0 else CACTUS[1])
            cv.set(int(x), int(y), CACTUS[4] if t < length * 0.6 else CACTUS[2])
    for (x, y) in disc(cx + 3, top + 4, 2.5):
        cv.set(x, y, '#8A4A2A' if (x + y) % 2 else '#B8693F')
    return cv


def sandstone_arch() -> Canvas:
    """A ruined sandstone arch, 64 x 56: two weathered piers in courses, a broken lintel,
    sand drifted against its feet."""
    w, h = 64, 56
    cv = Canvas(w, h, pad=PAD)
    for (x0, x1) in ((4, 18), (46, 60)):
        for y in range(10, h - 4):
            for x in range(x0, x1):
                course = (y - 10) // 6
                c = ADOBE[4] if x < x0 + 3 else ADOBE[3] if x < x1 - 3 else ADOBE[2]
                if (y - 10) % 6 == 5 or (x + course * 4) % 9 == 0:
                    c = ADOBE[1]
                cv.set(x, y, c)
    for y in range(4, 12):  # the lintel, broken at the right
        for x in range(2, 50 + (y // 3)):
            cv.set(x, y, ADOBE[4] if y < 6 else ADOBE[3] if y < 10 else ADOBE[1])
    for (x, y) in oval(11, h - 3, 12, 4) | oval(53, h - 3, 12, 4):
        if y >= h - 5:
            cv.set(x, y, DESERT[4] if x < 32 else DESERT[3])
    return cv


def awning() -> Canvas:
    """A traders' shade awning, 72 x 50: striped cloth on poles seen from above, rugs
    and cushions in its shade, a brass tea tray."""
    w, h = 72, 50
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 22):
        for x in range(2, w - 2):
            stripe = (x // 6) % 3
            c = ('#C2453A', '#E8D8B8', '#3E6A8A')[stripe]
            if y > 18:
                c = ('#9A3028', '#C8B898', '#2C4A68')[stripe]
            cv.set(x, y, c)
    for px in (4, w - 7):
        gp.post(cv, px, 20, h - 2, w=2, ramp=WOOD)
    for (x, y) in ((xx, yy) for xx in range(10, w - 10) for yy in range(30, 44)):
        cv.set(x, y, '#8A3A2A' if (x // 4 + y // 4) % 2 else '#B8693F')
    for (cx0, c) in ((18, '#3E6A8A'), (50, GOLD[3])):
        for (x, y) in oval(cx0, 34, 5, 3):
            cv.set(x, y, c)
    for (x, y) in oval(34, 38, 5, 2.5):
        cv.set(x, y, MATERIALS['brass'][3] if x < 34 else MATERIALS['brass'][2])
    return cv


def water_jar() -> Canvas:
    """A tall clay water jar, 14 x 20, beaded with damp."""
    cv = Canvas(14, 20, pad=PAD)
    for (x, y) in oval(7, 12, 6, 7):
        cv.set(x, y, ADOBE[3] if x < 6 else ADOBE[2] if x < 9 else ADOBE[1])
    for (x, y) in oval(7, 4, 3, 1.5):
        cv.set(x, y, ADOBE[4])
    cv.set(5, 10, '#C6DDEE'); cv.set(4, 13, '#C6DDEE')
    return cv


CAMEL = ['#4E3222', '#7E5638', '#A87C52', '#C9A06E', '#E0C08E']


def camel() -> Canvas:
    """A camel resting with its legs folded under it, 48 x 36, seen from the side: the
    hump lit from the upper left, a striped saddle blanket, the long neck curving up to
    a drowsy head, the folded knees in the sand."""
    w, h = 48, 36
    cv = Canvas(w, h, pad=PAD)
    body = oval(20, 24, 16, 8) | oval(18, 15, 8, 6)  # body and hump
    for (x, y) in body:
        k = (x - 4) / 32 + (y - 8) / 22
        c = CAMEL[4] if k < 0.55 else CAMEL[3] if k < 0.95 else CAMEL[2] if k < 1.3 else CAMEL[1]
        cv.set(x, y, c)
    for y in range(12, 23):  # a woven saddle blanket over the hump, diamonds on red
        for x in range(11, 27):
            if (x, y) in body:
                d = (abs(x - 18) + abs(y - 17)) % 6
                c = '#9A3028' if x < 13 or y > 21 else '#B8443A' if d > 1 else GOLD[3] if d == 0 else '#2C2A3A'
                cv.set(x, y, c)
    cv.hline(11, 22, 16, GOLD[2])  # its fringe
    for t in range(18):  # the neck, curving up and forward
        x, y = 34 + t * 0.55, 22 - t * 0.9 + (t / 18) ** 2 * 3
        for d in range(-1, 2 + (t < 5)):
            cv.set(int(x + d * 0.3), int(y + d), CAMEL[3] if d < 0 else CAMEL[2] if d < 1 else CAMEL[1])
    for (x, y) in oval(44, 7, 4, 2.5):  # the head, eyes half shut
        cv.set(x, y, CAMEL[3] if y < 7 else CAMEL[2])
    cv.set(47, 8, CAMEL[0]); cv.set(43, 6, CAMEL[0]); cv.set(41, 4, CAMEL[2])
    for (kx, ky) in ((8, 31), (28, 31), (34, 30)):  # the folded knees
        for (x, y) in oval(kx, ky, 4, 2):
            cv.set(x, y, CAMEL[2] if x < kx else CAMEL[1])
    for x in range(4, 8):  # the tail
        cv.set(x - 2, 22 + (x - 4), CAMEL[1])
    return cv


def tent() -> Canvas:
    """A caravan tent, 72 x 48: dark woven goat-hair cloth pitched on poles, seen from
    above at the angle of the rest, its front panel rolled up to show the shade inside,
    guy ropes pegged in the sand."""
    w, h = 72, 48
    cv = Canvas(w, h, pad=PAD)
    cloth = ['#2A2220', '#3E3330', '#56484A', '#6E5E5C', '#8A7A72']
    poles = (22, 50)
    for x in range(6, w - 6):
        near = min(poles, key=lambda p: abs(x - p))
        d = abs(x - near)
        top = 4 + min(9, d * d // 22)  # the cloth sags between the poles
        if x < 14 or x > w - 15:
            top = max(top, 10 + abs(x - (14 if x < 14 else w - 15)))  # and falls away at the ends
        for y in range(top, 30):
            lit = x < near  # each peak's face towards the upper left catches the sun
            c = cloth[4] if lit and d < 6 and y < top + 6 else cloth[3] if lit else cloth[2]
            if y > 22:
                c = cloth[2] if lit else cloth[1]
            if (x * 2 + y * 3) % 13 == 0:
                c = cloth[1] if c not in (cloth[1], cloth[0]) else cloth[0]  # the weave
            if (x // 8) % 2 and y > top + 1 and (y - top) % 9 == 0:
                c = cloth[0]  # seams between the woven strips
            cv.set(x, y, c)
        cv.set(x, top, cloth[4] if x < near else cloth[3])
    for x in range(8, w - 8):  # the rolled front edge, white-striped
        cv.set(x, 30, '#E8D8B8' if (x // 3) % 2 else cloth[3])
        cv.set(x, 31, cloth[2])
    for y in range(32, 42):  # the shade inside, rugs and a cushion
        for x in range(12, w - 12):
            c = '#1E1614' if y < 34 else ('#8A3A2A' if (x // 4 + y // 4) % 2 else '#B8693F')
            cv.set(x, y, c)
    for (x, y) in oval(24, 37, 4, 2):
        cv.set(x, y, GOLD[3] if x < 24 else GOLD[2])
    for px in (12, 36, w - 13):
        gp.post(cv, px, 28, 42, w=1, ramp=WOOD)
    for (x0, y0, x1, y1) in ((6, 12, 1, 4), (w - 7, 12, w - 2, 4), (6, 26, 1, 40), (w - 7, 26, w - 2, 40)):
        for t in range(9):
            cv.set(int(x0 + (x1 - x0) * t / 8), int(y0 + (y1 - y0) * t / 8), MATERIALS['rope'][2])
    return cv


def fire_pit() -> Canvas:
    """A ring of stones round the embers of a small fire, 20 x 14, a teapot warming."""
    cv = Canvas(20, 14, pad=PAD)
    for k in range(10):
        a = 2 * math.pi * k / 10
        x, y = 10 + math.cos(a) * 7, 8 + math.sin(a) * 4
        for (sx, sy) in disc(x, y, 1.6):
            cv.set(sx, sy, STONE[3] if sy < y else STONE[1])
    for (x, y) in oval(10, 8, 4, 2):
        cv.set(x, y, '#3A2A22' if (x + y) % 2 else '#7A1A08')
    cv.set(9, 8, '#F2721E'); cv.set(11, 7, '#FFB648'); cv.set(10, 9, '#C2380E')
    for (x, y) in oval(15, 4, 2.5, 2):
        cv.set(x, y, MATERIALS['brass'][3] if x < 15 else MATERIALS['brass'][1])
    cv.set(18, 3, MATERIALS['brass'][2])
    return cv


def column_stump(seed: int = 0) -> Canvas:
    """A broken sandstone column, 16 x 26: fluted drums lit on the left, a jagged break
    at the top, one fallen drum and sand drifted at its foot."""
    cv = Canvas(16, 26, pad=PAD)
    top = 4 + seed % 3
    for y in range(top, 23):
        for x in range(3, 12):
            c = ADOBE[4] if x < 5 else ADOBE[3] if x < 9 else ADOBE[2]
            if (x - 3) % 3 == 2:
                c = ADOBE[2] if x < 9 else ADOBE[1]  # flutes
            if (y - top) % 7 == 6:
                c = ADOBE[1]
            cv.set(x, y, c)
    for x in range(3, 12):  # the break
        for y in range(top - 2 + int(noise2(x, seed, 470) * 3), top + 1):
            cv.set(x, y, ADOBE[4] if x < 8 else ADOBE[3])
    for (x, y) in oval(8, 23, 7, 2.5):
        if y >= 23:
            cv.set(x, y, DESERT[4] if x < 8 else DESERT[3])
    return cv


def papyrus() -> Canvas:
    """A clump of papyrus by the water, 22 x 28: tall stems ending in green tufts."""
    cv = Canvas(22, 28, pad=PAD)
    for k in range(7):
        bx = 5 + k * 2
        lean = (k - 3) * 0.35
        top = 6 + (k * 5) % 7
        for y in range(top, 27):
            cv.set(int(bx + lean * (27 - y) / 4), y, CACTUS[2] if k % 2 else CACTUS[3])
        tx = int(bx + lean * (27 - top) / 4)
        for (x, y) in disc(tx, top - 1, 2.6):
            cv.set(x, y, CACTUS[4] if x <= tx and y < top else CACTUS[3] if (x + y) % 2 else CACTUS[2])
    return cv


def shaduf() -> Canvas:
    """A shaduf, 56 x 52: the old lever for lifting water, a long pole balanced on a mud
    pillar with a stone counterweight at one end and a leather bucket on a rope at the
    other."""
    w, h = 56, 52
    cv = Canvas(w, h, pad=PAD)
    for y in range(22, h - 2):  # the pillar
        for x in range(20, 28):
            c = ADOBE[3] if x < 22 else ADOBE[2] if x < 26 else ADOBE[1]
            if (y + (x // 4) * 3) % 8 == 0:
                c = ADOBE[1]
            cv.set(x, y, c)
    for x in range(19, 29):
        cv.set(x, 21, ADOBE[4])
    for t in range(50):  # the pole, high over the water end
        x, y = 2 + t, 30 - t * 0.5
        cv.set(int(x), int(y), WOOD[3]); cv.set(int(x), int(y) + 1, WOOD[1])
    for (x, y) in disc(5, 30, 4):
        cv.set(x, y, STONE[3] if x + y < 33 else STONE[1])
    for y in range(6, 30):
        cv.set(51, y, MATERIALS['rope'][2])
    for (x, y) in oval(51, 32, 3.5, 3):
        cv.set(x, y, '#6A3E26' if x < 51 else '#4A2A1A')
    cv.hline(48, 30, 7, '#8A5A3A')
    return cv



def water_crane() -> Canvas:
    """A railway water crane, 34 x 56: an iron standpipe on a stone plinth, its arm
    swung out over the line with a canvas drop hose, a wheel valve, a red cap. The pipe
    under the sand brings it water from the spring."""
    w, h = 34, 56
    cv = Canvas(w, h, pad=PAD)
    for y in range(46, 54):
        for x in range(6, 22):
            cv.set(x, y, STONE[4] if y == 46 else STONE[3] if x < 9 else STONE[2] if x < 19 else STONE[1])
    for y in range(10, 46):
        for x in range(11, 17):
            cv.set(x, y, IRON[4] if x == 11 else IRON[3] if x < 14 else IRON[2] if x < 16 else IRON[1])
        if y % 12 == 0:
            cv.hline(10, y, 8, IRON[1])
    for x in range(8, 32):  # the arm
        for y in range(10, 14):
            cv.set(x, y, IRON[3] if y == 10 else IRON[2] if y < 13 else IRON[0])
    for y in range(14, 30):  # the drop hose
        cv.set(29, y, '#8A7A5A' if y % 3 else '#6E6046'); cv.set(30, y, '#6E6046')
    for (x, y) in disc(14, 6, 3):
        cv.set(x, y, RED[3] if x + y < 20 else RED[1])
    for k in range(12):
        a = 2 * math.pi * k / 12
        cv.set(int(round(19 + math.cos(a) * 3)), int(round(30 + math.sin(a) * 3)), RED[2])
    cv.set(19, 30, IRON[1]); cv.hline(17, 30, 2, IRON[1])
    return cv

def acacia() -> Canvas:
    """A desert acacia, 56 x 46: a flat umbrella crown of small olive leaf clumps (light
    caps, dark rims; style.leafy) on a leaning, forked trunk."""
    import style
    w, h = 56, 46
    cv = Canvas(w, h, pad=PAD)
    BARK = ['#3A2618', '#5A3C24', '#7A5434', '#9A7048', '#B88E62']
    for (x0, y0, x1, y1, wd) in ((26, h - 2, 24, 22, 3), (25, 28, 14, 16, 2), (25, 26, 40, 15, 2), (24, 24, 28, 12, 1)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            x, y = x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n
            for dx in range(wd + 1):
                cv.set(int(x) + dx, int(y), BARK[3] if dx == 0 else BARK[2] if dx < wd else BARK[1])
    OLIVE = ['#2E3A1C', '#4A5A2A', '#6A7A38', '#8E9A4A', '#B4BA6A']
    style.leafy(cv, 27, 12, 25, 8, OLIVE, r=2.4, seed=17)
    return cv


def desert_scrub(seed: int = 0) -> Canvas:
    """A low tamarisk scrub, 26 x 16: a tangle of grey-green feathery clumps with a few
    pink flower tips, dry twigs at its feet."""
    import style
    w, h = 26, 16
    cv = Canvas(w, h, pad=PAD)
    SAGE = ['#38402C', '#56603E', '#78825A', '#98A27A', '#BCC4A0']
    style.leafy(cv, 13, 8, 11, 5.5, SAGE, r=2.0, seed=seed + 9)
    for k in range(4):
        x, y = 5 + int(noise2(k, seed, 378) * 16), 4 + int(noise2(k, seed, 379) * 5)
        if cv.get(x, y)[3]:
            cv.set(x, y, '#E8A0BC')
    return cv


def sandstone_outcrop(seed: int = 0) -> Canvas:
    """Weathered sandstone blocks breaking out of the dune, 40 x 24: layered beds in
    adobe tones (lit tops, shaded right flanks; style.facet_stone), sand piled at the foot."""
    import style
    w, h = 40, 24
    cv = Canvas(w, h, pad=PAD)
    for k, (cx, cy, rx, ry) in enumerate(((16, 12, 13, 9), (30, 15, 9, 7), (8, 18, 6, 4))):
        pts = {(x, y) for y in range(cy - ry, cy + ry + 1) for x in range(cx - rx, cx + rx + 1)
               if max(abs(x - cx) / rx, abs(y - cy) / ry) * 0.7 + math.hypot((x - cx) / rx, (y - cy) / ry) * 0.3 <= 1}
        style.facet_stone(cv, pts, ADOBE, seed=seed + k)
        for (x, y) in pts:  # the beds
            if (y - cy + 40) % 4 == 0 and (x, y - 1) in pts and (x, y + 1) in pts:
                cv.set(x, y, ADOBE[1] if x > cx else ADOBE[2])
    for (x, y) in oval(20, h - 2, 18, 2.5):
        if y >= h - 3:
            cv.set(x, y, DESERT[4] if x < 20 else DESERT[3])
    return cv


def horse() -> Canvas:
    """A bay horse dozing on its feet in the corral, 44 x 36, seen from the side: the
    body lit along its back, a dark mane and tail, one hind hoof cocked (resting), the
    head low and its eyes shut."""
    w, h = 44, 36
    cv = Canvas(w, h, pad=PAD)
    BAY = ['#3A2218', '#5E3A24', '#80522E', '#A06A3C', '#C08850']
    body = oval(20, 17, 13, 7)
    for (x, y) in body:
        k = (x - 7) / 26 + (y - 10) / 14
        cv.set(x, y, BAY[4] if k < 0.45 else BAY[3] if k < 0.9 else BAY[2] if k < 1.3 else BAY[1])
    for (lx, cocked) in ((10, False), (14, True), (27, False), (30, False)):  # legs
        for y in range(22, h - 2 - (2 if cocked else 0)):
            cv.set(lx, y, BAY[2] if lx in (10, 27) else BAY[1]); cv.set(lx + 1, y, BAY[1])
        foot = h - 2 - (2 if cocked else 0)
        cv.hline(lx, foot, 2, '#2A2026')
        cv.set(lx, foot - 2, '#E8DCC8') if lx == 27 else None  # one white sock
    for t in range(9):  # the neck, low and forward
        x, y = 31 + t, 13 + t * 0.6
        for d in range(-2, 3):
            cv.set(int(x), int(y + d), BAY[3] if d < 0 else BAY[2])
    for (x, y) in oval(41, 20, 3.5, 2.8):  # the head, dozing
        cv.set(x, y, BAY[3] if y < 20 else BAY[2])
    cv.set(43, 22, BAY[0]); cv.set(40, 19, BAY[0]); cv.set(39, 16, BAY[2])
    for t in range(9):  # the mane
        cv.set(30 + t, 11 + int(t * 0.6), BAY[0]); cv.set(30 + t, 12 + int(t * 0.6), BAY[1])
    for t in range(10):  # the tail
        cv.set(7 - t // 4, 14 + t, BAY[0]); cv.set(8 - t // 4, 14 + t, BAY[1])
    return cv


def prickly_pear() -> Canvas:
    """A prickly pear, 20 x 18: flat round pads lit upper left, spines, two red fruit."""
    w, h = 20, 18
    cv = Canvas(w, h, pad=PAD)
    PAD_G = ['#2E5A34', '#447A44', '#62995A', '#8CBB72']
    for (cx, cy, rx, ry) in ((10, 13, 5, 4), (6, 8, 4, 3.5), (14, 7, 3.5, 3.2)):
        for (x, y) in oval(cx, cy, rx, ry):
            k = (x - cx) / rx + (y - cy) / ry
            cv.set(x, y, PAD_G[3] if k < -0.6 else PAD_G[2] if k < 0.4 else PAD_G[1])
        for (dx, dy) in ((-2, -1), (1, 1), (2, -2)):
            cv.set(cx + dx, cy + dy, '#E8DCC8')
    cv.set(6, 4, '#C2453A'); cv.set(7, 4, '#9A3028'); cv.set(15, 3, '#C2453A')
    return cv


def props() -> dict[str, Canvas]:
    return {
        'saloon': false_front(104, 0, RED, 'saloon'), 'store': false_front(88, 3, WTR, 'store'),
        'water_tower': water_tower(), 'saguaro': saguaro(True), 'saguaro_small': saguaro(False),
        'tumbleweed': tumbleweed(), 'wagon': wagon(), 'windpump': windpump(), 'trough': trough(),
        'cow_skull': cow_skull(), 'mine_portal': mine_portal(), 'dry_well': dry_well(), 'keg': keg(),
        'hay_bale': hay_bale(), 'dynamite_crate': dynamite_crate(), 'hitching_rail': hitching_rail(),
        'poster_board': poster_board(), 'corral_side': corral_side(), 'corral_rail': corral_rail(),
        'palm': palm(True), 'palm_small': palm(False), 'sandstone_arch': sandstone_arch(), 'awning': awning(),
        'water_jar': water_jar(), 'camel': camel(), 'tent': tent(), 'fire_pit': fire_pit(),
        'column_stump': column_stump(0), 'column_stump_b': column_stump(2), 'papyrus': papyrus(), 'shaduf': shaduf(),
        'water_crane': water_crane(), 'acacia': acacia(), 'desert_scrub': desert_scrub(0),
        'desert_scrub_b': desert_scrub(4), 'sandstone_outcrop': sandstone_outcrop(0), 'sandstone_outcrop_b': sandstone_outcrop(5),
        'horse': horse(), 'prickly_pear': prickly_pear(),
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
