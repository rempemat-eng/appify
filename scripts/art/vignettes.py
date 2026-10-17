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
import worlds as w  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'scenes')
W, H, SCALE, GROUND = 216, 150, 4, 39
FEET = H - GROUND

DAY_SKY = ['#A9D3E6', '#C3E0EA', '#DCEBE6', '#EEF2DF']
NIGHT_SKY = ['#1A2142', '#252E55', '#323C66', '#434C74']
DAWN_SKY = ['#D7A1A0', '#E8BCA3', '#F1D6AD', '#F5E8C2']

# Actual sprites reused at native size, not enlarged UI icons. The same tree
# has different neighbours, silhouettes and framing in each place.
PROPS = {
    'tree': lambda: g.tree(True), 'small_tree': lambda: g.tree(False),
    'autumn': lambda: g.tree(True, True), 'pine': g.pine, 'bush': g.bush,
    'hut': g.nap_hut, 'stall': g.stall, 'bed': g.bed, 'mailbox': g.mailbox,
    'sign': g.signpost, 'lantern': g.leaf_lantern, 'fence': lambda: g.fence_h(38),
    'bench': w.bench, 'library': w.library, 'cart': w.book_cart,
    'house_red': w.house, 'house_blue': lambda: w.house(g.NAP),
    'cafe': w.cafe_table, 'fountain': w.fountain, 'cabin': w.cabin,
    'cairn': w.cairn, 'boulder': w.boulder, 'rock': lambda: w.boulder(False),
    'lamp': w.lamp, 'duck': w.duck,
}

SCENES = {
    'habitat': {
        'ground': 'meadow', 'path': [(105, 77), (107, 105), (115, 150)],
        'props': [('tree', -9, 43), ('hut', 29, 57), ('small_tree', 181, 54),
                  ('fence', 0, 99), ('bench', 160, 92), ('lantern', 193, 91),
                  ('bush', -9, 121), ('bush', 196, 124), ('rock', 148, 137)],
        'pond': (176, 126, 24, 10), 'flowers': [(18, 115), (194, 110), (153, 143)],
    },
    'market': {
        'focusY': 106,
        'ground': 'paving', 'path': [],
        'props': [('small_tree', 3, 57), ('house_red', 32, 53), ('house_blue', 151, 48),
                  ('stall', 85, 68), ('cart', 43, 100), ('lantern', 146, 95),
                  ('bush', 5, 126), ('bush', 193, 125), ('rock', 169, 138)],
        'flowers': [(25, 109), (181, 115)], 'detail': 'market',
    },
    'town': {
        'focusY': 70,
        'ground': 'practice', 'path': [(107, 77), (108, 109), (110, 150)],
        'props': [('tree', -14, 38), ('house_red', 34, 46), ('house_blue', 143, 52),
                  ('small_tree', 190, 53), ('fence', 0, 99), ('fence', 179, 104),
                  ('lantern', 25, 110), ('bush', -6, 129), ('bush', 196, 126)],
        'flowers': [(15, 113), (202, 117)], 'detail': 'practice',
    },
    'nest': {
        'ground': 'nursery', 'path': [],
        'props': [('tree', -15, 39), ('small_tree', 188, 49), ('fence', 13, 82),
                  ('fence', 164, 82), ('bed', 174, 121), ('lantern', 27, 108),
                  ('bush', -5, 123), ('bush', 197, 128)],
        'flowers': [(29, 133), (184, 142)], 'detail': 'nursery',
    },
    'trail': {
        'focusY': 100,
        'ground': 'meadow', 'path': [(126, 73), (116, 91), (96, 116), (105, 150)],
        'props': [('tree', -5, 46), ('pine', 177, 45), ('small_tree', 31, 69),
                  ('sign', 46, 106), ('boulder', 165, 116), ('bush', 1, 128),
                  ('bush', 196, 135), ('rock', 143, 139)],
        'flowers': [(24, 114), (182, 137)], 'detail': 'trail',
    },
    'park': {
        'ground': 'meadow', 'path': [(109, 75), (108, 105), (115, 150)],
        'props': [('tree', -7, 42), ('autumn', 173, 42), ('fountain', 32, 77),
                  ('bench', 151, 95), ('lamp', 191, 80), ('duck', 184, 123),
                  ('bush', 0, 129), ('bush', 199, 136)],
        'pond': (179, 127, 25, 11), 'flowers': [(22, 120), (143, 137)],
    },
    'book': {
        'ground': 'paving', 'path': [],
        'props': [('tree', -12, 45), ('library', 72, 37), ('small_tree', 191, 51),
                  ('cart', 35, 106), ('cafe', 157, 111), ('lamp', 192, 89),
                  ('bush', 1, 132), ('bush', 200, 132)],
        'flowers': [(22, 117), (184, 139)], 'detail': 'book',
    },
    'mountain': {
        'ground': 'ridge', 'path': [(106, 78), (108, 114), (99, 150)],
        'props': [('pine', -9, 63), ('cabin', 27, 78), ('pine', 183, 62),
                  ('cairn', 162, 105), ('boulder', 179, 123), ('rock', 19, 132)],
        'flowers': [(33, 121), (148, 139)], 'detail': 'mountain',
    },
    'return': {
        'ground': 'meadow', 'path': [(109, 76), (108, 110), (109, 150)],
        'props': [('tree', -11, 42), ('small_tree', 187, 48), ('fence', 14, 91),
                  ('fence', 164, 94), ('mailbox', 44, 97), ('bench', 158, 102),
                  ('lantern', 22, 115), ('bush', -7, 131), ('bush', 197, 130)],
        'flowers': [(31, 130), (181, 131), (13, 111)],
    },
}


