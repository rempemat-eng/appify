"""Detailed, non-interactive frames for NapAttack's screens and postcards.

These use the garden's native material ramps and actual world prop drawings.
The registry below changes composition, not art style. Keep the middle of
companion frames quiet; the player owns the character placed above this art.
Run: python3 scripts/art/vignettes.py. No animation clocks or game rules.
"""
from __future__ import annotations

import math
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval, smooth_noise  # noqa: E402
import garden as g  # noqa: E402
import garden_props as gp  # noqa: E402
import world_props as wp  # noqa: E402
import worlds as w  # noqa: E402
import detail  # noqa: E402
import style  # noqa: E402
from materials import PLASTER  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'scenes')
# Step 7c: the frames are drawn at the garden's density, twice the size of the old
# 216 x 150 frames, so the world's props (drawn at twice the old density) keep their
# old composition. K converts the older layout numbers to the new frame.
K = 2


def k(v: float) -> int:
    return int(round(v * K))


# Exported at 2x: one art pixel is two image pixels (the frame is twice the old
# size, so phone memory stays where it was).
W, H, SCALE, GROUND = 432, 300, 2, 78
FEET = H - GROUND
HORIZON = k(83)

DAY_SKY = ['#A9D3E6', '#C3E0EA', '#DCEBE6', '#EEF2DF']
NIGHT_SKY = ['#1A2142', '#252E55', '#323C66', '#434C74']
DAWN_SKY = ['#D7A1A0', '#E8BCA3', '#F1D6AD', '#F5E8C2']

# Actual sprites reused at native size, not enlarged UI icons. The same tree
# has different neighbours, silhouettes and framing in each place.
PROPS = {
    'tree': lambda: gp.tree(True), 'small_tree': lambda: gp.tree(False),
    'autumn': lambda: gp.tree(True, True), 'pine': gp.pine, 'bush': gp.bush,
    'hut': gp.hut, 'stall': gp.stall, 'bed': gp.bed, 'mailbox': gp.mailbox,
    'sign': gp.signpost, 'lantern': gp.lantern, 'fence': lambda: gp.fence_h(56),
    'bench': wp.bench, 'library': wp.library, 'cart': wp.book_cart,
    'house_red': wp.house, 'house_blue': lambda: wp.house(wp.BLUE_ROOF, sign=True),
    'cafe': wp.cafe_table, 'fountain': wp.fountain, 'cabin': wp.cabin,
    'cairn': wp.cairn, 'boulder': wp.boulder, 'rock': lambda: wp.boulder(False),
    'lamp': wp.lamp, 'duck': wp.duck,
}

SCENES = {  # props: (name, centre x, foot y), in the 2x frame
    'habitat': {'ground': 'meadow', 'path': [(210, 154), (214, 210), (230, 300)], 'props': [('tree', 18, 178), ('hut', 108, 206), ('small_tree', 388, 176), ('fence', 38, 224), ('bench', 346, 216), ('lantern', 398, 234), ('bush', 4, 278), ('bush', 414, 284), ('rock', 310, 294)], 'pond': (352, 252, 48, 20), 'flowers': [(36, 230), (388, 220), (306, 286)]},
    'market': {'focusY': 180, 'ground': 'paving', 'path': [], 'props': [('small_tree', 32, 182), ('house_red', 104, 186), ('house_blue', 342, 176), ('stall', 216, 216), ('cart', 112, 240), ('lantern', 304, 242), ('bush', 32, 288), ('bush', 408, 286), ('rock', 352, 296)], 'flowers': [(50, 218), (362, 230)], 'detail': 'market'},
    'town': {'focusY': 134, 'ground': 'practice', 'path': [(214, 154), (216, 218), (220, 300)], 'props': [('tree', 8, 168), ('house_red', 108, 172), ('house_blue', 326, 184), ('small_tree', 406, 174), ('fence', 38, 224), ('fence', 396, 234), ('lantern', 62, 272), ('bush', 10, 294), ('bush', 414, 288)], 'flowers': [(30, 226), (404, 234)], 'detail': 'practice'},
    'nest': {'ground': 'nursery', 'path': [], 'props': [('tree', 6, 170), ('small_tree', 402, 166), ('fence', 64, 190), ('fence', 366, 190), ('bed', 370, 266), ('lantern', 66, 268), ('bush', 12, 282), ('bush', 416, 292)], 'flowers': [(58, 266), (368, 284)], 'detail': 'nursery'},
    'trail': {'focusY': 236, 'ground': 'meadow', 'path': [(252, 146), (232, 182), (192, 232), (210, 300)], 'props': [('tree', 26, 184), ('pine', 376, 170), ('small_tree', 88, 206), ('sign', 112, 262), ('boulder', 356, 268), ('bush', 24, 292), ('bush', 414, 306), ('rock', 300, 298)], 'flowers': [(48, 228), (364, 274)], 'detail': 'trail'},
    'park': {'ground': 'meadow', 'path': [(218, 150), (216, 210), (230, 300)], 'props': [('tree', 22, 176), ('autumn', 382, 176), ('fountain', 104, 222), ('bench', 328, 222), ('lamp', 392, 228), ('duck', 378, 262), ('bush', 22, 294), ('bush', 420, 308)], 'pond': (358, 254, 50, 22), 'flowers': [(44, 240), (286, 274)]},
    'book': {'ground': 'paving', 'path': [], 'props': [('tree', 12, 182), ('library', 216, 182), ('small_tree', 408, 170), ('cart', 96, 252), ('cafe', 338, 278), ('lamp', 394, 246), ('bush', 24, 300), ('bush', 422, 300)], 'flowers': [(44, 234), (368, 278)], 'detail': 'book'},
    'mountain': {'ground': 'ridge', 'path': [(212, 156), (216, 228), (198, 300)], 'props': [('pine', 4, 206), ('cabin', 104, 240), ('pine', 388, 204), ('cairn', 340, 262), ('boulder', 384, 282), ('rock', 52, 284)], 'flowers': [(66, 242), (296, 278)], 'detail': 'mountain'},
    'return': {'ground': 'meadow', 'path': [(218, 152), (216, 220), (218, 300)], 'props': [('tree', 14, 176), ('small_tree', 400, 164), ('fence', 66, 208), ('fence', 366, 214), ('mailbox', 100, 238), ('bench', 342, 236), ('lantern', 56, 282), ('bush', 8, 298), ('bush', 416, 296)], 'flowers': [(62, 260), (362, 262), (26, 222)]},
}


