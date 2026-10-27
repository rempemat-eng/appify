"""A zone at density 2 from a plan and a biome: its layers, all through palette codes.

    ctx.configure(2.0, biome, plan)
    from scripts.art.native import screen
    z = screen.build()
    z.ground        RGBA texels: lawn, paths, places, light, water, rock, shadows, low plants
    z.objects       [(id, kind, (x, y, w, h) world px)]: each object's native picture's box,
                    its foot where the zone's own object stands (so walk and depth are unchanged)
    z.sprites       kind -> RGBA texels (one picture per kind, as the 1x zone has)
    z.flow          (sheet, (x, y, w, h) texels, cols) of the moving water, or None
    z.night         RGBA texels of the night light, or None (the woodland makes none)
    z.layers        name -> RGBA texels: terrain, water, shadows, light, plants (for review)

Nothing here belongs to one zone: the plan says where (today's geometry for a zone that keeps
its walk mask), the biome says how (recipes per kind, lawn, shadow, palette). The terrain is
the c-tiles lawn (terrain.scene.render on a flat plan); paths are scene.worn2; water is
water.paint on the plan's footprint; rocks are decals.lump_px; plants and props are the
kit's painters (foliage from the 1x masters, props, the one shadow rule in compose).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import ctx
from . import animate
from . import compose as CO
from . import props as P4
from . import water as WA
from .ctx import D, P
from .palette import C, FI, is_fam, sib, step
from .terrain import decals as DC
from .terrain import scene as SC
from .terrain import tiles as TL

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MASTERS = os.path.join(ROOT, 'art', 'masters')
TREES = ('tree',)


@dataclass
class Zone:
    ground: Image.Image
    objects: list
    sprites: dict
    flow: object
    night: object
    layers: dict = field(default_factory=dict)
    codes: np.ndarray | None = None


def mask_rle(rows, w, h) -> np.ndarray:
    """A world px mask from per-row runs [x0, x1, x0, x1, ...]."""
    m = np.zeros((h, w), bool)
    for y, row in enumerate(rows):
        for a, b in zip(row[0::2], row[1::2]):
            m[y, a:b] = True
    return m


def texels(m: np.ndarray) -> np.ndarray:
    k = int(D)
    return np.kron(m, np.ones((k, k), bool)).astype(bool)


def blob(cx, cy, rx, ry, seed=0, rough=0.18, w=None, h=None) -> np.ndarray:
    """An organic closed shape at texels: an ellipse whose radius wanders with the angle (the
    zones' blob, valley_zones.blob, drawn at density)."""
    import sys
    art = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if art not in sys.path:
        sys.path.insert(0, art)
    from pixel import noise2
    ph = [noise2(seed, k, 771) * 6.283 for k in range(4)]
    H, W = h, w
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = ((xx + 0.5) / D - cx) / rx, ((yy + 0.5) / D - cy) / ry
    a = np.arctan2(dy, dx)
    r = 1 + rough * (0.55 * np.sin(2 * a + ph[0]) + 0.35 * np.sin(3 * a + ph[1]) + 0.2 * np.sin(5 * a + ph[2])
                     + 0.1 * np.sin(8 * a + ph[3]))
    return dx * dx + dy * dy <= r * r


# ------------------------------------------------------------------------------------------------
# light: sun pools on the lawn
# ------------------------------------------------------------------------------------------------
def sun(cv: np.ndarray, m: np.ndarray, heart: float = 10.0, fade: float = 4.0, soft: bool = False) -> None:
    """A sun pool: the lawn's warm sibling at its own tone, the heart (`heart` texels in) a tone
    up, a 2 x 2 checker `fade` texels wide at the edge (the one place dither is used: light).
    `soft` (the soft grid's two-hue lawn): every hue moves one step warmer (cool to body, body to
    warm, warm a tone up), so the lawn's blobs and mottle still show in the sun."""
    lawn = m & (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)
    dist = ndi.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]
    yy, xx = np.mgrid[0:cv.shape[0], 0:cv.shape[1]]
    chk = ((xx // 2 + yy // 2) % 2) == 0
    sel = lawn & ((dist > fade) | chk)
    if soft:
        from .palette import FI
        cool = np.isin(cv // 8, [i for n, i in FI.items() if n in ('grass_cool', 'leaf_cool')])
        warm = np.isin(cv // 8, [i for n, i in FI.items() if n in ('grass_warm', 'leaf_warm')])
        a, b, c = sel & cool, sel & warm, sel & ~cool & ~warm
        cv[a] = sib(cv[a], 'body')
        cv[b] = np.minimum(cv[b] + 1, cv[b] - cv[b] % 8 + 5)
        cv[c] = sib(cv[c], 'warm')
        return
    cv[sel] = sib(cv[sel], 'warm')
    up = lawn & (dist > heart)
    cv[up] = step(cv[up], 1)


# ------------------------------------------------------------------------------------------------
# rock
# ------------------------------------------------------------------------------------------------
def boulder(cv: np.ndarray, cx, base, w, h, seed, moss=True, fams=('stone', 'stone_warm', 'stone_cool')) -> None:
    """A stone lying on the ground (cx, base, w, h world px): the kit's pixel-art stone
    (decals.lump_px) with its contact shadow, a moss cushion on its crown when `moss`."""
    lp = DC.lump_px(P(w), P(h), seed, fams=fams)
    X, Y = P(cx - w / 2, -10 ** 6), P(base - h, -10 ** 6)
    if moss:
        hh, ww = lp.shape
        rng = np.random.default_rng(seed + 5)
        yy, xx = np.mgrid[0:hh, 0:ww]
        u, v = (xx - (ww - 1) / 2) / (ww / 2), (yy - (hh - 1) / 2) / (hh / 2)
        top = (lp >= 0) & (v < -0.35 + 0.15 * np.sin(u * 5 + rng.uniform(0, 6))) & (np.abs(u) < 0.75)
        top &= (lp % 8 >= 2) & (lp % 8 < 6)
        lp[top] = np.where(u[top] + v[top] < -0.75, C('leaf', 4), C('leaf', 3))
        under = np.zeros_like(top)
        under[1:] = top[:-1]
        under &= ~top & (lp >= 0) & (lp % 8 < 6)
        lp[under] = C('leaf', 2)
    DC.paste(cv, lp, X, Y, shadow=True, shadow_dx=P(2), shadow_dy=P(1))


def scree(cv: np.ndarray, depth, avoid: np.ndarray, seed=1612) -> None:
    """The talus along the top edge: a calm gravel band (the ledge floor's dirt, a tone down)
    with a soft lower edge, and pebbles of 2 to 4 world px lying in it in drifts that thin
    away from the face, each the kit's pixel-art stone with its contact shade."""
    import sys
    art = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if art not in sys.path:
        sys.path.insert(0, art)
    from pixel import noise2, smooth_noise
    H, W = cv.shape
    k = int(D)
    yy, xx = np.mgrid[0:H, 0:W]
    dep = np.array(depth, float)[np.clip(xx // k, 0, len(depth) - 1)]
    wob = np.array([[smooth_noise(x, y, 5, seed + 2) for x in range(W // k)] for y in range(H // k)])
    wobt = np.kron(wob, np.ones((k, k)))[:H, :W]
    band = (yy / D < dep * (0.75 + 0.35 * wobt)) & ~avoid & (cv >= 0)
    if D >= HD:      # density 3: the band's lower edge on the soft grid (softedge)
        from . import softedge as SE
        band = SE.soft(band, smooth=1.3) & ~avoid & (cv >= 0)
    sheet = TL.SHEETS['path']
    fill = sheet[np.ix_(np.arange(H) % sheet.shape[0], np.arange(W) % sheet.shape[1])]
    cv[band] = step(fill[band], -1)
    edge = band & ~ndi.binary_erosion(band, iterations=max(1, int(D)))
    cv[edge & (cv % 8 < 6)] = step(cv[edge & (cv % 8 < 6)], -1)
    for x in range(1, len(depth) - 2, 2):
        for y in range(1, depth[x] - 2, 2):
            t = y / depth[x]
            if noise2(x, y, seed) < 0.62 + t * 0.3 or avoid[min(H - 1, y * k), min(W - 1, x * k)]:
                continue
            s_ = 2.0 + 2.4 * noise2(x, y, seed + 3) * (1 - t)
            lp = DC.lump_px(P(s_ * 1.2), P(s_), int(seed * 31 + x * 7 + y), fams=('stone', 'stone_warm', 'stone_cool'))
            DC.paste(cv, lp, x * k, y * k, shadow=True, shadow_dx=P(1), shadow_dy=P(0.5))


# ------------------------------------------------------------------------------------------------
# places
# ------------------------------------------------------------------------------------------------
def trodden(cv: np.ndarray, m: np.ndarray) -> None:
    """Trodden earth (the worn track's dirt) on a mask, a damp row along its edge."""
    sheet = TL.SHEETS['trail']
    H, W = cv.shape
    ys, xs = np.arange(H), np.arange(W)
    fill = sheet[np.ix_(ys % sheet.shape[0], xs % sheet.shape[1])]
    cv[m] = step(fill[m], -1)
    edge = m & ~ndi.binary_erosion(m, iterations=max(1, int(D)))
    cv[edge] = step(cv[edge], -1)


def footbridge(cv: np.ndarray, x0, w, y0, y1, water: np.ndarray) -> None:
    """A plank footbridge over a stream (world px): planks laid across, lit along their top
    edge, joints in shade, a lit west rail and a shaded east rail on posts, dressed stone
    abutments, its shadow on the water east of it."""
    H, W = cv.shape
    X0, X1, Y0, Y1 = P(x0, 0), P(x0 + w, 0), P(y0, 0), P(y1, 0)
    for Y in range(max(0, Y0 + P(4) - 1), min(H, Y1 + P(6))):          # its shadow on the water
        for X in range(X1 + P(1), min(W, X1 + P(3))):
            if water[Y, X]:
                cv[Y, X] = step(cv[Y:Y + 1, X:X + 1], -2)[0, 0]
    for Y in range(Y0 - P(3), Y0):                                     # the north abutment
        for X in range(X0 - P(3), X1 + P(3)):
            if 0 <= Y < H and 0 <= X < W and not water[Y, X]:
                cv[Y, X] = C('stone', 3 if (Y - Y0) > -P(1) else 2) if (X // P(4) + Y // P(1)) % 5 else C('stone', 1)
    for Y in range(Y1, Y1 + P(4)):                                     # the south abutment, its face lit
        for X in range(X0 - P(3), X1 + P(3)):
            if 0 <= Y < H and 0 <= X < W:
                r = (Y - Y1) / D
                c = C('stone', 4) if r < 1 else (C('stone', 3) if (X // P(5) + int(r) // 2) % 4 else C('stone', 2))
                cv[Y, X] = C('stone', 1) if r >= 3 else c
    pw = 3.0
    k = 0
    y = float(y0)
    while y < y1 - 0.01:
        ya, yb = P(y, 0), P(min(y1, y + pw), 0)
        for Y in range(ya, yb):
            for X in range(X0, X1):
                if not (0 <= Y < H and 0 <= X < W):
                    continue
                rr = (Y - ya) / D
                t = 4 if rr < 1 else (3 if rr < 2 else 1)
                if t == 3 and ((X // P(3) + k) % 7 == 0):
                    t = 2                                              # grain
                cv[Y, X] = C('timber', t)
            for nx in (X0 + P(1), X1 - P(1) - 1):                      # nails over the stringers
                if 0 <= ya + P(1) < H:
                    cv[ya + P(1), nx] = C('stone', 1)
        y += pw
        k += 1
    for (rx, lit) in ((X0 - P(1), True), (X1, False)):                 # the rails on their posts
        for Y in range(Y0 - P(4), Y1 - P(1)):
            for j in range(P(1)):
                if 0 <= Y < H and 0 <= rx + j < W:
                    cv[Y, rx + j] = C('timber', 4 if lit else 2) if j == 0 else C('timber', 3 if lit else 1)
        for py in (y0 - 1, (y0 + y1) / 2, y1 - 1):
            for Y in range(P(py - 4, 0), P(py, 0)):
                for j in range(-P(0.5), P(1) + P(0.5)):
                    if 0 <= Y < H and 0 <= rx + j < W:
                        cv[Y, rx + j] = C('timber', 3 if lit else 1)


# ------------------------------------------------------------------------------------------------
# density 3 and up (25 Oct, Matt on the woodland at density 3: "this scene needs to be improved
# almost everywhere"): the water's footprint with natural banks and a source that reads, a real
# footbridge, the pilot's boulders, mushrooms at a stump, ferns and foxgloves, a calmer lawn
# ------------------------------------------------------------------------------------------------
HD = 2.5


def to_codes(img) -> np.ndarray:
    """An RGBA picture drawn on the house palette as a decal in palette codes (-1 clear)."""
    from .palette import LUT
    a = np.asarray(img)
    out = np.full(a.shape[:2], -1, np.int32)
    m = a[..., 3] > 0
    cols = a[m][:, :3].astype(int)
    uniq, inv = np.unique(cols, axis=0, return_inverse=True)
    L = LUT.astype(int)
    codes = np.array([int(((L - c) ** 2).sum(1).argmin()) for c in uniq])
    out[m] = codes[inv.ravel()]
    return out


def water_mask_soft(plan: dict, W: int, H: int) -> np.ndarray:
    """The woodland's water on the soft grid (Matt, 27 Oct: "is there any water in eastward that you
    can use as inspiration"; Eastward 13's canal, 37's pond): the river a channel of whole cells
    and steady width, the fall's pool a rounded union of cells under the lip, both one outline with
    rounded corners (softgrid.shape); the rill a narrow channel of steady width coming down from
    the top edge in long rounded bends (softgrid.curve_texels) to the fall's lip. Texels."""
    from . import softgrid as SG
    sw = plan['water']['soft']
    h, w = int(H * D), int(W * D)
    cells = np.zeros(SG.grid_shape(h, w), bool)
    r = sw['river']
    cells |= SG.cells_route(r['points'], r['cells'], h, w)
    cells |= SG.cells_rects(sw['pool'], h, w)
    # (Matt, 27 Oct: "not a ruler") a few rounded cell-steps: the river widens and narrows by a
    # cell and bends gently; the banks lumped 2 to 5 px over 10 to 26 px as natural water is
    cells |= SG.cells_rects(r.get('add', []), h, w)
    cells &= ~SG.cells_rects(r.get('cut', []), h, w)
    lump = dict(amp=tuple(sw.get('amp', SG.AMP)), lump=tuple(sw.get('lump', SG.LUMP)))
    m = SG.shape(cells, h, w, sw.get('seed', 402), r_out=1.3, r_in=0.6, **lump)
    rl = sw['rill']
    m |= SG.curve_texels(rl['points'], rl['cells'], h, w, rl['bend'], sw.get('seed', 402) + 1, rl.get('share', 0.95),
                         rl.get('breathe', 0.0), amp=tuple(rl.get('amp', (0.0, 0.0))))
    if rl.get('mouth'):
        # wider where it meets the fall's lip
        m |= SG.shape(SG.cells_rects([rl['mouth']], h, w), h, w, sw.get('seed', 402) + 2, r_out=1.0, r_in=0.6, **lump)
    return m


def ledge(cv: np.ndarray, x0: float, w: float, y: float) -> None:
    """The fall's lip (world px): a flat stone ledge across the top of the rocks, its top lit, its
    front a narrow face in shade, worn smooth and wet where the water spills over its middle."""
    X0, X1 = P(x0 - 9, 0), P(x0 + w + 9, 0)
    Y0 = P(y, 0)
    th, fh = P(2.0), P(1.6)
    for Y in range(Y0 - th, Y0 + fh):
        for X in range(X0, X1):
            if not (0 <= Y < cv.shape[0] and 0 <= X < cv.shape[1]):
                continue
            edge = X in (X0, X1 - 1)
            if Y < Y0:
                t = 5 if (Y == Y0 - th and X < (X0 + X1) // 2) else (4 if X < X1 - P(2) else 3)
                fam = 'stone_warm' if t >= 4 else 'stone'
            else:
                t, fam = (2 if X < X1 - P(2) else 1), 'stone_cool'
            if edge:
                t, fam = (1, 'stone_cool')
            cv[Y, X] = C(fam, t)
    for X in range(X0, X1, P(4)):                                     # joints between the slabs
        if 0 <= Y0 < cv.shape[0] and X0 < X < X1 - 1:
            cv[Y0 - th:Y0 + fh, X] = C('stone_cool', 1)


def water_mask_hd(plan: dict, W: int, H: int) -> np.ndarray:
    """The water's footprint at this density from the 1x one: specks dropped, the river carried
    on under the footbridge, the rill run on between the boulders to the fall's lip (so the
    water visibly comes down from the top edge, over the lip, into the pool and out to the
    river), the rill meandering gently (a texel-smooth sway, at most 1.8 world px), and every
    bank softened to a curve (water.smooth_mask). The walk mask is the zone's own and unchanged."""
    m1 = mask_rle(plan['water']['water_rle'], W, H)
    lab, n = ndi.label(m1)
    if n:
        sizes = ndi.sum(m1, lab, range(1, n + 1))
        m1 = np.isin(lab, 1 + np.nonzero(sizes >= 6)[0])
    # bites out of the banks (reed cells, stray rows) close; the reeds stand in the water
    m1 = ndi.binary_fill_holes(ndi.binary_closing(np.pad(m1, 6), structure=np.ones((5, 5), bool)))[6:-6, 6:-6] | m1
    br = plan['places']['bridge']
    x0, x1 = int(br['x0']) - 8, int(br['x0'] + br['w']) + 8
    y0, y1 = int(br['y0']) - 2, int(br['y1']) + 6
    box = m1[y0:y1, x0:x1]
    m1[y0:y1, x0:x1] = ndi.binary_closing(np.pad(box, ((0, 0), (12, 12)), mode='edge'),
                                          structure=np.ones((1, 25), bool))[:, 12:-12] | box
    f = plan['water']['fall']
    rows = []
    for y in range(int(f['y0']) - 40, int(f['y0'])):     # the rill's last rows above the heap
        if m1[y].sum() >= 3:
            rows.append(y)
        elif rows:
            break
    if rows:
        ya = rows[-1]
        xs_ = np.nonzero(m1[ya])[0]
        xa, xb = (xs_.min() + xs_.max() + 1) / 2.0, f['x0'] + f['w'] / 2.0
        for y in range(ya, int(f['y0']) + 2):
            t = (y - ya) / max(1, f['y0'] - ya)
            xc = xa + (xb - xa) * t * t
            m1[y, int(round(xc - 2.2)):int(round(xc + 2.2)) + 1] = True
    # the rill (from the top edge to the heap) is redrawn as a meandering brook: its 1x centre
    # line swings up to 3 world px either side and its width breathes between 0.7 and 1.5 of
    # the 1x width, both fading out at the top edge and where it reaches the stones
    yend = int(f['y0']) if rows else 230     # the brook runs on through the channel to the lip
    cx1, hw1 = {}, {}
    prev = None
    for y in range(yend, -1, -1):              # follow the rill's own run up to the top edge
        row = np.concatenate([[False], m1[y, :110], [False]]).astype(int)
        dd = np.diff(row)
        runs = list(zip(np.nonzero(dd == 1)[0], np.nonzero(dd == -1)[0]))
        if not runs:
            continue
        if prev is None:
            a0, b0 = max(runs, key=lambda r: r[1] - r[0])
        else:
            a0, b0 = min(runs, key=lambda r: abs((r[0] + r[1]) / 2.0 - prev))
            if abs((a0 + b0) / 2.0 - prev) > 6:
                continue
        if b0 - a0 >= 2 and b0 - a0 <= 9:
            cx1[y], hw1[y] = (a0 + b0) / 2.0, (b0 - a0) / 2.0
            prev = cx1[y]
    k = int(round(D))
    up = np.kron(m1.astype(float), np.ones((k, k)))
    if len(cx1) > 20:
        ys1 = np.array(sorted(cx1))
        for y in cx1:                          # the 1x rill out, the brook in
            up[int(y * D):int((y + 1) * D), int((cx1[y] - hw1[y] - 1) * D):int((cx1[y] + hw1[y] + 1) * D)] = 0.0
        Xw = (np.arange(up.shape[1]) + 0.5) / D
        for Y in range(int(ys1.min() * D), int((yend + 1) * D)):
            yw = (Y + 0.5) / D
            c = np.interp(yw, ys1 + 0.5, [cx1[y] for y in ys1])
            hw = np.interp(yw, ys1 + 0.5, [hw1[y] for y in ys1])
            taper = float(np.clip(min(0.5 + yw / 16.0, (yend - yw) / 14.0), 0, 1))
            c += taper * (4.2 * np.sin(yw / 21.0 + 0.4) + 2.4 * np.sin(yw / 5.6 + 0.2) + 0.8 * np.sin(yw / 3.1 + 0.3))
            hw *= 1.0 + taper * (0.3 * np.sin(yw / 11.0 + 1.3) + 0.15 * np.sin(yw / 4.3))
            # the banks' small irregularity (stones, roots, a bitten edge), so no diagonal reads as a
            # regular staircase of steps
            # (#288 second review: a per-row jitter read as a run of 45-degree zigzags; the
            # irregularity is now a slow wander, a few world px long, so the rill meanders)
            c += 0.35 * np.sin(yw / 1.9 + 1.1) * np.sin(yw / 7.3) + 0.8 * np.sin(yw / 4.4 + 2.0)
            hw += 0.25 * np.sin(yw / 2.7 + 0.5) * np.sin(yw / 9.1 + 2.0)
            up[Y, :int(110 * D)] = np.maximum(up[Y, :int(110 * D)], np.clip(hw + 0.5 - np.abs(Xw[:int(110 * D)] - c), 0, 1))
    # the river sways a little too (no ruler-straight reach): its columns east of the bridge move
    # up and down by up to 1.6 world px
    x_a = int((br["x0"] + br["w"] + 3) * D)
    y_a, y_b = int((br['y0'] - 30) * D), int((br['y1'] + 30) * D)
    # (26 Oct, fix queue: the reach just east of the bridge still ran as a straight diagonal
    # channel, both banks parallel.) Each bank now sways on its own, so the river narrows over a
    # shoal and widens into a slack pool as a stream does, and a slower bend is added
    yy_ = np.arange(y_a, y_b)
    for X in range(x_a, up.shape[1]):
        xw = X / D
        fade = min(1.0, (xw - x_a / D) / 5.0)
        sh = fade * D * (2.2 * np.sin(xw / 13.0 + 0.8) + 2.0 * np.sin(xw / 6.1 + 2.1) + 2.6 * np.sin(xw / 23.0 + 2.6))
        col = up[y_a:y_b, X]
        if col.sum() < 1:
            up[y_a:y_b, X] = ndi.shift(col, sh, order=1, mode='nearest')
            continue
        mid = float((col * yy_).sum() / col.sum())
        dw = fade * D * (1.5 * np.sin(xw / 8.3 + 0.4) + 0.8 * np.sin(xw / 3.9 + 1.7))
        top = ndi.shift(col, sh - dw, order=1, mode='nearest')
        bot = ndi.shift(col, sh + dw, order=1, mode='nearest')
        up[y_a:y_b, X] = np.where(yy_ < mid + sh, top, bot)
    soft = ndi.gaussian_filter(up, 0.9 * D)
    # a bitten, uneven edge (roots, stones, slumped turf): a small noise on the soft edge so a
    # diagonal bank never reads as a staircase of equal steps
    rn = np.random.default_rng(4423).random(soft.shape)
    wob = ndi.gaussian_filter(rn, 1.6 * D)
    wob = (wob - wob.mean()) / max(1e-6, wob.std())
    band = (soft > 0.08) & (soft < 0.92)
    m = np.where(band, soft + 0.45 * wob, soft) > 0.5
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, 1 + np.nonzero(sizes >= 6 * D * D)[0])
    return m[:H * k, :W * k]


def footbridge_hd(cv: np.ndarray, x0, w, y0, y1, water: np.ndarray) -> None:
    """A plank footbridge at density 3 and up (world px): it spans the water from bank to bank,
    its ends resting on dressed stone abutments set into both banks; the deck's planks laid
    across, each lit along its top edge, a dark joint between, ragged ends; two kerb beams along
    its sides and a hand rail on posts on each side (the west lit, the east in shade); the side
    beam's face and the deck's shadow on the water east of it; the path meets it at both ends."""
    H, W = cv.shape
    wr = np.nonzero(water[:, P(x0 + w / 2, 0)])[0]
    wr = wr[(wr >= P(y0 - 10, 0)) & (wr <= P(y1 + 10, 0))]
    ya_w, yb_w = (wr.min() / D, (wr.max() + 1) / D) if len(wr) else (y0, y1)
    ya, yb = ya_w - 4.0, yb_w + 3.0                    # the deck reaches 3 to 4 px onto each bank
    X1, Y0, Y1 = P(x0 + w, 0), P(ya, 0), P(yb, 0)
    rng = np.random.default_rng(int(x0 * 13 + y0))

    def put(Y, X, c):
        if 0 <= Y < H and 0 <= X < W:
            cv[Y, X] = c
    # the abutments: dressed stone under each end, wider than the deck, their faces to the south
    for (ay, face) in ((ya_w - 2.5, True), (yb_w - 1.0, True)):
        for Y in range(P(ay, 0), P(ay + 3.5, 0)):
            for X in range(P(x0 - 2.5, 0), P(x0 + w + 2.5, 0)):
                r = (Y / D - ay)
                course = int(r // 1.75)
                joint = ((X / D - x0 + 3 * course) % 4.0) < 1.0 / D
                c = C('stone', 4) if r < 0.7 else (C('stone', 1) if (joint or (r % 1.75) < 1.0 / D) else C('stone', 3 - course % 2))
                if X > P(x0 + w + 1.0, 0):
                    c = c - 1 if c % 8 > 1 else c
                put(Y, X, c)
    # the shadow of the deck on the water east and south of it
    for Y in range(Y0 + P(2), Y1 + P(1)):
        for X in range(X1 + P(1.5), X1 + P(4.5)):
            if 0 <= Y < H and 0 <= X < W and water[Y, X]:
                cv[Y, X] = C('water_cool', 1) if cv[Y, X] % 8 > 1 else cv[Y, X]
    # the side beam's face (east), seen over the water
    for Y in range(Y0 + P(1), Y1):
        for X in range(X1, X1 + P(1.5)):
            put(Y, X, C('timber_cool', 2) if (Y // P(3)) % 4 else C('timber_cool', 0))
    # the planks
    pw = 2.4
    y = ya
    k = 0
    while y < yb - 0.01:
        Ya, Yb = P(y, 0), P(min(yb, y + pw), 0)
        la, lb = rng.uniform(-0.6, 0.3), rng.uniform(-0.3, 0.6)
        fam = ('timber', 'timber_warm', 'timber')[k % 3]
        for Y in range(Ya, Yb):
            rr = (Y - Ya) / D
            for X in range(P(x0 + la, 0), P(x0 + w + lb, 0)):
                t = 4 if rr < 1.0 / D + 0.01 else (3 if rr < pw - 1.0 / D - 0.01 else 1)
                if t == 3 and ((X // P(2.5) + k * 3) % 5 == 0) and rr > 0.5:
                    t = 2
                put(Y, X, C(fam, t))
        for nx in (x0 + 1.6, x0 + w - 1.8):
            put(Ya + P(0.8), P(nx, 0), C('iron', 2))
        y += pw
        k += 1
    # the south abutment's face below the deck's end, lit, in courses
    for Y in range(Y1, Y1 + P(2.6)):
        for X in range(P(x0 - 2.0, 0), P(x0 + w + 2.0, 0)):
            r = (Y - Y1) / D
            joint = ((X / D - x0 + 2 * int(r // 1.3)) % 3.5) < 1.0 / D or (r % 1.3) < 1.0 / D
            c = C('stone', 1) if joint else C('stone', 4 if r < 1.3 else 3)
            if X >= P(x0 + w, 0):
                c = C('stone', 1) if joint else C('stone', 2)
            put(Y, X, c)
    for X in range(P(x0 - 2.0, 0), P(x0 + w + 2.0, 0)):
        put(Y1 + P(2.6), X, C('stone', 0))
    # the kerbs and the rails on posts (the posts stand up, so the rail runs 4 px above the deck)
    for (sx, lit) in ((x0 - 0.2, True), (x0 + w - 1.4, False)):
        X = P(sx, 0)
        for Y in range(Y0, Y1):
            for j in range(P(1.4)):
                put(Y, X + j, C('timber', (4 if j == 0 else 3) if lit else (2 if j == 0 else 1)))
        rail_y0, rail_y1 = ya - 3.6, yb - 3.6
        for Y in range(P(rail_y0, 0), P(rail_y1, 0)):
            for j in range(P(1.0)):
                put(Y, X + j, C('timber', 4 if lit else 2) if j == 0 else C('timber', 3 if lit else 1))
        for py in np.linspace(ya + 1.0, yb - 0.8, 3):
            for Y in range(P(py - 4.4, 0), P(py + 0.4, 0)):
                for j in range(-1, P(1.6) + 1):
                    edge_ = j < 0 or j >= P(1.6) or Y >= P(py + 0.4, 0) - 1
                    top_ = Y < P(py - 4.4, 0) + P(0.7)
                    c = C('timber_cool', 0) if edge_ else C('timber', (5 if top_ else (4 if j == 0 else 3)) if lit else (3 if top_ else 2))
                    put(Y, X + j - P(0.3), c)
            if not lit:
                for j in range(P(1.0)):
                    yy_, xx_ = P(py + 0.4, 0) + j, X + P(1.6)
                    if 0 <= yy_ < H and 0 <= xx_ < W:
                        put(yy_, xx_, C('water_cool', 1) if water[yy_, xx_] else C('earth', 1))


def path_hd(cv: np.ndarray, pts, hw0: float, seed: int = 0, spur: bool = False) -> np.ndarray:
    """A worn footpath at density 3 and up, on the soft grid (Matt, 26 Oct 10:19: paths should
    "adhere to the soft grid more", like the bench and lamp of the cast video). Its width wanders
    slowly (two long waves), so the edge runs smooth and steps a texel at a time; a rounded bite of
    turf or a tongue of dirt about every 16 world px; no one-texel teeth (softedge.soft). The dirt
    under the turf's north and west lip a tone down, the turf just south of it lit. Inside, calm:
    one body tone with a few large trodden and dry patches, two faint ruts where feet run, and
    pebbles in a few small clusters lit at their upper left with a shade under them. A spur (a short
    side path) widens where it leaves the main path and ends in a small apron."""
    from scipy.spatial import cKDTree
    from .terrain import noise as TN
    from . import softedge as SE
    H, W = cv.shape
    cp, sarc = SC._curve(pts)
    tree = cKDTree(cp)
    ys = np.arange(max(0, P(cp[:, 1].min() - 14, 0)), min(H, P(cp[:, 1].max() + 14, 0)))
    xs = np.arange(max(0, P(cp[:, 0].min() - 14, 0)), min(W, P(cp[:, 0].max() + 14, 0)))
    if not len(ys) or not len(xs):
        return
    YY, XX = np.meshgrid(ys, xs, indexing='ij')
    wy, wx = YY / D + 0.5 / D, XX / D + 0.5 / D
    dist, idx = tree.query(np.stack([wx.ravel(), wy.ravel()], 1))
    dist, idx = dist.reshape(wx.shape), idx.reshape(wx.shape)
    sa = sarc[idx]
    tx_, ty_ = np.gradient(cp[:, 0])[idx], np.gradient(cp[:, 1])[idx]
    side = np.sign(tx_ * (wy - cp[idx, 1]) - ty_ * (wx - cp[idx, 0]))      # which side of the line
    # the width wanders in two long waves, each side on its own
    hw = hw0 + 0.7 * np.sin(sa / 13.0 + seed + side * 1.3) + 0.45 * np.sin(sa / 5.3 + 2 * seed + side * 2.1)
    # a rounded bite or tongue about every 16 world px along each side
    k_ = np.floor(sa / 16.0)
    hb = ((k_.astype(np.int64) * 2654435761 + seed * 97 + (side > 0) * 13) % 1000) / 1000.0
    ph = sa / 16.0 - k_
    bump = np.exp(-((ph - 0.5) / 0.09) ** 2) * np.where(hb < 0.5, -1.4, 1.1) * (hb < 0.8)
    hw = hw + bump
    if spur:
        hw = hw + 4.0 * np.exp(-sa / 4.0) + 1.8 * np.exp(-((sarc[-1] - sa) - 2.5) ** 2 / 20.0)
        hw = hw * np.clip((sarc[-1] - sa + 2.5) / 5.0, 0.35, 1.0)
    cur = cv[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    grassy = is_fam(cur, 'grass') | is_fam(cur, 'leaf')
    dirt = SE.soft(dist <= hw) & grassy
    dirt = SE.soft(dirt)
    # calm inside (#288 review B1): one body tone; large trodden and dry patches as round lobes in
    # the cool and warm siblings of the same tone (about 16 L apart, Eastward's ground band), from
    # a noise that avalanches (no rows on the lattice) and one field for every piece of the network
    # (no seam where two pieces join)
    m1 = TN.vnoise_hd(wx, wy, 11.0, 51)
    t = np.full(dirt.shape, 3)
    fam = np.full(dirt.shape, FI['path'])
    fam[m1 < 0.3] = FI['path_cool']
    fam[m1 > 0.7] = FI['path_warm']
    # two ruts where feet and wheels run, wandering a texel, broken, on the main line only (not
    # round a piece's ends, so no loop where pieces join, S8)
    rw = (TN.vnoise_hd(wx, wy, 5.0, 59) - 0.5) * 0.7
    mid = (sa > 2.5) & (sa < sarc[-1] - 2.5)
    rut = (np.abs(dist - 0.38 * hw0 + rw) < 0.34) & (TN.vnoise_hd(wx, wy, 7.0, 55) > 0.42) & (dist < hw - 1.2) & mid \
        & (hw0 >= 5) & ~spur
    t[rut] -= 1
    out = cur.copy()
    out[dirt] = fam[dirt] * 8 + np.clip(t[dirt], 1, 5)
    # pebbles in a few small clusters
    rng = np.random.default_rng(1301 + seed)
    inner = dirt & (dist < hw - 1.5)
    iy, ix = np.nonzero(inner)
    for _ in range(int(len(iy) / (220 * D * D)) + 1 if len(iy) else 0):
        k = int(rng.integers(0, len(iy)))
        for _j in range(int(rng.integers(2, 5))):
            py, px = iy[k] + int(rng.normal(0, 1.4 * D)), ix[k] + int(rng.normal(0, 2.0 * D))
            rr = max(1, int(round(rng.uniform(0.5, 0.9) * D)))
            if not (rr <= py < out.shape[0] - rr - 2 and rr <= px < out.shape[1] - rr - 2) or not inner[py, px]:
                continue
            Yp, Xp = np.mgrid[-rr:rr + 2, -rr:rr + 2]
            stone = (Yp ** 2 + (Xp * 0.8) ** 2 <= rr * rr)
            shade_ = ((Yp - 1) ** 2 + ((Xp - 1) * 0.8) ** 2 <= rr * rr) & ~stone
            win = out[py - rr:py + rr + 2, px - rr:px + rr + 2]
            dwin = dirt[py - rr:py + rr + 2, px - rr:px + rr + 2]
            win[shade_ & dwin] = step(win[shade_ & dwin], -1)
            win[stone] = np.where((Yp[stone] < 0) & (Xp[stone] <= 0), C('stone', 4), C('stone', 3))
    # clods, dips and cracks a few world px apart (so the trodden earth is ground, not a fill)
    SE.soil_marks(out, dirt & (dist < hw - 1.0) & (TN.vnoise_hd(wx, wy, 7.0, 61) > 0.45), np.random.default_rng(1401 + seed),
                  spacing=1.2, p=0.6)
    cv[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] = out
    full = np.zeros((H, W), bool)
    full[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] = dirt
    return full


def tree_shadow_hd(x, y, ex, W, H) -> np.ndarray:
    """A tree's shadow at density 3 and up: the crown's shade as a ground shape that starts at
    the trunk's foot and reaches east and a little south (the sun at the upper left), as wide as
    the crown, so it always reads as that tree's. Its edge is scalloped by the crown's clumps
    (26 Oct: an even ellipse read as a rug) and a few sun flecks fall through the leaves inside."""
    cw = ex['w']
    cx, cy = x + 0.1 * cw, y + 0.03 * cw
    rx, ry = 0.36 * cw, 0.14 * cw + 2.0
    Y, X = np.mgrid[0:H, 0:W]
    wx, wy = (X + 0.5) / D, (Y + 0.5) / D
    seed = int(x * 31 + y * 7) % 10007
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.283, 3)
    a = np.arctan2((wy - cy) / ry, (wx - cx) / rx)
    r = 1.0 + 0.07 * np.sin(6 * a + ph[0]) + 0.045 * np.sin(11 * a + ph[1]) + 0.03 * np.sin(17 * a + ph[2])
    m = ((wx - cx) / rx) ** 2 + ((wy - cy) / ry) ** 2 <= r * r
    for _ in range(max(2, int(cw / 10))):
        t = rng.uniform(0, 6.283)
        q = np.sqrt(rng.uniform(0.05, 0.55))
        fx_, fy_ = cx + q * rx * np.cos(t), cy + q * ry * np.sin(t)
        for _k in range(int(rng.integers(1, 4))):           # a fleck: one to three small spots of sun
            ox_, oy_ = fx_ + rng.uniform(-1.2, 1.2), fy_ + rng.uniform(-0.6, 0.6)
            fr = rng.uniform(0.45, 0.9)
            m &= ~(((wx - ox_) / (fr * 1.5)) ** 2 + ((wy - oy_) / fr) ** 2 <= 1.0)
    return m


def lawn_dressing_hd(cv: np.ndarray, plan: dict, h: int, w: int) -> list:
    """The lawn's dressing at density 3 and up, the way Eastward dresses grass: few, clustered and
    varied, with calm lawn between. Clusters stand about one in two 20 world px cells; each holds
    2 to 5 of: a tuft (fine, broad or seeding, 0.5 to 1.6 of the kit's size, three greens), a group
    of small flowers (white, yellow, violet), or a clover patch laid into the lawn (trefoils, lit at
    their upper left). Never on paths, water, rock or under an object's foot. Returns low items;
    the clover is drawn into the codes."""
    from . import ground as GR
    from .terrain import noise as TN
    rng = np.random.default_rng(1907)
    lawn = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)
    lawn = ndi.binary_erosion(lawn, iterations=P(3))
    for (oid, kind, x, y, ow, oh) in plan['objects']:
        x0, x1 = P(x - 2, 0), P(x + ow + 2, 0)
        y0, y1 = P(y + oh * 0.55, 0), P(y + oh + 3, 0)
        lawn[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = False
    items = []
    cell = 20.0
    for cy in np.arange(0, h / D, cell):
        for cx in np.arange(0, w / D, cell):
            if rng.random() > 0.5:
                continue
            ccx, ccy = cx + rng.uniform(2, cell - 2), cy + rng.uniform(2, cell - 2)
            if TN.vnoise_hd(np.array([ccx]), np.array([ccy]), 60.0, 77)[0] < 0.3:
                continue                                       # a calm stretch of lawn
            n = int(rng.integers(2, 6))
            for j in range(n):
                tx, ty = ccx + rng.normal(0, 3.2), ccy + rng.normal(0, 2.0)
                X_, Y_ = int(tx * D), int(ty * D)
                if not (0 <= Y_ < h and 0 <= X_ < w) or not lawn[Y_, X_]:
                    continue
                r = rng.random()
                if r < 0.55:
                    fam = ('grass', 'leaf', 'grass')[int(rng.integers(0, 3))]
                    img = GR.tuft(D, int(rng.integers(0, 10 ** 6)), float(rng.uniform(0.5, 1.6)), fam=fam)
                elif r < 0.8:
                    kind = ('white', 'yellow', 'violet', 'white')[int(rng.integers(0, 4))]
                    img = P4.flowers4(D, int(rng.integers(0, 10 ** 6)), kind=kind, n=int(rng.integers(2, 4)))
                else:
                    # a clover patch: trefoils laid into the lawn
                    for q in range(int(rng.integers(4, 9))):
                        qx, qy = X_ + int(rng.normal(0, 2.2 * D)), Y_ + int(rng.normal(0, 1.4 * D))
                        for (dy, dx) in ((-1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (0, 0), (1, 0)):
                            yy_, xx_ = qy + dy, qx + dx
                            if 0 <= yy_ < h and 0 <= xx_ < w and lawn[yy_, xx_]:
                                cv[yy_, xx_] = C('leaf', 4) if (dy, dx) in ((-1, -1), (-1, 0)) else (
                                    C('leaf', 2) if (dy, dx) == (1, 0) else C('leaf', 3))
                    continue
                a = np.asarray(img)[..., 3] > 0
                if not a.any():
                    continue
                x0, y0, x1, y1 = CO._bbox(a)
                items.append((ty, img, ((x0 + x1) / 2, y1), (tx * D, ty * D), False))
    return items


def _wnoise(h, w, scale, seed):
    """Smooth noise at texels, its features about `scale` world px across, normalised."""
    rng = np.random.default_rng(seed)
    hh, ww = int(h / D / scale * 4) + 4, int(w / D / scale * 4) + 4
    f = ndi.gaussian_filter(rng.random((hh, ww)), 1.2)
    f = (f - f.mean()) / max(1e-6, f.std())
    z = ndi.zoom(f, (h / hh + 1e-3, w / ww + 1e-3), order=1)
    return z[:h, :w]


def ground_detail_hd(cv: np.ndarray, plan: dict, trees: list, h: int, w: int, shade: np.ndarray, soft: bool = False) -> None:
    """The lawn's ground detail at density 3 and up, drawn into the codes before the shadows so
    shade falls over it (26 Oct, fix queue: the scene gate found large flat stretches of lawn, the
    glade one tone and every crown's shadow a rug). Clustered where it would gather, calm between,
    never a uniform stipple:
      - broad soft patches of the cool and the lit grass (a few world px to a dozen across), more of
        them where the turf is thin (round trees and in the glade's sun);
      - worn patches where feet and animals go (the path's shoulders, the glade under the hollow
        tree, before the bench and the stumps): bare earth with a dark turf lip on the north edge,
        a lit lip on the south, a pebble or two and a sprout of grass left in them;
      - leaf litter under every broadleaf crown in drifts (clay, brass and dry green leaves of two
        or three texels, lit at their upper left with a shade texel under);
      - twigs and clover in the same drifts."""
    rng = np.random.default_rng(2611)
    grass = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)
    lawn = ndi.binary_erosion(grass, iterations=P(1.5))
    Y, X = np.mgrid[0:h, 0:w]
    wx, wy = (X + 0.5) / D, (Y + 0.5) / D
    # where turf is thin: round trunks (a crown's width), the glade, the sun
    thin = np.zeros((h, w))
    for (fx, fy, cw, _k) in trees:
        thin = np.maximum(thin, np.clip(1.15 - np.hypot((wx - fx - 0.08 * cw) / (0.55 * cw), (wy - fy) / (0.3 * cw + 3)), 0, 1))
    g = plan['places']['glade']
    thin = np.maximum(thin, 0.8 * np.clip(1.1 - np.hypot((wx - g['at'][0]) / g['r'][0], (wy - g['at'][1]) / g['r'][1]), 0, 1))
    # 1. soft patches where the lawn is calm (one tone over a few world px), gathered by a slow
    #    field; the lawn's own mottle elsewhere is left alone
    win = P(5)
    same = ndi.uniform_filter((cv == ndi.median_filter(cv, size=3)).astype(float), size=win)
    cmax = ndi.maximum_filter(cv, size=win)
    cmin = ndi.minimum_filter(cv, size=win)
    calm = lawn & (cmax == cmin) & (same > 0.9)
    calm = ndi.binary_dilation(calm, iterations=P(2)) & lawn
    if soft:
        calm[:] = False            # the soft grid's lawn (softground.lawn) carries its own field and marks
    nA = _wnoise(h, w, 7.0, 41)
    nB = _wnoise(h, w, 30.0, 47)
    gather = nB + 1.2 * thin
    chk = ((X // 2 + Y // 2) % 2) == 0
    va = nA + 0.25 * _wnoise(h, w, 2.0, 43)
    dn_core = calm & (va > 1.05 - 0.45 * np.clip(gather, 0, 1.4))
    up_core = calm & (va < -1.15 + 0.3 * np.clip(gather, 0, 1.4))
    # (hard edges: the blade marks below break them, as Eastward's patches end in blades). The
    # patches change hue, not value: the cool sibling for the damp, the warm one for the dry; a
    # tone of value would stand out further than Eastward's ground pieces do from each other
    sel = dn_core & (cv % 8 < 6)
    warm = sel & (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & np.isin(cv // 8, [FI['grass_warm'], FI['leaf_warm']])
    cv[warm] = sib(cv[warm], 'body')
    cv[sel & ~warm] = sib(cv[sel & ~warm], 'cool')
    sel = up_core & (cv % 8 < 6)
    cv[sel] = sib(cv[sel], 'warm')
    # 1a. a pool of sun fades out through a 2 x 2 checker a tone down, 3 world px deep (light is the
    #     one place dither is used), so a thin pool is a soft glow rather than a bright slab
    heart = lawn & (cv // 8 == FI['grass_warm']) & (cv % 8 >= 4)
    lab_, n_ = ndi.label(heart)
    if n_:
        sizes_ = ndi.sum(heart, lab_, range(1, n_ + 1))
        heart = np.isin(lab_, 1 + np.nonzero(sizes_ < 900 * D * D / 9)[0])     # the small pools (the glade keeps its sun)
    band_ = heart & ~ndi.binary_erosion(heart, iterations=P(3)) & chk
    cv[band_] = step(cv[band_], -1)
    # 1b. the blade texture (Eastward's lawn, shot 13): small V marks of the grass a tone down,
    #     staggered about 2.5 world px apart and gathered by a slow field (from a few to dense),
    #     so no stretch of turf is a flat fill and the patches' edges break into blades
    sp_x, sp_y = max(6, P(2.6)), max(5, P(1.9))
    dens = np.clip(0.6 + 0.35 * nB + 0.25 * thin, 0.4, 0.95)
    # in shade the turf grows long and dark: the blades stand twice as close there (and every blade
    # shows in a pool of sun)
    grid = [(gy, gx) for gy in range(0, h, sp_y) for gx in range((gy // sp_y) % 2 * (sp_x // 2), w, sp_x)]
    grid += [(gy, gx) for gy in range(sp_y // 2, h, sp_y) for gx in range(((gy // sp_y) % 2 * (sp_x // 2) + sp_x // 4), w, sp_x)
             if shade[gy, min(w - 1, gx)]]
    if soft:
        grid = []
    for (gy, gx) in grid:
        y0 = gy + int(rng.integers(-1, 2))
        x0 = gx + int(rng.integers(-2, 3))
        if not (1 <= y0 < h - 2 and 1 <= x0 < w - 3) or not lawn[y0, x0] or rng.random() > (0.95 if (shade[y0, x0] or cv[y0, x0] % 8 >= 4) else dens[y0, x0]):
            continue
        k = int(rng.integers(0, 4))
        pts = (((0, 0), (1, 1), (0, 2)), ((0, 0), (1, 1), (0, 2)), ((0, 1), (1, 0)), ((0, 0), (1, 1)))[k]
        for (dy, dx) in pts:
            yy, xx = y0 + dy, x0 + dx
            if lawn[yy, xx] and cv[yy, xx] % 8 > 0:
                cv[yy, xx] = step(cv[yy, xx], -1)
    # 2. worn patches: bare earth where feet go
    sites = []
    for p in plan['paths']:
        pts = [tuple(q) for q in p['points']]
        for (a, b) in zip(pts[:-1], pts[1:]):
            n = int(np.hypot(b[0] - a[0], b[1] - a[1]) / 44) + 1
            for k in range(n):
                t = (k + rng.uniform(0.2, 0.8)) / n
                px, py = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                dx, dy = b[1] - a[1], -(b[0] - a[0])
                nn = max(1e-6, np.hypot(dx, dy))
                side = 1 if rng.random() < 0.5 else -1
                # a worn shoulder joined to the path (where feet step off it), not a loose blob beside it
                off = p['radius'] - 1.0 + rng.uniform(0.0, 1.5)
                sites.append((px + side * dx / nn * off, py + side * dy / nn * off, int(rng.integers(1, 3))))
    for (oid, kind, x, y, ow, oh) in plan['objects']:
        if kind in ('forest_bench', 'stump', 'hollow_tree'):
            sites.append((x + ow / 2 + rng.uniform(-3, 3), y + oh + rng.uniform(3, 6), int(rng.integers(2, 4))))
    sites.append((g['at'][0] + 6, g['at'][1] + 10, 4))
    earth = np.zeros((h, w), bool)
    for (sx, sy, n) in sites:
        for j in range(n):
            cx_, cy_ = sx + rng.normal(0, 3.2), sy + rng.normal(0, 1.8)
            rx, ry = rng.uniform(1.4, 3.6), rng.uniform(0.9, 2.0)
            m = blob(cx_, cy_, rx, ry, seed=int(rng.integers(0, 10 ** 6)), rough=0.35, w=w, h=h)
            earth |= m
    earth &= lawn
    # on the soft grid (26 Oct): smooth runs, no teeth; dark under the turf's north and west lip,
    # the turf south of it lit; no dither at the boundary (eastward-edges.md 5.4)
    from . import softedge as SE
    earth = SE.soft(earth, min_area=4.0) & lawn
    cv[earth] = C('earth_warm', 3)
    inner = earth & ndi.binary_erosion(earth, iterations=2)
    cv[inner & (_wnoise(h, w, 2.4, 53) > 0.7)] = C('earth_warm', 4)
    SE.rim(cv, earth, grass & ~earth)
    ys, xs = np.nonzero(inner)
    for k in rng.choice(len(ys), size=min(len(ys), int(len(ys) / (9 * D * D)) + 1), replace=False) if len(ys) else []:
        y0, x0 = ys[k], xs[k]
        if rng.random() < 0.55:                                         # a pebble, lit at its upper left
            cv[y0:y0 + 2, x0:x0 + 2] = C('earth_warm', 4)
            cv[y0 + 1, x0 + 1] = C('earth_warm', 3)
            cv[y0 + 2, x0:x0 + 2] = C('earth_warm', 1)
        else:                                                            # a sprout of grass left in it
            cv[y0 - 2:y0 + 1, x0] = C('grass', 3)
            cv[y0 - 1:y0 + 1, x0 + 1] = C('grass', 2)
    # 2b. in shade the trodden path shows its clods closer (the shade keeps them, two tones down)
    pathlike = is_fam(cv, 'path') & (cv % 8 < 6)
    SE.soil_marks(cv, pathlike & ndi.binary_erosion(shade, iterations=2), rng, spacing=0.55, p=1.0)
    # 3. leaf litter, twigs and clover in drifts under the broadleaf crowns
    leaf_tones = [C('clay', 4), C('brass', 4), C('earth_warm', 3), C('leaf_warm', 2), C('clay', 5)]
    for (fx, fy, cw, kind_) in trees:
        if kind_ == 'pine':
            continue                                      # needles, not leaves: no litter drifts
        nd = int(rng.integers(2, 5))
        for _ in range(nd):
            dcx = fx + rng.uniform(-0.15, 0.45) * cw
            dcy = fy + rng.uniform(-0.5, 0.8) * (0.14 * cw + 2)
            for _ in range(int(rng.integers(4, 10))):
                lx_, ly_ = dcx + rng.normal(0, 2.6), dcy + rng.normal(0, 1.4)
                X0, Y0 = int(lx_ * D), int(ly_ * D)
                if not (2 <= Y0 < h - 3 and 2 <= X0 < w - 4) or not lawn[Y0, X0]:
                    continue
                r = rng.random()
                if r < 0.72:
                    c0 = leaf_tones[int(rng.integers(0, len(leaf_tones)))]
                    lw = 3 if rng.random() < 0.5 else 2
                    cv[Y0, X0:X0 + lw] = c0
                    cv[Y0 + 1, X0 + 1:X0 + lw + 1] = step(np.array(c0), -1)
                    cv[Y0, X0] = step(np.array(c0), 1)
                    cv[Y0 + 2, X0 + 1:X0 + lw + 1] = step(cv[Y0 + 2, X0 + 1:X0 + lw + 1], -1)
                elif r < 0.86:
                    ln = int(rng.integers(3, 6))
                    for q in range(ln):
                        cv[Y0 + (q * int(rng.integers(0, 2)) // 3), X0 + q] = C('earth_warm', 1) if q % 2 else C('earth', 2)
                else:
                    for (dy, dx) in ((-1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (0, 0), (1, 0)):
                        cv[Y0 + dy, X0 + dx] = C('leaf', 4) if (dy, dx) in ((-1, -1), (-1, 0)) else (
                            C('leaf', 2) if (dy, dx) == (1, 0) else C('leaf', 3))


def mushrooms_at(plan: dict) -> list:
    """Where the woodland's mushrooms grow: in clusters at the feet of stumps and fallen logs,
    on the side away from the path (density 3 and up; the 1x fairy ring was head-sized)."""
    out = []
    for i, (oid, kind, x, y, w, h) in enumerate(plan['objects']):
        if kind in ('stump', 'mossy_log') and i % 2 == 0:
            side = 1 if (i // 2) % 2 else -1
            fx = x + (w + 2.5 if side > 0 else -2.5)
            out.append((fx, y + h + 0.5, 600 + i, 'red' if i % 4 == 0 else 'brown'))
    return out


# ------------------------------------------------------------------------------------------------
# objects: one picture per kind from the biome's recipe
# ------------------------------------------------------------------------------------------------
def _master(name: str) -> str:
    return os.path.join(MASTERS, name)


def tree_dims(master: str) -> dict:
    """A tree master's box, trunk width and crown height (world px), read from its pixels."""
    a = np.asarray(Image.open(_master(master)).convert('RGBA')).astype(int)
    al = a[..., 3] > 0
    green = al & (a[..., 1] > a[..., 0] + 4)
    H1, W1 = al.shape
    gy = np.nonzero(green.any(1))[0]
    ch = int(gy.max()) + 1 if len(gy) else H1 // 2
    wood = al & ~green & (a[..., 0] > a[..., 1] + 10)
    low = wood[H1 - 4:H1]
    cols = np.nonzero(low.any(0))[0]
    tw = int(cols.max() - cols.min() + 1) if len(cols) else max(4, W1 // 6)
    return dict(w=W1, h=H1, tw=int(np.clip(tw - 2, 3, W1 * 0.2)), ch=int(ch * 0.9))


def monolith(w: float, h: float, seed: int, fam: str = 'stone'):
    """One standing stone (Matt, 27 Oct: the ring "looks a bit odd"): a single upright slab w x h world
    px, its crown worn round and leaning a touch, seen from the front a little above: the top a
    narrow lit cap, the front face lit on the west and falling into shade to the east, the east
    edge dark, a base band at the foot; weathering in flakes and one crack, lichen in a few small
    patches on the lit side, moss at the foot. Returns (picture, anchor at the foot, alpha)."""
    rng = np.random.default_rng(seed)
    pad = P(2)
    Wt, Ht = P(w) + 2 * pad, P(h) + 2 * pad
    a = np.full((Ht, Wt), -1, np.int32)
    yy, xx = np.mgrid[0:Ht, 0:Wt].astype(float)
    x0, x1 = pad, pad + P(w)
    yb, yt = Ht - pad, pad
    cw = (x1 - x0) / 2.0
    lean = rng.uniform(-0.12, 0.12) * cw
    t = (yb - yy) / max(1.0, yb - yt)                                 # 0 at the foot, 1 at the crown
    cx = (x0 + x1) / 2.0 + lean * t
    half = cw * (1.0 - 0.10 * t) + (TN_noise(Ht, seed) - 0.5) * 1.4   # a slight taper, a worn edge
    crown_r = cw * 0.95
    u = (xx - cx) / np.maximum(half, 1)                               # -1 west .. 1 east
    # a rough slab's top, not a headstone's arch: sloping one way, its shoulders broken off
    sl = rng.choice([-1.0, 1.0]) * rng.uniform(0.25, 0.5)
    top_y = yt + crown_r * (0.55 + sl * u * 0.6) + crown_r * 0.55 * np.clip(np.abs(u) - 0.45, 0, 1) ** 1.5 * 2.2
    top_y += (TN_noise2(Ht, Wt, seed + 7)[0][None, :] - 0.5) * 2.0
    body = (np.abs(xx - cx) <= half) & (yy <= yb) & (yy >= top_y)
    # the face's planes: the light falls off to the east, broken into weathered plates (a slow
    # blotch field), so the stone reads as rough rock, not a turned column
    blot = TN_noise2(Ht, Wt, seed + 2)
    lv = 3.2 - 1.5 * u + (blot - 0.5) * 1.6 + 0.4 * t
    tone = np.clip(np.round(lv), 1, 4).astype(int)
    tone = np.where(u > 0.78, 1, tone)
    # the cap: the worn top seen from above, lit on the west, its east rim a dark arris
    capm = body & (yy < top_y + crown_r * 0.55)
    ct = np.clip(np.round(4.5 - 1.3 * u + (TN_noise2(Ht, Wt, seed + 3) - 0.5) * 1.8), 3, 5).astype(int)
    tone = np.where(capm, ct, tone)
    rim = capm & ~np.roll(capm, -1, 0) & (u > -0.1)
    tone = np.where(rim, 2, tone)
    tone = np.where(body & (yy >= yb - P(1.2)), np.maximum(1, tone - 1), tone)  # the base, a tone down
    fams = np.where(tone >= 4, FI[fam + '_warm'], np.where(tone <= 1, FI[fam + '_cool'], FI[fam]))
    a[body] = (fams * 8 + tone)[body]
    # flakes: small lit or dark plates down the face, a crack with its lit lip
    # flakes: plates of 2 to 4 texels a tone down with a lit upper edge (where a flake has come
    # away), pits, and grain specks, over the face and the cap
    for _ in range(int(P(w) * P(h) / 26)):
        fy, fx = int(rng.uniform(yt + 2, yb - P(2))), int(rng.uniform(x0 + 1, x1 - 3))
        L = int(rng.integers(2, 5))
        if not (1 <= fy < Ht - 2 and 0 <= fx < Wt - L - 1) or not body[fy, fx:fx + L].all():
            continue
        r_ = rng.random()
        if r_ < 0.55:
            a[fy, fx:fx + L] = step(a[fy, fx:fx + L], -1)
            if body[fy - 1, fx:fx + L].all():
                a[fy - 1, fx:fx + L] = step(a[fy - 1, fx:fx + L], 1)
        elif r_ < 0.8:
            a[fy:fy + 2, fx:fx + 2] = step(a[fy:fy + 2, fx:fx + 2], -1)
            a[fy, fx] = step(a[fy, fx], -1)
        else:
            a[fy, fx:fx + L] = step(a[fy, fx:fx + L], 1)
    ky = int(rng.uniform(yt + crown_r * 1.2, yb - P(4)))
    kx = int(cx[ky, 0] + rng.uniform(-0.2, 0.3) * cw) if ky < Ht else x0 + 2
    for j in range(int(P(5))):
        y_, x_ = ky + j, kx + (j // 3) * (1 if seed % 2 else -1)
        if 0 <= y_ < Ht and 0 <= x_ < Wt - 1 and body[y_, x_]:
            a[y_, x_] = C(fam + '_cool', 0)
            if body[y_, x_ - 1]:
                a[y_, x_ - 1] = C(fam + '_warm', 4)
    # the lit planes are the most weathered: their grain shows as short dashes a tone down and the
    # odd bright grain, so no lit plane is one smooth patch (and it keeps a top and a front plane)
    lit_ = body & (a % 8 >= 4) & ((a // 8) != FI['leaf'])
    ly_, lx_ = np.nonzero(lit_)
    for kk in rng.permutation(len(ly_))[: len(ly_) // 7]:
        y_, x_ = int(ly_[kk]), int(lx_[kk])
        if x_ + 1 < Wt and lit_[y_, x_ + 1]:
            d_ = -1 if rng.random() < 0.7 else 1
            a[y_, x_:x_ + 2] = step(a[y_, x_:x_ + 2], d_)
    # lichen on the lit side, moss at the foot
    for _ in range(3):
        ly, lx = rng.uniform(yt + crown_r, yb - P(4)), rng.uniform(x0, cx.mean())
        lm = body & (((xx - lx) / P(1.6)) ** 2 + ((yy - ly) / P(1.0)) ** 2 <= 1) & (rng.random((Ht, Wt)) < 0.8)
        a[lm] = np.where(yy[lm] < ly, C('lichen' if 'lichen' in FI else 'leaf_warm', 4), C('lichen' if 'lichen' in FI else 'leaf_warm', 3))
    mm = body & (yy >= yb - P(2.2) - 3 * TN_noise2(Ht, Wt, seed + 5)) & (TN_noise2(Ht, Wt, seed) > 0.58)
    a[mm] = np.where(yy[mm] < yb - P(1.2), C('leaf', 4), C('leaf', 3))
    # the outline: dark on the east and the foot, the west edge a lit rim
    ed = body & ~ndi.binary_erosion(body)
    east = ed & (u > 0)
    a[east] = C(fam + '_cool', 0)
    a[ed & (yy >= yb - 1)] = C(fam + '_cool', 0)
    west = ed & (u <= 0) & (yy < yb - 1)
    a[west] = C(fam + '_warm', 5) if (fam + '_warm') in FI else C(fam, 5)
    from .palette import to_rgba
    img = Image.fromarray(to_rgba(a), 'RGBA')
    alpha = a >= 0
    return img, ((x0 + x1) / 2.0, yb - 1), alpha


def TN_noise(H: int, seed: int) -> np.ndarray:
    """A slow wander per row (0..1), the same for every column: the stone's worn outline."""
    rng = np.random.default_rng(seed + 9)
    v = ndi.gaussian_filter1d(rng.random(H), 2.0)
    v = (v - v.min()) / max(1e-6, v.max() - v.min())
    return v[:, None]


def TN_noise2(H: int, W: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed + 13)
    v = ndi.gaussian_filter(rng.random((H, W)), 1.2)
    return (v - v.min()) / max(1e-6, v.max() - v.min())


def sprite(kind: str, recipe: dict, seed: int):
    """(picture, anchor (texels: the foot), alpha, shadow extra) for one kind."""
    paint = recipe['paint']
    look = dict(crown=recipe.get('crown'), bark=recipe.get('bark', 'oak'), scale=recipe.get('scale'))
    seed = recipe.get('seed', seed)
    if paint == 'tree':
        ex = tree_dims(recipe['master'])
        ex.update(look)
        if recipe.get('trunk_w'):
            ex['tw'] = recipe['trunk_w']
        ex['hollow'] = recipe.get('hollow', False)
        img, anc, a = CO.sprite_for('tree', _master(recipe['master']), D, seed, ex)
        return img, anc, a, ex
    if paint == 'foliage':
        img, anc, a = CO.sprite_for('bush', _master(recipe['master']), D, seed, look)
        return img, anc, a, None
    if paint == 'boulder':
        img, anc, a = P4.boulder4(D, recipe['size'][0], recipe['size'][1], seed=seed, fam=recipe.get('fam', 'stone'),
                                  moss=recipe.get('moss', 'top'))
    elif paint == 'monolith':
        img, anc, a = monolith(recipe['size'][0], recipe['size'][1], seed, fam=recipe.get('fam', 'stone'))
        return img, anc, a, None
    elif paint == 'stump':
        img, anc, a = P4.stump4(D, seed=seed)
    elif paint == 'log':
        img, anc, a = P4.log4(D, length=recipe.get('length', 54), seed=seed)
    elif paint == 'bench':
        img, anc, a = P4.bench4(D, seed=seed)
    else:
        raise KeyError(paint)
    x0, y0, x1, y1 = CO._bbox(a)
    return img, ((x0 + x1) / 2, y1), a, None


# ------------------------------------------------------------------------------------------------
def terrain(plan: dict, layers: dict) -> tuple:
    """The ground codes before shadows: lawn, light, paths, places, water, rock."""
    W, H = plan['screen']['w'], plan['screen']['h']
    w, h = int(W * D), int(H * D)
    cv, _hp, _occ = SC.render()
    cv = cv[:h, :w].copy()
    soft_lawn = np.zeros(cv.shape, bool)
    if D >= HD:
        # the soft grid's lawn (softground.lawn, 26 Oct): a calm field of two sibling hues, a low
        # mottle and loose clumps of tufts in place of the tiles' lawn, wherever the tiles laid turf
        from . import softground as GD
        lawn_ = GD.lawn(h, w, 977)
        soft_lawn = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)
        cv[soft_lawn] = lawn_[soft_lawn]
    layers['lawn'] = cv.copy()
    pl = plan['places']
    g = pl['glade']
    sun(cv, blob(*g['at'], *g['r'], seed=g['seed'], rough=g['rough'], w=w, h=h), heart=10 ** 6, fade=P(3), soft=D >= HD)
    s = pl['sun']
    sun(cv, blob(*s['at'], *s['r'], seed=s['seed'], rough=s['rough'], w=w, h=h), heart=P(4), fade=P(2), soft=D >= HD)
    for (lx, ly, rx, ry) in pl['light_pools']:
        sun(cv, blob(lx, ly, rx, ry, seed=int(lx * 7 + ly), rough=0.3, w=w, h=h), heart=P(5), fade=P(2), soft=D >= HD)
    paths_m = np.zeros(cv.shape, bool)
    if D >= HD:
        # the path network on the soft grid (Matt, 26 Oct): each path's plan in whole cells (two
        # for a path, one for a narrow spur), long straight runs, one rounded and lumped outline for
        # the network, packed earth inside (softground.dirt), the turf fraying over its edge
        from . import softgrid as SG
        cells_ = np.zeros(SG.grid_shape(h, w), bool)
        for p in plan['paths']:
            if not p.get('bend'):
                cells_ |= SG.cells_route(p['points'], max(1, int(round(2 * p['radius'] / 8.0))), h, w)
        net = SG.shape(cells_, h, w, 41, r_out=SG.R_TURN_OUT, r_in=SG.R_TURN_IN)
        # desire lines (Matt, 27 Oct): straight runs, turns and offsets as wide rounded bends
        for k_, p in enumerate(plan['paths']):
            if p.get('bend'):
                net |= SG.curve_texels(p['points'], max(1, int(round(2 * p['radius'] / 8.0))), h, w, p['bend'], 47 + k_)
        net &= is_fam(cv, 'grass') | is_fam(cv, 'leaf')
        turf0 = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & ~net
        GD.dirt(cv, net, 43, fam='path', cell=12)
        GD.sunken_edge(cv, net, turf0, np.random.default_rng(45))
        soft_lawn |= ndi.binary_dilation(net, iterations=6)
        paths_m |= net
    for k, p in enumerate(plan['paths'] if D < HD else []):
        if D >= HD:
            paths_m |= path_hd(cv, [tuple(q) for q in p['points']], hw0=p['radius'] - 2.0, seed=k, spur=p.get('spur', False))
        else:
            SC.worn2(cv, [tuple(q) for q in p['points']], hw0=p['radius'] - 2.0)

    co, ci = pl['circle_out'], pl['circle_in']
    ring = blob(*co['at'], *co['r'], seed=co['seed'], rough=co['rough'], w=w, h=h) & \
        ~blob(*ci['at'], *ci['r'], seed=ci['seed'], rough=ci['rough'], w=w, h=h)
    trodden(cv, ring)
    layers['places'] = cv.copy()
    hd = D >= HD
    soft_w = hd and 'soft' in plan['water']
    if soft_w:
        wm = water_mask_soft(plan, W, H)
    else:
        wm = water_mask_hd(plan, W, H) if hd else texels(mask_rle(plan['water']['water_rle'], W, H))
    rock = texels(mask_rle(plan['rock']['rock_rle'], W, H))
    scree(cv, plan['rock']['talus']['depth'], wm)
    for b in sorted(plan['rock']['talus']['boulders'], key=lambda b: b['at'][1]):
        boulder(cv, b['at'][0], b['at'][1], b['size'][0], b['size'][1], b['seed'], moss=b['moss'])
    f = plan['water']['fall']
    br = pl['bridge']
    if hd:
        if soft_w:
            # the soft grid's water (softground.water, the swatch's river): the far bank's earth
            # face under the grass lip, the light waterline, the depth band, calm water with
            # sparse ripples along the flow, reeds and rushes at the edges; the footbridge spans
            # the river bank to bank at a straight crossing, on an abutment in each bank
            from . import softground as GD
            items = GD.water(cv, wm, 402, bank_h=P(3.4, 0), flow='auto', stones=plan['water']['soft'].get('stones', 0.0),
                             reeds=0.8, rush_clumps=plan['water']['soft'].get('rush_clumps'))
            for (img_, anc_, (fx_, fy_)) in sorted(items, key=lambda it: it[2][1]):
                # stones breaking the banks, laid into the ground with their shade
                dec_ = to_codes(img_)
                DC.paste(cv, dec_, int(round(fx_ - anc_[0])), int(round(fy_ - anc_[1])), shadow=True,
                         shadow_dx=P(1), shadow_dy=P(0.5))
            GD.footbridge(cv, P(br['x0'], 0), P(br['x0'] + br['w'], 0), wm, np.random.default_rng(12))
        else:
            WA.paint_hd(cv, wm)            # (no reeds at density 3: their stalks bit stairs into the bank)
            footbridge_hd(cv, br['x0'], br['w'], br['y0'], br['y1'], wm)
        # the spring's heap: the pilot's boulders (props.boulder4), back to front, the lip stone
        # first; moss grows in from their tops
        # the rill's channel between the stones stays open water down to the lip
        chan = wm.copy()
        chan[P(f['y0'], 0):] = False
        chan[:P(f['y0'] - 40, 0)] = False
        for b in sorted(plan['rock']['heap'], key=lambda b: b['at'][1]):
            img, anc, _a = P4.boulder4(D, b['size'][0], b['size'][1], seed=b['seed'])
            dec = to_codes(img)
            X, Y = int(round(b['at'][0] * D - anc[0])), int(round(b['at'][1] * D - anc[1]))
            hh, ww = dec.shape
            sub = chan[max(0, Y):Y + hh, max(0, X):X + ww]
            dec[max(0, -Y):max(0, -Y) + sub.shape[0], max(0, -X):max(0, -X) + sub.shape[1]][sub] = -1
            DC.paste(cv, dec, X, Y, shadow=True, shadow_dx=P(2), shadow_dy=P(1))
        WA.wet_rock(cv, f['x0'], f['w'], f['y0'] - 2, f['y1'])
        if soft_w:
            ledge(cv, f['x0'], f['w'], f['y0'])          # the lip the water spills over
        WA.fall_hd(cv, f['x0'], f['w'], f['y0'], f['y1'], seed=f.get('seed', 11))
    else:
        WA.paint(cv, wm)
        footbridge(cv, br['x0'], br['w'], br['y0'], br['y1'], wm)
        for b in sorted(plan['rock']['heap'], key=lambda b: b['at'][1]):
            boulder(cv, b['at'][0], b['at'][1], b['size'][0], b['size'][1], b['seed'], moss=b['moss'])
        WA.wet_rock(cv, f['x0'], f['w'], f['y0'] - 2, f['y1'])
        WA.fall(cv, f['x0'], f['w'], f['y0'], f['y1'], seed=f.get('seed', 11))
        SC.reeds(cv)
    layers['water'] = cv.copy()
    # no speckle: a lone pixel takes its most common neighbour (outlines and water excepted)
    keep = (cv % 8 >= 6) | np.isin(cv // 8, [FI['water'], FI['water_warm'], FI['water_cool']]) | soft_lawn
    for _ in range(2):
        Pd = np.pad(cv, 1, mode='edge')
        nb = np.stack([Pd[:-2, 1:-1], Pd[2:, 1:-1], Pd[1:-1, :-2], Pd[1:-1, 2:]])
        lone = (cv != nb[0]) & (cv != nb[1]) & (cv != nb[2]) & (cv != nb[3]) & ~keep & (cv >= 0)
        for y, x in zip(*np.nonzero(lone)):
            v = list(nb[:, y, x])
            cv[y, x] = max(set(v), key=v.count)
    return cv, wm, rock


def foot_at_bottom_centre(img, anc, a, ex):
    """Pad a sprite so its foot (anchor) is the middle of its picture's bottom edge: the game sorts
    and places a picture by that point, so the object stands exactly where the plan puts its foot,
    on the soft grid (26 Oct; gen_zone, scene.check_grid)."""
    ax, ay = anc
    w, h = img.size
    left = int(round(max(ax, w - ax) - ax))
    right = int(round(max(ax, w - ax) - (w - ax)))
    bottom = max(0, int(round(ay)) - h)
    top = 0
    if ay < h:                                   # drop transparent rows below the foot
        a_ = np.asarray(img)[..., 3]
        if not a_[int(round(ay)):].any():
            img = img.crop((0, 0, w, int(round(ay))))
            a = a[:int(round(ay))]
            h = img.size[1]
    W2 = w + left + right
    if (W2 - 2 * (ax + left)) != 0:              # an odd half texel: one more on the right
        right += 1 if (ax + left) * 2 > W2 else 0
        W2 = w + left + right
    out = Image.new('RGBA', (W2, h + bottom + top), (0, 0, 0, 0))
    out.alpha_composite(img, (left, top))
    na = np.zeros((h + bottom + top, W2), bool)
    na[top:top + a.shape[0], left:left + a.shape[1]] = a
    return out, (ax + left, ay + top), na, ex


def build() -> Zone:
    plan, biome = ctx.PLAN, ctx.BIOME
    layers = {}
    cv, wm, rock = terrain(plan, layers)
    h, w = cv.shape
    recipes = biome['recipes']
    sprites, objects, things, casts, tcasts = {}, [], [], [], []
    for k, kind in enumerate(sorted({o[1] for o in plan['objects']})):
        sprites[kind] = sprite(kind, recipes[kind], 700 + k)
        if D >= HD:
            sprites[kind] = foot_at_bottom_centre(*sprites[kind])
    for (oid, kind, x, y, ow, oh) in plan['objects']:
        img, anc, a, ex = sprites[kind]
        fx, fy = x + ow / 2.0, y + oh                     # the 1x object's foot
        at = (fx * D, fy * D)
        things.append((fy, img, anc, at))
        if ex is not None and D >= HD:
            casts.append(tree_shadow_hd(fx, fy, ex, w, h))          # the house rule: solid, a one-tone rim
        elif ex is not None:
            tcasts.append(CO.tree_shadow(fx, fy, ex, D, w, h))
        else:
            casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
        if D >= HD and kind in ('forest_bench', 'stump', 'mossy_log'):
            # a firm contact shade under what lies or stands on the ground, a little east
            x0_, _y0, x1_, _y1 = CO._bbox(a)
            half = (x1_ - x0_) / D / 2.0
            Yg, Xg = np.mgrid[0:h, 0:w]
            wx_, wy_ = (Xg + 0.5) / D, (Yg + 0.5) / D
            casts.append(((wx_ - fx - 1.0) / (half + 1.2)) ** 2 + ((wy_ - fy - 0.4) / 2.6) ** 2 <= 1.0)
        bx, by = (at[0] - anc[0]) / D, (at[1] - anc[1]) / D
        objects.append((oid, kind, (bx, by, img.width / D, img.height / D)))
    # low plants baked into the ground: ferns, the fairy ring, fallen leaves
    low = []
    hd = D >= HD
    for j, (x, y, seed, size) in enumerate(plan['dressing']['ferns']):
        if hd:
            # ferns, and a foxglove in four, in the shade of the woodland (no spiky rosettes)
            img, anc, a = (P4.foxglove_hd(D, seed=seed, size=min(1.1, 0.75 + size * 0.2)) if j % 4 == 3 else
                           P4.fern_hd(D, seed=seed, size=min(1.15, 0.55 + size * 0.3)))
        else:
            img, anc, a = P4.fern4(D, seed=seed, size=size * 0.8)
        x0, y0, x1, y1 = CO._bbox(a)
        anc = ((x0 + x1) / 2, y1)
        at = (x * D, y * D)
        low.append((y, img, anc, at, True))
        casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
    if hd:
        for (x, y, seed, kind) in mushrooms_at(plan):
            img, anc, a = P4.mushrooms_hd(D, n=3 + seed % 3, seed=seed, kind=kind)
            at = (x * D, y * D)
            low.append((y, img, anc, at, True))
    else:
        fr = plan['places']['fairy_ring']
        img, anc, a = P4.mushroom_ring4(D, w=int(fr['r'][0] * 2.6), h=int(fr['r'][1] * 2.4), seed=85)
        x0, y0, x1, y1 = CO._bbox(a)
        anc = ((x0 + x1) / 2, y1)
        at = (fr['at'][0] * D, (fr['at'][1] + fr['r'][1]) * D)
        low.append((fr['at'][1] + fr['r'][1], img, anc, at, True))
    if hd:
        # tufts where grass grows long: at the feet of trunks, stones and stumps, in clumps of 1
        # to 3 of different kinds and sizes (fine grass, broad leaf grass, a seeding tuft)
        from . import ground as GR
        rt = np.random.default_rng(733)
        for (oid, kind, x, y, ow, oh) in plan['objects']:
            if kind.split('_')[0] in ('forest', 'mossy', 'bush', 'holly', 'bramble') or rt.random() < 0.25:
                continue
            fx, fy = x + ow / 2.0, y + oh
            for j in range(int(rt.integers(1, 4))):
                side = -1 if (j + int(fx)) % 2 else 1
                tx = fx + side * (ow * rt.uniform(0.18, 0.42) + rt.uniform(0, 3))
                ty = fy + rt.uniform(-1.0, 2.5)
                Y_, X_ = int(ty * D), int(tx * D)
                if not (0 <= Y_ < h and 0 <= X_ < w) or not (is_fam(cv[Y_, X_], 'grass') or is_fam(cv[Y_, X_], 'leaf')):
                    continue
                fam = ('grass', 'leaf', 'grass')[int(rt.integers(0, 3))]
                img = GR.tuft(D, int(rt.integers(0, 10 ** 6)), float(rt.uniform(0.6, 1.5)), fam=fam)
                a = np.asarray(img)[..., 3] > 0
                x0, y0, x1, y1 = CO._bbox(a)
                low.append((ty, img, ((x0 + x1) / 2, y1), (tx * D, ty * D), False))
    if hd:
        low += lawn_dressing_hd(cv, plan, h, w)
    rng = np.random.default_rng(421)
    for (x, y, _k) in plan['dressing']['leaves']:
        limg = CO.fallen_leaf(D, rng)
        low.append((y - 30, limg, (limg.width / 2, limg.height), (x * D, y * D), False))
    if hd:
        # the ground detail goes in before the shade, which keeps it (compose.cast_shadows); under
        # every cast shadow the blades stand closer
        trees = [(x + ow / 2.0, y + oh, sprites[kind][3]['w'], kind) for (oid, kind, x, y, ow, oh)
                 in plan['objects'] if sprites[kind][3] is not None]
        shade = np.zeros((h, w), bool)
        for m in casts:
            shade |= m
        ground_detail_hd(cv, plan, trees, h, w, shade, soft=True)
    G = CO.ground_from_codes(cv, D)
    CO.cast_shadows(G, casts, tcasts, things + [(l[0], l[1], l[2], l[3]) for l in low if l[4]], D)
    ground = G.rgba()
    for (_y, im, an, at_, _c) in sorted(low, key=lambda t: t[0]):
        CO.paste(ground, im, an, at_)
    layers['ground'] = ground
    # the moving water: frames of only the changing texels
    codes = (G.fam.astype(np.int32) * 8 + G.tone).astype(np.int32)
    still = np.zeros_like(wm)
    for (x0, y0, x1, y1) in plan['water'].get('still', []):
        still[P(y0, 0):P(y1, 0), P(x0, 0):P(x1, 0)] = True
    moving = wm.copy()
    if plan['water'].get('animate'):
        box = np.zeros_like(wm)
        x0, y0, x1, y1 = plan['water']['animate']
        box[P(y0, 0):P(y1, 0), P(x0, 0):P(x1, 0)] = True
        moving &= box
    frames = animate.water(codes, moving, still & moving, D, thin=D >= HD)
    flow = animate.pack(frames)
    return Zone(ground=ground, objects=objects, sprites={k: v[0] for k, v in sprites.items()}, flow=flow, night=None,
                layers=layers, codes=codes)


def preview(z: Zone) -> Image.Image:
    """Everything composed as the game shows it (objects sorted by their feet)."""
    img = z.ground.copy()
    for (_oid, kind, (bx, by, bw, bh)) in sorted(z.objects, key=lambda o: o[2][1] + o[2][3]):
        sp = z.sprites[kind]
        X, Y = int(round(bx * D)), int(round(by * D))
        sx, sy = max(0, -X), max(0, -Y)
        img.alpha_composite(sp.crop((sx, sy, sp.width, sp.height)), (X + sx, Y + sy))
    return img

