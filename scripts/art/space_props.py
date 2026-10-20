"""Props for Halcyon Station and the moon Lumen, the end of the line (world-atlas.md).

On the station, light comes from panels and the planet below: hull plates in cool
greys with a bright top edge, round viewports, garden pods under glass. On Lumen the
light is starlight and the plants' own glow. Run directly for a contact sheet.
"""
from __future__ import annotations

import math
import random
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import reach_detail as rd  # noqa: E402
from materials import MATERIALS, LEAF, NAP, GOLD, RED, WTR, WOOD  # noqa: E402

HULL, VOID, GLOW = (MATERIALS[k] for k in ('hull', 'void', 'glowflora'))
# Lumen's regolith, grey to brown-grey and airless (Matt, 20 Oct ~11:00: never lavender);
# the shared ramp in art/materials.json, until the house palette recolours it
LUNAR = MATERIALS['regolith']
REGOLITH = LUNAR
CYAN = MATERIALS['neon_cyan']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def garden_pod(variant: int = 0) -> Canvas:
    """A hydroponic garden pod, 64 x 56: a glass dome seen from above with plants in
    rings under it, a reflection arc on the glass, and a hull collar with status lights.
    variant 1 (review 19 Oct: not two the same) grows a dwarf citrus tree in its middle
    with oranges on it over a ring of strawberries, and its lights run amber."""
    w, h = 64, 56
    cv = Canvas(w, h, pad=PAD)
    if variant:
        return _pod_citrus(cv, w, h)
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


def _pod_citrus(cv: Canvas, w: int, h: int) -> Canvas:
    for (x, y) in oval(32, 40, 30, 12):  # the collar
        cv.set(x, y, HULL[3] if y < 40 else HULL[2])
    for (x, y) in oval(32, 28, 26, 22):  # dark soil under the dome
        if y < 44:
            cv.set(x, y, '#3A2A24' if (x + y) % 3 else '#4A362C')
    for k in range(16):  # a ring of strawberries, white flowers and red fruit
        a = 2 * math.pi * k / 16
        px, py = 32 + math.cos(a) * 20, 30 + math.sin(a) * 11
        for (x, y) in disc(px, py, 2.0):
            if y < 44:
                cv.set(x, y, LEAF[3] if (x - px) + (y - py) < 0 else LEAF[2])
        cv.set(int(px), int(py) + 1, RED[3] if k % 2 else '#F4F0E8')
    for (x, y) in disc(32, 24, 10.5):  # the dwarf citrus: a round crown, lit upper left
        k = (x - 32) + (y - 24)
        cv.set(x, y, LEAF[4] if k < -6 else LEAF[3] if k < 4 else LEAF[2])
    for (ox, oy) in ((27, 20), (36, 22), (30, 28), (38, 27), (25, 26)):
        cv.set(ox, oy, GOLD[4]); cv.set(ox + 1, oy, GOLD[3])  # oranges
    cv.vline(32, 33, 5, '#6A4A32')  # its stem
    for (x, y) in oval(32, 28, 26, 22):
        if y < 44 and math.hypot((x - 22) / 18, (y - 18) / 12) < 1 and math.hypot((x - 24) / 18, (y - 21) / 12) > 1:
            cv.set(x, y, '#E6F2FF')  # the glass's reflection arc
    for (x, y) in oval(32, 28, 26, 22):
        if y < 44 and (math.hypot((x - 32) / 25, (y - 28) / 21) > 1):
            cv.set(x, y, HULL[4])
    for k, lx in enumerate(range(12, 54, 10)):
        cv.set(lx, 46, GOLD[3] if k % 2 else GOLD[2])
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


HULL_METALS = ('#66728A', '#707684', '#5C6A86', '#78808C', '#6A6E7E')  # the station's plates (D13)


def _conduit(cv: Canvas, x: int, y0: int, h: int):
    """A pipe and a cable run down a bulkhead on brackets: the pipe brass, lit on its
    left; the cable red beside it; a bracket every eight pixels, each with its shadow."""
    brass = MATERIALS['brass']
    for y in range(y0, y0 + h):
        rd.put(cv, x, y, brass[4]); rd.put(cv, x + 1, y, brass[3]); rd.put(cv, x + 2, y, brass[1])
        rd.put(cv, x + 3, y, RED[2] if y % 6 else RED[1]); rd.put(cv, x + 4, y, rd.step(cv.get(x + 4, y), -1.5))
        if (y - y0) % 8 == 3:
            for k in range(-1, 5):
                rd.put(cv, x + k, y, HULL[4] if k < 2 else HULL[2])
            rd.put(cv, x + 4, y + 1, HULL[0])


