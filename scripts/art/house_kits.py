"""House-style design kits, one per environment (docs/vision/house-style.md, "Kits").

Matt, 20 Oct ~11:35: "you can use the house style where it fits but mindful of the
environment. but within the same environment you can reuse it. but to make it less
repetative perhaps come up with a few different designs that you can then reuse".

So each environment has its own kit of reusable pieces, every piece in the house style
(house palette, parts and clusters, light from the upper left, edge-tone outline) and in
a few distinct variants:

    front(env, v)    a whole building front: wall, roof edge, door, windows, sign
    door(env, v)     a door in its surround, on a patch of the environment's wall
    window(env, v)   a window in its wall
    roof(env, v)     the roof or top edge as it meets the wall
    sign(env, v)     a sign, awning, banner or label
    prop(env, v)     a small prop that belongs there

`env` is one of ENVS; `v` is 0 .. variants(env, piece) - 1; `front(env, v, cw)` also takes a
colourway (see COLOURWAYS). Everything is deterministic and sized by the scale table
(size-guide.md 3: an adult 25 px, a door 32 x 14, a shop's or double door 32 x 22, a window
16 x 12, a storey 32, a shop storey 44). A front is a sprite with its
outline; a door, window or roof is drawn into a patch of its own wall, which is how a zone
uses it (draw the wall, then the pieces into it).

    python3 scripts/art/house_kits.py [OUT_DIR] [env ...]
    python3 scripts/art/house_kits.py --check

writes one kit sheet per environment (OUT_DIR/kit-<env>.png, at 3x, with today's
equivalents on the left), a sheet of every front (fronts.png) and one street per setting
(streets.png) at 2x, and prints the style lint, the detail bar and the logic check for
every front in every colourway. `--check` runs only the logic check and the colourway
picker on many streets, and exits non-zero on any fault.
Nothing in the game reads this file yet; the lanes draw from it as their zones move to the
house style.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw  # noqa: E402

import house_palette as hp  # noqa: E402
from pixel import Canvas, disc, noise2, smooth_noise  # noqa: E402
from style_sheet import (T, sib, step, rect, part, courses, boards, bricks, roof_rows, plates, grain,  # noqa: E402
                         ground, glass, frame, overhang, cylinder, outline, cast, leafy, wall_light,
                         stone_pick, plaster, rivets, banner, H_GRAIN, V_GRAIN, pebble, tone_at, soft_patches)

ENVS = ('valley', 'cogsworth', 'sunstone', 'hearthold', 'neon', 'halcyon', 'lumen')
TITLES = {
    'valley': 'Valley and isles: cottages', 'cogsworth': 'Cogsworth: brick and iron',
    'sunstone': 'Sunstone Reach: frontier timber and adobe', 'hearthold': 'Hearthold: castle stone',
    'neon': 'Neon Harbour: shopfronts and facades', 'halcyon': 'Halcyon Station: modules',
    'lumen': 'Lumen: habitats and regolith',
}


# --- colourways (Matt, 20 Oct 12:09) -------------------------------------------------------
# "to increase variety even more you can use the same building and switch some of the colors
# (like the door, banners/ cloth and other pieces where it makes sense that the color would
# change)". A front keeps its structure and takes a named colourway, which repaints only the
# parts a resident or owner would paint: doors and hatches, shutters, painted window frames
# and trim, awnings, banners, curtains and other cloth, sign boards, flower pots and the
# flowers in them, painted cladding, neon glass, livery stripes. Stone, brick, adobe, metal
# panels, natural roof tiles and slates, timber left natural and glass never change.
#
# Every value is a ramp of the house palette (six tones by the one rule, its own edge tone
# for the outline), so a repainted part shades and outlines exactly as before. Roles:
#   door      the door leaf or hatch          shutter  shutters, roller shutters
#   trim      painted frames, risers, posts   cloth    awnings, banners, curtains (the main colour)
#   cloth2    an awning's second stripe       sign     sign boards and fascias
#   ink       a sign's lettering or charge    flower   window-box and pot flowers
#   pot       flower pots (terracotta or glazed)        cladding  painted boards on a wall
#   glow      neon tubes, lightboxes, status lights     livery    a module's painted stripe
PAINTED = ('door', 'shutter', 'trim', 'cloth', 'cloth2', 'sign', 'ink', 'flower', 'pot', 'cladding', 'glow', 'livery')

COLOURWAYS = {
    # the valley and the isles: painted cottage colours, a door and its shutters often matched
    'valley': [
        ('cornflower', dict(door='sky', shutter='sky', trim='sky', cloth='berry', sign='sky', ink='brass', flower='berry',
                            pot='clay', cladding='plaster')),
        ('heather', dict(door='dusk', shutter='dusk', trim='dusk_cool', cloth='berry_cool', sign='dusk', ink='plaster', flower='brass',
                         pot='clay', cladding='sand')),
        ('sage', dict(door='leaf', shutter='leaf_cool', trim='leaf_cool', cloth='dusk', sign='leaf', ink='plaster', flower='brass',
                      pot='plaster', cladding='sky')),
        ('poppy', dict(door='berry', shutter='berry_cool', trim='berry_cool', cloth='sky', sign='berry', ink='brass', flower='dusk',
                       pot='clay', cladding='lagoon')),
        ('harbour', dict(door='lagoon', shutter='lagoon', trim='lagoon', cloth='plaster', sign='lagoon', ink='plaster', flower='berry',
                         pot='sky', cladding='berry')),
    ],
    # Cogsworth: Victorian enamel and brass-age paints, gilt lettering, cream sashes
    'cogsworth': [
        ('oxblood', dict(door='berry_cool', shutter='berry_cool', trim='plaster', cloth='plaster', cloth2='berry_cool', sign='berry_cool',
                         ink='brass', flower='berry', pot='clay')),
        ('bottle green', dict(door='copper_cool', shutter='copper_cool', trim='plaster', cloth='brass', cloth2='copper_cool',
                              sign='copper_cool', ink='brass', flower='brass', pot='iron')),
        ('prussian', dict(door='sky_cool', shutter='sky_cool', trim='plaster', cloth='berry', cloth2='plaster', sign='sky_cool',
                          ink='brass', flower='plaster', pot='clay')),
        ('black and gilt', dict(door='iron', shutter='iron', trim='iron_warm', cloth='dusk', cloth2='plaster', sign='iron',
                                ink='brass', flower='dusk', pot='iron')),
    ],
    # Sunstone Reach: sun-faded cloth and painted boards; the wood shows where paint wore off
    'sunstone': [
        ('faded red', dict(door='sky', shutter='sky', trim='bleached', cloth='berry_warm', cloth2='plaster', sign='berry_warm',
                           ink='plaster', flower='brass', pot='clay', cladding='berry')),
        ('faded blue', dict(door='berry_warm', shutter='berry_warm', trim='bleached', cloth='sky', cloth2='plaster', sign='sky',
                            ink='plaster', flower='berry', pot='clay', cladding='sky')),
        ('mustard', dict(door='cactus', shutter='cactus', trim='bleached_cool', cloth='brass', cloth2='plaster', sign='brass_cool',
                         ink='timber', flower='berry', pot='adobe', cladding='brass')),
        ('sage', dict(door='brass_cool', shutter='brass_cool', trim='bleached', cloth='lagoon', cloth2='plaster', sign='cactus',
                      ink='plaster', flower='dusk', pot='clay', cladding='cactus')),
        ('bare wood', dict(door='bleached', shutter='bleached', trim='timber', cloth='plaster', cloth2='berry', sign='timber',
                           ink='plaster', flower='brass', pot='adobe', cladding='bleached')),
    ],
    # Hearthold: heraldic cloth (purpure, gules, azure, vert, or) and oak or painted doors
    'hearthold': [
        ('purpure', dict(door='timber', shutter='timber', cloth='dusk', sign='dusk', ink='brass', flower='plaster', pot='clay')),
        ('gules', dict(door='timber_cool', shutter='timber_cool', cloth='berry', sign='berry', ink='brass', flower='brass', pot='clay')),
        ('azure', dict(door='berry_cool', shutter='timber', cloth='sky', sign='sky', ink='plaster', flower='berry', pot='clay')),
        ('vert', dict(door='timber_warm', shutter='timber_warm', cloth='leaf', sign='leaf', ink='brass', flower='dusk', pot='clay')),
        ('or', dict(door='leaf_cool', shutter='leaf_cool', cloth='brass', sign='brass', ink='berry_cool', flower='berry', pot='clay')),
    ],
    # Neon Harbour: signage colours on awnings, shutters and the glass of the tubes
    'neon': [
        ('rose', dict(door='lagoon_cool', shutter='sky', trim='iron', cloth='berry', cloth2='plaster', sign='asphalt', ink='plaster',
                      glow='neon_pink', flower='berry', pot='concrete')),
        ('teal', dict(door='dusk', shutter='brass', trim='iron', cloth='lagoon', cloth2='plaster', sign='asphalt', ink='plaster',
                      glow='neon_cyan', flower='brass', pot='concrete')),
        ('amber', dict(door='sky_cool', shutter='berry', trim='iron', cloth='brass', cloth2='asphalt', sign='asphalt', ink='plaster',
                       glow='lava', flower='plaster', pot='clay')),
        ('mint', dict(door='berry_cool', shutter='dusk', trim='iron', cloth='copper', cloth2='plaster', sign='asphalt', ink='plaster',
                      glow='glowflora', flower='dusk', pot='concrete')),
        ('violet', dict(door='copper_cool', shutter='lagoon', trim='iron', cloth='dusk', cloth2='plaster', sign='asphalt', ink='plaster',
                        glow='neon_pink', flower='brass', pot='iron')),
    ],
    # Halcyon Station: a module's livery stripe and the colour its hatches are painted
    'halcyon': [
        ('rescue red', dict(door='berry', livery='berry', glow='neon_cyan', trim='panel', cloth='berry', flower='glowflora', pot='hull')),
        ('signal blue', dict(door='sky', livery='sky', glow='glowflora', trim='panel', cloth='sky', flower='brass', pot='hull')),
        ('hazard ochre', dict(door='brass', livery='brass', glow='neon_cyan', trim='panel', cloth='brass', flower='berry', pot='hull')),
        ('lagoon', dict(door='lagoon', livery='lagoon', glow='lamp', trim='panel', cloth='lagoon', flower='dusk', pot='hull')),
    ],
    # Lumen: the same livery and hatch paints, out on the moon
    'lumen': [
        ('rescue red', dict(door='berry', livery='berry', glow='glowflora', trim='hull', cloth='berry')),
        ('signal blue', dict(door='sky', livery='sky', glow='neon_cyan', trim='hull', cloth='sky')),
        ('hazard ochre', dict(door='brass', livery='brass', glow='glowflora', trim='hull', cloth='brass')),
        ('dusk', dict(door='dusk', livery='dusk', glow='lamp', trim='hull', cloth='dusk')),
    ],
}
# each front's own colourway when none is asked for (index into its environment's list)
DEFAULT_CW = {'valley': (0, 3, 4, 1), 'cogsworth': (1, 0, 2, 3), 'sunstone': (4, 1, 0, 2), 'hearthold': (0, 1, 4, 3),
              'neon': (0, 1, 2, 3), 'halcyon': (0, 1, 2, 3), 'lumen': (0, 1, 2, 3)}

PAINT: dict = {}   # the colourway being drawn (role -> ramp); empty means each part's own default


def paint(role: str, default: str) -> str:
    """The ramp a painted part takes: the current colourway's, or the part's own default."""
    return PAINT.get(role) or default


def colourway(env: str, cw) -> tuple:
    """(name, roles) of a colourway, by index or by name."""
    ways = COLOURWAYS[env]
    if isinstance(cw, str):
        return next(w for w in ways if w[0] == cw)
    return ways[cw % len(ways)]


# --- pictograms (signs use pictures, never words: world-atlas.md) ---------------------------
PICTO = {
    'cup': ['..+.+..', '...+...', '######.', '#####.#', '#####.#', '######.', '.####..'],
    'bread': ['.......', '..###..', '.#+#+#.', '#######', '#######', '.#####.', '.......'],
    'fish': ['.......', '#...##.', '##.##+#', '#######', '##.####', '#...##.', '.......'],
    'key': ['.###...', '#...#..', '#...####', '.###.#.#', '.....#..', '.......', '.......'],
    'moon': ['..###..', '.##....', '##.....', '##.....', '##.....', '.##....', '..###..'],
    'gear': ['.#.#.#.', '#######', '##...##', '##.+.##', '##...##', '#######', '.#.#.#.'],
    'mug': ['++++...', '####...', '####.#.', '####..#', '####.#.', '####...', '.......'],
    'shoe': ['.#...#.', '#.....#', '#.....#', '#.....#', '##...##', '.##.##.', '.......'],
    'star': ['...#...', '..###..', '#######', '.#####.', '..###..', '.##.##.', '##...##'],
    'sack': ['..#.#..', '...#...', '..###..', '.##+##.', '#######', '#######', '.#####.'],
    'anchor': ['..###..', '...#...', '#######', '...#...', '#..#..#', '##.#.##', '.#####.'],
    'bowl': ['#.#.#..', '.#.#.#.', '.......', '#######', '.#####.', '..###..', '.......'],
    'shield': ['#######', '#+..#.#', '#+..#.#', '#######', '.#.#.#.', '..#.#..', '...#...'],
    'bolt': ['...##..', '..##...', '.####..', '...##..', '..##...', '.##....', '#......'],
    'leaf': ['....##.', '..####.', '.##+##.', '.####..', '..#....', '.#.....', '#......'],
    'bed': ['#......', '#.##...', '#######', '#######', '#.....#', '.......', '.......'],
    'pot': ['.#.#.#.', '.......', '#######', '.#####.', '.#####.', '..###..', '.......'],
}


def picto(cv: Canvas, x, y, name, ramp='brass', base=4):
    """A pictogram, lit tone on its top rows, a tone down at its foot."""
    rows = PICTO[name]
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '#':
                cv.set(x + c, y + r, T(ramp, base if r < len(rows) - 2 else base - 1))
            elif ch == '+':
                cv.set(x + c, y + r, T(ramp, base + 1))


# --- walls ---------------------------------------------------------------------------------
def wall(cv: Canvas, x0, y0, w, h, kind, seed=0, avoid=()):
    """A wall of one material, lit at its upper left. The kinds are each environment's
    building materials; nothing else in a kit invents its own. Painted boards take the
    colourway's cladding paint. `avoid` (boxes x0, y0, x1, y1) keeps a bulkhead's equipment
    bays out from behind doors and windows, where they would only show as cut-off noise."""
    pts = rect(x0, y0, w, h)
    if kind in ('plaster', 'whitewash', 'pink'):
        fam = {'plaster': 'plaster', 'whitewash': 'plaster', 'pink': 'plaster'}[kind]
        plaster(cv, x0, y0, w, h, seed, fam)
        if kind == 'whitewash':   # limewash: the plaster a tone lighter
            for p in pts:
                step(cv, p[0], p[1], 1)
        # the splash zone: near the foot the render has worn back to the rubble under it, in
        # patches, with green damp in the lowest joints (rain splashing off the ground)
        sub = Canvas(cv.w, cv.h)
        courses(sub, x0, y0 + h - 9, w, 9, stone_pick(('stone', 'ashlar'), seed + 4), course=4, lengths=(4, 7),
                seam=T('stone_cool', 1), seed=seed + 4)
        for (x, y) in rect(x0, y0 + h - 9, w, 9):
            d = (y - (y0 + h - 9)) / 9
            if smooth_noise(x, y, 4, seed + 5) > 0.78 - 0.32 * d:
                c = sub.get(x, y)
                if c[3]:
                    cv.set(x, y, c)
                    if y >= y0 + h - 2 and smooth_noise(x, y, 2, seed + 6) > 0.5:
                        cv.set(x, y, T('leaf_cool', 2))
        if kind == 'pink':
            for p in pts:
                if smooth_noise(p[0], p[1], 9, seed) > 0.0:
                    hit = tone_at(cv, *p)
                    if hit:
                        cv.set(p[0], p[1], T('berry', min(5, hit[1] + 2)) if hit[1] >= 3 else T('plaster', hit[1]))
    elif kind == 'drystone':
        courses(cv, x0, y0, w, h, stone_pick(('stone', 'ashlar'), seed), course=5, lengths=(5, 10),
                seam=T('stone_cool', 1), seed=seed)
        grain(cv, pts, 0.05, seed + 1, lit=wall_light(x0, y0, w, h))
    elif kind == 'ashlar':
        courses(cv, x0, y0, w, h, stone_pick(('ashlar', 'ashlar', 'stone'), seed), course=6, lengths=(9, 15),
                seam=T('stone_cool', 1), seed=seed)
        grain(cv, pts, 0.03, seed + 1, lit=wall_light(x0, y0, w, h))
    elif kind == 'rubble':
        courses(cv, x0, y0, w, h, stone_pick(('stone', 'stone', 'ashlar'), seed), course=6, lengths=(6, 11),
                seam=T('stone_cool', 1), seed=seed)
    elif kind in ('brick', 'brick_soot'):
        bricks(cv, x0, y0, w, h, seed, soot_rows=3 if kind == 'brick_soot' else 1, moss_rows=1)
    elif kind == 'stock':   # London stock: yellow-grey brick
        bricks(cv, x0, y0, w, h, seed, soot_rows=2)
        for p in pts:
            hit = tone_at(cv, *p)
            if hit and hp.family(hit[0]) == 'clay':
                cv.set(p[0], p[1], T(sib('sand', noise2(p[0] // 8, p[1] // 4, seed), 0.3), hit[1] - 1))
    elif kind in ('boards_sky', 'boards_berry', 'boards_timber', 'bleached', 'boards_lagoon'):
        fam = {'boards_sky': 'sky', 'boards_berry': 'berry', 'boards_timber': 'timber', 'bleached': 'bleached',
               'boards_lagoon': 'lagoon'}[kind]
        if fam not in ('bleached', 'timber'):   # painted cladding: the colourway's paint
            fam = hp.family(paint('cladding', fam))
        mix = 'timber' if fam == 'bleached' else fam
        boards(cv, x0, y0, w, h, lambda b, s: (sib(fam if noise2(b, s, 3) < 0.8 else mix, noise2(b, s, 4), 0.3),
                                              3 + (1 if b < 2 and fam == 'bleached' else 0)), board=4, seed=seed)
        if fam not in ('bleached', 'timber'):
            for (x, y) in pts:   # paint worn back to the wood in clusters, most at the foot
                if smooth_noise(x, y, 3, seed + 6) > 0.78 - 0.1 * (y - y0) / max(1, h) and (y - y0) % 4 in (1, 2):
                    cv.set(x, y, T('bleached', 3))
        grain(cv, pts, 0.04, seed + 1, shapes=H_GRAIN, lit=wall_light(x0, y0, w, h))
    elif kind == 'adobe':
        for (x, y) in pts:
            cv.set(x, y, T(sib('adobe', smooth_noise(x, y, 8, seed), 0.2), 3))
        soft_patches(cv, pts, seed + 1, scale=5, light=0.68, dark=0.24)
        grain(cv, pts, 0.035, seed + 2, lit=wall_light(x0, y0, w, h), up=0.25, down=0.2)
        for i in range(w * h // 700):   # cracks in the render, and patches where it fell to the mud brick
            cx, cy = x0 + int(noise2(i, 1, seed) * (w - 6)), y0 + int(noise2(i, 2, seed) * (h - 4))
            if noise2(i, 3, seed) < 0.5:
                for k in range(4):
                    cv.set(cx + k // 2, cy + k, T('adobe', 1))
            else:
                part(cv, cx, cy, 6, 3, 'adobe_cool', 2, glint=False)
    elif kind == 'corrugated':   # corrugated iron: each corrugation a lit crest and a shaded trough, 2 px each,
        for (x, y) in pts:           # sheets lapped every 30 rows, rust running down from the laps in streaks
            j = (x - x0) % 4
            k = 3 if j < 2 else 2
            if j == 0 and (y - y0) % 30 < 2:
                k = 4
            sheet_y = (y - y0) % 30
            run = 4 + int(noise2((x - x0) // 4, (y - y0) // 30, seed) * 12)
            rust = smooth_noise((x - x0) // 4 * 4, (y - y0) // 30, 2, seed) > 0.62 and sheet_y < run
            if (y - y0) % 30 == 29:
                k = 1                                   # the lap
            cv.set(x, y, T('clay_cool', k) if rust and k > 1 else T(sib('iron', noise2((x - x0) // 16, (y - y0) // 30, seed), 0.3), k))
    elif kind == 'concrete':
        courses(cv, x0, y0, w, h, lambda ci, si: (sib('concrete', noise2(ci, si, seed)), 2 + (1 if noise2(ci, si, 5) > 0.7 else 0)),
                course=16, lengths=(16, 24), seam=T('asphalt', 1), seed=seed)
        grain(cv, pts, 0.06, seed + 3, lit=wall_light(x0, y0, w, h), up=0.15, down=0.4)
        for py in range(y0 + 4, y0 + h - 2, 8):   # the formwork's tie holes, two to a board, in rows
            for px in range(x0 + 5 + (4 if (py - y0) % 16 else 0), x0 + w - 2, 12):
                cv.set(px, py, T('asphalt', 1)); cv.set(px + 1, py, T('concrete', 1))
                cv.set(px, py + 1, T('concrete', 4))
        for x in range(x0, x0 + w):   # rain streaks
            if noise2(x, 0, seed + 4) < 0.1:
                for y in range(y0 + 1, y0 + 6 + int(noise2(x, 1, seed) * 10)):
                    step(cv, x, y, -1)
    elif kind == 'tile':     # glazed tiles, the old city's shop walls: a field, a dado, a frieze
        dado = y0 + h - 12       # the lowest courses in dark glazed tiles that take the kicks
        for (x, y) in pts:
            j, r = (x - x0) % 5, (y - y0) % 5
            ti = ((x - x0) // 5, (y - y0) // 5)
            band = y >= dado or ti[1] == 2          # the dado, and a one-tile frieze high on the wall
            field = 'concrete_warm' if (ti[0] + ti[1]) % 2 else 'concrete'   # the field laid in two glazes, chequered
            rp = 'lagoon_cool' if band else field
            k = 1 if (j == 4 or r == 4) else 3 if (j == 0 or r == 0) else 2
            if band and r == 1 and j in (1, 2):
                k = 4                                  # the glaze catches the light at its top left
            cv.set(x, y, T(rp, k))
        for x in range(x0, x0 + w):                    # a bullnose tile capping the dado
            cv.set(x, dado - 1, T('lagoon', 4)); cv.set(x, dado - 2, T('lagoon_cool', 2))
        grain(cv, rect(x0, y0, w, dado - 2 - y0), 0.03, seed + 2, shapes=H_GRAIN[:2], swap=0.4, up=0.1, down=0.5)
    elif kind == 'cladding':  # profiled steel sheet on a harbour shed: ribs, laps, fixings, rust runs
        for (x, y) in pts:
            sheet_i = (x - x0) // 24
            j = (x - x0) % 6
            k = 4 if j == 0 else 3 if j in (1, 2) else 2 if j in (3, 4) else 1
            n_ = noise2(sheet_i, (y - y0) // 30, seed)
            rp = sib('slate', n_, 0.34)                                   # sheets painted harbour grey-blue,
            if smooth_noise(x, y, 3, seed + 9) > 0.7 and j in (1, 2):    # the paint off the crests in patches
                rp = 'iron'
            if (y - y0) % 30 == 29:
                k = 1                                  # the lap where one sheet overlaps the next
            cv.set(x, y, T(rp, k))
        for sx in range(x0, x0 + w, 24):               # fixings along each rib at the laps
            for y in range(y0 + 2, y0 + h, 15):
                for xx in range(sx + 1, min(sx + 24, x0 + w), 6):
                    cv.set(xx, y, T('iron', 5))
        for i in range(w // 9):                        # rust runs down from the fixings, in clusters
            rx = x0 + 2 + int(noise2(i, 0, seed + 3) * (w - 4))
            ry = y0 + 2 + int(noise2(i, 1, seed + 3) * (h - 12))
            for yy in range(ry + 1, ry + 4 + int(noise2(i, 2, seed) * 6)):
                for xx in (rx, rx + 1):
                    if (xx, yy) in pts:
                        cv.set(xx, yy, T('clay_cool', 2 if yy < ry + 3 else 1))
    elif kind in ('hull', 'panel', 'hull_ext'):
        fam = 'hull' if kind == 'hull_ext' else kind
        plates(cv, x0, y0, w, h, fam, seed, pw=22, ph=12, other='panel' if fam == 'hull' else 'iron')
        for y in range(y0 + 3, y0 + h, 12):
            rivets(cv, x0 + 3, x0 + w - 2, y, every=4)
        for y in range(y0 + 6, y0 + h - 2, 12):   # a ribbed band at mid plate
            for x in range(x0 + 1, x0 + w - 1):
                if (x - x0) % 22 not in (0, 1):
                    step(cv, x, y, -1)
        if kind == 'hull_ext' and seed % 2:   # gold foil blankets quilted over part of the shell
            fx = x0 + 4 + int(noise2(seed, 0, 3) * (w - 24))
            for (x, y) in rect(fx, y0 + 2, 18, min(14, h - 4)):
                q = ((x - fx) // 4 + (y - y0) // 4) % 2
                cv.set(x, y, T(sib('brass', noise2((x - fx) // 4, (y - y0) // 4, seed), 0.35), 4 if q else 3))
            frame(cv, fx - 1, y0 + 1, 20, min(14, h - 4) + 2, 'brass', 2, t=1)
    elif kind == 'bulkhead':   # a station wall inside: plates above, equipment bays, a kick plate
        plates(cv, x0, y0, w, h, 'panel', seed, pw=12, ph=8, other='hull')
        for y in range(y0 + 2, y0 + h - 6, 8):
            rivets(cv, x0 + 2, x0 + w - 2, y, every=6, ramp='panel')
        for ri in range((h - 5) // 8):   # each plate is for something: a vent, a label, an access panel, a socket
            for ci in range(-1, w // 12 + 1):
                px0 = x0 + ci * 12 - (6 if ri % 2 else 0) + 3
                py0 = y0 + ri * 8 + 3
                if px0 < x0 + 3 or px0 + 7 > x0 + w - 3:
                    continue
                f = noise2(ri, ci, seed + 21)
                if f < 0.18:      # vent slots
                    for vy in (py0, py0 + 2):
                        cv.hline(px0 + 1, vy, 5, T('panel', 1)); cv.hline(px0 + 1, vy + 1, 5, T('panel', 4))
                elif f < 0.32:    # a label
                    part(cv, px0, py0, 6, 3, 'plaster', 4, glint=False)
                    cv.hline(px0 + 1, py0 + 1, 3, T(('berry', 'sky', 'brass', 'lagoon')[int(f * 40) % 4], 2))
                elif f < 0.44:    # an access panel with its latch
                    for (qx, qy) in rect(px0, py0, 7, 4):
                        e = qx in (px0, px0 + 6) or qy in (py0, py0 + 3)
                        cv.set(qx, qy, T('panel', (4 if qx == px0 or qy == py0 else 1) if e else 3))
                    cv.hline(px0 + 4, py0 + 2, 2, T('brass', 4))
                elif f < 0.52:    # a power socket
                    part(cv, px0 + 1, py0, 4, 4, 'hull', 4, glint=False)
                    cv.set(px0 + 2, py0 + 2, T('iron', 1)); cv.set(px0 + 3, py0 + 2, T('iron', 1))
        bay_y = y0 + max(4, h // 3)
        bx, i = x0 + 3, 0
        while bx < x0 + w - 11:
            if any(bx < a[2] + 1 and a[0] - 1 < bx + 10 and bay_y < a[3] and a[1] < bay_y + 12 for a in avoid):
                bx += 2
                continue   # never a bay half hidden behind a door or a window: slide along to the next gap
            kind_ = ('grille', 'locker', 'screen', 'label', 'valves')[int(noise2(i, seed, 5) * 5)]
            i += 1
            bx_, bx = bx, bx + 12
            bx = bx_
            part(cv, bx, bay_y, 10, 12, 'panel', 2)   # the bay, set back
            for yy in range(bay_y, bay_y + 12):
                step(cv, bx, yy, -1)
            if kind_ == 'grille':
                for yy in range(bay_y + 2, bay_y + 10, 2):
                    cv.hline(bx + 2, yy, 6, T('panel', 1))
            elif kind_ == 'locker':
                part(cv, bx + 1, bay_y + 1, 8, 10, sib('hull', noise2(i, 1, seed), 0.3), 3)
                cv.hline(bx + 6, bay_y + 6, 2, T('brass', 4))
            elif kind_ == 'screen':
                part(cv, bx + 1, bay_y + 2, 8, 6, 'void', 2, glint=False)
                for yy in (bay_y + 3, bay_y + 5):
                    cv.hline(bx + 2, yy, 3 + (yy % 3), T('neon_cyan', 4))
            elif kind_ == 'label':
                part(cv, bx + 1, bay_y + 2, 8, 4, 'plaster', 4, glint=False)
                cv.hline(bx + 2, bay_y + 3, 5, T('iron', 2))
                cv.hline(bx + 2, bay_y + 8, 6, T('berry', 3))
            else:
                for gx in (bx + 3, bx + 7):
                    for (px, py) in disc(gx, bay_y + 6, 1.8):
                        cv.set(px, py, T('berry' if gx < bx + 5 else 'brass', 4 if px + py < gx + bay_y + 6 else 2))
            part(cv, bx + 2, bay_y - 4, 6, 3, 'plaster', 4, glint=False)   # its label plate above it
            cv.hline(bx + 3, bay_y - 3, 3, T(('berry', 'sky', 'brass', 'lagoon')[i % 4], 2))
            bx += 12
        for (x, y) in rect(x0, y0 + h - 5, w, 5):   # the kick plate, scuffed, a hazard band at its top
            cv.set(x, y, T('iron', 3 if y == y0 + h - 5 else 2))
            if y == y0 + h - 4:
                cv.set(x, y, T('brass', 4) if ((x + y) // 3) % 2 else T('iron', 1))
        grain(cv, rect(x0, y0 + h - 4, w, 4), 0.1, seed + 2, shapes=H_GRAIN[:2], swap=0.3, up=0.1, down=0.5)
    elif kind == 'berm':     # moon soil heaped over a habitat shell: no stone, no bricks
        for (x, y) in pts:   # a smooth heap: lit to the west, broad soft drifts, grit as clusters
            u = (x - x0) / max(1, w)
            k = 4 if u < 0.22 else 3 if u < 0.72 else 2
            n = smooth_noise(x, y, 7, seed)
            if n > 0.68 and k < 4:
                k += 1
            elif n < 0.22 and k > 2:
                k -= 1
            cv.set(x, y, T(sib('regolith', smooth_noise(x, y, 5, seed + 3), 0.3), k))
        grain(cv, pts, 0.10, seed + 1, swap=0.95, up=0.05, down=0.05)
        for i in range(w * h // 160):   # stones half buried in the heap, each with its hard shadow
            px, py = x0 + int(noise2(i, 1, seed) * (w - 4)), y0 + int(noise2(i, 2, seed) * (h - 3))
            pebble(cv, px, py, 'regolith', 3, big=noise2(i, 3, seed) < 0.3)
    else:
        raise ValueError(kind)
    return pts


def plinth(cv, x0, y0, w, h, kind='stone', seed=0):
    fams = {'stone': ('stone', 'ashlar'), 'slate': ('slate', 'stone'), 'adobe': ('adobe',), 'regolith': ('regolith',)}[kind]
    courses(cv, x0, y0, w, h, stone_pick(fams, seed), course=max(3, h // 2), lengths=(5, 9),
            seam=T(fams[0] + '_cool', 1), seed=seed)


HATCH_PICTO = ('bed', 'leaf', 'bolt', 'cup')   # quarters, hydroponics, power, galley
ROOM = ['bar']   # what a lit doorway shows: set per door (a noodle bar's curtain, a station's corridor)


def interior(cv, x, y, w, h, seed=0, kind='shop'):
    """A lit room seen through glass at night: the back wall warm under a hanging lamp, a
    floor, and what the room holds (a counter and stools in a bar, a curtain over a kitchen
    door, a dresser in a house). Light, not a lamp-coloured slab (art-style.md)."""
    for (px, py) in rect(x, y, w, h):
        fy = (py - y) / max(1, h - 1)
        cv.set(px, py, T('lamp', 2 if fy < 0.25 else 3 if fy < 0.6 else 4))
    lx = x + w // 2
    cv.vline(lx, y, 2, T('iron', 1))
    for (px, py) in disc(lx + 0.5, y + 3, 1.8):   # the hanging lamp, its bright core
        if x <= px < x + w and y <= py < y + h:
            cv.set(px, py, T('lamp', 5))
    floor = y + h - max(3, h // 6)
    for (px, py) in rect(x, floor, w, y + h - floor):
        cv.set(px, py, T('timber', 3 if (px + py) % 4 else 2))
    if kind == 'bar':   # a counter across the room, a stool before it
        cy = floor - 6
        for (px, py) in rect(x, cy, w, 6):
            cv.set(px, py, T('timber', 4 if py == cy else 2 if py > cy + 1 else 3))
        sx = x + w // 3
        cv.hline(sx, floor - 2, 3, T('iron', 3)); cv.vline(sx + 1, floor - 1, 1, T('iron', 1))
    elif kind == 'lab':   # a station lab behind the glass: a console under its screens, a grow-lit plant
        cy = floor - 7
        for (px, py) in rect(x, cy, w, 7):
            cv.set(px, py, T('panel', 4 if py == cy else 2 if py > cy + 4 else 3))
        for i, sx in enumerate(range(x + 1, x + w - 4, 6)):
            part(cv, sx, cy - 7, 5, 6, 'void', 2, glint=False)
            cv.hline(sx + 1, cy - 5, 3, T('neon_cyan', 4)); cv.hline(sx + 1, cy - 3, 2, T('glowflora' if i % 2 else 'neon_cyan', 3))
        px0 = x + w - 4
        part(cv, px0, cy - 3, 3, 3, 'hull', 3, glint=False)
        for (qx, qy) in disc(px0 + 1.5, cy - 6, 2.4):
            if x <= qx < x + w:
                cv.set(qx, qy, T('glowflora' if (qx + qy) % 3 == 0 else 'leaf', 4 if qy < cy - 6 else 3))
        for (px, py) in rect(x, y + 1, w, 2):   # the grow light's band across the ceiling
            cv.set(px, py, T('dusk', 4 if py == y + 1 else 3))
    elif kind == 'noren':   # a split curtain over the kitchen door at the back
        cloth = paint('cloth', 'berry')
        for (px, py) in rect(x + 1, y + 1, w - 2, h // 3):
            if (px - x) % (w // 3 + 1) == 0:
                continue
            cv.set(px, py, T(cloth, 4 if py == y + 1 else 3))


# --- doors ---------------------------------------------------------------------------------
def leaf(cv, x, y, w, h, fam, kind, seed=0, lit=False):
    """A door leaf. kinds: plank, ledged, panel, stable, glazed, studded, batwing, roller,
    slide, hatch, iris."""
    if kind in ('plank', 'ledged', 'studded'):   # boards 4 wide: a dark joint, a lit edge, the body, a shaded edge
        for (px, py) in rect(x, y, w, h):
            bw_ = 5 if w >= 20 else 4   # a big door's boards are wider
            bi, j = divmod(px - x, bw_)
            rp = sib(fam, noise2(bi, 0, seed), 0.34)
            k = 0 if j == 0 and px > x else 4 if j == 1 else 2 if j == bw_ - 1 else 3
            cv.set(px, py, T(rp, k))
        if hp.family(fam) in ('timber', 'bleached'):   # grain shows on natural wood; paint covers it
            grain(cv, rect(x, y, w, h), 0.025, seed + 1, shapes=V_GRAIN)
        if kind == 'ledged':
            for ly in (y + 3, y + h - 6):
                part(cv, x, ly, w, 3, fam, 3, glint=False)
            for i in range(h - 12):   # the brace, rising to the hinge side
                bx = x + w - 2 - int(i * (w - 3) / (h - 12))
                cv.set(bx, y + 6 + i, T(fam, 4)); cv.set(bx + 1, y + 6 + i, T(fam, 2))
        if kind == 'studded':
            for sy in (y + 4, y + h // 2, y + h - 5):
                for px in range(x, x + w):
                    cv.set(px, sy, T('iron', 3)); cv.set(px, sy + 1, T('iron', 1))
                    if (px - x) % 4 == 2:
                        cv.set(px, sy - 1, T('iron', 4))
        else:   # strap hinges from the hinge side, nailed through, and a ring latch on the other
            for sy in (y + 6, y + h - 8):
                for px in range(x, x + int(w * 0.6)):
                    cv.set(px, sy, T('iron', 3 if px < x + 2 else 2)); cv.set(px, sy + 1, T('iron', 1))
                cv.set(x + int(w * 0.6) - 1, sy - 1, T('iron', 2))   # the strap's turned-up end
            rx, ry = x + w - 4, y + h // 2
            for (px, py) in ((rx, ry), (rx + 1, ry), (rx - 1, ry + 1), (rx + 2, ry + 1), (rx, ry + 2), (rx + 1, ry + 2)):
                cv.set(px, py, T('iron', 4 if py == ry else 2))
        for (px, py) in rect(x, y + h - 2, w, 2):   # the foot of the door, darkened by splashes
            step(cv, px, py, -1)
    elif kind == 'panel' and w >= 20:   # a pair of doors: each leaf glazed above, a raised panel below,
        for (px, py) in rect(x, y, w, h):  # pull handles at the meeting stiles, a kick plate across both
            cv.set(px, py, T(fam, 3))
        half = w // 2
        for lx in (x, x + half):
            gx0, gx1 = lx + 2, lx + half - 2
            if lit:
                interior(cv, gx0, y + 3, gx1 - gx0, h // 2 - 4, seed, 'shop')
            else:
                glass(cv, gx0, y + 3, gx1 - gx0, h // 2 - 4, False)
            for (px, py) in rect(gx0, y + h // 2 + 1, gx1 - gx0, h // 2 - 6):
                a, b = y + h // 2 + 1, y + h - 5
                cv.set(px, py, T(fam, 4 if (py == a or px == gx0) else 2 if (py == b - 1 or px == gx1 - 1) else 3))
            cv.set(gx0, y + h // 2 + 1, T(fam, 5))
        cv.vline(x + half - 1, y, h, T(fam, 1)); cv.vline(x + half, y, h, T(fam, 4))
        for hx in (x + half - 3, x + half + 2):
            cv.vline(hx, y + h // 2 - 3, 5, T('brass', 4)); cv.set(hx, y + h // 2 + 2, T('brass', 2))
        for (px, py) in rect(x + 1, y + h - 3, w - 2, 2):
            cv.set(px, py, T('brass', 4 if py == y + h - 3 else 2))
    elif kind in ('panel', 'stable', 'glazed'):
        for (px, py) in rect(x, y, w, h):
            cv.set(px, py, T(fam, 3))
        rows = [(y + 2, y + h // 2 - 2), (y + h // 2 + 1, y + h - 3)]
        for ri, (a, b) in enumerate(rows):
            if kind == 'glazed' and ri == 0:   # the glass: the lit room behind it at night, the sky by day
                if lit:
                    interior(cv, x + 2, a, w - 4, b - a, seed, 'bar')
                else:
                    glass(cv, x + 2, a, w - 4, b - a, lit)
                cv.vline(x + w // 2, a, b - a, T(fam, 2))
                continue
            for cx0, cx1 in ((x + 2, x + w // 2 - 1), (x + w // 2 + 1, x + w - 2)):
                for (px, py) in rect(cx0, a, cx1 - cx0, b - a):   # a raised panel: lit top and left, dark bottom and right
                    k = 4 if (py == a or px == cx0) else 2 if (py == b - 1 or px == cx1 - 1) else 3
                    cv.set(px, py, T(fam, k))
        for (cx0, a) in ((x + 2, y + 2), (x + w // 2 + 1, y + 2), (x + 2, y + h // 2 + 1), (x + w // 2 + 1, y + h // 2 + 1)):
            if kind == 'glazed' and a == y + 2:
                continue
            cv.set(cx0, a, T(fam, 5))   # each panel's moulding catches the light at its corner
        if kind == 'stable':   # the top half stands open by day: the room inside, its lamp, the ledge
            for (px, py) in rect(x, y, w, h // 2 - 1):
                fy = (py - y) / max(1, h // 2 - 2)
                cv.set(px, py, T('timber_cool', 1 if fy < 0.5 else 2))
            for (px, py) in disc(x + w * 0.65, y + h * 0.18, 2.4):
                if y <= py < y + h // 2 - 1:
                    cv.set(px, py, T('lamp', 4 if py < y + h * 0.18 else 3))
            for py in range(y + h // 2 - 7, y + h // 2 - 1):   # a dresser's shelf of plates inside
                cv.set(x + 2, py, T('plaster', 4 if py % 2 else 3)); cv.set(x + 3, py, T('sky', 3 if py % 2 else 2))
            part(cv, x - 1, y + h // 2 - 1, w + 2, 2, fam, 4, glint=False)
        elif w >= 12:          # a brass letter plate on the middle rail, a kick plate at the foot
            cv.hline(x + w // 2 - 2, y + h // 2, 4, T('brass', 4)); cv.hline(x + w // 2 - 2, y + h // 2 + 1, 4, T('brass', 1))
            for (px, py) in rect(x + 1, y + h - 3, w - 2, 2):
                cv.set(px, py, T('brass', 4 if py == y + h - 3 else 2))
    elif kind == 'steel':     # a steel door: flat leaf on a frame, a wired vision panel lit from inside,
        for (px, py) in rect(x, y, w, h):   # a lever, a kick plate, a fire-exit sticker
            lv = (px - x) / w + (py - y) / h
            cv.set(px, py, T(fam, 4 if px == x or py == y else 2 if px == x + w - 1 else 3 if lv < 1.1 else 2))
        vx, vy = x + 3, y + 5
        interior(cv, vx, vy, w - 6, 9, seed, 'shop') if lit else glass(cv, vx, vy, w - 6, 9, False)
        for (px, py) in rect(vx, vy, w - 6, 9):
            if (px - vx) % 3 == 2 and (py - vy) % 3 == 2:
                cv.set(px, py, T('iron', 2))   # the wire mesh in the glass
        frame(cv, vx - 1, vy - 1, w - 4, 11, fam, 2, t=1)
        cv.hline(x + w - 5, y + h // 2, 4, T('hull', 5)); cv.set(x + w - 5, y + h // 2 + 1, T('hull', 2))
        for (px, py) in rect(x + 1, y + h - 4, w - 2, 3):
            cv.set(px, py, T('hull', 4 if py == y + h - 4 else 3))
        part(cv, x + 3, y + h // 2 + 4, 5, 4, 'glowflora', 3, glint=False)   # the exit sticker
        cv.set(x + 4, y + h // 2 + 5, T('plaster', 5))
    elif kind == 'batwing':   # a saloon's doorway: the lamplit room behind, two short leaves at chest height
        for (px, py) in rect(x, y, w, h):   # the room: dark back wall, a lamp's pool, floorboards
            fy = (py - y) / max(1, h - 1)
            k = 1 if fy < 0.55 else 2
            if abs(px + 0.5 - (x + w * 0.62)) < 3 and 0.15 < fy < 0.55:
                k = 2
            cv.set(px, py, T('timber_cool', k))
        for (px, py) in disc(x + w * 0.62, y + h * 0.28, 2.2):   # a hanging lamp lit inside
            if x <= px < x + w and y <= py < y + h:
                cv.set(px, py, T('lamp', 4 if py < y + h * 0.28 else 3))
        cv.vline(int(x + w * 0.62), y, int(h * 0.2), T('iron', 1))
        for py in range(y + h - 7, y + h):   # floorboards running in, lit near the door
            for px in range(x, x + w):
                cv.set(px, py, T('timber', 3 if (py - (y + h)) % 2 else 2) if (px - x) % 7 else T('timber', 1))
        lh = 18                              # the leaves: chest to knee, hung 9 above the floor
        ly = y + h - 9 - lh
        for (lx, lw, hinge_left) in ((x, w // 2 - 1, True), (x + w // 2 + 1, w // 2 - 1, False)):
            for (px, py) in rect(lx, ly, lw, lh):
                top = ly + (2 if (px - lx) % 3 == 1 else 0)   # a shaped top rail
                if py < top:
                    continue
                j = (px - lx) % 3
                k = 4 if j == 0 else 3 if j == 1 else 2
                if py in (ly + 3, ly + lh - 4) or py == ly + lh - 1:
                    k = 4 if py != ly + lh - 1 else 1   # rails across the louvres
                cv.set(px, py, T(fam, k))
            hx = lx if hinge_left else lx + lw - 1
            for hy in (ly + 3, ly + lh - 4):
                cv.set(hx, hy, T('iron', 4)); cv.set(hx, hy + 1, T('iron', 1))
    elif kind == 'roller':   # a roller shutter half up: coil box, guide rails, slats, bottom bar, the lit shop below
        box_h = 4
        for (px, py) in rect(x, y, w, box_h):   # the coil box
            cv.set(px, py, T('iron', 4 if py == y else 3 if py < y + box_h - 1 else 1))
        open_y = y + box_h + int((h - box_h) * 0.55)
        for (px, py) in rect(x, y + box_h, w, open_y - y - box_h):
            r = (py - y - box_h) % 2
            cv.set(px, py, T(sib(fam, noise2(0, (py - y) // 2, seed), 0.3), 4 if r == 0 else 2))
        for px in range(x, x + w):               # the bottom bar and its handle
            cv.set(px, open_y, T('iron', 4)); cv.set(px, open_y + 1, T('iron', 1))
        part(cv, x + w // 2 - 3, open_y + 2, 6, 2, 'iron', 3, glint=False)
        glass(cv, x + 1, open_y + 2, w - 2, y + h - open_y - 2, True)   # the shop lit inside
        for (px, py) in rect(x + 2, y + h - 6, w - 4, 3):   # a counter seen under the shutter
            cv.set(px, py, T('timber', 3 if py == y + h - 6 else 2))
        for py in range(y + box_h, y + h):       # the guide rails either side
            cv.set(x, py, T('iron', 2)); cv.set(x + w - 1, py, T('iron', 1))
        grain(cv, rect(x + 1, y + box_h, w - 2, open_y - y - box_h), 0.06, seed + 2, shapes=H_GRAIN[:2], swap=0.3, up=0.0, down=0.6)
    elif kind == 'slide':
        for (px, py) in rect(x, y, w, h):
            cv.set(px, py, T('iron', 2))
        half = w // 2
        if lit:   # the room behind the glass, one pane slid half open
            interior(cv, x + 1, y + 1, w - 2, h - 2, seed, ROOM[0])
            for py in range(y + 1, y + h - 1):
                cv.set(x + half, py, T('iron', 3)); cv.set(x + half - 1, py, T('iron', 1))
        else:
            glass(cv, x + 1, y + 1, half - 2, h - 2, lit); glass(cv, x + half + 1, y + 1, half - 2, h - 2, lit)
        cv.hline(x + 2, y + h // 2, w - 4, T('iron', 3))
        for px in (x + half - 2, x + half + 1):   # the pull handles
            cv.vline(px, y + h // 2 - 3, 6, T(fam if fam != 'panel' else 'iron', 4))
    elif kind in ('hatch', 'pod'):   # a pressure hatch: rounded corners (a pod is rounded top and foot),
        r = 3 if kind == 'hatch' else w / 2   # panels, a porthole, a handwheel, hinges
        cx = x + w / 2

        def inside(px, py):
            if kind == 'pod':
                for cy_ in (y + r, y + h - r):
                    if (py < y + r and cy_ == y + r) or (py >= y + h - r and cy_ == y + h - r):
                        return (px + 0.5 - cx) ** 2 + (py + 0.5 - cy_) ** 2 <= r * r
                return True
            dx, dy = min(px - x, x + w - 1 - px), min(py - y, y + h - 1 - py)
            return not (dx + dy < r)
        body = {(px, py) for (px, py) in rect(x, y, w, h) if inside(px, py)}
        for (px, py) in body:
            edge = any((px + dx, py + dy) not in body for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            lv = (px - x) / w + (py - y) / h
            k = 4 if lv < 0.35 else 3 if lv < 1.25 else 2
            if edge:
                k = 4 if (px < cx and py < y + h / 2) else 1
            cv.set(px, py, T(fam, k))
        for py in (y + h // 3, y + 2 * h // 3):   # panel seams
            for px in range(x + 2, x + w - 2):
                if (px, py) in body:
                    cv.set(px, py, T(fam, 2)); cv.set(px, py + 1, T(fam, 4))
        porthole(cv, cx - 0.5, y + h * 0.2 + (2 if kind == 'pod' else 0), min(4.2, w / 4), 'hull', lit)
        picto(cv, int(cx) - 3, y + int(h * 0.7), HATCH_PICTO[seed % len(HATCH_PICTO)], 'plaster', 5)   # what is behind it, stencilled
        for (px, py) in body:   # a bare-metal wear plate where boots and trolleys strike it
            if py >= y + h - 5 and py < y + h - 1:
                cv.set(px, py, T('hull', 4 if py == y + h - 5 else 3 if (px - x) % 5 else 2))
        wy = y + int(h * 0.56)
        for (px, py) in disc(cx - 0.5, wy, 4.6):   # the boss plate the handwheel turns on
            if (px, py) in body:
                cv.set(px, py, T('hull', 4 if px + py < cx + wy - 2 else 2))
        for (px, py) in disc(cx - 0.5, wy, 3.4):
            cv.set(px, py, T('iron', 4 if px + py < cx + wy - 1 else 2))
        for (px, py) in disc(cx - 0.5, wy, 1.9):
            cv.set(px, py, T(fam, 2))
        cv.set(int(cx), wy, T('iron', 1))
        for hy in (y + 5, y + h - 7):            # hinges on the west side
            part(cv, x - 1, hy, 3, 3, 'iron', 3, glint=False)
    else:
        raise ValueError(kind)


def doorway(cv, x, yb, w, h, fam, kind, frame_fam, seed=0, arch=False, fan=False, step_fam='stone',
            knob='brass', lit=False, frame_t=2, coaming=False, collar=None, lintel=None):
    """A door in its surround: a frame (or arch) round it, the leaf set back in a recess
    (its top row and hinge-side column in shade), a knob or latch, and what it stands on: a
    step (one riser, a lit tread), a raised coaming under a pressure hatch, or a collar of
    hull round an airlock in a heap of moon soil. `lintel` lays a stone or timber head over
    a square door in a masonry or adobe wall. Returns its box (x0, y0, x1, y1)."""
    y = yb - h
    top = y - frame_t
    if collar:   # an airlock's collar: a thick ring of hull standing proud of the heap, its foot on a pad
        ct = 4
        for (px, py) in rect(x - ct, y - ct, w + 2 * ct, h + ct):
            lv = (px - (x - ct)) / (w + 2 * ct) + (py - (y - ct)) / (h + ct)
            k = 4 if lv < 0.45 else 3 if lv < 1.2 else 2
            if px in (x - ct, x + w + ct - 1) or py == y - ct:
                k = 5 if (px == x - ct or py == y - ct) and lv < 1.0 else 1
            cv.set(px, py, T(collar, k))
        for px in range(x - ct + 2, x + w + ct - 2, 5):   # bolts round the collar
            cv.set(px, y - ct + 1, T('iron', 1))
        for py in range(y + 2, yb, 6):
            cv.set(x - ct + 1, py, T('iron', 1)); cv.set(x + w + ct - 2, py, T('iron', 1))
        overhang(cv, x - ct, x + w + ct, yb, 0)
    if lintel and not arch:
        part(cv, x - frame_t - 2, y - frame_t - 4, w + 2 * frame_t + 4, 4, lintel, 4)
    opening = rect(x, y, w, h)
    if arch:
        r = w / 2
        opening = {(px, py) for (px, py) in opening if py >= y + r or (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= r * r}
        ring = {(px, py) for px in range(x - frame_t, x + w + frame_t) for py in range(y - frame_t, yb)
                if (py >= y + r or (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= (r + frame_t) ** 2)} - opening
        for (px, py) in ring:
            a = math.atan2(-(py + 0.5 - (y + r)), px + 0.5 - (x + w / 2))
            lit_side = px < x + w / 2
            k = 4 if (py < y + r and a > 1.0) or (lit_side and py >= y + r) else 2 if not lit_side else 3
            if py < y + r and int(a / (math.pi / 7)) % 2 == 0 and abs(math.hypot(px + 0.5 - (x + w / 2), py + 0.5 - (y + r)) - r - frame_t / 2) < 0.6:
                k -= 1
            cv.set(px, py, T(frame_fam, k))
    elif kind in ('hatch', 'pod'):   # a pressure frame: thick, its own bolts, hazard chevrons up its jambs
        frame(cv, x - frame_t, y - frame_t, w + 2 * frame_t, h + frame_t, frame_fam, 3, t=frame_t)
        for py in range(y + 2, yb - 4):
            for jx in (x - frame_t + 1, x + w + 1):
                if ((py + (jx - x)) // 3) % 2 == 0:
                    cv.set(jx, py, T('brass', 4 if jx < x else 3))
                else:
                    cv.set(jx, py, T('iron', 1))
        for py in range(y + 1, yb - 1, 5):
            cv.set(x - frame_t, py, T(frame_fam, 5)); cv.set(x + w + frame_t - 1, py, T('iron', 1))
        for px in range(x + 2, x + w - 2):   # the lintel's pressure seal, a dark line with a lit lip
            cv.set(px, y - 1, T('iron', 1))
    else:
        frame(cv, x - frame_t, y - frame_t, w + 2 * frame_t, h + frame_t, frame_fam, 3, t=frame_t)
    if fan and not arch:
        glass(cv, x, y, w, 4, lit)
        cv.hline(x, y + 4, w, T(frame_fam, 3))
        y, h = y + 5, h - 5
    if coaming:    # the raised sill a hatch closes onto: you step over it
        h -= 3
    sub = Canvas(cv.w, cv.h)
    if kind in ('hatch', 'pod'):
        for (px, py) in opening:   # the frame's inner shadow behind the hatch's rounded corners
            sub.set(px, py, T('iron', 1))
    leaf(sub, x, y, w, h, fam, kind, seed, lit)
    for (px, py) in opening:
        if py >= y:
            c = sub.get(px, py)
            if c[3]:
                cv.set(px, py, c)
    for (px, py) in opening:   # the recess: shade under the head and on the hinge side
        if (px, py - 1) not in opening or (px - 1, py) not in opening:
            step(cv, px, py, -1)
    if knob and kind not in ('batwing', 'roller', 'slide', 'hatch', 'pod', 'steel') and not (kind == 'panel' and w >= 20):
        kx = x + w - 4
        cv.set(kx, y + h // 2, T(knob, 5)); cv.set(kx, y + h // 2 + 1, T(knob, 2))
    if coaming:
        for px in range(x - frame_t, x + w + frame_t):
            for i in range(3):
                cv.set(px, yb - 3 + i, T('brass', 4) if i == 0 else (T('brass', 3) if ((px + i) // 2) % 2 else T('iron', 1)))
    elif step_fam:   # one riser and its tread, wider than the door
        part(cv, x - frame_t - 1, yb, w + 2 * frame_t + 2, 3, step_fam, 4)
    x0 = x - frame_t - (4 if collar else 1) - (2 if lintel and not arch else 0)
    x1 = x + w + frame_t + (4 if collar else 1) + (2 if lintel and not arch else 0)
    y0 = top - (4 if collar else 0) - (4 if lintel and not arch else 0)
    return (x0, y0, x1, yb + 3)


# --- windows -------------------------------------------------------------------------------
def soldier_arch(cv, x0, y, w, seed=0):
    """A gauged brick head over an opening: rubbed bricks stood on end (2 wide, 4 tall) in
    fine lime joints, a warmer red than the wall, lit at the top and the west, rising a
    pixel at the middle like a flat segmental arch. It carries the wall over the window."""
    mid = x0 + w / 2
    for px in range(x0, x0 + w):
        lift = 1 if abs(px + 0.5 - mid) < w * 0.32 else 0
        j = (px - x0) % 3
        rp = 'clay_warm'
        for i in range(4 + lift):
            py = y - lift + i
            if j == 2:
                cv.set(px, py, T('stone', 3 if i < 3 + lift else 2))     # a fine lime joint
            else:
                k = 4 if i == 0 else 3 if j == 0 else 2
                if i == 3 + lift:
                    k = 2
                cv.set(px, py, T(rp, k))
    for px in range(x0, x0 + w):   # the arch's soffit line on the window head
        step(cv, px, y + 4, -1)


def casement(cv, x, y, w, h, frame_fam='timber', cols=2, rows=2, lit=False, shutters=None, sill='stone',
             box=False, arch=False, lintel=None, bars=False, curtain=True, blind=False, leaded=False, t=2,
             paint_frame=False, seed=0, space=False):
    """A window in its wall: frame, panes (lit from inside or the sky in them), glazing
    bars, optional shutters on their hinges, a head (stone or timber lintel, a brick soldier
    arch, or an arch of its own), a sill that throws a band, and a flower box on two
    brackets. Painted frames, shutters, curtains and flowers take the colourway. Returns the
    box it fills (x0, y0, x1, y1)."""
    if paint_frame:
        frame_fam = paint('trim', frame_fam)
    x0b, y0b, x1b, y1b = x, y, x + w, y + h
    if lintel == 'brick':
        soldier_arch(cv, x - 2, y - 4, w + 4, seed)
        x0b, y0b, x1b = x - 2, y - 6, x + w + 2
    elif lintel:
        part(cv, x - 2, y - 3, w + 4, 3, lintel, 4)
        x0b, y0b, x1b = x - 2, y - 3, x + w + 2
    if shutters:
        sh = paint('shutter', shutters)
        for sx in (x - 5, x + w):
            boards(cv, sx, y, 5, h, lambda b, s_: (sh, 3), board=4, seed=sx, nails=False, grain=0, joints=(40, 41))
            for yy in range(y, y + h):
                cv.set(sx, yy, T(sh, 4)); cv.set(sx + 4, yy, T(sh, 1))
            for hy in (y + 2, y + h - 3):   # the hinge straps, on the side against the frame
                hx = sx + 3 if sx < x else sx
                cv.hline(hx, hy, 2, T('iron', 2))
        x0b, x1b = min(x0b, x - 5), max(x1b, x + w + 5)
    hole = rect(x, y, w, h)
    if arch:
        r = w / 2
        hole = {(px, py) for (px, py) in hole if py >= y + r or (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= r * r}
        for (px, py) in rect(x - 1, y - 1, w + 2, int(r) + 1):
            if (px, py) not in hole and (px + 0.5 - (x + w / 2)) ** 2 + (py + 0.5 - (y + r)) ** 2 <= (r + 1.5) ** 2:
                cv.set(px, py, T(frame_fam, 4 if px < x + w / 2 else 2))
        x0b, y0b, x1b = min(x0b, x - 1), min(y0b, y - 1), max(x1b, x + w + 1)
    for (px, py) in hole:
        cv.set(px, py, T(frame_fam, 3))
    inner = {(px, py) for (px, py) in hole if x + t <= px < x + w - t and y + t <= py < y + h - t and
             all((px + dx, py + dy) in hole for dx in (-t, t) for dy in (-t, t))}
    if not inner:
        return (x0b, y0b, x1b, y1b)
    ix0, iy0 = min(p[0] for p in inner), min(p[1] for p in inner)
    ix1, iy1 = max(p[0] for p in inner) + 1, max(p[1] for p in inner) + 1
    sub = Canvas(cv.w, cv.h)
    if space and not lit:   # a station's window looks out on space: near-black, a planet's limb, stars
        for (px, py) in rect(ix0, iy0, ix1 - ix0, iy1 - iy0):
            sub.set(px, py, T('void', 0))
        pcx, pcy, pr = ix1 - 2, iy1 + 3, (iy1 - iy0) * 0.9
        for (px, py) in disc(pcx, pcy, pr):
            lv = -(px + 0.5 - pcx) - (py + 0.5 - pcy)
            sub.set(px, py, T('sky' if lv > 0 else 'sky_cool', 4 if lv > pr * 0.8 else 3 if lv > pr * 0.2 else 1))
        for (sx, sy) in ((ix0 + 2, iy0 + 2), (ix0 + (ix1 - ix0) // 2, iy0 + 4)):
            sub.set(sx, sy, T('hull', 5)); sub.set(sx + 1, sy, T('hull', 3))
    else:
        glass(sub, ix0, iy0, ix1 - ix0, iy1 - iy0, lit)
    for p in inner:
        cv.set(p[0], p[1], sub.get(*p))
    for (px, py) in hole - inner:   # the frame: lit top and left, dark bottom and right
        k = 4 if (py < iy0 or px < ix0) and not (py >= iy1 or px >= ix1) else 2 if (py >= iy1 or px >= ix1) else 3
        cv.set(px, py, T(frame_fam, k))
    for c in range(1, cols):
        bx = ix0 + c * (ix1 - ix0) // cols
        for py in range(iy0, iy1):
            if (bx, py) in inner:
                cv.set(bx, py, T(frame_fam, 2))
    for r in range(1, rows):
        by = iy0 + r * (iy1 - iy0) // rows
        for px in range(ix0, ix1):
            if (px, by) in inner:
                cv.set(px, by, T(frame_fam, 4))
    if leaded:
        for (px, py) in inner:
            if (px - ix0 + py - iy0) % 3 == 0 and (px - ix0 - (py - iy0)) % 3 == 0:
                cv.set(px, py, T('iron', 1))
    cloth = paint('cloth', 'berry')
    if curtain and lit:   # a curtain drawn back to one side, lit through
        for py in range(iy0, iy1):
            if (ix0, py) in inner:
                cv.set(ix0, py, T(cloth, 3)); cv.set(ix0 + 1, py, T(cloth, 2))
    elif curtain:         # a net curtain half down by day
        for py in range(iy0, iy0 + (iy1 - iy0) // 2):
            cv.set(ix0, py, T('plaster', 5)); cv.set(ix0 + 1, py, T('plaster', 4))
    if blind:
        for py in range(iy0, iy0 + (iy1 - iy0) // 2):
            for px in range(ix0, ix1):
                if (px, py) in inner:
                    cv.set(px, py, T('plaster', 4 if (py - iy0) % 2 == 0 else 3))
    if bars:
        for px in range(ix0 + 1, ix1, 3):
            for py in range(iy0, iy1):
                if (px, py) in inner:
                    cv.set(px, py, T('iron', 2 if py > iy0 else 3))
    if sill:
        part(cv, x - 2, y + h, w + 4, 2, sill, 4, glint=False)
        overhang(cv, x - 1, x + w + 2, y + h + 2, 2)
        x0b, x1b, y1b = min(x0b, x - 2), max(x1b, x + w + 2), y + h + 2
    if space:   # a station window's inside ledge: the crew's plant from hydroponics, a mug
        part(cv, x - 1, y + h - 3, w + 2, 3, 'hull', 4, glint=False)
        part(cv, x + 2, y + h - 7, 4, 4, paint('pot', 'hull'), 3, glint=False)
        leafy(cv, x + 4, y + h - 9, 3.2, 2.6, seed=seed + 7, ramp='leaf')
        cv.set(x + 3, y + h - 11, T(paint('flower', 'glowflora'), 5))
        part(cv, x + w - 5, y + h - 6, 3, 3, paint('cloth', 'berry'), 4, glint=False)
        cv.set(x + w - 2, y + h - 5, T(paint('cloth', 'berry'), 2))
    if box:   # a flower box on two iron brackets under the sill
        bx0, by0 = x - 1, y + h + 2
        part(cv, bx0, by0, w + 2, 4, 'timber', 2)
        flowers = (paint('flower', 'berry'), 'brass', paint('flower', 'berry'), 'plaster')
        for i, fx in enumerate(range(x, x + w, 3)):
            cv.hline(fx, by0 - 1, 3, T('leaf', 3)); cv.set(fx + 1, by0 - 2, T('leaf', 4))
            col = flowers[(i + x) % 4]
            cv.hline(fx, by0 - 3 + (i % 2), 2, T(col, 4)); cv.set(fx, by0 - 3 + (i % 2), T(col, 5))
        for bx in (bx0 + 1, bx0 + w - 1):
            cv.set(bx, by0 + 4, T('iron', 3)); cv.set(bx + 1, by0 + 4, T('iron', 2)); cv.set(bx, by0 + 5, T('iron', 2))
        overhang(cv, x - 1, x + w + 2, by0 + 6, 2)
        y1b = by0 + 6
    return (x0b, y0b, x1b, y1b)


def porthole(cv, cx, cy, r, ring='brass', lit=True, space=False):
    """A round window in a thick bolted ring: lit from inside, the sky in its glass, or (from
    inside the station) space beyond it: near-black, a planet's lit limb, two stars."""
    for (px, py) in disc(cx, cy, r):
        lv = -(px + 0.5 - cx) - (py + 0.5 - cy)
        cv.set(px, py, T(ring, 4 if lv > r * 0.4 else 3 if lv > -r * 0.4 else 2))
    sub = Canvas(cv.w, cv.h)
    if space:
        for (px, py) in rect(int(cx - r), int(cy - r), int(2 * r) + 1, int(2 * r) + 1):
            sub.set(px, py, T('void', 0))
        pcx, pcy, pr = cx + r * 0.9, cy + r * 1.1, r * 1.2   # the planet low in the window
        for (px, py) in disc(pcx, pcy, pr):
            d = math.hypot(px + 0.5 - pcx, py + 0.5 - pcy)
            lv = -(px + 0.5 - pcx) - (py + 0.5 - pcy)
            sub.set(px, py, T('sky' if lv > 0 else 'sky_cool', 4 if d > pr - 1.2 and lv > 0 else 3 if lv > pr * 0.3 else 2 if lv > -pr * 0.3 else 1))
        for (px, py) in disc(pcx - pr * 0.3, pcy - pr * 0.4, pr * 0.35):
            sub.set(px, py, T('leaf', 3))
        for (px, py) in disc(pcx - pr * 0.55, pcy - pr * 0.1, pr * 0.3):   # a weather system over the sea
            if (px, py) in disc(pcx, pcy, pr - 0.5):
                sub.set(px, py, T('snow', 4))
        for (sx, sy) in ((cx - r * 0.45, cy - r * 0.4), (cx + r * 0.1, cy - r * 0.6)):
            sub.set(int(sx), int(sy), T('hull', 5)); sub.set(int(sx) + 1, int(sy), T('hull', 3))
    else:
        glass(sub, int(cx - r), int(cy - r), int(2 * r) + 1, int(2 * r) + 1, lit)
    for (px, py) in disc(cx, cy, r - 1.6):
        cv.set(px, py, sub.get(px, py))
    for k in range(4):   # bolts round the ring
        a = k * math.pi / 2 + math.pi / 4
        cv.set(int(cx + (r - 0.8) * math.cos(a)), int(cy + (r - 0.8) * math.sin(a)), T(ring, 1))


