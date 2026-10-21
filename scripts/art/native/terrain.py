"""Terrain for a native screen: height, faces, water and paths through the cliff core.

A screen layout (native/screens/<name>.py) gives raised blocks (`MOUNDS`), the brook on a tier
(`BROOK` reaches), the stream at the foot (from `STREAM_X0`, matched to a neighbour's own rows
from `STREAM_MATCH`), and paths as whole grid cells (`PATHS`, plus a ring). This module builds
the cliff-core Plan in the layout's biome, rasterises it at the density, puts the stream and the
paths on it at texel resolution (rounded corners at texel radius, eastward-edges 1.5), renders it
and returns the picture with the masks every later layer needs.

    t = terrain.build(layout, density=2)
    t.image          RGB, texels (W*d x H*d)
    t.kind, t.z      per texel: 1 a top, 2 a face; z of the ground seen there (world px)
    t.tag            the cliff core's tag per texel (ground, rock, water, path, ...)
    t.F, t.T         palette family id and tone per texel (to step shadows along ramps)
    t.water, t.path  texel masks
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
if ART not in sys.path:
    sys.path.insert(0, ART)
import cliff_core as cc  # noqa: E402
import terrace  # noqa: E402


WATER_ROUND = 5.0     # world px: a bend's outer radius (eastward-edges 1.5: 2 to 3)


@dataclass
class Terrain:
    image: object
    F: np.ndarray
    T: np.ndarray
    tag: np.ndarray
    kind: np.ndarray
    z: np.ndarray
    water: np.ndarray
    path: np.ndarray
    walk: np.ndarray
    world: object
    density: float
    falls: list


def rects_mask(rects, shape, s: float, row0: float = 0.0, r_out: int = 0, r_in: int = 0) -> np.ndarray:
    """A union of world-px rectangles (x0, y0, x1, y1) as a texel mask (s texels a world px),
    rows offset by row0 world px; corners rounded at texel radius."""
    m = np.zeros(shape, bool)
    H, W = shape
    for (x0, y0, x1, y1) in rects:
        a, b = int(round((y0 + row0) * s)), int(round((y1 + row0) * s))
        c, d = int(round(x0 * s)), int(round(x1 * s))
        m[max(0, a):max(0, min(H, b)), max(0, c):max(0, min(W, d))] = True
    if r_out or r_in:
        m = terrace.rounded(m, r_out, r_in)
    return m


def stream_rows(L, centre, half):
    """The stream's (top, bottom) world rows per column from STREAM_X0 to the east edge: in
    16 px reaches whose banks move only at a reach's end (a cell line), then the neighbour's
    own rows column by column from STREAM_MATCH, so the seam meets to the pixel."""
    out = {}
    x = L.STREAM_X0
    while x < L.STREAM_MATCH:
        xs = range(x, min(x + 16, L.STREAM_MATCH))
        c = sum(centre(v) for v in xs) / len(xs)
        h = sum(half(v) for v in xs) / len(xs)
        for v in xs:
            out[v] = (int(round(c - h)), int(round(c + h)) + 1)
        x += 16
    for v in range(L.STREAM_MATCH, L.W):
        out[v] = (int(centre(v) - half(v)), int(centre(v) + half(v)) + 1)
    return out


def build(L, density: float = 2.0, centre=None, half=None) -> Terrain:
    s = float(density)
    plan = cc.Plan(L.W, L.H, L.BIOME, seed=L.SEED, top=L.TOP)
    for (z, x0, y0, x1, y1) in L.MOUNDS:
        plan.mound(z, x0, y0, x1, y1)
    plan.snap()
    # the brook on its tier (plan rows y + top + z), to the rim
    for (x0, x1, y0, y1) in L.BROOK:
        r0, r1 = y0 + L.TOP + L.SPUR_Z, y1 + L.TOP + L.SPUR_Z
        sub = plan.Z[max(0, r0):r1, x0:x1] == L.SPUR_Z
        plan.water_m[max(0, r0):r1, x0:x1] |= sub
    w = plan.world(s)
    shape = w.Z.shape
    zt = int(round(L.SPUR_Z * s))
    ground0 = w.Z == 0
    # the lower brook, the spring pool and the stream at z 0, texel exact: reaches on the grid,
    # their corners rounded at WATER_ROUND world px outside and half that inside
    rows = stream_rows(L, centre, half)
    st = np.zeros(shape, bool)
    for x, (a, b) in rows.items():
        st[int((a + L.TOP) * s):int((b + L.TOP) * s), int(x * s):int((x + 1) * s)] = True
    low = rects_mask([(x0, y0, x1, y1) for (x0, x1, y0, y1) in getattr(L, 'LOW_BROOK', [])], shape, s, L.TOP)
    pond = rects_mask([L.POND], shape, s, L.TOP, int(round(8 * s)), 0) if getattr(L, 'POND', None) else np.zeros(shape, bool)
    st_r = terrace.rounded(st | low, int(round(WATER_ROUND * s)), int(round(WATER_ROUND * s / 2))) | pond
    edge_cols = np.zeros(shape, bool)
    edge_cols[:, int(L.STREAM_MATCH * s):] = True
    st = np.where(edge_cols, st, st_r) & ground0
    w.water = w.water | st
    # paths (whole cells, outer corners 8 tx, inner 4 tx at 2x) and the stone circle's ring
    pm = rects_mask(L.PATHS, shape, s, L.TOP, int(round(4 * s)), int(round(2 * s)))
    ring = rects_mask([L.RING], shape, s, L.TOP, int(round(6 * s)), 0) & ~rects_mask([L.RING_IN], shape, s, L.TOP, int(round(4 * s)), 0)
    w.path = (pm | ring) & ground0 & ~w.water
    w._falls = None
    r = cc.render(w)
    img = r.image()
    fr = r.fr
    x0, y0, x1, y1 = r.crop
    K = fr.P['kind'][y0:y1, x0:x1]
    z = np.rint(fr.P['ZH'][y0:y1, x0:x1] / s).astype(np.int32)
    F, T, tag = (a.copy() for a in r.arrays())
    water = tag == cc.TAG['water']
    path = tag == cc.TAG['path']
    walk = cc.walk_mask(r) & (z == 0) & (K == cc.TOP)
    return Terrain(img, F, T, tag, K, z, water, path, walk, w, s, cc.falls(w))


def fall_box(t: Terrain, L):
    """The fall's sheet in texels (x0, y0, x1, y1) on the screen, for the animator."""
    out = []
    for f in t.falls:
        s = t.density
        rim_row = f['py'] - t.world.top - f['h']
        top_row = rim_row + (f['h'] - f['ztop']) + 1
        foot_row = rim_row + (f['h'] - f['h2'])
        out.append((int(f['x0']), int(top_row), int(f['x1']), int(foot_row)))
    return out
