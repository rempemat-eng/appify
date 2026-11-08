"""Pale speck scatter: Matt's "terrazzo of specks" (U1, 25 Oct; the 8 Nov Undercroft audit, G-2, P-2,
SE-2, L-3). Texture drawn as an even scatter of tiny pale dots (two to six pixels, each lighter than
the stone round it) reads as terrazzo, not as stone. Stone texture is sibling clusters at the same
value, a few a tone up only on the lit side, gathered in drifts (house-style.md, "Clusters").

    speck_scatter(rgba)  ->  pale specks per 1000 opaque pixels

A speck is a 4-connected run of one colour, 2 to 6 pixels, at least two pixels inside the
silhouette, whose mean luminance is at least `lift` above the median of the opaque pixels in the
9 x 9 window round it, and which sits in a calm field (three quarters of the pixels round it are one
colour): a dot on a flat ground, not a lit arris, a rivet head or a pebble's crown at an edge. A dot
of another material in a calm field (tan lichen on grey stone, a moss dash) counts too; light (the
glow in a carved glyph, a flame, a crystal) does not. The Undercroft's pieces before the 8 Nov redraw scored 4 to 14 (the plates, seals and
levers), after it under 1.5.
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import ndimage as ndi

LIMIT = 2.0          # specks per 1000 opaque pixels
GLOWS = {'dusk', 'snow', 'lamp', 'lava'}   # light in a glyph, a flame, a crystal: not texture


def _lum(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(float)
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


@functools.lru_cache(maxsize=4096)
def _family(colour_key: int):
    """The parent ramp of a house colour (None off the palette)."""
    from scripts.art.native import palette as PAL
    c = ((colour_key >> 16) & 255, (colour_key >> 8) & 255, colour_key & 255)
    e = PAL.code_of(c)
    if e is None or e == 'ink':
        return e
    return PAL.parent(e[0])


def speck_scatter(rgba: np.ndarray, lift: float = 16.0, sizes=(2, 6)) -> float:
    rgba = np.asarray(rgba)
    if rgba.shape[-1] == 4:
        op = rgba[..., 3] > 128
    else:
        op = np.ones(rgba.shape[:2], bool)
    rgb = rgba[..., :3].astype(np.int32)
    key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    key = np.where(op, key, -1)
    L = _lum(rgb)
    # the local median round each pixel (9 x 9); transparent pixels take the opaque mean, and specks
    # within two pixels of the silhouette are not counted, so the edge barely matters
    med = ndi.median_filter(np.where(op, L, L[op].mean() if op.any() else 0), size=9)
    inner = ndi.binary_erosion(op, iterations=2)
    H, W = op.shape
    n = 0
    for k in np.unique(key[op]):
        lab, cnt = ndi.label(key == k)
        if not cnt:
            continue
        fam_k = None
        for lid, sl in enumerate(ndi.find_objects(lab), start=1):
            if sl is None or (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) > 36:
                continue
            y0, y1 = max(0, sl[0].start - 1), min(H, sl[0].stop + 1)
            x0, x1 = max(0, sl[1].start - 1), min(W, sl[1].stop + 1)
            c = lab[y0:y1, x0:x1] == lid
            area = int(c.sum())
            if not (sizes[0] <= area <= sizes[1]) or not inner[y0:y1, x0:x1][c].all():
                continue
            ring = ndi.binary_dilation(c) & ~c
            kr = key[y0:y1, x0:x1][ring]
            v, cnt_ = np.unique(kr, return_counts=True)
            if cnt_.max() < 0.75 * ring.sum():              # not in a calm field
                continue
            lift_ = L[y0:y1, x0:x1][c].mean() - med[y0:y1, x0:x1][c].mean()
            if fam_k is None:
                fam_k = _family(int(k)) or ''
            if fam_k in GLOWS:
                continue
            fr = _family(int(v[np.argmax(cnt_)]))
            foreign = fam_k not in ('', 'ink') and fr not in (None, 'ink') and fr != fam_k
            if lift_ >= lift or foreign:                    # a pale dot, or a dot of another material (lichen,
                n += 1                                      # moss dashes): the terrazzo's mark
    return 1000.0 * n / max(1, int(op.sum()))
