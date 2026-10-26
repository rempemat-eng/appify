"""Organic edges on the soft grid (density 3 and up).

Matt, 26 Oct 10:19, on the cast-v2 video's background (the park bench and the green-capped lamp,
a dirt path through the grass): "the lamp and bench are exactly the style i'm going for ... if all
of the paths look like this it would be better if they adhere to the soft grid more (also for
similar structures)". Their edges were per-pixel noise. Eastward's rims step one pixel at a time
in runs of 1 to 10 that lengthen and shorten slowly round a curve, bites and tufts are rounded
shapes, a sunken surface has a dark rim under the turf on its north side and the turf below it
catches the light (eastward-edges.md 1.4 to 1.6, 5.1; art-style.md 7).

    m = softedge.soft(mask)            # a texel mask: smooth runs, no one-texel spurs or bites
    softedge.rim(cv, m, ground)        # its dark north rim and the lit lip of the turf south of it

Every painter that draws a path, a worn patch, a puddle or pond, a burnt lot, a ring or a crater
at density 3 and up goes through these (screen.path_hd, screen.ground_detail_hd, town.build).
The review twin is scripts/review/edges.py (detail.ragged_edge).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from . import ctx
from .palette import step

CROSS = ndi.generate_binary_structure(2, 1)


def soft(mask: np.ndarray, smooth: float = 0.55, min_area: float = 3.0) -> np.ndarray:
    """The region of `mask` with its outline on the soft grid: smoothed at about `smooth` world px
    (so runs lengthen and shorten slowly), then every one-texel spur and bite removed (an opening
    and a closing with the 4-connected cross) and specks and pinholes under `min_area` world px^2
    dropped or filled."""
    D = ctx.D
    m = mask.astype(bool)
    if not m.any():
        return m
    f = ndi.gaussian_filter(m.astype(np.float32), max(0.5, smooth * D))
    m = f >= 0.5
    for _ in range(2):
        m = ndi.binary_closing(np.pad(m, 2), structure=CROSS)[2:-2, 2:-2]
        m = ndi.binary_opening(np.pad(m, 2), structure=CROSS)[2:-2, 2:-2]
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


def rim(cv: np.ndarray, m: np.ndarray, ground: np.ndarray, width: int = 1, lit: bool = True) -> None:
    """A sunken surface's edge: its texels under the turf on the north (and west) a tone down,
    `width` texels deep; the turf's texels just south of it a tone up (the lip catching the light).
    `ground` limits the lip to the turf (not paving, water or rock)."""
    above = np.zeros_like(m)
    above[1:] = m[:-1]
    left = np.zeros_like(m)
    left[:, 1:] = m[:, :-1]
    dark = m & (~above | ~left)                    # the north and west edge under the turf
    for k in range(1, width):
        nxt = np.zeros_like(dark)
        nxt[1:] = dark[:-1]
        dark |= nxt & m
    sel = dark & (cv % 8 < 6) & (cv % 8 > 0)
    cv[sel] = step(cv[sel], -1)
    if lit:
        lip = ~m & above & ground & (cv % 8 < 5)
        cv[lip] = step(cv[lip], 1)


def soil_marks(cv, mask, rng, drawn=None, spacing=1.0, p=0.7):
    """Bare ground drawn as ground (26 Oct): clods and pebbles lit at their upper left with a shade
    texel under them, and short cracks, a few world px apart, so trodden earth, ash and the burnt
    floor are never a flat fill."""
    D = ctx.D
    H, W = cv.shape
    sp_x, sp_y = max(4, int(round(2.2 * D * spacing))), max(3, int(round(1.7 * D * spacing)))
    for gy in range(0, H, sp_y):
        for gx in range((gy // sp_y) % 2 * (sp_x // 2), W, sp_x):
            y0, x0 = gy + int(rng.integers(-1, 2)), gx + int(rng.integers(-2, 3))
            if not (1 <= y0 < H - 3 and 1 <= x0 < W - 3) or not mask[y0, x0] or rng.random() > p:
                continue
            c0 = cv[y0, x0]
            if c0 % 8 >= 6:
                continue
            r = rng.random()
            if r < 0.45:                                            # a clod: lit cap, its shade below
                pts = (((0, 0), 1), ((0, 1), 1), ((1, 0), 0), ((1, 1), 0), ((2, 1), -1), ((2, 2), -1), ((1, 2), -1),
                       ((1, 0), 1))
            elif r < 0.75:                                          # a dip: shade at its north lip, lit south
                pts = (((0, 0), -1), ((0, 1), -1), ((1, 1), 1), ((1, 2), 1))
            else:                                                   # a crack
                pts = (((0, 0), -1), ((1, 0), -1), ((1, 1), -1), ((1, 2), -1), ((2, 2), -1))
            for (dy, dx), dt in pts:
                yy, xx = y0 + dy, x0 + dx
                if mask[yy, xx] and dt != 0:
                    cv[yy, xx] = step(cv[yy, xx], dt)
                    if drawn is not None:
                        drawn[yy, xx] = True
