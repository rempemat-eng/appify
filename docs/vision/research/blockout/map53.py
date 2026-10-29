"""The v53 overview map: a stylised continent in the house palette, drawn from geo53.py's state (README.md, "v53").

The land is drawn as the in-game map would show it (world-plan 12): tiers as soft-grid plateaus with a darker south face
and a thin rim, flat biome blocks with soft-grid edges, tree, peak, dune and reed marks, light from the upper left, the sea
in stepped depth bands. On it: region, biome, place, water and route names; the rail and ferry lines; the gates and their
ways; the waystones; the craters; and three overlays (built zones, act 1's route, the crater ring), a soft-grid scale ruler
and a north arrow. Every layer is written alone and combined, at 1920 x 1080 and at 2x.

Called by geo53.py (render_all); not run on its own."""
import json, math, os
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.graph import MCP_Geometric
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import geo5 as g
import geo52 as G
from geo5 import H, W, CELL, chaikin, densify, WPX, HPX

BASE_W, BASE_H = 1920, 1080
HI = 5                                     # hi-res pixels per 8 px cell, before the 2x map's resample (2.5 px a cell)


# ------------------------------------------------------------------------------------------ palette and fonts
def load_palette(root):
    P = json.load(open(os.path.join(root, 'art', 'house-palette.json')))
    return {k: [hexc(c) for c in v] for k, v in P['ramps'].items()}, hexc(P['ink'])


