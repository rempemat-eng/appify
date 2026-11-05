"""The coast kit: the pieces every shore of the world is painted with.

Claude C's lane (the Tidebloom Isles, Neon Harbour and its coast, Gullwick and Lullford;
docs/vision/rebuild-plan.md, section 3: "Coast kit: sea cliffs, beaches, shingle, rock
pools, surf, harbours' sea walls"). Nothing in the game reads it yet: it proves the look
before a region is rebuilt from it, as the river kit (#133), the dry kit (#137) and the
mountain kit (#148) do. No old asset is reused (AGENTS.md): every picture here is new.

How it is built (Claude A's lesson from the mountain pilot, crew board to-all-kits-organic):
the soft grid fixes face heights (32 px tiers, south faces only, 5 px side bands, 8 px
shadows), not plan shapes. Shorelines, tier outlines and the sea's depth bands are
organic (curving, lobed, with spurs and bays), kept on the 8 px grid only as stepped runs
and 45 degree diagonals; nothing is a rectangle with chamfered corners and no face runs
straight across a screen. Cliffs are a hand-drawn tileset laid by an autotiler, the way
Sea of Stars and Eastward build them:

- The tileset is data, in `coast_tiles.py`: rock columns 10 to 24 px wide, each a stack of
  rounded stones (Sea of Stars' pillow rock) in crowns, bodies and feet; lips (sea turf
  with thrift, a marram dune's sand lip, bare coping with lichen); side bands lit west and
  dark east with caps for the outer corners; feet on sand, shingle, rock and turf; thrift
  and campion hanging over the faces.
- The autotiler (`lattice`, `cliff_faces`, `lips`, `hangs`, `bands`, `feet`) lays them
  along the tiers' outlines: a dual-grid corner autotiler keeps every outline on the grid
  as runs and 45 degree diagonals; each column is stacked to its face's height from hashed
  pieces, each stone one of the cliff's rocks; a stretch of face turned west is lit and
  warm, one turned east shaded and cool. Variants are picked by hash, never the same one
  twice running.
- Where a face stands in the sea, `sea_foot` wets its lowest rows (a tone down), with
  barnacles above the tide line and weed below it, and the surf draws its foam.

The sea (`sea`, `surf`) is one calm plane in soft depth bands that follow the shore, as
Sea of Stars paints it: pale lagoon over sand at the edge, teal over the shelf, deep blue
beyond, with swell lines lying along the shore, the sand floor and stones showing through
the shallows, a white foam line hugging every shore with a second broken line of lace out
from it and a dark wet ring between, wet sand a tone down where the swash reaches. Moving
water comes from water_flow.py (`flow_frames`): glints on open water and foam lapping the
shore, recoloured onto the house ramps.

Everything is drawn in the house style (docs/vision/house-style.md): every pixel a tone of
a house ramp (art/house-palette.json) or a family's edge tone; shade and light move along
the ramps; texture comes in clusters of two to four pixels; light from the upper left;
cast shadows step the ground two tones down its own ramp (one on water).

Sizes follow docs/vision/size-guide.md and the Tidebloom brief (regions/tidebloom-isles.md,
section 4): an adult 25 px; tiers of 32 px; sea cliffs of 64 and 96 against beaches at sea
level; side bands 5; cast shadows 8; a cliff path 16 and ramps 24 along a face at 1 in 3
with a parapet; stairs 40 open between 4 px cheeks; a pier 32 wide on piles; a slipway 28
wide running at least 16 into the water; a quay's sea wall a tier of 32 in dressed courses.

The model is the mountain kit's (#148, head 6d46084): a `Plot` holds the house ramp and
tone of every pixel, pieces paint masks into it, standing things are `Sprite`s pasted with
an edge-tone outline and a cast shadow. The shared core (noise, the plot, clusters,
outline, shadow, sprites, the relief and its lattice, the ways up) is copied from it, so
the kits stay independent until scripts/art/kit_core.py lands.

The pieces (each with a seed, all deterministic):
- relief: `Relief`, `lattice()`, `cove_cells()`.
- cliffs: `cliff_faces()`, `lips()`, `hangs()`, `bands()`, `feet()`, `sea_foot()`,
  `tier_shadows()`.
- tops: `sea_turf()` (thrift, campion, short turf), `dune()` (marram on sand).
- shore: `beach()` (dry sand, wind ripples, the wrack line), `shingle()` (graded pebbles to
  a storm ridge), `platform()` (a wave-cut rock platform) with `rock_pools()`.
- water: `sea()` (depth bands, swell, the floor in the shallows), `surf()` (foam, lace, the
  wet ring, the swash on sand), `reef()` and `south_edge()` (the layered edge: shallows,
  the reef with its breakers, the deep, far isles in the haze).
- built: `quay()` (a harbour sea wall: dressed courses, coping, mooring rings, a ladder,
  weed and wet below the tide line; setts on top), `pier()` (a timber pier on piles),
  `slipway()` (setts on a ramp into the water between granite kerbs), `trail()`,
  `ramp_along()`, `stair()`.
- things: `boulder()`, `driftwood()`, `bollard()`.

Run:
    python3 scripts/art/coast_kit.py --check     (walk contracts; exits non-zero on a fault)
    python3 scripts/art/coast_kit.py [OUT_DIR]
writes OUT_DIR/cove.png (a cove under a cliff with a pier and a path down, 640 x 640 at
1x), cove-2x.png (with residents standing in it for scale), cove-night.png, cove-flow.gif
(the moving water), kit-sheet.png (every piece at 2x, labelled with its detail bar
result), tileset.png (the tileset at 5x), compare.png (cove crops beside Sea of Stars and
Eastward coast and water scenes at the same character height, when the screenshots are in
REF_DIR), and prints the bar for the measured boxes. Default OUT_DIR: napattack-coast-kit
in the system's temp folder, never the repository.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import house_palette as hp  # noqa: E402
import coast_tiles as tiles  # noqa: E402

PAL = hp.load()
RAMPS = PAL['ramps']
EDGES = PAL['edges']
NAMES = sorted(RAMPS) + ['ink']
IDX = {n: i for i, n in enumerate(NAMES)}
EDGE_T = 6                         # the tone index that means "this family's edge tone"
COL = np.zeros((len(NAMES), 7, 3), np.uint8)
for _n, _i in IDX.items():
    if _n == 'ink':
        COL[_i, :, :] = hp.hex_rgb(PAL['ink'])
        continue
    for _t, _c in enumerate(RAMPS[_n]):
        COL[_i, _t] = hp.hex_rgb(_c)
    COL[_i, EDGE_T] = hp.hex_rgb(EDGES.get(hp.family(_n), PAL['ink']))
FAMILY = np.array([IDX[hp.family(n)] if n != 'ink' else IDX['ink'] for n in NAMES])
WARM = np.array([IDX.get(f'{NAMES[FAMILY[i]]}_warm', FAMILY[i]) for i in range(len(NAMES))])
COOL = np.array([IDX.get(f'{NAMES[FAMILY[i]]}_cool', FAMILY[i]) for i in range(len(NAMES))])
GLOW = np.array([PAL['kinds'].get(n, '') == 'glow' for n in NAMES])

# The soft grid (verticality.md 4f; terrace.py; size guide 7)
GRID = 8
FACE = 32          # a tier's face
STRIP = 5          # a side band: 0.2 of an adult
SHADOW = 8         # a tier's cast shadow, whatever its height
THROW = 1.0        # sprites' shadows

# The cliffs' rocks: each stone of a column is one of these ramps (a coast of sandstone and
# grit, as at the Heights and Gullwick; the isles' cove is basalt)
SANDSTONE = ('bleached', 'bleached', 'bleached_warm', 'sand_cool', 'ashlar_warm')
BASALT = ('basalt', 'basalt', 'basalt_warm', 'stone_cool', 'slate_cool', 'basalt_cool')
ROCK = ('stone', 'stone_warm', 'stone_cool', 'ashlar', 'bleached_cool')   # loose stones


# --- the shared core (copied from the mountain kit, #148 head 6d46084) ---------------------------
def hash01(x, y, seed=0):
    """Hash noise in [0, 1) on integer coordinates (32-bit arithmetic; plain ints for a
    single point, which is far faster than numpy on scalars)."""
    if isinstance(x, (int, np.integer)) and isinstance(y, (int, np.integer)):
        h = (int(x) * 374761393 + int(y) * 668265263 + (seed * 2246822519 & 0xFFFFFFFF)) & 0xFFFFFFFF
        h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
        h = h ^ (h >> 16)
        return (h & 0xFFFFFF) / float(0x1000000)
    x = np.asarray(x)
    y = np.asarray(y)
    if x.dtype.kind == 'f':
        x = x.astype(np.int64)
    if y.dtype.kind == 'f':
        y = y.astype(np.int64)
    x = x.astype(np.uint32)
    y = y.astype(np.uint32)
    h = x * np.uint32(374761393) + y * np.uint32(668265263) + np.uint32(seed * 2246822519 & 0xFFFFFFFF)
    h = (h ^ (h >> np.uint32(13))) * np.uint32(1274126177)
    h = h ^ (h >> np.uint32(16))
    return (h & np.uint32(0xFFFFFF)) / float(0x1000000)


def vnoise(x, y, scale, seed=0):
    """Smooth value noise in [0, 1): lattice every `scale` px, smoothstep between."""
    gx, gy = np.asarray(x, np.float64) / scale, np.asarray(y, np.float64) / scale
    x0, y0 = np.floor(gx).astype(np.int64), np.floor(gy).astype(np.int64)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hash01(x0, y0, seed), hash01(x0 + 1, y0, seed)
    c, d = hash01(x0, y0 + 1, seed), hash01(x0 + 1, y0 + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, scale, seed=0, octaves=3):
    v, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        v = v + amp * vnoise(x, y, scale / 2 ** o, seed + 17 * o)
        tot += amp
        amp *= 0.5
    return v / tot


def shift(a, dx, dy, fill=0):
    """a moved by (dx, dy): out[y, x] = a[y - dy, x - dx]."""
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    if abs(dx) >= w or abs(dy) >= h:
        return out
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def dilate(m, r=1):
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o[1:] |= out[:-1]
        o[:-1] |= out[1:]
        o[:, 1:] |= out[:, :-1]
        o[:, :-1] |= out[:, 1:]
        out = o
    return out


def erode(m, r=1):
    return ~dilate(~m, r)


def blob(cx, cy, rx, ry, shape, seed=0, wob=0.18, lobes=7):
    """A soft natural shape: an ellipse with a wobbling rim (never a perfect ellipse)."""
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    ang = np.arctan2(v, u)
    r = 1 + wob * (0.6 * np.sin(ang * lobes + seed) + 0.4 * np.sin(ang * (lobes + 4) + seed * 1.7))
    return u * u + v * v <= r * r


def edge_dist(m, cap=12):
    """Px from each masked pixel to the mask's edge (1 on the edge), capped."""
    d = np.zeros(m.shape, int)
    cur = np.asarray(m, bool).copy()
    for i in range(cap):
        d[cur] = i + 1
        cur = erode(cur, 1)
        if not cur.any():
            break
    return d


class Plot:
    """A ground canvas as house ramp indices (f) and tones (t, 0..5, 6 the edge tone)."""

    def __init__(self, w, h, ramp='sand', tone=3):
        self.w, self.h = w, h
        self.f = np.full((h, w), IDX[ramp], np.int16)
        self.t = np.full((h, w), tone, np.int8)
        self.wet = np.zeros((h, w), bool)      # water surface (for water_flow)
        self.lava = np.zeros((h, w), bool)     # open lava and glowing cracks (water_flow's lava)
        self.solid = np.zeros((h, w), bool)    # what stands up (outlined, never re-textured)
        self.walk = np.ones((h, w), bool)      # walkable on foot
        # Barriers no ordinary paint may reopen (water, young lava): a stair, trail or wash
        # never makes them walkable; only an explicit crossing (a causeway) clears them.
        self.hazard = np.zeros((h, w), bool)
        self.tier = np.zeros((h, w), np.int8)  # the tier whose top is seen here (-1: a face)
        self.vents = []                        # (x, y, size) of steam sources
        self.y, self.x = np.mgrid[0:h, 0:w]

    def put(self, m, ramp, tone):
        m = np.asarray(m, bool)
        self.f[m] = IDX[ramp] if isinstance(ramp, str) else np.asarray(ramp)[m] if np.ndim(ramp) else ramp
        self.t[m] = tone if np.ndim(tone) == 0 else np.asarray(tone)[m]

    def step(self, m, k, lo=0, hi=5):
        """Move pixels k tones along their own ramp (never edge tones or glows)."""
        m = np.asarray(m, bool) & (self.t < EDGE_T) & ~GLOW[self.f]
        if np.ndim(k):
            k = np.asarray(k)[m]
        self.t[m] = np.clip(self.t[m] + k, lo, hi)

    def fam(self, name):
        return FAMILY[self.f] == IDX[name]

    def image(self, scale=1):
        rgb = COL[self.f, np.clip(self.t, 0, EDGE_T)]
        img = Image.fromarray(rgb, 'RGB')
        return img.resize((self.w * scale, self.h * scale), Image.NEAREST) if scale != 1 else img

    def mask(self):
        return np.ones((self.h, self.w), bool)

    def snap(self):
        return (self.f.copy(), self.t.copy(), self.solid.copy(), self.walk.copy(), self.hazard.copy())

    def restore(self, s, m=None):
        if m is None:
            self.f[:], self.t[:], self.solid[:], self.walk[:], self.hazard[:] = s
        else:
            for a, v in zip(('f', 't', 'solid', 'walk', 'hazard'), s):
                getattr(self, a)[m] = v[m]


# Cluster shapes: two to four pixels, never one (house rule 4).
DOMINOES = (((0, 0), (1, 0)), ((0, 0), (0, 1)))
SMALL = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)),
         ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1)))
FLAT = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1)))


def stamp(p: Plot, m, density, seed, shapes=SMALL, ramp=None, dt=0, swap=None, same_family=True,
          tone=None):
    """Clusters over a mask: at seeds (hash < density) each stamps one of `shapes` with the
    seed pixel's ramp moved `dt` tones, swapped to a sibling ('warm', 'cool', 'mix') or set
    to `ramp`/`tone`. With same_family, a cluster only covers pixels of the seed's family
    within one tone of it, so clusters stay inside their surface. Returns what changed."""
    m = np.asarray(m, bool)
    if np.ndim(density):
        seeds = m & (hash01(p.x, p.y, seed) < np.asarray(density))
    else:
        seeds = m & (hash01(p.x, p.y, seed) < density)
    k = (hash01(p.x, p.y, seed + 1) * len(shapes)).astype(int)
    if ramp is not None:
        nf = np.full(p.f.shape, IDX[ramp], np.int16) if isinstance(ramp, str) else np.asarray(ramp, np.int16)
    else:
        nf = p.f.copy()
        if swap == 'mix':
            r = hash01(p.x, p.y, seed + 2)
            nf = np.where(r < 0.5, WARM[nf], COOL[nf]).astype(np.int16)
            nf = np.where(nf == p.f, FAMILY[p.f], nf).astype(np.int16)
        elif swap:
            nf = (WARM if swap == 'warm' else COOL)[nf].astype(np.int16)
    if tone is not None:
        nt = np.full(p.t.shape, tone, np.int8) if np.ndim(tone) == 0 else np.asarray(tone, np.int8)
    else:
        nt = np.clip(p.t + (dt if np.ndim(dt) == 0 else np.asarray(dt)), 0, 5).astype(np.int8)
    seed_fam, seed_t = FAMILY[p.f], p.t.copy()
    changed = np.zeros(m.shape, bool)
    for i, shp in enumerate(shapes):
        s = seeds & (k == i)
        if not s.any():
            continue
        for dx, dy in shp:
            tgt = shift(s, dx, dy, False) & m & ~p.solid
            sf, st = shift(seed_fam, dx, dy, -1), shift(seed_t, dx, dy, -9)
            fnew, tnew = shift(nf, dx, dy, 0), shift(nt, dx, dy, 0)
            if same_family:
                tgt &= (FAMILY[p.f] == sf) & (np.abs(p.t - st) <= 1) & (p.t < EDGE_T)
            p.f[tgt], p.t[tgt] = fnew[tgt], tnew[tgt]
            changed |= tgt
    return changed


