"""Finding the things on a screen without scene data: everything that is not ground.

The ground of a screen is its calm field: the few colours that together cover half of it
(grass in two tones, a lawn's mottle, paving's main tones). Whatever is left after a 3 x 3
opening (which drops thin tufts and single-pixel dressing) is an object: a tree, a rock, a
bench, a mushroom, a path, the water. Each object gets simple features (its colour families,
size against H, solidity, how spiky its top is, its outline) that the logic checks use to
tell a trunk from a path or an agave from a fern. When a Godot scene is given, the sprites'
own boxes replace this guess (scene.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage as ndi

from .core import keys, hsv, lum, regions, slice_box, water_mask


@dataclass
class Obj:
    id: int
    box: tuple
    area: int
    mask: np.ndarray            # full-size bool mask
    fam: dict = field(default_factory=dict)   # colour family -> share
    kind: str = ''              # a guess: canopy, trunk, rosette, mushroom, rock, path, water, wood, other


def ground_palette(native: np.ndarray, share: float = 0.5, levels: int = 32):
    k = keys(native, levels)
    v, c = np.unique(k, return_counts=True)
    o = np.argsort(-c)
    cum = np.cumsum(c[o]) / c.sum()
    n = int(np.searchsorted(cum, share)) + 1
    return k, v[o[:n]]


def families(rgb: np.ndarray) -> dict:
    """Colour families of a set of pixels (N x 3), as shares."""
    if len(rgb) == 0:
        return {}
    h, s, v = hsv(rgb.reshape(-1, 1, 3))
    h, s, v = h.ravel(), s.ravel(), v.ravel()
    out = {
        'outline': (v < 0.25),
        'green': (h >= 55) & (h < 170) & (s >= 0.18) & (v >= 0.25),
        'blue': (h >= 170) & (h < 250) & (s >= 0.25) & (v >= 0.25),
        'brown': (h >= 8) & (h < 50) & (s >= 0.25) & (v >= 0.25) & (v < 0.85),
        'red': ((h < 12) | (h >= 330)) & (s >= 0.35) & (v >= 0.25),
        'pale': (s < 0.18) & (v >= 0.75),
        'grey': (s < 0.18) & (v >= 0.25) & (v < 0.75),
        'yellow': (h >= 40) & (h < 62) & (s >= 0.35) & (v >= 0.5),
    }
    return {k: float(m.mean()) for k, m in out.items()}


def segment(native: np.ndarray, H: float, min_area: float = 0.04) -> tuple[list[Obj], np.ndarray]:
    k, ground = ground_palette(native)
    g = np.isin(k, ground)
    obj = ~g
    if native.shape[-1] == 4:
        obj &= native[..., 3] > 0
    obj = ndi.binary_opening(obj, structure=np.ones((3, 3)))
    obj = ndi.binary_closing(obj, structure=np.ones((3, 3)))
    lab, regs = regions(obj, min_area=int(min_area * H * H))
    out = []
    for lid, sl, area in regs:
        m = lab == lid
        fam = families(native[..., :3][m])
        o = Obj(lid, slice_box(sl), area, m, fam)
        o.kind = classify(o, native, H)
        out.append(o)
    return out, obj


def classify(o: Obj, native, H) -> str:
    f = o.fam
    x0, y0, x1, y1 = o.box
    w, h = x1 - x0, y1 - y0
    if f.get('blue', 0) > 0.45:
        return 'water'
    if f.get('green', 0) > 0.55:
        if area_frac(o) < 0.62 and tips(o.mask[y0:y1, x0:x1]) >= 5 and h <= 1.2 * H:
            return 'rosette'
        return 'canopy' if (w * h > 0.8 * H * H) else 'plant'
    if f.get('brown', 0) > 0.45:
        if h >= 0.6 * H and h >= 1.4 * w and w <= 0.9 * H:
            return 'trunk'
        if w * h >= 2 * H * H:
            return 'path'
        return 'wood'
    if f.get('grey', 0) + f.get('pale', 0) > 0.5:
        return 'rock'
    return 'other'


def area_frac(o: Obj) -> float:
    x0, y0, x1, y1 = o.box
    return o.area / max(1, (x1 - x0) * (y1 - y0))


def tips(m: np.ndarray, prominence: float = 0.22) -> int:
    """How many spikes stand out of a shape's upper outline, seen from the middle of its base:
    peaks of the polar radius over the upper half-plane with a prominence of at least
    `prominence` of the largest radius."""
    ys, xs = np.nonzero(m)
    if len(ys) < 10:
        return 0
    cy, cx = ys.max() + 0.5, (xs.min() + xs.max() + 1) / 2
    ang = np.arctan2(cy - ys, xs - cx)          # 0 east, pi/2 up
    r = np.hypot(xs - cx, cy - ys)
    bins = np.linspace(-0.15, np.pi + 0.15, 61)
    idx = np.digitize(ang, bins) - 1
    prof = np.zeros(60)
    for i in range(60):
        sel = idx == i
        if sel.any():
            prof[i] = r[sel].max()
    if prof.max() <= 0:
        return 0
    p = prof / prof.max()
    n = 0
    for i in range(1, 59):
        if p[i] >= p[i - 1] and p[i] > p[i + 1]:
            left = p[max(0, i - 6):i].min()
            right = p[i + 1:i + 7].min()
            if p[i] - max(left, right) >= prominence:
                n += 1
    return n


def outline_share(o: Obj, native) -> float:
    """The share of an object's boundary that is drawn in a dark outline tone."""
    m = o.mask
    edge = m & ~ndi.binary_erosion(m)
    if edge.sum() == 0:
        return 0.0
    L = lum(native)
    return float((L[edge] < 70).mean())
