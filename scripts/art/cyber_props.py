"""Props for Neon Harbour, the rainy city at permanent dusk (world-atlas.md).

The valley's rules still hold (steep top-down roofs, light from the upper left,
material shading, an outline), but the light is night light: surfaces sit low on the
`night` ramp and the neon ramps carry the glow. Signs use abstract glyphs, never real
words or brands. Run directly for a contact sheet: python3 scripts/art/cyber_props.py
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
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
    """The space elevator's ribbon, 40 x 260, rising from its anchor out of sight: two
    pale strands with a cyan guide light between and a soft glow round them, a climber
    car a third of the way up with its windows lit, the whole thing thinning and fading
    into dots as it climbs."""
    w, h = 40, 260
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(0, h - 2):
        t = y / h  # 0 at the top, far up
        if t > 0.3:  # the glow, strongest near the ground
            for dx in (-7, -6, 6, 7) if t > 0.6 else (-6, 6):
                if (y + dx) % 2:
                    cv.set(cx + dx, y, CYAN[1] if abs(dx) == 6 else CYAN[0])
        for dx, c in ((-4, PORCELAIN[5]), (-3, PORCELAIN[3]), (3, PORCELAIN[2]), (4, PORCELAIN[1])):
            if t > 0.35 or (y + dx) % max(2, int(7 - t * 14)) == 0:
                cv.set(cx + dx, y, c)
        if t > 0.2 or y % 3 == 0:
            for dx in (-1, 0, 1):
                cv.set(cx + dx, y, CYAN[4] if dx == 0 else CYAN[3] if (y // 4) % 2 else CYAN[2])
        if y % 14 == 0 and t > 0.3:
            cv.hline(cx - 5, y, 11, PORCELAIN[5])  # spacer clamps
    cy = int(h * 0.38)  # the climber
    for y in range(cy, cy + 32):
        for x in range(cx - 15, cx + 16):
            r = abs(x - cx) / 15
            if r > 1 - (abs(y - cy - 16) / 16) ** 4 * 0.45:
                continue
            c = PORCELAIN[5] if x < cx - 7 else PORCELAIN[4] if x < cx + 4 else PORCELAIN[2]
            if 9 <= y - cy <= 15 and abs(x - cx) < 12:
                c = AMBER[3] if (x - cx) % 4 else NIGHT[1]
            cv.set(x, y, c)
    cv.hline(cx - 12, cy + 24, 25, CYAN[3])
    for y in range(h - 16, h - 2):  # its foot: a clamp collar
        cv.hline(cx - 8, y, 17, PORCELAIN[3] if y % 4 else PORCELAIN[1])
        cv.set(cx - 8, y, PORCELAIN[5])
    return cv


def ticket_gates() -> Canvas:
    """A row of five quiet ticket gates, 82 x 24: white pods with cyan-lit readers and
    glass paddles open, seen from above at the angle of the rest."""
    w, h = 82, 24
    cv = Canvas(w, h, pad=PAD)
    for k in range(6):
        x0 = 2 + k * 15
        for y in range(4, 20):
            for x in range(x0, x0 + 6):
                c = PORCELAIN[5] if y < 7 else PORCELAIN[4] if x < x0 + 2 else PORCELAIN[3] if x < x0 + 5 else PORCELAIN[1]
                cv.set(x, y, c)
        cv.hline(x0 + 1, 8, 4, CYAN[3]); cv.hline(x0 + 1, 9, 4, CYAN[1])
        if k < 5:
            for y in range(10, 16):  # the glass paddles, open
                cv.set(x0 + 7, y, CYAN[1]); cv.set(x0 + 13, y, CYAN[1])
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

def props() -> dict[str, Canvas]:
    return {
        'tower_pink': tower(112, 150, 0, PINK), 'tower_cyan': tower(96, 136, 1, CYAN),
        'tower_amber': tower(104, 142, 2, AMBER), 'noodle_stall': noodle_stall(),
        'vending_machine': vending_machine(), 'street_light': street_light(), 'holo_board': holo_board(),
        'drone': drone(), 'cable_pole': cable_pole(), 'shelter': shelter(), 'uv_planter': uv_planter(),
        'containers': containers(), 'ferry': ferry(),
        'maglev': maglev(), 'tether': tether(), 'ticket_gates': ticket_gates(), 'departure_pylon': departure_pylon(),
        'luggage_bot': luggage_bot(), 'pod_tree': pod_tree(), 'sky_bench': sky_bench(),
        'cables': cables(), 'bike_rack': bike_rack(),
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
