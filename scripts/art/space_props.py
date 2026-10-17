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
from materials import MATERIALS, LEAF, NAP, GOLD, RED, WTR  # noqa: E402

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


def props_station() -> dict[str, Canvas]:
    return {'garden_pod': garden_pod(), 'viewport': viewport(), 'sleep_pod': sleep_pod(), 'airlock': airlock(),
            'console': console()}


def props_lumen() -> dict[str, Canvas]:
    return {'moon_shrub': moon_shrub(), 'moon_crystal': moon_crystal(), 'shuttle': shuttle(), 'dream_pool': dream_pool()}


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
