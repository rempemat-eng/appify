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

Falls (woodland water review, round 5, W5-1). No official Eastward shot shows a falling sheet of
water: not the Steam store's 11 shots of the base game (all in the local set), not the 5 of the
Octopia DLC, nor the press images checked (Gematsu, 80.lv), searched on 5 Nov 2026. So a fall is
scored against its house sibling, the woodland's painted sheet (groups.fall, 17.0 tones and 39.5
shapes a patch through the same pipe), plus a direction check (fall_grain: changes across at least
4 x as often as down, a median vertical run of at least 6), never against borrowed mist. groups.mist
is 37's mist over a lawn and pines (round 4 called it "white water", wrongly; it is isotropic and
rewards a chip mosaic), kept as a number only:

    python3 -m scripts.review.bands --mist <folder of Eastward shots>       rebuilds groups.mist

When an official Eastward shot with a falling sheet is found, measure the sheet into a group of its
own (its source noted on its box) and score falls against it.
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
    """Ours against the Eastward band for `group` (prop, foliage, stone; fall is the house sibling); ratio 1 means
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


GRAIN_RATIO = 4.0          # a falling sheet: changes across at least 4 x as often as down
GRAIN_RUN = 6              # and a median vertical run of one colour of at least 6 texels


def fall_grain(rgb: np.ndarray, mask: np.ndarray, step: float = 8.0) -> dict:
    """The direction of a falling sheet's marks (woodland review, round 5, K5-1): the share of
    horizontal and of vertical neighbours inside `mask` whose lightness differs by more than `step`,
    their ratio (across / down; the woodland's sheet: 10.2, a chip mosaic about 1), and the median
    length of the vertical runs of one colour. Streaks that fall run long down and change across."""
    from .core import lum
    L = lum(rgb[..., :3]).astype(float)
    hm = mask[:, 1:] & mask[:, :-1]
    vm = mask[1:, :] & mask[:-1, :]
    h = float((np.abs(np.diff(L, axis=1)) > step)[hm].mean()) if hm.any() else 0.0
    v = float((np.abs(np.diff(L, axis=0)) > step)[vm].mean()) if vm.any() else 0.0
    key = (rgb[..., 0].astype(np.int64) << 16) | (rgb[..., 1].astype(np.int64) << 8) | rgb[..., 2]
    runs = []
    for x in range(rgb.shape[1]):
        col, m = key[:, x], mask[:, x]
        n = 0
        for y in range(rgb.shape[0]):
            if m[y] and n and col[y] == col[y - 1]:
                n += 1
            else:
                if n:
                    runs.append(n)
                n = 1 if m[y] else 0
        if n:
            runs.append(n)
    return dict(across=round(h, 4), down=round(v, 4), ratio=round(h / max(v, 1e-6), 2),
                median_run=float(np.median(runs)) if runs else 0.0,
                passed=bool(h / max(v, 1e-6) >= GRAIN_RATIO and (np.median(runs) if runs else 0) >= GRAIN_RUN))


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


# 37: mist over lawn and pines (round 5, W5-1: round 4 measured this box as "white water"; it holds
# no water), box-averaged from its 1920 x 1080 shot to 640 x 360, native px. Not a band for falls.
EW_MIST = {'37': [(560, 190, 640, 300, 'mist_over_lawn_and_pines'), (560, 170, 640, 300, 'mist_over_lawn_and_pines_top')]}

# the house sibling a fall is scored against until an Eastward sheet is measured (round 5, W5-1):
# the woodland's sheet, game/zones/woodland/art/ground.png 220-256 x 772-880, frame 0 overlaid,
# through jpeg_roundtrip and patch_counts as the auditor measured it
FALL_BAND = dict(tones=17.0, shapes=39.5, boxes=1, patches=12, source='house sibling: the woodland sheet, '
                 'game/zones/woodland/art/ground.png 220-256 x 772-880 (docs/reviews/2026-11-04-woodland-water.md, round 5)',
                 about='a falling sheet, crest and foam; no official Eastward shot shows one (bands.py)')


def build_water(folder: str) -> dict:
    """Measures EW_MIST in a local copy of the shots into groups.mist (a number only), and writes
    groups.fall (FALL_BAND), the band a waterfall is scored against (assets.group_of). The prop,
    stone, foliage and ground bands and construct.py's checks are untouched."""
    from PIL import Image as _I
    d = load_bands()
    adult = d.get('adult_native', 54)
    Hh = d.get('H', 74)
    rows = []
    for shot, boxes in EW_MIST.items():
        im = _I.open(os.path.join(folder, shot + '.jpg')).convert('RGB')
        nat = np.asarray(im.resize((640, 360), _I.BOX))
        for x0, y0, x1, y1, name in boxes:
            crop = _I.fromarray(nat[y0:y1, x0:x1, :3])
            s = Hh / adult
            big = np.asarray(crop.resize((int(crop.width * s), int(crop.height * s)), _I.NEAREST))
            pc = patch_counts(big, np.ones(big.shape[:2], bool), Hh)
            rows.append(dict(shot=f'eastward/{shot}.jpg', box=[x0, y0, x1, y1], name=name, group='mist',
                             patches=pc['patches'], tones=round(pc['tones'], 2), shapes=round(pc['shapes'], 2)))
    g = dict(tones=round(float(np.mean([r['tones'] for r in rows])), 2),
             shapes=round(float(np.mean([r['shapes'] for r in rows])), 2), boxes=len(rows),
             patches=int(sum(r['patches'] for r in rows)),
             about="37: mist over lawn and pines; not water, not a band for falls (round 5, W5-1)")
    d['boxes'] = [b for b in d.get('boxes', []) if b.get('group') not in ('water', 'mist')] + rows
    d.setdefault('groups', {}).pop('water', None)
    d['groups']['mist'] = g
    d['groups']['fall'] = dict(FALL_BAND)
    with open(BANDS, 'w') as f:
        json.dump(d, f, indent=1)
        f.write('\n')
    return g


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--ground', help='folder of the Eastward shots (local only): rebuild groups.ground')
    ap.add_argument('--mist', help='folder of the Eastward shots (local only): rebuild groups.mist and groups.fall')
    a_ = ap.parse_args()
    if a_.ground:
        print(json.dumps(build_ground(a_.ground), indent=1))
    if a_.mist:
        print(json.dumps(build_water(a_.mist), indent=1))
