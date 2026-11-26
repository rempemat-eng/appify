"""Frostline conifers and dead pines."""
from __future__ import annotations

from ._shared import (
    C,
    FI,
    K,
    SNOW,
    V,
    WEATHERED,
    _drift_west,
    _snowcap,
    _solo,
    ndi,
    np,
)

# ------------------------------------------------------------------------------------------------
# conifers (F-P1, Z2; A3 round 3, 27 Nov): every crown built from bough masses as the approved woodland
# pine is (a lobed spray pad each, a lit cap on its upper west, its body, a dark pocket under it), the
# species told apart by their build: a spruce a dense narrow cone of drooping tiers to near the ground,
# a pine a high open crown of rounded clumps on limbs over a long warm bole, a squat pine a broad
# wind-cropped cone, a krummholz a mat on the snow with flag branches streaming to the lee. Snow lies in
# a few long loads on the pads' tops, heavy at the trunk end and on the west, thinning to the tip.
# ------------------------------------------------------------------------------------------------
# (scale of the woodland pine's master crown (x, y), seed): the picture's size and the variant's seed
CONIFERS = {'spruce': ((0.95, 1.06), 507), 'pine': ((1.0, 1.0), 511), 'squat': ((1.18, 0.74), 521),
            'krummholz': ((1.25, 0.44), 531), 'krummholz_b': ((1.0, 0.36), 547), 'krummholz_c': ((1.4, 0.52), 559)}

# the crown's value bands, pocket to cap, cooled towards the snow (round 3, F8): each band lists
# siblings at nearly one value, so a pad can change family without stepping a tone
BANDS = [(('leaf_cool', 0), ('leaf_cool', 0), ('grass_cool', 0)),
         (('leaf_cool', 1), ('leaf_cool', 1), ('leaf', 1)),
         (('leaf_cool', 2), ('grass_cool', 1), ('leaf_cool', 2)),
         (('leaf_cool', 3), ('grass_cool', 2), ('leaf', 3)),
         (('grass_cool', 3), ('leaf_cool', 4), ('grass_cool', 3)),
         (('grass_cool', 4), ('leaf_cool', 5), ('grass_cool', 4))]


def _band(b, j=0):
    b = int(min(len(BANDS) - 1, max(0, b)))
    f, t = BANDS[b][j % len(BANDS[b])]
    return C(f, t)


# ---------------------------------------------------------------------------------------- the pads
def _pad_mask(w, h, rng, side, tip):
    """One spray pad, w x h texels, drawn for its side of the tree (-1 west, 1 east): a lobe with a
    rounded top, its outer end hanging lower than its inner, its lower edge scalloped into two or three
    sub-sprays; its tip `blunt`, `splay` (two or three needle points) or `long` (a drooping end 2 to
    8 texels beyond the lobe). Returns (mask, top row per column, bottom row per column)."""
    W = int(w) + 10
    H = int(h) + 10
    m = np.zeros((H, W), bool)
    xs = np.arange(W) - 5.0
    cx = (w - 1) / 2.0
    u = (xs - cx) / max(1.0, w / 2.0)
    outer = u * side                                          # 1 at the pad's outer end
    sag = np.clip(outer, 0, 1) ** 1.5 * rng.uniform(1.0, 3.0)  # the outer end hangs lower
    top = 2.0 + h * 0.5 * (1 - np.sqrt(np.clip(1 - u * u, 0, 1))) * rng.uniform(0.9, 1.4) + sag * 0.6
    nsub = int(rng.integers(2, 4))
    phase = rng.uniform(0, np.pi)
    scal = np.abs(np.sin((u + 1) * np.pi * nsub / 2 + phase)) * rng.uniform(0.8, 2.0)
    bot = 2.0 + h - scal + sag
    for x in range(W):
        if abs(u[x]) > 1.0:
            continue
        y0, y1 = int(round(top[x])), int(round(bot[x]))
        if y1 >= y0:
            m[max(0, y0):min(H, y1 + 1), x] = True
    # the tip at the outer lower end
    ox = int(round(5 + (w - 1 if side > 0 else 0)))
    oy = int(round(2 + h + sag.max() * 0.7))
    if tip == 'splay':
        for dx, dy in ((1, 0), (1, 1), (2, 2), (1, -1), (2, 0))[:int(rng.integers(3, 6))]:
            xx, yy = ox + side * dx, min(H - 1, oy - 1 + dy)
            if 0 <= xx < W:
                m[max(0, yy - 1):yy + 1, xx] = True
    elif tip == 'long':
        ln = int(rng.integers(2, 9))
        for j in range(ln):
            xx = ox + side * (j + 1)
            yy = min(H - 2, oy - 2 + int(j * rng.uniform(0.3, 0.7)))
            if 0 <= xx < W:
                m[yy:yy + 2, xx] = True                           # two texels thick where it joins
    m = ndi.binary_closing(np.pad(m, 1), structure=np.ones((2, 2), bool))[1:-1, 1:-1]
    return m


def _place_pad(pads, pid, mask, x0, y0, side, tier, H, W):
    ys, xs = np.nonzero(mask)
    ys = ys + y0
    xs = xs + x0
    ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
    pads.append(dict(id=pid, ys=ys[ok], xs=xs[ok], side=side, tier=tier))