def hexc(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def fonts(root, s):
    pix = os.path.join(root, 'game', 'ui', 'fonts', 'PixelifySans-Regular.ttf')
    nun = os.path.join(root, 'game', 'addons', 'phantom_camera', 'fonts')
    dv = '/usr/share/fonts/truetype/dejavu/'
    f = lambda path, n: ImageFont.truetype(path, int(round(n * s)))
    return {'region': f(pix, 27), 'biome': f(pix, 16), 'town': f(os.path.join(nun, 'Nunito-Black.ttf'), 14),
            'place': f(os.path.join(nun, 'Nunito-Black.ttf'), 11), 'water': f(dv + 'DejaVuSerif-Italic.ttf', 11),
            'route': f(os.path.join(nun, 'Nunito-Black.ttf'), 10), 'gate': f(os.path.join(nun, 'Nunito-Black.ttf'), 10),
            'num': f(os.path.join(nun, 'Nunito-Black.ttf'), 10), 'small': f(os.path.join(nun, 'Nunito-Regular.ttf'), 11),
            'legend': f(os.path.join(nun, 'Nunito-Black.ttf'), 11), 'title': f(pix, 22), 'way': f(os.path.join(nun, 'Nunito-Black.ttf'), 8)}


# ------------------------------------------------------------------------------------------ ground classes
def classes(R):
    """Map ground kinds (geo5/geo52's K) to the overview's biome blocks and their colours (house ramps)."""
    return {
        'water': (['river', 'creek', 'canal', 'oxbow', 'tarn', 'mere', 'rapids', 'falls', 'channel', 'pool', 'lake'], R['water_warm'][3]),
        'shoal': (['shoal', 'sandbar', 'pointbar'], R['sand'][4]),
        'meadow': (['meadow', 'clearing', 'garden', 'lawn'], R['grass'][3]),
        'wetgrass': (['watermeadow', 'scroll'], R['grass_cool'][3]),
        'field': (['field'], R['grass_warm'][4]), 'field2': (['field2'], mix(R['brass'][5], R['grass_warm'][4], 0.35)),
        'fallow': (['fallow'], R['path'][4]), 'hedge': (['hedge'], R['leaf'][2]), 'orchard': (['orchard'], R['leaf_warm'][3]),
        'broadleaf': (['broadleaf', 'felltree', 'thicket'], R['leaf'][3]), 'conifer': (['conifer'], R['leaf_cool'][2]),
        'oldforest': (['wild', 'ancient'], R['leaf_cool'][1]), 'carr': (['carr'], R['leaf_warm'][2]),
        'deadwood': (['deadwood'], R['basalt_warm'][4]),
        'heath': (['heath', 'gorse', 'bramble'], mix(R['dusk_cool'][4], R['grass'][3], 0.45)),
        'steppe': (['steppe'], mix(R['grass_warm'][4], R['sand'][3], 0.4)),
        'scrub': (['scrub', 'scrubwall', 'caravan'], R['sand_cool'][3]), 'desert': (['desert', 'wash', 'dunewall'], R['sand'][4]),
        'erg': (['erg'], R['sand_warm'][4]), 'salt': (['saltpan'], R['plaster'][5]),
        'badland': (['badland', 'ravine'], R['clay'][4]), 'mesa': (['mesa'], R['clay'][3]),
        'wetland': (['reeds', 'bog', 'sinkhole'], R['grass_cool'][2]), 'mud': (['mud'], R['earth'][3]),
        'alpine': (['alpine', 'tor'], R['grass_cool'][4]),
        'rock': (['barren', 'scree', 'scree2', 'talus', 'moraine', 'boulders'], R['stone'][4]),
        'crag': (['crag', 'cliff', 'wall', 'retain'], R['stone'][2]),
        'snow': (['snow'], R['snow'][4]), 'glacier': (['glacier', 'crevasse'], R['snow_cool'][3]),
        'ash': (['ash'], R['basalt'][4]), 'lavastone': (['lavastone', 'fireweed'], R['basalt_warm'][4]),
        'basalt': (['basalt', 'aa', 'spoil'], R['basalt'][2]), 'blacksand': (['blacksand'], R['basalt'][3]),
        'lava': (['lava', 'fissure', 'crater'], R['clay_warm'][4]),
        'beach': (['sand', 'driftwood'], R['sand'][5]),
        'roof': (['building', 'warehouse', 'hut', 'keep', 'stall', 'fishmarket', 'crane'], R['clay'][3]),
        'tower': (['tower', 'terminal', 'hangar', 'neon'], R['slate'][3]),
        'wallc': (['castlewall'], R['stone'][3]),
        'paved': (['yard', 'plaza', 'lane', 'quay', 'boulevard', 'arcade', 'apron', 'dock', 'pier', 'pad', 'airfield'], R['plaster'][3]),
        'glass': (['shardglass'], R['dusk'][3]), 'craterrim': (['craterrim'], R['dusk'][2]),
        'scorch': (['scorch'], mix(R['dusk'][1], R['basalt'][3], 0.35)), 'circle': (['circle'], R['stone'][5]),
        'farisle': (['farisle'], R['grass_cool'][2]),
    }


ROUTE_KINDS = {'road', 'path', 'stair', 'trail', 'bridge', 'bar', 'viaduct', 'viapier', 'ruinbridge'}
SMOOTH = {'meadow', 'wetgrass', 'broadleaf', 'conifer', 'oldforest', 'carr', 'deadwood', 'heath', 'steppe', 'scrub', 'desert', 'erg',
          'badland', 'wetland', 'alpine', 'rock', 'snow', 'glacier', 'ash', 'lavastone', 'basalt', 'blacksand', 'mud'}


def class_grid(S, R):
    C = classes(R); names = list(C); cid = {n: i for i, n in enumerate(names)}
    k2c = {}
    for n, (ks, _) in C.items():
        for k in ks:
            k2c[k] = cid[n]
    kinds = S['kinds']; K = S['K']
    lut = np.full(len(kinds), cid['meadow'], np.int16); sea_code = -1
    for i, k in enumerate(kinds):
        if k == 'sea' or k == 'surf':
            lut[i] = -1
        elif k in ROUTE_KINDS:
            lut[i] = -2
        else:
            lut[i] = k2c.get(k, cid['meadow'])
    cg = lut[K]
    cg[~S['land']] = -1
    # route cells take the class of the nearest ground beside them (the routes are drawn as lines on top)
    rm = cg == -2
    if rm.any():
        _, (iy, ix) = ndi.distance_transform_edt(rm, return_indices=True); cg = cg[iy, ix]
    # soft-grid blocks: a majority filter on the open natural classes only, so speckle merges into readable biome blocks
    sm_ids = [cid[n] for n in SMOOTH]
    natural = np.isin(cg, sm_ids)
    votes = np.stack([ndi.uniform_filter((cg == i).astype(np.float32), 5) for i in sm_ids])
    best = np.array(sm_ids, np.int16)[np.argmax(votes, axis=0)]
    cg = np.where(natural & (votes.max(axis=0) > 0.34), best, cg)
    cols = np.array([C[n][1] for n in names], np.float32)
    return cg, names, cid, cols


# ------------------------------------------------------------------------------------------ the base map at 2x
def base_2x(S, R, ink, realistic=False):
    """The land at 2.5 px a cell (the 2x map), before labels: biome blocks, soft-grid tiers with south faces, light, sea."""
    cg, names, cid, cols = class_grid(S, R)
    land = S['land']; h = S['h'].astype(np.float32)
    if realistic:
        rgb = S['real'].astype(np.float32)
    else:
        rgb = np.zeros((H, W, 3), np.float32)
        okm = cg >= 0
        rgb[okm] = cols[cg[okm]]
        # gentle variation inside a block: low noise, so blocks stay flat but not dead
        nz = ndi.gaussian_filter(np.random.default_rng(5).standard_normal((H, W)).astype(np.float32), 6) * 6
        rgb[okm] *= (1 + 0.012 * nz[okm])[:, None]
        # the frame (land beyond the walk) a touch hazier
        fr = S['frame'] & land
        rgb[fr] = rgb[fr] * 0.86 + np.array(R['plaster'][2], np.float32) * 0.14
    # the sea in stepped bands by distance from land: shallows, shelf, deep
    dsea = ndi.distance_transform_edt(~land) * CELL
    bands = [(90, R['water_warm'][4]), (260, R['water_warm'][3]), (600, R['water'][3]), (1100, R['water'][2]), (1e9, R['water'][1])]
    sea_rgb = np.zeros((H, W, 3), np.float32); prev = np.zeros((H, W), bool)
    for lim, c in bands:
        m = (dsea < lim + 25 * g.noise(160, 801)) & ~prev & ~land
        sea_rgb[m] = c; prev |= m
    if not realistic:
        rgb = np.where(land[..., None], rgb, sea_rgb)
    # hi-res: 5 px a cell, nearest, then the soft-grid tiers and light; in strips of cell rows, to keep the memory small
    t = S['tiers'].astype(np.int32)
    mt = np.where(t <= 12, t, 12 + (t - 12) // 3)
    mt = np.where(land, mt, -1).astype(np.int16)
    hs = ndi.gaussian_filter(h, 2.0); gy, gx = np.gradient(hs)
    lit = np.clip(1.0 - (gx + gy) * (22.0 + 40.0 * np.clip(hs - 0.45, 0, 1)), 0.72, 1.22)
    lit = np.where(land, lit, 1.0).astype(np.float32)
    out = Image.new('RGB', (int(W * 2.5), int(H * 2.5)))
    STRIP, OV = 96, 4
    for y0 in range(0, H, STRIP):
        y1 = min(H, y0 + STRIP); a0, a1 = max(0, y0 - OV), min(H, y1 + OV)
        up = lambda a: np.repeat(np.repeat(a[a0:a1], HI, 0), HI, 1)
        img = up(rgb)
        if not realistic:
            mt_hi = up(mt); land_hi = up(land)
            img *= up(lit)[..., None]
            face = np.zeros(mt_hi.shape, bool)
            for dd in range(1, 11):
                above = np.full_like(mt_hi, -1); above[dd:] = mt_hi[:-dd]
                drop = above - mt_hi
                face |= (drop > 0) & (np.clip(drop * 2 + 2, 4, 10) >= dd)
            img = np.where((face & land_hi)[..., None], img * 0.70 + np.array(ink, np.float32) * 0.08, img)
            img = np.where((face & ~land_hi)[..., None], img * 0.82, img)
            top = np.zeros(mt_hi.shape, bool); top[:-1] = (mt_hi[:-1] > mt_hi[1:])
            img = np.where(top[..., None], np.minimum(img * 1.12 + 6, 255), img)
            side = np.zeros(mt_hi.shape, bool); side[:, 1:] = mt_hi[:, 1:] != mt_hi[:, :-1]
            img = np.where((side & land_hi)[..., None], img * 0.86, img)
            coast = land_hi & ~ndi.binary_erosion(land_hi, iterations=1)
            sea_edge = ~land_hi & ndi.binary_dilation(land_hi, iterations=2)
            img = np.where(sea_edge[..., None], img * 0.5 + np.array(R['snow'][5], np.float32) * 0.5, img)
            img = np.where(coast[..., None], img * 0.8, img)
        strip = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((int(W * 2.5), int((a1 - a0) * 2.5)), Image.LANCZOS)
        top_px = int((y0 - a0) * 2.5)
        out.paste(strip.crop((0, top_px, strip.width, top_px + int((y1 - y0) * 2.5))), (0, int(y0 * 2.5)))
    return out, cg, names, cid



def stamps(im, S, R, cg, cid, k):
    """Tree, peak, dune, reed and heath marks on the 2x map (k: px per world px)."""
    d = ImageDraw.Draw(im); rng = np.random.default_rng(11)
    cell_px = CELL * k

    def cls_at(x, y):
        cx, cy = int(x / cell_px), int(y / cell_px)
        if 0 <= cx < W and 0 <= cy < H:
            return cg[cy, cx]
        return -9
    fr = S['frame']
    spec = [('broadleaf', 9, 'round', R['leaf'][4], R['leaf'][1], 4.2), ('oldforest', 10, 'round', R['leaf_cool'][3], R['leaf_cool'][0], 5.5),
            ('carr', 9, 'round', R['leaf_warm'][4], R['leaf_warm'][1], 3.8), ('orchard', 7, 'round', R['leaf_warm'][4], R['leaf_warm'][1], 2.6),
            ('conifer', 8, 'cone', R['leaf_cool'][4], R['leaf_cool'][0], 4.0), ('deadwood', 10, 'snag', R['basalt_warm'][2], R['basalt'][1], 4.0),
            ('erg', 18, 'dune', R['sand_warm'][2], None, 6.0), ('wetland', 9, 'reed', R['grass_cool'][1], None, 3.0),
            ('heath', 9, 'dot', R['dusk_cool'][3], R['berry_cool'][4], 1.6), ('steppe', 13, 'tuft', R['grass_warm'][2], None, 2.2),
            ('scrub', 13, 'dot', R['sand_cool'][1], None, 1.6), ('desert', 22, 'dot', R['sand'][2], None, 1.2),
            ('ash', 14, 'dot', R['basalt'][2], None, 1.4), ('lavastone', 12, 'dot', R['basalt_warm'][2], R['clay_warm'][4], 1.5)]
    marks = []
    for nm, sp, kind, c1, c2, r in spec:
        if nm not in cid:
            continue
        ci = cid[nm]
        ys = np.arange(sp / 2, im.height, sp); xs = np.arange(sp / 2, im.width, sp)
        for yi, y in enumerate(ys):
            for x in xs + (sp / 2 if yi % 2 else 0):
                jx, jy = x + rng.uniform(-sp * 0.3, sp * 0.3), y + rng.uniform(-sp * 0.3, sp * 0.3)
                if cls_at(jx, jy) != ci:
                    continue
                cx_, cy_ = int(jx / cell_px), int(jy / cell_px)
                faint = fr[min(cy_, H - 1), min(cx_, W - 1)]
                marks.append((jy, jx, kind, c1, c2, r * (0.8 if faint else 1.0) * rng.uniform(0.85, 1.15)))
    marks.sort(key=lambda m: m[0])
    for y, x, kind, c1, c2, r in marks:
        if kind == 'round':
            d.ellipse([x - r + 1, y - r + 1.6, x + r + 1, y + r + 1.6], fill=c2)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c1)
            d.ellipse([x - r * 0.55, y - r * 0.6, x - r * 0.05, y - r * 0.1], fill=mix(c1, (255, 255, 230), 0.25))
        elif kind == 'cone':
            d.polygon([(x + 1, y - r * 1.4 + 1.5), (x + r + 1, y + r * 0.8 + 1.5), (x - r + 1, y + r * 0.8 + 1.5)], fill=c2)
            d.polygon([(x, y - r * 1.4), (x + r, y + r * 0.8), (x - r, y + r * 0.8)], fill=c1)
            d.polygon([(x, y - r * 1.4), (x, y + r * 0.8), (x - r, y + r * 0.8)], fill=mix(c1, (255, 255, 230), 0.18))
        elif kind == 'snag':
            d.line([(x, y - r), (x, y + r * 0.6)], fill=c1, width=2); d.line([(x, y - r * 0.3), (x + r * 0.6, y - r * 0.8)], fill=c1, width=1)
        elif kind == 'dune':
            d.arc([x - r * 1.6, y - r * 0.6, x + r * 1.6, y + r * 0.9], 200, 340, fill=c1, width=2)
        elif kind == 'reed':
            for o in (-2, 0, 2):
                d.line([(x + o, y + r), (x + o * 1.4, y - r)], fill=c1, width=1)
        elif kind == 'tuft':
            d.line([(x - r, y), (x, y - r)], fill=c1, width=1); d.line([(x, y - r), (x + r, y)], fill=c1, width=1)
        elif kind == 'dot':
            d.ellipse([x - r, y - r, x + r, y + r], fill=c1 if (c2 is None or rng.random() < 0.7) else c2)
    # peaks: the massif's and Mount Ember's summits as stepped triangles, lit from the left
    h = S['h']; land = S['land']
    pk = peak_local_max(np.where(land, ndi.gaussian_filter(h, 2), 0), min_distance=16, threshold_abs=0.66)
    peaks = sorted([(int(y), int(x)) for y, x in pk], key=lambda p: p[0])
    for (cy_, cx_) in peaks:
        hv = float(h[cy_, cx_]); x, y = (cx_ + 0.5) * cell_px, (cy_ + 0.5) * cell_px
        ht = 14 + 26 * min(1.0, (hv - 0.62) / 0.5); wd = ht * 0.95
        if fr[cy_, cx_]:
            ht *= 0.85; wd *= 0.85
        base_c = R['stone'][3] if hv < 0.86 else R['snow_cool'][3]
        d.polygon([(x, y - ht), (x + wd / 2 + 2, y + 2), (x - wd / 2 + 2, y + 2)], fill=R['stone'][0])
        d.polygon([(x, y - ht), (x + wd / 2, y), (x - wd / 2, y)], fill=mix(base_c, R['stone'][1], 0.35))
        d.polygon([(x, y - ht), (x, y), (x - wd / 2, y)], fill=mix(base_c, (255, 255, 240), 0.2))
        if hv > 0.78:
            cap = 0.38
            d.polygon([(x, y - ht), (x + wd / 2 * cap, y - ht * (1 - cap)), (x, y - ht * (1 - cap * 0.7)), (x - wd / 2 * cap, y - ht * (1 - cap))],
                      fill=R['snow'][5])
    return im


# ------------------------------------------------------------------------------------------ vectors: water, routes, lines
def polyline(d, pts, P, fill, width, dash=None, joint=True):
    q = [P(*p) for p in pts]
    if dash is None:
        d.line(q, fill=fill, width=max(1, int(round(width))), joint='curve' if joint else None)
        return
    on, off = dash; acc = 0.0; draw = True
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        L = math.hypot(x1 - x0, y1 - y0); t = 0.0
        while t < L:
            seg = min((on if draw else off) - acc, L - t)
            if draw:
                a = t / L; b = (t + seg) / L
                d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=fill, width=max(1, int(round(width))))
            t += seg; acc += seg
            if acc >= (on if draw else off) - 1e-6:
                acc = 0.0; draw = not draw


