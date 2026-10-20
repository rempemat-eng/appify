"""NapAttack's house palette (docs/vision/house-style.md): one rule makes every ramp.

Every material ramp in the game comes from one body colour and one rule, so a brick in
Cogsworth, a board in Dust Gulch and a panel on Halcyon shade the same way:

- six tones, 0 (deepest shade) to 5 (highlight), with the body at 3;
- the shade tones walk the hue towards DUSK, the game's violet (the colour of sleep), and
  the light tones walk it towards LAMP, a warm candle yellow: warm light, cool shade;
- lightness is spaced evenly in OKLab between a floor and a ceiling, so every ramp has the
  same contrast whatever its body;
- chroma eases off at both ends (deep shade and highlights are calmer than the body);
- an edge tone, the outline for that material, is its deepest tone pulled towards INK.

Glow ramps (lamplight, neon, lava, glowflora) are light sources, not lit surfaces: they run
from a deep, saturated colour up to a near-white core, keep their hue, and get no edge.

The palette lives in art/house-palette.json, written by this file:
    python3 scripts/art/house_palette.py           # check the JSON matches the rule
    python3 scripts/art/house_palette.py --write   # rewrite it from BASES
    python3 scripts/art/house_palette.py --preview-materials OUT.json
        # today's materials.json recoloured to the house palette, for a trial render
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JSON = os.path.join(HERE, '..', '..', 'art', 'house-palette.json')

# --- the anchors ------------------------------------------------------------------------
DUSK_HUE = 298.0     # OKLCH hue that shade leans to: the nap violet
LAMP_HUE = 82.0      # OKLCH hue that light leans to: candle yellow
INK = '#211A22'      # the deepest outline, a warm violet near-black
SHADE_HUE_STEP = (10.0, 6.0, 3.0)    # degrees the hue turns towards DUSK, tones 0, 1, 2
LIGHT_HUE_STEP = (5.0, 10.0)         # degrees it turns towards LAMP, tones 4, 5
SHADE_TINT = (0.030, 0.021, 0.011)   # OKLab chroma added at DUSK_HUE, tones 0..2 (greys go violet)
LIGHT_TINT = (0.012, 0.024)          # added at LAMP_HUE, tones 4..5 (greys go warm)
SHADE_DL = (-0.33, -0.215, -0.105)     # OKLab lightness from the body, tones 0..2
LIGHT_DL = (0.085, 0.16)             # tones 4..5
L_FLOOR, L_CEIL = 0.21, 0.965        # offsets shrink to fit between these
SHADE_C = (0.85, 0.95, 1.0)          # chroma relative to the body, tones 0..2
LIGHT_C = (0.92, 0.70)               # tones 4..5
SIBLING_TURN, SIBLING_DL, SIBLING_C = 9.0, (0.025, -0.03), (1.05, 0.92)   # warm, cool
EDGE_TO_INK = 0.62                   # how far the edge tone is pulled from tone 0 to INK

# --- the master palette: one body colour per ramp ---------------------------------------
# 'core' ramps are shared by every region. 'accent' ramps belong to the settings named and
# are made by the same rule; a region uses the core plus at most three accents of its own.
# 'glow' ramps are light sources.
BASES = {
    # core: the cosy valley's materials, and what every other place is also built of
    'grass':   ('core', '#86A458'),
    'leaf':    ('core', '#5C8A4C'),
    'earth':   ('core', '#7A6250'),   # soil, banks, faces (olive brown with violet darks)
    'path':    ('core', '#A87C60'),   # trodden earth (the reference's reddish dirt ring)
    'sand':    ('core', '#D4B488'),
    'water':   ('core', '#4C86B4'),
    'stone':   ('core', '#8E8782'),   # warm grey: dry stone, castle, footings, flags
    'slate':   ('core', '#6E7890'),   # cool blue grey: slates, cut stone in shade, steel
    'timber':  ('core', '#8E6242'),
    'plaster': ('core', '#E0CCA6'),   # lime plaster, cream paint, canvas, paper
    'clay':    ('core', '#AE5A42'),   # brick, terracotta, red roof tiles
    'iron':    ('core', '#565868'),   # cast and wrought iron, dark metal
    'brass':   ('core', '#C2903C'),
    'berry':   ('core', '#B2465A'),   # painted red: doors, flags, cloth, fruit
    'dusk':    ('core', '#7262A4'),   # the nap violet: the game's own accent, shutters, sleep
    'sky':     ('core', '#5E8EC0'),   # painted blue: doors, shutters, cloth
    'snow':    ('core', '#D6DEEA'),
    # accents, by setting
    'lagoon':    ('accent:isles', '#3CA6A4'),
    'basalt':    ('accent:isles,fire', '#4E4652'),
    'copper':    ('accent:cogsworth', '#4E9A84'),   # verdigris roofs
    'soot':      ('accent:cogsworth', '#4A4448'),   # sooted brick and iron
    'bleached':  ('accent:reach', '#B4987C'),       # sun-bleached boards
    'adobe':     ('accent:reach', '#C08A5E'),
    'cactus':    ('accent:reach', '#5C8C58'),
    'ashlar':    ('accent:castle', '#A69C8E'),      # dressed stone, a step warmer than stone
    'ash':       ('accent:fire', '#7C746E'),
    'concrete':  ('accent:neon', '#6C6878'),
    'asphalt':   ('accent:neon', '#3E3C50'),        # the wet street and the night walls
    'hull':      ('accent:station', '#C4C8D2'),     # white pressure shells
    'panel':     ('accent:station', '#7A8296'),     # inner deck and bulkhead metal
    'regolith':  ('accent:moon', '#8E877E'),        # grey to brown-grey (Matt, 20 Oct)
    'void':      ('accent:station,moon', '#2A2C44'),  # space seen through glass, the sky past the moon
    # glows: light sources, a deep colour up to a near-white core
    'lamp':      ('glow', '#F0B050'),
    'neon_pink': ('glow', '#F04A9E'),
    'neon_cyan': ('glow', '#2CC0D8'),
    'lava':      ('glow', '#F27222'),
    'glowflora': ('glow', '#36D0B0'),
}

# A cast shadow steps the ground this many tones down its own ramp, so it stays on the
# palette and turns violet by the ramps' own lean. A setting may only change the step
# (hard black shadows on the airless moon, softer ones at night).
SHADOW_STEPS = {'default': 2, 'desert': 2, 'night': 1, 'moon': 3}


# --- colour maths (OKLab, Bjorn Ottosson) --------------------------------------------------
def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_rgb(h: str) -> tuple:
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c) -> str:
    return '#%02X%02X%02X' % tuple(max(0, min(255, round(v))) for v in c[:3])


def to_oklab(c) -> tuple:
    r, g, b = (_lin(v / 255) for v in c[:3])
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _oklab_lin(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def from_oklch(L: float, C: float, h: float) -> tuple:
    """sRGB for an OKLCH colour, chroma reduced until it fits the gamut."""
    for _ in range(40):
        a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
        lin = _oklab_lin(L, a, b)
        if all(-1e-4 <= v <= 1 + 1e-4 for v in lin):
            return tuple(_gam(max(0.0, min(1.0, v))) * 255 for v in lin)
        C *= 0.94
    return tuple(_gam(max(0.0, min(1.0, v))) * 255 for v in _oklab_lin(L, 0, 0))


def oklch(c) -> tuple:
    L, a, b = to_oklab(c)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def delta(c1, c2) -> float:
    """Perceptual distance (OKLab Euclidean; 0.02 is about one just-visible step)."""
    p, q = to_oklab(c1), to_oklab(c2)
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(p, q)))


def _toward(h: float, target: float, deg: float) -> float:
    d = (target - h + 540) % 360 - 180
    return (h + math.copysign(min(abs(d), deg), d)) % 360


# --- the rule ------------------------------------------------------------------------------
def _tone(L, C, h, dl, cf, turn, tint, tint_hue):
    a = C * cf * math.cos(math.radians(turn)) + tint * math.cos(math.radians(tint_hue))
    b = C * cf * math.sin(math.radians(turn)) + tint * math.sin(math.radians(tint_hue))
    return rgb_hex(from_oklch(L + dl, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360))


def ramp(body: str) -> list:
    """Six tones, 0..5, from one body colour (tone 3): the same lightness steps for every
    material (squeezed only where they would pass the floor or ceiling), the hue turning a
    little towards DUSK in the shade and LAMP in the light, plus a small fixed tint of each,
    so even a grey has violet shade and warm highlights."""
    L, C, h = oklch(hex_rgb(body))
    ks = min(1.0, (L - L_FLOOR) / -SHADE_DL[0])
    kl = min(1.0, (L_CEIL - L) / LIGHT_DL[1])
    out = [_tone(L, C, h, SHADE_DL[i] * ks, SHADE_C[i], _toward(h, DUSK_HUE, SHADE_HUE_STEP[i]),
                 SHADE_TINT[i], DUSK_HUE) for i in range(3)]
    out.append(rgb_hex(hex_rgb(body)))
    out += [_tone(L, C, h, LIGHT_DL[i] * kl, LIGHT_C[i], _toward(h, LAMP_HUE, LIGHT_HUE_STEP[i]),
                  LIGHT_TINT[i], LAMP_HUE) for i in range(2)]
    return out


def edge(r: list) -> str:
    """The outline tone of a ramp: its deepest tone pulled towards INK."""
    a, b = to_oklab(hex_rgb(r[0])), to_oklab(hex_rgb(INK))
    L, A, B = (x + (y - x) * EDGE_TO_INK for x, y in zip(a, b))
    lin = _oklab_lin(L, A, B)
    return rgb_hex(tuple(_gam(max(0.0, min(1.0, v))) * 255 for v in lin))


def glow_ramp(body: str) -> list:
    """A light source: deep and saturated at 0, the body at 3, a near-white core at 5."""
    L, C, h = oklch(hex_rgb(body))
    Ls = (max(0.28, L - 0.38), max(0.38, L - 0.24), max(0.5, L - 0.11), L,
          L + (0.97 - L) * 0.5, 0.975)
    Cs = (C * 0.8, C * 0.95, C, C, C * 0.6, C * 0.22)
    hs = (h, h, h, h, _toward(h, LAMP_HUE, 6), _toward(h, LAMP_HUE, 10))
    out = [rgb_hex(from_oklch(Ls[i], Cs[i], hs[i])) for i in range(6)]
    out[3] = rgb_hex(hex_rgb(body))
    return out


def siblings(body: str) -> tuple:
    """The warm and cool siblings of a body colour: the hue turned a few degrees towards
    LAMP (a little lighter) or DUSK (a little darker). A surface built of many parts (boards,
    stones, plates, clods) gives each part one of the three, so it has Eastward's many tones
    while every colour stays on the palette."""
    L, C, h = oklch(hex_rgb(body))
    warm = rgb_hex(from_oklch(L + SIBLING_DL[0], C * SIBLING_C[0] + 0.006, _toward(h, LAMP_HUE, SIBLING_TURN)))
    cool = rgb_hex(from_oklch(L + SIBLING_DL[1], C * SIBLING_C[1] + 0.004, _toward(h, DUSK_HUE, SIBLING_TURN)))
    return warm, cool


def build() -> dict:
    ramps, edges, kinds = {}, {}, {}
    for name, (kind, body) in BASES.items():
        if kind == 'glow':
            ramps[name] = glow_ramp(body)
            kinds[name] = kind
            continue
        ramps[name] = ramp(body)
        edges[name] = edge(ramps[name])
        kinds[name] = kind
        warm, cool = siblings(body)
        for tag, b in (('warm', warm), ('cool', cool)):
            ramps[f'{name}_{tag}'] = ramp(b)
            kinds[f'{name}_{tag}'] = f'sibling:{name}'
    return {'ramps': ramps, 'edges': edges, 'kinds': kinds}


def family(name: str) -> str:
    """The parent ramp of a sibling ('timber_warm' -> 'timber')."""
    for tag in ('_warm', '_cool'):
        if name.endswith(tag):
            return name[:-len(tag)]
    return name


# --- the palette as data, for the generators and the lint ----------------------------------
def load() -> dict:
    with open(JSON) as f:
        return json.load(f)


def colours(pal: dict | None = None) -> dict:
    """Every palette colour as rgb -> (ramp, tone); edges are tone -1."""
    pal = pal or load()
    out = {}
    for name, r in pal['ramps'].items():
        for i, c in enumerate(r):
            out.setdefault(hex_rgb(c), (name, i))
    for name, c in pal['edges'].items():
        out.setdefault(hex_rgb(c), (name, -1))
    out.setdefault(hex_rgb(pal['ink']), ('ink', -1))
    return out


# Today's ramps (art/materials.json) that do not simply go to their nearest house ramp.
MAP_OVERRIDE = {
    'nap': 'dusk', 'roof': 'clay', 'brick': 'clay', 'red': 'berry', 'cream': 'plaster',
    'gold': 'brass', 'night': 'asphalt', 'tar': 'asphalt', 'neon_amber': 'lamp',
    'lamplight': 'lamp', 'sailcloth': 'plaster', 'rope': 'bleached', 'desert': 'sand',
    'soil': 'earth', 'wood': 'timber', 'hull': 'panel',
}


def mapping(pal: dict | None = None) -> dict:
    """For each of today's ramps: the house ramp it becomes, which house tone each of its
    tones becomes (nearest in lightness, in order), and how far it drifts (mean OKLab
    distance of its tones from what they become; above 0.06 the region will look changed)."""
    pal = pal or build()
    with open(os.path.join(HERE, '..', '..', 'art', 'materials.json')) as f:
        mats = json.load(f)['materials']
    out = {}
    for old, tones in mats.items():
        def cost(name):
            r = pal['ramps'][name]
            return sum(min(delta(hex_rgb(t), hex_rgb(c)) for c in r) for t in tones) / len(tones)
        parents = [n for n in pal['ramps'] if not pal['kinds'][n].startswith('sibling')]
        name = MAP_OVERRIDE.get(old) or (old if old in pal['ramps'] else min(parents, key=cost))
        r = pal['ramps'][name]
        # tones in order: each old tone to the nearest house tone by lightness, never going back
        idx, last = [], 0
        Ls = [oklch(hex_rgb(c))[0] for c in r]
        for t in tones:
            L = oklch(hex_rgb(t))[0]
            best = min(range(last, len(r)), key=lambda i: abs(Ls[i] - L))
            idx.append(best)
            last = best
        drift = sum(delta(hex_rgb(t), hex_rgb(r[i])) for t, i in zip(tones, idx)) / len(tones)
        out[old] = {'to': name, 'tones': idx, 'drift': round(drift, 3)}
    return out


def aliased_materials(pal: dict | None = None) -> dict:
    """art/materials.json as it would be with every one of today's ramps recoloured to the
    house palette by `mapping()`: same names, same lengths, same indices, so no generator
    changes to try it. The first step of the migration (house-style.md)."""
    pal = pal or build()
    with open(os.path.join(HERE, '..', '..', 'art', 'materials.json')) as f:
        mats = json.load(f)
    for old, m in mapping(pal).items():
        mats['materials'][old] = [pal['ramps'][m['to']][i] for i in m['tones']]
    mats['outline'] = INK
    return mats


def main(argv) -> int:
    built = build()
    if '--preview-materials' in argv:
        out = argv[argv.index('--preview-materials') + 1]
        with open(out, 'w') as f:
            json.dump(aliased_materials(built), f, indent=2)
            f.write('\n')
        print('wrote', out, '(a preview; art/materials.json is unchanged)')
        return 0
    if '--write' in argv:
        data = {'about': 'NapAttack house palette, proposed (docs/vision/house-style.md). Written by '
                         'scripts/art/house_palette.py --write; edit BASES there, not this file.'}
        data['ink'] = INK
        data['rule'] = {
            'dusk_hue': DUSK_HUE, 'lamp_hue': LAMP_HUE, 'shade_hue_step': SHADE_HUE_STEP,
            'light_hue_step': LIGHT_HUE_STEP, 'shade_tint': SHADE_TINT, 'light_tint': LIGHT_TINT,
            'shade_dl': SHADE_DL, 'light_dl': LIGHT_DL, 'l_floor': L_FLOOR, 'l_ceil': L_CEIL,
            'shade_c': SHADE_C, 'light_c': LIGHT_C,
            'edge_to_ink': EDGE_TO_INK, 'shadow_steps': SHADOW_STEPS, 'sibling_turn': SIBLING_TURN, 'sibling_dl': SIBLING_DL,
            'sibling_c': SIBLING_C,
        }
        data['bases'] = {k: {'kind': v[0], 'body': v[1]} for k, v in BASES.items()}
        data.update(built)
        data['from_materials'] = mapping(built)
        with open(JSON, 'w') as f:
            json.dump(data, f, indent=1)
            f.write('\n')
        print('wrote', os.path.relpath(JSON))
        return 0
    data = load()
    bad = [k for k in built['ramps'] if data['ramps'].get(k) != built['ramps'][k]]
    bad += [k for k in built['edges'] if data['edges'].get(k) != built['edges'][k]]
    if bad:
        print('house-palette.json is out of date with the rule for:', ', '.join(sorted(set(bad))))
        return 1
    fam = sum(1 for k in built['kinds'].values() if not k.startswith('sibling'))
    print(f'house palette: {fam} families, {len(built["ramps"])} ramps with siblings, {sum(len(r) for r in built["ramps"].values())} tones, '
          f'{len(built["edges"])} edge tones; matches the rule')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
