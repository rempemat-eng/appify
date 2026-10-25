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

from . import ctx
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
# r7 style (the biome's style.foliage): the clump field's share of the crown's tone field, the
# leaf-jagged lit rim one tone down, lit leaves on the cool sibling (a touch cooler than the lawn)
_FS = ctx.BIOME.get('style', {}).get('foliage', {})
CLUMP_MIX = _FS.get('clump_mix', 0.7)
LIT_RIM = _FS.get('lit_rim', True)
COOL_LIT = _FS.get('cool_lit', True)
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


def clump_field(fol, n, seed=0):
    """r7: a tone field (at the master's 1x size) made of n readable clumps laid over the master's
    silhouette: the silhouette's pixels are split into n clusters (k-means), each becomes a dome
    lit from the upper left (a lit cap, the body, a shaded lower right, a dark rim along its
    underside); clumps lower on the screen stand in front, and where a front clump rises over
    the one behind, the back clump is in a dark pocket."""
    ys, xs = np.nonzero(fol)
    P_ = np.stack([xs, ys], 1).astype(float)
    rng = np.random.default_rng(seed + 991)
    # k-means with farthest-point seeding (deterministic)
    cen = [P_[np.argmin(P_[:, 1])]]
    for _ in range(1, n):
        dmin = np.min([((P_ - c) ** 2).sum(1) for c in cen], 0)
        cen.append(P_[np.argmax(dmin)])
    cen = np.array(cen)
    for _ in range(12):
        lab = np.argmin(((P_[:, None, :] - cen[None]) ** 2).sum(2), 1)
        cen = np.array([P_[lab == k].mean(0) if (lab == k).any() else cen[k] for k in range(n)])
    rad = np.array([np.sqrt(max(1, (lab == k).sum()) / np.pi) * 1.18 for k in range(n)])
    order = np.argsort(cen[:, 1])                        # back (higher) first
    H, W = fol.shape
    Y, X = np.mgrid[0:H, 0:W].astype(float)
    owner = np.full((H, W), -1)
    for k in order:
        m = (((X - cen[k, 0]) / rad[k]) ** 2 + ((Y - cen[k, 1]) / (rad[k] * 0.92)) ** 2 <= 1.0) & fol
        owner[m] = k
    if (owner < 0).any():
        miss = fol & (owner < 0)
        yy, xx = np.nonzero(miss)
        owner[yy, xx] = np.argmin((xx[:, None] - cen[None, :, 0]) ** 2 + (yy[:, None] - cen[None, :, 1]) ** 2, 1)
    L = np.array([-0.55, -0.62, 0.56]); L = L / np.linalg.norm(L)
    tone = np.full((H, W), 2.0)
    for k in range(n):
        m = owner == k
        u = (X - cen[k, 0]) / rad[k]
        v = (Y - cen[k, 1]) / (rad[k] * 0.92)
        lam = u * L[0] + v * L[1] + np.sqrt(np.clip(1 - u * u - v * v, 0.02, 1)) * L[2]
        t = np.full((H, W), 3.0)
        t[lam > 0.80] = 4.0
        t[lam < 0.52] = 2.0
        t[lam < 0.25] = 1.0
        tone[m] = t[m]
    # dark rims and pockets where clumps meet: the back clump darkens along the front clump's edge
    for k in range(n):
        m = owner == k
        ring = ndi.binary_dilation(m, iterations=1) & ~m & fol
        tone[ring & (owner != k)] = np.minimum(tone[ring & (owner != k)], 0.5)
    tone[~fol] = 2.0
    return tone


def _luma_green(a):
    m = (a[..., 3] > 0) & (a[..., 1].astype(int) > a[..., 0].astype(int) + 4)
    c = a[..., :3].astype(float)
    return float((0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2])[m].mean()) if m.any() else 0.0


def paint(arr, d, seed=0, size=None, blossoms=True, legs=True, crease=True, crease_depth=1.0, clumps=0):
    """Paint, then match the master's lightness: the foliage's mean luma is brought within
    about 2 points of the 1x master's by a small bias on the tone field."""
    target = _luma_green(arr) - 2.5
    bias = 0.0
    best = None
    for _ in range(9):
        out, anc, info = _paint(arr, d, seed, size, blossoms, legs, bias, crease_depth, clumps)
        diff = _luma_green(out) - target
        if best is None or abs(diff) < best[0]:
            best = (abs(diff), out, anc, info)
        if abs(diff) <= 2.0:
            break
        bias -= diff / 40.0
    _, out, anc, info = best
    return out, anc, info


