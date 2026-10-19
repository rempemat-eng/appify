"""Props for Neon Harbour, the rainy city at permanent dusk (world-atlas.md).

The valley's rules still hold (steep top-down roofs, light from the upper left,
material shading, an outline), but the light is night light: surfaces sit low on the
`night` ramp and the neon ramps carry the glow. Signs use abstract glyphs, never real
words or brands. Run directly for a contact sheet: python3 scripts/art/cyber_props.py
"""
from __future__ import annotations

import functools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, STONE, WOOD  # noqa: E402

NIGHT, PINK, CYAN, AMBER = (MATERIALS[k] for k in ('night', 'neon_pink', 'neon_cyan', 'neon_amber'))
IRON = MATERIALS['iron']
PAD = 4


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def glow(cv: Canvas, pts, ramp, r: int = 2):
    """A soft halo round neon tubes: the pixels near a tube step toward its colour."""
    pts = set(pts)
    for (x, y) in pts:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                q = (x + dx, y + dy)
                if q in pts or dx * dx + dy * dy > r * r:
                    continue
                c = cv.get(*q)
                if c[3]:
                    t = ramp[1] if dx * dx + dy * dy > 2 else ramp[2]
                    rgb = tuple(int(t[k:k + 2], 16) for k in (1, 3, 5))
                    cv.set(q[0], q[1], tuple((c[i] + rgb[i]) // 2 for i in range(3)) + (255,))


def glyph(cv: Canvas, x: int, y: int, seed: int, ramp, size: int = 5):
    """An abstract sign glyph: a few strokes on a 5 x 5 grid (never real lettering)."""
    pts = set()
    strokes = [((0, 0), (4, 0)), ((2, 0), (2, 4)), ((0, 2), (4, 2)), ((0, 4), (4, 4)), ((0, 0), (0, 4)),
               ((4, 0), (4, 4)), ((0, 0), (4, 4)), ((1, 1), (3, 1)), ((1, 3), (3, 3))]
    for k in range(3):
        (a, b), (c, d) = strokes[int(noise2(seed, k, 171) * len(strokes))]
        n = max(abs(c - a), abs(d - b)) + 1
        for t in range(n):
            px = a + round((c - a) * t / max(1, n - 1))
            py = b + round((d - b) * t / max(1, n - 1))
            pts.add((x + px * size // 5, y + py * size // 5))
    for (px, py) in pts:
        cv.set(px, py, ramp[3])
    return pts


def tower(width: int = 112, height: int = 150, seed: int = 0, sign=PINK) -> Canvas:
    """A tower block's lower floors seen steeply from above: a flat roof with vents and
    a water tank, a concrete facade with rows of windows (some lit warm, some blue
    with screens, some dark), air-conditioner boxes, a vertical neon sign, a fire
    escape and a lit shopfront at street level."""
    w, h = width, height
    cv = Canvas(w, h, pad=PAD)
    roof_h = 24
    for y in range(2, roof_h):  # the flat roof, seen from above
        for x in range(2, w - 2):
            n = noise2(x // 3, y // 3, 172 + seed)
            cv.set(x, y, NIGHT[3] if n > 0.5 else NIGHT[2])
    cv.hline(2, 2, w - 4, NIGHT[4]); cv.hline(2, roof_h - 1, w - 4, NIGHT[1])
    for (vx, vy) in ((10, 8), (w - 30, 6)):  # vents and a water tank
        for (x, y) in rect_set(vx, vy, 12, 8):
            cv.set(x, y, IRON[3] if y == vy else IRON[2] if x < vx + 6 else IRON[1])
    for (x, y) in oval(w // 2, 11, 9, 6):
        cv.set(x, y, NIGHT[4] if x < w // 2 else NIGHT[3])
    for (x, y) in oval(w // 2, 9, 6, 3):
        cv.set(x, y, NIGHT[5])
    # the facade
    fy0, fy1 = roof_h, h - 30
    for y in range(fy0, fy1):
        for x in range(2, w - 2):
            cv.set(x, y, NIGHT[2] if x > 5 else NIGHT[3])
    for x in range(2, w - 2):
        cv.set(x, fy0, NIGHT[1])
    for fl, y in enumerate(range(fy0 + 6, fy1 - 10, 16)):
        cv.hline(2, y + 12, w - 4, NIGHT[3])  # a floor ledge, lit on top
        for i, x in enumerate(range(10, w - 16, 18)):
            n = noise2(fl, i, 173 + seed)
            lit = AMBER if n > 0.62 else CYAN if n > 0.42 else None
            for (px, py) in rect_set(x, y, 11, 8):
                if lit:
                    cv.set(px, py, lit[3] if py < y + 3 else lit[2])
                else:
                    cv.set(px, py, NIGHT[0] if py > y + 1 else NIGHT[1])
            cv.hline(x, y - 1, 11, NIGHT[4])
            if noise2(fl, i, 174 + seed) > 0.6:  # an air conditioner box under the window
                for (px, py) in rect_set(x + 2, y + 9, 7, 3):
                    cv.set(px, py, STONE[3] if py == y + 9 else STONE[2])
                cv.set(x + 5, y + 10, STONE[1])
    # the fire escape down the left side
    for y in range(fy0 + 4, fy1 - 4):
        cv.set(8, y, IRON[3]); cv.set(9, y, IRON[1])
        if (y - fy0) % 16 == 2:
            cv.hline(4, y, 10, IRON[3]); cv.hline(4, y + 1, 10, IRON[1])
    # the vertical neon sign
    sx = w - 15
    tube = set()
    for y in range(fy0 + 8, fy1 - 6):
        for x in range(sx, sx + 9):
            cv.set(x, y, NIGHT[0])
    for k, y in enumerate(range(fy0 + 11, fy1 - 12, 9)):
        tube |= glyph(cv, sx + 2, y, seed * 10 + k, sign)
    frame = {(x, y) for x in range(sx, sx + 9) for y in (fy0 + 8, fy1 - 7)} | {(x, y) for y in range(fy0 + 8, fy1 - 6) for x in (sx, sx + 8)}
    for (x, y) in frame:
        cv.set(x, y, sign[2])
    glow(cv, tube | frame, sign)
    # the shopfront at street level
    sy = fy1
    for y in range(sy, h - 4):
        for x in range(2, w - 2):
            cv.set(x, y, NIGHT[1])
    awn = sign if seed % 2 == 0 else CYAN
    for x in range(2, w - 2):
        cv.set(x, sy, awn[3]); cv.set(x, sy + 1, awn[2]); cv.set(x, sy + 2, awn[1])
    for (x, y) in rect_set(12, sy + 6, w - 40, 14):
        cv.set(x, y, AMBER[3] if y < sy + 10 else AMBER[2])
    for x in range(12, w - 28, 6):
        cv.vline(x, sy + 6, 14, NIGHT[1])
    for (x, y) in rect_set(w - 26, sy + 5, 12, 21):  # a door, a strip of light under it
        cv.set(x, y, NIGHT[0])
    cv.hline(w - 26, sy + 25, 12, AMBER[3])
    detail.stones(cv, 2, h - 4, w - 4, 4, NIGHT, seed=seed, course=2)
    return cv


def noodle_stall() -> Canvas:
    """A street food stall, 72 x 58: a striped awning seen from above with paper
    lanterns, a steaming pot and a counter lit from inside."""
    w, h = 72, 58
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 22):  # the awning
        for x in range(2, w - 2):
            stripe = (x // 7) % 2
            c = (PINK[2] if stripe else NIGHT[4]) if y < 18 else (PINK[1] if stripe else NIGHT[3])
            if y == 4:
                c = PINK[3] if stripe else NIGHT[5]
            cv.set(x, y, c)
    for x in range(2, w - 2):
        cv.set(x, 22 + (1 if (x // 3) % 2 else 0), PINK[1] if (x // 7) % 2 else NIGHT[2])
    for lx in (10, 36, 62):  # paper lanterns
        for (x, y) in oval(lx, 28, 3.5, 4.5):
            cv.set(x, y, AMBER[3] if y < 28 else AMBER[2])
        cv.hline(lx - 2, 23, 5, NIGHT[1])
    for y in range(26, h - 4):  # the counter
        for x in range(4, w - 4):
            cv.set(x, y, WOOD[2] if y > 34 else AMBER[2] if y > 28 else AMBER[3])
    cv.hline(4, 34, w - 8, WOOD[4]); cv.hline(4, 35, w - 8, WOOD[3])
    detail.boards(cv, rect_set(4, 36, w - 8, h - 40), WOOD, 2, 36, board=5, vertical=True, x0=4)
    for (x, y) in oval(52, 32, 7, 3):  # the pot
        cv.set(x, y, IRON[3] if x < 52 else IRON[1])
    for (x, y) in oval(52, 31, 5, 1.6):
        cv.set(x, y, AMBER[4])
    for i, (bx, by) in enumerate(((50, 24), (54, 20), (51, 16))):
        for (x, y) in disc(bx, by, 2.2 - i * 0.4):
            cv.set(x, y, '#D9DCE8' if x < bx else '#A9ADC0')
    return cv


def vending_machine() -> Canvas:
    """A glowing vending machine, 22 x 40: a lit panel of drinks, a coin slot and a tray."""
    cv = Canvas(22, 40, pad=PAD)
    for y in range(2, 38):
        for x in range(1, 21):
            cv.set(x, y, NIGHT[3] if x < 4 else NIGHT[2])
    cv.hline(1, 2, 20, NIGHT[5])
    for (x, y) in rect_set(4, 6, 12, 20):
        cv.set(x, y, CYAN[3] if y < 9 else CYAN[2])
    for row in range(3):
        for col in range(3):
            c = (PINK, AMBER, CYAN)[(row + col) % 3]
            cv.rect(5 + col * 4, 10 + row * 5, 2, 3, c[3])
            cv.set(5 + col * 4, 10 + row * 5, c[4])
    cv.rect(17, 12, 2, 4, NIGHT[0]); cv.set(17, 18, AMBER[3])
    cv.rect(5, 29, 10, 4, NIGHT[0]); cv.hline(5, 29, 10, NIGHT[1])
    glow(cv, rect_set(4, 6, 12, 20), CYAN, r=1)
    return cv


def street_light() -> Canvas:
    """A city street light, 20 x 56: a slim pole and a long head with a cool LED strip."""
    cv = Canvas(20, 56, pad=PAD)
    for y in range(6, 54):
        cv.set(4, y, IRON[3]); cv.set(5, y, IRON[2]); cv.set(6, y, IRON[1])
    cv.rect(2, 52, 7, 3, IRON[2])
    cv.rect(4, 3, 14, 4, IRON[3]); cv.hline(4, 3, 14, IRON[4])
    cv.hline(7, 7, 10, CYAN[4]); cv.hline(7, 8, 10, CYAN[3])
    return cv


def holo_board() -> Canvas:
    """A holographic billboard on a pole, 44 x 52: a cyan frame, a soft pink shape inside."""
    cv = Canvas(44, 52, pad=PAD)
    for y in range(30, 50):
        cv.set(21, y, IRON[3]); cv.set(22, y, IRON[1])
    for (x, y) in rect_set(2, 2, 40, 28):
        cv.set(x, y, CYAN[1] if (y // 2) % 2 else CYAN[0])
    frame = {(x, y) for x in range(2, 42) for y in (2, 29)} | {(x, y) for y in range(2, 30) for x in (2, 41)}
    for (x, y) in frame:
        cv.set(x, y, CYAN[3])
    for (x, y) in disc(16, 15, 7):
        cv.set(x, y, PINK[3] if (x + y) % 3 else PINK[2])
    for k in range(3):
        cv.hline(26, 10 + k * 5, 12 - k * 3, CYAN[4])
    glow(cv, frame, CYAN, r=2)
    return cv


def drone() -> Canvas:
    """A small delivery drone, 18 x 10, with a red tail light."""
    cv = Canvas(18, 10, pad=PAD)
    for (x, y) in oval(9, 5, 4, 2.5):
        cv.set(x, y, NIGHT[4] if y < 5 else NIGHT[2])
    for rx in (2, 15):
        cv.hline(rx - 2, 2, 5, NIGHT[5]); cv.set(rx, 3, IRON[3])
    cv.set(13, 5, PINK[4])
    return cv


def cable_pole() -> Canvas:
    """A wooden utility pole with a transformer and cables, 26 x 70."""
    cv = Canvas(26, 70, pad=PAD)
    gp.post(cv, 11, 6, 68, w=4, ramp=WOOD)
    cv.hline(2, 10, 22, WOOD[2]); cv.hline(2, 9, 22, WOOD[3])
    for (x, y) in rect_set(14, 20, 8, 10):
        cv.set(x, y, IRON[3] if x < 17 else IRON[2])
    for x in (3, 22):
        cv.set(x, 8, STONE[4])
    return cv


def shelter() -> Canvas:
    """A tram shelter, 56 x 44: a glass roof seen from above with rain beading on it,
    a lit ad panel at one end, a slim bench and a neon route stripe."""
    w, h = 56, 44
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 16):  # the glass roof
        for x in range(2, w - 2):
            cv.set(x, y, '#3A4A6A' if (x + y) % 7 else '#5A6E92')
    cv.hline(2, 4, w - 4, '#8FA6CC'); cv.hline(2, 16, w - 4, NIGHT[1])
    for k in range(14):
        cv.set(4 + int(noise2(k, 0, 175) * (w - 8)), 6 + int(noise2(k, 1, 175) * 8), '#C9DAF2')
    for px in (4, w - 7):
        for y in range(16, h - 2):
            cv.set(px, y, IRON[3]); cv.set(px + 1, y, IRON[2]); cv.set(px + 2, y, IRON[1])
    for (x, y) in rect_set(w - 20, 18, 12, 20):
        cv.set(x, y, PINK[2] if y < 26 else CYAN[2])
    glow(cv, rect_set(w - 20, 18, 12, 20), PINK, r=1)
    cv.hline(8, 32, w - 30, WOOD[3]); cv.hline(8, 33, w - 30, WOOD[1])
    cv.hline(2, 17, w - 4, CYAN[3])
    return cv


def uv_planter() -> Canvas:
    """A concrete planter with a bonsai-like shrub under a violet grow light, 26 x 30."""
    cv = Canvas(26, 30, pad=PAD)
    for (x, y) in rect_set(2, 20, 22, 9):
        cv.set(x, y, NIGHT[4] if y == 20 else NIGHT[3] if x < 6 else NIGHT[2])
    for (x, y) in oval(13, 13, 9, 6):
        n = noise2(x, y, 176)
        cv.set(x, y, '#3E7A5A' if (x - 13) + (y - 13) < -2 else '#2A5A44' if n > 0.3 else '#1E4434')
    cv.vline(13, 17, 4, WOOD[1])
    cv.hline(6, 3, 14, IRON[3]); cv.hline(7, 4, 12, '#B07CF0')
    for (x, y) in oval(13, 12, 10, 6):
        c = cv.get(x, y)
        if c[3] and (x + y) % 2:
            cv.set(x, y, tuple(min(255, (c[i] + (0x9A, 0x6A, 0xE0)[i]) // 2) for i in range(3)) + (255,))
    return cv


def containers() -> Canvas:
    """Two stacked shipping containers, 64 x 50, corrugated, one rust red, one teal,
    with stencilled marks and a lit top."""
    w, h = 64, 50
    cv = Canvas(w, h, pad=PAD)
    for (y0, ramp) in ((22, ['#3A1A16', '#5E2A22', '#80402E', '#A05A3E', '#C27A56']),
                       (2, ['#0E3036', '#16525A', '#21757C', '#3A9AA0', '#6CC2C4'])):
        for y in range(y0, y0 + 24):
            for x in range(2, w - 2):
                c = ramp[2] if (x // 3) % 2 else ramp[1]
                if y == y0:
                    c = ramp[4]
                elif y < y0 + 3:
                    c = ramp[3]
                elif y == y0 + 23:
                    c = ramp[0]
                cv.set(x, y, c)
        cv.vline(2, y0, 24, ramp[3]); cv.vline(w - 3, y0, 24, ramp[0])
        cv.rect(10, y0 + 9, 14, 4, '#E8E2D0')
    return cv


def ferry() -> Canvas:
    """A small harbour ferry moored at the quay, 112 x 46: a dark hull, a cabin with a
    strip of screen-blue windows, a neon line along its rail and a red mast light."""
    w, h = 112, 46
    cv = Canvas(w, h, pad=PAD)
    hull = oval(56, 30, 52, 13)
    for (x, y) in hull:
        cv.set(x, y, NIGHT[3] if y < 24 else NIGHT[2] if y < 34 else NIGHT[1])
    for (x, y) in hull:
        if (x, y - 1) not in hull:
            cv.set(x, y, NIGHT[5])
    for x in range(10, w - 10):
        if (x, 25) in hull:
            cv.set(x, 25, CYAN[3])
    for (x, y) in rect_set(30, 8, 46, 16):
        cv.set(x, y, NIGHT[4] if y < 11 else NIGHT[3])
    cv.hline(30, 8, 46, NIGHT[5])
    for x in range(34, 72, 6):
        for (px, py) in rect_set(x, 14, 4, 5):
            cv.set(px, py, CYAN[3] if py < 16 else CYAN[2])
    for y in range(0, 9):
        cv.set(70, y, IRON[3])
    cv.set(70, 0, PINK[4]); cv.set(69, 1, PINK[2]); cv.set(71, 1, PINK[2])
    glow(cv, {(x, 25) for x in range(10, w - 10) if (x, 25) in hull}, CYAN, r=1)
    return cv


PORCELAIN = ['#3A4258', '#5C6680', '#8A94AC', '#B8C0D2', '#DCE2EC', '#F4F7FB']  # the skyport's clean white


def maglev() -> Canvas:
    """A maglev train on its guideway, 132 x 34, side on: a long pale body with a
    tapered nose at the east end, a band of lit windows with passengers' shapes, a
    cyan strip along the skirt and the faint blue of the levitation gap beneath."""
    w, h = 132, 34
    cv = Canvas(w, h, pad=PAD)
    for x in range(2, w - 2):
        nose = max(0, x - (w - 30))
        top = 6 + nose * nose // 60
        for y in range(top, 26):
            c = PORCELAIN[5] if y < top + 2 else PORCELAIN[4] if y < 15 else PORCELAIN[3] if y < 22 else PORCELAIN[2]
            if x < 4:
                c = PORCELAIN[2]
            cv.set(x, y, c)
        if top < 11:
            for y in range(11, 16):  # the window band
                win = (x - 6) % 14 < 11 and x < w - 30
                c = NIGHT[1] if not win else AMBER[3] if y < 13 else AMBER[2]
                if win and (x - 6) % 14 in (4, 5) and y >= 13 and (x // 14) % 2:
                    c = NIGHT[2]  # someone reading by the window
                cv.set(x, y, c)
        if x > w - 30 and 11 <= top + 6 < 20:
            cv.set(x, top + 5, NIGHT[1])  # the cab's windscreen line
        cv.set(x, 22, CYAN[3]); cv.set(x, 23, CYAN[2])
        if x % 22 == 0:
            cv.vline(x, 8, 18, PORCELAIN[2])  # doors
    for x in range(4, w - 6):  # the levitation gap and the guideway's top
        cv.set(x, 27, CYAN[1] if x % 3 else CYAN[2])
        cv.set(x, 28, PORCELAIN[1])
    return cv


def tether() -> Canvas:
    """The space elevator's lift, 56 x 272, standing on its anchor ring (fault 25): a
    climber car docked in its cradle at the foot, door open toward the boarding ramp,
    gripping the ribbon with a wheel housing on its roof; the ribbon (two pale strands
    tied every few pixels, a cyan guide light between) climbs out of its roof and out
    of sight, narrowing and breaking into dashes as it goes; a second car far up, small,
    its own grip on the ribbon. No glow: the light is in the guide line and the windows."""
    w, h = 56, 272
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    car_top, car_bot = h - 58, h - 14
    # the ribbon, from the top of the sprite down into the roof housing
    for y in range(0, car_top - 6):
        t = y / (car_top - 6)  # 0 far up, 1 at the car
        half = 1 if t < 0.25 else 2 if t < 0.6 else 3
        if t < 0.25 and y % 5 in (3, 4):
            continue  # far up it breaks into dashes, out of sight
        if 0.25 <= t < 0.4 and y % 9 == 8:
            continue
        cv.set(cx - half, y, PORCELAIN[5] if half > 1 else PORCELAIN[4])
        cv.set(cx + half, y, PORCELAIN[2])
        for dx in range(-half + 1, half):
            cv.set(cx + dx, y, CYAN[4] if dx == 0 else CYAN[2])
        if half == 3 and y % 6 == 0:
            cv.hline(cx - 3, y, 7, PORCELAIN[3])  # ties between the strands
    # a second car far up the ribbon, small, with its grips
    uy = int((car_top - 6) * 0.3)
    for y in range(uy, uy + 12):
        for x in range(cx - 5, cx + 6):
            c = PORCELAIN[5] if x < cx - 1 else PORCELAIN[3] if x < cx + 3 else PORCELAIN[1]
            if y in (uy + 5, uy + 6) and cx - 4 <= x <= cx + 4:
                c = AMBER[3] if x % 2 else AMBER[2]
            cv.set(x, y, c)
    for y in (uy - 2, uy + 13):
        cv.hline(cx - 3, y, 7, NIGHT[1]); cv.set(cx - 3, y, PORCELAIN[3]); cv.set(cx + 3, y, PORCELAIN[3])
    # the roof housing: the grip, two wheels pressing each strand
    for y in range(car_top - 7, car_top + 1):
        for x in range(cx - 8, cx + 9):
            c = NIGHT[2] if y > car_top - 6 else PORCELAIN[3]
            if x <= cx - 7:
                c = PORCELAIN[4]
            elif x >= cx + 7:
                c = PORCELAIN[1]
            cv.set(x, y, c)
    for wx in (cx - 5, cx + 4):
        for (x, y) in disc(wx, car_top - 3, 1.6):
            cv.set(x, y, PORCELAIN[2] if x <= wx else NIGHT[3])
        cv.set(wx, car_top - 3, CYAN[3])
    # the car: a rounded capsule, lit on its upper left, a band of windows, its door open
    for y in range(car_top, car_bot):
        ry = (y - car_top) / (car_bot - car_top)
        inset = int(6 * (1 - min(ry / 0.25, 1)) ** 2) + int(3 * max(0, (ry - 0.85) / 0.15) ** 2)
        for x in range(cx - 17 + inset, cx + 18 - inset):
            k = (x - (cx - 17)) / 34
            c = PORCELAIN[5] if k < 0.22 and ry < 0.7 else PORCELAIN[4] if k < 0.55 else PORCELAIN[3] if k < 0.82 else PORCELAIN[1]
            if ry < 0.12:
                c = PORCELAIN[5] if k < 0.6 else PORCELAIN[3]
            cv.set(x, y, c)
    wy = car_top + 12
    for x in range(cx - 14, cx + 15):  # the window band, mullions every 5
        for y in range(wy, wy + 6):
            cv.set(x, y, NIGHT[1] if (x - cx) % 5 == 0 else AMBER[3] if y < wy + 2 else AMBER[2])
    cv.hline(cx - 15, wy - 1, 31, PORCELAIN[2])
    cv.hline(cx - 15, wy + 6, 31, PORCELAIN[5])
    dx0, dy0 = cx - 5, car_top + 22  # the door, slid open: lit inside, a seat back
    for y in range(dy0, car_bot - 2):
        for x in range(dx0, dx0 + 10):
            cv.set(x, y, '#E8C890' if y < dy0 + 4 else '#B88E62' if x < dx0 + 8 else '#7A5A44')
    cv.hline(dx0 + 2, dy0 + 8, 6, '#5C6680'); cv.hline(dx0 + 2, dy0 + 9, 6, '#3A4258')
    for y in range(dy0, car_bot - 2):
        cv.set(dx0 - 1, y, PORCELAIN[5]); cv.set(dx0 + 10, y, PORCELAIN[1])
    cv.hline(cx - 12, car_top + 28, 5, CYAN[3]); cv.hline(cx + 8, car_top + 28, 5, CYAN[3])  # the running lights
    # the cradle: four arms out to a ring of clamps on the deck, the boarding ramp
    for (ax, side) in ((cx - 18, -1), (cx + 18, 1)):
        for y in range(car_bot - 16, car_bot + 2):
            for x in range(ax - (2 if side < 0 else 0), ax + (1 if side < 0 else 3)):
                cv.set(x, y, PORCELAIN[4] if side < 0 else PORCELAIN[1])
        cv.set(ax, car_bot - 16, PORCELAIN[5])
    for y in range(car_bot - 2, car_bot + 8):  # the ramp, its edges lit cyan
        for x in range(dx0 - 1, dx0 + 11):
            c = PORCELAIN[3] if (y - car_bot) % 3 else PORCELAIN[2]
            if x in (dx0 - 1, dx0 + 10):
                c = CYAN[3]
            cv.set(x, y, c)
    return cv


def ticket_gates() -> Canvas:
    """A bank of ticket gates across the pier's entry, 82 x 30 (fault 24): six cabinets
    seen in the three-quarter view, each a long top (a lit reader at the near end, a
    small screen) over a front face with a status light and a kick plate; between them
    the glass paddles stand folded back, so the five lanes are open."""
    w, h = 82, 30
    cv = Canvas(w, h, pad=PAD)
    for k in range(6):
        x0 = 1 + k * 15
        for y in range(5, 18):  # the top, long because it runs away from us
            for x in range(x0, x0 + 6):
                c = PORCELAIN[5] if x == x0 or y == 5 else PORCELAIN[4] if x < x0 + 4 else PORCELAIN[3]
                cv.set(x, y, c)
        cv.rect(x0 + 1, 7, 4, 2, CYAN[3]); cv.hline(x0 + 1, 9, 4, CYAN[1])  # the reader
        cv.rect(x0 + 1, 12, 4, 3, NIGHT[1]); cv.hline(x0 + 2, 13, 2, AMBER[3])  # the screen
        for y in range(18, 28):  # the front face, in shade
            for x in range(x0, x0 + 6):
                c = PORCELAIN[2] if x < x0 + 4 else PORCELAIN[1]
                if y == 20:
                    c = CYAN[3] if k % 2 == 0 else CYAN[2]
                if y >= 26:
                    c = NIGHT[2]
                cv.set(x, y, c)
        if k < 5:  # the paddles, folded back against each side of the lane
            for y in range(10, 22):
                cv.set(x0 + 6, y, (164, 220, 236, 150) if y < 20 else PORCELAIN[1])
                cv.set(x0 + 14, y, (164, 220, 236, 150) if y < 20 else PORCELAIN[1])
            cv.set(x0 + 6, 10, PORCELAIN[5]); cv.set(x0 + 14, 10, PORCELAIN[5])
    return cv


def glass_screen() -> Canvas:
    """A glass screen, 24 x 26, that closes the pier's entry either side of the gates: a
    chrome top rail on three posts, the glass between catching two pale glints."""
    w, h = 24, 26
    cv = Canvas(w, h, pad=PAD)
    for y in range(6, 23):
        for x in range(1, w - 1):
            cv.set(x, y, (150, 206, 226, 110))
    for k, x in enumerate(range(5, w - 3, 7)):  # glints, slanting with the light
        for d in range(5):
            cv.set(x + d, 18 - d * 2, (240, 250, 255, 200)); cv.set(x + d, 17 - d * 2, (240, 250, 255, 200))
    cv.hline(0, 5, w, PORCELAIN[5]); cv.hline(0, 6, w, PORCELAIN[3])
    cv.hline(0, 23, w, PORCELAIN[2]); cv.hline(0, 24, w, PORCELAIN[0])
    for x in (0, w // 2 - 1, w - 2):
        for y in range(5, 25):
            cv.set(x, y, PORCELAIN[4]); cv.set(x + 1, y, PORCELAIN[2])
    return cv


def holo_map() -> Canvas:
    """A wayfinding table, 40 x 40 (fault 24): a low round porcelain plinth with a dark
    glass top, and over it a small crisp hologram of the planet with the ribbon rising
    from it and a climber on the ribbon, drawn in whole cyan lines with a scan gap."""
    w, h = 40, 40
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(26, 38):  # the plinth: a short drum seen from above and in front
        for x in range(cx - 13, cx + 14):
            if ((x - cx) / 13.5) ** 2 + ((y - 29) / 4) ** 2 <= 1:
                cv.set(x, y, NIGHT[1] if ((x - cx) / 11) ** 2 + ((y - 29) / 3) ** 2 <= 1 else PORCELAIN[5] if x < cx else PORCELAIN[3])
            elif y > 29 and abs(x - cx) <= 13 - max(0, y - 35):
                cv.set(x, y, PORCELAIN[4] if x < cx - 6 else PORCELAIN[2] if x < cx + 7 else PORCELAIN[1])
    cv.hline(cx - 12, 34, 25, CYAN[2])
    for x in range(cx - 8, cx + 9):  # the emitter ring on the glass
        cv.set(x, 29 + (1 if abs(x - cx) < 6 else 0), CYAN[3])
    gy = 16  # the planet: a circle of lines, a latitude band, the night side broken
    for a in range(0, 360, 6):
        r = math.radians(a)
        x, y = cx + round(8 * math.cos(r)), gy + round(7 * math.sin(r))
        if a < 200 or a % 12 == 0:
            cv.set(x, y, CYAN[4] if 100 < a < 260 else CYAN[3])
    for x in range(cx - 7, cx + 8):
        if x % 2 or x < cx:
            cv.set(x, gy + 1, CYAN[2])
    for y in range(gy - 6, gy + 7):
        cv.set(cx - 3 + abs(y - gy) // 3, y, CYAN[2] if y % 2 else CYAN[1])
    for y in range(0, gy - 6):  # the ribbon from the planet, a climber on it
        cv.set(cx + 4, y, CYAN[4] if y % 4 else CYAN[2])
    cv.rect(cx + 3, 4, 3, 3, CYAN[4])
    for y in range(gy + 8, 28, 2):  # the beam down to the glass, in scan lines
        cv.hline(cx - 2, y, 5, CYAN[1])
    return cv


def departure_pylon() -> Canvas:
    """A departures pylon, 26 x 56: a tall slim board listing the climbers in amber
    glyph rows (no real words), the next one blinking cyan."""
    w, h = 26, 56
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, h - 2):
        for x in range(3, w - 3):
            c = NIGHT[1]
            if x in (3, 4) or y in (2, 3):
                c = PORCELAIN[4]
            elif x >= w - 5 or y >= h - 6:
                c = PORCELAIN[2]
            cv.set(x, y, c)
    for row in range(8):
        y = 7 + row * 5
        for x in range(7, w - 7):
            if noise2(x // 2, row, 490) > 0.3 or x < 10:
                cv.set(x, y, CYAN[3] if row == 0 else AMBER[3] if x < 10 else AMBER[2])
    return cv


def luggage_bot() -> Canvas:
    """A little luggage robot, 16 x 18: a white rounded body with a suitcase on its back
    and one soft blue eye."""
    cv = Canvas(16, 18, pad=PAD)
    for (x, y) in oval(8, 11, 6, 5):
        cv.set(x, y, PORCELAIN[5] if x + y < 16 else PORCELAIN[3] if x < 11 else PORCELAIN[2])
    for y in range(1, 8):
        for x in range(3, 12):
            cv.set(x, y, AMBER[2] if x > 4 else AMBER[3])
    cv.hline(6, 0, 3, AMBER[1])
    cv.set(11, 11, CYAN[3]); cv.set(12, 11, CYAN[4])
    for x in (4, 12):
        cv.set(x, 16, NIGHT[1])
    return cv


def pod_tree() -> Canvas:
    """A calm little tree in a white pod planter, 36 x 46: a rounded crown of soft green
    leaves lit on the upper left, the only living green in the city."""
    w, h = 36, 46
    cv = Canvas(w, h, pad=PAD)
    G = ['#1E3A2E', '#2E5A40', '#447A50', '#62995E', '#8CBB76']
    for y in range(20, 34):
        cv.set(17, y, WOOD[2]); cv.set(18, y, WOOD[1])
    crown = oval(18, 16, 14, 12)
    for (x, y) in crown:
        k = (x - 4) / 28 + (y - 4) / 24
        n = noise2(x // 2, y // 2, 491)
        c = G[4] if k < 0.5 else G[3] if k < 0.9 else G[2] if k < 1.3 else G[1]
        if n > 0.8:
            c = G[max(0, G.index(c) - 1)]
        cv.set(x, y, c)
    for y in range(32, 44):
        for x in range(6, 30):
            r = abs(x - 18) / 12
            if r > 1 - max(0, y - 40) * 0.12:
                continue
            cv.set(x, y, PORCELAIN[5] if y < 34 else PORCELAIN[4] if x < 14 else PORCELAIN[3] if x < 25 else PORCELAIN[1])
    cv.hline(8, 33, 20, '#3A2A22')
    return cv


def sky_bench() -> Canvas:
    """A curved white bench, 44 x 14, with a soft cyan light under its seat."""
    w, h = 44, 14
    cv = Canvas(w, h, pad=PAD)
    for x in range(2, w - 2):
        sag = int(((x - w / 2) / (w / 2)) ** 2 * 3)
        for y in range(3 + sag, 9 + sag):
            cv.set(x, y, PORCELAIN[5] if y < 5 + sag else PORCELAIN[4] if y < 7 + sag else PORCELAIN[2])
        cv.set(x, 10 + sag, CYAN[2] if x % 2 else CYAN[1])
    return cv


def sky_planter(seed: int = 0) -> Canvas:
    """A long white planter bed, 64 x 24: soft feather grasses and a few low flowering
    clumps (style.leafy) spilling over a porcelain trough lit on its top edge."""
    import style
    w, h = 64, 24
    cv = Canvas(w, h, pad=PAD)
    G = ['#1E3A2E', '#2E5A40', '#447A50', '#62995E', '#8CBB76']
    for k in range(3):
        style.leafy(cv, 12 + k * 20 + int(noise2(k, seed, 494) * 4), 10, 10, 5, G, r=2.2, seed=seed + k)
    for k in range(9):  # feather grass blades over the clumps
        x = 5 + k * 6 + int(noise2(k, seed, 495) * 3)
        top = 1 + int(noise2(k, seed, 496) * 4)
        for y in range(top, 13):
            cv.set(x + (1 if y < top + 3 else 0), y, '#C8C89A' if y < top + 2 else G[3])
    for k in range(5):  # flowers
        x, y = 8 + int(noise2(k, seed, 497) * 48), 7 + int(noise2(k, seed, 498) * 5)
        if cv.get(x, y)[3]:
            col = ('#F2A0C8', '#F7F2E8', '#9A8BC8')[k % 3]
            cv.set(x, y, col); cv.set(x + 1, y, col)
    for y in range(13, h - 1):
        for x in range(2, w - 2):
            cv.set(x, y, PORCELAIN[5] if y == 13 else PORCELAIN[4] if y < 16 else PORCELAIN[3] if x < w - 8 else PORCELAIN[1])
    cv.hline(3, 14, w - 6, '#3A2A22')  # the soil line
    cv.hline(2, h - 2, w - 4, PORCELAIN[1])
    return cv


def flower_kiosk() -> Canvas:
    """A small flower kiosk under the guideway, 48 x 40: a curved white canopy with a
    cyan edge light, buckets of flowers on stepped shelves, and a warm lamp inside."""
    w, h = 48, 40
    cv = Canvas(w, h, pad=PAD)
    for y in range(4, 14):  # the canopy, seen from above and in front
        for x in range(2, w - 2):
            c = PORCELAIN[5] if y < 7 else PORCELAIN[4] if x < w - 10 else PORCELAIN[3]
            cv.set(x, y, c)
    for x in range(2, w - 2):
        cv.set(x, 14, CYAN[3] if x % 2 else CYAN[2])
    for y in range(15, h - 2):  # the back wall in warm lamplight
        for x in range(5, w - 5):
            cv.set(x, y, '#E8C890' if y < 20 and x < w - 12 else '#B88E62' if x < w - 12 else '#7A5A44')
    PETAL = ['#F2A0C8', '#E8D27A', '#F7F2E8', '#E86A5A', '#9A8BC8']
    for row, y in enumerate((22, 28)):  # stepped shelves of buckets
        cv.hline(5, y + 5, w - 10, PORCELAIN[2])
        for k in range(5):
            bx = 8 + k * 7 + row * 3
            cv.rect(bx, y + 2, 5, 3, PORCELAIN[3] if k % 2 else PORCELAIN[4])
            for (dx, dy) in ((0, 0), (2, -1), (4, 0), (1, 1), (3, 1)):
                cv.set(bx + dx, y + dy, PETAL[(k + row * 2 + dx) % 5])
            cv.set(bx + 1, y + 1, '#447A50'); cv.set(bx + 3, y, '#447A50')
    for y in range(15, h - 1):  # the posts
        cv.set(3, y, PORCELAIN[4]); cv.set(4, y, PORCELAIN[2])
        cv.set(w - 5, y, PORCELAIN[3]); cv.set(w - 4, y, PORCELAIN[1])
    cv.hline(3, h - 2, w - 6, PORCELAIN[1])
    return cv


def cables() -> Canvas:
    """Wires strung over the street, 300 x 150 (drawn above everything): sagging lines
    from the towers to the pole across the road, a string of small lanterns on one,
    and a sign hanging from another."""
    w, h = 300, 150
    cv = Canvas(w, h, pad=PAD)
    spans = [((10, 6), (152, 144), 22), ((120, 10), (290, 108), 18), ((40, 4), (290, 40), 26), ((152, 144), (290, 70), 10)]
    for k, ((x0, y0), (x1, y1), sag) in enumerate(spans):
        n = int(abs(x1 - x0)) + 1
        for i in range(n):
            t = i / (n - 1)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t + math.sin(t * math.pi) * sag
            cv.set(int(x), int(y), NIGHT[1] if k % 2 else '#0A0910')
            if k == 2 and i % 14 == 7:  # a string of lanterns
                ramp = (PINK, CYAN, AMBER)[(i // 14) % 3]
                for (px, py) in disc(int(x), int(y) + 3, 1.8):
                    cv.set(px, py, ramp[3] if px <= x else ramp[2])
    for y in range(52, 64):  # a hanging sign on the long span
        for x in range(196, 210):
            cv.set(x, y, NIGHT[2] if x in (196, 209) or y in (52, 63) else CYAN[1])
    glyph(cv, 199, 55, 5, CYAN, size=5)
    cv.vline(198, 46, 6, NIGHT[1]); cv.vline(207, 46, 6, NIGHT[1])
    return cv


def bike_rack() -> Canvas:
    """A rack of three e-bikes, 46 x 22, their little lights glowing."""
    w, h = 46, 22
    cv = Canvas(w, h, pad=PAD)
    for x in range(2, w - 2):
        cv.set(x, 18, IRON[3]); cv.set(x, 19, IRON[1])
    for k in range(3):
        bx = 6 + k * 13
        for (cx, cy) in ((bx, 14), (bx + 9, 14)):
            for a in range(16):
                ang = 2 * math.pi * a / 16
                cv.set(int(round(cx + math.cos(ang) * 3.5)), int(round(cy + math.sin(ang) * 3.5)), NIGHT[4])
        for t in range(9):
            cv.set(bx + t, 10 - (t > 3), (PINK, CYAN, AMBER)[k][2])
        cv.vline(bx + 7, 6, 4, NIGHT[4]); cv.hline(bx + 6, 6, 3, NIGHT[5])
        cv.set(bx + 9, 9, (PINK, CYAN, AMBER)[k][4])
    return cv

# ---- the city's buildings (N1): every one different, all from one generator ----------
GLASS = ['#0E1424', '#16203A', '#1E2E50', '#2A4068', '#3A5684', '#5A78A8']
CONCRETE = ['#1E1C2A', '#2C2A3C', '#3C3A50', '#4E4C64', '#64627C', '#807E96']
TILE_C = ['#2A1C24', '#3E2832', '#543844', '#6C4A56', '#8A6070', '#A87C8A']  # old glazed tile, mauve at dusk
METAL = ['#1A1E26', '#2A303C', '#3C4452', '#56606E', '#76808E', '#A0A8B4']
WARM_W = ['#4A2A08', '#9A5A10', '#E8962A', '#FFC766', '#FFE9B0']  # lamplit rooms
COOL_W = ['#0C2A3A', '#11506A', '#1F8AA8', '#6FD0E6', '#C8F4FF']  # screens and offices
SIGN_RAMPS = (PINK, CYAN, AMBER)


def _shade(c, k: int):
    """A colour stepped toward black (k > 0) or white (k < 0) by about a twelfth a step."""
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5)) if isinstance(c, str) else c[:3]
    f = 1 - 0.09 * k
    if k < 0:
        return '#%02X%02X%02X' % tuple(min(255, int(v + (255 - v) * 0.09 * -k)) for v in (r, g, b))
    return '#%02X%02X%02X' % tuple(max(0, int(v * f)) for v in (r, g, b))


def _rooftop(cv: Canvas, x0: int, x1: int, y0: int, y1: int, seed: int, tall: bool, ramp):
    """A flat roof seen from above: a parapet lit along its front and west edges, the
    membrane darker toward the back, and the things that live on roofs, each with its
    lit top and its shadow down and to the right: a water tank on legs, air-conditioner
    units with their fans, a stair bulkhead with its door facing us, vent stacks, solar
    panels, planters, and on the tallest an antenna with a red light or a helipad."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            n = noise2(x // 3, y // 2, 1900 + seed)
            back = (y - y0) / max(1, y1 - y0)
            c = ramp[2] if n > 0.45 else ramp[1]
            if back < 0.2:
                c = ramp[1]
            cv.set(x, y, c)
    for x in range(x0, x1):  # the parapet: its top lit, its inner face in shade
        cv.set(x, y1 - 1, ramp[4]); cv.set(x, y1 - 2, ramp[3]); cv.set(x, y0, ramp[3])
    for y in range(y0, y1):
        cv.set(x0, y, ramp[4]); cv.set(x1 - 1, y, ramp[2])
    things = []
    W_ = x1 - x0
    r = noise2(seed, 1, 1901)
    if W_ > 40:
        things.append(('tank', x0 + 6 + int(r * (W_ - 26)), y0 + 2))
    things.append(('ac', x0 + 4 + int(noise2(seed, 2, 1901) * max(1, W_ - 20)), y1 - 9))
    if W_ > 56:
        things.append(('ac', x0 + 4 + int(noise2(seed, 3, 1901) * max(1, W_ - 20)), y1 - 9))
        things.append(('bulkhead', x1 - 18 - int(noise2(seed, 4, 1901) * 10), y0 + 3))
    if noise2(seed, 5, 1901) > 0.5:
        things.append(('solar', x0 + 4, y0 + 2))
    elif noise2(seed, 6, 1901) > 0.4:
        things.append(('garden', x0 + 3, y1 - 8))
    if tall:
        things.append(('antenna', x0 + W_ // 3 + int(noise2(seed, 7, 1901) * W_ // 3), y0 + 1))
    taken = []
    for (kind, tx, ty) in things:
        box = {'tank': (16, 14), 'ac': (12, 6), 'bulkhead': (14, 10), 'solar': (22, 8), 'garden': (20, 5),
               'antenna': (3, 3)}[kind]
        if any(tx < a + c and tx + box[0] > a and ty < b + d and ty + box[1] > b for (a, b, c, d) in taken):
            continue
        if tx + box[0] > x1 - 2:
            continue
        taken.append((tx, ty, box[0], box[1]))
        if kind == 'tank':  # a timber water tank on a steel stand, its conical lid
            for y in range(ty + 4, ty + 12):
                for x in range(tx + 2, tx + 14):
                    c = WOOD[3] if x < tx + 5 else WOOD[2] if x < tx + 11 else WOOD[1]
                    if (y - ty) % 3 == 0:
                        c = IRON[1]  # the hoops
                    cv.set(x, y, c)
            for k in range(5):
                cv.hline(tx + 2 + k, ty + 4 - k, 12 - 2 * k, IRON[3] if k < 2 else IRON[4])
            for lx in (tx + 3, tx + 12):
                cv.vline(lx, ty + 12, 3, IRON[2])
            for x in range(tx + 4, tx + 17):
                cv.set(x, ty + 15, ramp[0])  # its shadow
        elif kind == 'ac':  # an air-conditioner unit: a lit lid and a fan
            for y in range(ty, ty + 6):
                for x in range(tx, tx + 12):
                    cv.set(x, y, METAL[4] if y == ty else METAL[3] if x < tx + 9 else METAL[2])
            for (x, y) in disc(tx + 4, ty + 3, 2):
                cv.set(x, y, METAL[1])
            cv.set(tx + 4, ty + 3, METAL[3])
            cv.hline(tx + 1, ty + 6, 12, ramp[0])
        elif kind == 'bulkhead':  # the stair's head-house, a door toward us
            for y in range(ty, ty + 10):
                for x in range(tx, tx + 14):
                    c = ramp[4] if y < ty + 3 else ramp[3] if x < tx + 10 else ramp[2]
                    if y < ty + 3 and x >= tx + 10:
                        c = ramp[3]
                    cv.set(x, y, c)
            for y in range(ty + 4, ty + 10):
                for x in range(tx + 4, tx + 9):
                    cv.set(x, y, METAL[1])
            cv.set(tx + 7, ty + 7, AMBER[3])
            cv.vline(tx + 14, ty + 1, 10, ramp[0])
        elif kind == 'solar':
            for y in range(ty, ty + 8):
                for x in range(tx, tx + 22):
                    c = '#1E3A6A' if (x - tx) % 5 and (y - ty) % 4 else METAL[3]
                    if (x - tx) % 5 == 1 and (y - ty) % 4 == 1:
                        c = '#4A70A8'
                    cv.set(x, y, c)
        elif kind == 'garden':
            for x in range(tx, tx + 20):
                for y in range(ty, ty + 5):
                    c = WOOD[2] if y >= ty + 3 else '#2E5A40' if (x + y) % 3 else '#4A8A5A'
                    cv.set(x, y, c)
        elif kind == 'antenna':
            top = max(0, ty - 18)
            for y in range(top, ty + 3):
                cv.set(tx, y, METAL[4]); cv.set(tx + 1, y, METAL[2])
            for y in range(top + 4, ty, 5):
                cv.hline(tx - 2, y, 6, METAL[3])
            cv.set(tx, top, PINK[3]); cv.set(tx + 1, top, PINK[2])  # the red warning light


def _facade(cv: Canvas, x0: int, x1: int, y0: int, y1: int, style: str, seed: int):
    """One stretch of facade, floor by floor (12 px a floor). glass: a curtain wall, its
    mullions and spandrels, panes dark with the sky's reflection running down them on a
    slant, offices lit here and there; flats: concrete with window pairs, balconies
    whose slabs catch the light, air conditioners, plants and washing; old: glazed tile
    with framed windows, sills, and a fire escape zigzagging down."""
    ramp = GLASS if style == 'glass' else TILE_C if style == 'old' else CONCRETE
    floors = (y1 - y0) // 12
    for y in range(y0, y1):
        for x in range(x0, x1):
            cv.set(x, y, ramp[2] if x > x0 + 1 else ramp[3])
    for f in range(floors):
        fy = y1 - (f + 1) * 12
        if style == 'glass':
            for x in range(x0, x1):
                for y in range(fy, fy + 12):
                    r = y - fy
                    col = (x - x0) % 7
                    if r < 2:
                        c = METAL[3] if r == 0 else METAL[2]  # the spandrel
                    elif col == 0:
                        c = METAL[2] if x > x0 else METAL[4]  # the mullion
                    else:
                        refl = ((x - x0) + (y - y0) * 0.6 + seed * 13) % 37
                        c = GLASS[4] if refl < 3 else GLASS[3] if refl < 9 else GLASS[1] if r > 8 else GLASS[2]
                        n = noise2((x - x0) // 7, f, 1910 + seed)
                        if n > 0.8:
                            c = WARM_W[3] if r < 6 else WARM_W[2]
                        elif n > 0.7:
                            c = COOL_W[3] if r < 6 else COOL_W[2]
                    cv.set(x, y, c)
        else:
            bay = 16 if style == 'flats' else 14
            cv.hline(x0, fy, x1 - x0, ramp[4] if style == 'old' else ramp[3])  # the floor's ledge
            for k, bx in enumerate(range(x0 + 4, x1 - 10, bay)):
                n = noise2(k, f, 1912 + seed)
                lit = WARM_W if n > 0.62 else COOL_W if n > 0.5 else None
                ww, wh = 9, 7
                wx, wy = bx, fy + 3
                for y in range(wy, wy + wh):
                    for x in range(wx, wx + ww):
                        if lit:
                            c = lit[3] if y < wy + 3 else lit[2]
                        else:
                            c = NIGHT[1] if y > wy + 1 else NIGHT[2]
                        if style == 'old' and (x == wx + ww // 2 or y == wy + 3):
                            c = ramp[5]  # the glazing bars of a sash
                        cv.set(x, y, c)
                if lit and noise2(k, f, 1913 + seed) > 0.5:
                    cv.hline(wx + 1, wy + 1, 3, '#FFF6D8' if lit is WARM_W else '#E8FBFF')  # a lamp, a curtain
                if style == 'old':
                    cv.hline(wx - 1, wy - 1, ww + 2, ramp[5]); cv.hline(wx - 1, wy + wh, ww + 2, ramp[5])
                    cv.hline(wx - 1, wy + wh + 1, ww + 2, ramp[1])
                if style == 'flats' and noise2(k, f, 1914 + seed) > 0.55 and f > 0:
                    # a balcony: its slab lit on top, its rail, its shadow on the wall below
                    for x in range(wx - 2, wx + ww + 2):
                        cv.set(x, wy + wh, ramp[5]); cv.set(x, wy + wh + 1, ramp[3])
                        cv.set(x, wy + wh + 2, ramp[0])
                        if (x - wx) % 2 == 0:
                            cv.set(x, wy + wh - 1, METAL[4]); cv.set(x, wy + wh - 2, METAL[3])
                    cv.hline(wx - 2, wy + wh - 3, ww + 4, METAL[4])
                    if noise2(k, f, 1915 + seed) > 0.5:  # a plant, or washing
                        cv.set(wx + 1, wy + wh - 1, '#4A8A5A'); cv.set(wx + 1, wy + wh - 2, '#2E5A40')
                    else:
                        for d in range(3):
                            cv.set(wx + 3 + d * 2, wy + wh - 2, ('#E8E2D2', '#C8463A', '#6FA8D8')[d])
                elif noise2(k, f, 1916 + seed) > 0.6:  # an air conditioner under the window
                    for x in range(wx + 1, wx + 7):
                        cv.set(x, wy + wh + 1, METAL[4]); cv.set(x, wy + wh + 2, METAL[2]); cv.set(x, wy + wh + 3, ramp[0])
                    cv.set(wx + 6, wy + wh + 4, '#5A78A8')  # a drip
        if style == 'old' and f % 2 == 0:  # the fire escape: a landing a floor, stairs between
            ex = x1 - 16
            for x in range(ex, ex + 14):
                cv.set(x, fy + 11, IRON[3]); cv.set(x, fy + 10, IRON[2] if x % 2 else IRON[4])
            for t in range(10):
                cv.set(ex + 2 + t, fy + 10 - t, IRON[3])
    for y in range(y0, y1):  # the lit west edge and the shaded east edge of the stretch
        cv.set(x0, y, ramp[4]); cv.set(x1 - 1, y, ramp[0])


def _shopfront(cv: Canvas, x0: int, x1: int, y0: int, y1: int, seed: int, kind: str):
    """The street floor (24 px): a lit shop window in its frame with goods behind it, a
    door with light under it, a half-drawn shutter, an awning or a lit canopy, and a
    signboard of glyphs over it (never real words); a lobby for a glass tower."""
    sign = SIGN_RAMPS[seed % 3]
    for y in range(y0, y1):
        for x in range(x0, x1):
            cv.set(x, y, CONCRETE[1])
    if kind == 'lobby':  # a glazed lobby: its hall lit warm behind the mullions, a desk,
        # a plant, the revolving door under a canopy lit from beneath
        mx = (x0 + x1) // 2
        for y in range(y0 + 4, y1):
            for x in range(x0 + 3, x1 - 3):
                r = y - y0
                c = WARM_W[2] if r > 9 else WARM_W[3] if r > 5 else WARM_W[1]
                if (x - x0) % 8 == 3:
                    c = METAL[3] if x < mx else METAL[2]
                if r >= 14 and abs(x - mx) > 12 and (x // 10) % 3 == 1 and r < 18:
                    c = WOOD[2]  # the desk
                if r >= 10 and (x - x0) % 23 == 6:
                    c = '#2E5A40' if r < 16 else WOOD[1]  # a plant in a pot
                cv.set(x, y, c)
        for y in range(y0 + 8, y1):
            for x in range(mx - 6, mx + 6):
                cv.set(x, y, METAL[3] if abs(x - mx) in (0, 5) else METAL[1] if (x + y) % 4 == 0 else WARM_W[3])
        for x in range(mx - 15, mx + 15):
            cv.set(x, y0 + 1, METAL[5]); cv.set(x, y0 + 2, METAL[3]); cv.set(x, y0 + 3, WARM_W[4])
        return
    door_l = noise2(seed, 1, 1920) > 0.5
    dx = x0 + 4 if door_l else x1 - 16
    wx0, wx1 = (x0 + 18, x1 - 4) if door_l else (x0 + 4, x1 - 18)
    shutter = noise2(seed, 2, 1920) > 0.6
    goods = (AMBER, PINK, CYAN, ['#2E5A40', '#447A50', '#62995E', '#8AC07A', '#C8E8B0'])[seed % 4]
    for y in range(y0 + 7, y1 - 1):
        for x in range(wx0, wx1):
            c = WARM_W[3] if y < y0 + 12 else WARM_W[2]
            if (x - wx0) % 9 == 0 or y == y1 - 2:
                c = METAL[1]
            if shutter and y < y0 + 13:
                c = METAL[3] if (y - y0) % 2 else METAL[2]  # the roller shutter, half down
            cv.set(x, y, c)
        if y > y1 - 6:
            for gx in range(wx0 + 3, wx1 - 2, 4):
                cv.set(gx, y, goods[3] if y == y1 - 5 else goods[2])
    for y in range(y0 + 7, y1 - 1):  # the door
        for x in range(dx, dx + 12):
            cv.set(x, y, NIGHT[0] if x > dx + 1 else METAL[2])
    cv.hline(dx, y1 - 2, 12, AMBER[3])  # the light under it
    cv.set(dx + 9, y0 + 15, AMBER[4])
    if noise2(seed, 3, 1920) > 0.45:  # an awning, a plane sloping out toward us
        aw = SIGN_RAMPS[(seed + 1) % 3]
        for y in range(y0 + 3, y0 + 7):
            for x in range(wx0 - 2, wx1 + 2):
                st = ((x - wx0) // 4) % 2
                c = (aw[2] if st else CONCRETE[4]) if y < y0 + 6 else (aw[1] if st else CONCRETE[2])
                cv.set(x, y, c)
    sx0, sx1 = x0 + 3, x1 - 3  # the signboard
    tubes = set()
    for x in range(sx0, sx1):
        cv.set(x, y0, sign[1]); cv.set(x, y0 + 1, NIGHT[0]); cv.set(x, y0 + 2, sign[1])
    for k, gx in enumerate(range(sx0 + 3, sx1 - 5, 7)):
        if noise2(seed, k, 1921) > 0.25:
            tubes |= glyph(cv, gx, y0 - 1, seed * 7 + k, sign, size=4)
    glow(cv, tubes, sign, r=1)


def blade_sign(cv: Canvas, x: int, y0: int, y1: int, seed: int, ramp):
    """A vertical neon sign on brackets, standing out from the wall: a dark box with a lit
    frame and glyphs stacked down it, a halo round the tubes."""
    tubes = set()
    for y in range(y0, y1):
        for xx in range(x, x + 9):
            cv.set(xx, y, NIGHT[0])
    for y in range(y0, y1):
        cv.set(x, y, ramp[2]); cv.set(x + 8, y, ramp[1])
        tubes |= {(x, y), (x + 8, y)}
    cv.hline(x, y0, 9, ramp[3]); cv.hline(x, y1 - 1, 9, ramp[1])
    for k, gy in enumerate(range(y0 + 3, y1 - 6, 8)):
        tubes |= glyph(cv, x + 2, gy, seed * 11 + k, ramp)
    for by in (y0 + 2, y1 - 3):  # its brackets to the wall
        cv.hline(x - 3, by, 3, IRON[3])
    glow(cv, tubes, ramp)


def building(width: int, floors: int, style: str = 'flats', seed: int = 0, shop: str = 'shop',
             setback: bool = False, blade: int = 0) -> Canvas:
    """A city building in the three-quarter view: its front facing the street below it and
    its flat roof seen above it, as every building in the world is drawn. Width, floors and
    style vary (glass towers, concrete flats, old tiled walk-ups), each with its own
    street floor, roof furniture and signs, so no two read alike. A tall glass tower may
    step back, its lower block's roof a terrace in front of the upper block. blade: a
    vertical neon sign on the west (-1) or east (1) side."""
    lobby = 24
    R = max(14, min(24, width // 4))  # how deep a roof we see
    upper = floors
    lower = 0
    inset = 0
    if setback and floors >= 10:
        lower = floors * 2 // 5
        upper = floors - lower
        inset = max(8, width // 6)
    Rl = 10 if lower else 0
    h = R + upper * 12 + Rl + lower * 12 + lobby + 4
    pad_l = pad_r = 0  # (a blade sign hangs on the facade, inside the building's width)
    w = width + pad_l + pad_r
    cv = Canvas(w, h, pad=PAD)
    bx0, bx1 = pad_l, pad_l + width
    ramp = METAL if style == 'glass' else CONCRETE if style == 'flats' else TILE_C
    y = 0
    _rooftop(cv, bx0 + inset, bx1 - inset, y, y + R, seed, floors >= 12, METAL if style == 'glass' else CONCRETE)
    y += R
    _facade(cv, bx0 + inset, bx1 - inset, y, y + upper * 12, style, seed)
    if style == 'glass':  # a lit crown band under the parapet
        crown = SIGN_RAMPS[seed % 3]
        for x in range(bx0 + inset, bx1 - inset):
            cv.set(x, y, crown[3] if x % 4 else crown[2]); cv.set(x, y + 1, crown[1])
    y += upper * 12
    if lower:
        for yy in range(y, y + Rl):  # the terrace on the lower block's roof
            for x in range(bx0, bx1):
                c = CONCRETE[2] if (x // 6 + yy // 3) % 2 else CONCRETE[3]
                if yy == y + Rl - 1:
                    c = CONCRETE[5]
                cv.set(x, yy, c)
        for x in range(bx0 + 2, bx1 - 2, 9):  # planters along it
            cv.set(x, y + 4, '#4A8A5A'); cv.set(x + 1, y + 4, '#2E5A40'); cv.set(x, y + 5, WOOD[2]); cv.set(x + 1, y + 5, WOOD[1])
        for x in range(bx0 + inset, bx1 - inset):  # the upper block's foot shades the terrace
            cv.set(x, y, CONCRETE[0])
        y += Rl
        _facade(cv, bx0, bx1, y, y + lower * 12, style, seed + 3)
        y += lower * 12
    for x in range(bx0, bx1):  # the cornice over the street floor
        cv.set(x, y, ramp[5] if style != 'glass' else METAL[4]); cv.set(x, y + 1, ramp[2])
    _shopfront(cv, bx0, bx1, y + 2, y + 2 + lobby, seed, 'lobby' if style == 'glass' and shop != 'shop' else shop)
    y += 2 + lobby
    for x in range(bx0, bx1):  # the plinth
        cv.set(x, y, CONCRETE[3]); cv.set(x, y + 1, CONCRETE[2])
    if blade:  # on the block it is fixed to: the lower one where the tower steps back
        sx = bx0 + 4 if blade == -1 else bx1 - 13
        if lower:
            top = R + upper * 12 + Rl + 4
            bottom = top + lower * 12 - 6
        else:
            top = R + 6
            bottom = min(h - lobby - 8, top + 12 + min(upper, 7) * 10)
        blade_sign(cv, sx, top, bottom, seed, SIGN_RAMPS[(seed + 2) % 3])
    return cv


# ---- the city's street furniture and harbour (N1), in the three-quarter view ---------
def city_lamp() -> Canvas:
    """A street lamp, 18 x 56: a steel column on a square base lit on its west face, a
    curved arm, and a flat luminaire whose top we see and whose underside glows."""
    cv = Canvas(18, 56, pad=PAD)
    for y in range(10, 52):
        cv.set(6, y, METAL[4]); cv.set(7, y, METAL[3]); cv.set(8, y, METAL[1])
    for y in range(48, 54):
        for x in range(4, 11):
            cv.set(x, y, METAL[4] if y == 48 else METAL[3] if x < 7 else METAL[1])
    for t in range(6):
        cv.set(7 + t, 10 - (t // 2), METAL[3])
    for x in range(8, 18):  # the luminaire: its top plane, its lit lens
        cv.set(x, 5, METAL[4]); cv.set(x, 6, METAL[3]); cv.set(x, 7, METAL[2])
        cv.set(x, 8, WARM_W[4] if 9 < x < 16 else WARM_W[3])
    cv.set(17, 6, METAL[1]); cv.set(17, 7, METAL[1])
    return cv


def street_tree(seed: int = 0, pit: bool = True) -> Canvas:
    """A street tree in its pit, 40 x 60: a cast-iron grate round the trunk, a slim trunk
    lit on the west, a crown of leaf clusters darker at dusk, a guard hoop. Without its
    pit (pit=False) it is planted in open ground: the trunk flares into roots instead."""
    import style as _st
    cv = Canvas(40, 60, pad=PAD)
    if pit:
        for y in range(52, 58):  # the grate
            for x in range(10, 30):
                c = IRON[2] if (x + y) % 3 else IRON[1]
                if y == 52:
                    c = IRON[3]
                cv.set(x, y, c)
    for y in range(26, 55 if pit else 57):
        cv.set(19, y, '#5E4632'); cv.set(20, y, '#4A3828'); cv.set(21, y, '#33261C')
    if pit:
        for y in range(44, 54):  # the guard hoop
            cv.set(13, y, METAL[4]); cv.set(27, y, METAL[2])
        cv.hline(13, 44, 15, METAL[4])
    else:
        cv.hline(17, 56, 7, '#4A3828'); cv.set(18, 55, '#5E4632'); cv.set(22, 55, '#33261C')
        cv.set(16, 57, '#5E4632'); cv.set(24, 57, '#33261C')
    _st.leafy(cv, 20, 18, 15 + noise2(seed, 1, 1960) * 3, 13, ['#14281F', '#1F3A2A', '#2E5A40', '#447A50', '#62995E'],
              r=2.4, seed=1961 + seed)
    return cv


def city_bench() -> Canvas:
    """A bench, 34 x 20: timber slats on steel legs, its seat seen from above, its back
    rail, lit on top."""
    cv = Canvas(34, 20, pad=PAD)
    for x in range(2, 32):
        for y in range(3, 7):  # the back
            cv.set(x, y, WOOD[4] if y == 3 else WOOD[3] if y < 6 else WOOD[1])
        for y in range(9, 14):  # the seat's slats, seen from above
            cv.set(x, y, WOOD[4] if y % 2 else WOOD[2])
        cv.set(x, 14, WOOD[1])
    for lx in (4, 28):
        for y in range(3, 19):
            cv.set(lx, y, METAL[3]); cv.set(lx + 1, y, METAL[1])
    return cv


def litter_bin() -> Canvas:
    """A litter bin, 12 x 18: a steel drum with a domed lid, lit on the west."""
    cv = Canvas(12, 18, pad=PAD)
    for y in range(5, 17):
        for x in range(1, 11):
            cv.set(x, y, METAL[4] if x < 3 else METAL[3] if x < 7 else METAL[2] if x < 9 else METAL[1])
        if y % 4 == 0:
            cv.hline(1, y, 10, METAL[1])
    for (x, y) in oval(6, 4, 5, 2.5):
        cv.set(x, y, METAL[5] if x < 6 else METAL[3])
    cv.set(5, 4, METAL[0]); cv.set(6, 4, METAL[0])
    return cv


def bollard() -> Canvas:
    """A mooring bollard on a quay, 12 x 14: a squat iron post with a cap, lit on the west."""
    cv = Canvas(12, 14, pad=PAD)
    for y in range(4, 13):
        for x in range(2, 10):
            cv.set(x, y, IRON[4] if x < 4 else IRON[3] if x < 7 else IRON[1])
    for (x, y) in oval(6, 4, 5, 2):
        cv.set(x, y, IRON[4] if x < 6 else IRON[2])
    cv.hline(2, 9, 8, AMBER[3])
    return cv


def crossing_signal() -> Canvas:
    """A crossing signal, 12 x 50: a post with a box showing a lit walking light."""
    cv = Canvas(12, 50, pad=PAD)
    for y in range(14, 48):
        cv.set(5, y, METAL[4]); cv.set(6, y, METAL[2])
    for y in range(2, 16):
        for x in range(2, 10):
            cv.set(x, y, METAL[2] if x < 9 else METAL[1])
    for (x, y) in disc(5.5, 6, 2):
        cv.set(x, y, '#3A0E14')
    for (x, y) in disc(5.5, 11, 2):
        cv.set(x, y, '#6FE6A0' if x < 6 else '#3FB07A')
    cv.hline(2, 2, 8, METAL[4])
    return cv


def vending_box(seed: int = 0) -> Canvas:
    """A vending machine against a wall, 22 x 36: its top seen, its lit front with rows of
    cans, the coin panel, the hatch, a shaded side."""
    ramp = SIGN_RAMPS[seed % 3]
    cv = Canvas(22, 36, pad=PAD)
    for x in range(1, 21):
        for y in range(1, 5):
            cv.set(x, y, METAL[4] if y == 1 else METAL[3])
    for y in range(5, 34):
        for x in range(1, 18):
            c = ramp[2] if x < 3 else ramp[1]
            if 7 <= y < 24 and 3 <= x < 13:
                c = '#E8F4FF' if (y - 7) % 4 == 0 else (ramp[3], AMBER[3], CYAN[3], '#E8E2D2')[(x + (y // 4)) % 4]
            if 7 <= y < 24 and x in (13, 14, 15, 16):
                c = METAL[2] if (y % 3) else METAL[4]
            if y >= 27 and 4 <= x < 14:
                c = NIGHT[0] if y < 31 else METAL[2]
            cv.set(x, y, c)
        for x in range(18, 21):
            cv.set(x, y, ramp[0])
    return cv


def market_stall(seed: int = 0) -> Canvas:
    """A market stall, 58 x 44: a striped canopy as a plane sloping toward us on poles, a
    lantern under it, the counter's front of boards with goods heaped on its top (fruit,
    fish on ice, lanterns or parts by the seed), crates stacked beside it."""
    cv = Canvas(58, 44, pad=PAD)
    canopy = SIGN_RAMPS[seed % 3]
    kind = seed % 4
    for y in range(2, 14):  # the canopy
        for x in range(2, 56):
            st = ((x - 2) // 6) % 2
            c = (canopy[3] if st else '#F2ECDE') if y < 11 else (canopy[2] if st else '#C8C0B0')
            if y == 2:
                c = canopy[4] if st else '#FFFFFF'
            cv.set(x, y, c)
        if y == 13:
            for x in range(2, 56, 6):
                cv.set(x + 2, 14, canopy[1])  # the scalloped edge
    for px in (4, 52):
        for y in range(14, 40):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
    for (x, y) in disc(28, 18, 2.5):  # a paper lantern
        cv.set(x, y, AMBER[3] if x < 28 else AMBER[2])
    for y in range(26, 40):  # the counter's front
        for x in range(6, 52):
            c = WOOD[3] if (x // 5) % 2 else WOOD[2]
            if y == 26:
                c = WOOD[4]
            cv.set(x, y, c)
    goods = [(AMBER, '#C8463A', '#62995E'), ('#DCE2EC', '#9AB0C8', '#5A78A8'), (PINK, AMBER, CYAN),
             ('#76808E', '#A0A8B4', AMBER)][kind]
    for k in range(18):  # the goods heaped on the counter's top
        gx = 8 + (k * 7 + int(noise2(seed, k, 1965) * 4)) % 42
        gy = 22 + int(noise2(k, seed, 1966) * 4)
        g = goods[k % 3]
        col = g[3] if isinstance(g, list) else g
        cv.set(gx, gy, col); cv.set(gx + 1, gy, col); cv.set(gx, gy + 1, col)
        cv.set(gx + 1, gy + 1, (g[1] if isinstance(g, list) else '#3A3040'))
    for y in range(32, 42):  # crates stacked beside
        for x in range(50, 58):
            c = WOOD[3] if y in (32, 37) else WOOD[2] if x < 56 else WOOD[1]
            cv.set(x, y, c)
    return cv


def fountain() -> Canvas:
    """The plaza's fountain, 80 x 64: a round basin in the three-quarter view, its rim lit
    on the far side, still water holding the lights, a slender lit column in the middle
    with a fall of water round it."""
    cv = Canvas(80, 64, pad=PAD)
    cx, cy = 40, 40
    for (x, y) in oval(cx, cy, 36, 14):  # the basin's rim
        cv.set(x, y, PORC_[3] if y < cy else PORC_[2])
    for x in range(4, 77):  # its front face, below the rim's near edge
        if ((x - cx) / 36) ** 2 <= 1:
            yb = cy + int(14 * math.sqrt(max(0.0, 1 - ((x - cx) / 36) ** 2)))
            for y in range(yb, yb + 6):
                cv.set(x, y, PORC_[1] if x > cx + 10 else PORC_[2])
            cv.set(x, yb + 6, PORC_[0])
    for (x, y) in oval(cx, cy, 32, 11):  # the water
        c = '#16324A' if (x + y // 2) % 7 else CYAN[2]
        if (x - cx) % 11 == 0 and y % 3 == 0:
            c = AMBER[3]
        cv.set(x, y, c)
    for y in range(6, cy):  # the column
        for x in range(cx - 3, cx + 4):
            cv.set(x, y, CYAN[3] if x < cx else CYAN[2] if x < cx + 2 else CYAN[1])
    for (x, y) in oval(cx, 6, 6, 2.5):
        cv.set(x, y, PORC_[4])
    for t in range(16):  # the water falling round it
        for side in (-1, 1):
            x = cx + side * (4 + t // 3)
            cv.set(x, 8 + t * 2, '#D2FBFF' if t % 2 else CYAN[3])
    glow(cv, {(cx, y) for y in range(8, cy - 2)}, CYAN)
    return cv


PORC_ = ['#3A4258', '#5C6680', '#8A94AC', '#B8C0D2', '#DCE2EC', '#F4F7FB']


def tram_stop() -> Canvas:
    """A tram stop, 64 x 50: a glass shelter whose roof we see from above, its back panel a
    lit map of the lines, a bench inside, a pole with the stop's lit sign."""
    cv = Canvas(64, 50, pad=PAD)
    for y in range(4, 12):  # the roof, from above
        for x in range(2, 58):
            cv.set(x, y, PORC_[4] if y == 4 else PORC_[3] if x < 40 else PORC_[2])
    cv.hline(2, 12, 56, PORC_[1])
    for y in range(13, 44):
        for x in range(4, 56):
            c = '#1E2E50' if (x + y) % 9 else '#3A5684'  # the glass back
            if 18 <= y < 30 and 16 <= x < 44:
                c = CYAN[2] if (x - 16) % 7 == 0 or (y - 18) % 5 == 0 else NIGHT[1]  # the lines' map, lit
            cv.set(x, y, c)
        cv.set(4, y, METAL[4]); cv.set(55, y, METAL[2])
    for x in range(10, 50):  # the bench
        cv.set(x, 36, WOOD[4]); cv.set(x, 37, WOOD[2])
    for y in range(4, 48):
        cv.set(60, y, METAL[4]); cv.set(61, y, METAL[2])
    for y in range(4, 12):
        for x in range(57, 64):
            cv.set(x, y, AMBER[3] if 58 < x < 63 and 5 < y < 11 else METAL[2])
    return cv


def food_kiosk(seed: int = 0) -> Canvas:
    """A food kiosk on the promenade, 50 x 52: a small box with its roof seen from above,
    a serving hatch with its shutter propped up, lit inside, a menu board of glyphs, a
    stool or two at its counter."""
    ramp = SIGN_RAMPS[seed % 3]
    cv = Canvas(50, 52, pad=PAD)
    for y in range(2, 12):
        for x in range(2, 48):
            cv.set(x, y, METAL[4] if y == 2 else METAL[3] if x < 34 else METAL[2])
    for y in range(12, 48):
        for x in range(4, 46):
            c = ramp[1] if x > 6 else ramp[2]
            if 18 <= y < 32 and 10 <= x < 40:
                c = WARM_W[3] if y < 24 else WARM_W[2]
            cv.set(x, y, c)
    for x in range(8, 42):  # the propped shutter
        cv.set(x, 15, METAL[4]); cv.set(x, 16, METAL[2])
    for x in range(8, 42):  # the counter
        cv.set(x, 32, METAL[5]); cv.set(x, 33, METAL[3])
    tubes = set()
    for k in range(3):
        tubes |= glyph(cv, 12 + k * 9, 36, seed * 5 + k, ramp, size=4)
    glow(cv, tubes, ramp, r=1)
    for sx in (12, 30):  # stools
        cv.hline(sx, 40, 6, METAL[4]); cv.vline(sx + 2, 41, 7, METAL[2])
    return cv


def gantry_crane() -> Canvas:
    """A container crane on the quay, 120 x 170: two A-frame legs on rails, a high
    girder, the boom out over the water to the east, the operator's cab with a lit
    window, a spreader hanging on its cables; painted steel, lit on the west faces."""
    cv = Canvas(120, 170, pad=PAD)
    RED_ = ['#4A1210', '#7A1E18', '#A8302A', '#D04A3E', '#F07A6A']
    for (lx, lean) in ((14, 1), (58, -1)):  # the legs
        for y in range(40, 166):
            t = (y - 40) / 126
            x = int(lx + lean * (1 - t) * 6)
            for d in range(5):
                cv.set(x + d, y, RED_[3] if d < 2 else RED_[2] if d < 4 else RED_[1])
    for y in range(52, 160, 22):  # cross bracing between the legs
        for t in range(39):
            cv.set(19 + t, y + t // 3, RED_[2])
    for x in range(10, 118):  # the girder and the boom, seen from below-front
        for y in range(30, 42):
            c = RED_[3] if y < 33 else RED_[2] if y < 39 else RED_[1]
            if (x - 10) % 12 == 0 and 33 <= y < 39:
                c = RED_[1]  # the truss's verticals
            if y == 30:
                c = RED_[4]
            cv.set(x, y, c)
    for y in range(4, 32):  # the apex mast and its stays
        cv.set(40, y, RED_[3]); cv.set(41, y, RED_[1])
    for t in range(60):
        cv.set(40 + t, 4 + t * 26 // 60, METAL[3])
        cv.set(40 - t // 2, 4 + t * 26 // 30 if t < 30 else 30, METAL[3])
    for y in range(42, 56):  # the cab
        for x in range(74, 92):
            c = METAL[4] if y == 42 else WARM_W[3] if 45 <= y < 52 and 76 <= x < 90 else METAL[2]
            cv.set(x, y, c)
    for y in range(42, 120):  # the spreader's cables
        cv.set(100, y, METAL[3]); cv.set(108, y, METAL[3])
    for y in range(120, 128):
        for x in range(92, 118):
            cv.set(x, y, AMBER[3] if y == 120 else AMBER[2] if x < 112 else AMBER[1])
    for x in range(10, 66):  # the rail bogies at the feet
        cv.set(x, 166, METAL[3]); cv.set(x, 167, METAL[1])
    return cv


def container_stack(seed: int = 0) -> Canvas:
    """Shipping containers stacked two high, 74 x 46: each box's top seen from above with
    its corrugation, its doors toward us with locking bars, colours varied, lit on top."""
    cols = (['#1A3A4A', '#24506A', '#2E6A8A', '#4A8AAA'], ['#4A1E18', '#6A2A22', '#8A3A2E', '#AA5A4A'],
            ['#3A3A18', '#5A5A22', '#7A7A2E', '#9A9A4A'], ['#1E3A2A', '#2A5A3E', '#3A7A52', '#5A9A72'],
            ['#3A2A4A', '#52406A', '#6A588A', '#8A78AA'])
    cv = Canvas(74, 46, pad=PAD)
    boxes = [(0, 22, 36, 0), (37, 22, 36, 1), (8, 2, 36, 2)] if seed % 2 == 0 else \
            [(0, 22, 36, 0), (37, 22, 36, 1), (30, 2, 36, 2)]
    for (bx, by, bw, k) in boxes:
        ramp = cols[(seed + k * 2) % len(cols)]
        for y in range(by, by + 6):  # its top
            for x in range(bx, bx + bw):
                cv.set(x, y, ramp[3] if (x - bx) % 3 else ramp[2])
        for y in range(by + 6, by + 22):  # its doors
            for x in range(bx, bx + bw):
                c = ramp[2] if x < bx + bw // 2 else ramp[1]
                if (x - bx) % 4 == 0:
                    c = ramp[0]  # the corrugation
                if x in (bx + 8, bx + 14, bx + bw - 14, bx + bw - 8) and by + 8 < y < by + 20:
                    c = METAL[4]  # the locking bars
                cv.set(x, y, c)
        cv.hline(bx, by + 6, bw, ramp[3])
        cv.hline(bx, by + 21, bw, ramp[0])
        for y in range(by + 8, by + 12):  # a plate of glyph-like markings
            for x in range(bx + 18, bx + 26):
                cv.set(x, y, '#E8E2D2' if (x + y) % 3 else ramp[1])
    return cv


def cargo_ship() -> Canvas:
    """A cargo ship moored along the quay, 76 x 190, its length north-south: the hull seen
    from above and a little from the side (its east flank in shade), the deck stacked with
    containers whose tops we see, the bridge house at the stern with lit windows, mooring
    lines; it floats (the water round it is drawn by the zone)."""
    cv = Canvas(76, 190, pad=PAD)
    cx = 38
    for y in range(6, 186):
        half = 30 if y > 30 else int(30 * math.sqrt(max(0, (y - 6) / 24)))
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) > half - 3
            c = '#2A3A52' if edge and x < cx else '#16202E' if edge else '#4A5A6E'
            cv.set(x, y, c)
        if half > 4:
            cv.set(cx + half + 1, y, '#0B1220')
            cv.set(cx + half + 2, y, '#6A2A22')  # its red boot-topping in shade
    for k in range(6):  # containers on deck, rows of tops
        y0 = 40 + k * 20
        for j in range(2):
            ramp = (['#24506A', '#2E6A8A', '#4A8AAA'], ['#6A2A22', '#8A3A2E', '#AA5A4A'],
                    ['#5A5A22', '#7A7A2E', '#9A9A4A'])[(k + j) % 3]
            for y in range(y0, y0 + 16):
                for x in range(cx - 24 + j * 25, cx - 1 + j * 25):
                    c = ramp[2] if (x - cx) % 3 else ramp[1]
                    if y == y0:
                        c = '#E8E2D2'
                    if y >= y0 + 13:
                        c = ramp[0]
                    cv.set(x, y, c)
    for y in range(160, 182):  # the bridge house
        for x in range(cx - 20, cx + 21):
            c = '#DCE2EC' if y < 164 else '#B8C0D2' if x < cx + 14 else '#8A94AC'
            if 168 <= y < 172 and (x - cx) % 5 and abs(x - cx) < 17:
                c = WARM_W[3]
            cv.set(x, y, c)
    for y in range(150, 160):  # its funnel
        for x in range(cx - 4, cx + 5):
            cv.set(x, y, '#C8463A' if x < cx + 2 else '#9A3028')
    cv.hline(cx - 4, 150, 9, '#1A1A22')
    return cv


def lighthouse() -> Canvas:
    """The point's lighthouse, 40 x 120: a white tapering tower in bands, lit on the west,
    a gallery with its railing, the lantern room glowing, a cap with a vane; on a plinth."""
    cv = Canvas(40, 120, pad=PAD)
    for y in range(28, 112):
        t = (y - 28) / 84
        half = 8 + t * 6
        for x in range(int(20 - half), int(20 + half) + 1):
            k = (x - (20 - half)) / (2 * half)
            band = ((y - 28) // 14) % 2
            c = ('#F4F7FB' if k < 0.3 else '#DCE2EC' if k < 0.7 else '#B8C0D2') if not band else \
                ('#E04A3E' if k < 0.3 else '#C0362C' if k < 0.7 else '#902420')
            cv.set(x, y, c)
    for y in range(100, 112):  # the door at the foot of the stair inside
        for x in range(17, 23):
            cv.set(x, y, METAL[1] if x > 18 else METAL[2])
    for y in range(112, 118):
        for x in range(6, 34):
            cv.set(x, y, CONC_[4] if y == 112 else CONC_[2] if x < 28 else CONC_[1])
    for x in range(8, 33):  # the gallery
        cv.set(x, 26, METAL[4]); cv.set(x, 27, METAL[2])
        if x % 3 == 0:
            cv.vline(x, 22, 4, METAL[3])
    cv.hline(8, 22, 25, METAL[4])
    for y in range(12, 22):  # the lantern room, lit
        for x in range(13, 28):
            c = WARM_W[4] if 15 < x < 25 else WARM_W[3]
            if (x - 13) % 5 == 0:
                c = METAL[2]
            cv.set(x, y, c)
    for y in range(5, 12):  # the cap
        half = (y - 5) + 2
        for x in range(20 - half, 20 + half + 1):
            cv.set(x, y, METAL[3] if x < 20 else METAL[1])
    cv.vline(20, 0, 5, METAL[4])
    glow(cv, {(x, y) for x in range(15, 26) for y in range(13, 21)}, AMBER, r=2)
    return cv


CONC_ = ['#1E1C2A', '#2C2A3C', '#3C3A50', '#4E4C64', '#64627C', '#807E96']


def skybridge(width: int = 64, seed: int = 0) -> Canvas:
    """A skybridge across a street, width x 30, seen from below and in front: an enclosed
    glazed walkway, its roof's top lit, its long side glazed and lit with people crossing,
    its steel deck's edge and soffit dark, a strip of light along its foot. It lands in a
    doorway in the tower at each end (the towers carry it)."""
    w = width
    cv = Canvas(w, 30, pad=PAD)
    for x in range(w):
        cv.set(x, 2, METAL[5]); cv.set(x, 3, METAL[4]); cv.set(x, 4, METAL[3])  # the roof
        for y in range(5, 20):  # the glazed side
            c = WARM_W[2] if y > 12 else COOL_W[3] if y < 8 else WARM_W[3]
            if x % 8 == 0:
                c = METAL[2]
            cv.set(x, y, c)
        cv.set(x, 20, METAL[4]); cv.set(x, 21, METAL[2])  # the deck's edge
        for y in range(22, 26):
            cv.set(x, y, METAL[1] if y < 25 else METAL[0])  # the soffit
        cv.set(x, 26, CYAN[2] if x % 3 else CYAN[1])  # the light strip under it
    for k in range(3):  # people crossing, in silhouette against the light
        px = 6 + int(noise2(seed, k, 1970) * (w - 12))
        for y in range(10, 19):
            cv.set(px, y, NIGHT[0]); cv.set(px + 1, y, NIGHT[0])
        cv.set(px, 9, NIGHT[1]); cv.set(px + 1, 9, NIGHT[1])
    return cv


def water_taxi() -> Canvas:
    """A water taxi at the quay, 64 x 26: a low hull seen from above and a little from the
    side, a glazed cabin with its roof and a lit sign, fenders along its flank."""
    cv = Canvas(64, 26, pad=PAD)
    for (x, y) in oval(32, 14, 30, 9):
        c = '#3A4258' if y < 14 else '#1E2436'
        cv.set(x, y, c)
    for x in range(4, 60):
        cv.set(x, 20, '#0B1220')
    for y in range(6, 15):
        for x in range(18, 46):
            c = PORC_[4] if y == 6 else COOL_W[3] if 8 <= y < 12 and (x - 18) % 5 else PORC_[2]
            cv.set(x, y, c)
    for x in range(26, 38):
        cv.set(x, 4, AMBER[3]); cv.set(x, 5, AMBER[2])
    for fx in range(10, 56, 9):
        cv.set(fx, 17, '#1A1A22'); cv.set(fx, 18, '#1A1A22')
    return cv


# ---- the city's plan (shared with city_zones.py, which paints it and cuts the zones)
CITY = {'heights': (0, 0), 'plaza': (1, 0), 'waterfront': (2, 0), 'market': (0, 1), 'downtown': (1, 1),
        'docks': (2, 1), 'neon': (0, 2), 'skyport': (1, 2), 'point': (2, 2)}
CW, CH = 3 * 320, 3 * 576
CN = CW * CH
QUAY_X = 800  # the east quay's edge (the sea beyond it)
DOCK_X = 836  # where the docks' apron widens the quay for the cranes
HARBOUR_Y = 1622  # the south quay's edge (Neon's and the Skyport's harbour)

# (name, centre line, road half-width, pavement width, grade)
STREETS = [
    ('hill', [(-20, 300), (180, 290), (330, 300), (470, 308), (640, 300), (QUAY_X - 30, 296)], 14, 12, 1),
    ('cable', [(-20, 604), (90, 610), (170, 600)], 10, 10, 2),
    ('cable_e', [(480, 600), (640, 612), (QUAY_X - 30, 606)], 10, 10, 2),
    ('market', [(-20, 880), (160, 872), (330, 862), (480, 872), (650, 884), (QUAY_X - 30, 880)], 14, 14, 1),
    ('harbour', [(-20, 1344), (300, 1344), (420, 1344)], 36, 0, 1),  # (the old core's street, as it was)
    ('avenue', [(160, 1310), (158, 1150), (150, 960), (164, 760), (172, 520), (166, 330), (150, 140), (140, 40)],
     16, 12, 1),
    ('towerrow', [(480, 404), (486, 520), (478, 720), (482, 880), (480, 1110)], 12, 12, 1),
    ('quayroad', [(QUAY_X - 40, 40), (QUAY_X - 40, 600), (QUAY_X - 60, 700), (QUAY_X - 60, 1060), (QUAY_X - 46, 1420)],
     12, 0, 1),
    ('terminal', [(-20, 1112), (160, 1118), (320, 1124), (QUAY_X - 30, 1124)], 0, 18, 3),  # a walk behind the core and the Skyport
]
# the plaza: the city's square, where Hill Street meets Tower Row (centre, radii)
PLAZA = (480, 340, 110, 70)
# the heights' terraces above Hill Street, climbed by stairs (rim rows, from the street up)
TERRACES = [(232, 'lower'), (150, 'upper')]
TERRACE_STAIRS = [(130, 232, 56), (123, 150, 56)]


def chaikin(pts, n: int = 3):
    """Corner-cutting: a polyline's corners rounded off, its ends kept."""
    pts = list(pts)
    for _ in range(n):
        out = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            out += [(x0 * .75 + x1 * .25, y0 * .75 + y1 * .25), (x0 * .25 + x1 * .75, y0 * .25 + y1 * .75)]
        out.append(pts[-1])
        pts = out
    return pts



LINES = {name: (chaikin(line, 3), hw, pw, grade) for (name, line, hw, pw, grade) in STREETS}
RIMS = {'rim1': (232, 1810), 'rim2': (150, 1812)}  # the heights' terrace rims (base row, seed)


def rim_y(x: float, base: float, seed: int) -> float:
    """Where a terrace's rim runs at x: a contour, not a ruled line."""
    return base + (smooth_noise(x, 0, 40, seed) - 0.5) * 14 + (smooth_noise(x, 0, 11, seed + 1) - 0.5) * 4


def _line_y(name: str, x: float) -> float:
    if name in RIMS:
        return rim_y(x, *RIMS[name])
    return street_y(name, x)
def street_y(name: str, x: float) -> float:
    """Where an east-west street's centre line runs at x (city px)."""
    sm = LINES[name][0]
    for (x0, y0), (x1, y1) in zip(sm, sm[1:]):
        if min(x0, x1) <= x <= max(x0, x1) and x1 != x0:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return sm[0][1] if x < sm[0][0] else sm[-1][1]


def street_x(name: str, y: float) -> float:
    """Where a north-south street's centre line runs at y."""
    sm = LINES[name][0]
    for (x0, y0), (x1, y1) in zip(sm, sm[1:]):
        if min(y0, y1) <= y <= max(y0, y1) and y1 != y0:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return sm[0][0] if abs(y - sm[0][1]) < abs(y - sm[-1][1]) else sm[-1][0]


# The frontages: each a row of buildings standing on the back of a street's north
# pavement and facing it (street, x from, x to, the deepest a building may reach north
# of its foot, the district's style mix, the most floors).
FRONTAGES = [
    ('hill', 300, 780, 'top', ('glass', 'flats', 'old'), 18),
    ('cable', -10, 150, 'hill', ('flats', 'old'), 16),
    ('cable_e', 490, 640, 'hill', ('flats', 'glass'), 16),
    ('market', -10, 150, 'cable', ('old', 'flats'), 14),
    ('market', 180, 470, 'hill', ('glass',), 32),
    ('market', 490, 640, 'cable_e', ('glass', 'flats'), 14),
    ('terminal', -10, 640, 'market', ('glass', 'flats', 'old'), 13),
    ('harbour', -10, 330, 'terminal', ('flats', 'old'), 12),
    ('rim1', 0, 300, 'rim2', ('old', 'flats'), 2),
    ('rim2', 0, 300, 'top', ('old', 'flats'), 7),
]


def _ns_blocked(y0: float, y1: float, foot: float = 1e9):
    """The x ranges a building may not cover between rows y0 and y1: the north-south
    streets and their pavements (a building never stands in a street)."""
    out = []
    for name in ('avenue', 'towerrow', 'quayroad'):
        sm, hw, pw, _g = LINES[name]
        ys = [p[1] for p in sm]
        if max(ys) < y0 or min(ys) > y1:
            continue
        xs = [street_x(name, y) for y in range(int(y0), int(y1) + 1, 8) if min(ys) <= y <= max(ys)]
        if xs:
            out.append((min(xs) - hw - pw - 4, max(xs) + hw + pw + 4))
    pcx, pcy, prx, pry = PLAZA
    if y0 < pcy + pry and y1 > pcy - pry and foot > pcy - pry - 2 + 0.5 * pry * 0:
        if foot > pcy - pry:  # (a building may face the square, never stand in it)
            out.append((pcx - prx - 4, pcx + prx + 4))
    return out


@functools.lru_cache(maxsize=1)
def city_buildings() -> list:
    """Every building in the city as (key, sprite, foot x, foot y), feet in city px.
    Walking along each frontage, a building is as wide as chance gives (an alley now and
    then), as tall as its block allows (never hiding the street behind it) and as tall as
    its district wants, in the district's styles; a few carry a blade sign."""
    out = []
    n = 0
    for (street, xa, xb, behind, styles, most) in FRONTAGES:
        sm, hw, pw, _g = LINES[street] if street in LINES else (None, 0, 0, 0)
        x = xa
        k = 0
        while x < xb - 40:
            w = 48 + int(noise2(n, 1, 1950) * 60)
            w -= w % 4
            foot = min(_line_y(street, xx) for xx in range(int(x), int(x + w), 4)) - hw - pw - 1
            if street in RIMS:
                foot -= 7  # (a walk along the terrace's edge in front of the houses)
            pcx, pcy, prx, pry = PLAZA
            if x < pcx + prx and x + w > pcx - prx and street == 'hill':  # facing the square across its edge
                top = min(pcy - pry * math.sqrt(max(0.0, 1 - ((xx - pcx) / prx) ** 2)) for xx in range(int(x), int(x + w), 4))
                foot = min(foot, top - 2)
            if behind == 'top':
                limit = foot - 6
            elif behind in RIMS:
                limit = foot - (max(_line_y(behind, xx) for xx in range(int(x), int(x + w), 4)) + 18)
            else:
                bsm, bhw, bpw, _ = LINES[behind]
                limit = foot - (max(street_y(behind, xx) for xx in range(int(x), int(x + w), 4)) + bhw + bpw) - 16
            room = int((limit - 18 - 24 - 6) // 12)
            floors = max(2, min(most, room) - int(noise2(n, 3, 1950) * 4))
            if x < pcx + prx + 4 and x + w > pcx - prx - 4 and foot > pcy + pry:
                floors = max(2, min(floors, int((foot - (pcy + pry + 10) - 64) // 12)))  # (never over the square)
            tall = 24 + 26 + floors * 12 + 10  # (the sprite's height, near enough)
            blocked = _ns_blocked(foot - tall, foot, foot)
            clash = [r for r in blocked if x < r[1] and x + w > r[0]]
            if clash:
                room_w = int(min(r[0] for r in clash) - x) - 2
                if room_w >= 44 and min(r[0] for r in clash) > x:
                    w = room_w - room_w % 4
                else:
                    x = max(r[1] for r in clash) + 2
                    continue
            if x + w > xb:
                w = int(xb - x)
                w -= w % 4
                if w < 44:
                    break
            style = styles[int(noise2(n, 2, 1950) * len(styles))]
            if style == 'glass' and floors < 6:
                style = 'flats'
            setback = style == 'glass' and floors >= 12 and noise2(n, 4, 1950) > 0.4
            blade = 0 if style == 'glass' else (-1 if noise2(n, 5, 1950) < 0.25 else 1 if noise2(n, 5, 1950) > 0.7 else 0)
            spec = (w, floors, style, 2000 + n, 'shop', setback, blade)
            out.append((f'city_b{n}', spec, int(x + w / 2), int(foot)))
            n += 1
            k += 1
            x += w + (12 if noise2(n, 6, 1950) > 0.88 else 2)
    return out


@functools.lru_cache(maxsize=1)
def city_skybridges() -> list:
    """The skybridges: where two towers of four floors or more face each other across a
    north-south street on the same frontage, an enclosed walkway joins them at their
    third floor, landing in each (key, width, foot x of its middle, foot y, height)."""
    out = []
    bs = sorted(city_buildings(), key=lambda b: (b[3], b[2]))
    for (k1, s1, x1, y1), (k2, s2, x2, y2) in zip(bs, bs[1:]):
        if abs(y1 - y2) > 24 or s1[1] < 4 or s2[1] < 4:
            continue
        r1, l2 = x1 + s1[0] // 2, x2 - s2[0] // 2
        gap = l2 - r1
        if not 40 <= gap <= 110:
            continue
        h = 26 + 2 * 12 + 4  # the third floor's sill, above the street
        out.append((f'skybridge_{len(out)}', gap + 8, (r1 + l2) // 2, max(y1, y2), h))
    return out


def city_props() -> dict[str, Canvas]:
    """The city's own props: its buildings (each its own sprite), its skybridges, its street
    furniture, the market, the plaza, the quays."""
    out = {key: building(*spec) for (key, spec, _x, _y) in city_buildings()}
    out.update({key: skybridge(w, seed=k) for k, (key, w, _x, _y, _h) in enumerate(city_skybridges())})
    out.update({
        'city_lamp': city_lamp(), 'city_street_tree': street_tree(0), 'city_street_tree_b': street_tree(1), 'city_tree_planted': street_tree(2, pit=False),
        'city_bench': city_bench(), 'city_litter_bin': litter_bin(), 'city_quay_bollard': bollard(),
        'city_crossing_signal': crossing_signal(), 'city_vending_box': vending_box(0), 'city_vending_box_b': vending_box(1),
        'city_vending_box_c': vending_box(2), 'city_market_stall': market_stall(0), 'city_market_stall_b': market_stall(1),
        'city_market_stall_c': market_stall(2), 'city_market_stall_d': market_stall(3), 'city_fountain': fountain(),
        'city_tram_stop': tram_stop(), 'city_food_kiosk': food_kiosk(0), 'city_food_kiosk_b': food_kiosk(1),
        'city_gantry_crane': gantry_crane(), 'city_container_stack': container_stack(0), 'city_container_stack_b': container_stack(1),
        'city_container_stack_c': container_stack(2), 'city_container_stack_d': container_stack(3),
        'city_cargo_ship': cargo_ship(), 'city_lighthouse': lighthouse(), 'city_water_taxi': water_taxi(),
    })
    return out


def props() -> dict[str, Canvas]:
    return {**city_props(),
        'tower_pink': tower(112, 150, 0, PINK), 'tower_cyan': tower(96, 136, 1, CYAN),
        'tower_amber': tower(104, 142, 2, AMBER), 'noodle_stall': noodle_stall(),
        'vending_machine': vending_machine(), 'street_light': street_light(), 'holo_board': holo_board(),
        'drone': drone(), 'cable_pole': cable_pole(), 'shelter': shelter(), 'uv_planter': uv_planter(),
        'containers': containers(), 'ferry': ferry(),
        'maglev': maglev(), 'tether': tether(), 'ticket_gates': ticket_gates(), 'glass_screen': glass_screen(),
        'holo_map': holo_map(), 'departure_pylon': departure_pylon(),
        'luggage_bot': luggage_bot(), 'pod_tree': pod_tree(), 'sky_bench': sky_bench(),
        'cables': cables(), 'bike_rack': bike_rack(), 'sky_planter': sky_planter(0), 'sky_planter_b': sky_planter(3),
        'flower_kiosk': flower_kiosk(),
    }


if __name__ == '__main__':
    from PIL import Image
    import style
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (42, 38, 64, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    out.save(os.environ.get('SHEET', '/tmp/cyber-props.png'))
    print('sheet', out.size)
