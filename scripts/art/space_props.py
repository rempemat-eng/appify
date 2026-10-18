"""Props for Halcyon Station and the moon Lumen, the end of the line (world-atlas.md).

On the station, light comes from panels and the planet below: hull plates in cool
greys with a bright top edge, round viewports, garden pods under glass. On Lumen the
light is starlight and the plants' own glow. Run directly for a contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
from materials import MATERIALS, LEAF, NAP, GOLD, RED, WTR, WOOD  # noqa: E402

HULL, VOID, REGOLITH, GLOW = (MATERIALS[k] for k in ('hull', 'void', 'regolith', 'glowflora'))
CYAN = MATERIALS['neon_cyan']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def garden_pod() -> Canvas:
    """A hydroponic garden pod, 64 x 56: a glass dome seen from above with plants in
    rings under it, a reflection arc on the glass, and a hull collar with status lights."""
    w, h = 64, 56
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(32, 40, 30, 12):  # the collar
        cv.set(x, y, HULL[3] if y < 40 else HULL[2])
    for (x, y) in oval(32, 28, 26, 22):  # dark soil under the dome
        if y < 44:
            cv.set(x, y, '#3A2A24' if (x + y) % 3 else '#4A362C')
    for ring, r in enumerate((6, 12, 18)):  # plants in rings round the centre
        for k in range(6 + ring * 5):
            a = 2 * math.pi * k / (6 + ring * 5) + ring * 0.3
            px, py = 32 + math.cos(a) * r * 1.1, 28 + math.sin(a) * r * 0.9
            for (x, y) in disc(px, py, 2.4):
                if y < 44:
                    cv.set(x, y, LEAF[3] if (x - px) + (y - py) < 0 else LEAF[2])
            if ring == 1 and k % 2 == 0:
                cv.set(int(px), int(py) - 1, RED[3])  # tomatoes
            if ring == 2 and k % 3 == 0:
                cv.set(int(px), int(py) - 1, GOLD[4])
    for (x, y) in oval(32, 28, 26, 22):
        if y < 44 and math.hypot((x - 22) / 18, (y - 18) / 12) < 1 and math.hypot((x - 24) / 18, (y - 21) / 12) > 1:
            cv.set(x, y, '#E6F2FF')  # the glass's reflection arc
    for (x, y) in oval(32, 28, 26, 22):
        if y < 44 and (math.hypot((x - 32) / 25, (y - 28) / 21) > 1):
            cv.set(x, y, HULL[4])
    for k, lx in enumerate(range(12, 54, 10)):
        cv.set(lx, 46, (CYAN[3], GOLD[3], CYAN[3], RED[3], CYAN[3])[k % 5])
    return cv


def viewport() -> Canvas:
    """A floor-to-ceiling window onto the planet, 120 x 70: a hull frame with ribs, the
    planet's curve below with cloud bands and the thin blue rim of its air, stars."""
    w, h = 120, 70
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rect_set(4, 4, w - 8, h - 12):
        cv.set(x, y, VOID[0] if noise2(x, y, 341) > 0.02 else '#FFFFFF')
    for (x, y) in rect_set(4, 4, w - 8, h - 12):
        d = math.hypot(x - 60, y - 160)
        if d < 118:
            band = int((y + math.sin(x / 9) * 2) / 4) % 3
            cv.set(x, y, ('#3E6AA8', '#5A8AC4', '#E6EEF6')[band] if d < 116 else '#9AD2FF')
    for rx in range(4, w - 4, 28):
        for y in range(4, h - 8):
            cv.set(rx, y, HULL[3]); cv.set(rx + 1, y, HULL[2])
    for x in range(0, w):
        for y in range(0, 4):
            cv.set(x, y, HULL[4] if y == 0 else HULL[3])
        for y in range(h - 8, h):
            cv.set(x, y, HULL[2] if y < h - 4 else HULL[1])
    return cv


