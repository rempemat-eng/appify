"""Keepsakes for the nap hut (living-world plan W4, C12; docs/vision/world-atlas.md,
"Decorating"): small things the companion brings home from the places it walks, one
from each, placed anywhere on the hut's floor. Collect once, place freely: nothing is
bought, nothing wears out, nothing is scored.

Same rules as every prop (art-style.md): the native pixel grid, light from the upper
left, material ramps from materials.py, a closed tinted outline (style.finalize). Each
is small (a keepsake, not furniture), so it never crowds the room the companion walks.

Writes assets/decor/<id>.png and lib/decor-assets.ts (images, sizes and footprints).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, shade_blob  # noqa: E402
import style  # noqa: E402
import worlds  # noqa: E402
from materials import MATERIALS, WOOD, STONE, LEAF, GOLD, RED, NAP, SAND  # noqa: E402

PAD = 3
CLAY = MATERIALS['adobe']
BRASS = MATERIALS['brass']
CACTUS = MATERIALS['cactus']
BASALT, LAVA = MATERIALS['basalt'], MATERIALS['lava']
PINK = MATERIALS['neon_pink']
GLOW = MATERIALS['glowflora']
HULL = MATERIALS['hull']
WTR = MATERIALS['water']
CREAM = MATERIALS['cream']


def _pot(cv: Canvas, cx: float, top: int, bottom: int, rim: float, foot: float, ramp=CLAY):
    """A clay pot, wider at the rim, lit on its left; a darker rim lip and soil showing."""
    for y in range(top, bottom):
        t = (y - top) / max(1, bottom - top - 1)
        half = rim + (foot - rim) * t
        for x in range(int(cx - half), int(cx + half) + 1):
            k = (x - (cx - half)) / max(1, 2 * half)
            cv.set(x, y, ramp[4] if k < 0.25 else ramp[3] if k < 0.55 else ramp[2] if k < 0.85 else ramp[1])
    for x in range(int(cx - rim) - 1, int(cx + rim) + 2):  # the rim
        cv.set(x, top, ramp[4] if x < cx else ramp[3])
        cv.set(x, top + 1, ramp[1])


def fern_pot() -> Canvas:
    """A fern in a clay pot, 20 x 24: arching fronds, lit tips on the left."""
    cv = Canvas(20, 24, pad=PAD)
    for k, (dx, lean, length) in enumerate(((-1, -0.9, 11), (1, 0.9, 11), (0, -0.25, 12), (0, 0.3, 12),
                                            (-1, -0.55, 12), (1, 0.6, 10))):
        for t in range(length):
            x = 10 + dx + lean * t
            y = 14 - t + (t * t) * 0.07 * abs(lean) * 1.6
            lit = lean < 0.1 and t > 3
            cv.set(int(x), int(y), LEAF[4] if lit and t % 3 == 0 else LEAF[3] if lit else LEAF[2])
            if t % 2 == 0 and t > 2:  # leaflets
                cv.set(int(x) - 1, int(y), LEAF[3] if lit else LEAF[1])
                cv.set(int(x) + 1, int(y), LEAF[2] if lit else LEAF[1])
    _pot(cv, 10, 15, 24, 5.5, 4)
    return cv


def stool() -> Canvas:
    """A three-legged milking stool, 16 x 16: a round seat seen from above, its grain."""
    cv = Canvas(16, 16, pad=PAD)
    for (lx, top) in ((3, 8), (12, 8), (8, 9)):
        for y in range(top, 16):
            cv.set(lx, y, WOOD[1] if lx > 8 else WOOD[2])
    shade_blob(cv, oval(8, 6, 7, 4.2), WOOD[1], WOOD[2], WOOD[3], WOOD[4])
    for x in range(3, 13, 3):
        cv.set(x, 6, WOOD[2])
    return cv


def rag_rug() -> Canvas:
    """A braided rag rug, 40 x 22, flat on the floor (walked over): rings of rag colours."""
    cv = Canvas(40, 22, pad=PAD)
    rings = (RED[2], CREAM[2], NAP[2], CREAM[1], RED[3], NAP[3], CREAM[2])
    for y in range(22):
        for x in range(40):
            d = ((x + 0.5 - 20) / 19.5) ** 2 + ((y + 0.5 - 11) / 10.5) ** 2
            if d > 1:
                continue
            k = int((1 - d ** 0.5) * 7)
            c = rings[min(k, len(rings) - 1)]
            if (x + y) % 3 == 0 and d > 0.15:  # the braid's twist
                c = CREAM[3] if c in (CREAM[1], CREAM[2]) else CREAM[2]
            cv.set(x, y, c)
    return cv


def shell_bowl() -> Canvas:
    """A shallow wooden bowl of shells from the shore, 20 x 14: the rim seen from above, the
    hollow in shade, a scallop, a cone and two pale cockles catching the light."""
    cv = Canvas(20, 14, pad=PAD)
    outer, inner = oval(10, 8, 9.5, 5.5), oval(10, 7.4, 7.6, 3.8)
    for (x, y) in outer:
        cv.set(x, y, WOOD[3] if (x - 10) * 0.6 + (y - 8) < -1 else WOOD[2] if y < 11 else WOOD[1])
    for (x, y) in inner:
        cv.set(x, y, WOOD[1] if y < 7 else WOOD[0])
    # a scallop (ribbed fan), a spiral cone, two cockles
    for (x, y) in oval(6.5, 7, 2.6, 2):
        cv.set(x, y, RED[4] if (x % 2) else RED[3])
    cv.set(6, 9, RED[2])
    for (x, y, c) in ((10, 6, CREAM[3]), (11, 6, CREAM[3]), (11, 7, CREAM[2]), (12, 7, CREAM[2]), (12, 8, CREAM[1]), (10, 7, SAND[2])):
        cv.set(x, y, c)
    for (cx, cy) in ((14.5, 7.5), (9, 9)):
        for (x, y) in oval(cx, cy, 1.8, 1.4):
            cv.set(x, y, CREAM[3] if x < cx else SAND[2])
    return cv


def cairn() -> Canvas:
    """A little cairn of ridge stones, 14 x 20, each stone faceted and lit from above left."""
    cv = Canvas(14, 20, pad=PAD)
    for (cx, cy, rx, ry, s) in ((7, 16, 6.5, 3.5, 1), (6.5, 11, 5, 2.8, 2), (7.5, 7, 3.8, 2.3, 3), (7, 3.5, 2.6, 1.8, 4)):
        style.facet_stone(cv, oval(cx, cy, rx, ry), STONE, seed=s)
    return cv


def town_lantern() -> Canvas:
    """A brass hand lantern, 12 x 20: a ring handle, glass panes with a warm flame."""
    cv = Canvas(12, 20, pad=PAD)
    for (x, y) in ((4, 1), (5, 0), (6, 0), (7, 1)):
        cv.set(x, y, BRASS[2])
    for x in range(2, 10):
        cv.set(x, 3, BRASS[3] if x < 6 else BRASS[2])
        cv.set(x, 17, BRASS[2] if x < 6 else BRASS[1])
    for y in range(4, 17):
        cv.set(2, y, BRASS[3]); cv.set(9, y, BRASS[1])
        for x in range(3, 9):
            glow = abs(x - 5.5) + abs(y - 11) * 0.6
            cv.set(x, y, GOLD[4] if glow < 2 else GOLD[3] if glow < 3.5 else MATERIALS['lamplight'][1])
    for x in range(1, 11):
        cv.set(x, 18, BRASS[2] if x < 6 else BRASS[1])
        cv.set(x, 19, BRASS[1])
    return cv


def reed_vase() -> Canvas:
    """A tall blue vase of reeds and bulrushes from the river, 12 x 26."""
    cv = Canvas(12, 26, pad=PAD)
    for k, (x0, top, lean) in enumerate(((4, 1, -0.12), (6, 0, 0.02), (8, 3, 0.15), (5, 4, -0.05), (7, 5, 0.08))):
        for y in range(top, 15):
            x = int(x0 + (15 - y) * lean)
            cv.set(x, y, '#9DB25A' if x < 6 and y < 9 else '#6E8A3E')
        if k < 3:
            for y in range(top, top + 4):
                cv.set(int(x0 + (15 - y) * lean), y, '#6E4A2A' if y < top + 2 else '#4A3020')
    _pot(cv, 6, 14, 26, 3, 4, ramp=WTR)
    return cv


def pinecone_jar() -> Canvas:
    """A glass jar of pine cones from the woodland, 14 x 16."""
    cv = Canvas(14, 16, pad=PAD)
    for y in range(3, 16):
        for x in range(1, 13):
            cv.set(x, y, '#CFE0E6' if x < 4 else '#A9C2CC' if x < 10 else '#8AA4AE')
    for (cx, cy) in ((4.5, 12), (9, 12.5), (6.5, 8)):
        for (x, y) in oval(cx, cy, 2.4, 3):
            cv.set(x, y, WOOD[3] if (x + y) % 2 and x < cx else WOOD[2] if (x + y) % 2 else WOOD[1])
    for x in range(2, 12):
        cv.set(x, 1, WOOD[3] if x < 7 else WOOD[2])  # the cork
        cv.set(x, 2, WOOD[1])
    for y in range(4, 14, 2):
        cv.set(2, y, '#F2F8FA')  # the glass catches the light
    return cv


def cactus_pot() -> Canvas:
    """A little barrel cactus in a painted pot, 14 x 20, a pink flower on top."""
    cv = Canvas(14, 20, pad=PAD)
    shade_blob(cv, oval(7, 7.5, 5, 6.5), CACTUS[1], CACTUS[2], CACTUS[3], CACTUS[4])
    for x in (4, 7, 10):  # ribs
        for y in range(3, 13):
            if (x - 7) ** 2 / 25 + (y - 7.5) ** 2 / 42 < 0.85:
                cv.set(x, y, CACTUS[1] if x > 6 else CACTUS[2])
    for (x, y) in ((6, 1), (7, 0), (8, 1), (7, 1)):
        cv.set(x, y, PINK[3] if (x, y) != (7, 1) else GOLD[4])
    _pot(cv, 7, 13, 20, 5, 4)
    for x in range(4, 11, 2):
        cv.set(x, 16, MATERIALS['neon_cyan'][2])  # a painted band
    return cv


def cog_clock() -> Canvas:
    """A brass mantel clock from Cogsworth, 16 x 24: a cog for a face, a pendulum below."""
    cv = Canvas(16, 24, pad=PAD)
    for y in range(9, 24):
        for x in range(3, 13):
            cv.set(x, y, WOOD[3] if x < 5 else WOOD[2] if x < 11 else WOOD[1])
    for y in range(13, 21):
        for x in range(6, 10):
            cv.set(x, y, WOOD[0])
    for y in range(13, 19):
        cv.set(8, y, BRASS[3])
    for (x, y) in disc(8, 19.5, 1.6):
        cv.set(x, y, BRASS[4] if x < 8 else BRASS[2])
    teeth = {(x, y) for (x, y) in disc(8, 7, 7) if (x, y) not in disc(8, 7, 5.5)}
    face = disc(8, 7, 5.6)
    for (x, y) in face:
        cv.set(x, y, CREAM[3] if (x - 8) + (y - 7) < 0 else CREAM[2])
    for (x, y) in teeth:
        import math
        a = math.atan2(y - 7, x - 8)
        if int((a + math.pi) / (2 * math.pi) * 12) % 2 == 0:
            cv.set(x, y, BRASS[4] if x + y < 15 else BRASS[2])
    for (x, y) in {(x, y) for (x, y) in disc(8, 7, 6) if (x, y) not in face}:
        cv.set(x, y, BRASS[3] if x + y < 15 else BRASS[1])
    for (x, y) in ((8, 7), (8, 6), (8, 5), (9, 7), (10, 7)):
        cv.set(x, y, MATERIALS['iron'][1])
    return cv


def neon_sign() -> Canvas:
    """A small neon sign on a stand, 22 x 16: a pink 'zz' (a nap) on a dark board."""
    cv = Canvas(22, 16, pad=PAD)
    night = MATERIALS['night']
    for y in range(0, 12):
        for x in range(0, 22):
            cv.set(x, y, night[2] if x < 11 else night[1])
    # two Zs (a nap), the big one and a small one, glowing tubes with a soft halo
    big = [(3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (6, 3), (5, 4), (4, 5), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]
    small = [(10, 5), (11, 5), (12, 5), (11, 6), (10, 7), (11, 7), (12, 7)]
    for (x, y) in big + small:
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in big + small and cv.get(x + dx, y + dy)[3]:
                cv.set(x + dx, y + dy, PINK[0])
    for (x, y) in big + small:
        cv.set(x, y, PINK[3] if (x + y) % 3 else PINK[4])
    for (x, y) in ((16, 3), (17, 2), (18, 2)):  # a little moon
        cv.set(x, y, MATERIALS['neon_cyan'][3])
    cv.set(17, 3, MATERIALS['neon_cyan'][2]); cv.set(16, 4, MATERIALS['neon_cyan'][3]); cv.set(17, 5, MATERIALS['neon_cyan'][3])
    for y in range(12, 16):
        cv.set(5, y, MATERIALS['iron'][2]); cv.set(16, y, MATERIALS['iron'][1])
    return cv


def ember_lamp() -> Canvas:
    """A basalt lamp from the fire country, 12 x 20: a cracked stone bowl holding embers."""
    cv = Canvas(12, 20, pad=PAD)
    for y in range(10, 20):
        half = 2 if y < 17 else 4
        for x in range(6 - half, 6 + half):
            cv.set(x, y, BASALT[3] if x < 6 else BASALT[2])
    shade_blob(cv, oval(6, 8, 5.5, 3), BASALT[1], BASALT[2], BASALT[3], BASALT[4])
    for (x, y) in oval(6, 7, 3.6, 1.4):
        cv.set(x, y, LAVA[4] if (x + y) % 3 else LAVA[5])
    for (x, y) in ((5, 4), (6, 3), (7, 5), (6, 1)):
        cv.set(x, y, LAVA[4] if y > 2 else LAVA[3])
    for (x, y) in ((3, 9), (4, 10), (8, 9)):
        cv.set(x, y, LAVA[3])  # cracks still glowing
    return cv


def dragon_plush() -> Canvas:
    """A night-blue dragon plush from Hearthold's gift stall, 22 x 16: sat up, felt wings,
    a gold belly, button eyes. A toy, so soft rounded shapes."""
    cv = Canvas(22, 16, pad=PAD)
    blue = HULL
    for (x, y) in oval(16, 12, 5, 2.4):  # the tail curled round
        cv.set(x, y, blue[2] if x < 16 else blue[1])
    shade_blob(cv, oval(10, 10, 6, 5.5), blue[1], blue[2], blue[3], blue[4])
    for (x, y) in oval(10, 11.5, 3.4, 3.2):
        cv.set(x, y, GOLD[4] if x < 10 else GOLD[3])
    for (x, y) in oval(4, 6, 3.5, 3):  # the wing, felt with seams
        cv.set(x, y, NAP[2] if y < 6 else NAP[1])
    shade_blob(cv, oval(11, 3.5, 4.5, 3.3), blue[1], blue[2], blue[3], blue[4])
    cv.set(9, 3, MATERIALS['iron'][0]); cv.set(13, 3, MATERIALS['iron'][0])
    for (x, y) in ((8, 0), (14, 0), (9, 1), (13, 1)):
        cv.set(x, y, CREAM[3])  # little horns
    return cv


def star_globe() -> Canvas:
    """A star globe from Halcyon Station, 16 x 22: a dark glass sphere of constellations on
    a brass stand."""
    cv = Canvas(16, 22, pad=PAD)
    void = MATERIALS['void']
    for (x, y) in disc(8, 7.5, 7):
        d = (x - 5) + (y - 4.5)
        cv.set(x, y, void[3] if d < -2 else void[2] if d < 4 else void[1])
    for (x, y) in ((5, 4), (7, 6), (10, 5), (11, 9), (6, 10), (9, 12), (4, 8)):
        cv.set(x, y, CREAM[3])
    for (a, b) in (((5, 4), (7, 6)), ((7, 6), (10, 5))):
        pass
    cv.set(6, 5, GLOW[3]); cv.set(8, 6, GLOW[2]); cv.set(9, 5, GLOW[2])
    for y in range(15, 19):
        cv.set(8, y, BRASS[3] if y < 17 else BRASS[2])
    for x in range(3, 13):
        cv.set(x, 19, BRASS[3] if x < 8 else BRASS[2])
        cv.set(x, 20, BRASS[1])
    for (x, y) in ((2, 6), (2, 7), (2, 8), (3, 11), (4, 13), (13, 3), (14, 6)):
        cv.set(x, y, BRASS[3])  # the meridian ring
    return cv


def moon_crystal() -> Canvas:
    """A cluster of Lumen's glowing crystals, 14 x 20, lit from within."""
    cv = Canvas(14, 20, pad=PAD)
    for (x0, top, w, lean) in ((6, 1, 3, 0), (3, 7, 2, -0.2), (10, 6, 2, 0.2), (8, 9, 2, 0.1)):
        for y in range(top, 18):
            xx = int(x0 + (18 - y) * lean)
            for dx in range(w):
                c = GLOW[4] if dx == 0 and y < top + 4 else GLOW[3] if dx == 0 else GLOW[2]
                cv.set(xx + dx, y, c)
        cv.set(int(x0 + (18 - top) * lean), top - 1, GLOW[4])
    for x in range(1, 13):
        cv.set(x, 18, MATERIALS['regolith'][3] if x < 6 else MATERIALS['regolith'][2])
        cv.set(x, 19, MATERIALS['regolith'][1])
    return cv


