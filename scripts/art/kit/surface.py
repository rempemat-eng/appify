"""Width classes and surface variants for the baked ground (docs/world-editor.md, "Widths and
variants"). Matt, 27 Oct 17:05: "not every part of a dirt path should look the same. create a few
variants ... that work in harmony with each other ... also consider what 2 grid block or 3 grid
block etc. wide paths/water etc. look like".

Everything here is drawn over a material that its painter (softground.dirt, lawn, water) has
already painted across its whole outline, so the variants share its palette, clods and edges and
any mix reads as one surface:

- **Width classes**, from each cell's width across the body (the shorter of its row and column
  run): paths 1 (a footpath: one worn line down the middle, the turf close), 2 (a lane), 3 (a road:
  two wheel ruts and a grassy crown), 4+ (a street's approach: compacted, more stones); water 1 (a
  rill), 2 (a stream: stones standing in it), 3 to 5 (a river: shingle on the inside of each bend, a
  scoured deep channel on the outside), 6+ (a wide river or lake: broad lit shallows and lines of
  swell along the shore). Where the width changes along a course the outline is eased over two
  cells (`taper`), so a stream widens into a river rather than stepping.
- **Variants**, one per cell (a plan's `variants` rows; '.' or none picks one): chosen by weight
  and context (near trees, water, doors, routes; a footpath's low traffic), never the same as the
  cell to the west or north (the plain surface may run on), and drawn as a soft blob round the cell, never its square. A slow
  tone field (about 200 texels across) shifts the hue over a whole area, so a long path is never
  stamped.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from scripts.art.native import softground as GD
from scripts.art.native.palette import C, FI, is_fam, sib, step

CELL = 24

# variant letter -> (name, weight); the context rules in `assign` raise or forbid them
VARIANTS = {
    'dirt': {'b': ('plain', 3.0), 'w': ('worn centre', 1.4), 'g': ('grassy verge', 0.6), 's': ('stony', 1.0),
             'd': ('damp, a puddle', 0.5), 'l': ('leaf litter', 0.0), 'c': ('compacted', 0.0)},
    'lawn': {'b': ('calm field', 6.0), 'v': ('clover', 0.6), 'f': ('daisies', 0.5), 'n': ('long grass', 0.6),
             't': ('trampled', 0.0)},
    'water': {'b': ('still', 3.0), 'r': ('rippled', 1.2), 'e': ('reedy', 0.0), 'y': ('lilies', 0.0),
              'o': ('shallow over stones', 0.0)},
}


def widths(cells: np.ndarray, top: int = 8) -> np.ndarray:
    """Per cell of `cells` (bool), the body's width there: the largest k (up to `top`) such that a
    k x k square of the body covers the cell. A junction of two lanes stays a lane, a run three
    cells across is three wide wherever it runs."""
    out = np.where(cells, 1, 0)
    for k in range(2, top + 1):
        st = np.ones((k, k), bool)
        op = ndi.binary_dilation(ndi.binary_erosion(cells, structure=st, border_value=1), structure=st) & cells
        out[op] = k
    return out


def path_class(wd: np.ndarray) -> np.ndarray:
    return np.clip(wd, 0, 4)


def water_class(wd: np.ndarray) -> np.ndarray:
    return np.select([wd >= 6, wd >= 3, wd == 2, wd == 1], [6, 3, 2, 1], 0)


def texels(cells: np.ndarray) -> np.ndarray:
    return np.kron(cells, np.ones((CELL, CELL), bool))


def soft_zone(cells: np.ndarray, seed: int, grow: float = 0.15) -> np.ndarray:
    """A cell set as a soft organic region at texels: blurred and cut on a noisy level, so a
    variant's patch is a blob round its cells, never their squares."""
    H, W = cells.shape[0] * CELL, cells.shape[1] * CELL
    f = ndi.gaussian_filter(texels(cells).astype(float), 7.0)
    return f + (GD.nz(H, W, 14.0, seed) - 0.5) * 0.5 + grow > 0.5


