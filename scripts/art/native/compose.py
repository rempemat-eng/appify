"""r1 (21 Oct, Matt via the coordinator): one scene, one design per object, three levels.

The 1x is the master design. Every object at 1.5x and 2x is the same object (props4 draws the
1x sprite's design natively with more detail); the 1x keeps its own sprites, mapped onto the
house palette (one palette for all levels), the oak's and small tree's trunks repaired (no sawn
collar, no slots). One shadow rule at every level: each object's silhouette projected east and
down in world units, two ramp tones down with a one-tone rim, solid (it flattens the ground's
texture), plus a contact line; the ground is the c-tiles port's codes at every level.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import ctx
from . import raster as pk
from . import props as P4
from . import chars
from . import ground as GR
from . import foliage as F5
from . import terrain as TER
from .palette import FAMS, C

MASTERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'masters')

FOLIAGE = ('bush', 'tree', 'oak')
LEAVES_PER_TREE = 7     # r6: fallen leaves under each tree
# r7 style (the biome's style.foliage and style.lawn): readable clumps per crown, the dressing
# tufts' size range, the calm untufted lawn round crowns, bushes and trunk bases (world px)
_ST = ctx.BIOME.get('style', {})
CLUMPS = dict(_ST.get('foliage', {}).get('clumps', dict(oak=6, tree=5, bush=3)))
TUFT_SIZES = tuple(_ST.get('lawn', {}).get('tuft_sizes', (0.8, 1.4)))
CALM_BAND = _ST.get('lawn', {}).get('calm_band', 4.0)
BUSH_MASTER = 'zones_props_bush.png'

SHADOW = tuple(ctx.BIOME['shadow']['project'])   # one projection for every object, in world units


# ------------------------------------------------------------------------------------------------
# one palette: the 1x sprites mapped onto the house ramps
_PAL = None


def _palette():
    global _PAL
    if _PAL is None:
        cols = set()
        for f in pk.RAMPS:
            for t in range(7):
                cols.add(pk.rgb(f, t))
        cols.add(pk.ink())
        _PAL = np.array(sorted(cols), float)
    return _PAL


def to_house(img: Image.Image) -> Image.Image:
    a = np.asarray(img.convert('RGBA')).copy()
    m = a[..., 3] > 0
    px = a[m][:, :3].astype(float)
    P = _palette()
    uniq, inv = np.unique(px, axis=0, return_inverse=True)
    d = ((uniq[:, None, :] - P[None, :, :]) ** 2).sum(-1)
    near = P[d.argmin(1)]
    a[m, :3] = near[inv.ravel()].astype(np.uint8)
    a[..., 3] = np.where(m, 255, 0)
    return Image.fromarray(a, 'RGBA')


def fix_trunk(img: Image.Image) -> Image.Image:
    """The 1x tree trunks: no sawn collar or checker ring under the crown, no light slots; a
    straight trunk lit on its west band, a dark band right under the crown."""
    a = np.asarray(img.convert('RGBA')).astype(int).copy()
    H, W = a.shape[:2]
    green = (a[..., 1] > a[..., 0]) & (a[..., 3] > 0)
    brown = (a[..., 0] >= a[..., 1]) & (a[..., 3] > 0)
    yb = H - 8
    cols = np.nonzero(brown[yb])[0]
    tx0, tx1 = cols.min(), cols.max()
    gy = np.nonzero(green.any(1))[0]
    y0 = int(gy.max()) + 1 if len(gy) else 0
    L = tuple(pk.rgb('timber_cool', 4))
    M = tuple(pk.rgb('timber_cool', 3))
    Dk = tuple(pk.rgb('timber_cool', 2))
    E = tuple(pk.rgb('timber_cool', 6))
    for y in range(y0, H - 3):
        for x in range(W):
            if not brown[y, x]:
                continue
            if x < tx0 or x > tx1:
                a[y, x, 3] = 0
                continue
        for x in range(tx0, tx1 + 1):
            u = (x - tx0) / max(1, tx1 - tx0)
            c = E if x == tx0 else (L if u < 0.34 else (M if u < 0.8 else Dk))
            if y - y0 < 4:
                c = E if x == tx0 else (M if u < 0.34 else Dk)
            a[y, x, :3] = c
            a[y, x, 3] = 255
        # a dark bark line here and there
    # r3: the trunk's top between the crown's lobes is in the crown's shade (no lighter collar,
    # no notch): bark there is the darkest trunk tone, and bark sticking out past the trunk's
    # sides takes the crown's underside green
    gdark = a[green][:, :3]
    if len(gdark):
        Ls = gdark @ np.array([0.299, 0.587, 0.114])
        UG = tuple(int(v) for v in gdark[np.argsort(Ls)[max(0, len(Ls) // 20)]])
        D1 = tuple(pk.rgb('timber_cool', 1))
        for y in range(max(0, y0 - 8), y0):
            for x in range(W):
                if not brown[y, x]:
                    continue
                if x < tx0 or x > tx1:
                    a[y, x, :3] = UG
                else:
                    a[y, x, :3] = E if x == tx0 else D1
    rng = np.random.default_rng(5)
    for k in range(3):
        x = int(rng.integers(tx0 + 2, tx1))
        y = int(rng.integers(y0 + 6, H - 8))
        for j in range(int(rng.integers(3, 6))):
            if y + j < H - 3:
                a[y + j, x, :3] = Dk
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def foliage_sprite(kind, old, d, seed, ex):
    """r4: bushes and tree crowns painted natively from their 1x master (foliage5); trees keep
    the native tapered trunk, the crown placed by the master's trunk foot."""
    im, anc1, a1 = old_sprite(old, raw=True)
    A = np.asarray(im)
    if kind == 'bush':
        out, _, (pad, sx, sy) = F5.paint(A, d, seed=seed, crease_depth=0.9, clumps=CLUMPS['bush'])
        return Image.fromarray(out), None, out[..., 3] > 0
    out, _, (pad, sx, sy) = F5.paint(A, d, seed=seed, blossoms=False, legs=False, crease_depth=1.5,
                                     clumps=CLUMPS['oak' if 'oak' in old else 'tree'])
    _, _, _, _, wood = F5.read_master(A)
    ys, xs = np.nonzero(wood)
    low = ys >= ys.max() - 6
    tcx, tby = xs[low].mean() + 0.5, ys.max() + 1
    tr, tanc, _ = P4.oak4(d, ex['w'], ex['h'], ex['tw'], ex['ch'], seed=seed)
    fx, fy = pad + tcx * sx, pad + tby * sy               # the trunk foot in the crown image
    # offsets so the trunk's anchor and the crown's trunk foot coincide
    oxt, oyt = 0.0, 0.0
    oxf, oyf = tanc[0] - fx, tanc[1] - fy
    mx, my = min(oxt, oxf), min(oyt, oyf)
    oxt, oyt, oxf, oyf = oxt - mx, oyt - my, oxf - mx, oyf - my
    W = int(np.ceil(max(oxt + tr.width, oxf + out.shape[1])))
    H = int(np.ceil(max(oyt + tr.height, oyf + out.shape[0])))
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    c.alpha_composite(tr, (int(round(oxt)), int(round(oyt))))
    c.alpha_composite(Image.fromarray(out), (int(round(oxf)), int(round(oyf))))
    return c, None, np.asarray(c)[..., 3] > 0


