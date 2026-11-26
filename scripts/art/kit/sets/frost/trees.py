"""Frostline conifers and dead pines."""
from __future__ import annotations

from ._shared import (
    C,
    FI,
    K,
    SNOW,
    V,
    WEATHERED,
    _crust,
    _drift_west,
    _snowcap,
    _solo,
    ndi,
    np,
)

# ------------------------------------------------------------------------------------------------
# conifers (F-P1, Z2; A3, 26 Nov): tiered spruces and pines drawn as tiers of boughs, each tier a
# skirt with pointed bough tips, lit from the upper left, its needles in drooping clusters, snow lying
# on every bough as a shelf heaped west and sagging at the tip
# ------------------------------------------------------------------------------------------------
# (scale of the woodland pine's master crown (x, y), seed, tier pitch in texels, silhouette power)
CONIFERS = {'spruce': ((0.95, 1.06), 507), 'pine': ((1.0, 1.0), 511), 'squat': ((1.18, 0.74), 521),
            'krummholz': ((1.25, 0.44), 531), 'krummholz_b': ((1.0, 0.36), 547), 'krummholz_c': ((1.4, 0.52), 559)}

# per form: tier pitch (texels), the cone's power (under 1 swells the upper crown), the wind's
# flagging (west reach, east reach: a krummholz grows to the lee), snow thickness on a bough
FORMS = {'spruce': (15.0, 1.0, (1.0, 1.0), 7.5), 'pine': (18.0, 0.95, (1.0, 1.0), 8.0),
         'squat': (17.0, 0.78, (0.96, 1.04), 7.5), 'krummholz': (14.0, 0.8, (0.62, 1.14), 7.0),
         'krummholz_b': (13.0, 0.75, (0.6, 1.16), 6.5), 'krummholz_c': (15.0, 0.8, (0.64, 1.12), 7.0)}

# the needles' value bands, deep to lit; each band lists siblings at (nearly) the same value, so a
# cluster can change family without stepping a tone (house-style 4: shape without value noise)
BANDS = [(('leaf_cool', 1), ('leaf', 1), ('grass_cool', 0), ('grass', 0)),
         (('leaf_cool', 2), ('grass_cool', 1), ('leaf', 2), ('grass', 1)),
         (('leaf', 3), ('leaf_cool', 3), ('grass_cool', 2), ('grass', 2)),
         (('leaf', 4), ('leaf_cool', 4), ('grass_cool', 3), ('grass', 3)),
         (('leaf_warm', 4), ('grass_cool', 4), ('leaf', 5), ('grass', 4))]


def _band(b, j=0):
    b = int(min(4, max(0, b)))
    f, t = BANDS[b][j % len(BANDS[b])]
    return C(f, t)


