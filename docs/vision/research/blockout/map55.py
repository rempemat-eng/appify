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


def stamps55(im, S, R, cg, cid, k, ox, oy, M, ink, peaks=True, calm=(), sparse=None):
    calm_m = S.get('calm_mask')                                      # v56: no dot, tuft or snag marks round the fire country's towns
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
        if nm not in cid or nm in calm:                              # v56 leaves the lava field's dots to its relief
            continue
        ci = cid[nm]; sp = sp * kk * ((sparse or {}).get(nm, 1.0)); r = r * kk
        ys = np.arange(sp / 2, im.height, sp); xs = np.arange(sp / 2, im.width, sp)
        for yi, y in enumerate(ys):
            for x in xs + (sp / 2 if yi % 2 else 0):
                jx, jy = x + rng.uniform(-sp * 0.32, sp * 0.32), y + rng.uniform(-sp * 0.32, sp * 0.32)
                cc = cell(jx, jy)
                if cc is None or cg[cc[1], cc[0]] != ci:
                    continue
                if calm_m is not None and kind in ('dot', 'tuft', 'snag') and calm_m[cc[1], cc[0]]:
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
    if peaks:                                                       # v56 draws the range as relief (grow56) instead
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
                out.append((dt.get(b['district'], P['name']), x, y, w, h_, b['type'], b.get('form', b['type']), b.get('door_cells'), b.get('bays')))
        return out
    return [(town, x, y, w, h_, use, use, None, None) for town, r in S['towns'].items() for (x, y, w, h_, use, counted) in r['buildings']]


ROOF_RGB = {'flat': (150, 150, 146), 'tin': (112, 130, 146), 'tile': (172, 92, 64), 'slate': (88, 96, 112), 'thatch': (190, 160, 96), 'stone': (140, 132, 120)}


