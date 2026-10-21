"""The 16 px autotiles: every tile is a 16 x 16 array of palette codes (-1 = nothing), made
from its 3 x 3 neighbourhood and its place in the world, and cached by that key, so the set
the scene uses is a finite tileset (tileset.png) and the scene is laid only from it.

Kinds:
- top(mat, nb, wx, wy): a tier's walkable top, 47-blob by its 8 neighbours (in = same tier or
  higher). Edges by side: south runs to the tile's foot (the lip hangs into the face tile
  below), west a lit 5 px side band, east a dark 5 px side band, north a rim with nothing
  beyond. Corners round off (radius 4) both ways.
- over(base, mat2, nb2, wx, wy): a second material inside a tier, 47-blob: snow (scalloped,
  lit lip, shaded south face), water (earth bank on the north, dark under it), path.
- face(...): one 16 px window of the boulder sheet, with its lip fringe and overhang shadow
  (top row), its darker damp base (bottom row) and rounded, lit or shaded ends.
- foot(base, ...): the ground under a face: contact line, damp shade, fallen stones.
- stair: rounded slab steps with boulder cheeks.
"""
import numpy as np
from scipy import ndimage as ndi

from .. import ctx
from . import sheets
from ..palette import C, step, is_fam
from ..ctx import D, TT, P

T = TT
_CACHE = {}
FACE, FACE_AUX = sheets.face_sheet(seed=ctx.BIOME.get('sheets', {}).get('face', 7))
_SEEDS = ctx.BIOME.get('sheets', {})
SHEETS = {
    'snow': sheets.snow_sheet(64, 64, seed=_SEEDS.get('snow', 5)),
}
BIG = True
# r1: canvas-sized fields, so nothing repeats on screen; Eastward's grass method
_FW, _FH = ctx.PLAN['terrain']['field']
SHEETS['grass'] = sheets.grass_field_d(_FW, _FH, seed=_SEEDS.get('grass', 3))
SHEETS['hgrass'] = sheets.grass_field_d(_FW, _FH, seed=_SEEDS.get('hgrass', 4), density=_SEEDS.get('hgrass_density', 1.1))
# the 1x dirt's own design (soft blotches, short dashes, dents), drawn finer; no repeat
SHEETS['path'] = sheets.path_sheet_d(_FW, _FH, seed=_SEEDS.get('path', 11))
SHEETS['trail'] = sheets.path_sheet_d(_FW, _FH, seed=_SEEDS.get('trail', 12))


def win(sheet, wx, wy):
    H, W = sheet.shape
    ys = (np.arange(T) + wy) % H
    xs = (np.arange(T) + wx) % W
    return sheet[np.ix_(ys, xs)]


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def _vnoise(x, y, cell, seed):
    """Smooth value noise in [0, 1] over world coordinates (hashed lattice, bilinear)."""
    gx, gy = np.floor(x / cell).astype(np.int64), np.floor(y / cell).astype(np.int64)
    fx, fy = x / cell - gx, y / cell - gy
    def h(a, b):
        return (((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) & 0xffff) / 65535.0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return (h(gx, gy) * (1 - sx) + h(gx + 1, gy) * sx) * (1 - sy) + (h(gx, gy + 1) * (1 - sx) + h(gx + 1, gy + 1) * sx) * sy


def _comp(nb):
    c = np.zeros((3 * T, 3 * T), bool)
    for i in range(3):
        for j in range(3):
            if nb[i][j]:
                c[i * T:(i + 1) * T, j * T:(j + 1) * T] = True
    return c


def rounded(m, sigma=3.2, bias=0.5):
    """Round a blocky mask: blur and threshold. Straight edges stay put, convex and concave
    corners both round off (radius about 2.5 sigma), thin strips survive. sigma in world px."""
    sigma = sigma * D
    pd = int(3 * sigma) + 2
    p = np.pad(m.astype(float), pd, mode='edge')
    b = ndi.gaussian_filter(p, sigma)[pd:-pd, pd:-pd]
    return b > bias


def nearest_dir(inside):
    """For each pixel inside: distance to the nearest outside pixel and the direction to it
    (dy, dx) as unit-ish ints."""
    p = np.pad(inside, 2, mode='edge')
    d, (iy, ix) = ndi.distance_transform_edt(p, return_indices=True)
    d = d[2:-2, 2:-2]
    yy, xx = np.mgrid[0:inside.shape[0], 0:inside.shape[1]]
    dy = iy[2:-2, 2:-2] - 2 - yy
    dx = ix[2:-2, 2:-2] - 2 - xx
    return d, dy, dx


def _streaks(W=None, H=None, seed=17):
    W, H = W or P(64), H or P(64)
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W), np.int8)
    for _ in range(int(46 * D * D)):
        y, x, L = int(rng.integers(0, H)), int(rng.integers(0, W)), int(rng.integers(P(3), P(6)))
        for i in range(L):
            a[y, (x + i) % W] = 1
            a[(y + 1) % H, (x + i + 1) % W] = 2
    for _ in range(int(10 * D * D)):
        y, x = int(rng.integers(0, H)), int(rng.integers(0, W))
        a[y, x] = 3
        a[y, (x + 1) % W] = 3
    return a


STREAKS = _streaks()

TOP_FILL = {'grass': 'grass', 'hgrass': 'hgrass', 'path': 'path', 'snow': 'snow'}
LIPFAM = {'grass': 'grass', 'hgrass': 'grass', 'path': 'path', 'snow': 'snow'}


def top(mat, nb, wx, wy, cut=True):
    key = ('top' if cut else 'topback', mat, tuple(map(tuple, nb)), wx if BIG else wx % P(384), wy if BIG else wy % P(192), cut)
    return cached(key, lambda: _top(mat, nb, wx, wy, cut))


def _win48(a, wx, wy):
    H, W = a.shape
    ys = (np.arange(3 * T) + wy - T) % H
    xs = (np.arange(3 * T) + wx - T) % W
    return a[np.ix_(ys, xs)]


