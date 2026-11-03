"""v56's map frame: the drawn canvas grows north and east past the world canvas, the range is drawn as one hand-drawn
massif (a spine, spurs, a back range, passes and valley heads) instead of stamped peaks, the fire country's hills are
shaded as dark volcanic rock, and the four edges fade into weather that suits each side.

The world (every table, plan, route, gate and check) stays on its 12544 x 7168 world px canvas. Only the drawing grows:
the map frame is 13568 x 7744 world px and the world's origin sits at (0, 576) inside it, one uniform offset applied at
projection (P), so every relative position is unchanged. The bands added north (72 cells) and east (128 cells) carry no
town, road, rail, ferry or label; the only lines that run into them are the ones that leave the world (the closed pass
road, river heads, the Glint out of the fens), and those run on into the haze."""
import math
import numpy as np
from scipy import ndimage as ndi
from PIL import Image

from geo5 import CELL

NY, NX = 72, 128                     # cells added to the north and to the east
DY, EX = NY * CELL, NX * CELL        # 576 and 1024 world px: 8.0 % and 8.2 %
NATURAL = ('conifer', 'ancient', 'wild', 'thicket', 'bog', 'mere', 'pool', 'sinkhole', 'reeds', 'carr', 'broadleaf', 'scrub', 'steppe',
           'meadow', 'bramble', 'heath', 'gorse', 'alpine', 'scree', 'scree2', 'talus', 'moraine', 'boulders', 'crag', 'glacier', 'snow',
           'barren', 'tor', 'clearing')
CLOUD_TOP = -330                     # world y: the north cloud bank's mean lower edge; nothing drawn above it matters


def frame_dims(Wpx, Hpx):
    return Wpx + EX, Hpx + DY


def fbm1(n, scales, seed):
    out = np.zeros(n, np.float32); r = np.random.default_rng(seed)
    for sc, amp in scales:
        pts = r.uniform(-1, 1, int(n / sc) + 3)
        out += amp * np.interp(np.arange(n) / sc, np.arange(len(pts)), pts)
    return out


class Noise2:
    """Smooth value noise in [-1, 1], one feature every `scale` samples (a cubic spline through a random lattice), read a
    band of rows at a time so a large image never needs its whole field in memory."""

    def __init__(self, shape, scale, seed):
        r = np.random.default_rng(seed)
        self.scale = scale
        self.lat = r.uniform(-1, 1, (int(shape[0] / scale) + 4, int(shape[1] / scale) + 4)).astype(np.float32)
        self.W = shape[1]

    def rows(self, r0, r1):
        yy = np.arange(r0, r1, dtype=np.float32) / self.scale + 1
        xx = np.arange(self.W, dtype=np.float32) / self.scale + 1
        Y, X = np.meshgrid(yy, xx, indexing='ij')
        return ndi.map_coordinates(self.lat, [Y, X], order=3, mode='nearest', output=np.float32)


def vnoise(shape, scale, seed):
    return Noise2(shape, scale, seed).rows(0, shape[0])


def to_cells(pts, n_rows, n_cols, step=4.0):
    """A world-px polyline as ext-grid cell indices (rows, cols), densified."""
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, int(L / step))
        t = np.linspace(0, 1, n + 1)
        out.append(np.stack([ay + (by - ay) * t, ax + (bx - ax) * t], 1))
    if not out:
        return np.zeros(0, int), np.zeros(0, int)
    a = np.concatenate(out)
    r = (a[:, 0] / CELL + NY).astype(int); c = (a[:, 1] / CELL).astype(int)
    ok = (r >= 0) & (r < n_rows) & (c >= 0) & (c < n_cols)
    return r[ok], c[ok]


# ------------------------------------------------------------------------------------------ the lines that leave the world
def head_north(pts, top_y, seed, wander=60):
    """A river that rises at the world's north edge, continued up its valley to a glacier snout at top_y."""
    x0, y0 = pts[0]
    n = max(3, int((y0 - top_y) / 40))
    dx = fbm1(n + 1, [(6, wander), (2, wander * 0.3)], seed)
    dx -= dx[-1]                                            # meets the old head exactly
    lead = [(x0 + dx[i], top_y + (y0 - top_y) * i / n) for i in range(n)]
    return [(float(a), float(b)) for a, b in lead] + list(pts)


def draw_lines56(S):
    """The state's lines with v56's continuations past the world's edge, for drawing only: the rivers that rise at the
    north edge run up to their glacier snouts, the Glint comes out of the fens past the east edge, and the closed pass road
    runs on north through its col into the cloud."""
    rivers = dict(S['river_px'])
    sx, sy = zip(*SPINE)
    heads = {'the Amber': 3, 'the Cog': 5, 'the Lull': 6, 'the Sorrel': 7}          # the Rift already runs on north, in its gorge
    for nm, seed in heads.items():
        if nm in rivers and rivers[nm][0][1] < 300:
            top = float(np.interp(rivers[nm][0][0], sx, sy)) + 90              # each rises in a cirque under the spine
            if rivers[nm][0][1] > top + 40:
                rivers[nm] = head_north(rivers[nm], top, 4400 + seed)
    if 'the Glint' in rivers:
        pts = list(rivers['the Glint'])
        x0, y0 = pts[0]
        lead = [(x0 + 640 - i * 64 + 18 * math.sin(i * 0.9), y0 - 120 + i * 12 + 22 * math.cos(i * 0.7)) for i in range(10)]
        rivers['the Glint'] = lead + pts
    closed = list(S['closed_px'])
    x1, y1 = closed[-1]
    closed = closed + [(x1 + 4, y1 - 120), (x1 + 14, y1 - 260), (x1 + 8, y1 - 420), (x1 - 6, y1 - 560), (x1 - 10, -DY - 60)]
    return rivers, closed