def sky(phase='day', full=False):
    cv = Canvas(W, H)
    bands = NIGHT_SKY if phase == 'night' else DAWN_SKY if phase == 'sunrise' else DAY_SKY
    horizon = H if full else 78
    for y in range(H):
        i = min(3, int(y / horizon * 4))
        cv.hline(0, y, W, bands[i])
        if i and y == int(i * horizon / 4):
            for x in range(y % 2, W, 2):
                cv.set(x, y, bands[i - 1])
    if phase == 'night':
        for x, y in oval(171, 25, 7, 7):
            if (x - 174) ** 2 + (y - 23) ** 2 > 30:
                cv.set(x, y, '#F6E7A8')
        for i in range(31):
            x = int(noise2(i, 1, 93) * W)
            y = int(noise2(i, 2, 93) * (H - 10 if full else 59))
            cv.set(x, y, '#DCD8E9' if i % 5 else '#F6E7A8')
    else:
        cx, cy = (164, 65) if phase == 'sunrise' else (171, 23)
        for x, y in oval(cx, cy, 9, 9):
            cv.set(x, y, '#FFF3C4')
    for cx, cy, width in ((22, 24, 24), (87, 16, 19), (192, 43, 14)):
        pts = oval(cx, cy, width / 2, 3) | oval(cx - 3, cy - 3, width / 4, 5)
        for x, y in pts:
            cv.set(x, y, ('#56638C' if phase == 'night' else '#E5D5C8' if phase == 'sunrise' else '#C9DCE3')
                   if (x, y + 2) not in pts else ('#747D9D' if phase == 'night' else '#F8EAD9' if phase == 'sunrise' else '#F5F4E7'))
    return cv


def distant(cv, mountain=False):
    if mountain:
        for cx, peak, breadth in ((33, 21, 42), (116, 8, 56), (190, 31, 45)):
            for x in range(max(0, cx - breadth), min(W, cx + breadth)):
                top = int(peak + abs(x - cx) * (81 - peak) / breadth)
                for y in range(top, 82):
                    snowy = y < peak + 14 + abs(x - cx) * 0.25 + (x % 5)
                    cv.set(x, y, w.SNOW[3 if x < cx else 1] if snowy else '#899596' if x < cx else '#67747F')
    for x in range(W):
        top = 68 + int(math.sin(x / 23) * 6 + math.sin(x / 9) * 3)
        for y in range(top, 85):
            cv.set(x, y, '#97BBA6' if y < top + 2 else '#A7C7B4')
    for x in range(-5, W + 8, 8):
        base = 83 + int(noise2(x, 1, 18) * 3)
        height = 7 + int(noise2(x, 2, 18) * 8)
        for y in range(base - height, base):
            half = max(1, int((y - base + height) * 0.35))
            for xx in range(x - half, x + half + 1):
                cv.set(xx, y, '#6E9F6B' if xx < x else '#5C895E')