def water_and_routes(im, S, R, ink, k, ox, M):
    d = ImageDraw.Draw(im, 'RGBA'); P = lambda x, y: (x * k + ox, y * k)
    s = k / (2160 / HPX)                                                        # 1 at the 2x map
    wcol = R['water_warm'][3]; wdark = R['water'][2]
    for nm, pts in S['river_px'].items():
        if nm in ('the Dry Fork', 'Brackens wash'):
            continue
        sm = chaikin(pts, 2) if len(pts) < 200 else pts
        base = {'the Lull': 5.0, 'the Rift': 3.0, 'the Glint': 3.4, 'the Sorrel': 2.6, 'the Cog': 2.4}.get(nm, 1.8) * s
        n = len(sm)
        for i in range(0, n - 1, 1):
            w = base * (1 + (1.6 if nm == 'the Lull' else 0.5) * i / n)
            d.line([P(*sm[i]), P(*sm[i + 1])], fill=wdark + (150,), width=int(round(w + 2 * s)))
        for i in range(0, n - 1, 1):
            w = base * (1 + (1.6 if nm == 'the Lull' else 0.5) * i / n)
            d.line([P(*sm[i]), P(*sm[i + 1])], fill=wcol, width=max(1, int(round(w))))
    for arm in S['delta']:
        polyline(d, arm, P, wcol, 3.5 * s)
    # routes: a dark edge, then the pale track; roads wider than paths, the Shell Bar dashed on the sand
    order = sorted(S['route_px'].items(), key=lambda kv: {'road': 1, 'bridge': 2, 'bar': 0, 'path': 0}.get(S['routes'][kv[0]][0], 0))
    for nm, sm in order:
        kind = S['routes'][nm][0]
        w = {'road': 3.2, 'bridge': 3.2, 'bar': 3.0, 'path': 2.2}[kind] * s
        if nm.startswith('Valley lane'):
            w = 2.0 * s
        polyline(d, sm, P, R['path'][1] + (200,), w + 2.2 * s)
    for nm, sm in order:
        kind = S['routes'][nm][0]
        w = {'road': 3.2, 'bridge': 3.2, 'bar': 3.0, 'path': 2.2}[kind] * s
        if nm.startswith('Valley lane'):
            w = 2.0 * s
        if kind == 'bar':
            polyline(d, sm, P, R['sand'][5], w, dash=(6 * s, 4 * s))
        else:
            polyline(d, sm, P, R['path'][5] if kind != 'road' else R['plaster'][4], w)
    return im


def rail_lines(S):
    """The rail, cart and boat lines (geo5 SHORTCUTS) as smooth lines, station to station."""
    out = []
    for nm, a, b, _, way, via in g.SHORTCUTS:
        pts = chaikin([g.pt(a)] + list(via) + [g.pt(b)], 3)
        kind = 'boat' if ('ferry' in nm or 'steamer' in nm) else ('cart' if 'cart' in nm else 'rail')
        out.append((nm, kind, pts, way))
    return out


