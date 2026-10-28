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


# ------------------------------------------------------------------------------------------ the label font's B
# PixelifySans draws its capital B with rounded left corners, the same shape as its G and 8, so at map sizes "TIDEBLOOM"
# reads "TIDEGLOOM" and "HARBOUR" "HARGOUR". The map squares the B's left side (a full-height stem), drawing over the
# glyph; the game's font file is not changed.
def _stem(font):
    """The left stem of the font's B: (x offset, width) in px, measured from the glyph."""
    key = (getattr(font, 'path', ''), font.size)
    if key not in _STEM:
        m = font.getmask('B'); w, h = m.size
        arr = np.array(m, dtype=np.uint8).reshape(h, w) > 127
        cols = arr[h // 2 - 1:h // 2 + 2].any(0) if h > 4 else arr.any(0)
        x0 = int(np.argmax(cols)); x1 = x0
        while x1 < w and cols[x1]:
            x1 += 1
        _STEM[key] = (x0, max(1, x1 - x0))
    return _STEM[key]


_STEM = {}
_draw_text = Placer.draw_text


def _draw_text_b(self, xy, text, font, fill, stroke_fill, anchor='mm', stroke=2, spacing=0):
    _draw_text(self, xy, text, font, fill, stroke_fill, anchor, stroke, spacing)
    if 'B' not in text or 'Pixelify' not in getattr(font, 'path', ''):
        return
    # where each B sits: the same advance as the drawing above
    if spacing:
        w = sum(self.d.textlength(ch, font=font) for ch in text) + spacing * (len(text) - 1)
        x = xy[0] - w / 2 if anchor[0] == 'm' else (xy[0] if anchor[0] == 'l' else xy[0] - w)
        starts = []
        for ch in text:
            starts.append(x); x += self.d.textlength(ch, font=font) + spacing
        anc = 'lm'; ys = [xy[1]] * len(text)
    else:
        bb = self.d.textbbox(xy, text, font=font, anchor=anchor)
        starts = [bb[0] + self.d.textlength(text[:i], font=font) for i in range(len(text))]; anc = 'lm'; ys = [(bb[1] + bb[3]) / 2] * len(text)
    sx, sw = _stem(font)
    for ch, x0, y in zip(text, starts, ys):
        if ch != 'B':
            continue
        gb = self.d.textbbox((x0, y), 'B', font=font, anchor=anc)
        l = gb[0] + sx - (self.d.textbbox((x0, y), 'B', font=font, anchor=anc)[0] - gb[0])
        self.d.rectangle([l - stroke, gb[1] - stroke, l + sw - 1 + stroke, gb[3] - 1 + stroke], fill=stroke_fill)
        _draw_text(self, (x0, y), 'B', font, fill, stroke_fill, anc, stroke, 0)
        self.d.rectangle([l, gb[1], l + sw - 1, gb[3] - 1], fill=fill)


Placer.draw_text = _draw_text_b


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


def plan_buildings(S):
    """Every building from the town plans (towns/<id>.json): (town, x, y, w, h, use); the old records when there are none."""
    if S.get('plans'):
        out = []
        for P in S['plans'].values():
            dt = {d_['id']: d_.get('town', P['name']) for d_ in P['districts']}
            for b in P['buildings']:
                x, y, w, h_ = b['rect_px']
                out.append((dt.get(b['district'], P['name']), x, y, w, h_, b['type'], b.get('form', b['type']), b.get('door_cells')))
        return out
    return [(town, x, y, w, h_, use, use, None) for town, r in S['towns'].items() for (x, y, w, h_, use, counted) in r['buildings']]


FLAT = {'office', 'tower', 'hangar', 'warehouse', 'station', 'keep', 'hall'}


def draw_towns(d, S, R, ink, P, s, k, neon_lights=True):
    """Every building as a small roof, drawn by its form: a shadow to the south-east, a ridge roof lit on its west slope (an
    apartment row or a terrace split into its houses), flat roofs with a lit parapet (warehouses with roof lights, slabs and towers
    with a core, adobes pale and flat), and a tall board front on the street side of a frontier shop, saloon or depot."""
    kk = s
    for (town, x, y, w, h_, use, form, door) in plan_buildings(S):
        X0, Y0 = P(x, y); X1, Y1 = P(x + w, y + h_)
        if X1 - X0 < 1.0:
            d.rectangle([X0, Y0, X0 + 1, Y0 + 1], fill=roof_colour(R, town, use))
            continue
        c = roof_colour(R, town, use); lt, md, sh = tones(c)
        if form == 'adobe':
            lt, md, sh = tones(R['sand_warm'][3] if 'sand_warm' in R else c)
        off = max(1.0, 0.9 * kk)
        d.rectangle([X0 + off, Y0 + off, X1 + off, Y1 + off], fill=ink + (70,))
        d.rectangle([X0, Y0, X1, Y1], fill=sh)
        long_x = (X1 - X0) >= (Y1 - Y0)
        if use in FLAT or form in ('adobe', 'slab', 'bigtower'):
            d.rectangle([X0, Y0, X1, Y0 + (Y1 - Y0) * 0.55], fill=md)               # flat roofs: a lit parapet band
            d.line([(X0, Y0), (X1, Y0)], fill=lt, width=max(1, int(kk)))
            if form == 'longwarehouse' and X1 - X0 > 6:                            # roof lights across a long warehouse
                n = max(2, int(w // 32))
                for i in range(1, n):
                    if long_x:
                        xx = X0 + (X1 - X0) * i / n; d.line([(xx, Y0 + 1), (xx, Y1 - 1)], fill=lt + (200,), width=1)
                    else:
                        yy = Y0 + (Y1 - Y0) * i / n; d.line([(X0 + 1, yy), (X1 - 1, yy)], fill=lt + (200,), width=1)
            if form in ('slab', 'bigtower') and X1 - X0 > 6:                         # the lift and stair core
                cx_, cy_ = (X0 + X1) / 2, (Y0 + Y1) / 2; r_ = max(1.0, min(X1 - X0, Y1 - Y0) * 0.16)
                d.rectangle([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], fill=sh, outline=lt)
        elif form in ('aptrow', 'terrace') and X1 - X0 > 4:                            # a row: the ridge along it, one house a bay
            if long_x:
                d.rectangle([X0, Y0, X1, (Y0 + Y1) / 2], fill=lt)
                n = max(2, int(w // 24))
                for i in range(1, n):
                    xx = X0 + (X1 - X0) * i / n; d.line([(xx, Y0), (xx, Y1)], fill=ink + (110,), width=1)
            else:
                d.rectangle([X0, Y0, (X0 + X1) / 2, Y1], fill=lt)
                n = max(2, int(h_ // 24))
                for i in range(1, n):
                    yy = Y0 + (Y1 - Y0) * i / n; d.line([(X0, yy), (X1, yy)], fill=ink + (110,), width=1)
        else:
            d.rectangle([X0, Y0, (X0 + X1) / 2, Y1], fill=lt)                        # a ridge roof: the west slope lit
        if form in ('frontshop', 'saloon', 'depot') and door and X1 - X0 > 3:          # the false front on the street side
            dx, dy = door; fx, fy = P(dx * CELL + 4, dy * CELL + 4)
            t_ = max(1.0, 6 * k)
            front = R['plaster'][4]
            if fy >= Y1 - 0.5:
                d.rectangle([X0, Y1 - t_, X1, Y1], fill=front, outline=ink + (200,))
            elif fy <= Y0 + 0.5:
                d.rectangle([X0, Y0, X1, Y0 + t_], fill=front, outline=ink + (200,))
            elif fx <= X0 + 0.5:
                d.rectangle([X0, Y0, X0 + t_, Y1], fill=front, outline=ink + (200,))
            else:
                d.rectangle([X1 - t_, Y0, X1, Y1], fill=front, outline=ink + (200,))
        if X1 - X0 > 3.5:
            d.rectangle([X0, Y0, X1, Y1], outline=ink + (150,), width=1)
        if neon_lights and town == 'Neon Harbour: the Company district' and use in ('office', 'tower') and (int(x) // 8) % 3 == 0:
            d.line([(X0 + 1, Y1 - 1), (X1 - 1, Y1 - 1)], fill=R['berry'][4] + (230,), width=max(1, int(kk)))


def draw_walls(d, S, R, ink, P, k):
    """A fortified town's wall from its plan: dark stone two cells thick with a lit top edge, square towers, the gate open."""
    for P_ in (S.get('plans') or {}).values():
        F = P_.get('fortification')
        if not F:
            continue
        xs = [v[0] for v in F['wall_px']]; ys = [v[1] for v in F['wall_px']]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys); t_ = F.get('thick_cells', 2) * CELL
        gates = [g_ for g_ in F['gates'] if g_.get('open', True)]
        stone, lit = R['stone'][1], R['stone'][4]
        segs = [(x0, y0, x1, y0 + t_), (x0, y1 - t_, x1, y1), (x0, y0, x0 + t_, y1), (x1 - t_, y0, x1, y1)]
        out = []
        for (a, b, c, e) in segs:                                   # cut the gates out of their wall
            pieces = [(a, b, c, e)]
            for g_ in gates:
                gx0, gx1 = g_['x_px']; gy0, gy1 = g_['y_px']
                nxt = []
                for (pa, pb, pc, pe) in pieces:
                    if gy0 < pe and gy1 > pb and gx0 < pc and gx1 > pa:
                        if pc - pa >= pe - pb:
                            nxt += [(pa, pb, gx0, pe), (gx1, pb, pc, pe)]
                        else:
                            nxt += [(pa, pb, pc, gy0), (pa, gy1, pc, pe)]
                    else:
                        nxt.append((pa, pb, pc, pe))
                pieces = nxt
            out += [q for q in pieces if q[2] > q[0] and q[3] > q[1]]
        off = max(1.0, 3 * k)
        for (a, b, c, e) in out:
            X0, Y0 = P(a, b); X1, Y1 = P(c, e)
            d.rectangle([X0 + off, Y0 + off, X1 + off, Y1 + off], fill=ink + (90,))
        for (a, b, c, e) in out:
            X0, Y0 = P(a, b); X1, Y1 = P(c, e)
            d.rectangle([X0, Y0, X1, Y1], fill=stone, outline=ink)
            d.line([(X0, Y0), (X1, Y0)], fill=lit, width=max(1, int(round(2 * k))))
        for (tx, ty) in F.get('towers_px', []):
            X0, Y0 = P(tx - 2 * CELL, ty - 2 * CELL); X1, Y1 = P(tx + 2 * CELL, ty + 2 * CELL)
            d.rectangle([X0 + off, Y0 + off, X1 + off, Y1 + off], fill=ink + (90,))
            d.rectangle([X0, Y0, X1, Y1], fill=stone, outline=ink)
            d.rectangle([X0, Y0, X1, Y0 + (Y1 - Y0) * 0.3], fill=lit)


def draw_street_bridges(d, S, R, ink, P, k):
    """Where a town street crosses water: a plank deck as wide as the street, with its side rails (the plans' bridge cells)."""
    import sys as _s
    rp = os.path.join(os.environ.get('REPO_ROOT', ''), 'scripts', 'review')
    if rp not in _s.path:
        _s.path.insert(0, rp)
    import town_plan as tp
    deck, rail = R['timber'][4], R['timber'][2]
    for P_ in (S.get('plans') or {}).values():
        c0, r0, w, h = P_['terrain']['box_cells']
        ter = tp.rle_decode(P_['terrain']['rows'], w)
        if not (ter == 'b').any():
            continue
        m = np.zeros((h, w), bool)
        for st in P_['streets']:
            if st['class'] != 'arrival':
                m |= tp.band([tuple(v) for v in st['vertices_px']], st['width_cells'], 'euclid' if st.get('follows_route') else 'cheb', (c0, r0, w, h))
        bm = m & (ter == 'b')
        lab, n = ndi.label(bm)
        for sl_ in ndi.find_objects(lab):                             # one deck a crossing, its rails along its edge
            if sl_ is None:
                continue
            r0_, r1_, c0_, c1_ = sl_[0].start, sl_[0].stop, sl_[1].start, sl_[1].stop
            X0, Y0 = P((c0_ + c0) * CELL, (r0_ + r0) * CELL); X1, Y1 = P((c1_ + c0) * CELL, (r1_ + r0) * CELL)
            d.rectangle([X0, Y0, X1, Y1], fill=deck, outline=rail, width=max(1, int(round(1.5 * k))))


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
    biome += [('the upper Cog', 8200, 1500), ('the east coast', 12440, 4720)]
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
QUIET = ['the old forest', 'the moss fens', 'the dune sea', 'the salt lake', 'the dead forest', 'the moor', 'Mount Ember', 'the Lull delta',
         'the southern sea', 'the northern massif', 'the coal hills', 'the Narrows']          # the continent map's second tier: edges, landmarks
VILLAGES = ['Driftwood', 'Lullford', 'Gullwick', 'Cinder Springs', 'Lane End', 'Glintside', 'Canalside', 'Halcyon Row']
MINOR_TOWNS = {'Driftwood', 'Lullford', 'Gullwick', 'Cinder Springs', 'the Lode', 'Ember forge', 'Launch Cape', 'Halcyon Row', 'Glintside', 'Canalside'}
PRINCIPAL = {"Drover's Road", 'Lull Road', 'Ash Coast', 'Canyon Road', 'Foothill Road', 'the Garth Road', 'Coast Path', 'High Fells', 'Towpath'}


def labels55(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, reserved, mode='continent', box=None):
    """Names on their own layer, none overlapping. mode 'continent': regions, the towns and the city, the circle, the principal
    routes and the closed pass. mode 'full' (the reference and the insets): every name."""
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    pl = Placer(d, Wc, Hc)
    _put = pl.put; done = set()

    def put_once(xy, text, *a, **kw):                                # one label per name
        if text in done:
            return None
        b = _put(xy, text, *a, **kw)
        if b is not None:
            done.add(text)
        return b
    pl.put = put_once
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
        elif nm in VILLAGES:
            icons.append((nm, x, y, 'place', 'village', 2))
    if not full:
        for x, y, nm in M.FARMS:
            if nm in VILLAGES:
                icons.append((nm, x, y, 'place', 'village', 2))
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
    order = sorted(placed_icons, key=lambda p: (p[6], {'circle': -1, 'town': 0, 'closed': 0, 'town2': 1, 'village': 1, 'district': 1, 'crater': 2, 'peak': 3, 'gate': 4,
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
        elif cat == 'village':
            font, fill, st = F['place'], mix(R['plaster'][5], R['stone'][3], 0.25), mix(ink, R['stone'][1], 0.35)
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
    if not full:                                                     # the quieter second tier: edges and landmarks
        qf = F['quiet']; qfill = mix(R['snow'][5], R['stone'][3], 0.3); qst = mix(ink, R['stone'][1], 0.45)
        for t, x, y in biome:
            if t in QUIET:
                X, Y = P(x, y)
                pl.put((X, Y), t, qf, qfill, qst, [(0, 0, 'mm'), (0, -12 * s, 'mm'), (0, 12 * s, 'mm'), (30 * s, 0, 'mm'), (-30 * s, 0, 'mm'),
                                                   (0, -24 * s, 'mm'), (0, 24 * s, 'mm'), (60 * s, 0, 'mm'), (-60 * s, 0, 'mm')],
                       stroke=max(1, int(1.5 * s)), spacing=1 * s, pad=1 * s, name=False)
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
    F['quiet'] = ImageFont.truetype(os.path.join(M.ROOT, 'game', 'ui', 'fonts', 'PixelifySans-Regular.ttf'), int(round(13 * s)))
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
    draw_street_bridges(d, S, R, ink, P, k)
    draw_walls(d, S, R, ink, P, k)
    draw_towns(d, S, R, ink, P, s, k)
    neon_accents(d, S, P, s, k, lines)
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


# ------------------------------------------------------------------------------------------ the town plans, one inset each
TOWN_INSETS = (('crossroads', 8.0), ('dust-gulch', 8.0), ('hearthold', 8.0), ('neon-harbour', 4.5))
CLASS_COL = {'main': (247, 236, 206), 'side': (236, 220, 186), 'lane': (222, 204, 168), 'close': (204, 184, 150)}
FN_COL = {'market and civic': (178, 64, 74), 'homes': (196, 120, 74), 'crafts and work': (150, 112, 52), 'docks and transport': (54, 106, 150),
          'offices and trade': (112, 74, 150), 'edge': (88, 128, 64)}


def _fn_col(fn):
    for k_, c in FN_COL.items():
        if fn.startswith(k_):
            return c
    return FN_COL['edge'] if fn.startswith('edge') else (120, 120, 120)


class _D:
    def __init__(self, d):
        self.d = d


def town_inset(S, M, R, ink, cg, cid, rgb, sea_rgb, P, ppc):
    """One town's plan over its ground: streets by class, buildings by district, doors, squares, landmarks, the ways in, later
    shortcuts and quiet corners; one phone screen (40 x 22.5 cells) drawn for scale."""
    import sys as _s
    sys_path = os.path.join(M.ROOT, 'scripts', 'review')
    if sys_path not in _s.path:
        _s.path.insert(0, sys_path)
    import town_plan as tp
    c0, r0, w, h = P['terrain']['box_cells']
    cbox = (c0, r0, c0 + w, r0 + h)
    kb = ppc / CELL
    img = M54.base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, cbox, ppc)
    oxb, oyb = -c0 * CELL * kb, -r0 * CELL * kb
    stamps55(img, S, R, cg, cid, kb, oxb, oyb, M, ink)
    s_ = 1.4 if ppc >= 6 else 1.3
    Wb, Hb = img.size
    side = int(330 * s_)
    Hc_ = Hb                                                         # cropped to the map: the side panel scales to fit it
    canvas = Image.new('RGB', (Wb + side, Hc_), R['plaster'][5]); canvas.paste(img, (0, 0))
    M54.water_and_routes(canvas, S, R, ink, kb, oxb, oyb, M)
    Pf = lambda x, y: (x * kb + oxb, y * kb + oyb)
    d = ImageDraw.Draw(canvas, 'RGBA')
    box = (c0, r0, w, h)
    # streets by class (their cells), centre lines
    ov = np.zeros((h, w, 4), np.uint8)
    ter_ = tp.rle_decode(P['terrain']['rows'], w)
    for st in sorted(P['streets'], key=lambda q: ['close', 'lane', 'side', 'main', 'arrival'].index(q['class'])):
        if st['class'] == 'arrival':
            continue
        m = tp.band([tuple(v) for v in st['vertices_px']], st['width_cells'], 'euclid' if st.get('follows_route') else 'cheb', box)
        ov[m & ~np.isin(ter_, ['~', 'b'])] = CLASS_COL[st['class']] + (150,)
    ovi = Image.fromarray(ov, 'RGBA').resize((int(w * ppc), int(h * ppc)), Image.NEAREST)
    canvas.paste(ovi, (0, 0), ovi)
    d = ImageDraw.Draw(canvas, 'RGBA')
    for st in P['streets']:
        if st['class'] in ('arrival',):
            continue
        q = [Pf(*v) for v in st['vertices_px']]
        if len(q) >= 2:
            d.line(q, fill=ink + (90 if st['class'] != 'close' else 60,), width=1)
    draw_street_bridges(d, S, R, ink, Pf, kb)
    draw_walls(d, S, R, ink, Pf, kb)
    draw_towns(d, S, R, ink, Pf, max(1.0, ppc / 4), kb)
    if P['id'] == 'neon-harbour':
        mat = S.get('mat')
        if mat is not None:                                          # the Company district's slab modules: light lines every 4 cells
            sub = mat[r0:r0 + h, c0:c0 + w]
            for rr in range(0, h, 4):
                for cc in np.nonzero(sub[rr] == 2)[0]:
                    d.line([(cc * ppc, rr * ppc), ((cc + 1) * ppc, rr * ppc)], fill=(210, 236, 250, 150), width=1)
            for cc in range(0, w, 4):
                for rr in np.nonzero(sub[:, cc] == 2)[0]:
                    d.line([(cc * ppc, rr * ppc), (cc * ppc, (rr + 1) * ppc)], fill=(210, 236, 250, 150), width=1)
        neon_accents(d, S, Pf, max(1.0, ppc / 3), kb, rail_lines(S))
    dfn = {d_['id']: d_['function'] for d_ in P['districts']}
    for b in P['buildings']:
        x, y, bw, bh = b['rect_px']; X0, Y0 = Pf(x, y); X1, Y1 = Pf(x + bw, y + bh)
        d.rectangle([X0 - 1, Y0 - 1, X1, Y1], outline=_fn_col(dfn.get(b['district'], '')) + (255,), width=2 if ppc >= 6 else 1)
        if b.get('door_cells'):
            dx, dy = b['door_cells']; Xd, Yd = Pf(dx * CELL + 4, dy * CELL + 4)
            r_ = max(1.5, ppc * 0.35)
            d.rectangle([Xd - r_, Yd - r_, Xd + r_, Yd + r_], fill=ink + (230,))
    lay = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay, 'RGBA')
    pl = Placer(dl, Wb, Hb)
    texts = []                                                       # every label box, checked for overlaps at the end
    _put = pl.put

    def put_(*a, **kw):
        kw.setdefault('pad', 4)
        b = _put(*a, **kw)
        if b:
            texts.append((a[1], b))
        return b
    pl.put = put_
    F = M54.fonts54(M.ROOT, s_)
    paper = R['plaster'][5]
    # markers first (reserved), then names
    for l in P['game_layout']['landmarks']:
        X, Y = Pf(*l['xy']); r_ = 6 * s_
        star = [(X + (r_ if i % 2 == 0 else r_ * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5), Y + (r_ if i % 2 == 0 else r_ * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
        dl.polygon(star, fill=(236, 196, 72, 255), outline=ink + (255,)); pl.reserve((X - r_, Y - r_, X + r_, Y + r_))
    for a in P['arrivals']:
        for e in a['entries_px']:
            X, Y = Pf(*e); X = min(max(X, 10 * s_), Wb - 10 * s_); Y = min(max(Y, 10 * s_), Hb - 10 * s_)
            r_ = 7 * s_
            dl.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(70, 130, 170, 235), outline=ink + (255,), width=2)
            dl.text((X, Y), 'in', font=F['way'], fill=paper, anchor='mm')
            pl.reserve((X - r_, Y - r_, X + r_, Y + r_))
            pl.put((X, Y), a['route'] if a['kind'] != 'ferry' else 'the ferry from Driftwood', F['route'], ink, paper + (230,), around(r_, s_), stroke=2, name=False)
    for q in P['game_layout'].get('shortcuts_later', []):
        X, Y = Pf(*q['xy']); r_ = 7 * s_
        if 0 <= X <= Wb and 0 <= Y <= Hb:
            for a0 in range(0, 360, 40):
                dl.arc([X - r_, Y - r_, X + r_, Y + r_], a0, a0 + 22, fill=(150, 70, 150, 255), width=2)
            pl.reserve((X - r_, Y - r_, X + r_, Y + r_))
    for q in P['game_layout'].get('quiet_corners', []):
        X, Y = Pf(*q['xy']); r_ = 5 * s_
        if 0 <= X <= Wb and 0 <= Y <= Hb:
            dl.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(120, 170, 110, 220), outline=ink + (200,))
            pl.reserve((X - r_, Y - r_, X + r_, Y + r_))
    for b in P['buildings']:
        x, y, bw, bh = b['rect_px']; X0, Y0 = Pf(x, y); X1, Y1 = Pf(x + bw, y + bh)
        pl.reserve((X0, Y0, X1, Y1))
    for l in P['game_layout']['landmarks']:
        X, Y = Pf(*l['xy'])
        pl.put((X, Y), l['name'], F['small'], ink, paper + (235,), around(7 * s_, s_), stroke=2, leader=[22 * s_, 34 * s_], name=False)
    for q in P['squares']:
        cx, cy, cw, ch_ = q['cells']; X, Y = Pf((cx + cw / 2) * CELL, (cy + ch_ / 2) * CELL)
        if q['name']:
            pl.put((X, Y), q['name'], F['small'], (60, 50, 40), paper + (220,), [(0, 0, 'mm'), (0, -10 * s_, 'mm'), (0, 10 * s_, 'mm')], stroke=2, name=False)
    seen = set()
    for st in sorted(P['streets'], key=lambda q: -len(q['vertices_px'])):
        nm = st.get('name')
        if not nm or st['class'] in ('arrival', 'close') or nm in seen:
            continue
        nm_ = nm.split(' (')[0]
        if nm_ in seen:
            continue
        v = st['vertices_px']
        best = max(zip(v, v[1:]), key=lambda ab: math.hypot(ab[1][0] - ab[0][0], ab[1][1] - ab[0][1]))
        X, Y = Pf((best[0][0] + best[1][0]) / 2, (best[0][1] + best[1][1]) / 2)
        if pl.put((X, Y), nm_, F['route'], (70, 52, 36), paper + (220,), [(0, 0, 'mm'), (0, -9 * s_, 'mm'), (0, 9 * s_, 'mm'), (14 * s_, 0, 'lm'), (-14 * s_, 0, 'rm')], stroke=2, name=False):
            seen.add(nm_)
    for d_ in P['districts']:
        if d_.get('buildings'):
            bs = [b for b in P['buildings'] if b['district'] == d_['id']]
            X, Y = Pf(np.mean([b['rect_px'][0] + b['rect_px'][2] / 2 for b in bs]), np.mean([b['rect_px'][1] + b['rect_px'][3] / 2 for b in bs]))
        elif d_.get('box_px'):
            bx = d_['box_px']; X, Y = Pf((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)
        else:
            continue
        if d_['name'] in seen:
            continue
        if 0 <= X <= Wb and 0 <= Y <= Hb:
            pl.put((X, Y), d_['name'].upper() if d_.get('buildings') else d_['name'], F['legend'], _fn_col(d_['function']), paper + (235,),
                   [(0, 0, 'mm'), (0, -16 * s_, 'mm'), (0, 16 * s_, 'mm'), (30 * s_, 0, 'lm'), (-30 * s_, 0, 'rm')], stroke=3, leader=[40 * s_], name=False)
    over = [(a, b) for i, (a, ba) in enumerate(texts) for (b, bb) in texts[i + 1:]
            if not (ba[2] <= bb[0] or bb[2] <= ba[0] or ba[3] <= bb[1] or bb[3] <= ba[1])]
    if over:
        raise RuntimeError(f"{P['id']}: labels overlap: {over[:4]}")
    P['_labels'] = len(texts)
    canvas = canvas.convert('RGBA'); canvas.alpha_composite(lay)
    d = ImageDraw.Draw(canvas, 'RGBA')
    # one phone screen, for scale (bottom left of the map)
    sw, sh = 40 * CELL * kb, 22.5 * CELL * kb
    sx0, sy0 = 14 * s_, Hb - sh - 14 * s_
    d.rectangle([sx0, sy0, sx0 + sw, sy0 + sh], outline=ink + (230,), width=2)
    d.rectangle([sx0 + 2, sy0 + 2, sx0 + sw - 2, sy0 + sh - 2], outline=paper + (200,), width=1)
    _D_ = _D(d)
    Placer.draw_text(_D_, (sx0, sy0 - 4 * s_), 'one screen: 40 x 22.5 cells', F['small'], ink, paper, 'lb', 2)
    # the side panel: title, numbers, legend (scaled down when the map is short)
    s_ = s_ * min(1.0, Hb / (720 * s_))
    F = M54.fonts54(M.ROOT, s_)
    d.rectangle([Wb, 0, Wb + side, Hc_], fill=paper)
    if Hc_ > Hb:
        d.rectangle([0, Hb, Wb, Hc_], fill=paper)
    d.line([(Wb, 0), (Wb, Hc_)], fill=ink, width=2)
    x0 = Wb + 14 * s_; y = 14 * s_
    Placer.draw_text(_D_, (x0, y + 10 * s_), P['name'], F['title'], ink, paper, 'lm', 0); y += 30 * s_
    Placer.draw_text(_D_, (x0, y + 6 * s_), 'town plan, v55 (towns/%s.json)' % P['id'], F['small'], R['timber'][2], paper, 'lm', 0); y += 22 * s_
    nblk = P.get('_blocks')
    lines_ = [f"{P['buildings_counted']} buildings (range {P['target'][0]} to {P['target'][1]})",
              f"{sum(1 for q in P['streets'] if q['class'] not in ('arrival', 'close'))} streets, {sum(1 for q in P['streets'] if q['class'] == 'close')} closes, {len(P['squares'])} squares",
              f"{len(P['arrivals'])} ways in; {len([d_ for d_ in P['districts'] if d_.get('buildings')])} districts",
              f"{P['game_layout']['screens'][0]} x {P['game_layout']['screens'][1]} screens"]
    for t_ in lines_:
        Placer.draw_text(_D_, (x0, y + 6 * s_), t_, F['small'], ink, paper, 'lm', 0); y += 17 * s_
    y += 10 * s_
    Placer.draw_text(_D_, (x0, y + 6 * s_), 'Streets (width in cells)', F['legend'], ink, paper, 'lm', 0); y += 20 * s_
    for cl, wc in (('main', 6), ('side', 4), ('lane', 3), ('close', 2)):
        d.rectangle([x0, y, x0 + 26 * s_, y + 10 * s_], fill=CLASS_COL[cl] + (255,), outline=ink)
        Placer.draw_text(_D_, (x0 + 34 * s_, y + 5 * s_), f'{cl} ({wc})', F['small'], ink, paper, 'lm', 0); y += 16 * s_
    d.line([(x0, y + 5 * s_), (x0 + 26 * s_, y + 5 * s_)], fill=R['plaster'][2], width=int(4 * s_))
    Placer.draw_text(_D_, (x0 + 34 * s_, y + 5 * s_), 'regional route (a way in)', F['small'], ink, paper, 'lm', 0); y += 22 * s_
    Placer.draw_text(_D_, (x0, y + 6 * s_), 'Districts (outline colour)', F['legend'], ink, paper, 'lm', 0); y += 20 * s_
    used = sorted({d_['function'] for d_ in P['districts']})
    for fn in used:
        d.rectangle([x0, y, x0 + 26 * s_, y + 10 * s_], outline=_fn_col(fn) + (255,), width=3)
        Placer.draw_text(_D_, (x0 + 34 * s_, y + 5 * s_), fn, F['small'], ink, paper, 'lm', 0); y += 16 * s_
    y += 8 * s_
    Placer.draw_text(_D_, (x0, y + 6 * s_), 'Marks', F['legend'], ink, paper, 'lm', 0); y += 20 * s_
    for what in ('landmark (seen from the ways in)', 'way in', 'door', 'shortcut that opens later', 'quiet corner'):
        X, Y = x0 + 13 * s_, y + 5 * s_; r_ = 5 * s_
        if what.startswith('landmark'):
            star = [(X + (r_ if i % 2 == 0 else r_ * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5), Y + (r_ if i % 2 == 0 else r_ * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
            d.polygon(star, fill=(236, 196, 72, 255), outline=ink)
        elif what == 'way in':
            d.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(70, 130, 170, 235), outline=ink)
        elif what == 'door':
            d.rectangle([X - 2, Y - 2, X + 2, Y + 2], fill=ink)
        elif what.startswith('shortcut'):
            for a0 in range(0, 360, 40):
                d.arc([X - r_, Y - r_, X + r_, Y + r_], a0, a0 + 22, fill=(150, 70, 150, 255), width=2)
        else:
            d.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(120, 170, 110, 220), outline=ink)
        Placer.draw_text(_D_, (x0 + 34 * s_, y + 5 * s_), what, F['small'], ink, paper, 'lm', 0); y += 16 * s_
    y += 10 * s_
    Placer.draw_text(_D_, (x0, y + 6 * s_), 'First view', F['legend'], ink, paper, 'lm', 0); y += 18 * s_
    words = P['game_layout']['first_view'].split(); line = ''
    for wd in words:
        if d.textlength(line + ' ' + wd, font=F['small']) > side - 28 * s_:
            Placer.draw_text(_D_, (x0, y + 6 * s_), line.strip(), F['small'], ink, paper, 'lm', 0); y += 15 * s_; line = ''
        line += ' ' + wd
    Placer.draw_text(_D_, (x0, y + 6 * s_), line.strip(), F['small'], ink, paper, 'lm', 0); y += 15 * s_
    Placer.draw_text(_D_, (x0, Hc_ - 12 * s_), f'1 px = {1 / kb:.2f} world px; cells of 8 px', F['small'], R['timber'][2], paper, 'lm', 0)
    d.rectangle([2, 2, canvas.width - 3, canvas.height - 3], outline=ink, width=2)
    return canvas


def class_grid(S, R, M):
    """map54's classes; a land cell left without one (a route cell whose nearest ground was sea, at a bridge's end) takes
    the class of the nearest classed land cell. The city's paved ground (the town plans' materials 1 to 6, the cape's
    apron) is paved, so no tree or tuft is stamped on it."""
    cg, names_, cid, cols = M54.class_grid(S, R, M)
    hole = S['land'] & (cg < 0)
    if hole.any():
        _, (iy, ix) = ndi.distance_transform_edt(~(S['land'] & (cg >= 0)), return_indices=True)
        cg = np.where(hole, cg[iy, ix], cg)
    mat = S.get('mat')
    if mat is not None and 'paved' in cid:
        cg = np.where(S['land'] & np.isin(mat, [1, 2, 3, 4, 5, 6, 12]), cid['paved'], cg)
    return cg, names_, cid, cols


def ground_tints(rgb, S):
    """The towns' ground (town_plans.MATERIALS): each material mixed into the cell's colour, a subtle change on the same cells;
    the reef shallows tint the sea instead."""
    mat = S.get('mat')
    if mat is None:
        return rgb
    rgb = rgb.copy()
    import town_plans as TP                                          # the table as it is now (the state keeps the codes)
    for code, (nm, col, a) in TP.MATERIALS.items():
        m = (mat == code) & S['land']
        if m.any():
            rgb[m] = rgb[m] * (1 - a) + np.array(col, np.float32) * a
    return rgb


def sea_tints(sea_rgb, S):
    mat = S.get('mat')
    if mat is None:
        return sea_rgb
    sea_rgb = sea_rgb.copy()
    m = (mat == 23) & ~S['land']
    if m.any():
        import town_plans as TP
        nm, col, a = TP.MATERIALS[23]
        sea_rgb[m] = sea_rgb[m] * (1 - a) + np.array(col, np.float32) * a
    return sea_rgb


NEON_CYAN, NEON_MAGENTA = (64, 232, 240), (236, 72, 196)


def neon_accents(d, S, P, s, k, lines=()):
    """Neon Harbour's retro-future ground on the overview: thin cyan and magenta light strips along both kerbs of its main and
    side streets (on the cell lines), and a cyan strip beside the maglev into the terminus."""
    plan = (S.get('plans') or {}).get('neon-harbour')
    if not plan:
        return
    wpx = max(1, int(round(0.6 * s)))
    for st in plan['streets']:
        if st['class'] not in ('main', 'side'):
            continue
        hw = st['width_cells'] * CELL / 2 - 2
        v = st['vertices_px']
        for (ax, ay), (bx, by) in zip(v, v[1:]):
            L = math.hypot(bx - ax, by - ay)
            if L < 8:
                continue
            nx, ny = -(by - ay) / L, (bx - ax) / L
            if nx + ny > 0:
                nx, ny = -nx, -ny                                     # cyan on the north or west kerb, magenta on the other
            d.line([P(ax + nx * hw, ay + ny * hw), P(bx + nx * hw, by + ny * hw)], fill=NEON_CYAN + (230,), width=wpx)
            d.line([P(ax - nx * hw, ay - ny * hw), P(bx - nx * hw, by - ny * hw)], fill=NEON_MAGENTA + (220,), width=wpx)
    x0, y0, x1, y1 = plan['footprint_px']
    for nm, kind, pts, way in lines:
        if 'maglev' not in nm:
            continue
        q = [(x, y) for x, y in pts if x0 - 600 <= x <= x1 and y0 - 600 <= y <= y1]
        if len(q) >= 2:
            off = 6
            qq = []
            for i, (x, y) in enumerate(q):
                a_, b_ = q[max(0, i - 1)], q[min(len(q) - 1, i + 1)]
                L = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1
                qq.append(P(x - (b_[1] - a_[1]) / L * off, y + (b_[0] - a_[0]) / L * off))
            d.line(qq, fill=NEON_CYAN + (235,), width=wpx)


def render_all(S, M):
    R, ink = load_palette(M.ROOT)
    cg, names_, cid, cols = class_grid(S, R, M)
    rgb = ground_tints(M54.cell_colours(S, R, cg, cid, cols), S); sea_rgb = sea_tints(M54.sea_colours(S, R), S)
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
    for pid, ppc in TOWN_INSETS:
        P = (S.get('plans') or {}).get(pid)
        if not P:
            continue
        out = town_inset(S, M, R, ink, cg, cid, rgb, sea_rgb, P, ppc)
        for o in outs:
            out.convert('RGB').save(os.path.join(o, f'map55-town-{pid}.png'))
        out.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(os.path.join(M.DATA, f'town-{pid}-v55.png'), optimize=True)
    print('labels not placed (tiers 1 and 2):', json.dumps(missed_all))
    return missed_all
