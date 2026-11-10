"""Contract v2: surface helpers for the 3/4 facings (SE, NE and their mirrored SW, NW).

The torso is an elliptic cylinder round the body axis (half width w across, half depth d front to
back); a feature on it (buckle, button, strap, hem, lapel) is a point on that surface, projected
by the facing's Rig and drawn only where the surface faces the camera (vis > 0).  The head is a
sphere: a shape drawn for the S view (dx right, dy down from the head centre) is wrapped onto
the front of the sphere, a shape drawn for the N view onto the back, and projected, so the S and
N heads' own features land where they belong in any facing.  Nothing here is a flipped or
squashed image; every point goes through parts.proj.
"""
import math

import numpy as np


def ring(R, c3, up, w, d, th):
    """Screen point and facing (vis, -1..1) of the cylinder point at angle th (0 = front,
    + toward the character's right) at height up, round the axis through c3 (fwd, -, lat)."""
    p3 = (c3[0] + d * math.cos(th), up, c3[2] + w * math.sin(th))
    return R.p(p3), R.vis((math.cos(th) / d, 0.0, math.sin(th) / w))


def arc(R, c3, up, w, d, n=48, vmin=0.0, ths=None):
    out = []
    for th in (ths if ths is not None else np.linspace(-math.pi, math.pi, n)):
        (x, y), v = ring(R, c3, up, w, d, th)
        if v >= vmin:
            out.append((th, x, y, v))
    return out


def extremes(R, c3, up, w, d):
    """Leftmost and rightmost screen x of the ring (the silhouette at that height)."""
    xs = [ring(R, c3, up, w, d, th)[0][0] for th in np.linspace(-math.pi, math.pi, 72)]
    return min(xs), max(xs)


def band(f, R, c3, up0, up1, w, d, vmin=-0.02):
    """Polygon mask of the visible band of the cylinder between heights up0 < up1."""
    top = sorted(arc(R, c3, up1, w, d, 64, vmin), key=lambda q: q[1])
    bot = sorted(arc(R, c3, up0, w, d, 64, vmin), key=lambda q: q[1])
    if len(top) < 2 or len(bot) < 2:
        return None
    return f.poly([(x, y) for _, x, y, _ in top] + [(x, y) for _, x, y, _ in reversed(bot)])


def panel(f, R, c3, th0, th1, up_top, up_bot, w, d, n=12, flare=1.0, vmin=None):
    """Mask of a surface panel between angles th0..th1 and heights up_top (fn of th or number)
    and up_bot; flare widens the bottom edge (a skirt or coat tail).  vmin: drop the panel where
    it faces away more than this (None keeps it all; the caller picks the depth)."""
    ths = np.linspace(th0, th1, n)
    ut = up_top if callable(up_top) else (lambda th: up_top)
    ub = up_bot if callable(up_bot) else (lambda th: up_bot)
    top = [ring(R, c3, ut(t), w, d, t) for t in ths]
    bot = [ring(R, c3, ub(t), w * flare, d * flare, t) for t in ths]
    if vmin is not None and max(v for _, v in top) < vmin:
        return None
    return f.poly([p for p, _ in top] + [p for p, _ in reversed(bot)])


