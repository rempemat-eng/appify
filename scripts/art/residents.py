"""The people who live in the world's zones (world-atlas.md, "A world that feels
alive", L6): one or two residents per place, each dressed for it, drawn in the shared
rules (light from the upper left, material shading, a tinted outline) at the scale of
the zone props. Two walking frames each; the atlas moves them along short routes.

Writes assets/residents/<id>-<frame>.png, lib/resident-sprites.ts (data) and
lib/resident-assets.ts (images).
Run: python3 scripts/art/residents.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, oval  # noqa: E402
import style  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCALE = 4
W, H, PAD = 20, 28, 3


class Shifted:
    """Draws onto a canvas one pixel in from its top-left, leaving room for the outline."""

    def __init__(self, cv: Canvas, dx: int = 1, dy: int = 1):
        self.cv, self.dx, self.dy = cv, dx, dy

    def set(self, x, y, c):
        self.cv.set(x + self.dx, y + self.dy, c)

    def hline(self, x, y, w, c):
        self.cv.hline(x + self.dx, y + self.dy, w, c)

    def vline(self, x, y, h, c):
        self.cv.vline(x + self.dx, y + self.dy, h, c)

SKIN = {
    'a': ('#F2C9A0', '#D9A77E'), 'b': ('#D9A070', '#B87E52'), 'c': ('#A86E48', '#8A5434'),
    'd': ('#7A4E32', '#5E3A24'), 'e': ('#E8B890', '#C8946C'),
}
HAIR = {'dark': '#2A1E18', 'brown': '#5E3A24', 'red': '#A8482A', 'grey': '#B8B4AE', 'black': '#141016',
        'blond': '#E2BC5E'}


def shade(c: str, k: float) -> str:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    f = (lambda v: max(0, min(255, int(v * k)))) if k < 1 else (lambda v: min(255, int(v + (255 - v) * (k - 1))))
    return '#%02X%02X%02X' % (f(r), f(g), f(b))


def person(look: dict, frame: int) -> Canvas:
    """A resident, 20 x 28 (drawn one pixel in), facing the viewer three-quarters to the right: legs in
    trousers or a skirt, a torso in their working clothes with an apron or a trim, arms
    swinging with the step, a head with a face and hair or a hat."""
    canvas = Canvas(W, H, pad=PAD)
    cv = Shifted(canvas)
    skin, skin_dark = SKIN[look.get('skin', 'a')]
    top = look['top']
    legs = look.get('legs', '#3E3A50')
    cx = 8
    # legs: apart on frame 0, together on frame 1
    stride = 2 if frame == 0 else 0
    for (lx, front) in ((cx - 2 - stride // 2, False), (cx + 1 + stride // 2, True)):
        for y in range(18, 24):
            cv.set(lx, y, legs if front else shade(legs, 0.75)); cv.set(lx + 1, y, shade(legs, 0.75))
        cv.hline(lx, 24, 2, look.get('shoes', '#2A2026'))
    if look.get('skirt'):
        for y in range(16, 21):
            hw = 3 + (y - 16) // 2
            for x in range(cx - hw, cx + hw):
                cv.set(x, y, look['skirt'] if x < cx + 1 else shade(look['skirt'], 0.8))
    # the torso
    for y in range(10, 18):
        for x in range(cx - 4, cx + 4):
            c = shade(top, 1.15) if x < cx - 2 else top if x < cx + 2 else shade(top, 0.78)
            cv.set(x, y, c)
    if look.get('apron'):
        for y in range(12, 19):
            for x in range(cx - 2, cx + 3):
                cv.set(x, y, look['apron'] if x < cx + 2 else shade(look['apron'], 0.85))
    if look.get('trim'):
        cv.hline(cx - 4, 17, 8, look['trim']); cv.vline(cx, 10, 7, look['trim'])
    # arms swing opposite the legs
    sw = 1 if frame == 0 else -1
    for (ax, d) in ((cx - 5, sw), (cx + 4, -sw)):
        for y in range(11, 16):
            cv.set(ax, y + (d if y > 13 else 0), shade(top, 0.9) if ax < cx else shade(top, 0.7))
        cv.set(ax, 16 + d, skin)
    if look.get('carry'):
        kind, col = look['carry']
        if kind == 'basket':
            for (x, y) in oval(cx + 6, 16, 2.5, 2):
                cv.set(x, y, col)
        elif kind == 'plant':
            cv.set(cx + 5, 15, '#8A5A3A'); cv.set(cx + 6, 15, '#8A5A3A')
            for (x, y) in disc(cx + 5.5, 13, 1.8):
                cv.set(x, y, col)
        elif kind == 'lantern':
            cv.set(cx + 5, 17, '#2A2026'); cv.set(cx + 5, 18, col); cv.set(cx + 6, 18, shade(col, 0.8))
        elif kind == 'tray':
            cv.hline(cx + 3, 14, 5, col)
    # the head
    for (x, y) in disc(cx, 6, 3.6):
        cv.set(x, y, skin if x < cx + 2 else skin_dark)
    cv.set(cx + 1, 6, '#2A1E18'); cv.set(cx + 3, 6, '#2A1E18')  # eyes, looking right
    cv.set(cx + 2, 8, shade(skin_dark, 0.85))
    hair = HAIR[look.get('hair', 'dark')]
    for (x, y) in disc(cx - 1, 4, 3.2):
        if y <= 4 or x < cx - 2:
            cv.set(x, y, hair)
    hat = look.get('hat')
    if hat:
        kind, col = hat
        if kind == 'straw':
            cv.hline(cx - 5, 3, 11, col); cv.hline(cx - 3, 1, 6, col); cv.hline(cx - 3, 2, 6, shade(col, 0.85))
        elif kind == 'cap':
            cv.hline(cx - 3, 2, 6, col); cv.hline(cx - 3, 3, 8, shade(col, 0.8))
        elif kind == 'wide':
            cv.hline(cx - 6, 3, 13, shade(col, 0.8)); cv.hline(cx - 3, 0, 6, col); cv.hline(cx - 3, 1, 6, col)
            cv.hline(cx - 3, 2, 6, col)
        elif kind == 'goggles':
            cv.hline(cx - 3, 3, 7, '#5E3D2E'); cv.set(cx + 1, 3, '#C99A3C'); cv.set(cx + 3, 3, '#C99A3C')
        elif kind == 'wrap':
            for (x, y) in disc(cx - 1, 4, 3.6):
                if y <= 5:
                    cv.set(x, y, col if x < cx else shade(col, 0.8))
            cv.vline(cx - 4, 5, 6, shade(col, 0.8))
        elif kind == 'hood':
            for (x, y) in disc(cx - 1, 5, 4.2):
                if not ((x - cx) ** 2 + (y - 6) ** 2 < 7 and x > cx - 2):
                    cv.set(x, y, col if x < cx else shade(col, 0.75))
        elif kind == 'bowler':
            cv.hline(cx - 4, 3, 9, col); cv.hline(cx - 2, 1, 5, col); cv.hline(cx - 2, 2, 5, shade(col, 0.8))
        elif kind == 'helmet':
            for (x, y) in disc(cx, 5, 4.6):
                if (x - cx) ** 2 + (y - 6) ** 2 >= 8 or y < 3:
                    cv.set(x, y, '#DCE2EC' if x < cx else '#B8C0D2')
    return canvas


# Who lives where, and what they wear (zone ids from scripts/art/zones.py).
RESIDENTS = {
    'gardener': {'zone': 'town', 'skin': 'b', 'top': '#5E8A62', 'apron': '#C8A06A', 'hat': ('straw', '#E2BC5E'),
                 'carry': ('basket', '#C89C6A')},
    'baker': {'zone': 'town', 'skin': 'a', 'top': '#E8DCC8', 'apron': '#F7F2E8', 'hair': 'red', 'legs': '#5E4A3A',
              'carry': ('tray', '#C8803A')},
    'fisher': {'zone': 'harbour', 'skin': 'c', 'top': '#E8C04A', 'legs': '#3E5468', 'hat': ('cap', '#3E5468')},
    'keeper': {'zone': 'harbour', 'skin': 'a', 'top': '#3E4A6A', 'hair': 'grey', 'trim': '#E8D8B8',
               'carry': ('lantern', '#FFC766')},
    'steward': {'zone': 'hearthold', 'skin': 'd', 'top': '#6A4A8A', 'trim': '#E6BC5C', 'hair': 'black'},
    'tinkerer': {'zone': 'junction', 'skin': 'e', 'top': '#6E4A2E', 'apron': '#3E2A1E', 'hat': ('goggles', ''),
                 'hair': 'brown'},
    'boatwoman': {'zone': 'canal', 'skin': 'b', 'top': '#2C5A44', 'skirt': '#6E2C24', 'hat': ('cap', '#1E3E30'),
                  'legs': '#2A2026'},
    'cowhand': {'zone': 'gulch', 'skin': 'c', 'top': '#A8482A', 'legs': '#3E4A6A', 'hat': ('wide', '#8A6040'),
                'trim': '#C99466'},
    'saloon': {'zone': 'gulch', 'skin': 'a', 'top': '#E8DCC8', 'trim': '#5E3A24', 'hat': ('bowler', '#2A2026'),
               'legs': '#2A2026'},
    'trader': {'zone': 'oasis', 'skin': 'd', 'top': '#E2D2B0', 'skirt': '#C8B48A', 'hat': ('wrap', '#3E6A8A')},
    'smith': {'zone': 'caldera', 'skin': 'c', 'top': '#3E3A44', 'apron': '#6E4A2E', 'hair': 'black'},
    'attendant': {'zone': 'springs', 'skin': 'a', 'top': '#E8E2D8', 'trim': '#C2621E', 'hair': 'dark',
                  'carry': ('tray', '#F2EEE6')},
    'vendor': {'zone': 'neon', 'skin': 'e', 'top': '#2A2640', 'trim': '#E8429A', 'hat': ('hood', '#3B3657')},
    'courier': {'zone': 'neon', 'skin': 'd', 'top': '#1FB5D0', 'legs': '#1C192B', 'hat': ('cap', '#1C192B')},
    'porter': {'zone': 'skyport', 'skin': 'b', 'top': '#DCE2EC', 'trim': '#1FB5D0', 'legs': '#5C6680',
               'hat': ('cap', '#5C6680')},
    'farmer': {'zone': 'halt', 'skin': 'c', 'top': '#4A6A8A', 'apron': '#3E5468', 'hat': ('straw', '#E2BC5E'),
               'legs': '#5E4A3A'},
    'hiker': {'zone': 'ridge', 'skin': 'a', 'top': '#C2453A', 'legs': '#3E3A50', 'hat': ('cap', '#2E5A40'),
              'trim': '#E8D8B8'},
    'forager': {'zone': 'woodland', 'skin': 'd', 'top': '#6A7A3A', 'skirt': '#5E3D2E', 'hair': 'black',
                'carry': ('basket', '#A5764C')},
    'picnicker': {'zone': 'park', 'skin': 'e', 'top': '#E8A0BC', 'skirt': '#F2EEE6', 'hair': 'blond',
                  'carry': ('basket', '#C89C6A')},
    'miller': {'zone': 'riverside', 'skin': 'd', 'top': '#8A7A5E', 'apron': '#F2EEE6', 'legs': '#5E4A3A',
               'hat': ('cap', '#D8D0BE')},
    'angler': {'zone': 'riverside', 'skin': 'b', 'top': '#5A7A4A', 'legs': '#3E4A3A', 'hat': ('wide', '#7A6A4A')},
    'botanist': {'zone': 'station', 'skin': 'a', 'top': '#B8C2D6', 'trim': '#22B5A0', 'hair': 'blond',
                 'carry': ('plant', '#557A45')},
    'stargazer': {'zone': 'lumen', 'skin': 'e', 'top': '#3E3A6A', 'trim': '#9AD2FF', 'legs': '#2A2838',
                  'hat': ('helmet', '#C8C2DA'), 'carry': ('lantern', '#9AD2FF')},
    # the Frostline Highlands and the Tidebloom Isles (18 Oct)
    'warden': {'zone': 'saddle', 'skin': 'b', 'top': '#B83A32', 'legs': '#3E3A50', 'hat': ('cap', '#E8DCC8'),
               'carry': ('lantern', '#FFC766')},
    'skater': {'zone': 'snowmelt', 'skin': 'a', 'top': '#3E6AA8', 'trim': '#F7F2E8', 'legs': '#2A2838',
               'hat': ('hood', '#F7F2E8')},
    'ferryman': {'zone': 'landing', 'skin': 'c', 'top': '#F2EEE6', 'trim': '#3E6AA8', 'legs': '#3E5468',
                 'hat': ('cap', '#3E6AA8')},
    'naturalist': {'zone': 'rainforest', 'skin': 'd', 'top': '#7A8A4A', 'legs': '#5E4A3A', 'hat': ('wide', '#C8B48A'),
                   'carry': ('plant', '#4A8A44')},
    'beachcomber': {'zone': 'cove', 'skin': 'e', 'top': '#E8A0BC', 'skirt': '#F2EEE6', 'hair': 'dark',
                    'carry': ('basket', '#C89C6A')},
}


def main():
    out = os.path.join(ROOT, 'assets', 'residents')
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        os.remove(os.path.join(out, old))
    entries, imports, sizes = [], [], {}
    ident = lambda s: ''.join(p.capitalize() for p in s.replace('-', '_').split('_'))  # noqa: E731
    for rid, look in RESIDENTS.items():
        frames = []
        for f in (0, 1):
            sp = style.finalize(person(look, f), keep_size=True, name=f'{rid}-{f}')
            sp.save(os.path.join(out, f'{rid}-{f}.png'), SCALE)
            name = f'resident{ident(rid)}{f}'
            imports.append(f"import {name} from '@/assets/residents/{rid}-{f}.png';")
            frames.append(name)
        entries.append(f"  {rid}: [{', '.join(frames)}],")
        sizes[rid] = (sp.w, sp.h)
    data = [
        '// Generated by scripts/art/residents.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ZoneId } from './zone-maps';",
        '',
        '/** The residents of each zone and their sprite size in art pixels (images: resident-assets.ts). */',
        'export const residentSprites: Record<string, { zone: ZoneId; w: number; h: number }> = {',
        *[f"  {rid}: {{ zone: {json.dumps(look['zone'])}, w: {sizes[rid][0]}, h: {sizes[rid][1]} }}," for rid, look in RESIDENTS.items()],
        '};',
        '',
    ]
    images = [
        '// Generated by scripts/art/residents.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        *imports,
        '',
        '/** Two walking frames for each resident. */',
        'export const residentFrames: Record<string, readonly ImageSourcePropType[]> = {',
        *entries,
        '};',
        '',
    ]
    paths = [os.path.join(ROOT, 'lib', 'resident-sprites.ts'), os.path.join(ROOT, 'lib', 'resident-assets.ts')]
    for path, body in zip(paths, (data, images)):
        with open(path, 'w') as f:
            f.write('\n'.join(body))
    subprocess.run(['npx', 'oxfmt', '--write', *paths], cwd=ROOT, check=True, capture_output=True)
    if os.environ.get('ZONE_PREVIEW'):
        from PIL import Image
        ims = [Image.open(os.path.join(out, f'{rid}-{f}.png')) for rid in RESIDENTS for f in (0, 1)]
        sheet = Image.new('RGBA', (sum(i.width + 8 for i in ims), max(i.height for i in ims)), (200, 190, 170, 255))
        x = 0
        for i in ims:
            sheet.alpha_composite(i, (x, 0)); x += i.width + 8
        sheet.save(os.path.join(os.environ['ZONE_PREVIEW'], 'residents.png'))
    print('ok residents', len(RESIDENTS))


if __name__ == '__main__':
    main()