def sky(phase='day', full=False):
    cv = Canvas(W, H)
    bands = NIGHT_SKY if phase == 'night' else DAWN_SKY if phase == 'sunrise' else DAY_SKY
    horizon = H if full else k(78)
    for y in range(H):
        i = min(3, int(y / horizon * 4))
        cv.hline(0, y, W, bands[i])
        if i and y == int(i * horizon / 4):
            for x in range(y % 2, W, 2):
                cv.set(x, y, bands[i - 1])
    if phase == 'night':
        for x, y in oval(k(171), k(25), k(7), k(7)):
            if (x - k(174)) ** 2 + (y - k(23)) ** 2 > k(5.5) ** 2:
                cv.set(x, y, '#F6E7A8')
        for i in range(48):
            x = int(noise2(i, 1, 93) * W)
            y = int(noise2(i, 2, 93) * (H - 10 if full else k(59)))
            cv.set(x, y, '#DCD8E9' if i % 5 else '#F6E7A8')
            if i % 7 == 0:
                cv.set(x + 1, y, '#DCD8E9'); cv.set(x, y + 1, '#DCD8E9')
    else:
        cx, cy = (k(164), k(65)) if phase == 'sunrise' else (k(171), k(23))
        for x, y in oval(cx, cy, k(12), k(12)):
            cv.set(x, y, (255, 250, 230, 90))
        for x, y in oval(cx, cy, k(9), k(9)):
            cv.set(x, y, '#FFF3C4')
    for cx, cy, width in ((22, 24, 24), (87, 16, 19), (192, 43, 14)):
        cx, cy, width = k(cx), k(cy), k(width)
        pts = oval(cx, cy, width / 2, k(3)) | oval(cx - k(3), cy - k(3), width / 4, k(5))
        for x, y in pts:
            cv.set(x, y, ('#56638C' if phase == 'night' else '#E5D5C8' if phase == 'sunrise' else '#C9DCE3')
                   if (x, y + 2) not in pts else ('#747D9D' if phase == 'night' else '#F8EAD9' if phase == 'sunrise' else '#F5F4E7'))
    return cv


