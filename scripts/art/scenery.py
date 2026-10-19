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

import garden_props
import style
from materials import MATERIALS
from pixel import Canvas, noise2

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


def ridged(X, Y, scale: float, seed: int):
    return 1 - np.abs(2 * vnoise(X, Y, scale, seed) - 1)


# ---- what the land is, per region -------------------------------------------------
def _lerp_points(x, pts):
    """Piecewise-linear through (x, y) control points, flat past the ends."""
    xs, ys = zip(*pts)
    return np.interp(x, xs, ys)


# The valley's coast: where the sea begins, by region x. It meets the harbour's sea at
# the harbour's west edge (y 1721) and the headland's at its east edge (y 1531); under
# the two zones the sea starts at their bottom edge.
VALLEY_COAST = [(-960, 1690), (-560, 1700), (-320, 1716), (0, 1721), (640, 1531), (760, 1490),
                (1000, 1420), (1280, 1400)]
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
    away = np.clip(np.minimum(np.abs(X - 0), np.abs(X - 640)) / 80, 0, 1)
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
    n = vnoise(X, Y, 9, 951)
    return _pick(FOREST_FLOOR, np.where(n > 0.62, 2, np.where(n > 0.3, 1, 0)))


def _sea_rgb(X, Y, coast):
    """Open sea in the harbour's water: deep with long swells, shallower by the shore."""
    depth = Y - coast
    n = vnoise(X, Y, 110, 961) + 0.08 * (vnoise(X, Y, 9, 965) - 0.5)
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


@functools.lru_cache(maxsize=512)
def _crown_img(rx: int, k: int) -> Image.Image:
    ry = rx * 0.72
    blob = Canvas(int(rx * 2) + 14, int(ry * 2) + 14)
    style.leafy(blob, blob.w / 2, blob.h / 2, rx, ry, CANOPY, r=3.8, seed=k + 3)
    return blob.img


def _crown(cv: Canvas, cx: float, cy: float, rx: float, k: int):
    """A crown of the canopy: one of a few dozen drawn crowns (by size and a variant),
    so the forest stays varied without drawing every crown afresh."""
    im = _crown_img(int(rx), k % 9)
    _stamp(cv, im, int(cx - im.width / 2), int(cy - im.height / 2))


def _trees(region: str, col: int, row: int, kind_at):
    """Crowns and pines on a jittered grid over the region, every one that reaches this
    canvas, back to front. `kind_at(x, y)` says what grows at a region point."""
    x0, y0 = col * W - S - 60, row * H - S - 60
    x1, y1 = (col + 1) * W + S + 60, (row + 1) * H + S + 60
    J, I = np.meshgrid(np.arange(math.floor(y0 / 30), math.ceil(y1 / 30) + 1),
                       np.arange(math.floor(x0 / 40), math.ceil(x1 / 40) + 1), indexing='ij')
    GX = I * 40 + (_hash(I, J, 552) - 0.5) * 28
    GY = J * 30 + (_hash(I, J, 553) - 0.5) * 22
    kinds = kind_at(GX, GY)
    out = []
    for (j, i), what in np.ndenumerate(kinds):
        gx, gy, ii, jj = float(GX[j, i]), float(GY[j, i]), int(I[j, i]), int(J[j, i])
        if what == 'crown':
            out.append((gy, gx, 'crown', 22 + noise2(ii, jj, 554) * 12, ii * 7919 + jj))
        elif what == 'pine' and noise2(ii, jj, 555) < 0.75:
            out.append((gy, gx, 'pine', 0, ii * 7919 + jj))
    return sorted(out)


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