def draw_lines(d, lines, P, R, ink, s):
    for nm, kind, pts, way in lines:
        if kind == 'boat':
            polyline(d, pts, P, R['snow'][5] + (230,), 1.6 * s, dash=(5 * s, 4 * s))
        else:
            polyline(d, pts, P, ink + (235,), (3.0 if kind == 'rail' else 2.2) * s)
            polyline(d, pts, P, R['plaster'][5] + (255,), (1.2 if kind == 'rail' else 0.9) * s, dash=(4 * s, 4 * s))


# ------------------------------------------------------------------------------------------ labels
class Placer:
    """Labels that never overlap: every placed box (text and icon) is kept; a label tries its spots in order."""

    def __init__(self, d, Wc, Hc):
        self.d = d; self.boxes = []; self.Wc = Wc; self.Hc = Hc; self.missed = []

    def free(self, b, pad=0):
        if b[0] < 4 or b[1] < 4 or b[2] > self.Wc - 4 or b[3] > self.Hc - 4:
            return False
        return all(b[2] + pad < o[0] or b[0] - pad > o[2] or b[3] + pad < o[1] or b[1] - pad > o[3] for o in self.boxes)

    def reserve(self, b):
        self.boxes.append(b)

    def text_box(self, xy, text, font, anchor='mm', stroke=2, spacing=0):
        if spacing:
            w = sum(self.d.textlength(ch, font=font) for ch in text) + spacing * (len(text) - 1)
            bb = self.d.textbbox((0, 0), 'Ag', font=font, anchor='lt')
            hgt = bb[3] - bb[1]
            x0 = xy[0] - w / 2 if anchor[0] == 'm' else (xy[0] if anchor[0] == 'l' else xy[0] - w)
            return (x0 - stroke, xy[1] - hgt / 2 - stroke, x0 + w + stroke, xy[1] + hgt / 2 + stroke)
        return self.d.textbbox(xy, text, font=font, anchor=anchor, stroke_width=stroke)

    def draw_text(self, xy, text, font, fill, stroke_fill, anchor='mm', stroke=2, spacing=0):
        if spacing:
            w = sum(self.d.textlength(ch, font=font) for ch in text) + spacing * (len(text) - 1)
            x = xy[0] - w / 2 if anchor[0] == 'm' else (xy[0] if anchor[0] == 'l' else xy[0] - w)
            for ch in text:
                self.d.text((x, xy[1]), ch, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor='lm')
                x += self.d.textlength(ch, font=font) + spacing
        else:
            self.d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)

    def put(self, xy, text, font, fill, stroke_fill, offsets, stroke=2, spacing=0, pad=1, leader=None, name=None):
        for dx, dy, anc in offsets:
            p = (xy[0] + dx, xy[1] + dy)
            b = self.text_box(p, text, font, anc, stroke, spacing)
            if self.free(b, pad):
                self.draw_text(p, text, font, fill, stroke_fill, anc, stroke, spacing); self.reserve(b); return b
        if leader:
            for r in leader:
                for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
                    p = (xy[0] + r * math.cos(a), xy[1] + r * math.sin(a))
                    b = self.text_box(p, text, font, 'mm', stroke, spacing)
                    if self.free(b, pad):
                        ex, ey = min(max(xy[0], b[0]), b[2]), min(max(xy[1], b[1]), b[3])
                        self.d.line([xy, (ex, ey)], fill=stroke_fill, width=2); self.d.line([xy, (ex, ey)], fill=fill, width=1)
                        self.draw_text(p, text, font, fill, stroke_fill, 'mm', stroke, spacing); self.reserve(b); return b
        if name is not False:
            self.missed.append(name or text)
        return None


def around(r, s):
    """Label spots round an icon of radius r: right, left, above, below, then the diagonals."""
    g_ = 3 * s
    return [(r + g_, 0, 'lm'), (-r - g_, 0, 'rm'), (0, -r - g_, 'mb'), (0, r + g_, 'mt'), (r + g_, -r - g_, 'lb'), (-r - g_, -r - g_, 'rb'),
            (r + g_, r + g_, 'lt'), (-r - g_, r + g_, 'rt')]


def icon(d, kind, X, Y, s, R, ink):
    """Small map icons, 1x size about 7 to 12 px. Returns the half-size reserved."""
    o = ink
    if kind in ('city', 'town', 'village', 'hamlet', 'harbour', 'oasis', 'frontier', 'mine', 'forge', 'springs', 'cape', 'cirque', 'hilltown', 'castle'):
        if kind == 'city':
            for i, (dx, hh) in enumerate([(-6, 9), (-1, 13), (4, 8)]):
                d.rectangle([X + dx * s - 2.5 * s, Y - hh * s / 2, X + dx * s + 2.5 * s, Y + 5 * s], fill=R['slate'][4], outline=o)
            d.rectangle([X - 9 * s, Y + 4 * s, X + 9 * s, Y + 6 * s], fill=R['berry'][4], outline=o)
            return 10 * s
        if kind in ('hilltown', 'castle'):
            d.rectangle([X - 6 * s, Y - 3 * s, X + 6 * s, Y + 5 * s], fill=R['stone'][4], outline=o)
            for dx in (-6, -2, 2):
                d.rectangle([X + dx * s, Y - 6 * s, X + (dx + 2.5) * s, Y - 3 * s], fill=R['stone'][4], outline=o)
            d.rectangle([X - 1.5 * s, Y + 1 * s, X + 1.5 * s, Y + 5 * s], fill=ink)
            return 8 * s
        big = kind in ('town',)
        r = (6.5 if big else 5) * s
        d.polygon([(X - r, Y), (X, Y - r), (X + r, Y)], fill=R['clay'][4], outline=o)
        d.rectangle([X - r * 0.75, Y, X + r * 0.75, Y + r * 0.85], fill=R['plaster'][5], outline=o)
        d.rectangle([X - r * 0.18, Y + r * 0.3, X + r * 0.18, Y + r * 0.85], fill=R['timber'][2])
        return r + 1 * s
    if kind == 'gate':
        d.rectangle([X - 3.5 * s, Y - 3.5 * s, X + 3.5 * s, Y + 3.5 * s], fill=R['brass'][4], outline=o)
        d.line([(X - 2 * s, Y), (X + 2 * s, Y)], fill=o, width=max(1, int(s)))
        return 5 * s
    if kind == 'waystone_plan' or kind == 'waystone_proposed':
        pts = [(X - 2.5 * s, Y + 3.5 * s), (X - 2 * s, Y - 3 * s), (X, Y - 4.5 * s), (X + 2 * s, Y - 3 * s), (X + 2.5 * s, Y + 3.5 * s)]
        d.polygon(pts, fill=R['sky'][5] if kind == 'waystone_plan' else None, outline=R['sky'][5] if kind != 'waystone_plan' else o, width=max(1, int(s)))
        d.ellipse([X - 1 * s, Y - 1.5 * s, X + 1 * s, Y + 0.5 * s], fill=R['brass'][5])
        return 5 * s
    if kind == 'crater':
        d.ellipse([X - 5 * s, Y - 5 * s, X + 5 * s, Y + 5 * s], fill=R['dusk'][2], outline=R['brass'][5], width=max(1, int(s)))
        st = [(X + 3 * s * math.cos(a) * (1 if i % 2 == 0 else 0.45), Y + 3 * s * math.sin(a) * (1 if i % 2 == 0 else 0.45))
              for i, a in enumerate(np.linspace(-math.pi / 2, 1.5 * math.pi, 9)[:-1])]
        d.polygon(st, fill=R['brass'][5])
        return 6 * s
    if kind == 'circle':
        for a in np.linspace(0, 2 * math.pi, 9)[:-1]:
            cx, cy = X + 6 * s * math.cos(a), Y + 6 * s * math.sin(a)
            d.rectangle([cx - 1.4 * s, cy - 2.2 * s, cx + 1.4 * s, cy + 1.4 * s], fill=R['stone'][5], outline=o)
        d.ellipse([X - 2 * s, Y - 2 * s, X + 2 * s, Y + 2 * s], fill=R['brass'][5], outline=o)
        return 9 * s
    # small places: a dot by kind
    col = {'cave': R['stone'][1], 'shrine': R['brass'][4], 'hut': R['timber'][3], 'view': R['snow'][5], 'tower': R['plaster'][5],
           'station': R['iron'][2], 'place': R['plaster'][5], 'zone': R['grass'][5]}.get(kind, R['plaster'][5])
    d.ellipse([X - 2.6 * s, Y - 2.6 * s, X + 2.6 * s, Y + 2.6 * s], fill=col, outline=o, width=max(1, int(s)))
    return 3.5 * s


