"""The land past the walkable world (docs/vision/art-faults.md, rule 13): every cell of a
region's grid that has no zone, and the ring of cells round the region, drawn as real
scenery you cannot walk on. Matt, 19 Oct: "also think of a better way to solve world
borders".

Each cell is painted from the region's own coordinates, never from a tile that repeats,
so mountains, forest, a river and the sea run on across cell edges without a seam and
no two cells look alike. Where the scenery meets a zone, it meets what that zone shows
at its edge: the harbour's and the headland's sea runs on into open sea, the river that
leaves the riverside runs on east under the trees, the meadow gives way to old forest,
the ridge's alpine slopes climb into the high peaks.

`cells(layout, region)` returns, for each such cell, a canvas of the cell plus BEYOND_SPILL all round: the
ground fills the cell, and only things that stand up (crowns, boulders, pines) reach
into the spill, so the edge against a zone is grown, not cut.

The kinds of land are fields over the region (numpy), so a whole cell paints in a
fraction of a second."""
from __future__ import annotations

import functools
import math

import numpy as np
from PIL import Image

import detail
import garden_props
import style
from materials import MATERIALS
from pixel import Canvas, noise2, smooth_noise

W, H = 320, 576
S = 20  # BEYOND_SPILL in zones.py

SN, ST, WTR = MATERIALS['snow'], MATERIALS['stone'], MATERIALS['water']
FOREST_FLOOR = ['#1A2A20', '#22382A', '#2B4430']
CANOPY = ['#122019', '#1A2C22', '#22392A', '#2E4C34', '#3E6240']
ALPINE = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
SAND = MATERIALS['sand']


def _rgb(c: str):
    return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))