def taper(m: np.ndarray, cells: np.ndarray, cls: np.ndarray) -> np.ndarray:
    """Ease a body's outline where its width class changes along its course: a gaussian over two
    cells round each change, so a stream widens into a river without a step."""
    ch = np.zeros(cls.shape, bool)
    ch[:, 1:] |= (cls[:, 1:] != cls[:, :-1]) & cells[:, 1:] & cells[:, :-1]
    ch[1:, :] |= (cls[1:, :] != cls[:-1, :]) & cells[1:, :] & cells[:-1, :]
    if not ch.any():
        return m
    zone = texels(ndi.binary_dilation(ch, iterations=2))
    sm = ndi.gaussian_filter(m.astype(float), 9.0) > 0.5
    return np.where(zone, sm, m)


def assign(kind: str, cells: np.ndarray, given: np.ndarray | None, ctx_: dict, seed: int) -> np.ndarray:
    """A variant letter per cell of `cells`: the plan's where given, else weighted by context, never
    the same as the west or north neighbour's."""
    rng = np.random.default_rng(seed)
    defs = VARIANTS[kind]
    H, W = cells.shape
    out = np.full((H, W), '', '<U1')
    for y in range(H):
        for x in range(W):
            if not cells[y, x]:
                continue
            g = given[y, x] if given is not None else '.'
            if g in defs:
                out[y, x] = g
                continue
            wts = {k: v[1] for k, v in defs.items()}
            if kind == 'dirt':
                if ctx_['tree'][y, x]:
                    wts['l'] = 3.0
                if ctx_['water'][y, x]:
                    wts['d'] = 2.0
                if ctx_['door'][y, x]:
                    wts['c'] = 4.0
                if ctx_['cls'][y, x] <= 1:
                    wts['g'] = 2.5               # a footpath: low traffic, the turf creeps in
            elif kind == 'lawn':
                if ctx_['route'][y, x]:
                    wts['t'] = 2.0
                if ctx_['water'][y, x] or ctx_['tree'][y, x]:
                    wts['n'] = 3.0
            elif kind == 'water':
                if ctx_['cls'][y, x] <= 2:
                    wts['o'] = 2.0
                if ctx_['shore'][y, x] and ctx_['cls'][y, x] >= 3:
                    wts['e'] = 1.5
                if ctx_['cls'][y, x] >= 6 and ctx_['shore'][y, x]:
                    wts['y'] = 0.8
            for nb in ((y, x - 1), (y - 1, x)):
                if nb[0] >= 0 and nb[1] >= 0 and out[nb] and out[nb] != 'b':
                    wts[out[nb]] = 0.0          # the plain surface may run on; a variant never repeats
            ks = [k for k, v in wts.items() if v > 0]
            if not ks:                   # every weighted one is a neighbour's: the context-only ones
                ban = {out[nb] for nb in ((y, x - 1), (y - 1, x)) if nb[0] >= 0 and nb[1] >= 0}
                wts = {k: 0.5 for k in defs if k not in ban}
                ks = list(wts)
            p = np.array([wts[k] for k in ks])
            out[y, x] = ks[int(rng.choice(len(ks), p=p / p.sum()))]
    return out


def tone_field(cv: np.ndarray, m: np.ndarray, seed: int, scale: float = 200.0) -> None:
    """A slow hue shift over a whole area: the warm sibling where the field is high, the cool one
    where it is low (tones 0 to 5 only), so a long path or a wide lawn never looks stamped."""
    H, W = cv.shape
    f = GD.nz(H, W, scale, seed)
    # only the body sibling moves: the painter's own warm and cool patches keep their contrast
    sel = m & (cv >= 0) & (cv % 8 < 6) & (sib(np.maximum(cv, 0), 'body') == np.maximum(cv, 0))
    hi = sel & (f > 0.66)
    lo = sel & (f < 0.30)
    cv[hi] = sib(cv[hi], 'warm')
    cv[lo] = sib(cv[lo], 'cool')


