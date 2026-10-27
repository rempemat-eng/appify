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


def derive(cells: np.ndarray, tiers, kit):
    """Faces under raised ground (ground-rules.md 1): below every cell whose south neighbour lies on
    a lower tier, the next `height_cells` x (the drop in tiers) cells of that column become the face
    material, on the lower tier (TerrainGround.derive does the same). Returns (cells, tiers)."""
    cells = cells.copy()
    if tiers is None:
        return cells, np.zeros_like(cells)
    tiers = np.asarray(tiers).copy()
    if kit.face_material is None or not tiers.any():
        return cells, tiers
    rows, cols = cells.shape
    fm, fh = kit.face_material, kit.face_cells
    t0 = tiers.copy()
    for x in range(cols):
        for y in range(rows - 1):
            if t0[y, x] > t0[y + 1, x]:
                for kk in range(1, fh * int(t0[y, x] - t0[y + 1, x]) + 1):
                    if y + kk < rows and t0[y + kk, x] < t0[y, x]:
                        cells[y + kk, x] = fm
    return cells, tiers


def strip_rows(cells: np.ndarray, kit) -> np.ndarray:
    """Per cell, its row in a face strip: the number of face cells straight above it (faces only);
    -1 for a cell with a face just below it, -2 elsewhere (the strip's top and last rows)."""
    rows, cols = cells.shape
    out = np.full((rows, cols), -2, np.int32)
    fm = kit.face_material
    if fm is None:
        return out
    for x in range(cols):
        run = 0
        for y in range(rows):
            if cells[y, x] == fm:
                out[y, x] = run
                run += 1
            else:
                run = 0
                if y + 1 < rows and cells[y + 1, x] == fm:
                    out[y, x] = -1
    return out


def render(cells: np.ndarray, kit, dressing: bool = True, pieces=None, tiers=None) -> np.ndarray:
    """cells: (rows, cols) material ids (0 = nothing, outside the zone); tiers: the same shape, the
    height tier of each cell (faces are derived). Returns codes of (rows * CELL, cols * CELL); -1
    where no material is."""
    cells, tiers = derive(cells, tiers, kit)
    rows, cols = cells.shape
    H, W = rows * CELL, cols * CELL
    out = np.full((H, W), -1, np.int32)
    P = kit.period
    sr = strip_rows(cells, kit)
    yy, xx = np.mgrid[0:CELL, 0:CELL]

    def eprio(L):
        return L[1] * 256 + kit.prio[L[0]]

    def fill(m, Y, X):
        if m in kit.strip:
            r = sr[Y // CELL, X // CELL]
            fy = np.where(r >= 0, r * CELL + Y % CELL, np.where(r == -1, 0, kit.strip[m] - 1))
            return kit.fills[m][np.clip(fy, 0, kit.strip[m] - 1), X % P]
        return kit.fills[m][Y % P, X % P]

    for j in range(rows + 1):
        for i in range(cols + 1):
            cc = [(min(max(j - 1, 0), rows - 1), min(max(i - 1, 0), cols - 1)), (min(max(j - 1, 0), rows - 1), min(i, cols - 1)),
                  (min(j, rows - 1), min(max(i - 1, 0), cols - 1)), (min(j, rows - 1), min(i, cols - 1))]
            q = [(int(cells[c]), int(tiers[c])) for c in cc]
            y0, x0 = j * CELL - HALF, i * CELL - HALF
            ys, xs = slice(max(0, y0), min(H, y0 + CELL)), slice(max(0, x0), min(W, x0 + CELL))
            if ys.start >= ys.stop or xs.start >= xs.stop:
                continue
            ly, lx = ys.start - y0, xs.start - x0
            hh, ww = ys.stop - ys.start, xs.stop - xs.start
            Y = yy[ly:ly + hh, lx:lx + ww] + y0
            X = xx[ly:ly + hh, lx:lx + ww] + x0
            present = sorted({L for L in q if L[0] > 0}, key=eprio)
            if not present:
                continue
            base = present[0]
            code = fill(base[0], Y, X).copy()
            below = base
            for M in present[1:]:
                bits = sum(b for b, L in zip((1, 2, 4, 8), q) if L[0] > 0 and eprio(L) >= eprio(M))
                fu = fill(M[0], Y, X)
                if bits == 15:
                    code = fu.copy()
                else:
                    pair = kit.pair_for(M[0], below[0], M[1] != below[1])
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
                        mk = M[0] + 64 * M[1]
                        t = kit.over[pair][tile_index(i, j, mk, bits, kit.variants)][ly:ly + hh, lx:lx + ww]
                        op, val = t[..., 0], t[..., 1]
                        d = val - 128
                        code = np.where(op == OP_UPPER, step(fu, d), code)
                        code = np.where(op == OP_DELTA, step(code, d), code)
                        code = np.where(op == OP_ABS, val, code)
                below = M
            out[ys, xs] = code
    if pieces:
        sh = shadows(pieces, H, W)
        out = np.where(sh > 0, step(out, -sh), out)
    if dressing:
        from .dressing import overlay
        overlay(out, cells, kit, tiers)
    return out


_INDEX = None


def piece_index() -> dict:
    global _INDEX
    if _INDEX is None:
        import json
        import os
        from .schema import ROOT
        _INDEX = json.load(open(os.path.join(ROOT, 'game', 'kit', 'props', 'index.json')))
    return _INDEX


def shadows(pieces, H: int, W: int) -> np.ndarray:
    """The pieces' cast shadows as ramp steps per texel (TerrainGround.rebuild_shadows): an ellipse
    from the piece's foot, its core (6 texels in from the rim) two tones down, the rim one."""
    idx = piece_index()
    out = np.zeros((H, W), np.int32)
    for pc in pieces:
        e = idx.get(pc['piece'])
        if not e or not e.get('shadow'):
            continue
        cx = pc['at'][0] + e['shadow']['dir'][0]
        cy = pc['at'][1] + e['shadow']['dir'][1]
        rx, ry = e['shadow']['size']
        y0, y1 = max(0, int(np.floor(cy - ry))), min(H, int(np.ceil(cy + ry)) + 1)
        x0, x1 = max(0, int(np.floor(cx - rx))), min(W, int(np.ceil(cx + rx)) + 1)
        if y0 >= y1 or x0 >= x1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
        q = (dx / rx) ** 2 + (dy / ry) ** 2
        v = np.where(q <= 1.0, 1, 0)
        if rx > 6 and ry > 6:
            v = np.where((dx / (rx - 6)) ** 2 + (dy / (ry - 6)) ** 2 <= 1.0, 2, v)
        out[y0:y1, x0:x1] = np.maximum(out[y0:y1, x0:x1], v)
    return out

