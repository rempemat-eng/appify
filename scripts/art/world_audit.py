"""The whole-world audit: every 32 px cell of the world against the standards, one gate.

Matt, 20 Oct 20:54: "Can you make absolutely sure the whole map adheres to the highest level of
detail, the soft grid etc. specified. not just individual sections but everything." (and 20:04,
on the old summit: "non of this looks natural (given the soft grid), there is no verticality,
hard edges"). So this measures all of it, not samples: every zone's ground and props, every
scenery cell past the world and the garden, stitched into region canvases from the layout
(today), or every 256 px world tile of every chunk once the regions are built on the world
canvas (lib/world-canvas.ts; `--source world`). Both go through one tile iterator.

Per 32 x 32 cell it runs the checks below, rolls them up per 256 px tile, zone (or area),
region and lane, colours every cell by its worst result (green: all measured checks pass;
amber: a soft finding, judged by eye or pending a decision; red: fails the standard), and
writes a heat map of the world, a sheet per region, crops of the worst problems and a JSON
report. docs/vision/world-audit.md explains each check and its source.

  (a) detail     detail_bar.py by kind (ground, paving, water, stream, face; a prop's kind where
                 a prop covers half the cell), through the reference's own JPEG pipe, the
                 cleanliness tests included, under the house rulings (tones at 85 %)
  (b) soft grid  structure on the 8 px grid (verticality.md 4f): boundaries in straight runs
                 (grid-edges), long runs on multiples of 8 (rim-on-grid), face heights 12, 16,
                 32 or 40; with a tier map: no tier step outside a stair or ramp, faces only
                 on south edges, side bands 1 to 2 cells
  (c) hard edges straight boundaries over 96 px without an 8 px jog (benchmark check 8; path
                 edges 240, check 16), ruler-straight pixel edges over 96 px, and seams where a
                 zone, area, scenery cell or world chunk meets the next (world_lint's seam
                 figure plus a cut test; a tile inside a chunk cannot seam, see seams())
  (d) style      the house palette share (amber: the palette is pending Matt), checker dither
                 on walkable ground, and style_lint.py on every placed sprite
  (e) size       size_check.py's ranges for every placed sprite
  (f) ledger     the asset ledger's KEEP / REWORK / RETIRE for every placed asset, or
                 'ungraded' while there is no ledger
  (g) benchmark  per screen: content density (check 1), empty path stretches (check 2),
                 identical runs (check 9) and landmark spacing (check 3), all amber

Run:
  python3 scripts/art/world_audit.py                    # whole world, report + images
  python3 scripts/art/world_audit.py --region valley    # one region (fast iteration)
  python3 scripts/art/world_audit.py --gate             # the self-test, then fail if a region
                                                        # marked "rebuilt" in
                                                        # art/world-audit-regions.json is not
                                                        # 100 % green (npm run check:world-audit)
  python3 scripts/art/world_audit.py --selftest         # the checks on a made-up region with
                                                        # known faults
  options: --source zones|world (default zones, or $WORLD_AUDIT_SOURCE); --out DIR for the
           images (default $WORLD_AUDIT_OUT, else napattack-world-audit in the system temp
           folder, never inside the repository); --json PATH (default art/world-audit.json
           for a whole-world run; '-' skips it); --ledger PATH or git:REF (the asset ledger on
           a branch); --no-images; --cells PATH (every cell's results as JSON)
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

import detail_bar  # noqa: E402
import house_palette as hp  # noqa: E402
import size_check  # noqa: E402

CELL = 32          # the audit cell (px)
TILE = 256         # a world tile
WALK = 4           # a walk/terrain cell
GRID = 8           # the soft grid
ZW, ZH = 320, 576  # a zone, a scenery cell, a screen
PATCH = detail_bar.PATCH
RING = 32          # world source: the ring of the neighbouring chunk read round a chunk's box
CODES = {'-': 0, '.': 1, '=': 2, '~': 3, '!': 4, '^': 5}
NONE, GROUND, PATH, WATER, LAVA, WALL = range(6)
WALKABLE_CODES = (GROUND, PATH)
HEIGHTS = (12, 16, 32, 40)      # the only face heights (terrace.HEIGHTS, verticality.md rule 3)
STRAIGHT_MAX = 96               # benchmark check 8
PATH_STRAIGHT_MAX = 240         # benchmark check 16
TONES_RULING = 0.85             # house-style.md, rulings on the bar: ramp-built art, tones at 85 %
PASS, AMBER, RED, NA = 0, 1, 2, -1

# Which lane owns which generator (docs/vision/coherence-plan.md, "Who does what").
LANE_OF_MODULE = {'valley_zones': 'E', 'frost_zones': 'A', 'zones': 'A', 'ground': 'A', 'scenery': 'A',
                  'isle_zones': 'C', 'city_zones': 'C', 'sunstone_zones': 'D', 'space_zones': 'D',
                  'home_zones': 'B', 'garden': 'B'}

# The checks, their family and the worst they can be.
CHECKS = {
    'detail': ('a detail', 'detail_bar by kind, cleanliness included (house rulings)'),
    'grid-edges': ('b soft grid', 'structure boundaries in straight runs of 16 px or more (80 % a cell)'),
    'rim-on-grid': ('b soft grid', 'straight runs of 24 px or more on multiples of 8 px'),
    'face-height': ('b soft grid', 'faces 12, 16, 32 or 40 px tall'),
    'tier-step': ('b soft grid', 'tiers change only at a stair or ramp (tier map)'),
    'north-face': ('b soft grid', 'faces only on south edges (tier map)'),
    'side-band': ('b soft grid', 'side bands 1 to 2 cells (5 px) wide (tier map)'),
    'straight-run': ('c hard edges', 'no straight boundary over 96 px (paths 240) without an 8 px jog'),
    'ruler-edge': ('c hard edges', 'no pixel-straight contrast edge over 96 px'),
    'seam': ('c hard edges', 'no cut, tone or terrain seam where zones, areas, scenery cells or chunks meet'),
    'palette': ('d style', 'on the house palette (90 %); pending Matt, so amber'),
    'dither': ('d style', 'no checker dither on walkable ground'),
    'sprite-style': ('d style', 'style_lint on every placed sprite'),
    'size': ('e size', 'size_check range for every placed sprite'),
    'ledger': ('f ledger', 'asset ledger KEEP for every placed asset'),
    'density': ('g benchmark', 'interactables and story props per screen (check 1)'),
    'empty-path': ('g benchmark', 'no 200 px of path without something to notice (check 2)'),
    'identical': ('g benchmark', 'no more than 3 identical props in a row (check 9)'),
    'landmark': ('g benchmark', 'a landmark within a screen (check 3)'),
}
CHECK_IDS = list(CHECKS)


# --------------------------------------------------------------------------------------------
# reading generated TypeScript data

def ts_data(root: str, rel: str, names: list) -> dict:
    """Named exports of a generated data module, read with node + tsx."""
    path = os.path.join(root, rel)
    code = ("const m = await import('file://' + process.argv[1]); const out = {};"
            "for (const n of JSON.parse(process.argv[2])) if (n in m) out[n] = m[n];"
            "process.stdout.write(JSON.stringify(out));")
    node = os.environ.get('NODE', 'node')
    r = subprocess.run([node, '--import', 'tsx', '--input-type=module', '-e', code, path, json.dumps(names)],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'world_audit: could not read {rel}: {r.stderr[-800:]}')
    return json.loads(r.stdout)


def unrle(row: str, alphabet: str) -> str:
    return re.sub(r'(\d+)([' + re.escape(alphabet) + r'])', lambda m: m.group(2) * int(m.group(1)), row)


def unrle_tiers(s: str, n: int) -> str | None:
    """Tier rows (digits for tiers, 'f' a face, 'b' a side band, 's' a stair or ramp). Their run-length code puts
    a count before each run, so a run of tier digits is ambiguous ('121'); decode greedily and
    give up (None) unless the result has exactly n cells."""
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j].isdigit():
            j += 1
        if j == i or j >= len(s) + 1:
            return None
        if j == len(s):
            return None
        if s[j].isdigit():
            return None
        out.append(s[j] * int(s[i:j]))
        i = j + 1
    flat = ''.join(out)
    return flat if len(flat) == n else None


# --------------------------------------------------------------------------------------------
# colour helpers (vectorised OKLab)

def oklab(rgb: np.ndarray) -> np.ndarray:
    c = rgb[..., :3].astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    lm = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    mm = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    sm = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    lm, mm, sm = np.cbrt(lm), np.cbrt(mm), np.cbrt(sm)
    return np.stack([0.2104542553 * lm + 0.7936177850 * mm - 0.0040720468 * sm,
                     1.9779984951 * lm - 2.4285922050 * mm + 0.4505937099 * sm,
                     0.0259040371 * lm + 0.7827717662 * mm - 0.8086757660 * sm], -1)


def rgb_key(rgb: np.ndarray) -> np.ndarray:
    a = rgb[..., :3].astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


class Palette:
    """Which colours are on the house palette (within style_lint's NEAR) and on today's ramps."""

    NEAR = 0.02

    def __init__(self, root: str):
        pal = hp.load()
        house = np.array(list(hp.colours(pal)), dtype=np.uint8).reshape(-1, 3)
        self.house_lab = oklab(house)
        with open(os.path.join(root, 'art', 'materials.json')) as f:
            mats = json.load(f)
        today = [hp.hex_rgb(c) for r in mats['materials'].values() for c in r] + [hp.hex_rgb(mats['outline'])]
        self.today = set(int(k) for k in rgb_key(np.array(today, dtype=np.uint8)))
        self.snow = np.array([hp.hex_rgb(c) for c in mats['materials']['snow']], dtype=np.uint8)
        self._cache: dict = {}

    def on_house(self, keys: np.ndarray) -> np.ndarray:
        """bool per colour key."""
        u, inv = np.unique(keys, return_inverse=True)
        want = [k for k in u.tolist() if k not in self._cache]
        if want:
            arr = np.array(want, dtype=np.int64)
            rgb = np.stack([(arr >> 16) & 255, (arr >> 8) & 255, arr & 255], -1).astype(np.uint8)
            lab = oklab(rgb)
            for i in range(0, len(arr), 2048):
                d = ((lab[i:i + 2048, None, :] - self.house_lab[None]) ** 2).sum(-1).min(1)
                for k, v in zip(arr[i:i + 2048].tolist(), (d <= self.NEAR ** 2).tolist()):
                    self._cache[k] = v
        res = np.array([self._cache[k] for k in u.tolist()], dtype=bool)
        return res[inv].reshape(keys.shape)


# --------------------------------------------------------------------------------------------
# the detail bar, vectorised over a whole place (same counts as detail_bar.counts)

def pipe_keys(rgb: np.ndarray, adult: float, quality: int | None) -> np.ndarray:
    """detail_bar's pipe for a whole image: blown up to the reference's adult height (nearest),
    saved at its JPEG quality, brought back down to our scale by the most common quantised
    colour of each block. Returns colour keys of the same size as `rgb`."""
    h, w = rgb.shape[:2]
    f = adult / detail_bar.ADULT
    big = Image.fromarray(np.ascontiguousarray(rgb[..., :3])).resize(
        (max(1, round(w * f)), max(1, round(h * f))), Image.NEAREST)
    if quality:
        b = io.BytesIO()
        big.save(b, 'JPEG', quality=quality)
        b.seek(0)
        big = Image.open(b).convert('RGB')
    key = detail_bar.quantised(big)
    H, W = key.shape
    y0 = np.minimum((np.arange(h) * f).astype(np.int64), H - 1)
    y1 = np.minimum(np.maximum(y0 + 1, (np.arange(1, h + 1) * f).astype(np.int64)), H)
    x0 = np.minimum((np.arange(w) * f).astype(np.int64), W - 1)
    x1 = np.minimum(np.maximum(x0 + 1, (np.arange(1, w + 1) * f).astype(np.int64)), W)
    ky, kx = int((y1 - y0).max()), int((x1 - x0).max())
    out = np.empty((h, w), np.int32)
    step = max(1, 400000 // (w * ky * kx))
    for r0 in range(0, h, step):
        r1 = min(h, r0 + step)
        n = (r1 - r0) * w
        stack = np.empty((ky * kx, n), np.int64)
        i = 0
        for dy in range(ky):
            rows = y0[r0:r1] + dy
            vy = rows < y1[r0:r1]
            rows = np.minimum(rows, H - 1)
            for dx in range(kx):
                cols = x0 + dx
                vx = cols < x1
                cols = np.minimum(cols, W - 1)
                v = key[rows[:, None], cols[None, :]].astype(np.int64)
                ok = vy[:, None] & vx[None, :]
                v = np.where(ok, v, (1 << 20) + i)   # invalid: unique, above every key
                stack[i] = v.ravel()
                i += 1
        s = np.sort(stack, axis=0)
        start = np.ones_like(s, dtype=bool)
        start[1:] = s[1:] != s[:-1]
        rid = np.cumsum(start, axis=0)                     # 1..K per column
        col = np.broadcast_to(np.arange(n), s.shape)
        cnt = np.bincount((col * (ky * kx + 1) + rid).ravel(), minlength=n * (ky * kx + 1))
        cnt = cnt.reshape(n, ky * kx + 1)
        at = cnt[col, rid]                                 # each position's run length
        best = at.argmax(axis=0)                           # first max: the smallest key
        out[r0:r1] = s[best, np.arange(n)].reshape(r1 - r0, w)
    return out


def label_patches(key: np.ndarray, patch: int = PATCH) -> np.ndarray:
    """4-connected one-colour regions, never across a patch border: a label per pixel (the
    smallest flat index in its region)."""
    h, w = key.shape
    lab = np.arange(h * w, dtype=np.int64).reshape(h, w)
    ys, xs = np.arange(h), np.arange(w)
    right = (key[:, 1:] == key[:, :-1]) & ((xs[1:] % patch) != 0)[None, :]
    down = (key[1:, :] == key[:-1, :]) & ((ys[1:] % patch) != 0)[:, None]
    while True:
        new = lab.copy()
        m = np.minimum(new[:, 1:], new[:, :-1])
        new[:, 1:] = np.where(right, m, new[:, 1:])
        new[:, :-1] = np.where(right, np.minimum(new[:, :-1], new[:, 1:]), new[:, :-1])
        m = np.minimum(new[1:, :], new[:-1, :])
        new[1:, :] = np.where(down, m, new[1:, :])
        new[:-1, :] = np.where(down, np.minimum(new[:-1, :], new[1:, :]), new[:-1, :])
        flat = new.ravel()
        for _ in range(4):
            flat = flat[flat]
        new = flat.reshape(h, w)
        if np.array_equal(new, lab):
            return lab
        lab = new


def patch_counts(key: np.ndarray) -> dict:
    """Per 16 x 16 patch (whole patches only, from the top-left): tones, shapes, dressing,
    isolated and cluster, exactly as detail_bar.counts measures one patch."""
    h, w = key.shape
    ph, pw = h // PATCH, w // PATCH
    key = key[:ph * PATCH, :pw * PATCH]
    h, w = key.shape
    pad = np.pad(key, 1, mode='edge')
    c = pad[1:-1, 1:-1]
    lone = (c != pad[:-2, 1:-1]) & (c != pad[2:, 1:-1]) & (c != pad[1:-1, :-2]) & (c != pad[1:-1, 2:])
    blocks = key.reshape(ph, PATCH, pw, PATCH).transpose(0, 2, 1, 3).reshape(ph * pw, PATCH * PATCH)
    s = np.sort(blocks, axis=1)
    start = np.ones_like(s, dtype=bool)
    start[:, 1:] = s[:, 1:] != s[:, :-1]
    rid = np.cumsum(start, axis=1)
    n = ph * pw
    rowi = np.broadcast_to(np.arange(n)[:, None], s.shape)
    cnt = np.bincount((rowi * (PATCH * PATCH + 1) + rid).ravel(), minlength=n * (PATCH * PATCH + 1))
    cnt = cnt.reshape(n, PATCH * PATCH + 1)
    tones = (cnt >= 2).sum(1)
    at = cnt[rowi, rid]
    main = s[np.arange(n), at.argmax(1)]
    lab = label_patches(key)
    flat = lab.ravel()
    sizes = np.bincount(flat, minlength=h * w)
    roots = np.flatnonzero(sizes)
    ry, rx = roots // w, roots % w
    rp = (ry // PATCH) * pw + (rx // PATCH)
    rsize = sizes[roots]
    rkey = key.ravel()[roots]
    nreg = np.bincount(rp, minlength=n)
    shapes = np.bincount(rp, weights=(rsize >= 2), minlength=n)
    dressing = np.bincount(rp, weights=((rsize >= 2) & (rsize <= 12) & (rkey != main[rp])), minlength=n)
    iso = lone.reshape(ph, PATCH, pw, PATCH).transpose(0, 2, 1, 3).reshape(n, -1).mean(1)
    cluster = PATCH * PATCH / np.maximum(nreg, 1)
    shp = (ph, pw)
    return {'tones': tones.reshape(shp).astype(float), 'shapes': shapes.reshape(shp),
            'dressing': dressing.reshape(shp), 'isolated': iso.reshape(shp), 'cluster': cluster.reshape(shp)}


def judge_cell(ours: dict, ref: dict) -> tuple[bool, str]:
    bad = []
    for m, share in (('tones', TONES_RULING), ('shapes', detail_bar.TOLERANCE), ('dressing', detail_bar.TOLERANCE)):
        if ours[m] < share * ref[m]:
            bad.append(f'{m} {ours[m]:.1f}/{ref[m]:.1f} LOW')
    if ours['isolated'] > ref['isolated'] + detail_bar.ISOLATED_MARGIN:
        bad.append(f'isolated {ours["isolated"]:.3f}/{ref["isolated"]:.3f} NOISY')
    if ours['cluster'] < detail_bar.CLUSTER_SHARE * ref['cluster']:
        bad.append(f'cluster {ours["cluster"]:.1f}/{ref["cluster"]:.1f} NOISY')
    return (not bad), '; '.join(bad)


# --------------------------------------------------------------------------------------------
# the world as regions: places on a canvas, from today's zones or from world tiles

class Place:
    """A part of a region's canvas: a zone (or an area), the garden, or a scenery cell."""

    def __init__(self, id: str, kind: str, region: str, module: str, rect: tuple, grid: tuple | None = None,
                 painted: bool = False):
        self.id, self.kind, self.region, self.module = id, kind, region, module
        # an area of a chunk painted whole (a lane's painter, not today's zones): its edges with
        # the chunk's other areas are lines drawn for counting, not joins, so they cannot seam
        self.painted = painted
        self.lane = LANE_OF_MODULE.get(module, '?')
        self.rect = rect            # (x, y, w, h) in canvas px
        self.grid = grid            # (col, row) on the region's zone grid, when it has one

    @property
    def screen(self) -> bool:
        return self.kind in ('zone', 'garden', 'area')


class Region:
    def __init__(self, id: str, plane: str, w: int, h: int, origin: tuple):
        self.id, self.plane, self.w, self.h = id, plane, w, h
        self.origin = origin        # region (or world) px of canvas (0, 0)
        self.ground = np.zeros((h, w, 4), np.uint8)
        self.terrain = np.zeros((h // WALK, w // WALK), np.uint8)
        self.walk = np.zeros((h // WALK, w // WALK), bool)
        self.tiers = np.full((h // WALK, w // WALK), 255, np.uint8)   # 255: no tier map
        self.tier_note: list = []
        self.props: list = []       # dicts: id, sprite, x, y, w, h (canvas px), img, png, place, overhead
        self.places: list = []
        self.stands: list = []      # (x, y) canvas px: residents, stands
        self.pieces: list = []      # (file, (x, y, w, h)): the ground pictures the canvas is made of
        self.residents: dict = {}   # place id -> count

    def add_place(self, p: Place):
        self.places.append(p)


def zone_modules(root: str) -> dict:
    """zone id -> the generator module that draws it (zones.py main(): build('id', fn, ...))."""
    src = open(os.path.join(root, 'scripts', 'art', 'zones.py')).read()
    calls = dict(re.findall(r"build\('(\w+)',\s*(\w+),", src))
    defs = {}
    for f in sorted(os.listdir(os.path.join(root, 'scripts', 'art'))):
        if f.endswith('_zones.py') or f == 'zones.py':
            for fn in re.findall(r'^def (\w+)\(', open(os.path.join(root, 'scripts', 'art', f)).read(), re.M):
                defs.setdefault(fn, f[:-3])
    return {z: defs.get(fn, 'zones') for z, fn in calls.items()}


def _png_1x(path: str, w: int | None = None) -> np.ndarray:
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)
    if w:
        s = max(1, round(im.width / w))
        a = a[::s, ::s]
    return a


def _paste_rgba(dst: np.ndarray, src: np.ndarray, x: int, y: int, owner: np.ndarray | None = None, idx: int = -1):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    a = s[..., 3:4] / 255.0
    out = s[..., :3] * a + d[..., :3] * (1 - a)
    da = d[..., 3:4] / 255.0
    oa = a + da * (1 - a)
    dst[y0:y1, x0:x1, :3] = np.clip(np.round(out), 0, 255).astype(np.uint8)
    dst[y0:y1, x0:x1, 3:4] = np.clip(np.round(oa * 255), 0, 255).astype(np.uint8)
    if owner is not None:
        owner[y0:y1, x0:x1][src[y0 - y:y1 - y, x0 - x:x1 - x, 3] >= 128] = idx


def _rows(rows: list, alphabet: str) -> np.ndarray:
    return np.array([list(unrle(r, alphabet)) for r in rows])


def load_zones(root: str, only: set | None = None) -> list:
    """Today's world: each region's zones, the garden and the scenery cells past the world,
    stitched on one canvas per region from the layout (lib/zone-maps.ts regionLayout)."""
    d = ts_data(root, 'lib/zone-maps.ts', ['regionLayout', 'zoneMaps', 'zoneTerrain', 'zoneOverhead', 'zoneTier'])
    g = ts_data(root, 'lib/garden-map.ts', ['gardenObjects', 'gardenWater'])
    res = ts_data(root, 'lib/resident-routes.ts', ['residentRoutes']).get('residentRoutes', {})
    modules = zone_modules(root)
    overhead = set(d.get('zoneOverhead', []))
    scen_dir = os.path.join(root, 'assets', 'zones', 'scenery')
    scen = {}
    for f in sorted(os.listdir(scen_dir)) if os.path.isdir(scen_dir) else []:
        m = re.match(r'(\w+?)_(m?\d+)_(m?\d+)\.png$', f)
        if m:
            num = lambda s: -int(s[1:]) if s.startswith('m') else int(s)  # noqa: E731
            scen.setdefault(m.group(1), {})[(num(m.group(2)), num(m.group(3)))] = os.path.join(scen_dir, f)
    regions = []
    for rid, layout in d['regionLayout'].items():
        if only and rid not in only:
            continue
        cells = {tuple(v): z for z, v in layout.items()}
        sc = scen.get(rid, {})
        allc = set(cells) | set(sc)
        c0, r0 = min(c for c, _ in allc), min(r for _, r in allc)
        c1, r1 = max(c for c, _ in allc), max(r for _, r in allc)
        zc0, zr0 = min(c for c, _ in cells), min(r for _, r in cells)
        R = Region(rid, {'space': 'orbit', 'moon': 'moon', 'home': 'hut'}.get(rid, 'continent'),
                   (c1 - c0 + 1) * ZW, (r1 - r0 + 1) * ZH, ((c0 - zc0) * ZW, (r0 - zr0) * ZH))
        for (c, r), z in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            ox, oy = (c - c0) * ZW, (r - r0) * ZH
            if z == 'garden':
                R.add_place(Place('garden', 'garden', rid, 'garden', (ox, oy, ZW, ZH), (c, r)))
                _load_garden(root, R, ox, oy, g, len(R.places) - 1)
                continue
            R.add_place(Place(z, 'zone', rid, modules.get(z, 'zones'), (ox, oy, ZW, ZH), (c, r)))
            pi = len(R.places) - 1
            gp = os.path.join(root, 'assets', 'zones', z, 'ground.png')
            R.ground[oy:oy + ZH, ox:ox + ZW] = _png_1x(gp, ZW)[:ZH, :ZW]
            R.pieces.append((gp, (ox, oy, ZW, ZH)))
            zm = d['zoneMaps'][z]
            ty, tx = oy // WALK, ox // WALK
            R.terrain[ty:ty + ZH // WALK, tx:tx + ZW // WALK] = np.vectorize(CODES.get)(_rows(d['zoneTerrain'][z], '~!^=.'))
            R.walk[ty:ty + ZH // WALK, tx:tx + ZW // WALK] = _rows(zm['walk'], '.#') == '.'
            tiers = (d.get('zoneTier') or {}).get(z)
            if tiers:
                flat = unrle_tiers(''.join(tiers) if isinstance(tiers, list) else tiers, (ZW // WALK) * (ZH // WALK))
                if flat is None:
                    R.tier_note.append(f'{z}: tier map present but its run-length code is ambiguous')
                else:
                    R.tiers[ty:ty + ZH // WALK, tx:tx + ZW // WALK] = np.frombuffer(flat.encode(), np.uint8).reshape(ZH // WALK, ZW // WALK)
            for (oid, key, x, y, w, h) in zm['objects']:
                png = os.path.join(root, 'assets', 'zones', 'props', f'{key}.png')
                if not os.path.exists(png):
                    continue
                R.props.append({'id': f'{z}:{oid}', 'sprite': key, 'x': ox + x, 'y': oy + y, 'w': w, 'h': h,
                                'png': png, 'place': pi, 'overhead': key in overhead, 'source': 'zones'})
            for sid, (sx, sy) in zm.get('stands', {}).items():
                R.stands.append((ox + sx, oy + sy))
        for name, rt in res.items():
            for p in R.places:
                if p.id == rt.get('zone'):
                    R.residents[p.id] = R.residents.get(p.id, 0) + 1
                    x, y, _w, _h = p.rect
                    R.stands += [(x + rt['from'][0], y + rt['from'][1]), (x + rt['to'][0], y + rt['to'][1])]
        for (c, r), path in sorted(sc.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            ox, oy = (c - c0) * ZW, (r - r0) * ZH
            im = Image.open(path).convert('RGBA')
            s = max(1, round(im.width / (ZW + 2 * 20)))
            a = np.asarray(im)[::s, ::s]
            sp = (a.shape[1] - ZW) // 2
            R.ground[oy:oy + ZH, ox:ox + ZW] = a[sp:sp + ZH, sp:sp + ZW]
            R.pieces.append((path, (ox, oy, ZW, ZH)))
            R.terrain[oy // WALK:(oy + ZH) // WALK, ox // WALK:(ox + ZW) // WALK] = colour_terrain(a[sp:sp + ZH, sp:sp + ZW])
            R.add_place(Place(f'{rid}:{c},{r}', 'scenery', rid, 'scenery', (ox, oy, ZW, ZH), (c, r)))
        regions.append(R)
    return regions


def colour_terrain(a: np.ndarray) -> np.ndarray:
    """Terrain for ground with no terrain map (the scenery past the world), read from colour
    by world_lint's rules: water (bluish), lava, else ground. Trees, rocks and snow are
    free-form (verticality.md 4f), so only coasts, banks and lava edges count as structure."""
    r, g, b = (a[..., i].astype(int) for i in range(3))
    water = (b >= r + 18) & (b >= g - 6) & (r < 150)
    lava = (r >= 170) & (g <= 160) & (b <= 90) & (r - g >= 50)
    h, w = water.shape
    q = lambda m: m.reshape(h // WALK, WALK, w // WALK, WALK).sum((1, 3))  # noqa: E731
    nw, nl = q(water), q(lava)
    out = np.full((h // WALK, w // WALK), GROUND, np.uint8)
    out[nw >= 8] = WATER
    out[(nl >= 8) & (nl > nw)] = LAVA
    out[q(a[..., 3] > 0) < 8] = NONE
    return out


def _load_garden(root: str, R: Region, ox: int, oy: int, g: dict, pi: int):
    gdir = os.path.join(root, 'assets', 'garden')
    a = _png_1x(os.path.join(gdir, 'ground.png'), ZW)[:ZH, :ZW].copy()
    for wv in g.get('gardenWater', []):
        p = os.path.join(gdir, f"water-{wv['id']}-0.png")
        if os.path.exists(p):
            _paste_rgba(a, _png_1x(p, wv['w']), wv['x'], wv['y'])
    R.ground[oy:oy + ZH, ox:ox + ZW] = a
    R.pieces.append((os.path.join(gdir, 'ground.png'), (ox, oy, ZW, ZH)))
    import world_lint
    img = Image.fromarray(a)
    blocked = {(x, y) for y in range(ZH) for x in range(ZW) if world_lint._bluish(*a[y, x, :3].tolist())}
    rows = world_lint.classify(img, blocked)
    t = np.array([[CODES[ch] for ch in r] for r in rows], np.uint8)
    ty, tx = oy // WALK, ox // WALK
    R.terrain[ty:ty + ZH // WALK, tx:tx + ZW // WALK] = t
    R.walk[ty:ty + ZH // WALK, tx:tx + ZW // WALK] = np.isin(t, WALKABLE_CODES)
    for o in g.get('gardenObjects', []):
        png = os.path.join(gdir, f"{o['sprite']}.png")
        if not os.path.exists(png):
            continue
        R.props.append({'id': f"garden:{o['id']}", 'sprite': o['sprite'], 'x': ox + o['x'], 'y': oy + o['y'],
                        'w': o['w'], 'h': o['h'], 'png': png, 'place': pi, 'overhead': False, 'source': 'garden',
                        'action': o.get('action')})


def load_world(root: str, only: set | None = None) -> list:
    """The world canvas (lib/world-canvas.ts, docs/vision/region-canvas.md): each chunk's box
    assembled from the 256 px world tiles that cover it; its areas are the places."""
    d = ts_data(root, 'lib/world-canvas.ts', ['WORLD_TILE', 'worldChunks', 'worldAreas', 'worldTiles'])
    if not d.get('worldTiles'):
        raise RuntimeError('world_audit: lib/world-canvas.ts has no world tiles')
    res = ts_data(root, 'lib/resident-routes.ts', ['residentRoutes']).get('residentRoutes', {})
    arts = {}
    ap = os.path.join(root, 'lib', 'world-canvas-assets.ts')
    if os.path.exists(ap):
        src = open(ap).read()
        imports = dict(re.findall(r"import (\w+) from '@/assets/(world/[^']+\.png)'", src))
        for key, ident in re.findall(r"'([^']+)': (\w+),", src):
            if ident in imports:
                arts.setdefault(key, os.path.join(root, 'assets', imports[ident]))
    modules = zone_modules(root) if os.path.exists(os.path.join(root, 'scripts', 'art', 'zones.py')) else {}
    tsz = d['WORLD_TILE']['size']
    tc = tsz // WALK
    regions = []
    for ch in d['worldChunks']:
        if only and ch['id'] not in only:
            continue
        # the chunk's box and a ring of RING px round it, so its edges can be checked against the
        # chunk next to it (the ring itself is not counted: it belongs to no area of this chunk)
        (bx, by), (bw, bh) = ch['origin'], ch['size']
        ox, oy, w, h = bx - RING, by - RING, bw + 2 * RING, bh + 2 * RING
        R = Region(ch['id'], ch['plane'], w, h, (ox, oy))
        tiles = d['worldTiles'].get(ch['plane'], {})
        for c in range(math.floor(ox / tsz), math.floor((ox + w - 1) / tsz) + 1):
            for r in range(math.floor(oy / tsz), math.floor((oy + h - 1) / tsz) + 1):
                t = tiles.get(f'{c},{r}')
                if not t:
                    continue
                X, Y = c * tsz - ox, r * tsz - oy        # the tile's top-left on the chunk canvas
                x0, y0, x1, y1 = max(0, X), max(0, Y), min(w, X + tsz), min(h, Y + tsz)
                if t.get('fill'):
                    col = hp.hex_rgb(t['fill'][:7]) + (int(t['fill'][7:9] or 'ff', 16),)
                    tile = np.zeros((tsz, tsz, 4), np.uint8)
                    tile[:] = col
                elif t.get('art') and t['art'] in arts:
                    tile = _png_1x(arts[t['art']], tsz)
                    R.pieces.append((arts[t['art']], (x0, y0, x1 - x0, y1 - y0)))
                else:
                    tile = np.zeros((tsz, tsz, 4), np.uint8)
                R.ground[y0:y1, x0:x1] = tile[y0 - Y:y1 - Y, x0 - X:x1 - X]
                cells = lambda s, alph: np.array(list(unrle(s, alph))).reshape(tc, tc)  # noqa: E731
                ter = np.vectorize(lambda ch_: CODES.get(ch_, 0))(cells(t['terrain'], '~!^=.-'))
                wk = cells(t['walk'], '.#') == '.'
                sl = (slice(y0 // WALK, y1 // WALK), slice(x0 // WALK, x1 // WALK))
                ss = (slice((y0 - Y) // WALK, (y1 - Y) // WALK), slice((x0 - X) // WALK, (x1 - X) // WALK))
                R.terrain[sl] = ter[ss]
                R.walk[sl] = wk[ss]
                if t.get('tiers'):
                    flat = unrle_tiers(t['tiers'], tc * tc)
                    if flat is None:
                        R.tier_note.append(f'tile {c},{r}: tier map present but its run-length code is ambiguous')
                    else:
                        R.tiers[sl] = np.frombuffer(flat.encode(), np.uint8).reshape(tc, tc)[ss]
                for (oid, key, x, y, ow, oh) in t.get('objects', []):
                    png = os.path.join(root, 'assets', 'zones', 'props', f'{key}.png')
                    fx, fy = x + ow // 2, y + oh - 2
                    if os.path.exists(png) and bx <= fx < bx + bw and by <= fy < by + bh:
                        R.props.append({'id': oid, 'sprite': key, 'x': x - ox, 'y': y - oy, 'w': ow, 'h': oh,
                                        'png': png, 'place': -1, 'overhead': False, 'source': 'world'})
                for sid, (sx, sy) in t.get('stands', {}).items():
                    if bx <= sx < bx + bw and by <= sy < by + bh:
                        R.stands.append((sx - ox, sy - oy))
        for a in d['worldAreas']:
            if a['chunk'] != ch['id']:
                continue
            x, y, aw, ah = a['rect']
            mod = 'garden' if a['kind'] == 'garden' else modules.get(a['id'], 'zones')
            R.add_place(Place(a['id'], 'garden' if a['kind'] == 'garden' else 'area', ch['id'], mod,
                              (x - ox, y - oy, aw, ah), painted=a['kind'] != 'garden' and a['id'] not in modules))
        for p in R.props:
            fx, fy = p['x'] + p['w'] // 2, p['y'] + p['h'] - 2
            for i, pl in enumerate(R.places):
                x, y, aw, ah = pl.rect
                if x <= fx < x + aw and y <= fy < y + ah:
                    p['place'] = i
                    break
        for name, rt in res.items():
            for p in R.places:
                if p.id == rt.get('zone'):
                    R.residents[p.id] = R.residents.get(p.id, 0) + 1
                    x, y, _w, _h = p.rect
                    R.stands += [(x + rt['from'][0], y + rt['from'][1]), (x + rt['to'][0], y + rt['to'][1])]
        regions.append(R)
    return regions


def tiles_of(R: Region):
    """The 256 px world tiles over a region's canvas: (col, row, x0, y0, x1, y1) in canvas px.
    Region (or world) px = canvas px + origin; tiles sit on multiples of 256 of those."""
    ox, oy = R.origin
    for row in range(math.floor(oy / TILE), math.floor((oy + R.h - 1) / TILE) + 1):
        for col in range(math.floor(ox / TILE), math.floor((ox + R.w - 1) / TILE) + 1):
            x0, y0 = max(0, col * TILE - ox), max(0, row * TILE - oy)
            x1, y1 = min(R.w, (col + 1) * TILE - ox), min(R.h, (row + 1) * TILE - oy)
            yield col, row, x0, y0, x1, y1


# --------------------------------------------------------------------------------------------
# the audit of one region

# a placed sprite's surface, by its size-guide kind (size_guide.json), for the detail bar
DETAIL_KIND = {}
for _k in ('broadleaf', 'young_tree', 'veteran_tree', 'birch', 'willow', 'conifer', 'palm', 'small_palm', 'acacia',
           'snag'):
    DETAIL_KIND[_k] = 'tree'
for _k in ('bush',):
    DETAIL_KIND[_k] = 'hedge'
for _k in ('keep', 'gatehouse', 'castle_tower', 'postern', 'curtain_wall', 'crag', 'boulder', 'standing_stone', 'well'):
    DETAIL_KIND[_k] = 'stone-wall'
for _k in ('false_front', 'barn', 'shed', 'boathouse', 'hut', 'signal_box'):
    DETAIL_KIND[_k] = 'wood-front'
for _k in ('module', 'lander', 'shuttle', 'lunar_habitat', 'crane', 'gantry_crane', 'mast', 'water_tower', 'windpump',
           'industrial', 'car', 'van', 'truck', 'tram', 'locomotive', 'railcar', 'tub', 'launch', 'narrowboat', 'ferry',
           'container_stack', 'dome', 'kiosk', 'vending', 'grow_pod', 'appliance'):
    DETAIL_KIND[_k] = 'machinery'
for _k in ('cottage', 'house', 'farmhouse', 'civic', 'shop', 'town_house', 'workshop', 'warehouse', 'station_building',
           'city_building', 'adobe', 'landmark_tower', 'tower', 'windmill', 'water_mill', 'smithy', 'pavilion', 'shelter'):
    DETAIL_KIND[_k] = 'facade'
CITY_REGIONS = {'neon', 'steam', 'space', 'home'}
# Built places: streets, quays and walls are straight by construction (Eastward's kerbs and
# street walls are), so there the straight-run check holds only main paths to 240 px (check
# 16) and the ruled-edge check is off; their hard edges are judged by the bar and by eye.
BUILT_REGIONS = {'neon', 'steam'}
# Interiors (the station's deck, the hut's room) are rooms, not landscape: no straight-run,
# ruled-edge, inferred face or benchmark checks there.
INTERIOR_REGIONS = {'space', 'home'}
NO_BASELINE = ('lava', 'snow', 'cloth', 'other')
INTERACT = {'bench', 'bench_side', 'sign', 'tall_sign', 'stall', 'food_stall', 'cart_stall', 'cafe_set', 'well',
            'fountain', 'telescope', 'kiosk', 'vending', 'shrine'}
LANDMARK = {'landmark_tower', 'tower', 'windmill', 'water_mill', 'keep', 'gatehouse', 'mast', 'gantry_crane', 'dome',
            'civic', 'industrial', 'shuttle', 'lunar_habitat', 'veteran_tree', 'crag', 'warehouse'}
STYLE_AMBER = {'palette', 'colours', 'outline-flat-ink'}   # wait on Matt's palette decision


class Audit:
    def __init__(self, R: Region, ctx: dict):
        self.R, self.ctx = R, ctx
        self.ny, self.nx = R.h // CELL, R.w // CELL
        self.status = {c: np.full((self.ny, self.nx), NA, np.int8) for c in CHECK_IDS}
        self.why: dict = {}             # (check, cy, cx) -> short reason
        self.metrics: dict = {}
        self.findings: list = []        # sprite-level and screen-level findings

    # -- helpers ---------------------------------------------------------------------------
    def mark(self, check: str, cy: int, cx: int, sev: int, why: str = ''):
        if not (0 <= cy < self.ny and 0 <= cx < self.nx):
            return
        if sev > self.status[check][cy, cx]:
            self.status[check][cy, cx] = sev
            if why:
                self.why[(check, cy, cx)] = why
        elif sev == self.status[check][cy, cx] and why and (check, cy, cx) not in self.why:
            self.why[(check, cy, cx)] = why

    def pass_where(self, check: str, mask: np.ndarray):
        s = self.status[check]
        s[(s == NA) & mask] = PASS

    def cells_of_box(self, x: int, y: int, w: int, h: int):
        for cy in range(max(0, y // CELL), min(self.ny, (y + h - 1) // CELL + 1)):
            for cx in range(max(0, x // CELL), min(self.nx, (x + w - 1) // CELL + 1)):
                yield cy, cx

    # -- composing -------------------------------------------------------------------------
    def compose(self):
        R = self.R
        self.comp = R.ground.copy()
        self.owner = np.full((R.h, R.w), -1, np.int32)
        order = sorted(range(len(R.props)), key=lambda i: (R.props[i]['overhead'], R.props[i]['y'] + R.props[i]['h'],
                                                             R.props[i]['x'], R.props[i]['id']))
        for i in order:
            p = R.props[i]
            p['img'] = self.ctx['sprites'].get(p['png'])
            if p['img'] is None:
                p['img'] = self.ctx['sprites'][p['png']] = _png_1x(p['png'], p['w'])
            _paste_rgba(self.comp, p['img'], p['x'], p['y'], None if p['overhead'] else self.owner, i)
        a = R.ground[..., 3] > 0
        self.art = a.reshape(self.ny, CELL, self.nx, CELL).mean((1, 3)) >= 0.5
        pm = np.full((self.ny, self.nx), -1, np.int32)
        for i, pl in enumerate(R.places):
            x, y, w, h = pl.rect
            pm[y // CELL:(y + h) // CELL, x // CELL:(x + w) // CELL] = i
        self.place = pm
        self.art &= pm >= 0          # only cells of a place count (not a world chunk's ring)
        self.pm4 = np.repeat(np.repeat(pm, CELL // WALK, 0), CELL // WALK, 1)
        # prop coverage per cell: share of the cell's pixels each prop shows on top
        own = self.owner.reshape(self.ny, CELL, self.nx, CELL).transpose(0, 2, 1, 3).reshape(self.ny * self.nx, -1)
        self.cover = {}            # prop index -> list of (cy, cx, share)
        self.top = np.full((self.ny, self.nx), -1, np.int32)
        self.top_share = np.zeros((self.ny, self.nx))
        cell_i = np.repeat(np.arange(self.ny * self.nx), CELL * CELL)
        o = own.ravel()
        m = o >= 0
        if m.any():
            pair = cell_i[m].astype(np.int64) * (len(R.props) + 1) + o[m]
            u, c = np.unique(pair, return_counts=True)
            for k, n in zip(u.tolist(), c.tolist()):
                ci, pi = divmod(k, len(R.props) + 1)
                share = n / (CELL * CELL)
                cy, cx = divmod(ci, self.nx)
                self.cover.setdefault(pi, []).append((cy, cx, share))
                if share > self.top_share[cy, cx]:
                    self.top_share[cy, cx], self.top[cy, cx] = share, pi

    def prop_cells(self, i: int):
        """The cells a placed sprite answers for: those it covers by a quarter or more, and the
        cell of its foot."""
        p = self.R.props[i]
        out = {(cy, cx) for (cy, cx, s) in self.cover.get(i, []) if s >= 0.25}
        out.add(((p['y'] + p['h'] - 2) // CELL, (p['x'] + p['w'] // 2) // CELL))
        return [(cy, cx) for (cy, cx) in out if 0 <= cy < self.ny and 0 <= cx < self.nx]

    # -- (a) detail ------------------------------------------------------------------------
    def kinds(self):
        R, pal = self.R, self.ctx['palette']
        T = R.terrain.reshape(self.ny, CELL // WALK, self.nx, CELL // WALK).transpose(0, 2, 1, 3).reshape(self.ny, self.nx, -1)
        cnt = np.stack([(T == c).sum(-1) for c in range(6)], -1)
        major = cnt.argmax(-1)
        lab = oklab(R.ground[..., :3]).reshape(self.ny, CELL, self.nx, CELL, 3).transpose(0, 2, 1, 3, 4)
        L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
        C = np.hypot(A, B)
        snowy = ((L > 0.80) & (C < 0.045)).mean((2, 3))
        rgb = R.ground[..., :3].astype(int).reshape(self.ny, CELL, self.nx, CELL, 3).transpose(0, 2, 1, 3, 4)
        bluish = ((rgb[..., 2] >= rgb[..., 0] + 18) & (rgb[..., 2] >= rgb[..., 1] - 6) & (rgb[..., 0] < 150)).mean((2, 3))
        canopy = ((rgb[..., 1] > rgb[..., 0]) & (rgb[..., 1] > rgb[..., 2]) & (L < 0.5)).mean((2, 3))
        # how wide the water is: erosions of the water mask until it is gone (in walk cells)
        wmask = R.terrain == WATER
        depth = np.zeros(wmask.shape, np.int16)
        cur = wmask.copy()
        k = 0
        while cur.any() and k < 64:
            k += 1
            depth[cur] = k
            p = np.pad(cur, 1, constant_values=False)
            cur = cur & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
        dcell = depth.reshape(self.ny, CELL // WALK, self.nx, CELL // WALK).max((1, 3))
        dp = np.pad(dcell, 1)
        wide = np.max(np.stack([dp[y:y + self.ny, x:x + self.nx] for y in range(3) for x in range(3)]), 0)
        kind = np.empty((self.ny, self.nx), object)
        guide = self.ctx['guide']
        scen = np.zeros((self.ny, self.nx), bool)
        for i, pl in enumerate(R.places):
            if pl.kind == 'scenery':
                scen |= self.place == i
        for cy in range(self.ny):
            for cx in range(self.nx):
                t = int(major[cy, cx])
                if t == NONE:
                    if bluish[cy, cx] >= 0.5:
                        k_ = 'water'
                    elif snowy[cy, cx] >= 0.5:
                        k_ = 'snow'
                    elif canopy[cy, cx] >= 0.5:
                        k_ = 'tree'
                    else:
                        k_ = 'ground'
                elif t == WATER:
                    k_ = 'stream' if wide[cy, cx] * WALK <= 24 else 'water'
                elif t == LAVA:
                    k_ = 'lava'
                elif t == WALL:
                    k_ = 'face'
                elif snowy[cy, cx] >= 0.5:
                    k_ = 'snow'
                elif scen[cy, cx] and canopy[cy, cx] >= 0.5:
                    k_ = 'tree'          # the forest's canopy past the world
                else:
                    k_ = 'paving' if R.id in CITY_REGIONS else 'ground'
                pi = self.top[cy, cx]
                if pi >= 0 and self.top_share[cy, cx] >= 0.5:
                    sk = (guide['sprites'].get(re.sub(r'_f\d+$', '', R.props[pi]['sprite'])) or [None])[0]
                    k_ = DETAIL_KIND.get(sk, 'cloth' if sk in ('tent', 'stall', 'food_stall', 'cart_stall', 'cafe_set',
                                                               'hammock', 'washing_line') else 'other')
                kind[cy, cx] = k_
        self.kind = kind

    def detail(self):
        R = self.R
        base = self.ctx['baselines']
        bars = self.ctx['bars']
        pipes: dict = {}
        for k in set(self.kind.ravel().tolist()):
            if k in bars:
                pipes.setdefault((bars[k]['adult_px'], bars[k]['jpeg_quality']), set()).add(k)
        for pl in R.places:
            x, y, w, h = pl.rect
            cys, cxs = slice(y // CELL, (y + h) // CELL), slice(x // CELL, (x + w) // CELL)
            sub = self.kind[cys, cxs]
            art = self.art[cys, cxs]
            for (adult, q), ks in pipes.items():
                want = np.isin(sub, list(ks)) & art
                if not want.any():
                    continue
                keys = pipe_keys(self.comp[y:y + h, x:x + w], adult, q)
                pc = patch_counts(keys)
                per = {m: v.reshape(h // CELL, CELL // PATCH, w // CELL, CELL // PATCH).mean((1, 3)) for m, v in pc.items()}
                for cy, cx in zip(*np.nonzero(want)):
                    ours = {m: float(per[m][cy, cx]) for m in per}
                    k = sub[cy, cx]
                    ok, why = judge_cell(ours, bars[k])
                    gy, gx = cy + y // CELL, cx + x // CELL
                    self.metrics.setdefault('detail', {})[(gy, gx)] = (k, ours)
                    self.mark('detail', gy, gx, PASS if ok else RED, '' if ok else f'{k}: {why}')
        for cy, cx in zip(*np.nonzero(self.art)):
            k = self.kind[cy, cx]
            if k not in bars:
                self.mark('detail', cy, cx, AMBER, f'{k}: no baseline, judged by eye')
        del base

    # -- (b) soft grid and (c) straight runs, from the terrain ------------------------------
    @staticmethod
    def run_lengths(m: np.ndarray) -> np.ndarray:
        """For each True, the length of the run of Trues along the last axis it belongs to."""
        rows, n = m.shape
        mp = np.concatenate([m.astype(np.int8), np.zeros((rows, 1), np.int8)], 1).ravel()
        d = np.diff(np.concatenate([[0], mp]))
        st, en = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        out = np.zeros(mp.size, np.int32)
        if len(st):
            ln = en - st
            idx = np.repeat(st, ln) + (np.arange(ln.sum()) - np.repeat(np.cumsum(ln) - ln, ln))
            out[idx] = np.repeat(ln, ln)
        return out.reshape(rows, n + 1)[:, :n]

    def soft_grid(self):
        R = self.R
        T = R.terrain
        pm = self.pm4
        known = T != NONE
        scale = CELL // WALK
        # samples: horizontal edges hb[y, x] between rows y and y + 1 (line y + 1), vertical vb
        hb = (T[:-1] != T[1:]) & known[:-1] & known[1:] & (pm[:-1] == pm[1:])
        vb = (T[:, :-1] != T[:, 1:]) & known[:, :-1] & known[:, 1:] & (pm[:, :-1] == pm[:, 1:])
        hr = self.run_lengths(hb)
        vr = self.run_lengths(vb.T).T
        n = np.zeros((self.ny, self.nx), int)
        ok = np.zeros((self.ny, self.nx), int)
        off = np.zeros((self.ny, self.nx), int)
        for (b, r, line_axis) in ((hb, hr, 0), (vb, vr, 1)):
            ys, xs = np.nonzero(b)
            cy, cx = ys // scale, xs // scale
            np.add.at(n, (cy, cx), 1)
            np.add.at(ok, (cy, cx), (r[ys, xs] >= 4).astype(int))
            line = (ys if line_axis == 0 else xs) + 1
            bad = (r[ys, xs] >= 6) & ((line * WALK) % GRID != 0)
            np.add.at(off, (cy[bad], cx[bad]), 1)
        has = self.art & known.reshape(self.ny, scale, self.nx, scale).any((1, 3))
        self.pass_where('grid-edges', has)
        self.pass_where('rim-on-grid', has)
        for cy, cx in zip(*np.nonzero((n >= 4) & has)):
            share = ok[cy, cx] / n[cy, cx]
            if share < 0.8:
                self.mark('grid-edges', cy, cx, RED, f'{100 * share:.0f} % of {n[cy, cx]} boundary samples in straight runs of 16 px')
        for cy, cx in zip(*np.nonzero((off > 0) & has)):
            self.mark('rim-on-grid', cy, cx, RED, f'{off[cy, cx]} samples of straight runs off the 8 px lines')
        # faces: a band of wall or cliff between walkable ground above and below, two cells wide
        tiered = R.tiers != 255
        if R.id in INTERIOR_REGIONS and not tiered.any():
            return
        self.pass_where('face-height', has)
        wall = (T == WALL) & ~tiered
        wr = self.run_lengths(wall.T).T          # vertical run length of each wall cell
        walkable = np.isin(T, WALKABLE_CODES)
        top = np.zeros_like(wall)
        top[1:] = wall[1:] & ~wall[:-1]
        wide2 = np.zeros_like(wall)
        wide2[:, 1:] |= wall[:, :-1]
        wide2[:, :-1] |= wall[:, 1:]
        for y, x in zip(*np.nonzero(top & wide2)):
            L = int(wr[y, x])
            if y - 1 < 0 or y + L >= T.shape[0] or L > 16:
                continue
            if not (walkable[y - 1, x] and walkable[y + L, x]) or pm[y - 1, x] != pm[y + L, x]:
                continue
            hpx = L * WALK
            if hpx not in HEIGHTS:
                for yy in range(y, y + L):
                    self.mark('face-height', yy // scale, x // scale, RED, f'a {hpx} px face (12, 16, 32 or 40)')
        if tiered.any():
            self.tier_checks(tiered, scale)

    def tier_checks(self, tiered: np.ndarray, scale: int):
        R = self.R
        t = R.tiers
        # 'f' a face, 'b' a side band (the 3 to 8 px band where a tier ends west or east): a band
        # separates two tiers sideways like a face, but only 'f' has a face's height and side
        digit = (t >= ord('0')) & (t <= ord('9'))
        face = t == ord('f')
        stair = t == ord('s')
        val = np.where(digit, t.astype(int) - ord('0'), -1)
        has = self.art & tiered.reshape(self.ny, scale, self.nx, scale).any((1, 3))
        for c in ('tier-step', 'north-face', 'side-band'):
            self.pass_where(c, has)
        wk = R.walk
        for a, b in (((slice(None, -1), slice(None)), (slice(1, None), slice(None))),
                     ((slice(None), slice(None, -1)), (slice(None), slice(1, None)))):
            bad = digit[a] & digit[b] & wk[a] & wk[b] & (val[a] != val[b])
            for y, x in zip(*np.nonzero(bad)):
                self.mark('tier-step', y // scale, x // scale, RED, 'walkable cells on two tiers meet with no stair or ramp')
        fr = self.run_lengths(face)              # horizontal run of each face cell
        fv = self.run_lengths(face.T).T          # vertical run
        topf = np.zeros_like(face)
        topf[1:] = face[1:] & ~face[:-1]
        topf[0] = face[0]
        for y, x in zip(*np.nonzero(topf & (fr >= 3))):
            L = int(fv[y, x])
            hpx = L * WALK
            if hpx not in HEIGHTS:
                for yy in range(y, y + L):
                    self.mark('face-height', yy // scale, x // scale, RED, f'a {hpx} px face (12, 16, 32 or 40)')
            above = val[y - 1, x] if y > 0 else -1
            below = val[y + L, x] if y + L < t.shape[0] else -1
            if above >= 0 and below >= 0 and above <= below:
                self.mark('north-face', y // scale, x // scale, RED, 'a face on a north edge (the higher tier is south)')
        # a tier that drops to the south with no face, or ends west or east with no side band
        a, b = digit[:-1] & digit[1:], val[:-1] > val[1:]
        for y, x in zip(*np.nonzero(a & b)):
            self.mark('face-height', y // scale, x // scale, RED, 'a tier drops to the south with no face')
        a, b = digit[:, :-1] & digit[:, 1:], val[:, :-1] != val[:, 1:]
        for y, x in zip(*np.nonzero(a & b)):
            self.mark('side-band', y // scale, x // scale, RED, 'a tier ends west or east with no side band')
        st = self.run_lengths(stair)
        for y, x in zip(*np.nonzero(stair & (st < 8))):
            self.mark('tier-step', y // scale, x // scale, RED, f'a stair or ramp {int(st[y, x]) * WALK} px wide (34 or more)')

    # -- (c) hard edges --------------------------------------------------------------------
    def straight_runs(self):
        """Benchmark check 8 on the 8 px grid (roughness inside a cell drops out): a boundary
        between two kinds of ground that runs on one line for more than 96 px without a jog
        (path edges 240 px, check 16)."""
        R = self.R
        T = R.terrain
        r2, c2 = T.shape[0] // 2, T.shape[1] // 2
        q = T[:r2 * 2, :c2 * 2].reshape(r2, 2, c2, 2).transpose(0, 2, 1, 3).reshape(r2, c2, 4)
        cnt = np.stack([(q == c).sum(-1) for c in range(6)], -1)
        T8 = cnt.argmax(-1)
        pm8 = self.pm4[::2, ::2]
        known = T8 != NONE
        if R.id in INTERIOR_REGIONS:
            return
        has = self.art & np.isin(self.R.terrain, list(range(1, 6))).reshape(self.ny, 8, self.nx, 8).any((1, 3))
        self.pass_where('straight-run', has)
        s = CELL // GRID
        names = {GROUND: 'ground', PATH: 'path', WATER: 'water', LAVA: 'lava', WALL: 'cliff or wall'}
        for horiz in (True, False):
            A = T8 if horiz else T8.T
            P = pm8 if horiz else pm8.T
            K = known if horiz else known.T
            b = (A[:-1] != A[1:]) & K[:-1] & K[1:] & (P[:-1] == P[1:])
            pathy = np.isin(A[:-1], (GROUND, PATH)) & np.isin(A[1:], (GROUND, PATH))
            subs = [(b & pathy, PATH_STRAIGHT_MAX)] + ([] if R.id in BUILT_REGIONS else [(b & ~pathy, STRAIGHT_MAX)])
            for sub, limit in subs:
                rl = self.run_lengths(sub)
                for y, x in zip(*np.nonzero(sub & (rl * GRID > limit))):
                    ln = int(rl[y, x]) * GRID
                    what = f'{names.get(int(A[y, x]), "?")}/{names.get(int(A[y + 1, x]), "?")}'
                    cy, cx = (y // s, x // s) if horiz else (x // s, y // s)
                    self.mark('straight-run', cy, cx, RED, f'a {ln} px straight {what} edge with no 8 px jog (max {limit})')

    def ruler_edges(self):
        """Pixel-straight edges: a step in colour (4 px bands either side differ by 20 or more,
        mean RGB) whose strongest row (or column) stays exactly the same for more than 96 px.
        Drawn roughness (a lip, tufts, a chipped coping) moves the strongest line and breaks
        the run; only a ruled line survives."""
        R = self.R
        if R.id in BUILT_REGIONS | INTERIOR_REGIONS:
            return
        self.pass_where('ruler-edge', self.art)
        for pl in R.places:
            x, y, w, h = pl.rect
            g = R.ground[y:y + h, x:x + w, :3].astype(np.float32)
            alpha = R.ground[y:y + h, x:x + w, 3] > 0
            for horiz in (True, False):
                G = g if horiz else g.transpose(1, 0, 2)
                Am = alpha if horiz else alpha.T
                n = G.shape[0]
                cs = np.concatenate([np.zeros((1,) + G.shape[1:], np.float32), np.cumsum(G, 0)], 0)
                step = np.zeros(G.shape[:2], np.float32)
                ys = np.arange(4, n - 4)
                below = (cs[ys + 4] - cs[ys]) / 4
                above = (cs[ys] - cs[ys - 4]) / 4
                step[ys] = np.abs(below - above).mean(-1)
                lm = np.zeros_like(step, dtype=bool)
                lm[1:-1] = (step[1:-1] > step[:-2]) & (step[1:-1] >= step[2:]) & (step[1:-1] >= 20)
                lm &= Am & np.roll(Am, 1, 0)
                rl = self.run_lengths(lm)
                for yy, xx in zip(*np.nonzero(lm & (rl > STRAIGHT_MAX))):
                    if xx % 8:
                        continue
                    px, py = (x + xx, y + yy) if horiz else (x + yy, y + xx)
                    self.mark('ruler-edge', py // CELL, px // CELL, RED,
                              f'a ruled {"horizontal" if horiz else "vertical"} edge {int(rl[yy, xx])} px long')

    def seams(self):
        """Where a zone (an area), the garden, a scenery cell or a chunk meets the next: a cut (the
        line is sharper than the picture round it), world_lint's tone figure (mean of the 6 px
        strips over plain ground where the walk crosses, more than 14 apart) and its terrain
        runs (water, a path or lava on one side only, 16 px or more)."""
        R = self.R
        g = R.ground[..., :3].astype(np.float32)
        alpha = R.ground[..., 3] > 0
        self.pass_where('seam', self.art)
        lines = {}
        for pl in R.places:
            x, y, w, h = pl.rect
            for k in (('v', x), ('v', x + w), ('h', y), ('h', y + h)):
                lines.setdefault(k, []).append(pl)
        # a line between areas of one painted chunk is no join (the ground is one picture): skip
        # it when every place along it is painted and it lies inside the painted areas' box
        pp = [pl.rect for pl in R.places if pl.painted]
        if pp:
            px0, py0 = min(r[0] for r in pp), min(r[1] for r in pp)
            px1, py1 = max(r[0] + r[2] for r in pp), max(r[1] + r[3] for r in pp)
            for (o, B) in list(lines):
                inner = (px0 < B < px1) if o == 'v' else (py0 < B < py1)
                if inner and all(pl.painted for pl in lines[(o, B)]):
                    del lines[(o, B)]
        # (A 256 px world tile inside a chunk is a copy of one composite, so its edge cannot seam:
        # world_canvas checks the tiles against the chunk pixel for pixel. The joins that can seam
        # are the zones' and areas' edges, the scenery cells' and a chunk's box against the ring
        # of its neighbour, which are all place edges here.)
        for (o, B), what in sorted(lines.items()):
            if B <= 8 or B >= (R.w if o == 'v' else R.h) - 8:
                continue
            G = g if o == 'v' else g.transpose(1, 0, 2)
            Al = alpha if o == 'v' else alpha.T
            length = G.shape[0]
            dif = {k: np.abs(G[:, B + k] - G[:, B + k - 1]).mean(-1) for k in range(-8, 9)}
            cuts = []
            for s0 in range(0, length, CELL):
                s1 = min(length, s0 + CELL)
                if not (Al[s0:s1, B - 8:B + 8].all()):
                    continue
                d0 = float(dif[0][s0:s1].mean())
                din = float(np.median([dif[k][s0:s1].mean() for k in (-8, -7, -6, -5, -4, -3, -2, 2, 3, 4, 5, 6, 7, 8)]))
                if d0 >= 16 and d0 >= 2.5 * din + 6:
                    cuts.append((s0, d0, din))
            for s0, d0, din in cuts:
                self._seam_mark(o, B, s0, f'cut: the line steps {d0:.0f} against {din:.0f} round it')
        # the lint's tone and terrain figures, between neighbouring places that have terrain
        T, wk = R.terrain, R.walk
        for i, a in enumerate(R.places):
            for b in R.places[i + 1:]:
                if a.painted and b.painted:
                    continue
                ax, ay, aw, ah = a.rect
                bx, by, bw, bh = b.rect
                if ax + aw == bx and ay < by + bh and by < ay + ah:
                    o, B, lo, hi = 'v', bx, max(ay, by), min(ay + ah, by + bh)
                elif bx + bw == ax and ay < by + bh and by < ay + ah:
                    o, B, lo, hi = 'v', ax, max(ay, by), min(ay + ah, by + bh)
                elif ay + ah == by and ax < bx + bw and bx < ax + aw:
                    o, B, lo, hi = 'h', by, max(ax, bx), min(ax + aw, bx + bw)
                elif by + bh == ay and ax < bx + bw and bx < ax + aw:
                    o, B, lo, hi = 'h', ay, max(ax, bx), min(ax + aw, bx + bw)
                else:
                    continue
                Tt = T if o == 'v' else T.T
                Wt = wk if o == 'v' else wk.T
                G = g if o == 'v' else g.transpose(1, 0, 2)
                c = B // WALK
                near, far = Tt[:, c - 3:c], Tt[:, c:c + 3]
                if (near == NONE).all() or (far == NONE).all():
                    continue
                for want, name in ((WATER, 'water'), (PATH, 'a path'), (LAVA, 'lava')):
                    diff = (near == want).any(1) != (far == want).any(1)
                    diff[:lo // WALK] = False
                    diff[hi // WALK:] = False
                    rl = self.run_lengths(diff[None, :])[0]
                    for k in np.nonzero(diff & (rl >= 4))[0]:
                        self._seam_mark(o, B, int(k) * WALK, f'{name} stops at the border')
                for s0 in range(lo, hi, CELL):
                    rows = np.arange(s0 // WALK, min(hi, s0 + CELL) // WALK)
                    keep = rows[(Tt[rows, c - 1] == GROUND) & (Tt[rows, c] == GROUND) & Wt[rows, c - 1] & Wt[rows, c]]
                    if len(keep) * WALK < 12:
                        continue
                    px = np.concatenate([np.arange(r * WALK, r * WALK + WALK) for r in keep])
                    ta = G[px, B - 6:B].reshape(-1, 3).mean(0)
                    tb = G[px, B:B + 6].reshape(-1, 3).mean(0)
                    dd = float(np.abs(ta - tb).mean())
                    if dd > 14:
                        self._seam_mark(o, B, s0, f'tone: the ground changes by {dd:.0f} across the border')

    def _seam_mark(self, o: str, B: int, s: int, why: str):
        if o == 'v':
            for cx in ((B - 1) // CELL, B // CELL):
                self.mark('seam', s // CELL, cx, RED, why)
        else:
            for cy in ((B - 1) // CELL, B // CELL):
                self.mark('seam', cy, s // CELL, RED, why)

    # -- (d) style -------------------------------------------------------------------------
    def style(self):
        R, pal = self.R, self.ctx['palette']
        keys = rgb_key(self.comp)
        on = pal.on_house(keys)
        a = self.comp[..., 3] > 0
        sh = (on & a).reshape(self.ny, CELL, self.nx, CELL).sum((1, 3)) / np.maximum(1, a.reshape(self.ny, CELL, self.nx, CELL).sum((1, 3)))
        today = np.isin(keys, list(pal.today))
        tsh = (today & a).reshape(self.ny, CELL, self.nx, CELL).sum((1, 3)) / np.maximum(1, a.reshape(self.ny, CELL, self.nx, CELL).sum((1, 3)))
        self.metrics['palette'] = sh
        self.metrics['today'] = tsh
        self.pass_where('palette', self.art)
        for cy, cx in zip(*np.nonzero(self.art & (sh < 0.9))):
            self.mark('palette', cy, cx, AMBER, f'{100 * sh[cy, cx]:.0f} % on the house palette ({100 * tsh[cy, cx]:.0f} % on today\'s ramps)')
        # checker dither on walkable ground (house-style rule 4: never on open walkable ground)
        k = rgb_key(R.ground)
        p = np.pad(k, 1, mode='edge')
        c = p[1:-1, 1:-1]
        lone = (c != p[:-2, 1:-1]) & (c != p[2:, 1:-1]) & (c != p[1:-1, :-2]) & (c != p[1:-1, 2:])
        chk = lone & (c == p[:-2, :-2]) & (c == p[2:, 2:]) & (c == p[:-2, 2:]) & (c == p[2:, :-2])
        wpx = np.repeat(np.repeat(R.walk, WALK, 0), WALK, 1)
        n = wpx.reshape(self.ny, CELL, self.nx, CELL).sum((1, 3))
        d = (chk & wpx).reshape(self.ny, CELL, self.nx, CELL).sum((1, 3))
        self.pass_where('dither', self.art & (n >= 256))
        for cy, cx in zip(*np.nonzero(self.art & (n >= 256) & (d > 0.005 * n))):
            self.mark('dither', cy, cx, RED, f'{100 * d[cy, cx] / n[cy, cx]:.1f} % checker dither on walkable ground')

    # -- (d, e, f) every placed sprite, and (f) every ground picture -----------------------
    def sprites(self):
        R = self.R
        ctx = self.ctx
        for path, (x, y, w, h) in R.pieces:
            sev, why = ctx['ground_ledger'](path)
            for cy, cx in self.cells_of_box(x, y, w, h):
                self.mark('ledger', cy, cx, sev, f'{os.path.relpath(path, ctx["root"])}: {why}' if why else '')
        for i, p in enumerate(R.props):
            cells = self.prop_cells(i)
            if not cells:
                continue
            st = ctx['sprite_style'](p)
            sz = ctx['sprite_size'](p)
            lg = ctx['sprite_ledger'](p)
            for (check, (sev, why)) in (('sprite-style', st), ('size', sz), ('ledger', lg)):
                for cy, cx in cells:
                    self.mark(check, cy, cx, sev, f'{p["sprite"]}: {why}' if why else '')
                if sev in (AMBER, RED):
                    self.findings.append({'check': check, 'severity': 'red' if sev == RED else 'amber',
                                          'sprite': p['sprite'], 'id': p['id'], 'why': why,
                                          'box': [p['x'], p['y'], p['w'], p['h']]})

    # -- (g) the benchmark, per screen ------------------------------------------------------
    def benchmark(self):
        R, guide = self.R, self.ctx['guide']
        if R.id in INTERIOR_REGIONS:
            return
        screens = [(i, pl) for i, pl in enumerate(R.places) if pl.screen]
        kinds = [(guide['sprites'].get(re.sub(r'_f\d+$', '', p['sprite'])) or [None])[0] for p in R.props]
        groups = {k: v['group'] for k, v in guide['kinds'].items()}
        foot = [(p['x'] + p['w'] // 2, p['y'] + p['h'] - 2) for p in R.props]
        has_lm = {}
        for i, pl in screens:
            x, y, w, h = pl.rect
            inside = [j for j, (fx, fy) in enumerate(foot) if x <= fx < x + w and y <= fy < y + h]
            builds = [j for j in inside if groups.get(kinds[j]) == 'buildings']
            inter = [j for j in inside if kinds[j] in INTERACT or groups.get(kinds[j]) == 'buildings'
                     or R.props[j].get('action')]
            story = [j for j in inside if j not in inter and kinds[j] is not None
                     and (groups.get(kinds[j]) in ('street furniture and vehicles', 'people and animals')
                          or kinds[j] in ('snowman', 'scarecrow', 'beehive', 'cairn', 'standing_stone', 'woodpile', 'bale',
                                          'haystack'))]
            n_inter = len(inter) + R.residents.get(pl.id, 0)
            settle = len(builds) >= 2
            lo_i, lo_s = (6, 6) if settle else (2, 3)
            cys, cxs = slice(y // CELL, (y + h) // CELL), slice(x // CELL, (x + w) // CELL)
            mask = np.zeros((self.ny, self.nx), bool)
            mask[cys, cxs] = True
            mask &= self.art
            self.pass_where('density', mask)
            self.metrics.setdefault('screens', {})[pl.id] = {'settlement': settle, 'interactables': n_inter,
                                                             'story': len(story), 'buildings': len(builds)}
            if n_inter < lo_i or len(story) < lo_s:
                why = (f'{"settlement" if settle else "route"} screen: {n_inter} interactables (min {lo_i}), '
                       f'{len(story)} story props (min {lo_s})')
                for cy, cx in zip(*np.nonzero(mask)):
                    self.mark('density', cy, cx, AMBER, why)
                self.findings.append({'check': 'density', 'severity': 'amber', 'place': pl.id, 'why': why})
            has_lm[i] = any(kinds[j] in LANDMARK for j in inside)
        # landmark spacing: one in this screen or the next (any of the eight round it)
        for i, pl in screens:
            x, y, w, h = pl.rect
            near = [j for j, q in screens if abs(q.rect[0] - x) <= ZW and abs(q.rect[1] - y) <= ZH]
            mask = np.zeros((self.ny, self.nx), bool)
            mask[y // CELL:(y + h) // CELL, x // CELL:(x + w) // CELL] = True
            mask &= self.art
            self.pass_where('landmark', mask)
            if not any(has_lm.get(j) for j in near):
                for cy, cx in zip(*np.nonzero(mask)):
                    self.mark('landmark', cy, cx, AMBER, 'no landmark in this screen or the ones round it')
                self.findings.append({'check': 'landmark', 'severity': 'amber', 'place': pl.id,
                                      'why': 'no landmark within a screen'})
        # empty path: path cells more than 100 px from anything to notice (a prop's foot, a stand)
        pts = np.array(foot + list(R.stands), float) if (foot or R.stands) else np.zeros((0, 2))
        ys, xs = np.nonzero((R.terrain == PATH) & R.walk)
        has = self.art & (R.terrain == PATH).reshape(self.ny, 8, self.nx, 8).any((1, 3))
        self.pass_where('empty-path', has)
        if len(ys) and len(pts):
            cx_, cy_ = xs * WALK + 2, ys * WALK + 2
            far = np.ones(len(ys), bool)
            for k in range(0, len(pts), 256):
                d = (cx_[:, None] - pts[None, k:k + 256, 0]) ** 2 + (cy_[:, None] - pts[None, k:k + 256, 1]) ** 2
                far &= (d > 100 ** 2).all(1)
            for y, x in zip(ys[far], xs[far]):
                self.mark('empty-path', y // 8, x // 8, AMBER, 'path more than 100 px from anything to notice')
        # identical runs: four or more of one sprite in a row (check 9)
        self.pass_where('identical', self.art)
        by = {}
        for j, p in enumerate(R.props):
            if not p['overhead']:
                by.setdefault(re.sub(r'_f\d+$', '', p['sprite']), []).append(j)
        for spr, js in by.items():
            if len(js) < 4:
                continue
            for horiz in (True, False):
                pts_ = sorted(js, key=lambda j: (foot[j][1] if horiz else foot[j][0], foot[j][0] if horiz else foot[j][1]))
                used = set()
                for a in pts_:
                    if a in used:
                        continue
                    chain = [a]
                    while True:
                        last = chain[-1]
                        nxt = [b for b in js if b not in chain and
                               (abs(foot[b][1] - foot[last][1]) <= 8 and 0 < foot[b][0] - foot[last][0] <= 1.5 * R.props[b]['w'] + 8
                                if horiz else
                                abs(foot[b][0] - foot[last][0]) <= 8 and 0 < foot[b][1] - foot[last][1] <= 1.5 * R.props[b]['h'] + 8)]
                        if not nxt:
                            break
                        chain.append(min(nxt, key=lambda b: abs(foot[b][0] - foot[last][0]) + abs(foot[b][1] - foot[last][1])))
                    if len(chain) >= 4:
                        used |= set(chain)
                        why = f'{len(chain)} {spr} in a row'
                        for j in chain:
                            for cy, cx in self.prop_cells(j):
                                self.mark('identical', cy, cx, AMBER, why)
                        self.findings.append({'check': 'identical', 'severity': 'amber', 'sprite': spr, 'why': why,
                                              'box': [R.props[chain[0]]['x'], R.props[chain[0]]['y'],
                                                      R.props[chain[-1]]['x'] + R.props[chain[-1]]['w'] - R.props[chain[0]]['x'],
                                                      R.props[chain[-1]]['y'] + R.props[chain[-1]]['h'] - R.props[chain[0]]['y']]})

    # -- all of it -------------------------------------------------------------------------
    def run(self, timing: dict | None = None):
        steps = [('compose', self.compose), ('kinds', self.kinds), ('detail', self.detail), ('soft grid', self.soft_grid),
                 ('straight runs', self.straight_runs), ('ruler edges', self.ruler_edges), ('seams', self.seams),
                 ('style', self.style), ('sprites', self.sprites), ('benchmark', self.benchmark)]
        for name, fn in steps:
            t = time.time()
            fn()
            if timing is not None:
                timing[name] = timing.get(name, 0) + time.time() - t
        for c in CHECK_IDS:
            self.status[c][~self.art] = NA
        self.settle()
        return self

    def settle(self):
        st = np.stack([self.status[c] for c in CHECK_IDS])
        self.worst = st.max(0)
        self.worst[~self.art] = NA
        # the drawing alone: every check but the ledger (which grades the pictures, not a cell)
        self.drawn = np.stack([self.status[c] for c in CHECK_IDS if c != 'ledger']).max(0)
        self.drawn[~self.art] = NA


# --------------------------------------------------------------------------------------------
# per-sprite judgements (each sprite once), the ledger, the context

def load_ledger(root: str, path: str | None) -> tuple[dict | None, str]:
    """The asset ledger (docs/vision/asset-ledger.md, scripts/art/asset_ledger.json): each
    picture's grade, KEEP, REWORK or RETIRE, by file (assets/...) and by name. `path` may be a
    file or 'git:REF' (the ledger on a branch that has not merged yet). Also reads simpler
    shapes ({name: status}, a list of records, or a Markdown table with a backticked name and a
    status in one row). (None, '') when there is no ledger: every placed asset is 'ungraded'."""
    text, label = None, ''
    if path and path.startswith('git:'):
        ref = path[4:]
        r = subprocess.run(['git', 'show', f'{ref}:scripts/art/asset_ledger.json'], cwd=root, capture_output=True, text=True)
        sha = subprocess.run(['git', 'rev-parse', '--short', ref], cwd=root, capture_output=True, text=True).stdout.strip()
        if r.returncode == 0:
            text, label = r.stdout, f'{ref}@{sha}:scripts/art/asset_ledger.json'
    else:
        for p in ([path] if path else [os.path.join(root, 'scripts', 'art', 'asset_ledger.json'),
                                       os.path.join(root, 'docs', 'vision', 'asset-ledger.md')]):
            if p and os.path.exists(p):
                text, label = open(p).read(), os.path.relpath(p, root)
                break
    if text is None:
        return None, ''
    by_file, by_name = {}, {}
    if label.endswith('.json'):
        data = json.loads(text)
        items = data.get('assets', data) if isinstance(data, dict) else data
        recs = list(items.items()) if isinstance(items, dict) else [(None, v) for v in items]
        for k, v in recs:
            if isinstance(v, str):
                by_name[k] = (v.upper(), '')
                continue
            g = (v.get('grade') or v.get('status') or '').upper()
            if g not in ('KEEP', 'REWORK', 'RETIRE'):
                continue
            why = v.get('why', '')
            for f in v.get('files', []):
                by_file[f] = (g, why)
            name = v.get('name') or v.get('asset') or v.get('sprite') or k
            if name and (k is None or k.startswith('prop/') or name not in by_name):
                by_name[name] = (g, why)
        for rule in (data.get('rules', []) if isinstance(data, dict) else []):
            by_file['glob:' + rule['glob']] = (rule['grade'].upper(), rule.get('why', ''))
    else:
        for line in text.splitlines():
            m = re.search(r'\b(KEEP|REWORK|RETIRE)\b', line)
            if m and line.lstrip().startswith('|'):
                for name in re.findall(r'`([\w./-]+)`', line):
                    (by_file if '/' in name else by_name).setdefault(name, (m.group(1), ''))
    return {'file': by_file, 'name': by_name}, label


def ledger_grade(ledger: dict | None, root: str, path: str, name: str | None = None) -> tuple[int, str]:
    if ledger is None:
        return AMBER, 'ungraded (no asset ledger yet)'
    rel = os.path.relpath(path, root)
    hit = ledger['file'].get(rel)
    if hit is None:
        import fnmatch
        for k, v in ledger['file'].items():
            if k.startswith('glob:') and fnmatch.fnmatch(rel, k[5:]):
                hit = v
                break
    if hit is None and name:
        hit = ledger['name'].get(name)
    if hit is None:
        return AMBER, 'not in the asset ledger'
    g, why = hit
    return (PASS, '') if g == 'KEEP' else (RED, f'{g}' + (f': {why[:120]}' if why else ''))


def make_context(root: str, ledger_path: str | None) -> dict:
    import style_lint
    guide = size_check.load_guide()
    base = detail_bar.load()
    bars = {}
    for k in detail_bar.KINDS:
        try:
            bars[k] = detail_bar.bar(k, base)
        except KeyError:
            pass
    ledger, ledger_src = load_ledger(root, ledger_path)
    cache: dict = {}

    def base_name(p):
        return re.sub(r'_f\d+$', '', p['sprite'])

    def sprite_style(p):
        key = ('style', p['png'])
        if key not in cache:
            m = style_lint.measure(Image.fromarray(p['img']))
            miss = style_lint.misses(m) if m else []
            red = [x for x in miss if x not in STYLE_AMBER]
            amb = [x for x in miss if x in STYLE_AMBER]
            cache[key] = (RED, ', '.join(red + amb)) if red else (AMBER, ', '.join(amb)) if amb else (PASS, '')
            cache[('style-m', p['png'])] = m
        return cache[key]

    def sprite_size(p):
        key = ('size', p['png'])
        if key not in cache:
            entry = guide['sprites'].get(base_name(p))
            if entry is None:
                cache[key] = (AMBER, 'no kind in the size guide')
            elif entry[0] is None:
                cache[key] = (NA, '')
            else:
                scale = guide['unit']['png_scale'] if p['source'] != 'garden' else max(1, round(Image.open(p['png']).width / p['w']))
                h, w = size_check.measure(p['png'], scale)
                k = guide['kinds'][entry[0]]
                dh, dw = size_check.judge(h, k['h'], guide['tolerance']), size_check.judge(w, k['w'], guide['tolerance'])
                if dh or dw:
                    parts = []
                    if dh:
                        parts.append(f"h {h:g} {'over' if dh > 0 else 'under'} {k['h'][0]} to {k['h'][1]}")
                    if dw:
                        parts.append(f"w {w:g} {'over' if dw > 0 else 'under'} {k['w'][0]} to {k['w'][1]}")
                    cache[key] = (RED, f'{entry[0]}: ' + ', '.join(parts))
                else:
                    cache[key] = (PASS, '')
        return cache[key]

    def sprite_ledger(p):
        return ledger_grade(ledger, root, p['png'], base_name(p))

    def ground_ledger(path):
        return ledger_grade(ledger, root, path)

    return {'guide': guide, 'baselines': base, 'bars': bars, 'palette': Palette(root), 'sprites': {},
            'sprite_style': sprite_style, 'sprite_size': sprite_size, 'sprite_ledger': sprite_ledger,
            'ground_ledger': ground_ledger, 'ledger_src': ledger_src,
            'ledger_n': len(ledger['file']) if ledger else 0, 'cache': cache}


def apply_exemptions(audits: list, cfg: dict) -> int:
    """Findings that are right as drawn, each with its reason (art/world-audit-regions.json,
    "exempt": [{"region", "check", "rect": [x, y, w, h] in region px, "why"}])."""
    n = 0
    for e in cfg.get('exempt', []):
        for A in audits:
            if A.R.id != e['region']:
                continue
            x, y, w, h = e['rect']
            ox, oy = A.R.origin
            for cy, cx in A.cells_of_box(x - ox, y - oy, w, h):
                for c in ([e['check']] if e['check'] != '*' else CHECK_IDS):
                    if A.status[c][cy, cx] > PASS:
                        A.status[c][cy, cx] = PASS
                        n += 1
            A.settle()
    return n


# --------------------------------------------------------------------------------------------
# roll-ups, report, images

def tally(worst: np.ndarray) -> dict:
    v = worst[worst != NA]
    n = int(v.size)
    g, a, r = int((v == PASS).sum()), int((v == AMBER).sum()), int((v == RED).sum())
    return {'cells': n, 'green': g, 'amber': a, 'red': r,
            'compliant_pct': round(100 * g / n, 1) if n else None,
            'red_pct': round(100 * r / n, 1) if n else None}


def problems(A: Audit) -> list:
    """Failing cells grouped into problems: connected cells failing one check in one place."""
    out = []
    R = A.R
    nred = np.stack([A.status[c] == RED for c in CHECK_IDS if c != 'ledger']).sum(0)
    for c in CHECK_IDS:
        s = A.status[c]
        for sev in (RED, AMBER):
            m = (s == sev)
            if not m.any():
                continue
            seen = np.zeros_like(m)
            for y0, x0 in zip(*np.nonzero(m)):
                if seen[y0, x0]:
                    continue
                pl = A.place[y0, x0]
                stack, comp = [(y0, x0)], []
                seen[y0, x0] = True
                while stack:
                    y, x = stack.pop()
                    comp.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < A.ny and 0 <= xx < A.nx and m[yy, xx] and not seen[yy, xx] and A.place[yy, xx] == pl:
                            seen[yy, xx] = True
                            stack.append((yy, xx))
                ys, xs = [p[0] for p in comp], [p[1] for p in comp]
                whys = {}
                for p in comp:
                    w = A.why.get((c, p[0], p[1]))
                    if w:
                        whys[w] = whys.get(w, 0) + 1
                top = sorted(whys.items(), key=lambda kv: -kv[1])[:3]
                ox, oy = R.origin
                box = [int(min(xs) * CELL + ox), int(min(ys) * CELL + oy), int((max(xs) - min(xs) + 1) * CELL),
                       int((max(ys) - min(ys) + 1) * CELL)]
                place = R.places[pl] if pl >= 0 else None
                out.append({'region': R.id, 'place': place.id if place else None, 'lane': place.lane if place else '?',
                            'scenery': bool(place and place.kind == 'scenery'),
                            'check': c, 'severity': 'red' if sev == RED else 'amber', 'cells': len(comp),
                            'box_region_px': box,
                            'box_place_px': ([box[0] - ox - place.rect[0], box[1] - oy - place.rect[1], box[2], box[3]]
                                             if place else None),
                            'tile': [math.floor(box[0] / TILE), math.floor(box[1] / TILE)],
                            'why': [f'{w} ({n})' for w, n in top],
                            'reds_per_cell': round(float(np.mean([nred[p] for p in comp])), 2),
                            '_canvas': (min(xs), min(ys), max(xs), max(ys))})
    return out


def report(audits: list, ctx: dict, cfg: dict, source: str, timing: dict, exempted: int) -> dict:
    regions, lanes, places, tiles, checks = {}, {}, {}, {}, {}
    lane_cells: dict = {}
    for A in audits:
        R = A.R
        dr = tally(A.drawn)
        regions[R.id] = {**tally(A.worst), 'drawn_compliant_pct': dr['compliant_pct'], 'drawn_red_pct': dr['red_pct'],
                         'status': cfg['regions'].get(R.id, 'old'), 'plane': R.plane,
                         'tier_map': bool((R.tiers != 255).any()), 'notes': R.tier_note}
        for i, pl in enumerate(R.places):
            m = A.place == i
            t = tally(np.where(m, A.worst, NA))
            dr = tally(np.where(m, A.drawn, NA))
            places[f'{R.id}/{pl.id}'] = {**t, 'drawn_compliant_pct': dr['compliant_pct'], 'kind': pl.kind, 'lane': pl.lane, 'module': pl.module}
            lane_cells.setdefault(pl.lane + (' scenery' if pl.kind == 'scenery' else ''), []).append((A.worst[m], A.drawn[m]))
        for (col, row, x0, y0, x1, y1) in tiles_of(R):
            t = tally(A.worst[y0 // CELL:(y1 + CELL - 1) // CELL, x0 // CELL:(x1 + CELL - 1) // CELL])
            if t['cells']:
                tiles[f'{R.id}:{col},{row}'] = t['compliant_pct']
        for c in CHECK_IDS:
            s = A.status[c][A.art]
            d = checks.setdefault(c, {'family': CHECKS[c][0], 'rule': CHECKS[c][1], 'measured': 0, 'amber': 0, 'red': 0})
            d['measured'] += int((s != NA).sum())
            d['amber'] += int((s == AMBER).sum())
            d['red'] += int((s == RED).sum())
    for lane, arrs in sorted(lane_cells.items()):
        dr = tally(np.concatenate([b.ravel() for _a, b in arrs]))
        lanes[lane] = {**tally(np.concatenate([a.ravel() for a, _b in arrs])),
                       'drawn_compliant_pct': dr['compliant_pct'], 'drawn_red_pct': dr['red_pct']}
    # sprites by owning lane (size guide lanes)
    guide = ctx['guide']
    sprite_rows = {}
    for A in audits:
        for p in A.R.props:
            b = re.sub(r'_f\d+$', '', p['sprite'])
            if b in sprite_rows:
                sprite_rows[b]['placed'] += 1
                continue
            entry = guide['sprites'].get(b) or [None, None]
            st, sz, lg = ctx['sprite_style'](p), ctx['sprite_size'](p), ctx['sprite_ledger'](p)
            sprite_rows[b] = {'lane': guide['lanes'].get(entry[1], '?') if entry[1] else '?', 'module': entry[1],
                              'kind': entry[0], 'placed': 1, 'style': st[1] or 'ok', 'size': sz[1] or ('ok' if sz[0] == PASS else '-'),
                              'ledger': lg[1] or 'KEEP',
                              'worst': max(st[0], sz[0], lg[0])}
    prop_lanes = {}
    for b, r in sprite_rows.items():
        d = prop_lanes.setdefault(r['lane'], {'sprites': 0, 'green': 0, 'amber': 0, 'red': 0})
        d['sprites'] += 1
        d['green' if r['worst'] <= PASS else 'amber' if r['worst'] == AMBER else 'red'] += 1
    for d in prop_lanes.values():
        d['compliant_pct'] = round(100 * d['green'] / d['sprites'], 1) if d['sprites'] else None
    probs = [p for A in audits for p in problems(A)]
    weight = {'red': 3, 'amber': 1}
    # walked places first: a problem past the world (scenery) weighs half
    # (ties: the place failing more checks per cell first)
    probs.sort(key=lambda p: (-weight[p['severity']] * p['cells'] * (0.5 if p['scenery'] else 1), -p['reds_per_cell'],
                              p['region'], p['check']))
    # the ten worst drawing faults: the largest red problems, at most two per check and three
    # per region so the list shows the spread (the ledger and the palette grade pictures, not
    # a drawing fault in a place)
    worst, per_check, per_place, per_region = [], {}, set(), {}
    for p in probs:
        if p['severity'] != 'red' or p['check'] in ('ledger', 'palette'):
            continue
        if per_check.get(p['check'], 0) >= 2 or (p['place'], p['check']) in per_place \
                or per_region.get(p['region'], 0) >= 3:
            continue
        per_check[p['check']] = per_check.get(p['check'], 0) + 1
        per_region[p['region']] = per_region.get(p['region'], 0) + 1
        per_place.add((p['place'], p['check']))
        worst.append(p)
        if len(worst) == 10:
            break
    total = tally(np.concatenate([A.worst.ravel() for A in audits]))
    dr = tally(np.concatenate([A.drawn.ravel() for A in audits]))
    total.update(drawn_compliant_pct=dr['compliant_pct'], drawn_red_pct=dr['red_pct'], drawn_amber=dr['amber'])
    gate = [r for r, v in regions.items() if v['status'] == 'rebuilt' and v['green'] != v['cells']]
    clean = lambda p: {k: v for k, v in p.items() if not k.startswith('_')}  # noqa: E731
    return {
        'about': ('The whole-world audit (scripts/art/world_audit.py, docs/vision/world-audit.md): every 32 px cell '
                  'of the world against the standards; a cell is green when every check measured there passes, amber '
                  'on a soft finding (judged by eye, or pending a decision), red when it fails the standard. '
                  'Regenerate with python3 scripts/art/world_audit.py.'),
        'source': source,
        'ledger': ctx['ledger_src'] or None,
        'world': total,
        'regions': regions,
        'lanes': lanes,
        'prop_lanes': prop_lanes,
        'checks': checks,
        'places': places,
        'tiles': tiles,
        'worst': [clean(p) for p in worst],
        'top_failures': [clean(p) for p in probs[:60]],
        'sprites_failing': {b: {k: v for k, v in r.items() if k != 'worst'} for b, r in sorted(sprite_rows.items())
                            if r['worst'] >= AMBER},
        'gate': {'rebuilt': [r for r, v in regions.items() if v['status'] == 'rebuilt'], 'failing': gate},
        'exempted_cells': exempted,
        'seconds': {k: round(v, 1) for k, v in timing.items()},
        '_problems': probs,
    }


def _plain(o):
    return o.item() if hasattr(o, 'item') else str(o)


COL = {PASS: (64, 176, 96), AMBER: (232, 170, 40), RED: (214, 52, 52)}


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


REDS = ((242, 128, 112), (214, 52, 52), (160, 24, 40), (100, 8, 34))   # 1, 2, 3, 4 or more red checks


def heat(A: Audit, art_alpha: float = 0.35, cell: int = CELL, drawn: bool = False) -> Image.Image:
    """The region's art, dimmed, under a colour per cell: green, amber, or a red that darkens
    with the number of checks the cell fails (1, 2, 3, 4 or more); places outlined and labelled.
    `drawn` leaves the ledger out (the drawing alone)."""
    R = A.R
    worst = A.drawn if drawn else A.worst
    checks = [c for c in CHECK_IDS if not (drawn and c == 'ledger')]
    nred = np.stack([A.status[c] == RED for c in checks]).sum(0)
    base = Image.fromarray(A.comp).convert('RGB')
    grey = np.asarray(base.convert('L').convert('RGB')).astype(np.float32)
    over = np.zeros((A.ny, A.nx, 3), np.float32)
    known = worst != NA
    over[worst == PASS] = COL[PASS]
    over[worst == AMBER] = COL[AMBER]
    for i, c in enumerate(REDS):
        over[(worst == RED) & (np.minimum(nred, 4) == i + 1)] = c
    over = np.repeat(np.repeat(over, CELL, 0), CELL, 1)
    kn = np.repeat(np.repeat(known, CELL, 0), CELL, 1)[..., None]
    img = np.where(kn, grey * art_alpha + over * (1 - art_alpha), grey * 0.25 + 20)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if cell != CELL:
        im = im.resize((R.w * cell // CELL, R.h * cell // CELL), Image.NEAREST)
    d = ImageDraw.Draw(im)
    f = cell / CELL
    for i, pl in enumerate(R.places):
        x, y, w, h = (int(v * f) for v in pl.rect)
        if pl.kind == 'scenery':
            d.rectangle([x, y, x + w - 1, y + h - 1], outline=(90, 90, 110))
            continue
        d.rectangle([x, y, x + w - 1, y + h - 1], outline=(250, 250, 250), width=2)
        t = tally(np.where(A.place == i, worst, NA))
        d.text((x + 6, y + 4), f'{pl.id} ({pl.lane})', fill=(255, 255, 255), font=_font(max(11, int(22 * f))),
               stroke_width=2, stroke_fill=(0, 0, 0))
        if t['cells']:
            d.text((x + 6, y + 6 + max(11, int(22 * f))), f"{t['compliant_pct']:.0f} % green", fill=(255, 255, 255),
                   font=_font(max(10, int(16 * f))), stroke_width=2, stroke_fill=(0, 0, 0))
    return im


def write_images(audits: list, rep: dict, out: str):
    os.makedirs(out, exist_ok=True)
    rdir = os.path.join(out, 'regions')
    os.makedirs(rdir, exist_ok=True)
    half = 16
    for A in audits:
        # the region sheet: the art at 1x beside its heat map at 1x
        art = Image.fromarray(A.comp).convert('RGB')
        hm = heat(A, drawn=True)
        sheet = Image.new('RGB', (art.width * 2 + 24, art.height + 70), (24, 22, 28))
        sheet.paste(art, (0, 70))
        sheet.paste(hm, (art.width + 24, 70))
        t = rep['regions'][A.R.id]
        d = ImageDraw.Draw(sheet)
        d.text((8, 8), f"{A.R.id}: {t['compliant_pct']} % green with every check, {t['drawn_compliant_pct']} % for the "
               f"drawing alone ({t['drawn_red_pct']} % red) of {t['cells']} cells", fill=(255, 255, 255), font=_font(26))
        d.text((8, 42), 'left: the art (ground and props, 1x); right: each 32 px cell by its worst check except the '
               'asset ledger, red darker the more checks fail', fill=(200, 200, 200), font=_font(18))
        sheet.save(os.path.join(rdir, f'{A.R.id}.png'), optimize=True)
        # every check on its own: a small map per check, 4 px a cell
        k = 4
        mw, mh = A.nx * k, A.ny * k
        cols = len(CHECK_IDS)
        ch = Image.new('RGB', (cols * (mw + 12) + 12, mh + 64), (24, 22, 28))
        dc = ImageDraw.Draw(ch)
        for i, c in enumerate(CHECK_IDS):
            arr = np.full((A.ny, A.nx, 3), 40, np.uint8)
            arr[A.art] = (70, 70, 80)
            for v, colr in COL.items():
                arr[(A.status[c] == v) & A.art] = colr
            im = Image.fromarray(np.repeat(np.repeat(arr, k, 0), k, 1))
            X = 12 + i * (mw + 12)
            ch.paste(im, (X, 52))
            dc.text((X, 6), c, fill=(255, 255, 255), font=_font(13))
            dc.text((X, 26), CHECKS[c][0], fill=(180, 180, 190), font=_font(11))
        ch.save(os.path.join(rdir, f'{A.R.id}-checks.png'), optimize=True)
    # the whole world: every region in a row at half scale, labelled; once with every check,
    # once for the drawing alone (the ledger left out)
    for drawn, name in ((False, 'world-audit.png'), (True, 'world-audit-drawing.png')):
        hs = [(A, heat(A, cell=half, drawn=drawn)) for A in audits]
        gap, top = 56, 170
        W = sum(h.width for _, h in hs) + gap * (len(hs) + 1)
        H = max(h.height for _, h in hs) + top + 80
        world = Image.new('RGB', (W, H), (18, 16, 22))
        d = ImageDraw.Draw(world)
        w0 = rep['world']
        pct = w0['drawn_compliant_pct'] if drawn else w0['compliant_pct']
        red = w0['drawn_red_pct'] if drawn else w0['red_pct']
        d.text((gap, 18), f"NapAttack world audit{', the drawing alone' if drawn else ''}: {pct} % of {w0['cells']} "
               f"cells green, {red} % red", fill=(255, 255, 255), font=_font(40))
        d.text((gap, 70), ('every 32 px cell coloured by its worst check' + (' except the asset ledger' if drawn else '')
                           + ': green passes every measured check, amber is a soft finding (by eye or pending a decision), '
                           'red fails the standard and darkens with the number of checks failed. Grey: no art.'),
               fill=(210, 210, 210), font=_font(22))
        x = gap
        for A, h in hs:
            t = rep['regions'][A.R.id]
            d.text((x, top - 58), A.R.id, fill=(255, 255, 255), font=_font(26))
            g_ = t['drawn_compliant_pct'] if drawn else t['compliant_pct']
            r_ = t['drawn_red_pct'] if drawn else t['red_pct']
            d.text((x, top - 28), f"{g_:.1f} % green, {r_:.0f} % red", fill=(220, 220, 220),
                   font=_font(18 if h.width >= 300 else 13))
            world.paste(h, (x, top))
            x += h.width + gap
        yk = H - 54
        keys = [(COL[PASS], 'green: passes'), (COL[AMBER], 'amber: soft')] + \
               [(c, f'red: fails {i + 1}{" or more" if i == 3 else ""} check{"s" if i else ""}') for i, c in enumerate(REDS)]
        for i, (c, lab) in enumerate(keys):
            d.rectangle([gap + i * 300, yk, gap + i * 300 + 28, yk + 28], fill=c)
            d.text((gap + i * 300 + 38, yk), lab, fill=(230, 230, 230), font=_font(22))
        world.save(os.path.join(out, name), optimize=True)
    # the worst problems, cropped at 3x with the failing cells outlined
    wdir = os.path.join(out, 'worst')
    os.makedirs(wdir, exist_ok=True)
    for f in os.listdir(wdir):
        os.remove(os.path.join(wdir, f))
    by = {A.R.id: A for A in audits}
    for n, p in enumerate(rep['_worst_full'], 1):
        A = by[p['region']]
        x0, y0, x1, y1 = p['_canvas']
        pad = 2
        cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
        cx1, cy1 = min(A.nx - 1, x1 + pad), min(A.ny - 1, y1 + pad)
        if (cx1 - cx0 + 1) * CELL > 640:
            cx1 = cx0 + 640 // CELL - 1
        if (cy1 - cy0 + 1) * CELL > 640:
            cy1 = cy0 + 640 // CELL - 1
        box = (cx0 * CELL, cy0 * CELL, (cx1 + 1) * CELL, (cy1 + 1) * CELL)
        crop = Image.fromarray(A.comp).convert('RGB').crop(box).resize(((box[2] - box[0]) * 3, (box[3] - box[1]) * 3), Image.NEAREST)
        d = ImageDraw.Draw(crop)
        m = A.status[p['check']] == RED
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                if m[cy, cx] and A.place[cy, cx] == A.place[y0, x0]:
                    X, Y = (cx * CELL - box[0]) * 3, (cy * CELL - box[1]) * 3
                    d.rectangle([X, Y, X + CELL * 3 - 1, Y + CELL * 3 - 1], outline=(255, 40, 40), width=2)
        cap = Image.new('RGB', (max(crop.width, 900), crop.height + 96), (24, 22, 28))
        cap.paste(crop, (0, 96))
        dd = ImageDraw.Draw(cap)
        dd.text((8, 6), f"{n}. {p['check']} in {p['region']}/{p['place']} (lane {p['lane']}): {p['cells']} cells, "
                f"region px {p['box_region_px']}", fill=(255, 255, 255), font=_font(20))
        for i, w in enumerate(p['why'][:2]):
            dd.text((8, 34 + i * 26), w[:110], fill=(230, 200, 200), font=_font(17))
        cap.save(os.path.join(wdir, f"{n:02d}-{p['region']}-{p['place']}-{p['check']}.png".replace(':', '_').replace(',', '_')))


# --------------------------------------------------------------------------------------------

def selftest(root: str) -> list:
    """The checks on a made-up region whose faults are known (nothing read from the world):
    each check must fire where the fault is and stay quiet where the drawing is right."""
    R = Region('selftest', 'continent', 2 * ZW, ZH, (0, 0))
    R.add_place(Place('a', 'zone', 'selftest', 'valley_zones', (0, 0, ZW, ZH), (0, 0)))
    R.add_place(Place('b', 'zone', 'selftest', 'valley_zones', (ZW, 0, ZW, ZH), (1, 0)))
    R.ground[:, :ZW] = (126, 159, 80, 255)          # flat lawn: too little detail
    R.ground[:, ZW:] = (84, 120, 60, 255)           # a different lawn: a cut at x 320
    R.terrain[:] = GROUND
    R.walk[:] = True
    t = R.terrain
    # place a: a pool whose west bank is a single-cell staircase (off the soft grid) and whose
    # north bank runs straight for 200 px (no jog) on a line off the 8 px grid (y 100: 4 * 25)
    for i in range(20):
        t[25 + i, 10 + i:40] = WATER
    t[25:60, 10:60] = np.where(t[25:60, 10:60] == WATER, WATER, t[25:60, 10:60])
    t[25:45, 30:60] = WATER
    R.walk[t == WATER] = False
    # place b: tier 1 at the top with a 32 px face (8 rows) below it on the west, a 20 px face on
    # the east, then tier 0; and a tier 1 block meeting tier 0 sideways with no side band
    tv = np.full(t.shape, 255, np.uint8)
    tb = tv[:, 80:]
    tb[:] = ord('0')
    tb[0:40, 0:40] = ord('1')
    tb[40:48, 0:20] = ord('f')                       # 32 px: right
    tb[40:45, 20:40] = ord('f')                      # 20 px: wrong
    tb[45:48, 20:40] = ord('0')
    tb[100:110, 0:10] = ord('1')                     # a tier ending east with no side band
    R.tiers = tv
    R.walk[:, 80:][tb == ord('f')] = False
    ctx = make_context(root, None)
    ctx['source'], ctx['root'] = 'zones', root
    A = Audit(R, ctx).run()
    fails = []

    def expect(check, cy, cx, want, why):
        got = A.status[check][cy, cx]
        if (got == RED) != want:
            fails.append(f'{check} at cell ({cx}, {cy}): {"expected a finding" if want else "expected none"} ({why})')

    expect('detail', 15, 2, True, 'flat lawn')
    expect('grid-edges', 30 * WALK // CELL, 12 * WALK // CELL, True, 'a staircase of 4 px steps')
    expect('straight-run', 25 * WALK // CELL, 45 * WALK // CELL, True, 'the pool\'s north bank runs 200 px with no jog')
    expect('straight-run', 15, 2, False, 'open lawn, no boundary')
    expect('rim-on-grid', 25 * WALK // CELL, 45 * WALK // CELL, True, 'a straight bank on y 100, off the 8 px lines')
    expect('seam', 5, 9, True, 'two lawns cut at the zone edge')
    expect('seam', 5, 4, False, 'inside one lawn')
    expect('face-height', 40 * WALK // CELL, (80 + 5) * WALK // CELL, False, 'a 32 px face')
    expect('face-height', 40 * WALK // CELL, (80 + 30) * WALK // CELL, True, 'a 20 px face')
    expect('side-band', 100 * WALK // CELL, (80 + 9) * WALK // CELL, True, 'a tier ends east with no side band')
    expect('tier-step', 100 * WALK // CELL, (80 + 9) * WALK // CELL, True, 'walkable tiers meet with no stair')
    expect('palette', 15, 2, False, 'palette findings are amber, never red')
    # a painted chunk (two areas of one picture): its own area line is no seam, and a side band
    # ('b') that meets a 32 px face at a jog in the tier's side passes every tier check
    R2 = Region('selftest-painted', 'continent', 2 * ZW, ZH, (0, 0))
    R2.add_place(Place('p1', 'area', 'selftest-painted', 'painted', (0, 0, ZW, ZH), painted=True))
    R2.add_place(Place('p2', 'area', 'selftest-painted', 'painted', (ZW, 0, ZW, ZH), painted=True))
    R2.ground[:, :ZW] = (126, 159, 80, 255)
    R2.ground[:, ZW:] = (84, 120, 60, 255)
    R2.terrain[:] = GROUND
    R2.walk[:] = True
    tv2 = np.full(R2.terrain.shape, ord('0'), np.uint8)
    tv2[0:40, 0:40] = ord('1')
    tv2[0:40, 40:42] = ord('b')                      # the band down the tier's east side
    tv2[40:48, 0:20] = ord('1')
    tv2[40:48, 20:42] = ord('f')                     # a 32 px face under the jog's rim
    tv2[48:100, 0:20] = ord('1')
    tv2[48:100, 20:22] = ord('b')                    # the band carries on below the face
    R2.tiers = tv2
    R2.walk[(tv2 == ord('f')) | (tv2 == ord('b'))] = False
    A2 = Audit(R2, ctx).run()

    def expect2(check, cy, cx, want, why):
        got = A2.status[check][cy, cx]
        if (got == RED) != want:
            fails.append(f'{check} at cell ({cx}, {cy}) of the painted chunk: '
                         f'{"expected a finding" if want else "expected none"} ({why})')
    expect2('seam', 5, 9, False, 'the line between two areas of one painted chunk')
    expect2('face-height', 40 * WALK // CELL, 30 * WALK // CELL, False, 'a 32 px face beside a side band')
    expect2('face-height', 60 * WALK // CELL, 20 * WALK // CELL, False, 'a side band below a face is no face')
    expect2('north-face', 48 * WALK // CELL, 20 * WALK // CELL, False, 'a band starting under a face')
    expect2('side-band', 20 * WALK // CELL, 40 * WALK // CELL, False, 'tiers apart with a band between')
    expect2('side-band', 70 * WALK // CELL, 20 * WALK // CELL, False, 'tiers apart with a band between, lower')
    expect2('tier-step', 20 * WALK // CELL, 40 * WALK // CELL, False, 'a band blocks the walk sideways')
    # the vectorised bar against detail_bar itself, on a real ground
    g = np.asarray(Image.open(os.path.join(root, 'assets', 'zones', 'town', 'ground.png')).convert('RGB'))
    g = g[::max(1, g.shape[1] // ZW), ::max(1, g.shape[1] // ZW)][:ZH, :ZW]
    box = (32, 288, 130, 386)
    ref = detail_bar.bar('ground')
    shot = detail_bar.through_jpeg(Image.fromarray(np.ascontiguousarray(g[box[1]:box[3], box[0]:box[2]])), ref['adult_px'], ref['jpeg_quality'])
    want = detail_bar.counts(detail_bar.to_scale(shot, ref['adult_px']))
    mine = pipe_keys(g[box[1]:box[3], box[0]:box[2]], ref['adult_px'], ref['jpeg_quality'])
    k = detail_bar.to_scale(shot, ref['adult_px'])
    hh, ww = min(mine.shape[0], k.shape[0]), min(mine.shape[1], k.shape[1])
    if not np.array_equal(mine[:hh, :ww], k[:hh, :ww]):
        fails.append('pipe_keys differs from detail_bar.to_scale')
    pc = patch_counts(mine[:hh, :ww])
    for m in ('tones', 'shapes', 'dressing', 'isolated', 'cluster'):
        if abs(float(np.mean(pc[m])) - want[m]) > 0.01:
            fails.append(f'patch_counts {m} {float(np.mean(pc[m])):.3f} against detail_bar {want[m]}')
    summary = markdown_summary({
        'world': {'cells': 2, 'compliant_pct': 50, 'amber': 0, 'red': 1},
        'regions': {
            'a|b': {'status': 'rebuilt', 'compliant_pct': 50, 'red_pct': 50, 'cells': 2,
                    'drawn_compliant_pct': 100, 'drawn_red_pct': 0},
        },
        'gate': {'rebuilt': ['a|b'], 'failing': ['a|b']},
    }, 'zones', previews='cached')
    if '| a\\|b | rebuilt | FAIL |' not in summary or 'Previews: cached.' not in summary:
        fails.append('the CI Markdown summary does not preserve region rows and preview state')
    return fails


def markdown_summary(rep: dict, source: str, previews: str) -> str:
    """Compact GitHub summary, written before gate failure so every region stays visible."""
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')

    rebuilt = set(rep.get('gate', {}).get('rebuilt', []))
    failing = set(rep.get('gate', {}).get('failing', []))
    rows = []
    for region, value in rep['regions'].items():
        gate = 'FAIL' if region in failing else 'PASS' if region in rebuilt else 'not gated'
        rows.append(
            f"| {cell(region)} | {cell(value['status'])} | {gate} | {value['compliant_pct']}% | "
            f"{value['red_pct']}% | {value['drawn_compliant_pct']}% | {value['drawn_red_pct']}% | "
            f"{value['cells']} |"
        )
    world = rep['world']
    return '\n'.join([
        '# Whole-world compliance audit',
        '',
        f"Source: `{cell(source)}`. Every region was audited; only regions marked `rebuilt` are blocking. Previews: {cell(previews)}.",
        '',
        f"World: **{world['compliant_pct']}% green**, {world['red']} red and {world['amber']} amber cells out of {world['cells']}.",
        '',
        '| Region | Status | Gate | Green | Red | Drawing green | Drawing red | Cells |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |',
        *rows,
        '',
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--source', choices=('zones', 'world'))
    ap.add_argument('--region', action='append', help='only this region (repeatable)')
    ap.add_argument('--out', default=os.environ.get('WORLD_AUDIT_OUT')
                    or os.path.join(tempfile.gettempdir(), 'napattack-world-audit'))
    ap.add_argument('--json', default=None, help="the report (default art/world-audit.json; '-' skips it)")
    ap.add_argument('--cells', help='every cell of every region as JSON')
    ap.add_argument('--ledger')
    ap.add_argument('--config', default=None)
    ap.add_argument('--no-images', action='store_true',
                    default=os.environ.get('WORLD_AUDIT_NO_IMAGES') == '1')
    ap.add_argument('--gate', action='store_true', help='fail if a region marked rebuilt is not 100 %% green')
    ap.add_argument('--selftest', action='store_true', help='run the checks on a made-up region with known faults')
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    if args.selftest or args.gate:
        fails = selftest(root)
        for f in fails:
            print('world audit self-test:', f)
        if fails:
            return 1
        print('world audit self-test: every check fires on its known fault and stays quiet where the drawing is right')
        if args.selftest:
            return 0
    cfg_path = args.config or os.path.join(root, 'art', 'world-audit-regions.json')
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {'regions': {}}
    source = args.source or os.environ.get('WORLD_AUDIT_SOURCE') or 'zones'
    only = set(args.region) if args.region else None
    if args.gate:
        rebuilt = {r for r, s in cfg['regions'].items() if s == 'rebuilt'}
        if not rebuilt:
            print('world audit gate: no region is marked "rebuilt"; auditing every region for the report')
        elif only:
            only &= rebuilt
    t0 = time.time()
    regions = load_world(root, only) if source == 'world' else load_zones(root, only)
    ctx = make_context(root, args.ledger)
    ctx['source'] = source
    ctx['root'] = root
    timing = {'load': time.time() - t0}
    audits = []
    for R in regions:
        t = time.time()
        audits.append(Audit(R, ctx).run(timing))
        print(f'world audit: {R.id} audited in {time.time() - t:.1f} s', flush=True)
    exempted = apply_exemptions(audits, cfg)
    rep = report(audits, ctx, cfg, source, timing, exempted)
    full = [p for p in rep['_problems'] if any(p['region'] == w['region'] and p['place'] == w['place']
                                                 and p['check'] == w['check'] and p['box_region_px'] == w['box_region_px']
                                                 for w in rep['worst'])]
    rep['_worst_full'] = full
    if not args.no_images:
        write_images(audits, rep, args.out)
    if args.cells:
        cells = []
        for A in audits:
            ox, oy = A.R.origin
            for cy, cx in zip(*np.nonzero(A.worst != NA)):
                cells.append({'region': A.R.id, 'x': int(cx * CELL + ox), 'y': int(cy * CELL + oy),
                              'place': A.R.places[A.place[cy, cx]].id if A.place[cy, cx] >= 0 else None,
                              'kind': A.kind[cy, cx], 'worst': int(A.worst[cy, cx]),
                              'fails': {c: A.why.get((c, cy, cx), '') for c in CHECK_IDS if A.status[c][cy, cx] > PASS}})
        with open(args.cells, 'w') as f:
            json.dump(cells, f, default=_plain)
    out_json = args.json or (None if (only and not args.gate) else os.path.join(root, 'art', 'world-audit.json'))
    pub = {k: v for k, v in rep.items() if not k.startswith('_')}
    if args.gate:
        out_json = None
    if out_json and out_json != '-':
        with open(out_json, 'w') as f:
            json.dump(pub, f, indent=1, default=_plain)
            f.write('\n')
    w = rep['world']
    print(f"world audit ({source}): {w['cells']} cells, {w['compliant_pct']} % green, {w['amber']} amber, {w['red']} red")
    for r, v in rep['regions'].items():
        print(f"  {r:8s} {v['status']:8s} {v['compliant_pct']:5.1f} % green  {v['red_pct']:5.1f} % red  ({v['cells']} cells; "
              f"drawing alone {v['drawn_compliant_pct']} % green, {v['drawn_red_pct']} % red)")
    for lane, v in rep['lanes'].items():
        print(f"  lane {lane}: {v['compliant_pct']} % green, {v['red_pct']} % red of {v['cells']} cells "
              f"(drawing alone {v['drawn_compliant_pct']} % green, {v['drawn_red_pct']} % red)")
    for c, v in rep['checks'].items():
        print(f"  {c:14s} measured {v['measured']:6d}  red {v['red']:6d}  amber {v['amber']:6d}")
    if not args.no_images:
        print(f'  images: {os.path.join(args.out, "world-audit.png")}, {os.path.join(args.out, "regions")}/, '
              f'{os.path.join(args.out, "worst")}/')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        previews = 'not rendered' if args.no_images else 'generated for these inputs'
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write(markdown_summary(rep, source, previews) + '\n')
    if args.gate:
        bad = rep['gate']['failing']
        if bad:
            for r in bad:
                v = rep['regions'][r]
                print(f'world audit gate: {r} is marked rebuilt but only {v["compliant_pct"]} % of its cells are green '
                      f'({v["amber"]} amber, {v["red"]} red)')
                for p in [p for p in rep['_problems'] if p['region'] == r][:12]:
                    print(f"  {p['severity']:5s} {p['check']:13s} {p['place']}: {p['cells']} cells at region px "
                          f"{p['box_region_px']}: {'; '.join(p['why'][:1])}")
            return 1
        if rep['gate']['rebuilt']:
            print('world audit gate: every rebuilt region is 100 % green')
        else:
            print('world audit gate: no region is rebuilt yet; report only')
    return 0


if __name__ == '__main__':
    sys.exit(main())
