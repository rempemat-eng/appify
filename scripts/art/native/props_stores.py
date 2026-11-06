"""Stores at 2x: the barrel, the crate, the sack and a stack of them (Claude B, lane B's first
kit module, to-all-kit-modules 21 Oct).

The 1x masters are garden_props.barrel, crate and sack (scripts/art/garden_props.py, the
designs every zone places today). Each is drawn here natively, in props.py's style: the same
silhouette, type, colours and proportions as its 1x sprite, more detail at 2x (stave joints and
hoops, lid boards, planks with grain and nail heads, hessian folds and a tied neck).

Units: 1 unit = 1 px at density 2 (0.5 world px); y runs up from the ground point (negative is
up). Each function returns (img, anchor, alpha) with the anchor the ground point under the
object, like props.py. Colour comes only from palette families (raster.Part.fam).

Sizes, in world px, from the 1x masters and the size guide (size_guide.json kinds):
    barrel       11 wide, 14 tall      (barrel: 10 to 14 wide, 12 to 15 tall)
    crate        12 wide, 11 tall      (crate: 10 to 16 wide, 9 to 13 tall)
    sack         12 wide, 11 tall      (sack: 9 to 14 wide, 8 to 13 tall)
    crate_stack  a crate, a smaller crate on its lid, a sack against its east side
                 (crate_stack: 20 to 40 wide, 16 to 30 tall)

Stores stand against something (world-rules 6.4; prop_clusters' `against`); the cluster
placer, not this module, decides where.

    python3 -m scripts.art.native.props_stores [OUT_DIR]   writes the 2x swatch beside the golden
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

from . import raster as pk
from .props import _out, _sprite

WOOD = ['timber', 'timber_warm', 'timber_cool']


# ------------------------------------------------------------------------------------------------
def _barrel(sp, cx=0.0, base=0.0, w=22.0, h=28.0, seed=0, z=1.0, tag=''):
    """A barrel's parts into sprite sp, its foot at (cx, base): bellied staves lit on the west
    with their joints, two iron hoops that catch the light, the lid's boards inside its rim, a
    dark bottom chime."""
    g = sp.g
    rng = np.random.default_rng(seed)
    top = base - h
    rx = w / 2
    belly = 0.06 * w                          # how far the staves bow out at the middle
    lid_ry = max(2.2, w * 0.15)
    # the staves' outline: a gentle barrel curve from chime to chime
    pts = []
    n = 12
    for i in range(n + 1):
        t = i / n
        y = top + lid_ry + t * (h - lid_ry)
        bow = belly * math.sin(math.pi * t)
        pts.append((cx - rx - bow, y))
    for i in range(n, -1, -1):
        t = i / n
        y = top + lid_ry + t * (h - lid_ry)
        bow = belly * math.sin(math.pi * t)
        pts.append((cx + rx + bow, y))
    body = g.poly(pts) | g.ellipse(cx, base - lid_ry * 0.6, rx, lid_ry * 0.6)
    nm = f'staves{tag}'
    p = sp.add(nm, body, 'timber', base=3, lo=0, hi=5, z=z, mode='cyl', k=1.0)
    # sibling timbers stave by stave (each stave its own piece of oak)
    sw = w / 6
    edges = [cx - rx - belly + sw * k for k in range(1, 7)]
    fam = np.full(body.shape, 'timber', dtype=object)
    for k in range(6):
        x0 = cx - rx - belly + sw * k
        sel = (g.X >= x0) & (g.X < x0 + sw)
        fam[sel] = WOOD[(k + seed) % 3]
    p.famarr = fam
    for x in edges[:-1]:                      # the joints between staves
        sp.mark(nm, g.rect(x - 0.5, top, x + 0.5, base), -1)
    for _ in range(4):                        # grain in the staves
        gx = rng.uniform(cx - rx + 2, cx + rx - 3)
        gy = rng.uniform(top + lid_ry + 3, base - 4)
        sp.mark(nm, g.rect(gx, gy, gx + 0.8, gy + rng.uniform(2.5, 5)), -1)
    sp.mark(nm, g.rect(cx - rx - 3, base - 2.4, cx + rx + 3, base), -1)    # the bottom chime
    # two iron hoops, a band each near the chimes, lit on the west, a glint
    for j, hy in enumerate((top + lid_ry + h * 0.14, base - h * 0.22)):
        hn = f'hoop{tag}{j}'
        band = body & (g.Y >= hy - 1.4) & (g.Y < hy + 1.4)
        sp.add(hn, band, 'iron', base=3, lo=1, hi=5, z=z + 0.2, mode='cyl', k=1.1)
        sp.mark(hn, band & (g.Y < hy - 0.4), 1)
        gx = cx - rx * 0.55
        sp.detail(g.rect(gx - 1.0, hy - 1.4, gx + 1.0, hy - 0.4), pk.rgb('iron', 5))
    # the lid seen from above inside its rim: three boards, the rim lit at the back
    rim = g.ellipse(cx, top + lid_ry, rx + belly * 0.2, lid_ry)
    sp.add(f'rim{tag}', rim, 'timber', base=4, lo=2, hi=5, z=z + 0.3, flat=True)
    # the rim's top edge as one lighter ring all round (A's sign-off note, 21 Oct), turned from
    # the light only at its east end
    ring = rim & ~g.ellipse(cx, top + lid_ry + 0.3, rx - 2.2, lid_ry - 1.1)
    sp.mark(f'rim{tag}', ring & (g.X < cx + rx * 0.55), 1)
    lid = g.ellipse(cx, top + lid_ry + 0.3, rx - 2.2, lid_ry - 1.1)
    ln = f'lid{tag}'
    sp.add(ln, lid, 'timber_warm', base=3, lo=1, hi=4, z=z + 0.4, flat=True)
    for k in (-1, 1):
        sp.mark(ln, g.rect(cx + k * (rx - 2.2) / 3 - 0.5, top, cx + k * (rx - 2.2) / 3 + 0.5, top + 2 * lid_ry), -1)
    sp.mark(ln, g.rect(cx - rx, top + lid_ry - 0.2, cx - rx * 0.3, top + lid_ry + 0.8), 1)
    sp.mark(f'rim{tag}', rim & (g.Y < top + lid_ry * 0.6) & (g.X < cx + rx * 0.4), 1)


def _crate(sp, cx=0.0, base=0.0, w=24.0, h=22.0, seed=0, z=1.0, tag='', lid_frac=0.3):
    """A crate's parts into sprite sp, its foot at (cx, base): the lid of three boards seen
    from above, lit from the upper left; the front of two planks with grain between corner
    battens; nail heads; the east batten turned from the light."""
    g = sp.g
    rng = np.random.default_rng(seed + 17)
    x0, x1 = cx - w / 2, cx + w / 2
    top = base - h
    lid_b = top + h * lid_frac
    # the front: two planks with a seam, grain, the bottom board darker
    fn = f'front{tag}'
    front = g.rect(x0, lid_b, x1, base)
    p = sp.add(fn, front, 'timber', base=2, lo=0, hi=3, z=z, flat=True)
    mid = (lid_b + base) / 2
    fam = np.where(g.Y < mid, WOOD[seed % 3], WOOD[(seed + 1) % 3]).astype(object)
    p.famarr = fam
    sp.mark(fn, g.rect(x0, mid - 0.5, x1, mid + 0.6), -1)           # the seam between planks
    sp.mark(fn, g.rect(x0, lid_b, x1, lid_b + 1.0), -1)             # the lid's shadow line
    sp.mark(fn, g.rect(x0, base - 1.2, x1, base), -1)
    for _ in range(3):
        gx = rng.uniform(x0 + 4, x1 - 9)
        gy = rng.uniform(lid_b + 2, base - 3)
        sp.mark(fn, g.rect(gx, gy, gx + rng.uniform(3, 6), gy + 0.8), -1)
    # corner battens: the west one lit, the east one turned from the light
    bw = max(2.2, w * 0.12)
    sp.add(f'batW{tag}', g.rect(x0, lid_b, x0 + bw, base), 'timber', base=3, lo=2, hi=4, z=z + 0.1, flat=True)
    sp.add(f'batE{tag}', g.rect(x1 - bw, lid_b, x1, base), 'timber_cool', base=1, lo=0, hi=2, z=z + 0.1, flat=True)
    sp.mark(f'batE{tag}', g.rect(x1 - 0.9, lid_b, x1, base), -1)
    # the lid, a plane seen from above in our 3/4 view (A's sign-off note, 21 Oct: like the hut's
    # table): lighter than the front, two boards running across with one seam, lit from the
    # upper left (its west end and back edge brightest), its east end turned from the light
    ln = f'lidtop{tag}'
    lid = g.rect(x0, top, x1, lid_b)
    p = sp.add(ln, lid, 'timber_warm', base=4, lo=3, hi=5, z=z + 0.2, flat=True)
    lh = lid_b - top
    fam = np.where(g.Y < top + lh / 2, 'timber_warm', WOOD[(seed + 2) % 3]).astype(object)
    p.famarr = fam
    yy = top + lh / 2
    sp.mark(ln, g.rect(x0 + 1, yy - 0.45, x1 - 1, yy + 0.45), -1)
    sp.mark(ln, g.rect(x0, top, x1 - 4, top + 1.0) | g.rect(x0, top, x0 + w * 0.3, lid_b), 1)
    sp.mark(ln, g.rect(x1 - 4, top, x1, lid_b), -1)
    gx = rng.uniform(x0 + 3, x1 - 8)
    sp.mark(ln, g.rect(gx, top + lh * 0.45, gx + 4, top + lh * 0.45 + 0.7), -1)
    # nail heads at the battens' ends and the lid's corners
    for (nx, ny) in ((x0 + bw / 2, lid_b + 2.2), (x0 + bw / 2, base - 2.6), (x1 - bw / 2, lid_b + 2.2),
                     (x1 - bw / 2, base - 2.6), (x0 + 2.0, top + lh / 2), (x1 - 2.0, top + lh / 2)):
        sp.detail(g.rect(nx - 0.6, ny - 0.6, nx + 0.6, ny + 0.6), pk.rgb('iron', 1))


def _sack(sp, cx=0.0, base=0.0, w=24.0, h=22.0, seed=0, z=1.0, tag='', lean=0.0):
    """A hessian sack's parts into sprite sp, its foot at (cx, base): a full body slumped on
    its base, lit on the west, folds where it sags, a gathered neck tied with cord."""
    g = sp.g
    rng = np.random.default_rng(seed + 29)
    rx, ry = w / 2, h * 0.36
    cy = base - ry * 1.05
    body = g.ellipse(cx, cy, rx, ry) | g.ellipse(cx + lean, base - ry * 0.55, rx * 1.04, ry * 0.58)
    nx = cx + lean * 0.4
    neck = g.capsule(nx, cy - ry * 0.55, nx + lean * 0.6, base - h + 2.4, max(2.4, w * 0.13))
    ear = g.ellipse(nx + lean * 0.6, base - h + 1.8, max(2.6, w * 0.15), 1.8)
    bn = f'sack{tag}'
    sp.add(bn, body, 'sand', base=3, lo=0, hi=5, z=z, mode='form', k=1.0)
    sp.add(f'neck{tag}', neck | ear, 'sand', base=3, lo=1, hi=4, z=z + 0.1, mode='form', k=1.0)
    # folds where the cloth sags from the neck, and a seam
    for k in (-1, 1):
        sp.mark(bn, g.stroke([(nx + k * 1.5, cy - ry * 0.6), (cx + k * rx * 0.45, cy + ry * 0.2),
                              (cx + k * rx * 0.55, base - 2.5)], 0.6), -1)
    sp.mark(bn, g.stroke([(cx - rx * 0.6, cy - ry * 0.2), (cx - rx * 0.3, cy - ry * 0.55)], 0.7), 1)
    sp.mark(bn, g.ellipse(cx - rx * 0.35, cy - ry * 0.25, rx * 0.28, ry * 0.35), 1)
    # the cord round the neck
    cyc = cy - ry * 0.75
    cord = g.rect(nx - w * 0.17, cyc - 1.0, nx + w * 0.17, cyc + 0.6) & (neck | body)
    sp.add(f'cord{tag}', cord | g.capsule(nx + 1.5, cyc, nx + 3.5, cyc + 3.5, 0.6), 'timber_cool', base=2, lo=0,
           hi=3, z=z + 0.2, flat=True)
    # a stencilled mark on the cloth (a miller's or a grower's), two dark dabs
    if rng.random() < 0.6:
        mx = cx + rx * 0.15
        sp.mark(bn, g.rect(mx - 1.5, cy + 0.5, mx + 1.5, cy + 1.5) | g.rect(mx - 0.5, cy - 0.5, mx + 0.5, cy + 2.5), -1)


# ------------------------------------------------------------------------------------------------
def barrel4(d, seed=0):
    """The 1x barrel (11 x 14 world px)."""
    sp = _sprite(d, 34, 36, 17, 3)
    _barrel(sp, 0, 0, 22, 28, seed)
    return _out(sp)


def crate4(d, seed=0):
    """The 1x crate (12 x 11 world px)."""
    sp = _sprite(d, 34, 30, 17, 3)
    _crate(sp, 0, 0, 24, 22, seed)
    return _out(sp)


def sack4(d, seed=0):
    """The 1x sack (12 x 11 world px)."""
    sp = _sprite(d, 34, 30, 17, 3)
    _sack(sp, 0, 0, 24, 22, seed)
    return _out(sp)


def crate_stack4(d, seed=0):
    """A stack against a wall or a cart (crate_stack, 2 x 1 cells): a crate, a smaller crate
    on its lid set back and to the west, a sack slumped against its east side."""
    sp = _sprite(d, 56, 54, 26, 3)
    _crate(sp, -2, 0, 26, 22, seed, z=1.0, tag='a')
    _crate(sp, -5, -18.6, 18, 16, seed + 1, z=2.0, tag='b')   # on the lid, set back to its middle
    _sack(sp, 15, 0, 18, 18, seed + 2, z=3.0, tag='c', lean=-2.0)
    return _out(sp)


KINDS = {'barrel': barrel4, 'crate': crate4, 'sack': sack4, 'crate_stack': crate_stack4}

# Each store keeps its pieces apart (A, 21 Oct: barrels, crates and sacks will likely break in
# fights): every part is named by its piece, so a break can lift the lid, spring the hoops and
# split the staves. `pieces` renders each piece alone on the same canvas (no frames yet).
PIECES = {
    'barrel': {'lid': ('lid', 'rim'), 'hoops': ('hoop',), 'staves': ('staves',)},
    'crate': {'lid': ('lidtop',), 'front': ('front',), 'battens': ('batW', 'batE')},
    'sack': {'neck': ('neck', 'cord'), 'body': ('sack',)},
}
_BUILD = {
    'barrel': lambda d, seed: (_sprite(d, 34, 36, 17, 3), lambda sp: _barrel(sp, 0, 0, 22, 28, seed)),
    'crate': lambda d, seed: (_sprite(d, 34, 30, 17, 3), lambda sp: _crate(sp, 0, 0, 24, 22, seed)),
    'sack': lambda d, seed: (_sprite(d, 34, 30, 17, 3), lambda sp: _sack(sp, 0, 0, 24, 22, seed)),
}


def pieces(kind: str, d: float, seed: int = 0) -> dict:
    """{piece: RGBA image} for one store, each piece drawn alone on the whole sprite's canvas
    (same anchor), so the pieces lie exactly where the whole store has them."""
    out = {}
    for piece, prefixes in PIECES[kind].items():
        sp, draw = _BUILD[kind](d, seed)
        draw(sp)
        keep = [pt for pt in sp.parts if pt.name.startswith(prefixes)]
        sp.parts = keep
        sp.inkmarks = []
        out[piece] = sp.render()
    return out


# ------------------------------------------------------------------------------------------------
# the swatch: one phone screen of the pilot's ground with these stores on it, beside the golden
# ------------------------------------------------------------------------------------------------
SWATCH = [  # (kind, foot x, foot y in the terrain canvas's world px, seed): two groups on the lawn
    ('crate_stack', 214, 424, 3), ('barrel', 236, 424, 1), ('barrel', 246, 428, 2), ('sack', 196, 427, 4),
    ('crate', 58, 506, 5), ('sack', 72, 508, 6), ('barrel', 44, 504, 7),
]


def swatch(out_dir: str, d: float = 2) -> str:
    """Render the swatch: the pilot's terrain (its lawn, rock, paths and water, with none of its
    props), the stores from SWATCH, the boulder from props.py as the meadow's rock for
    comparison, shadows and contact lines by compose's one rule; then the golden scene beside it
    at the same scale. Returns the path written."""
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
    sc = C.screen_crop(codes, d)
    G = C.ground_from_codes(sc, d)
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
    golden = Image.open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))), 'art', 'golden', 'pilot', 'scene_2x.png')).convert('RGBA')
    gap = 16
    both = Image.new('RGBA', (pic.width + gap + golden.width, max(pic.height, golden.height)), (20, 18, 24, 255))
    both.alpha_composite(pic, (0, 0))
    both.alpha_composite(golden, (pic.width + gap, 0))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'props_stores_swatch_2x.png')
    both.save(path)
    # the stores alone at 4x, at 1.5 and 2, for the review
    row = []
    for dd in (1.5, 2):
        for kind in KINDS:
            row.append(KINDS[kind](dd, seed=3)[0])
    sheet = Image.new('RGBA', (sum(r.width for r in row) + 8 * (len(row) + 1), max(r.height for r in row) + 16),
                      (124, 150, 80, 255))
    x = 8
    for r in row:
        sheet.alpha_composite(r, (x, sheet.height - 8 - r.height))
        x += r.width + 8
    sheet = sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST)
    sheet.save(os.path.join(out_dir, 'props_stores_sheet.png'))
    return path


if __name__ == '__main__':
    import tempfile
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), 'napattack-props-stores')
    print(swatch(out))
