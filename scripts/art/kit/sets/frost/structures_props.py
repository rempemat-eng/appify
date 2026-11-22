"""Frostline structures and props."""
from __future__ import annotations

from ._shared import (
    B,
    C,
    FI,
    GRANITE,
    K,
    OAK,
    RED,
    SNOW,
    V,
    _crust,
    _drift_west,
    _grain_after,
    _granite_dress,
    _grow,
    _snow_light,
    _snowcap,
    _solo,
    hsh,
    math,
    ndi,
    np,
)
from .water_ice import (
    ICE,
    _ice_faces,
    _line,
)

HUT_SPEC = dict(kind='hut', w=64, depth=34, wall_h=41, roof_h=26, wall='stone', roof='slate', paint='timber',
                doors=[[22, 'timber']], door_w=13, door_h=29, windows=[47], win_w=10, win_h=11, win_top=30,
                shutters=False, slate_calm=True, eave_dark=True, roof_moss=0, roof_lichen=0, chimney=[52],
                chimney_w=7, chimney_h=12)



def fire_ring(seed=67):
    """The fallen climbers' camp's hearth, cold (round 3, R2-P6): a ring of granite stones, each a
    block with a lit top and its grey east side showing under a small cap of snow; inside, a hollow
    scraped clear to soot-dark ash with charred brands and charcoal; snow banked round the outside.
    No green (Z6)."""
    sc = K.Scene(-30, 30, -24, 16, 40)
    rng = np.random.default_rng(seed)
    # the snow banked round the outside of the ring (low, against the stones), deeper on the west
    sc.ellipsoid(-1.5, 0.5, 0.1, 17.5, 12.0, 2.2, SNOW, base=3.8, k=1.0, tag='drift', flat=2.4)
    # the hearth: ash and soot in the scraped hollow
    sc.ellipsoid(0.5, 0.5, 1.0, 8.0, 5.4, 1.6, [('soot', 'soot', 'ash')], base=1.6, k=0.8, tag='soot', flat=1.6)
    sc.ellipsoid(-1.5, -0.5, 1.5, 4.2, 2.8, 1.4, [('soot', 'ash', 'ash')], base=2.6, k=0.8, tag='ash', flat=1.4)
    for (x0, y0, x1, y1) in ((-4, 1, 3, 2.6), (0, -2.5, 5.5, -1.2), (2, 2.4, 6, 3.6)):
        sc.box(x0, y0, 1.6, x1, y1, 3.4, [('soot', 'timber_cool', 'timber')], base=1.3, k=1.2, tag='brand', round_=0.8)
    for k in range(8):
        ang = 2 * math.pi * k / 8 + rng.uniform(-0.15, 0.15)
        x, y = 10.5 * math.cos(ang), 7.2 * math.sin(ang)
        sz = rng.uniform(3.8, 4.6)
        sc.ellipsoid(x, y, sz * 0.62, sz * 1.1, sz * 0.8, sz * 0.66, GRANITE, base=3.0, k=1.4, tag='rock', mix=rng.random(),
                     flat=2.3)
        if math.sin(ang) < -0.3:                          # the far and side stones hold snow; the near ones less
            sc.ellipsoid(x - sz * 0.25, y - sz * 0.15, sz * 1.25, sz * 0.62, sz * 0.45, sz * 0.32, SNOW, base=3.9, k=1.1,
                         tag='snow', flat=1.6)

    def dress(s_, a):
        _snow_light(s_, a, swell=0.0)
        lab = s_.label
        m = np.isin(lab, [i for i, q in enumerate(s_.solids) if q.tag == 'soot'])
        H, W = a.shape
        Y, X = np.mgrid[0:H, 0:W]
        coal = m & (K.vhash(X // 3, Y // 2, seed + 3) > 2.0)
        a[coal] = np.where(K.vhash(X, Y, seed + 4)[coal] > 0.5, C('soot', 0), C('ash', 2))
        ember = m & (K.vhash(X // 2, Y // 2, seed + 5) > 2.0)
        a[ember] = C('timber_cool', 1)
    a = _solo(sc, dress=dress)
    _grain_after(sc, a, seed, swap=0.3, step=0.0, crust=0)
    return K.crop(a, sc.ox, sc.oy)



# ------------------------------------------------------------------------------------------------
# the Col hut (B5: door 87, eaves 123 art px; F-H1, F-H2)
# ------------------------------------------------------------------------------------------------
def _plume_frame(i, n, W, H, seed):
    """One frame of the stove's smoke (round 3, R2-H2): a soft plume rising from the pot's mouth
    (the frame's bottom row, column 6), thickening as it leans east, then breaking into two or three
    puffs that rise with the loop's phase, swell, thin and fade; each part lit on its upper west,
    a cool grey body and a darker east side, no outline (smoke has none)."""
    a = np.full((H, W), -1, np.int32)
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    ph = i / float(n)
    blobs = []                                   # (cx, cy, r, fade 0..1)
    for k in range(28):                           # the connected column, the lower 45 %
        t = 0.45 * k / 27.0
        blobs.append((6 + 11 * t ** 1.3 + 0.9 * math.sin(2 * math.pi * (t * 2.2 - ph)), H - 1.5 - t * (H - 4), 2.2 + 11.0 * t, 0.0))
    for k in range(3):                            # the puffs above it, travelling up with the phase
        t = 0.45 + 0.55 * ((ph + k / 3.0) % 1.0)
        r = (2.2 + 11.0 * t) * (1.0 - 0.55 * max(0.0, t - 0.7) / 0.3) * (0.9 + 0.2 * hsh(seed, k))
        if t < 0.52:
            r *= (t - 0.45) / 0.07 * 0.6 + 0.4
        blobs.append((6 + 11 * t ** 1.3 + 0.9 * math.sin(2 * math.pi * (t * 2.2 - ph)) + 1.5 * (hsh(seed, k, 2) - 0.5),
                      H - 1.5 - t * (H - 4), max(1.2, r), max(0.0, (t - 0.7) / 0.3)))
    best = np.full((H, W), 9.0)
    lx = np.zeros((H, W))
    ly = np.zeros((H, W))
    fade = np.zeros((H, W))
    for (cx, cy, r, f) in blobs:
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r
        win = d < best
        best = np.where(win, d, best)
        lx = np.where(win, (X - cx) / r, lx)
        ly = np.where(win, (Y - cy) / r, ly)
        fade = np.where(win, f, fade)
    body = (best <= 1.0) & (Y < H - 0.5)
    lit = lx * -0.7 + ly * -0.7                  # toward the upper west
    t_ = np.where(lit > 0.45, 3, np.where(lit > -0.1, 2, np.where(lit > -0.55, 1, 0)))
    t_ = np.minimum(3, t_ + np.round(fade * 1.5).astype(int))
    pal = np.array([C('slate', 4), C('snow_cool', 2), C('snow_cool', 3), C('snow_cool', 4)])
    a[body] = pal[t_][body]
    # the thinning tops of the high puffs break into tufts (no lone texels)
    thin = body & (fade > 0.35) & (K.vhash(np.floor(X).astype(int) // 2, np.floor(Y).astype(int) // 2, seed + i) < 0.3 * fade)
    a[thin] = -1
    K.despeckle(a, size=2)
    return a



def col_hut(seed=31):
    """The Col hut at the size guide's Frostline scale (huts: eaves 40 to 44, door about 32 world px):
    rubble granite under slate from the house builder, door leaf 87 art px, eaves at 123. On the roof
    a mass of snow with thickness: a lit top plane, a slight lit crest at the ridge, its end thickness
    showing at each verge, a soft cornice hanging over the eave, a wind scoop in the chimney's lee.
    Icicles 2 texels at the root, gathered at the corners and over the door. A drift banked against
    the foot, rising to the corners and the west, the doorway dug clear. The stove's smoke loops
    as a connected plume (8 frames)."""
    from scripts.art.native import houses as HS
    b = HS.building(HUT_SPEC, seed=seed)
    p = _grow(b.base, 10, 8)
    a = p.a
    H, W = a.shape
    oy, ox = 10, 8
    rm = np.zeros((H, W), bool)
    rm[oy:, ox:ox + b.base.W] = b.info['roof']
    y_r, y_e = b.info['y_r'] + oy, b.info['y_eave'] + oy
    Yg, Xg = np.mgrid[0:H, 0:W]
    stoneish = np.isin(a // 8, [FI[n] for n in ('stone', 'stone_cool', 'stone_warm', 'ashlar', 'ashlar_warm')])
    chim_cols = ndi.binary_dilation((stoneish & (Yg < y_r + 4)).sum(0) > 4, iterations=1)
    stack = chim_cols[None, :] & (Yg < y_e) & (stoneish | (a // 8 == FI['soot']))
    chim = ndi.binary_dilation(stack, structure=np.ones((1, 3), bool))
    roof = rm & ~chim
    cols = np.nonzero(roof.any(0))[0]
    rows = np.nonzero(roof.any(1))[0]
    L, R, top = cols.min(), cols.max(), rows.min()
    rng = np.random.default_rng(seed)
    orig = a.copy()
    ladder = [C('sky_cool', 4), C('sky_cool', 5), C('snow_cool', 2), C('snow', 2), C('snow_cool', 3), C('snow', 3),
              C('snow_cool', 4), C('snow', 4), C('snow_warm', 4), C('snow', 5)]
    NL = len(ladder)
    # (round 3, R2-H1) the cornice's lower edge: a slow lumpy line hanging 2 to 3 texels over the eave
    prof = ndi.gaussian_filter1d(rng.random(W), 4.0, mode='nearest')
    prof = (prof - prof.mean()) / (prof.std() + 1e-9)
    hang = np.clip(np.round(2.4 + 0.8 * prof), 2, 4).astype(int)
    low = (y_e + hang)[None, :]
    span = (Xg >= L - 3) & (Xg <= R + 3)
    # the ridge: snow heaped over it in soft mounds (1 to 4 texels), its top edge irregular
    rp = ndi.gaussian_filter1d(rng.random(W), 3.0, mode='nearest')
    rp = (rp - rp.min()) / max(1e-6, rp.max() - rp.min())
    heap = np.round(1 + 4 * rp).astype(int)
    heap[np.abs(np.arange(W) - (L - 3)) < 3] -= 1
    heap[np.abs(np.arange(W) - (R + 3)) < 3] -= 1
    mass = span & (Yg >= (top - heap)[None, :]) & (Yg <= low)
    mass &= ~chim
    cx0, cx1 = np.nonzero(chim_cols)[0].min(), np.nonzero(chim_cols)[0].max()
    ccx = (cx0 + cx1) / 2.0
    stack_foot = int(np.nonzero(stack.any(1))[0].max())
    # the planes: the lit crest and upper plane (the slope toward the ridge faces the sky), cooling
    # down the slope and to the east, broad wind-laid swells; the slates' courses showing through
    # the thinner snow as faint cool steps
    lv = (Yg - top) / max(1, (y_e - top))
    east = (Xg - L) / max(1, R - L)
    sw_ = ndi.gaussian_filter(rng.random((H, W)), (1.4, 6.0))
    sw_ = (sw_ - sw_.mean()) / (sw_.std() + 1e-9)
    # the snow has crept on the slates into pillows (four to six across the roof), each rounded:
    # lit on its upper west, turning cool to its east crease and down its front
    edges_x = [L - 3]
    while edges_x[-1] < R - 26:
        edges_x.append(edges_x[-1] + int(rng.integers(30, 58)))
    edges_x[-1] = R + 4
    pu = np.zeros((H, W))
    pv = np.zeros((H, W))
    for j in range(len(edges_x) - 1):
        x0_, x1_ = edges_x[j], edges_x[j + 1]
        wob = 2.0 * np.sin((Yg - top) / 7.0 + j * 1.7) + (Yg - top) * 0.15
        inside = (Xg >= x0_ + wob) & (Xg < x1_ + wob)
        pu = np.where(inside, (Xg - x0_ - wob) / max(1.0, x1_ - x0_), pu)
    du = pu - 0.3
    # a pillow's crease fades toward the ridge (the snow is one mass there) and deepens down the slope
    v = (8.6 - 5.0 * np.clip(du, 0, None) ** 1.5 * (0.4 + lv) - 2.0 * np.clip(-du, 0, None) * lv - 2.8 * lv - 0.8 * east
         + 0.7 * np.clip(sw_, -1.4, 1.4))
    v = np.where((pu > 0.94) & (lv > 0.35) & (lv < 0.97), v - 2.6 * lv, v)
    # the slates' courses under the thinner snow of the lower slope: each a lit step over a cool row,
    # broken where the wind has laid the snow deeper
    seg = K.vhash((Xg + 3 * ((Yg - top) // 5)) // 7, (Yg - top) // 5, seed + 13) > 0.3
    thin = (sw_ < 0.7) & (lv > 0.3) & seg
    v = np.where(thin & ((Yg - top) % 5 == 4), v - 2.2, v)
    v = np.where(thin & ((Yg - top) % 5 == 3), v + 1.0, v)
    # the chimney's lee: a scoop east of the stack, cool, with a lit rim on its far (east) side
    dl = ((Xg - cx1 - 7) / 8.0) ** 2 + ((Yg - stack_foot + 2) / 6.0) ** 2
    v = np.where(dl < 1.0, v - 3.5 * (1 - dl), v)
    rim = (dl >= 1.0) & (dl < 1.6) & (Xg > cx1 + 7)
    v = np.where(rim, v + 1.8, v)
    idx = np.clip(np.round(v), 0, NL - 1).astype(int)
    codes = np.array(ladder)[idx]
    a[mass] = codes[mass]
    # the stove's warmth: a melt west of and under the stack, the wet slates showing, an edge of
    # slush; and a wind-scoured patch high on the east where the slates break through
    mn = ndi.gaussian_filter(rng.random((H, W)), 2.0)
    mn = (mn - mn.mean()) / (mn.std() + 1e-9)
    dm = ((Xg - ccx) / ((cx1 - cx0) / 2.0 + 6.0)) ** 2 + ((Yg - stack_foot - 1) / 4.0) ** 2 + 0.2 * mn
    melt = mass & (dm < 1.0) & (Yg > top + 3) & (Yg < y_e - 4)
    sc_ = ndi.gaussian_filter(rng.random((H, W)), (2.0, 5.0))
    sc_ = (sc_ - sc_.mean()) / (sc_.std() + 1e-9)
    # the slates' lower edges breaking through the thin snow near the eave, in short dark runs
    run_h = K.vhash((Xg + 5 * ((Yg - top) // 5)) // 4, (Yg - top) // 5, seed + 19)
    slat = np.isin(orig // 8, [FI['slate'], FI['slate_cool'], FI['slate_warm'], FI['iron']]) & (orig >= 0)
    edges_s = mass & thin & ((Yg - top) % 5 == 4) & (lv > 0.45) & (run_h > 0.55) & (sw_ < -0.15) & (Yg < y_e - 3) & \
        (pu < 0.85) & slat
    bare = melt | edges_s
    wet = orig[bare]
    a[bare] = np.where(wet >= 0, (wet // 8) * 8 + np.maximum(1, wet % 8 - 1), C('slate', 2))
    slush = ndi.binary_dilation(bare, iterations=1) & mass & ~bare
    a[slush] = np.where((Yg[slush] % 2) == 0, C('snow_cool', 3), C('sky_cool', 4))
    lit_edge = slush & ~np.roll(bare, -1, 0) & np.roll(bare, 1, 0)
    a[lit_edge] = C('sky_cool', 3)
    # the crust: short runs along the wind, a step down on the lit planes and up in the cool
    Hh = np.arange(H)[:, None]
    off = (K.vhash(Hh, Hh // 2, seed + 9) * 4).astype(int)
    run = (Xg + off) // 3
    hc = K.vhash(run, Yg, seed + 4)
    tip = K.vhash(Xg, Yg, seed + 6) < 0.25
    crust = mass & ~bare & ~slush & (hc < 0.3) & ~tip & np.isin(a, ladder)
    for i_, c_ in enumerate(ladder):
        s2 = crust & (a == c_)
        a[s2] = ladder[max(0, min(NL - 1, i_ - 2 if i_ >= 5 else i_ + 2))]
    # the ridge's lit crest along the snow's top and a cool row behind the heaps
    crest = mass & ~np.roll(mass, 1, 0)
    a[crest] = C('snow', 5)
    below_c = np.roll(crest, 1, 0) & mass & ~bare
    a[below_c & (K.vhash(Xg // 2, 0, seed) > 0.5)] = C('snow', 5)
    # the cornice: its last four rows: the lit lip, the cool front, the darker turn, the underside
    edge = mass & ~np.roll(mass, -1, 0)
    for k_, code in ((0, C('snow_cool', 2)), (1, C('snow_cool', 3)), (2, C('snow_cool', 4)), (3, C('snow', 5))):
        sel = np.roll(edge, -k_, 0) & mass & ~bare
        a[sel] = code
    under = np.roll(edge, 1, 0) & ~mass & (a >= 0)
    a[under] = C('sky_cool', 2)
    under2 = np.roll(edge, 2, 0) & ~mass & (a >= 0) & (K.vhash(Xg // 3, 1, seed) > 0.4)
    a[under2] = (a[under2] // 8) * 8 + np.maximum(0, a[under2] % 8 - 1)
    # the verges: the snow's end thickness, three texels down each gable: lit on the west end, in
    # shade on the east
    for xv, codes_v in ((L - 3, (C('snow', 5), C('snow', 4))), (L - 2, (C('snow', 4), C('snow_cool', 4))),
                        (R + 2, (C('snow_cool', 3), C('snow_cool', 2))), (R + 3, (C('snow_cool', 2), C('snow_cool', 2)))):
        ys_ = np.nonzero(mass[:, xv])[0]
        if len(ys_):
            for y in range(ys_.min() + 1, ys_.max() - 3):
                a[y, xv] = codes_v[0] if (y - ys_.min()) % 6 < 4 else codes_v[1]
    # the chimney: snow seated on the stack's cap either side of the pot, and a rim of it on the pot
    capm = stack & (Yg <= np.nonzero(stack.any(1))[0].min() + 3)
    ctop = int(np.nonzero(capm.any(1))[0].min()) if capm.any() else top
    potm = (orig >= 0) & np.isin(orig // 8, [FI['clay'], FI['clay_cool'], FI['crag'], FI['crag_warm'], FI['crag_cool']]) \
        & (Yg <= ctop) & (Xg >= cx0 - 2) & (Xg <= cx1 + 2)
    for x in range(cx0 - 1, cx1 + 2):
        col_ = np.nonzero(((orig[:, x] >= 0) & (Yg[:, x] < stack_foot)) & ~potm[:, x])[0]
        if not len(col_):
            continue
        yt = int(col_.min())
        hh = 2 if x in (cx0 - 1, cx1 + 1) else 3
        if potm[:, x].any():
            continue                                        # the warm pot melts the snow at its foot
        if potm[:, max(0, x - 1):x + 2].any():
            hh = 1
        for k_ in range(hh):
            y = yt - hh + k_
            if 0 <= y < H:
                a[y, x] = C('snow', 5) if k_ == 0 else (C('snow', 4) if x < ccx else C('snow_cool', 3))
    # snow caught on the rough wall: on the stones' top edges, more on the windward (west) half, in
    # runs of two to four texels, and on the window sill and the door's lintel
    wx0, wx1, wy0, wy1 = b.info['wall']
    wx0, wx1, wy0, wy1 = wx0 + ox, wx1 + ox, wy0 + oy + 4, wy1 + oy
    up1 = np.full_like(orig, -1)
    up1[1:] = orig[:-1]
    stone_top = (orig >= 0) & (up1 >= 0) & np.isin(orig // 8, [FI[n] for n in ('stone', 'stone_cool', 'stone_warm', 'ashlar',
                                                                               'ashlar_warm')]) & \
        (up1 % 8 + 2 <= orig % 8) & (Yg > wy0) & (Yg < wy1 - 6) & (Xg > wx0 + 1) & (Xg < wx1 - 1)
    wu = (Xg - wx0) / max(1, wx1 - wx0)
    lodge = stone_top & (K.vhash(Xg // 3, Yg, seed + 23) < 0.55 - 0.45 * wu) & (a == orig)
    a[lodge] = np.where(K.vhash(Xg, Yg, seed + 24)[lodge] > 0.4, C('snow', 5), C('snow', 4))
    lodge2 = np.roll(lodge, 1, 0) & (a == orig) & (K.vhash(Xg // 2, Yg, seed + 25) > 0.35)
    a[lodge2] = C('snow_cool', 3)
    # the sill and the lintels: snow lying along them, two texels deep, lit on top, cool at the front
    for (o0, o1, o2, o3) in b.info['openings']:
        for (yy, x0_, x1_) in ((o1 + oy - 2, o0 + ox - 1, o2 + ox + 1), (o3 + oy, o0 + ox - 2, o2 + ox + 2)):
            if yy >= y_e + 4 and yy < wy1 - 4:
                for x in range(x0_, x1_):
                    if a[yy, x] >= 0 and hsh(seed, x // 3, yy) > 0.15:
                        a[yy - 1, x] = C('snow', 5)
                        a[yy, x] = C('snow_cool', 4) if x > (x0_ + x1_) / 2 else C('snow', 4)
    # icicles under the cornice: gathered at the corners and over the door, 2 texels at the root
    door_l = ox + b.info['L'] + V.q(HUT_SPEC['doors'][0][0])
    door_r = door_l + V.q(HUT_SPEC['door_w'])
    groups = [(L + 2, L + 16), (R - 16, R - 2), (door_l - 2, door_r + 2)]
    for g0, g1 in groups:
        x = g0 + int(rng.integers(0, 3))
        while x < g1:
            col_ = np.nonzero(mass[:, x])[0]
            if len(col_):
                y0 = col_.max() + 1
                n = int(rng.integers(4, 11))
                for k_ in range(n):
                    y = y0 + k_
                    if y >= H:
                        break
                    wide = k_ < max(2, n // 2)
                    a[y, x] = C('snow', 5) if k_ == 0 else C('sky_cool', 5)
                    if wide and x + 1 < W:
                        a[y, x + 1] = C('sky_cool', 4) if k_ > 0 else C('snow', 4)
            x += int(rng.integers(4, 7))
    # the drift against the foot: rises toward the corners and the west, the doorway clear; a lit
    # crest, the upper body, the cool lower body and its foot, the wind's crust, a blue shade row on
    # the wall above it
    foot = p.ay
    wl, wr = ox + b.info['L'], ox + b.info['R']
    for x in range(wl - 6, wr + 5):
        if door_l - 4 <= x <= door_r + 3:
            continue
        u = (x - wl) / max(1, wr - wl)
        h = 5 + 9 * max(0.0, 0.35 - u) / 0.35 + 6 * max(0.0, u - 0.8) / 0.2 + 2.0 * prof[x % W]
        if x < wl or x > wr:
            h = max(2, h - 3 * abs(x - (wl if x < wl else wr)))
        h = int(round(h))
        cool = u > 0.55
        for k_ in range(h):
            y = foot - k_
            if not (0 <= y < H):
                continue
            f = k_ / max(1.0, h - 1.0)
            if k_ == h - 1:
                c = C('snow', 5)
            elif f > 0.6:
                c = C('snow', 4) if not cool else C('snow_cool', 4)
            elif f > 0.25:
                c = C('snow_cool', 4) if not cool else C('snow_cool', 3)
            else:
                c = C('snow_cool', 3) if not cool else C('snow_cool', 2)
            if 0 < k_ < h - 1 and K.vhash((x + (y // 2) % 2) // 3, y, seed + 21) < 0.28:
                c = C('snow', 4) if c != C('snow', 4) else C('snow_cool', 4)
            a[y, x] = c
        y = foot - h
        if 0 <= y < H and a[y, x] >= 0 and wl <= x <= wr:
            a[y, x] = C('sky_cool', 2)
    V.outline(p.a)
    V.tidy(p.a)
    q_ = K.crop(p.a, p.ax, p.ay)
    pots = b.info.get('pots') or []
    if pots:
        px, py = pots[0]
        pot_x, pot_y = int(px + ox - p.ax + q_.ax), int(py + oy - p.ay + q_.ay) - 2
    elif potm.any():
        # the plume leaves the pot's mouth (R2-H2): its foot overlaps the rim by a texel
        pys, pxs = np.nonzero(potm)
        pot_x, pot_y = int(round(pxs.mean())) - p.ax + q_.ax, int(pys.min()) - p.ay + q_.ay + 1
    else:
        pot_x, pot_y = int(cx0 + (cx1 - cx0) / 2 - p.ax + q_.ax), int(ctop - p.ay + q_.ay) - 2
    sw, sh = 36, 60
    up = max(0, sh - pot_y + 2)
    east = max(0, pot_x - 6 + sw - q_.W)
    r = V.Pic(q_.W + east, q_.H + up, q_.ax, q_.ay + up)
    r.a[up:, :q_.W] = q_.a
    region = (pot_x - 6, pot_y + up - sh, sw, sh)
    frames = [V.Pic(sw, sh, 0, sh) for _ in range(8)]
    for i, fr in enumerate(frames):
        fr.a[:] = _plume_frame(i, 8, sw, sh, seed)
    return r, {'frames': frames, 'fps': 6.0, 'clip': 'smoke', 'region': region}

ROPE = [('earth_cool', 'sand_cool', 'sand_warm')]

IRON = [('soot', 'iron', 'iron')]



def sledge(seed=53):
    """The ice-cutter's sledge: two runners turned up at the front in a smooth curl with iron
    shoeing, a plank bed on short posts, three blocks of lake ice lashed on it with a rope that
    crosses them diagonally to knots at the bed rail, and the bow saw leaning against its east end
    at an angle (a curved timber bow, a toothed blade catching the light)."""
    sc = K.Scene(-52, 52, -24, 14, 90)
    for y0 in (-13.0, 3.0):
        sc.box(-30, y0, 0, 30, y0 + 3, 3, OAK, base=2.5, k=1.5, tag='runner', round_=1.0)
        sc.box(-30, y0, -0.5, 31, y0 + 3, 0.6, IRON, base=2.6, k=1.4, tag='iron')
        for k in range(10):                                 # the curl, in one-texel steps on an arc
            ang = math.pi * k / 18.0
            x = -30 - 6 * math.sin(ang)
            z = 6 - 6 * math.cos(ang)
            sc.box(x - 1.2, y0, z, x + 0.2, y0 + 3, z + 2.6, OAK, base=2.7, k=1.5, tag='runner', round_=0.6)
    for x in (-22, 0, 22):
        for y0 in (-13.0, 3.0):
            sc.box(x - 2, y0, 3, x + 2, y0 + 3, 8, OAK, base=2.1, k=1.4, tag='post')
    sc.box(-28, -15, 8, 28, 7, 11, OAK, base=2.8, k=1.6, tag='bed', round_=0.8, tex='wood')
    sc.box(-28, 6, 9, 28, 8, 13, OAK, base=2.4, k=1.6, tag='rail', round_=0.6)
    blocks = [(-25, -11, -10, 3, 13), (-7, -12, 7, 4, 11), (10, -10, 25, 3, 14)]
    for k, (x0, y0, x1, y1, h) in enumerate(blocks):
        sc.box(x0, y0, 11, x1, y1, 11 + h, ICE, base=3.4, k=1.3, tag='ice', round_=1.2)
    sc.render()
    a = sc.shade(crevice=1.0, rim=0.6)
    _ice_faces(sc, a, seed)
    V.tidy(a)
    V.outline(a)
    # the rope: two diagonals over the load to knots on the rail
    oxn, oyn = sc.ox, sc.oy
    p = lambda x, y, z: (oxn + x, oyn + y - z)     # noqa: E731
    for (x0, x1) in ((-26, 8), (26, -8)):
        _line(a, p(x0, 7, 12), p(x1 * 0.2, -2, 26), C('sand_cool', 3))
        _line(a, p(x0, 7, 12), p(x0 + (1 if x0 < 0 else -1), 7, 10), C('earth_cool', 1))
        kx, ky = p(x0, 7, 12)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            if 0 <= ky + dy < a.shape[0] and 0 <= kx + dx < a.shape[1]:
                a[ky + dy, kx + dx] = C('sand_warm', 4)
    # the bow saw against the east end, leaning: the bow (a curve), the blade (straight, toothed)
    bx0, by0 = p(33, 4, 0)
    bx1, by1 = p(44, 4, 34)
    n = 26
    for k in range(n + 1):
        t = k / n
        x = bx0 + (bx1 - bx0) * t + 5 * math.sin(math.pi * t)
        y = by0 + (by1 - by0) * t
        for dx in (0, 1):
            xi, yi = int(round(x)) + dx, int(round(y))
            if 0 <= yi < a.shape[0] and 0 <= xi < a.shape[1]:
                a[yi, xi] = C('timber', 3) if dx == 0 else C('timber_cool', 2)
    for k in range(n + 1):
        t = k / n
        x = int(round(bx0 + (bx1 - bx0) * t)) - 1
        y = int(round(by0 + (by1 - by0) * t))
        if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
            a[y, x] = C('iron', 4) if k % 3 else C('snow', 5)
    return K.crop(a, sc.ox, sc.oy)



# ------------------------------------------------------------------------------------------------
# the hut's yard and the Col Path's markers (Z5)
# ------------------------------------------------------------------------------------------------
def woodpile(seed=71):
    """The warden's woodpile against the cold (round 3, R2-P3): split and round logs stacked between
    two stakes, their cut ends to the south in several sizes, laid staggered in rough courses (each
    end a bark rim, a pale sapwood ring, the heartwood with its rings and a radial check, lit on its
    upper west), the gaps between them dark; a pillowed cap of snow on top, snow at its west end."""
    sc = K.Scene(-40, 40, -20, 12, 70)
    sc.box(-30, -8, 0, 30, 4, 24, B.OAK, base=1.6, k=1.0, tag='pile', round_=1.5, tex='wood')
    for x in (-33, 31):
        sc.box(x, -2, 0, x + 3, 1, 31, B.OAK, base=2.4, k=1.6, tag='stake', round_=0.8, tex='wood_v')
    for (cx, w, h) in ((-18, 15, 4.4), (1, 17, 5.2), (18, 14, 4.0)):
        sc.ellipsoid(cx, -2.0, 24.5, w, 7.8, h, SNOW, base=3.9, k=1.1, tag='snow', flat=1.6)
    sc.ellipsoid(-33, 3.5, 0.2, 6.5, 4.0, 6.0, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)

    a = _solo(sc, dress=lambda s_, a: _snow_light(s_, a, swell=0.1))
    _crust(sc, a, seed, rate=0.18)

    def logs(s_, a):
        rng = np.random.default_rng(seed)
        m = np.isin(s_.label, [i for i, q in enumerate(s_.solids) if q.tag == 'pile']) & (s_.n[..., 1] > 0.5)
        m &= ndi.binary_erosion(a >= 0)
        ys, xs = np.nonzero(m)
        if not len(ys):
            return
        H, W = a.shape
        a[m] = C('timber_cool', 1)                         # the dark gaps between the logs
        Yi, Xi = np.mgrid[0:H, 0:W]
        y = ys.max() + 0.5
        row = 0
        while y > ys.min() + 3:
            x = xs.min() - (2.5 if row % 2 else 0.5) + rng.uniform(0, 1.5)
            rs = []
            while x < xs.max() + 2:
                r = float(rng.choice([3.0, 3.5, 4.0, 4.6]))
                cx, cy = x + r, y - r - rng.uniform(0, 0.8)
                rs.append(r)
                d = np.sqrt((Xi + 0.5 - cx) ** 2 + (Yi + 0.5 - cy) ** 2) / r
                disc = (d <= 1.0) & m
                ddx, ddy = (Xi + 0.5 - cx) / r, (Yi + 0.5 - cy) / r
                lit = -ddx - ddy
                c = np.where(d > 0.8, np.where(lit > 0.2, C('timber', 3), C('timber_cool', 2)),
                             np.where(d > 0.58, np.where(lit > -0.2, C('sand_cool', 4), C('sand_cool', 3)),
                                      np.where((np.abs(d - 0.3) < 0.08) & (r > 3.2), C('sand_cool', 3),
                                               np.where(lit > 0.5, C('sand', 5), np.where(lit > -0.3, C('sand', 4),
                                                                                         C('sand_cool', 4))))))
                check = (ddx > 0.05) & (np.abs(ddy) < 0.12) & (d < 0.6) & (r > 3.4)
                c = np.where(check, C('sand_cool', 2), c)
                a[disc] = c[disc]
                x += 2 * r - rng.uniform(0, 0.8)
            y -= 2 * float(np.mean(rs)) * 0.86
            row += 1
    logs(sc, a)
    return K.crop(a, sc.ox, sc.oy)



def hut_tools(seed=73):
    """The warden's ice tools in a rack by the hut (round 3, R2-P4): a two-post rail, and leaning on
    it at their own angles an ice saw (a long toothed blade, its T handle up), a felling axe (a lit
    steel head with its edge catching the light, a curved haft) and a snow shovel (a broad lit blade,
    its shaft and grip); each part lit on its west side and dark on its east, snow on their tops and
    heaped at their feet."""
    sc = K.Scene(-30, 30, -14, 12, 90)
    sc.box(-21, -4, 0, 21, -1, 50, B.OAK, base=2.2, k=1.4, tag='board', round_=0.6, tex='wood_v')
    for x in (-23, 19):
        sc.box(x, -2, 0, x + 4, 1, 54, B.OAK, base=2.6, k=1.6, tag='post', round_=0.8, tex='wood_v')
    sc.box(-24, -5, 50, 24, 2, 53, B.OAK, base=2.7, k=1.6, tag='rail', round_=1.0, tex='wood')
    for (cx, w) in ((-13, 12), (5, 14), (17, 8)):
        sc.ellipsoid(cx, -1.5, 53.5, w, 4.5, 2.6, SNOW, base=3.9, k=1.1, tag='snow', flat=1.8)
    sc.ellipsoid(-1, 3, 0.2, 21, 6.0, 4.0, SNOW, base=3.8, k=1.0, tag='drift', flat=1.4)
    sc.render()
    a = sc.shade()
    _snow_light(sc, a)
    # the backboard's planks: joints, a lit west edge on each, nail heads at the rail
    H_, W_ = a.shape
    Y_, X_ = np.mgrid[0:H_, 0:W_]
    bd = np.isin(sc.label, [i for i, q in enumerate(sc.solids) if q.tag == 'board']) & (sc.n[..., 1] > 0.5)
    pl = (X_ - sc.ox + 21) % 7
    a[bd & (pl == 6)] = C('timber_cool', 1)
    a[bd & (pl == 0)] = (a[bd & (pl == 0)] // 8) * 8 + np.minimum(5, a[bd & (pl == 0)] % 8 + 1)
    V.tidy(a)
    V.outline(a)
    p = lambda x, z, y=4: (sc.ox + x, sc.oy + y - z)     # noqa: E731

    tool = set()

    def stick(x0, z0, x1, z1, w, lit_c, body_c, dark_c):
        n = int(max(abs(x1 - x0), abs(z1 - z0))) + 1
        for t in np.linspace(0, 1, n):
            X, Y = p(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t)
            X, Y = int(round(X)), int(round(Y))
            for k in range(w):
                if 0 <= Y < a.shape[0] and 0 <= X + k < a.shape[1]:
                    a[Y, X + k] = lit_c if k == 0 else (dark_c if k == w - 1 else body_c)
            if 0 <= Y < a.shape[0] and 0 <= X + w < a.shape[1] and a[Y, X + w] not in tool:
                a[Y, X + w] = C('timber_cool', 0)
            for k in range(w):
                if 0 <= Y < a.shape[0] and 0 <= X + k < a.shape[1]:
                    tool.add(int(a[Y, X + k]))
    # the ice saw: a long blade leaning west of centre, teeth on its east edge, a T handle at the top
    stick(-16, 1, -11, 62, 5, C('snow', 4), C('iron', 5), C('iron', 2))
    for k in range(4, 58, 2):
        X, Y = p(-16 + 5 * k / 61 + 5, 1 + k)
        X, Y = int(round(X)), int(round(Y))
        if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
            a[Y, X] = C('soot', 0)
            if X + 1 < a.shape[1]:
                a[Y, X + 1] = C('iron', 3)
    stick(-17, 61, -7, 63, 3, C('timber', 4), C('timber', 3), C('timber_cool', 1))
    # the axe: its haft leaning west on the rail, the steel head at the top, its bit to the east
    stick(4, 1, -1, 52, 3, C('timber', 5), C('timber', 3), C('timber_cool', 1))
    hx, hz = 0, 41
    for dz in range(-6, 7):
        for dx in range(-2, 11):
            X, Y = p(hx + dx, hz + dz)
            X, Y = int(round(X)), int(round(Y))
            half = 2 + max(0, dx - 2) * 0.55
            if abs(dz) <= half and 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
                if dx <= 0:
                    c = C('iron', 2)                                  # the eye round the haft
                elif dx >= 9 or abs(abs(dz) - half) < 0.6:
                    c = C('snow', 5) if dz < 0 or dx >= 9 else C('iron', 3)   # the bit's edge and the bevel
                else:
                    c = C('iron', 5) if dz < -1 else (C('iron', 4) if dz < 2 else C('iron', 2))
                a[Y, X] = c
    for dz in range(-7, 8):
        X, Y = p(hx + 11, hz + dz)
        X, Y = int(round(X)), int(round(Y))
        if abs(dz) <= 7 and 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
            a[Y, X] = C('soot', 0)
    # the shovel: shaft leaning on the rail, a broad blade at its foot, the grip at the top
    stick(14, 14, 9, 58, 3, C('timber', 5), C('timber', 3), C('timber_cool', 1))
    stick(5, 57, 13, 59, 3, C('timber', 5), C('timber_cool', 2), C('timber_cool', 1))
    for dz in range(0, 17):
        wdt = 12 - dz // 3 if dz < 14 else 3
        for dx in range(-wdt // 2, wdt - wdt // 2):
            X, Y = p(14.5 + dx - dz * 0.1, 1 + dz)
            X, Y = int(round(X)), int(round(Y))
            if 0 <= Y < a.shape[0] and 0 <= X < a.shape[1]:
                u = (dx + wdt / 2) / max(1, wdt) + (0.25 if dz < 6 else 0.0)
                a[Y, X] = (C('snow_cool', 3) if u < 0.15 else C('slate', 5) if u < 0.35 else C('slate', 4) if u < 0.6 else
                           C('slate', 3) if u < 0.85 else C('slate_cool', 1))
    # snow on the tools' tops
    for (x, z) in ((-12, 63), (-7, 64), (-2, 53), (3, 55), (9, 59), (12, 60)):
        X, Y = p(x, z + 1)
        for k in range(3):
            if 0 <= Y < a.shape[0] and 0 <= X + k < a.shape[1]:
                a[Y, int(X) + k] = C('snow', 5)
    V.outline(a)
    _crust(sc, a, seed, rate=0.4)
    return K.crop(a, sc.ox, sc.oy)



def bench(seed=79):
    """A granite slab bench by the Col Path (round 3, R2-P1): a dressed slab with its lit top, a
    front face a step down and a dark east end, chamfered; two block legs, each with a lit top and
    a shaded east side; a pillow of snow on the east half of the seat (lit west, a cool front edge,
    shade under its lip), the west half brushed clear; the gap under the seat in shade."""
    sc = K.Scene(-40, 40, -16, 10, 50)
    for x in (-28, 20):
        sc.box(x, -5, 0, x + 8, 4.5, 13.2, GRANITE, base=2.9, k=1.9, tag='rock', round_=2.2, mix=0.3 + 0.4 * (x > 0), tex='stone')
    sc.box(-35, -8, 13, 35, 5, 18, GRANITE, base=3.1, k=1.9, tag='slab', round_=1.6, mix=0.55, tex='stone')
    sc.ellipsoid(17.0, -1.8, 18.6, 16.5, 6.6, 3.0, SNOW, base=3.9, k=1.1, tag='snow', flat=2.2)
    sc.ellipsoid(9.0, -2.5, 20.0, 6.5, 4.0, 2.2, SNOW, base=3.9, k=1.1, tag='snow', flat=1.6)
    sc.ellipsoid(-29.5, 4.0, 0.2, 5.0, 3.0, 3.6, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)

    def dress(s_, a):
        _granite_dress(s_, a, seed, tags=('rock', 'slab'), n_frac=2)
        lab = s_.label
        slab = np.isin(lab, [i for i, q in enumerate(s_.solids) if q.tag == 'slab'])
        H, W = a.shape
        Y, X = np.mgrid[0:H, 0:W]
        xs = np.nonzero(slab.any(0))[0]
        front = slab & (s_.n[..., 1] > 0.5)
        if len(xs):
            east = front & (X >= xs.max() - 3)
            a[east] = C('slate_cool', 1)
            a[slab & (X >= xs.max() - 1) & ~front] = C('slate_cool', 2)
            # the chamfer: the front's top row lit where it turns from the top
            ch = front & ~np.roll(front, 1, 0) & (X < xs.max() - 3)
            a[ch] = C('slate', 4)
            # tool marks along the dressed front
            tm = front & (K.vhash(X // 4, Y, seed + 7) > 0.8) & ~ch & (X < xs.max() - 3)
            a[tm] = C('slate_cool', 2)
        # the gap under the seat: the snow between the legs in the slab's shade
        rows = np.nonzero(slab.any(1))[0]
        if len(rows):
            yb = rows.max() + 1
            legs = np.isin(lab, [i for i, q in enumerate(s_.solids) if q.tag == 'rock'])
            lx = np.nonzero(legs.any(0))[0]
            for x in range(xs.min() + 2, xs.max() - 1):
                if legs[:, x].any() or not (lx.min() < x < lx.max()):
                    continue
                for d in range(2):
                    if yb + d < H and a[yb + d, x] < 0:
                        a[yb + d, x] = C('sky_cool', 4) if d == 0 else C('snow_cool', 3)
    a = _solo(sc, dress=dress)
    _grain_after(sc, a, seed, tags=('rock', 'slab'), swap=0.5)
    return K.crop(a, sc.ox, sc.oy)



def noticeboard(seed=83):
    """The warden's board at the foot of the col: two posts, a plank board under a little pent roof
    with snow on it, notices pinned (weather, the ring shut)."""
    sc = K.Scene(-36, 36, -10, 10, 110)
    for x in (-20, 17):
        sc.box(x, -2, 0, x + 3, 1, 78, B.OAK, base=2.4, k=1.5, tag='post')
    sc.box(-24, -2, 40, 24, 1, 74, B.OAK, base=2.7, k=1.4, tag='board', tex='wood')
    sc.box(-27, -6, 74, 27, 4, 78, [('slate_cool', 'slate', 'slate')], base=2.6, k=1.6, tag='roof', round_=0.8)
    # (round 3, R2-P5) the snow on the pent roof: a mass with thickness, heaped west, its top edge
    # lumpy, its front hanging over the roof's edge with a shade under it
    for (cx, w, h) in ((-17, 11, 4.4), (-3, 12, 5.0), (12, 11, 4.0), (22, 5, 3.0)):
        sc.ellipsoid(cx, -0.5, 78.5, w, 6.2, h, SNOW, base=3.9, k=1.1, tag='snow', flat=1.8)
    sc.ellipsoid(-21.5, 1.5, 0.2, 5.0, 3.0, 4.5, SNOW, base=3.8, k=1.0, tag='drift', flat=1.2)
    sc.render()
    a = sc.shade()
    _snow_light(sc, a)
    p = lambda x, y, z: (sc.ox + x, sc.oy + y - z)     # noqa: E731
    for (x0, z0, x1, z1, fam) in ((-20, 70, -4, 50, 'plaster'), (0, 68, 18, 56, 'plaster_warm'), (-2, 52, 12, 44, 'plaster')):
        X0, Y0 = p(x0, 1, z0)
        X1, Y1 = p(x1, 1, z1)
        a[Y0:Y1, X0:X1] = C(fam, 4)
        for yy in range(Y0 + 2, Y1 - 1, 2):
            a[yy, X0 + 2:X1 - 2 - (yy % 3)] = C('stone_cool', 2)
        a[Y0, X0 + (X1 - X0) // 2] = C('berry', 3)
    V.tidy(a)
    V.outline(a)
    _crust(sc, a, seed, rate=0.3)
    return K.crop(a, sc.ox, sc.oy)



def snow_pole(seed=89):
    """A snow pole marking the Col Path where drifts cover it: a tall stake banded red and white,
    a cap of snow, a drift at its foot."""
    sc = K.Scene(-14, 14, -8, 8, 110)
    for k in range(8):
        z0 = k * 11.0
        sets = RED if k % 2 else [('plaster', 'plaster', 'plaster_warm')]
        sc.cylinder(0, 0, 1.8, z0, z0 + 11.0, sets, base=3.0, k=1.4, tag='pole')
    _snowcap(sc, 0, 0, 88.6, 2.4, 2.0, th=1.4, seed=seed)
    _drift_west(sc, -2, 2, 6, seed)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)



def lost_hat(seed=97):
    """A story detail on the path: a red bobble hat dropped in the snow, half drifted over."""
    sc = K.Scene(-14, 14, -10, 8, 20)
    sc.ellipsoid(0, 0, 2.5, 6, 4.5, 4.0, RED, base=2.8, k=1.5, tag='hat', flat=1.2)
    sc.box(-6, -1, 0, 6, 3, 2.2, [('plaster', 'plaster', 'plaster_warm')], base=3.4, k=1.0, tag='band', round_=1.0)
    sc.ellipsoid(1, -1, 7.2, 2.2, 2.0, 2.0, [('plaster', 'plaster', 'plaster_warm')], base=3.6, k=1.0, tag='bobble')
    sc.ellipsoid(4.5, 1.5, 1.6, 5, 3.5, 2.2, SNOW, base=3.8, k=0.9, tag='snow', flat=1.3)
    a = _solo(sc)
    return K.crop(a, sc.ox, sc.oy)



def footbridge(seed=131):
    """The Col Path's crossing of the tarn's outlet, seen from above in the three-quarter view
    (Matt's review of round 3: the round 3 bridge was drawn front-on like a fence). The deck's
    planks lie across the way, seen from above and a little foreshortened, each with its grain and
    a dark gap; a trodden track of packed snow runs along the deck; log kerbs edge it north and south
    on short posts, the south kerb over the deck's dark edge; the deck's shadow falls on the ice
    below it; abutments of laid stone are set into each bank, their tops under snow."""
    W, H = 5 * 24, 2 * 24 + 18
    a = np.full((H, W), -1, np.int32)
    rng = np.random.default_rng(seed)
    x0, x1 = 13, W - 13
    y0, y1 = 10, 44                                       # the deck's top, north edge to south edge
    # the shadow on the ice under the deck (south of it, the light being north-west)
    for x in range(x0 - 2, x1 + 4):
        h = 9 + int(round(2 * hsh(seed, x // 5, 3)))
        for k in range(h):
            y = y1 + 3 + k
            if y < H:
                a[y, x] = C('slate_cool', 1) if k < h - 3 else C('sky_cool', 2)
    # the deck: planks across the way
    x = x0
    k = 0
    while x < x1:
        w = int(rng.integers(5, 7))
        tone = 4 if k % 3 == 0 else 3
        for xx in range(x, min(x1, x + w)):
            u = xx - x
            for yy in range(y0, y1):
                if u == w - 1:
                    c = C('timber_cool', 1)                                   # the gap between planks
                elif u == 0:
                    c = C('timber', min(5, tone + 1))                         # the plank's lit west arris
                else:
                    g = hsh(seed + k, xx, (yy + int(hsh(seed, k) * 9)) // 5)
                    c = C('timber', tone) if g > 0.3 else (C('timber_cool', tone) if g > 0.1 else C('timber', tone - 1))
                a[yy, xx] = c
        for yy in (y0 + 3, y1 - 4):                                           # nail heads at the joists
            a[yy, x + 1] = C('iron', 2)
        x += w
        k += 1
    # the trodden track: packed snow along the deck, its edges ragged, bootprints in it
    for xx in range(x0, x1):
        t0 = y0 + 10 + int(round(2 * hsh(seed, xx // 4, 5)))
        t1 = y1 - 9 - int(round(2 * hsh(seed, xx // 4, 6)))
        for yy in range(t0, t1):
            g = hsh(seed, (xx + yy * 3) // 4, yy)
            a[yy, xx] = (C('snow', 4) if (yy - t0) == 0 else C('snow_cool', 3) if g > 0.82 else
                         C('snow', 3) if g > 0.55 else C('snow_cool', 4))
        a[t1, xx] = C('sky_cool', 4)
    for xx in range(x0 + 6, x1 - 6, 9):
        yy = y0 + 13 + (xx // 9) % 2 * 4
        a[yy:yy + 2, xx:xx + 3] = C('snow_cool', 3)
    # snow lying on the deck along the north kerb, and lodged in the plank gaps
    for xx in range(x0, x1):
        h = 3 + int(round(3 * hsh(seed, xx // 5, 7)))
        for yy in range(y0, y0 + h):
            a[yy, xx] = (C('snow', 5) if yy == y0 else C('snow_cool', 2) if yy == y0 + h - 1 else
                         C('snow_cool', 3) if yy == y0 + h - 2 else
                         C('snow', 4) if hsh(seed, xx // 3, yy) > 0.35 else C('snow_cool', 4))
        if a[y0 + h, xx] >= 0 and a[y0 + h, xx] // 8 in (FI['timber'], FI['timber_cool']):
            a[y0 + h, xx] = C('timber', 5)
    # the kerbs: logs seen from above on short posts; the south one over the deck's dark edge
    for (yr, north) in ((y0 - 4, True), (y1 - 1, False)):
        for xx in range(x0 - 3, x1 + 3):
            a[yr, xx] = C('timber', 4)
            a[yr + 1, xx] = C('timber', 3)
            a[yr + 2, xx] = C('timber_cool', 2)
            if north:
                a[yr - 1, xx] = C('snow', 5) if hsh(seed, xx // 3, 9) > 0.3 else C('snow', 4)
        for xp in range(x0 + 2, x1, 20):
            a[yr - 2:yr + 3, xp:xp + 3] = C('timber_cool', 1)
            a[yr - 2, xp:xp + 3] = C('snow', 5)
            a[yr - 1, xp] = C('timber', 4)
        if not north:
            for d in range(3):
                a[yr + 3 + d, x0 - 2:x1 + 2] = C('timber_cool', 1) if d < 2 else C('timber_cool', 0)
    # the abutments: laid stones set into the banks, seen from above, their tops under snow
    for (xa, xb) in ((0, x0 + 1), (x1 - 1, W)):
        y = y0 - 8
        row = 0
        while y < y1 + 8:
            hh = int(rng.integers(5, 8))
            x = xa - (3 if row % 2 else 0)
            while x < xb:
                w = int(rng.integers(5, 9))
                for yy in range(y, min(y + hh, y1 + 8)):
                    for xx in range(max(xa, x), min(xb, x + w)):
                        r_ = yy - y
                        if xx == x + w - 1 or r_ == hh - 1:
                            c = C('slate_cool', 0)
                        elif r_ < hh - 3:
                            c = C('slate', 4) if xx < x + w - 2 else C('slate', 3)      # the stone's top
                        else:
                            c = C('slate_cool', 2)                                     # its face, in shade
                        a[yy, xx] = c
                x += w
            y += hh
            row += 1
        for xx in range(xa, xb):
            h = 4 + int(round(4 * hsh(seed, xx // 3, 11)))
            for yy in range(y0 - 8, y0 - 8 + h):
                a[yy, xx] = C('snow', 5) if yy == y0 - 8 else C('snow', 4)
            a[y0 - 8 + h, xx] = C('snow_cool', 3)
    V.outline(a)
    pic = V.Pic(W, H, W // 2, H - 1)
    pic.a[:] = a
    return pic
