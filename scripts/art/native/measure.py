"""The lawn measure every round of the perfected scene used (pilot2x perfect/MEASURE.md).

The mask: the open lawn from the terrain codes (the grass families, so no path, herb bed,
water, face or stair), minus every prop's box grown by 2 world px and a box round each walker,
eroded by one world px. The dressing (flowers, tufts) is lawn texture and stays in.

- edge share: of all right and down neighbour pairs inside the lawn, the share whose colours
  differ by more than 20 (Euclidean RGB); the meadow's band at 2x is 0.17 to 0.21
- lone px: pixels unlike all four neighbours, as a mean over 16 x 16 boxes at least 90 % lawn
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .palette import FI

LAWN_FAMS = ('grass', 'grass_warm', 'grass_cool')


def lawn_mask(plan: dict, d: float, codes: np.ndarray) -> np.ndarray:
    """codes: the terrain canvas cropped to the screen (compose.LAST['codes'])."""
    m = np.isin(codes // 8, [FI[f] for f in LAWN_FAMS])
    obj = np.zeros_like(m)
    g = 2
    for p in plan['props']:
        x0, y0, x1, y1 = p['box']
        obj[max(0, int((y0 - g) * d)):max(0, int((y1 + g) * d)), max(0, int((x0 - g) * d)):max(0, int((x1 + g) * d))] = True
    for w in plan['walkers']:
        fx, fy = w['foot']
        obj[max(0, int((fy - 30) * d)):int((fy + 3) * d), max(0, int((fx - 14) * d)):int((fx + 14) * d)] = True
    m &= ~obj
    return ndi.binary_erosion(m, iterations=max(1, int(d)))


def lawn(img, mask: np.ndarray, thr: float = 20.0) -> dict:
    a = np.asarray(img.convert('RGB')).astype(float)
    dh = np.sqrt(((a[:, 1:] - a[:, :-1]) ** 2).sum(2)) > thr
    dv = np.sqrt(((a[1:] - a[:-1]) ** 2).sum(2)) > thr
    mh, mv = mask[:, 1:] & mask[:, :-1], mask[1:] & mask[:-1]
    share = (dh[mh].sum() + dv[mv].sum()) / max(1, mh.sum() + mv.sum())
    k = (a[..., 0] * 65536 + a[..., 1] * 256 + a[..., 2]).astype(np.int64)
    P = np.pad(k, 1, mode='edge')
    lone = (k != P[:-2, 1:-1]) & (k != P[2:, 1:-1]) & (k != P[1:-1, :-2]) & (k != P[1:-1, 2:])
    ls = []
    for y in range(0, k.shape[0] - 15, 16):
        for x in range(0, k.shape[1] - 15, 16):
            if mask[y:y + 16, x:x + 16].mean() >= 0.9:
                ls.append(lone[y:y + 16, x:x + 16].mean())
    return dict(edge_share=float(share), lone_px=float(np.mean(ls)) if ls else 0.0, lawn_px=int(mask.sum()))
