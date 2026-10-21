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
import facade as fc  # noqa: E402
import garden_props as gp  # noqa: E402
from materials import MATERIALS, STONE, WOOD  # noqa: E402

NIGHT, PINK, CYAN, AMBER = (MATERIALS[k] for k in ('night', 'neon_pink', 'neon_cyan', 'neon_amber'))
IRON = MATERIALS['iron']
PAD = 4
# The scale table (verticality.md section 5, A = an adult resident, 25 px): an upper
# storey is 32 px, a shop's street storey 44 (its shopfront 40 between the cornice and
# the plinth), a single door 14 x 32, a shop's double door 22 x 32, a window 12 x 16.
FLOOR = 32
SHOP = 44
SHOPFRONT = SHOP - 4
DOOR_H = 32
SHOP_DOOR_W = 22


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
    fy0, fy1 = roof_h, h - 48  # (the shop storey below, 44 px, the scale table's)
    for y in range(fy0, fy1):
        for x in range(2, w - 2):
            cv.set(x, y, NIGHT[2] if x > 5 else NIGHT[3])
    for x in range(2, w - 2):
        cv.set(x, fy0, NIGHT[1])
    for fl, y in enumerate(range(fy1 - FLOOR + 7, fy0 + 2, -FLOOR)):  # a storey every FLOOR px
        cv.hline(2, y + 23, w - 4, NIGHT[3])  # a floor ledge, lit on top
        for i, x in enumerate(range(12, w - 18, 20)):
            n = noise2(fl, i, 173 + seed)
            lit = AMBER if n > 0.62 else CYAN if n > 0.42 else None
            for (px, py) in rect_set(x, y, 12, 16):
                if lit:
                    cv.set(px, py, lit[3] if py < y + 6 else lit[2])
                else:
                    cv.set(px, py, NIGHT[0] if py > y + 3 else NIGHT[1])
            cv.hline(x, y - 1, 12, NIGHT[4])
            if noise2(fl, i, 174 + seed) > 0.6:  # an air conditioner box under the window
                for (px, py) in rect_set(x + 2, y + 17, 8, 4):
                    cv.set(px, py, STONE[3] if py == y + 17 else STONE[2])
                cv.set(x + 5, y + 18, STONE[1])
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
    for (x, y) in rect_set(12, sy + 12, w - 44, 28):
        cv.set(x, y, AMBER[3] if y < sy + 18 else AMBER[2])
    for x in range(12, w - 32, 8):
        cv.vline(x, sy + 12, 28, NIGHT[1])
    for (x, y) in rect_set(w - 28, sy + 8, 14, DOOR_H):  # a door, a strip of light under it
        cv.set(x, y, NIGHT[0])
    cv.hline(w - 28, sy + 7 + DOOR_H, 14, AMBER[3])
    detail.stones(cv, 2, h - 4, w - 4, 4, NIGHT, seed=seed, course=2)
    return cv


