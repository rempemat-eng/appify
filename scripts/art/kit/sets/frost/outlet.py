"""The Frostline's open outlet drawn as one surface (Matt, 23 Nov: the tarn frozen, its outlet open,
thawing water; a short thaw band at the woodland's north seam), after the round 1 audits of #535.

The kit's live water is drawn cell by cell in the woodland's summer ramp: its banks scallop once a
cell and its colour is the brook's. The outlet is therefore painted here from the zone's own plan
(game/kit/zones/frostline.json) as a ground dressing laid over the water cells, which stay as they
are (walkability is the cells'):

- the water: a calm winter body (slate, L about 0.36 to 0.40, C about 0.05 to 0.06) with depth bands
  that follow the flow (contours of the distance to the bank), a darker thalweg, lit shallows, a dark
  band stepping back under every north bank, paired glints along the flow; it climbs to the
  woodland brook's own ramp over the last two cells before the seam;
- the banks: a soft-grid line that wanders off the cells (straight runs, bays and points of
  different sizes); a north bank shows its face (snow lip, shaded undercut, wet rock, a light
  waterline), every other shore only its rim (eastward-edges 5.3a, 5.3c: the shore is the land's own
  snow and rock);
- the outlet's mouth: the tarn's one lead, jagged and narrowing northward, fanning into the pool,
  the ice's cut face on its far edges; the pool narrowing to the sheet's width over its last rows;
- shelf ice fast to the banks near the tarn, thinning downstream, and a few floes, each with a wet
  contact.

The ground under the overlay's land texels is the kit's own render (scripts/art/kit/compose.py, the
renderer the Godot fixtures pin) of the plan with the outlet's cells given to the land beside them,
so the land it repaints near the banks is the ground the zone shows.

`inflow` treats the frozen rill coming into the tarn the same way, and `thaw_band` lays the thaw
across the zone's last three rows, its rivulets running to this water's edge.
"""
from __future__ import annotations

from functools import lru_cache

from ._shared import C, FACE_PX, K, LIP_PX, ROOT, V, hsh, json, math, ndi, np, os

ZONE = os.path.join(ROOT, 'game', 'kit', 'zones', 'frostline.json')
CELL = 24
MARGIN = 16                        # texels past the water cells the overlay may repaint (the live edges reach 12)
OUTLET_TOP = 13                    # the outlet's first water row; above it the tarn
LEAD_TOP = 10                      # the lead starts on the tarn's ice this many rows down

# the water's tones by role, in three ramps: the winter outlet, a step toward the woodland, the brook's
RAMPS = {
    'winter': dict(deep=C('slate_cool', 1), body=C('slate_warm', 1), mid=C('slate_cool', 2), shallow=C('slate', 2),
                   band0=C('slate_cool', 0), band1=C('slate', 0), band2=C('slate_cool', 1), glint=C('slate', 3)),
    'mid': dict(deep=C('water_cool', 1), body=C('sky_cool', 1), mid=C('sky_cool', 2), shallow=C('sky_cool', 2),
                band0=C('water_cool', 0), band1=C('slate', 0), band2=C('water_cool', 1), glint=C('sky_cool', 3)),
    'wood': dict(deep=C('water', 1), body=C('water', 2), mid=C('water', 2), shallow=C('water', 3),
                 band0=C('water', 0), band1=C('water_cool', 0), band2=C('water', 1), glint=C('water', 4)),
}
RIM = C('slate_cool', 1)          # a texel of wet rock at the land's edge
WATERLINE = C('snow_cool', 3)     # the light line under a north bank, in the snow's cool tones



@lru_cache(maxsize=None)
def _plan_text():
    with open(ZONE) as f:
        return f.read()



def _plan():
    return json.loads(_plan_text())



def _grid(plan):
    return np.array([list(r) for r in plan['rows']])



def _water_cells(g):
    """The outlet's cells: open water from its mouth down (the ice-cutter's hole is the tarn's)."""
    w = g == 'a'
    w[:OUTLET_TOP] = False
    return w



def _fall(plan):
    """The fall piece's picture box in world texels: (x0, y0) of the picture, its lip row and the
    sheet's columns (water_ice.SHEET_X), read from the plan's icefall piece."""
    from .water_ice import SHEET_X
    p = next(q for q in plan['pieces'] if q['piece'] == 'frost_icefall')
    ax, ay = 48, LIP_PX + FACE_PX - 1              # rock._face's foot: (W // 2, yf - 1), W = 96
    x0, y0 = int(p['at'][0]) - ax, int(p['at'][1]) - ay
    return x0, y0, y0 + LIP_PX, x0 + SHEET_X[0], x0 + SHEET_X[1]



