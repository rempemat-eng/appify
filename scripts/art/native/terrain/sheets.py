"""Periodic source sheets the tiles are cut from (each tiles seamlessly with itself).

face_sheet: packed rounded boulders, the cliff face. Every boulder is a cell of a weighted
Voronoi packing on a torus, shaded as a pillow (dome normal from its own distance field,
light from the upper left, hard steps between tones), with a crevice on its upper-left
boundary and an underside on its lower edge, sibling clusters on its skin, moss on a few
caps. The face tiles are 16 px windows of this sheet anchored to the world, so boulders run
across tile borders and no column or course appears.
"""
import numpy as np
from scipy import ndimage as ndi

from .. import ctx
from ..palette import C, FI, FAMS as FAMS_, step
from ..ctx import D, P

# r6 style constants (the 2x kit reads these)
_SS = ctx.BIOME.get('style', {}).get('stone', {})
STONE = dict(_SS.get('ramp', dict(cap=0.86, body=0.62, shade=0.36)))     # r6: stone_paint's tone thresholds on the light
STONE_MOSS = _SS.get('moss', 0.16)      # r6: share of face boulders with a moss crown
SHEET_TUFTS = []     # r4: world positions of the lawn's tuft clumps (for objects.json)
FAMSIB = {'crag': 'crag_cool', 'crag_cool': 'crag', 'crag_warm': 'crag', 'stone': 'stone_cool',
          'stone_cool': 'stone', 'stone_warm': 'stone'}   # r8: a stone's sibling hue for its shade
STONE_TEX = dict(_SS.get('texture', dict(bulge=22, pit=14, chip=36, lichen=45)))    # r7: world px² of stone per texture mark
STONE_MOTTLE = _SS.get('mottle', 0.35)      # r9: share of shade and body under a sibling-hue mottle
JOINT_W = int(_SS.get('joint_px', 2))       # r9: art px of the joint between two whole boulders
STONE_SPLIT = _SS.get('split', 6.0)      # r8: boulders wider than this (world px radius) may split into overlapping lumps
SHEET_TUFTS = []     # r4: world positions of the lawn's tuft clumps (for objects.json)
BUSY = ctx.BIOME.get('lawn', {}).get('busy', 0.8)      # lawn mottle share in the busy half
FINE = ctx.BIOME.get('lawn', {}).get('fine', 0.7)
TUFTG = ctx.BIOME.get('lawn', {}).get('tuft_spacing', 6.8)    # tuft clump spacing (world px)

L3 = np.array([-0.55, -0.62, 0.56])
L3 = L3 / np.linalg.norm(L3)


def _rng(seed):
    return np.random.default_rng(seed)


def place_boulders(W, H, seed, n_try=6000, rmin=5.0, rmax=15.0):
    """Ellipses on a torus: (x, y, rx, ry, a). Bigger first, then smaller ones fill in."""
    rng = _rng(seed)
    out = []
    for k in range(n_try):
        frac = k / n_try
        r = rmax - (rmax - rmin) * min(1.0, frac * 3.0) - rng.random() * 2.0
        r = max(rmin, r)
        asp = 0.75 + 0.6 * rng.random()          # rx/ry: some lumps tall, most a little wide
        rx, ry = r * (asp ** 0.5) * 1.1, r / (asp ** 0.5)
        x, y = rng.random() * W, rng.random() * H
        ok = True
        for (bx, by, brx, bry, _a) in out:
            dx = min(abs(x - bx), W - abs(x - bx))
            dy = min(abs(y - by), H - abs(y - by))
            if (dx / (0.70 * (rx + brx))) ** 2 + (dy / (0.70 * (ry + bry))) ** 2 < 1.0:
                ok = False
                break
        if ok:
            out.append((x, y, rx, ry, rng.random()))
    return out


