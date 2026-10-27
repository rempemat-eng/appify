"""The soft grid: blocky plans with soft outlines (density 3 and up).

Matt, 26 Oct 15:36, with an Eastward forest screenshot (raised grass plateaus with earth ledges, a
dirt path, wooden steps): "this is what i mean with soft grid. edges and paths are a bit block like
but they are not sharp like minecraft. think about how this could be implemented and do it".

What the screenshot shows, and what every ground generator does through this module:

1. The plan is a mask of whole cells on the 8 world px grid (24 art px at density 3): rectangles,
   steps and notches of whole cells. A route is the cells whose centres lie within its half width
   of its line, so a diagonal becomes a staircase of cells.
2. The outline is the plan's dual-grid outline: the cell mask laid on the texel grid.
3. Corners are rounded: outer corners with a large radius (about 0.4 of a cell), inner corners
   filled with a smaller fillet (about 0.25 of a cell). Both are exact pixel circles (a closing then
   an opening by a disc, done with distance transforms).
4. The rounded outline is displaced by seeded smooth noise: lumps 8 to 20 art px long and 1 to 3
   px deep, never single-pixel teeth (the noise is smooth at that scale, and the result is cleaned
   of one-texel spurs and bites).
5. It is rasterised by the soft-grid pixel rules (1 px steps, clean runs): the mask itself, then
   the painters lay their bands (a sunken path's rim and lit lip, a ledge's lip, under-lip line,
   face, clods and foot) from eastward-edges.md 2 and 3.
6. Breakers (tufts, roots, pebbles) sit on 10 to 20 % of the edge length, so no long run reads as
   ruled.

    cells = softgrid.cells_polyline(points, width, H, W)   # the plan, in cells
    m = softgrid.shape(cells, H, W, seed)                   # the soft outline, in texels
    softgrid.breakers(cv, m, rng, kind='path')              # tufts and pebbles on the edge

The review twins: scripts/review/edges.py (detail.ragged_edge, detail.corner_radius).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import ctx
from .palette import C, FI, step
from .terrain import noise as TN

CELL = 8.0                    # world px
R_OUT = 0.4                   # outer corner radius, in cells
R_IN = 0.25                   # inner corner fillet, in cells
R_TURN_OUT = 0.4              # a route's turn, outer corner (cells): Eastward 13's dirt paths turn at 6.4 native px, 0.38 of a tile
R_TURN_IN = 0.25              # and the inner fillet
LUMP = (8.0, 20.0)            # lump length, art px
AMP = (1.5, 3.0)              # lump depth, art px
CROSS = ndi.generate_binary_structure(2, 1)


def cell_px() -> int:
    return int(round(CELL * ctx.D))


# ------------------------------------------------------------------------------------------------
# 1. plans in cells
# ------------------------------------------------------------------------------------------------
def grid_shape(H: int, W: int) -> tuple:
    c = cell_px()
    return (H + c - 1) // c, (W + c - 1) // c


def cells_polyline(points, width: float, H: int, W: int, shrink: float = 0.0, run: float | None = 3.0) -> np.ndarray:
    """The cells a route covers: those whose centres lie within width / 2 - shrink world px of its
    line (made blocky first, manhattan, unless run is None), joined 4-connected."""
    if run:
        points = manhattan(points, run)
    gh, gw = grid_shape(H, W)
    cy, cx = (np.mgrid[0:gh, 0:gw] + 0.5) * CELL
    d = np.full((gh, gw), 1e9)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((cx - x0) * dx + (cy - y0) * dy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(cx - x0 - t * dx, cy - y0 - t * dy))
    m = d <= width / 2.0 - shrink
    return join4(m, d)


def manhattan(points, run: float = 3.0) -> list:
    """A route's line made blocky: every slanting stretch becomes a few long runs along x and y
    (each about `run` cells long), turning at cell centres, so the cells it covers step in a few
    big notches (Eastward's paths), never a one-cell staircase."""
    out = [tuple(points[0])]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) < 1e-6 or abs(dy) < 1e-6:
            out.append((x1, y1))
            continue
        n = max(1, int(round(max(abs(dx), abs(dy)) / (run * CELL))))
        snap = lambda v: (np.floor(v / CELL) + 0.5) * CELL
        px, py = x0, y0
        for i in range(1, n + 1):
            nx, ny = x0 + dx * i / n, y0 + dy * i / n
            if i < n:
                nx, ny = snap(nx), snap(ny)
            if abs(dx) >= abs(dy):
                out += [(nx, py), (nx, ny)]
            else:
                out += [(px, ny), (nx, ny)]
            px, py = nx, ny
    return out