# ---------------------------------------------------------------------------------- tree builds
def _tiers_cone(rng, yt, yb, x0, x1, cxm, kind, build=None):
    """The tiers of a coned tree (spruce, squat): [(bot row, west reach, east reach, centre)], top
    first, with uneven pitches, a fuller side, a tier set off the axis and the odd short side."""
    if kind == 'spruce':
        pitch, power = rng.uniform(13.0, 16.0), 1.0
    else:
        pitch, power = rng.uniform(15.0, 19.0), 0.7
    # the variant's own build: a narrower or fuller tree, a crown starting higher or lower on the bole,
    # now and then a broken top (a spruce) or a top cropped flat by the wind (a squat)
    bd = build or {}
    wf = bd.get('wf', rng.uniform(0.85, 1.0))
    H0 = yb - yt
    yt = yt + H0 * bd.get('top', 0.0)
    yb = yb - H0 * bd.get('base', 0.0)
    x0 = cxm - (cxm - x0) * wf
    x1 = cxm + (x1 - cxm) * wf
    H = yb - yt
    first = yt + rng.uniform(8, 12)
    span = yb - first
    steps = []
    acc = 0.0
    while acc < span:
        st = pitch * rng.uniform(0.65, 1.4) * (0.7 + 0.55 * acc / max(1.0, span))
        steps.append(st)
        acc += st
    steps = np.array(steps[:max(1, len(steps) - (1 if acc - span > 0.5 * steps[-1] else 0))])
    steps *= span / steps.sum()
    bots = [first] + list(first + np.cumsum(steps))
    lean = bd.get('lean', rng.uniform(-3.0, 3.0))
    side_w, side_e = rng.uniform(0.72, 1.0), rng.uniform(0.72, 1.0)
    out = []
    for k, b in enumerate(bots):
        f = (b - yt) / H
        g = 0.13 + 0.87 * f ** power
        if kind == 'squat':
            g = min(1.0, g * 1.05) if f > 0.2 else g
        aw = g * side_w * rng.uniform(0.82, 1.12)
        ae = g * side_e * rng.uniform(0.82, 1.12)
        if 0 < k < len(bots) - 1 and rng.random() < 0.25:
            if rng.random() < 0.5:
                aw *= 0.7
            else:
                ae *= 0.7
        cx = cxm + lean * (1 - f) ** 2 + (rng.uniform(-2.0, 2.0) if 0 < k < len(bots) - 1 and rng.random() < 0.3 else 0)
        out.append([b, f, cx, aw, ae])
    sw = (cxm - x0) / max(r[3] for r in out)
    se = (x1 - cxm) / max(r[4] for r in out)
    return [(b, f, cx, min(aw * sw, cx - x0), min(ae * se, x1 - cx)) for b, f, cx, aw, ae in out]


def _pads_cone(rng, H, W, yt, yb, x0, x1, cxm, kind, build=None):
    """Spray pads along each tier of a coned tree, bottom tier first (so a tier above hangs in front)."""
    tiers = _tiers_cone(rng, yt, yb, x0, x1, cxm, kind, build)
    pads = []
    pid = 0
    prev_bot = yt
    tops = []
    for k, (b, f, cx, aw, ae) in enumerate(tiers):
        tops.append(prev_bot)
        prev_bot = b
    order = list(range(len(tiers)))[::-1]
    for k in order:
        b, f, cx, aw, ae = tiers[k]
        top_k = tops[k]
        span = aw + ae
        # two rows a tier: a back row of pads up under the tier above, then the front row hanging
        # at the tier's foot, staggered, so a tier is a mass of boughs and not a course of bricks
        for row in (0, 1):
            wmin, wmax = ((10, 15) if kind == 'spruce' else (12, 17))
            n = max(2, int(round(span / rng.uniform(wmin - 1, wmax - 2))))
            n = min(n, 6)
            ws = rng.uniform(0.65, 1.4, n)
            ws = ws / ws.sum() * (span + 6) * (0.85 if row == 0 else 1.0)
            xa = cx - aw * (0.85 if row == 0 else 1.0) - 2 + (rng.uniform(2, 5) if row == 0 else 0)
            cells = []
            for i in range(n):
                cells.append((xa, ws[i]))
                xa += ws[i] - (6.0 / max(1, n - 1) if n > 1 else 0)
            idx = sorted(range(n), key=lambda i: -abs((cells[i][0] + cells[i][1] / 2) - cx))
            for i in idx:
                xl, w = cells[i]
                xc = xl + w / 2
                side = -1 if xc < cx else 1
                reach = aw if side < 0 else ae
                outer = min(1.0, abs(xc - cx) / max(1.0, reach))
                h = float(np.clip(w * rng.uniform(0.5, 0.68), 6.0, 11.0))
                if row == 0:
                    # the back row tucks up under the tier above and reaches down behind the front row,
                    # so no sky shows between tiers
                    h = float(np.clip(max(h, (b - top_k) * 0.75 + 2.0), 6.0, 15.0))
                    pb = top_k + h - rng.uniform(2.0, 4.0)
                else:
                    droop = (1.5 + 3.5 * f) * outer ** 2 * rng.uniform(0.6, 1.5)
                    pb = b + droop + rng.uniform(-1.0, 2.0)
                tip = rng.choice(['blunt', 'splay', 'long', 'blunt'], p=[0.35, 0.3, 0.15, 0.2]) if row else 'blunt'
                m = _pad_mask(max(6.0, w), h, rng, side, tip)
                _place_pad(pads, pid, m, int(round(xl - 5)), int(round(pb - h - 2)), side, k, H, W)
                pid += 1
    return pads, tiers


def _pads_pine(rng, H, W, yt, yb, x0, x1, cxm):
    """A Scots pine's crown (director's note on round 3): six to nine overlapping rounded clumps that
    merge into one irregular, flat-topped mass over the upper two thirds of the tree, wider than it is
    deep: a top row of two or three clumps at nearly one height (the flat top), a fuller middle row,
    and one or two clumps low on the sides; one or two small gaps where clumps part and a limb shows,
    and one broken limb on the variant. Returns (pads, limbs, the row under the crown, the broken
    limb or None)."""
    pads = []
    limbs = []
    pid = 0
    clump = 0
    Hc = yb - yt
    lean = rng.uniform(-6.0, 6.0)
    hw_w, hw_e = cxm - x0, x1 - cxm
    rows = [(yt + Hc * 0.15, int(rng.integers(2, 4)), 0.6), (yt + Hc * 0.42, int(rng.integers(3, 5)), 0.92),
            (yt + Hc * 0.7, int(rng.integers(2, 4)), 1.0)]
    spots = []
    for r_, (y, n, spread) in enumerate(rows):
        cx = cxm + lean * (1 - (y - yt) / Hc)
        xs_ = np.linspace(-1, 1, n) if n > 1 else np.array([0.0])
        if r_ == 2:
            xs_ = np.array([-1.0, 1.0])[:n] if n > 1 else np.array([rng.choice((-1.0, 1.0))])
        for u in xs_:
            reach = hw_w if u < 0 else hw_e
            xc = cx + u * reach * spread * rng.uniform(0.62, 0.8) + rng.uniform(-3, 3)
            spots.append((r_, xc, y + rng.uniform(-3, 3), cx))
    # the crown's back mass: pads across its middle, drawn first, so the clumps in front merge into
    # one irregular crown; one or two windows are left where the limbs show
    cxc = cxm + lean * 0.5
    gaps = [(cxc + rng.choice((-1, 1)) * rng.uniform(0.3, 0.6) * hw_w, yt + Hc * rng.uniform(0.45, 0.6))
            for _ in range(int(rng.integers(1, 3)))]
    for k in range(int(rng.integers(15, 20))):
        w = rng.uniform(22, 32)
        h = w * rng.uniform(0.55, 0.7)
        py = yt + Hc * rng.uniform(0.14, 0.8)
        f_ = (py - yt) / Hc
        px = cxc + rng.uniform(-1.0, 1.0) * (hw_w + hw_e) / 2 * (0.55 + 0.3 * min(1.0, f_ * 1.6))
        if any(abs(px - gx) < 9 and abs(py - gy) < 7 for gx, gy in gaps):
            continue
        m = _pad_mask(w, h, rng, -1 if px < cxc else 1, 'blunt')
        _place_pad(pads, pid, m, int(round(px - w / 2 - 5)), int(round(py - h / 2 - 2)), -1 if px < cxc else 1, 99, H, W)
        pid += 1
    # bottom row first, so an upper clump hangs in front of the one below
    for r_, xc, yc, cx in sorted(spots, key=lambda q: -q[2]):
        clump += 1
        cw = rng.uniform(34, 46) * (0.85 if r_ == 2 else 1.0)
        ch = cw * rng.uniform(0.6, 0.75)
        if abs(xc - cx) > 8:
            limbs.append((cx, yc + ch * 0.4, xc, yc + ch * 0.25))
        for q in range(int(rng.integers(5, 8))):
            w = cw * rng.uniform(0.42, 0.62)
            h = w * rng.uniform(0.55, 0.72)
            px = xc + rng.uniform(-cw * 0.34, cw * 0.34)
            py = yc + rng.uniform(-ch * 0.35, ch * 0.35) + q * 1.0
            side = -1 if px < cx else 1
            tip = rng.choice(['blunt', 'splay', 'long'], p=[0.5, 0.35, 0.15])
            m = _pad_mask(w, h, rng, side, tip)
            _place_pad(pads, pid, m, int(round(px - w / 2 - 5)), int(round(py - h / 2 - 2)), side, 100 + clump, H, W)
            pid += 1
    # the broken limb: a bare stub out of the crown's lower side, its end snapped
    sgn = rng.choice((-1, 1))
    yb_ = yt + Hc * rng.uniform(0.72, 0.82)
    cxb = cxm + lean * (1 - (yb_ - yt) / Hc)
    broken = (cxb, yb_, cxb + sgn * rng.uniform(12, 20), yb_ - rng.uniform(1, 5))
    low = int(max(q[2] for q in spots) + 14)
    return pads, limbs, low, broken


