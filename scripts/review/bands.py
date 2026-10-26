"""The per-object detail bar: an object's detail density next to Eastward's props at the
same character height.

Per patch of 0.25 H square (18 texels in the game, 14 native px in Eastward), over the
patches the object covers at least 60 %:

  tones   16-level colours covering at least 2 px
  shapes  4-connected one-colour regions of at least 2 px (planks, staves, stones, leaves)

Eastward's shots are JPEG (quality about 90) at 3 screen px a texel. To be fair, ours goes
through the same pipe first (3x nearest, JPEG at 90, back to the grid by centre samples),
and Eastward's native crop is brought to our H by nearest resampling (no colours invented).
The bands are numbers only (eastward_bands.json); the screenshots stay local
(scripts/review/calibrate.py --bands rebuilds them from a local copy).

The ground band (groups.ground) is measured the same way on Eastward's calm ground planes (the
dungeon floor in shade, lawns, a yard's dirt: calibrate_boxes.EW_GROUND) and adds one number, the
contrast between the pieces of the plane (`contrast`: the spread of the luminance after a median
over 0.12 H, which keeps flag against flag and drops joints and grain, less its blur over 0.5 H,
which is the light's gradient and not the pieces). A ground plane passes when
it is drawn (tones and shapes a patch at least the band's least, times GROUND_TOLERANCE) and calm
(contrast at most the band's most, times GROUND_CONTRAST_SLACK):

    python3 -m scripts.review.bands --ground <folder of Eastward shots>     rebuilds groups.ground
"""
from __future__ import annotations

import io
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from .core import keys

HERE = os.path.dirname(os.path.abspath(__file__))
BANDS = os.path.join(HERE, 'eastward_bands.json')
TOLERANCE = 0.9
GROUND_TOLERANCE = 0.9          # a ground plane's tones and shapes: at least 0.9 of Eastward's least
GROUND_CONTRAST_SLACK = 1.15    # its piece-to-piece contrast: at most 1.15 x Eastward's most


def jpeg_roundtrip(rgb: np.ndarray, scale: int = 3, quality: int = 90) -> np.ndarray:
    im = Image.fromarray(rgb[..., :3].astype(np.uint8))
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    big.save(buf, 'JPEG', quality=quality)
    buf.seek(0)
    back = np.asarray(Image.open(buf).convert('RGB'))
    c = scale // 2
    return back[c::scale, c::scale][:rgb.shape[0], :rgb.shape[1]]


def patch_counts(rgb: np.ndarray, mask: np.ndarray, H: float) -> dict:
    P = max(6, int(round(0.25 * H)))
    k = keys(rgb, 16)
    tones, shapes = [], []
    for y in range(0, rgb.shape[0] - P + 1, P):
        for x in range(0, rgb.shape[1] - P + 1, P):
            m = mask[y:y + P, x:x + P]
            if m.mean() < 0.6:
                continue
            kk = np.where(m, k[y:y + P, x:x + P], -1)
            v, c = np.unique(kk[kk >= 0], return_counts=True)
            tones.append(int((c >= 2).sum()))
            n = 0
            for val in v:
                lab, cnt = ndi.label(kk == val)
                if cnt:
                    sizes = np.bincount(lab.ravel())[1:]
                    n += int((sizes >= 2).sum())
            shapes.append(n)
    if not tones:
        return dict(patches=0, tones=0.0, shapes=0.0)
    return dict(patches=len(tones), tones=float(np.mean(tones)), shapes=float(np.mean(shapes)))


def load_bands() -> dict:
    if os.path.exists(BANDS):
        return json.load(open(BANDS))
    return {}


def score(rgb: np.ndarray, mask: np.ndarray, H: float, group: str = 'prop') -> dict:
    """Ours against the Eastward band for `group` (prop, foliage, stone, water); ratio 1 means
    as detailed as Eastward's mean."""
    bands = load_bands().get('groups', {})
    band = bands.get(group) or bands.get('prop')
    ours = patch_counts(jpeg_roundtrip(rgb), mask, H)
    if not band or ours['patches'] == 0:
        return dict(ours=ours, band=band, ratio=None, passed=None)
    rt = ours['tones'] / max(1e-6, band['tones'])
    rs = ours['shapes'] / max(1e-6, band['shapes'])
    r = min(rt, rs)
    return dict(ours=ours, band=band, ratio=round(float(r), 3), tones_ratio=round(float(rt), 3),
                shapes_ratio=round(float(rs), 3), passed=bool(r >= TOLERANCE))