def draw_bays(d, ink, P, x, y, w, h_, bays, k, kk, tile=None):
    """A block of fronts sharing walls: each bay its own roof (flat with clutter, pitched tin, tiles, slate, thatch), the taller
    ones casting a longer shadow, a dark line on each party wall."""
    along_x = abs(sum(q['w_cells'] for q in bays) * CELL - w) <= abs(sum(q['w_cells'] for q in bays) * CELL - h_)
    at = 0
    for q in bays:
        bw = q['w_cells'] * CELL
        bx, by, bww, bhh = (x + at, y, bw, h_) if along_x else (x, y + at, w, bw)
        X0, Y0 = P(bx, by); X1, Y1 = P(bx + bww, by + bhh)
        off = max(1.0, (0.6 + 0.5 * q.get('storeys', 1)) * kk)
        d.rectangle([X0 + off, Y0 + off, X1 + off, Y1 + off], fill=ink + (60,))
        at += bw
    at = 0
    for i, q in enumerate(bays):
        bw = q['w_cells'] * CELL
        bx, by, bww, bhh = (x + at, y, bw, h_) if along_x else (x, y + at, w, bw)
        X0, Y0 = P(bx, by); X1, Y1 = P(bx + bww, by + bhh)
        roof = q.get('roof')
        if tile:                                                         # v56's old harbour quarter: mixed tile, pitched, house by house
            hq = (int(bx) * 2654435761 ^ int(by) * 40503) & 0xffff
            base = tile[hq % len(tile)]; roof = 'tile'
        else:
            base = ROOF_RGB.get(roof, (150, 140, 130))
        lt, md, sh = tones(base)
        d.rectangle([X0, Y0, X1, Y1], fill=sh)
        if roof == 'flat':
            d.rectangle([X0, Y0, X1, Y0 + (Y1 - Y0) * 0.5], fill=md)
            if X1 - X0 > 5 and Y1 - Y0 > 5:                              # roof clutter: a tank, a vent
                cx_, cy_ = X0 + (X1 - X0) * (0.3 + 0.4 * (i % 2)), Y0 + (Y1 - Y0) * 0.55
                d.rectangle([cx_ - 1.2 * kk, cy_ - 1.2 * kk, cx_ + 1.2 * kk, cy_ + 1.2 * kk], fill=lt, outline=ink + (160,))
        elif along_x:
            d.rectangle([X0, Y0, X1, (Y0 + Y1) / 2], fill=lt)                # the ridge along the street, the front slope lit
            if roof == 'tin' and X1 - X0 > 4:
                for j in range(1, max(2, int((X1 - X0) // max(2, 2 * kk)))):
                    xx = X0 + j * 2 * kk; d.line([(xx, Y0), (xx, Y1)], fill=sh + (160,), width=1)
        else:
            d.rectangle([X0, Y0, (X0 + X1) / 2, Y1], fill=lt)
            if roof == 'tin' and Y1 - Y0 > 4:
                for j in range(1, max(2, int((Y1 - Y0) // max(2, 2 * kk)))):
                    yy = Y0 + j * 2 * kk; d.line([(X0, yy), (X1, yy)], fill=sh + (160,), width=1)
        if i:
            if along_x:
                d.line([(X0, Y0), (X0, Y1)], fill=ink + (200,), width=1)
            else:
                d.line([(X0, Y0), (X1, Y0)], fill=ink + (200,), width=1)
        at += bw
    X0, Y0 = P(x, y); X1, Y1 = P(x + w, y + h_)
    if X1 - X0 > 3.5:
        d.rectangle([X0, Y0, X1, Y1], outline=ink + (170,), width=1)


OLD_JP = {'machiya', 'machiya_row', 'honjin', 'temple_hall', 'pagoda', 'watchkeep', 'minka_thatched', 'kura', 'bathhouse'}
VERMILION = (198, 62, 44)


def draw_old_jp(d, ink, P, x, y, w, h_, form, k, kk, door, storeys=2):
    """Highgarth's old post town at map scale: dark tiled roofs with a white plaster line along the eave, the thatched farmhouses
    straw and steep, the storehouses white-walled, the temple hall's hipped roof, the pagoda as its own mark (stacked roofs, vermilion
    trim) and the watch keep black on its grey stone base, snow on its roof."""
    X0, Y0 = P(x, y); X1, Y1 = P(x + w, y + h_)
    off = max(1.0, (0.6 + 0.4 * storeys) * kk)
    dark, darkl, white, straw = (52, 50, 54), (84, 84, 92), (236, 232, 222), (196, 168, 104)
    snowy = y < 1100 and form in ('minka_thatched', 'watchkeep') and 600 < y and 7600 < x < 8400   # Highgarth's upper terraces under snow
    if form == 'watchkeep':
        B0, B1 = P(x - 8, y - 8), P(x + w + 8, y + h_ + 8)
        d.polygon([(B0[0] - 2 * kk, B1[1]), (B0[0], B0[1]), (B1[0], B0[1]), (B1[0] + 2 * kk, B1[1])], fill=(128, 124, 118), outline=ink)
    d.rectangle([X0 + off, Y0 + off, X1 + off, Y1 + off], fill=ink + (80,))
    if form == 'pagoda':
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2; r_ = max(2.5, (X1 - X0) / 2)
        for i in range(5):                                              # five stacked roofs, each smaller, vermilion trim
            q = r_ * (1 - i * 0.17)
            d.rectangle([cx - q, cy - q, cx + q, cy + q], fill=dark if i % 2 == 0 else darkl, outline=VERMILION)
        d.line([(cx, cy - r_ * 1.25), (cx, cy - r_ * 0.2)], fill=(200, 170, 80), width=max(1, int(kk)))
        return
    if form == 'minka_thatched':                                       # a steep hipped thatch: four slopes to a short ridge
        d.rectangle([X0, Y0, X1, Y1], fill=tuple(int(v * 0.68) for v in straw))
        mx = min(X1 - X0, Y1 - Y0) / 2
        d.polygon([(X0, Y0), (X1, Y0), (X1 - mx, (Y0 + Y1) / 2), (X0 + mx, (Y0 + Y1) / 2)], fill=straw)
        d.polygon([(X0, Y0), (X0 + mx, (Y0 + Y1) / 2), (X0, Y1)], fill=tuple(int(v * 0.85) for v in straw))
        d.line([(X0 + mx, (Y0 + Y1) / 2), (X1 - mx, (Y0 + Y1) / 2)], fill=(120, 96, 52), width=max(1, int(kk)))
        if snowy:
            d.polygon([(X0, Y0), (X1, Y0), (X1 - mx * 0.6, Y0 + (Y1 - Y0) * 0.3), (X0 + mx * 0.6, Y0 + (Y1 - Y0) * 0.3)], fill=(246, 248, 252))
        d.rectangle([X0, Y0, X1, Y1], outline=ink + (180,))
        return
    if form == 'kura':
        d.rectangle([X0, Y0, X1, Y1], fill=white, outline=ink)
        d.rectangle([X0, Y0, X1, Y0 + (Y1 - Y0) * 0.45], fill=dark)
        return
    d.rectangle([X0, Y0, X1, Y1], fill=dark)
    if form in ('temple_hall', 'watchkeep'):                            # a hipped roof: the hips to a short ridge
        mx = (Y1 - Y0) / 2
        d.polygon([(X0, Y0), (X1, Y0), (X1 - mx, (Y0 + Y1) / 2), (X0 + mx, (Y0 + Y1) / 2)], fill=darkl)
        d.line([(X0, Y0), (X0 + mx, (Y0 + Y1) / 2), (X1 - mx, (Y0 + Y1) / 2), (X1, Y0)], fill=ink, width=1)
        d.line([(X0, Y1), (X0 + mx, (Y0 + Y1) / 2)], fill=ink, width=1); d.line([(X1, Y1), (X1 - mx, (Y0 + Y1) / 2)], fill=ink, width=1)
        if form == 'watchkeep':
            d.rectangle([X0, Y0, X1, Y0 + (Y1 - Y0) * 0.3], fill=(244, 246, 250))   # snow on its roof
        d.rectangle([X0, Y0, X1, Y1], outline=white, width=max(1, int(round(1.2 * kk))))
        return
    # machiya, honjin, bathhouse: the ridge along the street, the front slope lit, a white plaster line under the eave
    if (X1 - X0) >= (Y1 - Y0):
        d.rectangle([X0, Y0, X1, (Y0 + Y1) / 2], fill=darkl)
    else:
        d.rectangle([X0, Y0, (X0 + X1) / 2, Y1], fill=darkl)
    if door:
        dx, dy = door; fx, fy = P(dx * CELL + 4, dy * CELL + 4); t_ = max(1.0, 2.5 * k)
        if fy >= Y1 - 0.5:
            d.line([(X0, Y1 - t_), (X1, Y1 - t_)], fill=white, width=max(1, int(round(t_))))
        elif fy <= Y0 + 0.5:
            d.line([(X0, Y0 + t_), (X1, Y0 + t_)], fill=white, width=max(1, int(round(t_))))
        elif fx <= X0 + 0.5:
            d.line([(X0 + t_, Y0), (X0 + t_, Y1)], fill=white, width=max(1, int(round(t_))))
        else:
            d.line([(X1 - t_, Y0), (X1 - t_, Y1)], fill=white, width=max(1, int(round(t_))))
    d.rectangle([X0, Y0, X1, Y1], outline=ink + (200,))


def draw_forest(d, S, R, ink, P, k, s):
    """The old forest's places: the Elder Oak (a colossal crown) and its standing stones, the moon observatory's ruin, the log
    flume and the rail spur of the Company's camp, the boardwalk into the fens and the reed hide."""
    F = S.get('forest')
    if not F:
        return
    fe, pl_ = F['features'], F['places']
    w1 = max(1, int(round(1.4 * s)))
    polyline(d, fe['log_flume_px'], P, R['timber'][2] + (230,), 2.4 * s)
    polyline(d, fe['log_flume_px'], P, R['timber'][4] + (230,), 1.0 * s)
    polyline(d, fe['rail_spur_px'], P, ink + (235,), 2.4 * s)
    polyline(d, fe['rail_spur_px'], P, R['plaster'][5] + (220,), 1.0 * s, dash=(3 * s, 3 * s))
    polyline(d, fe['boardwalk_px'], P, R['timber'][3] + (240,), 2.6 * s)
    polyline(d, fe['boardwalk_px'], P, R['timber'][1] + (200,), 0.8 * s, dash=(2 * s, 2 * s))
    hx, hy = P(*fe['reed_hide_px']); r_ = max(1.5, 4 * k)
    d.rectangle([hx - r_, hy - r_, hx + r_, hy + r_], fill=R['timber'][2], outline=ink)
    for (x, y) in fe['standing_stones_px']:
        X, Y = P(x, y); r_ = max(1.0, 3.5 * k)
        d.ellipse([X - r_, Y - r_ * 1.3, X + r_, Y + r_ * 1.3], fill=R['stone'][4], outline=ink + (200,))
    ox, oy = pl_['the Elder Oak']['xy_px']; X, Y = P(ox, oy); r_ = max(4.0, 40 * k)
    d.ellipse([X - r_ + 2 * k * 10, Y - r_ + 2 * k * 10, X + r_ + 2 * k * 10, Y + r_ + 2 * k * 10], fill=ink + (90,))
    d.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(46, 92, 52), outline=ink)
    d.ellipse([X - r_ * 0.85, Y - r_ * 0.85, X + r_ * 0.2, Y + r_ * 0.2], fill=(84, 140, 76))
    d.ellipse([X - r_ * 0.12, Y - r_ * 0.12, X + r_ * 0.12, Y + r_ * 0.12], fill=(110, 80, 50))
    bx, by = pl_["the moon-watchers' observatory"]['xy_px']; X, Y = P(bx, by); r_ = max(3.0, 26 * k)
    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
        if 0.6 < a < 1.6:
            continue                                                   # the fallen part of the ring
        sx_, sy_ = X + r_ * math.cos(a), Y + r_ * 0.8 * math.sin(a); q = max(1.0, 3 * k)
        d.rectangle([sx_ - q, sy_ - q, sx_ + q, sy_ + q], fill=R['stone'][3], outline=ink + (200,))
    d.arc([X - r_ * 0.55, Y - r_ * 0.55, X + r_ * 0.55, Y + r_ * 0.55], 180, 330, fill=R['stone'][4], width=max(1, int(round(3 * k))))


def draw_city_features(d, S, R, ink, P, k, s, plans=None):
    """Neon Harbour's vertical links: sky bridges between towers (a pale deck with a cyan edge), the funicular up the Heights
    (a dark track with a car at each station), the lighthouse's beam arc at the harbour mouth."""
    for P_ in (plans or (S.get('plans') or {}).values()):
        fe = P_.get('features') or {}
        for sb in fe.get('sky_bridges', []):
            (ax, ay), (bx, by) = sb['px']
            X0, Y0 = P(ax, ay); X1, Y1 = P(bx, by)
            wd = max(2, int(round(10 * k)))
            d.line([(X0, Y0), (X1, Y1)], fill=(214, 220, 232, 255), width=wd)
            d.line([(X0, Y0), (X1, Y1)], fill=(80, 230, 255, 220), width=max(1, wd // 4))
        fu = fe.get('funicular')
        if fu:
            pts = [P(x, y) for x, y in fu['px']]
            d.line(pts, fill=(60, 52, 60, 255), width=max(2, int(round(6 * k))))
            for i in range(1, 12):
                X = pts[0][0] + (pts[1][0] - pts[0][0]) * i / 12; Y = pts[0][1] + (pts[1][1] - pts[0][1]) * i / 12
                r_ = max(1.0, 4 * k); d.line([(X - r_, Y - r_), (X + r_, Y + r_)], fill=(150, 140, 150, 255), width=1)
            for X, Y in pts:
                r_ = max(2.0, 7 * k); d.rectangle([X - r_, Y - r_, X + r_, Y + r_], fill=(230, 80, 90, 255), outline=ink + (255,))
        hb = fe.get('harbour')
        if hb and hb.get('lighthouse'):
            X, Y = P(*hb['lighthouse']); r_ = max(4.0, 90 * k)
            d.pieslice([X - r_, Y - r_, X + r_, Y + r_], 200, 250, fill=(255, 244, 170, 60))
        BOAT = {'ferry': ((236, 236, 230), (200, 60, 60)), 'boat': ((230, 226, 214), (90, 120, 160)), 'barge': ((92, 70, 52), (150, 120, 80)),
                'sampan': ((176, 140, 92), (220, 90, 70)), 'pilot boat': ((240, 200, 60), (40, 40, 40))}
        for bt in (hb or {}).get('boats', []):                          # the busy water: moored boats, ferries, barges, sampans
            x, y = bt['xy_px']; L = bt['len_px']; Wd = max(6, L // 3)
            hw_, hh_ = (L / 2, Wd / 2) if bt['along'] == 'x' else (Wd / 2, L / 2)
            X0, Y0 = P(x - hw_, y - hh_); X1, Y1 = P(x + hw_, y + hh_)
            hull, deck = BOAT.get(bt['kind'], BOAT['boat'])
            if X1 - X0 < 3 or Y1 - Y0 < 3:
                d.rectangle([X0, Y0, max(X0, X1), max(Y0, Y1)], fill=hull + (255,))
                continue
            d.rounded_rectangle([X0, Y0, X1, Y1], radius=max(1, int(min(X1 - X0, Y1 - Y0) / 2) - 1), fill=hull + (255,), outline=ink + (200,))
            if X1 - X0 > 6 and Y1 - Y0 > 3:
                mx, my = (X0 + X1) / 2, (Y0 + Y1) / 2
                d.rectangle([mx - (X1 - X0) * 0.18, my - (Y1 - Y0) * 0.22, mx + (X1 - X0) * 0.18, my + (Y1 - Y0) * 0.22], fill=deck + (255,))
        ml = fe.get('maglev')
        if ml and len(ml.get('px', [])) >= 2:                          # the elevated maglev: a dark viaduct, a cyan rail, its pylons
            pts = [P(x, y) for x, y in ml['px']]
            d.line(pts, fill=(54, 50, 62, 255), width=max(3, int(round(12 * k))))
            d.line(pts, fill=(80, 230, 255, 255), width=max(1, int(round(3 * k))))
            (ax, ay), (bx, by) = ml['px'][0], ml['px'][-1]; L = math.hypot(bx - ax, by - ay)
            for i in range(0, int(L // 64) + 1):
                X, Y = P(ax + (bx - ax) * i * 64 / max(L, 1), ay + (by - ay) * i * 64 / max(L, 1)); r_ = max(1.5, 5 * k)
                d.rectangle([X - r_, Y - r_, X + r_, Y + r_], fill=(110, 104, 120, 255))
        for lf in fe.get('lifts', []):                                  # public lifts between the terrace levels
            X, Y = P(*lf['xy_px']); r_ = max(2.0, 7 * k)
            d.rectangle([X - r_, Y - r_, X + r_, Y + r_], fill=(250, 210, 80, 255), outline=ink + (255,))
            d.line([(X, Y - r_ * 0.7), (X, Y + r_ * 0.7)], fill=ink + (255,), width=1)
        for b in P_.get('buildings', []):                               # verticality: a long shadow by floor count (light from the
            v = b.get('vertical')                                       # upper left), and a mark on the towers one can go up
            if not v:
                continue
            x, y, w, h_ = b['rect_px']; L = min(80, v['floors'] * 1.6)
            if L >= 8:
                for (sx0, sy0, sx1, sy1) in ((x + w, y + L * 0.5, x + w + L, y + h_ + L), (x + L * 0.5, y + h_, x + w + L, y + h_ + L)):
                    X0, Y0 = P(sx0, sy0); X1, Y1 = P(sx1, sy1)
                    d.rectangle([X0, Y0, X1, Y1], fill=(20, 18, 34, min(110, 30 + int(v['floors'] * 2))))
            if v.get('way_up') and k > 0.3:
                X, Y = P(x + 10, y + 10); r_ = max(3.0, 6 * k)
                d.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(250, 250, 250, 255), outline=ink + (255,))
                d.polygon([(X, Y - r_ * 0.6), (X - r_ * 0.5, Y + r_ * 0.4), (X + r_ * 0.5, Y + r_ * 0.4)], fill=ink + (255,))


def draw_shrines(d, S, R, ink, P, k, s, plans=None):
    """A shrine path drawn as a stone stair (a light line with step ticks) and its repeated timber gates with vermilion
    lintels; a footbridge where a plan has one."""
    for P_ in (plans or (S.get('plans') or {}).values()):
        fe = P_.get('features') or {}
        pts = fe.get('shrine_path_px')
        if pts:
            polyline(d, pts, P, R['stone'][4] + (255,), max(2.0, 14 * k))
            polyline(d, pts, P, ink + (150,), max(1.0, 1.0 * s))
            (ax, ay), (bx, by) = pts[0], pts[-1]
            L = math.hypot(bx - ax, by - ay); n = int(L // 12)
            for i in range(1, n):
                x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n; X, Y = P(x, y); r_ = max(1.0, 7 * k)
                d.line([(X - r_, Y), (X + r_, Y)], fill=ink + (110,), width=1)
        for (gx, gy) in fe.get('shrine_gates_px', []):
            X, Y = P(gx, gy); r_ = max(2.0, 10 * k)
            d.line([(X - r_ * 0.6, Y - r_ * 0.5), (X - r_ * 0.6, Y + r_ * 0.6)], fill=(110, 72, 40), width=max(1, int(round(2.5 * k + 0.5))))
            d.line([(X + r_ * 0.6, Y - r_ * 0.5), (X + r_ * 0.6, Y + r_ * 0.6)], fill=(110, 72, 40), width=max(1, int(round(2.5 * k + 0.5))))
            d.line([(X - r_, Y - r_ * 0.55), (X + r_, Y - r_ * 0.55)], fill=VERMILION + (255,), width=max(1, int(round(3 * k + 0.5))))
        fb = fe.get('footbridge')
        if fb:
            x, y = fb['xy_px']; X0, Y0 = P(x - 48, y - 8); X1, Y1 = P(x + 48, y + 8)
            d.rectangle([X0, Y0, X1, Y1], fill=R['timber'][4], outline=R['timber'][1], width=max(1, int(round(1.5 * k + 0.5))))


def draw_kerbs(d, S, R, P, k, plans=None):
    """Painted kerb lines along both edges of the streets with a continuous frontage."""
    for P_ in (plans or (S.get('plans') or {}).values()):
        for st in P_['streets']:
            if st.get('frontage') != 'continuous':
                continue
            hw = st['width_cells'] * CELL / 2 - 1.5
            v = st['vertices_px']
            for (ax, ay), (bx, by) in zip(v, v[1:]):
                L = math.hypot(bx - ax, by - ay)
                if L < 8:
                    continue
                nx, ny = -(by - ay) / L, (bx - ax) / L
                for sg in (1, -1):
                    d.line([P(ax + nx * hw * sg, ay + ny * hw * sg), P(bx + nx * hw * sg, by + ny * hw * sg)], fill=R['plaster'][5] + (200,), width=max(1, int(round(1.2 * k))))


FLAT = {'office', 'tower', 'hangar', 'warehouse', 'station', 'keep', 'hall'}


def draw_farmsteads56(d, S, steads, R, ink, P, s, k):
    """Farmsteads as small clusters (a house, a barn, a shed round a yard) with a lane to the nearest road when one is near
    and no river is in the way."""
    rivers = [p for nm, p in S['river_px'].items() if nm not in ('the Dry Fork', 'Brackens wash')]
    routes = [p for nm, p in S['route_px'].items() if S['routes'][nm][0] in ('road', 'path', 'bridge')]
    for i, (x0, y0, x1, y1) in enumerate(steads):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        for pts in routes:
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1
                t = max(0, min(1, ((cx - ax) * (bx - ax) + (cy - ay) * (by - ay)) / L2))
                qx, qy = ax + t * (bx - ax), ay + t * (by - ay); dd = math.hypot(qx - cx, qy - cy)
                if best is None or dd < best[0]:
                    best = (dd, qx, qy)
        if best and best[0] < 520 and not any(_crossings([(cx, cy), (best[1], best[2])], rp) for rp in rivers):
            lane = [(cx, cy), (cx, best[2]), (best[1], best[2])] if i % 2 else [(cx, cy), (best[1], cy), (best[1], best[2])]
            polyline(d, lane, P, R['path'][1] + (170,), 2.0 * s); polyline(d, lane, P, R['path'][4], 1.1 * s)
        w, h_ = x1 - x0, y1 - y0
        parts = [(x0 + w * 0.08, y0 + h_ * 0.1, w * 0.42, h_ * 0.3, R['clay'][3]),       # the house
                 (x0 + w * 0.45, y0 + h_ * 0.5, w * 0.5, h_ * 0.38, R['timber'][3]),     # the barn
                 (x0 + w * 0.1, y0 + h_ * 0.62, w * 0.24, h_ * 0.22, R['slate'][3])]     # the shed
        for bx, by, bw, bh, c in parts:
            X0, Y0 = P(bx, by); X1, Y1 = P(bx + bw, by + bh)
            lt, md, sh = tones(c)
            o = max(1.0, 0.8 * s)
            d.rectangle([X0 + o, Y0 + o, X1 + o, Y1 + o], fill=ink + (70,))
            d.rectangle([X0, Y0, X1, Y1], fill=sh)
            d.rectangle([X0, Y0, (X0 + X1) / 2, Y1], fill=lt)
            if X1 - X0 > 3:
                d.rectangle([X0, Y0, X1, Y1], outline=ink + (150,), width=1)


def draw_trees56(d, pts, R, ink, P, k):
    """Lone trees, small stands and hedgerow trees: a round crown lit on its upper left, a shadow to the south-east."""
    r = max(1.1, 13 * k)
    lt, md, sh = tones(R['leaf'][3])
    for i, (x, y) in enumerate(sorted(pts, key=lambda p: p[1])):
        X, Y = P(x, y); rr = r * (0.85 + 0.3 * ((i * 37) % 10) / 10)
        d.ellipse([X - rr + 0.5 * rr, Y - rr + 0.6 * rr, X + rr + 0.5 * rr, Y + rr + 0.6 * rr], fill=ink + (60,))
        d.ellipse([X - rr, Y - rr, X + rr, Y + rr], fill=md, outline=ink + (110,) if rr > 2.5 else None)
        if rr > 1.6:
            d.pieslice([X - rr * 0.9, Y - rr * 0.9, X + rr * 0.55, Y + rr * 0.55], 150, 330, fill=lt)


COMPANY = 'Neon Harbour: the Company district'
COMPANY_BOX = (11600, 4150, 12470, 5180)


def company_floors(S):
    P_ = (S.get('plans') or {}).get('neon-harbour') or {}
    dt = {d_['id']: d_.get('town', '') for d_ in P_.get('districts', [])}
    return {tuple(b['rect_px']): (b.get('vertical') or {}).get('floors', 4) for b in P_.get('buildings', []) if dt.get(b['district']) == COMPANY}


def draw_company56(d, S, R, ink, P, s, k):
    """The Company district from above, before its roofs: the plan's open spaces (the park, the squares, the yards) as
    lighter breaks, street trees along its avenues and the spine, and every block's shadow cast to the south-east by its
    height (18-floor slabs short, 28 to 32-floor towers long), so the roofs stand at their heights."""
    P_ = (S.get('plans') or {}).get('neon-harbour')
    if not P_:
        return
    bx0, by0, bx1, by1 = COMPANY_BOX
    inb = lambda x, y: bx0 <= x <= bx1 and by0 <= y <= by1
    for dd in P_['districts']:                                       # the Company park
        if dd['id'].endswith('company-park') and dd.get('box_px'):
            x0, y0, x1, y1 = dd['box_px']; A = P(x0, y0); B = P(x1, y1)
            d.rectangle([A[0], A[1], B[0], B[1]], fill=R['grass'][3])
            for i in range(int((x1 - x0) // 36)):
                draw_trees56(d, [(x0 + 18 + 36 * i, y0 + 16 + (i % 2) * 22)], R, ink, P, k * 0.7)
    for sq in P_.get('squares', []) + P_.get('open_uses', []):
        c = sq.get('cells')
        if not c or len(c) != 4:
            continue
        x, y, w, h_ = c[0] * CELL, c[1] * CELL, c[2] * CELL, c[3] * CELL
        if not inb(x + w / 2, y + h_ / 2):
            continue
        A = P(x, y); B = P(x + w, y + h_)
        green = sq.get('type') == 'green' or 'garden' in (sq.get('name') or '')
        d.rectangle([A[0], A[1], B[0], B[1]], fill=(R['grass'][3] if green else R['concrete'][5]) + (235,))
    for st in P_['streets']:                                         # street trees on the avenues and the spine
        if st['class'] not in ('main', 'side'):
            continue
        v = st['vertices_px']
        if not all(inb(x, y) for x, y in v):
            continue
        hw = st['width_cells'] * CELL / 2 - 3
        for (ax, ay), (bx, by) in zip(v, v[1:]):
            L = math.hypot(bx - ax, by - ay)
            if L < 40:
                continue
            ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy, ux
            pts = [(ax + ux * t_ + nx * sg * hw, ay + uy * t_ + ny * sg * hw) for t_ in np.arange(20, L - 10, 44) for sg in (-1, 1)]
            draw_trees56(d, pts, R, ink, P, k * 0.55)
    fl = company_floors(S)                                           # shadows by height, longest first
    for (x, y, w, h_), f in sorted(fl.items(), key=lambda kv: -kv[1]):
        Ls = 2.2 * f
        corners = [(x + w, y), (x + w, y + h_), (x, y + h_)]
        poly = [P(*corners[0]), P(corners[0][0] + Ls, corners[0][1] + Ls * 0.8), P(corners[1][0] + Ls, corners[1][1] + Ls * 0.8),
                P(corners[2][0] + Ls, corners[2][1] + Ls * 0.8), P(*corners[2]), P(*corners[1])]
        d.polygon(poly, fill=ink + (95 if f >= 28 else 70,))


def company_roof(R, f, x, y):
    """Roof colour by height: towers pale steel, slabs a mid slate; the two landmark slabs (the bank, the Company's head
    office) in verdigris copper."""
    if (x, y) == (11744, 4608):
        return R['copper'][3]
    if (x, y) == (12048, 4280):
        return R['copper_cool'][4] if 'copper_cool' in R else R['brass'][3]
    return R['concrete'][4] if f >= 28 else (R['slate'][3] if f >= 18 else R['iron'][3])


def roof_details56(d, R, ink, X0, Y0, X1, Y1, x, y, kk):
    """A flat city roof seen from above: rooftop plant, a light well, a planted roof terrace, a helipad on the tallest, now
    and then a neon roof sign; chosen per building so no two neighbours repeat."""
    w, h_ = X1 - X0, Y1 - Y0
    if w < 4 or h_ < 4:
        return
    hsh = (int(x) * 73856093 ^ int(y) * 19349663) & 0xffff
    u = max(1.0, kk)
    kind = hsh % 4
    if kind == 0 and w > 8 and h_ > 8:                               # a light well: a dark shaft with a lit north rim
        a0, b0, a1, b1 = X0 + w * 0.36, Y0 + h_ * 0.38, X0 + w * 0.64, Y0 + h_ * 0.66
        d.rectangle([a0, b0, a1, b1], fill=R['iron'][0]); d.line([(a0, b0), (a1, b0)], fill=R['concrete'][5], width=max(1, int(u)))
    elif kind == 1:                                                  # a roof terrace, planted
        d.rectangle([X0 + u, Y1 - max(2 * u, h_ * 0.3), X0 + w * 0.6, Y1 - u], fill=R['leaf'][3], outline=R['leaf'][1])
        d.point([(X0 + w * 0.2, Y1 - h_ * 0.15), (X0 + w * 0.42, Y1 - h_ * 0.2)], fill=R['leaf'][5])
    elif kind == 2 and w > 10 and h_ > 10:                           # a helipad
        cx_, cy_ = X0 + w * 0.62, Y0 + h_ * 0.55; r_ = min(w, h_) * 0.18
        d.ellipse([cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_], fill=R['iron'][2], outline=R['brass'][5])
    for j in range(1 + (hsh >> 3) % 2):                               # rooftop plant: units with a lit top
        px_ = X0 + w * (0.12 + 0.3 * j + 0.1 * ((hsh >> 5) % 3)); py_ = Y0 + h_ * 0.16
        d.rectangle([px_, py_, px_ + 2.4 * u, py_ + 1.8 * u], fill=R['iron'][2], outline=ink + (160,))
        d.line([(px_, py_), (px_ + 2.4 * u, py_)], fill=R['iron'][5], width=1)
    if hsh % 5 == 2 and w > 6:                                       # a neon roof sign
        d.line([(X0 + w * 0.2, Y0 + 1), (X0 + w * 0.6, Y0 + 1)], fill=(64, 232, 240) if hsh % 2 else (236, 72, 196), width=max(1, int(u)))


_CF = {}
OLD_QUARTER = {'Neon Harbour: the old waterfront', 'Neon Harbour: Canalside, the canal quarter', 'Neon Harbour: the Crescent'}


def draw_towns(d, S, R, ink, P, s, k, neon_lights=True, roofs=False):
    """Every building as a small roof, drawn by its form: a shadow to the south-east, a ridge roof lit on its west slope (an
    apartment row or a terrace split into its houses), flat roofs with a lit parapet (warehouses with roof lights, slabs and towers
    with a core, adobes pale and flat), and a tall board front on the street side of a frontier shop, saloon or depot."""
    kk = s
    for (town, x, y, w, h_, use, form, door, bays) in plan_buildings(S):
        X0, Y0 = P(x, y); X1, Y1 = P(x + w, y + h_)
        if X1 - X0 < 1.0:
            d.rectangle([X0, Y0, X0 + 1, Y0 + 1], fill=roof_colour(R, town, use))
            continue
        if form in OLD_JP:
            if bays:                                                   # a block of machiya: each front its own dark roof and white eave line
                along_x = abs(sum(q['w_cells'] for q in bays) * CELL - w) <= abs(sum(q['w_cells'] for q in bays) * CELL - h_)
                at = 0
                for q in bays:
                    bw = q['w_cells'] * CELL
                    bx, by, bww, bhh = (x + at, y, bw, h_) if along_x else (x, y + at, w, bw)
                    draw_old_jp(d, ink, P, bx, by, bww, bhh, 'machiya', k, kk, door, storeys=q.get('storeys', 2))
                    at += bw
            else:
                draw_old_jp(d, ink, P, x, y, w, h_, form, k, kk, door)
            continue
        if bays and X1 - X0 >= 2.5:
            tile = None
            if roofs and town in OLD_QUARTER:
                tile = (R['clay'][3], R['clay_warm'][2], R['timber'][3], R['clay'][2], R['slate'][3], R['clay_cool'][3], R['clay_warm'][3])
            draw_bays(d, ink, P, x, y, w, h_, bays, k, kk, tile=tile)
            if any(q.get('false_front') for q in bays) and door:
                dx, dy = door; fx, fy = P(dx * CELL + 4, dy * CELL + 4); t_ = max(1.0, 6 * k); front = R['plaster'][4]
                if fy >= Y1 - 0.5:
                    d.rectangle([X0, Y1 - t_, X1, Y1], fill=front, outline=ink + (200,))
                elif fy <= Y0 + 0.5:
                    d.rectangle([X0, Y0, X1, Y0 + t_], fill=front, outline=ink + (200,))
            continue
        if form in OLD_JP:
            draw_old_jp(d, ink, P, x, y, w, h_, form, k, kk, door)
            continue
        c = roof_colour(R, town, use)
        if roofs and town in OLD_QUARTER:                              # v56: the harbour quarter older than the Company, in mixed tile
            hq = (int(x) * 2654435761 ^ int(y) * 40503) & 0xffff
            c = (R['clay'][3], R['clay_warm'][2], R['timber'][3], R['clay'][2], R['slate'][3], R['clay_cool'][3])[hq % 6]
        cfl = None
        if roofs and town == COMPANY:
            cfl = _CF.get(id(S))
            if cfl is None:
                cfl = _CF[id(S)] = company_floors(S)
            f_ = cfl.get((x, y, w, h_))
            if f_ is not None:
                c = company_roof(R, f_, x, y)
        lt, md, sh = tones(c)
        if form == 'adobe':
            lt, md, sh = tones(R['sand_warm'][3] if 'sand_warm' in R else c)
        off = max(1.0, 0.9 * kk)
        if not (cfl and (x, y, w, h_) in cfl):                         # the Company's shadows are cast by height (draw_company56)
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
        if roofs and town.startswith('Neon Harbour') and (use in FLAT or form in ('slab', 'bigtower', 'tower')) and form not in ('longwarehouse',):
            roof_details56(d, R, ink, X0, Y0, X1, Y1, x, y, kk)
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
    biome = [(t, 7860, 1880) if t == 'the coal hills' else (t, x, y) for t, x, y in biome]   # on the hills, off the old forest
    biome += [('the upper Cog', 8200, 1500), ('the east coast', 12440, 4720)]
    if getattr(M, 'REVISION', 'v55') == 'v56':                         # off the old crossing's line, onto the gorge's east wall
        biome = [(t, x + 120, y - 150) if t == 'the Narrows' else (t, x, y) for t, x, y in biome]
        region = [(t, 1300, 4930) if t == 'THE FIRE COUNTRY' else (t, x, y) for t, x, y in region]   # clear of the west haze
    small = [(nm, *Pr((x, y)), kind) for nm, x, y, kind in M54.SMALL_PLACES if nm not in ('the old town', 'the docks', 'new town', 'the Skyport', 'Gull Strand')]
    small += [('the rockfall', M.ROCKFALL[0] + 40, M.ROCKFALL[1], 'gate'), ('the slate quarry', 8256, 1192, 'place'), ('the folds', 7915, 900, 'place'),
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
    if getattr(M, 'REVISION', 'v55') == 'v56':
        settle.pop('Canalside', None); settle.pop('Glintside', None)    # districts of Neon Harbour in v56 (Matt, 2 Nov)
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
    for nm, q in ((S.get('forest') or {}).get('places') or {}).items():  # the old forest's places
        if full or q['tier'] <= 2:
            icons.append((nm, q['xy_px'][0], q['xy_px'][1], 'place', 'village' if not full else 'place', 2 if not full else 3))
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
        if getattr(M, 'REVISION', 'v55') == 'v56':                   # v56: a full ink halo, so the quiet names hold on dark forest at 1920
            qfill = R['snow'][5]; qst = ink
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
    if getattr(M, 'REVISION', 'v55') == 'v56':
        paper = R['plaster'][5] + (236,)
        x0 = lb[0] + 12 * s
        yy = lb[1] + 174 * s                                       # the ferry row: white dashes on water, as drawn
        d.rectangle([x0 - 1 * s, yy - 4 * s, x0 + 17 * s, yy + 4 * s], fill=paper)
        d.rectangle([x0, yy - 3 * s, x0 + 16 * s, yy + 3 * s], fill=R['water_warm'][3])
        for q in range(1, 16, 6):
            d.line([(x0 + q * s, yy), (x0 + (q + 3) * s, yy)], fill=R['snow'][5], width=max(1, int(1.6 * s)))
        d.rectangle([bx - 3 * s, lb[1] + 53 * s, bx + 11 * s, lb[1] + 61 * s], fill=paper)          # the closed pass, as drawn
        for q in (0, 5):
            d.line([(bx - 2 * s + q * s, lb[1] + 57 * s), (bx + 1 * s + q * s, lb[1] + 57 * s)], fill=R['timber'][2], width=max(1, int(1.4 * s)))
        for i in range(2):
            d.rectangle([bx + 6 * s + i * 2 * s, lb[1] + 55.6 * s, bx + 8 * s + i * 2 * s, lb[1] + 58.4 * s], fill=(R['berry'][4] if i == 0 else R['plaster'][5]), outline=ink)
        y_ = lb[1] + 73 * s                                        # the shard lines
        d.line([(bx - 2 * s, y_), (bx + 10 * s, y_)], fill=R['plaster'][5], width=max(1, int(3 * s)))
        for q in (0, 6):
            d.line([(bx - 2 * s + q * s, y_), (bx + 2 * s + q * s, y_)], fill=R['dusk'][2], width=max(1, int(1.6 * s)))
        d.text((bx + 12 * s, y_), 'shard line', font=F['small'], fill=ink, anchor='lm')
        y_ = lb[1] + 110 * s                                       # the built area
        d.rectangle([bx - 2 * s, y_ - 3.5 * s, bx + 10 * s, y_ + 3.5 * s], outline=R['brass'][5], width=max(1, int(1.4 * s)))
        d.text((bx + 12 * s, y_), 'built now', font=F['small'], fill=ink, anchor='lm')
        y_ = lb[1] + 126 * s                                       # the edges
        for i, a in enumerate((60, 120, 190, 235)):
            d.rectangle([bx - 2 * s + i * 3 * s, y_ - 3.5 * s, bx + 1 * s + i * 3 * s, y_ + 3.5 * s], fill=R['snow'][4] + (a,))
        d.rectangle([bx - 2 * s, y_ - 3.5 * s, bx + 10 * s, y_ + 3.5 * s], outline=R['timber'][2], width=1)
        d.text((bx + 12 * s, y_), 'past the world', font=F['small'], fill=ink, anchor='lm')
    rb = panel_boxes(Wc, Hc, s)[1]
    if getattr(M, 'REVISION', 'v55') == 'v56':
        import grow56 as GR
        txt = f"v56 world {g.WPX} x {g.HPX} px, drawn to {g.WPX + GR.EX} x {g.HPX + GR.DY} (the edges past it)"
    else:
        txt = f"{getattr(M, 'REVISION', 'v55')} canvas {g.WPX} x {g.HPX} world px (v54: 11264 x 6912)"
    d.text((rb[2] - 10 * s, rb[1] + 12 * s), txt, font=F['small'], fill=R['timber'][2], anchor='rt')


# ------------------------------------------------------------------------------------------ compose
def frame_fit(Wc, Hc, s):
    k = Hc / g.HPX
    if g.WPX * k > Wc - 20 * s:
        k = (Wc - 20 * s) / g.WPX
    ox = (Wc - g.WPX * k) / 2; oy = (Hc - g.HPX * k) / 2
    return k, ox, oy


def compose(S, M, R, ink, s, base, k, ox, oy, Wc, Hc, paths, lines, mode, title, panels_on=True, box=None, act=True, grow=None):
    F = M54.fonts54(M.ROOT, s)
    F['quiet'] = ImageFont.truetype(os.path.join(M.ROOT, 'game', 'ui', 'fonts', 'PixelifySans-Regular.ttf'), int(round(13 * s)))
    canvas = Image.new('RGB', (Wc, Hc), R['snow'][3])
    px0, py0 = (0, 0) if box is not None else (int(round(ox)), int(round(oy)))     # an inset's base is already cut to its box
    if grow is not None:                                             # v56: the base is the grown frame, its row 0 north of the world
        px0, py0 = int(round(grow['ox'])), int(round(grow['oy']))
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
    Rw = R
    if grow is not None:                                             # v56: the dry beds in sand, not near-white
        Rw = dict(R); Rw['sand_warm'] = list(R['sand_warm'][:5]) + [R['sand_warm'][3]]
    M54.water_and_routes(canvas, S, Rw, ink, k, ox, oy, M)
    d = ImageDraw.Draw(canvas, 'RGBA')
    if grow is not None:                                             # v56: boats berth at jetties, rails cross rivers on bridges
        lines, jet = boat_ends56(S, lines)
        draw_jetties56(d, jet, P, R, ink, s)
        rail_bridges56(d, S, lines, P, R, ink, s)
        footbridges56(d, S, P, R, ink, s)
        bay_wakes56(d, S, P, R, s)
    draw_lines(d, lines, P, R, ink, s)
    draw_street_bridges(d, S, R, ink, P, k)
    draw_shrines(d, S, R, ink, P, k, s)
    draw_city_features(d, S, R, ink, P, k, s)
    draw_forest(d, S, R, ink, P, k, s)
    draw_kerbs(d, S, R, P, k)
    draw_walls(d, S, R, ink, P, k)
    if grow is not None:
        draw_farmsteads56(d, S, grow.get('steads', []), R, ink, P, s, k)
        draw_trees56(d, grow.get('trees', []), R, ink, P, k)
        draw_company56(d, S, R, ink, P, s, k)
    draw_towns(d, S, R, ink, P, s, k, roofs=grow is not None)
    if grow is not None:                                             # v56: the map's small secrets (map_secrets56, proposals)
        import map_secrets56 as MS
        MS.draw(d, grow['Sx'], P, R, ink, k, s)
    neon_accents(d, S, P, s, k, lines)
    draw_closed_pass(d, S, M, R, ink, P, s)
    draw_cape(d, S, M, R, ink, P, s)
    canvas = neon_glow(canvas, S, P, s, k, M)
    d = ImageDraw.Draw(canvas, 'RGBA')
    haze = None
    if box is None and grow is not None:                             # v56: four edges of weather, far islands in the south fog
        import grow56 as GR
        canvas, haze = GR.edge_frame(canvas, grow['Sx'], R, s, k, grow['ox'], grow['oy'])
        d = ImageDraw.Draw(canvas, 'RGBA'); GR.far_islands(d, R, s, Wc, Hc)
        import map_secrets56 as MS
        MS.draw(d, grow['Sx'], P, R, ink, k, s, after=True)
    elif box is None:
        canvas = cloud_bank(canvas, S, M, R, s, k, ox, oy, window=P(*M.HIGHGARTH_PASS))
        far_land(canvas, M, R, s, P)
        d = ImageDraw.Draw(canvas, 'RGBA')
    if box is None and mode == 'continent' and grow is None:         # v56 drops the dashed inset boxes (the insets are their own maps)
        M54.inset_mark(d, M, R, ink, P, s)
    if box is None and mode == 'continent' and grow is None:
        nb = M.NEON_INSET; pts = [(nb[0], nb[1]), (nb[2], nb[1]), (nb[2], nb[3]), (nb[0], nb[3]), (nb[0], nb[1])]
        polyline(d, pts, P, R['plaster'][5] + (170,), 2.4 * s, dash=(6 * s, 5 * s)); polyline(d, pts, P, ink + (150,), 1.0 * s, dash=(6 * s, 5 * s))
    d.rectangle([3 * s, 3 * s, Wc - 3 * s, Hc - 3 * s], outline=ink, width=max(1, int(2 * s)))
    d.rectangle([7 * s, 7 * s, Wc - 7 * s, Hc - 7 * s], outline=R['timber'][3], width=max(1, int(s)))
    reserved = (panel_boxes(Wc, Hc, s) if panels_on else []) + [(0, 0, Wc, 26 * s)]
    _am = M54.act_marks
    if grow is not None:
        M54.act_marks = act_marks56                                  # v56: beats that share a spot are set apart
    reserved += [(X - 7 * s, Y - 7 * s, X + 7 * s, Y + 7 * s) for i, X, Y in M54.act_marks(M, P, s)] if act else []
    if grow is not None:
        reserved += [(0, 0, Wc, 52 * s), (0, 0, 52 * s, Hc), (Wc - 48 * s, 0, Wc, Hc), (0, Hc - 30 * s, Wc, Hc), built_tag56(M, P, s)]
        for town in ('Gullwick', 'Driftwood', 'Lullford', 'Dust Gulch', 'Palm Spring'):    # the hand-laid towns' names never sit on their houses
            for (x, y, w, h_, *_r) in (S['towns'].get(town) or {}).get('buildings', []):
                X0, Y0 = P(x, y); X1, Y1 = P(x + w, y + h_)
                reserved.append((X0 - s, Y0 - s, X1 + s, Y1 + s))
    else:
        reserved += [M54.built_tag(P, s)]
    lab, pl = labels55(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, lines, reserved, mode=mode, box=box)
    built = overlay_built56(S, M, R, ink, s, k, ox, oy, Wc, Hc, F) if grow is not None else M54.overlay_built(S, M, R, ink, s, k, ox, oy, Wc, Hc, F)
    if grow is not None:                                             # the built outline breaks round every name instead of crossing it
        ba = np.asarray(built).copy(); tb_ = built_tag56(M, P, s)
        for b_ in pl.boxes:
            x0_, y0_, x1_, y1_ = [int(round(v)) for v in (b_[0] - 2 * s, b_[1] - 2 * s, b_[2] + 2 * s, b_[3] + 2 * s)]
            if x1_ < tb_[0] or x0_ > tb_[2] or y1_ < tb_[1] or y0_ > tb_[3]:
                ba[max(0, y0_):max(0, y1_), max(0, x0_):max(0, x1_), 3] = 0
        built = Image.fromarray(ba, 'RGBA')
    layers = [built]
    if act:
        layers.insert(0, M54.overlay_ring(S, M, R, ink, s, k, ox, oy, Wc, Hc, F))
    layers.append(lab)
    if act:
        M54.act_marks = act_marks56 if grow is not None else _am
        layers.append(M54.overlay_act1(S, M, R, ink, s, k, ox, oy, Wc, Hc, F, paths))
    M54.act_marks = _am
    out = canvas.convert('RGBA')
    for layer in layers:
        out.alpha_composite(layer)
    if panels_on:
        pan = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); panels55(pan, S, M, R, ink, s, k, Wc, Hc, F, act1=act, title=title)
        out.alpha_composite(pan)
    return out, pl.missed, {'canvas': canvas, 'built': built, 'labels': lab, 'haze': haze}


def act_marks56(M, P, s):
    """act 1's beat marks, each set apart from any earlier one it would overlap (stepped west, then north)."""
    out = []
    for i, (nm, p, what) in enumerate(M.ACT1):
        X, Y = P(*p); X -= 9 * s; Y -= 9 * s
        for step in range(12):
            if all(math.hypot(X - a, Y - b) >= 14 * s for _, a, b in out):
                break
            X -= 14 * s if step % 2 == 0 else 0; Y -= 0 if step % 2 == 0 else 14 * s
        out.append((i, X, Y))
    return out


def _crossings(P_, Q_):
    """Where polyline P_ crosses polyline Q_: (x, y, segment index in P_)."""
    out = []
    P_ = np.asarray(P_, float); Q_ = np.asarray(Q_, float)
    if len(P_) < 2 or len(Q_) < 2:
        return out
    qa, qb = Q_[:-1], Q_[1:]
    for i in range(len(P_) - 1):
        a, b = P_[i], P_[i + 1]
        dd = (b[0] - a[0]) * (qb[:, 1] - qa[:, 1]) - (b[1] - a[1]) * (qb[:, 0] - qa[:, 0])
        with np.errstate(divide='ignore', invalid='ignore'):
            t = ((qa[:, 0] - a[0]) * (qb[:, 1] - qa[:, 1]) - (qa[:, 1] - a[1]) * (qb[:, 0] - qa[:, 0])) / dd
            u = ((qa[:, 0] - a[0]) * (b[1] - a[1]) - (qa[:, 1] - a[1]) * (b[0] - a[0])) / dd
        for j in np.flatnonzero((dd != 0) & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)):
            x, y = a[0] + t[j] * (b[0] - a[0]), a[1] + t[j] * (b[1] - a[1])
            if all(math.hypot(x - x2, y - y2) > 60 for x2, y2, _ in out):
                out.append((x, y, i))
    return out


def rail_bridges56(d, S, lines, P, R, ink, s):
    """Where a rail or cart line crosses a river, a bridge: a stone deck over the water with parapets in ink (a viaduct's
    piers below it when the line is a viaduct)."""
    rivers = {nm: p for nm, p in S['river_px'].items() if nm not in ('the Dry Fork', 'Brackens wash')}
    for nm, kind, pts, way in lines:
        if kind == 'boat':
            continue
        for rn, rp in rivers.items():
            for x, y, i in _crossings(pts, rp):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                L = math.hypot(bx - ax, by - ay) or 1; ux, uy = (bx - ax) / L, (by - ay) / L
                half = 110 if 'viaduct' in nm.lower() else 56
                X0, Y0 = P(x - ux * half, y - uy * half); X1, Y1 = P(x + ux * half, y + uy * half)
                Ls = math.hypot(X1 - X0, Y1 - Y0) or 1; nx, ny = -(Y1 - Y0) / Ls, (X1 - X0) / Ls
                w = 3.0 * s
                quad = [(X0 + nx * w, Y0 + ny * w), (X1 + nx * w, Y1 + ny * w), (X1 - nx * w, Y1 - ny * w), (X0 - nx * w, Y0 - ny * w)]
                d.polygon([(qx + 1.2 * s, qy + 1.6 * s) for qx, qy in quad], fill=ink + (90,))      # its shadow on the water
                d.polygon(quad, fill=R['stone'][4], outline=ink)
                if 'viaduct' in nm.lower():
                    for f in np.linspace(0.15, 0.85, 4):
                        cx_, cy_ = X0 + (X1 - X0) * f, Y0 + (Y1 - Y0) * f
                        d.rectangle([cx_ - 0.8 * s, cy_ + w, cx_ + 0.8 * s, cy_ + w + 2.4 * s], fill=R['stone'][2], outline=ink)


def footbridges56(d, S, P, R, ink, s):
    """The old forest's boardwalk crosses the Lull in the Narrows: a timber footbridge where it does."""
    F = S.get('forest') or {}
    bw = (F.get('features') or {}).get('boardwalk_px')
    if not bw:
        return
    for nm, rp in S['river_px'].items():
        for x, y, i in _crossings(bw, rp):
            (ax, ay), (bx, by) = bw[i], bw[i + 1]
            L = math.hypot(bx - ax, by - ay) or 1; ux, uy = (bx - ax) / L, (by - ay) / L
            X0, Y0 = P(x - ux * 40, y - uy * 40); X1, Y1 = P(x + ux * 40, y + uy * 40)
            Ls = math.hypot(X1 - X0, Y1 - Y0) or 1; nx, ny = -(Y1 - Y0) / Ls, (X1 - X0) / Ls; w = 1.8 * s
            quad = [(X0 + nx * w, Y0 + ny * w), (X1 + nx * w, Y1 + ny * w), (X1 - nx * w, Y1 - ny * w), (X0 - nx * w, Y0 - ny * w)]
            d.polygon([(qx + 1.0 * s, qy + 1.4 * s) for qx, qy in quad], fill=ink + (80,))
            d.polygon(quad, fill=R['timber'][4], outline=ink)


def bay_wakes56(d, S, P, R, s):
    """Two wake lines in Neon's bay: boats coming in through the opening toward the ferry piers."""
    hb = (((S.get('plans') or {}).get('neon-harbour') or {}).get('features') or {}).get('harbour') or {}
    if hb.get('shape') != 'half moon':
        return
    cx, cy = hb['bay_centre_px']; rb = hb['bay_radius_px']
    for sx in (-1, 1):
        pts = [(cx + sx * (60 + 30 * t), cy + 120 - 300 * t + 40 * t * t) for t in np.linspace(0, 1, 8)]
        for j in range(len(pts) - 1):
            if j % 2 == 0:
                d.line([P(*pts[j]), P(*pts[j + 1])], fill=R['snow'][5] + (200,), width=max(1, int(round(0.9 * s))))
        X, Y = P(*pts[-1]); r_ = 1.6 * s
        d.ellipse([X - r_, Y - r_ * 0.7, X + r_, Y + r_ * 0.7], fill=R['plaster'][5], outline=(30, 26, 34))


def boat_ends56(S, lines):
    """Ferry and steamer lines end at a jetty, not on the beach or in open water: a line whose end is on land is cut back
    to the shore and given a jetty out to its new end; a line ending in open water gets a jetty from the nearest shore. An
    end already at a plan's pier (Neon's ferry piers) is left alone. Returns the lines and the jetties (shore, head)."""
    land = S['land']; Hh, Ww = land.shape
    piers = []
    for P_ in (S.get('plans') or {}).values():
        hb = (P_.get('features') or {}).get('harbour') or {}
        piers += [tuple(q['to_px']) for q in hb.get('piers', [])]
    _, (iy, ix) = ndi.distance_transform_edt(~land, return_indices=True)

    def on_land(p):
        cy, cx = int(min(max(p[1] // CELL, 0), Hh - 1)), int(min(max(p[0] // CELL, 0), Ww - 1))
        return bool(land[cy, cx]), (cy, cx)
    out = []; jet = []
    for nm, kind, pts, way in lines:
        if kind != 'boat':
            out.append((nm, kind, pts, way)); continue
        pts = list(pts)
        for end in (0, -1):
            q = pts if end == 0 else pts[::-1]
            e = q[0]
            if any(math.hypot(e[0] - a, e[1] - b) < 48 for a, b in piers):
                continue
            ld, (cy, cx) = on_land(e)
            if ld:                                                  # cut back to the first water, a jetty from the shore out 64 px
                j = 0
                while j < len(q) - 1 and on_land(q[j])[0]:
                    j += 1
                (sx, sy) = q[max(0, j - 1)]; (wx, wy) = q[j]
                L = math.hypot(wx - sx, wy - sy) or 1; ux, uy = (wx - sx) / L, (wy - sy) / L
                head = (sx + ux * 64, sy + uy * 64)
                q = [head] + q[j + 1:] if math.hypot(q[j][0] - sx, q[j][1] - sy) < 64 else [head] + q[j:]
                jet.append(((sx, sy), head))
            else:                                                   # in open water: a jetty from the nearest shore cell
                sx, sy = (ix[cy, cx] + 0.5) * CELL, (iy[cy, cx] + 0.5) * CELL
                if math.hypot(e[0] - sx, e[1] - sy) < 240:
                    jet.append(((sx, sy), e))
            pts = q if end == 0 else q[::-1]
        out.append((nm, kind, pts, way))
    return out, jet


def draw_jetties56(d, jet, P, R, ink, s):
    """A timber jetty: planks on posts, lit on its west edge, its shadow on the water."""
    for (sx, sy), (hx, hy) in jet:
        A = P(sx, sy); B = P(hx, hy)
        L = math.hypot(B[0] - A[0], B[1] - A[1]) or 1; nx, ny = -(B[1] - A[1]) / L, (B[0] - A[0]) / L
        w = 1.8 * s
        quad = [(A[0] + nx * w, A[1] + ny * w), (B[0] + nx * w, B[1] + ny * w), (B[0] - nx * w, B[1] - ny * w), (A[0] - nx * w, A[1] - ny * w)]
        d.polygon([(qx + 1.0 * s, qy + 1.4 * s) for qx, qy in quad], fill=ink + (80,))
        d.polygon(quad, fill=R['timber'][4], outline=ink)
        d.rectangle([B[0] - 2.6 * s, B[1] - 2.6 * s, B[0] + 2.6 * s, B[1] + 2.6 * s], fill=R['timber'][3], outline=ink)   # the landing stage


def built_tag56(M, P, s):
    x0 = min(b[0] for b in M.BUILT.values()); y0 = min(b[1] for b in M.BUILT.values())
    X, Y = P(x0, y0)
    return (X, Y - 13 * s, X + 56 * s, Y)


def overlay_built56(S, M, R, ink, s, k, ox, oy, Wc, Hc, F):
    """What the game has built so far, as one outline: the union of the built boxes drawn as a single brass line on the
    cell lines (no wash over the map, no dashes), with its tag sitting on the outline's top-left corner like a file tab."""
    lay = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    P = lambda x, y: (x * k + ox, y * k + oy)
    m = Image.new('L', (Wc, Hc), 0); dm = ImageDraw.Draw(m)
    for nm, (x0, y0, x1, y1) in M.BUILT.items():
        if 'below' in nm:
            continue
        a, b = P(x0, y0), P(x1, y1)
        dm.rectangle([round(a[0]), round(a[1]), round(b[0]), round(b[1])], fill=255)
    mm = np.asarray(m) > 0
    edge = mm & ~ndi.binary_erosion(mm, iterations=max(1, int(round(1.4 * s))))
    outer = ndi.binary_dilation(mm, iterations=max(1, int(round(1.0 * s)))) & ~mm
    arr = np.zeros((Hc, Wc, 4), np.uint8)
    arr[outer] = ink + (150,)
    arr[edge] = R['brass'][5] + (255,)
    lay = Image.fromarray(arr, 'RGBA'); d = ImageDraw.Draw(lay)
    tb = built_tag56(M, P, s)
    d.rectangle(tb, fill=R['brass'][4] + (255,), outline=ink)
    d.text(((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2 + 0.5 * s), 'BUILT NOW', font=F['way'], fill=ink, anchor='mm')
    return lay


# ------------------------------------------------------------------------------------------ the town plans, one inset each
TOWN_INSETS = (('crossroads', 8.0), ('dust-gulch', 8.0), ('hearthold', 8.0), ('neon-harbour', 6.0), ('highgarth', 8.0), ('cinderwick', 8.0))
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
    draw_shrines(d, S, R, ink, Pf, kb, max(1.0, ppc / 4), [P])
    draw_city_features(d, S, R, ink, Pf, kb, max(1.0, ppc / 4), [P])
    draw_kerbs(d, S, R, Pf, kb, [P])
    draw_walls(d, S, R, ink, Pf, kb)
    draw_towns(d, S, R, ink, Pf, max(1.0, ppc / 4), kb)
    TH = P.get('theme') or {}
    if TH:                                                           # the theme: waystone, the line to the beam, the crater, Moss, the Company
        sl_ = TH.get('sightline')
        if sl_:
            (fx_, fy_), (tx_, ty_) = sl_['from_px'], sl_['to_px']
            br = math.radians(sl_['bearing_deg'])
            ex_, ey_ = tx_ + math.cos(br) * 400, ty_ + math.sin(br) * 400
            polyline(d, [(fx_, fy_), (ex_, ey_)], Pf, (250, 240, 190, 230), max(2.0, 3 * kb), dash=(10 * kb + 4, 8 * kb + 3))
        ws_ = TH.get('waystone')
        if ws_:
            X, Y = Pf(*ws_['xy_px']); r_ = max(3.0, 5 * kb)
            d.polygon([(X - r_ * 0.6, Y + r_), (X - r_ * 0.45, Y - r_ * 1.2), (X, Y - r_ * 1.8), (X + r_ * 0.45, Y - r_ * 1.2), (X + r_ * 0.6, Y + r_)],
                      fill=(150, 170, 200, 255), outline=ink + (255,))
            d.line([(X - r_ * 0.3, Y - r_ * 0.6), (X + r_ * 0.3, Y - r_ * 0.6)], fill=(200, 230, 255, 255), width=max(1, int(kb * 2)))
    PROP_RGB = {'sign': (236, 196, 72), 'awning': (196, 70, 80), 'AC unit': (200, 210, 220), 'pipes': (120, 120, 130), 'gas tank': (230, 230, 220),
                'potted plants': (90, 150, 70), 'planter tree': (60, 120, 60), 'washing line': (240, 240, 240)}
    for st in P['streets']:                                          # the frontage props, a dot each
        for q in st.get('frontage_props', []):
            X, Y = Pf(*q['at_px']); r_ = max(1.0, ppc * 0.22)
            d.rectangle([X - r_, Y - r_, X + r_, Y + r_], fill=PROP_RGB.get(q['kind'], (180, 160, 120)) + (255,), outline=ink + (160,))
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
    TH = P.get('theme') or {}
    for key_, col_, lab_ in (('moss', (90, 150, 90), 'M'), ('company', (150, 70, 150), 'C')):
        q = TH.get(key_) or {}
        if q.get('xy_px'):
            X, Y = Pf(*q['xy_px']); r_ = 7 * s_
            dl.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=col_ + (240,), outline=ink + (255,), width=2)
            dl.text((X, Y), lab_, font=F['way'], fill=(255, 255, 255), anchor='mm')
            pl.reserve((X - r_, Y - r_, X + r_, Y + r_))
    for b in P['buildings']:
        x, y, bw, bh = b['rect_px']; X0, Y0 = Pf(x, y); X1, Y1 = Pf(x + bw, y + bh)
        pl.reserve((X0, Y0, X1, Y1))
    if TH.get('waystone'):
        X, Y = Pf(*TH['waystone']['xy_px'])
        pl.put((X, Y), 'waystone', F['small'], (40, 60, 100), paper + (235,), around(9 * s_, s_), stroke=2, leader=[26 * s_, 40 * s_], name=False)
    if TH.get('sightline'):
        X, Y = Pf(*TH['sightline']['to_px'])
        pl.put((X, Y), 'toward the beam', F['small'], (120, 100, 40), paper + (235,), around(6 * s_, s_), stroke=2, leader=[24 * s_], name=False)
    if TH.get('crater'):                                               # an arrow at the inset's edge toward the region's crater
        cxp, cyp = TH['crater']['xy_px']
        mx_, my_ = Pf((P['footprint_px'][0] + P['footprint_px'][2]) / 2, (P['footprint_px'][1] + P['footprint_px'][3]) / 2)
        tx_, ty_ = Pf(cxp, cyp); ang = math.atan2(ty_ - my_, tx_ - mx_)
        t_ = min((Wb / 2 - 30 * s_) / max(1e-6, abs(math.cos(ang))), (Hb / 2 - 30 * s_) / max(1e-6, abs(math.sin(ang))))
        ax_, ay_ = Wb / 2 + math.cos(ang) * t_, Hb / 2 + math.sin(ang) * t_
        r_ = 9 * s_
        dl.polygon([(ax_ + math.cos(ang) * r_, ay_ + math.sin(ang) * r_), (ax_ + math.cos(ang + 2.5) * r_, ay_ + math.sin(ang + 2.5) * r_),
                    (ax_ + math.cos(ang - 2.5) * r_, ay_ + math.sin(ang - 2.5) * r_)], fill=(120, 80, 170, 240), outline=ink + (255,))
        pl.reserve((ax_ - r_, ay_ - r_, ax_ + r_, ay_ + r_))
        pl.put((ax_, ay_), f"to {TH['crater']['name']}", F['small'], (90, 50, 130), paper + (235,), around(r_, s_), stroke=2, name=False)
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
    Placer.draw_text(_D_, (x0, y + 6 * s_), f"town plan, {getattr(M, 'REVISION', 'v55')} ({getattr(M, 'PLAN_DIRECTORY', 'towns')}/{P['id']}.json)", F['small'], R['timber'][2], paper, 'lm', 0); y += 22 * s_
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
    for what in ('landmark (seen from the ways in)', 'way in', 'door', 'shortcut that opens later', 'quiet corner', 'frontage prop (sign, awning, plants...)',
                 'waystone (a chip of the circle)', 'M: where Moss trades', "C: the Company's foothold", 'toward the beam / the crater'):
        X, Y = x0 + 13 * s_, y + 5 * s_; r_ = 5 * s_
        if what.startswith('landmark'):
            star = [(X + (r_ if i % 2 == 0 else r_ * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5), Y + (r_ if i % 2 == 0 else r_ * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
            d.polygon(star, fill=(236, 196, 72, 255), outline=ink)
        elif what == 'way in':
            d.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(70, 130, 170, 235), outline=ink)
        elif what == 'door':
            d.rectangle([X - 2, Y - 2, X + 2, Y + 2], fill=ink)
        elif what.startswith('waystone'):
            d.polygon([(X - 3, Y + 5), (X - 2, Y - 4), (X, Y - 7), (X + 2, Y - 4), (X + 3, Y + 5)], fill=(150, 170, 200), outline=ink)
        elif what.startswith('M:') or what.startswith('C:'):
            d.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(90, 150, 90) if what.startswith('M') else (150, 70, 150), outline=ink)
        elif what.startswith('toward'):
            d.line([(X - 8, Y), (X + 8, Y)], fill=(200, 180, 90), width=2)
        elif what.startswith('frontage'):
            d.rectangle([X - 2, Y - 2, X + 2, Y + 2], fill=(236, 196, 72), outline=ink)
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


def sea_tints(sea_rgb, S, R=None):
    mat = S.get('mat')
    if mat is None:
        return sea_rgb
    sea_rgb = sea_rgb.copy()
    hb = (((S.get('plans') or {}).get('neon-harbour') or {}).get('features') or {}).get('harbour')
    if hb and R is not None:                                           # Neon's basin: a shallow band along every quay, a deep
        bx0, by0, bx1, by1 = hb['basin_px']                            # channel from the mouth to the islands, the rest between
        Hh, Ww = S['land'].shape
        yy, xx = np.mgrid[0:Hh, 0:Ww]; Xw = (xx + 0.5) * CELL; Yw = (yy + 0.5) * CELL
        inb = (Xw >= bx0 - 8) & (Xw <= bx1 + 8) & (Yw >= by0 - 8) & (Yw <= by1 + 200) & ~S['land']
        d = ndi.distance_transform_edt(~S['land']) * CELL
        cx0, cy0, cx1, cy1 = hb['channel_px']
        chan = (Xw >= cx0) & (Xw <= cx1) & (Yw >= cy0) & (Yw <= cy1)
        sea_rgb[inb] = R['water_warm'][3]
        sea_rgb[inb & chan & (d > 24)] = R['water'][2]
        sea_rgb[inb & (d <= 24)] = R['water_warm'][4]
        if hb.get('shape') == 'half moon':                              # v56: a wider shelf and a dark deep centre, so the bay reads at 1920
            cxb, cyb = hb['bay_centre_px']; rb = hb['bay_radius_px']
            rr = np.hypot(Xw - cxb, Yw - cyb)
            sea_rgb[inb & (d <= 48)] = R['water_warm'][4]
            sea_rgb[inb & (d > 48) & (rr < rb * 0.62)] = R['water'][2]
            sea_rgb[inb & (d > 64) & (rr < rb * 0.42)] = R['water'][1]
    m = (mat == 23) & ~S['land']
    if m.any():
        import town_plans as TP
        nm, col, a = TP.MATERIALS[23]
        sea_rgb[m] = sea_rgb[m] * (1 - a) + np.array(col, np.float32) * a
    return sea_rgb


NEON_CYAN, NEON_MAGENTA = (64, 232, 240), (236, 72, 196)


def neon_glow(canvas, S, P, s, k, M):
    """Neon Harbour on bought shard light: a glow round the Company's tower and district and over its yard's crater, the
    brightest things on the map."""
    plan = (S.get('plans') or {}).get('neon-harbour')
    if not plan:
        return canvas
    lay = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); dg = ImageDraw.Draw(lay)
    dt = {d_['id']: d_.get('town', '') for d_ in plan['districts']}
    for b in plan['buildings']:
        if dt.get(b['district'], '').endswith('the Company district'):
            x, y, w, h_ = b['rect_px']; X0, Y0 = P(x - 16, y - 16); X1, Y1 = P(x + w + 16, y + h_ + 16)
            dg.rectangle([X0, Y0, X1, Y1], fill=(170, 250, 255, 150 if b['type'] == 'tower' else 95))
    cx, cy = M.V.CRATERS['the Company crater'][:2] if hasattr(M, 'V') else (11780, 4159)
    X, Y = P(cx, cy); r_ = 110 * k
    dg.ellipse([X - r_, Y - r_, X + r_, Y + r_], fill=(220, 160, 255, 140))
    lay = lay.filter(ImageFilter.GaussianBlur(max(2, 8 * s)))
    out = canvas.convert('RGBA'); out.alpha_composite(lay)
    return out.convert('RGB')


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


def grow_setup(S, M, R, cg, cid, cols, rgb, sea_rgb):
    """v56's grown frame (grow56): the state's cells grown north and east, the class grid with the massif's rock and snow,
    the lines with their runs past the world's edge. The world's own dims are restored before returning."""
    import grow56 as GR
    W0, H0 = S['dims']
    Fw = features(S, M)
    rivers, closed = GR.draw_lines56(S)
    Wf, Hf = GR.frame_dims(W0, H0)
    M.set_dims(Wf, Hf)
    try:
        Sx, cgx, rgbx, seax = GR.extend(S, R, cg, rgb, sea_rgb, cid, cols, lambda Sx_: M54.sea_colours(Sx_, R))
        _FEAT[id(Sx)] = dict(Fw, m=np.pad(Fw['m'], ((GR.NY, 0), (0, GR.NX)), mode='symmetric'))
        GR.range_field(Sx, rivers, closed)
        cgr = GR.range_classes(Sx, cgx, cid, rivers, closed)
        cg0 = cgr.copy()
        cgr = GR.overview_classes(Sx, cgr, cid, rivers)
        rgbx = GR.recolour(Sx, cgr, rgbx, cols, R, (cgr != cg0) | GR.ne_zone(Sx))   # the ground's colour follows the drawn class
        rgbx = GR.glade_texture(Sx, rgbx, R)
        seax = GR.sea_polish(Sx, seax, R)
        cgr, rgbx, steads = GR.farm_overview(S, Sx, cgr, rgbx, cid, R)
        cg1 = cgr.copy()
        cgr, rgbx = GR.fire_calm(S, Sx, cgr, rgbx, cid, R)
        rgbx = GR.recolour(Sx, cgr, rgbx, cols, R, (cgr != cg1) & (cgr != cid.get('lava', -9)))
    finally:
        M.set_dims(W0, H0)
    audit = lambda Aq, k, ox, oy, lines: GR.haze_audit(Aq, S, M, k, ox, oy, lines, rivers, closed)
    return dict(GR=GR, Sx=Sx, cg=cgr, rgb=rgbx, sea=seax, rivers=rivers, closed=closed, Wf=Wf, Hf=Hf, W0=W0, H0=H0, audit_fn=audit,
                steads=steads)


def grow_fit(GX, Wc, Hc, s):
    """The grown frame fitted to the canvas: k, the world origin's canvas position (for P), and the frame's own origin."""
    k = Hc / GX['Hf']
    if GX['Wf'] * k > Wc - 20 * s:
        k = (Wc - 20 * s) / GX['Wf']
    oxe = (Wc - GX['Wf'] * k) / 2; oye = (Hc - GX['Hf'] * k) / 2
    return k, oxe, oye + GX['GR'].DY * k, {'ox': oxe, 'oy': oye, 'Sx': GX['Sx'], 'steads': GX.get('steads', []),
                                         'trees': GX['Sx'].get('glade_trees', []) + GX['Sx'].get('hedge_trees', [])}


def grow_base(GX, S, M, R, ink, cid, k, ppc):
    """The grown frame's ground at k: the cells at ppc, the massif and the fire country's hills in relief, then the
    trees and tufts (no stamped peaks)."""
    GR = GX['GR']; Sx = GX['Sx']
    M.set_dims(GX['Wf'], GX['Hf'])
    try:
        Hc_, Wc_ = Sx['K'].shape
        base = M54.base_hi(Sx, R, ink, GX['cg'], cid, GX['rgb'], GX['sea'], M, (0, 0, Wc_, Hc_), ppc)
        base = base.resize((int(round(GX['Wf'] * k)), int(round(GX['Hf'] * k))), Image.LANCZOS)
        base, _ = GR.relief(base, Sx, R, ink, k, GX['rivers'], GX['closed'], cgx=GX['cg'], cid=cid)
        stamps55(base, Sx, R, GX['cg'], cid, k, 0, 0, M, ink, peaks=False, calm=('ash', 'lavastone'),
                 sparse={'deadwood': 1.8, 'heath': 1.9, 'scrub': 1.7, 'desert': 1.5, 'steppe': 1.3})
    finally:
        M.set_dims(GX['W0'], GX['H0'])
    return base


def render_all(S, M):
    revision = getattr(M, 'REVISION', 'v55')
    prefix = 'map' + revision[1:]
    R, ink = load_palette(M.ROOT)
    cg, names_, cid, cols = class_grid(S, R, M)
    rgb = ground_tints(M54.cell_colours(S, R, cg, cid, cols), S); sea_rgb = sea_tints(M54.sea_colours(S, R), S, R)
    paths = act1_path(S, M); lines = rail_lines(S)
    outs = [os.environ.get('MAP55_OUT')] if os.environ.get('MAP55_OUT') else []
    outs.append(M.HERE)
    for o in outs:
        os.makedirs(o, exist_ok=True)
    full_box = (0, 0, g.W, g.H)
    missed_all = {}
    # the continent at 1920 and 3840 (one base at the 3840 scale, resampled for 1920)
    s2 = 2; Wc, Hc = BASE_W * s2, BASE_H * s2
    GX = grow_setup(S, M, R, cg, cid, cols, rgb, sea_rgb) if revision == 'v56' else None
    Sd = dict(S, river_px=GX['rivers'], closed_px=GX['closed']) if GX else S       # the lines with their runs past the edge
    if GX:
        k, ox, oy, g2 = grow_fit(GX, Wc, Hc, s2)
        base = grow_base(GX, S, M, R, ink, cid, k, 2.5)
        res2, missed, parts2 = compose(Sd, M, R, ink, s2, base, k, ox, oy, Wc, Hc, paths, lines, 'continent', f'The continent ({revision})', grow=g2)
    else:
        k, ox, oy = frame_fit(Wc, Hc, s2)
        base = M54.base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, full_box, 2.5)          # 2.5 px a cell: whole strips, no seams
        base = base.resize((int(round(g.WPX * k)), int(round(g.HPX * k))), Image.LANCZOS)
        stamps55(base, S, R, cg, cid, k, 0, 0, M, ink)
        res2, missed, parts2 = compose(S, M, R, ink, s2, base, k, ox, oy, Wc, Hc, paths, lines, 'continent', f'The continent: overview ({revision})')
    missed_all['3840'] = missed
    s1 = 1; Wc1, Hc1 = BASE_W, BASE_H
    if GX:
        k1, ox1, oy1, g1 = grow_fit(GX, Wc1, Hc1, s1)
        base1 = base.resize((int(round(GX['Wf'] * k1)), int(round(GX['Hf'] * k1))), Image.LANCZOS)
        res1, missed, parts1 = compose(Sd, M, R, ink, s1, base1, k1, ox1, oy1, Wc1, Hc1, paths, lines, 'continent', f'The continent ({revision})', grow=g1)
        import map_secrets56 as MS                                     # the secrets version: each one circled and numbered
        sec = MS.overlay(res2.convert('RGB'), GX['Sx'], lambda x, y: (x * k + ox, y * k + oy), R, ink, k, s2, M54.fonts54(M.ROOT, s2)['way'])
        for o in outs:
            sec.save(os.path.join(o, f'{prefix}-3840-secrets.png'))
        GX['audit'] = {'1920': GX['audit_fn'](parts1['haze'], k1, ox1, oy1, lines), '3840': GX['audit_fn'](parts2['haze'], k, ox, oy, lines)}
        print('haze audit:', json.dumps(GX['audit']))
    else:
        k1, ox1, oy1 = frame_fit(Wc1, Hc1, s1)
        base1 = base.resize((int(round(g.WPX * k1)), int(round(g.HPX * k1))), Image.LANCZOS)
        res1, missed, parts1 = compose(S, M, R, ink, s1, base1, k1, ox1, oy1, Wc1, Hc1, paths, lines, 'continent', f'The continent: overview ({revision})')
    missed_all['1920'] = missed
    for o in outs:
        res1.convert('RGB').save(os.path.join(o, f'{prefix}-1920.png'))
        res2.convert('RGB').save(os.path.join(o, f'{prefix}-3840.png'))
    if os.environ.get('MAP56_CONTINENT_ONLY'):                      # a quick look while drawing: the two overviews only
        return missed_all
    small = res1.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    small.save(os.path.join(M.DATA, f'continent-1x-{revision}.png'), optimize=True)
    v54 = Image.open(os.path.join(M.DATA, 'continent-1x-v54.png')).convert('RGB')
    cmp_ = Image.new('RGB', (1920 * 2 + 24, 1080 + 40), (30, 26, 34)); dc = ImageDraw.Draw(cmp_)
    cmp_.paste(v54, (0, 40)); cmp_.paste(res1.convert('RGB'), (1920 + 24, 40))
    Fc = fonts(M.ROOT, 1)
    dc.text((10, 20), 'v54 (11264 x 6912 world px)', font=Fc['title'], fill=(240, 230, 210), anchor='lm')
    dc.text((1920 + 34, 20), f'{revision} (12544 x 7168: towns, the east coast, Launch Cape and the closed pass)' if revision != 'v56' else
            'v56 (world 12544 x 7168, drawn to 13568 x 7744: the range, the fens and the sea past the world)', font=Fc['title'],
            fill=(240, 230, 210), anchor='lm')
    for o in outs:
        cmp_.save(os.path.join(o, f'{prefix}-v54-vs-{revision}.png'))
    # the reference: the whole continent at 3x with every name
    s3 = 3; Wc3, Hc3 = BASE_W * s3, BASE_H * s3
    if GX:
        k3, ox3, oy3, g3 = grow_fit(GX, Wc3, Hc3, s3)
        base3 = grow_base(GX, S, M, R, ink, cid, k3, 3.75)
        res3, missed, _ = compose(Sd, M, R, ink, s3 * 0.8, base3, k3, ox3, oy3, Wc3, Hc3, paths, lines, 'full', f'The continent: reference ({revision}), every name', grow=g3)
    else:
        k3, ox3, oy3 = frame_fit(Wc3, Hc3, s3)
        base3 = M54.base_hi(S, R, ink, cg, cid, rgb, sea_rgb, M, full_box, 3.75)
        base3 = base3.resize((int(round(g.WPX * k3)), int(round(g.HPX * k3))), Image.LANCZOS)
        stamps55(base3, S, R, cg, cid, k3, 0, 0, M, ink)
        res3, missed, _ = compose(S, M, R, ink, s3 * 0.8, base3, k3, ox3, oy3, Wc3, Hc3, paths, lines, 'full', f'The continent: reference ({revision}), every name')
    missed_all['reference'] = missed
    for o in outs:
        res3.convert('RGB').save(os.path.join(o, f'{prefix}-reference.png'))
    del base3, res3
    # the insets: the home valley and Neon Harbour, every name
    for tag, bx, ppc, title in (('home-valley', M.INSET, 4.0, f'The home valley ({revision} inset)'), ('neon-harbour', M.NEON_INSET, 4.0, f'Neon Harbour and Launch Cape ({revision} inset)')):
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
            out.convert('RGB').save(os.path.join(o, f'{prefix}-inset-{tag}.png'))
        out.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(os.path.join(M.DATA, f'inset-{tag}-{revision}.png'), optimize=True)
    for pid, ppc in TOWN_INSETS:
        P = (S.get('plans') or {}).get(pid)
        if not P:
            continue
        out = town_inset(S, M, R, ink, cg, cid, rgb, sea_rgb, P, ppc)
        for o in outs:
            out.convert('RGB').save(os.path.join(o, f'{prefix}-town-{pid}.png'))
        out.convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(os.path.join(M.DATA, f'town-{pid}-{revision}.png'), optimize=True)
    print('labels not placed (tiers 1 and 2):', json.dumps(missed_all))
    return missed_all