# region and biome names: world position, text (curated, placed like a game map; regions larger and spaced)
REGION_NAMES = [
    ('THE HOME VALLEY', 6050, 4430), ('THE FROSTLINE', 6230, 1330), ('THE BRACKENS', 4930, 2140), ('COGSWORTH', 8350, 1700),
    ('THE LULL', 8000, 4560), ('NEON HARBOUR', 10560, 3720), ('SUNSTONE REACH', 2950, 1850), ('THE FIRE COUNTRY', 1150, 5300),
    ('TIDEBLOOM ISLES', 8450, 6120),
]
BIOME_NAMES = [
    ('the northern massif', 3300, 650), ('glaciers', 8200, 700), ('the old forest', 10400, 1650), ('the moss fens', 10800, 3150),
    ('the coal hills', 8650, 2050), ('the Fern hills', 6980, 2650), ('the High Fells', 6950, 1520), ('the moor', 5250, 2900),
    ('the Lull plain', 7650, 4150), ('the meander belt', 9650, 3500), ('the Lull delta', 8750, 5300), ('the Narrows', 9300, 2200),
    ('the Heights', 9600, 5130), ('the steppe', 4000, 2300), ('the Sunstone basin', 3500, 2350), ('the dune sea', 900, 2900),
    ('the salt lake', 1950, 3560), ('the ash fields', 2950, 3700), ('the Ember range', 850, 4430), ('Mount Ember', 2450, 4250),
    ('the dead forest', 3450, 5150), ('the Rift gorge', 4480, 1180), ('Amber canyon', 2560, 3420), ('the Headland', 7140, 5700),
    ('the southern sea', 3600, 6450), ('the watermeadows', 8150, 4380), ('the hay slope', 6560, 2520),
]


def labels_layer(S, M, R, ink, s, k, ox, Wc, Hc, F, lines):
    """Every name on its own transparent layer, placed so none overlaps another."""
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k)
    pl = Placer(d, Wc, Hc)
    cream, inkc = R['plaster'][5], ink
    # reserve the panels (legend top-left, ruler bottom-left, compass bottom-right)
    for b in panel_boxes(Wc, Hc, s):
        pl.reserve(b)
    for i, X, Y in act_marks(M, P, s):
        pl.reserve((X - 7 * s, Y - 7 * s, X + 7 * s, Y + 7 * s))
    pl.reserve(built_tag(P, s))
    # 1. icons first, so names keep off every icon
    icons = []
    settle = dict(g.SETTLE); settle.pop('Home valley', None); settle.pop('the Frostline', None)
    settle['Crossroads'] = (M.CROSSROADS[0], M.CROSSROADS[1], 300, 'town')
    for nm, (x, y, r, kind) in settle.items():
        icons.append((nm, x, y, kind if kind in ('city', 'town', 'hilltown') else 'village', 'town', 0))
    icons.append(('the stone circle', M.CIRCLE[0], M.CIRCLE[1], 'circle', 'place', 1))
    for nm, (x, y, r, region, story) in M.CRATERS.items():
        if nm != 'the Crossroads crater':
            icons.append((nm, x, y, 'crater', 'crater', 2))
    gates = [('the ridge col', 6230, 2040, 'W2'), ('the Col hut', 6290, 2350, 'W2'), ("Drover's bridge", 4330, 3440, 'W5'),
             ('the Rift viaduct', 4300, 3720, 'W5'), ('the Rift ferry', 4180, 5240, 'W5'), ('the chasm bridge', 2170, 4920, 'W6'),
             ('the crust causeway', 3300, 5560, 'W6'), ('the Millrace cutting', 7650, 2740, 'W3'), ('Lullford swing bridge', 8960, 4310, 'W7'),
             ('the Narrows viaduct', 9030, 2330, ''), ('the Headland stile', 6990, 5300, 'W1'), ('the Shell Bar', 6900, 5900, 'W4'),
             ('the Cog foot', 8530, 3060, 'W3'), ('the Brackens gap', 5200, 3760, ''), ('the Cinder Rise', 2270, 3860, ''),
             ('the Harbour Bridge', 10300, 4990, ''), ('the canal embankment', 9450, 4680, '')]
    for nm, x, y, w in gates:
        icons.append((nm, x, y, 'gate', 'gate', 3))
    for nm, (x, y, st) in M.WAYSTONES.items():
        icons.append(('waystone: ' + nm, x, y, 'waystone_' + st, 'none', 9))
    places = [('the woodland', 5800, 2620, 'zone'), ('the garden', 6296, 3088, 'zone'), ('the riverside', 6660, 3080, 'zone'),
              ('the park', 6816, 3648, 'zone'), ('the halt', 5760, 4048, 'station'), ('the tarn', 6200, 1800, 'place'),
              ('the bothy', 6520, 2168, 'hut'), ('the ice caves', 6080, 1660, 'cave'), ('the Saddle House', 6440, 2010, 'shrine'),
              ('high lookout', 5968, 1584, 'view'), ("Old Fang's barrow", 4930, 2980, 'cave'), ('the spur tor', 4990, 1960, 'view'),
              ('drove well', 5064, 3316, 'place'), ('the lighthouse', 6600, 4995, 'tower'), ('the old town', 10176, 4344, 'place'),
              ('the docks', 10300, 4720, 'place'), ('new town', 10900, 4560, 'place'), ('the Skyport', 10920, 5120, 'place'),
              ('Gull Strand', 10520, 5320, 'place'), ('Beacon Isle', 10096, 5440, 'place'), ('the old volcano', 7112, 6216, 'view'),
              ('turtle beach', 6368, 6648, 'place'), ('the sea cave', 6880, 6680, 'cave'), ('the pit head', 7248, 3000, 'place'),
              ('the echo cave', 7596, 1852, 'cave'), ('the oxbow bell', 9450, 3900, 'place'),
              ('the dusty corral', 2988, 2476, 'place'), ('the basalt ring', 2520, 4840, 'place'), ('the reed hides', 8800, 4700, 'view')]
    for nm, x, y, kind in places:
        icons.append((nm, x, y, kind, 'place', 4))
    # draw and reserve all icons
    placed_icons = []
    for nm, x, y, kind, cat, pr in icons:
        X, Y = P(x, y); r = icon(d, kind, X, Y, s, R, ink)
        pl.reserve((X - r, Y - r, X + r, Y + r)); placed_icons.append((nm, X, Y, r, cat, kind))
    # way badges by the gates
    for nm, x, y, w in gates:
        if w:
            X, Y = P(x, y); bx, by = X + 5 * s, Y - 9 * s
            b = (bx - 1 * s, by - 5 * s, bx + 14 * s, by + 5 * s)
            if pl.free(b):
                d.rounded_rectangle(b, radius=2 * s, fill=R['berry'][3], outline=ink); d.text(((b[0] + b[2]) / 2, by), w, font=F['way'], fill=cream, anchor='mm'); pl.reserve(b)
    # 2. region names (large, spaced), then biome names
    for t, x, y in REGION_NAMES:
        X, Y = P(x, y)
        pl.put((X, Y), t, F['region'], cream, inkc, [(0, 0, 'mm'), (0, -18 * s, 'mm'), (0, 18 * s, 'mm'), (40 * s, 0, 'mm'), (-40 * s, 0, 'mm')],
               stroke=int(3 * s), spacing=3 * s, pad=2 * s)
    for t, x, y in BIOME_NAMES:
        X, Y = P(x, y)
        pl.put((X, Y), t, F['biome'], R['snow'][5], mix(ink, R['stone'][1], 0.3), [(0, 0, 'mm'), (0, -14 * s, 'mm'), (0, 14 * s, 'mm'), (30 * s, 0, 'mm'),
                                                                                    (-30 * s, 0, 'mm'), (0, -28 * s, 'mm'), (0, 28 * s, 'mm')],
               stroke=int(2 * s), spacing=1 * s, pad=1 * s)
    # 3. settlements, the circle, craters, gates, places: names beside their icons
    order = sorted(placed_icons, key=lambda p: {'town': 0, 'place': 2, 'crater': 1, 'gate': 3, 'none': 9}[p[4]] if p[0] != 'the stone circle' else -1)
    for nm, X, Y, r, cat, kind in order:
        if cat == 'none':
            continue
        if cat == 'town':
            font, fill, st = F['town'], cream, inkc
        elif cat == 'crater':
            font, fill, st = F['place'], R['dusk'][5], R['dusk'][0]
        elif cat == 'gate':
            font, fill, st = F['gate'], R['brass'][5], inkc
        else:
            font, fill, st = F['place'], R['plaster'][5], inkc
        if nm == 'the stone circle':
            font, fill = F['town'], R['brass'][5]
        pl.put((X, Y), nm, font, fill, st, around(r, s), stroke=int(2 * s), leader=[r + 14 * s, r + 24 * s, r + 36 * s], name=nm)
    # 4. water names along the rivers and in the sea
    for nm, pts in S['river_px'].items():
        if nm in ('the Dry Fork', 'Brackens wash'):
            continue
        for frac in (0.42, 0.3, 0.58, 0.7, 0.2, 0.5, 0.36, 0.64, 0.8, 0.25, 0.75, 0.12, 0.88):
            q = pts[int(len(pts) * frac)]; X, Y = P(*q)
            if pl.put((X, Y), nm, F['water'], R['sky'][5], R['water'][0], [(0, -9 * s, 'mb'), (0, 9 * s, 'mt'), (12 * s, 0, 'lm'), (-12 * s, 0, 'rm')],
                      stroke=int(2 * s), name=False):
                break
        else:
            pl.missed.append(nm)
    for t, x, y in [('the southern sea', 9000, 6300), ('the ria', 10230, 4700)]:
        X, Y = P(x, y); pl.put((X, Y), t, F['water'], R['sky'][5], R['water'][0], [(0, 0, 'mm'), (0, 14 * s, 'mm')], stroke=int(2 * s))
    # 5. route names: rotated along the route, small caps, where there is room
    for nm, sm in S['route_px'].items():
        kind = S['routes'][nm][0]
        if nm.startswith('Valley lane') or nm in ('Old Bridges', 'Quay Street', 'Forge Stair', 'Beacon Causeway', 'Harbour Bridge', 'Shell Bar'):
            continue
        rotated(pl, lay, sm, P, nm, F['route'], R['path'][5], inkc, s, [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.45, 0.55, 0.35, 0.65, 0.15, 0.85])
    for nm, kind, pts, way in lines:
        label = {'valley train': 'the valley train', 'desert line (Rift viaduct)': 'the desert line', 'maglev (Narrows Viaduct)': 'the maglev',
                 'ferry': 'the isles ferry', 'mine cart (S1)': 'the mine cart', 'coastal steamer (S3)': 'the coastal steamer'}.get(nm, nm)
        rotated(pl, lay, pts, P, label, F['route'], R['snow'][5] if kind == 'boat' else R['plaster'][5], inkc, s, [0.5, 0.4, 0.6, 0.3, 0.7], italic=True)
    return lay, pl