def sleep_pod() -> Canvas:
    """A crew sleep pod, 30 x 48: a capsule bed under a frosted lid lit softly from
    inside, a dim violet night light and a folded blanket."""
    cv = Canvas(30, 48, pad=PAD)
    body = oval(15, 24, 13, 22)
    for (x, y) in body:
        k = (x - 2) / 26
        cv.set(x, y, HULL[4] if k < 0.2 else HULL[3] if k < 0.6 else HULL[2])
    for (x, y) in oval(15, 22, 9, 17):
        cv.set(x, y, NAP[4] if (x + y) % 4 else NAP[3])
    for (x, y) in rect_set(8, 30, 14, 6):
        cv.set(x, y, NAP[2] if y < 32 else NAP[1])
    cv.set(15, 4, NAP[4]); cv.set(14, 4, NAP[3]); cv.set(16, 4, NAP[3])
    return cv


def airlock() -> Canvas:
    """The space elevator's arrival hatch, 56 x 50: a round door with a lit rim, warning
    chevrons and a status panel."""
    cv = Canvas(56, 50, pad=PAD)
    for (x, y) in rect_set(2, 4, 52, 44):
        cv.set(x, y, HULL[3] if y < 8 else HULL[2])
    for (x, y) in disc(28, 28, 16):
        cv.set(x, y, HULL[4] if (x - 28) + (y - 28) < -10 else HULL[1])
    for (x, y) in disc(28, 28, 13):
        cv.set(x, y, HULL[3] if x < 28 else HULL[2])
    cv.vline(28, 15, 27, HULL[0])
    for x in range(4, 52, 6):
        for t in range(3):
            cv.set(x + t, 44 + t % 2, GOLD[3])
            cv.set(x + t + 3, 44 + t % 2, VOID[2])
    cv.rect(44, 10, 6, 8, VOID[1]); cv.set(46, 12, CYAN[3]); cv.set(46, 15, GOLD[3])
    return cv


def console() -> Canvas:
    """A navigation console, 40 x 26: a sloped panel of soft screens and buttons."""
    cv = Canvas(40, 26, pad=PAD)
    for (x, y) in rect_set(2, 6, 36, 18):
        cv.set(x, y, HULL[3] if y < 9 else HULL[2])
    for (x0, c) in ((6, CYAN), (18, CYAN), (30, NAP)):
        for (x, y) in rect_set(x0, 10, 8, 6):
            cv.set(x, y, c[3] if y < 12 else c[2])
    for x in range(6, 36, 4):
        cv.set(x, 19, (RED[3], GOLD[3], CYAN[3])[x % 3])
    return cv


def moon_shrub() -> Canvas:
    """A glowing Lumen shrub, 34 x 36: translucent curling fronds lit from within,
    brightest at their tips, with a bulb at the heart and spores drifting off."""
    cv = Canvas(34, 36, pad=PAD)
    for k in range(11):
        a = math.pi * (0.08 + 0.84 * k / 10)
        curl = 0.06 * (1 if k % 2 else -1)
        x, y = 17.0, 32.0
        for t in range(16):
            x += math.cos(a + curl * t) * 0.95
            y -= math.sin(a + curl * t) * 1.1
            c = GLOW[1] if t < 4 else GLOW[2] if t < 9 else GLOW[3] if t < 13 else GLOW[4]
            cv.set(int(x), int(y), c)
            if t > 6:
                cv.set(int(x) + 1, int(y), GLOW[1])
    for (x, y) in disc(17, 30, 3.2):
        cv.set(x, y, GLOW[4] if (x - 17) + (y - 30) < 0 else GLOW[3])
    for (sx, sy) in ((5, 6), (28, 4), (16, 1), (9, 2)):
        cv.set(sx, sy, GLOW[4])
    return cv


def moon_crystal() -> Canvas:
    """A cluster of pale moon crystals, 26 x 30: faceted prisms, lit facets toward the
    sky, a violet core."""
    cv = Canvas(26, 30, pad=PAD)
    for (cx, top, half) in ((9, 4, 4), (16, 0, 5), (21, 10, 3)):
        for y in range(top, 28):
            hw = half if y > top + half else (y - top)
            for x in range(cx - hw, cx + hw + 1):
                k = (x - (cx - hw)) / (2 * hw + 1)
                cv.set(x, y, '#E6E0FA' if k < 0.3 else '#B8AEE6' if k < 0.6 else NAP[2])
    return cv