# ------------------------------------------------------------------------------------------------
# paths
# ------------------------------------------------------------------------------------------------
def path_widths(cv: np.ndarray, net: np.ndarray, cls_t: np.ndarray, seed: int, fam: str = 'path') -> None:
    """The centre treatment of each path class (cls_t: the class per texel)."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    dist = ndi.distance_transform_edt(net)
    wob = (GD.nz(H, W, 16.0, seed + 8) - 0.5) * 3.0
    # 1: a footpath, one worn line down its middle: smooth, a tone lighter in the dry sibling
    one = net & (cls_t == 1)
    if one.any():
        line = one & (dist + wob * 0.5 > 6.5) & (cv % 8 < 5)
        body = line & (sib(np.maximum(cv, 0), 'body') == np.maximum(cv, 0))
        cv[body] = sib(cv[body], 'warm')
    # 3: a road, two wheel ruts and a grassy crown between them
    three = net & (cls_t == 3)
    if three.any():
        rut = three & (np.abs(dist - 17 + wob) < 2.4) & (GD.nz(H, W, 30.0, seed + 9) > 0.3)
        cv[rut] = C(fam + '_cool', 2)
        cv[rut & (GD.nz(H, W, 9.0, seed + 10) > 0.62)] = C(fam + '_cool', 1)
        lip = GD.down(rut, 1) & ~rut & three & (GD.nz(H, W, 5.0, seed + 11) > 0.5)
        cv[lip] = C(fam + '_warm', 4)
        crown = three & (dist > 23)
        gp = crown & (GD.nz(H, W, 6.0, seed + 31) > 0.62) & (GD.nz(H, W, 2.5, seed + 32) > 0.35)
        cv[gp] = C('grass_warm', 2)
        cy_, cx_ = np.nonzero(crown)
        for k in rng.permutation(len(cy_))[: len(cy_) // 140]:
            GD.stamp(cv, int(cy_[k]), int(cx_[k]), GD.tuft_shape(rng, rng.uniform(0.8, 1.3)), C('grass_warm', 2), net)
    # 4+: a street's approach, compacted (the gaps between clods filled) with more stones
    four = net & (cls_t >= 4)
    if four.any():
        gap = four & (cv % 8 == 2) & is_fam(cv, fam) & (GD.nz(H, W, 4.0, seed + 12) > 0.7)
        cv[gap] = cv[gap] + 1
        iy, ix = np.nonzero(four & ndi.binary_erosion(four, iterations=5))
        for _ in range(len(iy) // 900):
            k = int(rng.integers(0, len(iy)))
            GD.pebble(cv, int(iy[k]), int(ix[k]), rng, big=rng.random() < 0.3, ok=net)


def path_variants(cv: np.ndarray, net: np.ndarray, var: np.ndarray, seed: int, fam: str = 'path') -> None:
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    for k, (name, _w) in VARIANTS['dirt'].items():
        cells = var == k
        if k == 'b' or not cells.any():
            continue
        z = soft_zone(cells, seed + ord(k)) & net
        inner = z & ndi.binary_erosion(net, iterations=4)
        if k == 'w':                 # worn centre: dry, the joints half trodden away
            sel = inner & (cv % 8 < 6) & (sib(np.maximum(cv, 0), 'body') == np.maximum(cv, 0))
            cv[sel] = sib(cv[sel], 'warm')
            gap = inner & (cv % 8 == 2) & (GD.nz(H, W, 4.0, seed + 41) > 0.55)
            cv[gap] = cv[gap] + 1
        elif k == 'g':               # the verge creeps in: grass patches and tufts along the earth's edge
            dist_e = ndi.distance_transform_edt(net)
            gp = z & (dist_e < 7 + 3 * GD.nz(H, W, 9.0, seed + 44)) & (GD.nz(H, W, 7.0, seed + 42) > 0.5)
            gp = ndi.binary_opening(gp, structure=np.ones((5, 5), bool))
            cv[gp] = C('grass', 3)
            cv[gp & (GD.nz(H, W, 2.5, seed + 43) > 0.6)] = C('grass', 2)
            ys, xs = np.nonzero(z & (dist_e > 5) & (dist_e < 12))
            for j in rng.permutation(len(ys))[: len(ys) // 220]:
                GD.stamp(cv, int(ys[j]), int(xs[j]), GD.tuft_shape(rng, rng.uniform(0.7, 1.2)), C('grass', 3), net)
        elif k == 's':               # stony: pebble clusters and a larger stone, off the edge
            ys, xs = np.nonzero(z & ndi.binary_erosion(net, iterations=8))
            for _ in range(max(2, len(ys) // 260)):
                j = int(rng.integers(0, len(ys)))
                for _q in range(int(rng.integers(2, 5))):
                    GD.pebble(cv, int(ys[j] + rng.normal(0, 3)), int(xs[j] + rng.normal(0, 4)), rng, big=rng.random() < 0.25, ok=net)
        elif k == 'd':               # damp, a puddle in a hollow
            sel = z & (cv % 8 < 6)
            cv[sel] = sib(cv[sel], 'cool')
            ys, xs = np.nonzero(inner & ndi.binary_erosion(inner, iterations=6))
            if len(ys):
                j = len(ys) // 2
                GD.puddle(cv, int(xs[j]), int(ys[j]), rng.uniform(7, 11), rng.uniform(3.5, 5.5), seed=seed + j)
        elif k == 'l':               # leaf litter under trees
            GD.litter(cv, z, rng, 0.9)
        elif k == 'c':               # compacted near a door: light, the joints mostly closed
            sel = z & (cv % 8 == 2) & (GD.nz(H, W, 4.0, seed + 44) > 0.4)
            cv[sel] = cv[sel] + 1


# ------------------------------------------------------------------------------------------------
# lawn
# ------------------------------------------------------------------------------------------------
def lawn_variants(cv: np.ndarray, turf: np.ndarray, var: np.ndarray, seed: int) -> list:
    from scripts.art.native import ctx
    from scripts.art.native import props as P4
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    D = ctx.D
    items = []
    for k, (name, _w) in VARIANTS['lawn'].items():
        cells = var == k
        if k == 'b' or not cells.any():
            continue
        z = soft_zone(cells, seed + ord(k), grow=0.0) & turf
        ys, xs = np.nonzero(z)
        if not len(ys):
            continue
        if k == 'v':                 # clover: trefoils laid into the lawn in patches
            for _ in range(len(ys) // 160):
                j = int(rng.integers(0, len(ys)))
                qy, qx = ys[j], xs[j]
                for (dy, dx) in ((-1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (0, 0), (1, 0)):
                    yy_, xx_ = qy + dy, qx + dx
                    if 0 <= yy_ < H and 0 <= xx_ < W and turf[yy_, xx_]:
                        cv[yy_, xx_] = C('leaf', 4) if (dy, dx) in ((-1, -1), (-1, 0)) else (C('leaf', 2) if (dy, dx) == (1, 0) else C('leaf', 3))
        elif k == 'f':               # daisies in small groups (laid in as pictures: the caller pastes them)
            for _ in range(max(1, len(ys) // 2500)):
                j = int(rng.integers(0, len(ys)))
                img = P4.flowers4(D, int(rng.integers(0, 10 ** 6)), kind='white', n=int(rng.integers(2, 5)))
                a = np.asarray(img)[..., 3] > 0
                if a.any():
                    bx = np.nonzero(a.any(0))[0]
                    by = np.nonzero(a.any(1))[0]
                    items.append((img, ((bx[0] + bx[-1]) / 2.0, by[-1]), (int(xs[j]), int(ys[j]))))
        elif k == 'n':               # long grass: the cool sibling, dense tufts with dark roots
            sel = z & (cv % 8 < 6) & (GD.nz(H, W, 9.0, seed + 51) > 0.4)
            cv[sel] = sib(cv[sel], 'cool')
            for j in rng.permutation(len(ys))[: len(ys) // 170]:
                GD.stamp(cv, int(ys[j]), int(xs[j]), GD.tuft_shape(rng, rng.uniform(0.9, 1.5)), C('grass_cool', 2), turf)
        elif k == 't':               # trampled beside a route: short, lighter, a bare speck or two
            sel = z & (cv % 8 < 4) & (GD.nz(H, W, 6.0, seed + 52) > 0.45)
            cv[sel] = sib(cv[sel], 'warm')
            for j in rng.permutation(len(ys))[: len(ys) // 700]:
                cv[ys[j], xs[j]] = C('earth_warm', 3)
    return items


# ------------------------------------------------------------------------------------------------
# water
# ------------------------------------------------------------------------------------------------
def water_widths(cv: np.ndarray, wm: np.ndarray, wcells: np.ndarray, cls: np.ndarray, seed: int) -> list:
    """Stones standing in a stream; shingle on the inside of a river's bends and a scoured deep
    channel on the outside; broad shallows and swell lines along a wide river's or lake's shore.
    Returns sprites (stones) to lay into the ground."""
    from scripts.art.native import ctx
    from scripts.art.native import props as P4
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    D = ctx.D
    items = []
    inner = wm & ndi.binary_erosion(wm, iterations=5)
    R, Cc = wcells.shape
    # 2: a stream, a stone standing in it every few cells, a ring of lit water round its foot
    for y in range(R):
        for x in range(Cc):
            if cls[y, x] == 2 and rng.random() < 0.22:
                cy, cx = int((y + rng.uniform(0.3, 0.8)) * CELL), int((x + rng.uniform(0.3, 0.7)) * CELL)
                if 0 <= cy < H and 0 <= cx < W and inner[cy, cx]:
                    w_ = rng.uniform(4.0, 6.5)
                    img, anc, _a = P4.boulder4(D, w_, w_ * 0.6, seed=int(rng.integers(0, 10 ** 6)), moss='top' if rng.random() < 0.5 else None)
                    y0, y1, x0, x1 = max(0, cy - 12), min(H, cy + 12), max(0, cx - 24), min(W, cx + 24)
                    ly, lx = np.mgrid[y0:y1, x0:x1]
                    ring = ((lx - cx) / (w_ * D * 0.7)) ** 2 + ((ly - cy) / (w_ * D * 0.3)) ** 2
                    rs = wm[y0:y1, x0:x1] & (ring <= 1.0) & (ring > 0.55)
                    sub = cv[y0:y1, x0:x1]
                    sub[rs] = step(sub[rs], 1)
                    items.append((img, anc, (cx, cy)))
    # 3 to 5: bends. A land cell with water on two adjacent sides and the diagonal between them
    # is the inside of a bend: shingle there; the far side of the bend scours a deep channel
    yy, xx = np.mgrid[0:H, 0:W]
    for y in range(1, R - 1):
        for x in range(1, Cc - 1):
            if wcells[y, x]:
                continue
            for dy, dx in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if not (wcells[y + dy, x] and wcells[y, x + dx] and wcells[y + dy, x + dx]):
                    continue
                if wcells[y - dy, x] or wcells[y, x - dx]:
                    continue                     # not a corner of the land: no bend here
                # a bend, not a meander's one-cell step: the water runs along both sides of the
                # corner for two cells or more
                ok = True
                for k in (1, 2):
                    a1, a2 = (y - k * dy, x + dx), (y + dy, x - k * dx)
                    for (qy, qx) in (a1, a2):
                        if not (0 <= qy < R and 0 <= qx < Cc and wcells[qy, qx]):
                            ok = False
                if not ok:
                    continue
                if min(cls[y + dy, x], cls[y, x + dx], cls[y + dy, x + dx]) < 3:
                    continue                     # a river's bend, not a stream's jog
                # the bend's inner corner at the shared vertex
                vx, vy = (x + (dx > 0)) * CELL, (y + (dy > 0)) * CELL
                d = np.hypot(xx - vx, yy - vy)
                # a rounded bar lying along the inside of the bend, off its corner into the water
                bx, by = vx + dx * 3, vy + dy * 3
                e = ((xx - bx) * 0.7071 * (dx * dy) + (yy - by) * 0.7071) ** 2 / 7.0 ** 2 + \
                    ((xx - bx) * 0.7071 - (yy - by) * 0.7071 * (dx * dy)) ** 2 / 19.0 ** 2
                bar = wm & (e + (GD.nz(H, W, 5.0, seed + x * 7 + y) - 0.5) * 0.6 < 1.0)
                cv[bar] = C('sand_cool', 3)
                cv[bar & (GD.nz(H, W, 2.2, seed + 3) > 0.55)] = C('stone', 3)
                cv[bar & (GD.nz(H, W, 2.2, seed + 5) > 0.7)] = C('stone_cool', 2)
                cv[bar & (GD.nz(H, W, 2.2, seed + 4) > 0.75)] = C('stone_warm', 4)
                edge = bar & ~ndi.binary_erosion(bar, iterations=1)
                cv[edge] = C('water', 4)
                far = wm & (d > 34) & (d < 58) & ((xx - vx) * dx > 0) & ((yy - vy) * dy > 0) & ~bar
                sc = far & ((xx + yy) % 2 == 0) & (d > 40) & (d < 52)
                cv[sc & (cv % 8 > 0)] = step(cv[sc & (cv % 8 > 0)], -1)
    # 6+: a wide river or a lake: broad lit shallows and swell lines along the shore
    wide = texels(cls >= 6) & wm
    if wide.any():
        dist = ndi.distance_transform_edt(wm)
        sh = wide & (dist <= 9 + 4 * GD.nz(H, W, 18.0, seed + 61)) & (cv % 8 < 5)
        cv[sh] = step(cv[sh], 1)
        for r_ in (13, 19):
            sw = wide & (np.abs(dist - r_ - 2 * GD.nz(H, W, 20.0, seed + r_)) < 0.6) & (GD.nz(H, W, 11.0, seed + 70 + r_) > 0.5)
            cv[sw] = step(cv[sw], 1)
    return items


def water_variants(cv: np.ndarray, wm: np.ndarray, var: np.ndarray, seed: int) -> None:
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    inner = wm & ndi.binary_erosion(wm, iterations=4)
    for k, (name, _w) in VARIANTS['water'].items():
        cells = var == k
        if k == 'b' or not cells.any():
            continue
        z = soft_zone(cells, seed + ord(k)) & inner
        ys, xs = np.nonzero(z)
        if not len(ys):
            continue
        if k == 'r':                 # rippled: short lit lines across the flow, a dark texel under
            for _ in range(len(ys) // 160):
                j = int(rng.integers(0, len(ys)))
                y, x, L = ys[j], xs[j], int(rng.integers(4, 10))
                for q in range(L):
                    if x + q < W and z[y, x + q]:
                        cv[y, x + q] = step(cv[y, x + q], 2 if 0 < q < L - 1 else 1)
                        if y + 1 < H and wm[y + 1, x + q]:
                            cv[y + 1, x + q] = step(cv[y + 1, x + q], -1)
        elif k == 'e':               # reedy: clumps of reeds in the shallows by the shore
            dshore = ndi.distance_transform_edt(wm)
            sy, sx = np.nonzero(z & (dshore > 3) & (dshore < 8))
            for _ in range(min(2, max(1, len(sy) // 400))):
                if not len(sy):
                    break
                j = int(rng.integers(0, len(sy)))
                GD.reed_clump(cv, int(sy[j]), int(sx[j]), rng)
        elif k == 'y':               # lilies on still water
            j0 = int(rng.integers(0, len(ys)))          # one raft of three to six pads
            for _ in range(int(rng.integers(3, 7))):
                y_, x_ = int(ys[j0] + rng.normal(0, 4)), int(xs[j0] + rng.normal(0, 7))
                if 0 <= y_ < H and 0 <= x_ < W and z[y_, x_]:
                    GD.lily(cv, y_, x_, rng, z)
        elif k == 'o':               # shallow over stones: the stones showing through, lit tops
            for _ in range(len(ys) // 90):
                j = int(rng.integers(0, len(ys)))
                y, x = ys[j], xs[j]
                rw, rh = int(rng.integers(2, 4)), int(rng.integers(1, 3))
                blk = (slice(max(0, y - rh), y + rh), slice(max(0, x - rw), x + rw))
                sel = z[blk]
                sub = cv[blk]
                sub[sel] = step(sub[sel], 1)
                cv[blk] = sub
                if y - rh >= 0 and z[y - rh, x]:
                    cv[y - rh, x] = step(cv[y - rh, x], 1)