def rotated(pl, lay, pts, P, text, font, fill, stroke_fill, s, fracs, italic=False):
    x, y, al, tot = densify(pts, 6)
    tw = pl.d.textlength(text, font=font)
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
        # offset the label to one side of the line, so it does not sit on the track
        nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
        for side, dist_ in ((-1, 7), (1, 7), (-1, 12), (1, 12)):
            cx, cy = X + nx * side * dist_ * s, Y + ny * side * dist_ * s
            b = (cx - rt.width / 2 + pad, cy - rt.height / 2 + pad, cx + rt.width / 2 - pad, cy + rt.height / 2 - pad)
            if pl.free(b, 1):
                lay.alpha_composite(rt, (int(round(cx - rt.width / 2)), int(round(cy - rt.height / 2))))
                pl.reserve(b); return True
    i = int(0.5 * (len(x) - 1)); X, Y = P(x[i], y[i])
    if pl.put((X, Y), text, font, fill, stroke_fill, around(3 * s, s), stroke=int(2 * s), leader=[16 * s, 26 * s, 38 * s], name=False):
        return True
    pl.missed.append(text)
    return False


# ------------------------------------------------------------------------------------------ panels: legend, ruler, compass
def panel_boxes(Wc, Hc, s):
    return [(12 * s, 12 * s, 330 * s, 300 * s), (12 * s, Hc - 150 * s, 560 * s, Hc - 12 * s), (Wc - 120 * s, Hc - 130 * s, Wc - 12 * s, Hc - 12 * s)]


