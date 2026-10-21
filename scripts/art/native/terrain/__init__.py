"""The terrain canvas for a plan: the c-tiles tiers, faces, stairs, water and decals in palette
codes, with the hand-placed dressing. The plants (bushes, ferns, tufts, flowers) are returned
as items for the sprites in compose.py.

    codes, items = terrain.canvas()
"""
import numpy as np

from .. import ctx
from ..palette import FI
from . import scene as SC
from . import sheets


def items_now(cv):
    plan = ctx.PLAN
    base = cv.copy()
    items = SC.place_decals(cv)
    x0, y0, x1, y1 = plan['decals']['props_box']
    now_items = [it for it in items if not (x0 <= it[2] <= x1 and y0 <= it[0] <= y1 and it[1] in ('bush', 'lump', 'fern', 'b32'))
                 or (it[1] == 'lump' and it[4] >= 91)]     # r5: the laid seam boulders stay
    kinds = {'white': 'white', 'yellow': 'yellow', 'violet': 'violet', 'red': 'red', 'blue': 'violet'}

    def wet(x, y):   # no dressing on the brook, the track, the pool, a face or a path
        if (int(x // 16), int(y // 16)) in SC.WET or (int(x // 16), int(y // 16)) in SC.TRAIL:
            return True
        bx0, by0, bx1, by1 = SC.BED
        if bx0 - 3 <= x <= bx1 + 3 and by0 - 3 <= y <= by1 + 6:
            return True
        if any(c0 - 4 <= x <= c1 + 4 and r0 - 4 <= y <= r1 for (c0, r0, c1, r1) in SC.CROWNS):
            return True
        return not SC._foot_ok(cv, x - 3, y, 6)
    for k, (fx, fy, kind, n) in enumerate(plan['dressing']['flowers']):
        if not wet(fx, fy):
            now_items.append((fy, 'flowers', int(fx) - 3, int(fy) - 5, 900 + k, kinds[kind]))
    for k, (tx, ty, sz) in enumerate(plan['dressing']['tufts']):
        if not wet(tx, ty):
            now_items.append((ty, 'tuft', int(tx) - 3, int(ty) - 6, k % 3, None))
    now_items.sort(key=lambda t: t[0])
    return base, now_items


def canvas():
    """The scene's terrain canvas (codes, the margin rows above the screen cut off) and its
    plant items; lone pixels take their most common neighbour (outlines, water and snow
    sparkles excepted)."""
    cv, hp_, occ = SC.render()
    base, now_items = items_now(cv)
    cv_now = cv
    SC.PLANTS.clear()
    SC.draw_items(cv_now, now_items)
    keep = (cv_now % 8 >= 6) | np.isin(cv_now // 8, [FI['water'], FI['water_warm'], FI['water_cool']])
    for _ in range(2):
        P_ = np.pad(cv_now, 1, mode='edge')
        nb = np.stack([P_[:-2, 1:-1], P_[2:, 1:-1], P_[1:-1, :-2], P_[1:-1, 2:]])
        lone = (cv_now != nb[0]) & (cv_now != nb[1]) & (cv_now != nb[2]) & (cv_now != nb[3]) & ~keep & (cv_now >= 0)
        ys, xs = np.nonzero(lone)
        for y, x in zip(ys, xs):
            v = list(nb[:, y, x])
            cv_now[y, x] = max(set(v), key=v.count)
    return cv_now, now_items, list(sheets.SHEET_TUFTS)
