"""Detail and craft measures for one object (a sprite with alpha, or an object mask on a
screen), and the per-object detail bar against Eastward at the same character height.

The measures are robust to JPEG (Eastward's official shots are JPEG at quality 90): flat
means smooth (a 3 x 3 neighbourhood within FLAT_TOL of luminance), tones are 16-level colour
bins, so our PNGs and their JPEGs are counted the same way.

Per part (a connected run of one material family inside the object):

  flat        the largest smooth patch as a share of the part, and its size in H^2
  tones       colour bins covering at least 2 px
  planes      luminance bands (12 L wide) holding at least 8 % of the part: a solid form
              shows a lit top, a mid front and a dark side (3 planes or more)
  lrange      p90 - p10 of luminance across the part
  grad        the fitted luminance slope per H along x and y (light from the upper left
              gives a negative slope in both)
  edges       the share of the part's pixels that touch a different colour inside the part
              (staves, grain, courses, bevels, leaf clusters)

Per object: outline share, thin-dark-stroke share (canopy contour mesh), lone pixels,
floating parts, stilts, dotted lines, repeated identical parts, water depth and half discs.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .core import Finding, hsv, lum, keys, regions, slice_box

FLAT_TOL = 7          # L units: a 3 x 3 neighbourhood this even is a smooth (flat) patch
MIN_PART = 0.012      # parts smaller than this many H^2 are not judged


def family_map(rgb: np.ndarray) -> np.ndarray:
    """A material family per pixel: 0 outline, 1 green, 2 blue, 3 brown/wood, 4 red, 5 grey,
    6 pale, 7 yellow, 8 violet, 9 other."""
    h, s, v = hsv(rgb)
    f = np.full(h.shape, 9, np.int8)
    f[(s < 0.2) & (v >= 0.25)] = 5
    f[(s < 0.2) & (v >= 0.78)] = 6
    sat = (s >= 0.2) & (v >= 0.25)
    f[sat & (h >= 62) & (h < 170)] = 1
    f[sat & (h >= 170) & (h < 255)] = 2
    f[sat & (h >= 255) & (h < 330)] = 8
    f[sat & ((h < 12) | (h >= 330))] = 4
    f[sat & (h >= 12) & (h < 45)] = 3
    f[sat & (h >= 45) & (h < 62)] = 7
    f[v < 0.25] = 0
    return f


FAMILY = {0: 'outline', 1: 'foliage', 2: 'water', 3: 'wood', 4: 'red', 5: 'stone', 6: 'pale',
          7: 'straw', 8: 'violet', 9: 'other'}


def smooth_mask(L: np.ndarray) -> np.ndarray:
    mx = ndi.maximum_filter(L, size=3)
    mn = ndi.minimum_filter(L, size=3)
    return (mx - mn) <= FLAT_TOL


def part_metrics(rgb: np.ndarray, part: np.ndarray, H: float) -> dict:
    L = lum(rgb)
    area = int(part.sum())
    sm = smooth_mask(L) & part
    lab, n = ndi.label(sm)
    big = 0
    if n:
        big = int(np.bincount(lab[lab > 0]).max())
    k = keys(rgb, 16)[part]
    _, cnt = np.unique(k, return_counts=True)
    tones = int((cnt >= 2).sum())
    lv = L[part]
    bands = np.floor(lv / 12).astype(int)
    _, bc = np.unique(bands, return_counts=True)
    planes = int((bc >= 0.08 * area).sum())
    lrange = float(np.percentile(lv, 90) - np.percentile(lv, 10))
    ys, xs = np.nonzero(part)
    gx = gy = 0.0
    if area >= 8 and xs.std() > 0.5 and ys.std() > 0.5:
        A = np.vstack([xs - xs.mean(), ys - ys.mean(), np.ones(area)]).T
        coef, *_ = np.linalg.lstsq(A, lv, rcond=None)
        gx, gy = float(coef[0] * H), float(coef[1] * H)
    kk = keys(rgb, 32)
    diff = np.zeros(part.shape, bool)
    diff[:, 1:] |= (kk[:, 1:] != kk[:, :-1]) & part[:, :-1]
    diff[:, :-1] |= (kk[:, 1:] != kk[:, :-1]) & part[:, 1:]
    diff[1:] |= (kk[1:] != kk[:-1]) & part[:-1]
    diff[:-1] |= (kk[1:] != kk[:-1]) & part[1:]
    inner = part & ndi.binary_erosion(part)
    edges = float((diff & inner).sum() / max(1, inner.sum()))
    return dict(area=area, area_h=area / (H * H), flat=big / max(1, area), flat_h=big / (H * H),
                tones=tones, planes=planes, lrange=lrange, gx=gx, gy=gy, edges=edges)


def parts(rgb: np.ndarray, mask: np.ndarray, H: float):
    """Material parts of an object: connected runs of one family (outline excluded), at least
    MIN_PART H^2."""
    fam = family_map(rgb)
    out = []
    for f in np.unique(fam[mask]):
        if f == 0:
            continue
        m = mask & (fam == f)
        m = ndi.binary_closing(m, iterations=1) & mask
        lab, regs = regions(m, min_area=max(12, int(MIN_PART * H * H)))
        for lid, sl, a in regs:
            out.append((int(f), lab == lid, slice_box(sl)))
    return out


def thin_dark(rgb: np.ndarray, mask: np.ndarray) -> float:
    """The share of an area drawn as 1 px dark strokes: pixels darker than both neighbours
    along x or along y by at least 18 L. Contour-mesh canopies are full of them."""
    L = lum(rgb)
    t = np.zeros(L.shape, bool)
    t[:, 1:-1] |= (L[:, 1:-1] < L[:, :-2] - 18) & (L[:, 1:-1] < L[:, 2:] - 18)
    t[1:-1] |= (L[1:-1] < L[:-2] - 18) & (L[1:-1] < L[2:] - 18)
    inner = mask & ndi.binary_erosion(mask, iterations=1)
    return float((t & inner).sum() / max(1, inner.sum()))


def lone_pixels(rgb: np.ndarray, mask: np.ndarray) -> float:
    k = keys(rgb, 16)
    p = np.pad(k, 1, mode='edge')
    c = p[1:-1, 1:-1]
    same = (p[:-2, 1:-1] == c) | (p[2:, 1:-1] == c) | (p[1:-1, :-2] == c) | (p[1:-1, 2:] == c)
    inner = mask & ndi.binary_erosion(mask, iterations=1)
    return float((~same & inner).sum() / max(1, inner.sum()))


def outline_share(rgb: np.ndarray, alpha: np.ndarray) -> float:
    """The share of a sprite's silhouette edge drawn in a dark edge tone (the house outline or
    the material's own darkest tone)."""
    edge = alpha & ~ndi.binary_erosion(alpha)
    if edge.sum() == 0:
        return 0.0
    L = lum(rgb)
    inner = alpha & ndi.binary_erosion(alpha, iterations=2)
    ref = np.median(L[inner]) if inner.any() else np.median(L[alpha])
    return float(((L[edge] < 0.62 * ref) | (L[edge] < 60)).mean())


