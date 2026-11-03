"""Shared drawing tools for the prop sets (density 3: a cell is 24 texels, an adult 74).

**The ray renderer.** A prop is built from solids in ground texels (x east, y south, z up) and seen
in the house's three-quarter view: a point (x, y, z) lands on the picture at (x, y - z). Through a
picture texel (sx, sy) runs the line y = sy + z; the solid seen there is the one met at the
greatest z on that line (the most southern, the nearest the eye). Each solid is solved exactly on
that line, so stones are round where they turn and boxes show their top and front faces, and the
texel keeps the solid's label, its surface normal and where on the solid it was hit. Shading is
the house light (scripts/art/native/village.py LIGHT: from the upper left) on that normal, stepped
on the solid's own (cool, body, warm) ramps; the lit rim, the crevice under each stone and the
outline in each material's own edge tone follow (house-style 2 to 4).

Solids: `box` (axis-aligned, an optional rounding of its top edges), `ellipsoid`, `cylinder`
(upright). Labels are the solids' indices; `Scene.owner` lets a modular piece keep only the texels
its own cell wins, as the fence cells do (scripts/art/kit/fences.py).

**The tone measure** (`tones`): distinct colours (binned in 16s per channel) in each 16 x 16 patch
at least 80 % covered, averaged; with no such patch, the best 16 x 16 window (stride 2, at least 70 %
covered) marked "w". This is how the editor-props pass (PR #430) measured its pieces.
"""
from __future__ import annotations

import math
import os

import numpy as np
from scipy import ndimage as ndi

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.native import village as V
from scripts.art.native.palette import FI, to_rgba

LIGHT = np.array(V.LIGHT, float)
LIGHT = LIGHT / np.linalg.norm(LIGHT)
CELL = 24


def C(fam, t):
    return FI[fam] * 8 + int(max(0, min(5, round(t))))


def hsh(*v) -> float:
    """A deterministic hash of integers to 0..1 (never Python's salted hash())."""
    h = 2166136261
    for x in v:
        h = ((h ^ (int(x) & 0xffffffff)) * 16777619) & 0xffffffff
        h ^= h >> 13
    return (h & 0xffff) / 65535.0


def rpaint(a, m, sets, t, mix):
    """Paint mask m with float tones t (0..5) in one of several (cool, body, warm) triples chosen
    per texel by mix (0..1): hue shifts across one material."""
    t = np.clip(np.round(np.broadcast_to(np.asarray(t, float), m.shape)), 0, 5).astype(int)
    mix = np.broadcast_to(np.asarray(mix, float), m.shape)
    k = np.clip((mix * len(sets)).astype(int), 0, len(sets) - 1)
    fam = np.zeros(m.shape, int)
    for i, (cool, body, warm) in enumerate(sets):
        f = np.where(t >= 4, FI[warm], np.where(t <= 1, FI[cool], FI[body]))
        fam = np.where(k == i, f, fam)
    a[m] = (fam * 8 + t)[m]


def noise(shape, rng, sigma=1.0):
    n = ndi.gaussian_filter(rng.random(shape), sigma)
    return (n - n.min()) / max(1e-6, n.max() - n.min())


# ------------------------------------------------------------------------------------------------
# the ray renderer
# ------------------------------------------------------------------------------------------------
class Solid:
    __slots__ = ('kind', 'p', 'sets', 'base', 'k', 'owner', 'tag', 'mix', 'tex')

    def __init__(self, kind, p, sets, base=3.0, k=1.6, owner=0, tag='', mix=None, tex=None):
        self.kind, self.p, self.sets, self.base, self.k, self.owner, self.tag = kind, p, sets, base, k, owner, tag
        self.mix = mix
        self.tex = tex


def vhash(x, y, seed=0):
    """A vectorised hash of integer arrays to 0..1 (deterministic)."""
    h = (np.asarray(x, np.int64) * 73856093) ^ (np.asarray(y, np.int64) * 19349663) ^ (int(seed) * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xffff) / 65535.0


