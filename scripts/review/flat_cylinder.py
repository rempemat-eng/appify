"""Flat cylinders: a long round part (a log, a pipe, a post, a column) painted as a strip, with a
band of near-one tone that drops hard into its shadow and no mid tones between (the detail audit of
the Act 1 props, round 2: the landslip's birch, "1 row at 243 L, 3 at 233, 3 at 211, then a hard drop
to 87 and 57", missed by detail.volume two rounds running).

**The measure.** Down each column (for a part lying along x) and along each row (for a part standing
up), the luminance profile across the part is read. A column is flat where at least `RUN` texels in
a row stay within `SPREAD` L of each other and the very next texel drops by more than `DROP` L, so
the form goes from lit to dark in one step instead of turning through mid tones (a cylinder in the
house style turns in four or five steps of 20 to 45 L: house-style.md 3, 5). A part is a flat
cylinder where such columns run on, side by side at the same rows (within a texel), for at least
`LONG` texels: a strip, not a highlight on one stone.

    python3 -m scripts.review.flat_cylinder PNG [PNG ...]
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image

from .core import Finding, lum

RUN = 5          # texels of the near-flat band
SPREAD = 36.0    # L: the band's own spread (243, 233, 211 is 32)
DROP = 100.0     # L: the hard step out of it into the shade
LONG = 40        # texels: how long the strip must run to be a log or a pipe, not a board or a glint
MIN_L = 150.0    # the band is a lit band


MAXBAND = 9     # texels: a round part's lit band; a longer flat field is a panel, not a cylinder


def _hits(L: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """(H, W) bool: the texel where a flat lit band ends in a hard drop, down each column; the band
    is RUN to MAXBAND texels long and starts at an edge (transparent above it, or a texel at least
    40 L darker): a strip lit from above, not a lit panel."""
    H, W = L.shape
    out = np.zeros((H, W), bool)
    for y in range(RUN - 1, H - 2):
        band = L[y - RUN + 1:y + 1]
        ok = alpha[y - RUN + 1:y + 2].all(0)
        flat = (band.max(0) - band.min(0) <= SPREAD) & (band.min(0) >= MIN_L)
        drop = (band[-1] - L[y + 1]) > DROP
        cand = np.nonzero(ok & flat & drop)[0]
        for x in cand:
            lo, hi = band[:, x].min(), band[:, x].max()
            s0 = y - RUN + 1
            while s0 - 1 >= 0 and alpha[s0 - 1, x] and L[s0 - 1, x] >= MIN_L and max(hi, L[s0 - 1, x]) - min(lo, L[s0 - 1, x]) <= SPREAD:
                s0 -= 1
                lo, hi = min(lo, L[s0, x]), max(hi, L[s0, x])
            if y - s0 + 1 > MAXBAND:
                continue
            edge = s0 == 0 or not alpha[s0 - 1, x] or L[s0 - 1, x] < lo - 40
            # the shade side is part of the form (two texels at least before the edge), not an outline
            body = y + 2 < H and alpha[y + 2, x] and L[y + 2, x] < lo - 60
            out[y, x] = edge and body
    return out


def _runs(hit: np.ndarray, gap: int = 12):
    """Strips of hits running along x at about one row, bridging gaps of up to `gap` texels (a
    lenticel or a knot breaks the band, not the strip): (length, y, x0, x1) of the longest."""
    H, W = hit.shape
    best = (0, 0, 0, 0)
    seen = np.zeros_like(hit)
    for y, x in zip(*np.nonzero(hit)):
        if seen[y, x]:
            continue
        yy, xx, x0, last = y, x, x, x
        while xx < W and xx - last <= gap:
            cand = [yy + d for d in (0, -1, 1, -2, 2) if 0 <= yy + d < H and hit[yy + d, xx]]
            if cand:
                yy = cand[0]
                seen[yy, xx] = True
                last = xx
            xx += 1
        n = last - x0 + 1
        if n > best[0]:
            best = (n, int(y), int(x0), int(last + 1))
    return best


def measure(rgb: np.ndarray, alpha: np.ndarray):
    """(longest flat strip in texels, its box (x0, y0, x1, y1), 'along x' or 'upright')."""
    L = lum(rgb)
    n1, y1, x0, x1 = _runs(_hits(L, alpha))
    Lt, at = L.T, alpha.T
    n2, x2, y0, y3 = _runs(_hits(Lt, at))
    if n1 >= n2:
        return n1, (x0, y1 - RUN, x1, y1 + 2), 'along x'
    return n2, (x2 - RUN, y0, x2 + 2, y3), 'upright'


def check(rgb: np.ndarray, alpha: np.ndarray, H: float, subject: str) -> list[Finding]:
    """The asset gate's flat-cylinder finding on one object picture (alpha marks the object)."""
    n, box, how = measure(rgb, alpha)
    if n < LONG:
        return []
    return [Finding('detail.flat_cylinder', 'fault', box,
                    f'{subject}: a round part {how} is painted as a strip: for {n} texels a lit band of near one tone '
                    f'drops more than {DROP:.0f} L into its shadow with no mid tones between',
                    'shade it as a cylinder in five steps: a highlight row, two lit rows, the body, the turn and a dark '
                    'underside over its outline (house-style.md 3 and 5; Eastward\'s fallen trunk in shadows/g2018_002)',
                    score=float(n), threshold=float(LONG), subject=subject)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('png', nargs='+')
    a = ap.parse_args(argv)
    for p in a.png:
        im = np.asarray(Image.open(p).convert('RGBA'))
        n, box, how = measure(im[..., :3], im[..., 3] > 128)
        print('%-50s longest flat strip %3d texels %s %s' % (os.path.basename(p), n, how, box))
    return 0


if __name__ == '__main__':
    sys.exit(main())
