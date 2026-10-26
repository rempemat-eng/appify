"""Ground painters on the soft grid, at Eastward's level of detail (density 3 and up).

Matt, 26 Oct: "this is what i mean with soft grid. edges and paths are a bit block like but they
are not sharp like minecraft"; "most props should probably stay as before (detailled of course)
but the ground and the placement of the props changes"; "eastward is really the example the soft
grid should follow, of course adapted to my pixel density".

softgrid.py lays the plans (whole cells, rounded corners, lumpy outlines). This module paints what
fills them and what happens where they meet, measured on the Eastward references at our density
(an adult 74 art px, Eastward's 54 native: k = 1.37; eastward-edges.md):

    lawn(H, W, seed)                 grass: a calm field, large soft blotches 26 to 57 px, clustered
                                     tufts 5 to 9 px with dark roots and lit tips, flowers in groups
    dirt(cv, m, seed)                packed earth: clods 10 to 15 px lit at their upper left with
                                     broken joints, ruts, pebble clusters, crumbs along the edge
    sunken_edge(cv, m, turf, rng)    grass meeting a lower surface (a path, a bed's soil): the turf
                                     bulges over the north edge in lobes with a dark underside and a
                                     shadow on the dirt; on the south edge the turf's lip is lit and
                                     tufts lean out over the dirt; stones straddle the edge
    ledge(cv, top, face_h, rng)      raised ground: a lit band and an overhanging grass lip, hanging
                                     tufts, the under-lip shade, a face of rounded clods (earth) or
                                     boulders (rock) lit at their upper left, roots, a dark foot
                                     with pebbles, weeds over it, a soft cast shadow on the ground
    log_steps(cv, ...)               steps cut into a ledge: sawn log treads, earth cheeks
    water(cv, m, seed)               still or running water: the north bank's earth face under a
                                     grass lip, a 1 px light waterline, depth bands under the
                                     north bank, lit shallows, ripples 4 to 15 px, glints
    sand(cv, m, seed)                sand with soft patches, wind ripples, shells and pebbles
    shadow(cv, m, core)              a cast shadow or ambient occlusion as ramp steps

Every painter draws palette codes (palette.py), steps along a family's own ramp for light and
shade, and returns the sprites it wants laid over the ground (plants that cross an edge) as
(image, anchor, foot) triples for the caller to sort by foot.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import ctx
from .palette import C, FI, is_fam, sib, step
from .terrain import noise as TN

CROSS = ndi.generate_binary_structure(2, 1)


# ------------------------------------------------------------------------------------------------
# noise and masks
# ------------------------------------------------------------------------------------------------
def nz(H: int, W: int, cell: float, seed: int) -> np.ndarray:
    """Smooth value noise over texels, features about `cell` art px across (0..1)."""
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    return TN.vnoise_hd(xx, yy, cell, seed)


def fbm(H: int, W: int, cell: float, seed: int) -> np.ndarray:
    return (0.55 * nz(H, W, cell, seed) + 0.3 * nz(H, W, cell / 2.7, seed + 1) +
            0.15 * nz(H, W, cell / 7.0, seed + 2))


def patches(H: int, W: int, seed: int, cell: float, share: float) -> np.ndarray:
    """Soft, frayed patches covering about `share` of the area."""
    v = fbm(H, W, cell, seed)
    return v > np.quantile(v, 1 - share)


def blobs(H: int, W: int, seed: int, cell: float, share: float) -> np.ndarray:
    """Rounder soft patches than `patches`: a slow field with one finer octave, so their outline
    wanders in lumps rather than fraying into a camouflage pattern."""
    # smoothed white noise (no value-noise lattice: its level sets run straight along the lattice
    # lines at large cells), with a finer octave for a lumpy outline
    r = np.random.default_rng(seed)
    big = ndi.gaussian_filter(r.random((H, W)), cell / 4.0, mode='wrap')
    fine = ndi.gaussian_filter(r.random((H, W)), cell / 14.0, mode='wrap')
    big = (big - big.mean()) / max(1e-9, big.std())
    fine = (fine - fine.mean()) / max(1e-9, fine.std())
    v = big + 0.25 * fine
    return v > np.quantile(v, 1 - share)


def scallops(n: int, rng, length=(8, 20), depth=(1, 4)) -> np.ndarray:
    """A lumpy profile along n texels: rounded bumps `length` px long, `depth` px deep at their
    middle (a lip's overhang, a bank's turf), each bump a half ellipse."""
    out = np.zeros(n, np.int32)
    x = -int(rng.integers(0, length[1]))
    while x < n:
        L = int(rng.integers(length[0], length[1] + 1))
        d = rng.uniform((depth[0] + depth[1]) / 2, depth[1]) if rng.random() < 0.6 else rng.uniform(depth[0], depth[1])
        u = (np.arange(L) + 0.5) / L * 2 - 1
        prof = np.round(depth[0] + (d - depth[0]) * np.sqrt(np.clip(1 - u * u, 0, 1)) ** 0.7).astype(np.int32)
        a, b = max(0, x), min(n, x + L)
        if a < b:
            out[a:b] = np.maximum(out[a:b], prof[a - x:b - x])
        x += L + int(rng.integers(-2, 4))
    return np.maximum(out, depth[0])


def down(m: np.ndarray, k: int = 1) -> np.ndarray:
    """The mask moved k rows down (what lies k rows above each texel)."""
    o = np.zeros_like(m)
    if k > 0:
        o[k:] = m[:-k]
    elif k < 0:
        o[:k] = m[-k:]
    else:
        o[:] = m
    return o


def right(m: np.ndarray, k: int = 1) -> np.ndarray:
    o = np.zeros_like(m)
    if k > 0:
        o[:, k:] = m[:, :-k]
    elif k < 0:
        o[:, :k] = m[:, -k:]
    else:
        o[:] = m
    return o


def runs_from_top(m: np.ndarray) -> np.ndarray:
    """Per texel of m: 1 + how many texels of m lie directly above it in an unbroken run."""
    H, W = m.shape
    out = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H):
        run = np.where(m[y], run + 1, 0)
        out[y] = run
    return out


def runs_from_bottom(m: np.ndarray) -> np.ndarray:
    return runs_from_top(m[::-1])[::-1]


def grassy(cv: np.ndarray) -> np.ndarray:
    return (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)


def put(cv: np.ndarray, y: int, x: int, code, ok: np.ndarray | None = None) -> bool:
    H, W = cv.shape
    if 0 <= y < H and 0 <= x < W and (ok is None or ok[y, x]):
        cv[y, x] = code
        return True
    return False


def shift(cv: np.ndarray, sel: np.ndarray, d: int) -> None:
    """Step the codes under `sel` d tones along their own ramps (edge tones stay)."""
    sel = sel & (cv >= 0) & (cv % 8 < 6)
    cv[sel] = step(cv[sel], d)


# ------------------------------------------------------------------------------------------------
# tufts: Eastward's grass clumps (5 to 9 px across, 3 to 7 tall at our scale)
# ------------------------------------------------------------------------------------------------
def tuft_shape(rng, size: float = 1.0):
    """A tuft as (dy, dx, dt) texels relative to its root's centre (dy < 0 is up): three to six
    blades fanning out from a dark root, the inner blades taller, lit tips on the west blades,
    one row of shade under the root."""
    nb = int(rng.integers(3, 6 if size >= 1 else 5))
    span = max(2, int(round((nb - 1) * rng.uniform(1.0, 1.6) * size)))
    pts = {}
    for b in range(nb):
        u = b / max(1, nb - 1) * 2 - 1                         # -1 west .. 1 east
        bx = int(round(u * span / 2))
        h = max(2, int(round((4.6 - 2.0 * abs(u)) * size * rng.uniform(0.75, 1.15))))
        lean = int(np.sign(u)) if abs(u) > 0.4 else 0
        for j in range(1, h + 1):
            x = bx + (lean if j > h * 0.55 else 0)
            dt = 1 if (j == h and u <= 0.3) else (0 if j == h else -1)
            pts[(-j, x)] = dt
    for x in range(-span // 2 - 1, span // 2 + 2):
        pts.setdefault((0, x), -1)
    return [(dy, dx, dt) for (dy, dx), dt in pts.items()]


def stamp(cv: np.ndarray, y: int, x: int, shape, base, ok: np.ndarray | None = None) -> None:
    """Draw a relative stamp: base is a code (absolute, stepped by dt) or None (step what is there)."""
    H, W = cv.shape
    for dy, dx, dt in shape:
        Y, X = y + dy, x + dx
        if not (0 <= Y < H and 0 <= X < W) or (ok is not None and not ok[Y, X]):
            continue
        if base is None:
            if cv[Y, X] >= 0 and cv[Y, X] % 8 < 6:
                cv[Y, X] = step(cv[Y, X], dt)
        else:
            cv[Y, X] = step(base, dt)


def flower(cv, y, x, kind, ok=None):
    """A small flower 3 px across: four petals round a centre, a shade texel under it."""
    pet = {'white': C('plaster', 5), 'yellow': C('brass', 5), 'violet': C('dusk', 4), 'pink': C('berry', 4)}[kind]
    mid = C('brass', 4) if kind != 'yellow' else C('lamp', 3)
    for (dy, dx) in ((-1, 0), (0, -1), (0, 1), (1, 0)):
        put(cv, y + dy, x + dx, pet, ok)
    put(cv, y, x, mid, ok)
    if ok is None or (0 <= y + 2 < cv.shape[0] and 0 <= x + 1 < cv.shape[1] and ok[y + 2, x + 1]):
        if 0 <= y + 2 < cv.shape[0] and 0 <= x + 1 < cv.shape[1] and cv[y + 2, x + 1] % 8 < 6:
            cv[y + 2, x + 1] = step(cv[y + 2, x + 1], -1)


# ------------------------------------------------------------------------------------------------
# lawn
# ------------------------------------------------------------------------------------------------
def lawn(H: int, W: int, seed: int, fam: str = 'grass', base: int = 3, lush: float = 1.0,
         flowers: float = 1.0, grain: float = 1.0, mottle: float = 3.0) -> np.ndarray:
    """Eastward's lawn at our density (shots 12, 13, 37): one calm field tone; large soft blotches
    (26 to 57 px) a step darker in the cool sibling and a few lit ones in the warm sibling, their
    edges frayed by blades; tufts in loose clumps, dense where the turf is long and sparse between
    (never a uniform stipple, never a calm stretch large enough to read as a flat fill); short lit
    blades in the sun; flowers in small groups."""
    rng = np.random.default_rng(seed)
    cv = np.full((H, W), C(fam, base), np.int32)
    # blotches (Eastward 13 and 37): damp patches where the turf grows long, in the cool sibling,
    # crowded with darker, taller tufts (their dark comes from the blades, so they have no hard
    # outline and are never a flat shape); dry patches in the warm sibling with sparse tufts; both
    # fade out through a 2 x 2 checker (fades are where dither belongs)
    cool = fam + '_cool' if fam + '_cool' in FI else fam
    warm = fam + '_warm' if fam + '_warm' in FI else fam
    # (the two hues share the field about evenly, so neither reads as a shape on the other)
    dark = blobs(H, W, seed + 1, 70.0, 0.42)
    lit = blobs(H, W, seed + 2, 80.0, 0.2) & ~ndi.binary_dilation(dark, iterations=4)
    yy, xx = np.mgrid[0:H, 0:W]
    chk = ((xx // 2 + yy // 2) % 2) == 0
    cv[dark] = C(cool, base)
    cv[ndi.binary_dilation(dark, iterations=3) & ~dark & chk] = C(cool, base)
    cv[lit] = C(warm, base)
    cv[ndi.binary_dilation(lit, iterations=2) & ~lit & ~dark & chk] = C(warm, base)
    damp = ndi.gaussian_filter(dark.astype(float), 5.0)
    # a low mottle: small clumps (3 to 6 px) of the sibling hue at the same tone, about a third of
    # the field, so the turf is never one flat colour yet stays calm (its value hardly moves)
    mot = fbm(H, W, mottle, seed + 21) > 0.53
    swap = np.where(dark, C(fam, base), np.where(lit, C(fam, base), C(cool, base)))
    sel = mot & ((cv == C(fam, base)) | (cv == C(cool, base)) | (cv == C(warm, base)))
    cv[sel] = swap[sel]
    # a calm grain (Matt, 26 Oct: the lawn too busy): short lit blades a texel or two long, sparse,
    # and a dark blade now and then, so no stretch is one flat tone but nothing reads as stipple
    # (the scale guide: dark marks of 3 px and up, about 34 to a H square in Eastward)
    for _ in range(int(H * W / 95)):
        y, x = int(rng.integers(2, H - 1)), int(rng.integers(1, W - 2))
        cv[y, x] = step(cv[y, x], 1)
        if rng.random() < 0.6:
            cv[y - 1, x + (1 if rng.random() < 0.5 else 0)] = step(cv[y - 1, x], 1)
    for _ in range(int(H * W / 420 * grain)):
        y, x = int(rng.integers(3, H - 1)), int(rng.integers(1, W - 2))
        for j in range(int(rng.integers(2, 4))):
            cv[y - j, x + (j // 2)] = step(cv[y - j, x], -1)
    # tufts in loose clumps (tufts 7 to 14 px across, clumps 15 to 40), the clumps 35 to 60 px
    # apart, more in the damp patches, calm turf between them
    gather = fbm(H, W, 50.0, seed + 3) + 0.5 * damp
    cl = []
    for _ in range(int(H * W / 900)):
        y, x = rng.uniform(-10, H + 10), rng.uniform(-10, W + 10)
        if any((y - a) ** 2 + (x - b) ** 2 < (36 * (1.2 - 0.4 * lush)) ** 2 for a, b in cl):
            continue
        g = gather[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))]
        if rng.random() > np.clip(0.25 + g * 0.9, 0.1, 0.95) * lush:
            continue
        cl.append((y, x))
        dmp = damp[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))]
        for _k in range(int(rng.integers(3, 8))):
            ty = int(round(y + rng.normal(0, 4.5)))
            tx = int(round(x + rng.normal(0, 8.0)))
            shp = tuft_shape(rng, rng.uniform(1.25, 2.1))
            if rng.random() < 0.5 * dmp:
                shp = [(dy, dx, dt - 1 if dt <= 0 else dt) for (dy, dx, dt) in shp]
            stamp(cv, ty, tx, shp, None)
    # no near-black in the turf: the darkest blade is a tone above the ramp's floor
    low = (cv % 8 == 0)
    cv[low] = cv[low] + 1
    # flowers in small groups, few
    if flowers > 0:
        n = int(H * W / 16000 * flowers)
        for _ in range(n):
            cy, cx = int(rng.integers(6, H - 6)), int(rng.integers(6, W - 6))
            kind = ('white', 'white', 'yellow', 'violet')[int(rng.integers(0, 4))]
            for _k in range(int(rng.integers(2, 5))):
                flower(cv, cy + int(rng.normal(0, 3.0)), cx + int(rng.normal(0, 4.5)), kind)
    return cv


# ------------------------------------------------------------------------------------------------
# packed earth
# ------------------------------------------------------------------------------------------------
def dirt(cv: np.ndarray, m: np.ndarray, seed: int, fam: str = 'path', cell: float = 13.0,
         ruts: float | None = None, stones: float = 1.0) -> None:
    """Packed earth (Eastward 13 and 17): clods 10 to 15 px in two close tones of the family and
    its siblings, each lit along its upper left with a joint a tone down along its lower right
    (joints broken, so the ground never reads as a mesh); large trodden and damp patches; two
    ruts (lit on their south lip) at `ruts` px in from the edge; pebbles in small clusters, lit
    at their upper left with a shade under them; dark crumbs near the edge."""
    from scipy.spatial import cKDTree
    H, W = m.shape
    if not m.any():
        return
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W]
    # clods: a jittered lattice of seeds, nearest two
    pts = []
    sy = cell * 0.82
    for j, gy in enumerate(np.arange(-cell, H + cell, sy)):
        for gx in np.arange(-cell + (j % 2) * cell / 2, W + cell, cell):
            pts.append((gx + rng.uniform(-0.32, 0.32) * cell, gy + rng.uniform(-0.3, 0.3) * sy))
    pts = np.array(pts)
    tree = cKDTree(pts)
    d, i = tree.query(np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1), k=2)
    d1, d2 = d[:, 0].reshape(H, W), d[:, 1].reshape(H, W)
    cid = i[:, 0].reshape(H, W)
    h = (cid * 2654435761 % 1000) / 1000.0
    famc = np.full((H, W), FI[fam])
    # big soft patches decide the sibling: dry (warm) and damp (cool); the clods add a little more
    pw = patches(H, W, seed + 5, 40.0, 0.28)
    pc = patches(H, W, seed + 6, 36.0, 0.22) & ~pw
    famc[pw] = FI[fam + '_warm']
    famc[pc] = FI[fam + '_cool']
    famc[(h < 0.12) & ~pc] = FI[fam + '_warm']
    t = np.full((H, W), 3)
    # rounded clods 10 to 15 px (Eastward 12 and 13: cobble-like packed earth): each a calm dome
    # of the body tone, a tone lighter at its upper left rim on the lighter ones; the gaps between
    # them a tone down, soft and round, hidden in stretches by a slow field so the ground never
    # reads as a mesh
    vx, vy = (xx + 0.5 - pts[cid, 0]), (yy + 0.5 - pts[cid, 1])
    rr = cell * 0.5 * (0.86 + 0.22 * nz(H, W, 5.0, seed + 11))
    gap = (d1 > rr) | ((d2 - d1) < 1.3)
    show = nz(H, W, 26.0, seed + 7) > 0.28
    t[gap & show] = 2
    hi = ~gap & ((vx * 0.6 + vy * 0.8) < -0.42 * rr) & (d1 > 0.42 * rr) & (h > 0.4)
    t[hi] = 4
    # ruts: two soft worn bands, a tone down in the damp sibling, lit along their south lip
    if ruts:
        dist = ndi.distance_transform_edt(m)
        wob = (nz(H, W, 16.0, seed + 8) - 0.5) * 4.0
        rut = (np.abs(dist - ruts + wob) < 1.6) & (nz(H, W, 30.0, seed + 9) > 0.42) & m
        famc[rut] = FI[fam + '_cool']
        t[rut & (t >= 3) & (nz(H, W, 4.0, seed + 10) > 0.35)] = 2
        t[down(rut, 1) & ~rut & m & (t >= 3)] = 4
    sel = m & (cv >= 0)
    cv[sel] = (famc * 8 + t)[sel]
    # dry blades blown onto the dirt: short pale curves (Eastward 12)
    ys2, xs2 = np.nonzero(m & ndi.binary_erosion(m, iterations=6))
    for k in rng.permutation(len(ys2))[: len(ys2) // 1800]:
        y, x = int(ys2[k]), int(xs2[k])
        L = int(rng.integers(3, 7))
        d_ = 1 if rng.random() < 0.5 else -1
        for j in range(L):
            put(cv, y - (j * j) // 6, x + d_ * j, C('grass_warm', 4 if j < L - 1 else 5), m)
    # pebbles in small clusters, a larger stone now and then
    inner = m & ndi.binary_erosion(m, iterations=5)
    iy, ix = np.nonzero(inner)
    if len(iy) and stones > 0:
        n_cl = max(1, int(len(iy) / 2600 * stones))
        for _ in range(n_cl):
            k = int(rng.integers(0, len(iy)))
            for _j in range(int(rng.integers(2, 6))):
                py = iy[k] + int(rng.normal(0, 4.0))
                px = ix[k] + int(rng.normal(0, 6.0))
                pebble(cv, py, px, rng, big=rng.random() < 0.15, ok=m)
    # crumbs along the edge, dark, 1 to 2 px
    edge = m & ~ndi.binary_erosion(m, iterations=4)
    ey, ex = np.nonzero(edge)
    for k in rng.permutation(len(ey))[:len(ey) // 24]:
        y, x = int(ey[k]), int(ex[k])
        cv[y, x] = C(fam, 1)
        if rng.random() < 0.5:
            put(cv, y, x + 1, C(fam, 2), m)


def pebble(cv, y, x, rng, big=False, fam='stone', ok=None):
    """A pebble 3 to 4 px (a stone 5 to 7) lit at its upper left, its shade on the ground below."""
    H, W = cv.shape
    w = int(rng.integers(5, 8)) if big else int(rng.integers(3, 5))
    hh = max(2, int(round(w * rng.uniform(0.55, 0.75))))
    fam = fam if rng.random() < 0.6 else (fam + '_warm' if fam + '_warm' in FI else fam)
    for dy in range(-1, hh + 1):
        for dx in range(-1, w + 1):
            Y, X = y + dy, x + dx
            if not (0 <= Y < H and 0 <= X < W) or (ok is not None and not ok[Y, X]):
                continue
            inside = 0 <= dy < hh and 0 <= dx < w and not ((dy in (0, hh - 1)) and (dx in (0, w - 1)))
            if inside:
                u, v = dx / max(1, w - 1), dy / max(1, hh - 1)
                tt = 4 if (u + v < 0.55) else (3 if u + v < 1.25 else 2)
                if big and (dy == hh - 1 or dx == w - 1):
                    tt = 1
                cv[Y, X] = C(fam, tt)
            elif dy == hh and 0 < dx <= w and cv[Y, X] % 8 < 6:
                cv[Y, X] = step(cv[Y, X], -1)


# ------------------------------------------------------------------------------------------------
# grass meeting a lower surface
# ------------------------------------------------------------------------------------------------
def sunken_edge(cv: np.ndarray, m: np.ndarray, turf: np.ndarray, rng, lobes: float = 1.0,
                tufts: float = 1.0, stones: float = 1.0) -> None:
    """Where turf meets a surface a little below it (a path, a bed's soil): Eastward 13's frayed
    edge on the soft grid. On every side the turf creeps over the edge in rounded lobes 0 to 4 px
    deep and 8 to 20 long. North edge (turf above): the lobes' underside a tone down and a 2 px
    shadow on the dirt under them, blades hanging over it here and there. South edge (turf below):
    the turf's first row lit, tufts standing on it lean out over the dirt. West: a texel of shade
    on the dirt; east: the turf's west-facing side lit. Pebbles and stones straddle the edge now
    and then. No outline and no dither at the boundary (eastward-edges.md 5.1)."""
    from .softgrid import clean
    H, W = cv.shape
    s0 = int(rng.integers(0, 99999))
    turf = turf & ~m
    if not turf.any():
        return
    # lobes of turf over the edge, on every side, taking the nearest turf texel's code
    dt = ndi.distance_transform_edt(m)
    dep = np.clip((fbm(H, W, 15.0, s0) - 0.3) * 15.0 * lobes, 0, 5.5)
    near = ndi.binary_dilation(turf, iterations=6)
    lob = m & (dt <= dep) & near
    m2 = clean(m & ~lob, min_area=1.0)
    lob = m & ~m2
    _, (iy, ix) = ndi.distance_transform_edt(~turf, return_indices=True)
    cv[lob] = cv[iy[lob], ix[lob]]
    turf2 = (turf | lob) & ~m2
    # north edge: the lobes' underside, then the shadow on the dirt
    und = turf2 & down(m2, -1)
    shift(cv, und, -1)
    sh1 = m2 & down(turf2, 1)
    sh2 = m2 & down(turf2, 2) & ~sh1
    yy, xx = np.mgrid[0:H, 0:W]
    shift(cv, sh1, -1)
    shift(cv, sh2 & (((xx + yy) % 2) == 0), -1)
    # west turf shades a texel of dirt; east turf's west-facing side is lit
    shift(cv, m2 & right(turf2, 1) & ~sh1, -1)
    shift(cv, turf2 & right(m2, 1) & ~und & ~down(m2, 1), 1)
    # south edge: the turf's first row lit
    s_lip = turf2 & down(m2, 1)
    shift(cv, s_lip, 1)
    # the turf's last texels at the edge a tone down in the cool sibling, broken (Eastward 13: the
    # grass darkens where it thins out over the edge), then tufts on it, lighter than the field,
    # leaning out over the dirt (about one in 10 px of edge)
    fr = turf2 & ndi.binary_dilation(m2, iterations=2) & ~und & ~s_lip & (nz(H, W, 7.0, s0 + 3) > 0.35)
    if tufts > 0:
        shift(cv, fr, -1)
    bnd = turf2 & ndi.binary_dilation(m2, structure=CROSS) & ~und
    ys, xs = np.nonzero(bnd)
    taken = np.zeros_like(m)
    for k in rng.permutation(len(ys))[: int(len(ys) / 6 * tufts)]:
        y, x = int(ys[k]), int(xs[k])
        if taken[max(0, y - 4):y + 5, max(0, x - 5):x + 6].any():
            continue
        taken[y, x] = True
        base = cv[y, x] if cv[y, x] % 8 < 6 else C('grass', 3)
        shp = [(dy, dx, dt_) for (dy, dx, dt_) in tuft_shape(rng, rng.uniform(1.1, 1.7)) if dy < 0]
        stamp(cv, y + 1, x, shp, step(base, 1))
    # blades hanging over the north edge
    ys, xs = np.nonzero(und)
    for k in rng.permutation(len(ys))[: int(len(ys) / 16 * tufts)]:
        y, x = int(ys[k]), int(xs[k])
        base = cv[y - 1, x] if y > 0 and cv[y - 1, x] % 8 < 6 else C('grass', 3)
        for b in range(int(rng.integers(2, 4))):
            L = int(rng.integers(1, 4))
            for j in range(1, L + 1):
                put(cv, y + j, x + 2 * b, step(base, -1 if j == L else 0), m2)
    # stones on the edge, straddling it
    e = m2 & ndi.binary_dilation(turf2, structure=CROSS)
    ys, xs = np.nonzero(e)
    for k in rng.permutation(len(ys))[: int(len(ys) / 90 * stones)]:
        y, x = int(ys[k]), int(xs[k])
        pebble(cv, y - 1, x - 2, rng, big=rng.random() < 0.45)


# ------------------------------------------------------------------------------------------------
# shadows and ambient occlusion
# ------------------------------------------------------------------------------------------------
def shadow(cv: np.ndarray, m: np.ndarray, core: int = 2, rim: int = 2, fade: bool = True) -> None:
    """A cast shadow as ramp steps (house-style 6): its core `core` tones down, its outer `rim` px
    one tone down, and (fade) a further 2 px checker one tone down, the soft edge Eastward's light
    gives at our pixel size."""
    H, W = cv.shape
    inner = ndi.binary_erosion(m, iterations=rim) if rim > 0 else m
    shift(cv, inner, -core)
    shift(cv, m & ~inner, -1)
    if fade:
        yy, xx = np.mgrid[0:H, 0:W]
        chk = ((xx + yy) % 2) == 0
        f = ndi.binary_dilation(m, iterations=2) & ~m & chk
        shift(cv, f, -1)


def contact(cv: np.ndarray, fx: float, fy: float, w: float, depth: float = 0.3, dx: float = 3.0, dy: float = 1.5,
            core: int = 2) -> None:
    """A prop's shadow on the ground: an ellipse under its foot thrown a little east and down,
    as wide as the prop's base."""
    H, W = cv.shape
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    rx, ry = w * 0.55, max(3.0, w * depth * 0.5)
    q = ((xx - fx - dx) / rx) ** 2 + ((yy - fy - dy + ry * 0.35) / ry) ** 2
    # the core under the foot, a tone deeper only close in; the rest a tone, its rim a checker
    shift(cv, q <= 1.0, -1)
    shift(cv, q <= 0.35, -(core - 1))
    shift(cv, (q > 1.0) & (q <= 1.45) & (((xx + yy) % 2) == 0), -1)


# ------------------------------------------------------------------------------------------------
# raised ground: plateaus, ledges and cliffs
# ------------------------------------------------------------------------------------------------
def _earth(earth):
    return (earth, earth + '_warm' if earth + '_warm' in FI else earth, earth + '_cool' if earth + '_cool' in FI else earth)


def clods(cv, region, rng, earth='earth', size=(9, 15), ratio=0.8, gap_t=1, moss=0.0, fams=None, lit_t=4,
          seed=0, stone_share=0.0, spacing=0.9):
    """Rounded lumps packed over `region` (a face): each a dome lit at its upper left, its body
    mid, its lower right shaded, the gaps between them dark; sizes vary, rows offset, so the face
    reads as knobbly earth (Eastward's forest ledges) or boulders (its rock cliffs)."""
    H, W = cv.shape
    e0, ew, ec = fams or _earth(earth)
    cv[region] = C(e0, gap_t)
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    s_mid = (size[0] + size[1]) / 2
    sx, sy = s_mid * spacing, s_mid * ratio * spacing * 0.95
    ys, xs = np.nonzero(region)
    if not len(ys):
        return
    # lumps scattered over the region (a blue-noise draw: each new centre the best of a few
    # candidates), dense enough that only crevices show between them; no rows, no bricks
    n = int(len(ys) / (sx * sy) * 1.15) + 1
    lumps_ = []
    cand = rng.integers(0, len(ys), size=(n, 6))
    for row in cand:
        best, bd = None, -1.0
        for k in row:
            cy, cx = ys[k] + rng.uniform(-0.5, 0.5), xs[k] + rng.uniform(-0.5, 0.5)
            d = min((((cy - a) / sy) ** 2 + ((cx - b) / sx) ** 2 for a, b in lumps_[-400:]), default=9.0)
            if d > bd:
                best, bd = (cy, cx), d
        lumps_.append(best)
    # draw from the back (top) to the front so lower lumps overlap upper ones
    for (cy, cx) in sorted(lumps_):
        rw = rng.uniform(size[0], size[1]) / 2
        rh = rw * ratio * rng.uniform(0.85, 1.1)
        Y0, Y1 = max(0, int(cy - rh - 1)), min(H, int(cy + rh + 2))
        X0, X1 = max(0, int(cx - rw - 1)), min(W, int(cx + rw + 2))
        if Y0 >= Y1 or X0 >= X1:
            continue
        dy = (yy[Y0:Y1, X0:X1] - cy) / rh
        dx = (xx[Y0:Y1, X0:X1] - cx) / rw
        # a rounded, slightly squarish lump
        r = (np.abs(dx) ** 2.4 + np.abs(dy) ** 2.4) ** (1 / 2.4)
        inside = (r <= 1.0) & region[Y0:Y1, X0:X1]
        if not inside.any():
            continue
        lam = -0.62 * dx - 0.78 * dy + 0.35 * (1 - r)
        stone = rng.random() < stone_share
        fl = ('stone', 'stone_warm', 'stone_cool') if stone else (e0, ew, ec)
        t = np.where(lam > 0.62, lit_t, np.where(lam > 0.05, lit_t - 1, np.where(lam > -0.55, lit_t - 2, lit_t - 3)))
        fam = np.where(lam > 0.62, FI[fl[1]], np.where(lam < -0.55, FI[fl[2]], FI[fl[0]]))
        # a rim of the gap tone where the lump meets the one behind it (only at its top and left)
        edge = inside & (r > 0.86) & ((dy < -0.2) | (dx < -0.5))
        sub = cv[Y0:Y1, X0:X1]
        code = fam * 8 + np.clip(t, 0, 5)
        sub[inside] = code[inside]
        sub[edge & (lam < 0.4)] = C(e0, gap_t)
        if moss > 0 and not stone and rng.random() < moss:
            # a moss cap over the dome's crown: its lower edge wavy, lit on top, a dark rim row,
            # a drip or two hanging from it
            ph = rng.uniform(0, 6.28)
            edge_y = -0.28 + 0.18 * np.sin(dx * 5.0 + ph) + 0.1 * np.sin(dx * 11.0 + 2 * ph)
            mm = inside & (dy < edge_y) & (r < 0.97)
            low = mm & ~np.roll(mm, -1, 0)
            sub[mm] = np.where(lam[mm] > 0.8, C('grass', 4), C('grass', 3))
            sub[low] = C('grass_cool', 2)
            hh_, ww_ = sub.shape
            for _d in range(int(rng.integers(0, 3))):
                cand = np.argwhere(low)
                if not len(cand):
                    break
                yy0, xx0 = cand[int(rng.integers(0, len(cand)))]
                for j in range(1, int(rng.integers(2, 5))):
                    if yy0 + j < hh_ and inside[yy0 + j, xx0]:
                        sub[yy0 + j, xx0] = C('grass_cool', 2 if j > 1 else 3)


def ledge(cv: np.ndarray, top: np.ndarray, face_h: int, rng, seed: int = 0, kind: str = 'earth',
          earth: str = 'earth', overhang: float = 1.0, roots: float = 1.0, tufts: float = 1.0,
          shadow_px: int = 10, plants=None) -> tuple:
    """Raised ground under a soft plan `top` (texels), its face `face_h` art px tall, seen from the
    south (eastward-edges.md 2 and 3, Matt's 26 Oct screenshot). Top to bottom: a lit band on the
    top's grass behind the lip; the grass lip hanging over the face 1 to 4 px in lumps, its
    underside a dark row, tufts hanging from it; the under-lip line and shade; the face's body of
    rounded clods (earth) or boulders with streaks above them (rock), roots and vines from the
    rim; a dark foot with pebbles; weeds of the lower ground over the foot; a soft shadow cast on
    the lower ground (core 2 tones, a 1-tone rim and a checker fade). The narrow side faces where
    the top ends west and east: lit on the west, dark on the east, a broken dark line on the
    outside. Returns (face mask, sprites over the edge)."""
    H, W = cv.shape
    items = []
    e0, ew, ec = _earth(earth)
    rock = kind == 'rock'
    yy, xx = np.mgrid[0:H, 0:W]
    # the face: the top extruded down, its foot lumpy
    face = np.zeros_like(top)
    for k in range(1, face_h + 1):
        face[k:] |= top[:-k]
    face &= ~top
    jag = (fbm(H, W, 14.0, seed + 101) - 0.5) * 6.0
    foot_line = runs_from_top(face)
    face = face & ~((foot_line > face_h - 3) & (jag < -1.2))
    extra = np.zeros_like(face)
    for k in range(1, 4):
        extra |= down(face, k)
    face |= extra & (jag > 1.4) & ~top
    from .softgrid import clean
    face = clean(face & ~top, min_area=1.0)
    # the side walls (eastward-edges.md 3.3, Matt 26 Oct 19:42): wherever raised ground ends west
    # or east, its wall shows as a narrow band seen almost edge-on: along the top's west and east
    # edges (over the lower ground, or over the face of a lower part at an inner corner) and past
    # the face's ends, down to its foot. A wall facing west is lit, one facing east in shade.
    sw = 6
    row = np.ones((1, 2 * sw + 1), bool)
    face0 = face.copy()
    near_top = ndi.binary_dilation(top, structure=row) & ~top
    near_face = ndi.binary_dilation(face0, structure=row) & ~top & ~face0
    side = (near_top & ~face0) | (near_top & face0) | near_face
    side = clean(side, min_area=0.5)
    face = face0 & ~side
    raised_for = np.where(face0, 0, 1)          # in a face, only the top makes a wall; elsewhere top and face
    R_all = top | face0
    east_r = np.zeros_like(top)
    west_r = np.zeros_like(top)
    for k in range(1, sw + 2):
        east_r |= np.where(raised_for == 1, right(R_all, -k), right(top, -k))
        west_r |= np.where(raised_for == 1, right(R_all, k), right(top, k))
    west_side = side & east_r & ~west_r          # the raised ground lies east: the wall faces west, lit
    lower = ~(top | face0 | side)
    # the lip: how far the grass hangs over the face, per column, in lumps
    ov = np.broadcast_to(scallops(W, rng, (9, 22), (1, int(round(2 + 5 * overhang))))[None, :], (H, W))
    dtop = runs_from_top(face)
    lip = face & (dtop <= ov)
    # the face's bands
    face_b = face & ~lip
    dt2 = runs_from_top(face_b)
    db2 = runs_from_bottom(face_b)
    if rock:
        u1, u2 = 5, 13                              # under-lip deep shade in two values (E 8 to 11)
        streak = 14
        clods(cv, face_b & (dt2 > u2 + streak - 4), rng, earth, size=(12, 26), ratio=0.8, gap_t=0, moss=0.22,
              lit_t=4, seed=seed, stone_share=0.04, spacing=0.82)
        cv[face_b & (dt2 <= u2 + streak) & (dt2 > u2)] = C(e0, 2)
        # the zone under the shade: small flat stones in the shade, wider than tall, lit only along
        # their top (Eastward 12's streaks read as a layer of flatter rock under the lip)
        zs = face_b & (dt2 <= u2 + streak) & (dt2 > u2)
        tmp = cv.copy()
        clods(tmp, zs, rng, earth, size=(6, 13), ratio=0.5, gap_t=0, lit_t=3, seed=seed + 5, spacing=0.85)
        cv[zs] = tmp[zs]
        cv[face_b & (dt2 <= u2)] = C(ec, 1)
        cv[face_b & (dt2 <= u1)] = C(ec, 0)
        footh = 9
    else:
        clods(cv, face_b, rng, earth, size=(9, 22), ratio=0.76, gap_t=1, moss=0.0, lit_t=4, seed=seed,
              stone_share=0.0, fams=(ew, 'crag_warm', 'crag_cool'), spacing=0.8)
        cv[face_b & (dt2 <= 2)] = C(ec, 0)
        sel = face_b & (dt2 > 2) & (dt2 <= 4)
        shift(cv, sel, -2)
        sel = face_b & (dt2 > 4) & (dt2 <= 6)
        shift(cv, sel, -1)
        footh = 6
    # the foot: dark, the lumps' bottoms in shade, the last rows darkest
    fb = face_b & (db2 <= footh)
    shift(cv, fb, -1)
    shift(cv, face_b & (db2 <= 2), -1)
    # pebbles at the foot
    ys, xs = np.nonzero(face_b & (db2 == 2))
    for k in rng.permutation(len(ys))[: len(ys) // 16]:
        pebble(cv, int(ys[k]) - 1, int(xs[k]), rng, big=rng.random() < 0.3, ok=face | lower)
    # the side walls, 6 px across (eastward-edges.md 3.3, Eastward 12 and 39): next to the top the
    # grass lip turns down over the corner (2 px of the top's own turf, its outer texel a tone
    # down); then the wall: lit in two or three columns when it faces west, a step or two darker
    # when it faces east, seamed across every few px like the face's clods; the outer edge the
    # darkest line of the picture, broken; at its foot the face's clods turn the corner
    if side.any():
        hd = np.zeros((H, W), np.int32)
        src = np.full((H, W), -1, np.int32)
        for k in range(sw + 1, 0, -1):
            for d in (k, -k):
                Rk = np.where(raised_for == 1, right(R_all, d), right(top, d))
                hit = side & Rk
                hd[hit] = k
                sh_ = np.roll(cv, -d, axis=1)
                tk = right(top, d)
                src[hit & tk] = sh_[hit & tk]
        lipc = side & (hd <= 2) & (src >= 0) & grassy(np.where(src >= 0, src, 0))
        cv[lipc] = src[lipc]
        shift(cv, lipc & (hd == 2), -1)
        body = side & ~lipc
        seam = (((yy + (xx // 3)) % 6) == 0) & (nz(H, W, 3.0, seed + 12) > 0.3)
        wl = body & west_side
        el = body & ~west_side
        cv[wl] = np.where(hd[wl] <= 4, C(ew, 4), C(e0, 3))
        cv[wl & (hd == 3)] = C(ew, 3)
        cv[el] = np.where(hd[el] <= 4, C(ec, 2), C(ec, 1))
        cv[el & (hd == 3)] = C(e0, 2)
        cv[body & seam] = step(cv[body & seam], -1)
        cv[body & seam & ~np.roll(seam, 1, 0) & west_side] = step(cv[body & seam & ~np.roll(seam, 1, 0) & west_side], 0)
        outer = side & (hd >= sw) & (nz(H, W, 4.0, seed + 11) > 0.25)
        outer |= side & ndi.binary_dilation(lower, structure=np.ones((1, 3), bool)) & (nz(H, W, 4.0, seed + 11) > 0.25)
        cv[outer] = C(ec, 0)
        # the wall's foot: darker, and the face's clods turning the corner over it
        fb_ = side & (runs_from_bottom(side) <= 4)
        shift(cv, fb_, -1)
        corner = (side | face0) & ndi.binary_dilation(side & (runs_from_bottom(side) <= 9), iterations=4) & \
            (runs_from_bottom(side | face0) <= 9)
        tmp = cv.copy()
        clods(tmp, corner, rng, earth, size=(6, 9), ratio=0.8, gap_t=1, lit_t=4, seed=seed + 3,
              fams=(e0, ew, ec) if rock else (ew, 'crag_warm', 'crag_cool'))
        cv[corner] = tmp[corner]
        shift(cv, corner & ~west_side & side, -1)
    # the grass lip: top's codes continue down over the overhang, its last row dark, tufts hanging
    colfill = np.where(top, cv, -1)
    for y in range(1, H):
        colfill[y] = np.where((colfill[y] < 0) & lip[y], colfill[y - 1], colfill[y])
    lp = lip & (colfill >= 0)
    cv[lp] = colfill[lp]
    under = lp & ~down(lp, -1) & down(face_b | side, -1)
    shift(cv, under, -2)
    shift(cv, lp & down(under, -1), -1)
    # lit band on the top behind the lip (1 to 3 rows, a tone up)
    # the lip runs down the sides too: the top's last column over a wall a tone down, the next lit
    sl = top & ndi.binary_dilation(side, structure=np.ones((1, 3), bool))
    shift(cv, sl & (cv % 8 < 6), -1)
    sl2 = top & ndi.binary_dilation(sl, structure=np.ones((1, 3), bool)) & ~sl
    shift(cv, sl2 & (cv % 8 < 5), 1)
    lit_rows = np.zeros_like(top)
    tl = top & down(lp | face, -1)
    for k in range(1, 4):
        lit_rows |= down(tl, -k) & top & (nz(H, W, 10.0, seed + 13 + k) > 0.25 * k)
    shift(cv, lit_rows & (cv % 8 < 5), 1)
    # tufts on the lip, some hanging down over the face
    ys, xs = np.nonzero(under)
    taken = np.zeros_like(top)
    for k in rng.permutation(len(ys))[: int(len(ys) * 0.3 * tufts)]:
        y, x = int(ys[k]), int(xs[k])
        if taken[max(0, y - 2):y + 3, max(0, x - 6):x + 7].any():
            continue
        taken[y, x] = True
        base = cv[y - 1, x] if cv[y - 1, x] % 8 < 6 else C('grass', 3)
        if rng.random() < 0.55:
            # hanging blades: 2 to 6 px down over the face, the tips a tone down
            for b in range(int(rng.integers(2, 5))):
                bx = x + b * 2 - 2
                L = int(rng.integers(2, 7))
                for j in range(1, L + 1):
                    put(cv, y + j, bx + (1 if j > L * 0.6 and b % 2 else 0),
                        step(base, -1 if j == L else (0 if j < 2 else -1)), face | side)
        else:
            stamp(cv, y, x, [(dy, dx, dt) for (dy, dx, dt) in tuft_shape(rng, rng.uniform(1.0, 1.5)) if dy < 0],
                  step(base, 1))
    # roots (earth) or vines (rock) from under the lip
    ys, xs = np.nonzero(under)
    nroot = int(len(ys) / (70 if not rock else 55) * roots)
    for k in rng.permutation(len(ys))[:nroot]:
        y, x = int(ys[k]) + 1, int(xs[k])
        L = int(rng.integers(8, 20 if not rock else 40))
        for j in range(L):
            Y = y + j
            if not (0 <= Y < H and 0 <= x < W) or not (face_b[Y, x]):
                break
            if rock:
                cv[Y, x] = C('leaf', 2 if j % 4 else 3)
                if j % 5 == 2:
                    put(cv, Y, x + (1 if (j // 5) % 2 else -1), C('leaf', 3), face_b)
                    put(cv, Y - 1, x + (1 if (j // 5) % 2 else -1), C('leaf', 4), face_b)
            else:
                cv[Y, x] = C('timber_cool', 2 if j % 3 else 3)
                put(cv, Y, x + 1, C('timber_cool', 1), face_b)
            if rng.random() < 0.28:
                x += 1 if rng.random() < 0.5 else -1
    # the lower ground: weeds over the foot, the cast shadow
    sh = np.zeros_like(top)
    reach = (shadow_px + (fbm(H, W, 16.0, seed + 21) - 0.5) * 8).astype(int)
    fs = runs_from_top(~(face | side | top))           # rows below the nearest raised texel above
    above_raised = np.zeros_like(top)
    for k in range(1, shadow_px + 6):
        above_raised |= down(face | side, k)
    sh = lower & above_raised & (fs <= reach)
    # east of a side face the shadow is thrown east too
    for k in range(1, 7):
        sh |= right(side & ~west_side, k) & lower & ~top
    core = lower & (fs <= np.maximum(3, reach // 2 - 1)) & above_raised
    shift(cv, sh & ~core, -1)
    shift(cv, core, -2)
    yy2, xx2 = np.mgrid[0:H, 0:W]
    chk = ((xx2 + yy2) % 2) == 0
    fade = lower & ndi.binary_dilation(sh, iterations=2) & ~sh & chk & above_raised
    shift(cv, fade, -1)
    # weeds rooted on the lower ground just under the foot, standing up over it
    footrow = lower & down(face | side, 1)
    ys, xs = np.nonzero(footrow)
    taken = np.zeros_like(top)
    for k in rng.permutation(len(ys))[: int(len(ys) * 0.16 * tufts)]:
        y, x = int(ys[k]), int(xs[k])
        if taken[max(0, y - 2):y + 3, max(0, x - 6):x + 7].any():
            continue
        taken[y, x] = True
        g = cv[min(H - 1, y + 2), x]
        base = g if g % 8 < 6 and (is_fam(np.array(g), 'grass') or is_fam(np.array(g), 'leaf')) else C('grass_cool', 2)
        stamp(cv, y + 1, x, [(dy, dx, dt) for (dy, dx, dt) in tuft_shape(rng, rng.uniform(0.9, 1.4)) if dy < 0 or dt != -1],
              step(base, 1))
    # loose rocks fallen to the foot and plants against it (eastward-edges.md 8: one per 16 to 32
    # cells of edge): the caller lays them over the ground, sorted by their feet
    from . import props as P4
    ys, xs = np.nonzero(footrow)
    placed = []
    gap_ = 90 if rock else 130
    for k in rng.permutation(len(ys)):
        y, x = int(ys[k]), int(xs[k])
        if any(abs(x - a) < gap_ for a in placed):
            continue
        placed.append(x)
        w_ = rng.uniform(7, 13) if rock else rng.uniform(4, 7)
        img, anc, _a = P4.boulder4(ctx.D, w_, w_ * rng.uniform(0.55, 0.75), seed=int(rng.integers(0, 10 ** 6)),
                                   fam='stone',
                                   moss='top' if rng.random() < 0.5 else None)
        items.append((img, anc, (x + int(rng.integers(-4, 5)), y + int(rng.integers(2, 6)))))
    return face | side, items, lp


def log_steps(cv: np.ndarray, x0: int, x1: int, y_top: int, y_foot: int, n: int, rng, wood: str = 'timber',
              earth: str = 'earth') -> None:
    """Steps cut into a ledge's face, as in Matt's 26 Oct screenshot: `n` sawn log treads from the
    rim down to the foot, the head flush with the top. Each log's top is lit with a pale front
    edge and grain, darker towards its back; its sawn ends show as lit rings at the cheeks; the
    riser under it is the earth in deep shade. Earth cheeks either side carry the face's clods
    down beside the flight, the west lit, the east in shade."""
    H, W = cv.shape
    e0, ew, ec = _earth(earth)
    cheek = 7
    pitch = (y_foot - y_top) / n
    reg = np.zeros((H, W), bool)
    reg[y_top:y_foot, x0:x0 + cheek] = True
    clods(cv, reg, rng, earth, size=(6, 10), ratio=0.85, gap_t=1, seed=7)
    reg2 = np.zeros((H, W), bool)
    reg2[y_top:y_foot, x1 - cheek:x1] = True
    clods(cv, reg2, rng, earth, size=(6, 10), ratio=0.85, gap_t=1, seed=8)
    shift(cv, reg2, -1)
    a, b = x0 + cheek, x1 - cheek
    for k in range(n):
        ya = int(round(y_top + k * pitch))
        yb = int(round(y_top + (k + 1) * pitch))
        tread = max(5, int(round(pitch * 0.66)))
        cv[ya:yb, a:b] = C(ec, 0)                                       # the riser in shade
        cv[ya + tread:yb, a:b] = C(ec, 0)
        if yb - (ya + tread) > 2:
            cv[ya + tread + 1:yb, a:b] = C(e0, 1)
        for j in range(tread):
            y = ya + j
            tt = 2 if j == 0 else (3 if j < tread * 0.45 else (4 if j < tread - 1 else 5))
            cv[y, a:b] = C(wood, tt)
        cv[ya + tread - 1, a:b] = C(wood + '_warm' if wood + '_warm' in FI else wood, 4)
        cv[ya + tread, a:b] = C(wood, 1)                               # the log's round underside
        # grain and knots, lighter blotches where it is worn
        for gx in range(a + 2, b - 3, 5):
            gy = ya + int(rng.integers(1, max(2, tread - 2)))
            L = int(rng.integers(3, 9))
            cv[gy, gx:min(b - 2, gx + L)] = C(wood, 2)
            if rng.random() < 0.3:
                cv[gy - 1, gx + 1:min(b - 2, gx + 3)] = C(wood, 4)
        # the sawn ends: rings, lit on the west end
        for (ex, lit) in ((a, True), (b - 3, False)):
            for j in range(tread + 1):
                for q in range(3):
                    put(cv, ya + j, ex + q, C('timber_warm' if lit else wood, (4 if q == 1 and 0 < j < tread else 3) if lit else 2))
            put(cv, ya + tread // 2, ex + 1, C(wood, 2 if lit else 1))
    # earth spilled on the lowest tread and the path's start
    cv[y_foot - 1, a:b] = np.where(rng.random(b - a) < 0.3, C(e0, 3), cv[y_foot - 1, a:b])


# ------------------------------------------------------------------------------------------------
# water
# ------------------------------------------------------------------------------------------------
def water(cv: np.ndarray, m: np.ndarray, seed: int, bank_h: int = 7, flow=None, lilies: float = 0.0,
          stones: float = 1.0, fam: str = 'water', reeds: float = 1.0) -> list:
    """Water on a soft plan (eastward-edges.md 5.3, shots 13 and 37). The north bank: the grass
    lip hanging 1 to 3 px over an earth face `bank_h` px tall of small clods, darkest where it
    meets the water; then a 1 px very light waterline; the water under it dark in a band 4 to 14
    px that steps back to the body in three steps (the bank's shade). The south, west and east
    shores: the turf's lip lit, a texel of wet earth, a light waterline and lit shallows 2 to 5 px.
    The body one tone with large soft patches a step lighter (the sky), ripple lines 4 to 15 px
    (a lit line over a darker texel) along the flow, a few glints. Stones on the bank, lilies on
    still water. Returns sprites to lay over (stones on the bank)."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    items = []
    if not m.any():
        return items
    land = ~m
    turf = grassy(cv) & land
    # the north bank: the water's first rows under land become the bank's face
    rt = runs_from_top(m)
    bh = np.clip(bank_h + (fbm(H, W, 15.0, seed + 1) - 0.5) * 4, 3, bank_h + 3).astype(int)
    bank = m & (rt <= bh)
    from .softgrid import clean
    bank = m & ~clean(m & ~bank, min_area=1.0)
    wat = m & ~bank
    # the water's body
    d_in = ndi.distance_transform_edt(wat)
    t = np.full((H, W), 2)
    yy_, xx_ = np.mgrid[0:H, 0:W]
    # the body: one calm tone; a faint lighter sheen in broad soft patches (a hue step to the
    # warm sibling, the sky's reflection), never dark holes
    famw = np.full((H, W), FI[fam])
    sky = blobs(H, W, seed + 2, 70.0, 0.25) & (d_in > 10)
    famw[sky] = FI[fam + '_warm'] if fam + '_warm' in FI else FI[fam]
    # deeper water in the middle of wide water: a tone down, its edge a checker (a depth fade)
    yy0, xx0 = np.mgrid[0:H, 0:W]
    dp = d_in > 22 + 6 * nz(H, W, 30.0, seed + 13)
    t[dp] = 1
    t[(d_in > 18 + 6 * nz(H, W, 30.0, seed + 13)) & ~dp & ((xx0 + yy0) % 2 == 0)] = 1
    # shade under the north bank: the rows below the bank, in three steps back to the body
    rb = runs_from_top(wat)
    band = (7 + (fbm(H, W, 14.0, seed + 4) - 0.5) * 6).astype(int)
    t[wat & (rb <= band)] = 1
    t[wat & (rb <= 3)] = 0
    t[wat & (rb > band) & (rb <= band + 5) & ((xx_ + yy_) % 2 == 0)] = 2
    under_n = wat & (rb <= band + 5)
    # lit shallows along the other shores: 2 to 6 px a tone up, the edge a tone more
    sh = wat & (d_in <= 2 + 4 * nz(H, W, 18.0, seed + 6)) & ~under_n
    t[sh] = 3
    t[wat & (d_in <= 1.5) & ~under_n] = 4
    # ripples: short lit lines along the flow, a darker texel below; gathered, not even
    if isinstance(flow, str):
        # along the channel: across the gradient of the distance to the banks
        dsm = ndi.gaussian_filter(ndi.distance_transform_edt(m), 6.0)
        gy_, gx_ = np.gradient(dsm)
        fx, fy = np.abs(gy_) + 1e-6, np.abs(gx_)
    else:
        fx, fy = flow if flow is not None else (1.0, 0.0)
    ys, xs = np.nonzero(wat & (d_in > 4))
    nr = int(len(ys) / 650)
    dens = nz(H, W, 26.0, seed + 5)
    for k in rng.permutation(len(ys))[: nr * 3]:
        if nr <= 0:
            break
        y, x = int(ys[k]), int(xs[k])
        if dens[y, x] < 0.45 or rng.random() > dens[y, x]:
            continue
        nr -= 1
        L = int(rng.integers(4, 13))
        vertical = abs(fy) > abs(fx) if np.ndim(fx) == 0 else abs(fy[y, x]) > abs(fx[y, x])
        for j in range(L):
            Y, X = (y + j, x) if vertical else (y, x + j)
            if 0 <= Y < H and 0 <= X < W and wat[Y, X] and d_in[Y, X] > 2:
                t[Y, X] = min(5, t[Y, X] + 2) if 0 < j < L - 1 else min(5, t[Y, X] + 1)
                Y2, X2 = (Y, X + 1) if vertical else (Y + 1, X)
                if 0 <= Y2 < H and 0 <= X2 < W and wat[Y2, X2]:
                    t[Y2, X2] = max(0, t[Y2, X2] - 1)
    # glints
    for k in rng.permutation(len(ys))[: len(ys) // 4000 + 1]:
        y, x = int(ys[k]), int(xs[k])
        for (dy, dx) in ((0, 0), (0, 1), (-1, 0), (0, -1), (1, 0)):
            if wat[min(H - 1, y + dy), min(W - 1, x + dx)]:
                t[min(H - 1, y + dy), min(W - 1, x + dx)] = 5 if (dy, dx) == (0, 0) else 4
    out = cv.copy()
    out[wat] = (famw * 8 + t)[wat]
    # the light waterline at the foot of the north bank
    wl = wat & down(bank, 1)
    out[wl] = C(fam, 5)
    # the bank face: small clods of earth, darkest at the bottom and wet
    rngc = np.random.default_rng(seed + 9)
    tmp = out.copy()
    clods(tmp, bank, rngc, 'earth', size=(5, 9), ratio=0.8, gap_t=1, lit_t=3, seed=seed)
    out[bank] = tmp[bank]
    rbb = runs_from_bottom(bank)
    out[bank & (rbb <= 2)] = C('earth_cool', 0)
    sel = bank & (rbb > 2) & (rbb <= 4)
    out[sel] = step(out[sel], -1)
    # the grass lip over the bank's top
    colfill = np.where(land, out, -1)
    ov = np.clip((fbm(H, W, 12.0, seed + 12) - 0.3) * 6 + 1, 1, 3).astype(int)
    lipm = bank & (runs_from_top(bank) <= ov)
    for y in range(1, H):
        colfill[y] = np.where((colfill[y] < 0) & lipm[y], colfill[y - 1], colfill[y])
    lp = lipm & (colfill >= 0) & grassy(np.where(colfill >= 0, colfill, 0))
    out[lp] = colfill[lp]
    und = lp & down(bank & ~lp, -1)
    out[und] = step(out[und], -2)
    # the other shores: the turf's lip lit
    shore = land & ndi.binary_dilation(wat, structure=CROSS) & ~ndi.binary_dilation(bank, iterations=2)
    out[shore & turf] = step(out[shore & turf], 1)
    # the east and west banks (Matt, 26 Oct 19:42): a narrow wall of earth 3 px seen almost
    # edge-on, like a ledge's side: on the west shore it faces east and lies in shade, on the east
    # shore it faces west and is lit; a light waterline along its foot. Under the north bank the
    # bank face itself turns the corner, so the bend joins without a seam.
    westl = np.zeros((H, W), bool)
    eastl = np.zeros((H, W), bool)
    for k in range(1, 6):
        westl |= right(land, k)
        eastl |= right(land, -k)
    rbw = runs_from_top(wat)
    sideb = wat & (westl ^ eastl) & (rbw > 3)
    vert = ndi.binary_opening(sideb, structure=np.ones((5, 1), bool))      # only along north-south runs
    wb = vert & westl
    eb = vert & eastl
    out[wb] = C('earth', 2)
    out[wb & ~right(land, 4) & right(land, 3)] = C('earth', 1)
    out[wb & right(land, 1)] = step(np.where(right(land, 1), np.roll(cv, 1, axis=1), C('grass', 2)), -1)[wb & right(land, 1)]
    out[eb] = C('earth_warm', 3)
    out[eb & right(land, -2)] = C('earth_warm', 4)
    out[eb & right(land, -1)] = np.roll(cv, -1, axis=1)[eb & right(land, -1)]
    seam_ = (((np.mgrid[0:H, 0:W][0]) % 5) == 0)
    out[(wb | eb) & seam_ & ~right(land, 1) & ~right(land, -1)] = step(out[(wb | eb) & seam_ & ~right(land, 1) & ~right(land, -1)], -1)
    for b_, d_ in ((wb, 1), (eb, -1)):
        wl_ = wat & ~vert & right(b_, d_)
        out[wl_] = C(fam, 5)
    cv[:] = out
    # the turf hangs over the other shores in rounded tongues (8 to 16 px, 2 to 5 deep), their
    # underside a tone down and their shade on the water, and reed clumps stand at the waterline
    # (solid clumps: their blades rise over the turf, not over the water, so the waterline stays
    # one smooth line; Matt, 26 Oct: no bare banks)
    sy_, sx_ = np.nonzero(shore & turf)
    placed = []
    for k in rng.permutation(len(sy_)):
        y, x = int(sy_[k]), int(sx_[k])
        if any((x - a) ** 2 + (y - b) ** 2 < 26 ** 2 for a, b in placed):
            continue
        placed.append((x, y))
        # the direction into the water
        dyw = int(wat[min(H - 1, y + 2), x]) - int(wat[max(0, y - 2), x])
        dxw = int(wat[y, min(W - 1, x + 2)]) - int(wat[y, max(0, x - 2)])
        if dyw == 0 and dxw == 0:
            continue
        hw = rng.uniform(4, 8)
        dep = rng.uniform(2.5, 5.0)
        base = cv[y - 2 * dyw if 0 <= y - 2 * dyw < H else y, x - 2 * dxw if 0 <= x - 2 * dxw < W else x]
        base = base if grassy(np.array([[base]]))[0, 0] else C('grass', 3)
        lob = np.zeros((H, W), bool)
        for t_ in np.arange(-hw, hw + 0.5, 0.5):
            for d_ in np.arange(0, dep * np.sqrt(max(0.0, 1 - (t_ / hw) ** 2)) + 0.01, 0.5):
                Y = int(round(y + dyw * d_ + dxw * t_ * 0 + (t_ if dxw else 0)))
                X = int(round(x + dxw * d_ + (t_ if dyw else 0)))
                if 0 <= Y < H and 0 <= X < W:
                    lob[Y, X] = True
        lob = ndi.binary_closing(lob, structure=np.ones((3, 3)))
        lob &= wat & ~under_n
        if lob.sum() < 12:
            continue
        cv[lob] = base
        cv[lob & ~ndi.binary_erosion(lob | ~wat, structure=CROSS)] = step(base, -1)
        shd = wat & ~lob & ndi.binary_dilation(lob, iterations=2) & ~ndi.binary_dilation(lob, iterations=0)
        cv[shd & (cv % 8 > 0)] = cv[shd & (cv % 8 > 0)] - 1
        if rng.random() < 0.45 * reeds:
            reed_clump(cv, y, x, rng, turf_ok=~wat | ndi.binary_erosion(lob, structure=CROSS))
    # stones on the bank and the shore, straddling the waterline, a dark ring on the water
    from . import props as P4
    ey, ex = np.nonzero((bank & (runs_from_bottom(bank) <= 3)) | shore)
    placed = []
    for k in rng.permutation(len(ey)):
        if len(placed) >= int(len(ey) / 260 * stones) + 1:
            break
        y, x = int(ey[k]), int(ex[k])
        if any((x - a) ** 2 + (y - b) ** 2 < 30 ** 2 for a, b in placed):
            continue
        placed.append((x, y))
        n = int(rng.integers(1, 4))
        for j in range(n):
            w_ = rng.uniform(6.0, 11.0) if j == 0 else rng.uniform(3.5, 6.0)
            img, anc, _a = P4.boulder4(ctx.D, w_, w_ * rng.uniform(0.55, 0.7), seed=int(rng.integers(0, 10 ** 6)),
                                       moss='top' if rng.random() < 0.4 else None)
            fx_, fy_ = x + (j * 9 - 4 if j else 0) + rng.integers(-2, 3), y + 3 + int(rng.integers(-1, 2))
            items.append((img, anc, (fx_, fy_)))
            # its shade on the water
            yy, xx = np.mgrid[0:H, 0:W]
            ring = (((xx - fx_ - 2) / (w_ * 1.7 + 2)) ** 2 + ((yy - fy_ - 1) / 3.0) ** 2 <= 1) & wat
            cv[ring] = C(fam, 1)
    # reeds and rushes standing in the shallows a few px off the shore (one clump in 40 to 70 px)
    dsh = ndi.distance_transform_edt(m)
    ey, ex = np.nonzero(wat & (dsh >= 6) & (dsh <= 8) & ~under_n)
    placed = []
    for k in rng.permutation(len(ey)):
        if len(placed) >= int(len(ey) / 55 * reeds) + (1 if reeds > 0 else 0):
            break
        y, x = int(ey[k]), int(ex[k])
        if any((x - a) ** 2 + (y - b) ** 2 < 40 ** 2 for a, b in placed):
            continue
        placed.append((x, y))
        rush(cv, y, x, rng, ok=wat & (dsh >= 3))
    # lilies on still water
    if lilies > 0:
        ys, xs = np.nonzero(wat & (d_in > 8))
        for k in rng.permutation(len(ys))[: int(len(ys) / 1600 * lilies)]:
            lily(cv, int(ys[k]), int(xs[k]), rng, wat)
    return items


def reed_clump(cv, y, x, rng, turf_ok=None):
    """A clump of reeds at the waterline: a solid fan of blades 10 to 18 px tall in the leaf ramp,
    lit on the west, dark at the foot, some with a brown head; blades rise over the land side."""
    H, W = cv.shape
    n = int(rng.integers(5, 9))
    for b in range(n):
        u = b / max(1, n - 1) * 2 - 1
        bx = x + int(round(u * 4))
        L = int(round((18 - 6 * abs(u)) * rng.uniform(0.7, 1.0)))
        for j in range(L):
            X = bx + int(round(u * j * 0.25))
            Y = y - j
            tt = 4 if (u < 0 and j > 2) else (3 if j > 2 else 2)
            if j == L - 1:
                tt = 5 if u < 0.3 else 4
            put(cv, Y, X, C('leaf', tt), turf_ok)
            if j < 4:
                put(cv, Y, X + 1, C('leaf', 2), turf_ok)
        if rng.random() < 0.3:
            X = bx + int(round(u * L * 0.25))
            for j in range(3):
                put(cv, y - L - j, X, C('timber', 3 if j else 2), turf_ok)


def rush(cv, y, x, rng, n=None, ok=None):
    """A clump of rushes 8 to 16 px tall: straight blades in the leaf ramp, lit on their west
    side and tip, some with a brown seed head; a shade texel at each foot."""
    H, W = cv.shape
    n = n or int(rng.integers(4, 8))
    for b in range(n):
        bx = x + int(round((b - n / 2) * rng.uniform(1.2, 2.0)))
        L = int(rng.integers(8, 17))
        lean = rng.uniform(-0.25, 0.25)
        for j in range(L):
            X = bx + int(round(lean * j))
            tt = 4 if j > L - 3 else (3 if b % 2 == 0 else 2)
            put(cv, y - j, X, C('leaf', tt) if j < L - 1 else C('leaf_warm', 4), ok)
        if rng.random() < 0.3:
            X = bx + int(round(lean * L))
            for j in range(3):
                put(cv, y - L - j + 1, X, C('timber', 3 if j else 2), ok)
                put(cv, y - L - j + 1, X + 1, C('timber', 2), ok)
        put(cv, y + 1, bx, C('water', 1), ok)


def lily(cv, y, x, rng, ok):
    """A lily pad: a lit disc with a notch, a dark rim on the water below it; a flower on some."""
    H, W = cv.shape
    r = rng.uniform(3.0, 5.0)
    a0 = rng.uniform(0, 6.28)
    for dy in range(-6, 7):
        for dx in range(-7, 8):
            Y, X = y + dy, x + dx
            if not (0 <= Y < H and 0 <= X < W and ok[Y, X]):
                continue
            q = (dx / r) ** 2 + (dy / (r * 0.7)) ** 2
            ang = (np.arctan2(dy, dx) - a0) % 6.28
            if q <= 1 and not (ang < 0.45 and q > 0.1):
                cv[Y, X] = C('leaf', 4 if dx + dy < -r * 0.4 else (3 if q < 0.7 else 2))
            elif q <= 1.5 and dy > 0:
                cv[Y, X] = C('water', 1)
    if rng.random() < 0.35:
        flower(cv, y - 1, x, 'pink')


# ------------------------------------------------------------------------------------------------
# sand
# ------------------------------------------------------------------------------------------------
def sand(cv: np.ndarray, m: np.ndarray, seed: int, fam: str = 'sand') -> None:
    """Sand (Eastward 39): a pale calm field with large soft patches of its siblings (hue steps, no
    value jumps), wind ripples gathered in a few drifts (gentle arcs 6 to 14 px, a shade line under
    a lit one, parallel, 4 to 6 px apart), shells and pebbles here and there."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    t = np.full((H, W), 3)
    f = np.full((H, W), FI[fam])
    f[blobs(H, W, seed + 1, 60.0, 0.25)] = FI[fam + '_warm']
    f[blobs(H, W, seed + 2, 50.0, 0.15) & (f == FI[fam])] = FI[fam + '_cool']
    yy, xx = np.mgrid[0:H, 0:W]
    lit = blobs(H, W, seed + 3, 30.0, 0.08)
    t[lit] = 4
    t[ndi.binary_dilation(lit, iterations=2) & ~lit & (((xx // 2 + yy // 2) % 2) == 0)] = 4
    sel = m & (cv >= 0)
    cv[sel] = (f * 8 + t)[sel]
    # ripple drifts: inside a few soft areas, rows of arcs
    drift = blobs(H, W, seed + 4, 70.0, 0.35) & ndi.binary_erosion(m, iterations=5)
    ph = nz(H, W, 40.0, seed + 5) * 6.0
    for y in range(2, H - 2, 6):
        x = int(rng.integers(0, 10))
        while x < W:
            L = int(rng.integers(10, 22))
            if drift[y, min(W - 1, x)] and rng.random() < 0.75:
                for j in range(L):
                    Y = y - int(round(1.4 * np.sin(np.pi * j / max(1, L - 1)) + 0.8 * np.sin(ph[y, min(W - 1, x)] + j * 0.4)))
                    X = x + j
                    if 1 <= Y < H - 1 and 0 <= X < W and drift[Y, X] and m[Y, X]:
                        cv[Y, X] = step(cv[Y, X], -1)
                        if 0 < j < L - 1:
                            cv[Y - 1, X] = step(cv[Y - 1, X], 1)
            x += L + int(rng.integers(4, 12))
    ys, xs = np.nonzero(m & ndi.binary_erosion(m, iterations=4))
    for k in rng.permutation(len(ys))[: len(ys) // 1600]:
        y, x = int(ys[k]), int(xs[k])
        if rng.random() < 0.5:
            pebble(cv, y, x, rng, ok=m)
        else:                                                   # a shell: a pale fan, shade under
            for (dy, dx, tt) in ((0, 1, 5), (1, 0, 5), (1, 1, 5), (1, 2, 4), (2, 1, 3)):
                put(cv, y + dy, x + dx, C('plaster', tt), m)
            put(cv, y + 3, x + 1, step(cv[min(H - 1, y + 3), x + 1], -1), m)
            put(cv, y + 2, x + 2, step(cv[min(H - 1, y + 2), x + 2], -1), m)


# ------------------------------------------------------------------------------------------------
# garden beds (Eastward 12 and 13)
# ------------------------------------------------------------------------------------------------
def leaf(cv, cy, cx, ang, L, Wd, fam='leaf', lit_t=4, ok=None):
    """A leaf: an ellipse `L` long and `Wd` wide pointing along `ang`, lit on its upper left half,
    a dark rim on its lower right, a pale midrib."""
    H, W = cv.shape
    ca, sa = np.cos(ang), np.sin(ang)
    R = int(L) + 2
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            q = ((u - L / 2) / (L / 2)) ** 2 + (v / (Wd / 2)) ** 2
            Y, X = cy + dy, cx + dx
            if q > 1 or not (0 <= Y < H and 0 <= X < W) or (ok is not None and not ok[Y, X]):
                continue
            litside = (dx * 0.7 + dy * 0.7) < 0 or v < 0
            if q > 0.62:
                tt = lit_t - 1 if litside else lit_t - 3
            else:
                tt = lit_t if litside else lit_t - 1
            if abs(v) < 0.6 and 0.25 * L < u < 0.8 * L:
                tt = min(5, lit_t + 1) if litside else lit_t - 1
            cv[Y, X] = C(fam, max(0, tt))


def crop(cv, cy, cx, rng, kind, ok=None):
    """A crop in its plot, at a growth stage: 'seedling' (two or three small leaves), 'young' (a
    small rosette), 'lettuce' (a loose rosette of ruffled leaves), 'cabbage' (a pale head in a
    ring of dark outer leaves), 'carrot' (feathery fronds over an orange shoulder), 'onion'
    (upright blades over a pale bulb) or 'flowering' (a rosette with a flower stalk). Every leaf
    is lit on its upper left with a pale midrib and a dark rim; the crop's shade lies on the soil
    to its lower right."""
    H, W = cv.shape
    # its shade on the soil first
    r_sh = {'seedling': 3, 'young': 6, 'lettuce': 9, 'cabbage': 10, 'carrot': 7, 'onion': 5, 'flowering': 8}[kind]
    for dy in range(-2, 4):
        for dx in range(-r_sh, r_sh + 3):
            if ((dx - 2) / (r_sh + 1)) ** 2 + ((dy - 1) / 3.0) ** 2 <= 1:
                Y, X = cy + dy + 2, cx + dx
                if 0 <= Y < H and 0 <= X < W and (ok is None or ok[Y, X]) and cv[Y, X] % 8 < 6:
                    cv[Y, X] = step(cv[Y, X], -1)
    if kind == 'seedling':
        for a in (-2.5, -0.65, -1.57)[:int(rng.integers(2, 4))]:
            leaf(cv, cy, cx, a, 5.5, 3.5, 'grass', 4, ok)
        put(cv, cy + 1, cx, C('grass', 2), ok)
    elif kind == 'young':
        a0 = rng.uniform(0, 0.8)
        for k in range(4):
            leaf(cv, cy, cx, a0 + k * 1.571, 7.0, 5.0, 'leaf', 4, ok)
        put(cv, cy, cx, C('leaf', 2), ok)
    elif kind == 'lettuce':
        a0 = rng.uniform(0, 1.0)
        for k in range(7):
            leaf(cv, cy + 1, cx, a0 + k * 0.9, 10.0, 7.5, 'grass', 4, ok)
        for k in range(4):
            leaf(cv, cy, cx, a0 + 0.4 + k * 1.571, 6.0, 5.0, 'grass', 5, ok)
        # ruffled rims: a lit texel here and there along the outer leaves
        for _ in range(8):
            a = rng.uniform(0, 6.28)
            put(cv, cy + int(round(7 * np.sin(a) * 0.8)), cx + int(round(8 * np.cos(a))), C('grass', 5), ok)
    elif kind == 'cabbage':
        for k in range(7):
            leaf(cv, cy + 2, cx, k * 0.9 + 0.2, 11.0, 7.5, 'leaf_cool', 4, ok)
        for dy in range(-5, 5):
            for dx in range(-6, 7):
                q = (dx / 6.2) ** 2 + (dy / 4.8) ** 2
                if q <= 1:
                    lam = -0.6 * dx / 6 - 0.8 * dy / 5
                    tt = 5 if lam > 0.55 else (4 if lam > -0.1 else (3 if lam > -0.6 else 2))
                    put(cv, cy + dy, cx + dx, C('grass_cool', tt), ok)
        for dx in (-3, 0, 3):                                    # the veins of the wrapping leaves
            put(cv, cy - 2, cx + dx, C('grass_cool', 3), ok)
            put(cv, cy - 1, cx + dx + (1 if dx > 0 else -1 if dx < 0 else 0), C('grass_cool', 3), ok)
    elif kind == 'carrot':
        for k in range(6):
            ang = -1.571 + (k - 2.5) * 0.36 + rng.uniform(-0.1, 0.1)
            L = rng.uniform(9, 14)
            for j in range(int(L)):                                # a frond: a stem with leaflets
                X = cx + int(round(np.cos(ang) * j))
                Y = cy + int(round(np.sin(ang) * j))
                put(cv, Y, X, C('grass', 3 if j < L * 0.6 else 4), ok)
                if j % 3 == 2:
                    put(cv, Y, X - 1, C('grass', 4), ok)
                    put(cv, Y, X + 1, C('grass', 2), ok)
        for dx in range(-3, 4):
            put(cv, cy + 1, cx + dx, C('clay', 5 if dx < -1 else (4 if dx < 2 else 3)), ok)
        for dx in range(-2, 3):
            put(cv, cy + 2, cx + dx, C('clay', 3 if dx < 1 else 2), ok)
    elif kind == 'onion':
        for dx in (-3, -1, 1, 3):
            L = int(rng.integers(8, 13))
            for j in range(L):
                put(cv, cy - j, cx + dx + (j // 5) * (1 if dx > 0 else -1), C('leaf_cool', 4 if dx < 0 else 3), ok)
        for dx in range(-3, 4):
            put(cv, cy + 1, cx + dx, C('plaster', 5 if dx < 0 else 4), ok)
        put(cv, cy + 2, cx - 1, C('plaster', 3), ok)
        put(cv, cy + 2, cx, C('plaster', 3), ok)
    else:                                                       # flowering: a rosette and a stalk
        for k in range(5):
            leaf(cv, cy + 1, cx, k * 1.257, 8.0, 5.5, 'leaf', 4, ok)
        for j in range(1, 12):
            put(cv, cy - j, cx, C('leaf', 3), ok)
        flower(cv, cy - 12, cx, 'yellow', ok)
        flower(cv, cy - 8, cx + 2, 'yellow', ok)


def bed(cv, frame, rng, cells_in, cell, rows=('cabbage', 'lettuce', 'carrot', 'onion'),
        wood='earth', earth='earth_warm'):
    """A raised garden bed (Eastward 12 and 13, in our own timber): a frame of boards round it,
    their grain running along them with knots, joints and nail heads, square corner posts with
    their end grain on top, a low front face of boards on the south and its shade on the turf;
    inside, the soil a little lower, worked into a rounded mound per cell ringed by a furrow, clods
    and crumbs on it; a crop per plot by rows at mixed growth stages (some freshly sown, one dug
    over), a weed or two and dropped leaves. `cells_in`: (x0, y0, x1, y1) of the plots, in cells."""
    H, W = cv.shape
    yy, xx = np.mgrid[0:H, 0:W]
    # weathered boards: the cool timber for the body, the plain timber for lit edges
    wc = wood + '_cool' if wood + '_cool' in FI else wood
    ww = 'timber' if wood == 'earth' else (wood + '_warm' if wood + '_warm' in FI else wood)
    band = 9
    inner = ndi.binary_erosion(frame, iterations=band)
    ring = frame & ~inner
    # the low front face on the south: boards seen edge-on, and its shade on the turf
    face = np.zeros_like(frame)
    for k in range(1, 6):
        face |= down(frame, k)
    face &= ~frame
    turf = grassy(cv) & ~frame & ~face
    sh = np.zeros_like(frame)
    for k in range(1, 5):
        sh |= down(face, k)
    for k in range(1, 4):
        sh |= right(frame | face, k)
    sh &= turf
    shadow(cv, sh, core=1, rim=0, fade=True)
    fr = runs_from_top(face)
    vf = nz(H, W, 7.0, 68) > 0.5
    cv[face] = np.where(vf, C(wc, 2), C(wood, 2))[face]
    cv[face & (fr == 1)] = np.where(vf, C(wood, 3), C(ww, 3))[face & (fr == 1)]
    gv2 = nz(H, W, 3.5, 70)
    cv[face & (fr >= 4)] = np.where(gv2 > 0.6, C(wood, 2), np.where(gv2 > 0.35, C(wc, 1), C(wc, 0)))[face & (fr >= 4)]
    # the boards: along x on the north and south, along y on the west and east
    ys_, xs_ = np.nonzero(frame)
    fx0, fx1, fy0, fy1 = xs_.min(), xs_.max(), ys_.min(), ys_.max()
    ns = ring & ((yy - fy0 < band) | (fy1 - yy < band))
    we = ring & ~ns
    t = np.full((H, W), 3)
    # grain: long streaks a tone down, a few lit, knotted
    gx = np.sin(xx * 0.09 + yy * 1.7 + 3 * nz(H, W, 14.0, 62)) > 0.82
    gy = ((np.sin(yy * 0.09 + xx * 1.7 + 3 * nz(H, W, 14.0, 63)) > 0.82))
    t[ns & gx] = 2
    t[we & gy] = 2
    t[ring & (nz(H, W, 6.0, 64) > 0.78)] = 4
    t[ring & (nz(H, W, 2.5, 65) > 0.7)] = np.minimum(t[ring & (nz(H, W, 2.5, 65) > 0.7)], 2)
    cv[ring] = (FI[wood] * 8 + t)[ring]
    # the boards' lit inner and outer edges, a dark gap between board and soil
    outer = ring & ~ndi.binary_erosion(frame, structure=CROSS)
    vv = nz(H, W, 6.0, 67) > 0.5
    sel = outer & (down(~frame, 1) | right(~frame, 1))
    cv[sel] = np.where(vv, C(ww, 4), C(wood, 4))[sel]
    sel = outer & (down(~frame, -1) | right(~frame, -1))
    cv[sel] = np.where(vv, C(wc, 2), C(wood, 2))[sel]
    gap_ = ring & ndi.binary_dilation(inner, structure=CROSS)
    gv = nz(H, W, 4.0, 66)
    cv[gap_] = np.where(gv > 0.62, C(earth, 2), np.where(gv > 0.4, C(wood, 1), C(wc, 0)))[gap_]
    cv[ring & ndi.binary_dilation(gap_, structure=CROSS) & ~gap_ & (down(gap_, 1) | right(gap_, 1))] = C(wc, 2)
    # board joints with nails either side, every 34 to 56 px
    nails = []
    x = fx0 + int(rng.integers(30, 50))
    while x < fx1 - 20:
        for (yA, yB) in ((fy0, fy0 + band), (fy1 - band + 1, fy1 + 1)):
            cv[yA:yB, x][ring[yA:yB, x]] = C(wc, 1)
            nails += [(yA + band // 2, x - 3), (yA + band // 2, x + 3)]
        x += int(rng.integers(34, 57))
    y = fy0 + int(rng.integers(26, 40))
    while y < fy1 - 20:
        for (xA, xB) in ((fx0, fx0 + band), (fx1 - band + 1, fx1 + 1)):
            cv[y, xA:xB][ring[y, xA:xB]] = C(wc, 1)
            nails += [(y - 3, xA + band // 2), (y + 3, xA + band // 2)]
        y += int(rng.integers(34, 57))
    for (ny, nx) in nails:
        put(cv, ny, nx, C('iron', 1), ring)
        put(cv, ny - 1, nx - 1, C('iron', 4), ring)
    # corner posts: 12 px squares a little proud of the frame, end grain on top, lit west side
    for (px, py) in ((fx0 - 1, fy0 - 1), (fx1 - 10, fy0 - 1), (fx0 - 1, fy1 - 10), (fx1 - 10, fy1 - 10)):
        for dy in range(12):
            for dx in range(12):
                Y, X = py + dy, px + dx
                if not (0 <= Y < H and 0 <= X < W):
                    continue
                rr = np.hypot(dx - 5.5, dy - 5.5)
                tt = 4 if rr < 1.5 else (3 if int(rr) % 2 else 2)
                if dx == 0 or dy == 0:
                    tt = 5
                if dx == 11 or dy == 11:
                    tt = 1
                cv[Y, X] = C(ww if tt >= 4 else wood, tt)
        if py > fy0:                                           # the south posts show their front
            for dy in range(12, 17):
                for dx in range(12):
                    put(cv, py + dy, px + dx, C(wc, 2 if dx > 0 else 3) if dy < 16 else C(wc, 1))
    # the soil inside, a little lower: shaded under the north and west boards, clods and crumbs
    fi = np.full((H, W), FI[earth])
    fi[blobs(H, W, 79, 40.0, 0.3)] = FI['earth']
    ti = np.full((H, W), 3)
    cv[inner] = (fi * 8 + ti)[inner]
    band_ = inner & ndi.binary_dilation(~inner, iterations=3) & (down(~inner, 3) | right(~inner, 3))
    dd_ = ndi.distance_transform_edt(inner)
    shift(cv, band_ & ((dd_ <= 1.5) | (((xx + yy) % 2 == 0) & (dd_ <= 3))) & (nz(H, W, 4.0, 69) > 0.2), -1)
    ys2, xs2 = np.nonzero(inner)
    for k in rng.permutation(len(ys2))[: len(ys2) // 160]:
        y_, x_ = int(ys2[k]), int(xs2[k])
        cv[y_, x_] = C(earth, 4)
        put(cv, y_, x_ + 1, C(earth, 4), inner)
        put(cv, y_ + 1, x_, C(earth, 1), inner)
        put(cv, y_ + 1, x_ + 1, C(earth, 2), inner)
    # the plots
    x0c, y0c, x1c, y1c = cells_in
    for cyc in range(y0c, y1c):
        kind = rows[(cyc - y0c) % len(rows)]
        for cxc in range(x0c, x1c):
            X0, Y0 = cxc * cell + 1, cyc * cell + 1
            X1, Y1 = X0 + cell - 2, Y0 + cell - 2
            px, py = xx[Y0:Y1, X0:X1] - X0, yy[Y0:Y1, X0:X1] - Y0
            w_, h_ = X1 - X0, Y1 - Y0
            u = (px + 0.5) / w_ * 2 - 1
            v = (py + 0.5) / h_ * 2 - 1
            r = (np.abs(u) ** 4 + np.abs(v) ** 4) ** 0.25
            plot = r <= 1.0
            sub = cv[Y0:Y1, X0:X1]
            lam = -0.62 * u - 0.78 * v
            body = np.where(lam > 0.45, 4, np.where(lam > -0.35, 3, 2))
            sub[plot] = (FI[earth] * 8 + body)[plot]
            sub[plot & (r > 0.88)] = C(earth, 1)                        # the furrow round it
            sub[plot & (r > 0.78) & (r <= 0.88) & (lam > 0)] = C(earth, 4)
            # clods on the mound
            for _ in range(int(rng.integers(3, 7))):
                gy_, gx_ = int(rng.integers(4, h_ - 4)), int(rng.integers(4, w_ - 4))
                sub[gy_, gx_] = C(earth, 4)
                if gx_ + 1 < w_:
                    sub[gy_, gx_ + 1] = C(earth, 3)
                if gy_ + 1 < h_:
                    sub[gy_ + 1, gx_] = C(earth, 1)
            stage = rng.random()
            k2 = kind
            if stage < 0.12:
                k2 = 'seedling'
            elif stage < 0.22 and kind in ('cabbage', 'lettuce'):
                k2 = 'young'
            elif stage < 0.27 and kind == 'lettuce':
                k2 = 'flowering'
            if stage > 0.95:
                # dug over: furrow lines across the mound, no crop
                for ry in range(5, h_ - 4, 4):
                    sub[ry, 4:w_ - 4][plot[ry, 4:w_ - 4]] = C(earth, 1)
                    sub[ry - 1, 4:w_ - 4][plot[ry - 1, 4:w_ - 4]] = C(earth, 4)
                continue
            crop(cv, Y0 + h_ // 2 + 1, X0 + w_ // 2 + int(rng.integers(-1, 2)), rng, k2)
    # a weed or two in the soil between the plots, leaves dropped on frame and soil
    soil_gap = inner & ~ndi.binary_dilation(np.isin(cv // 8, [FI['leaf'], FI['leaf_cool'], FI['grass'],
                                                               FI['grass_cool']]), iterations=2)
    ys3, xs3 = np.nonzero(soil_gap)
    for k in rng.permutation(len(ys3))[:3]:
        stamp(cv, int(ys3[k]), int(xs3[k]), tuft_shape(rng, 0.8), C('grass', 3), inner)
    litter(cv, frame, rng, 0.25)


def weeds_at_foot(cv, raised, rng, rate=0.12):
    """Tufts of the turf standing at the foot of something raised (a bed's frame, a kerb, a wall),
    growing up over its lowest rows, about one every 8 to 12 px (eastward-edges.md 3.2, 8.2)."""
    H, W = cv.shape
    face = np.zeros_like(raised)
    for k in range(1, 5):
        face |= down(raised, k)
    foot = grassy(cv) & ~raised & ~face & down(face, 1)
    # the tufts stay on the turf (the raised outline is not broken into one-texel teeth): those
    # under the front face stand in front of it, so they are lowered by a texel or two
    ok = grassy(cv) & ~raised & ~face
    ys, xs = np.nonzero(foot)
    taken = np.zeros_like(raised)
    for k in rng.permutation(len(ys))[: int(len(ys) * rate)]:
        y, x = int(ys[k]), int(xs[k])
        if taken[max(0, y - 3):y + 4, max(0, x - 5):x + 6].any():
            continue
        taken[y, x] = True
        base = cv[min(H - 1, y + 2), x]
        base = base // 8 * 8 + 3 if base % 8 < 6 else C('grass', 3)       # lit turf: they stand in the light
        stamp(cv, y + 3, x, [(dy, dx, d_) for (dy, dx, d_) in tuft_shape(rng, rng.uniform(0.9, 1.4)) if dy < 0 or d_ != -1],
              base, ok=ok)


# ------------------------------------------------------------------------------------------------
# paving and a kerb (Eastward 16 and 01)
# ------------------------------------------------------------------------------------------------
def paving(cv, pave, rng, kerb=9, course=(18, 23), length=(18, 30), fams=('stone_warm', 'stone_warm', 'ashlar')):
    """A paved square: flags in staggered courses, each a calm slab lit along its top and west
    edges, shaded along its bottom and east, dark joints between them, a chipped corner or a
    crack here and there, moss and grass in a few joints, a worn lighter middle; a kerb of long
    slabs round it with a lit top row, a low dark front face on the south and its shadow on the
    ground (eastward-edges.md 5.2). Returns the kerb's face mask."""
    H, W = cv.shape
    inner = ndi.binary_erosion(pave, iterations=kerb)
    kb = pave & ~inner
    # the flags: courses of varied height, each split into slabs of varied length; now and then a
    # big slab spans two courses (no brick bond, no repeat)
    sl = np.full((H, W), -1, np.int64)
    k = 0
    y = -int(rng.integers(0, 10))
    while y < H:
        ch = int(rng.choice([14, 18, 18, 22, 26]))
        x = -int(rng.integers(0, 30))
        while x < W:
            L = int(rng.integers(14, 36))
            if rng.random() < 0.12:                                  # a big slab over two courses
                sl[max(0, y):max(0, y + ch + 16), max(0, x):max(0, x + L + 8)] = k
                L += 8
            else:
                sl[max(0, y):max(0, y + ch), max(0, x):max(0, x + L)][sl[max(0, y):max(0, y + ch), max(0, x):max(0, x + L)] < 0] = k
            k += 1
            x += L
        y += ch
    hsh = (sl * 2654435761 % 1000) / 1000.0
    joint = np.zeros((H, W), bool)
    joint[:-1] |= sl[:-1] != sl[1:]
    joint[:, :-1] |= sl[:, :-1] != sl[:, 1:]
    # chipped corners: where joints cross, the joint widens to a small round chip on some slabs
    cross_ = joint & (ndi.convolve(joint.astype(int), np.ones((3, 3), int), mode='constant') >= 5)
    chip = ndi.binary_dilation(cross_ & (hsh > 0.55), structure=CROSS)
    joint |= chip
    top_r = np.zeros((H, W), bool)
    top_r[1:] = joint[:-1] & ~joint[1:]
    left_c = np.zeros((H, W), bool)
    left_c[:, 1:] = joint[:, :-1] & ~joint[:, 1:]
    fam = np.array([FI[fams[int(v * 997) % len(fams)]] for v in hsh.ravel()]).reshape(H, W)
    t = np.where(hsh > 0.8, 4, np.where(hsh < 0.12, 2, 3))
    # the worn line where feet go (the centre and the way in) a tone lighter on most slabs
    wear = blobs(H, W, 91, 70.0, 0.3) & (hsh > 0.25)
    t = np.where(wear & (t == 3), 4, t)
    code = fam * 8 + t
    lit = (top_r | left_c) & ~joint
    code[lit] = fam[lit] * 8 + np.minimum(5, t[lit] + 1)
    near_bot = (down(joint, -1) | (down(joint, -2) & (((np.mgrid[0:H, 0:W][1]) % 2) == 0))) & ~joint
    near_r = right(joint, -1) & ~joint
    code[near_bot | near_r] = fam[near_bot | near_r] * 8 + np.maximum(1, t[near_bot | near_r] - 1)
    code[joint] = C('stone', 1)
    # pits and speckles of the stone's grain, two texels, a tone down, sparse
    gy_, gx_ = np.nonzero(~joint & ~lit)
    for kk in rng.permutation(len(gy_))[: len(gy_) // 35]:
        y0, x0 = int(gy_[kk]), int(gx_[kk])
        code[y0, x0] = step(code[y0, x0], -1)
        if x0 + 1 < W and not joint[y0, x0 + 1]:
            code[y0, x0 + 1] = step(code[y0, x0 + 1], -1)
    # the pale flags are the most worn: their grain shows as small pits
    pale = (t >= 4) & ~joint & ~lit
    py_, px_ = np.nonzero(pale)
    for kk in rng.permutation(len(py_))[: len(py_) // 22]:
        code[py_[kk], px_[kk]] = step(code[py_[kk], px_[kk]], -1)
    cv[inner] = code[inner]
    # cracks: a few, running from a joint across a slab in single steps, a lit texel beside
    ys, xs = np.nonzero(inner & joint)
    for kk in rng.permutation(len(ys))[: len(ys) // 400]:
        y0, x0 = int(ys[kk]), int(xs[kk])
        d = 1 if rng.random() < 0.5 else -1
        for j in range(1, int(rng.integers(6, 14))):
            yy_, xx_ = y0 + j // 2 + (j % 3 == 0), x0 + d * j
            if not (0 <= yy_ < H and 0 <= xx_ < W) or not inner[yy_, xx_] or joint[yy_, xx_]:
                break
            cv[yy_, xx_] = step(cv[yy_, xx_], -2)
            put(cv, yy_ - 1, xx_, step(cv[max(0, yy_ - 1), xx_], 1), inner & ~joint)
    # moss and grass in the joints, more towards the edges of the square, and dirt in a few
    dk = ndi.distance_transform_edt(inner)
    jy, jx = np.nonzero(inner & joint)
    for kk in rng.permutation(len(jy))[: len(jy) // 40]:
        y0, x0 = int(jy[kk]), int(jx[kk])
        if rng.random() > 1.2 - dk[y0, x0] / 60.0:
            continue
        horiz_j = 0 <= x0 + 1 < W and joint[y0, x0 + 1]
        for j in range(int(rng.integers(2, 7))):
            yy_, xx_ = (y0, x0 + j) if horiz_j else (y0 + j, x0)
            if 0 <= yy_ < H and 0 <= xx_ < W and joint[yy_, xx_] and inner[yy_, xx_]:
                cv[yy_, xx_] = C('grass', 3 if j % 2 else 2)
                if j % 2 == 0:
                    put(cv, yy_ - 1, xx_, C('grass', 4), inner)
    for kk in rng.permutation(len(jy))[: len(jy) // 150]:
        y0, x0 = int(jy[kk]), int(jx[kk])
        cv[y0, x0] = C('earth', 2)
    # the kerb: long slabs round the square, their top lit, joints across the band
    dist_out = ndi.distance_transform_edt(pave)
    kcode = np.full((H, W), C('ashlar', 4))
    kcode[dist_out <= 2.5] = C('ashlar', 5)
    kcode[(dist_out > kerb - 2.5)] = C('ashlar', 3)
    # joints across the band, every 20 to 30 px of its length (by angle round the square's centre
    # is overkill: cut along x on the north and south runs, along y on the west and east runs)
    ys_, xs_ = np.nonzero(pave)
    cy0, cx0 = ys_.mean(), xs_.mean()
    yyg, xxg = np.mgrid[0:H, 0:W]
    horiz = np.abs(yyg - cy0) / max(1, np.ptp(ys_)) > np.abs(xxg - cx0) / max(1, np.ptp(xs_))
    cut = np.where(horiz, (xxg % 26) == 0, (yyg % 22) == 0)
    kcode[cut] = C('stone', 1)
    kcode[np.roll(cut, 1, 1) & horiz] = C('ashlar', 5)
    kcode[np.roll(cut, 1, 0) & ~horiz] = C('ashlar', 5)
    cv[kb] = kcode[kb]
    ie = kb & ndi.binary_dilation(inner, structure=CROSS)                       # the kerb's inner edge
    var = nz(H, W, 9.0, 85) > 0.45
    cv[ie] = np.where(var, C('stone', 2), C('stone', 3))[ie]
    cv[kb & cut] = C('stone', 1)
    # the low front face on the south, the side faces darker, and the shadow on the ground
    face = np.zeros_like(pave)
    for k2 in range(1, 6):
        face |= down(pave, k2)
    face &= ~pave
    cv[face] = np.where(var, C('ashlar', 2), C('stone_warm', 2))[face]
    sel = face & ~down(face, 1)
    cv[sel] = np.where(var, C('ashlar', 3), C('ashlar', 4))[sel]
    cv[face & ~down(face, -1)] = C('stone', 1)
    fcut = face & np.roll(cut, 0, 1)
    cv[fcut] = C('stone', 1)
    sh = np.zeros_like(pave)
    for k2 in range(1, 4):
        sh |= down(face, k2)
    for k2 in range(1, 4):
        sh |= right(pave | face, k2)
    sh &= ~pave & ~face
    shadow(cv, sh, core=2, rim=1, fade=True)
    return face


# ------------------------------------------------------------------------------------------------
# where two grounds meet on one level (grass to sand): frayed, no rim, no shadow
# ------------------------------------------------------------------------------------------------
def frayed_edge(cv, m, turf, rng, tufts=1.0, strays=1.0):
    """Turf meeting a ground on its own level (sand, a yard): lobes of turf creep over the edge,
    tufts lean out over it, single tufts stray onto it within a cell, and the turf thins (its last
    texels a tone lighter and warmer). No outline, no rim and no shadow (eastward-edges.md 4.1)."""
    from .softgrid import clean
    H, W = cv.shape
    s0 = int(rng.integers(0, 99999))
    turf = turf & ~m
    dt = ndi.distance_transform_edt(m)
    dep = np.clip((fbm(H, W, 13.0, s0) - 0.28) * 20.0, 0, 8)
    lob = m & (dt <= dep) & ndi.binary_dilation(turf, iterations=7)
    m2 = clean(m & ~lob, min_area=1.0)
    lob = m & ~m2
    _, (iy, ix) = ndi.distance_transform_edt(~turf, return_indices=True)
    cv[lob] = cv[iy[lob], ix[lob]]
    turf2 = (turf | lob) & ~m2
    thin = turf2 & ndi.binary_dilation(m2, iterations=2)
    cv[thin] = sib(cv[thin], 'warm')
    bnd = turf2 & ndi.binary_dilation(m2, structure=CROSS)
    ys, xs = np.nonzero(bnd)
    taken = np.zeros_like(m)
    for k in rng.permutation(len(ys))[: int(len(ys) / 6 * tufts)]:
        y, x = int(ys[k]), int(xs[k])
        if taken[max(0, y - 4):y + 5, max(0, x - 5):x + 6].any():
            continue
        taken[y, x] = True
        base = cv[y, x] if cv[y, x] % 8 < 6 else C('grass', 3)
        stamp(cv, y + 1, x, [(dy, dx, d_) for (dy, dx, d_) in tuft_shape(rng, rng.uniform(1.0, 1.6)) if dy < 0], base)
    # strays: tufts on the other ground within 4 to 20 px of the edge
    dd = ndi.distance_transform_edt(m2)
    ys, xs = np.nonzero(m2 & (dd > 4) & (dd < 20))
    for k in rng.permutation(len(ys))[: int(len(ys) / 260 * strays)]:
        y, x = int(ys[k]), int(xs[k])
        stamp(cv, y, x, tuft_shape(rng, rng.uniform(0.8, 1.4)), C('grass_warm', 3))
    return m2


# ------------------------------------------------------------------------------------------------
# the sea's edge on sand
# ------------------------------------------------------------------------------------------------
def shore(cv, sand_m, sea, rng, seed=0):
    """Sand meeting still sea (Eastward 39): the sand darkens and cools in a wet band 5 to 10 px
    above the water, a lumpy line of spent swash (a pale lit line, broken) along the water's edge,
    then the shallows lit and warm 6 to 12 px, stepping down to the body; stones in the shallows."""
    H, W = cv.shape
    land = sand_m & ~sea
    dl = ndi.distance_transform_edt(~sea)
    wet = land & (dl <= 5 + 5 * nz(H, W, 22.0, seed + 1))
    cv[wet] = C('sand_cool', 2)
    cv[wet & (dl <= 2)] = C('sand_cool', 1)
    cv[wet & ~ndi.binary_erosion(wet | sea, iterations=1) & ~sea & (dl > 3)] = C('sand_cool', 3)
    dw = ndi.distance_transform_edt(sea)
    t = np.full((H, W), 2)
    t[sea & (dw <= 12 + 6 * nz(H, W, 26.0, seed + 2))] = 3
    t[sea & (dw <= 5 + 3 * nz(H, W, 14.0, seed + 3))] = 4
    fam = np.full((H, W), FI['water'])
    fam[sea & (dw <= 14)] = FI['water_warm']
    cv[sea] = (fam * 8 + t)[sea]
    # the swash line: a pale line 1 to 2 px a little out from the edge, in lumps, broken
    sw = sea & (np.abs(dw - (2.5 + 2.0 * nz(H, W, 10.0, seed + 4))) < 0.8) & (nz(H, W, 7.0, seed + 5) > 0.3)
    cv[sw] = C('water', 5)
    cv[sea & down(sw, 1) & ~sw] = C('water_warm', 3)
    # ripples on the open water
    ys, xs = np.nonzero(sea & (dw > 16))
    for k in rng.permutation(len(ys))[: len(ys) // 520]:
        y, x = int(ys[k]), int(xs[k])
        L = int(rng.integers(4, 12))
        for j in range(L):
            if 0 <= x + j < W and sea[y, x + j]:
                cv[y, x + j] = C('water', 4 if 0 < j < L - 1 else 3)
                if y + 1 < H and sea[y + 1, x + j]:
                    cv[y + 1, x + j] = C('water', 1)


# ------------------------------------------------------------------------------------------------
# the forest floor
# ------------------------------------------------------------------------------------------------
def litter(cv, m, rng, density=1.0, shade=True):
    """Fallen leaves and twigs in drifts over `m`: leaves 2 to 3 px (clay, brass, dry earth and
    dead green), each lit at its upper left with a shade texel under it; twigs 4 to 7 px."""
    H, W = cv.shape
    tones = [C('clay', 3), C('brass', 3), C('earth_warm', 4), C('leaf_warm', 3), C('earth_warm', 3), C('brass', 2)]
    drift = nz(H, W, 30.0, int(rng.integers(0, 9999)))
    ys, xs = np.nonzero(m)
    for k in rng.permutation(len(ys))[: int(len(ys) / 90 * density)]:
        y, x = int(ys[k]), int(xs[k])
        if rng.random() > drift[y, x] * 1.3 or not (1 <= y < H - 2 and 1 <= x < W - 3):
            continue
        if rng.random() < 0.88:
            c0 = tones[int(rng.integers(0, len(tones)))]
            lw = 3 if rng.random() < 0.5 else 2
            cv[y, x:x + lw] = c0
            cv[y, x] = step(c0, 1)
            if rng.random() < 0.6:
                cv[y - 1, x + 1] = c0
            if shade:
                sel = cv[y + 1, x + 1:x + lw + 1]
                cv[y + 1, x + 1:x + lw + 1] = np.where(sel % 8 < 6, step(sel, -1), sel)
        else:
            L = int(rng.integers(4, 8))
            for j in range(L):
                put(cv, y + (j // 3 if rng.random() < 0.5 else 0), x + j, C('timber', 2 if j % 2 else 3))


def forest_floor(cv, rng, seed, feet=()):
    """Under trees (Eastward 02 and 22): the leaf-green turf thin and patchy; bare earth in frayed
    patches under a drift of litter; moss in soft cushions; the canopy's shade over most of it,
    fading out through a checker, with sun flecks falling through."""
    H, W = cv.shape
    yy, xx = np.mgrid[0:H, 0:W]
    wob = fbm(H, W, 10.0, seed + 9)
    bare = np.zeros((H, W), bool)
    for (fx_, fy_, r_) in feet:                     # bare earth round the trunks, where roots break the turf
        bare |= ((xx - fx_ - r_ * 0.15) / (r_ * 1.15)) ** 2 + ((yy - fy_ - 1) / (r_ * 0.38)) ** 2 <= 0.55 + 0.7 * wob
    f = np.full((H, W), FI['earth_warm'])
    f[patches(H, W, seed + 2, 24.0, 0.4)] = FI['earth']
    t = np.full((H, W), 3)
    t[patches(H, W, seed + 3, 12.0, 0.25)] = 2
    cv[bare] = (f * 8 + t)[bare]
    turf = grassy(cv)
    # the turf frays onto the bare earth
    frayed_edge(cv, bare, turf, rng, tufts=0.8, strays=0.6)
    litter(cv, bare | (patches(H, W, seed + 4, 30.0, 0.3) & ~bare), rng, 0.25, shade=False)
    moss = blobs(H, W, seed + 5, 22.0, 0.05) & ~bare
    cv[moss] = C('leaf', 4)
    cv[moss & ~ndi.binary_erosion(moss, structure=CROSS) & down(~moss, -1)] = C('leaf', 2)
    cv[moss & ndi.binary_erosion(moss, iterations=2) & (nz(H, W, 5.0, seed + 6) > 0.62)] = C('leaf_warm', 4)
    # the canopy's shade and sun flecks
    sh = blobs(H, W, seed + 7, 110.0, 0.68)
    # no small islands of light in the shade: a gap in the canopy is a broad pool or none
    holes = ~sh
    lab_, n_ = ndi.label(holes)
    if n_:
        sz_ = ndi.sum(holes, lab_, range(1, n_ + 1))
        sh |= np.isin(lab_, 1 + np.nonzero(sz_ < 3000)[0])
    shift(cv, sh, -1)
    # its edge fades over 6 px through a checker, then a sparser one (no crisp outline)
    dsh = ndi.distance_transform_edt(~sh)
    shift(cv, (dsh > 0) & (dsh <= 3) & (((xx + yy) % 2) == 0), -1)
    shift(cv, (dsh > 3) & (dsh <= 6) & ((xx % 2) == 0) & ((yy % 2) == 0), -1)
    # out of the shade the turf catches the light: lit blade tips in pairs, a few more of them
    ys_, xs_ = np.nonzero(~sh & (dsh > 1) & grassy(cv))
    for k in rng.permutation(len(ys_))[: len(ys_) // 40]:
        y_, x_ = int(ys_[k]), int(xs_[k])
        if 1 <= y_ < H and 1 <= x_ < W - 1 and cv[y_, x_] % 8 < 5:
            cv[y_, x_] = step(cv[y_, x_], 1)
            cv[y_ - 1, x_ + (1 if k % 2 else -1)] = step(cv[y_ - 1, x_ + (1 if k % 2 else -1)], 2)
    # in the shade the litter lies thicker and the odd dapple of light gets through
    litter(cv, sh & (nz(H, W, 20.0, seed + 10) > 0.5), rng, 0.3, shade=False)
    for _ in range(int(sh.sum() / 900)):
        ys_, xs_ = np.nonzero(sh)
        k = int(rng.integers(0, len(ys_)))
        y_, x_ = int(ys_[k]), int(xs_[k])
        for (dy, dx) in ((0, 0), (0, 1), (1, 0), (1, 1), (0, 2)):
            if 0 <= y_ + dy < H and 0 <= x_ + dx < W and cv[y_ + dy, x_ + dx] % 8 < 5:
                cv[y_ + dy, x_ + dx] = step(cv[y_ + dy, x_ + dx], 1)
    # sun flecks through the leaves: small soft ovals, a tone up, their rims a checker
    fl = np.zeros((H, W), bool)
    for _ in range(int(H * W / 16000)):
        fy_, fx_ = rng.uniform(0, H), rng.uniform(0, W)
        rx_, ry_ = rng.uniform(3, 6), rng.uniform(1.5, 3)
        fl |= ((xx - fx_) / rx_) ** 2 + ((yy - fy_) / ry_) ** 2 <= 1
    shift(cv, fl, 1)
    shift(cv, ndi.binary_dilation(fl, iterations=2) & ~fl & (((xx + yy) % 2) == 0), 1)
    return sh


def roots(cv, x, y, rng, half=12, n=4, wood='timber'):
    """Roots spreading from a trunk's foot over the ground: each 14 to 34 px, out to the side and a
    little down, tapering from 3 px to 1, lit along its top, dark beneath, its shade on the ground,
    the ground bulging a texel round it."""
    H, W = cv.shape
    for k in range(n):
        side = -1 if k % 2 == 0 else 1
        sx = x + side * int(half * rng.uniform(0.75, 1.0))
        sy = y - int(rng.integers(2, 6))
        ang = rng.uniform(0.2, 0.75)
        L = int(rng.integers(18, 40))
        px, py = float(sx), float(sy)
        for j in range(L):
            wd = 4 if j < L * 0.2 else (3 if j < L * 0.5 else (2 if j < L * 0.8 else 1))
            ang += rng.uniform(-0.15, 0.15)
            px += side * np.cos(ang)
            py += np.sin(ang) * 0.6
            X, Y = int(round(px)), int(round(py))
            for q in range(wd):
                tt = 5 if q == 0 else (4 if q < wd - 1 else 2)
                put(cv, Y + q, X, C(wood, tt))
            if 0 <= Y + wd < H and 0 <= X < W and cv[Y + wd, X] % 8 < 6:
                cv[Y + wd, X] = step(cv[Y + wd, X], -2)
            if 0 <= Y + wd + 1 < H and 0 <= X < W and cv[Y + wd + 1, X] % 8 < 6 and j % 2:
                cv[Y + wd + 1, X] = step(cv[Y + wd + 1, X], -1)


# ------------------------------------------------------------------------------------------------
# a footbridge (Matt, 26 Oct 19:42: bank to bank, abutments on both banks, posts both sides)
# ------------------------------------------------------------------------------------------------
def footbridge(cv, x0, x1, water, rng, wood='timber', stone='ashlar') -> list:
    """A plank footbridge across water running east and west, from x0 to x1 (texels): a dressed
    stone abutment set into each bank, the deck's planks laid across from one abutment to the other
    (each lit along its top, a dark joint, a nail at each end), a kerb beam along both sides, posts
    on both sides at the abutments and mid-span joined by a rail; the deck's thickness shows as a
    narrow side band (lit on the west, in shade on the east) and its shade lies on the water to the
    east. Returns the deck mask."""
    H, W = cv.shape
    cols = water[:, x0:x1].any(1)
    ys = np.nonzero(cols)[0]
    if not len(ys):
        return np.zeros((H, W), bool)
    yn, ys_ = int(ys.min()), int(ys.max())
    wc = wood + '_cool' if wood + '_cool' in FI else wood
    ww = wood + '_warm' if wood + '_warm' in FI else wood
    # the shade on the water, east and a little south of the deck
    sh = np.zeros((H, W), bool)
    sh[yn:ys_ + 1, x1:min(W, x1 + 7)] = True
    sh &= water
    shift(cv, sh, -2)
    shift(cv, water & np.roll(sh, 3, 1) & ~sh, -1)
    # the abutments: dressed stone blocks, wider than the deck, their tops lit, faces to the south
    for (ya, yb) in ((yn - 14, yn + 5), (ys_ - 4, ys_ + 13)):
        for y in range(ya, yb):
            for x in range(x0 - 9, x1 + 9):
                if not (0 <= y < H and 0 <= x < W):
                    continue
                by = (y - ya) // 6
                bx = (x - x0 + 9 + (by % 2) * 7) // 14
                jy = (y - ya) % 6 == 5
                jx = (x - x0 + 9 + (by % 2) * 7) % 14 == 13
                tt = 1 if (jy or jx) else (4 if (y - ya) % 6 == 0 else (3 if (bx + by) % 3 else 2))
                if y >= yb - 3:
                    tt = 2 if not jx else 1                       # the abutment's front face
                cv[y, x] = C(stone, tt)
    # the deck: planks across, from the north abutment's top to the south one's
    d0, d1 = yn - 10, ys_ + 8
    deck = np.zeros((H, W), bool)
    deck[d0:d1, x0:x1] = True
    for y in range(d0, d1):
        k = (y - d0) % 6
        pl = (y - d0) // 6
        body = 3 if (pl * 7919) % 5 else 2
        for x in range(x0, x1):
            tt = 4 if k == 0 else (1 if k == 5 else body)
            cv[y, x] = C(ww if k == 0 else wood, tt)
        if (y - d0) % 6 == 2:
            put(cv, y, x0 + 4, C('iron', 1))
            put(cv, y, x1 - 5, C('iron', 1))
        if (y - d0) % 6 == 3 and rng.random() < 0.5:                 # grain
            gx = x0 + int(rng.integers(6, max(7, x1 - x0 - 12)))
            cv[y, gx:gx + int(rng.integers(3, 8))] = C(wood, 2)
    # kerb beams along both sides
    cv[d0:d1, x0:x0 + 3] = C(ww, 4)
    cv[d0:d1, x0 + 2] = C(wood, 2)
    cv[d0:d1, x1 - 3:x1] = C(wc, 2)
    cv[d0:d1, x1 - 3] = C(wood, 3)
    # the deck's thickness: a side band beyond each beam, lit west, dark east, over the water
    cv[d0 + 2:d1, x0 - 2:x0] = C(wood, 3)
    cv[d0 + 2:d1, x0 - 2] = C(wc, 1)
    cv[d0 + 2:d1, x1:x1 + 2] = C(wc, 1)
    cv[d1:d1 + 3, x0:x1] = np.where(cv[d1:d1 + 3, x0:x1] >= 0, C(wc, 1), cv[d1:d1 + 3, x0:x1])
    deck[d0:d1 + 3, x0 - 2:x1 + 2] = True
    # posts both sides at the abutments and mid-span, their tops lit, joined by rails
    posts = sorted({d0 + 4, (d0 + d1) // 2, d1 - 2})
    for side_x, lit in ((x0 - 2, True), (x1 - 2, False)):
        # the rail first (it runs between the posts' tops), then the posts over it
        for y in range(posts[0] - 10, posts[-1] - 9):
            put(cv, y, side_x, C(ww, 4) if lit else C(wood, 3))
            put(cv, y, side_x + 1, C(wood, 3) if lit else C(wc, 1))
        for py in posts:
            for dy in range(-12, 1):
                for dx in range(4):
                    tt = (4 if dx == 0 else (3 if dx < 3 else 1)) if lit else (3 if dx == 0 else (2 if dx < 3 else 1))
                    if dy <= -11:
                        tt = 5 if dx < 3 else 3
                    put(cv, py + dy, side_x - 1 + dx, C(ww if tt >= 4 else wood, tt))
            # its shade on the deck or the water to the east
            for dy in range(-2, 1):
                X = side_x + 3
                if 0 <= py + dy < H and 0 <= X < W and cv[py + dy, X] % 8 < 6:
                    cv[py + dy, X] = step(cv[py + dy, X], -1)
    return deck


# ------------------------------------------------------------------------------------------------
# a tree standing on the ground (Matt, 26 Oct 19:42: "the trees could be improved a touch")
# ------------------------------------------------------------------------------------------------
def seat_tree(img, anc, rng, crown=True):
    """A kit tree seated in its place, its own design kept: the crown's underside scalloped (no flat
    base) and a step darker, its shade falling on the trunk below it, and the trunk's foot flaring
    a few texels into the ground (the roots and the contact shadow are drawn on the ground)."""
    from PIL import Image
    from .palette import is_fam as _isf, to_rgba as _rgba
    from .screen import to_codes
    cd = to_codes(img)
    h, w = cd.shape
    green = (_isf(cd, 'grass') | _isf(cd, 'leaf')) & (cd >= 0)
    if not green.any():
        return img, anc
    wood = (cd >= 0) & ~green & (cd % 8 < 6)
    # the crown's lowest texel per column, and its scalloped underside
    low = np.full(w, -1)
    for x in range(w):
        ys = np.nonzero(green[:, x])[0]
        if len(ys):
            low[x] = ys.max()
    sc = scallops(w, rng, (6, 12), (0, 3))
    for x in range(w):
        if low[x] < 0 or not crown:
            continue
        cut = int(sc[x])
        for k in range(cut):
            y = low[x] - k
            if green[y, x] and not wood[min(h - 1, y + 1), x]:
                cd[y, x] = -1
        y0 = low[x] - cut
        y = y0
        if 0 <= y < h and green[y, x] and cd[y, x] >= 0 and cd[y, x] % 8 >= 2:
            cd[y, x] = step(cd[y, x], -1)
        # the crown's shade on the trunk under it, fading over 8 texels
        for k in range(1, 9):
            y = low[x] + k
            if 0 <= y < h and wood[y, x] and (k < 4 or (k + x) % 2 == 0):
                cd[y, x] = step(cd[y, x], -2 if k < 4 else -1)
    # the trunk's foot flares: its last rows widen a texel or two each side, in its dark tones
    foot = int(round(anc[1])) - 1
    if 0 <= foot < h:
        xs = np.nonzero(wood[foot])[0]
        if len(xs):
            xl, xr = xs.min(), xs.max()
            for k, wd in ((0, 3), (1, 2), (2, 1), (3, 1)):
                y = foot - k
                for d in range(1, wd + 1):
                    if 0 <= xl - d < w and cd[y, xl - d] < 0:
                        cd[y, xl - d] = C('timber', 2 if d < wd else 1)
                    if 0 <= xr + d < w and cd[y, xr + d] < 0:
                        cd[y, xr + d] = C('timber_cool', 1)
    return Image.fromarray(_rgba(cd), 'RGBA'), anc


def tidy_codes(cv: np.ndarray, keep: np.ndarray | None = None) -> None:
    """No lone texels: one unlike all four neighbours takes their most common code."""
    from .village import tidy
    tidy(cv, passes=1, keep=keep)
