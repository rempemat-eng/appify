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

# the water's tones by role, in four stages from the winter outlet to the woodland's brook (round 2 audits of
# #535, R1, R2 and logic F2): the winter water greyed in water's own hue (water_winter, OKLCH 0.386 / 0.056 /
# 250, the body), then chroma first (water_thaw 2 under the winter's thalweg), then value (water_thaw 3), then
# the woodland brook's own ramp in its last 8 to 12 texels
STAGES = [
    dict(deep=C('water_winter', 2), body=C('water_winter', 3), band0=C('water_winter', 1), band1=C('water_winter', 2),
         lit=C('water_winter', 4), core=C('water_winter', 5)),
    dict(deep=C('water_winter', 2), body=C('water_thaw', 2), band0=C('water_winter', 1), band1=C('water_winter', 2),
         lit=C('water_thaw', 4), core=C('water_thaw', 5)),
    dict(deep=C('water_thaw', 2), body=C('water_thaw', 3), band0=C('water_thaw', 1), band1=C('water_thaw', 2),
         lit=C('water_thaw', 4), core=C('water_thaw', 5)),
    dict(deep=C('water', 1), body=C('water', 2), band0=C('water', 0), band1=C('water', 1),
         lit=C('water', 4), core=C('water', 5)),
]
RAMPS = {'winter': STAGES[0], 'wood': STAGES[3]}
RIM = C('slate_cool', 1)          # a texel of wet rock at the land's edge
WATERLINE = C('snow_cool', 3)     # the light line under a north bank, in the snow's cool tones
REFLECT = C('snow_cool', 2)       # the snow's reflection: a broken line under a south bank
SEAM_TOP = 945                    # the climb toward the woodland's brook starts under the bridge



@lru_cache(maxsize=None)
def _plan_text():
    with open(ZONE) as f:
        return f.read()



def _plan():
    return json.loads(_plan_text())



def _grid(plan):
    return np.array([list(r) for r in plan['rows']])



def _water_cells(g):
    """The outlet's cells: open water from its mouth down."""
    w = g == 'a'
    w[:OUTLET_TOP] = False
    return w



def _hole_cells(g):
    """The ice-cutter's hole in the tarn (round 2 detail audit, R9): open water above the outlet's mouth."""
    w = g == 'a'
    w[OUTLET_TOP:] = False
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
    row to the tarn's ice, the trod's crossing to the trod, the rest to snow; the ice-cutter's hole to
    the tarn's ice (the outlet piece paints it)."""
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
    g2[_hole_cells(g)] = 'i'
    kit = Kit()
    legend = {s: kit.ids[n] for s, n in plan['legend'].items()}
    cells = np.array([[legend[ch] for ch in row] for row in g2], np.int32)
    return compose.render(cells, kit, dressing=True), g2



def _noise(shape, sigma, seed):
    n = ndi.gaussian_filter(np.random.default_rng(seed).standard_normal(shape), sigma)
    return n / (n.std() + 1e-9)



def _runs1d(n, rng, lo, hi, run=(2, 5)):
    """A row of whole-texel offsets in runs (lo .. hi, each held 2 to 5 texels): a clustered, stepped edge."""
    out = np.zeros(n, np.int32)
    x = 0
    while x < n:
        k = int(rng.integers(run[0], run[1] + 1))
        out[x:x + k] = int(rng.integers(lo, hi + 1))
        x += k
    return out



def _walk1d(n, rng, lo, hi, run=(3, 6)):
    """A row of whole-texel offsets that wanders: each run of 3 to 6 texels steps one texel from the last."""
    out = np.zeros(n, np.int32)
    x, v = 0, int(rng.integers(lo, hi + 1))
    while x < n:
        k = int(rng.integers(run[0], run[1] + 1))
        out[x:x + k] = v
        v = int(np.clip(v + rng.choice([-1, 1]), lo, hi))
        x += k
    return out



def _disk(r):
    k = np.arange(-r, r + 1)
    return np.add.outer(k * k, k * k) <= r * r



def _round(m, r):
    """Round every corner of a mask to radius r or more (closing then opening by a disk), the canvas's
    edges continuing outward."""
    p = r + 2
    q = np.pad(m, p, mode='edge')
    q = ndi.binary_closing(q, structure=_disk(r))
    q = ndi.binary_opening(q, structure=_disk(r))
    return q[p:-p, p:-p]



def _pin_rows(m, y0, y1, ease, l_to, r_to, centre, seed=0):
    """Rows y0 .. y1 - 1 hold exactly columns l_to .. r_to - 1; over the `ease` rows above them each bank
    curves from where it stands at the first of those rows to the pinned column (a smoothstep, with a
    texel of wobble on its way), so no cell's corner shows as a step in the last rows."""
    H, W = m.shape
    yr = max(0, y0 - ease)
    cols = np.nonzero(m[yr])[0]
    if len(cols):
        lab, _n = ndi.label(m[yr])
        k = lab[int(centre)] if m[yr, int(centre)] else lab[cols[np.argmin(np.abs(cols - centre))]]
        run = np.nonzero(lab == k)[0]
        ln, rn = int(run.min()), int(run.max()) + 1
    else:
        ln, rn = l_to, r_to
    wob = np.round(0.9 * _noise((ease + 1, 2), 2.0, seed + 77)).astype(int)
    for y in range(yr + 1, min(H, y1)):
        if y >= y0:
            m[y, :] = False
            m[y, l_to:r_to] = True
            continue
        f = (y - yr) / float(ease)
        f = f * f * (3 - 2 * f)
        damp = 1.0 - f
        lw = int(round(ln + (l_to - ln) * f + damp * wob[y - yr, 0]))
        rw = int(round(rn + (r_to - rn) * f + damp * wob[y - yr, 1]))
        lab, _n = ndi.label(m[y])
        c_ = int(np.clip(centre, 0, W - 1))
        if m[y, c_]:
            run = np.nonzero(lab == lab[c_])[0]
            m[y, run.min():run.max() + 1] = False
        m[y, lw:rw] = True



