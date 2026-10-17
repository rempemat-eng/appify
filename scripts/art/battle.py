"""The battle field as a close-up of the world (coherence plan, step 7b).

Run: python3 scripts/art/battle.py
Writes assets/battle/:
  sky-{day,night}.png    the sky with clouds and the sun or moon (still)
  far-{day,night}.png    hills and the distant treeline (a parallax layer)
  near-{day,night}.png   the meadow, the framing trees and the worn path (front layer)
  platform{,-night}.png  the raised mound each fighter stands on
  backdrop-{day,night}.png  all three layers flattened (the garden's tilt view)

Everything is drawn with the garden's material detail rules (scripts/art/detail.py)
and lit from the upper left. The app shows the field at a whole-number zoom of the
shared pixel grid, so the fighters, the field and the platforms share one pixel size.
Layers are exported at 4x; the night versions are the day art in moonlight.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
import style  # noqa: E402
from materials import G, LEAF, P, SOIL, STONE, WOOD  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'battle')
os.makedirs(OUT, exist_ok=True)
W, H = 216, 150
HORIZON = 78
FEET = 24  # the fighters' feet stand this many native pixels above the bottom edge
SCALE = 4
PLATFORM_W, PLATFORM_H = 48, 18

SKY_DAY = ['#A9D3E6', '#C3E0EA', '#DCEBE6', '#EEF2DF']
SKY_NIGHT = ['#1A2142', '#252E55', '#323C66', '#434C74']
CLOUD_DAY = ['#FFFFFF', '#E9F1F2', '#C9DCE3']
CLOUD_NIGHT = ['#5A6390', '#4A5280', '#3A4270']
HILL_FAR = ['#97BBA6', '#A7C7B4', '#B9D3C2']
HILL_NEAR = ['#6E9F6B', '#7FB07A', '#93BF88']
TREELINE = ['#2F5A40', '#3E6E4E', '#4E7F5A']


def moonlight(cv: Canvas) -> Canvas:
    """The same art under the moon: darker, cooler, blue-shifted (alpha kept)."""
    out = Canvas(cv.w, cv.h)
    for y in range(cv.h):
        for x in range(cv.w):
            r, g, b, a = cv.get(x, y)
            if a:
                out.px[x, y] = (int(r * 0.4), int(g * 0.48), int(b * 0.7 + 14), a)
    return out


def sky(night: bool) -> Canvas:
    cv = Canvas(W, H)
    bands = SKY_NIGHT if night else SKY_DAY
    for y in range(H):
        i = min(len(bands) - 1, int(min(y, HORIZON) / HORIZON * len(bands)))
        cv.hline(0, y, W, bands[i])
        if i and y == int(i * HORIZON / len(bands)):
            for x in range(0, W, 2):
                cv.set(x + (y % 2), y, bands[i - 1])
    if night:
        for (x, y) in oval(170, 20, 7, 7):
            if (x - 173) ** 2 + (y - 18) ** 2 > 30:
                cv.set(x, y, '#F6E7A8')
        for i in range(44):
            x, y = int(noise2(i, 1, 90) * W), int(noise2(i, 2, 90) * 60)
            cv.set(x, y, '#E8E6F2' if i % 4 else '#FFF6C8')
    else:
        for (x, y) in oval(172, 22, 12, 12):
            cv.set(x, y, (255, 250, 230, 90))
        for (x, y) in oval(172, 22, 9, 9):
            cv.set(x, y, '#FFF3C4')
        for (x, y) in oval(169.5, 19.5, 4, 4):
            cv.set(x, y, '#FFFBE6')
    cloud = CLOUD_NIGHT if night else CLOUD_DAY
    for (cx, cy, s) in ((30, 22, 1.0), (92, 14, 0.8), (140, 36, 0.7), (205, 12, 0.6)):
        blob = set()
        for (dx, dy, r) in ((0, 0, 7), (8, -3, 6), (15, 0, 6), (-7, 1, 5), (22, 2, 4)):
            blob |= {(x, y) for (x, y) in oval(cx + dx * s, cy + dy * s, r * s * 1.4, r * s)}
        for (x, y) in blob:
            under = (x, y + 2) not in blob
            cv.set(x, y, cloud[2] if under else cloud[1] if (x, y - 2) in blob else cloud[0])
    return cv


def far() -> Canvas:
    """Rolling hills lit on their left slopes, and a distant treeline of small pines and
    round trees set back behind the nearer hill."""
    cv = Canvas(W, H)
    for x in range(W):
        h1 = HORIZON - 16 - int(8 * math.sin(x / 23) + 5 * math.sin(x / 9 + 1))
        slope = math.cos(x / 23) * 8 / 23 + math.cos(x / 9 + 1) * 5 / 9
        for y in range(h1, HORIZON + 4):
            t = 2 if y == h1 else 1 if slope > 0 else 0
            cv.set(x, y, HILL_FAR[t])
    for i, x in enumerate(range(-4, W + 6, 7)):
        base = HORIZON - 4 + (i % 3)
        if i % 4 == 1:
            for (px, py) in oval(x, base - 7, 4.5, 4.5):
                lit = (px - x) + (py - (base - 7)) < -1
                cv.set(px, py, TREELINE[2] if lit else TREELINE[1] if px <= x + 1 else TREELINE[0])
            cv.vline(x, base - 3, 3, WOOD[1])
        else:
            hgt = 12 + (i * 5) % 6
            for k in range(hgt):
                half = int(k * 0.42) + 1
                for px in range(x - half, x + half + 1):
                    t = 2 if px < x else 0 if px > x else 1
                    if k % 4 == 3:
                        t = max(0, t - 1)
                    cv.set(px, base - hgt + k, TREELINE[t])
    for x in range(W):
        h2 = HORIZON - 4 - int(3 * math.sin(x / 13 + 4) + 2 * math.sin(x / 5))
        slope = math.cos(x / 13 + 4) * 3 / 13 + math.cos(x / 5) * 2 / 5
        for y in range(h2, HORIZON + 6):
            t = 2 if y == h2 else 1 if slope > 0 else 0
            cv.set(x, y, HILL_NEAR[t])
    return cv


def near() -> Canvas:
    """The meadow the fighters stand in: grass masses, tufts larger toward the viewer,
    a worn path receding between them, and trees framing both edges with shadows."""
    cv = Canvas(W, H)
    top = HORIZON + 4
    for y in range(top, H):
        depth = (y - top) / (H - top)
        for x in range(W):
            n = smooth_noise(x, y, 14, 7)
            light = n < 0.55 - depth * 0.25 or (n < 0.58 - depth * 0.25 and (x + y) % 2 == 0)
            cv.set(x, y, G[3] if light else G[2])
    for x in range(W):  # the meadow's far edge meets the hills with a darker lip
        cv.set(x, top, G[1])
    # the worn path, packed earth with pebbles and a darker rim
    path = set()
    for y in range(top + 1, H):
        t = (y - top) / (H - top)
        half = 1.5 + t * 9
        cx = W / 2 + math.sin(y / 11) * 2
        for x in range(int(cx - half), int(cx + half) + 1):
            path.add((x, y))
    for (x, y) in path:
        n = smooth_noise(x, y, 5, 3)
        cv.set(x, y, P[4] if n > 0.62 else P[3])
    detail.grass_edge(cv, path, G, P, seed=21)
    for i in range(14):
        y = top + 8 + int(noise2(i, 3, 12) * (H - top - 10))
        x = int(W / 2 + (noise2(i, 4, 12) - 0.5) * (2 + (y - top) / (H - top) * 12))
        if (x - 1, y) in path and (x + 2, y + 1) in path:
            detail.pebble(cv, x, y, STONE, big=y > H - 30)
    # tufts, larger toward the viewer
    for ty in range(top + 4, H, 5):
        for tx in range(0, W, 6):
            x = tx + int(noise2(tx, ty, 4) * 6)
            y = ty + int(noise2(tx, ty, 5) * 5)
            if (x, y) in path or noise2(tx, ty, 3) > 0.42:
                continue
            ground = 3 if cv.get(x, y)[:3] == tuple(int(G[3][k:k + 2], 16) for k in (1, 3, 5)) else 2
            near_kinds = (1, 2, 4) if y > H - 40 else (0, 3, 5)
            detail.grass_tuft(cv, x, y, near_kinds[int(noise2(tx, ty, 8) * 3)], G, ground)
            if noise2(tx, ty, 9) < 0.08:
                cv.set(x + 3, y - 1, ['#F2D16B', '#FBF4E4', '#CFC4EC'][int(noise2(tx, ty, 10) * 3)])
    # trees framing the field, with silhouette shadows down and to the right
    for (tx, ty, sprite) in ((-10, HORIZON - 30, gp.tree(True)), (194, HORIZON - 24, gp.tree(False)),
                             (182, HORIZON - 34, gp.pine()), (14, HORIZON - 26, gp.pine())):
        s = style.finalize(sprite, name='battle-tree')
        for (sx, sy) in detail.silhouette_shadow(s, tx + s.ox, ty + s.oy):
            if sy > HORIZON + 4:
                style.darken(cv, sx, sy)
        cv.paste(s, tx + s.ox, ty + s.oy)
    # transparent above the meadow and the trees
    return cv


def platform() -> Canvas:
    """A raised mound of turf: a lit grass top with tufts and a lit back rim, an earth
    face in layers with bedded stones that turns darker to the right, and roots."""
    w, h = PLATFORM_W, PLATFORM_H
    cv = Canvas(w, h)
    cx = w / 2
    face = oval(cx, 9.5, 23, 7.5)
    for (x, y) in face:
        u = (x + 0.5 - cx) / 23
        k = (y - 3) // 3
        t = 3 if u < -0.45 else 2 if u < 0.35 else 1
        if k % 2:
            t -= 1
        cv.set(x, y, SOIL[max(0, t)])
    for (sx, sy) in ((10, 12), (30, 13), (38, 10), (19, 14)):
        if (sx, sy) in face and (sx + 2, sy + 1) in face:
            detail.pebble(cv, sx, sy, STONE)
    for (rx, ry) in ((14, 11), (33, 12)):
        cv.set(rx, ry, WOOD[1]); cv.set(rx + 1, ry + 1, WOOD[1]); cv.set(rx + 1, ry + 2, WOOD[0])
    top = oval(cx, 6.5, 22.5, 5.2)
    for (x, y) in top:
        u, v = (x + 0.5 - cx) / 22.5, (y + 0.5 - 6.5) / 5.2
        r = u * u + v * v
        t = 3
        if r > 0.8:
            t = 4 if v < 0 and u < 0.3 else 2  # the lit back rim, the shaded front lip
        elif -u * 0.5 - v * 0.8 > 0.45:
            t = 4
        cv.set(x, y, G[t])
    for (x, y) in top:  # turf hangs over the face at the front
        if (x, y + 1) not in top and (x + y) % 3 == 0:
            cv.set(x, y + 1, G[1])
    for i in range(10):
        x = int(cx - 18 + noise2(i, 1, 77) * 36)
        y = int(4 + noise2(i, 2, 77) * 6)
        if (x, y) in top and (x + 2, y) in top:
            detail.grass_tuft(cv, x + 1, y, (0, 3, 5)[i % 3], G, 3)
    out = Canvas(w, h)
    for (x, y) in oval(cx + 2, 13.5, 24, 4):  # its shadow on the meadow
        out.set(x, y, (40, 52, 36, 90))
    out.paste(cv, 0, 0)
    style.close_outline(out)
    return out


def flatten(*layers: Canvas) -> Canvas:
    out = Canvas(W, H)
    for layer in layers:
        out.paste(layer, 0, 0)
    return out


def main():
    f, n = far(), near()
    layers = {
        'sky-day': sky(False), 'sky-night': sky(True),
        'far-day': f, 'far-night': moonlight(f),
        'near-day': n, 'near-night': moonlight(n),
        'platform': platform(), 'platform-night': moonlight(platform()),
    }
    for key, cv in layers.items():
        cv.save(os.path.join(OUT, f'{key}.png'), SCALE)
    flatten(layers['sky-day'], f, n).save(os.path.join(OUT, 'backdrop-day.png'), SCALE)
    flatten(layers['sky-night'], layers['far-night'], layers['near-night']).save(
        os.path.join(OUT, 'backdrop-night.png'), SCALE)
    prev = flatten(layers['sky-day'], f, n)
    p = layers['platform']
    prev.paste(p, 46 - PLATFORM_W // 2, H - FEET - 8)
    prev.paste(p, W - 46 - PLATFORM_W // 2, H - FEET - 8)
    prev.save(os.environ.get('BATTLE_PREVIEW', '/tmp/battle-preview.png'), 4)
    print('ok', W, H)


if __name__ == '__main__':
    main()
