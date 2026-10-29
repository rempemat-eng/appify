"""World plan v5.3's block-out, v55: the continent with room for its towns (Matt's brief of 27 Oct, layout steps 1 to 4).

Matt: "keep v54's overall geography, enlarge the usable world by roughly 20%, and give its settlements substantially more
space and everyday activity. The expansion should follow the places that need room, especially Neon Harbour, rather than
stretch every distance equally."

How v55 is made (README.md, "v55"):
1. v54's ground is built exactly as before, in v54's coordinates (geo52's land, rivers, routes, settlements; geo53's
   craters; the obstacles, pockets, mixing bands and borders).
2. It is then stretched onto the v55 canvas by a separable, piecewise-linear warp that only ever widens (STRETCH_X,
   STRETCH_Y): the home valley, the Frostline, the woodland and Crossroads keep their coordinates exactly; the land east of
   the Fern hills widens, Neon Harbour's coast most; the south coast's band (the halt, Driftwood, Lullford, Hearthold,
   Gullwick, Cinderwick, Launch Cape) grows south; the Sunstone basin and the fire country widen west; the massif deepens
   north. The far west of the dune sea and the top of the ice cap (past the walk) run off the canvas.
3. On the v55 canvas: the settlement footprints at the agreed building counts (towns.py), Neon Harbour's five districts and
   inhabited outskirts with the east coast and Launch Cape as a full headland, the mountain valley town (Highgarth) and the
   closed pass to its rockfall, and the roads, rivers and land use fitted round them.
4. The analysis (content, markers, the gate check with the closed pass, walk times, tiers, the benchmark) runs on the v55
   canvas, and the JSON is written in v55's world px.

Run from this folder:  python3 -I geo55.py              (data and every map)
                       RENDER_ONLY=1 python3 -I geo55.py (the maps again from out/state-v55.pkl)
                       QUICK=data python3 -I geo55.py   (the JSON and the state only)
It writes blockout-v55.json, stats-v55.json and gates-v55.json next to itself (committed) and the renders to out/ (or
$BLOCKOUT_OUT); MAP55_OUT, if set, also receives the maps. Needs geo54.py, geo53.py, geo52.py and geo5.py beside it."""
import json, math, os, pickle, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage as ndi
import geo5 as g
import geo52 as G
import geo53 as V
import geo54 as V54
import towns55
from geo5 import chaikin, densify

DATA, HERE, ROOT = V.DATA, V.HERE, V.ROOT
REVISION = os.environ.get('MYGAME_MAP_REVISION', 'v55')
if REVISION not in ('v55', 'v56'):
    raise ValueError('MYGAME_MAP_REVISION must be v55 or v56')
SUF = '-' + REVISION
PLAN_DIRECTORY = 'towns-v56' if REVISION == 'v56' else 'towns'
# v56 is a new prospective run, not a reconstruction of the lost v55 process seed.
PROSPECTIVE_SEED = 'crc32-utf8/355; explicit town seeds retained'
NEW_KINDS = {'lane': '#CDB894', 'fence': '#5A4E44', 'rockfall': '#8A8078', 'closedroad': '#B7A88A', 'pad': '#C9C6C0'}
g.COL.update(NEW_KINDS)
g.WALK |= {'lane', 'quay', 'boulevard', 'apron', 'pad', 'arcade'}

# ------------------------------------------------------------------------------------------ the warp (v54 px -> v55 px)
OLD_W, OLD_H = g.WPX, g.HPX                       # 11264 x 6912
NEW_W, NEW_H = 12544, 7168                        # 49 x 28 tiles of 256 px
# (from, to, slope): each band of v54's x (or y) is widened by its slope; slope 1 keeps the band's size. The anchor bands
# (x 5400 to 7000, y 1400 to 3900) keep their coordinates, so the home valley, the woodland, Crossroads and the Frostline
# are where every plan has them.
STRETCH_X = {'down': [(4300, 1.06), (1500, 1.14), (-2e4, 1.0)], 'up': [(8400, 1.10), (9400, 1.06), (OLD_W, None), (OLD_W + 2e4, 1.0)]}
STRETCH_Y = {'down': [(300, 1.20), (-2e4, 1.0)], 'up': [(5950, None), (OLD_H + 2e4, 1.0)]}
ANCHOR_X, ANCHOR_Y = (5400, 7000), (1400, 3900)
WHY_STRETCH = {
    'x 9400 to 11264 (Neon Harbour, the ria, Launch Cape, the fens)': 'the city, its outskirts, its east coast and the cape: the most room',
    'x 7000 to 8400 (Fernhollow, Cogsworth, the Lull plain)': "two town footprints and the Lull plain's farms",
    'x 8400 to 9400 (the Narrows, the meander belt, Lullford)': 'a little: the river corridor and the delta',
    'x 1500 to 4300 (the Sunstone basin, Dust Gulch, Palm Spring, Hearthold, Cinderwick)': 'the desert and fire country towns and their settled margins',
    'x 4300 to 5400 (the Rift, the steppe, the Brackens)': "a little: the steppe's transition and the Rift's bays",
    'y 3900 to 5950 (the south: the halt, Driftwood, Lullford, Hearthold, Gullwick, Cinderwick, Launch Cape)': 'the coast band and its towns',
    'y 300 to 1400 (the massif)': 'the mountain valley town and the approach to the closed pass',
}


def _knots(st, anchor, old_max, new_max):
    """Knots (old, new) of a piecewise-linear map: the anchor band keeps its coordinates; each band outward is widened
    by its slope; the band with slope None takes whatever brings old_max to new_max."""
    lo, hi = anchor
    pts = [(lo, lo), (hi, hi)]
    xo, xn = lo, lo
    for b, s in st['down']:
        xn -= (xo - b) * s; xo = b; pts.insert(0, (xo, xn))
    up = st['up']; fixed = sum((min(b, old_max) - a) * s for (a, (b, s)) in zip([hi] + [u[0] for u in up], up) if s and a < old_max)
    xo, xn = hi, hi
    for b, s in up:
        if s is None:
            s = (new_max - hi - fixed) / (b - xo)
        xn += (b - xo) * s; xo = b; pts.append((xo, xn))
    return np.array([p[0] for p in pts], float), np.array([p[1] for p in pts], float)


KX = _knots(STRETCH_X, ANCHOR_X, OLD_W, NEW_W)
KY = _knots(STRETCH_Y, ANCHOR_Y, OLD_H, NEW_H)


def fx(x):
    return np.interp(x, KX[0], KX[1])


def fy(y):
    return np.interp(y, KY[0], KY[1])


def ifx(X):
    return np.interp(X, KX[1], KX[0])


def ify(Y):
    return np.interp(Y, KY[1], KY[0])


def sx(x):
    """The x stretch (slope) at v54's x."""
    i = int(np.clip(np.searchsorted(KX[0], x) - 1, 0, len(KX[0]) - 2))
    return float((KX[1][i + 1] - KX[1][i]) / (KX[0][i + 1] - KX[0][i]))


def sy(y):
    i = int(np.clip(np.searchsorted(KY[0], y) - 1, 0, len(KY[0]) - 2))
    return float((KY[1][i + 1] - KY[1][i]) / (KY[0][i + 1] - KY[0][i]))


def P(p):
    """A v54 point in v55 world px."""
    return (float(fx(p[0])), float(fy(p[1])))


def Pr(p):
    return (int(round(fx(p[0]))), int(round(fy(p[1]))))


def PL(pts):
    return [P(p) for p in pts]


def Pbox(b):
    x0, y0, x1, y1 = b
    return (int(round(fx(x0))), int(round(fy(y0))), int(round(fx(x1))), int(round(fy(y1))))


def warp_table():
    """The knots as a table for the README and the JSON."""
    return {'x': [[round(float(a)), round(float(b))] for a, b in zip(*KX)], 'y': [[round(float(a)), round(float(b))] for a, b in zip(*KY)],
            'old_world_px': [OLD_W, OLD_H], 'new_world_px': [NEW_W, NEW_H], 'anchor_x': list(ANCHOR_X), 'anchor_y': list(ANCHOR_Y),
            'why': WHY_STRETCH,
            'how_to_move_a_point': 'piecewise linear in x and in y separately (np.interp over the knots); boxes by their corners'}


# ------------------------------------------------------------------------------------------ stage 1: v54's ground, as built
def stage_old():
    """geo53.data_stage's ground, in v54's coordinates: the land, routes, settlements, craters, obstacles, pockets, mixing
    bands, the frame and the borders. (Content, markers and the analysis run after the warp, on the v55 canvas.)"""
    from geo5 import noise, PX, PY
    T = G.build51(); g.routes(T); g.settle(T)
    V.craters(T)
    obs = G.obstacles(T); pocks = G.pockets(T); G.mixing_bands(T)
    g.FRAME = ndi.distance_transform_edt(~T['used']) * g.CELL > (g.FRAME_PX + 200 * noise(500, 70) + 45 * noise(90, 71, 2) + 16 * noise(30, 72, 2) + 12 * noise(16, 73, 1))
    jit = 30 * noise(60, 604, 2) + 12 * noise(16, 605, 1)
    g.FRAME &= ~((PX > 9500 + 120 * noise(400, 600) + jit) & (PY > 4200 + 120 * noise(400, 601) + jit) & (PY < 5500 + 120 * noise(400, 602) + jit) & (PX < 11200 + 60 * noise(400, 603) + jit))
    G.borders(T)
    T['FRAME'] = g.FRAME
    return T, obs, pocks