@lru_cache(maxsize=None)
def _mask_key(text, seed=401):
    """The outlet's water (world texels), after the round 2 logic audit's F1 (no staircase banks): the
    cells' outline smoothed and set wandering on the soft grid along every bank (straight runs of 12 to
    16 texels at most, bays and points of 3 to 8), every corner rounded to 6 texels or more; pinned
    only over the last 5 rows above the lip (the sheet's columns) and the last 4 rows at the zone's
    edge (the brook's cells, where the woodland carries it on); the tarn's ice ragged across the
    mouth; the lead cut into the ice above it."""
    plan = json.loads(text)
    g = _grid(plan)
    H, W = g.shape[0] * CELL, g.shape[1] * CELL
    w = np.kron(_water_cells(g), np.ones((CELL, CELL), bool))
    sd = ndi.distance_transform_edt(w) - ndi.distance_transform_edt(~w)
    sd = ndi.gaussian_filter(sd, 6.0)
    off = 4.4 * _noise((H, W), 11.0, seed + 1) + 1.7 * _noise((H, W), 4.5, seed + 2)
    m = (sd + 8.0 * np.tanh(off / 8.0)) > 0
    m = _round(m, 6)
    mouth = OUTLET_TOP * CELL
    m[:mouth - 8] = False
    # the tarn's ice across the mouth: rotten, ragged by 2 to 6 texels in clustered steps
    rng = np.random.default_rng(seed + 3)
    rag = _walk1d(W, rng, -3, 3, (3, 6))
    core = np.nonzero(m[mouth:mouth + 12].any(0))[0]
    for x in range(core.min() if len(core) else 0, core.max() + 1 if len(core) else 0):
        top = mouth + int(rag[x])
        m[mouth - 8:top, x] = False
        if m[mouth + 10, x] or m[mouth + 4, x]:
            m[top:mouth + 4, x] = True
    # the mouth's corners rounded where its ice edge meets the banks (radius 8)
    for y in range(mouth - 4, mouth + 10):
        cols = np.nonzero(m[y])[0]
        if not len(cols):
            continue
        dy = y - (mouth - 4)
        cut = int(round(8 - math.sqrt(max(0.0, 64 - (8 - min(8, dy)) ** 2))))
        m[y, cols.min():cols.min() + cut] = False
        m[y, cols.max() + 1 - cut:cols.max() + 1] = False
    # the last 5 rows above the lip: the sheet's width exactly (the glassy tongue), the banks easing in
    _x0, _y0, lip, s0, s1 = _fall(plan)
    _pin_rows(m, lip - 4, lip + 1, 22, s0, s1, (s0 + s1) / 2.0, seed)
    m[lip + 1:_y0 + LIP_PX + 96, :] = False            # under the face nothing shows: the channel straight there
    m[lip + 1:_y0 + LIP_PX + 96, s0:s1] = True
    # the last 4 rows at the zone's edge: the brook's cells, where the woodland's brook carries on
    last = np.nonzero(w[H - 1])[0]
    if len(last):
        _pin_rows(m, H - 4, H, 26, int(last.min()), int(last.max()) + 1, (last.min() + last.max() + 1) / 2.0, seed + 1)
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



@lru_cache(maxsize=None)
def _hole_key(text, seed=411):
    """The ice-cutter's hole (R9): its cell sawn square into the ice, a texel or two in from the cell,
    its sawn sides straight but for a jog of a texel here and there, its corners chipped."""
    plan = json.loads(text)
    g = _grid(plan)
    H, W = g.shape[0] * CELL, g.shape[1] * CELL
    w = np.kron(_hole_cells(g), np.ones((CELL, CELL), bool))
    m = ndi.binary_erosion(w, iterations=3)
    if not m.any():
        return m
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    for (yy, out_) in ((y0, y0 - 1), (y1 - 1, y1)):                 # the north and south saw cuts
        jog = _runs1d(x1 - x0, rng, -1, 1, (5, 12))
        for i, x in enumerate(range(x0, x1)):
            if jog[i] > 0:
                m[out_, x] = True
            elif jog[i] < 0:
                m[yy, x] = False
    for (xx, out_) in ((x0, x0 - 1), (x1 - 1, x1)):                 # the west and east cuts
        jog = _runs1d(y1 - y0, rng, -1, 1, (5, 12))
        for i, y in enumerate(range(y0, y1)):
            if jog[i] > 0:
                m[y, out_] = True
            elif jog[i] < 0:
                m[y, xx] = False
    Y, X = np.mgrid[0:H, 0:W]
    for (cy, cx) in ((y0, x0), (y0, x1 - 1), (y1 - 1, x0), (y1 - 1, x1 - 1)):
        r = int(rng.integers(2, 4))
        m[(np.abs(Y - cy) + np.abs(X - cx)) < r] = False
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



def _stage_at(Y, X, rel, H, seed):
    """Which stage a texel's water takes (R2, logic F2): the winter's down to the bridge; below it the
    lighter stages advance down the shallows first and the dark thalweg holds longest, so every
    boundary is a tongue lying along the flow (the contours of the depth), never on a row; the
    woodland's own ramp only over the last 8 to 12 texels."""
    ye = H - 14
    t = np.clip((Y - SEAM_TOP) / float(ye - SEAM_TOP), 0.0, 1.0)
    e = t + 0.34 * (1.0 - rel) + 0.05 * _noise(Y.shape, 3.0, seed + 41)
    st = np.where(Y < SEAM_TOP - 6, 0, np.where(e < 0.32, 0, np.where(e < 0.70, 1, 2)))
    wood = Y >= H - 12 + 4.0 * rel + 0.8 * _noise(Y.shape, 2.0, seed + 42)
    return np.where(wood, 3, st)



