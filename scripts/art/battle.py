"""DS-style battle backdrop and fighter platforms for NapAttack.

Run: python3 scripts/art/battle.py
Writes assets/battle/{backdrop-day,backdrop-night,platform}.png (6x nearest).
The backdrop is anchored to the stage's bottom edge; fighters' feet stand
FEET native pixels above it, which is where the platforms are centred.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval, smooth_noise  # noqa: E402
import garden  # noqa: E402  (reuse the garden's trees so both worlds match)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'battle')
os.makedirs(OUT, exist_ok=True)
W, H = 216, 150
FEET = 24
SCALE = 6

DAY = {
    'sky': ['#A9D3E6', '#C3E0EA', '#DCEBE6', '#EEF2DF'],
    'cloud': ['#FFFFFF', '#E9F1F2', '#C9DCE3'],
    'hill_far': ['#A7C7B4', '#97BBA6'],
    'hill_near': ['#7FB07A', '#6E9F6B'],
    'grass': garden.G,
    'sun': '#FFF3C4',
}
NIGHT = {
    'sky': ['#1A2142', '#252E55', '#323C66', '#434C74'],
    'cloud': ['#5A6390', '#4A5280', '#3A4270'],
    'hill_far': ['#2E3D58', '#283650'],
    'hill_near': ['#2D4A45', '#27413D'],
    'grass': ['#1D3A33', '#27493C', '#2F5845', '#3A6650', '#4F7B5E'],
    'sun': '#F6E7A8',
}


def backdrop(pal, night=False) -> Canvas:
    cv = Canvas(W, H)
    horizon = 78
    # sky: stepped gradient with a dithered row between steps
    bands = pal['sky']
    for y in range(horizon):
        i = min(len(bands) - 1, int(y / horizon * len(bands)))
        cv.hline(0, y, W, bands[i])
        if i and y == int(i * horizon / len(bands)):
            for x in range(0, W, 2):
                cv.set(x + (y % 2), y, bands[i - 1])
    # sun or moon
    if night:
        for (x, y) in oval(170, 20, 7, 7):
            if (x - 173) ** 2 + (y - 18) ** 2 > 30:
                cv.set(x, y, pal['sun'])
        for i in range(40):
            x, y = int(noise2(i, 1, 90) * W), int(noise2(i, 2, 90) * 60)
            cv.set(x, y, '#E8E6F2' if i % 4 else '#FFF6C8')
    else:
        for (x, y) in oval(172, 22, 9, 9):
            cv.set(x, y, pal['sun'])
        for (x, y) in oval(172, 22, 12, 12):
            if cv.get(x, y)[:3] != (255, 243, 196):
                cv.set(x, y, (255, 250, 230, 90))
    # clouds: puffy pixel clusters with a shaded underside
    for (cx, cy, s) in ((30, 22, 1.0), (92, 14, 0.8), (140, 34, 0.7), (205, 12, 0.6)):
        blob = set()
        for (dx, dy, r) in ((0, 0, 7), (8, -3, 6), (15, 0, 6), (-7, 1, 5), (22, 2, 4)):
            blob |= {(x, y) for (x, y) in oval(cx + dx * s, cy + dy * s, r * s * 1.4, r * s)}
        for (x, y) in blob:
            under = (x, y + 2) not in blob
            cv.set(x, y, pal['cloud'][2] if under else pal['cloud'][1] if (x, y - 2) in blob else pal['cloud'][0])
    # far hills, near hills
    for x in range(W):
        h1 = horizon - 14 - int(8 * math.sin(x / 23) + 5 * math.sin(x / 9 + 1))
        h2 = horizon - 6 - int(6 * math.sin(x / 17 + 2) + 3 * math.sin(x / 7))
        for y in range(h1, horizon):
            cv.set(x, y, pal['hill_far'][0] if y > h1 + 1 else pal['hill_far'][1])
        for y in range(h2, horizon + 2):
            cv.set(x, y, pal['hill_near'][0] if y > h2 + 1 else pal['hill_near'][1])
    # distant tree line: small pines and round trees, set back behind the near hills
    far = ['#4E7F5A', '#3E6E4E', '#2F5A40'] if not night else ['#24413A', '#1E3832', '#182E2A']
    for i, x in enumerate(range(-4, W + 6, 7)):
        base = horizon - 4 + (i % 3)
        if i % 4 == 1:  # round tree
            for (px, py) in oval(x, base - 7, 4.5, 4.5):
                lit = (px - x) + (py - (base - 7)) < 0
                cv.set(px, py, far[0] if lit else far[1])
            cv.vline(x, base - 3, 3, '#5A4632' if not night else '#2A2420')
        else:  # pine
            hgt = 12 + (i * 5) % 6
            for k in range(hgt):
                half = int(k * 0.42) + 1
                for px in range(x - half, x + half + 1):
                    cv.set(px, base - hgt + k, far[0] if px < x else far[1] if px > x else far[2] if k % 4 == 3 else far[1])
    # near hills overlap the tree bases for depth
    for x in range(W):
        h3 = horizon - 2 - int(3 * math.sin(x / 13 + 4) + 2 * math.sin(x / 5))
        for y in range(h3, horizon + 5):
            cv.set(x, y, pal['hill_near'][0] if y > h3 + 1 else pal['hill_near'][1])
    # meadow: textured grass, darker toward the viewer for depth
    g = pal['grass']
    for y in range(horizon + 4, H):
        depth = (y - horizon) / (H - horizon)
        for x in range(W):
            n = smooth_noise(x, y, 14, 7)
            base = g[3] if n < 0.55 - depth * 0.25 else g[2]
            cv.set(x, y, base)
    for i in range(160):  # tufts, bigger near the bottom
        x = int(noise2(i, 5, 31) * W)
        y = horizon + 6 + int(noise2(i, 6, 31) * (H - horizon - 8))
        big = y > H - 40
        cv.set(x, y, g[1]); cv.set(x + 2, y, g[1]); cv.set(x + 1, y + 1, g[1])
        if big:
            cv.set(x, y - 1, g[1]); cv.set(x + 2, y - 1, g[4] if not night else g[3])
        if i % 9 == 0 and not night:
            cv.set(x + 4, y - 1, ['#F2D16B', '#FBF4E4', '#CFC4EC'][i % 3])
    # a worn path receding into the distance between the fighters
    for y in range(horizon + 4, H):
        t = (y - horizon) / (H - horizon)
        half = 1.5 + t * 8
        cx = W / 2 + math.sin(y / 11) * 2
        for x in range(int(cx - half), int(cx + half) + 1):
            edge = abs(x - cx) > half - 1.2
            col = garden.P[1] if edge else garden.P[3] if smooth_noise(x, y, 5, 3) > 0.6 else garden.P[2]
            if night:
                col = '#4E4A5A' if edge else '#5E5A6A'
            cv.set(x, y, col)
    return cv


def platform() -> Canvas:
    """Oval grassy mound under each fighter: bright top, 3px dirt side, soft shadow."""
    w, h = 64, 20
    cv = Canvas(w, h)
    cx = w / 2
    for (x, y) in oval(cx, 13, 32, 6):
        cv.set(x, y, (40, 52, 36, 80))
    side = oval(cx, 10, 30, 7)
    for (x, y) in side:
        cv.set(x, y, garden.P[0] if y > 12 else garden.P[1])
    top = oval(cx, 7.5, 29.5, 6)
    for (x, y) in top:
        u, v = (x + 0.5 - cx) / 29.5, (y + 0.5 - 7.5) / 6
        r = u * u + v * v
        col = garden.G[3]
        if r > 0.82:
            col = garden.G[2] if v > 0 else garden.G[4]  # rim: lit back edge, shaded front edge
        elif -u * 0.4 - v * 0.9 > 0.45:
            col = garden.G[4]
        cv.set(x, y, col)
    for i in range(16):
        x = int(cx - 24 + noise2(i, 1, 77) * 48)
        y = int(4 + noise2(i, 2, 77) * 7)
        if (x, y) in top and (x + 2, y) in top:
            cv.set(x, y, garden.G[2]); cv.set(x + 2, y, garden.G[2]); cv.set(x + 1, y + 1, garden.G[2])
    cv.outline('#3E5A2E')
    return cv


def main():
    backdrop(DAY).save(os.path.join(OUT, 'backdrop-day.png'), SCALE)
    backdrop(NIGHT, night=True).save(os.path.join(OUT, 'backdrop-night.png'), SCALE)
    platform().save(os.path.join(OUT, 'platform.png'), SCALE)
    prev = backdrop(DAY)
    p = platform()
    prev.paste(p, 46 - 32, H - FEET - 8)
    prev.paste(p, W - 46 - 32, H - FEET - 8)
    prev.save('/tmp/battle-preview.png', 4)
    print('ok', W, H)


if __name__ == '__main__':
    main()