def cells_route(points, n: int, H: int, W: int, run: float = 5.0) -> np.ndarray:
    """A route of constant width: n cells wide all along, laid in long straight runs along x and y
    (a slanting stretch becomes a few runs of about `run` cells), each run a band of exactly n cells
    centred on its line, the runs overlapping at the turns so a turn is a clean L (rounded later by
    the outline). For an even n the line lies on cell lines, for an odd n on cell centres."""
    gh, gw = grid_shape(H, W)
    m = np.zeros((gh, gw), bool)
    pts = manhattan(points, run)
    if n % 2 == 0:
        snap = lambda v: int(round(v / CELL))                       # a cell line index
        lo, hi = n // 2, n // 2
    else:
        snap = lambda v: int(np.floor(v / CELL))                    # a cell index
        lo, hi = (n - 1) // 2, (n - 1) // 2 + 1
    q = [(snap(x), snap(y)) for x, y in pts]
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        if y0 == y1:                                                # along x
            a, b = sorted((x0, x1))
            m[max(0, y0 - lo):max(0, y0 + hi), max(0, a - lo):max(0, b + hi)] = True
        elif x0 == x1:                                              # along y
            a, b = sorted((y0, y1))
            m[max(0, a - lo):max(0, b + hi), max(0, x0 - lo):max(0, x0 + hi)] = True
        else:                                                       # (manhattan leaves none; be safe)
            m[max(0, min(y0, y1) - lo):max(y0, y1) + hi, max(0, min(x0, x1) - lo):max(x0, x1) + hi] = True
    return m


def curve_line(points, radius: float, share: float = 0.95) -> np.ndarray:
    """The polyline (world px) with each corner filleted to a smooth arc of `radius` world px (a
    fillet takes at most `share` of either leg; 0.5 lets the bends meet, a meander with no
    straight reach), sampled every 2 px."""
    pts = [np.asarray(p, float) for p in points]
    samp = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        u, v = (a - b) / np.linalg.norm(a - b), (c - b) / np.linalg.norm(c - b)
        ang = np.arccos(np.clip(np.dot(u, v), -1, 1))
        t = min(radius / np.tan(ang / 2), np.linalg.norm(a - b) * share, np.linalg.norm(c - b) * share)
        p0, p1 = b + u * t, b + v * t
        for s_ in np.linspace(0, 1, 48):                           # a quadratic curve through the corner
            samp.append((1 - s_) ** 2 * p0 + 2 * (1 - s_) * s_ * b + s_ * s_ * p1)
    samp.append(pts[-1])
    dense = []
    for a, b in zip(samp, samp[1:]):
        k = max(2, int(np.linalg.norm(b - a) / 2))
        dense += [a + (b - a) * j / k for j in range(k)]
    dense.append(samp[-1])
    return np.array(dense)


def cells_curve(points, n: int, H: int, W: int, radius: float) -> np.ndarray:
    """The cells a desire line covers (curve_texels' plan): every cell whose centre lies within n/2
    cells of the filleted line."""
    from scipy.spatial import cKDTree
    gh, gw = grid_shape(H, W)
    cy, cx = np.mgrid[0:gh, 0:gw]
    ctr = np.stack([(cx.ravel() + 0.5) * CELL, (cy.ravel() + 0.5) * CELL], 1)
    d, _ = cKDTree(curve_line(points, radius)).query(ctr)
    return join4(d.reshape(gh, gw) <= n * CELL / 2.0)


