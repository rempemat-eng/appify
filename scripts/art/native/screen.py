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
def sun(cv: np.ndarray, m: np.ndarray, heart: float = 10.0, fade: float = 4.0) -> None:
    """A sun pool: the lawn's warm sibling at its own tone, the heart (`heart` texels in) a tone
    up, a 2 x 2 checker `fade` texels wide at the edge (the one place dither is used: light)."""
    lawn = m & (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & (cv % 8 < 6)
    dist = ndi.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]
    yy, xx = np.mgrid[0:cv.shape[0], 0:cv.shape[1]]
    chk = ((xx // 2 + yy // 2) % 2) == 0
    sel = lawn & ((dist > fade) | chk)
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
    k = int(round(D))
    up = np.kron(m1.astype(float), np.ones((k, k)))
    sway = np.zeros(up.shape[0])
    for Y in range(up.shape[0]):
        yw = Y / D
        if 32 <= yw <= (rows[-1] if rows else 230):
            taper = min(1.0, (yw - 32) / 24.0, ((rows[-1] if rows else 230) - yw) / 24.0)
            sway[Y] = 1.8 * D * taper * np.sin(yw / 15.0 + 0.4)
    west = np.zeros(up.shape[1], bool)
    west[:int(110 * D)] = True                        # only the rill sways
    for Y in np.nonzero(sway)[0]:
        row = up[Y].copy()
        up[Y, west] = ndi.shift(row, sway[Y], order=1, mode='nearest')[west]
    return ndi.gaussian_filter(up, 0.9 * D)[:H * k, :W * k] > 0.5


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
    X0, X1, Y0, Y1 = P(x0, 0), P(x0 + w, 0), P(ya, 0), P(yb, 0)
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
        for py in np.linspace(ya + 1.0, yb - 0.8, 4):
            for Y in range(P(py - 5.0, 0), P(py + 0.4, 0)):
                for j in range(-1, P(1.4) + 1):
                    edge_ = j < 0 or j >= P(1.4)
                    put(Y, X + j, C('timber_cool', 0) if edge_ else C('timber', (4 if j == 0 else 3) if lit else 2))
            if not lit:
                for j in range(P(1.0)):
                    put(P(py + 0.4, 0) + j, X + P(1.4) + 1, C('water_cool', 1) if water[min(H - 1, P(py + 0.4, 0) + j), min(W - 1, X + P(1.4) + 1)] else C('earth', 1))
        rail_y0, rail_y1 = ya - 5.0, yb - 5.0
        for Y in range(P(rail_y0, 0), P(rail_y1, 0)):
            for j in range(-1, P(1.2) + 1):
                edge_ = j < 0 or j >= P(1.2)
                put(Y, X + j, C('timber_cool', 0) if edge_ else C('timber', 5 if (lit and j == 0) else (4 if lit else 2)))


def path_hd(cv: np.ndarray, pts, hw0: float, seed: int = 0, spur: bool = False) -> None:
    """A worn footpath at density 3 and up: trodden dirt whose edge wanders at two scales (no
    hard rim), the lawn creeping in over it in leaf-sized tips and a few grass islands near the
    margin; the dirt mottled in soft patches (trodden darker, dry lighter) with pebbles of 1 to
    1.6 world px lying here and there, lit at the upper left with a shade under them. A spur
    (a short side path) widens where it leaves the main path and ends in a small apron."""
    from scipy.spatial import cKDTree
    from .terrain import noise as TN
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
    hw = hw0 + 0.6 * np.sin(sa / 11.0 + seed) + (TN.vnoise(wx, wy, 6.0, 41 + seed) - 0.5) * 1.8 \
        + (TN.vnoise(wx, wy, 1.6, 43 + seed) - 0.5) * 0.9
    if spur:
        hw = hw + 4.0 * np.exp(-sa / 4.0) + 1.8 * np.exp(-((sarc[-1] - sa) - 2.5) ** 2 / 20.0)
        hw = hw * np.clip((sarc[-1] - sa + 2.5) / 5.0, 0.35, 1.0)
    cur = cv[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    grassy = is_fam(cur, 'grass') | is_fam(cur, 'leaf')
    # the lawn's tips over the margin: leaf-shaped, one every 3 texels, 1 to 4 texels in
    tip = ((XX // 3) * 2654435761 ^ (YY // 5) * 40503 ^ seed) & 0xff
    creep = ((tip % 5) + ((XX % 3) == 1)) / D * (dist > hw - 1.6)
    dirt = grassy & (dist <= hw - creep)
    isl = (TN.vnoise(wx, wy, 2.2, 47 + seed) > 0.8) & (dist > hw - 2.4) & (dist < hw - 0.8)
    dirt &= ~isl
    m1 = TN.vnoise(wx, wy, 5.0, 51 + seed) + 0.35 * TN.vnoise(wx, wy, 1.8, 53 + seed)
    t = np.full(dirt.shape, 3)
    t[m1 < 0.42] = 2
    t[m1 > 1.0] = 4
    fam = np.full(dirt.shape, FI['path'])
    fam[TN.vnoise(wx, wy, 9.0, 57 + seed) > 0.62] = FI['path_warm']
    out = cur.copy()
    out[dirt] = fam[dirt] * 8 + t[dirt]
    # under the lawn's lip on the north and west margins, a tone of shade (the grass is higher)
    Pd = np.pad(dirt, 1)
    north_grass = dirt & (~Pd[:-2, 1:-1] | ~Pd[1:-1, :-2])
    out[north_grass] = step(out[north_grass], -1)
    # pebbles
    ph = ((XX // P(4.5)) * 73856093 ^ (YY // P(4.0)) * 19349663 ^ (seed * 7 + 5)) & 0xffff
    cy0, cx0 = (YY // P(4.0)) * P(4.0) + (ph % P(4.0)), (XX // P(4.5)) * P(4.5) + ((ph >> 4) % P(4.5))
    rr = np.maximum(1, np.round((0.5 + ((ph >> 9) % 3) * 0.25) * D)).astype(int)
    peb = dirt & (ph % 7 == 0) & (dist < hw - 1.2)
    ry_, rx_ = (YY - cy0), (XX - cx0)
    inp = peb & (ry_ ** 2 + (rx_ * 0.8) ** 2 <= rr * rr)
    out[inp] = np.where((ry_[inp] < 0) & (rx_[inp] <= 0), C('stone', 4), C('stone', 3))
    sh = peb & ~inp & (ry_ >= 0) & (ry_ <= rr + 1) & (rx_ >= -rr + 1) & (rx_ <= rr + 1) & \
        ((ry_ - 1) ** 2 + ((rx_ - 1) * 0.8) ** 2 <= rr * rr)
    out[sh & dirt] = step(out[sh & dirt], -1)
    cv[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] = out


def tree_shadow_hd(x, y, ex, W, H) -> np.ndarray:
    """A tree's shadow at density 3 and up: the crown's shade as a ground ellipse that starts at
    the trunk's foot and reaches east and a little south (the sun at the upper left), as wide as
    the crown, so it always reads as that tree's."""
    cw = ex['w']
    cx, cy = x + 0.2 * cw, y + 0.035 * cw
    rx, ry = 0.5 * cw, 0.17 * cw + 2.0
    Y, X = np.mgrid[0:H, 0:W]
    wx, wy = (X + 0.5) / D, (Y + 0.5) / D
    return ((wx - cx) / rx) ** 2 + ((wy - cy) / ry) ** 2 <= 1.0


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
    layers['lawn'] = cv.copy()
    pl = plan['places']
    g = pl['glade']
    sun(cv, blob(*g['at'], *g['r'], seed=g['seed'], rough=g['rough'], w=w, h=h), heart=10 ** 6, fade=P(3))
    s = pl['sun']
    sun(cv, blob(*s['at'], *s['r'], seed=s['seed'], rough=s['rough'], w=w, h=h), heart=P(4), fade=P(2))
    for (lx, ly, rx, ry) in pl['light_pools']:
        sun(cv, blob(lx, ly, rx, ry, seed=int(lx * 7 + ly), rough=0.3, w=w, h=h), heart=P(5), fade=P(2))
    for k, p in enumerate(plan['paths']):
        if D >= HD:
            path_hd(cv, [tuple(q) for q in p['points']], hw0=p['radius'] - 2.0, seed=k, spur=p.get('spur', False))
        else:
            SC.worn2(cv, [tuple(q) for q in p['points']], hw0=p['radius'] - 2.0)
    co, ci = pl['circle_out'], pl['circle_in']
    ring = blob(*co['at'], *co['r'], seed=co['seed'], rough=co['rough'], w=w, h=h) & \
        ~blob(*ci['at'], *ci['r'], seed=ci['seed'], rough=ci['rough'], w=w, h=h)
    trodden(cv, ring)
    layers['places'] = cv.copy()
    hd = D >= HD
    wm = water_mask_hd(plan, W, H) if hd else texels(mask_rle(plan['water']['water_rle'], W, H))
    rock = texels(mask_rle(plan['rock']['rock_rle'], W, H))
    scree(cv, plan['rock']['talus']['depth'], wm)
    for b in sorted(plan['rock']['talus']['boulders'], key=lambda b: b['at'][1]):
        boulder(cv, b['at'][0], b['at'][1], b['size'][0], b['size'][1], b['seed'], moss=b['moss'])
    f = plan['water']['fall']
    br = pl['bridge']
    if hd:
        WA.paint_hd(cv, wm)
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
    keep = (cv % 8 >= 6) | np.isin(cv // 8, [FI['water'], FI['water_warm'], FI['water_cool']])
    for _ in range(2):
        Pd = np.pad(cv, 1, mode='edge')
        nb = np.stack([Pd[:-2, 1:-1], Pd[2:, 1:-1], Pd[1:-1, :-2], Pd[1:-1, 2:]])
        lone = (cv != nb[0]) & (cv != nb[1]) & (cv != nb[2]) & (cv != nb[3]) & ~keep & (cv >= 0)
        for y, x in zip(*np.nonzero(lone)):
            v = list(nb[:, y, x])
            cv[y, x] = max(set(v), key=v.count)
    return cv, wm, rock


def build() -> Zone:
    plan, biome = ctx.PLAN, ctx.BIOME
    layers = {}
    cv, wm, rock = terrain(plan, layers)
    G = CO.ground_from_codes(cv, D)
    h, w = cv.shape
    recipes = biome['recipes']
    sprites, objects, things, casts, tcasts = {}, [], [], [], []
    for k, kind in enumerate(sorted({o[1] for o in plan['objects']})):
        sprites[kind] = sprite(kind, recipes[kind], 700 + k)
    for (oid, kind, x, y, ow, oh) in plan['objects']:
        img, anc, a, ex = sprites[kind]
        fx, fy = x + ow / 2.0, y + oh                     # the 1x object's foot
        at = (fx * D, fy * D)
        things.append((fy, img, anc, at))
        if ex is not None:
            tcasts.append(tree_shadow_hd(fx, fy, ex, w, h) if D >= HD else CO.tree_shadow(fx, fy, ex, D, w, h))
        else:
            casts.append(CO.shadow_mask(a, anc, D, w, h, at, *CO.SHADOW))
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
    rng = np.random.default_rng(421)
    for (x, y, _k) in plan['dressing']['leaves']:
        limg = CO.fallen_leaf(D, rng)
        low.append((y - 30, limg, (limg.width / 2, limg.height), (x * D, y * D), False))
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