@lru_cache(maxsize=None)
def _background_key(text):
    """The kit's render of the plan with the outlet's cells given to their land: the mouth's first
    row to the tarn's ice, the trod's crossing to the trod, the rest to snow."""
    import sys
    from scripts.art.kit.build import Kit
    from scripts.art.kit import compose
    plan = json.loads(text)
    g = _grid(plan)
    w = _water_cells(g)
    g2 = g.copy()
    for (r, c) in zip(*np.nonzero(w)):
        if r == OUTLET_TOP:
            g2[r, c] = 'i'
        elif 'b' in (g[r, c - 1], g[r, min(g.shape[1] - 1, c + 1)]) or 'b' in g[r, :c].tolist()[-3:]:
            g2[r, c] = 'b'
        else:
            g2[r, c] = '.'
    kit = Kit()
    legend = {s: kit.ids[n] for s, n in plan['legend'].items()}
    cells = np.array([[legend[ch] for ch in row] for row in g2], np.int32)
    del sys
    return compose.render(cells, kit, dressing=True), g2



def _noise(shape, sigma, seed):
    n = ndi.gaussian_filter(np.random.default_rng(seed).standard_normal(shape), sigma)
    return n / (n.std() + 1e-9)



@lru_cache(maxsize=None)
def _mask_key(text, seed=401):
    """The outlet's water (world texels): the cells' outline smoothed and set wandering on the soft
    grid, the lead cut into the tarn's ice above its mouth, the pool narrowed to the sheet's width
    over the last rows before the lip."""
    plan = json.loads(text)
    g = _grid(plan)
    H, W = g.shape[0] * CELL, g.shape[1] * CELL
    w = np.kron(_water_cells(g), np.ones((CELL, CELL), bool))
    sd = ndi.distance_transform_edt(w) - ndi.distance_transform_edt(~w)
    sd = ndi.gaussian_filter(sd, 5.0)
    # the wander: some runs straight (the amplitude low), bays and points of different sizes elsewhere
    amp = np.clip(0.75 * _noise((H, W), 46.0, seed) + 0.5, 0.2, 1.0)
    big = _noise((H, W), 26.0, seed + 1)
    small = _noise((H, W), 7.0, seed + 2)
    m = (sd + amp * (8.0 * big + 0.8 * small)) > 0
    # the line stays within 9 texels outside the water cells and 10 inside them (the walk grid's edge)
    m &= ndi.distance_transform_edt(~w) <= 9
    m |= ndi.distance_transform_edt(w) > 10
    m = ndi.binary_opening(m, iterations=2)
    # the mouth's north end rounded where it leaves the tarn's ice (radius 12)
    mouth = OUTLET_TOP * CELL
    for y in range(mouth - 2, mouth + 12):
        cols = np.nonzero(m[y])[0]
        if not len(cols):
            continue
        dy = y - (mouth - 2)
        cut = int(round(12 - math.sqrt(max(0.0, 144 - (12 - dy) ** 2))))
        m[y, cols.min():cols.min() + cut] = False
        m[y, cols.max() + 1 - cut:cols.max() + 1] = False
    # the pool's last rows before the lip: the sheet's width exactly (a glassy tongue), easing in
    _x0, _y0, lip, s0, s1 = _fall(plan)
    t0 = lip - 30
    rows = np.nonzero(m[t0])[0]
    if len(rows):
        l0, r0 = rows.min(), rows.max() + 1
        for y in range(t0, lip + 1):
            f = (y - t0) / 30.0
            f = f * f * (3 - 2 * f)
            lw = int(round(l0 + (s0 - l0) * f))
            rw = int(round(r0 + (s1 - r0) * f))
            m[y, :] = False
            m[y, lw:rw] = True
    # under the face nothing shows: keep the channel straight there
    m[lip + 1:_y0 + LIP_PX + 96, s0:s1] = True
    # the lead: down the tarn's ice from LEAD_TOP into the mouth, jagged, narrowing northward
    rng = np.random.default_rng(seed + 7)
    top, mouth = LEAD_TOP * CELL + 6, OUTLET_TOP * CELL
    cols = np.nonzero(m[mouth + 8])[0]
    cx0 = (cols.min() + cols.max()) / 2.0 if len(cols) else W / 2
    wid = 2.0
    for y in range(top, mouth + 10):
        f = (y - top) / float(mouth + 10 - top)
        if (y - top) % int(rng.integers(4, 9)) == 0:
            wid = 5.5 + 7.0 * f ** 1.3 + rng.uniform(-1.5, 1.5)
        if y > mouth - 10:                                  # fanning into the pool
            wid += 3.0
        cx = cx0 + 3.0 * math.sin(y / 9.0 + 1.3) + 1.5 * math.sin(y / 3.7)
        a, b = int(round(cx - wid / 2)), int(round(cx + wid / 2 + rng.uniform(-1, 1)))
        m[y, max(0, a):min(W, b)] = True
    return m