def _top(mat, nb, wx, wy, cut=True):
    comp = _comp(nb)
    grass = comp.copy()
    carve = np.zeros((3 * T, 3 * T), np.int8)   # 1 west band, 2 east band, 3 north rim
    for i in range(3):
        for j in range(3):
            if not nb[i][j]:
                continue
            y0, x0 = i * T, j * T
            if j > 0 and not nb[i][j - 1]:
                carve[y0:y0 + T, x0:x0 + P(5)] = 1
            if j < 2 and not nb[i][j + 1]:
                if D > 1:
                    # r8: the east band's inner edge walks 1 to 3 px (the floor's east edge was ruled)
                    for yy_ in range(T):
                        yw_ = (wy + (i - 1) * T + yy_) / D
                        wv_ = P(5) + int(round(1.0 * np.sin(yw_ / 3.3) + 0.8 * np.sin(yw_ / 1.6 + 0.8)))
                        carve[y0 + yy_, x0 + T - wv_:x0 + T] = 2
                else:
                    carve[y0:y0 + T, x0 + T - P(5):x0 + T] = 2
            if i > 0 and not nb[i - 1][j]:
                carve[y0:y0 + P(2), x0:x0 + T] = 3
    grass &= carve == 0
    solid = comp.copy()
    for i in range(1, 3):        # a cell under an in-cell that is out is the face: solid
        for j in range(3):
            if not nb[i][j] and nb[i - 1][j]:
                solid[i * T:(i + 1) * T, j * T:(j + 1) * T] = True
    solid = rounded(solid, 4.2)
    if cut:
        cw, ce = cut if isinstance(cut, tuple) else (True, True)
        # a side band's outer edge follows its lumps: a lump whose centre lies past the
        # brink is left out, so the side reads as stacked rock, not a ruled line
        dxc = _win48(FACE_AUX['dxc'], wx, wy)
        xl = np.mgrid[0:3 * T, 0:3 * T][1] % T
        av = np.abs(_win48(FACE_AUX['V'], wx, wy))
        cutm = (cw & (carve == 1) & (((xl + dxc < P(2)) & (xl <= P(3))) | (xl < 3.5 * D * av ** 2.2))) | \
            (ce & (carve == 2) & (((xl + dxc > T - P(3)) & (xl >= T - P(4))) | (xl > T - 1 - 3.5 * D * av ** 2.2)))
        if D > 1:
            # r7: the east (shaded) band's outer edge is a soft wave, not lump teeth
            yw_ = (np.mgrid[0:3 * T, 0:3 * T][0] + wy - T) / D
            wv = D * (1.5 + 0.3 * np.sin(yw_ / 2.7) + 0.2 * np.sin(yw_ / 1.3 + 1.0))
            cutm = (cutm & (carve != 2)) | (ce & (carve == 2) & (xl > T - 1 - wv))
        solid &= ~cutm
        cutside = np.where((carve == 1) & cutm, -4, np.where((carve == 2) & cutm, -5, 0))[T:2 * T, T:2 * T]
    else:
        cutside = np.zeros((T, T), int)
    grass = rounded(grass, 4.0) & solid
    cs = (slice(T, 2 * T), slice(T, 2 * T))
    G, S = grass[cs], solid[cs]
    fill = win(SHEETS[TOP_FILL[mat]], wx, wy)
    rock = win(FACE, wx, wy)
    out = np.full((T, T), -1, np.int32)
    out[G] = fill[G]
    # rock: which side each pixel belongs to
    lab = carve.copy()
    _, (iy, ix) = ndi.distance_transform_edt(lab == 0, return_indices=True)
    side = lab[iy, ix][cs]
    R = S & ~G
    west = R & (side == 1)
    east = R & (side == 2)
    north = R & ((side == 3) | (side == 0))
    out[west] = np.clip(step(rock[west], 1), 0, None)
    out[west & (rock % 8 == 0)] = C('crag', 1)
    out[east] = step(rock[east], -2)
    out[north] = C('crag', 2)
    # grass edges: a lit lip curling over a west band and the north rim, a shaded lip over
    # an east band, a lit crest at the south brink
    lf = LIPFAM[mat]
    d, dy, dx = nearest_dir(grass)
    d, dy, dx = d[cs], dy[cs], dx[cs]
    near = G & (d <= 1.0)
    near2 = G & (d > 1.0) & (d <= 1.0 + D)
    to_w = dx < 0
    to_e = dx > 0
    to_n = (dy < 0) & (dx == 0)
    to_s = (dy > 0) & (dx == 0)
    yy, xx = np.mgrid[0:T, 0:T]
    wxx = ((xx + wx) / D).astype(int)
    if FIXT and D > 1:
        # r6: a soft lip, no lit line tracing the cell outline: the grass a tone lighter at its
        # sunny edges, a tone darker at its shaded ones, the crest only in broken runs
        out[near & to_w] = step(fill[near & to_w], 1)
        out[near & to_e] = step(fill[near & to_e], -1)
        cr = near & to_s
        run = ((wxx // 3) * 2654435761 >> 5) % 5 < 2
        out[cr & run] = step(fill[cr & run], 1)
    else:
        out[near & to_w] = C(lf, 5) if lf != 'snow' else C('snow', 5)
        out[near2 & to_w] = step(fill[near2 & to_w], 1)
        out[near & to_e] = C(lf, 2)
        out[near2 & to_e] = step(fill[near2 & to_e], -1)
        out[near & to_n] = C(lf, 4)
        cr = near & to_s
        out[cr] = np.where(wxx[cr] % 7 < 4, C(lf, 4), step(fill[cr], 1))
        out[near2 & to_s & (wxx % 5 == 0)] = C(lf, 4)
    # under a lip, the band's first rock pixel is in its shade
    gn = np.zeros((T + 2, T + 2), bool)
    gn[1:-1, 1:-1] = G
    adj = (gn[:-2, 1:-1] | gn[1:-1, :-2] | gn[1:-1, 2:])
    adj = adj & R
    out[adj & west] = C('crag', 2)
    out[adj & east] = C('crag', 0)
    out[adj & north] = C('crag', 1)
    # the turf lip hangs over the top of a side band where grass lies above it (the brink
    # turning the corner): two or three rows of lip and an edge, as on a face below
    gfull = grass
    for x in range(T):
        X = x + T
        for y in range(T):
            Y = y + T
            if R[y, x] and gfull[Y - 1, X] and not gfull[Y, X]:
                wq = int((wx + x) / D)
                dep = P(2) + P(1) * ((wq % 5 == 0) + (wq % 3 == 0)) if not FIXT else P(1)
                for i in range(dep + 1):
                    if y + i < T and R[y + i, x]:
                        out[y + i, x] = C(lf, 3 if i < dep - 1 else 2) if i < dep else C(lf, 6)
                for i in range(dep + 1, dep + 1 + P(2)):
                    if y + i < T and R[y + i, x]:
                        out[y + i, x] = step(out[y + i, x], -1)
    # outline against nothing: the family's edge tone, broken to tone 1 where it closes a
    # lit top or left edge
    sp = np.pad(solid, 1, mode='constant', constant_values=False)[T:2 * T + 2, T:2 * T + 2]
    border = S & ~(sp[:-2, 1:-1] & sp[2:, 1:-1] & sp[1:-1, :-2] & sp[1:-1, 2:])
    fam_e = np.where(is_fam(out, 'crag'), C('crag', 6), C(lf, 6))
    up_open = S & ~sp[:-2, 1:-1]
    left_open = S & ~sp[1:-1, :-2]
    lit_break = (up_open | left_open) & (out % 8 >= 4)
    out[border] = np.where(lit_break[border], out[border] // 8 * 8 + 1, fam_e[border])
    hole = (out < 0) & (cutside < 0)
    out[hole] = cutside[hole]
    return out


# --- second material within a tier -------------------------------------------------------


def scallop(x, period=8, amp=1.6, phase=0):
    return amp * np.abs(np.sin(np.pi * (x + phase) / period)) - amp * 0.5


def over(base, mat2, nb2, wx, wy, key_extra=()):
    key = ('over', mat2, tuple(map(tuple, nb2)), wx if BIG else wx % P(64), wy if BIG else wy % P(64), base.tobytes(), key_extra)
    return cached(key, lambda: _over(base, mat2, nb2, wx, wy))


def _over(base, mat2, nb2, wx, wy):
    comp = _comp(nb2)
    m = rounded(comp, {'snow': 5.0, 'water': 5.5, 'trail': 8.0 if FIXT else 6.0}.get(mat2, 3.6))
    yy, xx = np.mgrid[0:3 * T, 0:3 * T]
    if mat2 == 'snow':
        pd = P(4)
        din = ndi.distance_transform_edt(np.pad(m, pd, mode='edge'))[pd:-pd, pd:-pd]
        dout = ndi.distance_transform_edt(np.pad(~m, pd, mode='edge'))[pd:-pd, pd:-pd]
        sd = din - dout + scallop(xx + wx - T, 7 * D, 2.2 * D) + scallop(yy + wy - T, 9 * D, 1.2 * D, 3 * D)
        m = sd > 0
    cs = (slice(T, 2 * T), slice(T, 2 * T))
    M = m[cs] & (is_fam(base, 'grass') | is_fam(base, 'leaf'))
    out = base.copy()
    d, dy, dx = nearest_dir(m)
    d, dy, dx = d[cs], dy[cs], dx[cs]
    # outside pixels next to the material
    d2, dy2, dx2 = nearest_dir(~m)
    d2, dy2, dx2 = d2[cs], dy2[cs], dx2[cs]
    to_s = (dy > 0) & (np.abs(dx) <= np.abs(dy))
    to_n = (dy < 0) & (np.abs(dx) <= np.abs(dy))
    to_w = (dx < 0) & ~to_s & ~to_n
    to_e = (dx > 0) & ~to_s & ~to_n
    if mat2 == 'snow':
        fill = win(SHEETS['snow'], wx, wy)
        out[M] = fill[M]
        e1 = M & (d <= 1)
        e2 = M & (d > 1) & (d <= 1 + D)
        e3 = M & (d > 1 + D) & (d <= 1 + 2 * D)
        out[e1 & to_s] = C('snow', 1)
        out[e2 & to_s] = C('snow', 2)
        out[e3 & to_s] = C('snow', 5)
        out[e1 & to_w] = C('snow', 5)
        out[e1 & to_n] = C('snow', 4)
        out[e1 & to_e] = C('snow', 2)
        # the ground just south of the snow lies in its shade (two tones down)
        g = ~M & (base >= 0)
        sh1 = g & (d2 <= 1) & (dy2 < 0)
        sh2 = g & (d2 > 1) & (d2 <= 1 + D) & (dy2 < 0)
        out[sh1] = step(base[sh1], -2)
        out[sh2] = step(base[sh2], -1)
        # the snow's own edge: one pixel of its edge tone against the ground to the south
        out[e1 & to_s & ((((xx[cs] + wx) / D).astype(int)) % 6 == 0)] = C('snow', 6)
    elif mat2 == 'water' and FIXT:
        # r1: one calm body tone; a dark band under the cliff (north) stepping back in three
        # steps; a 1 px light waterline on the other shores; an earth bank, lit where it faces
        # the light (the south and east banks), shaded on the west; a few glints only
        out[M] = C('water', 2)
        # the dark band under the north bank, measured straight down each column (no stair-steps)
        run = np.zeros(m.shape, int)
        for yy_ in range(1, m.shape[0]):
            run[yy_] = np.where(m[yy_], run[yy_ - 1] + 1, 0)
        dv = run[cs]
        if D > 1:
            # r6: the band follows a smoothed shoreline, so it does not repeat the bank's steps
            mm = m.astype(bool)
            ytop = np.where(mm.any(0), mm.argmax(0), -1).astype(float)
            ok = ytop >= 0
            if ok.any():
                yt = np.where(ok, ytop, np.nan)
                k_ = P(6)
                pad_ = np.pad(yt, k_, mode='edge')
                sm_ = np.array([np.nanmean(pad_[i:i + 2 * k_ + 1]) if not np.isnan(pad_[i + k_]) else np.nan
                                for i in range(len(yt))])
                yy3 = np.mgrid[0:m.shape[0], 0:m.shape[1]][0]
                dvs = np.where(ok[None, :], yy3 - np.nan_to_num(sm_, nan=0.0)[None, :], 99)
                dv = np.maximum(dvs[cs], 0)
        out[M & (dv <= 2 * D)] = C('water', 0)
        out[M & (dv > 2 * D) & (dv <= 4.5 * D)] = C('water_cool', 1)
        out[M & (dv > 4.5 * D) & (dv <= 7 * D)] = C('water', 1)
        out[M & (d <= 1) & ~to_n & (dv > 7 * D)] = C('water', 4)
        st = win(STREAKS, wx, wy)
        gl = M & (d >= 4 * D) & (st == 3) & ((((xx[cs] + wx) // P(23)) + ((yy[cs] + wy) // P(17))) % 3 == 0)
        out[gl] = C('water', 5)
        g = ~M & (base >= 0) & (is_fam(base, 'grass') | is_fam(base, 'leaf'))
        bank = g & (d2 <= D + 0.01)
        out[bank & (dy2 > 0)] = C('earth', 1)                     # water south of it: the north bank
        out[bank & (dy2 < 0)] = C('earth_warm', 3)                # the south bank faces the light
        out[bank & (dx2 > 0) & (np.abs(dx2) > np.abs(dy2))] = C('earth', 2)   # west shore, shaded
        out[bank & (dx2 < 0) & (np.abs(dx2) > np.abs(dy2))] = C('earth_warm', 3)  # east shore, lit
        lip2 = g & (d2 > D + 0.01) & (d2 <= D + 1.01)
        out[lip2 & ((dy2 < 0) | (dx2 < 0))] = C('grass', 4)
        out[lip2 & ~((dy2 < 0) | (dx2 < 0))] = C('grass', 2)
    elif mat2 == 'water':
        # depth in soft bands: shallows by the shore, the body, a deep core
        out[M] = C('water', 2)
        out[M & (d <= 2.5 * D)] = C('water', 3)
        out[M & (d >= 6 * D)] = C('water_cool', 2)
        out[M & (d >= 9 * D)] = C('water_cool', 1)
        # the current: lit streaks over their own shadow, glints in pairs
        st = win(STREAKS, wx, wy)
        inn = M & (d >= 3 * D)
        out[inn & (st == 1)] = C('water', 4)
        out[inn & (st == 2)] = C('water', 1)
        out[inn & (st == 3)] = C('water', 5)
        # dark under the north bank: the bank's face (earth), then deep shade on the water
        out[M & (d <= 1) & to_n] = C('earth', 2)
        out[M & (d > 1) & (d <= 1 + D) & to_n] = C('earth', 1)
        out[M & (d > 1 + D) & (d <= 1 + 3 * D) & to_n] = C('water', 0)
        out[M & (d > 1 + 3 * D) & (d <= 1 + 4.5 * D) & to_n] = C('water', 1)
        out[M & (d <= 1) & to_w] = C('earth', 2)
        out[M & (d <= 1) & to_e] = C('earth', 1)
        out[M & (d <= 1) & to_s] = C('water', 4)
        g = ~M & (base >= 0)
        lipm = g & (d2 <= 1)
        out[lipm & (dy2 > 0)] = C('grass', 4)
        out[lipm & ~(dy2 > 0)] = C('grass', 1)
    elif mat2 == 'trail':
        fill = win(SHEETS['trail'], wx, wy)
        out[M] = step(fill[M], -1)

        if not FIXT:
            out[M & (d <= 1) & to_n] = C('path', 1)
            out[M & (d > 1) & (d <= 1 + D) & to_n] = C('path', 2)
            out[M & (d <= 1) & to_w] = C('path', 2)
            out[M & (d <= 1) & (to_s | to_e)] = C('path', 3)
        g = ~M & (base >= 0)
        lipm = g & (d2 <= 1)
        if not FIXT:
            out[lipm & ((((xx[cs] + yy[cs] + wx) / D).astype(int)) % 3 != 0)] = C('grass', 4)
        if D != 1 or FIXT:
            # Eastward's frayed edge: grass reaching over the dirt 0 to 3 world px, broken in
            # runs of a few px, its tips lit; a damp darker row of dirt just inside it
            Xw = ((xx[cs] + wx) / D).astype(int)
            Yw = ((yy[cs] + wy) / D).astype(int)
            hsh = ((Xw * 73856093) ^ (Yw * 19349663) ^ 0x5bd1e995) & 0xffff
            # a wavy grass margin 0 to 3 world px over the dirt, with single blades poking past it
            if FIXT:
                # r1b: the edge wanders 1 to 3 world px over 8 to 16 px runs (smooth value
                # noise), with a tuft over it or a bite out of it every 12 to 20 px, irregularly
                wxf = (xx[cs] + wx) / D
                wyf = (yy[cs] + wy) / D
                lob = _vnoise(wxf, wyf, 7.0, 11) * 2.4 + 0.6
                ev = _vnoise(wxf, wyf, 15.0, 29)
                lob = lob + np.where(ev > 0.78, (ev - 0.78) * 14, 0) - np.where(ev < 0.2, (0.2 - ev) * 16, 0)
                wave = np.round(lob * D)
                bl = ((hsh % 29) == 0) * D
                depth = np.maximum(wave, 0) + bl
                bite = g & (wave < 0) & (d2 <= -wave) & (d2 > 0)
                out[bite] = step(fill[bite], -2)
            else:
                wave = 1.1 + 1.0 * np.sin(Xw * 0.83 + Yw * 0.61) + 0.7 * np.sin(Xw * 0.31 - Yw * 1.17 + 2.0)
                wave = np.clip(np.round(wave), 0, 3) * D
                bl = (hsh % 6 == 0) * (1 + hsh // 6 % 2) * D
                depth = wave + bl
            grass = M & (d <= depth) & (d >= 0.5)
            out[grass] = base[grass]
            if not FIXT:
                rim = M & (d <= wave) & (d > wave - 1) & (wave > 0)
                out[rim] = step(base[rim], 1)
            tip = M & (bl > 0) & (d > depth - D) & (d <= depth)
            out[tip] = C('grass', 4)
            # the dirt along the margin is a shade darker (damp, in the grass's shadow)
            damp = M & ~grass & (d <= depth + 1)
            if FIXT and D == 1:
                # r3: at 1x the damp row breaks into crumbs (no ruled dark rim along the path)
                hr = (((Xw // 2) * 2654435761) ^ ((Yw // 2) * 40503) ^ 0x1b873593) & 0xff
                damp &= (hr % 11 < 2)
            out[damp] = step(out[damp], -1)
            if FIXT:
                # crumbs: dark dirt specks just outside the edge, and pebble pairs just inside
                cr = g & (d2 <= D) & (d2 > 0.5) & (hsh % 211 == 0)
                Xc, Yc = Xw, Yw
                for (yy0, xx0) in zip(*np.nonzero(cr)):
                    for a_ in range(P(1)):
                        for b_ in range(P(1)):
                            Y_, X_ = yy0 + a_, xx0 + b_
                            if Y_ < T and X_ < T:
                                out[Y_, X_] = C('path', 1)
                pb = M & ~grass & (d > depth + 1) & (d <= depth + 1 + 2 * D) & (hsh % 53 == 0)
                for (yy0, xx0) in zip(*np.nonzero(pb)):
                    for q in range(2 if (hsh[yy0, xx0] // 53) % 2 else 3):
                        Y_, X_ = yy0 + (q % 2) * P(1), xx0 + q * P(2)
                        for a_ in range(P(1)):
                            for b_ in range(P(1.5)):
                                Y2, X2 = Y_ + a_, X_ + b_
                                if Y2 < T and X2 < T and M[Y2, X2]:
                                    out[Y2, X2] = C('stone', 4 if (a_ == 0 and b_ == 0) else 3)
                        if Y_ + P(1) < T and X_ < T and M[min(T - 1, Y_ + P(1)), X_]:
                            out[min(T - 1, Y_ + P(1)), X_] = C('path', 1)
    return out


# --- faces --------------------------------------------------------------------------------
def _profile(n, seed, wmin, wmax, dmin, dmax):
    n, wmin, wmax, dmin, dmax = P(n), P(wmin), P(wmax), P(dmin), P(dmax)
    """A lip's hanging depth along x: soft scallops, flat-bottomed (a cushion of turf over the
    brink, not teeth). Periodic over n px."""
    rng = np.random.default_rng(seed)
    prof = np.zeros(n, int)
    x = 0
    while x < n:
        w = int(rng.integers(wmin, wmax + 1))
        dm = int(rng.integers(dmin, dmax + 1))
        for i in range(w):
            if x + i < n:
                prof[x + i] = max(1, int(round(dm * np.sin(np.pi * (i + 0.5) / w) ** 0.3)))
        x += w
    return prof


PROF = {
    'g': _profile(64, 21, 8, 13, 3, 5),
    'gdeep': _profile(64, 22, 9, 14, 5, 7),
    's': _profile(64, 23, 7, 11, 3, 6),
    'p': np.full(P(64), P(2)),
}
FIXT = True
LIP_TUFT_SEG = ctx.BIOME.get('style', {}).get('lip', {}).get('tuft_every', 24.0)     # r7: world px between the tufts hanging over a lip (one per segment, some skipped)
if FIXT:
    # r1: a clean lip, no teeth. The turf ends in one darker row on a 1 px wobble: one world px
    # deep, plus one art px in runs of 3 to 10 world px (overhang at most 1 px at 1x, 2 at 2x)
    def _lip(n, seed, at1=False):
        rng = np.random.default_rng(seed)
        prof = np.zeros(P(n), int)
        x = 0
        while x < P(n):
            w = P(int(rng.integers(3, 11)))
            prof[x:x + w] = P(1) + (1 if (rng.random() < 0.5 and (D > 1 or at1)) else 0)
            x += w
        return prof
    # r4: the ledge floor's rim wobbles too (it was ruled), at 1x as well
    PROF = {'g': _lip(64, 21), 'gdeep': _lip(64, 22), 's': _lip(64, 23), 'p': _lip(64, 24, at1=True)}
    if D > 1:
        # r8: the turf lip's depth walks in one-px steps (0 to 2 px, runs of 2 to 6 world px), so
        # its dark row never runs straight
        def _walk(seed):
            rw = np.random.default_rng(seed)
            pr = np.zeros(P(64), int)
            x_, v_ = 0, 1
            while x_ < P(64):
                w_ = P(float(rw.uniform(2, 6)))
                pr[x_:x_ + w_] = P(1) + v_
                v_ = int(np.clip(v_ + rw.choice([-1, 1]), 0, 2))
                x_ += w_
            return pr
        PROF['g'], PROF['gdeep'] = _walk(31), _walk(32)
    PRIM = _lip(64, 25, at1=True) - P(1)        # 0 or 1 px, in runs of 3 to 10 world px
    if D > 1:
        # r7: the rim's lit row wanders (a walk of one px steps, 0 to 3 px at 2x, runs of 2 to 6
        # world px) so it never reads as a ruled line
        _rr = np.random.default_rng(26)
        _pr = np.zeros(P(64), int)
        _x, _v = 0, 1
        while _x < P(64):
            _w = P(float(_rr.uniform(2, 6)))
            _pr[_x:_x + _w] = _v
            _v = int(np.clip(_v + _rr.choice([-1, 1]), 0, P(1.5)))
            _x += _w
        PRIM = _pr


def face(wx, wy, k, d, lt, rt, fringe, deep=False, snowy=False, wet=None):
    key = ('face', wx % P(128), wy % P(64), k, d, lt, rt, fringe, deep, snowy, wet)
    return cached(key, lambda: _face(wx, wy, k, d, lt, rt, fringe, deep, snowy, wet))


def face_backing(wx, wy, k, d, fringe, deep=False, snowy=False, wet=None):
    """The same window without its end cuts: shown only where a cut would open onto nothing."""
    key = ('backing', wx % P(128), wy % P(64), k, d, fringe, deep, snowy, wet)
    return cached(key, lambda: _face(wx, wy, k, d, 'cont', 'cont', fringe, deep, snowy, wet))


def _face(wx, wy, k, d, lt, rt, fringe, deep, snowy, wet):
    out = win(FACE, wx, wy).copy()
    crev = win(FACE_AUX['crev'].astype(np.int32), wx, wy).astype(bool)
    V = win(FACE_AUX['V'], wx, wy)
    lam = win(FACE_AUX['lam'], wx, wy)
    dxc = win(FACE_AUX['dxc'], wx, wy)
    yy, xx = np.mgrid[0:T, 0:T]
    fy = (k * T + yy) / (d * T)
    # damp, shaded base: the lowest third a tone down (r1: measured up from the foot in world
    # px, so faces of different heights side by side share one line, no seam at the cell edge)
    if FIXT:
        low = (((d - k) * T - yy) <= P(10)) & ~crev
    else:
        low = (fy > 0.68) & ~crev
    out[low] = step(out[low], -1)
    if snowy:   # snow lodged on the lumps' crowns
        cap = (V < -0.74) & (lam > 0.5) & ~crev & (fy < 0.85)
        out[cap] = np.where(lam[cap] > 0.8, C('snow', 4), C('snow', 3))
        capu = np.roll(cap, 1, 0) & ~cap & ~crev
        out[capu] = C('snow_cool', 1)
    alpha = np.ones((T, T), bool)
    # ends: the wall turns away; the silhouette follows the lumps (a lump whose centre lies
    # past the end is left out), the last lumps lit on the west end, shaded on the east
    dyc = win(FACE_AUX['dyc'], wx, wy)
    side = np.zeros((T, T), int)
    av = np.abs(V)
    if lt == 'outer':
        cut = ((xx + dxc < P(2)) & (xx <= P(4))) | (xx < 4.0 * D * av ** 2.2)
        alpha &= ~cut
        side[cut] = -4
    if rt == 'outer':
        cut = ((xx + dxc > T - P(3)) & (xx >= T - P(5))) | (xx > T - 1 - 4.0 * D * av ** 2.2)
        alpha &= ~cut
        side[cut] = -5
    if k == d - 1:
        # the foot follows the lumps too: a lump centred below the foot line is left out
        cut = (yy + dyc > T - P(2)) & (yy >= T - P(4))
        alpha &= ~cut
        side[cut & (side == 0)] = -6
    if FIXT and (k == d - 1 or lt == 'outer' or rt == 'outer'):
        # r3: a boulder that crosses the face's foot or an open end is not sliced on the cell
        # line: it is squashed to end there, so it turns under in a round bottom and rounds off
        # at the end (no vertical side longer than a few px, no flat-cut base); the foot line
        # also wobbles by one world px in runs of 1 to 10
        Uv = win(FACE_AUX['U'], wx, wy)
        Vv = win(FACE_AUX['V'], wx, wy)
        bidw = win(FACE_AUX['bid'], wx, wy)
        dx = -dxc.astype(float)
        dy = -dyc.astype(float)
        cx = xx + dxc
        cy = yy + dyc
        rx = np.where(np.abs(Uv) > 0.08, np.abs(dx / np.where(np.abs(Uv) > 0.08, Uv, 1)), 1e9)
        ry = np.where(np.abs(Vv) > 0.08, np.abs(dy / np.where(np.abs(Vv) > 0.08, Vv, 1)), 1e9)
        rxf, ryf = rx.copy(), ry.copy()
        if lt == 'outer':
            sq = (dx < 0) & (cx - rx < 0)
            rxf = np.where(sq, np.maximum(cx - 0.5, 0.5), rxf)
        if rt == 'outer':
            sq = (dx > 0) & (cx + rx > T - 0.5)
            rxf = np.where(sq, np.maximum(T - 0.5 - cx, 0.5), rxf)
        if k == d - 1:
            sq = (dy > 0) & (cy + ry > T - 0.5)
            ryf = np.where(sq, np.maximum(T - 0.5 - cy, 0.5), ryf)
        q = np.abs(dx / rxf) ** 2.4 + np.abs(dy / ryf) ** 2.4
        changed = (rxf < rx - 0.01) | (ryf < ry - 0.01)
        rcut = (bidw >= 0) & changed & (q > 1.0)
        # a lump whose centre lies past the end or the foot was sliced on the cut line: what is
        # left of it becomes a smaller lump of its own, rounded off before the cut
        def _beyond(lo, hi, cc, rr, other, other_r):
            ctr = (lo + hi) / 2.0
            half = np.maximum((hi - lo) / 2.0, 0.5)
            return np.abs((cc - ctr) / half) ** 2.4 + np.abs(other / other_r) ** 2.4 > 1.0
        if rt == 'outer':
            bey = (bidw >= 0) & (cx > T - P(3))
            rcut |= bey & _beyond(cx - rx, T - P(5), xx + 0.5, rx, dy, ry)
        if lt == 'outer':
            bey = (bidw >= 0) & (cx < P(2))
            rcut |= bey & _beyond(P(4), cx + rx, xx + 0.5, rx, dy, ry)
        if k == d - 1:
            bey = (bidw >= 0) & (cy > T - P(2))
            rcut |= bey & _beyond(cy - ry, T - P(4), yy + 0.5, ry, dx, rx)
        # an open end is a stack of rounded boulder ends, not a ruled cut: scallops 8 to 12
        # world px tall, each bulging out by up to 3 world px
        yw = (wy + yy) / D
        def _scal(seed):
            per = 10.0
            ph = ((seed * 2654435761) % 997) / 997.0 * per
            n = np.floor((yw + ph) / per)
            pj = per * (0.8 + 0.4 * (((n * 40503 + seed) % 7) / 6.0))
            u = (((yw + ph) % per) / per) * 2 - 1
            prof = 1 - np.sqrt(np.clip(1 - (u * 0.92) ** 2, 0, 1))
            return D * 2.0 * prof / 0.6 * (pj / per)
        if rt == 'outer':
            rcut |= (cx > T - P(3)) & (xx > T - P(5) - _scal(int(wx / D) + 17))
        if lt == 'outer':
            rcut |= (cx < P(2)) & (xx < P(4) + _scal(int(wx / D) + 5))
        if k == d - 1:
            depth = (T - 1 - yy)
            wq = (((wx + xx) % P(128)) / D).astype(np.int64)
            run = (wq * 2654435761 // 7 ^ 0x5bd1) & 0xffff
            seg = (wq + (run % 3)) // 6
            wob = (((seg * 40503) ^ (seg >> 1) * 977) % 5 < 2).astype(int) * P(1)
            rcut |= depth < wob
        rcut &= alpha
        alpha &= ~rcut
        side[rcut & (side == 0) & (xx < P(4)) & (lt == 'outer')] = -4
        side[rcut & (side == 0) & (xx >= T - P(5)) & (rt == 'outer')] = -5
        side[rcut & (side == 0)] = -6
    if k == d - 1:
        r = P(7)
        if lt == 'outer':
            alpha &= ~((yy > T - 1 - r) & (xx < r - np.sqrt(np.clip(r * r - (yy - (T - 1 - r)) ** 2, 0, None))))
        if rt == 'outer':
            alpha &= ~((yy > T - 1 - r) & (xx > T - 1 - r + np.sqrt(np.clip(r * r - (yy - (T - 1 - r)) ** 2, 0, None))))
    if FIXT:
        lt = 'cont' if lt == 'edge' else lt
        rt = 'cont' if rt == 'edge' else rt
    if lt in ('outer', 'edge') or rt in ('outer', 'edge'):
        dist_edge = ndi.distance_transform_edt(np.pad(alpha, ((0, 0), (1, 1)), constant_values=False))[:, 1:-1]
        if lt in ('outer', 'edge'):
            m = alpha & (dist_edge <= P(3)) & (xx < T // 2) & ~crev
            out[m] = step(out[m], 1)
        if rt in ('outer', 'edge'):
            m = alpha & (dist_edge <= P(4)) & (xx >= T // 2) & ~crev
            out[m] = step(out[m], -1)
            m = alpha & (dist_edge <= P(2)) & (xx >= T // 2)
            out[m] = step(out[m], -1)
    if k == 0 and fringe is not None:
        for x in range(T):
            f = fringe[x]
            if f is None:
                continue
            pk = 'gdeep' if (f == 'g' and deep) else f
            dep = int(PROF[pk][(wx + x) % P(64)])
            dl = min([abs(x - j) for j in range(T) if fringe[j] is None] + [99])
            dep = min(dep, dl + 1)
            fam = {'g': 'grass', 's': 'snow', 'p': 'crag'}[f]
            lit_y, lit_on = 0, True
            if FIXT and D > 1 and f == 'g':
                # r8: the lip's lit crest in broken runs, now and then a px lower (it ran straight)
                sgq = int(((wx + x) / D + 7 * np.sin((wx + x) / D / 9.0)) // 4)
                hq_ = (sgq * 2654435761 >> 6) % 7
                lit_on = hq_ != 0
                lit_y = 1 if (hq_ in (2, 5) and dep > 3) else 0
            po = int(PRIM[(wx + x) % P(64)]) if (FIXT and f == 'p') else 0
            if f == 'p':
                dep = max(dep, po + 2)
            for y in range(dep):
                if f == 'p':
                    if FIXT and y < po:
                        out[y, x] = C('path', 3)   # r5: the floor reaches a px further in runs (no ruled rim)
                        continue
                    out[y, x] = C('crag_warm', 4) if y == po else C('crag', 3)
                    continue
                if y == dep - 1:
                    t = 2 if f == 'g' else 1
                elif y == dep - 2 and dep > 3:
                    t = 2 if f == 'g' else 2
                elif y == lit_y:
                    t = 4 if lit_on else 3
                else:
                    t = 3
                ff = fam if (int((x + wx) / D) // 3 + int(y / D)) % 4 else fam + '_cool'
                out[y, x] = C(ff, t)
            if f != 'p' and dep < T:
                out[dep, x] = C(fam, 6)
            if FIXT and D > 1 and f == 'g':
                # r7: an occasional tuft hangs over the lip (one per 16 to 32 world px, irregular),
                # its blades of different lengths, a little shade under it on the face; the lip
                # between tufts stays clean
                xw = (wx + x) / D
                seg = int(xw // LIP_TUFT_SEG)
                hs = (seg * 2654435761 + 977) & 0xffff
                if hs % 3 != 0:
                    ctr = seg * LIP_TUFT_SEG + 3 + (hs >> 3) % int(LIP_TUFT_SEG - 6)
                    off = xw - ctr
                    if abs(off) <= 3.0:
                        hb_ = ((int(xw * 2) * 40503) ^ hs) & 0xff
                        ln_ = P(1.0 + 3.0 * (1 - abs(off) / 3.2) * (0.5 + (hb_ % 7) / 12.0))
                        if hb_ % 4 != 0:
                            for y in range(dep, min(T, dep + ln_)):
                                out[y, x] = C('grass', 3 if y < dep + ln_ - P(1) else 4)
                            if dep + ln_ < T and is_fam(out[dep + ln_:dep + ln_ + 1, x:x + 1], 'crag')[0, 0]:
                                out[dep + ln_, x] = step(out[dep + ln_, x], -1)
            s0 = dep + 1
            s1 = s0 + P(2) + int(x / D) // 8
            s2 = s1 + P(2)
            for y in range(s0, min(T, s2)):
                if is_fam(out[y:y + 1, x:x + 1], 'crag')[0, 0]:
                    out[y, x] = step(out[y, x], -2 if y < s1 else -1)
            if FIXT and D > 1 and f == 'g':
                # Eastward's streak zone under a lip: short horizontal marks for 6 to 10 world px
                wq = int((wx + x) / D)
                for y in range(s2, min(T, s2 + P(8))):
                    yq = int(y / D)
                    hq = ((wq // 3) * 2654435761 ^ yq * 40503) & 0xff
                    if hq < 34 and is_fam(out[y:y + 1, x:x + 1], 'crag')[0, 0] and not crev[y, x]:
                        out[y, x] = step(out[y, x], -1 if hq < 22 else 1)
            # hanging strands of grass and roots from a deep turf lip: short leaf clusters
            hx = ((int((wx + x) / D)) * 2654435761) % 97
            if f == 'g' and deep and hx < 9 and dep >= P(4) and not FIXT:
                ln = P(2) + P(1) * (hx % 3)
                for y in range(dep, min(T, dep + ln)):
                    out[y, x] = C('grass', 3 if y < dep + ln - 1 else 2)
                if dep + ln < T:
                    out[dep + ln, x] = C('grass', 6)
    if k == d - 1:
        for x in range(T):
            col = np.nonzero(alpha[:, x])[0]
            if len(col):
                out[col[-1], x] = C('crag', 0)
    if wet is not None:   # the rock beside a trickle is dark and wet
        x0, x1 = wet
        m = (xx >= x0 - P(0.5)) & (xx <= x1 + P(0.5)) & ~crev     # r8: a narrow wet strip (a wide one read as light from the east)
        out[m] = step(out[m], -1)
    out[~alpha] = np.where(side[~alpha] < 0, side[~alpha], -1)
    o = alpha
    p = np.pad(o, 1, constant_values=True)
    border = o & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    out[border] = C('crag', 6)
    return out


# --- stairs cut into a face ---------------------------------------------------------------


# --- the ground at the foot of a face -----------------------------------------------------
PEBBLES = [
    ('.43.',
     '4321',
     '.10.'),
    ('43',
     '21'),
    ('.443.',
     '43321',
     '32210',
     '.000.'),
    ('543',
     '321',
     '.0.'),
]


def stamp(out, rows, y, x, fam, mask_ok=None):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == '.':
                continue
            yy, xx = y + dy, x + dx
            if 0 <= yy < out.shape[0] and 0 <= xx < out.shape[1]:
                if mask_ok is not None and not mask_ok[yy, xx]:
                    continue
                out[yy, xx] = C(fam, int(ch))


def foot(base, wx, wy, density=1.0, key_extra=()):
    key = ('foot', base.tobytes(), wx % P(64), wy % P(64), density, key_extra)
    return cached(key, lambda: _foot(base, wx, wy, density))


def _foot(base, wx, wy, density):
    out = base.copy()
    ok = base >= 0
    xx = np.arange(T)
    # contact line and damp shade under the wall (r3: with the fixes the composite draws it
    # under the face's own silhouette, so it follows the round boulder bottoms)
    for x in (range(0) if FIXT else range(T)):
        wq = int((wx + x) / D)
        dep = P(2) + P(1) * (wq * 7 % 5 == 0)
        out[0, x] = step(base[0, x], -3)
        for y in range(1, dep + 1):
            out[y, x] = step(base[y, x], -2 if y < dep else -1)
        for y in range(dep + 1, dep + 1 + P(2)):
            if (wq + int(y / D)) % 4:
                out[y, x] = step(base[y, x], -1)
    # fallen stones, thinning away from the wall, each with its own contact shade
    wxw, wyw = int(round(wx / D)), int(round(wy / D))     # world coords: the same stones at every density
    rng = np.random.default_rng((wxw * 73856093 ^ wyw * 19349663) & 0xffffffff)
    if FIXT:
        # r1: rubble in clusters of 2 to 4 stones close under the wall, each stone lit at its
        # upper left, dark beneath, with a contact line on the ground
        for _ in range(int(round(1.2 * density + rng.random() * 0.8))):
            cyw, cxw = rng.uniform(2.5, 6.0), rng.uniform(2, 14)
            for q in range(int(rng.integers(2, 5))):
                ry, rx = rng.uniform(0.8, 1.6), rng.uniform(1.0, 2.3)
                sy, sx = cyw + rng.uniform(-1.5, 1.5), cxw + q * 2.6 + rng.uniform(-0.5, 0.5)
                fam = ('crag_warm', 'crag', 'stone_warm')[int(rng.integers(0, 3))]
                for Y in range(P(sy - ry - 1, 0), P(sy + ry + 1, 0) + 1):
                    for X in range(P(sx - rx - 1, 0), P(sx + rx + 1, 0) + 1):
                        if not (0 <= Y < T and 0 <= X < T) or not ok[Y, X]:
                            continue
                        vy, vx = (Y / D + 0.5 / D - sy) / ry, (X / D + 0.5 / D - sx) / rx
                        r2 = vx * vx + vy * vy
                        if r2 <= 1:
                            t = 4 if (vy < -0.3 and vx < 0.2) else (1 if vy > 0.45 else 3)
                            out[Y, X] = C(fam, t)
                        elif r2 <= 1.0 + 2.2 / (ry * D + 1) and vy > 0.3 and not is_fam(out[Y:Y + 1, X:X + 1], 'crag')[0, 0]                                 and not is_fam(out[Y:Y + 1, X:X + 1], 'stone')[0, 0]:
                            out[Y, X] = step(base[Y, X], -2)
        return out
    n = int(round(3 * density))
    for _ in range(n):
        p = PEBBLES[int(rng.integers(0, len(PEBBLES)))]
        y = P(int(rng.integers(1, 9)), 0)
        x = int(round(int(rng.integers(-1, 16 - 2)) * D))
        fam = ['crag', 'crag_warm', 'crag_cool'][int(rng.integers(0, 3))]
        if D != 1:
            from . import decals
            lp = decals.lump(P(len(p[0])), P(len(p)), int(rng.integers(0, 10 ** 6)), fams=(fam,))
            lm = lp >= 0
            ys_, xs_ = np.nonzero(lm)
            for dy, dx in zip(ys_, xs_):
                sy, sx = y + dy + P(1), x + dx + P(1)
                if 0 <= sy < T and 0 <= sx < T and out[sy, sx] >= 0 and not is_fam(out[sy:sy + 1, sx:sx + 1], 'crag')[0, 0]:
                    out[sy, sx] = step(base[sy, sx], -2)
            for dy, dx in zip(ys_, xs_):
                yy_, xx_ = y + dy, x + dx
                if 0 <= yy_ < T and 0 <= xx_ < T and ok[yy_, xx_]:
                    out[yy_, xx_] = lp[dy, dx]
            continue
        # shade on the ground to the lower right
        for dy, row in enumerate(p):
            for dx, ch in enumerate(row):
                if ch != '.':
                    sy, sx = y + dy + 1, x + dx + 1
                    if 0 <= sy < T and 0 <= sx < T and out[sy, sx] >= 0 and not is_fam(out[sy:sy + 1, sx:sx + 1], 'crag')[0, 0]:
                        out[sy, sx] = step(base[sy, sx], -2)
        stamp(out, p, y, x, fam, ok)
    return out


# --- the fixed stair (pilot r1): a wide flight of slab steps between straight cheeks ---------
def stair2(wx, wy, k, d, cell, ncols, x0, x1, seed=91):
    """One cell of a flight `ncols` cells wide rising through a d-tile face. x0..x1 (world px
    from the flight's west cell edge) is the tread band; outside it the cheeks are the face's
    own rock, a tone down, with a crisp dark line along the stair. Five steps: each a slab
    tread (tone 3 at the back, 4 in the middle, a lit tone-5 nosing at the front) over a riser
    in shade (tone 1, a tone-0 line at its foot). One joint per tread at most, offset."""
    key = ('stair2', wx % P(128), wy % P(64), k, d, cell, ncols, x0, x1, seed)
    return cached(key, lambda: _stair2(wx, wy, k, d, cell, ncols, x0, x1, seed))


def _stair2(wx, wy, k, d, cell, ncols, x0, x1, seed):
    out = win(FACE, wx, wy).copy()
    yy, xx = np.mgrid[0:T, 0:T]
    gy = k * T + yy
    gx = cell * T + xx
    Hs = d * T
    n = 5
    bnd = [int(round(i * Hs / n)) for i in range(n + 1)]
    X0, X1 = P(x0, 0), P(x1, 0)
    rng = np.random.default_rng(seed)
    joints = [X0 + int((0.25 + 0.5 * rng.random()) * (X1 - X0)) if rng.random() < 0.7 else -99 for _ in range(n)]
    cheek = (gx < X0)
    out[cheek] = step(out[cheek], -1)          # the west cheek faces east: in shade
    # r7: one soft worn patch per tread, at its own place and width (no repeated patch, no stripes)
    wear = []
    for i_ in range(n):
        rw = np.random.default_rng(seed * 31 + i_ * 7 + 3)
        wc = X0 + (X1 - X0) * rw.uniform(0.3, 0.7)
        ww = (X1 - X0) * rw.uniform(0.12, 0.22)
        wear.append((wc, ww, rw.integers(0, 1 << 16)))
    for y in range(T):
        for x in range(T):
            g, G = gx[y, x], gy[y, x]
            if g == X0 - 1:
                out[y, x] = C('crag', 0)
                continue
            if g == X1:
                out[y, x] = C('crag_warm', 4) if (G % P(6)) else C('crag', 2)   # the east cheek faces the light
                continue
            if not (X0 <= g < X1):
                continue
            i = max(j for j in range(n) if bnd[j] <= G)
            r = G - bnd[i]
            hgt = bnd[i + 1] - bnd[i]
            tread = max(2, int(round(hgt * 0.58)))
            fam = 'path_warm' if (i % 2) else 'path'
            if r < tread:
                if r == tread - 1:
                    t = 5 if g < X0 + (X1 - X0) * 0.7 else 4          # the lit nosing
                elif r < max(1, tread // 3):
                    t = 3                                            # the back, under the step above
                else:
                    t = 4
                if g == X0:
                    t = min(5, t + 1)                                # lit west end
                elif g == X1 - 1:
                    t = max(2, t - 1)                                # shaded east end
                c = C(fam, t)
                if g == joints[i] and r < tread - 1:
                    c = C(fam, 2)
                if FIXT and D > 1:
                    # r6: wear: the nosing chipped in a few places, the middle of each tread worn
                    # a touch lighter where feet go, a few grit specks in the back corner
                    hq = ((int(g / D) * 2654435761) ^ (i * 40503) ^ (seed * 977)) & 0xff
                    wc, ww, wh = wear[i]
                    ragged = ((((r * 2654435761) ^ wh) >> 5) % 3) - 1     # the patch's ends wander a px per row
                    mid = abs(g - wc) < ww + ragged
                    if r == tread - 1 and hq % 9 == 0:
                        c = C('crag', 1)                                 # a chip out of the nosing
                    elif mid and 0 < r < tread - 1 and t == 4:
                        c = C(fam, 5) if fam == 'path' else C('path', 4)
                    elif r < max(1, tread // 3) and hq % 13 == 1:
                        c = C('earth', 2)
            else:
                c = C('crag', 0) if r == hgt - 1 else C('crag', 1 if g < X1 - P(3) else 0)
                if g == joints[i]:
                    c = C('crag', 0)
            out[y, x] = c
    return out
