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
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
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


def station_view(X: int, Y: int) -> str:
    """What Halcyon's lounge windows look out on, at a point of the station's own
    coordinates (so the three windows show one view, not three planets): black space
    and stars, the planet's limb below with its thin blue air, seas, land and clouds lit
    from the upper left, and the station's own solar wing reaching out to the east."""
    PX, PY, PR = 150, 236, 196
    d = math.hypot(X - PX, Y - PY)
    if 250 <= X <= 318 and abs(Y - (14 + (X - 250) * 0.28)) < 1.2:
        return '#C8CED8'  # the wing's truss
    if 256 <= X <= 316:
        top = 16 + (X - 250) * 0.28
        if top + 2 < Y < top + 16 and (X - 256) % 15 < 13:
            u, v = (X - 256) % 15, int(Y - top)
            c = '#2A4480' if (u // 3 + v // 3) % 2 else '#1E2E5A'
            if v == 3 or u == 0:
                c = '#5A7AC0'  # the blanket's lit edge
            return c
    if d < PR:
        nx, ny = (X - PX) / PR, (Y - PY) / PR
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        light = -0.55 * nx - 0.55 * ny + 0.6 * nz
        sx, sy = nx / (0.5 + 0.5 * nz) * 70, ny / (0.5 + 0.5 * nz) * 70
        land = smooth_noise(sx + 90, sy + 90, 18, 395) > 0.56
        cloud = smooth_noise(sx * 0.9 + sy * 0.5, sy * 1.8, 8, 396) > 0.64
        if cloud:
            return '#F4F6FA' if light > 0.25 else '#9AA6C0'
        if land:
            return '#7A9A4A' if light > 0.25 else '#4E6A36'
        return '#3E6AA8' if light > 0.25 else '#2A4A80'
    if d < PR + 2:
        return '#9AD2FF' if d < PR + 1 else '#3A5A9A'  # its air
    return VOID[0] if noise2(X, Y, 341) > 0.02 else '#FFFFFF'


def viewport(x0: int = 0, y0: int = 0, w: int = 96) -> Canvas:
    """A floor-to-ceiling window in the pressure hull, `w` x 70, standing at (x0, y0) in
    the station: a thick frame with ribs between triple panes, each pane showing its own
    part of one view (station_view), a faint reflection streak on the glass, the sill's
    lit edge and the frame's shadow."""
    h = 70
    cv = Canvas(w, h, pad=PAD)
    for (x, y) in rect_set(4, 4, w - 8, h - 12):
        cv.set(x, y, station_view(x0 + x, y0 + y))
    for (x, y) in rect_set(4, 4, w - 8, h - 12):  # a reflection streak across the glass
        if abs((x - 4) - (y - 4) * 0.8 - w * 0.25) < 1.5 and (x + y) % 2:
            r, g, b, a = cv.get(x, y)
            cv.set(x, y, (min(255, r + 40), min(255, g + 44), min(255, b + 50), a))
    for rx in range(4, w - 4, 30):  # the ribs between the panes
        for y in range(4, h - 8):
            cv.set(rx, y, HULL[4]); cv.set(rx + 1, y, HULL[3]); cv.set(rx + 2, y, HULL[1])
    for x in range(0, w):
        for y in range(0, 4):
            cv.set(x, y, HULL[4] if y == 0 else HULL[3])
        for y in range(h - 8, h):
            cv.set(x, y, HULL[5] if y == h - 8 else HULL[2] if y < h - 4 else HULL[1])
    for y in range(0, h):  # the frame's sides
        for x in (0, 1, 2, 3):
            cv.set(x, y, HULL[4] if x == 0 else HULL[3])
        for x in (w - 4, w - 3, w - 2, w - 1):
            cv.set(x, y, HULL[2] if x < w - 1 else HULL[1])
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


def dream_pool(seed: int = 0) -> Canvas:
    """A still pool in the greenhouse where the companion can rest, 48 x 26: fed with
    water melted from the crater's ice, held in a kerb of pale cast regolith blocks lit
    on their upper left, the water clear and green-blue over a pale floor, deeper in the
    middle, the grow lamps above reflected as warm glints, a fringe of moss at the rim.
    (No stars: it is indoors, under a roof; fault 38.)"""
    w, h = 48, 26
    cv = Canvas(w, h, pad=PAD)
    WATER = ['#0E3A44', '#16606A', '#2A8C8E', '#62BCB4', '#B8E8DC']

    def rim_r(a):
        return 1 + 0.07 * math.sin(3 * a + seed) + 0.04 * math.sin(5 * a + seed * 2)
    kerb = {(x, y) for (x, y) in oval(24, 13, 22, 11)
            if math.hypot((x - 24) / 22, (y - 13) / 11) <= rim_r(math.atan2(y - 13, x - 24))}
    inner = {(x, y) for (x, y) in kerb
             if math.hypot((x - 24) / 18, (y - 13.5) / 7.5) <= rim_r(math.atan2(y - 13, x - 24))}
    for (x, y) in kerb - inner:  # the kerb: blocks, each lit on its upper left
        a = math.atan2(y - 13, x - 24)
        blk = int((a + math.pi) * 3.2)
        c = REGOLITH[5] if y < 13 and x < 30 else REGOLITH[4] if y < 15 else REGOLITH[3]
        if blk % 2 and c != REGOLITH[5]:
            c = REGOLITH[3] if c == REGOLITH[4] else REGOLITH[2]
        cv.set(x, y, c)
    for (x, y) in inner:
        d = math.hypot((x - 24) / 18, (y - 13.5) / 7.5)
        c = WATER[1] if d < 0.45 else WATER[2] if d < 0.78 else WATER[3]
        if (x, y - 1) not in inner or (x, y - 2) not in inner:
            c = WATER[0]  # the kerb's shadow on the water
        cv.set(x, y, c)
    for (gx, gy) in ((17, 12), (27, 14), (33, 11)):  # the grow lamps, reflected
        if (gx, gy) in inner:
            cv.hline(gx, gy, 3, '#FFE8B0'); cv.set(gx + 1, gy + 1, WATER[4])
    for (x, y) in kerb - inner:  # moss at the rim where it stays damp
        if y > 15 and noise2(x, y, 343 + seed) > 0.6:
            cv.set(x, y, GLOW[1] if (x + y) % 2 else GLOW[2])
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
    """A hammock in the greenhouse, 68 x 40, slung between two light alloy stands (each a
    post on a splayed foot, a hook at the top): soft woven cloth in nap violet sagging in
    the low gravity, a folded blanket and a small pillow in it."""
    w, h = 68, 40
    cv = Canvas(w, h, pad=PAD)
    for (cx, top) in ((5, 4), (62, 6)):  # the stands
        for y in range(top, h - 3):
            cv.set(cx, y, WHITE[4]); cv.set(cx + 1, y, WHITE[2])
        for d in range(1, 5):  # the splayed foot
            cv.set(cx - d, h - 3 + d // 3, WHITE[3]); cv.set(cx + 1 + d, h - 3 + d // 3, WHITE[1])
        cv.set(cx, top - 1, WHITE[5]); cv.set(cx + 1, top - 1, WHITE[3])  # the cap
        cv.set(cx + (2 if cx < 30 else -1), top + 3, '#22222C')  # the hook
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
    for (ax, ay, bx, by) in ((7, 10, 10, 15), (61, 12, 57, 15)):  # the ropes from the hooks
        for t in range(6):
            cv.set(int(ax + (bx - ax) * t / 5), int(ay + (by - ay) * t / 5), REGOLITH[1])
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


def old_lander() -> Canvas:
    """An old lander left long ago, 40 x 36: a squat octagonal body wrapped in gold foil
    (lit facets upper left, creased, a dark facet lower right), a dish on top, four
    splayed legs on round feet, and dust drifted over one foot."""
    w, h = 40, 36
    cv = Canvas(w, h, pad=PAD)
    FOIL = ['#5A3A10', '#8A5E1A', '#C2902E', '#E8BE52', '#FFE28A']
    for (x0, y0, x1, y1, fx) in ((8, 20, 2, 32, -1), (32, 20, 38, 32, 1), (14, 22, 11, 34, -1), (26, 22, 29, 34, 1)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):  # a leg
            x, y = x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n
            cv.set(x, y, HULL[3] if fx < 0 else HULL[2]); cv.set(x + 1, y, HULL[1])
        for (x, y) in oval(x1, y1, 3, 1.4):
            cv.set(x, y, HULL[4] if x < x1 else HULL[2])  # its foot
    body = {(x, y) for y in range(8, 24) for x in range(7, 33) if abs(x - 20) + abs(y - 16) * 0.8 < 16}
    for (x, y) in body:
        face = (x - 7) // 6
        c = FOIL[4] if face == 0 else FOIL[3] if face == 1 else FOIL[2] if face < 3 else FOIL[1]
        if y < 11:
            c = FOIL[4] if x < 22 else FOIL[3]
        if (x * 7 + y * 3) % 11 == 0:
            c = FOIL[min(4, FOIL.index(c) + 1)] if x < 20 else FOIL[max(0, FOIL.index(c) - 1)]  # creases in the foil
        if (x - 7) % 6 == 0:
            c = FOIL[0]  # the seam between facets
        cv.set(x, y, c)
    for (x, y) in body:
        if (x, y + 1) not in body:
            cv.set(x, y, FOIL[0])
    cv.vline(20, 2, 7, HULL[2])
    for (x, y) in oval(20, 3, 6, 2.4):  # the dish
        cv.set(x, y, HULL[5] if x < 19 else HULL[3] if y < 4 else HULL[2])
    cv.set(20, 3, HULL[1])
    for (x, y) in oval(29, 34, 7, 2):  # dust over a foot
        if y >= 33:
            cv.set(x, y, REGOLITH[4] if x < 29 else REGOLITH[3])
    return cv


def aquarium_column() -> Canvas:
    """A round water column in the atrium, 26 x 50: in low gravity the station keeps its
    fish in a standing cylinder of water, lit cyan from the base, weeds swaying, two
    little fish, bubbles, and hull rings at top and foot."""
    w, h = 26, 50
    cv = Canvas(w, h, pad=PAD)
    WATER = ['#0E3A4A', '#16586A', '#1F7A8A', '#3EA6B0', '#8ADCDC']
    for y in range(6, h - 6):
        for x in range(3, w - 3):
            k = (x - 3) / (w - 6)
            c = WATER[3] if k < 0.2 else WATER[2] if k < 0.65 else WATER[1]
            if y > h - 14 and (x + y) % 2:
                c = WATER[3]  # the light from below
            cv.set(x, y, c)
        cv.set(5, y, WATER[4] if y % 7 else WATER[3])  # the glass catching the light
    for (bx, top) in ((8, 26), (16, 20), (12, 30)):  # weeds
        for y in range(top, h - 6):
            cv.set(bx + (1 if (y // 3) % 2 else 0), y, '#447A50' if y % 4 else '#62995E')
    for (fx, fy, col) in ((10, 16, '#E8803A'), (16, 32, '#F2D27A')):  # fish
        cv.hline(fx, fy, 3, col); cv.set(fx - 1, fy, col); cv.set(fx + 3, fy - 1, col); cv.set(fx + 3, fy + 1, col)
        cv.set(fx, fy, '#1E1917')
    for (x, y) in ((14, 10), (15, 13), (13, 17), (18, 24)):
        cv.set(x, y, WATER[4])
    for (y0, y1) in ((2, 6), (h - 6, h - 1)):  # hull rings
        for y in range(y0, y1):
            for x in range(1, w - 1):
                cv.set(x, y, HULL[5] if y == y0 else HULL[3] if x < w // 2 else HULL[2])
        cv.hline(1, y1 - 1, w - 2, HULL[1])
    cv.hline(3, h - 6, w - 6, CYAN[3])
    return cv


def cargo_crates() -> Canvas:
    """Supply crates strapped down in the atrium, 34 x 26: white hull boxes with orange
    stencils and webbing straps, the smaller one stacked on top."""
    w, h = 34, 26
    cv = Canvas(w, h, pad=PAD)
    for (x0, y0, bw, bh) in ((2, 10, 20, 14), (20, 14, 12, 10), (6, 2, 12, 9)):
        for y in range(y0, y0 + bh):
            for x in range(x0, x0 + bw):
                c = HULL[5] if y < y0 + 2 else HULL[4] if x < x0 + bw - 3 else HULL[3]
                cv.set(x, y, c)
        cv.hline(x0, y0 + bh - 1, bw, HULL[2])
        cv.hline(x0 + 2, y0 + bh // 2, max(2, bw - 6), '#E8803A')  # a stencil stripe
        cv.vline(x0 + bw // 2, y0, bh, '#3E5A6A')  # a strap
    return cv


def floor_cushions() -> Canvas:
    """A heap of floor cushions and a folded blanket in the sleep bay, 34 x 18."""
    w, h = 34, 18
    cv = Canvas(w, h, pad=PAD)
    for (cx, cy, rx, ry, col) in ((10, 11, 8, 5, NAP), (22, 12, 9, 5, GOLD), (16, 6, 7, 4, NAP)):
        for (x, y) in oval(cx, cy, rx, ry):
            k = (x - cx) / rx + (y - cy) / ry
            cv.set(x, y, col[3] if k < -0.4 else col[2] if k < 0.6 else col[1])
        cv.set(cx, cy, col[1])  # a button
    for x in range(20, 32):  # the blanket's folded edge
        cv.set(x, h - 3, '#C8D2E6'); cv.set(x, h - 2, '#8E9AB8')
    return cv


# Lumen made livable (M1; Matt, 19 Oct: "think about the logic of the moon and space and
# what is required for anything living to be there"; art-faults.md rule 10). There is no
# air, so nothing grows or rests on the open regolith: plants and people live in
# pressurised, shielded rooms (drawn into the ground in zones), with water mined as ice
# from a crater in permanent shadow, power from solar arrays, heat dumped by radiators,
# and suits for anyone who goes outside. The light is hard sunlight from the upper left
# with no air to soften it: lit faces bright, shadows nearly black.
WHITE = ['#3A3C4A', '#6A7084', '#A2A8BA', '#CDD2DE', '#EEF1F6', '#FFFFFF']  # painted panels in vacuum
CELL = ['#141C38', '#1E2E5A', '#2A4480', '#5A7AC0', '#B8D0F4']  # solar cells
ORANGE = ['#5A2A10', '#9A4A18', '#D8742A', '#F2A458']


def _box(cv: Canvas, x0: int, y0: int, w: int, d: int, h: int, ramp, top=None):
    """A box in the three-quarter view: its top (`d` deep) lit, its front face (`h` tall)
    in the mid tone darkening toward the foot, its right edge in shade."""
    top = top or ramp
    for y in range(y0, y0 + d):
        for x in range(x0, x0 + w):
            cv.set(x, y, top[4] if y == y0 else top[3] if x < x0 + w - 2 else top[2])
    for y in range(y0 + d, y0 + d + h):
        for x in range(x0, x0 + w):
            k = (y - y0 - d) / max(1, h)
            c = ramp[3] if k < 0.15 else ramp[2] if k < 0.8 else ramp[1]
            if x >= x0 + w - 2:
                c = ramp[1]
            cv.set(x, y, c)


def shuttle() -> Canvas:
    """The crew shuttle on Lumen's pad, 80 x 78, in the three-quarter view: a white cabin
    shaped like a cut cone with two warm-lit windows and a hatch at its foot, standing on
    a descent stage with orange-striped panels, thruster quads at the corners and a dark
    engine bell beneath, on four splayed legs with round footpads; a ladder runs from the
    hatch down the stage. It reads as a lander, not a saucer (art-faults.md, fault 37)."""
    w, h = 80, 78
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for (x0, y0, x1, y1, lit) in ((22, 52, 10, 66, 1), (58, 52, 70, 66, 0)):  # the back legs, behind
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            x, y = x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n
            cv.set(x, y, WHITE[2] if lit else WHITE[1]); cv.set(x + 1, y, WHITE[1])
        for (x, y) in oval(x1, y1 + 1, 4, 1.6):
            cv.set(x, y, WHITE[3] if x < x1 else WHITE[1])
    for (x, y) in oval(cx, 66, 9, 4):  # the engine bell under the stage, sooted
        cv.set(x, y, '#22222C' if y > 65 else '#3A3A48')
    for (x, y) in oval(cx, 67, 5, 2):
        cv.set(x, y, '#121218')
    # the descent stage: an eight-sided deck seen from above and in front
    stage_top = {(x, y) for y in range(40, 50) for x in range(12, 68) if abs(x - cx) + (49 - y) * 1.4 < 30}
    for (x, y) in stage_top:
        k = (x - 12) / 56
        cv.set(x, y, WHITE[4] if k < 0.45 else WHITE[3] if k < 0.8 else WHITE[2])
    for y in range(50, 62):  # its front faces: a lit left facet, the front, a shaded right facet
        for x in range(14, 66):
            if abs(x - cx) > 26 - (y - 50) // 4:
                continue
            c = WHITE[3] if x < cx - 14 else WHITE[2] if x < cx + 14 else WHITE[1]
            if x in (cx - 14, cx + 14):
                c = WHITE[0]  # the seams between facets
            if y in (53, 54):
                c = ORANGE[2] if x < cx + 14 else ORANGE[1]  # the stage's stripe
            if y == 61:
                c = WHITE[0]
            cv.set(x, y, c)
    for (qx, qy) in ((14, 46), (62, 46)):  # thruster quads at the corners, nozzles out
        _box(cv, qx, qy, 6, 2, 4, WHITE)
        cv.set(qx - 1, qy + 4, '#22222C'); cv.set(qx + 6, qy + 4, '#22222C')
    for (x0, y0, x1, y1, lit) in ((18, 58, 4, 74, 1), (62, 58, 76, 74, 0)):  # the front legs
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            x, y = x0 + (x1 - x0) * t // n, y0 + (y1 - y0) * t // n
            cv.set(x, y, WHITE[4] if lit else WHITE[2]); cv.set(x + 1, y, WHITE[1])
            if t == n // 2:  # the strut's knee joint
                cv.set(x, y - 1, WHITE[5] if lit else WHITE[3])
        for (x, y) in oval(x1, y1 + 1, 5, 2):
            cv.set(x, y, WHITE[4] if x < x1 else WHITE[2] if y <= y1 + 1 else WHITE[1])
    # the cabin: a cut cone of white panels, lit on the left, in courses
    for y in range(8, 42):
        t = (y - 8) / 34
        hw = 11 + t * 9
        for x in range(int(cx - hw), int(cx + hw) + 1):
            k = (x - (cx - hw)) / (2 * hw)
            c = WHITE[5] if k < 0.2 else WHITE[4] if k < 0.5 else WHITE[3] if k < 0.78 else WHITE[2]
            if (y - 8) % 7 == 6:
                c = WHITE[2] if k < 0.78 else WHITE[1]  # the panel courses
            if y >= 39:
                c = '#2A2A36' if k < 0.85 else '#1C1C26'  # the dark heat-shield ring at its base
            cv.set(x, y, c)
    for y in range(4, 8):  # the docking collar on top
        for x in range(cx - 7, cx + 8):
            cv.set(x, y, WHITE[4] if y == 4 else WHITE[2] if x < cx + 4 else WHITE[1])
    for (wx, wy) in ((cx - 8, 18), (cx + 3, 18)):  # two windows, lit from within
        for (x, y) in oval(wx + 2, wy + 2, 2.6, 2.6):
            cv.set(x, y, '#FFDC92' if (x - wx) + (y - wy) < 4 else '#F2A048')
        cv.set(wx + 1, wy + 1, '#FFF4D6')
    for y in range(28, 39):  # the hatch at the cabin's foot, framed, its handle
        for x in range(cx - 4, cx + 5):
            c = WHITE[3] if x < cx + 2 else WHITE[2]
            if x in (cx - 4, cx + 4) or y == 28:
                c = WHITE[1]
            cv.set(x, y, c)
    cv.set(cx + 2, 33, ORANGE[3])
    for y in range(42, 62, 3):  # the ladder down the stage's front
        cv.hline(cx - 3, y, 7, WHITE[1])
    cv.vline(cx - 4, 42, 20, WHITE[2]); cv.vline(cx + 4, 42, 20, WHITE[1])
    cv.hline(cx - 9, 30, 4, NAP[3]); cv.hline(cx + 6, 30, 4, NAP[2])  # the line's violet band
    for (x, y) in oval(cx + 16, 14, 4, 2):  # the antenna dish on its arm
        cv.set(x, y, WHITE[4] if x < cx + 16 else WHITE[2])
    cv.hline(cx + 11, 16, 5, WHITE[1])
    return cv


def solar_array(width: int = 64, seed: int = 0) -> Canvas:
    """A solar array on its mast, `width` x 44: a wing of cells tilted up toward the
    sun in the upper left, its cells dark blue in a lit silver frame with one long glint,
    on a mast with a sun tracker and a foot plate, its cable running off along the dust."""
    w, h = width, 44
    cv = Canvas(w, h, pad=PAD)
    mx = w // 2
    for y in range(18, h - 3):  # the mast and its tracker joint
        cv.set(mx, y, WHITE[3]); cv.set(mx + 1, y, WHITE[1])
    _box(cv, mx - 3, 16, 7, 2, 3, WHITE)
    for x in range(mx - 5, mx + 7):  # the foot plate, dust over its edge
        cv.set(x, h - 3, WHITE[3] if x < mx + 3 else WHITE[2]); cv.set(x, h - 2, WHITE[1])
    for x in range(mx + 7, w - 1):  # the cable away along the dust
        cv.set(x, h - 2 + (x // 9) % 2, '#22222C')
    panel = set()
    for y in range(2, 20):
        t = (y - 2) / 17
        xa, xb = int(2 + t * 4), int(w - 6 + t * 3)  # tilted: the top edge set back
        for x in range(xa, xb):
            panel.add((x, y))
    for (x, y) in panel:
        u, v = x // 6, (y - 2) // 4
        c = CELL[2] if noise2(u, v, 380 + seed) > 0.3 else CELL[1]
        if (x % 6 == 0) or ((y - 2) % 4 == 0):
            c = CELL[0]  # the gaps between cells
        if abs((x - 2) - (y - 2) * 3 - w * 0.3) < 2:
            c = CELL[4] if (x + y) % 2 else CELL[3]  # the sun's glint across the cells
        cv.set(x, y, c)
    for (x, y) in panel:  # the frame: lit along the top and left, shaded on the right and below
        if (x, y - 1) not in panel or (x - 1, y) not in panel:
            cv.set(x, y, WHITE[4])
        elif (x, y + 1) not in panel or (x + 1, y) not in panel:
            cv.set(x, y, WHITE[1])
    for x in range(4, w - 3):  # the panel's thin edge seen below it, in shade
        if (x, 19) in panel:
            cv.set(x, 20, WHITE[0])
    return cv


def radiator() -> Canvas:
    """A heat radiator, 34 x 40: white fins standing on edge to throw the base's heat
    into space, a coolant manifold along their foot, lit on their left faces."""
    w, h = 34, 40
    cv = Canvas(w, h, pad=PAD)
    for k in range(5):
        x0 = 3 + k * 6
        top = 4 + (k % 2) * 2
        for y in range(top, h - 8):
            cv.set(x0, y, WHITE[5] if y == top else WHITE[4])
            cv.set(x0 + 1, y, WHITE[3]); cv.set(x0 + 2, y, WHITE[3] if y < h - 14 else WHITE[2])
            cv.set(x0 + 3, y, WHITE[1])
            if (y - top) % 6 == 5:
                cv.set(x0 + 1, y, WHITE[2])  # the coolant channels in the fin
    _box(cv, 1, h - 9, w - 3, 2, 5, WHITE)
    for x in range(3, w - 4, 6):
        cv.set(x, h - 6, ORANGE[2])  # valves
    return cv


def ice_rig() -> Canvas:
    """The ice rig at the dark crater's rim, 72 x 52: a tracked excavator in white and
    orange with its arm reaching down into the shadow, its bucket heaped with icy
    regolith, a hopper on its back. It is driven from inside the hub (nobody walks the
    surface): a whip antenna with a red beacon and a camera head over the arm."""
    w, h = 72, 52
    cv = Canvas(w, h, pad=PAD)
    for y in range(36, 46):  # the tracks: treads in a dark band, the wheels showing
        for x in range(4, 44):
            c = '#2A2A36' if (x // 3) % 2 else '#3E3E4C'
            if y in (36, 45):
                c = '#1C1C26'
            cv.set(x, y, c)
    for wx in (8, 18, 28, 38):
        for (x, y) in oval(wx, 41, 3, 3):
            cv.set(x, y, WHITE[2] if (x - wx) + (y - 41) < 0 else WHITE[1])
    _box(cv, 6, 20, 34, 6, 10, WHITE)  # the body
    for x in range(6, 40):
        cv.set(x, 30, ORANGE[2] if x < 37 else ORANGE[1])
    _box(cv, 10, 10, 16, 4, 6, WHITE, top=[WHITE[0], WHITE[1], '#8A93A8', '#AEB6CA', '#D6DCE8'])  # the hopper
    for x in range(11, 25):  # ice in the hopper, glinting
        cv.set(x, 11, '#D8ECFA' if x % 3 else '#FFFFFF'); cv.set(x, 12, '#9CB4CC')
    for (x, y) in oval(32, 18, 3, 2):  # the camera mast's lamp
        cv.set(x, y, '#FFDC92')
    cv.vline(32, 19, 2, WHITE[1])
    # the arm, from the body out and down over the rim into the crater
    for t in range(30):
        x, y = 40 + t, 22 + int(t * 0.55) + (t * t) // 90
        for d in range(3):
            cv.set(x, y + d, WHITE[4] if d == 0 else ORANGE[2] if d == 1 else ORANGE[1])
    bx, by = 68, 40
    for y in range(by - 2, by + 6):  # the bucket, heaped with icy regolith
        for x in range(bx - 6, bx + 2):
            c = WHITE[2] if x > bx - 2 else WHITE[3]
            if y < by:
                c = '#C8DCEE' if (x + y) % 2 else '#8EA4BE'
            cv.set(x, y, c)
    # nobody stands out here (review 19 Oct: nothing alive outside the pressurised base):
    # the rig is driven from the hub, so it carries a whip antenna with a beacon and a
    # camera head looking down the arm
    cv.vline(14, 0, 10, WHITE[3]); cv.set(15, 1, WHITE[1])
    cv.set(14, 0, RED[3]); cv.set(13, 0, RED[4])
    for (x, y) in rect_set(34, 16, 5, 3):
        cv.set(x, y, WHITE[4] if y == 16 else WHITE[2])
    cv.set(38, 17, '#2A4480'); cv.set(38, 18, '#5A7AC0')  # its lens, toward the bucket
    return cv


def comm_mast() -> Canvas:
    """A communications mast, 26 x 64: a lattice tower on a foot plate, a dish turned
    toward the planet in the sky, a red beacon on top."""
    w, h = 26, 64
    cv = Canvas(w, h, pad=PAD)
    for y in range(10, h - 3):
        t = (y - 10) / (h - 13)
        hw = 2 + t * 4
        xa, xb = int(13 - hw), int(13 + hw)
        cv.set(xa, y, WHITE[4]); cv.set(xb, y, WHITE[2])
        if (y - 10) % 6 < 2:  # the lattice's cross-bracing
            k = (y - 10) % 6
            for x in range(xa, xb + 1):
                if (x - xa + k) % 3 == 0:
                    cv.set(x, y, WHITE[3])
    _box(cv, 5, h - 4, 17, 1, 2, WHITE)
    for (x, y) in oval(8, 12, 7, 5):  # the dish, its bowl toward the planet
        k = (x - 8) + (y - 12)
        cv.set(x, y, WHITE[5] if k < -3 else WHITE[4] if k < 2 else WHITE[2])
    for (x, y) in oval(8, 12, 3, 2):
        cv.set(x, y, WHITE[2])
    cv.vline(13, 3, 7, WHITE[3]); cv.set(13, 2, RED[3]); cv.set(12, 2, RED[4])
    return cv


def suit_rack() -> Canvas:
    """Two pressure suits hanging by the outer hatch, 40 x 42, in the three-quarter view:
    white suits on a rack against the wall, their helmets on the shelf above with gold
    visors, life-support packs, gloves and boots; a hose coiled on a hook."""
    w, h = 40, 42
    cv = Canvas(w, h, pad=PAD)
    _box(cv, 1, 6, w - 2, 3, 2, WHITE)  # the shelf
    cv.hline(2, 4, w - 4, WHITE[2])
    for k, hx in enumerate((10, 28)):
        for (x, y) in disc(hx, 3, 3.6):  # a helmet on the shelf
            if y < 7:
                cv.set(x, y, WHITE[5] if x < hx else WHITE[3])
        for (x, y) in oval(hx - 1, 3, 2.2, 1.5):
            cv.set(x, y, GOLD[4] if x < hx - 1 else GOLD[2])
        for y in range(13, h - 2):  # the suit, hanging
            hw = 6 if y < 28 else 5
            for x in range(hx - hw, hx + hw):
                if y > 30 and abs(x - hx) < 1:
                    continue
                c = WHITE[5] if x < hx - 2 else WHITE[4] if x < hx + 2 else WHITE[2]
                if y in (20, 29):
                    c = WHITE[2]  # its joint rings
                if y == 24 and abs(x - hx) < 2:
                    c = ORANGE[2] if k == 0 else NAP[3]  # the chest panel, one colour each
                cv.set(x, y, c)
            if y in (22, 23, 24, 25):
                cv.set(hx - hw - 1, y, WHITE[3]); cv.set(hx + hw, y, WHITE[2])  # gloves
        cv.vline(hx, 9, 4, '#22222C')  # its hanger
        for x in range(hx - 5, hx + 6):  # boots at the foot
            cv.set(x, h - 2, WHITE[1])
    return cv


def water_tank() -> Canvas:
    """The melt tank, 30 x 44: a white cylinder holding the water melted from the
    crater's ice, a sight glass showing it half full, pipes in at the top and out at the
    foot, a valve wheel."""
    w, h = 30, 44
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(6, h - 3):
        for x in range(3, w - 3):
            k = (x - 3) / (w - 7)
            c = WHITE[5] if k < 0.15 else WHITE[4] if k < 0.5 else WHITE[3] if k < 0.8 else WHITE[2]
            if (y - 6) % 9 == 8:
                c = WHITE[2] if k < 0.8 else WHITE[1]  # its hoops
            cv.set(x, y, c)
    for (x, y) in oval(cx, 6, w / 2 - 3, 3):  # the lid
        cv.set(x, y, WHITE[5] if x < cx else WHITE[4])
    for y in range(14, h - 8):  # the sight glass, half full
        cv.set(cx + 5, y, '#2A4480' if y > 24 else '#C8D8EE')
        cv.set(cx + 6, y, '#1E2E5A' if y > 24 else '#9AB0CC')
    for x in range(cx - 2, cx + 3):  # the pipe in at the top
        cv.set(x, 2, WHITE[3]); cv.set(x, 3, WHITE[2])
    cv.vline(cx - 2, 2, 4, WHITE[4])
    for (x, y) in disc(8, h - 7, 2.4):  # the valve wheel
        cv.set(x, y, RED[3] if x < 8 else RED[2])
    cv.set(8, h - 7, '#22222C')
    return cv


def grow_lamp() -> Canvas:
    """A grow lamp on its stand over a bed, 30 x 40: a slim pole and arm, a long lamp
    head glowing warm white (the light the plants live by, in place of a sky)."""
    w, h = 30, 40
    cv = Canvas(w, h, pad=PAD)
    cv.vline(4, 8, h - 10, WHITE[3]); cv.vline(5, 8, h - 10, WHITE[1])
    _box(cv, 1, h - 3, 8, 1, 1, WHITE)
    cv.hline(4, 7, 8, WHITE[3])
    for y in range(5, 10):  # the lamp head
        for x in range(10, w - 2):
            c = WHITE[4] if y == 5 else WHITE[2]
            if y >= 8:
                c = '#FFF4D6' if (x % 4) else '#FFDC92'  # its lit underside
            cv.set(x, y, c)
    return cv


def moon_rock(big: bool = True, seed: int = 0) -> Canvas:
    """A boulder thrown out by an old impact, 30 x 20 (or 18 x 12): angular, broken
    faces (a sunlit top plane, a mid front, a near-black flank, airless contrast), small
    pits, and dust banked at its foot."""
    import style
    w, h = (30, 20) if big else (18, 12)
    cv = Canvas(w, h, pad=PAD)
    pts = set()
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            a = math.atan2((y - h / 2) / (h / 2), (x - w / 2) / (w / 2))
            r = 0.92 + 0.12 * math.sin(3 * a + seed) + 0.06 * math.sin(5 * a + seed * 2)
            r = max(0.6, min(1.0, r))  # broken, flat-sided faces
            if math.hypot((x - w / 2) / (w / 2 - 1), (y - h / 2 - 1) / (h / 2 - 1)) <= r:
                pts.add((x, y))
    style.facet_stone(cv, pts, [REGOLITH[0], REGOLITH[1], REGOLITH[3], REGOLITH[4], REGOLITH[5]], seed=seed + w,
                      outline=None)
    for i in range(3):  # pits
        px, py = 3 + int(noise2(i, seed, 381) * (w - 6)), 3 + int(noise2(i, seed, 382) * (h - 6))
        if (px, py) in pts and (px + 1, py) in pts:
            cv.set(px, py, REGOLITH[2]); cv.set(px + 1, py, REGOLITH[4])
    for x in range(2, w - 2):  # dust banked at its foot
        if (x, h - 2) in pts:
            cv.set(x, h - 1, REGOLITH[3] if x < w // 2 else REGOLITH[2])
    return cv


# Lumen's pressurised volumes, roofed (Claude A's review, 19 Oct 14:20: "a pressurised
# habitat needs a roof (regolith-covered), airlocks and closed tubes"; "glaze the whole
# dome"). The companion walks inside them and is drawn behind them, its outline showing
# through (the Ghost), the way it walks behind a roof.
TUBE_W, TUBE_L = 28, 66
DOME = (120, 140, 118, 64, 74)  # the dome sprite's base centre, radii and height
REG = ['#2A2838', '#3E3A50', '#585270', '#77708E', '#9C96B2', '#C8C2DA']  # regolith (materials)


def _bags(cv: Canvas, x: int, y: int, lit: float, seed: int = 0):
    """One pixel of a berm of regolith bags laid in courses: each bag a soft pillow 10 x 5,
    its ends rounded into the gaps, a highlight along the middle of its top where it
    bulges, its lower half in shade; the courses wander a little so they never line up
    like brick. `lit` (-1..1) shades the berm as a form under the upper-left sun."""
    row = y // 5
    off = (row % 2) * 5 + int(noise2(row, 0, 407 + seed) * 3)
    u, v = (x + off) % 10, y % 5
    t = noise2((x + off) // 10, row, 401 + seed)
    base = 3 + (1 if t > 0.7 else -1 if t < 0.15 else 0) + round(lit)
    base = max(1, min(4, base))
    c = REG[base]
    end = u in (0, 9)
    if (end and v in (0, 4)) or (u == 0 and v in (1, 3)):
        c = REG[max(0, base - 2)]  # the gap between two bags, where their rounded ends meet
    elif v == 4:
        c = REG[max(0, base - 2)] if not end else REG[max(0, base - 1)]  # the shadow under the bag
    elif v == 0 and 2 <= u <= 7:
        c = REG[min(5, base + 1)]  # the bulge of its top catching the light
    elif v == 3 or end:
        c = REG[max(1, base - 1)]
    cv.set(x, y, c)


def pressure_tube(length: int = TUBE_L, dock: bool = False) -> Canvas:
    """A closed pressurised tube between two modules, running north-south, 28 x `length`:
    a white hull seen from above, rounded (lit on the left, falling into shade on the
    right), stiffened by ring frames every few paces, a strip of small lit ports along
    its crown, and saddles on short feet where it rests on the dust."""
    w, h = TUBE_W, length
    cv = Canvas(w, h, pad=PAD)
    for y in range(0, h):
        for x in range(3, w - 3):
            k = (x - 3) / (w - 7)
            c = WHITE[5] if k < 0.18 else WHITE[4] if k < 0.45 else WHITE[3] if k < 0.75 else WHITE[2]
            if k > 0.92:
                c = WHITE[1]
            ring = y % 12
            if ring == 0:
                c = WHITE[1] if k > 0.45 else WHITE[2]  # a ring frame
            elif ring == 1:
                c = WHITE[5] if k < 0.75 else WHITE[3]  # its lit edge
            if x == 9 and ring in (5, 6):
                c = '#FFDC92' if ring == 5 else '#F2A048'  # a small lit port on the crown
            cv.set(x, y, c)
    if dock:  # the docking collar at its north end, clamped to the shuttle's hatch
        for y in range(0, 6):
            for x in range(1, w - 1):
                k = (x - 1) / (w - 3)
                c = WHITE[5] if k < 0.2 else WHITE[4] if k < 0.6 else WHITE[2] if k < 0.9 else WHITE[1]
                if y in (2, 5):
                    c = WHITE[1] if k > 0.5 else WHITE[2]
                if y == 3 and x % 5 == 0:
                    c = '#E8C04A'  # the clamps
                cv.set(x, y, c)
    for y in range(6, h, 24):  # saddles on their feet, at the sides
        for (sx, d) in ((1, -1), (w - 3, 1)):
            for k in range(3):
                cv.set(sx + (k if d < 0 else -k + 1), y + 4, WHITE[2] if d < 0 else WHITE[1])
            cv.set(sx, y + 5, WHITE[1]); cv.set(sx + (0 if d < 0 else 1), y + 6, REG[1])
    return cv


def hab_hub() -> Canvas:
    """The hub, 148 x 122: a vaulted habitat buried under a berm of regolith bags (a
    metre or two of moon dust stops the radiation and the micrometeorites), seen from
    above: the roof as smooth dust heaped over the vault and lit from the upper left,
    breaking at a clear edge over the front wall of bags laid in courses in its shade
    (review 19 Oct: no brick all over, no diagonal seam, no face); a flat service hatch
    and a vent mast on the roof; at the front, a white entrance porch with its hatch open
    into the warm-lit lock and a lamp over it, where the tube to the greenhouse leaves.
    No door to the surface: nobody goes out."""
    w, h = 148, 122
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2
    berm = set()
    for x in range(0, w):
        d = abs(x - cx) / (w / 2)
        top = int(8 + 30 * d ** 2.4 + (smooth_noise(x, 0, 9, 402) - 0.5) * 4)
        for y in range(top, h - 2 - int(10 * d ** 3)):  # its toe rounding off at the ends
            berm.add((x, y))
    def crest(x):  # where the roof's slope breaks over into the bagged front wall
        return int(70 - abs(x - cx) / (w / 2) * 10 + (smooth_noise(x, 1, 11, 405) - 0.5) * 3)
    for (x, y) in berm:
        k = (x - cx) / (w / 2)
        if y < crest(x):  # the roof: moon dust heaped over the vault, smooth, lit from the upper left
            n = smooth_noise(x, y, 8, 403)
            lit = 1.0 - (k + 1) * 0.35 + (n - 0.5) * 0.8
            base = max(2, min(5, 3 + round(lit)))
            c = REG[base] if (x + y) % 2 or n > 0.45 else REG[max(2, base - 1)]
            if noise2(x, y, 406) > 0.97:
                c = REG[5]  # a bright grain
            cv.set(x, y, c)
        else:  # the front wall: regolith bags in courses, in the shade of the roof's edge
            _bags(cv, x, y, -0.7 - max(0, k) * 0.4, seed=1)
    for (x, y) in berm:  # the break between roof and wall: a lit lip, the shadow under it
        cy = crest(x)
        if y == cy - 1:
            cv.set(x, y, REG[5] if x < cx + 30 else REG[4])
        elif y in (cy, cy + 1):
            cv.set(x, y, REG[0] if y == cy else REG[1])
    for (x, y) in berm:  # its edge against the dust beyond, its toe in shadow
        if (x, y - 1) not in berm:
            cv.set(x, y, REG[5] if x < cx + 30 else REG[4])
        elif (x, y + 1) not in berm:
            cv.set(x, y, REG[0])
    for (x, y) in rect_set(36, 24, 12, 6):  # one flat service hatch on the roof, white, its rim lit
        cv.set(x, y, WHITE[4] if y == 24 or x == 36 else WHITE[2] if x < 47 else WHITE[1])
    cv.hline(37, 30, 11, REG[1])  # its shadow on the dust
    cv.vline(122, 8, 30, WHITE[3]); cv.vline(123, 8, 30, WHITE[1])  # the vent mast
    cv.set(122, 7, RED[3]); cv.set(123, 7, RED[2])
    cv.hline(124, 38, 3, REG[1])
    # the entrance porch at the front: a white box with its hatch open into the lit lock
    px0, pw, ptop, pfoot = 60, 28, 76, h - 1
    for y in range(ptop, ptop + 8):  # its roof
        for x in range(px0, px0 + pw):
            cv.set(x, y, WHITE[5] if y == ptop else WHITE[4] if x < px0 + pw - 3 else WHITE[2])
    for y in range(ptop + 8, pfoot):  # its front face
        for x in range(px0, px0 + pw):
            c = WHITE[3] if x < px0 + pw - 3 else WHITE[1]
            if y > pfoot - 4:
                c = '#E8C04A' if ((x + y) // 3) % 2 else '#2A2630'  # hazard stripes on the sill
            cv.set(x, y, c)
    for y in range(ptop + 12, pfoot - 3):  # the open hatch: the lock beyond, lit warm
        for x in range(px0 + 5, px0 + pw - 5):
            c = '#F2C890' if y < ptop + 18 else '#C89060' if (x + y) % 5 else '#B07A50'
            if x in (px0 + 5, px0 + pw - 6):
                c = WHITE[1]
            cv.set(x, y, c)
    for (x, y) in oval(px0 + pw / 2, ptop + 11, 9, 2.4):  # the hatch's rounded head
        if y <= ptop + 11 and (x, y) not in ():
            cv.set(x, y, WHITE[2])
    for x in range(px0 + 10, px0 + 18):  # the lamp over it
        cv.set(x, ptop + 9, '#FFE8B0')
    return cv


def airlock_module() -> Canvas:
    """The airlock between the corridor tube and the greenhouse, 46 x 58: a white
    module with its roof lit, two hatches in a line (the outer at its north end hidden
    behind it, the inner opening south into the dome), hazard stripes on its sill, a
    status light that is green (both doors may open: the dome is at pressure)."""
    w, h = 46, 58
    cv = Canvas(w, h, pad=PAD)
    for y in range(0, 30):  # its roof, ribbed
        for x in range(2, w - 2):
            k = (x - 2) / (w - 4)
            c = WHITE[5] if k < 0.2 else WHITE[4] if k < 0.7 else WHITE[2]
            if y % 9 == 0:
                c = WHITE[2] if k < 0.7 else WHITE[1]
            cv.set(x, y, c)
    for y in range(30, h - 1):  # its front face with the inner hatch
        for x in range(2, w - 2):
            c = WHITE[3] if x < w - 6 else WHITE[1]
            if y > h - 5:
                c = '#E8C04A' if ((x + y) // 3) % 2 else '#2A2630'
            cv.set(x, y, c)
    for y in range(34, h - 5):
        for x in range(12, w - 12):
            c = '#CFE8C8' if y < 40 else '#7FA878' if (x + y) % 4 else '#6E9868'  # the greenhouse's green light
            if x in (12, w - 13):
                c = WHITE[1]
            cv.set(x, y, c)
    cv.set(w - 9, 33, '#4AD07A'); cv.set(w - 8, 33, '#2A9A5A')  # the status light
    return cv


def glass_dome() -> Canvas:
    """The greenhouse dome, 240 x 208, glazed all over (the review: "glaze the whole
    dome, plants inside"): panes of tinted glass in a frame of struts, meridians and
    rings, the sun's reflection on the upper left, the glass only faintly tinted so the
    plants and the people inside show through it, on a cast sill, with a collar where
    the airlock joins it at the back. Drawn over everything inside it."""
    cx, cy, rx, ry, dh = DOME
    w, h = 2 * cx, cy + ry + 4
    cv = Canvas(w, h, pad=PAD)
    pts = {}
    for i in range(0, 721):
        th = 2 * math.pi * i / 720
        for j in range(0, 181):
            ph = (math.pi / 2) * j / 180
            X = cx + rx * math.cos(ph) * math.cos(th)
            Y = cy - ry * math.cos(ph) * math.sin(th) - dh * math.sin(ph)
            p = (int(round(X)), int(round(Y)))
            front = math.sin(th) < 0
            # where the front and back surfaces both cover a pixel, the front one is seen
            if p not in pts or (front and not pts[p][2]):
                pts[p] = (th, ph, front)
    for (x, y), (th, ph, front) in pts.items():
        if not (0 <= x < w and 0 <= y < h):
            continue
        # a frame of meridians and rings, thin (a strut is a few centimetres across), the
        # meridians stopping at the top ring so they do not crowd into the crown
        mer = ph < 1.15 and abs(th * 8 / math.pi - round(th * 8 / math.pi)) * (1 + 2.5 * ph) < 0.07
        ring = abs(ph * 8 / math.pi - round(ph * 8 / math.pi)) < 0.035 and ph > 0.05
        if mer or ring:
            lit = math.cos(th - 2.4) * math.cos(ph) + math.sin(ph) * 0.6
            c = (236, 240, 248, 255) if lit > 0.3 else (176, 184, 200, 255) if lit > -0.3 else (120, 128, 148, 255)
        else:
            # glass: a cool tint, a little stronger on the back half (seen through twice)
            a = 54 if front else 70
            c = (150, 196, 228, a)
            u = math.cos(th - 2.2) * math.cos(ph) + math.sin(ph) * 0.5
            if front and 0.55 < u < 0.95 and (x + y) % 2 == 0:
                c = (240, 248, 255, 150)  # the sun's reflection, high on the upper left
            elif front and u > 0.95:
                c = (255, 255, 255, 190)
        cv.set(x, y, c)
    # the collar where the airlock from the corridor joins the glass at the back (review
    # 19 Oct): a white frame round the opening, lit on its top and left, clamped to the sill
    ax0, ax1, ay0, ay1 = 89, 139, cy - ry - 10, cy - ry + 8
    for y in range(ay0, ay1):
        for x in range(ax0, ax1):
            edge = min(x - ax0, ax1 - 1 - x, y - ay0, ay1 - 1 - y)
            if edge < 4:
                c = (238, 240, 246, 255) if (y - ay0 < 2 or x - ax0 < 2) else (178, 182, 198, 255) if edge < 3 else (124, 128, 148, 255)
                if edge == 1 and (x + y) % 6 == 0:
                    c = (232, 192, 74, 255)  # its clamps
                cv.set(x, y, c)
    for i in range(0, 721):  # the sill: a cast ring the glass stands on, its front lit
        th = 2 * math.pi * i / 720
        for k in range(4):
            x, y = int(round(cx + (rx + 1) * math.cos(th))), int(round(cy - (ry + 1) * math.sin(th))) + k
            if math.sin(th) < 0.1 and 0 <= x < w and 0 <= y < h:
                cv.set(x, y, (232, 228, 238, 255) if k == 0 else (184, 180, 200, 255) if k < 3 else (120, 116, 140, 255))
    return cv


def props_station() -> dict[str, Canvas]:
    return {'garden_pod': garden_pod(), 'viewport': viewport(18, 8), 'viewport_b': viewport(112, 8),
            'viewport_c': viewport(206, 8), 'sleep_pod': sleep_pod(), 'airlock': airlock(),
            'console': console(), 'hydro_trough': hydro_trough(), 'galley_table': galley_table(),
            'bookshelf': bookshelf(), 'telescope': telescope(), 'lounge_bench': lounge_bench(), 'lockers': lockers(),
            'tea_dispenser': tea_dispenser(), 'aquarium_column': aquarium_column(), 'cargo_crates': cargo_crates(),
            'floor_cushions': floor_cushions()}


def props_lumen() -> dict[str, Canvas]:
    return {'shuttle': shuttle(), 'dream_pool': dream_pool(), 'dream_pool_b': dream_pool(4), 'moon_tree': moon_tree(), 'hammock': hammock(),
            'moon_rock': moon_rock(True), 'moon_rock_small': moon_rock(False), 'moon_rock_b': moon_rock(True, 3),
            'moon_rock_small_b': moon_rock(False, 5), 'glow_caps': glow_caps(), 'old_lander': old_lander(),
            'solar_array': solar_array(64, 0), 'solar_array_b': solar_array(52, 1), 'radiator': radiator(),
            'ice_rig': ice_rig(), 'comm_mast': comm_mast(), 'grow_lamp': grow_lamp(), 'pressure_tube': pressure_tube(), 'pressure_tube_dock': pressure_tube(78, dock=True), 'hab_hub': hab_hub(),
            'airlock_module': airlock_module(), 'glass_dome': glass_dome()}


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