def noodle_stall() -> Canvas:
    """A street food stall, 72 x 48: a striped awning seen from above with paper lanterns
    under it on two posts, a counter at a person's hip (13 px, the scale table's) lit
    from inside with a steaming pot on it, two stools before it."""
    w, h = 72, 48
    cv = Canvas(w, h, pad=PAD)
    for y in range(2, 13):  # the awning
        for x in range(2, w - 2):
            stripe = (x // 7) % 2
            c = (PINK[2] if stripe else NIGHT[4]) if y < 10 else (PINK[1] if stripe else NIGHT[3])
            if y == 2:
                c = PINK[3] if stripe else NIGHT[5]
            cv.set(x, y, c)
    for x in range(2, w - 2):
        cv.set(x, 13 + (1 if (x // 3) % 2 else 0), PINK[1] if (x // 7) % 2 else NIGHT[2])
    for px in (5, w - 7):  # the posts
        for y in range(14, h - 4):
            cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
    for lx in (16, 36, 56):  # paper lanterns
        cv.vline(lx, 14, 2, NIGHT[1])
        for (x, y) in oval(lx, 19, 3, 3.5):
            cv.set(x, y, AMBER[3] if y < 19 else AMBER[2])
    top, front = h - 4 - 13 - 3, h - 4 - 13  # the counter's top (seen from above) and its front
    for y in range(top, front):
        for x in range(8, w - 8):
            cv.set(x, y, WOOD[4] if y == top else WOOD[3])
    for y in range(front, h - 4):
        for x in range(8, w - 8):
            cv.set(x, y, AMBER[2] if y < front + 3 else WOOD[2])
    cv.hline(8, front, w - 16, WOOD[1])
    detail.boards(cv, rect_set(8, front + 3, w - 16, h - 4 - front - 3), WOOD, 2, front + 3, board=5, vertical=True, x0=8)
    for (x, y) in oval(50, top + 1, 6, 2.4):  # the pot on the counter
        cv.set(x, y, IRON[3] if x < 50 else IRON[1])
    for (x, y) in oval(50, top, 4, 1.4):
        cv.set(x, y, AMBER[4])
    for (bx, by) in ((20, top - 1), (26, top)):  # bowls
        cv.hline(bx, by, 4, '#E8E2D2'); cv.hline(bx + 1, by + 1, 2, '#B8B0A0')
    for i, (bx, by) in enumerate(((49, top - 4), (52, top - 8))):  # its steam
        for (x, y) in disc(bx, by, 2.0 - i * 0.4):
            cv.set(x, y, '#D9DCE8' if x < bx else '#A9ADC0')
    for sx in (22, 44):  # stools before the counter
        cv.hline(sx - 3, h - 10, 7, '#C8463A'); cv.hline(sx - 3, h - 9, 7, '#8A2A22')
        cv.vline(sx - 2, h - 8, 5, IRON[2]); cv.vline(sx + 2, h - 8, 5, IRON[1])
    return cv


def vending_machine() -> Canvas:
    """A glowing vending machine, 22 x 32 (the scale table's 30): a lit panel of drinks, a coin slot and a tray."""
    cv = Canvas(22, 32, pad=PAD)
    for y in range(2, 30):
        for x in range(1, 21):
            cv.set(x, y, NIGHT[3] if x < 4 else NIGHT[2])
    cv.hline(1, 2, 20, NIGHT[5])
    for (x, y) in rect_set(4, 5, 12, 15):
        cv.set(x, y, CYAN[3] if y < 8 else CYAN[2])
    for row in range(3):
        for col in range(3):
            c = (PINK, AMBER, CYAN)[(row + col) % 3]
            cv.rect(5 + col * 4, 8 + row * 4, 2, 2, c[3])
            cv.set(5 + col * 4, 8 + row * 4, c[4])
    cv.rect(17, 10, 2, 4, NIGHT[0]); cv.set(17, 15, AMBER[3])
    cv.rect(5, 23, 10, 4, NIGHT[0]); cv.hline(5, 23, 10, NIGHT[1])
    glow(cv, rect_set(4, 5, 12, 15), CYAN, r=1)
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
    """The space elevator's lift, 56 x 84, standing on its anchor ring (fault 25): a
    climber car docked in its cradle at the foot, door open toward the boarding ramp,
    gripping the ribbon with a wheel housing on its roof, the ribbon's foot (two pale
    strands tied together, a cyan guide light between) entering the grip and fading out a
    few pixels above it (Matt's World Logic answer 18)."""
    w, h = 56, 84
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    car_top, car_bot = h - 58, h - 14
    # the ribbon (Matt's World Logic answer 18): it goes up off the anchor only, two pale
    # strands tied together with a cyan guide light between, and fades out within a few
    # pixels above the grip, a glow at its foot; nothing of it is painted further up
    r_top, r_bot = car_top - 24, car_top - 6
    foot = set()
    for y in range(r_top, r_bot):
        t = (y - r_top) / (r_bot - r_top)  # 0 where it fades out, 1 at the grip
        if t < 0.3 and y % 3:
            continue  # it thins to a few dashes and is gone
        half = 1 if t < 0.55 else 2
        lit = PORCELAIN[5] if t > 0.6 else PORCELAIN[3] if t > 0.3 else PORCELAIN[2]
        cv.set(cx - half, y, lit)
        if half > 1:
            cv.set(cx + half, y, PORCELAIN[2])
            cv.set(cx - 1, y, CYAN[2]); cv.set(cx + 1, y, CYAN[2])
            if y % 5 == 0:
                cv.hline(cx - 2, y, 5, PORCELAIN[3])  # ties between the strands
        cv.set(cx, y, CYAN[4] if t > 0.6 else CYAN[3] if t > 0.3 else CYAN[2])
        if t > 0.7:
            foot.add((cx, y))
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
    glow(cv, foot, CYAN, r=3)  # the guide light's glow where the ribbon enters the grip
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
GLASS_TEAL = ['#0A1A1E', '#12302E', '#1A4844', '#24605A', '#3A8078', '#62A89C']
GLASS_BRONZE = ['#1A1410', '#2E2218', '#443222', '#5C4630', '#7A6044', '#A08466']
CONCRETE_SAND = ['#241E1C', '#3A322C', '#524640', '#6A5C52', '#86786C', '#A49688']
CONCRETE_BLUE = ['#1A1E2A', '#262E40', '#344058', '#465472', '#5C6C8C', '#7C8CAA']
TILE_BRICK = ['#241410', '#3E201A', '#5A2E24', '#743E30', '#905040', '#AE6A56']
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
    """A flat roof seen from above: a parapet lit along its front and west edges, and a
    surface that differs from roof to roof (rule 8): a membrane laid in strips with drains,
    pale gravel, a timber deck with planters, a green sedum roof, or rows of solar panels;
    a deep roof opens on a light well. Then the things that live on roofs, more or fewer,
    each with its lit top and its shadow down and to the right: a water tank on legs,
    air-conditioner units, a stair bulkhead with its door facing us, solar panels,
    planters, and on the tallest an antenna with a red light."""
    kind = ('membrane', 'membrane', 'gravel', 'deck', 'green', 'solar')[int(noise2(seed, 0, 1902) * 6)]
    if y1 - y0 < 16 and kind in ('deck', 'solar'):
        kind = 'membrane'
    fc.roof(cv, x0, x1, y0, y1, kind, ramp, seed)
    if kind == 'membrane':  # drains
        for k in range(1 + (x1 - x0) // 40):
            dx = x0 + 6 + int(noise2(seed, 5 + k, 1902) * max(1, x1 - x0 - 12))
            dy = y0 + 3 + int(noise2(seed, 15 + k, 1902) * max(1, y1 - y0 - 6))
            cv.set(dx, dy, ramp[0]); cv.set(dx + 1, dy, ramp[1])
    if y1 - y0 >= 44 and x1 - x0 >= 40:  # a light well, its walls lit on the far side
        lw, lh = 14 + int(noise2(seed, 2, 1902) * 10), 10 + int(noise2(seed, 3, 1902) * 8)
        lx = x0 + 6 + int(noise2(seed, 4, 1902) * max(1, x1 - x0 - lw - 12))
        ly = y0 + (y1 - y0 - lh) // 2
        for y in range(ly, ly + lh):
            for x in range(lx, lx + lw):
                c = NIGHT[0]
                if y < ly + 3:
                    c = ramp[3] if y == ly else ramp[1]  # its north wall, lit, a window
                    if y == ly + 1 and (x - lx) % 5 == 2:
                        c = WARM_W[3]
                cv.set(x, y, c)
        cv.hline(lx - 1, ly + lh, lw + 2, ramp[4])
    for x in range(x0, x1):  # the parapet: its top lit, its inner face in shade
        cv.set(x, y1 - 1, ramp[4]); cv.set(x, y1 - 2, ramp[3]); cv.set(x, y0, ramp[3])
    for y in range(y0, y1):
        cv.set(x0, y, ramp[4]); cv.set(x1 - 1, y, ramp[2])
    if kind in ('solar', 'deck') and noise2(seed, 9, 1902) > 0.5:
        return  # a roof given over to one use
    things = []
    W_ = x1 - x0
    r = noise2(seed, 1, 1901)
    if W_ > 40 and noise2(seed, 8, 1901) > 0.35:
        things.append(('tank', x0 + 6 + int(r * (W_ - 26)), y0 + 2))
    if noise2(seed, 9, 1901) > 0.3:
        things.append(('ac', x0 + 4 + int(noise2(seed, 2, 1901) * max(1, W_ - 20)), y1 - 9))
    if W_ > 56 and noise2(seed, 10, 1901) > 0.4:
        things.append(('ac', x0 + 4 + int(noise2(seed, 3, 1901) * max(1, W_ - 20)), y1 - 9))
    if W_ > 56 and noise2(seed, 11, 1901) > 0.5:
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
    """One stretch of facade, floor by floor (FLOOR px a floor, the scale table's upper
    storey: about 1.3 people), drawn to Eastward's level of detail (facade.py; art-style.md):
    glass: a curtain wall, louvred spandrels, mullions lit on their west face, panes with the
    sky, the street's skyline and a glint in them, or offices behind; flats: precast panels
    with their board marks (or worn render), windows a person's height and more in stone
    reveals with curtains, lamps and plants, balconies whose slabs catch the light behind a
    waist-high rail, air conditioners dripping rust; old: brick in running bond or glazed
    tile, soldier-course lintels, sash windows, a fire escape zigzagging down. Every floor's
    ledge leaves its soot under it, a downpipe runs to the street, cables are clipped along,
    and the east end of the front is a step darker than the west."""
    # each building its own rhythm and colour (rule 8; to-c-city-review 3): the mullion
    # spacing, the bay, the window's size and the cladding's tint come from its seed
    v = noise2(seed, 0, 1915)
    if style == 'glass':
        ramp = (GLASS, GLASS_TEAL, GLASS_BRONZE)[int(v * 3)]
    elif style == 'flats':
        ramp = (CONCRETE, CONCRETE_SAND, CONCRETE_BLUE)[int(v * 3)]
    else:
        ramp = (TILE_C, TILE_BRICK, TILE_C)[int(v * 3)]
    mull = 10 + int(noise2(seed, 1, 1915) * 6)
    bay_w = (22 if style == 'flats' else 20) + int(noise2(seed, 2, 1915) * 8)
    win_w = 11 + int(noise2(seed, 3, 1915) * 4)
    win_h = 14 + int(noise2(seed, 4, 1915) * 4)
    floors = (y1 - y0) // FLOOR
    restore = fc.guard(cv, x0, x1, y0, y1)
    if style == 'glass':
        fc.curtain_wall(cv, x0, x1, y0, y1, ramp, seed, FLOOR, mull)
        restore()
        fc.east_shade(cv, x0, x1, y0, y1)
        return
    kind = ('panel' if noise2(seed, 8, 1915) > 0.3 else 'render') if style == 'flats' else \
        ('tile' if ramp is TILE_C else 'brick')
    wall_r = list(ramp[1:]) if kind in ('panel', 'render') else list(ramp)
    fc.wall(cv, x0, x1, y0, y1, kind, wall_r, seed)
    frame = (['#2A2630', '#5A5460', '#9A949C', '#D8D2D0'], ['#1E2A26', '#2E4A40', '#4A7A64', '#8AB8A0'],
             ['#2A1A14', '#5A3424', '#8A5434', '#C8925A'])[int(noise2(seed, 9, 1915) * 3)]
    bay = max(bay_w, win_w + 6)
    xs = list(range(x0 + 5, x1 - win_w - 2, bay))
    gaps = [bx + win_w + (bay - win_w) // 2 for bx in xs[:-1]]
    pipe = None
    if gaps and noise2(seed, 10, 1915) > 0.25:
        pipe = gaps[int(noise2(seed, 11, 1915) * len(gaps))]
    elif x1 - (xs[-1] + win_w if xs else x0) >= 9:
        pipe = x1 - 6
    for f in range(floors):
        fy = y1 - (f + 1) * FLOOR
        fc.ledge(cv, x0, x1, fy, fc.STONE_T if kind != 'panel' else [ramp[0]] + list(ramp[1:]), seed + f)
        for k, bx in enumerate(xs):
            n = noise2(k, f, 1912 + seed)
            lit = WARM_W if n > 0.62 else COOL_W if n > 0.5 else None
            ws = seed * 31 + k * 7 + f * 131
            wx, wy = bx, fy + 7
            balcony = style == 'flats' and noise2(k, f, 1914 + seed) > 0.55 and f > 0
            fc.window(cv, wx, wy, win_w, win_h, wall_r, lit, ws, frame=frame,
                      bars='sash' if style == 'old' else ('casement' if k % 2 else 'none'),
                      lintel='soldier' if kind == 'brick' else 'stone' if kind in ('tile', 'render') else 'none',
                      extras=not balcony)
            wh, ww = win_h, win_w
            if balcony:
                # a balcony: its slab lit on top, its rail at a person's waist, its
                # shadow on the wall below
                for x in range(wx - 3, wx + ww + 3):
                    cv.set(x, wy + wh, ramp[5]); cv.set(x, wy + wh + 1, ramp[3])
                    cv.set(x, wy + wh + 2, ramp[1])
                    fc.darken(cv, x + 1, wy + wh + 3, 1.6); fc.darken(cv, x + 2, wy + wh + 4, 0.8)
                    if (x - wx) % 3 == 0:
                        for d in range(1, 8):
                            cv.set(x, wy + wh - d, METAL[4] if d > 5 else METAL[3])
                cv.hline(wx - 3, wy + wh - 8, ww + 6, METAL[5])
                cv.hline(wx - 3, wy + wh - 7, ww + 6, METAL[2])
                if noise2(k, f, 1915 + seed) > 0.5:  # a plant, or washing
                    for d in range(1, 6):
                        cv.set(wx + 1, wy + wh - d, fc.LEAF[3] if d > 2 else fc.LEAF[1])
                        cv.set(wx + 2, wy + wh - d - 1, fc.LEAF[2])
                        cv.set(wx + 3, wy + wh - d, '#6A3A24' if d < 3 else fc.LEAF[4])
                else:
                    cv.hline(wx, wy + wh - 9, ww, '#C8C0B0')  # the line
                    for d in range(3):
                        for e in range(3):
                            c = ('#E8E2D2', '#C8463A', '#6FA8D8')[d]
                            cv.set(wx + 1 + d * 4, wy + wh - 8 + e, c if e < 2 else fc.step(c, 1))
                            cv.set(wx + 2 + d * 4, wy + wh - 8 + e, c if e < 2 else fc.step(c, 1))
            elif noise2(k, f, 1916 + seed) > 0.55:  # an air conditioner under the window
                fc.ac_unit(cv, wx + (1 if k % 2 else ww - 9), wy + wh + 3, METAL, seed + k)
            elif noise2(k, f, 1917 + seed) > 0.7:
                fc.vent(cv, wx + ww + 2, wy + wh - 4)
        if style == 'old' and f % 2 == 0:  # the fire escape: a landing a floor, stairs between
            ex = x1 - 22
            if ex > x0 + 8:
                for x in range(ex, ex + 20):
                    cv.set(x, fy + FLOOR - 1, IRON[3]); cv.set(x, fy + FLOOR - 2, IRON[2] if (x // 2) % 2 else IRON[4])
                    fc.darken(cv, x + 1, fy + FLOOR, 1.5)
                    if x % 3 == 0:
                        for d in range(3, 9):
                            cv.set(x, fy + FLOOR - d, IRON[3])
                cv.hline(ex, fy + FLOOR - 9, 20, IRON[4])  # its rail
                cv.hline(ex, fy + FLOOR - 8, 20, IRON[1])
                rise = FLOOR - 4
                for t in range(rise):
                    sx = ex + 2 + t * 16 // rise
                    cv.set(sx, fy + FLOOR - 2 - t, IRON[3]); cv.set(sx + 1, fy + FLOOR - 2 - t, IRON[1])
        if f > 0 and noise2(seed, f, 1918) > 0.5:  # a cable run clipped along under the ledge
            fc.cable(cv, x0 + 2, x1 - 2, fy + 4, 2, '#1A1820', seed + f)
        if noise2(seed, f, 1919) > 0.7 and xs:  # pigeons on the ledge
            bxp = xs[int(noise2(seed, f, 1920) * len(xs))] + 2
            fc.bird(cv, bxp, fy - 1)
    if pipe is not None:
        fc.downpipe(cv, pipe, y0 + 1, y1, METAL, seed)
    restore()
    fc.east_shade(cv, x0, x1, y0, y1)


def _shopfront(cv: Canvas, x0: int, x1: int, y0: int, y1: int, seed: int, kind: str):
    """The street floor (SHOPFRONT px, the scale table's shop storey less its cornice and
    plinth), to Eastward's level of detail: stone piers in courses at either end with the
    things a street leaves on them (posters, a tag, a meter box); a signboard with depth over
    the front, its tube frame and glyphs lit (never real words); a lit shop window in its
    frame with goods on its shelves, a pendant lamp and a glint on the glass, over a tiled
    stall riser; a glazed double door a head taller than the people going in, with its kick
    plate, push bars and the light under it; an awning, or a roller shutter half down; a
    lobby for a glass tower, with its desk, its plants and a revolving door."""
    restore = fc.guard(cv, x0, x1, y0, y1)
    sign = SIGN_RAMPS[seed % 3]
    goods = (AMBER, PINK, CYAN, ['#2E5A40', '#447A50', '#62995E', '#8AC07A', '#C8E8B0'])[seed % 4]
    pier = fc.STONE_T if noise2(seed, 5, 1920) > 0.4 else [fc.step(c, 0.4) for c in CONCRETE_SAND]
    fc.wall(cv, x0, x1, y0, y1, 'ashlar', pier, seed + 77)
    dtop = y1 - 1 - DOOR_H  # the doors' head, a door's height above the step
    sx0, sx1 = x0 + 2, x1 - 2  # the signboard over the whole front
    if kind == 'lobby':  # a glazed lobby: its hall lit warm behind the mullions, a desk,
        # plants, the revolving door under a canopy lit from beneath
        mx = (x0 + x1) // 2
        for y in range(y0 + 6, y1):
            for x in range(x0 + 3, x1 - 3):
                r = y - y0
                c = WARM_W[3] if r < 9 else WARM_W[2] if r < 20 else fc.step(WARM_W[2], 0.7)
                if r in (7, 8) and (x - x0) % 6 in (2, 3):
                    c = WARM_W[4]  # the ceiling's lights
                if r >= 31:
                    c = '#C8B8A0' if ((x - x0) // 3 + r) % 2 else '#9A8A78'  # the stone floor
                if (x - x0) % 10 in (3, 4):
                    c = METAL[4] if (x - x0) % 10 == 3 else METAL[2]
                if 25 <= r < 31 and abs(x - mx) > 16 and (x // 14) % 3 == 1:
                    c = WOOD[4] if r == 25 else WOOD[2] if r < 29 else WOOD[1]  # the desk
                if r >= 20 and (x - x0) % 29 in (7, 8, 9):
                    c = (fc.LEAF[3] if (x + r) % 3 else fc.LEAF[2]) if r < 29 else (WOOD[2] if r < 31 else WOOD[1])
                cv.set(x, y, c)
        for y in range(dtop, y1):
            for x in range(mx - 11, mx + 11):
                c = METAL[4] if x == mx - 11 else METAL[2] if abs(x - mx) in (0, 10) else \
                    METAL[3] if (x - mx + 11) % 7 in (0, 1) and y > dtop + 2 else WARM_W[3] if y < dtop + 12 else WARM_W[2]
                cv.set(x, y, c)
        cv.hline(mx - 11, dtop, 22, METAL[4])
        for x in range(mx - 18, mx + 18):
            cv.set(x, y0 + 6, METAL[5]); cv.set(x, y0 + 7, METAL[3]); cv.set(x, y0 + 8, WARM_W[4])
            fc.darken(cv, x + 1, y0 + 9, 1.2)
        fc.sign_box(cv, sx0, y0, sx1, y0 + 6, sign, seed)
        restore()
        return
    door_l = noise2(seed, 1, 1920) > 0.5
    dx = x0 + 4 if door_l else x1 - 4 - SHOP_DOOR_W
    wx0, wx1 = (dx + SHOP_DOOR_W + 4, x1 - 4) if door_l else (x0 + 4, dx - 4)
    shutter = noise2(seed, 2, 1920) > 0.6
    wy0 = y0 + 12
    if wx1 - wx0 >= 8:
        riser = y1 - 7
        for y in range(riser, y1 - 1):  # the stall riser, tiled
            for x in range(wx0, wx1):
                u = x - wx0
                cv.set(x, y, '#3A3440' if y == riser else ('#6A5E70' if (u // 2 + (y - riser) // 2) % 2 else '#4E4458'))
        fc.shop_window(cv, wx0 + 1, wy0 + 1, wx1 - 1, riser, seed, WARM_W)
        for x in range(wx0, wx1):  # the frame and its mullions
            cv.set(x, wy0, METAL[4])
        for y in range(wy0, riser):
            cv.set(wx0, y, METAL[4]); cv.set(wx1 - 1, y, METAL[1])
            for x in range(wx0 + 12, wx1 - 4, 12):
                cv.set(x, y, METAL[3])
        if noise2(seed, 6, 1920) > 0.5:  # stickers on the glass
            for (sx, sy, sc) in ((wx0 + 2, riser - 4, PINK[3]), (wx1 - 4, riser - 4, CYAN[3])):
                cv.set(sx, sy, sc); cv.set(sx + 1, sy, sc); cv.set(sx, sy + 1, fc.step(sc, 1)); cv.set(sx + 1, sy + 1, fc.step(sc, 1))
        if shutter:  # the roller shutter, half down, its box above
            for y in range(wy0, wy0 + 11):
                for x in range(wx0, wx1):
                    c = METAL[4] if (y - wy0) % 2 == 0 else METAL[2]
                    if y == wy0 + 10:
                        c = METAL[1]
                    cv.set(x, y, c)
            fc.weather(cv, wx0, wx1, wy0, wy0 + 10, seed + 5, 1.5)
            for k, tx in enumerate(range(wx0 + 3, wx1 - 10, 22)):  # tags and posters on it
                if noise2(seed, k, 1927) > 0.5:
                    fc.tag(cv, tx + int(noise2(seed, k, 1928) * 6), wy0 + 2, seed + k)
                else:
                    fc.poster(cv, tx + int(noise2(seed, k, 1928) * 6), wy0 + 1, 5, 7, seed + k)
            for x in range(wx0, wx1):
                fc.darken(cv, x, wy0 + 11, 1.4)
    for y in range(dtop, y1 - 1):  # the double door: two leaves glazed above, a frame round them
        for x in range(dx, dx + SHOP_DOOR_W):
            r, col = y - dtop, x - dx
            if col in (0, SHOP_DOOR_W - 1) or r == 0:
                c = METAL[4] if col == 0 or r == 0 else METAL[2]
            elif col == SHOP_DOOR_W // 2:
                c = METAL[2]  # the meeting stiles
            elif r >= DOOR_H - 5 and col not in (1, SHOP_DOOR_W - 2):
                c = METAL[4] if r == DOOR_H - 5 else METAL[3] if (col + r) % 7 else METAL[5]  # the kick plates
            elif r >= 23 and col not in (1, SHOP_DOOR_W - 2, SHOP_DOOR_W // 2 - 1, SHOP_DOOR_W // 2 + 1):
                # a raised panel under the glass, lit on its top and west edges
                lc = (col - 2) % (SHOP_DOOR_W // 2)
                c = WOOD[4] if r == 23 or lc == 0 else WOOD[1] if r == DOOR_H - 6 or lc == SHOP_DOOR_W // 2 - 4 else WOOD[2]
            elif 3 <= r < 22 and col not in (1, SHOP_DOOR_W - 2, SHOP_DOOR_W // 2 - 1, SHOP_DOOR_W // 2 + 1):
                c = WARM_W[3] if r < 9 else WARM_W[2]  # the glass, the shop lit behind it
                if (col + r) % 13 in (3, 4):
                    c = WARM_W[4]
            else:
                c = NIGHT[1] if col > 1 else METAL[3]
            cv.set(x, y, c)
    for (l0, l1) in ((dx + 2, dx + SHOP_DOOR_W // 2 - 1), (dx + SHOP_DOOR_W // 2 + 2, dx + SHOP_DOOR_W - 2)):
        fc.shop_window(cv, l0, dtop + 3, l1, dtop + 22, seed + l0, WARM_W)  # the shop through the glass
    for side in (-1, 1):  # the push bars
        bx = dx + SHOP_DOOR_W // 2 + side * 3 - (1 if side < 0 else 0)
        cv.set(bx, dtop + 13, METAL[5]); cv.set(bx, dtop + 14, METAL[5]); cv.set(bx, dtop + 15, METAL[3])
    if noise2(seed, 8, 1920) > 0.4:  # a notice taped inside the glass
        px = dx + 3
        for y in range(dtop + 5, dtop + 9):
            for x in range(px, px + 4):
                cv.set(x, y, '#E8E2D2' if (y - dtop) % 2 else '#B8B0A0')
    if noise2(seed, 10, 1920) > 0.3:  # an open sign hung inside the door
        ox = dx + SHOP_DOOR_W // 2 + 2
        for y in range(dtop + 9, dtop + 12):
            for x in range(ox, ox + 6):
                cv.set(x, y, NIGHT[0] if y == dtop + 9 or x in (ox, ox + 5) else CYAN[3] if (x - ox) % 3 else CYAN[2])
        cv.set(ox + 1, dtop + 8, METAL[1]); cv.set(ox + 4, dtop + 8, METAL[1])
    cv.hline(dx, y1 - 2, SHOP_DOOR_W, AMBER[3])  # the light under it
    cv.hline(dx - 1, dtop - 1, SHOP_DOOR_W + 2, fc.STONE_T[5])  # the lintel
    cv.hline(dx - 1, dtop - 2, SHOP_DOOR_W + 2, fc.STONE_T[3])
    for y in range(dtop, y1 - 1):  # the door's reveal shades its frame's west side
        fc.darken(cv, dx + SHOP_DOOR_W, y, 1.4)
    # what the street leaves on the piers
    piers = [(x0, min(dx, wx0)), (max(dx + SHOP_DOOR_W, wx1), x1)]
    for (p0, p1) in piers:
        if p1 - p0 >= 6 and noise2(seed, p0, 1925) > 0.35:
            fc.poster(cv, p0 + 1, y0 + 14 + int(noise2(seed, p0, 1926) * 6), min(5, p1 - p0 - 2), 7, seed + p0)
    wide = max(piers, key=lambda p: p[1] - p[0])
    if wide[1] - wide[0] >= 5:  # a lamp over the door, or on the widest pier; the number by it
        fc.wall_lamp(cv, (wide[0] + wide[1]) // 2 - 1, y0 + 10, fc.WARM if seed % 3 else fc.COOL)
    else:
        fc.wall_lamp(cv, dx + SHOP_DOOR_W // 2 - 1, dtop - 6, fc.WARM)
    pl = piers[0] if piers[0][1] - piers[0][0] >= 7 else piers[1]
    if pl[1] - pl[0] >= 7:
        fc.plaque(cv, pl[0] + 1, y1 - 12, ('#2E5A9A', '#8A2A2A', '#2A6A4A')[seed % 3])
    if noise2(seed, 9, 1920) > 0.55 and wx1 - wx0 >= 8:  # an awning, a plane sloping out toward us
        fc.awning(cv, wx0 - 2, wx1 + 2, y0 + 7, SIGN_RAMPS[(seed + 1) % 3], 4)
    fc.sign_box(cv, sx0, y0, sx1, y0 + 7, sign, seed, face=('#0E0C16', '#2A1A14', '#14202A')[seed % 3])
    restore()
    fc.east_shade(cv, x0, x1, y0 + 6, y1)


def blade_sign(cv: Canvas, x: int, y0: int, y1: int, seed: int, ramp):
    """A vertical neon sign on brackets, standing out from the wall: a box with depth, a lit
    frame and glyphs stacked down it, a halo on its face, its shadow on the wall."""
    for by in (y0 + 2, y1 - 3):  # its brackets to the wall
        cv.hline(x - 3, by, 3, IRON[3]); cv.hline(x - 3, by + 1, 3, IRON[1])
    fc.sign_box(cv, x, y0, x + 10, y1, ramp, seed, vertical=True)


def _tiers(width: int, floors: int, depth: int, most: int, seed: int, style: str) -> list:
    """How a building fills its block (N3; to-c-city-review: "fill every block edge to
    edge"): its parts from the street back to the street behind, each (ground depth,
    floors, inset), front first. Mostly a podium of `floors` on the pavement with its
    shops and a tower rising behind it (now and then narrower, set back from both sides);
    sometimes the front block is itself the tower. Behind the tower, wings of varied
    height run on to the back of the block, so a deep block reads as a roofscape with
    faces stepping up and down, not one flat roof. The last part's roof ends exactly
    `depth` px above the foot, never beyond (two-level-walk.md rule 6)."""
    H = lambda f: f * FLOOR + SHOP
    r = lambda k: noise2(seed, k, 1990)
    fit = lambda g, f: max(1, min(f, (depth - g - 14 - SHOP) // FLOOR))  # the most floors that still fit
    parts = []
    g = 0
    podium = r(1) > 0.25 and floors < most - 1
    if podium:
        d = 10 + int(r(2) * 20)
        parts.append([d, floors, 0])
        g = d
        ft = fit(g, floors + 1 + int(r(3) * max(1, most - floors)))
        if ft <= floors:  # no room for a tower behind the podium: the podium is the building
            parts, g, podium = [], 0, False
    if not podium:
        ft = fit(0, max(floors, most // 2 + int(r(3) * (most - most // 2 + 1))))
    inset = 0
    if podium and width >= 72 and r(4) > 0.45:
        inset = 4 * (2 + int(r(5) * (width // 24)))
    dt = 26 + int(r(6) * 40)
    if inset:
        dt = min(dt, H(parts[0][1]))  # (its sides stay covered by the podium's roof)
    if g + dt + H(ft) >= depth - 30:  # the tower's roof runs on to the back of the block
        parts.append([max(12, depth - g - H(ft)), ft, inset])
        return [tuple(p) for p in parts]
    parts.append([dt, ft, inset])
    g += dt
    for k in range(8):  # the wings behind the tower
        lo = max(1, ft // 2 - 1)
        fw = lo + int(r(10 + k) * max(1, ft - lo))
        dw = 24 + int(r(20 + k) * 32)
        if g + dw + H(fw) >= depth - 40 or k == 7:
            fw = fit(g, min(most, max(fw, (depth - g - 50 - SHOP) // FLOOR)))
            parts.append([max(12, depth - g - H(fw)), fw, 0])
            break
        parts.append([dw, fw, 0])
        g += dw
    return [tuple(p) for p in parts]


BRIDGE_H = SHOP  # a skybridge's foot above the street (it lands on the front blocks' first upper floor)
BRIDGE_SILL = 9  # its deck above its sprite's foot (skybridge())


def building(width: int, floors: int, style: str = 'flats', seed: int = 0, shop: str = 'shop',
             setback: bool = False, blade: int = 0, depth: int = 0, most: int = 0, doors: tuple = ()) -> Canvas:
    """A city building in the three-quarter view: its front facing the street below it and
    its flat roof seen above it, as every building in the world is drawn. Width, floors and
    style vary (glass towers, concrete flats, old tiled walk-ups, brick and stucco), each
    with its own street floor, roof furniture and signs, so no two read alike.

    With a depth (N3), the building fills its block to the street behind: a run of parts
    (_tiers) painted from the back forward, each a face and a roof, so a podium shows its
    tower rising behind it and the roofs step back to the block's far edge. Without one it
    is a single block as before; a tall glass tower may then step back, its lower block's
    roof a terrace in front of the upper block. blade: a vertical neon sign on the west
    (-1) or east (1) side. doors: the sides ('w', 'e') where a skybridge lands."""
    if depth:
        return _tiered(width, floors, style, seed, shop, blade, depth, max(most, floors), doors)
    lobby = SHOPFRONT
    R = max(14, min(24, width // 4))  # how deep a roof we see
    upper = floors
    lower = 0
    inset = 0
    if setback and floors >= 4:
        lower = floors * 2 // 5
        upper = floors - lower
        inset = max(8, width // 6)
    Rl = 10 if lower else 0
    h = R + upper * FLOOR + Rl + lower * FLOOR + lobby + 4
    pad_l = pad_r = 0  # (a blade sign hangs on the facade, inside the building's width)
    w = width + pad_l + pad_r
    cv = Canvas(w, h, pad=PAD)
    bx0, bx1 = pad_l, pad_l + width
    ramp = METAL if style == 'glass' else CONCRETE if style == 'flats' else TILE_C
    y = 0
    _rooftop(cv, bx0 + inset, bx1 - inset, y, y + R, seed, floors >= 5, METAL if style == 'glass' else CONCRETE)
    y += R
    _facade(cv, bx0 + inset, bx1 - inset, y, y + upper * FLOOR, style, seed)
    if style == 'glass':  # a lit crown band under the parapet
        crown = SIGN_RAMPS[seed % 3]
        for x in range(bx0 + inset, bx1 - inset):
            cv.set(x, y, crown[3] if x % 4 else crown[2]); cv.set(x, y + 1, crown[1])
    y += upper * FLOOR
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
        _facade(cv, bx0, bx1, y, y + lower * FLOOR, style, seed + 3)
        y += lower * FLOOR
    for x in range(bx0, bx1):  # the cornice over the street floor
        cv.set(x, y, ramp[5] if style != 'glass' else METAL[4]); cv.set(x, y + 1, ramp[2])
    _shopfront(cv, bx0, bx1, y + 2, y + 2 + lobby, seed, 'lobby' if style == 'glass' and shop != 'shop' else shop)
    y += 2 + lobby
    for x in range(bx0, bx1):  # the plinth
        cv.set(x, y, CONCRETE[3]); cv.set(x, y + 1, CONCRETE[2])
    if blade:  # on the block it is fixed to: the lower one where the tower steps back
        sx = bx0 + 4 if blade == -1 else bx1 - 13
        if lower:
            top = R + upper * FLOOR + Rl + 4
            bottom = top + lower * FLOOR - 6
        else:
            top = R + 6
            bottom = min(h - lobby - 8, top + 12 + min(upper, 3) * 26)
        blade_sign(cv, sx, top, bottom, seed, SIGN_RAMPS[(seed + 2) % 3])
    return cv




def _tiered(width: int, floors: int, style: str, seed: int, shop: str, blade: int, depth: int, most: int,
            doors: tuple) -> Canvas:
    lobby = SHOPFRONT
    H = lambda f: f * FLOOR + SHOP
    depth = max(depth, H(1) + 12)  # (a terrace house on a shallow lot rises a little past it, as before)
    parts = _tiers(width, max(1, min(floors, (depth - 12 - SHOP) // FLOOR)), depth, most, seed, style)
    tops, g = [], 0
    for (d, f, _i) in parts:
        g += d
        tops.append(g + H(f))
    h = max(depth, max(tops))
    cv = Canvas(width, h, pad=PAD)
    roof_ramp = METAL if style == 'glass' else CONCRETE
    # each part's place: ground from g0 to g1 behind the foot; screen rows from the foot (h)
    spans, g = [], 0
    for (d, f, inset) in parts:
        spans.append((g, g + d, f, inset))
        g += d
    tallest = max(f for (_d, f, _i) in parts)
    for i in range(len(spans) - 1, -1, -1):  # back to front: a nearer part covers what it hides
        g0, g1, f, inset = spans[i]
        x0, x1 = inset, width - inset
        face_bot = h - g0
        face_top = face_bot - H(f)
        roof_top = h - g1 - H(f)
        st = style if i == 0 else _part_style(style, seed + i)
        _rooftop(cv, x0, x1, max(0, roof_top), face_top, seed + i * 7, f == tallest and f >= 5, roof_ramp)
        if i == 0:
            _facade(cv, x0, x1, face_top, face_bot - lobby - 4, st, seed)
            for x in range(x0, x1):  # the cornice over the street floor
                cv.set(x, face_bot - lobby - 4, TILE_C[5] if st == 'old' else METAL[4] if st == 'glass' else CONCRETE[5])
                cv.set(x, face_bot - lobby - 3, CONCRETE[2])
            _shopfront(cv, x0, x1, face_bot - lobby - 2, face_bot - 2, seed,
                       'lobby' if st == 'glass' and shop != 'shop' else shop)
            for x in range(x0, x1):  # the plinth
                cv.set(x, face_bot - 2, CONCRETE[3]); cv.set(x, face_bot - 1, CONCRETE[2])
        else:
            _facade(cv, x0, x1, face_top, face_bot, st, seed + 11 * i)
        if st == 'glass' and f == tallest:  # a lit crown band under the parapet
            crown = SIGN_RAMPS[seed % 3]
            for x in range(x0, x1):
                cv.set(x, face_top, crown[3] if x % 4 else crown[2]); cv.set(x, face_top + 1, crown[1])
        if i > 0:  # the nearer part's roof edge throws a strip of shade on this face's foot
            for x in range(x0, x1):
                if cv.get(x, face_bot - 1)[3]:
                    cv.set(x, face_bot - 1, _shade(cv.get(x, face_bot - 1), 3))
    # (doors: a skybridge's door is in the block's side wall, out of this view; the bridge's
    # own collar meets the corner, so nothing is painted over the facade: Matt, 20 Oct 10:15)
    sides = {side for (side, _dy) in doors}
    if (blade == -1 and 'w' in sides) or (blade == 1 and 'e' in sides):
        blade = -blade if not {'w', 'e'} <= sides else 0  # (the sign moves off the corner a skybridge lands on)
    if blade:
        f0 = parts[0][1]
        sx = 4 if blade == -1 else width - 13
        bottom = h - lobby - 10
        top = max(h - H(f0) + 6, bottom - 12 - min(f0, 3) * 26)
        if bottom - top >= 20:
            blade_sign(cv, sx, top, bottom, seed, SIGN_RAMPS[(seed + 2) % 3])
    return cv


def _part_style(style: str, seed: int) -> str:
    """A part behind the front block: mostly the same build, now and then another."""
    if style == 'glass':
        return 'glass'
    return style if noise2(seed, 0, 1991) > 0.3 else ('flats' if style != 'flats' else 'old')


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


def tram() -> Canvas:
    """A city tram waiting at its stop, 104 x 44, side on along Hill Street: a cream body
    with a teal skirt and a lit band of windows (passengers in silhouette), its doors
    open on the near side, rounded ends with a headlamp and a destination blind of
    glyphs, the roof's top lit with a pantograph up to the wire."""
    w, h = 104, 44
    cv = Canvas(w, h, pad=PAD)
    CREAM = ['#3E3A3A', '#7A746A', '#B8B0A0', '#DCD4C2', '#F2ECDC']
    TEAL = ['#0E2A2E', '#174A50', '#236E74', '#3A9AA0']
    for y in range(12, h - 3):
        r = (y - 12) / (h - 15)
        cut = int(3 * (1 - min(1.0, r * 4)) ** 2)  # the rounded ends
        for x in range(cut, w - cut):
            c = CREAM[3] if x > 3 else CREAM[4]
            if x >= w - 4:
                c = CREAM[2]
            if r > 0.72:
                c = TEAL[2] if y < h - 6 else TEAL[1]  # the skirt
            cv.set(x, y, c)
    for y in range(8, 12):  # the roof, seen from above
        for x in range(4, w - 4):
            cv.set(x, y, CREAM[4] if y < 10 else CREAM[3])
    cv.hline(4, 12, w - 8, CREAM[1])
    for x in range(6, w - 6):  # the window band
        for y in range(15, 24):
            c = WARM_W[3] if y < 18 else WARM_W[2]
            if x % 9 == 0:
                c = CREAM[1]
            cv.set(x, y, c)
    for k in range(5):  # passengers
        px = 12 + int(noise2(k, 0, 1975) * (w - 24))
        for y in range(18, 24):
            cv.set(px, y, NIGHT[1]); cv.set(px + 1, y, NIGHT[1])
        cv.set(px, 17, NIGHT[2])
    for dx in (30, 66):  # the doors, open: lit steps
        for y in range(15, h - 5):
            for x in range(dx, dx + 8):
                cv.set(x, y, WARM_W[2] if y < h - 9 else WARM_W[1])
        cv.hline(dx, h - 5, 8, CREAM[2])
    for ex in (2, w - 6):  # the ends: a blind of glyphs over the cab window, a headlamp
        cv.rect(ex, 14, 4, 3, NIGHT[0])
        cv.set(ex + 1, 15, AMBER[3]); cv.set(ex + 2, 15, AMBER[3])
        cv.set(ex + 1, 28, '#FFF6D8')
    for x in range(40, 60):  # the pantograph up to the wire
        y = 7 - abs(x - 50) // 3
        cv.set(x, y, METAL[3])
    cv.hline(44, 2, 12, METAL[4])
    for y in range(2, 8):
        cv.set(50, y, METAL[2])
    return cv


def city_car(seed: int = 0) -> Canvas:
    """A car parked at the kerb, 38 x 22, side on along the street: its roof and bonnet
    seen from above and lit, the windows dark with a streak of the street's light, a body
    colour of its own, wheels in their arches, a headlamp and a red tail light."""
    w, h = 38, 22
    cv = Canvas(w, h, pad=PAD)
    BODY = (['#5A1E2A', '#8A2E3A', '#B8485A', '#D87888'], ['#1E3A5A', '#2E5A8A', '#4A7AB0', '#78A8D8'],
            ['#4A4A50', '#6E6E78', '#9898A2', '#C4C4CC'], ['#5A4A1E', '#8A722E', '#B89A48', '#D8C078'],
            ['#1E4A3A', '#2E6A54', '#4A8E72', '#78B89A'])[seed % 5]
    for y in range(8, 18):  # the body's side
        for x in range(2, w - 2):
            c = BODY[2] if y < 11 else BODY[1]
            if x in (2, w - 3):
                c = BODY[1]
            cv.set(x, y, c)
    cv.hline(2, 8, w - 4, BODY[3])  # the shoulder line, lit
    for y in range(3, 8):  # the cabin: roof from above, windows
        for x in range(10, w - 8):
            c = BODY[3] if y < 5 else NIGHT[1]
            if y >= 5 and (x - 10) % 9 == 0:
                c = BODY[1]  # the pillars
            if y == 5 and x % 5 == 0:
                c = '#4A6A9A'  # a streak of light in the glass
            cv.set(x, y, c)
    for y in range(6, 9):  # the bonnet and the boot, from above
        for x in list(range(3, 10)) + list(range(w - 8, w - 3)):
            cv.set(x, y, BODY[3] if y == 6 else BODY[2])
    for wx in (9, w - 10):  # the wheels in their arches
        for (x, y) in disc(wx, 17, 3.2):
            cv.set(x, y, NIGHT[0] if math.hypot(x - wx, y - 17) > 1.5 else METAL[3])
    cv.set(w - 3, 11, '#FFF6D8'); cv.set(w - 3, 12, '#FFE9B0')  # the headlamp (facing east)
    cv.set(2, 11, PINK[3]); cv.set(2, 12, PINK[2])  # the tail light
    return cv


def steam_grate() -> Canvas:
    """A grate in the pavement with steam rising from it, 16 x 30 (to-c-city-review,
    "steam from grates"): the iron bars, and above them a soft column of white wisps,
    thinning and drifting east as it rises."""
    w, h = 16, 30
    cv = Canvas(w, h, pad=PAD)
    for x in range(2, 14):
        for y in range(25, 29):
            cv.set(x, y, IRON[1] if x % 2 else IRON[3])
    for y in range(2, 25):
        t = (25 - y) / 23
        cx = 8 + int(t * 3 + math.sin(y / 3.0) * 1.5)
        r = 2 + int(t * 3)
        for x in range(cx - r, cx + r + 1):
            if noise2(x, y, 1976) > 0.35 + t * 0.4:
                cv.set(x, y, (232, 238, 246, int(150 - t * 90)))
    return cv


def food_cart(seed: int = 0) -> Canvas:
    """A street-food cart, 30 x 34: a steel cart on two wheels with a lit counter and a
    steaming pot, under a striped umbrella seen from above and in front."""
    w, h = 30, 34
    cv = Canvas(w, h, pad=PAD)
    ramp = SIGN_RAMPS[seed % 3]
    for y in range(2, 10):  # the umbrella
        half = 4 + (y - 2) * 2
        for x in range(15 - half, 15 + half):
            if 0 <= x < w:
                st = ((x - 15) // 3) % 2
                cv.set(x, y, (ramp[3] if st else '#F2ECDC') if y < 8 else (ramp[1] if st else '#B8B0A0'))
    cv.vline(15, 10, 8, METAL[3])
    for y in range(18, 29):  # the cart
        for x in range(4, 26):
            c = METAL[4] if y == 18 else METAL[3] if x < 20 else METAL[2]
            if 20 <= y <= 23 and 6 <= x <= 23:
                c = WARM_W[3] if y < 22 else WARM_W[2]  # the lit counter
            cv.set(x, y, c)
    for (x, y) in disc(9, 16, 2.5):  # the pot, steaming
        cv.set(x, y, METAL[4] if y < 16 else METAL[2])
    for k in range(4):
        cv.set(8 + k % 2, 12 - k, (232, 238, 246, 140))
    for wx in (8, 22):
        for (x, y) in disc(wx, 30, 2.2):
            cv.set(x, y, NIGHT[0])
    return cv


def city_cat(seed: int = 0) -> Canvas:
    """A cat sitting on a step, 12 x 12, its tail curled round its feet, ears up."""
    cv = Canvas(12, 12, pad=PAD)
    fur = (['#2A2A30', '#3E3E46', '#56565E'], ['#8A5A2A', '#B87A3E', '#D89A5A'], ['#B8B0A8', '#D8D0C8', '#F2ECE4'])[seed % 3]
    for (x, y) in oval(6, 8, 3, 3):
        cv.set(x, y, fur[1] if x > 5 else fur[2])
    for (x, y) in disc(6, 4, 2.2):
        cv.set(x, y, fur[1] if x > 6 else fur[2])
    cv.set(4, 2, fur[0]); cv.set(8, 2, fur[0]); cv.set(4, 1, fur[1]); cv.set(8, 1, fur[1])  # ears
    cv.set(5, 4, '#C8E85A'); cv.set(7, 4, '#C8E85A')  # eyes catching the light
    cv.hline(3, 11, 7, fur[0])  # the tail round its feet
    return cv


def telescope() -> Canvas:
    """A coin telescope on the lookout, 14 x 26: a steel post on a round foot, the coin box,
    and the barrel tilted toward the city below, its eyepiece toward us, lit on top."""
    cv = Canvas(14, 26, pad=PAD)
    for y in range(12, 24):
        cv.set(6, y, METAL[4]); cv.set(7, y, METAL[2])
    cv.hline(3, 24, 8, METAL[3]); cv.hline(4, 25, 6, METAL[1])
    for y in range(9, 14):  # the coin box
        for x in range(4, 10):
            cv.set(x, y, METAL[4] if y == 9 else METAL[3] if x < 8 else METAL[1])
    cv.set(8, 11, AMBER[3])
    for k in range(9):  # the barrel, tilted down toward the city
        x, y = 2 + k, 7 - k // 3
        cv.set(x, y, METAL[5] if k < 7 else METAL[4]); cv.set(x, y + 1, METAL[3]); cv.set(x, y + 2, METAL[1])
    cv.set(1, 8, NIGHT[0]); cv.set(1, 9, NIGHT[0]); cv.set(2, 10, METAL[2])  # the eyepiece's hood
    cv.set(11, 4, CYAN[2])  # light caught in the lens
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
    """A vending machine against a wall, 22 x 31 (the scale table's 30, a head taller than
    a person): its top seen, its lit front with rows of
    cans, the coin panel, the hatch, a shaded side."""
    ramp = SIGN_RAMPS[seed % 3]
    cv = Canvas(22, 31, pad=PAD)
    for x in range(1, 21):
        for y in range(1, 4):
            cv.set(x, y, METAL[4] if y == 1 else METAL[3])
    for y in range(4, 30):
        for x in range(1, 18):
            c = ramp[2] if x < 3 else ramp[1]
            if 6 <= y < 21 and 3 <= x < 13:
                c = '#E8F4FF' if (y - 6) % 4 == 0 else (ramp[3], AMBER[3], CYAN[3], '#E8E2D2')[(x + (y // 4)) % 4]
            if 6 <= y < 21 and x in (13, 14, 15, 16):
                c = METAL[2] if (y % 3) else METAL[4]
            if y >= 23 and 4 <= x < 14:
                c = NIGHT[0] if y < 27 else METAL[2]
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
    """A skybridge across a street, width x 46, in the world's three-quarter view (Matt's
    World Logic answer 17: keep it as scenery, make it realistic). How it is built: a
    steel Warren truss a storey deep spans from block to block, its top and bottom chords
    I-beams bolted at every panel point, its diagonals outside the glass; the walkway's
    concrete deck rides on the bottom chord, a standing-seam roof with a gutter on the top
    chord, glazing between. Through the near glass we see the lit inside: the ceiling with
    a light fitting in every bay, the far glazing dark with the night beyond, the handrail,
    the floor lit in pools, people crossing upright. At each end a steel portal frame
    (a collar) seals the tube against the block's side wall where its door is, warm light
    spilling onto the floor from the open door, and the collar sits 4 px over the block's
    corner so the bridge reads as carried by the block. Under the deck a row of downlights
    for the street. Its deck is BRIDGE_SILL above its foot."""
    w, h = width, 46
    cv = Canvas(w, h, pad=PAD)
    C = 7  # the collar's width at each end
    floor = h - BRIDGE_SILL - 1  # the walkway's floor row (people stand on it)
    bay = 12
    inner = w - 2 * C
    n = max(2, round(inner / bay))
    edges = [C + round(i * inner / n) for i in range(n + 1)]  # panel points, end to end
    # the roof seen from above: a standing seam every 4 px, lit on its upper-left
    for y in range(0, 6):
        for x in range(C - 1, w - C + 1):
            c = METAL[3] if y < 2 else METAL[2]
            if (x - C) % 4 == 0:
                c = METAL[4] if y < 3 else METAL[3]  # the seams catch the light
            if y == 0:
                c = METAL[4]
            cv.set(x, y, c)
    for x in range(C - 1, w - C + 1):  # the gutter along the eave
        cv.set(x, 6, METAL[5] if x % 9 else METAL[4]); cv.set(x, 7, METAL[1])
    top, bot = 8, floor + 1  # the top chord's row and the bottom chord's top row
    gl0, gl1 = top + 2, floor  # the glazing between the chords
    for x in range(C, w - C):
        for y in range(gl0, gl1):
            # inside, through the near glass: the ceiling, the far glazing, the floor's lit wall foot
            if y < gl0 + 3:
                c = CONC_[1] if y == gl0 else CONC_[2]
            elif y < gl0 + 15:
                c = '#101A30' if y < gl0 + 6 else '#14203A' if y < gl0 + 10 else '#1A2A48'  # the far glass, the night beyond
            elif y == gl0 + 15:
                c = METAL[4]  # the handrail along the far side
            elif y == gl0 + 16:
                c = METAL[1]
            else:
                c = WARM_W[1] if y < gl1 - 3 else WARM_W[2]  # the far side's lit kick panels
            cv.set(x, y, c)
    for i in range(n):  # through the far glass, the city beyond: lit windows of the blocks behind, 2 x 2
        for j in range(3):
            wx = edges[i] + 3 + int(noise2(seed * 7 + i, j, 1973) * (edges[i + 1] - edges[i] - 6))
            wy = gl0 + 5 + int(noise2(seed * 7 + i, j, 1974) * 7)
            c = (WARM_W[2], COOL_W[2], WARM_W[1], '#3A4E78')[int(noise2(seed + i, j, 1975) * 4)]
            for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                cv.set(wx + dx, wy + dy, c)
        for x in range(edges[i] + 2, edges[i + 1]):  # the floor's tiles, two tones a tile
            if (x // 3) % 2:
                cv.set(x, gl1 - 4, WARM_W[0])
    for i in range(n):  # in every bay a light fitting and its pool on the floor
        mx = (edges[i] + edges[i + 1]) // 2
        cv.hline(mx - 2, gl0 + 2, 5, WARM_W[4]); cv.hline(mx - 1, gl0 + 3, 3, WARM_W[3])
        for dx in range(-4, 5):
            cv.set(mx + dx, gl1 - 1, WARM_W[3] if abs(dx) < 3 else WARM_W[2])
            if abs(dx) < 2:
                cv.set(mx + dx, gl1 - 2, WARM_W[3])
        for (dx, dy) in ((-5, 6), (-4, 7), (3, 5), (4, 6)):  # the far glass mirrors the fitting
            cv.set(mx + dx, gl0 + dy, '#2A3C5E')
    for end in (C, w - C - 1):  # the open doors' light, spilling along the floor from each end
        d = 1 if end == C else -1
        for k in range(10):
            for y in range(gl1 - 5 + k // 4, gl1):
                c = WARM_W[3] if k < 5 else WARM_W[2]
                if cv.get(end + d * k, y)[:3] != (255, 233, 176):
                    cv.set(end + d * k, y, c)
        for y in range(gl0 + 3, gl1):  # the doorway's jamb, seen in the side wall's plane
            cv.set(end + 2 * d, y, WARM_W[4] if y > gl0 + 6 else WARM_W[3])
            cv.set(end + 3 * d, y, WARM_W[3] if y > gl0 + 6 else WARM_W[2])
    coats = (CONCRETE_BLUE, PINK, CYAN, CONCRETE_SAND, AMBER)
    skins = (('#E0A882', '#B07858'), ('#A87050', '#7A4C34'), ('#F0C8A0', '#C89A74'))
    for k in range(3):  # people crossing, upright, lit by the ceiling: coat, legs, face, hair
        px = C + 6 + k * (inner - 12) // 3 + int(noise2(seed, k, 1970) * max(1, (inner - 12) // 3 - 6))
        coat = coats[int(noise2(seed, k, 1971) * len(coats))]
        skin = skins[int(noise2(seed, k, 1972) * len(skins))]
        head = gl1 - 23
        for y in range(head + 5, gl1):
            if y < head + 15:  # the coat, lit on its upper-left side
                for dd in range(-1, 3):
                    cv.set(px + dd, y, coat[3] if dd == -1 and y < head + 10 else coat[2] if dd < 2 else coat[1])
                cv.set(px + 3 if (seed + k) % 2 else px - 2, y, coat[1]) if head + 6 <= y < head + 13 else None  # an arm
            else:  # the legs, a stride
                stride = (seed + k) % 2 and y > head + 18
                for dd in ((-1, 2) if stride else (0, 1)):
                    cv.set(px + dd, y, NIGHT[1] if dd < 1 else NIGHT[0])
        for (x, y) in disc(px + 1, head + 2, 2.2):
            cv.set(x, y, skin[0] if x <= px + 1 and y >= head + 1 else skin[1])
        cv.hline(px, head, 3, NIGHT[0])  # hair
        cv.set(px - 1, head + 1, NIGHT[0])
    # the truss outside the glass: mullions at the panel points, a diagonal across each bay
    for i, ex in enumerate(edges):
        for y in range(gl0, gl1):
            cv.set(ex, y, METAL[4]); cv.set(ex + 1, y, METAL[2])
    for i in range(n):
        x0, x1 = edges[i] + 2, edges[i + 1] - 1
        rising = i % 2 == 0
        for y in range(gl0, gl1):
            t = (y - gl0) / max(1, gl1 - gl0 - 1)
            xx = round(x0 + (1 - t if rising else t) * (x1 - x0 - 1))
            cv.set(xx, y, METAL[3]); cv.set(xx + 1, y, METAL[1])
        for y in range(gl0 + 1, gl1 - 1, 7):  # a streak of glare on the near pane, upper-left light
            gx = edges[i] + 3 + (y - gl0) // 4
            if gx + 1 < edges[i + 1] and cv.get(gx, y)[:3] != tuple(int(METAL[3][k:k + 2], 16) for k in (1, 3, 5)):
                cv.set(gx, y, '#3A5274' if y < gl0 + 15 else WARM_W[3])
    for x in range(C, w - C):  # the chords: I-beams, the flange lit, the web in shade, bolts at the panel points
        cv.set(x, top, METAL[5]); cv.set(x, top + 1, METAL[2])
        cv.set(x, bot, METAL[4]); cv.set(x, bot + 1, METAL[3]); cv.set(x, bot + 2, METAL[1])
        cv.set(x, bot + 3, CONC_[4]); cv.set(x, bot + 4, CONC_[3]); cv.set(x, bot + 5, CONC_[2])  # the deck slab's edge
        cv.set(x, bot + 6, CONC_[0])
    for ex in edges:  # gusset plates where the members meet
        for (dx, yy) in ((-1, top + 1), (2, top + 1), (-1, bot + 1), (2, bot + 1)):
            cv.set(ex + dx, yy, METAL[4])
        cv.set(ex, bot + 1, METAL[5]); cv.set(ex, top + 1, METAL[5])
    for i in range(n):  # the downlights under the deck, for the street below
        mx = (edges[i] + edges[i + 1]) // 2
        cv.hline(mx - 1, bot + 7, 3, CONC_[1]); cv.set(mx, bot + 7, CYAN[4])
    # the collars: a steel portal at each end, standing proud of the tube, bolted to the block
    for side in (0, 1):
        xa = 0 if side == 0 else w - C
        for x in range(xa, xa + C):
            k = x - xa if side == 0 else xa + C - 1 - x  # 0 at the wall, C-1 at the tube
            for y in range(0, bot + 7):
                c = METAL[3]
                if x == xa:
                    c = METAL[5]  # the lit left edge
                elif x == xa + C - 1:
                    c = METAL[1]
                elif y < 2:
                    c = METAL[4]
                elif k in (1, 2):
                    c = METAL[2]  # the flashing sealed against the wall
                if (y - 3) % 9 == 0 and x == xa + C // 2:
                    c = METAL[5]  # bolt heads
                elif (y - 3) % 9 == 1 and x == xa + C // 2:
                    c = METAL[0]
                cv.set(x, y, c)
            cv.set(x, bot + 7, METAL[0])
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
    ('towerrow', [(480, 404), (486, 520), (478, 720), (482, 880), (480, 1110)], 12, 16, 1),  # (a boulevard: wide pavements, trees)
    ('quayroad', [(QUAY_X - 40, 40), (QUAY_X - 40, 600), (QUAY_X - 60, 700), (QUAY_X - 60, 1060), (QUAY_X - 54, 1400)],
     12, 6, 1),
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
# of its foot, the district's style mix, the most upper floors over the shop storey).
# At the scale table's 32 px storeys (verticality.md section 5) the old 12 to 32 floor
# towers are blocks of three to seven storeys; downtown's glass towers are the tallest.
FRONTAGES = [
    ('hill', 300, 780, 'top', ('glass', 'flats', 'old'), 6),
    ('cable', -10, 150, 'hill', ('flats', 'old'), 6),
    ('cable_e', 490, 744, 'hill', ('flats', 'glass', 'old'), 6),
    ('market', -10, 150, 'cable', ('old', 'flats'), 5),
    ('market', 180, 470, 'hill', ('glass',), 9),
    ('market', 490, 744, 'cable_e', ('glass', 'flats'), 5),
    ('terminal', -10, 640, 'market', ('glass', 'flats', 'old'), 5),
    ('harbour', -10, 318, 'terminal', ('flats', 'old'), 4),
    ('rim1', 0, 300, 'rim2', ('old', 'flats'), 1),
    ('rim2', 0, 300, 'top', ('old', 'flats'), 2),
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
    if y0 < pcy + pry and y1 > pcy - pry:  # (a building may face the square, never stand in it)
        dy = 0 if y0 <= pcy <= y1 else min(abs(y0 - pcy), abs(y1 - pcy))
        half = prx * math.sqrt(max(0.0, 1 - (dy / pry) ** 2))
        if half > 0:
            out.append((pcx - half - 4, pcx + half + 4))
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

                def back(xx):  # the back of the block at xx: the street behind, or the square's edge
                    b = street_y(behind, xx) + bhw + bpw + 2
                    if abs(xx - pcx) < prx + 4 and foot > pcy + pry:
                        b = max(b, pcy + pry * math.sqrt(max(0.0, 1 - min(1.0, abs(xx - pcx) / (prx + 4)) ** 2)) + 6)
                    return b
                limit = foot - max(back(xx) for xx in range(int(x), int(x + w) + 1, 4))
            limit = int(limit)
            tall = limit
            blocked = _ns_blocked(foot - tall, foot, foot)
            ahead = [r[0] for r in blocked if r[0] > x]  # (where the next street cuts this frontage)
            stop = min([xb] + ahead)
            clash = [r for r in blocked if x < r[1] and x + w > r[0]]
            on_corner = bool(clash) or (x > xa and any(abs(x - 2 - r[1]) < 3 for r in blocked))
            if clash:
                room_w = int(min(r[0] for r in clash) - x) - 2
                if room_w >= 32 and min(r[0] for r in clash) > x:
                    w = room_w - room_w % 4
                else:
                    x = max(r[1] for r in clash) + 2
                    continue
            if x + w > xb:
                w = int(xb - x)
                w -= w % 4
                if w < 36:
                    break
            if 0 < stop - (x + w) < 48:
                w = int(stop - x) - int(stop - x) % 4  # (no sliver left at the block's end)
            on_corner = on_corner or stop - (x + w) < 4 and stop < xb
            style = styles[int(noise2(n, 2, 1950) * len(styles))]
            floors = 1 + int(noise2(n, 3, 1950) * 3)  # the front block on the pavement: two to four storeys
            if on_corner and limit >= 160:
                floors = max(floors, 2)  # (a corner block stands tall enough to carry a skybridge)
            if most <= 3:
                floors = min(floors, most)
            if style == 'glass' and limit < 200:
                style = 'flats'
            blade = 0 if style == 'glass' else (-1 if noise2(n, 5, 1950) < 0.25 else 1 if noise2(n, 5, 1950) > 0.7 else 0)
            spec = (w, floors, style, 2000 + n, 'shop', False, blade, limit, most)
            out.append((f'city_b{n}', spec, int(x + w / 2), int(foot)))
            n += 1
            k += 1
            x += w + (10 if noise2(n, 6, 1950) > 0.85 else 0)  # (party walls, an alley now and then)
    return out


@functools.lru_cache(maxsize=1)
def city_skybridges() -> list:
    """The skybridges: where two blocks of three storeys or more face each other across a
    north-south street on the same frontage, an enclosed walkway joins them at their
    first upper floor, landing in each (key, width, foot x of its middle, foot y, height)."""
    out = []
    bs = city_buildings()
    pairs = []
    for (k1, s1, x1, y1) in bs:
        for (k2, s2, x2, y2) in bs:
            r1, l2 = x1 + s1[0] // 2, x2 - s2[0] // 2
            street = any(r1 - 4 <= (a + b) / 2 <= l2 + 4 for (a, b) in _ns_blocked(y1 - 40, y1, y1))
            if k1 != k2 and abs(y1 - y2) <= 12 and s1[1] >= 2 and s2[1] >= 2 and 40 <= l2 - r1 <= 110 and street:
                pairs.append(((k1, s1, x1, y1), (k2, s2, x2, y2)))
    for (k1, s1, x1, y1), (k2, s2, x2, y2) in pairs:
        r1, l2 = x1 + s1[0] // 2, x2 - s2[0] // 2
        gap = l2 - r1
        h = BRIDGE_H  # the first upper floor, above the street
        out.append((f'skybridge_{len(out)}', gap + 8, (r1 + l2) // 2, max(y1, y2), h))
    return out


def _bridge_doors() -> dict:
    """Where a skybridge lands on a building: {key: ((side, dy), ...)}, side 'w' or 'e', dy
    how far below the building's foot the bridge's foot row lies."""
    out: dict = {}
    bs = {key: (spec, x, y) for (key, spec, x, y) in city_buildings()}
    for (bkey, w, mx, my, _h) in city_skybridges():
        for key, (spec, x, y) in bs.items():
            if abs(y - my) <= 24 and abs((x + spec[0] // 2) - (mx - w // 2 + 4)) <= 2:
                out[key] = out.get(key, ()) + (('e', my - y),)
            if abs(y - my) <= 24 and abs((x - spec[0] // 2) - (mx + w // 2 - 4)) <= 2:
                out[key] = out.get(key, ()) + (('w', my - y),)
    return out


def city_props() -> dict[str, Canvas]:
    """The city's own props: its buildings (each its own sprite), its skybridges, its street
    furniture, the market, the plaza, the quays."""
    doors = _bridge_doors()
    out = {key: building(*spec, doors=doors.get(key, ())) for (key, spec, _x, _y) in city_buildings()}
    out.update({key: skybridge(w, seed=k) for k, (key, w, _x, _y, _h) in enumerate(city_skybridges())})
    out.update({
        'city_lamp': city_lamp(), 'city_street_tree': street_tree(0), 'city_street_tree_b': street_tree(1), 'city_tree_planted': street_tree(2, pit=False),
        'city_bench': city_bench(), 'city_telescope': telescope(), 'city_tram': tram(),
        'city_car': city_car(0), 'city_car_b': city_car(1), 'city_car_c': city_car(2), 'city_car_d': city_car(3),
        'city_car_e': city_car(4), 'city_steam': steam_grate(), 'city_food_cart': food_cart(0),
        'city_food_cart_b': food_cart(1), 'city_cat': city_cat(0), 'city_cat_b': city_cat(1), 'city_cat_c': city_cat(2),
        'city_bike_rack': bike_rack(), 'city_litter_bin': litter_bin(), 'city_quay_bollard': bollard(),
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
