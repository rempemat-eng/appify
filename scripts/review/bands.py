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