def foliage_sprite_hd(kind, old, d, seed, ex, look=None, bark='oak', scale=None):
    """Density 3 and up (25 Oct): a crown or a bush painted as leaf masses (foliage.paint_masses)
    from its 1x master. A bush sits on the ground with no stems. A tree stands on its own trunk
    (props.trunk4) whose foot is the master's trunk foot and whose top reaches 3 world px up
    under the crown, so the crown always covers it. Returns (img, None, alpha)."""
    im, _anc1, _a1 = old_sprite(old, raw=True)
    A = np.asarray(im)
    H1, W1 = A.shape[:2]
    size = (W1 * scale[0], H1 * scale[1]) if scale else None
    look = dict(look or {})
    if kind == 'bush':
        look.setdefault('form', 'bush')
        look.setdefault('clump', 7.0)
        look.setdefault('fam', 'grass_cool')
    elif 'oak' in os.path.basename(old):
        look.setdefault('clump', 11.0)
    out, _, (pad, sx, sy) = F5.paint_masses(A, d, seed=seed, look=look, size=size)
    if look.get('form') == 'bush':
        return Image.fromarray(out), None, out[..., 3] > 0
    # the trunk's foot and width from the master: its opaque, non-green pixels in the bottom rows
    a8 = A.astype(int)
    al = a8[..., 3] > 0
    green = al & (a8[..., 1] > a8[..., 0] + 4)
    yb = int(np.nonzero(al.any(1))[0].max())
    rows = slice(max(0, yb - 5), yb - 1) if yb > 6 else slice(yb, yb + 1)
    base = al[rows] & ~green[rows]
    cols = np.nonzero(base.any(0))[0]
    if not len(cols):
        cols = np.nonzero(al[yb])[0]
    tcx = (cols.min() + cols.max() + 1) / 2.0
    tw = ex.get('tw') or max(2.0, (cols.max() - cols.min() + 1) * 0.8)
    fx, fy = pad + tcx * sx, pad + (yb + 1) * sy                 # the trunk foot in the crown image
    crown = F5.LAST_MASS['mass']
    sm_ = F5.LAST_MASS.get('strands')
    if d >= 2.5 and sm_ is not None and sm_.shape == out.shape[:2]:
        # a weeping crown's strands stop above the ground: none hangs past the trunk's foot
        cut = np.zeros_like(sm_)
        cut[max(0, int(fy - 2 * d)):] = True
        out = out.copy()
        out[sm_ & cut] = 0
    half = max(1, int(tw * d / 2))
    band = crown[:, max(0, int(fx) - half):int(fx) + half + 1]
    bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
    cb = min(bots) if bots else fy - 10 * d          # the crown's highest underside over the trunk
    length = max(4.0, (fy - cb) / d + 3.0)
    tr, tanc, _ = P4.trunk4(d, length=length, trunk_w=tw, seed=seed, bark=bark,
                            flare=ex.get('flare', 1.0 if tw >= 5 else 0.0), hollow=ex.get('hollow', False))
    oxt, oyt = 0.0, 0.0
    oxf, oyf = tanc[0] - fx, tanc[1] - fy
    mx, my = min(oxt, oxf), min(oyt, oyf)
    oxt, oyt, oxf, oyf = oxt - mx, oyt - my, oxf - mx, oyf - my
    W = int(np.ceil(max(oxt + tr.width, oxf + out.shape[1])))
    H = int(np.ceil(max(oyt + tr.height, oyf + out.shape[0])))
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    c.alpha_composite(tr, (int(round(oxt)), int(round(oyt))))
    c.alpha_composite(Image.fromarray(out), (int(round(oxf)), int(round(oyf))))
    if ex.get('trunk_shade'):
        # (the Crossroads' trees, 27 Oct) the crown's shadow on its trunk: the bark just under the
        # crown two tones down for 3 world px, one tone for 3 more, along its own ramp
        c = _shade_trunk(c, d)
    return c, None, np.asarray(c)[..., 3] > 0