def distant(cv, mountain=False):
    if mountain:
        for cx, peak, breadth in ((33, 21, 42), (116, 8, 56), (190, 31, 45)):
            cx, peak, breadth = k(cx), k(peak), k(breadth)
            for x in range(max(0, cx - breadth), min(W, cx + breadth)):
                top = int(peak + abs(x - cx) * (k(81) - peak) / breadth)
                for y in range(top, k(82)):
                    snowy = y < peak + k(14) + abs(x - cx) * 0.25 + (x % 9)
                    cv.set(x, y, w.SNOW[3 if x < cx else 1] if snowy else '#899596' if x < cx else '#67747F')
    for x in range(W):
        top = k(68) + int(math.sin(x / 46) * 12 + math.sin(x / 18) * 6)
        for y in range(top, HORIZON + 4):
            cv.set(x, y, '#97BBA6' if y < top + 2 else '#A7C7B4')
    for x in range(-8, W + 14, 13):
        base = HORIZON + int(noise2(x, 1, 18) * 6)
        height = 14 + int(noise2(x, 2, 18) * 14)
        for y in range(base - height, base):
            half = max(1, int((y - base + height) * 0.35))
            for xx in range(x - half, x + half + 1):
                cv.set(xx, y, '#6E9F6B' if xx < x else '#5C895E' if (y - base) % 4 else '#4F7B55')


