"""Wayside props at 2x: the water troughs and the stone bench (Claude B, lane B's second kit
module, to-all-kit-modules 21 Oct). Noticeboards and wells follow in this module; stiles, gates
and fingerposts are lane G's thresholds (native/paths.py), not here.

The 1x masters are wayside_props.trough (variants 0 stone, 1 timber, 2 half barrel) and
wayside_props.bench_stone (scripts/art/wayside_props.py). Each is drawn natively in props.py's
style: the same silhouette, type, colours and proportions as its 1x sprite, more detail at 2x.
Stone follows the kit's stone (props.boulder4, r8): a flat lit top plane, a hard step to a
darker face, a base band, joints as chunky gaps with their lower lip lit, never polygon lines.

Units: 1 unit = 1 px at density 2 (0.5 world px); y runs up from the ground point (negative is
up). Each function returns (img, anchor, alpha) like props.py. Colour comes only from palette
families.

Sizes, in world px, from the 1x masters and the size guide (trough 24 to 40 long, 8 to 14
tall; bench 28 to 36 long, 12 to 14 tall):
    trough_stone   32 x 14      trough_timber  32 x 13      trough_barrel  20 x 13
    bench_stone    32 x 14

    python3 -m scripts.art.native.props_wayside [OUT_DIR]   writes the 2x swatch beside the golden
"""
from __future__ import annotations

import os
import sys

import numpy as np

from . import raster as pk
from .props import _out, _sprite

WOOD = ['timber', 'timber_warm', 'timber_cool']


# ------------------------------------------------------------------------------------------------
def _water(sp, g, x0, x1, y0, y1, z, tag=''):
    """Still water inside a rim: darker under the near (south) lip and the far rim's shadow,
    the sky's light in a short band, a fallen leaf afloat."""
    nm = f'water{tag}'
    m = g.rrect(x0, y0, x1, y1, 1.0)
    sp.add(nm, m, 'water', base=2, lo=0, hi=4, z=z, flat=True, outline=False, casts=False)
    sp.mark(nm, g.rect(x0, y0, x1, y0 + 1.2), -1)                       # the far rim's shade
    sp.mark(nm, g.rect(x0 + (x1 - x0) * 0.12, (y0 + y1) / 2 - 0.5, x0 + (x1 - x0) * 0.32, (y0 + y1) / 2 + 0.6), 2)
    return nm