# ------------------------------------------------------------------------------------------ stage 2: the warp
def grid_index():
    """For every v55 cell, the v54 cell it samples (nearest), and the fractional v54 cell coordinates (for linear fields)."""
    Wn, Hn = NEW_W // g.CELL, NEW_H // g.CELL
    Xc = (np.arange(Wn) + 0.5) * g.CELL; Yc = (np.arange(Hn) + 0.5) * g.CELL
    ox, oy = ifx(Xc), ify(Yc)
    ix = np.clip((ox // g.CELL).astype(int), 0, OLD_W // g.CELL - 1); iy = np.clip((oy // g.CELL).astype(int), 0, OLD_H // g.CELL - 1)
    fxc = np.clip(ox / g.CELL - 0.5, 0, OLD_W // g.CELL - 1); fyc = np.clip(oy / g.CELL - 0.5, 0, OLD_H // g.CELL - 1)
    return ix, iy, fxc, fyc


def warp_arr(A, idx):
    ix, iy, fxc, fyc = idx
    if A.dtype.kind == 'f':
        return ndi.map_coordinates(A, np.meshgrid(fyc, fxc, indexing='ij'), order=1, mode='nearest').astype(A.dtype)
    return A[iy[:, None], ix[None, :]]


def warp_any(v, idx, shape):
    if isinstance(v, np.ndarray) and v.shape == shape:
        return warp_arr(v, idx)
    if isinstance(v, dict):
        return {k: warp_any(x, idx, shape) for k, x in v.items()}
    return v


def set_dims(Wpx, Hpx):
    """Point geo5, geo52, geo53, map53 and map54 at a canvas of Wpx x Hpx world px."""
    W_, H_ = Wpx // g.CELL, Hpx // g.CELL
    yy, xx = np.mgrid[0:H_, 0:W_]
    vals = {'WPX': Wpx, 'HPX': Hpx, 'W': W_, 'H': H_, 'xx': xx, 'yy': yy, 'PX': xx * g.CELL + g.CELL / 2.0, 'PY': yy * g.CELL + g.CELL / 2.0}
    mods = [g, G, V, V54] + [sys.modules[m] for m in ('map53', 'map54', 'map55', 'towns55') if m in sys.modules]
    for m in mods:
        for k_, v in vals.items():
            if hasattr(m, k_):
                setattr(m, k_, v)
    g.NOISE_CACHE.clear()
    g.WARP = (vals['PX'], vals['PY'])


def warp_T(T, obs, pocks):
    """T onto the v55 canvas: every field resampled (nearest for kinds and masks, linear for heights and wetness), every
    line and point moved by the warp."""
    shape = T['K'].shape
    idx = grid_index()
    out = {}
    for k_, v in T.items():
        out[k_] = warp_any(v, idx, shape)
    for k_ in ('route_px', 'river_px'):
        out[k_] = {nm: PL(pts) for nm, pts in T[k_].items()}
    out['delta'] = [PL(pts) for pts in T['delta']]
    out['flows'] = [PL(pts) for pts in T.get('flows', [])]
    out['oxbows'] = [(kind, *Pr((x, y))) for kind, x, y in T['oxbows']]
    out['huts'] = [(lab, *P((x, y))) for lab, x, y in T['huts']]
    out['crossings'] = [dict(c, x=Pr((c['x'], c['y']))[0], y=Pr((c['x'], c['y']))[1]) for c in T['crossings']]
    cr = {}
    for nm, c in T['craters'].items():
        c = dict(c); c['x'], c['y'] = Pr((c['x'], c['y']))
        if 'scorch_tip' in c:
            c['scorch_tip'] = list(Pr(c['scorch_tip']))
        cr[nm] = c
    out['craters'] = cr
    obs2 = []
    for o in obs:
        o = dict(o); x, y = Pr((o['x'], o['y'])); o['x'], o['y'] = x, y
        if 'along' in o:
            o['along'] = float(o['along']) * math.sqrt(sx(o['x']) * sy(o['y']))
        obs2.append(o)
    pocks2 = [dict(p, x=Pr((p['x'], p['y']))[0], y=Pr((p['x'], p['y']))[1]) for p in pocks]
    out['obstacles'] = obs2; out['pockets'] = pocks2
    out['mixing'] = T['mixing']
    return out, obs2, pocks2


def warp_tables():
    """Every table of places and boxes, moved onto the v55 canvas (in place)."""
    r_ = lambda x, y, r: r * math.sqrt(sx(x) * sy(y))
    g.SETTLE.update({nm: (*Pr((x, y)), int(round(r_(x, y, r))), k) for nm, (x, y, r, k) in g.SETTLE.items()})
    g.STATIONS.update({nm: Pr(p) for nm, p in g.STATIONS.items()})
    g.BRIDGES.update({nm: (*Pr((v[0], v[1])), *v[2:]) for nm, v in g.BRIDGES.items()})
    g.EGGS.update({nm: Pr(p) for nm, p in g.EGGS.items()})
    g.HOME = Pr(g.HOME); g.VOLCANO = Pr(g.VOLCANO)
    for w, discs in list(g.WAYS.items()):
        g.WAYS[w] = [(*P((x, y)), r * max(sx(x), sy(y))) for x, y, r in discs]
    g.BEHIND.update({w: [t if isinstance(t, str) else Pr(t) for t in v] for w, v in g.BEHIND.items()})
    g.SHORTCUTS[:] = [(a, b, c, d, e, PL(via)) for a, b, c, d, e, via in g.SHORTCUTS]
    g.ROUTES.update({nm: (PL(pts), kind, feats) for nm, (pts, kind, feats) in g.ROUTES.items()})
    G.THRESHOLDS.update({nm: Pr(p) for nm, p in G.THRESHOLDS.items()})
    G.LIFTS.update({nm: [Pr(p) for p in v] for nm, v in G.LIFTS.items()})
    G.TLANDMARK.update({nm: (a, *Pr((x, y))) for nm, (a, x, y) in G.TLANDMARK.items()})
    for tab in (G.REGIONS, G.BIOMES, G.CROPS, G.BOUNDARY_CROPS):
        for nm, b in list(tab.items()):
            x0, y0, x1, y1 = Pbox(b)
            x1 = NEW_W if b[2] >= OLD_W else x1; y1 = NEW_H if b[3] >= OLD_H else y1
            x0 = 0 if b[0] <= 0 else x0; y0 = 0 if b[1] <= 0 else y0
            tab[nm] = (x0, y0, x1, y1)
    V.CIRCLE = Pr(V.CIRCLE); V.CROSSROADS = Pr(V.CROSSROADS)
    V.CRATERS.update({nm: (*Pr((x, y)), r, reg, st) for nm, (x, y, r, reg, st) in V.CRATERS.items()})
    V.POI53.update({nm: (*Pr((x, y)), k, why) for nm, (x, y, k, why) in V.POI53.items()})
    V.WAYSTONES.update({nm: (*Pr((x, y)), s_) for nm, (x, y, s_) in V.WAYSTONES.items()})
    V.BUILT.update({nm: Pbox(b) for nm, b in V.BUILT.items()})
    V.ACT1[:] = [(nm, Pr(p), what) for nm, p, what in V.ACT1]
    V54.PEAK_NAMES[:] = [(int(round(fx(x))), nm) for x, nm in V54.PEAK_NAMES]
    V54.PASSES.update({nm: (*Pr((x, y)), *rest) for nm, (x, y, *rest) in V54.PASSES.items()})
    V54.GLACIERS.update({nm: (*Pr((x, y)), why) for nm, (x, y, why) in V54.GLACIERS.items()})
    V54.BUTTES.update({nm: (*Pr((x, y)), r) for nm, (x, y, r) in V54.BUTTES.items()})
    V54.SALT_FLATS.update({nm: (*Pr((x, y)), int(rx * sx(x)), int(ry * sy(y))) for nm, (x, y, rx, ry) in V54.SALT_FLATS.items()})
    V54.DRY_BEDS.update({nm: [Pr(p) for p in pts] for nm, pts in V54.DRY_BEDS.items()})
    V54.INSET = Pbox(V54.INSET)
    for nm in list(V.NEW_ROUTES):
        pts, kind, feats = V.NEW_ROUTES[nm]; V.NEW_ROUTES[nm] = (PL(pts), kind, feats)


# ------------------------------------------------------------------------------------------ stage 3a: the east coast and Launch Cape
# The coast east of the city (v55 world px): the open sea comes in along the city's east side from the canvas edge at the
# fens' foot, and the shore runs on round Launch Cape, now a full headland, back to the ria's mouth.
EAST_SHORE = [(12544, 4230), (12470, 4370), (12400, 4560), (12370, 4800), (12390, 5000), (12420, 5170), (12390, 5370), (12350, 5560),
              (12370, 5800), (12350, 6060), (12300, 6300), (12220, 6510), (12110, 6660)]
CAPE_WEST = [(12110, 6660), (11990, 6640), (11900, 6500), (11860, 6290), (11810, 6080), (11720, 5900), (11620, 5790)]
CITY_KINDS = {'building', 'warehouse', 'tower', 'neon', 'plaza', 'boulevard', 'arcade', 'lane', 'quay', 'terminal', 'hangar', 'apron', 'airfield',
              'retain', 'keep', 'fishmarket', 'stall', 'crane', 'pier', 'dock', 'pad', 'yard', 'garden'}
CITY_BOX = (9700, 4050, 12544, 5900)


def _poly_mask(pts):
    from skimage.draw import polygon as skpoly
    rr, cc = skpoly([p[1] / g.CELL for p in pts], [p[0] / g.CELL for p in pts], shape=(g.H, g.W))
    m = np.zeros((g.H, g.W), bool); m[rr, cc] = True
    return m


def _jitter(m, amp, seed, scale=200):
    """A mask's edge pushed in and out by noise, so a drawn line becomes a shore."""
    din = ndi.distance_transform_edt(m) * g.CELL; dout = ndi.distance_transform_edt(~m) * g.CELL
    sd = np.where(m, din, -dout)
    return sd + amp * g.noise(scale, seed) + 0.4 * amp * g.noise(scale / 3, seed + 1, 2) > 0


def east_coast(T):
    """The sea east of EAST_SHORE; Launch Cape's headland between CAPE_WEST and EAST_SHORE south of the old coast."""
    K, land = T['K'], T['land']; PX, PY = g.PX, g.PY
    east = _poly_mask([(12544, 4100)] + EAST_SHORE + [(12544, 7168)])
    east = _jitter(east, 40, 5501) & (PY > 4180)
    cape = _poly_mask(CAPE_WEST + EAST_SHORE[::-1][:8] + [(11500, 5600), (11500, 5790)])
    cape = _jitter(cape, 46, 5502) & ~east
    new_land = cape & ~land
    new_sea = east & land
    land = (land & ~east) | cape
    lab, n = ndi.label(land); sizes = ndi.sum(land, lab, range(1, n + 1))
    land &= np.isin(lab, 1 + np.nonzero(sizes >= 40)[0])
    T['land'] = land; T['sea'] = ~land; T['barriers']['sea'] = T['sea']
    K[new_sea] = 'sea'
    # the headland: a low spine of heath and short turf, cliffs on the open east shore, a beach on the sheltered west
    spine = chaikin([(11700, 5800), (11950, 6050), (12080, 6330), (12110, 6560)], 2)
    d_sp = g.raster(spine)[0]
    h0 = 0.10 + 0.13 * np.exp(-(d_sp / 260) ** 2) + 0.02 * g.noise(200, 5503)
    T['h'] = np.where(new_land, h0, T['h']); T['wet'] = np.where(new_land, 0.55, T['wet'])
    K[new_land] = np.where(g.noise(160, 5504)[new_land] > 0.15, 'heath', 'meadow')
    dsea = ndi.distance_transform_edt(land) * g.CELL
    shore = land & (dsea < 30 + 18 * (g.noise(120, 5505) + 1)) & ((PX > 11600) & (PY > 4200))
    eastside = (PX > np.interp(PY, [p[1] for p in EAST_SHORE], [p[0] for p in EAST_SHORE]) - 140) & (PY > 5650)
    K[shore & eastside & ~np.isin(K, ['road', 'path', 'bridge'])] = 'cliff'
    K[shore & ~eastside & ~np.isin(K, ['road', 'path', 'bridge', 'cliff'])] = 'sand'
    dl = ndi.distance_transform_edt(~land) * g.CELL
    rnd = np.random.default_rng(5506).random((g.H, g.W))
    K[~land & (dl < 14 + 10 * g.noise(60, 505)) & (rnd < 0.7) & (PX > 11400) & (PY > 4150)] = 'surf'
    T['used'] &= land
    return {'new_land_cells': int(new_land.sum()), 'new_sea_cells': int(new_sea.sum())}


def clear_city(T):
    """Neon Harbour's v52 districts lifted off the ground (the routes, rivers, canal and falls stay), so v55's five districts
    can be laid on the wider canvas."""
    K = T['K']; K0 = T['K0']
    x0, y0, x1, y1 = CITY_BOX
    a, b = int(y0 // g.CELL), int(x0 // g.CELL); c, d = int(y1 // g.CELL), int(x1 // g.CELL)
    sub = K[a:c, b:d]; base = K0[a:c, b:d]
    m = (np.isin(sub, list(CITY_KINDS)) | (np.isin(sub, ['road', 'path']) & ~T['used_routes'][a:c, b:d])) & T['land'][a:c, b:d]
    nat = np.where(np.isin(base, ['sea', 'river', 'canal', 'road', 'path', 'bridge', 'stair']), 'meadow', base)
    nat = np.where(np.isin(nat, ['wild', 'ancient', 'thicket', 'felltree']), 'broadleaf', nat)
    sub[m] = nat[m]
    sub[np.isin(sub, ['pier']) & ~T['land'][a:c, b:d]] = 'sea'
    T['used'][a:c, b:d] &= ~m
    return int(m.sum())


# ------------------------------------------------------------------------------------------ stage 3c: the mountain valley town
# Highgarth: a sheltered valley on the upper Cog, inside the range north of Cogsworth. Slate quarries and summer pastures,
# a drovers' inn and a sawmill; it sends slate, timber and wool down the Garth Road to Cogsworth. The Northway climbs from
# it to the head of the valley, where a rockfall closes the old pass (since the Starfall); the road goes on beyond it, over
# the col to the land north of the range (a later region). The pass is closed for movement, navigation and travel.
HIGHGARTH = (7905, 1190)
GARTH_ROAD = [(8045, 2372), (8010, 2200), (7990, 2030), (7960, 1860), (7915, 1690), (7880, 1520), (7885, 1360), (7905, 1250)]
NORTHWAY_OPEN = [(7925, 1090), (7905, 960), (7880, 830), (7850, 700), (7825, 600)]
ROCKFALL = (7815, 545)
ROCKFALL_LINE = [(7480, 580), (7700, 556), (7815, 545), (8000, 530), (8300, 508)]   # the slide across the valley's head, wall to wall
NORTHWAY_CLOSED = [(7812, 515), (7795, 400), (7775, 280), (7752, 160), (7740, 40), (7736, -10)]
HIGHGARTH_PASS = (7742, 70)                     # the col at the head of the valley, under the cloud bank
NEON_INSET = (9600, 3850, 12544, 6800)          # the Neon Harbour inset's box (world px): the city, its outskirts, the east coast, the cape
VALLEY_FLOOR = [(7820, 820), (7880, 1050), (7895, 1250), (7860, 1480)]
SNOW_PEAKS = [(7380, 760, 150, 0.26), (8300, 640, 160, 0.27), (8090, 300, 140, 0.24), (7420, 300, 140, 0.25), (7620, 110, 120, 0.2)]


def highgarth_valley(T):
    """Open the upper Cog's valley floor for a town (lower, cleared, pasture and terraced fields), its slopes steep and wooded,
    snow on the peaks round it."""
    K = T['K']; h = T['h']; PX, PY = g.PX, g.PY
    floor = (g.capsule(VALLEY_FLOOR, 230, 200, 5511, 0.5) | g.shape(7930, 1220, 260, 200, 5515, 0.45) | g.shape(7880, 1480, 200, 150, 5516, 0.5)) & T['land']
    d_f = ndi.distance_transform_edt(~floor) * g.CELL
    hf = 0.43 + 0.012 * g.noise(120, 5512)
    blend = np.exp(-(d_f / 170) ** 2)
    h2 = np.where(floor, np.minimum(h, hf), h - (h - hf) * blend * (h > hf))
    for (px_, py_, r, a) in SNOW_PEAKS:
        h2 = h2 + a * np.exp(-((PX - px_) ** 2 + (PY - py_) ** 2) / r ** 2) * (1 + 0.25 * g.ridged(90, 5513))
    T['h'] = h2
    water = np.isin(K, ['river', 'creek', 'rapids', 'tarn'])
    woods = ['wild', 'ancient', 'thicket', 'felltree', 'broadleaf', 'conifer', 'scree', 'boulders', 'cliff', 'crag', 'alpine', 'barren']
    open_ = floor & ~water & np.isin(K, woods)
    K[open_] = np.where(g.noise(90, 5514)[open_] > 0.25, 'alpine', 'meadow')
    far = np.hypot(PX - HIGHGARTH[0], PY - HIGHGARTH[1]) > 260
    K[open_ & far & (g.noise(140, 5517) + 0.5 * g.noise(50, 5518, 2) > 0.45)] = 'conifer'      # stands of larch left on the floor
    slopes = (d_f > 0) & (d_f < 420) & ~water & np.isin(K, ['wild', 'ancient', 'broadleaf', 'thicket'])
    K[slopes] = 'conifer'
    near = (PX > 7100) & (PX < 8600) & (PY < 1700) & T['land'] & ~water & np.isin(K, woods + ['snow'])
    K[near & (h2 > 0.86)] = 'snow'
    K[near & (h2 > 0.74) & (h2 <= 0.86)] = 'scree'
    T['highgarth_floor'] = floor
    return floor


# ------------------------------------------------------------------------------------------ the old forest (Matt, 28 Oct)
FOREST_TRAIL = [(8300, 2744), (8420, 2620), (8470, 2470), (8500, 2330), (8560, 2150), (8660, 2010), (8720, 1960), (8800, 1830), (8830, 1760)]
FOREST_LAKE_BRANCH = [(8560, 2150), (8700, 2190), (8830, 2230)]
FOREST_CAMP_BRANCH = [(8420, 2620), (8540, 2660), (8650, 2670)]
FOREST_PLACES = {   # name: (x, y, clearing radius px, what, tier on the overview: 2 named, 3 reference only)
    'the Elder Oak': (8720, 1960, 96, "a colossal ancient oak in its clearing, ringed by mossy standing stones: kin of the circle, a waystone among them", 2),
    "the moon-watchers' observatory": (8830, 1750, 72, "the circle-builders' overgrown moon observatory, half sunk in the trees: older than every town", 2),
    "the Company's timber camp": (8660, 2680, 110, "the Company eating into the forest's south edge: felled ground, a log flume to the river, a rail spur to the Cogsworth line", 2),
    'Charcoal Hollow': (8470, 2440, 70, "the foresters' and charcoal burners' hamlet in its clearing", 2),
    'Fernmere': (8860, 2240, 60, 'the forest lake: a boardwalk runs from it into the moss fens; a reed hide on its shore', 3),
    'the hidden glade': (8350, 2000, 40, 'a glade off the trail, through a gap in the trees, for those who look', 3),
    'the fern glade': (8790, 2470, 36, 'a second hidden glade, deep in the wood', 3),
}


def old_forest(T):
    """The old forest north-east of Cogsworth gets things to see (Matt, 28 Oct): uneven density (open woods and clearings in the
    deep canopy), a trail from the Towpath to its places, the Elder Oak and its stones, the moon observatory, the Company's timber
    camp on its south edge with its log flume and rail spur, Charcoal Hollow, the forest lake with its boardwalk and reed hide,
    and two hidden glades. Returns the places for the plan, the labels and the map."""
    K = T['K']
    box = (g.PX > 8180) & (g.PX < 9000) & (g.PY > 1640) & (g.PY < 2900) & ~ndi.binary_dilation(T['FRAME'], iterations=3)
    wild = box & np.isin(K, ['wild', 'ancient'])
    nz = g.noise(140, 7101)
    K[wild & (nz > 0.15)] = 'broadleaf'                              # uneven density: open woods through the deep canopy
    K[wild & (nz > 0.62)] = 'clearing'
    for nm, (x, y, r, what, tier) in FOREST_PLACES.items():
        m = g.shape(x, y, r, r * 0.8, 7110 + len(nm), 0.18) & box & ~np.isin(K, ['river', 'creek', 'canal', 'road', 'path', 'bridge'])
        K[m] = 'clearing' if nm != "the Company's timber camp" else 'fallow'
    add_route(T, 'the Old Forest Trail', FOREST_TRAIL, 'path')
    add_route(T, 'the Fernmere path', FOREST_LAKE_BRANCH, 'path')
    add_route(T, 'the camp track', FOREST_CAMP_BRANCH, 'path')
    for (x, y) in ((8350, 2000), (8790, 2470)):                     # the gaps in the trees to the hidden glades
        p = np.asarray(T['route_px']['the Old Forest Trail'], float); i = int(np.argmin(np.hypot(p[:, 0] - x, p[:, 1] - y)))
        gap = G._orig_line_mask([(p[i, 0], p[i, 1]), (x, y)], 16) & box & np.isin(K, ['wild', 'ancient', 'broadleaf', 'conifer', 'thicket'])
        K[gap] = 'broadleaf'
    # the Elder Oak's standing stones; the lake, its reeds and boardwalk
    ox, oy = FOREST_PLACES['the Elder Oak'][:2]
    stones = [(ox + 64 * math.cos(a), oy + 52 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    for (x, y) in stones:
        K[int(y // g.CELL), int(x // g.CELL)] = 'tor'
    lx, ly = FOREST_PLACES['Fernmere'][:2]
    lake = g.shape(lx, ly, 44, 32, 7120, 0.2) & box
    reeds = ndi.binary_dilation(lake, iterations=2) & ~lake & box & ~np.isin(K, ['path', 'road', 'bridge'])
    K[reeds] = 'reeds'; K[lake] = 'mere'
    bw = G._orig_line_mask([(lx + 20, ly), (9000, ly + 10)], 12) & ~ndi.binary_dilation(T['FRAME'], iterations=3) & ~lake
    K[bw & ~np.isin(K, ['path', 'road'])] = 'bridge'
    places = {nm: {'xy_px': [x, y], 'what': what, 'tier': tier} for nm, (x, y, r, what, tier) in FOREST_PLACES.items()}
    feats = {'standing_stones_px': [[int(x), int(y)] for x, y in stones],
             'boardwalk_px': [[lx + 20, ly], [9000, ly + 10], [9380, ly + 40]], 'reed_hide_px': [lx + 52, ly - 30],
             'log_flume_px': [[8640, 2660], [8480, 2650], [8300, 2630], [8210, 2620]],
             'rail_spur_px': [[8680, 2720], [8600, 2780], [8460, 2810], [8380, 2810]],
             'camp_sheds_px': [[8620, 2650, 56, 32], [8690, 2640, 48, 32], [8660, 2700, 64, 32]]}
    for (x, y, w, h) in feats['camp_sheds_px']:
        a, b = int(y // g.CELL), int(x // g.CELL)
        sub = K[a:a + h // g.CELL, b:b + w // g.CELL]; sub[np.isin(sub, ['fallow', 'clearing', 'broadleaf', 'wild', 'conifer'])] = 'building'
    V.WAYSTONES['the Elder Oak'] = (ox + 4, oy + 36, 'proposed')
    T['forest'] = {'places': places, 'features': feats}
    return T['forest']


def add_route(T, name, pts, kind='path', feats=(), wiggle=True, seed=None):
    """A v55 route painted as geo5's routes are (a meandering line, bridges over small water); it may cross no barrier."""
    import zlib
    K = T['K']
    sm = g.meander(pts, 18, (seed or zlib.crc32(name.encode())) % 1000, 140) if wiggle else chaikin(pts, 2)
    width = {'road': 40, 'path': 24}[kind]
    rmask = G._orig_line_mask(sm, width)
    for bname, bm in T['barriers'].items():
        if (rmask & bm).any():
            raise ValueError(f'{name} crosses {bname}')
    water = rmask & np.isin(K, ['river', 'rapids', 'creek', 'canal', 'oxbow', 'tarn', 'mere', 'channel'])
    K[water] = 'bridge'
    K[rmask & ~water & ~np.isin(K, ['bridge', 'bar', 'stair', 'road'])] = kind
    T['route_px'][name] = sm; g.ROUTES[name] = (pts, kind, list(feats))
    T['used'] |= rmask; T['used_routes'] |= rmask
    if name not in G.MAIN_ROUTES:
        G.MAIN_ROUTES.append(name)
    return sm


def closed_pass(T):
    """The Northway's closed part: a rockfall across the road at the valley's head (never walkable), the road beyond it to
    the col drawn but not walkable, and no waystone, station or shortcut past it."""
    K = T['K']
    rf = (g.shape(ROCKFALL[0], ROCKFALL[1], 70, 46, 5521, 0.35) | G._orig_line_mask(ROCKFALL_LINE, 64)) & T['land']
    rf &= ~np.isin(K, ['river', 'rapids', 'creek'])
    K[rf] = 'rockfall'
    sm = chaikin(NORTHWAY_CLOSED, 2)
    cm = G._orig_line_mask(sm, 24) & T['land'] & ~rf
    K[cm & ~np.isin(K, ['river', 'rockfall'])] = 'closedroad'
    T['route_px']['the Northway (closed)'] = sm
    T['closed_mask'] = rf | cm
    return sm


def unframe(T, mask, pad=260):
    """Take the frame off a newly walked area (and its surroundings, pad px), so its borders can be drawn round it."""
    near = ndi.distance_transform_edt(~mask) * g.CELL < pad + 60 * g.noise(160, 5531) + 20 * g.noise(40, 5532, 2)
    T['FRAME'] &= ~(near & T['land'])
    g.FRAME = T['FRAME']


def reborder(T, region):
    """geo52's borders (the fade, the wall and the far clumps, by the ground's own blockers) round the walk inside region,
    run on a copy and merged back only inside it."""
    import copy
    T2 = dict(T); T2['K'] = T['K'].copy()
    fr0 = T['FRAME'].copy(); g.FRAME = T['FRAME'].copy()
    G.borders(T2)
    m = region
    T['K'][m] = T2['K'][m]
    for k_ in ('border_s1', 'border_s2', 'border_assigned', 'fade_clumps'):
        T[k_] = np.where(m, T2[k_], T[k_])
    T['FRAME'] = np.where(m, g.FRAME, fr0)
    g.FRAME = T['FRAME']


# ------------------------------------------------------------------------------------------ stage 3d: the land between the towns
PAD = (12085, 6455)                               # Launch Cape's pad, at the headland's tip
PAD_ROAD = [(12095, 5722), (12030, 5880), (12010, 6040), (12040, 6230), (12070, 6380)]
# the central green: farmsteads in the Lull plain and the valley's south, each a farmhouse, a barn, an orchard and fields
FARMS = [(6900, 4300, 'Hollins farm'), (7250, 4120, 'Sedge farm'), (7650, 4300, 'Brook farm'), (7350, 4650, 'Dale farm'), (8000, 4450, 'Wheatley'),
         (7700, 4900, 'Long Acre'), (8350, 4600, 'Ferry farm'), (6750, 4750, 'Coombe farm'), (5900, 4500, 'Halt farm'), (7580, 3720, 'Lane End')]
WINDMILLS = [(7480, 4420, 'Brook mill'), (8150, 4250, 'Wheatley mill'), (6980, 4560, 'Coombe mill')]
COPSES = [(7120, 4420, 120), (7820, 4600, 90), (8250, 4900, 110), (6850, 4980, 80), (7480, 4060, 70), (8550, 4420, 80), (6080, 4380, 90)]
TERRACES = {'the Lull terraces': [(8560, 3980), (8520, 4250), (8600, 4550), (8700, 4850)]}   # river terraces stepped up from the Lull's west bank


def central_green(T, TW):
    """Give the Lull plain and the valley's south a farmed identity: farmsteads with orchards and hedged fields, windmills on
    the rises, small woods, and river terraces stepping up from the Lull; open meadow left between."""
    K = T['K']; out = []
    for i, (x, y, nm) in enumerate(FARMS):
        t = TW.Town(T, nm, (x, y), 'farmstead', (2, 3), 'a farm of the central green', 'the Lull plain', seed=400 + i)
        t.cluster(x, y, 60, ['farmhouse', 'barn'], 2, plot=(40, 'yard'))
        t.fields(x - 110, y - 90, x + 110, y + 70, ('orchard',), hedge=False, size=(64, 96), p=0.7)
        t.fields(x - 280, y - 220, x + 280, y + 220, ('field', 'field2', 'fallow'), size=(112, 208), p=0.45)
        out.append(t)
    for i, (x, y, nm) in enumerate(WINDMILLS):
        t = TW.Town(T, nm, (x, y), 'mill', (1, 1), 'a windmill on a rise of the plain', 'the Lull plain', seed=500 + i)
        t.cluster(x, y, 40, ['mill'], 1, plot=None); out.append(t)
    for i, (x, y, r) in enumerate(COPSES):
        m = g.shape(x, y, r, r * 0.8, 5600 + i, 0.4) & np.isin(K, ['meadow', 'watermeadow', 'steppe', 'fallow']) & ~T['taken'] & ~T['street']
        K[m] = 'broadleaf'
    for nm, pts in TERRACES.items():
        d, al, tot = g.raster(chaikin(pts, 2))
        band_ = (d < 520) & T['land'] & np.isin(K, ['meadow', 'watermeadow', 'scroll', 'carr', 'field', 'field2', 'hedge', 'orchard'])
        step = np.clip(d // 130, 0, 4)                                  # four flat steps, each a tier above the last
        T['h'] = np.where(band_, np.minimum(T['h'], 0.10 + 0.034 * step + 0.004 * g.noise(80, 5601)), T['h'])
    return out


def settled_margins(T):
    """The desert's and the fire country's settled edges: scrub along the dry beds, green along the irrigated channels."""
    K = T['K']
    for nm, pts in V54.DRY_BEDS.items():
        d = g.raster(chaikin(pts, 2))[0]
        K[(d < 70 + 30 * g.noise(60, 5611)) & np.isin(K, ['desert', 'erg']) & T['land']] = 'scrub'
    for nm in ('the Amber', 'the Willow Run'):
        d = g.raster(T['river_px'][nm])[0]
        near = (d < 90) & np.isin(K, ['desert', 'scrub', 'erg', 'badland']) & T['land'] & (g.PY > 2300) & (g.PY < 3300)
        K[near] = 'steppe'


# ------------------------------------------------------------------------------------------ stage 3e: what the stretch changed
BORDER_MATERIALS = {'thicket', 'bramble', 'felltree', 'ancient', 'gorse', 'boulders', 'scrubwall', 'dunewall', 'scree2', 'crag', 'crevasse', 'aa', 'pool',
                    'mere', 'sinkhole', 'driftwood'}


def break_runs(T):
    """The warp repeats cells, so a border prop that ran three cells can run five: break any run of one material longer than
    three props (nine cells), as geo52's borders do. Cells the towns or roads have since built on leave the border band."""
    K = T['K']; T['border_assigned'] &= np.isin(K, list(BORDER_MATERIALS)); band_ = T['border_assigned']; n = 0
    alt = {'boulders': 'scree2', 'scree2': 'boulders', 'bramble': 'gorse', 'gorse': 'bramble', 'thicket': 'felltree', 'felltree': 'thicket', 'ancient': 'thicket',
           'dunewall': 'scrubwall', 'scrubwall': 'dunewall', 'crag': 'scree2', 'crevasse': 'crag', 'aa': 'boulders', 'sinkhole': 'pool', 'pool': 'sinkhole',
           'mere': 'bramble', 'driftwood': 'boulders'}
    alt2 = {'boulders': 'gorse', 'scree2': 'crag', 'bramble': 'thicket', 'gorse': 'boulders', 'thicket': 'bramble', 'felltree': 'bramble', 'ancient': 'felltree',
            'dunewall': 'boulders', 'scrubwall': 'boulders', 'crag': 'boulders', 'crevasse': 'scree2', 'aa': 'scree2', 'pool': 'bramble', 'sinkhole': 'bramble',
            'mere': 'pool', 'driftwood': 'scree2'}

    def pick(Ka, jj, ii, a):
        """alt or alt2, whichever differs from the cell's four neighbours (so a fix across never makes a run down)."""
        nb = {Ka[y, x] for y, x in ((jj - 1, ii), (jj + 1, ii), (jj, ii - 1), (jj, ii + 1)) if 0 <= y < Ka.shape[0] and 0 <= x < Ka.shape[1]}
        for c in (alt.get(a, 'boulders'), alt2.get(a, 'scree2'), 'bramble', 'scree2'):
            if c not in nb:
                return c
        return alt.get(a, 'boulders')
    for _ in range(8):
        changed = 0
        for Ka, Ba in ((K, band_), (K.T, band_.T)):
            same = np.zeros(Ka.shape, bool); same[:, 1:] = (Ka[:, 1:] == Ka[:, :-1]) & Ba[:, 1:] & Ba[:, :-1]
            for j in np.nonzero(same.any(1))[0]:
                run = 0
                for i in range(Ka.shape[1]):
                    run = run + 1 if (i > 0 and Ka[j, i] == Ka[j, i - 1] and Ba[j, i] and Ba[j, i - 1]) else 0
                    if run == 8:
                        a_ = Ka[j, i]
                        for (dj, di) in ((0, 0), (0, 1), (-1, 0), (1, 0)):
                            jj, ii = j + dj, i + di
                            if 0 <= jj < Ka.shape[0] and 0 <= ii < Ka.shape[1] and Ba[jj, ii]:
                                Ka[jj, ii] = pick(Ka, jj, ii, a_)
                        run = 0; n += 1; changed += 1
        if not changed:
            break
    return n


def town_events(T, towns):
    """In a town the street bends round its buildings: a building whose front is within 60 px of a main route is something the
    route meets (the benchmark's check 16), one every 120 px or so; no side path."""
    out = []
    for rn in G.MAIN_ROUTES:
        x, y, al, tot = densify(T['route_px'][rn], 8)
        last = -1e9
        for nm, t in towns.items():
            for b in t.buildings:
                cx, cy = b['x'] + b['w'] / 2, b['y'] + b['h'] / 2
                d = np.hypot(x - cx, y - cy) - max(b['w'], b['h']) / 2
                i = int(np.argmin(d))
                if d[i] < 60:
                    out.append((float(al[i]), rn, int(cx), int(cy), nm))
    out.sort()
    ev = []; lastpos = {}
    for a, rn, cx, cy, nm in out:
        if a - lastpos.get(rn, -1e9) >= 120:
            ev.append({'route': rn, 'obstacle': 'a building of ' + nm.split(':')[0], 'x': cx, 'y': cy, 'side_path': False, 'v55': True}); lastpos[rn] = a
    return ev


def gap_obstacles(T, obs):
    """Where the stretch left a route more than 260 px without a bend or an obstacle (the benchmark's check 16), an obstacle
    beside it with a side path round its far side, as geo52's obstacles are made."""
    K = T['K']; out = []
    bar = np.zeros((g.H, g.W), bool)
    for m in T['barriers'].values():
        bar |= m
    hard = np.isin(K, ['river', 'rapids', 'lava', 'aa', 'fissure', 'sea', 'canal', 'wall', 'cliff', 'crag', 'glacier', 'building', 'tower', 'warehouse',
                       'castlewall', 'tarn', 'oxbow', 'mere', 'crater', 'erg', 'rockfall', 'fence', 'keep'])
    obs_by = {}
    for o in obs:
        obs_by.setdefault(o['route'], []).append((o['x'], o['y']))
    for k_, rn in enumerate(G.MAIN_ROUTES):
        for _ in range(6):
            x, y, al, tot = densify(T['route_px'][rn], 8)
            hd = np.unwrap(np.arctan2(np.gradient(y), np.gradient(x))); hd = ndi.gaussian_filter1d(hd, 3)
            win = 10; turn = np.abs(hd[win:] - hd[:-win]); bend_pos = list(al[win:][turn > math.radians(15)])
            evp = obs_by.get(rn, []) + obs_by.get('ring', []) + [(c['x'], c['y']) for c in T['crossings'] if c['route'] == rn] + list(G.THRESHOLDS.values())
            ev = bend_pos + [al[int(np.argmin(np.hypot(x - ox, y - oy)))] for ox, oy in evp if np.hypot(x - ox, y - oy).min() < 120]
            pos = np.sort(np.r_[0, ev, tot]); gaps = np.diff(pos)
            if len(gaps) == 0 or gaps.max() <= 260:
                break
            gi = int(gaps.argmax()); a0 = (pos[gi] + pos[gi + 1]) / 2
            placed = False
            for da in (0, -50, 50, -90, 90):
                i = int(np.argmin(np.abs(al - (a0 + da))))
                tx, ty = x[min(i + 2, len(x) - 1)] - x[max(i - 2, 0)], y[min(i + 2, len(x) - 1)] - y[max(i - 2, 0)]; Lt = math.hypot(tx, ty) or 1
                nx_, ny_ = -ty / Lt, tx / Lt
                for sd in (1, -1):
                    ox, oy = x[i] + nx_ * sd * 110, y[i] + ny_ * sd * 110
                    a, b = int(oy // g.CELL), int(ox // g.CELL)
                    if not (0 < a < g.H and 0 < b < g.W):
                        continue
                    ground = K[a, b]
                    kind = {'broadleaf': 'thicket', 'conifer': 'felltree', 'wild': 'thicket', 'carr': 'thicket', 'reeds': 'pool', 'watermeadow': 'pool',
                            'bog': 'pool', 'scroll': 'pool', 'meadow': 'boulders', 'field': 'boulders', 'field2': 'thicket', 'steppe': 'boulders',
                            'desert': 'boulders', 'scrub': 'boulders', 'sand': 'driftwood', 'heath': 'boulders', 'alpine': 'scree', 'ash': 'boulders',
                            'lavastone': 'boulders', 'fireweed': 'thicket', 'basalt': 'boulders', 'blacksand': 'driftwood', 'deadwood': 'felltree',
                            'garden': 'thicket', 'orchard': 'thicket', 'hedge': 'thicket', 'fallow': 'boulders', 'barren': 'boulders', 'badland': 'boulders',
                            'clearing': 'boulders', 'gorse': 'boulders'}.get(ground)
                    if not kind:
                        continue
                    ob = g.shape(ox, oy, 60, 40, 5700 + 2 * (len(out) % 4), 0.45, math.atan2(ty, tx))
                    routec = np.isin(K, ['path', 'road', 'bridge', 'stair', 'bar', 'trail', 'lane'])
                    ob &= T['land'] & ~routec & ~hard & ~bar & ~T.get('taken', np.zeros_like(bar))
                    if ob.sum() < 16:
                        continue
                    j0 = int(np.argmin(np.abs(al - (al[i] - 220)))); j1 = int(np.argmin(np.abs(al - (al[i] + 220))))
                    loop = chaikin([(x[j0], y[j0]), (ox + nx_ * sd * 100 - tx / Lt * 90, oy + ny_ * sd * 100 - ty / Lt * 90),
                                    (ox + nx_ * sd * 100 + tx / Lt * 90, oy + ny_ * sd * 100 + ty / Lt * 90), (x[j1], y[j1])], 3)
                    lm = G._orig_line_mask(loop, 20)
                    if (lm & (bar | hard | ob)).any():
                        continue
                    K[ob] = kind; K[lm & ~routec] = 'trail'; T['used'] |= lm | ob
                    o = {'route': rn, 'obstacle': kind, 'x': round(ox), 'y': round(oy), 'side_path': True, 'along': float(al[i]), 'v55': True}
                    obs.append(o); out.append(o); obs_by.setdefault(rn, []).append((o['x'], o['y'])); placed = True
                    break
                if placed:
                    break
            if not placed:
                break
    return out


# ------------------------------------------------------------------------------------------ v56: fit ground to the authored places
CROSSROADS_RIVER_BOX = (6120, 3096, 6736, 3968)
CROSSROADS_RIVER = [(6256, 3120), (6400, 3176), (6656, 3216), (6680, 3376),
                    (6680, 3760), (6616, 3864), (6384, 3928)]


def feedback_river(T, points, zone_box, *, corridor=CROSSROADS_RIVER_BOX):
    """Divert the macro Sleepwater around the existing dry gameplay zone.

    The actual channel, its source polyline and barrier masks move together.
    This does not paint a building over water or erase a river from the picture.
    The same source and downstream mill reach remain connected.
    """
    K = T['K']; x0, y0, x1, y1 = corridor
    win = (g.PX >= x0) & (g.PX < x1) & (g.PY >= y0) & (g.PY < y1)
    old_line = list(map(tuple, T['river_px']['the Sleepwater']))
    inside = [i for i, (x, y) in enumerate(old_line) if x0 <= x < x1 and y0 <= y < y1]
    if not inside:
        raise ValueError('v56 Sleepwater corridor has no inherited river to join')
    i0, i1 = inside[0], inside[-1]
    segment = ([old_line[i0 - 1]] if i0 else []) + list(points) + ([old_line[i1 + 1]] if i1 + 1 < len(old_line) else [])
    segment = chaikin(segment, 2)
    channel = G._orig_line_mask(segment, 24) & win & T['land']
    old = T['river_masks']['the Sleepwater'] & win
    zx0, zy0, zx1, zy1 = zone_box
    zone = (g.PX >= zx0) & (g.PX < zx1) & (g.PY >= zy0) & (g.PY < zy1)
    # The existing zone has no water; small drainage creeks cannot remain under it.
    retired = (old | zone) & np.isin(K, ['river', 'rapids', 'creek', 'bridge']) & ~channel
    K[retired] = 'meadow'
    crossed_routes = channel & np.isin(K, ['road', 'path', 'trail', 'bridge'])
    K[channel] = 'river'; K[crossed_routes] = 'bridge'
    T['river_masks']['the Sleepwater'] = (T['river_masks']['the Sleepwater'] & ~win) | channel
    T['river_px']['the Sleepwater'] = old_line[:i0] + list(map(tuple, segment)) + old_line[i1 + 1:]
    for key, mask in T['barriers'].items():
        if mask.shape == K.shape:
            mask[retired] = False
    if 'water' in T:
        T['water'][retired] = False; T['water'][channel] = True
    if (channel & zone).any():
        raise ValueError('v56 Sleepwater still crosses the existing Crossroads zone')
    return {'retired_channel_cells': int(retired.sum()), 'new_channel_cells': int(channel.sum()),
            'source': 'the Sleepwater', 'joins': 'same upstream source and downstream mill reach',
            'zone_water_cells': int(np.isin(K[zone], ['river', 'creek', 'rapids']).sum())}


def feedback_ground(T):
    """Local terrain revision before placement; sea, rivers and story sites stay authoritative."""
    zp = json.load(open(os.path.join(ROOT, 'game', 'data', 'plans', 'crossroads.json')))
    ox, oy = zp['origin_on_canvas']; _, _, zw, zh = zp['box']
    rec = feedback_river(T, CROSSROADS_RIVER, (ox, oy, ox + zw, oy + zh))
    K = T['K']
    # Urban ground is terraced dry land, never a rectangular paving overwrite of water.
    dry = T['land'] & ~np.isin(K, ['river', 'rapids', 'creek', 'canal', 'sea', 'surf', 'falls',
                                  'pool', 'crater', 'shardglass', 'craterrim', 'scorch'])
    east = dry & (g.PX >= 10520) & (g.PX < 12384) & (g.PY >= 4224) & (g.PY < 5600)
    west = dry & (g.PX >= 9776) & (g.PX < 10416) & (g.PY >= 4704) & (g.PY < 5728)
    # A city built on successive waterfront terraces, with the Heights descending to a park.
    shelf = np.where(g.PY < 4480, 7, np.where(g.PY < 4928, 6, 5))
    height = np.where(g.PY < 4928, 9, np.maximum(5, 8 - (g.PY - 4928) // 192))
    for mask, tiers in ((east, shelf), (west, height)):
        T['h'][mask] = (tiers[mask] + 0.5) / 30.0
        K[mask & np.isin(K, ['cliff', 'crag', 'tor', 'boulders', 'scree', 'wild', 'ancient', 'thicket', 'conifer'])] = 'meadow'
    # Existing Crossroads floor/terrace identity is retained at macro scale too.
    zone = (g.PX >= ox) & (g.PX < ox + zw) & (g.PY >= oy) & (g.PY < oy + zh)
    clear = zone & np.isin(K, ['meadow', 'watermeadow', 'broadleaf', 'conifer', 'creek', 'field', 'field2', 'hedge', 'yard', 'garden'])
    K[clear] = 'meadow'
    return rec


def feedback_checks(T, plans):
    """Fail closed on literal final ground, including inherited zone buildings."""
    import town_plans as TP
    K = T['K']
    for pid in ('crossroads', 'neon-harbour'):
        P = plans[pid]
        expected = {'crossroads': 40, 'neon-harbour': 72}[pid]
        if P['buildings_counted'] != expected:
            raise ValueError(f"v56 {pid}: {P['buildings_counted']} counted buildings, expected retained {expected}")
        occupied = np.zeros(K.shape, bool)
        for b in P['buildings']:
            c, r, w, h = b['footprint_cells']
            if occupied[r:r + h, c:c + w].any():
                raise ValueError(f"v56 {b['id']}: footprint overlaps another building")
            occupied[r:r + h, c:c + w] = True
            if np.isin(K[r:r + h, c:c + w], TP.WATER_K + TP.BARRIER_K).any():
                raise ValueError(f"v56 {b['id']}: footprint intersects final water/barrier ground")


def feedback_plan_checks(T, plans):
    """Retain every final town finding, not only the revised towns' count checks.

    Failed proposals can still be pictured for review; the v56 command exits 1
    after writing the complete report and requested pictures. No finding is
    demoted, and neither a picture nor a count becomes an acceptance pass.
    """
    import town_plans as TP
    checker = TP.TW._review()
    blockout = {'routes': {rn: {'polyline': pts} for rn, pts in T['route_px'].items()}, 'stations': g.STATIONS}
    reports = {}
    for pid, P in plans.items():
        c, r, w, h = P['terrain']['box_cells']
        P['terrain']['rows'] = TP.terrain_rows(T['K'][r:r + h, c:c + w])
        failures, notes, metrics = checker.check_plan(P, blockout)
        occupied = np.zeros(T['K'].shape, bool)
        for b in P['buildings']:
            bc, br, bw, bh = b['footprint_cells']
            if bc < 0 or br < 0 or bc + bw > T['K'].shape[1] or br + bh > T['K'].shape[0]:
                failures.append(f"bounds: {b['id']} leaves final terrain")
                continue
            footprint = T['K'][br:br + bh, bc:bc + bw]
            if np.isin(footprint, TP.WATER_K + TP.BARRIER_K).any():
                failures.append(f"final_ground: {b['id']} intersects literal water/barrier ground")
            if occupied[br:br + bh, bc:bc + bw].any():
                failures.append(f"final_ground: {b['id']} overlaps another footprint")
            occupied[br:br + bh, bc:bc + bw] = True
        expected = {'crossroads': 40, 'neon-harbour': 72}.get(pid)
        if expected is not None and P['buildings_counted'] != expected:
            failures.append(f"retained_count: {P['buildings_counted']} != {expected}")
        reports[pid] = {'pass': not failures, 'failures': failures, 'notes': notes,
                        'metrics': metrics, 'actual_count': P['buildings_counted'], 'retained_count': expected}
        print(('PASS' if not failures else 'FAIL'), 'v56 town', pid, json.dumps(reports[pid]))
    return reports


# ------------------------------------------------------------------------------------------ stage 3: everything on the v55 canvas
def v55_paint(T):
    import towns55 as TW
    rec = {}
    rec['city_cleared_cells'] = clear_city(T)
    rec['east_coast'] = east_coast(T)
    highgarth_valley(T)
    add_route(T, 'the Garth Road', GARTH_ROAD, 'path')
    add_route(T, 'the Northway', [HIGHGARTH] + NORTHWAY_OPEN, 'path')
    closed_pass(T)
    add_route(T, 'the Pad Road', PAD_ROAD, 'road')
    rec['forest'] = old_forest(T)                                    # the old forest's places, its trail and clearings
    # the new walked ground: the valley, its roads, the cape; the frame taken off and the borders drawn round them
    new_walk = T['highgarth_floor'] | G._orig_line_mask(T['route_px']['the Garth Road'], 120) | G._orig_line_mask(T['route_px']['the Northway'], 120)
    cape = T['land'] & (((g.PX > 11300) & (g.PY > 5300)) | ((g.PX > 11300) & (g.PX < 12420) & (g.PY > 4300)))
    unframe(T, new_walk, 100)
    T['FRAME'] &= ~cape; g.FRAME = T['FRAME']
    yl = np.interp(g.PX, [x for x, y in ROCKFALL_LINE], [y for x, y in ROCKFALL_LINE])
    beyond = T['land'] & (g.PY < yl - 16) & (g.PX > 7300) & (g.PX < 8500)
    T['FRAME'] |= beyond; g.FRAME = T['FRAME']                       # past the rockfall is past the walk: the pass is closed
    region = ndi.distance_transform_edt(~(new_walk | cape)) * g.CELL < 900
    reborder(T, region)
    T['FRAME'] |= beyond & ~T['closed_mask']; g.FRAME = T['FRAME']   # the borders' fade may not open it again
    if os.environ.get('DEV_PRE'):                                    # a development cache: the ground just before the towns
        pickle.dump({'T': T}, open(os.environ['DEV_PRE'], 'wb'), protocol=4); sys.exit(0)
    if REVISION == 'v56':
        rec['feedback_ground'] = feedback_ground(T)
    TW.prepare(T, keepout_boxes=[V.BUILT['the woodland']],
               keepout_discs=[(6296, 3088, 150), (6816, 3648, 110), (6484, 3712, 90), (V.CIRCLE[0], V.CIRCLE[1], 120)])
    towns = (TW.lay_feedback if REVISION == 'v56' else TW.lay_all)(T, sys.modules[__name__])
    towns.update(TW.launch_cape(T, sys.modules[__name__]))
    towns.update(TW.charcoal_hollow(T, sys.modules[__name__]))
    for t in towns.values():                                         # no impassable deep forest inside a town: open woods
        if t.buildings:
            x0, y0, x1, y1 = t.record()['footprint_box']
            a, b, c, d = int(max(0, y0 - 60) // g.CELL), int(max(0, x0 - 60) // g.CELL), int((y1 + 60) // g.CELL), int((x1 + 60) // g.CELL)
            sub = T['K'][a:c, b:d]; sub[np.isin(sub, ['wild', 'ancient']) & ~T['FRAME'][a:c, b:d]] = 'broadleaf'
    import town_plans as TP                                          # each town's plan: arrivals, access, the record (towns/<id>.json)
    rec['plans'] = TP.finish(T, towns, sys.modules[__name__])
    farms = central_green(T, TW)
    settled_margins(T)
    TP.ground(T, rec['plans'], towns, sys.modules[__name__])        # what each town's ground is made of (a tint, not a kind)
    rec['towns'] = towns; rec['farms'] = farms
    return rec


# ------------------------------------------------------------------------------------------ stage 4: tables, checks, data
NEW_PLACES = {   # v55's new settlements (SETTLE form: x, y, radius px, kind)
    'Highgarth': (HIGHGARTH[0], HIGHGARTH[1], 260, 'hilltown'), 'Halcyon Row': (12020, 5590, 180, 'village'),
    'Glintside': (11120, 4150, 160, 'hamlet'), 'Canalside': (10000, 4430, 200, 'hamlet')}
CLOSED = {'C1': {'name': 'the Highgarth pass', 'gate': 'the Highgarth rockfall', 'gate_xy': list(ROCKFALL), 'col_xy': list(HIGHGARTH_PASS),
                 'route': 'the Northway', 'open_to': 'the rockfall (a viewpoint, a sign and the road beyond seen, not walked)',
                 'movement': 'closed: the rockfall and the road beyond are not walkable ground', 'navigation': 'closed: no route, path plan or '
                 'act 1 beat runs past the rockfall; the road beyond is listed under closed_routes, not routes',
                 'travel': 'closed: no waystone, station, shortcut, ferry or fast-travel target beyond it', 'state': 'closed', 'opens': 'later, with a '
                 'region north of the range; the road runs on over the col at the canvas\'s top edge, so the new region joins there without moving a '
                 'town or rescaling the continent', 'separate_from_story': 'the act 1 crossings are the ridge col (W2) and the Fells saddle, 1.3 km '
                 'west; the Northway shares no ground with them'}}
LABEL_ZOOM = {'continent (the 1920 and 3840 maps)': 'regions, the large and medium towns and the city, the stone circle, the principal routes '
              '(roads, rail and ferries) and the closed pass; nothing else', 'region (the insets)': 'every settlement, gate, crater, peak, biome, water '
              'and route in the inset', 'reference (map55-reference)': 'every name on the continent, at 3x'}


def update_tables(T, towns):
    """The settlement table from the footprints, the new places, the ways and the waystones."""
    for nm, v in NEW_PLACES.items():
        g.SETTLE[nm] = v
    for nm, t in towns.items():
        base = nm.split(':')[0]
        if base in g.SETTLE and t.buildings and not nm.startswith('Neon'):
            r = t.record(); x0, y0, x1, y1 = r['footprint_box']
            cx, cy, rad, kind = g.SETTLE[base]
            g.SETTLE[base] = (cx, cy, int(max(rad, 0.5 * math.hypot(x1 - x0, y1 - y0) * 0.8)), kind)
    g.SETTLE['Launch Cape'] = (PAD[0], PAD[1], 240, 'cape')
    g.WAYS['W8'] = [(PAD[0], PAD[1], 80)]
    g.BEHIND['W3'] = list(g.BEHIND['W3']) + ['Highgarth', (7860, 700)]
    g.BEHIND['W7'] = list(g.BEHIND['W7']) + ['Halcyon Row', 'Glintside', (12030, 6250)]
    V.WAYSTONES['Highgarth'] = (7930, 1225, 'proposed')
    V.WAYSTONES['Launch Cape'] = (12000, 5560, 'proposed')
    V.WAYSTONES['the market (Neon)'] = (11150, 4500, 'proposed')
    G.REGIONS['the upper Cog (Highgarth)'] = (7300, 200, 8600, 1750)
    G.REGIONS['Neon Harbour'] = (G.REGIONS['Neon Harbour'][0], G.REGIONS['Neon Harbour'][1], NEW_W, 6760)
    G.BIOMES['Neon Harbour'] = (G.BIOMES['Neon Harbour'][0], G.BIOMES['Neon Harbour'][1], NEW_W, 6760)


def closed_check(K):
    """With every way open, nothing beyond the rockfall is reachable from home, and the Northway up to it is."""
    Wm = g.walk_mask(K); lab, _ = ndi.label(Wm)
    hy, hx = g.nearest_walk(Wm, *g.HOME); home = lab[hy, hx]
    out = {'beyond': [], 'open_part_reached': None}
    x, y, al, tot = densify(chaikin(NORTHWAY_CLOSED, 2), 40)
    for px_, py_ in zip(x, y):
        if py_ > ROCKFALL[1] - 50 or py_ < 0:
            continue
        a, b = int(py_ // g.CELL), int(px_ // g.CELL); r = 6
        win = (lab[max(0, a - r):a + r + 1, max(0, b - r):b + r + 1] == home)
        out['beyond'].append({'x': round(float(px_)), 'y': round(float(py_)), 'reachable': bool(win.any())})
    ey, ex = g.nearest_walk(Wm, *NORTHWAY_OPEN[-1])
    out['open_part_reached'] = bool(lab[ey, ex] == home)
    out['leaks'] = [p for p in out['beyond'] if p['reachable']]
    out['pass'] = not out['leaks'] and out['open_part_reached']
    return out


JOURNEYS = [('Crossroads', 'Fernhollow', 'Cogsworth'), ('Crossroads', 'Palm Spring', 'Dust Gulch'), ('Dust Gulch', 'Hearthold', 'Cinderwick'),
            ('Lullford', 'Canalside', 'Neon Harbour', 'Halcyon Row', 'Launch Cape'), ('Cogsworth', 'Highgarth', 'the rockfall')]


def journeys(K, speed):
    """Step 7's journeys as a baseline: each leg walked on the block-out with every way open (no trains), its length and its
    time at Bramble's speed."""
    from skimage.graph import MCP_Geometric
    Wm = g.walk_mask(K); cost = np.where(Wm, 1.0, np.inf)
    pts = {nm: v[:2] for nm, v in g.SETTLE.items()}; pts['the rockfall'] = (ROCKFALL[0], ROCKFALL[1] + 70); pts['Crossroads'] = V.CROSSROADS
    out = []
    for j in JOURNEYS:
        legs = []
        for a, b in zip(j, j[1:]):
            ya, xa = g.nearest_walk(Wm, *pts[a]); yb, xb = g.nearest_walk(Wm, *pts[b])
            m = MCP_Geometric(cost); d, _ = m.find_costs([(ya, xa)], [(yb, xb)])
            px_ = float(d[yb, xb]) * g.CELL
            legs.append({'from': a, 'to': b, 'walk_px': round(px_), 'walk_s_at_hero_speed': round(px_ / speed, 1) if np.isfinite(px_) else None})
        out.append({'journey': ' - '.join(j), 'legs': legs, 'total_s': round(sum(l['walk_s_at_hero_speed'] or 0 for l in legs), 1)})
    return out


def usable(T):
    K = T['K']
    return int((T['land'] & ~T['FRAME'] & (np.isin(K, list(g.WALK)) | np.isin(K, ['building', 'warehouse', 'tower', 'keep', 'hangar', 'terminal', 'neon']))).sum())


def route_widths(T):
    """geo52's varied route widths (line_mask_var's seeded draws), for a run from the development cache."""
    out = []
    for rn, pts in T['route_px'].items():
        kind = g.ROUTES.get(rn, (0, 'path'))[1]
        width = 40 if kind in ('road', 'bar', 'bridge') else 24
        x, y, al, tot = densify(pts, 6)
        r = np.random.default_rng(int(abs(x[0] * 7 + y[0] * 13)) % 2 ** 31)
        n = max(1, int(tot // 120))
        out += [int(min(64, width + r.choice([0, 0, 8, 16, 24]))) for _ in range(n)]
    return out


def data_stage():
    V.SUF = SUF
    cache = os.environ.get('OLD_CACHE')                              # a development cache of v54's ground (deterministic)
    if cache and os.path.exists(cache):
        D = pickle.load(open(cache, 'rb')); T, obs, pocks = D['T'], D['obs'], D['pocks']; g.WAYS.clear(); g.WAYS.update(D['WAYS']); g.FRAME = T['FRAME']
        G.ROUTE_WIDTHS[:] = D.get('ROUTE_WIDTHS') or route_widths(T)               # the varied stroke widths the benchmark reads
    else:
        T, obs, pocks = stage_old()
        if cache:
            pickle.dump({'T': T, 'obs': obs, 'pocks': pocks, 'WAYS': g.WAYS, 'ROUTE_WIDTHS': list(G.ROUTE_WIDTHS)}, open(cache, 'wb'), protocol=4)
    u54 = usable(T)
    T, obs, pocks = warp_T(T, obs, pocks)
    warp_tables(); set_dims(NEW_W, NEW_H)
    g.FRAME = T['FRAME']
    u_warp = usable(T)
    rec = v55_paint(T)
    towns = rec['towns']
    update_tables(T, towns)
    K = T['K']
    nb = break_runs(T)
    print('break_runs replaced', nb)
    obs += town_events(T, towns)
    rec['gap_obstacles'] = gap_obstacles(T, obs)
    if os.environ.get('DEV_PKL'):
        pickle.dump({'T': T}, open(os.environ['DEV_PKL'], 'wb'), protocol=4)
    pois, per = G.content(T)
    pois.append({'name': 'the rockfall sign', 'cat': 'view', 'biome': G.biome_of(*ROCKFALL) or '', 'x': ROCKFALL[0], 'y': ROCKFALL[1] + 40,
                 'route': 'the Northway', 'off_path': False})
    for nm, cat, rn in (("the moon-watchers' observatory", 'story', 'the Old Forest Trail'), ('the Elder Oak', 'story', 'the Old Forest Trail'),
                        ('Fernmere', 'view', 'the Fernmere path'), ("the Company's timber camp", 'story', 'the camp track')):
        x_, y_ = FOREST_PLACES[nm][:2]                               # the old forest's places, where its trails end
        pois.append({'name': nm, 'cat': cat, 'biome': G.biome_of(x_, y_) or '', 'x': x_, 'y': y_, 'route': rn, 'off_path': False})
    pois = G.fill_required(T, pois); marks = G.markers(T)
    gates = g.gate_check(K, T['crossings'])
    gates['closed: the Highgarth pass'] = closed_check(K)
    res, rl, wc = g.times(K)
    t = G.tier_field(T); steps = G.route_steps(T, t); vstats = G.vertical_stats(T, t, steps)
    art_speed, speed = V.hero_speed()
    k_ = g.SPEED / speed
    hero = {nm: {kk: (round(v * k_, 1) if v is not None else None) for kk, v in d.items()} for nm, d in res.items()}
    Wm = g.walk_mask(K); lab, _ = ndi.label(Wm); hy, hx = g.nearest_walk(Wm, *g.HOME); home = lab[hy, hx]
    reach = {}
    pts = [(n, c[:2]) for n, c in V.CRATERS.items()] + [(n, c[:2]) for n, c in V.POI53.items()] + [(n, c[:2]) for n, c in V.WAYSTONES.items()] \
        + [('the stone circle', V.CIRCLE)] + [(n, v[:2]) for n, v in NEW_PLACES.items()] + [('the pad', PAD)]
    for nm, p in pts:
        yy_, xx_ = g.nearest_walk(Wm, *p); reach[nm] = {'reached': bool(lab[yy_, xx_] == home), 'snap_px': round(math.hypot(xx_ * g.CELL + 4 - p[0], yy_ * g.CELL + 4 - p[1]))}
    u55 = usable(T)
    jr = journeys(K, speed)
    town_rec = {nm: t.record() for nm, t in towns.items()}
    neon = {nm: r for nm, r in town_rec.items() if nm.startswith('Neon Harbour')}
    v55 = {'warp': warp_table(),
           'usable_land': {'definition': 'land cells outside the frame that are walkable or built on (8 px cells)', 'v54_cells': u54,
                           'after_warp_cells': u_warp, 'v55_cells': u55, 'increase_pct': round(100 * (u55 / u54 - 1), 1)},
           'settlements': {nm: {k: v for k, v in r.items() if k not in ('buildings', 'streets')} for nm, r in town_rec.items()},
           'building_counts': {nm: r['buildings_counted'] for nm, r in town_rec.items()},
           'neon_harbour': {'buildings_total': sum(r['buildings_counted'] for r in neon.values()), 'districts': list(neon)},
           'farms': [{'name': f.name, 'x': f.centre[0], 'y': f.centre[1], 'buildings': f.count()} for f in rec['farms']],
           'east_coast': {'shore': [list(p) for p in EAST_SHORE], 'cape_west_shore': [list(p) for p in CAPE_WEST], **rec['east_coast']},
           'launch_cape': {'pad': list(PAD), 'pad_road': [list(p) for p in PAD_ROAD], 'buffer_px_to_nearest_house': None},
           'highgarth': {'centre': list(HIGHGARTH), 'garth_road': [list(p) for p in GARTH_ROAD], 'northway_open': [list(p) for p in NORTHWAY_OPEN],
                         'valley_floor': [list(p) for p in VALLEY_FLOOR], 'behind_way': 'W3 (with Cogsworth)'},
           'closed': CLOSED, 'closed_check': gates['closed: the Highgarth pass'],
           'central_green': {'farms': [list(f) for f in FARMS], 'windmills': [list(w) for w in WINDMILLS], 'copses': [list(c) for c in COPSES],
                             'terraces': {k: [list(p) for p in v] for k, v in TERRACES.items()}},
           'label_zoom': LABEL_ZOOM, 'levelled_footprints': len(T.get('levelled', [])), 'journeys': jr,
           'note': "v54's ground warped onto the v55 canvas (warp), then the towns, the east coast and cape, Highgarth and its closed pass "
                   'laid on it; steps 5 to 7 are a plan in README.md, v55'}
    hs = [b for nm in ('Halcyon Row',) for b in town_rec.get(nm, {}).get('buildings', [])]
    if hs:
        v55['launch_cape']['buffer_px_to_nearest_house'] = round(min(math.hypot(b[0] + b[2] / 2 - PAD[0], b[1] + b[3] / 2 - PAD[1]) for b in hs))
    stats = {'world_px': [NEW_W, NEW_H], 'walkable_zone_areas': round(wc / 2880, 1), 'routes_s': rl, 'home_to': res, 'why_here': g.WHY,
             'bridges': g.BRIDGES, 'easter_egg_spots_later': g.EGGS, 'ways': g.WAY_NAMES, 'oxbows': T['oxbows'], 'delta_arms': len(T['delta']),
             'vertical': vstats, 'route_tier_changes': {rn: sum(1 for s_ in steps if s_[0] == rn) for rn in g.ROUTES}, 'thresholds': G.THRESHOLDS,
             'content_per_biome': per, 'content': pois, 'obstacles': obs, 'pockets': pocks, 'markers': marks,
             'settlement_density': T['settlement_density'], 'mixing': T['mixing'],
             'v53': {'circle': V.CIRCLE, 'crossroads': V.CROSSROADS, 'craters': T['craters'], 'new_routes': V.NEW_ROUTE_WHY, 'poi': V.POI53,
                     'waystones': V.WAYSTONES, 'reachable_with_every_way_open': reach,
                     'hero': {'cast': 'bramble', 'walk_speed_art_px_s': art_speed, 'walk_speed_world_px_s': round(speed, 2),
                              'cells_s': round(speed / g.CELL, 3), 'screen_1080p_s': round(320 / speed, 1),
                              'note': 'home_to and routes_s keep the plan speed of 40 px a second for comparison; home_to_at_hero_speed uses the manifest'},
                     'home_to_at_hero_speed': hero},
             REVISION: v55}
    if REVISION == 'v56':
        v55['revision'] = {'id': REVISION, 'base': '303@4984438d + 355@7afe9efd',
                           'seed_contract': PROSPECTIVE_SEED, 'historical_equivalence': False,
                           'feedback_ground': rec['feedback_ground'],
                           'counts': {'crossroads': 40, 'neon-harbour': 72, 'neon_size_approved': False}}
    bres = G.bench(T, pois, marks, pocks, obs, steps, gates); stats['benchmark'] = bres; stats['biome_detail'] = T['biome_detail']
    for b_ in bres:
        print(('PASS' if b_['pass'] else 'FAIL'), b_['n'], b_['check'], '|', b_['measured'])
    print('diag9', T.get('diag9'), 'diag16', str(T.get('diag16'))[:300])
    print(json.dumps({k: v for k, v in gates.items() if k not in ('crossings', 'closed: the Highgarth pass')})[:3000])
    print('closed pass', gates['closed: the Highgarth pass']['pass'], gates['closed: the Highgarth pass']['leaks'][:3])
    print('usable land', v55['usable_land'])
    um = T['land'] & ~T['FRAME'] & (np.isin(K, list(g.WALK)) | np.isin(K, ['building', 'warehouse', 'tower', 'keep', 'hangar', 'terminal']))
    print('usable: valley box', int(um[0:220, 900:1080].sum()), 'cape/east', int(um[500:, 1410:].sum()))
    S = {'T': T, 'stats': stats, 'gates': gates, 't': t, 'steps': steps, 'vstats': vstats, 'town_rec': town_rec, 'res': res, 'plans': rec['plans']}
    return S


def write_data(S):
    """The three JSON files and the map state."""
    T, stats, gates, t, steps, vstats, town_rec = S['T'], S['stats'], S['gates'], S['t'], S['steps'], S['vstats'], S['town_rec']
    import map55
    if REVISION == 'v56':
        S['stats'][REVISION]['physical_checks'] = feedback_plan_checks(T, S['plans'])
    state = map_state(S)
    F = map55.features(state, sys.modules[__name__])
    stats['v54'] = V54.v54_block(F)
    json.dump(stats, open(os.path.join(DATA, f'stats{SUF}.json'), 'w'), indent=1)
    json.dump(gates, open(os.path.join(DATA, f'gates{SUF}.json'), 'w'), indent=1)
    if REVISION == 'v56':
        json.dump(stats[REVISION]['physical_checks'], open(os.path.join(DATA, 'town-checks-v56.json'), 'w'), indent=1)
    G.export_blockout(T, t, steps, vstats, gates, os.path.join(DATA, f'blockout{SUF}.json'))
    bj = json.load(open(os.path.join(DATA, f'blockout{SUF}.json')))
    bj['version'] = (REVISION + ' prospective city-coherence revision (29 Oct)' if REVISION == 'v56' else
                     'v5.3 block-out, v55 (world plan v5.3; the continent with room for its towns, 27 Oct)')
    bj['v53'] = {'circle': list(V.CIRCLE), 'crossroads': list(V.CROSSROADS),
                 'craters': {nm: {k: v for k, v in c.items() if k in ('x', 'y', 'radius_px', 'region', 'scorch_tip', 'scorch_heading_deg', 'trail_to')}
                             for nm, c in T['craters'].items()},
                 'new_routes': list(V.NEW_ROUTES), 'poi': {nm: [x, y, k] for nm, (x, y, k, _) in V.POI53.items()},
                 'waystones': {nm: [x, y, s] for nm, (x, y, s) in V.WAYSTONES.items()}, 'built': {nm: list(b) for nm, b in V.BUILT.items()},
                 'act1': [[nm, list(p), what] for nm, p, what in V.ACT1]}
    bj['v54'] = stats['v54']
    v55 = dict(stats[REVISION])
    v55['settlement_footprints'] = {nm: {'buildings': r['buildings'], 'streets': r['streets'], 'squares': r['squares'], 'outskirts': r['outskirts'],
                                         'size': r['size'], 'buildings_counted': r['buildings_counted']} for nm, r in town_rec.items()}
    v55['closed_routes'] = {'the Northway (closed)': {'polyline': [[int(round(x)), int(round(y))] for x, y in T['route_px']['the Northway (closed)']],
                                                      'closed': True, 'closed_for': ['movement', 'navigation', 'travel'], 'way': 'C1'}}
    v55['old_forest'] = T.get('forest')
    bj[REVISION] = v55
    with open(os.path.join(DATA, f'blockout{SUF}.json'), 'w') as f:
        json.dump(bj, f, separators=(',', ':'))
    write_plans(S)
    pickle.dump(state, open(os.path.join(HERE, f'state{SUF}.pkl'), 'wb'), protocol=4)
    return state


def write_plans(S):
    """towns/<id>.json: each plan, its terrain grid taken from the finished ground (so the checker sees what the map shows)."""
    import town_plans as TP
    T = S['T']; K = T['K']
    d = os.path.join(DATA, PLAN_DIRECTORY); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.json'):
            os.remove(os.path.join(d, f))
    for pid, P in S['plans'].items():
        c0, r0, w, h = P['terrain']['box_cells']
        P['terrain']['rows'] = TP.terrain_rows(K[r0:r0 + h, c0:c0 + w])
        with open(os.path.join(d, f'{pid}.json'), 'w') as f:
            json.dump(P, f, indent=1)


def map_state(S):
    T = S['T']; K = T['K']
    kinds = sorted(set(K.ravel().tolist())); idx = {k: i for i, k in enumerate(kinds)}
    codes = np.vectorize(idx.get, otypes=[np.int16])(K)
    real = np.clip(g.colour(T, K), 0, 255).astype(np.uint8)
    return {'kinds': kinds, 'K': codes, 'h': T['h'].astype(np.float32), 'land': T['land'], 'sea': T['sea'], 'tiers': S['t'].astype(np.int16),
            'frame': T['FRAME'], 'route_px': {nm: v for nm, v in T['route_px'].items() if nm in g.ROUTES}, 'river_px': T['river_px'],
            'closed_px': T['route_px']['the Northway (closed)'], 'delta': T['delta'], 'real': real,
            'routes': {nm: (kind, feats) for nm, (pts, kind, feats) in g.ROUTES.items()}, 'crater_mask': T['crater_mask'],
            'craters': T['craters'], 'stats_home': S['res'], 'hero': S['stats']['v53']['hero'], 'towns': S['town_rec'],
            'farms': S['stats'][REVISION]['farms'], 'closed': CLOSED, 'dims': (NEW_W, NEW_H), 'plans': S['plans'],
            'mat': T.get('mat'), 'materials': __import__('town_plans').MATERIALS,
            'forest': T.get('forest'),
            'revision': REVISION, 'plan_directory': PLAN_DIRECTORY,
            'physical_checks': S['stats'][REVISION].get('physical_checks') if REVISION == 'v56' else None,
            'tables': {'SETTLE': dict(g.SETTLE), 'STATIONS': dict(g.STATIONS), 'SHORTCUTS': list(g.SHORTCUTS), 'BRIDGES': dict(g.BRIDGES),
                       'CIRCLE': V.CIRCLE, 'CROSSROADS': V.CROSSROADS, 'CRATERS': dict(V.CRATERS), 'POI53': dict(V.POI53),
                       'WAYSTONES': dict(V.WAYSTONES), 'BUILT': dict(V.BUILT), 'ACT1': list(V.ACT1), 'PEAK_NAMES': list(V54.PEAK_NAMES),
                       'PASSES': dict(V54.PASSES), 'GLACIERS': dict(V54.GLACIERS), 'BUTTES': dict(V54.BUTTES), 'SALT_FLATS': dict(V54.SALT_FLATS),
                       'DRY_BEDS': dict(V54.DRY_BEDS), 'INSET': V54.INSET, 'THRESHOLDS': dict(G.THRESHOLDS), 'LIFTS': dict(G.LIFTS)}}


def restore_tables(state):
    """For RENDER_ONLY: the warped tables back into the modules (they are module state)."""
    tb = state['tables']
    set_dims(*state['dims'])
    g.SETTLE.clear(); g.SETTLE.update(tb['SETTLE']); g.STATIONS.clear(); g.STATIONS.update(tb['STATIONS'])
    g.SHORTCUTS[:] = tb['SHORTCUTS']; g.BRIDGES.clear(); g.BRIDGES.update(tb['BRIDGES'])
    V.CIRCLE = tb['CIRCLE']; V.CROSSROADS = tb['CROSSROADS']
    for name in ('CRATERS', 'POI53', 'WAYSTONES', 'BUILT'):
        getattr(V, name).clear(); getattr(V, name).update(tb[name])
    V.ACT1[:] = tb['ACT1']; V54.PEAK_NAMES[:] = tb['PEAK_NAMES']
    for name in ('PASSES', 'GLACIERS', 'BUTTES', 'SALT_FLATS', 'DRY_BEDS'):
        getattr(V54, name).clear(); getattr(V54, name).update(tb[name])
    V54.INSET = tb['INSET']; G.THRESHOLDS.clear(); G.THRESHOLDS.update(tb['THRESHOLDS']); G.LIFTS.clear(); G.LIFTS.update(tb['LIFTS'])


# the module-level names map55 reads (as geo54's are read by map54)
CIRCLE, CROSSROADS = V.CIRCLE, V.CROSSROADS


def sync_names():
    """map55 reads the tables through this module, as map54 read them through geo54."""
    M = sys.modules[__name__]
    for nm in ('CIRCLE', 'CROSSROADS', 'CRATERS', 'POI53', 'WAYSTONES', 'BUILT', 'ACT1'):
        setattr(M, nm, getattr(V, nm))
    for nm in ('SNOWLINE', 'PEAK_NAMES', 'PASSES', 'NOTCH_PX', 'GLACIERS', 'WIND_FROM_DEG', 'DUNES', 'BUTTES', 'SALT_FLATS', 'DRY_BEDS', 'EDGES',
               'LABEL_TIERS', 'INSET'):
        setattr(M, nm, getattr(V54, nm))


if __name__ == '__main__':
    if os.environ.get('RENDER_ONLY'):
        state = pickle.load(open(os.path.join(HERE, f'state{SUF}.pkl'), 'rb'))
        restore_tables(state)
    else:
        S = data_stage()
        sync_names()
        state = write_data(S)
    sync_names()
    if os.environ.get('QUICK') != 'data':
        import map55
        map55.render_all(state, sys.modules[__name__])
    if REVISION == 'v56':
        checks = state.get('physical_checks') or {}
        if not checks or any(not q['pass'] for q in checks.values()):
            print('FAIL v56: physical checks incomplete or failing; see town-checks-v56.json')
            sys.exit(1)
