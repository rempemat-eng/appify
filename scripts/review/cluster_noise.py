"""Cluster noise: random value noise in 2 x 2 clusters standing in for material (the detail audit of
the Act 1 props, docs/reviews/2026-11-04-act1-props.md, finding 4).

The house style allows grain in clusters of two texels or more, but "most clusters only swap to a
sibling ramp at the same tone (they add shape without value noise); a few step one tone up (more on
the lit side) or down" (house-style.md 4). A painter that steps a tone on a large share of 2 x 2
cells at random, whatever the form, raises the tone count and the detail bar while the surface
reads as terrazzo. Lone texels (one-pixel speckle) do not see it: the unit is the cluster.

**The measure.** The picture is cut into 2 x 2 blocks on the art grid. A block counts when it and
its whole 3 x 3 block neighbourhood are opaque (the interior: the outline and the silhouette's edge
are not material). Its baseline is form-aware: the median of the mean luminance of the nine blocks,
so it follows the light across a form, and the step from one part to the next only counts where it
is a single block wide. A block is noisy when its mean is more than 10 L from that baseline. The
share is noisy blocks over counted blocks.

**Calibration** (`python3 -m scripts.review.cluster_noise --calibrate`, at our character height:
Eastward's native 640 x 360 crops scaled 74/54 with nearest neighbour; the style anchors as drawn):

| | share |
| --- | --- |
| Eastward prop boxes (the audit's subjects, in `CALIBRATION`) | median 29.3 %, from 11.9 % (the rockfall in 17) to 47.0 % (a bench with two people on it in 12) |
| the style anchors (`kit/lantern`, `kit/bench`) | 29.6 %, 27.5 % |
| the Act 1 set as audited at 8f560abf | the landslip 54.9 %, the platform edge 52 %, the skep 34.8 %, kerb a 31.4 % (the audit: 54.4, 52.4, 35.2, 31.0) |

So a prop at or under `CALM` (32 %, the anchors' ceiling) reads as Eastward does; over `POLISH`
(40 %, past all but Eastward's busiest box) it is flagged; over `FAULT` (48 %, past every Eastward
box) it is a fault. The bar has to be earned with parts, joints and wear, not grain.

    python3 -m scripts.review.cluster_noise PNG [PNG ...]       # the share of each picture
    python3 -m scripts.review.cluster_noise --calibrate         # Eastward's boxes and the anchors
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from .core import Finding, lum

DELTA = 10.0           # L: a block this far from its neighbourhood's median steps a tone
CALM = 0.32            # the style anchors' ceiling
POLISH = 0.40          # over this: flagged (polish)
FAULT = 0.48           # over every Eastward prop box: a fault
MIN_BLOCKS = 12        # too small an interior to judge

# Eastward prop boxes (shot, native 640 x 360 box): the audit's subjects (churns, the lamp post, benches,
# rocks, the post box, the fence)
CALIBRATION = [
    ('17', (135, 47, 162, 112)), ('17', (340, 40, 392, 83)), ('13', (505, 295, 540, 350)),
    ('13', (375, 20, 415, 125)), ('17', (410, 15, 472, 55)), ('12', (180, 200, 248, 235)),
    ('17', (460, 165, 550, 250)), ('13', (325, 247, 350, 268)), ('12', (387, 200, 420, 248)),
    ('17', (305, 177, 450, 218)),
]


def share(rgb: np.ndarray, alpha: np.ndarray, delta: float = DELTA):
    """(share of noisy 2 x 2 blocks, the noisy-block mask at block scale, blocks counted), the share
    the mean over the four phases of the 2 x 2 grid (round 7 of the Act 1 detail audit, R7-6: on one
    grid the same pixels moved a texel scored anywhere from 48.9 to 59.5 %, so a part shifted by a
    texel could cross the fault line unchanged). The mask and the count are the grid at (0, 0)'s;
    `phases` gives each phase's share and the spread."""
    shares = []
    first = None
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
        s_, noisy, cnt = share_at(rgb[dy:, dx:], alpha[dy:, dx:], delta)
        if first is None:
            first = (noisy, cnt)
        if cnt:
            shares.append(s_)
    return (float(np.mean(shares)) if shares else 0.0), first[0], first[1]


def phases(rgb: np.ndarray, alpha: np.ndarray, delta: float = DELTA) -> list:
    """The share at each of the four phases of the 2 x 2 grid ((0,0), (0,1), (1,0), (1,1))."""
    return [share_at(rgb[dy:, dx:], alpha[dy:, dx:], delta)[0] for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1))]


