"""The one palette: house ramps as codes (rules-system.md 2, SB-04).

Every colour comes from art/house-palette.json, plus the kit's proposed accents in
`accents.json` (each a ramp made by the house rule from one body colour, with its warm and
cool siblings and its edge tone): its rulings ('decided': the meadow's crag #8A5048 wins over
main's #8A5546) and its proposals, to be folded into the house palette by Claude A. Painters
draw in (family, tone); colour is applied once, when a picture is written.

Two views of the same palette:
- names: `rgb(family, tone)` for sprites (tone 0 to 5 on the ramp, 6 the family's edge tone);
- codes: a terrain canvas holds integers `family_index * 8 + tone` (tone 6 and 7 the edge
  tone), -1 for nothing, so shadows and light step along the ramps (`step`) and never mix.

`restrict` maps a finished picture onto a biome's allowed colours (its `palette` list).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(ART))
if ART not in sys.path:
    sys.path.insert(0, ART)
import house_palette as hp  # noqa: E402

_P = json.load(open(os.path.join(ROOT, 'art', 'house-palette.json')))
RAMPS: dict = dict(_P['ramps'])
EDGES: dict = dict(_P['edges'])
INK = _P['ink']
ACCENTS = json.load(open(os.path.join(HERE, 'accents.json')))


def add_family(name: str, body: str):
    """A family made by the house rule from one body colour: the ramp, its edge tone and its
    warm and cool siblings."""
    r = hp.ramp(body)
    RAMPS[name] = r
    EDGES[name] = hp.edge(r)
    w, c = hp.siblings(body)
    RAMPS[name + '_warm'] = hp.ramp(w)
    RAMPS[name + '_cool'] = hp.ramp(c)


for _name, _body in list(ACCENTS.get('decided', {}).items()) + list(ACCENTS['families'].items()):
    if not _name.startswith('_'):
        add_family(_name, _body)
for _name, _edge in ACCENTS['edges'].items():
    EDGES[_name] = _edge


def parent(f: str) -> str:
    return hp.family(f)


def rgb(fam: str, t: int) -> tuple:
    if t >= 6:
        e = EDGES.get(parent(fam))
        return hp.hex_rgb(e if e else INK)
    return hp.hex_rgb(RAMPS[fam][max(0, min(5, t))])


def ink() -> tuple:
    return hp.hex_rgb(INK)


# ------------------------------------------------------------------------------------------------
# codes: family * 8 + tone on a terrain canvas
# ------------------------------------------------------------------------------------------------
FAMS = ['crag', 'crag_warm', 'crag_cool', 'grass', 'grass_warm', 'grass_cool', 'leaf', 'leaf_warm',
        'leaf_cool', 'earth', 'earth_warm', 'earth_cool', 'path', 'path_warm', 'path_cool', 'snow',
        'snow_warm', 'snow_cool', 'water', 'water_warm', 'water_cool', 'plaster', 'brass', 'berry',
        'dusk', 'sky', 'timber', 'stone', 'stone_warm', 'stone_cool',
        # appended for the village kit (village.py): existing codes keep their numbers
        'timber_warm', 'timber_cool', 'plaster_warm', 'slate', 'slate_warm', 'slate_cool', 'sand', 'sand_warm',
        'sand_cool', 'clay', 'clay_cool', 'iron', 'lamp', 'soot', 'ash', 'void', 'lava', 'fox', 'ashlar',
        'ashlar_warm', 'berry_cool', 'sky_cool', 'brass_warm', 'dusk_cool']
FI = {n: i for i, n in enumerate(FAMS)}

LUT = np.zeros((len(FAMS) * 8, 3), np.uint8)
for _n, _i in FI.items():
    for _t in range(8):
        LUT[_i * 8 + _t] = rgb(_n, _t)


def C(fam, tone):
    return FI[fam] * 8 + tone


def step(code, d):
    """Move codes d tones along their own ramp (edge tones stay)."""
    code = np.asarray(code)
    f, t = code // 8, code % 8
    nt = np.clip(t + d, 0, 5)
    out = np.where((code >= 0) & (t < 6), f * 8 + nt, code)
    return out


def sib(code, which):
    """The same tone on a sibling ramp of the same parent family."""
    code = np.asarray(code)
    out = code.copy()
    for n, i in FI.items():
        p = parent(n)
        tgt = p if which == 'body' else f'{p}_{which}'
        if tgt in FI:
            m = (code // 8 == i) & (code >= 0)
            out[m] = FI[tgt] * 8 + code[m] % 8
    return out


def is_fam(code, parent_name):
    f = code // 8
    m = np.zeros(code.shape, bool)
    for n, i in FI.items():
        if parent(n) == parent_name:
            m |= (f == i)
    return m & (code >= 0)


def to_rgba(code):
    code = np.asarray(code)
    out = np.zeros(code.shape + (4,), np.uint8)
    ok = code >= 0
    out[ok, :3] = LUT[code[ok]]
    out[ok, 3] = 255
    return out


# ------------------------------------------------------------------------------------------------
# a biome's colours
# ------------------------------------------------------------------------------------------------
def colour_of(entry) -> tuple:
    """A palette entry as RGB: [family, tone] or 'ink'."""
    if entry == 'ink':
        return ink()
    return rgb(entry[0], int(entry[1]))


def code_of(c: tuple, names=None):
    """The [family, tone] entry for an RGB colour (or 'ink'), or None if no house colour."""
    c = tuple(int(v) for v in c)
    if c == ink():
        return 'ink'
    for f in (names or RAMPS):
        for t in range(7):
            if rgb(f, t) == c:
                return [f, t]
    return None


def restrict(img, allowed):
    """Every colour of an RGBA picture that is not in `allowed` ([family, tone] entries or
    'ink') moves to the nearest allowed colour (RGB distance). Returns the picture and how
    many pixels moved."""
    from PIL import Image
    a = np.asarray(img.convert('RGB')).copy()
    pal = np.array(sorted({colour_of(e) for e in allowed}), dtype=np.int64)
    flat = a.reshape(-1, 3)
    uniq, inv = np.unique(flat, axis=0, return_inverse=True)
    keyset = {tuple(c) for c in pal}
    out = uniq.copy()
    moved = np.zeros(len(uniq), bool)
    P = pal.astype(float)
    for i, c in enumerate(uniq):
        if tuple(c) not in keyset:
            out[i] = pal[((P - c.astype(float)) ** 2).sum(1).argmin()]
            moved[i] = True
    res = out[inv.ravel()].reshape(a.shape).astype(np.uint8)
    n = int(moved[inv.ravel()].sum())
    return Image.fromarray(res, 'RGB').convert('RGBA'), n