def trough_stone4(d, seed=72):
    """The 1x stone trough (32 x 14 world px): a hewn block, its rim a lit top plane round the
    water, the front face a tone darker in two courses of tooling, the east end turned from the
    light, weed at the waterline, an iron spout at the west end feeding it."""
    sp = _sprite(d, 76, 36, 38, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    L, top, rim_b = 31.0, -22.0, -14.0
    front = g.rrect(-L, rim_b - 1, L, 0, 1.5)
    sp.add('face', front, 'stone', base=2, lo=0, hi=3, z=1, flat=True)
    sp.mark('face', g.rect(-L, rim_b - 1, L, rim_b + 0.6), 1)            # the lip's lit edge
    sp.mark('face', g.rect(L - 6, rim_b, L, 0), -1)                       # the east end
    sp.mark('face', g.rect(-L, -2.2, L, 0), -1)                           # the base band
    for k in range(5):                                                    # tooling across the face
        x = rng.uniform(-L + 3, L - 12)
        y = rng.uniform(rim_b + 2.5, -4)
        sp.mark('face', g.rect(x, y, x + rng.uniform(4, 8), y + 1.0), -1)
    sp.mark('face', g.rect(-L, -8.4, L, -7.4), -1)                        # the course joint
    sp.mark('face', g.rect(-L, -7.4, L, -6.6), 1)                         # its lower lip, lit
    rim = g.rrect(-L, top, L, rim_b, 2.0)
    sp.add('rim', rim, 'stone', base=4, lo=2, hi=5, z=2, flat=True)
    sp.mark('rim', g.rect(-L, top, L - 4, top + 1.2) | g.rect(-L, top, -L + 2.4, rim_b), 1)
    sp.mark('rim', g.rect(L - 4, top, L, rim_b), -1)
    _water(sp, g, -L + 4, L - 4, top + 2.6, rim_b - 1.6, 2.5)
    sp.add('weed', g.rect(-L + 5, rim_b - 2.4, L - 6, rim_b - 1.6), 'leaf', base=2, lo=1, hi=3, z=2.6, flat=True,
           outline=False, casts=False)
    leaf_x = rng.uniform(4, 14)
    sp.detail(g.rect(leaf_x, top + 4.0, leaf_x + 3.0, top + 5.2), pk.rgb('clay', 4))
    # the spout at the west end, its trickle
    sp.add('spout', g.rrect(-L - 2, top - 5, -L + 9, top - 2.4, 1.0), 'iron', base=3, lo=1, hi=5, z=3, flat=True)
    sp.mark('spout', g.rect(-L - 2, top - 5, -L + 9, top - 4.0), 1)
    sp.add('trickle', g.rect(-L + 7.4, top - 2.4, -L + 8.8, top + 3.0), 'water', base=4, lo=3, hi=5, z=3.1,
           flat=True, outline=False, casts=False)
    return _out(sp)


def trough_timber4(d, seed=73):
    """The 1x timber trough (32 x 13 world px): planks with their joints held by two iron bands,
    the top edge lit round the water, standing on a pair of sleepers."""
    sp = _sprite(d, 76, 34, 38, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    L, top, rim_b = 31.0, -22.0, -16.0
    body = g.rect(-L, rim_b, L, -3.2)
    p = sp.add('planks', body, 'timber', base=3, lo=0, hi=4, z=1, flat=True)
    h = -3.2 - rim_b
    fam = np.full(body.shape, 'timber', dtype=object)
    for k in range(3):
        sel = (g.Y >= rim_b + h * k / 3) & (g.Y < rim_b + h * (k + 1) / 3)
        fam[sel] = WOOD[(k + seed) % 3]
        if k:
            sp.mark('planks', g.rect(-L, rim_b + h * k / 3 - 0.5, L, rim_b + h * k / 3 + 0.5), -2)
    p.famarr = fam
    sp.mark('planks', g.rect(L - 5, rim_b, L, 0), -1)
    for _ in range(4):
        x = rng.uniform(-L + 3, L - 12)
        y = rng.uniform(rim_b + 1.5, -5)
        sp.mark('planks', g.rect(x, y, x + rng.uniform(4, 9), y + 0.8), -1)
    rim = g.rect(-L, top, L, rim_b)
    sp.add('rim', rim, 'timber', base=4, lo=2, hi=5, z=2, flat=True)
    sp.mark('rim', g.rect(-L, top, L - 4, top + 1.0), 1)
    sp.mark('rim', g.rect(L - 4, top, L, rim_b), -1)
    _water(sp, g, -L + 3, L - 3, top + 1.6, rim_b - 1.2, 2.5)
    for bx in (-L + 9, L - 11):                                           # iron bands over the planks
        band = g.rect(bx, top + 0.5, bx + 2.4, -3.2)
        sp.add(f'band{bx:.0f}', band, 'iron', base=3, lo=1, hi=4, z=3, flat=True)
        sp.mark(f'band{bx:.0f}', g.rect(bx, top, bx + 1.0, 0), 1)
        for y in (rim_b + 2, -6):
            sp.detail(g.rect(bx + 0.7, y, bx + 1.7, y + 1.0), pk.rgb('iron', 5))
    for sx in (-L + 3, L - 15):                                           # the sleepers it stands on
        sp.add(f'sleeper{sx:.0f}', g.rect(sx, -3.6, sx + 12, 0), 'timber_cool', base=2, lo=0, hi=3, z=0.5, flat=True)
        sp.mark(f'sleeper{sx:.0f}', g.rect(sx, -3.6, sx + 12, -2.8), 1)
    return _out(sp)


def trough_barrel4(d, seed=74):
    """The 1x half barrel by a spring pipe (20 x 13 world px): bellied staves with their joints,
    two iron hoops lit on the west, the rim's end grain round the water, moss on the shaded
    staves, the pipe running in from the west with its trickle."""
    sp = _sprite(d, 56, 34, 24, 3)
    g = sp.g
    rx, top = 18.0, -20.0
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((-rx - 1.2 * np.sin(np.pi * t), top + 3 + t * (-top - 3)))
    for i in range(8, -1, -1):
        t = i / 8
        pts.append((rx + 1.2 * np.sin(np.pi * t), top + 3 + t * (-top - 3)))
    body = g.poly(pts)
    p = sp.add('staves', body, 'timber', base=3, lo=0, hi=5, z=1, mode='cyl', k=1.0)
    fam = np.full(body.shape, 'timber', dtype=object)
    for k in range(6):
        x0 = -rx + 2 * rx * k / 6
        fam[(g.X >= x0) & (g.X < x0 + 2 * rx / 6)] = WOOD[(k + seed) % 3]
        if k:
            sp.mark('staves', g.rect(x0 - 0.5, top, x0 + 0.5, 0), -1)
    p.famarr = fam
    sp.mark('staves', g.rect(-rx - 2, -2.4, rx + 2, 0), -1)
    for j, hy in enumerate((top + 6, -5.0)):
        band = body & (g.Y >= hy - 1.3) & (g.Y < hy + 1.3)
        sp.add(f'hoop{j}', band, 'iron', base=3, lo=1, hi=5, z=1.2, mode='cyl', k=1.1)
        sp.detail(g.rect(-rx * 0.6, hy - 1.3, -rx * 0.6 + 2, hy - 0.4), pk.rgb('iron', 5))
    sp.add('moss', body & g.ellipse(rx * 0.55, -9, 5, 3.5), 'leaf', base=2, lo=1, hi=3, z=1.1, flat=True,
           outline=False)
    rim = g.ellipse(0, top + 3, rx + 0.6, 4.4)
    sp.add('rim', rim, 'timber', base=5, lo=3, hi=5, z=2, flat=True)
    sp.mark('rim', g.ellipse(0, top + 3, rx + 0.6, 4.4) & (g.X > rx * 0.4), -1)
    sp.add('water', g.ellipse(0, top + 3.4, rx - 2.4, 2.8), 'water', base=2, lo=0, hi=4, z=2.5, flat=True,
           outline=False, casts=False)
    sp.mark('water', g.rect(-rx * 0.55, top + 3.0, -rx * 0.15, top + 4.0), 2)
    # the spring pipe from the west, its trickle into the barrel
    sp.add('pipe', g.rect(-rx - 9, top - 4, -rx + 6, top - 1.6), 'iron', base=3, lo=1, hi=5, z=3, flat=True)
    sp.mark('pipe', g.rect(-rx - 9, top - 4, -rx + 6, top - 3.0), 1)
    sp.add('trickle', g.rect(-rx + 4.4, top - 1.6, -rx + 5.8, top + 3.4), 'water', base=4, lo=3, hi=5, z=3.1,
           flat=True, outline=False, casts=False)
    return _out(sp)


def bench_stone4(d, seed=21):
    """The 1x stone bench at a viewpoint (32 x 14 world px): a dressed seat slab on two coursed
    blocks, a lower slab set upright behind as its back, the seat worn smooth and paler where
    people sit, moss along the back's top and in the joints."""
    sp = _sprite(d, 72, 34, 36, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    L = 31.0
    # the back slab, behind: its top lit, its face in half light, moss along the top
    sp.add('back', g.rrect(-L + 2, -28, L - 2, -16, 1.4), 'stone', base=3, lo=1, hi=5, z=0.5, flat=True)
    sp.mark('back', g.rect(-L, -28, L - 6, -26.6), 2)
    sp.mark('back', g.rect(-L, -26.6, L - 6, -25.4), 1)
    sp.mark('back', g.rect(L - 6, -28, L, -16), -1)
    for x in (-L + 6, -6.0, 12.0):
        sp.detail(g.rect(x, -28.6, x + rng.uniform(3.5, 6), -27.4), pk.rgb('leaf', 3))
    # the seat slab seen from above, worn pale in the middle, its front edge in shade
    seat = g.rrect(-L, -17, L, -11, 1.2)
    sp.add('seat', seat, 'stone_warm', base=4, lo=2, hi=5, z=2, flat=True)
    sp.mark('seat', g.ellipse(0, -14, 13, 2.2), 1)
    sp.mark('seat', g.rect(L - 4, -17, L, -11), -1)
    sp.add('edge', g.rect(-L, -11, L, -7.4), 'stone', base=2, lo=0, hi=3, z=2.1, flat=True)
    sp.mark('edge', g.rect(-L, -11, L, -10.2), 1)
    sp.mark('edge', g.rect(L - 4, -11, L, -7.4), -1)
    # two coursed blocks under it, lit on the west
    for bx in (-L + 5, L - 17):
        nm = f'block{bx:.0f}'
        sp.add(nm, g.rect(bx, -7.4, bx + 12, 0), 'stone', base=3, lo=0, hi=4, z=1, mode='cyl', k=0.9)
        sp.mark(nm, g.rect(bx, -4.2, bx + 12, -3.4), -1)
        sp.mark(nm, g.rect(bx, -3.4, bx + 12, -2.8), 1)
        sp.detail(g.rect(bx + 3, -4.2, bx + 6, -3.4), pk.rgb('leaf', 2))
    # the shade under the seat between the blocks
    sp.add('under', g.rect(-L + 17, -7.4, L - 17, -5.6), 'stone_cool', base=0, lo=0, hi=1, z=0.4, flat=True,
           outline=False, casts=False)
    return _out(sp)


KINDS = {'trough_stone': trough_stone4, 'trough_timber': trough_timber4, 'trough_barrel': trough_barrel4,
         'bench_stone': bench_stone4}


# ------------------------------------------------------------------------------------------------
# the swatch: one phone screen of the pilot's ground with these props on it, beside the golden
# ------------------------------------------------------------------------------------------------
SWATCH = [  # (kind, foot x, foot y in the terrain canvas's world px, seed)
    ('trough_stone', 226, 428, 72), ('bench_stone', 212, 384, 21), ('trough_timber', 64, 506, 73),
    ('trough_barrel', 96, 470, 74),
]


def swatch(out_dir: str, d: float = 2) -> str:
    """The pilot's terrain with none of its props, these wayside props and props.py's boulder,
    shadows and contact lines by compose's one rule, the golden beside it (as props_stores)."""
    from PIL import Image
    from scipy import ndimage as ndi

    from . import ctx, load_biome, load_plan
    plan = load_plan('pilot')
    biome = load_biome(plan['biome'])
    ctx.configure(d, biome, plan)
    from . import compose as C
    from . import palette
    from . import props as P4
    from . import terrain as TER
    codes, _items, _tufts = TER.canvas()
    G = C.ground_from_codes(C.screen_crop(codes, d), d)
    W, H = G.w, G.h
    dy = plan['screen']['canvas_dy']
    items = []
    for kind, x, y, seed in SWATCH:
        img, anc, a = KINDS[kind](d, seed=seed)
        x0, y0, x1, y1 = C._bbox(a)
        items.append((y, img, ((x0 + x1) / 2, y1), (x * d, (y - dy) * d), a))
    img, anc, a = P4.boulder4(d, seed=31)
    x0, y0, x1, y1 = C._bbox(a)
    items.append((468, img, ((x0 + x1) / 2, y1), (200 * d, (468 - dy) * d), a))
    core = np.zeros((H, W), bool)
    for (_, im, an, at, a) in items:
        core |= C.shadow_mask(a, an, d, W, H, at, *C.SHADOW)
    ground = C.walkable_ground(G)
    inner = ndi.binary_erosion(core, iterations=max(1, int(round(d))))
    names = np.array(G.fams, dtype=object)[G.fam]
    body = np.where(np.isin(names, ['path', 'path_warm', 'path_cool', 'earth', 'earth_warm', 'earth_cool']), 4, 3)
    sel = inner & ground
    G.tone[sel] = np.clip(np.minimum(G.tone[sel], body[sel]) - 2, 0, 5)
    sel = core & ~inner & ground
    G.tone[sel] = np.clip(np.minimum(G.tone[sel], body[sel]) - 1, 0, 5)
    cm = np.zeros((H, W), bool)
    for (_, im, an, at, a) in items:
        cm |= C._contact(im, an, at, W, H, d)
    G.tone[cm & ground] = np.minimum(G.tone[cm & ground], 1)
    pic = G.rgba()
    for (_, im, an, at, a) in sorted(items, key=lambda t: t[0]):
        C.paste(pic, im, an, at)
    pic, _moved = palette.restrict(pic, biome['palette'])
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    golden = Image.open(os.path.join(root, 'art', 'golden', 'pilot', 'scene_2x.png')).convert('RGBA')
    gap = 16
    both = Image.new('RGBA', (pic.width + gap + golden.width, max(pic.height, golden.height)), (20, 18, 24, 255))
    both.alpha_composite(pic, (0, 0))
    both.alpha_composite(golden, (pic.width + gap, 0))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'props_wayside_swatch_2x.png')
    both.save(path)
    row = [KINDS[k](dd)[0] for dd in (1.5, 2) for k in KINDS]
    sheet = Image.new('RGBA', (sum(r.width for r in row) + 8 * (len(row) + 1), max(r.height for r in row) + 16),
                      (124, 150, 80, 255))
    x = 8
    for r in row:
        sheet.alpha_composite(r, (x, sheet.height - 8 - r.height))
        x += r.width + 8
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(
        os.path.join(out_dir, 'props_wayside_sheet.png'))
    return path


if __name__ == '__main__':
    import tempfile
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), 'napattack-props-wayside')
    print(swatch(out))
