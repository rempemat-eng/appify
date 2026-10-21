"""Interface icon set (docs/vision/coherence-plan.md, step 4).

Every icon is drawn on the shared 16x16 icon grid from the canonical material ramps,
with the garden's rules: light from the upper left, three tones per part plus one
highlight, and a 1 px outline tinted by each part's material. Parts are painted back
to front; a part's outline cuts into what is behind it, which is what separates
overlapping pieces (crossed swords, a door in a wall).

Writes:
  lib/icon-art.ts            palette and rows for PixelIcon (generated; do not edit)
  art/icons/<name>.png       6x proofs, checked by `npm run check:sprites`
  docs/vision/icon-sheet.png contact sheet at 1x, 2x and 4x on paper, grass and night

Run: python3 scripts/art/icons.py && npx oxfmt --write lib/icon-art.ts
"""
from pathlib import Path

from PIL import Image

import style
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, RED, STONE, WOOD, WTR
from pixel import Canvas, disc, hex_rgba, oval

ROOT = Path(__file__).resolve().parents[2]
SIZE = 16
GRASS = MATERIALS['grass']
PATH = MATERIALS['path']
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# --- shapes ---------------------------------------------------------------
def R(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def poly(points):
    """Pixels whose centres fall inside the polygon (even-odd rule)."""
    out = set()
    for y in range(SIZE):
        for x in range(SIZE):
            px, py = x + 0.5, y + 0.5
            inside = False
            for i in range(len(points)):
                (x0, y0), (x1, y1) = points[i], points[i - 1]
                if (y0 > py) != (y1 > py) and px < (x1 - x0) * (py - y0) / (y1 - y0) + x0:
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def steps(*runs):
    """Rows of (y, x0, x1) runs, inclusive."""
    return {(x, y) for (y, x0, x1) in runs for x in range(x0, x1 + 1)}


def mirror(pts):
    return {(SIZE - 1 - x, y) for (x, y) in pts}


def flip(pts):
    return {(x, SIZE - 1 - y) for (x, y) in pts}


def clip(pts, y_max=SIZE - 2):
    return {(x, y) for (x, y) in pts if 0 < x < SIZE - 1 and 0 < y <= y_max}


# --- painting -------------------------------------------------------------
def outline_for(ramp):
    return style.outline_tone(hex_rgba(ramp[1 if len(ramp) > 3 else 0]))


def part(cv, pts, ramp, base, ring=True, highlight=True):
    """Fill a shape with three tones lit from the upper left and outline it."""
    pts = set(pts)
    if ring:
        oc = outline_for(ramp)
        for (x, y) in pts:
            for dx, dy in N4:
                n = (x + dx, y + dy)
                if n not in pts:
                    cv.set(*n, oc)
    top = len(ramp) - 1
    for (x, y) in pts:
        up, left = (x, y - 1) in pts, (x - 1, y) in pts
        down, right = (x, y + 1) in pts, (x + 1, y) in pts
        lit = not up or not left
        dark = not down or not right
        tone = base
        if lit and not dark:
            tone = base + 1
        elif dark and not lit:
            tone = base - 1
        elif lit and dark and not up:
            tone = base + 1
        if highlight and not up and not left and down and right:
            tone = base + 2
        cv.set(x, y, ramp[max(0, min(top, tone))])


def dots(cv, pts, color):
    for p in pts:
        cv.set(*p, color)


def icon(draw):
    cv = Canvas(SIZE, SIZE)
    draw(cv)
    return cv


# --- the set --------------------------------------------------------------
def home(cv):
    part(cv, R(10, 2, 2, 4), STONE, 2)
    part(cv, R(2, 8, 12, 6), CREAM, 2)
    part(cv, steps((1, 7, 8), (2, 6, 9), (3, 5, 10), (4, 4, 11), (5, 3, 12), (6, 2, 13), (7, 1, 14)), RED, 2)
    dots(cv, {(6, 4), (8, 5), (10, 4), (5, 6), (9, 6)}, RED[1])  # shingles
    part(cv, R(8, 10, 3, 4), WOOD, 2, highlight=False)
    part(cv, R(4, 10, 2, 2), WTR, 3)
    dots(cv, {(10, 12)}, GOLD[3])


def missions(cv):
    part(cv, R(1, 3, 5, 10), CREAM, 3)
    part(cv, R(6, 2, 5, 10), CREAM, 2)
    part(cv, R(11, 3, 4, 10), CREAM, 3)
    dots(cv, {(2, 4), (3, 4), (2, 5)}, LEAF[3])
    dots(cv, {(7, 4), (8, 4), (8, 5)}, WTR[3])
    dots(cv, {(2, 11), (4, 10), (7, 9), (9, 8), (12, 7)}, RED[2])
    dots(cv, {(12, 4), (14, 4), (13, 5), (12, 6), (14, 6)}, RED[1])


def nap(cv):
    moon = disc(7.5, 8.5, 6.2) - disc(10.6, 6.4, 5.2)
    part(cv, clip(moon), GOLD, 3)
    part(cv, {(12, 10), (11, 11), (12, 11), (13, 11), (12, 12)}, CREAM, 3, highlight=False)
    dots(cv, {(13, 3)}, CREAM[3])


def sword(tip_left=True):
    """Blade from the upper corner to a short crossguard, grip and pommel in the lower one."""
    blade = {(1, 1)} | {(i, i) for i in range(2, 10)} | {(i + 1, i) for i in range(1, 9)}
    guard = {(12, 8), (11, 9), (10, 10), (9, 11)}
    grip = {(11, 11), (12, 12)}
    pommel = {(13, 13)}
    parts = [blade, guard, grip, pommel]
    return parts if tip_left else [mirror(p) for p in parts]


def arena(cv):
    # one outline around each whole sword, so the crossguard reads as a solid bar
    for side in (True, False):
        blade, guard, grip, pommel = sword(side)
        part(cv, blade | guard | grip | pommel, STONE, 3)
        for (x, y) in guard:
            cv.set(x, y, GOLD[4] if (x, y) == min(guard) else GOLD[3])
        dots(cv, grip, WOOD[3])
        dots(cv, pommel, GOLD[2])


def shop(cv):
    part(cv, clip(oval(7.5, 10.6, 5.8, 4.3)), WOOD, 3)
    part(cv, {(5, 2), (6, 2), (9, 2), (10, 2)} | R(5, 3, 6, 1) | R(6, 4, 4, 2), WOOD, 3)
    part(cv, R(5, 6, 6, 1), RED, 3, highlight=False)
    part(cv, disc(11.5, 11.5, 2.6), GOLD, 3)
    dots(cv, {(11, 11)}, GOLD[2])


def shield(cv):
    outer = poly([(2, 2), (14, 2), (14, 8.5), (8, 14.8), (2, 8.5)])
    part(cv, outer, GOLD, 3)
    inner = poly([(4, 4), (12, 4), (12, 8.2), (8, 12.4), (4, 8.2)])
    part(cv, inner, LEAF, 3)
    part(cv, {(9, 5), (8, 6), (9, 6), (7, 7), (8, 7), (9, 7), (7, 8), (8, 8), (6, 9)}, CREAM, 2,
         ring=False)


def blade_of_grass(x, base_y, height, lean):
    pts = set()
    for t in range(height):
        y = base_y - t
        f = t / max(1, height - 1)
        cx = x + round(lean * f * f)
        pts.add((cx, y))
        if f < 0.55:
            pts.add((cx + 1, y))
    return pts


def grass(cv):
    """Blades of grass, flung by PixelBurst on hits, level-ups and crumbs (not the currency)."""
    part(cv, blade_of_grass(3, 13, 8, -2), GRASS, 2)
    part(cv, blade_of_grass(11, 13, 9, 3), GRASS, 2)
    part(cv, blade_of_grass(7, 13, 12, 1), GRASS, 3)


# the dust's surface per column: a low heap, highest just left of the middle
DUST_TOP = {2: 12, 3: 11, 4: 11, 5: 10, 6: 10, 7: 10, 8: 11, 9: 11, 10: 12}


def dream_dust(cv):
    """The currency (renamed from GRASS on 20 Oct): a stoppered vial of glowing dream dust.

    Violet glass for the dusk shade, the dust in candle gold heaped inside it, lit from
    the upper left, specks of dust afloat in the glass and a few motes drifting up and to
    the right out of the stopper. Motes are three pixels or fewer and carry no outline;
    the one sparkle is a small part with its own gold edge.
    """
    bulb = clip(disc(6.5, 10.4, 4.4))
    part(cv, bulb, NAP, 3)
    part(cv, R(5, 4, 3, 3), NAP, 3, highlight=False)  # neck
    part(cv, R(4, 3, 5, 1), NAP, 4, highlight=False)  # lip
    part(cv, R(5, 1, 3, 2), WOOD, 3, highlight=False)  # cork
    dust = {(x, y) for (x, y) in bulb if y >= DUST_TOP.get(x, SIZE)}
    for (x, y) in sorted(dust):
        top = (x, y - 1) not in dust
        left = (x - 1, y) not in dust
        low = (x, y + 1) not in dust or (x + 1, y) not in dust
        tone = 4 if top else 2 if low and not left else 3
        cv.set(x, y, GOLD[tone])
    dots(cv, {(5, 11), (8, 12), (6, 13)}, CREAM[3])  # sparks in the heap
    dots(cv, {(4, 8)}, CREAM[3])  # glint on the glass
    dots(cv, {(7, 8), (5, 7)}, GOLD[4])  # dust afloat in the glass
    part(cv, {(12, 4), (11, 5), (12, 5), (13, 5), (12, 6)}, GOLD, 4, highlight=False)
    dots(cv, {(12, 5)}, CREAM[3])
    dots(cv, {(10, 1), (14, 9)}, GOLD[3])


def time(cv):
    part(cv, R(2, 3, 1, 10), WOOD, 2, highlight=False)
    part(cv, R(13, 3, 1, 10), WOOD, 2, highlight=False)
    glass = steps((3, 4, 11), (4, 4, 11), (5, 5, 10), (6, 6, 9), (7, 7, 8), (8, 7, 8), (9, 6, 9),
                  (10, 5, 10), (11, 4, 11), (12, 4, 11))
    part(cv, glass, WTR, 4)
    dots(cv, steps((5, 6, 9), (6, 7, 8)), GOLD[3])
    dots(cv, {(7, 8), (8, 9)}, GOLD[3])
    dots(cv, steps((11, 6, 9), (12, 5, 10)), GOLD[2])
    dots(cv, {(7, 11), (8, 11), (8, 10)}, GOLD[3])
    part(cv, R(1, 1, 14, 2), WOOD, 3)
    part(cv, R(1, 13, 14, 2), WOOD, 3)


def heart(cv):
    shape = disc(5.2, 6.2, 3.3) | disc(10.8, 6.2, 3.3) | poly([(1.9, 7), (14.1, 7), (8, 13.8)])
    part(cv, clip(shape), RED, 3)
    dots(cv, {(4, 5)}, CREAM[3])


def menu(cv):
    for y in (2, 7, 12):
        part(cv, R(2, y, 12, 2), WOOD, 3, highlight=False)


def companion(cv):
    part(cv, clip(oval(8, 11.4, 3.7, 2.7)), PATH, 3)
    for toe in (R(2, 6, 2, 3), R(5, 3, 2, 3), R(9, 3, 2, 3), R(12, 6, 2, 3)):
        part(cv, toe, PATH, 3, highlight=False)


def bag(cv):
    part(cv, {(6, 2), (7, 2), (8, 2), (9, 2), (6, 3), (9, 3), (6, 4), (9, 4)}, WOOD, 2, highlight=False)
    body = R(3, 5, 10, 9) - {(3, 5), (12, 5), (3, 13), (12, 13)}
    part(cv, body, LEAF, 3)
    part(cv, R(3, 5, 10, 4) - {(3, 5), (12, 5)}, LEAF, 4)
    part(cv, R(5, 10, 6, 3), LEAF, 2, highlight=False)
    dots(cv, {(7, 9), (8, 9)}, GOLD[3])


def journal(cv):
    part(cv, R(11, 3, 3, 10), CREAM, 3, highlight=False)
    dots(cv, {(12, 5), (12, 7), (12, 9), (12, 11)}, CREAM[1])
    part(cv, R(2, 2, 10, 12), LEAF, 3)
    part(cv, R(2, 2, 2, 12), LEAF, 2, highlight=False)
    part(cv, R(6, 5, 4, 2), CREAM, 3, ring=False)
    part(cv, {(9, 13), (10, 13), (9, 14), (10, 14)}, RED, 3, highlight=False)


def garden(cv):
    part(cv, poly([(4, 9.5), (12, 9.5), (11, 15), (5, 15)]), RED, 3)
    part(cv, R(3, 8, 10, 2), RED, 3)
    part(cv, R(7, 4, 2, 4), LEAF, 3, highlight=False)
    part(cv, oval(4.8, 4.6, 2.6, 1.6), GRASS, 3)
    part(cv, oval(11.0, 3.6, 2.8, 1.7), GRASS, 3)


def rhythm(cv):
    """A day-and-night dial: the lit half gold, the far half night, one outline."""
    dial = disc(8, 8, 6.3)
    part(cv, dial, GOLD, 3)
    night = {(x, y) for (x, y) in dial if x + y > 15}
    shade = {(x, y) for (x, y) in night if (x + 1, y) not in dial or (x, y + 1) not in dial}
    dots(cv, night - shade, NAP[2])
    dots(cv, shade, NAP[1])
    dots(cv, {(x, 15 - x + 1) for x in range(3, 14) if (x, 16 - x) in dial}, NAP[3])
    dots(cv, {(11, 10), (9, 12), (12, 11)}, CREAM[3])
    dots(cv, {(5, 5), (6, 5), (5, 6)}, GOLD[4])


def settings(cv):
    gear = disc(8, 8, 4.6) | R(7, 1, 2, 3) | R(7, 12, 2, 3) | R(1, 7, 3, 2) | R(12, 7, 3, 2)
    gear |= R(3, 3, 2, 2) | R(11, 3, 2, 2) | R(3, 11, 2, 2) | R(11, 11, 2, 2)
    part(cv, gear - disc(8, 8, 1.7), STONE, 3)


def close(cv):
    stroke = {(i, i) for i in range(3, 13)} | {(i + 1, i) for i in range(3, 12)}
    part(cv, stroke | mirror(stroke), RED, 3, highlight=False)


def sun(cv):
    for ray in (R(7, 1, 2, 2), R(7, 13, 2, 2), R(1, 7, 2, 2), R(13, 7, 2, 2),
                {(3, 3), (4, 4)}, {(12, 3), (11, 4)}, {(3, 12), (4, 11)}, {(12, 12), (11, 11)}):
        part(cv, ray, GOLD, 3, highlight=False)
    part(cv, disc(8, 8, 3.7), GOLD, 3)


def sprout(cv):
    part(cv, oval(8, 13.2, 5.6, 1.8), PATH, 2)
    part(cv, R(7, 6, 2, 6), LEAF, 3, highlight=False)
    part(cv, oval(4.8, 6.4, 2.8, 1.7), GRASS, 3)
    part(cv, oval(11.2, 5.0, 3.0, 1.8), GRASS, 3)


def bell(cv):
    part(cv, disc(8, 13.6, 1.5), GOLD, 2, highlight=False)
    body = steps((3, 6, 9), (4, 5, 10), (5, 4, 11), (6, 4, 11), (7, 4, 11), (8, 3, 12), (9, 3, 12),
                 (10, 2, 13), (11, 2, 13))
    part(cv, body, GOLD, 3)
    part(cv, R(7, 1, 2, 2), GOLD, 2, highlight=False)


def fast(cv):
    part(cv, poly([(1.5, 2.5), (8.5, 8), (1.5, 13.5)]), LEAF, 3)
    part(cv, poly([(7.5, 2.5), (14.5, 8), (7.5, 13.5)]), LEAF, 3)


def chevron_down(cv):
    v = {(2 + i, 4 + i) for i in range(6)} | {(3 + i, 4 + i) for i in range(6)}
    part(cv, v | mirror(v), WOOD, 3, highlight=False)


def chevron_up(cv):
    v = {(2 + i, 4 + i) for i in range(6)} | {(3 + i, 4 + i) for i in range(6)}
    part(cv, flip(v | mirror(v)), WOOD, 3, highlight=False)


def friends(cv):
    part(cv, clip(oval(10.6, 13, 4.0, 3.2)), NAP, 3)
    part(cv, disc(10.6, 5.2, 2.6), NAP, 3)
    part(cv, clip(oval(6.0, 13.6, 4.4, 3.2)), LEAF, 3)
    part(cv, disc(6.0, 6.6, 2.8), LEAF, 3)


def arrow_up(cv):
    part(cv, R(6, 7, 4, 7) | poly([(1.5, 8), (8, 1.5), (14.5, 8)]), LEAF, 3)


def arrow_down(cv):
    part(cv, flip(R(6, 7, 4, 7) | poly([(1.5, 8), (8, 1.5), (14.5, 8)])), RED, 3)


def energy(cv):
    part(cv, poly([(9.5, 1), (3, 9), (7.5, 9), (6, 15), (13, 6.5), (8.5, 6.5), (11, 1)]), GOLD, 3)


def check(cv):
    stroke = {(2 + i, 8 + i) for i in range(5)} | {(3 + i, 8 + i) for i in range(5)}
    stroke |= {(6 + i, 12 - i) for i in range(8)} | {(7 + i, 12 - i) for i in range(8)}
    part(cv, clip(stroke), LEAF, 3, highlight=False)


def eye(cv):
    part(cv, poly([(1, 8), (5, 4.2), (11, 4.2), (15, 8), (11, 11.8), (5, 11.8)]), CREAM, 3)
    part(cv, disc(8, 8, 2.6), WTR, 2)
    dots(cv, {(8, 8), (7, 8), (8, 7), (7, 7)}, WTR[0])
    dots(cv, {(7, 7)}, CREAM[3])


def lock(cv):
    part(cv, {(5, y) for y in range(3, 8)} | {(10, y) for y in range(3, 8)} | R(6, 2, 4, 1),
         STONE, 3, highlight=False)
    part(cv, R(3, 7, 10, 7), GOLD, 3)
    dots(cv, {(7, 9), (8, 9), (7, 10), (8, 10), (8, 11)}, GOLD[0])


def tree(cv):
    part(cv, R(7, 10, 2, 5), WOOD, 3, highlight=False)
    part(cv, clip(disc(8, 6.6, 5.6)), LEAF, 3)
    dots(cv, {(6, 4), (10, 7), (5, 8)}, LEAF[4])
    dots(cv, {(10, 4), (7, 8)}, RED[3])


def flower(cv):
    part(cv, R(7, 9, 2, 6), LEAF, 3, highlight=False)
    part(cv, oval(4.6, 11.6, 2.6, 1.4), GRASS, 3)
    part(cv, oval(11.4, 12.2, 2.6, 1.4), GRASS, 3)
    for (x, y) in ((8, 2.6), (4.6, 6), (11.4, 6), (6, 9.2), (10, 9.2)):
        part(cv, disc(x, y, 2.1), RED, 3, highlight=False)
    part(cv, disc(8, 6.4, 1.8), GOLD, 3, highlight=False)


def signpost(cv):
    part(cv, R(7, 6, 2, 9), WOOD, 2, highlight=False)
    part(cv, poly([(2, 2), (12, 2), (14.6, 4.5), (12, 7), (2, 7)]), WOOD, 3)
    dots(cv, {(4, 4), (5, 4), (6, 4), (8, 4), (9, 4), (10, 4)}, WOOD[1])


def bowl(cv):
    part(cv, steps((7, 4, 5), (6, 6, 8), (7, 9, 11), (6, 10, 11), (8, 6, 8)), GOLD, 3, highlight=False)
    part(cv, steps((9, 2, 13), (10, 2, 13), (11, 3, 12), (12, 4, 11), (13, 5, 10)), RED, 3)
    dots(cv, {(3, 10), (4, 10), (5, 10), (6, 10)}, RED[4])


ICONS = {
    'home': home, 'missions': missions, 'nap': nap, 'arena': arena, 'shop': shop,
    'shield': shield, 'grass': grass, 'time': time, 'heart': heart, 'menu': menu,
    'companion': companion, 'bag': bag, 'journal': journal, 'garden': garden,
    'rhythm': rhythm, 'settings': settings, 'close': close, 'sun': sun, 'moon': nap,
    'sprout': sprout, 'bell': bell, 'fast': fast, 'chevronDown': chevron_down,
    'chevronUp': chevron_up, 'friends': friends, 'arrowUp': arrow_up,
    'arrowDown': arrow_down, 'energy': energy, 'check': check, 'eye': eye, 'lock': lock,
    'tree': tree, 'flower': flower, 'signpost': signpost, 'bowl': bowl,
    'dreamDust': dream_dust,
}

KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


def hexcode(c):
    return '#{:02X}{:02X}{:02X}'.format(*c[:3])


def main():
    drawn = {name: icon(fn) for name, fn in ICONS.items()}
    palette, rows = [], {}
    for name, cv in drawn.items():
        lines = []
        for y in range(SIZE):
            line = ''
            for x in range(SIZE):
                c = cv.get(x, y)
                if c[3] == 0:
                    line += '.'
                    continue
                code = hexcode(c)
                if code not in palette:
                    palette.append(code)
                line += KEYS[palette.index(code)]
            lines.append(line)
        rows[name] = lines
    assert len(palette) <= len(KEYS), 'icon palette too large'

    out = ['// Generated by scripts/art/icons.py (coherence plan, step 4). Do not edit by hand.',
           '/* oxlint-disable */', '',
           f'export const iconPalette = {palette!r} as const;'.replace("'", '"'), '',
           '/** 16x16 rows; each character indexes iconPalette, "." is transparent. */',
           'export const iconRows = {']
    for name, lines in rows.items():
        out.append(f'  {name}: [')
        out += [f'    "{line}",' for line in lines]
        out.append('  ],')
    out += ['} as const;', '', 'export type IconName = keyof typeof iconRows;', '']
    (ROOT / 'lib' / 'icon-art.ts').write_text('\n'.join(out))

    proofs = ROOT / 'art' / 'icons'
    proofs.mkdir(parents=True, exist_ok=True)
    for old in proofs.glob('*.png'):
        old.unlink()
    for name, cv in drawn.items():
        cv.save(str(proofs / f'{name}.png'), scale=6)

    # contact sheet: each icon at 1x, 2x and 4x on paper, grass and night
    grounds = [hex_rgba('#FBF4E4'), hex_rgba(GRASS[2]), hex_rgba(NAP[1])]
    cell = SIZE * 4 + 8
    sheet = Image.new('RGBA', (len(grounds) * (SIZE * 7 + 24) + 8, len(drawn) * cell + 8), (40, 34, 30, 255))
    for row, (name, cv) in enumerate(drawn.items()):
        for col, ground in enumerate(grounds):
            ox = 8 + col * (SIZE * 7 + 24)
            oy = 8 + row * cell
            tile = Image.new('RGBA', (SIZE * 7 + 16, cell - 4), ground)
            x = 4
            for scale in (1, 2, 4):
                img = cv.img.resize((SIZE * scale, SIZE * scale), Image.NEAREST)
                tile.alpha_composite(img, (x, (cell - 4 - SIZE * scale) // 2))
                x += SIZE * scale + 4
            sheet.alpha_composite(tile, (ox, oy))
    sheet.save(ROOT / 'docs' / 'vision' / 'icon-sheet.png', optimize=True)
    print(f'{len(drawn)} icons, {len(palette)} colours')


if __name__ == '__main__':
    main()
