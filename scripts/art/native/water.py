"""Water on any footprint: a body, its banks, its current and a fall, in palette codes.

The c-tiles scene draws its water along a centre line (scene.brook2) or in cells
(tiles.over); a zone that keeps an older walk mask has its water as a footprint instead.
These painters take that footprint (a boolean mask in texels) and draw it the same way:

- one calm body tone (2), shaded (tone 1) under the bank that faces away from the light
  (north and west), lit (tone 4) off the bank that faces it (south and east), a dark band
  (tones 0, 1) under a high north bank where the water is wide;
- the current as short streaks a tone up over their own one-texel shadow on lanes along the
  flow, about one lane cell in five lit, so most of the water stays plain; glints in pairs;
- an earth bank one world px wide (shaded on the north and west shores, lit on the south and
  east), then a one-texel grass lip, only where the ground beside is lawn;
- bed stones at the edges every ~15 world px, lit at the upper left.

fall() is a single drop: a sheet lit on its west edge, white water breaking over the lip,
broken white streaks, a plume and foam where it lands.

(After r7, scene.brook2 and the water branch of tiles.over can be expressed through these, so
water has one implementation; until then the pilot's own water stays as it is.)
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .ctx import D, P
from .palette import C, FI, is_fam

WATERS = ('water', 'water_warm', 'water_cool')


def _dirs(inside: np.ndarray):
    """Distance (texels) to the nearest pixel outside, and the direction to it."""
    p = np.pad(inside, 2, mode='edge')
    dist, (iy, ix) = ndi.distance_transform_edt(p, return_indices=True)
    yy, xx = np.mgrid[0:inside.shape[0], 0:inside.shape[1]]
    return dist[2:-2, 2:-2], iy[2:-2, 2:-2] - 2 - yy, ix[2:-2, 2:-2] - 2 - xx


def flow_field(mask: np.ndarray):
    """The flow direction (unit vectors) along the water's long axis (water_flow's structure
    tensor), pointing downhill."""
    import os
    import sys
    art = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if art not in sys.path:
        sys.path.insert(0, art)
    import water_flow
    fx, fy, _coh = water_flow._flow(mask)          # downhill already: south, or east where level
    fx, fy = fx.astype(float) / 256.0, fy.astype(float) / 256.0
    n = np.maximum(1e-6, np.hypot(fx, fy))
    return fx / n, fy / n


def paint(cv: np.ndarray, mask: np.ndarray, seed: int = 23) -> None:
    """Water on the footprint `mask` (texels) of the code canvas `cv`, with its banks."""
    H, W = cv.shape
    d, dy, dx = _dirs(mask)                 # inside: to the shore
    wd = d / D                              # world px from the shore
    t = np.full((H, W), 2)                  # the calm body
    north_or_west = (dy < 0) | ((dx < 0) & (np.abs(dx) >= np.abs(dy)))
    t[(wd <= 1.2) & north_or_west] = 1      # shade under the bank that faces away
    t[(wd <= 0.8) & ~north_or_west] = 4     # light off the bank that faces the light
    # a dark band under a high north bank, where the water is wide (measured down each column)
    run = np.zeros((H, W), int)
    for y in range(1, H):
        run[y] = np.where(mask[y], run[y - 1] + 1, 0)
    depth_down = np.zeros((H, W), int)
    for y in range(H - 2, -1, -1):
        depth_down[y] = np.where(mask[y], depth_down[y + 1] + 1, 0)
    wide = (run + depth_down) / D >= 12
    t[wide & (run <= 2 * D)] = 0
    t[wide & (run > 2 * D) & (run <= 4.5 * D)] = 1
    # the current: streaks of irregular length along the flow
    fx, fy = flow_field(mask)
    yy, xx = np.mgrid[0:H, 0:W]
    wx, wy = (xx + 0.5) / D, (yy + 0.5) / D
    u = wx * fx + wy * fy                   # along the flow (world px)
    v = -wx * fy + wy * fx                  # across it
    lane = np.floor((v + 1000) / 2.2).astype(np.int64)
    cell = np.floor((u + lane * 2.9) / 6.5).astype(np.int64)
    hh = ((lane * 73856093) ^ (cell * 19349663) ^ seed) & 0xffff
    off = (hh % 100) / 100.0 * 2.5
    ln = 1.5 + (hh // 100 % 6) * 0.5
    pos = u + lane * 2.9 - cell * 6.5 - off
    on = (hh % 14 < 3) & (wd > 1.2) & mask
    t[on & (pos >= 0) & (pos < ln)] = 3
    t[on & (pos >= ln) & (pos < ln + 1.0 / D + 0.01)] = 1
    out = cv.copy()
    out[mask] = FI['water'] * 8 + t[mask]
    cool = mask & (t <= 1) & wide
    out[cool & (run > 2 * D)] = C('water_cool', 1)
    # glints in pairs
    g = mask & (wd > 1.5) & ((((xx // P(3)) * 2654435761) ^ ((yy // P(2)) * 40503) ^ seed) % 61 == 0)
    for (y, x) in zip(*np.nonzero(g)):
        for k in range(P(2)):
            if x + k < W and mask[y, x + k]:
                out[y, x + k] = C('water', 5)
    # banks and the lip, on lawn only
    od, ody, odx = _dirs(~mask)             # outside: to the water
    lawn = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & ~mask
    bank = lawn & (od <= D + 0.01)
    water_south = ody > 0
    water_east = (odx > 0) & (np.abs(odx) > np.abs(ody))
    water_west = (odx < 0) & (np.abs(odx) > np.abs(ody))
    out[bank & water_south] = C('earth', 1)                  # the north bank: in its own shade
    out[bank & ~water_south] = C('earth_warm', 3)            # the south bank faces the light
    out[bank & water_east] = C('earth', 2)                   # the west shore, shaded
    out[bank & water_west] = C('earth_warm', 3)              # the east shore, lit
    lip = lawn & (od > D + 0.01) & (od <= D + 1.01)
    lit_lip = (ody < 0) | (odx < 0)
    out[lip & lit_lip] = C('grass', 4)
    out[lip & ~lit_lip] = C('grass', 2)
    # bed stones at the edges, lit high-left, dark beneath
    edge = mask & (wd > 0.3) & (wd <= 1.0)
    ey, ex = np.nonzero(edge)
    rng = np.random.default_rng(seed)
    if len(ey):
        order = np.lexsort((ey, ex))
        last = -99.0
        for k in order:
            x0w = ex[k] / D
            if x0w - last < 15.0 or rng.random() < 0.5:
                continue
            last = x0w
            cy, cx = ey[k] / D, ex[k] / D
            rx, ry = rng.uniform(1.4, 2.1), rng.uniform(1.0, 1.4)
            for Y in range(P(cy - ry, 0), P(cy + ry, 0) + 1):
                for X in range(P(cx - rx, 0), P(cx + rx, 0) + 1):
                    if 0 <= Y < H and 0 <= X < W and (mask[Y, X] or bank[Y, X]):
                        vy = (Y / D + 0.5 / D - cy) / ry
                        vx = (X / D + 0.5 / D - cx) / rx
                        if vx * vx + vy * vy <= 1:
                            out[Y, X] = C('stone', 4 if (vy < -0.2 and vx < 0.3) else (2 if vy > 0.45 else 3))
    cv[:] = out


def fall(cv: np.ndarray, x0: float, w: float, y0: float, y1: float, seed: int = 11) -> None:
    """A single drop from a lip at y0 into water at y1 (world px), x0..x0+w wide."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    cx = x0 + w / 2.0
    streak_x = [-1.6, -0.5, 0.6, 1.6]
    gaps = {sx: [(rng.uniform(0, 40), rng.uniform(2, 6)) for _ in range(3)] for sx in streak_x}
    for Y in range(P(y0, 0), P(y1, 0)):
        yw = Y / D
        hw = w / 2.0 + (yw - y0) / 30.0
        hl = hw + 0.4 * np.sin(yw / 3.3)
        hr = hw + 0.4 * np.sin(yw / 2.7 + 1.0)
        for X in range(max(0, P(cx - hw - 1.5, 0)), min(W, P(cx + hw + 1.5, 0) + 1)):
            u = X / D + 0.5 / D - cx
            if not (-hl <= u <= hr):
                continue
            if u < -hl + 1.0:
                tt = 4
            elif u > hr - 1.0:
                tt = 1
            elif u > hr - 2.0:
                tt = 2
            else:
                tt = 3
            c = C('water', tt)
            for sx in streak_x:
                if abs(u - sx) < 0.5 and tt in (2, 3):
                    if not any(g0 <= (yw - y0) % 40 < g0 + gl for (g0, gl) in gaps[sx]):
                        c = C('snow', 4) if sx < 1 else C('water', 4)
            lipw = 1.3 + 0.8 * abs(np.sin(u * 1.9 + 0.7))
            if yw < y0 + lipw:
                c = C('snow', 5) if u < hw - 1.0 else C('snow', 4)
            elif yw < y0 + lipw + 1.0 / D + 0.01:
                c = C('water', 4) if u < 0 else C('water', 2)
            cv[Y, X] = c
    # the plume and the foam where it lands
    parts = [(cx + rng.uniform(-0.6, 0.6) * w, y1 + rng.uniform(-0.4, 0.4) * 2.4, w * rng.uniform(0.4, 0.6),
              2.4 * rng.uniform(0.6, 0.95)) for _ in range(5)]
    for Y in range(P(y1 - 4, 0), P(y1 + 4, 0) + 1):
        for X in range(P(cx - w * 1.5, 0), P(cx + w * 1.5, 0) + 1):
            if not (0 <= Y < H and 0 <= X < W):
                continue
            r = min(((X / D - px) / pw) ** 2 + ((Y / D - py) / ph) ** 2 for (px, py, pw, ph) in parts)
            if r <= 1.0:
                vv = (Y / D - y1) / 2.4
                cv[Y, X] = C('snow', 5) if (vv < -0.2 and r < 0.75) else (C('snow', 4) if r < 0.75 else C('water', 4))
    for k in range(8):                       # spray in pairs beside the plume
        side = -1 if k % 2 else 1
        sx = cx + side * (w * 0.9 + (k // 2) * 1.4 + rng.uniform(0, 0.8))
        sy = y1 - 2 - (k // 2) * 0.8 - rng.uniform(0, 0.6)
        Y, X = P(sy, 0), P(sx, 0)
        if 0 <= Y < H and 0 <= X < W:
            cv[Y, X] = C('snow', 5) if k < 4 else C('water', 4)


def wet_rock(cv: np.ndarray, x0: float, w: float, y0: float, y1: float) -> None:
    """The rock beside a fall is dark and wet: a tone down within 2 world px of the sheet."""
    H, W = cv.shape
    for Y in range(P(y0, 0), min(H, P(y1, 0))):
        for X in range(max(0, P(x0 - 2.5, 0)), min(W, P(x0 + w + 2.5, 0))):
            c = cv[Y, X]
            if c >= 0 and (c // 8) not in [FI[n] for n in WATERS] and c % 8 not in (0, 6, 7) and \
                    (c // 8) in (FI['stone'], FI['stone_warm'], FI['stone_cool'], FI['crag'], FI['crag_warm'], FI['crag_cool']):
                cv[Y, X] = c - 1


# ------------------------------------------------------------------------------------------------
# density 3 and up (25 Oct, Matt: "this scene needs to be improved almost everywhere")
# ------------------------------------------------------------------------------------------------
def smooth_mask(m1: np.ndarray, sigma: float = 0.9) -> np.ndarray:
    """A 1x footprint (world px) at this density with natural banks: upsampled, softened by
    sigma world px and cut at the middle, so a run of 1 px steps becomes a curve and every
    corner is rounded (the soft grid), and the water's width is kept."""
    k = int(round(D))
    up = np.kron(m1.astype(float), np.ones((k, k)))
    return ndi.gaussian_filter(up, sigma * D) > 0.5


def paint_hd(cv: np.ndarray, mask: np.ndarray, seed: int = 23) -> np.ndarray:
    """Water on a smooth footprint at density 3 and up, with its banks. Depth from the bank to
    the middle: a lit shallow rim on the south and east shores, a body tone, a deep tone in the
    middle of wide water, the bank's shade along the north and west shores. Gentle highlights:
    one-texel ripple lines along the flow (a lit line over a darker one), never blocks. Banks: a
    wet dark edge, an earth bank lit or shaded by its facing, stones lying on its lip, and on the
    north shore the grass hanging over it in leaf-sized tips. Returns the bank mask (texels)."""
    H, W = cv.shape
    d_in, dy, dx = _dirs(mask)
    wd = d_in / D
    north_or_west = (dy < 0) | ((dx < 0) & (np.abs(dx) >= np.abs(dy)))
    # the water's half width: the deepest point of each part, spread back over it
    width = ndi.grey_dilation(np.where(mask, wd, 0), size=(int(6 * D) | 1, int(6 * D) | 1))
    t = np.full((H, W), 2)
    deep = mask & (wd > 3.4) & (width > 5.5)
    t[deep] = 1
    t[mask & (wd <= 1.0) & ~north_or_west] = 3          # the lit shallows (the near, south and east shores)
    # under the north and west bank the water is darker, stepping back to the body (eastward-edges
    # 5.3: 2 to 8 px, 3 to 4 steps; #288 review S9)
    t[mask & (wd <= 2.4) & north_or_west] = 1
    t[mask & (wd <= 1.3) & north_or_west] = 1            # the bank's shade on the water
    t[mask & (wd <= 0.8) & north_or_west] = 0
    fam = np.full((H, W), FI['water'])
    # (the deep stays in the water's own ramp: no navy hole in the middle)
    # ripple lines along the flow: one texel thin, 2 to 5 world px long, a lit line over the
    # body tone's own shade (one texel below it)
    fx, fy = flow_field(mask)
    yy, xx = np.mgrid[0:H, 0:W]
    wx, wy = (xx + 0.5) / D, (yy + 0.5) / D
    u = wx * fx + wy * fy
    v = -wx * fy + wy * fx
    lane = np.floor((v + 1000) / 2.6).astype(np.int64)
    cell = np.floor((u + lane * 3.7) / 9.0).astype(np.int64)
    hh = ((lane * 73856093) ^ (cell * 19349663) ^ seed) & 0xffff
    off = (hh % 100) / 100.0 * 3.0
    ln = 2.0 + (hh // 100 % 4) * 1.0
    pos = u + lane * 3.7 - cell * 9.0 - off
    vin = (v + 1000) - lane * 2.6
    on = (hh % 9 < 3) & (wd > 1.0) & mask
    line = on & (pos >= 0) & (pos < ln) & (vin < 1.0 / D)
    t[line] = np.minimum(4, t[line] + 2)
    below = np.zeros_like(line)
    below[1:] = line[:-1]
    below &= mask & ~line & on
    t[below] = np.maximum(0, t[below] - 1)
    # a 1 px very light waterline where the water meets its bank, all round (5.3)
    edge_w = mask & ~ndi.binary_erosion(mask, structure=np.ones((3, 3), bool))
    t[edge_w] = np.where(north_or_west[edge_w], 3, 4)
    out = cv.copy()
    out[mask] = fam[mask] * 8 + t[mask]
    # the banks, on lawn and paths only
    od, ody, odx = _dirs(~mask)
    land = ~mask & (cv >= 0) & (cv % 8 < 6)
    wet = land & (od <= 1.01)
    bank = land & (od <= D + 1.01) & ~wet
    water_south = (ody > 0) & (np.abs(ody) >= np.abs(odx))
    water_west = (odx < 0) & (np.abs(odx) > np.abs(ody))
    out[wet] = C('earth', 0)
    out[wet & ~water_south] = C('earth', 1)
    out[bank & water_south] = C('earth', 1)                  # the north bank, in its own shade
    out[bank & ~water_south] = C('earth_warm', 3)            # banks facing the light
    out[bank & ~water_south & ~water_west & (odx > 0)] = C('earth', 2)
    # the north bank's grass hangs over it in rounded lobes, not one-texel tips (#288 review B2:
    # the tips were per-texel teeth); the lobes' depth wanders slowly along the bank and the
    # outline is drawn on the soft grid (softedge), as the paths are
    from . import softedge as SE
    from .terrain import noise as TN
    lawn = (is_fam(cv, 'grass') | is_fam(cv, 'leaf')) & ~mask & ~(wet | bank)
    reach = TN.vnoise_hd(wx, wy, 7.0, seed + 31) * (D - 1.0)          # the bank keeps 2 texels of face
    over = (wet | bank) & water_south & (od >= (D + 1.0) - reach + 0.5) & (od > 1.01)
    reach2 = TN.vnoise_hd(wx, wy, 7.0, seed + 37) * (D - 1.0)
    over |= (wet | bank) & ~water_south & (np.abs(odx) > np.abs(ody)) & (od >= (D + 1.0) - reach2 + 0.5) & (od > 1.01)
    turf = SE.soft(lawn | over, smooth=0.45, min_area=1.0) & ~mask
    over = turf & (wet | bank)
    out[over] = C('grass', 2)
    out[over & ~ndi.binary_erosion(over, iterations=1) & np.roll(~over, 1, axis=0)] = C('grass', 3)
    # where smoothing took turf away from the bank's edge, the bank fills it
    gone = (wet | bank) & ~turf
    out[gone & ~(wet | bank)] = C('earth', 1)
    nb = lawn & ~turf & ~mask
    out[nb] = np.where(water_south[nb], C('earth', 1), C('earth_warm', 3))
    # one last pass on the soft grid over water and bank together: what the turf's lobes left as
    # a one-texel tooth on the outline goes back to turf, a one-texel bite becomes bank
    wb = (mask | wet | bank) & ~over
    wb2 = SE.soft(wb, smooth=0.35, min_area=1.0)
    out[wb & ~wb2 & ~mask] = C('grass', 2)
    turf = (turf | (wb & ~wb2)) & ~mask
    add = wb2 & ~wb & ~mask
    out[add] = np.where(water_south[add], C('earth', 1), C('earth_warm', 3))
    over = turf & (wet | bank)
    lip = turf & ~over & ndi.binary_dilation(wb2 & ~mask, structure=np.ones((3, 3), bool))
    lit_lip = (ody < 0) | (odx < 0)
    out[lip & lit_lip] = C('grass', 4)
    out[lip & ~lit_lip] = C('grass', 2)
    # stones on the bank's lip, lit at the upper left, a dark row beneath; never in a line
    rng = np.random.default_rng(seed + 1)
    wide_near = ndi.grey_dilation(np.where(mask, width, 0), size=(int(4 * D) | 1, int(4 * D) | 1))
    ey, ex = np.nonzero(bank & (od > D * 0.6) & (wide_near > 1.2))
    if len(ey):
        placed = []
        for k in rng.permutation(len(ey))[:4000]:
            cy, cx = ey[k] / D, ex[k] / D
            narrow = wide_near[ey[k], ex[k]] < 3.0
            if any((cx - a) ** 2 + (cy - b) ** 2 < (24.0 if narrow else 15.0) ** 2 for a, b in placed) or \
                    rng.random() < (0.85 if narrow else 0.7):
                continue
            placed.append((cx, cy))
            rx, ry = rng.uniform(1.0, 2.8), rng.uniform(0.8, 1.7)
            for Y in range(P(cy - ry, 0), P(cy + ry, 0) + 2):
                for X in range(P(cx - rx, 0), P(cx + rx, 0) + 2):
                    if not (0 <= Y < H and 0 <= X < W):
                        continue
                    vy = (Y / D + 0.5 / D - cy) / ry
                    vx = (X / D + 0.5 / D - cx) / rx
                    q = vx * vx + vy * vy
                    if q <= 1:
                        out[Y, X] = C('stone', 4 if (vy < -0.25 and vx < 0.35) else (2 if vy > 0.45 or vx > 0.7 else 3))
                    elif q <= 1.5 and vy > 0.6 and mask[Y, X]:
                        out[Y, X] = C('water', 1)
    cv[:] = out
    return bank | wet


def fall_hd(cv: np.ndarray, x0: float, w: float, y0: float, y1: float, seed: int = 11) -> None:
    """A fall with volume (density 3 and up): a stone lip across its top that the water pours
    over (the crest a lit white curl), the sheet shaded as a curved ribbon (lit west, a body,
    shade on the east) with falling streaks in broken runs, darker where it thins to the foot, a
    churning white plume where it lands, foam rings spreading on the pool and spray beside it."""
    H, W = cv.shape
    rng = np.random.default_rng(seed)
    cx = x0 + w / 2.0
    # the lip: the water runs over a worn ledge stone, a little wider than the fall, rounded at
    # its ends, its top wet and lit, its face dark; the water's own surface slides over it
    rx, ry, ly = w / 2.0 + 2.2, 1.7, y0 - 0.9
    for Y in range(P(ly - ry, 0), P(ly + ry, 0) + 1):
        for X in range(P(cx - rx, 0), P(cx + rx, 0) + 1):
            if not (0 <= Y < H and 0 <= X < W):
                continue
            u, v = (X / D + 0.5 / D - cx) / rx, (Y / D + 0.5 / D - ly) / ry
            if u * u + v * v > 1.0:
                continue
            if abs(X / D + 0.5 / D - cx) < w / 2.0 - 0.3 and v < 0.6:
                cv[Y, X] = C('water', 4) if v < -0.2 else C('water', 3)       # the glassy tongue over the lip
            else:
                cv[Y, X] = C('stone', 4) if v < -0.35 else (C('stone', 2) if v < 0.5 else C('stone', 1))
    cols = {}
    for Y in range(P(y0, 0), P(y1, 0)):
        yw = Y / D
        f = (yw - y0) / max(1.0, (y1 - y0))
        hw = w / 2.0 + f * 1.4
        hl = hw + 0.35 * np.sin(yw / 3.1)
        hr = hw + 0.35 * np.sin(yw / 2.6 + 1.0)
        for X in range(max(0, P(cx - hw - 1.5, 0)), min(W, P(cx + hw + 1.5, 0) + 1)):
            u = X / D + 0.5 / D - cx
            if not (-hl <= u <= hr):
                continue
            s = (u + hl) / (hl + hr)                       # 0 west .. 1 east across the ribbon
            tt = 4 if s < 0.18 else (3 if s < 0.62 else (2 if s < 0.86 else 1))
            fam = 'water'
            c = C(fam, tt)
            key = int((X / D - x0) * 1.6)
            if key not in cols:
                cols[key] = (rng.uniform(0, 60), rng.uniform(9, 22), rng.uniform(3, 8), rng.random() < 0.45)
            ph, run, gap, on_ = cols[key]
            if on_ and ((yw - y0 + ph) % (run + gap)) < run and 0.1 < s < 0.8:
                c = C('snow', 4) if s < 0.5 else C('snow', 2)     # a falling streak
            if yw < y0 + 1.4 + 0.5 * np.sin(u * 2.3):
                c = C('snow', 5) if s < 0.7 else C('snow', 4)     # the crest curling over the lip
            elif yw < y0 + 1.4 + 1.0 / D + 0.01 + 0.5 * np.sin(u * 2.3):
                c = C('water', 2)                                   # its shade under the curl
            cv[Y, X] = c
    # the plume: churning white where it lands, foam rings spreading on the pool
    parts = [(cx + rng.uniform(-0.7, 0.7) * w, y1 + rng.uniform(-0.6, 0.4) * 2.6, w * rng.uniform(0.45, 0.7),
              2.6 * rng.uniform(0.65, 1.0)) for _ in range(6)]
    for Y in range(P(y1 - 5, 0), P(y1 + 5, 0) + 1):
        for X in range(P(cx - w * 1.8, 0), P(cx + w * 1.8, 0) + 1):
            if not (0 <= Y < H and 0 <= X < W):
                continue
            r = min(((X / D - px) / pw) ** 2 + ((Y / D - py) / ph) ** 2 for (px, py, pw, ph) in parts)
            if r <= 1.0:
                vv = (Y / D - y1) / 2.6
                lit = (X / D - cx) < 0.3 * w
                cv[Y, X] = C('snow', 5) if (vv < 0 and r < 0.6 and lit) else (C('snow', 4) if r < 0.7 else C('snow', 2))
    for k, (rx, ry) in enumerate(((w * 1.6, 2.6), (w * 2.3, 3.6))):    # rings on the pool
        for Y in range(P(y1 - ry, 0), P(y1 + ry + 2.5, 0) + 1):
            for X in range(P(cx - rx - 1, 0), P(cx + rx + 1, 0) + 1):
                if not (0 <= Y < H and 0 <= X < W) or not ((cv[Y, X] // 8) in [FI[n] for n in WATERS]):
                    continue
                q = ((X / D - cx) / rx) ** 2 + ((Y / D - (y1 + 1.2)) / ry) ** 2
                if abs(q - 1.0) < 0.09 and (Y / D) > y1 - 0.5 and ((X // P(2)) + k) % 3:
                    cv[Y, X] = C('water', 4) if k == 0 else C('water', 3)
    for k in range(10):                      # spray drops beside the plume
        side = -1 if k % 2 else 1
        sx = cx + side * (w * 1.0 + (k // 2) * 1.3 + rng.uniform(0, 1.0))
        sy = y1 - 2.5 - (k // 2) * 1.0 - rng.uniform(0, 0.8)
        Y, X = P(sy, 0), P(sx, 0)
        for (a, b) in ((0, 0), (0, 1)):
            if 0 <= Y + a < H and 0 <= X + b < W:
                cv[Y + a, X + b] = C('snow', 5) if k < 5 else C('snow', 4)
