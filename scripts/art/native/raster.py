"""Raster kit: density-independent part drawing in the house style (scripts/art/native).

Everything is drawn in *units*: one unit is one texel at density 2 (an adult 50 units), so at
density d a unit is d / 2 texels. Shapes are rasterised at the target density by testing pixel
centres, never resampled, so every density is drawn natively (DENSITY.md 4).

A Sprite collects parts (a mask, a family, a base tone, a depth). render() shades each part as
one form lit from the upper left (bands that follow the silhouette, so a part's rim catches the
light and its lower right falls into shade), throws contact shade from nearer parts onto the
ones behind, applies the part's marks (folds, fur locks, grain), removes lone pixels and specks
inside every part, and closes the silhouette with the house outline: one pixel in the edge tone
of the material it closes, broken to tone 1 on lit top and left edges (house-style 2 to 4).

A Grid may be mirrored (`mirror=True`): x is measured to the left, so a west facing is drawn
from the east facing's geometry while the light stays upper left (a facing is drawn, never a
flipped picture).

Colours come only from the house palette (art/house-palette.json).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
if ART not in sys.path:
    sys.path.insert(0, ART)
import house_palette as hp  # noqa: E402

_P = hp.load()
RAMPS: dict = dict(_P['ramps'])
EDGES: dict = dict(_P['edges'])
INK = _P['ink']


def parent(f: str) -> str:
    return hp.family(f)


def rgb(fam: str, t: int) -> tuple:
    if t == 6:
        e = EDGES.get(parent(fam))
        return hp.hex_rgb(e if e else INK)
    return hp.hex_rgb(RAMPS[fam][max(0, min(5, t))])


def ink() -> tuple:
    return hp.hex_rgb(INK)


# ------------------------------------------------------------------------------------------
# rasterising (units -> pixels)
# ------------------------------------------------------------------------------------------
class Grid:
    """Pixel-centre coordinates in units for a W x H pixel canvas whose unit origin sits at
    pixel (ox, oy) (in pixels), at s px a unit."""

    def __init__(self, w: int, h: int, s: float, ox: float, oy: float, mirror: bool = False):
        self.w, self.h, self.s, self.ox, self.oy = w, h, s, ox, oy
        self.mirror = mirror
        ys, xs = np.mgrid[0:h, 0:w]
        self.X = (xs + 0.5 - ox) / s
        if mirror:
            self.X = -self.X
        self.Y = (ys + 0.5 - oy) / s

    def px(self, x: float, y: float) -> tuple:
        if self.mirror:
            x = -x
        return (int(math.floor(self.ox + x * self.s)), int(math.floor(self.oy + y * self.s)))

    # shapes return boolean masks -------------------------------------------------------
    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        X, Y = self.X - cx, self.Y - cy
        if rot:
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            X, Y = X * c + Y * s, -X * s + Y * c
        rx = max(rx, 0.5 / self.s)
        ry = max(ry, 0.5 / self.s)
        return (X / rx) ** 2 + (Y / ry) ** 2 <= 1.0

    def superellipse(self, cx, cy, rx, ry, n=3.0):
        return (np.abs((self.X - cx) / rx) ** n + np.abs((self.Y - cy) / ry) ** n) <= 1.0

    def rect(self, x0, y0, x1, y1):
        return (self.X >= x0) & (self.X < x1) & (self.Y >= y0) & (self.Y < y1)

    def rrect(self, x0, y0, x1, y1, r):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        cx = np.clip(self.X, x0 + r, x1 - r)
        cy = np.clip(self.Y, y0 + r, y1 - r)
        return ((self.X - cx) ** 2 + (self.Y - cy) ** 2 <= r * r) & self.rect(x0, y0, x1, y1)

    def capsule(self, x0, y0, x1, y1, r0, r1=None):
        """A tapered limb from (x0, y0) radius r0 to (x1, y1) radius r1."""
        r1 = r0 if r1 is None else r1
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((self.X - x0) * dx + (self.Y - y0) * dy) / L2, 0, 1)
        px, py = x0 + t * dx, y0 + t * dy
        r = r0 + (r1 - r0) * t
        r = np.maximum(r, 0.5 / self.s)
        return (self.X - px) ** 2 + (self.Y - py) ** 2 <= r * r

    def poly(self, pts):
        """Even-odd polygon fill at pixel centres."""
        X, Y = self.X, self.Y
        inside = np.zeros(X.shape, bool)
        n = len(pts)
        for i in range(n):
            xa, ya = pts[i]
            xb, yb = pts[(i + 1) % n]
            if ya == yb:
                continue
            cond = (ya > Y) != (yb > Y)
            xint = xa + (Y - ya) * (xb - xa) / (yb - ya)
            inside ^= cond & (X < xint)
        return inside

    def line(self, pts, w: int = 1):
        """A hand-drawn line through the points: one run of w px per row (or per column where
        the line is flatter than 45 degrees), so diagonals step cleanly with no gaps."""
        m = np.zeros((self.h, self.w), bool)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            sx = -1 if self.mirror else 1
            x0, y0 = self.ox + sx * ax * self.s, self.oy + ay * self.s
            x1, y1 = self.ox + sx * bx * self.s, self.oy + by * self.s
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for k in range(n + 1):
                t = k / n
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                xi, yi = int(math.floor(x)), int(math.floor(y))
                for j in range(w):
                    if abs(y1 - y0) >= abs(x1 - x0):
                        xx, yy = xi - (w - 1) // 2 + j, yi
                    else:
                        xx, yy = xi, yi - (w - 1) // 2 + j
                    if 0 <= xx < self.w and 0 <= yy < self.h:
                        m[yy, xx] = True
        return m

    def stroke(self, pts, r):
        m = np.zeros((self.h, self.w), bool)
        for (a, b), (c, d) in zip(pts, pts[1:]):
            m |= self.capsule(a, b, c, d, r)
        return m


def round_mask(m: np.ndarray, r: int = 1) -> np.ndarray:
    """Knock off one-pixel corners and fill one-pixel notches (keeps silhouettes clean)."""
    if r <= 0:
        return m
    st = ndi.generate_binary_structure(2, 1)
    m = ndi.binary_closing(m, st, iterations=r)
    m = ndi.binary_opening(m, st, iterations=r)
    return m


# ------------------------------------------------------------------------------------------
# sprites
# ------------------------------------------------------------------------------------------
class Part:
    def __init__(self, name, mask, fam, base=3, z=0.0, lo=None, hi=None, mode='form', k=1.0,
                 casts=True, rel=None, fixed=None, light=(-0.55, -0.83), line=False, glow=False,
                 outline=True, clean=True, flat=False):
        self.name, self.mask, self.fam, self.base, self.z = name, mask, fam, base, z
        self.lo = base - 2 if lo is None else lo
        self.hi = base + 1 if hi is None else hi
        self.mode, self.k, self.casts, self.light = mode, k, casts, light
        self.rel = rel            # int array of tone offsets (marks), or None
        self.fixed = fixed        # a fixed tone (details), or None
        self.line = line          # draw this part's edge tone where it overlaps a farther part
        self.glow = glow          # a light source: fixed tones, no outline, no shading
        self.outline = outline    # take part in the silhouette outline
        self.clean = clean
        self.flat = flat          # no form shading (base tone + marks only)
        self.famarr = None        # optional per-pixel family names (siblings), via set_fams


class Sprite:
    def __init__(self, w: int, h: int, s: float, ox: float, oy: float, mirror: bool = False):
        self.g = Grid(w, h, s, ox, oy, mirror)
        self.w, self.h, self.s = w, h, s
        self.parts: list[Part] = []
        self.over = []            # (mask, rgb) drawn last, no outline (glints, eyes)
        self.inkmarks = []        # (mask, rgb) drawn last and counted inside the silhouette

    def add(self, name, mask, fam, **kw) -> Part:
        p = Part(name, mask, fam, **kw)
        self.parts.append(p)
        return p

    def part(self, name) -> Part:
        for p in self.parts:
            if p.name == name:
                return p
        raise KeyError(name)

    def mark(self, name, mask, d):
        """Add a tone offset d to a part where mask is set (folds, locks, grain)."""
        p = self.part(name)
        if p.rel is None:
            p.rel = np.zeros((self.h, self.w), int)
        p.rel[mask & p.mask] += d

    def detail(self, mask, rgbc, inside=True):
        (self.inkmarks if inside else self.over).append((mask, rgbc))

    # ---------------------------------------------------------------------------------------
    def _shade(self, p: Part) -> np.ndarray:
        """Tone per pixel of the part's whole mask (also where nearer parts hide it)."""
        m = p.mask
        t = np.full(m.shape, p.base, int)
        if p.flat or not m.any():
            return t
        ys, xs = np.nonzero(m)
        ext = min(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
        lx, ly = p.light
        nrm = math.hypot(lx, ly)
        lx, ly = lx / nrm, ly / nrm

        def gone(r):
            # pixels whose neighbour r px towards (or away from) the light leaves the part
            dx, dy = int(round(lx * r)), int(round(ly * r))
            sh = np.zeros_like(m)
            H, W = m.shape
            y0, y1 = max(0, -dy), min(H, H - dy)
            x0, x1 = max(0, -dx), min(W, W - dx)
            sh[y0:y1, x0:x1] = m[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
            return m & ~sh

        if p.mode == 'form':
            r_lit = max(1, int(round(ext * 0.16 * p.k)))
            r_sh = max(1, int(round(ext * 0.30 * p.k)))
            r_deep = max(1, int(round(ext * 0.11 * p.k)))
            lit = gone(r_lit)                # near the upper-left rim
            shade = gone(-r_sh)              # within r_sh of the lower-right rim
            deep = gone(-r_deep)
            t = t + lit.astype(int) - shade.astype(int) - deep.astype(int)
        elif p.mode == 'cyl':                # a vertical cylinder: bands across
            x0, x1 = xs.min(), xs.max() + 1
            rowmin = np.full(m.shape[0], 10 ** 6)
            rowmax = np.full(m.shape[0], -1)
            for y in np.unique(ys):
                r = np.nonzero(m[y])[0]
                rowmin[y], rowmax[y] = r.min(), r.max()
            Y, X = np.mgrid[0:m.shape[0], 0:m.shape[1]]
            wdt = np.maximum(1, rowmax[:, None] - rowmin[:, None] + 1)
            u = (X - rowmin[:, None] + 0.5) / wdt
            t = t + np.where(u < 0.3 * p.k, 1, 0) - np.where(u > 1 - 0.3 * p.k, 1, 0) \
                - np.where(u > 1 - 0.12 * p.k, 1, 0)
        elif p.mode == 'top':                # a flat top plane (benches, slabs): lit front rows
            t = t + 0
        return t

    def render(self, outline=True, contact=True, tidy=True, min_cluster=None) -> Image.Image:
        H, W = self.h, self.w
        order = sorted(range(len(self.parts)), key=lambda i: self.parts[i].z)
        owner = np.full((H, W), -1, int)
        for i in order:
            owner[self.parts[i].mask] = i
        tone = np.full((H, W), -1, int)
        famidx = {}
        fams = []
        famof = np.full((H, W), -1, int)

        def fi(f):
            if f not in famidx:
                famidx[f] = len(fams)
                fams.append(f)
            return famidx[f]

        shaded = {}
        for i in order:
            p = self.parts[i]
            vis = owner == i
            if not vis.any():
                continue
            if p.fixed is not None:
                t = np.full((H, W), p.fixed, int)
            else:
                t = self._shade(p)
                if p.rel is not None:
                    t = t + p.rel
                t = np.clip(t, p.lo, p.hi)
            shaded[i] = t
            tone[vis] = t[vis]
            if p.famarr is not None:
                for f in np.unique(p.famarr[vis]):
                    sel = vis & (p.famarr == f)
                    famof[sel] = fi(str(f))
            else:
                famof[vis] = fi(p.fam)
        # contact shade: a nearer casting part darkens the part behind just below / right of it
        if contact:
            sw = max(1, int(round(self.s * 1.0)))
            for i in order:
                p = self.parts[i]
                if not p.casts or p.glow:
                    continue
                m = owner == i
                sh = np.zeros_like(m)
                for k in range(1, sw + 1):
                    sh[k:, :] |= m[:-k, :]
                    sh[k:, k:] |= m[:-k, :-k]
                    sh[:, k:] |= m[:, :-k] if k == 1 else False
                tgt = sh & (owner >= 0) & ~m
                for j in np.unique(owner[tgt]):
                    q = self.parts[j]
                    if q.z >= p.z or q.fixed is not None or q.glow:
                        continue
                    sel = tgt & (owner == j)
                    tone[sel] = np.maximum(q.lo, tone[sel] - 1)
                if p.line:
                    edge = ndi.binary_dilation(m, ndi.generate_binary_structure(2, 1)) & ~m & (owner >= 0)
                    for j in np.unique(owner[edge]):
                        q = self.parts[j]
                        if q.z >= p.z or q.glow:
                            continue
                        sel = edge & (owner == j)
                        tone[sel] = np.minimum(tone[sel], max(0, q.lo - 1))
        # tidy: no lone pixels or specks smaller than min_cluster inside a part
        if tidy:
            mc = min_cluster or (3 if self.s >= 0.9 else 2)
            for i in order:
                p = self.parts[i]
                if not p.clean or p.fixed is not None:
                    continue
                vis = owner == i
                for _ in range(2):
                    for tv in np.unique(tone[vis]):
                        sel = vis & (tone == tv)
                        lab, n = ndi.label(sel)
                        if n == 0:
                            continue
                        sizes = ndi.sum(sel, lab, range(1, n + 1))
                        for k, sz in enumerate(sizes, 1):
                            if sz >= mc:
                                continue
                            blob = lab == k
                            ring = ndi.binary_dilation(blob) & ~blob & vis
                            if not ring.any():
                                continue
                            v, c = np.unique(tone[ring], return_counts=True)
                            tone[blob] = v[c.argmax()]
        out = np.zeros((H, W, 4), np.uint8)
        solid = owner >= 0
        for y, x in zip(*np.nonzero(solid)):
            p = self.parts[owner[y, x]]
            f = fams[famof[y, x]]
            out[y, x, :3] = rgb(f, tone[y, x])
            out[y, x, 3] = 255
        for m, c in self.inkmarks:
            out[m, :3] = c
            out[m, 3] = 255
            solid = solid | m
        if outline:
            outl = [i for i in range(len(self.parts)) if self.parts[i].outline and not self.parts[i].glow]
            body = np.isin(owner, outl) | (solid & (owner < 0))
            ring = ndi.binary_dilation(body, ndi.generate_binary_structure(2, 1)) & ~solid
            for y, x in zip(*np.nonzero(ring)):
                # the inside neighbour that closes it: prefer below, then right, left, above
                best = None
                for dx, dy, lit in ((0, 1, True), (1, 0, True), (-1, 0, False), (0, -1, False)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and body[yy, xx] and owner[yy, xx] >= 0:
                        best = (yy, xx, lit)
                        break
                if best is None:
                    out[y, x, :3] = ink()
                    out[y, x, 3] = 255
                    continue
                yy, xx, lit = best
                f = fams[famof[yy, xx]]
                if lit and tone[yy, xx] >= 4:
                    out[y, x, :3] = rgb(f, 1)
                else:
                    out[y, x, :3] = rgb(f, 6)
                out[y, x, 3] = 255
        for m, c in self.over:
            out[m, :3] = c
            out[m, 3] = 255
        return Image.fromarray(out, 'RGBA')


def lone_share(img: Image.Image) -> float:
    """Share of opaque pixels unlike all four neighbours (the house no-speckle test)."""
    a = np.asarray(img.convert('RGBA')).astype(np.int64)
    key = a[..., 0] * 65536 + a[..., 1] * 256 + a[..., 2]
    key[a[..., 3] == 0] = -1
    P = np.pad(key, 1, constant_values=-2)
    c = P[1:-1, 1:-1]
    lone = (c != P[:-2, 1:-1]) & (c != P[2:, 1:-1]) & (c != P[1:-1, :-2]) & (c != P[1:-1, 2:])
    inside = (a[..., 3] > 0)
    er = ndi.binary_erosion(inside)
    return float(lone[er].mean()) if er.any() else 0.0


def zoom(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)
