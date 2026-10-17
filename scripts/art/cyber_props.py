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


def props() -> dict[str, Canvas]:
    return {
        'tower_pink': tower(112, 150, 0, PINK), 'tower_cyan': tower(96, 136, 1, CYAN),
        'tower_amber': tower(104, 142, 2, AMBER), 'noodle_stall': noodle_stall(),
        'vending_machine': vending_machine(), 'street_light': street_light(), 'holo_board': holo_board(),
        'drone': drone(), 'cable_pole': cable_pole(), 'shelter': shelter(), 'uv_planter': uv_planter(),
        'containers': containers(), 'ferry': ferry(),
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
