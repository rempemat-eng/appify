"""Overlay decals that break the tile grid: placed by hand at the story spots and by hash
elsewhere. Each returns (code array with -1 = nothing, foot y offset) and, where it stands
on the ground, a cast-shadow mask thrown down and to the right."""
import numpy as np

from ..palette import C, FI, step

# r6 style constants (the 2x kit reads these)
IVY_FAMS = ['leaf', 'grass_cool', 'leaf']     # r6: ivy in the foliage greens (no cyan)

L3 = np.array([-0.55, -0.62, 0.56])
L3 = L3 / np.linalg.norm(L3)


def lump(w, h, seed, fams=('crag', 'crag_warm', 'crag_cool'), facets=True):
    """One rounded rock, w x h, faceted like the face sheet, outlined in its edge tone.
    r6: with the fixes at 1.5x and 2x it is a pixel-art stone (sheets.stone_paint), no facets."""
    from ..ctx import D as _D
    if _D > 1:
        return lump_px(w, h, seed, fams)
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    u, v = (xx - cx) / (w / 2), (yy - cy) / (h / 2)
    d = (np.abs(u) ** 2.3 + np.abs(v) ** 2.3) ** (1 / 2.3)
    m = d <= 1.0
    r2 = np.clip(u ** 2 + v ** 2, 0, 0.98)

    def lamb(a, b):
        rr = np.clip(a ** 2 + b ** 2, 0, 0.98)
        return a * L3[0] + b * L3[1] + np.sqrt(1 - rr) * L3[2]
    lam = lamb(u, v)
    if facets:
        k = int(np.clip(w * h / 40, 3, 9))
        ang = rng.random(k) * 2 * np.pi
        rad = np.sqrt(rng.random(k)) * 0.8
        fu, fv = rad * np.cos(ang), rad * np.sin(ang)
        dd = (u[..., None] - fu) ** 2 + ((v[..., None] - fv) * 1.3) ** 2
        j = dd.argmin(-1)
        lf = lamb(fu * 1.15, fv * 1.15)[j]
        rr = np.sqrt(r2)
        lam = np.where(rr > 0.85, lam, 0.8 * lf + 0.2 * lam)
        jj = j
    tone = np.full((h, w), 3)
    tone[lam > 0.80] = 4
    tone[lam > 0.93] = 5
    tone[lam < 0.58] = 2
    tone[lam < 0.32] = 1
    fam = fams[int(rng.integers(0, len(fams)))]
    out = np.where(m, FI[fam] * 8 + tone, -1)
    if facets:
        up = np.roll(jj, 1, 0)
        lf_ = np.roll(jj, 1, 1)
        joint = m & np.roll(m, 1, 0) & np.roll(m, 1, 1) & ((jj != up) | (jj != lf_))
        joint &= (xx + yy) % 3 != 0
        out[joint] = np.where(out[joint] % 8 > 1, out[joint] - 1, out[joint])
    # outline: edge tone, broken to tone 1 on the lit top-left
    p = np.pad(m, 1)
    border = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    lit = border & ((u + v) < -0.5)
    out[border] = C('crag', 6)
    out[lit] = FI[fam] * 8 + 1
    return out


def lump_px(w, h, seed, fams=('crag', 'crag_warm', 'crag_cool'), outline=('crag', 0)):
    """r6: a loose stone in pixel-art manner: an irregular round silhouette, the shared
    stone_paint ramp and texture, a dark edge on its lower right and a soft one-tone-1 edge on
    its upper left."""
    from . import sheets as _SH
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    u, v = (xx - cx) / (w / 2), (yy - cy) / (h / 2)
    th = np.arctan2(v, u)
    ph = rng.random() * 6.28
    wob = 1.0 + 0.07 * np.sin(3 * th + ph) + 0.04 * np.sin(5 * th + 2 * ph)
    wob = np.where(v > 0.55, np.minimum(wob, 1.0), wob)       # it sits flat-ish on the ground
    d = (np.abs(u) ** 2.3 + np.abs(v) ** 2.3) ** (1 / 2.3) / wob
    m = d <= 1.0
    U, V = u / wob, v / wob
    fam = fams[int(rng.integers(0, len(fams)))]
    code = np.full((h, w), -1)
    _SH.stone_paint(code, m, U, V, fam, rng, big=min(w, h) > 10)
    p = np.pad(m, 1)
    border = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    lit = border & ((u + v) < -0.3)
    if min(w, h) / 2 > _SH.STONE_SPLIT * _SH.D:
        # r8: a big loose boulder stays whole, with one natural crack: from a notch in its upper
        # edge, wandering down and across about half its height, a lit lip on its upper-left side
        y_, x_ = int(h * rng.uniform(0.12, 0.2)), int(w * rng.uniform(0.42, 0.6))
        while y_ < h and not m[y_, x_]:
            y_ += 1
        dx_ = rng.choice([-1, 1])
        for s_ in range(int(h * rng.uniform(0.4, 0.55))):
            if not (0 <= y_ < h and 0 <= x_ < w) or not m[y_, x_]:
                break
            code[y_, x_] = C('crag', 0)
            if x_ - 1 >= 0 and m[y_, x_ - 1] and code[y_, x_ - 1] % 8 < 5:
                code[y_, x_ - 1] += 1
            y_ += 1
            if rng.random() < 0.45:
                x_ += dx_
            if rng.random() < 0.12:
                dx_ = -dx_
    code[border] = C(*outline)
    code[lit] = FI[fam] * 8 + 1
    return np.where(m, code, -1)


