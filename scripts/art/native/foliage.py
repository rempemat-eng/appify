"""r4 foliage: crowns and bushes painted natively at any density from the 1x master sprite.

The 1x master is the design: its silhouette, its lobes and clumps, its light and its hues. Each
master pixel is read as (family, tone) on the house ramps; that map is carried to the target
density as a smooth tone field and a family map, and the crown is then painted the way Eastward
paints foliage: overlapping leaf stamps (5 to 7 px at 2x), each in the tone of the field under its
centre, with a lit upper-left edge and a darker lower-right edge, darker leaves first so lit leaves
overlap them (pockets are gatherings of dark leaves, never a stroked line), leaves jutting a few px
past the rim. The silhouette closes in the foliage's own dark green: tone 1 on the upper left,
tone 0 on the lower right (the same rule the 1x masters get)."""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import raster as pk

GREENS = ['grass', 'grass_cool', 'grass_warm', 'leaf']     # r5: no blue-teal leaf_cool, no leaf_warm
EDGE_LIT = ('grass_cool', 1)
CAPHI = 3.9
# r6 style constants (crisper leaves, deeper pockets)
LEAF_JITTER = 0.08
LEAF_PITCH = 1.75
POCKET = 1.35
LOCAL_SIGMA = 3.0
LOCAL_CONTRAST = 1.9
EDGE_DARK = ('grass_cool', 0)

# leaf stamps (art px); the big set at 2x, the small set at 1.5x, single tufts at 1x
_BIG = ["..X..\nX.X.X\nXXXXX\n.XXX.\n.X.X.",
        ".XX.X.\nXXXXXX\nXXXXX.\n.X.XX.",
        "...X...\n.XXXXX.\nXXXXXXX\n.XXXXX.\n..X.X..",
        "..X..\n.XXX.\nXXXXX\nXXXXX\n.XXX.\n..X.."]
_SMALL = [".X.X\nXXXX\n.XXX\n..X.", "..X.\n.XXX\nXXXX\n.X..", ".XX.\nXXXX\nXXXX\n.X..", "X.X\nXXX\n.X."]
_TINY = [".X.\nXXX\n.X.", "XX\nXX", "X.\nXX"]


def _parse(s):
    return np.array([[c == 'X' for c in row] for row in s.split('\n')], bool)


def _variants(shapes):
    out = []
    for s in shapes:
        m = _parse(s)
        for k in range(4):
            r = np.rot90(m, k)
            out.append(r)
            out.append(r[:, ::-1])
    return out


STAMPS = {'big': _variants(_BIG), 'small': _variants(_SMALL), 'tiny': _variants(_TINY)}
_PAL = [(f, t, np.array(pk.rgb(f, t), float)) for f in GREENS for t in range(6)]


def read_master(arr, crease_depth=1.0):
    """Classify a 1x master (RGBA uint8 array): returns tone (float, nan off foliage), family
    index, foliage mask (greens + outline + blossoms), blossom mask, wood mask."""
    rgb = arr[..., :3].astype(float)
    a = arr[..., 3] > 0
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    L = 0.299 * R + 0.587 * G + 0.114 * B
    green = a & (G > R + 4)
    blossom = a & ~green & (R > 180) & (L > 150)
    wood = a & ~green & ~blossom & (R > G + 10) & (L > 55)
    outline = a & ~green & ~blossom & ~wood & ndi.binary_dilation(green, iterations=1)
    H, W = a.shape
    tone = np.full((H, W), np.nan)
    fam = np.zeros((H, W), int)
    for y, x in zip(*np.nonzero(green)):
        c = rgb[y, x]
        d = [((c - p) ** 2).sum() for (_, _, p) in _PAL]
        k = int(np.argmin(d))
        tone[y, x] = _PAL[k][1]
        fam[y, x] = GREENS.index(_PAL[k][0])
    fol = green | outline | blossom
    # outline pixels belong to the silhouette; they carry the tone of the leaves beside them
    # minus one (the rim is in shade), so the field has no hole there
    known = ~np.isnan(tone)
    if known.any():
        idx = ndi.distance_transform_edt(~known, return_distances=False, return_indices=True)
        tf = tone[idx[0], idx[1]]
        ff = fam[idx[0], idx[1]]
    else:
        tf, ff = np.full((H, W), 3.0), fam
    # the silhouette's own outline is the rim in shade (one tone down); an outline pixel inside
    # the crown is a crease between clumps: a pocket (tone 0)
    P = np.pad(a, 1)
    rim = outline & ~(P[:-2, 1:-1] & P[2:, 1:-1] & P[1:-1, :-2] & P[1:-1, 2:])
    tf = np.where(rim, np.maximum(0, tf - 1), tf)
    tf = np.where(outline & ~rim, 0.0, tf)
    # a thin dark line in the master (darker than the pixels on both sides by more than a tone)
    # is a crease between lobes: deepen it into a pocket
    t0 = np.where(np.isnan(tone), tf, tone)
    Pt = np.pad(t0, 1, mode='edge')
    creaseh = (t0 < np.minimum(Pt[1:-1, :-2], Pt[1:-1, 2:]) - 1.0)
    creasev = (t0 < np.minimum(Pt[:-2, 1:-1], Pt[2:, 1:-1]) - 1.0)
    crease = (creaseh | creasev) & green & ~rim
    # r6: a crease spreads a little into the clump below it, so the pocket reads at 2x
    if crease_depth > 1.0:
        below = np.zeros_like(crease)
        below[1:] = crease[:-1]
        crease |= below & green & ~rim
    tf = np.where(crease, np.maximum(0.0, tf - crease_depth), tf)
    return tf, ff, fol & ~wood, blossom, wood