def _paint(arr, d, seed, size, blossoms, legs, bias, crease_depth=1.0, clumps=0):
    """Paint the master `arr` (1x RGBA) natively at density d. size=(w, h) in world px rescales
    the design (for the smaller c-tiles shrubs). Returns RGBA uint8 and the anchor (bottom
    centre of the master's box, in output px)."""
    H1, W1 = arr.shape[:2]
    tf, ff, fol, bl, wood = read_master(arr, crease_depth)
    if clumps:
        tf = CLUMP_MIX * clump_field(fol, clumps, seed) + (1 - CLUMP_MIX) * tf
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
    pitch = max(1.0, LEAF_PITCH * d * (0.9 if kind == 'tiny' else 1.0))
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
        famo[sub] = GREENS.index('grass_cool') if (t >= 4 or (COOL_LIT and t == 3 and fi == GREENS.index('grass'))) else fi   # r5: the brightest leaves at about 165
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
    if kind != 'tiny' and LIT_RIM:
        # r7: the lit side closes in a leaf-jagged rim one tone down: 1 to 2 px deep, in leaf-sized
        # bumps (cells of 2 to 3 px), so the crown's sunny outline is leaves, not a traced line
        dist, (iy, ix) = ndi.distance_transform_edt(painted, return_indices=True)
        lit_dir = ((iy - yy) < 0) | ((ix - xx) < 0)
        cell = (((yy // 2) * 73856093) ^ ((xx // 3) * 19349663)) & 0xff
        deep = np.where(cell % 3 == 0, 2.5, np.where(cell % 3 == 1, 1.5, 1.0))
        rim = painted & lit_dir & (dist <= deep) & ~edge & (tone >= 3)
        for y, x in zip(*np.nonzero(rim)):
            out[y, x, :3] = pk.rgb(GREENS[famo[y, x]], int(tone[y, x] - 1))
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


# ------------------------------------------------------------------------------------------------
# density 3 and up: leaf masses (25 Oct, Matt: "especially the trees look really strange")
# ------------------------------------------------------------------------------------------------
# At 2x the leaf stamps above read as foliage; at 3x and 4x the same algorithm draws a mesh of
# thin dark contours round many small cells. From density HD on, a crown is painted the way
# Eastward paints one: a few large clumps laid over the master's silhouette, each a dome lit from
# the upper left (a lit top, a mid-tone body, a shaded lower right, a dark under-shade where it
# tucks under the clump in front of it), the tones meeting in leaf-shaped scallops whose lit tips
# point down; sparse leaf marks and glints inside; leaf tips break the silhouette, and only the
# silhouette is outlined. Sizes are in world px, so the masses keep their size at every density.
HD = 2.5
LAST_MASS = {}      # the last crown's leaf mass (no strands): the trunk is sized under it

# a leaf at density 3 (scaled for other densities): rounded, its tip pointing down
_LEAF3 = [".XXX.", "XXXXX", "XXXXX", ".XXX.", "..X.."]


def _leaf_stamp(d):
    """The leaf for density d: the 3x leaf at d < 3.5, a larger one at 4x."""
    if d < 3.5:
        rows = _LEAF3
    else:
        rows = ["..XXX..", ".XXXXX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
    return _parse('\n'.join(rows))


def _clump_cover(S, r, rng, max_n=16, cover=0.97):
    """Circles of radius about r (texels) that cover the mask S: greedy, each pick the centre that
    covers most of what is still bare. Returns [(cx, cy, r)]."""
    H, W = S.shape
    Y, X = np.mgrid[0:H, 0:W]
    inner = ndi.binary_erosion(S, iterations=max(1, int(r * 0.45)))
    if inner.sum() < 4:
        inner = S
    ys, xs = np.nonzero(inner)
    step = max(1, int(r / 3))
    sel = (ys % step == 0) & (xs % step == 0)
    cand = np.stack([xs[sel], ys[sel]], 1) if sel.any() else np.stack([xs, ys], 1)
    bare = S.copy()
    total = S.sum()
    out = []
    while len(out) < max_n and bare.sum() > (1 - cover) * total:
        rr = r * rng.uniform(0.88, 1.12)
        best, bscore = None, 0
        for (cx, cy) in cand:
            y0, y1 = max(0, int(cy - rr)), min(H, int(cy + rr) + 1)
            x0, x1 = max(0, int(cx - rr)), min(W, int(cx + rr) + 1)
            sub = bare[y0:y1, x0:x1]
            m = (X[y0:y1, x0:x1] - cx) ** 2 + (Y[y0:y1, x0:x1] - cy) ** 2 <= rr * rr
            sc = int((sub & m).sum())
            if sc > bscore:
                best, bscore = (float(cx), float(cy), rr), sc
        if best is None or bscore < 0.08 * np.pi * rr * rr:
            break
        cx, cy, rr = best
        bare &= ~((X - cx) ** 2 + (Y - cy) ** 2 <= rr * rr)
        out.append(best)
    return out


def _tiers(S, th):
    """A conifer's tiers: bands th texels tall from the top down, each an ellipse as wide as the
    silhouette at the band's foot (the skirt), lower tiers in front."""
    ys = np.nonzero(S.any(1))[0]
    out = []
    y = float(ys.min())
    while y < ys.max() - th * 0.4:
        yb = int(min(ys.max(), y + th))
        cols = np.nonzero(S[yb])[0] if S[yb].any() else np.nonzero(S[int(y)])[0]
        xl, xr = cols.min(), cols.max()
        out.append(((xl + xr) / 2.0, y + th * 0.55, (xr - xl) / 2.0 + 1, th * 0.62))
        y += th * 0.72
    return out


def paint_masses(arr, d, seed=0, look=None, size=None):
    """Paint the master `arr` (1x RGBA) as leaf masses at density d (>= HD). look (the biome's
    recipe 'crown'): form ('round', 'conifer', 'weeping', 'bush'), clump (a clump's radius in
    world px), fam (the body's green), lit (the lit top's green), shade (the under-shade's
    green), dark (tones down for a darker tree, 0 or 1), berries (a family for the master's
    blossoms, or none). size=(w, h) world px rescales the design. Returns (RGBA uint8, anchor,
    (pad, sx, sy)) like paint()."""
    lk = dict(form='round', clump=8.0, fam='grass', lit='grass', shade='grass_cool', dark=0, berries=None,
              glint=0.25, marks=0.2)
    lk.update(look or {})
    H1, W1 = arr.shape[:2]
    _tf, _ff, fol, bl, wood = read_master(arr)
    # the crown is the master's greens (closed, filled): never its trunk, stems or outline
    a8 = arr.astype(int)
    green = (a8[..., 3] > 0) & (a8[..., 1] > a8[..., 0] + 4)
    fol = ndi.binary_fill_holes(ndi.binary_closing(np.pad(green, 2), iterations=1))[2:-2, 2:-2] & (a8[..., 3] > 0)
    fol |= green
    # below the crown's foot (the first row under its widest that is narrower than a fifth of
    # it; a weeping crown's foot is where its strands begin) is trunk, not crown
    widths = fol.sum(1)
    wmax = widths.max()
    peak = int(np.argmax(widths))
    cut_share = 0.62 if lk['form'] == 'weeping' else 0.2
    low = np.nonzero((np.arange(H1) > peak) & (widths < cut_share * wmax))[0]
    strands = np.zeros_like(fol)
    if len(low):
        strands[low[0]:] = green[low[0]:]
        fol[low[0]:] = False
    sx = d * (size[0] / W1 if size else 1.0)
    sy = d * (size[1] / H1 if size else 1.0)
    W, H = int(round(W1 * sx)), int(round(H1 * sy))
    pad = int(np.ceil(2 * d)) + 2
    Wp, Hp = W + 2 * pad, H + 2 * pad
    rng = np.random.default_rng(seed + 4049)
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    u = (xx - pad + 0.5) / sx - 0.5
    v = (yy - pad + 0.5) / sy - 0.5
    # the silhouette, smooth at this density (no 1x stair steps), held a leaf inside the master's
    # edge so the leaf tips can break it
    f = ndi.map_coordinates(ndi.gaussian_filter(fol.astype(float), 0.7), [v, u], order=1, mode='constant', cval=0.0)
    S = f > 0.42
    if lk['form'] == 'bush':
        # a bush sits on the ground: its foot flattened, no stems
        ys_ = np.nonzero(S.any(1))[0]
        S[ys_.max() - max(1, int(0.6 * d)) + 1:] = False
    if lk['form'] != 'bush':
        # no bay under the crown where the master's trunk stood: its underside closes over it
        r_ = max(2, int(round(2.5 * d)))
        Y_, X_ = np.mgrid[-r_:r_ + 1, -r_:r_ + 1]
        S = ndi.binary_closing(np.pad(S, r_ + 1), structure=(X_ * X_ + Y_ * Y_) <= r_ * r_)[r_ + 1:-r_ - 1, r_ + 1:-r_ - 1]
    lab, n = ndi.label(S)
    if n > 1:                                         # strays off the main mass go
        sizes = ndi.sum(S, lab, range(1, n + 1))
        S = np.isin(lab, 1 + np.nonzero(sizes >= 0.04 * sizes.max())[0])
    leaf = _leaf_stamp(d)
    lh, lw = leaf.shape
    S_in = ndi.binary_erosion(S, iterations=max(1, int(round(0.5 * d))))
    if S_in.sum() < 10:
        S_in = S
    # the clumps
    r = lk['clump'] * d
    if lk['form'] == 'conifer':
        clumps = [(cx, cy, rx, ry) for (cx, cy, rx, ry) in _tiers(S_in, r)]
    else:
        clumps = [(cx, cy, rr, rr * 0.9) for (cx, cy, rr) in _clump_cover(S_in, r, rng)]
    if not clumps:
        ys_, xs_ = np.nonzero(S)
        clumps = [(xs_.mean(), ys_.mean(), (xs_.max() - xs_.min()) / 2 + 1, (ys_.max() - ys_.min()) / 2 + 1)]
    clumps.sort(key=lambda c: (c[1] + 0.15 * c[0]))       # back (higher) first, lower in front
    owner = np.full((Hp, Wp), -1)
    for k, (cx, cy, rx, ry) in enumerate(clumps):
        ang = np.arctan2(yy - cy, xx - cx)
        ph = rng.uniform(0, 6.283, 3)
        wob = 1 + 0.07 * np.sin(3 * ang + ph[0]) + 0.05 * np.sin(5 * ang + ph[1])
        m = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= wob * wob) & S
        owner[m] = k
    miss = S & (owner < 0)
    if miss.any():
        idx = ndi.distance_transform_edt(owner < 0, return_distances=False, return_indices=True)
        owner[miss] = owner[idx[0][miss], idx[1][miss]]
    # the light: each clump a dome lit from the upper left, plus the crown as a whole
    L = np.array([-0.55, -0.68, 0.48])
    L = L / np.linalg.norm(L)
    C = np.array(clumps, float)
    cx, cy, rx, ry = (C[np.clip(owner, 0, None), i] for i in range(4))
    U = np.clip((xx - cx) / rx, -1, 1)
    V = np.clip((yy - cy) / ry, -1, 1)
    lam = U * L[0] + V * L[1] + np.sqrt(np.clip(1 - U * U - V * V, 0.0, 1)) * L[2]
    ys_, xs_ = np.nonzero(S)
    gx, gy = (xs_.min() + xs_.max()) / 2, (ys_.min() + ys_.max()) / 2
    grx, gry = (xs_.max() - xs_.min()) / 2 + 1, (ys_.max() - ys_.min()) / 2 + 1
    Ug, Vg = np.clip((xx - gx) / grx, -1, 1), np.clip((yy - gy) / gry, -1, 1)
    lamg = Ug * L[0] + Vg * L[1] + np.sqrt(np.clip(1 - Ug * Ug - Vg * Vg, 0, 1)) * L[2]
    s = 0.5 * lam + 0.5 * lamg
    tone = np.where(s > 0.80, 4, np.where(s > 0.52, 3, np.where(s > 0.12, 2, 1)))
    if lk['dark']:
        tone = np.maximum(1, tone - lk['dark'])
    # where a clump tucks under the one in front of it (below it), it is in deep shade
    front_below = np.zeros((Hp, Wp), bool)
    gap = max(2, int(round(1.0 * d)))
    for k in range(len(clumps)):
        mk = owner == k
        down = np.zeros_like(mk)
        for j in range(1, gap + 1):
            down[:-j] |= (owner[j:] > k) & S[j:]
        front_below |= mk & down
    tone = np.where(front_below, np.minimum(tone, 1), tone)
    # leaves: staggered cells, each a leaf in the tone under its centre; lower leaves first so a
    # leaf's tip lies over the one below it (the lit tips point down into the shade)
    out_t = np.full((Hp, Wp), -1)
    out_k = np.full((Hp, Wp), -1)
    allow = ndi.binary_dilation(S, iterations=max(1, int(round(0.4 * d))))
    px, py = lw - 1, lh - 2
    cells = []
    for k in range(len(clumps)):
        for j, y in enumerate(np.arange(0, Hp, py)):
            off = (px / 2.0) * (j % 2)
            for x in np.arange(-px, Wp, px) + off:
                yc, xc = int(y + rng.integers(0, 2)), int(x + rng.integers(0, 2))
                if 0 <= yc < Hp and 0 <= xc < Wp and owner[yc, xc] == k and S[yc, xc]:
                    cells.append((k, -yc, xc, rng.random()))
    cells.sort()
    sid = 0
    marks = []
    for (k, nyc, xc, rr_) in cells:
        yc = -nyc
        t = int(tone[yc, xc])
        ys0, xs0 = np.nonzero(leaf)
        Y, X = ys0 + yc - lh // 2, xs0 + xc - lw // 2
        ok = (Y >= 0) & (Y < Hp) & (X >= 0) & (X < Wp)
        Y, X = Y[ok], X[ok]
        keep = allow[Y, X]
        Y, X = Y[keep], X[keep]
        if not len(Y):
            continue
        out_t[Y, X] = t
        out_k[Y, X] = sid
        if 2 <= t <= 4 and rr_ < lk['marks']:
            marks.append((yc + lh // 2 - 1, xc, t, sid))       # a leaf mark at its tip
        elif t <= 2 and rr_ < lk['marks'] * 0.8:
            marks.append((yc - lh // 2 + 1, xc, -(t + 1), sid))  # a shaded leaf's lit edge
        if t == 4 and s[yc, xc] > 0.9 and rr_ > 1 - lk['glint']:
            marks.append((yc - lh // 2 + 1, xc - 1, 5, sid))    # a glint on the lit top
        sid += 1
    painted = out_t >= 0
    for (y, x, t, sid_) in marks:
        if not (0 <= y < Hp and 0 <= x < Wp) or out_k[y, x] != sid_:
            continue
        if t == 5:
            for (dy, dx) in ((0, 0), (0, 1)):
                if 0 <= y + dy < Hp and 0 <= x + dx < Wp and out_k[y + dy, x + dx] == sid_:
                    out_t[y + dy, x + dx] = 5
        elif t < 0:
            for (dy, dx) in ((0, -1), (0, 0), (1, -2)):         # a lit leaf edge in the shade
                if 0 <= y + dy < Hp and 0 <= x + dx < Wp and out_k[y + dy, x + dx] == sid_:
                    out_t[y + dy, x + dx] = -t
        else:
            for (dy, dx) in ((0, 0), (-1, -1), (-1, 1)):          # a small V at the leaf's tip, never a line
                if 0 <= y + dy < Hp and 0 <= x + dx < Wp and out_k[y + dy, x + dx] == sid_:
                    out_t[y + dy, x + dx] = t - 1
    # no lone pixels inside
    for _ in range(2):
        Pp = np.pad(out_t, 1, constant_values=-1)
        nb = np.stack([Pp[:-2, 1:-1], Pp[2:, 1:-1], Pp[1:-1, :-2], Pp[1:-1, 2:]])
        lone = painted & (out_t != nb[0]) & (out_t != nb[1]) & (out_t != nb[2]) & (out_t != nb[3])
        for y, x in zip(*np.nonzero(lone)):
            vals = [q for q in nb[:, y, x] if q >= 0]
            if vals:
                out_t[y, x] = max(set(vals), key=vals.count)
    # the silhouette: lone spurs go, notches fill
    for _ in range(2):
        P4_ = np.pad(painted, 1)
        nbn = P4_[:-2, 1:-1].astype(int) + P4_[2:, 1:-1] + P4_[1:-1, :-2] + P4_[1:-1, 2:]
        spur = painted & (nbn <= 1)
        notch = ~painted & (nbn >= 3)
        if notch.any():
            idx = ndi.distance_transform_edt(~painted, return_distances=False, return_indices=True)
            out_t[notch] = out_t[idx[0][notch], idx[1][notch]]
        painted = (painted & ~spur) | notch
        out_t[~painted] = -1
    painted |= ndi.binary_fill_holes(painted)
    hole = painted & (out_t < 0)
    if hole.any():
        idx = ndi.distance_transform_edt(out_t < 0, return_distances=False, return_indices=True)
        out_t[hole] = out_t[idx[0][hole], idx[1][hole]]
    # a weeping crown's strands hang behind its leaf masses: ribbons lit on their left, a
    # leaf notch every few texels, the tips a tone down
    LAST_MASS['strands'] = None
    if lk['form'] == 'weeping' and strands.any():
        # one ribbon per master column of strands, 2 texels wide with a texel of air between,
        # its leaves in short segments (a darker leaf every few texels, offset per strand)
        mass_bottom = painted.copy()
        rw = max(2, int(round(0.67 * d)))
        seg = max(3, int(round(1.4 * d)))
        sm = np.zeros((Hp, Wp), bool)
        st = np.full((Hp, Wp), 2)
        for x1 in np.nonzero(strands.any(0))[0][::2]:
            col = np.nonzero(strands[:, x1])[0]
            xa = int(pad + x1 * sx)
            ya = int(pad + col.min() * sy) - int(2 * d)
            yb_ = int(pad + (col.max() + 1) * sy) - int(rng.integers(0, max(1, int(d))))
            ph = int(rng.integers(0, seg))
            for y in range(max(0, ya), min(Hp, yb_)):
                for k_ in range(rw):
                    x = xa + k_
                    if 0 <= x < Wp and not mass_bottom[y, x]:
                        sm[y, x] = True
                        t = 2 if k_ == 0 else 1
                        if (y + ph) % seg == 0 and k_ == 0:
                            t = 3                                    # a lit leaf on the strand
                        if y >= yb_ - max(1, int(d / 2)):
                            t = min(t, 2)
                        st[y, x] = t
        out_t[sm] = st[sm]
        painted |= sm
        LAST_MASS['strands'] = sm
    # the bush's foot: the lowest leaves in the under-shade, where it meets the ground
    if lk['form'] == 'bush':
        yb = np.nonzero(painted.any(1))[0].max()
        foot = painted & (yy >= yb - max(1, int(round(0.8 * d))))
        out_t[foot] = np.minimum(out_t[foot], 1)
    out = np.zeros((Hp, Wp, 4), np.uint8)

    def fam_of(t):
        return lk['lit'] if t >= 4 else (lk['shade'] if t <= 1 else lk['fam'])
    for t in range(6):
        m = painted & (out_t == t)
        if m.any():
            out[m, :3] = pk.rgb(fam_of(t), t)
            out[m, 3] = 255
    # the outline, on the silhouette only: the foliage's own darkest green on the lower right,
    # a tone-1 leaf edge on the lit upper left
    edge = painted & ~ndi.binary_erosion(painted)
    Pm = np.pad(painted, 1)
    lit_side = edge & (~Pm[:-2, 1:-1] | ~Pm[1:-1, :-2]) & Pm[2:, 1:-1] & Pm[1:-1, 2:]
    out[edge & ~lit_side, :3] = pk.rgb(lk['shade'], 0)
    for y, x in zip(*np.nonzero(lit_side)):
        out[y, x, :3] = pk.rgb(fam_of(int(out_t[y, x])), int(max(1, min(2, out_t[y, x] - 1))))
    sm_ = LAST_MASS.get('strands')
    if sm_ is not None:                    # the strands keep their own light (no outline)
        for t in range(6):
            m = sm_ & (out_t == t)
            out[m, :3] = pk.rgb(lk['fam'] if t >= 2 else lk['shade'], t)
    # berries or blossoms from the master: a small dot with one lit pixel
    if lk['berries'] and bl.any():
        k_ = max(2, int(round(0.7 * d)))
        for y1, x1 in zip(*np.nonzero(bl)):
            y, x = int(pad + (y1 + 0.5) * sy) - k_ // 2, int(pad + (x1 + 0.5) * sx) - k_ // 2
            if 0 <= y < Hp - k_ and 0 <= x < Wp - k_ and painted[y:y + k_, x:x + k_].all():
                out[y:y + k_, x:x + k_, :3] = pk.rgb(lk['berries'], 3)
                out[y + k_ - 1, x + 1:x + k_, :3] = pk.rgb(lk['berries'], 1)
                out[y, x, :3] = pk.rgb(lk['berries'], 5)
    anc = (pad + W1 * sx / 2.0, pad + H1 * sy)
    LAST_MASS['mass'] = S
    return out, anc, (pad, sx, sy)
