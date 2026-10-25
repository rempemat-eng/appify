"""Upland ground at any density: heather moor, bracken, upland grass, scree and snow with its
lip (Claude F, lane F's kit module, to-all-kit-modules 21 Oct: the Frostline, the massif and
the Brackens).

Every painter here works on a terrain canvas of palette codes (family * 8 + tone, palette.py),
like terrain/sheets.py: colour is a family and a tone, shade and light step along the ramps,
and nothing is a literal RGB. Sizes are in world px (an adult is 25) and drawn at ctx.D art px
per world px, so the same field comes out at 1.5x and 2x with the same shapes in the same
places; smooth fields are laid out in world px (`wfield`), never per texel.

The house rules from the perfected scene, as they apply here:
- calm ground with detail in clusters (no lone pixels: `tidy`), detail as placed things;
- heather and bracken as drifts of small mounds and fronds with lit tops on a calm base, never
  speckle; the drifts' edges frayed by whole mounds, not ruled;
- stones in the pixel-art manner of the kit's loose rock (decals.lump_px: stone_paint's ramp,
  a dark lower-right edge, a lit upper-left), larger towards the foot of a scree fan, each
  with a contact shade thrown east and down;
- snow as one calm plane (sheets.snow_sheet) with a cornice over a rim: a lit top, a scalloped
  overhang, a blue shade under it and a few icicles; frayed into the grass where it thins.

Families (all on the code palette): heather in dusk (mauve), earth_warm and earth (brown),
berry (the flowering tips), bilberry in leaf; bracken in grass_warm and leaf_warm with earth_warm
dead fronds; grit and scree in crag, crag_cool and stone; snow in snow and snow_cool with sky
for the ice. The biome data is scripts/art/biomes/moor.json and highland.json.

    python3 -m scripts.art.native.upland [OUT_DIR] [DENSITY]   the swatch (2x beside the golden; 3x alone)
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from scipy import ndimage as ndi
from scipy.special import ndtri

from . import ctx
from .palette import C, FI, step


def _rng(seed):
    return np.random.default_rng(seed)


def _z(a):
    return (a - a.mean()) / (a.std() + 1e-9)


def wfield(H, W, sig, seed):
    """A smooth field laid out in world px (the same at every density), sampled at art px; mean
    0, deviation 1. H and W are in art px, sig in world px."""
    D = ctx.D
    Hw, Ww = int(math.ceil(H / D)) + 8, int(math.ceil(W / D)) + 8
    a = _z(ndi.gaussian_filter(_rng(seed).random((Hw, Ww)), sig, mode='wrap'))
    yy, xx = np.mgrid[0:H, 0:W]
    return ndi.map_coordinates(a, [(yy + 0.5) / D + 4, (xx + 0.5) / D + 4], order=1)


def tidy(code, keep=None, passes=2):
    """No lone pixels: a pixel unlike all four neighbours takes its upper neighbour (the
    sheets' rule), outside `keep`."""
    for _ in range(passes):
        P_ = np.pad(code, 1, mode='edge')
        nb = [P_[:-2, 1:-1], P_[2:, 1:-1], P_[1:-1, :-2], P_[1:-1, 2:]]
        lone = (code != nb[0]) & (code != nb[1]) & (code != nb[2]) & (code != nb[3]) & (code >= 0)
        if keep is not None:
            lone &= ~keep
        code = np.where(lone, nb[0], code)
    return code


def _disc(cy, cx, ry, rx, H, W):
    """Pixels of an ellipse (art px), clipped to the canvas, as (ys, xs, u, v) with u, v the
    normalised offsets (-1..1)."""
    y0, y1 = max(0, int(cy - ry - 1)), min(H, int(cy + ry + 2))
    x0, x1 = max(0, int(cx - rx - 1)), min(W, int(cx + rx + 2))
    if y0 >= y1 or x0 >= x1:
        return (np.zeros(0, int),) * 2 + (np.zeros(0),) * 2
    yy, xx = np.mgrid[y0:y1, x0:x1]
    u, v = (xx + 0.5 - cx) / max(rx, 0.5), (yy + 0.5 - cy) / max(ry, 0.5)
    m = u * u + v * v <= 1.0
    return yy[m], xx[m], u[m], v[m]


# ------------------------------------------------------------------------------------------------
# heather moor and bracken
# ------------------------------------------------------------------------------------------------
def bloom_share(f):
    """The share of heather mounds in flower (mauve) for a flowering field value f: a quarter
    on average, up to about a half where the drift blooms, so the moor reads purple-brown."""
    return 0.25 + 0.2 * np.tanh(f)


def hummock(code, cy, cx, rx, ry, rng, fams=('leaf_warm', 'earth_warm'), bloom=0.3, flower='dusk',
            dark='leaf', under=None):
    """One heather hummock in the kit's foliage manner (foliage.py): a low dome of overlapping
    leaf stamps, darker stamps first so lit ones overlap them, each in the tone of the dome's
    light under its centre (lit upper left, pockets of dark stamps low on the right), closed
    by its darkest tone on the lower right. Ling is dark olive foliage (the pockets in `dark`,
    the body in `fams`); a hummock in flower (chance `bloom`) has its lit cap in mauve
    (`flower`) with berry tips in clusters; a contact shade a tone down on the ground east and below it. cy is
    the hummock's foot row, rx and ry its half width and height in art px."""
    from .foliage import STAMPS
    H, W = code.shape
    D = ctx.D
    small = STAMPS['small'] if D >= 1.75 else STAMPS['tiny']
    oy = cy - ry                      # the dome's centre
    # contact shade on the ground: east and down
    ys, xs, u, v = _disc(cy - ry * 0.25 + 0.5 * D, cx + 0.8 * D, ry * 0.55, rx * 1.02, H, W)
    ok = (code[ys, xs] >= 0) & (code[ys, xs] % 8 < 6)
    if under is not None:
        ok &= under[ys, xs]
    code[ys[ok], xs[ok]] = step(code[ys[ok], xs[ok]], -1)
    stamps = []
    n = int(max(6, rx * ry * 0.35))
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.random())
        u, v = r * math.cos(a), r * math.sin(a) * 0.95
        y, x = oy + v * ry, cx + u * rx
        light = -(u * 0.62 + v * 0.78) * 0.85 + 0.35 * math.sqrt(max(0.0, 1 - r * r)) + rng.normal(0, 0.18)
        stamps.append((light, y, x))
    stamps.sort()
    base_fam = fams[int(rng.integers(0, len(fams)))]
    in_flower = rng.random() < bloom
    for light, y, x in stamps:
        t = 1 if light < -0.45 else (2 if light < 0.05 else (3 if light < 0.5 else 4))
        st = small[int(rng.integers(0, len(small)))]
        if t <= 1:
            fam = dark                                   # the pockets: dark foliage
        elif t >= 3 and in_flower and rng.random() < 0.8:
            fam, t = flower, min(t, 4)                   # the lit cap in flower
        else:
            fam = base_fam if rng.random() < 0.85 else fams[int(rng.integers(0, len(fams)))]
        h, w = st.shape
        Y0, X0 = int(round(y - h / 2)), int(round(x - w / 2))
        for dy in range(h):
            for dx in range(w):
                if st[dy, dx] and 0 <= Y0 + dy < H and 0 <= X0 + dx < W:
                    code[Y0 + dy, X0 + dx] = C(fam, t)
    # the silhouette closes on the lower right in the hummock's darkest tone
    ys, xs, u, v = _disc(oy, cx, ry + 0.5, rx + 0.5, H, W)
    rim = (u * u + v * v > 0.72) & ((u * 0.6 + v * 0.8) > 0.35)
    code[ys[rim], xs[rim]] = C(dark, 0)
    # the brightest flower tips on the lit cap, in clusters of two to four
    if in_flower:
        for _ in range(int(rng.integers(2, 5))):
            a = rng.uniform(math.pi, 1.6 * math.pi)
            r = rng.uniform(0.15, 0.6)
            y, x = int(oy + r * math.sin(a) * ry), int(cx + r * math.cos(a) * rx)
            for dy, dx, t in ((0, 0, 3), (0, 1, 3), (-1, 0, 4)):
                if 0 <= y + dy < H and 0 <= x + dx < W:
                    code[y + dy, x + dx] = C(flower, t) if t == 3 else C('berry', 3)