def _pads_krummholz(rng, H, W, yt, yb, x0, x1, cxm, mat_h):
    """A krummholz as a shrub (director's note on round 3): a dense low mat of wide pads in three rows,
    most of the tree's mass, its top uneven; at most one short stem leaning east out of it, mostly
    hidden in the foliage; one flag of growth streaming east from the stem's top as a ragged wedge
    (deep at the stem, thinning and breaking up downwind); the dead windward stubs on the stem's west.
    Returns (pads, the stem as a polyline, stubs, the mat's top row)."""
    pads = []
    pid = 0
    mat_top = yb - mat_h
    rise = rng.uniform(10, 22)
    sx0 = x0 + (x1 - x0) * rng.uniform(0.26, 0.38)
    y_base = mat_top + mat_h * 0.35
    top = (sx0 + rng.uniform(3, 7), mat_top - rise)
    stem = [(sx0, y_base), (sx0 + (top[0] - sx0) * 0.5 + rng.uniform(-1, 1), (y_base + top[1]) / 2), top]
    stubs = [(top[1] + rng.uniform(2, 6), top[0] - 1, rng.uniform(3, 6)),
             (top[1] + rng.uniform(8, 13), (top[0] + sx0) / 2 - 1, rng.uniform(3, 7))]
    # the flag: a wedge of pads from the stem's top streaming east, deep at the stem, thinning,
    # ragged in height and breaking into a last small pad or two
    ln = (x1 - top[0]) * rng.uniform(0.55, 0.85)
    n = max(3, int(ln / rng.uniform(7, 9)))
    for j in range(n):
        t = j / max(1, n - 1)
        w = rng.uniform(11, 16) * (1.0 - 0.45 * t)
        h = rng.uniform(9, 13) * (1.0 - 0.55 * t) + 2
        px = top[0] - 3 + t * ln + rng.uniform(-1.5, 1.5)
        py = top[1] - 2 + t * rng.uniform(1, 6) + rng.uniform(-2.5, 2.5)
        if t > 0.75 and rng.random() < 0.3:
            continue                                                 # the wedge breaks up downwind
        m = _pad_mask(w, h, rng, 1, rng.choice(['blunt', 'splay', 'long'], p=[0.25, 0.45, 0.3]))
        _place_pad(pads, pid, m, int(round(px - 5)), int(round(py - 2)), 1, 5, H, W)
        pid += 1
    # the mat: a mound of wide pads in three staggered rows, highest near the stem on the windward
    # side and falling away to the lee end, the back row up to the mound's line, the front on the snow
    span = x1 - x0
    for row in (0, 1, 2):
        xa = x0 + span * (0.08, 0.04, 0.02)[row] + rng.uniform(-3, 3)
        xe = x1 - span * (0.05, 0.03, 0.01)[row]
        while xa < xe - 6:
            w = rng.uniform(18, 30)
            h = min(w * rng.uniform(0.5, 0.7), mat_h * rng.uniform(0.45, 0.6))
            xc = xa + w / 2
            mound = 1.0 - 0.45 * abs((xc - (sx0 + span * 0.12)) / span) ** 1.3 - 0.15 * max(0.0, (xc - cxm) / span)
            y_top = yb - mat_h * mound + row * mat_h * 0.26 + rng.uniform(-0.1, 0.1) * mat_h
            side = -1 if xc < cxm else 1
            m = _pad_mask(w, h, rng, side, rng.choice(['blunt', 'splay', 'long'], p=[0.5, 0.35, 0.15]))
            _place_pad(pads, pid, m, int(round(xa - 5)), int(round(y_top - 2)), side, 10 + row, H, W)
            pid += 1
            xa += w * rng.uniform(0.5, 0.75)
    return pads, stem, stubs, mat_top


