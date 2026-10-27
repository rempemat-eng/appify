"""The Crossroads market at density 3 (Matt, 27 Oct: "this square could be a larger and a proper
market", "why only one market stall"): market stalls with their trade's goods, baskets, and the
hay field on the slope above the square ("if those are hay bales where is the hay field?").

    stall(w, h, seed, goods)   produce, bread, fish, cloth, tools, or closed (covered, awning furled)
    basket(w, h, seed)         a wicker basket of apples
    hayfield(w, h, seed)       a cut hay field: stubble in drilled rows, raked windrows, bales on it

Every stall is the same build as Moss's (village.p_stall): a counter of sawn boards on trestles,
two poles, a striped awning with a scalloped hem and its shade on the counter; only the goods,
the awning's colour and what hangs from it change with the trade. Light from the upper left,
house ramps only, clusters of two texels or more.
"""
from __future__ import annotations

import math

import numpy as np

from . import village as V
from .palette import FI

q, code, fill = V.q, V.code, V.fill
AWNING = {'produce': 'berry', 'bread': 'brass', 'fish': 'slate', 'cloth': 'dusk', 'tools': 'leaf', 'closed': 'berry'}


def grid(a):
    H, W = a.shape
    return np.mgrid[0:H, 0:W] + 0.5


def _dome(a, cx, cy, rx, ry, fam, t=3, where=None):
    """A small round thing (a fruit, a cob, a pot) lit on its upper left."""
    Y, X = grid(a)
    dx, dy = (X - cx) / rx, (Y - cy) / ry
    m = dx * dx + dy * dy <= 1
    if where is not None:
        m &= where
    v = -0.6 * dx - 0.8 * dy
    tt = np.where(v > 0.55, t + 2, np.where(v > -0.1, t + 1, np.where(v > -0.6, t, t - 1)))
    a[m] = (FI[fam] * 8 + np.clip(tt, 0, 5))[m]
    return m