def _shade_trunk(img, d):
    """The bark under a crown in its shade: in each trunk column, the pixels for 4 world px below
    the crown's lowest leaf a tone down along their own house ramp (the bark's texture kept)."""
    from .palette import RAMPS
    a = np.asarray(img).copy()
    al = a[..., 3] > 0
    rgbi = a[..., :3].astype(int)
    green = al & (rgbi[..., 1] > rgbi[..., 0] + 4)
    bark = al & ~green
    look = {}
    for f in RAMPS:
        for t in range(6):
            look[tuple(pk.rgb(f, t))] = (f, t)
    for x in np.nonzero(bark.any(0))[0]:
        gy = np.nonzero(green[:, x])[0]
        by = np.nonzero(bark[:, x])[0]
        if not len(gy) or not len(by):
            continue
        y0 = gy.max() + 1
        for y in range(y0, min(a.shape[0], y0 + int(round(4 * d)))):
            if not bark[y, x]:
                continue
            k = look.get(tuple(int(v) for v in a[y, x, :3]))
            if k:
                a[y, x, :3] = pk.rgb(k[0], max(1, k[1] - 1) if k[1] >= 1 else 0)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def ctiles_bush(d, w, h, seed):
    """The c-tiles shrubs: the 1x master bush's design at their own size (no stubs, no
    blossoms), painted the same way at every level."""
    im, _, _ = old_sprite(BUSH_MASTER, raw=True)
    A = np.asarray(im)
    _, _, fol, _, wood = F5.read_master(A)
    ys = np.nonzero(fol.any(1))[0]
    A = A[:ys.max() + 1]                    # the foliage only (the stubs stay off)
    out, _, _ = F5.paint(A, d, seed=seed, size=(w, h), blossoms=False, legs=False, crease_depth=0.5)
    return Image.fromarray(out), out[..., 3] > 0


def old_sprite(name, raw=False):
    im = Image.open(os.path.join(MASTERS, name)).convert('RGBA')
    if 'oak' in name or 'tree_small' in name:
        im = fix_trunk(im)
    im = to_house(im)
    if 'props_oak' in name:
        im = Image.fromarray(F5.relight_1x(np.asarray(im)))   # r5: the oak lit from the upper left
    if not raw and ('oak' in name or 'tree_small' in name or 'props_bush' in name):
        im = Image.fromarray(F5.edge_1x(np.asarray(im)))     # r4: foliage closes in its own dark green
    a = np.asarray(im)[..., 3] > 0
    ys, xs = np.nonzero(a)
    anc = ((xs.min() + xs.max() + 1) / 2, ys.max() + 1)
    return im, anc, a