def curve_texels(points, n: int, H: int, W: int, radius: float, seed: int, share: float = 0.95,
                 breathe: float = 0.0, amp=AMP) -> np.ndarray:
    """A desire line (Matt, 27 Oct): a path n cells wide whose straight runs lie on the grid like any
    route and whose one long bend is a smooth arc (Eastward's paths bend smoothly where feet cut a
    corner), its edge lumped like the rest of the soft grid."""
    from scipy.spatial import cKDTree
    yy, xx = np.mgrid[0:H, 0:W]
    tq = np.stack([(xx.ravel() + 0.5) / ctx.D, (yy.ravel() + 0.5) / ctx.D], 1)
    line = curve_line(points, radius, share)
    d, i = cKDTree(line).query(tq)
    hw = np.full(len(line), n * CELL / 2.0)
    if breathe:
        # a natural stream's width breathes (narrows over a shoal, widens in a slack): `breathe` of
        # the half width, on two slow waves along its length (world px)
        sl = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))])
        ph = (seed % 97) * 0.37
        hw = hw * (1.0 + breathe * (0.6 * np.sin(sl / 7.0 + ph) + 0.4 * np.sin(sl / 3.3 + 1.0 + ph)))
    m = d.reshape(H, W) <= hw[i].reshape(H, W)
    return soften(m, seed, r_out=R_TURN_OUT, r_in=R_TURN_IN, amp=amp)


def route_shape(points, n: int, H: int, W: int, seed: int, run: float = 5.0) -> np.ndarray:
    """A path or road on the soft grid: constant width, long runs, wide rounded turns."""
    return shape(cells_route(points, n, H, W, run), H, W, seed, r_out=R_TURN_OUT, r_in=R_TURN_IN)


def join4(m: np.ndarray, cost: np.ndarray | None = None) -> np.ndarray:
    """Where two cells touch only at a corner, add the cheaper of the two cells that join them."""
    m = m.copy()
    for _ in range(3):
        a = m[:-1, :-1] & m[1:, 1:] & ~m[:-1, 1:] & ~m[1:, :-1]
        b = m[:-1, 1:] & m[1:, :-1] & ~m[:-1, :-1] & ~m[1:, 1:]
        if not (a.any() or b.any()):
            break
        for (ys, xs) in zip(*np.nonzero(a)):
            c1, c2 = (ys, xs + 1), (ys + 1, xs)
            pick = c1 if cost is None or cost[c1] <= cost[c2] else c2
            m[pick] = True
        for (ys, xs) in zip(*np.nonzero(b)):
            c1, c2 = (ys, xs), (ys + 1, xs + 1)
            pick = c1 if cost is None or cost[c1] <= cost[c2] else c2
            m[pick] = True
    return m


def cells_rects(rects, H: int, W: int) -> np.ndarray:
    """The cells covered by world-px rectangles [x, y, w, h] (by their centres)."""
    gh, gw = grid_shape(H, W)
    cy, cx = (np.mgrid[0:gh, 0:gw] + 0.5) * CELL
    m = np.zeros((gh, gw), bool)
    for x, y, w, h in rects:
        m |= (cx >= x) & (cx < x + w) & (cy >= y) & (cy < y + h)
    return m


def cells_majority(mask: np.ndarray, share: float = 0.5) -> np.ndarray:
    """A texel mask to cells: a cell is in when at least `share` of its texels are."""
    c = cell_px()
    H, W = mask.shape
    gh, gw = grid_shape(H, W)
    P = np.zeros((gh * c, gw * c), np.float32)
    P[:H, :W] = mask
    return P.reshape(gh, c, gw, c).mean(axis=(1, 3)) >= share


def texels(cells: np.ndarray, H: int, W: int) -> np.ndarray:
    c = cell_px()
    return np.kron(cells.astype(np.uint8), np.ones((c, c), np.uint8)).astype(bool)[:H, :W]


# ------------------------------------------------------------------------------------------------
# 2 to 5. the soft outline
# ------------------------------------------------------------------------------------------------
def _dilate(m, r):
    return ndi.distance_transform_edt(~m) <= r


def _erode(m, r):
    return ndi.distance_transform_edt(m) > r


def round_corners(m: np.ndarray, r_out: float, r_in: float) -> np.ndarray:
    """Inner corners filled with a fillet of radius r_in, then outer corners rounded to r_out
    (texels); exact pixel circles. The canvas edge is not an edge of the shape."""
    p = int(max(r_out, r_in)) + 3
    mp = np.pad(m, p, mode='edge')
    if r_in > 0:
        mp = _erode(_dilate(mp, r_in), r_in)
    if r_out > 0:
        mp = _dilate(_erode(mp, r_out), r_out)
    return mp[p:-p, p:-p]


