"""Eastward-style character rig: parts, shared shading rules, outline and cleanup.

Coordinates are art pixels on the 960x540 grid, relative to the ground pivot (feet centre):
x to the right, y down, so a head sits at y ~ -60.  A figure is a list of parts.  Each part is a
mask (built from primitives), a material, a depth z and a few shading knobs.  render() turns the
parts into a sprite with the same rules for every character:

  1. Form light.  Every part is shaded from its own silhouette: a dome built from its distance
     field, lit from the upper left.  A narrow light rim on the upper-left edge, base in the
     middle, a wider shadow band on the lower-right edge.  Four tones per material
     (deep, shadow, base, light); deep is kept for cast shadows, creases and inner lines.
  2. Cast shadows.  Heads, hat brims, mantles and arms drop one tone onto what lies under
     them, offset down and right.
  3. Clean clusters.  Lone tone pixels inside a part are merged into their neighbours, so no
     speckle survives.
  4. Lines.  Parts that overlap other parts get a 1 px inner line in their own edge tone
     ('hard': limbs, heads, hands) or their deep tone ('soft': cloth over cloth).
  5. Outline.  One continuous 1 px outline outside the silhouette (4-neighbour, so diagonals
     stay single), coloured with the edge tone of the material it wraps.
  6. Details (eyes, glints, strings) are placed last, by hand, as explicit pixels.

West is drawn from the east geometry on a mirrored x axis (Fig(flip=True)), and the light is
computed after the mirror, so it stays upper left.  Asymmetric gear is placed by each character.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

INK = '#1E1917'


def hx(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def tohex(c):
    c = np.clip(np.round(c), 0, 255).astype(int)
    return '#%02X%02X%02X' % tuple(c)


def mix(a, b, t):
    return tohex(hx(a) * (1 - t) + hx(b) * t)


FACE_INK = '#1E1917'      # the eye ink (parts.EYE): details in it are tagged 'face'

class Mat:
    """A material ramp: tones[0..3] = deep, shadow, base, light (an optional tones[4] = shine,
    used only by hand for metal glints).  edge = outline colour (deep pulled toward the ink)."""

    def __init__(self, name, tones, edge=None):
        self.name = name
        self.tones = [hx(t) for t in tones]
        self.hex = list(tones)
        self.edge = hx(edge) if edge else hx(mix(tones[0], INK, 0.62))


MATS: dict[str, Mat] = {}


def mat(name, tones, edge=None):
    MATS[name] = Mat(name, tones, edge)


class Part:
    __slots__ = ('mask', 'mat', 'z', 'rl', 'rs', 'tl', 'ts', 'vgrad', 'flat', 'line', 'cast',
                 'clean', 'tonemap', 'deep', 'dim', 'noout', 'tag', 'xy', 'twin')

    def __init__(self, **k):
        for s in self.__slots__:
            setattr(self, s, k.get(s))


class Fig:
    """One frame of one character."""

    def __init__(self, W=128, H=128, gx=None, gy=None, flip=False, scale=1.0):
        """scale > 1 draws the figure larger at the same pixel density: every coordinate a
        build passes is multiplied by scale (shapes are resampled crisply, not upscaled), and
        anchors come back in screen pixels.  The foot pivot stays the pivot."""
        self.W, self.H = W, H
        self.scale = scale
        self.gx = W // 2 if gx is None else gx
        self.gy = H - 8 if gy is None else gy
        self.flip = flip
        yy, xx = np.mgrid[0:H, 0:W].astype(float)
        self.X = (xx - self.gx + 0.5) / scale
        self.Y = (yy - self.gy + 0.5) / scale
        if flip:
            self.X = -self.X
        self.parts: list[Part] = []
        self.details = []          # (mask, rgb, solid, tag)
        self.anchors = {}          # name -> (x, y) in screen pixels relative to the pivot
        self.tags = {}             # tag -> visible pixel count (filled by render)
        self._tag = None           # default tag for parts and details (see tagging())

    def tagging(self, tag):
        """with f.tagging('bow'): ... stamps the tag on every part and detail added inside."""
        fig = self

        class _T:
            def __enter__(self_):
                self_.prev = fig._tag
                fig._tag = tag

            def __exit__(self_, *a):
                fig._tag = self_.prev
        return _T()

    def anchor(self, name, x, y):
        """Record a named point (hand, muzzle, strike tip) given in pivot space; it is stored
        in screen orientation, so a flipped (west) figure stores -x."""
        x, y = x * self.scale, y * self.scale
        self.anchors[name] = ((-x if self.flip else x), y)

    # ------------------------------------------------------------------ primitives (masks)
    def ell(self, cx, cy, rx, ry):
        return ((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2 <= 1.0

    def rell(self, cx, cy, a, b, ang):
        """Rotated ellipse in pivot space: semi-axis a along the angle ang (radians), b across it."""
        c, s = np.cos(ang), np.sin(ang)
        dx, dy = self.X - cx, self.Y - cy
        u = dx * c + dy * s
        v = -dx * s + dy * c
        return (u / max(a, 0.3)) ** 2 + (v / max(b, 0.3)) ** 2 <= 1.0

    def rect(self, x0, y0, x1, y1):
        return (self.X >= x0) & (self.X < x1) & (self.Y >= y0) & (self.Y < y1)

    def cap(self, x0, y0, x1, y1, r0, r1=None):
        """Tapered capsule from (x0,y0) radius r0 to (x1,y1) radius r1."""
        r1 = r0 if r1 is None else r1
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-9
        t = np.clip(((self.X - x0) * dx + (self.Y - y0) * dy) / L2, 0, 1)
        px, py = x0 + t * dx, y0 + t * dy
        r = r0 + (r1 - r0) * t
        return (self.X - px) ** 2 + (self.Y - py) ** 2 <= r * r

    def poly(self, pts):
        """Polygon in pivot coordinates (mirrored when the figure is flipped)."""
        img = Image.new('L', (self.W, self.H), 0)
        sx = -1 if self.flip else 1
        k = self.scale
        P = [(self.gx + sx * x * k - 0.5, self.gy + y * k - 0.5) for x, y in pts]
        ImageDraw.Draw(img).polygon(P, fill=255, outline=255)
        return np.array(img) > 0

    def pixels(self, pts):
        m = np.zeros((self.H, self.W), bool)
        sx = -1 if self.flip else 1
        for x, y in pts:
            k = self.scale
            c = int(np.floor(self.gx + sx * (x * k + 0.5) + 1e-6 * sx))
            r = int(np.floor(self.gy + y * k + 1e-6))
            if 0 <= r < self.H and 0 <= c < self.W:
                m[r, c] = True
        return m

    def seg(self, x0, y0, x1, y1):
        """A 1 px line (Bresenham) between two pivot-space points."""
        pts = []
        k = self.scale                      # walk the line in screen pixels
        x0, y0, x1, y1 = int(round(x0 * k)), int(round(y0 * k)), int(round(x1 * k)), int(round(y1 * k))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            pts.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return self.pixels([(x / k, y / k) for x, y in pts])

    def stamp(self, rows, x, y, key, z=None):
        """Explicit pixels from text rows: key maps a character to (material, tone) or a hex
        colour.  (x, y) is the top-left in pivot space (mirrored when flipped)."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in key:
                    self.dot(x + i, y + j, key[ch])

    # ------------------------------------------------------------------ adding
    def add(self, mask, mat, z=0, rl=2.0, rs=3.0, tl=0.42, ts=0.42, vgrad=0.0, flat=None,
            line='hard', cast=None, clean=True, tonemap=None, deep=False, dim=0, noout=False, tag=None):
        """rl / rs: widths (px) of the light rim and the shadow band; tl / ts: thresholds (lower
        = more light / more shadow); vgrad: extra shadow toward the bottom of the part;
        flat: a fixed tone; cast: (dx, dy, strength) shadow dropped on parts beneath;
        tonemap: fn(X, Y, tones) -> tones to add hand folds."""
        if mask is not None and getattr(self, '_clip', None) is not None:
            mask = mask & self._clip                  # v2: turn.Warp(clip=...) keeps a far half inside the silhouette
        if mask is None or not mask.any():
            return None
        p = Part(mask=mask, mat=mat, z=z + getattr(self, '_zoff', 0.0), rl=rl, rs=rs, tl=tl, ts=ts, vgrad=vgrad, flat=flat,
                 line=line, cast=cast, clean=clean, tonemap=tonemap, deep=deep, dim=dim, noout=noout, tag=tag or self._tag,
                 xy=getattr(self, '_xy', None), twin=getattr(self, '_twin', None))   # v2: turn.Warp contexts
        self.parts.append(p)
        return p

    def dot(self, x, y, c, solid=True, tag=None, z=None):
        self.detail(self.pixels([(x, y)]), c, solid, tag, z)

    def detail(self, mask, c, solid=True, tag=None, z=None):
        if getattr(self, '_clip', None) is not None:
            mask = mask & self._clip
        """Explicit pixels drawn after shading.  z: when given, the pixels only show where no
        part nearer than z covers them (so a glint or rivet on a hidden item stays hidden)."""
        tag = tag or self._tag
        if tag is None and isinstance(c, str) and c.upper() == FACE_INK:
            tag = 'face'           # 26 Oct: eye ink is a face part (checks.py: no face from behind)
        self.details.append((mask, c, solid, tag, z))

    # ------------------------------------------------------------------ render
    def _shade(self, p: Part):
        H, W = self.H, self.W
        if p.flat is not None:
            t = np.full((H, W), p.flat, int)
        else:
            m = np.pad(p.mask, 3)
            d = ndi.distance_transform_edt(m)[3:-3, 3:-3]
            t = np.full((H, W), 2, int)

            def lit(R):
                h = np.sqrt(np.clip(d / R, 0, 1))
                gy, gx = np.gradient(h)
                return (0.6 * gx + 0.8 * gy) * R

            ll = lit(p.rl)
            ls = lit(p.rs)
            if p.vgrad:
                ys = np.where(p.mask)[0]
                y0, y1 = ys.min(), ys.max() + 1
                rows = (np.arange(H)[:, None] - y0) / max(1, y1 - y0)
                ls = ls - p.vgrad * np.clip(rows, 0, 1)
            t[ll > p.tl] = 3
            t[ls < -p.ts] = 1
            if p.deep:
                t[ls < -p.ts * 2.6] = 0
        if p.tonemap is not None:
            X, Y = p.xy if p.xy is not None else (self.X, self.Y)    # a part drawn in a turn.Warp keeps its own grid
            t = p.tonemap(X, Y, t)
        if p.dim:
            t = np.maximum(t - p.dim, 0 if p.deep else 1) if p.flat is None else np.maximum(t - p.dim, 0)
        return t

    def render(self, outline=True):
        H, W = self.H, self.W
        parts = sorted(enumerate(self.parts), key=lambda q: (q[1].z, q[0]))
        pid = np.full((H, W), -1, int)
        tone = np.zeros((H, W), int)
        zmap = np.full((H, W), -1e9)
        plist = []
        for k, (_, p) in enumerate(parts):
            t = self._shade(p)
            m = p.mask
            pid[m] = k
            tone[m] = t[m]
            zmap[m] = p.z
            plist.append(p)
        # cast shadows onto lower parts
        for k, p in enumerate(plist):
            if not p.cast:
                continue
            dx, dy, s = p.cast
            dx = -dx if self.flip else dx
            sh = np.roll(np.roll(p.mask, dy, 0), dx, 1)
            hit = sh & (pid >= 0) & (zmap < p.z) & ~p.mask
            # do not let the shadow spill onto parts that are not under this one
            if s >= 2:
                tone[hit] = 0
            else:
                tone[hit] = np.where(tone[hit] >= 2, 1, np.maximum(tone[hit] - 1, 0))
        # clean clusters: lone pixels of a tone inside one part take their neighbours' tone
        for _ in range(2):
            for k, p in enumerate(plist):
                if not p.clean:
                    continue
                inside = pid == k
                for tv in (0, 1, 2, 3):
                    tm = inside & (tone == tv)
                    if not tm.any():
                        continue
                    lab, n = ndi.label(tm)
                    if n == 0:
                        continue
                    sizes = ndi.sum(tm, lab, range(1, n + 1))
                    lim = 1 if tv in (1, 2) else 2
                    for ci in np.where(sizes <= lim)[0]:
                        cm = lab == ci + 1
                        ring = ndi.binary_dilation(cm, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~cm & inside
                        if ring.any():
                            vals = tone[ring]
                            tone[cm] = np.bincount(vals, minlength=4).argmax()
        # colours
        out = np.zeros((H, W, 4), float)
        for k, p in enumerate(plist):
            m = pid == k
            if not m.any():
                continue
            M = MATS[p.mat]
            T = np.array(M.tones)[:4]
            out[m, :3] = T[np.clip(tone[m], 0, 3)]
            out[m, 3] = 255
        # inner lines
        four = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for k, p in enumerate(plist):
            if p.line not in ('hard', 'soft', 'shade'):
                continue
            m = pid == k
            edge = np.zeros_like(m)
            # v2: no line between the near and far halves of one turned (turn.Warp) surface of one material
            twin_ok = np.array([q.twin is not None and p.twin is not None and q.twin != p.twin and q.mat == p.mat for q in plist] + [False])
            for dy, dx in four:
                nb = np.roll(np.roll(pid, dy, 0), dx, 1)
                nz = np.roll(np.roll(zmap, dy, 0), dx, 1)
                edge |= m & (nb >= 0) & (nb != k) & (nz < p.z) & ~twin_ok[nb]
            same = np.zeros_like(m)
            M = MATS[p.mat]
            c = {'hard': M.edge, 'soft': M.tones[0], 'shade': M.tones[1]}[p.line]
            out[edge, :3] = c
        # details
        nout = np.zeros((H, W), bool)
        for k, p in enumerate(plist):
            if p.noout:
                nout |= pid == k
        solid = (pid >= 0) & ~nout
        tagmap = np.zeros((H, W), int)
        tnames = [None]

        def tcode(tg):
            if tg not in tnames:
                tnames.append(tg)
            return tnames.index(tg)
        for k, p in enumerate(plist):
            if p.tag:
                tagmap[pid == k] = tcode(p.tag)
        for d in self.details:                     # tolerate (mask, c, solid[, tag[, z]]) appended directly
            m, c, s = d[:3]
            tg = d[3] if len(d) > 3 else None
            dz = d[4] if len(d) > 4 else None
            if dz is not None:
                m = m & ((zmap <= dz) | (pid < 0))
            if tg:
                tagmap[m] = tcode(tg)
            if isinstance(c, tuple):
                mm, tv = c
                col = MATS[mm].tones[tv] if tv != 'edge' else MATS[mm].edge
            else:
                col = hx(c)
            out[m, :3] = col
            out[m, 3] = 255
            if s:
                solid = solid | m
        # outline
        if outline:
            cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
            ol = ndi.binary_dilation(solid, structure=cross) & ~solid & ~nout
            # edge colour of the wrapped material: take the top-most inside 4-neighbour
            best = np.full((H, W), -1e9)
            col = np.zeros((H, W, 3))
            for dy, dx in four:
                nb = np.roll(np.roll(pid, dy, 0), dx, 1)
                nz = np.roll(np.roll(zmap, dy, 0), dx, 1)
                nbo = np.roll(np.roll(nout, dy, 0), dx, 1)
                ok = ol & (nb >= 0) & (nz > best) & ~nbo
                if ok.any():
                    for k in np.unique(nb[ok]):
                        mm = ok & (nb == k)
                        col[mm] = MATS[plist[k].mat].edge
                    best[ok] = nz[ok]
            noc = ol & (best < -1e8)
            col[noc] = hx(INK)
            out[ol, :3] = col[ol]
            out[ol, 3] = 255
        self.tags = {}
        self.tagmasks = {}             # v2: tag -> visible pixel mask (release anchors are checked against it)
        cnt = np.bincount(tagmap.ravel(), minlength=len(tnames))
        for i, tg in enumerate(tnames[1:], 1):
            self.tags[tg] = self.tags.get(tg, 0) + int(cnt[i])
            self.tagmasks[tg] = self.tagmasks[tg] | (tagmap == i) if tg in self.tagmasks else (tagmap == i)
        self.pid, self.plist = pid, plist
        if getattr(self, 'despeckle', False):
            out = despeckle(out)
        return out.astype(np.uint8)


def despeckle(a, passes=2):
    """Opt-in (Fig.despeckle = True): an opaque pixel whose four neighbours are opaque, all of
    one other colour, takes that colour (the lone rim and shade pixels checks.py warns about)."""
    a = a.copy()
    for _ in range(passes):
        rgb = a[..., :3].astype(np.int64)
        op = a[..., 3] > 0
        key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
        k = key[1:-1, 1:-1]
        nb = [key[:-2, 1:-1], key[2:, 1:-1], key[1:-1, :-2], key[1:-1, 2:]]
        on = op[:-2, 1:-1] & op[2:, 1:-1] & op[1:-1, :-2] & op[1:-1, 2:] & op[1:-1, 1:-1]
        m = on & (nb[0] != k) & (nb[0] == nb[1]) & (nb[1] == nb[2]) & (nb[2] == nb[3])
        if not m.any():
            break
        inner = a[1:-1, 1:-1]
        src = a[:-2, 1:-1]
        inner[m] = src[m]
    return a


def to_img(a):
    return Image.fromarray(a, 'RGBA')


def zoom(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def trim_box(arrs, pad=2):
    """Common bounding box of several RGBA arrays."""
    m = np.zeros(arrs[0].shape[:2], bool)
    for a in arrs:
        m |= a[..., 3] > 0
    ys, xs = np.where(m)
    return xs.min() - pad, ys.min() - pad, xs.max() + 1 + pad, ys.max() + 1 + pad
