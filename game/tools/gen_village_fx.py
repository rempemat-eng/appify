#!/usr/bin/env python3
"""Looping effect strips for a restored village: python3 game/tools/gen_village_fx.py

Writes game/zones/crossroads/art/fx/:
  forge_fire_8.png    the forge's fire, 8 drawings of 54 x 72 side by side (same frame and foot as
                      the kit's static forge_fire.png, which the strip replaces once the forge is lit)
  chimney_smoke_8.png the smithy chimney's smoke, 8 drawings of 32 x 56, foot at the bottom centre
                      (the pot's top)

Pixel art at the zone's density (1 texel per pixel), hard alpha, the kit's fire colours and three
smoke greys. world/loop_fx.gd plays them (only on screen; one still drawing under reduced motion).
Deterministic: same output every run."""
import math
import os

import numpy as np
from PIL import Image

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(GAME, 'zones', 'crossroads', 'art', 'fx')
N = 8

# the kit's fire ramp (forge_fire.png): ember, deep, flame, light, pale, core
EMBER, DEEP, FLAME, LIGHT, PALE, CORE = (139, 59, 1), (195, 87, 10), (242, 114, 34), (252, 182, 138), (245, 212, 156), (255, 246, 230)
SMOKE = [(122, 118, 122), (156, 152, 154), (190, 186, 184), (214, 210, 204)]


def fire_frame(i):
    W, H = 54, 72
    img = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    base = 66                                      # the coal bed's top row, as in the static picture
    t = i / N
    tongues = [(9, 16, 0.0), (17, 25, 1.7), (25, 33, 3.1), (33, 28, 4.4), (41, 21, 5.6), (47, 13, 2.4)]
    level = np.zeros((H, W), int)                  # 0 none, 1 deep, 2 flame, 3 light, 4 pale, 5 core
    for cx, h, ph in tongues:
        hh = h * (0.78 + 0.22 * math.sin(2 * math.pi * t + ph)) + 2.0 * math.sin(4 * math.pi * t + ph * 1.3)
        sway = 1.6 * math.sin(2 * math.pi * t + ph * 0.7)
        top = base - hh
        for k, (lv, shrink) in enumerate(((1, 0.0), (2, 0.18), (3, 0.42), (4, 0.62), (5, 0.8))):
            ht = hh * (1 - shrink)
            if ht < 2:
                continue
            ty = base - ht
            # a tongue: wide at the bed, pointed at the top, leaning with the sway
            rel = np.clip((yy - ty) / max(ht, 1e-3), 0, 1)
            half = (4.2 - 3.0 * shrink) * np.sqrt(rel)
            cxs = cx + sway * (1 - rel)
            m = (yy >= ty) & (yy <= base) & (np.abs(xx - cxs) <= half)
            level = np.where(m, np.maximum(level, lv), level)
    # the coal bed: a low band of embers glowing on top
    bed = (yy >= base - 1) & (yy <= base + 1) & (xx >= 4) & (xx <= 50)
    level = np.where(bed, np.maximum(level, 2), level)
    cols = {1: DEEP, 2: FLAME, 3: LIGHT, 4: PALE, 5: CORE}
    for lv, c in cols.items():
        img[level == lv, :3] = c
        img[level == lv, 3] = 255
    # dark rim on the outside of the flame (upper-left light: rim only on the right and below)
    op = level > 0
    edge = op & ~np.roll(op, -1, axis=1) | op & ~np.roll(op, -1, axis=0)
    img[edge & (level <= 2), :3] = EMBER
    # two sparks rising
    for k in range(2):
        sx = int(14 + 22 * k + 3 * math.sin(2 * math.pi * (t + k * 0.37)))
        sy = int(base - 22 - ((t * 30 + k * 13) % 26))
        if 0 <= sy < H:
            img[sy, sx, :3] = PALE if (i + k) % 2 else LIGHT
            img[sy, sx, 3] = 255
    return img


def smoke_frame(i):
    W, H = 32, 56
    img = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    lv = np.zeros((H, W), int)
    for k in range(3):                             # three puffs, a third of a cycle apart
        p = ((i / N) + k / 3.0) % 1.0
        r = 3.0 + 4.5 * p
        cx = 14 + 7 * p + 1.5 * math.sin(2 * math.pi * p)
        cy = H - 4 - 46 * p
        if p > 0.86:                               # the last stretch thins out (fewer pixels, not alpha)
            r *= (1 - p) / 0.14
        d = ((xx - cx) ** 2 + (yy - cy) ** 2) / max(r * r, 1e-3)
        body = d <= 1.0
        tone = np.where(((xx - cx + 0.35 * r) ** 2 + (yy - cy + 0.35 * r) ** 2) <= (0.55 * r) ** 2, 4, np.where(d < 0.55, 3, 2))
        lv = np.where(body, np.maximum(lv, tone), lv)
    edge = (lv > 0) & ((np.roll(lv, -1, 0) == 0) | (np.roll(lv, -1, 1) == 0))
    lv = np.where(edge, 1, lv)
    for v in (1, 2, 3, 4):
        img[lv == v, :3] = SMOKE[v - 1]
        img[lv == v, 3] = 255
    return img


def strip(frames):
    h, w = frames[0].shape[:2]
    out = np.zeros((h, w * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        out[:, i * w:(i + 1) * w] = f
    return Image.fromarray(out, 'RGBA')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    strip([fire_frame(i) for i in range(N)]).save(os.path.join(OUT, 'forge_fire_8.png'))
    strip([smoke_frame(i) for i in range(N)]).save(os.path.join(OUT, 'chimney_smoke_8.png'))
    print('wrote', OUT)
