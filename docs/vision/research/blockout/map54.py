"""The v54 overview map, drawn from geo54.py's state (README.md, "v54"); v53's map (map53.py) with:

- the northern range: peaks drawn as a range in the map's oblique style (each lit on its west face and shaded on its
  east, as the trees and peak marks are), heights from the height field, snow above one snowline, glaciers in the high
  valleys between them with crevasse strokes, notches where routes cross (no peak near a route, the crest dipping toward
  each pass), foothills stepping down to the Frostline and the forests, the highest peak in each stretch named, and a
  cloud bank along the top so the range frames the map;
- the desert: transverse dunes under one wind (crest lines, lit stoss faces, shaded lee faces to the south-south-east),
  tall in the dune sea and low on the sand sheet; mesas and buttes with strata faces and cast shadows; salt flats with
  a crack pattern; dry riverbeds to the oasis; sand, scrub and steppe blended over a wide edge;
- biome edges a little clearer: forest rims, the moor's heather tint and edge, the ash's rim and fall-off, the fens'
  marsh pattern, the Lull's flood line;
- a clean frame (cloud and sea margins in place of the stretched blur), a label hierarchy, and the home valley inset.

Called by geo54.py (render_all, features); not run on its own."""
import json, math, os
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import geo5 as g
import geo52 as G
import map53 as M53
from map53 import load_palette, hexc, mix, fonts, polyline, rail_lines, draw_lines, Placer, around, icon, rotated, act1_path
from geo5 import H, W, CELL, chaikin, densify, WPX, HPX, noise, shape

BASE_W, BASE_H = 1920, 1080
HI = 5                                     # hi-res pixels per 8 px cell, before resampling
FOREST = ('broadleaf', 'conifer', 'oldforest', 'carr')
DRY = ('erg', 'desert', 'scrub', 'steppe')
ROCKY = {'crag', 'cliff', 'talus', 'moraine', 'scree', 'scree2', 'barren', 'snow', 'alpine', 'boulders', 'tor'}
WATERK = {'river', 'creek', 'canal', 'oxbow', 'tarn', 'mere', 'rapids', 'falls', 'channel', 'pool', 'lake', 'sea', 'surf'}


# ------------------------------------------------------------------------------------------ ground classes
def classes(R):
    C = M53.classes(R)
    C['desert'] = (['desert', 'dunewall'], R['sand'][4])
    C['wash'] = (['wash'], R['sand_warm'][5])
    C['heath'] = (C['heath'][0], mix(R['dusk_cool'][4], R['grass'][3], 0.62))          # a touch more heather
    C['wetgrass'] = (C['wetgrass'][0], mix(R['grass_cool'][3], R['water_warm'][4], 0.14))  # the floodplain a little cooler
    C['salt'] = (['saltpan'], R['snow_warm'][5])
    return C


def class_grid(S, R, M):
    C = classes(R); names = list(C); cid = {n: i for i, n in enumerate(names)}
    k2c = {k: cid[n] for n, (ks, _) in C.items() for k in ks}
    kinds = S['kinds']
    lut = np.full(len(kinds), cid['meadow'], np.int16)
    for i, k in enumerate(kinds):
        lut[i] = -1 if k in ('sea', 'surf') else (-2 if k in M53.ROUTE_KINDS else k2c.get(k, cid['meadow']))
    cg = lut[S['K']]
    cg[~S['land']] = -1
    rm = cg == -2
    if rm.any():
        _, (iy, ix) = ndi.distance_transform_edt(rm, return_indices=True); cg = cg[iy, ix]
    sm_ids = [cid[n] for n in M53.SMOOTH if n in cid]
    natural = np.isin(cg, sm_ids)
    votes = np.stack([ndi.uniform_filter((cg == i).astype(np.float32), 5) for i in sm_ids])
    best = np.array(sm_ids, np.int16)[np.argmax(votes, axis=0)]
    cg = np.where(natural & (votes.max(axis=0) > 0.34), best, cg)
    # v54's drawn additions: buttes and the small salt pans, only on open dry ground
    open_dry = np.isin(cg, [cid[n] for n in DRY + ('badland',)])
    for i, (nm, (x, y, r)) in enumerate(M.BUTTES.items()):
        cg[shape(x, y, r, r * 0.85, 7100 + i, 0.25) & open_dry] = cid['mesa']
    for i, (nm, (x, y, rx, ry)) in enumerate(M.SALT_FLATS.items()):
        cg[shape(x, y, rx, ry, 7200 + i, 0.4) & open_dry] = cid['salt']
    cols = np.array([C[n][1] for n in names], np.float32)
    return cg, names, cid, cols


def cell_colours(S, R, cg, cid, cols, realistic=False):
    land = S['land']
    if realistic:
        return S['real'].astype(np.float32)
    rgb = np.zeros((H, W, 3), np.float32)
    okm = cg >= 0
    rgb[okm] = cols[cg[okm]]
    # sand, scrub and steppe blend over a wide edge (normalised blur inside the dry classes only)
    dry = np.isin(cg, [cid[n] for n in DRY])
    num = np.stack([ndi.gaussian_filter(rgb[..., c] * dry, 4.5) for c in range(3)], -1)
    den = ndi.gaussian_filter(dry.astype(np.float32), 4.5)[..., None]
    rgb = np.where(dry[..., None], num / np.maximum(den, 1e-3), rgb)
    nz = ndi.gaussian_filter(np.random.default_rng(5).standard_normal((H, W)).astype(np.float32), 6) * 6
    rgb[okm] *= (1 + 0.012 * nz[okm])[:, None]
    fr = S['frame'] & land
    rgb[fr] = rgb[fr] * 0.88 + np.array(R['plaster'][2], np.float32) * 0.12
    return rgb


def sea_colours(S, R):
    land = S['land']
    dsea = ndi.distance_transform_edt(~land) * CELL
    bands = [(90, R['water_warm'][4]), (260, R['water_warm'][3]), (600, R['water'][3]), (1100, R['water'][2]), (1e9, R['water'][1])]
    sea_rgb = np.zeros((H, W, 3), np.float32); prev = np.zeros((H, W), bool)
    for lim, c in bands:
        m = (dsea < lim + 25 * g.noise(160, 801)) & ~prev & ~land
        sea_rgb[m] = c; prev |= m
    return sea_rgb


# ------------------------------------------------------------------------------------------ the northern range
_FEAT = {}


