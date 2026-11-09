"""Tones and noise of the kit's prop pictures (PR #430, rounds 3 to 5).

    python3 -m scripts.art.kit.tone_audit [png ...]      # every farm, commons and rail picture by default

- **tones:** distinct colours (binned //16 per channel) per 16 x 16 patch at least 80 % opaque,
  averaged; a sprite with no such patch is measured in its best window (stride 2, at least 70 %
  opaque) and marked `w`. Targets (art-style.md, Claude A's reviews): animals 12, props 11,
  fences 9.
- **isolated:** the share of opaque pixels whose colour differs from all four neighbours
  (transparent neighbours count as different). Eastward builds its tones from a few large planned
  clusters (light plane, mid, core shadow, reflected light, rim), not scattered pixels; the target
  is 4 % or less, so a tone count can't be met with speckle (Claude A's review of the v4 images).
- **cluster:** the mean size in pixels of the four-connected runs of one colour.
- **specks:** the share of opaque pixels in runs of 3 pixels or fewer. The renderer's tidy pass
  already removes most single pixels, so speckle shows here first: a sponge-like coat is made of
  2 and 3 pixel runs. Target 15 % or less on animals and props.
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from scripts.art.kit.schema import ROOT

ISOLATED_MAX = 0.04
SPECKS_MAX = 0.15


def tones(rgba, n=16):
    a = rgba[..., :3].astype(int)
    m = rgba[..., 3] > 0
    out = []
    for y in range(0, a.shape[0] - n + 1, n):
        for x in range(0, a.shape[1] - n + 1, n):
            mm = m[y:y + n, x:x + n]
            if mm.mean() >= 0.8:
                out.append(len({tuple(v) for v in (a[y:y + n, x:x + n][mm] // 16).tolist()}))
    if out:
        return round(float(np.mean(out)), 1), False
    best = None
    for y in range(0, max(1, a.shape[0] - n + 1), 2):
        for x in range(0, max(1, a.shape[1] - n + 1), 2):
            mm = m[y:y + n, x:x + n]
            if mm.mean() >= 0.7:
                k = len({tuple(v) for v in (a[y:y + n, x:x + n][mm] // 16).tolist()})
                if best is None or mm.mean() > best[1]:
                    best = (k, mm.mean())
    return (float(best[0]) if best else None), True


def noise(rgba):
    """(isolated share, mean cluster size, specks share) over the opaque pixels."""
    m = rgba[..., 3] > 0
    key = (rgba[..., 0].astype(np.int64) << 16) | (rgba[..., 1].astype(np.int64) << 8) | rgba[..., 2].astype(np.int64)
    key = np.where(m, key, -1)
    pad = np.pad(key, 1, constant_values=-2)
    c = pad[1:-1, 1:-1]
    same = (pad[:-2, 1:-1] == c) | (pad[2:, 1:-1] == c) | (pad[1:-1, :-2] == c) | (pad[1:-1, 2:] == c)
    iso = float((m & ~same).sum()) / max(1, int(m.sum()))
    clusters = 0
    specks = 0
    for v in np.unique(key[m]):
        lab, n = ndi.label(key == v)
        clusters += n
        sizes = np.bincount(lab.ravel())[1:]
        specks += int(sizes[sizes <= 3].sum())
    total = max(1, int(m.sum()))
    return round(iso, 3), round(float(m.sum()) / max(1, clusters), 1), round(specks / total, 3)


def measure(path):
    rgba = np.asarray(Image.open(path).convert('RGBA'))
    t, window = tones(rgba)
    iso, cl, sp = noise(rgba)
    return {'tones': t, 'window': window, 'isolated': iso, 'cluster': cl, 'specks': sp}


def pictures():
    art = os.path.join(ROOT, 'game', 'kit', 'props', 'art')
    out = sorted(p for p in glob.glob(os.path.join(art, 'farm', '*.png')) + glob.glob(os.path.join(art, 'commons', '*.png'))
                 if not p.endswith('_idle.png'))
    return out


def main(argv=None) -> int:
    paths = (argv if argv is not None else sys.argv[1:]) or pictures()
    bad = 0
    for p in paths:
        r = measure(p)
        flag = '' if r['isolated'] <= ISOLATED_MAX and r['specks'] <= SPECKS_MAX else '  NOISY'
        bad += bool(flag)
        print('%-30s tones %5s%s  isolated %4.1f %%  specks %4.1f %%  cluster %5.1f px%s' % (
            os.path.basename(p), r['tones'], 'w' if r['window'] else ' ', 100 * r['isolated'], 100 * r['specks'], r['cluster'], flag))
    print('tone audit: %d pictures, %d noisy (isolated over %d %% or specks over %d %%)' % (len(paths), bad, round(100 * ISOLATED_MAX), round(100 * SPECKS_MAX)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
