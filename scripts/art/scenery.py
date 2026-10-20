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
from pixel import Canvas, disc, noise2, oval, smooth_noise

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
# (y 1531); under the zones the sea starts at their bottom edge. Past the Headland's
# east side the land runs on down beside it, and the coast comes round under its corner
# as the Headland's own sea cliff (HEADLAND_CLIFF), then away north-east (world review
# 20 Oct 07:53, finding 2: the Headland's grass was cut straight against open sea).
VALLEY_COAST = [(-960, 1108), (-640, 1112), (-320, 1115), (-36, 1140), (-14, 1158), (-1, 1158),
                (0, 1721), (300, 1662), (560, 1650), (640, 1792), (662, 1810), (692, 1818), (732, 1802),
                (790, 1748), (870, 1592), (1000, 1420), (1280, 1400)]
# Region x over which the coast is the Headland's sea cliff: its foot (valley_zones'
# coast_top and coast_height, the Headland's row) up to its east side, then carried on
# round its corner, the face sinking into the beach by the east end.
HEADLAND_CLIFF = (560, 820)
HEADLAND_ROW = 2
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


@functools.lru_cache(maxsize=1)
def _headland_line():
    """The Headland's sea cliff in region px, over HEADLAND_CLIFF: (x, the foot's y
    up to its east side, the face's height). Past its east side the face's height runs
    on and sinks to nothing over the last 80 px."""
    import valley_zones as vz  # (loaded by zones.py)
    xs = np.arange(HEADLAND_CLIFF[0], HEADLAND_CLIFF[1] + 1)
    foot = np.array([HEADLAND_ROW * H + vz.coast_top(int(x)) + vz.coast_height(int(x)) for x in xs], dtype=float)
    hts = np.array([vz.coast_height(int(x)) for x in xs], dtype=float)
    hts = np.where(xs > 640, hts * np.clip((HEADLAND_CLIFF[1] - xs) / 80, 0, 1), hts)
    return xs, foot, hts


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
    # (beside the Headland the shore is its own cliff's foot, to the pixel)
    hx, hfoot, _hh = _headland_line()
    under = (X >= HEADLAND_CLIFF[0]) & (X <= 640)
    coast = np.where(under, np.interp(X, hx, hfoot), coast)
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
    hx, _hf, hh = _headland_line()
    h_face = np.where((X >= HEADLAND_CLIFF[0]) & (X <= HEADLAND_CLIFF[1]), np.interp(X, hx, hh), 0)
    sand = (X > CLIFF_COAST_X) & coast_free & ~sea & (Y - coast > -10) & (h_face < 3)
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
    if zone_at(1, HEADLAND_ROW) == 'headland' and x0 < HEADLAND_CLIFF[1] and x0 + CW > HEADLAND_CLIFF[0]:
        # the Headland's sea cliff runs on out of its bottom edge and round its corner,
        # drawn as the zone draws it (its seed, in its own px), so the face's blocks run
        # on across the seam; only the part in this cell is kept
        zox, zoy = W, HEADLAND_ROW * H
        tops, hts = {}, {}
        for cx in range(CW):
            Xc = x0 + cx
            h = int(round(float(h_face[0, cx])))
            if h < 3:
                continue
            sea_top = int(math.floor(coast[0, cx])) + 1
            tops[Xc - zox], hts[Xc - zox] = sea_top - h - zoy, h
        if tops:
            tmp = Canvas(CW, CH)
            vz.cliff(_Shift(tmp, zox - x0, zoy - y0), tops, hts, seed=982)
            a = np.array(tmp.img)
            keep = (a[..., 3] > 0) & inside
            arr = np.array(cv.img)
            arr[keep] = a[keep]
            cv.img.paste(Image.fromarray(arr, 'RGBA'))

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


# The fire country and the desert past Sunstone's zones (world review 20 Oct 15:53,
# finding 1: dunes ran straight into Hearthold's ash on the zone's edge, a stone's throw
# from the lava moat). Sand never meets lava country directly (world-rules 4): from the
# fire zones out, the ground is the zones' own ash with basalt ridges in it, then cooled
# crust, then scrub, and sand only toward the desert's zones. The grade follows how far a
# point lies from the fire zones against how far from the desert's, so it bends round
# every zone and never lies along a cell's edge.
FIRE_ZONES = ('caldera', 'springs', 'hearthold', 'scorch')
SAND_ZONES = ('gulch', 'oasis')
FIRE_X, FIRE_Y = 320, 1152      # layout px to sunstone_zones' fire-country coordinates (the caldera's)
SCRUB = ['#2A2E20', '#454A2E', '#62683C', '#80844E', '#A3A26A']   # dusty creosote and sage


def _fire_ash_np(X, Y):
    """sunstone_zones.fire_ash at layout px, vectorised (the same noise and thresholds),
    so the ground carries on across a fire zone's edge with no change."""
    FX, FY = X - FIRE_X, Y + FIRE_Y
    n = vnoise(FX, FY, 30, 261)
    i = np.where((n > 0.3) | ((n > 0.26) & ((FX + FY) % 2 == 1)), 2, 1)
    rgb = _pick(ASH, i)
    g = _hash(FX // 2, FY, 270)
    rgb = np.where((g > 0.965)[..., None], _pick(BASALT, np.full(X.shape, 2)), rgb)
    rgb = np.where(((g > 0.95) & (g <= 0.965))[..., None], _pick(ASH, np.full(X.shape, 3)), rgb)
    return rgb


def _plates(X, Y, size: float, seed: int):
    """Cooled crust broken into plates: per point its plate's hash, the distance to the
    plate's edge, and whether that edge lies up and to the left (a jittered Voronoi)."""
    gx, gy = np.floor(X / size).astype(np.int64), np.floor(Y / size).astype(np.int64)
    best = np.full(X.shape, 1e9)
    second = np.full(X.shape, 1e9)
    hid = np.zeros(X.shape)
    bdx = np.zeros(X.shape)
    bdy = np.zeros(X.shape)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = gx + ox, gy + oy
            px = (cx + 0.15 + 0.7 * _hash(cx, cy, seed)) * size
            py = (cy + 0.15 + 0.7 * _hash(cx, cy, seed + 1)) * size
            d = np.hypot(X - px, Y - py)
            closer = d < best
            second = np.where(closer, best, np.minimum(second, d))
            hid = np.where(closer, _hash(cx, cy, seed + 2), hid)
            bdx = np.where(closer, X - px, bdx)
            bdy = np.where(closer, Y - py, bdy)
            best = np.minimum(best, d)
    return hid, second - best, (bdx + bdy) < 0


def _sunstone_grade(X, Y, zone_at):
    """0 at a fire zone's edge .. 1 at a desert zone's, wandering; and the distance to the
    nearest fire zone (px)."""
    c0, r0 = int(np.floor(X.min() / W)), int(np.floor(Y.min() / H))
    c1, r1 = int(np.floor(X.max() / W)), int(np.floor(Y.max() / H))
    fire, sand = [], []
    for r in range(r0 - 3, r1 + 4):
        for c in range(c0 - 3, c1 + 4):
            z = zone_at(c, r)
            if z in FIRE_ZONES:
                fire.append((c * W, r * H, (c + 1) * W, (r + 1) * H))
            elif z in SAND_ZONES:
                sand.append((c * W, r * H, (c + 1) * W, (r + 1) * H))
    df = _zone_dist(X, Y, fire) if fire else np.full(X.shape, 4000.0)
    ds = _zone_dist(X, Y, sand) if sand else np.full(X.shape, 4000.0)
    t = df / (df + ds + 1.0)
    away = np.clip(np.minimum(df, ds) / 60, 0, 1)   # (the wander dies out at a zone's edge)
    t = t + away * (0.16 * (wnoise(X, Y, 70, 1311) - 0.5) + 0.06 * (vnoise(X, Y, 14, 1312) - 0.5))
    return t, df


def west_cell(col: int, row: int, zone_at) -> Canvas:
    """Sunstone Reach's surroundings. Round the fire country: the zones' own grey ash
    running on past their edges with its cinders, rubble and drifts, low basalt ridges lit
    on their west, cinder cones; then the old flows cooled to a crust of dark plates with
    ash in the cracks; then scrub (creosote and sage on gravelly sand, dry tufts); then
    the open desert's long dunes and sandstone buttes round the gulch and the oasis."""
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + CW), np.arange(y0, y0 + CH))
    t, df = _sunstone_grade(X, Y, zone_at)
    # dunes: a wandering crest line, light rising to the crest, the lee in shade
    lx = X + (vnoise(0 * X, Y, 60, 781) * 40).astype(int)
    k = (Y + (np.sin(lx / 23.0) * 9 + vnoise(X, 0 * Y, 50, 782) * 18).astype(int)) % 46
    di = np.where(k < 2, 5, np.where(k < 12, 4, np.where(k > 38, 2, 3)))
    di = np.where((k > 34) & ((X + Y) % 2 == 1), 2, di)
    ripple = (Y + (np.sin(X / 8.0 + Y / 37.0) * 2).astype(int)) % 7
    di = np.where((ripple == 0) & (k > 14) & (k < 32), 4, di)
    sand = _pick(DESERT, di)
    # scrub: gravelly sand in low, soft patches, grit lit on its upper left
    gn = vnoise(X, Y, 16, 1321)
    gravel = _pick(DESERT, np.where(gn > 0.62, 3, np.where(gn > 0.3, 2, 1)))
    grit = _hash(X // 2, Y, 1322) > 0.94
    gravel = np.where(grit[..., None], np.where((X % 2 == 0)[..., None], _pick(ASH, np.full(X.shape, 3)),
                                                 _pick(ASH, np.full(X.shape, 1))), gravel)
    # cooled crust: plates of old lava, each its own tone, lit on its upper-left lip, dark
    # joints with ash blown into the widest of them
    hid, edge, up_left = _plates(X, Y, 17.0, 1331)
    ci = np.where(hid > 0.7, 3, 2)
    crust = _pick(BASALT, ci)
    dust = vnoise(X, Y, 12, 1333) > 0.58   # ash lying in soft patches on the plates
    crust = np.where((dust & (hid < 0.7))[..., None], _pick(ASH, np.full(X.shape, 1)), crust)
    crust = np.where((edge < 0.9)[..., None], _pick(BASALT, np.full(X.shape, 0)), crust)
    crust = np.where(((edge >= 0.9) & (edge < 1.9) & up_left)[..., None], _pick(BASALT, np.full(X.shape, 4)), crust)
    dusted = (edge < 0.9) & (vnoise(X, Y, 9, 1332) > 0.55)
    crust = np.where(dusted[..., None], _pick(ASH, np.full(X.shape, 2)), crust)
    # the fire country: the zones' ash, with outcrops of basalt standing out of it away
    # from the zones' edges, seen in the three-quarter view: a top lit on its upper-left
    # lip, a south face of columns in shade, a shadow cast down and right on the ash
    ash = _fire_ash_np(X, Y)
    FH = 5
    top_at = lambda XX, YY: (wnoise(XX, YY, 34, 1341) > 0.79) & (_sunstone_grade(XX, YY, zone_at)[1] > 40)  # noqa: E731
    XX = np.broadcast_to(np.arange(x0 - 2, x0 + CW)[None, :], (CH + FH + 2, CW + 2))
    YY = np.broadcast_to(np.arange(y0 - FH - 2, y0 + CH)[:, None], (CH + FH + 2, CW + 2))
    tops = top_at(XX, YY) & (_sunstone_grade(XX, YY, zone_at)[0] < 0.3)
    top = tops[FH + 2:, 2:]
    face = np.zeros(top.shape, dtype=bool)
    for d in range(1, FH + 1):
        face |= tops[FH + 2 - d:FH + 2 - d + CH, 2:]
    face &= ~top
    shadow = np.zeros(top.shape, dtype=bool)
    for d in range(FH + 1, FH + 3):
        shadow |= tops[FH + 2 - d:FH + 2 - d + CH, 1:CW + 1]
    shadow &= ~top & ~face
    lip = top & ~tops[FH + 1:FH + 1 + CH, 1:CW + 1]
    ti = np.where(vnoise(X, Y, 6, 1343) > 0.55, 3, 2)
    ash = np.where(shadow[..., None], _pick(ASH, np.full(X.shape, 0)), ash)
    ash = np.where(top[..., None], _pick(BASALT, ti), ash)
    ash = np.where(lip[..., None], _pick(BASALT, np.full(X.shape, 4)), ash)
    col_i = np.where((X % 3) == 0, 0, np.where((X % 3) == 1, 1, 2))
    ash = np.where(face[..., None], _pick(BASALT, col_i), ash)
    # the bands, interleaved in clumps where they meet so no change runs along a line
    clump = vnoise(X, Y, 7, 1351) * 0.7 + vnoise(X, Y, 3, 1352) * 0.3
    tt = t + (clump - 0.5) * 0.08
    ground = np.where((tt < 0.3)[..., None], ash, np.where((tt < 0.44)[..., None], crust,
                                                          np.where((tt < 0.62)[..., None], gravel, sand)))
    # drifts where one ground lies over the next: ash over the crust's edge, sand over the scrub's
    drift_a = (tt >= 0.3) & (tt < 0.34) & (vnoise(X, Y, 5, 1353) > 0.55)
    ground = np.where(drift_a[..., None], _pick(ASH, np.where((X + Y) % 3 == 0, 3, 2)), ground)
    drift_s = (tt >= 0.56) & (tt < 0.62) & (vnoise(X, Y, 6, 1354) > 0.5)
    ground = np.where(drift_s[..., None], _pick(DESERT, np.where(k < 12, 4, 3)), ground)
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    _paint(cv, ground, inside)
    rc = _RegionCv(cv, x0, y0)
    xa, xb, ya, yb = col * W, (col + 1) * W, row * H, (row + 1) * H

    def t_at(px, py):
        return float(_sunstone_grade(np.array([[float(px)]]), np.array([[float(py)]]), zone_at)[0][0, 0])

    # what lies on the ash (as sunstone_zones.ash_dressing): rubble heaps and pale drifts
    for i, j, bx, by in _scatter(col, row, 26, 22, 1361, margin=20):
        if noise2(i, j, 1362) < 0.55:
            continue
        bx, by = int(bx), int(by)
        if not (xa - 6 <= bx < xb + 6 and ya - 4 <= by < yb + 4):
            continue
        tv = t_at(bx, by)
        if tv < 0.28:
            if noise2(i, j, 1363) < 0.62:
                for kk in range(2 + int(noise2(i, j, 1364) * 3)):
                    detail.pebble(rc, bx + int((noise2(i, kk, 1365) - 0.5) * 9), by + int((noise2(i, kk, 1366) - 0.5) * 5),
                                  BASALT, big=kk == 0 and noise2(i, j, 1367) > 0.6)
            else:
                n = 4 + int(noise2(i, j, 1368) * 4)
                for kk in range(n):
                    rc.set(bx + kk, by, ASH[3] if kk % 3 else ASH[4])
                    if 0 < kk < n - 1:
                        rc.set(bx + kk + 1, by + 1, ASH[1])
        elif 0.44 <= tv < 0.64:
            # a scrub bush: a rounded clump, lit on its upper left, its shadow on the sand
            rx = 2 + int(noise2(i, j, 1369) * 3)
            ry = max(1, rx - 1)
            for yy in range(by - ry, by + ry + 1):
                for xx in range(bx - rx, bx + rx + 1):
                    u, v = (xx - bx) / (rx + 0.5), (yy - by) / (ry + 0.5)
                    if u * u + v * v <= 1:
                        s = u + v
                        rc.set(xx, yy, SCRUB[3] if s < -0.5 else SCRUB[2] if s < 0.3 else SCRUB[1])
            for xx in range(bx - rx + 1, bx + rx + 2):
                rc.darken(xx, by + ry + 1)
            rc.set(bx - 1, by - ry, SCRUB[4])
        elif 0.62 <= tv < 0.7 and noise2(i, j, 1370) < 0.6:
            # a dry tuft at the scrub's edge
            for kk, (dx, dy) in enumerate(((0, 0), (-1, -1), (1, -1), (0, -2))):
                rc.set(bx + dx, by + dy, '#B89A5E' if kk else '#8A6E42')
    # landmarks: cinder cones in the fire country, buttes in the open desert, the change of
    # ground between them left open
    things = []
    for i, j, bx, by in _scatter(col, row, 190, 150, 1301, margin=280):
        if noise2(i, j, 1303) < 0.72:
            continue
        tv = t_at(bx, by)
        if 0.24 < tv < 0.7:
            continue
        size = 0.5 + noise2(i, j, 1304) ** 2 * 1.1
        if tv <= 0.24:
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


# ---- Cogsworth's surroundings (world review 20 Oct 07:53, finding 1) -------------------
# The steam town's land past its edges, in its own style. The main line runs on east and
# west in brick cuttings to a tunnel portal each side, telegraph poles along it. Behind
# the engine yard a brick yard wall with bills on it, the terraces' back yards and their
# backs, a street, the fronts of the next row, the works' chimneys over the roofs. The
# square's setts run on as pavements and streets between houses and warehouses. The
# canal runs on west past a row of warehouses, down through a lock and under a road
# bridge, and east to a basin fed from the north by a culverted feeder; the atmospheric
# tube runs on east on its trestles into its pumping house. South of the town a hedged
# lane and soot-darkened fields. Everything is laid out in region px (the Junction's own,
# the Canal's plus 576 down), so the ground at every seam is the zone's own drawing
# carried on (city_zones.junction and canal: the cinder yard, the rails, the setts, the
# towpaths, the canal's water and walls, the sooty grass), and everything that stands
# is placed in the region and drawn by every cell it reaches.
SOOT_G = ['#2B3B2E', '#46583F', '#5C6E4C', '#6B7C55', '#8E9C6E']   # city_zones' sooty grass
GRANITE = ['#3A3A42', '#55555E', '#73737A', '#93918F', '#B4B0A8', '#D2CDC2']
SL = ['#8C8574', '#A9A28F', '#C2B9A2', '#D4CBB3', '#E6DEC8']       # worlds.paint_paving's slabs
IRON, BRICK, ASHLAR_, SLATE_ = MATERIALS['iron'], MATERIALS['brick'], MATERIALS['ashlar'], MATERIALS['slate']
BROWN = ['#2A1A16', '#46302A', '#5E4236', '#7A5846', '#98725A']   # steampunk_props' darker brick
TAR_, SOIL, BRASS = MATERIALS['tar'], MATERIALS['soil'], MATERIALS['brass']
HEDGE = ['#141F18', '#1E2E22', '#2A3F2C', '#3A5236', '#4E6644']    # a hedge dulled by the smoke
# more bricks and slates, so a wall or a roof is laid from several kilns and quarries
# (Eastward's walls and roofs carry many close tones; one ramp a surface reads flat)
BLUE_BRICK = ['#22202A', '#34303E', '#4A4456', '#605A6E', '#7A7488']   # engineering brick
RED_BRICK = ['#3A1C14', '#5E2C1E', '#844230', '#A85A40', '#C87A58']    # a hotter-fired brick
OCHRE_BRICK = ['#3A2A18', '#5A4224', '#7A5A32', '#9A7444', '#B89058']  # a yellow stock brick
WELSH = ['#2E2A38', '#46405A', '#5E5874', '#7C7692', '#A49EB6']        # purple Welsh slate
GREEN_SLATE = ['#2E3A34', '#46564C', '#5E7064', '#7A8C80', '#9AAAA0']  # green Lakeland slate
LICHEN = ['#4E5432', '#6E7444', '#8E9450', '#B0B060']
RIDGE = MATERIALS['roof']                                              # red clay ridge tiles
CURTAIN = (('#6E2A24', '#9A3E30'), ('#2E4A34', '#46684A'), ('#C8BC98', '#E2D8B8'), ('#3A3E6A', '#545A8E'))
for _ramp in (BLUE_BRICK, RED_BRICK, OCHRE_BRICK, WELSH, GREEN_SLATE, LICHEN):
    for _i, _c in enumerate(_ramp):  # (so detail.shade steps these along their own ramps too)
        detail._LOOKUP.setdefault(_rgb(_c), (_ramp, _i))
CANAL_Y = 576                  # the Canal zone's top, region px
RAIL_Y0 = 82                   # city_zones.junction: paint_rails(cv, 82)
STEAM_RAIL = (RAIL_Y0 - 3, RAIL_Y0 + 16)
CY0, CY1 = CANAL_Y + 176, CANAL_Y + 244     # the canal's water between its walls (canal: CY0, CY1)
TOW_N = (CANAL_Y + 126, CY0)                # the towpaths of setts
TOW_S = (CY1 + 2, CANAL_Y + 292)
TUBE = (CANAL_Y + 340, CANAL_Y + 356, CANAL_Y + 372)   # the brass tube, and its trestles' foot
PORTAL_W, PORTAL_E = -136, W + 150          # the main line's tunnel portals (centre x)
LOCK = (-122, -66)                          # the lock west of the town: its chamber (x)
BRIDGE = (-240, -198)                       # the road over the canal west (x), parapets included
BASIN = (404, 596, CANAL_Y + 150, CANAL_Y + 270)   # the basin east: x0, x1, its water's y0, y1
FEEDER = (566, 580, CANAL_Y + 54)           # the feeder channel's x span, its culvert's foot
ENGINE_X = 456                              # the tube's pumping house (its west wall)
LANE = (1172, 1192)                         # the hedged lane south of the town
# the rows of terraces behind the yard wall: (foot, back or front), their yards, streets
ROWS = ((-84, True), (-224, False), (-372, True), (-512, False))
YARDS = ((-84, -56), (-372, -330))
STREETS = ((-224, -190), (-512, -478))


def _sgrid(col, row):
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + W + 2 * S), np.arange(y0, y0 + H + 2 * S))
    return x0, y0, X, Y