def shuttle() -> Canvas:
    """The little shuttle landed on Lumen, 84 x 56: a rounded white hull from above with
    a cockpit glazing, stubby wings, landing legs and a glowing engine bell."""
    w, h = 84, 56
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(42, 26, 22, 18):
        k = (x - 20) / 44 + (y - 8) / 36
        cv.set(x, y, '#F4F6FA' if k < 0.5 else '#D2D8E4' if k < 1.0 else '#A9B2C4')
    for side in (-1, 1):
        for t in range(16):
            for y in range(28, 36 - t // 3):
                cv.set(42 + side * (20 + t), y, HULL[3] if side < 0 else HULL[2])
    for (x, y) in oval(42, 18, 9, 5):
        cv.set(x, y, '#5A8AC4' if y < 18 else '#2C4A78')
    cv.set(38, 16, '#E6F2FF')
    for (x, y) in oval(42, 45, 7, 3):
        cv.set(x, y, CYAN[3] if y < 45 else CYAN[2])
    for lx in (26, 58):
        cv.vline(lx, 36, 12, HULL[2]); cv.hline(lx - 2, 48, 5, HULL[1])
    return cv


def dream_pool() -> Canvas:
    """A still pool of light on Lumen where the companion can rest, 48 x 26: a rim of
    pale stones round water that holds the stars."""
    w, h = 48, 26
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(24, 13, 22, 11):
        cv.set(x, y, REGOLITH[4] if x < 24 else REGOLITH[3])
    for (x, y) in oval(24, 13, 18, 8):
        cv.set(x, y, VOID[2] if (x + y) % 5 else VOID[3])
        if noise2(x, y, 342) > 0.94:
            cv.set(x, y, '#FFFFFF')
    for (x, y) in oval(24, 13, 18, 8):
        if (x, y - 1) not in oval(24, 13, 18, 8):
            cv.set(x, y, GLOW[3])
    return cv


def hydro_trough() -> Canvas:
    """A hydroponic trough, 56 x 30: a white tank of leafy greens in rows (lettuce and
    herbs, lit from above), a violet grow-light bar on two arms, a drip line."""
    w, h = 56, 30
    cv = Canvas(w, h, pad=PAD)
    for y in range(14, 28):
        for x in range(2, w - 2):
            c = HULL[5] if y == 14 else HULL[4] if y < 20 else HULL[3] if x < w - 6 else HULL[2]
            cv.set(x, y, c)
    for k in range(9):  # heads of greens in two rows
        for row in (0, 1):
            cx, cy = 7 + k * 5 + row * 2, 13 + row * 3
            for (x, y) in disc(cx, cy, 2.6):
                cv.set(x, y, LEAF[4] if x + y < cx + cy - 1 else LEAF[3] if (x + y) % 2 else LEAF[2])
    for px in (4, w - 6):
        cv.vline(px, 2, 12, HULL[3]); cv.vline(px + 1, 2, 12, HULL[1])
    for x in range(4, w - 4):
        cv.set(x, 2, NAP[4]); cv.set(x, 3, NAP[3]); cv.set(x, 4, HULL[1])
    for x in range(6, w - 6, 3):
        cv.set(x, 5, NAP[2] if x % 2 else NAP[1])  # the violet light falling
    cv.hline(3, 22, w - 6, CYAN[2])
    return cv


def galley_table() -> Canvas:
    """The galley table, 52 x 34: a round white table with two mugs and a teapot, four
    stools round it, the crew's one shared meal a day."""
    w, h = 52, 34
    cv = Canvas(w, h, pad=PAD)
    for (sx, sy) in ((6, 16), (46, 16), (26, 4), (26, 30)):
        for (x, y) in oval(sx, sy, 5, 3):
            cv.set(x, y, NAP[3] if y < sy else NAP[2])
        cv.set(sx, sy + 3, HULL[1])
    for (x, y) in oval(26, 16, 16, 9):
        k = (x - 10) / 32 + (y - 7) / 18
        cv.set(x, y, HULL[5] if k < 0.5 else HULL[4] if k < 1.0 else HULL[3])
    for y in range(25, 28):
        cv.hline(23, y, 6, HULL[1])
    for (mx, my, c) in ((18, 14, RED[3]), (32, 18, GOLD[3])):
        for (x, y) in disc(mx, my, 2):
            cv.set(x, y, c)
        cv.set(mx, my, '#5A3A24')
    for (x, y) in oval(26, 13, 4, 3):
        cv.set(x, y, WTR[3] if x < 26 else WTR[2])
    cv.set(30, 12, WTR[2]); cv.set(26, 9, HULL[5])
    return cv


def bookshelf() -> Canvas:
    """A curved bookshelf, 44 x 46, its shelves held by elastic straps against zero g:
    spines in soft colours, a plant trailing from the top."""
    w, h = 44, 46
    cv = Canvas(w, h, pad=PAD)
    for y in range(8, h - 2):
        for x in range(2, w - 2):
            cv.set(x, y, HULL[3] if x < 5 else HULL[2] if x < w - 5 else HULL[1])
    cols = [RED[3], GOLD[3], NAP[3], LEAF[3], WTR[3], '#E8D8B8', RED[2], NAP[2]]
    for shelf in range(3):
        y0 = 11 + shelf * 11
        x = 6
        k = shelf * 3
        while x < w - 7:
            bw = 2 + (k * 7) % 3
            bh = 7 + (k * 5) % 3
            for yy in range(y0 + 9 - bh, y0 + 9):
                for xx in range(x, min(x + bw, w - 6)):
                    cv.set(xx, yy, cols[k % len(cols)] if xx > x else HULL[0])
            x += bw + 1
            k += 1
        cv.hline(5, y0 + 9, w - 10, HULL[4])
        cv.hline(5, y0 + 5, w - 10, CYAN[1])  # the strap
    for (x, y) in disc(12, 6, 5):  # the plant on top, trailing down the side
        cv.set(x, y, LEAF[4] if x + y < 16 else LEAF[2])
    for t in range(14):
        cv.set(4 + (t % 2), 8 + t, LEAF[3] if t % 3 else LEAF[1])
    return cv


def telescope() -> Canvas:
    """A brass telescope on a tripod, 30 x 40, pointed out of the viewport at the planet."""
    w, h = 30, 40
    cv = Canvas(w, h, pad=PAD)
    for t in range(22):  # the tube, raised toward the upper right
        x, y = 6 + t, 20 - t * 0.6
        for d in range(-2, 3):
            cv.set(int(x), int(y + d), GOLD[4] if d < -1 else GOLD[3] if d < 1 else GOLD[1])
    for (x, y) in disc(27, 7, 2.5):
        cv.set(x, y, HULL[1])
    for (dx, ex) in ((14, 5), (16, 16), (18, 26)):
        for t in range(18):
            cv.set(int(dx + (ex - dx) * t / 18), 20 + t, HULL[3] if ex < 16 else HULL[1])
    return cv


def lounge_bench() -> Canvas:
    """A low padded bench, 52 x 18, cushions in soft violet, for watching the planet."""
    w, h = 52, 18
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, 14):
        for x in range(2, w - 2):
            cv.set(x, y, HULL[3] if y > 11 else NAP[3] if y < 8 else NAP[2])
    for cx in (10, 26, 42):
        for (x, y) in oval(cx, 6, 6, 3):
            cv.set(x, y, NAP[4] if x < cx else NAP[3])
    cv.hline(2, 14, w - 4, HULL[1])
    return cv