def _bbox(a):
    ys, xs = np.nonzero(a)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def new_sprite(kind, d, seed, ex):
    if kind in ('oak', 'tree'):
        raise ValueError('a crown is painted from its 1x master (foliage_sprite); give the prop a master')
    elif kind == 'bush':
        img, anc, a = P4.bush4(d, ex.get('w', 32), ex.get('h', 25), seed=seed, flowers=ex.get('flowers', True),
                               stems=ex.get('stems', True))
    elif kind == 'bench':
        img, anc, a = P4.bench4(d, seed=seed)
    elif kind == 'lantern':
        img, anc, a = P4.lantern4(d)
    elif kind == 'signpost':
        img, anc, a = P4.signpost4(d, seed=seed)
    elif kind == 'fence':
        img, anc, a = P4.fence4(d, ex.get('length', 66), seed=seed)
    elif kind == 'gateleaf':
        img, anc, a = P4.gateleaf4(d)
    elif kind == 'fence_side':
        img, anc, a = P4.fence_side4(d, ex.get('length', 36), seed=seed, top_post=ex.get('top_post', True),
                                     bottom_post=ex.get('bottom_post', True), rail_end=ex.get('rail_end', 0.0))
    elif kind == 'stump':
        img, anc, a = P4.stump4(d, seed=seed)
    elif kind == 'log':
        img, anc, a = P4.log4(d, seed=seed)
    elif kind == 'mushrooms':
        img, anc, a = P4.mushroom_ring4(d, seed=seed)
    elif kind == 'boulder':
        img, anc, a = P4.boulder4(d, seed=seed)
    elif kind == 'fern':
        img, anc, a = P4.fern4(d, seed=seed, size=ex.get('size', 27 / 22))
    elif kind == 'post':
        img, anc, a = P4.post4(d)
    else:
        raise KeyError(kind)
    return img, anc, a


def sprite_for(kind, old, d, seed, ex):
    """(img, anchor, alpha) at density d; the anchor is where the 1x sprite's anchor is: the
    bottom centre of its box (the fence: its west post)."""
    if d >= F5.HD and old and kind in FOLIAGE:
        img, anc, a = foliage_sprite_hd(kind, old, d, seed, ex, ex.get('crown'), ex.get('bark', 'oak'), ex.get('scale'))
        x0, y0, x1, y1 = _bbox(a)
        return img, ((x0 + x1) / 2, y1), a
    if d != 1 and old and kind in FOLIAGE:
        img, anc, a = foliage_sprite(kind, old, d, seed, ex)
        x0, y0, x1, y1 = _bbox(a)
        return img, ((x0 + x1) / 2, y1), a
    img, anc, a = new_sprite(kind, d, seed, ex)
    x0, y0, x1, y1 = _bbox(a)
    if kind == 'fence':
        anc = (x0 + 3 * d, y1)
    elif kind in ('fence_side', 'post', 'lantern'):
        anc = (anc[0], y1)
    elif kind == 'gateleaf':
        anc = (x1, y1)
    else:
        anc = ((x0 + x1) / 2, y1)
    return img, anc, a


# ------------------------------------------------------------------------------------------------
def shadow_mask(alpha, anchor, d, W, H, at, kx, ky):
    return _shadow_mask(alpha, anchor, d, W, H, at, kx, ky)


def tree_shadow(x, y, ex, d, W, H):
    """A tree's shadow in world units (the same at every level): a round blob for the crown,
    thrown east and down by the one projection, and the trunk's band joining the foot to it with
    square ends (no chevron)."""
    kx, ky = SHADOW
    hc = ex['h'] - ex['ch'] / 2.0
    cx, cy = x + kx * hc, y + ky * hc
    rx, ry = ex['w'] * 0.44, ex['w'] * 0.18
    Y, X = np.mgrid[0:H, 0:W]
    wx, wy = (X + 0.5) / d, (Y + 0.5) / d
    m = ((wx - cx) / rx) ** 2 + ((wy - cy) / ry) ** 2 <= 1.0
    # the trunk band: from the foot along the projection, as wide as the trunk
    ux, uy = kx, ky
    L = np.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    t = (wx - x) * ux + (wy - y) * uy
    n = np.abs(-(wx - x) * uy + (wy - y) * ux)
    m |= (t >= -0.5) & (t <= np.hypot(cx - x, cy - y)) & (n <= ex['tw'] * 0.5)
    return m