def share_at(rgb: np.ndarray, alpha: np.ndarray, delta: float = DELTA):
    """(share of noisy 2 x 2 blocks, the noisy-block mask at block scale, blocks counted) on the grid
    that starts at the picture's corner."""
    H, W = alpha.shape
    h2, w2 = H // 2, W // 2
    if h2 < 3 or w2 < 3:
        return 0.0, np.zeros((max(h2, 0), max(w2, 0)), bool), 0
    L = lum(rgb[:h2 * 2, :w2 * 2]).reshape(h2, 2, w2, 2)
    A = alpha[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2)
    full = A.all(axis=(1, 3))
    mean = L.mean(axis=(1, 3))
    # the 3 x 3 block neighbourhood's median, over opaque blocks only
    pad = np.pad(np.where(full, mean, np.nan), 1, constant_values=np.nan)
    stack = np.stack([pad[dy:dy + h2, dx:dx + w2] for dy in range(3) for dx in range(3)], 0)
    with np.errstate(all='ignore'):
        n = np.sum(~np.isnan(stack), 0)
        med = np.nanmedian(np.where(n[None] > 0, stack, 0.0), 0)
    ok = full & (n == 9)
    noisy = ok & (np.abs(mean - med) > delta)
    cnt = int(ok.sum())
    return (float(noisy.sum()) / cnt if cnt else 0.0), noisy, cnt


def check(rgb: np.ndarray, alpha: np.ndarray, H: float, subject: str) -> list[Finding]:
    """The asset gate's cluster-noise finding on one object picture (alpha marks the object)."""
    s, noisy, cnt = share(rgb, alpha)
    if cnt < MIN_BLOCKS or s <= POLISH:
        return []
    ph = phases(rgb, alpha)
    ys, xs = np.nonzero(alpha)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    sev = 'fault' if s > FAULT else 'polish'
    return [Finding('detail.cluster_noise', sev, box,
                    f'{subject}: {s:.0%} of its 2 x 2 blocks (the mean of the grid\'s four phases, {min(ph):.0%} to {max(ph):.0%}) step more than {DELTA:.0f} L off their neighbourhood '
                    f'(Eastward\'s props median 29 %, the style anchors 28 to 30 %): random value grain, not material',
                    'drop the grain to sibling swaps at the same tone; step a tone on at most 10 % of cells, tied to the form '
                    '(+1 only on lit planes, -1 only in shade); earn the detail with parts, joints, wear and story details '
                    '(house-style.md 4)', score=s, threshold=POLISH if sev == 'polish' else FAULT, subject=subject)]


def share_png(path: str) -> float:
    a = np.asarray(Image.open(path).convert('RGBA'))
    return share(a[..., :3], a[..., 3] > 128)[0]


def eastward_box(folder: str, shot: str, box, char_scale: float = 74.0 / 54.0) -> np.ndarray:
    """A native 640 x 360 box of an Eastward shot (the jpgs are 1920 x 1080, 3 texels a native pixel)
    scaled to our character height with nearest neighbour, as RGB."""
    im = np.asarray(Image.open(os.path.join(folder, shot + '.jpg')).convert('RGB'))
    k = im.shape[1] // 640
    nat = im[k // 2::k, k // 2::k][:360, :640]
    x0, y0, x1, y1 = box
    crop = Image.fromarray(nat[y0:y1, x0:x1])
    return np.asarray(crop.resize((int(round(crop.width * char_scale)), int(round(crop.height * char_scale))), Image.NEAREST))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('png', nargs='*')
    ap.add_argument('--calibrate', action='store_true')
    ap.add_argument('--eastward', default=None, help='folder of Eastward shots (12.jpg, 13.jpg, 17.jpg)')
    a = ap.parse_args(argv)
    if a.calibrate:
        if a.eastward:
            vals = []
            for shot, box in CALIBRATION:
                rgb = eastward_box(a.eastward, shot, box)
                s = share(rgb, np.ones(rgb.shape[:2], bool))[0]
                vals.append(s)
                print('eastward %s %s %.1f %%' % (shot, box, 100 * s))
            print('eastward median %.1f %%, max %.1f %%' % (100 * float(np.median(vals)), 100 * max(vals)))
        from . import assets as AS
        for name in ('lantern', 'bench'):
            p = AS.render_kit(name)
            print('anchor kit/%s %.1f %%' % (name, 100 * share_png(p)))
    for p in a.png:
        print('%-60s %.1f %%' % (os.path.basename(p), 100 * share_png(p)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