def panels(lay, S, M, R, ink, s, k, Wc, Hc, F, act1=True, title='The continent: overview (v53)'):
    d = ImageDraw.Draw(lay)
    paper = R['plaster'][5] + (236,); edge = R['timber'][2]
    lb, rb, cb = panel_boxes(Wc, Hc, s)
    # legend and act 1's beats (top left, over the northern massif's frame)
    d.rounded_rectangle(lb, radius=6 * s, fill=paper, outline=edge, width=max(1, int(2 * s)))
    x0, y = lb[0] + 12 * s, lb[1] + 10 * s
    d.text((x0, y), title, font=F['title'], fill=ink, anchor='lt'); y += 30 * s
    rows = [('town', 'town or village'), ('circle', 'the stone circle (centre)'), ('crater', 'great shard crater'),
            ('gate', 'gate between regions (way W1 to W7)'), ('waystone_plan', 'waystone (in a plan)'), ('waystone_proposed', 'waystone (proposed)')]
    for kind, txt in rows:
        icon(d, kind, x0 + 8 * s, y + 6 * s, s * 0.9, R, ink); d.text((x0 + 22 * s, y + 6 * s), txt, font=F['small'], fill=ink, anchor='lm'); y += 16 * s
    for kind, txt in [('road', 'road / path'), ('rail', 'rail line'), ('boat', 'ferry or steamer'), ('act1', "act 1's route")]:
        yy = y + 6 * s
        if kind == 'road':
            d.line([(x0, yy), (x0 + 16 * s, yy)], fill=R['path'][1], width=int(5 * s)); d.line([(x0, yy), (x0 + 16 * s, yy)], fill=R['path'][5], width=int(3 * s))
        elif kind == 'rail':
            d.line([(x0, yy), (x0 + 16 * s, yy)], fill=ink, width=int(3 * s))
            for q in range(0, 16, 6):
                d.line([(x0 + q * s, yy), (x0 + (q + 3) * s, yy)], fill=R['plaster'][5], width=max(1, int(1.2 * s)))
        elif kind == 'boat':
            for q in range(0, 16, 6):
                d.line([(x0 + q * s, yy), (x0 + (q + 3) * s, yy)], fill=R['water'][2], width=max(1, int(2 * s)))
        else:
            for q in range(0, 16, 5):
                d.ellipse([x0 + q * s, yy - 1.5 * s, x0 + (q + 3) * s, yy + 1.5 * s], fill=R['berry'][4])
        d.text((x0 + 22 * s, yy), txt, font=F['small'], fill=ink, anchor='lm'); y += 16 * s
    if act1:
        y += 4 * s
        d.text((x0, y), "Act 1, one order of its beats", font=F['legend'], fill=ink, anchor='lt'); y += 16 * s
        col2 = lb[0] + (lb[2] - lb[0]) / 2
        for i, (nm, p, what) in enumerate(M.ACT1):
            cx = x0 if i < 7 else col2; cy = y + (i % 7) * 14 * s
            d.ellipse([cx, cy, cx + 11 * s, cy + 11 * s], fill=R['berry'][4], outline=ink)
            d.text((cx + 5.5 * s, cy + 5.5 * s), str(i), font=F['way'], fill=R['plaster'][5], anchor='mm')
            d.text((cx + 15 * s, cy + 5.5 * s), nm, font=F['small'], fill=ink, anchor='lm')
    # the ruler (bottom left, over the sea)
    d.rounded_rectangle(rb, radius=6 * s, fill=paper, outline=edge, width=max(1, int(2 * s)))
    hero = S['hero']; v = hero['walk_speed_world_px_s']
    x0, y0 = rb[0] + 14 * s, rb[1] + 12 * s
    d.text((x0, y0), 'Scale: the soft grid', font=F['legend'], fill=ink, anchor='lt')
    d.text((x0, y0 + 15 * s), f"1 cell = 8 world px = 24 art px. Walk times at Bramble's {hero['walk_speed_art_px_s']:g} art px/s "
                              f"({v:.1f} world px/s, {v / 8:.2f} cells/s)", font=F['small'], fill=ink, anchor='lt')
    bx, by = x0 + 4 * s, y0 + 52 * s; cpx = 8 * k                              # px per cell on this map
    marks = [0, 10, 50, 100, 200, 300]
    for a, b_ in zip(marks, marks[1:]):
        d.rectangle([bx + a * cpx, by, bx + b_ * cpx, by + 6 * s], fill=ink if marks.index(a) % 2 == 0 else R['plaster'][3], outline=ink)
    for m in marks:
        d.line([(bx + m * cpx, by - 3 * s), (bx + m * cpx, by + 9 * s)], fill=ink, width=max(1, int(s)))
        if m:
            d.text((bx + m * cpx, by - 4 * s), f'{m}' + (' cells' if m == 300 else ''), font=F['small'], fill=ink, anchor='mb')
        if m:
            d.text((bx + m * cpx, by + 11 * s), f'{m * 8 / v:.0f} s', font=F['small'], fill=R['timber'][2], anchor='mt')
    # one 1080p screen: 960 art px = 320 world px = 40 cells
    sx, sy = bx, by + 30 * s; sw = 40 * cpx
    d.rectangle([sx, sy, sx + sw, sy + 22 * s], outline=R['sky'][2], width=max(1, int(2 * s)), fill=R['sky'][5] + (140,))
    d.text((sx + sw + 8 * s, sy + 11 * s), f'one 1080p screen = 960 art px = 320 world px = 40 cells: {320 / v:.1f} s to walk across',
           font=F['small'], fill=ink, anchor='lm')
    d.text((x0, sy + 27 * s), f"Map: 1 px = {1 / k:.1f} world px ({1 / k / 8:.2f} cells). W1 to W7: the ways (world-plan 10).",
           font=F['small'], fill=R['timber'][2], anchor='lt')
    # north arrow (bottom right)
    d.rounded_rectangle(cb, radius=6 * s, fill=paper, outline=edge, width=max(1, int(2 * s)))
    cx, cy = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2 + 6 * s; r = 34 * s
    d.polygon([(cx, cy - r), (cx + 9 * s, cy), (cx, cy - 6 * s)], fill=ink)
    d.polygon([(cx, cy - r), (cx - 9 * s, cy), (cx, cy - 6 * s)], fill=R['berry'][4], outline=ink)
    d.polygon([(cx, cy + r * 0.7), (cx + 9 * s, cy), (cx, cy + 6 * s)], fill=R['plaster'][3], outline=ink)
    d.polygon([(cx, cy + r * 0.7), (cx - 9 * s, cy), (cx, cy + 6 * s)], fill=R['plaster'][5], outline=ink)
    d.text((cx, cy - r - 4 * s), 'N', font=F['title'], fill=ink, anchor='mb')


# ------------------------------------------------------------------------------------------ overlays
def act_marks(M, P, s):
    """Where act 1's numbered beats are drawn: up and left of each beat's point, repeats stacked to the left."""
    seen = {}; out = []
    for i, (nm, p, what) in enumerate(M.ACT1):
        X, Y = P(*p); X -= 9 * s; Y -= 9 * s
        key = (round(X / (10 * s)), round(Y / (10 * s)))
        off = seen.get(key, 0); seen[key] = off + 1
        out.append((i, X - off * 14 * s, Y))
    return out


def built_tag(P, s):
    x, y = P(5640, 2432)
    return (x + 3 * s, y + 3 * s, x + 59 * s, y + 16 * s)


def overlay_built(S, M, R, ink, s, k, ox, Wc, Hc, F):
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k)
    for nm, (x0, y0, x1, y1) in M.BUILT.items():
        a, b = P(x0, y0), P(x1, y1)
        under = 'below' in nm
        if under:
            polyline(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], P, R['brass'][5] + (255,), 1.6 * s, dash=(4 * s, 3 * s))
        else:
            d.rectangle([a[0] - 2 * s, a[1] - 2 * s, b[0] + 2 * s, b[1] + 2 * s], outline=R['brass'][2] + (200,), width=int(4 * s))
            d.rectangle([a, b], outline=R['brass'][5] + (255,), width=max(1, int(1.6 * s)), fill=R['brass'][5] + (46,))
    tb = built_tag(P, s)
    d.rounded_rectangle(tb, radius=3 * s, fill=R['brass'][4] + (255,), outline=ink)
    d.text(((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2), 'BUILT NOW', font=F['way'], fill=ink, anchor='mm')
    return lay


def act1_path(S, M):
    """Act 1's route: the shortest walk between the beats on the block-out's ground, preferring routes."""
    K = S['K']; kinds = S['kinds']
    walk = np.isin(np.array(kinds, dtype=object)[K], list(g.WALK)) & ~S['frame']
    rk = np.isin(np.array(kinds, dtype=object)[K], ['road', 'path', 'stair', 'bridge', 'trail', 'lane', 'boulevard', 'plaza', 'yard', 'bar'])
    cost = np.where(walk, np.where(rk, 1.0, 4.0), np.inf)
    out = []
    for (n0, p0, _), (n1, p1, _) in zip(M.ACT1, M.ACT1[1:]):
        a = g.nearest_walk(walk, *p0); b = g.nearest_walk(walk, *p1)
        m = MCP_Geometric(cost); m.find_costs([a], [b]); path = m.traceback(b)
        out.append([((x + 0.5) * CELL, (y + 0.5) * CELL) for y, x in path])
    return out


def overlay_act1(S, M, R, ink, s, k, ox, Wc, Hc, F, paths):
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k)
    for i, pts in enumerate(paths):
        sm = pts[::3] + [pts[-1]]
        q = [P(*p) for p in sm]
        # dots every few px along the walk
        x, y, al, tot = densify(q, 1.0)
        step = 5.5 * s
        for a in np.arange(0, tot, step):
            j = int(np.argmin(np.abs(al - a)))
            d.ellipse([x[j] - 1.6 * s, y[j] - 1.6 * s, x[j] + 1.6 * s, y[j] + 1.6 * s], fill=R['berry'][4] + (255,), outline=R['plaster'][5] + (200,))
    for i, X, Y in act_marks(M, P, s):
        d.ellipse([X - 6.5 * s, Y - 6.5 * s, X + 6.5 * s, Y + 6.5 * s], fill=R['berry'][4] + (255,), outline=ink, width=max(1, int(s)))
        d.text((X, Y), str(i), font=F['num'], fill=R['plaster'][5], anchor='mm')
    return lay