NOCONTACT = set()
LAST = {}          # the last build's terrain codes (the lawn measure reads them)


def fallen_leaf(d, rng):
    """r6: a fallen leaf, 2 x 1.5 world px: a lit half and a dark half, warm green or autumn."""
    w, h = max(2, int(round(2.0 * d))), max(1, int(round(1.4 * d)))
    a = np.zeros((h, w, 4), np.uint8)
    fam = ['leaf_warm', 'brass', 'leaf_warm', 'grass_warm'][int(rng.integers(0, 4))]
    for y in range(h):
        for x in range(w):
            if (x == 0 or x == w - 1) and (y == 0 or y == h - 1) and w > 2:
                continue
            a[y, x, :3] = pk.rgb(fam, 4 if (x + y) < (w + h) / 2 - 1 else 2)
            a[y, x, 3] = 255
    return Image.fromarray(a)


def build(d: float, frame: int = 1):
    """The scene at density d from the plan (ctx.PLAN), the biome (ctx.BIOME) and the kit:
    the terrain canvas, the props, the dressing plants, the walkers, one shadow rule, contact
    lines. Returns an RGBA picture of the screen."""
    plan = ctx.PLAN
    NOCONTACT.clear()    # ids are only meaningful within one build (CPython reuses them)
    codes, _items, _tufts = TER.canvas()
    LAST['codes'] = screen_crop(codes, d)
    Hs, Ws = LAST['codes'].shape
    # r7: the sprites first, so the lawn round crowns, bushes and trunk bases can be calmed
    sprites = [sprite_for(pr['kind'], pr.get('master'), d, pr['seed'], pr.get('extra', {})) for pr in plan['props']]
    pitems = list(plant_items())
    bushes = {j: ctiles_bush(d, w, h, seed) for j, (kind, x, y, w, h, seed, extra) in enumerate(pitems) if kind == 'bush'}
    sil = np.zeros((Hs, Ws), bool)
    for pr, (img, anc, a) in zip(plan['props'], sprites):
        if pr['kind'] in ('oak', 'tree', 'bush'):
            _stamp(sil, a, anc, (pr['foot'][0] * d, pr['foot'][1] * d))
    for j, (img, a) in bushes.items():
        kind, x, y, w, h, seed, extra = pitems[j]
        x0, y0, x1, y1 = _bbox(a)
        _stamp(sil, a, ((x0 + x1) / 2, y1), ((x + w / 2) * d, (y + h) * d))
    calm = calm_band(sil, d)
    LAST['codes'] = calm_lawn(LAST['codes'], calm)
    G = ground_from_codes(LAST['codes'], d)
    W, H = G.w, G.h
    things, shadows, small_sh, tshadows = [], [], [], []
    for i, pr in enumerate(plan['props']):
        kind, (x, y), old, sh, ex = pr['kind'], pr['foot'], pr.get('master'), pr['shadow'], pr.get('extra', {})
        img, anc, a = sprites[i]
        at = (x * d, y * d)
        things.append((y, img, anc, at))
        if sh and kind in ('oak', 'tree'):
            tshadows.append(tree_shadow(x, y, ex, d, W, H))
            # r6: a few fallen leaves on the ground under the crown
            rl = np.random.default_rng(int(x * 7 + y))
            for _ in range(LEAVES_PER_TREE):
                lx, ly = x + rl.uniform(-0.45, 0.6) * ex['w'], y + rl.uniform(-4, 9)
                limg = fallen_leaf(d, rl)
                things.append((ly - 30, limg, (limg.width / 2, limg.height), (lx * d, ly * d)))
                NOCONTACT.add(id(limg))
        elif sh and kind == 'lantern' and d != 1:
            # r4: a thin object's shadow is projected at 1x and scaled, so it covers the same
            # ground in world units at every level
            # r7: the 1x silhouette (world units) is scaled up first and projected at this density,
            # so the shadow covers the same ground at every level without 2 px stair-steps
            im1, anc1, a1 = old_sprite(old)
            az = ndi.zoom(a1.astype(np.uint8), d, order=0).astype(bool)
            shadows.append(shadow_mask(az, (anc1[0] * d, anc1[1] * d), d, W, H, at, *SHADOW))
        elif sh:
            shadows.append(shadow_mask(a, anc, d, W, H, at, *SHADOW))
    if True:
        # the weed at the signpost's foot, as the 1x master has it (the ground kit's tuft)
        sx_, sy_ = plan['sign_weed']
        timg = GR.tuft(d, 4242, 1.0)
        NOCONTACT.add(id(timg))
        things.append((sy_ + 0.1, timg, (timg.width / 2, timg.height - max(1, int(round(d / 2)))), (sx_ * d, sy_ * d)))
        for j, (kind, x, y, w, h, seed, extra) in enumerate(pitems):
            fx_, fy_ = int((x + w / 2) * d), int((y + h) * d) - 1
            if kind in ('tuft', 'flowers') and 0 <= fy_ < H and 0 <= fx_ < W and calm[fy_, fx_]:
                continue                                    # r7: no tufts in the calm band
            if kind == 'bush':
                img, a = bushes[j]
                x0, y0, x1, y1 = _bbox(a)
                anc = ((x0 + x1) / 2, y1)
                shk = True
            elif kind == 'fern':
                img, anc, a = P4.fern4(d, seed=seed, size=w / 22)
                x0, y0, x1, y1 = _bbox(a)
                anc = ((x0 + x1) / 2, y1)
                shk = True
            elif kind == 'tuft':
                img = tuft_variant(d, seed * 7 + j)
                anc = (img.width / 2, img.height - max(1, int(round(d / 2))))
                a = np.asarray(img)[..., 3] > 0
                shk = False
            else:
                img = P4.flowers4(d, seed * 3 + j, extra if isinstance(extra, str) else 'white', 3 + (seed % 2))
                anc = (img.width / 2, img.height - max(1, int(round(d / 2))))
                a = np.asarray(img)[..., 3] > 0
                shk = False
            foot = (x + w / 2, y + h)
            at = (foot[0] * d, foot[1] * d)
            things.append((foot[1] - 0.25, img, anc, at))
            if kind in ('tuft', 'flowers'):
                NOCONTACT.add(id(img))      # r5: no contact row under a tuft (it read as a comb)
            if shk:
                small_sh.append(shadow_mask(a, anc, d, W, H, at, *SHADOW))
    # the walkers
    ovals = []
    for w in plan['walkers']:
        fn, pad = (chars.bramble, chars.PAD) if w['who'] == 'bramble' else (chars.mossling, 3)
        fr = fn(d, w['action'], w['facing'], w['frame'])
        anc = (fr.width / 2, fr.height - max(1, int(round(pad * d / 2))))
        at = (w['foot'][0] * d, w['foot'][1] * d)
        things.append((w['foot'][1], fr, anc, at))
        ovals.append(foot_shadow(fr, anc, W, H, at, d))
    cast_shadows(G, shadows + small_sh + ovals, tshadows, things, d)
    img = G.rgba()
    things.sort(key=lambda t: t[0])
    for (_, im, an, at_) in things:
        paste(img, im, an, at_)
    return img