def valley_cell(col: int, row: int, zone_at) -> Canvas:
    """One cell of scenery in the valley. `zone_at(col, row)` names the zone there, if any.

    The high country is a range of mountains drawn like the forest's crowns, back to
    front in the same three-quarter view as everything else, over snowfields and
    alpine turf; below the treeline, pines; in the valley's own country, old forest;
    then the shore and the open sea."""
    CW, CH = W + 2 * S, H + 2 * S
    cv = Canvas(CW, CH)
    x0, y0 = col * W - S, row * H - S
    X, Y = np.meshgrid(np.arange(x0, x0 + CW), np.arange(y0, y0 + CH))
    alt, sea, river, coast, rc = valley_fields(X, Y)
    snowy = alt + 0.4 * (vnoise(X, Y, 60, 993) - 0.5) > 0.9
    n = vnoise(X, Y, 34, 991)
    fine = vnoise(X, Y, 6, 995)
    snowfield = _pick(SN, np.where(n > 0.45, 3, 2))
    snowfield = np.where(((fine > 0.88) & (n < 0.45))[..., None], _pick(SN, np.full(X.shape, 1)), snowfield)
    turf = _pick(ALPINE, np.where(n > 0.62, 3, 2))
    turf = np.where((vnoise(X, Y, 3.5, 992) > 0.82)[..., None], _pick(ST, np.where(fine > 0.5, 3, 2)), turf)
    ground = np.where(snowy[..., None], snowfield, turf)
    ground = np.where((alt <= 0.12)[..., None], _forest_floor_rgb(X, Y), ground)
    ground = np.where(sea[..., None], _sea_rgb(X, Y, coast), ground)
    ground = np.where((river & ~sea)[..., None], _river_rgb(X, Y, rc), ground)
    # Where a zone beside the cell lies under snow at the shared edge, its snow runs on
    # into the scenery for a ragged 30 to 80 px, so a snowfield never stops on a ruled
    # line against green (review 15:54, the ridge beside the forest past the riverside).
    reach = 30 + vnoise(X, Y, 18, 996) * 50
    for (dc, dr) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        z = zone_at(col + dc, row + dr)
        if not z or z == 'garden':
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
        under = (d >= 0) & (d < reach * snowline[along])
        ground = np.where(under[..., None], snowfield, ground)
    inside = np.zeros((CH, CW), dtype=bool)
    inside[S:S + H, S:S + W] = True
    # the railway: the halt's cutting (its walls, ballast, sleepers and rails) carried on
    # west from its edge, column for column, to the portal
    rc_, rr_ = RAIL['cell']
    ry0, ry1 = rr_ * H + RAIL['y0'], rr_ * H + RAIL['y1']
    rx_end = rc_ * W                       # the halt's west edge, in region x
    rx_portal = rx_end - RAIL['portal_in']
    track = (Y >= ry0) & (Y < ry1) & (X >= rx_portal) & (X < rx_end)
    if track.any() and zone_at(rc_, rr_) == RAIL['zone']:
        hg = _zone_ground(RAIL['zone'])
        lx = 1 + np.mod(X - rx_end, 7)
        ly = np.clip(Y - rr_ * H, 0, H - 1)
        ground = np.where(track[..., None], hg[ly, lx], ground)
    _paint(cv, ground, inside)

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
        # what grows at each candidate point (arrays): nothing in water, in a zone or
        # above the treeline; pines below it; crowns at the valley's level, not on the beach
        a, s1, r1, _c, _r = valley_fields(GX, GY)
        zone = np.vectorize(lambda x, y: bool(zone_px(x, y)))(GX, GY)
        beach = GY > _lerp_points(GX, VALLEY_COAST) - 34
        rail = (GY > ry0 - 14) & (GY < ry1 + 22) & (GX > rx_portal - 6) & (GX < rx_end)
        return np.where(s1 | r1 | zone | rail | (a > 0.6), None,
                        np.where(a > 0.12, 'pine', np.where(beach, None, 'crown')))

    # mountains and trees together, back to front
    things = [(by, 'peak', (left, top, w, h, seed, snow)) for (by, left, top, w, h, seed, snow)
              in _peaks(col, row, lambda x, y: field(x, y)[0], free)]
    things += [(gy, what, (gx, rx, k)) for (gy, gx, what, rx, k) in _trees('valley', col, row, kind_at)]
    # Along an edge the forest shares with a zone, a fringe of crowns straddling the edge,
    # so the forest floor never ends on a ruled line against the zone's ground (the
    # crowns reach over it by up to the spill, each by a different amount: review 15:54).
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
            if what == 'crown':
                things.append((gy, 'crown', (gx, 14 + noise2(i, col + row * 7, 563) * 8, i * 131 + col * 17 + row)))
            elif what == 'pine' and noise2(i, col + row * 5, 564) < 0.8:
                things.append((gy + 8, 'pine', (gx, 0, 0)))
    if track.any() and zone_at(rc_, rr_) == RAIL['zone']:
        things.append((ry1, 'portal', None))
    pine = _pine()
    for (by, what, d) in sorted(things, key=lambda t: t[0]):
        if what == 'peak':
            left, top, w, h, seed, snow = d
            sp = _peak(w, h, seed, snow)
            px, py = left - x0, top - y0
            # (cut to the canvas; the neighbouring cell draws the rest the same way)
            cx0, cy0 = max(0, px), max(0, py)
            cx1, cy1 = min(CW, px + w), min(CH, py + h)
            if cx1 > cx0 and cy1 > cy0:
                cv.img.alpha_composite(sp.crop((cx0 - px, cy0 - py, cx1 - px, cy1 - py)), (cx0, cy0))
        elif what == 'portal':
            pi = _portal()
            _stamp(cv, pi, int(rx_portal - x0 - pi.width + 6), int(ry1 - y0 - pi.height))
        elif what == 'crown':
            gx, rx, k = d
            X0, Y0 = gx - x0, by - y0
            rx = max(8.0, min(rx, X0 - 4, CW - X0 - 4, (Y0 - 4) / 0.72, (CH - Y0 - 4) / 0.72))
            if rx >= 8:
                _crown(cv, X0, Y0, rx, k)
        else:
            gx, _rx, _k = d
            X0, Y0 = gx - x0, by - y0
            px, py = int(X0 - pine.w / 2), int(Y0 - pine.h + 8)
            if 0 <= px and px + pine.w <= CW and 0 <= py and py + pine.h <= CH:
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
    out = {}
    for row in range(min(rows) - ring, max(rows) + ring + 1):
        for col in range(min(cols) - ring, max(cols) + ring + 1):
            if (col, row) not in taken:
                if region == 'moon' and row < 0:
                    continue  # above the moon's horizon there is only space (the backdrop)
                out[(col, row)] = paint(col, row, zone_at)
    return out