# ------------------------------------------------------------------------------------------
# Thresholds (calibrate.py): Matt's flagged sprites must fail, Eastward props must pass.
T = dict(
    flat=0.40,          # a part whose largest smooth patch is over 40 % of it ...
    flat_h=0.010,       # ... and over 0.01 H^2 (55 texels in the game) is flat
    planes=3,           # fewer luminance planes than this and the part has no volume
    lrange=45,          # and a luminance spread under 45 L (or any part under 20 L), with smooth
                        # patches (flat >= 0.1: JPEG-textured reference parts never trip it)
    edges=0.20,         # wood, stone and metal parts need this much drawn texture
    light=-6.0,         # a part lit from the right: x slope above +6 L per H against the house light
    mesh=0.16,          # canopy thin dark strokes above 16 % of the crown is contour mesh
    outline=0.55,       # under 55 % of the silhouette in an edge tone: the outline is broken
    water_tones=5,
)
TEXTURED = {3, 5, 8, 9}     # wood, stone, violet (paint), other: need drawn texture


def judge_object(rgb, mask, H, subject='', box0=(0, 0), kind=''):
    """Detail findings for one object. `box0` offsets the boxes into the reviewed picture."""
    fs = []
    ox, oy = box0
    big_parts = []
    water_kind = any(k in (subject + kind) for k in ('well', 'trough', 'tub', 'bucket', 'fountain', 'basin',
                                                      'pond', 'pool', 'water', 'flow', 'ground'))
    for f, pm, pb in parts(rgb, mask, H):
        m = part_metrics(rgb, pm, H)
        name = FAMILY[f]
        b = (pb[0] + ox, pb[1] + oy, pb[2] + ox, pb[3] + oy)
        if m['area_h'] < 0.02:
            continue
        big_parts.append((f, m))
        if f == 2:
            if not water_kind:
                continue          # slate, glass, paint: judged by the glyph and flat checks
            if m['tones'] < T['water_tones'] or m['flat'] > 0.5:
                fs.append(Finding('detail.water_flat', 'fault', b,
                                  f'{subject}: the water is flat: {m["tones"]} tones, one smooth patch covers {m["flat"]:.0%}',
                                  'give water depth: a dark band under the near rim, the inner wall lit or shaded '
                                  'as the opening curves, a 1 px light waterline and a few short highlights '
                                  '(eastward-edges.md 5.3)', score=m['flat'], threshold=0.5, subject=subject, extra=m))
            continue
        if m['flat'] > T['flat'] and m['flat_h'] > T['flat_h']:
            fs.append(Finding('detail.flat', 'fault', b,
                              f'{subject}: a flat {name} area: one smooth patch covers {m["flat"]:.0%} '
                              f'({m["flat_h"]:.3f} H^2), {m["tones"]} tones',
                              f'draw the {name} as its material: break the fill with its own structure (staves and hoops, '
                              'grain and nail heads, courses, bevels, leaf clusters) in 4 to 5 tones of its ramp',
                              score=m['flat'], threshold=T['flat'], subject=subject, extra=m))
        if f != 1 and m['flat'] >= 0.1 and ((m['planes'] < T['planes'] and m['lrange'] < T['lrange']) or m['lrange'] < 20):
            fs.append(Finding('detail.volume', 'fault', b,
                              f'{subject}: the {name} reads 2D: {m["planes"]} light planes, luminance spread {m["lrange"]:.0f}',
                              'give it volume: a lit top plane, a mid front and a dark side (or a cylinder: a highlight '
                              'band left of centre and a core shadow right), occlusion where parts meet, and thickness '
                              'on thin parts', score=float(m['planes']), threshold=T['planes'], subject=subject, extra=m))
        if f in TEXTURED and m['edges'] < T['edges'] and m['area_h'] >= 0.03:
            fs.append(Finding('detail.texture', 'fault', b,
                              f'{subject}: the {name} has no drawn material: only {m["edges"]:.0%} of it shows structure',
                              'draw the material: planks with grain and a lit edge, staves and hoops, stone courses '
                              'with chipped corners, a bevel on cut stone, a ring of rust on iron',
                              score=m['edges'], threshold=T['edges'], subject=subject, extra=m))
        if m['gx'] > -T['light'] and m['area_h'] >= 0.03 and m['lrange'] >= 20:
            fs.append(Finding('detail.light', 'polish', b,
                              f'{subject}: the {name} is lit from the right (luminance rises {m["gx"]:.0f} L per H to the east)',
                              'light from the upper left: lit faces west and north, dark faces east and south',
                              score=m['gx'], threshold=-T['light'], subject=subject, extra=m))
    fol = mask & (family_map(rgb) == 1)
    if fol.sum() >= 0.3 * H * H:
        td = thin_dark(rgb, ndi.binary_dilation(fol, iterations=1) & mask)
        if td > T['mesh']:
            ys, xs = np.nonzero(fol)
            fs.append(Finding('detail.mesh', 'fault', (xs.min() + ox, ys.min() + oy, xs.max() + 1 + ox, ys.max() + 1 + oy),
                              f'{subject}: the foliage is a contour mesh: {td:.0%} of it is 1 px dark strokes',
                              'build the crown from leaf clusters: stamped clumps with a lit cap and a dark U-shaped lower '
                              'rim, gaps showing the dark inside, no outline round every blob (art-style.md 4)',
                              score=td, threshold=T['mesh'], subject=subject))
    return fs, big_parts
