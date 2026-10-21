"""The floor of a native screen, its light and its shadows, kept as palette codes.

The terrain (native.terrain) arrives as family ids and tones per texel (the cliff core's F, T).
Everything here moves pixels along their own ramp or swaps to a sibling, never mixes colours
(house-style 1): sun is a tone up on the floor's warm sibling, shade a tone or two down, a cast
shadow two tones down in its core and one in its rim, a contact line tone 1.

    g = Floor(terrain, biome, density)
    g.calm()                      # the cliff core's lawn, its stray light pools taken out
    g.patch(mask, family, tone)   # a place on the floor (a glade's grass, the ring's turf)
    g.sun(mask)                   # a light pool with a checker fade (dither only for light)
    g.litter(points, seed)        # leaf litter in clusters round the trees' feet
    g.shadow(mask)                # a cast shadow (core and rim)
    g.contact(mask)               # contact lines
    img = g.image()
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from . import style as ST
from . import terrain as TR

cc = TR.cc
FID = cc.FID
LUT = cc.LUT


def fid(name):
    return FID[name]


def sibs(name):
    return [FID[name], FID[name + '_warm'], FID[name + '_cool']]


class Floor:
    def __init__(self, t: 'TR.Terrain', biome: dict):
        self.t = t
        self.B = biome
        self.s = t.density
        self.F = t.F.copy()
        self.T = t.T.copy()
        self.tag = t.tag
        H, W = self.F.shape
        self.H, self.W = H, W
        self.Y, self.X = np.mgrid[0:H, 0:W]
        floor = biome['ground']['floor']
        self.floor_ids = sibs(floor)
        self.open = (t.tag == cc.TAG['ground']) & np.isin(self.F, self.floor_ids) & (t.kind == cc.TOP)
        self.locked = np.zeros((H, W), bool)
        self.shadow_mask = np.zeros((H, W), np.int8)     # the layer export: 2 core, 1 rim
        self.light_mask = np.zeros((H, W), np.int8)

    # -- the floor --------------------------------------------------------------------------------
    def calm(self):
        """The cliff core's lawn is the field: one tone, broad sibling patches, a few patches a
        tone darker. Its light pools come out (light is placed by the screen, where the light
        is), so no ground pixel is tone 4 or 5 except where this module puts light."""
        lit = self.open & (self.T >= 4)
        self.T[lit] = 3
        self.F[lit] = self.floor_ids[0]

    def patch(self, mask, family, tone=3, sib_noise=None):
        m = mask & self.open
        if sib_noise is not None:
            ids = sibs(family)
            self.F[m] = np.array(ids)[np.where(sib_noise < 0.35, 2, 0)][m]
        else:
            self.F[m] = fid(family)
        self.T[m] = tone

    def sun(self, mask, fade=None, heart=None):
        """A light pool (Claude A, render 1: a slightly warmer green, not yellow): the floor's
        warm sibling at its own tone, its heart a tone up on the body ramp, and at its edge a
        2 x 2 checker `fade` texels wide (eastward-edges 5.4: dither belongs to light)."""
        fade = fade if fade is not None else int(self.B['ground']['sun']['fade_texels'])
        heart = heart if heart is not None else int(self.B['ground']['sun'].get('heart_texels', 10))
        ok = self.open & ~self.locked
        core = ndi.binary_erosion(mask, iterations=max(1, fade // 2)) & ok
        ring = mask & ok & ~core
        inner = ndi.binary_erosion(mask, iterations=heart) & ok
        chk = ((self.X // 2 + self.Y // 2) % 2) == 0
        for m in (core, ring & chk):
            fam = self.F[m]
            self.F[m] = np.array([self._warm(f) for f in fam]) if len(fam) else fam
            self.light_mask[m] = 1
        self.T[inner] = np.minimum(4, self.T[inner] + 1)
        self.F[inner] = np.array([self._body(f) for f in self.F[inner]]) if inner.any() else self.F[inner]
        self.light_mask[inner] = 2

    def _body(self, f):
        name = cc.NAMES[f]
        return FID.get(name.replace('_warm', '').replace('_cool', ''), f)

    def banks(self, water, seed, still=None):
        """Damp banks along running water (Claude A, render 1): a band of damp earth one to two
        world px wide where the floor meets the water on its sides and south (the north bank
        has the cliff core's small face), its inner row darker, and bed pebbles in clusters of
        two or three along it, lit on top, dark under."""
        s = self.s
        w2 = int(round(2 * s))
        grow = ndi.binary_dilation(water, iterations=w2)
        band = grow & ~water & (self.t.kind == cc.TOP) & (self.tag == cc.TAG['ground'])
        band &= ~self.locked
        inner = band & ndi.binary_dilation(water, iterations=max(1, int(s // 2)))
        n = cc.vnoise2(self.X, self.Y, 5.0 * s, cc.hashu(seed, 1))
        band &= (n > 0.25) | inner
        ef = sibs('earth')
        self.F[band] = ef[2]
        self.T[band] = 3
        self.T[inner] = 2
        rng = np.random.default_rng(seed)
        ys, xs = np.nonzero(band & ~inner)
        taken = []
        st = sibs('stone')
        for i in rng.permutation(len(ys)):
            y, x = ys[i], xs[i]
            if any(abs(x - a) < 12 * s and abs(y - b) < 6 * s for a, b in taken):
                continue
            taken.append((x, y))
            for k in range(int(rng.integers(2, 4))):
                px, py = x + int(rng.integers(-3, 4)) * int(s), y + int(rng.integers(-1, 2)) * int(s)
                rw, rh = int(rng.integers(3, 5)), 2
                if not (0 <= py < self.H - rh - 1 and 0 <= px < self.W - rw - 1):
                    continue
                if not (band | water)[py:py + rh + 1, px:px + rw].all():
                    continue
                self.F[py:py + rh, px:px + rw] = st[int(rng.integers(0, 3))]
                self.T[py:py + rh, px:px + rw] = 4
                self.T[py + rh - 1, px + 1:px + rw] = 2
                self.T[py, px:px + rw - 1] = 5 if rng.random() < 0.3 else 4
                self.locked[py:py + rh, px:px + rw] = True

    def _warm(self, f):
        name = cc.NAMES[f]
        base = name.replace('_warm', '').replace('_cool', '')
        return FID.get(base + '_warm', f)

    def litter(self, centres, seed, radius_world=22.0, rate=None):
        """Leaf litter round the trees' feet: clusters of 2 to 4 texels (dominoes and L shapes)
        in the litter families, more near the trunk, none on paths or water, sparse enough that
        the floor stays a calm field."""
        G = self.B['ground']['litter']
        rate = rate if rate is not None else G['rate']
        fams = [fid(f) for f in G['families']]
        rng = np.random.default_rng(seed)
        s = self.s
        shapes = [[(0, 0), (0, 1)], [(0, 0), (0, 1), (1, 1)], [(0, 0), (1, 0)], [(0, 0), (0, 1), (0, 2)], [(0, 1), (1, 0), (1, 1)]]
        near = np.zeros((self.H, self.W), np.float32)
        for (cx, cy) in centres:
            X, Y = cx * s, cy * s
            r = radius_world * s
            y0, y1 = int(max(0, Y - r)), int(min(self.H, Y + r * 0.6))
            x0, x1 = int(max(0, X - r)), int(min(self.W, X + r))
            if y0 >= y1 or x0 >= x1:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1]
            dd = np.sqrt(((xx - X) / r) ** 2 + ((yy - Y) / (r * 0.6)) ** 2)
            near[y0:y1, x0:x1] = np.maximum(near[y0:y1, x0:x1], np.clip(1 - dd, 0, 1))
        ok = self.open & ~self.locked
        ys, xs = np.nonzero(ok & (near > 0))
        pick = rng.random(len(ys)) < near[ys, xs] * rate
        placed = np.zeros((self.H, self.W), bool)
        for y, x in zip(ys[pick], xs[pick]):
            st = shapes[int(rng.integers(0, len(shapes)))]
            pts = [(y + a, x + b) for a, b in st]
            if any(not (0 <= a < self.H and 0 <= b < self.W) or not ok[a, b] for a, b in pts):
                continue
            if placed[max(0, y - 2):y + 4, max(0, x - 2):x + 5].any():
                continue
            f = fams[int(rng.integers(0, len(fams)))]
            dark = rng.random() < 0.35
            for a, b in pts:
                self.F[a, b] = f
                self.T[a, b] = 2 if dark else G['tone']
                placed[a, b] = True

    # -- the raised ground as masses (Matt, 13:37: "massing in 3D", "strong form shading") ------
    def masses(self):
        """Shade every face as part of a mass: the face's run turns away from the light over its
        last 6 world px east (a tone down) and catches it over its first 2 px west (a tone up),
        and the ground at its foot is in ambient occlusion for 3 world px (a tone down, on top of
        the cliff core's foot band). Returns the face mask."""
        s = self.s
        K = self.t.kind
        face = (K == cc.FACEK) & np.isin(self.tag, (cc.TAG['rock'], cc.TAG['recess']))
        de = np.zeros(face.shape, np.int32)
        dw = np.zeros(face.shape, np.int32)
        cur_e, cur_w = face.copy(), face.copy()
        for k in range(1, int(8 * s)):
            ne = np.zeros_like(face)
            ne[:, :-1] = cur_e[:, 1:]
            cur_e = face & ne
            de += cur_e
            nw = np.zeros_like(face)
            nw[:, 1:] = cur_w[:, :-1]
            cur_w = face & nw
            dw += cur_w
        east = face & (de < int(ST.get('rock', 'east_turn_world', 6) * s)) & (dw > int(4 * s))
        west = face & (dw < int(ST.get('rock', 'west_catch_world', 2) * s)) & (de > int(4 * s))
        self.T[east] = np.maximum(0, self.T[east] - 1)
        self.T[west & (self.T < 4) & (self.T > 0)] += 1
        ground = (K == cc.TOP) & (self.t.z == 0) & ~np.isin(self.tag, (cc.TAG['water'],))
        below = np.zeros_like(face)
        cur = face.copy()
        for k in range(1, int(ST.get('rock', 'ao_world', 3) * s) + 1):
            sh = np.zeros_like(cur)
            sh[1:] = cur[:-1]
            cur = sh
            below |= cur
        ao = below & ground & ~face
        self.T[ao] = np.maximum(0, self.T[ao] - 1)
        return face

    def mass_shadow(self, kx, ky, dapple=None):
        """The raised ground's cast shadow (house-style 6, Matt: east, about 0.6 of the height):
        every texel of a face or a raised top is thrown from its height above the floor, so an
        outcrop throws a long parallelogram east and every face a band at its foot."""
        s = self.s
        K = self.t.kind
        H, W = self.H, self.W
        face = K == cc.FACEK
        top = (K == cc.TOP) & (self.t.z > 0)
        hgt = np.zeros((H, W), np.float64)
        hgt[top] = self.t.z[top] * s
        # a face texel's height: the rows from it down to its column's foot
        for x in range(W):
            col = face[:, x]
            if not col.any():
                continue
            foot = -1
            for y in range(H - 1, -1, -1):
                if col[y]:
                    if foot < 0:
                        foot = y + 1
                    hgt[y, x] = foot - y
                else:
                    foot = -1
        ys, xs = np.nonzero(hgt > 0)
        h = hgt[ys, xs]
        gy = ys + np.where(top[ys, xs], h, 0)
        X = np.round(xs + kx * h).astype(int)
        Y = np.round(gy + ky * h).astype(int)
        ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
        m = np.zeros((H, W), bool)
        m[Y[ok], X[ok]] = True
        k = max(2, int(round(2.5 * s)))
        m = ndi.binary_erosion(ndi.binary_fill_holes(ndi.binary_dilation(m, iterations=k)), iterations=k)
        m = soften(m, s) & (K == cc.TOP) & (self.t.z == 0)
        self.shadow(m)
        return m

    # -- shadow -----------------------------------------------------------------------------------
    def dapple(self, mask, seed):
        """Light through the canopy (Claude A, render 1): flecks of 2 to 6 texels inside a crown's
        shadow core, stepped back to the rim's tone, so the shade under a wood is dappled, not a
        flat dark stain (dither stays for fades only; these are clusters)."""
        s = self.s
        n = cc.vnoise2(self.X, self.Y, 4.0 * s, cc.hashu(seed, 2)) * 0.7 + cc.vnoise2(self.X, self.Y, 11.0 * s, cc.hashu(seed, 3)) * 0.3
        fleck = mask & (n > 0.7)
        fleck = ndi.binary_opening(fleck, iterations=max(1, int(s)))
        return fleck

    def shadow(self, mask, night=False, dapple=None):
        """A cast shadow (house-style 6, eastward-edges 7.2): its core two tones down, its outer
        rim (rim_world world px) one tone down, on whatever ground it falls on (floor, path,
        bank); never on water (water keeps its own dark band) or a face."""
        S = self.B['shadow']
        rim_w = max(1, int(round(S['rim_world'] * self.s)))
        ground = (self.t.kind == cc.TOP) & ~np.isin(self.tag, (cc.TAG['water'], cc.TAG['foam']))
        inner = ndi.binary_erosion(mask, iterations=rim_w)
        rim = mask & ~inner
        core_steps = S['night_steps'] if night else S['core_steps']
        if dapple is not None:
            fl = inner & dapple
            inner = inner & ~dapple
            rim = rim | fl
        self.T[inner & ground] = np.maximum(0, self.T[inner & ground] - core_steps)
        self.T[rim & ground] = np.maximum(0, self.T[rim & ground] - S['rim_steps'])
        self.shadow_mask[rim & ground] = np.maximum(self.shadow_mask[rim & ground], 1)
        self.shadow_mask[inner & ground] = 2

    def contact(self, mask):
        ok = self.t.kind == cc.TOP
        self.T[mask & ok] = np.minimum(self.T[mask & ok], self.B['shadow']['contact_tone'])
        self.shadow_mask[mask & ok] = 3

    def image(self):
        from PIL import Image
        rgb = LUT[self.F, np.clip(self.T, 0, 6)]
        return Image.fromarray(rgb, 'RGB').convert('RGBA')


# ------------------------------------------------------------------------------------------------
# shadow geometry
# ------------------------------------------------------------------------------------------------
def cast(alpha: np.ndarray, anchor, at, W: int, H: int, d: float, kx=0.6, ky=0.12, trunk_from=None, soft=True):
    """The silhouette thrown east onto the ground: a pixel h texels above the foot line lands
    kx * h east and ky * h south of the foot (Matt: east, about 0.6 of the height). Holes are
    closed and its outline smoothed (soften) so it reads as one shape. Worked in a box round
    the shadow, returned as a screen mask."""
    ys, xs = np.nonzero(alpha)
    out = np.zeros((H, W), bool)
    if not len(ys):
        return out
    ax, ay = anchor
    hgt = np.maximum(0, ay - ys)
    gx = xs + kx * hgt
    gy = ay + ky * hgt - np.maximum(0, (ys - ay))
    X = np.round(gx - ax + at[0]).astype(int)
    Y = np.round(gy - ay + at[1]).astype(int)
    k = max(2, int(round(2.5 * d)))
    pad = k + 8
    x0, y0 = X.min() - pad, Y.min() - pad
    x1, y1 = X.max() + pad + 1, Y.max() + pad + 1
    m = np.zeros((y1 - y0, x1 - x0), bool)
    m[Y - y0, X - x0] = True
    m = ndi.binary_dilation(m, iterations=k)
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_erosion(m, iterations=k)
    if soft:
        m = soften(m, d)
    a0, b0 = max(0, y0), max(0, x0)
    a1, b1 = min(H, y1), min(W, x1)
    if a0 < a1 and b0 < b1:
        out[a0:a1, b0:b1] = m[a0 - y0:a1 - y0, b0 - x0:b1 - x0]
    return out


def soften(m: np.ndarray, d: float) -> np.ndarray:
    """A shadow's outline in the soft-grid manner: no single-texel teeth, corners rounded (the
    same rounding the cliff core gives a rim, at texel radius 2 world px)."""
    import terrace
    r = max(2, int(round(2 * d)))
    return terrace.rounded(m, r, max(1, r // 2))


def contact_line(alpha: np.ndarray, anchor, at, W: int, H: int, d: float) -> np.ndarray:
    """The ground one texel under each column of the sprite's lowest pixels (those within two
    world px of its foot)."""
    ax, ay = anchor
    m = np.zeros((H, W), bool)
    near = int(round(2 * d))
    cols = np.nonzero(alpha.any(axis=0))[0]
    for x in cols:
        ys = np.nonzero(alpha[:, x])[0]
        y = ys.max()
        if y < ay - near - 1:
            continue
        X = int(round(at[0] - ax + x))
        Y = int(round(at[1] - ay + y + 1))
        if 0 <= X < W and 0 <= Y < H:
            m[Y, X] = True
    return m


def blob(cx, cy, rx, ry, shape, seed, rough=0.25, s=2.0):
    """An organic patch (a sun pool, a clearing's edge) in texels: an ellipse whose edge is
    moved by smooth noise. Inside a place's outline the texture keeps its own shape
    (eastward-edges 1.3)."""
    H, W = shape
    Y, X = np.mgrid[0:H, 0:W]
    a = np.arctan2((Y - cy * s) / (ry * s), (X - cx * s) / (rx * s))
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * math.pi, 3)
    wob = 1 + rough * (0.5 * np.sin(3 * a + ph[0]) + 0.3 * np.sin(5 * a + ph[1]) + 0.2 * np.sin(7 * a + ph[2]))
    q = ((X - cx * s) / (rx * s)) ** 2 + ((Y - cy * s) / (ry * s)) ** 2
    return q <= wob ** 2