def airlock() -> Canvas:
    """The space elevator's arrival hatch, 56 x 60: a round door 32 across in a lit rim
    (verticality.md 5: a door 32 tall for an adult of 25), warning chevrons at its sill
    and a status panel. D13: the bulkhead in riveted plates of several alloys with scuffs,
    grime and the odd rust run; the rim bolted; the door's two leaves panelled, their
    meeting seam dark, a lit edge where the light from the upper left catches them."""
    cv = Canvas(56, 60, pad=PAD)
    wall = rect_set(2, 4, 52, 54)
    rd.panels(cv, wall, HULL_METALS, seed=171, pw=17, ph=12, foot=57, stagger=False)
    for x in range(2, 54):
        rd.put(cv, x, 4, HULL[4]); rd.put(cv, x, 5, HULL[3])   # the bulkhead's lit top lip
    _conduit(cv, 5, 8, 46)                                     # a conduit down the west side
    for (x, y) in rect_set(36, 8, 8, 3):                      # a stencilled band over the door
        rd.put(cv, x, y, '#D89A3A' if (x // 2) % 2 == 0 else '#3A3440')
    rim = disc(28, 33, 19)
    door = set(disc(28, 33, 16))
    for (x, y) in rim:
        if (x, y) in door:
            continue
        a = math.atan2(y - 33, x - 28)
        lit = -math.cos(a + math.pi / 4)                  # 1 at the upper left
        c = rd.step(HULL[3], 1.6 * lit)
        r = math.hypot(x - 28, y - 33)
        if r > 18.2:
            c = rd.step(c, -1.4)                          # the rim's outer bevel
        elif r < 16.9:
            c = rd.step(HULL[2], -0.6 if lit > 0 else -1.6)   # its inner reveal, in shade
        if 17.2 < r < 18.2 and int((a + math.pi) / (2 * math.pi) * 16 + 0.5) % 2 == 0 \
                and abs(((a + math.pi) / (2 * math.pi) * 16) % 1 - 0.5) > 0.38:
            c = rd.step(HULL[4], 1) if lit > -0.2 else HULL[2]   # its bolts
        rd.put(cv, x, y, c)
    for (x, y) in door:
        west = x < 28
        c = rd.step('#7A8496' if west else '#5E687C', 0.9 * -((x - 28) + (y - 33)) / 22)
        dx, dy = (x - 28), (y - 33)
        if abs(dy) in (6, 7) and abs(dx) > 2:
            c = rd.step(c, -1.6 if abs(dy) == 6 else 0.8)   # the leaves' panel lines
        if abs(dx) in (5, 6) and abs(dy) < 6:
            c = rd.step(c, -1.2 if abs(dx) == 6 else 0.6)
        if dy > 9 and rd.smooth_noise(x, y, 3, 172) < 0.4:
            c = rd.mix(c, (74, 64, 60), 0.4)               # grime where boots and carts pass
        if math.hypot(dx, dy) > 15.2:
            c = rd.step(c, -1.2 if dx + dy > 0 else 1.0)   # the leaves' edge
        rd.put(cv, x, y, c)
    for y in range(17, 50):
        rd.put(cv, 28, y, HULL[0]); rd.put(cv, 27, y, rd.step('#7A8496', 1.4))   # the meeting seam
    for (hx, hy) in ((24, 31), (24, 35), (31, 31), (31, 35)):  # the leaves' handles
        rd.put(cv, hx, hy, '#C8CCD4'); rd.put(cv, hx + 1, hy, '#C8CCD4'); rd.put(cv, hx, hy + 1, HULL[1]); rd.put(cv, hx + 1, hy + 1, HULL[1])
    for x in range(4, 52, 6):
        for t in range(3):
            cv.set(x + t, 54 + t % 2, GOLD[3])
            cv.set(x + t + 3, 54 + t % 2, VOID[2])
    for x in range(4, 52):  # the chevrons scuffed where feet cross the sill
        if 18 <= x <= 38 and rd.smooth_noise(x, 54, 2, 173) < 0.45:
            rd.put(cv, x, 54, rd.mix(cv.get(x, 54), (150, 140, 128), 0.5))
    cv.rect(45, 9, 8, 10, HULL[0])
    cv.rect(46, 10, 6, 8, VOID[1])
    cv.hline(46, 10, 6, '#2C4A5A'); cv.hline(47, 13, 4, '#1E3A48'); cv.hline(47, 16, 3, '#1E3A48')   # its screen's lines
    cv.set(48, 12, CYAN[3]); cv.set(49, 12, CYAN[2]); cv.set(48, 15, GOLD[3]); cv.set(49, 15, GOLD[2])
    cv.hline(45, 19, 8, HULL[4])
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

def hydro_trough(crop: str = 'greens', length: int = 56) -> Canvas:
    """A hydroponic trough, `length` x 30: a white tank of plants in rows lit from above, a
    violet grow-light bar on two arms, a drip line. `crop` (review 19 Oct: not four the
    same): 'greens' (heads of lettuce), 'tomato' (vines on canes with red fruit), 'herbs'
    (feathery dill and basil, purple flowers) or 'sprouts' (seedling trays, young and
    pale)."""
    w, h = length, 30
    cv = Canvas(w, h, pad=PAD)
    for y in range(14, 28):
        for x in range(2, w - 2):
            c = HULL[5] if y == 14 else HULL[4] if y < 20 else HULL[3] if x < w - 6 else HULL[2]
            cv.set(x, y, c)
    n = (w - 10) // 5
    if crop == 'greens':
        for k in range(n):  # heads of greens in two rows
            for row in (0, 1):
                cx, cy = 7 + k * 5 + row * 2, 13 + row * 3
                for (x, y) in disc(cx, cy, 2.6):
                    cv.set(x, y, LEAF[4] if x + y < cx + cy - 1 else LEAF[3] if (x + y) % 2 else LEAF[2])
    elif crop == 'tomato':
        for k in range(0, n, 2):  # vines up thin canes, leaves and red fruit
            cx = 8 + k * 5
            cv.vline(cx, 6, 9, '#C8B48A')
            for y in range(7, 16):
                for dx in (-2, -1, 1, 2):
                    if noise2(cx + dx, y, 391) > 0.45:
                        cv.set(cx + dx, y, LEAF[3] if dx < 0 else LEAF[2])
            for (fx, fy) in ((cx - 2, 10), (cx + 2, 13), (cx + 1, 8)):
                cv.set(fx, fy, RED[3]); cv.set(fx, fy + 1, RED[2])
    elif crop == 'herbs':
        for k in range(n * 2):  # feathery fronds, a few purple flowers
            cx, cy = 5 + k * 2 + (k % 3), 10 + (k * 7) % 6
            for t in range(4):
                cv.set(cx + (t % 2), cy + t, LEAF[4] if t < 2 else LEAF[3])
            if k % 5 == 2:
                cv.set(cx, cy - 1, NAP[4])
    else:  # sprouts: seedling trays, young and pale
        for k in range(n * 2):
            cx, cy = 5 + k * 2 + (k % 2), 12 + (k % 3) * 2
            cv.set(cx, cy, LEAF[4]); cv.set(cx, cy + 1, '#C8D8A0')
    for px in (4, w - 6):
        cv.vline(px, 2, 12, HULL[3]); cv.vline(px + 1, 2, 12, HULL[1])
    for x in range(4, w - 4):
        cv.set(x, 2, NAP[4]); cv.set(x, 3, NAP[3]); cv.set(x, 4, HULL[1])
    for x in range(6, w - 6, 3):
        cv.set(x, 5, NAP[2] if x % 2 else NAP[1])  # the violet light falling
    cv.hline(3, 22, w - 6, CYAN[2])
    return cv


def _stool(cv: Canvas, cx: int, top: int, foot: int, seat=NAP):
    """A galley stool bolted to the deck (audit 20 Oct: the old ring of ovals read as a
    flying saucer): a padded round seat 7 px off the floor seen from the front and a
    little above, lit on its upper left, on a steel post to a bolted floor plate."""
    for (x, y) in oval(cx, top + 1.5, 4.5, 2):
        rd.put(cv, x, y, seat[4] if x < cx - 1 and y <= top + 1 else seat[3] if x < cx + 2 else seat[2])
    for x in range(cx - 4, cx + 5):
        rd.put(cv, x, top + 3, seat[1])                      # the cushion's side
    rd.put(cv, cx, top + 1, seat[1]); rd.put(cv, cx - 2, top + 1, seat[4])   # its button and a sheen
    for y in range(top + 4, foot - 1):                       # the post
        rd.put(cv, cx - 1, y, '#C8CCD8'); rd.put(cv, cx, y, '#8A90A2'); rd.put(cv, cx + 1, y, '#5E6476')
    for x in range(cx - 3, cx + 4):                          # the floor plate and its bolts
        rd.put(cv, x, foot - 1, '#9AA0B0' if x < cx else '#6A7084')
    rd.put(cv, cx - 3, foot - 1, '#E2E6EE'); rd.put(cv, cx + 3, foot - 1, '#4A5064')
    for x in range(cx - 2, cx + 5):
        rd.put(cv, x, foot, rd.step(cv.get(x, foot), -1.2) if cv.get(x, foot)[3] else HULL[1])


def galley_table() -> Canvas:
    """The galley table, 52 x 34 (audit 20 Oct, REDRAW: "reads as a flying saucer"): the
    crew's one shared meal a day at a long table bolted to the deck, seen from the front
    and above like everything else. Its top is a lit composite slab at counter height
    (13 px, an adult is 25) with a teal edge trim, its front apron in shade, one steel
    pedestal to a bolted foot plate; four stools bolted round it, two behind showing
    above the far edge and two in front; on the top, two meal trays with compartments
    (greens from the hydroponics, rice, a citrus half), mugs and the shared teapot."""
    w, h = 52, 34
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    for sx in (15, 37):  # the two stools behind the table, their seats showing over its far edge
        _stool(cv, sx, 4, 13)
    x0, x1, ty0, ty1 = 6, w - 6, 10, 19      # the top: front edge at foot - 13 = 20
    for y in range(ty0, ty1 + 1):
        for x in range(x0, x1):
            k = (x - x0) / (x1 - x0)
            c = rd.step('#D8DCE4', 0.9 - 1.4 * k - 0.04 * (y - ty0))
            if y == ty0:
                c = rd.step('#D8DCE4', 1.6 - k)               # the far edge catching the light
            if 0.3 < (x - y * 0.8 - 6) % 23 < 2.2 and y > ty0 + 1:
                c = rd.step(c, 0.7)                           # a wiped streak in the sheen
            rd.put(cv, x, y, c)
    for x in range(x0, x1):  # the trim and the apron, in shade under the top's lit edge
        k = (x - x0) / (x1 - x0)
        rd.put(cv, x, ty1 + 1, rd.step('#3E9AA0', 0.8 - k))
        for y in range(ty1 + 2, ty1 + 5):
            c = rd.step('#7A8094', -0.4 - 1.2 * k - 0.3 * (y - ty1 - 2))
            if y == ty1 + 4 and x % 6 == 2:
                c = '#3A3E4C'                                 # rivets along the apron's foot
            rd.put(cv, x, y, c)
    for x in (x0, x1 - 1):  # rounded corners
        rd.put(cv, x, ty0, (0, 0, 0, 0)) if False else None
    for y in range(ty1 + 5, foot - 1):  # the pedestal, a lit steel column
        for (dx, c) in ((-2, '#D0D4DE'), (-1, '#A8AEBE'), (0, '#8A90A2'), (1, '#6A7084'), (2, '#4E5466')):
            rd.put(cv, w // 2 + dx, y, c)
    for x in range(w // 2 - 6, w // 2 + 7):
        rd.put(cv, x, foot - 1, '#9AA0B0' if x < w // 2 else '#6A7084')
        rd.put(cv, x, foot, '#3A3E4C')
    rd.put(cv, w // 2 - 5, foot - 1, '#E2E6EE'); rd.put(cv, w // 2 + 5, foot - 1, '#4A5064')
    # the trays: compartments of food, each tray lit on its upper left
    for (tx, ty, tray) in ((10, 12, ('#E8A43A', '#B87420')), (31, 13, ('#4A8AC8', '#2E5E94'))):
        for y in range(ty, ty + 6):
            for x in range(tx, tx + 11):
                c = tray[0] if (x == tx or y == ty) else tray[1] if (x == tx + 10 or y == ty + 5) else rd.step(tray[0], -0.4)
                rd.put(cv, x, y, c)
        for (fx, fy, fw, fh, ramp) in ((tx + 1, ty + 1, 5, 4, LEAF), (tx + 7, ty + 1, 3, 2, ['#B0A890', '#D8D0B8', '#EEE8D8', '#F8F4EA', '#FFFFFF']),
                                       (tx + 7, ty + 3, 3, 2, GOLD)):
            for y in range(fy, fy + fh):
                for x in range(fx, fx + fw):
                    n = noise2(x, y, 291)
                    rd.put(cv, x, y, ramp[3] if n > 0.6 else ramp[2] if n > 0.25 else ramp[1])
    for (mx, my, c) in ((24, 11, RED), (27, 16, WTR)):  # mugs, with the tea's dark surface
        for (x, y) in ((mx, my), (mx + 1, my), (mx + 2, my)):
            rd.put(cv, x, y, '#5A3A24')
        for x in range(mx, mx + 3):
            rd.put(cv, x, my + 1, c[3] if x == mx else c[2]); rd.put(cv, x, my + 2, c[2] if x == mx else c[1])
        rd.put(cv, mx + 3, my + 1, c[1])
    for (x, y) in oval(45 - 6, 12, 3.2, 2.2):  # the shared teapot at the far end, its lid and spout
        rd.put(cv, x, y, '#F0EEE8' if x < 38 and y < 12 else '#C8C4BE' if x < 41 else '#8E8A86')
    rd.put(cv, 39, 9, '#8E8A86'); rd.put(cv, 38, 9, '#F0EEE8'); rd.put(cv, 43, 11, '#C8C4BE'); rd.put(cv, 44, 10, '#C8C4BE')
    for (nx, ny) in ((8, 18), (22, 18), (29, 19), (43, 17)):  # napkins and cutlery at each place
        rd.put(cv, nx, ny, '#F4EEDC'); rd.put(cv, nx + 1, ny, '#F4EEDC'); rd.put(cv, nx + 1, ny + 1, '#C8BEA4')
        rd.put(cv, nx + 2, ny, '#9AA0B0'); rd.put(cv, nx + 2, ny - 1, '#E2E6EE')
    for (x, y) in ((20, 13), (20, 14), (21, 14)):  # a cup with a sprig from the hydroponics
        rd.put(cv, x, y, '#E8E4DC' if y == 14 else '#B8B4AC')
    rd.put(cv, 20, 12, LEAF[3]); rd.put(cv, 21, 11, LEAF[4]); rd.put(cv, 19, 11, LEAF[2])
    rd.put(cv, 34, 10, '#C84A3A'); rd.put(cv, 34, 11, '#8E2E26'); rd.put(cv, 35, 11, '#6A2420'); rd.put(cv, 34, 9, '#E8E4DC')  # the hot sauce
    for (x, y) in ((17, 18), (18, 18), (40, 19), (41, 19)):
        rd.put(cv, x, y, rd.step(cv.get(x, y), -0.9))       # crumbs and rings where mugs stood
    for sx in (13, 39):  # the two stools in front, pulled in under the table's edge
        _stool(cv, sx, foot - 8, foot)
    return cv


def bookshelf() -> Canvas:
    """A bookshelf, 40 x 36 (size guide: a cupboard is 28 to 38 tall), its three shelves
    held by elastic straps against the station's low gravity: spines of different heights
    and colours, each lit on its west edge, the odd one leaning, a plant trailing from the
    top. Its carcass is hull panelling, lit on the west, in shade on the east."""
    w, h = 40, 36
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, h - 1):
        for x in range(2, w - 2):
            cv.set(x, y, HULL[4] if x < 4 else HULL[3] if x < w - 5 else HULL[1])
    cv.hline(2, 6, w - 4, HULL[5]); cv.hline(2, h - 2, w - 4, HULL[1])
    cols = [RED, GOLD, NAP, LEAF, WTR, RED, NAP, GOLD]
    for shelf in range(3):
        y0 = 8 + shelf * 9
        for (x, y) in rect_set(5, y0, w - 10, 8):
            cv.set(x, y, HULL[0] if y < y0 + 2 else HULL[1])     # the shelf's shadowed back
        x, k = 6, shelf * 3
        while x < w - 8:
            bw = 2 + (k * 7) % 2
            bh = 5 + (k * 5) % 3
            ramp = cols[k % len(cols)]
            for yy in range(y0 + 7 - bh, y0 + 7):
                for xx in range(x, min(x + bw, w - 6)):
                    cv.set(xx, yy, ramp[3] if xx == x else ramp[2])
            cv.set(x, y0 + 7 - bh, ramp[4])                       # the spine's lit top
            if k % 3 == 1:
                cv.set(x + bw, y0 + 7 - bh + 1, ramp[2])           # a band on the spine
            x += bw + (1 if k % 4 else 2)
            k += 1
        cv.hline(5, y0 + 7, w - 10, HULL[4]); cv.hline(5, y0 + 8, w - 10, HULL[2])   # the shelf board
        cv.hline(5, y0 + 4, w - 10, CYAN[1]); cv.set(5, y0 + 4, CYAN[3])             # the strap and its buckle
    for (x, y) in disc(11, 4, 4):  # the plant on top, trailing down the side
        cv.set(x, y, LEAF[4] if x + y < 13 else LEAF[3] if x < 13 else LEAF[2])
    for t in range(12):
        cv.set(3 + (t % 2), 6 + t, LEAF[3] if t % 3 else LEAF[1])
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
    """A low padded bench, 34 x 18 (audit and size guide: 32 long, seat 7), two cushions
    in soft violet buttoned and lit on their upper left, on a hull frame with its feet,
    for watching the planet."""
    w, h = 34, 18
    cv = Canvas(w, h, pad=PAD)
    for y in range(7, 13):
        for x in range(2, w - 2):
            cv.set(x, y, HULL[3] if y > 10 else NAP[2] if x < w - 4 else NAP[1])
    for cx in (10, 24):
        for (x, y) in oval(cx, 6, 7, 3):
            cv.set(x, y, NAP[4] if x < cx - 1 and y < 6 else NAP[3] if x < cx + 3 else NAP[2])
        cv.set(cx, 6, NAP[1]); cv.set(cx - 3, 5, NAP[4])       # its button and a sheen
    cv.hline(2, 11, w - 4, HULL[4])
    for fx in (4, w - 6):
        cv.vline(fx, 13, 3, HULL[2]); cv.vline(fx + 1, 13, 3, HULL[1])
    cv.hline(2, 13, w - 4, HULL[1])
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


def solar_array(width: int = 64, seed: int = 0, tilt: int = 4) -> Canvas:
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
        xa, xb = int(2 + t * tilt), int(w - 6 + t * (tilt - 1))  # tilted: the top edge set back
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
REG = LUNAR  # Lumen's regolith


def pressure_tube(length: int = TUBE_L, dock: bool = False) -> Canvas:
    """A closed pressurised tube between two modules, running north-south, 28 x `length`:
    a white hull seen from above, rounded (lit on the left, falling into shade on the
    right), stiffened by ring frames every few paces, a strip of small lit ports along
    its crown, and saddles on short feet where it rests on the dust."""
    w, h = TUBE_W, length
    cv = Canvas(w, h, pad=PAD)
    tints = ((242, 240, 232), (226, 232, 242), (214, 216, 222), (238, 230, 214))
    seam = 3 + int((w - 7) * 0.62)
    for y in range(0, h):
        sec, ring = divmod(y, 12)
        rr = random.Random(971 * 31 + sec * 7 + length)
        tint, hatch, marks = tints[rr.randrange(4)], rr.random() < 0.3, rr.random() < 0.5
        for x in range(3, w - 3):
            k = (x - 3) / (w - 7)
            v = 1.0 if k < 0.12 else 0.4 if k < 0.3 else 0 if k < 0.5 else -0.9 if k < 0.7 else -1.9 if k < 0.84 else -3.0
            if k > 0.92:
                v = -4.2
            c = rd.step(tint, v)
            if ring == 0:
                c = rd.step(c, -2.2)                       # a ring frame
            elif ring == 1:
                c = rd.step(c, 0.9)                        # its lit edge
            elif ring == 2 and x % 3 == 1 and 0.12 < k < 0.9:
                c = rd.step(c, -2.4)                       # rivets along the frame
            elif ring == 2 and x % 3 == 0 and 0.12 < k < 0.9:
                c = rd.step(c, 0.6)
            elif x == seam and ring > 1:
                c = rd.step(c, -1.6)                       # the plates' long seam
            elif x == seam + 1 and ring > 1:
                c = rd.step(c, 0.7)
            elif sec % 3 == 1 and ring in (8, 9) and x > 10:
                c = rd.mix(c, '#3E78B8' if ring == 8 else '#E8A43A', 0.7)   # a section's ID band
            elif hatch and 14 <= x <= 19 and 4 <= ring <= 9:
                c = rd.step(c, -1.8 if x == 19 or ring == 9 else 1.2 if x == 14 or ring == 4 else -0.4)  # an inspection hatch
                if (x, ring) == (16, 6):
                    c = (64, 66, 80)                       # its latch
            elif marks and ring in (4, 6) and 4 <= x <= 7 and (x + ring) % 4 != 0:
                c = rd.step(c, -3.2)                       # a stencilled mark
            if x == 9 and ring in (5, 6):
                c = '#FFDC92' if ring == 5 else '#F2A048'  # a small lit port on the crown
            rd.put(cv, x, y, c)
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
    rd.weather(cv, rect_set(3, 0, w - 6, h), seed=971 + length, chips=0.05, chip=(118, 126, 146),
               streaks=0.12, streak=(120, 112, 128), scuffs=0.08)
    for y in range(0, h):  # dust settled on the tube's lower, shaded flank
        for x in range(w - 9, w - 3):
            if rd.smooth_noise(x, y, 4, 975) < 0.45:
                rd.put(cv, x, y, rd.mix(cv.get(x, y), REG[3], 0.4))
    for y in range(6, h, 24):  # saddles on their feet, at the sides
        for (sx, d) in ((1, -1), (w - 3, 1)):
            for k in range(3):
                cv.set(sx + (k if d < 0 else -k + 1), y + 4, WHITE[2] if d < 0 else WHITE[1])
            cv.set(sx, y + 5, WHITE[1]); cv.set(sx + (0 if d < 0 else 1), y + 6, REG[1])
    return cv


def hab_hub() -> Canvas:
    """The hub, 148 x 122 (Matt, 20 Oct 10:15: "looks flat and its hard to tell what it is
    supposed to be"; a lunar habitat reads at a glance as a pressurised module): a long
    cylindrical module lying east-west on three cradles, seen from the front and above.
    Its curved shell is white plates in rings, with ring frames, rivets and long seams; in
    airless light its upper surface is lit from the upper left and the shade begins at a
    hard terminator, with no ambient fill, the underside near black. The west end cap
    faces the sun, the east cap is dark. A row of small round viewports glows warm along
    its front, an ID band runs below them, dust has climbed the lower plates. On top: the
    docking collar where the gangway tube from the shuttle arrives, a mast with a dish
    and a red beacon, a whip antenna and a vent box. The cradles stand on broad footpads
    in the dust. At the west end an EVA airlock: a box with a framed hatch and a round
    window, steps down to the regolith and a handrail. A power cable runs from the east
    cap down to the ground. At the front centre, the docking porch where the tube to the
    greenhouse leaves, its hatch open into the warm-lit lock."""
    w, h = 148, 122
    cv = Canvas(w, h, pad=PAD)
    X0, X1, Y0, Y1 = 14, 134, 14, 92       # the shell's cylinder (its axis east-west)
    # the shell's plates: white beta cloth, greyer shielding, tan where the cloth has aged
    # in the sun, the odd panel of gold foil
    tints = ((226, 226, 222), (200, 210, 226), (224, 208, 180), (192, 194, 200), (214, 220, 212), (200, 172, 104))
    term = 0.44                             # the terminator: lit above, shade below
    for y in range(Y0, Y1 + 1):
        u = (y - Y0) / (Y1 - Y0)
        for x in range(X0, X1 + 1):
            ring, band = (x - X0) // 20, int(u * 3)
            col, row = (x - X0) // 10, (y - Y0) // 9            # each ring is clad in small plates
            pick = int(noise2(col, row, 1179) * 13)
            tint = tints[5] if pick == 12 and row < 6 else tints[pick % 5]
            tint = rd.step(tint, (noise2(col, row, 1178) - 0.5) * 1.2)
            west = 1 - (x - X0) / (X1 - X0)
            if u < 0.06:
                v = 1.4                                     # the crest catching the sun
            elif u < term + 0.03 * math.sin(x / 7):
                v = 0.6 - u * 1.0 + 0.6 * west              # the upper surface, lit
            elif u < 0.84:
                v = -1.9 + 0.4 * west - (u - term) * 1.0    # the front, past the terminator
            else:
                v = -3.6                                    # the underside, near black
            c = rd.step(tint, v)
            px = (x - X0) % 20
            if px == 0:
                c = rd.step(c, -2.0)                        # a ring frame
            elif px == 1:
                c = rd.step(c, 0.9 if u < term else 0.4)
            elif px in (3, 17) and int(u * 40) % 4 == 1 and u < 0.84:
                c = rd.step(c, -1.8)                        # rivets down the ring
            if abs(u - 0.24) < 0.012 or abs(u - 0.62) < 0.012:
                c = rd.step(c, -1.4)                        # the long seams between plates
            if 0.7 < u < 0.745:
                c = rd.mix(c, '#3E78B8' if u < 0.725 else '#E8A43A', 0.7)   # the ID band
            elif u < 0.84 and ((y - Y0) % 9 == 0 or (x - X0) % 10 == 0):
                c = rd.step(c, -1.0)                        # the joints between the small plates
            elif u < 0.84 and ((y - Y0) % 9 == 1 or (x - X0) % 10 == 1):
                c = rd.step(c, 0.5)
            if 0.7 < u < 0.84 and rd.smooth_noise(x, y, 4, 1180) < 0.35 + (u - 0.7) * 2:
                c = rd.mix(c, REG[2], 0.45)                 # dust thrown up onto the lower plates
            rd.put(cv, x, y, c)
    shell = rect_set(X0, Y0, X1 - X0 + 1, int((Y1 - Y0) * 0.84))
    rd.weather(cv, shell, seed=1182, chips=0.0, streaks=0.0, scuffs=0.12)
    for ring in range(6):  # EVA handrails along the top, yellow, on standoffs, and a grapple pin
        x0r = X0 + ring * 20 + 4
        for x in range(x0r, x0r + 13):
            rd.put(cv, x, Y0 + 8, '#F2C84A' if x < x0r + 9 else '#C8962A')
            if (x - x0r) % 6 == 0:
                rd.put(cv, x, Y0 + 9, '#8A90A2'); rd.put(cv, x, Y0 + 10, rd.step(cv.get(x, Y0 + 10), -1.8))
        if ring in (1, 4):
            for (x, y) in rect_set(x0r + 4, Y0 + 20, 6, 4):   # an access panel, lit on its top and west
                rd.put(cv, x, y, rd.step(cv.get(x, y), 1.0 if (y == Y0 + 20 or x == x0r + 4) else -1.4 if (y == Y0 + 23 or x == x0r + 9) else 0))
            rd.put(cv, x0r + 7, Y0 + 21, '#3E4252'); rd.put(cv, x0r + 8, Y0 + 21, '#3E4252')
    for x in range(X0 + 2, X1 - 1):  # two pipes along the front under the band, on brackets
        if 56 <= x <= 92:
            continue
        py = Y0 + int((Y1 - Y0) * 0.79)
        rd.put(cv, x, py, '#E8ECF2'); rd.put(cv, x, py + 1, '#8A93A8')
        rd.put(cv, x, py + 2, MATERIALS['brass'][4]); rd.put(cv, x, py + 3, MATERIALS['brass'][2])
        if x % 9 == 0:
            for d in range(4):
                rd.put(cv, x, py + d, '#4E5466')
    for (sx0, sx1) in ((X0 + 22, X0 + 38), (X0 + 82, X0 + 98)):  # strips of solar cells on the top, in their frames
        for y in range(Y0 + 12, Y0 + 19):
            for x in range(sx0, sx1):
                edge = y in (Y0 + 12, Y0 + 18) or x in (sx0, sx1 - 1)
                cell = ((x - sx0) // 3 + (y - Y0) // 3) % 2
                c = '#C8CCD8' if edge else ('#2E4A7A' if cell else '#3A5A90')
                if not edge and (x - sx0) % 3 == 0:
                    c = '#5878A8'                           # the cells' bus bars catching the light
                if not edge and y == Y0 + 13 and x < sx0 + 8:
                    c = '#8AA8D0'                           # the sky's glint on the glass
                rd.put(cv, x, y, c)
    cy_ = Y0 + int((Y1 - Y0) * 0.36)
    for x in range(X0 + 3, X1 - 2):  # a cable bundle along the shell's shoulder, clipped at each ring
        rd.put(cv, x, cy_, '#C8443A'); rd.put(cv, x, cy_ + 1, '#3E78B8'); rd.put(cv, x, cy_ + 2, '#5E6476')
        if (x - X0) % 20 == 10:
            for d in range(-1, 4):
                rd.put(cv, x, cy_ + d, '#E8ECF2' if d < 1 else '#8A93A8')
    for k in range(6):  # status lights beside each ring's viewport, green and amber
        lx, ly = X0 + 15 + k * 20, Y0 + int((Y1 - Y0) * 0.55) + 3
        if abs(lx - 74) < 20:
            continue
        rd.put(cv, lx, ly, '#4AD07A'); rd.put(cv, lx, ly + 1, '#2A7A4A')
        rd.put(cv, lx + 2, ly, '#F2A048'); rd.put(cv, lx + 2, ly + 1, '#9A5A20')
    for (mx, my) in ((X0 + 23, Y0 + 30), (X0 + 63, Y0 + 30), (X0 + 103, Y0 + 30)):  # stencilled marks by the rings
        for k in range(4):
            rd.put(cv, mx + k, my, '#3A3E4C' if k != 2 else '#E8A43A')
    for y in range(Y0, Y1 + 1):  # the end caps: the west one faces the sun, the east one is dark
        u = (y - Y0) / (Y1 - Y0)
        half = 6 * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2))
        for x in range(int(X0 - half), X0):
            rd.put(cv, x, y, rd.step((236, 236, 232), 1.2 - 0.6 * u if u < 0.84 else -2.6))
        for x in range(X1 + 1, int(X1 + 1 + half)):
            rd.put(cv, x, y, rd.step((220, 222, 226), -2.4 - u))
        if 0.1 < u < 0.84:
            rd.put(cv, int(X0 - half * 0.5), y, rd.step((236, 236, 232), 0.2))   # the cap's bolted rim
            rd.put(cv, int(X1 + 1 + half * 0.5), y, rd.step((220, 222, 226), -3.4))
    for k in range(6):  # the viewports: round, deep, warm inside, along the front
        vx, vy = X0 + 10 + k * 20, Y0 + int((Y1 - Y0) * 0.55)
        if abs(vx - 74) < 18:
            continue  # the porch stands there
        for (x, y) in disc(vx, vy, 2.6):
            rd.put(cv, x, y, '#5E6476')
        for (x, y) in disc(vx, vy, 1.6):
            rd.put(cv, x, y, '#FFDC92' if (x, y) != (vx + 1, vy + 1) else '#E8A44A')
        rd.put(cv, vx - 1, vy - 1, '#FFF4D0')
    for (cx_, collar) in ((75, True),):  # the docking collar on top, where the gangway arrives
        for y in range(Y0 - 4, Y0 + 6):
            for x in range(cx_ - 14, cx_ + 15):
                k = (x - cx_ + 14) / 28
                c = rd.step((232, 232, 228), 1.0 - 2.2 * k)
                if y in (Y0 - 4, Y0 + 5):
                    c = rd.step(c, -1.6)
                if y == Y0 and (x - cx_) % 5 == 0:
                    c = '#E8C04A'                           # its clamps
                rd.put(cv, x, y, c)
    for y in range(0, Y0 + 8):  # the mast with its dish and beacon, on the east of the top
        rd.put(cv, 118, y, '#D8DCE4'); rd.put(cv, 119, y, '#7A8094')
    for (x, y) in oval(115, 6, 5, 2.4):
        rd.put(cv, x, y, '#F0F2F6' if x < 115 else '#B8BECC' if x < 118 else '#7A8094')
    rd.put(cv, 115, 6, '#4A5064'); rd.put(cv, 118, 0, RED[3]); rd.put(cv, 119, 0, RED[1])
    for y in range(2, Y0 + 6):  # a whip antenna on the west of the top
        rd.put(cv, 30, y, '#C8CCD4' if y % 4 else '#7A8094')
    for (x, y) in rect_set(40, Y0 + 2, 10, 6):  # a vent box, lit on its top and west
        rd.put(cv, x, y, '#F2F2EE' if y == Y0 + 2 or x == 40 else '#5E6476' if x == 49 or y == Y0 + 7 else '#9AA0B0')
    for x in range(41, 52):
        rd.put(cv, x, Y0 + 8, rd.step(cv.get(x, Y0 + 8), -2.4))   # its hard shadow on the shell
    for cx_ in (32, 118):  # the cradles under the shell, on broad footpads in the dust
        for y in range(Y1 - 2, Y1 + 6):
            for x in range(cx_ - 7, cx_ + 8):
                rd.put(cv, x, y, '#8A90A2' if x < cx_ else '#4E5466')
        for y in range(Y1 + 6, h - 8):
            for (dx, c) in ((-5, '#B8BECC'), (-4, '#6A7084'), (4, '#8A90A2'), (5, '#3E4252')):
                rd.put(cv, cx_ + dx, y, c)
        for y in range(h - 8, h - 5):
            for x in range(cx_ - 9, cx_ + 10):
                c = '#C8CCD8' if y == h - 8 else '#6A7084' if x < cx_ + 4 else '#3E4252'
                if y == h - 6 and rd.smooth_noise(x, y, 2, 1181) < 0.5:
                    c = REG[3]                              # dust kicked over the pad
                rd.put(cv, x, y, c)
    # the EVA airlock at the west end: a box, its framed hatch with a round window, steps
    ex0, ex1, ey0, ey1 = 0, 22, 52, 96
    for y in range(ey0, ey1 + 1):
        for x in range(ex0, ex1 + 1):
            if y < ey0 + 5:
                c = rd.step((236, 236, 232), 1.2 - (x - ex0) / 30)     # its roof, lit
            else:
                c = rd.step((228, 228, 226), -0.9 - (x - ex0) / 40)      # its front
                if x in (ex0, ex1):
                    c = rd.step(c, -1.2)
            if y == ey0 + 5:
                c = rd.step((228, 228, 226), -2.4)
            rd.put(cv, x, y, c)
    for y in range(ey0 + 10, ey1 - 1):  # the hatch in its frame
        for x in range(ex0 + 5, ex1 - 4):
            frame = x in (ex0 + 5, ex1 - 5) or y in (ey0 + 10, ey1 - 2)
            c = '#E8C04A' if frame and (x + y) % 4 < 2 else '#3A3E4C' if frame else rd.step('#9AA0B0', -0.4 * (x > ex0 + 11))
            rd.put(cv, x, y, c)
    for (x, y) in disc(ex0 + 11, ey0 + 18, 2.4):
        rd.put(cv, x, y, '#FFDC92' if y > ey0 + 17 else '#FFF0C0')     # its window, lit from inside
    rd.put(cv, ex0 + 15, ey0 + 26, '#E8E4DC'); rd.put(cv, ex0 + 15, ey0 + 27, '#5E6476')   # the handle
    for k in range(3):  # the steps down to the regolith, each tread lit, each riser in shade
        y = ey1 + 1 + k * 4
        for x in range(ex0 + 3 - k, ex1 - 2 - k):
            rd.put(cv, x, y, '#D8DCE4'); rd.put(cv, x, y + 1, '#9AA0B0')
            rd.put(cv, x, y + 2, '#4E5466'); rd.put(cv, x, y + 3, '#3A3E4C')
    for y in range(ey1 - 4, ey1 + 12):  # the handrail
        rd.put(cv, ex1 - 1 - (y - ey1) // 4, y, '#E8C04A' if y % 3 else '#9A7A2A')
    for y in range(66, h - 10):  # the power cable from the east cap down to the dust
        rd.put(cv, X1 + 4, y, '#3A3C4A'); rd.put(cv, X1 + 5, y, '#8A93A8' if y % 5 else '#3A3C4A')
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
    for x in range(px0 + 3, px0 + pw - 3):  # the hatch's hood, standing out over the lamp
        cv.set(x, ptop + 7, WHITE[5] if x < px0 + pw - 6 else WHITE[3])
        cv.set(x, ptop + 8, WHITE[2] if x < px0 + pw - 6 else WHITE[1])
    for x in range(px0 + 4, px0 + pw - 2):
        rd.put(cv, x, ptop + 10, rd.step(cv.get(x, ptop + 10), -1.4))   # its shadow
    frame = rect_set(px0, ptop, pw, pfoot - ptop - 4) - rect_set(px0 + 5, ptop + 11, pw - 10, pfoot - ptop - 14)
    rd.weather(cv, frame, seed=1071, chips=0.06, chip=(120, 128, 150), dust=REG[3], foot=pfoot - 4, reach=8)
    return cv


def _through_hatch(x: int, y: int, w: int, h: int):
    """The greenhouse seen through the open inner hatch (D13): its glass bright overhead,
    leafy beds either side of a grated walk running in, the light green and warm."""
    if y < 6:
        return rd.mix('#E4F2DC', '#CFE8C8', y / 6)            # the glazing overhead
    side = min(x, w - 1 - x)
    walk = side > 4 + (y - 6) // 6                           # the walk narrows into the distance
    if walk:
        c = rd.rgb('#9AA898' if y % 3 else '#7E8C80')         # the grating, lit, its bars
        if y > h - 8:
            c = rd.step(c, 0.6)
        return c
    n = rd.smooth_noise(x, y, 3, 1147)
    leaf = LEAF[4] if n > 0.72 else LEAF[3] if n > 0.45 else LEAF[2] if n > 0.22 else LEAF[1]
    if 0.62 < n < 0.65 and y > 12:
        leaf = '#E89A4A'                                     # a ripening fruit among the leaves
    return rd.step(leaf, 0.6 - y / h)


def airlock_module() -> Canvas:
    """The airlock between the corridor tube and the greenhouse, 46 x 58: a white
    module with its roof lit, two hatches in a line (the outer at its north end hidden
    behind it, the inner opening south into the dome), hazard stripes on its sill, a
    status light that is green (both doors may open: the dome is at pressure)."""
    w, h = 46, 58
    cv = Canvas(w, h, pad=PAD)
    for y in range(0, 20):  # its roof, ribbed
        for x in range(2, w - 2):
            k = (x - 2) / (w - 4)
            c = WHITE[5] if k < 0.2 else WHITE[4] if k < 0.7 else WHITE[2]
            if y % 9 == 0:
                c = WHITE[2] if k < 0.7 else WHITE[1]
            cv.set(x, y, c)
    for y in range(0, 20):  # D13: the roof's plates of slightly different whites, riveted along the ribs
        for x in range(2, w - 2):
            t = ((214, 224, 240), (240, 228, 206), (196, 200, 212))[((x - 2) // 14 + y // 9) % 3]
            c = cv.get(x, y)
            out = rd.mix(c, t, 0.6)
            if rd.smooth_noise(x, y, 4, 1146) < 0.3:
                out = rd.mix(out, REG[4], 0.35)               # moon dust drifted onto the roof
            if y % 9 == 1 and x % 3 == 0 and x < w - 6:
                out = rd.step(out, -2.2)
            elif y % 9 == 2 and x % 3 == 0 and x < w - 6:
                out = rd.step(out, -0.8)
            rd.put(cv, x, y, out)
    for (x, y) in rect_set(8, 4, 9, 5):  # a vent box on the roof, lit on its top and west
        rd.put(cv, x, y, '#F2F2EE' if y == 4 or x == 8 else '#5E6476' if x == 16 or y == 8 else
               ('#8A90A2' if (x - 8) % 2 else '#B8BECC'))
    for x in range(8, 18):
        rd.put(cv, x, 9, rd.step(cv.get(x, 9), -1.6))       # its shadow
    for y in range(2, 19):  # a cable tray along the roof's east side
        rd.put(cv, w - 10, y, '#4A5064'); rd.put(cv, w - 9, y, RED[2] if y % 5 else RED[1]); rd.put(cv, w - 8, y, '#3E78B8')
    face = rect_set(2, 20, w - 6, h - 25)
    rd.panels(cv, face, ('#D4D8E2', '#E4DCC8', '#B8BECC', '#DADCE0', '#C4C0B8'), seed=1144, pw=14, ph=10, light_x=0.08,
              grime=(120, 112, 112), rust=(150, 120, 96))
    for y in range(20, h - 1):  # its front face with the inner hatch (32 tall: verticality.md 5)
        for x in range(2, w - 2):
            if x >= w - 6:
                rd.put(cv, x, y, rd.step(WHITE[1], -0.6 if x == w - 3 else 0))   # its east side, in shade
            if y > h - 5:
                cv.set(x, y, '#E8C04A' if ((x + y) // 3) % 2 else '#2A2630')
    rd.weather(cv, rect_set(2, 0, w - 4, h - 5), seed=1145, chips=0.05, chip=(120, 128, 150), dust=REG[3],
               foot=h - 5, reach=8, scuffs=0.06)
    for y in range(h - 41, h - 9):
        for x in range(12, w - 12):
            c = _through_hatch(x - 12, y - (h - 41), w - 24, 32)  # the greenhouse seen through the hatch
            if x in (12, w - 13):
                c = WHITE[1]
            rd.put(cv, x, y, c)
    cv.set(w - 9, h - 40, '#4AD07A'); cv.set(w - 8, h - 40, '#2A9A5A')  # the status light
    for y in range(h - 9, h - 5):  # the collar where it meets the dome's sill, clamped
        for x in range(0, w):
            c = WHITE[4] if y == h - 9 else WHITE[2] if x < w - 6 else WHITE[1]
            if y == h - 7 and x % 6 == 2:
                c = '#E8C04A'
            cv.set(x, y, c)
    return cv


def glass_dome() -> Canvas:
    """The greenhouse dome, 240 x 208, glazed all over (the review: "glaze the whole
    dome, plants inside"): panes of tinted glass in a frame of struts, meridians and
    rings, the sun's reflection on the upper left, the glass only faintly tinted so the
    plants and the people inside show through it, on a cast sill. The back half is a
    little denser, so the airlock that joins it at the back reads as behind the glass
    (review 19 Oct). Drawn over everything inside it."""
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
        # (review 19 Oct: the small ring at the crown and the struts' ends there read as
        # a cable over the top, so the frame stops at the second ring and the crown is a
        # single clear pane)
        mer = ph < 0.79 and abs(th * 8 / math.pi - round(th * 8 / math.pi)) * (1 + 2.5 * ph) < 0.07
        ring = abs(ph * 8 / math.pi - round(ph * 8 / math.pi)) < 0.035 and 0.05 < ph < 0.9
        if mer or ring:
            lit = math.cos(th - 2.4) * math.cos(ph) + math.sin(ph) * 0.6
            c = (236, 240, 248, 255) if lit > 0.3 else (176, 184, 200, 255) if lit > -0.3 else (120, 128, 148, 255)
            if mer and ring and front:
                c = (255, 230, 170, 255) if lit > 0 else (90, 96, 118, 255)   # a node where struts meet, its bolt cap
            if not front:  # the far struts, seen through the glass: faint, so they never read as cables over it
                c = (150, 160, 182, 96)
        else:
            # glass: a cool tint, a little stronger on the back half (seen through twice)
            a = 54 if front else 104  # the back half denser: what stands behind the dome reads as behind glass
            # D13 (audit: glazing lines only): every pane catches the sky a little differently,
            # some bluer, some greener or violet, the panes facing up brightest
            # (each pane is the cell between two meridians and two rings, so its tint stops
            # at the struts; above the top ring, where the meridians stop, the crown is one
            # clear pane with one tint)
            pane = (int(th * 8 / math.pi), int(ph * 8 / math.pi)) if ph < 0.79 else (0, 99)
            pv = noise2(*pane, 1181)
            tint = (150, 196, 228) if pv < 0.4 else (140, 206, 210) if pv < 0.65 else (170, 180, 230) if pv < 0.85 else (196, 214, 236)
            c = (*tint, a + (14 if front and ph > 0.55 else 0))
            if ph >= 0.79:  # the crown, one curved pane: the sky's tint deepening toward its top, its edge brighter
                k = min(1.0, (ph - 0.79) / 0.78)
                c = (int(196 - 50 * k), int(214 - 24 * k), int(236 - 6 * k), min(120, a + 14 + int(26 * (1 - k))))
            u = math.cos(th - 2.2) * math.cos(ph) + math.sin(ph) * 0.5
            if front and 0.55 < u < 0.95:
                c = (240, 248, 255, int(70 + 120 * (u - 0.55)))  # the sun's reflection, high on the upper left, soft
            elif front and u > 0.95:
                c = (255, 255, 255, 200)
            if front and 0.05 < (th * 8 / math.pi) % 1 < 0.12 and 0.15 < ph < 0.7 and pv > 0.5:
                c = (255, 255, 255, 120)  # a glint along a pane's edge
        cv.set(x, y, c)
    for i in range(0, 721):  # the sill: a cast ring the glass stands on, its front lit
        th = 2 * math.pi * i / 720
        for k in range(4):
            x, y = int(round(cx + (rx + 1) * math.cos(th))), int(round(cy - (ry + 1) * math.sin(th))) + k
            if math.sin(th) < 0.1 and 0 <= x < w and 0 <= y < h:
                c = (232, 228, 238, 255) if k == 0 else (184, 180, 200, 255) if k < 3 else (120, 116, 140, 255)
                if k == 1 and i % 24 < 2:
                    c = (98, 96, 118, 255)            # a bolt in the sill's ring
                elif k == 2 and i % 24 < 2:
                    c = (210, 206, 220, 255)
                elif k == 3 and rd.smooth_noise(x, y, 3, 1183) < 0.4:
                    c = (*rd.mix(c, REG[3], 0.5), 255)  # moon dust against its foot
                cv.set(x, y, c)
    return cv


def props_station() -> dict[str, Canvas]:
    return {'garden_pod': garden_pod(), 'garden_pod_b': garden_pod(1), 'viewport': viewport(18, 8), 'viewport_b': viewport(112, 8),
            'viewport_c': viewport(206, 8), 'sleep_pod': sleep_pod(), 'airlock': airlock(),
            'console': console(), 'hydro_trough': hydro_trough(), 'hydro_trough_tomato': hydro_trough('tomato', 52), 'hydro_trough_herbs': hydro_trough('herbs', 48), 'hydro_trough_sprouts': hydro_trough('sprouts', 56), 'galley_table': galley_table(),
            'bookshelf': bookshelf(), 'telescope': telescope(), 'lounge_bench': lounge_bench(), 'lockers': lockers(),
            'tea_dispenser': tea_dispenser(), 'aquarium_column': aquarium_column(), 'cargo_crates': cargo_crates(),
            'floor_cushions': floor_cushions()}


def props_lumen() -> dict[str, Canvas]:
    return {'shuttle': shuttle(), 'dream_pool': dream_pool(), 'dream_pool_b': dream_pool(4), 'moon_tree': moon_tree(), 'hammock': hammock(),
            'moon_rock': moon_rock(True), 'moon_rock_small': moon_rock(False), 'moon_rock_b': moon_rock(True, 3),
            'moon_rock_small_b': moon_rock(False, 5), 'glow_caps': glow_caps(), 'old_lander': old_lander(),
            'solar_array': solar_array(64, 0), 'solar_array_b': solar_array(52, 1, 6), 'solar_array_c': solar_array(58, 2, 2), 'radiator': radiator(),
            'ice_rig': ice_rig(), 'comm_mast': comm_mast(), 'grow_lamp': grow_lamp(), 'pressure_tube': pressure_tube(), 'pressure_tube_dock': pressure_tube(78, dock=True), 'hab_hub': hab_hub(),
            'airlock_module': airlock_module(), 'glass_dome': glass_dome()}


# The station's white shells lose Eastward's tone count when cut to the house colour
# budget (house-style.md: "white shells need more parts in accent families"), so until
# the house kit's station modules land they keep their colours; everything else is held
# to the budget (rd.limit_colours).
OVER_BUDGET = {'hab_hub', 'airlock', 'airlock_module', 'pressure_tube', 'pressure_tube_dock', 'galley_table'}


def props() -> dict[str, Canvas]:
    return {k: v if k in OVER_BUDGET else rd.limit_colours(v) for k, v in {**props_station(), **props_lumen()}.items()}


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