def _smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _steam_d(X):
    """How far past the town's west or east edge a point lies (0 inside its columns)."""
    return np.maximum(np.maximum(-X, X - (W - 1)), 0)


def _cut_h(X):
    """The height of the main line's cutting wall: none by the town, rising to 22 px."""
    return np.round(22 * _smooth((_steam_d(X) - 16) / 56)).astype(int)


def _frame_y(X, Y):
    """The zone frame a point's grass reads its noise in: the Junction's (region y) above
    a line that wanders away from the zones, the Canal's (y - 576) below it."""
    k = np.clip(_steam_d(X) / 60, 0, 1)
    line = CANAL_Y + k * 34 * (vnoise(X, 0 * X, 47, 1801) - 0.5)
    return np.where(Y >= line, Y - CANAL_Y, Y)


def _const(c, shape):
    return np.broadcast_to(np.array(_rgb(c), dtype=np.uint8), tuple(shape) + (3,))


def _soot_grass(X, Y):
    """city_zones' sooty grass (worlds.grass in the zones' ramp): two close tones in broad
    patches with two-pixel blades, read in the frame of the zone it runs on from."""
    fy = _frame_y(X, Y)
    n = vnoise(X, fy, 22, 11)
    tone = np.where(n < 0.62, 2, 3)
    out = _pick(SOOT_G, tone)
    blade = _hash(X, fy, 9) <= 0.055
    below = np.roll(tone, -1, axis=0) == tone
    for (sel, top, root) in ((tone == 3, 4, 2), (tone == 2, 3, 1)):
        b = blade & below & sel
        out = np.where(b[..., None], _pick(SOOT_G, np.full(X.shape, top)), out)
        out = np.where(np.roll(b, 1, axis=0)[..., None], _pick(SOOT_G, np.full(X.shape, root)), out)
    return out, tone