# id: (painter, footprint height in art pixels (0: flat, walked over))
ITEMS = {
    'fern_pot': (fern_pot, 6),
    'stool': (stool, 6),
    'rag_rug': (rag_rug, 0),
    'shell_bowl': (shell_bowl, 6),
    'cairn': (cairn, 6),
    'town_lantern': (town_lantern, 4),
    'reed_vase': (reed_vase, 5),
    'pinecone_jar': (pinecone_jar, 6),
    'cactus_pot': (cactus_pot, 5),
    'cog_clock': (cog_clock, 6),
    'neon_sign': (neon_sign, 4),
    'ember_lamp': (ember_lamp, 5),
    'dragon_plush': (dragon_plush, 6),
    'star_globe': (star_globe, 4),
    'moon_crystal': (moon_crystal, 5),
}


def sprites() -> dict:
    return {key: style.finalize(paint(), name=key) for key, (paint, _foot) in ITEMS.items()}


def main():
    out = os.path.join(worlds.ROOT, 'assets', 'decor')
    os.makedirs(out, exist_ok=True)
    for old in os.listdir(out):
        os.remove(os.path.join(out, old))
    built = sprites()
    for key, sp in built.items():
        sp.save(os.path.join(out, f'{key}.png'), worlds.SCALE)
    ident = lambda k: ''.join(p.capitalize() for p in k.split('_'))  # noqa: E731
    images = [
        '// Generated by scripts/art/decor.py. Do not edit by hand.',
        "import type { ImageSourcePropType } from 'react-native';",
        *[f"import decor{ident(k)} from '@/assets/decor/{k}.png';" for k in built],
        '',
        '/** Each keepsake\'s image (its size and footprint: lib/decor-sizes.ts). */',
        'export const decorImages: Record<string, ImageSourcePropType> = {',
        *[f'  {k}: decor{ident(k)},' for k in built],
        '};',
        '',
    ]
    sizes = [
        '// Generated by scripts/art/decor.py. Do not edit by hand.',
        '/** Each keepsake\'s size in art pixels; `foot` is how tall its footprint is (the part',
        ' *  that stands on the floor and blocks the way; 0 for a rug, walked over). */',
        'export const decorSizes: Record<string, { w: number; h: number; foot: number }> = {',
        *[f'  {k}: {{ w: {sp.w}, h: {sp.h}, foot: {ITEMS[k][1]} }},' for k, sp in built.items()],
        '};',
        '',
    ]
    for name, text in (('decor-assets.ts', images), ('decor-sizes.ts', sizes)):
        with open(os.path.join(worlds.ROOT, 'lib', name), 'w') as f:
            f.write('\n'.join(text))
    preview = os.environ.get('DECOR_PREVIEW')
    if preview:
        x = 4
        sheet = Canvas(sum(sp.w + 4 for sp in built.values()) + 4, max(sp.h for sp in built.values()) + 8)
        for sp in built.values():
            for yy in range(sp.h):
                for xx in range(sp.w):
                    c = sp.img.getpixel((xx, yy))
                    if c[3]:
                        sheet.img.putpixel((x + xx, 4 + yy), c)
            x += sp.w + 4
        sheet.save(preview, 6)
    print(f'ok decor: {len(built)} keepsakes')


if __name__ == '__main__':
    main()
