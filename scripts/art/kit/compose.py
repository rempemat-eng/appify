"""The terrain kit's reference renderer: the exact algorithm of game/world/terrain/terrain.gdshader
in numpy, so Python tools (sheets, review:scene, tests) see the same pixels Godot draws.

    codes = compose.render(cells, kit)        # cells: (rows, cols) material ids, 0 = none

For each display tile (centred on a cell corner, offset half a cell from the logical grid):
1. the four cells round the corner give up to four materials, ordered by priority;
2. the lowest is the base: its fill at the texel's world position (mod the period);
3. each higher material M is laid over it with the tile for its mask (the cells whose priority is at
   least M's) from the transition set of the pair (M, the next lower material present), the
   variant chosen by a hash of the tile and M; a texel's operation steps or replaces the code.
"""
from __future__ import annotations

import numpy as np

from scripts.art.native.palette import step

from .edges import CELL, HALF, NPROF, OP_ABS, OP_DELTA, OP_UPPER, crossings, mask_base


def variant(i, j, m, n):
    """The variant of a display tile (i, j) for material m among n: a 32-bit integer hash, the same
    in the shader (uint arithmetic)."""
    i, j, m, M = int(i), int(j), int(m), 0xFFFFFFFF
    h = ((i * 0x8DA6B343) & M) ^ ((j * 0xD8163841) & M) ^ ((m * 0xCB1AB31F) & M)
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & M
    h ^= h >> 12
    return h % n


def profile(a, b, c, m, n=NPROF):
    """The profile of an outline's crossing of a tile border, keyed by the cell edge it lies on
    (a, b, c: column, row, 0 for a vertical cell edge, 1 for a horizontal one) and the material."""
    a, b, c, m, M = int(a), int(b), int(c), int(m), 0xFFFFFFFF
    h = ((a * 0x9E3779B1) & M) ^ ((b * 0x85EBCA77) & M) ^ ((c * 0xC2B2AE3D) & M) ^ ((m * 0x27D4EB2F) & M)
    h ^= h >> 16
    h = (h * 0x7FEB352D) & M
    h ^= h >> 15
    return h % n


def tile_index(i, j, m, bits, variants):
    """The transition tile for display tile (i, j), material m and mask bits (edges.layout)."""
    keys = ((i, j - 1, 0), (i, j, 1), (i, j, 0), (i - 1, j, 1))      # n, e, s, w crossings
    combo = 0
    for side, c in enumerate(crossings(bits)):
        if c:
            combo = combo * NPROF + profile(*keys[side], m)
    return mask_base(variants)[bits] + combo * variants + variant(i, j, m, variants)


def render(cells: np.ndarray, kit, dressing: bool = True) -> np.ndarray:
    """cells: (rows, cols) material ids (0 = nothing, outside the zone). Returns codes of
    (rows * CELL, cols * CELL); -1 where no material is."""
    rows, cols = cells.shape
    H, W = rows * CELL, cols * CELL
    out = np.full((H, W), -1, np.int32)
    P = kit.period
    yy, xx = np.mgrid[0:CELL, 0:CELL]
    for j in range(rows + 1):
        for i in range(cols + 1):
            q = [cells[min(max(j - 1, 0), rows - 1), min(max(i - 1, 0), cols - 1)],
                 cells[min(max(j - 1, 0), rows - 1), min(i, cols - 1)],
                 cells[min(j, rows - 1), min(max(i - 1, 0), cols - 1)],
                 cells[min(j, rows - 1), min(i, cols - 1)]]
            y0, x0 = j * CELL - HALF, i * CELL - HALF
            ys, xs = slice(max(0, y0), min(H, y0 + CELL)), slice(max(0, x0), min(W, x0 + CELL))
            if ys.start >= ys.stop or xs.start >= xs.stop:
                continue
            ly, lx = ys.start - y0, xs.start - x0
            hh, ww = ys.stop - ys.start, xs.stop - xs.start
            wy = (yy[ly:ly + hh, lx:lx + ww] + y0) % P
            wx = (xx[ly:ly + hh, lx:lx + ww] + x0) % P
            present = sorted({m for m in q if m > 0}, key=lambda m: kit.prio[m])
            if not present:
                continue
            base = present[0]
            code = kit.fills[base][wy, wx].copy()
            below = base
            for M in present[1:]:
                bits = sum(b for b, m in zip((1, 2, 4, 8), q) if m > 0 and kit.prio[m] >= kit.prio[M])
                fu = kit.fills[M][wy, wx]
                if bits == 15:
                    code = fu.copy()
                else:
                    pair = kit.pair_for(M, below)
                    if pair is None:
                        # no transition drawn yet: a hard cell edge (shown, never shipped:
                        # the library gate refuses a zone that needs a missing pair)
                        sub = np.zeros((CELL, CELL), bool)
                        for b, (a0, a1) in zip((1, 2, 4, 8), ((0, 0), (0, 1), (1, 0), (1, 1))):
                            if bits & b:
                                sub[a0 * HALF:(a0 + 1) * HALF, a1 * HALF:(a1 + 1) * HALF] = True
                        sub = sub[ly:ly + hh, lx:lx + ww]
                        code = np.where(sub, fu, code)
                    else:
                        t = kit.over[pair][tile_index(i, j, M, bits, kit.variants)][ly:ly + hh, lx:lx + ww]
                        op, val = t[..., 0], t[..., 1]
                        d = val - 128
                        code = np.where(op == OP_UPPER, step(fu, d), code)
                        code = np.where(op == OP_DELTA, step(code, d), code)
                        code = np.where(op == OP_ABS, val, code)
                below = M
            out[ys, xs] = code
    if dressing:
        from .dressing import overlay
        overlay(out, cells, kit)
    return out