def _goods(a, goods, x0, x1, yb, rng):
    """The trade's goods on the counter top (its surface at yb - 16.5 world px), in front of the
    awning's shade, each piece a small volume."""
    top = yb - q(16.5)
    Y, X = grid(a)
    if goods == 'produce':
        xx = x0 + q(2)
        for fam, t in (('fox', 2), ('leaf', 2), ('berry', 2), ('brass', 3)):
            cw = q((x1 - x0) / 3.0 / 4.6)
            for row in range(3):
                for j in range(4):
                    fx = xx + q(1.3) + j * (cw - q(2.4)) // 3 + (q(0.7) if row % 2 else 0)
                    fy = top - q(4.6) + row * q(1.2)
                    _dome(a, fx, fy, q(1.3), q(1.1), fam, t)
            V.board(a, xx, top - q(3.0), cw, q(1.8), 0, 'timber', 3, rng, split=False, grain=False)
            V.board(a, xx, top - q(1.2), cw, q(1.4), 0, 'timber_warm', 2, rng, split=False, grain=False)
            xx += cw + q(1.5)
    elif goods == 'bread':
        # loaves on a cloth: long bloomers scored across, round cobs, a basket of rolls at the end
        cl = (X >= x0 + q(1.5)) & (X < x1 - q(1.5)) & (Y >= top - q(1.6)) & (Y < top + q(0.4))
        a[cl] = code('plaster', 4)
        a[cl & (Y >= top)] = code('plaster', 3)
        a[cl & ((X.astype(int) // q(3)) % 2 == 0) & (Y >= top - q(1.6)) & (Y < top - q(1.0))] = code('berry', 3)
        x = x0 + q(2.5)
        k = 0
        while x < x1 - q(9):
            if k % 3 == 2:
                m = _dome(a, x + q(2.2), top - q(2.4), q(2.2), q(1.9), 'clay', 3)
                a[m & (np.abs(Y - (top - q(2.6))) < 1) & (np.abs(X - x - q(2.2)) < q(1.2))] = code('clay', 1)
                x += q(5.2)
            else:
                m = _dome(a, x + q(3.0), top - q(1.9), q(3.0), q(1.5), 'clay', 3)
                for s in (-1, 0, 1):
                    sx = x + q(3.0) + s * q(1.4)
                    a[m & (np.abs(X - sx - (Y - top) * 0.5) < 0.9) & (Y < top - q(1.9))] = code('clay', 1)
                x += q(6.6)
            k += 1
        bx = x1 - q(8)
        bm = (X >= bx) & (X < bx + q(6)) & (Y >= top - q(3)) & (Y < top)
        a[bm] = code('timber_warm', 3)
        a[bm & (((X.astype(int) + Y.astype(int)) // 2) % 2 == 0)] = code('timber_warm', 2)
        a[bm & (Y < top - q(2.4))] = code('timber_warm', 4)
        for j in range(3):
            _dome(a, bx + q(1.2) + j * q(1.8), top - q(3.4), q(1.0), q(0.8), 'brass_warm', 3)
    elif goods == 'fish':
        # a crate of crushed ice with fish laid across it, silver backs lit, a pail of shellfish
        ice = (X >= x0 + q(1.5)) & (X < x1 - q(7)) & (Y >= top - q(2.4)) & (Y < top + q(0.2))
        a[ice] = code('sky_cool', 4)
        a[ice & (((X.astype(int) * 3 + Y.astype(int) * 5) % 7) < 2)] = code('snow', 4)
        V.board(a, x0 + q(1.5), top, x1 - x0 - q(8.5), q(1.6), 0, 'timber', 2, rng, split=False, grain=False)
        x = x0 + q(2.5)
        k = 0
        while x < x1 - q(12):
            cy = top - q(1.2) - (k % 2) * q(0.8)
            L = q(rng.uniform(4.2, 5.2))
            body = ((X - x - L / 2) / (L / 2)) ** 2 + ((Y - cy) / q(1.0)) ** 2 <= 1
            a[body] = code('slate_cool', 3)
            a[body & (Y < cy - 1)] = code('slate_cool', 4)
            a[body & (Y < cy - q(0.6))] = code('sky', 4)
            a[body & (Y > cy + 1)] = code('plaster', 4)
            tail = (X >= x + L - 1) & (X < x + L + q(1.4)) & (np.abs(Y - cy) <= (X - x - L + 2) * 0.7) & ~body
            a[tail] = code('slate_cool', 2)
            fill(a, int(x + q(1.0)), int(cy - 1), int(x + q(1.0)) + 2, int(cy + 1), code('void', 1))     # the eye
            x += L + q(1.6)
            k += 1
        px = x1 - q(6)
        pm = (X >= px) & (X < px + q(4.4)) & (Y >= top - q(3.6)) & (Y < top + q(0.4))
        u = (X - px) / q(4.4)
        a[pm] = (FI['iron'] * 8 + np.select([u < 0.25, u < 0.7], [4, 3], 2))[pm]
        for j in range(3):
            _dome(a, px + q(1.0) + j * q(1.2), top - q(3.6), q(0.8), q(0.6), 'dusk', 2)
    elif goods == 'cloth':
        # bolts of cloth stacked on the counter, folded edges lit, a length draped over the front
        x = x0 + q(2)
        for k, fam in enumerate(('berry', 'sky', 'brass', 'dusk', 'leaf', 'plaster')):
            bw = q(4.2)
            if x + bw > x1 - q(2):
                break
            for j in range(2 if k % 2 == 0 else 1):
                y1_ = top - j * q(2.2)
                m = (X >= x) & (X < x + bw) & (Y >= y1_ - q(2.2)) & (Y < y1_)
                a[m] = code(fam, 3)
                a[m & (Y < y1_ - q(1.6))] = code(fam, 4)
                a[m & (Y >= y1_ - 2)] = code(fam, 2)
                a[m & (X >= x + bw - 2)] = code(fam, 2)
                a[m & (X < x + 2) & (Y < y1_ - 2)] = code(fam, 4)
            x += bw + q(0.6)
        dr = (X >= x0 + q(3)) & (X < x0 + q(14)) & (Y >= top) & (Y < top + q(6))
        dr &= Y < top + q(4) + q(2) * np.sin((X - x0) / q(2.4)) ** 2
        u = ((X - x0) / q(2.4)) % 2
        a[dr] = (FI['dusk'] * 8 + np.where(u < 0.6, 4, np.where(u < 1.4, 3, 2)))[dr]
        a[dr & (Y >= top + q(3.2))] = code('dusk', 2)
    elif goods == 'tools':
        # a rack of hand tools: billhooks, a hammer, trowels laid out; two pots and a coil of rope
        x = x0 + q(2.5)
        for k in range(3):
            hx = x + k * q(4.0)
            V.bar(a, hx, top - q(0.4), hx + q(2.4), top - q(0.4), 1.0, 'timber_warm', 3)
            hook = ((X - hx - q(3.4)) ** 2 + (Y - top + q(0.8)) ** 2 <= q(1.4) ** 2) & ~((X - hx - q(3.0)) ** 2 + (Y - top + q(1.1)) ** 2 <= q(0.8) ** 2)
            hook &= Y < top + q(0.2)
            a[hook] = code('iron', 3)
            a[hook & (Y < top - q(1.2))] = code('iron', 5)
        x += q(12.5)
        for k in range(2):
            m = _dome(a, x + q(1.8) + k * q(4.2), top - q(1.6), q(1.8), q(1.6), 'iron', 2)
            a[m & (Y < top - q(2.6))] = code('void', 1)
        rx = x + q(9.0)
        if rx < x1 - q(3):
            ring = ((X - rx) ** 2 / q(1.8) ** 2 + (Y - top + q(1.2)) ** 2 / q(1.2) ** 2 <= 1) & \
                ~((X - rx) ** 2 / q(0.8) ** 2 + (Y - top + q(1.2)) ** 2 / q(0.5) ** 2 <= 1)
            a[ring] = code('sand', 3)
            a[ring & (((X.astype(int) + Y.astype(int)) % 3) == 0)] = code('sand', 2)
            a[ring & (Y < top - q(1.8))] = code('sand', 4)
    elif goods == 'closed':
        # the goods under a sacking cover, roped down, the cover lit across its top
        cm = (X >= x0 + q(1.5)) & (X < x1 - q(1.5)) & (Y >= top - q(3.6)) & (Y < top + q(1.0))
        cm &= Y >= top - q(3.6) + q(0.8) * np.sin((X - x0) / q(3.0)) ** 2
        u = ((X - x0) / q(3.0)) % 2
        a[cm] = (FI['sand_cool'] * 8 + np.where(u < 0.5, 4, np.where(u < 1.5, 3, 2)))[cm]
        a[cm & (Y >= top + q(0.2))] = code('sand_cool', 2)
        for rx in (x0 + q(6), x1 - q(6)):
            V.bar(a, rx, top - q(3.6), rx + q(0.6), top + q(1.0), 0.9, 'timber_warm', 2)


def stall(w, h, seed, goods='produce'):
    """A market stall: Moss's build with this trade's goods and awning (`goods` closed: the
    goods covered and the awning furled round its rail)."""
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=36, side=4)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    for xx, t in ((x0, 3), (x1 - q(2.2), 2)):
        V.beam(a, xx, yb - q(38), xx + q(2.2), yb, rng, 'timber', t, hd=True)
    # the counter's front: boards with gaps and nails, a sack or a crate at the foot
    xx = x0 + q(2.2)
    while xx < x1 - q(2.2):
        bw = q(rng.uniform(3, 4.2))
        V.board(a, xx, yb - q(1), q(12), bw - 1, -90, ('timber', 'timber_warm', 'timber_cool')[int(rng.integers(0, 3))],
                int(rng.choice([2, 3, 3])), rng)
        V.nail(a, xx + bw // 2 - 1, yb - q(11), rng=rng)
        xx += bw
    V.prism(a, x0, yb - q(16.5), x1, yb - q(13), q(1.8), 'timber_warm', 3, side=q(1))
    _goods(a, goods, x0, x1, yb, rng)
    Y, X = grid(a)
    fam = AWNING.get(goods, 'berry')
    if goods == 'closed':
        # the awning furled round its rail: a roll of canvas, lit along its top, ties round it
        ry0, ry1 = int(yb - q(42)), int(yb - q(38.5))
        rm = (X >= x0 - q(2)) & (X < x1 + q(2)) & (Y >= ry0) & (Y < ry1)
        rel = (Y - ry0) / max(1, ry1 - ry0)
        a[rm] = (FI[fam] * 8 + np.select([rel < 0.25, rel < 0.6, rel < 0.85], [4, 3, 2], 1))[rm]
        for tx in np.linspace(x0 + q(3), x1 - q(3), 4):
            fill(a, int(tx), ry0, int(tx) + 2, ry1, code('sand', 3))
    else:
        ay0, ay1 = yb - q(42), yb - q(33)
        am = (X >= x0 - q(2)) & (X < x1 + q(2)) & (Y >= ay0) & (Y < ay1)
        hem = (Y >= ay1) & (Y < ay1 + q(2.4)) & (X >= x0 - q(2)) & (X < x1 + q(2)) & \
            ((((X - x0) % q(4)) - q(2)) ** 2 / q(2) ** 2 + ((Y - ay1) / q(2.4)) ** 2 <= 1)
        m = am | hem
        stripe = ((X - x0 + q(2)) // q(4)).astype(int) % 2
        tt = np.where(stripe == 0, 4, 3)
        tt = np.where(Y < ay0 + q(1.5), tt + 1, tt)
        tt = np.where((Y >= ay1 - q(1.5)) & (Y < ay1), tt - 1, tt)
        us = ((X - x0 + q(2)) % q(4)) / q(4)
        tt = tt + np.where((us > 0.15) & (us < 0.45), 1, 0) - np.where(us > 0.8, 1, 0)
        tt = tt - np.where((Y > ay0 + (ay1 - ay0) * 0.55) & (np.abs(X - (x0 + x1) / 2) < (x1 - x0) * 0.3), 1, 0)
        tt = np.clip(tt, 0, 5)
        a[m & (stripe == 0)] = FI['plaster'] * 8 + tt[m & (stripe == 0)]
        a[m & (stripe == 1)] = FI[fam] * 8 + tt[m & (stripe == 1)]
        under = V._rect(a.shape, x0, ay1 + q(2.4), x1, ay1 + q(4)) & (a >= 0)
        a[under] = np.maximum((a[under] // 8) * 8, a[under] - 1)
        # what hangs from the awning's rail: strings of onions, a fish on a hook, a length of cloth,
        # a bill hook (never in front of the stallholder's face: at the poles' ends)
        hx = x1 - q(4.5)
        if goods == 'produce':
            for j in range(3):
                _dome(a, hx - j * q(1.0), ay1 + q(3.4) + j * q(1.7), q(1.0), q(0.9), 'brass_warm', 3)
            fill(a, hx, ay1 + q(2.4), hx + 1, ay1 + q(3.0), code('sand', 2))
        elif goods == 'fish':
            fill(a, hx, ay1 + q(2.4), hx + 1, ay1 + q(3.4), code('iron', 3))
            body = ((X - hx) / q(0.9)) ** 2 + ((Y - ay1 - q(5.6)) / q(2.4)) ** 2 <= 1
            a[body] = code('slate_cool', 2)
            a[body & (X < hx)] = code('slate_cool', 4)
        elif goods == 'cloth':
            dm = (X >= x1 - q(7)) & (X < x1 - q(2.5)) & (Y >= ay1 + q(2.4)) & (Y < ay1 + q(9))
            u = ((X - x1) / q(1.5)) % 2
            a[dm] = (FI['berry'] * 8 + np.where(u < 0.7, 4, np.where(u < 1.4, 3, 2)))[dm]
        elif goods == 'bread':
            for j in range(2):
                m = ((X - hx + j * q(2.4)) ** 2 + (Y - ay1 - q(4.6)) ** 2 <= q(1.4) ** 2) & \
                    ~((X - hx + j * q(2.4)) ** 2 + (Y - ay1 - q(4.6)) ** 2 <= q(0.6) ** 2)
                a[m] = code('clay', 3)
                a[m & (Y < ay1 + q(4.2))] = code('clay', 4)
        elif goods == 'tools':
            V.bar(a, hx, ay1 + q(2.4), hx, ay1 + q(7.5), 0.9, 'timber_warm', 3)
            fill(a, hx - q(1.6), ay1 + q(2.6), hx + q(1.6), ay1 + q(3.6), code('iron', 3))
    # the price board at the foot
    V.prism(a, x1 - q(8), yb - q(10), x1 - q(1), yb, q(1), 'slate', 1, side=q(1))
    for ly in (yb - q(8), yb - q(5.5), yb - q(3)):
        fill(a, x1 - q(6.5), ly, x1 - q(3) - int(rng.integers(0, q(1.5))), ly + 2, code('plaster', 5))
    if goods == 'closed':
        V.prism(a, x0 + q(1), yb - q(6), x0 + q(8), yb, q(1.2), 'timber_warm', 3, side=q(1))       # a crate, shut
    else:
        V.sack(a, x0 + q(3), yb - q(3.6), q(3.4), q(3.4))
    return V.finish(p)


def basket(w, h, seed):
    """A wicker basket of apples on the flags: the weave in staggered rows (over and under, a tone
    apart), its rim a lit rolled edge, the apples domes lit on the upper left, a cloth tucked in."""
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=7, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    rx = q(w / 2)
    top = yb - q(6)
    body = (np.abs(X - cx) <= rx - (yb - Y) * 0.12) & (Y >= top) & (Y < yb)
    u = (X - cx) / rx
    row = ((Y - top) // q(1.2)).astype(int)
    weave = ((X.astype(int) // q(1.2) + row) % 2 == 0)
    tt = np.where(u < -0.4, 4, np.where(u < 0.3, 3, 2)) - np.where(weave, 1, 0)
    a[body] = (FI['timber_warm'] * 8 + np.clip(tt, 0, 5))[body]
    a[body & (Y >= yb - 2)] = code('timber_warm', 1)
    rim = (np.abs(X - cx) <= rx + 1) & (Y >= top - 2) & (Y < top + 1)
    a[rim] = code('sand', 3)
    a[rim & (Y < top - 1)] = code('sand', 4)
    for j in range(int(w / 2.6)):
        fx = cx - rx + q(1.6) + j * q(2.4) + int(rng.integers(-1, 2))
        _dome(a, fx, top - q(0.9), q(1.2), q(1.0), ('fox', 'berry', 'leaf')[j % 3], 2)
    fill(a, cx + rx - q(3), top - q(1.2), cx + rx - q(0.6), top + q(0.6), code('plaster', 4))
    return V.finish(p)


def hayfield(w, h, seed):
    """A hay field, cut: the stubble in drilled rows across the slope (short pale stalks lit on
    their tips, the soil between them darker), two raked windrows of drying hay curving along the
    rows, the field's edge a soft rounded outline on whole cells, and the bales standing on it
    (village.p_hay_hd), each with its contact shade."""
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=12, side=1)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = grid(a)
    x0, x1, y0 = cx - q(w / 2), cx + q(w / 2), yb - q(h)
    # the field: whole cells, corners rounded (soft grid), the edge lumped a texel or two
    r = q(10)
    ccx = np.clip(X, x0 + r, x1 - r)
    ccy = np.clip(Y, y0 + r, yb - r)
    wob = 1.2 * np.sin(X / q(3.1)) + 1.0 * np.sin(Y / q(2.7) + 1.3)
    f = ((X - ccx) ** 2 + (Y - ccy) ** 2 <= (r + wob) ** 2) & (X >= x0) & (X < x1) & (Y >= y0) & (Y < yb)
    # the cut ground: pale stubble, a tone lighter or darker in soft drifts where it dried
    rowp = q(3.0)
    drift = np.sin(X / q(5) + 0.7) + np.sin(Y / q(4) - X / q(7))
    a[f] = code('sand_warm', 3)
    a[f & (drift > 1.1)] = code('sand_warm', 2)
    a[f & (drift < -1.1)] = code('sand_warm', 4)
    # stubble: short clusters of cut stalks standing in drilled rows, lit at their tips, a dark
    # foot where each tuft meets the ground; gaps between them
    for yy in np.arange(y0 + q(2), yb - 2, rowp):
        x = x0 + int(rng.integers(0, 4))
        while x < x1 - 2:
            yy_ = int(yy) + int(rng.integers(-1, 2))
            if 0 <= yy_ + 2 < a.shape[0] and f[yy_ + 2, int(x)] and f[yy_ - 2, int(x)]:
                n = int(rng.integers(2, 5))
                for k in range(n):
                    hgt = int(rng.integers(2, 4))
                    xx = int(x) + k
                    fill(a, xx, yy_ - hgt + 1, xx + 1, yy_ + 1, code('sand', 3 + (k == 0)))
                    fill(a, xx, yy_ - hgt + 1, xx + 1, yy_ - hgt + 2, code('sand', 5))
                fill(a, int(x), yy_ + 1, int(x) + n, yy_ + 2, code('earth_warm', 2))
            x += int(rng.integers(3, 6))
    # windrows: raked hay lying in long soft ridges, lit on their north side, shade on the south
    for k, fy in enumerate((0.35, 0.72)):
        yc0 = y0 + (yb - y0) * fy
        amp = q(1.6)
        rid = f & (np.abs(Y - yc0 - amp * np.sin((X - x0) / q(9) + k)) < q(1.2)) & (X > x0 + q(4)) & (X < x1 - q(4))
        rid &= np.sin((X - x0) / q(5.5) + 2 * k) > -0.75                       # raked in lengths, gaps between
        d = Y - yc0 - amp * np.sin((X - x0) / q(9) + k)
        a[rid] = code('brass', 3)
        a[rid & (d < -q(0.6))] = code('brass', 4)
        a[rid & (d > q(0.8))] = code('brass', 2)
        a[rid & (((X.astype(int) * 7 + Y.astype(int) * 3) % 9) < 2)] = code('sand', 4)
        sh = f & ~rid & (d >= q(1.6)) & (d < q(2.4))
        a[sh & (a >= 0)] = np.maximum((a[sh & (a >= 0)] // 8) * 8, a[sh & (a >= 0)] - 1)
    # the field's edge: the stubble frays into the turf (a darker rim on its lower and east edges)
    T_, L_, B_, R_ = V.edges(f)
    a[B_ | R_] = code('earth_warm', 2)
    # bales standing on the cut field: two, each from the kit's bale painter, with a contact shade
    for (bxf, byf, s) in ((0.32, 0.55, 11), (0.7, 0.9, 13)):
        bp = V.prop('hay', 18, 10, seed=seed + s, hd=True)
        bx, by = int(x0 + (x1 - x0) * bxf), int(y0 + (yb - y0) * byf)
        sh = (np.abs(X - bx - q(1.5)) < q(10)) & (Y >= by - q(1.2)) & (Y < by + q(1.0)) & f
        a[sh & (a >= 0)] = np.maximum((a[sh & (a >= 0)] // 8) * 8, a[sh & (a >= 0)] - 1)
        ox, oy = bx - bp.ax, by - bp.ay
        src = bp.a
        hh, ww = src.shape
        Ys, Xs = np.nonzero(src >= 0)
        Yd, Xd = Ys + oy, Xs + ox
        ok = (Yd >= 0) & (Yd < a.shape[0]) & (Xd >= 0) & (Xd < a.shape[1])
        a[Yd[ok], Xd[ok]] = src[Ys[ok], Xs[ok]]
    V.tidy(a)
    return p