def cast_shadows(G, casts, tshadows, things, d):
    """The one shadow rule, on a ground canvas in codes: every cast (a mask) solid, two tones
    under the ground's own body tone with a one-tone rim (1 world px); a crown's shadow
    (tshadows) with a dappled rim; a contact line (tone 1) under every thing's foot. Only
    walkable ground takes them (not rock faces or water)."""
    # shadows: solid, two tones under the ground's own body tone, a one-tone rim (1 world px)
    H, W = G.h, G.w
    ground_px = walkable_ground(G)
    core = np.zeros((H, W), bool)
    for m in casts:
        core |= m
    rim_w = max(1, int(round(d)))
    inner = ndi.binary_erosion(core, iterations=rim_w)
    names = np.array(G.fams, dtype=object)[G.fam]
    body = np.where(np.isin(names, ['path', 'path_warm', 'path_cool', 'earth', 'earth_warm', 'earth_cool']), 4, 3)
    sel = inner & ground_px
    if d >= 2.5:
        # density 3 and up (26 Oct): the shade keeps the ground's own variation (patches, worn
        # earth, litter, tufts' roots) two tones down, so a shadow is never a one-tone rug
        G.tone[sel] = np.clip(np.minimum(G.tone[sel] - 2, body[sel]), 0, 5)
        sel = core & ~inner & ground_px
        G.tone[sel] = np.clip(np.minimum(G.tone[sel] - 1, body[sel] + 1), 0, 5)
    else:
        G.tone[sel] = np.clip(np.minimum(G.tone[sel], body[sel]) - 2, 0, 5)
        sel = core & ~inner & ground_px
        G.tone[sel] = np.clip(np.minimum(G.tone[sel], body[sel]) - 1, 0, 5)
    # r3: a crown's shadow has a dappled rim, not a rug's edge: in a band about 3 world px
    # wide, blobs of full shade, half shade and sun at leaf scale (the same in world units at
    # every level), and a few sun flecks inside
    tcore = np.zeros((H, W), bool)
    for m in tshadows:
        tcore |= m
    tcore &= ~core
    if tcore.any():
        rng = np.random.default_rng(ctx.BIOME['shadow'].get('dapple_seed', 907))
        Hw, Ww = int(np.ceil(H / d)) + 2, int(np.ceil(W / d)) + 2
        nf = ndi.gaussian_filter(rng.random((Hw, Ww)), 0.9)
        nf = (nf - nf.mean()) / nf.std()
        Y, X = np.mgrid[0:H, 0:W]
        nz = nf[(Y / d).astype(int), (X / d).astype(int)]
        dist = ndi.distance_transform_edt(tcore) / d          # world px from the edge
        band = ctx.BIOME['shadow'].get('dapple_band', 3.2)
        a_ = np.clip(dist / band, 0, 1)                      # 0 at the edge, 1 inside
        full_ = tcore & ((a_ >= 1) | (nz + 2.2 * a_ - 1.0 > 0.35))
        half_ = tcore & ~full_ & (nz + 2.2 * a_ - 1.0 > -0.55)
        fleck = tcore & (a_ >= 1) & (nz > 1.9)
        full_ &= ~fleck
        half_ |= fleck
        sel = full_ & ground_px
        G.tone[sel] = np.clip(np.minimum(G.tone[sel], body[sel]) - 2, 0, 5)
        sel = half_ & ground_px
        G.tone[sel] = np.clip(np.minimum(G.tone[sel], body[sel]) - 1, 0, 5)
    # contact lines under every object's foot
    cm = np.zeros((H, W), bool)
    for (_, im, an, at_) in things:
        if id(im) not in NOCONTACT:
            cm |= _contact(im, an, at_, W, H, d)
    G.tone[cm & ground_px] = np.minimum(G.tone[cm & ground_px], 1)