def texture(kind, X, Y, seed):
    """A surface's grain in tone steps, in clusters of two texels or more (art-style: no single-pixel
    noise): 'stone' pits and grains, 'wood' (boards along x) or 'wood_v' (along y on the picture)
    streaks and knots, 'turf' fibres."""
    X = np.asarray(X).astype(np.int64)
    Y = np.asarray(Y).astype(np.int64)
    if kind == 'stone':
        n = vhash(X // 2, Y // 2, seed)
        m = vhash((X + 1) // 3, (Y + 1) // 2, seed + 1)
        return np.where(n > 0.86, -1.0, np.where(m > 0.88, 0.8, 0.0))
    if kind == 'wood':
        row = vhash(Y, Y // 3, seed)
        streak = vhash(X // 6 + (Y * 7), Y, seed + 2)
        return np.where(streak > 0.82, -1.0, np.where(row > 0.75, 0.5, 0.0)) + np.where((X + Y * 3) % 17 == 0, -0.6, 0.0)
    if kind == 'wood_v':
        col = vhash(X, X // 3, seed)
        streak = vhash(Y // 6 + X * 7, X, seed + 2)
        return np.where(streak > 0.82, -1.0, np.where(col > 0.75, 0.5, 0.0))
    if kind == 'turf':
        n = vhash(X // 2, Y, seed)
        return np.where(n > 0.8, -1.0, np.where(n < 0.12, 0.9, 0.0))
    return 0.0


class Scene:
    """Solids in ground texels about an origin (the piece's foot), rendered onto a canvas whose
    texel (ox, oy) is the ground point (0, 0) at z = 0."""

    def __init__(self, x0, x1, y0, y1, zmax):
        self.x0, self.x1, self.y0, self.y1, self.zmax = int(x0), int(x1), int(y0), int(y1), int(zmax)
        self.W = self.x1 - self.x0
        self.H = self.y1 - self.y0 + self.zmax
        self.ox, self.oy = -self.x0, self.zmax - self.y0
        self.solids: list[Solid] = []
        self.clip = None                  # (x0, y0, x1, y1): see only solid ground inside this box

    # solids -------------------------------------------------------------------------------------
    def box(self, x0, y0, z0, x1, y1, z1, sets, base=3.0, k=1.6, owner=0, tag='', round_=0.0, mix=None, tex=None):
        self.solids.append(Solid('box', (x0, y0, z0, x1, y1, z1, round_), sets, base, k, owner, tag, mix, tex))
        return len(self.solids) - 1

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, sets, base=3.0, k=1.8, owner=0, tag='', mix=None, flat=1.0, tex=None):
        """flat > 1 shades it as a block with rounded arrises (a superellipsoid's normals): its faces
        flat and evenly lit, turning only near its edges; the outline stays the ellipsoid's."""
        self.solids.append(Solid('ell', (cx, cy, cz, rx, ry, rz, flat), sets, base, k, owner, tag, mix, tex))
        return len(self.solids) - 1

    def cylinder(self, cx, cy, r, z0, z1, sets, base=3.0, k=1.6, owner=0, tag='', mix=None, tex=None):
        self.solids.append(Solid('cyl', (cx, cy, r, z0, z1), sets, base, k, owner, tag, mix, tex))
        return len(self.solids) - 1

    # rendering ----------------------------------------------------------------------------------
    def _hit(self, s: Solid):
        """(rows, cols, z, nx, ny, nz) of every canvas texel this solid is seen on, at its nearest."""
        if s.kind == 'box':
            x0, y0, z0, x1, y1, z1, rnd = s.p
            cx0, cx1 = int(math.floor(x0)) + self.ox, int(math.ceil(x1)) + self.ox
            sy0, sy1 = int(math.floor(y0 - z1)) + self.oy, int(math.ceil(y1 - z0)) + self.oy
        elif s.kind == 'ell':
            cx, cy, cz, rx, ry, rz, _f = s.p
            cx0, cx1 = int(math.floor(cx - rx)) + self.ox, int(math.ceil(cx + rx)) + self.ox
            sy0, sy1 = int(math.floor(cy - ry - cz - rz)) + self.oy, int(math.ceil(cy + ry - max(0.0, cz - rz))) + self.oy
        else:
            cx, cy, r, z0, z1 = s.p
            cx0, cx1 = int(math.floor(cx - r)) + self.ox, int(math.ceil(cx + r)) + self.ox
            sy0, sy1 = int(math.floor(cy - r - z1)) + self.oy, int(math.ceil(cy + r - z0)) + self.oy
        cx0, cx1 = max(0, cx0), min(self.W, cx1 + 1)
        sy0, sy1 = max(0, sy0), min(self.H, sy1 + 1)
        if cx1 <= cx0 or sy1 <= sy0:
            return None
        R, Cc = np.mgrid[sy0:sy1, cx0:cx1]
        X = Cc - self.ox + 0.5            # ground x of the texel's centre
        Sy = R - self.oy + 0.5            # y - z on the line through it
        if s.kind == 'box':
            x0, y0, z0, x1, y1, z1, rnd = s.p
            inx = (X >= x0) & (X < x1)
            lo = np.maximum(z0, y0 - Sy)
            hi = np.minimum(z1, y1 - Sy)
            if self.clip is not None:
                inx &= (X >= self.clip[0]) & (X < self.clip[2])
                lo = np.maximum(lo, self.clip[1] - Sy)
                hi = np.minimum(hi, self.clip[3] - Sy - 1e-6)
            ok = inx & (hi >= lo) & (hi >= 0)
            z = hi
            top = ok & (z == z1)
            nx = np.zeros_like(X)
            ny = np.where(top, 0.0, 1.0)
            nz = np.where(top, 1.0, 0.0)
            if rnd > 0:
                # the top's arrises rounded: the top tilts toward its west, east and south edges
                ex = np.clip((x0 + rnd - X) / rnd, 0, 1) - np.clip((X - (x1 - rnd)) / rnd, 0, 1)
                ys = Sy + z
                es = np.clip((ys - (y1 - rnd)) / rnd, 0, 1) - np.clip((y0 + rnd - ys) / rnd, 0, 1)
                nx = np.where(top, -0.8 * ex, nx)
                ny = np.where(top, 0.8 * es, ny)
                nz = np.where(top, 1.0 - 0.5 * (np.abs(ex) + np.abs(es)), nz)
                # and the front's upper arris turns up
                ez = np.clip((z - (z1 - rnd)) / rnd, 0, 1)
                ny = np.where(~top, 1.0 - 0.5 * ez, ny)
                nz = np.where(~top, 0.8 * ez, nz)
                nx = np.where(~top, -0.8 * ex, nx)
        elif s.kind == 'ell':
            cx, cy, cz, rx, ry, rz, flat = s.p
            A = 1.0 / ry ** 2 + 1.0 / rz ** 2
            B = 2.0 * (Sy - cy) / ry ** 2 - 2.0 * cz / rz ** 2
            Cq = ((X - cx) / rx) ** 2 + (Sy - cy) ** 2 / ry ** 2 + cz ** 2 / rz ** 2 - 1.0
            disc = B * B - 4 * A * Cq
            ok = disc >= 0
            z = (-B + np.sqrt(np.maximum(disc, 0))) / (2 * A)
            if self.clip is not None:
                zl = (-B - np.sqrt(np.maximum(disc, 0))) / (2 * A)
                z = np.minimum(z, self.clip[3] - Sy - 1e-6)
                ok &= (z >= zl) & (z >= self.clip[1] - Sy) & (X >= self.clip[0]) & (X < self.clip[2])
            ok &= z >= 0
            yy = Sy + z
            u, v, w = (X - cx) / rx, (yy - cy) / ry, (z - cz) / rz
            if flat != 1.0:
                u, v, w = np.sign(u) * np.abs(u) ** flat, np.sign(v) * np.abs(v) ** flat, np.sign(w) * np.abs(w) ** flat
            nx, ny, nz = u / rx, v / ry, w / rz
        else:
            cx, cy, r, z0, z1 = s.p
            d2 = r * r - (X - cx) ** 2
            ok = d2 >= 0
            h = np.sqrt(np.maximum(d2, 0))
            hi = np.minimum(z1, cy + h - Sy)
            lo = np.maximum(z0, cy - h - Sy)
            if self.clip is not None:
                ok &= (X >= self.clip[0]) & (X < self.clip[2])
                lo = np.maximum(lo, self.clip[1] - Sy)
                hi = np.minimum(hi, self.clip[3] - Sy - 1e-6)
            ok &= (hi >= lo) & (hi >= 0)
            z = hi
            top = ok & (z == z1)
            yy = Sy + z
            nx = np.where(top, 0.0, (X - cx) / r)
            ny = np.where(top, 0.0, (yy - cy) / r)
            nz = np.where(top, 1.0, 0.0)
        n = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        return R[ok], Cc[ok], z[ok], (nx / n)[ok], (ny / n)[ok], (nz / n)[ok], (Sy + z)[ok]

    def render(self):
        """Fill the maps: depth (z of the nearest hit), label, normal, ground y of the hit."""
        H, W = self.H, self.W
        self.depth = np.full((H, W), -1e9)
        self.label = np.full((H, W), -1, int)
        self.n = np.zeros((H, W, 3))
        self.gy = np.zeros((H, W))
        for i, s in enumerate(self.solids):
            hit = self._hit(s)
            if hit is None:
                continue
            r, c, z, nx, ny, nz, gy = hit
            # nearest wins: the greater z on the line; a later solid wins a tie (laid on top)
            win = z >= self.depth[r, c] - 1e-6
            r, c = r[win], c[win]
            self.depth[r, c] = z[win]
            self.label[r, c] = i
            self.n[r, c] = np.stack([nx[win], ny[win], nz[win]], -1)
            self.gy[r, c] = gy[win]
        return self

    def light(self):
        """-1 .. 1: the house light on each texel's normal."""
        return self.n @ LIGHT

    def shade(self, crevice=2, rim=0.7):
        """Codes for every texel: each solid's base tone plus k times the light, stepped on its ramps;
        the lit rim along each solid's upper west edge; a crevice where a solid tucks under the one
        in front of it (the texel below belongs to a nearer solid)."""
        H, W = self.H, self.W
        a = np.full((H, W), -1, np.int32)
        L = self.light()
        lab = self.label
        up = np.full_like(lab, -1)
        up[1:] = lab[:-1]
        lf = np.full_like(lab, -1)
        lf[:, 1:] = lab[:, :-1]
        dn = np.full_like(lab, -1)
        dn[:-1] = lab[1:]
        rt = np.full_like(lab, -1)
        rt[:, :-1] = lab[:, 1:]
        dd = np.full_like(self.depth, -1e9)
        dd[:-1] = self.depth[1:]
        for i, s in enumerate(self.solids):
            m = lab == i
            if not m.any():
                continue
            t = s.base + s.k * L
            if s.tex:
                Hh, Ww = lab.shape
                Xs = np.arange(Ww)[None, :] - self.ox + np.zeros((Hh, 1))
                t = t + texture(s.tex, Xs, np.arange(Hh)[:, None] - self.oy + np.zeros((1, Ww)), i * 7 + 3)
            edge_t = m & (up != i)
            edge_l = m & (lf != i)
            t = np.where(edge_t & (self.n[..., 2] > 0.2), t + rim, t)
            t = np.where(edge_l & ~edge_t & (self.n[..., 0] < 0.3), t + 0.5 * rim, t)
            under = m & (dn != i) & (dn >= 0) & (dd > self.depth + 0.5)
            t = np.where(under, t - crevice, t)
            t = np.where(m & (rt != i) & (rt >= 0), t - 0.6 * crevice, t)
            mix = s.mix if s.mix is not None else hsh(i, 7)
            rpaint(a, m, s.sets, t, mix)
        self.a = a
        return a

    def owners(self):
        o = np.full(self.label.shape, -1, int)
        for i, s in enumerate(self.solids):
            o[self.label == i] = s.owner
        return o

    def ground_owners(self, box):
        """0 where the texel's hit lies on ground inside box (x0, y0, x1, y1), 1 elsewhere: a
        modular piece keeps the texels whose ground its own cell holds."""
        H, W = self.label.shape
        X = np.arange(W)[None, :] - self.ox + 0.5
        x0, y0, x1, y1 = box
        inside = (X >= x0) & (X < x1) & (self.gy >= y0) & (self.gy < y1)
        return np.where(self.label >= 0, np.where(inside, 0, 1), -1)


def despeckle(a, keep=None, size=2, passes=2):
    """Clean clusters (Claude A, round 2: "clean 2 to 4 px clusters rather than single-pixel
    speckle"): a run of one colour of `size` texels or fewer (four-connected) takes the colour most
    of its neighbours share. `keep` protects texels that must stay (eyes, glints, lettering)."""
    H, W = a.shape
    for _ in range(passes):
        changed = False
        for v in np.unique(a[a >= 0]):
            lab, n = ndi.label(a == v)
            if n == 0:
                continue
            sizes = np.bincount(lab.ravel())
            small = np.nonzero(sizes[1:] <= size)[0] + 1
            if not len(small):
                continue
            sm = np.isin(lab, small)
            if keep is not None:
                sm &= ~keep
            ys, xs = np.nonzero(sm)
            for y, x in zip(ys, xs):
                nb = [a[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                      if 0 <= yy < H and 0 <= xx < W and a[yy, xx] >= 0 and a[yy, xx] != v]
                if nb:
                    a[y, x] = max(set(nb), key=nb.count)
                    changed = True
        if not changed:
            break
    return a


def modular(sc, box, dress=None):
    """A modular piece's picture (fences.py's cell model) from its neighbourhood scene: the texels
    where its own solids, cut at its ground box, are seen (so a placed neighbour drawn after it by
    the zone's foot order covers what the neighbour hides, and nothing is left open between them),
    coloured as the whole neighbourhood shows them where it shows them, and the neighbourhood's
    outline where it closes this piece's texels. dress(scene, codes) adds marks tied to solids."""
    import copy
    sc.clip = None
    sc.render()
    aF = sc.shade()
    if dress:
        dress(sc, aF)
    V.tidy(aF)
    despeckle(aF)
    O = copy.copy(sc)
    O.clip = box
    O.render()
    aO = O.shade()
    if dress:
        dress(O, aO)
    V.tidy(aO)
    despeckle(aO)
    H, W = aF.shape
    X = np.arange(W)[None, :] - sc.ox + 0.5
    insideF = (X >= box[0]) & (X < box[2]) & (sc.gy >= box[1]) & (sc.gy < box[3])
    mine = O.label >= 0
    a = np.where(mine, np.where((sc.label == O.label) & insideF, aF, aO), -1).astype(np.int32)
    # the outline: the neighbourhood's where it closes this piece's texels, and this piece's own
    # where nothing of the neighbourhood lies beyond it
    oF = aF.copy()
    V.outline(oF)
    edgeF = (oF >= 0) & (aF < 0)
    near = ndi.binary_dilation(mine, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool))
    a = np.where(edgeF & near & ~mine, oF, a)
    oO = a.copy()
    V.outline(oO)
    extra = (oO >= 0) & (a < 0) & (aF < 0) & ~edgeF
    a = np.where(extra, oO, a)
    return a


def outline_owned(a, owner):
    """Close the silhouette (V.outline) and give every outline texel to the owner of the texel it
    closes; returns the new owner map."""
    before = a >= 0
    V.outline(a)
    new = (a >= 0) & ~before
    if new.any():
        idx = ndi.distance_transform_edt(~before, return_distances=False, return_indices=True)
        o2 = owner[idx[0], idx[1]]
        owner = np.where(new, o2, owner)
    return owner


def crop(a, ox, oy):
    """A Pic of the opaque part of a code canvas, its foot at canvas (ox, oy)."""
    ys, xs = np.nonzero(a >= 0)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    p = V.Pic(x1 - x0, y1 - y0, ox - x0, oy - y0)
    p.a[:] = a[y0:y1, x0:x1]
    return p


def strip(frames):
    w, h = frames[0].W, frames[0].H
    s = np.full((h, w * len(frames)), -1, np.int32)
    for k, f in enumerate(frames):
        assert (f.W, f.H) == (w, h)
        s[:, k * w:(k + 1) * w] = f.a
    return s


def grid(a):
    return np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(float)


# ------------------------------------------------------------------------------------------------
# the tone measure (PR #430's)
# ------------------------------------------------------------------------------------------------
def tones(rgba: np.ndarray, patch=16, cover=0.8, wcover=0.7):
    """(mean distinct tones per covered 16 x 16 patch, number of patches, window flag)."""
    al = rgba[..., 3] > 0
    q = (rgba[..., :3] // 16).astype(int)
    key = (q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2])
    H, W = al.shape
    vals = []
    for y in range(0, H - patch + 1, patch):
        for x in range(0, W - patch + 1, patch):
            m = al[y:y + patch, x:x + patch]
            if m.mean() >= cover:
                vals.append(len(np.unique(key[y:y + patch, x:x + patch][m])))
    if vals:
        return float(np.mean(vals)), len(vals), False
    best = 0
    for y in range(0, max(1, H - patch + 1), 2):
        for x in range(0, max(1, W - patch + 1), 2):
            m = al[y:y + patch, x:x + patch]
            if m.size and m.mean() >= wcover:
                best = max(best, len(np.unique(key[y:y + patch, x:x + patch][m])))
    return float(best), 0, True


def rgba_of(a):
    return to_rgba(a)


def relpath(p, root):
    return os.path.relpath(p, root)