def lockers() -> Canvas:
    """Crew lockers, 46 x 40: four tall doors with name glyphs and a pressed suit badge."""
    w, h = 46, 40
    cv = Canvas(w, h, pad=PAD)
    for k in range(4):
        x0 = 2 + k * 11
        for y in range(4, h - 2):
            for x in range(x0, x0 + 10):
                cv.set(x, y, HULL[4] if x == x0 or y == 4 else HULL[3] if x < x0 + 8 else HULL[2])
        for x in range(x0 + 2, x0 + 8, 2):
            cv.set(x, 9, (CYAN[3], GOLD[3], NAP[3], LEAF[4])[k])
        cv.hline(x0 + 7, 20, 2, HULL[1])
        for y in range(28, 34, 2):
            cv.hline(x0 + 2, y, 6, HULL[1])  # vents
    return cv


def tea_dispenser() -> Canvas:
    """A wall tea dispenser, 18 x 30: a squat urn with a warm amber light and a cup."""
    cv = Canvas(18, 30, pad=PAD)
    for y in range(4, 24):
        for x in range(3, 15):
            cv.set(x, y, HULL[5] if x < 5 else HULL[4] if x < 12 else HULL[2])
    for (x, y) in rect_set(5, 8, 8, 5):
        cv.set(x, y, GOLD[3] if y < 10 else GOLD[2])
    cv.hline(7, 16, 4, HULL[0]); cv.set(9, 17, WTR[2])
    for (x, y) in rect_set(7, 19, 4, 4):
        cv.set(x, y, '#F2EEE6' if x < 9 else '#D8D2C6')
    cv.hline(3, 24, 12, HULL[1])
    return cv