def ground(cv, spec):
    terrain = spec['ground']
    for y in range(HORIZON, H):
        for x in range(W):
            if terrain == 'paving':
                row = y // 12
                mortar = (x + (row % 2) * 9) % 20 == 0 or y % 12 == 0
                col = '#B8AD91' if mortar else '#D5C8A7' if noise2(x // 20, row, 43) > 0.3 else '#CBBF9F'
                if y % 12 == 1 and not mortar:
                    col = '#E3D7B8'
            elif terrain == 'ridge':
                col = '#919B84' if smooth_noise(x, y, 28, 14) > 0.47 else '#A2AD97'
            else:
                col = g.G[2] if smooth_noise(x, y, 40, 11) < 0.6 else g.G[3]
            cv.set(x, y, col)
    for ty in range(HORIZON + 6, H, 6):
        for tx in range(0, W, 6):
            x, y = tx + int(noise2(tx, ty, 4) * 6), ty + int(noise2(tx, ty, 5) * 5)
            quiet = k(69) < x < k(148) and k(90) < y < k(137)
            if terrain == 'paving' or quiet or noise2(tx, ty, 49) > 0.32:
                continue
            if terrain == 'ridge':
                cv.hline(x, y, 3, w.MOSSROCK[2]); cv.set(x, y - 1, w.MOSSROCK[4])
            else:
                ground_t = 3 if cv.get(x, y)[:3] == tuple(int(g.G[3][i:i + 2], 16) for i in (1, 3, 5)) else 2
                detail.grass_tuft(cv, x, y, int(noise2(tx, ty, 8) * 6), g.G, ground_t)
    if terrain in ('practice', 'nursery'):
        for x, y in oval(k(108), k(113), k(48 if terrain == 'practice' else 71), k(18)):
            cv.set(x, y, g.P[2] if smooth_noise(x, y, 16, 55) < 0.7 else g.P[3])
    path = spec.get('path', [])
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        for yy in range(max(HORIZON, y0), min(H, y1 + 1)):
            t = (yy - y0) / max(1, y1 - y0)
            cx = x0 + (x1 - x0) * t
            radius = 6 + (yy - HORIZON) * 0.11
            for xx in range(int(cx - radius), int(cx + radius) + 1):
                col = g.P[1] if abs(xx - cx) > radius - 1 else g.P[3] if smooth_noise(xx, yy, 6, 8) > 0.66 else g.P[2]
                cv.set(xx, yy, col)


def pond(cv, cx, cy, rx, ry):
    for x, y in oval(cx, cy + 1, rx + 4, ry + 4):
        cv.set(x, y, g.SAND[1] if y < cy else g.SAND[0])
    pts = oval(cx, cy, rx, ry)
    for x, y in pts:
        kk = next((i for i in range(4) if (x, y - i - 1) not in pts), 4)
        col = g.P[1] if kk == 0 else g.P[0] if kk in (1, 2) else g.WTR[0] if kk == 3 else g.WTR[1] if y < cy else g.WTR[2]
        cv.set(x, y, col)
    for dx, dy, length in ((-24, -2, 10), (8, 3, 14), (-8, 10, 8)):
        cv.hline(cx + dx, cy + dy, length, g.WTR[3])
    for x, y in oval(cx - 14, cy + 6, 6, 4):
        cv.set(x, y, g.LEAF[3] if y < cy + 6 else g.LEAF[2])
    cv.set(cx - 15, cy + 4, g.LEAF[4])
    for x, y in ((cx - rx + 4, cy - 6), (cx + rx - 2, cy + 2)):
        cv.vline(x, y - 10, 12, g.LEAF[1]); cv.vline(x + 2, y - 6, 8, g.LEAF[2]); cv.set(x - 1, y - 10, g.LEAF[3])


def flowers(cv, cx, cy, seed):
    colors = (g.RED[3], g.NAP[3], '#F2D16B', PLASTER[5])
    for i, (dx, dy) in enumerate(((-10, 4), (4, 0), (12, 8))):
        x, y = cx + dx, cy + dy
        cv.vline(x, y, 5, g.LEAF[1]); cv.set(x + 1, y + 3, g.LEAF[2]); cv.set(x - 1, y + 2, g.LEAF[3])
        c = colors[(i + seed) % len(colors)]
        for px, py in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
            cv.set(px, py, c)
        cv.set(x - 1, y - 1, c); cv.set(x, y, '#E6B24E')


def details(cv, kind):
    if kind == 'market':
        for x, y in oval(k(108), k(88), 8, 6):
            cv.set(x, y, g.LEAF[2] if y > k(88) else g.LEAF[3])
        cv.set(k(106), k(87), g.INK); cv.set(k(110), k(87), g.INK)
        for x in (k(69), k(145)):  # crates: a lit top over a darker front
            y = k(113)
            cv.rect(x, y, 18, 18, g.WOOD[1]); cv.rect(x + 1, y + 1, 16, 5, g.WOOD[4]); cv.rect(x + 1, y + 6, 16, 11, g.WOOD[2])
            cv.hline(x + 1, y + 11, 16, g.WOOD[1]); cv.vline(x + 16, y + 6, 11, g.WOOD[1]); cv.hline(x, y + 17, 18, g.WOOD[0])
    elif kind == 'practice':
        for x, y in ((k(54), k(110)), (k(157), k(114))):
            cv.rect(x, y - 36, 6, 36, g.WOOD[2]); cv.vline(x + 1, y - 36, 36, g.WOOD[4]); cv.vline(x + 5, y - 36, 36, g.WOOD[1])
            cv.rect(x - 10, y - 32, 26, 12, g.WOOD[3]); cv.hline(x - 10, y - 32, 26, g.WOOD[4]); cv.hline(x - 10, y - 21, 26, g.WOOD[1])
            cv.rect(x + 1, y - 28, 4, 4, g.NAP[3]); cv.set(x + 1, y - 28, g.NAP[4])
        for x in range(k(69), k(149)):
            cy = k(70) + int(math.sin((x - k(69)) / k(80) * math.pi) * 10)
            cv.set(x, cy, g.WOOD[0])
            if x % 26 < 10:
                ln = 10 - abs(x % 26 - 4) * 2
                cv.vline(x, cy + 1, max(1, ln), g.NAP[3] if x // 26 % 2 else PLASTER[4])
    elif kind == 'nursery':
        cv.rect(k(78), k(76), k(61), 8, g.WOOD[2]); cv.rect(k(78), k(76) - 2, k(61), 2, g.WOOD[4])
        cv.rect(k(81), k(80), 6, 20, g.WOOD[1]); cv.rect(k(132), k(80), 6, 20, g.WOOD[1])
        for x, y in ((k(67), k(83)), (k(146), k(89)), (k(26), k(137)), (k(183), k(138))):
            cv.rect(x, y, 18, 14, g.RED[2]); cv.rect(x - 2, y, 22, 3, g.RED[3]); cv.hline(x - 2, y, 22, g.RED[4])
            cv.vline(x + 2, y + 3, 10, g.RED[4]); cv.vline(x + 15, y + 3, 10, g.RED[1]); cv.hline(x + 1, y + 13, 16, g.RED[1])
            for dx, dy, c in ((4, -6, g.LEAF[3]), (8, -10, g.LEAF[2]), (11, -7, g.LEAF[3]), (7, -3, g.LEAF[1])):
                cv.rect(x + dx, y + dy, 4, 4, c)
    elif kind == 'trail':
        cairn = style.finalize(wp.cairn(), name='cairn')
        cv.paste(cairn, k(176), k(80))
    elif kind == 'book':
        cv.rect(k(154), k(125), 18, 4, g.NAP[1]); cv.hline(k(155), k(125), 16, PLASTER[5])
    elif kind == 'mountain':
        for x, y in ((k(9), k(116)), (k(164), k(142)), (k(196), k(112))):
            cv.hline(x, y, 26, w.SNOW[1]); cv.hline(x + 4, y - 1, 18, w.SNOW[3]); cv.hline(x + 8, y - 2, 10, w.SNOW[3])


def atmosphere(cv, phase, lights=()):
    if phase == 'day':
        return cv
    out = Canvas(W, H)
    day_sky, authored = sky(), sky(phase)
    for y in range(H):
        for x in range(W):
            r, green, b, a = cv.get(x, y)
            if cv.get(x, y) == day_sky.get(x, y):
                out.set(x, y, authored.get(x, y))
                continue
            if phase == 'night':
                color = (round(r * 0.37 + 9), round(green * 0.42 + 9), round(b * 0.53 + 18), a)
            else:
                color = (min(255, round(r * 1.02 + 7)), min(255, round(green * 0.97 + 4)), round(b * 0.88 + 4), a)
            out.set(x, y, color)
    if phase == 'night':  # warm pools of light from windows and lanterns (no timers)
        for (cx, cy, rx, ry) in lights:
            for x, y in oval(cx, cy, rx, ry):
                d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
                out.set(x, y, (255, 214, 122, 120 if d < 0.25 else 80 if d < 0.6 else 44))
    return out


def draw(spec, phase='day'):
    cv = sky()
    distant(cv, spec.get('detail') == 'mountain')
    ground(cv, spec)
    if 'pond' in spec:
        pond(cv, *spec['pond'])
    # The world's own props at the garden's density, anchored by their feet, with
    # the shared silhouette shadows and contact shade (scripts/art/detail.py).
    sprites = []
    lights = []
    for name, cx, foot in spec['props']:
        raw = PROPS[name]()
        sprite = style.finalize(raw, name=name)
        x = int(round(cx - raw.w / 2)) + sprite.ox
        y = foot - raw.h + sprite.oy
        sprites.append((sprite, x, y))
        if name in ('lantern', 'lamp'):
            lights.append((cx, foot - 2, 22, 9))
        elif name in ('hut', 'house_red', 'house_blue', 'cabin', 'library'):
            lights.append((cx, foot + 4, raw.w * 0.42, 9))
    shade = set()
    for sprite, x, y in sprites:
        shade |= detail.silhouette_shadow(sprite, x, y)
    for (sx, sy) in shade:
        if sy >= HORIZON:
            style.darken(cv, sx, sy)
    for sprite, x, y in sorted(sprites, key=lambda item: item[2] + item[0].h):
        cv.paste(sprite, x, y)
    details(cv, spec.get('detail'))
    for i, (x, y) in enumerate(spec.get('flowers', [])):
        flowers(cv, x, y, i)
    return atmosphere(cv, phase, lights)


def main():
    os.makedirs(OUT, exist_ok=True)
    names = [name for name in SCENES if name != 'return']
    for name in names:
        draw(SCENES[name]).save(os.path.join(OUT, f'{name}.png'), SCALE)
    draw(SCENES['habitat'], 'night').save(os.path.join(OUT, 'night.png'), SCALE)
    draw(SCENES['return'], 'sunrise').save(os.path.join(OUT, 'return.png'), SCALE)
    for phase in ('day', 'night', 'sunrise'):
        sky(phase, full=True).save(os.path.join(OUT, f'sky-{phase}.png'), SCALE)
    imports = [f"import {name} from '@/assets/scenes/{name}.png';" for name in names]
    imports += ["import night from '@/assets/scenes/night.png';", "import homecoming from '@/assets/scenes/return.png';"]
    imports += [f"import sky{phase.capitalize()} from '@/assets/scenes/sky-{phase}.png';" for phase in ('day', 'night', 'sunrise')]
    content = '\n'.join([
        '// Generated by scripts/art/vignettes.py. Do not edit by hand.',
        '/* eslint-disable */', *imports,
        f'export const sceneFrame = {{ width: {W}, height: {H}, feet: {FEET}, ground: {GROUND}, window: {k(160)} }} as const;',
        f"export const sceneImages = {{ {', '.join(names)} }} as const;",
        'export const sceneFocus: Partial<Record<keyof typeof sceneImages, number>> = ' +
        json.dumps({name: SCENES[name]['focusY'] for name in names if 'focusY' in SCENES[name]}) + ';',
        'export const sceneNight = night;', 'export const sceneReturn = homecoming;',
        'export const sceneSkies = { day: skyDay, night: skyNight, sunrise: skySunrise } as const;',
        f"export const sceneSkyColors = {{ day: '{DAY_SKY[0]}', night: '{NIGHT_SKY[0]}', sunrise: '{DAWN_SKY[0]}' }} as const;", '',
    ])
    with open(os.path.join(ROOT, 'lib', 'scene-assets.ts'), 'w') as f:
        f.write(content)
    print(f'ok {len(names) + 5} screen vignettes, {W}x{H}, footline {FEET}')


if __name__ == '__main__':
    main()
