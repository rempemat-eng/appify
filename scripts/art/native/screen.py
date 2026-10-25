"""A zone at density 2 from a plan and a biome: its layers, all through palette codes.

    ctx.configure(2.0, biome, plan)
    from scripts.art.native import screen
    z = screen.build()
    z.ground        RGBA texels: lawn, paths, places, light, water, rock, shadows, low plants
    z.objects       [(id, kind, (x, y, w, h) world px)]: each object's native picture's box,
                    its foot where the zone's own object stands (so walk and depth are unchanged)
    z.sprites       kind -> RGBA texels (one picture per kind, as the 1x zone has)
    z.flow          (sheet, (x, y, w, h) texels, cols) of the moving water, or None
    z.night         RGBA texels of the night light, or None (the woodland makes none)
    z.layers        name -> RGBA texels: terrain, water, shadows, light, plants (for review)

Nothing here belongs to one zone: the plan says where (today's geometry for a zone that keeps
its walk mask), the biome says how (recipes per kind, lawn, shadow, palette). The terrain is
the c-tiles lawn (terrain.scene.render on a flat plan); paths are scene.worn2; water is
water.paint on the plan's footprint; rocks are decals.lump_px; plants and props are the
kit's painters (foliage from the 1x masters, props, the one shadow rule in compose).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import ctx
from . import animate
from . import compose as CO
from . import props as P4
from . import props_stones as PS
from . import props_trees as PT
from . import water as WA
from .ctx import D, P
from .palette import C, FI, is_fam, sib, step
from .terrain import decals as DC
from .terrain import scene as SC
from .terrain import tiles as TL

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MASTERS = os.path.join(ROOT, 'art', 'masters')
TREES = ('tree',)


@dataclass
class Zone:
    ground: Image.Image
    objects: list
    sprites: dict
    flow: object
    night: object
    layers: dict = field(default_factory=dict)
    codes: np.ndarray | None = None


def mask_rle(rows, w, h) -> np.ndarray:
    """A world px mask from per-row runs [x0, x1, x0, x1, ...]."""
    m = np.zeros((h, w), bool)
    for y, row in enumerate(rows):
        for a, b in zip(row[0::2], row[1::2]):
            m[y, a:b] = True
    return m


def texels(m: np.ndarray) -> np.ndarray:
    k = int(D)
    return np.kron(m, np.ones((k, k), bool)).astype(bool)


def blob(cx, cy, rx, ry, seed=0, rough=0.18, w=None, h=None) -> np.ndarray:
    """An organic closed shape at texels: an ellipse whose radius wanders with the angle (the
    zones' blob, valley_zones.blob, drawn at density)."""
    import sys
    art = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if art not in sys.path:
        sys.path.insert(0, art)
    from pixel import noise2
    ph = [noise2(seed, k, 771) * 6.283 for k in range(4)]
    H, W = h, w
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = ((xx + 0.5) / D - cx) / rx, ((yy + 0.5) / D - cy) / ry
    a = np.arctan2(dy, dx)
    r = 1 + rough * (0.55 * np.sin(2 * a + ph[0]) + 0.35 * np.sin(3 * a + ph[1]) + 0.2 * np.sin(5 * a + ph[2])
                     + 0.1 * np.sin(8 * a + ph[3]))
    return dx * dx + dy * dy <= r * r


# ------------------------------------------------------------------------------------------------
# light: sun pools on the lawn
# ------------------------------------------------------------------------------------------------
def sun(cv: np.ndarray, m: np.ndarray, heart: float = 10.0, fade: float = 4.0) -> None:
    """A sun pool: the lawn's warm sibling at its own tone, the heart (`heart` texels in) a tone
    up, a 2 x 2 checker `fade` texels wide at the edge (the one place dither is used: light)."""
    lawn = m & (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)
    dist = ndi.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]
    yy, xx = np.mgrid[0:cv.shape[0], 0:cv.shape[1]]
    chk = ((xx // 2 + yy // 2) % 2) == 0
    sel = lawn & ((dist > fade) | chk)
    cv[sel] = sib(cv[sel], 'warm')
    up = lawn & (dist > heart)
    cv[up] = step(cv[up], 1)


# ------------------------------------------------------------------------------------------------
# rock
# ------------------------------------------------------------------------------------------------
def boulder(cv: np.ndarray, cx, base, w, h, seed, moss=True, fams=('stone', 'stone_warm', 'stone_cool')) -> None:
    """A stone lying on the ground (cx, base, w, h world px): the kit's pixel-art stone
    (decals.lump_px) with its contact shadow, a moss cushion on its crown when `moss`."""
    lp = DC.lump_px(P(w), P(h), seed, fams=fams)
    X, Y = P(cx - w / 2, -10 ** 6), P(base - h, -10 ** 6)
    if moss:
        hh, ww = lp.shape
        rng = np.random.default_rng(seed + 5)
        yy, xx = np.mgrid[0:hh, 0:ww]
        u, v = (xx - (ww - 1) / 2) / (ww / 2), (yy - (hh - 1) / 2) / (hh / 2)
        top = (lp >= 0) & (v < -0.35 + 0.15 * np.sin(u * 5 + rng.uniform(0, 6))) & (np.abs(u) < 0.75)
        top &= (lp % 8 >= 2) & (lp % 8 < 6)
        lp[top] = np.where(u[top] + v[top] < -0.75, C('leaf', 4), C('leaf', 3))
        under = np.zeros_like(top)
        under[1:] = top[:-1]
        under &= ~top & (lp >= 0) & (lp % 8 < 6)
        lp[under] = C('leaf', 2)
    DC.paste(cv, lp, X, Y, shadow=True, shadow_dx=P(2), shadow_dy=P(1))


def scree(cv: np.ndarray, depth, avoid: np.ndarray, seed=1612) -> None:
    """The talus along the top edge: a calm gravel band (the ledge floor's dirt, a tone down)
    with a soft lower edge, and pebbles of 2 to 4 world px lying in it in drifts that thin
    away from the face, each the kit's pixel-art stone with its contact shade."""
    import sys
    art = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if art not in sys.path:
        sys.path.insert(0, art)
    from pixel import noise2, smooth_noise
    H, W = cv.shape
    k = int(D)
    yy, xx = np.mgrid[0:H, 0:W]
    dep = np.array(depth, float)[np.clip(xx // k, 0, len(depth) - 1)]
    wob = np.array([[smooth_noise(x, y, 5, seed + 2) for x in range(W // k)] for y in range(H // k)])
    wobt = np.kron(wob, np.ones((k, k)))[:H, :W]
    band = (yy / D < dep * (0.75 + 0.35 * wobt)) & ~avoid & (cv >= 0)
    sheet = TL.SHEETS['path']
    fill = sheet[np.ix_(np.arange(H) % sheet.shape[0], np.arange(W) % sheet.shape[1])]
    cv[band] = step(fill[band], -1)
    edge = band & ~ndi.binary_erosion(band, iterations=max(1, int(D)))
    cv[edge & (cv % 8 < 6)] = step(cv[edge & (cv % 8 < 6)], -1)
    for x in range(1, len(depth) - 2, 2):
        for y in range(1, depth[x] - 2, 2):
            t = y / depth[x]
            if noise2(x, y, seed) < 0.62 + t * 0.3 or avoid[min(H - 1, y * k), min(W - 1, x * k)]:
                continue
            s_ = 2.0 + 2.4 * noise2(x, y, seed + 3) * (1 - t)
            lp = DC.lump_px(P(s_ * 1.2), P(s_), int(seed * 31 + x * 7 + y), fams=('stone', 'stone_warm', 'stone_cool'))
            DC.paste(cv, lp, x * k, y * k, shadow=True, shadow_dx=P(1), shadow_dy=P(0.5))


# ------------------------------------------------------------------------------------------------
# places
# ------------------------------------------------------------------------------------------------
def trodden(cv: np.ndarray, m: np.ndarray) -> None:
    """Trodden earth (the worn track's dirt) on a mask, a damp row along its edge."""
    sheet = TL.SHEETS['trail']
    H, W = cv.shape
    ys, xs = np.arange(H), np.arange(W)
    fill = sheet[np.ix_(ys % sheet.shape[0], xs % sheet.shape[1])]
    cv[m] = step(fill[m], -1)
    edge = m & ~ndi.binary_erosion(m, iterations=max(1, int(D)))
    cv[edge] = step(cv[edge], -1)


def footbridge(cv: np.ndarray, x0, w, y0, y1, water: np.ndarray) -> None:
    """A plank footbridge over a stream (world px): planks laid across, lit along their top
    edge, joints in shade, a lit west rail and a shaded east rail on posts, dressed stone
    abutments, its shadow on the water east of it."""
    H, W = cv.shape
    X0, X1, Y0, Y1 = P(x0, 0), P(x0 + w, 0), P(y0, 0), P(y1, 0)
    for Y in range(max(0, Y0 + P(4) - 1), min(H, Y1 + P(6))):          # its shadow on the water
        for X in range(X1 + P(1), min(W, X1 + P(3))):
            if water[Y, X]:
                cv[Y, X] = step(cv[Y:Y + 1, X:X + 1], -2)[0, 0]
    for Y in range(Y0 - P(3), Y0):                                     # the north abutment
        for X in range(X0 - P(3), X1 + P(3)):
            if 0 <= Y < H and 0 <= X < W and not water[Y, X]:
                cv[Y, X] = C('stone', 3 if (Y - Y0) > -P(1) else 2) if (X // P(4) + Y // P(1)) % 5 else C('stone', 1)
    for Y in range(Y1, Y1 + P(4)):                                     # the south abutment, its face lit
        for X in range(X0 - P(3), X1 + P(3)):
            if 0 <= Y < H and 0 <= X < W:
                r = (Y - Y1) / D
                c = C('stone', 4) if r < 1 else (C('stone', 3) if (X // P(5) + int(r) // 2) % 4 else C('stone', 2))
                cv[Y, X] = C('stone', 1) if r >= 3 else c
    pw = 3.0
    k = 0
    y = float(y0)
    while y < y1 - 0.01:
        ya, yb = P(y, 0), P(min(y1, y + pw), 0)
        for Y in range(ya, yb):
            for X in range(X0, X1):
                if not (0 <= Y < H and 0 <= X < W):
                    continue
                rr = (Y - ya) / D
                t = 4 if rr < 1 else (3 if rr < 2 else 1)
                if t == 3 and ((X // P(3) + k) % 7 == 0):
                    t = 2                                              # grain
                cv[Y, X] = C('timber', t)
            for nx in (X0 + P(1), X1 - P(1) - 1):                      # nails over the stringers
                if 0 <= ya + P(1) < H:
                    cv[ya + P(1), nx] = C('stone', 1)
        y += pw
        k += 1
    for (rx, lit) in ((X0 - P(1), True), (X1, False)):                 # the rails on their posts
        for Y in range(Y0 - P(4), Y1 - P(1)):
            for j in range(P(1)):
                if 0 <= Y < H and 0 <= rx + j < W:
                    cv[Y, rx + j] = C('timber', 4 if lit else 2) if j == 0 else C('timber', 3 if lit else 1)
        for py in (y0 - 1, (y0 + y1) / 2, y1 - 1):
            for Y in range(P(py - 4, 0), P(py, 0)):
                for j in range(-P(0.5), P(1) + P(0.5)):
                    if 0 <= Y < H and 0 <= rx + j < W:
                        cv[Y, rx + j] = C('timber', 3 if lit else 1)


# ------------------------------------------------------------------------------------------------
# objects: one picture per kind from the biome's recipe
# ------------------------------------------------------------------------------------------------
def _master(name: str) -> str:
    return os.path.join(MASTERS, name)


def tree_dims(master: str) -> dict:
    """A tree master's box, trunk width and crown height (world px), read from its pixels."""
    a = np.asarray(Image.open(_master(master)).convert('RGBA')).astype(int)
    al = a[..., 3] > 0
    green = al & (a[..., 1] > a[..., 0] + 4)
    H1, W1 = al.shape
    gy = np.nonzero(green.any(1))[0]
    ch = int(gy.max()) + 1 if len(gy) else H1 // 2
    wood = al & ~green & (a[..., 0] > a[..., 1] + 10)
    low = wood[H1 - 4:H1]
    cols = np.nonzero(low.any(0))[0]
    tw = int(cols.max() - cols.min() + 1) if len(cols) else max(4, W1 // 6)
    return dict(w=W1, h=H1, tw=int(np.clip(tw - 2, 3, W1 * 0.2)), ch=int(ch * 0.9))


def sprite(kind: str, recipe: dict, seed: int):
    """(picture, anchor (texels: the foot), alpha, shadow extra) for one kind."""
    paint = recipe['paint']
    if paint == 'tree' and recipe.get('trunk') in PT.SPECIES:
        # a birch or beech: the trunk read from the master by its shape and drawn for the
        # species, joined up into the crown (props_trees.py, Claude B)
        im, _, _ = CO.old_sprite(_master(recipe['master']), raw=True)
        img, anc, a, ex = PT.tree_sprite(np.asarray(im), D, seed, recipe['trunk'])
        return img, anc, a, ex
    if paint == 'tree':
        ex = tree_dims(recipe['master'])
        img, anc, a = CO.sprite_for('tree', _master(recipe['master']), D, seed, ex)
        return img, anc, a, ex
    if paint == 'foliage':
        img, anc, a = CO.sprite_for('bush', _master(recipe['master']), D, seed, {})
        return img, anc, a, None
    if paint == 'boulder':
        img, anc, a = P4.boulder4(D, recipe['size'][0], recipe['size'][1], seed=seed, fam=recipe.get('fam', 'stone'))
    elif paint == 'standing_stone':
        img, anc, a = PS.standing_stone4(D, recipe['size'][0], recipe['size'][1], seed=seed,
                                         fam=recipe.get('fam', 'stone'))
    elif paint == 'stump':
        img, anc, a = P4.stump4(D, seed=seed)
    elif paint == 'log':
        img, anc, a = P4.log4(D, length=recipe.get('length', 54), seed=seed)
    elif paint == 'bench':
        img, anc, a = P4.bench4(D, seed=seed)
    else:
        raise KeyError(paint)
    x0, y0, x1, y1 = CO._bbox(a)
    return img, ((x0 + x1) / 2, y1), a, None


# ------------------------------------------------------------------------------------------------
def terrain(plan: dict, layers: dict) -> tuple:
    """The ground codes before shadows: lawn, light, paths, places, water, rock."""
    W, H = plan['screen']['w'], plan['screen']['h']
    w, h = int(W * D), int(H * D)
    cv, _hp, _occ = SC.render()
    cv = cv[:h, :w].copy()
    layers['lawn'] = cv.copy()
    pl = plan['places']
    g = pl['glade']
    sun(cv, blob(*g['at'], *g['r'], seed=g['seed'], rough=g['rough'], w=w, h=h), heart=10 ** 6, fade=P(3))
    s = pl['sun']
    sun(cv, blob(*s['at'], *s['r'], seed=s['seed'], rough=s['rough'], w=w, h=h), heart=P(4), fade=P(2))
    for (lx, ly, rx, ry) in pl['light_pools']:
        sun(cv, blob(lx, ly, rx, ry, seed=int(lx * 7 + ly), rough=0.3, w=w, h=h), heart=P(5), fade=P(2))
    for p in plan['paths']:
        SC.worn2(cv, [tuple(q) for q in p['points']], hw0=p['radius'] - 2.0)
    co, ci = pl['circle_out'], pl['circle_in']
    ring = blob(*co['at'], *co['r'], seed=co['seed'], rough=co['rough'], w=w, h=h) & \
        ~blob(*ci['at'], *ci['r'], seed=ci['seed'], rough=ci['rough'], w=w, h=h)
    trodden(cv, ring)
    layers['places'] = cv.copy()
    wm = texels(mask_rle(plan['water']['water_rle'], W, H))
    rock = texels(mask_rle(plan['rock']['rock_rle'], W, H))
    scree(cv, plan['rock']['talus']['depth'], wm)
    for b in sorted(plan['rock']['talus']['boulders'], key=lambda b: b['at'][1]):
        boulder(cv, b['at'][0], b['at'][1], b['size'][0], b['size'][1], b['seed'], moss=b['moss'])
    WA.paint(cv, wm)
    br = pl['bridge']
    footbridge(cv, br['x0'], br['w'], br['y0'], br['y1'], wm)
    for b in sorted(plan['rock']['heap'], key=lambda b: b['at'][1]):
        boulder(cv, b['at'][0], b['at'][1], b['size'][0], b['size'][1], b['seed'], moss=b['moss'])
    f = plan['water']['fall']
    WA.wet_rock(cv, f['x0'], f['w'], f['y0'] - 2, f['y1'])
    WA.fall(cv, f['x0'], f['w'], f['y0'], f['y1'], seed=f.get('seed', 11))
    SC.reeds(cv)
    layers['water'] = cv.copy()
    # no speckle: a lone pixel takes its most common neighbour (outlines and water excepted)
    keep = (cv % 8 >= 6) | np.isin(cv // 8, [FI['water'], FI['water_warm'], FI['water_cool']])
    for _ in range(2):
        Pd = np.pad(cv, 1, mode='edge')
        nb = np.stack([Pd[:-2, 1:-1], Pd[2:, 1:-1], Pd[1:-1, :-2], Pd[1:-1, 2:]])
        lone = (cv != nb[0]) & (cv != nb[1]) & (cv != nb[2]) & (cv != nb[3]) & ~keep & (cv >= 0)
        for y, x in zip(*np.nonzero(lone)):
            v = list(nb[:, y, x])
            cv[y, x] = max(set(v), key=v.count)
    return cv, wm, rock


def build() -> Zone:
    plan, biome = ctx.PLAN, ctx.BIOME
    layers = {}
    cv, wm, rock = terrain(plan, layers)
    G = CO.ground_from_codes(cv, D)
    h, w = cv.shape
    recipes = biome['recipes']
    sprites, objects, things, casts, tcasts = {}, [], [], [], []
    for k, kind in enumerate(sorted({o[1] for o in plan['objects']})):
        sprites[kind] = sprite(kind, recipes[kind], 700 + k)
    for (oid, kind, x, y, ow, oh) in plan['objects']:
        img, anc, a, ex = sprites[kind]
        fx, fy = x + ow / 2.0, y + oh                     # the 1x object's foot
        at = (fx * D, fy * D)
        things.append((fy, img, anc, at))
        if ex is not None:
            tcasts.append(CO.tree_shadow(fx, fy, ex, D, w, h))
        else:
            casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
        bx, by = (at[0] - anc[0]) / D, (at[1] - anc[1]) / D
        objects.append((oid, kind, (bx, by, img.width / D, img.height / D)))
    # low plants baked into the ground: ferns, the fairy ring, fallen leaves
    low = []
    for (x, y, seed, size) in plan['dressing']['ferns']:
        img, anc, a = P4.fern4(D, seed=seed, size=size * 0.8)
        x0, y0, x1, y1 = CO._bbox(a)
        anc = ((x0 + x1) / 2, y1)
        at = (x * D, y * D)
        low.append((y, img, anc, at, True))
        casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
    fr = plan['places']['fairy_ring']
    img, anc, a = P4.mushroom_ring4(D, w=int(fr['r'][0] * 2.6), h=int(fr['r'][1] * 2.4), seed=85)
    x0, y0, x1, y1 = CO._bbox(a)
    anc = ((x0 + x1) / 2, y1)
    at = (fr['at'][0] * D, (fr['at'][1] + fr['r'][1]) * D)
    low.append((fr['at'][1] + fr['r'][1], img, anc, at, True))
    rng = np.random.default_rng(421)
    for (x, y, _k) in plan['dressing']['leaves']:
        limg = CO.fallen_leaf(D, rng)
        low.append((y - 30, limg, (limg.width / 2, limg.height), (x * D, y * D), False))
    CO.cast_shadows(G, casts, tcasts, things + [(l[0], l[1], l[2], l[3]) for l in low if l[4]], D)
    ground = G.rgba()
    for (_y, im, an, at_, _c) in sorted(low, key=lambda t: t[0]):
        CO.paste(ground, im, an, at_)
    layers['ground'] = ground
    # the moving water: frames of only the changing texels
    codes = (G.fam.astype(np.int32) * 8 + G.tone).astype(np.int32)
    still = np.zeros_like(wm)
    for (x0, y0, x1, y1) in plan['water'].get('still', []):
        still[P(y0, 0):P(y1, 0), P(x0, 0):P(x1, 0)] = True
    moving = wm.copy()
    if plan['water'].get('animate'):
        box = np.zeros_like(wm)
        x0, y0, x1, y1 = plan['water']['animate']
        box[P(y0, 0):P(y1, 0), P(x0, 0):P(x1, 0)] = True
        moving &= box
    frames = animate.water(codes, moving, still & moving, D)
    flow = animate.pack(frames)
    return Zone(ground=ground, objects=objects, sprites={k: v[0] for k, v in sprites.items()}, flow=flow, night=None,
                layers=layers, codes=codes)


def preview(z: Zone) -> Image.Image:
    """Everything composed as the game shows it (objects sorted by their feet)."""
    img = z.ground.copy()
    for (_oid, kind, (bx, by, bw, bh)) in sorted(z.objects, key=lambda o: o[2][1] + o[2][3]):
        sp = z.sprites[kind]
        X, Y = int(round(bx * D)), int(round(by * D))
        sx, sy = max(0, -X), max(0, -Y)
        img.alpha_composite(sp.crop((sx, sy, sp.width, sp.height)), (X + sx, Y + sy))
    return img