def lumps(H: int, W: int, seed: int, amp=AMP, lump=LUMP) -> np.ndarray:
    """Smooth displacement in texels: two octaves of value noise whose lumps are `lump` art px
    long, scaled to between amp[0] and amp[1] px deep (varying slowly along the edge)."""
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    v = 0.65 * (2 * TN.vnoise_hd(xx, yy, lump[1] * 0.9, seed) - 1) + \
        0.35 * (2 * TN.vnoise_hd(xx, yy, lump[0] * 1.1, seed + 17) - 1)
    depth = amp[0] + (amp[1] - amp[0]) * TN.vnoise_hd(xx, yy, lump[1] * 3.0, seed + 29)
    return np.clip(v / 0.45, -1.0, 1.0) * depth


def clean(m: np.ndarray, min_area: float = 3.0) -> np.ndarray:
    """No one-texel spurs or bites; specks and pinholes under min_area world px^2 dropped/filled."""
    D = ctx.D
    for _ in range(2):
        m = ndi.binary_closing(np.pad(m, 2, mode='edge'), structure=CROSS)[2:-2, 2:-2]
        m = ndi.binary_opening(np.pad(m, 2, mode='edge'), structure=CROSS)[2:-2, 2:-2]
    lim = int(min_area * D * D)
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, 1 + np.nonzero(sizes >= lim)[0])
    holes = ndi.binary_fill_holes(m) & ~m
    lab, n = ndi.label(holes)
    if n:
        sizes = ndi.sum(holes, lab, range(1, n + 1))
        m |= np.isin(lab, 1 + np.nonzero(sizes < lim)[0])
    return m


def soften(m: np.ndarray, seed: int, r_out: float = R_OUT, r_in: float = R_IN, amp=AMP, lump=LUMP) -> np.ndarray:
    """A blocky texel mask (whole cells) to its soft outline: corners rounded, then lumped."""
    c = cell_px()
    H, W = m.shape
    m = round_corners(m.astype(bool), r_out * c, r_in * c)
    if amp[1] > 0:
        p = 4
        mp = np.pad(m, p, mode='edge')
        # a signed distance that is continuous across the edge (+0.5 on the first texel in, -0.5 on
        # the first texel out), so a lump of 1.5 px moves the edge by one or two texels
        sd = np.where(mp, ndi.distance_transform_edt(mp) - 0.5, 0.5 - ndi.distance_transform_edt(~mp))
        sd = sd[p:-p, p:-p]
        m = sd + lumps(H, W, seed, amp, lump) > 0
    return clean(m)


def shape(cells: np.ndarray, H: int, W: int, seed: int, **kw) -> np.ndarray:
    """The plan (cells) as a soft texel mask."""
    return soften(texels(cells, H, W), seed, **kw)


def path_rim(cv: np.ndarray, m: np.ndarray, turf: np.ndarray) -> None:
    """A path's edge bands: a 1 px darker rim along its lower edges (the dirt where the turf below
    it begins) and a lit lip on the turf along its upper edges."""
    below = np.zeros_like(m)
    below[:-1] = m[1:]
    above = np.zeros_like(m)
    above[1:] = m[:-1]
    rim = m & ~below & (cv % 8 > 0) & (cv % 8 < 6)
    cv[rim] = step(cv[rim], -1)
    lip = turf & ~m & below & (cv % 8 < 5)
    cv[lip] = step(cv[lip], 1)


def soft_patches(H: int, W: int, seed: int, cell: float, share: float = 0.18) -> np.ndarray:
    """Irregular, soft-edged patches covering about `share` of an area: a slow field for where they
    gather, finer octaves for a frayed outline, never a geometric round blob."""
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    v = 0.6 * TN.vnoise_hd(xx, yy, cell, seed) + 0.28 * TN.vnoise_hd(xx, yy, cell / 3.1, seed + 3) + \
        0.12 * TN.vnoise_hd(xx, yy, cell / 8.0, seed + 5)
    thr = np.quantile(v, 1 - share)
    return clean(v > thr, min_area=1.5)


# ------------------------------------------------------------------------------------------------
# 6. breakers
# ------------------------------------------------------------------------------------------------
def edge_points(m: np.ndarray, side: str = 'out') -> np.ndarray:
    """The texels just outside (or inside) a mask's outline."""
    e = ndi.binary_dilation(m, CROSS) & ~m if side == 'out' else m & ~ndi.binary_erosion(m, CROSS)
    return e