def moon_tree() -> Canvas:
    """The sleeping tree at the heart of Lumen, 76 x 92: a pale twisted trunk lit from
    the upper left, a wide crown of soft teal leaves glowing from within, and lantern
    pods hanging from its boughs like slow breaths."""
    w, h = 76, 92
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(44, h - 2):  # the trunk, twisting, with roots spreading
        t = (y - 44) / (h - 46)
        twist = int(math.sin(t * 4) * 2)
        hw = 4 + int(t * t * 8)
        for x in range(cx - hw + twist, cx + hw + twist):
            k = (x - (cx - hw + twist)) / (2 * hw)
            c = REGOLITH[5] if k < 0.25 else REGOLITH[4] if k < 0.55 else REGOLITH[3] if k < 0.8 else REGOLITH[2]
            if (y + x // 3) % 7 == 0:
                c = REGOLITH[2]  # the bark's spiral grain
            cv.set(x, y, c)
    for (bx, by, ex, ey) in ((cx, 50, 14, 34), (cx, 48, 62, 30), (cx, 46, 30, 22)):
        for t in range(24):
            x, y = bx + (ex - bx) * t / 23, by + (ey - by) * t / 23
            cv.set(int(x), int(y), REGOLITH[4]); cv.set(int(x), int(y) + 1, REGOLITH[2])
    clumps = []  # the crown in soft clumps, each lit on its own upper left
    for i in range(46):
        a = noise2(i, 0, 360) * 2 * math.pi
        r = math.sqrt(noise2(i, 1, 360))
        clumps.append((cx + math.cos(a) * r * 30, 27 + math.sin(a) * r * 18, 5 + noise2(i, 2, 360) * 3))
    for (ccx, ccy, cr) in sorted(clumps, key=lambda c: c[1]):
        base = (ccx - 4) / 68 + (ccy - 6) / 46  # where the clump sits in the crown's light
        for (x, y) in disc(ccx, ccy, cr):
            k = base + ((x - ccx) + (y - ccy)) / (cr * 4)
            c = GLOW[4] if k < 0.5 else GLOW[3] if k < 0.85 else GLOW[2] if k < 1.2 else GLOW[1]
            cv.set(x, y, c)
    for (px, py) in ((16, 44), (30, 50), (50, 48), (62, 42), (40, 52)):  # hanging lantern pods
        cv.vline(px, py - 6, 6, GLOW[1])
        for (x, y) in oval(px, py + 2, 2.5, 3.5):
            cv.set(x, y, '#FFF6D0' if x < px else '#F2D27A')
    return cv


def hammock() -> Canvas:
    """A hammock slung between two crystal spires, 68 x 40: soft woven cloth in nap
    violet sagging in the low gravity, a folded blanket and a small pillow in it."""
    w, h = 68, 40
    cv = Canvas(w, h, pad=PAD)
    for (cx, top) in ((5, 2), (62, 4)):  # the spires
        for y in range(top, h - 2):
            hw = min(4, (y - top) // 2 + 1)
            for x in range(cx - hw, cx + hw + 1):
                k = (x - (cx - hw)) / (2 * hw + 1)
                cv.set(x, y, '#E6E0FA' if k < 0.35 else '#B8AEE6' if k < 0.7 else NAP[2])
    for x in range(9, 59):  # the cloth, sagging
        t = (x - 9) / 49
        y0 = int(14 + math.sin(t * math.pi) * 10)
        for y in range(y0, y0 + 5):
            c = NAP[4] if y == y0 else NAP[3] if (x // 3 + y) % 2 else NAP[2]
            cv.set(x, y, c)
        if x % 4 == 0:
            cv.set(x, y0 + 5, NAP[1])  # its fringe
    for (x, y) in oval(22, 20, 6, 2.5):
        cv.set(x, y, '#F2EEE6' if x < 22 else '#D8D2C6')  # pillow
    for x in range(30, 46):
        cv.set(x, 22, GOLD[3]); cv.set(x, 23, GOLD[2])  # the blanket's edge
    for (ax, ay, bx, by) in ((6, 10, 10, 15), (61, 12, 57, 15)):
        for t in range(6):
            cv.set(int(ax + (bx - ax) * t / 5), int(ay + (by - ay) * t / 5), REGOLITH[1])
    return cv


def moon_rock(big: bool = True) -> Canvas:
    """A moon boulder, 30 x 20 (or 18 x 12): rounded, lit on its upper left, a sharp
    dark side in the airless light."""
    w, h = (30, 20) if big else (18, 12)
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in oval(w / 2, h / 2 + 1, w / 2 - 2, h / 2 - 2):
        k = (x - 2) / (w - 4) + (y - 2) / (h - 4)
        c = REGOLITH[5] if k < 0.5 else REGOLITH[4] if k < 0.9 else REGOLITH[2] if k < 1.3 else REGOLITH[1]
        if noise2(x // 2, y // 2, 365 + w) > 0.82:
            c = REGOLITH[3]
        cv.set(x, y, c)
    return cv


def glow_caps() -> Canvas:
    """A ring of little glowing mushrooms, 26 x 14, their caps lit from beneath."""
    cv = Canvas(26, 14, pad=PAD)
    for k, (mx, my, r) in enumerate(((5, 8, 3), (12, 5, 4), (20, 8, 3), (16, 11, 2), (8, 11, 2))):
        cv.vline(mx, my, 3, REGOLITH[4])
        for (x, y) in oval(mx, my, r, r * 0.6):
            if y <= my:
                cv.set(x, y, GLOW[4] if x < mx else GLOW[3])
        cv.set(mx - 1, my, GLOW[2])
    return cv


def props_station() -> dict[str, Canvas]:
    return {'garden_pod': garden_pod(), 'viewport': viewport(), 'sleep_pod': sleep_pod(), 'airlock': airlock(),
            'console': console(), 'hydro_trough': hydro_trough(), 'galley_table': galley_table(),
            'bookshelf': bookshelf(), 'telescope': telescope(), 'lounge_bench': lounge_bench(), 'lockers': lockers(),
            'tea_dispenser': tea_dispenser()}


def props_lumen() -> dict[str, Canvas]:
    return {'moon_shrub': moon_shrub(), 'moon_crystal': moon_crystal(), 'shuttle': shuttle(), 'dream_pool': dream_pool(),
            'moon_tree': moon_tree(), 'hammock': hammock(), 'moon_rock': moon_rock(True), 'moon_rock_small': moon_rock(False),
            'glow_caps': glow_caps()}


def props() -> dict[str, Canvas]:
    return {**props_station(), **props_lumen()}


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (62, 58, 80, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/space-props.png'))
    print('sheet', out.size)