# ------------------------------------------------------------------------------------------------
# the screen, the ground canvas, shadows and contact (the pilot's settle helpers)
# ------------------------------------------------------------------------------------------------
def tuft_variant(d, seed):
    """r7: a dressing tuft whose size, green and bloom vary with its seed (up close no two read
    the same): sizes across TUFT_SIZES, one in five on the deep leaf green, one in five with a
    small bloom at a blade tip."""
    hv = (seed * 2654435761) >> 8
    lo, hi = TUFT_SIZES
    size = lo + (hi - lo) * ((hv % 97) / 96.0)
    img = GR.tuft(d, seed, size, fam='leaf' if hv % 5 == 0 else 'grass')
    if hv % 5 == 1:
        a = np.asarray(img).copy()
        ys, xs = np.nonzero(a[..., 3] > 0)
        if len(ys):
            k = int(np.argmin(ys + 0.01 * xs))
            y, x = ys[k], xs[k]
            q = max(1, int(round(d / 2)))
            a[max(0, y - q):y + q, max(0, x - q):x + q, :3] = pk.rgb('snow', 5)
            a[max(0, y - q):y + q, max(0, x - q):x + q, 3] = 255
            a[y, x, :3] = pk.rgb('brass_warm', 4)
            img = Image.fromarray(a)
    return img


def _stamp(m, alpha, anc, at):
    """Or a sprite's alpha into a screen mask, placed by its anchor at `at`."""
    ys, xs = np.nonzero(alpha)
    Y = np.round(ys - anc[1] + at[1]).astype(int)
    X = np.round(xs - anc[0] + at[0]).astype(int)
    ok = (Y >= 0) & (Y < m.shape[0]) & (X >= 0) & (X < m.shape[1])
    m[Y[ok], X[ok]] = True


def calm_band(sil, d):
    """r7: a band about CALM_BAND world px wide round the silhouettes, its outer edge wandering."""
    if not sil.any():
        return sil
    rng = np.random.default_rng(4401)
    nz = ndi.gaussian_filter(rng.random(sil.shape), 1.5 * d)
    nz = (nz - nz.mean()) / (nz.std() + 1e-6)
    dist = ndi.distance_transform_edt(~sil) / d
    return (dist <= CALM_BAND + 0.9 * nz) & ~sil