# ---- noise over the region, vectorised ----------------------------------------------
def _hash(ix, iy, seed):
    v = np.sin(ix * 12.9898 + iy * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


def vnoise(X, Y, scale: float, seed: int):
    """Value noise in [0, 1] at region pixels (X, Y), smooth over `scale` pixels. The
    lattice is hashed once over the small grid of corners the points need."""
    X, Y = np.asarray(X, dtype=float), np.asarray(Y, dtype=float)
    gx, gy = X / scale, Y / scale
    x0, y0 = np.floor(gx), np.floor(gy)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    ix, iy = x0.astype(np.int64), y0.astype(np.int64)
    if ix.size == 0:
        return np.zeros(X.shape)
    bx, by = ix.min(), iy.min()
    lx, ly = np.arange(bx, ix.max() + 2), np.arange(by, iy.max() + 2)
    LX, LY = np.meshgrid(lx.astype(float), ly.astype(float))
    lat = _hash(LX, LY, seed)
    cx, cy = ix - bx, iy - by
    a, b = lat[cy, cx], lat[cy, cx + 1]
    c, d = lat[cy + 1, cx], lat[cy + 1, cx + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def wnoise(X, Y, scale: float, seed: int, warp: float = 0.36):
    """vnoise with its domain warped by a second value noise on a lattice 0.618 times as
    wide (so the two never share a period), by up to `warp` x scale px each way (`warp`
    may be an array: 0 leaves the plain noise, so a field can match a zone at its edge
    and bend away from it). A patch
    cut from it by a threshold has edges that wander, never the rows and columns of one
    square lattice, which show as blocks under the night tint (art-faults.md A6)."""
    X, Y = np.asarray(X, dtype=float), np.asarray(Y, dtype=float)
    a = 2 * warp * scale
    s2 = scale * 0.618
    dx = vnoise(X, Y, s2, seed + 7001) - 0.5
    dy = vnoise(X + 0.37 * scale, Y - 0.29 * scale, s2, seed + 7002) - 0.5
    return vnoise(X + a * dx, Y + a * dy, scale, seed)


def ridged(X, Y, scale: float, seed: int):
    return 1 - np.abs(2 * vnoise(X, Y, scale, seed) - 1)


# ---- what the land is, per region -------------------------------------------------
def _lerp_points(x, pts):
    """Piecewise-linear through (x, y) control points, flat past the ends."""
    xs, ys = zip(*pts)
    return np.interp(x, xs, ys)


# The valley's coast: where the sea begins, by region x. West of the valley it runs
# under the Halt's sea cliff (it meets the Halt's sea at the Halt's west edge, halt
# (0, 540)) and round Driftwood's west point (the Halt's farm reaches the corner at
# x -32..0, Driftwood's west rocks begin at its top), so the cells south and south-west
# of the Halt are open sea and the world's edge there is sea and cliff, never forest
# (art-faults.md A3). East of the valley it meets the headland's sea at its east edge
# (y 1531); under the zones the sea starts at their bottom edge.
VALLEY_COAST = [(-960, 1108), (-640, 1112), (-320, 1115), (-36, 1140), (-14, 1158), (-1, 1158),
                (0, 1721), (640, 1531), (760, 1490), (1000, 1420), (1280, 1400)]
# where the coast meets a zone's own shore it must not wander (region x)
COAST_ANCHORS = (-320, 0, 640)
# west of this x the coast is a low sea cliff, carried on from the Halt's (no beach)
CLIFF_COAST_X = -320
# The river that leaves the riverside at its east edge (region y 1-576 band 295-350)
# runs on east through the old forest (its centre line by region x, and its width).
# (none since 19 Oct: Claude E's V2 turns the valley's river south inside the valley, so
# nothing leaves the riverside's east edge; kept as a hook for a river that does)
VALLEY_RIVER: list = []
RIVER_HALF = 26


def valley_fields(X, Y):
    """The valley's land at region pixels: altitude (in rows of 576 px, rising north),
    sea mask and river mask."""
    alt = -Y / H + 0.55 * (vnoise(X, Y, 150, 931) - 0.5) + 0.25 * (vnoise(X, Y, 50, 932) - 0.5)
    coast = _lerp_points(X, VALLEY_COAST)
    # (away from the zones the coast wanders)
    away = np.clip(np.min([np.abs(X - a) for a in COAST_ANCHORS], axis=0) / 80, 0, 1)
    # (under the Halt it stays put, so the cell south of it is sea from its top row)
    away = np.where((X > COAST_ANCHORS[0]) & (X < COAST_ANCHORS[1]), 0, away)
    coast = coast + away * 46 * (vnoise(X, 0 * X, 70, 933) - 0.5) + away * 12 * (vnoise(X, 0 * X, 18, 934) - 0.5)
    sea = Y > coast
    if VALLEY_RIVER:
        rc = _lerp_points(X, VALLEY_RIVER) + 10 * (vnoise(X, 0 * X, 40, 935) - 0.5) * np.clip((X - 640) / 60, 0, 1)
        river = (np.abs(Y - rc) < RIVER_HALF) & (X >= 640) & (Y > -60) & (Y < 600)
    else:
        rc, river = np.zeros(np.shape(X)), np.zeros(np.shape(X), dtype=bool)
    return alt, sea, river, coast, rc


# ---- painting -----------------------------------------------------------------------
def _grid(col, row):
    """Region pixel coordinates of a cell's canvas (cell plus spill)."""
    xs = np.arange(-S, W + S) + col * W
    ys = np.arange(-S, H + S) + row * H
    return np.meshgrid(xs, ys)


def _pick(ramp, idx):
    pal = np.array([_rgb(c) for c in ramp], dtype=np.uint8)
    return pal[np.clip(idx, 0, len(ramp) - 1)]


def _mountain_rgb(X, Y, alt):
    """High country: ridged rock lit from the upper left, snow lying where it can."""
    def height(x, y):
        return (0.55 * ridged(x, y, 130, 941) + 0.3 * ridged(x, y, 46, 942)
                + 0.15 * vnoise(x, y, 13, 943)) + 0.35 * (-y / H)
    h = height(X, Y)
    lit = height(X - 2, Y - 2) - height(X + 2, Y + 2)  # > 0 faces the light (upper left)
    steep = np.abs(lit)
    # rock tones by how it faces the light, with a dark crevice line along ridge valleys
    rock_i = np.where(lit > 0.06, 3, np.where(lit > 0.015, 2, np.where(lit > -0.04, 1, 0)))
    rock_i = np.where((lit > 0.11) & (vnoise(X, Y, 3, 944) > 0.55), 4, rock_i)
    rock = _pick(ST, rock_i)
    # snow: high up, on gentle faces; less on the steepest rock
    snowy = alt - 0.75 + 0.9 * (h - 0.75) - 3.0 * np.maximum(steep - 0.05, 0)
    snow_i = np.where(lit > 0.035, 3, np.where(lit > -0.01, 2, np.where(lit > -0.05, 1, 0)))
    snow = _pick(SN, snow_i)
    out = np.where((snowy > 0)[..., None], snow, rock)
    # scree and alpine turf at the foot of the rock
    low = alt < 0.75 + 0.25 * (vnoise(X, Y, 30, 945) - 0.5)
    turf_i = np.where(lit > 0.02, 3, np.where(lit > -0.03, 2, 1))
    turf = _pick(ALPINE, turf_i)
    stones = vnoise(X, Y, 4, 946) > 0.78
    turf = np.where(stones[..., None], _pick(ST, np.where(lit > 0, 3, 2)), turf)
    out = np.where((low & (snowy <= 0))[..., None], turf, out)
    return out


def _forest_floor_rgb(X, Y):
    n = wnoise(X, Y, 9, 951)
    return _pick(FOREST_FLOOR, np.where(n > 0.62, 2, np.where(n > 0.3, 1, 0)))


def _sea_rgb(X, Y, coast):
    """Open sea in the harbour's water: deep with long swells, shallower by the shore."""
    depth = Y - coast
    n = wnoise(X, Y, 110, 961) + 0.08 * (vnoise(X, Y, 9, 965) - 0.5)
    dith = (np.abs(n - 0.5) < 0.025) & ((X + Y) % 2 == 0)
    base = np.where(depth < 14, 1, np.where((n > 0.5) ^ dith, 0, 1))
    swell = (Y + (np.sin(X / 23.0) * 4 + vnoise(X, Y, 60, 962) * 8).astype(int)) % 19
    idx = np.where((swell == 0) & (depth > 10), 2, base)
    cap = (swell == 1) & (_hash(X // 5, Y // 19, 963) > 0.82) & (depth > 18)
    rgb = _pick(WTR, idx)
    rgb = np.where(cap[..., None], np.array(_rgb('#F4F8F8'), dtype=np.uint8), rgb)
    foam = (depth >= 0) & (depth < 3)
    rgb = np.where(foam[..., None], _pick(WTR, np.full(X.shape, 4)), rgb)
    sand = (depth < 0) & (depth > -10)
    rgb = np.where(sand[..., None], _pick(SAND, np.where(depth > -4, 0, np.where(vnoise(X, Y, 3, 964) > 0.5, 2, 1))), rgb)
    return rgb


FOAM = '#EEF5F8'  # the zones' foam (valley_zones.FOAM)
SEA_OWN_X = ('halt',)  # zones that paint their sea's noise in their own x, not valley x


@functools.lru_cache(maxsize=32)
def _has_sea(zone: str) -> bool:
    """Whether a zone shows open water along any of its edges."""
    if not zone or zone == 'garden':
        return False
    g = _zone_ground(zone).astype(int)
    pal = np.array([_rgb(c) for c in WTR[:3]])  # the sea's own blues (not a snow's shade)
    for edge in (g[:, 0], g[:, W - 1], g[0, :], g[H - 1, :]):
        wet = ((edge[:, None, :] - pal[None]) ** 2).sum(-1).min(1) < 20 ** 2
        if wet.mean() > 0.15:
            return True
    return False


def _shore_sea_rgb(X, Y, d, fx: int = 0, fy: int = 0, warp=0.0):
    """The valley's sea as its zones paint theirs (valley_zones.sea): pale over the
    shallows, deepening in soft-edged bands with the distance `d` from the shore (px) to
    the open sea's deep blue with long dashed swells and the odd whitecap; foam and a
    second line of surf along the shore. Its noise is read in a zone's own frame (x + fx,
    y + fy: Driftwood and the Headland paint theirs in valley x from their own top row,
    the Halt in its own x and y), so the patches and swells run on across the seam;
    `warp` (0 at a zone's edge, rising away from it) bends the deep patches' edges (A6)."""
    y = Y + fy
    X = X + fx
    dn = d + (vnoise(X, y, 26, 979) - 0.5) * 22
    chk = ((X // 2 + y // 2) % 2) == 1
    idx = np.where(dn < 5, 3, np.where(dn < 8, np.where(chk, 3, 2), np.where(dn < 26, 2, np.where(
        dn < 32, np.where(chk, 2, 1), np.where(dn < 60, 1, -1)))))
    deep = np.where(wnoise(X, y, 40, 861, warp) > 0.55, 0, 1)
    deep = np.where((dn < 66) & chk, 1, deep)
    idx = np.where(idx < 0, deep, idx)
    sw = (y + np.trunc(np.sin(X / 23) * 4 + vnoise(X, y, 60, 862) * 8).astype(int)) % 19
    dash = (dn > 46) & (sw == 0) & (_hash(X // 9, y // 19, 864) > 0.25)
    idx = np.where(dash, np.where(dn > 56, 2, 3), idx)
    rgb = _pick(WTR, idx)
    cap = (dn > 50) & (sw == 1) & (_hash(X // 5, y // 19, 863) > 0.8)
    rgb = np.where(cap[..., None], np.array(_rgb('#F4F8F8'), dtype=np.uint8), rgb)
    # the waterline: foam on the shore, a lap of pale water, the next wave coming in
    dd = np.floor(d).astype(int)
    wob = np.trunc((vnoise(X, Y, 5, 458) - 0.5) * 3).astype(int)
    surf = vnoise(X, Y, 9, 459)
    foam = (dd <= 0) | ((dd == 1) & ((X + Y) % 3 != 0))
    lap = (dd == 2) & ((X // 2 + Y) % 3 != 0)
    wave = (dd == 6 + wob) & (surf > 0.45)
    wave2 = (dd == 7 + wob) & (surf > 0.5) & ((X + Y) % 2 == 1)
    foam_rgb = np.array(_rgb(FOAM), dtype=np.uint8)
    rgb = np.where(wave2[..., None], _pick(WTR, np.full(X.shape, 3)), rgb)
    rgb = np.where(wave[..., None], np.where(((X + Y) % 4 != 0)[..., None], _pick(WTR, np.full(X.shape, 4)), foam_rgb), rgb)
    rgb = np.where(lap[..., None], _pick(WTR, np.full(X.shape, 4)), rgb)
    return np.where(foam[..., None], foam_rgb, rgb)


@functools.lru_cache(maxsize=64)
def _edge_water(zone: str, side: str):
    """The water along one side of a zone, read from its ground: per pixel along the
    side, (depth, shore). `depth` is how far from the shore its water there is painted
    (px, from the bands of valley_zones.sea, land counting as the shore itself; a running
    median, so a swell's dash or a whitecap is not read as shallows). `shore` is how far
    in from the edge the zone's land lies (spread along the edge as a cone), or 999 where
    the zone paints its edge as open sea."""
    g = _zone_ground(zone).astype(int)
    strip = {'w': g[:, :48], 'e': g[:, W - 1:W - 49:-1],
             'n': g[:48, :].transpose(1, 0, 2), 's': g[H - 1:H - 49:-1, :].transpose(1, 0, 2)}[side]
    wet = (strip[..., 2] > strip[..., 0] + 25) | ((strip.sum(-1) > 600) & (strip[..., 2] >= strip[..., 0]))
    geo = np.where((~wet).any(1), (~wet).argmax(1), 48)
    pal = np.array([_rgb(c) for c in WTR] + [_rgb(FOAM), _rgb('#F4F8F8')])
    dist = ((strip[:, 0, None, :] - pal[None, :, :]) ** 2).sum(-1)
    depth = np.array([80, 45, 16, 3, 0, 0, 60])[dist.argmin(1)]
    depth = np.where(wet[:, 0], depth, 0)
    win = 15
    padded = np.pad(depth, win // 2, mode='edge')
    edge_d = np.median(np.lib.stride_tricks.sliding_window_view(padded, win), axis=1)
    for i in range(1, len(edge_d)):  # (open sea shoals toward land along the edge)
        edge_d[i] = min(edge_d[i], edge_d[i - 1] + 2)
    for i in range(len(edge_d) - 2, -1, -1):
        edge_d[i] = min(edge_d[i], edge_d[i + 1] + 2)
    # (land within the strip is a shore, unless the zone paints its edge as open sea)
    carry = np.where((edge_d < 45) | (geo == 0), geo, 999).astype(float)
    for i in range(1, len(carry)):  # (a shore spreads as a cone, never a stripe)
        carry[i] = min(carry[i], carry[i - 1] + 1)
    for i in range(len(carry) - 2, -1, -1):
        carry[i] = min(carry[i], carry[i + 1] + 1)
    return edge_d, carry


def _river_rgb(X, Y, rc):
    d = np.abs(Y - rc)
    idx = np.where(d > RIVER_HALF - 3, 3, np.where(vnoise(X, Y, 14, 971) > 0.6, 1, 2))
    rgb = _pick(WTR, idx)
    bank = (d > RIVER_HALF - 1)
    return np.where(bank[..., None], _pick(['#3B2E22', '#5A4632'], (Y < rc).astype(int)), rgb)


@functools.lru_cache(maxsize=1)
def _pine():
    return garden_props.pine()


def _stamp(cv: Canvas, sp, x: int, y: int):
    """Composite a sprite (a Canvas or an image) at (x, y), cut to the canvas."""
    im = sp.img if isinstance(sp, Canvas) else sp
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(cv.w, x + im.width), min(cv.h, y + im.height)
    if x1 > x0 and y1 > y0:
        cv.img.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


# ---- the forest: crowns in stands and clumps, and its edges (art-faults.md A11) ------
# Crown palettes, dark to light: the old wood's cool green, oak, beech (warmer), a
# blue-dark for crowns deep in the shade, birch (light) and autumn. The kinds grow in
# stands, with a birch or an autumn tree now and then, so the canopy reads as many trees
# of a few kinds, not one repeated scale.
OAK = ['#16241B', '#20341F', '#2E4A2A', '#40633A', '#58804A']
BEECH = ['#1B2A1C', '#2A4026', '#3C5A2E', '#557839', '#77984A']
SHADE_GREEN = ['#111D1C', '#182A28', '#22392F', '#2E4C3C', '#406552']
BIRCH_LEAF = ['#25381F', '#3D5A2C', '#5B7E3A', '#7DA04A', '#A8C26A']
CROWN_RAMPS = (CANOPY, OAK, BEECH, SHADE_GREEN, BIRCH_LEAF, garden_props.AUTUMN, MATERIALS['leaf'])
BIRCH_BARK = ['#2E2C2A', '#6E6A62', '#B9B4A6', '#DDD8CA', '#F2EFE6']
WOOD = MATERIALS['wood']
# shade where it falls past the cell on a zone's ground (drawn as an overlay there)
SHADE_INK = (0, 12, 27)  # (with these alphas it matches style.SHADOW_MUL on the turf)
SHADE_ALPHA = (0, 80, 138)


@functools.lru_cache(maxsize=1024)
def _crown_img(rx: int, k: int, pal: int = 0, r10: int = 38) -> Image.Image:
    ry = rx * 0.72
    blob = Canvas(int(rx * 2) + 14, int(ry * 2) + 14)
    style.leafy(blob, blob.w / 2, blob.h / 2, rx, ry, CROWN_RAMPS[pal], r=r10 / 10, seed=k + 3)
    return blob.img


def _crown(cv: Canvas, cx: float, cy: float, rx: float, k: int, pal: int = 0, r10: int = 38):
    """A crown of the canopy: one of a few hundred drawn crowns (by size, kind, leaf size
    and a variant), so the forest stays varied without drawing every crown afresh."""
    im = _crown_img(int(rx), k % 9, pal, r10)
    _stamp(cv, im, int(cx - im.width / 2), int(cy - im.height / 2))


def _crown_kind(gx: float, gy: float, i: int, j: int):
    """The palette and leaf size of the canopy's crown at a grid point."""
    stand = float(vnoise(np.array(gx), np.array(gy), 150, 571))
    h = noise2(i, j, 574)
    if h < 0.04:
        pal = 4  # a birch among the oaks
    elif h < 0.052:
        pal = 5  # an autumn tree
    else:
        pal = 1 if stand < 0.36 else 2 if stand < 0.52 else 0 if stand < 0.8 else 3
    return pal, 30 + int(noise2(i, j, 575) * 14)


def _trees(region: str, col: int, row: int, kind_at, room=None):
    """Crowns and pines on a jittered grid over the region, every one that reaches this
    canvas, back to front. `kind_at(x, y)` says what grows at a region point; `room(x, y)`
    (arrays) how far a crown there may reach before the forest's edge. The crowns stand
    in clumps: where a slow noise is low the canopy opens on the forest floor with a bush
    or two, where it is high the crowns are bigger and overlap more."""
    x0, y0 = col * W - S - 60, row * H - S - 60
    x1, y1 = (col + 1) * W + S + 60, (row + 1) * H + S + 60
    J, I = np.meshgrid(np.arange(math.floor(y0 / 30), math.ceil(y1 / 30) + 1),
                       np.arange(math.floor(x0 / 40), math.ceil(x1 / 40) + 1), indexing='ij')
    GX = I * 40 + (_hash(I, J, 552) - 0.5) * 28
    GY = J * 30 + (_hash(I, J, 553) - 0.5) * 22
    kinds = kind_at(GX, GY)
    clump = wnoise(GX, GY, 80, 572)
    reach = room(GX, GY) if room is not None else np.full(GX.shape, 99.0)
    out = []
    for (j, i), what in np.ndenumerate(kinds):
        gx, gy, ii, jj = float(GX[j, i]), float(GY[j, i]), int(I[j, i]), int(J[j, i])
        if what == 'crown':
            c = float(clump[j, i])
            if c < 0.2:
                if noise2(ii, jj, 576) < 0.6:  # a gap in the canopy, a bush in its shade
                    out.append((gy, gx, 'under', ('bush', 6 + int(noise2(ii, jj, 577) * 4), ii * 31 + jj, 3), 0))
                continue
            rx = 20 + noise2(ii, jj, 554) * 10 + (c - 0.5) * 14
            rx = min(rx, float(reach[j, i]) - 2)
            if rx < 10:
                continue
            pal, r10 = _crown_kind(gx, gy, ii, jj)
            out.append((gy, gx, 'crown', (rx, pal, r10), ii * 7919 + jj))
        elif what == 'pine' and noise2(ii, jj, 555) < 0.75:
            out.append((gy, gx, 'pine', 0, ii * 7919 + jj))
    return sorted(out, key=lambda t: (t[0], t[1]))


@functools.lru_cache(maxsize=512)
def _edge_tree(kind: str, size: int, seed: int, pal: int = 1):
    """A tree of the forest's front row, drawn whole: (image, ax, ay) with its trunk's
    foot at (ax, ay). 'broad' an oak or beech, 'birch' a slim white-barked birch, 'pine'
    the garden's pine, 'sapling' a young tree, 'bush' a shrub. Lit from the upper left."""
    if kind == 'pine':
        p = _pine()
        return p.img, p.pad + p.w // 2, p.pad + p.h - 1
    rnd = lambda k: noise2(seed, k, 601)  # noqa: E731
    birch = kind == 'birch'
    if kind == 'bush':
        rx = size
        ry = rx * 0.7
        cv = Canvas(int(2 * rx) + 8, int(2 * ry) + 6)
        cx, cy = cv.w / 2, ry + 3
        style.leafy(cv, cx, cy, rx, ry, CROWN_RAMPS[pal], r=2.4, seed=seed % 7 + 1, flat_bottom=0.9)
        for k in range(3):  # stems under it
            sx = int(cx - rx * 0.4 + k * rx * 0.4)
            cv.set(sx, int(cy + ry) - 1, WOOD[1]); cv.set(sx, int(cy + ry), WOOD[0])
        return cv.img, int(cx), int(cy + ry)
    if kind == 'sapling':
        rx = size
        ry = rx * 0.95
        tl = 5 + int(rnd(1) * 3)
        cv = Canvas(int(2 * rx) + 8, int(2 * ry) + tl + 6)
        cx, cy = cv.w / 2, ry + 3
        foot = int(cy + ry) + tl
        cv.vline(int(cx), int(cy), foot - int(cy), WOOD[2])
        cv.set(int(cx), foot - 1, WOOD[1])
        style.leafy(cv, cx, cy, rx, ry, CROWN_RAMPS[pal], r=1.8, seed=seed % 5 + 1)
        return cv.img, int(cx), foot
    rx = size
    ry = rx * (1.15 if birch else 0.78)
    tl = (11 if birch else 5) + int(rnd(1) * 5)       # how much trunk shows under the crown
    tw = 3 if birch else 4 + (rx > 14)
    cv = Canvas(int(2 * rx) + 14, int(2 * ry) + tl + 10)
    cx, cy = cv.w / 2, ry + 5
    foot = int(cy + ry * 0.8) + tl
    tx = int(cx - tw / 2)
    bark = BIRCH_BARK if birch else WOOD
    style.trunk(cv, tx, int(cy), foot, tw, bark)
    if birch:  # the birch's dark lenticels across the white bark
        for k in range(int(cy) + 2, foot - 3, 3):
            if noise2(seed, k, 602) > 0.4:
                cv.hline(tx + (k % 2), k, 2, BIRCH_BARK[0])
    # the crown in the zones' own manner (garden_props.canopy): a few leaf masses, each
    # lit from the upper left, built of leaf clusters, listed back to front
    if birch:
        lobes = [(cx + (rnd(2) - 0.5) * 2, cy - ry * 0.42, rx * 0.62), (cx - rx * 0.3, cy + ry * 0.12, rx * 0.58),
                 (cx + rx * 0.3, cy + ry * 0.22, rx * 0.56)]
    else:
        n = 4 + (rx > 13) + int(rnd(3) * 2)
        lobes = []
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * rnd(10 + k)) / n
            d = 0.42 + 0.18 * rnd(20 + k)
            lobes.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d * 0.9, rx * (0.48 + 0.14 * rnd(30 + k))))
        lobes.append((cx - rx * 0.08, cy - ry * 0.1, rx * 0.55))
        lobes.sort(key=lambda lb: lb[1])
    shape = garden_props.canopy(cv, lobes, CROWN_RAMPS[pal], seed=seed % 11 + 1, clumps=rx >= 11)
    # (and the trunk again from just under the crown, with the crown's shadow across it)
    under = max([y for (x, y) in shape if tx <= x < tx + tw] + [int(cy)]) + 1
    if under < foot - 3:
        style.trunk(cv, tx, under, foot, tw, bark, shape)
    cv = style.close_outline(cv)
    return cv.img, int(cx), foot


def _paint(cv: Canvas, rgb, mask):
    """Copy region pixels into the canvas where mask holds."""
    a = np.zeros(mask.shape + (4,), dtype=np.uint8)
    a[..., :3] = rgb
    a[..., 3] = np.where(mask, 255, 0)
    over = Image.fromarray(a, 'RGBA')
    cv.img.alpha_composite(over, (cv.pad, cv.pad))


OUTLINE = '#2A2630'


@functools.lru_cache(maxsize=1024)
def _peak(w: int, h: int, seed: int, snow: float) -> Image.Image:
    """A mountain in the three-quarter view, as one sprite: a rock mass rising to a
    peak (sometimes with a shoulder), its west face lit and its east face in shade
    either side of the ridge, gullies running down the fall line, a snow cap whose lower
    edge is ragged and reaches down the gullies. `snow` is how far down the cap comes
    (0 none, 1 all)."""
    rnd = lambda k: float(_hash(np.array(seed), np.array(k), 1001))  # noqa: E731
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u = (xx + 0.5) / w * 2 - 1           # -1 west .. 1 east
    v = (yy + 0.5) / h                   # 0 top .. 1 foot
    ax = (rnd(1) - 0.5) * 0.5            # where the summit stands
    # the silhouette: the main peak, and often a lower shoulder to one side
    def cone(ax_, top, half):
        span = (v - top) / max(1e-3, 1 - top)
        return (span >= 0) & (np.abs(u - ax_) <= span * half)
    jag = (vnoise(xx, yy, 5, seed * 7 + 1) - 0.5) * 0.10 + (vnoise(xx, yy, 13, seed * 7 + 2) - 0.5) * 0.10
    form = rnd(7)
    if form < 0.4:      # a massif: a broad mass with two or three summits along a crest
        body = np.zeros(u.shape, dtype=bool)
        n_tops = 2 + (rnd(8) > 0.5)
        for t in range(n_tops):
            tx = -0.55 + 1.1 * (t + 0.5) / n_tops + (rnd(10 + t) - 0.5) * 0.25
            body |= cone(tx, 0.0 if t == n_tops // 2 else 0.12 + rnd(20 + t) * 0.25, 0.62 + jag)
        ax = -0.55 + 1.1 * (n_tops // 2 + 0.5) / n_tops
    else:               # a peak, often with a lower shoulder
        body = cone(ax, 0.0, 1.0 + jag)
        if rnd(2) > 0.35:
            sx = ax + (0.55 if rnd(3) > 0.5 else -0.55)
            body |= cone(sx, 0.28 + rnd(4) * 0.18, 0.75 + jag)
    body &= v <= 1 - 0.10 * u * u        # a rounded foot
    # the ridge that splits the lit face from the shaded one wanders down from the summit
    ridge = ax + (v * (0.15 + rnd(5) * 0.2) * (1 if rnd(6) > 0.5 else -1)) + (vnoise(0 * xx, yy, 9, seed * 7 + 3) - 0.5) * 0.12
    west = u < ridge
    # gullies down the fall line (streaks that splay out from the summit)
    slope_x = (u - ax) / np.maximum(v, 0.05)
    gully = ridged(slope_x * 40 + 0 * yy, yy * 0.15, 6, seed * 7 + 4)
    deep = gully > 0.82
    # the snow's lower edge: ragged, lower in the gullies
    edge = snow * (0.55 + 0.25 * (vnoise(xx, 0 * yy, 7, seed * 7 + 5) - 0.5)) + 0.18 * snow * (gully - 0.5)
    snowy = v < edge
    rock = np.where(west, np.where(deep, 1, np.where(gully > 0.55, 3, 2)), np.where(deep, 0, 1))
    rgb = _pick(ST, rock)
    sn = np.where(west, np.where(gully > 0.7, 2, 3), np.where(deep, 0, 1))
    rgb = np.where(snowy[..., None], _pick(SN, sn), rgb)
    # a lit rim along the west skyline
    rim = body & ~np.roll(body, 1, axis=1) & west
    rgb = np.where(rim[..., None], _pick(SN, np.full(u.shape, 3)), rgb)
    a = np.zeros((h, w, 4), dtype=np.uint8)
    a[..., :3] = rgb
    a[..., 3] = np.where(body, 255, 0)
    # an outline round the skyline and sides (not the foot, which meets the ground)
    edge_px = body & ~(np.roll(body, 1, 0) & np.roll(body, -1, 0) & np.roll(body, 1, 1) & np.roll(body, -1, 1))
    foot = v > 0.9
    ol = edge_px & ~foot
    a[ol, :3] = _rgb(OUTLINE)
    return Image.fromarray(a, 'RGBA')


def _peaks(col: int, row: int, alt_at, free):
    """Mountains on a jittered grid over the region that reach this cell's canvas, back to
    front, bigger and snowier the higher they stand."""
    x0, y0 = col * W - S - 260, row * H - S - 40
    x1, y1 = (col + 1) * W + S + 260, (row + 1) * H + S + 340
    out = []
    for j in range(math.floor(y0 / 84), math.ceil(y1 / 84) + 1):
        for i in range(math.floor(x0 / 150), math.ceil(x1 / 150) + 1):
            k = i * 7907 + j * 131
            # (every other row shifted half a step, then jittered: no columns)
            bx = i * 150 + (75 if j % 2 else 0) + (noise2(i, j, 1011) - 0.5) * 110
            by = j * 84 + (noise2(i, j, 1012) - 0.5) * 60
            a = alt_at(bx, by)
            if a < 0.62 or noise2(i, j, 1015) < 0.18:
                continue
            size = min(1.0, 0.15 + (a - 0.62) * 0.5) * (0.55 + noise2(i, j, 1013) * 0.8)
            w = int(100 + 260 * size)
            h = int(w * (0.5 + noise2(i, j, 1014) * 0.35))
            w, h = w // 8 * 8, h // 8 * 8
            snow = float(np.clip((a - 0.6) * 0.8 + 0.25, 0, 1))
            left, top = int(bx - w / 2), int(by - h)
            if not free(left, top, w, h):
                continue
            out.append((by, left, top, w, h, k % 23, round(snow * 4) / 4))
    return sorted(out)


# The valley's railway leaves the halt's west edge in its cutting (halt rows 306-333) and
# runs on west to a tunnel portal in the wooded hillside, so the line visibly goes
# somewhere (the 19 Oct merge review: it ran straight into the canopy).
RAIL = {'zone': 'halt', 'cell': (-1, 1), 'y0': 306, 'y1': 334, 'portal_in': 150}


@functools.lru_cache(maxsize=4)
def _zone_ground(zone: str) -> np.ndarray:
    import os
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'zones', zone, 'ground.png')
    return np.array(Image.open(path).convert('RGB').resize((W, H), Image.NEAREST))


@functools.lru_cache(maxsize=2)
def _portal(w: int = 44, h: int = 46) -> Image.Image:
    """A railway tunnel's portal in the three-quarter view: a face of coursed stone with
    a lit upper-left edge, a round-headed arch over the track with a keystone, the dark
    of the tunnel inside, and a bank of earth over its top."""
    yy, xx = np.mgrid[0:h, 0:w]
    rgb = _pick(ST, np.where(((yy // 4) % 2 == 0) ^ (((xx + (yy // 4) * 3) // 7) % 2 == 0), 2, 3))
    rgb = np.where(((yy % 4) == 3)[..., None], _pick(ST, np.full(xx.shape, 1)), rgb)
    cx, top, half = w / 2, h - 30, 11
    arch = ((np.abs(xx + 0.5 - cx) <= half) & (yy >= top + half)) | (np.hypot(xx + 0.5 - cx, yy + 0.5 - (top + half)) <= half)
    ring = (((np.abs(xx + 0.5 - cx) <= half + 3) & (yy >= top + half)) | (np.hypot(xx + 0.5 - cx, yy + 0.5 - (top + half)) <= half + 3)) & ~arch
    rgb = np.where(ring[..., None], _pick(ST, np.where(xx < cx, 4, 2)), rgb)
    key = (np.abs(xx + 0.5 - cx) <= 2) & (yy >= top - 3) & (yy < top + 1)
    rgb = np.where(key[..., None], _pick(ST, np.full(xx.shape, 4)), rgb)
    rgb = np.where(arch[..., None], np.array(_rgb('#14131A'), dtype=np.uint8), rgb)
    inner = arch & (np.abs(xx + 0.5 - cx) > half - 2)
    rgb = np.where(inner[..., None], np.array(_rgb('#2A2733'), dtype=np.uint8), rgb)
    bank = yy < 6
    rgb = np.where(bank[..., None], _pick(FOREST_FLOOR, np.where(yy < 3, 1, 2)), rgb)
    lit = (xx < 2) & ~bank
    rgb = np.where(lit[..., None], _pick(ST, np.full(xx.shape, 4)), rgb)
    a = np.zeros((h, w, 4), dtype=np.uint8)
    a[..., :3] = rgb
    a[..., 3] = 255
    return Image.fromarray(a, 'RGBA')


@functools.lru_cache(maxsize=8)
def _terrace(zone: str):
    """The snow terrace a zone ends with at its east edge, read from its ground (the
    ridge's: snow down to a rim, a rock face under it, turf at its foot): (rim, face) in
    the zone's px, the first row below the snow and the face's height; or None."""
    col = _zone_ground(zone).astype(int)[:, W - 1]
    snow = (col[:, 2] >= col[:, 0]) & (col.sum(axis=1) > 450)
    green = (col[:, 1] > col[:, 0] + 10) & (col[:, 1] >= col[:, 2])
    for y in range(150, H - 60):
        # (the snow's last row may be a broken cornice: a drift pixel hangs below its lip)
        if snow[y - 12:y].sum() >= 11 and not snow[y] and snow[y:y + 4].sum() <= 1:
            for f in range(y + 4, y + 44):
                if green[f:f + 3].all():
                    return y, f - y
            return None
    return None


@functools.lru_cache(maxsize=8)
def _sea_cliff(zone: str):
    """The sea cliff a zone ends with at its west edge, read from its ground (the Halt's):
    (top, height) in the zone's px, where the face begins and how tall it is down to the
    sea; or None."""
    col = _zone_ground(zone).astype(int)[:, 0]
    wet = (col[:, 2] > col[:, 0] + 25) | ((col.sum(axis=1) > 600) & (col[:, 2] >= col[:, 0]))
    green = (col[:, 1] > col[:, 0] + 10) & (col[:, 1] >= col[:, 2])
    y = H - 1
    while y > H // 2 and wet[y]:
        y -= 1
    if y == H - 1 or y <= H // 2:
        return None
    sea_top = y + 1
    t = y
    while t > sea_top - 40 and not (green[t] and green[t - 1]):
        t -= 1
    h = sea_top - (t + 1)
    return (t + 1, h) if 4 <= h < 40 else None


class _Shift:
    """A canvas seen from another frame (a neighbouring zone's own pixels), so a zone's
    drawing helper paints on in the scenery with the zone's own coordinates and seeds."""

    def __init__(self, cv: Canvas, dx: int, dy: int):
        self.cv, self.dx, self.dy = cv, dx, dy

    def set(self, x, y, c, alpha=None):
        self.cv.set(x + self.dx, y + self.dy, c, alpha)

    def get(self, x, y):
        return self.cv.get(x + self.dx, y + self.dy)


def _zone_rects(col: int, row: int, zone_at):
    """The zones round a cell, as region rectangles [x0, x1) x [y0, y1)."""
    return [(c * W, r * H, (c + 1) * W, (r + 1) * H)
            for c in range(col - 1, col + 2) for r in range(row - 1, row + 2) if zone_at(c, r)]


def _zone_dist(X, Y, rects):
    """How far each point lies from the nearest of the zones (0 inside one), in px."""
    X, Y = np.asarray(X, dtype=float), np.asarray(Y, dtype=float)
    d = np.full(X.shape, 1e4)
    for (a, b, c, e) in rects:
        dx = np.maximum(np.maximum(a - X, X - (c - 1)), 0)
        dy = np.maximum(np.maximum(b - Y, Y - (e - 1)), 0)
        d = np.minimum(d, np.hypot(dx, dy))
    return d


# Zone sides that keep their own wood up to the edge (Claude E's Woodland, E18: belts of
# trees two or three deep along its west edge). There the forest closes up to the zone's
# trees instead of leaving a meadow and a front row before them, which read as a ride
# between two tree lines. cells() resolves them to (zone col, zone row, side) per region.
WOODED = {'valley': {('woodland', 'w')}}
_wooded: list = []


def _wooded_k(X, Y):
    """How much a point lies before a wooded zone side (1 along it, easing to 0 over the
    last 60 px toward its corners and 120 px out from it)."""
    k = np.zeros(np.shape(X))
    for (zc, zr, side) in _wooded:
        a, b = (Y - zr * H, (zr + 1) * H - Y) if side in 'we' else (X - zc * W, (zc + 1) * W - X)
        along = np.clip(np.minimum(a, b) / 60, 0, 1)
        out = {'w': zc * W - X, 'e': X - (zc + 1) * W, 'n': zr * H - Y, 's': Y - (zr + 1) * H}[side]
        k = np.maximum(k, along * np.clip((120 - out) / 40, 0, 1) * (out > -60))
    return k


def _margin(X, Y):
    """The meadow the forest leaves before a zone's edge: 16 to 30 px, wandering."""
    return 16 + 14 * wnoise(X, Y, 46, 581)


def _front(X, Y, rects, coast):
    """How far inside the forest a point lies (px; negative out in the meadow before
    it). The forest keeps a meadow from every zone's edge (art-faults.md A11), and 30 to
    46 px of turf from the shore, the cliff top or the beach, so no crown stands over a
    zone's field or at the water's edge (A3)."""
    ms = 30 + 16 * wnoise(X, Y, 40, 582)
    return np.minimum(_zone_dist(X, Y, rects) - _margin(X, Y), (coast - Y) - ms)


def _meadow(ground, X, Y, mask):
    """The valley's meadow on the scenery's side of an edge, in ground.py's own ramps and
    patches, so a zone's lawn runs on into the forest's margin without a seam; with the
    lawn's two-pixel blades. Returns the ground and the tufts to draw on it."""
    import ground as vground
    tone = np.where(vground.patches(X, Y), 3, 2)
    out = ground.copy()
    ramp_at = {}
    pal = {}
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        G = vground.kind_at(int(X[y, x]), int(Y[y, x]))
        ramp_at[(x, y)] = G
        if id(G) not in pal:
            pal[id(G)] = [_rgb(c) for c in G]
        out[y, x] = pal[id(G)][tone[y, x]]
    tufts = []
    for (x, y), G in ramp_at.items():
        gx, gy = int(X[y, x]), int(Y[y, x])
        P = pal[id(G)]
        if noise2(gx, gy, 9) <= 0.055 and ramp_at.get((x, y + 1)) is G and tone[y, x] == tone[y + 1, x]:
            if tone[y, x] == 3:
                out[y, x], out[y + 1, x] = P[4], P[2]
            else:
                out[y, x], out[y + 1, x] = P[3], P[1]
        if gx % 6 == 0 and gy % 6 == 0:  # tufts on the valley's own six-pixel grid
            tx, ty = x + int(noise2(gx, gy, 4) * 6), y + int(noise2(gx, gy, 5) * 6)
            if (tx, ty) in ramp_at and (tx, ty + 2) in ramp_at:
                cluster = smooth_noise(gx, gy, 25, 63) > 0.57
                if noise2(gx, gy, 3) < (0.36 if cluster else 0.14):
                    tufts.append((tx, ty + 2, int(noise2(gx, gy, 8) * 6), ramp_at[(tx, ty)], int(tone[ty, tx])))
    return out, tufts


def _front_row(col: int, row: int, zone_at, rects, rail):
    """The forest's front row along every edge it shares with a zone or the shore: a tree
    every 13 to 21 px on the front line, of mixed kinds and sizes, and saplings and bushes
    out in the meadow before them. The places come from the region's coordinates (the
    edge and a step along it), so the cells either side of a corner plant the same trees.
    Returns (foot x, foot y, kind, size, seed, palette) in region px, and the cast
    shadows (x, y, rx)."""
    x0, y0 = col * W - S - 70, row * H - S - 70
    x1, y1 = (col + 1) * W + S + 70, (row + 1) * H + S + 110
    cand = []
    for (a, b, c, e) in rects:
        zc, zr = a // W, b // H
        for side, (nx, ny) in (('w', (-1, 0)), ('e', (1, 0)), ('n', (0, -1)), ('s', (0, 1))):
            if zone_at(zc + nx, zr + ny):
                continue  # that edge meets another zone, not the land beyond
            if (zc, zr, side) in _wooded:
                continue  # the zone's own trees stand along it
            vertical = side in 'we'
            span = H if vertical else W
            ex = a - 1 if side == 'w' else c
            ey = b - 1 if side == 'n' else e
            key = (zc + 7) * 131 + (zr + 7) * 17 + 'wens'.index(side)
            step = 21 if vertical else 17
            for i in range(-3, span // step + 4):
                t = i * step + (noise2(i, key, 591) - 0.5) * 9
                px, py = (ex, b + t) if vertical else (a + t, ey)
                m = float(_margin(np.array(px + nx * 23.0), np.array(py + ny * 23.0)))
                # (under a zone's south edge the trees stand deeper: their crowns rise toward
                # it; beside a zone they stand at depths that vary more, so each shows)
                dd = m + 1 + noise2(i, key, 592) * (11 if vertical else 5) + (26 if side == 's' else 0)
                fx, fy = px + nx * dd, py + ny * dd
                if x0 <= fx < x1 and y0 <= fy < y1:
                    cand.append((fx, fy, (-nx, -ny), key * 1009 + i + 50))
    for i in range(math.floor(x0 / 17), math.ceil(x1 / 17) + 1):  # along the shore
        fx = i * 17 + (noise2(i, 7, 593) - 0.5) * 9
        cst = float(valley_fields(np.array([[fx]]), np.array([[0.0]]))[3][0, 0])
        ms = 30 + 16 * float(wnoise(np.array(fx), np.array(cst - 38), 40, 582))
        fy = cst - ms - 1 - noise2(i, 7, 594) * 5
        if x0 <= fx < x1 and y0 <= fy < y1:
            cand.append((fx, fy, (0, 1), 900001 + i))
    if not cand:
        return [], []
    CX = np.array([[p[0] for p in cand]])
    CY = np.array([[p[1] for p in cand]])
    a_, s_, r_, c_, _rc = valley_fields(CX, CY)
    f_ = _front(CX, CY, rects, c_)
    zd = _zone_dist(CX, CY, rects)
    ok = (a_ <= 0.12) & ~s_ & ~r_ & (zd > 0) & (f_ > -8) & (f_ < 14) & ~rail(CX, CY)
    kept, items, shadows = [], [], []
    for k, (fx, fy, out, seed) in enumerate(cand):
        if not ok[0, k] or any(abs(fx - qx) < 11 and abs(fy - qy) < 11 for (qx, qy) in kept):
            continue
        kept.append((fx, fy))
        h = noise2(seed, 0, 595)
        kind = 'broad' if h < 0.38 else 'birch' if h < 0.56 else 'autumn' if h < 0.62 else 'pine' if h < 0.76 else 'broad'
        size = int(9 + noise2(seed, 1, 596) * 9) if kind in ('broad', 'autumn') else int(7 + noise2(seed, 1, 596) * 4)
        if out[0] and kind != 'pine':
            size = min(size, int(zd[0, k]) - 3)  # never over a zone beside it
            if size < 7:
                kind, size = 'sapling', 4
        hp = noise2(seed, 2, 597)
        pal = 5 if kind == 'autumn' else 4 if kind == 'birch' else (1 if hp < 0.4 else 2 if hp < 0.75 else 6)
        items.append((fx, fy, 'broad' if kind == 'autumn' else kind, size, seed % 97, pal))
        shadows.append((fx, fy, 16 if kind == 'pine' else size))
        # out in the meadow before it: a bush or a sapling, now and then
        if noise2(seed, 3, 598) < 0.62:
            dist = (size * 0.9 if out[0] else 0) + 6 + noise2(seed, 4, 599) * 9
            side = (noise2(seed, 5, 599) - 0.5) * 14
            bx, by = fx + out[0] * dist - out[1] * side, fy + out[1] * dist + out[0] * side
            small = noise2(seed, 6, 599) < 0.55
            sz = (5 + int(noise2(seed, 7, 599) * 4)) if small else (3 + int(noise2(seed, 7, 599) * 3))
            BX, BY = np.array([[bx]]), np.array([[by]])
            _ba, bs, br, bc, _brc = valley_fields(BX, BY)
            if (float(_zone_dist(BX, BY, rects)[0, 0]) > sz + 3 and not bs[0, 0] and not br[0, 0]
                    and float(bc[0, 0] - by) > 18 and not rail(BX, BY)[0, 0]):
                pal_b = 6 if noise2(seed, 8, 599) < 0.5 else 2
                items.append((bx, by, 'bush' if small else 'sapling', sz, (seed * 7) % 97, pal_b))
                shadows.append((bx, by, sz))
    return items, shadows


@functools.lru_cache(maxsize=64)
def _edge_land(zone: str, side: str):
    """Where a zone's land meets one of its sides over open sea: per pixel along the side,
    how far the land runs on past the edge (px) as a rounded point, else 0."""
    g = _zone_ground(zone).astype(int)
    edge = {'w': g[:, 0], 'e': g[:, W - 1], 'n': g[0, :], 's': g[H - 1, :]}[side]
    wet = (edge[:, 2] > edge[:, 0] + 25) | ((edge.sum(axis=1) > 600) & (edge[:, 2] >= edge[:, 0]))
    out = np.zeros(len(edge))
    if wet.mean() < 0.2:
        return out  # (a side that is land along its length meets land beyond, not the sea)
    i = 0
    while i < len(edge):
        if wet[i]:
            i += 1
            continue
        j = i
        while j < len(edge) and not wet[j]:
            j += 1
        h = (j - i) / 2
        if h >= 1.5:
            cmid, top = (i + j - 1) / 2, min(12.0, 2 + 0.5 * h)
            for t in range(i, j):
                u = (t - cmid) / (h + 0.5)
                out[t] = top * math.sqrt(max(0.0, 1 - u * u)) * (0.8 + 0.4 * noise2(t // 3, j, 468))
        i = j
    return out


def _zone_grass(X, Y, zone_at):
    """Whether each point shows grass in the zone it lies in (False outside zones)."""
    out = np.zeros(np.shape(X), dtype=bool)
    C, R = np.floor_divide(X, W), np.floor_divide(Y, H)
    for (c, r) in set(zip(C.ravel().tolist(), R.ravel().tolist())):
        z = zone_at(c, r)
        if not z or z == 'garden':
            continue
        m = (C == c) & (R == r)
        g = _zone_ground(z).astype(int)[Y[m] - r * H, X[m] - c * W]
        out[m] = (g[:, 1] > g[:, 0] + 10) & (g[:, 1] >= g[:, 2])
    return out


def valley_cell(col: int, row: int, zone_at) -> Canvas:
    """One cell of scenery in the valley. `zone_at(col, row)` names the zone there, if any.

    The high country is a range of mountains drawn like the forest's crowns, back to
    front in the same three-quarter view as everything else, over snowfields and
    alpine turf; below the treeline, pines; in the valley's own country, old forest;
    then the shore and the open sea.

    Where it meets a zone it carries on what the zone shows at its edge (art-faults.md,
    19 Oct 22:40): the ridge's snow terrace and its rock face run on into the cell and
    die out (A4); the Halt's sea cliff runs on west along the coast (A3); and the forest
    stops short of every zone and shore, behind a meadow with a front row of single trees
    of mixed kinds, saplings and bushes, and its shade lying out over the grass (A11);
    before a zone side that keeps its own wood (WOODED) the zone's trees are the front
    row, and the canopy comes up to the meadow and leans over it."""
    import ground as vground
    import valley_zones as vz  # (the face and cliff painters the zones use; loaded by zones.py)
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + CW), np.arange(y0, y0 + CH))
    alt, sea, river, coast, rc = valley_fields(X, Y)
    rects = _zone_rects(col, row, zone_at)
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    front = _front(X, Y, rects, coast)
    in_zone = _zone_dist(X, Y, rects) == 0
    snowy = alt + 0.4 * (vnoise(X, Y, 60, 993) - 0.5) > 0.9
    n = wnoise(X, Y, 34, 991)
    fine = vnoise(X, Y, 6, 995)
    snowfield = _pick(SN, np.where(n > 0.45, 3, 2))
    snowfield = np.where(((fine > 0.88) & (n < 0.45))[..., None], _pick(SN, np.full(X.shape, 1)), snowfield)
    # alpine turf in the valley's own patches (ground.py), so it meets a zone's turf whole
    turf = _pick(ALPINE, np.where(vground.patches(X, Y), 3, 2))
    turf = np.where((vnoise(X, Y, 3.5, 992) > 0.82)[..., None], _pick(ST, np.where(fine > 0.5, 3, 2)), turf)
    ground = np.where(snowy[..., None], snowfield, turf)
    lowland = alt <= 0.12
    forest = lowland & (front > 0)
    ground = np.where(forest[..., None], _forest_floor_rgb(X, Y), ground)
    # the meadow: before the forest, and within the margin of any zone (its own turf, so
    # the two meet whole: ground.kind_at gives the zone's ramp, ground.patches its patches)
    near_zone = _zone_dist(X, Y, rects) - _margin(X, Y) <= 0
    meadow = (lowland & ~forest | ~lowland & near_zone & ~snowy) & ~sea & ~river & inside
    tufts = []
    if meadow.any():
        ground, tufts = _meadow(ground, X, Y, meadow)
    # The sea, banded as the zones paint theirs by how far it lies from the shore: the
    # scenery's own coast where that coast is scenery, and the water at a zone's edge
    # carried on into the cell (the Halt's cove, Driftwood's west shallows), so the bands
    # and the foam run on across the seam instead of meeting the open sea on a line.
    coast_free = _zone_dist(X, coast, rects) > 0
    own = np.where(coast_free, Y - coast, 999.0)   # how far from the scenery's own shore
    near_s = np.full(X.shape, np.inf)               # the nearest zone side with water...
    near_e = np.zeros(X.shape)                      # ...and how deep its water is there
    cap = np.zeros(X.shape, dtype=bool)             # a zone's land running on into the sea
    for (a, b, c, e) in rects:
        zc, zr = a // W, b // H
        z = zone_at(zc, zr)
        if z == 'garden':
            continue
        for side, (nx, ny) in (('w', (-1, 0)), ('e', (1, 0)), ('n', (0, -1)), ('s', (0, 1))):
            if zone_at(zc + nx, zr + ny):
                continue
            edge_d, carry = _edge_water(z, side)
            if side in 'we':
                k = (a - X) if side == 'w' else (X - (c - 1))   # how far out past the edge
                t, span = Y - b, H
            else:
                k = (b - Y) if side == 'n' else (Y - (e - 1))
                t, span = X - a, W
            along = np.clip(t, 0, span - 1)
            off = np.maximum(np.maximum(-t, t - (span - 1)), 0)
            beyond = k >= 1
            # land just inside the zone's edge is a shore for the scenery's water too
            own = np.where(beyond & (off == 0), np.minimum(own, carry[along] + k), own)
            # where its land meets the edge over open sea, the land ends past it in a
            # rounded point of rocks instead of a cut (the lighthouse's point, the Halt's
            # cliff foot)
            reach_in = _edge_land(z, side)[along]
            here = beyond & (off == 0) & (reach_in > 0)
            cap |= here & (k <= reach_in) & sea
            own = np.where(here, np.minimum(own, k - reach_in), own)
            sd = np.hypot(np.maximum(k, 0), off)
            closer = beyond & (sd < near_s)
            near_s = np.where(closer, sd, near_s)
            near_e = np.where(closer, edge_d[along], near_e)
    # where a zone paints its edge as open sea, the water past it is as deep, giving way
    # to the scenery's own depth over 40 px; its shallows come from its land (the shore)
    wgt = np.clip(near_s / 40, 0, 1)
    depth = np.maximum(np.clip(own, 0, 90), near_e * (1 - wgt))
    # Each stretch of open water reads its noise in the frame of the nearest zone with a
    # sea (the frames meet along a wandering line out on the water), so the scenery's
    # patches and swells run on from every zone's own; with no such zone near, valley x
    # from the bottom row's top.
    warp = 0.36 * np.clip(_zone_dist(X, Y, rects) / 60, 0, 1)
    d_sea = np.clip(depth, 0, 90)
    seas = [(c_ * W, r_ * H, (c_ + 1) * W, (r_ + 1) * H) for c_ in range(col - 3, col + 4)
            for r_ in range(row - 3, row + 4) if _has_sea(zone_at(c_, r_))]
    best, sea_rgb = np.full(X.shape, np.inf), None
    for r_ in seas or [None]:
        if r_ is None:
            fx, fy, dist = 0, -(row // 2 * 2) * H, np.zeros(X.shape)
        else:
            z = zone_at(r_[0] // W, r_[1] // H)
            fx, fy = (-r_[0] if z in SEA_OWN_X else 0), -r_[1]
            dist = _zone_dist(X, Y, [r_]) + 24 * (vnoise(X, Y, 50, 991) - 0.5)
        rgb = _shore_sea_rgb(X, Y, d_sea, fx, fy, warp)
        take = dist < best
        best = np.where(take, dist, best)
        sea_rgb = rgb if sea_rgb is None else np.where(take[..., None], rgb, sea_rgb)
    ground = np.where(sea[..., None], sea_rgb, ground)
    if cap.any():
        rock = vnoise(X, Y, 4, 467)
        ci = np.where(rock > 0.62, 3, np.where(rock > 0.38, 2, 1))
        lit_edge = cap & ~np.roll(cap, 1, axis=0)
        ci = np.where(lit_edge, 4, ci)
        rim = cap & ~(np.roll(cap, -1, 0) & np.roll(cap, -1, 1))
        ci = np.where(rim & ~lit_edge, 0, ci)
        ground = np.where(cap[..., None], _pick(ST, ci), ground)
        sea = sea & ~cap
    sand = (X > CLIFF_COAST_X) & coast_free & ~sea & (Y - coast > -10)
    sand_rgb = _pick(SAND, np.where(Y - coast > -4, 0, np.where(vnoise(X, Y, 3, 964) > 0.5, 2, 1)))
    ground = np.where(sand[..., None], sand_rgb, ground)
    ground = np.where((river & ~sea)[..., None], _river_rgb(X, Y, rc), ground)

    # The ridge's snow terrace runs on from the zone to the west (A4): the snow ends on
    # the same rim, the rock face under it carries on and dies out, the snow then coming
    # down as a bank to the turf, and the rim climbs away toward the peaks.
    wz = zone_at(col - 1, row)
    terrace = _terrace(wz) if wz and wz != 'garden' else None
    tox, toy = (col - 1) * W, row * H  # that zone's origin

    def terrace_line(Xs):
        """(top of the face, height of the face, its foot) by region x, or None."""
        rim0, F0 = terrace
        d = Xs - col * W
        t = np.clip(d / 130 + (vnoise(Xs, 0 * Xs, 23, 611) - 0.5) * 0.3, 0, 1)
        fh = np.round(F0 * (1 - t * t * (3 - 2 * t))).astype(int)
        u = np.clip((d - 150) / 170, 0, 1)
        rim = np.floor(toy + rim0 + (vnoise(Xs, 0 * Xs, 27, 612) - 0.5) * 14 * np.clip(d / 24, 0, 1)
                       - 280 * u * u * (3 - 2 * u)).astype(int)
        foot = rim + F0
        return foot - fh, fh, foot

    if terrace:
        ftop, fh, ffoot = terrace_line(X)
        rim0, F0 = terrace
        xl, yl = X - tox, Y - toy
        # the snow in the ridge's own texture (drifts and the wind's ripples), giving way
        # to the high snowfields' further east
        nn = vnoise(xl, yl, 18, 443)
        ci = np.where(nn > 0.4, 3, np.where((nn > 0.22) | ((xl + yl) % 2 == 1), 2, 1))
        rip = (yl * 2 + np.trunc(np.sin(xl / 13 + yl / 31) * 4).astype(int)) % 9
        ci = np.where((rip == 0) & (nn > 0.3), 2, np.where((rip == 1) & (nn > 0.3), 3, ci))
        ridge_snow = _pick(SN, ci)
        own = (X - col * W) + 70 * (vnoise(X, Y, 40, 614) - 0.5) < 210
        bank = (Y < ftop) & ~((Y >= ffoot - F0) & (Y > ftop - 3) & (vnoise(X, Y, 5, 449) > 0.82))
        carried = bank & (X >= col * W) & ~sea
        ground = np.where((carried & own)[..., None], ridge_snow, ground)
        ground = np.where((carried & ~own)[..., None], snowfield, ground)

    # Where a zone beside the cell lies under snow at the shared edge, its snow runs on
    # into the scenery for a ragged 30 to 80 px, so a snowfield never stops on a ruled
    # line against green (review 15:54, the ridge beside the forest past the riverside).
    reach = 30 + vnoise(X, Y, 18, 996) * 50
    for (dc, dr) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        z = zone_at(col + dc, row + dr)
        if not z or z == 'garden' or (dc == -1 and terrace):
            continue
        g = _zone_ground(z).astype(int)
        edge = g[:, W - 1] if dc < 0 else g[:, 0] if dc > 0 else g[H - 1, :] if dr < 0 else g[0, :]
        # snow, and the bare grey rock of a snowy face (neither is green)
        sat = edge.max(axis=1) - edge.min(axis=1)
        raw = (((edge.sum(axis=1) > 600) & (edge[:, 2] >= edge[:, 0])) | ((sat < 26) & (edge.sum(axis=1) > 330))).astype(float)
        # (the snow's extent along the edge, not single bright pixels: a running majority)
        frac = np.convolve(raw, np.ones(41) / 41, mode='same')
        # (how far the snow runs in: full along the snow, tapering where it ends)
        snowline = np.clip((frac - 0.3) / 0.45, 0, 1)
        if not snowline.any():
            continue
        if dc:
            along = np.clip(Y - row * H, 0, H - 1)
            d = (X - col * W) if dc < 0 else ((col + 1) * W - 1 - X)
        else:
            along = np.clip(X - col * W, 0, W - 1)
            d = (Y - row * H) if dr < 0 else ((row + 1) * H - 1 - Y)
        under = (d >= 0) & (d < reach * snowline[along]) & ~sea
        ground = np.where(under[..., None], snowfield, ground)
    # the railway: the halt's cutting (its walls, ballast, sleepers and rails) carried on
    # west from its edge, column for column, to the portal
    rc_, rr_ = RAIL['cell']
    ry0, ry1 = rr_ * H + RAIL['y0'], rr_ * H + RAIL['y1']
    rx_end = rc_ * W                       # the halt's west edge, in region x
    rx_portal = rx_end - RAIL['portal_in']
    track = (Y >= ry0) & (Y < ry1) & (X >= rx_portal) & (X < rx_end)
    has_rail = track.any() and zone_at(rc_, rr_) == RAIL['zone']
    if has_rail:
        hg = _zone_ground(RAIL['zone'])
        lx = 1 + np.mod(X - rx_end, 7)
        ly = np.clip(Y - rr_ * H, 0, H - 1)
        ground = np.where(track[..., None], hg[ly, lx], ground)

    def rail(GX, GY):
        return (GY > ry0 - 14) & (GY < ry1 + 22) & (GX > rx_portal - 6) & (GX < rx_end + 4)

    _paint(cv, ground, inside)
    for (x, y, k, G, t) in tufts:
        detail.grass_tuft(cv, x, y, k, G, t)

    # Shade: the forest floor's shade lies out over the meadow before the trees, 20 to 40
    # px, ragged, darkest at the trees' feet; past the cell it falls on the zone's own
    # ground as an overlay (above its ground, under its props, as the renderer draws the
    # spill). Each tree of the front row casts its shadow down and to the right.
    dcell = np.hypot(np.maximum(np.maximum(col * W - X, X - ((col + 1) * W - 1)), 0),
                     np.maximum(np.maximum(row * H - Y, Y - ((row + 1) * H - 1)), 0))
    # (past the cell, shade falls only on a zone's grass, never on its water or paving)
    spill_zone = in_zone & ~inside & _zone_grass(X, Y, zone_at)
    out_by = np.where(spill_zone, _margin(X, Y) + dcell, -front)
    on_grass = (meadow | spill_zone) & lowland
    far = 20 + 20 * wnoise(X, Y, 30, 631)
    near = 4 + 5 * wnoise(X, Y, 12, 632)
    lvl = np.where(on_grass & (out_by >= 0) & (out_by < near), 2,
                   np.where(on_grass & (out_by >= 0) & (out_by < far), 1, 0)).astype(np.uint8)
    edge_items, shadows = _front_row(col, row, zone_at, rects, rail)
    for (fx, fy, r) in shadows:
        cx_, cy_ = fx + r * 0.45 - x0, fy + 1 - y0
        rx_, ry_ = r * 0.95 + 1, max(2.0, r * 0.32)
        X0_, X1_ = max(0, int(cx_ - rx_) - 1), min(CW, int(cx_ + rx_) + 2)
        Y0_, Y1_ = max(0, int(cy_ - ry_) - 1), min(CH, int(cy_ + ry_) + 2)
        if X1_ <= X0_ or Y1_ <= Y0_:
            continue
        yy, xx = np.mgrid[Y0_:Y1_, X0_:X1_]
        e = ((xx + 0.5 - cx_) / rx_) ** 2 + ((yy + 0.5 - cy_) / ry_) ** 2
        sub = lvl[Y0_:Y1_, X0_:X1_]
        g_ok = on_grass[Y0_:Y1_, X0_:X1_]
        sub[:] = np.where(g_ok & (e <= 0.45), np.maximum(sub, 2), np.where(g_ok & (e <= 1), np.maximum(sub, 1), sub))
    arr = np.array(cv.img)
    mul = np.array(style.SHADOW_MUL)
    for L in (1, 2):
        m_ = inside & (lvl == L)
        arr[m_, :3] = (arr[m_, :3] * mul ** L).astype(np.uint8)
    sp = spill_zone & (lvl > 0)
    arr[sp, :3] = SHADE_INK
    arr[sp, 3] = np.array(SHADE_ALPHA, dtype=np.uint8)[lvl[sp]]
    cv.img.paste(Image.fromarray(arr, 'RGBA'))

    # the faces carried on from the zones beside the cell, drawn as the zones draw theirs
    if terrace:
        rim0, F0 = terrace
        tops, hts = {}, {}
        for cx in range(S, S + W):
            if fh[0, cx] >= 3:
                tops[cx + x0 - tox] = int(ftop[0, cx]) - toy
                hts[cx + x0 - tox] = int(fh[0, cx])
        if tops:
            sh = _Shift(cv, tox - x0, toy - y0)
            snow_lip = [SN[0], SN[0], SN[1], SN[2], SN[3]]
            vz.cliff(sh, tops, hts, seed=446, lip=snow_lip)
            for xl_, t in tops.items():  # snow on the ledges, the face's shadow on the turf
                for k in range(2, hts[xl_] - 3):
                    y = t + k
                    if sh.get(xl_, y)[:3] == _rgb(ST[4]) and noise2(xl_ // 2, y, 448) > 0.45:
                        sh.set(xl_, y, SN[3] if (xl_ + y) % 3 else SN[2])
                for d in range(3):
                    if (xl_ + d) % 2 or d == 0:
                        style.darken(cv, xl_ + tox - x0, t + hts[xl_] + d + toy - y0)
    ez = zone_at(col + 1, row)
    cliff_in = _sea_cliff(ez) if ez and ez != 'garden' else None
    if cliff_in:
        # the Halt's low sea cliff runs on west along the coast, its height wandering
        # from the Halt's own at the seam (A3)
        _top0, h0 = cliff_in
        zox, zoy = (col + 1) * W, row * H
        tops, hts = {}, {}
        for cx in range(S, S + W):
            Xc = x0 + cx
            if Xc > CLIFF_COAST_X:
                continue
            sea_top = int(math.floor(coast[0, cx])) + 1
            s = min(1.0, (zox - Xc) / 40)
            h = int(round(h0 * (1 - s) + (11 + float(vnoise(np.array(Xc), np.array(0.0), 9, 456)) * 5) * s))
            top = sea_top - h
            if y0 <= top and sea_top <= y0 + CH:
                tops[Xc - zox], hts[Xc - zox] = top - zoy, h
        if tops:
            vz.cliff(_Shift(cv, zox - x0, zoy - y0), tops, hts, seed=458)

    def field(x, y):
        a1, s1, r1, _c, _r = valley_fields(np.array([[x]]), np.array([[y]]))
        return float(a1[0, 0]), bool(s1[0, 0]), bool(r1[0, 0])

    def zone_px(x, y):
        return zone_at(math.floor(x / W), math.floor(y / H))

    def free(left, top, w, h):
        # a mountain stands on scenery only: it may lean over a zone by the spill at most
        for fx in (0.0, 0.25, 0.5, 0.75, 1.0):
            for fy in (0.0, 0.5, 1.0):
                x, y = left + fx * w, top + fy * h
                if zone_px(x, y) and zone_px(x + (S if fx < 0.5 else -S), y + (S if fy < 0.5 else -S)):
                    return False
        a, s1, r1 = field(left + w / 2, top + h)
        return not (s1 or r1)

    def kind_at(GX, GY):
        # what grows at each candidate point (arrays): nothing in water, in a zone, on the
        # rails or above the treeline; pines below it (not on the carried snow); crowns at
        # the valley's level, well inside the forest's edge (up to it before a zone's own
        # wood, where they may lean over its edge by the spill)
        a, s1, r1, c1, _r = valley_fields(GX, GY)
        zone = _zone_dist(GX, GY, rects) == 0
        f = _front(GX, GY, rects, c1)
        snow = np.zeros(GX.shape, dtype=bool)
        if terrace:
            _t_top, _t_h, t_foot = terrace_line(GX)
            snow = (GY < t_foot + 6) & (GX >= col * W - 4) & (GX - col * W < 330)
        return np.where(s1 | r1 | zone | rail(GX, GY) | (a > 0.6), None,
                        np.where(a > 0.12, np.where(snow | (c1 - GY < 40), None, 'pine'),
                                 np.where(f > 22 - 18 * _wooded_k(GX, GY), 'crown', None)))

    def room(GX, GY):
        # (a crown of the canopy keeps clear of the front row's own crowns, so it reads;
        # before a zone's own wood there is no front row, and it may lean over the edge)
        _a, _s, _r, c1, _rc = valley_fields(GX, GY)
        return _front(GX, GY, rects, c1) - 12 + 28 * _wooded_k(GX, GY)

    zone_sides = {s for s, (dc, dr) in {'w': (-1, 0), 'e': (1, 0), 'n': (0, -1), 's': (0, 1)}.items()
                  if zone_at(col + dc, row + dr)}

    def fits(left, top, im):
        # (a sprite may run past the canvas into the next cell of scenery, which draws its
        # other part, but never past the spill into a zone, where it would be cut)
        bb = im.getbbox()
        if bb is None:
            return False
        l_, t_, r_, b_ = left + bb[0], top + bb[1], left + bb[2], top + bb[3]
        return not (('w' in zone_sides and l_ < 0) or ('e' in zone_sides and r_ > CW)
                    or ('n' in zone_sides and t_ < 0) or ('s' in zone_sides and b_ > CH))

    # mountains and trees together, back to front
    things = [(by, 'peak', (left, top, w, h, seed, snow)) for (by, left, top, w, h, seed, snow)
              in _peaks(col, row, lambda x, y: field(x, y)[0], free)]
    things += [(gy, what, (gx, d, k)) for (gy, gx, what, d, k) in _trees('valley', col, row, kind_at, room)]
    things += [(fy, 'edge', (fx, kind, size, seed, pal)) for (fx, fy, kind, size, seed, pal) in edge_items]
    # Along an edge the pines share with a zone, a fringe of pines straddling the edge, so
    # the alpine turf never ends on a ruled line against the zone's ground (review 15:54).
    cx0_, cy0_ = col * W, row * H
    for side, (dc, dr) in {'w': (-1, 0), 'e': (1, 0), 'n': (0, -1), 's': (0, 1)}.items():
        if not zone_at(col + dc, row + dr):
            continue
        span = H if side in 'we' else W
        for i in range(-1, span // 22 + 2):
            t = i * 22 + (noise2(i, col * 31 + row, 561 + len(side)) - 0.5) * 12
            inset = 3 + noise2(i, row * 17 + col, 562) * 12      # how far inside the cell
            if side == 'w':
                gx, gy = cx0_ + inset, cy0_ + t
            elif side == 'e':
                gx, gy = cx0_ + W - inset, cy0_ + t
            elif side == 'n':
                gx, gy = cx0_ + t, cy0_ + inset
            else:
                gx, gy = cx0_ + t, cy0_ + H - inset
            ix, iy = gx + (8 if side == 'w' else -8 if side == 'e' else 0), gy + (8 if side == 'n' else -8 if side == 's' else 0)
            what = kind_at(np.array([[ix]]), np.array([[iy]]))[0, 0]
            if what == 'pine' and noise2(i, col + row * 5, 564) < 0.8:
                things.append((gy + 8, 'pine', (gx, 0, 0)))
    if has_rail:
        things.append((ry1, 'portal', None))
    pine = _pine()
    for (by, what, d) in sorted(things, key=lambda t: (t[0], t[1])):
        if what == 'peak':
            left, top, w, h, seed, snow = d
            sp_ = _peak(w, h, seed, snow)
            px, py = left - x0, top - y0
            # (cut to the canvas; the neighbouring cell draws the rest the same way)
            cx0, cy0 = max(0, px), max(0, py)
            cx1, cy1 = min(CW, px + w), min(CH, py + h)
            if cx1 > cx0 and cy1 > cy0:
                cv.img.alpha_composite(sp_.crop((cx0 - px, cy0 - py, cx1 - px, cy1 - py)), (cx0, cy0))
        elif what == 'portal':
            pi = _portal()
            _stamp(cv, pi, int(rx_portal - x0 - pi.width + 6), int(ry1 - y0 - pi.height))
        elif what == 'crown':
            gx, (rx, pal, r10), k = d
            X0, Y0 = gx - x0, by - y0
            # (only toward a zone is a crown kept inside the spill; elsewhere it runs on
            # into the next cell, which draws the same crown, so no cell edge shows)
            if 'w' in zone_sides:
                rx = min(rx, X0 - 4)
            if 'e' in zone_sides:
                rx = min(rx, CW - X0 - 4)
            if 'n' in zone_sides:
                rx = min(rx, (Y0 - 4) / 0.72)
            if 's' in zone_sides:
                rx = min(rx, (CH - Y0 - 4) / 0.72)
            if rx >= 8:
                _crown(cv, X0, Y0, rx, k, pal, r10)
        elif what in ('edge', 'under'):
            if what == 'edge':
                fx, kind, size, seed, pal = d
            else:
                fx = d[0]
                kind, size, seed, pal = d[1]
            im, ax, ay = _edge_tree(kind, int(size), int(seed), int(pal))
            left, top = int(round(fx - x0)) - ax, int(round(by - y0)) - ay
            if fits(left, top, im):
                _stamp(cv, im, left, top)
        else:
            gx, _rx, _k = d
            X0, Y0 = gx - x0, by - y0
            px, py = int(X0 - pine.w / 2), int(Y0 - pine.h + 8)
            if fits(px, py, pine.img):
                _stamp(cv, pine, px, py)
    return cv


DESERT, BASALT, ASH, LAVA = (MATERIALS[k] for k in ('desert', 'basalt', 'ash', 'lava'))
ADOBE, REGOLITH = MATERIALS['adobe'], MATERIALS['regolith']


def _blend_cells(X, Y, value, spread: float = 0.28, seed: int = 1101):
    """A field that is `value(col, row)` at each cell's middle and blends between cells:
    bilinear between the middles, then a wandering noise, so a change of kind lies
    somewhere across the land rather than on a cell's edge."""
    fx, fy = X / W - 0.5, Y / H - 0.5
    c0, r0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - c0, fy - r0
    vals = {}
    def v(c, r):
        out = np.zeros(c.shape)
        for (cc, rr) in set(zip(c.ravel().tolist(), r.ravel().tolist())):
            if (cc, rr) not in vals:
                vals[(cc, rr)] = float(value(cc, rr))
            out[(c == cc) & (r == rr)] = vals[(cc, rr)]
        return out
    a = v(c0, r0) * (1 - tx) + v(c0 + 1, r0) * tx
    b = v(c0, r0 + 1) * (1 - tx) + v(c0 + 1, r0 + 1) * tx
    f = a * (1 - ty) + b * ty
    return f + spread * (vnoise(X, Y, 90, seed) - 0.5) + 0.1 * (vnoise(X, Y, 23, seed + 1) - 0.5)


@functools.lru_cache(maxsize=256)
def _mesa(w: int, h: int, seed: int) -> Image.Image:
    """A sandstone butte in the three-quarter view: a flat top lit by the sun, sheer
    walls of banded strata (the west wall lit, the east in shade), a skirt of talus at
    its foot."""
    rnd = lambda k: float(_hash(np.array(seed), np.array(k), 1201))  # noqa: E731
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u = (xx + 0.5) / w * 2 - 1
    v = (yy + 0.5) / h
    jag = (vnoise(xx, yy, 6, seed * 5 + 1) - 0.5) * 0.08
    top = 0.18 + rnd(1) * 0.1
    half_top = 0.55 + rnd(2) * 0.2 + jag
    # the cap (an ellipse seen from above), the walls below it, the talus flaring out
    cap = ((u / half_top) ** 2 + ((v - top) / 0.16) ** 2) <= 1
    wall = (v >= top) & (np.abs(u) <= half_top + np.maximum(0, v - 0.72) * 1.4 + jag)
    body = (cap | wall) & (v <= 1 - 0.12 * u * u)
    west = u < -0.1 + (vnoise(0 * xx, yy, 11, seed * 5 + 2) - 0.5) * 0.2
    band = ((yy + vnoise(xx, 0 * yy, 20, seed * 5 + 3) * 6) // max(3, h // 18)).astype(int) % 3
    wall_i = np.where(west, np.where(band == 0, 4, 3), np.where(band == 0, 2, 1))
    rgb = _pick(ADOBE, wall_i)
    talus = v > 0.74
    rgb = np.where(talus[..., None], _pick(DESERT, np.where(west, 3, 2)), rgb)
    is_cap = cap & ~(v > top + 0.13)
    rgb = np.where(is_cap[..., None], _pick(DESERT, np.where(vnoise(xx, yy, 7, seed) > 0.6, 5, 4)), rgb)
    rim = cap & ~np.roll(cap, -2, axis=0) & (v > top)   # the cap's lit south lip
    rgb = np.where(rim[..., None], _pick(DESERT, np.full(u.shape, 5)), rgb)
    a = np.zeros((h, w, 4), dtype=np.uint8)
    a[..., :3] = rgb
    a[..., 3] = np.where(body, 255, 0)
    edge_px = body & ~(np.roll(body, 1, 0) & np.roll(body, -1, 0) & np.roll(body, 1, 1) & np.roll(body, -1, 1))
    a[edge_px & (v < 0.9), :3] = _rgb(ADOBE[0])
    return Image.fromarray(a, 'RGBA')


@functools.lru_cache(maxsize=256)
def _cinder_cone(w: int, h: int, seed: int) -> Image.Image:
    """A cinder cone on the volcano's flank: a black cone of loose scoria, lit on the
    west, grey ash streaking its slopes, a crater at the top with a faint glow."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u = (xx + 0.5) / w * 2 - 1
    v = (yy + 0.5) / h
    crater_v = 0.16
    span = (v - crater_v * 0.4) / (1 - crater_v * 0.4)
    jag = (vnoise(xx, yy, 6, seed * 3 + 1) - 0.5) * 0.08
    body = (span >= 0) & (np.abs(u) <= 0.28 + span * 0.72 + jag) & (v <= 1 - 0.1 * u * u)
    west = u < (vnoise(0 * xx, yy, 13, seed * 3 + 2) - 0.5) * 0.15
    streak = ridged(u * 30 / np.maximum(v, 0.1), yy * 0.2, 5, seed * 3 + 3) > 0.78
    idx = np.where(west, 3, 1)
    rgb = _pick(BASALT, idx)
    rgb = np.where((streak & west)[..., None], _pick(ASH, np.full(u.shape, 3)), rgb)
    rgb = np.where((streak & ~west)[..., None], _pick(ASH, np.full(u.shape, 1)), rgb)
    crater = ((u / 0.3) ** 2 + ((v - crater_v) / 0.07) ** 2) <= 1
    rgb = np.where(crater[..., None], _pick(BASALT, np.full(u.shape, 0)), rgb)
    glow = ((u / 0.16) ** 2 + ((v - crater_v - 0.01) / 0.035) ** 2) <= 1
    rgb = np.where(glow[..., None], _pick(LAVA, np.full(u.shape, 1)), rgb)
    a = np.zeros((h, w, 4), dtype=np.uint8)
    a[..., :3] = rgb
    a[..., 3] = np.where(body, 255, 0)
    edge_px = body & ~(np.roll(body, 1, 0) & np.roll(body, -1, 0) & np.roll(body, 1, 1) & np.roll(body, -1, 1))
    a[edge_px & (v < 0.9), :3] = _rgb(BASALT[0])
    return Image.fromarray(a, 'RGBA')


def _scatter(col, row, step_x, step_y, seed, margin=200):
    """Jittered points over the region reaching this cell's canvas (rows offset by half a
    step, so nothing lines up)."""
    x0, y0 = col * W - S - margin, row * H - S - 40
    x1, y1 = (col + 1) * W + S + margin, (row + 1) * H + S + margin
    for j in range(math.floor(y0 / step_y), math.ceil(y1 / step_y) + 1):
        for i in range(math.floor(x0 / step_x), math.ceil(x1 / step_x) + 1):
            bx = i * step_x + (step_x / 2 if j % 2 else 0) + (noise2(i, j, seed) - 0.5) * step_x * 0.7
            by = j * step_y + (noise2(i, j, seed + 1) - 0.5) * step_y * 0.7
            yield i, j, bx, by


def _place(cv, img, left, top, x0, y0):
    px, py = left - x0, top - y0
    _stamp(cv, img, px, py)


def _free_of_zones(zone_at, left, top, w, h):
    for fx in (0.0, 0.25, 0.5, 0.75, 1.0):
        for fy in (0.0, 0.5, 1.0):
            x, y = left + fx * w, top + fy * h
            if zone_at(math.floor(x / W), math.floor(y / H)) and zone_at(
                    math.floor((x + (S if fx < 0.5 else -S)) / W), math.floor((y + (S if fy < 0.5 else -S)) / H)):
                return False
    return True


def west_cell(col: int, row: int, zone_at) -> Canvas:
    """Sunstone Reach's surroundings: open desert of long dunes with sandstone buttes
    round the gulch and the oasis, giving way (across the land, not at a line) to the
    volcano's flank of basalt steps, drifted ash and cinder cones round the fire country."""
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + CW), np.arange(y0, y0 + CH))
    ashy = lambda c, r: 1.0 if (c >= 1 or (c >= 0 and r <= -2)) else 0.0  # noqa: E731
    ash = _blend_cells(X, Y, ashy) > 0.5
    # dunes: a wandering crest line, light rising to the crest, the lee in shade
    lx = X + (vnoise(0 * X, Y, 60, 781) * 40).astype(int)
    k = (Y + (np.sin(lx / 23.0) * 9 + vnoise(X, 0 * Y, 50, 782) * 18).astype(int)) % 46
    di = np.where(k < 2, 5, np.where(k < 12, 4, np.where(k > 38, 2, 3)))
    di = np.where((k > 34) & ((X + Y) % 2 == 1), 2, di)
    ripple = (Y + (np.sin(X / 8.0 + Y / 37.0) * 2).astype(int)) % 7
    di = np.where((ripple == 0) & (k > 14) & (k < 32), 4, di)
    sand = _pick(DESERT, di)
    # the flank: basalt steps with lit lips, ash in the hollows, a few glowing cracks
    off = (vnoise(X, 0 * Y, 40, 762) * 30).astype(int)
    kk = (Y + off) % 22
    bi = np.where(((Y + off) // 22) % 2 == 1, 2, 1)
    bi = np.where(kk == 0, 4, np.where(kk < 3, 3, np.where(kk > 18, 0, bi)))
    basalt = _pick(BASALT, bi)
    drift = (vnoise(X, Y, 14, 763) > 0.6) & (kk > 3)
    basalt = np.where(drift[..., None], _pick(ASH, np.where((X + Y) % 2 == 1, 1, 2)), basalt)
    crack = (ridged(X, Y, 18, 767) > 0.97) & (vnoise(X, Y, 60, 768) > 0.55)
    basalt = np.where(crack[..., None], _pick(LAVA, np.where((X + Y) % 3 == 0, 2, 1)), basalt)
    # the shore of the two: sand blown over the first of the basalt
    near = np.abs(_blend_cells(X, Y, ashy) - 0.5) < 0.04
    ground = np.where(ash[..., None], basalt, sand)
    ground = np.where((near & ash & ((X * 7 + Y * 3) % 5 < 2))[..., None], _pick(DESERT, np.full(X.shape, 2)), ground)
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    _paint(cv, ground, inside)
    things = []
    for i, j, bx, by in _scatter(col, row, 190, 150, 1301, margin=280):
        # a few landmarks with open country between them, never a field of stamps
        if noise2(i, j, 1303) < 0.72:
            continue
        fld = _blend_cells(np.array([[bx]]), np.array([[by]]), ashy)[0, 0]
        if abs(fld - 0.5) < 0.12:
            continue  # the change of ground stays open
        size = 0.5 + noise2(i, j, 1304) ** 2 * 1.1
        if fld > 0.5:
            w = int(80 + 110 * size) // 8 * 8
            h = int(w * (0.5 + noise2(i, j, 1306) * 0.2)) // 8 * 8
            img = ('cone', w, h, (i * 31 + j) % 17)
        else:
            w = int(100 + 150 * size) // 8 * 8
            h = int(w * (0.45 + noise2(i, j, 1305) * 0.35)) // 8 * 8
            img = ('mesa', w, h, (i * 31 + j) % 17)
        left, top = int(bx - w / 2), int(by - h)
        if _free_of_zones(zone_at, left, top, w, h):
            things.append((by, left, top, img))
    for (by, left, top, (kind, w, h, seed)) in sorted(things):
        img = _cinder_cone(w, h, seed) if kind == 'cone' else _mesa(w, h, seed)
        _place(cv, img, left, top, x0, y0)
    return cv


def isles_cell(col: int, row: int, zone_at) -> Canvas:
    """Open sea round the Tidebloom Isles, in the islands' own water, the swells and
    whitecaps running on from cell to cell."""
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + CW), np.arange(y0, y0 + CH))
    sea = _sea_rgb(X, Y, np.full(X.shape, -10 ** 6))
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    _paint(cv, sea, inside)
    return cv


def moon_cell(col: int, row: int, zone_at) -> Canvas:
    """Lumen's plain, running on round the base: grey regolith, craters of every size
    (each rim lit on its upper left and its bowl shaded on the same side, as the light
    falls), scattered rocks with their shadows, and nothing alive on it."""
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + CW), np.arange(y0, y0 + CH))
    n = vnoise(X, Y, 40, 1401) * 0.7 + vnoise(X, Y, 9, 1402) * 0.3
    ri = np.where(n > 0.62, 4, np.where(n > 0.32, 3, 2))
    ground = _pick(REGOLITH, ri)
    for i, j, bx, by in _scatter(col, row, 70, 60, 1411, margin=60):
        if noise2(i, j, 1413) < 0.55:
            continue
        r = 4 + noise2(i, j, 1414) ** 3 * 44  # many small craters, a few big ones
        dx, dy = (X - bx) / r, (Y - by) / (r * 0.72)
        d = np.hypot(dx, dy)
        bowl = d < 1
        rim = (d >= 1) & (d < 1.22)
        lit_side = (dx + dy) > 0  # inside the bowl the far (lower right) wall catches the light
        ground = np.where((bowl & ~lit_side)[..., None], _pick(REGOLITH, np.full(X.shape, 1)), ground)
        ground = np.where((bowl & lit_side)[..., None], _pick(REGOLITH, np.full(X.shape, 3)), ground)
        ground = np.where((rim & ((dx + dy) < 0))[..., None], _pick(REGOLITH, np.full(X.shape, 5)), ground)
        ground = np.where((rim & ((dx + dy) >= 0))[..., None], _pick(REGOLITH, np.full(X.shape, 2)), ground)
    rocks = (vnoise(X, Y, 3, 1421) > 0.86) & (vnoise(X, Y, 50, 1422) > 0.45)
    ground = np.where(rocks[..., None], _pick(REGOLITH, np.full(X.shape, 4)), ground)
    shadow = np.roll(np.roll(rocks, 1, 0), 1, 1) & ~rocks
    ground = np.where(shadow[..., None], _pick(REGOLITH, np.full(X.shape, 0)), ground)
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    _paint(cv, ground, inside)
    return cv


CELL_PAINTERS = {'valley': None, 'west': west_cell, 'isles': isles_cell, 'moon': moon_cell}


def cells(layout: dict, region: str, ring: int = 1):
    """The cells of scenery a region needs: its grid's gaps and a ring round it."""
    if region not in CELL_PAINTERS:
        return {}
    paint = CELL_PAINTERS[region] or valley_cell
    cols = [c for c, _r in layout.values()]
    rows = [r for _c, r in layout.values()]
    taken = {tuple(v): k for k, v in layout.items()}
    zone_at = lambda c, r: taken.get((c, r))  # noqa: E731
    _wooded[:] = [(*layout[z], side) for (z, side) in sorted(WOODED.get(region, ())) if z in layout]
    out = {}
    for row in range(min(rows) - ring, max(rows) + ring + 1):
        for col in range(min(cols) - ring, max(cols) + ring + 1):
            if (col, row) not in taken:
                if region == 'moon' and row < 0:
                    continue  # above the moon's horizon there is only space (the backdrop)
                out[(col, row)] = paint(col, row, zone_at)
    return out