LEAF4 = ('.ab.',
         'abbc',
         'bccd',
         '.dd.')
LEAF3 = ('ab.',
         'bcd',
         '.d.')


def paste(canvas, dec, x, y, shadow=None, shadow_dx=3, shadow_dy=2, under=None):
    """Draw a decal; -2 in a decal steps what is under it one tone up. With shadow, the
    decal's silhouette is thrown down-right onto what is already there, two tones down."""
    h, w = dec.shape
    H, W = canvas.shape
    m = dec >= 0
    if shadow:
        sm = np.zeros((H, W), bool)
        ys, xs = np.nonzero(m)
        sy, sx = ys + y + shadow_dy, xs + x + shadow_dx
        ok = (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
        sm[sy[ok], sx[ok]] = True
        if under is not None:
            sm &= under
        canvas[sm & (canvas >= 0)] = step(canvas[sm & (canvas >= 0)], -2)
    for yy in range(h):
        for xx in range(w):
            c = dec[yy, xx]
            Y, X = y + yy, x + xx
            if not (0 <= Y < H and 0 <= X < W):
                continue
            if c >= 0:
                canvas[Y, X] = c
            elif c == -2 and canvas[Y, X] >= 0:
                canvas[Y, X] = step(canvas[Y, X], 1)


# --- density-native versions (the same pieces, drawn at D art px per world px) ---------------


def ivy2(seed, w, h, D):
    """r1 ivy at any density: three to five strands of different lengths hanging from the lip,
    each a sinuous 1 px stem (dark, a lit px on its west side at 2x) with leaves of three sizes
    (2 to 4 world px) set alternately left and right at irregular spacing, each leaf lit at its
    upper left and dark at its lower right; the strands thin towards their tips."""
    rng = np.random.default_rng(seed + 7000)
    out = np.full((h, w), -1)
    ns = 3 + int(rng.integers(0, 3))
    xs = np.sort(rng.uniform(0.12, 0.88, ns)) * w
    fams = IVY_FAMS
    for s_, x0 in enumerate(xs):
        L = h * rng.uniform(0.35, 1.0)
        amp = rng.uniform(0.6, 1.6) * D
        lam = rng.uniform(5, 9) * D
        ph = rng.uniform(0, 6.3)
        X = lambda y: x0 + amp * np.sin(y / lam + ph)
        for y in range(int(L)):
            ix = int(round(X(y)))
            if 0 <= ix < w:
                out[y, ix] = C('leaf', 1)
                if D >= 1.75 and 0 <= ix - 1 < w and out[y, ix - 1] < 0 and y % 3:
                    out[y, ix - 1] = C('leaf', 2)
        y = rng.uniform(0, 2) * D
        side = int(rng.integers(0, 2))
        while y < L:
            frac = y / max(L, 1)
            if rng.random() < 0.15 + 0.5 * frac:
                y += rng.uniform(2, 4) * D
                side ^= 1
                continue
            size = rng.choice([2.0, 3.0, 4.0], p=[0.3, 0.45, 0.25]) * (1.0 - 0.35 * frac)
            fam = fams[int(rng.integers(0, 3))]
            base = 3 if frac < 0.6 else 2
            cx0 = X(y) + (-1 if side else 1) * size * 0.5 * D
            cy0 = y + size * 0.35 * D
            # r6: a cluster of two or three small leaves hanging off the node (foliage greens)
            nl = 1 if D < 1.25 else int(rng.integers(2, 4))
            for li in range(nl):
                cx = cx0 + (rng.uniform(-0.5, 0.5) * size * D if li else 0)
                cy = cy0 + li * size * 0.45 * D
                sz = size * (1.0 if li == 0 else 0.75)
                rx, ry = max(0.8, sz * 0.5 * D), max(0.7, sz * 0.45 * D)
                for yy in range(int(cy - ry - 1), int(cy + ry + 2)):
                    for xx in range(int(cx - rx - 1), int(cx + rx + 2)):
                        if not (0 <= yy < h and 0 <= xx < w):
                            continue
                        u, v = (xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry
                        if u * u + (v - 0.25 * u * u) ** 2 > 1:      # a leaf drooping at its tip
                            continue
                        t = base + 1 if (u + v < -0.5) else (base - 1 if (u + v > 0.7) else base)
                        out[yy, xx] = C(fam, max(1, min(4, t)))
            side ^= 1
            y += rng.uniform(3.0, 6.0) * D * (0.7 if frac < 0.3 else 1.0)
    return out
