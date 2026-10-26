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
FLOOR_LADDER = [(('soot', 1), ('void', 2)), (('slate_cool', 1), ('soot', 2)), (('void', 4), ('stone_cool', 1)),
                (('stone_warm', 1), ('ash', 2)), (('stone', 2), ('stone_warm', 2)), (('stone', 3), ('stone_warm', 3)),
                (('stone_warm', 4), ('stone', 4))]
# under the skylight the same rungs on the cool ramps (daylight from above is blue against the torches)
FLOOR_LADDER_COOL = {3: (('slate', 2), ('slate_cool', 2)), 4: (('slate', 3), ('slate_cool', 3)),
                     5: (('slate', 4), ('slate_cool', 4)), 6: (('slate', 5), ('slate_cool', 5))}
# under a torch the pool's rungs lean warm (pitch-light on stone: the warm grey and the sand ramp)
FLOOR_LADDER_WARM = {3: (('stone_warm', 1), ('ash', 2)), 4: (('stone_warm', 2), ('ashlar', 2)),
                     5: (('ashlar', 3), ('sand', 2)), 6: (('sand', 3), ('ashlar', 4))}
FLOOR_AMBIENT = 1                # far from every light the floor sits on rung 1, in shade, as Eastward's


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
    keep = np.concatenate([[False], rng.random(nm) < 0.35])          # only some corners are worn open
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
    for _ in range(int(n * 0.9)):
        ys, xs = np.nonzero(joint)
        if not len(ys):
            break
        k = int(rng.integers(0, len(ys)))
        y, x = int(ys[k]), int(xs[k])
        h_, w_ = (2, int(rng.integers(2, 5))) if rng.random() < 0.5 else (int(rng.integers(2, 5)), 2)
        sel = np.zeros(shape, bool)
        sel[max(0, y - 1):y - 1 + h_, max(0, x - 1):x - 1 + w_] = True
        off[sel & where] = -1
    for _ in range(int(n * 1.6)):                                  # pits and scuffs, in two-texel clusters
        y, x = int(rng.integers(2, H - 3)), int(rng.integers(2, W - 4))
        w_ = int(rng.integers(2, 4))
        if ids[y, x] and not joint[y:y + 2, x:x + w_].any():
            off[y:y + 2, x:x + w_] = -1
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
    # no large flag is left a bare field: a pit or two (a tone down, two to three texels) in its body,
    # as Eastward's flags carry a few marks each
    objs = ndi.find_objects(ids)
    for f, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        m = ids[sl] == f
        a_ = int(m.sum())
        if a_ < 450:
            continue
        inner = ndi.binary_erosion(m, iterations=4)
        ys, xs = np.nonzero(inner)
        for _ in range(min(len(ys), a_ // 240)):
            k = int(rng.integers(0, len(ys)))
            y, x = ys[k] + sl[0].start, xs[k] + sl[1].start
            off[y:y + 2, x:x + int(rng.integers(2, 4))] = -1
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
    out[dirt] = _FI['earth_cool'] * 8 + np.clip(lv[dirt] - 1, 1, 3)
    drift = mat == 3                                  # grey grit drifted over the flags, a step under them
    out[drift] = _FI['ash'] * 8 + np.clip(lv[drift] - 1, 1, 3)
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
        mottle(a, m, rng, sigma=1.3, sib_share=0.1)


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
    for _ in range(lets):
        i = int(rng.integers(0, len(pts)))
        x, y = pts[i]
        side = 1 if rng.random() < 0.5 else -1
        Lr = V.q(rng.uniform(4, 9))
        tip = (x + side * Lr, y + V.q(rng.uniform(2, 6)))
        mid = ((x + tip[0]) / 2, y + V.q(1) * side * 0.3)
        lm = line_mask(cv.shape, [(x, y), mid, tip], 0.7) & where & ~m
        cv[lm] = V.code(fam, max(0, base - 1))
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


def wall_face(cv, x0, y0, x1, y1, rng, where, roots=(), arcade=True):
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
        n = max(1, int(round((x1 - x0) / bay)))
        bw = (x1 - x0) / n
        for i in range(n):
            bx0 = int(x0 + i * bw)
            bx1 = int(x0 + (i + 1) * bw)
            # the pilaster at the bay's west end
            px0, px1 = bx0, bx0 + pil
            pm = np.zeros(cv.shape, bool)
            pm[y0 + corn:y1 - plin, px0:px1] = True
            pm &= where
            masonry(cv, px0, y0 + corn, px1, y1 - plin, rng, pm, base=3, course=4.5, length=(8, 8.1), east_dark=False)
            cv[y0 + corn:y1 - plin, px0:px0 + 1][pm[y0 + corn:y1 - plin, px0:px0 + 1]] = code('stone', 4)
            cv[y0 + corn:y1 - plin, px1 - 1:px1][pm[y0 + corn:y1 - plin, px1 - 1:px1]] = code('stone_cool', 1)
            # the recess under the arch
            rx0, rx1 = px1 + q(2), bx1 - q(2) if i < n - 1 else bx1 - pil - q(2)
            if rx1 - rx0 < q(10):
                continue
            rad = (rx1 - rx0) / 2
            cx = (rx0 + rx1) / 2
            spring = y0 + corn + q(3) + rad
            Y, X = np.mgrid[0:cv.shape[0], 0:cv.shape[1]] + 0.5
            rec = (((X - cx) ** 2 + (Y - spring) ** 2 <= rad * rad) & (Y < spring)) | \
                  ((X >= rx0) & (X < rx1) & (Y >= spring) & (Y < y1 - plin))
            rec &= where
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
    mottle(cv, where & ndi.binary_erosion(where, iterations=1), rng, sigma=1.8, sib_share=0.1)
    for rx in roots:
        split_root(cv, rx, y0, y1, rng, where)


def split_root(cv, x, y0, y1, rng, where):
    """One of the oak's roots breaking through the vault: a ragged hole at the cornice where it came
    through (broken stones lit round its lip), down the face with the masonry beside it cracked and a
    block pushed out, then over the plinth onto the floor."""
    V = _v()
    q, code = V.q, V.code
    pts = [(x, y0 + q(1))]
    y = y0 + q(1)
    while y < y1 + q(6):
        y += q(6)
        pts.append((pts[-1][0] + int(rng.integers(-q(2.5), q(2.5) + 1)), y))
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
    root(cv, pts, q(4.2), q(1.8), allm, rng, base=2, lets=6)


def p_rubble(w, h, seed):
    """Fallen vault stones: dressed blocks of several sizes, each with its top, bevel and front,
    piled back to front (the big ones at the foot, a split block leaning on them), chips and grit
    round the heap."""
    V = _v()
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=h * 1.1, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    items = []
    n = max(4, int(w * h / 40))
    for k in range(n):
        fx = rng.uniform(-0.5, 0.5)
        fy = rng.random() ** 0.6
        items.append((fy, fx))
    items.sort()
    for fy, fx in items:
        bw = q(rng.uniform(4, 8.5) * (0.7 + 0.5 * fy))
        bh = q(rng.uniform(2.6, 4.2) * (0.7 + 0.4 * fy))
        top = max(3, int(bh * rng.uniform(0.35, 0.55)))
        hump = (1 - (2 * fx) ** 2) * q(h * 0.6)
        x = int(cx + fx * q(w) - bw / 2)
        y = int(yb - q(h) * (1 - fy) * 0.55 - hump * (1 - fy) - bh)
        cut_block(a, x, y, x + bw, y + bh, top, str(rng.choice(['stone', 'stone_warm', 'stone_cool'])),
                  int(rng.choice([2, 3, 3])), rng)
    for _ in range(int(w / 2)):
        x = cx + int(rng.integers(-q(w / 2) - q(3), q(w / 2) + q(3)))
        y = yb - int(rng.integers(0, q(2.5)))
        V.blk(a, x, y - 2, x + int(rng.integers(3, 6)), y + 1, 'stone', int(rng.choice([2, 3])), cut=0)
    return V.finish(p)


def p_roots(w, h, seed):
    """Roots come down through the vault and lie over the floor: thick runners from one knot,
    sinuous and tapering, over clods of spilled soil and a few fallen stones."""
    V = _v()
    q = V.q
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=6, side=10)
    a, cx, yb = p.a, p.ax, p.ay
    for _ in range(int(w / 6)):
        sx = cx + q(rng.uniform(-w / 2.4, w / 2.4))
        sy = yb - q(rng.uniform(0.5, h * 0.7))
        V.blk(a, sx, sy, sx + q(rng.uniform(2, 3.4)), sy + q(rng.uniform(1.4, 2.2)), 'stone_cool', int(rng.choice([2, 3])), cut=1)
    allm = np.ones(a.shape, bool)
    knot = (cx + q(rng.uniform(-2, 2)), yb - q(h * 0.75))
    for k in range(4):
        ang = (-0.15, 0.25, 0.85, 1.15)[k] * math.pi + rng.uniform(-0.15, 0.15)
        pts = [knot]
        L = w * (0.55 if k in (0, 3) else 0.35)
        for i in range(1, 6):
            t = i / 5
            wob = math.sin(t * 5 + k) * q(1.6)
            pts.append((knot[0] + math.cos(ang) * q(L) * t, knot[1] + math.sin(ang) * q(h * 0.5) * t + wob))
        root(a, pts, q(3.0 if k in (0, 3) else 2.3), q(1.0), allm, rng, base=2, lets=3)
    return V.finish(p)


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
    sp.add('mouth', g.ellipse(0, -39.5, 6.5, 2.0), 'soot', base=1, z=2, fixed=1, outline=False)
    for sx in (-1, 1):
        sp.add('lug%d' % sx, g.capsule(sx * 9, -33, sx * 14, -28, 2.4, 2.0), 'clay', base=3, z=-0.5, k=0.8)
    band = (g.ellipse(0, -18, 15.2, 17.2) & (g.Y > -24) & (g.Y < -20.5))
    sp.add('band', band, 'clay_cool', base=2, z=0.5, k=0.8)
    sp.add('chip', g.poly([(5, -30), (10, -27), (7, -24)]), 'sand', base=4, z=0.6, k=0.6)
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
    weather(p.a, p.a >= 0, np.random.default_rng(seed), 1.0, moss=False)
    return p


def p_stump(w, h, seed):
    """A broken pillar of the old vault on its square plinth: a fluted drum shaded as a cylinder (lit
    left, shade and core shadow right), its jagged break a lit top plane with the flutes' ends showing,
    a fallen drum piece and chips at its base."""
    from scripts.art.native import raster as R
    V = _v()
    rng = np.random.default_rng(seed)
    s = ctx.D / 3.0
    W, H = int(round(84 * s)), int(round(104 * s))
    sp = R.Sprite(W, H, s, W / 2, H - 6 * s)
    g = sp.g
    r = w * 3 / 2 - 3
    sp.add('plinth_top', g.rect(-r - 6, -16, r + 6, -9), 'stone', base=3, z=0, flat=True, lo=0, hi=5)
    sp.add('plinth', g.rect(-r - 6, -9, r + 6, 0), 'stone', base=2, z=0.1, flat=True, lo=0, hi=5)
    up_ = (g.X + r + 6) / (2 * r + 12)
    for nm in ('plinth_top', 'plinth'):                     # the plinth lit from the left too
        sp.mark(nm, (up_ > 0.08) & (up_ < 0.4), 1)
        sp.mark(nm, up_ > 0.8, -1)
    xs = np.linspace(-r, r, 9)
    brk = [(x, -70 + 9 * math.sin(x * 0.35 + seed) + x * 0.35) for x in xs]
    shaft = g.poly([(-r, -12)] + brk + [(r, -12)])
    sp.add('shaft', shaft, 'stone', base=1, z=1, flat=True, lo=0, hi=5)
    sp.mark('shaft', (g.X + r) / (2 * r) < 0.66, 1)
    u = (g.X + r) / (2 * r)                                  # across the drum, light from the left
    sp.mark('shaft', (u > 0.1) & (u < 0.42), 2)
    sp.mark('shaft', ((u <= 0.1) | ((u >= 0.42) & (u < 0.66))), 1)
    sp.mark('shaft', u > 0.88, -1)
    for fx in np.linspace(-r + 4, r - 4, 6):                 # flutes: a shadowed groove, its far edge lit
        sp.mark('shaft', g.rect(fx - 0.9, -80, fx + 0.4, -14), -1)
        sp.mark('shaft', g.rect(fx + 0.4, -80, fx + 1.3, -14), 1)
    top = np.zeros_like(shaft)
    for (xa, ya), (xb, yb) in zip(brk, brk[1:]):
        top |= g.poly([(xa, ya), (xb, yb), (xb, yb + 5), (xa, ya + 5)])
    sp.add('break', top & shaft, 'stone_warm', base=3, z=1.5, mode='top')
    for k in range(3):
        cx = r + 9 + k * 4 + rng.uniform(-1, 1)
        sp.add('chip%d' % k, g.ellipse(cx, -2 - (k % 2) * 2, 2.4, 1.8), 'stone_cool', base=1, z=2.2)
    pic = _sprite_pic(sp.render(), W, H, int(round(H - 6 * s)))
    left = np.zeros(pic.a.shape, bool)
    left[:, :pic.a.shape[1] // 2] = True                   # age on the lit side only: the shade side stays dark
    weather(pic.a, (pic.a >= 0) & left, rng, 1.4, moss=True)
    return V.finish(pic)


def p_shard(w, h, seed):
    """The woodland's great shard: a long crystal of the moon driven into the floor at a slant. Six
    facets each catch the upper-left light differently (the lit face, two mid faces, the shadow side),
    fine fractures run along its length, and broken flags heave up round its foot; a light source,
    so no outline on the crystal itself."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native.raster import Grid
    rng = np.random.default_rng(seed)
    p = V._pic(w, h, up=32, side=8)
    a, cx, yb = p.a, p.ax, p.ay
    g = Grid(a.shape[1], a.shape[0], 1.0, 0, 0)
    tip = (cx + q(7), yb - q(31))
    L, R = (cx - q(5), yb - q(2)), (cx + q(4), yb)
    ml, mr = (cx - q(3.5), yb - q(18)), (cx + q(6), yb - q(15))
    mid = (cx + q(0.5), yb - q(5))
    facets = [([L, ml, tip, mid], 3), ([mid, tip, mr, R], 1), ([L, mid, R], 2),
              ([ml, (cx - q(1), yb - q(25)), tip], 4), ([mr, tip, (cx + q(7.5), yb - q(22))], 0)]
    for poly, t in facets:
        a[g.poly(poly)] = code('dusk', t)
    for k in range(3):                                         # fractures along the length
        f0 = (cx - q(2) + k * q(2), yb - q(4))
        f1 = (cx + q(1) + k * q(2), yb - q(20) - k * q(2))
        m = line_mask(a.shape, [f0, f1], 0.6) & (a >= 0)
        a[m] = code('dusk', 1 if k != 1 else 5)
    a[g.poly([(cx - q(1.5), yb - q(6)), (cx, yb - q(22)), (cx + q(1.5), yb - q(6))])] = code('dusk', 4)
    lit = a == code('dusk', 3)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    for k in range(6):                                         # step facets across the long lit face
        band = lit & (Y > yb - q(6 + 5 * k)) & (Y < yb - q(3 + 5 * k)) & ((X + Y // 3) % 7 < 4)
        a[band] = code('dusk', 2 + (k % 2) * 2)
    tipm = (a >= 0) & (Y < yb - q(20))
    for k in range(3):                                         # fractures near the tip
        f0 = (tip[0] - q(2 + k), tip[1] + q(4 + 2 * k))
        f1 = (tip[0] - q(4 + k), tip[1] + q(10 + 2 * k))
        a[line_mask(a.shape, [f0, f1], 0.6) & tipm] = code('dusk', 1 + 3 * (k % 2))
    for _ in range(14):                                        # bright inclusions, in pairs
        k = int(rng.integers(0, max(1, int((a >= 0).sum()))))
        ys, xs = np.nonzero(a >= 0)
        y, x = ys[k], xs[k]
        a[y:y + 2, x:x + 2] = np.where(a[y:y + 2, x:x + 2] >= 0, code('dusk', 4), a[y:y + 2, x:x + 2])
    V.tidy(a)
    return p

def p_torch(frame, seed):
    """A wall torch: an iron bracket on the face, a cup of pitch and its flame. Four drawings of the
    flame (it leans and lifts) for a finite flicker; the bracket never moves. The canvas's foot is
    the cup; the flame is a light source (no outline)."""
    V = _v()
    q, code = V.q, V.code
    W, H = q(10), q(22)
    p = V.Pic(W, H, W // 2, H - q(6))
    a, cx, cy = p.a, p.ax, p.ay
    V.blk(a, cx - q(1.8), cy + q(2.2), cx + q(1.8), cy + q(6.4), 'iron', 2, cut=1)    # the plate on the wall
    for ry in (2.9, 5.2):
        V.fill(a, cx - q(1.1), cy + q(ry), cx - q(1.1) + 2, cy + q(ry) + 2, code('iron', 4))   # rivets into the joint
        V.fill(a, cx + q(0.6), cy + q(ry), cx + q(0.6) + 2, cy + q(ry) + 2, code('iron', 4))
    V.bar(a, cx, cy + q(3.6), cx, cy + q(0.6), q(0.6), 'iron', 3)                      # the arm out from the wall
    V.bar(a, cx, cy + q(3.0), cx + q(1.2), cy + q(1.2), q(0.45), 'iron', 2)            # its strut
    cup = V.ellipse_mask(a.shape, cx, cy - q(0.4), q(2.4), q(1.6)) & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] >= cy - q(1.4))
    V.blob(a, cup, 'iron', 3)
    for bx in (-1.4, 0.6):                                                              # the basket's straps
        V.fill(a, cx + q(bx), cy - q(1.3), cx + q(bx) + 2, cy + q(0.9), code('iron', 1))
    V.fill(a, cx - q(2.4), cy - q(1.4), cx + q(2.4), cy - q(1.4) + 2, code('iron', 4))  # the lit rim
    a[V.ellipse_mask(a.shape, cx, cy - q(1.9), q(1.9), q(0.6))] = code('soot', 1)       # pitch in the cup
    V.outline(a)
    lean = (0, 1, 0, -1)[frame % 4]
    hgt = (9.0, 10.5, 8.0, 10.0)[frame % 4]
    base_y = cy - q(2)
    outer = np.zeros(a.shape, bool)
    mid = np.zeros(a.shape, bool)
    inner = np.zeros(a.shape, bool)
    for i in range(10):
        t = i / 9
        r = q(2.6) * (1 - t) ** 0.8 + 0.6
        x = cx + lean * q(1.4) * t * t
        y = base_y - q(hgt) * t
        outer |= V.ellipse_mask(a.shape, x, y, r, r)
        if t < 0.7:
            mid |= V.ellipse_mask(a.shape, x, y, r * 0.66, r * 0.66)
        if t < 0.4:
            inner |= V.ellipse_mask(a.shape, x, y, r * 0.38, r * 0.5)
    a[outer] = code('lava', 3)
    a[mid] = code('lamp', 4)
    a[inner] = code('lamp', 5)
    if frame % 2 == 0:
        sx = cx + (q(2) if frame == 0 else -q(2))
        V.fill(a, sx, base_y - q(hgt) - q(2), sx + 2, base_y - q(hgt) - q(2) + 2, code('lamp', 5))
    V.tidy(a)
    return p


def sigil(a, cx, cy, r, lit):
    """The starfall sigil carved in stone: a ring and a four-pointed star; glowing while it holds."""
    V = _v()
    q, code = V.q, V.code
    ring = V.ellipse_mask(a.shape, cx, cy, r, r * 0.8) & ~V.ellipse_mask(a.shape, cx, cy, r - 2, r * 0.8 - 2)
    star = line_mask(a.shape, [(cx, cy - r * 0.7), (cx, cy + r * 0.7)], 0.7) | \
        line_mask(a.shape, [(cx - r * 0.7, cy), (cx + r * 0.7, cy)], 0.7)
    star |= V.ellipse_mask(a.shape, cx, cy, q(1.2), q(1.0))
    m = ring | star
    if lit:
        a[m] = code('dusk', 4)
        a[m & (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] < cy)] = code('dusk', 5)
    else:
        a[m] = code('stone_cool', 1)
        lip = np.roll(m, 1, 0) & ~m & (a >= 0)
        a[lip] = code('stone', 4)
    return m


def p_seal(w, h, height, sealed=True):
    """The sealed slab: a block of dressed stone plugging the passage, `height` world px tall, seen
    like every wall: its top (the sigil carved in it, glowing while it holds, a lit lip at its south
    edge) and its south face (two courses and a plinth with a dark foot)."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(5)
    W, H = q(w) + 6, q(h) + q(height) + 6
    p = V.Pic(W, H, W // 2, H - 4)
    a = p.a
    x0, x1 = 3, W - 3
    ytop, yface, yb = 3, 3 + q(h), H - 3
    # the top: three long slabs end to end, the middle one with the sigil
    for k, (s0, s1) in enumerate(((ytop, ytop + (yface - ytop) // 3), (ytop + (yface - ytop) // 3, ytop + 2 * (yface - ytop) // 3),
                                  (ytop + 2 * (yface - ytop) // 3, yface))):
        cut_block(a, x0, s0, x1, s1 - 1, (s1 - s0) - q(2), 'stone_warm' if k != 1 else 'stone', 1, rng, grain=False)
        sm = np.zeros(a.shape, bool)
        sm[s0 + 2:s1 - 3, x0 + 2:x1 - 2] = True
        wear(a, sm & (a >= 0), 'stone_warm' if k != 1 else 'stone', 2, rng)
    V.fill(a, x0, ytop, x1, yface, code('stone_cool', 0), a < 0)
    sigil(a, (x0 + x1) / 2, (ytop + yface) / 2, q(5.5), sealed)
    weather(a, (a >= 0), rng, 0.8)
    V.fill(a, x0, yface - 2, x1, yface, code('stone', 4))                 # the lit lip
    m = np.zeros(a.shape, bool)
    m[yface:yb, x0:x1] = True
    masonry(a, x0, yface, x1, yb, rng, m, base=1, course=6, length=(7, 9), east_dark=False)
    V.fill(a, x0, yface, x1, yface + 1, code('stone_cool', 0))
    V.fill(a, x0, yb - q(5), x1, yb - q(5) + 1, code('stone', 3))
    V.fill(a, x0, yb - 2, x1, yb, code('stone_cool', 0))
    V.fill(a, x1 - 2, yface, x1, yb, code('stone_cool', 1))
    fm = np.zeros(a.shape, bool)
    fm[yface + 2:yb - 2, x0:x1 - 2] = True
    weather(a, fm & (a >= 0), rng, 0.8)
    V.finish(p)
    break_runs(a, a >= 0, rng, longest=40)                 # the outline too: no ruler-straight edge
    return p


def p_seal_sunk(w, h):
    """The slab sunk flush with the floor: its top only, the sigil gone dark."""
    V = _v()
    q = V.q
    W, H = q(w) + 4, q(h) + 4
    p = V.Pic(W, H, W // 2, H - 2)
    a = p.a
    for k in range(3):
        cut_block(a, 2, 2 + k * (H - 4) // 3, W - 2, 2 + (k + 1) * (H - 4) // 3 - 1, (H - 4) // 3 - 3,
                  'stone_warm' if k != 1 else 'stone', 2, np.random.default_rng(k), grain=False)
        sm = np.zeros(a.shape, bool)
        sm[4 + k * (H - 4) // 3:(k + 1) * (H - 4) // 3 - 2, 4:W - 4] = True
        wear(a, sm & (a >= 0), 'stone_warm' if k != 1 else 'stone', 3, np.random.default_rng(k + 5))
    weather(a, a >= 0, np.random.default_rng(23), 1.5)
    sigil(a, W / 2, H / 2, q(5.5), False)
    return V.finish(p)


def p_plate(w, h, pressed):
    """The pressure plate: a square slab set in a frame of narrow stones, the sigil carved in a sunk
    panel. Raised two world px it shows a bevel and its front; pressed, it sits flush, its edge in
    the frame's shadow, and the sigil glows."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(13)
    up = 0 if pressed else 2
    W, H = q(w + 4) + 6, q(h + 4 + up) + 6
    p = V.Pic(W, H, W // 2, H - 3)
    a = p.a
    x0, y0, x1, y1 = 3, 3 + q(up), W - 3, H - 3
    for (fx0, fy0, fx1, fy1) in ((x0, y0, x1, y0 + q(2)), (x0, y1 - q(2), x1, y1), (x0, y0, x0 + q(2), y1), (x1 - q(2), y0, x1, y1)):
        V.blk(a, fx0, fy0, fx1, fy1, 'stone_cool', 2, cut=1)
    ix0, iy0, ix1, iy1 = x0 + q(2), y0 + q(2), x1 - q(2), y1 - q(2)
    if pressed:
        V.fill(a, ix0, iy0, ix1, iy0 + 2, code('soot', 1))
        cut_block(a, ix0, iy0 + 2, ix1, iy1, iy1 - iy0 - 3, 'stone_warm', 1, rng, bevel=0, grain=False)
    else:
        cut_block(a, ix0, iy0 - q(up), ix1, iy1, iy1 - iy0 - q(up) + q(0.5), 'stone_warm', 1, rng, grain=False)
    cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2 - (0 if pressed else q(up))
    pan = np.zeros(a.shape, bool)
    pan[int(cy - q(4)):int(cy + q(4)), int(cx - q(4)):int(cx + q(4))] = True
    a[pan] = code('stone_warm', 1)
    # the sunk panel: its top and west walls in shade, its bottom and east walls catching the light
    py0, py1, px0, px1 = int(cy - q(4)), int(cy + q(4)), int(cx - q(4)), int(cx + q(4))
    a[py0:py0 + 3, px0:px1] = code('stone_warm', 0)
    a[py0:py1, px0:px0 + 3] = code('stone_warm', 0)
    a[py1 - 2:py1, px0 + 3:px1] = code('stone_warm', 3)
    a[py0 + 3:py1, px1 - 2:px1] = code('stone_warm', 3)
    star = line_mask(a.shape, [(cx, cy - q(3.4)), (cx, cy + q(3.4))], 0.7) | line_mask(a.shape, [(cx - q(3.4), cy), (cx + q(3.4), cy)], 0.7)
    star |= V.ellipse_mask(a.shape, cx, cy, q(1.2), q(1.2))
    a[star & pan] = code('dusk', 4) if pressed else code('soot', 1)
    weather(a, (a >= 0) & ~pan, rng, 2.0, moss=True)
    return V.finish(p)


def p_lever(pulled):
    """The lever: a dressed stone post (top, bevel, front, a carved slot in its top), an iron pivot
    plate bolted to its face with four rivets, an iron arm through the slot and a wooden grip bound
    with two iron bands; pulled, the arm lies down to the east."""
    V = _v()
    q, code = V.q, V.code
    rng = np.random.default_rng(11)
    W, H = q(18), q(24)
    p = V.Pic(W, H, W // 2, H - 3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(4), cx + q(4)
    cut_block(a, x0, yb - q(12), x1, yb, q(3.5), 'stone', 3, rng)
    pm = np.zeros(a.shape, bool)
    pm[yb - q(12) + 2:yb - 1, x0 + 1:x1 - 1] = True
    weather(a, pm & (a >= 0), rng, 2.0)
    V.fill(a, cx - q(0.8), yb - q(11.2), cx + q(0.8), yb - q(9.4), code('soot', 0))       # the slot
    V.fill(a, cx - q(0.8), yb - q(9.4), cx + q(0.8), yb - q(9.4) + 1, code('stone', 4))
    V.blk(a, cx - q(2.4), yb - q(8), cx + q(2.4), yb - q(3.6), 'iron', 2, cut=1)          # the pivot plate
    for dx in (-1.6, 1.2):
        for dy in (7.2, 4.6):
            V.fill(a, cx + q(dx), yb - q(dy), cx + q(dx) + 2, yb - q(dy) + 2, code('iron', 4))
    if pulled:
        arm = (cx, yb - q(10.4), cx + q(7), yb - q(6.5))
    else:
        arm = (cx, yb - q(10.4), cx - q(2.6), yb - q(19))
    V.bar(a, arm[0], arm[1], arm[2], arm[3], q(0.8), 'iron', 3)
    gx, gy = arm[2], arm[3]
    dx, dy = (gx - arm[0]), (gy - arm[1])
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    gm = V.bar(a, gx - ux * q(1), gy - uy * q(1), gx + ux * q(2.6), gy + uy * q(2.6), q(1.3), 'timber', 3)
    gl = line_mask(a.shape, [(gx - ux * q(0.8) - uy * 1.5, gy - uy * q(0.8) + ux * 1.5), (gx + ux * q(2.4) - uy * 1.5, gy + uy * q(2.4) + ux * 1.5)], 0.6) & gm
    a[gl] = code('timber', 4)
    gd = line_mask(a.shape, [(gx - ux * q(0.8) + uy * 2, gy - uy * q(0.8) - ux * 2), (gx + ux * q(2.4) + uy * 2, gy + uy * q(2.4) - ux * 2)], 1.1) & gm
    a[gd] = code('timber', 2)
    for t_ in (0.0, 1.6):
        bx, by = gx + ux * q(t_), gy + uy * q(t_)
        V.bar(a, bx - uy * q(1.3), by + ux * q(1.3), bx + uy * q(1.3), by - ux * q(1.3), 0.8, 'iron', 2)
    return V.finish(p)


def p_channel(pts, lit):
    """The channel's inlay once the plate is down: the brass strip in the carved groove glows with the
    shard's light. Rounded in section (a pale core, its lower side a tone down, a dark lip at each
    edge) and pulsing along its length between the rivets, brightest near the plate."""
    V = _v()
    q, code = V.q, V.code
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    W, H = q(x1 - x0) + 2, 10
    p = V.Pic(W, H, 1, H // 2)
    a = p.a
    c = H // 2
    for x in range(1, W - 1):
        u = x / W
        seg = (x % q(8)) / q(8)
        if seg < 0.12:                                     # a rivet: the brass shows dark between pulses
            a[c - 2:c + 2, x] = code('brass', 2)
            continue
        hot = 0.5 + 0.5 * math.sin(seg * math.pi) - 0.35 * u
        a[c - 3, x] = code('dusk', 2)
        a[c - 2, x] = code('dusk', 4)
        a[c - 1:c + 1, x] = code('dusk', 5 if hot > 0.45 else 4)
        a[c + 1, x] = code('dusk', 3)
        a[c + 2, x] = code('dusk', 2 if hot < 0.6 else 3)
    return p

def p_cairn_alcove(seed):
    """Cairn asleep in the wall: his slumped drawing (the cast's last defeat frame) brought onto the
    house ramps a step into shade, half sunk behind the masonry and earth that grew over his legs."""
    V = _v()
    q, code = V.q, V.code
    from scripts.art.native import palette as PAL
    rng = np.random.default_rng(seed)
    src = np.asarray(Image.open(CAIRN).convert('RGBA'))[:, -160:]
    ys, xs = np.nonzero(src[..., 3] > 0)
    src = src[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    fam_for = {}
    names = ['stone', 'stone_cool', 'leaf', 'leaf_cool', 'lamp', 'brass', 'void', 'soot']
    pal = [(f, t, np.array(PAL.rgb(f, t), float)) for f in names for t in range(6)]
    h, w = src.shape[:2]
    scale = ctx.D / 3.0
    sh, sw = max(1, int(round(h * scale))), max(1, int(round(w * scale)))
    if (sh, sw) != (h, w):
        src = np.asarray(Image.fromarray(src, 'RGBA').resize((sw, sh), Image.NEAREST))
    pad = q(4)
    W, H = sw + 2 * pad, sh + pad
    p = V.Pic(W, H, W // 2, H - 1)
    a = p.a
    for y in range(sh):
        for x in range(sw):
            px = src[y, x]
            if px[3] == 0:
                continue
            key = tuple(int(v) for v in px[:3])
            if key not in fam_for:
                c = np.array(key, float)
                f, t, _ = min(pal, key=lambda e: ((e[2] - c) ** 2).sum())
                fam_for[key] = V.code(f, max(0, t - 2) if f not in ('lamp', 'brass') else 1)
            a[y, x + pad] = fam_for[key]
    # his moss in clumps: soft clusters a tone up and down, lit on top
    lf = (a // 8 == V.FI['leaf']) | (a // 8 == V.FI['leaf_cool'])
    nz = ndi.gaussian_filter(rng.random(a.shape), 1.3)
    nz = (nz - nz[lf].mean()) / (nz[lf].std() + 1e-9) if lf.any() else nz
    up_ = lf & (nz > 0.6)
    dn_ = lf & (nz < -0.6)
    a[up_] = np.minimum(a[up_] + 1, (a[up_] // 8) * 8 + 5)
    a[dn_] = np.maximum(a[dn_] - 1, (a[dn_] // 8) * 8)
    # half sunk: masonry and earth over his lower third
    cover = int(sh * 0.36)
    yb = H - 1
    m = np.zeros(a.shape, bool)
    m[yb - cover:yb + 1, :] = True
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    m &= (Y >= yb - cover + (np.sin(X / q(3)) * q(1.5)).astype(int))
    V.rubble(a, 0, yb - cover - q(2), W, yb + 1, rng, fams=STONES, base=2, course=(2.6, 3.6), length=(4, 8), moss=0.5,
             east_dark=True, where=m, mortar=('earth_cool', 1))
    turf = m & ~np.roll(m, q(2.5), 0)
    a[turf] = code('leaf_cool', 2)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    blades = turf & ((X // 2) % 3 == 0)                      # tufts: blades a tone up and down in clusters
    a[blades] = code('leaf_cool', 3)
    a[turf & ((X // 2) % 5 == 2)] = code('leaf_cool', 1)
    a[turf & ~np.roll(turf, 1, 0)] = code('leaf', 3)          # the lit tips
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
def build(plan: dict, out_dir: str, preview: str | None = None) -> dict:
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
    blot = ndi.gaussian_filter(rng.random((H, W)), q(9))
    blot = (blot - blot.mean()) / (blot.std() + 1e-9)
    fvar = np.where(blot > 1.3, 1 - fvar, fvar)                           # a few large soft blotches
    wn = ndi.gaussian_filter(rng.random((H, W)), q(0.9))
    fvar = np.where(wn > np.quantile(wn, 0.76), 1 - fvar, fvar)           # worn patches inside the flags
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
    for wl in plan['walls']:
        x, y, w, h = wl['rect']
        f = wl.get('face', 0)
        if f:
            fm = rmask([x, y + h - f, w, f])
            wall_face(cv, q(x), q(y + h - f), q(x + w), q(y + h), rng, fm, roots=[q(r) for r in wl.get('roots', [])],
                      arcade=w >= 40)
            if wl.get('alcove'):
                ax = q(wl['alcove'])
                ay0, ay1 = q(y + h - f) + q(4), q(y + h) - q(1)
                rad = q(14)
                al = ((((WX * D - ax) ** 2 + (WY * D - (ay0 + rad)) ** 2) <= rad * rad) & (WY * D < ay0 + rad)) | \
                     ((np.abs(WX * D - ax) < rad) & (WY * D >= ay0 + rad) & (WY * D < ay1))
                al &= fm
                V.rubble(cv, ax - rad, ay0, ax + rad, ay1, rng, fams=STONES, base=0, course=(2.4, 3.2), length=(3, 6),
                         moss=0.3, east_dark=False, where=al, mortar=('void', 0))
                rim = ndi.binary_dilation(al, iterations=q(2)) & ~al & fm
                cv[rim & (WX * D < ax)] = code('stone', 4)
                cv[rim & (WX * D >= ax)] = code('stone', 2)
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
    weather(cv, band & ~far & ~jnt, rng, 0.7, moss=False, lichen=False)
    cv[jnt & (dist > 2) & ~far] = code('void', 1)
    # the south wall's outer face below its coping: the wall's thickness, seen as Eastward cuts it away
    souter = cap & (WY >= by + bh - 9)
    masonry(cv, 0, q(by + bh - 9), W, H, rng, souter, base=2, course=3.0, length=(6, 10), east_dark=False)
    cv[souter & (WY < by + bh - 9 + 1 / D * 2)] = code('stone_cool', 0)
    cv[souter & (WY >= by + bh - 1.2)] = code('void', 0)
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
    fshade += np.clip(-(vn - 0.5) * 1.2, -0.25, 0.25)                 # the soft blotches of damp and dust
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
    fmat[patch] = 3
    foff[patch] = 0                                                  # the grit lies over the joints
    grit = floor & (rng.random((H, W)) < 0.0012 + 0.004 * (dfl <= q(12))) & (fmat != 2)
    grit = ndi.binary_dilation(grit, structure=np.ones((2, 2)))
    foff[grit & (fmat == 0)] = 1                                     # small lit stones: a rung up
    east_edge = walls_m & ~np.roll(walls_m, -1, 1)
    east_sh = np.zeros((H, W), bool)
    for k in range(1, q(4) + 1):
        east_sh |= np.roll(east_edge, k, 1)
    fshade[east_sh & floor & ~outer] += 0.6

    # --- the plate's channel, carved (its glow is an overlay) -------------------------------
    pz = plan.get('puzzle', {})
    fixed = np.zeros((H, W), bool)
    if pz.get('channel'):
        (x0, y0), (x1, y1) = pz['channel'][0], pz['channel'][-1]
        gy = q(y0)
        gx0, gx1 = q(x0), q(x1)
        fixed[gy - q(3):gy + q(3) + 2, gx0:gx1] = True
        cv[gy - q(3):gy + q(3), gx0:gx1] = code('stone_cool', 1)          # the groove's floor
        cv[gy - q(3):gy - q(3) + 5, gx0:gx1] = code('stone_cool', 0)      # its north wall, deep in shade
        cv[gy + q(3) - 3:gy + q(3), gx0:gx1] = code('stone', 4)           # its south wall, lit
        cv[gy + q(3):gy + q(3) + 2, gx0:gx1] = code('stone', 3)
        # the groove was cut by hand: its lit wall is chipped and worn in places, not one ruled stroke
        crng = np.random.default_rng(41)
        k = gx0 + int(crng.integers(6, 14))
        while k < gx1 - 4:
            L = int(crng.integers(3, 8))
            cv[gy + q(3) - 3:gy + q(3) - 1, k:k + L] = code('stone', 3)
            cv[gy + q(3):gy + q(3) + 2, k + 1:k + L + 2] = code('stone', 2)
            k += L + int(crng.integers(10, 22))
        cv[gy - 3:gy + 3, gx0:gx1] = code('brass', 1)                      # the inlay, dull until charged
        cv[gy - 3:gy - 1, gx0:gx1] = code('brass', 2)
        for k in range(gx0 + q(8), gx1, q(8)):
            cv[gy - 3:gy + 3, k:k + 2] = code('brass', 3)                  # its rivets

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
            for k in range(6):
                ang = k * math.pi / 3 + 0.4
                pts = [(q(x), q(y))]
                for s in range(1, 4):
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
        dt = np.hypot((WX - tx) / 46, (WY - ty - 22) / 38) + nz * 0.15
        # the pool's heart (up to rung 4 to 5) and its wide spill (a rung over the room's shade)
        lt = 5.0 * np.clip(1 - dt, 0, 1) ** 1.6 + 1.1 * np.clip(1 - dt / 2.2, 0, 1) ** 0.9
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
        lf_cool = 3.4 * np.clip(1 - ds, 0, 1) ** 1.4 + 1.1 * np.clip(1 - ds / 2.2, 0, 1) ** 0.9
    if plan.get('stair'):
        sx, sy, sw, sh = plan['stair']['rect']
        d = np.hypot((WX - sx - sw) / 40, (WY - sy - sh / 2) / 24)
        lightv = np.maximum(lightv, np.where(d < 0.5, 1, np.where(d < 1.2, 0, -1)))
        lf = np.maximum(lf, 2.2 * np.clip(1 - (d / 1.6 + nz * 0.3), 0, 1))
    lightv[stair] = 0
    lightv = np.clip(ndi.median_filter(lightv, size=5), -1, 2)
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
    fcool = lf_cool > lf
    lf = np.maximum(lf, lf_cool)
    fwarm = (lf_warm >= lf) & (lf_warm > 1.6)
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
                                foot=(q(wl['alcove']), q(y + h) - q(1)), anchor=(pic.ax, pic.ay), alpha=None, cond=None,
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
        pic = p_channel(pz['channel'], True)
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
            fshade[sel] += 1.2 * (1 - e[sel]) ** 0.5
    # --- the floor painted: light minus shade, flag by flag ----------------------------------------
    # Each flag takes the light at its middle (a little jitter, so the steps are few and irregular and
    # follow the stones, as Eastward's 06); the joints stay dark, rising only slowly in a pool.
    level = FLOOR_AMBIENT + lf - fshade
    level -= 0.6 * np.clip(1 - lf / 0.9, 0, 1)            # far from every light the floor sinks towards the dark
    rung = np.clip(np.floor(level + 0.5).astype(int), 0, 6)
    if nflags:
        with np.errstate(invalid="ignore"):
            fl = np.nan_to_num(ndi.mean(level, labels=slab, index=np.arange(1, nflags + 1)), nan=1.0)
        fj = np.random.default_rng(93).uniform(-0.3, 0.3, nflags)
        fr = np.concatenate([[0], np.clip(np.floor(fl + fj + 0.5).astype(int), 0, 6)])
        rung[slab > 0] = fr[slab[slab > 0]]
    jl = FLOOR_AMBIENT + 0.45 * lf - fshade - 0.6 * np.clip(1 - lf / 0.9, 0, 1)
    jr = np.clip(np.floor(jl + 0.5).astype(int), 0, 4)
    nb = ndi.grey_erosion(np.where(slab > 0, rung, 9), size=(3, 3))      # the darkest flag beside the joint
    jt = (slab == 0) & floor
    rung[jt] = np.minimum(jr[jt], np.maximum(0, nb[jt] - 1)) + 1          # +1: floor_codes takes the joint's -1
    # arrises catch the light only inside a pool: a flag's top and west edge a rung up, here and there
    top_l = (slab > 0) & (np.roll(fjoint, 1, 0) | np.roll(fjoint, 1, 1)) & (foff == 0)
    arris = top_l & (rung >= 4) & (np.random.default_rng(92).random((H, W)) < 0.35)
    off = foff + arris.astype(int)
    # a lit flag shows its wear: worn patches on its sibling stone and a few more pits, so a pool's
    # flags are lit stone, not flat tiles
    lit_f = (slab > 0) & (rung >= 3)
    wl = ndi.gaussian_filter(np.random.default_rng(94).random((H, W)), q(1.1))
    fvar = np.where(lit_f & (wl > np.quantile(wl, 0.55)), 1 - fvar, fvar)
    pit = lit_f & (np.random.default_rng(95).random((H, W)) < 0.006) & (foff == 0)
    pit = ndi.binary_dilation(pit, structure=np.ones((2, 2))) & lit_f
    off[pit] = -1
    paint = floor & ~outer & ~fixed
    fc = floor_codes(rung, off, fmat, fvar, fcool, fwarm)
    cv[paint] = fc[paint]
    break_runs(cv, cv >= 0, np.random.default_rng(77))
    V.tidy(cv, passes=2, keep=(cv % 8 >= 6))
    ground = Image.fromarray(to_rgba(cv), 'RGBA').convert('RGB')

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