def features(S, M):
    """The range's glyphs (peaks and foothills), named peaks, passes, glaciers, and the desert's buttes and pans, in world px.
    Deterministic; cached per state."""
    key = id(S)
    if key in _FEAT:
        return _FEAT[key]
    kinds = S['kinds']; K = S['K']; land = S['land']; fr = S['frame']
    kind_of = np.array(kinds, dtype=object)
    h = ndi.gaussian_filter(S['h'].astype(np.float32), 1.2)
    yy, xx = np.mgrid[0:H, 0:W]; Xw = (xx + 0.5) * CELL; Yw = (yy + 0.5) * CELL
    east = np.clip((Xw - 7600) / 2400.0, 0, 1)
    m = h + (0.24 + 0.16 * east) * np.clip(1 - Yw / (1000.0 - 250 * east), 0, 1)     # the range closes the whole north edge
    relief = m - ndi.gaussian_filter(m, 7)                                           # > 0 on ridges and shoulders, < 0 in valleys
    Kk = kind_of[K]
    water = np.isin(Kk, list(WATERK))
    ice = np.isin(Kk, ['glacier', 'crevasse'])
    rocky_north = np.isin(Kk, ['crag', 'talus', 'moraine']) & (Yw < 2300)
    zone = land & (Yw < 2400) & (fr | rocky_north) & ~water
    # keep clear: routes, rivers, ice, settlements, craters, places
    clear = np.zeros((H, W), bool)
    for nm, pts in S['route_px'].items():
        clear |= g.line_mask(pts, 2 * 70)
    d_water = ndi.distance_transform_edt(~water) * CELL
    d_ice = ndi.distance_transform_edt(~ice) * CELL
    clear |= (d_water < 30) | (d_ice < 24) | S['crater_mask']
    for nm, (x, y, r, kind) in g.SETTLE.items():
        if nm not in ('Home valley', 'the Frostline'):
            clear |= np.hypot(Xw - x, Yw - y) < r + 60
    clear |= np.hypot(Xw - 6220, Yw - 1800) < 150                                   # the tarn's bowl stays open
    for nm, (x, y, kind, _) in M.POI53.items():
        clear |= np.hypot(Xw - x, Yw - y) < 70
    ok = zone & ~clear
    dip = np.ones((H, W), np.float32)
    for nm, (x, y, rn, way, why) in M.PASSES.items():
        dp = np.hypot(Xw - x, Yw - y)
        ok &= dp > M.NOTCH_PX
        dip = np.minimum(dip, 0.4 + 0.6 * np.clip((dp - M.NOTCH_PX) / 450.0, 0, 1))
    ice_cnt = ndi.uniform_filter(ice.astype(np.float32), 9)                          # ice share round a point (72 px)
    rng = np.random.default_rng(54)
    cands = []
    step = 30
    for yw in np.arange(step / 2, 2400, step):
        for xw in np.arange(step / 2 + (step / 2 if int(yw / step) % 2 else 0), WPX, step):
            jx, jy = xw + rng.uniform(-11, 11), yw + rng.uniform(-11, 11)
            cx, cy = int(jx / CELL), int(jy / CELL)
            if not (0 <= cx < W and 0 <= cy < H) or not ok[cy, cx]:
                continue
            mv = float(m[cy, cx]); dv = float(dip[cy, cx]); rv = float(relief[cy, cx]); under = Kk[cy, cx]
            # the ice lies in the valleys: no peak whose body would cover it (its box runs north of the foot)
            cy_up = max(0, cy - 12)
            if float(ice_cnt[cy_up:cy + 1, max(0, cx - 4):cx + 5].max()) > 0.2:
                continue
            if mv > 0.62 and rv > -0.012:
                ridge = float(np.clip(rv / 0.05, 0, 1))
                ht = (70 + 300 * min(1.0, (mv - 0.62) / 0.5)) * (0.7 + 0.5 * ridge) * dv * rng.uniform(0.8, 1.2)
                v = rng.choice(['single', 'single', 'twin', 'broad'])
                w_ = ht * {'single': rng.uniform(0.95, 1.25), 'twin': rng.uniform(1.35, 1.6), 'broad': rng.uniform(1.6, 1.9)}[v] + 30
                cands.append(dict(kind='peak', v=str(v), x=float(jx), y=float(jy), ht=ht, w=w_, e=mv, skew=rng.uniform(-0.16, 0.16),
                                  j1=rng.uniform(-0.1, 0.1), j2=rng.uniform(-0.1, 0.1), j3=rng.uniform(0, 1), under=str(under)))
            elif 0.5 < mv <= 0.66 and rv > -0.02 and fr[cy, cx] and under not in ('broadleaf', 'conifer', 'wild', 'ancient', 'thicket', 'snow', 'glacier'):
                ht = (26 + 50 * (mv - 0.5) / 0.16) * dv * rng.uniform(0.85, 1.15)
                cands.append(dict(kind='hill', v='hill', x=float(jx), y=float(jy), ht=ht, w=ht * rng.uniform(2.4, 3.0), e=mv,
                                  skew=rng.uniform(-0.1, 0.1), j1=0.0, j2=0.0, j3=0.0, under=str(under)))
    cands.sort(key=lambda c: -c['ht'])
    grid = {}; kept = []
    for c in cands:
        r_ = c['w'] * (0.36 if c['kind'] == 'peak' else 0.6)
        gx_, gy_ = int(c['x'] // 120), int(c['y'] // 120); hit = False
        for ddx in (-2, -1, 0, 1, 2):
            for ddy in (-2, -1, 0, 1, 2):
                for o in grid.get((gx_ + ddx, gy_ + ddy), ()):
                    if math.hypot(o['x'] - c['x'], (o['y'] - c['y']) * 1.4) < max(r_, o['w'] * 0.3) * (0.75 if o['kind'] != c['kind'] else 1.0):
                        hit = True; break
                if hit:
                    break
            if hit:
                break
        if not hit:
            kept.append(c); grid.setdefault((gx_, gy_), []).append(c)
    kept.sort(key=lambda c: c['y'])
    for c in kept:
        c['apex_e'] = c['e'] + 0.0011 * c['ht']
        if c['kind'] == 'peak' and c['apex_e'] > M.SNOWLINE:
            c['snow'] = float(np.clip((c['apex_e'] - M.SNOWLINE) / max(c['apex_e'] - c['e'], 1e-3), 0.12, 0.5))
        else:
            c['snow'] = 0.0
    # named peaks: the tallest in each stretch
    named = {}
    bands = M.PEAK_NAMES + [(WPX + 1, None)]
    for (x0, nm), (x1, _) in zip(bands, bands[1:]):
        pk = [c for c in kept if c['kind'] == 'peak' and x0 <= c['x'] < x1 and c['y'] - c['ht'] > 260 and 700 < c['y'] < 2000]
        pk = pk or [c for c in kept if c['kind'] == 'peak' and x0 <= c['x'] < x1 and c['y'] - c['ht'] > 150 and c['y'] > 350]
        if pk:
            c = max(pk, key=lambda c: (c['apex_e'], c['ht']))
            c['name'] = nm; c['ht'] *= 1.12
            named[nm] = {'x': round(c['x']), 'y': round(c['y']), 'apex_y': round(c['y'] - c['ht']), 'h': round(c['apex_e'], 3),
                         'snow_cap': round(c['snow'], 2)}
    # glaciers: the ice body nearest each named point
    lab, n = ndi.label(ice)
    gl = {}
    for nm, (x, y, why) in M.GLACIERS.items():
        if n == 0:
            continue
        sizes = ndi.sum(ice, lab, range(1, n + 1)); com = ndi.center_of_mass(ice, lab, range(1, n + 1))
        best = min(range(n), key=lambda i: math.hypot((com[i][1] + 0.5) * CELL - x, (com[i][0] + 0.5) * CELL - y) - 0.02 * sizes[i])
        cy, cx = com[best]
        gl[nm] = {'x': round((cx + 0.5) * CELL), 'y': round((cy + 0.5) * CELL), 'area_cells': int(sizes[best]), 'why': why}
    passes = {nm: {'x': x, 'y': y, 'route': rn, 'way': way, 'why': why} for nm, (x, y, rn, way, why) in M.PASSES.items()}
    # buttes and pans: where they landed (they are drawn only on open dry ground)
    cgk = None
    rr = {'peaks': sum(1 for c in kept if c['kind'] == 'peak'), 'foothills': sum(1 for c in kept if c['kind'] == 'hill'),
          'snowcapped': sum(1 for c in kept if c['snow'] > 0)}
    out = {'glyphs': kept, 'named_peaks': named, 'passes': passes, 'glaciers': gl, 'range': rr, 'm': m,
           'buttes': {nm: {'x': x, 'y': y, 'r': r, 'route_px': round(route_dist(S, x, y))} for nm, (x, y, r) in M.BUTTES.items()},
           'salt_flats': {nm: {'x': x, 'y': y, 'rx': rx, 'ry': ry} for nm, (x, y, rx, ry) in M.SALT_FLATS.items()}}
    _FEAT[key] = out
    return out


def route_dist(S, x, y):
    best = 1e9
    for nm, pts in S['route_px'].items():
        px, py, _, _ = densify(pts, 16)
        best = min(best, float(np.min(np.hypot(px - x, py - y))))
    return best


# ------------------------------------------------------------------------------------------ the base, at any scale
def up_lin(a, f):
    return ndi.zoom(a, f, order=1)


def hash01(ix, iy):
    v = np.sin(ix * 12.9898 + iy * 78.233) * 43758.5453
    return v - np.floor(v)


def base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, box, ppc, realistic=False):
    """The land in the cell box (cx0, cy0, cx1, cy1) at ppc px a cell: biome blocks, soft-grid tiers with south faces, light,
    the sea; and v54's dunes, salt cracks, mesa faces and shadows, glacier edges and biome rims (drawn at HI px a cell, then
    resampled)."""
    cx0, cy0, cx1, cy1 = box
    land = S['land']; h = S['h'].astype(np.float32)
    col = np.where(land[..., None], rgb, sea_rgb) if not realistic else rgb
    t = S['tiers'].astype(np.int32)
    mt = np.where(t <= 12, t, 12 + (t - 12) // 3)
    mt = np.where(land, mt, -1).astype(np.int16)
    hs = ndi.gaussian_filter(h, 2.0); gy, gx = np.gradient(hs)
    lit = np.clip(1.0 - (gx + gy) * (22.0 + 40.0 * np.clip(hs - 0.45, 0, 1)), 0.72, 1.22)
    lit = np.where(land, lit, 1.0).astype(np.float32)
    F = features(S, M)
    zone = F['m'] > 0.5
    zone &= (np.arange(H)[:, None] * CELL < 2400) & S['frame']
    lit = np.where(zone, 1.0 + 0.35 * (lit - 1.0), lit)              # under the range the peaks carry the light; the floor stays calm
    mesa_c = cg == cid['mesa']
    zone_flat = zone | ndi.binary_dilation(mesa_c, iterations=3)
    # dune fields: one wind from the north-north-west; crests across it
    a = math.radians(M.WIND_FROM_DEG)
    Dx, Dy = -math.sin(a), math.cos(a)                     # downwind unit vector (blowing toward the south-south-east)
    warp = 70 * noise(520, 7001) + 26 * noise(170, 7002, 2)
    amp = np.clip(0.75 + 0.7 * noise(420, 7003), 0.15, 1.0)
    ids = {n: cid[n] for n in ('erg', 'desert', 'salt', 'mesa', 'glacier', 'heath', 'ash', 'wetgrass', 'wash')}
    forest_ids = [cid[n] for n in FOREST]
    Wb, Hb = cx1 - cx0, cy1 - cy0
    out = Image.new('RGB', (int(round(Wb * ppc)), int(round(Hb * ppc))))
    STRIP, OV = 64, 9
    c0, c1 = max(0, cx0 - OV), min(W, cx1 + OV)
    for y0 in range(cy0, cy1, STRIP):
        y1 = min(cy1, y0 + STRIP); a0, a1 = max(0, y0 - OV), min(H, y1 + OV)
        up = lambda arr: np.repeat(np.repeat(arr[a0:a1, c0:c1], HI, 0), HI, 1)
        img = up(col).astype(np.float32)
        land_hi = up(land)
        if not realistic:
            cgh = up(cg)
            Xh = ((np.arange(c0 * HI, c1 * HI) + 0.5) / HI * CELL)[None, :]
            Yh = ((np.arange(a0 * HI, a1 * HI) + 0.5) / HI * CELL)[:, None]
            img *= up(lit)[..., None]
            rnd = np.random.default_rng(1000 + y0).random(cgh.shape)
            # -- dunes
            for kind in ('erg', 'desert'):
                msk = cgh == ids[kind]
                if not msk.any():
                    continue
                par = M.DUNES[kind]; lam = par['wavelength_px']; rel = par['relief']
                wv = up_lin(warp[a0:a1, c0:c1], HI) * (1.0 if kind == 'erg' else 0.6)
                am = up_lin(amp[a0:a1, c0:c1], HI) * rel
                phi = (Xh * Dx + Yh * Dy + wv) / lam
                f = phi - np.floor(phi)
                A = 0.74
                mult = np.where(f < A, 1.0 + 0.075 * (f / A), 0.80 + 0.12 * (f - A) / (1 - A))
                crest = (f >= A - 0.035) & (f < A)
                mult = np.where(crest, 1.13, mult)
                mult = 1 + am * (mult - 1)
                img[msk] *= mult[msk][:, None]
            # -- salt flats: a crack pattern and a crust edge
            msk = cgh == ids['salt']
            if msk.any():
                G_ = 34.0
                ys_, xs_ = np.nonzero(msk)
                px = Xh[0, xs_]; py = Yh[ys_, 0]
                gi = np.floor(px / G_); gj = np.floor(py / G_)
                d1 = np.full(px.shape, 1e9); d2 = np.full(px.shape, 1e9)
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        qi, qj = gi + di, gj + dj
                        qx = (qi + 0.15 + 0.7 * hash01(qi, qj)) * G_; qy = (qj + 0.15 + 0.7 * hash01(qj + 17.0, qi + 3.0)) * G_
                        dd = np.hypot(px - qx, py - qy)
                        d2 = np.where(dd < d1, d1, np.minimum(d2, dd)); d1 = np.minimum(d1, dd)
                crack = (d2 - d1) < 2.2
                vals = img[ys_, xs_]
                vals[crack] = vals[crack] * 0.86
                img[ys_, xs_] = vals
                edge = msk & ~ndi.binary_erosion(msk, iterations=4)
                img[edge] = img[edge] * 0.9 + np.array(R['sand'][3], np.float32) * 0.1
            # -- glaciers: a darker edge, so the ice tongues read between the peaks
            msk = cgh == ids['glacier']
            if msk.any():
                edge = msk & ~ndi.binary_erosion(msk, iterations=2)
                img[edge] = img[edge] * 0.78 + np.array(R['snow_cool'][1], np.float32) * 0.1
            # -- tiers: soft-grid plateaus with south faces (not under the range or round mesas, which are drawn below)
            mt_hi = up(mt); flat = up(zone_flat)
            face = np.zeros(mt_hi.shape, bool)
            for dd in range(1, 11):
                above = np.full_like(mt_hi, -1); above[dd:] = mt_hi[:-dd]
                drop = above - mt_hi
                face |= (drop > 0) & (np.clip(drop * 2 + 2, 4, 10) >= dd)
            face &= ~flat
            img = np.where((face & land_hi)[..., None], img * 0.70 + np.array(ink, np.float32) * 0.08, img)
            img = np.where((face & ~land_hi)[..., None], img * 0.82, img)
            top = np.zeros(mt_hi.shape, bool); top[:-1] = (mt_hi[:-1] > mt_hi[1:]); top &= ~flat
            img = np.where(top[..., None], np.minimum(img * 1.12 + 6, 255), img)
            side = np.zeros(mt_hi.shape, bool); side[:, 1:] = mt_hi[:, 1:] != mt_hi[:, :-1]; side &= ~flat
            img = np.where((side & land_hi)[..., None], img * 0.86, img)
            # -- biome edges (modest): forest rims, the moor's edge, the ash's rim and fall-off, the floodplain's flood line
            fo = np.isin(cgh, forest_ids)
            rim = fo & ~ndi.binary_erosion(fo, iterations=3)
            img[rim] *= 0.80
            he = cgh == ids['heath']
            rim = he & ~ndi.binary_erosion(he, iterations=3)
            img[rim] = img[rim] * 0.84 + np.array(R['dusk_cool'][2], np.float32) * 0.08
            ash = cgh == ids['ash']
            if ash.any():
                rim = ash & ~ndi.binary_erosion(ash, iterations=3)
                img[rim] *= 0.80
                dist = ndi.distance_transform_edt(~ash)
                fringe = (dist > 0) & (dist < 14) & land_hi & (rnd < 0.42 * (1 - dist / 14)) & ~np.isin(cgh, [cid['water'], cid['lava']])
                img[fringe] = img[fringe] * 0.35 + np.array(R['basalt'][3], np.float32) * 0.65
            wg = cgh == ids['wetgrass']
            if wg.any():
                rim = wg & ~ndi.binary_erosion(wg, iterations=2)
                yy_, xx_ = np.mgrid[0:wg.shape[0], 0:wg.shape[1]]
                rim &= ((xx_ + yy_) // 3) % 2 == 0
                img[rim] = img[rim] * 0.6 + np.array(R['grass_cool'][1], np.float32) * 0.4
            # -- mesas and buttes: a lit top, strata faces to the south and a shadow cast to the south-east
            me = cgh == ids['mesa']
            if me.any():
                FH = 20
                face = np.zeros(me.shape, bool); depth = np.zeros(me.shape, np.int16)
                for dd in range(1, FH + 1):
                    sh = np.zeros_like(me); sh[dd:] = me[:-dd]
                    new = sh & ~me & ~face
                    depth[new] = dd; face |= new
                body = me | face
                shadow = np.zeros_like(me); shadow[12:, 16:] = body[:-12, :-16]
                for dd in range(4, 12, 4):
                    s2 = np.zeros_like(me); s2[dd:, int(dd * 1.3):] = body[:-dd, :-int(dd * 1.3)]; shadow |= s2
                shadow &= ~body & land_hi
                img[shadow] *= 0.70
                band = (depth // 5) % 2 == 0
                fc = np.where(band[..., None], np.array(R['clay'][2], np.float32), np.array(R['clay'][1], np.float32))
                lit_face = np.clip(1.08 - 0.25 * (depth / FH), 0.8, 1.1)[..., None]
                img = np.where(face[..., None], fc * lit_face, img)
                foot = face & ~np.vstack([face[1:], np.zeros((1, face.shape[1]), bool)])
                img[foot] = np.array(ink, np.float32) * 0.6 + img[foot] * 0.4
                topc = np.array(R['clay'][4], np.float32)
                img[me] = img[me] * 0.35 + topc * 0.65
                hl = me & ~np.vstack([np.zeros((2, me.shape[1]), bool), me[:-2]])
                hl |= me & ~np.hstack([np.zeros((me.shape[0], 2), bool), me[:, :-2]])
                img[hl] = np.minimum(img[hl] * 1.18 + 10, 255)
            # -- the coast
            coast = land_hi & ~ndi.binary_erosion(land_hi, iterations=1)
            sea_edge = ~land_hi & ndi.binary_dilation(land_hi, iterations=2)
            img = np.where(sea_edge[..., None], img * 0.5 + np.array(R['snow'][5], np.float32) * 0.5, img)
            img = np.where(coast[..., None], img * 0.8, img)
        r0 = (y0 - a0) * HI; r1 = r0 + (y1 - y0) * HI
        q0 = (cx0 - c0) * HI; q1 = q0 + Wb * HI
        crop = np.clip(img[r0:r1, q0:q1], 0, 255).astype(np.uint8)
        strip = Image.fromarray(crop)
        if ppc != HI:
            strip = strip.resize((int(round(Wb * ppc)), int(round((y1 - y0) * ppc))), Image.LANCZOS)
        out.paste(strip, (0, int(round((y0 - cy0) * ppc))))
    return out


# ------------------------------------------------------------------------------------------ marks: trees, dunes, marsh, peaks
def stamps(im, S, R, cg, cid, k, ox, oy, M):
    """Tree, tuft, marsh, crevasse and pebble marks, then the range, on a base image (k px per world px; world (0, 0) at
    (ox, oy))."""
    d = ImageDraw.Draw(im, 'RGBA'); rng = np.random.default_rng(11)
    kk = k / (2160 / HPX)                                           # 1 at the 2x map
    fr = S['frame']
    forest = np.isin(cg, [cid[n] for n in FOREST])
    edge = forest & ~ndi.binary_erosion(forest, iterations=1)

    def cell(x, y):
        wx, wy = (x - ox) / k, (y - oy) / k
        cx, cy = int(wx / CELL), int(wy / CELL)
        if 0 <= cx < W and 0 <= cy < H:
            return cx, cy
        return None
    spec = [('broadleaf', 9, 'round', R['leaf'][4], R['leaf'][1], 4.2), ('oldforest', 10, 'round', R['leaf_cool'][3], R['leaf_cool'][0], 5.5),
            ('carr', 9, 'round', R['leaf_warm'][4], R['leaf_warm'][1], 3.8), ('orchard', 7, 'round', R['leaf_warm'][4], R['leaf_warm'][1], 2.6),
            ('conifer', 8, 'cone', R['leaf_cool'][4], R['leaf_cool'][0], 4.0), ('deadwood', 10, 'snag', R['basalt_warm'][2], R['basalt'][1], 4.0),
            ('wetland', 9, 'reed', R['grass_cool'][1], None, 3.0),
            ('heath', 9, 'dot', R['berry_cool'][3], R['dusk_cool'][2], 1.5), ('steppe', 13, 'tuft', R['grass_warm'][2], None, 2.2),
            ('scrub', 15, 'dot', R['sand_cool'][1], R['cactus'][2], 1.6), ('desert', 34, 'dot', R['sand'][2], None, 1.0),
            ('ash', 14, 'dot', R['basalt'][2], None, 1.4), ('lavastone', 12, 'dot', R['basalt_warm'][2], R['clay_warm'][4], 1.5),
            ('glacier', 8, 'crev', R['snow_cool'][1], None, 2.6), ('wash', 9, 'dot', R['sand'][2], None, 0.9)]
    gy_, gx_ = np.gradient(ndi.gaussian_filter(S['h'].astype(np.float32), 2.0))
    marks = []
    for nm, sp, kind, c1, c2, r in spec:
        if nm not in cid:
            continue
        ci = cid[nm]; sp = sp * kk; r = r * kk
        ys = np.arange(sp / 2, im.height, sp); xs = np.arange(sp / 2, im.width, sp)
        for yi, y in enumerate(ys):
            for x in xs + (sp / 2 if yi % 2 else 0):
                jx, jy = x + rng.uniform(-sp * 0.3, sp * 0.3), y + rng.uniform(-sp * 0.3, sp * 0.3)
                c = cell(jx, jy)
                if c is None or cg[c[1], c[0]] != ci:
                    continue
                cx_, cy_ = c
                faint = fr[cy_, cx_]
                k_ = kind
                cc1, cc2 = c1, c2
                if nm == 'wetland' and (cx_ * CELL > 9700):
                    k_ = 'marsh'
                if kind in ('round', 'cone') and edge[cy_, cx_]:
                    cc1 = mix(c1, c2, 0.35)
                marks.append((jy, jx, k_, cc1, cc2, r * (0.8 if faint else 1.0) * rng.uniform(0.85, 1.15), (gx_[cy_, cx_], gy_[cy_, cx_])))
    marks.sort(key=lambda m: m[0])
    for y, x, kind, c1, c2, r, grad in marks:
        if kind == 'round':
            d.ellipse([x - r + 1 * kk, y - r + 1.6 * kk, x + r + 1 * kk, y + r + 1.6 * kk], fill=c2)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c1)
            d.ellipse([x - r * 0.55, y - r * 0.6, x - r * 0.05, y - r * 0.1], fill=mix(c1, (255, 255, 230), 0.25))
        elif kind == 'cone':
            d.polygon([(x + 1 * kk, y - r * 1.4 + 1.5 * kk), (x + r + 1 * kk, y + r * 0.8 + 1.5 * kk), (x - r + 1 * kk, y + r * 0.8 + 1.5 * kk)], fill=c2)
            d.polygon([(x, y - r * 1.4), (x + r, y + r * 0.8), (x - r, y + r * 0.8)], fill=c1)
            d.polygon([(x, y - r * 1.4), (x, y + r * 0.8), (x - r, y + r * 0.8)], fill=mix(c1, (255, 255, 230), 0.18))
        elif kind == 'snag':
            d.line([(x, y - r), (x, y + r * 0.6)], fill=c1, width=max(1, int(2 * kk))); d.line([(x, y - r * 0.3), (x + r * 0.6, y - r * 0.8)], fill=c1, width=max(1, int(kk)))
        elif kind == 'reed':
            for o in (-2, 0, 2):
                d.line([(x + o * kk, y + r), (x + o * 1.4 * kk, y - r)], fill=c1, width=max(1, int(kk)))
        elif kind == 'marsh':
            wc = R['water_warm'][3]
            d.line([(x - r * 1.3, y + r * 0.5), (x + r * 1.3, y + r * 0.5)], fill=wc, width=max(1, int(1.2 * kk)))
            d.line([(x - r * 0.6, y + r * 1.3), (x + r * 0.9, y + r * 1.3)], fill=wc, width=max(1, int(kk)))
            for o in (-1, 0, 1):
                d.line([(x + o * r * 0.45, y + r * 0.35), (x + o * r * 0.7, y - r * 0.8)], fill=c1, width=max(1, int(kk)))
        elif kind == 'tuft':
            d.line([(x - r, y), (x, y - r)], fill=c1, width=max(1, int(kk))); d.line([(x, y - r), (x + r, y)], fill=c1, width=max(1, int(kk)))
        elif kind == 'dot':
            d.ellipse([x - r, y - r, x + r, y + r], fill=c1 if (c2 is None or rng.random() < 0.7) else c2)
        elif kind == 'crev':
            gx0, gy0 = grad; n_ = math.hypot(gx0, gy0)
            if n_ < 1e-6 or rng.random() < 0.35:
                continue
            ux, uy = -gy0 / n_, gx0 / n_                         # across the ice's flow
            d.line([(x - ux * r, y - uy * r), (x + ux * r, y + uy * r)], fill=c1 + (190,), width=max(1, int(kk)))
    mountains(d, S, R, k, ox, oy, M, np.asarray(im).copy())
    return im


def mountains(d, S, R, k, ox, oy, M, ground):
    """The northern range: peaks and foothills from features(), drawn north to south so the nearer overlap the farther;
    each lit on its west face, shaded on its east, with a cast shadow to the south-east; snow above the snowline."""
    F = features(S, M)
    P = lambda x, y: (x * k + ox, y * k + oy)
    kk = k / (2160 / HPX)
    st = R['stone']; sn = R['snow']; snc = R['snow_cool']
    for c in F['glyphs']:
        X, Y = P(c['x'], c['y']); ht = c['ht'] * k; w = c['w'] * k
        if X + w < -5 or X - w > d.im.size[0] + 5 or Y - ht > d.im.size[1] + 5 or Y < -5:
            continue
        if c['kind'] == 'hill':
            gx0 = int(min(max(X, 0), ground.shape[1] - 1)); gy0 = int(min(max(Y - ht * 0.2, 0), ground.shape[0] - 1))
            col = tuple(int(v) for v in ground[gy0, gx0][:3])        # the hill takes the ground it rises from
            lc, dc = mix(col, (255, 248, 226), 0.10), mix(col, st[1], 0.24)
            n = 16
            pts = [(X - w / 2 + w * i / n + c['skew'] * w * math.sin(math.pi * i / n), Y - ht * math.sin(math.pi * i / n) ** 0.7) for i in range(n + 1)]
            d.polygon([(px + 0.08 * w, py + 0.04 * w) for px, py in pts], fill=st[0] + (45,))
            mid = n // 2
            d.polygon(pts, fill=dc)
            d.polygon(pts[:mid + 1] + [(pts[mid][0] + 0.12 * w, Y)], fill=lc)
            d.line(pts, fill=mix(dc, st[0], 0.4) + (140,), width=max(1, int(round(0.8 * kk))))
            continue
        ax = X + c['skew'] * w; ay = Y - ht
        Lf = (X - w / 2, Y); Rf = (X + w / 2, Y)
        v = c['v']
        if v == 'twin':                                   # two summits on one ridge, the west one higher or the east
            a2x = X + w * (0.22 if c['skew'] < 0 else -0.22); a2y = Y - ht * (0.78 + 0.1 * c['j3'])
            if a2x < ax:
                crest = [Lf, (X - w * 0.38, Y - ht * 0.42), (a2x, a2y), ((a2x + ax) / 2, Y - ht * 0.62), (ax, ay), (X + w * 0.3, Y - ht * (0.48 + c['j2'])), Rf]
            else:
                crest = [Lf, (X - w * 0.3, Y - ht * (0.46 + c['j1'])), (ax, ay), ((a2x + ax) / 2, Y - ht * 0.62), (a2x, a2y), (X + w * 0.38, Y - ht * 0.4), Rf]
        elif v == 'broad':                                # a broad massif: a shouldered summit ridge
            crest = [Lf, (X - w * 0.34, Y - ht * (0.42 + c['j1'])), (X - w * 0.16, Y - ht * 0.78), (ax - w * 0.04, ay + ht * 0.04), (ax, ay),
                     (ax + w * 0.1, ay + ht * 0.08), (X + w * 0.22, Y - ht * 0.7), (X + w * 0.36, Y - ht * (0.4 + c['j2'])), Rf]
        else:
            crest = [Lf, (X - w * 0.3, Y - ht * (0.44 + c['j1'])), (X - w * 0.12 + c['skew'] * w * 0.5, Y - ht * (0.8 + 0.08 * c['j3'])), (ax, ay),
                     (X + w * 0.14 + c['skew'] * w * 0.5, Y - ht * (0.74 + 0.06 * c['j3'])), (X + w * 0.29, Y - ht * (0.5 + c['j2'])), Rf]
        B = (X + w * 0.08 + c['skew'] * w * 0.3, Y)
        Mr = (ax + (B[0] - ax) * 0.45 + w * 0.06, ay + ht * 0.45)
        ia = crest.index((ax, ay))
        d.polygon([(px + 0.16 * w, py + 0.05 * w) for px, py in crest], fill=st[0] + (70,))          # shadow to the south-east
        lit_c = st[4] if c['e'] > 0.72 else mix(st[4], R['grass_cool'][3], 0.3)
        mid_c = mix(st[3], st[2], 0.5)
        d.polygon(crest[ia:] + [B, Mr], fill=st[1])                                                   # east faces in shade
        d.polygon(crest[:ia + 1] + [Mr, B], fill=lit_c)                                               # west faces lit
        # a secondary spur on the lit face, a little darker, for relief
        sp = crest[1]
        d.polygon([sp, (sp[0] + w * 0.1, sp[1] + ht * 0.12), (X - w * 0.18, Y), (X - w * 0.36, Y)], fill=mix(lit_c, mid_c, 0.45))
        d.line([(ax, ay), Mr, B], fill=st[2], width=max(1, int(round(0.8 * kk))))
        f = c['snow']
        if f > 0:
            ys = ay + ht * f
            zz = max(1.5, ht * 0.06)
            left_path = crest[:ia + 1][::-1]; right_path = crest[ia:]
            xl = edge_x(left_path, ys); xr = edge_x(right_path, ys); xm = edge_x([(ax, ay), Mr, B], ys)
            lp = [p for p in left_path if p[1] < ys]; rp = [p for p in right_path if p[1] < ys]
            left = lp[::-1][:0] + [(ax, ay)] + [p for p in lp[1:]] + [(xl, ys)]
            for i in range(1, 3):
                left.append((xl + (xm - xl) * i / 3, ys + (zz if i % 2 else -zz * 0.5)))
            left.append((xm, ys + zz * 0.6))
            right = [(ax, ay), (xm, ys + zz * 0.6)]
            for i in range(1, 3):
                right.append((xm + (xr - xm) * i / 3, ys + (-zz * 0.5 if i % 2 else zz)))
            right += [(xr, ys)] + [p for p in rp[1:]][::-1]
            d.polygon(right, fill=snc[2])
            d.polygon(left, fill=sn[5])
        d.line(crest, fill=st[0] + (170,), width=max(1, int(round(0.9 * kk))))
        if c.get('name'):
            d.line([(ax, ay - 2 * kk), (ax, ay - 7 * kk)], fill=st[0], width=max(1, int(round(kk))))


def edge_x(path, y):
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if min(y0, y1) <= y <= max(y0, y1) and y1 != y0:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return path[-1][0]


# ------------------------------------------------------------------------------------------ vectors: water, dry beds, routes
def water_and_routes(im, S, R, ink, k, ox, oy, M):
    d = ImageDraw.Draw(im, 'RGBA'); P = lambda x, y: (x * k + ox, y * k + oy)
    s = k / (2160 / HPX)
    # dry riverbeds: a pale sandy bed between dotted banks, braided where it widens (the block-out's two and v54's)
    beds = [(nm, S['river_px'][nm]) for nm in ('the Dry Fork', 'Brackens wash') if nm in S['river_px']]
    beds += [(nm, chaikin(pts, 3)) for nm, pts in M.DRY_BEDS.items()]
    for nm, pts in beds:
        x, y, al, tot = densify(pts, 6)
        q = [P(a, b) for a, b in zip(x, y)]
        for i in range(len(q) - 1):
            w = (2.6 + 3.2 * i / len(q)) * s
            d.line([q[i], q[i + 1]], fill=R['sand'][1] + (200,), width=max(1, int(round(w + 2.6 * s))))
        for i in range(len(q) - 1):
            w = (2.6 + 3.2 * i / len(q)) * s
            d.line([q[i], q[i + 1]], fill=R['sand_warm'][5], width=max(1, int(round(w))))
        rng = np.random.default_rng(len(nm))
        for i in range(0, len(q), 3):
            if rng.random() < 0.6:
                X, Y = q[i]; rr = 0.7 * s
                X += rng.uniform(-1.5, 1.5) * s; Y += rng.uniform(-1, 1) * s
                d.ellipse([X - rr, Y - rr, X + rr, Y + rr], fill=R['sand'][1] + (200,))
    wcol = R['water_warm'][3]; wdark = R['water'][2]
    for nm, pts in S['river_px'].items():
        if nm in ('the Dry Fork', 'Brackens wash'):
            continue
        sm = chaikin(pts, 2) if len(pts) < 200 else pts
        base = {'the Lull': 5.0, 'the Rift': 3.0, 'the Glint': 3.4, 'the Sorrel': 2.6, 'the Cog': 2.4}.get(nm, 1.8) * s
        n = len(sm)
        for i in range(0, n - 1):
            w = base * (1 + (1.6 if nm == 'the Lull' else 0.5) * i / n)
            d.line([P(*sm[i]), P(*sm[i + 1])], fill=wdark + (150,), width=int(round(w + 2 * s)))
        for i in range(0, n - 1):
            w = base * (1 + (1.6 if nm == 'the Lull' else 0.5) * i / n)
            d.line([P(*sm[i]), P(*sm[i + 1])], fill=wcol, width=max(1, int(round(w))))
    for arm in S['delta']:
        polyline(d, arm, P, wcol, 3.5 * s)
    order = sorted(S['route_px'].items(), key=lambda kv: {'road': 1, 'bridge': 2, 'bar': 0, 'path': 0}.get(S['routes'][kv[0]][0], 0))
    for pass_ in (0, 1):
        for nm, sm in order:
            kind = S['routes'][nm][0]
            w = {'road': 3.2, 'bridge': 3.2, 'bar': 3.0, 'path': 2.2}[kind] * s
            if nm.startswith('Valley lane'):
                w = 2.0 * s
            if pass_ == 0:
                polyline(d, sm, P, R['path'][1] + (200,), w + 2.2 * s)
            elif kind == 'bar':
                polyline(d, sm, P, R['sand'][5], w, dash=(6 * s, 4 * s))
            else:
                polyline(d, sm, P, R['path'][5] if kind != 'road' else R['plaster'][4], w)
    return im


# ------------------------------------------------------------------------------------------ the frame: clouds and sea margins
def clouds(canvas, S, R, s, land_x0, land_x1, sea_rows):
    """A cloud bank along the top edge and in the side margins (where the land runs on), the sea carried flat into the
    margins where the edge is sea. Light from the upper left: each puff lit on its upper left, shaded lower right."""
    Wc, Hc = canvas.size
    d = ImageDraw.Draw(canvas, 'RGBA'); rng = np.random.default_rng(77)
    puffs = []
    x = -10 * s
    while x < Wc + 20 * s:                                   # the top bank, two rows of uneven puffs
        r = rng.uniform(12, 28) * s
        puffs.append((x, rng.uniform(-8, 7) * s, r))
        if rng.random() < 0.45:
            r2 = rng.uniform(7, 15) * s
            puffs.append((x + rng.uniform(-r, r) * 0.5, rng.uniform(6, 16) * s, r2))
        x += r * rng.uniform(0.7, 1.4)
    for side, xe in (('l', land_x0), ('r', land_x1)):
        y = 0
        while y < Hc:
            r = rng.uniform(9, 28) * s
            yc = y
            row = min(Hc - 1, max(0, int(yc)))
            if not sea_rows[row]:
                off = rng.uniform(-4, 14) * s
                xc = xe - off if side == 'r' else xe + off
                puffs.append((xc, yc, r))
                # a second row out in the margin
                puffs.append((xc + (r * 0.9 if side == 'r' else -r * 0.9), yc + rng.uniform(-6, 6) * s, r * 1.15))
            y += r * rng.uniform(0.85, 1.15)
    for xc, yc, r in puffs:
        d.ellipse([xc - r + 2 * s, yc - r + 3 * s, xc + r + 2 * s, yc + r + 3 * s], fill=R['snow'][1] + (90,))
    for xc, yc, r in puffs:
        d.ellipse([xc - r, yc - r, xc + r, yc + r], fill=R['snow'][3])
    for xc, yc, r in puffs:
        d.ellipse([xc - r * 0.82, yc - r * 0.9, xc + r * 0.55, yc + r * 0.45], fill=R['snow'][4])
    for xc, yc, r in puffs:
        d.ellipse([xc - r * 0.6, yc - r * 0.7, xc + r * 0.1, yc - r * 0.05], fill=R['snow'][5])
    return puffs


def margin_boxes(Wc, Hc, s, land_x0, land_x1):
    return [(0, 0, Wc, 22 * s), (0, 0, land_x0 + 18 * s, Hc), (land_x1 - 18 * s, 0, Wc, Hc)]


# ------------------------------------------------------------------------------------------ labels
REGION_NAMES = M53.REGION_NAMES
BIOME_NAMES = [b for b in M53.BIOME_NAMES if b[0] != 'glaciers']
SMALL_PLACES = [('the woodland', 5800, 2620, 'zone'), ('the garden', 6296, 3088, 'zone'), ('the riverside', 6660, 3080, 'zone'),
                ('the park', 6816, 3648, 'zone'), ('the halt', 5760, 4048, 'station'), ('the tarn', 6200, 1800, 'place'),
                ('the bothy', 6520, 2168, 'hut'), ('the ice caves', 6080, 1660, 'cave'), ('the Saddle House', 6440, 2010, 'shrine'),
                ('high lookout', 5968, 1584, 'view'), ("Old Fang's barrow", 4930, 2980, 'cave'), ('the spur tor', 4990, 1960, 'view'),
                ('drove well', 5064, 3316, 'place'), ('the lighthouse', 6600, 4995, 'tower'), ('the old town', 10176, 4344, 'place'),
                ('the docks', 10300, 4720, 'place'), ('new town', 10900, 4560, 'place'), ('the Skyport', 10920, 5120, 'place'),
                ('Gull Strand', 10520, 5320, 'place'), ('Beacon Isle', 10096, 5440, 'place'), ('the old volcano', 7112, 6216, 'view'),
                ('turtle beach', 6368, 6648, 'place'), ('the sea cave', 6880, 6680, 'cave'), ('the pit head', 7248, 3000, 'place'),
                ('the echo cave', 7596, 1852, 'cave'), ('the oxbow bell', 9450, 3900, 'place'),
                ('the dusty corral', 2988, 2476, 'place'), ('the basalt ring', 2520, 4840, 'place'), ('the reed hides', 8800, 4700, 'view')]
GATES = [('the ridge col', 6230, 2040, 'W2'), ('the Col hut', 6290, 2350, 'W2'), ("Drover's bridge", 4330, 3440, 'W5'),
         ('the Rift viaduct', 4300, 3720, 'W5'), ('the Rift ferry', 4180, 5240, 'W5'), ('the chasm bridge', 2170, 4920, 'W6'),
         ('the crust causeway', 3300, 5560, 'W6'), ('the Millrace cutting', 7650, 2740, 'W3'), ('Lullford swing bridge', 8960, 4310, 'W7'),
         ('the Narrows viaduct', 9030, 2330, ''), ('the Headland stile', 6990, 5300, 'W1'), ('the Shell Bar', 6900, 5900, 'W4'),
         ('the Cog foot', 8530, 3060, 'W3'), ('the Brackens gap', 5200, 3760, ''), ('the Cinder Rise', 2270, 3860, ''),
         ('the Harbour Bridge', 10300, 4990, ''), ('the canal embankment', 9450, 4680, '')]


def in_box(x, y, b):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def labels_layer(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, reserved, mode='main'):
    """Every name on its own transparent layer, none overlapping, by tier: regions, towns and the circle always; craters,
    biomes, named peaks and gates with a way next; small places, passes, water and routes only where space allows (on
    the main map, not inside the inset's box)."""
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    pl = Placer(d, Wc, Hc)
    cream, inkc = R['plaster'][5], ink
    main = mode == 'main'
    inset = M.INSET
    for b in reserved:
        pl.reserve(b)
    FE = features(S, M)
    icons = []
    settle = dict(g.SETTLE); settle.pop('Home valley', None); settle.pop('the Frostline', None)
    settle['Crossroads'] = (M.CROSSROADS[0], M.CROSSROADS[1], 300, 'town')
    for nm, (x, y, r, kind) in settle.items():
        icons.append((nm, x, y, kind if kind in ('city', 'town', 'hilltown') else 'village', 'town', 1))
    icons.append(('the stone circle', M.CIRCLE[0], M.CIRCLE[1], 'circle', 'circle', 1))
    for nm, (x, y, r, region, story) in M.CRATERS.items():
        if nm != 'the Crossroads crater':
            icons.append((nm, x, y, 'crater', 'crater', 2))
    for nm, x, y, w in GATES:
        if main and not w and in_box(x, y, inset):
            continue
        t3 = not w or (main and in_box(x, y, inset) and nm != 'the ridge col')
        icons.append((nm, x, y, 'gate', 'gate3' if t3 else 'gate', 3 if t3 else 2))
    for nm, (x, y, st) in M.WAYSTONES.items():
        icons.append(('waystone: ' + nm, x, y, 'waystone_' + st, 'none', 9))
    for nm, x, y, kind in SMALL_PLACES:
        if main and in_box(x, y, inset):
            continue
        icons.append((nm, x, y, kind, 'place', 3))
    placed_icons = []
    for nm, x, y, kind, cat, tier in icons:
        X, Y = P(x, y)
        if not (0 <= X <= Wc and 0 <= Y <= Hc):
            continue
        r = icon(d, kind, X, Y, s, R, ink)
        pl.reserve((X - r, Y - r, X + r, Y + r)); placed_icons.append((nm, X, Y, r, cat, kind, tier))
    # passes: a saddle mark (two facing brackets) across the route
    for nm, (x, y, rn, way, why) in M.PASSES.items():
        X, Y = P(x, y)
        if not (0 <= X <= Wc and 0 <= Y <= Hc):
            continue
        r = 4.5 * s
        for sgn in (-1, 1):
            bx = X + sgn * 3.2 * s
            box_ = [bx - r, Y - r, bx + r, Y + r]
            d.arc(box_, 300 if sgn < 0 else 120, 60 if sgn < 0 else 240, fill=ink, width=max(1, int(2.6 * s)))
            d.arc(box_, 300 if sgn < 0 else 120, 60 if sgn < 0 else 240, fill=cream, width=max(1, int(1.2 * s)))
        pl.reserve((X - 8 * s, Y - 5 * s, X + 8 * s, Y + 5 * s))
        if nm != 'the ridge col':
            placed_icons.append((nm, X, Y, 8 * s, 'pass', 'pass', 3))
    # named peaks
    for nm, p in FE['named_peaks'].items():
        X, Y = P(p['x'], p['apex_y'])
        if 0 <= X <= Wc and 0 <= Y <= Hc:
            placed_icons.append((nm, X, Y - 4 * s, 3 * s, 'peak', 'peak', 2))
    for nm, x, y, w in GATES:
        if w:
            X, Y = P(x, y); bx, by = X + 5 * s, Y - 9 * s
            b = (bx - 1 * s, by - 5 * s, bx + 14 * s, by + 5 * s)
            if pl.free(b):
                d.rounded_rectangle(b, radius=2 * s, fill=R['berry'][3], outline=ink); d.text(((b[0] + b[2]) / 2, by), w, font=F['way'], fill=cream, anchor='mm'); pl.reserve(b)
    # tier 1: regions, then towns and the circle
    for t, x, y in REGION_NAMES:
        if not main:                                     # the inset names the regions it cuts, inside its edge
            x = min(max(x, inset[0] + 420), inset[2] - 420); y = min(max(y, inset[1] + 140), inset[3] - 220)
            if t == 'THE FROSTLINE':
                x, y = 5560, 1760
            if t in ('THE LULL', 'NEON HARBOUR', 'SUNSTONE REACH', 'THE FIRE COUNTRY', 'TIDEBLOOM ISLES', 'COGSWORTH'):
                continue
        X, Y = P(x, y)
        pl.put((X, Y), t, F['region'], cream, inkc, [(0, 0, 'mm'), (0, -18 * s, 'mm'), (0, 18 * s, 'mm'), (40 * s, 0, 'mm'), (-40 * s, 0, 'mm'),
                                                     (90 * s, 30 * s, 'mm'), (-90 * s, 30 * s, 'mm'), (0, 50 * s, 'mm'), (160 * s, 40 * s, 'mm')],
               stroke=int(3 * s), spacing=3 * s, pad=2 * s, name=t if 0 <= X <= Wc and 0 <= Y <= Hc else False)
    order = sorted(placed_icons, key=lambda p: (p[6], {'circle': -1, 'town': 0, 'crater': 1, 'peak': 2, 'gate': 3, 'pass': 4, 'gate3': 5, 'place': 6, 'none': 9}[p[4]]))
    tier1 = [p for p in order if p[6] == 1]
    rest = [p for p in order if p[6] > 1]

    def name_icon(p, pad, leader):
        nm, X, Y, r, cat, kind, tier = p
        if cat == 'none':
            return
        if cat == 'town':
            font, fill, st = F['town'], cream, inkc
        elif cat == 'circle':
            font, fill, st = F['town'], R['brass'][5], inkc
        elif cat == 'crater':
            font, fill, st = F['place'], R['dusk'][5], R['dusk'][0]
        elif cat in ('gate', 'gate3', 'pass'):
            font, fill, st = F['gate'], R['brass'][5], inkc
        elif cat == 'peak':
            font, fill, st = F['peak'], R['snow'][5], R['stone'][0]
        else:
            font, fill, st = F['place'], R['plaster'][5], inkc
        offs = around(r, s) if cat != 'peak' else [(0, -2 * s, 'mb'), (8 * s, -2 * s, 'lb'), (-8 * s, -2 * s, 'rb'), (0, 12 * s, 'mt')]
        pl.put((X, Y), nm, font, fill, st, offs, stroke=int(2 * s), pad=pad,
               leader=leader, name=nm if tier <= 2 else False)
    for p in tier1:
        name_icon(p, 1, [p[3] + 14 * s, p[3] + 24 * s, p[3] + 36 * s])
    # tier 2: biome names, then craters, peaks and gates with a way
    for t, x, y in BIOME_NAMES:
        X, Y = P(x, y)
        if main or (0 <= X <= Wc and 0 <= Y <= Hc):
            pl.put((X, Y), t, F['biome'], R['snow'][5], mix(ink, R['stone'][1], 0.3), [(0, 0, 'mm'), (0, -14 * s, 'mm'), (0, 14 * s, 'mm'), (30 * s, 0, 'mm'),
                                                                                        (-30 * s, 0, 'mm'), (0, -28 * s, 'mm'), (0, 28 * s, 'mm'),
                                                                                        (60 * s, 0, 'mm'), (-60 * s, 0, 'mm'), (40 * s, 20 * s, 'mm'), (-40 * s, 20 * s, 'mm'),
                                                                                        (0, 42 * s, 'mm'), (0, -42 * s, 'mm'), (90 * s, 10 * s, 'mm'), (-90 * s, 10 * s, 'mm')]
                   + [(rr * s * math.cos(aa), rr * s * 0.6 * math.sin(aa), 'mm') for rr in (50, 75, 100) for aa in np.linspace(0, 2 * math.pi, 12, endpoint=False)],
                   stroke=int(2 * s), spacing=1 * s, pad=1 * s, name=t if (0 <= X <= Wc and 0 <= Y <= Hc) else False)
    for nm, p in FE['glaciers'].items():
        X, Y = P(p['x'], p['y'])
        if 0 <= X <= Wc and 0 <= Y <= Hc:
            pl.put((X, Y), nm, F['water'], R['snow'][5], R['sky'][1], [(0, 0, 'mm'), (0, 12 * s, 'mm'), (0, -12 * s, 'mm'), (24 * s, 0, 'mm'), (-24 * s, 0, 'mm')],
                   stroke=int(2 * s), name=False)
    for p in rest:
        if p[6] == 2:
            name_icon(p, 1, [p[3] + 14 * s, p[3] + 24 * s])
    for p in rest:
        if p[6] >= 3:
            name_icon(p, (3 if main else 1) * s, None if main else [p[3] + 14 * s, p[3] + 24 * s])
    # tier 3: water and routes
    for nm, pts in S['river_px'].items():
        if nm in ('the Dry Fork', 'Brackens wash'):
            continue
        for frac in (0.42, 0.3, 0.58, 0.7, 0.2, 0.5, 0.36, 0.64, 0.8, 0.25, 0.75, 0.12, 0.88):
            q = pts[int(len(pts) * frac)]; X, Y = P(*q)
            if pl.put((X, Y), nm, F['water'], R['sky'][5], R['water'][0], [(0, -9 * s, 'mb'), (0, 9 * s, 'mt'), (12 * s, 0, 'lm'), (-12 * s, 0, 'rm')],
                      stroke=int(2 * s), name=False, pad=2 * s if main else 1):
                break
    for t, x, y in [('the southern sea', 9000, 6300), ('the ria', 10230, 4700)]:
        X, Y = P(x, y); pl.put((X, Y), t, F['water'], R['sky'][5], R['water'][0], [(0, 0, 'mm'), (0, 14 * s, 'mm')], stroke=int(2 * s), name=False)
    for nm, pts in M.DRY_BEDS.items():
        q = pts[len(pts) // 2]; X, Y = P(*q)
        pl.put((X, Y), nm, F['water'], R['sand'][5], R['sand'][0], [(10 * s, 0, 'lm'), (-10 * s, 0, 'rm'), (0, -9 * s, 'mb')], stroke=int(2 * s), name=False, pad=2 * s)
    for nm, sm in S['route_px'].items():
        if nm.startswith('Valley lane') or nm in ('Old Bridges', 'Quay Street', 'Forge Stair', 'Beacon Causeway', 'Harbour Bridge', 'Shell Bar'):
            continue
        mid = sm[len(sm) // 2]
        if main and in_box(mid[0], mid[1], inset):
            continue
        rotated2(pl, lay, sm, P, nm, F['route'], R['path'][5], inkc, s, [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.45, 0.55, 0.35, 0.65, 0.15, 0.85])
    for nm, kind, pts, way in lines:
        label = {'valley train': 'the valley train', 'desert line (Rift viaduct)': 'the desert line', 'maglev (Narrows Viaduct)': 'the maglev',
                 'ferry': 'the isles ferry', 'mine cart (S1)': 'the mine cart', 'coastal steamer (S3)': 'the coastal steamer'}.get(nm, nm)
        rotated2(pl, lay, pts, P, label, F['route'], R['snow'][5] if kind == 'boat' else R['plaster'][5], inkc, s, [0.5, 0.4, 0.6, 0.3, 0.7], italic=True)
    return lay, pl


def rotated2(pl, lay, pts, P, text, font, fill, stroke_fill, s, fracs, italic=False):
    """map53's rotated label, without the fallback leader (tier 3 goes only where it fits)."""
    x, y, al, tot = densify(pts, 6)
    for fr in fracs:
        i = int(fr * (len(x) - 1))
        X0, Y0 = P(x[max(i - 8, 0)], y[max(i - 8, 0)]); X1, Y1 = P(x[min(i + 8, len(x) - 1)], y[min(i + 8, len(x) - 1)])
        ang = math.degrees(math.atan2(Y1 - Y0, X1 - X0))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        if abs(ang) > 80:
            continue
        X, Y = P(x[i], y[i])
        pad = int(3 * s)
        bb = pl.d.textbbox((0, 0), text, font=font, anchor='lt', stroke_width=int(2 * s))
        tile = Image.new('RGBA', (int(bb[2] - bb[0] + 2 * pad), int(bb[3] - bb[1] + 2 * pad)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        td.text((pad - bb[0], pad - bb[1]), text, font=font, fill=fill, stroke_width=int(2 * s), stroke_fill=stroke_fill, anchor='lt')
        if italic:
            tile = tile.transform(tile.size, Image.AFFINE, (1, 0.2, -0.1 * tile.height, 0, 1, 0), Image.BICUBIC)
        rt = tile.rotate(-ang, expand=True, resample=Image.BICUBIC)
        nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
        for side, dist_ in ((-1, 7), (1, 7), (-1, 12), (1, 12)):
            cx, cy = X + nx * side * dist_ * s, Y + ny * side * dist_ * s
            b = (cx - rt.width / 2 + pad, cy - rt.height / 2 + pad, cx + rt.width / 2 - pad, cy + rt.height / 2 - pad)
            if pl.free(b, 2 * s):
                lay.alpha_composite(rt, (int(round(cx - rt.width / 2)), int(round(cy - rt.height / 2))))
                pl.reserve(b); return True
    return False


# ------------------------------------------------------------------------------------------ panels and overlays
def panel_boxes(Wc, Hc, s):
    return [(12 * s, 12 * s, 330 * s, 334 * s), (12 * s, Hc - 150 * s, 560 * s, Hc - 12 * s), (Wc - 120 * s, Hc - 130 * s, Wc - 12 * s, Hc - 12 * s)]


def panels(lay, S, M, R, ink, s, k, Wc, Hc, F, act1=True, title='The continent: overview (v54)'):
    M53.panel_boxes = panel_boxes                         # the legend a little taller: act 1's list fits inside it
    M53.panels(lay, S, M, R, ink, s, k, Wc, Hc, F, act1=act1, title=title)


def inset_mark(d, M, R, ink, P, s):
    x0, y0, x1, y1 = M.INSET
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    polyline(d, pts, P, R['plaster'][5] + (170,), 2.4 * s, dash=(6 * s, 5 * s))
    polyline(d, pts, P, ink + (150,), 1.0 * s, dash=(6 * s, 5 * s))


def overlay_built(S, M, R, ink, s, k, ox, oy, Wc, Hc, F):
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    for nm, (x0, y0, x1, y1) in M.BUILT.items():
        a, b = P(x0, y0), P(x1, y1)
        if 'below' in nm:
            polyline(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], P, R['brass'][5] + (255,), 1.6 * s, dash=(4 * s, 3 * s))
        else:
            d.rectangle([a[0] - 2 * s, a[1] - 2 * s, b[0] + 2 * s, b[1] + 2 * s], outline=R['brass'][2] + (200,), width=int(4 * s))
            d.rectangle([a, b], outline=R['brass'][5] + (255,), width=max(1, int(1.6 * s)), fill=R['brass'][5] + (46,))
    tb = built_tag(P, s)
    d.rounded_rectangle(tb, radius=3 * s, fill=R['brass'][4] + (255,), outline=ink)
    d.text(((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2), 'BUILT NOW', font=F['way'], fill=ink, anchor='mm')
    return lay


def built_tag(P, s):
    x, y = P(5640, 2432)
    return (x + 3 * s, y + 3 * s, x + 59 * s, y + 16 * s)


def act_marks(M, P, s):
    seen = {}; out = []
    for i, (nm, p, what) in enumerate(M.ACT1):
        X, Y = P(*p); X -= 9 * s; Y -= 9 * s
        key = (round(X / (10 * s)), round(Y / (10 * s)))
        off = seen.get(key, 0); seen[key] = off + 1
        out.append((i, X - off * 14 * s, Y))
    return out


def overlay_act1(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, paths):
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    for pts in paths:
        q = [P(*p) for p in pts[::3] + [pts[-1]]]
        x, y, al, tot = densify(q, 1.0)
        for a in np.arange(0, tot, 5.5 * s):
            j = int(np.argmin(np.abs(al - a)))
            d.ellipse([x[j] - 1.6 * s, y[j] - 1.6 * s, x[j] + 1.6 * s, y[j] + 1.6 * s], fill=R['berry'][4] + (255,), outline=R['plaster'][5] + (200,))
    for i, X, Y in act_marks(M, P, s):
        d.ellipse([X - 6.5 * s, Y - 6.5 * s, X + 6.5 * s, Y + 6.5 * s], fill=R['berry'][4] + (255,), outline=ink, width=max(1, int(s)))
        d.text((X, Y), str(i), font=F['num'], fill=R['plaster'][5], anchor='mm')
    return lay


def overlay_ring(S, M, R, ink, s, k, ox, oy, Wc, Hc, F):
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    C = P(*M.CIRCLE)
    for nm, (x, y, r, region, story) in M.CRATERS.items():
        X, Y = P(x, y)
        polyline(d, [(x, y), M.CIRCLE], P, R['plaster'][5] + (110,), 3.6 * s)
        polyline(d, [(x, y), M.CIRCLE], P, R['dusk'][2] + (215,), 1.8 * s, dash=(7 * s, 4 * s))
        d.ellipse([X - 9 * s, Y - 9 * s, X + 9 * s, Y + 9 * s], outline=R['brass'][5] + (210,), width=max(1, int(1.4 * s)))
    for rr, al in ((26, 60), (18, 90), (11, 140)):
        d.ellipse([C[0] - rr * s, C[1] - rr * s, C[0] + rr * s, C[1] + rr * s], fill=R['brass'][5] + (al // 3,))
    return lay


def fonts54(root, s):
    F = fonts(root, s)
    nun = os.path.join(root, 'game', 'addons', 'phantom_camera', 'fonts')
    F['peak'] = ImageFont.truetype(os.path.join(nun, 'Nunito-Black.ttf'), int(round(11 * s)))
    return F


# ------------------------------------------------------------------------------------------ compose and save
def render_scale(S, M, s, base2x, paths, lines, R, ink, real2x=None):
    Wc, Hc = int(BASE_W * s), int(BASE_H * s)
    k = Hc / HPX; ox = Wc / 2 - M.CIRCLE[0] * k; oy = 0
    F = fonts54(M.ROOT, s)
    land_x0 = int(round(ox)); land_x1 = int(round(ox + WPX * k))
    rows = (np.arange(Hc) / k / CELL).astype(int).clip(0, H - 1)
    sea_l = ~S['land'][rows, 0]; sea_r = ~S['land'][rows, W - 1]
    sea_rows = sea_l & sea_r

    def frame_base(b2):
        bimg = b2 if s == 2 else b2.resize((int(b2.width * s / 2), int(b2.height * s / 2)), Image.LANCZOS)
        arr = np.asarray(bimg)
        canvas = np.zeros((Hc, Wc, 3), np.uint8)
        canvas[:] = np.array(R['snow'][3], np.uint8)
        x0 = max(land_x0, 0); w_ = min(arr.shape[1], Wc - x0)
        canvas[:, x0:x0 + w_] = arr[:Hc, :w_]
        # the sea runs on flat into the margins where the edge is sea
        for side, sl, edge_col in (('l', slice(0, x0), arr[:Hc, 0]), ('r', slice(x0 + w_, Wc), arr[:Hc, w_ - 1])):
            seam = sea_l if side == 'l' else sea_r
            band = np.repeat(edge_col[:, None, :], canvas[:, sl].shape[1], 1)
            canvas[:, sl] = np.where(seam[:, None, None], band, canvas[:, sl])
        return Image.fromarray(canvas)
    canvas = frame_base(base2x)
    d = ImageDraw.Draw(canvas, 'RGBA'); P = lambda x, y: (x * k + ox, y * k + oy)
    water_and_routes(canvas, S, R, ink, k, ox, oy, M)
    draw_lines(d, lines, P, R, ink, s)
    clouds(canvas, S, R, s, land_x0, land_x1, np.zeros(Hc, bool) | (sea_l & sea_r))
    inset_mark(d, M, R, ink, P, s)
    d.rectangle([3 * s, 3 * s, Wc - 3 * s, Hc - 3 * s], outline=ink, width=max(1, int(2 * s)))
    d.rectangle([7 * s, 7 * s, Wc - 7 * s, Hc - 7 * s], outline=R['timber'][3], width=max(1, int(s)))
    reserved = panel_boxes(Wc, Hc, s) + margin_boxes(Wc, Hc, s, land_x0, land_x1)
    reserved += [(X - 7 * s, Y - 7 * s, X + 7 * s, Y + 7 * s) for i, X, Y in act_marks(M, P, s)] + [built_tag(P, s)]
    lab, pl = labels_layer(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, reserved)
    pan = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); panels(pan, S, M, R, ink, s, k, Wc, Hc, F)
    built = overlay_built(S, M, R, ink, s, k, ox, oy, Wc, Hc, F)
    act = overlay_act1(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, paths)
    ring = overlay_ring(S, M, R, ink, s, k, ox, oy, Wc, Hc, F)
    out = {}
    base_rgba = canvas.convert('RGBA')
    full = base_rgba.copy()
    for layer in (ring, built, lab, act, pan):
        full.alpha_composite(layer)
    out['full'] = full
    plain = base_rgba.copy(); plain.alpha_composite(lab)
    pan2 = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); panels(pan2, S, M, R, ink, s, k, Wc, Hc, F, act1=False)
    plain.alpha_composite(pan2); out['labels'] = plain
    muted = Image.blend(canvas, Image.new('RGB', (Wc, Hc), R['plaster'][4]), 0.45).convert('RGBA')
    for nm, layer in (('built', built), ('act1', act), ('ring', ring)):
        o = muted.copy(); o.alpha_composite(layer); out['overlay-' + nm] = o; out['layer-' + nm] = layer
    out['layer-labels'] = lab; out['base'] = canvas
    if real2x is not None:
        rc = frame_base(real2x); water_and_routes(rc, S, R, ink, k, ox, oy, M); dd = ImageDraw.Draw(rc, 'RGBA'); draw_lines(dd, lines, P, R, ink, s)
        clouds(rc, S, R, s, land_x0, land_x1, sea_l & sea_r)
        rr = rc.convert('RGBA')
        for layer in (ring, built, lab, act, pan):
            rr.alpha_composite(layer)
        out['realistic'] = rr
    return out, pl.missed


def render_inset(S, M, R, ink, cg, cid, rgb, sea_rgb, lines):
    """The home valley at 4 px a cell (0.5 px a world px, 3.2 times the 1920 map), every name in its box."""
    x0, y0, x1, y1 = M.INSET
    box = (x0 // CELL, y0 // CELL, x1 // CELL, y1 // CELL)
    ppc = 4.0; k = ppc / CELL; s = 1.3
    img = base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, box, ppc)
    ox, oy = -box[0] * CELL * k, -box[1] * CELL * k
    stamps(img, S, R, cg, cid, k, ox, oy, M)
    Wc, Hc = img.size
    F = fonts54(M.ROOT, s)
    P = lambda x, y: (x * k + ox, y * k + oy)
    water_and_routes(img, S, R, ink, k, ox, oy, M)
    d = ImageDraw.Draw(img, 'RGBA'); draw_lines(d, lines, P, R, ink, s)
    built = overlay_built(S, M, R, ink, s, k, ox, oy, Wc, Hc, F)
    tb = (12 * s, 12 * s, 560 * s, 66 * s); rb = (12 * s, Hc - 62 * s, 430 * s, Hc - 12 * s)
    lab, pl = labels_layer(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, [tb, rb, built_tag(P, s)], mode='inset')
    out = img.convert('RGBA'); out.alpha_composite(built); out.alpha_composite(lab)
    dd = ImageDraw.Draw(out)
    paper = R['plaster'][5] + (236,); edge = R['timber'][2]
    dd.rounded_rectangle(tb, radius=6 * s, fill=paper, outline=edge, width=max(1, int(2 * s)))
    dd.text((tb[0] + 12 * s, tb[1] + 10 * s), 'The home valley (v54 inset)', font=F['title'], fill=ink, anchor='lt')
    dd.text((tb[0] + 12 * s, tb[1] + 38 * s), f'world px {x0} to {x1} east, {y0} to {y1} south; 1 px = 2 world px (3.2 times the 1920 map)',
            font=F['small'], fill=R['timber'][2], anchor='lt')
    dd.rounded_rectangle(rb, radius=6 * s, fill=paper, outline=edge, width=max(1, int(2 * s)))
    v = S['hero']['walk_speed_world_px_s']; cpx = 8 * k
    bx, by = rb[0] + 14 * s, rb[1] + 26 * s
    marks = [0, 10, 50, 100]
    for a, b_ in zip(marks, marks[1:]):
        dd.rectangle([bx + a * cpx, by, bx + b_ * cpx, by + 6 * s], fill=ink if marks.index(a) % 2 == 0 else R['plaster'][3], outline=ink)
    for m_ in marks[1:]:
        dd.text((bx + m_ * cpx, by - 3 * s), f'{m_}' + (' cells' if m_ == 100 else ''), font=F['small'], fill=ink, anchor='mb')
        dd.text((bx + m_ * cpx, by + 9 * s), f'{m_ * 8 / v:.0f} s', font=F['small'], fill=R['timber'][2], anchor='mt')
    dd.text((bx + 100 * cpx + 50 * s, by + 3 * s), "Bramble's walk", font=F['small'], fill=ink, anchor='lm')
    dd.rectangle([1, 1, Wc - 2, Hc - 2], outline=ink, width=2)
    return out, pl.missed


def render_all(S, M):
    R, ink = load_palette(M.ROOT)
    cg, names, cid, cols = class_grid(S, R, M)
    rgb = cell_colours(S, R, cg, cid, cols); sea_rgb = sea_colours(S, R)
    k2 = 2160 / HPX
    full = (0, 0, W, H)
    base2x = base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, full, 2.5)
    stamps(base2x, S, R, cg, cid, k2, 0, 0, M)
    real2x = base_hi(S, R, ink, cg, cid, cell_colours(S, R, cg, cid, cols, realistic=True), sea_rgb, M, full, 2.5, realistic=True)
    paths = act1_path(S, M); lines = rail_lines(S)
    outs = [os.environ.get('MAP54_OUT')] if os.environ.get('MAP54_OUT') else []
    outs.append(M.HERE)
    missed_all = {}
    for s, tag in ((1, '1920'), (2, '3840')):
        res, missed = render_scale(S, M, s, base2x, paths, lines, R, ink, real2x)
        missed_all[tag] = missed
        for o in outs:
            os.makedirs(o, exist_ok=True)
            res['full'].convert('RGB').save(os.path.join(o, f'map54-{tag}.png'))
            if s == 1:
                for key in ('labels', 'overlay-built', 'overlay-act1', 'overlay-ring', 'realistic', 'base'):
                    res[key].convert('RGB').save(os.path.join(o, f'map54-{key}-{tag}.png'))
                for key in ('layer-built', 'layer-act1', 'layer-ring', 'layer-labels'):
                    res[key].save(os.path.join(o, f'map54-{key}-{tag}.png'))
        if s == 1:
            small = res['full'].convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            small.save(os.path.join(M.DATA, 'continent-1x-v54.png'), optimize=True)
            v53 = Image.open(os.path.join(M.DATA, 'continent-1x-v53.png')).convert('RGB')
            cmp_ = Image.new('RGB', (1920 * 2 + 24, 1080 + 40), (30, 26, 34)); dc = ImageDraw.Draw(cmp_)
            cmp_.paste(v53, (0, 40)); cmp_.paste(res['full'].convert('RGB'), (1920 + 24, 40))
            Fc = fonts(M.ROOT, 1)
            dc.text((10, 20), 'v53 (overview map, 1920 x 1080)', font=Fc['title'], fill=(240, 230, 210), anchor='lm')
            dc.text((1920 + 34, 20), 'v54 (the range, the desert, biome edges, frame, labels)', font=Fc['title'], fill=(240, 230, 210), anchor='lm')
            for o in outs:
                cmp_.save(os.path.join(o, 'map54-v53-vs-v54.png'))
    ins, missed = render_inset(S, M, R, ink, cg, cid, rgb, sea_rgb, lines)
    missed_all['inset'] = missed
    for o in outs:
        ins.convert('RGB').save(os.path.join(o, 'map54-inset-home-valley.png'))
    ins.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(
        os.path.join(M.DATA, 'inset-home-valley-v54.png'), optimize=True)
    print('labels not placed (tiers 1 and 2):', json.dumps(missed_all))
    print('range:', json.dumps(features(S, M)['range']), json.dumps(features(S, M)['named_peaks']))
    return missed_all