def bloom_share(f):
    """The share of heather hummocks in flower for a flowering field value f: under half on
    average, more where the drift blooms, so the moor reads purple over dark olive."""
    return float(np.clip(0.45 + 0.25 * np.tanh(f), 0.1, 0.8))


def heather(code, mask, seed=60, bilberry=0.12, size=(3.0, 5.5), gap=0.85):
    """Ling over `mask`: hummocks (hummock) packed in drifts on the ground, larger in the
    drift's middle and smaller towards its edge, the gaps between them the calm ground below
    (Eastward's tufts on a calm base, not a carpet); a few bilberry hummocks green in the shady
    part, more flowering where the drift blooms. Edits code in place."""
    D = ctx.D
    H, W = code.shape
    rng = _rng(seed)
    flower = wfield(H, W, 22.0, seed + 1)
    shade = wfield(H, W, 30.0, seed + 2)
    depth = ndi.distance_transform_edt(mask) / D
    under = ~np.isin(code // 8, [FI['path'], FI['path_warm'], FI['path_cool'], FI['water'], FI['water_cool']])
    pts = []
    Hw, Ww = H / D, W / D
    g = (size[0] + size[1]) * gap
    for gy in np.arange(0, Hw, g * 0.6):
        for gx in np.arange(0, Ww, g):
            yw = gy + rng.random() * g * 0.6
            xw = gx + rng.random() * g
            Y, X = int(yw * D), int(xw * D)
            if 0 <= Y < H and 0 <= X < W and mask[Y, X]:
                pts.append((Y, X))
    pts.sort()                         # drawn from the back (north) to the front
    for Y, X in pts:
        f = min(1.0, depth[Y, X] / 6.0)
        r = (size[0] + (size[1] - size[0]) * f * rng.uniform(0.6, 1.0)) * D
        if shade[Y, X] > 0.7 and rng.random() < bilberry * 3:
            hummock(code, Y, X, r, r * 0.62, rng, fams=('leaf', 'grass_cool'), bloom=0.0, dark='grass_cool',
                    under=under)
        else:
            hummock(code, Y, X, r, r * 0.62, rng, bloom=bloom_share(flower[Y, X]), under=under)
    return code


def bracken(code, mask, seed=80, dead=0.18, spacing=2.2):
    """Bracken over `mask`: fronds drawn over the ground (no filled base, so the drift's edge
    is fronds, not a line), each a short arch of two strokes from a dark root
    (leaf_warm), green-gold along its length and lit at the tip (grass_warm), some fronds rust
    (earth_warm, last year's). Edits code in place."""
    D = ctx.D
    H, W = code.shape
    rng = _rng(seed)
    Hw, Ww = H / D, W / D
    thick = 2 if D >= 2.5 else 1         # a frond's stroke: one texel at 2x, two at 3x
    for gy in np.arange(0, Hw, spacing * 0.7):
        for gx in np.arange(0, Ww, spacing):
            yw, xw = gy + rng.random() * spacing * 0.7, gx + rng.random() * spacing
            Y, X = int(yw * D), int(xw * D)
            if not (0 <= Y < H and 0 <= X < W) or not mask[Y, X]:
                continue
            rust = rng.random() < dead
            body = 'earth_warm' if rust else 'grass_warm'
            L = rng.uniform(2.2, 3.4) * D
            for side in (-1, 1):
                if rng.random() < 0.15:
                    continue
                ang = math.radians(rng.uniform(35, 65))
                n = max(2, int(round(L)))
                py, px = Y, X
                for i in range(1, n + 1):
                    f = i / n
                    y = int(round(Y - L * math.sin(ang) * f + L * 0.35 * f * f))
                    x = int(round(X + side * L * math.cos(ang) * f))
                    tone = 2 if f < 0.35 else (3 if f < 0.8 else 4)
                    fam = 'leaf_warm' if (f < 0.35 and not rust) else body
                    # 4-connected: step sideways on the old row, then up
                    while px != x:
                        px += 1 if x > px else -1
                        for k in range(thick):
                            if 0 <= py < H and 0 <= px + k < W:
                                code[py, px + k] = C(fam, tone)
                    py = y
                    for k in range(thick):
                        if 0 <= y < H and 0 <= x + k < W:
                            code[y, x + k] = C(fam, tone)
    return code


def moor_field(H, W, seed=60, heather_share=0.42, bracken_share=0.16, grit_share=0.04, base=None):
    """A heather moor as large as the canvas (art px H x W): sheep-bitten turf (the kit's lawn,
    sparser), heather in drifts, bracken in drifts on the deeper ground, a little grit where the
    peat is thin. Returns the code canvas and the heather mask."""
    from .terrain import sheets as SH
    D = ctx.D
    if base is None:
        base = SH.grass_field_d(int(math.ceil(W / D)), int(math.ceil(H / D)), seed, fam='grass', density=0.55)
    code = base[:H, :W].copy()
    drift = wfield(H, W, 16.0, seed + 3) + 0.35 * wfield(H, W, 5.0, seed + 4)
    hm = _z(drift) > ndtri(1 - heather_share)
    hm = ndi.binary_opening(hm, iterations=max(1, int(round(D))))
    deep = _z(wfield(H, W, 20.0, seed + 5) + 0.45 * wfield(H, W, 4.0, seed + 10)) > ndtri(1 - bracken_share)
    bm = deep & ~ndi.binary_dilation(hm, iterations=max(1, int(round(4 * D))))
    bm = ndi.binary_opening(bm, iterations=max(1, int(round(D))))
    bracken(code, bm, seed + 6)
    heather(code, hm, seed + 7)
    gm = (_z(wfield(H, W, 4.0, seed + 8)) > ndtri(1 - grit_share)) & ~hm & ~bm
    grit(code, gm, seed + 9, density=0.02)
    return tidy(code), hm


# ------------------------------------------------------------------------------------------------
# upland grass, grit and scree
# ------------------------------------------------------------------------------------------------
def upland_grass(H, W, seed=40, base=None, cool=0.45, stones=0.0004):
    """Upland grass: the kit's lawn, sparser and cooler with height (warm flecks turn cool),
    with a few small stones sitting in it."""
    from .terrain import sheets as SH
    D = ctx.D
    if base is None:
        base = SH.grass_field_d(int(math.ceil(W / D)), int(math.ceil(H / D)), seed, fam='grass', density=0.7)
    code = base[:H, :W].copy()
    rng = _rng(seed + 1)
    warm = code // 8 == FI['grass_warm']
    turn = warm & (wfield(H, W, 9.0, seed + 2) < ndtri(cool))
    code[turn] = FI['grass_cool'] * 8 + code[turn] % 8
    n = int(H * W / (D * D) * stones)
    pts = [(int(rng.integers(0, H)), int(rng.integers(0, W))) for _ in range(n)]
    stones_at(code, pts, seed + 3, size=(3.0, 5.0), fams=('stone', 'stone_cool'), under=code // 8 != FI['path'])
    return tidy(code)


def stones_at(code, pts, seed, size=(2.0, 4.0), fams=('crag', 'crag_cool', 'stone'), under=None):
    """Loose stones (the kit's pixel-art stone, decals.lump_px) with their foot at each (y, x)
    in art px, each throwing a contact shade east and down onto the ground under it."""
    from .terrain import decals as DC
    D = ctx.D
    rng = _rng(seed)
    H, W = code.shape
    for (y, x) in sorted(pts):
        w = max(3, int(round(rng.uniform(*size) * D)))
        h = max(3, int(round(w * rng.uniform(0.6, 0.8))))
        dec = DC.lump_px(w, h, int(rng.integers(0, 1 << 30)), fams=fams)
        DC.paste(code, dec, x - w // 2, y - h + 1, shadow=True, shadow_dx=max(1, int(round(D))),
                 shadow_dy=max(1, int(round(0.5 * D))), under=under)
    return code


def grit(code, mask, seed=90, density=0.05):
    """Grit where the peat or turf is thin: pale stone in two-pixel flecks over `mask` and the
    odd small stone."""
    D = ctx.D
    rng = _rng(seed)
    H, W = code.shape
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return code
    code[ys, xs] = np.where(rng.random(ys.size) < 0.5, C('stone', 3), C('stone_cool', 3))
    k = rng.random(ys.size) < 0.25
    for y, x in zip(ys[k], xs[k]):
        for dx in (0, 1):
            if x + dx < W:
                code[y, x + dx] = C('stone', 4)
    n = int(ys.size / (D * D) * density)
    sel = rng.choice(ys.size, size=min(n, ys.size), replace=False) if n else []
    stones_at(code, [(int(ys[i]), int(xs[i])) for i in sel], seed + 1, size=(1.6, 2.6))
    return code


def scree(code, mask, seed=100, coarse=(2.0, 6.5), fill=0.55, fams=('stone', 'stone_cool', 'crag_cool')):
    """A scree fan over `mask`: grey gravel between stones (its edge broken by whole patches), the stones packed close and larger
    towards the fan's foot (its southern rows), each a pixel-art stone with a contact shade;
    fine gravel in two-pixel flecks between them."""
    D = ctx.D
    H, W = code.shape
    rng = _rng(seed)
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return code
    # the gravel bed: grey, a little warmer in patches, its edge broken by whole patches
    warm = wfield(H, W, 5.0, seed + 1) > 0.6
    edge = ~ndi.binary_erosion(mask, iterations=max(1, int(round(1.5 * D))))
    keep = ~edge[ys, xs] | (wfield(H, W, 1.5, seed + 2)[ys, xs] > 0)
    ys, xs = ys[keep], xs[keep]
    code[ys, xs] = np.where(warm[ys, xs], C('stone_warm', 2), np.where(rng.random(ys.size) < 0.5,
                                                                         C('stone_cool', 2), C('stone', 2)))
    fl = rng.random(ys.size) < 0.18
    for y, x in zip(ys[fl], xs[fl]):
        for dx in (0, 1):
            if x + dx < W and mask[y, x + dx]:
                code[y, x + dx] = C('stone', 3) if rng.random() < 0.6 else C('stone_cool', 1)
    top, bot = ys.min(), ys.max()
    pts = []
    area = ys.size / (D * D)
    for _ in range(int(area * fill / 9)):
        i = int(rng.integers(0, ys.size))
        pts.append((int(ys[i]), int(xs[i])))
    pts.sort()
    for (y, x) in pts:
        f = (y - top) / max(1, bot - top)
        lo, hi = coarse
        s = lo + (hi - lo) * (0.25 + 0.75 * f) * rng.uniform(0.6, 1.0)
        stones_at(code, [(y, x)], int(rng.integers(0, 1 << 30)), size=(s, s * 1.1), fams=fams, under=mask)
    return tidy(code)


# ------------------------------------------------------------------------------------------------
# snow and its lip
# ------------------------------------------------------------------------------------------------
def snow_plane(H, W, seed=5):
    """One calm snow plane laid out in world px: snow 3 with broad swells a tone lighter, soft
    cool hollows, wind ripples as short cool dashes in drifts, and sparkles in pairs; no tile,
    so nothing repeats."""
    D = ctx.D
    rng = _rng(seed)
    n1 = wfield(H, W, 9.0, seed)
    n2 = wfield(H, W, 3.5, seed + 1)
    f = n1 + 0.35 * n2
    code = np.full((H, W), C('snow', 3))
    code[f > 0.55] = C('snow', 4)
    code[f < -1.1] = C('snow_cool', 3)
    drift = wfield(H, W, 16.0, seed + 2)
    Dp = max(1, int(round(D)))
    for _ in range(int(H * W / (D * D) * 0.012)):
        y, x = int(rng.integers(0, H)), int(rng.integers(0, W - 4 * Dp))
        if drift[y, x] < 0.2:
            continue
        L = int(rng.integers(2, 4)) * Dp
        code[y, x:x + L] = np.where(code[y, x:x + L] // 8 == FI['snow'], C('snow_cool', 3), code[y, x:x + L])
        if y > 0:
            code[y - 1, x:x + L] = np.where(code[y - 1, x:x + L] // 8 == FI['snow'], C('snow', 4), code[y - 1, x:x + L])
    for _ in range(int(H * W / (D * D) * 0.002)):
        y, x = int(rng.integers(0, H)), int(rng.integers(0, W - 1))
        if code[y, x] == C('snow', 4):
            code[y, x] = code[y, x + 1] = C('snow', 5)
    return code


def snow(code, mask, seed=5, fray=3.0):
    """Snow over `mask`: a calm snow plane (snow_plane), its edge into the ground frayed by whole
    patches a cell or so across (the ground shows through where it thins), never a ruled
    line, with a tone of cool shade along the thin edge. Returns code and the snow mask."""
    D = ctx.D
    H, W = code.shape
    sheet = snow_plane(H, W, seed)
    dist = ndi.distance_transform_edt(mask) / D
    thin = wfield(H, W, 2.5, seed + 1)
    keep = mask & ((dist > fray) | (thin > (1.0 - dist / fray) * 2.2 - 0.6))
    keep = ndi.binary_opening(keep, iterations=max(1, int(round(0.75 * D))))
    code[keep] = sheet[keep]
    rim = keep & ~ndi.binary_erosion(keep, iterations=max(1, int(round(0.5 * D))))
    code[rim] = C('snow_cool', 3)
    return tidy(code, keep=(code % 8) == 5), keep


def cornice(code, top, seed=7, over=(1.0, 2.5), icicles=0.06):
    """A snow lip along the southern rim of `top` (bool, the snow-covered tier top): the snow
    rolls over the rim in a scalloped overhang 1 to 2.5 world px deep: its lip lit along the
    top, its front in cool shade, a dark cool line under it, and a few icicles below. Edits code in place."""
    D = ctx.D
    H, W = code.shape
    rng = _rng(seed)
    below = np.zeros_like(top)
    below[1:] = top[:-1] & ~top[1:]          # the first row under the rim
    cols = np.nonzero(below.any(0))[0]
    phase = rng.random() * 6.28
    for x in cols:
        ys = np.nonzero(below[:, x])[0]
        for y0 in ys:
            depth = over[0] + (over[1] - over[0]) * (0.5 + 0.5 * math.sin(x / (5.0 * D) + phase))
            n = max(2, int(round(depth * D)))
            for i in range(n):
                y = y0 + i
                if y >= H:
                    break
                # the overhang's front in shade, its underside a dark cool line
                code[y, x] = C('snow_cool', 3) if i < n - 1 else C('snow_cool', 1)
            # the lit edge on the rim's last row of snow
            if y0 - 1 >= 0:
                code[y0 - 1, x] = C('snow', 5)
            if rng.random() < icicles and y0 + n + 1 < H:
                L = int(rng.integers(2, 5) * D / 2) + 1
                for j in range(L):
                    yy = y0 + n + j
                    if yy < H:
                        code[yy, x] = C('sky', 4) if j < L - 1 else C('snow_cool', 3)
                        if x + 1 < W and j < L // 2:
                            code[yy, x + 1] = C('sky', 3)
    return code


# ------------------------------------------------------------------------------------------------
# the swatch: one phone screen of the pilot's terrain re-grounded as upland, beside the golden
# ------------------------------------------------------------------------------------------------
UPLAND_PALETTE_FAMS = ('dusk', 'berry', 'earth', 'earth_warm', 'earth_cool', 'leaf_warm', 'grass_warm',
                       'stone', 'stone_cool', 'stone_warm', 'crag', 'crag_cool', 'crag_warm', 'snow',
                       'snow_cool', 'sky')


def swatch(out_dir: str, d: float = 2) -> str:
    """The pilot's terrain (its faces, stairs, paths and water) with its lawn re-grounded: snow
    with a cornice on the upper tier, scree at the foot of the faces, heather moor and bracken
    west of the path, upland grass with stones east of it; then the golden beside it."""
    from PIL import Image

    from . import load_biome, load_plan
    plan = load_plan('pilot')
    biome = load_biome(plan['biome'])
    ctx.configure(d, biome, plan)
    from . import compose as Cm
    from . import palette
    from . import terrain as TER
    codes, _items, _tufts = TER.canvas()
    sc = Cm.screen_crop(codes, d).copy()
    H, W = sc.shape
    fam = np.where(sc >= 0, sc // 8, -1)
    lawn = np.isin(fam, [FI['grass'], FI['grass_warm'], FI['grass_cool'], FI['leaf']])
    rock = np.isin(fam, [FI['crag'], FI['crag_warm'], FI['crag_cool']])
    path = np.isin(fam, [FI['path'], FI['path_warm'], FI['path_cool']])
    # the upper tier: lawn above the first rock in its column (the cliff's top)
    first_rock = np.where(rock.any(0), rock.argmax(0), -1)
    yy = np.arange(H)[:, None]
    upper = lawn & (first_rock[None, :] > 0) & (yy < first_rock[None, :])
    upper &= yy < int(200 * d / 2)
    lab, _n = ndi.label(upper)
    upper = lab == lab[int(10 * d), int(10 * d)] if lab[int(10 * d), int(10 * d)] else upper
    # scree: lawn just under a face (within 14 world px below rock in the same column)
    rock_above = np.zeros_like(rock)
    k = int(14 * d)
    for s in range(1, k + 1):
        rock_above[s:] |= rock[:-s]
    foot = lawn & rock_above & ~upper
    foot = ndi.binary_opening(foot, iterations=int(d))
    # west and east of the main path (its mean column)
    pc = int(np.median(np.nonzero(path[int(H * 0.5):])[1])) if path.any() else W // 2
    rest = lawn & ~upper & ~foot
    lab, n = ndi.label(rest)
    west = np.zeros_like(rest)
    for i in range(1, n + 1):
        m = lab == i
        if np.nonzero(m)[1].mean() < pc:
            west |= m
    east = rest & ~west
    moor, _hm = moor_field(H, W, seed=61)
    sc[west] = moor[west]
    up = upland_grass(H, W, seed=41)
    sc[east] = up[east]
    scree(sc, foot, seed=101)
    sc, keep = snow(sc, upper, seed=6)
    cornice(sc, keep & upper, seed=8)
    sc = tidy(sc, keep=(sc % 8 >= 5))
    pic = Image.fromarray(palette.to_rgba(sc), 'RGBA')
    allowed = list(biome['palette']) + [[f, t] for f in UPLAND_PALETTE_FAMS for t in range(6)]
    pic, _moved = palette.restrict(pic, allowed)
    os.makedirs(out_dir, exist_ok=True)
    tag = ('%g' % d).replace('.', '_')
    path_out = os.path.join(out_dir, f'upland_swatch_{tag}x.png')
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    gold = os.path.join(root, 'art', 'golden', 'pilot', f'scene_{tag}x.png')
    if not os.path.exists(gold):        # the golden is frozen at 2x: no beside-it at other densities
        pic.save(path_out)
        return path_out
    golden = Image.open(gold).convert('RGBA')
    gap = 16
    both = Image.new('RGBA', (pic.width + gap + golden.width, max(pic.height, golden.height)), (20, 18, 24, 255))
    both.alpha_composite(pic, (0, 0))
    both.alpha_composite(golden, (pic.width + gap, 0))
    both.save(path_out)
    return path_out


if __name__ == '__main__':
    import tempfile
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), 'napattack-upland')
    print(swatch(out, float(sys.argv[2]) if len(sys.argv) > 2 else 2))