def _luma_green(a):
    m = (a[..., 3] > 0) & (a[..., 1].astype(int) > a[..., 0].astype(int) + 4)
    c = a[..., :3].astype(float)
    return float((0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2])[m].mean()) if m.any() else 0.0


def paint(arr, d, seed=0, size=None, blossoms=True, legs=True, crease=True, crease_depth=1.0):
    """Paint, then match the master's lightness: the foliage's mean luma is brought within
    about 2 points of the 1x master's by a small bias on the tone field."""
    target = _luma_green(arr) - 2.5
    bias = 0.0
    best = None
    for _ in range(9):
        out, anc, info = _paint(arr, d, seed, size, blossoms, legs, bias, crease_depth)
        diff = _luma_green(out) - target
        if best is None or abs(diff) < best[0]:
            best = (abs(diff), out, anc, info)
        if abs(diff) <= 2.0:
            break
        bias -= diff / 40.0
    _, out, anc, info = best
    return out, anc, info


def _paint(arr, d, seed, size, blossoms, legs, bias, crease_depth=1.0):
    """Paint the master `arr` (1x RGBA) natively at density d. size=(w, h) in world px rescales
    the design (for the smaller c-tiles shrubs). Returns RGBA uint8 and the anchor (bottom
    centre of the master's box, in output px)."""
    H1, W1 = arr.shape[:2]
    tf, ff, fol, bl, wood = read_master(arr, crease_depth)
    sx = d * (size[0] / W1 if size else 1.0)
    sy = d * (size[1] / H1 if size else 1.0)
    W, H = int(round(W1 * sx)), int(round(H1 * sy))
    pad = int(np.ceil(3 * d)) + 2
    Wp, Hp = W + 2 * pad, H + 2 * pad
    rng = np.random.default_rng(seed)
    # fields at the target density
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    u = (xx - pad + 0.5) / sx - 0.5          # master coords
    v = (yy - pad + 0.5) / sy - 0.5
    field = ndi.map_coordinates(tf, [v, u], order=1, mode='nearest')
    # r6: clumps read crisper: the field's local contrast raised (caps up, pockets down)
    loc = ndi.gaussian_filter(field, LOCAL_SIGMA * sx)
    field = loc + LOCAL_CONTRAST * (field - loc)
    fmask = ndi.map_coordinates(fol.astype(float), [v, u], order=1, mode='constant', cval=0.0)
    ui, vi = np.clip(np.round(u).astype(int), 0, W1 - 1), np.clip(np.round(v).astype(int), 0, H1 - 1)
    famp = ff[vi, ui]
    mask = fmask > 0.5
    if d < 1.25 and size is None:
        mask = fol[vi, ui] & (u > -0.5) & (u < W1 - 0.5) & (v > -0.5) & (v < H1 - 0.5)
    # the master's creases (its darkest interior lines) as a field too, so pockets follow them
    tone = np.full((Hp, Wp), -1, int)
    famo = np.zeros((Hp, Wp), int)
    kind = 'big' if d >= 1.75 else ('small' if d >= 1.25 else 'tiny')
    stamps = STAMPS[kind]
    # the big stamps are drawn at 2x texels: past 2x the pitch stays at their 2x spacing, so the
    # leaves still overlap into one mass (at 3x a 1.5x wider pitch left the crown a lace; Claude B,
    # lane R 25 Oct 17:08 finding 3). Unchanged at density 2 and below.
    pitch = max(1.0, LEAF_PITCH * min(d, 2.0) * (0.9 if kind == 'tiny' else 1.0))
    allow = ndi.binary_dilation(mask, iterations=max(1, int(round(1.6 * d)))) if kind != 'tiny' else mask
    leaves = []
    for cy in np.arange(0, Hp, pitch):
        for cx in np.arange(0, Wp, pitch):
            y, x = int(cy + rng.uniform(0, pitch)), int(cx + rng.uniform(0, pitch))
            if not (0 <= y < Hp and 0 <= x < Wp) or not mask[y, x]:
                continue
            f = field[y, x] + bias + rng.normal(0, LEAF_JITTER)
            t = int(np.clip(np.round(f), 0, 5))
            leaves.append((t, rng.random(), y, x, int(famp[y, x])))
    leaves.sort()
    fvals = np.array([field[y, x] for (_, _, y, x, _) in leaves]) if leaves else np.zeros(1)
    crest = np.quantile(fvals, 0.88) if len(fvals) else 9
    for (t, _, y, x, fi) in leaves:
        if field[y, x] + bias < POCKET and t >= 1:
            t = t - 1                                 # r5: the pocket cores a tone deeper
        cap_edge = False
        if t >= 4 and field[y, x] + bias < CAPHI:
            t, cap_edge = 3, True                     # r5: caps are tone-3 leaves with tone-4 edges
        st = stamps[int(rng.integers(0, len(stamps)))]
        h, w = st.shape
        y0, x0 = y - h // 2, x - w // 2
        sub = np.zeros((Hp, Wp), bool)
        ys_, xs_ = np.nonzero(st)
        Y, X = ys_ + y0, xs_ + x0
        ok = (Y >= 0) & (Y < Hp) & (X >= 0) & (X < Wp)
        Y, X = Y[ok], X[ok]
        keep = allow[Y, X]
        Y, X = Y[keep], X[keep]
        if not len(Y):
            continue
        sub[Y, X] = True
        tone[sub] = t
        if rng.random() < 0.12:     # a sibling hue now and then, as a whole leaf
            fi = GREENS.index(['grass_cool', 'leaf', 'grass'][int(rng.integers(0, 3))]) if t < 4 \
                else GREENS.index('grass')
        famo[sub] = GREENS.index('grass_cool') if t >= 4 else fi   # r5: the brightest leaves at about 165
        if kind != 'tiny':
            ul = sub & ~(np.roll(sub, 1, 0) & np.roll(sub, 1, 1))
            lr = sub & ~(np.roll(sub, -1, 0) & np.roll(sub, -1, 1))
            if (field[y, x] >= crest or cap_edge) and t >= 2:
                tone[ul & ~lr] = 4            # r5: the crest: the cap's leading leaf edges at the brightest tone
                famo[ul & ~lr] = GREENS.index('grass_cool')
            elif t == 3 and field[y, x] > 3.2:
                tone[ul & ~lr] = 4            # a lit leaf edge where the body turns to the light
            elif t == 4 and field[y, x] >= 4.35 and rng.random() < 0.3:
                tone[ul & ~lr] = 5           # a small glint on the brightest caps only
            if t >= 1:
                tone[lr & ~ul] = t - 1
    painted = tone >= 0
    # no lone pixels: a pixel unlike all four neighbours takes the commonest of them
    key = np.where(painted, famo * 8 + tone, -1)
    for _ in range(2):
        P = np.pad(key, 1, constant_values=-1)
        nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
        lone = painted & (key != nb[0]) & (key != nb[1]) & (key != nb[2]) & (key != nb[3])
        for y, x in zip(*np.nonzero(lone)):
            vals = [v for v in nb[:, y, x] if v >= 0]
            if vals:
                key[y, x] = max(set(vals), key=vals.count)
    famo, tone = np.where(key >= 0, key // 8, 0), np.where(key >= 0, key % 8, -1)
    painted = tone >= 0
    # fill pinholes inside the silhouette
    holes = ndi.binary_fill_holes(painted) & ~painted
    if holes.any():
        idx = ndi.distance_transform_edt(~painted, return_distances=False, return_indices=True)
        tone[holes] = tone[idx[0][holes], idx[1][holes]]
        famo[holes] = famo[idx[0][holes], idx[1][holes]]
        painted |= holes
    out = np.zeros((Hp, Wp, 4), np.uint8)
    for fi, f in enumerate(GREENS):
        for t in range(6):
            m = painted & (famo == fi) & (tone == t)
            if m.any():
                out[m, :3] = pk.rgb(f, t)
                out[m, 3] = 255
    # r5: no sawtooth: lone spurs off the silhouette go, one-pixel notches fill
    for _ in range(2):
        P4_ = np.pad(painted, 1)
        nbn = P4_[:-2, 1:-1].astype(int) + P4_[2:, 1:-1] + P4_[1:-1, :-2] + P4_[1:-1, 2:]
        spur = painted & (nbn <= 1)
        notch = ~painted & (nbn >= 3)
        if notch.any():
            idx = ndi.distance_transform_edt(~painted, return_distances=False, return_indices=True)
            tone[notch] = tone[idx[0][notch], idx[1][notch]]
            famo[notch] = famo[idx[0][notch], idx[1][notch]]
        painted = (painted & ~spur) | notch
        tone[~painted] = -1
    out[...] = 0
    for fi, f in enumerate(GREENS):
        for t in range(6):
            m = painted & (famo == fi) & (tone == t)
            if m.any():
                out[m, :3] = pk.rgb(f, t)
                out[m, 3] = 255
    # the silhouette closes in the foliage's own dark green
    inner = ndi.binary_erosion(painted)
    edge = painted & ~inner
    P = np.pad(painted, 1)
    out_up, out_left = ~P[:-2, 1:-1], ~P[1:-1, :-2]
    lit_side = edge & (out_up | out_left)
    out[edge & ~lit_side, :3] = pk.rgb(*EDGE_DARK)
    # r5: on the lit side the leaf closes one tone down in its own green (not a dark line)
    for y, x in zip(*np.nonzero(lit_side)):
        out[y, x, :3] = pk.rgb(GREENS[famo[y, x]], int(max(1, min(2, tone[y, x] - 1))))
    # blossoms: the master's orange dots, 2 x 2 at 2x with one lit pixel
    if blossoms and bl.any() and size is None:
        for y1, x1 in zip(*np.nonzero(bl)):
            c = arr[y1, x1, :3]
            if c[1] > 210:      # the master's pale pixel is the dot's light; place the dot by its orange
                continue
            y, x = int(pad + y1 * sy), int(pad + x1 * sx)
            k = max(1, int(round(d)))
            out[y:y + k, x:x + k, :3] = pk.rgb('brass_warm', 4)
            out[y:y + k, x:x + k, 3] = 255
            out[y, x, :3] = pk.rgb('sand', 5)
    # legs (the bush's stubs): the master's wood pixels below the foliage, drawn as round stems
    if legs and wood.any() and size is None:
        ys_, xs_ = np.nonzero(wood)
        lab, n = ndi.label(wood)
        for i in range(1, n + 1):
            yy1, xx1 = np.nonzero(lab == i)
            x0, x1_ = int(pad + xx1.min() * sx), int(pad + (xx1.max() + 1) * sx)
            y0, y1_ = int(pad + yy1.min() * sy), int(pad + (yy1.max() + 1) * sy)
            for y in range(y0, min(Hp, y1_)):
                for x in range(x0, min(Wp, x1_)):
                    if out[y, x, 3] and y < y0 + d:     # the foliage stays in front at the top
                        continue
                    u_ = (x - x0) / max(1, x1_ - x0)
                    c = pk.rgb('timber_cool', 3 if u_ < 0.34 else (2 if u_ < 0.75 else 1))
                    if y >= y1_ - max(1, int(d / 2)):
                        c = pk.rgb('timber_cool', 0)
                    out[y, x, :3] = c
                    out[y, x, 3] = 255
    anc = (pad + W1 * sx / 2.0, pad + H1 * sy)
    return out, anc, (pad, sx, sy)


def relight_1x(arr, k_global=1.0, seed=0):
    """r5: light a 1x master crown from the upper left. Each green pixel moves on its own ramp:
    up to a tone on the crown's west and north, down on its east and south (a smooth gradient
    across the crown), plus each clump's own light: a tone up on the cap just inside the clump's
    upper-left rim, a tone down along its lower-right rim (rims found from the crease lines and
    the silhouette). The family (hue) of every pixel is kept."""
    a = arr.copy()
    tf, ff, fol, bl, wood = read_master(a)
    rgb = a[..., :3].astype(int)
    al = a[..., 3] > 0
    green = al & (rgb[..., 1] > rgb[..., 0] + 4)
    tone = np.where(green, np.round(tf), -1).astype(int)
    ys, xs = np.nonzero(green)
    cx, cy = xs.mean(), ys.mean()
    rx, ry = (xs.max() - xs.min()) / 2 + 1, (ys.max() - ys.min()) / 2 + 1
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    lg = -0.62 * (X - cx) / rx - 0.5 * (Y - cy) / ry
    delta = np.round(np.clip(lg * 1.6 * k_global, -1.3, 1.3)).astype(int)
    # creases and the silhouette bound the clumps
    crease = (al & ~green) | (green & (tone <= 1))
    crease |= ~al
    dist, (iy, ix) = ndi.distance_transform_edt(~crease, return_indices=True)
    vy, vx = iy - Y, ix - X                       # towards the nearest crease
    towards_lr = (vx + vy) > 0
    delta += np.where(green & towards_lr & (dist <= 2.0), -1, 0)
    delta += np.where(green & ~towards_lr & (dist >= 2.0) & (dist <= 3.5), 1, 0)
    nt = np.clip(tone + np.clip(delta, -2, 2), 1, 4)
    for y, x in zip(ys, xs):
        if tone[y, x] <= 1:
            continue                              # the creases stay as drawn
        f = GREENS[ff[y, x]]
        a[y, x, :3] = pk.rgb(f, int(nt[y, x]))
    return a