def water_mask(plan=None):
    return _mask_key(_plan_text() if plan is None else json.dumps(plan, sort_keys=True, indent=1))



def _flow_dir(dist):
    """The flow's direction per texel (unit vectors, pointing downstream): along the contours of the
    distance to the bank, turned to run southward."""
    d = ndi.gaussian_filter(dist, 3.0)
    gy, gx = np.gradient(d)
    ty, tx = gx, -gy
    flip = ty < 0
    ty, tx = np.where(flip, -ty, ty), np.where(flip, -tx, tx)
    n = np.hypot(ty, tx) + 1e-9
    return ty / n, tx / n



def _ramp_at(Y, X):
    """Which ramp a texel takes: winter, a step toward the brook from row 42, the brook's own over
    the last cell and a half (the boundaries wander with the water)."""
    y1 = 42 * CELL + 6 + 8 * np.sin(X / 31.0) + 4 * np.sin(X / 11.0 + 1.0)
    y2 = 43 * CELL + 16 + 7 * np.sin(X / 27.0 + 2.0) + 3 * np.sin(X / 9.0)
    return np.where(Y >= y2, 2, np.where(Y >= y1, 1, 0))



def _paint_water(out, m, landmat, H, W, seed):
    """Paint the outlet's water into `out` (world texels) where `m`: roles, then ramps."""
    Y, X = np.mgrid[0:H, 0:W]
    dist = ndi.distance_transform_edt(m)
    ds = ndi.gaussian_filter(dist, 1.2)
    hw = ndi.gaussian_filter(ndi.maximum_filter(dist, size=41), 8.0)
    rel = ds / np.maximum(hw, 1.0)
    role = np.full((H, W), 'body', object)
    deep = (rel > 0.72) & (hw >= 9)
    deep = ndi.binary_opening(deep, iterations=2)
    role[deep] = 'deep'
    role[(ds <= 2.6) & (K.vhash(X // 3, Y // 5, seed + 9) > 0.45)] = 'mid'
    role[ds <= 1.4] = 'shallow'
    # the run of water down from the land above, per column
    top = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H):
        run = np.where(m[y], run + 1, 0)
        top[y] = run
    # a north bank is a stretch where the water's first row lies level for 7 texels or more
    first = m & ~np.vstack([np.zeros((1, W), bool), m[:-1]])
    level = ndi.uniform_filter(first.astype(float), size=(1, 7)) > 0.99
    level = ndi.binary_dilation(level, structure=np.ones((1, 3), bool)) & first
    face_col = np.zeros((H, W), bool)
    face_col[level] = True
    # the face hangs from the level first row down: propagate per column for the first rows
    north = np.zeros((H, W), bool)
    for k in range(10):
        north |= np.roll(face_col, k, 0) & m & (top == k + 1)
    bd = np.clip(np.round(5.0 + 2.5 * _noise((H, W), 18.0, seed + 3)), 2, 8)
    band_role = np.where(top <= np.maximum(1, bd * 0.3), 'band0', np.where(top <= bd * 0.6, 'band1',
                                                                           np.where(top <= bd, 'band2', None)))
    sel = m & (top <= bd) & north
    role[sel] = band_role[sel]
    # paint by ramp
    rp = _ramp_at(Y, X)
    keys = ['winter', 'mid', 'wood']
    for r in ('deep', 'body', 'mid', 'shallow', 'band0', 'band1', 'band2'):
        for i, k in enumerate(keys):
            s = m & (role == r) & (rp == i)
            out[s] = RAMPS[k][r]
    # the north bank's face where the land above is snow or trod (2 rows of wet rock, a light line),
    # the ice's cut face where it is the tarn's ice
    land_above = np.vstack([np.full((1, W), '.', object), landmat[:-1]])
    for y in range(1, H):
        land_above[y] = np.where(m[y] & (top[y] > 1), land_above[y - 1], land_above[y])
    icey = land_above == 'i'
    face = north & ~icey
    lit_stone = K.vhash(X // 3, Y, seed + 5) > 0.72
    out[face & (top == 1)] = np.where(lit_stone[face & (top == 1)], C('slate', 3), C('slate_cool', 1))
    out[face & (top == 2)] = C('slate_cool', 0)
    out[face & (top == 3)] = WATERLINE
    # the face's snow lip over it: the land's last row lit, the row under it a shaded undercut
    lipm = np.roll(face & (top == 1), -1, 0) & ~m
    out[lipm] = C('snow_cool', 2)
    out[np.roll(lipm, -1, 0) & ~m] = C('snow', 5)
    # ice cut face on the lead's and the mouth's far edges: a lit fascia, then shade in steps
    cut = m & icey
    out[cut & (top == 1)] = C('sky_cool', 5)
    out[cut & (top == 2)] = C('sky_cool', 3)
    # the side shores: a texel of wet rock on the land's edge, the snow's lip lit where it faces west
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    edge_land = ndi.binary_dilation(m, structure=cross) & ~m
    snowy = (landmat == '.') | (landmat == 'b')
    out[edge_land & snowy & ~lipm & ~np.roll(lipm, -1, 0)] = RIM
    ice_edge = edge_land & (landmat == 'i')
    out[ice_edge] = C('sky_cool', 5)
    second = ndi.binary_dilation(edge_land, structure=cross) & ~m & ~edge_land & snowy
    faces_west = second & np.roll(m, -2, 1)           # water two texels east: an east bank, lit
    faces_east = second & np.roll(m, 2, 1)
    out[faces_west & ~lipm] = C('snow', 5)
    out[faces_east & ~lipm] = C('snow_cool', 3)
    return dist, top, rp, north



def _glints(out, m, dist, top, rp, H, W, seed):
    """Paired glints along the flow: a streak of 3 to 5 texels and a shorter one beside it."""
    ty, tx = _flow_dir(dist)
    rng = np.random.default_rng(seed + 11)
    keys = ['winter', 'mid', 'wood']
    ys, xs = np.nonzero(m & (dist >= 4) & (top > 9))
    n = len(ys) // 500
    for _k in range(n):
        j = int(rng.integers(0, len(ys)))
        y, x = ys[j], xs[j]
        a = math.atan2(ty[y, x], tx[y, x])
        a = round(a / (math.pi / 4)) * (math.pi / 4)
        dy, dx = math.sin(a), math.cos(a)
        g = RAMPS[keys[rp[y, x]]]['glint']
        for (oy, ox, L) in ((0, 0, int(rng.integers(3, 6))), (-dx * 2 + dy * 2, dy * 2 + dx * 2, int(rng.integers(2, 4)))):
            for i in range(L):
                Y_, X_ = int(round(y + oy + dy * i)), int(round(x + ox + dx * i))
                if 0 <= Y_ < H and 0 <= X_ < W and m[Y_, X_] and dist[Y_, X_] >= 3:
                    out[Y_, X_] = g



def _shelf(out, m, dist, top, north, H, W, seed):
    """Shelf ice fast to the banks near the tarn, thinning downstream: plates 4 to 12 texels out from
    the bank and one to three cells long, a ragged water edge in clusters, a lit top, a shaded fascia
    where it meets open water and the water a tone darker in its shade."""
    Y, X = np.mgrid[0:H, 0:W]
    reach = np.clip((30 * CELL - Y) / (16.0 * CELL), 0.0, 1.0)          # full at the mouth, gone by row 30
    seg = _noise((H, W), 22.0, seed + 21) + 1.6 * reach - 0.9
    wid = 6.0 + 8.0 * np.clip(0.5 + 0.5 * _noise((H, W), 12.0, seed + 22), 0, 1)
    rag = 2.5 * _noise((H, W), 2.5, seed + 23)
    shelf = m & (seg > 0) & (dist <= wid * reach + rag) & (reach > 0) & (top > 3)
    shelf = ndi.binary_opening(shelf, iterations=2)
    lit = ndi.gaussian_filter(K.vhash(X // 2, Y // 2, seed + 24), 1.5) > 0.55
    out[shelf] = np.where(lit[shelf], C('sky_cool', 5), C('snow_cool', 4))
    water = m & ~shelf
    s_s = shelf & np.roll(water, -1, 0)                 # its south edge: the plate's thickness, two rows
    out[s_s] = C('sky_cool', 3)
    out[shelf & np.roll(s_s, -1, 0) & ~s_s] = C('sky_cool', 4)
    s_e = shelf & (np.roll(water, -1, 1) | np.roll(water, 1, 1)) & ~s_s
    out[s_e] = C('sky_cool', 4)
    n_e = shelf & np.roll(~shelf, 1, 0) & ~s_s
    out[n_e] = C('snow', 5)
    shade = water & (np.roll(shelf, 1, 0) | np.roll(np.roll(shelf, 1, 0), 1, 1))
    out[shade] = C('slate_cool', 1)
    return shelf



def _floes(out, m, dist, shelf, H, W, seed, n=2):
    """A few floes broken off the shelf, drifting in the upper reach, each with its wet contact:
    the water a tone darker round it and a light ripple arc on its downstream side."""
    rng = np.random.default_rng(seed + 31)
    ys, xs = np.nonzero(m & (dist >= 7) & ~shelf & (np.arange(H)[:, None] < 26 * CELL) & (np.arange(H)[:, None] > 23 * CELL))
    Y, X = np.mgrid[0:H, 0:W]
    for _k in range(n if len(ys) else 0):
        j = int(rng.integers(0, len(ys)))
        cy, cx = ys[j], xs[j]
        rx, ry = rng.uniform(4, 7), rng.uniform(2.5, 4)
        f = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + 0.4 * (K.vhash(X // 2, Y // 2, seed + j) - 0.5)) < 1.0
        f &= m
        if not f.any():
            continue
        ring = ndi.binary_dilation(f, iterations=1) & m & ~f
        out[ring] = C('slate_cool', 1)
        arc = np.roll(ring, 2, 0) & m & ~f & ~ring
        out[arc & (K.vhash(X, Y, seed + j) > 0.25)] = C('slate', 3)
        out[f] = C('snow_cool', 4)
        out[f & ~np.roll(f, 1, 0)] = C('snow', 5)
        sth = f & ~np.roll(f, -1, 0)
        out[sth] = C('sky_cool', 3)



def outlet(seed=401):
    """The outlet's surface as one ground piece: its picture box covers the water cells and the lead
    with a margin; texels far from the water are left clear, so the zone's ground (and the shadows
    the shader lays on it) show."""
    plan = _plan()
    text = _plan_text()
    bg, g2 = _background_key(text)
    H, W = bg.shape
    m = water_mask()
    gw = np.kron(_water_cells(_grid(plan)), np.ones((CELL, CELL), bool))
    landmat = np.kron(g2, np.ones((CELL, CELL), object)).astype(object)
    out = bg.copy()
    dist, top, rp, north = _paint_water(out, m, landmat, H, W, seed)
    shelf = _shelf(out, m, dist, top, north, H, W, seed)
    _floes(out, m, dist, shelf, H, W, seed)
    _glints(out, m & ~shelf, dist, top, rp, H, W, seed)
    # keep only what differs from the zone's ground near the water, clear elsewhere
    near = ndi.binary_dilation(gw | m, iterations=MARGIN)
    out[~near] = -1
    ys, xs = np.nonzero(near)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    p = V.Pic(x1 - x0, y1 - y0, (x1 - x0) // 2, 0)
    p.a[:] = out[y0:y1, x0:x1]
    p.world = (int(x0), int(y0))
    return p



def outlet_at():
    """Where the outlet piece is placed (its foot: the top middle of its box, so it sorts under every
    other ground piece)."""
    p = outlet()
    return [p.world[0] + p.W // 2, p.world[1]]



def inflow(seed=421):
    """The frozen rill coming into the tarn from the north gully (zone rows 0 to 4): clear dark ice
    down its middle, the lake ice either side, snow banked on both banks over a shaded underside,
    cracks along the flow, and at the frame's top the runnel choked with snow."""
    plan = _plan()
    g = _grid(plan)
    rows = 5
    cm = np.zeros(g.shape, bool)
    cm[:rows] = g[:rows] == 'i'
    H, W = rows * CELL + 12, g.shape[1] * CELL
    w = np.kron(cm, np.ones((CELL, CELL), bool))[:H]
    if w.shape[0] < H:
        w = np.vstack([w, np.repeat(w[-1:], H - w.shape[0], 0)])
    # the tarn below continues: the last 12 rows keep the channel's columns
    Y, X = np.mgrid[0:H, 0:W]
    sd = ndi.distance_transform_edt(w) - ndi.distance_transform_edt(~w)
    sd = ndi.gaussian_filter(sd, 3.0) + 2.5 * _noise((H, W), 7.0, seed)
    m = sd > 0
    dist = ndi.distance_transform_edt(m)
    hw = ndi.maximum_filter(dist, size=31)
    out = np.full((H, W), -1, np.int32)
    out[m] = C('sky_cool', 4)
    core = m & (dist >= np.maximum(hw * 0.55, 3))
    out[core] = C('water_cool', 4)
    out[core & (dist >= hw * 0.8)] = C('water_cool', 3)
    # cracks along the flow, one or two, a lit texel on their west side
    rng = np.random.default_rng(seed + 1)
    ys, xs = np.nonzero(core)
    for _k in range(2 if len(ys) else 0):
        j = int(rng.integers(0, len(ys)))
        y, x = float(ys[j]), float(xs[j])
        for _i in range(int(rng.integers(30, 60))):
            y += 1.0
            x += rng.normal(0, 0.45)
            Y_, X_ = int(y), int(round(x))
            if 0 <= Y_ < H and 0 <= X_ < W and m[Y_, X_]:
                out[Y_, X_] = C('water_cool', 2)
                if X_ > 0 and m[Y_, X_ - 1]:
                    out[Y_, X_ - 1] = C('sky_cool', 5)
    # snow banked over both banks: a lip lit on top, a 2-texel shaded underside on the ice
    bank = ndi.binary_dilation(m, iterations=3) & ~ndi.binary_erosion(m, iterations=2)
    bank &= K.vhash(X // 4, Y // 3, seed + 2) > -1
    lipw = bank & ~m
    out[lipw] = C('snow', 4)
    out[lipw & ~np.roll(lipw, 1, 1)] = C('snow', 5)
    inner = bank & m
    out[inner] = C('snow_cool', 3)
    out[inner & np.roll(m & ~bank, -1, 1)] = C('sky_cool', 3)
    out[inner & np.roll(m & ~bank, 1, 1)] = C('sky_cool', 3)
    # the runnel choked with snow at the frame's top: the channel drifted over, a slot left dark
    choke = m & (Y < 10)
    out[choke] = C('snow', 4)
    slot = choke & core & (Y >= 4)
    out[slot] = C('snow_cool', 2)
    out[choke & (Y == 9)] = C('snow_cool', 3)
    near = ndi.binary_dilation(m, iterations=4)
    out[~near] = -1
    ys, xs = np.nonzero(out >= 0)
    y0, y1, x0, x1 = 0, ys.max() + 1, xs.min(), xs.max() + 1
    p = V.Pic(x1 - x0, y1 - y0, (x1 - x0) // 2, 0)
    p.a[:] = out[y0:y1, x0:x1]
    p.world = (int(x0), int(y0))
    return p



def inflow_at():
    p = inflow()
    return [p.world[0] + p.W // 2, p.world[1]]



def thaw_band(seed=441):
    """The short thaw band at the woodland's north seam (Matt, 23 Nov), over the zone's last three
    rows and its whole width: the snow wet and greying southward, then breaking into lobed patches
    of bare cold earth and flattened brown grass every 100 to 200 texels, growing toward the seam;
    slush round each patch (a shaded inner wall on its north, a lit far rim); rivulets 2 to 3 texels
    wide running downhill to the outlet's water (a dark north edge, a lit south line); on the Col
    Path slush and puddles; the snow pulled back round the feet of the trees on these rows. Only
    land texels are painted (the outlet's water is the outlet piece's)."""
    plan = _plan()
    g = _grid(plan)
    rows = 3
    Hz, Wz = g.shape[0] * CELL, g.shape[1] * CELL
    y0 = Hz - rows * CELL - 12
    H, W = Hz - y0, Wz
    Y, X = np.mgrid[0:H, 0:W]
    v = np.clip((Y - 6.0) / (H - 7.0), 0, 1)                        # 0 at the band's top, 1 at the seam
    wm = water_mask()[y0:]
    gw = np.kron(g[-(H // CELL + 1):], np.ones((CELL, CELL), object))[-H:]
    trod = gw == 'b'
    land = ~wm & ~ndi.binary_dilation(wm, iterations=2)
    rng = np.random.default_rng(seed)
    # where the patches open: centres every 100 to 200 texels along the band, lobed
    lob = np.zeros((H, W))
    x = float(rng.uniform(10, 60))
    while x < W:
        cy = float(rng.uniform(0.45, 0.95)) * H
        r = float(rng.uniform(16, 48))
        for _k in range(int(rng.integers(3, 6))):
            ox, oy = rng.uniform(-r, r) * 0.8, rng.uniform(-r, r) * 0.35
            rr = r * rng.uniform(0.45, 0.8)
            lob = np.maximum(lob, 1.0 - (((X - x - ox) / rr) ** 2 + ((Y - cy - oy) / (rr * 0.55)) ** 2))
        x += float(rng.uniform(100, 200))
    # snow pulled back round the trees' feet on these rows
    for p in plan['pieces']:
        if p['piece'] in ('frost_pine', 'frost_pine_squat', 'frost_spruce', 'frost_krummholz', 'frost_snag'):
            fx, fy = p['at'][0], p['at'][1] - y0
            if -10 <= fy <= H + 10:
                lob = np.maximum(lob, 0.9 * (1.0 - (((X - fx) / 15.0) ** 2 + ((Y - fy) / 7.0) ** 2)))
    n = _noise((H, W), 4.0, seed + 1)
    field = lob + 0.25 * n + 0.55 * v - 0.25
    bare = land & (field > 0.35)
    bare = ndi.binary_opening(bare, iterations=1)
    wet = land & (field > 0.0) & ~bare
    rimw = land & ndi.binary_dilation(bare, iterations=2) & ~bare
    out = np.full((H, W), -1, np.int32)
    # wet, grey-stained crust: the snow's own drift tones a step down, in clusters
    grey = K.vhash(X // 3, Y // 2, seed + 2) > 0.45
    out[wet] = np.where(grey[wet], C('snow_cool', 3), C('snow_cool', 2))
    # slush round each patch: the inner wall shaded where the patch lies south of it, the far rim lit
    out[rimw] = C('sky_cool', 4)
    out[rimw & np.roll(bare, -1, 0)] = C('snow_cool', 2)
    out[rimw & np.roll(bare, 1, 0)] = C('snow', 5)
    # the bare ground: cold earth, flattened brown grass lying downhill, a stone now and then; on the trod slush and puddles
    eb = bare & ~trod
    tone = _noise((H, W), 2.0, seed + 3)
    out[eb] = np.where(tone[eb] > 0.2, C('earth_cool', 2), C('earth_cool', 3))
    gr = eb & (K.vhash(X // 2, Y // 3, seed + 4) > 0.55) & np.roll(eb, 1, 0)
    out[gr] = C('earth', 3)
    out[gr & (K.vhash(X, Y, seed + 5) > 0.55)] = C('grass_warm', 0)
    out[eb & np.roll(~eb, 1, 0)] = C('earth_cool', 1)                  # the patch's north edge in shade
    for _k in range(6):
        ys, xs = np.nonzero(eb & ndi.binary_erosion(eb, iterations=3))
        if not len(ys):
            break
        j = int(rng.integers(0, len(ys)))
        cy, cx = ys[j], xs[j]
        st = ((X - cx) / rng.uniform(2.2, 3.6)) ** 2 + ((Y - cy) / rng.uniform(1.6, 2.6)) ** 2 < 1.0
        out[st] = C('stone', 3)
        out[st & ((X - cx) + (Y - cy) < -1)] = C('stone', 4)
        out[st & ((X - cx) + (Y - cy) > 1.5)] = C('stone', 2)
        out[np.roll(st, 1, 0) & ~st & eb] = C('earth_cool', 1)
    pb = bare & trod
    out[pb] = C('slate', 2)
    out[pb & np.roll(~pb, 1, 0)] = C('slate_cool', 1)                  # the puddle's inner wall, shaded north
    out[pb & np.roll(~pb, -1, 0)] = C('snow_cool', 3)                  # its far rim lit
    out[pb & (K.vhash(X // 2, Y, seed + 6) > 0.85)] = C('slate', 3)
    # rivulets to the water: 2 to 3 texels wide, a dark north edge and a lit south line
    wcols = np.nonzero(wm.any(0))[0]
    wx0, wx1 = (wcols.min(), wcols.max()) if len(wcols) else (W // 2, W // 2)
    for side in (-1, 1):
        for _k in range(3):
            if side < 0:
                x = float(rng.uniform(max(0, wx0 - 150), wx0 - 40))
            else:
                x = float(rng.uniform(wx1 + 40, min(W - 1, wx1 + 150)))
            y = float(rng.uniform(H * 0.1, H * 0.45))
            wd = int(rng.integers(2, 4))
            for _i in range(800):
                X_, Y_ = int(round(x)), int(round(y))
                if not (0 <= X_ < W and 0 <= Y_ < H - wd - 1) or wm[Y_, X_]:
                    break
                for k in range(wd):
                    if land[Y_ + k, X_] or wm[Y_ + k, X_]:
                        out[Y_ + k, X_] = C('slate_cool', 1) if k == 0 else C('slate', 2)
                if land[Y_ + wd, X_]:
                    out[Y_ + wd, X_] = C('snow_cool', 3)
                x += -side * 1.0
                y += 0.32 + 0.15 * math.sin(x / 7.0)
    out[~land & (out >= 0) & (wm)] = -1
    p = V.Pic(W, H, W // 2, 0)
    p.a[:] = out
    p.world = (0, int(y0))
    return p



def thaw_at():
    p = thaw_band()
    return [p.world[0] + p.W // 2, p.world[1]]



WOODLAND_GROUND = os.path.join(ROOT, 'game', 'zones', 'woodland', 'art', 'ground.png')
WOODLAND_CONIFERS = ((204, 192), (384, 192))      # the north pines' feet (woodland_base.tscn pine-1, pine-7)



def woodland_seam(seed=461, width=624, height=216):
    """The woodland's half of the thaw at the Frostline door (round 1 audits of #535): over the
    woodland's north rows from its west edge past the door, drawn over the woodland's own baked
    ground (game/zones/woodland/art/ground.png): old snow lying in the lee (east) of the scree's
    stones and thick along the north edge, thinning south; the scree round it wet (its own tones a
    step darker); meltwater rivulets running from the snow to the brook; on the lawn's first row the
    grass flattened and brown; and a patch of old snow in the shade under each north pine. Only the
    texels it changes are opaque."""
    from PIL import Image
    from scripts.art.native.palette import LUT
    rgb = np.asarray(Image.open(WOODLAND_GROUND).convert('RGB'))[:height, :width].astype(np.int32)
    inv = {tuple(int(v) for v in LUT[i][:3]): i for i in range(len(LUT))}
    key = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
    codes = np.full(key.shape, -1, np.int32)
    for k in np.unique(key):
        c = inv.get((int(k) >> 16, (int(k) >> 8) & 255, int(k) & 255))
        if c is not None:
            codes[key == k] = c
    H, W = codes.shape
    Y, X = np.mgrid[0:H, 0:W]
    fam = np.where(codes >= 0, codes // 8, -1)
    tone = np.where(codes >= 0, codes % 8, 0)
    water = np.isin(fam, [FI_ for FI_ in (C('water', 0) // 8, C('water_cool', 0) // 8)])
    green = np.isin(fam, [C('grass', 0) // 8, C('grass_cool', 0) // 8, C('grass_warm', 0) // 8, C('leaf', 0) // 8])
    stone = np.isin(fam, [C('stone', 0) // 8, C('stone_cool', 0) // 8, C('crag', 0) // 8])
    scree = (codes >= 0) & ~water & ~green
    out = np.full((H, W), -1, np.int32)
    n = _noise((H, W), 5.0, seed)
    # snow: thick at the north edge, thinning south through the scree; in each stone's lee
    lee = (np.roll(stone, 2, 1) | np.roll(stone, 3, 1)) & ~stone & scree
    edge = np.clip(1.0 - Y / 90.0, 0, 1)
    snow = scree & ~stone & ((n + 1.8 * edge - 1.3 > 0) | (lee & (n > 0.2 - edge)))
    for (cx, cy) in WOODLAND_CONIFERS:
        under = (((X - cx) / 26.0) ** 2 + ((Y - cy + 6) / 9.0) ** 2 + 0.3 * n) < 1.0
        snow |= under & ~water
    snow = ndi.binary_opening(snow, iterations=1) & (codes >= 0) & ~water & ~stone
    sv = K.vhash(X // 4, Y // 3, seed) > 0.55
    out[snow] = np.where(sv[snow], C('snow_cool', 3), C('snow_cool', 4))
    out[snow & ~np.roll(snow, 1, 0)] = C('snow', 5)
    out[snow & ~np.roll(snow, -1, 0)] = C('snow_cool', 2)
    # the wet scree round the snow: its own tones a step darker
    wet = ndi.binary_dilation(snow, iterations=5) & ~snow & scree & (tone > 0)
    wet |= scree & (tone > 0) & (n + 1.4 * edge - 0.6 > 0) & ~snow
    out[wet] = codes[wet] - 1
    # the lawn's first row flattened and brown, in clumps
    lawn_top = np.zeros((H, W), bool)
    for x in range(W):
        col = np.nonzero(green[:, x] & (Y[:, x] < 140))[0]
        if len(col):
            y0 = col.min()
            d = 6 + int(10 * hsh(seed, x // 9))
            lawn_top[y0:y0 + d, x] = True
    flat = lawn_top & green & (ndi.gaussian_filter(K.vhash(X // 2, Y // 2, seed + 1), 1.5) > 0.42)
    fv = K.vhash(X, Y // 2, seed + 2) > 0.5
    out[flat] = np.where(fv[flat], C('grass_warm', 0), C('earth', 3))
    # meltwater rivulets from the snow to the brook: a dark line, its north edge lit
    wcols = np.nonzero(water[:100].any(0))[0]
    if len(wcols):
        bx0, bx1 = wcols.min(), wcols.max()
        rng = np.random.default_rng(seed + 3)
        for _k in range(5):
            side = -1 if rng.random() < 0.4 else 1
            x = float(rng.uniform(max(0, bx0 - 70), bx0 - 10) if side < 0 else rng.uniform(bx1 + 10, min(W - 1, bx1 + 80)))
            y = float(rng.uniform(8, 50))
            for _i in range(int(rng.integers(30, 90))):
                Xi, Yi = int(round(x)), int(round(y))
                if not (0 <= Xi < W and 1 <= Yi < H - 2) or water[Yi, Xi]:
                    break
                out[Yi, Xi] = C('slate_cool', 1)
                out[Yi + 1, Xi] = C('water', 2)
                out[Yi - 1, Xi] = C('snow_cool', 3) if snow[Yi - 1, Xi] else out[Yi - 1, Xi]
                x += 1.0 if side < 0 else -1.0
                y += 0.45 + 0.25 * math.sin(x / 6.0)
    p = V.Pic(W, H, 0, 0)
    p.a[:] = out
    return p
