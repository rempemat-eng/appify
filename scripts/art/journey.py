"""The journeys between regions (world-atlas.md, "Seamless travel"): between regions
the trip itself is the transition. Each destination gets three scrolling layers seen
from the carriage window (sky, far land, near land with the line) that loop across,
plus the vehicle. Run: python3 scripts/art/journey.py  (JOURNEY_PREVIEW=dir for a sheet)
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import style  # noqa: E402
import steampunk_props as sp  # noqa: E402
from materials import MATERIALS, G, STONE, WOOD, SNOW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'journeys')
W, H, SCALE = 320, 160, 4  # one loop of each layer; the app repeats it side by side

M = MATERIALS
THEMES = {
    # destination: sky top/bottom, far ramp, near ramp, extras
    'valley': {'sky': ('#7FB4E6', '#D8ECF6'), 'far': ['#5E8A8E', '#77A0A0', '#94B8B0'], 'near': G, 'kind': 'meadow'},
    'steam': {'sky': ('#B8A890', '#E8D8B8'), 'far': ['#6E5A50', '#8A7060', '#A08878'], 'near': M['brick'], 'kind': 'town'},
    'west': {'sky': ('#E8A060', '#FBE0A8'), 'far': M['adobe'], 'near': M['desert'], 'kind': 'mesa'},
    'lava': {'sky': ('#2A0E0A', '#7A2A10'), 'far': M['basalt'], 'near': M['ash'], 'kind': 'lava'},
    'neon': {'sky': ('#140E28', '#3A1E4A'), 'far': M['night'], 'near': M['night'], 'kind': 'city'},
    'space': {'sky': ('#05060C', '#141A30'), 'far': M['hull'], 'near': M['hull'], 'kind': 'space'},
    'moon': {'sky': ('#05060C', '#0B0E1C'), 'far': M['regolith'], 'near': M['regolith'], 'kind': 'moon'},
}


def lerp(a: str, b: str, t: float) -> tuple:
    ca = [int(a[k:k + 2], 16) for k in (1, 3, 5)]
    cb = [int(b[k:k + 2], 16) for k in (1, 3, 5)]
    return tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3)) + (255,)


def sky(theme) -> Canvas:
    top, bottom = theme['sky']
    cv = Canvas(W, H)
    for y in range(H):
        t = y / (H - 1)
        band = round(t * 6) / 6  # stepped bands, dithered at the joins
        for x in range(W):
            tt = band if (x + y) % 2 or abs(t - band) > 0.03 else t
            cv.set(x, y, lerp(top, bottom, tt))
    if theme['kind'] in ('neon', 'space', 'lava', 'moon') or theme['kind'] == 'city':
        for i in range(70 if theme['kind'] in ('space', 'moon') else 30):
            x, y = int(noise2(i, 0, 501) * W), int(noise2(i, 1, 501) * H * 0.7)
            cv.set(x, y, '#FFFFFF' if theme['kind'] != 'lava' else '#FFB648')
    else:
        for (cx, cy, r) in ((60, 30, 14), (210, 22, 18), (290, 44, 10)):  # soft clouds
            for (x, y) in oval(cx, cy, r * 1.8, r * 0.6):
                cv.set(x % W, y, '#FFFFFF' if y < cy else '#EAF2F8')
    if theme['kind'] == 'moon':
        for (x, y) in disc(250, 46, 26):  # the planet, far behind now
            band = int((y + math.sin(x / 7) * 2) / 4) % 3
            cv.set(x, y, ('#3E6AA8', '#5A8AC4', '#E6EEF6')[band] if (x - 250) + (y - 46) < 20 else '#2C4A78')
    if theme['kind'] == 'space':
        for (x, y) in disc(240, 150, 70):  # the planet below
            if 0 <= y < H:
                band = int((y + math.sin(x / 9) * 2) / 5) % 3
                cv.set(x, y, ('#3E6AA8', '#5A8AC4', '#E6EEF6')[band])
    return cv


def ridge(cv: Canvas, ramp, base: int, amp: float, freq: float, seed: int, lit: bool = True):
    """A loopable skyline of land: height from sines with whole periods across W."""
    for x in range(W):
        top = base - int(amp * (0.6 * math.sin(2 * math.pi * x * freq / W + seed) + 0.4 * math.sin(2 * math.pi * x * (freq * 2) / W + seed * 2)))
        for y in range(top, H):
            k = y - top
            c = ramp[2] if k < 2 and lit else ramp[1] if k < 10 else ramp[0]
            cv.set(x, y, c)


def far(theme) -> Canvas:
    cv = Canvas(W, H)
    kind = theme['kind']
    if kind == 'city':
        for i in range(16):  # tower silhouettes with lit windows
            x0 = i * 20 + int(noise2(i, 0, 502) * 6)
            hgt = 40 + int(noise2(i, 1, 502) * 60)
            for y in range(H - hgt, H):
                for x in range(x0, x0 + 16):
                    cv.set(x % W, y, theme['far'][2])
            for wy in range(H - hgt + 4, H - 4, 6):
                for wx in range(x0 + 2, x0 + 14, 4):
                    if noise2(wx, wy, 503) > 0.55:
                        cv.set(wx % W, wy, ('#FFC766', '#6FE6F2', '#FF7EC2')[(wx + wy) % 3])
        return cv
    if kind == 'space':
        return cv  # the void; the planet is in the sky layer
    if kind == 'moon':  # the moon's grey mountains coming up to meet the shuttle
        ridge(cv, theme['far'], 110, 22, 2, 4)
        ridge(cv, [theme['far'][1], theme['far'][2], theme['far'][3]], 130, 10, 3, 6)
        return cv
    if kind == 'town':
        for i in range(10):  # chimneys and clock towers on the horizon
            x0 = i * 32 + int(noise2(i, 0, 504) * 8)
            hgt = 30 + int(noise2(i, 1, 504) * 30)
            for y in range(H - hgt, H):
                for x in range(x0, x0 + 18):
                    cv.set(x % W, y, theme['far'][1])
            for y in range(H - hgt - 14, H - hgt):
                for x in range(x0 + 12, x0 + 16):
                    cv.set(x % W, y, theme['far'][0])
        ridge(cv, theme['far'], 140, 6, 2, 1)
        return cv
    if kind == 'mesa':
        for x in range(W):  # flat-topped mesas
            top = 80 if (x // 80) % 2 == 0 and 10 < x % 80 < 60 else 120
            for y in range(top, H):
                cv.set(x, y, theme['far'][3] if y < top + 3 else theme['far'][2] if (y // 6) % 2 else theme['far'][1])
        return cv
    if kind == 'lava':
        ridge(cv, theme['far'], 90, 30, 2, 3)
        for x in range(W):  # glowing seams down the slopes
            if noise2(x // 3, 0, 505) > 0.8:
                for y in range(100, H, 2):
                    cv.set(x, y, M['lava'][2])
        return cv
    ridge(cv, theme['far'], 90, 18, 2, 2)  # meadow hills
    ridge(cv, ['#3E6A4A', '#4E7A50', '#6A9468'], 120, 10, 3, 5)
    return cv


def near(theme) -> Canvas:
    cv = Canvas(W, H)
    ramp = theme['near']
    kind = theme['kind']
    if kind == 'moon':  # regolith and craters rushing past under the shuttle
        for y in range(128, H):
            for x in range(W):
                n = smooth_noise(x, y, 12, 509)
                cv.set(x, y, ramp[3] if n > 0.45 else ramp[2])
        for i in range(8):
            cx = i * 40 + int(noise2(i, 0, 510) * 10)
            for (x, y) in oval(cx, 144, 10, 4):
                cv.set(x % W, y, ramp[1] if (x - cx) + (y - 144) * 2 > 0 else ramp[4])
        return cv
    if kind == 'space':
        for x in range(W):  # the elevator's cable rushing past
            if x % 80 in (38, 39):
                for y in range(0, H):
                    cv.set(x, y, M['hull'][3] if x % 80 == 38 else M['hull'][2])
        return cv
    for y in range(110, H):  # the embankment: calm bands, a few stones
        for x in range(W):
            n = smooth_noise(x, y, 14, 506)
            c = ramp[2] if n > 0.45 or (n > 0.4 and (x + y) % 2) else ramp[1]
            if y > 140:
                c = ramp[1] if n > 0.5 else ramp[0]
            if noise2(x, y, 508) > 0.985:
                c = STONE[3]
            cv.set(x, y, c)
    if kind == 'meadow':
        for i in range(12):  # trees and fence posts flicking past
            x = i * 27 + int(noise2(i, 0, 507) * 6)
            for (tx, ty) in disc(x, 96, 10):
                cv.set(tx % W, ty, G[3] if (tx - x) + (ty - 96) < 0 else G[2])
            for y in range(100, 112):
                cv.set(x % W, y, WOOD[2])
    elif kind == 'mesa':
        for i in range(6):
            x = i * 53 + 10
            for y in range(84, 112):
                for dx in range(-2, 3):
                    cv.set((x + dx) % W, y, M['cactus'][3] if dx < 0 else M['cactus'][2])
    elif kind == 'city':
        for i in range(8):  # pillars of the elevated line with neon strips
            x = i * 40
            for y in range(60, 112):
                for dx in range(8):
                    cv.set((x + dx) % W, y, M['night'][4] if dx < 2 else M['night'][3] if dx < 5 else M['night'][2])
            for y in range(72, 90):
                cv.set((x + 3) % W, y, M['neon_pink'][3] if (x // 40) % 2 else M['neon_cyan'][3])
    elif kind == 'lava':
        for x in range(W):
            if (x // 40) % 2 == 0:
                for y in range(104, 110):
                    cv.set(x, y, M['lava'][3] if y < 107 else M['lava'][2])
    for x in range(W):  # sleepers and the rail
        if x % 6 < 3:
            for y in range(120, 126):
                cv.set(x, y, WOOD[2] if y < 123 else WOOD[1])
        cv.set(x, 120, STONE[4]); cv.set(x, 121, STONE[2])
    return cv


def carriage() -> Canvas:
    """A passenger carriage, 72 x 40, side on: a varnished body with warm windows."""
    w, h = 72, 40
    cv = Canvas(w, h, pad=4)
    for x in range(2, w - 2):
        for y in range(6, 32):
            cv.set(x, y, WOOD[3] if y < 9 else WOOD[2] if y < 26 else WOOD[1])
    cv.rect(0, 3, w, 4, M['iron'][3]); cv.hline(0, 3, w, M['iron'][4])
    for wx in range(8, w - 12, 14):
        for (x, y) in ((xx, yy) for xx in range(wx, wx + 10) for yy in range(11, 20)):
            cv.set(x, y, M['lamplight'][3] if y < 14 else M['lamplight'][2])
    for wxx in (14, w - 14):
        for (x, y) in disc(wxx, 34, 5):
            cv.set(x, y, M['red'][2] if x < wxx else M['red'][1])
        cv.set(wxx, 34, M['brass'][4])
    cv.hline(0, 30, w, M['iron'][1])
    return cv


def capsule() -> Canvas:
    """The space elevator's capsule, 48 x 56: a rounded white pod with a viewport ring
    and the cable through its spine."""
    w, h = 48, 56
    cv = Canvas(w, h, pad=4)
    for (x, y) in oval(24, 28, 20, 26):
        k = (x - 4) / 40
        cv.set(x, y, '#F4F6FA' if k < 0.35 else '#D2D8E4' if k < 0.7 else '#A9B2C4')
    for (x, y) in oval(24, 26, 12, 8):
        cv.set(x, y, '#5A8AC4' if y < 26 else '#2C4A78')
    cv.set(19, 22, '#E6F2FF')
    for y in range(0, h):
        cv.set(24, y, M['hull'][2]) if not (2 < y < 54) else None
    for y in (44, 46):
        cv.hline(10, y, 28, M['neon_cyan'][3])
    return cv


def main():
    os.makedirs(OUT, exist_ok=True)
    preview = os.environ.get('JOURNEY_PREVIEW')
    sheet = Canvas(W * 2, H * len(THEMES)) if preview else None
    for i, (dest, theme) in enumerate(THEMES.items()):
        layers = {'sky': sky(theme), 'far': far(theme), 'near': near(theme)}
        for name, cv in layers.items():
            cv.save(os.path.join(OUT, f'{dest}-{name}.png'), SCALE)
        if sheet:
            for k in range(2):
                for name in ('sky', 'far', 'near'):
                    sheet.paste(layers[name], k * W, i * H)
    engine = style.finalize(sp.locomotive(), name='journey-engine')
    coach = style.finalize(carriage(), name='journey-carriage')
    pod = style.finalize(capsule(), name='journey-capsule')
    engine.save(os.path.join(OUT, 'engine.png'), SCALE)
    coach.save(os.path.join(OUT, 'carriage.png'), SCALE)
    pod.save(os.path.join(OUT, 'capsule.png'), SCALE)
    if sheet:
        for i in range(len(THEMES)):
            if list(THEMES)[i] not in ('space', 'moon'):  # the engine faces left and leads; the coach follows
                sheet.paste(engine, 120, i * H + 72)
                sheet.paste(coach, 226, i * H + 82)
            else:
                sheet.paste(pod, 140, i * H + 40)
        sheet.save(os.path.join(preview, 'journeys.png'), 2)
    ident = lambda k: k[0].upper() + k[1:]  # noqa: E731
    lines = [
        '// Generated by scripts/art/journey.py. Do not edit by hand.',
        "import type { ImageSourcePropType } from 'react-native';",
        *[f"import {d}{ident(n)} from '@/assets/journeys/{d}-{n}.png';" for d in THEMES for n in ('sky', 'far', 'near')],
        "import engine from '@/assets/journeys/engine.png';",
        "import carriage from '@/assets/journeys/carriage.png';",
        "import capsule from '@/assets/journeys/capsule.png';",
        f'export const JOURNEY = {{ width: {W}, height: {H}, rail: 120 }} as const;',
        '/** Sky, far land and near land for the trip to each region; each loops across. `above` and',
        ' * `below` fill the screen past the band (the sky\'s top, the ground\'s foot). */',
        'export const journeyLayers: Record<string, { sky: ImageSourcePropType; far: ImageSourcePropType; near: ImageSourcePropType; above: string; below: string }> = {',
        *[f"  {d}: {{ sky: {d}Sky, far: {d}Far, near: {d}Near, above: '{t['sky'][0]}', below: '{'#05060C' if d == 'space' else t['near'][0]}' }}," for d, t in THEMES.items()],
        '};',
        'export const journeyVehicles: Record<string, { source: ImageSourcePropType; w: number; h: number }> = {',
        f'  engine: {{ source: engine, w: {engine.w}, h: {engine.h} }},',
        f'  carriage: {{ source: carriage, w: {coach.w}, h: {coach.h} }},',
        f'  capsule: {{ source: capsule, w: {pod.w}, h: {pod.h} }},',
        '};',
        '',
    ]
    target = os.path.join(ROOT, 'lib', 'journey-assets.ts')
    with open(target, 'w') as f:
        f.write('\n'.join(lines))
    import subprocess
    subprocess.run(['npx', 'oxfmt', '--write', target], cwd=ROOT, check=False, capture_output=True)
    print('ok journeys', ', '.join(THEMES))


if __name__ == '__main__':
    main()
