#!/usr/bin/env python3
"""Looping effect strips for a restored village: python3 game/tools/gen_village_fx.py

Writes game/zones/crossroads/art/fx/:
  forge_fire_8.png    the forge's fire, 8 drawings of 54 x 72 side by side (same frame and foot as
                      the kit's static forge_fire.png, which the strip replaces once the forge is lit)
  chimney_smoke_8.png the smithy chimney's smoke, 8 drawings of 32 x 56, foot at the bottom centre
                      (the pot's top)
  forge_ember_8.png   the forge paid for before Hale is home (Matt, 11 Nov: a dark hearth until she
                      arrives): "an ember under the ash", a banked heap of grey ash on the hearth with
                      three coals breathing red through cracks in it, slowly; no flame, no sparks, no smoke.
                      Same frame and foot as forge_fire_8.png

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
# the house palette's ash ramp (art/house-palette.json 'ash', tones 0 to 5)
ASH = [(0x24, 0x1A, 0x26), (0x41, 0x37, 0x3E), (0x5F, 0x55, 0x57), (0x7C, 0x74, 0x6E), (0x98, 0x8D, 0x7F), (0xB2, 0xA4, 0x8F)]
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


def ember_frame(i):
    """The banked hearth (12 Nov audit, E1/E2): a heap of ash on the hearth's stone top, under the
    hood. Its crest stands 6 px over the coping (rows 49 to 54 of this frame; the coping is rows 53
    and 54, the hood's fringe ends at row 46, so 2 px stay clear under it), highest left of centre.
    The two rows under the hood take the overhang's shade (ash 2 to 3); below them the west slope is
    lit (ash 3 to 4, a 2 px ash-5 glint at its crest), the east slope falls to ash 2. Finer ash
    drifts over the coping's front edge; three charcoal lumps are 2 x 2 with a lit top-left pixel.
    Three coals glow through cracks in the crust, 3 to 5 px long and 2 deep: a dark crack with the
    hottest colour at its bottom, stepping three tones over the cycle (ember, deep, flame), each
    ringed by ash warmed to the path ramp's reds as it breathes; at the big coal's peak a warm pair
    of pixels lights the hood's lower lip above it (lamp 1). Whole pixels only, hard alpha."""
    W, H = 54, 72
    img = np.zeros((H, W, 4), np.uint8)
    top_row, base = 49, 54                         # the crest row and the heap's lowest row (on the coping)

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            img[y, x, :3] = c
            img[y, x, 3] = 255
    # the heap's profile: highest left of centre, a long east slope, uneven by a pixel here and there
    x0, x1, crest = 17, 51, 27
    tops = {}
    for x in range(x0, x1):
        if x <= crest:
            u = (crest - x) / (crest - x0)
            h = 6.0 * (1 - u ** 1.6)
        else:
            u = (x - crest) / (x1 - 1 - crest)
            h = 6.0 * (1 - u ** 1.15)
        h += (0.6 if x % 7 == 3 else 0.0) - (0.6 if x % 9 == 5 else 0.0)
        tops[x] = min(base - 1, max(top_row, int(round(base + 1 - h))))
    for x, t0 in tops.items():
        for y in range(t0, base + 1):
            if y <= 50:
                tone = 3 if x < crest - 2 else 2          # the overhang band under the hood
            elif x < crest and y <= 52:
                tone = 4 if y == t0 or y == t0 + 1 else 3  # the lit west slope
            elif x < crest + 6:
                tone = 3
            else:
                tone = 2 if y < base else 2
            put(x, y, ASH[tone])
    # the outline: the darkest ash on the right and the lowest row only (never a full ink ring)
    for x, t0 in tops.items():
        put(x, base, ASH[1])
        if x + 1 not in tops or tops[x + 1] > t0:
            put(x, t0, ASH[1] if x > crest else ASH[2])
    # the crest's glint on the lit slope
    gx = crest - 3
    gy = max(tops[gx], 51)
    put(gx, gy, ASH[5])
    put(gx + 1, gy, ASH[5])
    # finer ash drifting over the coping's front edge (row 55 is the bricks' top course)
    for x, y, t in ((20, 55, 3), (21, 55, 2), (33, 55, 2), (34, 55, 3), (35, 55, 2), (44, 55, 2), (45, 56, 2)):
        put(x, y, ASH[t])
    # charcoal: 2 x 2 lumps, a lit top-left pixel
    for x, y in ((22, 52), (39, 52), (46, 53)):
        put(x, y, ASH[3])
        put(x + 1, y, ASH[0])
        put(x, y + 1, ASH[1])
        put(x + 1, y + 1, ASH[0])
    # the coals: cracks in the crust, breathing out of phase
    WARM = [ASH[2], (0x67, 0x5C, 0x5A), (0x88, 0x5C, 0x4B), (0xA8, 0x7C, 0x60)]   # ash 2, ash_warm 2, path 2, path 3
    for k, (cx, cy, ln, big) in enumerate(((24, 51, 3, False), (30, 52, 5, True), (41, 52, 4, False))):
        b = 0.5 - 0.5 * math.cos(2 * math.pi * (i / N + k / 3.0))
        lvl = 0 if b < 0.34 else (1 if b < 0.72 else 2)
        if not big:
            lvl = min(lvl, 1) + (1 if b > 0.9 else 0)
        hot = (EMBER, DEEP, FLAME)[lvl]
        mid = (ASH[0], EMBER, DEEP)[lvl]
        for d in range(ln):
            put(cx + d, cy, ASH[0] if d in (0, ln - 1) else mid)       # the crack's dark lip, embers inside
            put(cx + d, cy + 1, hot if 0 < d < ln - 1 or ln <= 3 else mid)
        ring = WARM[min(3, lvl + (1 if big else 0))]
        for d in range(-1, ln + 1):
            put(cx + d, cy - 1, ring)                     # the ash warmed round the crack
        put(cx - 1, cy, ring)
        put(cx + ln, cy, ring)
        if big and lvl == 2:                              # its light on the hood's lower lip
            put(cx + 1, 46, (0x9B, 0x69, 0x12))
            put(cx + 2, 46, (0x9B, 0x69, 0x12))
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
    strip([ember_frame(i) for i in range(N)]).save(os.path.join(OUT, 'forge_ember_8.png'))
    print('wrote', OUT)
