"""Contract v2: three-quarter facings (SE, NE, SW, NW) for builds that draw their torso and head
as flat S (front) and N (back) drawings.

`Warp` wraps such a drawing round the body and turns it to the facing.  A point of the S drawing
at (x, y) (offsets from the axis; S shows the character's right side on the screen left) is the
point of a surface with lateral coordinate -x and forward depth d(x, y): an elliptic cylinder
(half width W, half depth D) for a torso, a sphere (D = W, the depth shrinking toward the top and
bottom) for a head.  That 3D point goes through the rig's projection (parts.proj, the same as the
limbs), so a buckle moves toward the facing, the near flank widens, the far flank narrows and
folds out of sight at the terminator, and the near side sits a little lower (K).  The N drawing
is the back of the same surface.  Nothing is flipped: in SW and NW (drawn on the rig's mirrored
grid) the drawing keeps its own sides, so a left-hip pouch stays on the left hip.

    with turn.Warp(f, R, cx, W, D, 'S'):                         # the near half (front in SE, SW)
        draw_front(...)
    with turn.Warp(f, R, cx, W, D, 'N', far=True, sphere=True, cy=hy):   # far half of a head
        draw_back(...)

Inside, every mask primitive (ell, rect, cap, rell), polygon, pixel, segment and detail lands on
the turned surface; parts keep their warped grid for their tonemaps (ew.Part.xy).  Parts of the
far half sit just behind the near half (zoff) and no seam line is drawn where the two halves of
one material meet (ew: twin).  Shapes past the surface (ears, a brim) continue it linearly.
"""
import math

import numpy as np

import parts

N = 241


class Warp:
    def __init__(self, f, R, cx, W, D=None, view='S', far=False, zoff=None, cy=0.0, sphere=False, clip=None):
        self.f, self.R = f, R
        self.cx, self.cy = float(cx), float(cy)
        self.W = max(1.0, float(W))
        self.D = float(D if D is not None else 0.75 * W)
        self.view, self.far, self.sphere = view, far, sphere
        self.zoff = (-0.6 if far else 0.0) if zoff is None else zoff
        base = parts.MIRROR.get(R.facing, R.facing)
        self.a = math.radians(parts.ANG[base])
        self.mir = f.flip
        self.xs = np.linspace(-4 * self.W, 4 * self.W, N)
        self._cache = {}
        self.clip = clip

    # ------------------------------------------------------------------ the map for one row
    def _row(self, yrel):
        key = round(float(yrel) * 2) / 2 if self.sphere else 0.0
        if key in self._cache:
            return self._cache[key]
        W, D = self.W, self.D
        if self.sphere:
            s = math.sqrt(max(0.12, 1 - (key / W) ** 2))
            D = D * s                     # toward the crown and chin the head is shallower (a sphere),
                                          # but the drawing's own width is kept (hair, ears, a brim)
        xs = self.xs
        u = np.clip(xs / W, -1.0, 1.0)
        depth = D * np.sqrt(1 - u * u)
        if self.view == 'S':
            lat, fwd, y0 = -xs, depth, parts.K * depth
        else:
            lat, fwd, y0 = xs.copy(), -depth, parts.K * depth
        nf = np.sqrt(1 - u * u) / D * (1 if self.view == 'S' else -1)
        nl = np.where(np.abs(xs) < W, np.abs(u) / W, 1.0 / W) * np.sign(lat)
        if self.mir:
            lat, nl = -lat, -nl
        c, sn = math.cos(self.a), math.sin(self.a)
        gx = fwd * c - lat * sn
        gy = fwd * sn + lat * c
        X = gx - parts.SKEW * lat * c
        Y = parts.K * gy - y0
        vis = (nf * sn + nl * c) > -1e-3
        out = (X, Y, vis)
        self._cache[key] = out
        return out

    def fwd(self, x, y):
        X, Y, vis = self._row(y - self.cy)
        dx = x - self.cx
        i = int(np.clip(np.searchsorted(self.xs, dx), 1, N - 1))
        t = (dx - self.xs[i - 1]) / (self.xs[i] - self.xs[i - 1])
        Xi = X[i - 1] + (X[i] - X[i - 1]) * t
        Yi = Y[i - 1] + (Y[i] - Y[i - 1]) * t
        if not (vis[i - 1] or vis[i]):           # out of sight: onto the rim (zero width)
            vx = X[vis]
            Xi = vx.max() if Xi > vx.mean() else vx.min()
            return self.cx + Xi, y + Yi, False
        return self.cx + Xi, y + Yi, True

    def __enter__(self):
        f = self.f
        self.saved = (f.X, f.Y, f.poly, f.pixels, getattr(f, '_xy', None), getattr(f, '_zoff', 0.0), getattr(f, '_twin', None),
                      getattr(f, '_clip', None))
        Xs, Ys = f.X, f.Y
        Xd = np.full(Xs.shape, 1e4)
        Yd = Ys.copy()
        for r in range(Xs.shape[0]):
            yrow = Ys[r, 0]
            X, Y, vis = self._row(yrow - self.cy)
            if not vis.any():
                continue
            fx, xs, dy = X[vis], self.xs[vis], Y[vis]
            o = np.argsort(fx)
            fx, xs, dy = fx[o], xs[o], dy[o]
            Xt = Xs[r] - self.cx
            ins = (Xt >= fx[0]) & (Xt <= fx[-1])
            Xd[r] = np.where(ins, self.cx + np.interp(Xt, fx, xs), 1e4)
            Yd[r] = Ys[r] - np.interp(Xt, fx, dy)
        f.X, f.Y = Xd, Yd
        f._xy = (Xd, Yd)
        f._zoff = self.saved[5] + self.zoff
        f._twin = 'far' if self.far else 'near'
        if self.clip is not None:
            f._clip = self.clip
        poly0, pix0 = self.saved[2], self.saved[3]
        warp = self

        def poly(pts):
            res = []
            n = len(pts)
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                k = max(1, int(math.hypot(x1 - x0, y1 - y0) / 1.5))
                for j in range(k):
                    t = j / k
                    x, y, _ = warp.fwd(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
                    res.append((x, y))
            return poly0(res)

        def pixels(pts):
            out = []
            for x, y in pts:
                X, Y, ok = warp.fwd(x, y)
                if ok:
                    out.append((X, Y))
            return pix0(out)
        f.poly, f.pixels = poly, pixels
        return f

    def __exit__(self, *a):
        f = self.f
        f.X, f.Y, f.poly, f.pixels, f._xy, f._zoff, f._twin, f._clip = self.saved
