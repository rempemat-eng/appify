"""Pale speck scatter: a regression pin for Matt's "terrazzo of specks" (U1, 25 Oct; the 8 Nov
Undercroft audit, G-2, P-2, SE-2, L-3) on the Undercroft's six flat stone pieces (plate_up,
plate_down, lever_up, lever_down, seal_slab, seal_sunk) and its floor. It is not a general detector:
it is not calibrated on approved art and must not be wired into the asset gate. Round 2 of the
audit ran it on the 45 reviewer-passed assets and it failed 9 of them (the willow, sacks, boulder,
barrels, anvil, fences), and on other redrawn Undercroft pieces it counts structure (flute
highlights, lit facets, lit bark streaks) as specks.

    speck_scatter(rgba)  ->  pale specks per 1000 opaque pixels

A speck is an 8-connected run of one colour (so a dither checker's cells, which touch at their
corners, are one run, not specks), 2 to 6 pixels, at least two pixels inside the
silhouette, sitting in a calm field (three quarters of the pixels round it are one colour), which
is either at least `lift` lighter than the median of the 9 x 9 window round it, or of another
material than that field (tan lichen on grey stone, a moss dash). Light does not count: the dusk,
lamp and lava ramps, and the snow ramp only where it is the white core of a dusk glow (snow drawn as
a material counts).

`dark_speck_scatter` is the same count for dark grit (a tone under its field), which the round 3 floor
carried in its warm pools (G-16): its room 1 pool (scripts/review/fixtures/undercroft_r3_pool.png) scores
4.6 a 1000 px; the round 4 floor 0.3 (0.5 in the same box).

What it measured (8 Nov): the six stone pieces 3.1 to 4.0 and the floor 3.0 to 4.2 before the
redraw; after it the six pieces 0 to 1.64 and the floor under 1.0, against the limit of 2.0.
"""
from __future__ import annotations

import functools

import numpy as np
from scipy import ndimage as ndi

LIMIT = 2.0          # specks per 1000 opaque pixels
GLOWS = {'dusk', 'lamp', 'lava'}          # light in a glyph, a flame, a crystal: not texture


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


def speck_scatter(rgba: np.ndarray, lift: float = 16.0, sizes=(2, 6), dark: bool = False) -> float:
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
        # 8-connected: the cells of a 2 x 2 checker (a dithered light fade, eastward-edges 5.4) join into one
        # large run and are not counted; a terrazzo speck stands alone even diagonally
        lab, cnt = ndi.label(key == k, structure=np.ones((3, 3), bool))
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
            if dark:                                        # the dark form: grit a tone under its field
                lift_ = -lift_
            if fam_k is None:
                fam_k = _family(int(k)) or ''
            if fam_k in GLOWS:
                continue
            fr = _family(int(v[np.argmax(cnt_)]))
            if fam_k == 'snow' and fr == 'dusk':          # the white core of a glow, not snow on stone
                continue
            foreign = fam_k not in ('', 'ink') and fr not in (None, 'ink') and fr != fam_k
            if dark:
                foreign = False                             # (the dark form counts value only)
            if lift_ >= lift or foreign:                    # a pale dot, or a dot of another material (lichen,
                n += 1                                      # moss dashes): the terrazzo's mark
    return 1000.0 * n / max(1, int(op.sum()))


def dark_speck_scatter(rgba: np.ndarray, drop: float = 12.0, sizes=(2, 6)) -> float:
    """The dark form (8 Nov round 3, G-16): grit of 2 to 6 px a tone (`drop` L) under the calm field round it,
    per 1000 opaque px. The round 3 floor's warm pools held 16 to 17 of these (earth grit in the hearts)."""
    return speck_scatter(rgba, lift=drop, sizes=sizes, dark=True)