def path_on(R, c3, w, d, a, b, n=14):
    """Points along the surface from a = (th, up) to b = (th, up), each with its vis."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(ring(R, c3, a[1] + (b[1] - a[1]) * t, w, d, a[0] + (b[0] - a[0]) * t))
    return out


def strap(f, pts, r=1.5, vmin=0.05):
    """Mask of a strap following path_on points, only where it faces the camera."""
    m = None
    for ((x0, y0), v0), ((x1, y1), v1) in zip(pts[:-1], pts[1:]):
        if min(v0, v1) < vmin:
            continue
        c = f.cap(x0, y0, x1, y1, r)
        m = c if m is None else m | c
    return m


def boot_3q(f, R, foot3, mat_, z, dim=0, shaft=0, cuff=True, shade=None):
    """A boot seen three-quarter: the toe pushed along the projected forward direction, a flat
    sole, an optional tall shaft (shaft px)."""
    fx, fy = R.p(foot3)
    tx, ty = R.p((foot3[0] + 2.2, foot3[1], foot3[2]))
    dx, dy = tx - fx, ty - fy
    m = f.ell(fx + dx, fy - 2.6 + dy * 0.5, 4.9, 3.0) | f.rect(fx - 3.7, fy - 8, fx + 3.7, fy - 2)
    m &= f.Y < fy + max(0.0, dy)
    sh0 = dict(rl=1.6, rs=2.2)
    if shade:
        sh0.update({k: v for k, v in shade.items() if k in ('rl', 'tl')})
    f.add(m, mat_, z=z, dim=dim, line='hard', tonemap=(lambda X, Y, t: cyl_highlight(f, X, Y, t, fx + dx * 0.6)) if shade else None, **sh0)
    if shaft:
        sh = dict(rl=1.4, rs=2.2)
        sh.update(shade or {})
        f.add(f.rect(fx - 3.7, fy - 7 - shaft, fx + 3.7, fy - 6) | f.ell(fx, fy - 7 - shaft, 3.7, 1.5), mat_, z=z + 0.1,
              dim=dim, line='hard', tonemap=lambda X, Y, t: cyl_highlight(f, X, Y, t, fx), **sh)
        f.add(f.rect(fx - 4.1, fy - 7.5 - shaft, fx + 4.1, fy - 5.5 - shaft), mat_, z=z + 0.2, flat=3 if not dim else 2,
              dim=dim, line='hard')
    elif cuff:
        f.add(f.rect(fx - 4.1, fy - 9, fx + 4.1, fy - 6) & f.ell(fx, fy - 7.5, 4.7, 3), mat_, z=z + 0.5, flat=1,
              line='soft', dim=dim)
    return fx, fy


def cyl_highlight(f, X, Y, t, cx, off=1.8, w=0.7):
    """A cylinder's highlight: a 1 px light band left of centre (screen terms, mirror-safe) on
    the base tone, so a boot shaft or a sleeve reads round."""
    sx = -1 if f.flip else 1
    m = (np.abs(X - (cx - off * sx)) < w) & (t == 2)
    out = t.copy()
    out[m] = 3
    return out


def left_light(m, t, w=2, tone=2):
    """The w px of a part nearest the light (screen left, in array columns, so mirrored figures
    are lit the same way) take the light tone: a lit edge plane on long cloth such as coat tails."""
    c = np.cumsum(m, axis=1)
    band = m & (c >= 1) & (c <= w)
    out = t.copy()
    out[band & (t == tone)] = 3
    return out


# ------------------------------------------------------------------------------------ head
def ellpts(cx, cy, rx, ry, n=24):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def on_sphere(R, c3, dx, dy, r, back=False, bulge=0.85):
    """An S-view point (dx right, dy down from the head centre) wrapped onto the front of the
    head sphere (back=True: an N-view point onto the back), projected.  Returns (x, y, depth)."""
    lat = dx if back else -dx
    q = r * r - dx * dx - dy * dy
    fwd = math.sqrt(max(0.0, q)) * bulge * (-1 if back else 1)
    p3 = (c3[0] + fwd, c3[1] - dy, c3[2] + lat)
    x, y = R.p(p3)
    return x, y, R.d((fwd, 0.0, lat))


def sphere_poly(f, R, c3, pts, r, back=False):
    """Mask of an S-view (or N-view, back=True) polygon wrapped onto the head sphere."""
    return f.poly([on_sphere(R, c3, x, y, r, back)[:2] for x, y in pts])


def sphere_ell(f, R, c3, cx, cy, rx, ry, r, back=False, n=24):
    return sphere_poly(f, R, c3, ellpts(cx, cy, rx, ry, n), r, back)