def calm_lawn(codes, calm):
    """r7: in the calm band the lawn keeps its broad patches (the body and its cool sibling at
    tone 3) and loses its marks and tufts."""
    out = codes.copy()
    fam = codes // 8
    g, gc = FAMS.index('grass'), FAMS.index('grass_cool')
    lawn = calm & (codes >= 0) & np.isin(fam, [g, gc, FAMS.index('grass_warm'), FAMS.index('leaf')]) & (codes % 8 < 6)
    out[lawn & (fam == gc)] = C('grass_cool', 3)
    out[lawn & (fam != gc)] = C('grass', 3)
    return out


def screen_crop(arr, d):
    scr = ctx.PLAN['screen']
    y0 = int(round(scr['canvas_dy'] * d))
    return arr[y0:y0 + int(round(scr['h'] * d)), :int(round(scr['w'] * d))]


def plant_items():
    """The dressing plants (bushes, ferns, tufts, flowers) in screen world px:
    (kind, top-left x, top-left y, w, h, seed, extra)."""
    dy = ctx.PLAN['screen']['canvas_dy']
    out = []
    for (yf, kind, x, y, seed, extra) in ctx.PLAN['dressing']['plants']:
        y = y - dy
        if kind == 'bush':
            out.append((kind, x, y, extra[0], extra[1], seed, extra))
        elif kind == 'fern':
            out.append((kind, x, y, 20, 16, seed, extra))
        elif kind == 'tuft':
            out.append((kind, x, y, (6, 4, 5)[seed % 3], 4, seed, extra))
        elif kind == 'flowers':
            out.append((kind, x, y, 9, 7, seed, extra))
    return out


def ground_from_codes(codes, d):
    H, W = codes.shape
    G = GR.Ground(W, H, d, fams=list(FAMS))
    G.fam = (np.where(codes >= 0, codes // 8, 0)).astype(np.int16)
    G.tone = (np.where(codes >= 0, codes % 8, 3)).astype(np.int16)
    return G


def walkable_ground(G):
    """Pixels where a cast shadow may fall: the ground families (grass, path, earth, snow), not
    rock faces or water."""
    names = np.array(G.fams, dtype=object)[G.fam]
    ok = np.isin(names, ['grass', 'grass_warm', 'grass_cool', 'path', 'path_warm', 'path_cool', 'earth',
                         'earth_warm', 'earth_cool', 'leaf', 'leaf_warm', 'leaf_cool', 'snow', 'snow_warm',
                         'snow_cool'])
    return ok & (G.tone < 6)


def _shadow_mask(alpha, anchor, d, W, H, at, kx=0.42, ky=0.2):
    ys, xs = np.nonzero(alpha)
    ax, ay = anchor
    hgt = np.maximum(0, ay - ys)
    gx = xs + kx * hgt
    gy = ay + ky * hgt - np.maximum(0, (ys - ay))
    X = np.round(gx - ax + at[0]).astype(int)
    Y = np.round(gy - ay + at[1]).astype(int)
    m = np.zeros((H, W), bool)
    ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
    m[Y[ok], X[ok]] = True
    k = max(2, int(round(2.5 * d)))
    m = ndi.binary_dilation(m, iterations=k)
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_erosion(m, iterations=k)
    return m


def foot_shadow(img, anchor, W, H, at, d):
    a = np.asarray(img)[..., 3] > 0
    ys, xs = np.nonzero(a)
    ax, ay = anchor
    low = ys >= ys.max() - max(2, int(2 * d))
    x0, x1 = xs[low].min(), xs[low].max()
    cx = (x0 + x1 + 1) / 2 + d * 0.8 - ax + at[0]
    cy = at[1] + 0.3 * d
    rx = max(3 * d, (x1 - x0 + 1) / 2 + d)
    ry = max(1.6, 1.8 * d)
    Y, X = np.mgrid[0:H, 0:W]
    return ((X + 0.5 - cx) / rx) ** 2 + ((Y + 0.5 - cy) / ry) ** 2 <= 1.0


def paste(canvas, img, anchor, at):
    canvas.alpha_composite(img, (int(round(at[0] - anchor[0])), int(round(at[1] - anchor[1]))))


def _contact(img, anchor, at, W, H, d):
    a = np.asarray(img)[..., 3] > 0
    ax, ay = anchor
    m = np.zeros((H, W), bool)
    near = int(round(2 * d))
    for x in range(a.shape[1]):
        ys = np.nonzero(a[:, x])[0]
        if not len(ys) or ys.max() < ay - near - 1:
            continue
        X = int(round(at[0] - ax + x))
        Y = int(round(at[1] - ay + ys.max() + 1))
        if 0 <= X < W and 0 <= Y < H:
            m[Y, X] = True
    return m