def overlay_ring(S, M, R, ink, s, k, ox, Wc, Hc, F):
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k)
    C = P(*M.CIRCLE)
    for nm, (x, y, r, region, story) in M.CRATERS.items():
        X, Y = P(x, y)
        polyline(d, [(x, y), M.CIRCLE], P, R['plaster'][5] + (110,), 3.6 * s)
        polyline(d, [(x, y), M.CIRCLE], P, R['dusk'][2] + (215,), 1.8 * s, dash=(7 * s, 4 * s))
        d.ellipse([X - 9 * s, Y - 9 * s, X + 9 * s, Y + 9 * s], outline=R['brass'][5] + (210,), width=max(1, int(1.4 * s)))
    # the ring itself: a faint ellipse through the craters' mean distance, and the circle's glow
    for rr, al in ((26, 60), (18, 90), (11, 140)):
        d.ellipse([C[0] - rr * s, C[1] - rr * s, C[0] + rr * s, C[1] + rr * s], fill=R['brass'][5] + (al // 3,))
    return lay


# ------------------------------------------------------------------------------------------ compose and save
def render_scale(S, M, s, base2x, paths, lines, R, ink, real2x=None):
    Wc, Hc = int(BASE_W * s), int(BASE_H * s)
    k = Hc / HPX; ox = Wc / 2 - M.CIRCLE[0] * k
    F = fonts(M.ROOT, s)

    def frame_base(b2):
        bimg = b2 if s == 2 else b2.resize((int(b2.width * s / 2), int(b2.height * s / 2)), Image.LANCZOS)
        canvas = Image.new('RGB', (Wc, Hc), R['plaster'][3])
        # the land goes on past the drawn edges: stretch the outer columns into the margins and fade them to paper
        arr = np.asarray(bimg); xo = int(round(ox)); left, right = xo, Wc - xo - arr.shape[1]
        if left > 0 or right > 0:
            L_, R_ = max(left, 0), max(right, 0)
            ext = np.pad(arr, ((0, 0), (L_, R_), (0, 0)), mode='reflect')
            blur = np.asarray(Image.fromarray(ext).filter(ImageFilter.GaussianBlur(6 * s))).astype(np.float32)
            arr2 = ext.astype(np.float32)
            fade = np.ones(arr2.shape[1], np.float32)
            if L_:
                fade[:L_] = np.linspace(0.25, 0.9, L_)
            if R_:
                fade[-R_:] = np.linspace(0.9, 0.25, R_)
            margin = np.zeros(arr2.shape[1], bool); margin[:L_] = True
            if R_:
                margin[-R_:] = True
            arr2[:, margin] = blur[:, margin]
            paper = np.array(R['plaster'][4], np.float32)
            arr2 = arr2 * fade[None, :, None] + paper * (1 - fade[None, :, None])
            canvas.paste(Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8)), (min(xo, 0), 0))
        else:
            canvas.paste(bimg, (xo, 0))
        return canvas
    canvas = frame_base(base2x)
    # vectors at this scale
    d = ImageDraw.Draw(canvas, 'RGBA'); P = lambda x, y: (x * k + ox, y * k)
    water_and_routes(canvas, S, R, ink, k, ox, M)
    draw_lines(d, lines, P, R, ink, s)
    # a thin frame
    d.rectangle([3 * s, 3 * s, Wc - 3 * s, Hc - 3 * s], outline=ink, width=max(1, int(2 * s)))
    d.rectangle([7 * s, 7 * s, Wc - 7 * s, Hc - 7 * s], outline=R['timber'][3], width=max(1, int(s)))
    lab, pl = labels_layer(S, M, R, ink, s, k, ox, Wc, Hc, F, lines)
    pan = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); panels(pan, S, M, R, ink, s, k, Wc, Hc, F)
    built = overlay_built(S, M, R, ink, s, k, ox, Wc, Hc, F)
    act = overlay_act1(S, M, R, ink, s, k, ox, Wc, Hc, F, paths)
    ring = overlay_ring(S, M, R, ink, s, k, ox, Wc, Hc, F)
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
        rc = frame_base(real2x); water_and_routes(rc, S, R, ink, k, ox, M); dd = ImageDraw.Draw(rc, 'RGBA'); draw_lines(dd, lines, P, R, ink, s)
        rr = rc.convert('RGBA')
        for layer in (ring, built, lab, act, pan):
            rr.alpha_composite(layer)
        out['realistic'] = rr
    return out, pl.missed


def render_all(S, M):
    R, ink = load_palette(M.ROOT)
    base2x, cg, names, cid = base_2x(S, R, ink)
    k2 = 2160 / HPX
    stamps(base2x, S, R, cg, cid, k2)
    real2x, _, _, _ = base_2x(S, R, ink, realistic=True)
    paths = act1_path(S, M); lines = rail_lines(S)
    outs = [os.environ.get('MAP53_OUT')] if os.environ.get('MAP53_OUT') else []
    outs.append(M.HERE)
    missed_all = {}
    for s, tag in ((1, '1920'), (2, '3840')):
        res, missed = render_scale(S, M, s, base2x, paths, lines, R, ink, real2x)
        missed_all[tag] = missed
        for o in outs:
            os.makedirs(o, exist_ok=True)
            res['full'].convert('RGB').save(os.path.join(o, f'map53-{tag}.png'))
            if s == 1:
                for key in ('labels', 'overlay-built', 'overlay-act1', 'overlay-ring', 'realistic', 'base'):
                    res[key].convert('RGB').save(os.path.join(o, f'map53-{key}-{tag}.png'))
                for key in ('layer-built', 'layer-act1', 'layer-ring', 'layer-labels'):
                    res[key].save(os.path.join(o, f'map53-{key}-{tag}.png'))
        if s == 1:
            small = res['full'].convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            small.save(os.path.join(M.DATA, 'continent-1x-v53.png'), optimize=True)
            # v52 against v53, side by side at the same scale
            v52 = Image.open(os.path.join(M.DATA, 'continent-1x-v52.png')).convert('RGB').resize((int(WPX * 1080 / HPX), 1080), Image.LANCZOS)
            cmp_ = Image.new('RGB', (v52.width + 1920 + 24, 1080 + 40), (30, 26, 34)); dc = ImageDraw.Draw(cmp_)
            cmp_.paste(v52, (0, 40)); cmp_.paste(res['full'].convert('RGB'), (v52.width + 24, 40))
            Fc = fonts(M.ROOT, 1)
            dc.text((10, 20), 'v52 (block-out render, 1 px = 8 world px, resized)', font=Fc['title'], fill=(240, 230, 210), anchor='lm')
            dc.text((v52.width + 34, 20), 'v53 (overview map, 1920 x 1080)', font=Fc['title'], fill=(240, 230, 210), anchor='lm')
            for o in outs:
                cmp_.save(os.path.join(o, 'map53-v52-vs-v53.png'))
    print('labels not placed:', json.dumps(missed_all))
    return missed_all
