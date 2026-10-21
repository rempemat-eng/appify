"""The ground canvas at any density, kept as palette codes (family, tone) so shadows and light
pools step along the ramps instead of mixing colours; and the lawn's tuft sprite.

World coordinates are 1x art px (an adult 25 px); at density d one world px is d screen-art px.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from . import raster as pk


class Ground:
    def __init__(self, w: int, h: int, d: float, fams=('grass', 'grass_warm', 'grass_cool')):
        self.w, self.h, self.d = w, h, d
        self.fams = list(fams)
        self.fam = np.zeros((h, w), np.int16)     # index into self.fams
        self.tone = np.full((h, w), 3, np.int16)
        self.lock = np.zeros((h, w), bool)        # pixels owned by something else (paths, the cliff)

    def fi(self, name: str) -> int:
        if name not in self.fams:
            self.fams.append(name)
        return self.fams.index(name)

    def rgba(self) -> Image.Image:
        out = np.zeros((self.h, self.w, 4), np.uint8)
        for i, f in enumerate(self.fams):
            m = self.fam == i
            if not m.any():
                continue
            for t in range(7):
                mm = m & (self.tone == t)
                if mm.any():
                    out[mm, :3] = pk.rgb(f, t)
        out[..., 3] = 255
        return Image.fromarray(out, 'RGBA')

    def step(self, mask: np.ndarray, dt: int, lo: int = 0, hi: int = 5):
        self.tone[mask] = np.clip(self.tone[mask] + dt, lo, hi)


# ------------------------------------------------------------------------------------------------
# ground dressing: tufts and flowers as small sprites drawn in units (1 unit = 1 px at 2x)
# ------------------------------------------------------------------------------------------------
def tuft(d: float, seed: int, size: float = 1.0, fam='grass') -> Image.Image:
    """A tuft of 3 to 5 blades: dark roots, the body, lit tips; 8 to 14 units tall."""
    rng = np.random.default_rng(seed)
    s = d / 2
    Wu, Hu = 22 * size, 18 * size
    sp = pk.Sprite(int(math.ceil(Wu * s)) | 1, int(math.ceil(Hu * s)), s, (int(math.ceil(Wu * s)) | 1) / 2,
                   int(math.ceil(Hu * s)) - max(1, int(round(1 * s))))
    g = sp.g
    nb = int(rng.integers(4, 7))
    m = np.zeros((g.h, g.w), bool)
    tips = np.zeros_like(m)
    wbase = 2 if d >= 1.75 else 1
    for k in range(nb):
        a = (k - (nb - 1) / 2) / max(1, nb - 1)
        bx = a * 5.0 * size + rng.uniform(-0.6, 0.6)
        tx = bx + a * 8.0 * size + rng.uniform(-1.5, 1.5)
        ty = -(9.0 + rng.uniform(0, 5.0)) * size * (1.0 - 0.3 * abs(a))
        mx, my = bx + (tx - bx) * 0.45, ty * 0.5
        m |= g.line([(bx, 0), (mx, my)], wbase) | g.line([(mx, my), (tx, ty)], 1)
        tips |= g.line([(bx + (tx - bx) * 0.72, ty * 0.72), (tx, ty)], 1)
    # r4: the roots stand in one irregular dark mass 1 to 2 px tall (no comb of separate roots)
    base = np.zeros_like(m)
    for k in range(3):
        base |= g.ellipse(rng.uniform(-3.0, 3.0) * size, -0.6 * size, rng.uniform(2.5, 4.0) * size,
                          rng.uniform(1.0, 1.8) * size)
    # an irregular bottom edge (1 to 2 px of variation in runs, never alternating)
    cols = np.unique(g.X)
    edge = np.zeros_like(g.X)
    runv, run_left = 0.0, 0
    for cx in cols:
        if run_left <= 0:
            runv = rng.choice([0.0, -0.7, -1.4])
            run_left = int(rng.integers(2, 5))
        edge[g.X == cx] = runv
        run_left -= 1
    base &= g.Y <= 0.2 + edge
    m = (m | base) & ~g.rect(-50, 0.2, 50, 10)
    sp.add('blades', m, fam, base=2, lo=0, hi=4, z=1, flat=True, casts=False)
    sp.mark('blades', tips, 2)
    p_ = sp.part('blades')
    p_.famarr = np.where(tips, fam + '_warm', fam).astype(object)    # lit tips lean yellow (Eastward)
    # r2: no ruled base row; only the blade roots are a tone down
    sp.mark('blades', base & m, -1)
    return sp.render(outline=False, contact=False)


# ------------------------------------------------------------------------------------------------
# revision 2: Eastward ground on the soft grid (flat fields, grid-shaped patches and paths)
# ------------------------------------------------------------------------------------------------
CELL = 8          # world px: the 16 px soft grid at 2x (12 px at 1.5x)


# ------------------------------------------------------------------------------------------------
# revision 3: Eastward's frayed path, grid blobs, and sparse grass marks in drifts
# ------------------------------------------------------------------------------------------------


MARKS = [  # 4-connected stamps (art px), so no mark has a lone pixel: (dy, dx) lists
    [(0, 0), (1, 0), (1, 1)],                       # a tick
    [(0, 1), (1, 1), (1, 0), (2, 0)],               # a slanted blade
    [(0, 0), (1, 0), (2, 0), (2, 1), (1, 2), (2, 2)],   # a small V on a base
    [(0, 1), (1, 1), (2, 1), (2, 0)],               # a leaning blade
    [(0, 0), (0, 1), (1, 1)],                       # a short dash with a hook
]