def _cinders(X, Y, seed=1):
    """city_zones.cinder_yard, in region px: cinders and ballast in small lumps, oil-dark
    where engines stood, sooty grass in the corners."""
    n = _hash(X // 3, Y // 2, 1720 + seed)
    k = (X // 3 + (Y // 2) * 7) % 5
    idx = np.where(n > 0.8, 3, np.where(n > 0.45, 2, np.where(n > 0.15, 5, 1)))
    pal = np.array([_rgb(c) for c in IRON] + [_rgb(ST[1])], dtype=np.uint8)
    joint = ((X % 3 == 0) | (Y % 2 == 0)) & (k != 0)
    idx = np.where(joint, np.where(idx == 1, 0, 1), idx)
    oil = vnoise(X, Y, 18, 1721 + seed) > 0.76
    idx = np.where(oil, np.where((X + Y) % 2 == 1, 0, 1), idx)
    out = pal[idx]
    weed = (vnoise(X, Y, 11, 1722 + seed) < 0.16) & ((X + Y) % 3 != 0)
    return np.where(weed[..., None], np.where(((X + Y) % 2 == 1)[..., None], _const('#46583F', X.shape),
                                              _const('#5C6E4C', X.shape)), out)


def _fan(X, Y, seed=1, R=15):
    """city_zones.paint_fan, in region px: setts laid in fans, each lit on its top edge."""
    sh = np.where((Y // R) % 2 == 1, R, 0)
    col = (X + sh) // (2 * R)
    u = X + sh - col * 2 * R - R
    yy = Y + R - np.sqrt(np.maximum(0.0, R * R - u * u)) * 0.85
    row = (yy // 4).astype(int)
    along = X + row * 3
    stone = along // 5
    r, a = yy.astype(int) % 4, along % 5
    t = _hash(stone, row, 1701 + seed)
    base = np.where(t > 0.78, 4, np.where(t > 0.3, 3, 2))
    idx = np.where((r == 0) | (a == 0), 1, np.where(r == 1, np.where(t > 0.78, 5, 4),
                   np.where((r == 3) | (a == 4), np.where(base != 2, 2, 1), base)))
    return _pick(GRANITE, idx)


# Claude C's lock in the Canal (#132): its north half is the lock side, paved at towpath
# level from the bridge to the zone's east edge, and above its head gates the upper pound
# stands higher (a shallower dry face, a wet band, lighter water). Where the Canal's own
# ground shows that at its east edge, the scenery carries both on: the lock side runs on
# LOCK_RUN px to a coped end, and the canal east of the town, the basin with it, is the
# upper pound. (Read from the zone's picture, so either form of the Canal meets its land.)
LOCK_SIDE_Z = 205      # city_zones.LOCK_SIDE: the lock side's coping row (canal px)
LOCK_RUN = 28          # how far past the seam the lock side runs before its coped end


@functools.lru_cache(maxsize=1)
def _canal_lock_side() -> bool:
    g = _zone_ground('canal').astype(int)
    patch = g[180:200, W - 8]
    return bool(patch.sum(axis=1).mean() > 240)   # setts there (mean ~330), not dark water (~160)


def _upper_pound(X, Y, top):
    """city_zones.canal_lock's upper pound in region px: a dry face of four courses, a wet
    band, the wall's shadow on the water, the lighter water of the higher pound."""
    k = Y - top
    yl = Y - CANAL_Y
    n = vnoise(X, yl, 8, 494)
    out = np.where((n > 0.6)[..., None], _const('#3A5E54', X.shape),
                   np.where((n > 0.3)[..., None], _const('#2E5048', X.shape), _const('#264640', X.shape)))
    out = np.where((k < 9)[..., None], _const('#1A3430', X.shape), out)
    out = np.where((k < 6)[..., None], _const('#2A3A30', X.shape), out)
    dry = np.where((((X + (k // 3) * 4) // 8) % 2) == 1, 2, 1)
    return np.where((k < 4)[..., None], _pick(ASHLAR_, dry), out)


def _cobbles(X, Y):
    """worlds.paint_cobbles, in region px: rounded cobbles, a lit top left and a dark gap."""
    cx = X % 10
    cy = (Y + (X // 10) % 2 * 4) % 8
    n = _hash(X // 10, (Y + (X // 10) % 2 * 4) // 8, 81)
    pal = np.array([_rgb(c) for c in SLATE_] + [_rgb('#A7A291')], dtype=np.uint8)
    base = np.where(n < 0.5, 3, 5)
    idx = np.where((cx == 0) | (cy == 0), 1, np.where((cx <= 2) & (cy <= 2), 4,
                   np.where((cx >= 8) | (cy >= 6), 2, base)))
    return pal[idx]


def _bricks_np(X, Y, ramp=BRICK, seed=0, base=2):
    """detail.bricks in region px: bricks three rows tall and six wide, staggered, each
    with a lit top edge and its own tone, laid from several kilns (the main brick, a
    darker, a hotter-fired and the odd blue engineering brick), the mortar lit where the
    light catches its joint."""
    ci, r = Y // 3, Y % 3
    shift = np.where(ci % 2 == 1, 3, 0)
    bi, c = (X + shift) // 6, (X + shift) % 6
    h = _hash(ci, bi, 1811 + seed)
    t = base + np.where(h > 0.78, 1, np.where(h < 0.18, -1, 0))
    idx = np.clip(np.where((r == 0) & (h > 0.45), t + 1, t), 0, 4)
    k = _hash(ci, bi, 1813 + seed)
    out = _pick(ramp, idx)
    for (lo, hi, alt) in ((0.0, 0.22, BROWN if ramp is not BROWN else BRICK), (0.22, 0.34, RED_BRICK), (0.34, 0.4, BLUE_BRICK)):
        out = np.where(((k >= lo) & (k < hi))[..., None], _pick(alt, idx), out)
    return np.where(((r == 2) | (c == 5))[..., None], _const('#2A2622', X.shape), out)


def _canal_water(X, Y, face=6, top=CY0):
    """city_zones.canal's water, in region px: the north wall's face in ashlar (`face`
    rows, taller where the water lies lower), murky green water, the wall's shadow on
    it, and ripples, read in the Canal's frame."""
    yl = Y - CANAL_Y
    k = Y - top
    wall = np.where(((X // 7 + k // 3) % 2) == 1, 1, 2)
    wall = np.where(k == 0, 4, wall)
    n = vnoise(X, yl, 8, 494)
    wat = np.where(n > 0.6, 0, np.where(n > 0.3, 1, 2))
    wpal = np.array([_rgb(c) for c in ('#2C4A44', '#22403A', '#1A3430', '#14281F', '#3E6A5E')], dtype=np.uint8)
    wat = np.where(k < face + 3, 3, wat)
    rip = ((Y - top) % 6 == 2) & (_hash(X // 7, yl, 495) > 0.62) & (k >= face + 3)
    wat = np.where(rip, 4, wat)
    out = wpal[wat]
    return np.where((k < face)[..., None], _pick(ASHLAR_, wall), out)


def _rails_np(X, Y):
    """paint_rails in region px: ballast, sleepers lit on top, two rails with a bright
    running edge (the sleepers keep the zone's seven-pixel spacing)."""
    y0 = RAIL_Y0
    n = _hash(X, Y, 141)
    out = _pick(ST, np.where(n > 0.55, 2, np.where(n > 0.15, 1, 3)))
    sx = (X - 1) % 7
    sl = (sx < 4) & (Y >= y0) & (Y < y0 + 13)
    sl_i = np.where(sx == 0, np.where(Y == y0, 3, 2), np.where(sx == 1, 2, np.where(sx == 2, 1, np.where(Y > y0, 1, 2))))
    out = np.where(sl[..., None], _pick(WOOD, sl_i), out)
    for ry in (y0 + 2, y0 + 9):
        for (dy, i) in ((0, 4), (1, 2), (2, 0)):
            out = np.where((Y == ry + dy)[..., None], _pick(IRON, np.full(X.shape, i)), out)
    return out


def _field_kind(X, Y):
    """Which field a point south of the lane lies in, and what grows there: 0 ploughed,
    1 cabbages, 2 stubble, 3 rough pasture. The hedges between them wander."""
    fx = np.floor_divide(X + 420 + (vnoise(0 * X, Y, 90, 1844) * 36).astype(int), 260)
    fy = np.floor_divide(Y - LANE[1] - 14 + (vnoise(X, 0 * X, 110, 1845) * 30).astype(int), 190)
    return (fx * 5 + fy * 3 + 7) % 4, fx, fy


def _fields(X, Y):
    """The fields: ploughed earth in furrows lying across the slope (each field its own
    way), cabbages in rows on dark soil, pale stubble in drill lines, rough pasture; all
    dulled by the works' smoke, with soot-dark patches where the wind drops it."""
    kind, fx, fy = _field_kind(X, Y)
    tilt = ((fx * 3 + fy) % 3 - 1) * 0.18
    yy = Y + (X * tilt).astype(int) + (vnoise(X, 0 * X, 40, 1846) * 4).astype(int)
    f = yy % 5
    DIRT = ['#1E1714', '#2C221C', '#3A2E25', '#4A3B2F', '#5E4C3C']   # soil darkened by the smoke
    plough = _pick(DIRT, np.where(f == 0, 4, np.where(f == 1, 3, np.where(f == 4, 1, 2))))
    red = _hash(X // 9, yy // 5, 1974) > 0.6   # each run of furrow its own earth, some redder
    plough = np.where((red & (f > 0))[..., None], _pick(['#2A1A14', '#3A241C', '#4E3226', '#644030', '#7A5240'],
                                                         np.where(f == 1, 3, np.where(f == 4, 1, 2))), plough)
    clod = (_hash(X // 2, yy // 2, 1847) > 0.88) & (f > 1)
    plough = np.where(clod[..., None], _pick(DIRT, np.full(X.shape, 4)), plough)
    r6 = yy % 7
    cx = (X + (yy // 7) % 2 * 3) % 6
    gone = _hash((X + (yy // 7) % 2 * 3) // 6, yy // 7, 1852) < 0.14   # a head lifted, a gap in the row
    big = _hash((X + (yy // 7) % 2 * 3) // 6, yy // 7, 1853) > 0.6
    head = (r6 >= 1 - big) & (r6 <= 4) & (cx >= 1 - big) & (cx <= 4 + big) & ~gone
    ci = np.where((r6 <= 1) | (cx <= 1), 3, np.where((r6 == 4) | (cx >= 4), 1, 2))
    cab = np.where(head[..., None], _pick(['#22301F', '#344A2C', '#4C6338', '#647A48'], ci),
                   _pick(['#1E1714', '#2C221C', '#3A2E25', '#4A3B2F'], np.where(r6 == 0, 1, 2)))
    st_ = _pick(['#4A4436', '#5E5644', '#746A52', '#8A7E62', '#A09474'],
                np.where(f == 0, 1, np.where((f == 2) & ((X + yy // 5) % 3 == 0), 4, np.where(f == 3, 2, 3))))
    past, _t = _soot_grass(X, Y)
    out = np.where((kind == 0)[..., None], plough, np.where((kind == 1)[..., None], cab,
                   np.where((kind == 2)[..., None], st_, past)))
    soot = (vnoise(X, Y, 30, 1848) > 0.72) & ((X + Y) % 2 == 0)
    return np.where(soot[..., None], (out * 0.82).astype(np.uint8), out), kind


def _steam_masks(X, Y):
    """What ground lies at each region point round Cogsworth, one mask a kind."""
    d = _steam_d(X)
    west, east = X < 0, X >= W
    side = west | east
    hw = _cut_h(X)
    on_line = (west & (X > PORTAL_W)) | (east & (X < PORTAL_E))
    m = {'d': d, 'side': side}
    m['track'] = on_line & (Y >= STEAM_RAIL[0]) & (Y < STEAM_RAIL[1])
    m['wall'] = on_line & (Y >= STEAM_RAIL[0] - hw) & (Y < STEAM_RAIL[0]) & (hw > 0)
    m['coping'] = on_line & (Y >= STEAM_RAIL[0] - hw - 2) & (Y < STEAM_RAIL[0] - hw) & (hw > 0)
    m['scoping'] = on_line & (d > 26) & (Y >= STEAM_RAIL[1]) & (Y < STEAM_RAIL[1] + 4)
    rag = (vnoise(X, Y, 14, 1803) - 0.5) * 26 + (vnoise(X, Y, 3, 1804) - 0.5) * 5   # a ragged edge onto grass
    hill = ((west & (X < PORTAL_W + 24 + rag)) | (east & (X > PORTAL_E - 24 - rag))) & (Y > -16 + rag * 0.6)
    m['yard'] = ((Y >= -34) & (Y < 0) & ~hill) | (side & on_line & ~hill & (Y >= 0) & (Y < STEAM_RAIL[0] - hw - 2)) | \
        (west & (X > BRIDGE[1] + 6 + rag) & (Y >= 286) & (Y < 404) & (d >= 14)) | \
        (east & (Y >= 348) & (Y < 476) & (d >= 14) & (X < 500 + rag))
    edge = 406 + (np.sin(X / 41) * 5 + vnoise(X, 0 * X, 23, 152) * 10).astype(int)
    street = (west & (Y >= 232) & (Y < 286)) | (east & (Y >= 300) & (Y < 348))
    road = (X >= BRIDGE[0] + 4) & (X < BRIDGE[1] - 4) & (Y >= 232) & (Y < LANE[0])
    m['setts'] = side & (((d < 14) & (Y >= 136) & (Y < edge)) | street | road
                         | ((d > 26) & (Y >= STEAM_RAIL[1] + 4) & (Y < 136)))
    near = np.roll(m['setts'], 1, axis=0) | np.roll(m['setts'], -1, axis=0) | np.roll(m['setts'], 1, axis=1) | np.roll(m['setts'], -1, axis=1)
    m['kerb'] = side & ~m['setts'] & near
    m['ncob'] = Y < -56          # behind the yard wall: streets, ginnels and yards
    for (a, b) in STREETS:
        m['ncob'] |= (Y >= a) & (Y < b)
    m['ash'] = np.zeros(X.shape, dtype=bool)
    for (a, b) in YARDS:
        m['ash'] |= (Y >= a) & (Y < b)
    m['towpath'] = side & (((Y >= TOW_N[0]) & (Y < TOW_N[1])) | ((Y >= TOW_S[0]) & (Y < TOW_S[1])))
    m['canal'] = side & (Y >= CY0) & (Y < CY1) & ~((X >= BASIN[0]) & (X < BASIN[1]))
    # (the lock side over the canal's north half, past the seam, when the Canal has its lock)
    m['lockside'] = (X >= W) & (X < W + LOCK_RUN) & (Y >= CY0 - 1) & (Y < CANAL_Y + LOCK_SIDE_Z + 2) & _canal_lock_side()
    m['canal'] &= ~m['lockside']
    m['basin'] = (X >= BASIN[0]) & (X < BASIN[1]) & (Y >= BASIN[2]) & (Y < BASIN[3])
    m['quay'] = east & (X >= BASIN[0] - 14) & (X < BASIN[1] + 18) & (Y >= BASIN[2] - 34) & (Y < BASIN[3] + 26) & ~m['basin']
    m['feeder'] = (X >= FEEDER[0]) & (X < FEEDER[1]) & (Y >= FEEDER[2]) & (Y < BASIN[2] - 1)
    wob = (vnoise(X, 0 * X, 80, 1841) * 6).astype(int)
    m['lane'] = (Y >= LANE[0] + wob) & (Y < LANE[1] + wob)
    m['field'] = Y >= LANE[1] + wob + 14
    return m


def _rich(X, Y):
    """How far a point lies from the town (0 at its edge, 1 from 50 px out): the ground
    is the zone's own at the seam and gathers its own dressing further out."""
    dx = np.maximum(np.maximum(-X, X - (W - 1)), 0)
    dy = np.maximum(np.maximum(-Y, Y - (2 * H - 1)), 0)
    return np.clip((np.hypot(dx, dy) - 10) / 40, 0, 1)


def _dressing(X, Y, out, m, grass, rich):
    """The ground's dressing away from the town (Eastward's ground is never one texture):
    on the grass, soft patches of shade and light, ragwort and willowherb, bare cinder
    where it is worn; on cinders, rust stains, ash and spilt coal; on the water, scum,
    leaves, an oily sheen and the light on the ripples; on setts, puddles and moss in the
    joints; in the fields, stones and weeds."""
    def col(c):
        return _const(c, X.shape)

    def put(mask, rgb):
        nonlocal out
        out = np.where(mask[..., None], rgb, out)
    chk = (X + Y) % 2 == 0
    r1 = _hash(X // 7, Y // 7, 1950) < 0.09 * rich          # one weed in a 7 px cell, now and then
    cx, cy = X % 7, Y % 7
    g = grass & (rich > 0)
    shade = g & ((vnoise(X, Y, 16, 1951) > 0.72) | ((vnoise(X, Y, 16, 1951) > 0.68) & chk)) & (rich > 0.3)
    put(shade, np.where((out == _rgb(SOOT_G[3])).all(-1)[..., None], col(SOOT_G[2]), col(SOOT_G[1])))
    lit = g & ((vnoise(X, Y, 19, 1952) > 0.76) | ((vnoise(X, Y, 19, 1952) > 0.72) & chk)) & (rich > 0.3)
    put(lit & (out == _rgb(SOOT_G[2])).all(-1), col(SOOT_G[3]))
    mott = g & (vnoise(X, Y, 3.5, 1970) > 0.64) & (rich > 0.15) & (vnoise(X, Y, 3.5, 1971) > 0.4)
    put(mott, np.where((out == _rgb(SOOT_G[3])).all(-1)[..., None], col('#647550'), np.where((out == _rgb(SOOT_G[2])).all(-1)[..., None], col('#52653F'), out)))
    clover = g & (vnoise(X, Y, 6, 1972) > 0.78) & (rich > 0.4)
    put(clover, np.where(((X // 2 + Y // 2) % 3 == 0)[..., None], col('#728A5A'), col('#56704A')))
    put(clover & (_hash(X // 3, Y // 3, 1973) > 0.9) & (X % 3 == 0) & (Y % 3 == 0), col('#E8E2D2'))
    bare = g & (vnoise(X, Y, 20, 1953) > 0.86) & (rich > 0.6)   # worn to the earth
    put(bare, _pick(['#2E2620', '#3E342A', '#4E4234', '#62543E'], np.where(vnoise(X, Y, 4, 1976) > 0.6, 3, np.where(vnoise(X, Y, 20, 1953) > 0.84, 1, 2))))
    rag = g & r1 & (_hash(X // 7, Y // 7, 1960) > 0.5)
    put(rag & (cx >= 2) & (cx <= 3) & (cy >= 2) & (cy <= 3), np.where((cy == 2)[..., None], col('#E8C860'), col('#C8A848')))
    put(rag & (cx == 3) & (cy == 4), col(SOOT_G[1]))
    herb = g & r1 & ~rag
    put(herb & (cx == 3) & (cy >= 1) & (cy <= 3), np.where((cy == 1)[..., None], col('#D898B8'), col('#B87898')))
    put(herb & (cx == 3) & (cy == 4), col(SOOT_G[1]))
    cin = (m['yard'] | m['ash']) & (rich > 0)
    put(cin & (vnoise(X, Y, 10, 1954) > 0.76) & chk, col('#6A4A30'))
    put(cin & (vnoise(X, Y, 10, 1954) > 0.82), col('#8A5A38'))
    put(cin & (vnoise(X, Y, 14, 1955) > 0.8) & ~chk, col('#8A8A90'))
    put(cin & (vnoise(X, Y, 14, 1955) > 0.85), col('#A4A4AA'))
    lump = cin & (_hash(X // 3, Y // 3, 1961) > 0.94) & (X % 3 < 2) & (Y % 3 < 2)
    put(lump, np.where(((X % 3 == 0) & (Y % 3 == 0))[..., None], col('#45465A'), col('#14131A')))
    wet = (m['canal'] | m['basin']) & (rich > 0) & ~((out == _rgb(ASHLAR_[1])).all(-1) | (out == _rgb(ASHLAR_[2])).all(-1) | (out == _rgb(ASHLAR_[4])).all(-1)
                                                   | (out == _rgb('#2A3A30')).all(-1) | (out == _rgb('#1A3430')).all(-1))
    put(wet & (vnoise(X, Y, 16, 1956) > 0.74), col('#34503A'))   # scum drifting in rafts
    put(wet & (vnoise(X, Y, 16, 1956) > 0.8), col('#4E6A44'))
    put(wet & (vnoise(X, Y, 16, 1957) > 0.82), col('#3E4A64'))   # an oily sheen where the works drain
    hi = wet & ((Y + X // 11) % 9 == 0) & (_hash(X // 6, Y, 1962) > 0.35)   # light on the ripples, 6 px
    put(hi, col('#5E8A7E'))
    put(hi & (X % 6 < 2), col('#86AAA0'))
    leaf = wet & (_hash(X // 6, Y // 4, 1963) > 0.93) & (X % 6 < 3) & (Y % 4 < 2)
    put(leaf, np.where((Y % 4 == 0)[..., None], col('#A07A42'), col('#6A4A2A')))
    pave = (m['setts'] | m['ncob'] | m['towpath'] | m['quay'] | m['lockside']) & (rich > 0)
    cob = (_hash(X // 10, (Y + (X // 10) % 2 * 4) // 8, 1978) * rich)
    face = pave & ((out == _rgb(SLATE_[3])).all(-1) | (out == _rgb('#A7A291')).all(-1))   # a cobble's body only
    put(face & (cob > 0.7), col('#8A7E6E'))   # a brown stone
    put(face & (cob > 0.55) & (cob <= 0.7), col(GRANITE[3]))
    pv = vnoise(X, Y, 11, 1958)
    pud = pave & (pv > 0.82)   # puddles: dark with the sky in them, lit along their far edge
    rim = pud & ~(np.roll(pud, 1, axis=0) & np.roll(pud, 1, axis=1))
    put(pud, np.where((pv > 0.86)[..., None], col('#3A4650'), col('#4A5A66')))
    put(rim, col('#7A8A94'))
    joint = pave & ((out.astype(int).sum(-1)) < 200) & (vnoise(X, Y, 7, 1959) > 0.62)
    put(joint, np.where(chk[..., None], col('#3A4A34'), col('#4C5E40')))
    fld = m['field']
    put(fld & (_hash(X // 4, Y // 3, 1964) > 0.95) & (X % 4 < 2) & (Y % 3 == 0), np.where((X % 4 == 0)[..., None], col(ST[3]), col(ST[2])))
    put(fld & (_hash(X // 6, Y // 4, 1965) > 0.93) & (X % 6 == 2) & (Y % 4 < 2), np.where((Y % 4 == 0)[..., None], col(SOOT_G[3]), col(SOOT_G[1])))
    poppy = fld & (_hash(X // 8, Y // 5, 1969) > 0.95) & (X % 8 < 2) & (Y % 5 == 1)
    put(poppy, np.where((X % 8 == 0)[..., None], col('#C83A2E'), col('#8E2A22')))
    put(fld & (vnoise(X, Y, 9, 1975) > 0.83) & ((X + Y) % 3 == 0), col('#4A5A66'))   # standing water in the furrows
    return out


def _steam_ground(X, Y):
    """The ground round Cogsworth at region points: (rgb, grass tone or -1 where it is not
    open grass (so tufts grow only there), the masks)."""
    m = _steam_masks(X, Y)
    out, tone = _soot_grass(X, Y)
    grass = np.ones(X.shape, dtype=bool)

    def put(mask, rgb):
        nonlocal out, grass
        out = np.where(mask[..., None], rgb, out)
        grass &= ~mask
    put(m['yard'], _cinders(X, Y))
    # the lane: packed cinder and earth, two wheel ruts, grass down its crown, puddles
    wob = (vnoise(X, 0 * X, 80, 1841) * 6).astype(int)
    ly = Y - LANE[0] - wob
    rut = (ly == 5) | (ly == 6) | (ly == 13) | (ly == 14)
    lane = _pick(['#2E2620', '#3E342A', '#544636', '#6A5A44', '#84725A'],
                 np.where(rut, 1, np.where(_hash(X // 3, ly // 2, 1842) > 0.7, 3, 2)))
    lane = np.where((rut & (ly % 2 == 1))[..., None], _pick(IRON, np.full(X.shape, 1)), lane)
    crown = (ly >= 8) & (ly <= 11) & (vnoise(X, Y, 9, 1849) > 0.45)
    lane = np.where(crown[..., None], _pick(SOOT_G, np.where((X + ly) % 3 == 0, 3, 2)), lane)
    puddle = rut & (vnoise(X, Y, 13, 1850) > 0.74)
    lane = np.where(puddle[..., None], np.where(((X + Y) % 5 == 0)[..., None], _const('#6A7A84', X.shape),
                                                _const('#3A4650', X.shape)), lane)
    put(m['lane'], lane)
    fields, _k = _fields(X, Y)
    put(m['field'], fields)
    fan = m['setts'] & ((m['d'] < 30) | ~(((Y >= 232) & (Y < 286)) | ((Y >= 300) & (Y < 348)) | ((X >= BRIDGE[0]) & (X < BRIDGE[1]))))
    put(m['setts'] & ~fan, _cobbles(X, Y))
    put(fan, _fan(X, Y))
    put(m['setts'] & ((m['d'] == 30) | (m['d'] == 31)), _pick(GRANITE, np.where(m['d'] == 30, 4, 2)))
    st_rows = ((Y >= 232) & (Y < 286)) | ((Y >= 300) & (Y < 348))
    gut = m['setts'] & ~fan & st_rows & ((Y == 233) | (Y == 284) | (Y == 301) | (Y == 346))
    put(gut, _pick(GRANITE, np.where(((X // 3) % 2 == 0), 1, 0)))
    grate = m['setts'] & ~fan & st_rows & ((X % 44) < 6) & (((Y >= 280) & (Y < 284)) | ((Y >= 342) & (Y < 346)))
    put(grate, np.where(((X % 2 == 0) & ((Y % 4) != 0))[..., None], _const(IRON[0], X.shape), _const(IRON[3], X.shape)))
    cover = m['setts'] & ~fan & st_rows & (np.hypot((X % 70) - 35, (Y - (258 + 66 * (Y >= 300))) * 1.4) < 4)
    put(cover, np.where((((X % 70) - 35 + (Y - 258)) < 0)[..., None], _const(IRON[3], X.shape), _const(IRON[1], X.shape)))
    litter = m['setts'] & ~fan & (_hash(X // 4, Y // 3, 1967) > 0.985) & (X % 4 < 2) & (Y % 3 == 0)
    put(litter, np.where((_hash(X // 3, Y // 2, 1968) > 0.5)[..., None], _const('#E8E2D2', X.shape), _const('#C8A848', X.shape)))
    put(m['kerb'] & ~m['yard'], _pick(ST, np.where(np.roll(m['setts'], -1, axis=0), 3, 1)))
    put(m['ncob'] | m['towpath'] | m['quay'], _cobbles(X, np.where(Y >= CANAL_Y, Y - CANAL_Y, Y)))
    put(m['ash'], _cinders(X, Y, seed=4))
    side = m['side']
    for (ky, c) in ((TOW_N[0] - 1, ST[3]), (TOW_S[1], ST[3]), (TOW_S[1] + 1, ST[1])):
        put(side & (Y == ky) & ~m['quay'], _const(c, X.shape))  # the towpaths' kerbs, as the zone's
    put(m['track'], _rails_np(X, Y))
    put(m['wall'], _bricks_np(X, Y, BRICK, seed=3, base=2))
    put(m['coping'], _pick(ST, np.where(Y == STEAM_RAIL[0] - _cut_h(X) - 2, 4, 2)))
    put(m['scoping'], _pick(ST, np.select([Y == STEAM_RAIL[1], Y == STEAM_RAIL[1] + 1, Y == STEAM_RAIL[1] + 2], [4, 3, 2], 1)))
    # the canal west and east of the town, a step lower past the lock (a taller wall shows)
    low = X < LOCK[1]
    upper = _canal_lock_side()
    east_water = _upper_pound(X, Y, CY0) if upper else _canal_water(X, Y)
    put(m['canal'], np.where(low[..., None], _canal_water(X, Y, face=10), east_water))
    for (ky, c) in ((CY0 - 1, ASHLAR_[3]), (CY1, ASHLAR_[5]), (CY1 + 1, ASHLAR_[3])):
        put((Y == ky) & side & ~((X >= BASIN[0]) & (X < BASIN[1])), _const(c, X.shape))
    # the basin: the canal widened between quay walls, copings round it
    put(m['basin'], _upper_pound(X, Y, BASIN[2]) if upper else _canal_water(X, Y, top=BASIN[2]))
    if upper:
        # the lock side carried on past the seam: setts at towpath level over the canal's
        # north half, its coping over the pound, its east end coped; the pound below it
        ls = CANAL_Y + LOCK_SIDE_Z
        run = (X >= W) & (X < W + LOCK_RUN)
        put(run & (Y >= CY0 - 1) & (Y < ls), _cobbles(X, Y - CANAL_Y))
        alt = (vnoise(X // 9 * 9, 0 * X, 9, 1784) > 0.5)
        cope = np.where(((X // 9) % 2 == 1)[..., None], _pick(GRANITE, np.full(X.shape, 5)), _pick(GRANITE, np.full(X.shape, 4)))
        cope = np.where(alt[..., None], cope, np.where(((X // 9) % 2 == 1)[..., None], _pick(ASHLAR_, np.full(X.shape, 5)),
                                                         _pick(ASHLAR_, np.full(X.shape, 4))))
        put(run & (Y == ls), cope)
        put(run & (Y == ls + 1), np.where((X % 9 == 0)[..., None], _pick(ASHLAR_, np.full(X.shape, 1)), _pick(ASHLAR_, np.full(X.shape, 3))))
        put(run & (Y >= ls + 2) & (Y < CY1), _upper_pound(X, Y, ls + 2))
        end = W + LOCK_RUN
        put((X == end - 2) & (Y >= CY0 - 1) & (Y < ls + 2), _pick(ASHLAR_, np.full(X.shape, 5)))
        put((X == end - 1) & (Y >= CY0 - 1) & (Y < ls + 2), _pick(ASHLAR_, np.full(X.shape, 3)))
    for (ky, c) in ((BASIN[2] - 1, ASHLAR_[3]), (BASIN[2] - 2, ASHLAR_[5]), (BASIN[3], ASHLAR_[5]), (BASIN[3] + 1, ASHLAR_[3])):
        put((Y == ky) & (X >= BASIN[0] - 2) & (X < BASIN[1] + 2), _const(c, X.shape))
    for (kx, c) in ((BASIN[0] - 2, ASHLAR_[5]), (BASIN[0] - 1, ASHLAR_[3]), (BASIN[1], ASHLAR_[5]), (BASIN[1] + 1, ASHLAR_[3])):
        open_ = (kx < BASIN[1]) & (Y >= CY0 - 1) & (Y < CY1 + 2)
        put((X == kx) & (Y >= BASIN[2] - 2) & (Y < BASIN[3] + 2) & ~open_, _const(c, X.shape))
    # the lock: its chamber narrower than the canal between broad stone copings, the
    # water in it and below it a step down (its wall's face taller)
    lk = (X >= LOCK[0]) & (X < LOCK[1])
    nw, sw = CY0 + 12, CY1 - 12
    put(lk & (Y >= CY0 - 3) & (Y < nw), _pick(ASHLAR_, np.where(Y == CY0 - 3, 5, np.where(((X // 9 + (Y - CY0) // 4) % 2) == 0, 4, 3))))
    put(lk & (Y >= sw) & (Y < CY1 + 3), _pick(ASHLAR_, np.where(Y >= CY1 + 1, 2, np.where(((X // 9 + (Y - sw) // 4) % 2) == 0, 4, 3))))
    put(lk & (Y >= nw) & (Y < sw), _canal_water(X, Y, face=12, top=nw))
    put(lk & (Y == sw - 1), _pick(ASHLAR_, np.full(X.shape, 1)))
    # the road over the canal west: a humpback deck of setts, lighter at its crown
    deck = (X >= BRIDGE[0] + 4) & (X < BRIDGE[1] - 4) & (Y >= TOW_N[0] - 4) & (Y < TOW_S[1] + 4)
    crown = 1 - np.abs(Y - (CY0 + CY1) / 2) / ((TOW_S[1] - TOW_N[0]) / 2 + 4)
    put(deck, np.clip(_fan(X, Y).astype(int) * (0.86 + 0.18 * crown[..., None]), 0, 255).astype(np.uint8))
    # the feeder: a narrow stone channel down from its culvert, stepping in small weirs
    fx = X - FEEDER[0]
    fw = FEEDER[1] - FEEDER[0]
    feed = _pick(MATERIALS['water'], np.where((Y + fx // 2) % 6 == 0, 3, np.where(fx < 6, 2, 1)))
    weir = ((Y - FEEDER[2]) % 24 < 2) & (Y > FEEDER[2] + 6)
    feed = np.where(weir[..., None], _const('#EEF5F8', X.shape), feed)
    feed = np.where((fx < 2)[..., None], _pick(ASHLAR_, np.where(fx == 0, 4, 3)), feed)
    feed = np.where((fx >= fw - 2)[..., None], _pick(ASHLAR_, np.where(fx == fw - 1, 1, 2)), feed)
    put(m['feeder'], feed)
    out = _dressing(X, Y, out, m, grass, _rich(X, Y))
    return out, np.where(grass, tone, -1), m


# ---- what stands round Cogsworth ------------------------------------------------------
def _mixed_bricks(cv, x0, y0, w, h, main=BRICK, seed=0):
    """Bricks on a sprite, laid from several kilns as _bricks_np lays them."""
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]
    rgb = _bricks_np(xx, yy, main, seed=seed, base=2 if main is BROWN else 3)
    for j in range(h):
        for i in range(w):
            cv.set(x0 + i, y0 + j, tuple(int(v) for v in rgb[j, i]) + (255,))
HOUSE = 34          # one house of a terrace, party wall to party wall
STOREYS = (42, 32)  # the ground storey and the one above (verticality.md, section 5)


def _sp():
    import steampunk_props
    return steampunk_props


@functools.lru_cache(maxsize=96)
def _terrace_row(n: int, seed: int, back: bool, roof: int = 0):
    """A terrace of n houses in the three-quarter view, as one sprite: (image, its foot
    row). A roof whose ridge runs along the row (the far plane a lit sliver, the near
    plane in courses of slates, a tone a slate, the odd one replaced, moss low down),
    brick stacks with their pots on every other party wall, a gutter and the eaves'
    shadow, brick walls (each house its own brick), a stone footing. `back` shows the
    rear: a small sash, a plank back door, the scullery window, drainpipes, soot; else
    the street front: sash windows with lintels and sills, panelled doors with fanlights
    and steps. `roof` 0 slate, 1 tarred iron."""
    sp = _sp()
    R = (SLATE_, TAR_)[roof]
    w = n * HOUSE + 2
    stack_h, far, ridge, near = 16, 5, 2, 22
    wall = sum(STOREYS)
    ry = stack_h + far             # the ridge's row
    ey = ry + ridge + near         # the eaves
    foot = ey + wall + 4
    cv = Canvas(w, foot + 2)

    def rnd(a, b=0, c=0):
        return noise2(seed * 31 + a, b, 1851 + c)
    for x in range(1, w - 1):
        for y in range(stack_h, ry):  # the far plane: it faces the light
            c = R[4] if (y - stack_h) % 3 == 0 else R[3]
            if (x + (y // 3) * 2) % 5 == 0:
                c = R[2]
            cv.set(x, y, c)
        red = roof == 0 and seed % 3 == 0   # some rows have red clay ridge tiles
        RR = RIDGE if red else R
        cv.set(x, ry, RR[4] if x % 4 else RR[3]); cv.set(x, ry + 1, RR[2] if x % 4 else RR[1])
        for y in range(ry + ridge, ey):  # the near plane, in courses of slates
            k, r = divmod(y - ry - ridge, 3)
            sx = (x + (k % 2) * 2) // 5
            t = rnd(sx, k)
            q = rnd(sx, k, 2)   # slates from three quarries, as a roof is patched over the years
            Q = (WELSH if q > 0.62 else GREEN_SLATE if q < 0.1 else R) if roof == 0 else R
            base = 3 if t > 0.86 else 1 if t < 0.16 else 2
            c = Q[base + 1 if r == 0 and base < 4 else base]
            if r == 2 or (x + (k % 2) * 2) % 5 == 0:
                c = Q[0]
            if roof == 1:   # corrugated iron sheets, tarred, the odd one new, rust where the tar has gone
                sheet = (x // 12 + k // 3) % 5
                c = R[3] if x % 3 == 0 else R[2] if x % 3 == 1 else R[1]
                if sheet == 0:
                    c = ('#8E8E99', '#64646F', '#474753')[x % 3]
                if vnoise(np.array(x + seed * 50), np.array(y), 7, 1977) > 0.68:
                    c = ('#8A5432', '#6A3E24', '#4A2A1A')[x % 3]
                if r == 2 and k % 3 == 2:
                    c = R[0]   # the sheets' overlap
            if rnd(x // 3, k, 1) > 0.86 and r != 2 and y > ry + 6:
                c = LICHEN[2 if r == 0 else 1] if rnd(x // 2, k, 3) > 0.4 else LICHEN[0]   # lichen on the slates
            cv.set(x, y, c)
        cv.set(x, ey, IRON[3]); cv.set(x, ey + 1, IRON[1])  # the gutter
    for k in range(n):
        hx = 1 + k * HOUSE
        ramp = BROWN if rnd(k, 2) > 0.55 else OCHRE_BRICK if rnd(k, 14) > 0.85 else BRICK
        _mixed_bricks(cv, hx, ey + 2, HOUSE, wall, ramp, seed=seed * 7 + k)
        for x in range(hx, hx + HOUSE):  # soot low on the wall
            for y in range(ey + wall - 2, ey + wall + 2):
                detail.shade(cv, x, y, 1)
        up, gr = ey + 2 + 8, ey + 2 + STOREYS[1] + 6
        flip = (k + seed) % 2
        if back:
            sp.sash(cv, hx + (6 if flip else HOUSE - 18), up, 10, 14, lit=rnd(k, 3) > 0.6)
            dx = hx + (HOUSE - 15 if flip else 4)
            for y in range(ey + wall - 28, ey + wall + 2):
                for x in range(dx, dx + 11):
                    c = WOOD[2] if (x - dx) % 4 else WOOD[1]
                    if x == dx:
                        c = WOOD[3]
                    if y in (ey + wall - 27, ey + wall - 12) and dx < x < dx + 10:
                        c = WOOD[1]  # the ledges across the planks
                    cv.set(x, y, c)
            paint = (('#2E4A34', '#46684A', '#5E8460'), ('#6E2A24', '#9A3E30', '#B85A44'),
                     ('#2C3E4C', '#3E566A', '#5A7690'), (WOOD[1], WOOD[2], WOOD[3]))[int(rnd(k, 15) * 4)]
            for y in range(ey + wall - 27, ey + wall + 1):  # the back door painted, the paint worn
                for x in range(dx + 1, dx + 10):
                    if rnd(x, y, 16) > 0.18:
                        cv.set(x, y, paint[1] if (x - dx) % 4 else paint[0])
                cv.set(dx + 1, y, paint[2])
            cv.set(dx + 8, ey + wall - 13, BRASS[4]); cv.set(dx + 8, ey + wall - 12, BRASS[1])
            cv.hline(dx - 1, ey + wall - 29, 13, ST[3]); cv.hline(dx - 1, ey + wall - 28, 13, ST[1])
            sp.sash(cv, hx + (17 if flip else 4), gr + 4, 10, 12, lit=rnd(k, 4) > 0.5)
            if rnd(k, 17) > 0.5:  # a tin bath hung on a nail by the door
                bx, by = hx + (8 if flip else HOUSE - 14), ey + wall - 36
                for (x, y) in oval(bx + 3, by + 3, 4, 2.5):
                    cv.set(x, y, IRON[4] if y < by + 2 else IRON[3] if x < bx + 4 else IRON[2])
                cv.set(bx + 3, by - 1, IRON[1])
        else:
            for j, wx in enumerate((hx + 4, hx + HOUSE - 16)):
                sp.sash(cv, wx, up, 12, 16, lit=rnd(k, 5 + j) > 0.45)
            dx = hx + (3 if flip else HOUSE - 17)
            paint = [['#1E2A34', '#2C3E4C', '#3E566A', '#5A7690'], ['#2A1C1A', '#4A2A24', '#6E3A2E', '#8E5040'],
                     ['#1C2A22', '#2A4234', '#3A5A46', '#567A60']][int(rnd(k, 8) * 3)]
            sp.panel_door(cv, dx, ey + wall + 1, 14, 30, paint)
            wx = hx + (19 if flip else 4)
            sp.sash(cv, wx, gr + 2, 12, 16, lit=rnd(k, 9) > 0.4)
            if rnd(k, 18) > 0.45:  # a window box of geraniums on the sill
                for x in range(wx - 1, wx + 13):
                    cv.set(x, gr + 20, WOOD[3]); cv.set(x, gr + 21, WOOD[1])
                    if (x + k) % 3:
                        cv.set(x, gr + 19, '#3A5A30' if x % 2 else '#4E7A3A')
                    if (x + k) % 4 == 0:
                        cv.set(x, gr + 18, ('#D84A3A', '#E8C24A', '#E8E2D2')[(x + k) % 3])
            cv.set(dx + 6, ey + wall - 24, BRASS[4]); cv.set(dx + 8, ey + wall - 24, BRASS[3])  # the number
        px = hx + HOUSE - 2  # the drainpipe down the party wall, with its brackets, rusting
        for y in range(ey + 1, ey + wall + 2):
            cv.set(px, y, IRON[3]); cv.set(px + 1, y, IRON[1])
            if (y - ey) % 9 == 0:
                cv.hline(px - 1, y, 4, IRON[2])
            elif (y - ey) % 9 in (1, 2) and rnd(k, y, 23) > 0.4:
                cv.set(px, y, '#8A5432'); cv.set(px + 1, y, '#5A3420')
        if back and rnd(k, 24) > 0.4:  # a pot on the scullery sill
            sx_ = hx + (17 if flip else 4) + 3
            sy_ = gr + 4 + 12 + 1
            cv.set(sx_, sy_ - 1, '#B85A44'); cv.set(sx_ + 1, sy_ - 1, '#8E4030'); cv.set(sx_ + 2, sy_ - 1, '#B85A44')
            cv.set(sx_ + 1, sy_ - 2, '#4E7A3A'); cv.set(sx_, sy_ - 3, '#3A5A30'); cv.set(sx_ + 2, sy_ - 3, '#5E8A44')
        for t in range(2):  # soot streaks down from the eaves
            sx = hx + 3 + int(rnd(k, 10 + t) * (HOUSE - 8))
            for y in range(ey + 2, ey + 2 + 6 + int(rnd(k, 12 + t) * 14)):
                if (sx + y) % 3:
                    detail.shade(cv, sx, y, 1)
                    detail.shade(cv, sx + 1, y, 1)
    # curtains hung at the outer sides of the panes, each house its own colour
    glass = {_rgb(SLATE_[2]), _rgb(SLATE_[1]), _rgb(MATERIALS['lamplight'][2]), _rgb(MATERIALS['lamplight'][3])}
    warm = {_rgb(MATERIALS['lamplight'][2]), _rgb(MATERIALS['lamplight'][3])}
    for k in range(n):
        if rnd(k, 20) < 0.25:
            continue  # (no curtains here)
        cl = CURTAIN[int(rnd(k, 19) * 4)]
        for y in range(ey + 2, ey + wall):
            runs, x = [], 1 + k * HOUSE
            while x < 1 + (k + 1) * HOUSE:
                if cv.get(x, y)[:3] in glass:
                    a_ = x
                    while cv.get(x, y)[:3] in glass:
                        x += 1
                    runs.append((a_, x - 1))
                x += 1
            for i, (a_, b_) in enumerate(runs):
                if i + 1 < len(runs) and runs[i + 1][0] - b_ == 2:      # the left pane of a sash
                    pts = (a_, a_ + 1)
                elif i > 0 and a_ - runs[i - 1][1] == 2:                 # the right pane
                    pts = (b_ - 1, b_)
                else:
                    continue
                for x in pts:
                    lit = cv.get(x, y)[:3] in warm
                    cv.set(x, y, cl[1] if lit else cl[0])
    detail.overhang_shadow(cv, 1, w - 1, ey + 2, lambda x: 2, k=1)
    detail.stones(cv, 0, ey + wall + 2, w, 3, ST, seed=seed + 3, course=3)
    for k in range(n):  # a skylight in the odd roof: an iron frame, the glass catching the sky
        if rnd(k, 21) > 0.62:
            lx = 1 + k * HOUSE + 10 + int(rnd(k, 22) * 10)
            for y in range(ry + 6, ry + 14):
                for x in range(lx, lx + 8):
                    edge = x in (lx, lx + 7) or y in (ry + 6, ry + 13)
                    cv.set(x, y, IRON[1] if edge else ('#9AB4C8' if y < ry + 9 else '#5E7890'))
            cv.hline(lx, ry + 14, 8, SLATE_[0])
    for k in range(n):  # pigeons along the ridge, grey with a lit back
        if rnd(k, 25) > 0.55:
            px_ = 1 + k * HOUSE + 6 + int(rnd(k, 26) * 20)
            cv.set(px_, ry - 2, '#9A9AA4'); cv.set(px_ + 1, ry - 2, '#B4B4BC'); cv.set(px_ + 2, ry - 1, '#6A6A74')
            cv.set(px_, ry - 1, '#7A7A84'); cv.set(px_ + 1, ry - 1, '#8A8A94'); cv.set(px_ - 1, ry - 2, '#4A4A54')
            cv.set(px_ + 1, ry, '#C8A040')
    for k in range(0, n + 1, 2):  # the stacks, on every other party wall, lead flashed round
        sx = min(w - 11, max(0, k * HOUSE - 4))
        for x in range(sx - 2, sx + 12):
            cv.set(x, ry + 3, '#7A8494' if x < sx + 5 else '#5A6474'); cv.set(x, ry + 4, '#5A6474')
        sp.brick_stack(cv, sx, ry - 10, ry + 3, w=10, pots=2 + (k // 2) % 2)
    style.close_outline(cv)
    return cv.img, foot


@functools.lru_cache(maxsize=4)
def _mill(w: int = 186, seed: int = 1):
    """A mill of four storeys: long brick walls with rows of tall windows under stone
    arches, a stone string course under each floor, pilasters between the bays, a slate
    roof with a glazed lantern along its ridge. (image, foot row)."""
    floors, fh = 4, 26
    roof_h = 30
    wall_top = roof_h
    foot = wall_top + floors * fh + 4
    cv = Canvas(w, foot + 2)
    for x in range(1, w - 1):
        for y in range(6, roof_h):
            if y < 11:
                c = SLATE_[4] if (y - 6) % 3 == 0 else SLATE_[3]
            elif y < 13:
                c = SLATE_[4] if y == 11 else SLATE_[2]
            else:
                k, r = divmod(y - 13, 3)
                c = SLATE_[2] if r else SLATE_[3]
                if r == 2 or (x + k * 2) % 6 == 0:
                    c = SLATE_[0]
            cv.set(x, y, c)
        cv.set(x, roof_h, IRON[3]); cv.set(x, roof_h + 1, IRON[1])
    for x in range(w // 2 - 22, w // 2 + 22):  # the lantern
        for y in range(1, 11):
            c = '#E8E2D2' if y < 3 else ('#5A7690' if (x // 3) % 2 else '#3E566A') if y < 9 else SLATE_[1]
            if x in (w // 2 - 22, w // 2 + 21):
                c = IRON[1]
            cv.set(x, y, c)
    _mixed_bricks(cv, 1, wall_top + 2, w - 2, floors * fh, BRICK, seed=seed + 50)
    for f in range(floors):
        y0 = wall_top + 2 + f * fh
        cv.hline(1, y0, w - 2, ST[4]); cv.hline(1, y0 + 1, w - 2, ST[2])
        for wx in range(8, w - 12, 14):
            lit = noise2(wx, f, 1901 + seed)
            glass = (MATERIALS['lamplight'][2], MATERIALS['lamplight'][3]) if lit > 0.62 else \
                ('#B8782E', '#F0B85A') if lit > 0.5 else ('#2C3E4C', '#3E566A') if lit > 0.2 else ('#1E2A34', '#5A7690')
            for y in range(y0 + 6, y0 + 22):
                for x in range(wx, wx + 8):
                    c = (glass[0] if y > y0 + 13 else glass[1]) if (x - wx) % 4 else '#B8B0A0'
                    if (x - wx) % 4 and noise2(x, y, 1902 + seed) > 0.95:
                        c = '#14131A'  # a broken pane
                    if y in (y0 + 6, y0 + 13):
                        c = '#B8B0A0'
                    cv.set(x, y, c)
            cv.hline(wx - 1, y0 + 22, 10, ST[4]); cv.hline(wx - 1, y0 + 23, 10, ST[1])
            for x in range(wx - 1, wx + 9):
                cv.set(x, y0 + 5, ST[3] if x < wx + 4 else ST[2])
    for y in range(wall_top + 2, foot - 2):
        for bx in range(4, w - 4, 42):
            cv.set(bx, y, BRICK[4]); cv.set(bx + 1, y, BRICK[3]); cv.set(bx + 2, y, BRICK[1])
    for x in range(30, w - 30):  # the mill's name painted along the top floor
        for y in range(wall_top + 3, wall_top + 7):
            c = '#E8DCC0' if 0 < y - wall_top - 3 < 3 else '#2A1A16'
            if c == '#E8DCC0' and y == wall_top + 4 and (x // 2) % 4 and 36 < x < w - 36:
                c = '#6E2A24'
            cv.set(x, y, c)
    for dp in (2 + 42 * 2 - 6, w - 8):  # drainpipes, rusting; soot down from the gutter
        for y in range(wall_top + 2, foot - 4):
            cv.set(dp, y, IRON[3] if (y // 2) % 7 else '#8A5432'); cv.set(dp + 1, y, IRON[1] if (y // 2) % 7 else '#5A3420')
    for i in range(9):
        sx = 10 + int(noise2(i, 0, 1904) * (w - 20))
        for y in range(wall_top + 2, wall_top + 8 + int(noise2(i, 1, 1904) * 30)):
            if (sx + y) % 3:
                detail.shade(cv, sx, y, 1); detail.shade(cv, sx + 1, y, 1)
    for f in range(1, 4):
        for bx in range(4, w - 4, 42):  # tie plates on the pilasters
            cv.set(bx, wall_top + 2 + f * fh - 3, IRON[3]); cv.set(bx + 1, wall_top + 2 + f * fh - 3, IRON[1])
    detail.stones(cv, 0, foot - 4, w, 4, ST, seed=seed + 51, course=4)
    detail.overhang_shadow(cv, 1, w - 1, wall_top + 2, lambda x: 2, k=1)
    style.close_outline(cv)
    return cv.img, foot


@functools.lru_cache(maxsize=16)
def _works_chimney(h: int, seed: int):
    """A mill or works chimney: a brick shaft on a stone plinth, tapering, lit on its
    west face and dark on its east, banded in stone, a corbelled cap black with soot,
    and smoke leaning away east. (image, foot x, foot y)."""
    w = 44
    top = 30
    cv = Canvas(w, h + top + 1)
    cx = 13
    for y in range(top, top + h):
        t = (y - top) / h
        half = 4 + t * 3
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x - (cx - half)) / (2 * half)
            c = BRICK[4] if u < 0.22 else BRICK[3] if u < 0.55 else BRICK[2] if u < 0.8 else BRICK[1]
            if y % 3 == 2 and (x + (y // 3) * 3) % 6 != 0:
                c = BRICK[2] if u < 0.55 else BRICK[0]
            if (y - top) % 30 == 14:
                c = ST[4] if u < 0.4 else ST[2]
            if y < top + 12 and (x + y) % 3:
                c = IRON[1] if u > 0.4 else BRICK[1]
            cv.set(x, y, c)
    for y in range(top - 4, top):
        for x in range(cx - 6, cx + 7):
            cv.set(x, y, IRON[3] if y == top - 4 else IRON[1] if x < cx else IRON[0])
    for y in range(top + h - 9, top + h):
        for x in range(cx - 8, cx + 9):
            c = ST[3] if x < cx - 3 else ST[2] if x < cx + 5 else ST[1]
            if y == top + h - 9:
                c = ST[4]
            cv.set(x, y, c)
    puffs = [(cx + 2, top - 8, 4.5), (cx + 9, top - 13, 5.5), (cx + 17, top - 18, 6.2), (cx + 25, top - 21, 5.0)]
    for i, (px, py, r) in enumerate(puffs):
        ramp = ['#3A3A42', '#55555E', '#73737A', '#93918F'] if i < 2 else ['#55555E', '#73737A', '#93918F', '#B4B0A8']
        for (x, y) in disc(px, py, r + noise2(seed, i, 1861)):
            k = (x - px) + (y - py)
            cv.set(x, y, ramp[3] if k < -r * 0.6 else ramp[2] if k < 0.5 else ramp[1])
    style.close_outline(cv)
    return cv.img, cx, top + h - 1


@functools.lru_cache(maxsize=2)
def _rail_portal():
    """The main line's tunnel portal, in brick: a parapet with a stone coping, a stone
    string course, brick pilasters lit on the west, a ring of stone voussoirs with a
    keystone round the arch, a date stone, soot from the engines blackening the brick
    over the arch, and the dark of the tunnel with the rails running into it.
    (image, arch centre x, foot row)."""
    w, h = 66, 56
    cv = Canvas(w, h)
    cx, half = w // 2, 13
    spring = h - 24
    _mixed_bricks(cv, 0, 4, w, h - 4, BRICK, seed=71)
    for y in range(h - 9, h - 3):  # a plinth course of blue engineering brick
        for x in range(w):
            cv.set(x, y, BLUE_BRICK[3] if (y - h) % 3 == 0 else BLUE_BRICK[2] if (x + (y // 3) * 3) % 6 else BLUE_BRICK[0])
    for y in range(0, 4):
        for x in range(w):
            cv.set(x, y, (ST[4], ST[3], ST[2], ST[1])[y])
    for x in range(w):
        cv.set(x, 9, ST[4]); cv.set(x, 10, ST[2])
    for (px, lit) in ((0, True), (w - 7, False)):
        for y in range(4, h):
            for x in range(px, px + 7):
                c = BRICK[4] if (lit and x < px + 2) else BRICK[3] if x < px + 5 else BRICK[1]
                if y % 3 == 2:
                    c = BRICK[1] if x < px + 5 else BRICK[0]
                cv.set(x, y, c)
        cv.hline(px, 4, 7, ST[4]); cv.hline(px, 5, 7, ST[2])
    for y in range(11, spring):
        for x in range(cx - half - 6, cx + half + 7):
            k = abs(x - cx) / (half + 6) + (spring - y) / (spring - 11) * 0.8
            if (k < 0.95 and (x + y) % 2 == 0) or k < 0.55:
                detail.shade(cv, x, y, 1)
    for y in range(spring - half - 4, h):
        for x in range(cx - half - 4, cx + half + 5):
            dx, dy = x + 0.5 - cx, y + 0.5 - spring
            r = math.hypot(dx, dy) if dy < 0 else abs(dx)
            if half <= r < half + 4:
                a = math.atan2(dy, dx)
                stone = int((a + math.pi) / math.pi * 11)
                c = ST[4] if dx < 0 and r < half + 1.5 else ST[3] if stone % 2 else ST[2]
                if dy >= 0:
                    c = (ST[3] if dx < 0 else ST[1]) if (y - spring) % 5 != 4 else (ST[1] if dx < 0 else ST[0])
                elif stone % 4 == 1:
                    c = RED_BRICK[3] if dx < 0 else RED_BRICK[2]   # the ring banded in red brick and stone
                cv.set(x, y, c)
            elif r < half:
                # the tunnel's brick lining going into the dark, lit only on its west side
                if r > half - 5:
                    lining = (BLUE_BRICK[1], BLUE_BRICK[0]) if dx < 0 else ('#1E1C26', '#14131A')
                    c = lining[0] if (int(y) // 2 + int(r)) % 3 else lining[1]
                    if dx < 0 and r > half - 2:
                        c = BLUE_BRICK[2]
                else:
                    c = '#14131A' if r < half - 7 else '#1A1922'
                cv.set(x, y, c)
    for y in range(spring - half - 5, spring - half + 1):
        for x in range(cx - 2, cx + 3):
            cv.set(x, y, ST[4] if x < cx + 1 else ST[2])
    for y in range(13, 18):
        for x in range(cx - 7, cx + 8):
            c = ST[3] if y == 13 else ST[2]
            if y in (15, 16) and x % 2 and abs(x - cx) < 5:
                c = ST[0]
            cv.set(x, y, c)
    for ry in (h - 15, h - 8):
        for x in range(cx - half + 1, cx + half - 1):
            cv.set(x, ry, IRON[3] if abs(x - cx) > half - 5 else IRON[2])
    for x in range(w):  # moss along the coping's foot and weeds at the face's
        if noise2(x // 2, 0, 1903) > 0.55:
            cv.set(x, 4, LICHEN[1]); cv.set(x, 5, '#3A4632')
        if (x < cx - half - 5 or x > cx + half + 5) and noise2(x // 2, 1, 1903) > 0.5:
            cv.set(x, h - 2, '#46583F'); cv.set(x, h - 3, '#5C6E4C' if x % 2 else '#46583F')
            if noise2(x, 2, 1903) > 0.6:
                cv.set(x, h - 4, '#8E9C6E')
    for y in range(14, h - 4):  # ivy climbing its west pilaster
        for x in range(0, 6 - abs((y % 11) - 5) // 2):
            if noise2(x // 2, y // 2, 1905) > 0.35:
                cv.set(x, y, ('#22352C', '#3A5939', '#557A45', '#749A50')[int(noise2(x, y // 2, 1906) * 3.99)])
    for y in range(5, 9):  # a cast-iron plate with the company's number
        for x in range(w - 22, w - 10):
            cv.set(x, y, IRON[1] if y in (5, 8) or x in (w - 22, w - 11) else ('#C8B48A' if (x + y) % 3 == 0 else IRON[2]))
    for (lx, ly) in ((10, 24), (w - 16, 30)):  # streaks of rust and lime from the coping
        for y in range(ly, ly + 10):
            cv.set(lx, y, '#8A5432' if y % 3 else '#C6BDAE')
    style.close_outline(cv)
    return cv.img, cx, h - 1


@functools.lru_cache(maxsize=16)
def _heap(w: int, h: int, seed: int, kind: str):
    """A heap of coal (black lumps with blue-lit edges) or slag (grey-brown clinker),
    lit from the upper left, its lumps in clusters. (image, foot x, foot y)."""
    ramp = ['#14131A', '#1E1E28', '#2C2C38', '#45465A', '#6A6E86'] if kind == 'coal' else \
        ['#2A2420', '#3E3630', '#564C42', '#73675A', '#948775']
    cv = Canvas(w + 4, h + 4)
    cx, cy = w / 2 + 2, h + 1
    for y in range(h + 4):
        for x in range(w + 4):
            dx, dy = (x + 0.5 - cx) / (w / 2), (y + 0.5 - cy) / h
            jag = (noise2(x // 2, y // 2, 1871 + seed) - 0.5) * 0.2
            if dx * dx + dy * dy <= 1 + jag and dy <= 0.02:
                lit = -0.6 * dx - 0.5 * dy
                lump = noise2(x // 2, y // 2, 1872 + seed)
                i = 3 if lit > 0.35 else 2 if lit > 0.0 else 1
                i = min(4, i + 1) if lump > 0.8 else max(0, i - 1) if lump < 0.18 else i
                cv.set(x, y, ramp[i])
    style.close_outline(cv)
    return cv.img, int(cx), h + 1


@functools.lru_cache(maxsize=4)
def _privy(seed: int):
    """A brick privy or coal house in a back yard: a lean-to slate roof falling toward
    us, a plank door with a heart cut in it."""
    w, h = 16, 26
    cv = Canvas(w, h)
    for y in range(0, 8):
        for x in range(w):
            c = SLATE_[3] if y % 3 == 0 else SLATE_[2]
            if (x + (y // 3) * 2) % 5 == 0:
                c = SLATE_[1]
            cv.set(x, y, c)
    cv.hline(0, 8, w, IRON[1])
    detail.bricks(cv, 1, 9, w - 2, h - 9, BROWN if seed % 2 else BRICK, seed=seed, base=2)
    for y in range(11, h):
        for x in range(4, 12):
            cv.set(x, y, WOOD[2] if (x - 4) % 3 else WOOD[1])
    cv.set(7, 14, WOOD[0]); cv.set(8, 14, WOOD[0]); cv.set(7, 15, WOOD[0])
    style.close_outline(cv)
    return cv.img


@functools.lru_cache(maxsize=8)
def _hedge_blob(seed: int, r: int):
    """One mass of a hedge, in the zones' leaf rule (style.leafy) in a sooty green."""
    cv = Canvas(2 * r + 8, int(r * 1.6) + 8)
    style.leafy(cv, cv.w / 2, cv.h / 2, r, r * 0.75, HEDGE, r=2.2, seed=seed, flat_bottom=0.85)
    lit = {_rgb(HEDGE[3]), _rgb(HEDGE[4])}
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.get(x, y)[:3] in lit and noise2(x, y, 1966 + seed) > 0.93:
                cv.set(x, y, '#E8E2D2' if seed % 2 else '#A83A2E')   # hawthorn: May blossom, or haws
                if cv.get(x + 1, y)[3]:
                    cv.set(x + 1, y, '#C8C0B0' if seed % 2 else '#7A2A22')
    return cv.img


@functools.lru_cache(maxsize=1)
def _built():
    """Buildings and things from the town's own set (steampunk_props), finalised once."""
    sp = _sp()
    return {
        'house_a': style.finalize(sp.townhouse(88, 2, sp.SLATE, 'brown', door_x=18, chimney=1, seed=11), name='house_a'),
        'house_b': style.finalize(sp.townhouse(92, 2, sp.TAR, 'brick', door_x=60, chimney=-1, seed=12), name='house_b'),
        'shop_a': style.finalize(sp.townhouse(92, 2, sp.SLATE, 'ashlar', shop=True, chimney=1, seed=14), name='shop_a'),
        'house_c': style.finalize(sp.townhouse(84, 2, sp.SLATE, 'brick', door_x=48, chimney=-1, seed=13), name='house_c'),
        'warehouse': style.finalize(sp.warehouse(), name='warehouse'),
        'engine_house': style.finalize(sp.townhouse(80, 2, sp.SLATE, 'ashlar', door_x=33, chimney=1, seed=15), name='engine_house'),
        'lamp': style.finalize(sp.gas_lamp(), name='lamp'),
        'boat': style.finalize(sp.narrowboat(), name='boat'),
        'crane': style.finalize(sp.canal_crane(), name='crane'),
        'cart': style.finalize(sp.coal_cart(), name='cart'),
        'trunk': style.finalize(sp.steamer_trunk(), name='trunk'),
        'bench': style.finalize(sp.iron_bench(), name='bench'),
    }


@functools.lru_cache(maxsize=1)
def _steam_things():
    """Everything that stands round the town, in region px: (foot y, kind, data), back to
    front."""
    out = []
    b = _built()

    def put(key, x, foot):
        sp_ = b[key]
        out.append((foot, 'sprite', (key, x + sp_.ox, foot - sp_.h + 2)))
    # behind the yard wall: terraces in segments with ginnels between, their backs or
    # their fronts, slate or tarred iron; a mill stands in the second row
    mill_x = (336, 336 + 186)
    for (ry, back) in ROWS:
        x = -320 - 20
        k = 0
        while x < 640 + 20:
            if not back and ry == ROWS[1][0] and mill_x[0] - 30 < x < mill_x[1]:
                x = mill_x[1] + 10
                continue
            n = 2 + int(noise2(k, ry, 1881) * 4)
            roof = 1 if noise2(k, ry, 1883) > 0.72 else 0
            out.append((ry, 'terrace', (n, (ry * 7 + k * 13) % 997, back, roof, x)))
            x += n * HOUSE + 2 + (8 if noise2(k, ry, 1882) > 0.5 else 14)
            k += 1
    out.append((ROWS[1][0], 'mill', (mill_x[0],)))
    for (lx, foot) in ((-250, -226), (-80, -226), (90, -226), (270, -226), (-170, 236), (-40, 236), (360, 302), (480, 302),
                       (590, 302), (-30, CY0 - 30), (-170, CY0 - 30), (380, CY0 - 30), (-90, TOW_S[1] - 4), (360, TOW_S[1] - 4)):
        put('lamp', lx, foot)
    for (cx, foot, h, seed) in ((-250, -250, 150, 1), (430, -238, 176, 2), (12, -398, 160, 3), (-90, 402, 132, 4),
                                (ENGINE_X + 92, TUBE[2] + 12, 150, 5)):
        out.append((foot, 'chimney', (cx, h, seed)))
    put('house_a', -104, 230)
    put('house_c', -196, 230)
    put('house_b', -296, 230)
    put('warehouse', -150, 402)
    put('cart', -40, 398)
    put('trunk', -62, 398)
    put('shop_a', 336, 296)
    put('house_a', 438, 296)
    put('house_c', 536, 296)
    put('warehouse', 386, 474)
    put('cart', 504, 470)
    put('warehouse', -132, TOW_N[0] - 1)
    put('warehouse', -282, TOW_N[0] - 1)
    put('warehouse', 336, TOW_N[0] - 1)
    put('warehouse', 452, BASIN[2] - 36)
    put('crane', 520, BASIN[2] - 4)
    put('boat', 420, CY1 - 6)
    put('bench', -60, TOW_S[1] - 2)
    put('engine_house', ENGINE_X, TUBE[2] + 14)
    for (cx, foot, w, h, seed, kind) in ((-70, 32, 34, 14, 1, 'coal'), (406, 42, 40, 16, 2, 'coal'),
                                         (-250, 500, 64, 28, 3, 'slag'), (-90, 1040, 56, 22, 4, 'slag'),
                                         (-150, -6, 30, 12, 6, 'coal'), (210, -4, 26, 11, 7, 'coal'),
                                         (-190, 470, 40, 16, 8, 'slag'), (560, 40, 30, 12, 9, 'coal')):
        out.append((foot, 'heap', (cx, w, h, seed, kind)))
    # bushes in the rough grass: on the hills over the tunnels, by the fences and walls
    for (bx, foot, sz, seed) in ((-196, 62, 8, 1), (-168, 34, 6, 2), (-262, 92, 9, 3), (-300, 40, 7, 4), (524, 52, 7, 5),
                                 (566, 24, 8, 6), (612, 84, 9, 7), (-34, 474, 7, 8), (-128, 566, 8, 9), (-286, 446, 9, 10),
                                 (352, 524, 8, 11), (452, 566, 7, 12), (604, 434, 9, 13), (-44, 904, 8, 14), (-164, 966, 7, 15),
                                 (-286, 1124, 9, 16), (344, 1104, 7, 17), (602, 1084, 8, 18), (-300, 700, 7, 19), (626, 650, 7, 20)):
        out.append((foot, 'bush', (bx, sz, seed)))
    out.append((STEAM_RAIL[1] - 1, 'portal', (PORTAL_W,)))
    out.append((STEAM_RAIL[1] - 1, 'portal', (PORTAL_E,)))
    for x in range(-330, 650, 7):  # hedges along the lane and between the fields
        wob = int(float(vnoise(np.array(x), np.array(0), 80, 1841)) * 6)
        out.append((LANE[1] + wob + 10, 'hedge', (x, (x // 7) % 5 + 1, 6 + (x * 7) % 3)))
        out.append((LANE[0] + wob - 2, 'hedge', (x, (x // 7) % 5 + 3, 5 + (x * 5) % 3)))
    for gy in range(LANE[1] + 20, H * 3 + 10, 7):
        _kind, fx, _fy = _field_kind(np.arange(-330, 650), np.full(980, gy))
        for i in np.nonzero(np.diff(fx) != 0)[0]:
            out.append((gy, 'hedge', (int(i) - 330, (gy // 7) % 5 + 2, 5 + (gy * 3) % 3)))
    for (tx, ty, sz, seed) in ((-240, LANE[1] + 12, 15, 1), (90, LANE[1] + 13, 13, 2), (420, LANE[1] + 11, 16, 3),
                               (250, LANE[0] - 2, 12, 4), (-60, LANE[0] - 3, 14, 5)):
        out.append((ty, 'tree', (tx, sz, seed)))
    return sorted(out, key=lambda t: (t[0], t[1]))


class _RegionCv:
    """A cell's canvas addressed in region px, drawing only inside the cell (each cell
    draws everything that reaches it, so a thing across a cell edge is drawn whole)."""

    def __init__(self, cv: Canvas, x0: int, y0: int):
        self.cv, self.x0, self.y0 = cv, x0, y0
        self.w, self.h = 10 ** 6, 10 ** 6

    def ok(self, x, y):
        return S <= x - self.x0 < S + W and S <= y - self.y0 < S + H

    def set(self, x, y, c, alpha=None):
        if self.ok(x, y):
            self.cv.set(x - self.x0, y - self.y0, c, alpha)

    def get(self, x, y):
        return self.cv.get(x - self.x0, y - self.y0)

    def hline(self, x, y, w, c):
        for i in range(w):
            self.set(x + i, y, c)

    def vline(self, x, y, h, c):
        for i in range(h):
            self.set(x, y + i, c)

    def rect(self, x, y, w, h, c, alpha=None):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c, alpha)

    def darken(self, x, y):
        if self.ok(x, y):
            style.darken(self.cv, x - self.x0, y - self.y0)

    def stamp(self, img, x, y):
        """Composite an image at region (x, y), cut to the cell."""
        cx0, cy0 = self.x0 + S, self.y0 + S
        a0, b0 = max(x, cx0), max(y, cy0)
        a1, b1 = min(x + img.width, cx0 + W), min(y + img.height, cy0 + H)
        if a1 > a0 and b1 > b0:
            self.cv.img.alpha_composite(img.crop((a0 - x, b0 - y, a1 - x, b1 - y)), (a0 - self.x0, b0 - self.y0))

    def shadow(self, x, y, w, h, reach=3):
        """A building's hard shadow on the ground beside it, down and to the right."""
        for d in range(1, reach + 1):
            for yy in range(y + d, y + h + d):
                self.darken(x + w - 1 + d, yy)
            for xx in range(x + d, x + w + d):
                self.darken(xx, y + h - 1 + d)


def _railings(rc, x, foot, h=7):
    """One column of iron railings on a wall top: square bars two pixels wide every four,
    lit on the west, with spear tips, a top and a bottom rail."""
    if x % 4 in (0, 1):
        for y in range(foot - h, foot):
            rc.set(x, y, (IRON[4] if y == foot - h else IRON[3]) if x % 4 == 0 else IRON[1])
    rc.set(x, foot - h + 1, IRON[2]); rc.set(x, foot - 2, IRON[2])


def _pole(rc, x, foot):
    """A telegraph pole: a creosoted post with two cross-arms and white insulators."""
    for y in range(foot - 34, foot):
        rc.set(x, y, WOOD[2]); rc.set(x + 1, y, WOOD[1])
    for (ay, half) in ((foot - 32, 6), (foot - 27, 5)):
        rc.hline(x - half, ay, 2 * half + 2, WOOD[3]); rc.hline(x - half, ay + 1, 2 * half + 2, WOOD[1])
        for ix in (x - half, x - half // 2, x + half // 2 + 1, x + half + 1):
            rc.set(ix, ay - 1, '#E8E2D2'); rc.set(ix, ay - 2, '#F6F2E8')
    for d in range(1, 4):
        rc.darken(x + 1 + d, foot - 1 + (d > 2))


def _wire(rc, xa, xb, ya, sag=4.0):
    n = abs(xb - xa)
    for t in range(n + 1):
        rc.set(xa + (xb - xa) * t // max(1, n), ya + int(round(sag * math.sin(math.pi * t / max(1, n)))), '#2A2630')


def _bollard(rc, x, y):
    """An iron mooring bollard on a coping: a squat post lit on the west, a cap."""
    for yy in range(y - 4, y + 1):
        rc.set(x, yy, IRON[4] if yy < y - 2 else IRON[3]); rc.set(x + 1, yy, IRON[2]); rc.set(x + 2, yy, IRON[1])
    rc.hline(x - 1, y - 5, 5, IRON[3]); rc.set(x + 3, y - 5, IRON[1])
    rc.darken(x + 3, y); rc.darken(x + 3, y - 1)


def _fence(rc, xa, xb, y, seed=0):
    """A boarded timber fence along y: weathered boards with lit tops, a tarred patch."""
    for x in range(xa, xb):
        tall = 10 + (1 if noise2(x // 3, y, 1911 + seed) > 0.7 else 0)
        for k in range(tall):
            c = WOOD[2] if (x % 3) else WOOD[1]
            if k == tall - 1:
                c = WOOD[4] if x % 3 else WOOD[2]
            if noise2(x // 3, k // 4, 1912 + seed) > 0.93:
                c = '#3A3A42'
            rc.set(x, y - k, c)
        rc.set(x, y - 4, WOOD[1])
        rc.darken(x + 1, y + 1)


LOCK_N, LOCK_S = CY0 + 12, CY1 - 12   # the chamber's water between its walls


def _gates_and_beams(rc, gx, upper):
    """A pair of mitre gates across the lock at x, meeting in a V that points upstream
    (east): heavy timber leaves with a walkway rail along their tops, the water a step
    lower below them (spouting through their seams on the lower side), and a balance
    beam on each coping, dark timber with its end painted white."""
    span = LOCK_S - LOCK_N
    for t in range(span):
        y = LOCK_N + t
        x = gx - int(abs(t - span / 2) * 0.34)
        for d in range(5):
            rc.set(x + d, y, WOOD[4] if d == 0 else WOOD[3] if d == 1 else WOOD[2] if d < 4 else WOOD[0])
        if t % 4 == 0:
            rc.set(x + 2, y, IRON[2])  # the iron straps
        rc.set(x - 1, y, '#3E6A5E' if upper else '#14281F')
        if (t + gx) % 5 in (0, 1):  # water spouting through on the lower side
            rc.set(x - 2, y, '#EEF5F8'); rc.set(x - 3, y, '#86AAD0')
    for (ya_, yb_) in ((LOCK_N - 3, CY0 - 16), (LOCK_S + 1, CY1 + 12)):
        # the beam runs from the leaf's heel out over the coping onto the towpath
        n = 26
        for t in range(n):
            x, y = gx + 2 + t, ya_ + (yb_ - ya_) * t // n
            tip = t > n - 6
            for k in range(3):
                c = (WOOD[3], WOOD[2], WOOD[0])[k] if not tip else ('#F2F0EA', '#C8C4BA', '#6A6660')[k]
                rc.set(x, y + k, c)
            rc.darken(x + 1, y + 3)
        for y in range(ya_ - 2, ya_ + 4):
            rc.set(gx + 2, y, IRON[3]); rc.set(gx + 3, y, IRON[1])


def steam_cell(col: int, row: int, zone_at) -> Canvas:
    """One cell of the land round Cogsworth (see the notes above SOOT_G)."""
    import worlds
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0, X, Y = _sgrid(col, row)
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    ground, tone, m = _steam_ground(X, Y)
    _paint(cv, ground, inside)
    rc = _RegionCv(cv, x0, y0)
    xa, xb, ya, yb = col * W, (col + 1) * W, row * H, (row + 1) * H
    # tufts on the open grass, on the zones' six-pixel grid, in clusters
    for gy in range((ya // 6) * 6 - 6, yb + 6, 6):
        for gx in range((xa // 6) * 6 - 6, xb + 6, 6):
            tx, ty = gx + int(noise2(gx, gy, 4) * 6), gy + int(noise2(gx, gy, 5) * 6)
            if not (xa <= tx < xb and ya <= ty < yb - 3):
                continue
            t = tone[ty - y0, tx - x0]
            if t < 0 or tone[ty + 2 - y0, tx - x0] < 0:
                continue
            cluster = float(vnoise(np.array(tx), np.array(ty), 25, 63)) > 0.57
            if noise2(gx, gy, 3) < (0.36 if cluster else 0.16) + 0.4 * float(_rich(np.array(tx), np.array(ty))):
                detail.grass_tuft(rc, tx, ty + 2, int(noise2(gx, gy, 8) * 6), SOOT_G, int(t))
    # out from the town the grass grows rougher: a second sowing of tufts between the first
    for gy in range((ya // 6) * 6 - 3, yb + 6, 6):
        for gx in range((xa // 6) * 6 - 3, xb + 6, 6):
            tx, ty = gx + int(noise2(gx, gy, 14) * 6), gy + int(noise2(gx, gy, 15) * 6)
            if not (xa <= tx < xb and ya <= ty < yb - 3):
                continue
            t = tone[ty - y0, tx - x0]
            if t < 0 or tone[ty + 2 - y0, tx - x0] < 0:
                continue
            if noise2(gx, gy, 13) < 0.55 * float(_rich(np.array(tx), np.array(ty))) - 0.25:
                detail.grass_tuft(rc, tx, ty + 2, int(noise2(gx, gy, 18) * 6), SOOT_G, int(t))
    # the platform carried on to its ramp, in the zone's slabs, with its painted edge
    for sgn, ex in ((-1, -1), (1, W)):
        lo, hi = min(ex, ex + sgn * 26), max(ex, ex + sgn * 26)
        if hi < xa or lo >= xb or ya > 136 or yb < 100:
            continue
        # (the slabs are laid a few columns into the zone too, so no lawn edge is drawn at the seam)
        plat = {(x, y) for x in range(lo - 3 * (sgn > 0), hi + 1 + 3 * (sgn < 0)) for y in range(100, 134)}
        worlds.paint_paving(rc, plat, seed=7, street=7)
        for x in range(lo, hi + 1):
            d = abs(x - ex)
            rc.set(x, 100, '#E8C860' if d < 20 else ST[3]); rc.set(x, 101, '#B8962E' if d < 20 else ST[2])
            rc.set(x, 134, ST[1]); rc.set(x, 135, ST[2])
            if d >= 20:
                for y in range(102, 134):
                    if y - 102 < (d - 19) * 6:
                        rc.set(x, y, SL[1] if (x + y) % 4 else SL[0])
    # railings along the cutting's walls; telegraph poles and their wires on its north side
    for (a, b_) in ((PORTAL_W + 34, -16), (W + 16, PORTAL_E - 34)):
        for x in range(max(a, xa), min(b_, xb)):
            hw = int(_cut_h(np.array(x)))
            if hw >= 6:
                _railings(rc, x, STEAM_RAIL[0] - hw - 2)
            if abs(x - (-1 if b_ < 0 else W)) > 26:
                _railings(rc, x, STEAM_RAIL[1] + 1)
    poles = [x for x in range(-296, 640, 52) if (x < -40 or x > W + 40) and abs(x - PORTAL_W) > 40 and abs(x - PORTAL_E) > 40]
    feet = {px: STEAM_RAIL[0] - int(_cut_h(np.array(px))) - 6 for px in poles}
    for i, px in enumerate(poles):
        if i + 1 < len(poles) and poles[i + 1] - px < 60:
            for (k, ay) in enumerate((32, 27)):
                _wire(rc, px, poles[i + 1], min(feet[px], feet[poles[i + 1]]) - ay - 1, sag=3 + k)
    for px in poles:
        _pole(rc, px, feet[px])
    # the yard wall along the back of the town: brick in region px, piers lit on the
    # west, a coping, bills pasted on it, some torn; its shadow and weeds at its foot
    if ya < -30 and yb > -58:
        for y in range(-56, -34):
            for x in range(xa, xb):
                if y < -54:
                    rc.set(x, y, ST[4] if y == -56 else ST[2])
                    continue
                c = _bricks_np(np.array(x), np.array(y), BROWN, seed=9, base=2)
                rc.set(x, y, tuple(int(v) for v in c) + (255,))
                p = x % 48
                if p < 4:
                    rc.set(x, y, BROWN[4] if p == 0 else BROWN[3] if p < 3 else BROWN[1])
                if y >= -36:
                    rc.darken(x, y)
        for i in range(-6, 14):
            bx = i * 77 + int(noise2(i, 0, 1891) * 30)
            if noise2(i, 1, 1891) < 0.45:
                continue
            cols = (('#C8B48A', '#9C3A2E'), ('#D8D0B8', '#2C3E4C'), ('#B89A5A', '#3A2A22'))[i % 3]
            for y in range(-51, -40):
                for x in range(bx, bx + 12):
                    if (x - bx) + (y + 51) > 17 and noise2(x // 2, y // 2, 1892) > 0.4:
                        continue  # (torn, in flakes of two or more)
                    rc.set(x, y, cols[0] if (y + 51) % 4 or x in (bx, bx + 11) else cols[1])
        for x in range(xa, xb):
            rc.darken(x, -34)
            if x % 2:
                rc.darken(x + 1, -33)
            if noise2(x // 2, 7, 1893) > 0.72:
                detail.grass_tuft(rc, x, -32, int(noise2(x, 1, 1894) * 6), SOOT_G, 2)
    # the back yards: walls between them, privies, washing hung across some
    for (ry, back) in ROWS:
        if not back or ry > yb + 40 or ry + 40 < ya:
            continue
        yard_to = -56 if ry == -84 else ry + 42
        for i, x in enumerate(range(-320 - 20, 640 + 20, HOUSE)):
            for y in range(ry - 2, yard_to):
                rc.set(x, y, BROWN[3] if y > ry - 1 else BROWN[4]); rc.set(x + 1, y, BROWN[2]); rc.set(x + 2, y, BROWN[1])
                rc.darken(x + 3, y)
            if noise2(i, ry, 1895) > 0.4:
                rc.stamp(_privy(i % 3), x + 5, yard_to - 26)
            if noise2(i, ry, 1896) > 0.55:
                for t in range(26):
                    yy = ry + 6 + int(math.sin(math.pi * t / 26) * 2)
                    rc.set(x + 4 + t, yy, '#D8D0B8')
                    if 2 < t < 24 and (t // 5) % 2 == 0:
                        cl = ['#E8E2D2', '#8E5040', '#5A7690', '#D8B87C'][(i + t // 5) % 4]
                        for k in range(1, 5):
                            rc.set(x + 4 + t, yy + k, cl if k < 4 or t % 5 else '#A8A090')
    for (a, b_, fy) in ((-300, -18, 412), (W + 18, 620, 488)):  # timber fences
        if a < xb and b_ > xa:
            _fence(rc, a, b_, fy)
    for x in list(range(-300, -10, 46)) + list(range(W + 20, BASIN[0] - 10, 46)) + list(range(BASIN[0] + 10, BASIN[1], 40)):
        _bollard(rc, x, CY0 - 3 if x < BASIN[0] else BASIN[2] - 4)
        if not (BASIN[0] <= x < BASIN[1]):
            _bollard(rc, x + 20, CY1 + 6)
    # the lock: gates at each end of its chamber, the chamber's copings proud of the paths
    if xa < LOCK[1] + 40 and xb > LOCK[0] - 40:
        _gates_and_beams(rc, LOCK[0] + 8, upper=False)
        _gates_and_beams(rc, LOCK[1] - 2, upper=True)
    # the road over the canal west: a deck of setts between brick parapets
    if xa < BRIDGE[1] + 8 and xb > BRIDGE[0]:
        for y in range(TOW_N[0] - 4, TOW_S[1] + 4):
            for x in range(BRIDGE[0], BRIDGE[1]):
                k = x - BRIDGE[0]
                last = BRIDGE[1] - BRIDGE[0] - 5
                if k < 5 or k >= last:
                    j = k if k < 5 else k - last
                    c = (ST[4], ST[3], BRICK[3], BRICK[2], BRICK[1])[j]  # coping, then the brick
                    if j >= 2 and y % 3 == 2:
                        c = BRICK[1] if j < 4 else BRICK[0]
                    rc.set(x, y, c)
            if CY0 <= y < CY1:
                for d in range(1, 6):  # the span's shadow on the water, deeper to the east
                    rc.darken(BRIDGE[1] - 1 + d, y)
                rc.darken(BRIDGE[0] - 1, y)
        for y in (TOW_N[0] - 5, TOW_S[1] + 4):
            rc.hline(BRIDGE[0], y, BRIDGE[1] - BRIDGE[0], ST[4])
    # the tube on east to its pumping house, on the zone's trestles
    if xb > W and xa < ENGINE_X:
        for x in range(max(W, xa), min(ENGINE_X + 14, xb)):
            for y in range(TUBE[0], TUBE[1]):
                k = (y - TUBE[0]) / 16
                c = BRASS[4] if k < 0.2 else BRASS[3] if k < 0.5 else BRASS[2] if k < 0.85 else BRASS[1]
                if (x - 38 - 196) % 10 == 0:
                    c = IRON[1]
                rc.set(x, y, c)
            if x % 24 == 8:
                for y in range(TUBE[1], TUBE[2]):
                    rc.set(x, y, IRON[3]); rc.set(x + 1, y, IRON[1])
            if x % 2:
                rc.darken(x + 1, TUBE[2])
            rc.set(x, TUBE[2], '#2B3B2E')
    # the feeder's culvert: a brick face with an arched mouth and its iron grille
    fcx = (FEEDER[0] + FEEDER[1]) // 2
    if xa < fcx + 30 and xb > fcx - 30:
        top = FEEDER[2] - 22
        for y in range(top, FEEDER[2]):
            for x in range(fcx - 26, fcx + 27):
                c = tuple(int(v) for v in _bricks_np(np.array(x), np.array(y), BRICK, seed=21, base=2)) + (255,)
                if y < top + 3:
                    c = (ST[4], ST[3], ST[2])[y - top]
                rc.set(x, y, c)
        for y in range(FEEDER[2] - 13, FEEDER[2]):
            for x in range(fcx - 9, fcx + 10):
                dx, dy = x + 0.5 - fcx, y + 0.5 - (FEEDER[2] - 5)
                r = math.hypot(dx, dy) if dy < 0 else abs(dx)
                if r < 7:
                    rc.set(x, y, '#14131A' if (x - fcx) % 3 else IRON[3])
                elif r < 9.5:
                    rc.set(x, y, ST[4] if dx < 0 else ST[2])
    # what stands, back to front
    b = _built()
    for (foot, kind, data) in _steam_things():
        if kind == 'terrace':
            n, seed, back, roof, tx = data
            img, f = _terrace_row(n, seed, back, roof)
            if tx + img.width < xa or tx > xb or foot - f > yb or foot < ya:
                continue
            rc.stamp(img, tx, foot - f)
            rc.shadow(tx, foot - f + 20, img.width, f - 20)
        elif kind == 'mill':
            (mx,) = data
            img, f = _mill()
            rc.stamp(img, mx, foot - f)
            rc.shadow(mx, foot - f + 10, img.width, f - 10)
        elif kind == 'sprite':
            key, sx, sy = data
            sp_ = b[key]
            if sx > xb or sx + sp_.w < xa or sy > yb or sy + sp_.h < ya:
                continue
            rc.stamp(sp_.img, sx, sy)
            if key not in ('lamp', 'boat', 'bench', 'trunk', 'cart'):
                rc.shadow(sx, sy + sp_.h // 3, sp_.w, sp_.h - sp_.h // 3 - 1)
        elif kind == 'chimney':
            cx, h, seed = data
            img, fx, fy = _works_chimney(h, seed)
            rc.stamp(img, cx - fx, foot - fy)
        elif kind == 'heap':
            cx, w, h, seed, k = data
            img, fx, fy = _heap(w, h, seed, k)
            rc.stamp(img, cx - fx, foot - fy)
            rc.shadow(cx - fx + 4, foot - h // 2, img.width - 8, h // 2, reach=2)
        elif kind == 'portal':
            (px,) = data
            img, fx, fy = _rail_portal()
            rc.stamp(img, px - fx, foot - fy)
        elif kind == 'hedge':
            hx, seed, r = data
            img = _hedge_blob(seed, r)
            rc.stamp(img, hx - img.width // 2, foot - img.height + 3)
        elif kind == 'bush':
            bx, sz, seed = data
            img, ax, ay = _edge_tree('bush', sz, seed, 3)
            rc.stamp(img, bx - ax, foot - ay)
            rc.shadow(bx - sz // 2, foot - 3, sz, 3, reach=2)
        elif kind == 'tree':
            tx, sz, seed = data
            img, ax, ay = _edge_tree('broad', sz, seed, 3)
            rc.stamp(img, tx - ax, foot - ay)
    return cv


CELL_PAINTERS = {'valley': None, 'west': west_cell, 'isles': isles_cell, 'moon': moon_cell, 'steam': steam_cell}


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