def breakers(cv: np.ndarray, m: np.ndarray, rng, share: float = 0.15, kind: str = 'path',
             drawn: np.ndarray | None = None, turf: np.ndarray | None = None) -> None:
    """Break the edge on `share` of its length: on a path, grass tufts leaning in over the edge
    from the turf and pebbles lying on it; on a ledge's lip (kind 'lip'), tufts standing up over the
    rim. Each breaker is a small rounded shape lit at its upper left (no one-texel marks)."""
    D = ctx.D
    out = edge_points(m, 'out')
    if turf is not None:
        out &= turf
    ys, xs = np.nonzero(out)
    if not len(ys):
        return
    H, W = cv.shape
    per = max(4, int(round(3.2 * D)))                 # a breaker covers ~3 world px of edge
    n = int(len(ys) * share / per)
    taken = np.zeros_like(m)
    for k in rng.permutation(len(ys))[:n * 4]:
        if n <= 0:
            break
        y, x = int(ys[k]), int(xs[k])
        if taken[max(0, y - per):y + per, max(0, x - per):x + per].any():
            continue
        r = rng.random()
        if kind == 'path' and r < 0.35:
            # a pebble on the path's edge: a small rounded stone, lit cap, dark foot
            pw, ph = int(rng.integers(3, 6)), int(rng.integers(2, 4))
            for dy in range(ph):
                for dx in range(pw):
                    yy, xx = y + dy - ph // 2, x + dx - pw // 2
                    if not (0 <= yy < H and 0 <= xx < W) or ((dy in (0, ph - 1)) and (dx in (0, pw - 1))):
                        continue
                    t = 4 if (dy == 0 or dx == 0) else (2 if dy == ph - 1 else 3)
                    cv[yy, xx] = C('stone', t)
                    if drawn is not None:
                        drawn[yy, xx] = True
        else:
            # a tuft: three to five blades from the edge, leaning out over it, lit tips
            nb = int(rng.integers(3, 6))
            lean = 1 if rng.random() < 0.5 else -1
            for b in range(nb):
                bx = x + b - nb // 2
                L = int(rng.integers(max(2, int(1.2 * D)), max(3, int(2.4 * D))))
                for j in range(L):
                    yy = y - j if kind == 'lip' else y - j + (1 if m[min(H - 1, y + 1), min(W - 1, max(0, bx))] else 0)
                    xx = bx + (lean * j) // 3
                    if 0 <= yy < H and 0 <= xx < W:
                        cv[yy, xx] = C('grass', 4 if j >= L - 1 else (3 if b % 2 else 2))
                        if drawn is not None:
                            drawn[yy, xx] = True
        taken[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = True
        n -= 1


# ------------------------------------------------------------------------------------------------
# a raised plateau's ledge (eastward-edges.md 2.2, 3)
# ------------------------------------------------------------------------------------------------
def ledge(cv: np.ndarray, top: np.ndarray, face_h: float, rng, seed: int = 0, earth: str = 'earth',
          drawn: np.ndarray | None = None, roots: bool = True) -> np.ndarray:
    """An earth ledge under a raised grass plateau `top` (a soft texel mask), `face_h` world px
    tall, seen from the south: the plateau's lip a darker row of its own grass with a lit row
    behind it, the rim line and the under-lip line (the face's darkest), two rows of under-lip shade
    stepping back up, the face body of rounded clods (wider than tall, lit on their upper left), a
    dark foot band whose lower edge is lumpy too, and the narrow side faces where the plateau ends
    east and west. Returns the face mask."""
    D = ctx.D
    H, W = cv.shape
    fh = int(round(face_h * D))
    # the face: the plateau extruded downwards
    face = np.zeros_like(top)
    for k in range(1, fh + 1):
        face[k:] |= top[:-k]
    face &= ~top
    # its foot lumpy on its own
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    jag = lumps(H, W, seed + 101, (1.0, 2.5), (8.0, 16.0))
    below = np.zeros_like(top)
    for k in range(1, 4):
        below[k:] |= face[:-k]
    face = (face | (below & ~top & (jag > 1.0))) & ~((jag < -1.2) & face & ~np.roll(face, 2, 0))
    face = clean(face & ~top, min_area=1.0)
    # the side faces: a narrow band where the plateau ends east and west, down to the face's foot
    sw = max(3, int(round(2.2 * D)))                 # a side face seen edge-on: about a third of a cell
    hd_ = ndi.binary_dilation(top | face, structure=np.ones((1, 2 * sw + 1), bool))
    side = hd_ & ~top & ~face
    side &= ndi.binary_dilation(top, structure=np.ones((1, 2 * sw + 1), bool)) | \
        ndi.binary_dilation(face, structure=np.ones((1, 2 * sw + 1), bool))
    side = clean(side & ~top & ~face, min_area=0.5)
    # depth into the face from its top (the lip), per column
    dtop = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H):
        run = np.where(face[y], run + 1, 0)
        dtop[y] = run
    dbot = np.zeros((H, W), np.int32)
    run = np.zeros(W, np.int32)
    for y in range(H - 1, -1, -1):
        run = np.where(face[y], run + 1, 0)
        dbot[y] = run
    body = C(earth, 3)
    cv[face] = body
    cv[face & (dtop == 1)] = C(earth, 1)                        # the rim line
    cv[face & (dtop == 2)] = C(earth + '_cool' if earth + '_cool' in FI else earth, 0)   # under-lip, darkest
    cv[face & (dtop >= 3) & (dtop <= 3 + max(1, int(0.6 * D)))] = C(earth, 1)
    cv[face & (dtop > 3 + max(1, int(0.6 * D))) & (dtop <= 4 + int(1.2 * D))] = C(earth, 2)
    footb = face & (dbot <= max(2, int(0.9 * D))) & (dtop > 4)
    cv[footb] = C(earth, 1)
    cv[face & (dbot == 1) & (dtop > 3)] = C(earth + '_cool' if earth + '_cool' in FI else earth, 0)
    # the face's body: knobbly earth, a crowd of small rounded clods (Eastward's forest ledges), each
    # a dome lit at its upper left with its lower right in shade, dark crevices between them
    bodym = (face & (dtop > 3 + max(1, int(0.6 * D))) & (dbot > 1)) | side
    cv[bodym] = C(earth, 1)                                         # the crevices
    rock = face_h >= 24                                            # a cliff (eastward-edges 2.3), not a low ledge
    sz = 2.2 if rock else 1.0                                      # its boulders 8 to 18 px, the ledge's clods smaller
    sx_, sy_ = 2.0 * D * sz, 1.6 * D * sz
    rows = np.arange(-sy_, H + sy_, sy_)
    for j, gy in enumerate(rows):
        for gx in np.arange(-sx_ + (j % 2) * sx_ / 2, W + sx_, sx_):
            cy = gy + rng.uniform(-0.35, 0.35) * sy_
            cx = gx + rng.uniform(-0.35, 0.35) * sx_
            iy, ix = int(cy), int(cx)
            if not (0 <= iy < H and 0 <= ix < W) or not bodym[iy, ix]:
                continue
            rw, rh = rng.uniform(0.95, 1.35) * D * sz, rng.uniform(0.8, 1.1) * D * sz
            y0, y1 = max(0, int(cy - rh - 1)), min(H, int(cy + rh + 2))
            x0, x1 = max(0, int(cx - rw - 1)), min(W, int(cx + rw + 2))
            dy = (yy[y0:y1, x0:x1] - cy) / rh
            dx = (xx[y0:y1, x0:x1] - cx) / rw
            dm = (dx * dx + dy * dy <= 1) & bodym[y0:y1, x0:x1]
            lit = dx * 0.7 + dy * 0.7
            t = np.where(lit < -0.45, 4, np.where(lit < 0.3, 3, 2))
            fam = np.where(t >= 4, FI[earth + '_warm'] if earth + '_warm' in FI else FI[earth], FI[earth])
            sub = cv[y0:y1, x0:x1]
            sub[dm] = (fam * 8 + t)[dm]
    if rock:
        # under the lip a deep shade in two values, ours 4 to 5 world px (Eastward 8 to 11 native in
        # 12), then a zone of horizontal streaks about 6 world px (13 native) before the boulders
        u1 = 3 + int(round(4.5 * D))
        sh = face & (dtop > 2) & (dtop <= u1)
        cv[sh] = C(earth, 1)
        cv[sh & (dtop <= 3 + int(round(2.0 * D)))] = C(earth + '_cool' if earth + '_cool' in FI else earth, 1)
        st = face & (dtop > u1) & (dtop <= u1 + int(round(6 * D))) & (dbot > 2)
        cv[st] = C(earth, 2)
        ys2, xs2 = np.nonzero(st)
        for k in rng.permutation(len(ys2))[:len(ys2) // int(6 * D)]:
            y, x = int(ys2[k]), int(xs2[k])
            L = int(rng.uniform(2.0, 5.0) * D)
            t = 3 if rng.random() < 0.55 else 1
            seg = st[y, x:x + L]
            cv[y, x:x + L][seg] = C(earth, t)
    lipy, lipx = np.nonzero(face & (dtop == 1))
    for k in (rng.permutation(len(lipy))[:max(1, len(lipy) // int(30 * D))] if roots else []):
        x0, y0 = int(lipx[k]), int(lipy[k])
        L = int(rng.uniform(1.5, 4.0) * D)
        x = x0
        for j in range(L):
            y = y0 + j
            if 0 <= y < H and 0 <= x < W and face[y, x] and dbot[y, x] > 2:
                cv[y, x] = C('timber_cool', 2 if j % 3 else 3)
                if drawn is not None:
                    drawn[y, x] = True
            if rng.random() < 0.3:
                x += 1 if rng.random() < 0.5 else -1
    # the side faces: the earth in shade, the west side a step lighter
    sel = side & (cv % 8 > 0) & (cv % 8 < 6)
    cv[sel] = step(cv[sel], -1)                                    # turned from the light, a step down
    # the plateau's lip: the grass's last row a step darker, a lit row one to three rows behind it
    lip = top & np.roll(face | side, -1, 0)
    lip |= top & (np.roll(side, 1, 1) | np.roll(side, -1, 1))
    cv[lip & (cv % 8 < 6)] = step(cv[lip & (cv % 8 < 6)], -1)
    lit = top & ~lip & (np.roll(lip, -1, 0) | np.roll(lip, -2, 0)) & ~np.roll(lip, 0, 0)
    sel = lit & (cv % 8 < 5)
    cv[sel] = step(cv[sel], 1)
    # the lower ground at the foot: a damp contact row
    cont = np.roll(face, 1, 0) & ~face & ~top & ~side
    sel = cont & (cv % 8 < 6) & (cv % 8 > 0)
    cv[sel] = step(cv[sel], -1)
    if drawn is not None:
        drawn |= face | side
    return face | side


def steps(cv: np.ndarray, x0: int, x1: int, y_top: int, y_foot: int, n: int, rng, wood: str = 'timber',
          earth: str = 'earth') -> None:
    """Steps cut into a ledge's face (Eastward's forest steps in Matt's 26 Oct screenshot and the
    farm stair in 13): n treads from the rim down to the foot, each a sawn log or plank lit along its
    front edge and darker on its top's back, over a dark riser; earth cheeks either side carry the
    face's clods down beside the flight. Texel coordinates; the flight is x0..x1, the rim y_top, the
    foot y_foot (the head is flush with the rim, the last tread lands on the ground)."""
    D = ctx.D
    H, W = cv.shape
    cheek = max(3, int(round(1.2 * D)))
    pitch = (y_foot - y_top) / n
    for k in range(n):
        ya = int(round(y_top + k * pitch))
        yb = int(round(y_top + (k + 1) * pitch))
        tread = max(3, int(round(pitch * 0.62)))
        cv[ya:yb, x0 + cheek:x1 - cheek] = C(earth + '_cool' if earth + '_cool' in FI else earth, 0)      # the riser's shade
        for j in range(tread):
            y = ya + j
            t = 4 if j == tread - 1 else (3 if j >= tread // 2 else 2)
            cv[y, x0 + cheek:x1 - cheek] = C(wood, t)
        # the log's grain and its lit west end, a dark east end
        for gx in range(x0 + cheek + 2, x1 - cheek - 2, max(4, int(2.4 * D))):
            gy = ya + int(rng.integers(1, max(2, tread - 1)))
            cv[gy, gx:gx + int(rng.integers(2, 5))] = C(wood, 1)
        cv[ya:ya + tread, x0 + cheek] = C(wood + '_warm' if wood + '_warm' in FI else wood, 4)
        cv[ya:ya + tread, x1 - cheek - 1] = C(wood, 1)
    # the cheeks: knobbly earth, the west one a step lighter
    for (c0, c1, t) in ((x0, x0 + cheek, 3), (x1 - cheek, x1, 2)):
        cv[y_top:y_foot, c0:c1] = C(earth, t)
        for y in range(y_top + 1, y_foot, max(3, int(1.6 * D))):
            cv[y, c0:c1] = C(earth, t - 1)
