"""Ragged edges: organic outlines that break the soft grid.

Matt, 26 Oct 10:19, on the background of the cast-v2 Bramble video (the park bench with iron
end posts and the wooden lamp post with its green-capped lantern, a dirt path through the grass):
"the lamp and bench are exactly the style i'm going for ... if all of the paths look like this it
would be better if they adhere to the soft grid more (also for similar structures)". The path's
edges were per-pixel noise: one-texel teeth, bites and spurs. Eastward's rims step one pixel at a
time in runs of 1 to 10 (eastward-edges.md 1.4 to 1.6, 5.1).

Two measures on a region's outline (a dirt path, a worn patch, a puddle, a bed, a sprite's
silhouette), both relative to its edge length, so they hold at every density:

  - teeth: outline texels that a one-texel opening or closing (4-connected) removes or adds:
    spurs one texel wide and bites one texel deep;
  - jags: along the outline's top and bottom (and left and right) profiles, steps of 2 texels or
    more that turn straight back (a spike or a notch), the per-pixel noise Matt saw; a soft-grid
    edge steps one texel at a time and its runs only lengthen or shorten slowly.

    python3 -m scripts.review.edges <png> [--H 74]       # prints the measures per region
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from .core import Finding, regions, slice_box
from . import detail as D

CROSS = ndi.generate_binary_structure(2, 1)
TEETH_MAX = 0.06       # share of the outline that is one-texel spurs and bites (the ragged woodland path 0.125, soft-grid paths 0.01 to 0.03)
JAGS_MAX = 0.05        # share of profile steps that are spikes or notches
WATER_TEETH_MAX = 0.08  # a bank of stones and roots may be a little rougher (the woodland river 0.006 to 0.009)


def _profile_jags(m: np.ndarray) -> tuple[int, int]:
    """Spikes and notches along the four profiles of a region (the first and last mask texel of
    every column and every row): a step of 2 or more texels whose neighbour step turns back."""
    jags = steps = 0
    for arr in (m, m.T):
        cols = np.nonzero(arr.any(0))[0]
        if len(cols) < 4:
            continue
        sub = arr[:, cols]
        top = np.argmax(sub, 0).astype(int)
        bot = (sub.shape[0] - 1 - np.argmax(sub[::-1], 0)).astype(int)
        for prof in (top, bot):
            # only where the profile is continuous (consecutive columns)
            d = np.diff(prof)
            gap = np.diff(cols) > 1
            d = np.where(gap, 0, d)
            steps += int((d != 0).sum())
            big = np.abs(d) >= 2
            back = np.zeros_like(big)
            back[:-1] = (np.sign(d[:-1]) * np.sign(d[1:]) < 0) & (np.abs(d[1:]) >= 1)
            jags += int((big & back).sum())
    return jags, steps


def measure(m: np.ndarray, exclude: np.ndarray | None = None) -> dict:
    """Teeth and jags of one region's outline (teeth on `exclude`, things lying over the edge, not
    counted)."""
    m = m.astype(bool)
    edge = m & ~ndi.binary_erosion(m, structure=CROSS)
    per = max(1, int(edge.sum()))
    pad = 3
    mp = np.pad(m, pad)
    op = ndi.binary_opening(mp, structure=CROSS)
    cl = ndi.binary_closing(mp, structure=CROSS)
    tm = ((mp & ~op) | (cl & ~mp))[pad:-pad, pad:-pad]
    # not where the region meets the picture's border (things cut by the frame are not its edge)
    b = 6
    tm[:b], tm[-b:], tm[:, :b], tm[:, -b:] = False, False, False, False
    if exclude is not None:
        tm &= ~ndi.binary_dilation(exclude, iterations=1)
    teeth = int(tm.sum())
    jags, steps = _profile_jags(m)
    return dict(perimeter=per, teeth=teeth / per, jags=jags / max(1, steps), steps=steps)


def ragged(mask: np.ndarray, H: float, subject: str, min_area: float = 0.3, box0=(0, 0), teeth_max: float = TEETH_MAX,
           sprite: bool = False, exclude: np.ndarray | None = None) -> list[Finding]:
    """A finding per region of `mask` (at least min_area H^2) whose outline is ragged."""
    out = []
    ox, oy = box0
    lab, regs = regions(mask, min_area=int(min_area * H * H))
    for lid, sl, a in regs:
        comp = lab == lid
        r = measure(comp, exclude)
        if r['perimeter'] < 0.6 * H:
            continue
        # a sprite's thin parts (legs, rails, posts) are one or two texels wide by design: its
        # silhouette is judged by its jags only
        if (not sprite and r['teeth'] > teeth_max) or r['jags'] > JAGS_MAX:
            x0, y0, x1, y1 = slice_box(sl)
            out.append(Finding('detail.ragged_edge', 'fault', (x0 + ox, y0 + oy, x1 + ox, y1 + oy),
                               f'{subject}: a ragged edge: {r["teeth"]:.0%} of its outline is one-texel spurs and bites, '
                               f'{r["jags"]:.0%} of its steps are spikes or notches (soft grid: at most '
                               f'{TEETH_MAX:.0%} and {JAGS_MAX:.0%})',
                               'draw the edge on the soft grid (eastward-edges.md 1.4 to 1.6, 5.1): smooth runs that step one '
                               'texel at a time and lengthen or shorten slowly round a curve, a darker rim on the shadow side '
                               'and a lit lip on the other, bites and tufts only as rounded shapes a few texels across',
                               score=max(r['teeth'], r['jags']), threshold=TEETH_MAX, subject=subject, extra=r))
    return out


# ------------------------------------------------------------------------------------------------
# corner radius (Matt, 26 Oct 15:36: "edges and paths are a bit block like but they are not sharp
# like minecraft"): a blocky plan's corners are rounded, outer ones by about 0.4 of a cell, inner
# ones by about 0.25 (eastward-edges.md 1.5, 1.6)
# ------------------------------------------------------------------------------------------------
CORNER_TURN = 1.05      # a corner turns at least 60 degrees within one cell of outline
CORNER_R_MIN = 0.2      # in cells: rounder than this, or it reads as a sharp (minecraft) corner
CORNER_SHARP_MAX = 0.25  # share of a region's corners that may be sharp
_MOORE = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def trace(m: np.ndarray) -> np.ndarray:
    """The outer outline of a region (one connected component) as an ordered list of (y, x)
    texels, by Moore-neighbour tracing."""
    ys, xs = np.nonzero(m)
    if not len(ys):
        return np.zeros((0, 2))
    k = np.lexsort((xs, ys))[0]
    start = (int(ys[k]), int(xs[k]))
    H, W = m.shape
    pts = [start]
    cur, back = start, 6                     # we arrived from the west
    for _ in range(8 * m.sum() + 8):
        found = False
        for j in range(8):
            d = (back + 1 + j) % 8
            ny, nx = cur[0] + _MOORE[d][0], cur[1] + _MOORE[d][1]
            if 0 <= ny < H and 0 <= nx < W and m[ny, nx]:
                back = (d + 4) % 8
                cur = (ny, nx)
                found = True
                break
        if not found or (cur == start and len(pts) > 2):
            break
        pts.append(cur)
    return np.array(pts, float)


def corners(m: np.ndarray, cell: float) -> list:
    """The corners of a region's outline: (y, x, turn in radians, radius in px). A corner is a
    place where the outline turns at least CORNER_TURN within one cell; its radius is the arc over
    which the middle 80 % of the turn happens, divided by that turn (a pixel staircase or a lump
    turns back within the cell and is not a corner)."""
    from scipy.ndimage import gaussian_filter1d
    P = trace(m)
    if len(P) < 4 * cell:
        return []
    P = np.stack([gaussian_filter1d(P[:, 0], 1.0, mode='wrap'), gaussian_filter1d(P[:, 1], 1.0, mode='wrap')], 1)
    seg = np.hypot(*np.diff(np.vstack([P, P[:1]]), axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    n = int(L)
    if n < 8:
        return []
    u = np.linspace(0, L, n, endpoint=False)
    Pc = np.vstack([P, P[:1]])
    Q = np.stack([np.interp(u, s, Pc[:, 0]), np.interp(u, s, Pc[:, 1])], 1)
    d = np.roll(Q, -1, 0) - Q
    th = np.unwrap(np.arctan2(d[:, 0], d[:, 1]))
    dth = np.angle(np.exp(1j * np.diff(np.concatenate([th, [th[0]]]))))
    w = max(3, int(round(cell / 2)))
    cum = np.concatenate([[0], np.cumsum(np.concatenate([dth, dth, dth]))])
    T = np.array([cum[n + i + w] - cum[n + i - w] for i in range(n)])
    out = []
    taken = np.zeros(n, bool)
    for i in np.argsort(-np.abs(T)):
        if abs(T[i]) < CORNER_TURN:
            break
        if taken[max(0, i - w):i + w].any() or taken[(np.arange(i - w, i + w)) % n].any():
            continue
        taken[(np.arange(i - w, i + w)) % n] = True
        c = cum[n + i - w:n + i + w + 1] - cum[n + i - w]
        tot = c[-1]
        f = c / tot if tot != 0 else c
        a = np.argmax(f >= 0.1)
        b = np.argmax(f >= 0.9)
        r = max(0.5, (b - a)) / (0.8 * abs(tot))
        # a plan's corner joins two straight arms (a run either side, each within 20 degrees of
        # its own direction); an organic bend or a lump does not
        ia = (np.arange(i - w, i - w // 3)) % n
        ib = (np.arange(i + w // 3, i + w)) % n
        tha = np.unwrap(th[ia])
        thb = np.unwrap(th[ib])
        straight = (np.ptp(tha) < 0.35) and (np.ptp(thb) < 0.35)
        out.append((Q[i, 0], Q[i, 1], float(tot), float(r), bool(straight)))
    return out


def corner_radius(mask: np.ndarray, H: float, subject: str, min_area: float = 0.5, box0=(0, 0)) -> list[Finding]:
    """A finding per region whose corners are mostly sharp: a blocky plan drawn as hard squares."""
    cell = 8.0 * H / 25.0                      # 8 world px at an adult of 25
    out = []
    ox, oy = box0
    lab, regs = regions(mask, min_area=int(min_area * H * H))
    for lid, sl, a in regs:
        comp = lab == lid
        Hm, Wm = comp.shape
        b = 6                                    # not where the frame cuts the region
        cs = [c for c in corners(comp, cell) if b <= c[0] < Hm - b and b <= c[1] < Wm - b
              and c[4] and 1.2 <= abs(c[2]) <= 1.95]           # plan corners: right angles between straight runs
        if len(cs) < 3:
            continue
        sharp = [c for c in cs if c[3] < CORNER_R_MIN * cell]
        share = len(sharp) / len(cs)
        if len(sharp) >= 3 and share > CORNER_SHARP_MAX:
            x0, y0, x1, y1 = slice_box(sl)
            out.append(Finding('detail.corner_radius', 'fault', (x0 + ox, y0 + oy, x1 + ox, y1 + oy),
                               f'{subject}: {len(sharp)} of {len(cs)} corners are sharp (radius under '
                               f'{CORNER_R_MIN:.1f} of a cell): blocky like minecraft, not the soft grid',
                               'round the plan\'s corners (Matt, 26 Oct: "a bit block like but ... not sharp like '
                               'minecraft"): outer corners about 0.4 of a cell, inner fillets about 0.25, runs with '
                               'lumps 8 to 20 px long and 1 to 3 px deep (softgrid.py, eastward-edges.md 1.5, 1.6)',
                               score=share, threshold=CORNER_SHARP_MAX, subject=subject,
                               extra=dict(corners=len(cs), sharp=len(sharp), radii=[round(c[3], 1) for c in cs][:20])))
    return out


# sprites that are laid-out ground (their silhouette is an organic edge): props and buildings keep
# their own drawn outlines (a damage overlay's boards and holes are not an organic edge)
ORGANIC_SPRITES = ('beds', 'bed_', 'pond', 'puddle', 'patch', 'plot', 'field')
GROUND_FAMS = (3, 2)        # brown (dirt, paths, worn earth), blue (puddles, ponds); not straw: olive shade on warm grass reads as straw


def ground_masks(rgb: np.ndarray, ignore: np.ndarray | None = None):
    """The organic ground regions of a picture: dirt (the brown family) and water, each closed over
    its own texture so the mask is the region, not its speckle. Stones and their dark outlines
    lying on the edge belong to the region (things over an edge, eastward-edges.md 8)."""
    fam = D.family_map(rgb)
    over = np.isin(fam, (0, 5, 6, 4, 8))
    for fams, name in (((3,), 'dirt'), ((2,), 'water')):
        m = np.isin(fam, fams)
        if ignore is not None:
            m &= ~ignore
        m |= over & ndi.binary_dilation(m, iterations=3)
        # the region's own texture (pebbles, ripples, darker patches) is inside it, not an edge
        m = ndi.binary_fill_holes(ndi.binary_closing(m, structure=np.ones((3, 3)), iterations=2))
        yield name, m, over
    # the water with its bank (#288 review B2): the turf-to-bank outline is where a bank's teeth
    # are; measured on everything that is not turf within a few texels of the water
    water = np.isin(fam, (2,))
    if ignore is not None:
        water &= ~ignore
    if water.any():
        near = ndi.binary_dilation(water, iterations=6)
        m = water | (near & np.isin(fam, (0, 3, 4, 5, 6, 9)))      # dark earth reads red
        m = ndi.binary_fill_holes(m)            # (no closing: it would fill the very teeth measured)
        yield 'bank', m, over & ~near


def ragged_ground(rgb: np.ndarray, H: float, subject: str, ignore=None) -> list[Finding]:
    out = []
    for name, m, over in ground_masks(rgb, ignore):
        out += ragged(m, H, f'{subject} ({name})', min_area=0.5,
                      teeth_max=WATER_TEETH_MAX if name in ('water', 'bank') else TEETH_MAX, exclude=over)
        if name in ('dirt', 'water'):
            out += corner_radius(m, H, f'{subject} ({name})')
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('png')
    ap.add_argument('--H', type=float, default=74.0)
    ap.add_argument('--sprite', action='store_true', help='measure the alpha silhouette')
    a = ap.parse_args(argv)
    im = np.asarray(Image.open(a.png).convert('RGBA'))
    if a.sprite:
        r = measure(im[..., 3] > 128)
        print(f'silhouette: teeth {r["teeth"]:.3f} jags {r["jags"]:.3f} ({r["steps"]} steps)')
        return 0
    for name, m, over in ground_masks(im[..., :3]):
        lab, regs = regions(m, min_area=int(0.5 * a.H * a.H))
        for lid, sl, ar in regs:
            r = measure(lab == lid, over)
            print(f'{name} {slice_box(sl)} area {ar}: teeth {r["teeth"]:.3f} jags {r["jags"]:.3f} ({r["steps"]} steps)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