def _paint_water(out, m, landmat, H, W, seed):
    """Paint the outlet's water into `out` (world texels) where `m`: a calm body, a darker thalweg, the
    north banks' face and dark band, the south banks' reflection, the side shores' rim."""
    Y, X = np.mgrid[0:H, 0:W]
    dist = ndi.distance_transform_edt(m)
    ds = ndi.gaussian_filter(dist, 1.2)
    hw = ndi.gaussian_filter(ndi.maximum_filter(dist, footprint=_disk(20)), 8.0)
    rel = np.clip(ds / np.maximum(hw, 1.0), 0.0, 1.0)
    st = _stage_at(Y, X, rel, H, seed)
    role = np.full((H, W), 'body', object)
    deep = (ndi.gaussian_filter(rel, 2.5) > 0.66) & (hw >= 8)
    deep = _round(deep, 3) & m
    role[deep] = 'deep'
    # the run of water down from the land above, per column, and up from the land below
    top = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H):
        run = np.where(m[y], run + 1, 0)
        top[y] = run
    bot = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H - 1, -1, -1):
        run = np.where(m[y], run + 1, 0)
        bot[y] = run
    # which way each bank faces: the mask's smoothed gradient at its first and last rows
    gm = ndi.gaussian_filter(m.astype(float), 2.5)
    gy, gx = np.gradient(gm)
    gn = np.hypot(gy, gx) + 1e-9
    first = m & (top == 1)
    lastw = m & (bot == 1)
    northf = first & (gy / gn > 0.8)                   # land to the north, the bank level within 37 degrees
    southf = lastw & (gy / gn < -0.8)
    # a north bank runs at least bank_h + 3 texels (5.3a): shorter lumps get no face
    lab, n = ndi.label(ndi.binary_dilation(northf, structure=np.ones((3, 3), bool)) & first)
    sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) if n else []
    keep = np.zeros(n + 1, bool)
    keep[1:] = np.asarray(sizes) >= 12
    northf = first & keep[lab]
    # the face hangs from the north bank's first row; its band beneath steps back to the body
    ncol = np.zeros((H, W), bool)
    ncol[northf] = True
    north = np.zeros((H, W), bool)
    for k in range(14):
        north |= np.roll(ncol, k, 0) & m & (top == k + 1)
    rng = np.random.default_rng(seed + 3)
    depth = _runs1d(W, rng, 2, 8, (8, 16))                # the band's depth, held straight 8 to 16 texels
    alt = _runs1d(W, rng, 0, 1, (2, 4)).astype(bool)      # its last step in clusters along the bank
    land_above = np.vstack([np.full((1, W), '.', object), landmat[:-1]])
    for y in range(1, H):
        land_above[y] = np.where(m[y] & (top[y] > 1), land_above[y - 1], land_above[y])
    icey = land_above == 'i'
    b = top - 3                                          # rows under the bank's face (rock or cut ice: 3 rows)
    d = depth[None, :].repeat(H, 0)
    band0 = north & (b >= 1) & (b <= np.ceil(d / 3.0))
    band1 = north & (b >= 1) & (b <= np.ceil(2 * d / 3.0)) & ~band0
    band2 = north & (b >= 1) & (b <= d) & ~band0 & ~band1 & alt[None, :]
    for i, stg in enumerate(STAGES):
        s_ = m & (st == i)
        out[s_ & (role == 'body')] = stg['body']
        out[s_ & (role == 'deep')] = stg['deep']
        out[s_ & band2] = stg['band1']
        out[s_ & band1] = stg['band1']
        out[s_ & band0] = stg['band0']
    # the north bank's face where the land above is snow or trod (2 rows of wet rock, the light
    # waterline), the ice's cut face where it is the tarn's ice (a lit fascia, its shaded foot, then the
    # waterline)
    face = north & ~icey
    lit_stone = _runs1d(W, rng, 0, 1, (2, 5)).astype(bool)[None, :].repeat(H, 0) & (K.vhash(X // 4, Y, seed + 5) > 0.5)
    sel = face & (top == 1)
    out[sel] = np.where(lit_stone[sel], C('slate', 3), C('slate_cool', 1))
    out[face & (top == 2)] = C('slate_cool', 0)
    out[face & (top == 3)] = WATERLINE
    cut = north & icey
    out[cut & (top == 1)] = C('snow', 5)
    out[cut & (top == 2)] = C('sky_cool', 4)
    out[cut & (top == 3)] = C('sky_cool', 2)
    # the face's snow lip over it: the land's last row lit, the row above it a shaded undercut
    lipm = np.roll(face & (top == 1), -1, 0) & ~m
    out[lipm] = C('snow_cool', 2)
    out[np.roll(lipm, -1, 0) & ~m] = C('snow', 5)
    # the south banks: a broken line of the snow's reflection, a texel under the bank, off the side shores
    lab, n = ndi.label(ndi.binary_dilation(southf, structure=np.ones((3, 3), bool)) & lastw)
    sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1)) if n else []
    keep = np.zeros(n + 1, bool)
    keep[1:] = np.asarray(sizes) >= 6
    southf = lastw & keep[lab]
    on = _runs1d(W, rng, 0, 2, (2, 6))[None, :].repeat(H, 0) > 0
    refl = np.roll(southf, -1, 0) & m & ~southf & on & (st < 3)
    out[refl] = REFLECT
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
    return dist, top, st, north, hw



def _streaks(out, m, dist, top, st, north, hw, H, W, seed):
    """Lit streaks along the flow lanes (R4: no stamped ticks): each a straight run of 4 to 7 texels down
    the current (its direction the nearest of eight), a shorter one parallel to it two texels across and
    a texel or two further down; more of them, longer and two texels thick where the water narrows and
    speeds up; the longer ones carry a brighter core."""
    ty, tx = _flow_dir(dist)
    rng = np.random.default_rng(seed + 11)
    ok = m & (dist >= 3) & ~north & (top > 6)
    ys, xs = np.nonzero(ok)
    if not len(ys):
        return
    wgt = 1.0 / np.maximum(hw[ys, xs], 5.0) ** 1.5
    wgt /= wgt.sum()
    n = len(ys) // 420
    taken = np.zeros((H, W), bool)

    def lane(y, x, dy, dx, L):
        pts = []
        for i in range(L):
            Y_, X_ = int(round(y + dy * i)), int(round(x + dx * i))
            if not (0 <= Y_ < H and 0 <= X_ < W) or not ok[Y_, X_]:
                break
            pts.append((Y_, X_))
        return pts
    for _k in range(n):
        j = int(rng.choice(len(ys), p=wgt))
        y, x = int(ys[j]), int(xs[j])
        if taken[y, x]:
            continue
        fast = hw[y, x] < 9.0
        a = round(math.atan2(ty[y, x], tx[y, x]) / (math.pi / 4)) * (math.pi / 4)
        dy, dx = round(math.sin(a)), round(math.cos(a))
        L = int(rng.integers(5, 8)) if fast else int(rng.integers(4, 7))
        pts = lane(y, x, dy, dx, L)
        if len(pts) < 4:
            continue
        stg = STAGES[int(st[y, x])]
        px, py = -dy, dx                                   # across the current
        for i, (Y_, X_) in enumerate(pts):
            out[Y_, X_] = stg['core'] if (len(pts) >= 5 and 1 <= i <= 2) else stg['lit']
            if fast and 0 < i < len(pts) - 1:
                Yt, Xt = Y_ + py, X_ + px
                if 0 <= Yt < H and 0 <= Xt < W and ok[Yt, Xt]:
                    out[Yt, Xt] = stg['lit']
        taken[max(0, y - 6):y + 10, max(0, x - 6):x + 7] = True
        side = 1 if rng.random() < 0.5 else -1
        sy, sx = y + dy * int(rng.integers(1, 3)) + side * 2 * py, x + dx * int(rng.integers(1, 3)) + side * 2 * px
        for (Y_, X_) in lane(sy, sx, dy, dx, max(2, len(pts) - int(rng.integers(2, 4)))):
            out[Y_, X_] = stg['lit']