def _spray_shapes(seed=83, n=24):
    """Needle clumps as drawn for a bough's west side (mirrored for the east): a fan of needles 5 to 7
    texels wide and 4 or 5 tall, its top rounded, hanging down and out (west) to a tip at its lower
    west corner. Its cap is the lit crescent two texels thick on its top and west, its rim the shade
    under it (the bottom row and the east column), both clusters, never single texels."""
    nr = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        w = int(nr.integers(5, 8))
        h = int(nr.integers(4, 6))
        m = np.zeros((h, w), bool)
        for y in range(h):
            if y == 0:
                m[y, 1:w - 1] = True
            elif y < h - 1:
                cut = int(round((y / (h - 1)) * nr.uniform(1.0, 2.2)))
                m[y, 0:w - cut] = True
            else:
                m[y, 0:max(2, w // 2 - 1)] = True
        Yy, Xx = np.mgrid[0:h, 0:w]
        cap = m & ((Yy == 0) | ((Yy == 1) & (Xx <= w - 3)) | ((Xx <= 1) & (Yy <= h - 2)))
        last = np.array([np.nonzero(m[y])[0].max() for y in range(h)])
        rim = m & ~cap & ((Yy == h - 1) | (Xx == last[:, None]) | ((Yy == h - 2) & (Xx >= w // 2)))
        out.append((m, cap, rim))
    return out


SPRAYS = _spray_shapes()


def _tier_plan(rng, yt, yb, x0, x1, cxm, form):
    """The tiers, top first: dicts with top, bot (the row of the bough tips before their droop), cx,
    the west and east reach, the tip columns, each tip's own hang and the notch depth between each
    pair of tips. The tiers' pitches are drawn at random and then fitted to the crown's height, so
    the lowest tier is no larger than its neighbours; the widest tier spans the master crown, so the
    picture keeps its width."""
    pitch, power, (fw, fe), _t = FORMS[form]
    krum = form.startswith('krummholz')
    H = yb - yt
    droop_last = 1.0
    y_first = yt + rng.uniform(10, 13) * (0.8 if krum else 1.0)
    span = (yb - droop_last) - y_first
    steps = []
    acc = 0.0
    while acc < span:
        f = acc / max(1.0, span)
        st = pitch * rng.uniform(0.82, 1.18) * (0.7 + 0.55 * f)
        steps.append(st)
        acc += st
    n_steps = max(1, len(steps) - (1 if acc - span > 0.5 * steps[-1] else 0))
    steps = np.array(steps[:n_steps])
    steps *= span / steps.sum()
    bots = [y_first] + list(y_first + np.cumsum(steps))
    # the leader leans a little; a krummholz's upper tiers are pushed to the lee (east) by the wind
    tilt = (rng.uniform(4.0, 7.0) if krum else rng.choice((-1, 1)) * rng.uniform(1.5, 3.0))
    notched = set()
    if len(bots) > 4:
        notched = set(int(k) for k in rng.choice(np.arange(2, len(bots) - 1), size=min(2, len(bots) - 3), replace=False))
    raw = []
    for k, bot in enumerate(bots):
        f = (bot - yt) / H
        g = 0.14 + 0.86 * f ** power
        # the wind's flagging is strongest high up, where the tree stands out of the snowpack
        wind = 1.0 - f if krum else 1.0
        aw = g * rng.uniform(0.9, 1.05) * (1 - (1 - fw) * (0.6 + 1.2 * wind))
        ae = g * rng.uniform(0.9, 1.05) * (1 + (fe - 1) * (0.6 + 1.2 * wind))
        if k in notched:
            if rng.random() < 0.5:
                aw *= 0.8
            else:
                ae *= 0.82
        cx = cxm + tilt * (1 - f) ** 2 + (rng.uniform(-1.0, 1.0) if k else 0.0)
        raw.append([bot, f, cx, aw, ae])
    # fit: the widest reach either side meets the master crown's extent
    sw = (cxm - x0) / max(r[3] for r in raw)
    se = (x1 - cxm) / max(r[4] for r in raw)
    tiers = []
    prev = None
    for k, (bot, f, cx, aw, ae) in enumerate(raw):
        aw = max(3.0, min(aw * sw, cx - x0))
        ae = max(3.0, min(ae * se, x1 - cx))
        # now and then one bough reaches past the cone line (a tier is never a clean triangle)
        if 1 < k < len(raw) - 1 and rng.random() < 0.4:
            if rng.random() < 0.5:
                aw = min(aw + rng.uniform(3.0, 6.0), cx - x0)
            else:
                ae = min(ae + rng.uniform(3.0, 6.0), x1 - cx)
        top = yt + 3 if prev is None else prev - (bot - prev) * rng.uniform(0.5, 0.62)
        n = max(2, int(round((aw + ae) / rng.uniform(6.5, 9.5))))
        tips = np.linspace(cx - aw, cx + ae, n + 1)
        tips[1:-1] += rng.uniform(-1.8, 1.8, n - 1)
        size = min(1.0, (aw + ae) / 40.0)
        deps = rng.uniform(2.2, 5.0, n) * (0.55 + 0.45 * size)
        # each tip hangs its own way: most a texel or so, the odd bough reaching longer and lower
        hangs = rng.uniform(-0.6, 1.2, n + 1) * (0.5 + 0.5 * size)
        long_ = rng.random(n + 1) < 0.18
        hangs[long_] += rng.uniform(1.5, 3.0, long_.sum()) * size
        droop = 1.0 + 2.5 * f
        tiers.append(dict(top=float(top), bot=float(bot), cx=float(cx), aw=float(aw), ae=float(ae), tips=tips,
                          deps=deps, hangs=hangs, droop=float(droop), f=float(f), last=k == len(raw) - 1))
        prev = bot
    return tiers


def _tier_geometry(t, H, W, rng):
    """(mask, bottom row per column, u across the tier, v down it) for one tier."""
    Y, X = np.mgrid[0:H, 0:W].astype(float)
    xs = np.arange(W, dtype=float)
    cx, aw, ae = t['cx'], t['aw'], t['ae']
    reach = np.where(xs < cx, aw, ae)
    tips, deps = t['tips'], t['deps']
    notch = np.zeros(W)
    for i in range(len(tips) - 1):
        a, b = tips[i], tips[i + 1]
        s = (xs - a) / max(1e-6, b - a)
        inside = (s >= 0) & (s <= 1)
        notch[inside] = deps[i] * (1 - np.abs(2 * s[inside] - 1)) ** 0.8
        hg = t['hangs'][i] * (1 - s[inside]) + t['hangs'][i + 1] * s[inside]
        notch[inside] -= hg * np.abs(2 * s[inside] - 1) ** 3
    if t.get('last'):
        notch *= np.clip(np.abs(xs - cx) / 6.0, 0, 1)            # the lowest skirt hangs whole over the trunk
    bottom = t['bot'] + t['droop'] * np.clip(np.abs(xs - cx) / reach, 0, 1) ** 2 - notch
    # the skirt widens from a narrow top to its full reach, its sides frayed a texel by needle tips
    tt = np.clip((Y - t['top']) / max(1.0, t['bot'] - t['top']), 0, 1)
    rch = np.where(X < cx, aw, ae)
    w_y = 0.3 * rch + 0.7 * rch * tt ** 0.7
    fray = ndi.gaussian_filter1d(rng.random(H), 1.0) * 2.4 - 1.2
    side = np.abs(X - cx) <= w_y + fray[:, None]
    m = (Y >= t['top']) & (Y <= bottom[None, :]) & side
    u = np.clip((X - cx) / np.maximum(1.0, w_y), -1.3, 1.3)
    v = np.clip((Y - t['top']) / np.maximum(1.0, bottom[None, :] - t['top']), 0, 1)
    return m, bottom, u, v


def frost_crown(S, form, seed, load=1.0):
    """A Frostline conifer's crown in the canvas of S (the woodland pine's master crown at this
    form's size, so the picture keeps its size): (codes, mask)."""
    rng = np.random.default_rng(seed * 7 + 31)
    H, W = S.shape
    ys, xs = np.nonzero(S)
    yt, yb, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    cxm = (x0 + x1) / 2.0
    tiers = _tier_plan(rng, yt, yb, x0, x1, cxm, form)
    n = len(tiers)
    geo = [_tier_geometry(t, H, W, rng) for t in tiers]
    owner = np.full((H, W), -1, int)
    U = np.zeros((H, W))
    V_ = np.zeros((H, W))
    for k in range(n - 1, -1, -1):
        m = geo[k][0]
        owner[m] = k
        U[m] = geo[k][2][m]
        V_[m] = geo[k][3][m]
    # the leader: a short spike over the top tier, leaning with it
    lx = int(round(tiers[0]['cx']))
    for y in range(yt, int(tiers[0]['top']) + 3):
        owner[y, lx] = 0
        if y > yt + 1:
            owner[y, lx - 1] = 0
    mask = owner >= 0
    Y, X = np.mgrid[0:H, 0:W]
    above = np.full_like(owner, -1)
    above[1:] = owner[:-1]
    # rows under the overhang of the tier above (its shade on this tier's top)
    under = np.zeros((H, W), int)
    edge = mask & (above >= 0) & (above < owner)
    for j in range(4):
        sh = np.zeros_like(edge)
        sh[j:] = edge[:H - j] if j else edge
        sh &= mask
        if j:
            sh &= (np.roll(owner, j, 0) == owner) | edge
        under[sh & (under == 0)] = 4 - j
    # light: west lit, east shaded, the upper skirt facing the sky, the tips' underside darker, the
    # whole tree a little lighter towards its top
    ry = (Y - yt) / max(1, yb - yt)
    L = 0.52 - 0.40 * U + 0.30 * (0.5 - V_) + 0.10 * (0.5 - ry)
    L -= np.choose(np.clip(under, 0, 4), [0.0, 0.08, 0.2, 0.34, 0.5])
    b = np.clip(np.floor(L * 5.0), 0, 4).astype(int)
    b = np.where(mask, b, 0)
    code = np.full((H, W), -1, np.int64)
    # the body of each band in broad sibling patches (hue, not value)
    fam = np.minimum((K.vhash(X // 5, Y // 3, seed + 3) * 4).astype(int), 3)
    for bb in range(5):
        for j in range(4):
            sel = mask & (b == bb) & (fam == j)
            code[sel] = _band(bb, j if bb < 4 else 0)
    # needle clumps: fans of needles hanging down and out from the trunk, shingled in rows along each
    # tier and drawn from the bough's tip back up (the clump above hangs in front of the one below):
    # a lit cap on the top and west (a tone up; on the shaded side only now and then), the body at its
    # band's value in one of four sibling families, the shade under it a tone down. Deep in the shade
    # under each tier they stay quiet (body and shade only).
    for k, t in enumerate(tiers):
        m_k = owner == k
        y0 = int(t['top']) - 2
        y1 = int(t['bot'] + t['droop'] + t['hangs'].max()) + 2
        rows = list(range(y0, y1, 4))
        plan = []
        for r_, ay in enumerate(rows):
            off = int(round(2.5 * (r_ % 2))) + int(rng.integers(0, 2))
            for ax in range(int(t['cx'] - t['aw']) - 3 + off, int(t['cx'] + t['ae']) + 4, 5):
                plan.append((ay + int(rng.integers(-1, 2)), ax + int(rng.integers(-1, 2)), int(rng.integers(0, len(SPRAYS))),
                             int(rng.integers(0, 4)), rng.random()))
        for ay, ax_, si, fam_j, rr in reversed(plan):
            if not (0 <= ay < H and 0 <= ax_ < W) or not m_k[ay, ax_]:
                continue
            u = U[ay, ax_]
            sm, cap, rim = SPRAYS[si]
            if u > 0:
                sm, cap, rim = sm[:, ::-1], cap[:, ::-1], rim[:, ::-1]
            hh, ww = sm.shape
            yy0, xx0 = ay - 1, ax_ - ww // 2
            quiet = under[ay, ax_] >= 3
            lit = (u < 0.3 or rr < 0.3) and not quiet
            for dy in range(hh):
                for dx in range(ww):
                    if not sm[dy, dx]:
                        continue
                    yy, xx = yy0 + dy, xx0 + dx
                    if not (0 <= yy < H and 0 <= xx < W) or not m_k[yy, xx]:
                        continue
                    bb = b[yy, xx]
                    if cap[dy, dx] and lit:
                        c = _band(bb + 1, fam_j)
                    elif rim[dy, dx]:
                        c = _band(bb - 1, (fam_j + 1) % 4)
                    else:
                        c = _band(bb, fam_j)
                    code[yy, xx] = c
    # no lone texels in the needles (house-style 4: a lone pixel is a rivet or a glint, not foliage)
    code[~mask] = -1
    V.tidy(code, passes=2)
    # the yellow-green rim on the lit west edge of each skirt's upper part
    left = np.zeros_like(mask)
    left[:, 1:] = mask[:, :-1]
    rim = mask & ~left & (U < -0.4) & (V_ < 0.75) & (under == 0)
    code[rim] = np.where(K.vhash(X, Y // 2, seed + 8)[rim] < 0.7, C('grass_cool', 4), C('leaf_warm', 4))
    snow = _shelves(code, owner, tiers, geo, U, above, rng, load, form)
    allm = mask | snow
    code[~allm] = -1
    V.tidy(code, passes=3)
    return code, allm


def _shelves(code, owner, tiers, geo, U, above, rng, load, form):
    """Snow on every bough (Matt's review of round 3: not one white triangle stamped on every bough):
    on each tier a shelf lies on each bough from the tip back to the trunk, its lower edge following
    the bough (so it sags at the tip), heaped on the west and thinning to nothing on the east,
    some boughs bare; under the tier above a dark row of needles is left between them, so the tiers
    read apart. Lit snow 5 on its top and west ends, the body snow 4, cool to the east, a cool lower
    edge, the needles under it in deep shade; on an exposed bough a heaped lump rises a row over the
    silhouette."""
    H, W = owner.shape
    T0 = FORMS[form][3] * load
    snow = np.zeros((H, W), bool)
    row = np.full((H, W), -1, int)
    nrows = np.zeros((H, W), int)
    xs = np.arange(W, dtype=float)
    for k, t in enumerate(tiers):
        m_k = owner == k
        bottom = geo[k][1]
        cols = np.nonzero(m_k.any(0))[0]
        if not len(cols):
            continue
        tips = t['tips']
        reach = np.where(xs < t['cx'], t['aw'], t['ae'])
        uu = np.clip((xs - t['cx']) / reach, -1, 1)
        th = np.zeros(W)
        for i, tp in enumerate(tips):
            if rng.random() < 0.12 and 0 < i < len(tips) - 1:
                continue                                                  # a bare bough
            half = 0.5 * ((tips[min(i + 1, len(tips) - 1)] - tips[max(i - 1, 0)]) / (2 if 0 < i < len(tips) - 1 else 1))
            half = max(2.5, half * 1.05)
            ui = float(np.clip((tp - t['cx']) / (t['aw'] if tp < t['cx'] else t['ae']), -1, 1))
            side = max(0.0, 1.2 - 0.6 * (ui + 1))
            if t['f'] > 0.45 and ui > 0.4:
                side *= 0.35
            amp = T0 * rng.uniform(0.65, 1.25) * side * (0.75 + 0.25 * min(1.0, (t['aw'] + t['ae']) / 30))
            c = tp - rng.uniform(0.5, 1.8)
            lump = np.clip(1 - ((xs - c) / half) ** 2, 0, 1) ** 0.55 * amp
            th = np.maximum(th, lump)
        hang = np.where(uu > 0.3, 4, np.where(uu < -0.3, 2, 3)) - (1 if form.startswith('krummholz') else 0)
        # the shelf's lower edge follows the bough, eased (it sags towards each tip without copying
        # the needles' notches)
        bot_s = ndi.gaussian_filter1d(bottom, 2.6, mode='nearest')
        for x in cols:
            colm = np.nonzero(m_k[:, x])[0]
            yv = int(colm.min())
            exposed = above[yv, x] < 0
            yl = int(round(min(bot_s[x], colm.max()))) - int(hang[x])
            tk = th[x]
            if tk < 1.5:
                continue
            ys0 = max(yv, int(round(yl - tk)))
            if exposed and tk >= 4.0 and yl - tk <= yv and yv - 1 >= 0 and owner[yv - 1, x] < 0:
                ys0 = yv - 1
            ys1 = yl
            if ys1 - ys0 < 1:
                continue
            for y in range(ys0, ys1):
                snow[y, x] = True
                row[y, x] = y - ys0
                nrows[y, x] = ys1 - ys0
    # no one-texel slot of green left inside a shelf
    gap = ~snow & (owner >= 0) & np.roll(snow, 1, 1) & np.roll(snow, -1, 1)
    snow |= gap
    row[gap] = 1
    nrows[gap] = 3
    lft = np.zeros_like(snow)
    lft[:, 1:] = snow[:, :-1]
    rgt = np.zeros_like(snow)
    rgt[:, :-1] = snow[:, 1:]
    sky = np.zeros_like(snow)
    sky[1:] = ~(owner[:-1] >= 0) & ~snow[:-1]
    sky[0] = True
    up_green = np.zeros_like(snow)
    up_green[1:] = (owner[:-1] >= 0) & ~snow[:-1]
    # the house snow recipe on a shelf: a lit top (snow 5 west, 4), the body, then its front face
    # turning from the light (snow_cool 3, then 2 at the bottom of a deep shelf), cooler to the east
    c = np.where(U < 0.35, C('snow', 4), C('snow_cool', 4))
    top = row == 0
    c = np.where(top & (U < 0.25), C('snow', 5), c)
    c = np.where(top & up_green & (U >= 0.25), C('snow_cool', 4), c)
    c = np.where(~lft & ~top & (U < 0.3), C('snow', 5), c)
    face = (row >= np.maximum(1, nrows - 2)) & (nrows >= 2)
    c = np.where(face, C('snow_cool', 3), c)
    c = np.where((row == nrows - 1) & (nrows >= 4), C('snow_cool', 2), c)
    c = np.where(~rgt & ~top, C('snow_cool', 3), c)
    c = np.where((U > 0.5) & ~top, np.where(row == nrows - 1, C('snow_cool', 2), C('snow_cool', 3)), c)
    code[snow] = c[snow]
    # the needles under each shelf: deep shade, a second row on the east
    below = np.zeros_like(snow)
    below[1:] = snow[:-1]
    sh1 = below & ~snow & (owner >= 0)
    code[sh1] = np.where(U[sh1] < -0.45, C('leaf_cool', 2), C('leaf_cool', 1))
    sh2 = np.zeros_like(snow)
    sh2[1:] = sh1[:-1]
    sh2 &= ~snow & (owner >= 0) & (U > -0.2)
    code[sh2] = C('leaf_cool', 2)
    return snow


def conifer(form='pine', load=1.0, seed=None):
    """A conifer of the Frostline at the woodland pine's size for its form (`spruce` tall and narrow,
    `pine`, `squat` wind-cropped, `krummholz` a low tree-line spruce flagged to the lee): tiers of
    boughs with snow lying on them (frost_crown), over the woodland pine's barked trunk, and a small
    drift banked at the trunk's west foot."""
    from scripts.art.native import compose as CO
    from scripts.art.native import screen as SCR
    from scripts.art.native import woodtrees as WT
    from scripts.art.native import ctx
    scale, s0 = CONIFERS[form]
    seed = s0 if seed is None else seed
    arr = np.asarray(CO.old_sprite(SCR._master('zones_props_pine.png'), raw=True)[0])
    tw = SCR.tree_dims('zones_props_pine.png')['tw']
    d = ctx.D
    rng = np.random.default_rng(seed * 7 + 31)
    S, foot, _ = WT.master_crown(arr, d, size=scale)
    code, mask = frost_crown(S, form, seed, load)
    # the crown's silhouette closed in each material's own edge tone (lit edges in its tone 1)
    pad = 2
    big = np.full((code.shape[0] + 2 * pad, code.shape[1] + 2 * pad), -1, np.int32)
    big[pad:-pad, pad:-pad] = np.where(mask, code, -1)
    V.outline(big)
    code = big.astype(np.int64)
    mask = big >= 0
    foot = (foot[0] + pad, foot[1] + pad)
    T = tw * d * (0.8 if form.startswith('krummholz') else 1.0)
    cols = int(round(foot[0]))
    half_t = max(2, int(T / 2))
    band = mask[:, max(0, cols - half_t):cols + half_t + 1]
    bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
    cb = min(bots) if bots else foot[1] - 10 * d
    length = int(foot[1] - cb + (4 if form.startswith('krummholz') else 10))
    tc, tm, (tfx, tfy), _ty = WT.trunk2('oak', length, T * 0.6, T * 1.05, rng, lean=2, twist=1.0, roots=3, limbs=0,
                                        limb_rise=12.0, limb_spread=0.0, bark='oak', front_root=False,
                                        root_rows=(5, 12), root_reach=(1, 8), root_w=(0.45, 3.4))
    out, ft = WT._compose((tc, tm, (tfx, tfy)), code, mask, foot)
    WT._close_pinholes(out)
    out, ft = WT._crop(out, ft)
    # the snow's bounce on the bark: the trunk's shaded east side takes a cool step of light from the
    # snow it stands in, two texels inside its edge, below the crown's shade (so it reads round)
    bark = np.isin(out // 8, [FI[f] for f in WT.BARKS['oak'][0]]) & (out >= 0)
    greens = [FI[f] for f in ('leaf', 'leaf_cool', 'leaf_warm', 'grass', 'grass_cool')]
    crown_rows = np.nonzero(np.isin(out // 8, greens).any(1))[0]
    yc = int(crown_rows.max()) + 6 if len(crown_rows) else 0
    for y in range(yc, out.shape[0] - 2):
        cols = np.nonzero(bark[y])[0]
        if len(cols) < 6:
            continue
        xe = int(cols.max())
        for x in (xe - 1, xe - 2):
            c = int(out[y, x])
            if bark[y, x] and c % 8 <= 2 and c != C('timber_cool', 0):
                out[y, x] = c + 1
    # the drift banked at the trunk's west foot: a lit crest, its body, a cool east fall, a shade row
    # at its foot
    fx, fy = int(round(ft[0])), int(round(ft[1]))
    pad = 6
    big = np.full((out.shape[0] + 2, out.shape[1] + 2 * pad), -1, np.int64)
    big[:out.shape[0], pad:pad + out.shape[1]] = out
    fx += pad
    xc = fx - 8 + int(rng.integers(-1, 2))
    for x in range(fx - 15, fx):
        h = int(round(3.6 - abs(x - xc) * 0.42 - (0.6 if x > xc else 0.0)))
        for k_ in range(max(0, h)):
            y = fy - k_
            if not (0 <= y < big.shape[0]):
                continue
            if big[y, x] >= 0 and x > fx - 4:
                continue                                                  # the root stays over it
            top_ = k_ == h - 1
            c = C('snow', 5) if (top_ and x <= xc) else C('snow', 4) if (top_ or x < xc) else C('snow_cool', 4)
            if k_ == 0:
                c = C('snow_cool', 3) if x <= xc + 1 else C('snow_cool', 2)
            big[y, x] = c
    out = big
    pic = K.crop(out.astype(np.int32), fx, fy)
    return pic



def _snag_dress(seed, stubs):
    """The dead pine's surface, laid after shading: silvered wood in spiral grain (streaks a tone down
    along the twist, two texels or more), drying checks (a dark split with a lit west lip), a knot
    ring where each stub leaves the bole, the last plates of bark clinging low on the sheltered east
    side, wolf lichen in small clusters on the lit west, and the snow shaded by its own planes."""
    def dress(sc, a):
        rng = np.random.default_rng(seed + 3)
        H, W = a.shape
        Y, X = np.mgrid[0:H, 0:W]
        wood = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag == 'wood']) & (a >= 0)
        if not wood.any():
            return
        L = sc.light()
        inner = ndi.binary_erosion(wood, iterations=1)
        ys, xs = np.nonzero(wood)
        y1 = ys.max()
        # spiral grain: streaks one texel wide, 3 to 8 long, leaning a texel every 6 rows (the twist)
        sid = X + (Y // 6)
        run = (Y + (K.vhash(sid, 0, seed) * 8).astype(int)) // int(rng.integers(5, 8))
        streak = inner & (K.vhash(sid, run, seed + 1) < 0.34)
        a[streak] = (a[streak] // 8) * 8 + np.clip(a[streak] % 8 - 1, 0, 5)
        lit_s = inner & ~streak & (L > 0.62) & (K.vhash(sid, run, seed + 2) < 0.18)
        a[lit_s] = (a[lit_s] // 8) * 8 + np.clip(a[lit_s] % 8 + 1, 0, 5)
        # drying checks: long splits following the twist
        for _ in range(int(rng.integers(3, 5))):
            k = int(rng.integers(0, len(ys)))
            y, x = int(ys[k]), int(xs[k])
            for j in range(int(rng.integers(8, 20))):
                yy, xx = y + j, x + (j + (y % 6)) // 6
                if not (0 <= yy < H and 0 <= xx < W) or not inner[yy, xx]:
                    break
                a[yy, xx] = C('soot', 1)
                if inner[yy, xx - 1]:
                    a[yy, xx - 1] = C('ash', 5) if L[yy, xx - 1] > 0.4 else C('ash', 3)
        # knots where the stubs leave the bole
        for (ky, kx) in stubs:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = ky + dy, kx + dx
                    if 0 <= yy < H and 0 <= xx < W and wood[yy, xx]:
                        a[yy, xx] = C('ash', 3) if (dy, dx) == (0, 0) else C('soot', 2)
        # the last bark, low on the sheltered east: plates of weathered bark with dark edges
        base = wood & (Y > y1 - 34) & (Y < y1 - 3)
        bys, bxs = np.nonzero(base)
        for _ in range(3):
            if not len(bys):
                break
            k = int(rng.integers(0, len(bys)))
            cy, cx = int(bys[k]), int(bxs[k])
            row = np.nonzero(wood[cy])[0]
            cx = int(row.max()) - int(rng.integers(1, 4))
            rx_, ry_ = rng.uniform(1.8, 2.8), rng.uniform(2.5, 4.5)
            rag = K.vhash(X, Y // 2, seed + int(rng.integers(0, 99))) * 0.5
            pm = wood & (((X - cx) / rx_) ** 2 + ((Y - cy) / ry_) ** 2 <= 1.0 + rag)
            a[pm] = np.where(L[pm] > 0.45, C('timber_cool', 3), C('timber_cool', 2))
            fis = ndi.binary_erosion(pm) & (((X + Y // 3) % 3) == 0)          # the bark's furrows
            a[fis] = C('soot', 2)
            ed = pm & ~ndi.binary_erosion(pm) & wood
            a[ed & (X >= cx)] = C('soot', 1)
            a[ed & (X < cx) & (Y <= cy)] = C('stone_cool', 4)
        # wolf lichen: small chartreuse clusters on the lit west face, more up the bole
        cand = np.nonzero(inner & (L > 0.35) & (Y < y1 - 20) & (X < np.median(xs) + 1))
        for _ in range(int(rng.integers(7, 10))):
            if not len(cand[0]):
                break
            k = int(rng.integers(0, len(cand[0])))
            cy, cx = int(cand[0][k]), int(cand[1][k])
            for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))[:int(rng.integers(3, 6))]:
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < H and 0 <= xx < W and wood[yy, xx]:
                    a[yy, xx] = C('grass_warm', 4) if dy == 0 else C('grass_warm', 3)
        # the snow: on each stub a ridge lit on top and west, cool on its front and east end; the
        # drift shaded by its own planes (a lit crest, the body, a cool east and front fall)
        sn = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in ('snow', 'drift')]) & (a >= 0)
        up = np.zeros_like(sn)
        up[1:] = sn[:-1]
        rt = np.zeros_like(sn)
        rt[:, :-1] = sn[:, 1:]
        v = L + K.vhash((X + Y // 3) // 3, Y // 2, 77) * 0.12
        c = np.where(v > 0.8, C('snow', 5), np.where(v > 0.62, C('snow', 4), np.where(v > 0.4, C('snow_cool', 4),
                     C('snow_cool', 3))))
        c = np.where(~up & (v > 0.5), C('snow', 5), c)
        c = np.where(up & ~rt, C('snow_cool', 3), c)
        a[sn] = c[sn]
        _crust(sc, a, seed, rate=0.25)
    return dress


def snag(seed=541):
    """A dead pine at the tree line: a silvered bole leaning a little east and tapering, its grain
    twisting, its top snapped into two jagged points, four stub limbs of different lengths rising a
    little from the bole, snow on the break and the stubs, a drift at its west foot, a root flare;
    its surface dressed by _snag_dress."""
    sc = K.Scene(-36, 36, -16, 14, 200)
    rng = np.random.default_rng(seed)
    h = 0.0
    r = 8.6
    x = 0.0
    sc.ellipsoid(0, 0, 2.0, 12.5, 7.5, 4.4, WEATHERED, base=2.4, k=1.6, tag='wood', flat=1.2)          # the root flare
    for k in range(8):
        z1 = h + 17 + rng.uniform(-2, 2)
        sc.cylinder(x, 0, r, h, z1, WEATHERED, base=2.7, k=1.7, tag='wood', mix=rng.random(), tex='wood_v')
        h = z1
        r = max(2.6, r - 0.75)
        x += 0.6 + k * 0.08
    sc.cylinder(x - 1.2, 0, 1.8, h, h + 14, WEATHERED, base=2.9, k=1.7, tag='wood')                 # the snapped points
    sc.cylinder(x + 1.5, 0, 1.4, h, h + 8, WEATHERED, base=2.6, k=1.7, tag='wood')
    stubs_w = []
    for (z, ln, side) in ((58, 9, -1), (78, 13, 1), (101, 7, -1), (119, 10, 1)):
        xx = x * z / max(1.0, h)
        rr = max(2.6, 8.6 - 0.75 * z / 17.0)
        x0, x1 = (xx - rr - ln, xx - rr * 0.6) if side < 0 else (xx + rr * 0.6, xx + rr + ln)
        sc.box(x0, -1.3, z, x1, 1.3, z + 2.8, WEATHERED, base=2.8, k=1.6, tag='wood', round_=0.9)
        tip = x0 if side < 0 else x1
        sc.box(tip - 1.2 if side < 0 else tip - 1.2, -1.1, z + 1.0, tip + 1.2, 1.1, z + 4.2, WEATHERED, base=2.8, k=1.6,
               tag='wood', round_=0.8)                                                              # the stub's upturned end
        sc.box(x0 + (1.5 if side < 0 else 0.5), -0.6, z + 2.6, x1 - (0.5 if side < 0 else 2.0), 0.3, z + 3.6, SNOW, base=3.9,
               k=1.0, tag='snow', round_=0.5)
        stubs_w.append((xx + side * rr * 0.75, z + 1.4))
    _snowcap(sc, x - 1.2, 0.0, h + 14.5, 2.0, 1.7, th=1.5, seed=seed)
    _drift_west(sc, -10, 2, 9.5, seed)
    sc.render()
    stubs = []
    for (wx, wz) in stubs_w:
        px, py = sc.ox + wx, sc.oy - wz
        stubs.append((int(round(py)), int(round(px))))
    a = _solo(sc, dress=_snag_dress(seed, stubs))
    return K.crop(a, sc.ox, sc.oy)