def contrast(rgb: np.ndarray, mask: np.ndarray, H: float) -> float:
    """The contrast between the pieces of a plane (flag against flag, patch against patch), in L
    units: the spread of the luminance after a median over 0.12 H, less the light's gradient (its
    blur over 0.5 H), inside the mask."""
    from .core import lum
    L = lum(rgb)
    med = ndi.median_filter(L, size=max(3, int(round(0.12 * H))))
    # the light's own gradient (a pool, falloff into a corner) is not contrast between the pieces:
    # take it out with a blur over 0.5 H, normalised inside the mask
    w = ndi.gaussian_filter(mask.astype(float), 0.5 * H)
    trend = ndi.gaussian_filter(np.where(mask, med, 0.0), 0.5 * H) / np.maximum(w, 1e-6)
    med = med - trend
    inner = ndi.binary_erosion(mask, iterations=max(1, int(0.06 * H)))
    v = med[inner] if inner.sum() > 50 else med[mask]
    return float(v.std()) if v.size else 0.0


def ground_plane(rgb: np.ndarray, mask: np.ndarray, H: float, jpeg: bool = True) -> dict:
    """A large calm area judged as ground against Eastward's ground band, not the prop rule: it
    passes when its texture is drawn (tones and shapes a patch) and calm (piece-to-piece contrast).
    `jpeg` sends ours through Eastward's JPEG pipe first, as score() does."""
    band = load_bands().get('groups', {}).get('ground')
    src = jpeg_roundtrip(rgb) if jpeg else rgb[..., :3]
    pc = patch_counts(src, mask, H)
    con = contrast(rgb[..., :3], mask, H)
    if not band or pc['patches'] == 0:
        return dict(ours=pc, contrast=con, band=band, passed=None)
    drawn = (pc['tones'] >= GROUND_TOLERANCE * band['min_tones'] and
             pc['shapes'] >= GROUND_TOLERANCE * band['min_shapes'])
    calm = con <= GROUND_CONTRAST_SLACK * band['max_contrast']
    return dict(ours=pc, contrast=round(con, 2), band=band, drawn=bool(drawn), calm=bool(calm),
                passed=bool(drawn and calm))


def build_ground(folder: str) -> dict:
    """Measures calibrate_boxes.EW_GROUND in a local copy of the shots into groups.ground."""
    from PIL import Image as _I
    from .core import to_native
    from .calibrate_boxes import EW_GROUND
    d = load_bands()
    adult = d.get('adult_native', 54)
    Hh = d.get('H', 74)
    rows = []
    for shot, boxes in EW_GROUND.items():
        nat, _, _ = to_native(_I.open(os.path.join(folder, shot + '.jpg')), 3)
        for x0, y0, x1, y1, name in boxes:
            crop = nat[y0:y1, x0:x1, :3]
            im = _I.fromarray(crop)
            s = Hh / adult
            big = np.asarray(im.resize((int(im.width * s), int(im.height * s)), _I.NEAREST))
            m = np.ones(big.shape[:2], bool)
            pc = patch_counts(big, m, Hh)
            rows.append(dict(shot=f'eastward/{shot}.jpg', box=[x0, y0, x1, y1], name=name, group='ground',
                             patches=pc['patches'], tones=round(pc['tones'], 2), shapes=round(pc['shapes'], 2),
                             contrast=round(contrast(big, m, Hh), 2)))
    g = dict(tones=round(float(np.mean([r['tones'] for r in rows])), 2),
             shapes=round(float(np.mean([r['shapes'] for r in rows])), 2),
             min_tones=min(r['tones'] for r in rows), min_shapes=min(r['shapes'] for r in rows),
             max_contrast=max(r['contrast'] for r in rows), boxes=len(rows),
             patches=int(sum(r['patches'] for r in rows)))
    d['boxes'] = [b for b in d.get('boxes', []) if b.get('group') != 'ground'] + rows
    d.setdefault('groups', {})['ground'] = g
    with open(BANDS, 'w') as f:
        json.dump(d, f, indent=1)
        f.write('\n')
    return g


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--ground', required=True, help='folder of the Eastward shots (local only)')
    print(json.dumps(build_ground(ap.parse_args().ground), indent=1))