# --- roofs and tops ------------------------------------------------------------------------
def roof_edge(cv, x0, y0, w, h, kind, seed=0):
    """The roof or top as it meets the wall below, h px tall, with the band it throws on the
    wall under it. kinds: tiles, slate, thatch, palm, shingle, copper, glass, corrugated,
    parapet, falsefront, vigas, crenel, cone, flat, radiator, berm, dome."""
    yb = y0 + h
    if kind in ('tiles', 'slate', 'shingle'):
        fam, row, tile = {'tiles': ('clay', 5, (6, 8)), 'slate': ('slate', 4, (5, 7)), 'shingle': ('timber', 5, (6, 9))}[kind]
        roof_rows(cv, x0, y0, w, h - 3, fam, 3, row=row, tile=tile, seed=seed, moss=kind != 'shingle')
        for x in range(x0, x0 + w):
            cv.set(x, yb - 3, T('timber', 4)); cv.set(x, yb - 2, T('timber', 2)); cv.set(x, yb - 1, T('timber', 1))
    elif kind in ('thatch', 'palm'):
        fam = 'sand' if kind == 'thatch' else 'bleached'
        for (x, y) in rect(x0, y0, w, h):
            ci = (y - y0) // 4
            sx = (x + (2 if ci % 2 else 0)) // 2
            n = noise2(sx, ci, seed)
            k = 3 + (1 if n > 0.7 else -1 if n < 0.25 else 0)
            if (y - y0) % 4 == 0:
                k -= 1
            if kind == 'palm' and (y - y0) % 6 == 4 and (x // 2) % 3:
                cv.set(x, y, T('bleached', 1))   # the binding of each bundle
                continue
            cv.set(x, y, T(sib(fam, noise2(sx, ci, seed + 1), 0.3), k))
        for x in range(x0, x0 + w):   # the thick rounded eave: lit lip, shade under
            d = 1 + (1 if (x // 3) % 2 else 0)
            for i in range(d):
                cv.set(x, yb - 3 + i, T(fam, 4))
            cv.set(x, yb - 1, T(fam, 1))
    elif kind == 'copper':
        for (x, y) in rect(x0, y0, w, h - 2):
            j = (x - x0) % 6
            k = 4 if j == 0 else 3 if j < 3 else 2 if j < 5 else 1
            cv.set(x, y, T(sib('copper', smooth_noise(x, y, 5, seed)), k + (1 if y < y0 + 2 else 0)))
        for x in range(x0, x0 + w):
            cv.set(x, yb - 2, T('copper', 1)); cv.set(x, yb - 1, T('iron', 2))
    elif kind == 'glass':   # a glazed roof on iron bars
        for (x, y) in rect(x0, y0, w, h - 2):
            j = (x - x0) % 7
            if j == 0:
                cv.set(x, y, T('iron', 3 if y > y0 else 4))
            else:
                k = 4 if (j == 1 and (y - y0) < 4) else 2 if (y - y0) > h // 2 else 3
                cv.set(x, y, T('sky_cool', k))
        for x in range(x0, x0 + w):
            cv.set(x, yb - 2, T('iron', 4)); cv.set(x, yb - 1, T('iron', 1))
    elif kind == 'corrugated':
        wall(cv, x0, y0, w, h - 1, 'corrugated', seed)
        for x in range(x0, x0 + w):
            cv.set(x, y0, T('iron', 5) if (x - x0) % 4 == 0 else T('iron', 4))
            cv.set(x, yb - 1, T('iron', 1))
    elif kind in ('parapet', 'falsefront', 'flat'):
        fam = {'parapet': 'ashlar', 'falsefront': 'bleached', 'flat': 'concrete'}[kind]
        part(cv, x0, yb - 4, w, 4, fam, 4)
        if kind == 'falsefront':   # the stepped top of a false front
            part(cv, x0 + w // 5, y0 + 2, w - 2 * (w // 5), yb - 4 - y0 - 2, fam, 3)
            part(cv, x0 + w // 3, y0, w - 2 * (w // 3), 3, fam, 4)
        if kind == 'flat':
            for x in range(x0 + 4, x0 + w - 4, 9):   # a rooftop rail
                cv.vline(x, y0 + 2, yb - 4 - y0 - 2, T('iron', 3))
            cv.hline(x0 + 3, y0 + 2, w - 6, T('iron', 4))
    elif kind == 'vigas':   # an adobe parapet with round roof beams poking through
        part(cv, x0, y0 + 2, w, h - 2, 'adobe', 4)
        for x in range(x0 + 4, x0 + w - 4, 10):
            for (px, py) in disc(x, yb - 3, 2.2):
                cv.set(px, py, T('timber', 4 if px + py < x + yb - 3 else 2))
            cv.set(x, yb - 3, T('timber', 1))
            step(cv, x + 1, yb, -2); step(cv, x + 2, yb, -1)
    elif kind == 'crenel':
        for x in range(x0, x0 + w):
            merlon = ((x - x0) // 6) % 2 == 0
            top = y0 if merlon else y0 + 5
            if not merlon:   # the wall walk seen through the gap, in the merlon's shadow
                for y in range(y0, top):
                    step(cv, x, y, -2 if (x - x0) % 6 < 2 else -1)
            for y in range(top, yb):
                k = 4 if y == top else 3
                if (x - x0) % 6 == 5 and merlon:
                    k = 2
                cv.set(x, y, T(sib('ashlar', noise2((x - x0) // 6, 0, seed), 0.3), k))
        for x in range(x0, x0 + w):
            cv.set(x, yb - 1, T('ashlar', 2))
    elif kind == 'cone':   # the foot of a slate cone roof, curving round a tower
        for (x, y) in rect(x0, y0, w, h - 2):
            u = (x - x0) / w
            roof_rows(cv, x, y, 1, 1, 'slate', 3 if 0.2 < u < 0.6 else 2 if u >= 0.6 else 4, row=4, tile=(5, 6), seed=seed)
        for x in range(x0, x0 + w):
            cv.set(x, yb - 2, T('slate', 1)); cv.set(x, yb - 1, T('timber', 1))
    elif kind == 'radiator':
        for x in range(x0, x0 + w):
            f = (x - x0) % 3
            for y in range(y0, yb):
                cv.set(x, y, T('panel', 4 if f == 0 else 3 if f == 1 else 1))
        cv.hline(x0, y0, w, T('panel', 5)); cv.hline(x0, yb - 1, w, T('panel', 1))
    elif kind == 'berm':
        wall(cv, x0, y0, w, h, 'berm', seed)
        for x in range(x0, x0 + w):
            cv.set(x, y0, T('regolith', 4))
    elif kind == 'dome':
        cx = x0 + w / 2
        for (x, y) in rect(x0, y0, w, h):
            u = (x + 0.5 - cx) / (w / 2)
            top = yb - h * math.sqrt(max(0, 1 - u * u))
            if y >= top:
                j = (x - x0) % 8
                k = 4 if u < -0.3 else 3 if u < 0.4 else 2
                cv.set(x, y, T('panel', 3) if j == 0 else T('sky_cool', k))
    else:
        raise ValueError(kind)
    overhang(cv, x0, x0 + w, yb, 2)


def chimney(cv, x, y, h=14, fam='brick'):
    """A chimney stack, 9 wide: lit west face, dark east face, an oversailing cap course and
    two clay pots on it (pots at y - 3). It stands over a hearth at a gable end or on the ridge
    and is drawn behind the roof, so the roof hides its foot (size-guide 3: 8 to 12 wide, 8 to
    16 above the roof it leaves; only where a hearth is inside)."""
    if fam == 'brick':
        bricks(cv, x, y + 3, 9, h - 3, x + y, soot_rows=2)
    else:
        courses(cv, x, y + 3, 9, h - 3, stone_pick((fam,), x), course=4, lengths=(4, 6), seam=T(fam + '_cool', 1), seed=x)
    for yy in range(y + 3, y + h):
        step(cv, x, yy, 1); step(cv, x + 7, yy, -1); step(cv, x + 8, yy, -2)
    part(cv, x - 1, y, 11, 3, 'stone', 4)
    for px in (x + 1, x + 5):   # pots
        for py in range(y - 3, y):
            cv.set(px, py, T('clay', 4)); cv.set(px + 1, py, T('clay', 3)); cv.set(px + 2, py, T('clay', 1))
        cv.hline(px, y - 3, 3, T('clay', 5))
    return (x - 1, y - 3, x + 10, y + h)


def roof_mass(cv, x0, y0, w, h, kind, shape, seed=0, gable_wall='plaster'):
    """The roof seen from the south and above, h px tall, standing on a wall that starts at
    y0 + h. Shapes: 'ridge' (the ridge runs across: the front plane narrows to a ridge cap,
    the gable ends cut its corners), 'gable' (the gable faces us: a lit west plane, a shaded
    east plane, barge boards, the gable wall between), 'hip' (a short ridge, hips lit west
    and shaded east), 'flat' (a flat roof seen from above with its parapet and rooftop
    things), 'falsefront' (a tall front with a stepped top and the tin roof behind it),
    'crenel' (battlements with the wall walk behind), 'dome', 'berm', 'radiator'."""
    fam = {'tiles': 'clay', 'slate': 'slate', 'shingle': 'timber', 'copper': 'copper', 'thatch': 'sand',
           'palm': 'bleached', 'glass': 'sky_cool', 'corrugated': 'iron'}.get(kind, 'slate')
    yb = y0 + h
    if shape in ('ridge', 'hip', 'gable'):
        if shape == 'gable':
            cx = x0 + w / 2
            plane = {(x, y) for x in range(x0, x0 + w) for y in range(y0, yb)
                     if abs(x + 0.5 - cx) < w / 2 * (0.42 + 0.58 * (y - y0) / h)}
            gab = {(x, y) for (x, y) in plane if abs(x + 0.5 - cx) < (y - y0) * (w * 0.32) / h}
            sub = Canvas(cv.w, cv.h)
            _roof_fill(sub, x0, y0, w, h, kind, fam, seed)
            for (x, y) in plane - gab:
                c = sub.get(x, y)
                if c[3]:
                    cv.set(x, y, c)
                    if x > cx:
                        step(cv, x, y, -1)
                    elif x < cx - w * 0.3:
                        step(cv, x, y, 1)
            wall(sub, x0, y0, w, h, gable_wall, seed + 3)
            for p in gab:
                cv.set(p[0], p[1], sub.get(*p))
            for (x, y) in gab:   # barge boards along the gable's two edges
                if (x - 1, y) not in gab and x < cx:
                    cv.set(x, y, T('timber', 4)); cv.set(x - 1, y, T('timber', 2))
                if (x + 1, y) not in gab and x >= cx:
                    cv.set(x, y, T('timber', 2)); cv.set(x + 1, y, T('timber', 1))
            for (x, y) in gab:   # the gable wall is in the roof's shadow at its top
                if y < y0 + 4:
                    step(cv, x, y, -1)
            vx = int(cx) - 2   # a vent in the gable
            if (vx, y0 + h // 2) in gab:
                part(cv, vx - 1, y0 + h // 2 - 2, 6, 5, 'timber', 2, glint=False)
        else:
            inset = 0.22 if shape == 'ridge' else 0.42
            sub = Canvas(cv.w, cv.h)
            _roof_fill(sub, x0, y0, w, h, kind, fam, seed)
            for (x, y) in rect(x0, y0, w, h):
                d = (yb - y) * inset * (w / max(1, h)) * 0.5
                if x0 + d - 1 <= x < x0 + w - d + 1:
                    c = sub.get(x, y)
                    if c[3]:
                        cv.set(x, y, c)
                        if shape == 'hip' and x < x0 + d + 6:
                            step(cv, x, y, 1)
                        elif x > x0 + w - d - 7:
                            step(cv, x, y, -1)
            top_d = int(h * inset * (w / max(1, h)) * 0.5)
            part(cv, x0 + top_d, y0, w - 2 * top_d, 3, fam if kind not in ('thatch', 'palm') else fam, 4)
        if kind not in ('thatch', 'palm', 'glass', 'corrugated'):
            for x in range(x0, x0 + w):   # fascia under the eave
                if cv.get(x, yb - 1)[3]:
                    cv.set(x, yb, T('timber', 4)); cv.set(x, yb + 1, T('timber', 2))
            overhang(cv, x0, x0 + w, yb + 2, 3)
        else:
            overhang(cv, x0, x0 + w, yb, 3)
    elif shape == 'flat':
        top = {'flat': 'ash', 'parapet': 'ashlar'}.get(kind, 'ash')
        ground(cv, x0 + 1, y0, w - 2, h - 4, top, 2, seed=seed, scale=4, density=0.12)
        part(cv, x0, yb - 4, w, 4, 'concrete' if top == 'ash' else 'ashlar', 4)
        part(cv, x0, y0 - 2, w, 3, 'concrete' if top == 'ash' else 'ashlar', 4, glint=False)
        for yy in range(y0, yb - 4):
            cv.set(x0, yy, T('concrete', 4)); cv.set(x0 + w - 1, yy, T('concrete', 2))
        # rooftop things, a different set on each roof, each with its shadow
        things = ['ac', 'tank', 'vent', 'dish', 'skylight', 'pots']
        order = sorted(things, key=lambda t: noise2(seed, things.index(t), 9))[:3]
        for i, t in enumerate(order):
            ax = x0 + 4 + i * (w - 8) // 3 + int(noise2(seed, i, 4) * 4)
            if t == 'ac':
                part(cv, ax, y0 + 2, 12, 7, 'panel', 3)
                for xx in range(ax + 2, ax + 10, 2):
                    cv.vline(xx, y0 + 4, 3, T('panel', 1))
                cast(cv, rect(ax + 12, y0 + 3, 2, 7))
            elif t == 'tank':
                cylinder(cv, ax, y0 + 1, 8, 9, 'timber', 3)
                cv.hline(ax, y0, 8, T('iron', 4))
                cast(cv, rect(ax + 8, y0 + 2, 2, 9))
            elif t == 'vent':
                cylinder(cv, ax + 2, y0 + 3, 3, 6, 'iron', 3)
                part(cv, ax, y0 + 1, 7, 3, 'iron', 4, glint=False)
                cast(cv, rect(ax + 5, y0 + 4, 2, 5))
            elif t == 'dish':
                for (px, py) in disc(ax + 5, y0 + 5, 4):
                    cv.set(px, py, T('hull', 4 if px + py < ax + y0 + 10 else 2))
                cast(cv, rect(ax + 9, y0 + 4, 2, 5))
            elif t == 'skylight':
                glass(cv, ax, y0 + 2, 10, 7, True)
                frame(cv, ax - 1, y0 + 1, 12, 9, 'iron', 3, t=1)
            else:
                for j in range(2):
                    part(cv, ax + j * 6, y0 + 5, 5, 4, 'clay', 3)
                    leafy(cv, ax + j * 6 + 2.5, y0 + 3, 3, 2.5, seed=seed + j)
        overhang(cv, x0, x0 + w, yb, 2)
    elif shape == 'falsefront':
        roof_mass(cv, x0 + 8, y0 + 4, w - 16, 10, 'corrugated', 'ridge', seed)
        wall(cv, x0, y0 + 10, w, h - 10, 'bleached', seed + 5)
        for (x, y) in rect(x0, y0 + 10, w, 4):   # the stepped top
            if x < x0 + 6 or x >= x0 + w - 6:
                cv.set(x, y, (0, 0, 0, 0))
        part(cv, x0 + 5, y0 + 9, w - 10, 2, 'bleached', 5, glint=False)
        part(cv, x0, y0 + 13, 6, 2, 'bleached', 5, glint=False); part(cv, x0 + w - 6, y0 + 13, 6, 2, 'bleached', 5, glint=False)
    elif shape == 'vigas':
        ground(cv, x0 + 2, y0 + 2, w - 4, h - 6, 'adobe', 3, seed=seed, scale=4, density=0.08)
        roof_edge(cv, x0, yb - 8, w, 8, 'vigas', seed)
        part(cv, x0, y0, w, 3, 'adobe', 4, glint=False)
        for yy in range(y0, yb - 8):
            cv.set(x0, yy, T('adobe', 4)); cv.set(x0 + w - 1, yy, T('adobe', 2))
    elif shape == 'crenel':
        courses(cv, x0, y0, w, h - 9, stone_pick(('stone',), seed), course=5, lengths=(8, 12), seam=T('stone_cool', 1), seed=seed)
        roof_edge(cv, x0, yb - 11, w, 11, 'crenel', seed)
    elif shape == 'conduit':   # the thick top of a bulkhead inside the station, services along it
        for (x, y) in rect(x0, y0, w, h):
            cv.set(x, y, T(sib('panel', noise2((x - x0) // 16, 0, seed), 0.3), 2 if (y - y0) % 6 else 1))
        part(cv, x0, y0, w, 2, 'panel', 4, glint=False)
        runs = [('pipe', y0 + 3), ('tray', y0 + 9), ('duct', y0 + 3), ('light', y0 + 14)]
        pick = [runs[int(noise2(seed, i, 7) * 4)] for i in range(2)] + [('light', yb - 4)]
        for kind_, y in pick:
            if kind_ == 'pipe':
                for x in range(x0, x0 + w):
                    for i, k in enumerate((4, 3, 2)):
                        cv.set(x, y + i, T('copper', k))
                    if (x - x0) % 14 in (0, 1):
                        cv.vline(x, y - 1, 5, T('brass', 4 if (x - x0) % 14 == 0 else 2))
            elif kind_ == 'tray':
                for x in range(x0, x0 + w):
                    cv.set(x, y, T('iron', 3)); cv.set(x, y + 4, T('iron', 1))
                    for i, c in enumerate(('berry', 'sky', 'brass')):
                        cv.set(x, y + 1 + i, T(c, 3 if (x + i) % 9 else 4))
            elif kind_ == 'duct':
                part(cv, x0, y, w, 5, 'hull', 3)
                for x in range(x0 + 6, x0 + w, 16):
                    cv.vline(x, y, 5, T('hull', 1))
            else:
                for x in range(x0 + 2, x0 + w - 2):
                    cv.set(x, y, T('lamp', 5 if (x - x0) % 12 < 9 else 2)); cv.set(x, y + 1, T('lamp', 3 if (x - x0) % 12 < 9 else 1))
        overhang(cv, x0, x0 + w, yb, 2)
    elif shape in ('dome', 'berm', 'radiator'):
        cx = x0 + w / 2
        for (x, y) in rect(x0, y0, w, h):
            u = (x + 0.5 - cx) / (w / 2)
            top = yb - h * math.sqrt(max(0, 1 - u * u)) * (0.95 if shape != 'radiator' else 0.5)
            if y < top:
                continue
            if shape == 'berm':
                continue
            else:
                pi_ = int((u + 1) * 4)
                k = 4 if u < -0.3 else 3 if u < 0.35 else 2
                if (y - y0) % 8 == 0 or int((u + 1) * 4 * 2) % 2 == 0 and (x + 0.5 - cx) % 8 < 1:
                    k -= 1
                cv.set(x, y, T(sib('hull', noise2(pi_, (y - y0) // 8, seed), 0.3), k))
        if shape == 'berm':   # the heap of moon soil over the shell, lit at the upper left
            sub = Canvas(cv.w, cv.h)
            wall(sub, x0, y0, w, h, 'berm', seed)
            for (x, y) in rect(x0, y0, w, h):
                u = (x + 0.5 - cx) / (w / 2)
                if y >= yb - h * math.sqrt(max(0, 1 - u * u)) * 0.95:
                    cv.set(x, y, sub.get(x, y))
                    if u < -0.35 and y < yb - h * 0.4:
                        step(cv, x, y, 1)
                    elif u > 0.45:
                        step(cv, x, y, -1)
        if shape == 'radiator':   # a radiator panel stood on two struts from the shell, its coolant lines down to it
            px0, px1, ptop, pbot = x0 + w // 4, x0 + 3 * w // 4, y0, y0 + h // 3
            for sx in (px0 + 4, px1 - 6):
                u = (sx + 1 - cx) / (w / 2)
                foot = int(yb - h * math.sqrt(max(0, 1 - u * u)) * 0.5) + 1
                cylinder(cv, sx, pbot, 2, max(1, foot - pbot), 'iron', 3)
                part(cv, sx - 1, foot - 1, 4, 2, 'iron', 2, glint=False)   # the strut's foot plate
            for lx in (int(cx) - 2, int(cx) + 1):   # coolant lines, copper
                foot = int(yb - h * 0.5) + 1
                cv.vline(lx, pbot, max(1, foot - pbot), T('copper', 4 if lx < cx else 2))
            for x in range(px0, px1):
                f = (x - x0) % 3
                for y in range(ptop, pbot):
                    cv.set(x, y, T('panel', 4 if f == 0 else 3 if f == 1 else 1))
            cv.hline(px0, ptop, px1 - px0, T('panel', 5)); cv.hline(px0, pbot - 1, px1 - px0, T('iron', 1))
        if shape != 'berm':   # the heap runs on down the wall: no eave
            overhang(cv, x0, x0 + w, yb, 2)
    else:
        raise ValueError(shape)


def _roof_fill(cv, x0, y0, w, h, kind, fam, seed):
    if kind in ('tiles', 'slate', 'shingle'):
        row, tile = {'tiles': (5, (6, 8)), 'slate': (4, (5, 7)), 'shingle': (5, (6, 9))}[kind]
        roof_rows(cv, x0, y0, w, h, fam, 3, row=row, tile=tile, seed=seed, moss=kind != 'shingle')
    elif kind == 'copper':
        for (x, y) in rect(x0, y0, w, h):
            j = (x - x0) % 6
            cv.set(x, y, T(sib('copper', smooth_noise(x, y, 5, seed)), 4 if j == 0 else 3 if j < 3 else 2 if j < 5 else 1))
    elif kind in ('thatch', 'palm'):
        for (x, y) in rect(x0, y0, w, h):
            ci = (y - y0) // 3
            sx = (x + (1 if ci % 2 else 0)) // 2
            n = noise2(sx, ci, seed)
            k = 3 + (1 if n > 0.72 else -1 if n < 0.22 else 0) - (1 if (y - y0) % 3 == 0 else 0)
            cv.set(x, y, T(sib(fam, noise2(sx, ci, seed + 1), 0.3), k))
        for x in range(x0, x0 + w):   # the thick rounded eave
            cv.set(x, y0 + h - 3, T(fam, 4)); cv.set(x, y0 + h - 2, T(fam, 3)); cv.set(x, y0 + h - 1, T(fam, 1))
        if kind == 'palm':   # tied bundles: a darker binding line every few rows
            for y in range(y0 + 4, y0 + h - 3, 6):
                for x in range(x0, x0 + w):
                    if (x // 2) % 3:
                        cv.set(x, y, T('bleached', 1))
    elif kind == 'glass':
        for (x, y) in rect(x0, y0, w, h):
            j = (x - x0) % 7
            cv.set(x, y, T('iron', 3) if j == 0 else T('sky_cool', 4 if (j == 1 and (y - y0) % 10 < 3) else 3 if (y - y0) < h // 2 else 2))
        for y in range(y0, y0 + h, 9):
            cv.hline(x0, y, w, T('iron', 4))
    elif kind == 'corrugated':
        wall(cv, x0, y0, w, h, 'corrugated', seed)
    else:
        roof_rows(cv, x0, y0, w, h, 'slate', 3, seed=seed)


# --- signs and wall fixtures -------------------------------------------------------------
# Each returns its box (x0, y0, x1, y1). Everything on a wall is fixed to it by something you
# can see: a plate and a bracket, a pole on two hooks, clips, a rail.
def hanging_sign(cv, x, y, pic, board='timber', ink='brass'):
    """A sign on a wall bracket: a plate fixed to the wall at x, an arm with a brace under
    it, two short chains and a board with a pictogram. The arm is at y (36 to 44 above the
    ground, size-guide 3: above a head, below the eaves)."""
    part(cv, x, y - 2, 2, 8, 'iron', 3, glint=False)                     # the wall plate
    cv.hline(x + 2, y, 14, T('iron', 4)); cv.hline(x + 2, y + 1, 14, T('iron', 1))   # the arm
    cv.set(x + 2, y + 4, T('iron', 2)); cv.set(x + 3, y + 3, T('iron', 2)); cv.set(x + 4, y + 2, T('iron', 2))   # the brace
    cv.set(x + 15, y - 1, T('iron', 3))                                    # a scroll at its tip
    for rx in (x + 7, x + 13):                                             # chains
        cv.set(rx, y + 2, T('iron', 3)); cv.set(rx, y + 3, T('iron', 1))
    part(cv, x + 5, y + 4, 11, 10, board, 3)
    picto(cv, x + 7, y + 5, pic, ink)
    return (x, y - 2, x + 16, y + 14)


def wall_lantern(cv, x, y, metal='iron'):
    """A lantern hung from a short arm on a wall plate: cap, lit glass, base, a hook."""
    part(cv, x, y, 2, 7, metal, 3, glint=False)
    cv.hline(x + 2, y + 1, 4, T(metal, 4)); cv.hline(x + 2, y + 2, 4, T(metal, 1))
    cv.set(x + 2, y + 3, T(metal, 2))
    cv.set(x + 5, y + 3, T(metal, 2))                                     # the hook
    part(cv, x + 3, y + 4, 6, 2, metal, 4, glint=False)                   # cap
    glass(cv, x + 4, y + 6, 4, 5, True)
    cv.vline(x + 3, y + 6, 5, T(metal, 4)); cv.vline(x + 8, y + 6, 5, T(metal, 1))
    part(cv, x + 3, y + 11, 6, 2, metal, 3, glint=False)                  # base
    return (x, y, x + 9, y + 13)


def fascia(cv, x, y, w, pic, board='berry', ink='brass', h=8):
    """A fascia board over a shop: lit top moulding, painted board, a pictogram with dots
    either side, a shadow under it."""
    part(cv, x, y, w, 2, board, 4, glint=False)
    for (px, py) in rect(x, y + 2, w, h - 3):
        cv.set(px, py, T(sib(board, noise2(px // 9, 0, 3), 0.3), 2 if py == y + h - 2 else 3))
    picto(cv, x + w // 2 - 3, y + 1, pic, ink)
    for dx in (-10, 10):
        cv.hline(x + w // 2 + dx - 1, y + 4, 2, T(ink, 4))
    cv.hline(x, y + h - 1, w, T(board, 1))
    for bx in (x + 1, x + w - 3):   # the console brackets that carry it at each end
        part(cv, bx, y + h - 1, 2, 3, board, 2, glint=False)
    overhang(cv, x, x + w, y + h, 2)
    return (x, y, x + w, y + h + 2)


def awning(cv, x, y, w, a='berry', b='plaster', drop=8):
    """A canvas awning on its roller box: stripes, folds lit and shaded, a scalloped valance,
    an iron arm at each end, its shade below."""
    for px in range(x, x + w):   # the roller box fixed to the wall
        cv.set(px, y - 2, T('iron', 4)); cv.set(px, y - 1, T('iron', 2))
    for (px, py) in rect(x, y, w, drop):
        stripe = a if ((px - x) // 5) % 2 == 0 else b
        f = (px - x) % 5
        k = 4 if f == 0 else 3 if f < 3 else 2
        if py < y + 2:
            k += 1
        cv.set(px, py, T(stripe, k))
    for px in range(x, x + w):
        d = 2 if (px - x) % 5 in (1, 2, 3) else 1
        stripe = a if ((px - x) // 5) % 2 == 0 else b
        for i in range(d):
            cv.set(px, y + drop + i, T(stripe, 2 if i < d - 1 else 1))
    for ax in (x, x + w - 1):   # the arms
        cv.vline(ax, y - 1, drop + 1, T('iron', 1))
    overhang(cv, x, x + w, y + drop + 2, 3)
    return (x, y - 2, x + w, y + drop + 2)


def lightbox(cv, x, y, w, pic, glow='neon_cyan'):
    """A sign box over a shop: a dark case on the wall, an iron edge, a neon pictogram in it."""
    for (px, py) in rect(x, y, w, 10):
        edge = py in (y, y + 9) or px in (x, x + w - 1)
        cv.set(px, py, T('iron', 3 if py == y else 1) if edge else T('asphalt', 2 if y < py < y + 9 else 1))
    neon_tube(cv, x + w // 2 - 3, y + 1, pic, glow, wall_fams=('asphalt',))
    for dx in (-10, 10):
        cv.hline(x + w // 2 + dx - 1, y + 5, 3, T(glow, 4))
    overhang(cv, x, x + w, y + 10, 1)
    return (x, y, x + w, y + 11)


def neon_tube(cv, x, y, pic, glow='neon_pink', wall_fams=('asphalt', 'concrete')):
    """A neon pictogram: the tube in the glow ramp, its halo in two bands on the wall."""
    tube = {(x + c, y + r) for r, row in enumerate(PICTO[pic]) for c, ch in enumerate(row) if ch in '#+'}
    for (px, py) in tube:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                p = (px + dx, py + dy)
                if p in tube:
                    continue
                hit = tone_at(cv, *p)
                if hit and hp.family(hit[0]) in wall_fams:
                    cv.set(p[0], p[1], T(glow, 0 if abs(dx) + abs(dy) > 2 else 1))
    for (px, py) in tube:
        cv.set(px, py, T(glow, 4))
    for (px, py) in sorted(tube)[::4]:
        cv.set(px, py, T(glow, 5))


def blade(cv, x, y, h, glow='neon_cyan', pics=('moon', 'cup')):
    """A vertical lightbox sign: a dark box, lit panels with pictograms, an iron bracket at
    its top and foot fixing it to the wall on its west side."""
    for (px, py) in rect(x, y, 9, h):
        edge = px in (x, x + 8) or py in (y, y + h - 1)
        cv.set(px, py, T('iron', 2 if edge else 1))
    for i, pic in enumerate(pics):
        picto(cv, x + 1, y + 2 + i * 9, pic, glow)
    for by in (y + 2, y + h - 4):
        part(cv, x - 3, by, 3, 2, 'iron', 3, glint=False)
        cv.set(x - 3, by + 2, T('iron', 1))
    return (x - 3, y, x + 9, y + h)


def stencil(cv, x, y, w, fam='berry', pic='bolt'):
    """A painted band on a hull with a pictogram, worn at its edges."""
    for (px, py) in rect(x, y, w, 7):
        cv.set(px, py, T(fam, 4 if py == y else 2 if py == y + 6 else 3))
    picto(cv, x + w // 2 - 3, y, pic, 'plaster', 5)
    grain(cv, rect(x, y, w, 7), 0.1, 7, shapes=H_GRAIN[:2], swap=0.2, up=0.0, down=0.6)
    return (x, y, x + w, y + 7)


def status_light(cv, x, y, glow='glowflora'):
    part(cv, x - 1, y - 1, 5, 4, 'panel', 2, glint=False)
    cv.hline(x, y, 3, T(glow, 4)); cv.set(x, y, T(glow, 5))
    return (x - 1, y - 1, x + 4, y + 3)


def gutter(cv, x0, x1, y):
    """A half-round iron gutter hung on the fascia: lit lip, dark belly, a bracket every 12."""
    for x in range(x0, x1):
        cv.set(x, y, T('iron', 4)); cv.set(x, y + 1, T('iron', 2)); cv.set(x, y + 2, T('iron', 1))
    for x in range(x0 + 4, x1 - 2, 12):
        cv.set(x, y + 1, T('iron', 5))


def downpipe(cv, x, y_top, ground):
    """A rainwater pipe from a hopper under the gutter (or a parapet's outlet) to a shoe
    that turns out over the ground; clipped to the wall every ten pixels."""
    part(cv, x - 1, y_top, 5, 3, 'iron', 3, glint=False)
    cylinder(cv, x, y_top + 3, 3, ground - 4 - (y_top + 3), 'iron', 3)
    for by in range(y_top + 9, ground - 6, 10):
        part(cv, x - 1, by, 5, 2, 'iron', 2, glint=False)
    for (px, py) in rect(x, ground - 4, 4, 3):   # the shoe
        cv.set(px, py, T('iron', 4 if py == ground - 4 else 3 if py == ground - 3 else 1))
    for yy in range(y_top + 3, ground - 4):
        step(cv, x + 3, yy, -1)
    return (x - 1, y_top, x + 4, ground)


def service_pipe(cv, x, y_top, yb, fam='copper'):
    """A station coolant line: out of the conduit by an elbow, down the wall on clips, a valve
    with its handwheel, and back into the wall at a flange."""
    part(cv, x - 1, y_top, 5, 3, fam, 4, glint=False)             # the elbow out of the conduit
    cylinder(cv, x, y_top + 3, 3, yb - 8 - (y_top + 3), fam, 3)
    for by in range(y_top + 8, yb - 10, 9):
        part(cv, x - 1, by, 5, 2, 'iron', 3, glint=False)
    vy = (y_top + yb) // 2
    part(cv, x - 1, vy - 2, 5, 4, 'brass', 3, glint=False)         # the valve body
    for (px, py) in disc(x + 1.5, vy - 4, 2.2):                     # its handwheel
        cv.set(px, py, T('berry', 4 if px + py < x + vy - 3 else 2))
    part(cv, x - 2, yb - 8, 7, 3, fam, 2, glint=False)              # the flange into the wall
    for yy in range(y_top + 3, yb - 8):
        step(cv, x + 3, yy, -1)
    return (x - 2, y_top, x + 5, yb - 5)


def ac_unit(cv, x, y):
    """A wall air conditioner on two angle brackets, its drip stain below."""
    part(cv, x, y, 12, 8, 'panel', 3)
    for xx in range(x + 2, x + 10, 2):
        cv.vline(xx, y + 2, 4, T('panel', 1))
    for bx in (x + 1, x + 9):
        cv.hline(bx, y + 8, 3, T('iron', 3)); cv.set(bx, y + 9, T('iron', 2)); cv.set(bx, y + 10, T('iron', 1))
    for yy in range(y + 11, y + 18):
        step(cv, x + 6, yy, -1)
    return (x, y, x + 12, y + 11)


def service_panel(cv, x, y):
    part(cv, x, y, 14, 12, 'panel', 3)
    for xx in range(x + 2, x + 12, 2):
        cv.vline(xx, y + 2, 4, T('panel', 1))
    part(cv, x + 2, y + 7, 6, 3, 'plaster', 4, glint=False)
    for gx in (x + 10, x + 12):
        cv.set(gx, y + 8, T('brass', 4)); cv.set(gx, y + 9, T('brass', 2))
    cv.hline(x, y + 12, 14, T('iron', 1))
    return (x, y, x + 14, y + 13)


def posters(cv, x, y):
    """Bills pasted on a blank wall, overlapping, the newest on top."""
    for j, (pw, ph, c) in enumerate(((7, 9, 'plaster'), (6, 8, 'sky'), (6, 6, 'berry'))):
        px, py = x + j * 5, y + (j % 2) * 3
        part(cv, px, py, pw, ph, c, 3, glint=False)
        cv.hline(px + 1, py + 2, pw - 2, T(c, 1)); cv.hline(px + 1, py + 4, pw - 3, T(c, 2))
    return (x, y, x + 16, y + 12)


def tie_plate(cv, x, y):
    """A pattress plate: the cast-iron end of a tie rod that holds the front to the floor
    joists, on the line of the upper floor (a Victorian brick terrace's own detail)."""
    for (px, py) in disc(x + 2.5, y + 2.5, 2.6):
        cv.set(px, py, T('iron', 4 if px + py < x + y + 4 else 2))
    cv.set(x + 2, y + 2, T('iron', 1)); cv.set(x + 3, y + 2, T('iron', 5))
    return (x, y, x + 5, y + 5)


def sconce(cv, x, y):
    """A torch in an iron sconce: a ring on a wall plate, the torch's shaft, its flame."""
    part(cv, x + 1, y + 7, 4, 3, 'iron', 3)
    cv.vline(x + 2, y + 3, 5, T('timber', 3)); cv.vline(x + 3, y + 3, 5, T('timber', 1))
    for (px, py) in disc(x + 2.5, y + 2, 2.3):
        cv.set(px, py, T('lava', 4 if py > y + 1 else 5))
    return (x, y, x + 6, y + 10)


# --- props ---------------------------------------------------------------------------------
def barrel(cv, x, yb, fam='timber', hoop='iron', w=10, h=12):
    y = yb - h
    for (px, py) in rect(x, y, w, h):
        f = (px - x + 0.5) / w
        bulge = 1 if 0.25 < (py - y) / h < 0.75 else 0
        k = 4 if 0.15 < f < 0.4 else 3 if f < 0.65 else 2 if f < 0.85 else 1
        if (px == x or px == x + w - 1) and not bulge:
            continue
        cv.set(px, py, T(fam, k))
    for hy in (y + 2, y + h - 3):
        for px in range(x, x + w):
            if cv.get(px, hy)[3]:
                cv.set(px, hy, T(hoop, 3 if px < x + w * 0.5 else 1))
    for px in range(x + 1, x + w - 1):   # the lid
        cv.set(px, y, T(fam, 4 if px < x + w - 3 else 3))


def crate(cv, x, yb, fam='timber', w=12, h=10):
    y = yb - h
    part(cv, x, y, w, 3, fam, 4)                   # the top, lit
    boards(cv, x, y + 3, w, h - 3, lambda b, s: (sib(fam, noise2(b, s, 2), 0.3), 3), board=3, seed=x, nails=True, grain=0.05, joints=(40, 41))
    for i in range(h - 4):   # the brace
        cv.set(x + 1 + i * (w - 3) // (h - 4), y + 3 + i, T(fam, 4))
    frame(cv, x, y + 3, w, h - 3, fam, 2, t=1)


def bench(cv, x, yb, fam='timber', leg='iron', w=22):
    for (px, py) in rect(x, yb - 9, w, 2):
        cv.set(px, py, T(fam, 4 if py == yb - 9 else 3))
    for (px, py) in rect(x, yb - 6, w, 2):
        cv.set(px, py, T(fam, 4 if py == yb - 6 else 2))
    for lx in (x + 2, x + w - 4):
        for py in range(yb - 7, yb):
            cv.set(lx, py, T(leg, 3)); cv.set(lx + 1, py, T(leg, 1))
    cv.hline(x + 1, yb - 11, w - 2, T(fam, 3)); cv.hline(x + 1, yb - 12, w - 2, T(fam, 4))
    for lx in (x + 2, x + w - 4):
        cv.vline(lx, yb - 12, 3, T(leg, 3))


def planter(cv, x, yb, pot='clay', plant='leaf', w=10, h=7, seed=0):
    part(cv, x, yb - h, w, h, pot, 3)
    cv.hline(x - 1, yb - h, w + 2, T(pot, 4))
    leafy(cv, x + w / 2, yb - h - 4, w * 0.55, 5, seed=seed, ramp=plant)


def potted_cactus(cv, x, yb):
    """A clay pot with a ribbed column cactus and one arm, spines as lit pairs."""
    part(cv, x, yb - 6, 10, 6, 'clay', 3)
    cv.hline(x - 1, yb - 6, 12, T('clay', 4))
    cylinder(cv, x + 3, yb - 22, 4, 16, 'cactus', 3)
    cylinder(cv, x + 7, yb - 17, 3, 3, 'cactus', 3)
    cylinder(cv, x + 8, yb - 21, 3, 5, 'cactus', 3)
    for (px, py) in rect(x + 3, yb - 23, 4, 1):
        cv.set(px, py, T('cactus', 4))
    for yy in range(yb - 20, yb - 7, 3):
        cv.set(x + 2, yy, T('sand', 5)); cv.set(x + 7, yy + 1, T('sand', 4))


def lamp(cv, x, yb, h=30, metal='iron', glow='lamp'):
    cylinder(cv, x, yb - h, 2, h, metal, 3)
    part(cv, x - 2, yb - 3, 6, 3, metal, 3)
    part(cv, x - 3, yb - h - 2, 8, 2, metal, 4, glint=False)
    glass(cv, x - 2, yb - h, 6, 6, True)
    cv.vline(x - 3, yb - h, 6, T(metal, 4)); cv.vline(x + 4, yb - h, 6, T(metal, 1))
    part(cv, x - 3, yb - h + 6, 8, 2, metal, 3, glint=False)


def trough(cv, x, yb, w=20):
    part(cv, x, yb - 7, w, 7, 'timber', 3)
    for (px, py) in rect(x + 2, yb - 6, w - 4, 2):
        cv.set(px, py, T('water', 3 if (px + py) % 5 else 4))


def tank(cv, x, yb, fam='hull', w=10, h=18, band='berry'):
    cylinder(cv, x, yb - h, w, h, fam, 3)
    for py in (yb - h + 3, yb - 4):
        for px in range(x, x + w):
            step(cv, px, py, -1)
    for (px, py) in rect(x, yb - h + 7, w, 3):
        hit = tone_at(cv, px, py)
        cv.set(px, py, T(band, hit[1] if hit else 3))
    part(cv, x + w // 2 - 2, yb - h - 2, 4, 2, 'iron', 3, glint=False)


def console(cv, x, yb, w=18):
    part(cv, x, yb - 14, w, 14, 'panel', 3)
    part(cv, x + 2, yb - 12, w - 4, 6, 'void', 2, glint=False)
    for i, px in enumerate(range(x + 3, x + w - 3, 3)):
        cv.hline(px, yb - 10 + (i % 2), 2, T('neon_cyan' if i % 3 else 'glowflora', 4))
    for px in range(x + 3, x + w - 3, 4):
        cv.hline(px, yb - 4, 2, T(('berry', 'brass', 'glowflora')[(px // 4) % 3], 4))


def rock(cv, cx, yb, r, fam='regolith'):
    pts = {(x, y) for (x, y) in disc(cx, yb - r * 0.7, r) if y < yb}
    for (x, y) in pts:
        lv = -(x + 0.5 - cx) - (y + 0.5 - (yb - r * 0.7))
        cv.set(x, y, T(sib(fam, noise2(x, y, 3), 0.3), 4 if lv > r * 0.5 else 3 if lv > -r * 0.3 else 2))
    return pts


def dish(cv, x, yb):
    cylinder(cv, x + 6, yb - 14, 2, 14, 'iron', 3)
    for (px, py) in disc(x + 7, yb - 18, 6):
        if py < yb - 15 + (px - x - 7) * 0.3:
            lv = -(px - x - 7) - (py - yb + 18)
            cv.set(px, py, T('hull', 4 if lv > 2 else 3 if lv > -3 else 2))
    cv.set(x + 7, yb - 19, T('berry', 5))


# --- dressing: the things people keep against a front -----------------------------------
# Each has a reason to be there and a way it stands or is fixed: a water butt only under a
# downpipe, logs by a house with a hearth, a keypad beside every hatch. Each returns its box.
def water_butt(cv, x, ground):
    """A rain barrel the downpipe runs into: staves, two hoops, a lid, a brass tap low down."""
    barrel(cv, x, ground - 2, 'timber', 'iron', w=10, h=13)
    part(cv, x - 1, ground - 2, 12, 2, 'stone', 3, glint=False)          # the stand it sits on
    part(cv, x - 1, ground - 16, 12, 2, 'timber', 4, glint=False)        # the lid
    cv.set(x + 3, ground - 6, T('brass', 5)); cv.set(x + 3, ground - 5, T('brass', 2)); cv.set(x + 2, ground - 5, T('brass', 3))
    return (x - 1, ground - 16, x + 11, ground)


def log_store(cv, x, ground, w=16, rows=3, seed=0):
    """Firewood stacked against the wall by a house with a hearth: log ends in rows, each a
    disc with its rings and a lit upper left, bark between them."""
    for (px, py) in rect(x, ground - rows * 4 - 1, w, rows * 4 + 1):
        cv.set(px, py, T('timber', 1))
    for r in range(rows):
        cy = ground - 3 - r * 4
        off = 2 if r % 2 else 0
        for i, cx in enumerate(range(x + 2 + off, x + w - 1, 4)):
            rp = sib('timber', noise2(i, r, seed), 0.4)
            for (px, py) in disc(cx, cy, 2.0):
                lv = (px - cx) + (py - cy)
                cv.set(px, py, T(rp, 5 if lv < -1 else 4 if lv < 1 else 3))
            cv.set(int(cx), int(cy), T(rp, 2))
    part(cv, x - 1, ground - rows * 4 - 3, w + 2, 2, 'timber', 3, glint=False)   # a plank laid over it against the rain
    return (x - 1, ground - rows * 4 - 3, x + w + 1, ground)


def hanging_basket(cv, x, y, seed=0):
    """A basket of flowers on a wall bracket: plate, arm, three chains, a moss-lined basket,
    trailing leaves and flowers in the colourway's colour."""
    part(cv, x, y, 2, 6, 'iron', 3, glint=False)
    cv.hline(x + 2, y + 1, 8, T('iron', 4)); cv.hline(x + 2, y + 2, 8, T('iron', 1))
    for i, cx in enumerate((x + 4, x + 7, x + 10)):
        cv.vline(cx, y + 3, 3, T('iron', 2))
    for (px, py) in rect(x + 3, y + 6, 9, 4):
        cv.set(px, py, T('earth', 3 if py < y + 8 else 2))
    leafy(cv, x + 7.5, y + 7, 5.5, 3.5, seed=seed + 3)
    col = paint('flower', 'berry')
    for (fx, fy) in ((x + 4, y + 5), (x + 8, y + 4), (x + 11, y + 7), (x + 6, y + 9)):
        cv.hline(fx, fy, 2, T(col, 4)); cv.set(fx, fy, T(col, 5))
    for tx in (x + 4, x + 10):   # trailing stems
        for i in range(4):
            cv.set(tx + (i % 2), y + 10 + i, T('leaf', 3 if i % 2 else 2))
    return (x, y, x + 13, y + 14)


def plaque(cv, x, y):
    """A cottage's name cut in a slate plaque, the letters picked out in white, on two screws."""
    part(cv, x, y, 9, 7, 'slate', 3)
    cv.hline(x + 2, y + 3, 5, T('plaster', 4)); cv.set(x + 3, y + 2, T('plaster', 5))
    cv.set(x + 1, y + 1, T('iron', 4)); cv.set(x + 7, y + 1, T('iron', 4))
    return (x, y, x + 9, y + 7)


def creeper(cv, x, w, top, ground, seed=0):
    """Ivy climbing a wall from its foot: clumps of leaves on woody stems, thinning upwards,
    tied in by nothing but its own roots."""
    shape = set()
    for i in range(int(w * (ground - top) / 22)):
        cx = x + noise2(i, 1, seed) * w
        f = noise2(i, 2, seed)
        cy = ground - 4 - f * f * (ground - top - 6)
        if abs(cx - (x + w / 2)) > w / 2 * (1.1 - 0.5 * (ground - cy) / (ground - top)):
            continue
        shape |= {p for p in disc(cx, cy, 2.2)}
    for (px, py) in sorted(shape):
        b = 4 if (px - 1, py) not in shape or (px, py - 1) not in shape else 2 if (px, py + 1) not in shape else 3
        cv.set(px, py, T(sib('leaf', noise2(px // 3, py // 3, seed), 0.35), b))
    for i in range(3):   # stems showing at the foot
        sx = x + 2 + i * max(1, w // 3)
        cv.vline(sx, ground - 6, 6, T('timber', 2))
    xs = [p[0] for p in shape] or [x]
    ys = [p[1] for p in shape] or [ground]
    return (min(xs), min(ys), max(xs) + 1, ground)


def nets(cv, x, y, w=14):
    """A fishing net hung to dry on two pegs: the mesh in a sagging drape, cork floats along it."""
    for px in (x, x + w - 1):
        part(cv, px - 1, y, 3, 2, 'timber', 4, glint=False)
    for px in range(x, x + w):
        sag = int(4 * math.sin(math.pi * (px - x) / (w - 1)))
        for py in range(y + 2, y + 9 + sag):
            if (px + py) % 3 == 0 or (px - py) % 3 == 0:
                cv.set(px, py, T('earth', 1 if py > y + 6 + sag else 2))   # tarred mesh
        cv.set(px, y + 2 + sag // 2, T('earth', 3))
    for i, px in enumerate(range(x + 2, x + w - 1, 4)):
        sag = int(4 * math.sin(math.pi * (px - x) / (w - 1)))
        f = 'berry' if i % 2 else 'brass'                                   # floats
        cv.hline(px, y + 9 + sag, 2, T(f, 4)); cv.hline(px, y + 10 + sag, 2, T(f, 2))
    return (x - 1, y, x + w + 1, y + 15)


def aboard(cv, x, ground, pic='cup'):
    """An A-board out on the ground: a slate in a timber frame on two splayed legs."""
    part(cv, x, ground - 16, 10, 12, 'timber', 3)
    part(cv, x + 1, ground - 15, 8, 10, 'slate', 1, glint=False)
    picto(cv, x + 2, ground - 13, pic, 'plaster', 4)
    for lx in (x, x + 9):   # the legs
        cv.vline(lx, ground - 4, 4, T('timber', 2))
    return (x, ground - 16, x + 10, ground)


def produce_crates(cv, x, ground, goods=('berry', 'leaf'), w=10, seed=0):
    """Two slatted crates stacked against the wall, the top one open with its goods heaped in
    it (apples and greens at a market, fish on ice at a fish shed)."""
    for i in range(2):
        cy = ground - 7 * (i + 1)
        part(cv, x, cy, w, 7, 'timber', 3)
        for py in (cy + 2, cy + 4):
            cv.hline(x + 1, py, w - 2, T('timber', 1))
    for i, gx in enumerate(range(x + 1, x + w - 1, 2)):   # the goods heaped over the rim
        g = goods[(i + seed) % len(goods)]
        cv.hline(gx, ground - 15 - (i % 2), 2, T(g, 4)); cv.hline(gx, ground - 14, 2, T(g, 2))
        cv.set(gx, ground - 15 - (i % 2), T(g, 5))
    return (x, ground - 16, x + w, ground)


def notice_case(cv, x, y):
    """A glazed notice case on a public building: a painted frame, bills pinned behind glass."""
    frame(cv, x, y, 13, 11, paint('trim', 'timber'), 3, t=1)
    for (px, py) in rect(x + 1, y + 1, 11, 9):
        cv.set(px, py, T('slate', 1))
    for (bx, by, bw_, bh, c) in ((x + 2, y + 2, 4, 5, 'plaster'), (x + 7, y + 2, 4, 3, 'brass'), (x + 6, y + 6, 5, 3, 'sky')):
        part(cv, bx, by, bw_, bh, c, 4, glint=False)
        cv.hline(bx + 1, by + 1, bw_ - 2, T(c, 2))
    cv.set(x + 2, y + 1, T('slate', 4)); cv.set(x + 3, y + 1, T('slate', 4))   # the glass's glint
    return (x, y, x + 13, y + 11)


def bird_box(cv, x, y):
    """A nesting box nailed up under the eaves: a pitched lid, a round hole, a perch peg."""
    part(cv, x, y + 2, 7, 8, 'timber', 3)
    for i in range(4):
        cv.hline(x + 3 - i, y + i - 1, 1 + 2 * i, T('timber', 4 if i < 2 else 2))
    cv.hline(x + 2, y + 4, 3, T('timber', 0)); cv.hline(x + 2, y + 5, 3, T('timber', 1))
    cv.set(x + 3, y + 7, T('timber', 5))
    return (x - 1, y - 1, x + 8, y + 10)


def wall_clock(cv, x, y):
    """A clock on a wall bracket over a door, as on any Victorian hall: brass bezel, a cream
    face, hands at ten to two."""
    part(cv, x + 4, y, 4, 3, 'iron', 3, glint=False)
    for (px, py) in disc(x + 6, y + 8, 5.5):
        lv = (px - x - 6) + (py - y - 8)
        cv.set(px, py, T('brass', 4 if lv < -2 else 3 if lv < 3 else 2))
    for (px, py) in disc(x + 6, y + 8, 4.0):
        cv.set(px, py, T('plaster', 5 if px + py < x + y + 13 else 4))
    for (px, py) in ((x + 6, y + 5), (x + 6, y + 6), (x + 6, y + 7), (x + 7, y + 8), (x + 8, y + 8)):
        cv.set(px, py, T('iron', 1))
    for (px, py) in ((x + 6, y + 4), (x + 10, y + 8), (x + 6, y + 12), (x + 2, y + 8)):
        cv.set(px, py, T('iron', 2))
    return (x, y, x + 12, y + 14)


def cables(cv, x0, x1, y, seed=0):
    """Power and phone lines crossing a front from the next building: three cables that sag
    between iron hooks, a junction box where they branch into the building."""
    hooks = list(range(x0 + 2, x1, 22))
    for i, (c, k) in enumerate((('iron', 3), ('asphalt', 4), ('iron', 4))):
        for px in range(x0, x1):
            seg = (px - x0) % 22
            sag = int(2.5 * math.sin(math.pi * seg / 22)) + i * 2
            cv.set(px, y + sag, T(c, k + (1 if seg in (5, 6) else 0)))   # wet sheen on the cable's curve
            step(cv, px, y + sag + 1, -1)                                  # its shadow on the wall
    for hx in hooks:
        part(cv, hx - 1, y - 2, 3, 2, 'iron', 4, glint=False)
    return (x0, y - 2, x1, y + 6)


def paper_lanterns(cv, x0, x1, y, seed=0):
    """A string of paper lanterns between two hooks over a doorway, each lit from inside,
    in the colourway's cloth with a dark rib top and bottom."""
    for px in (x0, x1 - 1):
        part(cv, px - 1, y - 1, 3, 2, 'iron', 4, glint=False)
    for px in range(x0, x1):
        sag = int(2 * math.sin(math.pi * (px - x0) / max(1, x1 - x0 - 1)))
        cv.set(px, y + sag, T('iron', 2))
    cloth = paint('cloth', 'berry')
    for i, cx in enumerate(range(x0 + 4, x1 - 2, 7)):
        sag = int(2 * math.sin(math.pi * (cx - x0) / max(1, x1 - x0 - 1)))
        cy = y + sag + 4
        for (px, py) in disc(cx, cy, 2.6):
            lv = (px - cx) + (py - cy) * 0.5
            cv.set(px, py, T(cloth if i % 2 == 0 else 'lamp', 5 if lv < -1 else 4 if lv < 1 else 3))
        cv.hline(cx - 1, cy - 3, 3, T('iron', 1)); cv.hline(cx - 1, cy + 3, 3, T('iron', 1))
        cv.set(cx, y + sag + 1, T('iron', 2))
    return (x0 - 1, y - 1, x1, y + 10)


def laundry(cv, x, y, w=14):
    """Washing on a line strung from a window's frame to a hook: three things pegged out."""
    part(cv, x + w - 1, y - 1, 2, 3, 'iron', 4, glint=False)
    cv.hline(x, y, w, T('plaster', 3))
    for i, (gx, gw, gh, c) in enumerate(((x + 1, 4, 6, paint('cloth', 'berry')), (x + 6, 3, 5, 'plaster'), (x + 10, 3, 7, 'sky'))):
        for (px, py) in rect(gx, y + 1, gw, gh):
            cv.set(px, py, T(c, 4 if px == gx else 2 if py == y + gh else 3))
        cv.set(gx, y, T('timber', 4)); cv.set(gx + gw - 1, y, T('timber', 4))
    return (x, y - 1, x + w + 1, y + 8)


def painted_sign(cv, x, y, w, h, pic, fam='berry'):
    """A sign painted straight onto a shed's wall: a field of paint with a border, a big
    pictogram twice size, the paint flaking in clusters where the sheet's ribs stand out."""
    for (px, py) in rect(x, y, w, h):
        hit = tone_at(cv, px, py)
        k = hit[1] if hit else 3
        edge = px in (x, x + w - 1) or py in (y, y + h - 1)
        cv.set(px, py, T('plaster' if edge else fam, max(1, min(4, k + (1 if edge else 0)))))
    rows = PICTO[pic]
    ox, oy = x + w // 2 - 7, y + (h - 14) // 2
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in '#+':
                for dx in (0, 1):
                    for dy in (0, 1):
                        cv.set(ox + 2 * c + dx, oy + 2 * r + dy, T('plaster', 5 if dy == 0 else 4))
    for i in range(w * h // 40):   # flaking back to the metal, two pixels at a time
        fx, fy = x + 1 + int(noise2(i, 1, x) * (w - 3)), y + 1 + int(noise2(i, 2, x) * (h - 2))
        cv.set(fx, fy, T('iron', 3)); cv.set(fx + 1, fy, T('iron', 2))
    return (x, y, x + w, y + h)


def meter_box(cv, x, y):
    """An electricity meter in a grey box, the cable into it from above, a dial behind glass."""
    part(cv, x, y, 9, 12, 'concrete', 4)
    glass(cv, x + 2, y + 2, 5, 4, False)
    cv.hline(x + 3, y + 4, 3, T('plaster', 5))
    cv.hline(x + 2, y + 8, 5, T('berry', 3)); cv.vline(x + 4, y - 4, 4, T('iron', 1))
    return (x, y - 4, x + 9, y + 12)


def vending(cv, x, ground):
    """A drinks machine against the wall: a lit front of cans, a coin slot, a dark tray."""
    part(cv, x, ground - 26, 14, 26, paint('cloth', 'berry'), 3)
    glass(cv, x + 2, ground - 24, 10, 12, True)
    for r in range(3):
        for i, cx in enumerate(range(x + 3, x + 11, 3)):
            col = ('sky', 'berry', 'leaf', 'brass')[(i + r) % 4]
            cv.vline(cx, ground - 23 + r * 4, 3, T(col, 4)); cv.vline(cx + 1, ground - 23 + r * 4, 3, T(col, 2))
    for i, bx in enumerate(range(x + 2, x + 12, 3)):   # a button and a price light under each column
        cv.hline(bx, ground - 11, 2, T('hull', 4)); cv.set(bx, ground - 10, T('glowflora' if i % 2 else 'neon_pink', 4))
    part(cv, x + 2, ground - 8, 5, 2, 'iron', 1, glint=False)            # the coin slot plate
    cv.vline(x + 10, ground - 9, 3, T('brass', 4))
    part(cv, x + 2, ground - 5, 10, 3, 'void', 2, glint=False)            # the tray
    cv.hline(x + 1, ground - 25, 12, T(paint('cloth', 'berry'), 5))       # its lit name strip
    return (x, ground - 26, x + 14, ground)


def bins(cv, x, ground):
    """Two bins against the wall, lids shut, a handle on each."""
    for i, fam in enumerate(('iron', 'leaf_cool')):
        bx = x + i * 9
        part(cv, bx, ground - 12, 8, 12, fam, 3)
        part(cv, bx - 1, ground - 13, 10, 2, fam, 4, glint=False)
        cv.hline(bx + 2, ground - 9, 4, T(fam, 1))
    return (x - 1, ground - 13, x + 18, ground)


def camera(cv, x, y):
    """A security camera on a wall bracket, looking down the street, its red light on."""
    part(cv, x, y, 2, 4, 'iron', 3, glint=False)
    cv.hline(x + 2, y + 1, 2, T('iron', 2))
    part(cv, x + 3, y, 7, 4, 'hull', 3)
    cv.set(x + 9, y + 2, T('void', 1)); cv.set(x + 4, y + 1, T('neon_pink', 4))
    return (x, y, x + 10, y + 4)


def keypad(cv, x, y, glow='neon_cyan'):
    """The control panel beside a hatch: a screen, a pad of keys, a status lamp."""
    part(cv, x, y, 6, 10, 'panel', 2)
    cv.hline(x + 1, y + 1, 4, T('void', 2)); cv.hline(x + 1, y + 2, 4, T(glow, 4))
    for (px, py) in ((x + 1, y + 4), (x + 3, y + 4), (x + 1, y + 6), (x + 3, y + 6)):
        cv.hline(px, py, 2, T('hull', 4))
    cv.set(x + 4, y + 8, T('glowflora', 5))
    return (x, y, x + 6, y + 10)


def extinguisher(cv, x, y):
    """A fire extinguisher in its wall bracket with a label plate over it, where any crew can reach."""
    part(cv, x, y, 6, 3, 'plaster', 4, glint=False)
    cv.hline(x + 1, y + 1, 4, T('berry', 3))
    cylinder(cv, x + 1, y + 5, 4, 10, 'berry', 3)
    part(cv, x + 1, y + 4, 4, 2, 'iron', 3, glint=False)
    cv.hline(x, y + 9, 6, T('iron', 2))
    return (x, y, x + 6, y + 15)


def handrail(cv, x0, x1, y):
    """A grab rail along a station wall on standoffs every 10 px, for low gravity."""
    for px in range(x0, x1):
        cv.set(px, y, T('hull', 5)); cv.set(px, y + 1, T('hull', 3))
    for px in range(x0 + 2, x1 - 1, 10):
        cv.set(px, y + 2, T('iron', 2)); cv.set(px, y + 3, T('iron', 1))
    return (x0, y, x1, y + 4)


def floodlight(cv, x, y):
    """A floodlight on a bracket over a hatch, lit (the moon's night is long)."""
    part(cv, x, y, 2, 4, 'iron', 3, glint=False)
    cv.hline(x + 2, y + 1, 3, T('iron', 2))
    part(cv, x + 4, y - 1, 7, 5, 'hull', 3)
    cv.hline(x + 5, y + 3, 5, T('lamp', 5)); cv.hline(x + 5, y + 4, 5, T('lamp', 3))
    return (x, y - 1, x + 11, y + 5)


def gas_rack(cv, x, ground):
    """Gas bottles chained in a rack against the wall: oxygen and nitrogen, colour-banded."""
    part(cv, x - 1, ground - 3, 15, 3, 'iron', 3, glint=False)
    for i, band in enumerate(('sky', 'lagoon', 'sky')):
        bx = x + i * 5
        cylinder(cv, bx, ground - 18, 4, 15, 'hull', 3)
        cv.hline(bx, ground - 16, 4, T(band, 4)); cv.hline(bx, ground - 15, 4, T(band, 2))
        part(cv, bx + 1, ground - 20, 2, 2, 'iron', 3, glint=False)
    cv.hline(x - 1, ground - 11, 15, T('iron', 1))   # the chain
    return (x - 1, ground - 20, x + 14, ground)


def warning(cv, x, y):
    """A hazard plate: a yellow triangle with its mark, on a white plate."""
    part(cv, x, y, 9, 8, 'hull', 4, glint=False)
    for i in range(5):
        cv.hline(x + 4 - i, y + 1 + i, 2 * i + 1, T('brass', 4 if i < 4 else 3))
    cv.vline(x + 4, y + 2, 3, T('iron', 1))   # its mark
    return (x, y, x + 9, y + 8)


# --- the environments ----------------------------------------------------------------------
def _sprite(w, h, draw):
    cv = Canvas(w + 2, h + 2)
    sub = Canvas(w, h)
    draw(sub)
    for y in range(h):
        for x in range(w):
            c = sub.get(x, y)
            if c[3]:
                cv.set(x + 1, y + 1, c)
    outline(cv)
    return cv


def _patch(wall_kind, w, h, draw, seed=0):
    """A piece shown on a patch of its own wall (doors, windows, roofs)."""
    cv = Canvas(w, h)
    wall(cv, 0, 0, w, h, wall_kind, seed)
    draw(cv)
    return cv


ENV = {
    'valley': {
        'walls': ('plaster', 'drystone', 'whitewash', 'boards_lagoon'),
        'roofs': ('tiles', 'slate', 'thatch', 'palm'),
        'doors': [dict(fam='sky', kind='plank', frame='stone', arch=True), dict(fam='berry', kind='panel', frame='timber'),
                  dict(fam='timber', kind='ledged', frame='stone', paint=False), dict(fam='dusk', kind='stable', frame='timber'),
                  dict(fam='lagoon', kind='plank', frame='timber')],
        'windows': [dict(shutters='dusk', box=True), dict(cols=3, rows=1), dict(arch=True, frame_fam='stone', cols=2, rows=1),
                    dict(shutters='lagoon', lit=True), dict(cols=1, rows=2, box=True, frame_fam='sky', paint_frame=True)],
        'signs': ('bread', 'cup', 'fish', 'key'),
        'wall_patch': 'plaster',
    },
    'cogsworth': {
        'walls': ('brick', 'brick_soot', 'stock', 'ashlar'),
        'roofs': ('copper', 'slate', 'glass', 'tiles'),
        'doors': [dict(fam='berry', kind='panel', frame='ashlar', fan=True), dict(fam='iron', kind='studded', frame='clay', arch=True),
                  dict(fam='dusk', kind='glazed', frame='ashlar'), dict(fam='copper', kind='panel', frame='ashlar', arch=True, big=True)],
        'windows': [dict(frame_fam='plaster', paint_frame=True, cols=2, rows=2, lit=True), dict(frame_fam='plaster', paint_frame=True, arch=True, lit=True, cols=2),
                    dict(frame_fam='iron', cols=4, rows=3, sill='ashlar', w=14), dict(frame_fam='plaster', paint_frame=True, cols=1, rows=2, blind=True)],
        'signs': ('gear', 'cup', 'key', 'pot'),
        'wall_patch': 'brick',
    },
    'sunstone': {
        'walls': ('bleached', 'adobe', 'corrugated', 'boards_berry'),
        'roofs': ('falsefront', 'vigas', 'corrugated', 'shingle'),
        'doors': [dict(fam='bleached', kind='batwing', frame='timber', big=True, step='timber'),
                  dict(fam='lagoon', kind='plank', frame='timber', step='adobe'),
                  dict(fam='bleached', kind='glazed', frame='bleached', step='timber'),
                  dict(fam='timber', kind='ledged', frame='bleached', paint=False, step='timber')],
        'windows': [dict(frame_fam='bleached', curtain=True, w=12, sill=None), dict(frame_fam='timber', bars=True, sill='adobe', cols=1, rows=1, w=10, h=10),
                    dict(frame_fam='bleached', cols=2, rows=2, lit=True), dict(frame_fam='bleached', shutters='bleached', cols=1, rows=2)],
        'signs': ('mug', 'sack', 'shoe', 'star'),
        'wall_patch': 'bleached',
    },
    'hearthold': {
        'walls': ('ashlar', 'rubble', 'ashlar', 'rubble'),
        'roofs': ('crenel', 'cone', 'slate', 'parapet'),
        'doors': [dict(fam='timber', kind='studded', frame='ashlar', arch=True, big=True), dict(fam='timber', kind='plank', frame='ashlar', arch=True),
                  dict(fam='timber', kind='ledged', frame='ashlar', arch=True), dict(fam='timber', kind='studded', frame='stone', big=True)],
        'windows': [dict(arch=True, frame_fam='ashlar', cols=1, rows=1, lit=True, leaded=True, sill='ashlar', w=8, h=18),
                    dict(slit=True),
                    dict(arch=True, frame_fam='ashlar', cols=2, rows=2, lit=True, leaded=True, sill='ashlar'),
                    dict(frame_fam='timber', cols=2, rows=1, shutters='timber', sill='ashlar')],
        'signs': ('shield', 'moon', 'star', 'key'),
        'wall_patch': 'ashlar',
    },
    'neon': {
        'walls': ('concrete', 'tile', 'cladding', 'concrete'),
        'roofs': ('flat', 'flat', 'parapet', 'flat'),
        'doors': [dict(fam='iron', kind='slide', frame='concrete', big=True, step='concrete'),
                  dict(fam='panel', kind='roller', frame='concrete', big=True, step='concrete', role='shutter'),
                  dict(fam='iron', kind='steel', frame='concrete', step='concrete'), dict(fam='dusk', kind='glazed', frame='concrete', step='concrete')],
        'windows': [dict(frame_fam='concrete', lit=True, cols=2, rows=1), dict(frame_fam='iron', lit=True, blind=True, cols=1, rows=1, curtain=False),
                    dict(frame_fam='concrete', lit=False, cols=2, rows=2), dict(frame_fam='iron', lit=True, cols=3, rows=1, bars=True, curtain=False)],
        'signs': ('cup', 'bowl', 'moon', 'fish'),
        'wall_patch': 'concrete',
    },
    'halcyon': {
        'walls': ('bulkhead',) * 4,
        'roofs': ('radiator', 'dome', 'flat', 'radiator'),
        'doors': [dict(fam='panel', kind='hatch', frame='hull', coaming=True), dict(fam='panel', kind='pod', frame='hull', coaming=True),
                  dict(fam='panel', kind='slide', frame='hull', coaming=True, big=True), dict(fam='panel', kind='hatch', frame='panel', coaming=True)],
        'windows': [dict(round=True), dict(frame_fam='panel', cols=3, rows=1, lit=False, curtain=False, sill=None),
                    dict(frame_fam='panel', cols=1, rows=1, lit=True, curtain=False, sill=None), dict(round=True, lit=False)],
        'signs': ('bolt', 'leaf', 'bed', 'cup'),
        'wall_patch': 'bulkhead',
    },
    'lumen': {
        'walls': ('berm', 'hull_ext', 'hull_ext', 'berm'),
        'roofs': ('berm', 'dome', 'radiator', 'berm'),
        'doors': [dict(fam='panel', kind='hatch', frame='hull', collar='hull_cool'), dict(fam='panel', kind='pod', frame='hull', coaming=True),
                  dict(fam='panel', kind='hatch', frame='hull', coaming=True), dict(fam='panel', kind='pod', frame='hull', collar='hull_cool')],
        'windows': [dict(round=True, collar=True), dict(round=True, lit=False), dict(frame_fam='panel', cols=2, rows=1, lit=True, curtain=False, sill=None),
                    dict(frame_fam='hull', cols=1, rows=1, lit=False, curtain=False, sill=None)],
        'signs': ('leaf', 'bolt', 'bed', 'moon'),
        'wall_patch': 'berm',
    },
}

# The walls an environment may build in (art-style.md, "the setting sets the style"):
# no brick in the neon city, no stone, brick or timber on the station or the moon.
ALLOWED_WALLS = {
    'valley': {'plaster', 'drystone', 'whitewash', 'pink', 'boards_sky', 'boards_lagoon', 'boards_timber'},
    'cogsworth': {'brick', 'brick_soot', 'stock', 'ashlar'},
    'sunstone': {'bleached', 'adobe', 'corrugated', 'boards_berry'},
    'hearthold': {'ashlar', 'rubble'},
    'neon': {'concrete', 'tile', 'cladding'},
    'halcyon': {'bulkhead'},
    'lumen': {'berm', 'hull_ext', 'panel'},
}
# What heads a square opening in each wall: a lintel the wall needs to carry itself.
# Render and boards hide or need none; brick takes a soldier arch; adobe a timber lintel.
HEAD = {'drystone': 'stone', 'rubble': 'ashlar', 'ashlar': 'ashlar', 'brick': 'brick', 'brick_soot': 'brick',
        'stock': 'brick', 'adobe': 'timber'}

PIECES = ('front', 'door', 'window', 'roof', 'sign', 'prop')


def variants(env: str, piece: str) -> int:
    e = ENV[env]
    return {'front': 4, 'door': len(e['doors']), 'window': len(e['windows']), 'roof': len(LAYOUT[env]),
            'sign': 4, 'prop': 4}[piece]


def _door_into(cv, env, v, x, yb, seed=0, wall_kind=None):
    """A door of the kit at x, standing on yb. A single door is 32 x 14, a shop's or a
    double door 32 x 22 (size-guide 3); a hatch 32 x 18 with its coaming. Returns its box."""
    spec = ENV[env]['doors'][v % len(ENV[env]['doors'])]
    kind = spec['kind']
    fam = spec['fam']
    if spec.get('paint', True):
        fam = paint(spec.get('role', 'door'), fam)
    w = 22 if spec.get('big') else 18 if kind in ('hatch', 'pod') else 14
    h = 32
    lit = env in ('neon', 'halcyon', 'lumen', 'cogsworth')
    step_fam = spec.get('step', 'regolith' if env == 'lumen' else 'stone')
    ROOM[0] = 'lab' if env in ('halcyon', 'lumen') else 'noren' if env == 'neon' and spec.get('big') else 'bar'
    lintel = None if spec.get('arch') or kind in ('hatch', 'pod') else HEAD.get(wall_kind or '')
    if lintel == 'brick':
        lintel = 'ashlar'   # a door in brick takes a stone head (its arch is the window's)
    return doorway(cv, x, yb, w, h, fam, kind, spec['frame'], seed=seed + v, arch=spec.get('arch', False),
                   fan=spec.get('fan', False), step_fam=step_fam, lit=lit, coaming=spec.get('coaming', False),
                   collar=spec.get('collar'), lintel=lintel, frame_t=3 if kind in ('hatch', 'pod') else 2)


def _window_into(cv, env, v, x, y, seed=0, wall_kind=None, extra=None):
    """A window of the kit with its top left at x, y. 16 tall and 12 wide by default
    (size-guide 3); multi-pane 18 wide; a lancet 8 x 18; an adobe window small and deep.
    Returns its box."""
    spec = dict(ENV[env]['windows'][v % len(ENV[env]['windows'])])
    spec.update(extra or {})
    if spec.pop('round', False):
        lit = spec.get('lit', True)
        ring = 'brass' if env == 'cogsworth' else 'hull' if env == 'lumen' else 'panel'
        if spec.get('collar'):   # a window through a heap of soil keeps its own collar
            for (px, py) in disc(x + 7, y + 7, 10):
                lv = -(px + 0.5 - x - 7) - (py + 0.5 - y - 7)
                cv.set(px, py, T('hull_cool', 4 if lv > 4 else 3 if lv > -4 else 2))
            porthole(cv, x + 7, y + 7, 7, ring, lit)
            return (x - 3, y - 3, x + 18, y + 18)
        porthole(cv, x + 7, y + 7, 7, ring, lit, space=(env == 'halcyon' and not lit))
        return (x, y, x + 15, y + 15)
    if spec.pop('slit', False):   # an arrow slit: a splayed reveal, a dark slot, a cross at mid height
        for yy in range(y, y + 16):
            cv.set(x, yy, T('ashlar', 5)); cv.set(x + 1, yy, T('ashlar', 4))
            cv.set(x + 2, yy, T('stone', 0)); cv.set(x + 3, yy, T('stone', 0))
            cv.set(x + 4, yy, T('ashlar', 2))
        cv.hline(x + 1, y + 7, 3, T('stone', 0))
        part(cv, x - 1, y - 2, 7, 2, 'ashlar', 4, glint=False)
        part(cv, x - 1, y + 16, 7, 2, 'ashlar', 4, glint=False)
        return (x - 1, y - 2, x + 6, y + 18)
    w = spec.pop('w', None) or (18 if spec.get('cols', 2) >= 3 else 12)
    h = spec.pop('h', None) or 16
    if 'lintel' not in spec and not spec.get('arch'):
        spec['lintel'] = HEAD.get(wall_kind or '')
    return casement(cv, x, y, w, h, seed=seed, space=env == 'halcyon' and not spec.get('lit', False), **spec)


def door(env, v):
    kind = ENV[env]['wall_patch']
    return _patch(kind, 40, 48, lambda cv: _door_into(cv, env, v, 12, 44, seed=v, wall_kind=kind), seed=v + 3)


def window(env, v):
    kind = ENV[env]['wall_patch']
    return _patch(kind, 40, 34, lambda cv: _window_into(cv, env, v, 11, 8, seed=v, wall_kind=kind), seed=v + 5)


def roof(env, v):
    """A roof or top, standing on a short piece of wall."""
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    cv = Canvas(50, 46)
    wall(cv, 2, 28, 46, 18, lay['wall'], v)
    roof_mass(cv, 2, 2, 46, 26, lay['roof'], lay['shape'], seed=v + 11, gable_wall=lay.get('gable', lay['wall']))
    return cv


def sign(env, v):
    pics = ENV[env]['signs']
    pic = pics[v % len(pics)]
    kind = 'hull_ext' if env == 'lumen' else ENV[env]['wall_patch']   # signs go on the shell, never on the soil
    cv = Canvas(40, 30)
    wall(cv, 0, 0, 40, 30, kind, v + 7)
    if env == 'valley':
        hanging_sign(cv, 4, 6, pic, ('timber', 'sky', 'berry', 'dusk')[v], 'brass' if v != 3 else 'plaster')
    elif env == 'cogsworth':
        if v < 2:
            fascia(cv, 2, 8, 36, pic, ('berry', 'copper')[v], 'brass')
        elif v == 2:
            hanging_sign(cv, 4, 6, pic, 'iron', 'brass')
        else:   # a brass plate by a door, on four screws
            part(cv, 10, 8, 20, 14, 'brass', 3)
            picto(cv, 17, 11, pic, 'iron', 2)
            for (sx, sy) in ((11, 9), (28, 9), (11, 20), (28, 20)):
                cv.set(sx, sy, T('brass', 5))
    elif env == 'sunstone':
        if v < 3:
            fascia(cv, 2, 8, 36, pic, ('berry', 'sky', 'bleached')[v], 'plaster' if v < 2 else 'berry')
        else:
            hanging_sign(cv, 4, 6, pic, 'bleached', 'clay')
    elif env == 'hearthold':
        if v == 0:
            banner(cv, 13, 5, 12, 20)
        elif v == 1:
            for (x, y) in rect(12, 4, 16, 18):   # a painted shield on the wall
                if y < 14 or abs(x + 0.5 - 20) < (22 - y) * 1.0:
                    cv.set(x, y, T('berry' if (x < 20) == (y < 13) else 'brass', 4 if x < 16 else 3))
            outline(cv, {(x, y) for (x, y) in rect(12, 4, 16, 18) if y < 14 or abs(x + 0.5 - 20) < (22 - y) * 1.0})
        elif v == 2:
            sconce(cv, 17, 8)
        else:
            part(cv, 10, 6, 20, 14, 'ashlar', 4)
            picto(cv, 17, 9, pic, 'ashlar', 2)
    elif env == 'neon':
        if v < 2:
            lightbox(cv, 4, 10, 32, pic, ('neon_pink', 'neon_cyan')[v])
        elif v == 2:
            blade(cv, 17, 2, 26, 'neon_cyan', ('moon', 'cup'))
        else:
            awning(cv, 0, 12, 40, 'lagoon', 'plaster')
    else:   # halcyon, lumen
        if v < 2:
            stencil(cv, 4, 10, 32, ('berry', 'sky')[v], pic)
        elif v == 2:
            part(cv, 10, 8, 20, 12, 'plaster', 4)
            picto(cv, 17, 10, pic, 'iron', 2)
            status_light(cv, 31, 9)
        else:
            for x in range(2, 38):
                for y in range(18, 22):
                    cv.set(x, y, T('brass', 4) if ((x + y) // 3) % 2 else T('iron', 1))
            status_light(cv, 18, 8, 'neon_cyan' if env == 'halcyon' else 'glowflora')
    return cv


def prop(env, v):
    def draw(cv):
        yb = cv.h - 2
        if env == 'valley':
            [lambda: barrel(cv, 4, yb), lambda: bench(cv, 1, yb, 'timber', 'timber'),
             lambda: planter(cv, 5, yb, 'clay', 'leaf', seed=v), lambda: crate(cv, 3, yb, 'timber')][v]()
        elif env == 'cogsworth':
            [lambda: lamp(cv, 9, yb, 26, 'iron'), lambda: bench(cv, 1, yb, 'timber', 'iron'),
             lambda: barrel(cv, 4, yb, 'iron', 'brass'), lambda: crate(cv, 3, yb, 'copper')][v]()
        elif env == 'sunstone':
            [lambda: barrel(cv, 4, yb, 'bleached', 'iron'), lambda: trough(cv, 1, yb),
             lambda: crate(cv, 3, yb, 'bleached'), lambda: potted_cactus(cv, 5, yb)][v]()
        elif env == 'hearthold':
            [lambda: barrel(cv, 4, yb, 'timber', 'iron'), lambda: bench(cv, 1, yb, 'ashlar', 'ashlar'),
             lambda: lamp(cv, 9, yb, 20, 'iron', 'lava'), lambda: crate(cv, 3, yb, 'timber')][v]()
        elif env == 'neon':
            [lambda: planter(cv, 5, yb, 'concrete', 'leaf', seed=v), lambda: bench(cv, 1, yb, 'iron', 'iron'),
             lambda: lamp(cv, 9, yb, 28, 'iron'), lambda: crate(cv, 3, yb, 'sky')][v]()
        elif env == 'halcyon':
            [lambda: tank(cv, 6, yb), lambda: console(cv, 2, yb), lambda: crate(cv, 3, yb, 'panel'),
             lambda: planter(cv, 5, yb, 'hull', 'leaf', seed=v)][v]()
        else:
            [lambda: rock(cv, 11, yb, 7), lambda: dish(cv, 4, yb), lambda: tank(cv, 6, yb, 'hull', band='brass'),
             lambda: crate(cv, 3, yb, 'panel')][v]()
    return _sprite(22, 34, draw)


# --- fronts --------------------------------------------------------------------------------
# Each front is a whole building made only of its environment's pieces: wall, roof (kind and
# shape), storeys, and what stands in its face, by x on a 68 px front. Heights follow the
# scale table (size-guide 3): an adult 25, a door 32 x 14 (a shop's or double door 22 wide),
# a window 16 x 12 with its head 26 above its floor, a ground storey 40 to 44 above a plinth of
# 4 (a shop storey 44 with its fascia), an upper storey 32, a sign's bracket 36 to 44 above
# the ground, an awning's front edge 36 to 40 above it.
#
# Items, by x (y is worked out from the storey unless given):
#   ('door', i, x)           ('win', i, x[, 'up'])     ('shopwin', x, w)
#   ('fascia', pic[, x, w])  ('awning', x, w)          ('lightbox', x, w, pic)
#   ('sign', pic, x)         ('lantern', x[, y])       ('blade', x, y)
#   ('chimney', x)           ('downpipe', x)           ('pipe', x)
#   ('banner', x)            ('sconce', x, y)          ('tie', x)
#   ('ac', x, y)             ('poster', x, y)          ('service', x, y)
#   ('stencil', i, x, w)     ('status', x, y)          ('porch',)
#   ('rose', x)              ('pots', x)               ('bench', x)   ('barrel', x)   ('cactus', x)
LAYOUT = {
    'valley': [
        dict(wall='plaster', roof='tiles', shape='ridge', items=[
            ('chimney', 5), ('door', 0, 10), ('rose', 29), ('win', 0, 38), ('downpipe', 62), ('butt', 56)]),
        dict(wall='drystone', roof='slate', shape='gable', gable='boards_timber', items=[
            ('door', 1, 8), ('sign', 1, 28), ('aboard', 29), ('win', 1, 47), ('bench', 45)]),
        dict(wall='whitewash', roof='thatch', shape='hip', items=[
            ('chimney', 52), ('plaque', 11, 33), ('win', 3, 8), ('logs', 4, 16, 2), ('door', 2, 28), ('rose', 47), ('birdbox', 56, 31), ('win', 4, 53)]),
        dict(wall='boards_lagoon', roof='palm', shape='hip', items=[
            ('sign', 2, 3), ('nets', 4, 48), ('door', 3, 24), ('lantern', 42), ('crates', 41), ('win', 4, 53)]),
    ],
    'cogsworth': [
        dict(wall='brick', roof='copper', shape='ridge', storeys=2, items=[
            ('fascia', 0, 3, 57), ('win', 2, 6), ('door', 1, 26), ('win', 2, 46), ('win', 0, 10, 'up'), ('win', 0, 46, 'up'),
            ('downpipe', 63)]),
        dict(wall='brick_soot', roof='slate', shape='gable', gable='brick_soot', storeys=2, items=[
            ('chimney', 29), ('door', 0, 10), ('win', 0, 46), ('win', 3, 12, 'up'), ('win', 3, 46, 'up'), ('tie', 31),
            ('downpipe', 63)]),
        dict(wall='stock', roof='slate', shape='ridge', storeys=2, items=[
            ('downpipe', 2), ('fascia', 2, 8, 57), ('shopwin', 9, 28), ('door', 2, 44), ('win', 1, 12, 'up'),
            ('win', 1, 46, 'up')]),
        dict(wall='ashlar', roof='glass', shape='ridge', storeys=2, items=[
            ('win', 2, 4, 'up'), ('clock', 28, 33), ('win', 2, 46, 'up'), ('notice', 3, 52), ('fascia', 3, 17, 34), ('door', 3, 23),
            ('lantern', 8), ('lantern', 51), ('crates', 4), ('crates', 50), ('downpipe', 63)]),
    ],
    'sunstone': [
        dict(wall='bleached', roof='corrugated', shape='falsefront', storeys=2, items=[
            ('fascia', 0, 3, 62, 12), ('win', 0, 12, 'up'), ('win', 0, 44, 'up'), ('porch',), ('win', 0, 8), ('door', 0, 24),
            ('win', 0, 50)]),
        dict(wall='adobe', roof='adobe', shape='vigas', ground=40, items=[
            ('door', 1, 10), ('sign', 3, 30), ('cactus', 31), ('win', 1, 48)]),
        dict(wall='boards_berry', roof='corrugated', shape='ridge', ground=45, items=[
            ('fascia', 1), ('shopwin', 6, 24), ('lantern', 33), ('door', 2, 46)]),
        dict(wall='corrugated', roof='shingle', shape='ridge', ground=40, items=[
            ('win', 3, 8), ('barrel', 9), ('door', 3, 28), ('win', 3, 50)]),
    ],
    'hearthold': [
        dict(wall='ashlar', roof='ashlar', shape='crenel', storeys=2, items=[
            ('banner', 6), ('win', 1, 31, 'up'), ('banner', 52), ('sconce', 13, 64), ('door', 0, 23), ('sconce', 50, 64)]),
        dict(wall='rubble', roof='slate', shape='gable', gable='ashlar', storeys=2, items=[
            ('chimney', 29), ('win', 0, 10, 'up'), ('win', 0, 50, 'up'), ('win', 3, 8), ('door', 1, 29), ('sconce', 52, 64)]),
        dict(wall='ashlar', roof='slate', shape='ridge', storeys=2, items=[
            ('chimney', 54), ('door', 2, 12), ('win', 2, 12, 'up'), ('banner', 50), ('win', 3, 44)]),
        dict(wall='rubble', roof='shingle', shape='ridge', ground=40, items=[
            ('chimney', 8), ('win', 3, 10), ('barrel', 11), ('door', 3, 36)]),
    ],
    'neon': [
        dict(wall='concrete', roof='flat', shape='flat', storeys=2, items=[
            ('cables', 20), ('shopwin', 5, 28), ('awning', 3, 32), ('lanterns', 38, 64, 46), ('door', 0, 39), ('win', 0, 8, 'up'),
            ('win', 1, 46, 'up'), ('ac', 26, 28)]),
        dict(wall='tile', roof='flat', shape='flat', storeys=2, items=[
            ('cables', 20), ('shopwin', 5, 28), ('lightbox', 4, 30, 'bowl'), ('door', 1, 39), ('win', 0, 8, 'up'),
            ('win', 2, 46, 'up'), ('ac', 26, 30)]),
        dict(wall='cladding', roof='parapet', shape='flat', storeys=2, items=[
            ('cables', 20), ('blade', 4, 27), ('painted', 16, 26, 24, 18, 'anchor'), ('win', 1, 46, 'up'), ('camera', 3, 57), ('vending', 2),
            ('poster', 14, 48), ('win', 3, 20), ('lantern', 31, 50), ('ac', 48, 45), ('door', 2, 44), ('downpipe', 63)]),
        dict(wall='concrete', roof='flat', shape='flat', storeys=2, items=[
            ('cables', 20), ('shopwin', 5, 22), ('lightbox', 4, 24, 'moon'), ('door', 3, 34), ('blade', 57, 27),
            ('meter', 56, 60), ('win', 3, 8, 'up'), ('win', 0, 36, 'up'), ('ac', 38, 44)]),
    ],
    'halcyon': [
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[
            ('stencil', 0, 4, 28), ('door', 0, 10), ('status', 35, 30), ('keypad', 34, 38), ('warning', 44, 26), ('win', 0, 42),
            ('rail', 34, 58, 54), ('pipe', 62)]),
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[
            ('warning', 5, 25), ('win', 3, 3), ('keypad', 18, 38), ('door', 1, 28), ('status', 52, 28), ('warning', 57, 22),
            ('win', 3, 52), ('rail', 3, 22, 54), ('rail', 52, 66, 54)]),
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[
            ('door', 2, 7), ('keypad', 34, 40), ('status', 35, 33), ('stencil', 1, 42, 22), ('win', 1, 44), ('rail', 36, 64, 56)]),
        dict(wall='bulkhead', roof='hull', shape='conduit', items=[
            ('door', 3, 8), ('status', 34, 34), ('keypad', 32, 40), ('extinguisher', 38, 38), ('win', 2, 44), ('pipe', 61)]),
    ],
    'lumen': [
        dict(wall='berm', roof='regolith', shape='berm', items=[
            ('win', 0, 4), ('door', 0, 30), ('status', 59, 40), ('keypad', 58, 46)]),
        dict(wall='hull_ext', roof='hull', shape='dome', items=[
            ('door', 1, 8), ('stencil', 0, 34, 26), ('status', 36, 40), ('keypad', 34, 46), ('win', 2, 44), ('pipe', 62)]),
        dict(wall='hull_ext', roof='hull', shape='radiator', items=[
            ('stencil', 1, 4, 32), ('win', 1, 3), ('win', 1, 18), ('keypad', 33, 44), ('door', 2, 43)]),
        dict(wall='berm', roof='regolith', shape='berm', items=[
            ('door', 3, 11), ('keypad', 38, 46), ('win', 3, 47), ('status', 63, 44)]),
    ],
}
ROOF_H = {'valley': 28, 'cogsworth': 24, 'sunstone': 24, 'hearthold': 22, 'neon': 18, 'halcyon': 18, 'lumen': 26}
GROUND = {'valley': 40, 'cogsworth': 40, 'sunstone': 36, 'hearthold': 36, 'neon': 40, 'halcyon': 44, 'lumen': 40}
UPPER = 32          # an upper storey (size-guide 3)
W_FRONT = 68
CHIMNEY_ROOM = 12   # headroom over the roof for a stack and its pots
SHAPES_WITH_EAVES = ('ridge', 'hip', 'gable')
NO_GUTTER = ('thatch', 'palm')   # thatch throws its water clear: no gutter, no downpipe
CLASS = {'door': 'opening', 'win': 'opening', 'shopwin': 'opening',
         'fascia': 'band', 'awning': 'band', 'lightbox': 'band', 'porch': 'band',
         'downpipe': 'pipe', 'pipe': 'pipe', 'post': 'pipe',
         'cables': 'band', 'rail': 'band',
         'pots': 'ground', 'bench': 'ground', 'barrel': 'ground', 'cactus': 'ground', 'butt': 'ground', 'logs': 'ground',
         'aboard': 'ground', 'crates': 'ground', 'vending': 'ground', 'bins': 'ground', 'gas': 'ground'}


def gutter_y(lay, rh):
    """Where the gutter hangs: on the fascia board under an eave, or right at the edge of a
    roof that has no fascia (glass, corrugated iron)."""
    return rh - 1 if lay['roof'] in ('glass', 'corrugated') else rh + 1


def geometry(env, v):
    """(rh, storeys, sh, H, yb, floor2) of a front: roof height, storeys, wall height, the
    sprite's height (before chimney room), the top of the plinth, and the upper floor's line."""
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    rh = ROOF_H[env]
    storeys = lay.get('storeys', 1)
    g = lay.get('ground', GROUND[env])
    sh = g + (storeys - 1) * UPPER
    H = rh + sh + 4
    yb = H - 4
    return rh, storeys, sh, H, yb, yb - g


def _feed(cv, x, y0, y1, fam):
    """The cable that feeds a panel or a lamp on a station wall: down from the ceiling's
    conduit to the device, clipped every six pixels, drawn only over the bare wall."""
    for y in range(y0, y1):
        hit = tone_at(cv, x, y)
        if hit and hp.family(hit[0]) in ('panel', 'hull', 'iron'):
            cv.set(x, y, T(fam, 4 if (y - y0) % 6 else 2))
            if (y - y0) % 6 == 0:
                cv.set(x - 1, y, T('iron', 2)); cv.set(x + 1, y, T('iron', 2))


def _shopfront(cv, x, yb, w, env, seed):
    """A shop window: glass 24 tall lit from inside with shelves of goods, a painted frame,
    a stone sill, and a panelled stall riser 8 tall under it (size-guide 3)."""
    top = yb - 32
    interior(cv, x, top, w, 23, seed, 'shop')
    for sy in (top + 7, top + 13, top + 19):
        cv.hline(x + 1, sy, w - 2, T('timber', 2))
        for i, xx in enumerate(range(x + 2, x + w - 2, 4)):
            col = ('lagoon', 'berry', 'brass', 'plaster', 'sky', 'leaf')[(i + sy + seed) % 6]
            cv.vline(xx, sy - 3, 3, T(col, 3)); cv.vline(xx + 1, sy - 3, 3, T(col, 2)); cv.set(xx, sy - 3, T(col, 4))
    trim = paint('trim', 'iron' if env == 'neon' else 'timber')
    frame(cv, x - 1, top - 1, w + 2, 25, trim, 3, t=1)
    part(cv, x - 1, yb - 9, w + 2, 2, 'stone' if env != 'sunstone' else 'bleached', 4, glint=False)
    for (px, py) in rect(x - 1, yb - 7, w + 2, 7):   # the stall riser: a raised panel
        edge = py in (yb - 7, yb - 1) or px in (x - 1, x + w)
        k = 2 if py == yb - 1 or px == x + w else 4 if (py == yb - 6 or px == x) and not edge else 3
        cv.set(px, py, T(trim, k if not edge else 2 if py == yb - 1 else 3))
    return (x - 1, top - 1, x + w + 1, yb)


def _porch(cv, W, y, yb):
    """A boardwalk porch roof of corrugated iron on two posts, its shade on the wall."""
    for (x, yy) in rect(0, y, W, 4):
        j = x % 4
        cv.set(x, yy, T('iron', 5 if yy == y and j == 0 else 4 if j == 0 else 3 if j == 1 else 2) if yy < y + 3 else T('iron', 1))
    overhang(cv, 0, W, y + 4, 4)
    posts = []
    for px in (2, W - 5):
        cylinder(cv, px, y + 4, 3, yb - y - 4, paint('trim', 'bleached'), 3)
        part(cv, px - 1, y + 4, 5, 2, paint('trim', 'bleached'), 4, glint=False)   # the post's cap under the beam
        posts.append((px - 1, y + 4, px + 4, yb))
    return (0, y, W, y + 8), posts


def _rose(cv, x, top, ground, v):
    """A climbing rose from a bed at the foot of the wall, tied up the wall, in flower."""
    part(cv, x - 1, ground - 3, 5, 3, 'earth', 3, glint=False)
    hi = ground
    for i in range(40):
        yy = ground - 3 - int(i * 1.5)
        if yy < top:
            break
        xx = x + int(2 * math.sin(i * 0.7))
        cv.hline(xx, yy, 2, T(sib('leaf', noise2(i, 0, v), 0.3), 3 if i % 3 else 4)); cv.set(xx + 1, yy + 1, T('leaf', 1))
        if i % 4 == 1:
            col = paint('flower', 'berry')
            cv.hline(xx - 1, yy - 1, 2, T(col, 4)); cv.set(xx - 1, yy - 1, T(col, 5))
        hi = yy - 1
    return (x - 1, hi, x + 4, ground)


def _pots(cv, x, ground, seed):
    """Two pots standing on the ground at the foot of the wall, a plant in each, one in flower."""
    pot = paint('pot', 'clay')
    for j in range(2):
        px0 = x + j * 5
        part(cv, px0, ground - 5, 4, 5, pot, 3, glint=False)
        cv.hline(px0 - (1 if j == 0 else 0), ground - 5, 5 if j == 0 else 4, T(pot, 4))
        for (px, py) in disc(px0 + 2, ground - 7, 2.4):
            cv.set(px, py, T(sib('leaf', noise2(px, py, j + seed), 0.35), 4 if px + py < px0 + ground - 5 else 2))
        if j == 0:
            col = paint('flower', 'berry')
            cv.hline(px0 + 1, ground - 9, 2, T(col, 4)); cv.set(px0 + 1, ground - 9, T(col, 5))
    return (x - 1, ground - 10, x + 9, ground)


def _draw_items(cv, env, v, lay, boxes, avoid_only=False):
    """Draw a front's items and record each one's box: (kind, class, (x0, y0, x1, y1))."""
    e = ENV[env]
    rh, storeys, sh, H, yb, floor2 = geometry(env, v)
    W = W_FRONT
    shop = any(it[0] in ('fascia', 'awning', 'lightbox') for it in lay['items'])
    for it in lay['items']:
        k = it[0]
        box = None
        if k == 'door':
            box = _door_into(cv, env, it[1], it[2], yb, seed=v, wall_kind=None if shop else lay['wall'])
        elif k == 'win':
            up = 'up' in it[3:]
            floor = floor2 if up else yb
            spec = dict(e['windows'][it[1] % len(e['windows'])])
            extra = it[-1] if isinstance(it[-1], dict) else {}
            spec.update(extra)
            head = 24 if up else 26   # the head 26 above its floor (24 upstairs, over the string course)
            y = floor - head - (2 if spec.get('h', 16) > 16 else 0)
            box = _window_into(cv, env, it[1], it[2], y, seed=v, wall_kind=lay['wall'], extra=extra)
            if lay['wall'] == 'berm' and not spec.get('round'):   # a window through soil: a hull collar round it
                x0, y0, x1, y1 = box
                for (px, py) in rect(x0 - 3, y0 - 3, x1 - x0 + 6, y1 - y0 + 6):
                    if not (x0 <= px < x1 and y0 <= py < y1):
                        lv = (px - x0) / (x1 - x0 + 6) + (py - y0) / (y1 - y0 + 6)
                        cv.set(px, py, T('hull_cool', 4 if lv < 0.5 else 3 if lv < 1.2 else 2))
                box = (x0 - 3, y0 - 3, x1 + 3, y1 + 3)
        elif k == 'shopwin':
            box = _shopfront(cv, it[1], yb, it[2], env, v)
        elif k == 'fascia':
            x0 = it[2] if len(it) > 2 else 3
            w = it[3] if len(it) > 3 else W - 6
            fy = it[4] if len(it) > 4 else max(rh + 1, yb - 44)
            board = paint('sign', ('berry', 'copper', 'sky', 'dusk')[it[1]] if env == 'cogsworth' else ('berry', 'sky', 'bleached')[it[1] % 3])
            ink = paint('ink', 'brass' if env == 'cogsworth' else 'plaster')
            box = fascia(cv, x0, fy, w, e['signs'][it[1]], board, ink)
        elif k == 'awning':
            box = awning(cv, it[1], H - 48, it[2], paint('cloth', 'berry'), paint('cloth2', 'plaster'), 8)
        elif k == 'lightbox':
            box = lightbox(cv, it[1], yb - 44, it[2], it[3], paint('glow', 'neon_cyan'))
        elif k == 'sign':
            board = paint('sign', ('timber', 'sky', 'berry', 'bleached')[it[1]] if env != 'sunstone' else 'bleached')
            ink = paint('ink', 'brass' if env != 'sunstone' else 'clay')
            box = hanging_sign(cv, it[2], H - 40, e['signs'][it[1]], board, ink)
        elif k == 'lantern':
            y = it[2] if len(it) > 2 else yb - 32
            box = wall_lantern(cv, it[1], y)
        elif k == 'blade':
            box = blade(cv, it[1], it[2], 26, paint('glow', 'neon_cyan' if it[1] > 30 else 'neon_pink'), ('cup', 'moon'))
        elif k == 'chimney':
            continue   # drawn behind the roof by front()
        elif k == 'downpipe':   # from a hopper under the gutter, or under the parapet's outlet on a flat roof
            box = downpipe(cv, it[1], gutter_y(lay, rh) + 2 if lay['shape'] in SHAPES_WITH_EAVES else rh, H)
        elif k == 'pipe':
            box = service_pipe(cv, it[1], rh, yb, 'copper')
        elif k == 'banner':
            y = rh + 8
            banner(cv, it[1], y, 10, 16, paint('cloth', 'dusk'))
            for bx in (it[1] - 1, it[1] + 10):   # the pole's two hooks into the wall
                cv.set(bx, y - 3, T('iron', 3)); cv.set(bx, y - 4, T('iron', 2))
            box = (it[1] - 1, y - 4, it[1] + 11, y + 20)
        elif k == 'sconce':
            box = sconce(cv, it[1], it[2])
        elif k == 'tie':
            box = tie_plate(cv, it[1], floor2 - 3)
        elif k == 'ac':
            box = ac_unit(cv, it[1], it[2])
        elif k == 'poster':
            box = posters(cv, it[1], it[2])
        elif k == 'service':
            box = service_panel(cv, it[1], it[2])
        elif k == 'stencil':
            box = stencil(cv, it[2], rh + 2, it[3], paint('livery', ('berry', 'sky', 'brass')[it[1]]), e['signs'][it[1]])
        elif k == 'status':
            box = status_light(cv, it[1], it[2], paint('glow', 'glowflora' if v % 2 else 'neon_cyan'))
            if env in ('halcyon', 'lumen'):
                _feed(cv, it[1] + 1, rh, it[2] - 1, 'brass')
        elif k == 'porch':
            box, posts = _porch(cv, W, yb - 42, yb)
            for p in posts:
                boxes.append(('post', 'pipe', p))
        elif k == 'rose':
            box = _rose(cv, it[1], yb - 30, H, v)
        elif k == 'pots':
            box = _pots(cv, it[1], H, v)
        elif k == 'bench':
            bench(cv, it[1], H, 'timber', 'timber')
            box = (it[1], H - 12, it[1] + 22, H)
        elif k == 'barrel':
            barrel(cv, it[1], H)
            box = (it[1], H - 12, it[1] + 10, H)
        elif k == 'cactus':
            potted_cactus(cv, it[1], H)
            box = (it[1] - 1, H - 23, it[1] + 11, H)
        elif k == 'butt':
            box = water_butt(cv, it[1], H)
        elif k == 'logs':
            box = log_store(cv, it[1], H, it[2] if len(it) > 2 else 16, it[3] if len(it) > 3 else 3, seed=v)
        elif k == 'basket':
            box = hanging_basket(cv, it[1], it[2], seed=v)
        elif k == 'plaque':
            box = plaque(cv, it[1], it[2])
        elif k == 'creeper':
            box = creeper(cv, it[1], it[2], it[3], H, seed=v + it[1])
        elif k == 'nets':
            box = nets(cv, it[1], it[2], it[3] if len(it) > 3 else 14)
        elif k == 'aboard':
            box = aboard(cv, it[1], H, e['signs'][1] if env == 'valley' else 'cup')
        elif k == 'crates':
            box = produce_crates(cv, it[1], H, ('sky', 'plaster') if env == 'valley' else ('berry', 'leaf', 'brass'), seed=v)
        elif k == 'notice':
            box = notice_case(cv, it[1], it[2])
        elif k == 'birdbox':
            box = bird_box(cv, it[1], it[2])
        elif k == 'clock':
            box = wall_clock(cv, it[1], it[2])
        elif k == 'cables':
            box = cables(cv, 0, W, it[1], seed=v)
        elif k == 'lanterns':
            box = paper_lanterns(cv, it[1], it[2], it[3], seed=v)
        elif k == 'laundry':
            box = laundry(cv, it[1], it[2])
        elif k == 'painted':
            box = painted_sign(cv, it[1], it[2], it[3], it[4], it[5], paint('cloth', 'berry'))
        elif k == 'meter':
            box = meter_box(cv, it[1], it[2])
        elif k == 'vending':
            box = vending(cv, it[1], H)
        elif k == 'bins':
            box = bins(cv, it[1], H)
        elif k == 'camera':
            box = camera(cv, it[1], it[2])
        elif k == 'keypad':
            box = keypad(cv, it[1], it[2], paint('glow', 'neon_cyan'))
            _feed(cv, it[1] + 4, rh, it[2], ('berry', 'sky')[v % 2])
        elif k == 'extinguisher':
            box = extinguisher(cv, it[1], it[2])
        elif k == 'rail':
            box = handrail(cv, it[1], it[2], it[3])
        elif k == 'flood':
            box = floodlight(cv, it[1], it[2])
        elif k == 'gas':
            box = gas_rack(cv, it[1], H)
        elif k == 'warning':
            box = warning(cv, it[1], it[2])
        else:
            raise ValueError(k)
        boxes.append((k, CLASS.get(k, 'fixture'), box))
    return boxes


GLOWS = ('lamp', 'neon_pink', 'neon_cyan', 'glowflora', 'lava')


def _spill(cv, wall_fams, x0, y0, x1, y1, reach=3):
    """Light as a material (art-style.md, Eastward): at night every lit pane, lightbox and
    tube lights the wall round it. Wall pixels within `reach` of a glowing pixel lift a tone,
    and the nearest ring takes the light's own colour at its deepest tone (a lamp's warm
    ochre, a tube's pink or cyan). Only the wall changes; nothing in front of it does."""
    src = {}
    for y in range(y0, y1):
        for x in range(x0, x1):
            hit = tone_at(cv, x, y)
            if hit and hp.family(hit[0]) in GLOWS and hit[1] >= 3:
                src[(x, y)] = hp.family(hit[0])
    best = {}
    for (sx, sy), g in src.items():
        for dy in range(-reach, reach + 1):
            for dx in range(-reach, reach + 1):
                d = max(abs(dx), abs(dy))
                p = (sx + dx, sy + dy)
                if d == 0 or p in src:
                    continue
                if p not in best or d < best[p][0]:
                    best[p] = (d, g)
    for (x, y), (d, g) in best.items():
        hit = tone_at(cv, x, y)
        if not hit or hp.family(hit[0]) not in wall_fams:
            continue
        if d == 1:
            cv.set(x, y, T(g, 1 if g != 'lamp' else 0))
        elif d == 2:
            step(cv, x, y, 1)


def _corners(cv, kind, y0, W, h):
    """How a front's corners are built, which is also where the light turns: an adobe wall's
    rounded corners (lit on the west, in shade on the east), dressed quoins on a stone wall,
    a concrete frame's columns, a bulkhead's structural ribs."""
    if kind == 'adobe':
        for y in range(y0, y0 + h):
            for x, k in ((0, 2), (1, 1), (2, 1), (W - 3, -1), (W - 2, -1), (W - 1, -2)):
                step(cv, x, y, k)
    elif kind in ('ashlar', 'rubble'):   # dressed quoins, long and short, the west ones in the light
        y, i = y0 + 3, 0
        while y < y0 + h - 2:
            ln = 8 if i % 2 == 0 else 5
            hh = min(6, y0 + h - y)
            for (x0_, k0) in ((0, 4), (W - ln, 2)):
                for (x, yy) in rect(x0_, y, ln, hh):
                    inner = x == (x0_ + ln - 1 if x0_ == 0 else x0_)
                    if yy == y + hh - 1 or inner:
                        cv.set(x, yy, T('ashlar_cool', 1))          # the joint round it
                    else:
                        cv.set(x, yy, T('ashlar', k0 + (1 if yy == y and x0_ == 0 else 0)))
            y += 6
            i += 1
    elif kind in ('concrete', 'tile'):
        for y in range(y0, y0 + h):
            for x in range(4):
                cv.set(x, y, T('concrete', 4 if x < 3 else 2))
                cv.set(W - 1 - x, y, T('concrete', 2 if x < 3 else 3))
            if (y - y0) % 16 == 15:   # the pour joints in the columns
                cv.hline(0, y, 4, T('concrete', 3)); cv.hline(W - 4, y, 4, T('concrete', 1))
    elif kind == 'bulkhead':
        for y in range(y0, y0 + h):
            for x in range(3):
                cv.set(x, y, T('panel', 4 if x < 2 else 3))
                cv.set(W - 1 - x, y, T('panel', 1 if x < 2 else 2))
            if (y - y0) % 8 == 4:
                cv.set(1, y, T('hull', 5)); cv.set(W - 2, y, T('hull', 3))


def front(env, v, cw=None):
    """A whole building front in the environment, 68 px wide: roof or top, one or two
    storeys of its wall, its door, windows, signs and dressing, painted in a colourway (its
    own default when cw is None); built only from this kit's pieces. The canvas carries
    `boxes` (each item's box) and `wall_box` (the wall below the roof, for the detail bar)."""
    global PAINT
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    rh, storeys, sh, H, yb, floor2 = geometry(env, v)
    W = W_FRONT
    name, roles = colourway(env, DEFAULT_CW[env][v % 4] if cw is None else cw)
    chim = [it for it in lay['items'] if it[0] == 'chimney']
    top = CHIMNEY_ROOM if chim else 0
    saved, PAINT = PAINT, dict(roles)
    try:
        dry = Canvas(W, H)   # a dry run finds where the items go, so the wall keeps its bays clear of them
        boxes = _draw_items(dry, env, v, lay, [])
        body = Canvas(W, H)
        wall(body, 0, rh, W, sh, lay['wall'], seed=v * 13 + 1,
             avoid=[b for (_k, c, b) in boxes if c in ('opening', 'fixture', 'pipe')])
        _corners(body, lay['wall'], rh, W, sh)
        has_band = any(it[0] in ('fascia',) for it in lay['items'])
        if storeys == 2 and env in ('cogsworth', 'hearthold', 'neon') and not has_band:   # a string course at the upper floor
            part(body, 0, floor2 - 2, W, 3, 'ashlar' if env != 'neon' else 'concrete', 4, glint=False)
            overhang(body, 0, W, floor2 + 1, 1)
        if env in ('valley', 'hearthold'):
            plinth(body, 0, H - 4, W, 4, 'stone', v)
        elif env == 'cogsworth':   # a plinth of dark engineering brick
            for (x, y) in rect(0, H - 4, W, 4):
                c, r = divmod(x + (2 if y % 2 else 0), 4)
                body.set(x, y, T(sib('iron', noise2(c, y // 2, v), 0.3), 1 if (r == 3 or y == H - 1) else 4 if y == H - 4 else 3))
        elif env == 'sunstone':    # the boardwalk the front stands on
            for x in range(W):
                for y in range(H - 4, H):
                    body.set(x, y, T(sib('timber', noise2(x // 8, 0, v), 0.3), 4 if y == H - 4 else 3 if y < H - 1 else 1))
                if x % 8 == 0:
                    body.set(x, H - 3, T('timber', 1))
        elif env == 'lumen':
            plinth(body, 0, H - 4, W, 4, 'regolith', v)
            if lay['wall'] in ('hull', 'hull_ext', 'panel'):   # moon dust kicked up onto the lower plates
                for (x, y) in rect(0, H - 14, W, 10):
                    hit = tone_at(body, x, y)
                    if smooth_noise(x, y, 3, v + 40) > 0.5 + 0.04 * (H - 4 - y) and hit and hp.family(hit[0]) in ('hull', 'panel', 'iron'):
                        body.set(x, y, T(sib('regolith', noise2(x, y, v), 0.3), 4 if y < H - 9 else 3))
        else:
            part(body, 0, H - 4, W, 4, 'concrete' if env == 'neon' else 'panel', 3)
        roof_mass(body, 0, 0, W, rh, lay['roof'], lay['shape'], seed=v * 7 + 2, gable_wall=lay.get('gable', lay['wall']))
        downs = [it for it in lay['items'] if it[0] == 'downpipe']
        if downs and lay['shape'] in SHAPES_WITH_EAVES:
            gutter(body, 0, W, gutter_y(lay, rh))
        boxes = _draw_items(body, env, v, lay, [])
        if env == 'neon':   # night: lit glass and signs throw their light on the wall round them
            _spill(body, ('concrete', 'asphalt', 'iron', 'lagoon', 'slate'), 0, rh, W, H - 4)
        cv = Canvas(W, H + top)
        for it in chim:   # the stack behind the roof: the roof hides its foot
            chimney(cv, it[1], 3, 16, 'brick' if env == 'cogsworth' else 'stone')
        for y in range(H):
            for x in range(W):
                c = body.get(x, y)
                if c[3]:
                    cv.set(x, y + top, c)
        for it in chim:   # its shadow on the roof to the east, just under its foot
            for yy in range(top, top + 4):
                for xx in (it[1] + 9, it[1] + 10):
                    step(cv, xx, yy, -1)
    finally:
        PAINT = saved
    out = Canvas(W + 2, H + top + 2)
    for y in range(H + top):
        for x in range(W):
            c = cv.get(x, y)
            if c[3]:
                out.set(x + 1, y + 1, c)
    outline(out)
    out.boxes = boxes                                          # in the building's own coordinates
    out.chimneys = [(it[1] - 1, 3 - top, it[1] + 10, 19 - top) for it in chim]
    out.wall_box = (2, rh + top + 2, W, H + top - 4)
    out.top, out.ground = top, H + top
    out.colourway = name
    return out


# --- the logic check -----------------------------------------------------------------------
# Matt, 20 Oct 12:09: "review the repeated buildings for logic issues and make sure there are
# not illogical parts". Each rule is one a builder or a resident would apply; every front in
# every colourway must pass all of them (`python3 scripts/art/house_kits.py --check`).
def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def logic(env, v, cv=None) -> list:
    """The faults of one front, as sentences (empty when it makes sense)."""
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    rh, storeys, sh, H, yb, floor2 = geometry(env, v)
    W = W_FRONT
    cv = cv or front(env, v)
    boxes = cv.boxes
    out = []
    if lay['wall'] not in ALLOWED_WALLS[env]:
        out.append(f"wall '{lay['wall']}' is not a material of {env}")
    for (k, c, b) in boxes:   # nothing cut off at the front's edge
        if c != 'band' and k != 'post' and (b[0] < 1 or b[2] > W - 1):
            out.append(f'{k} at x {b[0]}..{b[2]} is cut by the edge of the front')
        if c == 'ground' and b[3] != H:
            out.append(f'{k} does not stand on the ground')
        if k == 'door' and (b[0] < 3 or b[2] > W - 3):
            out.append(f'door at x {b[0]}..{b[2]} is pushed to the edge')
        if b[1] < rh - (6 if k in ('downpipe',) else 0) and k not in ('fascia',) and lay['shape'] != 'falsefront':
            out.append(f'{k} reaches up into the roof (y {b[1]} < {rh})')
    for i, (k1, c1, b1) in enumerate(boxes):
        for (k2, c2, b2) in boxes[i + 1:]:
            if not _overlap(b1, b2):
                continue
            pair = {c1, c2}
            if pair <= {'band', 'pipe'} and 'post' not in (k1, k2):
                continue   # a downpipe may pass a band
            if pair == {'band', 'pipe'} and 'post' in (k1, k2):
                continue   # porch posts carry the porch
            if {k1, k2} == {'butt', 'downpipe'}:
                continue   # the downpipe runs into the butt
            out.append(f'{k1} {b1} overlaps {k2} {b2}')
    doors = [b for (k, c, b) in boxes if k == 'door']
    for (k, c, b) in boxes:   # nothing stands in a doorway
        if c == 'ground' and any(b[0] < d[2] and d[0] < b[2] for d in doors):
            out.append(f'{k} stands in front of a door')
    for (k, c, b) in boxes:   # a fascia, awning or lightbox is over a shop or a door, in the same storey
        if k in ('fascia', 'awning', 'lightbox'):
            under = [ob for (ok, oc, ob) in boxes if oc == 'opening' and ob[0] < b[2] and b[0] < ob[2] and 0 <= ob[1] - b[3] <= 12]
            if not under and lay['shape'] != 'falsefront':
                out.append(f'{k} has no shopfront or door under it')
    downs = [it for it in lay['items'] if it[0] == 'downpipe']
    if downs and lay['roof'] in NO_GUTTER:
        out.append('a downpipe under a thatched eave, which has no gutter')
    for it in lay['items']:
        if it[0] == 'chimney':
            if env not in ('valley', 'cogsworth', 'hearthold') or lay['shape'] not in SHAPES_WITH_EAVES:
                out.append('a chimney where there is no hearth (a flat, false or vacuum top)')
            if it[1] < 1 or it[1] + 10 > W - 1:
                out.append('a chimney cut by the edge')
    pipes = [b for (k, c, b) in boxes if k == 'downpipe']
    for (k, c, b) in boxes:
        if k == 'butt' and not any(p[0] < b[2] and b[0] < p[2] for p in pipes):
            out.append('a water butt with no downpipe running into it')
        if k == 'logs' and not any(it[0] == 'chimney' for it in lay['items']):
            out.append('firewood stacked at a house with no chimney')
    if env in ('halcyon', 'lumen') and not any(k == 'keypad' for (k, c, b) in boxes):
        out.append('a hatch with no control panel beside it')
    signs = [b for (k, c, b) in boxes if k == 'sign']
    for b in signs:   # a hanging sign's arm is above a head and below the eaves
        arm = b[1] + 2
        if not (36 <= H - arm <= 44):
            out.append(f'sign bracket {H - arm} above the ground (36 to 44)')
    return out


# --- streets and the colourway picker ------------------------------------------------------
def street(env, n=7, seed=0) -> list:
    """A street of n fronts as they would stand, [(v, colourway index)], picked by seed:
    no two neighbours share a front variant, a door colour or a cloth colour, and a variant
    that repeats along the street never repeats its colourway."""
    nv = len(LAYOUT[env])
    ways = COLOURWAYS[env]
    seed = seed * 7 + ENVS.index(env) * 131   # each setting's streets run differently
    order = []
    for lap in range(n // nv + 2):   # each lap of the street takes the variants in a new order,
        p = sorted(range(nv), key=lambda i: noise2(seed + 97 * lap, i, 71))
        if order and p[0] == order[-1]:   # never the same front either side of a lap's end
            p = p[1:] + p[:1]
        order += p
    out, used = [], set()
    for i in range(n):
        v = order[i]
        cands = sorted(range(len(ways)), key=lambda c: noise2(seed + i, c, 73))
        pick = None
        for c in cands:
            if (v, c) in used:
                continue
            if out and not _neighbours_differ(env, out[-1], (v, c)):
                continue
            pick = c
            break
        if pick is None:
            raise ValueError(f'no colourway left for {env} front {v} at {i}')
        used.add((v, pick))
        out.append((v, pick))
    return out


def door_cloth(env, v, c) -> tuple:
    """The door colour and the cloth colour a front shows in a colourway (a natural door
    keeps its own timber)."""
    lay = LAYOUT[env][v % len(LAYOUT[env])]
    roles = colourway(env, c)[1]
    d = next((it for it in lay['items'] if it[0] == 'door'), None)
    spec = ENV[env]['doors'][d[1] % len(ENV[env]['doors'])] if d else None
    door_c = (roles.get(spec.get('role', 'door'), spec['fam']) if spec.get('paint', True) else spec['fam']) if spec else None
    return door_c, roles.get('cloth')


def _neighbours_differ(env, a, b) -> bool:
    if a[0] == b[0]:
        return False
    da, ca = door_cloth(env, *a)
    db, cb = door_cloth(env, *b)
    return (da is None or da != db) and ca != cb


def check_street(env, st) -> list:
    out = []
    for i in range(1, len(st)):
        if st[i][0] == st[i - 1][0]:
            out.append(f'{env} street: front {st[i][0]} stands beside itself at {i}')
        da, ca = door_cloth(env, *st[i - 1])
        db, cb = door_cloth(env, *st[i])
        if da == db:
            out.append(f'{env} street: neighbours {i - 1} and {i} share the door colour {da}')
        if ca == cb:
            out.append(f'{env} street: neighbours {i - 1} and {i} share the cloth colour {ca}')
    if len(set(st)) != len(st):
        out.append(f'{env} street: a front repeats in the same colourway')
    return out


# --- today's equivalents -------------------------------------------------------------------
TODAY = {
    'valley': [('harbour_props', 'cottage'), ('world_props', 'house_red'), ('isle_props', 'boathouse')],
    'cogsworth': [('steampunk_props', 'workshop'), ('steampunk_props', 'house_slate'), ('steampunk_props', 'shop_ashlar')],
    'sunstone': [('western_props', 'saloon'), ('western_props', 'store'), ('western_props', 'water_jar')],
    'hearthold': [('castle_props', 'gatehouse'), ('castle_props', 'postern'), ('castle_props', 'weapon_rack')],
    'neon': [('cyber_props', 'noodle_stall'), ('cyber_props', 'vending_machine'), ('cyber_props', 'city_food_kiosk')],
    'halcyon': [('space_props', 'airlock'), ('space_props', 'lockers'), ('space_props', 'console')],
    'lumen': [('space_props', 'airlock_module'), ('space_props', 'glass_dome'), ('space_props', 'old_lander')],
}


def today(env):
    import importlib
    import style
    out = []
    for mod, key in TODAY[env]:
        sp = importlib.import_module(mod).props()[key]
        img = style.finalize(sp, name=key).img
        if img.height > 110:   # tall buildings: their lower part, where the pieces are
            img = img.crop((0, img.height - 110, img.width, img.height))
        if img.width > 110:
            img = img.crop(((img.width - 110) // 2, 0, (img.width - 110) // 2 + 110, img.height))
        out.append((key, img))
    return out


# --- the kit sheet -------------------------------------------------------------------------
BAR_KIND_FRONT = {('lumen', 0): 'ground', ('lumen', 3): 'ground'}   # a heap of moon soil is ground
BAR_KIND = {'valley': 'facade', 'cogsworth': 'facade', 'sunstone': 'wood-front', 'hearthold': 'stone-wall',
            'neon': 'facade', 'halcyon': 'machinery', 'lumen': 'machinery'}


def sheet(env, out_dir, scale=3):
    from style_sheet import _font
    bg, fg = (52, 48, 58, 255), (236, 230, 214, 255)
    rows = [('today (main)', [img for _k, img in today(env)])]
    for piece in PIECES:
        fn = globals()[piece]
        rows.append((piece + 's', [fn(env, v).img for v in range(variants(env, piece))]))
    pad, lab = 10 * scale, 22
    width = max(sum(i.width * scale + pad for i in imgs) + pad for _t, imgs in rows)
    width = max(width, 900)
    height = 60 + sum(max(i.height for i in imgs) * scale + lab + pad for _t, imgs in rows)
    im = Image.new('RGBA', (width, height), bg)
    d = ImageDraw.Draw(im)
    d.text((pad, 14), f'{TITLES[env]}: the house kit (3x; an adult is 25 px)', fill=fg, font=_font(24))
    y = 60
    for title, imgs in rows:
        d.text((pad, y), title, fill=fg, font=_font(15))
        y += lab
        x = pad
        hmax = max(i.height for i in imgs) * scale
        for i in imgs:
            big = i.resize((i.width * scale, i.height * scale), Image.NEAREST)
            im.alpha_composite(big, (x, y + hmax - big.height))
            x += big.width + pad
        y += hmax + pad
    path = os.path.join(out_dir, f'kit-{env}.png')
    im.save(path)
    return path


def report(env, every=True) -> int:
    """The style lint, the detail bar and the logic check for every front of an environment in
    every colourway. Returns the number of lines that fail."""
    import style_lint
    try:
        import detail_bar
    except ImportError:
        detail_bar = None
    print(f'{env}:')
    bad = 0
    for v in range(variants(env, 'front')):
        for c in (range(len(COLOURWAYS[env])) if every else [None]):
            cv = front(env, v, c)
            m = style_lint.measure(cv.img)
            miss = style_lint.misses(m)
            if detail_bar:
                kind = BAR_KIND_FRONT.get((env, v), BAR_KIND[env])
                box = tuple(x + 1 for x in cv.wall_box)   # the wall below the roof, in the outlined sprite
                ok, _c, bl = detail_bar.check_image(cv.img.convert('RGB'), box, kind)
                bar = f'bar {kind} {"PASS" if ok else "FAIL"} ' + '; '.join(t for t in bl if 'LOW' in t or 'NOISY' in t)
            else:
                ok, bar = True, 'bar skipped (detail_bar.py not here)'
            faults = logic(env, v, cv)
            bad += (not ok) + bool(miss) + bool(faults)
            print(f'  front {v} {cv.colourway:15s} {m["colours"]:3d} colours, {100 * m["on_house"]:.0f}% house, '
                  f'W-E {m["west_east"]:+5.1f}, lone {100 * m["isolated"]:4.1f}%  lint {" ".join(miss) or "ok":8s} '
                  f'logic {"ok" if not faults else "; ".join(faults)}  {bar}')
    worst = []
    for v in range(variants(env, 'prop')):
        m = style_lint.measure(prop(env, v).img)
        if style_lint.misses(m):
            worst.append(f'prop {v}: {" ".join(style_lint.misses(m))}')
    if worst:
        print('  ' + '; '.join(worst))
    return bad


def check() -> int:
    """The logic check on every front in every colourway, and the colourway picker on
    streets of 4 to 9 fronts for 40 seeds in every environment. Returns the fault count."""
    faults = 0
    for env in ENVS:
        for v in range(len(LAYOUT[env])):
            for c in range(len(COLOURWAYS[env])):
                for f in logic(env, v, front(env, v, c)):
                    print(f'{env} front {v} ({colourway(env, c)[0]}): {f}')
                    faults += 1
        if len(COLOURWAYS[env]) < 3:
            print(f'{env}: fewer than three colourways')
            faults += 1
        for seed in range(40):
            for n in range(4, 10):
                for f in check_street(env, street(env, n, seed)):
                    print(f'seed {seed} n {n}: {f}')
                    faults += 1
    print(f'logic and colourway check: {faults} faults')
    return faults


def _label(im, x, y, text, size=14):
    from style_sheet import _font
    ImageDraw.Draw(im).text((x, y), text, fill=(236, 230, 214, 255), font=_font(size))


def fronts_sheet(path, scale=2):
    """Every front of every environment in its own colourway, a row per environment."""
    rows = [(env, [front(env, v) for v in range(len(LAYOUT[env]))]) for env in ENVS]
    pad, lab = 8 * scale, 26
    width = max(sum(c.img.width * scale + pad for c in cvs) for _e, cvs in rows) + pad
    height = 50 + sum(max(c.img.height for c in cvs) * scale + lab + pad for _e, cvs in rows)
    im = Image.new('RGBA', (width, height), (52, 48, 58, 255))
    _label(im, pad, 12, 'House kits v2: every front in its own colourway (2x; an adult is 25 px)', 20)
    y = 50
    for env, cvs in rows:
        _label(im, pad, y, f'{TITLES[env]}  ({", ".join(c.colourway for c in cvs)})')
        y += lab
        x, hmax = pad, max(c.img.height for c in cvs) * scale
        for c in cvs:
            big = c.img.resize((c.img.width * scale, c.img.height * scale), Image.NEAREST)
            im.alpha_composite(big, (x, y + hmax - big.height))
            x += big.width + pad
        y += hmax + pad
    im.save(path)
    return path


def street_strip(env, n=7, seed=0):
    """One street of n fronts standing shoulder to shoulder on one ground line."""
    st = street(env, n, seed)
    cvs = [front(env, v, c) for (v, c) in st]
    w = sum(c.img.width - 2 for c in cvs) + 2
    h = max(c.img.height for c in cvs)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for c in cvs:
        im.alpha_composite(c.img, (x, h - c.img.height))
        x += c.img.width - 2
    return st, cvs, im


def streets_sheet(path, scale=2, n=7, seed=3):
    strips = [(env,) + street_strip(env, n, seed) for env in ENVS]
    pad, lab = 8 * scale, 26
    width = max(im.width * scale for _e, _s, _c, im in strips) + 2 * pad
    height = 50 + sum(im.height * scale + lab + pad for _e, _s, _c, im in strips)
    out = Image.new('RGBA', (width, height), (52, 48, 58, 255))
    _label(out, pad, 12, f'House kits v2: one street per setting, {n} fronts, repeats in other colourways (2x)', 20)
    y = 50
    for env, st, cvs, im in strips:
        _label(out, pad, y, f'{TITLES[env]}: ' + ', '.join(f'{v}/{c.colourway}' for (v, _c), c in zip(st, cvs)))
        y += lab
        out.alpha_composite(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (pad, y))
        y += im.height * scale + pad
    out.save(path)
    return path


def main(argv) -> int:
    import tempfile
    if '--check' in argv:
        return 1 if check() else 0
    out = argv[0] if argv and not argv[0].startswith('-') else os.path.join(tempfile.gettempdir(), 'napattack-house-kits')
    os.makedirs(out, exist_ok=True)
    envs = [a for a in argv[1:] if a in ENVS] or list(ENVS)
    for env in envs:
        print('wrote', sheet(env, out))
        report(env)
    print('wrote', fronts_sheet(os.path.join(out, 'fronts.png')))
    print('wrote', streets_sheet(os.path.join(out, 'streets.png')))
    check()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