def ground(cv, spec):
    terrain = spec['ground']
    for y in range(83, H):
        for x in range(W):
            if terrain == 'paving':
                # Quiet worn slabs, not a distracting regular high-contrast grid.
                row = y // 7
                mortar = (x + (row % 2) * 5) % 11 == 0 or y % 7 == 0
                col = '#B8AD91' if mortar else '#D5C8A7' if noise2(x // 11, row, 43) > 0.3 else '#CBBF9F'
                if y % 7 == 1 and not mortar:
                    col = '#E3D7B8'
            elif terrain == 'ridge':
                col = '#919B84' if smooth_noise(x, y, 14, 14) > 0.47 else '#A2AD97'
            else:
                col = g.G[2] if smooth_noise(x, y, 22, 11) < 0.6 else g.G[3]
            cv.set(x, y, col)
    for y in range(89, H, 5):
        for x in range(1, W, 7):
            quiet = 69 < x < 148 and 90 < y < 137
            if terrain == 'paving' or quiet or noise2(x, y, 49) > 0.3:
                continue
            if terrain == 'ridge':
                cv.hline(x, y, 2, w.MOSSROCK[2]); cv.set(x, y - 1, w.MOSSROCK[4])
            else:
                cv.set(x, y, g.G[1]); cv.set(x + 2, y, g.G[1]); cv.set(x + 1, y + 1, g.G[1])
                cv.set(x + 2, y - 1, g.G[4])
    if terrain in ('practice', 'nursery'):
        for x, y in oval(108, 113, 48 if terrain == 'practice' else 71, 18):
            cv.set(x, y, g.P[2] if smooth_noise(x, y, 8, 55) < 0.7 else g.P[3])
    path = spec.get('path', [])
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        for yy in range(max(83, y0), min(H, y1 + 1)):
            t = (yy - y0) / max(1, y1 - y0)
            cx = x0 + (x1 - x0) * t
            radius = 3 + (yy - 83) * 0.11
            for xx in range(int(cx - radius), int(cx + radius) + 1):
                col = g.P[1] if abs(xx - cx) > radius - 1 else g.P[3] if noise2(xx, yy, 8) < 0.12 else g.P[2]
                cv.set(xx, yy, col)


def pond(cv, cx, cy, rx, ry):
    for x, y in oval(cx, cy + 1, rx + 2, ry + 2):
        cv.set(x, y, g.SAND[1] if y < cy else g.SAND[0])
    pts = oval(cx, cy, rx, ry)
    for x, y in pts:
        cv.set(x, y, g.WTR[0] if (x, y - 1) not in pts else g.WTR[1] if y < cy - 2 else g.WTR[2])
    for dx, dy, length in ((-12, -2, 5), (4, 1, 7), (-4, 5, 4)):
        cv.hline(cx + dx, cy + dy, length, g.WTR[3])
    for x, y in oval(cx - 7, cy + 3, 3, 2):
        cv.set(x, y, g.LEAF[3])
    cv.set(cx - 7, cy + 2, g.LEAF[4])
    for x, y in ((cx - rx + 2, cy - 3), (cx + rx - 1, cy + 1)):
        cv.vline(x, y - 5, 6, g.LEAF[1]); cv.vline(x + 2, y - 3, 4, g.LEAF[2])


def flowers(cv, cx, cy, seed):
    colors = (g.RED[3], g.NAP[3], '#F2D16B', g.CREAM[3])
    for i, (dx, dy) in enumerate(((-5, 2), (2, 0), (6, 4))):
        x, y = cx + dx, cy + dy
        cv.vline(x, y, 3, g.LEAF[1]); cv.set(x + 1, y + 2, g.LEAF[2])
        for px, py in ((x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)):
            cv.set(px, py, colors[(i + seed) % len(colors)])
        cv.set(x, y, '#E6B24E')


def details(cv, kind):
    if kind == 'market':
        # The shopkeeper, ledger, fabric bolts and seed tray belong to this stall.
        for x, y in oval(108, 88, 4, 3):
            cv.set(x, y, g.LEAF[2] if y > 87 else g.LEAF[3])
        cv.set(106, 87, g.INK); cv.set(110, 87, g.INK)
        cv.hline(106, 89, 5, g.LEAF[0])
        for x in (69, 145):
            cv.rect(x, 113, 9, 9, g.WOOD[1]); cv.rect(x + 1, 114, 7, 6, g.WOOD[3])
            cv.hline(x + 1, 115, 7, g.WOOD[4]); cv.hline(x, 120, 9, g.WOOD[0])
    elif kind == 'practice':
        for x, y in ((54, 110), (157, 114)):
            cv.rect(x, y - 18, 4, 18, g.WOOD[2]); cv.vline(x, y - 18, 18, g.WOOD[4])
            cv.rect(x - 5, y - 16, 14, 7, g.WOOD[1]); cv.hline(x - 4, y - 15, 12, g.WOOD[3])
            cv.set(x + 2, y - 13, g.NAP[3]); cv.set(x + 1, y - 13, g.NAP[4])
        # Short hanging pennants, rather than a second unrelated UI icon style.
        for x in range(69, 149):
            cy = 70 + int(math.sin((x - 69) / 80 * math.pi) * 5)
            cv.set(x, cy, g.WOOD[0])
            if x % 13 < 5:
                cv.vline(x, cy + 1, 5 - abs(x % 13 - 2), g.NAP[3] if x // 13 % 2 else g.CREAM[2])
    elif kind == 'nursery':
        # Distant potting bench, then a few asymmetrical clay pots on the edges.
        cv.rect(78, 76, 61, 4, g.WOOD[2]); cv.hline(78, 75, 61, g.WOOD[4])
        cv.rect(81, 80, 3, 10, g.WOOD[1]); cv.rect(132, 80, 3, 10, g.WOOD[1])
        for x, y in ((67, 83), (146, 89), (26, 137), (183, 138)):
            cv.rect(x, y, 9, 7, g.RED[2]); cv.hline(x - 1, y, 11, g.RED[3])
            cv.vline(x + 1, y + 1, 5, g.RED[4]); cv.hline(x + 2, y + 6, 6, g.RED[1])
            cv.vline(x + 4, y - 5, 5, g.LEAF[1]); cv.hline(x + 1, y - 5, 4, g.LEAF[3]); cv.hline(x + 5, y - 7, 3, g.LEAF[2])
    elif kind == 'trail':
        cv.paste(w.cairn(), 176, 86)
    elif kind == 'book':
        cv.rect(154, 125, 9, 2, g.NAP[1]); cv.hline(155, 125, 7, g.CREAM[3])
    elif kind == 'mountain':
        for x, y in ((9, 116), (164, 142), (196, 112)):
            cv.hline(x, y, 13, w.SNOW[1]); cv.hline(x + 2, y - 1, 9, w.SNOW[3])


def atmosphere(cv, phase):
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
                # Cool ambient material shading, with enough value separation to
                # keep bark, stone, grass and the clearing distinct.
                color = (round(r * 0.37 + 9), round(green * 0.42 + 9), round(b * 0.53 + 18), a)
            else:
                color = (min(255, round(r * 1.02 + 7)), min(255, round(green * 0.97 + 4)), round(b * 0.88 + 4), a)
            out.set(x, y, color)
    if phase == 'night':
        # A few fixed points of lamplight. No perpetual blink or hidden timer.
        for x, y in ((198, 100), (47, 88)):
            out.rect(x, y, 2, 3, '#F2D16B'); out.set(x, y, '#FFF3C4')
    return out


def draw(spec, phase='day'):
    cv = sky()
    distant(cv, spec.get('detail') == 'mountain')
    ground(cv, spec)
    if 'pond' in spec:
        pond(cv, *spec['pond'])
    # Shared shadows and one-pixel outlines are part of each original prop.
    sprites = [(PROPS[name](), x, y) for name, x, y in spec['props']]
    import style  # noqa: E402  (hard cast shadows, docs/vision/art-style.md)
    for sprite, x, y in sprites:
        style.cast_shadow(cv, x + sprite.w / 2 + 2.5, y + sprite.h - 1, max(3.5, sprite.w * 0.48),
                          max(2.2, min(4.5, sprite.h * 0.1)))
    for sprite, x, y in sorted(sprites, key=lambda item: item[2] + item[0].h):
        cv.paste(sprite, x, y)
    details(cv, spec.get('detail'))
    for i, (x, y) in enumerate(spec.get('flowers', [])):
        flowers(cv, x, y, i)
    return atmosphere(cv, phase)


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
        f'export const sceneFrame = {{ width: {W}, height: {H}, feet: {FEET}, ground: {GROUND}, window: 160 }} as const;',
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
