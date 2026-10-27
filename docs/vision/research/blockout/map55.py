"""The v55 overview map, drawn from geo55.py's state (README.md, "v55"); v54's map (map54.py) on the v55 canvas, with:

- the towns at their footprints: every building drawn as a small roof (lit on its west half, shaded east, a shadow to the
  south-east), the streets, squares, quays and yards on the ground, the working outskirts round them;
- Neon Harbour's five districts, the east coast and Launch Cape; Highgarth and the Northway to its rockfall, the road beyond
  drawn faint past the rockfall into a gap in the cloud bank where the land beyond shows (the pass is closed);
- one treatment for the range, the forests and the dunes: the same three tones from one ramp (lit, middle, shade), the same
  thin ink outline and the same cast shadow to the south-east on peaks, hills, trees, mesas and buildings; softer summits;
  projecting spurs and varied foothills along the northern wall; forests with clearings and uneven density;
- an irregular cloud edge (a noise-shaped bank, lit from the upper left) where the land runs off the canvas;
- labels by zoom: the continent map names the regions, the towns and the city, the circle and the principal routes; the
  insets and the reference (3x) name everything.

Called by geo55.py (render_all, features); not run on its own."""
import json, math, os
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import geo5 as g
import geo52 as G
import map53 as M53
import map54 as M54
from map53 import load_palette, mix, fonts, polyline, rail_lines, draw_lines, Placer, around, icon, act1_path
from geo5 import CELL, chaikin, densify, noise, shape

BASE_W, BASE_H = 1920, 1080
FOREST = M54.FOREST
_f54 = M54.features
_FEAT = {}