# ------------------------------------------------------------------------------------ the painter
def _paint_pads(pads, H, W, xmid, hw, yt, yb, rng, seed):
    """Paint the pads in order: for each, first the pocket (the dark band 2 to 3 texels under its lower
    edge, on whatever crown is already there), then the pad: a lit cap on its upper west in the two
    lightest bands, the body, its lower east a band down; a few needle clusters a sibling tone across
    its body. Returns (codes, mask, owner)."""
    code = np.full((H, W), -1, np.int64)
    owner = np.full((H, W), -1, int)
    for p in pads:
        ys, xs = p['ys'], p['xs']
        if not len(ys):
            continue
        pm = np.zeros((H, W), bool)
        pm[ys, xs] = True
        y0, y1, x0_, x1_ = ys.min(), ys.max(), xs.min(), xs.max()
        # the pocket under the pad, on the crown already drawn
        below = np.zeros_like(pm)
        for d, band in ((1, 0), (2, 0), (3, 1)):
            sh = np.zeros_like(pm)
            sh[d:] = pm[:-d]
            sh &= ~pm & (code >= 0) & ~below
            depth_ok = d <= (2 + int(K.vhash(np.array([p['id']]), np.array([d]), seed)[0] < 0.5))
            if depth_ok:
                code[sh] = _band(band, p['id'])
                below |= sh
        # the pad: its body one band by where it stands on the tree (lit west, shaded east, a little
        # lighter high up), its lower east quarter a band down, a lit cap on its upper west (2 to 4
        # texels), its foot a band down; a few clusters of a sibling family across the body
        cxp, cyp = (x0_ + x1_) / 2.0, (y0 + y1) / 2.0
        rx, ry = max(1.0, (x1_ - x0_) / 2.0), max(1.0, (y1 - y0) / 2.0)
        u = (xs - cxp) / rx
        v = (ys - cyp) / ry
        tree_u = (xs - xmid) / max(1.0, hw)
        Lb = 0.5 - 0.42 * float(np.mean(tree_u)) + 0.1 * (0.5 - (cyp - yt) / max(1, yb - yt))
        b0 = 3 if Lb > 0.62 else (2 if Lb > 0.3 else 1)
        b = np.full(len(ys), b0)
        b = np.where(u + v > 0.75, np.maximum(1, b0 - 1), b)
        top_of = np.full(W, 10 ** 6)
        np.minimum.at(top_of, xs, ys)
        capd = 2 + (K.vhash(xs // 4, np.full_like(xs, p['id']), seed + 5) * 3).astype(int)
        cap = (ys - top_of[xs] < capd) & (u < 0.35)
        b = np.where(cap, np.where((ys - top_of[xs] < 1) & (b0 >= 2) & (u < 0.0), np.minimum(5, b0 + 2), b0 + 1), b)
        bot_of = np.full(W, -1)
        np.maximum.at(bot_of, xs, ys)
        rim = (bot_of[xs] - ys < 2) & ~cap
        b = np.where(rim, np.maximum(1, b - 1), b)
        fam = int(K.vhash(np.array([p['id']]), np.array([3]), seed)[0] * 3)
        sib = (K.vhash(xs // 3, ys // 2, seed + 7) < 0.28) & ~cap & ~rim
        code[ys, xs] = [_band(int(bb), fam + (1 if sb else 0)) for bb, sb in zip(b, sib)]
        # a few needle clusters across the body: two or three texels of a sibling family
        body = ~cap & ~rim
        n = max(0, int(body.sum() / 45))
        idx = np.nonzero(body)[0]
        for _ in range(n):
            if not len(idx):
                break
            k = int(idx[int(rng.integers(0, len(idx)))])
            y, x = int(ys[k]), int(xs[k])
            sg = p['side']
            for (yy, xx) in ((y, x), (y + 1, x + sg), (y + 1, x)):
                if 0 <= yy < H and 0 <= xx < W and pm[yy, xx] and code[yy, xx] >= 0:
                    bb = int(b[k]) + (1 if (u[k] < -0.2 and v[k] < 0.3 and rng.random() < 0.5) else 0)
                    code[yy, xx] = _band(max(1, bb), fam + 1)
        owner[ys, xs] = p['id']
    return code, code >= 0, owner


def _loads(code, owner, pads, rng, xmid, hw, heavy, n_range):
    """Snow in a few long loads (round 3, F2): each lies along the visible top of one tier's pads, 12
    to 30 texels long from that side's tip inward, thick at its trunk end and on the west (5 to 8
    texels), thinning to 1 or 2 at the tip; the east and some tiers bare; the lengths drawn from a
    skewed range so no two tiers keep one rhythm."""
    H, W = code.shape
    snow = np.zeros((H, W), bool)
    rowi = np.full((H, W), -1, int)
    nrow = np.zeros((H, W), int)
    tier_of = {p['id']: p['tier'] for p in pads}
    otier = np.full((H, W), -999, int)
    for pid, t in tier_of.items():
        otier[owner == pid] = t
    tiers = sorted(set(tier_of.values()))
    runs = []
    for t in tiers:
        m = otier == t
        cols = np.nonzero(m.any(0))[0]
        if len(cols) < 8:
            continue
        top = np.full(W, -1)
        for c in cols:
            top[c] = np.nonzero(m[:, c])[0].min()
        ref = xmid if t < 100 else float(cols.mean())               # a pine's clump: its own two sides
        for sg in (-1, 1):
            side_cols = [c for c in cols if (c - ref) * sg > 0]
            if len(side_cols) < 6:
                continue
            tu = (np.mean(side_cols) - xmid) / max(1.0, hw)
            w = (1.6 if sg < 0 else 0.45) * (1.3 if tu < 0 else 0.8)
            runs.append((w * rng.uniform(0.5, 1.5), t, sg, side_cols, top, tu))
    runs.sort(key=lambda r: -r[0])
    n = int(rng.integers(*n_range))
    used = 0
    for _w, t, sg, side_cols, top, tu in runs:
        if used >= n:
            break
        if rng.random() < 0.15:
            continue                                                 # a bare bough among the loaded
        tip_end = min(side_cols) if sg < 0 else max(side_cols)
        length = int(np.clip(rng.gamma(4.0, 5.0), 12, 30))
        span = sorted((c for c in side_cols if abs(c - tip_end) <= length), key=lambda c: abs(c - tip_end))
        # the load stops where the tier's top jumps (a gap between pads under the overhang)
        keep = [span[0]]
        for c in span[1:]:
            if abs(c - keep[-1]) > 1 or abs(top[c] - top[keep[-1]]) > 5:
                break
            keep.append(c)
        if len(keep) < 8:
            continue
        tmax = (rng.uniform(5.0, 8.0) if sg < 0 else rng.uniform(3.0, 5.0)) * heavy
        tops_k = ndi.minimum_filter1d(np.array([top[c] for c in keep], float), 3)
        tops_k = np.round(ndi.uniform_filter1d(tops_k, 3)).astype(int)
        for i, c in enumerate(keep):
            s_ = min(1.0, i / 7.0)                                     # thin at the tip, full 7 texels in
            th = max(1.5, tmax * (0.25 + 0.75 * s_ ** 0.7) * rng.uniform(0.9, 1.08))
            y0 = int(min(top[c], tops_k[i]))
            if th >= 4.5 and y0 - 1 >= 0 and owner[y0 - 1, c] < 0:
                y0 -= 1                                                # a heavy load heaps over an exposed top
            yy = np.arange(y0, min(H, y0 + int(round(th))))
            yy = yy[(otier[yy, c] == t) | (yy < top[c])]
            if not len(yy):
                continue
            snow[yy, c] = True
            rowi[yy, c] = yy - yy.min()
            nrow[yy, c] = len(yy)
        used += 1
    # the loads shaded by the house snow recipe: a lit top (snow 5 west, 4), the body, the front face
    # turning from the light (snow_cool 3, then 2 at the foot of a deep load), cooler on the east
    X = np.mgrid[0:H, 0:W][1]
    tu = (X - xmid) / max(1.0, hw)
    c = np.where(tu < 0.3, C('snow', 4), C('snow_cool', 4))
    c = np.where((rowi == 0) & (tu < 0.25), C('snow', 5), c)
    c = np.where((rowi >= nrow - 2) & (nrow >= 3), C('snow_cool', 3), c)
    c = np.where((rowi == nrow - 1) & (nrow >= 4), C('snow_cool', 2), c)
    c = np.where((rowi == nrow - 1) & (nrow == 2), C('snow_cool', 3), c)
    code[snow] = c[snow]
    # the needles under each load in deep shade
    below = np.zeros_like(snow)
    below[1:] = snow[:-1]
    sh = below & ~snow & (code >= 0)
    code[sh] = _band(1, 0)
    return snow


def frost_crown(S, form, seed, load=1.0, foot_y=None, build=None):
    """A Frostline conifer's crown in the canvas of S (the woodland pine's master crown at this
    form's size): (codes, mask, extra) with extra the pine's limbs and open row or the krummholz's
    stem and stubs."""
    rng = np.random.default_rng(seed * 7 + 31)
    H, W = S.shape
    ys, xs = np.nonzero(S)
    yt, yb, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    cxm = (x0 + x1) / 2.0
    hw = (x1 - x0) / 2.0
    extra = {}
    if form == 'pine':
        if foot_y is not None:
            # the crown fills the upper 65 to 70 % of the tree; the bare bole is the lower third
            yb = int(round(yt + (foot_y - yt) * rng.uniform(0.8, 0.86)))
        pads, limbs, open_row, broken = _pads_pine(rng, H, W, yt, yb, x0, x1, cxm)
        extra.update(limbs=limbs, open_row=open_row, top_row=int(yt + (yb - yt) * 0.3), broken=broken)
        heavy, n_range = 1.0, (10, 15)
    elif form.startswith('krummholz'):
        if foot_y is not None:
            yb = int(round(foot_y)) - 1                              # the mat lies on the snow at the foot
        mat_h = (yb - yt) * rng.uniform(0.76, 0.84)                  # the mat is most of the shrub
        pads, stem, stubs, mat_top = _pads_krummholz(rng, H, W, yt, yb, x0, x1, cxm, mat_h)
        extra.update(stem=stem, stubs=stubs, mat_top=mat_top)
        heavy, n_range = 0.9 * load, (6, 10)
    else:
        kind = 'spruce' if form == 'spruce' else 'squat'
        pads, _tiers = _pads_cone(rng, H, W, yt, yb, x0, x1, cxm, kind, build)
        heavy, n_range = load, ((12, 19) if kind == 'spruce' else (10, 15))
    code, mask, owner = _paint_pads(pads, H, W, cxm, hw, yt, yb, rng, seed)
    # the leader: a spire on a spruce or a squat, a short leader on a pine
    if form in ('spruce', 'squat', 'pine'):
        top_ys = np.nonzero(mask.any(1))[0]
        if len(top_ys):
            ty = int(top_ys.min())
            cols = np.nonzero(mask[ty])[0]
            lx = int(round(cols.mean()))
            hgt = 6 if form == 'spruce' else 3
            for j in range(hgt):
                y = ty - 1 - j
                if y < 0:
                    break
                code[y, lx] = _band(3 if j < hgt - 2 else 4, 0)
                if j < hgt // 2:
                    code[y, lx + 1] = _band(2, 0)
            mask = code >= 0
            owner[mask & (owner < 0)] = -2
    snow = _loads(code, owner, pads, rng, cxm, hw, heavy, n_range)
    mask = mask | snow
    code[~mask] = -1
    V.tidy(code, passes=2)
    return code, mask, extra


def _limb(code, x0, y0, x1, y1, rng):
    """A pine's limb from the bole out to a clump: two texels thick, lit on its upper edge, warm bark."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n):
        t = i / max(1, n - 1)
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t - 2.5 * np.sin(np.pi * t)))
        for dy, c in ((0, C('timber_warm', 3)), (1, C('timber_cool', 1))):
            yy = y + dy
            if 0 <= yy < code.shape[0] and 0 <= x < code.shape[1] and code[yy, x] < 0:
                code[yy, x] = c


def conifer(form='pine', load=1.0, seed=None, build=None):
    """A conifer of the Frostline at the woodland pine's size for its form, built from bough masses
    (frost_crown): a spruce, a pine (its high open crown over a long warm bole), a squat wind-cropped
    pine, or a krummholz (a mat on the snow, flags to the lee, dead stubs to the wind). `build` sets a
    coned tree's own build: `wf` its width (a share of the master's), `top` a share of its height
    cropped off the top (a broken or wind-cropped top), `base` a share lifted off the crown's foot (a
    longer bare bole), `lean` its lean in texels at the top."""
    from scripts.art.native import compose as CO
    from scripts.art.native import screen as SCR
    from scripts.art.native import woodtrees as WT
    from scripts.art.native import ctx
    scale, s0 = CONIFERS[form]
    seed = s0 if seed is None else seed
    arr = np.asarray(CO.old_sprite(SCR._master('zones_props_pine.png'), raw=True)[0])
    tw = SCR.tree_dims('zones_props_pine.png')['tw']
    d = ctx.D
    rng = np.random.default_rng(seed * 11 + 3)
    S, foot, _ = WT.master_crown(arr, d, size=scale)
    code, mask, extra = frost_crown(S, form, seed, load, foot_y=foot[1], build=build)
    krum = form.startswith('krummholz')
    if krum:
        # the krummholz sits on the snow: its mat's foot on the foot row, no bole below it
        rows = np.nonzero(mask.any(1))[0]
        shift = int(round(foot[1])) - int(rows.max()) - 1
        code = np.roll(code, shift, 0)
        mask = np.roll(mask, shift, 0)
        if shift > 0:
            code[:shift] = -1
            mask[:shift] = False
        # the crooked stem rising from the mat's west to the flags (behind the pads), its dead windward
        # stubs bare and grey
        stem = [(x, y + shift) for x, y in extra['stem']]
        for (ax, ay), (bx, by) in zip(stem[:-1], stem[1:]):
            n = int(max(abs(bx - ax), abs(by - ay))) + 1
            for i in range(n):
                t = i / max(1, n - 1)
                x, y = int(round(ax + (bx - ax) * t)), int(round(ay + (by - ay) * t))
                for dx, c in ((-1, C('ash', 4)), (0, C('ash', 3)), (1, C('soot', 2))):
                    if 0 <= y < code.shape[0] and 0 <= x + dx < code.shape[1] and code[y, x + dx] < 0:
                        code[y, x + dx] = c
        for (sy, sx_, ln) in extra['stubs']:
            y0 = int(round(sy)) + shift
            for j in range(int(ln)):
                x = int(round(sx_)) - 2 - j
                yy = y0 - j // 2
                if 0 <= yy < code.shape[0] and 0 <= x < code.shape[1] and code[yy, x] < 0:
                    code[yy, x] = C('ash', 4) if j < ln - 1 else C('stone_warm', 4)    # a pale broken end
        mask = code >= 0
    # a gap closed in by pads (or a pocket a texel wide) is the deep shade between them, never sky
    if form == 'pine':
        # the pine's crown keeps one or two small windows where a limb shows (30 to 150 texels); a
        # smaller hole or a larger one closed in by its clumps is filled with the deep shade inside
        holes = ndi.binary_fill_holes(mask) & ~mask
        hl, hn = ndi.label(holes)
        if hn:
            hs = ndi.sum(holes, hl, range(1, hn + 1))
            keep_win = sorted([i for i in range(hn) if 30 < hs[i] <= 150], key=lambda i: -hs[i])[:2]
            holes = np.isin(hl, [1 + i for i in range(hn) if i not in keep_win])
    else:
        pm = np.pad(mask, 3)
        holes = (ndi.binary_fill_holes(ndi.binary_closing(pm, structure=np.ones((3, 3), bool), iterations=1))[3:-3, 3:-3]
                 & ~mask)
    code[holes] = _band(0, 0)
    mask = mask | holes
    lab, nl = ndi.label(mask)
    if nl > 1:
        sizes = ndi.sum(mask, lab, range(1, nl + 1))
        keep = 1 + np.nonzero(sizes >= 0.02 * sizes.max())[0]
        if form != 'pine':
            keep = 1 + np.nonzero(sizes >= 0.15 * sizes.max())[0]
        mask = np.isin(lab, keep)
        code[~mask] = -1
    # the outline in each material's own edge tone (tone 1 on the lit top and west)
    pad = 2
    big = np.full((code.shape[0] + 2 * pad, code.shape[1] + 2 * pad), -1, np.int32)
    big[pad:-pad, pad:-pad] = np.where(mask, code, -1)
    V.outline(big)
    code = big.astype(np.int64)
    mask = big >= 0
    foot = (foot[0] + pad, foot[1] + pad)
    if krum:
        out, ft = WT._crop(code, foot)
    else:
        T = tw * d
        cols = int(round(foot[0]))
        half_t = max(2, int(T / 2))
        band = mask[:, max(0, cols - half_t):cols + half_t + 1]
        bots = [np.nonzero(band[:, j])[0].max() for j in range(band.shape[1]) if band[:, j].any()]
        cb = min(bots) if bots else foot[1] - 10 * d
        if form == 'pine':
            cb = min(cb, extra['top_row'] + pad)                        # the bole runs up into the crown's top
        length = int(foot[1] - cb + 10)
        tc, tm, (tfx, tfy), _ty = WT.trunk2('oak', length, T * 0.6, T * 1.05, rng, lean=2, twist=1.0, roots=3, limbs=0,
                                            limb_rise=12.0, limb_spread=0.0,
                                            bark='oak', front_root=False,
                                            root_rows=(5, 12), root_reach=(1, 8), root_w=(0.45, 3.4))
        if form == 'pine':
            # the bole behind the crown: drawn first, the clumps over it, the limbs out to them
            ox, oy = int(round(foot[0] - tfx)), int(round(foot[1] - tfy))
            Hh = max(code.shape[0], oy + tc.shape[0]) - min(0, oy)
            Ww = max(code.shape[1], ox + tc.shape[1]) - min(0, ox)
            x0_, y0_ = min(0, ox), min(0, oy)
            out = np.full((Hh, Ww), -1, np.int64)
            sub = out[oy - y0_:oy - y0_ + tc.shape[0], ox - x0_:ox - x0_ + tc.shape[1]]
            sub[tm] = tc[tm]
            lim = np.full_like(out, -1)
            for (lx0, ly0, lx1, ly1) in extra['limbs']:
                _limb(lim, lx0 + pad - x0_, ly0 + pad - y0_, lx1 + pad - x0_, ly1 + pad - y0_, rng)
            bx0, by0, bx1, by1 = extra['broken']
            _limb(lim, bx0 + pad - x0_, by0 + pad - y0_, bx1 + pad - x0_, by1 + pad - y0_, rng)
            ex_, ey_ = int(round(bx1 + pad - x0_)), int(round(by1 + pad - y0_))
            if 0 <= ey_ < lim.shape[0] and 0 <= ex_ < lim.shape[1]:
                lim[ey_, ex_] = C('stone_warm', 4)                    # the snapped end, pale wood
            out[(lim >= 0)] = lim[lim >= 0]
            # the upper bole warms to a pine's orange-brown above the lowest storey, through a few rows
            warm = {FI['timber_cool']: FI['timber_warm'], FI['earth_cool']: FI['timber_warm'], FI['earth']: FI['timber']}
            yw = extra['open_row'] + pad - y0_ + 18
            for y in range(0, min(out.shape[0], yw)):
                row = out[y]
                for f_, g_ in warm.items():
                    sel = (row >= 0) & (row // 8 == f_) & (row % 8 > 0)
                    if y > yw - 8:
                        sel &= K.vhash(np.arange(len(row)) // 3, np.full(len(row), y // 3), 41) < (yw - y) / 8.0
                    row[sel] = g_ * 8 + row[sel] % 8
            csub = out[-y0_:-y0_ + code.shape[0], -x0_:-x0_ + code.shape[1]]
            csub[mask] = code[mask]
            ft = (ox - x0_ + tfx, oy - y0_ + tfy)
        else:
            out, ft = WT._compose((tc, tm, (tfx, tfy)), code, mask, foot)
        WT._close_pinholes(out, most=60)
        out, ft = WT._crop(out, ft)
        # the snow's bounce on the bark's shaded east side, below the crown's shade
        bark = np.isin(out // 8, [FI[f] for f in WT.BARKS['oak'][0]]) & (out >= 0)
        greens = [FI[f] for f in ('leaf', 'leaf_cool', 'leaf_warm', 'grass', 'grass_cool')]
        crown_rows = np.nonzero(np.isin(out // 8, greens).any(1))[0]
        yc = int(crown_rows.max()) + 6 if len(crown_rows) else 0
        for y in range(yc, out.shape[0] - 2):
            cols_ = np.nonzero(bark[y])[0]
            if len(cols_) < 6:
                continue
            xe = int(cols_.max())
            for x in (xe - 1, xe - 2):
                c = int(out[y, x])
                if bark[y, x] and c % 8 <= 2 and c != C('timber_cool', 0):
                    out[y, x] = c + 1
    # the drift banked at the foot's west: lobed, a lit west crest, its body, a cool east fall, a shade
    # row at its foot and against the stem
    fx, fy = int(round(ft[0])), int(round(ft[1]))
    padx = 10
    big = np.full((out.shape[0] + 2, out.shape[1] + 2 * padx), -1, np.int64)
    big[:out.shape[0], padx:padx + out.shape[1]] = out
    fx += padx
    span = (22, 3) if krum else (15, 0)
    xc = fx - span[0] // 2 - 2 + int(rng.integers(-1, 2))
    lobes = [(xc + rng.uniform(-3, 3), rng.uniform(2.6, 4.2) + (1.5 if krum else 0)) for _ in range(2)]
    for x in range(fx - span[0] - 2, fx + span[1]):
        h = max(max(0.0, hh_ - abs(x - lx) * 0.38) for lx, hh_ in lobes)
        h = int(round(h))
        for k_ in range(h):
            y = fy - k_
            if not (0 <= y < big.shape[0]):
                continue
            if big[y, x] >= 0 and not krum and x > fx - 4:
                continue
            top_ = k_ == h - 1
            west = x <= xc
            c = C('snow', 5) if (top_ and west) else (C('snow', 4) if (top_ or west) else C('snow_cool', 4))
            if k_ == 0:
                c = C('snow_cool', 3) if west else C('snow_cool', 2)
            big[y, x] = c
    out = big
    # no root gap left open over the snow: a transparent pocket closed in under the roots takes the
    # contact shade
    al = out >= 0
    low = np.zeros_like(al)
    low[max(0, fy - 14):fy + 1] = True
    gap = ndi.binary_fill_holes(ndi.binary_closing(al, structure=np.ones((3, 3), bool), iterations=2)) & ~al & low
    out[gap] = C('timber_cool', 0)
    # no pinhole of a few texels left anywhere in the picture: it takes its darkest neighbour
    al = out >= 0
    pin = ndi.binary_fill_holes(al) & ~al
    pl, pn = ndi.label(pin)
    for i in range(1, pn + 1):
        hm = pl == i
        if form == 'pine' and hm.sum() > 150:
            # a pine's window larger than a limb's gap, closed in by clumps and the bole: the crown's
            # deep interior (the pocket band), a band lighter in its top two rows where light gets in
            Yh, Xh = np.nonzero(hm)
            top_r = np.full(out.shape[1], 10 ** 6)
            np.minimum.at(top_r, Xh, Yh)
            out[Yh, Xh] = np.where(Yh - top_r[Xh] < 2, _band(2, 0), _band(1, 0))
            continue
        if hm.sum() > 6:
            continue
        ring = ndi.binary_dilation(hm) & al
        vals = out[ring]
        out[hm] = int(vals[np.argmin(vals % 8)])
    pic = K.crop(out.astype(np.int32), fx, fy)
    return pic


def _snag_dress(seed, stubs, top_xy):
    """The dead pine's surface, laid on the finished picture (so the tidy keeps its clusters): silvered
    wood in spiral grain (streaks a tone down along the twist), bark plates (a dark crack with a lit
    lip above it), drying checks (a long dark split with a lit west lip), a dark heart crack and a lit
    splinter at the broken top, a knot ring where each stub leaves the bole, the last plate of bark
    low on the sheltered east, wolf lichen in clusters on the lit west, the snow shaded by its planes,
    and the bole's contact shade over the drift."""
    def dress(sc, a):
        rng = np.random.default_rng(seed + 3)
        H, W = a.shape
        Y, X = np.mgrid[0:H, 0:W]
        wood = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag == 'wood']) & (a >= 0)
        if not wood.any():
            return
        L = sc.light()
        inner = ndi.binary_erosion(wood, iterations=1) & (a % 8 >= 1)
        ys, xs = np.nonzero(inner)
        y1 = int(np.nonzero(wood)[0].max())
        # spiral grain: streaks one texel wide, 4 to 9 long, leaning a texel every 6 rows
        sid = X + (Y // 6)
        run = (Y + (K.vhash(sid, 0, seed) * 8).astype(int)) // int(rng.integers(5, 8))
        streak = inner & (K.vhash(sid, run, seed + 1) < 0.3)
        a[streak] = (a[streak] // 8) * 8 + np.clip(a[streak] % 8 - 1, 1, 5)
        # bark plates: short cracks across the grain, a lit lip over each
        for _ in range(int(rng.integers(7, 11))):
            k = int(rng.integers(0, len(ys)))
            y, x = int(ys[k]), int(xs[k])
            ln = int(rng.integers(3, 6))
            for j in range(ln):
                xx = x + j
                if 0 < y < H and xx < W and inner[y, xx]:
                    a[y, xx] = C('soot', 1)
                    if inner[y - 1, xx]:
                        a[y - 1, xx] = C('ash', 5) if L[y - 1, xx] > 0.35 else C('ash', 4)
        # drying checks: long splits following the twist
        for _ in range(int(rng.integers(2, 4))):
            k = int(rng.integers(0, len(ys)))
            y, x = int(ys[k]), int(xs[k])
            for j in range(int(rng.integers(9, 20))):
                yy, xx = y + j, x + (j + (y % 6)) // 6
                if not (0 <= yy < H and 0 <= xx < W) or not inner[yy, xx]:
                    break
                a[yy, xx] = C('soot', 1)
                if inner[yy, xx - 1]:
                    a[yy, xx - 1] = C('ash', 5) if L[yy, xx - 1] > 0.4 else C('ash', 3)
        # the broken top: a dark heart crack down from the break, a lit splinter beside it
        tx, ty = top_xy
        for j in range(int(rng.integers(7, 11))):
            yy, xx = ty + 2 + j, tx + (1 if j > 4 else 0)
            if 0 <= yy < H and 0 <= xx < W and wood[yy, xx]:
                a[yy, xx] = C('soot', 0)
                if wood[yy, xx - 1]:
                    a[yy, xx - 1] = C('stone_warm', 4)
        # knots where the stubs leave the bole
        for (ky, kx) in stubs:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = ky + dy, kx + dx
                    if 0 <= yy < H and 0 <= xx < W and wood[yy, xx]:
                        a[yy, xx] = C('ash', 3) if (dy, dx) == (0, 0) else C('soot', 2)
        # the last bark, low on the sheltered east
        bys = np.nonzero(inner & (Y > y1 - 34) & (Y < y1 - 6))[0]
        if len(bys):
            k = int(rng.integers(0, len(bys)))
            cy = int(bys[k])
            row = np.nonzero(wood[cy])[0]
            cx = int(row.max()) - 2
            rx_, ry_ = rng.uniform(1.8, 2.6), rng.uniform(3.0, 4.5)
            rag = K.vhash(X, Y // 2, seed + 13) * 0.5
            pm = inner & (((X - cx) / rx_) ** 2 + ((Y - cy) / ry_) ** 2 <= 1.0 + rag)
            a[pm] = np.where(L[pm] > 0.45, C('timber_cool', 3), C('timber_cool', 2))
            ed = pm & ~ndi.binary_erosion(pm)
            a[ed & (X >= cx)] = C('timber_cool', 1)
        # wolf lichen: two or three clusters of 3 to 4 texels on the lit west face
        cand = np.nonzero(inner & (L > 0.3) & (Y < y1 - 18) & (X <= np.median(xs)))
        for _ in range(int(rng.integers(2, 4))):
            if not len(cand[0]):
                break
            k = int(rng.integers(0, len(cand[0])))
            cy, cx = int(cand[0][k]), int(cand[1][k])
            for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1), (0, 2), (1, -1))[:int(rng.integers(4, 7))]:
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < H and 0 <= xx < W and wood[yy, xx]:
                    a[yy, xx] = C('grass_warm', 4) if dy == 0 else C('grass_warm', 3)
        # the snow: ridges lit on top and west, cool on their front and east ends; the drift shaded
        # by its own planes
        sn = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag in ('snow', 'drift')]) & (a >= 0)
        sn &= a % 8 >= 1
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
        # the bole's contact shade where it stands in the drift
        dr = np.isin(sc.label, [i for i, s_ in enumerate(sc.solids) if s_.tag == 'drift'])
        over = np.zeros_like(dr)
        over[:-1] = dr[1:]
        cs = over & wood & ~dr & (a % 8 >= 2)
        a[cs] = (a[cs] // 8) * 8 + a[cs] % 8 - 1
    return dress


def snag(seed=541):
    """A dead pine at the tree line: a silvered bole leaning a little east and tapering, its top
    snapped into jagged points, stubs of different lengths angled down and tapering to broken pale
    ends (one a longer broken limb), snow lying unevenly on them, a lobed drift at its west foot, a
    root flare; its surface dressed by _snag_dress."""
    sc = K.Scene(-40, 40, -16, 14, 200)
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
    # the break: three jagged points of different heights
    sc.cylinder(x - 1.3, 0, 1.6, h, h + 15, WEATHERED, base=2.9, k=1.7, tag='wood')
    sc.cylinder(x + 1.4, 0, 1.3, h, h + 8, WEATHERED, base=2.6, k=1.7, tag='wood')
    sc.cylinder(x + 0.2, 0, 1.0, h, h + 11, WEATHERED, base=2.8, k=1.7, tag='wood')
    stubs_w = []
    specs = [(52, 11, -1, 16), (70, 15, 1, 24), (93, 7, -1, 12), (108, 9, 1, 28), (124, 10, -1, 20)]
    for (z, ln, side, ang) in specs:
        xx = x * z / max(1.0, h)
        rr = max(2.6, 8.6 - 0.75 * z / 17.0)
        # the stub: a chain of short segments stepping down and thinning outward
        nseg = max(2, int(ln / 2))
        zz = float(z)
        th = 2.8
        px = xx + side * rr * 0.85
        for j in range(nseg):
            x0_, x1_ = (px - 2.2, px) if side < 0 else (px, px + 2.2)
            sc.box(x0_, -1.2, zz, x1_, 1.2, zz + th, WEATHERED, base=2.8, k=1.6, tag='wood', round_=0.5)
            if j < nseg - 1 and rng.random() < (0.75 if side < 0 else 0.45):
                sc.box(x0_ + 0.3, -0.6, zz + th - 0.2, x1_ - 0.3, 0.3, zz + th + 1.0, SNOW, base=3.9, k=1.0, tag='snow',
                       round_=0.4)
            px += side * 2.0
            zz -= 2.0 * np.tan(np.radians(ang))
            th = max(1.4, th - 0.35)
        stubs_w.append((xx + side * rr * 0.75, z + 1.4, px, zz + th / 2))
    _snowcap(sc, x - 1.3, 0.0, h + 15.5, 1.8, 1.6, th=1.3, seed=seed)
    _drift_west(sc, -10, 2, 9.5, seed)
    sc.ellipsoid(-15.5, 4.0, 0.4, 6.0, 3.8, 3.0, SNOW, base=3.8, k=1.0, tag='drift', flat=1.1)       # a second lobe
    sc.render()
    stubs, ends = [], []
    for (wx, wz, ex, ez) in stubs_w:
        stubs.append((int(round(sc.oy - wz)), int(round(sc.ox + wx))))
        ends.append((int(round(sc.oy - ez)), int(round(sc.ox + ex))))
    top_xy = (int(round(sc.ox + x - 0.3)), int(round(sc.oy - h - 15)))
    a = _solo(sc)
    _snag_dress(seed, stubs, top_xy)(sc, a)
    # each stub's broken end: pale inner wood with a dark edge
    for (ey, ex) in ends:
        for dy in (-1, 0):
            if 0 <= ey + dy < a.shape[0] and 0 <= ex < a.shape[1] and a[ey + dy, ex] >= 0:
                a[ey + dy, ex] = C('stone_warm', 4) if dy == -1 else C('stone_warm', 3)
    return K.crop(a, sc.ox, sc.oy)