def _shelf(out, m, dist, top, north, H, W, seed):
    """Shelf ice fast to the banks near the tarn, thinning downstream: plates 4 to 12 texels out from
    the bank and one to three cells long, a ragged water edge in clusters, a lit top, a shaded fascia
    where it meets open water and the water a tone darker in its shade. Plates too small to hold to
    the bank, or standing out on the land's side, are left out (logic P3); a plate's corners are
    chipped (P2)."""
    Y, X = np.mgrid[0:H, 0:W]
    reach = np.clip((28 * CELL - Y) / (15.0 * CELL), 0.0, 1.0)          # full at the mouth, gone by row 28
    seg = _noise((H, W), 22.0, seed + 21) + 1.6 * reach - 0.9
    wid = 6.0 + 8.0 * np.clip(0.5 + 0.5 * _noise((H, W), 12.0, seed + 22), 0, 1)
    rag = 2.5 * _noise((H, W), 2.5, seed + 23)
    shelf = m & (seg > 0) & (dist <= wid * reach + rag) & (reach > 0) & (top > 3)
    shelf = ndi.binary_opening(shelf, iterations=2)
    lab, n = ndi.label(shelf)
    rng = np.random.default_rng(seed + 25)
    for k in range(1, n + 1):
        c = lab == k
        if c.sum() < 60:
            shelf[c] = False
            continue
        ys, xs = np.nonzero(c)
        for (cy, cx) in ((ys.min(), xs.min()), (ys.min(), xs.max()), (ys.max(), xs.min()), (ys.max(), xs.max())):
            if rng.random() < 0.6:
                r = int(rng.integers(2, 5))
                shelf[c & ((np.abs(Y - cy) + np.abs(X - cx)) < r)] = False
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
    out[shade] = C('water_winter', 2)
    return shelf