# ------------------------------------------------------------------------------------------ the range, with spurs
def features(S, M):
    """map54's range glyphs, plus spurs: chains of hills stepping down from the range front along the fall line, so the
    northern wall projects ridges into the lowland with valleys between them, and foothills of more varied size."""
    key = id(S)
    if key in _FEAT:
        return _FEAT[key]
    F = _f54(S, M)
    m = F['m']; H, W = m.shape
    land = S['land']; fr = S['frame']; kinds = np.array(S['kinds'], dtype=object); Kk = kinds[S['K']]
    gy, gx = np.gradient(ndi.gaussian_filter(m, 3.0))
    relief = m - ndi.gaussian_filter(m, 7)
    rng = np.random.default_rng(5501)
    blocked = np.isin(Kk, list(M54.WATERK) + ['glacier', 'crevasse', 'snow', 'broadleaf', 'conifer', 'wild', 'ancient', 'thicket']) | ~land | ~fr
    clear = np.zeros((H, W), bool)
    for nm, pts in S['route_px'].items():
        clear |= g.line_mask(pts, 160)
    for nm, r in S['towns'].items():
        if r['footprint_box']:
            x0, y0, x1, y1 = r['footprint_box']
            clear[max(0, int(y0 // CELL) - 12):int(y1 // CELL) + 12, max(0, int(x0 // CELL) - 12):int(x1 // CELL) + 12] = True
    seeds = []
    for yw in range(900, 2300, 70):
        for xw in range(200, int(g.WPX) - 200, 70):
            cy, cx = int(yw // CELL), int(xw // CELL)
            if 0.6 < m[cy, cx] < 0.72 and relief[cy, cx] > 0.012 and not blocked[cy, cx] and not clear[cy, cx]:
                seeds.append((float(relief[cy, cx]), xw, yw))
    seeds.sort(reverse=True)
    chosen = []
    for rv, xw, yw in seeds:
        if all(math.hypot(xw - a, yw - b) > 420 for a, b in chosen):
            chosen.append((xw, yw))
    spur = []
    for (xw, yw) in chosen[:40]:
        x, y = float(xw), float(yw); ht = rng.uniform(55, 80)
        for step in range(9):
            cy, cx = int(y // CELL), int(x // CELL)
            if not (0 <= cy < H and 0 <= cx < W) or blocked[cy, cx] or clear[cy, cx] or m[cy, cx] < 0.44:
                break
            spur.append(dict(kind='hill', v='hill', x=x, y=y, ht=ht, w=ht * rng.uniform(1.9, 2.6), e=float(m[cy, cx]), skew=rng.uniform(-0.15, 0.15),
                             j1=0.0, j2=0.0, j3=0.0, under=str(Kk[cy, cx]), spur=True))
            nx_, ny_ = -gx[cy, cx], -gy[cy, cx]; L = math.hypot(nx_, ny_) or 1
            x += nx_ / L * 64 + rng.uniform(-12, 12); y += max(30.0, ny_ / L * 64); ht *= rng.uniform(0.78, 0.9)
            if ht < 22:
                break
    glyphs = [c for c in F['glyphs']]
    for c in glyphs:                                  # foothills of varied size (map54's were nearly all one size)
        if c['kind'] == 'hill' and not c.get('spur'):
            f = 0.7 + 0.8 * rng.random(); c['ht'] *= f; c['w'] *= 0.85 + 0.4 * rng.random()
    glyphs += spur
    glyphs.sort(key=lambda c: c['y'])
    F = dict(F); F['glyphs'] = glyphs; F['range'] = dict(F['range'], spurs=len(chosen[:40]), spur_hills=len(spur))
    _FEAT[key] = F
    return F


M54.features = features                               # base_hi and the range drawing read the spurs too


# ------------------------------------------------------------------------------------------ one treatment for marks
def tones(c):
    """Lit, middle and shade from one base colour (the three tones every mark uses)."""
    return mix(c, (255, 248, 226), 0.22), c, mix(c, (30, 26, 40), 0.32)


def stamps55(im, S, R, cg, cid, k, ox, oy, M, ink):
    """Tree, tuft, marsh, crevasse and pebble marks, then the range: one treatment (three tones from one ramp, a thin ink
    outline, a cast shadow to the south-east); forests in uneven density with clearings."""
    d = ImageDraw.Draw(im, 'RGBA'); rng = np.random.default_rng(11)
    H, W = cg.shape
    kk = k / (2160 / g.HPX)
    fr = S['frame']
    forest = np.isin(cg, [cid[n] for n in FOREST if n in cid])
    edge = forest & ~ndi.binary_erosion(forest, iterations=1)
    deep = ndi.binary_erosion(forest, iterations=4)
    dens = noise(700, 5801) + 0.5 * noise(220, 5802, 2)                    # uneven density
    clearing = deep & (noise(300, 5803) + 0.4 * noise(90, 5804, 2) > 0.62)   # clearings inside the woods
    outline = ink + (95,)
    shadow = ink + (60,)

    def cell(x, y):
        wx, wy = (x - ox) / k, (y - oy) / k
        cx, cy = int(wx / CELL), int(wy / CELL)
        if 0 <= cx < W and 0 <= cy < H:
            return cx, cy
        return None
    spec = [('broadleaf', 10, 'round', R['leaf'][3], 4.6), ('oldforest', 11, 'round', R['leaf_cool'][2], 5.6), ('carr', 10, 'round', R['leaf_warm'][3], 4.0),
            ('orchard', 7, 'round', R['leaf_warm'][3], 2.6), ('conifer', 9, 'cone', R['leaf_cool'][3], 4.2), ('deadwood', 10, 'snag', R['basalt_warm'][2], 4.0),
            ('wetland', 9, 'reed', R['grass_cool'][1], 3.0), ('heath', 9, 'dot', R['berry_cool'][3], 1.5), ('steppe', 13, 'tuft', R['grass_warm'][2], 2.2),
            ('scrub', 14, 'dot', R['sand_cool'][1], 1.6), ('desert', 34, 'dot', R['sand'][2], 1.0), ('ash', 14, 'dot', R['basalt'][2], 1.4),
            ('lavastone', 12, 'dot', R['basalt_warm'][2], 1.5), ('glacier', 8, 'crev', R['snow_cool'][1], 2.6), ('wash', 9, 'dot', R['sand'][2], 0.9)]
    gy_, gx_ = np.gradient(ndi.gaussian_filter(S['h'].astype(np.float32), 2.0))
    marks = []
    for nm, sp, kind, c, r in spec:
        if nm not in cid:
            continue
        ci = cid[nm]; sp = sp * kk; r = r * kk
        ys = np.arange(sp / 2, im.height, sp); xs = np.arange(sp / 2, im.width, sp)
        for yi, y in enumerate(ys):
            for x in xs + (sp / 2 if yi % 2 else 0):
                jx, jy = x + rng.uniform(-sp * 0.32, sp * 0.32), y + rng.uniform(-sp * 0.32, sp * 0.32)
                cc = cell(jx, jy)
                if cc is None or cg[cc[1], cc[0]] != ci:
                    continue
                cx_, cy_ = cc
                if kind in ('round', 'cone'):
                    if clearing[cy_, cx_]:
                        continue
                    if not edge[cy_, cx_] and rng.random() < 0.28 * (1 - dens[cy_, cx_]):    # thinner where the density field is low
                        continue
                faint = fr[cy_, cx_]
                rr = r * (0.82 if faint else 1.0) * rng.uniform(0.8, 1.25) * (1.12 if kind in ('round', 'cone') and dens[cy_, cx_] > 0.3 else 1.0)
                marks.append((jy, jx, kind, c, rr, (gx_[cy_, cx_], gy_[cy_, cx_]), bool(edge[cy_, cx_])))
    marks.sort(key=lambda m_: m_[0])
    for y, x, kind, c, r, grad, ed in marks:
        lt, md, sh = tones(c)
        if kind == 'round':
            d.ellipse([x - r + 1.2 * kk, y - r + 1.8 * kk, x + r + 1.2 * kk, y + r + 1.8 * kk], fill=shadow)
            d.ellipse([x - r, y - r, x + r, y + r], fill=sh if ed else md, outline=outline if r > 2.5 else None)
            d.pieslice([x - r * 0.92, y - r * 0.92, x + r * 0.6, y + r * 0.6], 150, 330, fill=lt)
        elif kind == 'cone':
            d.polygon([(x + 1.2 * kk, y - r * 1.4 + 1.8 * kk), (x + r + 1.2 * kk, y + r * 0.8 + 1.8 * kk), (x - r + 1.2 * kk, y + r * 0.8 + 1.8 * kk)], fill=shadow)
            d.polygon([(x, y - r * 1.4), (x + r, y + r * 0.8), (x - r, y + r * 0.8)], fill=sh, outline=outline if r > 2.5 else None)
            d.polygon([(x, y - r * 1.4), (x, y + r * 0.8), (x - r, y + r * 0.8)], fill=lt if not ed else md)
        elif kind == 'snag':
            d.line([(x, y - r), (x, y + r * 0.6)], fill=md, width=max(1, int(2 * kk))); d.line([(x, y - r * 0.3), (x + r * 0.6, y - r * 0.8)], fill=md, width=max(1, int(kk)))
        elif kind == 'reed':
            k_ = 'marsh' if (x - ox) / k > 9700 * g.WPX / 11264 * 0 + 10400 else 'reed'
            if k_ == 'marsh':
                wc = R['water_warm'][3]
                d.line([(x - r * 1.3, y + r * 0.5), (x + r * 1.3, y + r * 0.5)], fill=wc, width=max(1, int(1.2 * kk)))
                for o in (-1, 0, 1):
                    d.line([(x + o * r * 0.45, y + r * 0.35), (x + o * r * 0.7, y - r * 0.8)], fill=md, width=max(1, int(kk)))
            else:
                for o in (-2, 0, 2):
                    d.line([(x + o * kk, y + r), (x + o * 1.4 * kk, y - r)], fill=md, width=max(1, int(kk)))
        elif kind == 'tuft':
            d.line([(x - r, y), (x, y - r)], fill=md, width=max(1, int(kk))); d.line([(x, y - r), (x + r, y)], fill=md, width=max(1, int(kk)))
        elif kind == 'dot':
            d.ellipse([x - r, y - r, x + r, y + r], fill=md if rng.random() < 0.7 else sh)
        elif kind == 'crev':
            gx0, gy0 = grad; n_ = math.hypot(gx0, gy0)
            if n_ < 1e-6 or rng.random() < 0.35:
                continue
            ux, uy = -gy0 / n_, gx0 / n_
            d.line([(x - ux * r, y - uy * r), (x + ux * r, y + uy * r)], fill=md + (190,), width=max(1, int(kk)))
    mountains55(d, S, R, k, ox, oy, M, np.asarray(im).copy(), ink)
    return im


def mountains55(d, S, R, k, ox, oy, M, ground, ink):
    """The range in the same treatment as the trees: each peak two faces (lit west, shade east) from the stone ramp, a soft
    crest (fewer jags than v54's), a thin ink outline and a shadow cast to the south-east; snow above the snowline; the
    foothills and spurs in the colour of the ground they rise from."""
    F = features(S, M)
    P = lambda x, y: (x * k + ox, y * k + oy)
    kk = k / (2160 / g.HPX)
    st = R['stone']; sn = R['snow']; snc = R['snow_cool']
    outline = ink + (110,); shadow = ink + (60,)
    for c in F['glyphs']:
        X, Y = P(c['x'], c['y']); ht = c['ht'] * k; w = c['w'] * k
        if X + w < -5 or X - w > d.im.size[0] + 5 or Y - ht > d.im.size[1] + 5 or Y < -5:
            continue
        if c['kind'] == 'hill':
            gx0 = int(min(max(X, 0), ground.shape[1] - 1)); gy0 = int(min(max(Y - ht * 0.2, 0), ground.shape[0] - 1))
            col = tuple(int(v) for v in ground[gy0, gx0][:3])
            lt, md, sh = tones(mix(col, st[3], 0.18))
            n = 16
            pts = [(X - w / 2 + w * i / n + c['skew'] * w * math.sin(math.pi * i / n), Y - ht * math.sin(math.pi * i / n) ** 0.75) for i in range(n + 1)]
            d.polygon([(px + 0.08 * w, py + 0.05 * w) for px, py in pts], fill=shadow)
            d.polygon(pts, fill=sh)
            mid = n // 2
            d.polygon(pts[:mid + 1] + [(pts[mid][0] + 0.1 * w, Y)], fill=lt)
            d.polygon(pts[mid // 2:mid + 1] + [(pts[mid][0], Y)], fill=md)
            d.line(pts, fill=outline, width=max(1, int(round(0.8 * kk))))
            continue
        ax = X + c['skew'] * w; ay = Y - ht
        Lf = (X - w / 2, Y); Rf = (X + w / 2, Y)
        if c['v'] == 'twin':
            a2x = X + w * (0.22 if c['skew'] < 0 else -0.22); a2y = Y - ht * (0.8 + 0.08 * c['j3'])
            crest = [Lf, (min(a2x, ax), a2y if a2x < ax else ay), ((a2x + ax) / 2, Y - ht * 0.66), (max(a2x, ax), ay if a2x < ax else a2y), Rf]
        elif c['v'] == 'broad':
            crest = [Lf, (X - w * 0.2, Y - ht * 0.8), (ax, ay), (X + w * 0.24, Y - ht * 0.74), Rf]
        else:
            crest = [Lf, (X - w * 0.22, Y - ht * (0.55 + c['j1'])), (ax, ay), (X + w * 0.24, Y - ht * (0.5 + c['j2'])), Rf]
        top = min(crest, key=lambda p: p[1]); ia = crest.index(top)
        B = (X + w * 0.06 + c['skew'] * w * 0.3, Y)
        lit_c = st[4] if c['e'] > 0.72 else mix(st[4], R['grass_cool'][3], 0.3)
        lt, md, sh = tones(mix(lit_c, st[3], 0.4))
        d.polygon([(px + 0.12 * w, py + 0.05 * w) for px, py in crest], fill=shadow)
        d.polygon(crest[ia:] + [B], fill=sh)
        d.polygon(crest[:ia + 1] + [B], fill=lt)
        mid = [(top[0] + (B[0] - top[0]) * 0.5 - w * 0.05, top[1] + ht * 0.5), B]
        d.polygon([top] + mid + [((crest[1][0] + B[0]) / 2, Y)], fill=md)
        f = c['snow']
        if f > 0:
            ys = top[1] + ht * f
            xl = M54.edge_x(crest[:ia + 1][::-1], ys); xr = M54.edge_x(crest[ia:], ys)
            zz = max(1.2, ht * 0.05)
            xm = top[0] + (B[0] - top[0]) * (ys - top[1]) / max(1e-6, B[1] - top[1])
            d.polygon([top, (xm, ys + zz), (xr, ys)] + [p for p in crest[ia + 1:] if p[1] < ys][::-1], fill=snc[2])
            d.polygon([top] + [p for p in crest[:ia] if p[1] < ys][::-1] + [(xl, ys), ((xl + xm) / 2, ys + zz * 0.6), (xm, ys + zz)], fill=sn[5])
        d.line(crest, fill=outline, width=max(1, int(round(0.9 * kk))))
        if c.get('name'):
            d.line([(top[0], top[1] - 2 * kk), (top[0], top[1] - 7 * kk)], fill=st[0], width=max(1, int(round(kk))))


# ------------------------------------------------------------------------------------------ towns, the pass, the cape
ROOFS = {'valley': ('clay', 3), 'desert': ('sand_warm', 2), 'fire': ('basalt_warm', 3), 'mountain': ('slate', 3), 'city': ('slate', 3),
         'works': ('clay_warm', 2), 'isles': ('sand', 3), 'company': ('iron', 3)}
TOWN_ROOF = {'Dust Gulch': 'desert', 'Palm Spring': 'desert', 'the Lode': 'desert', 'Hearthold': 'fire', 'Cinderwick': 'fire', 'Cinder Springs': 'fire',
             'Ember forge': 'fire', 'Highgarth': 'mountain', 'Cogsworth': 'works', 'Lagoon Landing': 'isles', 'Launch Cape': 'company',
             'Neon Harbour: the Company district': 'company'}


def roof_colour(R, town, use):
    style = TOWN_ROOF.get(town, 'city' if town.startswith('Neon') else 'valley')
    if use in ('warehouse', 'hangar', 'station'):
        style = 'works' if style != 'company' else 'company'
    ramp, i = ROOFS[style]
    return R[ramp][i] if ramp in R else R['clay'][3]


def draw_towns(d, S, R, ink, P, s, k, neon_lights=True):
    """Every building as a small roof: a shadow to the south-east, the roof (lit on its west half), a thin ink edge."""
    kk = s
    for town, r in S['towns'].items():
        for (x, y, w, h_, use, counted) in r['buildings']:
            X0, Y0 = P(x, y); X1, Y1 = P(x + w, y + h_)
            if X1 - X0 < 1.0:
                d.rectangle([X0, Y0, X0 + 1, Y0 + 1], fill=roof_colour(R, town, use))
                continue
            c = roof_colour(R, town, use); lt, md, sh = tones(c)
            off = max(1.0, 0.9 * kk)
            d.rectangle([X0 + off, Y0 + off, X1 + off, Y1 + off], fill=ink + (70,))
            d.rectangle([X0, Y0, X1, Y1], fill=sh)
            if use in ('office', 'tower', 'hangar', 'warehouse', 'station', 'keep', 'hall'):
                d.rectangle([X0, Y0, X1, Y0 + (Y1 - Y0) * 0.55], fill=md)           # flat roofs: a lit parapet band
                d.line([(X0, Y0), (X1, Y0)], fill=lt, width=max(1, int(kk)))
            else:
                d.rectangle([X0, Y0, (X0 + X1) / 2, Y1], fill=lt)                    # a ridge roof: the west slope lit
            if X1 - X0 > 3.5:
                d.rectangle([X0, Y0, X1, Y1], outline=ink + (150,), width=1)
            if neon_lights and town == 'Neon Harbour: the Company district' and use in ('office', 'tower') and (int(x) // 8) % 3 == 0:
                d.line([(X0 + 1, Y1 - 1), (X1 - 1, Y1 - 1)], fill=R['berry'][4] + (230,), width=max(1, int(kk)))
    for f in S.get('farms', []):
        pass


def draw_closed_pass(d, S, M, R, ink, P, s):
    """The rockfall across the Northway (a heap of boulders), the road beyond drawn faint and dashed to the col, a barrier."""
    rx, ry = M.ROCKFALL
    X, Y = P(rx, ry)
    rng = np.random.default_rng(77)
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0, 7) * s; r_ = rng.uniform(1.6, 3.4) * s
        cx, cy = X + rr * math.cos(a) * 1.4, Y + rr * math.sin(a) * 0.8
        lt, md, sh = tones(R['stone'][3])
        d.ellipse([cx - r_ + 0.8 * s, cy - r_ + 0.8 * s, cx + r_ + 0.8 * s, cy + r_ + 0.8 * s], fill=ink + (70,))
        d.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], fill=sh, outline=ink + (120,))
        d.pieslice([cx - r_, cy - r_, cx + r_ * 0.5, cy + r_ * 0.5], 150, 330, fill=lt)
    pts = S['closed_px']
    polyline(d, pts, P, R['plaster'][5] + (120,), 2.2 * s, dash=(4 * s, 4 * s))
    polyline(d, pts, P, ink + (90,), 0.8 * s, dash=(4 * s, 4 * s))
    bx, by = X, Y + 9 * s                                          # the barrier: a red and white bar across the road
    for i in range(4):
        d.rectangle([bx - 8 * s + i * 4 * s, by - 1.4 * s, bx - 4 * s + i * 4 * s, by + 1.4 * s], fill=(R['berry'][4] if i % 2 == 0 else R['plaster'][5]), outline=ink)


def draw_cape(d, S, M, R, ink, P, s):
    """The rocket on its pad (a small upright, lit west), the masts of the Skyport."""
    X, Y = P(*M.PAD)
    d.ellipse([X - 4 * s, Y - 2 * s, X + 4 * s, Y + 2 * s], fill=ink + (70,))
    d.polygon([(X, Y - 13 * s), (X + 2.4 * s, Y - 6 * s), (X + 2.4 * s, Y), (X - 2.4 * s, Y), (X - 2.4 * s, Y - 6 * s)], fill=R['plaster'][5], outline=ink)
    d.polygon([(X, Y - 13 * s), (X - 2.4 * s, Y - 6 * s), (X - 2.4 * s, Y), (X, Y)], fill=R['snow'][5])
    d.line([(X + 4.5 * s, Y), (X + 4.5 * s, Y - 14 * s)], fill=ink, width=max(1, int(s)))


# ------------------------------------------------------------------------------------------ the cloud edge
def cloud_bank(canvas, S, M, R, s, k, ox, oy, window=None):
    """An irregular cloud bank where the land runs off the canvas (the top, and the sides where the edge is land), its
    outline shaped by noise at three scales, lit from the upper left; a gap above the closed pass shows the land beyond."""
    Wc, Hc = canvas.size
    yy, xx = np.mgrid[0:Hc, 0:Wc].astype(np.float32)
    rng = np.random.default_rng(91)

    def fbm1(n, scales, seed):
        out = np.zeros(n, np.float32); r = np.random.default_rng(seed)
        for sc, amp in scales:
            pts = r.uniform(-1, 1, int(n / sc) + 3)
            out += amp * np.interp(np.arange(n) / sc, np.arange(len(pts)), pts)
        return out
    depth_top = 20 * s + fbm1(Wc, [(160 * s, 14 * s), (48 * s, 9 * s), (16 * s, 3.5 * s)], 911)
    if window is not None:                                          # the gap over the pass
        wx = window[0]; ww = 20 * s
        depth_top = depth_top * (1 - 0.95 * np.exp(-((np.arange(Wc) - wx) / ww) ** 2))
    cloud = yy < depth_top[None, :]
    land_x0 = ox; land_x1 = ox + g.WPX * k
    rows = np.clip(((np.arange(Hc) - oy) / k / CELL).astype(int), 0, g.H - 1)
    for side, xe, col in (('l', land_x0, 0), ('r', land_x1, g.W - 1)):
        landrow = S['land'][rows, col].astype(np.float32)
        landrow = ndi.uniform_filter1d(landrow, int(30 * s)) > 0.2
        dep = 18 * s + fbm1(Hc, [(130 * s, 14 * s), (40 * s, 9 * s), (14 * s, 3.5 * s)], 912 if side == 'l' else 913)
        dep = np.where(landrow, dep, -40 * s)
        dep = ndi.gaussian_filter1d(dep, 6 * s)
        if side == 'l':
            cloud |= xx < (xe + dep[:, None])
        else:
            cloud |= xx > (xe - dep[:, None])
    cloud |= (xx < land_x0) & (yy < 30 * s)                        # the corners close
    cloud |= (xx > land_x1) & (yy < 30 * s)
    cm = ndi.gaussian_filter(cloud.astype(np.float32), 2.5 * s)
    gy, gx = np.gradient(ndi.gaussian_filter(cloud.astype(np.float32), 5 * s))
    light = np.clip(0.5 + 6 * s * (gx + gy), 0, 1)                    # brighter where the bank faces the upper left
    base = np.array(R['snow'][3], np.float32); lit = np.array(R['snow'][5], np.float32); shd = np.array(R['snow'][1], np.float32)
    col = base[None, None, :] * (1 - 0.6 * light[..., None]) + lit[None, None, :] * (0.6 * light[..., None])
    inner = ndi.gaussian_filter(cloud.astype(np.float32), 9 * s)
    col = col * (0.85 + 0.15 * inner[..., None]) + lit * 0.15 * inner[..., None]
    # puffs inside the bank: a soft texture lit on its upper left, so it reads as cloud, not a band
    tex = ndi.gaussian_filter(rng.standard_normal((Hc, Wc)).astype(np.float32), 5 * s)
    tex = tex / (tex.std() + 1e-6)
    ty, tx = np.gradient(tex)
    puff = np.clip(0.5 - 2.2 * s * (tx + ty), 0, 1)
    col = col * (0.94 + 0.08 * puff[..., None]) - np.array([6, 5, 2], np.float32) * (1 - puff[..., None]) * inner[..., None]
    shadow = ndi.shift(cm, (3 * s, 4 * s), order=1) * (1 - cm)        # the bank's shadow on the land, to the south-east
    arr = np.asarray(canvas).astype(np.float32)
    arr = arr * (1 - 0.22 * shadow[..., None])
    a = np.clip(cm * 1.25, 0, 1)[..., None]
    edge = (cm > 0.15) & (cm < 0.6)
    col = np.where(edge[..., None], col * 0.93 + shd * 0.07, col)
    arr = arr * (1 - a) + col * a
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def far_land(canvas, M, R, s, P):
    """The land beyond the pass, seen through the gap in the cloud: hazy ridges, paler with distance."""
    d = ImageDraw.Draw(canvas, 'RGBA')
    X, Y = P(*M.HIGHGARTH_PASS)
    top = 10 * s                                                   # below the frame's double line
    for i, (dy, col, al) in enumerate(((0, R['sky'][4], 150), (5, R['stone'][4], 120), (10, R['grass_cool'][4], 110))):
        pts = [(X - 22 * s + j * 4.4 * s, top + dy * s + 3 * s * (1 + math.sin(j * 1.1 + i * 2.0))) for j in range(11)]
        d.polygon(pts + [(X + 22 * s, top + dy * s + 10 * s), (X - 22 * s, top + dy * s + 10 * s)], fill=col + (al,))


# ------------------------------------------------------------------------------------------ labels by zoom
def names(M):
    """Every name with its v55 point: map53's and map54's lists moved by the warp, and v55's new places."""
    Pr = M.Pr
    region = [(t, *Pr((x, y))) for t, x, y in M53.REGION_NAMES]
    region = [(t, x, y) if t != 'NEON HARBOUR' else (t, 11500, 3820) for t, x, y in region]
    region = [(t, x, y) if t != 'THE FIRE COUNTRY' else (t, 1080, 5560) for t, x, y in region]
    region += [('THE NORTHERN RANGE', 4300, 520)]
    biome = [(t, *Pr((x, y))) for t, x, y in M54.BIOME_NAMES]
    biome = [b for b in biome if b[0] not in ('the Heights',)]
    biome += [('the upper Cog', 8200, 1500), ('Launch Cape', 12230, 6560), ('the east coast', 12440, 4720)]
    small = [(nm, *Pr((x, y)), kind) for nm, x, y, kind in M54.SMALL_PLACES if nm not in ('the old town', 'the docks', 'new town', 'the Skyport', 'Gull Strand')]
    small += [('the rockfall', M.ROCKFALL[0] + 40, M.ROCKFALL[1], 'gate'), ('the slate quarry', 8120, 1110, 'place'), ('the folds', 7915, 900, 'place'),
              ('the Skyport', 10030, 4905, 'place'), ('the pad', M.PAD[0], M.PAD[1] + 40, 'place'), ("the Company's yard", 11780, 4159, 'place'),
              ('Bridgefoot', 11135, 4462, 'place'), ('the fish market', 11228, 5078, 'place'), ('the slip', 11480, 5430, 'place'),
              ('Terminus Square', 11650, 4565, 'place'), ('the East Shore', 12150, 5150, 'place'), ('the Lanes', 11420, 4380, 'place'),
              ('the corrals', 2910, 2460, 'place'), ('the goods yard', 2730, 2272, 'place'), ('the date gardens', 3280, 2980, 'place'),
              ('the wood yards', 7405, 2940, 'place'), ('the railway yard', 8385, 2815, 'place'), ('the kilns', 2670, 5800, 'place'),
              ('the boatyard', 6810, 6520, 'place'), ("the drovers' market", 6712, 3532, 'place'), ('the halt yard', 5880, 4078, 'place'),
              ('the vines', 2455, 5700, 'place'), ('the market gardens', 10020, 4560, 'place')]
    small += [(nm, x, y, 'farm') for x, y, nm in M.FARMS] + [(nm, x, y, 'mill') for x, y, nm in M.WINDMILLS]
    gates = [(nm, *Pr((x, y)), w) for nm, x, y, w in M54.GATES]
    return region, biome, small, gates


MAJOR = {'Crossroads', 'Dust Gulch', 'Palm Spring', 'Fernhollow', 'Cogsworth', 'Hearthold', 'Cinderwick', 'Lagoon Landing', 'Highgarth', 'Neon Harbour'}
MINOR_TOWNS = {'Driftwood', 'Lullford', 'Gullwick', 'Cinder Springs', 'the Lode', 'Ember forge', 'Launch Cape', 'Halcyon Row', 'Glintside', 'Canalside'}
PRINCIPAL = {"Drover's Road", 'Lull Road', 'Ash Coast', 'Canyon Road', 'Foothill Road', 'the Garth Road', 'Coast Path', 'High Fells', 'Towpath'}


def labels55(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, reserved, mode='continent', box=None):
    """Names on their own layer, none overlapping. mode 'continent': regions, the towns and the city, the circle, the principal
    routes and the closed pass. mode 'full' (the reference and the insets): every name."""
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    pl = Placer(d, Wc, Hc)
    cream, inkc = R['plaster'][5], ink
    full = mode == 'full'
    for b in reserved:
        pl.reserve(b)
    region, biome, small, gates = names(M)
    FE = features(S, M)
    icons = []
    settle = dict(g.SETTLE); settle.pop('Home valley', None); settle.pop('the Frostline', None)
    settle['Crossroads'] = (M.CROSSROADS[0], M.CROSSROADS[1], 300, 'town')
    for nm, (x, y, r, kind) in settle.items():
        if nm in MAJOR:
            icons.append((nm, x, y, 'city' if nm == 'Neon Harbour' else ('hilltown' if kind in ('hilltown', 'castle') else 'town'), 'town', 1))
        elif full or nm in ('Launch Cape',):
            icons.append((nm, x, y, 'cape' if nm == 'Launch Cape' else 'village', 'town2', 1))
    icons.append(('the stone circle', M.CIRCLE[0], M.CIRCLE[1], 'circle', 'circle', 1))
    for nm, (x, y, r, region_, story) in M.CRATERS.items():
        if nm != 'the Crossroads crater':
            icons.append((nm, x, y, 'crater', 'crater' if full else 'none', 2))
    if full:
        for nm, x, y, w in gates:
            icons.append((nm, x, y, 'gate', 'gate' if w else 'gate3', 2 if w else 3))
        for nm, (x, y, st) in M.WAYSTONES.items():
            icons.append(('waystone: ' + nm, x, y, 'waystone_' + st, 'none', 9))
        for nm, x, y, kind in small:
            icons.append((nm, x, y, kind if kind not in ('farm', 'mill') else 'place', 'place', 3))
        for town, r in S['towns'].items():
            if town.startswith('Neon Harbour: '):
                icons.append((town.split(': ')[1], r['centre'][0], r['centre'][1], 'none', 'district', 2))
    else:
        for nm, x, y, w in gates:
            if w:
                icons.append((nm, x, y, 'gate', 'none', 9))
    placed_icons = []
    for nm, x, y, kind, cat, tier in icons:
        X, Y = P(x, y)
        if not (0 <= X <= Wc and 0 <= Y <= Hc):
            continue
        if kind == 'none':
            placed_icons.append((nm, X, Y, 2 * s, cat, kind, tier)); continue
        r = icon(d, kind, X, Y, s, R, ink)
        pl.reserve((X - r, Y - r, X + r, Y + r)); placed_icons.append((nm, X, Y, r, cat, kind, tier))
    # the closed pass: always named (it is part of the geography now)
    X, Y = P(*M.ROCKFALL)
    if 0 <= X <= Wc and 0 <= Y <= Hc:
        pl.reserve((X - 9 * s, Y - 8 * s, X + 9 * s, Y + 14 * s))
        placed_icons.append(('the Highgarth pass (closed)', X, Y, 10 * s, 'closed', 'closed', 1))
    if full:
        for nm, (x, y, rn, way, why) in M.PASSES.items():
            X, Y = P(x, y)
            if 0 <= X <= Wc and 0 <= Y <= Hc:
                r = 4.5 * s
                for sgn in (-1, 1):
                    bx = X + sgn * 3.2 * s; b_ = [bx - r, Y - r, bx + r, Y + r]
                    d.arc(b_, 300 if sgn < 0 else 120, 60 if sgn < 0 else 240, fill=ink, width=max(1, int(2.6 * s)))
                    d.arc(b_, 300 if sgn < 0 else 120, 60 if sgn < 0 else 240, fill=cream, width=max(1, int(1.2 * s)))
                pl.reserve((X - 8 * s, Y - 5 * s, X + 8 * s, Y + 5 * s)); placed_icons.append((nm, X, Y, 8 * s, 'pass', 'pass', 3))
        for nm, p in FE['named_peaks'].items():
            X, Y = P(p['x'], p['apex_y'])
            if 0 <= X <= Wc and 0 <= Y <= Hc:
                placed_icons.append((nm, X, Y - 4 * s, 3 * s, 'peak', 'peak', 2))
        for nm, x, y, w in gates:
            if w:
                X, Y = P(x, y); bx, by = X + 5 * s, Y - 9 * s
                b = (bx - 1 * s, by - 5 * s, bx + 14 * s, by + 5 * s)
                if pl.free(b):
                    d.rounded_rectangle(b, radius=2 * s, fill=R['berry'][3], outline=ink); d.text(((b[0] + b[2]) / 2, by), w, font=F['way'], fill=cream, anchor='mm'); pl.reserve(b)
    for t, x, y in region:
        if box is not None and not (box[0] + 300 <= x <= box[2] - 300 and box[1] + 120 <= y <= box[3] - 120):
            continue
        X, Y = P(x, y)
        if not (0 <= X <= Wc and 0 <= Y <= Hc):
            continue
        pl.put((X, Y), t, F['region'], cream, inkc, [(0, 0, 'mm'), (0, -18 * s, 'mm'), (0, 18 * s, 'mm'), (40 * s, 0, 'mm'), (-40 * s, 0, 'mm'),
                                                     (90 * s, 30 * s, 'mm'), (-90 * s, 30 * s, 'mm'), (0, 50 * s, 'mm'), (160 * s, 40 * s, 'mm'), (0, -50 * s, 'mm')],
               stroke=int(3 * s), spacing=3 * s, pad=2 * s, name=t if box is None else False)
    order = sorted(placed_icons, key=lambda p: (p[6], {'circle': -1, 'town': 0, 'closed': 0, 'town2': 1, 'district': 1, 'crater': 2, 'peak': 3, 'gate': 4,
                                                         'pass': 5, 'gate3': 6, 'place': 7, 'none': 9}[p[4]]))

    def name_icon(p, pad, leader):
        nm, X, Y, r, cat, kind, tier = p
        if cat == 'none':
            return
        font, fill, st = F['place'], R['plaster'][5], inkc
        if cat == 'town':
            font, fill = F['town'], cream
        elif cat == 'town2':
            font = F['place']
        elif cat == 'district':
            font, fill = F['place'], R['brass'][5]
        elif cat == 'circle':
            font, fill = F['town'], R['brass'][5]
        elif cat == 'closed':
            font, fill, st = F['gate'], R['berry'][5], inkc
        elif cat == 'crater':
            font, fill, st = F['place'], R['dusk'][5], R['dusk'][0]
        elif cat in ('gate', 'gate3', 'pass'):
            font, fill = F['gate'], R['brass'][5]
        elif cat == 'peak':
            font, fill, st = F['peak'], R['snow'][5], R['stone'][0]
        offs = around(r, s) if cat != 'peak' else [(0, -2 * s, 'mb'), (8 * s, -2 * s, 'lb'), (-8 * s, -2 * s, 'rb'), (0, 12 * s, 'mt')]
        pl.put((X, Y), nm, font, fill, st, offs, stroke=int(2 * s), pad=pad, leader=leader, name=nm if tier <= 2 else False)
    for p in order:
        if p[6] == 1:
            name_icon(p, 1, [p[3] + 14 * s, p[3] + 24 * s, p[3] + 36 * s])
    if full:
        for t, x, y in biome:
            X, Y = P(x, y)
            if 0 <= X <= Wc and 0 <= Y <= Hc:
                pl.put((X, Y), t, F['biome'], R['snow'][5], mix(ink, R['stone'][1], 0.3), [(0, 0, 'mm'), (0, -14 * s, 'mm'), (0, 14 * s, 'mm'), (30 * s, 0, 'mm'),
                                                                                            (-30 * s, 0, 'mm'), (0, -28 * s, 'mm'), (0, 28 * s, 'mm'), (60 * s, 0, 'mm'),
                                                                                            (-60 * s, 0, 'mm')], stroke=int(2 * s), spacing=1 * s, pad=1 * s, name=False)
    for p in order:
        if p[6] == 2:
            name_icon(p, 1, [p[3] + 14 * s, p[3] + 24 * s])
    for p in order:
        if p[6] >= 3:
            name_icon(p, 1, None)
    # routes: the principal ones on the continent map; every route, water and line in full
    for nm, sm in S['route_px'].items():
        if nm.startswith('Valley lane') or nm in ('Old Bridges', 'Quay Street', 'Forge Stair', 'Beacon Causeway', 'Harbour Bridge', 'Shell Bar', 'the Northway (closed)'):
            continue
        if not full and nm not in PRINCIPAL:
            continue
        M54.rotated2(pl, lay, sm, P, nm, F['route'], R['path'][5], inkc, s, [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8, 0.45, 0.55, 0.35, 0.65, 0.15, 0.85])
    for nm, kind, pts, way in lines:
        label = {'valley train': 'the valley train', 'desert line (Rift viaduct)': 'the desert line', 'maglev (Narrows Viaduct)': 'the maglev',
                 'ferry': 'the isles ferry', 'mine cart (S1)': 'the mine cart', 'coastal steamer (S3)': 'the coastal steamer'}.get(nm, nm)
        if not full and kind == 'cart':
            continue
        M54.rotated2(pl, lay, pts, P, label, F['route'], R['snow'][5] if kind == 'boat' else R['plaster'][5], inkc, s, [0.5, 0.4, 0.6, 0.3, 0.7], italic=True)
    if full:
        for nm, pts in S['river_px'].items():
            if nm in ('the Dry Fork', 'Brackens wash'):
                continue
            for frac in (0.42, 0.3, 0.58, 0.7, 0.2, 0.5, 0.36, 0.64, 0.8, 0.25, 0.75, 0.12, 0.88):
                q = pts[int(len(pts) * frac)]; X, Y = P(*q)
                if pl.put((X, Y), nm, F['water'], R['sky'][5], R['water'][0], [(0, -9 * s, 'mb'), (0, 9 * s, 'mt'), (12 * s, 0, 'lm'), (-12 * s, 0, 'rm')],
                          stroke=int(2 * s), name=False, pad=1):
                    break
        for nm, pts in M.DRY_BEDS.items():
            q = pts[len(pts) // 2]; X, Y = P(*q)
            pl.put((X, Y), nm, F['water'], R['sand'][5], R['sand'][0], [(10 * s, 0, 'lm'), (-10 * s, 0, 'rm'), (0, -9 * s, 'mb')], stroke=int(2 * s), name=False, pad=2 * s)
        for t, x, y in [('the southern sea', 9000, 6650), ('the ria', 10850, 4950), ('the eastern sea', 12470, 5900)]:
            X, Y = P(x, y); pl.put((X, Y), t, F['water'], R['sky'][5], R['water'][0], [(0, 0, 'mm'), (0, 14 * s, 'mm')], stroke=int(2 * s), name=False)
        for nm, p in FE['glaciers'].items():
            X, Y = P(p['x'], p['y'])
            if 0 <= X <= Wc and 0 <= Y <= Hc:
                pl.put((X, Y), nm, F['water'], R['snow'][5], R['sky'][1], [(0, 0, 'mm'), (0, 12 * s, 'mm'), (0, -12 * s, 'mm')], stroke=int(2 * s), name=False)
    return lay, pl


# ------------------------------------------------------------------------------------------ panels
def panel_boxes(Wc, Hc, s):
    """The legend top left, the ruler bottom left (over the sea), the north arrow top right (over the old forest; Launch Cape
    now fills the bottom right)."""
    return [(12 * s, 12 * s, 330 * s, 334 * s), (12 * s, Hc - 150 * s, 560 * s, Hc - 12 * s), (Wc - 120 * s, 40 * s, Wc - 12 * s, 158 * s)]


def panels55(lay, S, M, R, ink, s, k, Wc, Hc, F, act1=True, title='The continent: overview (v55)'):
    M53.panel_boxes = panel_boxes
    M53.panels(lay, S, M, R, ink, s, k, Wc, Hc, F, act1=act1, title=title)
    d = ImageDraw.Draw(lay)
    lb = panel_boxes(Wc, Hc, s)[0]
    x0, y = lb[0] + 12 * s, lb[1] + 34 * s + 6 * 16 * s
    # two more legend rows, in the gap at the legend's right
    bx = lb[0] + 196 * s
    d.rectangle([bx, lb[1] + 40 * s, bx + 7 * s, lb[1] + 45 * s], fill=R['clay'][2], outline=ink)
    d.rectangle([bx, lb[1] + 40 * s, bx + 3.5 * s, lb[1] + 45 * s], fill=mix(R['clay'][3], (255, 248, 226), 0.22))
    d.text((bx + 12 * s, lb[1] + 42.5 * s), 'a building', font=F['small'], fill=ink, anchor='lm')
    d.rectangle([bx - 2 * s, lb[1] + 56 * s, bx + 10 * s, lb[1] + 58.4 * s], fill=R['berry'][4], outline=ink)
    d.text((bx + 12 * s, lb[1] + 57 * s), 'closed pass', font=F['small'], fill=ink, anchor='lm')
    rb = panel_boxes(Wc, Hc, s)[1]
    d.text((rb[2] - 10 * s, rb[1] + 12 * s), f'v55 canvas {g.WPX} x {g.HPX} world px (v54: 11264 x 6912)', font=F['small'], fill=R['timber'][2], anchor='rt')


# ------------------------------------------------------------------------------------------ compose
def frame_fit(Wc, Hc, s):
    k = Hc / g.HPX
    if g.WPX * k > Wc - 20 * s:
        k = (Wc - 20 * s) / g.WPX
    ox = (Wc - g.WPX * k) / 2; oy = (Hc - g.HPX * k) / 2
    return k, ox, oy


def compose(S, M, R, ink, s, base, k, ox, oy, Wc, Hc, paths, lines, mode, title, panels_on=True, box=None, act=True):
    F = M54.fonts54(M.ROOT, s)
    canvas = Image.new('RGB', (Wc, Hc), R['snow'][3])
    px0, py0 = (0, 0) if box is not None else (int(round(ox)), int(round(oy)))     # an inset's base is already cut to its box
    canvas.paste(base, (px0, py0))
    # the sea runs on flat into the margins where the edge is sea
    arr = np.asarray(canvas).copy(); x0 = px0; x1 = min(Wc, x0 + base.width)
    if x0 > 0:
        arr[:, :x0] = arr[:, x0:x0 + 1]
    if 0 < x1 < Wc:
        arr[:, x1:] = arr[:, x1 - 1:x1]
    y0 = py0; y1 = min(Hc, y0 + base.height)
    if y0 > 0:
        arr[:y0] = arr[y0:y0 + 1]
    if 0 < y1 < Hc:
        arr[y1:] = arr[y1 - 1:y1]
    canvas = Image.fromarray(arr)
    P = lambda x, y: (x * k + ox, y * k + oy)
    M54.water_and_routes(canvas, S, R, ink, k, ox, oy, M)
    d = ImageDraw.Draw(canvas, 'RGBA')
    draw_lines(d, lines, P, R, ink, s)
    draw_towns(d, S, R, ink, P, s, k)
    draw_closed_pass(d, S, M, R, ink, P, s)
    draw_cape(d, S, M, R, ink, P, s)
    if box is None:
        canvas = cloud_bank(canvas, S, M, R, s, k, ox, oy, window=P(*M.HIGHGARTH_PASS))
        far_land(canvas, M, R, s, P)
        d = ImageDraw.Draw(canvas, 'RGBA')
    if box is None and mode == 'continent':
        M54.inset_mark(d, M, R, ink, P, s)
    if box is None and mode == 'continent':
        nb = M.NEON_INSET; pts = [(nb[0], nb[1]), (nb[2], nb[1]), (nb[2], nb[3]), (nb[0], nb[3]), (nb[0], nb[1])]
        polyline(d, pts, P, R['plaster'][5] + (170,), 2.4 * s, dash=(6 * s, 5 * s)); polyline(d, pts, P, ink + (150,), 1.0 * s, dash=(6 * s, 5 * s))
    d.rectangle([3 * s, 3 * s, Wc - 3 * s, Hc - 3 * s], outline=ink, width=max(1, int(2 * s)))
    d.rectangle([7 * s, 7 * s, Wc - 7 * s, Hc - 7 * s], outline=R['timber'][3], width=max(1, int(s)))
    reserved = (panel_boxes(Wc, Hc, s) if panels_on else []) + [(0, 0, Wc, 26 * s)]
    reserved += [(X - 7 * s, Y - 7 * s, X + 7 * s, Y + 7 * s) for i, X, Y in M54.act_marks(M, P, s)] if act else []
    reserved += [M54.built_tag(P, s)]
    lab, pl = labels55(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, reserved, mode=mode, box=box)
    built = M54.overlay_built(S, M, R, ink, s, k, ox, oy, Wc, Hc, F)
    layers = [built]
    if act:
        layers.insert(0, M54.overlay_ring(S, M, R, ink, s, k, ox, oy, Wc, Hc, F))
    layers.append(lab)
    if act:
        layers.append(M54.overlay_act1(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, paths))
    out = canvas.convert('RGBA')
    for layer in layers:
        out.alpha_composite(layer)
    if panels_on:
        pan = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); panels55(pan, S, M, R, ink, s, k, Wc, Hc, F, act1=act, title=title)
        out.alpha_composite(pan)
    return out, pl.missed, {'canvas': canvas, 'built': built, 'labels': lab}


def class_grid(S, R, M):
    """map54's classes; a land cell left without one (a route cell whose nearest ground was sea, at a bridge's end) takes
    the class of the nearest classed land cell."""
    cg, names_, cid, cols = M54.class_grid(S, R, M)
    hole = S['land'] & (cg < 0)
    if hole.any():
        _, (iy, ix) = ndi.distance_transform_edt(~(S['land'] & (cg >= 0)), return_indices=True)
        cg = np.where(hole, cg[iy, ix], cg)
    return cg, names_, cid, cols


def render_all(S, M):
    R, ink = load_palette(M.ROOT)
    cg, names_, cid, cols = class_grid(S, R, M)
    rgb = M54.cell_colours(S, R, cg, cid, cols); sea_rgb = M54.sea_colours(S, R)
    paths = act1_path(S, M); lines = rail_lines(S)
    outs = [os.environ.get('MAP55_OUT')] if os.environ.get('MAP55_OUT') else []
    outs.append(M.HERE)
    for o in outs:
        os.makedirs(o, exist_ok=True)
    full_box = (0, 0, g.W, g.H)
    missed_all = {}
    # the continent at 1920 and 3840 (one base at the 3840 scale, resampled for 1920)
    s2 = 2; Wc, Hc = BASE_W * s2, BASE_H * s2
    k, ox, oy = frame_fit(Wc, Hc, s2)
    base = M54.base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, full_box, 2.5)          # 2.5 px a cell: whole strips, no seams
    base = base.resize((int(round(g.WPX * k)), int(round(g.HPX * k))), Image.LANCZOS)
    stamps55(base, S, R, cg, cid, k, 0, 0, M, ink)
    res2, missed, parts2 = compose(S, M, R, ink, s2, base, k, ox, oy, Wc, Hc, paths, lines, 'continent', 'The continent: overview (v55)')
    missed_all['3840'] = missed
    s1 = 1; Wc1, Hc1 = BASE_W, BASE_H
    k1, ox1, oy1 = frame_fit(Wc1, Hc1, s1)
    base1 = base.resize((int(round(g.WPX * k1)), int(round(g.HPX * k1))), Image.LANCZOS)
    res1, missed, parts1 = compose(S, M, R, ink, s1, base1, k1, ox1, oy1, Wc1, Hc1, paths, lines, 'continent', 'The continent: overview (v55)')
    missed_all['1920'] = missed
    for o in outs:
        res1.convert('RGB').save(os.path.join(o, 'map55-1920.png'))
        res2.convert('RGB').save(os.path.join(o, 'map55-3840.png'))
    small = res1.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    small.save(os.path.join(M.DATA, 'continent-1x-v55.png'), optimize=True)
    v54 = Image.open(os.path.join(M.DATA, 'continent-1x-v54.png')).convert('RGB')
    cmp_ = Image.new('RGB', (1920 * 2 + 24, 1080 + 40), (30, 26, 34)); dc = ImageDraw.Draw(cmp_)
    cmp_.paste(v54, (0, 40)); cmp_.paste(res1.convert('RGB'), (1920 + 24, 40))
    Fc = fonts(M.ROOT, 1)
    dc.text((10, 20), 'v54 (11264 x 6912 world px)', font=Fc['title'], fill=(240, 230, 210), anchor='lm')
    dc.text((1920 + 34, 20), 'v55 (12544 x 7168: towns at their footprints, the east coast and Launch Cape, Highgarth and the closed pass)', font=Fc['title'],
            fill=(240, 230, 210), anchor='lm')
    for o in outs:
        cmp_.save(os.path.join(o, 'map55-v54-vs-v55.png'))
    # the reference: the whole continent at 3x with every name
    s3 = 3; Wc3, Hc3 = BASE_W * s3, BASE_H * s3
    k3, ox3, oy3 = frame_fit(Wc3, Hc3, s3)
    base3 = M54.base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, full_box, 3.75)
    base3 = base3.resize((int(round(g.WPX * k3)), int(round(g.HPX * k3))), Image.LANCZOS)
    stamps55(base3, S, R, cg, cid, k3, 0, 0, M, ink)
    res3, missed, _ = compose(S, M, R, ink, s3 * 0.8, base3, k3, ox3, oy3, Wc3, Hc3, paths, lines, 'full', 'The continent: reference (v55), every name')
    missed_all['reference'] = missed
    for o in outs:
        res3.convert('RGB').save(os.path.join(o, 'map55-reference.png'))
    del base3, res3
    # the insets: the home valley and Neon Harbour, every name
    for tag, bx, ppc, title in (('home-valley', M.INSET, 4.0, 'The home valley (v55 inset)'), ('neon-harbour', M.NEON_INSET, 4.0, 'Neon Harbour and Launch Cape (v55 inset)')):
        x0, y0, x1, y1 = bx
        cbox = (x0 // CELL, y0 // CELL, x1 // CELL, y1 // CELL)
        kb = ppc / CELL; s_ = 1.3
        img = M54.base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, cbox, ppc)
        oxb, oyb = -cbox[0] * CELL * kb, -cbox[1] * CELL * kb
        stamps55(img, S, R, cg, cid, kb, oxb, oyb, M, ink)
        Wb, Hb = img.size
        out, missed, _ = compose(S, M, R, ink, s_, img, kb, oxb, oyb, Wb, Hb, paths, lines, 'full', title, panels_on=False, box=bx, act=(tag == 'home-valley'))
        dd = ImageDraw.Draw(out); F = M54.fonts54(M.ROOT, s_)
        paper = R['plaster'][5] + (236,); edge = R['timber'][2]
        tb = (12 * s_, 12 * s_, 600 * s_, 66 * s_)
        dd.rounded_rectangle(tb, radius=6 * s_, fill=paper, outline=edge, width=max(1, int(2 * s_)))
        dd.text((tb[0] + 12 * s_, tb[1] + 10 * s_), title, font=F['title'], fill=ink, anchor='lt')
        dd.text((tb[0] + 12 * s_, tb[1] + 38 * s_), f'world px {x0} to {x1} east, {y0} to {y1} south; 1 px = {1 / kb:.1f} world px',
                font=F['small'], fill=R['timber'][2], anchor='lt')
        rb = (12 * s_, Hb - 62 * s_, 430 * s_, Hb - 12 * s_)
        dd.rounded_rectangle(rb, radius=6 * s_, fill=paper, outline=edge, width=max(1, int(2 * s_)))
        v = S['hero']['walk_speed_world_px_s']; cpx = 8 * kb
        bxx, byy = rb[0] + 14 * s_, rb[1] + 26 * s_
        marks = [0, 10, 50, 100]
        for a, b_ in zip(marks, marks[1:]):
            dd.rectangle([bxx + a * cpx, byy, bxx + b_ * cpx, byy + 6 * s_], fill=ink if marks.index(a) % 2 == 0 else R['plaster'][3], outline=ink)
        for m_ in marks[1:]:
            dd.text((bxx + m_ * cpx, byy - 3 * s_), f'{m_}' + (' cells' if m_ == 100 else ''), font=F['small'], fill=ink, anchor='mb')
            dd.text((bxx + m_ * cpx, byy + 9 * s_), f'{m_ * 8 / v:.0f} s', font=F['small'], fill=R['timber'][2], anchor='mt')
        dd.text((bxx + 100 * cpx + 40 * s_, byy + 3 * s_), "Bramble's walk", font=F['small'], fill=ink, anchor='lm')
        missed_all['inset-' + tag] = missed
        for o in outs:
            out.convert('RGB').save(os.path.join(o, f'map55-inset-{tag}.png'))
        out.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(os.path.join(M.DATA, f'inset-{tag}-v55.png'), optimize=True)
    print('labels not placed (tiers 1 and 2):', json.dumps(missed_all))
    return missed_all
