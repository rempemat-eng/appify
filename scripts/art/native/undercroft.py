"""The undercroft kit: an old stone vault under the valley, drawn natively at any density in palette
codes only (the Undercroft, docs/vision/vertical-slice.md beat 6; game/data/plans/undercroft.json).

The house rules indoors: light still falls from the upper left on every block, plinth and lip, so
forms read; on top of that the torches throw warm pools and the skylight shaft a cool one, and the
corners far from both sink a step. Walls are blocks on the 8 px soft grid (eastward-edges.md 1 and
2): a top (the soil and coping over the vault, a lit lip where it breaks to the face) and a south
face 40 world px tall (a cliff-height face, 2.1: at least 1.3 people) built as a blind arcade:
cornice, voussoired arches over shaded recesses, pilasters with imposts, a plinth with a dark
foot. The oak's roots split some bays (cracks, a displaced block, rootlets) and run on over the
floor. The floor (round 4, after Eastward's dungeon in shot 06) is the calmest, darkest lit surface:
irregular flags on a 4 px sub-grid with warped joints, worn corners, dirt and moss in the joints,
pits and sparse cracks, no bevels, painted last from the light on one short value ladder
(FLOOR_LADDER: violet shade, warm pools that fall off softly, flag by flag into the dark corners).
The walls, coping and props carry the contrast and the 3D read.

    python3 -m scripts.art.native.undercroft --plan game/data/plans/undercroft.json --density 3 \\
        --out game/zones/undercroft/art --preview DIR

writes <out>/ground.png, one picture per object (props, the torch sheet, the seal, the plate and
lever in both states, Cairn's alcove, the channel lit) and <out>/../kit.json with every object's
foot, offset, condition, collision box and kind; game/tools/gen_undercroft.py writes the scene.
Units: plan positions are world px; pictures and kit.json are texels (world px x density).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import ctx  # noqa: E402

INPUTS = ('undercroft.py', 'village.py', 'palette.py', 'ctx.py')
STONES = ('stone', 'stone_warm', 'stone_cool')
CAIRN = os.path.join(ROOT, 'game', 'assets', 'characters', 'cairn', 'sheets', 'defeat_S.png')
TORCH_FRAMES = 4
TORCH_LIFT = 14          # world px from the face's foot to the torch's cup: low on the face, in view over its pool


def input_hash(plan_path: str, density: float) -> str:
    h = hashlib.sha256(('density %g\n' % density).encode())
    files = [os.path.join(HERE, f) for f in INPUTS] + [plan_path, CAIRN, os.path.join(ROOT, 'art', 'house-palette.json')]
    for f in files:
        h.update(os.path.relpath(f, ROOT).encode() + b'\0')
        h.update(open(f, 'rb').read())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------
# painters (need ctx configured: they read the density through village.q)
# ------------------------------------------------------------------------------------------------
def _v():
    from scripts.art.native import village as V
    return V


def line_mask(shape, pts, r=0.6):
    V = _v()
    m = np.zeros(shape, bool)
    for (a, b), (c, d) in zip(pts, pts[1:]):
        m |= V.seg_mask(shape, a, b, c, d, r)
    return m


def swap_fam(codes, table):
    """Moves codes between ramps by a table, tone kept: a pool of warm light turns grey stone warm and
    warm stone grey, so the veins inside a flag stay distinct under the light."""
    from .palette import FI as _FI
    out = codes.copy()
    for a, b in table.items():
        out[codes // 8 == _FI[a]] = _FI[b] * 8 + codes[codes // 8 == _FI[a]] % 8
    return out


def wear(cv, m, fam, t, rng):
    """A flag's face, cushioned like worn stone and lit from the upper left: the corner towards the
    light a tone up, the middle at the stone's tone, the side away from it (and a narrow band along the
    lower and east edges) a tone down, the three in about equal parts; one broad vein of the sibling
    ramp crosses the middle; a few pits and scuffs. Calm (three large tone fields, no speckle) and
    solid (three planes, as Eastward's floors read)."""
    from .palette import FI as _FI
    ys, xs = np.nonzero(m)
    if len(ys) < 30:
        return
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = m[y0:y1, x0:x1]
    blk = cv[y0:y1, x0:x1]
    Y, X = np.mgrid[0:y1 - y0, 0:x1 - x0]
    inner = ndi.binary_erosion(sub, iterations=1)
    tilt = rng.uniform(-0.12, 0.12)
    diag = X / max(1, x1 - x0) * (1 + tilt) + Y / max(1, y1 - y0) * (1 - tilt)
    lit = inner & (diag < 0.78)
    dark = inner & ((diag > 1.18) | (Y > (y1 - y0) - 4) | (X > (x1 - x0) - 3))
    mid = inner & ~lit & ~dark
    blk[lit] = _FI[fam] * 8 + min(5, t + 1)
    blk[mid] = _FI[fam] * 8 + t
    blk[dark] = _FI[fam] * 8 + max(0, t - 1)
    cy, cx = rng.uniform(0.35, 0.65) * (y1 - y0), rng.uniform(0.3, 0.7) * (x1 - x0)
    ry, rx = (y1 - y0) * rng.uniform(0.16, 0.24), (x1 - x0) * rng.uniform(0.22, 0.32)
    ry, rx = ry * 1.25, rx * 1.3
    vein = (mid | lit) & (((Y - cy) / ry) ** 2 + ((X - cx) / rx) ** 2 + 0.25 * np.sin(X * 0.7 + Y * 0.4) < 1)
    # a paler, greyer vein of the stone (the ash ramp, a step up to sit at the same value) across the face
    blk[vein & mid] = _FI['ash'] * 8 + min(5, t + 1)
    blk[vein & lit] = _FI['ashlar'] * 8 + t
    # the worn arris: the flag's top and west edges catch the light a further tone up (a bevel, as the
    # rounded edge of Eastward's flags), broken where the stone has chipped
    up = np.zeros_like(sub)
    up[2:, :] = sub[:-2, :]
    left = np.zeros_like(sub)
    left[:, 2:] = sub[:, :-2]
    arris = inner & (~up | ~left) & ~dark & (rng.random(sub.shape) > 0.12)
    blk[arris] = _FI['ashlar'] * 8 + min(5, t + 1)     # the paler stone of the arris, a value of its own in the dark
    weather(blk, inner, rng, 0.6, moss=False, lichen=False)


def break_runs(cv, mask, rng, longest=48):
    """No ruler lines: a run of one colour longer than `longest` texels along a row or a column is
    broken every so often by a short piece on its sibling ramp or a tone off, as a lip or a joint is
    never one unbroken stroke in stone."""
    from .palette import sib
    H, W = cv.shape
    for axis in (0, 1):
        a = cv if axis == 0 else cv.T
        m = mask if axis == 0 else mask.T
        for r in range(a.shape[0]):
            row, mr = a[r], m[r]
            x = 0
            n = row.shape[0]
            while x < n:
                c = row[x]
                e = x
                while e < n and row[e] == c and mr[e]:
                    e += 1
                if e - x > longest and c >= 0:
                    k = x + int(rng.integers(12, 30))
                    while k < e - 6:
                        L = int(rng.integers(5, 10))
                        seg = row[k:k + L]
                        alt = sib(np.array([c]), 'warm' if rng.random() < 0.5 else 'cool')[0]
                        if alt == c:
                            t = c % 8
                            alt = c - 1 if 0 < t < 6 else (c + 1 if t < 5 else c)
                        if c % 8 >= 6:      # an edge line (siblings share its colour): broken by the ramp's tone 1, a lit nick
                            alt = c // 8 * 8 + 1
                        seg[:] = alt
                        k += L + int(rng.integers(16, 34))
                x = max(e, x + 1)


# The floor's value ladder (round 4, matched to Eastward's dungeon, shot 06, at the same character
# height): the floor is the darkest lit surface on screen, a narrow run of values, and only the light
# pools climb it. Each rung is a (family, tone) pair with a sibling a few L units away for the flags'
# quiet variety; a joint, crack or chip sits one rung under its flag, never more.
#   rung  L    body               variant
#   0     38   soot 1             void 2            the walls' feet, the far corners
#   1     52   slate_cool 1       soot 2            the floor in shade (Eastward's 06: 52 to 57)
#   2     68   void 4             stone_cool 1      the floor at a pool's spill
# (a mark under rung 0 is void 1, so joints still show in the darkest corners; the shade rungs are
# violet and blue, the lit rungs warm grey: cool shade, warm light)
#   3     84   stone_warm 1       ash 2             a pool's rim
#   4     108  stone 2            stone_warm 2      a pool
#   5     140  stone 3            stone_warm 3      a pool's heart under the flame
#   6     166  stone_warm 4       stone 4           (lit arrises only)
FLOOR_LADDER = [(('void', 2), ('void', 2)), (('slate_cool', 1), ('slate', 1)), (('stone_cool', 1), ('stone', 1)),
                (('stone_warm', 1), ('ash', 2)), (('stone', 2), ('stone_warm', 2)), (('stone', 3), ('stone_warm', 3)),
                (('stone_warm', 4), ('stone', 4))]
# under the skylight the same rungs on the cool ramps (daylight from above is blue against the torches)
FLOOR_LADDER_COOL = {1: (('slate_cool', 1), ('slate_cool', 1)), 2: (('slate_cool', 1), ('slate', 1)), 3: (('slate', 2), ('slate_cool', 2)), 4: (('slate', 3), ('slate_cool', 3)),
                     5: (('slate', 4), ('slate_cool', 4)), 6: (('slate', 5), ('slate_cool', 5))}
# under a torch the pool's rungs lean warm (pitch-light on stone: the warm grey and the sand ramp)
# round 3 (8 Nov, G-1r): the warmth back in the torches' pools, amber over the grey: the earth and path ramps
# round 4 (8 Nov, G-14): a torch lights the floor's own stone on its warm siblings, never another material:
# stone_warm 1 for the spill, stone_warm 2 to 3 and ashlar 3 to 4 in the heart (house-style 1)
FLOOR_LADDER_WARM = {1: (('slate_cool', 1), ('slate', 1)), 2: (('stone_warm', 1), ('stone_warm', 1)),
                     3: (('stone_warm', 2), ('ashlar', 2)), 4: (('stone_warm', 3), ('ashlar', 3)),
                     5: (('ashlar', 4), ('stone_warm', 4)), 6: (('ashlar', 4), ('stone_warm', 4))}
FLOOR_AMBIENT = 1                # far from every light the floor sits on rung 1, in shade, as Eastward's
# round 5 (8 Nov, G-1): a pool climbs at most three rungs over the ambient, flag by flag (whole flags, or a
# flag split once by a straight line into halves a rung apart), never in ragged contour bands
POOL_STEPS = 3
POOL_HEART, POOL_SPILL = 3.0, 1.0


def flag_rungs(level, slab, nflags, rng, split=None, lo=0, hi=FLOOR_AMBIENT + POOL_STEPS):
    """The floor's light stepped by its flags: each flag takes one rung from the mean light over it (give
    or take a little, so the odd stone sits a rung off); where `split` holds (in a pool) and the light
    crosses a rung boundary well inside a flag, the flag is cut once by a straight line across the
    light's gradient into two halves a rung apart. Returns rungs per texel (0 off the flags)."""
    H, W = slab.shape
    idx = np.arange(1, nflags + 1)
    Y, X = np.mgrid[0:H, 0:W].astype(float)
    on = slab > 0
    with np.errstate(invalid='ignore', divide='ignore'):
        cnt = np.maximum(ndi.sum(on, labels=slab, index=idx), 1)
        mx = ndi.sum(X, labels=slab, index=idx) / cnt
        my = ndi.sum(Y, labels=slab, index=idx) / cnt
        ml = np.nan_to_num(ndi.sum(level, labels=slab, index=idx) / cnt, nan=float(FLOOR_AMBIENT))
        vx = ndi.sum(X * X, labels=slab, index=idx) / cnt - mx * mx
        vy = ndi.sum(Y * Y, labels=slab, index=idx) / cnt - my * my
        gx = (ndi.sum(X * level, labels=slab, index=idx) / cnt - mx * ml) / (vx + 1e-6)
        gy = (ndi.sum(Y * level, labels=slab, index=idx) / cnt - my * ml) / (vy + 1e-6)
    jit = rng.uniform(-0.15, 0.15, nflags)
    r0 = np.clip(np.floor(ml + jit + 0.5).astype(int), lo, hi)
    pad = lambda v: np.concatenate([[0], v])
    R0, MX, MY, ML, GX, GY = (pad(v) for v in (r0, mx, my, ml, gx, gy))
    out = np.zeros((H, W), int)
    out[on] = R0[slab[on]]
    if split is None:
        return out
    plane = np.zeros((H, W))
    f = slab[on]
    # the cut runs straight across the flag, east-west or north-south (whichever crosses the light's
    # gradient best), so a flag splits into two halves like a cracked stone, never a wedge
    horiz = np.abs(GY[f]) >= np.abs(GX[f])
    plane[on] = ML[f] + np.where(horiz, GY[f] * (Y[on] - MY[f]), GX[f] * (X[on] - MX[f]))
    up = on & (plane > out + 0.5)
    dn = on & (plane < out - 0.5)
    with np.errstate(invalid='ignore', divide='ignore'):
        fu = pad(ndi.sum(up, labels=slab, index=idx) / cnt)
        fd = pad(ndi.sum(dn, labels=slab, index=idx) / cnt)
    ok = on & split
    half_u = ok & up & (fu[slab] >= 0.25) & (fu[slab] <= 0.75) & (fu[slab] >= fd[slab])
    half_d = ok & dn & (fd[slab] >= 0.25) & (fd[slab] <= 0.75) & (fd[slab] > fu[slab])
    out[half_u] += 1
    out[half_d] -= 1
    return np.clip(out, lo, hi) * on


def flag_texture(cv, mask, rng, share=0.35):
    """A flag's face (8 Nov round 3, G-10): clusters of two to four texels on its two sibling ramps at
    the same tone and, now and then, a tone down (a worn hollow), gathered in drifts: many small shapes
    and tones in a patch, but no contrast between the flags."""
    from .palette import FAMS as FAMS_, parent, FI, LUT

    def _L(code_):
        r_, g_, b_ = (int(v) for v in LUT[code_])
        return 0.299 * r_ + 0.587 * g_ + 0.114 * b_
    H, W = cv.shape
    ok = mask & (cv >= 0) & (cv % 8 <= 5)
    ys, xs = np.nonzero(ok)
    if not len(ys):
        return
    dn = ndi.gaussian_filter(rng.random((H, W)), 3.0)
    dn = (dn - dn[ok].mean()) / (dn[ok].std() + 1e-9)
    for _ in range(int(len(ys) * share / 2.8)):
        k = int(rng.integers(0, len(ys)))
        y, x = int(ys[k]), int(xs[k])
        if dn[y, x] < rng.normal(-1.2, 0.8):                   # a light drift: every flag gets its share
            continue
        c = int(cv[y, x])
        pts = [(y + dy, x + dx) for dy, dx in _CLUSTERS[int(rng.integers(0, len(_CLUSTERS)))]
               if 0 <= y + dy < H and 0 <= x + dx < W and ok[y + dy, x + dx] and cv[y + dy, x + dx] == c]
        if len(pts) < 2:
            continue
        fn = FAMS_[c // 8]
        r = rng.random()
        shade_f = fn in ('soot', 'void')                         # in the shade only a rare hollow (logic.scale)
        if shade_f:                                               # round 4 (G-16): no tone-down grit anywhere
            continue
        else:
            par = parent(fn)
            other = [n for n in (par + '_warm', par + '_cool') if n in FI and n != fn]
            if fn != par:                                         # mostly its body ramp, now and then the other sibling
                opts = [par] if (rng.random() < 0.65 or not other) else other
            else:
                opts = other
            opts = [n for n in opts if n in FI and n != fn and abs(_L(FI[n] * 8 + c % 8) - _L(c)) <= 8]
            if not opts:                                          # only siblings close in value: no dark specks
                continue
            nc = FI[opts[int(rng.integers(0, len(opts)))]] * 8 + c % 8
        for p_ in pts:
            cv[p_] = nc


def flag_tint(slab, nflags, lf_cool, lf_torch, lf_warm):
    """Per flag: is it under the skylight's cool light, under a torch's warm light, or neither? Each flag
    takes one answer from the means of the light fields over it (8 Nov, G-7)."""
    idx = np.arange(1, nflags + 1)
    on = slab > 0
    with np.errstate(invalid='ignore'):
        mc = np.nan_to_num(ndi.mean(lf_cool, labels=slab, index=idx))
        mt = np.nan_to_num(ndi.mean(lf_torch, labels=slab, index=idx))
        mw = np.nan_to_num(ndi.mean(lf_warm, labels=slab, index=idx))
    cool_f = np.concatenate([[False], (mc > mt) & (mc > 0.5)])
    warm_f = np.concatenate([[False], (mw >= mc) & (mw > 0.9)])
    return cool_f[slab] & on, warm_f[slab] & on


def pool_rungs(level, slab, nflags, inpool, lo=0, hi=FLOOR_AMBIENT + POOL_STEPS):
    """The floor's rungs from its light (8 Nov round 3, G-1r): in the shade one rung a flag, from the mean
    light over it, with no jitter (calm); in a pool a smooth falloff texel by texel in palette ramp steps,
    whose edges follow the light's own curve (a joint only where one happens to lie on it), softened by a
    narrow 2 x 2 checker band one rung apart on each inner step (style.dither_dark, eastward-edges 5.4) (the light fade eastward-edges 5.4 allows on
    ground). Never more than POOL_STEPS rungs over the ambient."""
    H, W = level.shape
    idx = np.arange(1, max(1, nflags) + 1)
    with np.errstate(invalid='ignore'):
        ml = np.nan_to_num(ndi.mean(level, labels=slab, index=idx), nan=float(FLOOR_AMBIENT))
    per_flag = np.concatenate([[FLOOR_AMBIENT], np.clip(np.floor(ml + 0.5).astype(int), lo, hi)])
    sm = ndi.gaussian_filter(level, 2.0)
    r = np.floor(sm + 0.5)
    frac = sm + 0.5 - r                                   # 0 just over a step, 1 just under the next
    Y, X = np.mgrid[0:H, 0:W]
    chk = ((X // 2 + Y // 2) % 2) == 0                    # round 4 (G-14): a 2 x 2 checker band, not torn blocks
    chk_lo = chk & (frac < 0.12)
    chk_hi = chk & (frac > 0.88)
    # fade only the pool's inner steps; its rim against the shade stays one clean curve
    r = r - chk_lo + chk_hi
    r = np.clip(r.astype(int), lo, hi)
    # round 4 (G-15): the shade falls off on the light's own curves too, so no flag-sized skyline forms
    # where the floor sinks into the dark; a flag stays whole wherever the light is level over it
    return r


def flag_lips(slab, rng, gap=0.16):
    """Each flag's lips: its north and west edge texels (lit, broken here and there where the arris is
    worn) and its south and east edge texels (in shade), as masks."""
    on = slab > 0
    up = np.roll(slab, 1, 0) != slab
    lf = np.roll(slab, 1, 1) != slab
    dn = np.roll(slab, -1, 0) != slab
    rt = np.roll(slab, -1, 1) != slab
    H, W = slab.shape
    gaps = np.kron(rng.random(((H + 3) // 4, (W + 3) // 4)) < gap, np.ones((4, 4), bool))[:H, :W]
    nw = on & (up | lf) & ~gaps
    se = on & (dn | rt) & ~(up | lf)
    return nw, se


def floor_layout(shape, where, rng, cell):
    """Irregular flags on a `cell` texel sub-grid (squares and oblongs of two to four cells), their
    joints warped by a slow noise so no joint runs ruler-straight, their corners worn round. Returns
    (ids, joint, off, mat): each texel's flag id (0 on joints), the joint mask, a rung offset (-1 for
    joints, chips, pits and cracks) and a material map (0 stone, 1 dirt in the joint, 2 moss)."""
    H, W = shape
    ny, nx = (H + cell - 1) // cell, (W + cell - 1) // cell
    grid = np.zeros((ny, nx), np.int32)
    opts = [(3, 3)] * 3 + [(3, 2)] * 3 + [(2, 3)] * 2 + [(4, 3), (3, 4), (2, 2), (4, 2), (2, 4)]
    sid = 0
    for j in range(ny):
        for i in range(nx):
            if grid[j, i]:
                continue
            cw, chh = opts[int(rng.integers(0, len(opts)))]
            while cw > 1 and (i + cw > nx or grid[j, i:i + cw].any()):
                cw -= 1
            while chh > 1 and (j + chh > ny or grid[j:j + chh, i:i + cw].any()):
                chh -= 1
            sid += 1
            grid[j:j + chh, i:i + cw] = sid
    Y, X = np.mgrid[0:H, 0:W]
    amp = cell * 0.13
    wx = ndi.gaussian_filter(rng.random((H, W)), cell * 1.4)
    wy = ndi.gaussian_filter(rng.random((H, W)), cell * 1.4)
    wx = (wx - wx.mean()) / (wx.std() + 1e-9) * amp
    wy = (wy - wy.mean()) / (wy.std() + 1e-9) * amp
    gy = np.clip(((Y + wy) // cell).astype(int), 0, ny - 1)
    gx = np.clip(((X + wx) // cell).astype(int), 0, nx - 1)
    ids = grid[gy, gx]
    ids[~where] = 0
    joint = np.zeros(shape, bool)
    joint[:-1, :] |= ids[:-1, :] != ids[1:, :]
    joint[:, :-1] |= ids[:, :-1] != ids[:, 1:]
    joint &= where
    # worn corners: where three flags meet, the arrises are rounded off and the gap opens
    P = np.pad(ids, 1, mode='edge')
    nb = np.stack([P[:-2, :-2], P[:-2, 2:], P[2:, :-2], P[2:, 2:], P[1:-1, 1:-1]])
    srt = np.sort(nb, axis=0)
    kinds = 1 + (np.diff(srt, axis=0) != 0).sum(0)
    meet = (kinds >= 3) & where
    lab_m, nm = ndi.label(meet)
    keep = np.concatenate([[False], rng.random(nm) < 0.12])          # only a few corners are worn open (G-9)
    meet = ndi.binary_dilation(keep[lab_m], iterations=1) & where
    joint |= meet
    off = np.zeros(shape, np.int32)
    off[joint] = -1
    mat = np.zeros(shape, np.int8)
    # dirt packed in the joints: soft runs of earth along them, most where the noise says so
    dn = ndi.gaussian_filter(rng.random(shape), cell * 0.9)
    dn = (dn - dn.mean()) / (dn.std() + 1e-9)
    dirt = joint & (dn > 0.55) & ~meet
    mat[dirt] = 1
    # inside the flags: chipped arrises, a few pits, sparse cracks (the only marks; no bevels, no stripes)
    n = int(ids.max())
    for _ in range(int(n * 0.5)):                                  # chips: corners knocked off at the joints
        ys, xs = np.nonzero(joint)
        if not len(ys):
            break
        k = int(rng.integers(0, len(ys)))
        y, x = int(ys[k]), int(xs[k])
        h_, w_ = (2, int(rng.integers(2, 5))) if rng.random() < 0.5 else (int(rng.integers(2, 5)), 2)
        sel = np.zeros(shape, bool)
        sel[max(0, y - 1):y - 1 + h_, max(0, x - 1):x - 1 + w_] = True
        off[sel & where] = -1
    for f in range(1, n + 1):
        if rng.random() > 0.08:
            continue
        ys, xs = np.nonzero(ids == f)
        if len(ys) < 120:
            continue
        cx = int(rng.integers(xs.min() + 3, max(xs.min() + 4, xs.max() - 3)))
        pts = [(cx, ys.min() + 1)]
        while pts[-1][1] < ys.max() - 2:
            pts.append((pts[-1][0] + int(rng.integers(-3, 4)), pts[-1][1] + int(rng.integers(3, 6))))
        lm = line_mask(shape, pts, 0.55) & (ids == f)
        off[lm] = -1
    return ids, joint, off, mat


def floor_codes(level, off, mat, var, cool, warm=None):
    """The floor's codes from its light (a rung per texel), its marks (offsets) and materials."""
    from .palette import FI as _FI
    raw = level + off
    lv = np.clip(raw, 0, len(FLOOR_LADDER) - 1)
    out = np.zeros(lv.shape, np.int32)
    for r, pair in enumerate(FLOOR_LADDER):
        for v in (0, 1):
            fam, t = pair[v]
            m = (lv == r) & (var == v)
            out[m] = _FI[fam] * 8 + t
            if r in FLOOR_LADDER_COOL:
                cf, ct = FLOOR_LADDER_COOL[r][v]
                out[m & cool] = _FI[cf] * 8 + ct
            if warm is not None and r in FLOOR_LADDER_WARM:
                wf, wt = FLOOR_LADDER_WARM[r][v]
                out[m & warm & ~cool] = _FI[wf] * 8 + wt
    dirt = mat == 1                                   # earth packed in a joint, a rung under the stone
    out[dirt] = _FI['soot'] * 8 + np.clip(lv[dirt], 1, 3)                 # grime in the joint (G-9), not red wire
    drift = mat == 3                                  # grey grit drifted over the flags, a step under them
    out[drift] = _FI['ash'] * 8 + np.clip(lv[drift] - 1 + (lv[drift] >= 4), 1, 4)   # in a pool the grit is lit too
    if warm is not None:                              # in a torch's pool the grit is warm earth
        dw = drift & warm & ~cool
        out[dw] = _FI['earth'] * 8 + np.clip(lv[dw], 1, 3)
    dc = drift & cool                                 # under the skylight the grit takes the cool light too
    out[dc] = _FI['slate_cool'] * 8 + np.clip(lv[dc] - 1, 1, 4)
    moss = mat == 2
    out[moss] = _FI['leaf_cool'] * 8 + np.clip(lv[moss] - 1, 0, 3)
    out[(raw < 0) & ~moss] = _FI['void'] * 8 + 1
    return out


def mottle(cv, mask, rng, sigma=2.4, sib_share=0.12):
    """Stone grain inside the pieces of a surface: soft clusters a tone lighter or darker and patches
    on a sibling ramp (warm or cool), never smaller than two texels, so a slab or block reads as worn
    stone and not as a flat fill (art-style.md: Eastward's detail per patch)."""
    from .palette import sib
    H, W = cv.shape
    n1 = ndi.gaussian_filter(rng.random((H, W)), sigma)
    n1 = (n1 - n1.mean()) / (n1.std() + 1e-9)
    n2 = ndi.gaussian_filter(rng.random((H, W)), sigma * 2.2)
    n2 = (n2 - n2.mean()) / (n2.std() + 1e-9)
    t = cv % 8
    ok = mask & (cv >= 0) & (t >= 1) & (t <= 4)
    dn = ok & (n1 < -1.45)
    up = ok & (n1 > 1.6) & (t <= 3)
    cv[dn] = cv[dn] - 1
    cv[up] = cv[up] + 1
    thr = np.quantile(n2[ok], 1 - sib_share) if ok.any() else 9
    sw = ok & (n2 > thr)
    cv[sw] = sib(cv[sw], 'warm' if rng.random() < 0.5 else 'cool')
    sw2 = ok & (n2 < -thr)
    cv[sw2] = sib(cv[sw2], 'cool')


def weather(a, mask, rng, amount=1.0, moss=True, lichen=True):
    """Age on dressed stone (or any hard surface): pits and chips (two-texel clusters a tone down
    with a lit lip), short cracks, lichen spots, moss in the low corners, a few pale scuffs; drawn in
    clusters, never single texels, so the detail reads at the cast's scale."""
    V = _v()
    code = V.code
    ys, xs = np.nonzero(mask)
    if len(ys) < 40:
        return
    n = max(3, int(len(ys) / 70 * amount))
    for _ in range(n):
        k = int(rng.integers(0, len(ys)))
        y, x = int(ys[k]), int(xs[k])
        if not (0 < y < a.shape[0] - 3 and 0 < x < a.shape[1] - 3):
            continue
        c = a[y, x]
        if c < 0 or c % 8 >= 6:
            continue
        f, t = int(c // 8), int(c % 8)
        r = rng.random()
        if r < 0.38:                                  # a pit: dark pair with a lit lip below
            sel = np.zeros(a.shape, bool)
            sel[y:y + 2, x:x + 2] = True
            sel &= mask
            a[sel] = f * 8 + max(0, t - 1)
            lip = np.roll(sel, 2, 0) & mask & ~sel
            a[lip] = f * 8 + min(5, t + 1)
        elif r < 0.55:                                # a short crack
            L = int(rng.integers(4, 9))
            pts = [(x, y), (x + int(rng.integers(-3, 4)), y + L // 2), (x + int(rng.integers(-4, 5)), y + L)]
            m = line_mask(a.shape, pts, 0.6) & mask
            a[m] = f * 8 + max(0, t - 2)
        elif r < 0.72 and lichen:                     # lichen
            sel = np.zeros(a.shape, bool)
            sel[y:y + 2, x:x + 3] = True
            a[sel & mask] = code('sand', 2)
        elif r < 0.85 and moss and y > ys.min() + (ys.max() - ys.min()) * 0.5:
            sel = np.zeros(a.shape, bool)
            sel[y:y + 2, x:x + int(rng.integers(3, 6))] = True
            a[sel & mask] = code('leaf_cool', int(rng.choice([1, 2])))
        else:                                         # a pale scuff
            sel = np.zeros(a.shape, bool)
            sel[y:y + 2, x:x + int(rng.integers(3, 6))] = True
            a[sel & mask] = f * 8 + min(5, t + 1)


# ------------------------------------------------------------------------------------------------
# round 5 (8 Nov review, docs/reviews/2026-11-08-undercroft-woodland-placed.md): the craft helpers.
# No even scatter of pale 2 x 2 specks anywhere (Matt's "terrazzo of specks", U1): stone is textured
# with sibling clusters gathered in drifts, aged with a few chipped corners and the cracks that run
# from them, and mossed only in its low joints with a lit cap.
# ------------------------------------------------------------------------------------------------
_CLUSTERS = (((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 0), (0, 1), (1, 0)), ((0, 0), (0, 1), (1, 1)),
             ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (1, 1)))


def tex(a, mask, rng, share=0.2, up=0.0, down=0.05, drift=2.6):
    """Material texture as clusters of two to four texels (dominoes, L shapes, 2 x 2): most only swap
    to a sibling ramp at the same tone (shape without value noise), a few step a tone down (and, only
    when asked, a tone up on the lit north-west half); they gather in drifts by a slow noise, so they
    never lie as an even scatter, and no pale dot sits alone in a calm field (scripts/review/specks.py)."""
    from .palette import sib, FAMS as FAMS_
    H, W = a.shape
    ok = mask & (a >= 0) & (a % 8 <= 5)
    ys, xs = np.nonzero(ok)
    if len(ys) < 12:
        return
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    dn = ndi.gaussian_filter(rng.random((H, W)), drift)
    dn = (dn - dn[ok].mean()) / (dn[ok].std() + 1e-9)
    side = 'warm' if rng.random() < 0.5 else 'cool'
    for _ in range(int(len(ys) * share / 2.6)):
        k = int(rng.integers(0, len(ys)))
        y, x = int(ys[k]), int(xs[k])
        if dn[y, x] < rng.normal(0.2, 0.7):
            continue
        c = int(a[y, x])
        pts = [(y + dy, x + dx) for dy, dx in _CLUSTERS[int(rng.integers(0, len(_CLUSTERS)))]
               if 0 <= y + dy < H and 0 <= x + dx < W and ok[y + dy, x + dx] and a[y + dy, x + dx] == c]
        if len(pts) < 2:
            continue
        u = ((x - x0) / max(1, x1 - x0) + (y - y0) / max(1, y1 - y0)) / 2
        r, t = rng.random(), c % 8
        if r < up and u < 0.5 and t <= 3:
            nc = c + 1
        elif r < up + down and t >= 2:
            nc = c - 1
        else:
            # the sibling nearest in value: a cool stone swaps to its body ramp, never straight to the warm
            # one (a cool-to-warm swap is a pale dot), a warm stone to its body, the body to either
            fn = FAMS_[c // 8]
            which = 'body' if (fn.endswith('_cool') or fn.endswith('_warm')) else side
            nc = int(sib(np.array([c]), which)[0])
        for p_ in pts:
            a[p_] = nc


def patches(a, mask, rng, sigma=2.2, sib_share=0.2, down=0.06):
    """Broad soft patches inside a surface: large blots on a sibling ramp at the same tone, and a few
    a tone down (worn hollows); never a tone up, so they add no pale dots (unlike mottle)."""
    from .palette import sib
    H, W = a.shape
    ok = mask & (a >= 0) & (a % 8 >= 1) & (a % 8 <= 5)
    if ok.sum() < 20:
        return
    n1 = ndi.gaussian_filter(rng.random((H, W)), sigma)
    n1 = (n1 - n1[ok].mean()) / (n1[ok].std() + 1e-9)
    n2 = ndi.gaussian_filter(rng.random((H, W)), sigma * 1.6)
    n2 = (n2 - n2[ok].mean()) / (n2[ok].std() + 1e-9)
    dn = ok & (n1 < np.quantile(n1[ok], down))
    dn = ndi.binary_opening(dn, structure=np.ones((2, 2), bool))
    a[dn] = a[dn] - 1
    sw = ok & (n2 > np.quantile(n2[ok], 1 - sib_share)) & ~dn
    a[sw] = sib(a[sw], 'warm' if rng.random() < 0.5 else 'cool')


def chip(a, x, y, corner, mortar, depth=2):
    """A corner knocked off a block (corner 'nw', 'ne', 'sw' or 'se' at x, y): an L of texels down to
    the mortar, and the fracture it leaves a tone up where it faces the light (north and west) or a
    tone down where it faces away."""
    H, W = a.shape
    sx = 1 if corner[1] == 'w' else -1
    sy = 1 if corner[0] == 'n' else -1
    gone = [(y, x), (y, x + sx), (y + sy, x)] + ([(y, x + 2 * sx)] if depth > 2 else [])
    lips = [(y + sy, x + sx), (y + 2 * sy, x), (y, x + (depth) * sx), (y + sy, x + 2 * sx)]
    for (yy, xx) in gone:
        if 0 <= yy < H and 0 <= xx < W and a[yy, xx] >= 0:
            a[yy, xx] = mortar
    d = 1 if corner[0] == 'n' else -1
    for (yy, xx) in lips:
        if 0 <= yy < H and 0 <= xx < W and a[yy, xx] >= 0 and a[yy, xx] != mortar and a[yy, xx] % 8 <= 5:
            a[yy, xx] = a[yy, xx] // 8 * 8 + int(np.clip(a[yy, xx] % 8 + d, 0, 4))


def crack(a, x, y, rng, length, mask, dx=None):
    """A crack running from a chip into the stone: a dark line a tone or two down, wandering, with its
    lower lip lit for part of its length (the far wall of the split catches the light)."""
    pts = [(x, y)]
    ang = rng.uniform(0.6, 2.5) if dx is None else (0.5 if dx > 0 else 2.6)
    n = max(2, int(length / 3))
    for _ in range(n):
        ang += rng.uniform(-0.6, 0.6)
        pts.append((pts[-1][0] + 3 * math.cos(ang), pts[-1][1] + 3 * abs(math.sin(ang)) * 0.9 + 0.4))
    m = line_mask(a.shape, pts, 0.5) & mask & (a >= 0) & (a % 8 <= 5)
    lip = np.roll(m, 1, 0) & ~m & mask & (a >= 0) & (a % 8 <= 5)
    lip &= (np.mgrid[0:a.shape[0], 0:a.shape[1]][1] < x + length * 0.5)
    a[lip] = a[lip] // 8 * 8 + np.minimum(4, a[lip] % 8 + 1)
    a[m] = a[m] // 8 * 8 + np.maximum(0, a[m] % 8 - 2)


def moss_clump(a, x, y, w, mask=None):
    """Moss in a low joint: a clump w texels wide, two rows of body (leaf_cool 2), a lit cap (leaf 3,
    one texel brighter at its west end) and a dark underside where it meets the stone."""
    V = _v()
    code = V.code
    H, W = a.shape
    for i in range(w):
        xx = x + i
        if not (0 <= xx < W):
            continue
        hgt = 2 + (1 if 0 < i < w - 1 and (i * 7 + x) % 3 == 0 else 0)
        for j in range(hgt):
            yy = y - j
            if 0 <= yy < H and a[yy, xx] >= 0 and (mask is None or mask[yy, xx]):
                a[yy, xx] = code('leaf_cool', 1 if j == 0 else 2)
        yy = y - hgt
        if 0 <= yy < H and a[yy, xx] >= 0 and (mask is None or mask[yy, xx]):
            a[yy, xx] = code('leaf', 4 if i < max(2, w // 3) else 3)


def age_block(a, x0, y0, x1, y1, rng, mortar, chips=2, cracks=1, mask=None):
    """Age on one dressed block: a corner or two knocked off and a crack that starts at one of them."""
    m = np.zeros(a.shape, bool)
    m[y0:y1, x0:x1] = True
    if mask is not None:
        m &= mask
    corners = [('nw', x0, y0), ('ne', x1 - 1, y0), ('sw', x0, y1 - 1), ('se', x1 - 1, y1 - 1)]
    order = rng.permutation(4)
    done = []
    for k in order[:chips]:
        c, x, y = corners[int(k)]
        chip(a, x, y, c, mortar, depth=2 + int(rng.random() < 0.4))
        done.append((c, x, y))
    for c, x, y in done[:cracks]:
        crack(a, x + (2 if c[1] == 'w' else -2), y + (2 if c[0] == 'n' else -3), rng,
              rng.uniform(0.35, 0.6) * (x1 - x0), m, dx=1 if c[1] == 'w' else -1)


def carve(a, m, lit, fam='stone_warm', t=3):
    """A glyph cut into stone. Dark (spent): the groove's floor in shade, its north and west walls
    darkest (tone 0), its south and east walls catching the light, and the stone's lip just outside
    its south and east edges a tone up. Charged: the groove holds the shard's light, deep violet at
    its walls rising through the dusk ramp to a near-white core, with one tone of spill on the stone
    round it and its south and east lips lit."""
    V = _v()
    code = V.code
    T, L, B, R = V.edges(m)
    south = np.roll(m, 1, 0) & ~m & (a >= 0)
    east = np.roll(m, 1, 1) & ~m & (a >= 0)
    north = np.roll(m, -1, 0) & ~m & (a >= 0)
    west = np.roll(m, -1, 1) & ~m & (a >= 0)
    if not lit:
        a[m] = code(fam, max(0, t - 2))
        a[(B | R) & ~T & ~L] = code(fam, max(0, t - 1))
        a[T | L] = code(fam, 0)
        a[(south | east) & ~north & ~west] = code(fam, min(4, t + 1))
        return m
    d = ndi.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]
    ramp = {1: ('dusk', 2), 2: ('dusk', 4), 3: ('dusk', 5)}
    for k, (f, tt) in ramp.items():
        a[m & (d >= k) & (d < k + 1)] = code(f, tt)
    a[m & (d >= 4)] = code('snow', 4)
    a[m & (T | L)] = code('dusk', 1)                      # the north and west walls stay in the groove's shade
    # the spill: one tone of the glow on the stone round the groove, a cool sibling a step up, broken
    spill = ndi.binary_dilation(m, iterations=2) & ~m & (a >= 0) & (a % 8 <= 4)
    br = ((np.mgrid[0:a.shape[0], 0:a.shape[1]].sum(0) // 3) % 4 == 0) & ~ndi.binary_dilation(m, iterations=1)
    spill &= ~br
    a[spill] = V.FI['stone_cool'] * 8 + np.minimum(4, a[spill] % 8 + 1)
    a[(south | east) & ~north & ~west & (a % 8 <= 4)] = code(fam, min(4, t + 1)) + 0
    return m


def cut_block(a, x0, y0, x1, y1, top, fam, t, rng=None, bevel=1, grain=True):
    """A dressed stone block seen like everything in the world (3/4 from above, light upper left):
    a top face `top` texels deep a tone lighter with a lit back arris, a bevel catching the light
    along the front edge, the front face shading down to a dark foot, the east end a step darker,
    and stone grain in both faces. x0..x1, y0..y1 is the whole drawn block in texels."""
    V = _v()
    code = V.code
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    yt = y0 + int(top)
    if yt > y0:
        V.blk(a, x0, y0, x1, yt, fam, min(5, t + 1), cut=1, top=1, left=1, bot=0, right=-1)
    V.blk(a, x0, yt, x1, y1, fam, t, cut=1, top=0, left=1, bot=-1, right=-1)
    for k in range(bevel):
        V.fill(a, x0 + 1, yt + k, x1 - 1, yt + k + 1, code(fam, min(5, t + 2) if k == 0 else min(5, t + 1)))
    V.fill(a, x0 + 1, y1 - 2, x1 - 1, y1 - 1, code(fam, max(0, t - 1)))
    V.fill(a, x1 - max(2, (x1 - x0) // 6), yt + bevel, x1 - 1, y1 - 2, code(fam, max(0, t - 1)))
    if grain and rng is not None and (x1 - x0) * (y1 - y0) > 60:
        m = np.zeros(a.shape, bool)
        m[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = True
        patches(a, m, rng, sigma=1.6, sib_share=0.1)


def masonry(cv, x0, y0, x1, y1, rng, where, base=2, course=5.0, length=(8, 14), east_dark=True):
    """Dressed wall stone in courses, every block lit on its top and west arris."""
    V = _v()
    q, code = V.q, V.code
    V.fill(cv, x0, y0, x1, y1, code('stone_cool', 0), where)
    y, k = y1, 0
    while y > y0 + 1:
        h = q(course)
        yt = max(y0, y - h)
        x = x0 - (q(length[0] / 2) if k % 2 else 0) - int(rng.integers(0, q(3)))
        while x < x1:
            L = q(rng.uniform(*length))
            t = base + int(rng.choice([-1, 0, 0, 0, 1]))
            if east_dark and x > x0 + 0.72 * (x1 - x0) and rng.random() < 0.5:
                t -= 1
            sx0, sx1 = max(x, x0), min(x + L - 1, x1)
            if sx1 - sx0 >= 3:
                V.blk(cv, sx0, yt, sx1, y - 1, STONES[int(rng.integers(0, 3))], max(0, t), cut=1, where=where)
            x += L
        y = yt
        k += 1


def root(cv, pts, r0, r1, where, rng, fam='earth_warm', base=2, lets=4):
    """A root along pts tapering r0 to r1 texels: round in section (its side towards the upper-left
    light a tone up, the far side a tone and then two down), bark in broken streaks along its length,
    thin rootlets splaying from it."""
    V = _v()
    H, W = cv.shape
    n = len(pts) - 1
    best = np.full((H, W), 1e9)
    u = np.zeros((H, W))
    rad = np.ones((H, W))
    along = np.zeros((H, W))
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    acc = 0.0
    for i, ((a, b), (c, d)) in enumerate(zip(pts, pts[1:])):
        dx, dy = c - a, d - b
        L = math.hypot(dx, dy) or 1e-6
        t = np.clip(((X - a) * dx + (Y - b) * dy) / (L * L), 0, 1)
        px, py = a + t * dx, b + t * dy
        dist = np.hypot(X - px, Y - py)
        rr = r0 + (r1 - r0) * (i + t) / n
        sel = (dist <= rr) & (dist < best)
        best[sel] = dist[sel]
        nx, ny = -dy / L, dx / L
        u[sel] = ((X - px) * nx + (Y - py) * ny)[sel] / rr[sel]
        lit_n = nx * -0.6 + ny * -0.8
        u[sel] *= (1 if lit_n >= 0 else -1)                     # +1 is the lit side
        rad[sel] = rr[sel]
        along[sel] = (acc + t * L)[sel]
        acc += L
    m = (best < 1e9) & where
    # rootlets (8 Nov, RT-1): few and uneven, each tapering from about three texels to one, bending as
    # it goes, its upper side lit, its tip running in under the floor (a crumb of soil over its end)
    for k in range(lets):
        i = int(rng.integers(1, len(pts)))
        x, y = pts[i]
        side = 1 if (k + int(rng.integers(0, 2))) % 2 else -1
        Lr = V.q(rng.uniform(3, 10))
        drop = V.q(rng.uniform(1.5, 4))
        bend = V.q(rng.uniform(0.8, 2.2)) * (1 if rng.random() < 0.5 else -1)
        n_ = 9
        chain = []
        for j in range(n_ + 1):
            t = j / n_
            chain.append((x + side * Lr * t, y + drop * t * t + bend * math.sin(t * math.pi)))
        lm = np.zeros((H, W), bool)
        lit_side = np.zeros((H, W), bool)
        for j, ((a0, b0), (c0, d0)) in enumerate(zip(chain, chain[1:])):
            r_ = 1.5 * (1 - j / n_) + 0.5
            seg = V.seg_mask(cv.shape, a0, b0, c0, d0, r_)
            lm |= seg
            lit_side |= V.seg_mask(cv.shape, a0, b0 - r_ * 0.6, c0, d0 - r_ * 0.6, max(0.5, r_ * 0.5))
        lm &= where & ~m
        cv[lm] = V.code(fam, base)
        cv[lm & lit_side & ~np.roll(lm, 1, 0)] = V.code(fam, min(5, base + 1))
        cv[lm & ~np.roll(lm, -1, 0)] = V.code(fam, max(0, base - 1))
        tx, ty = int(chain[-1][0]), int(chain[-1][1])
        if 1 <= ty < H - 1 and 1 <= tx < W - 2:                 # the tip runs in under the floor: the hole's dark
            cv[ty:ty + 2, tx - 1:tx + 1][where[ty:ty + 2, tx - 1:tx + 1]] = V.code('earth_cool', 0)
    tone = np.full((H, W), base)
    tone[u > 0.35] = base + 1
    tone[u > 0.7] = base + 2
    tone[u < -0.3] = base - 1
    tone[u < -0.75] = base - 2
    noise = ndi.gaussian_filter(rng.random((H, W)), 1.2)
    bark = (np.abs(((u + 1) * rad / 2.6) % 1 - 0.5) < 0.16) & (np.sin(along / 5.0 + noise * 9) > -0.2) & (rad > 3)
    tone[bark & m] -= 1
    cv[m] = V.FI[fam] * 8 + np.clip(tone[m], 0, 5)
    return m


def wall_top(cv, x0, y0, x1, y1, rng, where):
    """The soil and rubble over the vault seen from above: dark, stony, root-veined."""
    V = _v()
    V.rubble(cv, x0, y0, x1, y1, rng, fams=('stone_cool', 'stone_cool', 'stone'), base=1, course=(3.0, 4.4),
             length=(4, 9), moss=0.04, east_dark=False, where=where, mortar=('earth_cool', 0))
    for _ in range(max(1, (x1 - x0) * (y1 - y0) // 12000)):
        ax = int(rng.integers(x0, max(x0 + 1, x1)))
        ay = int(rng.integers(y0, max(y0 + 1, y1)))
        pts = [(ax, ay)]
        for _k in range(4):
            pts.append((pts[-1][0] + int(rng.integers(-V.q(6), V.q(6))), pts[-1][1] + int(rng.integers(-V.q(3), V.q(4)))))
        root(cv, pts, V.q(0.9), V.q(0.5), where, rng, base=1, lets=1)


def wall_face(cv, x0, y0, x1, y1, rng, where, roots=(), arcade=True, alcove=None):
    """A south face of the vault: cornice, blind arcade (pilasters, voussoired arches over shaded
    recesses), plinth and a dark foot. x0..x1, y0..y1 in texels."""
    V = _v()
    q, code = V.q, V.code
    masonry(cv, x0, y0, x1, y1, rng, where, base=2)
    corn, plin = q(3), q(5)
    # the plinth: a course of big blocks, lit top arris, a dark foot row
    masonry(cv, x0, y1 - plin, x1, y1, rng, where, base=2, course=5, length=(12, 18))
    V.fill(cv, x0, y1 - plin, x1, y1 - plin + 1, code('stone', 4), where)
    V.fill(cv, x0, y1 - 2, x1, y1, code('stone_cool', 0), where)
    if arcade and x1 - x0 >= q(40):
        bay, pil = q(48), q(8)
        # the bays: evenly over the face; where Cairn's alcove is, its own bay round it (a pilaster, the
        # alcove's 28 world px opening, the margins), the arcade evenly either side (8 Nov, G-11)
        def even(a0, a1):
            n_ = max(1, int(round((a1 - a0) / bay + 0.01)))
            return [(int(a0 + i * (a1 - a0) / n_), int(a0 + (i + 1) * (a1 - a0) / n_), False) for i in range(n_)]
        if alcove is not None:
            ab0, ab1 = alcove - q(14) - q(2) - pil, alcove + q(14) + q(2)
            bays = (even(x0, ab0) if ab0 - x0 >= q(20) else []) + [(ab0, ab1, True)] + \
                ([(ab1, x1, False)] if x1 - ab1 >= pil else [])
        else:
            bays = even(x0, x1)
        n = len(bays)
        for i, (bx0, bx1, is_alcove) in enumerate(bays):
            # the pilaster at the bay's west end
            px0, px1 = bx0, bx0 + pil
            pm = np.zeros(cv.shape, bool)
            pm[y0 + corn:y1 - plin, px0:px1] = True
            pm &= where
            masonry(cv, px0, y0 + corn, px1, y1 - plin, rng, pm, base=3, course=4.5, length=(8, 8.1), east_dark=False)
            # the recess under the arch
            rx0, rx1 = px1 + q(2), bx1 - q(2) if (i < n - 1 or is_alcove) else bx1 - pil - q(2)
            if rx1 - rx0 < q(10):
                continue
            rad = (rx1 - rx0) / 2
            cx = (rx0 + rx1) / 2
            spring = y0 + corn + q(3) + rad
            Y, X = np.mgrid[0:cv.shape[0], 0:cv.shape[1]] + 0.5
            rec = (((X - cx) ** 2 + (Y - spring) ** 2 <= rad * rad) & (Y < spring)) | \
                  ((X >= rx0) & (X < rx1) & (Y >= spring) & (Y < y1 - plin))
            rec &= where
            if is_alcove:                                      # Cairn's alcove: deeper, darker, the stones loose
                V.rubble(cv, rx0, y0, rx1, y1 - plin, rng, fams=STONES, base=0, course=(2.4, 3.2), length=(3, 6),
                         moss=0.3, east_dark=False, where=rec, mortar=('void', 0))
            else:
                V.rubble(cv, rx0, y0, rx1, y1 - plin, rng, fams=STONES, base=1, course=(2.6, 3.6), length=(4, 7),
                         moss=0.25, east_dark=False, where=rec, mortar=('stone_cool', 0))
            # shade: the west jamb and the arch soffit throw shadow into the recess
            sh = rec & ((X < rx0 + q(3)) | ((X - cx) ** 2 + (Y - spring) ** 2 >= (rad - q(3)) ** 2) & (Y < spring + q(2)))
            cv[sh] = V.FI['stone_cool'] * 8 + np.maximum(0, cv[sh] % 8 - 1)
            # the voussoirs: a ring of wedge blocks, lit on the upper left
            ring = ((X - cx) ** 2 + (Y - spring) ** 2 < (rad + q(3)) ** 2) & ~rec & (Y < spring) & where
            ring &= (X >= rx0 - q(3)) & (X < rx1 + q(3))
            ang = np.degrees(np.arctan2(Y - spring, X - cx))       # -180 west .. -90 top .. 0 east
            seg = np.floor((ang + 180) / 20).astype(int)
            joint = np.abs(((ang + 180) % 20) - 0) < (60 / max(rad, 1))
            t = np.where(ang < -90, 4, 3)
            cv[ring] = (V.FI['stone'] * 8 + t)[ring]
            cv[ring & (seg % 2 == 1)] = V.FI['stone_warm'] * 8 + t[ring & (seg % 2 == 1)]
            cv[ring & joint] = code('stone_cool', 1)
            # imposts: the springing blocks, lit on top
            for ix in (rx0 - q(3), rx1):
                V.blk(cv, ix, int(spring) - q(1), ix + q(3), int(spring) + q(2), 'stone', 4, cut=0, where=where)
    # the cornice: a lit lip, then the shadow under it
    V.fill(cv, x0, y0, x1, y0 + corn, code('stone', 3), where)
    V.fill(cv, x0, y0, x1, y0 + 2, code('stone', 4), where)
    V.fill(cv, x0, y0 + corn, x1, y0 + corn + 1, code('stone_cool', 0), where)
    V.fill(cv, x0, y0 + corn + 1, x1, y0 + corn + 2, code('stone_cool', 1), where)
    for k in range(x0, x1, q(10)):
        V.fill(cv, k, y0 + 2, k + 1, y0 + corn, code('stone', 2), where)
    # moss along the foot, in clusters
    for _ in range((x1 - x0) // q(9)):
        mx = int(rng.integers(x0, x1))
        V.fill(cv, mx, y1 - plin - 2, mx + int(rng.integers(3, 8)), y1 - plin, code('leaf_cool', int(rng.integers(1, 3))), where)
    patches(cv, where & ndi.binary_erosion(where, iterations=1), rng, sigma=1.8, sib_share=0.1)
    tex(cv, where & ndi.binary_erosion(where, iterations=1) & (cv % 8 >= 1), rng, share=0.22)       # sibling clusters in every block
    below = np.zeros(cv.shape, bool)
    for rx in roots:
        below |= split_root(cv, rx, y0, y1, rng, where)
    return below


def split_root(cv, x, y0, y1, rng, where):
    """One of the oak's roots breaking through the vault: a ragged hole at the cornice where it came
    through (broken stones lit round its lip), down the face with the masonry beside it cracked and a
    block pushed out, then over the plinth onto the floor."""
    V = _v()
    q, code = V.q, V.code
    pts = [(x, y0 + q(1))]
    y = y0 + q(1)
    ph = rng.uniform(0, 6.3)
    while y < y1 + q(6):                                  # it hangs in a slow sway, not a zigzag (8 Nov, G-5)
        y += q(5)
        pts.append((x + q(1.6) * math.sin(ph + (y - y0) / q(11)), y))
    hole = V.ellipse_mask(cv.shape, x, y0 + q(2.5), q(5), q(3)) & where
    ring = ndi.binary_dilation(hole, iterations=q(1.5)) & ~hole & where
    cv[ring] = code('stone', 4)
    cv[ring & (np.mgrid[0:cv.shape[0], 0:cv.shape[1]][0] > y0 + q(2.5))] = code('stone', 2)
    cv[hole] = code('void', 0)
    for side in (-1, 1):
        cy = y0 + q(rng.uniform(8, 22))
        cpts = [(pts[2][0] + side * q(2), cy)]
        for _ in range(4):
            cpts.append((cpts[-1][0] + side * q(rng.uniform(2, 4)), cpts[-1][1] + q(rng.uniform(-1.5, 2.5))))
        m = line_mask(cv.shape, cpts, 0.6) & where
        lip = np.roll(m, 1, 0) & ~m & where
        cv[lip] = code('stone', 3)
        cv[m] = code('stone_cool', 0)
    bx = pts[3][0] + q(4)
    by = y0 + q(14)
    cut_block(cv, bx, by, bx + q(9), by + q(5), q(1.5), 'stone', 3)
    V.fill(cv, bx + 1, by + q(5), bx + q(9), by + q(6), code('stone_cool', 0), where)
    allm = where.copy()
    allm[y1:y1 + q(8)] = True
    rm = root(cv, pts, q(4.4), q(2.0), allm, rng, base=2, lets=2)
    # a thinner strand over it and down the face beside it, the main root in its shadow where it passes
    pts2 = [(px + q(3.5) * math.sin(ph * 1.7 + k_ * 0.9) + q(2.5), py) for k_, (px, py) in enumerate(pts[1:-1])]
    r2 = np.zeros(cv.shape, bool)
    if len(pts2) > 2:
        r2 = root(cv, pts2, q(1.6), q(0.9), allm, rng, base=2, lets=0)
        sh2 = np.roll(r2, 1, 0) & rm & ~r2
        cv[sh2 | (np.roll(sh2, 1, 1) & rm & ~r2)] = code('earth_warm', 0)
    # where it reaches the floor it dives in (8 Nov round 3, RT-4): the dark gap it went into, and the edge
    # of the flag it lifted, lit on top, so it goes somewhere
    ex, ey = pts[-1]
    Y_, X_ = np.mgrid[0:cv.shape[0], 0:cv.shape[1]]
    gap = V.ellipse_mask(cv.shape, ex, ey + q(0.6), q(3.4), q(1.3))
    cv[gap & ~rm & ~r2] = code('void', 0)
    lip = V.ellipse_mask(cv.shape, ex + q(0.4), ey + q(1.6), q(3.8), q(1.0)) & ~gap
    lip &= Y_ > ey + q(0.9)
    cv[lip] = code('stone_cool', 3)
    cv[lip & ~np.roll(lip, 1, 0)] = code('stone_cool', 4)
    cv[lip & ~np.roll(lip, -1, 0)] = code('stone_cool', 1)
    return (rm | r2 | gap | lip) & (Y_ >= y1)


def stone_box(a, g, base, w, d, hgt, ang, fam, t, rng, rough=None, tilt=0.0, occl=None):
    """One fallen block, 3/4 from above (8 Nov, R-1): its footprint a w x d rectangle turned by `ang`
    about its foot point `base` (x, y on the canvas), lifted `hgt` texels (its corners raised by `tilt`
    along its length, so it can lie askew). Its top plane is tone t+1, a side facing west or south-west
    t (to t+1), a side facing south t, a side facing east t-2 (to t-1). One visible side (`rough`, an
    index) is a fracture face: a jagged top edge, pits and lit grains; the others are dressed (a lit
    arris, a tool line). Anything it lands on gets a dark contact line under it (R-2). Returns its mask."""
    V = _v()
    code = V.code
    H, W = a.shape
    c, s_ = math.cos(ang), math.sin(ang)
    hw, hd = w / 2, d / 2
    loc = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    foot = [(base[0] + x * c - y * s_, base[1] + x * s_ + y * c) for x, y in loc]
    lift = [hgt + tilt * (x / max(hw, 1)) for x, _ in loc]
    topp = [(fx, fy - l) for (fx, fy), l in zip(foot, lift)]
    before = a >= 0
    mask = np.zeros((H, W), bool)
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        ex, ey = foot[j][0] - foot[i][0], foot[j][1] - foot[i][1]
        nx, ny = ey, -ex                                           # outward normal (the footprint runs clockwise)
        L = math.hypot(nx, ny) or 1
        nx, ny = nx / L, ny / L
        if ny <= 0.05:
            continue
        quad = [foot[i], foot[j], topp[j], topp[i]]
        m = g.poly(quad)
        if nx < -0.35:
            tt = t                                                 # a west face, towards the light
        elif nx > 0.35:
            tt = max(0, t - 2)                                     # an east face, in shade
        else:
            tt = max(0, t - 1)                                     # a south face
        faces.append((i, m, tt, quad))
    for i, m, tt, quad in faces:
        a[m] = code(fam, tt)
        mask |= m
        if rough is not None and i == faces[min(rough, len(faces) - 1)][0]:
            fac = ndi.gaussian_filter(rng.random((H, W)), 0.9)
            fac = (fac - fac[m].mean()) / (fac[m].std() + 1e-9) if m.any() else fac
            a[m & (fac < -1.3)] = code(fam, max(0, tt - 1))        # pits in the broken face
            a[m & (fac > 1.2) & ~(np.roll(m, -1, 0) & ~m)] = code(fam, min(4, tt + 1))   # lit grains
        else:
            bot = m & ~np.roll(m, -1, 0)
            a[bot] = code(fam, max(0, tt - 1))                     # the dressed face darkens to its foot
            if m.sum() > 24:                                       # the mason's drafted margin, a sibling line
                ys_ = np.nonzero(m.any(1))[0]
                yl = int((ys_.min() + ys_.max()) / 2)
                ln = m & (np.arange(H)[:, None] == yl) & ~bot
                ln &= (np.arange(W)[None, :] + yl) % 5 != 0
                a[ln] = V.FI[fam + '_cool' if fam == 'stone' else 'stone'] * 8 + a[ln] % 8
        tex(a, m, rng, share=0.3, up=0.0)
    topm = g.poly(topp)
    a[topm] = code(fam, min(4, t + 1))
    mask |= topm
    ta = topm & ~np.roll(topm, 1, 0)
    tl = topm & ~np.roll(topm, 1, 1)
    a[(ta | tl) & topm] = code(fam, min(5, t + 2))                 # the top's back and west arris, lit
    front = topm & ~np.roll(topm, -1, 0)
    a[front] = code(fam, min(5, t + 2))                            # the arris where top meets the front, lit
    if rough is not None:                                          # the top's edge over the broken face, jagged
        jag = front & (rng.random((H, W)) < 0.45)
        a[jag] = code(fam, t)
    tex(a, topm & ~ta & ~tl & ~front, rng, share=0.3, up=0.0)
    ys_, xs_ = np.nonzero(topm)
    if len(ys_) > 30:                                              # a corner of the top knocked off, a crack from it
        k = int(np.argmin(xs_ + ys_ * 0.3))
        chip(a, int(xs_[k]), int(ys_[k]), 'nw', code(fam, 6))
        if rng.random() < 0.6:
            crack(a, int(xs_[k]) + 2, int(ys_[k]) + 1, rng, 0.5 * w, topm, dx=1)
    # contact: where it lies on something drawn before, a dark line under its lowest edge
    under = np.roll(mask, 1, 0) & ~mask & before
    under |= np.roll(under, 1, 1) & before & ~mask
    if occl is not None:
        under &= occl
    a[under] = a[under] // 8 * 8 + np.where(a[under] % 8 <= 5, 0, a[under] % 8)
    return mask


def p_rubble(w, h, seed):
    """Fallen vault stones (8 Nov, R-1 to R-4): cut blocks of many sizes (6 to 20 texels), each with a
    top plane, a lit west face, a south face and a dark east face, one face of each a rough fracture;
    the big ones on the floor, smaller ones lying on them askew or on edge, every upper block seated
    with a contact line on what it lies on; pebbles in three tones round the heap."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native.raster import Grid
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=h * 1.1, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    g = Grid(a.shape[1], a.shape[0], 1.0, 0, 0)
    fams = ('stone', 'stone_warm', 'stone_cool')
    span, depth = q(w) * 0.5, q(h) * 0.5
    blocks = []
    # the floor layer: three to five big blocks across the footprint, back to front
    n0 = 3 + int(w >= 20) + int(w >= 26)
    sizes = [20, 14, 11, 9, 16, 8][:n0]
    rng.shuffle(sizes)
    for k in range(n0):
        fx = -span * 0.62 + 1.24 * span * (k + rng.uniform(0.3, 0.7)) / n0
        fy = rng.uniform(-depth * 0.35, depth * 0.4)
        bw = sizes[k] * (0.8 + 0.2 * (w / 28)) * rng.uniform(0.9, 1.1)
        blocks.append(dict(x=cx + fx, y=yb - depth * 0.6 + fy, w=bw, d=bw * rng.uniform(0.55, 0.8), h=rng.uniform(4.5, 7),
                           ang=rng.choice([-1, 1]) * rng.uniform(0.15, 0.75), lvl=0))
    # the upper layer: smaller blocks resting on the floor layer, some askew, one on edge
    n1 = 1 + int(w >= 20) + int(w >= 26)
    for k in range(n1):
        b = blocks[int(rng.integers(0, n0))]
        on_edge = k == 0 and w >= 20
        blocks.append(dict(x=b['x'] + rng.uniform(-3, 3), y=b['y'] - rng.uniform(0, 2), w=rng.uniform(7, 10) if not on_edge else 7,
                           d=rng.uniform(5, 7) if not on_edge else 3.5, h=rng.uniform(3.5, 5) if not on_edge else 8,
                           ang=rng.uniform(-0.7, 0.7), lvl=b['h'] - 1, tilt=0.0))
    blocks.sort(key=lambda b: (b['lvl'] > 0, b['y']))
    for b in blocks:
        base = (b['x'], b['y'] - b['lvl'])
        stone_box(a, g, base, b['w'], b['d'], b['h'], b['ang'], str(rng.choice(fams)), 3,
                  rng, rough=int(rng.integers(0, 3)), tilt=b.get('tilt', 0.0))
    # pebbles and chips round the heap, each in three tones: a lit crown, a body, a dark foot
    for _ in range(int(w / 1.6)):
        x = int(cx + rng.uniform(-span - q(2), span + q(2)))
        y = int(yb - rng.uniform(0, depth * 0.8))
        if not (2 <= x < a.shape[1] - 5 and 3 <= y < a.shape[0] - 2) or (a[y - 2:y + 2, x - 1:x + 5] >= 0).any():
            continue
        # a pebble (8 Nov round 3, R-5): 4 or 5 texels across, irregular, never a plus: a lit pair at its
        # upper left over its body, a dark lower row, and the floor's dark under it
        f = str(rng.choice(fams))
        ww = int(rng.integers(4, 6))
        s0 = int(rng.integers(0, 2))
        a[y - 1, x + s0:x + s0 + ww - 2] = code(f, 3)
        a[y - 1, x + s0:x + s0 + 2] = code(f, 4)
        a[y, x:x + ww] = code(f, 3)
        a[y, x + ww - 2:x + ww] = code(f, 2)
        a[y + 1, x + (1 - s0):x + ww - s0] = code(f, 1)
    return V.finish(p)


def lifted_flag(a, g, x, y, w, rng, side=1):
    """A flag the root has lifted on its edge: a thin slab tilted up (its lit top edge, its face, a dark
    underside), and the black gap under it where the root goes into the ground."""
    V = _v()
    code = V.code
    gap = V.ellipse_mask(a.shape, x, y + 1, w * 0.55, 2.2)
    a[gap] = code('void', 0)
    a[gap & ~np.roll(gap, -1, 0)] = code('earth_cool', 0)
    pts = [(x - w / 2, y - 1), (x + w / 2, y - 1 - side * 3), (x + w / 2, y + 2 - side * 3), (x - w / 2, y + 2)]
    m = g.poly(pts)
    a[m] = code('stone_cool', 1)
    a[m & ~np.roll(m, 1, 0)] = code('stone_cool', 3)                  # its lifted edge catches the light
    a[m & ~np.roll(m, -1, 0)] = code('stone_cool', 0)
    return m


def flat_lifted_flag(a, g, x, y, w, side=1):
    """A flag the root has lifted, drawn in the floor's own stone (8 Nov round 4, RT-5): a slab tilted
    up, its top plane three or four texels in the shade floor's tones, its arris one rung up, and a dark
    gap of a texel only along its lower edge, where the root goes under it."""
    V = _v()
    code = V.code
    pts = [(x - w / 2, y - 2), (x + w / 2, y - 2 - side * 2.5), (x + w / 2, y + 2 - side * 2.5), (x - w / 2, y + 2)]
    m = g.poly(pts)
    a[m] = code('slate_cool', 1)
    a[m & ~np.roll(m, 1, 0)] = code('stone_warm', 1)                 # its arris, a rung up
    low = np.roll(m, -1, 0) & ~m & (a < 0)
    a[np.roll(low, 1, 0) & m] = code('slate_cool', 1)
    a[low] = code('void', 0)                                         # the gap under its lower edge only
    return m


def roots_from_floor(w, h, seed):
    """roots_corridor (8 Nov round 4, RT-5): roots that come up out of the floor (each strand from the dark
    of its own hole at a joint, the flag beside it lying flat) and go down again under a flag they have
    lifted. Three strands, uneven: each its own
    thickness, its own start and end, its own wobble, twisting loosely over one another; their bark in
    long fissures; two short rootlets above them, no longer than half the bundle is wide."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native.raster import Grid
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=6, side=10)
    a, cx, yb = p.a, p.ax, p.ay
    H, W = a.shape
    g = Grid(W, H, 1.0, 0, 0)
    allm = np.ones(a.shape, bool)
    span = q(w) / 2
    base_y = yb - q(h) * 0.45
    strands = []
    specs = ((-0.9, 0.62, 4.0, 1.2, q(1.6), 0.4), (-0.78, 0.8, 2.6, 0.8, q(2.4), 2.3), (-0.6, 0.45, 1.6, 0.5, q(1.2), 4.4))
    for k, (s0, s1, r0, r1, amp, ph) in enumerate(specs):
        n = 16
        pts = []
        for i in range(n + 1):
            t = i / n
            x = cx + span * (s0 + (s1 - s0) * t)
            arch = -math.sin(t * math.pi) * q(1.8 + 0.5 * k)
            wob = amp * math.sin(t * math.pi * (1.6 + 0.4 * k) + ph) + rng.uniform(-1.2, 1.2)
            pts.append((x, base_y + arch + wob + (k - 1) * 2.5))
        strands.append((pts, r0, r1))
    # where they come up out of the floor: the dark of the hole each strand rises from (drawn under them)
    for pts, r0, r1 in strands:
        hx, hy = pts[0]
        hole = V.ellipse_mask(a.shape, hx - r0 * 0.4, hy + r0 * 0.5, r0 + 2.2, r0 * 0.75 + 1)
        a[hole] = code('void', 0)
        a[hole & ~np.roll(hole, -1, 0)] = code('slate_cool', 1)            # the floor's lip over it
    done = np.zeros(a.shape, bool)
    for pts, r0, r1 in sorted(strands, key=lambda s_: s_[1]):          # thin first: the thick lie over them
        m = root(a, pts, r0, r1, allm, rng, base=2, lets=0)
        over = done & ndi.binary_dilation(m, iterations=1) & ~m
        a[over] = code('earth_warm', 0)
        done |= m
    # each strand's start goes down into its hole: its rounded end is lost in the dark there
    Xs = np.mgrid[0:H, 0:W][1]
    for pts, r0, r1 in strands:
        hx, hy = pts[0]
        inhole = done & V.ellipse_mask(a.shape, hx - r0 * 0.4, hy + r0 * 0.5, r0 + 2.2, r0 * 0.75 + 2) & (Xs < hx + 1.5)
        a[inhole] = code('earth_warm', 0)
        a[inhole & (Xs < hx - 1)] = code('void', 0)
    # where they dive: a flag lifted on its edge, in the floor's own stone
    ex = max(p_[0][-1][0] for p_ in strands)
    ey = np.mean([p_[0][-1][1] for p_ in strands])
    flat_lifted_flag(a, g, ex + q(0.6), ey + q(0.4), q(5.0), side=1)
    # two short rootlets above the strands, tapering into the floor's joints
    for k, t in enumerate((0.35, 0.62)):
        pts, r0, r1 = strands[1]
        i = int(t * (len(pts) - 1))
        bx, by = pts[i]
        L_ = q(2.2 + k)
        rl = [(bx, by - r0 * 0.6), (bx + L_ * 0.5, by - q(1.2)), (bx + L_, by - q(1.6) - k)]
        mm = line_mask(a.shape, rl, 0.6) & (a < 0)
        a[mm] = code('earth_warm', 2)
        a[mm & ~np.roll(mm, 1, 0)] = code('earth_warm', 3)
    rt = done
    low = np.zeros(a.shape, bool)
    low[int(yb - q(h) * 0.8):, :] = True
    under = np.roll(rt, 1, 0) & (a < 0) & low
    a[under | (np.roll(under, 1, 1) & (a < 0) & low)] = code('earth_cool', 0)
    V.finish(p)
    V.tidy(p.a, passes=2)
    return p


def p_roots(w, h, seed):
    """The oak's roots over the floor (8 Nov round 3, RT-4): roots, not a body. They come out of somewhere
    and go somewhere: out of the wall's foot (the hall) or from under a flag they have lifted (the corridor),
    braided strands of different thickness (8, 5 and 3 texels) twisting over one another, each round in
    section (lit upper side, dark underside) with long bark fissures, tapering as they run, one branch
    leaving them; their far ends dive into the floor beside a lifted flag, and the thinnest end as rootlets
    running into the joints. No rounded ends, no knot, no runners like legs."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native.raster import Grid
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=6, side=10)
    a, cx, yb = p.a, p.ax, p.ay
    H, W = a.shape
    g = Grid(W, H, 1.0, 0, 0)
    allm = np.ones(a.shape, bool)
    from_wall = h >= 10                            # roots_hall (28 x 10) stands at the north wall's foot
    if not from_wall:                              # roots_corridor: up from the floor (round 4, RT-5)
        return roots_from_floor(w, h, seed)
    span = q(w) / 2
    if from_wall:
        S = (cx + span * 0.7, 2.0)                 # out of the wall's foot, at the picture's top edge
        E = (cx - span * 0.9, yb - q(2.0))
    else:
        S = (cx - span * 0.95, yb - q(h) * 0.55)
        E = (cx + span * 0.85, yb - q(1.0))
    dx, dy = E[0] - S[0], E[1] - S[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L

    def strand(phase, amp, r0, r1, n=14):
        pts = []
        for i in range(n + 1):
            t = i / n
            bow = math.sin(t * math.pi) * q(2.2) * (1 if from_wall else -1)
            tw = amp * math.sin(t * math.pi * 2.2 + phase) * (0.4 + 0.6 * t)
            pts.append((S[0] + dx * t + nx * (bow + tw), S[1] + dy * t + ny * (bow + tw)))
        return pts, r0, r1

    strands = [strand(2.4, q(3.0), 1.6, 0.6), strand(0.2, q(2.2), 2.6, 0.8), strand(4.2, q(1.2), 4.2, 1.1)]
    done = np.zeros(a.shape, bool)
    for k, (pts, r0, r1) in enumerate(strands):
        m = root(a, pts, r0, r1, allm, rng, base=2, lets=0)
        over = done & ndi.binary_dilation(m, iterations=1) & ~m      # where it lies over a thinner strand
        a[over] = code('earth_warm', 0)
        done |= m
    # a branch leaving the braid, tapering to a rootlet that runs into a joint
    bi = 7
    bx, by = strands[2][0][bi]
    bpts = [(bx, by)]
    for i in range(1, 7):
        t = i / 6
        bpts.append((bx + q(5.5) * t * (1 if E[0] > S[0] else -1) * -1 + q(0.8) * math.sin(t * 3), by + q(3.2) * t * t + q(0.6) * t))
    bm = root(a, bpts, q(0.6), 0.5, allm & ~done, rng, base=2, lets=0)
    tx, ty = int(bpts[-1][0]), int(bpts[-1][1])
    a[ty:ty + 2, tx - 1:tx + 1] = code('earth_cool', 0)                  # into the joint
    # where they dive into the floor: a flag lifted on its edge and the dark gap the roots go into
    ed = 1 if E[0] > S[0] else -1                                        # which way they run
    lifted_flag(a, g, E[0] + ed * q(1.6), E[1] + q(0.4), q(5.5), rng, side=ed)
    for k in range(2):                                                   # the thinnest strands as rootlets past it
        ex, ey = strands[k][0][-1]
        rl = [(ex, ey), (ex + ed * q(2.2), ey + q(0.8) + k), (ex + ed * q(4.2), ey + q(0.4) + 2 * k)]
        mm = line_mask(a.shape, rl, 0.55)
        a[mm & (a < 0)] = code('earth_warm', 1)
    if not from_wall:                                                    # they come up from under a lifted flag
        cover = V.ellipse_mask(a.shape, S[0] + q(0.6), S[1] - q(0.6), q(3.6), q(2.6))
        a[cover & (a // 8 == V.FI['earth_warm'])] = -1                   # the strands' start lies under it
        done &= ~cover
        lifted_flag(a, g, S[0] + q(1.2), S[1] + q(0.8), q(8.5), rng, side=-1)
    if from_wall:                                                        # where they leave the wall: the plinth broken
        gap = V.ellipse_mask(a.shape, S[0], 0, q(3.4), q(1.6)) & ~done
        a[gap] = code('void', 0)
    # contact: a dark line on the floor under the strands where they lie on it
    rt = done | bm
    low = np.zeros(a.shape, bool)
    low[int(yb - q(h) * 0.8):, :] = True
    under = np.roll(rt, 1, 0) & (a < 0) & low
    a[under | (np.roll(under, 1, 1) & (a < 0) & low)] = code('earth_cool', 0)
    V.finish(p)
    V.tidy(p.a, passes=2)                                                # the kit's lone-pixel rule (at most 1 %)
    return p


def p_urn(w, h, seed):
    """A clay storage jar: a swelling body thrown on the wheel (form-shaded, lit upper left), a
    rolled rim round a dark mouth, two lug handles, a painted band, a chip knocked out of the
    shoulder showing the paler clay inside."""
    from scripts.art.native import raster as R
    V = _v()
    s = ctx.D / 3.0
    W, H = int(round(48 * s)), int(round(60 * s))
    sp = R.Sprite(W, H, s, W / 2 / s * s, (H - 4 * s))
    g = sp.g
    sp.add('body', g.ellipse(0, -18, 15, 17) | g.rrect(-7, -38, 7, -28, 2), 'clay', base=2, z=0, flat=True)
    sp.add('rim', g.ellipse(0, -39, 9.5, 3.6), 'clay', base=4, z=1, k=0.8)
    sp.add('mouth', g.ellipse(0, -39.3, 6.6, 2.2), 'clay', base=1, z=2, fixed=1, outline=False)
    for sx in (-1, 1):
        sp.add('lug%d' % sx, g.capsule(sx * 9, -33, sx * 14, -28, 2.4, 2.0), 'clay', base=3, z=-0.5, k=0.8)
    band = (g.ellipse(0, -18, 15.2, 17.2) & (g.Y > -24) & (g.Y < -20.5))
    sp.add('band', band, 'clay_cool', base=2, z=0.5, k=0.8, flat=True, lo=0, hi=4)
    sp.add('foot', g.ellipse(0, -1.5, 9, 2.5), 'clay_cool', base=2, z=-0.2)
    body = sp.part('body')
    body.lo, body.hi = 0, 5
    rings = np.zeros_like(body.mask)
    for ry in (-33, -29, -12, -7):                           # the potter's throwing rings
        rings |= (g.Y > ry) & (g.Y < ry + 1.1)
    sp.mark('body', rings, -1)
    runs = np.zeros_like(body.mask)
    for rx, L in ((-9, 9), (-4, 13), (2, 7), (8, 11)):        # glaze run down from the shoulder
        runs |= g.capsule(rx, -27, rx + 0.5, -27 + L, 1.1, 0.8)
    sp.mark('body', runs & ~band, 1)
    uu = (g.X + 15) / 30
    sp.mark('body', uu < 0.6, 1)
    sp.mark('body', (uu > 0.14) & (uu < 0.4), 1)             # the highlight band left of centre
    sp.mark('body', uu > 0.74, -1)                           # the core shadow on the right
    sp.mark('body', (uu > 0.86) & (uu < 0.95), -1)
    sp.mark('body', g.Y < -30, 1)                            # the shoulder turns up to the light
    sp.mark('body', g.ellipse(-6, -24, 3, 4), 1)              # the glaze catches the light
    ub = (g.X + 15.2) / 30.4                                 # the band is turned as the body is (UR-3)
    sp.mark('band', (ub > 0.12) & (ub < 0.42), 2)
    sp.mark('band', (ub <= 0.12) | ((ub >= 0.42) & (ub < 0.62)), 1)
    sp.mark('band', ub > 0.8, -1)
    sp.mark('band', g.Y < -23.3, 1)                          # its upper edge catches the light, its lower in shade
    sp.mark('band', g.Y > -21.2, -1)
    img = sp.render()
    p = V.Pic(W, H, W // 2, H - int(round(4 * s)) - 1)
    from .palette import code_of, FI
    arr = np.asarray(img)
    for y, x in zip(*np.nonzero(arr[..., 3] > 0)):
        e = code_of(arr[y, x, :3])
        if e == 'ink':
            p.a[y, x] = FI['soot'] * 8 + 0
        elif e is not None:
            p.a[y, x] = FI[e[0]] * 8 + int(e[1])
    a = p.a
    Y, X = np.mgrid[0:H, 0:W]
    rng = np.random.default_rng(seed)
    # the lit break (house-style.md): where the outline closes the lit west side, it is the clay's tone 1
    ink = a == V.FI['soot'] * 8
    westlit = ink & (np.roll(a, -1, 1) >= 0) & (np.roll(a, -1, 1) // 8 != V.FI['soot']) & (np.roll(a, -1, 1) % 8 >= 3)
    westlit &= X < W * 0.5
    a[westlit] = V.code('clay', 1)
    for y_ in range(H):                                       # the west side is the lit side: no shade just inside it
        xs_ = np.nonzero(a[y_] >= 0)[0]
        if len(xs_) > 4:
            x_ = xs_[0] + 1
            if a[y_, x_] // 8 == V.FI['clay'] and a[y_, x_] % 8 <= 1:
                a[y_, x_] = V.code('clay', 2)
    cxp, my = W / 2, H - 4 * s - 39.3 * s
    # the mouth (UR-1): an ellipse, the far inner wall lit, the near inner wall in shade, dark at the bottom
    mo = ((X + 0.5 - cxp) / (6.8 * s)) ** 2 + ((Y + 0.5 - my) / (2.6 * s)) ** 2 <= 1
    yy = (Y + 0.5 - my) / (2.6 * s)                          # -1 at the far lip, +1 at the near lip
    a[mo] = V.code('clay', 1)
    a[mo & (yy < -0.2)] = V.code('clay', 3)                  # the far inner wall, lit
    a[mo & (yy < -0.2) & (X + 0.5 < cxp - 1 * s)] = V.code('clay', 4)
    deep = ((X + 0.5 - cxp) / (4.2 * s)) ** 2 + ((Y + 0.5 - my - 0.7 * s) / (1.2 * s)) ** 2 <= 1
    a[mo & deep] = V.code('clay', 0)                         # the dark below, under the near lip
    a[mo & deep & (np.abs(X + 0.5 - cxp) < 2.6 * s) & (yy > 0.3)] = V.code('soot', 0)
    tex(a, (a // 8 == V.FI['clay']) & (a % 8 <= 5) & ~mo, rng, share=0.3, up=0.0, down=0.06)
    # the glint on the shoulder at the upper left (UR-2): a lit pair over its tone-4 halo
    gx, gy = int(cxp - 7 * s), int(H - 4 * s - 32 * s)
    a[gy:gy + 2, gx:gx + 2][a[gy:gy + 2, gx:gx + 2] >= 0] = V.code('sand', 5)
    a[gy, gx + 2] = V.code('sand', 4)
    # chips knocked out of the body (UR-4): the paler clay inside, a dark north lip over it
    for (dx, dy, w_) in ((-12, -12, 4), (7, -8, 3)):
        x0, y0 = int(cxp + dx * s), int(H - 4 * s + dy * s)
        sel = np.zeros(a.shape, bool)
        sel[y0:y0 + 2, x0:x0 + w_] = True
        sel[y0 + 2, x0 + 1:x0 + w_ - 1] = True
        sel &= a >= 0
        a[sel] = V.code('sand', 3 if dx < 0 else 2)
        lip = np.roll(sel, -1, 0) & ~sel & (a >= 0)
        a[lip] = V.code('clay', 1)
        a[np.roll(sel, 1, 0) & ~sel & (a >= 0)] = V.code('clay', 2)
    V.tidy(a, passes=2)                                      # no lone pixels (the kit's rule: at most 1 %)
    for y_ in range(H):                                       # (after the tidy) no shade just inside the lit west side
        xs_ = np.nonzero(a[y_] >= 0)[0]
        if len(xs_) > 4:
            x_ = xs_[0] + 1
            if a[y_, x_] // 8 == V.FI['clay'] and a[y_, x_] % 8 <= 1:
                a[y_, x_] = V.code('clay', 2)
    return p


# the two broken pillars differ (8 Nov, ST-3): where the break falls, how high, and what lies at the foot
_PILLARS = {0: dict(top=62, teeth=(3, 9, 5, 7, 1), lean=0.25, debris='drum'),
            1: dict(top=48, teeth=(1, 4, 11, 6, 2), lean=-0.2, debris='chips')}


def p_stump(w, h, seed):
    """A broken pillar of the old vault on its square plinth (8 Nov, ST-1 to ST-3). The fluted drum is
    shaded as a cylinder (a lit band left of centre, the core shadow right); where it broke, a rough
    top plane inside the column's ellipse: lit facets to the north-west, pits, and a dark rim to the
    south-east, with the teeth of the far side standing above it, their fracture faces turned to us.
    The plinth has a lit top and arris, chipped corners and the shaft's occlusion where it stands on
    it. One pillar keeps a fallen drum at its foot, the other a scatter of chips and a broken slab."""
    V = _v()
    code = V.code
    rng = np.random.default_rng(seed)
    s = ctx.D / 3.0
    W, H = int(round(84 * s)), int(round(104 * s))
    ay = int(round(H - 6 * s))
    p = V.Pic(W, H, W // 2, ay)
    a = p.a
    cfg = _PILLARS[seed % 2]
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    cx, by = W / 2, ay + 0.5                       # by: the plinth's foot
    r = (w * 3 / 2 - 3) * s                        # the drum's radius (texels)
    pr = r + 6 * s
    mortar = code('stone_cool', 0)
    # --- the plinth: a top plane (7 rows), a front face (9 rows), lit west, dark east -----------------
    pt0, pf0 = by - 16 * s, by - 9 * s
    top = (X >= cx - pr) & (X < cx + pr) & (Y >= pt0) & (Y < pf0)
    front = (X >= cx - pr) & (X < cx + pr) & (Y >= pf0) & (Y < by)
    a[top] = code('stone', 4)
    a[front] = code('stone', 3)
    u = (X - (cx - pr)) / (2 * pr)
    a[front & (u > 0.78)] = code('stone', 2)
    a[front & (u > 0.92)] = code('stone', 1)
    a[front & (u < 0.06)] = code('stone', 4)
    a[top & (u > 0.86)] = code('stone', 3)
    a[(Y >= pf0) & (Y < pf0 + 1) & (X >= cx - pr + 1) & (X < cx + pr - 2)] = code('stone', 5)   # the lit arris
    for k in range(int(cx - pr + 7), int(cx + pr - 4), 10):
        a[int(pf0), k:k + 2] = code('stone', 4)                               # worn in places
    a[(Y >= by - 2) & front] = code('stone', 1)                               # the foot
    tex(a, front & (Y < by - 2) & (u < 0.9), rng, share=0.4)
    tex(a, top, rng, share=0.35)
    chip(a, int(cx - pr), int(pt0), 'nw', mortar)
    chip(a, int(cx + pr) - 1, int(by) - 1, 'se', mortar)
    chip(a, int(cx + pr) - 1, int(pf0) + 1, 'ne', mortar)
    crack(a, int(cx + pr) - 4, int(pf0) + 3, rng, 7, front, dx=-1)
    # --- the shaft --------------------------------------------------------------------------------
    ytop = by - cfg['top'] * s
    ery = r * 0.38                                  # the column's ellipse, seen from above at 3/4
    base_y = pt0 + 3.5 * s
    shaft = (np.abs(X - cx) <= r) & (Y <= base_y + ery * np.sqrt(np.clip(1 - ((X - cx) / r) ** 2, 0, 1))) & \
            (Y >= ytop + ery * np.sqrt(np.clip(1 - ((X - cx) / r) ** 2, 0, 1)))
    uc = (X - cx + r) / (2 * r)
    tt = np.select([uc < 0.1, uc < 0.42, uc < 0.62, uc < 0.84], [3, 4, 3, 2], 1)
    a[shaft] = (V.FI['stone'] * 8 + tt)[shaft]
    a[shaft & (uc > 0.17) & (uc < 0.3)] = code('stone', 5)                    # the highlight's heart
    for fx in np.linspace(-r + 4 * s, r - 4 * s, 6):                          # flutes: a shaded groove, its far edge lit
        g_ = shaft & (X >= cx + fx - 0.5) & (X < cx + fx + 0.5)
        a[g_] = a[g_] // 8 * 8 + np.maximum(0, a[g_] % 8 - 1)
        l_ = shaft & (X >= cx + fx + 0.5) & (X < cx + fx + 1.5) & (uc < 0.8)
        a[l_] = a[l_] // 8 * 8 + np.minimum(5, a[l_] % 8 + 1)
    # the drums' joints, a course apart, dark with a lit lip under them
    for jy in np.arange(base_y - 22 * s, ytop + 4 * s, -22 * s):
        jm = shaft & (np.abs(Y - (jy + ery * np.sqrt(np.clip(1 - ((X - cx) / r) ** 2, 0, 1)))) < 0.6)
        a[jm] = a[jm] // 8 * 8 + np.maximum(0, a[jm] % 8 - 2)
        a[np.roll(jm, 1, 0) & shaft & ~jm] = code('stone', 4)
    # occlusion where the shaft stands on the plinth: a dark band round its foot, deepest east
    occ = top & ~shaft & (((X - cx) / (r + 2.5)) ** 2 + ((Y - base_y) / (ery + 2)) ** 2 <= 1) & (Y > base_y - 1)
    a[occ] = code('stone', 2)
    a[occ & (X > cx)] = code('stone', 1)
    footm = shaft & (Y > base_y + ery * np.sqrt(np.clip(1 - ((X - cx) / r) ** 2, 0, 1)) - 2.5)
    a[footm] = a[footm] // 8 * 8 + np.maximum(0, a[footm] % 8 - 1)
    tex(a, shaft & (uc < 0.86), rng, share=0.25)
    # --- the break: teeth of the far side, then the top plane ----------------------------------------
    plane = (((X - cx) / r) ** 2 + ((Y - ytop) / ery) ** 2 <= 1)
    teeth = np.zeros((H, W), bool)
    xs = np.linspace(-r, r, len(cfg['teeth']) + 1)
    for k, th in enumerate(cfg['teeth']):
        xa, xb = xs[k], xs[k + 1]
        xm = (xa + xb) / 2 + cfg['lean'] * th
        ya = ytop - ery * np.sqrt(max(0, 1 - (xa / r) ** 2))
        yb = ytop - ery * np.sqrt(max(0, 1 - (xb / r) ** 2))
        wd = xb - xa
        tri = [(cx + xa, ya + 0.6), (cx + xm - 0.22 * wd, ytop - ery - th * s), (cx + xm + 0.12 * wd, ytop - ery - th * s * 0.7),
               (cx + xb, yb + 0.6)]
        from scripts.art.native.raster import Grid
        teeth |= Grid(W, H, 1.0, 0, 0).poly(tri)
    teeth &= ~plane
    a[teeth] = code('stone_warm', 3)                                         # the fracture faces, turned to us
    tu = (X - cx + r) / (2 * r)
    a[teeth & (tu > 0.62)] = code('stone_warm', 2)
    a[teeth & (tu > 0.85)] = code('stone_warm', 1)
    tedge = teeth & ~np.roll(teeth, 1, 0)
    a[tedge & (tu < 0.6)] = code('stone_warm', 5)                            # their lit crests
    a[tedge & (tu >= 0.6)] = code('stone_warm', 3)
    tex(a, teeth, rng, share=0.35, up=0.0)
    # the top plane: rough, lit facets to the north-west, pits, a dark rim to the south-east
    pu = (X - cx) / r + (Y - ytop) / ery
    a[plane] = code('stone_warm', 3)
    fac = ndi.gaussian_filter(rng.random((H, W)), 1.1)
    fac = (fac - fac[plane].mean()) / (fac[plane].std() + 1e-9)
    a[plane & (pu < -0.3) & (fac > -0.3)] = code('stone_warm', 4)
    a[plane & ndi.binary_opening((pu < -0.75) & (fac > 0.5), structure=np.ones((2, 3), bool))] = code('stone_warm', 5)
    a[plane & (pu > 0.35) & (fac < 0.3)] = code('stone_warm', 2)
    rimm = plane & ~ndi.binary_erosion(plane, iterations=1)
    a[rimm & (pu > 0.1)] = code('stone_warm', 1)                              # the south-east rim in shade
    a[rimm & (pu <= 0.1) & (Y > ytop)] = code('stone', 5)                    # the near lip lit where it faces the light
    pits = plane & ~rimm & (fac < -1.25)
    a[pits] = code('stone_warm', 1)
    a[np.roll(pits, 1, 0) & plane & ~pits & ~rimm] = code('stone_warm', 4)
    # --- what lies at the foot ----------------------------------------------------------------------
    if cfg['debris'] == 'drum':
        # a fallen drum on its side, east of the plinth: its end face an ellipse with the flutes' notches
        dx0, dy0 = cx + pr + 2 * s, by - 5 * s
        body = (X >= dx0) & (X < dx0 + 9 * s) & (np.abs(Y - dy0) <= 5 * s)
        endf = ((X - dx0) / (2.6 * s)) ** 2 + ((Y - dy0) / (5.2 * s)) ** 2 <= 1
        vv = (Y - dy0) / (5 * s)
        a[body] = np.where(vv[body] < -0.4, code('stone', 4), np.where(vv[body] < 0.3, code('stone', 3), code('stone', 2)))
        a[body & (vv > 0.75)] = code('stone', 1)
        a[endf] = code('stone_warm', 3)
        a[endf & ((X - dx0) + (Y - dy0) * 0.5 < -1.5)] = code('stone_warm', 4)
        a[endf & ~ndi.binary_erosion(endf) & (Y > dy0)] = code('stone_warm', 1)
        for ny in (-3, 0, 3):
            a[int(dy0 + ny * s), int(dx0 + 3):int(dx0 + 9 * s)] = code('stone', 2)
        tex(a, body & ~endf, rng, share=0.3)
    else:
        # a broken slab leaning on the plinth's east side, in its shade, and chips round it
        sx0 = cx + pr - 1
        slab = [(sx0, by - 1), (sx0 + 1 * s, by - 9 * s), (sx0 + 7 * s, by - 11 * s), (sx0 + 9 * s, by - 1)]
        from scripts.art.native.raster import Grid
        sm = Grid(W, H, 1.0, 0, 0).poly(slab) & (a < 0)
        a[sm] = code('stone_cool', 2)
        su = (X - sx0) / (10 * s)
        a[sm & (su < 0.3)] = code('stone_cool', 3)
        a[sm & (su > 0.75)] = code('stone_cool', 1)
        a[sm & (Y > by - 3 * s)] = code('stone_cool', 1)
        a[sm & ~np.roll(sm, 1, 0) & (su < 0.6)] = code('stone_cool', 4)
        tex(a, sm, rng, share=0.3)
        for (ox, oy, ww) in ((-pr - 5, -2, 4), (-pr - 10, -4, 3), (pr + 11, -1, 3)):
            x0, y0 = int(cx + ox * s), int(by + oy * s)
            if 0 <= x0 < W - ww and 0 < y0 < H - 2:
                a[y0 - 1, x0:x0 + ww - 1] = code('stone', 4)
                a[y0, x0:x0 + ww] = code('stone', 3)
                a[y0 + 1, x0 + 1:x0 + ww] = code('stone', 1)
    return V.finish(p)


def p_shard(w, h, seed):
    """The woodland's great shard: a long crystal of the moon driven into the floor at a slant (8 Nov,
    SH-1). Its faces catch the upper-left light each in its own tone (the lit face, a mid face, the
    shadow face), the ridges between them lit where they face the light, two or three facet lines
    inside the faces, cap facets meeting in its point (a tone-4 plane with tone-5 edges towards the
    light), sparkles in pairs and a one-texel outline in the crystal's edge tone. The heaved flags
    round its foot are drawn in the ground."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native.raster import Grid
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=32, side=8)
    a, cx, yb = p.a, p.ax, p.ay
    g = Grid(a.shape[1], a.shape[0], 1.0, 0, 0)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    # the crystal's axis leans east; its section is a hexagon, three faces towards us
    foot_l, foot_m, foot_r = (cx - q(5), yb - q(1.5)), (cx + q(0.5), yb + 0), (cx + q(4.5), yb - q(1))
    top_l, top_m, top_r = (cx + q(1.2), yb - q(27)), (cx + q(5.2), yb - q(26)), (cx + q(8.4), yb - q(28))
    apex = (cx + q(4.4), yb - q(34))                 # the point: the cap facets meet in it
    lit = g.poly([foot_l, top_l, top_m, foot_m])
    mid = g.poly([foot_m, top_m, top_r, foot_r])
    a[lit] = code('dusk', 3)
    a[mid] = code('dusk', 2)
    a[mid & (X > cx + q(3.2))] = code('dusk', 1)     # the shadow side, turning away
    cap_l = g.poly([top_l, apex, top_m])
    cap_r = g.poly([top_m, apex, top_r])
    cap_b = g.poly([top_l, (cx + q(3.0), yb - q(30)), apex])
    a[cap_b] = code('dusk', 4)
    a[cap_l] = code('dusk', 4)                       # the cap facet towards the light
    a[cap_r] = code('dusk', 2)
    cap = cap_l | cap_r | cap_b
    # inside the lit face: a broad paler band (a second facet) and the facet lines
    band = g.poly([(cx - q(3.2), yb - q(1.8)), (cx + q(2.2), yb - q(26.6)), (cx + q(3.4), yb - q(26.4)), (cx - q(1.4), yb - q(1.2))])
    a[band & lit] = code('dusk', 4)
    for k, (f0, f1, t) in enumerate((((cx - q(1.0), yb - q(4)), (cx + q(2.8), yb - q(20)), 2),
                                      ((cx + q(2.2), yb - q(3)), (cx + q(6.2), yb - q(18)), 3),
                                      ((cx - q(3.6), yb - q(8)), (cx - q(0.6), yb - q(19)), 5))):
        m = line_mask(a.shape, [f0, f1], 0.55) & (lit | mid) & ~cap
        a[m] = code('dusk', t if not (k == 1) else 3)
    # the ridges: lit where they face the light, the cap's edge brightest
    ridge = line_mask(a.shape, [foot_m, top_m], 0.7) & (lit | mid)
    a[ridge] = code('dusk', 5)
    a[line_mask(a.shape, [top_l, apex], 0.7) & cap] = code('dusk', 5)    # the cap's lit edges
    a[line_mask(a.shape, [top_m, apex], 0.6) & cap] = code('dusk', 5)
    ledge = line_mask(a.shape, [foot_l, top_l], 0.7) & lit
    a[ledge & (Y < yb - q(10))] = code('dusk', 4)
    # sparkles in pairs, on the lit face and the cap
    for (sx, sy) in ((cx - q(1.5), yb - q(15)), (cx + q(1.2), yb - q(23)), (cx + q(3.2), yb - q(29.0))):
        sx, sy = int(sx), int(sy)
        a[sy, sx:sx + 2] = code('snow', 4)
        a[sy - 1, sx] = code('snow', 5)
    # growth steps across the faces: short facets a sibling over (shape without value noise), the inner
    # planes a tone apart, inclusions in pairs, and the light coming back through the crystal along
    # its shadowed east edge
    body = (lit | mid) & ~cap & (a % 8 <= 5)
    for k in range(7):
        yy = yb - q(3 + 3.6 * k)
        stepm = body & (Y > yy - q(1.2)) & (Y < yy) & (((X - Y // 2) // q(2.2)) % 3 == k % 3)
        a[stepm] = V.FI['dusk_cool'] * 8 + a[stepm] % 8
    inner = mid & ~cap & (X > cx + q(4.6)) & (Y < yb - q(6)) & (Y > yb - q(24))
    a[inner & (a == code('dusk', 1))] = code('dusk_cool', 2)
    back = mid & ~ndi.binary_erosion(mid, iterations=2) & (X > cx + q(5)) & ~np.roll(mid, -2, 1)
    a[back & (Y < yb - q(4)) & (Y > yb - q(25))] = code('dusk', 3)             # light back through the crystal
    for (ix, iy, t) in ((-2.4, 9, 4), (0.4, 13, 4), (-0.6, 19, 2), (2.8, 9.5, 3), (4.4, 15, 3), (5.6, 21, 2), (1.6, 6, 5)):
        x_, y_ = int(cx + q(ix)), int(yb - q(iy))
        if body[y_, x_]:
            a[y_, x_:x_ + 2] = code('dusk_cool', t)
    # fractures near the foot, where it went in
    for k in range(2):
        f0 = (cx - q(3.5) + k * q(5), yb - q(1))
        f1 = (f0[0] + q(1.2), yb - q(6))
        m = line_mask(a.shape, [f0, f1], 0.55) & (lit | mid)
        a[m] = code('dusk', 1)
    V.tidy(a, keep=(a == code('snow', 4)) | (a == code('snow', 5)))
    V.outline(a)
    return p


# the flame's tongues per frame: (x offset of the tongue's foot, its lean, its height, its foot radius),
# texels at density 3. They part and rejoin over the four frames: frame 1 splits a west tongue off the
# main one, frame 2 lifts the main tongue and draws the east one in, frame 3 parts the east tongue.
_TONGUES = (
    ((0.0, 0.6, 29, 4.4), (-2.4, -2.0, 18, 2.4), (2.2, 1.2, 14, 2.0)),
    ((0.4, -1.4, 26, 4.2), (-3.0, -4.2, 21, 2.2), (2.4, 1.8, 12, 1.8)),
    ((-0.2, 1.6, 32, 4.2), (-2.0, -1.0, 13, 2.0), (1.8, 3.6, 20, 2.2)),
    ((0.2, -0.4, 28, 4.4), (-2.6, -2.6, 16, 2.2), (2.8, 4.6, 19, 2.0)),
)
_CORE = ((-0.6, 0), (0.8, -1), (-1.0, 1), (0.6, 0))          # the white core's offset frame by frame (x, lift)
_EMBERS = (((5, -38),), ((-6, -36), (4, -42)), ((-3, -44),), ((7, -34), (-5, -41)))


def p_torch(frame, seed):
    """A wall torch (8 Nov, T-1, T-2): an iron wall plate with two rivets, an arm out from it, a cup
    with a lit elliptical rim, its inside dark and a wad of pitch-soaked rag in it, and the flame: two
    or three tongues that part and rejoin over four frames (a finite flicker; the plate and cup never
    move), deep red-orange at their foot, the white core moving from frame to frame, embers rising
    in pairs. The canvas's foot is the cup; the flame is a light source (no outline)."""
    V = _v()
    q, code = V.q, V.code
    W, H = q(10), q(22)
    p = V.Pic(W, H, W // 2, H - q(6))
    a, cx, cy = p.a, p.ax, p.ay
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    # the wall plate: a sheen to the upper left, lit top edge, dark foot and east edge, two rivets
    px0, px1, py0, py1 = cx - 4, cx + 4, cy + 7, cy + 18
    pl = (X >= px0) & (X < px1) & (Y >= py0) & (Y < py1)
    dg = (X - px0) / 8 + (Y - py0) / 11
    a[pl] = np.where(dg[pl] < 0.6, code('iron', 3), np.where(dg[pl] < 1.3, code('iron', 2), code('iron', 1)))
    a[pl & (Y < py0 + 1)] = code('iron', 4)
    a[pl & (X < px0 + 1) & (Y >= py0 + 1)] = code('iron', 3)
    a[pl & (Y >= py1 - 1)] = code('iron', 0)
    a[pl & (X >= px1 - 1)] = code('iron', 1)
    for ry in (py0 + 2, py1 - 4):
        a[ry, cx - 1:cx + 1] = code('iron', 5) if ry < py0 + 5 else code('iron', 4)
        a[ry + 1, cx - 1:cx + 1] = code('iron', 0)
    # the arm: out from the plate and up to the cup, a curl to the east (a forged bracket)
    arm = V.seg_mask(a.shape, cx - 0.5, cy + 8, cx - 0.5, cy + 2, 1.3)
    a[arm] = code('iron', 2)
    a[arm & (X < cx)] = code('iron', 4)
    a[arm & (X >= cx + 1)] = code('iron', 1)
    curl = V.seg_mask(a.shape, cx + 1, cy + 7, cx + 5, cy + 5, 0.8) | V.seg_mask(a.shape, cx + 5, cy + 5, cx + 5, cy + 3, 0.8)
    curl &= ~arm
    a[curl] = code('iron', 2)
    a[curl & (np.roll(curl, 1, 0) == 0)] = code('iron', 3)
    # the cup: an iron bowl, round in section (lit west, core shadow east), its rim an ellipse
    bowl = V.ellipse_mask(a.shape, cx, cy - 1, 6.2, 3.8) & (Y >= cy - 1)
    u = (X - (cx - 6.2)) / 12.4
    tt = np.where(u < 0.18, 3, np.where(u < 0.45, 4, np.where(u < 0.7, 2, 1)))
    a[bowl] = (V.FI['iron'] * 8 + tt)[bowl]
    a[bowl & (Y >= cy + 2)] = np.minimum(a[bowl & (Y >= cy + 2)], code('iron', 2))
    for bx in (-3, 2):                                     # the bowl's straps, forged on
        st = (X >= cx + bx) & (X < cx + bx + 1) & bowl & (Y > cy)
        a[st] = code('iron', 1)
    rim = V.ellipse_mask(a.shape, cx, cy - 1, 6.6, 2.2)
    inside = V.ellipse_mask(a.shape, cx, cy - 1.2, 4.8, 1.2)
    a[rim] = code('iron', 3)
    a[rim & (X < cx - 1)] = code('iron', 4)
    a[rim & (Y < cy - 1.5) & (X < cx + 2)] = code('iron', 5)                 # the far rim catches the light
    a[rim & (Y > cy - 0.5) & (X > cx + 1)] = code('iron', 2)
    a[inside] = code('soot', 0)
    # the rag: a wad of pitch-soaked cloth in the cup, its folds lit by the flame
    rag = V.ellipse_mask(a.shape, cx - 0.3, cy - 3.0, 3.8, 1.9) & ~(Y > cy - 0.8)
    a[rag] = code('soot', 2)
    a[rag & (X < cx)] = code('soot', 3)
    a[rag & (Y < cy - 3.6)] = code('earth_cool', 2)
    a[rag & (Y < cy - 3.6) & (X > cx + 1)] = code('earth_cool', 1)
    V.outline(a)
    # the flame
    base_y = cy - 5
    tongues = _TONGUES[frame % 4]
    body = np.zeros(a.shape, bool)
    heart = np.zeros(a.shape, bool)
    for k, (fx, lean, hgt, r0) in enumerate(tongues):
        for i in range(24):
            t = i / 23
            r = r0 * (1 - t) ** 0.85 + 0.35
            x = cx + fx + lean * t * t + (0.8 * math.sin(t * 5 + frame + k) * t if k else 0)
            y = base_y - hgt * t
            e = ((X - x) / r) ** 2 + ((Y - y) / (r * 1.25)) ** 2 <= 1
            body |= e
            if k == 0 and t < 0.62:
                heart |= ((X - x) / (r * 0.62)) ** 2 + ((Y - y) / (r * 0.8)) ** 2 <= 1
    body &= Y < cy - 4.3
    hgt0 = tongues[0][2]
    lift = (base_y - Y) / hgt0                                           # 0 at the foot, 1 at the main tip
    a[body] = code('lava', 3)
    inner = ndi.binary_erosion(body, iterations=2)
    a[inner] = code('lamp', 3)
    rim_f = body & ~ndi.binary_erosion(body, iterations=1)
    a[rim_f & (lift < 0.3)] = code('lava', 2)                            # deep red-orange round the foot
    a[body & (lift < 0.05)] = code('lava', 2)
    a[rim_f & (lift < 0.12)] = code('lava', 1)
    a[heart & (lift > 0.08)] = code('lamp', 4)
    ox, ol = _CORE[frame % 4]
    core = ((X - cx - ox) / 1.7) ** 2 + ((Y - (base_y - 8 + ol)) / 3.6) ** 2 <= 1
    a[core & body] = code('lamp', 5)
    edge = body & ~ndi.binary_erosion(body)
    a[edge & (lift > 0.55)] = code('lava', 4)                            # the tips thin to pale orange
    for ex, ey in _EMBERS[frame % 4]:
        ex_, ey_ = cx + ex, cy + ey
        if 0 <= ey_ < H - 1 and 0 <= ex_ < W - 1:
            a[ey_:ey_ + 2, ex_] = code('lamp', 4)                         # an ember: a pair
    V.tidy(a, keep=(a // 8 == V.FI['lamp']) & (Y < base_y - hgt0))
    return p


def slab_top(a, x0, y0, x1, y1, fam, t, rng, mortar, lip=2, chips=2, cracks=1, texture=0.5):
    """A flag or slab seen from above (8 Nov, SE-1, G-3): calm, one tone of its stone with sibling
    clusters, a lit north and west lip a tone up (broken where it is worn), a south and east lip a
    tone down, its corners chipped and a crack from one of them. Never a glossy stripe: flags do not
    shine. Returns the slab's mask."""
    V = _v()
    code = V.code
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    w, h = x1 - x0, y1 - y0
    if w < 3 or h < 3:
        return np.zeros(a.shape, bool)
    m = np.zeros(a.shape, bool)
    m[y0:y1, x0:x1] = V.chamfer(h, w, 1)
    a[m] = code(fam, t)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    gaps = np.kron(rng.random(((a.shape[0] + 3) // 4, (a.shape[1] + 3) // 4)) < 0.16, np.ones((4, 4), bool))
    gaps = gaps[:a.shape[0], :a.shape[1]]
    nw = m & ((Y < y0 + lip) | (X < x0 + lip))
    se = m & ((Y >= y1 - lip) | (X >= x1 - lip)) & ~nw
    a[nw & ~gaps] = code(fam, min(4, t + 1))
    a[se] = code(fam, max(0, t - 1))
    a[m & ((Y == y1 - 1) | (X == x1 - 1)) & ~nw] = code(fam, max(0, t - 2))     # the arris in shade
    body = m & ~nw & ~se
    patches(a, body, rng, sigma=2.0, sib_share=0.22)                         # broad soft patches of its siblings
    tex(a, body, rng, share=texture)
    age_block(a, x0, y0, x1, y1, rng, mortar, chips=chips, cracks=cracks, mask=m)
    return m


def age_courses(a, mask, rng, mortar, moss_rows=None, chip_p=0.5, crack_p=0.2, moss_p=0.3):
    """Age on a face of courses already laid (masonry): each block found by its joints gets sibling
    clusters, perhaps a chipped corner and a crack from it, and the lowest joints a moss clump."""
    lab, n = ndi.label(mask & (a >= 0) & (a != mortar))
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        bm = lab == i
        if (y1 - y0) < 4 or (x1 - x0) < 6:
            continue
        tex(a, bm, rng, share=0.2)
        if rng.random() < chip_p:
            c = ('nw', 'ne', 'sw', 'se')[int(rng.integers(0, 4))]
            cx = x0 if c[1] == 'w' else x1 - 1
            cy = y0 if c[0] == 'n' else y1 - 1
            if bm[cy, cx] or bm[min(y1 - 1, cy + (1 if c[0] == 'n' else -1)), cx]:
                chip(a, cx, cy, c, mortar)
                if rng.random() < crack_p / chip_p:
                    crack(a, cx + (2 if c[1] == 'w' else -2), cy + (2 if c[0] == 'n' else -3), rng,
                          0.5 * (x1 - x0), bm, dx=1 if c[1] == 'w' else -1)
        if moss_rows is not None and y1 >= moss_rows and rng.random() < moss_p:
            mx = int(rng.integers(x0, max(x0 + 1, x1 - 6)))
            moss_clump(a, mx, y1 - 1, int(rng.integers(3, 7)), mask)


def star_mask(shape, cx, cy, R, w, ry=1.0):
    """A four-pointed star: two rhombi crossed, w texels half-wide at the heart, tapering to a point
    R texels out (its arms grow thin, so a glow in it runs from a bright heart to deep tips)."""
    Y, X = np.mgrid[0:shape[0], 0:shape[1]] + 0.5
    dx, dy = np.abs(X - cx), np.abs(Y - cy) / ry
    return ((dx / R + dy / w) <= 1) | ((dx / w + dy / R) <= 1)


def sigil(a, cx, cy, r, lit, fam='stone', t=3):
    """The starfall sigil carved in stone: a ring and a four-pointed star, cut as grooves (8 Nov, SE-3);
    glowing while it holds."""
    V = _v()
    ring = V.ellipse_mask(a.shape, cx, cy, r, r * 0.86) & ~V.ellipse_mask(a.shape, cx, cy, r - 4, r * 0.86 - 4)
    star = star_mask(a.shape, cx, cy, r * 0.78, 4.2, ry=0.9)
    m = (ring | star) & (a >= 0)
    return carve(a, m, lit, fam, t)


def ashlar_courses(a, x0, y0, x1, y1, rng, course=7, length=(9, 15), mortar=None):
    """Dressed courses as the house recipe draws stone (8 Nov round 3, SE-4): courses `course` texels of
    parts 9 to 15 long, each part a sibling of stone or ashlar at tone 3, the odd one a tone off, square
    cut (no pillow corners), its top row lit and its foot and east end a tone down; one-texel mortar at
    stone_cool 1; clusters of two to four texels inside each part; a corner knocked to mortar only here
    and there. Returns the parts' mask."""
    V = _v()
    code = V.code
    mortar = code('stone_cool', 1) if mortar is None else mortar
    a[y0:y1, x0:x1] = mortar
    parts = np.zeros(a.shape, bool)
    fams = ('stone', 'stone_warm', 'stone_cool', 'ashlar', 'ashlar_warm')
    y, k = y0, 0
    while y < y1 - 2:
        yb_ = min(y1, y + course)
        x = x0 - (int(rng.integers(3, length[0])) if k % 2 else 0)
        while x < x1:
            L_ = int(rng.integers(length[0], length[1] + 1))
            bx0, bx1 = max(x0, x), min(x1, x + L_ - 1)
            if bx1 - bx0 >= 3:
                fam = fams[int(rng.integers(0, len(fams)))]
                t = int(rng.choice([3, 3, 3, 3, 2, 4]))
                a[y:yb_ - 1, bx0:bx1] = code(fam, t)
                a[y, bx0:bx1] = code(fam, min(4, t + 1))                     # its lit top
                a[yb_ - 2, bx0:bx1] = code(fam, max(1, t - 1))               # its foot
                a[y + 1:yb_ - 1, bx1 - 1] = code(fam, max(1, t - 1))          # its east end
                m = np.zeros(a.shape, bool)
                m[y + 1:yb_ - 2, bx0:bx1 - 1] = True
                tex(a, m, rng, share=0.4, down=0.08)
                parts[y:yb_ - 1, bx0:bx1] = True
                if rng.random() < 0.18:
                    c = ('nw', 'ne', 'sw', 'se')[int(rng.integers(0, 4))]
                    chip(a, bx0 if c[1] == 'w' else bx1 - 1, y if c[0] == 'n' else yb_ - 2, c, mortar)
            x += L_
        y = yb_
        k += 1
    return parts


def p_seal(w, h, height, sealed=True):
    """The sealed slab: a block of dressed stone plugging the passage, `height` world px tall, seen
    like every wall: its top (three slabs end to end, the middle one with the sigil carved in it,
    glowing while it holds, a lit arris at its south edge) and its south face (courses on a plinth
    with a dark foot). Round 5: calm slab tops with lit north-west and dark south-east lips, sibling
    clusters, chipped corners; no gloss, no specks."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(5)
    W, H = q(w) + 6, q(h) + q(height) + 6
    p = V.Pic(W, H, W // 2, H - 4)
    a = p.a
    x0, x1 = 3, W - 3
    ytop, yface, yb = 3, 3 + q(h), H - 3
    mortar = code('stone_cool', 1)
    a[ytop:yface, x0:x1] = mortar
    cuts = [ytop, ytop + (yface - ytop) // 3, ytop + 2 * (yface - ytop) // 3, yface]
    for k in range(3):
        fam = 'stone' if k == 1 else ('stone_warm' if k == 0 else 'stone_cool')
        if k == 1:
            slab_top(a, x0, cuts[k], x1, cuts[k + 1] - 1, fam, 3, rng, mortar, lip=2, chips=2, cracks=0)
        else:                                       # the end slabs broken into two stones each (SE-4)
            sx = x0 + (x1 - x0) * (0.42 if k == 0 else 0.6)
            slab_top(a, x0, cuts[k], int(sx), cuts[k + 1] - 1, fam, 3, rng, mortar, lip=2, chips=1, cracks=1)
            slab_top(a, int(sx) + 1, cuts[k], x1, cuts[k + 1] - 1, 'ashlar' if k == 0 else 'stone', 3, rng, mortar,
                     lip=2, chips=1, cracks=0)
    tops = (a >= 0) & (a != mortar) & (a % 8 <= 5)
    tops[cuts[3]:] = False
    patches(a, tops, rng, sigma=1.5, sib_share=0.3, down=0.1)      # two or three soft blotches a tone apart
    sigil(a, (x0 + x1) / 2, (cuts[1] + cuts[2]) / 2, q(5.5), sealed, 'stone', 3)
    # the south arris: lit, broken where it is chipped
    V.fill(a, x0, yface - 2, x1, yface - 1, code('stone', 4))
    for k in range(x0 + 4, x1 - 4, 11):
        a[yface - 2, k:k + 2] = code('stone', 2)
    ashlar_courses(a, x0, yface + 1, x1, yb - q(5), rng)
    # the plinth course: taller parts, a lit top arris, a dark foot
    ashlar_courses(a, x0, yb - q(5), x1, yb, rng, course=q(5), length=(14, 22))
    V.fill(a, x0, yface, x1, yface + 1, code('stone_cool', 1))                  # the shadow under the top's arris
    V.fill(a, x0, yb - 1, x1, yb, code('stone_cool', 1))
    V.fill(a, x1 - 1, yface, x1, yb, code('stone_cool', 2))
    for k in range(2):                                                           # moss in the lowest joints only
        moss_clump(a, int(rng.integers(x0 + 2, x1 - 9)), yb - q(5) - 1, int(rng.integers(3, 7)))
    V.finish(p)
    return p


def p_seal_sunk(w, h):
    """The slab sunk flush with the floor: its three slabs' tops only, the sigil gone dark."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(23)
    W, H = q(w) + 4, q(h) + 4
    p = V.Pic(W, H, W // 2, H - 2)
    a = p.a
    mortar = code('stone_cool', 0)
    a[2:H - 2, 2:W - 2] = mortar
    cuts = [2 + k * (H - 4) // 3 for k in range(4)]
    for k in range(3):
        fam = 'stone' if k == 1 else ('stone_warm' if k == 0 else 'stone_cool')
        slab_top(a, 2, cuts[k], W - 2, cuts[k + 1] - 1, fam, 3, rng, mortar, lip=2, chips=2, cracks=1 if k != 1 else 0)
    # sunk to the floor, it has taken the floor's damp: worn hollows a tone down, a cool sibling in
    # patches, a hairline crack or two
    tops = (a >= 0) & (a != mortar) & (a % 8 <= 5)
    patches(a, tops, rng, sigma=1.5, sib_share=0.3, down=0.12)
    tex(a, tops, rng, share=0.35, down=0.1)
    for (cx_, cy_) in ((W * 0.7, cuts[0] + 8), (W * 0.25, cuts[2] + 14)):
        crack(a, int(cx_), int(cy_), rng, 12, tops)
    sigil(a, W / 2, (cuts[1] + cuts[2]) / 2, q(5.5), False, 'stone', 3)
    for k in (0, 2):                                    # damp in the sunk slab's low joints
        moss_clump(a, int(rng.integers(6, W - 14)), cuts[k + 1] - 1, int(rng.integers(3, 6)))
    return V.finish(p)


def p_plate(w, h, pressed):
    """The pressure plate: a square slab set in a frame of narrow stones, the starfall star carved in
    it (8 Nov, P-1 to P-3). Raised two world px it shows its top and its front, and throws a shadow on
    the frame's south and east stones; pressed, it sits in the frame with the north stones' shadow
    across its edge, and the star holds the shard's light (a glow ramp from deep violet tips to a
    near-white heart)."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(13)
    up = 0 if pressed else 2
    W, H = q(w + 4) + 6, q(h + 4 + up) + 6
    p = V.Pic(W, H, W // 2, H - 3)
    a = p.a
    x0, y0, x1, y1 = 3, 3 + q(up), W - 3, H - 3
    fw = q(2)
    mortar = code('stone_cool', 0)
    a[y0:y1, x0:x1] = mortar
    # the frame: narrow stones, two to a side, each its own slab with lips, chips and clusters
    sx = int(rng.integers(x0 + 16, x1 - 16))
    sy = int(rng.integers(y0 + 16, y1 - 16))
    pieces = [(x0, y0, sx, y0 + fw), (sx + 1, y0, x1, y0 + fw), (x0, y1 - fw, sx + 6, y1), (sx + 7, y1 - fw, x1, y1),
              (x0, y0 + fw + 1, x0 + fw, sy), (x0, sy + 1, x0 + fw, y1 - fw - 1),
              (x1 - fw, y0 + fw + 1, x1, sy - 5), (x1 - fw, sy - 4, x1, y1 - fw - 1)]
    for k, (a0, b0, a1, b1) in enumerate(pieces):
        fam = ('stone_cool', 'stone', 'stone_cool', 'stone_warm')[k % 4]
        slab_top(a, a0, b0, a1, b1 - 1 if b1 < y1 else b1, fam, 3, rng, mortar, lip=1, chips=1 + (k % 2),
                 cracks=1 if k in (1, 4) else 0, texture=0.18)
    ix0, iy0, ix1, iy1 = x0 + fw + 1, y0 + fw + 1, x1 - fw - 1, y1 - fw - 1
    a[iy0 - 1:iy1 + 1, ix0 - 1:ix1 + 1] = code('soot', 1)                    # the gap round the slab
    if pressed:
        top = slab_top(a, ix0, iy0, ix1, iy1, 'stone_warm', 3, rng, mortar, lip=2, chips=2, cracks=1)
        # the frame's north and west stones throw their shadow across the sunk slab's edge
        a[iy0:iy0 + 3, ix0:ix1][top[iy0:iy0 + 3, ix0:ix1]] = code('stone_warm', 1)
        a[iy0:iy1, ix0:ix0 + 2][top[iy0:iy1, ix0:ix0 + 2]] = code('stone_warm', 1)
        a[iy0, ix0:ix1] = code('stone_warm', 0)
        cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2 + 1
    else:
        lift = q(up)
        ty0, ty1 = iy0 - lift, iy1 - lift
        top = slab_top(a, ix0, ty0, ix1, ty1, 'stone_warm', 3, rng, mortar, lip=2, chips=2, cracks=1)
        # its front face: a lit arris, the face, its foot in shade, its east end a tone down
        a[ty1:iy1 + 1, ix0:ix1] = code('stone_warm', 2)
        a[ty1, ix0 + 1:ix1 - 1] = code('stone_warm', 4)
        a[iy1, ix0:ix1] = code('stone_warm', 1)
        a[ty1 + 1:iy1 + 1, ix1 - 3:ix1] = code('stone_warm', 1)
        for k in range(ix0 + 5, ix1 - 6, 13):                               # tool marks on the dressed front
            a[ty1 + 2:ty1 + 4, k:k + 2] = code('stone', 2)
        # its shadow on the frame: the south stones' top rows and the east stones' west columns sink
        sh = np.zeros(a.shape, bool)
        sh[iy1 + 1:iy1 + 3, ix0 + 3:ix1 + 2] = True
        sh[ty0 + 3:iy1 + 3, ix1 + 1:ix1 + 3] = True
        sh &= (a >= 0) & (a != mortar) & (a % 8 <= 5) & (a // 8 != V.FI['soot'])
        a[sh] = a[sh] // 8 * 8 + np.maximum(0, a[sh] % 8 - 2)
        cx, cy = (ix0 + ix1) / 2, (ty0 + ty1) / 2
    star = star_mask(a.shape, cx, cy, q(5.2), 4.4, ry=0.92) & top
    carve(a, star, pressed, 'stone_warm', 3)
    if not pressed:                                                          # a pit at the star's heart, its drain
        a[int(cy) - 1:int(cy) + 1, int(cx) - 1:int(cx) + 1] = code('stone_warm', 0)
    # moss only in the low joints: the south frame's joint and the slab's south-west gap
    moss_clump(a, sx + 2, y1 - fw - 1, 4)
    moss_clump(a, x0 + 1, y1 - fw - 1, 3)
    return V.finish(p)


def grip(a, x0, y0, x1, y1, r, fam='timber'):
    """A turned wooden grip from (x0, y0) to (x1, y1), r texels in radius: round in section, its
    highlight band on the side towards the light (left of centre), the far side dark, an end cap
    (an ellipse, lit if it faces up) at (x1, y1) and an iron ferrule at (x0, y0) (8 Nov, L-1)."""
    V = _v()
    code = V.code
    H, W = a.shape
    Y, X = np.mgrid[0:H, 0:W] + 0.5
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    if nx * -0.6 + ny * -0.8 < 0:                                           # the normal points to the light
        nx, ny = -nx, -ny
    s = (X - x0) * ux + (Y - y0) * uy
    v = -((X - x0) * nx + (Y - y0) * ny) / r                                # -1 on the lit side
    m = (s >= 0) & (s <= L) & (np.abs(v) <= 1)
    tt = np.full((H, W), 3)
    tt[v < -0.2] = 4
    tt[(v > -0.62) & (v < -0.3)] = 5
    tt[v < -0.75] = 3
    tt[v > 0.3] = 2
    tt[v > 0.72] = 1
    a[m] = (V.FI[fam] * 8 + tt)[m]
    grain = m & (np.abs(v - 0.12) < 0.14) & ((s // 3) % 3 != 0) & (s > 3)
    a[grain] = code(fam + '_cool' if fam + '_cool' in V.FI else fam, 2)
    fer = m & (s < 2.6)
    ft = np.where(v < -0.3, 4, np.where(v > 0.45, 1, 2))
    a[fer] = (V.FI['brass'] * 8 + ft)[fer]
    cap = ((X - x1) * ux + (Y - y1) * uy) ** 2 / 1.6 ** 2 + ((X - x1) * nx + (Y - y1) * ny) ** 2 / r ** 2 <= 1
    cap &= ((X - x1) * ux + (Y - y1) * uy) > -0.6
    lit_cap = uy < -0.3
    a[cap] = code(fam, 4 if lit_cap else 2)
    rim = cap & ~ndi.binary_erosion(cap)
    a[rim & (((X - x1) * nx + (Y - y1) * ny) > 0)] = code(fam, 2 if lit_cap else 1)
    return m | cap


def p_lever(pulled):
    """The lever: a dressed stone post (its top, a lit arris, its front; a carved slot in its top), an
    iron pivot plate bolted to its face, an iron rod through the slot and a turned wooden grip with an
    iron ferrule; pulled, the rod lies down to the east. Round 5 (8 Nov, L-1 to L-3): the plate has a
    sheen and lit-head rivets, the grip is turned, the post is aged by chips and clusters, not specks."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(11)
    W, H = q(18), q(24)
    p = V.Pic(W, H, W // 2, H - 3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(4), cx + q(4)
    yt, yf = yb - q(12), yb - q(12) + q(3.5)
    mortar = code('stone_cool', 0)
    slab_top(a, x0, yt, x1, yf, 'stone', 4, rng, mortar, lip=2, chips=1, cracks=0, texture=0.16)
    a[yf:yb, x0:x1] = code('stone', 3)                                       # the front face
    a[yf, x0 + 1:x1 - 1] = code('stone', 5)                                  # its lit arris
    a[yf + 1, x0:x1] = code('stone', 4)
    a[yf + 1:yb, x0:x0 + 2] = code('stone', 4)                               # the west edge turns to the light
    a[yf + 2:yb, x1 - 4:x1] = code('stone', 2)                               # the east end in shade
    a[yb - 2:yb, x0:x1] = code('stone', 1)                                   # its foot
    for k in range(x0 + 6, x1 - 4, 9):
        a[yf, k:k + 2] = code('stone', 3)                                    # the arris worn here and there
    face = np.zeros(a.shape, bool)
    face[yf + 2:yb - 2, x0 + 2:x1 - 4] = True
    patches(a, face, rng, sigma=1.8, sib_share=0.18)
    tex(a, face, rng, share=0.4)
    for k in range(x0 + 4, x1 - 6, 4):                                       # the mason's dressing: short tool strokes
        yy = int(rng.integers(yf + 4, yb - 8))
        a[yy:yy + 3, k] = code('stone_cool', 3)
    chip(a, x0, yb - 1, 'sw', mortar)
    chip(a, x1 - 1, yf + 2, 'ne', mortar)
    crack(a, x1 - 3, yf + 4, rng, 9, face | (np.roll(face, 2, 1)), dx=-1)
    moss_clump(a, x0, yb - 1, 5)
    # the slot in the top, its south lip lit
    V.fill(a, cx - q(0.8), yt + 2, cx + q(0.8), yt + q(1.8), code('soot', 0))
    V.fill(a, cx - q(0.8), yt + q(1.8), cx + q(0.8), yt + q(1.8) + 1, code('stone', 5))
    # the pivot plate: a sheen lighter to the upper left, a lit top edge, a dark lower edge
    px0, py0, px1, py1 = cx - q(2.4), yb - q(8), cx + q(2.4), yb - q(3.6)
    Y, X = np.mgrid[0:H, 0:W]
    pl = (X >= px0) & (X < px1) & (Y >= py0) & (Y < py1)
    dg = (X - px0) / (px1 - px0) + (Y - py0) / (py1 - py0)
    a[pl] = np.where(dg[pl] < 0.55, code('iron', 3), np.where(dg[pl] < 1.25, code('iron', 2), code('iron', 1)))
    a[pl & (Y == py0)] = code('iron', 4)
    a[pl & (X == px0) & (Y > py0)] = code('iron', 4)
    a[pl & (Y == py1 - 1)] = code('iron', 1)
    a[pl & (X == px1 - 1) & (Y > py0)] = code('iron', 1)
    a[(Y == py1) & (X >= px0 + 1) & (X <= px1)] = code('stone', 1)           # its shadow on the post
    a[(X == px1) & (Y > py0) & (Y <= py1)] = code('stone', 1)
    for rx in (px0 + 2, px1 - 4):
        for ry in (py0 + 2, py1 - 4):
            a[ry, rx:rx + 2] = code('iron', 5)                               # a rivet: its lit head
            a[ry + 1, rx:rx + 2] = code('iron', 0)                           # over its dark side
    # the rod and the grip
    pv = (cx, yb - q(10.4))
    end = (cx + q(7), yb - q(6.5)) if pulled else (cx - q(2.6), yb - q(19))
    dx, dy = end[0] - pv[0], end[1] - pv[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    rod_end = (end[0] - ux * q(2.2), end[1] - uy * q(2.2))
    V.bar(a, pv[0], pv[1], rod_end[0], rod_end[1], q(0.62), 'iron', 3)
    grip(a, rod_end[0], rod_end[1], end[0] + ux * q(1.6), end[1] + uy * q(1.6), q(0.95))
    a[int(pv[1]) - 1:int(pv[1]) + 2, int(pv[0]) - 1:int(pv[0]) + 2] = code('iron', 1)   # the pivot pin
    a[int(pv[1]) - 1, int(pv[0]) - 1] = code('iron', 4)
    return V.finish(p)


CH_HALF = 7          # texels from the groove's middle to its north (west) lip; to its south (east) lip, CH_HALF - 1


def channel_segments(pz):
    """The channel's straight runs as (x0, y0, x1, y1) in texels: the main run from the plate to the seal
    and its branch up to the lever (8 Nov, round 2 logic 1), each along x or y."""
    V = _v()
    q = V.q
    segs = []
    for key in ('channel', 'channel_branch'):
        pts = pz.get(key) or []
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            segs.append((q(min(ax, bx)), q(min(ay, by)), q(max(ax, bx)), q(max(ay, by))))
    return segs


def channel_field(shape, segs, ox=0, oy=0):
    """Per texel: the signed offset d across the nearest run (negative to the north or west, the side whose
    inner wall is in shade), the distance along it, and whether it lies on the main run. Off the
    channel d is a large number. At the T the branch opens through the main run's north wall, so the
    two grooves meet (round 3 logic 1)."""
    H, W = shape
    Y, X = np.mgrid[0:H, 0:W]
    X, Y = X + ox, Y + oy
    d = np.full((H, W), 99, int)
    along = np.zeros((H, W), int)
    main = np.zeros((H, W), bool)
    fields = []
    for (x0, y0, x1, y1) in segs:
        if y0 == y1:
            m = (X >= x0 - CH_HALF) & (X <= x1) & (np.abs(Y - y0) <= CH_HALF + 2)
            fields.append((m, Y - y0, X - x0))
        else:
            m = (Y >= y0) & (Y <= y1 + CH_HALF) & (np.abs(X - x0) <= CH_HALF + 2)
            fields.append((m, X - x0, y1 - Y))
    for m, dd, aa in reversed(fields[1:]):                            # the branches
        d[m], along[m] = dd[m], aa[m]
    m0, d0, a0 = fields[0]                                            # the main run wins, except ...
    d[m0], along[m0], main[m0] = d0[m0], a0[m0], True
    for m, dd, aa in fields[1:]:                                       # ... where a branch opens into it
        jn = m & m0 & (np.abs(dd) <= 3) & (d0 < -2)
        d[jn], along[jn], main[jn] = dd[jn], aa[jn], False
    return d, along, main


def carve_channel(cv, segs, rng):
    """The groove the plate's charge runs in, unlit (8 Nov, G-8): cut into the floor, not a strip laid on it.
    Across it from the shaded side: the floor's broken edge, the inner wall in shade (streaked where water
    ran down it), the wet floor of the groove (a broken sheen), the brass inlay showing only as a one-texel
    lit inner lip, tarnished green and brown in clusters, grimed in drifts and broken where a divider sits,
    the far inner wall catching the light, and the lit lip. Returns the mask the floor painter must leave."""
    V = _v()
    code = V.code
    H, W = cv.shape
    d, along, main = channel_field(cv.shape, segs)
    on = np.abs(d) <= CH_HALF
    on &= d <= CH_HALF - 1
    grime = ndi.gaussian_filter(rng.random((H, W)), 4.0)
    grime = (grime - grime.mean()) / (grime.std() + 1e-9)
    tarn = ndi.gaussian_filter(rng.random((H, W)), 1.2)
    tarn = (tarn - tarn.mean()) / (tarn.std() + 1e-9)
    # streaks down the shaded wall at uneven spacings (6 to 15 texels, round 4 G-18), not a comb
    marks = np.cumsum(np.random.default_rng(45).integers(6, 16, 200))
    streak = np.isin(along, marks) | np.isin(along, marks + 1) * (np.random.default_rng(46).random((H, W)) < 0.5)
    prof = {-7: code('stone_cool', 1), -6: code('stone_cool', 0), -5: code('stone_cool', 1), -4: code('stone_cool', 1),
            -3: code('stone_cool', 1), -2: code('void', 2), -1: code('void', 2), 0: code('void', 2), 1: code('void', 2),
            2: code('brass', 3), 3: code('stone', 2), 4: code('stone', 3), 5: code('stone_cool', 2), 6: code('stone_cool', 1)}
    for dd, c in prof.items():
        cv[on & (d == dd)] = c
    cv[on & (d >= -5) & (d <= -3) & streak] = code('stone_cool', 0)                 # streaks down the shaded wall
    sheen = on & (d == -1) & ((along // 5 + (along // 13)) % 3 == 0)
    cv[sheen] = code('slate_cool', 2)                                                # the wet floor's sheen, broken
    cv[on & (d == 0) & (grime > 0.9)] = code('void', 1)
    wet = on & (d >= -2) & (d <= 1) & (grime < -1.1)                                 # a wet patch or two on its floor
    cv[wet] = code('slate_cool', 1)
    cv[on & (d >= -5) & (d <= -4) & (tarn > 1.3)] = code('stone_cool', 2)          # damp catching a glint on the wall
    lip = on & (d == 2)
    cv[lip & (tarn > 0.8)] = code('leaf_cool', 2)                                    # verdigris on the brass
    cv[lip & (tarn < -0.9)] = code('earth_cool', 2)                                  # and brown tarnish
    cv[lip & (grime > 0.7)] = code('brass', 1)                                       # grime in drifts
    for k in range(V.q(8), int(along.max()) + 1, V.q(8)):                           # breaks where the dividers sit
        br = on & (np.abs(d) <= 2) & (along >= k) & (along < k + 2)
        cv[br] = code('brass', 1)
        cv[br & (d == -2)] = code('brass', 2)
    # the lit lip is chipped and worn in places, never one ruled stroke
    k = 0
    crng = np.random.default_rng(41)
    nx = int(along.max())
    while k < nx:
        L_ = int(crng.integers(3, 8))
        cv[on & (d == 4) & (along >= k) & (along < k + L_)] = code('stone', 2)
        cv[on & (d == 5) & (along >= k + 1) & (along < k + L_ + 2)] = code('stone_cool', 1)
        k += L_ + int(crng.integers(10, 22))
    return on | (np.abs(d) <= CH_HALF + 1)


def p_channel(pz, lit=True):
    """The channel once the plate is down (8 Nov round 4, C-3): a lit groove seen from three-quarter view,
    not a tube. The far (north, or west) inner wall takes the shard's light in two or three violet tones;
    the groove's floor is the core, near-white, swelling near the plate and at the T and thinning towards
    the ends; the near inner wall stays hidden under the lip, which keeps its stone with only its inner
    edge a rung up in violet. Every band runs in uneven lengths. The spill lies on the floor right against
    the groove beyond its lit far wall, a 2 x 2 checker of the floor's cool sibling a rung up, fading over four
    rows, each piece standing on the row nearer the groove. The brass
    dividers stand dark in it. The picture's foot is the plate's end of the main run."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(17)
    segs = channel_segments(pz)
    m_ = CH_HALF + 3
    X0 = min(s[0] for s in segs) - m_
    Y0 = min(s[1] for s in segs) - m_
    X1 = max(s[2] for s in segs) + m_
    Y1 = max(s[3] for s in segs) + m_
    W, H = X1 - X0, Y1 - Y0
    fx, fy = q(pz['channel'][0][0]), q(pz['channel'][0][1])
    p = V.Pic(W, H, fx - X0, fy - Y0)
    a = p.a
    d, along, main = channel_field(a.shape, segs, X0, Y0)
    Yg, Xg = np.mgrid[0:H, 0:W]
    span = max(1, int(along[np.abs(d) <= CH_HALF].max()))
    u = along / span
    # where the branch leaves the main run (the T), measured along the main run
    tx = None
    if len(segs) > 1:
        tx = segs[1][0] - segs[0][0]
    near_t = main & (np.abs(along - (tx if tx is not None else -999)) < q(4))
    swell = (u < 0.12) | near_t                                    # the charge is strongest at the plate and the T

    def broken(mask, t_hi, t_lo, fam, lmin=3, lmax=12):
        """A band in uneven lengths: runs of t_hi broken by shorter runs of t_lo."""
        a[mask] = code(fam, t_hi)
        x = int(rng.integers(0, 5))
        while x < span + 2:
            L_ = int(rng.integers(lmin, lmax))
            x += L_
            g = int(rng.integers(2, 5))
            a[mask & (along >= x) & (along < x + g)] = code(fam, t_lo)
            x += g

    groove = np.abs(d) <= CH_HALF
    # the far inner wall, lit in two or three tones (its top in shade, brighter towards the floor)
    broken(groove & (d == -6), 1, 2, 'dusk')
    broken(groove & (d == -5), 2, 3, 'dusk')
    broken(groove & (d == -4), 3, 2, 'dusk')
    broken(groove & (d == -3), 4, 3, 'dusk')
    # the floor of the groove: the core
    fl = groove & (d >= -2) & (d <= 1)
    broken(fl & ((d == -2) | (d == 1)), 4, 5, 'dusk', 4, 14)
    broken(fl & ((d == -1) | (d == 0)), 5, 4, 'dusk', 5, 16)
    core = fl & (d == 0) & (u < 0.92)
    x = 0
    while x < span:
        L_ = int(rng.integers(4, 15))
        a[core & (along >= x) & (along < x + L_)] = code('snow', 4)
        x += L_ + int(rng.integers(1, 4))
    a[fl & swell & ((d == -1) | (d == 0))] = code('snow', 4)
    a[fl & swell & (d == -1) & (u < 0.06)] = code('snow', 5)
    a[fl & (u > 0.8) & (d != 0)] = code('dusk', 3)               # it thins towards the far ends
    # the near wall under the lip: only the lip's inner edge, a rung up in violet, broken
    broken(groove & (d == 2), 3, 2, 'dusk_cool', 4, 10)
    # the spill on the floor against the groove: a 2 x 2 checker a rung up, fading over four rows
    # (each row's pieces stand on the row nearer the groove, so the light reads as one spill, not loose dots)
    chk = ((Xg // 2 + Yg // 2) % 2) == 0
    prev = groove & (a >= 0)
    for k, dens in enumerate((0.9, 0.6, 0.35, 0.18)):
        rowsN = d == -(CH_HALF + k)                    # the floor beyond the lit far wall (the near side is the lip)
        thin = np.random.default_rng(60 + k).random((H, W)) < dens
        touch = ndi.binary_dilation(prev, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool))
        sp = rowsN & chk & thin & touch & (u < 0.95) & (a < 0)
        a[sp] = code('slate_cool', 2)
        prev = sp
    # the brass dividers stand dark in the glow, lit on top, their east side in shade
    for k in range(q(8), span, q(8)):
        dv = groove & (d >= -2) & (d <= 2) & (along >= k) & (along < k + 2)
        a[dv] = code('brass', 2)
        a[dv & (d == -2)] = code('brass', 4)
        a[dv & (along == k + 1)] = code('brass', 1)
    return p


def p_cairn_alcove(seed):
    """Cairn asleep in the wall (8 Nov, CA-1 to CA-5): his slumped drawing (the cast's last defeat
    frame) brought onto the house ramps, its stones re-lit by the rock recipe (a lit crown to the
    upper left, the body, a dark underside, cluster texture), the moss taken off his shoulders and
    left only in the creases between his stones, a sprout growing from one; the loose pebbles of the
    cast frame dropped. He is half sunk behind squared courses (chipped corners, lit top edges) and a
    bank of damp earth with moss in it (no grass: no daylight reaches the alcove). The canvas is
    the scene's (108 x 100 at density 3, foot at its bottom centre)."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native import palette as PAL
    rng = np.random.default_rng(seed)
    src = np.asarray(Image.open(CAIRN).convert('RGBA'))[:, -160:]
    ys, xs = np.nonzero(src[..., 3] > 0)
    src = src[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # the cast frame's loose pebbles (they float over him) are dropped: keep his body only
    lab, n = ndi.label(src[..., 3] > 0)
    if n > 1:
        sizes = ndi.sum(np.ones(lab.shape), lab, index=np.arange(1, n + 1))
        keep = 1 + int(np.argmax(sizes))
        src = src * (lab == keep)[..., None]
        ys, xs = np.nonzero(src[..., 3] > 0)
        src = src[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = src.shape[:2]
    scale = ctx.D / 3.0
    sh, sw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    if (sh, sw) != (h, w):
        src = np.asarray(Image.fromarray(src, 'RGBA').resize((sw, sh), Image.NEAREST))
    W, H = int(round(108 * scale)), int(round(100 * scale))
    p = V.Pic(W, H, W // 2, H - 1)
    a = p.a
    ox, oy = (W - sw) // 2, H - sh
    rgb = src[..., :3].astype(int)
    al = src[..., 3] > 0
    r_, g_, b_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    L = (r_ + g_ + b_) / 3
    eye = al & (r_ > g_ + 40) & (b_ < g_)
    moss = al & (g_ > r_ + 15) & (g_ > b_ + 5) & ~eye
    line = al & (L < 70) & ~eye & ~moss
    stone = al & ~eye & ~moss & ~line
    body = np.zeros(a.shape, bool)
    body[oy:oy + sh, ox:ox + sw] = al
    sub = lambda m: np.pad(m, ((oy, H - oy - sh), (ox, W - ox - sw)))
    stone_m, line_m, eye_m, moss_m = sub(stone), sub(line), sub(eye), sub(moss)
    # the cast frame's sprout is thin: an opening of his silhouette drops it with the moss (one is grown below)
    thin = body & ~ndi.binary_opening(body, structure=np.ones((4, 4), bool))
    drop = thin & (moss_m | line_m)
    drop = ndi.binary_dilation(drop, iterations=1) & (moss_m | line_m) & thin
    for m_ in (stone_m, line_m, moss_m):
        m_ &= ~drop
    body &= ~drop
    lab2, n2 = ndi.label(body)
    if n2 > 1:
        big = 1 + int(np.argmax(ndi.sum(np.ones(lab2.shape), lab2, index=np.arange(1, n2 + 1))))
        for m_ in (stone_m, line_m, moss_m, eye_m, body):
            m_ &= lab2 == big
    a[line_m] = code('stone_cool', 0)
    a[eye_m] = code('lamp', 2)
    # the moss hats go: their texels become stone, lit as the crown of the stone under them
    stone_m |= moss_m
    # each stone of him, found between the drawn lines, lit by the rock recipe
    labs, nst = ndi.label(stone_m)
    Y, X = np.mgrid[0:H, 0:W]
    for i, sl in enumerate(ndi.find_objects(labs), start=1):
        if sl is None:
            continue
        m = labs == i
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        fam = ('stone', 'stone_warm', 'stone_cool')[i % 3]
        # a pillow: flat in the middle, its rim turning to the light at the upper left and away at the lower right
        dist = ndi.distance_transform_edt(m)
        bm = ndi.gaussian_filter(m.astype(float), 3.0)
        gy, gx = np.gradient(bm)
        nrm = np.hypot(gx, gy) + 1e-6
        lit = -(gx * -0.6 + gy * -0.8) / nrm                            # +1: the rim faces the light
        rimw = np.clip(1.2 - dist / 6.0, 0, 1)                          # the rim, about six texels in
        shd = lit * rimw
        uu = (X - x0) / max(1, x1 - x0) + (Y - y0) / max(1, y1 - y0)
        tt = np.full((H, W), 3)
        tt[(shd < -0.18) | (uu > 1.55)] = 2
        tt[shd < -0.5] = 1
        tt[(shd > 0.2) | (uu < 0.45)] = 4
        tt[(shd > 0.55) & (uu < 1.0)] = 5
        tt = np.maximum(1, tt - 1)                                        # a step into the alcove's shade (CA-7)
        a[m] = (V.FI[fam] * 8 + tt)[m]
        bot = m & ~np.roll(m, -1, 0)
        a[bot] = code(fam, 1)
        a[m & np.roll(bot, -1, 0) & ~bot] = code(fam, 2)               # the underside turning away
        if m.sum() > 20:
            tex(a, m & ~bot, rng, share=0.3, up=0.0)
    # moss only in the creases: clumps sitting in the lower joints between his stones
    crease = line_m & np.roll(stone_m, -1, 0) & np.roll(stone_m, 1, 0) & (Y > oy + sh * 0.35)
    cy_, cx_ = np.nonzero(crease)
    order = rng.permutation(len(cy_))[:4]
    for k in order:
        moss_clump(a, int(cx_[k]) - 1, int(cy_[k]), int(rng.integers(3, 5)), mask=body)
    # a sprout from the crease at his east shoulder
    top_rows = np.nonzero(body.any(1))[0]
    sx = ox + int(sw * 0.72)
    col = np.nonzero(body[:, sx])[0]
    if len(col):
        sy = int(col.min()) + 2
        moss_clump(a, sx - 2, sy, 4, mask=body)
        for k in range(1, 5):
            a[sy - 2 - k, sx] = code('leaf_cool', 2)
        a[sy - 7, sx - 2:sx] = code('leaf', 4)
        a[sy - 8, sx - 3:sx - 1] = code('leaf', 3)
        a[sy - 7, sx + 1:sx + 3] = code('leaf_cool', 3)
        a[sy - 8, sx + 2:sx + 4] = code('leaf_cool', 2)
    # half sunk: squared courses and a bank of earth over his lower third
    cover = int(sh * 0.36)
    yb = H - 1
    m = np.zeros(a.shape, bool)
    m[yb - cover:yb + 1, :] = True
    # the bank's lip (round 4, CA-8): a slow swell, and a step of a texel up or down every 4 to 8 texels
    lip = np.zeros(W)
    xk, v = 0, 0
    lrng = np.random.default_rng(seed + 31)
    while xk < W:
        L_ = int(lrng.integers(4, 9))
        v = int(np.clip(v + lrng.choice([-1, 1]), -2, 2))
        lip[xk:xk + L_] = v
        xk += L_
    crest_y = (yb - cover + np.sin(np.arange(W) / q(3)) * q(0.8) + lip).astype(int)
    m &= Y >= crest_y[None, :]
    m &= np.abs(X + 0.5 - W / 2) <= q(14) + 1                          # inside the alcove's jambs only
    bank = m & ~np.roll(m, q(2.5), 0)
    wall = m & ~bank
    wy0 = int(np.nonzero(wall.any(1))[0].min())
    masonry(a, 0, wy0, W, yb + 1, rng, wall, base=2, course=4.0, length=(6, 10), east_dark=True)
    age_courses(a, wall, rng, code('stone_cool', 0), moss_rows=yb - q(4), chip_p=0.6, crack_p=0.15, moss_p=0.35)
    # the bank (8 Nov round 4, CA-8): earth heaped in clods, not rows. Dark earth between them, clods of
    # three to six texels on the earth ramps, each with a lit pair at its upper left and a dark pixel at its
    # foot, laid back to front; pebbles in two drifts; moss in two or three clumps where it meets his stones
    a[bank] = code('earth_cool', 1)
    crest = bank & ~np.roll(bank, 1, 0)
    a[crest] = code('earth', 2)
    crng = np.random.default_rng(seed + 37)
    ys_, xs_ = np.nonzero(bank)
    clods = []
    for _ in range(int(bank.sum() / 9)):
        k = int(crng.integers(0, len(ys_)))
        clods.append((int(ys_[k]), int(xs_[k]), crng.uniform(1.5, 3.0), crng.uniform(1.0, 1.8),
                      ('earth', 'earth_warm', 'earth_cool')[int(crng.integers(0, 3))], int(crng.choice([2, 2, 3]))))
    for cy, cx, rx, ry, fam, t in sorted(clods):
        c = V.ellipse_mask(a.shape, cx + 0.5, cy + 0.5, rx, ry) & bank
        if not c.any():
            continue
        a[c] = code(fam, t)
        cys, cxs = np.nonzero(c)
        top = c & (Y <= cys.min()) & (X <= cxs.min() + 1)
        a[c & (Y == cys.min()) & (X < cxs.min() + 2)] = code(fam, min(4, t + 1))     # its lit pair
        a[c & (Y == cys.max()) & (X >= cxs.max() - 1)] = code(fam, 1)                # its foot in shade
    a[bank & ~np.roll(bank, -1, 0)] = code('earth_cool', 0)              # its foot on the courses
    for dx0 in (-0.45, 0.3):                                             # pebbles in two drifts
        for _ in range(3):
            px_ = int(W / 2 + dx0 * q(28) + crng.integers(-q(2), q(2)))
            col = np.nonzero(bank[:, min(W - 4, max(0, px_))])[0]
            if len(col) < 3:
                continue
            py_ = int(crng.integers(col.min() + 1, col.max()))
            ww = int(crng.integers(3, 5))
            for xx in range(ww):
                if 0 <= px_ + xx < W and bank[py_, px_ + xx]:
                    a[py_, px_ + xx] = code('stone', 3 if xx < ww - 1 else 2)
            if bank[py_ - 1, px_]:
                a[py_ - 1, px_:px_ + 2] = code('stone', 4)
            a[py_ + 1, px_ + 1:px_ + ww] = np.where(bank[py_ + 1, px_ + 1:px_ + ww], code('stone_cool', 1), a[py_ + 1, px_ + 1:px_ + ww])
    meet = crest & np.roll(body, -2, 0)                                 # where the bank meets his stones
    xs_m = np.nonzero(meet.any(0))[0]
    for w_ in (3, 6, 4)[:3 if len(xs_m) > 30 else 2]:
        if not len(xs_m):
            break
        x_ = int(xs_m[int(crng.integers(0, len(xs_m)))])
        col = np.nonzero(crest[:, x_])[0]
        if len(col):
            moss_clump(a, x_, int(col[0]), w_)
    return V.finish(p)


def _sprite_pic(img, W, H, ay):
    """A raster-kit sprite as a code Pic (house colours only; ink becomes the soot edge)."""
    V = _v()
    from .palette import code_of, FI
    p = V.Pic(W, H, W // 2, ay)
    arr = np.asarray(img)
    for y, x in zip(*np.nonzero(arr[..., 3] > 0)):
        e = code_of(arr[y, x, :3])
        if e == 'ink':
            p.a[y, x] = FI['soot'] * 8
        elif e is not None:
            p.a[y, x] = FI[e[0]] * 8 + int(e[1])
    return p


PROPS = {'rubble': p_rubble, 'roots': p_roots, 'urn': p_urn, 'stump': p_stump, 'shard': p_shard}


# ------------------------------------------------------------------------------------------------
# the zone
# ------------------------------------------------------------------------------------------------
def build(plan: dict, out_dir: str, preview: str | None = None, fields: dict | None = None) -> dict:
    V = _v()
    from scripts.art.native.palette import FI, step, to_rgba
    q, code = V.q, V.code
    D = ctx.D
    bx, by, bw, bh = plan['box']
    W, H = q(bw), q(bh)
    rng = np.random.default_rng(plan.get('art', {}).get('seed', 31))
    YY, XX = np.mgrid[0:H, 0:W]
    WX, WY = (XX + 0.5) / D, (YY + 0.5) / D

    def rmask(r):
        x, y, w, h = r
        return (WX >= x) & (WX < x + w) & (WY >= y) & (WY < y + h)

    cv = np.full((H, W), -1, np.int32)
    cap = np.zeros((H, W), bool)
    face = np.zeros((H, W), bool)
    for wl in plan['walls']:
        x, y, w, h = wl['rect']
        f = wl.get('face', 0)
        cap |= rmask([x, y, w, h - f])
        if f:
            face |= rmask([x, y + h - f, w, f])
    stair = rmask(plan['stair']['rect']) if plan.get('stair') else np.zeros((H, W), bool)
    # the soft grid's corners: a wall end that sticks into a room is rounded (eastward-edges.md 1.5)
    rr = q(2.5)
    disk = (np.add.outer(np.arange(-rr, rr + 1) ** 2, np.arange(-rr, rr + 1) ** 2) <= rr * rr)
    cap = ndi.binary_opening(np.pad(cap, rr + 1, mode='edge'), structure=disk)[rr + 1:-rr - 1, rr + 1:-rr - 1] | (cap & face.any() & False)
    floor = ~cap & ~face & ~stair

    # --- the floor ---------------------------------------------------------------------------
    # round 4: the floor is laid out first (flags, joints, marks) and painted last, from the light, on
    # one short value ladder (FLOOR_LADDER): calm, dark, low in contrast, as Eastward's dungeon floors
    slab, fjoint, foff, fmat = floor_layout((H, W), floor, rng, q(4))
    nflags = int(slab.max())
    fvar = (rng.random(nflags + 1) < 0.35).astype(np.int8)[slab]          # the quiet variant, flag by flag
    # round 3 (8 Nov, G-10): flag to flag only a sibling swap at the same tone; no worn patches mottling
    # the flags (Eastward 06's floor holds about 4 L between its pieces)
    fvar[fjoint] = 0
    cv[floor] = code('stone_cool', 1)

    # --- the stair up to the hatch -----------------------------------------------------------
    if plan.get('stair'):
        sx, sy, sw, sh = plan['stair']['rect']
        n = 4
        for i in range(n):
            x0 = q(sx + sw * i / n)
            x1 = q(sx + sw * (i + 1) / n)
            t = 4 - i
            V.fill(cv, x0, q(sy), x1, q(sy + sh), code('stone_warm', t))
            V.fill(cv, x0, q(sy), x0 + 2, q(sy + sh), code('stone_warm', min(5, t + 1)))    # the lit nosing
            V.fill(cv, x1 - q(1), q(sy), x1, q(sy + sh), code('stone_warm', max(0, t - 2)))  # the riser in shade
            V.fill(cv, x0, q(sy + sh) - q(2), x1, q(sy + sh), code('stone_cool', max(0, t - 2)))

    # --- wall tops and faces -----------------------------------------------------------------
    wall_roots = np.zeros((H, W), bool)                 # the wall roots where they run onto the floor and dive in
    for wl in plan['walls']:
        x, y, w, h = wl['rect']
        f = wl.get('face', 0)
        if f:
            fm = rmask([x, y + h - f, w, f])
            wall_roots |= wall_face(cv, q(x), q(y + h - f), q(x + w), q(y + h), rng, fm, roots=[q(r) for r in wl.get('roots', [])],
                      arcade=w >= 40, alcove=q(wl['alcove']) if wl.get('alcove') else None)
        # the skylight is a crack in the vault above the frame: only its shaft of light shows (below)

    # the vault's tops, cut away as Eastward does: the dark beyond, then a band of coping stones (a lit
    # top plane, its lit rim towards the room, its far edge in shadow) round every room and passage
    dist, (iy, ix) = ndi.distance_transform_edt(cap, return_indices=True)
    band = cap & (dist <= q(4.5))
    vn = ndi.gaussian_filter(rng.random((H, W)), q(3))
    cv[cap] = np.where(vn[cap] > 0.68, code('void', 1), code('void', 0))
    dy, dx = iy - YY, ix - XX                       # towards the nearest room texel
    horiz = np.abs(dy) >= np.abs(dx)
    seg = np.where(horiz, XX // q(8), YY // q(8))
    jnt = band & np.where(horiz, XX % q(8) == 0, YY % q(8) == 0)
    fam_b = np.where(seg % 3 == 1, FI['stone_warm'], np.where(seg % 3 == 2, FI['stone_cool'], FI['stone']))
    tb = 1 + (seg * 7 % 5 == 0).astype(int)                         # block by block, a tone apart now and then
    tb = tb + 1                                                     # round 4: the coping's top is lit, over the faces
    cv[band] = fam_b[band] * 8 + tb[band]
    far = band & (dist > q(3.2) + (seg % 2))                         # the far edge, ragged, falls into the dark
    cv[far] = code('void', 1)
    rim = band & (dist <= 2)
    facing_e = rim & (dx > 0) & ~horiz                               # a rim facing east is in shade
    cv[rim] = fam_b[rim] * 8 + np.minimum(5, tb[rim] + 1 + (seg[rim] % 4 == 1))     # always a tone over its block
    cv[facing_e] = fam_b[facing_e] * 8 + 1
    # the coping's top is rounded: past its middle it turns away from the light, a tone down
    back = band & ~far & ~rim & ~jnt & (dist > q(2.6))
    cv[back] = fam_b[back] * 8 + np.maximum(0, tb[back] - 1)
    # its outer edge drops into the dark in a shadowed lip: the coping's thickness, a form shadow
    lip = band & ~far & ~jnt & (dist > q(3.2) + (seg % 2) - 2)
    cv[lip] = fam_b[lip] * 8 + 0
    tex(cv, band & ~far & ~jnt, rng, share=0.45, up=0.0, down=0.1)      # worn coping: sibling clusters (no specks)
    cv[jnt & (dist > 2) & ~far] = code('void', 1)
    # the south wall's outer face below its coping: the wall's thickness, seen as Eastward cuts it away
    # (round 5: the strip of courses that ran along the picture's south edge belonged to no room; the void
    # beyond the south wall's coping now runs to the edge, as round every other wall)
    walls_m = cap | face
    outer = ndi.binary_dilation(walls_m, iterations=1) & ~walls_m & ~stair
    seg_o = (XX // q(8) + YY // q(8)) % 3
    cv[outer] = np.where(seg_o[outer] == 0, code('stone_cool', 0), np.where(seg_o[outer] == 1, code('void', 1), code('stone', 0)))

    # thresholds: a worn sill across every doorway between two wall ends
    byid = {w['id']: w for w in plan['walls']}
    sills = []
    for wid, wl in byid.items():
        if wid.startswith('sep') and wid.endswith('_n') and wid[:-2] + '_s' in byid:
            n_, s_ = wl['rect'], byid[wid[:-2] + '_s']['rect']
            sills.append([n_[0] - 2, n_[1] + n_[3], n_[2] + 4, s_[1] - (n_[1] + n_[3])])
    for sx_, sy_, sw_, sh_ in []:          # no sills: the flags run through the doorways
        x0, y0, x1, y1 = max(0, q(sx_)), q(sy_) + q(1), q(sx_ + sw_), q(sy_ + sh_) - q(1)
        sm = np.zeros((H, W), bool)
        sm[y0:y1, x0:x1] = V.chamfer(y1 - y0, x1 - x0, 3)
        tt = V.shade(sm, 3, top=1, left=1, bot=-1, right=-1)
        cv[sm] = FI['stone_warm'] * 8 + tt[sm]
        hollow = sm & V.ellipse_mask((H, W), (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 0.3, (y1 - y0) * 0.36)
        cv[hollow] = code('stone_warm', 2)
        cv[ndi.binary_dilation(sm) & ~sm & floor] = code('stone_cool', 0)
        slab[sm] = 0
        floor_sill = sm
        floor = floor & ~floor_sill

    # deep shade at the walls' feet and damp in the corners: the floor sinks towards the room's edges in
    # a soft ramp (a rung within a few px of a wall, half a rung further out, more under a south face),
    # goes cold and damp where two walls meet, and moss gathers in the joints there. Kept as a field of
    # rungs (fshade) and painted with the light at the end.
    dfl = ndi.distance_transform_edt(~walls_m)
    near_face = ndi.distance_transform_edt(~face) <= q(14)
    fshade = np.clip(1.0 - (dfl - q(1.5)) / q(9), 0, 1) * 1.0 + near_face * np.clip(1.0 - dfl / q(16), 0, 1) * 0.6
    # (round 4, G-15: no noise blotches in the shade: they split the flags into a quilt of two values)
    corner = ndi.uniform_filter(walls_m.astype(float), size=q(18)) > 0.42
    wet = floor & corner & (dfl <= q(14))
    fcool = np.zeros((H, W), bool)
    fvar[wet & ~fjoint] = 1                                          # damp stone, on its colder sibling
    blob = ndi.gaussian_filter(rng.random((H, W)), q(1.2))
    moss = (wet | (floor & (dfl <= q(5)))) & (fjoint | (blob > np.quantile(blob, 0.9))) & (blob > np.quantile(blob, 0.7))
    moss &= floor & (dfl <= q(9))
    moss = ndi.binary_opening(moss, structure=np.ones((2, 2))) | (moss & fjoint & (dfl <= q(6)))
    fmat[moss] = 2
    # packed dirt and grit drifted against the walls and into the corners, in a few soft patches
    dpn = ndi.gaussian_filter(rng.random((H, W)), q(2.2))
    dpn = (dpn - dpn.mean()) / (dpn.std() + 1e-9)
    patch = floor & (dpn > 2.0 - np.clip(1 - dfl / q(16), 0, 1) * 0.9) & (fmat == 0)
    patch = ndi.binary_opening(patch, structure=np.ones((3, 3)))
    edge_n = ndi.gaussian_filter(rng.random((H, W)), 0.8) > 0.5
    patch &= ~(ndi.binary_dilation(patch, iterations=2) & ~ndi.binary_erosion(patch, iterations=2) & edge_n)
    # round 4 (G-16, G-17): no drifts of grit or stain blotches over the open floor
    # (round 5: no scatter of small lit stones over the flags: that was the terrazzo of specks, G-2)
    east_edge = walls_m & ~np.roll(walls_m, -1, 1)
    east_sh = np.zeros((H, W), bool)
    for k in range(1, q(4) + 1):
        east_sh |= np.roll(east_edge, k, 1)
    fshade[east_sh & floor & ~outer] += 0.6

    # --- the plate's channel, carved (its glow is an overlay) -------------------------------
    pz = plan.get('puzzle', {})
    fixed = wall_roots & floor
    if pz.get('channel'):
        fixed |= carve_channel(cv, channel_segments(pz), np.random.default_rng(43)) & floor

    # --- the shard's crater ----------------------------------------------------------------------
    objects = []
    pics = {}

    def add_pic(name, img):
        pics[name] = img
        return name

    for pr in plan.get('props', []):
        if pr['kind'] == 'shard':
            x, y = pr['at']
            e = ((WX - x) / 14) ** 2 + ((WY - y) / 8) ** 2
            cr = (e < 1) & floor
            fshade[cr] += 0.7 * (1 - e[cr])                     # the heaved flags round its foot lie in shade
            for k in range(3):                                  # three cracks where it went in, not a web (G-13)
                ang = k * 2 * math.pi / 3 + 0.9
                pts = [(q(x), q(y))]
                for s in range(1, 3):
                    pts.append((q(x + math.cos(ang) * 6 * s), q(y + math.sin(ang) * 3.4 * s) + int(rng.integers(-2, 3))))
                m = line_mask(cv.shape, pts, 0.6) & floor
                foff[m] = -2

    # --- light: the torches' warm pools, the shaft's cool pool, the hatch's daylight, the dark ---
    # The floor's light is a smooth field in rungs over the ambient (lf), falling off softly from each
    # source; the faces and the stair take theirs in whole tones (lightv), as before.
    lightv = np.full((H, W), -1, int)
    nz = (ndi.gaussian_filter(rng.random((H, W)), q(2.5)) - 0.5) * 0.5
    warm = np.zeros((H, W), bool)
    cool = np.zeros((H, W), bool)
    lf = np.zeros((H, W))
    lf_cool = np.zeros((H, W))
    lf_warm = np.zeros((H, W))
    for tx, ty in plan.get('torches', []):
        dfl = np.hypot((WX - tx) / 40, (WY - ty - 12) / 26)        # the floor below
        dfa = np.hypot((WX - tx) / 18, (WY - ty + TORCH_LIFT + 2) / 16)    # the face round the bracket
        d = np.minimum(dfl, dfa) + nz
        lightv = np.maximum(lightv, np.where((dfa < 0.5) | (d < 0.5), 2, np.where(d < 0.95, 1, np.where(d < 1.4, 0, -1))))
        warm |= d < 1.1
        # round 4 (G-14): a pool about 1 to 1.3 H across its radius, brightest at the wall's foot under the
        # flame, and no two alike (the torch's own seed sets its reach, its depth and a lean)
        trng = np.random.default_rng(int(tx * 7 + ty))
        rx, ry = 25 * trng.uniform(0.9, 1.25), 19 * trng.uniform(0.85, 1.2)
        lean = trng.uniform(-4, 4)
        dt = np.hypot((WX - tx - lean * np.clip((WY - ty) / ry, 0, 1)) / rx, (WY - ty - 1) / ry)
        lt = POOL_HEART * np.clip(1 - dt, 0, 1) ** 1.1 + POOL_SPILL * np.clip(1 - dt / 1.7, 0, 1) ** 1.0
        lf = np.maximum(lf, lt)
        lf_warm = np.maximum(lf_warm, lt)
    sk = plan.get('skylight')
    if sk:
        sx, sy = sk['at']
        d = np.hypot((WX - sx) / sk['rx'], (WY - sy) / sk['ry']) + nz
        # the beam crosses the face too: from the hole in the vault down to the pool
        hole = [w for w in plan['walls'] if w.get('skylight')][0]['skylight']
        hx = hole[0] + hole[2] / 2
        tcol = (WY - hole[1]) / max(1, sy - hole[1])
        beam = (np.abs(WX - (hx + (sx - hx) * tcol)) < 14 + 6 * tcol) & (tcol > 0.1) & (tcol < 0.9) & face
        lightv = np.maximum(lightv, np.where(d < 0.55, 2, np.where(d < 1.05, 1, np.where(d < 1.6, 0, -1))))
        lightv[beam] = np.maximum(lightv[beam], 1)
        cool |= (d < 1.0) | beam
        ds = np.hypot((WX - sx) / (sk['rx'] * 1.1), (WY - sy) / (sk['ry'] * 1.1)) + nz * 0.15
        lf_cool = 2.2 * np.clip(1 - ds, 0, 1) ** 1.3 + 1.2 * np.clip(1 - ds / 2.0, 0, 1) ** 0.9   # daylight from above, soft
    if plan.get('stair'):
        sx, sy, sw, sh = plan['stair']['rect']
        d = np.hypot((WX - sx - sw) / 40, (WY - sy - sh / 2) / 24)
        lightv = np.maximum(lightv, np.where(d < 0.5, 1, np.where(d < 1.2, 0, -1)))
        lf = np.maximum(lf, 2.2 * np.clip(1 - (d / 1.6 + nz * 0.3), 0, 1))
    lightv[stair] = 0
    lightv = np.clip(ndi.median_filter(lightv, size=5), -1, 2)
    # on the faces the light falls off block by block along the courses, never a disc laid over the
    # masonry (8 Nov, G-4): each block takes the mean of the light over it, in whole steps
    blocks = face & (cv != code('stone_cool', 0)) & (cv >= 0) & (cv % 8 < 6)
    blab, nbl = ndi.label(blocks)
    if nbl:
        bmean = ndi.mean(lightv.astype(float), labels=blab, index=np.arange(1, nbl + 1))
        snapped = np.concatenate([[0], np.floor(bmean + 0.5).astype(int)])
        lightv[blocks] = snapped[blab[blocks]]
    # the walls' faces keep their own values in the ambient (they are lit stone, brighter than the floor)
    # and climb where a pool reaches them
    lightv[face] = np.maximum(lightv[face], 0)                       # faces keep their own values between the torches
    lightv[cap] = 0                          # the vault's tops and their coping keep their own values
    lightv[floor] = 0                        # the floor is painted from lf at the end
    edge_tone = (cv % 8 >= 6) | (cv < 0)
    for lv in (-2, -1, 1, 2):
        sel = (lightv == lv) & ~edge_tone
        cv[sel] = step(cv[sel], lv)
    sel = warm & ~edge_tone & ~cool & np.isin(cv // 8, [FI[s] for s in STONES]) & ~floor
    cv[sel] = swap_fam(cv[sel], {'stone': 'stone_warm', 'stone_warm': 'stone'})
    sel = cool & ~edge_tone & np.isin(cv // 8, [FI[s] for s in STONES]) & ~floor
    cv[sel] = swap_fam(cv[sel], {'stone': 'stone_cool', 'stone_cool': 'stone'})
    lf_torch = lf.copy()
    lf = np.maximum(lf, lf_cool)
    # the hue of the light is decided flag by flag (8 Nov, G-7), from its means over the flag, so no arc
    # of another colour cuts across a stone
    fcool, fwarm = flag_tint(slab, nflags, lf_cool, lf_torch, lf_warm)
    tint_masks = (fcool.copy(), fwarm.copy())
    fshade *= 1 - 0.45 * np.clip(lf / 3, 0, 1)                    # a pool reaches into the walls' feet

    # --- objects ---------------------------------------------------------------------------------
    for k, pr in enumerate(plan.get('props', [])):
        w, h = pr.get('size', [12, 8])
        pic = PROPS[pr['kind']](w, h, seed=pr.get('seed', 100 + k))
        x, y = pr['at']
        objects.append(dict(id=pr['id'], kind=pr['kind'], png=add_pic(pr['id'], pic.rgba()), foot=(q(x), q(y)),
                            anchor=(pic.ax, pic.ay), alpha=pic.alpha(), cond=pr.get('if'),
                            solid=[x - w / 2, y - h, w, h] if pr.get('solid') else None))
    frames = [p_torch(i, 7) for i in range(TORCH_FRAMES)]
    fw = frames[0].W
    sheet = Image.new('RGBA', (fw * TORCH_FRAMES, frames[0].H))
    for i, fr in enumerate(frames):
        sheet.paste(fr.rgba(), (i * fw, 0))
    add_pic('torch', sheet)
    for i, (tx, ty) in enumerate(plan.get('torches', [])):
        objects.append(dict(id='torch_%d' % (i + 1), kind='torch', png='torch', foot=(q(tx), q(ty)),
                            anchor=(frames[0].ax, frames[0].ay), lift=q(TORCH_LIFT), frames=TORCH_FRAMES, alpha=None, cond=None,
                            solid=None))
    for wl in plan['walls']:
        if wl.get('alcove'):
            x, y, w, h = wl['rect']
            pic = p_cairn_alcove(9)
            objects.append(dict(id='cairn_alcove', kind='cairn', png=add_pic('cairn_alcove', pic.rgba()),
                                foot=(q(wl['alcove']), q(y + h)), anchor=(pic.ax, pic.ay), alpha=None, cond=None,
                                solid=None))
    if pz:
        pl = pz['plate']
        x, y = pl['at']
        w, h = pl['size']
        flag = {'flags': [pl['flag']]}
        nflag = {'not_flags': [pl['flag']]}
        for pressed, cond in ((False, nflag), (True, flag)):
            pic = p_plate(w, h, pressed)
            nm = 'plate_down' if pressed else 'plate_up'
            objects.append(dict(id=nm, kind='floor', png=add_pic(nm, pic.rgba()), foot=(q(x), q(y + h / 2)),
                                anchor=(pic.ax, pic.ay), alpha=None, cond=cond, solid=None))
        pic = p_channel(pz, True)
        objects.append(dict(id='channel_lit', kind='floor', png=add_pic('channel_lit', pic.rgba()),
                            foot=(q(pz['channel'][0][0]), q(pz['channel'][0][1])), anchor=(pic.ax, pic.ay), alpha=None,
                            cond=flag, solid=None))
        lv = pz['lever']
        open_ = {'flags': [lv['flag']]}
        shut = {'not_flags': [lv['flag']]}
        x, y = lv['at']
        for pulled, cond in ((False, shut), (True, open_)):
            pic = p_lever(pulled)
            nm = 'lever_down' if pulled else 'lever_up'
            objects.append(dict(id=nm, kind='lever', png=add_pic(nm, pic.rgba()), foot=(q(x), q(y)),
                                anchor=(pic.ax, pic.ay), alpha=None, cond=cond, solid=[x - 3, y - 4, 6, 4]))
        sl = pz['seal']
        x, y, w, h = sl['rect']
        pic = p_seal(w, h, sl['height'], True)
        objects.append(dict(id='seal_slab', kind='seal', png=add_pic('seal_slab', pic.rgba()), foot=(q(x + w / 2), q(y + h)),
                            anchor=(pic.ax, pic.ay), alpha=None, cond=shut, solid=[x, y, w, h]))
        pic = p_seal_sunk(w, h)
        objects.append(dict(id='seal_sunk', kind='floor', png=add_pic('seal_sunk', pic.rgba()),
                            foot=(q(x + w / 2), q(y + h)), anchor=(pic.ax, pic.ay), alpha=None, cond=open_, solid=None))

    # cast shadows: the pillars throw theirs down and to the right, as long as they are tall
    for o in objects:
        if o['kind'] == 'stump':
            fx, fy = o['foot']
            Lh, wd = q(22), q(5)
            u = (XX - fx) * 0.7 + (YY - fy) * 0.7
            v = -(XX - fx) * 0.7 + (YY - fy) * 0.7
            sh = (u > -q(2)) & (u < Lh) & (np.abs(v) < wd * (1 - 0.35 * np.clip(u / Lh, 0, 1))) & floor
            fshade[sh] += 1.0 + 0.4 * np.clip(1 - u[sh] / Lh, 0, 1)      # the cast shadow, softening with length
    # contact shadows under the standing props
    for o in objects:
        if o['kind'] in ('rubble', 'roots', 'urn', 'stump', 'lever'):      # the seal stands in its own socket
            fx, fy = o['foot']
            w = (o['solid'][2] if o.get('solid') else 10) * D
            e = ((XX - fx - q(2)) / (w / 2 + q(3))) ** 2 + ((YY - fy + q(1)) / q(4)) ** 2
            sel = (e < 1) & floor
            fshade[sel] += 0.8 * (1 - e[sel]) ** 0.5
    # --- the floor painted: light minus shade --------------------------------------------------------
    # In the shade each flag takes the light at its middle (calm, the odd stone a tone off). In a pool
    # the light runs across the flags in a few soft, irregular steps: each flag is lit where the pool
    # reaches it and darker on its far side, its contours wobbling with a slow noise (no dither, no
    # flag-sized squares), so the pool reads round, as Eastward's 06; the joints stay dark.
    level = FLOOR_AMBIENT + lf - fshade
    level -= 0.75 * np.clip(1 - lf / 0.9, 0, 1)            # far from every light the floor sinks a little (the walls and corners do the rest)
    rung = pool_rungs(level, slab, nflags, lf >= 0.7)
    jl = FLOOR_AMBIENT + 0.45 * lf - fshade - 0.6 * np.clip(1 - lf / 0.9, 0, 1)
    jr = np.clip(np.floor(jl + 0.5).astype(int), 0, 4)
    nb = ndi.grey_erosion(np.where(slab > 0, rung, 9), size=(3, 3))      # the darkest flag beside the joint
    jt = (slab == 0) & floor
    rung[jt] = np.minimum(jr[jt], np.maximum(0, nb[jt] - 1)) + 1          # +1: floor_codes takes the joint's -1
    # in a pool the joints are lit too, a rung under the lit flag on its warm sibling (round 4, G-14)
    pj = jt & (nb >= FLOOR_AMBIENT + 1) & (nb < 9)
    rung[pj] = nb[pj]
    fwarm = fwarm | (ndi.binary_dilation(fwarm, iterations=1) & jt)
    fcool = fcool | (ndi.binary_dilation(fcool, iterations=1) & jt & ~fwarm)
    # every flag has its own lips (8 Nov, G-3, as each hex flag in Eastward's 06): its north and west
    # lip a rung up, broken where it is worn, its south and east lip a rung down
    nwl, sel_ = flag_lips(slab, np.random.default_rng(105))
    off = foff.copy()
    lit_lip = nwl & (foff == 0)
    off[lit_lip & (rung <= FLOOR_AMBIENT)] += 1            # in the shade the north-west lip is a rung up;
    fvar = np.where(lit_lip & (rung > FLOOR_AMBIENT), 1 - fvar, fvar)   # in a pool its sibling (no bright seams)
    off[sel_ & (foff == 0)] -= 1
    paint = floor & ~outer & ~fixed
    fc = floor_codes(rung, off, fmat, fvar, fcool, fwarm)
    cv[paint] = fc[paint]
    # each flag's face: sibling clusters at the same tone (shape, not contrast: house-style 8, G-10)
    blue = np.isin(cv // 8, [FI['slate'], FI['slate_cool']])
    flag_texture(cv, paint & (slab > 0) & ~nwl & ~sel_ & (foff == 0), np.random.default_rng(105))
    break_runs(cv, cv >= 0, np.random.default_rng(105))
    V.tidy(cv, passes=2, keep=(cv % 8 >= 6))
    ground = Image.fromarray(to_rgba(cv), 'RGBA').convert('RGB')
    if fields is not None:                              # for the tests: the floor's flags and where it was painted
        fields.update(slab=slab, paint=paint, joint=fjoint, codes=cv.copy(), tint_cool=tint_masks[0], tint_warm=tint_masks[1])

    # --- write ---------------------------------------------------------------------------------
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith('.png') and f != 'ground.png' and f[:-4] not in pics:
            os.remove(os.path.join(out_dir, f))
    ground.save(os.path.join(out_dir, 'ground.png'), optimize=True)
    for name, img in pics.items():
        img.save(os.path.join(out_dir, name + '.png'), optimize=True)
    doc = dict(zone=plan['id'], kit='undercroft', density=D, size=[W, H], inputs=plan.get('_inputs'),
               kit_drawn=sorted(n + '.png' for n in pics), objects=[])
    for o in objects:
        e = dict(id=o['id'], kind=o['kind'], png=o['png'] + '.png', foot=[int(o['foot'][0]), int(o['foot'][1])],
                 offset=[-int(o['anchor'][0]), -int(o['anchor'][1]) - int(o.get('lift', 0))], cond=o.get('cond'),
                 solid=o.get('solid'))
        if o.get('frames'):
            e['frames'] = o['frames']
        doc['objects'].append(e)
    json.dump(doc, open(os.path.join(os.path.dirname(out_dir.rstrip('/')), 'kit.json'), 'w'), indent=1)

    if preview:
        os.makedirs(preview, exist_ok=True)
        img = ground.convert('RGBA')
        for o in sorted(objects, key=lambda o: (o['kind'] != 'floor', o['foot'][1])):
            c = o.get('cond') or {}
            if c.get('flags'):
                continue
            pic = pics[o['png']]
            if o.get('frames'):
                pic = pic.crop((0, 0, pic.width // o['frames'], pic.height))
            X = int(o['foot'][0] - o['anchor'][0])
            Y = int(o['foot'][1] - o['anchor'][1] - o.get('lift', 0))
            img.alpha_composite(pic, (max(0, X), max(0, Y)))
        img.convert('RGB').save(os.path.join(preview, plan['id'] + '.png'))
    return dict(zone=plan['id'], size=[W, H], objects=len(objects), pictures=len(pics))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', required=True)
    ap.add_argument('--density', type=float, default=3.0)
    ap.add_argument('--out', required=True)
    ap.add_argument('--preview', default=None)
    a = ap.parse_args(argv)
    plan = json.load(open(a.plan))
    ctx.configure(a.density, {}, plan)
    plan['_inputs'] = input_hash(os.path.abspath(a.plan), a.density)
    print(json.dumps(build(plan, a.out, a.preview)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