def despeckle(p: Plot, m=None, passes=2):
    """No lone pixels: a pixel unlike all four neighbours takes its neighbours' commonest
    colour, unless it is a deliberate glint (tone 5), an edge or a glow."""
    key = p.f.astype(np.int32) * 8 + p.t
    m = np.ones(key.shape, bool) if m is None else np.asarray(m, bool)
    m = m & ~p.solid
    for _ in range(passes):
        nb = [shift(key, dx, dy, -1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        lone = m & (p.t < 5) & ~GLOW[p.f] & np.all([key != n for n in nb], axis=0)
        if not lone.any():
            break
        pick = nb[1].copy()
        for i in range(4):
            for j in range(i + 1, 4):
                pick = np.where((nb[i] == nb[j]) & (nb[i] >= 0), nb[i], pick)
        pick = np.where(pick < 0, nb[0], pick)
        ok = lone & (pick >= 0)
        p.f[ok], p.t[ok] = pick[ok] // 8, pick[ok] % 8
        key = p.f.astype(np.int32) * 8 + p.t


def base(p: Plot, m, ramps, seed, scale=9.0, tone=3, light=0.70, dark=0.27):
    """Calm ground (house rule 8): broad soft patches of the given ramps (the first is the
    body; a list of (ramp, share)), at one tone, a tone lighter where the noise is high and
    a tone down where it is low. No specks."""
    m = np.asarray(m, bool)
    if isinstance(ramps, str):
        ramps = [(f'{ramps}_warm', 0.3), (ramps, 0.4), (f'{ramps}_cool', 0.3)]
    n = fbm(p.x, p.y, scale * 1.7, seed + 7)
    f = np.full(p.f.shape, IDX[ramps[0][0]], np.int16)
    if m.any():
        tot = sum(s for _r, s in ramps)
        cuts = np.quantile(n[m], np.cumsum([s / tot for _r, s in ramps])[:-1]) if len(ramps) > 1 else []
        for r, c in zip([r for r, _s in ramps[1:]], cuts):
            f = np.where(n >= c, IDX[r], f)
    p.f[m] = f[m]
    p.t[m] = tone
    pn = fbm(p.x, p.y, scale, seed)
    p.step(m & (pn > light), 1)
    p.step(m & (pn < dark), -1)
    despeckle(p, m)


def texture(p: Plot, m, seed, swaps=0.10, ups=0.025, downs=0.025, shapes=SMALL):
    """Many small shapes without value noise: clusters that swap to a sibling ramp at the
    same tone, and a few a tone up or down."""
    stamp(p, m, swaps, seed, shapes, swap='mix')
    stamp(p, m, ups, seed + 10, shapes, dt=1)
    stamp(p, m, downs, seed + 20, shapes, dt=-1)


def _pt(p, x, y):
    m = np.zeros((p.h, p.w), bool)
    if 0 <= x < p.w and 0 <= y < p.h:
        m[y, x] = True
    return m


def _scatter(m, every, seed, margin=4):
    """Deterministic points over a mask, about one per `every` px, never on its edge."""
    m = erode(np.asarray(m, bool), margin) if margin else np.asarray(m, bool)
    h, w = m.shape
    cell = max(3, int(math.sqrt(every)))
    gy, gx = np.mgrid[0:h:cell, 0:w:cell]
    x = gx + (hash01(gx, gy, seed) * cell).astype(int)
    y = gy + (hash01(gx, gy, seed + 1) * cell).astype(int)
    ok = (x < w) & (y < h)
    x, y = x[ok], y[ok]
    ok = m[y, x]
    return [(int(a), int(b)) for a, b in zip(x[ok], y[ok])]


def spline(pts, step=1.0):
    """A Catmull-Rom curve through the points, resampled every `step` px of arc."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    dense = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (np.array(P[j], float) for j in (i - 1, i, i + 1, i + 2))
        n = max(4, int(np.hypot(*(p2 - p1)) * 3))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            dense.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    dense.append(np.array(pts[-1], float))
    dense = np.array(dense)
    seg = np.hypot(*np.diff(dense, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    out_s = np.arange(0, s[-1], step)
    return np.stack([np.interp(out_s, s, dense[:, 0]), np.interp(out_s, s, dense[:, 1])], 1)


class Channel:
    """Coordinates along a line for every pixel near it: s (px along it from the first
    point), n (px across, positive on the right looking downstream), the direction there."""

    def __init__(self, p: Plot, pts, reach=60):
        c = spline(pts)
        d = np.gradient(c, axis=0)
        d /= np.maximum(1e-9, np.hypot(d[:, 0], d[:, 1]))[:, None]
        h, w = p.h, p.w
        best = np.full((h, w), 1e9)
        idx = np.zeros((h, w), np.int32)
        for i in range(0, len(c)):
            cx, cy = c[i]
            x0, x1 = max(0, int(cx - reach)), min(w, int(cx + reach) + 1)
            y0, y1 = max(0, int(cy - reach)), min(h, int(cy + reach) + 1)
            if x0 >= x1 or y0 >= y1:
                continue
            dd = (p.x[y0:y1, x0:x1] + 0.5 - cx) ** 2 + (p.y[y0:y1, x0:x1] + 0.5 - cy) ** 2
            sel = dd < best[y0:y1, x0:x1]
            best[y0:y1, x0:x1][sel] = dd[sel]
            idx[y0:y1, x0:x1][sel] = i
        self.near = best < reach * reach
        self.c, self.dir = c, d
        rx, ry = p.x + 0.5 - c[idx, 0], p.y + 0.5 - c[idx, 1]
        self.s = idx.astype(np.float64)
        self.n = rx * (-d[idx, 1]) + ry * d[idx, 0]
        self.d = np.where(self.near, np.sqrt(best), 1e9)
        self.tx, self.ty = d[idx, 0], d[idx, 1]
        self.length = len(c)

    def band(self, hw, wob=0.0, seed=0, scale=30):
        """The pixels within hw of the line, the edge wandering by up to `wob` px."""
        e = hw + wob * (fbm(self.s, np.sign(self.n), scale, seed) - 0.5) * 2 if wob else hw
        return self.near & (np.abs(self.n) <= e)


def outline_mask(p: Plot, m):
    """The house outline round a standing mass: one pixel outside it in the edge tone of the
    family it closes; on its lit top and west edges the line breaks to that ramp's tone 1."""
    ring = dilate(m, 1) & ~m & ~p.solid
    for dx, dy, lit in ((-1, 0, True), (0, -1, True), (1, 0, False), (0, 1, False)):
        src_f, src_t = shift(p.f, dx, dy, 0), shift(p.t, dx, dy, 0)
        sel = ring & shift(m, dx, dy, False)
        if lit:
            brk = sel & (src_t >= 4) & (src_t < EDGE_T)
            p.f[sel], p.t[sel] = src_f[sel], EDGE_T
            p.f[brk], p.t[brk] = src_f[brk], 1
        else:
            p.f[sel], p.t[sel] = src_f[sel], EDGE_T
        ring &= ~sel
    return dilate(m, 1) & ~m


def cast(p: Plot, m, k=2):
    """A cast shadow: the ground steps k tones down its own ramp (house rule 6)."""
    m = np.asarray(m, bool) & ~p.solid
    p.step(m & ~p.wet & ~p.lava, -k, lo=0)
    p.step(m & p.wet, -1, lo=1)


class Sprite:
    """A small standing thing drawn on its own (ramp, tone and mask arrays), its foot at
    (fx, fy) in its own pixels."""

    def __init__(self, w, h, fx, fy):
        self.w, self.h, self.fx, self.fy = w, h, fx, fy
        self.f = np.zeros((h, w), np.int16)
        self.t = np.zeros((h, w), np.int8)
        self.m = np.zeros((h, w), bool)
        self.y, self.x = np.mgrid[0:h, 0:w]

    def put(self, sel, ramp, tone):
        sel = np.asarray(sel, bool)
        self.f[sel] = IDX[ramp] if isinstance(ramp, str) else np.asarray(ramp)[sel]
        self.t[sel] = tone if np.ndim(tone) == 0 else np.asarray(tone)[sel]
        self.m |= sel

    def px(self, x, y, ramp, tone):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.f[y, x] = IDX[ramp]
            self.t[y, x] = tone
            self.m[y, x] = True

    def step(self, sel, k, lo=0, hi=5):
        sel = np.asarray(sel, bool) & self.m
        self.t[sel] = np.clip(self.t[sel] + k, lo, hi)

    def blob_shadow(self, rx, ry=None, dx=None):
        """A round thing's shadow, thrown down and to the right of its foot."""
        ry = ry or max(2, rx * 0.35)
        dx = rx * 0.45 if dx is None else dx
        return blob(self.fx + dx, self.fy + ry * 0.35, rx, ry, self.m.shape, 3, wob=0.06)

    def thrown(self, k=0.55, foot_rows=None):
        """The silhouette thrown down and to the right (house rule 6): each row of the sprite
        at height z above the foot lands at (x + z * k, foot + z * k * 0.5), squashed."""
        sh = np.zeros(self.m.shape, bool)
        ys, xs = np.nonzero(self.m)
        if not len(ys):
            return sh
        z = self.fy - ys
        nx = np.clip((xs + z * k * THROW).astype(int), 0, self.w - 1)
        ny = np.clip((self.fy + z * k * 0.30).astype(int), 0, self.h - 1)
        sh[ny, nx] = True
        sh = erode(dilate(sh, 1), 1)
        return sh


def paste(p: Plot, sp: Sprite, x, y, outline=True, shadow=None, block=None, k=2):
    """Set a sprite with its foot at (x, y): its cast shadow first (the ground k tones down),
    then the sprite, then its outline in edge tones. `shadow` is a mask in the sprite's own
    pixels; `block` the pixels (sprite's own) that stop a walker (default: a 4 x 3 foot)."""
    ox, oy = x - sp.fx, y - sp.fy
    full = np.zeros(p.f.shape, bool)
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(sp.w, p.w - ox), min(sp.h, p.h - oy)
    if sx0 >= sx1 or sy0 >= sy1:
        return full
    sl = (slice(oy + sy0, oy + sy1), slice(ox + sx0, ox + sx1))
    ssl = (slice(sy0, sy1), slice(sx0, sx1))
    if shadow is not None:
        sh = np.zeros(p.f.shape, bool)
        sh[sl] = shadow[ssl]
        full[sl] = sp.m[ssl]
        cast(p, sh & ~full, k)
        full[:] = False
    full[sl] = sp.m[ssl]
    ff = np.zeros(p.f.shape, np.int16)
    tt = np.zeros(p.f.shape, np.int8)
    ff[sl], tt[sl] = sp.f[ssl], sp.t[ssl]
    p.f[full], p.t[full] = ff[full], tt[full]
    if outline:
        outline_mask(p, full)
    p.solid |= full
    b = np.zeros(p.f.shape, bool)
    if block is None:
        b[max(0, y - 2):y + 1, max(0, x - 2):x + 2] = True
    else:
        b[sl] = block[ssl]
    p.walk &= ~b
    return full


def cast_px(p: Plot, pts, k=2):
    """A cast shadow on a few listed pixels: each steps k tones down its own ramp (water one
    tone), never on standing things, edges or glows."""
    for (px, py) in pts:
        if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px] and p.t[py, px] < EDGE_T and not GLOW[p.f[py, px]]:
            if p.lava[py, px]:
                continue
            kk = 1 if p.wet[py, px] else k
            lo = 1 if p.wet[py, px] else 0
            p.t[py, px] = max(lo, min(5, p.t[py, px] - kk))


def pebble(p: Plot, x, y, ramp='stone', w=3, h=2, shadow=True, k=2):
    """A pebble or cobble drawn into the ground: lit top-left, body, dark lower-right, its
    shadow a short step on the ground to the right and below. Never smaller than 2 x 2.
    Returns the pixels it set."""
    w, h = max(2, w), max(2, h)
    pts = []
    for j in range(h):
        for i in range(w):
            if (i == 0 or i == w - 1) and (j == 0 or j == h - 1) and w > 2 and h > 2:
                continue                                   # corners knocked off
            pts.append((i, j))
    done = set()
    for (i, j) in pts:
        px, py = x + i, y + j
        if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
            tone = 4 if (i + j == 0 or (j == 0 and i < w // 2) or (i == 0 and j < h // 2 and h > 2)) else \
                2 if (i == w - 1 or j == h - 1) else 3
            if w == 2 and h == 2:
                tone = (4, 3, 3, 2)[i + 2 * j]
            p.f[py, px], p.t[py, px] = IDX[ramp], tone
            done.add((px, py))
    if shadow and done:
        sh = set()
        for (px, py) in done:
            for (dx, dy) in ((1, 0), (1, 1)):
                q = (px + dx, py + dy)
                if q not in done and (q[0], q[1] + 1) not in done:
                    sh.add(q)
        cast_px(p, sh, 1 if k < 2 else 2)
    return done


def light_of(u, v, lift=0.3):
    """Light on a rounded form at (u, v) from its centre (radius 1): the upper left lit."""
    r2 = np.clip(u * u + v * v, 0, 1)
    return -0.6 * u - 0.75 * v + lift * np.sqrt(1 - r2)


def tone_of(lam, cuts=(0.45, 0.0, -0.45)):
    """Hard steps of light (one hard terminator, house rule 3): 4, 3, 2, 1."""
    return np.where(lam > cuts[0], 4, np.where(lam > cuts[1], 3, np.where(lam > cuts[2], 2, 1)))


def box_blur(a, r):
    """The mean over a (2r + 1) square round each pixel, edges clamped."""
    a = np.asarray(a, np.float64)
    if r <= 0:
        return a.copy()
    n = 2 * r + 1
    pa = np.pad(a, r, mode='edge')
    c = np.pad(pa.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)


def wobble(m, seed, amp=1.5, scale=9):
    """A mask whose edge wanders up to `amp` px inside its edge cells (never a ruled line)."""
    m = np.asarray(m, bool)
    h, w = m.shape
    y, x = np.mgrid[0:h, 0:w]
    n = (fbm(x, y, scale, seed) - 0.5) * 2 * amp
    d_in, d_out = edge_dist(m, 4), edge_dist(~m, 4)
    return (m & ~((d_in <= 2) & (n < -(d_in - 0.5)))) | (~m & (d_out <= 2) & (n > d_out - 0.5))


def rounded(m, r=3):
    """Close then open a mask by r: every corner rounded by about a cell, straight runs kept."""
    m = erode(dilate(np.asarray(m, bool), r), r)
    return dilate(erode(m, r), r)


class Relief:
    """Tiers with their own heights. T (screen space): the tier whose top is seen at each
    pixel before the faces are hung; E[k]: the height of tier k's top in px. Under every rim
    a south face hangs as tall as the drop to the ground south of it (a low step of 16, a
    tier of 32, a stack of two). `face` the face pixels, `kf` the tier of the rim each hangs
    from, `kb` the tier at its foot, `depth` rows below that rim, `fh` the face's height."""

    def __init__(self, T, E):
        self.T = np.asarray(T, np.int16)
        self.E = np.asarray(E, np.int32)
        h, w = self.T.shape
        self.face = np.zeros((h, w), bool)
        self.kf = np.zeros((h, w), np.int16)
        self.kb = np.zeros((h, w), np.int16)
        self.depth = np.zeros((h, w), np.int16)
        self.fh = np.zeros((h, w), np.int16)
        below = shift(self.T, 0, -1, 999)
        for k in range(int(self.T.max()), int(self.T.min()), -1):
            rim = (self.T == k) & (below < k) & ~self.face
            ry, rx = np.nonzero(rim)
            if not len(ry):
                continue
            bk = np.clip(below[ry, rx], 0, k)
            fhk = (self.E[k] - self.E[bk]).astype(np.int16)
            alive = np.ones(len(ry), bool)
            for d in range(1, int(fhk.max()) + 1):
                yy = ry + d
                ok = alive & (yy < h) & (fhk >= d)
                ok[ok] &= (~self.face[yy[ok], rx[ok]]) & (self.T[yy[ok], rx[ok]] < k)
                alive &= ok | (fhk < d)
                sel = np.nonzero(ok)[0]
                if not len(sel):
                    if not alive.any():
                        break
                    continue
                Y, X = yy[sel], rx[sel]
                self.face[Y, X] = True
                self.kf[Y, X] = k
                self.kb[Y, X] = bk[sel]
                self.depth[Y, X] = d - 1
                self.fh[Y, X] = fhk[sel]
        self.rim = shift(self.face & (self.depth == 0), 0, -1, False) & ~self.face
        self.elev = np.where(self.face, self.E[self.kf] - self.depth - 1, self.E[np.clip(self.T, 0, len(self.E) - 1)])

    def top(self, k):
        return (self.T == k) & ~self.face

    def tops(self):
        return ~self.face

    def seen(self):
        return np.where(self.face, -1, self.T)


def lattice(C, w=None, h=None):
    """A pixel tier map from a cell map on the 8 px grid, as a dual-grid (Wang corner)
    autotiler lays it: every outline runs along the grid, each convex corner is cut and
    each concave corner filled by a 4 px run at 45 degrees, so a curve on the cells reads
    as stepped runs and 45 degree diagonals, never a staircase of single cells."""
    C = np.asarray(C, np.int16)
    rows, cols = C.shape
    w = w or cols * GRID
    h = h or rows * GRID
    y, x = np.mgrid[0:h, 0:w]
    ci, cj = np.clip(x // GRID, 0, cols - 1), np.clip(y // GRID, 0, rows - 1)
    lx, ly = x % GRID, y % GRID
    vx, vy = ci + (lx >= GRID // 2), cj + (ly >= GRID // 2)
    d = np.abs(lx + 0.5 - (vx - ci) * GRID) + np.abs(ly + 0.5 - (vy - cj) * GRID)
    Cp = np.pad(C, 1, mode='edge')            # Cp[j + 1, i + 1] = C[j, i]
    T = np.full((h, w), int(C.min()), np.int16)
    for k in range(int(C.min()) + 1, int(C.max()) + 1):
        A = Cp >= k
        # how many of the four cells round each vertex are on tier k or higher
        n = (A[:-1, :-1].astype(np.int8) + A[:-1, 1:] + A[1:, :-1] + A[1:, 1:])[vy, vx]
        inside = C[cj, ci] >= k
        m = inside & ~((n == 1) & (d < 4))
        m |= ~inside & (n == 3) & (d <= 4)
        T[m] = k
    return T


def facing(R, r=5):
    """How each face pixel turns, from the outward normal of its tier's outline at its rim:
    +1 west (to the light), -1 east (into shade), 0 south."""
    lam = np.zeros(R.T.shape)
    yy, xx = np.mgrid[0:R.T.shape[0], 0:R.T.shape[1]]
    for k in [int(v) for v in np.unique(R.kf[R.face])]:
        b = box_blur((R.T >= k).astype(np.float64), r)
        gx = shift(b, -1, 0, 0.0) - shift(b, 1, 0, 0.0)
        gy = shift(b, 0, -1, 0.0) - shift(b, 0, 1, 0.0)
        nx = -gx / (np.hypot(gx, gy) + 1e-9)
        sel = R.face & (R.kf == k)
        ry = np.clip(yy[sel] - R.depth[sel] - 1, 0, R.T.shape[0] - 1)
        lam[sel] = -nx[ry, xx[sel]]
    return lam


def _lay(seed, x, y, n=4, salt=0):
    """Which of n tile variants goes at column x of a run (by hash, never the one before),
    and the column inside the 8 px tile."""
    off = int(hash01(y // 8, salt, seed) * 8)
    seg = (x + off) // 8
    v = int(hash01(seg, y // 16, seed + 1) * n)
    if v == int(hash01(seg - 1, y // 16, seed + 1) * n):
        v = (v + 1) % n
    return v, (x + off) % 8


def tier_shadows(p: Plot, R: Relief, k_tones=2, throw=SHADOW):
    """Each tier throws its shadow down and to the right onto lower ground (soft grid: 8 px
    whatever its height): two tones down, one at its tail."""
    T, seen = R.T, R.seen()
    for k in range(int(T.min()) + 1, int(T.max()) + 1):
        body = (T >= k) | (R.face & (R.kf >= k))
        sh = np.zeros(p.f.shape, bool)
        tail = np.zeros(p.f.shape, bool)
        for i in range(1, throw + 1):
            s = shift(body, i, i // 3, False)
            (sh if i <= throw - 3 else tail)[...] |= s
        low = (seen >= 0) & (seen < k) & ~p.solid
        cast(p, sh & low, k_tones)
        cast(p, tail & ~sh & low, 1)


def stone(p: Plot, x, y, w, h, seed=0, snow_cap=False, ramp=None, k=2):  # noqa: C901
    """A stone or small boulder drawn into the ground (2 to 10 px): rounded, lit in a
    crescent on its upper left, its lower right dark, a short shadow down and to the right;
    with snow lying on its top when `snow_cap`. Returns the pixels it set."""
    ramp = ramp or ROCK[int(hash01(int(x), int(y), seed) * len(ROCK))]
    w, h = max(2, int(w)), max(2, int(h))
    done = {}
    for j in range(h):
        for i in range(w):
            u, v = (i + 0.5 - w / 2.0) / (w / 2.0), (j + 0.5 - h / 2.0) / (h / 2.0)
            if u * u + v * v > 1.15 and w > 3:
                continue
            px, py = x + i, y + j
            if not (0 <= px < p.w and 0 <= py < p.h) or p.solid[py, px]:
                continue
            lam = -0.6 * u - 0.8 * v
            t = 4 if lam > 0.45 else 3 if lam > -0.15 else 2 if lam > -0.7 else 1
            p.f[py, px], p.t[py, px] = IDX[ramp], t
            done[(px, py)] = (i, j)
    if snow_cap and w >= 4:
        for (px, py), (i, j) in done.items():
            top = (px, py - 1) not in done
            second = (px, py - 2) not in done and not top
            if top or (second and i < w - 1):
                p.f[py, px] = IDX['snow']
                p.t[py, px] = 5 if (top and i < w // 2) else 4
    if done:
        sh = set()
        reach = 3 if w < 6 else 4
        for (px, py) in done:
            for d in range(1, reach):
                q = (px + d, py + d // 2 + 1)
                if q not in done:
                    sh.add(q)
        cast_px(p, sh, k)
    return done


def view(p: Plot, y0, y1, x0, x1):
    """A window onto a plot: its arrays are views, so painting the window paints the plot;
    p.x and p.y keep their global values, so noise runs on across the window's edge."""
    q = object.__new__(Plot)
    sl = (slice(y0, y1), slice(x0, x1))
    for a in ('f', 't', 'wet', 'lava', 'solid', 'walk', 'hazard', 'tier', 'y', 'x'):
        setattr(q, a, getattr(p, a)[sl])
    q.h, q.w = q.f.shape
    q.vents = p.vents
    q.window = (y0, x0)
    return q


def local(fn, pad=10):
    """Run a piece that paints a mask (and returns nothing) on the mask's bounding box only,
    with a margin, instead of the whole plot: the same pixels, much less work."""
    def wrapped(p, m, *a, **k):
        if not isinstance(p, Plot) or hasattr(p, 'window'):
            return fn(p, m, *a, **k)
        m = np.asarray(m, bool)
        if m.shape != p.f.shape or not m.any():
            return fn(p, m, *a, **k)
        ys = np.nonzero(m.any(1))[0]
        xs = np.nonzero(m.any(0))[0]
        y0, y1 = max(0, int(ys[0]) - pad), min(p.h, int(ys[-1]) + 1 + pad)
        x0, x1 = max(0, int(xs[0]) - pad), min(p.w, int(xs[-1]) + 1 + pad)
        if (y1 - y0) * (x1 - x0) > 0.85 * p.h * p.w:
            return fn(p, m, *a, **k)
        q = view(p, y0, y1, x0, x1)

        def crop(v):
            if isinstance(v, np.ndarray) and v.shape == p.f.shape:
                return v[y0:y1, x0:x1]
            return v
        return fn(q, m[y0:y1, x0:x1], *[crop(v) for v in a], **{kk: crop(v) for kk, v in k.items()})
    wrapped.__name__ = fn.__name__
    wrapped.__doc__ = fn.__doc__
    return wrapped


def _open2(m):
    """Opening by a 2 x 2 cell square: no part of a level narrower than two cells."""
    e = m & shift(m, -1, 0, False) & shift(m, 0, -1, False) & shift(m, -1, -1, False)
    return e | shift(e, 1, 0, False) | shift(e, 0, 1, False) | shift(e, 1, 1, False)


def _close2(m):
    """Closing by a 2 x 2 cell square: no notch or gap narrower than two cells."""
    return ~_open2(~m)


def soft_grid_cells(C, E, iters=4):
    """A cell map of tiers made fit for the soft grid: every level's outline in runs of two
    cells or more (no one-cell notch, spur or step), and under every rim either a face and
    a ledge's room on the tier below (the face's height in cells plus one) or the tier below
    ending there too (a stack of two, never three). Levels stay nested."""
    C = np.asarray(C, np.int16)
    kmin, kmax = int(C.min()), int(C.max())
    M = {k: C >= k for k in range(kmin + 1, kmax + 1)}
    for _ in range(iters):
        prev = None
        for k in range(kmin + 1, kmax + 1):
            m = _close2(_open2(M[k]))
            if prev is not None:
                m &= prev
            M[k] = m
            prev = m
        for k in range(kmin + 2, kmax + 1):
            A, B = M[k - 1], M[k]
            fc = max(1, (E[k] - E[k - 1]) // GRID)
            for _step in range(fc + 2):
                edge = B & ~shift(B, 0, -1, False)           # B's last row in each column
                g = np.zeros(B.shape, np.int16)              # A's rows south of it
                run = edge.copy()
                for d in range(1, fc + 2):
                    run = shift(run, 0, 1, False) & A & ~B
                    g = np.where(shift(run, 0, -d, False) & edge, d, g)
                bad = edge & (g > 0) & (g < fc + 1)
                if not bad.any():
                    break
                grow = bad & (g <= fc // 2)
                for d in range(1, fc // 2 + 1):
                    B = B | (shift(grow & (g >= d), 0, d, False) & A)
                B = B & ~(bad & ~grow)
            # never three stacked: B, A and the level under A all ending on one row
            if k >= kmin + 3:
                A2 = M[k - 2]
                eb = B & ~shift(B, 0, -1, False)
                st = eb & ~shift(A, 0, -1, False) & ~shift(A2, 0, -1, False)
                B = B & ~st
            M[k] = B
    out = np.full(C.shape, kmin, np.int16)
    for k in range(kmin + 1, kmax + 1):
        out[M[k]] = k
    return out


def _from_canvas(cv):
    """A house_kits canvas (RGBA in house colours) as a kit Sprite: every colour mapped back
    to its ramp and tone."""
    img = cv.img if hasattr(cv, 'img') else cv
    a = np.asarray(img.convert('RGBA'))
    h, w = a.shape[:2]
    sp = Sprite(w, h, w // 2, h - 1)
    lut = {}
    for i in range(len(NAMES)):
        for t in range(EDGE_T + 1):
            key = tuple(int(c) for c in COL[i, t])
            if key not in lut or (t < EDGE_T and lut[key][1] == EDGE_T):
                lut[key] = (FAMILY[i] if t == EDGE_T else i, t)
    miss = 0
    for y in range(h):
        for x in range(w):
            if a[y, x, 3] < 128:
                continue
            k = (int(a[y, x, 0]), int(a[y, x, 1]), int(a[y, x, 2]))
            if k not in lut:
                best = min(lut, key=lambda c: sum((c[j] - k[j]) ** 2 for j in range(3)))
                lut[k] = lut[best]
                miss += 1
            sp.f[y, x], sp.t[y, x] = lut[k]
            sp.m[y, x] = True
    sp.miss = miss
    return sp


base = local(base)
texture = local(texture)
despeckle = local(despeckle)


# --- the ways up and down (from the mountain kit, in sand and stone) ------------------------------
def trail(p: Plot, pts, width=16, seed=0, kind='earth', m=None):
    """A mountain trail (size guide 16): on turf, packed earth worn lighter where feet go, its
    edges ragged into the turf, grit kicked to the sides; in sand, a shallow trodden trough,
    its floor packed a tone down, its sides kicked up a tone lighter. Walkable."""
    ch = Channel(p, pts, reach=width)
    hw = width / 2
    wob = (fbm(ch.s, np.sign(ch.n), 14, seed) - 0.5) * 3
    tm = ch.near & (np.abs(ch.n) <= hw + wob) & ~p.solid & ~dilate(p.wet, 2) & ~p.hazard
    if m is not None:
        tm &= np.asarray(m, bool)
    if kind == 'earth':
        edge = tm & (np.abs(ch.n) > hw + wob - 2.5)
        rag = edge & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.45)
        tm &= ~rag
        base(p, tm, [('path_warm', 0.3), ('path', 0.35), ('earth', 0.35)], seed + 2, 7)
        worn = tm & (np.abs(ch.n) < hw * 0.45) & (fbm(p.x, p.y, 9, seed + 3) > 0.42)
        p.step(worn, 1)
        stamp(p, tm, 0.07, seed + 4, FLAT, swap='mix')
        ring = dilate(tm, 1) & ~tm & ~p.solid
        p.step(ring & (hash01(p.x, p.y, seed + 5) < 0.6), -1)
        for (x, y) in _scatter(edge & tm, 40, seed + 6, margin=0):
            pebble(p, x, y, ROCK[(x + y) % 3], 2, 2, k=1)
        despeckle(p, tm)
    else:
        # a path trodden through sand: a shallow trough, its floor darker and packed, its
        # sides kicked up a tone lighter
        tm &= ~(tm & (np.abs(ch.n) > hw + wob - 2) & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.5))
        base(p, tm, [('sand', 0.5), ('sand_cool', 0.5)], seed + 2, 6, tone=2)
        packed = tm & (np.abs(ch.n) < hw * 0.45) & (fbm(p.x, p.y, 8, seed + 3) > 0.4)
        p.t[packed] = 3
        berm = dilate(tm, 1) & ~tm & ~p.solid & (FAMILY[p.f] == IDX['sand'])
        p.step(berm & (hash01(p.x // 2, p.y, seed + 4) < 0.6), 1)
        stamp(p, tm, 0.05, seed + 5, FLAT, dt=-1)
    p.walk |= tm & ~p.solid & ~p.hazard
    return ch, tm


def ramp_along(p: Plot, R: Relief, xa, xb, depth=24, seed=0, rising='east', kind='earth', k=None):
    """A ramp cut along a south face (soft grid: along the face at 1 in 3, at least 24 wide),
    rising from the foot at one end to the top at the other. Seen from the south: the cut's
    back wall (the face's own rock, carried up) behind the tread, the tread (trodden earth
    with ridges across the slope and a worn track, or trodden sand), and under its outer
    edge a drystone retaining wall holding it up, coursed stones lit on top, with a parapet
    of coping stones along the open side (size guide: a parapet on a ledge path). At the low
    end the notch's end wall shows as the tier's own dark side band. Returns the tread."""
    f0, t0 = p.f.copy(), p.t.copy()
    tread = np.zeros(p.f.shape, bool)
    lip_m = np.zeros(p.f.shape, bool)
    kerb_m = np.zeros(p.f.shape, bool)
    band_m = np.zeros(p.f.shape, bool)
    wall_m = np.zeros(p.f.shape, bool)
    ret_m = np.zeros(p.f.shape, bool)
    lo_x, hi_x = min(xa, xb), max(xa, xb)
    run = hi_x - lo_x
    for x in range(lo_x - STRIP, hi_x + STRIP):
        if not 0 <= x < p.w:
            continue
        fcol = R.face[:, x] if k is None else (R.face[:, x] & (R.kf[:, x] == k))
        ys = np.nonzero(fcol)[0]
        if not len(ys):
            continue
        Rr, yf = int(ys.min()), int(ys.max()) + 1
        F = yf - Rr
        low_end = x < lo_x if rising == 'east' else x >= hi_x
        if low_end:
            if (rising == 'east' and x >= lo_x - STRIP) or (rising == 'west' and x < hi_x + STRIP):
                for y in range(max(0, Rr - depth), Rr):
                    band_m[y, x] = True
            continue
        if not lo_x <= x < hi_x:
            continue
        u = (x - lo_x) / run if rising == 'east' else (hi_x - 1 - x) / run
        e = int(round(F * u))
        top_wall = Rr - depth
        tread_top = yf - depth - e
        for y in range(max(0, top_wall), max(0, tread_top)):
            if y + depth < p.h:
                p.f[y, x], p.t[y, x] = f0[y + depth, x], t0[y + depth, x]
                wall_m[y, x] = True
        for y in range(max(0, tread_top), max(0, yf - e)):
            tread[y, x] = True
        for y in range(max(0, yf - e), yf):
            ret_m[y, x] = True
        if yf - e - 1 >= 0 and e > 4:
            lip_m[yf - e - 1, x] = True
            kerb_m[yf - e - 1, x] = True
            if yf - e - 2 >= 0 and (x - lo_x + seed) % 9 < 6:
                kerb_m[yf - e - 2, x] = True
    tread &= ~p.hazard
    kerb_m &= tread
    # the retaining wall: drystone courses under the tread's outer edge
    rr = ret_m.copy()
    course = (p.y // 4)
    off = (hash01(course, 0, seed + 9) * 9).astype(int)
    sl = 5 + (hash01((p.x + off) // 7, course, seed + 10) * 4).astype(int)
    pj = ((p.x + off) % sl) == 0
    fam = np.array([IDX[r] for r in ROCK])[(hash01((p.x + off) // sl, course, seed + 11) * 3).astype(int)]
    p.f[rr] = fam[rr]
    rowc = p.y % 4
    p.t[rr] = np.where(rowc == 0, 4, np.where(rowc == 3, 1, 3))[rr]
    p.t[rr & pj & (rowc != 0)] = 1
    p.t[rr & (p.x > (lo_x + hi_x) // 2) & (rowc == 2)] = 2
    foot = rr & ~shift(rr, 0, -1, False)
    p.t[foot] = np.minimum(p.t[foot], 1)
    base_t = 3 if rising == 'east' else 2
    if kind == 'earth':
        sib = hash01(p.x // 4, p.y // 3, seed + 1)
        famt = np.where(sib < 0.3, IDX['stone_warm'], np.where(sib > 0.7, IDX['earth'], IDX['path_cool']))
        p.f[tread], p.t[tread] = famt[tread], base_t
    else:
        p.f[tread], p.t[tread] = IDX['sand_cool'], base_t
    rows_in = np.zeros(p.f.shape, np.int16)
    for x in range(lo_x, hi_x):
        col = np.nonzero(tread[:, x])[0]
        if len(col):
            rows_in[col, x] = col - col.min()
    mid = depth // 2
    track = tread & (np.abs(rows_in - mid) <= 3)
    ridge = tread & ~track & (((p.x - lo_x + (p.y // 5)) % 6) == 0)
    p.t[ridge] = base_t + 1
    if kind == 'earth':
        p.f[track & (hash01(p.x // 3, p.y, seed + 2) < 0.5)] = IDX['path']
    p.t[track & (hash01(p.x // 2, p.y // 2, seed + 3) < 0.2)] = base_t + 1
    backfoot = tread & (rows_in < 2)
    p.t[backfoot] = np.maximum(0, p.t[backfoot] - 1)
    for (x, y) in _scatter(tread & ~track, 40, seed + 4, margin=0):
        pebble(p, x, y, ROCK[(x + y) % 3], 2, 2, shadow=False, k=1)
    shade = tread & ((p.x - lo_x < 6) if rising == 'east' else (hi_x - 1 - p.x < 6)) & (rows_in < depth - 3)
    p.step(shade, -1, lo=0)
    # the parapet: coping stones on the open edge, lit on top
    p.put(kerb_m, 'stone', 3)
    p.t[kerb_m & ~shift(kerb_m, 0, 1, False)] = 4
    p.t[kerb_m & ~shift(kerb_m, -1, 0, False)] = 2
    p.t[kerb_m & ~shift(kerb_m, 1, 0, False) & ~shift(kerb_m, 0, 1, False)] = 5
    lump = ((p.y // 3 + p.x // 2) % 2 == 0)
    p.f[band_m] = np.where(lump[band_m], IDX['stone_cool'], IDX['slate'])
    p.t[band_m] = np.where(lump[band_m], 2, 1)
    edge = (shift(band_m, 1, 0, False) if rising == 'east' else shift(band_m, -1, 0, False)) & ~band_m & tread
    p.t[edge] = 0
    p.walk |= tread & ~kerb_m
    p.solid &= ~tread
    p.solid |= wall_m | band_m | kerb_m | ret_m
    p.walk &= ~(wall_m | band_m | kerb_m | ret_m)
    hi_end = (p.x >= (hi_x - 8 if rising == 'east' else lo_x)) & (p.x < (hi_x if rising == 'east' else lo_x + 8))
    head = hi_end & ~R.face & ~wall_m & ~band_m & ~p.hazard
    for dd in range(1, 7):
        p.walk |= head & shift(tread, 0, -dd, False)
    lo_end = (p.x >= (lo_x if rising == 'east' else hi_x - 8)) & (p.x < (lo_x + 8 if rising == 'east' else hi_x))
    for dd in range(1, 5):
        p.walk |= lo_end & shift(tread, 0, dd, False) & ~R.face & ~p.hazard & ~p.solid
    return tread


def stair(p: Plot, R: Relief, x0, width=40, seed=0, k=None):
    """A stair cut through a face (soft grid: 40 px open between 4 px cheeks, 4 px risers):
    stone treads laid in slabs, lit along their nose, each riser a dark line, worn in the
    middle, the west cheek lit and the east cheek dark, blown sand in the treads' back corners.
    Its column is opened to a walker."""
    col = (p.x >= x0) & (p.x < x0 + width + 8) & R.face & ~p.hazard
    if k is not None:
        col &= R.kf == k
    if not col.any():
        return np.zeros(p.f.shape, bool)
    cheek_w = col & (p.x < x0 + 4)
    cheek_e = col & (p.x >= x0 + width + 4)
    run = col & ~cheek_w & ~cheek_e
    d = R.depth
    r = d % 4
    p.put(run, 'stone', 3)
    sw = 8 + (hash01(d // 4, 0, seed) * 7).astype(int)
    slab = (p.x - x0 + (hash01(d // 4, 1, seed) * 9).astype(int)) // sw
    sib = hash01(slab, d // 4, seed)
    p.f[run & (sib < 0.4)] = IDX['stone_warm']
    p.f[run & (sib > 0.7)] = IDX['stone_cool']
    p.t[run & (r == 0)] = 4
    p.t[run & (r == 3)] = 1
    p.t[run & (r == 2)] = 2
    sj = run & (slab != shift(slab, 1, 0, -1)) & (r < 3)
    p.t[sj] = 2
    worn = run & (np.abs(p.x - (x0 + 4 + width / 2)) < width * 0.22) & (r == 1)
    p.t[worn] = 4
    corner = run & (r == 2) & ((p.x < x0 + 8) | (p.x >= x0 + width)) & (hash01(p.x // 3, d // 4, seed + 5) < 0.6)
    p.put(corner, 'sand', 4)          # blown sand in the treads' back corners
    p.put(cheek_w, 'stone_warm', 4)
    p.t[cheek_w & (p.x == x0 + 3)] = 3
    p.t[cheek_w & (p.x == x0)] = 1
    p.put(cheek_w & (d == 0), 'stone_warm', 5)
    p.put(cheek_e, 'stone_cool', 1)
    p.t[cheek_e & (p.x == x0 + width + 4)] = 2
    p.put(cheek_e & (d == 0), 'stone_cool', 2)
    p.walk[run] = True
    p.solid[run] = False
    head = (p.x >= x0 + 4) & (p.x < x0 + width + 4) & ~R.face
    for dd in range(1, 7):
        p.walk |= head & shift(run & (R.depth == 0), 0, -dd, False) & ~p.hazard
        p.walk |= head & shift(run & (R.depth == R.fh - 1), 0, dd, False) & ~p.hazard & ~p.solid
    return run


# --- distance ---------------------------------------------------------------------------------
def dilate8(m, r=1):
    out = np.asarray(m, bool).copy()
    for _ in range(r):
        o = dilate(out, 1)
        o[1:, 1:] |= out[:-1, :-1]
        o[1:, :-1] |= out[:-1, 1:]
        o[:-1, 1:] |= out[1:, :-1]
        o[:-1, :-1] |= out[1:, 1:]
        out = o
    return out


def dist_to(m, cap=64):
    """Px from each pixel to the mask (0 inside it), capped: grown alternately by the four
    and the eight neighbours, so the contours are octagons, not diamonds."""
    m = np.asarray(m, bool)
    d = np.full(m.shape, cap, np.int16)
    d[m] = 0
    cur = m.copy()
    for i in range(1, cap):
        nxt = dilate8(cur) if i % 2 else dilate(cur, 1)
        new = nxt & ~cur
        if not new.any():
            break
        d[new] = i
        cur = nxt
    return d


# --- the tileset and its autotiler -----------------------------------------------------------
# The pictures are data in coast_tiles.py (drawn pixel by pixel); here they are laid along
# the tiers' organic outlines, the way Sea of Stars and Eastward build their sea cliffs.
KEY = {}
for _i, _c in enumerate('012345'):
    KEY[_c] = ('rock', _i)
for _i, _c in enumerate('ABCDEF'):
    KEY[_c] = ('warm', _i)
for _i, _c in enumerate('PQRSTU'):
    KEY[_c] = ('cool', _i)
for _i, _c in enumerate('ghijkl'):
    KEY[_c] = ('grass', _i)
for _i, _c in enumerate('abcdef'):
    KEY[_c] = ('sand', _i)
KEY.update({'K': ('rock', EDGE_T), 'G': ('grass', EDGE_T), 'L': ('grass_cool', 2), 'M': ('grass_cool', 3),
            'O': ('clay_warm', 4), 's': ('berry', 3), 't': ('berry', 4), 'u': ('snow', 5),
            'v': ('stone', 2), 'w': ('stone', 4), 'x': ('leaf_cool', 1), 'y': ('leaf_cool', 2)})
ROCK_CHARS = set('012345ABCDEFPQRSTU')
WIDTHS = (10, 14, 18, 24)


def decode(ch, rock=None, key=None):
    """A tile character as (ramp index, tone): `rock` the ramp of the piece being laid (its
    siblings for the warm and cool letters)."""
    role, t = (key or KEY)[ch]
    if role == 'rock':
        return int(rock), t
    if role == 'warm':
        return int(WARM[rock]), t
    if role == 'cool':
        return int(COOL[rock]), t
    return IDX[role], t


def column_rows(w, H, seed):
    """A rock column w wide stacked from the tileset to at least H rows: a crown, bodies in
    hashed order (never one body twice running) and its foot. Returns the rows, which piece
    each row came from, and the foot."""
    C = tiles.COLUMNS
    rows = list(C[f'crown{w}{"abc"[int(hash01(seed, 0, 5) * 3)]}'])
    piece = [0] * len(rows)
    last, i = -1, 1
    while len(rows) < H:
        j = int(hash01(seed, i, 6) * 4)
        if j == last:
            j = (j + 1) % 4
        body = C[f'body{w}{"abcd"[j]}']
        rows += body
        piece += [i] * len(body)
        last, i = j, i + 1
    return rows, piece, C[f'foot{w}{"ab"[int(hash01(seed, 9, 7) * 2)]}']


def cliff_faces(p: Plot, R: Relief, seed=0, m=None, lam=None, rocks=SANDSTONE):
    """Every south face in m built from the tileset's columns of rounded stones: along each
    tier's faces the autotiler lays columns of hashed widths (10 to 24 px), each stone one
    of the cliff's `rocks` and the column stacked to that face's height; a stretch of face
    turned west to the light is a tone lighter and on its warm sibling, one turned east a
    tone darker on its cool sibling; the lowest quarter a tone down. A face under a diagonal
    rim is the same columns sheared (rows run with the rim, columns stay upright)."""
    fc = R.face if m is None else (R.face & np.asarray(m, bool))
    if not fc.any():
        return
    lam = facing(R) if lam is None else lam
    for k in [int(v) for v in np.unique(R.kf[fc])]:
        sel = fc & (R.kf == k)
        xs = np.nonzero(sel.any(0))[0]
        x = int(xs.min()) - int(hash01(k, 0, seed) * 24)
        ci = 0
        while x <= xs.max():
            w = WIDTHS[int(hash01(ci, k, seed + 1) ** 1.2 * len(WIDTHS))]
            x0, x1 = max(0, x), max(0, x + w)
            band = sel[:, x0:x1]
            if band.any():
                ys, bx = np.nonzero(band)
                bx = bx + x0
                cs = (ci * 131 + k * 7919 + seed) & 0xFFFF
                rows, piece, foot = column_rows(w, int(R.fh[ys, bx].max()), cs)
                fams = [IDX[rocks[int(hash01(cs, j, seed + 2) * len(rocks))]] for j in range(max(piece) + 1)]
                L = float(np.median(lam[ys, bx]))
                shade = 1 if L > 0.4 else (-1 if L < -0.25 else 0)
                swap = WARM if L > 0.4 else (COOL if L < -0.6 else None)
                for y_, x_ in zip(ys, bx):
                    d, fh = int(R.depth[y_, x_]), int(R.fh[y_, x_])
                    ch = foot[d - (fh - 4)][x_ - x] if d >= fh - 4 else rows[d][x_ - x]
                    fam = fams[piece[d]] if d < fh - 4 else fams[0]
                    f_, t = decode(ch, fam)
                    if ch in ROCK_CHARS:
                        t0 = t
                        t = t + (shade if (shade > 0 or t0 <= 3) else 0) - (1 if d >= fh * 0.75 else 0)
                        if swap is not None:
                            f_ = int(swap[f_])
                        t = max(t, min(t0, 1))        # the shade never swallows a stone's edge
                        t = int(np.clip(t, 0, 5))
                    p.f[y_, x_], p.t[y_, x_] = f_, t
            x += w
            ci += 1
    rock = fc & (p.t < EDGE_T) & np.isin(FAMILY[p.f], [FAMILY[IDX[r]] for r in rocks])
    stamp(p, rock, 0.06, seed + 7, SMALL, swap='mix')
    stamp(p, rock & (p.t <= 3), 0.02, seed + 8, DOMINOES, dt=1)
    p.solid |= fc
    p.walk &= ~fc


def lips(p: Plot, R: Relief, kind, seed=0, m=None):
    """What hangs over every face from the top above it, by that top's kind per pixel
    ('turf', 'marram', 'rock'): the tileset's lips laid along the rim (row 2 on the face's
    first row), variants by hash, never one twice running."""
    rim = R.rim if m is None else (R.rim & np.asarray(m, bool))
    for y, x in zip(*np.nonzero(rim)):
        kd = kind[y, x]
        if kd not in tiles.LIPS:
            continue
        v, col = _lay(seed, x, y)
        for i, row in enumerate(tiles.LIPS[kd][v]):
            yy = y - 1 + i
            ch = row[col]
            if not 0 <= yy < p.h or ch == '.' or (i >= 2 and not R.face[yy, x]):
                continue
            if ch in '-=':
                if p.t[yy, x] < EDGE_T:
                    p.t[yy, x] = max(0, p.t[yy, x] - (1 if ch == '-' else 2))
                continue
            p.f[yy, x], p.t[yy, x] = decode(ch, p.f[yy, x])


def hangs(p: Plot, R: Relief, kind, seed=0, every=0.08):
    """Thrift and sea campion hanging over faces from turf lips, one now and then (by hash)."""
    for y, x in zip(*np.nonzero(R.rim)):
        if kind[y, x] != 'turf' or hash01(x // 6, y // 8, seed) > every or x % 6:
            continue
        sp = tiles.HANGS[int(hash01(x, y, seed + 1) * len(tiles.HANGS))]
        for i, row in enumerate(sp):
            for j, ch in enumerate(row):
                yy, xx = y + 3 + i, x + j
                if ch != '.' and 0 <= yy < p.h and 0 <= xx < p.w and R.face[yy, xx]:
                    p.f[yy, xx], p.t[yy, xx] = decode(ch, p.f[yy, xx])


def bands(p: Plot, R: Relief, seed=0, kind=None, rocks=SANDSTONE):
    """The side bands (soft grid: 5 px) from the tileset: where a top ends west or east above
    lower ground, its last 5 px are its rock seen edge-on (lit on the west, in the two
    darkest tones on the east), the lip turning the corner over its first two rows (the
    outer corner); a lower face beside a band sits in a crease of shade (the inner corner)."""
    seen = R.seen()
    for k in range(int(R.T.min()) + 1, int(R.T.max()) + 1):
        topk = R.top(k)
        low = (seen >= 0) & (seen < k)
        for side, dx in (('w', 1), ('e', -1)):
            edge = topk & shift(low, dx, 0, False)
            edge &= shift(edge, 0, 1, False) | shift(edge, 0, -1, False)
            for y, x in zip(*np.nonzero(edge)):
                tile = tiles.BANDS[side][int(hash01(x // 5, y // 8, seed + k) * len(tiles.BANDS[side]))]
                row = tile[y % 8]
                top_d = 0
                while top_d < 2 and y - top_d - 1 >= 0 and edge[y - top_d - 1, x]:
                    top_d += 1
                if top_d < 2 and kind is not None and kind[y, x] in tiles.BAND_CAPS:
                    row = tiles.BAND_CAPS[kind[y, x]][top_d]
                rock = IDX[rocks[2]] if side == 'w' else IDX[rocks[-1]]
                for i in range(STRIP):
                    xx = x + i if side == 'w' else x - i
                    if not 0 <= xx < p.w or not topk[y, xx]:
                        break
                    ch = row[i] if side == 'w' else row[STRIP - 1 - i]
                    if ch == '.':
                        continue
                    p.f[y, xx], p.t[y, xx] = decode(ch, rock)
                    p.solid[y, xx] = True
                    p.walk[y, xx] = False
                xc = x - 1 if side == 'w' else x + 1
                if 0 <= xc < p.w and R.face[y, xc] and p.t[y, xc] < EDGE_T:
                    p.t[y, xc] = max(0, p.t[y, xc] - 1)


def feet(p: Plot, R: Relief, kind, seed=0):
    """The ground at the foot of every face on land, from the tileset's feet by that ground's
    kind ('sand', 'shingle', 'rock', 'turf'): the contact row, fallen stones, wrack."""
    foot = shift(R.face & (R.depth == R.fh - 1), 0, 1, False) & ~R.face & ~p.solid & ~p.wet
    for y, x in zip(*np.nonzero(foot)):
        kd = kind[y, x]
        if kd not in tiles.FEET:
            continue
        v, col = _lay(seed, x, y, salt=3)
        for i, row in enumerate(tiles.FEET[kd][v]):
            yy = y + i
            if yy >= p.h or R.face[yy, x] or p.solid[yy, x] or p.wet[yy, x]:
                break
            if row[col] != '.':
                p.f[yy, x], p.t[yy, x] = decode(row[col], IDX['stone'])


def sea_foot(p: Plot, R: Relief, water, seed=0, wet_rows=10):
    """Where a face stands in the sea: its lowest rows wet (a tone down, the stone's edges
    kept), weed hanging in the two rows at the water, barnacles in pairs above them up to the
    tide line, and a pale salt line along the tide's reach."""
    water = np.asarray(water, bool)
    up = R.fh - 1 - R.depth                        # rows above the face's foot
    col = R.face & (up == 0) & shift(water, 0, -1, False)
    for _ in range(wet_rows):
        col |= shift(col, 0, -1, False) & R.face
    wet = col & (up < wet_rows)
    p.step(wet & (up < wet_rows - 2), -1, lo=1)
    cl = hash01(p.x // 2, p.y // 2, seed)
    weed = wet & (up < 3) & (cl < 0.7)
    p.put(weed & (up < 2), 'leaf_cool', 1)
    p.put(weed & (up == 2) & (cl < 0.45), 'leaf_cool', 2)
    barn = wet & (up >= 3) & (up < wet_rows - 3) & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.16)
    p.put(barn & (p.x % 2 == 0), 'bleached', 5)
    p.put(barn & (p.x % 2 == 1), 'bleached', 3)
    tide = wet & (up == wet_rows - 2) & (hash01(p.x // 3, 0, seed + 2) < 0.55)
    p.step(tide, 1)


def tile_sprite(rows, key=None, ramp='bleached'):
    """A tileset picture as a Sprite (its '.' transparent), for the tileset sheet."""
    key = key or KEY
    h, w = len(rows), len(rows[0])
    sp = Sprite(w, h, w // 2, h - 1)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '.' or ch in '-=' or ch not in key:
                continue
            sp.f[y, x], sp.t[y, x] = decode(ch, IDX[ramp], key=key)
            sp.m[y, x] = True
    return sp


# --- tops: sea turf and dunes -------------------------------------------------------------------
def tuft(p: Plot, x, y, seed=0, ramp='grass', h=None):
    """A tuft of short turf: two or three blades, lit tips, a dark root."""
    h = h or 2 + int(hash01(x, y, seed) * 2)
    for dx, hh in ((0, h), (1, h - 1), (-1, h - 1 if hash01(x, y, seed + 1) < 0.5 else 0)):
        for j in range(hh):
            px, py = x + dx, y - j
            if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
                p.f[py, px] = IDX[ramp]
                p.t[py, px] = 4 if j == hh - 1 else (2 if j == 0 else 3)


def cushion(p: Plot, x, y, seed=0, flower='berry'):
    """A thrift cushion (or sea campion when flower is 'snow'): a low round mound of needle
    leaves, lit on its top row, its flowers in pairs on top, a short shadow."""
    w = 4 + int(hash01(x, y, seed) * 3)
    pts = []
    for j in range(3):
        for i in range(w):
            if j == 0 and (i == 0 or i == w - 1):
                continue
            px, py = x + i, y + j
            if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
                p.f[py, px] = IDX['grass_cool']
                p.t[py, px] = 4 if j == 0 else (3 if i < w - 2 else 2)
                if j == 2:
                    p.t[py, px] = 2
                pts.append((px, py))
    for i in range(1, w - 1, 2):
        if hash01(x + i, y, seed + 1) < 0.75:
            for (dx, dy, t) in ((0, -1, 4), (1, -1, 3)):
                px, py = x + i + dx, y + dy
                if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
                    p.f[py, px] = IDX[flower]
                    p.t[py, px] = 5 if flower == 'snow' else t
    cast_px(p, [(x + w, y + 1), (x + w, y + 2), (x + w - 1, y + 3), (x + 1, y + 3), (x + 2, y + 3)], 1)


def heath(p: Plot, m, seed=0):
    """Coastal heath in the turf: low cushions of heather and crowberry in their own dark
    greens and purples, in clumps a few px across, lit on their upper west."""
    m = np.asarray(m, bool)
    n = fbm(p.x, p.y, 5, seed)
    p.put(m & (n > 0.5), 'leaf_cool', 2)
    p.put(m & (n <= 0.5), 'berry_cool', 2)
    p.put(m & (n > 0.72), 'leaf_cool', 3)
    p.put(m & (n < 0.28), 'berry_cool', 3)
    top = m & ~shift(m, 0, 1, False)
    p.step(top, 1)
    stamp(p, m, 0.12, seed + 1, SMALL, swap='mix')
    flowers = m & (hash01(p.x // 2, p.y, seed + 2) < 0.05) & (n <= 0.5)
    p.put(flowers | (shift(flowers, 1, 0, False) & m), 'berry', 4)
    cast(p, shift(m, 1, 1, False) & ~m, 1)


def outcrop(p: Plot, x, y, seed=0, rocks=SANDSTONE, n=None):
    """Bedrock breaking the turf: three to six flat slabs of the cliff's rock, lit on their
    upper west, lichen on them, grass tufts in the cracks between."""
    n = n or 3 + int(hash01(x, y, seed) * 4)
    for i in range(n):
        sx = x + int((hash01(i, 0, seed + x) - 0.5) * 18)
        sy = y + int((hash01(i, 1, seed + y) - 0.5) * 8)
        w = 4 + int(hash01(i, 2, seed) * 6)
        h = 2 + int(hash01(i, 3, seed) * 3)
        done = stone(p, sx, sy, w, h, seed + i, ramp=rocks[int(hash01(i, 4, seed) * len(rocks))], k=1)
        for (px, py) in list(done)[:: 7]:
            if hash01(px, py, seed + 5) < 0.4:
                p.put(_pt(p, px, py) | _pt(p, px + 1, py), 'clay_warm', 4)
    tuft(p, x + 2, y + 4, seed + 6)


GORSE_FORMS = ('dome', 'low', 'tall', 'pair')


def gorse(seed=0, w=None, form=None):
    """A gorse bush on the cliff top: a mass of dark spiny clumps lit on the upper west,
    yellow flowers in pairs over the lit side, a dark skirt at its foot. Four forms (a
    dome, a low wind-pruned cushion leaning east, a tall clump, a pair of crowns grown
    together) and sizes from 8 to 26 wide, so a cluster never repeats one bush."""
    form = form or GORSE_FORMS[int(hash01(seed, 3, 29) * len(GORSE_FORMS))]
    w = w or 8 + int(hash01(seed, 0, 29) * 18)
    ratio = {'dome': 0.72, 'low': 0.45, 'tall': 1.0, 'pair': 0.62}[form]
    h = max(6, int(w * ratio))
    sp = Sprite(w + 6, h + 4, (w + 6) // 2, h + 1)
    cx, cy = sp.fx, sp.fy - h * 0.5
    clump = (fbm(sp.x, sp.y, 3, seed) - 0.5) * 0.5
    lobes = [(cx, cy, w / 2.0, h / 2.0)]
    if form == 'low':
        lobes = [(cx + w * 0.08, cy + h * 0.1, w / 2.0, h / 2.0)]
    if form == 'pair':
        lobes = [(cx - w * 0.2, cy + h * 0.05, w * 0.32, h * 0.5), (cx + w * 0.2, cy - h * 0.05, w * 0.34, h * 0.52)]
    shape = np.zeros(sp.m.shape, bool)
    lam = np.full(sp.m.shape, -9.0)
    for (lx, ly, rx, ry) in lobes:
        u, v = (sp.x + 0.5 - lx) / rx, (sp.y + 0.5 - ly) / ry
        if form == 'low':
            v = v + 0.25 * u                                  # pruned by the west wind: higher in the lee
        inside = (u * u + v * v <= 1 + clump) & (sp.y <= sp.fy)
        l_ = light_of(u, v, 0.3) + clump * 0.8
        lam = np.where(inside & (l_ > lam), l_, lam)
        shape |= inside
    tone = tone_of(lam, (0.45, 0.0, -0.4))
    fam = np.where(fbm(sp.x, sp.y, 4, seed + 1) > 0.5, IDX['leaf_cool'], IDX['leaf'])
    sp.put(shape, fam, np.maximum(1, tone - 1))
    fl = shape & (tone >= 3) & (hash01(sp.x // 2, sp.y, seed + 2) < (0.3 if form != 'tall' else 0.16))
    sp.put(fl, 'grass_warm', 5)
    sp.put(shift(fl, 1, 0, False) & shape & ~fl, 'sand_warm', 4)
    sp.put(shape & (sp.y >= sp.fy - 1), 'leaf', 0)
    return sp, sp.blob_shadow(w * 0.55, max(3, h * 0.3))


def sea_turf(p: Plot, m, seed=0, thrift=1.0, heathy=0.35):
    """The cliff top's short sea turf: broad calm patches of the grass ramps, darker where
    the ground is damp, short tufts gathered towards the edges, thrift cushions in flower and
    sea campion in drifts where the salt wind keeps the turf short, and inland of them
    cushions of heath and the odd slab of bedrock."""
    m = np.asarray(m, bool)
    base(p, m, [('grass_cool', 0.35), ('grass', 0.45), ('grass_warm', 0.2)], seed, 11, tone=3, light=0.76, dark=0.32)
    damp = m & (fbm(p.x, p.y, 34, seed + 11) < 0.36)
    p.step(damp, -1)
    texture(p, m, seed + 1, swaps=0.035, ups=0.012, downs=0.016, shapes=FLAT)
    if heathy:
        hm = m & (fbm(p.x, p.y, 28, seed + 12) > 1 - heathy * 0.5) & (edge_dist(m, 16) >= 16)
        heath(p, hm & (fbm(p.x, p.y, 6, seed + 13) > 0.42), seed + 14)
    near = m & (edge_dist(m, 12) < 12)
    for (x, y) in _scatter(near, 55, seed + 2):
        tuft(p, x, y, seed + 3, 'grass_warm' if (x + y) % 3 else 'grass')
    for (x, y) in _scatter(m & ~near, 100, seed + 4):           # tufts in clumps, the open between them calm
        for j in range(3 + int(hash01(x, y, seed + 20) * 4)):
            tx = x + int((hash01(x, j, seed + 21) - 0.5) * 9)
            ty = y + int((hash01(y, j, seed + 22) - 0.5) * 5)
            if 0 <= tx < p.w and 0 <= ty < p.h and m[ty, tx]:
                tuft(p, tx, ty, seed + 5 + j, 'grass_cool' if (tx * 7 + ty) % 3 else 'grass_warm')
    for (x, y) in _scatter(m & ~near, 150, seed + 17):          # bird's-foot trefoil and eyebright in pairs
        c = ('grass_warm', 5) if hash01(x, y, seed + 18) < 0.8 else ('snow', 4)
        if not p.solid[y, x]:
            p.put(_pt(p, x, y) | _pt(p, x + 1, y), *c)
            p.put(_pt(p, x, y + 1), 'grass_cool', 1)
    drift = m & (fbm(p.x, p.y, 30, seed + 6) > 0.55)
    lip = m & (edge_dist(m, 24) < 24) & ~shift(m, 0, -24, True)      # the last 24 px before a southern rim
    for (x, y) in _scatter(lip, int(60 / max(0.1, thrift)), seed + 19):
        cushion(p, x, y, seed + 8, 'berry' if hash01(x, y, seed + 9) < 0.8 else 'snow')
    for (x, y) in _scatter(drift & ~lip, int(260 / max(0.1, thrift)), seed + 7):
        cushion(p, x, y, seed + 8, 'berry' if hash01(x, y, seed + 9) < 0.75 else 'snow')
    despeckle(p, m)
    for (x, y) in _scatter(m & (edge_dist(m, 20) >= 20), 9000, seed + 15):
        outcrop(p, x, y, seed + 16)


def marram(p: Plot, x, y, seed=0):
    """A clump of marram grass on sand: blades fanning out of a dark heart, lit on their west
    sides, the sand scooped a tone down in the clump's lee to the east."""
    n = 4 + int(hash01(x, y, seed) * 3)
    for i in range(n):
        lean = (i - n / 2.0) * 0.6
        h = 4 + int(hash01(x + i, y, seed + 1) * 4)
        for j in range(h):
            px, py = int(round(x + i * 0.8 + lean * j / h * 2)), y - j
            if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
                p.f[py, px] = IDX['grass_warm']
                p.t[py, px] = 5 if j == h - 1 else (4 if px < x + n * 0.4 else 3) if j > 1 else 2
    for dx in range(n, n + 3):
        cast_px(p, [(x + dx, y), (x + dx - 1, y + 1)], 1)


def dune(p: Plot, m, seed=0, density=1.0):
    """A marram dune: warm dry sand in calm patches, wind ripples lying across the wind (from
    the west) in short broken crests, marram clumps thick on the hummocks and thinning into
    bare sand, a stalk or two of driftwood."""
    m = np.asarray(m, bool)
    base(p, m, [('sand_warm', 0.45), ('sand', 0.4), ('sand_cool', 0.15)], seed, 13, tone=4, light=0.78, dark=0.3)
    rip = m & (((p.x * 0.25 + p.y + (fbm(p.x, p.y, 20, seed + 1) - 0.5) * 10).astype(int) % 6) == 0)
    rip &= hash01(p.x // 7, p.y // 6, seed + 2) < 0.55
    p.step(rip, 1)
    p.step(shift(rip, 0, 1, False) & m & ~rip, -1)
    hum = m & (fbm(p.x, p.y, 26, seed + 3) > 0.5)
    for (x, y) in _scatter(hum, int(80 / density), seed + 4):
        marram(p, x, y, seed + 5)
    for (x, y) in _scatter(m & ~hum, int(400 / density), seed + 6):
        marram(p, x, y, seed + 7)
    despeckle(p, m)


# --- the shore ------------------------------------------------------------------------------------
def shell(p: Plot, x, y, seed=0):
    """A shell on the sand: two px of white and a pale pink or cream, its shade a px."""
    c = ('berry', 5) if hash01(x, y, seed) < 0.35 else ('sand_warm', 5)
    for (dx, dy, f, t) in ((0, 0, 'snow', 5), (1, 0) + c):
        if 0 <= x + dx < p.w and 0 <= y + dy < p.h and not p.solid[y + dy, x + dx]:
            p.f[y + dy, x + dx], p.t[y + dy, x + dx] = IDX[f], t
    cast_px(p, [(x, y + 1), (x + 1, y + 1)], 1)


def weed_clump(p: Plot, x, y, seed=0):
    """Wrack: a tangle of dark bladderwrack 3 to 6 px, its lit fronds a tone up."""
    w = 3 + int(hash01(x, y, seed) * 4)
    for i in range(w):
        for j in range(2 + (i % 2)):
            if hash01(x + i, y + j, seed + 1) < 0.8:
                px, py = x + i, y + j - 1
                if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
                    p.f[py, px] = IDX['leaf_cool'] if (i + j) % 3 else IDX['grass_warm']
                    p.t[py, px] = 2 if j == 0 else 1


def stick(p: Plot, x, y, seed=0, n=None):
    """A stick of driftwood lying on the sand: silvered, lit along its top, its shadow under."""
    n = n or 4 + int(hash01(x, y, seed) * 5)
    slope = 1 if hash01(x, y, seed + 1) < 0.5 else 0
    for i in range(n):
        px, py = x + i, y + (i * slope) // 4
        if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
            p.f[py, px] = IDX['bleached_cool'] if i % 4 else IDX['timber_cool']
            p.t[py, px] = 4 if i < n - 1 else 3
            if py + 1 < p.h and not p.solid[py + 1, px]:
                p.f[py + 1, px], p.t[py + 1, px] = IDX['bleached_cool'], 2
        cast_px(p, [(px + 1, py + 2)], 1)


def footprints(p: Plot, pts, seed=0, m=None, every=7):
    """A walker's prints across soft sand: pairs of small dents left and right of the line,
    each a tone down with its lit back edge, every few px."""
    c = spline(pts, every / 2.0)
    d = np.gradient(c, axis=0)
    d /= np.maximum(1e-9, np.hypot(d[:, 0], d[:, 1]))[:, None]
    for i in range(0, len(c), 2):
        side = 1 if (i // 2) % 2 else -1
        x = int(c[i, 0] - d[i, 1] * side * 2)
        y = int(c[i, 1] + d[i, 0] * side * 2)
        if not (0 <= x < p.w - 1 and 0 <= y < p.h - 1) or (m is not None and not m[y, x]) or p.solid[y, x]:
            continue
        p.step(_pt(p, x, y) | _pt(p, x + 1, y), -1)
        p.step(_pt(p, x, y + 1), 1)


def beach(p: Plot, m, water, seed=0, wrack=1.0):
    """A sand beach above the swash: dry pale sand in calm wide patches and a few wind
    ripples high up, the wrack line where the last high tide left weed, sticks and shells
    (lying along the shore), a band of firmer damp sand a tone down below it. The swash and
    wet sand at the water are the surf's (`surf`)."""
    m = np.asarray(m, bool)
    d = dist_to(water, 80)
    base(p, m, [('sand', 0.45), ('sand_warm', 0.33), ('sand_cool', 0.22)], seed, 14, tone=3, light=0.74, dark=0.3)
    dry = m & (d > 34 + (fbm(p.x, p.y, 18, seed + 1) - 0.5) * 16)
    p.step(dry & (fbm(p.x, p.y, 11, seed + 2) > 0.45), 1)
    damp = m & (d < 20 + (fbm(p.x, p.y, 14, seed + 3) - 0.5) * 8)
    p.f[damp & (FAMILY[p.f] == IDX['sand'])] = IDX['sand_cool']
    p.step(damp & (d >= 7) & (d < 15 + (fbm(p.x, p.y, 10, seed + 16) - 0.5) * 6), -1)   # damp sand above the swash
    texture(p, m, seed + 4, swaps=0.12, ups=0.035, downs=0.035)
    rip = dry & (((p.x * 0.3 + p.y + (fbm(p.x, p.y, 40, seed + 5) - 0.5) * 16).astype(int) % 9) == 0)
    rip &= hash01(p.x // 34, p.y // 9, seed + 6) < 0.5
    p.step(rip, 1)
    p.step(shift(rip, 0, 1, False) & m & ~rip, -1)
    wl = 26 + (fbm(p.x, p.y, 40, seed + 7) - 0.5) * 8
    line = m & (np.abs(d - wl) < 3.5)
    for (x, y) in _scatter(line, int(26 / max(0.1, wrack)), seed + 8, margin=0):
        r = hash01(x, y, seed + 9)
        if r < 0.5:
            weed_clump(p, x, y, seed + 10)
        elif r < 0.7:
            stick(p, x, y, seed + 11)
        else:
            shell(p, x, y, seed + 12)
    for (x, y) in _scatter(m & (d > 8) & ~line, 300, seed + 13):
        shell(p, x, y, seed + 14) if hash01(x, y, seed + 15) < 0.6 else pebble(p, x, y, ROCK[(x + y) % len(ROCK)], 2, 2, k=1)
    despeckle(p, m)
    p.walk |= m & ~p.solid & ~p.hazard


def shingle(p: Plot, m, water, seed=0):
    """A shingle beach: rounded pebbles packed close, small at the water and growing to the
    storm ridge where the biggest cobbles lie, smaller again behind it; flint grey, sandstone
    buff and the odd slate; wet and a tone down where the swash reaches; dark gaps between."""
    m = np.asarray(m, bool)
    d = dist_to(water, 60)
    base(p, m, [('stone_cool', 0.4), ('stone', 0.3), ('ashlar_cool', 0.3)], seed, 6, tone=2)
    ridge = 18 + (fbm(p.x, p.y, 30, seed + 1) - 0.5) * 8
    cell = 4
    gy, gx = np.mgrid[0:p.h:cell, 0:p.w:cell]
    pts = list(zip(gx.ravel(), gy.ravel()))
    stones = ('stone_warm', 'ashlar', 'bleached', 'ashlar_warm', 'stone', 'slate', 'bleached_cool', 'ashlar_cool')
    for (cx, cy) in pts:
        x = int(cx + hash01(cx, cy, seed + 2) * cell)
        y = int(cy + hash01(cx, cy, seed + 3) * cell)
        if not (0 <= x < p.w and 0 <= y < p.h) or not m[y, x]:
            continue
        dd = float(d[y, x])
        g = 1 - min(1.0, abs(dd - ridge[y, x]) / 22.0)
        w = 3 + int(g * 3 + hash01(x, y, seed + 4) * 1.6)
        h = max(2, w - 1 - int(hash01(x, y, seed + 5) * 1.5))
        if hash01(x, y, seed + 6) > 0.7 + 0.3 * g:
            continue
        ramp = stones[int(hash01(x, y, seed + 7) * len(stones))]
        done = pebble(p, x, y, ramp, w, h, shadow=True, k=1)
        if hash01(x, y, seed + 9) < 0.5:
            for (px, py) in done:
                p.t[py, px] = min(5, p.t[py, px] + 1)
        if dd < 8:
            for (px, py) in done:
                p.t[py, px] = max(1, p.t[py, px] - 1)
    crest = m & (np.abs(d - ridge) < 1.0) & (hash01(p.x // 4, 0, seed + 8) < 0.5)
    p.step(crest & (p.t < 4), 1)
    despeckle(p, m)
    p.walk |= m & ~p.hazard
    p.solid &= ~m


def grade(p: Plot, sand, shing, water, seed=0, reach=16):
    """Where shingle meets sand: pebbles thrown out over the sand for `reach` px, thinning
    with distance, smaller as they go, and sand blown into the shingle's last few px."""
    sand, shing = np.asarray(sand, bool), np.asarray(shing, bool)
    d = dist_to(shing, reach + 1)
    stones = ('stone_warm', 'ashlar', 'bleached', 'stone', 'slate', 'ashlar_cool')
    for (x, y) in _scatter(sand & (d <= reach), 10, seed, margin=0):
        k = d[y, x] / float(reach)
        if hash01(x, y, seed + 1) > (1 - k) ** 1.5 * 0.9:
            continue
        w = 2 + int((1 - k) * 2.5 * hash01(x, y, seed + 2) + 0.5)
        pebble(p, x, y, stones[int(hash01(x, y, seed + 3) * len(stones))], w, max(2, w - 1), shadow=True, k=1)
    din = dist_to(sand, 6)
    blown = shing & (din <= 5) & (hash01(p.x // 2, p.y // 2, seed + 4) < (6 - din) / 7.0)
    p.put(blown, 'sand_cool', 3)


def platform(p: Plot, m, water, seed=0, rock='stone'):
    """A wave-cut rock platform at the cliff's foot: the bedding of the rock in long low
    steps lying with the coast, each step's edge a dark fissure over a lit lip, cracks
    across them; drier and paler up the shore, wet, green with algae and black with weed
    towards the sea, barnacles and limpets in pairs where the waves wash."""
    m = np.asarray(m, bool)
    d = dist_to(water, 40)
    base(p, m, [(rock, 0.45), (f'{rock}_warm', 0.3), (f'{rock}_cool', 0.25)], seed, 9, tone=3)
    bed = p.y + p.x * 0.28 + (fbm(p.x, p.y, 26, seed + 1) - 0.5) * 22
    step_i = np.floor(bed / 7.0).astype(int)
    edge = m & (step_i != shift(step_i, 0, 1, -99)) & (hash01(p.x // 6, step_i, seed + 2) < 0.8)
    p.t[edge & (p.t < EDGE_T)] = 1
    lip = shift(edge, 0, 1, False) & m & ~edge
    p.step(lip, 1)
    lip2 = shift(lip, 0, 1, False) & m & ~edge & ~lip
    p.step(lip2 & (hash01(p.x // 2, p.y, seed + 3) < 0.5), 1)
    crack = m & (((p.x + (fbm(p.x, p.y, 8, seed + 4) - 0.5) * 6).astype(int) % 23) == 0) & \
        (hash01(p.x // 23, step_i, seed + 5) < 0.4)
    p.t[crack & (p.t < EDGE_T)] = 1
    texture(p, m, seed + 6, swaps=0.08, ups=0.02, downs=0.03)
    wet = m & (d < 12 + (fbm(p.x, p.y, 15, seed + 7) - 0.5) * 10)
    p.step(wet, -1, lo=1)
    alg = wet & (fbm(p.x, p.y, 7, seed + 8) > 0.58)
    stamp(p, alg, 0.5, seed + 9, SMALL, ramp='grass_cool', tone=2, same_family=False)
    weed = m & (d < 5) & (fbm(p.x, p.y, 5, seed + 10) > 0.45)
    stamp(p, weed, 0.6, seed + 11, SMALL, ramp='leaf_cool', tone=1, same_family=False)
    for (x, y) in _scatter(m & (d < 18) & ~weed, 70, seed + 12, margin=1):
        if not p.solid[y, x]:
            p.put(_pt(p, x, y) | _pt(p, x + 1, y), 'bleached', 5 if (x + y) % 2 else 4)
    p.walk |= m & ~p.hazard


def rock_pools(p: Plot, plat, pools, seed=0):
    """Pools left in the platform by the tide, each an organic hollow: under its north rim
    the platform's own little face in shade, its south rim a lit lip; clear shallow water a
    tone over the floor's sand and stones, weed fronds, red anemones and an orange starfish
    showing through. Not walkable."""
    plat = np.asarray(plat, bool)
    allw = np.zeros(plat.shape, bool)
    for i, (cx, cy, rx, ry) in enumerate(pools):
        w = blob(cx, cy, rx, ry, plat.shape, seed + i, wob=0.22, lobes=5) & erode(plat, 3)
        if not w.any():
            continue
        allw |= w
        dd = edge_dist(w, 6)
        floor = fbm(p.x, p.y, 6, seed + 20 + i)
        p.put(w, 'lagoon', 3)
        p.put(w & (dd >= 3), 'lagoon', 2)
        p.put(w & (dd >= 3) & (floor > 0.6), 'lagoon_warm', 3)       # sand on the floor
        p.put(w & (dd >= 5) & (floor < 0.3), 'lagoon_cool', 1)       # the deep middle
        north = w & ~shift(w, 0, 1, False)                           # the water's first row
        p.put(north, 'lagoon_cool', 1)
        p.put(shift(north, 0, 1, False) & w & ~north, 'lagoon_cool', 2)
        fr = shift(w, 0, 1, False) & ~w & plat                       # the rock over it: its little face
        p.put(fr, f'{p_rock(p, fr)}', 1)
        p.t[shift(fr, 0, 1, False) & ~w & plat & ~fr] = 2
        south = w & ~shift(w, 0, -1, False)
        lipm = shift(south, 0, 1, False) & ~w & plat
        p.step(lipm, 1)
        p.put(south, 'lagoon_warm', 4)
        for (x, y) in _scatter(w & (dd >= 2), 22, seed + 30 + i, margin=0):
            r = hash01(x, y, seed + 31)
            if r < 0.35:
                for j in range(3):
                    if w[min(p.h - 1, y + j), x]:
                        p.put(_pt(p, x + (j % 2), y + j), 'leaf', 3 - (j > 0))
            elif r < 0.55:
                p.put(_pt(p, x, y) | _pt(p, x + 1, y), 'berry', 4)
                p.put(_pt(p, x, y + 1) | _pt(p, x + 1, y + 1), 'berry', 2)
            elif r < 0.7:
                p.put(_pt(p, x, y) | _pt(p, x + 1, y), 'lagoon_cool', 1)
                p.put(_pt(p, x, y - 1), 'lagoon', 4)
        sx, sy = cx - rx // 3, cy
        if w[sy, sx]:
            for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                p.put(_pt(p, sx + dx, sy + dy), 'clay_warm', 4 if dy <= 0 else 3)
    p.wet |= allw
    p.walk &= ~allw
    p.hazard |= allw
    return allw


def p_rock(p: Plot, m):
    """The commonest ramp under a mask (to shade a pool's rim in the platform's own rock)."""
    vals = p.f[np.asarray(m, bool)]
    if not len(vals):
        return 'stone'
    return NAMES[int(np.bincount(vals).argmax())]


# --- the sea ----------------------------------------------------------------------------------------
def sea(p: Plot, m, land, seed=0, deep=1.0):
    """The sea as Sea of Stars paints it: one calm plane in soft depth bands lying along the
    shore (pale lagoon over sand at the edge, teal over the shelf, deep blue beyond), each
    band's edge wandering; in the shallows the sand floor's ripples, stones and dark weed
    showing through; swell lines lying along the shore in long broken dashes, lit on top
    with their shade under; pairs of glints out in the deep."""
    m = np.asarray(m, bool)
    d = dist_to(land, 160).astype(np.float64)
    dd = d * deep + (fbm(p.x, p.y, 26, seed) - 0.5) * 16
    bands = ((7, 'lagoon_warm', 4), (16, 'lagoon', 4), (30, 'lagoon', 3), (48, 'lagoon_cool', 2),
             (72, 'water', 2), (110, 'water_cool', 2), (1e9, 'water_cool', 1))
    lo = -1e9
    for hi, ramp, tone in bands:
        sel = m & (dd >= lo) & (dd < hi)
        p.put(sel, ramp, tone)
        lo = hi
    # soft patches of light and shade, one field in five steps: in the troughs the cool
    # sibling a tone down, then the cool sibling, the body, the warm sibling, and where the
    # light catches the swell the warm sibling a tone up
    q = fbm(p.x, p.y * 1.4, 24, seed + 12)
    cuts = np.quantile(q[m], (0.16, 0.38, 0.62, 0.84)) if m.any() else (0.3, 0.45, 0.55, 0.7)
    cl = np.digitize(q, cuts)
    p.f[m & (cl <= 1)] = COOL[p.f[m & (cl <= 1)]]
    p.f[m & (cl >= 3)] = WARM[p.f[m & (cl >= 3)]]
    p.step(m & (cl == 0), -1, lo=0)
    p.step(m & (cl == 4), 1)
    shallow = m & (dd < 30)
    rip = shallow & (((p.x * 0.35 + p.y + (fbm(p.x, p.y, 12, seed + 2) - 0.5) * 8).astype(int) % 5) == 0)
    rip &= hash01(p.x // 5, p.y // 5, seed + 3) < 0.5
    p.step(rip, 1)
    # a few soft patches of the floor (stones, weed) showing through the shallows only
    for (x, y) in _scatter(m & (dd > 8) & (dd < 30), 900, seed + 4):
        s = blob(x, y, 4 + hash01(x, y, seed) * 7, 2 + hash01(x, y, seed + 1) * 3, p.f.shape, seed, wob=0.25) & m
        p.step(s, -1, lo=1)
    weed = m & (dd > 12) & (dd < 30) & (fbm(p.x, p.y, 16, seed + 5) > 0.78)
    p.step(weed, -1, lo=1)
    phase = dd + (fbm(p.x, p.y, 10, seed + 6) - 0.5) * 3
    k = np.floor(phase / 13.0).astype(int)
    crest = m & (dd > 18) & (k != shift(k, 0, 1, -99))
    seg = hash01((p.x + k * 37) // 23, k, seed + 7) < 0.3
    crest &= seg
    p.step(crest, 1)
    p.step(shift(crest, 0, 1, False) & m & ~crest, -1, lo=0)
    deepm = m & (dd >= 48)
    swell = fbm(p.x * 0.6, p.y * 1.4, 22, seed + 11)
    p.step(deepm & (swell > 0.64), 1)
    p.step(deepm & (swell < 0.3), -1, lo=0)
    gl = m & (dd > 50) & (hash01(p.x // 2, p.y, seed + 8) < 0.006)
    p.step(gl | (shift(gl, 1, 0, False) & m), 2)
    ripples(p, m, seed + 9, every=140)
    despeckle(p, m)
    p.wet |= m
    p.walk &= ~m
    p.hazard |= m
    p.solid &= ~m


def ripples(p: Plot, m, seed=0, every=26):
    """The water's small movement, as Sea of Stars draws it all over its sea: short ripple
    marks 3 to 6 px long lying across the swell, each lit a tone up with a tone down under
    it, and finer sibling patches (warm where the light catches, cool in the troughs), so
    open water is never one flat colour."""
    m = np.asarray(m, bool)
    for (x, y) in _scatter(m, every, seed + 1, margin=1):
        n = 4 + int(hash01(x, y, seed + 2) * 5)
        bend = 1 if hash01(x, y, seed + 3) < 0.5 else -1
        for i in range(n):
            yy = y + (bend if i in (0, n - 1) else 0)
            if 0 <= x + i < p.w and 0 <= yy + 1 < p.h and m[yy, x + i] and not p.solid[yy, x + i]:
                p.t[yy, x + i] = min(5, p.t[yy, x + i] + 1)
                if m[yy + 1, x + i] and i not in (0, n - 1):
                    p.t[yy + 1, x + i] = max(0, p.t[yy + 1, x + i] - 1)


def surf(p: Plot, water, seed=0, beachy=None):
    """The surf along every shore: a white foam line hugging the land, broken now and then;
    against rock a dark wet ring outside it and a second broken line of lace a few px out
    (Sea of Stars); on a beach (`beachy`, the sand) a pale swash with two loose lines of lace
    over it, and on the sand the wet band a tone down, its contact darkest, the last wave's
    reach a pale line."""
    water = np.asarray(water, bool)
    land = ~water
    dw = dist_to(land, 16)
    dl = dist_to(water, 16)
    beachy = np.zeros(water.shape, bool) if beachy is None else np.asarray(beachy, bool)
    sandy = water & (dist_to(beachy, 14) < 12)
    warp = (fbm(p.x, p.y, 9, seed) - 0.5) * 3
    gap = hash01((p.x + p.y) // 7, 0, seed + 1) < 0.15
    foam = water & (dw <= np.where(sandy, 2, 1)) & ~gap
    p.put(foam, 'snow', 5)
    p.put(water & (dw <= 1) & gap, 'snow_cool', 3)
    ring = water & ~sandy & (dw >= 2) & (dw <= 3)
    p.step(ring, -1, lo=0)
    lace = water & ~sandy & (np.abs(dw + warp - 6) < 0.7) & (hash01((p.x - p.y) // 6, 1, seed + 2) < 0.55)
    p.put(lace, 'snow_cool', 4)
    swash = sandy & (dw >= 3) & (dw <= 7 + warp)
    p.put(swash, 'lagoon_warm', 5)
    for off, keep in ((9, 0.6), (14, 0.4)):
        l2 = sandy & (np.abs(dw + warp - off) < 0.7) & (hash01((p.x + off) // 8, off, seed + 3) < keep)
        p.put(l2, 'snow', 4)
        p.put(shift(l2, 0, 1, False) & sandy & ~l2 & (dw > 2), 'lagoon_warm', 4)
    wet = beachy & (dl <= 7 + warp)
    p.f[wet] = IDX['sand_cool']
    p.t[wet] = 2
    p.t[beachy & (dl <= 1)] = 1
    reach = beachy & (np.abs(dl - 8 - warp) < 0.6) & (hash01(p.x // 9, 2, seed + 4) < 0.6)
    p.put(reach, 'sand', 4)
    for (x, y) in _scatter(wet & (dl >= 3), 160, seed + 5, margin=0):
        shell(p, x, y, seed + 6)
    p.wet |= water


def reef(p: Plot, rocks, seed=0, ramp='basalt'):
    """Reef rocks awash: low rounded tops in the rock's dark ramp, lit on their upper west,
    weed black at the water; the surf draws their foam. Returns the rocks' mask (land)."""
    m = np.zeros(p.f.shape, bool)
    for i, (x, y, rx, ry) in enumerate(rocks):
        b = blob(x, y, rx, ry, p.f.shape, seed + i, wob=0.25, lobes=5)
        m |= b
        u, v = (p.x + 0.5 - x) / max(1, rx), (p.y + 0.5 - y) / max(1, ry)
        lump = (fbm(p.x, p.y, max(3, rx // 2), seed + i) - 0.5) * 0.9      # bulges across the rock
        tone = tone_of(light_of(u, v, 0.45) + lump, (0.5, 0.05, -0.45))
        p.f[b] = IDX[ramp] if hash01(i, 0, seed) < 0.6 else IDX[f'{ramp}_warm']
        p.t[b] = tone[b]
        p.put(b & (tone == 4) & (lump > 0.25), 'basalt_warm', 5)
        low = b & ~shift(b, 0, -2, False)
        p.put(low, 'leaf_cool', 1)
        p.put(b & ~low & ~shift(b, 0, -4, False) & (hash01(p.x // 2, p.y, seed + i) < 0.3), 'bleached', 4)
    p.wet &= ~m
    p.hazard |= m
    p.walk &= ~m
    return m


def breakers(p: Plot, line_pts, seed=0, width=5):
    """Waves breaking along the reef's seaward side: a broken white crest a few px deep, lit
    on its top, its foam trailing landward in lace; the water behind it churned a tone up."""
    ch = Channel(p, line_pts, reach=24)
    n = ch.n + (fbm(ch.s, 0, 20, seed) - 0.5) * 4
    on = hash01(ch.s.astype(int) // 26, 0, seed + 1) < 0.72
    crest = ch.near & on & (np.abs(n) < width / 2.0) & p.wet
    p.put(crest, 'snow', 4)
    p.put(crest & (n < -width / 2.0 + 1.5), 'snow', 5)
    p.put(crest & (n > width / 2.0 - 1.2), 'snow_cool', 3)
    churn = ch.near & on & (n >= width / 2.0) & (n < width / 2.0 + 7) & p.wet
    p.step(churn & (hash01(p.x // 2, p.y // 2, seed + 2) < 0.45), 1)
    lace = ch.near & on & (np.abs(n - width / 2.0 - 4) < 0.7) & p.wet & (hash01(p.x // 5, 3, seed + 3) < 0.6)
    p.put(lace, 'snow_cool', 4)


def far_isle(p: Plot, x, y, rx, ry, seed=0, haze=0):
    """An isle on the horizon (drawn, never walked): a silhouette with a ridge that rises
    and falls, its lit top in the cool greens (lighter on its west), a small cliff face of
    pale cool rock under its south rim with a darker foot, a faint line of surf; only the
    middle tones, and `haze` (0, 1, 2) steps it back towards the horizon."""
    h, w = p.f.shape
    u = (p.x + 0.5 - x) / float(rx)
    ridge = y - ry * np.clip(1 - u * u, 0, 1) ** 0.6 * (0.75 + 0.5 * fbm(p.x, 0 * p.y, 14, seed))
    cliff_h = 3 + 3 * fbm(p.x, 0 * p.y, 9, seed + 1)
    rim = y - 2 + (fbm(p.x, 0 * p.y, 11, seed + 2) - 0.5) * 3
    inside = np.abs(u) < 1
    top = inside & (p.y >= ridge) & (p.y < rim)
    face = inside & (p.y >= rim) & (p.y < rim + cliff_h)
    lift = haze
    p.put(top, 'leaf_cool', min(4, 2 + lift))
    p.put(top & (u < -0.15), 'leaf_cool', min(5, 3 + lift))
    p.put(top & (p.y < ridge + 2) & (u < 0.3), 'grass_cool', min(5, 4 + lift))
    stamp(p, top, 0.18, seed + 3, SMALL, dt=1)
    p.put(face, 'stone_cool', min(4, 3 + lift))
    p.put(face & (u > 0.2), 'stone_cool', min(4, 2 + lift))
    p.put(face & (p.y >= rim + cliff_h - 1.5), 'stone_cool', min(3, 1 + lift))
    b = top | face
    foam = shift(face, 0, -1, False) & ~b & p.wet
    p.put(foam & (hash01(p.x // 3, 0, seed + 4) < 0.7), 'snow_cool', 3 + min(1, lift))
    p.solid |= b
    p.walk &= ~b
    return b


def south_edge(p: Plot, y0, seed=0, isles=None):
    """The layered south edge (plan 5.5; the brief: the sea is the edge, far islands beyond):
    the reef (`reef`, `breakers`, placed by the scene) holds the first layer; past it the
    deep blue; then far isles on the horizon, the farther one hazier; towards the edge the
    sea lifts in soft steps, its families turned to their cool siblings and its deepest
    tones raised, so the world fades into haze instead of stopping."""
    depth = p.h - y0
    t = np.clip((p.y - y0 + (fbm(p.x, p.y, 18, seed) - 0.5) * 30) / float(depth), 0, 1)
    m = (t > 0) & p.wet
    lift = m & (p.t < EDGE_T)
    p.t[lift & (t > 0.35)] = np.maximum(p.t[lift & (t > 0.35)], 2)
    p.t[lift & (t > 0.7)] = np.maximum(p.t[lift & (t > 0.7)], 3)
    cool = m & (t > 0.2) & ~GLOW[p.f]
    p.f[cool] = COOL[p.f[cool]]
    for i, (x, y, rx, ry) in enumerate(isles or ()):
        far_isle(p, x, y, rx, ry, seed + 10 * i, haze=1 if i % 2 else 0)


# --- built: the quay, its sea wall, a pier, a slipway --------------------------------------------
def setts(p: Plot, m, seed=0, ramps=('stone_warm', 'ashlar', 'stone', 'ashlar_warm', 'stone_cool'), course=4):
    """Granite setts laid in courses: each sett 5 to 8 px long, lit along its top and west
    edge, its east and south joints dark, the courses broken bond; grass in a joint now and
    then; worn paler where feet go."""
    m = np.asarray(m, bool)
    row = p.y // course
    off = (hash01(row, 0, seed) * 8).astype(int)
    ln = 5 + (hash01((p.x + off) // 6, row, seed + 1) * 3).astype(int)
    idx = (p.x + off) // ln
    fam = np.array([IDX[r] for r in ramps])[(hash01(idx, row, seed + 2) * len(ramps)).astype(int)]
    p.f[m] = fam[m]
    r = p.y % course
    first = (idx != shift(idx, 1, 0, -1))
    last = (idx != shift(idx, -1, 0, -1))
    lit = hash01(idx, row, seed + 6)                # setts are domed a little: some catch more light
    t = np.where(r == 0, 4, np.where(r == course - 1, 2, np.where(lit < 0.4, 4, np.where(lit < 0.85, 3, 2))))
    t = np.where((r == 0) & (lit < 0.2), 5, t)
    t = np.where(first & (r < course - 1), 4, t)
    t = np.where(last, 2, t)
    p.t[m] = t[m]
    p.t[m & (r == course - 2) & ~last & (hash01(idx, row, seed + 3) < 0.5)] = 3
    worn = m & (fbm(p.x, p.y, 16, seed + 4) > 0.62) & (p.t == 3)
    p.t[worn] = 4
    joint = m & ((r == course - 1) | last) & (hash01(p.x // 2, p.y, seed + 5) < 0.05)
    p.put(joint, 'grass_cool', 3)
    p.walk |= m & ~p.hazard
    p.solid &= ~m


def masonry(p: Plot, R: Relief, m, seed=0, ramps=('ashlar', 'ashlar_warm', 'ashlar_cool', 'stone_warm'),
            course=6, water=None):
    """A harbour's sea wall as a built south face: courses of dressed blocks 6 px high and 9
    to 16 long in broken bond, each block lit along its top and west arris, its body in two
    tones, dark at its east and bed joints; a coping of long stones on the rim, lit on top,
    throwing a dark row under its nose; below the tide line (where the wall stands in the
    water) the blocks wet a tone down, green with weed on the lowest courses, barnacles in
    pairs, rust running from the iron."""
    fc = R.face & np.asarray(m, bool)
    if not fc.any():
        return fc
    d, fh = R.depth, R.fh
    row = d // course
    off = (hash01(row, 1, seed) * 10).astype(int)
    ln = 9 + (hash01((p.x + off) // 12, row, seed + 1) * 8).astype(int)
    idx = (p.x + off) // ln
    fam = np.array([IDX[r] for r in ramps])[(hash01(idx, row, seed + 2) * len(ramps)).astype(int)]
    r = d % course
    first = idx != shift(idx, 1, 0, -1)
    last = idx != shift(idx, -1, 0, -1)
    hb = hash01(idx, row, seed + 3)
    body = np.where(hb < 0.3, 2, np.where(hb > 0.85, 4, 3))
    t = np.where(r == 0, 4, np.where(r == course - 1, 1, body))
    t = np.where(first & (r < course - 1) & (r > 0), 4, t)
    t = np.where(last, 1, t)
    p.f[fc] = fam[fc]
    p.t[fc] = t[fc]
    # weather: dark damp streaks run down from the coping in pairs of px, a few blocks
    # spalled at their arris, a lighter patch where a block was renewed
    streak = fc & (d >= 4) & (hash01(p.x // 2, 0, seed + 7) < 0.12) & \
        (d < 4 + (hash01(p.x // 2, 1, seed + 8) * 18).astype(int))
    p.put(streak & (p.t >= 2), 'slate_cool', 2)
    spall = fc & first & (r == 1) & (hash01(idx, row, seed + 9) < 0.3)
    p.put(spall | (shift(spall, 1, 0, False) & fc), 'ashlar_cool', 2)
    new = fc & (hash01(idx, row, seed + 10) < 0.05) & ~last & (r > 0) & (r < course - 1)
    p.put(new, 'ashlar_warm', 4)
    cop = fc & (d < 4)
    p.put(cop, 'ashlar_warm', 4)
    p.put(cop & (d == 0), 'ashlar_warm', 5)
    p.put(cop & (d == 3), 'ashlar', 1)
    cj = cop & (((p.x + 7) // 21) != ((p.x + 8) // 21)) & (d < 3)
    p.put(cj, 'ashlar', 2)
    if water is not None:
        up = fh - 1 - d
        col = fc & (up == 0) & shift(np.asarray(water, bool), 0, -1, False)
        for _ in range(14):
            col |= shift(col, 0, -1, False) & fc
        wet = col & (up < 14)
        p.step(wet & (up < 12), -1, lo=1)
        green = wet & (up < 7) & (hash01(p.x // 2, p.y // 2, seed + 4) < 0.55)
        p.put(green & (up < 3), 'leaf_cool', 1)
        p.put(green & (up >= 3), 'grass_cool', 2)
        barn = wet & (up >= 6) & (up < 11) & (hash01(p.x // 2, p.y // 2, seed + 5) < 0.14)
        p.put(barn, 'bleached', 5)
    p.solid |= fc
    p.walk &= ~fc
    return fc


def ring(p: Plot, x, y):
    """A mooring ring on its staple: an iron ring 5 px across, lit on its upper west, a rust
    stain run down the stone under it."""
    for (dx, dy, t) in ((1, 0, 4), (2, 0, 3), (3, 0, 3), (0, 1, 4), (4, 1, 2), (0, 2, 3), (4, 2, 1),
                        (1, 3, 2), (2, 3, 1), (3, 3, 1), (2, 1, 1)):
        p.put(_pt(p, x + dx, y + dy), 'iron', t)
    for j in range(4, 9):
        if hash01(x, j, 3) < 0.8:
            p.put(_pt(p, x + 2, y + j) | _pt(p, x + 3, y + j), 'clay', 2 if j < 7 else 1)


def ladder(p: Plot, R: Relief, x, k=None, seed=0):
    """An iron ladder down a sea wall, set in a recess: two rails, rungs every 4 px lit on
    top, the recess behind it in deep shade, weed on its lowest rungs in the water."""
    col = R.face & (p.x >= x) & (p.x < x + 8)
    if k is not None:
        col &= R.kf == k
    p.put(col, 'ashlar', 0)
    rails = col & ((p.x == x + 1) | (p.x == x + 6))
    p.put(rails, 'iron', 3)
    p.put(rails & (p.x == x + 6), 'iron', 1)
    rung = col & ((R.depth % 4) == 1) & (p.x > x) & (p.x < x + 7)
    p.put(rung, 'iron', 4)
    p.put(shift(rung, 0, 1, False) & col & ~rails, 'iron', 1)
    low = col & (R.fh - 1 - R.depth < 4)
    p.put(low & (hash01(p.x, p.y, seed) < 0.6), 'leaf_cool', 1)


def pier(p: Plot, x0, y0, x1, y1, seed=0, legs=14):
    """A timber pier from the shore out over the water (32 wide): planks laid across in
    three timbers, each lit on its top row with a dark joint under it, nail pairs over the
    stringers, a worn path paler down the middle, a new plank and a gap here and there;
    the stringers along both edges with post heads standing proud; at its seaward end the
    deck's edge, then the piles in the water (lit west, dark east, cross braces, weed at
    the water line and a ring of foam round each); its shadow on the water to the east and
    south. The deck is walkable over the water."""
    w = x1 - x0
    deck = (p.x >= x0) & (p.x < x1) & (p.y >= y0) & (p.y < y1)
    row = (p.y - y0) // 4
    r = (p.y - y0) % 4
    fams = np.array([IDX['timber'], IDX['timber_warm'], IDX['timber_cool']])
    fam = fams[(hash01(row, 0, seed) * 3).astype(int)]
    p.f[deck] = fam[deck]
    t = np.where(r == 0, 4, np.where(r == 3, 1, 3))
    t = np.where((r == 2) & (hash01(p.x // 3, row, seed + 1) < 0.5), 2, t)
    p.t[deck] = t[deck]
    p.solid[deck] = False
    p.wet[deck] = False
    p.hazard[deck] = False
    p.walk[deck] = True
    worn = deck & (np.abs(p.x - (x0 + x1) / 2.0) < w * 0.22) & (r == 1) & (hash01(p.x // 2, row, seed + 2) < 0.6)
    p.step(worn, 1)
    newp = deck & (hash01(row, 3, seed + 3) < 0.08)
    p.f[newp] = IDX['timber_warm']
    p.step(newp & (r < 3), 1)
    gap = deck & (hash01(row, 4, seed + 4) < 0.05) & (r == 3)
    p.t[gap] = 0
    for sx in (x0 + 3, x1 - 4):
        nail = deck & (p.x == sx) & (r == 1)
        p.put(nail | shift(nail, 1, 0, False), 'iron', 3)
    edge = deck & ((p.x < x0 + 2) | (p.x >= x1 - 2))
    p.put(edge & (p.x < x0 + 1), 'timber_cool', 3)
    p.put(edge & (p.x == x0 + 1), 'timber_cool', 2)
    p.put(edge & (p.x >= x1 - 2), 'timber_cool', 1)
    p.t[edge & (p.x == x1 - 1)] = EDGE_T
    for py in range(y0 + 6, y1 - 2, 24):
        for px in (x0 - 1, x1 - 3):
            post = (p.x >= px) & (p.x < px + 4) & (p.y >= py) & (p.y < py + 4)
            p.put(post, 'timber', 3)
            p.put(post & (p.y == py), 'timber', 4)
            p.put(post & (p.x == px + 3), 'timber', 1)
            p.walk &= ~post
    end = (p.x >= x0) & (p.x < x1) & (p.y >= y1) & (p.y < y1 + 3)
    p.put(end, 'timber_cool', 2)
    p.put(end & (p.y == y1), 'timber_cool', 1)
    p.walk &= ~end
    p.solid |= end
    piles = np.zeros(p.f.shape, bool)
    for px in (x0 + 1, x0 + w // 2 - 2, x1 - 5):
        pl = (p.x >= px) & (p.x < px + 4) & (p.y >= y1 + 3) & (p.y < y1 + 3 + legs)
        piles |= pl
        p.put(pl, 'timber', 2)
        p.put(pl & (p.x == px), 'timber', 3)
        p.put(pl & (p.x == px + 3), 'timber', 1)
        p.put(pl & (p.y >= y1 + legs), 'leaf_cool', 1)
        rg = (np.abs(p.x - (px + 1.5)) <= 3) & (p.y == y1 + 3 + legs) & ~pl
        p.put(rg & p.wet, 'snow', 4)
    brace = np.zeros(p.f.shape, bool)
    for j in range(legs - 4):
        for (bx, sgn) in ((x0 + 5, 1), (x1 - 6, -1)):
            xx = bx + sgn * (j * (w // 2 - 6)) // max(1, legs - 4)
            if 0 <= xx < p.w and 0 <= y1 + 4 + j < p.h:
                brace[y1 + 4 + j, xx] = True
    p.put(brace & ~piles, 'timber_cool', 1)
    p.solid |= piles | brace
    sh = (shift(deck | end, 3, 3, False) | shift(piles, 2, 1, False)) & p.wet & ~deck & ~end & ~piles & ~brace
    p.step(sh, -1, lo=0)
    return deck


def stepped_tread(p: Plot, tread, rising='east', seed=0, step=6):
    """A ramp's tread laid as low stone steps across its slope (every `step` px): each
    step's riser faces down the slope, lit when it faces west and dark when it faces east,
    its slab in the stone ramps with a worn middle; the cut's back wall throws its shadow
    over the back of the tread, and grit gathers at the risers' feet."""
    tread = np.asarray(tread, bool)
    if not tread.any():
        return
    xs = np.nonzero(tread.any(0))[0]
    x0, x1 = int(xs.min()), int(xs.max())
    k = ((p.x - x0) // step) if rising == 'east' else ((x1 - p.x) // step)
    pos = ((p.x - x0) % step) if rising == 'east' else ((x1 - p.x) % step)
    fams = np.array([IDX['stone_warm'], IDX['ashlar'], IDX['stone'], IDX['ashlar_warm']])
    fam = fams[(hash01(k, 0, seed) * len(fams)).astype(int)]
    p.f[tread] = fam[tread]
    p.t[tread] = 3
    riser = tread & (pos == 0)
    p.t[riser] = 4 if rising == 'east' else 1
    p.t[tread & (pos == 1)] = 3 if rising == 'east' else 2
    p.t[tread & (pos == step - 1)] = 2
    top = np.full(p.f.shape, 10 ** 6)
    for x in xs:
        ys = np.nonzero(tread[:, x])[0]
        top[:, x] = ys.min()
    rows_in = p.y - top
    shade = tread & (rows_in < 5) & ((rows_in < 3) | (hash01(p.x // 2, p.y, seed + 1) < 0.5))
    p.step(shade, -1, lo=0)
    worn = tread & (rows_in > 7) & (rows_in < 16) & (pos > 1) & (pos < step - 1) & (hash01(p.x // 2, p.y // 2, seed + 2) < 0.5)
    p.step(worn, 1)
    grit = tread & (pos == step - 2) & (hash01(p.x, p.y // 2, seed + 3) < 0.35)
    p.put(grit, 'sand_cool', 2)


def coil(seed=0):
    """A coil of mooring rope on the quay: three turns of hemp lit on their upper west, the
    end trailing out."""
    sp = Sprite(12, 9, 6, 7)
    cx, cy = 5.5, 4.0
    for y in range(9):
        for x in range(12):
            r = math.hypot((x + 0.5 - cx) / 1.25, y + 0.5 - cy)
            if r <= 4.0 and r >= 1.2:
                turn = int(r) % 2
                lit = (x < cx and y < cy + 1)
                sp.px(x, y, 'sand_warm' if turn else 'timber_warm', (4 if lit else 2) if turn else (3 if lit else 1))
    for x in range(9, 12):
        sp.px(x, 7, 'sand_warm', 3)
    return sp, sp.blob_shadow(4, 2)


def fish_crate(seed=0):
    """A fish box: slatted timber, lit on its top rim, the catch silver and blue inside."""
    sp = Sprite(14, 10, 7, 9)
    for y in range(2, 10):
        for x in range(1, 13):
            rim = y == 2 or x in (1, 12)
            if rim:
                sp.px(x, y, 'timber_warm', 4 if (y == 2 and x < 9) else 2)
            elif y < 5:
                sp.px(x, y, 'snow_cool' if (x + y + seed) % 3 else 'water', 4 if (x + y) % 2 else 3)
            else:
                sp.px(x, y, 'timber_warm', 3 if (y % 3) else 1)
    return sp, sp.blob_shadow(6, 2)


def net_heap(seed=0):
    """A heap of drying net: green mesh in folds, cork floats along its rope."""
    sp = Sprite(18, 9, 9, 8)
    for y in range(1, 9):
        for x in range(1, 17):
            u, v = (x + 0.5 - 9) / 8.0, (y + 0.5 - 6) / 4.0
            if u * u + v * v > 1:
                continue
            mesh = (x + y) % 2 == 0
            sp.px(x, y, 'leaf_cool', (3 if v < 0 else 2) if mesh else 1)
    for x in range(2, 16, 3):
        sp.px(x, 4 + (x % 2), 'clay_warm', 4)
    return sp, sp.blob_shadow(8, 2)


def slipway(p: Plot, x0, x1, y0, y1, wl, seed=0):
    """A slipway running down the beach into the water (28 wide): big granite setts across
    it between two kerbs (the west lit, the east dark), slimed green and weedy towards the
    water line, the lower part under the water showing through it in the lagoon's tones.
    Walkable above the water line."""
    slip = (p.x >= x0) & (p.x < x1) & (p.y >= y0) & (p.y < y1)
    inner = slip & (p.x >= x0 + 2) & (p.x < x1 - 2)
    setts(p, inner, seed, ramps=('stone', 'stone_cool', 'ashlar'), course=5)
    kw = slip & (p.x < x0 + 2)
    ke = slip & (p.x >= x1 - 2)
    p.put(kw, 'ashlar_warm', 4)
    p.put(kw & (p.x == x0), 'ashlar_warm', 3)
    p.put(ke, 'ashlar_cool', 2)
    p.put(ke & (p.x == x1 - 1), 'ashlar_cool', 1)
    down = (p.y - y0) / max(1.0, float(wl - y0))                    # dry and pale at its head, darker going down
    p.step(inner & (down > 0.45), -1, lo=1)
    rib = inner & (((p.y - y0) % 10) == 0) & (p.y < wl)                # raised ribs across it for a grip
    p.put(rib, 'ashlar_warm', 4)
    p.put(shift(rib, 0, 1, False) & inner & (p.y < wl), 'ashlar', 1)
    apron = (np.abs(p.x - (x0 + x1) / 2.0) < (x1 - x0) / 2.0 + 6 - (p.y - (y0 - 10)) * 0.6) & (p.y >= y0 - 10) & \
        (p.y < y0) & ~p.solid & ~p.wet
    setts(p, apron & (hash01(p.x // 3, p.y // 2, seed + 5) < 0.85 - (y0 - p.y) * 0.05), seed + 6)
    slime = slip & (p.y >= wl - 14) & (p.y < wl) & (hash01(p.x // 2, p.y // 2, seed + 1) < (p.y - (wl - 14)) / 16.0)
    p.put(slime & (p.t >= 3), 'grass_cool', 3)
    p.put(slime & (p.t < 3), 'leaf_cool', 2)
    under = slip & ((p.y >= wl) | p.wet)
    tt = p.t.copy()
    p.f[under] = IDX['lagoon']
    p.t[under] = np.clip(np.where(tt >= 4, 4, np.where(tt <= 1, 2, 3)) - ((p.y - wl) // 10), 1, 4)[under]
    p.wet |= under
    p.hazard |= under
    p.walk |= slip & ~under
    p.walk &= ~under
    p.solid &= ~slip
    return slip & ~under


# --- things -------------------------------------------------------------------------------------
def boulder(seed=0, w=None, h=None, rocks=BASALT, weed=True):
    """A shore boulder (16 to 32 wide): a rounded mass broken into facets, lit from the upper
    left in hard steps, orange lichen above the tide, a skirt of black weed and barnacles at
    its foot where the sea washes it; a dark contact under it."""
    w = w or 14 + int(hash01(seed, 0, 19) * 14)
    h = h or int(w * (0.6 + 0.15 * hash01(seed, 1, 19)))
    sp = Sprite(w + 4, h + 4, (w + 4) // 2, h + 1)
    cx, cy = sp.fx, sp.fy - h * 0.48
    u, v = (sp.x + 0.5 - cx) / (w / 2), (sp.y + 0.5 - cy) / (h / 2)
    ang = np.arctan2(v, u)
    r = 1 + 0.10 * np.sin(ang * 3 + seed) + 0.05 * np.sin(ang * 7 + seed)
    shape = (u * u + v * v <= r * r) & (sp.y <= sp.fy)
    fac = (np.floor((ang + seed) / 1.1)).astype(int)
    lam = light_of(u, v, 0.35) + 0.15 * (hash01(fac, 0, seed + 2) - 0.5)
    tone = tone_of(lam, (0.42, -0.02, -0.45))
    pick = hash01(fac, 1, seed + 3)
    famr = np.where(pick < 0.4, IDX[rocks[0]], np.where(pick < 0.7, IDX[rocks[2]], IDX[rocks[-1]]))
    sp.put(shape, famr, tone)
    sp.put(shape & (tone == 4) & (lam > 0.62), famr, 5)
    lich = shape & (tone >= 3) & (v < 0) & (hash01(sp.x // 2, sp.y // 2, seed + 4) < 0.14)
    sp.put(lich, 'clay_warm', 4)
    if weed:
        skirt = shape & (sp.y >= sp.fy - max(2, h // 5))
        sp.put(skirt, 'leaf_cool', 1)
        sp.put(skirt & (hash01(sp.x, sp.y, seed + 5) < 0.3), 'leaf_cool', 2)
        barn = shape & (sp.y >= sp.fy - h // 3) & ~skirt & (hash01(sp.x // 2, sp.y // 2, seed + 6) < 0.25)
        sp.put(barn & (sp.x % 2 == 0), 'bleached', 5)
    sp.put(shape & (sp.y >= sp.fy - 1), famr, 1)
    return sp, sp.blob_shadow(w * 0.55, max(3, h * 0.3))


def driftwood(seed=0, n=None):
    """A driftwood log cast up on the beach (18 to 30 long): silvered by sun and salt, its
    grain running along it, lit on its top, a snapped end showing paler wood, a stub of a
    branch; its shadow on the sand under it."""
    n = n or 18 + int(hash01(seed, 0, 23) * 12)
    sp = Sprite(n + 4, 9, (n + 4) // 2, 7)
    for i in range(n):
        th = 4 if 2 < i < n - 3 else 3
        for j in range(th):
            y = 7 - th + j
            x = i + 1
            t = 4 if j == 0 else (3 if j < th - 1 else 2)
            if (i + seed) % 7 == 0 and j == 1:
                t = 2
            sp.px(x, y, 'bleached_cool' if (i // 5 + seed) % 3 else 'timber_cool', t)
    for j in range(3):
        sp.px(n, 5 - j + 1, 'bleached_warm', 5 - (j > 1))
    bx = 4 + int(hash01(seed, 1, 23) * (n - 10))
    for j in range(3):
        sp.px(bx + j, 2 - j // 2, 'bleached_cool', 4 if j < 2 else 3)
    return sp, shift(sp.m, 2, 1, False) & ~sp.m


def bollard(seed=0):
    """A cast-iron bollard on a quay (8 wide, 10 tall): a lit cap with its rim, a waisted
    body lit on its west, its base plate; the paint worn to the iron at the top."""
    sp = Sprite(10, 12, 5, 10)
    for y in range(2, 11):
        half = 3 if y < 4 else (2 if y < 8 else 3)
        for x in range(5 - half, 5 + half):
            t = 4 if x < 5 - half + 2 else (3 if x < 5 + half - 1 else 1)
            if y == 2:
                t = 5 if x < 5 else 4
            if y == 3:
                t = 2
            sp.px(x, y, 'iron', t)
    for x in range(2, 8):
        sp.px(x, 10, 'iron', 2 if x < 6 else 1)
    return sp, sp.blob_shadow(4, 2)


# --- the composed sample: a cove under a cliff, a pier and a path down --------------------------
CW, CH = 640, 640
E_COVE = [0, 32, 64, 96]          # the sea and the beach, the quay, the cliff top, the headland


def _curve(pts, x):
    """A smooth line through control points (x, y), read at each x (Catmull-Rom)."""
    c = spline(pts, 0.5)
    order = np.argsort(c[:, 0])
    return np.interp(x, c[order, 0], c[order, 1])


def cove_cells(seed=1):
    """The cove's tiers on the 8 px grid, from organic lines (lobes, bays, a spur), sampled
    at each cell's centre: the cliff top (3) round the bay, standing 96 over the sea at the
    headland in the west and over the beach at the bay's back; in the east under it a turf
    shelf (2) and the quay (1), each 32 lower; the sea and the beach (0)."""
    rows, cols = CH // GRID, CW // GRID
    X, Y = np.meshgrid(np.arange(cols) * GRID + 4.0, np.arange(rows) * GRID + 4.0)
    nz = (fbm(X, Y, 40, seed) - 0.5) * 2
    y3 = _curve([(-20, 300), (40, 318), (90, 302), (140, 324), (178, 300), (204, 236), (236, 178), (282, 160),
                 (330, 174), (380, 156), (420, 170), (446, 150), (472, 106), (520, 94), (580, 104), (640, 96),
                 (680, 100)], X) + 8 * nz
    y2 = _curve([(440, 186), (480, 172), (540, 180), (600, 170), (680, 176)], X) + 6 * nz
    yq = np.where(X < 520, 296.0, np.where(X < 540, 296.0 + (X - 520) * 0.8, 312.0))
    C = np.zeros((rows, cols), np.int16)
    xq = 436 + 10 * np.sin(Y / 37.0) + 6 * nz
    C[(X >= xq) & (Y < yq)] = 1
    C[(X >= xq + 16) & (Y < y2)] = 2
    C[Y < y3] = 3
    return C


def cove(seed=1):
    """The composed sample, 640 x 640 (two screens wide, a little more than one tall): a cove
    under a sandstone cliff. The headland stands 96 over the sea in the west with a wave-cut
    platform and its rock pools at its foot; the cliff top in sea turf curves round the bay's
    back, 64 over the beach; shingle under the headland grades into sand; a harbour quay of
    setts in the east, its sea wall in the water with a ladder and rings; the path down comes
    over the cliff top, along the cliff's last face by a ramp to the quay, and down the sea
    wall by a stair to the beach; a timber pier runs out into the cove beside a slipway; the
    reef and its breakers, the deep and two far isles in the haze make the south edge.
    Returns the plot and its parts."""
    C = cove_cells(seed)
    T = lattice(C, CW, CH)
    R = Relief(T, E_COVE)
    p = Plot(CW, CH, 'sand', 3)
    p.tier = R.seen().astype(np.int8)
    p.walk[:] = False
    tops = ~R.face
    # --- the shore line ------------------------------------------------------------------
    shore_y = _curve([(-10, 300), (30, 330), (64, 474), (110, 508), (160, 500), (200, 468), (240, 452),
                      (300, 472), (360, 462), (410, 446), (444, 392), (472, 364), (500, 344), (540, 336),
                      (660, 336)], p.x) + (fbm(p.x, p.y * 0, 20, seed + 1) - 0.5) * 8
    water = tops & (T == 0) & (p.y > shore_y)
    land0 = tops & (T == 0) & ~water
    under = land0 & (p.x < 205)                                     # the headland's foot
    plat = under & (p.y > _curve([(0, 420), (100, 432), (200, 444)], p.x) + (fbm(p.x, p.y, 12, seed + 2) - 0.5) * 10)
    plat |= under & (p.x < 186)
    sh_edge = 228 + 0.22 * (p.y - 260) + 16 * np.sin(p.y / 31.0 + 1) + (fbm(p.x, p.y, 20, seed + 3) - 0.5) * 30
    shing = land0 & ~plat & (p.x < sh_edge)
    sand_m = land0 & ~plat & ~shing
    turf = tops & (T >= 2)
    quay_top = tops & (T == 1)
    # --- the ground ----------------------------------------------------------------------
    sea_turf(p, turf & (T == 2), seed + 4, heathy=0)
    sea_turf(p, turf & (T == 3), seed + 5, thrift=1.4)
    setts(p, quay_top, seed + 6)
    beach(p, sand_m, water, seed + 7)
    shingle(p, shing, water, seed + 8)
    grade(p, sand_m, shing, water, seed + 12)
    platform(p, plat, water, seed + 9, rock='bleached')
    p.walk |= turf & ~p.solid
    sea(p, water, ~water, seed + 10)
    pools = rock_pools(p, plat, ((96, 466, 18, 8), (150, 480, 12, 6), (64, 452, 9, 5), (128, 448, 10, 4)), seed + 11)
    # --- the cliffs ----------------------------------------------------------------------
    quay_face = R.face & (R.kf == 1)
    cliff_faces(p, R, seed + 20, m=~quay_face)
    masonry(p, R, quay_face, seed + 21, water=water)
    kind = np.full(p.f.shape, '', object)
    kind[turf] = 'turf'
    kind[turf & (T == 3) & (p.x < 96)] = 'rock'                   # the headland's exposed seaward rim
    kind[turf & (T == 3) & (p.x > 300) & (p.x < 420)] = 'rock' 
    lips(p, R, kind, seed + 22)
    hangs(p, R, kind, seed + 23)
    bands(p, R, seed + 24, kind)
    fk = np.full(p.f.shape, '', object)
    fk[sand_m] = 'sand'
    fk[shing] = 'shingle'
    fk[plat] = 'rock'
    fk[quay_top] = 'rock'
    feet(p, R, fk, seed + 25)
    sea_foot(p, R, water, seed + 26)
    # --- the ways down -------------------------------------------------------------------
    path = []
    path.append(trail(p, [(600, -8), (590, 30), (604, 62), (606, 80)], 16, seed + 30))
    ramp = ramp_along(p, R, 480, 604, 24, seed + 31, rising='east', k=3)
    ramp2 = ramp_along(p, R, 478, 602, 24, seed + 32, rising='west', k=2)
    stepped_tread(p, ramp, 'east', seed + 36)
    stepped_tread(p, ramp2, 'west', seed + 37)
    ch = Channel(p, [(612, 216), (580, 250), (520, 268), (476, 282), (466, 292)], reach=12)
    polished = ch.near & (np.abs(ch.n) < 6 + (fbm(ch.s, 0, 12, seed + 38) - 0.5) * 4) & quay_top & ~p.solid
    p.step(polished & (p.t < 4), 1)                                 # setts polished by feet, not a dirt path
    st = stair(p, R, 444, 40, seed + 33, k=1)
    ramp = ramp | ramp2
    for x in range(448, 492):
        p.walk[332:338, x] |= land0[332:338, x]
    tier_shadows(p, R)
    surf(p, water, seed + 34, beachy=sand_m)
    p.walk &= ~water
    # --- the pier and the slipway ----------------------------------------------------------
    pier_m = pier(p, 296, 448, 328, 556, seed + 40)
    wl = int(shore_y[0, 404])
    slip = slipway(p, 386, 422, wl - 26, wl + 30, wl, seed + 41)
    # --- the reef, the deep and the far isles ----------------------------------------------
    rocks = []
    for ci, (cx, cy, n) in enumerate(((40, 588, 4), (170, 580, 3), (300, 600, 2), (470, 582, 5), (612, 596, 2),
                                      (252, 534, 1), (532, 470, 2))):
        for j in range(n):
            r = 4 + hash01(ci, j, seed + 47) ** 1.6 * 14              # a 3x and more range of sizes
            ox = (hash01(ci, j, seed + 48) - 0.5) * 34
            oy = (hash01(ci, j, seed + 49) - 0.5) * 12
            rocks.append((int(cx + ox), int(cy + oy), int(r), max(2, int(r * (0.38 + 0.1 * hash01(ci, j, 50))))))
    reef_m = reef(p, rocks, seed + 50, 'basalt')
    surf(p, p.wet & ~reef_m, seed + 51)
    for i, (x, y, rx, ry) in enumerate(rocks):
        if rx >= 11 and 30 < x < p.w - 30:     # the swell breaking round the big rocks' seaward side, in arcs
            span = 0.25 + hash01(i, 0, seed + 55) * 0.35
            a0 = math.pi * (0.5 - span) + (hash01(i, 1, seed + 56) - 0.5) * 0.4
            arc = [(x + (rx + 6) * math.cos(a0 + 2 * span * math.pi * t / 4.0),
                    y + (ry + 5) * math.sin(a0 + 2 * span * math.pi * t / 4.0)) for t in range(5)]
            breakers(p, arc, seed + 52 + i, width=2)
    south_edge(p, 566, seed + 53, isles=((120, 634, 64, 20), (520, 636, 84, 18)))
    # --- things ----------------------------------------------------------------------------
    for i, (x, y, w, ramps, weed) in enumerate(((200, 478, 22, SANDSTONE, True), (226, 446, 16, SANDSTONE, False),
                                                 (52, 490, 26, BASALT, True), (176, 420, 18, SANDSTONE, False),
                                                 (430, 360, 14, BASALT, True))):
        if p.solid[y, x]:
            continue
        b, bs = boulder(seed + 60 + i, w, None, ramps, weed)
        paste(p, b, x, y, shadow=bs, block=b.m & (b.y > b.fy - 5))
    footprints(p, [(468, 342), (440, 372), (396, 384), (352, 410), (322, 440), (314, 452)], seed + 75, m=sand_m)
    bushes = []
    for ci, (cx, cy, n) in enumerate(((60, 210, 4), (250, 120, 3), (150, 40, 5), (380, 70, 3), (520, 40, 2),
                                      (300, 22, 2), (100, 120, 2))):
        for j in range(n):
            bushes.append((int(cx + (hash01(ci, j, seed + 91) - 0.5) * 46), int(cy + (hash01(ci, j, seed + 92) - 0.5) * 22),
                           seed + 93 + ci * 7 + j))
    for (x, y, sd) in sorted(bushes, key=lambda b: b[1]):
        if not (0 <= x < p.w and 0 <= y < p.h) or p.solid[y, x] or not turf[y, x] or not R.top(int(T[y, x]))[y, x]:
            continue
        g, gs = gorse(sd)
        paste(p, g, x, y, shadow=gs, block=g.m & (g.y > g.fy - 4))
    for i, (x, y) in enumerate(((356, 398), (262, 420), (330, 372))):
        if p.solid[y, x] or p.wet[y, x]:
            continue
        dw, ds = driftwood(seed + 70 + i)
        paste(p, dw, x, y, shadow=ds, block=dw.m & (dw.y > dw.fy - 3))
    for i, (x, y) in enumerate(((524, 300), (604, 314), (500, 292))):
        if p.solid[y, x]:
            continue
        b, bs = bollard(seed + i)
        paste(p, b, x, y, shadow=bs, block=b.m & (b.y > b.fy - 3))
    for x in (316,):
        b, bs = bollard(seed + 9)
        paste(p, b, x, 548, shadow=bs, block=b.m & (b.y > b.fy - 3))
    for (mk, x, y, sd) in ((coil, 540, 290, 1), (fish_crate, 586, 296, 2), (fish_crate, 598, 302, 3), (net_heap, 620, 268, 4),
                           (coil, 472, 300, 5)):
        if p.solid[y, x] or not quay_top[y, x]:
            continue
        sp_, sh_ = mk(sd)
        paste(p, sp_, x, y, shadow=sh_, block=sp_.m & (sp_.y > sp_.fy - 3))
    moss = quay_top & (dist_to(~quay_top, 8) < 6) & (hash01(p.x // 2, p.y, seed + 81) < 0.08) & ~p.solid
    p.put(moss, 'grass_cool', 3)
    ladder(p, R, 560, k=1, seed=seed + 80)
    for x in (512, 596, 624):
        ys = np.nonzero(R.face[:, x] & (R.kf[:, x] == 1))[0]
        if len(ys):
            ring(p, x, int(ys.min()) + 8)
    parts = dict(R=R, T=T, water=water, sand=sand_m, shingle=shing, platform=plat, pools=pools, quay=quay_top,
                 turf=turf, ramp=ramp, stair=st, pier=pier_m, slip=slip, reef=reef_m, path=path, quay_face=quay_face)
    return p, parts


# --- moving water --------------------------------------------------------------------------------
def flow_frames(p: Plot):
    """The moving water, as water_flow.py draws it for the zones (glints on open water, foam
    lapping the shore), recoloured onto the house ramps: a changed pixel moves one tone up
    its own ramp (two where the flow is strongest) instead of being mixed with white.
    Returns (list of RGB frames, box)."""
    import water_flow
    img = p.image()
    wet = {(int(x), int(y)) for y, x in zip(*np.nonzero(p.wet))}
    res = water_flow.sheet(img, wet, set())
    if res is None:
        return [img], None
    stack, (x0, y0, bw, bh) = res
    a = np.asarray(stack)
    out = []
    base_rgb = np.asarray(img).astype(np.int32)
    for fi in range(water_flow.FRAMES):
        fr = a[fi * bh:(fi + 1) * bh]
        on = fr[..., 3] > 0
        q = Plot(p.w, p.h)
        q.f, q.t = p.f.copy(), p.t.copy()
        sel = np.zeros(p.f.shape, bool)
        sel[y0:y0 + bh, x0:x0 + bw] = on
        lit = np.zeros(p.f.shape, np.int32)
        lit[y0:y0 + bh, x0:x0 + bw] = fr[..., :3].astype(np.int32).sum(-1)
        strong = sel & (lit - base_rgb.sum(-1) > 150)
        q.step(sel, 1)
        q.step(strong, 1)
        out.append(q.image())
    return out, (x0, y0, bw, bh)


# --- the pieces on their own, for the kit sheet -----------------------------------------------------
def _cliff_piece(rows, E=(0, 32, 64, 96), rocks=SANDSTONE, top='turf', foot='sand', sea_below=False, seed=3):
    """A small cliff from a cell map (8 px a character, north at the top): organic outline
    with 45 degree runs, faces from the column tiles, lips, bands, feet and shadows, over a
    beach, shingle, rock or the sea."""
    C = np.array([[int(ch) for ch in r] for r in rows], np.int16)
    T = lattice(C)
    R = Relief(T, list(E))
    q = Plot(T.shape[1], T.shape[0], 'sand', 3)
    tops = ~R.face
    up = tops & (T >= 1)
    low = tops & (T == 0)
    if top == 'marram':
        dune(q, up, seed)
    else:
        sea_turf(q, up, seed)
    water = np.zeros(T.shape, bool)
    if sea_below:
        water = low & (q.y > np.nonzero(R.face.any(1))[0].max() - 2 + 0 * q.x)
        water |= low & (q.y > 70 + (fbm(q.x, q.y, 20, seed) - 0.5) * 10)
        rest = low & ~water
        beach(q, rest, water, seed + 1)
        sea(q, water, ~water, seed + 2)
    elif foot == 'shingle':
        water = low & (q.y > q.h - 14 + (fbm(q.x, q.y, 14, seed) - 0.5) * 6)
        shingle(q, low & ~water, water, seed + 1)
        sea(q, water, ~water, seed + 2)
    else:
        water = low & (q.y > q.h - 14 + (fbm(q.x, q.y, 14, seed) - 0.5) * 6)
        beach(q, low & ~water, water, seed + 1)
        sea(q, water, ~water, seed + 2)
    cliff_faces(q, R, seed + 5, rocks=rocks)
    kind = np.full(T.shape, top, object)
    lips(q, R, kind, seed + 6)
    hangs(q, R, kind, seed + 7, every=0.25)
    bands(q, R, seed + 8, kind, rocks=rocks)
    fk = np.full(T.shape, 'shingle' if foot == 'shingle' else 'sand', object)
    feet(q, R, fk, seed + 9)
    sea_foot(q, R, water, seed + 10)
    tier_shadows(q, R)
    surf(q, water, seed + 11, beachy=low & ~water & (foot != 'shingle'))
    return q, R


CLIFF_SEA = ['333333333333333333333',
             '333333333333333333333',
             '333333333333333333333',
             '333333333333333333333',
             '333333333333333333000',
             '333333333333333300000',
             '033333333333333000000',
             '000333333333330000000',
             '000003333333000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000',
             '000000000000000000000']
CLIFF_BAY = ['2222222222222222222222',
             '2222222222222222222222',
             '2222222222222222222222',
             '2222222220022222222222',
             '2222222000000222222222',
             '2222220000000000222222',
             '0222000000000000002220',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000']
DUNE_STEP = ['1111111111111111111111',
             '1111111111111111111111',
             '1111111111111111111100',
             '0111111111111111100000',
             '0001111111111000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000',
             '0000000000000000000000']


def _ground(w, h, fn, seed=0, water_rows=None, **kw):
    q = Plot(w, h, 'sand', 3)
    m = np.ones((h, w), bool)
    water = np.zeros((h, w), bool)
    if water_rows:
        water = q.y > h - water_rows + (fbm(q.x, q.y, 16, seed) - 0.5) * 8
        m &= ~water
    fn(q, m, water, seed, **kw) if fn in (beach, shingle, platform) else fn(q, m, seed, **kw)
    if water_rows:
        sea(q, water, ~water, seed + 1)
        surf(q, water, seed + 2, beachy=m if fn is beach else None)
    return q


def _quay_piece(seed=5):
    """A stretch of quay: setts on top, its sea wall standing in the water with a ladder,
    rings and bollards."""
    rows = ['111111111111111111111'] * 5 + ['111111111111111111100', '111111111111111110000'] + \
           ['000000000000000000000'] * 8
    C = np.array([[int(ch) for ch in r] for r in rows], np.int16)
    T = lattice(C)
    R = Relief(T, [0, 32])
    q = Plot(T.shape[1], T.shape[0], 'sand', 3)
    top = ~R.face & (T == 1)
    water = ~R.face & (T == 0)
    setts(q, top, seed)
    sea(q, water, ~water, seed + 1)
    masonry(q, R, R.face, seed + 2, water=water)
    ladder(q, R, 60, seed=seed + 3)
    for x in (24, 100):
        ys = np.nonzero(R.face[:, x])[0]
        ring(q, x, int(ys.min()) + 8)
    tier_shadows(q, R)
    surf(q, water, seed + 4)
    for x in (40, 120):
        b, bs = bollard(seed + x)
        paste(q, b, x, 30, shadow=bs)
    return q, R


def _pier_piece(seed=6):
    q = Plot(120, 150, 'sand', 3)
    water = q.y > 40 + (fbm(q.x, q.y, 16, seed) - 0.5) * 8
    beach(q, ~water, water, seed)
    sea(q, water, ~water, seed + 1)
    surf(q, water, seed + 2, beachy=~water)
    pier(q, 30, 20, 62, 120, seed + 3)
    slipway(q, 82, 110, 10, 70, int(40), seed + 4)
    b, bs = bollard(seed)
    paste(q, b, 46, 114, shadow=bs)
    return q


def _edge_piece(seed=7):
    q = Plot(240, 150, 'sand', 3)
    land = q.y < 18 + (fbm(q.x, q.y, 20, seed) - 0.5) * 10
    water = ~land
    beach(q, land, water, seed)
    sea(q, water, land, seed + 1)
    surf(q, water, seed + 2, beachy=land)
    rocks = [(40, 70, 14, 6), (120, 76, 10, 5), (190, 68, 16, 7)]
    rm = reef(q, rocks, seed + 3)
    surf(q, q.wet & ~rm, seed + 4)
    for i, (x, y, rx, ry) in enumerate(rocks):
        breakers(q, [(x - rx - 10, y + ry + 2), (x - rx // 2, y + ry + 7), (x + rx // 2, y + ry + 8),
                     (x + rx + 12, y + ry + 3)], seed + 5 + i, width=3)
    south_edge(q, 96, seed + 6, isles=((70, 150, 50, 14), (190, 154, 60, 16)))
    return q


def _ways_piece(seed=8):
    """A ramp along a cliff's face and a stair down a sea wall."""
    rows = ['2222222222222222222222222'] * 4 + ['1111111111111111111111111'] * 6 + ['0000000000000000000000000'] * 6
    C = np.array([[int(ch) for ch in r] for r in rows], np.int16)
    T = lattice(C)
    R = Relief(T, [0, 32, 64])
    q = Plot(T.shape[1], T.shape[0], 'sand', 3)
    tops = ~R.face
    sea_turf(q, tops & (T == 2), seed)
    setts(q, tops & (T == 1), seed + 1)
    beach(q, tops & (T == 0), np.zeros(T.shape, bool) | (q.y > q.h - 6), seed + 2)
    cliff_faces(q, R, seed + 3, m=R.kf == 2)
    masonry(q, R, R.face & (R.kf == 1), seed + 4)
    kind = np.full(T.shape, 'turf', object)
    lips(q, R, kind, seed + 5, m=R.rim & (R.T == 2))
    tier_shadows(q, R)
    ramp_along(q, R, 30, 150, 24, seed + 6, rising='east', k=2)
    stair(q, R, 140, 40, seed + 7, k=1)
    return q, R


def pieces():
    """Every piece on its own tile: (group, name, plot, [(box, kind)])."""
    out = []
    q, R = _cliff_piece(CLIFF_SEA, rocks=SANDSTONE, top='turf', sea_below=True, seed=3)
    out.append(('rock', 'a sea cliff of 96 in sandstone: pillow columns, turf and thrift lips, the wet foot in the sea',
                q, [(face_box(R, (0, 0, q.w, q.h)), 'face')]))
    q, R = _cliff_piece(CLIFF_BAY, E=(0, 32, 64), rocks=BASALT, top='turf', foot='shingle', seed=4)
    out.append(('rock', 'a basalt cliff of 64 round a bay, over shingle (the isles\' cove)', q,
                [(face_box(R, (0, 0, q.w, q.h)), 'face')]))
    q, R = _cliff_piece(DUNE_STEP, E=(0, 32), rocks=SANDSTONE, top='marram', seed=5)
    out.append(('rock', 'a dune\'s step of 32: marram lips over a sandstone foot', q,
                [(face_box(R, (0, 0, q.w, q.h)), 'face')]))
    q = _ground(160, 110, beach, 11, water_rows=26)
    out.append(('shore', 'a sand beach: dry sand, ripples, the wrack line, the swash and the wet band', q,
                [((10, 10, 82, 62), 'ground')]))
    q = _ground(160, 110, shingle, 12, water_rows=26)
    out.append(('shore', 'shingle graded to its storm ridge', q, [((10, 10, 82, 62), 'ground')]))
    q = _ground(170, 120, platform, 13, water_rows=30, rock='bleached')
    pm = ~q.wet
    rock_pools(q, pm, ((50, 40, 20, 9), (120, 56, 14, 7), (100, 26, 10, 5)), 14)
    out.append(('shore', 'a wave-cut platform with rock pools (weed, anemones, a starfish)', q,
                [((10, 6, 82, 62), 'ground'), ((30, 30, 66, 50), 'water')]))
    q = Plot(200, 120, 'sand', 3)
    land = q.y < 14 + (fbm(q.x, q.y, 18, 15) - 0.5) * 8
    beach(q, land, ~land, 15)
    sea(q, ~land, land, 16)
    surf(q, ~land, 17, beachy=land)
    out.append(('water', 'the sea from the swash to the deep: depth bands, the floor, swell lines', q,
                [((40, 20, 112, 72), 'water'), ((100, 60, 172, 112), 'water')]))
    q = _edge_piece()
    out.append(('water', 'the layered south edge: the reef and its breakers, the deep, far isles in the haze', q,
                [((20, 60, 92, 112), 'water')]))
    q, R = _quay_piece()
    out.append(('built', 'a quay: setts, its sea wall in dressed courses with coping, ladder, rings, wet and weed',
                q, [((10, 2, 82, 38), 'paving'), ((70, 44, 120, 70), 'stone-wall')]))
    q = _pier_piece()
    out.append(('built', 'a pier on piles and a slipway into the water', q,
                [((28, 30, 64, 66), 'paving'), ((80, 14, 112, 50), 'paving')]))
    q, R = _ways_piece()
    out.append(('built', 'the path down: a ramp along the cliff\'s face, a stair down the sea wall', q,
                [((40, 24, 112, 60), 'stair')]))
    q = Plot(190, 70, 'sand', 3)
    beach(q, np.ones(q.f.shape, bool), np.zeros(q.f.shape, bool), 18)
    for i, (x, y, w, rk, wd) in enumerate(((20, 40, 22, BASALT, True), (56, 44, 16, SANDSTONE, False),
                                            (92, 42, 26, SANDSTONE, True))):
        b, bs = boulder(30 + i, w, None, rk, wd)
        paste(q, b, x, y, shadow=bs)
    dw, ds = driftwood(40)
    paste(q, dw, 140, 40, shadow=ds)
    dw, ds = driftwood(41, 22)
    paste(q, dw, 130, 62, shadow=ds)
    b, bs = bollard(1)
    paste(q, b, 176, 40, shadow=bs)
    out.append(('things', 'boulders (basalt and sandstone, lichen, weed skirts), driftwood, a bollard', q, []))
    return out


# --- the sheet, the comparison, the bar, the checks ------------------------------------------------
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RAMP_TONES = 0.85     # house-style ruling (cea6bae): ramp-built art passes tones at 85 %

# Official screenshots of coasts, piers and water, for the side-by-side comparison. Only the
# URLs, boxes and the adult's height there are kept; the images stay out of the repository
# (read from REF_DIR by the URL's file name).
REFS = (
    ('Sea of Stars: a rocky shore, foam hugging the rocks, the shallows', 'https://shared.akamai.steamstatic.com/'
     'store_item_assets/steam/apps/1244090/ss_ac7d1a4a9fb207bc59637aeb24698758e4e847ad.1920x1080.jpg',
     (380, 0, 1920, 1080), 150.0),
    ('Sea of Stars: a cove with a pier and a quay under cliffs', 'https://shared.akamai.steamstatic.com/'
     'store_item_assets/steam/apps/1244090/ss_c250a7fd789b3cbab5ca8e99e3530cf933656ad1.1920x1080.jpg',
     (560, 560, 1560, 1080), 150.0),
    ('Sea of Stars: sea cliffs of pillow rock over the deep', 'https://shared.akamai.steamstatic.com/'
     'store_item_assets/steam/apps/1244090/ss_3444baf45a5dc2b27d0c7d385dbcad7e4b121791.1920x1080.jpg',
     (0, 0, 1240, 900), 150.0),
    ('Sea of Stars: a jetty over deep water between cliffs', 'https://shared.akamai.steamstatic.com/'
     'store_item_assets/steam/apps/1244090/ss_2f011be3599c238ff5d240bdb2bb2879e27271f1.1920x1080.jpg',
     (0, 300, 1600, 1080), 150.0),
    ('Eastward: a pond\'s stone bank and water (Octopia)', 'https://eastwardgame.com/wp-content/uploads/2024/06/'
     'Octopia-7_Fishing.jpg', (0, 200, 900, 900), 162.0),
    ('Eastward: a canal\'s stone edge (Octopia)', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/'
     '2305370/ss_f5788b1d4ade71e0cdb1e0110debfad3b32ca51c.1920x1080.jpg', (0, 700, 900, 1080), 162.0),
)


def ref_image(url, box, adult):
    """An official screenshot's crop at our scale (an adult 25 px, each pixel the commonest
    colour of its block), from a local copy in REF_DIR named as the URL's file; or None."""
    import detail_bar as db
    ref_dir = os.environ.get('REF_DIR', os.path.join(tempfile.gettempdir(), 'napattack-refs'))
    path = os.path.join(ref_dir, url.rsplit('/', 1)[1].split('?')[0])
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert('RGB').crop(box)
    key = db.to_scale(im, adult)
    out = np.zeros(key.shape + (3,), np.uint8)
    out[..., 0] = (key >> 8) * 16 + 8
    out[..., 1] = ((key >> 4) & 15) * 16 + 8
    out[..., 2] = (key & 15) * 16 + 8
    return Image.fromarray(out, 'RGB')


def _label(img, text, xy, fill=(240, 236, 228)):
    d = ImageDraw.Draw(img)
    x, y = xy
    d.text((x + 1, y + 1), text, fill=(20, 16, 20))
    d.text((x, y), text, fill=fill)


def judge(c, kind):
    """(strict pass, pass under the ramp ruling): tones at 85 % for art drawn only in house
    ramps; shapes, dressing and both cleanliness tests in full."""
    import detail_bar as db
    ref = db.bar(kind)
    rest = (c['shapes'] >= db.TOLERANCE * ref['shapes'] and c['dressing'] >= db.TOLERANCE * ref['dressing']
            and c['isolated'] <= ref['isolated'] + db.ISOLATED_MARGIN and c['cluster'] >= db.CLUSTER_SHARE * ref['cluster'])
    return rest and c['tones'] >= db.TOLERANCE * ref['tones'], rest and c['tones'] >= RAMP_TONES * ref['tones']


def bar_line(img, box, kind):
    import detail_bar as db
    ok, c, lines = db.check_image(img, box, kind)
    strict, ramp = judge(c, kind)
    return c, strict, ramp, f'{kind} t{c["tones"]:.0f}/{db.bar(kind)["tones"]:.0f} s{c["shapes"]:.0f}/{db.bar(kind)["shapes"]:.0f} ' \
        f'd{c["dressing"]:.0f}/{db.bar(kind)["dressing"]:.0f} {"PASS" if strict else "PASS@85" if ramp else "FAIL"}'


def face_box(R, region, w=50, h=34, avoid=None):
    """The box of w x h inside region that holds the most rock face."""
    x0, y0, x1, y1 = region
    fc = R.face.copy()
    if avoid is not None:
        fc &= ~np.asarray(avoid, bool)
    ii = np.pad(np.cumsum(np.cumsum(fc.astype(np.int32), 0), 1), ((1, 0), (1, 0)))
    best = None
    for y in range(y0, max(y0 + 1, y1 - h), 2):
        for x in range(x0, max(x0 + 1, x1 - w), 2):
            a = ii[min(y + h, fc.shape[0]), min(x + w, fc.shape[1])] - ii[y, min(x + w, fc.shape[1])] - \
                ii[min(y + h, fc.shape[0]), x] + ii[y, x]
            if best is None or a > best[0]:
                best = (a, (x, y, x + w, y + h))
    return best[1]


# Where the cove is measured: faces on the best 50 x 34 box of rock inside a region, the rest
# on fixed boxes.
COVE_FACES = (
    ((0, 300, 176, 440), 'face', 'the headland: a sea cliff of 96'),
    ((200, 160, 430, 280), 'face', 'the bay\'s back: a cliff of 64 over the beach'),
)
COVE_BOXES = (
    ((540, 312, 600, 342), 'stone-wall', 'the quay\'s sea wall in the water'),
    ((480, 200, 560, 260), 'paving', 'the quay\'s setts'),
    ((272, 300, 352, 380), 'ground', 'the beach: dry sand, the wrack line'),
    ((196, 330, 246, 400), 'ground', 'shingle under the headland'),
    ((70, 436, 140, 486), 'ground', 'the platform with its pools'),
    ((360, 470, 440, 520), 'water', 'the shallows and the surf'),
    ((440, 500, 520, 556), 'water', 'the cove out over the shelf'),
    ((296, 460, 328, 520), 'paving', 'the pier\'s deck'),
    ((240, 80, 340, 150), 'ground', 'sea turf on the cliff top'),
    ((500, 170, 570, 206), 'stair', 'the ramp down to the quay'),
)


def cove_preview(p, scale=2, people=True):
    """The cove at `scale`, with residents standing in it for scale (preview only)."""
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in (('beachcomber', (330, 404)), ('boatwoman', (312, 540)), ('ferryman', (500, 250)),
                             ('naturalist', (120, 444)), ('stroller', (604, 60))):
            path = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')
            if os.path.exists(path):
                r = Image.open(path).convert('RGBA')
                r = r.resize((r.width // 4, r.height // 4), Image.NEAREST)
                img.alpha_composite(r, (x - r.width // 2, y - r.height))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def night(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32) * np.array([0.42, 0.45, 0.68])
    return Image.fromarray(a.astype(np.uint8))


def compare_sheet(p, scale=3, size=(200, 140)):
    """Cove crops beside official Sea of Stars and Eastward coast and water scenes, all at the
    same character height (an adult 25 px) and the same scale."""
    ours = cove_preview(p, 1)
    crops = [('ours: the headland, its platform and pools', ours.crop((0, 360, 200, 500))),
             ('ours: the pier, the slipway and the beach', ours.crop((240, 380, 440, 520))),
             ('ours: the quay, its stair and the sea wall', ours.crop((420, 180, 620, 320))),
             ('ours: the bay\'s cliff over the shingle and sand', ours.crop((160, 160, 360, 300))),
             ('ours: the reef, the breakers and the far isles', ours.crop((380, 500, 580, 640))),
             ('ours: the path down the cliff\'s last face', ours.crop((440, 80, 640, 220)))]
    refs = []
    for (name, url, box, adult) in REFS:
        im = ref_image(url, box, adult)
        if im is not None:
            refs.append((name, im.crop((0, 0, min(im.width, size[0]), min(im.height, size[1])))))
    rows = max(len(crops), len(refs))
    cw, ch = size[0] * scale + 16, size[1] * scale + 30
    sheet = Image.new('RGB', (2 * cw + 16, rows * ch + 40), (46, 40, 52))
    _label(sheet, 'Ours (left) and official screenshots (right), all at an adult of 25 px, shown at 3x', (10, 10),
           (250, 214, 140))
    for i, (name, im) in enumerate(crops):
        sheet.paste(im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST), (10, 36 + i * ch))
        _label(sheet, name, (10, 36 + i * ch + im.height * scale + 2))
    for i, (name, im) in enumerate(refs):
        sheet.paste(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (cw + 16, 36 + i * ch))
        _label(sheet, name, (cw + 16, 36 + i * ch + im.height * scale + 2))
    return sheet


def kit_sheet(items, scale=2, groups=None, titles=None):
    """Every piece at `scale`, grouped, each labelled with its detail bar result."""
    pad, lab = 10, 30
    groups = groups or ['rock', 'shore', 'water', 'built', 'things']
    titles = titles or {'rock': 'Sea cliffs from the tileset, laid by the autotiler: pillow columns, lips, side bands, feet, the wet foot',
              'shore': 'The shore: sand with its wrack line and swash, shingle to its storm ridge, a platform with pools',
              'water': 'The sea: depth bands, the floor in the shallows, swell, surf; the layered south edge',
              'built': 'Built: a quay and its sea wall, a pier on piles, a slipway, the ways down',
              'things': 'Things: boulders, driftwood, a bollard'}
    maxw = 1500
    layout, y = [], 0
    for g in groups:
        y += 30
        x, rowh = pad, 0
        for it in items:
            if it[0] != g:
                continue
            w, h = it[2].w * scale, it[2].h * scale
            if x + w > maxw:
                x, y = pad, y + rowh + lab + pad
                rowh = 0
            layout.append((g, it, x, y))
            x += w + pad
            rowh = max(rowh, h)
        y += rowh + lab + pad
    sheet = Image.new('RGB', (maxw + pad, y + pad), (46, 40, 52))
    d = ImageDraw.Draw(sheet)
    seen = set()
    rows = []
    for (g, it, x, y0) in layout:
        if g not in seen:
            _label(sheet, titles[g], (pad, y0 - 22), (250, 214, 140))
            seen.add(g)
        img = it[2].image(scale)
        sheet.paste(img, (x, y0))
        subs = []
        for box, kind in it[3]:
            d.rectangle([x + box[0] * scale, y0 + box[1] * scale, x + box[2] * scale - 1, y0 + box[3] * scale - 1],
                        outline=(250, 214, 140))
            c, strict, ramp, line = bar_line(it[2].image(), box, kind)
            subs.append(line)
            rows.append((it[1], kind, c, strict, ramp))
        _label(sheet, it[1][:int(img.width / 6)], (x, y0 + img.height + 2))
        _label(sheet, ('  '.join(subs) if subs else 'judged by eye')[:int(img.width / 6)], (x, y0 + img.height + 15),
               (200, 200, 210))
    return sheet, rows


def tileset_sheet(scale=5):
    """The tileset itself, every picture at `scale` on a neutral ground, grouped and labelled."""
    groups = []
    for w in WIDTHS:
        groups.append((f'columns {w} px: three crowns, four bodies, two feet (sandstone; basalt below)',
                       [(tiles.COLUMNS[f'{k}{w}{c}'], 'bleached') for k, cs in
                        (('crown', 'abc'), ('body', 'abcd'), ('foot', 'ab')) for c in cs]))
    groups.append(('columns 14 px in basalt', [(tiles.COLUMNS[f'{k}14{c}'], 'basalt') for k, cs in
                                               (('crown', 'abc'), ('body', 'abcd')) for c in cs]))
    for kd in tiles.LIPS:
        groups.append((f'lips: {kd} (row 2 is the face\'s first row)', [(t, 'bleached') for t in tiles.LIPS[kd]]))
    groups.append(('side bands: lit west, dark east; caps (outer corners)',
                   [(t, 'bleached_warm') for t in tiles.BANDS['w']] + [(t, 'bleached_cool') for t in tiles.BANDS['e']]
                   + [(list(v), 'bleached') for v in tiles.BAND_CAPS.values()]))
    for kd in tiles.FEET:
        groups.append((f'feet: {kd}', [(t, 'stone') for t in tiles.FEET[kd]]))
    groups.append(('thrift and campion hanging over a face', [(t, 'bleached') for t in tiles.HANGS]))
    pad, maxw = 10, 1500
    layout, y = [], 10
    for title, items in groups:
        y += 22
        x, rowh = pad, 0
        for rows, ramp in items:
            w, h = len(rows[0]) * scale, len(rows) * scale
            if x + w > maxw:
                x, y, rowh = pad, y + rowh + pad, 0
            layout.append((title, rows, ramp, x, y))
            x += w + pad
            rowh = max(rowh, h)
        y += rowh + pad
    sheet = Image.new('RGB', (maxw + pad, y + pad), (46, 40, 52))
    seen = set()
    for (title, rows, ramp, x, y0) in layout:
        if title not in seen:
            _label(sheet, title, (pad, y0 - 18), (250, 214, 140))
            seen.add(title)
        h, w = len(rows), len(rows[0])
        img = np.full((h, w, 3), (92, 86, 98), np.uint8)
        for yy, r in enumerate(rows):
            for xx, ch in enumerate(r):
                if ch in KEY:
                    f_, t = decode(ch, IDX[ramp])
                    img[yy, xx] = COL[f_, t]
                elif ch in '-=':
                    img[yy, xx] = (60, 52, 66) if ch == '=' else (74, 68, 80)
        sheet.paste(Image.fromarray(img).resize((w * scale, h * scale), Image.NEAREST), (x, y0))
    return sheet


def _reaches(walk, a, b):
    """Whether a four-neighbour walk from a reaches b."""
    seen = np.zeros(walk.shape, bool)
    seen[a[1], a[0]] = walk[a[1], a[0]]
    while True:
        grown = dilate(seen, 1) & walk
        if grown[b[1], b[0]]:
            return True
        if (grown == seen).all():
            return False
        seen = grown


def check(p=None, parts=None) -> list:
    """The kit's contracts on the cove: the path down can be walked from the cliff top to
    the pier's end, and to the slipway and the platform; it changes tier only by its ramp
    and its stair (no face is walkable); the sea, the pools and the reef stop a walker
    (only the pier's deck crosses the water); the ramp is at least 24 wide, the stair 40
    open, the pier 32 wide and the slipway 28 running at least 16 into the water."""
    faults = []
    if p is None:
        p, parts = cove()
    R = parts['R']
    a = (600, 4)
    for name, b in (('the pier\'s end', (312, 540)), ('the slipway', (404, 432)), ('the platform', (120, 500)),
                    ('the quay', (560, 250)), ('the shelf', (540, 150))):
        if not p.walk[a[1], a[0]] or not p.walk[b[1], b[0]]:
            faults.append(f'the path to {name}: an end is not walkable ({bool(p.walk[a[1], a[0]])}, '
                          f'{bool(p.walk[b[1], b[0]])})')
        elif not _reaches(p.walk, a, b):
            faults.append(f'the path cannot be walked from the cliff top to {name}')
    ways = parts['ramp'] | parts['stair']
    bad = p.walk & R.face & ~ways
    if bad.any():
        ys, xs = np.nonzero(bad)
        faults.append(f'{int(bad.sum())} face pixels outside the ramp and stair are walkable (e.g. {xs[0]}, {ys[0]})')
    wet = p.walk & (p.wet | p.hazard) & ~parts['pier']
    if wet.any():
        ys, xs = np.nonzero(wet)
        faults.append(f'{int(wet.sum())} water, pool or reef pixels are walkable (e.g. {xs[0]}, {ys[0]})')
    r = parts['ramp']
    cols = r.sum(0)
    if r.any() and np.median(cols[cols > 0]) < 20:
        faults.append('the ramp is narrower than 24 px on screen')
    st = parts['stair']
    if st.any():
        xs = np.nonzero(st.any(0))[0]
        if xs.max() - xs.min() + 1 < 40:
            faults.append('the stair is narrower than 40 px open')
    pm = parts['pier']
    if pm.any():
        xs = np.nonzero(pm.any(0))[0]
        if xs.max() - xs.min() + 1 < 32:
            faults.append('the pier is narrower than 32 px')
    sl = parts['slip']
    under = sl & False
    if sl.any():
        xs = np.nonzero(sl.any(0))[0]
        if xs.max() - xs.min() + 1 < 28:
            faults.append('the slipway is narrower than 28 px')
        under = (p.x >= xs.min()) & (p.x <= xs.max()) & p.wet & (p.y < np.nonzero(sl.any(1))[0].max() + 40)
        if np.nonzero(under.any(1))[0].size < 16:
            faults.append('the slipway runs less than 16 px into the water')
    return faults


def main(argv):
    if '--check' in argv:
        faults = check()
        for f in faults:
            print('FAULT:', f)
        print('coast_kit check:', 'pass' if not faults else f'{len(faults)} faults')
        return 1 if faults else 0
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-coast-kit')
    os.makedirs(out, exist_ok=True)
    p, parts = cove()
    p.image().save(os.path.join(out, 'cove.png'))
    cove_preview(p, 2).save(os.path.join(out, 'cove-2x.png'))
    night(cove_preview(p, 1)).resize((p.w * 2, p.h * 2), Image.NEAREST).save(os.path.join(out, 'cove-night.png'))
    frames, box = flow_frames(p)
    if box is not None:
        crop = (240, 380, 560, 640)
        fr = [f.crop(crop).resize(((crop[2] - crop[0]) * 2, (crop[3] - crop[1]) * 2), Image.NEAREST) for f in frames]
        fr[0].save(os.path.join(out, 'cove-flow.gif'), save_all=True, append_images=fr[1:], duration=150, loop=0)
    print('cove boxes:')
    boxes = [(face_box(parts['R'], reg, avoid=parts['quay_face']), kind, what) for reg, kind, what in COVE_FACES]
    for box, kind, what in boxes + list(COVE_BOXES):
        c, strict, ramp, line = bar_line(p.image(), box, kind)
        print(f'  {what:46s} {line}  isolated {c["isolated"]:.3f} cluster {c["cluster"]:.1f}')
    compare_sheet(p).save(os.path.join(out, 'compare.png'))
    items = pieces()
    sheet, rows = kit_sheet(items)
    sheet.save(os.path.join(out, 'kit-sheet.png'))
    tileset_sheet(5).save(os.path.join(out, 'tileset.png'))
    print('kit pieces:')
    for name, kind, c, strict, ramp in rows:
        print(f'  {name[:60]:60s} {kind:10s} t{c["tones"]:5.1f} s{c["shapes"]:5.1f} d{c["dressing"]:5.1f} '
              f'iso {c["isolated"]:.3f} cl {c["cluster"]:.1f}  {"PASS" if strict else "PASS@85" if ramp else "FAIL"}')
    faults = check(p, parts)
    print('check:', 'pass' if not faults else '; '.join(faults))
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
