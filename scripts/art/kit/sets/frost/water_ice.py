"""Frostline open water, cut ice and frozen falls."""
from __future__ import annotations

from ._shared import (
    C,
    FACE_PX,
    K,
    LIP_PX,
    V,
    _drift_west,
    hsh,
    math,
    ndi,
    np,
)

# ------------------------------------------------------------------------------------------------
# the ice-cutter's sledge and the cut blocks (F-S1, B4)
# ------------------------------------------------------------------------------------------------
ICE = [('water_cool', 'sky_cool', 'sky_cool')]



def _ice_faces(sc, a, seed):
    """The cut blocks drawn as translucent lake ice: a frosted lit top plane, front faces in bands
    deepening downward, a lit west edge, a dark east face, saw-cut striations, a crack line and air
    bubbles in clusters."""
    rng = np.random.default_rng(seed)
    ids = [i for i, s_ in enumerate(sc.solids) if s_.tag == 'ice']
    for i in ids:
        m = sc.label == i
        if not m.any():
            continue
        nz, ny, nx = sc.n[..., 2], sc.n[..., 1], sc.n[..., 0]
        topm = m & (nz > 0.6)
        front = m & (ny > 0.5) & ~topm
        eastm = m & (nx > 0.5) & ~topm
        a[topm] = np.where(sc.gy[topm] < np.median(sc.gy[topm]) if topm.any() else False, C('snow', 5), C('snow', 4))
        if front.any():
            ys, xs = np.nonzero(front)
            yt, yb = ys.min(), ys.max()
            v = (ys - yt) / max(1, yb - yt)
            band = np.where(v < 0.25, C('sky_cool', 5), np.where(v < 0.55, C('sky_cool', 4), np.where(v < 0.85, C('sky_cool', 3),
                                                                                                             C('water_cool', 3))))
            a[ys, xs] = band
            xl = xs.min()
            a[ys[xs == xl], xl] = C('snow_cool', 4)                               # the lit west edge
            stri = ((ys - yt) % 4 == 2) & (xs > xl + 1) & (np.array([hsh(seed, x // 3, i) for x in xs]) > 0.35)
            a[ys[stri], xs[stri]] = np.where(v[stri] < 0.5, C('sky_cool', 3), C('water_cool', 2))
            # a crack and a cluster of bubbles
            cx = int(rng.integers(xs.min() + 2, max(xs.min() + 3, xs.max() - 2)))
            for k_ in range(int((yb - yt) * 0.7)):
                y = yt + 1 + k_
                x = cx + (k_ // 3) % 2
                if 0 <= y < a.shape[0] and front[y, x]:
                    a[y, x] = C('sky_cool', 2)
            bx, by = int(rng.integers(xs.min() + 2, max(xs.min() + 3, xs.max() - 3))), int(yt + (yb - yt) * 0.6)
            for dx, dy in ((0, 0), (2, -1), (1, 2)):
                if 0 <= by + dy < a.shape[0] and 0 <= bx + dx < a.shape[1] and front[by + dy, bx + dx]:
                    a[by + dy, bx + dx] = C('sky_cool', 5)
        if eastm.any():
            a[eastm] = C('water_cool', 2)



def _line(a, p0, p1, code, w=1):
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
    for t in np.linspace(0, 1, n):
        x = int(round(p0[0] + (p1[0] - p0[0]) * t))
        y = int(round(p0[1] + (p1[1] - p0[1]) * t))
        for k_ in range(w):
            if 0 <= y < a.shape[0] and 0 <= x + k_ < a.shape[1]:
                a[y, x + k_] = code



def ice_stack(seed=59):
    """The ice-cut's stack on the shore: cut blocks in two courses, frosted on top, a little snow
    blown against their west end."""
    sc = K.Scene(-40, 40, -24, 14, 80)
    blocks = [(-26, -12, 0, -9, 2, 14), (-7, -13, 0, 10, 1, 13), (12, -11, 0, 28, 3, 15), (-17, -10, 14, 0, 0, 26),
              (3, -11, 13, 19, -1, 25)]
    for (x0, y0, z0, x1, y1, z1) in blocks:
        sc.box(x0, y0, z0, x1, y1, z1, ICE, base=3.4, k=1.3, tag='ice', round_=1.2)
    _drift_west(sc, -28, 0, 7, seed)
    sc.render()
    a = sc.shade(crevice=1.0, rim=0.6)
    _ice_faces(sc, a, seed)
    V.tidy(a)
    V.outline(a)
    return K.crop(a, sc.ox, sc.oy)



def _icefall(a, fall, seed):
    """The outlet frozen over the face (round 3, R2-F3): bulging columns of ice of different widths
    that swell, pinch and merge into curtains, each lit on its west edge (snow 5, then frost white)
    and turning blue to a shaded east side; the lanes inside a column fall in long streaks; icicle
    clusters hang from the frozen lip, snow lies on its crown, and the ice spreads at the foot into
    an apron that meets the channel. Rock shows between the columns' pinches and at the edges."""
    H, W = a.shape
    rng = np.random.default_rng(seed + 31)
    f0, f1 = fall
    yf = LIP_PX + FACE_PX
    y_top, y_bot = LIP_PX - 6, yf + 1
    # columns: (centre, half width, bulge phase, bulge size, period); they overlap into curtains
    cols = []
    x = f0
    while x < f1 - 4:
        w = float(rng.choice([rng.uniform(4, 6), rng.uniform(6, 9), rng.uniform(9, 14)], p=[0.3, 0.45, 0.25]))
        w = min(w, max(3.0, (f1 - x) / 2.0))
        cols.append((x + w, w, rng.uniform(0, 2 * math.pi), rng.uniform(0.12, 0.3), rng.uniform(34, 70)))
        x += 2 * w - rng.uniform(0.5, 2.5)
    yy = np.arange(H)
    v = np.clip((yy - y_top) / float(y_bot - y_top), 0, 1)
    edges = []
    tops = []
    for j, (cx, hw, ph, bs, per) in enumerate(cols):
        # (round 5) each curtain narrower up at the lip, where the rock shows between them, and
        # built up thick and wide at the foot; its top bulging out over the lip by its own height
        wy = hw * (1 + bs * np.sin(2 * math.pi * yy / per + ph)) * (0.55 + 0.75 * v ** 1.3)
        cxy = cx + 1.2 * np.sin(2 * math.pi * yy / (per * 1.6) + ph * 0.7)
        L_ = np.round(ndi.uniform_filter1d(cxy - wy, 5)).astype(int)
        R_ = np.round(ndi.uniform_filter1d(cxy + wy, 5)).astype(int)
        q = 6 + j % 3                                     # the edges step every six to eight rows
        idx_ = np.clip(((yy + j * 2) // q) * q, 0, H - 1)
        L_, R_ = L_[idx_], R_[idx_]
        edges.append((L_, R_))
        tops.append(LIP_PX - 3 + int(rng.integers(0, 4)) if rng.random() < 0.45 else LIP_PX + int(rng.integers(3, 15)))
    # paint each column from its west edge (lit) to its east edge (shade); the body in lanes that
    # stay put (their tone steps only every 8 to 30 texels down), so the ice falls in streaks
    body = [C('snow', 5), C('snow', 4), C('snow', 4), C('snow_cool', 4), C('snow_cool', 4), C('sky_cool', 5), C('sky_cool', 5),
            C('sky_cool', 4), C('sky_cool', 3), C('sky_cool', 2)]
    icem = np.zeros((H, W), bool)
    for (L_, R_), t0 in zip(edges, tops):
        lm, rm = float(L_[y_top:y_bot].mean()), float(R_[y_top:y_bot].mean())
        for y in range(max(0, t0), y_bot):
            l, r = int(L_[y]), int(R_[y])
            if y - t0 < 3:                                   # the bulge's rounded crown
                l, r = l + (3 - (y - t0)), r - (3 - (y - t0))
                if r - l < 1:
                    continue
            for x in range(max(0, l), min(W, r + 1)):
                d, e = x - l, r - x
                if d == 0:
                    c = C('snow', 5)
                elif d <= 2:
                    c = C('snow', 4) if d == 1 or hsh(seed, x, y // 9) > 0.3 else C('snow', 5)
                elif e <= 1 + int(3.5 * x / W):
                    sg = (y + int(hsh(seed, x, 3) * 20)) // 11
                    c = (C('sky_cool', 2), C('water_cool', 3), C('sky_cool', 2), C('sky_cool', 3), C('water_cool', 2),
                         C('water', 3), C('water_cool', 4))[int(hsh(seed, x, sg, 4) * 7)] if e > 0 else C('sky_cool', 2)
                else:
                    ln = (x * 5 + int(hsh(seed, x // 2) * 3)) // 7
                    sg = (y + int(hsh(seed, ln, 1) * 30)) // (8 + int(hsh(seed, ln, 2) * 22))
                    # across the column the lanes go from frost white to blue shade, a step either way
                    rel = (x - lm) / max(1.0, rm - lm)
                    k_ = int(round(rel * 8.5 + 6.6 * x / W - 3.0 + (hsh(seed, ln, sg) - 0.5) * 2.2))
                    c = body[max(0, min(len(body) - 1, k_))]
                a[y, x] = c
                icem[y, x] = True
    # (Matt's review of round 3: why is one part frozen and the other not?) fast water freezes last:
    # the fall still runs in one narrow column down its middle, dark and quick, white where it
    # breaks; the ice either side is its frozen flows and icicle curtains
    cxw = (f0 + f1) / 2.0 + 3
    for y in range(y_top, y_bot):
        v_ = (y - y_top) / float(y_bot - y_top)
        yq = (y // 6) * 6                                    # the flow's banks step every six rows
        half = 5.0 + 1.5 * math.sin(yq / 9.0) + 2.5 * v_
        c0 = cxw + 3.0 * math.sin(yq / 17.0 + 1.0) + 1.2 * math.sin(yq / 6.0)
        l_, r_ = int(round(c0 - half)), int(round(c0 + half))
        for x in range(max(0, l_ - 1), min(W, r_ + 2)):
            if x == l_ - 1 or x == r_ + 1:
                a[y, x] = C('sky_cool', 3)                          # the ice's wet edge on the flow
                continue
            ln = (x * 3 + int(hsh(seed, x) * 5)) // 4
            sg = (y + int(hsh(seed, ln, 31) * 24)) // (6 + int(hsh(seed, ln, 32) * 14))
            g = hsh(seed, ln, sg, 33)
            rel = (x - l_) / max(1.0, r_ - l_)
            if rel < 0.2:
                c = C('snow', 5) if g > 0.4 else C('sky_cool', 5)
            elif g > 0.8:
                c = C('snow', 5)                                    # the water breaking white
            elif g > 0.6:
                c = C('water', 4)
            elif rel > 0.65:
                c = C('water_cool', 2) if g > 0.25 else C('sky_cool', 2)
            else:
                c = C('water', 2) if g > 0.3 else C('water', 3)
            a[y, x] = c
    # spray and rime at the foot: a soft cloud over the plunge, frost feathers on the ice beside it
    for y in range(y_bot - 16, y_bot + 1):
        for x in range(max(0, int(cxw) - 16), min(W, int(cxw) + 17)):
            d = ((x - cxw) / 15.0) ** 2 + ((y - y_bot + 3) / 10.0) ** 2
            if d < 1.0 and y < yf - 6 and hsh(seed, x // 2, y // 8, 40) > 0.25 + 0.6 * d:
                a[y, x] = C('snow', 5) if d < 0.45 else C('snow_cool', 4)
    # the lip over the fall: the upper tier's snow running to the edge in one soft mass per column
    # (no rows of shade under it here: the ice and the rime take its place)
    for x in range(max(0, f0), min(W, f1)):
        col = np.nonzero(icem[:, x])[0]
        t = int(col.min()) if len(col) else LIP_PX
        for y in range(4, min(t, LIP_PX + 1)):
            a[y, x] = C('snow', 5) if y < 6 else C('snow', 4)
    # the rock between the curtains: wet granite glazed with rime in streaks down the fall line
    for x in range(max(0, f0), min(W, f1)):
        ln = x // 2
        for y in range(LIP_PX, y_bot):
            if icem[y, x] or a[y, x] < 0:
                continue
            sg = (y + int(hsh(seed, ln, 51) * 40)) // 40
            g = hsh(seed, ln, sg, 53)
            a[y, x] = C('slate', 3) if g < 0.4 else (C('slate', 4) if g < 0.75 else C('snow_cool', 3))
    # the frozen lip: snow lying on each curtain's bulging crown (it follows the ice, not a ruler);
    # between the curtains an uneven fringe of icicles hangs over the bare rock from the lip
    for x in range(W):
        col = np.nonzero(icem[:, x])[0]
        if len(col):
            t = int(col.min())
            hcap = 3
            for k_ in range(hcap):
                y = t - hcap + 1 + k_
                if 0 <= y < H:
                    a[y, x] = C('snow', 5) if k_ == 0 else C('sky_cool', 5)
        elif f0 <= x < f1 and hsh(seed, x // 2, 7) > 0.35:
            ln = 3 + int(15 * hsh(seed, x, 8) ** 1.6)
            for k_ in range(ln):
                y = LIP_PX - 1 + k_
                if y < H:
                    a[y, x] = C('sky_cool', 5) if k_ < ln - 2 else C('sky_cool', 4)
    # the apron at the foot: the ice spreading in a low mound across the channel, lit on its top
    for x in range(max(0, f0 - 4), min(W, f1 + 4)):
        e = min(x - (f0 - 4), (f1 + 4) - x)
        h = int(round(min(9.0, 6 + e * 0.6) + 2.0 * hsh(seed, x // 5, 8)))
        for k_ in range(h):
            y = yf + 1 - h + k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5) if k_ == 0 else (C('snow', 4) if k_ < h - 2 else
                                                        (C('sky_cool', 4), C('water_cool', 4), C('sky_cool', 3), C('water', 4),
                                                         C('sky_cool', 5))[int(hsh(seed, x // 3, 9) * 5)])



# ------------------------------------------------------------------------------------------------
# open water in a frozen country (Matt's review of round 3): still water freezes first and fast water
# last, so the outlet is ice with a narrow dark lead of running water down its middle
# ------------------------------------------------------------------------------------------------
LEAD_WATER = [C('slate_cool', 1), C('slate', 1), C('slate_cool', 2), C('slate', 2), C('sky_cool', 2)]



def _lead_mask(H, W, seed, width=(5.0, 9.0), close=(), ends=True):
    """A lead's open water down a picture H tall: a channel that meanders a texel or two, swells and
    narrows, pinched shut at its ends (and where `close` lists rows, an ice bridge across it)."""
    rng = np.random.default_rng(seed)
    yy = np.arange(H)
    cx = W / 2.0 + 1.6 * np.sin(yy / 11.0 + rng.uniform(0, 6)) + 0.8 * np.sin(yy / 4.3 + rng.uniform(0, 6))
    w = width[0] + (width[1] - width[0]) * (0.5 + 0.5 * np.sin(yy / 13.0 + rng.uniform(0, 6)))
    if ends:
        # (round 5) wide through its middle, tapering gradually to a rounded end, not a sliver
        t = (yy + 0.5) / H
        w = np.maximum(0.0, w * np.sin(math.pi * t) ** 0.45 + 1.0) * (np.minimum(yy, H - 1 - yy) >= 1)
    for (c0, c1) in close:
        w[c0:c1] = 0
    w = ndi.uniform_filter1d(w, 3)
    L = np.round(cx - w / 2).astype(int)
    R = np.round(cx + w / 2).astype(int)
    m = np.zeros((H, W), bool)
    for y in range(H):
        if R[y] - L[y] >= 2:
            m[y, max(0, L[y]):min(W, R[y])] = True
    return m



def _paint_lead(a, m, seed):
    """Open water under shelf ice: a calm dark centre, lighter shallows at its edges, a faint line of
    current; the shelf's snow-covered lip round it (lit on the west and north), the lip's shadow
    lying on the water under its south-facing edges, and a stone breaking the ice here and there."""
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W]
    dist = ndi.distance_transform_edt(m)
    a[m] = np.where(dist[m] <= 1, C('sky_cool', 2), np.where(dist[m] <= 2, C('slate', 2), C('slate_cool', 1)))
    cur = m & (dist >= 2) & ((X + (Y // 7)) % 5 == 0) & (K.vhash(X, Y // 4, seed) > 0.55)
    a[cur] = C('slate', 2)
    l1 = ndi.binary_dilation(m, iterations=1) & ~m
    grow = K.vhash(X // 3, Y // 3, seed + 3) > 0.45
    lip = l1 | (ndi.binary_dilation(l1, iterations=1) & ~m & grow)
    lip2 = ndi.binary_dilation(lip, iterations=1) & ~m & ~lip & (K.vhash(X // 2, Y // 3, seed + 4) > 0.4)
    north = lip & np.roll(m, -1, 0) & ~np.roll(m, 1, 0)
    a[lip] = C('snow', 4)
    a[lip & np.roll(m, 1, 1)] = C('snow_cool', 3)                       # the east lip, facing west in shade
    a[lip & np.roll(m, -1, 1)] = C('snow', 5)                           # the west lip, lit
    a[lip2] = C('snow_cool', 4)
    shade = m & np.roll(lip, 1, 0) & (dist <= 2)                         # the lip's shadow on the water
    a[shade] = C('slate_cool', 0)
    a[north] = C('snow', 5)
    # small shelves of ice overhanging the water here and there, their shade on it
    rng = np.random.default_rng(seed + 9)
    edge = m & ~ndi.binary_erosion(m)
    ys, xs = np.nonzero(edge)
    for k in range(max(1, len(ys) // 18)):
        j = int(rng.integers(0, len(ys)))
        cy, cx = ys[j], xs[j]
        r = rng.uniform(1.4, 2.6)
        bump = ((Y - cy) ** 2 + (X - cx) ** 2 <= r * r) & m
        a[bump] = C('snow_cool', 4)
        a[bump & ~np.roll(bump, 1, 0)] = C('snow', 5)
        under = np.roll(bump, 1, 0) & m & ~bump
        a[under] = C('slate_cool', 0)



def lead(kind='run', seed=137):
    """A lead of open water in the frozen outlet (ground dressing laid on the ice): `run` three cells
    long, `short` two, `long` four with an ice bridge, `pool` the fall's plunge pool, half open under
    an ice rim with rime from the spray, `gap` the inflow's one dark gap."""
    if kind == 'pool':
        H, W = 2 * 24 + 6, 3 * 24 + 6
        a = np.full((H, W), -1, np.int32)
        Y, X = np.mgrid[0:H, 0:W]
        nz = ndi.gaussian_filter(np.random.default_rng(seed).random((H, W)), 4.0)
        nz = (nz - nz.mean()) / (nz.std() + 1e-9)
        d = ((X - W / 2) / (W / 2 - 3)) ** 2 + ((Y - H / 2) / (H / 2 - 3)) ** 2 + 0.1 * nz
        # (round 5) the plunge pool: an irregular open hole in the ice shelf where the fall lands,
        # a little north of the shelf's middle; a lit rim of ice round it (lit north and west, in
        # shade south and east), its interior dark and deepest at the middle; rime on the shelf
        dh = ((X - W * 0.48) / (W * 0.3)) ** 2 + ((Y - H * 0.42) / (H * 0.3)) ** 2 + 0.18 * nz
        hole = dh < 1.0
        dist = ndi.distance_transform_edt(hole)
        a[hole] = np.where(dist[hole] <= 1, C('sky_cool', 2), np.where(dist[hole] <= 3, C('slate', 2), C('slate_cool', 1)))
        a[hole & (dist > 5)] = C('slate_cool', 0)
        rim = ndi.binary_dilation(hole, iterations=2) & ~hole
        lit_side = (X - W * 0.48) / (W * 0.3) + (Y - H * 0.42) / (H * 0.3) < 0
        a[rim] = np.where(lit_side[rim], C('snow', 5), C('sky_cool', 4))
        sh_ = np.roll(rim & lit_side, 1, 0) & hole
        a[sh_] = C('slate_cool', 0)                                          # the rim's shadow inside
        shelf = (d < 1.0) & (a < 0)
        gs = ndi.gaussian_filter(np.random.default_rng(seed + 5).random((H, W)), 2.0)
        gs = (gs - gs.mean()) / (gs.std() + 1e-9)
        a[shelf] = np.where(gs[shelf] > 0.9, C('snow', 5), np.where(gs[shelf] > -0.7, C('snow_cool', 4), C('sky_cool', 5)))
        return _pic(a)
    if kind in ('strip', 'strip_long'):
        # laid over a one-cell channel of the kit's water: the shelf ice grown in from both sides
        # covers the cell to its edges, the lead open down its middle and running off the zone's edge
        H, W = (60 if kind == 'strip' else 120), 24
        m = _lead_mask(H, W, seed + H, (6.0, 10.0), ends=False)
        a = np.full((H, W), -1, np.int32)
        _paint_lead(a, m, seed)
        Y, X = np.mgrid[0:H, 0:W]
        shelf = a < 0
        g = K.vhash((X + Y // 4) // 4, Y // 3, seed + 6)
        a[shelf] = np.where(g[shelf] > 0.85, C('sky_cool', 5), np.where(g[shelf] > 0.45, C('water_cool', 4), C('sky_cool', 4)))
        return _pic(a)
    if kind == 'gap':
        H, W = 24, 16
        m = _lead_mask(H, W, seed, (3.0, 5.0))
    else:
        H = {'short': 72, 'run': 96, 'long': 120}[kind]
        W = 24
        close = ((44, 52),) if kind == 'long' else ()
        m = _lead_mask(H, W, seed + H, (7.0, 12.0), close=close)
    a = np.full((H, W), -1, np.int32)
    _paint_lead(a, m, seed)
    return _pic(a)



def _pic(a):
    H, W = a.shape
    p = V.Pic(W, H, W // 2, H - 1)
    p.a[:] = a
    return p