def _floes(out, m, dist, shelf, H, W, seed, n=2):
    """A few floes broken off the shelf, drifting in the upper reach, each with its wet contact:
    the water a tone darker round it and a light ripple arc on its downstream side; their outlines
    irregular, one larger than the other (P2)."""
    rng = np.random.default_rng(seed + 31)
    ys, xs = np.nonzero(m & (dist >= 8) & ~shelf & (np.arange(H)[:, None] < 26 * CELL) & (np.arange(H)[:, None] > 23 * CELL))
    Y, X = np.mgrid[0:H, 0:W]
    for k_ in range(n if len(ys) else 0):
        j = int(rng.integers(0, len(ys)))
        cy, cx = ys[j], xs[j]
        big = k_ == 0
        rx, ry = (rng.uniform(5.5, 7), rng.uniform(3, 4)) if big else (rng.uniform(3, 4.5), rng.uniform(2, 3))
        f = (((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + 0.6 * (K.vhash(X // 2, Y // 2, seed + j) - 0.5)) < 1.0
        f &= m
        if not f.any():
            continue
        ring = ndi.binary_dilation(f, iterations=1) & m & ~f
        out[ring] = C('water_winter', 2)
        arc = np.roll(ring, 2, 0) & m & ~f & ~ring
        out[arc & (K.vhash(X, Y, seed + j) > 0.25)] = C('water_winter', 4)
        out[f] = C('snow_cool', 4)
        out[f & ~np.roll(f, 1, 0)] = C('snow', 5)
        sth = f & ~np.roll(f, -1, 0)
        out[sth] = C('sky_cool', 3)



def _tongue(out, m, plan, H, W, seed):
    """The pool's last rows before the lip climb in value into the fall's glassy tongue, one tone a row
    in clustered steps (R1): body, then water_winter 4 from about 10 rows above the rim, under the
    fall piece's tongue (whose checker then lies on its own tone)."""
    _x0, _y0, lip, s0, s1 = _fall(plan)
    rng = np.random.default_rng(seed + 51)
    step = _runs1d(W, rng, 0, 2, (2, 4))
    for y in range(lip - 12, lip + 1):
        for x in range(W):
            if not m[y, x]:
                continue
            if y >= lip - 10 + int(step[x]):
                out[y, x] = C('water_winter', 4)
            elif y >= lip - 12 + int(step[x]):
                out[y, x] = C('water_winter', 3) if (x // 2 + y) % 3 else C('water_winter', 4)



def _hole(out, hm, H, W, seed):
    """The ice-cutter's hole in the winter water (R9): the ice's cut face on its far (north) edge, a lit
    texel over a shaded one, then the dark band under it in straight steps; a texel of the ice's own
    shade on the other sides; no checker."""
    if not hm.any():
        return
    top = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H):
        run = np.where(hm[y], run + 1, 0)
        top[y] = run
    rng = np.random.default_rng(seed + 61)
    depth = _runs1d(W, rng, 3, 7, (6, 12))[None, :].repeat(H, 0)
    out[hm] = C('water_winter', 3)
    out[hm & (top == 1)] = C('snow', 5)
    out[hm & (top == 2)] = C('sky_cool', 3)
    b = top - 2
    out[hm & (b >= 1) & (b <= np.ceil(depth / 3.0))] = C('water_winter', 1)
    out[hm & (b > np.ceil(depth / 3.0)) & (b <= depth)] = C('water_winter', 2)
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    rim = ndi.binary_dilation(hm, structure=cross) & ~hm
    out[rim & ~np.roll(hm, 1, 0)] = C('sky_cool', 3)
    # a slush crumb or two of the cut floating at the hole's south end, and one lit streak
    ys, xs = np.nonzero(hm & (top > 10))
    if len(ys):
        j = int(rng.integers(0, len(ys)))
        y, x = ys[j], xs[j]
        out[y, x:x + 3][hm[y, x:x + 3]] = C('water_winter', 4)
        out[y + 1, x + 1:x + 3][hm[y + 1, x + 1:x + 3]] = C('water_winter', 5)



def outlet(seed=401):
    """The outlet's surface as one ground piece: its picture box covers the water cells, the lead and
    the ice-cutter's hole with a margin; texels far from the water are left clear, so the zone's ground
    (and the shadows the shader lays on it) show."""
    plan = _plan()
    text = _plan_text()
    bg, g2 = _background_key(text)
    H, W = bg.shape
    m = water_mask()
    hm = _hole_key(text)
    g = _grid(plan)
    gw = np.kron(_water_cells(g) | _hole_cells(g), np.ones((CELL, CELL), bool))
    landmat = np.kron(g2, np.ones((CELL, CELL), object)).astype(object)
    out = bg.copy()
    dist, top, st, north, hw = _paint_water(out, m, landmat, H, W, seed)
    _tongue(out, m, plan, H, W, seed)
    shelf = _shelf(out, m, dist, top, north, H, W, seed)
    _floes(out, m, dist, shelf, H, W, seed)
    _streaks(out, m & ~shelf, dist, top, st, north, hw, H, W, seed)
    _hole(out, hm, H, W, seed)
    # keep only what differs from the zone's ground near the water, clear elsewhere
    near = ndi.binary_dilation(gw | m | hm, iterations=MARGIN)
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



@lru_cache(maxsize=None)
def _inflow_bg(text):
    """The kit's render of the plan with the inflow's cells (rows 0 to 4) given to the snow beside them,
    so the overlay can lay snow over the cells' old square banks."""
    from scripts.art.kit.build import Kit
    from scripts.art.kit import compose
    plan = json.loads(text)
    g = _grid(plan)
    g2 = g.copy()
    g2[:INFLOW_ROWS][g[:INFLOW_ROWS] == 'i'] = '.'
    kit = Kit()
    legend = {s: kit.ids[n] for s, n in plan['legend'].items()}
    cells = np.array([[legend[ch] for ch in row] for row in g2], np.int32)
    return compose.render(cells, kit, dressing=True)



INFLOW_ROWS = 5



def inflow(seed=421):
    """The frozen rill coming into the tarn from the north gully (zone rows 0 to 4), after the round 2
    audits of #535 (detail R5, logic F1c):
    - its banks wander 2 to 4 texels on the soft grid and its jog west is a bend of radius 12 or more,
      not the cells' L (snow is laid over the cells' old square banks);
    - the ice is the tarn's at this width: one body tone, clear dark ice in short lenses (6 to 14
      texels) along its middle, two or three wandering cracks with a lit texel on their west side;
    - snow banked 2 to 4 texels over each edge, its top lit; the west bank's snow shades the ice east
      of it, the east bank's catches the light on its face;
    - at the frame's top the channel runs in under a drift: a snow lip crossing it, its edge scalloped,
      its 2-texel shaded underside on the ice;
    - at its foot it opens into the tarn, the ice running on into the tarn's own (the kit's fill)."""
    plan = _plan()
    text = _plan_text()
    g = _grid(plan)
    rows = INFLOW_ROWS
    Wz = g.shape[1] * CELL
    H = rows * CELL + 12
    cm = np.zeros(g.shape, bool)
    cm[:rows] = g[:rows] == 'i'
    w = np.kron(cm, np.ones((CELL, CELL), bool))[:H]
    Y, X = np.mgrid[0:H, 0:Wz]
    sd = ndi.distance_transform_edt(w) - ndi.distance_transform_edt(~w)
    sd[rows * CELL - 6:] = 8.0 * (np.abs(X[rows * CELL - 6:] - (w[rows * CELL - 7].nonzero()[0].mean())) < 20) - 4.0
    sd = ndi.gaussian_filter(sd, 9.0)                         # the jog a bend of radius 12 or more
    m = (sd + 2.6 * np.tanh(_noise((H, Wz), 5.0, seed) / 1.2)) > 0
    m = _round(m, 6)
    tarn = np.kron(g[rows:rows + 1] == 'i', np.ones((1, CELL), bool))[0]
    m[rows * CELL:, :] |= tarn[None, :]
    bg = _inflow_bg(text)
    out = np.full((H, Wz), -1, np.int32)
    near = ndi.binary_dilation(w | m, iterations=14) & (Y < rows * CELL + 2)
    out[near & ~m] = bg[:H][near & ~m]
    body = m & (Y < rows * CELL + 2)
    # where the inflow meets the tarn the overlay's ice ends raggedly on the kit's own (the same body tone)
    rng = np.random.default_rng(seed + 1)
    end = rows * CELL - 4 + _walk1d(Wz, rng, -3, 3, (3, 6))
    body &= Y < end[None, :]
    out[body] = C('sky_cool', 4)
    dist = ndi.distance_transform_edt(m)
    # the channel's middle line per row, for the lenses and the cracks
    mid = np.full(H, -1.0)
    for y in range(H):
        cs = np.nonzero(body[y])[0]
        if len(cs):
            mid[y] = (cs.min() + cs.max()) / 2.0
    # clear dark ice in short lenses along the middle
    y = int(rng.integers(10, 18))
    while y < rows * CELL - 14:
        L = int(rng.integers(6, 15))
        wd = float(rng.uniform(1.3, 2.4))
        dx = float(rng.uniform(-7, 7))
        for k in range(L):
            yy = y + k
            if mid[yy] < 0:
                continue
            half = wd * math.sin(math.pi * (k + 0.5) / L)
            xa, xb = int(round(mid[yy] + dx - half)), int(round(mid[yy] + dx + half))
            for xx in range(xa, xb + 1):
                if body[yy, xx]:
                    out[yy, xx] = C('water_cool', 4)
            if half > 1.6 and body[yy, int(round(mid[yy] + dx))]:
                out[yy, int(round(mid[yy] + dx))] = C('sky_cool', 3)
        y += L + int(rng.integers(6, 16))
    # two or three wandering cracks, continuous, each its own length and slant, a lit texel on their west
    # side: one long down the flow, the others shorter and leaving it at a slant
    starts = [(int(rng.integers(14, 30)), float(rng.uniform(-8, -2)), 0.0, int(rng.integers(45, 70)))]
    starts += [(int(rng.integers(40, 80)), float(rng.uniform(2, 10)), float(rng.choice([-0.45, 0.5])), int(rng.integers(12, 26)))
               for _k in range(int(rng.integers(1, 3)))]
    for (y0, dx0, slant, L) in starts:
        if mid[y0] < 0:
            continue
        x = float(mid[y0] + dx0)
        for yy in range(y0, min(H, y0 + L)):
            if mid[yy] < 0:
                break
            x += slant + float(rng.normal(0, 0.55))
            X_ = int(round(x))
            if not (1 <= X_ < Wz - 1 and body[yy, X_] and dist[yy, X_] > 4):
                break
            out[yy, X_] = C('water_cool', 2)
            if out[yy, X_ - 1] not in (C('water_cool', 2),):
                out[yy, X_ - 1] = C('sky_cool', 5)
    # snow banked over each edge, 2 to 4 texels: its top lit; the west bank's shade on the ice east of
    # it, the east bank's face catching the light
    wid = _runs1d(H, rng, 2, 4, (4, 9))
    for yy in range(H):
        cs = np.nonzero(m[yy])[0]
        if not len(cs) or yy >= end.max():
            continue
        lab, n = ndi.label(m[yy])
        for k in range(1, n + 1):
            run = np.nonzero(lab == k)[0]
            a, b = run.min(), run.max()
            if b - a < 12 or a == 0:
                continue
            ww = int(wid[yy])
            out[yy, a:a + ww] = C('snow', 4)
            out[yy, a] = C('snow', 5)
            if body[yy, a + ww]:
                out[yy, a + ww] = C('sky_cool', 3)                 # the shade east of the west bank's snow
            if yy >= rows * CELL - 2:
                continue
            out[yy, b - ww + 1:b + 1] = C('snow', 4)
            out[yy, b - ww + 1] = C('snow', 5)                      # the east bank's snow, lit where it faces west
    # the drift's lip across the channel's top, scalloped, its 2-texel shaded underside
    sc = 7 + np.round(2.2 * np.sin(X[0] / 5.5) + 1.2 * np.sin(X[0] / 2.3 + 1.0)).astype(int)
    for xx in range(Wz):
        if not m[:20, xx].any():
            continue
        e = int(sc[xx])
        out[:e, xx][m[:e, xx]] = C('snow', 4)
        out[max(0, e - 2):e, xx][m[max(0, e - 2):e, xx]] = C('snow', 5)
        for k, c in ((0, C('snow_cool', 3)), (1, C('sky_cool', 3))):
            if e + k < H and m[e + k, xx]:
                out[e + k, xx] = c
    ys, xs = np.nonzero(out >= 0)
    y0, y1, x0, x1 = 0, ys.max() + 1, xs.min(), xs.max() + 1
    p = V.Pic(x1 - x0, y1 - y0, (x1 - x0) // 2, 0)
    p.a[:] = out[y0:y1, x0:x1]
    p.world = (int(x0), int(y0))
    return p



def inflow_at():
    p = inflow()
    return [p.world[0] + p.W // 2, p.world[1]]



THAW_ROWS = 6                     # the band's reach north of the seam (its top edge wanders a cell or two in it)



def _hollows(out, bare, sel=None):
    """A bare patch drawn as a hollow lit from the upper left (R7): a slush wall two texels wide, in
    shade, on its north and west inner edges, a lit rim of one texel on its south and east, and no ring
    elsewhere."""
    sel = bare if sel is None else sel
    nw = sel & (~np.roll(bare, 1, 0) | ~np.roll(bare, 2, 0) | ~np.roll(bare, 1, 1) | ~np.roll(bare, 2, 1))
    se = sel & (~np.roll(bare, -1, 0) | ~np.roll(bare, -1, 1)) & ~nw
    out[nw] = C('snow_cool', 1)
    out[nw & (~np.roll(bare, 1, 0) | ~np.roll(bare, 1, 1))] = C('snow_cool', 2)
    out[se] = C('snow', 5)
    return nw | se



def _earth(out, sel, X, Y, seed, rng, grass=True):
    """Cold wet earth in three or four tones in clusters of two texels or more, with flattened grass in
    short combed strokes lying downhill (R7: not specks)."""
    H, W = out.shape
    # clods: each 2 x 2 (or 2 x 3) cluster one tone, the tones leaning with a soft swell
    blk = K.vhash(X // 2, (Y + (X // 2) % 2) // 2, seed) - 0.5
    n = 0.9 * _noise((H, W), 4.0, seed + 1) + 2.2 * blk
    tone = np.where(n > 0.75, C('earth_cool', 3), np.where(n > -0.15, C('earth_cool', 2),
                    np.where(n > -0.9, C('earth_cool', 1), C('earth', 2))))
    out[sel] = tone[sel]
    if not grass:
        return
    ys, xs = np.nonzero(sel & ndi.binary_erosion(sel, iterations=2))
    for _k in range(len(ys) // 28):
        j = int(rng.integers(0, len(ys)))
        y, x = ys[j], xs[j]
        L = int(rng.integers(3, 6))
        c = C('grass_warm', 0) if rng.random() < 0.55 else C('earth', 3)
        for i in range(L):                                       # combed east and down the slope
            Y_, X_ = y + i // 2, x + i
            if 0 <= Y_ < H and 0 <= X_ < W and sel[Y_, X_]:
                out[Y_, X_] = c
        if 0 <= y + 1 < H and 0 <= x + 2 < W and sel[y + 1, x + 2] and L > 3:
            out[y + 1, x + 1] = c



def _rivulet(out, path, land, stop, bare, wmax=3):
    """One meltwater channel along `path` ((y, x) floats), tapering from a texel at its head to `wmax` at
    its foot: its water water_winter 4, a dark north edge, a lit south line; broken where it crosses a
    bare patch (logic P4); it stops at `stop` (the water)."""
    H, W = out.shape
    n = len(path)
    for i, (y, x) in enumerate(path):
        Y_, X_ = int(round(y)), int(round(x))
        if not (1 <= Y_ < H - 4 and 0 <= X_ < W):
            continue
        if stop[Y_, X_]:
            break
        if bare[Y_, X_]:
            continue
        wd = 1 + int((wmax - 1) * min(1.0, i / max(1.0, 0.6 * n)))
        if land[Y_ - 1, X_] and not bare[Y_ - 1, X_]:
            out[Y_ - 1, X_] = C('water_winter', 2)
        for k in range(wd):
            if land[Y_ + k, X_] or stop[Y_ + k, X_]:
                out[Y_ + k, X_] = C('water_winter', 4) if k < wd - 1 or wd == 1 else C('water_winter', 3)
        if land[Y_ + wd, X_] and not bare[Y_ + wd, X_]:
            out[Y_ + wd, X_] = C('snow', 5)



def _meander(rng, y, x, ty, tx, n, amp):
    """A path from (y, x) toward (ty, tx) that meanders by `amp` texels at a slow period."""
    pts = []
    L = max(1.0, math.hypot(ty - y, tx - x))
    per, ph = rng.uniform(14, 26), rng.uniform(0, 6.3)
    for i in range(n):
        f = i / float(n - 1)
        cy, cx = y + (ty - y) * f, x + (tx - x) * f
        py, px = -(tx - x) / L, (ty - y) / L
        o = amp * math.sin(i / per * 6.283 + ph) * math.sin(math.pi * min(1.0, f * 1.4))
        pts.append((cy + py * o, cx + px * o))
    return pts



def thaw_band(seed=441):
    """The short thaw band at the woodland's north seam (Matt, 23 Nov), after the round 2 audits of #535
    (detail R7, logic P2 and P4), over the zone's whole width:
    - it grows to the south: north of it only a few small patches open, its top edge wandering a cell
      or two; near the seam the patches are large and merge;
    - the crust is a calm wet-snow plane, one body tone (snow_cool 3) with grey staining in soft
      clusters of four texels or more;
    - each bare patch is a hollow lit from the upper left (_hollows), its earth in three or four tones
      in clusters with flattened grass in short combed strokes (_earth);
    - the Col Path keeps a trodden slush lane 36 texels wide running straight to the door, wetter and
      darker than the crust, a slush puddle or two in it;
    - rivulets: one meandering channel each, tapering, a dark north edge and a lit south line, running
      to the outlet's water and broken where they cross a bare patch;
    - the snow pulled back round the feet of the trees on these rows.
    Only land texels are painted (the outlet's water is the outlet piece's)."""
    plan = _plan()
    g = _grid(plan)
    Hz, Wz = g.shape[0] * CELL, g.shape[1] * CELL
    y0 = Hz - THAW_ROWS * CELL
    H, W = Hz - y0, Wz
    Y, X = np.mgrid[0:H, 0:W]
    rng = np.random.default_rng(seed)
    wm = water_mask()[y0:]
    gw = np.kron(g[-(H // CELL):], np.ones((CELL, CELL), object))[-H:]
    land = ~wm & ~ndi.binary_dilation(wm, iterations=2)
    # the band's top edge wanders a cell or two; t runs 0 there to 1 at the seam
    # round 3 (B1): the band fades out inside its own picture: a lobed, wandering edge 12 to 30 texels
    # down, nothing above it, so no row of the box shows as a line on the snow
    edge = np.clip(21.0 + 5.0 * _noise((1, W), 7.0, seed + 11)[0] + 3.0 * _noise((1, W), 2.5, seed + 12)[0], 12, 30)
    top = np.maximum(0.3 * H + 22.0 * _noise((1, W), 40.0, seed + 1)[0] + 8.0 * _noise((1, W), 12.0, seed + 2)[0], edge + 4)
    t = np.clip((Y - top[None, :]) / (H - 4 - top[None, :]), -1.0, 1.0)
    # the door's lane: the Col Path's middle 36 texels, straight to the door cells
    trod_cols = np.nonzero((gw[-1] == 'b'))[0]
    lc = (trod_cols.min() + trod_cols.max() + 1) / 2.0 if len(trod_cols) else W / 2.0
    # the lane tapers into the trod above it over its top 24 texels, its sides wandering 2 to 3 texels
    taper = np.clip((Y - edge[None, :]) / 24.0, 0.0, 1.0)
    half = np.maximum(6.0 + 12.5 * taper + np.round(2.0 * _noise((H, W), 4.0, seed + 3)), np.where(taper >= 1.0, 18.0, 0.0))
    lane = (np.abs(X - lc) <= half) & (Y >= edge[None, :]) & land
    # where the patches open: large and merging near the seam, a few small ones north
    nb = _noise((H, W), 9.0, seed + 4)
    ns = _noise((H, W), 3.5, seed + 5)
    field = 0.8 * nb + 0.3 * ns + 1.55 * t - 1.3
    for p in plan['pieces']:
        if p['piece'] in ('frost_pine', 'frost_pine_squat', 'frost_spruce', 'frost_krummholz', 'frost_snag'):
            fx, fy = p['at'][0], p['at'][1] - y0
            if -10 <= fy <= H + 10:
                field = np.maximum(field, 1.2 * (1.0 - (((X - fx) / 16.0) ** 2 + ((Y - fy) / 7.0) ** 2)) - 0.1)
    bare = land & ~lane & (field > 0)
    bare = _round(bare, 2)
    bare = ndi.binary_opening(bare, iterations=2) & land & ~lane
    lab, n = ndi.label(bare)
    if n:
        sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes >= 30
        bare = keep[lab]
    out = np.full((H, W), -1, np.int32)
    # the crust: one body tone, grey staining in soft clusters; it dissolves into the snow at its top edge
    crust = land & (t + 0.18 * _noise((H, W), 9.0, seed + 6) > 0.02)
    crust = _round(crust, 3) & land
    out[crust] = C('snow_cool', 3)
    stain = crust & (_noise((H, W), 4.0, seed + 7) + 0.6 * t > 1.1)
    stain = ndi.binary_opening(stain, structure=np.ones((2, 2), bool))
    out[stain] = C('snow_cool', 2)
    # the lane: trodden slush, wetter and darker than the crust, ruts along it, a puddle or two
    out[lane] = C('snow_cool', 2)
    slush = lane & (_noise((H, W), 3.0, seed + 8) > 0.6)
    slush = ndi.binary_opening(slush, structure=np.ones((2, 2), bool))
    out[slush] = C('snow_cool', 1)
    yy, side = float(rng.uniform(0, 4)), 1                              # one walker's prints pressed into it
    while yy < H - 3:
        fx = int(round(lc + side * rng.uniform(2, 4) + 3 * math.sin(yy / 23.0)))
        Y_ = int(yy)
        if lane[Y_, fx] and lane[Y_ + 2, fx + 1]:
            out[Y_:Y_ + 2, fx:fx + 2] = C('snow_cool', 1)
            out[Y_ + 2, fx:fx + 2] = C('snow_cool', 3)
        yy += float(rng.uniform(4.5, 7.0))
        side = -side
    for _k in range(2):
        cy, cx = rng.uniform(0.45, 0.85) * H, lc + rng.uniform(-9, 9)
        pud = lane & ((((X - cx) / rng.uniform(6, 9)) ** 2 + ((Y - cy) / rng.uniform(2.5, 3.5)) ** 2
                       + 0.3 * _noise((H, W), 1.5, seed + 9 + _k)) < 1.0)
        out[pud] = C('water_winter', 4)
        out[pud & ~np.roll(pud, 1, 0)] = C('water_winter', 2)              # its wall, shaded north
        out[pud & (~np.roll(pud, -1, 0) | ~np.roll(pud, -1, 1))] = C('snow_cool', 3)   # its far rim lit
    # the bare ground
    _earth(out, bare, X, Y, seed + 10, rng)
    _hollows(out, bare)
    for _k in range(5):                                                       # a stone here and there
        ys, xs = np.nonzero(bare & ndi.binary_erosion(bare, iterations=4))
        if not len(ys):
            break
        j = int(rng.integers(0, len(ys)))
        cy, cx = ys[j], xs[j]
        st = ((X - cx) / rng.uniform(2.2, 3.4)) ** 2 + ((Y - cy) / rng.uniform(1.6, 2.4)) ** 2 < 1.0
        out[st] = C('stone', 3)
        out[st & ((X - cx) + (Y - cy) < -1)] = C('stone', 4)
        out[st & ((X - cx) + (Y - cy) > 1.5)] = C('stone', 2)
        out[np.roll(st, 1, 0) & ~st & bare] = C('earth_cool', 0)
    # rivulets to the water: two each side, meandering downhill to the bank, tapering, broken over bare ground
    wcols = np.nonzero(wm.any(0))[0]
    if len(wcols):
        for side in (-1, 1):
            for k in range(2):
                ys0 = float(rng.uniform(0.2, 0.5) * H)
                xs0 = float(wcols.min() - rng.uniform(30 + 40 * k, 60 + 50 * k)) if side < 0 else \
                    float(wcols.max() + rng.uniform(30 + 40 * k, 60 + 50 * k))
                if side > 0 and abs(xs0 - lc) < 30:
                    xs0 = lc + 40
                ty = min(H - 6.0, ys0 + rng.uniform(30, 55))
                row = np.nonzero(wm[int(ty)])[0]
                if not len(row):
                    continue
                tx = float(row.min() + 1) if side < 0 else float(row.max() - 1)
                path = _meander(rng, ys0, xs0, ty, tx, int(abs(tx - xs0) + abs(ty - ys0)) + 4, float(rng.uniform(2, 4)))
                _rivulet(out, path, land & ~lane, wm, bare, int(rng.integers(2, 4)))
    out[~land & (out >= 0) & wm] = -1
    out[Y < edge[None, :]] = -1
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
    """The woodland's half of the thaw at the Frostline door (round 1 audits of #535; round 2 detail
    R8), over the woodland's north rows from its west edge past the door, drawn over the woodland's own
    baked ground (game/zones/woodland/art/ground.png): old snow lying in the lee (east) of the scree's
    stones and thick along the north edge, thinning south, with no halo (a lit top, a shaded
    north-west lip, a darker wet ring only on its downhill side); meltwater in three meandering
    channels from the snow to the brook's rim; on the lawn's first row the grass flattened and brown.
    Only the texels it changes are opaque. It is registered texel for texel to ground.png: if that
    picture changes (draft #421), regenerate this one."""
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
    # snow: thick at the north edge, thinning south through the scree; in each stone's lee; under a north
    # pine only where its foot stands on the scree (round 2 detail audit, R8: no lone patch on the lawn)
    lee = (np.roll(stone, 2, 1) | np.roll(stone, 3, 1)) & ~stone & scree
    edge = np.clip(1.0 - Y / 90.0, 0, 1)
    snow = scree & ~stone & ((n + 1.8 * edge - 1.3 > 0) | (lee & (n > 0.2 - edge)))
    for (cx, cy) in WOODLAND_CONIFERS:
        under = (((X - cx) / 26.0) ** 2 + ((Y - cy + 6) / 9.0) ** 2 + 0.3 * n) < 1.0
        snow |= under & scree
    snow = ndi.binary_opening(snow, iterations=1) & (codes >= 0) & ~water & ~stone & ~green
    # old snow with no halo (R8): its top lit (the body light, its upper rows lighter still), a shaded
    # north-west lip of one or two texels, and a darker wet ring only on its downhill (south) side
    out[snow] = C('snow', 4)
    upper = snow & np.roll(snow, 2, 0) & np.roll(snow, 3, 0) & ~np.roll(snow, -3, 0)
    out[upper] = C('snow_cool', 4)
    hi = snow & ~np.roll(snow, -2, 0) & np.roll(snow, 1, 0)
    out[snow & (K.vhash(X // 3, Y // 2, seed) > 0.6) & ~hi] = C('snow', 5)
    nw1 = snow & (~np.roll(snow, 1, 0) | ~np.roll(snow, 1, 1))
    nw2 = snow & (~np.roll(snow, 2, 0) | ~np.roll(snow, 2, 1)) & ~nw1 & (K.vhash(X // 2, Y // 2, seed + 4) > 0.5)
    out[nw1] = C('snow_cool', 2)
    out[nw2] = C('snow_cool', 3)
    ring = ~snow & (np.roll(snow, 1, 0) | (np.roll(snow, 2, 0) & (K.vhash(X // 2, Y, seed + 5) > 0.4))) & scree & (tone > 0)
    out[ring] = codes[ring] - 1
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
    # meltwater: three channels from the snow down to the brook's rim, meandering, tapering, a dark
    # north edge and a lit south line (as on the Frostline's side, _rivulet), none crossing another
    wcols = np.nonzero(water[:100].any(0))[0]
    if len(wcols):
        bx0, bx1 = wcols.min(), wcols.max()
        rng = np.random.default_rng(seed + 3)
        land = (codes >= 0) & ~water
        specs = [(-1, float(rng.uniform(60, 85)), float(rng.uniform(12, 22))),
                 (1, float(rng.uniform(25, 40)), float(rng.uniform(10, 18))),
                 (1, float(rng.uniform(85, 120)), float(rng.uniform(30, 45)))]
        for (side, dx, ys0) in specs:
            xs0 = bx0 - dx if side < 0 else bx1 + dx
            ty = ys0 + dx * float(rng.uniform(0.5, 0.8))
            row = np.nonzero(water[int(min(H - 4, ty))])[0]
            if not len(row):
                continue
            tx = float(row.min()) if side < 0 else float(row.max())
            path = _meander(rng, ys0, xs0, ty, tx, int(abs(tx - xs0) + abs(ty - ys0)) + 4, float(rng.uniform(2, 3.5)))
            _rivulet(out, path, land, water, stone, 3)
    p = V.Pic(W, H, 0, 0)
    p.a[:] = out
    return p
