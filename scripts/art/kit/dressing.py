"""Edge dressing: the tufts, hanging blades and pebbles along a transition, as decals.

docs/world-editor.md, "Transitions". The transition tiles are deterministic (edges.py); what makes
an edge look grown rather than drawn (Eastward 12 and 13: a tuft or a stone breaking the rim every
so often) is laid over them as small sprites. Each cell edge between two materials of a dressed pair
gets at most one decal, chosen by a hash of the cell edge, at a hashed place along it, seated on the
lumped outline (the edge's lump curve, edges.profile_curve, is known from the same hash as the
tile's). Godot (world/terrain/terrain_dressing.gd) and compose.render place them identically.

Decals are palette codes with an alpha (code in R and G, alpha in A, like the fills), painted once
from softground's own tuft and pebble recipes:

    tuft_*     a tuft rooted on the turf's south lip, its blades leaning out over the dirt
    blades_*   two or three blades hanging from the turf's north lip over the dirt
    pebble_*   a pebble or a stone lying across the edge, lit at its upper left
"""
from __future__ import annotations

import numpy as np

from scripts.art.native import softground as GD
from scripts.art.native.palette import C, step

from .edges import CELL, HALF

DECAL = 16            # decal canvas, texels


def _canvas():
    return np.full((DECAL, DECAL), -1, np.int32)


def tuft(seed: int):
    """softground.sunken_edge's lip tuft: blades above the root, lighter than the field."""
    rng = np.random.default_rng(seed)
    cv = _canvas()
    base = step(C('grass', 3), 1)
    shp = [(dy, dx, dt) for (dy, dx, dt) in GD.tuft_shape(rng, rng.uniform(1.1, 1.7)) if dy < 0]
    ay, ax = DECAL - 1, DECAL // 2
    for dy, dx, dt in shp:
        y, x = ay + dy + 1, ax + dx
        if 0 <= y < DECAL and 0 <= x < DECAL:
            cv[y, x] = step(base, dt)
    return cv, (ax, ay)


def blades(seed: int):
    """Blades hanging over a north lip: two or three, 1 to 3 texels, the tip a tone down."""
    rng = np.random.default_rng(seed)
    cv = _canvas()
    nb = int(rng.integers(2, 4))
    for b in range(nb):
        L = int(rng.integers(1, 4))
        for j in range(L + 1):
            cv[j, 4 + 2 * b] = C('grass', 2 if j == L else 3)
    return cv, (4 + nb - 1, 0)


def pebble(seed: int, big: bool):
    """softground.pebble: lit at its upper left, its lower right dark."""
    rng = np.random.default_rng(seed)
    cv = _canvas()
    w = int(rng.integers(5, 8)) if big else int(rng.integers(3, 5))
    hh = max(2, int(round(w * rng.uniform(0.55, 0.75))))
    fam = 'stone' if rng.random() < 0.6 else 'stone_warm'
    y0, x0 = DECAL // 2 - hh // 2, DECAL // 2 - w // 2
    for dy in range(hh):
        for dx in range(w):
            if (dy in (0, hh - 1)) and (dx in (0, w - 1)):
                continue
            u, v = dx / max(1, w - 1), dy / max(1, hh - 1)
            tt = 4 if (u + v < 0.55) else (3 if u + v < 1.25 else 2)
            if big and (dy == hh - 1 or dx == w - 1):
                tt = 1
            cv[y0 + dy, x0 + dx] = C(fam, tt)
    return cv, (DECAL // 2, DECAL // 2)


def paint_decals() -> dict:
    """id -> (codes, anchor (x, y)): the decal set the dressing draws from."""
    out = {}
    for i in range(6):
        out['tuft_%d' % i] = tuft(700 + i)
    for i in range(3):
        out['blades_%d' % i] = blades(800 + i)
    for i in range(4):
        out['pebble_%d' % i] = pebble(900 + i, big=i >= 2)
    return out


# ------------------------------------------------------------------------------------------------
# placement
# ------------------------------------------------------------------------------------------------
def dress_hash(a, b, c, m) -> int:
    M = 0xFFFFFFFF
    a, b, c, m = int(a), int(b), int(c), int(m)
    h = ((a * 0x1B873593) & M) ^ ((b * 0xCC9E2D51) & M) ^ ((c * 0x38B34AE5) & M) ^ ((m * 0xA1C9B2F7) & M)
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & M
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & M
    h ^= h >> 16
    return h


def placements(cells: np.ndarray, kit, tiers=None) -> list:
    """Every decal over a zone's cells: (decal id, x, y) of its anchor in texels, in draw order
    (row by row, each cell's south edge then its east edge)."""
    from .compose import profile
    rows, cols = cells.shape
    tiers = np.zeros_like(cells) if tiers is None else tiers
    out = []
    for cy in range(rows):
        for cx in range(cols):
            a = cells[cy, cx]
            for horiz, (ny, nx) in ((True, (cy + 1, cx)), (False, (cy, cx + 1))):
                if ny >= rows or nx >= cols:
                    continue
                b = cells[ny, nx]
                ta, tb = int(tiers[cy, cx]), int(tiers[ny, nx])
                if (a == b and ta == tb) or a == 0 or b == 0:
                    continue
                ea, eb = ta * 256 + kit.prio[a], tb * 256 + kit.prio[b]
                up, lo = (a, b) if ea > eb else (b, a)
                tu = ta if ea > eb else tb
                pair = kit.pair_for(up, lo, ta != tb)
                if pair is None or not kit.dressing.get(pair):
                    continue
                dr = kit.dressing[pair]
                # the cell edge's key, as edges/compose name the crossings
                key = (cx, cy + 1, 1) if horiz else (cx + 1, cy, 0)
                mk = up + 64 * tu
                h = dress_hash(*key, mk)
                if (h % 1000) >= int(dr['density'] * 1000):
                    continue
                t = ((h >> 10) % 17) - 8                     # texels from the edge's middle
                p = profile(*key, mk)
                disp = float(kit.man['curves'][p][t + HALF])   # the manifest's table, as Godot reads it
                if horiz:
                    line = (cy + 1) * CELL
                    upper_south = (b, tb) == (up, tu)
                    side = 'south' if upper_south else 'north'
                    bound = line + disp if upper_south else line - disp
                    x, y = cx * CELL + HALF + t, int(np.floor(bound + 0.5))
                else:
                    line = (cx + 1) * CELL
                    upper_east = (b, tb) == (up, tu)
                    side = 'side'
                    bound = line + disp if upper_east else line - disp
                    x, y = int(np.floor(bound + 0.5)), cy * CELL + HALF + t
                choices = dr[side]
                if not choices:
                    continue
                out.append((choices[(h >> 20) % len(choices)], int(x), int(y)))
    return out


def overlay(codes: np.ndarray, cells: np.ndarray, kit, tiers=None) -> np.ndarray:
    """Draw the dressing over rendered codes (compose.render's output; cells and tiers derived)."""
    H, W = codes.shape
    for did, x, y in placements(cells, kit, tiers):
        dc, (ax, ay) = kit.decals[did]
        y0, x0 = y - ay, x - ax
        for dy in range(dc.shape[0]):
            for dx in range(dc.shape[1]):
                c = dc[dy, dx]
                if c >= 0 and 0 <= y0 + dy < H and 0 <= x0 + dx < W:
                    codes[y0 + dy, x0 + dx] = c
    return codes