# ------------------------------------------------------------------------------------------ the state, grown
def coast_rows(n):
    """The fens' coast past the east edge: from the world's coast row (4232) bending north-east, wandering."""
    x = np.arange(n) * CELL
    y = (4236 - 0.3 * x - 160 * np.sin(x / 700.0) ** 2 + fbm1(n, [(40, 110), (14, 36), (5, 10)], 5611) * np.clip(x / 260, 0, 1)
         + 230 * np.exp(-((x - 430) / 95) ** 2)                      # a headland running out south-east
         - 120 * np.exp(-((x - 640) / 70) ** 2) - 90 * np.exp(-((x - 190) / 60) ** 2))   # coves either side of it
    return (y // CELL).astype(int)


def extend(S, R, cg, rgb, sea_rgb, cid, cols, sea_new):
    """The state's cell arrays grown NY rows north and NX columns east (mirrored ground, built things replaced by the
    nearest natural ground, the sea where the east edge is sea), and the class grid and colours to match."""
    H, W = S['K'].shape
    kinds = list(S['kinds']); kid = {k: i for i, k in enumerate(kinds)}
    pad = ((NY, 0), (0, NX))

    def mirror(a):
        return np.pad(a, pad + ((0, 0),) * (a.ndim - 2), mode='symmetric')
    K = mirror(S['K']); h = mirror(S['h'].astype(np.float32)); tiers = mirror(S['tiers']); real = mirror(S['real'])
    land = mirror(S['land']); frame = np.ones_like(land); frame[NY:, :W] = S['frame']
    band = np.ones_like(land); band[NY:, :W] = False
    # east band: land above the bent coast, sea below
    cr = coast_rows(NX) + NY
    rows = np.arange(H + NY)[:, None]
    east_land = rows < cr[None, :]
    land[:, W:] = east_land
    natural = np.isin(K, [kid[k] for k in NATURAL if k in kid])
    fix = band & land & ~natural
    if fix.any():
        _, (iy, ix) = ndi.distance_transform_edt(~(natural & land), return_indices=True)
        K = np.where(fix, K[iy, ix], K)
    # past the old forest the band is forest and fen, not open steppe: the far north-east is the old forest's giant trees
    cols_x = np.arange(W + NX) * CELL
    nz_ = ndi.gaussian_filter(np.random.default_rng(5612).standard_normal(land.shape).astype(np.float32), 5)
    nz_ /= nz_.std() + 1e-6
    depth = (NY - np.arange(H + NY))[:, None] / NY                      # 1 at the top, 0 at the world's edge
    ne = band & land & (cols_x[None, :] > 9600) & (nz_ * 0.5 + np.where(depth > 0, depth, 1.0) * 1.4 > 0.55)
    open_ = np.isin(K, [kid[k] for k in ('steppe', 'scrub', 'meadow', 'scree', 'scree2', 'alpine', 'barren', 'talus', 'moraine', 'boulders') if k in kid])
    K = np.where(ne & open_, np.where(nz_ > 0.1, kid['ancient'], kid['conifer']), K)
    yrow = (np.arange(H + NY) - NY)[:, None] * CELL
    wet = nz_ * 0.75 + np.clip((yrow - 2600) / 1400, 0, 1) * 0.8 - 0.35   # bog with scattered meres, not one sheet of water
    nz2 = ndi.gaussian_filter(np.random.default_rng(5613).standard_normal(land.shape).astype(np.float32), 3)
    nz2 /= nz2.std() + 1e-6
    eb = np.zeros_like(band); eb[:, W:] = (nz2[:, W:] * 0.9 + np.arange(NX)[None, :] / 28.0) > 0.7    # the world's edge ground runs on a little
    eb &= land
    fen = np.where(wet > 1.05, kid['mere'], np.where(wet > 0.35, kid['bog'], np.where(nz_ > -0.2, kid['ancient'], kid['conifer'])))
    # the band starts a little inside the world's wall, so its straight strip of trees does not double
    K = np.where(eb, fen, K)
    wk = np.isin(K, [kid[k] for k in ('sea', 'surf') if k in kid])        # no mirrored sea left on the band's land
    if (band & land & wk).any():
        K = np.where(band & land & wk, kid['bog'], K)
    beach = east_land & ~np.vstack([east_land[2:], np.zeros((2, NX), bool)]) & (nz2[:, W:] > -0.6)
    K[:, W:][beach] = kid['sand']                                    # a beach along the band's coast, broken where the fen comes down
    K[:, W:][~east_land] = kid['sea']
    sea_tier = int(np.min(S['tiers'][~S['land']])) if (~S['land']).any() else -1
    tiers[:, W:][~east_land] = sea_tier
    tiers[:, W:][east_land] = np.maximum(tiers[:, W:][east_land], 0)
    mat = np.zeros(land.shape, S['mat'].dtype); mat[NY:, :W] = S['mat']
    crater = np.zeros(land.shape, bool); crater[NY:, :W] = S['crater_mask']
    Sx = dict(S)
    Sx.update(K=K, h=h, tiers=tiers, real=real, land=land, sea=~land, frame=frame, mat=mat, crater_mask=crater)
    Sx['band'] = band
    # classes: the world's grid as drawn, the bands by the same lookup
    lut = np.full(len(kinds), cid['meadow'], np.int16)
    from map54 import classes
    k2c = {k: cid[n] for n, (ks, _) in classes(R).items() for k in ks}
    for i, k in enumerate(kinds):
        lut[i] = -1 if k in ('sea', 'surf') else k2c.get(k, cid['meadow'])
    cgx = lut[K]; cgx[~land] = -1
    cgx[NY:, :W] = cg
    rgbx = np.zeros(land.shape + (3,), np.float32)
    ok = cgx >= 0
    rgbx[ok] = cols[cgx[ok]]
    nz = ndi.gaussian_filter(np.random.default_rng(5).standard_normal(land.shape).astype(np.float32), 6) * 6
    rgbx[ok] *= (1 + 0.012 * nz[ok])[:, None]
    rgbx[land] = rgbx[land] * 0.88 + np.array(R['plaster'][2], np.float32) * 0.12
    rgbx[NY:, :W] = rgb
    seax = sea_new(Sx).astype(np.float32)
    seax[NY:, :W] = sea_rgb
    return Sx, cgx, rgbx, seax


# ------------------------------------------------------------------------------------------ the range
_RANGE = {}

SPINE = [(0, 260), (900, 210), (1800, 120), (2600, 40), (3300, 140), (4100, 20), (4900, 150), (5600, 240), (6400, 120),
         (7200, -60), (7742, -180), (8300, -150), (9000, -250), (9800, -300), (10600, -280), (11400, -330), (12200, -300), (13568, -280)]
SPINE_HT = [(0, 0.92), (1200, 1.0), (2200, 0.86), (3400, 1.04), (4600, 1.0), (5400, 0.94), (6400, 0.9), (7200, 0.82),
            (7742, 0.46), (8200, 0.8), (8900, 0.72), (9800, 0.6), (10800, 0.52), (11800, 0.56), (12600, 0.54), (13568, 0.5)]
PASS_X = 7742


def range_field(Sx, rivers, closed, M=None):
    """The massif's height at each ext cell (0 the lowland, about 1 the highest peaks): a spine with peaks and saddles, a
    back range behind it, spurs on the interfluves stepping down to the foot, a col where the closed road crosses, valleys
    cut where the rivers and roads run, a basin round Highgarth."""
    key = id(Sx)
    if key in _RANGE:
        return _RANGE[key]
    Hc, Wc = Sx['K'].shape
    Wpx = Wc * CELL
    xs = np.arange(0, Wpx, 4.0)
    ys = np.interp(xs, *zip(*SPINE)) + fbm1(len(xs), [(160, 70), (50, 22), (14, 6)], 6601)
    ht = np.interp(xs, *zip(*SPINE_HT)) * (0.86 + 0.16 * fbm1(len(xs), [(120, 1.0), (40, 0.45)], 6602) ** 2)
    ht *= 1 - 0.42 * np.exp(-((xs - PASS_X) / 170) ** 2)                 # the col at the head of the Garth valley
    R0 = np.full((Hc, Wc), -1.0, np.float32)

    def burn(pts, hts):
        for (a, b), (ha, hb) in zip(zip(pts, pts[1:]), zip(hts, hts[1:])):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 4))
            t = np.linspace(0, 1, n + 1)
            r = ((a[1] + (b[1] - a[1]) * t) / CELL + NY).astype(int); c = ((a[0] + (b[0] - a[0]) * t) / CELL).astype(int)
            v = ha + (hb - ha) * t
            ok = (r >= 0) & (r < Hc) & (c >= 0) & (c < Wc)
            np.maximum.at(R0, (r[ok], c[ok]), v[ok].astype(np.float32))
    burn(list(zip(xs, ys)), list(ht))
    # the back range: higher and whiter, mostly in the cloud
    yb = ys - 300 + fbm1(len(xs), [(90, 60), (30, 18)], 6603)
    hb = ht * 1.12 + 0.04
    hb *= 1 - 0.35 * np.exp(-((xs - PASS_X) / 150) ** 2)
    burn(list(zip(xs, yb)), list(hb))
    # the snowfields between them: a high plateau falling gently from the back range to the spine (west of the forests)
    rows = (np.arange(Hc) - NY) * CELL
    xc = np.arange(Wc) * CELL + 4
    ysc = ndi.gaussian_filter1d(np.interp(xc, xs, ys), 6); ybc = ndi.gaussian_filter1d(np.interp(xc, xs, yb), 6)
    htc = ndi.gaussian_filter1d(np.interp(xc, xs, ht), 10); hbc = ndi.gaussian_filter1d(np.interp(xc, xs, hb), 10)
    t = np.clip((rows[:, None] - ybc[None, :]) / np.maximum(ysc - ybc, 40)[None, :], 0, 1)
    inside = (rows[:, None] > ybc[None, :]) & (rows[:, None] < ysc[None, :]) & (xc[None, :] < 9600)
    plat = np.minimum(hbc, htc)[None, :] * (0.86 - 0.03 * np.sin(t * np.pi))           # a snowfield basin under both crests
    plat *= np.clip((9600 - xc) / 600, 0, 1)[None, :]
    wgt = ndi.gaussian_filter(inside.astype(np.float32), 5)
    plat = ndi.gaussian_filter(np.where(inside, plat, 0).astype(np.float32), 5) / np.maximum(wgt, 1e-3)
    R0 = np.where(inside & (wgt > 0.3), np.maximum(R0, plat.astype(np.float32)), R0)
    # keep-clear: towns (a basin), roads and rivers (valleys)
    clear = np.zeros((Hc, Wc), bool)
    lines = [p for p in Sx['route_px'].values()] + list(rivers.values()) + [closed]
    for pts in lines:
        r, c = to_cells(pts, Hc, Wc); clear[r, c] = True
    d_line = ndi.distance_transform_edt(~clear) * CELL
    town = np.zeros((Hc, Wc), bool)
    for nm, t in Sx['towns'].items():
        if t.get('footprint_box'):
            x0, y0, x1, y1 = t['footprint_box']
            town[max(0, int(y0 // CELL) + NY):int(y1 // CELL) + NY + 1, max(0, int(x0 // CELL)):int(x1 // CELL) + 1] = True
    d_town = ndi.distance_transform_edt(~town) * CELL
    water = np.isin(Sx['K'], [i for i, k in enumerate(Sx['kinds']) if k in ('tarn', 'mere', 'lake', 'pool')]) & Sx['land']
    d_water = ndi.distance_transform_edt(~water) * CELL
    # the foot: where the world's range ends (h below 0.5), smoothed along x
    h = ndi.gaussian_filter(Sx['h'], 4)
    foot = np.full(Wc, 320.0)
    for c in range(Wc):
        col = h[NY:NY + 260, c]; b = np.flatnonzero(col < 0.5)
        foot[c] = (b[0] * CELL) if len(b) else 2000
    foot = ndi.uniform_filter1d(ndi.minimum_filter1d(foot, 9), 41)
    foot = np.clip(foot, 260, 1500)
    rng = np.random.default_rng(6604)
    x = 160.0
    spurs = 0
    while x < Wpx - 80:
        x += rng.uniform(150, 330)
        if abs(x - PASS_X) < 230:
            continue
        i = int(x / 4)
        if i >= len(xs):
            break
        y0, h0 = ys[i], ht[i]
        c0 = int(x / CELL)
        target = y0 + (foot[min(c0, Wc - 1)] - y0) * rng.choice([rng.uniform(0.3, 0.55), rng.uniform(0.82, 1.0)], p=[0.45, 0.55])
        L = max(160.0, target - y0)
        th = math.radians(90 + rng.uniform(-40, 40))
        pts = [(x, y0)]; hs = [h0]
        px_, py_ = x, y0; steps = int(L / 16)
        branch_at = rng.uniform(0.25, 0.6) if rng.random() < 0.9 else 2.0
        for st in range(1, steps + 1):
            th += math.radians(rng.normal(0, 7))
            th = min(max(th, math.radians(35)), math.radians(145))
            px_ += 16 * math.cos(th); py_ += 16 * math.sin(th)
            rr, cc = int(py_ / CELL + NY), int(px_ / CELL)
            if not (0 <= rr < Hc and 0 <= cc < Wc) or d_line[rr, cc] < 150 or d_town[rr, cc] < 200 or d_water[rr, cc] < 90:
                break
            t = st / steps
            bump = 0.07 * math.sin(t * math.pi * rng.uniform(2, 3.4))
            pts.append((px_, py_)); hs.append(h0 * (1 - 0.72 * t ** 0.85) + bump * h0)
            if abs(t - branch_at) < 1 / steps or (branch_at < 1 and abs(t - branch_at - 0.25) < 1 / steps and rng.random() < 0.5):
                bt = th + math.radians(rng.choice([-1, 1]) * rng.uniform(38, 58))
                bx, by = px_, py_; bpts = [(bx, by)]; bhs = [hs[-1]]
                nb = int(steps * rng.uniform(0.3, 0.45))
                for j in range(1, nb + 1):
                    bx += 16 * math.cos(bt); by += 16 * math.sin(bt)
                    r2, c2 = int(by / CELL + NY), int(bx / CELL)
                    if not (0 <= r2 < Hc and 0 <= c2 < Wc) or d_line[r2, c2] < 150 or d_town[r2, c2] < 200:
                        break
                    bpts.append((bx, by)); bhs.append(bhs[0] * (1 - 0.8 * j / nb))
                if len(bpts) > 2:
                    burn(bpts, bhs)
        if len(pts) > 2:
            burn(pts, hs); spurs += 1
        # a short spur north to the back range, so cirques open between them
        if rng.random() < 0.55:
            yb0 = yb[i]
            dx_ = rng.choice([-1, 1]) * rng.uniform(90, 200)
            burn([(x, y0), (x + dx_ * 0.45 + rng.uniform(-30, 30), (y0 + yb0) / 2), (x + dx_, yb0)], [h0 * 0.97, h0 * 0.86, hb[min(len(hb) - 1, int((x + dx_) / 4))] * 0.97])
    # the cone: every cell takes the highest ridge height less a fall with (Euclidean) distance, by height levels
    s1 = 0.0125                                                    # height per cell of distance: faces of about 30 degrees
    Hm = np.zeros((Hc, Wc), np.float32)
    for L in np.linspace(0.02, float(R0.max()), 96):
        m = R0 >= L
        if not m.any():
            continue
        Hm = np.maximum(Hm, (L - s1 * ndi.distance_transform_edt(~m)).astype(np.float32))
    Hm = np.clip(Hm, 0, None)
    # valleys and the basin
    Hm *= 1 - 0.78 * np.exp(-(d_line / 120) ** 2)
    Hm *= np.clip(d_town / 260, 0.15, 1) ** 0.8
    Hm *= np.clip(d_water / 70, 0.1, 1)
    # the massif fades out where the world's own ground is low (the lowland, the Frostline's floor)
    hw = ndi.gaussian_filter(Sx['h'], 9)                         # smooth: the world's heights carry straight seams at the top
    t = ((NY - np.arange(NY)) / NY)[:, None]
    hw[:NY] = np.maximum(hw[:NY], hw[NY][None, :] + (0.85 - hw[NY][None, :]) * t)
    Hm *= np.clip((hw - 0.36) / 0.22, 0, 1)
    out = dict(H=Hm.astype(np.float32), Hs=ndi.gaussian_filter(Hm, 1.5).astype(np.float32), spurs=spurs,
               plat=ndi.gaussian_filter((inside & (wgt > 0.3)).astype(np.float32), 2.0), spine=(xs, ys, ht), back=(xs, yb, hb), d_line=d_line, d_town=d_town)
    _RANGE[key] = out
    return out


# ------------------------------------------------------------------------------------------ drawing the relief
def _shade(Hp, k, exag):
    gy, gx = np.gradient(Hp.astype(np.float32))
    gx *= k; gy *= k                                             # per world px (k: image px per world px)
    nx, ny = -exag * gx, -exag * gy
    L = np.array([-0.6, -0.5, 0.62]); L = L / np.linalg.norm(L)
    return (nx * L[0] + ny * L[1] + L[2]) / np.sqrt(nx * nx + ny * ny + 1)


def relief(img, Sx, R, ink, k, rivers, closed, cgx=None, cid=None, ox=0.0, oy=0.0, band=384):
    """The massif and the fire country's hills on the base image (the ext frame at k px per world px, world x 0 at ox and
    ext row 0 at oy): four light values from the upper left, stone in warm light and cool shade, snow above a snowline
    that rises to the east and dips on north faces, a crest line in the face's own dark, the volcanic hills in basalt.
    Drawn a band of rows at a time (with a few rows of overlap for the slopes), all in float32."""
    F = range_field(Sx, rivers, closed)
    arr_all = np.asarray(img)
    Hi, Wi = arr_all.shape[:2]
    out_all = arr_all.copy()
    sc = k * 150
    N1 = Noise2((Hi, Wi), max(3.0, sc), 7101); N2 = Noise2((Hi, Wi), max(2.0, sc * 0.35), 7102)
    NB = Noise2((Hi, Wi), max(4.0, k * 260), 7103); NC = Noise2((Hi, Wi), max(3.0, k * 110), 7104)   # snowfield swells, crevasses
    salt_cells = None
    if cgx is not None and cid is not None and 'salt' in cid:
        salt_cells = ndi.gaussian_filter((cgx == cid['salt']).astype(np.float32), 1.3)
        salt_d = ndi.distance_transform_edt(salt_cells > 0.5).astype(np.float32)    # cells in from the shore
    px = ((np.arange(Wi, dtype=np.float32) - ox) / k / CELL - 0.5).astype(np.float32)
    Xw1 = (px + 0.5) * CELL
    east1 = np.clip((Xw1 - 8800) / 2400, 0, 1).astype(np.float32)
    st = R['stone']; sw = R['stone_warm']; sc_ = R['slate']; sn = R['snow']; snc = R['snow_cool']
    rock_c = np.array([sc_[2], st[2], st[3], sw[4]], np.float32)
    snow_c = np.array([snc[1], snc[2], sn[4], sn[5]], np.float32)       # blue-grey shade side, white lit face
    scree_c = np.array([sc_[2], sw[2], sw[3], sw[4]], np.float32)
    fac = np.array([0.8, 0.9, 1.0, 1.08], np.float32)
    sw5 = R['snow_warm']; sa = R['sand']; saw = R['sand_warm']
    rk_cells = None
    if cgx is not None and cid is not None:
        rk_cells = np.isin(cgx, [cid[n] for n in ('rock', 'crag') if n in cid]).astype(np.float32)
    vol = volcanic_mask(Sx)
    hv = ndi.gaussian_filter(Sx['h'], 0.8).astype(np.float32) if vol is not None else None
    ba = R['basalt']; bw = R['basalt_warm']
    bas = np.array([ba[1], ba[2], bw[3], bw[4]], np.float32)
    PAD = 3
    for r0 in range(0, Hi, band):
        r1 = min(Hi, r0 + band); a0 = max(0, r0 - PAD); a1 = min(Hi, r1 + PAD)
        arr = arr_all[a0:a1].astype(np.float32)
        py = ((np.arange(a0, a1, dtype=np.float32) - oy) / k / CELL - 0.5).astype(np.float32)
        Y, X = np.meshgrid(py, px, indexing='ij')
        Hp = ndi.map_coordinates(F['Hs'], [Y, X], order=3, mode='nearest', output=np.float32)
        Yw = (Y + 0.5) * CELL - DY
        n1 = N1.rows(a0, a1); n2 = N2.rows(a0, a1)
        rid = 1 - np.abs(n1 * 0.7 + n2 * 0.3)
        plat = ndi.map_coordinates(F['plat'], [Y, X], order=1, mode='nearest', output=np.float32)
        nb = NB.rows(a0, a1)
        Hp = Hp + 0.026 * (rid - 0.6) * np.clip(Hp / 0.4, 0, 1) + 0.05 * nb * plat   # gullies; swells on the snowfields
        lv = np.digitize(_shade(Hp, k, 380), [0.2, 0.36, 0.78]).astype(np.int8)   # 0 deep shade .. 3 full light: lit north-west
        east = east1[None, :]
        snowline = 0.8 + 0.35 * east + 0.05 * n2 - 0.05 * (lv <= 1)              # snow on the high peaks and crests
        rock = Hp > 0.17 + 0.26 * east + 0.02 * n1
        if rk_cells is not None:                                  # the world's own rock and crag take the stone too
            rk = ndi.map_coordinates(rk_cells, [Y, X], order=0, mode='nearest', output=np.float32) > 0.5
            rock |= rk & (Hp > 0.04) & (Yw < 1400)
        field = rock & (plat > 0.55) & (Hp > 0.6 + 0.08 * n1)                 # the back range's snowfields
        snow = rock & ((Hp > snowline) | field)
        foot = (Hp > 0.05) & ~rock
        out = arr.copy()
        m = rock & ~snow
        out[m] = rock_c[lv[m]]
        sq = m & (Hp < 0.42) & (n2 > 0.25)                                  # scree on the lower slopes
        out[sq] = scree_c[lv[sq]]
        out[snow] = snow_c[lv[snow]]
        nc = NC.rows(a0, a1)                                                # crevasse lines across the snowfields
        crev = field & snow & (np.abs(np.sin(nc * 9.0)) < 0.09) & (n1 > -0.1) & (lv >= 2)
        out[crev] = np.array(snc[2], np.float32)
        out[foot] = np.clip(arr[foot] * fac[lv[foot]][:, None], 0, 255)   # foothills and forested ridges: the ground's own colour
        crest = np.zeros_like(rock)                                # where full light meets shade across a ridge: the shade's dark
        crest[:, 1:] = (lv[:, :-1] >= 2) & (lv[:, 1:] <= 1) & rock[:, 1:]
        crest[1:, :] |= (lv[:-1, :] >= 2) & (lv[1:, :] == 0) & rock[1:, :]
        cs = crest & snow; cr = crest & ~snow
        ink_ = np.array(ink, np.float32) * 0.15
        out[cs] = np.array(snc[0], np.float32) * 0.85 + ink_
        out[cr] = np.array(sc_[0], np.float32) * 0.85 + ink_
        rfoot = np.zeros_like(rock); rfoot[1:] = rock[:-1] & ~rock[1:] & (lv[:-1] <= 2)   # the rock's foot: a dark row
        out[rfoot] = out[rfoot] * 0.72
        if vol is not None:                                       # the fire country: its own heights in basalt, no snow
            Vm = ndi.map_coordinates(vol.astype(np.float32), [Y, X], order=1, mode='nearest', output=np.float32) > 0.5
            if Vm.any():
                Hv = ndi.map_coordinates(hv, [Y, X], order=1, mode='nearest', output=np.float32) + 0.012 * (rid - 0.6)
                lvv = np.digitize(_shade(Hv, k, 900), [0.25, 0.5, 0.74]).astype(np.int8)
                rockv = Vm & (ndi.map_coordinates(Sx['vol_rock'].astype(np.float32), [Y, X], order=0, mode='nearest', output=np.float32) > 0.5)
                out[rockv] = bas[lvv[rockv]]
                rest = Vm & ~rockv
                out[rest] = np.clip(arr[rest] * np.array([0.72, 0.86, 1.0, 1.08], np.float32)[lvv[rest]][:, None], 0, 255)
        if salt_cells is not None:                                # the salt lake: a clean shore and crust rings
            sm = ndi.map_coordinates(salt_cells, [Y, X], order=1, mode='nearest', output=np.float32)
            if (sm > 0.2).any():
                inside = sm > 0.5
                ring = ndi.map_coordinates(salt_d, [Y, X], order=1, mode='nearest', output=np.float32)
                out[inside] = out[inside] * 0.3 + np.array(sw5[5], np.float32) * 0.7          # calm white crust, cracks faint
                out[inside & (ring < 0.9)] = np.array(saw[4], np.float32)                    # the damp margin
                out[inside & (ring >= 1.5) & (ring < 2.0)] = np.array(sw5[3], np.float32)    # the first crust ring
                out[inside & (ring >= 3.6) & (ring < 4.0)] = np.array(sw5[3], np.float32)    # an inner ring
                shore = (sm > 0.38) & ~inside
                out[shore] = np.array(sa[2], np.float32)                                     # the shoreline
        out_all[r0:r1] = np.clip(out[r0 - a0:r0 - a0 + (r1 - r0)], 0, 255).astype(np.uint8)
    return Image.fromarray(out_all), None


VOLCANIC = ('ash', 'aa', 'basalt', 'lavastone', 'blacksand', 'talus', 'scree2', 'boulders', 'crater', 'fireweed', 'spoil')
VOL_ROCK = ('aa', 'basalt', 'talus', 'scree2', 'boulders', 'spoil')


def volcanic_mask(Sx):
    if 'vol_mask' in Sx:
        return Sx['vol_mask']
    kinds = Sx['kinds']; K = Sx['K']
    Hc, Wc = K.shape
    v = np.isin(K, [i for i, k in enumerate(kinds) if k in VOLCANIC])
    rows = (np.arange(Hc) - NY) * CELL; cols = np.arange(Wc) * CELL
    zone = (rows[:, None] > 3500) & (cols[None, :] < 4600)
    v &= zone
    v = ndi.binary_closing(v, iterations=2) & Sx['land'] & zone
    v = ndi.binary_opening(v, iterations=1)
    Sx['vol_mask'] = v
    vr = v & np.isin(K, [i for i, k in enumerate(kinds) if k in VOL_ROCK])
    Sx['vol_rock'] = (ndi.gaussian_filter(vr.astype(np.float32), 2.2) > 0.42) & v   # the flows as lobes, not speckle
    return v


def range_classes(Sx, cgx, cid, rivers, closed):
    """The class grid with the massif's rock and snow cells set to rock and snow, so no tree or tuft is stamped on them."""
    F = range_field(Sx, rivers, closed)
    Hm = F['H']
    Wc = Hm.shape[1]
    east = np.clip((np.arange(Wc) * CELL - 8800) / 2400, 0, 1)[None, :]
    cg = cgx.copy()
    rock = Sx['land'] & (Hm > 0.19 + 0.26 * east)
    snow = rock & (Hm > 0.66 + 0.4 * east)
    keep = np.isin(cg, [cid[n] for n in ('water',) if n in cid]) | (cg < 0)
    cg[rock & ~keep] = cid['rock']
    cg[snow & ~keep] = cid['snow']
    return cg


def overview_classes(Sx, cg, cid):
    """Overview drawing only (no cell of the world changes kind): the fire country's speckle of ash, aa, blacksand and
    scree generalised into fields and flows (a majority over 5 x 5 cells), and the straight strip of conifers along the old
    east edge (the world's wall) broken into irregular stands mixed with the old forest, so it does not read as a wall."""
    cg = cg.copy()
    Hc, Wc = cg.shape
    rows = (np.arange(Hc) - NY)[:, None] * CELL; cols = np.arange(Wc)[None, :] * CELL
    ids = [cid[n] for n in ('ash', 'lavastone', 'basalt', 'blacksand', 'rock', 'desert', 'erg', 'salt', 'scrub', 'badland') if n in cid]
    zone = (rows > 3300) & (cols < 4600) & np.isin(cg, ids)
    votes = np.stack([ndi.uniform_filter((cg == i).astype(np.float32), 5) for i in ids])
    best = np.array(ids, np.int16)[np.argmax(votes, axis=0)]
    cg = np.where(zone & (votes.max(axis=0) > 0.3), best, cg)
    fo = [cid[n] for n in ('conifer', 'oldforest') if n in cid]
    if len(fo) == 2:
        nz = ndi.gaussian_filter(np.random.default_rng(5614).standard_normal((Hc, Wc)).astype(np.float32), 4)
        nz /= nz.std() + 1e-6
        near = (np.abs(cols - 12480) + 90 * nz < 300) & np.isin(cg, fo) & (rows < 4300)
        cg = np.where(near, np.where(nz > 0.15, fo[0], fo[1]), cg)
    return cg


# ------------------------------------------------------------------------------------------ the edges
def _bayer(h, w):
    b = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 + 1 / 32
    return np.tile(b, (h // 4 + 1, w // 4 + 1))[:h, :w]


def edge_frame(canvas, Sx, R, s, k, ox, oy, isles_clear=True, band=320):
    """The four edges as weather: the north's peaks rise into a cloud bank; the west's dune sea thins into dust haze; the
    east's fens and old forest into marsh mist, and the sea beyond Neon into sea fog; the south's open sea into a low sea fog
    with far islands, the Tidebloom Isles left clear. Alpha comes in four steps with an ordered dither between them (a fade
    of light, not a boundary). (ox, oy): where the frame's world x 0 and ext row 0 fall on the canvas. Drawn a band of rows
    at a time. Returns the canvas and the cover (0 to 0.94) at every pixel."""
    Wc, Hc = canvas.size
    arr_all = np.asarray(canvas.convert('RGB'))
    out_all = arr_all.copy()
    Aq_all = np.zeros((Hc, Wc), np.float32)
    landx = Sx['land']; Hl, Wl = landx.shape

    def cell_of(px, py):
        cx = np.clip(((px - ox) / k / CELL).astype(int), 0, Wl - 1); cy = np.clip(((py - oy) / k / CELL).astype(int), 0, Hl - 1)
        return cy, cx
    # per-side depth in canvas px, wobbling along the edge
    dN = 34 * s + fbm1(Wc, [(150 * s, 12 * s), (46 * s, 7 * s), (15 * s, 2.5 * s)], 911)
    dS = 20 * s + fbm1(Wc, [(170 * s, 7 * s), (50 * s, 4 * s)], 914)
    dW = 44 * s + fbm1(Hc, [(140 * s, 12 * s), (40 * s, 6 * s)], 912)
    dE = 40 * s + fbm1(Hc, [(130 * s, 16 * s), (40 * s, 8 * s), (14 * s, 2.5 * s)], 913)
    # which kind of ground meets each side edge, row by row
    cyW, _ = cell_of(np.zeros(Hc) + ox + 2, np.arange(Hc)); cyE, cxE = cell_of(np.zeros(Hc) + Wc - 3, np.arange(Hc))
    landW = ndi.gaussian_filter1d(landx[cyW, 0].astype(np.float32), 26 * s)
    landE = ndi.gaussian_filter1d(landx[cyE, cxE].astype(np.float32), 26 * s)
    dl = (ndi.distance_transform_edt(~landx) * CELL * k).astype(np.float32) if isles_clear else None

    def ramp(d, depth, soft):
        return np.clip((depth - d) / soft + 1, 0, 1) ** 1.3
    T1 = Noise2((Hc, Wc), 36 * s, 915); ST = Noise2((max(1, Hc // 3), Wc), 30 * s, 917)   # fewer, larger, softer forms
    # the north cloud bank: a front row of puffs whose lower scallops make a clear line where the range ends and cloud begins
    rngp = np.random.default_rng(918)
    puffs = []; x_ = -10.0 * s
    while x_ < Wc + 20 * s:
        r_ = rngp.uniform(9, 17) * s
        cxp = x_ + r_ * 0.8
        puffs.append((cxp, float(dN[int(min(max(cxp, 0), Wc - 1))]) - r_ * 0.3, r_))
        x_ += rngp.uniform(1.0, 1.5) * r_
    e = np.full(Wc, -1e9, np.float32); fi = np.zeros(Wc, int)
    for i, (cxp, cyp, r_) in enumerate(puffs):
        xs_ = np.arange(max(0, int(cxp - r_)), min(Wc, int(cxp + r_) + 1))
        if len(xs_) == 0:
            continue
        bot = cyp + np.sqrt(np.clip(r_ * r_ - (xs_ - cxp) ** 2, 0, None))
        upd = bot > e[xs_]
        e[xs_[upd]] = bot[upd]; fi[xs_[upd]] = i
    pcx = np.array([puffs[i][0] for i in fi], np.float32); pcy = np.array([puffs[i][1] for i in fi], np.float32)
    prr = np.array([puffs[i][2] for i in fi], np.float32)
    warm = np.array(R['snow'][5], np.float32) * 0.5 + np.array(R['sand_warm'][5], np.float32) * 0.5
    lit_c = np.minimum(warm + 8, 255); under_c = warm * 0.65 + np.array(R['sand_warm'][3], np.float32) * 0.35
    rim_c = np.array(R['sand_warm'][2], np.float32) * 0.55 + np.array(R['snow'][2], np.float32) * 0.45
    colN = np.array(R['snow'][4], np.float32)
    dust = np.array(R['sand'][5], np.float32) * 0.6 + np.array(R['sand_warm'][4], np.float32) * 0.4
    mist = np.array(R['snow'][3], np.float32) * 0.62 + np.array(R['grass_cool'][4], np.float32) * 0.38
    seafog = np.array(R['snow'][4], np.float32) * 0.7 + np.array(R['water'][5], np.float32) * 0.3
    steps = np.array([0.0, 0.3, 0.55, 0.78, 0.94], np.float32)
    bay = _bayer(Hc, Wc)
    xx1 = np.arange(Wc, dtype=np.float32)
    PAD = int(12 * s) + 4
    for r0 in range(0, Hc, band):
        r1 = min(Hc, r0 + band); a0 = max(0, r0 - PAD); a1 = min(Hc, r1 + PAD); n = a1 - a0
        yy = np.arange(a0, a1, dtype=np.float32)[:, None]; xx = xx1[None, :]
        aN = np.zeros((n, Wc), np.float32)
        aS = ramp(Hc - 1 - yy, dS[None, :], 20 * s)
        aW = ramp(xx, dW[a0:a1, None], 30 * s)
        aE = ramp(Wc - 1 - xx, dE[a0:a1, None], 42 * s)
        if dl is not None:                                        # no fog over land in the south: the isles stay clear
            cy, cx = cell_of(np.broadcast_to(xx, (n, Wc)), np.broadcast_to(yy, (n, Wc)))
            aS = aS * np.clip((dl[cy, cx] - 10 * s) / (26 * s), 0, 1)
        tex = T1.rows(a0, a1)
        q0, q1 = a0 // 3, a1 // 3 + 1
        streak = np.repeat(ST.rows(q0, q1), 3, 0)[a0 - q0 * 3:a0 - q0 * 3 + n]   # wind-laid streaks in the dust
        aW_ = np.clip(aW * (0.85 + 0.25 * streak), 0, 1)
        lw = landW[a0:a1, None, None]; le = landE[a0:a1, None, None]
        cW = lw * dust + (1 - lw) * seafog; cE = le * mist + (1 - le) * seafog
        stack = [(aN, colN[None, None, :]), (aS * (0.8 + 0.3 * tex), seafog[None, None, :]), (aW_, cW),
                 (aE * (0.8 + 0.3 * tex), cE)]
        A = np.zeros((n, Wc), np.float32); Csum = np.zeros((n, Wc, 3), np.float32); wsum = np.zeros((n, Wc), np.float32)
        for a, c in stack:
            a = np.clip(a, 0, 1).astype(np.float32)
            A = 1 - (1 - A) * (1 - a)
            Csum += a[..., None] * c; wsum += a
        Cm = Csum / np.maximum(wsum, 1e-4)[..., None]
        del Csum
        Cm *= (1 + 0.035 * tex)[..., None]                          # a broad, soft lightening on the fog's thick parts
        qd = A * 4
        lo = np.clip(np.floor(qd).astype(np.int8), 0, 4); fr = qd - lo; hi = np.clip(lo + 1, 0, 4)
        Aq = np.where(fr > bay[a0:a1], steps[hi], steps[lo]).astype(np.float32)
        out = arr_all[a0:a1].astype(np.float32) * (1 - Aq[..., None]) + Cm * Aq[..., None]
        del Cm
        # the north cloud's body: warm white puffs, lit on their upper left, shaded underneath, a rim along the scallops and
        # a cast shadow on the peaks below
        E = e[None, :]
        bank = yy < E
        dxp = (xx - pcx[None, :]) / prr[None, :]; dyp = (yy - pcy[None, :]) / prr[None, :]
        inp = dxp * dxp + dyp * dyp <= 1.0
        fill = np.broadcast_to(warm, (n, Wc, 3)).copy()
        litm = bank & inp & (dxp * 0.6 + dyp * 0.8 < -0.45)
        fill[litm] = lit_c
        und = bank & inp & (dyp > 0.62)
        fill[und] = under_c
        top = bank & ~inp & (yy > E - 26 * s) & (np.abs(yy - (pcy[None, :] - np.sqrt(np.clip(1 - dxp * dxp, 0, 1)) * prr[None, :])) < 0.8 * s)
        fill[top] = lit_c                                           # the front puff's lit top edge against the bank behind
        rim = bank & (yy > E - 1.2 * s)
        fill[rim] = rim_c
        out[bank] = fill[bank]
        sh1 = ~bank & (yy < E + 2.5 * s); sh2 = ~bank & ~sh1 & (yy < E + 5 * s)
        out[sh1] = out[sh1] * 0.7; out[sh2] = out[sh2] * 0.85
        Aq = np.where(bank, 1.0, Aq).astype(np.float32)
        k0 = r0 - a0
        out_all[r0:r1] = np.clip(out[k0:k0 + (r1 - r0)], 0, 255).astype(np.uint8)
        Aq_all[r0:r1] = Aq[k0:k0 + (r1 - r0)]
    return Image.fromarray(out_all), Aq_all


def far_islands(d, R, s, Wc, Hc, seed=31):
    """Far islands on the southern horizon, in the fog: flat pale shapes, bluer with distance."""
    rng = np.random.default_rng(seed)
    col = tuple(int(v) for v in (np.array(R['water'][5], np.float32) * 0.55 + np.array(R['snow'][3], np.float32) * 0.45))
    for X in (0.14, 0.33, 0.52, 0.71, 0.86):
        X = X * Wc + rng.uniform(-30, 30) * s; Y = Hc - 11 * s - rng.uniform(0, 3) * s; w = rng.uniform(26, 60) * s; ht = rng.uniform(3, 5.5) * s
        n = 9
        pts = [(X - w / 2 + w * i / n, Y - ht * math.sin(math.pi * i / n) ** 0.6 * (0.8 + 0.4 * rng.random())) for i in range(n + 1)]
        d.polygon(pts + [(X + w / 2, Y + 1.5 * s), (X - w / 2, Y + 1.5 * s)], fill=col + (120,))


def haze_audit(Aq, S, M, k, ox, oy, lines, rivers, closed, limit=0.3):
    """What the haze covers: every town, road, rail and ferry point, and the river heads, with the cover at its pixel.
    Returns the items covered above `limit` (the run-offs that should vanish into it are listed apart)."""
    Hc, Wc = Aq.shape
    P = lambda x, y: (x * k + ox, y * k + oy)

    def cover(pts):
        m = 0.0
        for x, y in pts:
            X, Y = P(x, y)
            if 0 <= X < Wc and 0 <= Y < Hc:
                m = max(m, float(Aq[int(Y), int(X)]))
        return m
    bad = []
    for nm, t in S['towns'].items():
        if t.get('footprint_box'):
            x0, y0, x1, y1 = t['footprint_box']
            c = cover([(x0, y0), (x1, y0), (x0, y1), (x1, y1), ((x0 + x1) / 2, (y0 + y1) / 2)])
            if c > limit:
                bad.append(('town', nm, round(c, 2)))
    for nm, pts in S['route_px'].items():
        c = cover(pts)
        if c > limit:
            bad.append(('route', nm, round(c, 2)))
    for nm, kind, pts, way in lines:
        c = cover(pts)
        if c > limit:
            bad.append((kind, nm, round(c, 2)))
    runoff = {'closed pass road': round(cover(closed[-3:]), 2)}
    return bad, runoff