def face_sheet(W=None, H=None, seed=7, moss=0.12, rmin=5.0, rmax=15.0):
    """Rounded boulders stacked like a scree-built crag: drawn top to bottom, so each lump's
    round top sits in front of the underside of the one above. Shaded as a dome."""
    W = W or P(128)
    H = H or P(64)
    if True and D > 1:
        return face_sheet_px(W, H, seed, rmin, rmax)
    rng = _rng(seed + 1)
    # the same boulders at every density: positions and radii scale with D
    bs = [(x * D, y * D, rx * D, ry * D, a) for (x, y, rx, ry, a) in place_boulders(128, 64, seed, rmin=rmin, rmax=rmax)]
    n = len(bs)
    order = sorted(range(n), key=lambda i: bs[i][1] + bs[i][3] * 0.6)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    bid = np.full((H, W), -1, np.int32)
    U = np.zeros((H, W))
    V = np.zeros((H, W))
    DXC = np.zeros((H, W))
    DYC = np.zeros((H, W))
    for i in order:
        bx, by, rx, ry, _a = bs[i]
        dx = (xx - bx + W / 2) % W - W / 2
        dy = (yy - by + H / 2) % H - H / 2
        u, v = dx / rx, dy / ry
        # a soft superellipse: rounder than a diamond, fuller than an ellipse
        d = (np.abs(u) ** 2.4 + np.abs(v) ** 2.4) ** (1 / 2.4)
        m = d <= 1.0
        bid[m] = i
        U[m] = u[m]
        DXC[m] = -dx[m]
        DYC[m] = -dy[m]
        V[m] = v[m]
    def lamb(u, v):
        r2 = np.clip(u ** 2 + v ** 2, 0, 0.98)
        return u * L3[0] + v * L3[1] + np.sqrt(1 - r2) * L3[2]
    lam_px = np.where(bid >= 0, lamb(U, V), -1)
    # facets: each lump is cut into 4 to 7 flat facets, toned by the light at the facet's
    # centre, so it reads as broken rock rather than a smooth ball; the rim stays round
    lam = lam_px.copy()
    fid = np.full((H, W), -1, np.int32)
    rngf = _rng(seed + 9)
    nf_total = 0
    for i in range(n):
        m = bid == i
        if m.sum() < 12 * D * D:
            continue
        area = m.sum() / (D * D)
        k = int(np.clip(area / 24, 3, 14)) + int(rngf.integers(0, 2)) if D == 1 else \
            int(np.clip(area / 15, 3, 26)) + int(rngf.integers(0, 2))
        ang = rngf.random(k) * 2 * np.pi
        rad = np.sqrt(rngf.random(k)) * 0.85
        fu, fv = rad * np.cos(ang), rad * np.sin(ang) * 1.3
        uu, vv = U[m], V[m]
        dd = (uu[:, None] - fu[None]) ** 2 + ((vv[:, None] - fv[None]) * 1.4) ** 2
        j = dd.argmin(1)
        # a facet tilts towards its own centre: lit when it faces up-left
        lf = lamb(fu * 1.15, fv * 1.15)[j]
        rr = np.sqrt(uu ** 2 + vv ** 2)
        lam[m] = np.where(rr > 0.86, lam_px[m], 0.8 * lf + 0.2 * lam_px[m])
        fid[m] = nf_total + j
        nf_total += k
    fams = ['crag', 'crag_warm', 'crag_cool']
    bfam = [fams[int(b[4] * 3) % 3] for b in bs]
    boff = [(-1 if b[4] > 0.85 else 0) for b in bs]
    tone = np.full((H, W), 3)
    tone[lam > 0.80] = 4
    tone[lam < 0.58] = 2
    tone[lam < 0.32] = 1
    rr = np.sqrt(U ** 2 + V ** 2)
    big = np.zeros((H, W), bool)
    for i in range(n):
        if min(bs[i][2], bs[i][3]) > 8 * D:
            big |= bid == i
    tone[big & (lam > 0.93) & (rr > 0.55)] = 5
    code = np.full((H, W), C('crag', 0))
    for i in range(n):
        m = bid == i
        code[m] = FI[bfam[i]] * 8 + np.clip(tone[m] + boff[i], 1, 5)
    # skin clusters: sibling swaps, a few lit flecks and pits (2 to 3 px)
    edge_any = np.zeros((H, W), bool)
    for sy, sx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        edge_any |= np.roll(bid, (sy, sx), (0, 1)) != bid
    for _ in range(int(W * H * 0.13)):
        y, x = rng.integers(0, H), rng.integers(0, W)
        if bid[y, x] < 0 or edge_any[y, x]:
            continue
        shape = [(0, 0), (0, 1)] if rng.random() < 0.6 else [(0, 0), (1, 0)]
        if rng.random() < 0.3:
            shape = shape + [(1, 1)]
        r = rng.random()
        for dy, dx in shape:
            y2, x2 = (y + dy) % H, (x + dx) % W
            if bid[y2, x2] != bid[y, x] or edge_any[y2, x2]:
                continue
            c = code[y2, x2]
            f, t = c // 8, c % 8
            if r < 0.55:
                cur = [k for k, v in FI.items() if v == f][0]
                nf = FI[fams[(fams.index(cur) + 1 + (x2 + y2) % 2) % 3]] if cur in fams else f
                code[y2, x2] = nf * 8 + t
            elif r < 0.78 and lam[y, x] > 0.65:
                code[y2, x2] = f * 8 + min(5, t + 1)
            elif lam[y, x] < 0.8:
                code[y2, x2] = f * 8 + max(1, t - 1)
    # facet joints: a crack (tone -1) along the lower-right side of each facet joint and a
    # lit lip (tone +1) on the upper-left side, so a lump reads as split rock
    fup, fleft = np.roll(fid, 1, 0), np.roll(fid, 1, 1)
    same_b = (np.roll(bid, 1, 0) == bid) & (np.roll(bid, 1, 1) == bid)
    joint = (fid >= 0) & same_b & ((fid != fup) | (fid != fleft))
    jn = _noise(W, H, seed + 7, 2.0 * D)
    crackm = joint & (jn > np.percentile(jn, 35))
    code[crackm] = np.where(code[crackm] % 8 > 1, code[crackm] - 1, code[crackm])
    lip = np.roll(crackm, -1, 0) & ~crackm & (fid >= 0) & (lam > 0.55)
    code[lip] = np.where(code[lip] % 8 < 5, code[lip] + 1, code[lip])
    # outlines between lumps: the front lump's rim is a crevice (tone 0) on its upper-left
    # and an underside (tone 1) on its lower right
    up, left = np.roll(bid, 1, 0), np.roll(bid, 1, 1)
    down, right = np.roll(bid, -1, 0), np.roll(bid, -1, 1)
    crev = (bid >= 0) & ((bid != up) | (bid != left))
    under = (bid >= 0) & ((bid != down) | (bid != right)) & ~crev
    code[under] = np.where(code[under] % 8 > 1, code[under] // 8 * 8 + 1, code[under])
    code[crev] = C('crag', 0)
    # moss: a cushion on the crown of a few lumps, following the lump's own top curve, lit
    # above, its lower edge ragged with short hanging tips, a dark line beneath
    mn = _noise(W, H, seed + 5, 1.0 * D)
    mossy = [i for i in range(n) if rng.random() < moss]
    if True:
        mossy = []          # r2: no turf-slab moss cushions on the face lumps
    for i in mossy:
        lo = -0.62 - 0.12 * (mn > 0.5)
        m = (bid == i) & (V < lo) & (np.abs(U) < 0.6) & ~crev
        if m.sum() < 4 * D * D:
            continue
        code[m] = np.where(lam[m] > 0.78, C('leaf', 4), C('leaf', 3))
        tips = np.roll(m, 1, 0) & ~m & (bid == i) & (mn > 0.5)
        code[tips] = C('leaf', 2)
        below = np.roll(m | tips, 1, 0) & ~(m | tips) & (bid == i)
        code[below] = C('crag', 1)
    # lichen crusts on the lit crowns and damp stains on the shaded undersides: small
    # clusters (2 to 4 px) in the families that belong with rock (grass_cool, earth)
    FX = True
    for _ in range(int(W * H * 0.022 * (1.0 if D == 1 else (1.0 if FX else 1.6)))):
        y, x = int(rng.integers(0, H)), int(rng.integers(0, W))
        if bid[y, x] < 0 or crev[y, x]:
            continue
        lit = lam[y, x] > 0.7
        shp = [(0, 0), (0, 1)] + ([(1, 0)] if rng.random() < 0.5 else []) + ([(1, 1)] if rng.random() < 0.3 else [])
        for dy, dx in shp:
            y2, x2 = (y + dy) % H, (x + dx) % W
            if bid[y2, x2] != bid[y, x] or crev[y2, x2]:
                continue
            t = code[y2, x2] % 8
            if lit:
                code[y2, x2] = C('grass_cool', int(np.clip(t - 1, 2, 4))) if (rng.random() < 0.5 and not FX) else C('earth_warm', int(np.clip(t, 2, 5)))
            else:
                code[y2, x2] = C('earth_cool', int(np.clip(t, 1, 3))) if rng.random() < 0.6 else C('crag_cool', max(0, t - 1))
    # no speckle: a lone pixel (unlike all four neighbours) takes the colour of the pixel
    # above it, unless it is a crevice
    for _ in range(2):
        nb = [np.roll(code, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
        lone = (code != nb[0]) & (code != nb[1]) & (code != nb[2]) & (code != nb[3]) & ~crev
        code = np.where(lone, nb[0], code)
    aux = {'bid': bid, 'lam': lam, 'U': U, 'V': V, 'crev': crev, 'dxc': DXC, 'dyc': DYC}
    return code, aux


def stone_paint(code, m, U, V, fam, rng, big=True, glint=True):
    """r6: one stone in pixel-art manner (shared by the face sheet, the loose boulders and the
    bank stones): a 4-tone ramp lit from the upper left with a soft, clustered terminator (no
    hard bands, no facet lines), a small glint on big stones, and cluster texture: pits (a dark
    pair with a lit pixel under it), chips (a lit cluster near the lit rim), lichen in small
    clumps on the lit top, a little moss in the shade. Writes into code where m."""
    H, W = code.shape
    r2 = np.clip(U ** 2 + V ** 2, 0, 0.98)
    lam = U * L3[0] + V * L3[1] + np.sqrt(1 - r2) * L3[2]
    blob = ndi.gaussian_filter(rng.random((H, W)), 1.1 * D)
    blob = (blob - blob[m].mean()) / (blob[m].std() + 1e-6) if m.any() else blob
    lamn = lam + 0.075 * blob
    t = np.full((H, W), 3)
    t[lamn > STONE['cap']] = 4
    t[lamn < STONE['body']] = 2
    t[lamn < STONE['shade']] = 1
    # a lit crescent just inside the upper-left rim (Eastward's cobbles), a tone up
    er = ndi.binary_erosion(m, iterations=max(1, int(round(1.5 * D))))
    crest = m & ~er & (lam > 0.45) & (U + V < -0.25)
    t[crest] = np.minimum(5, t[crest] + 1)
    if glint and big:
        t[(lamn > 0.97) & m] = 5
    f = FI[fam]
    code[m] = f * 8 + t[m]
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    area = len(ys) / (D * D)
    # pits: a dark pair over a lit pixel, on the body and the lit side
    Y_, X_ = np.mgrid[0:H, 0:W]
    # r7: secondary bulges: soft blobs a tone up on the lit side, a tone down in the shade, so
    # no single tone covers a big field
    for _ in range(int(area / STONE_TEX['bulge'])):
        k = int(rng.integers(0, len(ys)))
        y, x = ys[k], xs[k]
        rb = rng.uniform(1.2, 2.6) * D
        bb = ((Y_ - y) ** 2 + (X_ - x) ** 2 <= rb * rb) & m
        sel = bb & (code // 8 == f)
        if lam[y, x] <= STONE['shade'] + 0.1:
            # r8: in the deep shade a bulge is a sibling hue at the same tone (variety without
            # lightening the shaded side, which read as light from the east)
            sib_ = FAMSIB.get(FAMS_[f], FAMS_[f])
            code[sel] = FI[sib_] * 8 + code[sel] % 8
            continue
        dt = 1 if lam[y, x] > 0.6 else -1
        code[sel] = f * 8 + np.clip(code[sel] % 8 + dt, 1, 5)
        edge_b = bb & ~ndi.binary_erosion(bb) & (code // 8 == f)
        if dt > 0:
            lo = edge_b & (Y_ > y + rb * 0.4)
            code[lo] = f * 8 + np.clip(code[lo] % 8 - 1, 1, 5)
    # r9: soft mottles of the sibling hue over the shade and the body (no new lines, no new
    # tones), so no one colour covers a big field
    if STONE_MOTTLE > 0:
        mot = ndi.gaussian_filter(rng.random((H, W)), 1.3 * D)
        sel_ = m & (code // 8 == f) & np.isin(code % 8, (1, 2, 3))
        if sel_.any():
            q_ = np.quantile(mot[sel_], 1 - STONE_MOTTLE)
            sw = sel_ & (mot > q_)
            code[sw] = FI[FAMSIB.get(FAMS_[f], FAMS_[f])] * 8 + code[sw] % 8
    # pits: a dark pair over a lit pixel, on the body and the lit side
    for _ in range(int(area / STONE_TEX['pit'])):
        k = int(rng.integers(0, len(ys)))
        y, x = ys[k], xs[k]
        if t[y, x] < 2:
            continue
        for (dy, dx, dt) in ((0, 0, -1), (0, 1, -1), (1, 1, 1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < H and 0 <= X < W and m[Y, X]:
                code[Y, X] = f * 8 + int(np.clip(t[Y, X] + dt, 1, 5))
    # chips: a small lit cluster near the lit rim
    rim_lit = m & (lam > 0.7) & ~ndi.binary_erosion(m, iterations=max(2, int(2.5 * D)))
    cy_, cx_ = np.nonzero(rim_lit)
    for _ in range(int(area / STONE_TEX['chip']) + 1 if len(cy_) else 0):
        k = int(rng.integers(0, len(cy_)))
        y, x = cy_[k], cx_[k]
        for (dy, dx) in ((0, 0), (0, 1), (1, 0)):
            Y, X = y + dy, x + dx
            if 0 <= Y < H and 0 <= X < W and m[Y, X]:
                code[Y, X] = f * 8 + min(5, t[Y, X] + 1)
    # lichen on the lit top, moss in the shade: small clumps
    for _ in range(int(area / STONE_TEX['lichen'])):
        k = int(rng.integers(0, len(ys)))
        y, x = ys[k], xs[k]
        lit = lam[y, x] > 0.72
        if not lit:
            continue                  # (no moss specks on the face: they read as green dots)
        cl = [(0, 0), (0, 1)] + ([(1, 0)] if rng.random() < 0.6 else []) + ([(1, 1), (0, 2)] if rng.random() < 0.4 else [])
        for (dy, dx) in cl:
            Y, X = y + dy, x + dx
            if 0 <= Y < H and 0 <= X < W and m[Y, X]:
                code[Y, X] = C('earth_warm', int(np.clip(t[Y, X], 2, 4))) if lit else C('leaf', 2 if t[Y, X] <= 1 else 3)


def split_boulder(code, m, U, V, fam, rr, rx, ry, k=2, theta=0.0):
    """r8: a big boulder painted as k (2 or 3) overlapping lumps along an axis at angle theta:
    each lump its own rounded mass (a wobbled ellipse, shaded by stone_paint), the lower lump in
    front. Where a front lump overlaps the one behind, the gap is a curved crevice 1 to 3 px
    wide following the front lump's outline (tone 0 at its core, a tone-1 shade beyond it), and
    the front lump's top edge is lit. Returns (crevice core, crevice shade, lit rim) masks."""
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    au, av = np.cos(theta), np.sin(theta) * 0.7
    if k == 2:
        offs, rfs = [-0.36, 0.38], [0.68, 0.60]
    else:
        offs, rfs = [-0.52, 0.04, 0.56], [0.56, 0.52, 0.48]
    subs = []
    for j in range(k):
        subs.append((offs[j] * au + rr.uniform(-0.05, 0.05),
                     offs[j] * av + rr.uniform(-0.05, 0.05) + (-0.14 if j == 0 else 0.06 * j),
                     rfs[j] * rr.uniform(0.94, 1.06), rr.random() * 6.28))
    order = sorted(range(k), key=lambda j_: subs[j_][1])       # back (higher) first
    own = np.full((H, W), -1)
    masks = {}
    for j in order:
        ox, oy, rf, ph = subs[j]
        uu, vv = (U - ox) / rf, (V - oy) / (rf * 0.9)
        th = np.arctan2(vv, uu)
        wob = 1.0 + 0.025 * np.sin(2 * th + ph)              # r9: near-convex (S-shaped gaps read as pillows)
        mj = m & (uu * uu + vv * vv <= (1.08 * wob) ** 2)
        own[mj] = j
        masks[j] = mj
    miss = m & (own < 0)
    if miss.any():
        dd = np.stack([((U - o) / r_) ** 2 + ((V - p) / r_) ** 2 for (o, p, r_, _) in subs])
        own[miss] = np.argmin(dd[:, miss], 0)
    for j in range(k):
        ox, oy, rf, _ = subs[j]
        mj = own == j
        uu, vv = (U - ox) / rf, (V - oy) / (rf * 0.9)
        r_ = np.sqrt(uu * uu + vv * vv)
        s_ = np.where(r_ > 0.98, 0.98 / np.maximum(r_, 1e-6), 1.0)     # round, not clipped square
        stone_paint(code, mj, uu * s_, vv * s_, fam, rr, big=True, glint=(j == order[0]))
    core = np.zeros((H, W), bool)
    shade = np.zeros((H, W), bool)
    rim = np.zeros((H, W), bool)
    nz = ndi.gaussian_filter(rr.random((H, W)), 1.4 * D)
    nz = (nz - nz.min()) / (np.ptp(nz) + 1e-6)
    wv = 1.4 + 1.6 * nz                                              # 1.4 to 3 px, varying along the gap
    for pos, j in enumerate(order[1:], 1):
        front = own == j
        behind = m & np.isin(own, order[:pos])
        if not front.any() or not behind.any():
            continue
        dt = ndi.distance_transform_edt(~front)
        core |= behind & (dt <= wv * 0.7)
        shade |= behind & (dt > wv * 0.7) & (dt <= wv + 1.0)
        P_ = np.pad(behind, 1)
        rim |= front & (P_[:-2, 1:-1] | P_[1:-1, :-2]) & ~ndi.binary_erosion(front)
    return core, shade, rim & ~core


def face_sheet_px(W, H, seed, rmin, rmax):
    """r6 (1.5x and 2x): the same boulders as the 1x face sheet, in pixel-art stone: irregular
    silhouettes, stone_paint shading and texture, a crevice on each lump's upper left and an
    underside on its lower right; no facet net, no crack lines."""
    rng = _rng(seed + 1)
    bs = [(x * D, y * D, rx * D, ry * D, a) for (x, y, rx, ry, a) in place_boulders(128, 64, seed, rmin=rmin, rmax=rmax)]
    n = len(bs)
    order = sorted(range(n), key=lambda i: bs[i][1] + bs[i][3] * 0.6)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    bid = np.full((H, W), -1, np.int32)
    U = np.zeros((H, W)); V = np.zeros((H, W)); DXC = np.zeros((H, W)); DYC = np.zeros((H, W))
    for i in order:
        bx, by, rx, ry, a_ = bs[i]
        dx = (xx - bx + W / 2) % W - W / 2
        dy = (yy - by + H / 2) % H - H / 2
        u, v = dx / rx, dy / ry
        th = np.arctan2(v, u)
        ph = a_ * 6.28
        wob = 1.0 + 0.07 * np.sin(3 * th + ph) + 0.045 * np.sin(5 * th + 2.1 * ph) + 0.03 * np.sin(8 * th + ph * 3.3)
        d = (np.abs(u) ** 2.3 + np.abs(v) ** 2.3) ** (1 / 2.3) / wob
        m = d <= 1.0
        bid[m] = i
        U[m] = u[m] / wob[m]
        V[m] = v[m] / wob[m]
        DXC[m] = -dx[m]
        DYC[m] = -dy[m]
    fams = ['crag', 'crag_warm', 'crag_cool']
    code = np.full((H, W), C('crag', 0))
    rr = np.random.default_rng(seed + 31)
    sub_crev = np.zeros((H, W), bool)
    sub_rim = np.zeros((H, W), bool)
    sub_shade = np.zeros((H, W), bool)
    for i in range(n):
        m = bid == i
        if not m.any():
            continue
        fam = fams[int(bs[i][4] * 3) % 3]
        bx, by, rx, ry, a_ = bs[i]
        # r8: only the larger boulders split (2 lumps, 3 for the largest), about a third stay
        # whole, and the split axis turns by the golden angle from boulder to boulder
        rw = min(rx, ry) / D
        hq = ((i * 2654435761) >> 7) % 3
        if rw <= STONE_SPLIT or (rw <= STONE_SPLIT + 3 and hq == 0) or hq == 1 and rw <= STONE_SPLIT + 6:
            stone_paint(code, m, U, V, fam, rr, big=min(rx, ry) > 8 * D)
            continue
        kk = 3 if rw > STONE_SPLIT + 6 else 2
        sc, shd, rim = split_boulder(code, m, U, V, fam, rr, rx, ry, k=kk, theta=(i * 2.39996) % np.pi)
        sub_crev |= sc
        sub_shade |= shd
        sub_rim |= rim
    up, left = np.roll(bid, 1, 0), np.roll(bid, 1, 1)
    down, right = np.roll(bid, -1, 0), np.roll(bid, -1, 1)
    crev = (bid >= 0) & ((bid != up) | (bid != left))
    if JOINT_W > 1:
        # r9: the joint between two whole boulders lies on the boulder behind, 2 px wide with a
        # tone-1 shade beyond it; about a third of the pairs simply overlap (shade only, no line)
        rank = np.zeros(n + 1, int)
        for r_, i_ in enumerate(order):
            rank[i_] = r_ + 1
        rk = np.where(bid >= 0, rank[np.maximum(bid, 0)], 0)
        dmin = np.full((H, W), 99)
        pair = np.full((H, W), -1)
        for k_ in range(1, JOINT_W + 2):
            for ax_, sg in ((0, 1), (0, -1), (1, 1), (1, -1)):
                nb_ = np.roll(bid, sg * k_, ax_)
                nr_ = np.roll(rk, sg * k_, ax_)
                hit = (bid >= 0) & (nb_ >= 0) & (nb_ != bid) & (nr_ > rk) & (dmin == 99)
                dmin[hit] = k_
                pair[hit] = (np.minimum(bid, nb_) * 131 + np.maximum(bid, nb_))[hit]
        overlap_only = (((pair * 2654435761) >> 9) % 3 == 0) & (pair >= 0)
        jcore = (dmin <= JOINT_W) & ~overlap_only
        jshade = (dmin == JOINT_W + 1) | ((dmin <= JOINT_W) & overlap_only)
        crev = ((bid >= 0) & ((up < 0) | (left < 0))) | jcore
    under = (bid >= 0) & ((bid != down) | (bid != right)) & ~crev
    code[under] = np.where(code[under] % 8 > 1, code[under] // 8 * 8 + 1, code[under])
    # the underside a second px dark at 2x, so each lump sits on the one below
    under2 = np.roll(under, -1, 0) & (bid >= 0) & ~crev & ~under & (bid == np.roll(bid, -1, 0))
    code[under2] = np.where(code[under2] % 8 > 2, code[under2] - 1, code[under2])
    code[crev] = C('crag', 0)
    if JOINT_W > 1:
        js_ = jshade & ~crev
        code[js_] = np.where(code[js_] % 8 > 1, code[js_] - 1, code[js_])
    code[sub_crev & ~crev] = C('crag', 0)
    sh_ = sub_shade & ~crev & ~sub_crev
    code[sh_] = np.where(code[sh_] % 8 > 1, code[sh_] // 8 * 8 + 1, code[sh_])   # the gap's shade on the lump behind
    lit_rim = sub_rim & ~crev & ~sub_crev
    code[lit_rim] = np.where(code[lit_rim] % 8 < 5, code[lit_rim] + 1, code[lit_rim])   # a lit rim on each lower lump's top
    crev = crev | sub_crev
    # r6: a little moss on some boulders' crowns, in soft clumps (never single green dots)
    for i in range(n):
        if rr.random() > STONE_MOSS:
            continue
        m = (bid == i) & (V < -0.55) & (np.abs(U) < 0.55) & ~crev
        if m.sum() < 10 * D * D:
            continue
        # r8: a cap that follows the lump's crown (an arc over its top), ragged below, never square
        nz = ndi.gaussian_filter(rr.random((H, W)), 0.8 * D)
        nz = (nz - nz[m].mean()) / (nz[m].std() + 1e-6)
        u0 = rr.uniform(-0.2, 0.15)
        cap = ((U - u0) / 0.34) ** 2 + ((V + 0.92) / 0.22) ** 2 <= 1.0 + 0.3 * nz
        mm = m & cap
        mm = ndi.binary_opening(mm, iterations=1)
        code[mm] = np.where(U[mm] + V[mm] < -0.75, C('leaf', 4), C('leaf', 3))
        rim_ = np.zeros_like(mm)
        rim_[1:] = mm[:-1]
        rim_ &= ~mm & (bid == i) & ~crev
        code[rim_] = C('leaf', 2)
    for _ in range(2):
        nb = [np.roll(code, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
        lone = (code != nb[0]) & (code != nb[1]) & (code != nb[2]) & (code != nb[3]) & ~crev
        code = np.where(lone, nb[0], code)
    lam = np.where(bid >= 0, U * L3[0] + V * L3[1] + np.sqrt(np.clip(1 - U ** 2 - V ** 2, 0.02, 1)) * L3[2], -1)
    aux = {'bid': bid, 'lam': lam, 'U': U, 'V': V, 'crev': crev, 'dxc': DXC, 'dyc': DYC}
    return code, aux


def _noise(W, H, seed, sigma):
    rng = _rng(seed)
    a = rng.random((H, W))
    return ndi.gaussian_filter(a, sigma, mode='wrap')


GRASS_MARKS = [
    # rows of (dy, dx, what): 'd' dark blade (one tone down), 'D' deep blade (the leaf ramp,
    # one tone down), 'l' lit tip (one up), 's' sibling swap at the same tone
    ((0, 0, 'd'), (1, 0, 'd')),
    ((0, 1, 'l'), (1, 0, 'd'), (1, 1, 'd')),
    ((0, 0, 'l'), (1, 0, 'd')),
    ((0, 0, 'D'), (1, 0, 'D'), (1, 1, 'd')),
    ((0, 0, 'l'), (0, 1, 'l')),
    ((0, 0, 's'), (0, 1, 's'), (1, 1, 's')),
    ((0, 0, 's'), (1, 0, 's')),
    ((0, 0, 'd'), (0, 2, 'd'), (1, 1, 'D'), (1, 0, 'd'), (1, 2, 'd')),
]


def snow_sheet(W=64, H=64, seed=5):
    """One calm plane (snow 3) with broad swells a tone lighter and soft blue-violet hollows
    on the cool sibling, a few sparkles in pairs."""
    W, H = P(W), P(H)
    rng = _rng(seed)
    n1 = _noise(W, H, seed, 8 * D)
    n2 = _noise(W, H, seed + 2, 4 * D)
    code = np.full((H, W), C('snow', 3))
    code[n1 > np.percentile(n1, 58)] = C('snow', 4)
    code[(n1 < np.percentile(n1, 20))] = C('snow_cool', 3)
    for _ in range(int(W * H * 0.004)):
        y, x = rng.integers(0, H), rng.integers(0, W)
        code[y, x] = C('snow', 5)
        code[y, (x + 1) % W] = C('snow', 5)
    return code


# --- density-native grass and dirt: the same marks at the same world spots, drawn crisply ----
def _blade(code, y0, x0, Lp, H, W, fn, lean):
    """A 1 px blade of Lp px rising from (y0, x0), leaning one px over its length."""
    for i in range(Lp):
        y = (y0 - i) % H
        x = (x0 + (lean if i >= Lp // 2 else 0)) % W
        code[y, x] = fn(code[y, x])
        if i == Lp // 2 and lean:
            code[y, (x0) % W] = fn(code[y, (x0) % W])


def grass_sheet_d(W=64, H=64, seed=3, fam='grass', base_tone=3, density=1.0, calm=1.0):
    """grass_sheet at density D: the same random marks at the same world positions as at 1x,
    drawn natively: blades as 1 px strokes D to 2D tall (lit tips as short dashes on top),
    sibling swaps as D x D cells, so the lawn keeps its liveliness and gains crispness."""
    Ww, Hw = W, H
    W, H = P(W), P(H)
    rng = _rng(seed)
    n1 = _noise(W, H, seed, 6 * D)
    sibs = [fam, fam + '_warm', fam + '_cool']
    names = [C(n, 0) // 8 for n in sibs]
    code = np.full((H, W), C(fam, base_tone))
    code[n1 < np.percentile(n1, 35)] = C(fam + '_cool', base_tone)
    _noise(Ww, Hw, seed + 1, 5)        # keep the random stream as at 1x
    g = 3
    dk = lambda c: step(c, -1)
    lt = lambda c: step(c, 1)
    deep = lambda c: C('leaf', max(1, c % 8 - 1))
    Dp = max(1, int(round(D)))
    for gy in range(0, Hw, g):
        for gx in range(0, Ww, g):
            if rng.random() > 0.95 * density * calm:
                continue
            yw, xw = gy + int(rng.integers(0, g)), gx + int(rng.integers(0, g))
            mk = GRASS_MARKS[int(rng.integers(0, len(GRASS_MARKS)))]
            # where a column of the mark has stacked blade cells, one longer blade
            for dy, dx, d in mk:
                Y, X = int((yw + dy) * D) % H, int((xw + dx) * D) % W
                lean = 1 if ((xw + dx + yw) % 3 == 0) else (-1 if (xw + dx) % 4 == 0 else 0)
                if d == 's':
                    for a in range(Dp):
                        for b in range(Dp):
                            yy, xx = (Y + a) % H, (X + b) % W
                            c = code[yy, xx]
                            f = c // 8
                            if f in names:
                                code[yy, xx] = names[(names.index(f) + 1 + (xx // Dp) % 2) % 3] * 8 + c % 8
                elif d in ('d', 'D'):
                    _blade(code, (Y + Dp - 1) % H, X + (Dp // 2), P(1.6), H, W, deep if d == 'D' else dk, lean)
                else:          # a lit tip: a short dash
                    for b in range(Dp):
                        code[Y % H, (X + b) % W] = lt(code[Y % H, (X + b) % W])
    # an extra pass (only at density): sibling-hue blades on a 2 world px grid, the fine leaf
    # texture Eastward's lawns carry, shape without value noise
    rng2 = _rng(seed + 401)
    for gy in range(0, Hw, 2):
        for gx in range(0, Ww, 2):
            if rng2.random() > 0.88:
                continue
            Y = int((gy + rng2.random() * 2) * D) % H
            X = int((gx + rng2.random() * 2) * D) % W
            c = code[Y, X]
            f = c // 8
            if f not in names:
                continue
            nf = names[(names.index(f) + 1 + int(rng2.integers(0, 2))) % 3]
            sib_fn = lambda cc, nf=nf: nf * 8 + cc % 8 if (cc // 8) in names else cc
            _blade(code, Y, X, P(1.4), H, W, sib_fn, int(rng2.integers(-1, 2)))
    # small two-pixel leaf marks between the blades (Eastward's lawn mottle): half sibling swaps,
    # half a tone down; never single pixels
    for _ in range(int(W * H / 26) if D >= 2 else 0):
        Y, X = int(rng2.integers(0, H)), int(rng2.integers(0, W))
        c = code[Y, X]
        f = c // 8
        if f not in names:
            continue
        horiz = rng2.random() < 0.7
        cells_ = ((0, 0), (0, 1)) if horiz else ((0, 0), (1, 0))
        down = rng2.random() < 0.45
        nf = names[(names.index(f) + 1 + int(rng2.integers(0, 2))) % 3]
        for a, b in cells_:
            yy, xx = (Y + a) % H, (X + b) % W
            cc = code[yy, xx]
            if cc // 8 in names:
                code[yy, xx] = step(cc, -1) if down else nf * 8 + cc % 8
    for _ in range(int(Ww * Hw / 14 * density * calm)):
        yw, xw = int(rng.integers(0, Hw)), int(rng.integers(0, Ww))
        horiz = rng.random() < 0.5
        Y, X = int(yw * D), int(xw * D)
        cells = [(0, b) for b in range(2 * Dp)] if horiz else [(a, 0) for a in range(2 * Dp)]
        for a, b in cells:
            yy, xx = (Y + a) % H, (X + b) % W
            c = code[yy, xx]
            f = c // 8
            if f in names:
                code[yy, xx] = names[(names.index(f) + 2) % 3] * 8 + c % 8
    # no lone pixels
    for _ in range(2):
        nb = [np.roll(code, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
        lone = (code != nb[0]) & (code != nb[1]) & (code != nb[2]) & (code != nb[3])
        code = np.where(lone, nb[0], code)
    return code


def path_sheet_d(W=64, H=64, seed=11, fam='path', body=4):
    """path_sheet at density D: the same grit, dents, pebbles and cracks at the same world spots,
    drawn natively (dashes 2 world px long, pebbles as lit-over-dark lumps, 1 px cracks)."""
    Ww, Hw = W, H
    W, H = P(W), P(H)
    rng = _rng(seed)
    n1 = _noise(W, H, seed, 6 * D)
    sibs = [fam, fam + '_warm', fam + '_cool']
    names = [C(n, 0) // 8 for n in sibs]
    code = np.full((H, W), C(fam, body))
    code[n1 > np.percentile(n1, 66)] = C(fam + '_warm', body)
    code[n1 < np.percentile(n1, 26)] = C(fam + '_cool', body)
    Dp = max(1, int(round(D)))
    # clods: soft lumps of a sibling with a shaded lower rim (trodden earth, not flat)
    rng3 = _rng(seed + 503)
    for _ in range(int(Ww * Hw / 40)):
        cyw, cxw = rng3.random() * Hw, rng3.random() * Ww
        rx, ry = rng3.uniform(1.6, 3.2) * D, rng3.uniform(1.0, 2.0) * D
        Yc, Xc = int(cyw * D), int(cxw * D)
        f0 = code[Yc % H, Xc % W] // 8
        nf = names[(names.index(f0) + 1 + int(rng3.integers(0, 2))) % 3] if f0 in names else f0
        for a in range(-int(ry) - 1, int(ry) + 2):
            for b in range(-int(rx) - 1, int(rx) + 2):
                if (b / rx) ** 2 + (a / ry) ** 2 <= 1:
                    yy, xx = (Yc + a) % H, (Xc + b) % W
                    code[yy, xx] = nf * 8 + code[yy, xx] % 8
                    if (b / rx) ** 2 + ((a + 1) / ry) ** 2 > 1 and a > 0:
                        code[yy, xx] = step(code[yy, xx], -1)
    for _ in range(int(Ww * Hw / 70) if False else 0):
        cyw, cxw = rng3.random() * Hw, rng3.random() * Ww
        for q in range(int(rng3.integers(1, 3))):
            pw_, ph_ = int(rng3.integers(2, 4)) * Dp, int(rng3.integers(1, 3)) * Dp
            Y0, X0 = int((cyw + q * 0.8) * D), int((cxw + q * 3.2) * D)
            fam_s = ('stone_warm', 'stone', 'path_warm')[int(rng3.integers(0, 3))]
            for a in range(ph_ + 1):
                for b in range(pw_):
                    if (a in (0, ph_) and b in (0, pw_ - 1)):
                        continue
                    yy, xx = (Y0 + a) % H, (X0 + b) % W
                    if a == ph_:
                        code[yy, xx] = step(code[yy, xx], -2)
                    else:
                        code[yy, xx] = C(fam_s, 5 if (a == 0 and b < pw_ // 2) else (4 if a < ph_ - 1 else 2))
    keep = 0.8 if False else 0.4
    for gy in range(0, Hw, 4):
        for gx in range(0, Ww, 4):
            if rng.random() > keep:
                continue
            yw, xw = gy + int(rng.integers(0, 4)), gx + int(rng.integers(0, 4))
            Y, X = int(yw * D) % H, int(xw * D) % W
            r = rng.random()
            if r < 0.45:
                f = code[Y, X] // 8
                nf = names[(names.index(f) + 1) % 3] if f in names else f
                for b in range(2 * Dp):
                    code[Y, (X + b) % W] = nf * 8 + code[Y, (X + b) % W] % 8
            elif r < 0.8:
                for b in range(2 * Dp):
                    code[Y, (X + b) % W] = step(code[Y, (X + b) % W], -1)
                for b in range(1, 2 * Dp - 1):
                    code[(Y - 1) % H, (X + b) % W] = step(code[(Y - 1) % H, (X + b) % W], 1) if Dp > 1 else code[(Y - 1) % H, (X + b) % W]
            elif r < 0.93:
                pw, ph = 2 * Dp, Dp + 1
                for a in range(ph):
                    for b in range(pw):
                        if (a == 0 and b in (0, pw - 1)) or (a == ph - 1 and b in (0, pw - 1)):
                            continue
                        yy, xx = (Y + a) % H, (X + b) % W
                        code[yy, xx] = step(code[yy, xx], 1 if a < ph - 1 else -2)
                for b in range(1, pw + 1):
                    yy, xx = (Y + ph) % H, (X + b) % W
                    code[yy, xx] = step(code[yy, xx], -1)
            else:
                n = 3 + int(rng.integers(0, 2))
                for i in range(int(n * D)):
                    yy, xx = (Y + int(i / D) // 2) % H, (X + i) % W
                    code[yy, xx] = step(code[yy, xx], -1)
    if D >= 2 and True and False:
        # Eastward's packed earth: faint rounded cells about 7 world px across, each with a
        # broken shaded rim low-right and a lit fleck high-left (tileable Voronoi)
        rng5 = _rng(seed + 1301)
        n = int(Ww * Hw / 42)
        pts = np.stack([rng5.random(n) * H, rng5.random(n) * W], 1)
        yy, xx = np.mgrid[0:H, 0:W]
        from scipy.spatial import cKDTree
        # periodic: query against the points and their 8 wrapped copies
        offs = [(dy, dx) for dy in (-H, 0, H) for dx in (-W, 0, W)]
        allp = np.concatenate([pts + np.array(o) for o in offs])
        dd, ii = cKDTree(allp).query(np.stack([yy.ravel(), xx.ravel()], 1), k=2)
        best = dd[:, 0].reshape(H, W); second = dd[:, 1].reshape(H, W)
        idx = (ii[:, 0] % n).reshape(H, W)
        border = (second - best) < 1.0 * D
        cy = pts[idx, 0]; cx = pts[idx, 1]
        oy = (yy - cy + H / 2) % H - H / 2; ox = (xx - cx + W / 2) % W - W / 2
        gate = ((((yy // (2 * Dp)) * 7 + (xx // (2 * Dp)) * 13 + idx * 5) % 2) == 0)
        low = border & (oy + ox * 0.6 > 0) & gate
        code[low] = np.vectorize(lambda c: step(c, -1))(code[low])
        hi = (best > 1.2 * D) & (best < 2.4 * D) & (oy < 0) & (ox < 0) & ((idx % 3) == 0) & ((xx + yy) % 2 == 0)
        code[hi] = np.vectorize(lambda c: step(c, 1))(code[hi])
    if D > 1:
        # Eastward's trodden earth: short worn streaks along the walk (lit), heel dents (dark),
        # and grit in two-pixel pairs of three tones; small pebble trios with a lit cap
        rng4 = _rng(seed + 907)
        for _ in range(int(W * H / (60 if False else 150))):
            Y, X = int(rng4.integers(0, H)), int(rng4.integers(0, W))
            r = rng4.random()
            if r < 0.35:
                L = int(rng4.integers(2, 5)) * Dp
                for i in range(L):
                    yy, xx = (Y + i // (2 * Dp)) % H, (X + i) % W
                    code[yy, xx] = step(code[yy, xx], 1)
            elif r < 0.6:
                for a in range(Dp):
                    for b in range(Dp + 1):
                        code[(Y + a) % H, (X + b) % W] = step(code[(Y + a) % H, (X + b) % W], -1)
                code[(Y - 1) % H, (X + 1) % W] = step(code[(Y - 1) % H, (X + 1) % W], -2)
            elif r < 0.85:
                t = (-2, -1, 1)[int(rng4.integers(0, 3))]
                horiz = rng4.random() < 0.7
                for i in range(2):
                    yy, xx = (Y + (0 if horiz else i)) % H, (X + (i if horiz else 0)) % W
                    code[yy, xx] = step(code[yy, xx], t)
            elif False:
                for q in range(3):
                    yy, xx = (Y + (q % 2)) % H, (X + 2 * q) % W
                    fs = ('stone', 'stone_warm', 'stone_cool')[q]
                    code[yy, xx] = C(fs, 5)
                    code[yy, (xx + 1) % W] = C(fs, 3)
                    code[(yy + 1) % H, xx] = step(code[(yy + 1) % H, xx], -2)
                    code[(yy + 1) % H, (xx + 1) % W] = step(code[(yy + 1) % H, (xx + 1) % W], -2)
    for _ in range(2):
        nb = [np.roll(code, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
        lone = (code != nb[0]) & (code != nb[1]) & (code != nb[2]) & (code != nb[3])
        code = np.where(lone, nb[0], code)
    return code


# --- r1 (Matt via the coordinator, 21 Oct): Eastward's grass method at 1.5x and 2x -------------
def _z(a):
    return (a - a.mean()) / (a.std() + 1e-9)


def grass_field_d(W=320, H=832, seed=3, fam='grass', base_tone=3, density=1.0, mottle=0.30, tufts=True):
    """A lawn as large as the canvas (no tile, no repeat), in Eastward's manner: one base tone
    with a fine low-contrast mottle (sibling ramps at the same tone, in 1 to 3 world px
    flecks), a few soft blotches a tone up (sun) or down (shade) with an in-between sibling
    rim, and the texture in tufts of 4 to 7 curved blades (dark at the root, lit at the tip)
    10 to 20 world px apart in loose drifts. No streak hatch. `tufts=False` leaves them out (the
    village at density 3 dresses its lawn itself: town.lawn_detail_hd)."""
    Ww, Hw = W, H
    W, H = P(W), P(H)
    rng = _rng(seed)
    g4 = lambda s, sig: ndi.gaussian_filter(_rng(s).random((H // 4 + 1, W // 4 + 1)), sig * D / 4)
    up = lambda a: ndi.zoom(a, 4, order=1)[:H, :W]
    yy_, xx_ = np.mgrid[0:H, 0:W]
    def wfield(sig, sd):
        # a smooth field laid out in world px (the same at every density), sampled at art px
        a = _z(ndi.gaussian_filter(_rng(sd).random((Hw + 8, Ww + 8)), sig))
        return ndi.map_coordinates(a, [(yy_ + 0.5) / D + 4, (xx_ + 0.5) / D + 4], order=1)
    warmth = wfield(13.0, seed + 1)
    fine = _z(ndi.gaussian_filter(rng.random((H, W)), FINE * D))
    code = np.full((H, W), C(fam, base_tone))
    # fine mottle at the base tone: warm flecks where the field is warm, cool where it is cool.
    # No blotches (r2): shade belongs to casters, and the 1x master has none. A slow mask (about
    # 80 world px) leaves about half the field near flat, so the lawn has large calm areas.
    # r4: the calm is a large-scale mask (30 to 60 world px): about half the field is near flat,
    # and the mottle gathers in the other half (Eastward's lawns)
    from scipy.special import ndtri
    calmm = wfield(24.0, seed + 5)
    sm = np.clip((calmm + 0.15) / 0.65, 0, 1)
    sm = sm * sm * (3 - 2 * sm)
    frac = BUSY - (BUSY - 0.05) * sm
    fl = fine > ndtri(1 - frac)
    code[fl & (warmth >= 0)] = C(fam + '_warm', base_tone)
    code[fl & (warmth < 0)] = C(fam + '_cool', base_tone)
    for _ in range(2):
        nb = [np.roll(code, sh, ax) for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1))]
        lone = (code != nb[0]) & (code != nb[1]) & (code != nb[2]) & (code != nb[3])
        code = np.where(lone, nb[0], code)
    if not tufts:
        return code
    # r3: tufts gather in clumps of 2 to 5 round sparse centres, with calm lawn between the
    # clumps (Eastward), thinned further by a drift noise so whole stretches stay quiet
    drift = up(_z(g4(seed + 3, 16)))
    g = TUFTG / max(0.6, density)
    rt = _rng(seed + 4)
    for cy in np.arange(0, Hw, g):
        for cx in np.arange(0, Ww, g):
            yw, xw = cy + rt.random() * g, cx + rt.random() * g
            Yc, Xc = int(yw * D), int(xw * D)
            if not (0 <= Yc < H and 0 <= Xc < W):
                continue
            if rt.random() > (0.42 + 0.38 * np.tanh(drift[Yc, Xc])) * (1.1 - 0.9 * sm[Yc, Xc]):
                continue           # r4: the calm stretches keep few tuft clumps
            n = int(rt.choice([2, 3, 3, 4, 5]))
            for _ in range(n):
                ty, tx = yw + rt.normal(0, 2.6), xw + rt.normal(0, 3.6)
                Yb, Xb = int(ty * D), int(tx * D)
                if 0 <= Yb < H and 0 <= Xb < W:
                    stamp_tuft(code, Yb, Xb, rt, fam, base_tone)
                    if fam == 'grass':
                        SHEET_TUFTS.append((round(float(tx), 1), round(float(ty), 1)))
    return code


def stamp_tuft(code, Yb, Xb, rt, fam='grass', base_tone=3, scale=1.0):
    """One clump of grass at its foot (Yb, Xb): a dark base mass, 4 to 7 blades fanning out and
    curving (4-connected strokes, so no blade breaks into lone pixels), lit upper halves and
    tips on the sunny clumps, a short shade to the lower right."""
    H, W = code.shape
    k = int(rt.integers(4, 8))
    hgt = rt.uniform(5.0, 8.5) * D * scale
    wid = max(2, int(round((k - 1) * 0.7 * D * scale)))
    kind = rt.random()
    sunny = kind < 0.4                          # dry yellow
    dark = kind > 0.8                           # deep green
    tf = fam + '_warm' if sunny else ('leaf' if dark and fam == 'grass' else fam)
    # (r3: no contact row under the clump: it read as a dashed base line)
    bh = 1
    for dx in range(-wid // 2 + 1, wid // 2):
        y, x = Yb, Xb + dx
        if 0 <= y < H and 0 <= x < W:
            code[y, x] = C(tf, base_tone - 2 if not sunny else base_tone - 1)
    for i in range(k):
        c = i - (k - 1) / 2
        x0 = Xb + int(round(c * wid / max(1, k - 1)))
        hi_ = max(3, int(round(hgt * rt.uniform(0.65, 1.0) * (1.0 - 0.45 * abs(c) / k))))
        lean = c / k * 7.0 * D * scale + rt.uniform(-0.8, 0.8) * D
        px, py = x0, Yb - bh + 1
        for j in range(1, hi_ + 1):
            y = Yb - bh + 1 - j
            x = x0 + int(round(lean * (j / hi_) ** 1.5))
            f = j / hi_
            cc = C(tf, base_tone - 1) if f < 0.45 else C(tf, base_tone + (1 if not dark else 0))
            if j == hi_ and (sunny or c < 0):
                cc = C(tf, min(5, base_tone + (2 if sunny else 1)))
            # 4-connected: step sideways on the old row before rising
            while px != x:
                px += 1 if x > px else -1
                if 0 <= py < H and 0 <= px < W:
                    code[py, px] = cc
            py = y
            if 0 <= y < H and 0 <= x < W:
                code[y, x] = cc


