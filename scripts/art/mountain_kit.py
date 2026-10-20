"""The mountain and snow kit: the pieces the massif and the Frostline are painted with.

Claude A's lane (the routes, the thresholds and the world's north edge). Matt, 20 Oct 20:04,
on the summit crop: "i hope this is not finished. there is so much wrong with this. non of
this looks natural (given the soft grid), there is no verticality, hard edges, the mountains
could use some improvement and so on". Patching the old zones cannot get there, so this kit
builds the mountains again from the soft grid, as a pilot that proves the look before any
region is rebuilt. Nothing in the game reads it yet.

Verticality is the soft grid's (verticality.md 4f, terrace.py on PR #90): a mountain is
stacked tiers, not a painted triangle. A tier is one south face of 32 px (16 for a low step
such as the moraine lip); only the south face is a face; west and east ends are 5 px side
bands, lit on the west and in the two darkest tones on the east; every tier throws a
constant 8 px shadow down and to the right; frame cliffs are stacked tiers with a ledge
every 32 to 44 px, often two tiers stacked into one face of 64 (size guide 7). The walked
benches are laid cell by cell with meandering rims (straight only where a ramp or a stair
is cut); the frame is built from masses (each a stack of noisy blobs stepping north and
narrowing, so its outline wanders in lobes and bays), a far range with a skyline, and
couloirs and buttresses carved diagonally down the walls; then every level is fitted to
the grid (runs of two cells or more, a face and a ledge between tiers or a stack of two,
corners rounded by a cell), so no ground meets another along a ruled line.

Everything is drawn in the house style (docs/vision/house-style.md, PR #121): every pixel is
a tone of a house ramp (art/house-palette.json) or a family's edge tone; shade and light move
along the ramps (no RGB arithmetic); texture is clusters of two to four pixels; light comes
from the upper left; cast shadows step the ground two tones down its own ramp, so shade on
snow is the snow ramp's own blue violet. Rock is the stone family and its siblings with
slate in the deepest shade; snow is the snow family. Snow follows the house recipe: one
calm, wide plane at body tone, broad swells a tone lighter, a crisp scalloped edge (6 px)
with a lit lip over its shaded south face, blue shade in hollows and on the south and east
of things, drifts in the lee of rocks and walls, wind ripples and sastrugi in clusters,
tracks pressed in, sparkles in pairs. The wind comes from the west, so drifts trail east.

Sizes follow docs/vision/size-guide.md (PR #124): an adult 25 px, tier faces 32, a low step
16, side bands 5, cast shadows 8, a mountain trail 16 and ramps 24 along a face at 1 in 3
with a parapet on the open side, stairs 40 open between 4 px cheeks, a stream 16 to 24,
a waterfall as wide as its channel into a pool 8 wider each side, a lake (the tarn) 240 or
more, boulders 16 to 32, a cairn 12 to 28, a hut with eaves at 40 to 44 and a 32 x 14 door,
pines thinning out with height and stopping below the col.

The model is the river kit's and the dry kit's (#133 and #137): a `Plot` holds the house
ramp and tone of every pixel, pieces paint masks into it, standing things are `Sprite`s
pasted with an edge-tone outline and a cast shadow. The shared core (noise, the plot,
clusters, outline, shadow, sprites) is copied from the dry kit so the kits stay independent
until they land; once they do it can move into one module they all import. Pieces that
paint a mask run on its bounding box only (`local`), which keeps the pilot to about 30 s.

The pieces (each with a seed, all deterministic):
- relief: `Relief` (tiers with their own heights: faces of 16, 32 and stacks of two),
  `smooth()`, `soft_grid_cells()` (a cell map fitted to the soft grid), `organic_rim()`,
  `mass_cells()`, `range_cells()` and `grooves()` (the pilot's benches, crags, far range,
  couloirs and buttresses).
- rock: `rock_faces()` (rounded granite blocks packed along beds that dip gently east,
  small lumps inside them, ledges with snow lying on them, lichen, water stains, a snow
  cornice, a grass lip or a lit coping at the rim, a dark foot; lit by `facet_light()` on
  the benches and `frame_light()` on the frame, so each mass and buttress is lit west and
  shaded east with one hard terminator), `side_bands()`, `tier_shadows()`, `talus()`,
  `scree_fan()` (lobed fans, the big stones running furthest, thinning onto the snow),
  `rock_ground()` (bare ledges), `boulder()`.
- snow: `snowfield()` (the calm plane, swells, blue hollows, ripples and sastrugi in
  clusters, sparkles in pairs), `snow_patches()` and `ledge_snow()` (where snow lies:
  in shade, at the backs of ledges, along lit rims), `snow_edge()` (the crisp scalloped
  edge), `cliff_feet()` (blue shade at the foot of cliffs), `drift()` (lee tails),
  `tracks()` (boot prints pressed in, a sledge's runners), `rocks_in_snow()`.
- ground: `alpine_turf()` and `meadow()` (calm, with `tuft()` and `flower_clump()`),
  `gravel()`, `fir()` (spires of needle layers with snow on them).
- ice and water: `glacier()` (névé with crevasses lit on the far wall, bare ice in ogive
  bands, a medial moraine), `ice_faces()` (the icefall: the glacier over the tiers as ice
  cliffs and broken ice, the north border), `snout()` (the tongue's front with its
  portal), `tarn()` (a rounded rectangle, deep in the middle, a broken reflection of the
  north bank, a lit lip on the south shore, an ice sheet and floes in the shade),
  `channel()` and `fall()` (meltwater down the step in straight falls into pools).
- built and placed: `trail()` (earth below, a trodden trench in snow above),
  `ramp_along()` (a ramp along a face with a drystone retaining wall and a parapet),
  `stair()`, `drystone()` (a sheep wall with its gate), `col_hut()` (the valley kit's
  stone hut from house_kits.py with snow on its roof), `cairn()`, `noticeboard()`,
  `fire_ring()`, `sledge()`.
- `haze()`: what lies beyond the far range, lighter and cooler towards the top edge.

Run:
    python3 scripts/art/mountain_kit.py --check     (walk contracts; exits non-zero on a fault)
    python3 scripts/art/mountain_kit.py [OUT_DIR]
writes OUT_DIR/pilot.png (the Col Path climbing in switchbacks past the Col hut to the
Frostline lip, the cirque with its tarn under the headwall, the massif and its icefall
beyond, 640 x 1152 at 1x), pilot-2x.png (with residents standing in it for scale),
pilot-night.png, kit-sheet.png (every piece at 2x, labelled with its detail bar result),
compare.png (pilot crops beside Eastward and Sea of Stars mountain and cliff scenes at the
same character height, when the screenshots are in REF_DIR), and prints the bar for the
measured boxes. Default OUT_DIR: napattack-mountain-kit in the system's temp folder, never
the repository.
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

# The soft grid (verticality.md 4f; terrace.py on PR #90; size guide 7)
GRID = 8
FACE = 32          # a tier's face
LOW = 16           # a low step (the moraine lip)
STRIP = 5          # a side band: 0.2 of an adult
SHADOW = 8         # a tier's cast shadow, whatever its height
THROW = 1.0        # sprites' shadows (the desert kit throws 1.3)


# --- noise (deterministic, numpy) ---------------------------------------------------------
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


# --- the plot: ramps and tones ------------------------------------------------------------
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


# --- outline, shadow, sprites --------------------------------------------------------------
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


# --- small ground things ----------------------------------------------------------------------
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


# --- light and smoothing helpers -------------------------------------------------------------
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


# --- relief: tiers with their own heights ------------------------------------------------------
def smooth(T, seed=0, round_r=6, wob=1.5):
    """Round a tier map's corners (close, then open, per level) and let its edges wander a
    pixel or two inside their edge cells. Each level is kept inside the one below it, so
    where the ground drops two tiers at once the two edges stay one edge."""
    T = np.asarray(T)
    top = int(T.max())
    lo = int(T.min())
    h, w = T.shape
    y, x = np.mgrid[0:h, 0:w]
    n = (fbm(x, y, 9, seed) - 0.5) * 2 * wob
    masks = {}
    for k in range(top, lo, -1):
        m = rounded(T >= k, max(1, round_r // 2))
        if wob:
            d_in, d_out = edge_dist(m, 3), edge_dist(~m, 3)
            m = (m & ~((d_in <= 2) & (n < -(d_in - 0.5)))) | (~m & (d_out <= 2) & (n > d_out - 0.5))
        if k < top:
            m |= masks[k + 1]
        masks[k] = m
    out = np.full(T.shape, lo, np.int16)
    for k in range(lo + 1, top + 1):
        out[masks[k]] = k
    return out


def fix_runs(r, min_run=2):
    """No rim run shorter than `min_run` columns (a diagonal is a staircase of runs of two
    cells or more): a lone column takes the value of the neighbour nearer to it."""
    r = np.array(r)
    for _ in range(4):
        changed = False
        i = 0
        n = len(r)
        while i < n:
            j = i
            while j + 1 < n and r[j + 1] == r[i]:
                j += 1
            if j - i + 1 < min_run and n >= min_run:
                left = r[i - 1] if i > 0 else None
                right = r[j + 1] if j + 1 < n else None
                cands = [v for v in (left, right) if v is not None]
                if cands:
                    best = min(cands, key=lambda v: abs(int(v) - int(r[i])))
                    r[i:j + 1] = best
                    changed = True
            i = j + 1
        if not changed:
            break
    return r


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


# --- rock: jointed granite in dipping beds ---------------------------------------------------------
ROCK = ('stone', 'stone_warm', 'stone_cool', 'slate_warm', 'ashlar_cool')
RIMS = {'rock': 0, 'snow': 1, 'turf': 2}


def beds(s, seed=0, thick=(6, 11)):
    """Beds along a dipping stratum coordinate s (px): the bed index, the row from the bed's
    top and its thickness. Beds are 6 to 11 px, every one a little different."""
    s = np.asarray(s, np.float64)
    lo, hi = int(np.floor(s.min())) - 2, int(np.ceil(s.max())) + 2
    edges = [lo]
    i = 0
    while edges[-1] < hi:
        edges.append(edges[-1] + thick[0] + int(hash01(i, 3, seed) * (thick[1] - thick[0] + 1)))
        i += 1
    e = np.array(edges)
    bi = np.clip(np.searchsorted(e, s, side='right') - 1, 0, len(e) - 2)
    top_of = e[bi + 1]
    th = e[bi + 1] - e[bi]
    row = (top_of - 1 - np.floor(s)).astype(int)
    return bi, np.clip(row, 0, th - 1), th


def facet_light(p, R, seed=0, scale=46):
    """The broad light on every face: where the ground rises to the east the face turns west
    to the light, where it falls the face turns east into shade (the ends of tiers, the
    flanks of spurs), plus buttresses: broad masses each lit on its west side and shaded on
    its east, so every buttress has one hard terminator. Returns a value about -1..1."""
    Tb = box_blur(np.where(R.face, R.kf, R.T).astype(np.float64), 12)
    gx = (shift(Tb, -3, 0, 0) - shift(Tb, 3, 0, 0))
    gx = np.where(np.abs(gx) > 5, 0, gx)
    # buttresses: a saw in x (lit rising to a crest, then a hard drop into shade), its crests
    # leaning with height and spaced unevenly, so they never read as a row of pipes
    el = R.elev.astype(np.float64)
    warp = (fbm(p.x, el, 70, seed + 3) - 0.5) * scale * 1.4 + el * 0.35
    u = (p.x + warp) / scale
    cell = np.floor(u)
    frac = u - cell
    crest = 0.45 + 0.35 * (hash01(cell.astype(int), 0, seed + 4) - 0.5)
    lit_side = frac < crest
    amp = 0.35 + 0.65 * hash01(cell.astype(int), 1, seed + 5)
    saw = np.where(lit_side, 0.55 * amp, -0.55 * amp)
    return np.clip(gx * 1.6 + saw, -1.2, 1.2)


def vcells(x, y, cw, ch, seed, jitter=0.8):
    """Cells of a jittered grid of cw x ch: for every pixel the distance to its nearest
    centre (d1) and the second nearest (d2), the cell's id and its centre."""
    gx, gy = np.floor(x / cw).astype(np.int64), np.floor(y / ch).astype(np.int64)
    d1 = np.full(np.shape(x), 1e9)
    d2 = np.full(np.shape(x), 1e9)
    c1x = np.zeros(np.shape(x))
    c1y = np.zeros(np.shape(x))
    cid = np.zeros(np.shape(x), np.int64)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = gx + ox, gy + oy
            px = (cx + 0.5 + (hash01(cx, cy, seed) - 0.5) * jitter) * cw
            py = (cy + 0.5 + (hash01(cx, cy, seed + 1) - 0.5) * jitter) * ch
            d = np.hypot(x - px, y - py)
            closer = d < d1
            second = ~closer & (d < d2)
            d2 = np.where(closer, d1, np.where(second, d, d2))
            d1 = np.where(closer, d, d1)
            c1x = np.where(closer, px, c1x)
            c1y = np.where(closer, py, c1y)
            cid = np.where(closer, (cx * 7919 + cy * 104729) & 0xFFFFF, cid)
    return d1, d2, cid, c1x, c1y


def rock_faces(p: Plot, R: Relief, m=None, seed=0, snow=0.0, dip=0.12, lichen=0.04, rim='rock',
               haze=0, mass=(26, 19), ledges=0.3, light=None):
    """Paint the south faces in m as alpine granite, in two scales as Sea of Stars and
    Eastward draw rock. Masses: big rounded bodies 14 to 40 px across, packed along beds that
    dip gently east, each lit from the upper left in hard steps on top of the face's broad
    light (`facet_light`: buttresses lit west and shaded east, tier ends turning to the light
    or away), split by dark crevices. Inside each mass, small lumps 6 to 9 px at low contrast:
    a lit edge on each lump's upper left, a dark seam on its lower right. Some bed tops are
    ledges (`ledges`): a lit lip with snow lying on it (`snow`: 0 none, 1 every ledge), the
    overhang's shadow under it, water stains hanging below. Lichen on lit masses. The rim
    gets a snow cornice (`rim='snow'`), a grass lip (`'turf'`) or a lit coping of rock, the
    foot is dark. `haze` (1 or 2) lifts the darkest tones on far faces."""
    fc = R.face if m is None else (R.face & np.asarray(m, bool))
    if not fc.any():
        return
    snow = np.broadcast_to(np.asarray(snow, np.float64), p.f.shape)
    rimk = np.full(p.f.shape, RIMS[rim], np.int8) if isinstance(rim, str) else np.asarray(rim, np.int8)
    el = R.elev.astype(np.float64)
    warp = (fbm(p.x, el, 37, seed) - 0.5) * 4.0
    s = el + p.x * dip + warp                 # height along the dipping beds
    ys = -s                                   # the same, increasing down the screen
    lam_f = facet_light(p, R, seed + 7) if light is None else np.asarray(light, np.float64)
    # lumps: rounded bodies packed along the dipping beds (Eastward's and Sea of Stars' rock),
    # each lit in a crescent on its upper left and darker to the lower right, in a dark matrix
    d1, d2, cid, cx, cy = vcells(p.x.astype(np.float64), ys, mass[0], mass[1], seed + 1, 0.85)
    gap = d2 - d1
    rad = (0.74 + 0.2 * hash01(cid, 6, seed + 6)) * np.hypot(mass[0], mass[1]) * 0.5
    crev = (gap < 1.6) | (d1 > rad)
    u = (p.x - cx) / (mass[0] * 0.55)
    v = (ys - cy) / (mass[1] * 0.55)
    lam_l = light_of(u, v, 0.3)
    lam = lam_f + 0.35 * np.clip(lam_l, -1, 1)
    body = np.where(lam > 0.45, 4, np.where(lam > 0.0, 3, np.where(lam > -0.5, 2, 1))).astype(np.int16)
    sib = hash01(cid, 0, seed + 8)
    fam = np.where(sib < 0.26, IDX['stone_warm'], np.where(sib > 0.84, IDX['slate_warm'],
                   np.where(sib > 0.62, IDX['stone_cool'], np.where(sib > 0.54, IDX['ashlar_cool'], IDX['stone']))))
    odd = hash01(cid, 1, seed + 9)
    tone = body + np.where(odd < 0.10, -1, 0)
    crescent = ~crev & (lam_l > 0.55) & (body >= 2)
    tone = np.where(crescent, tone + 1, tone)
    lower = ~crev & (lam_l < -0.45)
    tone = np.where(lower, tone - 1, tone)
    tone = np.where(crev, np.where(body >= 4, 2, np.where(body >= 2, 1, 0)), tone)
    # small lumps inside each block, at low contrast: a seam a tone down on each lump's lower
    # right, a lit edge on its upper left (the texture of the rock, never its structure)
    e1, e2, lid, lx, ly = vcells(p.x * 1.0, ys, 7, 5, seed + 2, 0.95)
    seam = (e2 - e1 < 0.8) & ~crev
    tone = np.where(seam & (body >= 2), tone - 1, tone)
    lit_edge = shift(seam, 1, 1, False) & ~seam & ~crev & (body >= 2) & ~crescent
    tone = np.where(lit_edge & (hash01(lid, 2, seed + 3) < 0.35), tone + 1, tone)
    # beds and ledges: some bed tops step out as ledges across the masses
    bi, row, th = beds(s, seed + 4, (7, 13))
    hard = hash01(bi, 2, seed + 10) < ledges
    ledge = fc & hard & (row <= 1) & (R.depth > 3) & (R.depth < R.fh - 3)
    tone = np.where(ledge & (row == 0), np.maximum(tone, 4), tone)
    tone = np.where(ledge & (row == 1), np.maximum(tone, 3), tone)
    under = fc & hard & shift(ledge & (row == 1), 0, 1, False) & ~ledge
    under2 = fc & hard & shift(under, 0, 1, False) & ~ledge & ~under
    tone = np.where(under, np.minimum(tone - 2, 1), tone)
    tone = np.where(under2, tone - 1, tone)
    tone = np.clip(tone, 0, 5)
    if haze:
        tone = np.clip(tone, haze, 5)
    p.f[fc] = fam[fc]
    p.t[fc] = tone[fc].astype(np.int8)
    deep = fc & (p.t == 0)
    p.f[deep] = IDX['slate_cool']
    p.t[deep] = 1
    p.f[fc & (p.t == 1) & ~deep] = IDX['stone_cool']
    if haze:
        p.t[deep] = np.maximum(p.t[deep], 1 + haze // 2)
    # grain: sibling swaps inside the masses (shape without value noise)
    inner = fc & ~crev & ~seam & ~ledge & ~under & (R.depth > 1)
    stamp(p, inner, 0.05, seed + 12, SMALL, swap='mix')
    # lichen: crusts on lit masses, clusters of two to four
    if lichen:
        lit_m = inner & (lam > 0.25) & (p.t >= 3) & (hash01(cid, 4, seed + 13) < 0.5)
        stamp(p, lit_m, lichen * 0.35, seed + 15, SMALL, ramp='brass_cool', tone=3, same_family=False)
        stamp(p, lit_m, lichen * 0.35, seed + 16, SMALL, ramp='grass_cool', tone=4, same_family=False)
    # water stains: dark streaks hanging from ledges, two px wide
    vstart = under2 & (hash01(p.x // 2, bi, seed + 17) < 0.2)
    vlen = (3 + hash01(p.x // 2, bi, seed + 18) * 8).astype(int)
    stain = np.zeros(p.f.shape, bool)
    for d in range(1, 12):
        stain |= shift(vstart & (vlen >= d), 0, d, False)
    stain = (stain | shift(stain, 1, 0, False)) & fc & ~crev & ~ledge
    p.f[stain] = COOL[p.f[stain]]
    p.step(stain & (p.t >= 2), -1)
    # snow lying on the ledges (house snow: lit lip, body, a scalloped shaded underside)
    if (snow[fc] > 0).any():
        segw = 7
        seg = (p.x + (hash01(bi, 5, seed) * 7).astype(int)) // segw
        on = ledge & (hash01(seg, bi, seed + 19) < snow * 0.55) & (lam > -0.7)
        on |= ledge & (hash01(seg - 1, bi, seed + 19) < snow * 0.55) & (lam > -0.7) & (hash01(seg, bi, seed + 31) < 0.6)
        lit = lam > -0.1
        cap0 = on & (row == 0)
        cap1 = on & (row == 1)
        scal = (p.x + (hash01(bi, 5, seed) * 7).astype(int)) % segw
        hang = fc & shift(cap1, 0, 1, False) & ~cap0 & ~cap1 & (scal >= 1) & (scal <= 4)
        p.put(cap0, 'snow', np.where(lit, 5, 3))
        p.put(cap1, 'snow', np.where(lit, 4, 2))
        p.put(hang, 'snow', np.where(lit, 2, 1))
        p.f[cap0 & ~lit] = IDX['snow_cool']
        sh = shift(hang, 0, 1, False) & fc & ~cap0 & ~cap1 & ~hang
        p.step(sh, -1, lo=0)
    # the rim: a snow cornice, a grass lip or a lit coping of rock, by what lies above it
    lip0 = fc & (R.depth == 0)
    lip20 = fc & (R.depth == 1)
    for kind in (1, 2, 0):
        lip, lip2 = lip0 & (rimk == kind), lip20 & (rimk == kind)
        if not (lip | lip2).any():
            continue
        if kind == 1:
            scal = (p.x + 3) % 6
            p.put(lip, 'snow', 4)
            p.put(lip & (scal < 3), 'snow', 5)
            hang1 = lip2 & (scal >= 1) & (scal <= 4)
            p.put(hang1, 'snow', 2)
            hang2 = fc & (rimk == 1) & (R.depth == 2) & (scal >= 2) & (scal <= 3)
            p.put(hang2, 'snow', 1)
            shade = fc & (rimk == 1) & (((R.depth == 2) & ~hang2) | ((R.depth == 1) & ~hang1) |
                                        ((R.depth == 3) & shift(hang2, 0, 1, False)))
            p.step(shade, -1, lo=0)
        elif kind == 2:
            scal = (p.x + (hash01(p.x // 6, 0, seed) * 3).astype(int)) % 6
            p.put(lip, 'grass_cool', 4)
            p.put(lip & (scal <= 1), 'grass_cool', 5)
            hang1 = lip2 & (scal >= 1) & (scal <= 4)
            p.put(hang1, 'grass_cool', 2)
            root = fc & (rimk == 2) & (R.depth >= 2) & (R.depth <= 4) & (hash01(p.x // 2, 0, seed + 21) < 0.05)
            p.put(root, 'earth', 1)
            p.step(fc & (rimk == 2) & (R.depth == 2) & ~root, -1, lo=0)
        else:
            p.t[lip] = np.maximum(p.t[lip], 4)
            glint = lip & (hash01(p.x // 2, p.y, seed + 22) < 0.25) & shift(lip, 1, 0, False)
            p.t[glint] = 5
            p.step(lip2 & ~crev, -1, lo=0)
    lip = lip0
    # the foot: dark, a contact line
    foot = fc & (R.depth >= R.fh - 2)
    p.step(foot & (FAMILY[p.f] != IDX['snow']), -1, lo=0)
    last_row = fc & (R.depth == R.fh - 1)
    p.t[last_row] = np.minimum(p.t[last_row], 1)
    # the ends of a face: the west end turns into the light, the east end into shade
    w_end = fc & ~shift(R.face, 1, 0, False)
    e_end = fc & ~shift(R.face, -1, 0, False)
    for i in range(3):
        we = shift(w_end, i, 0, False) & fc & (FAMILY[p.f] != IDX['snow'])
        ee = shift(e_end, -i, 0, False) & fc & (FAMILY[p.f] != IDX['snow'])
        p.step(we & (p.t < 4), 1 if i < 2 else 0)
        p.step(ee, -1, lo=1 if i else 0)
    despeckle(p, fc & ~lip)
    p.solid |= fc
    p.walk &= ~fc


def side_bands(p: Plot, R: Relief, seed=0, snowy=None):
    """The side bands (soft grid: 5 px): where a top ends to the west or east above lower
    ground, its last 5 px are the rock seen edge-on, a column of lumps 3 to 5 px tall, lit
    when it faces west and in the two darkest tones when it faces east, with an outline where
    it meets the ground. On snowy tops the band carries a cap of snow along its top edge.
    Back rims (a top's north edge over lower ground) get a lit lip and a hidden drop."""
    T = R.T
    seen = R.seen()
    band_w = np.zeros(p.f.shape, bool)
    band_e = np.zeros(p.f.shape, bool)
    dist_w = np.zeros(p.f.shape, np.int8)
    dist_e = np.zeros(p.f.shape, np.int8)
    for k in range(int(T.min()) + 1, int(T.max()) + 1):
        topk = R.top(k)
        low = (seen >= 0) & (seen < k)
        for i in range(STRIP, 0, -1):
            bw = topk & shift(low, i, 0, False)
            be = topk & shift(low, -i, 0, False)
            band_w |= bw
            band_e |= be
            dist_w[bw] = i
            dist_e[be] = i
        back = topk & shift(low, 0, 1, False)
        p.step(back & ~p.solid, 1)
        drop = low & shift(topk, 0, -1, False) & ~R.face
        p.t[drop] = EDGE_T
        p.step(low & shift(topk, 0, -2, False) & ~R.face & ~drop, -1)
        p.walk &= ~(dilate(back, 1) & topk)
        p.walk &= ~(topk & (shift(low, 0, 1, False) | shift(low, 0, 2, False) | shift(low, 0, 3, False)))
    band_e &= ~band_w | (dist_e <= dist_w)
    band_w &= ~band_e
    # the band's rock: irregular lumps 3 to 6 px tall stacked down the band (never rungs),
    # each lit along its top, a dark seam under it
    e1, e2, lid, lx, ly = vcells(p.x * 1.6, p.y.astype(np.float64), 6, 5, seed + 3, 0.95)
    seam = (e2 - e1) < 0.9
    top = ~seam & shift(seam, 0, 1, False)
    sib = hash01(lid, 0, seed + 1)
    fam = np.where(sib < 0.35, IDX['stone_warm'], np.where(sib > 0.7, IDX['stone_cool'], IDX['stone']))
    p.f[band_w] = fam[band_w]
    p.t[band_w] = np.where(seam[band_w], 2, np.where(top[band_w], 5, 4))
    p.t[band_w & (dist_w <= 1)] = np.minimum(p.t[band_w & (dist_w <= 1)], 3)
    p.f[band_e] = np.where(sib[band_e] < 0.5, IDX['stone_cool'], IDX['stone'])
    p.t[band_e] = np.where(seam[band_e], 0, np.where(top[band_e], 2, 1))
    # the outer edge of each band: a dark line on the ground side
    edge_w = shift(band_w, -1, 0, False) & ~band_w & ~R.face & ~band_e
    edge_e = shift(band_e, 1, 0, False) & ~band_e & ~R.face & ~band_w
    p.t[edge_w] = np.minimum(p.t[edge_w], 1)
    p.t[edge_e] = EDGE_T
    if snowy is not None:
        sn = np.asarray(snowy, bool)
        capw = band_w & sn & ~shift(band_w, 0, 1, False)
        cape = band_e & sn & ~shift(band_e, 0, 1, False)
        p.put(capw, 'snow', 5)
        p.put(cape, 'snow', 3)
        p.put(shift(capw, 0, -1, False) & band_w, 'snow', 4)
        p.put(shift(cape, 0, -1, False) & band_e & (p.x % 3 != 0), 'snow', 2)
    p.solid |= band_w | band_e
    p.walk &= ~(band_w | band_e)
    return band_w, band_e


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


# --- snow (house style: one calm plane, a crisp edge, blue shade, wind) ---------------------------
def snowfield(p: Plot, m, seed=0, swells=0.13, hollows=0.08, ripples=0.5, sastrugi=0.4, sparkle=0.004):
    """Snow as the house style draws it: one calm, wide plane at body tone in broad sibling
    patches (shape without value noise), long swells a tone lighter lying across the wind,
    each with a thin lee line, a few long hollows in blue shade with their far lip lit, wind
    ripples in clusters (a lit crest over a shaded trough, 4 to 9 px long, 3 px apart),
    sastrugi in other clusters (tapered ridges pointing downwind, blunt and lit at their
    windward west end, shaded underneath), and sparkles in pairs. No grit, no blobs."""
    m = np.asarray(m, bool)
    if not m.any():
        return
    x, y = p.x, p.y
    n = fbm(x * 0.5, y, 40, seed)
    fam = np.where(n < 0.4, IDX['snow_cool'], np.where(n > 0.62, IDX['snow_warm'], IDX['snow']))
    p.f[m] = fam[m]
    p.t[m] = 3
    sw = fbm(x * 0.22, y, 7, seed + 1)
    if swells:
        cut = np.quantile(sw[m], 1 - swells)
        swm = m & (sw > cut)
        swm = rounded(swm, 1)
        p.t[swm] = 4
        lee = shift(swm, 1, 1, False) & ~swm & m & ~shift(swm, 0, 1, False)
        lee |= shift(swm, 0, 1, False) & ~swm & m & (hash01(x // 4, y, seed + 9) < 0.5)
        p.t[lee] = 2
    if hollows:
        cut = np.quantile(sw[m], hollows)
        hol = rounded(m & (sw < cut), 1)
        p.t[hol] = 2
        p.f[hol] = IDX['snow_cool']
        lip = shift(hol, 0, 1, False) & ~hol & m
        p.t[lip] = 4
    # wind ripples in clusters
    if ripples:
        cl = m & (vnoise(x, y, 34, seed + 2) > 1 - ripples * 0.55) & erode(m, 3)
        wav = np.round(np.sin(x / 9.0 + y / 31.0) * 1.2).astype(int)
        r = (y + wav) % 4
        segx = (x + (hash01(y // 4, 0, seed + 3) * 9).astype(int))
        seg_on = (segx % 9) < 6
        seg_on &= hash01(segx // 9, y // 4, seed + 4) < 0.55
        crest = cl & (r == 0) & seg_on & (p.t == 3)
        trough = shift(crest, 0, 1, False) & cl & (p.t == 3)
        p.t[crest] = 4
        p.t[trough] = 2
    # sastrugi in other clusters
    if sastrugi:
        cl = m & (vnoise(x, y, 46, seed + 5) > 1 - sastrugi * 0.5) & erode(m, 4)
        for i, (sx, sy) in enumerate(_scatter(cl, 150, seed + 6, margin=0)):
            L = 6 + int(hash01(sx, sy, seed + 7) * 9)
            for j in range(L):
                px = sx + j
                if px >= p.w:
                    break
                taper = 1 if j > L * 0.6 else 2
                for k in range(taper + 1):
                    py = sy + k
                    if py >= p.h or not m[py, px]:
                        continue
                    if k == 0:
                        p.t[py, px] = 5 if j < 3 else 4
                    elif k < taper:
                        p.t[py, px] = 3
                    else:
                        p.t[py, px] = 2
                        p.f[py, px] = IDX['snow_cool']
    if sparkle:
        sp = m & (p.t >= 3) & (hash01(x // 2, y, seed + 8) < sparkle) & (x % 2 == 0)
        sp |= shift(sp, 1, 0, False) & m
        p.t[sp] = 5
    despeckle(p, m & (p.t < 5))


def snow_patches(p: Plot, m, cover, seed=0, scale=34, shade=None):
    """Where snow lies on other ground: patches whose outline is a natural shape (lobes of
    16 to 48 px, never a line), more of them in shade and hollows (`shade`: 0..1)."""
    m = np.asarray(m, bool)
    n = fbm(p.x * 0.8, p.y, scale, seed)
    if shade is not None:
        n = n + 0.35 * np.asarray(shade, np.float64)
    if not m.any():
        return np.zeros(p.f.shape, bool)
    cut = np.quantile(n[m], 1 - cover) if cover < 1 else -1
    s = m & (n > cut)
    s = rounded(s, 2)
    s = wobble(s, seed + 1, 1.5, 7) & m
    return s


def snow_edge(p: Plot, snow, ground=None, seed=0):
    """The crisp edge where snow ends on other ground (house snow): on its south side a lit
    lip (5) over the snow's shaded south face (2, then 1) hanging in 6 px scallops, the ground
    below two tones down; a lit rim on its west and north sides, a shaded one on the east
    with the ground beside it a tone down."""
    snow = np.asarray(snow, bool)
    ground = ~snow if ground is None else (np.asarray(ground, bool) & ~snow)
    ground &= ~p.solid
    south = snow & shift(ground, 0, -1, False)
    scal = (p.x + (hash01(p.x // 6, p.y // 8, seed) * 6).astype(int)) % 6
    deep = (scal >= 1) & (scal <= 4)
    deeper = (scal >= 2) & (scal <= 3)
    # the snow's thickness hangs into the ground below in scallops
    f1 = shift(south, 0, 1, False) & ground
    f2 = shift(f1, 0, 1, False) & ground & shift(deep, 0, 0, False)
    lipm = south
    p.put(lipm, 'snow', 5)
    p.put(f1, 'snow', 2)
    p.put(f2 & deeper, 'snow', 1)
    p.f[f2 & deeper] = IDX['snow_cool']
    sh1 = (shift(f1, 0, 1, False) & ~(f2 & deeper)) | shift(f2 & deeper, 0, 1, False)
    sh1 &= ground & ~f1 & ~(f2 & deeper)
    sh2 = shift(sh1, 0, 1, False) & ground & ~sh1 & ~f1 & ~(f2 & deeper)
    p.step(sh1, -2, lo=0)
    p.step(sh2 & (hash01(p.x, p.y, seed + 1) < 0.6), -1, lo=0)
    west = snow & shift(ground, 1, 0, False) & ~south
    north = snow & shift(ground, 0, 1, False) & ~south
    east = snow & shift(ground, -1, 0, False) & ~south
    p.t[west | north] = np.maximum(p.t[west | north], 4)
    p.t[east] = 2
    p.f[east] = IDX['snow_cool']
    beside = shift(east, 1, 0, False) & ground
    p.step(beside, -1, lo=0)
    return f1 | (f2 & deeper)


def tracks(p: Plot, pts, seed=0, kind='boots', on=None, every=5):
    """Tracks pressed into snow along a line: boot prints in pairs every 5 px, each a 2 x 2
    hollow shaded along its top with a lit lower lip; or a sledge's two runners 6 px apart,
    each a shaded line with a lit lower edge."""
    ch_pts = spline(pts, 1.0)
    on = np.ones(p.f.shape, bool) if on is None else np.asarray(on, bool)
    snowy = (FAMILY[p.f] == IDX['snow']) & on & ~p.solid
    if kind == 'boots':
        for i in range(0, len(ch_pts) - 1, every):
            x, y = ch_pts[i]
            nx, ny = ch_pts[min(i + 1, len(ch_pts) - 1)] - ch_pts[i]
            ln = max(1e-6, math.hypot(nx, ny))
            ox, oy = -ny / ln, nx / ln
            side = 1 if (i // every) % 2 else -1
            px, py = int(round(x + ox * 2 * side)), int(round(y + oy * 2 * side))
            for dx, dy, t in ((0, 0, 1), (1, 0, 2), (0, 1, 3), (1, 1, 3)):
                qx, qy = px + dx, py + dy
                if 0 <= qx < p.w and 0 <= qy < p.h and snowy[qy, qx]:
                    p.t[qy, qx] = t
                    p.f[qy, qx] = IDX['snow_cool']
            for dx in (0, 1):
                qx, qy = px + dx, py + 2
                if 0 <= qx < p.w and 0 <= qy < p.h and snowy[qy, qx]:
                    p.t[qy, qx] = 4
    else:
        for i in range(len(ch_pts) - 1):
            x, y = ch_pts[i]
            nx, ny = ch_pts[i + 1] - ch_pts[i]
            ln = max(1e-6, math.hypot(nx, ny))
            ox, oy = -ny / ln, nx / ln
            for side in (-3, 3):
                qx, qy = int(round(x + ox * side)), int(round(y + oy * side))
                if 0 <= qx < p.w and 0 <= qy + 1 < p.h and snowy[qy, qx]:
                    p.t[qy, qx] = 2
                    if snowy[qy + 1, qx]:
                        p.t[qy + 1, qx] = 4


def drift(p: Plot, x, y, w, seed=0, length=None):
    """A drift in the lee of a rock, a wall or a hut (the wind is from the west): a tongue of
    snow trailing east from (x, y), lit along its top, a shade line along its foot."""
    L = length or int(w * (1.6 + hash01(x, y, seed)))
    m = np.zeros(p.f.shape, bool)
    for j in range(L):
        hh = max(1, int(round((w / 2.2) * (1 - j / L) ** 0.7)))
        xx = x + j
        if not 0 <= xx < p.w:
            continue
        for k in range(-hh, 1):
            yy = y + k
            if 0 <= yy < p.h:
                m[yy, xx] = True
    m &= ~p.solid
    p.put(m, 'snow', 3)
    top = m & ~shift(m, 0, 1, False)
    p.t[top] = 4
    p.t[top & (p.x < x + L // 3)] = 5
    foot = m & ~shift(m, 0, -1, False)
    p.put(foot, 'snow_cool', 2)
    below = shift(foot, 0, 1, False) & ~m & ~p.solid
    p.step(below, -1, lo=0)
    return m


# --- ground below the snow ---------------------------------------------------------------------
def tuft(p: Plot, x, y, seed=0, ramp='grass_warm', h=None):
    """A grass tuft (size guide 4 to 8): three to five blades fanning from a dark base, lit
    on the west, their tips a tone up."""
    h = h or 3 + int(hash01(x, y, seed) * 3)
    for i, dx in enumerate((-2, -1, 0, 1, 2)):
        if hash01(x + dx, y, seed + 1) < 0.25 and dx not in (0, -1):
            continue
        L = h - abs(dx) + (1 if dx == -1 else 0)
        for j in range(max(1, L)):
            px, py = x + dx + (dx * j) // 3, y - j
            if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px] and not p.wet[py, px]:
                p.f[py, px] = IDX[ramp]
                p.t[py, px] = 2 if j == 0 else (4 if dx < 0 or j == L - 1 else 3)


def flower_clump(p: Plot, x, y, ramp, seed=0, n=3):
    """A few flowers together (each a 2 px head over a leaf), never one alone."""
    for i in range(n):
        fx = x + int((hash01(x, i, seed) - 0.5) * 7)
        fy = y + int((hash01(i, y, seed + 1) - 0.5) * 4)
        for (dx, dy, fam, t) in ((0, 0, ramp, 4), (1, 0, ramp, 3), (0, 1, 'grass_cool', 2)):
            px, py = fx + dx, fy + dy
            if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px] and not p.wet[py, px]:
                p.f[py, px], p.t[py, px] = IDX[fam], t


def alpine_turf(p: Plot, m, seed=0, flowers=0.5, stones=1.0, wet=None):
    """Short alpine turf, calm as walked ground must be (house rule 8): grass in its cool,
    body and warm siblings in broad soft patches at body tone, sibling clusters, tufts here
    and there, flowers in small clumps (moss campion, gentian, edelweiss), stones lying in
    the turf with a lit top and a short shadow, thin bare earth in a few places."""
    m = np.asarray(m, bool)
    if not m.any():
        return
    base(p, m, [('grass_cool', 0.45), ('grass', 0.3), ('grass_warm', 0.25)], seed, 12.0, light=0.74, dark=0.24)
    texture(p, m, seed + 1, swaps=0.07, ups=0.015, downs=0.02)
    bare = m & (fbm(p.x, p.y, 15, seed + 4) > 0.76) & erode(m, 2)
    base(p, bare, [('earth', 0.5), ('earth_warm', 0.3), ('path_cool', 0.2)], seed + 5, 6)
    if wet is not None:
        wm = m & np.asarray(wet, bool)
        p.step(wm & (FAMILY[p.f] == IDX['grass']), -1)
    stamp(p, m & ~bare, 0.012, seed + 6, SMALL, ramp='leaf', tone=3, same_family=False)
    for i, (x, y) in enumerate(_scatter(m & ~bare, 150, seed + 2)):
        tuft(p, x, y, seed + i, ('grass_warm', 'grass', 'grass_cool')[i % 3])
    if flowers:
        for i, (x, y) in enumerate(_scatter(m & ~bare, int(900 / flowers), seed + 3)):
            flower_clump(p, x, y, ('berry', 'sky', 'plaster', 'brass')[i % 4], seed + i, 2 + i % 3)
    if stones:
        for i, (x, y) in enumerate(_scatter(m, int(500 / stones), seed + 8)):
            w = 2 + int(hash01(x, y, seed + 9) * 3)
            pebble(p, x, y, ROCK[i % 3], w, 2 + (w > 3), k=1)
    despeckle(p, m)


def meadow(p: Plot, m, seed=0):
    """The hay meadow below the treeline: grass at body tone in broad patches, tufts, more
    flowers in clumps, a few stones."""
    m = np.asarray(m, bool)
    base(p, m, [('grass', 0.4), ('grass_warm', 0.35), ('grass_cool', 0.25)], seed, 12.0, light=0.74, dark=0.24)
    texture(p, m, seed + 1, swaps=0.08, ups=0.02, downs=0.02)
    stamp(p, m, 0.014, seed + 6, SMALL, ramp='leaf', tone=3, same_family=False)
    stamp(p, m, 0.006, seed + 7, DOMINOES, ramp='grass_cool', tone=2, same_family=False)
    for i, (x, y) in enumerate(_scatter(m, 110, seed + 2)):
        tuft(p, x, y, seed + i, ('grass_warm', 'grass', 'grass_warm')[i % 3], 4 + i % 3)
    for i, (x, y) in enumerate(_scatter(m, 500, seed + 3)):
        flower_clump(p, x, y, ('plaster', 'brass', 'dusk', 'berry')[i % 4], seed + i, 3 + i % 2)
    for i, (x, y) in enumerate(_scatter(m, 900, seed + 5)):
        pebble(p, x, y, ROCK[i % 3], 3, 2, k=1)
    despeckle(p, m)


def gravel(p: Plot, m, seed=0, ramp='stone'):
    """Loose rock ground (scree, a moraine, a shore): calm grit at body tone in broad sibling
    patches, a few clusters a tone up or down, so the stones lying on it read (they are
    drawn with `stone`), never static."""
    m = np.asarray(m, bool)
    if not m.any():
        return
    base(p, m, [(f'{ramp}_cool', 0.4), (ramp, 0.35), (f'{ramp}_warm', 0.25)], seed, 8.0, light=0.74, dark=0.3)
    stamp(p, m, 0.07, seed + 1, SMALL, swap='mix')
    stamp(p, m, 0.02, seed + 2, DOMINOES, dt=-1)
    stamp(p, m, 0.012, seed + 3, DOMINOES, dt=1)
    despeckle(p, m)


def stone(p: Plot, x, y, w, h, seed=0, snow_cap=False, ramp=None, k=2):
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


def talus(p: Plot, R: Relief, m=None, seed=0, reach=8, snowy=None):
    """Talus at the foot of every face in m: a skirt of fallen rock wandering 3 to `reach`
    px out, grit and stones in the face's own families, the odd larger block against the
    foot. On snowy ground the stones lie in the snow with caps."""
    foot = shift(R.face & (R.depth == R.fh - 1), 0, 1, False) & ~R.face & ~p.solid
    if m is not None:
        foot &= np.asarray(m, bool)
    zone = np.zeros(p.f.shape, bool)
    dd = np.zeros(p.f.shape)
    for d in range(reach, 0, -1):
        s = shift(foot, 0, d - 1, False)
        zone |= s
        dd = np.where(s, d, dd)
    wob = 2 + fbm(p.x, p.y, 7, seed) * reach
    zone &= (dd <= wob) & ~R.face & ~p.solid
    sn = np.zeros(p.f.shape, bool) if snowy is None else np.asarray(snowy, bool)
    grit = zone & ~sn & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.7)
    gravel(p, grit, seed + 2)
    p.step(zone & shift(foot, 0, 0, False), -1)
    for i, (x, y) in enumerate(_scatter(zone, 26, seed + 3, margin=0)):
        w = 2 + int(hash01(x, y, seed + 4) ** 2 * 5)
        stone(p, x - w // 2, y - 1, w, max(2, w * 2 // 3), seed + i, snow_cap=bool(sn[y, x]) and w >= 4)
    return zone


def scree_fan(p: Plot, apex, length, spread=0.9, seed=0, m=None, snowy=None, walk=False):
    """A scree fan below a gully: a cone of broken rock spreading downhill from its apex,
    grit near the top and stones growing with distance (the big ones run furthest), its
    outline in lobes, thinning at the edges into stones lying on the snow or turf beyond
    (no line). Returns the fan's mask."""
    ax, ay = apex
    dx, dy = p.x + 0.5 - ax, p.y + 0.5 - ay
    r = np.hypot(dx, dy * 1.35)
    ang = np.arctan2(dx, np.maximum(dy, 0.01))
    wid = spread * (0.3 + 0.7 * np.clip(r / length, 0, 1) ** 0.6)
    wid = wid + 0.35 * (fbm(p.x, p.y, 11, seed + 1) - 0.5)
    lim = length * (0.75 + 0.4 * fbm(p.x, p.y, 15, seed)) * (1 - 0.3 * np.clip(np.abs(ang) / np.maximum(wid, 0.1), 0, 1) ** 2)
    fan = (dy > -2) & (r < lim) & (np.abs(ang) < wid)
    if m is not None:
        fan &= np.asarray(m, bool)
    fan &= ~p.solid
    core = fan & (r < lim * 0.82) & (np.abs(ang) < wid * 0.8)
    gravel(p, core, seed + 2)
    t = np.clip(r / length, 0, 1)
    sn = np.zeros(p.f.shape, bool) if snowy is None else np.asarray(snowy, bool)
    for i, (x, y) in enumerate(_scatter(fan, 30, seed + 3, margin=0)):
        tt = t[y, x]
        if not core[y, x] and hash01(x, y, seed + 4) < 0.45:
            continue
        w = 2 + int((hash01(x, y, seed + 5) ** 1.5) * (2 + tt * 7))
        stone(p, x - w // 2, y - 1, w, max(2, int(w * 0.65)), seed + i, snow_cap=bool(sn[y, x]) and w >= 4)
    # outliers: stones run out past the fan's toe
    out = (r >= lim) & (r < lim * 1.3) & (np.abs(ang) < wid * 1.1) & (dy > 0) & ~p.solid
    if m is not None:
        out &= np.asarray(m, bool)
    for i, (x, y) in enumerate(_scatter(out, 140, seed + 6, margin=0)):
        w = 3 + int(hash01(x, y, seed + 7) * 5)
        stone(p, x - w // 2, y - 1, w, max(2, int(w * 0.65)), seed + 50 + i, snow_cap=bool(sn[y, x]))
    if not walk:
        p.walk &= ~core
    return fan


# --- water: the tarn, the meltwater, falls ---------------------------------------------------------
def rrect(p: Plot, x0, y0, x1, y1, r=8, seed=0, wob=2.0):
    """A rounded rectangle on the grid (ground shapes are never ellipses), its edge wandering
    a pixel or two inside its edge cells."""
    m = (p.x >= x0) & (p.x < x1) & (p.y >= y0) & (p.y < y1)
    m = rounded(m, r // 2) if r else m
    cx0, cy0, cx1, cy1 = x0 + r, y0 + r, x1 - r, y1 - r
    dx = np.maximum(np.maximum(cx0 - p.x - 0.5, p.x + 0.5 - cx1), 0)
    dy = np.maximum(np.maximum(cy0 - p.y - 0.5, p.y + 0.5 - cy1), 0)
    m &= (dx * dx + dy * dy) <= r * r
    return wobble(m, seed, wob, 8) if wob else m


def tarn(p: Plot, m, seed=0, ice=None):
    """A cirque tarn: dark blue in the deep middle, a tone lighter in bands towards the
    shore, shallows over pale stones near it; a dark band under the north bank and a lit lip
    on the south shore (verticality 4f); a few lit streaks lying with the wind over their own
    shade, glints in pairs; where `ice` (a width in px, or a mask) is given, a sheet of ice
    along the shaded north shore, cracked, with floes broken off it; a shore of wet stones.
    The water stops a walker."""
    m = np.asarray(m, bool)
    if not m.any():
        return
    d = edge_dist(m, 24)
    wobd = d + (fbm(p.x, p.y, 15, seed) - 0.5) * 3
    fam = np.where(fbm(p.x, p.y, 30, seed + 1) < 0.5, IDX['water'], IDX['water_cool'])
    tone = np.where(wobd > 12, 1, np.where(wobd > 6, 2, 3))
    p.f[m] = fam[m]
    p.t[m] = tone[m].astype(np.int8)
    # the sky in the open water, in broad soft patches
    skyp = m & (wobd > 8) & (fbm(p.x * 0.5, p.y, 18, seed + 15) > 0.62)
    p.put(skyp, 'sky', 2)
    p.put(skyp & (fbm(p.x * 0.5, p.y, 9, seed + 16) > 0.6), 'sky', 3)
    p.put(m & (d <= 6) & (d > 3) & (fbm(p.x, p.y, 7, seed + 17) > 0.66), 'water_cool', 3)
    # shallows: pale stones seen through the water near the shore
    sh = m & (d <= 4)
    e1, e2, lid, _a, _b = vcells(p.x.astype(np.float64), p.y.astype(np.float64), 5, 4, seed + 2)
    pal = sh & (e2 - e1 > 1.0) & (hash01(lid, 0, seed + 3) < 0.45)
    p.t[pal] = 4
    # rows from the north shore, for the bank's shade and the ice
    from_n = np.full(p.f.shape, 99, np.int16)
    cur = m & ~shift(m, 0, 1, False)
    for i in range(0, 24):
        from_n = np.where(cur & (from_n == 99), i, from_n)
        cur = shift(cur, 0, 1, False) & m
    # the north bank and the sky in it: a broken reflection, two tones down, under the shore
    refl = m & (from_n >= 1) & (from_n <= 9) & (d > 2)
    ly, lx = np.mgrid[0:p.h, 0:p.w]
    src_y = np.clip(ly - 2 * from_n - 1, 0, p.h - 1)
    sf, st = p.f[src_y, lx], p.t[src_y, lx]
    ok = refl & ~m[src_y, lx] & (st < EDGE_T) & ~GLOW[sf] & (ly - 2 * from_n - 1 >= 0)
    brk = ((p.y + (hash01(p.x // 5, p.y, seed + 12) * 2).astype(int)) % 3 == 0)
    ok &= ~brk
    p.f[ok] = COOL[sf[ok]]
    p.t[ok] = np.clip(st[ok] - 2, 1, 3)
    p.step(m & (from_n <= 1), -1, lo=0)
    # cat's paws: a patch where the wind ruffles the water, short lit arcs over shade
    paw = m & (d > 6) & (fbm(p.x, p.y, 22, seed + 13) > 0.62)
    arc = paw & (((p.x + 2 * ((p.y // 2) % 3)) % 5) < 2) & (p.y % 2 == 0)
    p.t[arc] = np.minimum(p.t[arc] + 1, 4)
    p.t[shift(arc, 0, 1, False) & paw & ~arc] = np.maximum(p.t[shift(arc, 0, 1, False) & paw & ~arc] - 1, 0)
    stamp(p, m & ~refl, 0.05, seed + 14, FLAT, swap='mix')
    south = m & ~shift(m, 0, -1, False)
    p.t[south] = 4
    p.t[m & shift(south, 0, 1, False) & ~south] = np.maximum(p.t[m & shift(south, 0, 1, False) & ~south], 3)
    # streaks lying with the wind, each over its own shade, and glints in pairs
    for i, (x, y) in enumerate(_scatter(m & (d > 4), 300, seed + 4)):
        L = 3 + int(hash01(x, y, seed + 5) * 4)
        for j in range(L):
            if x + j < p.w and y + 1 < p.h and m[y, x + j] and m[y + 1, x + j]:
                p.t[y, x + j] = 4 if j < L - 1 else 3
                p.t[y + 1, x + j] = max(0, p.t[y + 1, x + j] - 1)
    gl = m & (d > 3) & (hash01(p.x // 2, p.y, seed + 6) < 0.004) & (p.x % 2 == 0)
    gl |= shift(gl, 1, 0, False) & m
    p.t[gl] = 5
    if ice is not None:
        if np.ndim(ice) == 0:
            wdt = float(ice) * (0.55 + 0.9 * fbm(p.x, 0 * p.y, 26, seed + 7))
            im = m & (from_n < wdt)
        else:
            im = m & np.asarray(ice, bool)
        f1, f2, cid, _a, _b = vcells(p.x.astype(np.float64), p.y.astype(np.float64), 13, 6, seed + 8)
        crack = (f2 - f1 < 0.8)
        p.put(im, 'snow_cool', 3)
        p.t[im & crack] = 2
        p.t[im & shift(crack, 0, 1, False) & ~crack] = 4
        edge = im & ~shift(im, 0, -1, False)
        p.t[edge] = 2
        p.put(shift(edge, 0, 1, False) & m & ~im, 'water_cool', 1)
        # floes broken off the sheet
        near = m & ~im & dilate(im, 9) & (d > 2)
        floe = near & (f2 - f1 > 1.0) & (hash01(cid, 1, seed + 9) < 0.35)
        floe = _open2_px(floe)
        p.put(floe, 'snow_cool', 3)
        p.t[floe & ~shift(floe, 0, 1, False)] = 4
        fe = floe & ~shift(floe, 0, -1, False)
        p.t[fe] = 2
        p.put(shift(fe, 0, 1, False) & m & ~floe & ~im, 'water_cool', 1)
    # the shore: wet stones round the water
    ring = dilate(m, 2) & ~m & ~p.solid
    gravel(p, ring & (hash01(p.x // 2, p.y // 2, seed + 10) < 0.8), seed + 11)
    p.step(ring & dilate(m, 1), -1)
    p.wet |= m
    p.hazard |= m
    p.walk &= ~m


def _open2_px(m):
    """No part of a mask narrower than two pixels."""
    e = m & shift(m, -1, 0, False) & shift(m, 0, -1, False) & shift(m, -1, -1, False)
    return e | shift(e, 1, 0, False) | shift(e, 0, 1, False) | shift(e, 1, 1, False)


def channel(p: Plot, pts, width=16, seed=0):
    """Meltwater in a grid-led channel (pts: orthogonal runs on the 8 px grid): water with
    the current in lit streaks over their own shade, dark along the bank it runs under, a
    rocky bank of stones either side. Returns the water mask."""
    ch = Channel(p, pts, reach=width + 8)
    hw = width / 2
    wob = (fbm(ch.s, np.sign(ch.n), 11, seed) - 0.5) * 2
    wat = ch.near & (np.abs(ch.n) <= hw + wob) & ~p.solid
    bank = ch.near & (np.abs(ch.n) <= hw + wob + 3) & ~wat & ~p.solid
    gravel(p, bank, seed + 1)
    for i, (x, y) in enumerate(_scatter(bank, 22, seed + 2, margin=0)):
        w = 2 + int(hash01(x, y, seed + 3) * 3)
        stone(p, x - 1, y - 1, w, 2, seed + i, k=1)
    fam = np.where(hash01(p.x // 4, p.y // 6, seed + 4) < 0.5, IDX['water'], IDX['water_cool'])
    p.f[wat] = fam[wat]
    p.t[wat] = 2
    p.t[wat & (np.abs(ch.n) < hw * 0.5)] = 3
    # the current: streaks along the flow
    along = (ch.s + (hash01((ch.n + 20).astype(int), 0, seed + 5) * 9)).astype(int)
    streak = wat & (np.abs(ch.n) < hw - 1.5) & ((along % 11) < 4) & (hash01((ch.n + 20).astype(int) // 2, along // 11, seed + 6) < 0.5)
    p.t[streak] = 4
    p.t[shift(streak, 0, 1, False) & wat & ~streak] = 1
    edge = wat & ~erode(wat, 1)
    p.t[edge & (ch.n < 0)] = 1
    p.t[edge & (ch.n > 0)] = np.maximum(p.t[edge & (ch.n > 0)], 3)
    p.wet |= wat
    p.hazard |= wat
    p.walk &= ~wat
    return wat


def fall(p: Plot, R: Relief, x0, x1, seed=0, pool=True, k=None):
    """A waterfall straight down the face between x0 and x1 (as wide as its channel): white
    where it tips over the lip, falling streaks in water and snow-white, spray on the face
    beside it, a plunge pool 8 px wider each side and 8 deeper than the channel at its foot
    with foam where it lands."""
    col = (p.x >= x0) & (p.x < x1) & R.face
    if k is not None:
        col &= R.kf == k
    if not col.any():
        return
    ys = np.nonzero(col)[0]
    yb = int(ys.max()) + 1
    yt = int(ys.min())
    k = (p.x - x0 + (hash01(p.x, 0, seed) * 3).astype(int)) % 4
    ph = ((p.y + (hash01(p.x, 1, seed + 1) * 12).astype(int)) // 3) % 4
    p.put(col, 'water', 3)
    p.t[col & (k == 0)] = 4
    p.put(col & (k == 1) & (ph != 0), 'snow', 5)
    p.put(col & (k == 3) & (ph == 2), 'snow_cool', 4)
    p.t[col & ((p.x == x0) | (p.x == x1 - 1))] = 2
    lip = col & (p.y <= yt + 1)
    p.put(lip, 'snow', 5)
    spray = R.face & ~col & (np.abs(p.x - (x0 + x1) / 2) < (x1 - x0) / 2 + 4) & (p.y > yt + 4) & (p.y < yb)
    stamp(p, spray, 0.25, seed + 2, SMALL, ramp='snow_cool', tone=4, same_family=False)
    p.wet |= col
    p.hazard |= col
    if pool:
        pm = rrect(p, x0 - 8, yb - 2, x1 + 8, yb + (x1 - x0) // 2 + 14, 6, seed + 3, 1.0) & ~R.face
        tarn(p, pm, seed + 4)
        foam = pm & (np.abs(p.x - (x0 + x1) / 2) < (x1 - x0) / 2 + 2) & (p.y < yb + 6)
        stamp(p, foam, 0.5, seed + 5, SMALL, ramp='snow', tone=5, same_family=False)
        stamp(p, foam, 0.3, seed + 6, SMALL, ramp='snow_cool', tone=4, same_family=False)
        return pm
    return None


# --- ice: glacier, icefall --------------------------------------------------------------------------
def glacier(p: Plot, m, seed=0, bare=None, flow=(0.25, 1.0), crevasses=None):
    """A glacier's surface: névé (old snow, cooler and calmer than the fields) with crevasses
    lying across the flow, bowed downhill, each a dark slit whose far wall catches the light;
    where it is bare (`bare`), blue-grey ice in ogive bands bowed downstream, a medial moraine
    of rubble along the flow, dirt and stones near its snout. It stops a walker."""
    m = np.asarray(m, bool)
    fx, fy = flow
    ln = math.hypot(fx, fy)
    fx, fy = fx / ln, fy / ln
    along = p.x * fx + p.y * fy
    across = p.x * fy - p.y * fx
    snowfield(p, m, seed, swells=0.08, hollows=0.04, ripples=0.2, sastrugi=0.05, sparkle=0.003)
    p.f[m & (p.f == IDX['snow_warm'])] = IDX['snow']
    bm = np.zeros(p.f.shape, bool) if bare is None else (np.asarray(bare, bool) & m)
    if bm.any():
        bow = 0.006 * (across - np.median(across[bm])) ** 2
        ph = (along - bow) / 9.0 + (fbm(p.x, p.y, 12, seed + 1) - 0.5) * 0.6
        og = np.floor(ph).astype(int) % 2
        fr = ph - np.floor(ph)
        p.put(bm, 'snow_cool', 3)
        p.put(bm & (og == 1), 'snow_cool', 2)
        p.put(bm & (og == 1) & (fr > 0.8), 'water', 4)
        p.put(bm & (og == 0) & (fr < 0.2), 'snow', 4)
        stamp(p, bm, 0.05, seed + 2, FLAT, swap='mix')
        mid = bm & (np.abs(across - np.median(across[bm]) - 4) < 3 + (fbm(p.x, p.y, 9, seed + 3) - 0.5) * 3)
        gravel(p, mid, seed + 4)
    # crevasses: arcs across the flow, bowed downhill
    cm = erode(m, 3) if crevasses is None else (erode(m, 3) & np.asarray(crevasses, bool))
    for i, (x, y) in enumerate(_scatter(cm, 420, seed + 5)):
        L = 8 + int(hash01(x, y, seed + 6) * 14)
        for j in range(-L // 2, L // 2):
            cx = x + int(round(j * fy))
            cy = y + int(round(-j * fx + 0.02 * j * j))
            if not (0 <= cx < p.w and 0 <= cy + 2 < p.h) or not m[cy, cx]:
                continue
            p.put(_pt(p, cx, cy), 'snow_cool', 1 if abs(j) < L // 2 - 2 else 2)
            if abs(j) < L // 2 - 3 and m[cy + 1, cx]:
                p.put(_pt(p, cx, cy + 1), 'water', 2)
            if m[cy + 2, cx]:
                p.put(_pt(p, cx, cy + 2), 'snow', 5 if abs(j) < L // 2 - 3 else 4)
    p.hazard |= m
    p.walk &= ~m


def ice_faces(p: Plot, R: Relief, m, seed=0):
    """Where the glacier pours over the tiers (an icefall), every face in m is an ice cliff
    instead of rock: seracs as columns of blue ice 6 to 14 px wide, each lit on its west
    edge and darker to the east, split by deep blue cracks, striated, a thick cap of snow
    along the rim (scalloped where it overhangs) and a dark foot; the tops between are the
    glacier's broken surface (crevasses); the side bands are ice too. A boundary: nothing
    walks here."""
    m = np.asarray(m, bool)
    fc = R.face & m
    tops = m & ~R.face
    glacier(p, tops, seed, crevasses=tops)
    if fc.any():
        el = R.elev.astype(np.float64)
        off = (hash01(R.kf, 0, seed) * 13).astype(int)
        colw = 6 + (hash01((p.x + off) // 9, R.kf, seed + 1) * 9).astype(int)
        cidx = (p.x + off) // colw
        cpos = (p.x + off) - cidx * colw
        lean = ((el // 6) % 2).astype(int)
        crack = (cpos == 0) | ((cpos == 1) & (lean == 1) & (hash01(cidx, R.kf, seed + 2) < 0.5))
        pick = hash01(cidx, R.kf, seed + 3)
        p.put(fc, 'sky', 3)
        p.put(fc & (cpos <= 2), 'sky', 4)
        p.put(fc & (cpos <= 1) & (pick < 0.5), 'snow_cool', 4)
        p.put(fc & (cpos >= colw - 3), 'water', 2)
        p.put(fc & (pick > 0.7) & (cpos > 2) & (cpos < colw - 3), 'water', 3)
        stri = fc & ((p.x + p.y // 7) % 4 == 0) & (cpos > 2) & (cpos < colw - 3)
        p.step(stri, -1, lo=1)
        p.put(fc & crack, 'water_cool', 0)
        p.put(fc & shift(crack, -1, 0, False) & ~crack, 'water_cool', 1)
        lip = fc & (R.depth <= 2)
        sc = (p.x + off) % 6
        p.put(lip & (R.depth == 0), 'snow', 5)
        p.put(lip & (R.depth == 1), 'snow', 4)
        p.put(lip & (R.depth == 2) & (sc >= 1) & (sc <= 4), 'snow', 2)
        p.put(fc & (R.depth >= R.fh - 2), 'water_cool', 1)
    band = m & p.solid & ~R.face & ~tops
    p.hazard |= m
    p.walk &= ~m
    p.solid |= fc
    return band


def snout(p: Plot, tongue, h=12, seed=0):
    """A glacier's snout: the tongue's front as an ice cliff hanging under its south edge,
    `h` px tall in the middle and thinning to nothing at its sides, blue ice in vertical
    striations, lit on the west and shaded on the east, a lip of old snow along its top,
    dirty with grit along its foot, a dark portal in its middle where the meltwater comes
    out. Returns the portal's foot (x, y)."""
    tongue = np.asarray(tongue, bool)
    cols = np.nonzero(tongue.any(0))[0]
    if not len(cols):
        return (0, 0)
    x0, x1 = int(cols.min()), int(cols.max()) + 1
    xc, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    m = np.zeros(p.f.shape, bool)
    depth = np.zeros(p.f.shape, np.int16)
    for x in range(x0, x1):
        ys = np.nonzero(tongue[:, x])[0]
        ys_ = int(ys.max())
        hh = int(round(h * math.sqrt(max(0.0, 1 - ((x + 0.5 - xc) / half) ** 2)) + (hash01(x // 3, 0, seed) - 0.5) * 2))
        for d in range(1, hh + 1):
            if ys_ + d < p.h:
                m[ys_ + d, x] = True
                depth[ys_ + d, x] = d
    k = (p.x + (hash01(p.x // 3, 0, seed) * 4).astype(int)) % 5
    west = p.x < xc - half * 0.2
    p.put(m, 'sky', 3)
    p.put(m & west, 'sky', 4)
    p.put(m & (p.x > xc + half * 0.35), 'water', 2)
    p.put(m & (k == 0) & west, 'snow_cool', 4)
    p.step(m & (k == 2), -1, lo=1)
    p.put(m & (depth == 1), 'snow', 5)
    p.put(m & (depth == 2) & ((p.x % 6) > 1), 'snow_cool', 3)
    foot = m & ~shift(m, 0, -1, False)
    p.put(foot, 'stone_cool', 2)
    p.put(shift(foot, 0, 1, False) & ~m & ~p.solid, 'stone_cool', 1)
    px = int(xc) - 4
    ys_mid = int(np.nonzero(m[:, int(xc)])[0].max()) + 1 if m[:, int(xc)].any() else 0
    portal = m & (np.abs(p.x - xc) <= 5) & (p.y > ys_mid - 8)
    portal &= ((p.x - xc) ** 2 / 25 + (p.y - ys_mid) ** 2 / 64) <= 1
    p.put(portal, 'water_cool', 0)
    p.put(portal & ~shift(portal, 0, 1, False), 'slate', 1)
    p.hazard |= m
    p.walk &= ~m
    p.solid |= m
    return (px + 4, ys_mid)


# --- standing things ------------------------------------------------------------------------------
def boulder(seed=0, w=None, h=None, snow=False, blaze=False):
    """A granite boulder (size guide 16 to 32 tall, 20 to 48 wide): a rounded mass broken into
    facets, lit from the upper left in hard steps, a crack with a lit lower lip, lichen on the
    lit side, a dark contact at its foot; with a cap of snow on its top (`snow`) and the
    trail's red and white paint mark on its south face (`blaze`)."""
    w = w or 16 + int(hash01(seed, 0, 19) * 12)
    h = h or int(w * (0.62 + 0.15 * hash01(seed, 1, 19)))
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
    famr = np.where(pick < 0.33, IDX['stone_warm'], np.where(pick < 0.66, IDX['stone'], IDX['stone_cool']))
    sp.put(shape, famr, tone)
    sp.put(shape & (tone == 4) & (lam > 0.62), famr, 5)
    lich = shape & (tone >= 3) & (hash01(sp.x // 2, sp.y // 2, seed + 4) < 0.12)
    sp.put(lich, 'grass_cool', 4)
    for c in range(1 + int(hash01(seed, 2, 19) * 2)):
        x0 = int(cx - w * 0.2 + c * w * 0.3)
        for j in range(int(h * 0.5)):
            x = x0 + (j // 2) * (1 if c % 2 else -1)
            y = int(cy - h * 0.25) + j
            if 0 <= x < sp.w and 0 <= y < sp.h and shape[y, x]:
                sp.t[y, x] = 1
                if 0 <= y + 1 < sp.h and x - 1 >= 0 and shape[y + 1, x - 1]:
                    sp.t[y + 1, x - 1] = min(5, sp.t[y + 1, x - 1] + 1)
    if blaze:
        bx, by = int(cx - 4), int(cy - h * 0.05)
        for i in range(6):
            for j in range(3):
                if 0 <= by + j < sp.h and shape[by + j, bx + i]:
                    sp.f[by + j, bx + i] = IDX['plaster'] if j == 1 else IDX['berry']
                    sp.t[by + j, bx + i] = 4 if j == 1 else (3 if i < 4 else 2)
    if snow:
        top = shape & ~shift(shape, 0, 1, False)
        cap = np.zeros(shape.shape, bool)
        for d in range(0, max(2, h // 5)):
            cap |= shift(top, 0, d, False)
        cap &= shape & (v < 0.1) & (u < 0.75)
        sp.put(cap, 'snow', np.where(u < 0.1, 5, 4))
        under = shift(cap, 0, 1, False) & shape & ~cap & ((sp.x % 6) > 1)
        sp.put(under, 'snow', 2)
    sp.put(shape & (sp.y >= sp.fy - 1), famr, 1)
    return sp, sp.blob_shadow(w * 0.55, max(3, h * 0.3))


def fir(seed=0, h=None, snow=0.5):
    """A mountain fir or spruce (pines thin out with height, size guide 64 to 125): a
    narrow spire of drooping branch layers, each a band of needle clumps lit on the west,
    dark beneath, with snow lying on the tops of the layers (`snow`), a short trunk and a
    dark skirt at its foot."""
    h = h or 52 + int(hash01(seed, 0, 41) * 30)
    wmax = int(h * 0.42)
    sp = Sprite(wmax + 6, h + 4, (wmax + 6) // 2, h + 1)
    cx = sp.fx
    trunk = (np.abs(sp.x - cx + 0.5) <= 1.5) & (sp.y > sp.fy - 8) & (sp.y <= sp.fy)
    sp.put(trunk, 'timber', 2)
    sp.put(trunk & (sp.x < cx), 'timber', 3)
    nl = max(4, h // 9)
    top_y = sp.fy - h
    shape = np.zeros(sp.m.shape, bool)
    for i in range(nl):
        t0 = i / nl
        yb = int(top_y + 6 + (h - 10) * (i + 1) / nl)
        hw = 2 + (wmax / 2 - 2) * ((i + 1) / nl) ** 0.85 * (0.9 + 0.2 * hash01(i, seed, 42))
        yt = int(yb - (h - 10) / nl * 1.6)
        layer = (sp.y >= yt) & (sp.y <= yb)
        rel = (sp.y - yt) / max(1, yb - yt)
        half = hw * (0.35 + 0.65 * rel)
        droop = np.abs(sp.x + 0.5 - cx) <= half
        tip = (rel > 0.75) & (np.abs(sp.x + 0.5 - cx) > half - 2) & (hash01(sp.x, i, seed) < 0.5)
        lm = layer & droop & ~tip
        u = (sp.x + 0.5 - cx) / max(1.0, hw)
        tone = np.where(u < -0.3, 4, np.where(u < 0.25, 3, 2))
        tone = np.where(rel > 0.8, tone - 1, tone)
        fam = np.where(hash01(sp.x // 2, sp.y // 2, seed + i) < 0.35, IDX['leaf_cool'], IDX['leaf'])
        sp.put(lm & ~shape, fam, tone)
        shape |= lm
        del t0
        if snow and hash01(i, seed, 43) < snow + 0.2:
            topl = lm & (rel < 0.3) & (u < 0.55) & ~shift(lm, 0, 1, False)
            topl |= shift(topl, 0, -1, False) & lm & (u < 0.1)
            sp.put(topl, 'snow', np.where(u < -0.2, 5, 4))
    tipm = (np.abs(sp.x + 0.5 - cx) < 1.0) & (sp.y >= top_y) & (sp.y < top_y + 7)
    sp.put(tipm, 'leaf', 3)
    stamp_sprite_clumps(sp, shape, seed)
    skirt = shape & (sp.y >= sp.fy - 9) & (sp.y < sp.fy - 6)
    sp.step(skirt, -1, lo=1)
    sh = sp.thrown(0.45)
    return sp, sh


def stamp_sprite_clumps(sp, m, seed):
    """Needle clumps on a sprite: domino clusters a tone up on the lit side, down in shade."""
    for i in range(0, sp.w, 2):
        for j in range(0, sp.h, 2):
            if not m[j, i] or hash01(i, j, seed + 7) > 0.22:
                continue
            t = sp.t[j, i]
            nt = min(5, t + 1) if t >= 3 else max(1, t - 1)
            for dx, dy in ((0, 0), (1, 0)):
                if i + dx < sp.w and m[j + dy, i + dx] and FAMILY[sp.f[j + dy, i + dx]] == IDX['leaf']:
                    sp.t[j + dy, i + dx] = nt


def cairn(seed=0, h=None, snow=True):
    """A trail cairn (size guide 12 to 28): flat stones stacked, each narrower than the one
    under it, each lit on its upper left with a dark joint under it, a cap of snow on top."""
    h = h or 16 + int(hash01(seed, 0, 51) * 8)
    w = 14
    sp = Sprite(w + 4, h + 4, (w + 4) // 2, h + 1)
    y = sp.fy
    i = 0
    while y > sp.fy - h + 2:
        sw = max(4, int(w * (1 - 0.6 * (sp.fy - y) / h) + (hash01(i, seed, 52) - 0.5) * 3))
        sh = 3 + int(hash01(i, seed, 53) * 2)
        x0 = sp.fx - sw // 2 + int((hash01(i, seed, 54) - 0.5) * 3)
        ramp = ROCK[i % 3]
        for yy in range(y - sh, y):
            for xx in range(x0, x0 + sw):
                if (xx in (x0, x0 + sw - 1)) and yy in (y - sh, y - 1):
                    continue
                t = 4 if yy == y - sh else 1 if yy == y - 1 else 3
                if xx == x0 + sw - 1 and t == 3:
                    t = 2
                if xx <= x0 + 1 and t == 3:
                    t = 4
                sp.px(xx, yy, ramp, t)
        y -= sh
        i += 1
    if snow:
        top = sp.m & ~shift(sp.m, 0, 1, False)
        for (yy, xx) in zip(*np.nonzero(top)):
            sp.px(xx, yy, 'snow', 5 if xx < sp.fx else 4)
    return sp, sp.blob_shadow(w * 0.5, 3)


def noticeboard(seed=0):
    """The Col hut's notice board (size guide 28 to 44): two posts, a little roof, a board
    with pinned notices (a map, the weather, a lost hat)."""
    sp = Sprite(24, 34, 12, 33)
    for x in (3, 19):
        sp.put((sp.x >= x) & (sp.x < x + 2) & (sp.y >= 8) & (sp.y <= 33), 'timber', 2)
        sp.put((sp.x == x) & (sp.y >= 8) & (sp.y <= 33), 'timber', 3)
    board = (sp.x >= 2) & (sp.x < 22) & (sp.y >= 9) & (sp.y < 22)
    sp.put(board, 'timber_cool', 3)
    sp.put(board & ((sp.y - 9) % 4 == 3), 'timber_cool', 2)
    sp.put(board & (sp.y == 9), 'timber_cool', 4)
    sp.put(board & (sp.x == 21), 'timber_cool', 1)
    for (x, y, w, h, fam) in ((4, 11, 6, 7, 'plaster'), (11, 12, 5, 5, 'plaster'), (17, 11, 4, 8, 'sky')):
        n = (sp.x >= x) & (sp.x < x + w) & (sp.y >= y) & (sp.y < y + h)
        sp.put(n, fam, 4)
        sp.put(n & (sp.x == x + w - 1), fam, 3)
        sp.put(n & ((sp.y - y) % 2 == 1) & (sp.x > x) & (sp.x < x + w - 2), fam, 2)
        sp.px(x + w // 2, y, 'berry', 3)
    roof = (sp.y >= 4) & (sp.y < 9) & (np.abs(sp.x - 11.5) <= 12 - (8 - sp.y) * 0.3)
    sp.put(roof, 'slate', 3)
    sp.put(roof & (sp.y == 8), 'slate', 1)
    sp.put(roof & (sp.y <= 5), 'snow', 4)
    sp.put(roof & (sp.y <= 5) & (sp.x < 10), 'snow', 5)
    return sp, sp.thrown(0.4)


def fire_ring(p: Plot, x, y, seed=0):
    """A cold fire ring: a ring of stones round black ash and charred ends."""
    for i in range(9):
        a = i / 9 * 2 * math.pi
        sx, sy = int(x + math.cos(a) * 7), int(y + math.sin(a) * 4)
        stone(p, sx - 1, sy - 1, 3, 2, seed + i, k=1)
    ash = ((p.x - x) ** 2 / 25 + (p.y - y) ** 2 / 6) <= 1
    ash &= ~p.solid
    p.put(ash, 'basalt', 2)
    p.put(ash & (hash01(p.x, p.y, seed) < 0.3), 'basalt', 1)
    p.put(ash & (p.x == x) & (p.y == y), 'timber', 1)
    p.put(ash & (p.x == x + 1) & (p.y == y), 'timber', 2)


def sledge(seed=0):
    """The ice-cutter's sledge (about 20 x 10): two curled runners, a slatted bed, a block of
    lake ice lashed on it."""
    sp = Sprite(24, 14, 12, 13)
    run = (sp.y == 12) & (sp.x >= 2) & (sp.x < 22)
    sp.put(run, 'iron', 2)
    sp.px(1, 11, 'iron', 3)
    sp.px(1, 10, 'iron', 3)
    for x in (4, 10, 16):
        sp.put((sp.x >= x) & (sp.x < x + 2) & (sp.y >= 10) & (sp.y < 12), 'timber', 2)
    bed = (sp.x >= 2) & (sp.x < 21) & (sp.y >= 8) & (sp.y < 10)
    sp.put(bed, 'timber', 3)
    sp.put(bed & (sp.y == 8), 'timber', 4)
    blk = (sp.x >= 6) & (sp.x < 17) & (sp.y >= 2) & (sp.y < 8)
    sp.put(blk, 'sky', 4)
    sp.put(blk & (sp.y == 2), 'snow', 5)
    sp.put(blk & (sp.x >= 14), 'water', 3)
    sp.put(blk & (sp.x == 6), 'snow', 4)
    sp.put((sp.x == 11) & (sp.y >= 2) & (sp.y < 9), 'berry', 2)
    return sp, sp.thrown(0.3)


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


def col_hut(cw=1, seed=0):
    """The Col hut: the valley kit's stone hut (house_kits.front('valley', 1): drystone walls,
    a slate roof with a boarded gable, a door, a sign with a mug, a window, a bench and an
    A-board), in the heather colourway, with snow lying on its roof (thick on the lit west
    slope, a shaded cap on the east, scalloped over the eaves) and icicles along the eaves.
    Returns the sprite, its shadow and its foot block."""
    import house_kits as hk
    sp = _from_canvas(hk.front('valley', 1, cw))
    top = sp.m & ~shift(sp.m, 0, 1, False)
    roof_rows = hk.ROOF_H['valley']
    snow = np.zeros(sp.m.shape, bool)
    for d in range(0, 4):
        snow |= shift(top, 0, d, False)
    snow &= sp.m & (sp.y < roof_rows - 2)
    left = sp.x < sp.w // 2
    sp.put(snow, 'snow', np.where(left, 4, 3))
    sp.put(top & left, 'snow', 5)
    sp.put(top & ~left, 'snow', 4)
    sc = (sp.x % 6)
    under = shift(snow, 0, 1, False) & sp.m & ~snow & (sp.y < roof_rows) & (sc > 0) & (sc < 5)
    sp.put(under, 'snow', np.where(left, 2, 1))
    # snow lying along the eaves, and icicles hanging under them
    eave_y = roof_rows - 1
    eave = sp.m & (sp.y >= eave_y - 2) & (sp.y <= eave_y - 1) & ((sp.x < 10) | (sp.x > sp.w - 11))
    sp.put(eave, 'snow', 4)
    for x in range(2, sp.w - 2, 5):
        L = 1 + int(hash01(x, seed, 61) * 3)
        for j in range(L):
            yy = eave_y + j
            if 0 <= yy < sp.h and sp.m[yy, x] and FAMILY[sp.f[yy, x]] != IDX['snow']:
                sp.f[yy, x], sp.t[yy, x] = IDX['snow_cool'], 4 if j == 0 else 3
    block = sp.m & (sp.y >= sp.h - 14)
    return sp, sp.thrown(0.35), block


def drystone(p: Plot, x0, x1, y, seed=0, h=10, gate=None):
    """A drystone sheep wall along y from x0 to x1 (size guide 10 to 18 tall): courses of
    rough stones 4 to 8 long, each lit on top and darker under, through-stones every 32 to
    48, a row of coping stones on edge along the top, snow lying on the top in places; with
    a gap and a timber gate (`gate`: x of its west post) where the path goes through. Drawn
    as standing art: it stops a walker except at the gate."""
    gx0, gx1 = (gate, gate + 24) if gate is not None else (None, None)
    yrow = np.full(x1 - x0, y, np.int32) if np.ndim(y) == 0 else np.asarray(y, np.int32)
    wall = np.zeros(p.f.shape, bool)
    for x in range(x0, x1):
        if gx0 is not None and gx0 <= x < gx1:
            continue
        if not 0 <= x < p.w:
            continue
        y = int(yrow[x - x0])
        for j in range(h):
            yy = y - j
            if 0 <= yy < p.h:
                wall[yy, x] = True
            if not 0 <= yy < p.h:
                continue
            course = j // 3
            off = int(hash01(course, 0, seed) * 7)
            sl = 4 + int(hash01((x + off) // 6, course, seed + 1) * 5)
            px_ = (x + off) % sl
            ramp = ROCK[int(hash01((x + off) // sl, course, seed + 2) * 3)]
            t = 3
            if j % 3 == 2:
                t = 4
            if j % 3 == 0:
                t = 2
            if px_ == 0:
                t = 1
            if j == h - 1:
                t = 4 if (x // 2) % 2 else 3
            if j >= h - 2 and hash01(x // 7, 0, seed + 3) < 0.45:
                p.f[yy, x], p.t[yy, x] = IDX['snow'], 5 if j == h - 1 else 4
                continue
            p.f[yy, x], p.t[yy, x] = IDX[ramp], t
        if 0 <= y + 1 < p.h:
            p.step(_pt(p, x, y + 1), -2)
            if x + 1 < p.w:
                p.step(_pt(p, x + 1, y + 2) if y + 2 < p.h else _pt(p, x, y), -1)
    if gx0 is not None:
        y = int(yrow[min(len(yrow) - 1, max(0, gx0 - x0))])
        for gp in (gx0 - 2, gx1):
            post = (p.x >= gp) & (p.x < gp + 3) & (p.y > y - h - 4) & (p.y <= y)
            p.put(post, 'timber', 2)
            p.put(post & (p.x == gp), 'timber', 3)
            p.put(post & (p.y == y - h - 3), 'snow', 5)
            wall |= post
        # the gate stands open, swung back against the wall's west end
        gate_m = (p.x >= gx0 - 12) & (p.x < gx0 - 2) & (p.y > y - h + 1) & (p.y <= y - 1)
        bars = gate_m & (((p.y - y) % 3 == 0) | ((p.x - gx0) % 5 == 0))
        p.put(bars, 'timber', 3)
        p.put(bars & ((p.y - y) % 3 == 0) & (p.x % 2 == 0), 'timber', 4)
    outline_mask(p, wall)
    p.solid |= wall
    p.walk &= ~wall
    return wall


# --- ways up: trails, ramps, stairs --------------------------------------------------------------
def trail(p: Plot, pts, width=16, seed=0, kind='earth', m=None):
    """A mountain trail (size guide 16): on turf, packed earth worn lighter where feet go, its
    edges ragged into the turf, grit kicked to the sides; in snow, a trodden trench, shaded
    along its north wall, its floor packed and printed, its south lip lit. Walkable."""
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
        tm &= ~(tm & (np.abs(ch.n) > hw + wob - 2) & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.5))
        p.put(tm, 'snow_cool', 3)
        packed = tm & (np.abs(ch.n) < hw * 0.5) & (fbm(p.x, p.y, 8, seed + 2) > 0.45)
        p.t[packed] = 2
        nwall = tm & ~shift(tm, 0, 1, False)
        p.t[nwall] = 1
        p.t[shift(nwall, 0, -1, False) & tm] = 2
        slip = tm & ~shift(tm, 0, -1, False)
        p.put(slip, 'snow', 5)
        berm = dilate(tm, 1) & ~tm & ~p.solid & (FAMILY[p.f] == IDX['snow'])
        p.t[berm & shift(tm, 0, 1, False)] = 4
        tracks(p, pts, seed + 7, 'boots', on=tm, every=4)
    p.walk |= tm & ~p.solid & ~p.hazard
    return ch, tm


def ramp_along(p: Plot, R: Relief, xa, xb, depth=24, seed=0, rising='east', kind='earth', k=None):
    """A ramp cut along a south face (soft grid: along the face at 1 in 3, at least 24 wide),
    rising from the foot at one end to the top at the other. Seen from the south: the cut's
    back wall (the face's own rock, carried up) behind the tread, the tread (trodden earth
    with ridges across the slope and a worn track, or trodden snow), and under its outer
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
        p.f[tread], p.t[tread] = IDX['snow_cool'], base_t
    rows_in = np.zeros(p.f.shape, np.int16)
    for x in range(lo_x, hi_x):
        col = np.nonzero(tread[:, x])[0]
        if len(col):
            rows_in[col, x] = col - col.min()
    mid = depth // 2
    track = tread & (np.abs(rows_in - mid) <= 3)
    ridge = tread & ~track & (((p.x - lo_x + (p.y // 5)) % 6) == 0)
    p.t[ridge] = base_t + 1
    p.t[shift(ridge, 1, 0, False) & tread & ~track] = base_t - 1
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
    middle, the west cheek lit and the east cheek dark, snow in the treads' back corners.
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
    p.put(corner, 'snow', 4)
    p.put(cheek_w, 'stone_warm', 4)
    p.t[cheek_w & (p.x == x0 + 3)] = 3
    p.t[cheek_w & (p.x == x0)] = 1
    p.put(cheek_w & (d == 0), 'snow', 5)
    p.put(cheek_e, 'stone_cool', 1)
    p.t[cheek_e & (p.x == x0 + width + 4)] = 2
    p.put(cheek_e & (d == 0), 'snow', 3)
    p.walk[run] = True
    p.solid[run] = False
    head = (p.x >= x0 + 4) & (p.x < x0 + width + 4) & ~R.face
    for dd in range(1, 7):
        p.walk |= head & shift(run & (R.depth == 0), 0, -dd, False) & ~p.hazard
        p.walk |= head & shift(run & (R.depth == R.fh - 1), 0, dd, False) & ~p.hazard & ~p.solid
    return run


# --- working on the part of the plot a piece touches -----------------------------------------------
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


base = local(base)
texture = local(texture)
despeckle = local(despeckle)
snowfield = local(snowfield)
alpine_turf = local(alpine_turf)
meadow = local(meadow)
gravel = local(gravel)
tarn = local(tarn, pad=26)
glacier = local(glacier)


# --- the pilot: the Col Path to the Frostline lip, the cirque, the massif -------------------------
PW, PH = 640, 1152
# tier heights: the valley side 0, 32, 64, 96; the moraine lip a low step of 16; above it
# the frame in tiers of 32 (stacked cliffs with ledges, size guide 7)
E_PILOT = [0, FACE, 2 * FACE, 3 * FACE, 3 * FACE + LOW] + [3 * FACE + LOW + FACE * i for i in range(1, 26)]


# The walked benches: each rim meanders in lobes and bays (16 px either way over 90 to 160
# px) and runs straight where a ramp or the stair is cut into its face; (x0, x1) of each
# straight stretch and the rim's mean row
BENCH = {
    1: (976, [(312, 432)], 11),
    2: (816, [(288, 408)], 12),
    3: (640, [(384, 504)], 13),
    4: (576, [(368, 432)], 14),
}


def organic_rim(y0, straight, seed, amp=16, w=PW):
    """A rim over 8 px columns that meanders (a smooth curve of lobes and bays, amp px either
    way) and is laid on the grid in runs of two cells or more; level at y0 across the
    `straight` stretches (where a ramp or a stair needs a straight face)."""
    xs = np.arange(w // GRID) * GRID + 4.0
    c = (fbm(xs * 0.6, np.full_like(xs, 7.0 * seed), 18, seed) - 0.5) * 2 * amp * 1.6
    r = y0 + c
    for (a, b) in straight:
        sel = (xs >= a - 8) & (xs < b + 8)
        r = np.where(sel, y0, r)
    r = (np.round(r / GRID) * GRID).astype(np.int32)
    return fix_runs(r, 2)




# The frame's masses (plan 5.5: the fade, the wall, the beyond). Each is a stack of tiers:
# (x, y, rx, ry, base tier, tiers, px each tier steps north, how much each tier narrows).
# The crags beside the step stand one tier above the bench beside them; the cirque's walls,
# the headwall and the peaks rise in stacked faces with ledges between.
MASSES = (
    (30, 1066, 70, 60, 1, (0, 0), 0.10), (40, 878, 92, 100, 2, (0, 0, 52), 0.08),
    (52, 672, 100, 100, 3, (0, 0, 56), 0.08),
    (610, 1050, 70, 56, 1, (0, 0), 0.10), (602, 862, 90, 96, 2, (0, 0, 52), 0.08),
    (594, 664, 96, 94, 3, (0, 0, 56), 0.08),
    (62, 440, 140, 176, 5, (0, 0, 40, 0, 36, 0, 34), 0.11), (616, 434, 90, 170, 5, (0, 0, 40, 0, 36, 0), 0.11),
    (340, 236, 330, 176, 5, (0, 40, 40, 40, 40), 0.03),
)


def mass_cells(seed=1, cols=PW // GRID, rows=PH // GRID):
    """The frame's tier map on the 8 px grid: every mass a stack of noisy blobs, each tier's
    blob shifted north by its step and narrowed, kept inside the one under it, its south
    edge flattened (so it carries a face) and its outline wandering in lobes and bays."""
    X, Y = np.meshgrid(np.arange(cols) * GRID + 4.0, np.arange(rows) * GRID + 4.0)
    C = np.zeros((rows, cols), np.int16)
    for i, (cx, cy, rx, ry, b, steps, nar) in enumerate(MASSES):
        prev = None
        up = 0
        for j, st in enumerate(steps):
            k = b + j
            up += st
            ox = (hash01(i, j, seed) - 0.5) * rx * 0.25 if st else 0.0
            ccx, ccy = cx + ox, cy - up
            rrx, rry = rx * (1 - nar * j), ry * (1 - nar * j * 0.8)
            u = (X - ccx) / rrx
            v = (Y - ccy) / rry
            v = np.where(v > 0, v * 1.35, v)
            nz = (fbm(X * 0.9, Y, 40, seed + 31 * i + j) - 0.5) * 0.55 + (fbm(X, Y, 15, seed + 7 * i + j) - 0.5) * 0.22
            blob = np.hypot(u, v) + nz < 1.0
            if prev is not None and st == 0:
                blob = prev.copy()
            elif prev is not None:
                blob &= prev if st == 0 else (prev & shift(prev, 0, -max(1, (FACE + 8) // GRID), False))
            C = np.where(blob, np.maximum(C, k), C)
            prev = blob
    return C


# Couloirs and buttresses carved into the headwall and the cirque's walls: (x at the foot,
# y at the foot, y at the head, drift in x per px climbed, width at the foot, at the head,
# tiers: -1 a couloir cut down, +1 a buttress standing out)
GROOVES = (
    (236, 404, 170, 0.32, 40, 16, -1), (372, 410, 176, -0.22, 36, 16, -1), (486, 420, 120, 0.05, 100, 116, -1),
    (300, 408, 190, 0.10, 32, 18, 1),
)


# The far range behind the névé: (x, tiers above the névé) of its summits, its foot row
SUMMITS = ((88, 5.0, 70), (338, 3.6, 60), (604, 4.4, 64))
RANGE_FOOT = 176


def range_cells(C, seed=1, cols=PW // GRID, rows=PH // GRID):
    """The far range: stacked faces rising from the névé, two tiers high at its cols and five
    or six at its summits, each pair of tiers one face of 64 with a narrow ledge above it,
    the ledges stepping back as the range rises; its top tier ends 16 to 32 px behind its
    rim at the skyline (a back rim), so the summits stand up against the snow beyond."""
    xs = np.arange(cols) * GRID + 4.0
    H = np.full(cols, 3.4)
    for (sx, h, w) in SUMMITS:
        H = np.maximum(H, 3.4 + h * np.exp(-((xs - sx) / w) ** 2))
    H += (fbm(xs, np.zeros(cols), 30, seed + 60) - 0.5) * 1.2
    foot = RANGE_FOOT + 10 * np.sin(xs / 70.0) + (fbm(xs, np.full(cols, 9.0), 25, seed + 61) - 0.5) * 16
    depth = 18 + (fbm(xs, np.full(cols, 3.0), 20, seed + 62)) * 16
    steps = (0, 0, 44, 0, 40, 0, 36, 0, 32)
    ups = np.cumsum(steps)
    C = C.copy()
    yc = np.arange(rows) * GRID + 4.0
    # each tier reaches its own way along the range (lobes, not towers)
    reach = np.array([H + (fbm(xs * 1.3, np.full(cols, 31.0 * j), 26, seed + 63 + j) - 0.5) * 2.2
                      for j in range(len(steps))])
    nns = np.zeros(cols, int)
    for c in range(cols):
        nn = 0
        for j in range(len(steps)):
            if reach[j, c] > j + 0.5 and (j == 0 or nn == j):
                nn = j + 1
        nns[c] = max(1, nn)
    # no spire narrower than three cells: open the profile, then close it
    for _ in range(2):
        lo = np.minimum.reduce([np.roll(nns, -1), nns, np.roll(nns, 1)])
        nns = np.maximum.reduce([np.roll(lo, -1), lo, np.roll(lo, 1)])
    for c in range(cols):
        nn = int(nns[c])
        top_up = ups[nn - 1]
        sky = foot[c] - top_up - depth[c]
        for j in range(nn):
            on = (yc < foot[c] - ups[j]) & (yc >= sky)
            C[on, c] = np.maximum(C[on, c], 10 + j)
        C[yc < sky, c] = 9
    return C


def grooves(C, seed=1, cols=PW // GRID, rows=PH // GRID):
    """Carve couloirs (a groove a tier deep, its floor stepping up the wall, so snow lies
    in it at every ledge and its walls show as side bands) and buttresses (a rib a tier
    proud) into the frame, each drifting sideways as it climbs, so they run diagonally
    down the fall line and widen towards the foot."""
    X, Y = np.meshgrid(np.arange(cols) * GRID + 4.0, np.arange(rows) * GRID + 4.0)
    C = C.copy()
    for (xb, yb, yt, drift, wb, wt, dk) in GROOVES:
        t = np.clip((yb - Y) / max(1.0, yb - yt), 0, 1)
        cx = xb + (yb - Y) * drift
        w = wb + (wt - wb) * t + (fbm(X, Y, 30, seed + int(xb)) - 0.5) * 8
        sel = (np.abs(X - cx) < w / 2) & (Y <= yb) & (Y >= yt) & (C >= 5)
        C = np.where(sel, C + dk, C)
    return C


def frame_light(x, y, seed=1):
    """A smooth height for the frame's masses (tiers), for the light across their faces:
    each mass lit on its west flank and shaded on its east."""
    Z = np.full(np.shape(x), -9.0)
    for (cx, cy, rx, ry, b, steps, nar) in MASSES:
        n, up = len(steps), sum(steps)
        u = (x - cx) / rx
        v = (y - cy + up * 0.5) / (ry + up * 0.5)
        Z = np.maximum(Z, b + n * np.clip(1 - np.hypot(u, v), 0, 1))
    return Z


def _slope_x(f, d=3):
    return (shift(f, -d, 0, 0.0) - shift(f, d, 0, 0.0)) / (2.0 * d)


def pilot_tiers(seed=1):
    """The pilot's tier map: the walked benches drawn cell by cell, the frame from
    masses, the far range and the grooves, combined on the 8 px grid; every rim's runs two cells or more, tiers a
    face and a ledge apart (or stacked two high), then rounded and roughened."""
    cols, rows = PW // GRID, PH // GRID
    yc = np.arange(rows)[:, None] * GRID
    Cb = np.zeros((rows, cols), np.int16)
    for k, (y0, straight, sd) in BENCH.items():
        r = organic_rim(y0, straight, seed + sd)
        Cb = np.where(yc < r[None, :], np.maximum(Cb, k), Cb)
    xs = np.arange(cols) * GRID
    X, Y = np.meshgrid(xs + 4.0, np.arange(rows) * GRID + 4.0)
    Cf = grooves(range_cells(mass_cells(seed), seed), seed)
    Cf = np.where(Cf <= Cb, 0, Cf)
    C = soft_grid_cells(np.maximum(Cb, Cf), E_PILOT)
    T = np.repeat(np.repeat(C, GRID, 0), GRID, 1)[:PH, :PW].astype(np.int16)
    Tb = np.repeat(np.repeat(Cb, GRID, 0), GRID, 1)[:PH, :PW]
    T = smooth(T, seed, 12, 0.6)
    return T, Tb


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


def haze(p: Plot, depth=110, seed=0):
    """What lies beyond, hazier (plan 5.5): towards the top edge the darkest tones lift and
    the families turn to their cool siblings, so the far range sits back behind the névé;
    in the last rows a 2 x 2 checker of the snow's cool body (the house style's one use of
    dither: an atmospheric fade at a place's edge)."""
    t = np.clip((depth - p.y) / float(depth), 0, 1)
    m = t > 0
    lift = m & (p.t < EDGE_T)
    p.t[lift & (t > 0.25)] = np.maximum(p.t[lift & (t > 0.25)], 2)
    p.t[lift & (t > 0.6)] = np.maximum(p.t[lift & (t > 0.6)], 3)
    cool = m & (t > 0.15) & ~GLOW[p.f]
    p.f[cool] = COOL[p.f[cool]]
    edge = m & (p.t == EDGE_T) & (t > 0.35)
    p.t[edge] = 2
    chk = ((p.x // 2) + (p.y // 2)) % 2 == 0
    dth = m & chk & (p.y < 12) & (p.t < 3)
    p.put(dth, 'snow_cool', 3)


def rock_ground(p: Plot, m, seed=0):
    """Bare high ground between the cliffs: grey grit and broken rock in the stone family's
    cool siblings and slate (calm, body tone with soft patches), the cliff's granite lying
    loose as blocks and stones (lit on their upper left, a short shadow), moss in the
    hollows."""
    m = np.asarray(m, bool)
    if not m.any():
        return
    base(p, m, [('stone_cool', 0.5), ('slate_warm', 0.2), ('stone', 0.3)], seed, 11.0, tone=3, light=0.7, dark=0.3)
    stamp(p, m, 0.07, seed + 1, SMALL, swap='mix')
    stamp(p, m, 0.02, seed + 2, DOMINOES, dt=-1)
    moss = m & (fbm(p.x, p.y, 14, seed + 6) > 0.7)
    stamp(p, moss, 0.25, seed + 7, SMALL, ramp='grass_cool', tone=2, same_family=False)
    despeckle(p, m)
    for i, (x, y) in enumerate(_scatter(m, 200, seed + 8)):
        w = 3 + int(hash01(x, y, seed + 9) ** 1.5 * 10)
        stone(p, x - w // 2, y - 1, w, max(2, int(w * 0.6)), seed + i)


def cliff_feet(p: Plot, R: Relief, snow, seed=0):
    """Blue shade in the hollow at the foot of every cliff standing in snow (house snow: blue
    in hollows and on the south of things): two or three rows of the snow's own shade under
    the face's foot, wandering, the edge between them crisp."""
    foot = shift(R.face & (R.depth == R.fh - 1), 0, 1, False) & np.asarray(snow, bool) & ~p.solid
    reach = 2 + (fbm(p.x, p.y, 9, seed) * 3.5).astype(int)
    band = np.zeros(p.f.shape, bool)
    deep = np.zeros(p.f.shape, bool)
    for d in range(0, 6):
        s_ = shift(foot, 0, d, False) & np.asarray(snow, bool) & ~R.face & ~p.solid
        band |= s_ & (d < reach)
        deep |= s_ & (d < 1)
    p.put(band, 'snow_cool', 2)
    p.put(deep, 'snow_cool', 1)
    lip = shift(band, 0, 1, False) & ~band & np.asarray(snow, bool) & ~R.face & ~p.solid
    p.t[lip] = np.maximum(p.t[lip], 3)


def ledge_snow(p: Plot, R: Relief, m, seed=0, back=(4, 11), lip=(2, 4)):
    """Where snow lies on a ledge between cliffs (size guide: snow lies 2 to 4 px on lit
    tops): a lip along the rim, scalloped on its inner side, and a drift in the shade at the
    back, against the foot of the cliff above, 4 to 11 px deep and wandering. The rock
    between stays bare. Returns the mask (paint it with snowfield and snow_edge)."""
    m = np.asarray(m, bool)
    foot = shift(R.face & (R.depth == R.fh - 1), 0, 1, False) & m
    bd = back[0] + (fbm(p.x, p.y, 18, seed) * (back[1] - back[0] + 1)).astype(int)
    out = np.zeros(p.f.shape, bool)
    for d in range(0, back[1] + 1):
        out |= shift(foot, 0, d, False) & m & (d < bd)
    rim = shift(R.face & (R.depth == 0), 0, -1, False) & m
    ld = lip[0] + (fbm(p.x, p.y, 9, seed + 1) * (lip[1] - lip[0] + 1)).astype(int)
    sc = (p.x + (hash01(p.x // 6, 0, seed + 2) * 6).astype(int)) % 6
    ld = ld + ((sc >= 2) & (sc <= 3))
    for d in range(0, lip[1] + 2):
        out |= shift(rim, 0, -d, False) & m & (d < ld)
    return rounded(out, 1) & m


def rocks_in_snow(p: Plot, m, seed=0, every=1700):
    """Rocks breaking through the snow on high ground: stones and small blocks, each lit on
    its upper left, snow lying on its top, a blue shadow to the lower right."""
    for i, (x, y) in enumerate(_scatter(m, every, seed)):
        w = 5 + int(hash01(x, y, seed + 1) ** 1.5 * 9)
        stone(p, x - w // 2, y - 1, w, max(2, int(w * 0.6)), seed + i, snow_cap=w >= 4)


def pilot(seed=1):
    """The pilot scene, 640 x 1152 (two screens tall): the Col Path climbing in switchbacks
    (three ramps along faces, a stair through the moraine lip) past the Col hut to the
    Frostline lip, the cirque behind with its tarn under the headwall, the massif's peaks,
    névé and icefall beyond as the north border. Returns the plot and its parts."""
    T, Tb = pilot_tiers(seed)
    R = Relief(T, E_PILOT)
    p = Plot(PW, PH, 'snow', 3)
    p.tier = R.seen().astype(np.int8)
    frame = (T > Tb) & ~R.face
    tops = ~R.face
    E = np.asarray(E_PILOT)
    elev_top = E[np.clip(T, 0, len(E) - 1)]
    # --- grounds -------------------------------------------------------------------------
    walk_tops = tops & ~frame
    p.walk[:] = False
    # meadow, alpine turf, snow by height
    meadow(p, walk_tops & (T == 0), seed + 1)
    alpine_turf(p, walk_tops & (T == 1), seed + 2, flowers=0.8)
    alpine_turf(p, walk_tops & (T == 2), seed + 3, flowers=0.5)
    alpine_turf(p, walk_tops & (T == 3), seed + 4, flowers=0.3, stones=1.6)
    floor = walk_tops & (T == 4)
    snowfield(p, floor, seed + 5)
    # frame tops: turf ledges low down, snow ledges higher, snow on the névé and peaks
    low_frame = frame & (elev_top < 140)
    alpine_turf(p, low_frame, seed + 6, flowers=0.2, stones=2.0)
    beyond = frame & (T == 9) & (p.y < RANGE_FOOT - 40) & ~(p.x > 300) | (frame & (T == 9) & (p.y < 60))
    mid_frame = frame & (elev_top >= 140) & (elev_top < 300) & ~beyond
    rock_ground(p, mid_frame, seed + 15)
    high_frame = (frame & (elev_top >= 300)) | beyond
    snowfield(p, high_frame, seed + 7, swells=0.08, hollows=0.04, ripples=0.2, sastrugi=0.12)
    # snow lying on the walked benches: in the shade at the foot of faces and in hollows
    near_face = np.zeros(p.f.shape, np.float64)
    for d in range(1, 30, 3):
        near_face = np.maximum(near_face, shift(R.face, 0, d, False) * (1 - d / 30.0))
    shade = near_face + 0.6 * (fbm(p.x, p.y, 50, seed + 8) - 0.5)
    sn2 = snow_patches(p, walk_tops & (T == 2), 0.16, seed + 9, 26, shade * 1.6)
    sn3 = snow_patches(p, walk_tops & (T == 3), 0.34, seed + 10, 22, shade * 1.6)
    sn1 = snow_patches(p, walk_tops & (T == 1), 0.05, seed + 11, 20, shade * 1.6)
    snl = snow_patches(p, low_frame, 0.3, seed + 12, 20, shade * 1.6)
    snm = ledge_snow(p, R, mid_frame, seed + 16) | (snow_patches(p, mid_frame, 0.12, seed + 17, 16, shade * 1.8))
    snl |= ledge_snow(p, R, low_frame, seed + 18, back=(2, 6), lip=(1, 3))
    snowy = sn1 | sn2 | sn3 | snl | snm
    snowfield(p, snowy, seed + 13, swells=0.1, hollows=0.0, ripples=0.0, sastrugi=0.0, sparkle=0.002)
    snow_edge(p, snowy, (walk_tops | low_frame | mid_frame) & ~snowy, seed + 14)
    snow_all = floor | high_frame | snowy
    # --- faces, bands, shadows ---------------------------------------------------------------
    above_snow = shift(snow_all, 0, 1, False)
    rim_kind = np.zeros(p.f.shape, np.int8)    # 0 rock, 1 snow, 2 turf
    turf = tops & ~snow_all & (T >= 1) & ~mid_frame & ~high_frame
    # each face takes its rim's kind from the top just above it
    for k in range(1, int(T.max()) + 1):
        top_k = tops & (T == k)
        sn_k = top_k & snow_all
        tf_k = top_k & turf
        rk = (R.kf == k) & R.face
        # the rim row of every face column: what lies just above it
        colsn = (sn_k & shift(rk & (R.depth == 0), 0, -1, False)).any(0)
        coltf = (tf_k & shift(rk & (R.depth == 0), 0, -1, False)).any(0)
        rim_kind[rk & colsn[None, :]] = 1
        rim_kind[rk & coltf[None, :] & ~colsn[None, :]] = 2
    del above_snow
    snow_amt = np.clip((R.elev - 80) / 260.0, 0.1, 0.8)
    # the light on the frame's faces: each ridge lit on its west flank and shaded on its
    # east, each buttress likewise, with one hard terminator; the benches' own faces turn
    # at their ends (facet_light)
    zsm = frame_light(p.x + 0.5, p.y + 0.5, seed)
    lam_frame = np.clip(_slope_x(zsm, 3) * 70.0, -1.0, 1.0)
    rim_y = np.clip(p.y - R.depth - 1, 0, PH - 1)
    frame_face = R.face & (R.kf > Tb[rim_y, p.x])
    light = np.where(frame_face, lam_frame, facet_light(p, R, seed + 27))
    rock_faces(p, R, None, seed + 20, snow=snow_amt, rim=rim_kind, lichen=0.02, light=light)
    side_bands(p, R, seed + 21, snowy=snow_all)
    tier_shadows(p, R)
    cliff_feet(p, R, snow_all & ~R.face, seed + 22)
    talus(p, R, frame | floor, seed + 23, reach=7, snowy=snow_all)
    rocks_in_snow(p, high_frame & ~p.solid, seed + 24)
    # --- the cirque: tarn, moraine, glacier tongue, scree fans, icefall --------------------------
    tarn_m = rrect(p, 176, 424, 400, 512, 24, seed + 30, 1.5) & floor
    # the moraine: a ridge of rubble damming the tarn, its crest lit, its south slope in
    # shade with old snow lying in it
    yc = 538 + 7 * np.sin(p.x / 41.0) + 5 * (fbm(p.x, 0 * p.y, 30, seed + 31) - 0.5) * 2
    half = 18 + 6 * (fbm(p.x, p.y, 22, seed + 32) - 0.5) * 2
    moraine = floor & (np.abs(p.y - yc) < half) & (p.x > 150) & (p.x < 470) & ~dilate(tarn_m, 3)
    gravel(p, moraine, seed + 33)
    p.step(moraine & (p.y > yc + 3), -1)
    p.step(moraine & (np.abs(p.y - yc) <= 3), 1)
    msn = moraine & (p.y > yc + 6) & (fbm(p.x, p.y, 14, seed + 34) > 0.55)
    msn = rounded(msn, 1)
    snowfield(p, msn, seed + 35, swells=0.0, hollows=0.0, ripples=0.0, sastrugi=0.0, sparkle=0.0)
    p.f[msn] = IDX['snow_cool']
    snow_edge(p, msn, moraine & ~msn, seed + 36)
    for i, (x, y) in enumerate(_scatter(moraine & ~msn, 55, seed + 37)):
        w = 3 + int(hash01(x, y, seed + 38) ** 1.4 * 8)
        stone(p, x - w // 2, y - 1, w, max(2, int(w * 0.65)), seed + i, snow_cap=hash01(x, y, 3) < 0.3)
    ice_floor = floor & (p.x >= 436) & (p.y < 480)
    tongue = ice_floor & (((p.x - 490) / 52.0) ** 2 + ((p.y - 408) / 52.0) ** 2 <= 1)
    tongue = rounded(tongue, 3)
    glacier(p, tongue, seed + 36, bare=tongue & (p.y > 404), flow=(-0.2, 1.0))
    sx, sy = snout(p, tongue, 12, seed + 37)
    lat = dilate(tongue, 6) & ~tongue & floor & (p.x > 430) & (p.y > 396) & ~dilate(tarn_m, 3)
    gravel(p, lat, seed + 38)
    p.step(lat & ~shift(lat, 0, 1, False), 1)
    for i, (x, y) in enumerate(_scatter(lat, 40, seed + 45, margin=0)):
        w = 3 + int(hash01(x, y, seed + 46) * 4)
        stone(p, x - w // 2, y - 1, w, 2 + w // 3, seed + i, snow_cap=hash01(x, y, 5) < 0.4)
    # scree fans under the headwall's gullies, spreading onto the snow
    for i, (ax, ay, ln) in enumerate(((240, 402, 56), (366, 404, 48), (160, 470, 50))):
        scree_fan(p, (ax, ay), ln, 0.7, seed + 40 + i, m=floor & ~tarn_m & ~tongue, snowy=floor)
    tarn(p, tarn_m, seed + 39, ice=9)
    # meltwater from the snout into the tarn
    channel(p, [(sx, sy), (sx - 12, sy + 6), (396, sy + 6)], 8, seed + 41)
    # the icefall: the glacier pouring over the headwall's tiers as ice cliffs and broken ice
    cl_y = np.array([110.0, 170, 250, 330, 420])
    cl_x = np.array([492.0, 490, 484, 486, 488])
    hw_ = np.array([66.0, 54, 46, 44, 50])
    cxl = np.interp(p.y, cl_y, cl_x) + (fbm(0 * p.x, p.y, 40, seed + 40) - 0.5) * 10
    hwl = np.interp(p.y, cl_y, hw_) + (fbm(p.x, p.y, 24, seed + 42) - 0.5) * 12
    ice = (np.abs(p.x - cxl) < hwl) & (p.y >= 110) & (p.y < 400) & ((T >= 5) | (p.y < 396))
    ice = rounded(ice, 3)
    ice_faces(p, R, ice, seed + 43)
    neve = (T == 9) & ~R.face & (p.x > 300) & (p.x < 620)
    glacier(p, neve, seed + 44, crevasses=np.abs(p.x - 490) < 70)
    # --- the stream: the tarn's outflow down the step in falls ------------------------------------
    channel(p, [(192, 506), (192, 572)], 14, seed + 50)
    fall(p, R, 184, 200, seed + 51, k=4)
    channel(p, [(192, 600), (192, 620), (184, 636)], 14, seed + 52)
    fall(p, R, 176, 192, seed + 53, k=3)
    channel(p, [(184, 690), (184, 744), (200, 760), (200, 812)], 16, seed + 54)
    fall(p, R, 192, 208, seed + 55, k=2)
    channel(p, [(200, 860), (200, 920), (216, 950), (216, 976)], 16, seed + 56)
    fall(p, R, 208, 224, seed + 57, k=1)
    channel(p, [(216, 1016), (216, 1080), (240, 1110), (240, 1160)], 16, seed + 58)
    # --- the Col Path ---------------------------------------------------------------------------
    path = []
    path.append(trail(p, [(456, 1160), (456, 1080), (440, 1040), (432, 1010)], 16, seed + 60))
    rA = ramp_along(p, R, 320, 424, 24, seed + 61, rising='west', k=1)
    path.append(trail(p, [(316, 960), (312, 920), (304, 880), (300, 852)], 16, seed + 62))
    rB = ramp_along(p, R, 296, 400, 24, seed + 63, rising='east', k=2)
    path.append(trail(p, [(404, 800), (420, 760), (452, 720), (476, 690), (484, 672)], 16, seed + 64))
    path.append(trail(p, [(300, 784), (330, 790), (380, 790), (412, 784)], 12, seed + 65))
    rC = ramp_along(p, R, 392, 496, 24, seed + 66, rising='west', k=3)
    path.append(trail(p, [(388, 624), (396, 600)], 16, seed + 67))
    st = stair(p, R, 376, 40, seed + 68, k=4)
    path.append(trail(p, [(400, 560), (404, 530), (410, 500), (414, 482)], 12, seed + 69, kind='snow', m=floor))
    # --- things on the land ------------------------------------------------------------------------
    hut, hsh, hblock = col_hut(1, seed)
    paste(p, hut, 268, 778, shadow=hsh, block=hblock)
    nb, nbs = noticeboard(seed)
    paste(p, nb, 330, 772, shadow=nbs, block=nb.m & (nb.y > 30))
    wy = (618 + 4 * np.sin(np.arange(200, 524) / 37.0)).astype(np.int32)
    drystone(p, 200, 524, wy, seed + 71, 11, gate=380)
    for i, (x, y, w, sn, bl) in enumerate(((344, 952, 22, False, True), (476, 1048, 18, False, False),
                                             (260, 868, 24, False, True), (360, 700, 20, True, False),
                                             (520, 744, 26, True, False), (452, 600, 16, True, True),
                                             (300, 520, 20, True, False), (480, 520, 18, True, True))):
        b, bs = boulder(seed + 80 + i, w, None, sn, bl)
        paste(p, b, x, y, shadow=bs, block=b.m & (b.y > b.fy - 5))
        if sn:
            drift(p, x + w // 2, y, max(4, w // 3), seed + 90 + i)
    for i, (x, y) in enumerate(((396, 476), (420, 548), (420, 690), (340, 892), (448, 1000))):
        c, cs = cairn(seed + 100 + i, None, snow=y < 720)
        paste(p, c, x + 18, y, shadow=cs)
    fire_ring(p, 434, 500, seed + 110)
    sl, sls = sledge(seed)
    paste(p, sl, 412, 528, shadow=sls)
    # firs: thinning out with height, none above the hut's bench
    fir_spots = [(40, 1140, 84), (96, 1136, 70), (560, 1130, 80), (608, 1120, 66), (520, 1100, 58),
                 (140, 1100, 60), (600, 1000, 54), (64, 1040, 50), (256, 940, 52), (520, 940, 48),
                 (150, 900, 44)]
    fir_spots.sort(key=lambda t: t[1])
    for i, (x, y, h) in enumerate(fir_spots):
        if p.solid[y, x] or p.wet[y, x]:
            continue
        f_, fs = fir(seed + 120 + i, h, snow=0.25 if y > 1000 else 0.6)
        paste(p, f_, x, y, shadow=fs, block=f_.m & (f_.y > f_.fy - 3))
    haze(p, 110, seed + 130)
    parts = dict(R=R, T=T, Tb=Tb, frame=frame, tarn=tarn_m, tongue=tongue, ice=ice, ramps=(rA, rB, rC),
                 stair=st, path=path)
    return p, parts


# --- the sheet, the comparison, the bar, the checks ------------------------------------------------
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RAMP_TONES = 0.85     # house-style ruling (cea6bae): ramp-built art passes tones at 85 %

# Official screenshots of mountain, cliff and snow scenes, for the side-by-side comparison.
# Only the URLs, boxes and the adult's height there are kept; the images stay out of the
# repository (read from REF_DIR by the URL's file name).
REFS = (
    ('Sea of Stars: snow and rock walls (Wraith Island)', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/'
     'ss_f756ff477590284c7192ffcef99237de056e4aeb.1920x1080.jpg', (300, 100, 1500, 940), 150.0),
    ('Sea of Stars: a ledge path across a cliff', 'https://sabotagestudio.com/wp-content/uploads/2022/03/Traversal-4-launch.png',
     (440, 0, 1640, 840), 150.0),
    ('Sea of Stars: a cliff top over the void', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/'
     'ss_fde8785c643e0386e63cdb8057ff8c6d9cf24fe0.1920x1080.jpg', (0, 0, 1200, 840), 150.0),
    ('Eastward: a rock cliff, mountains beyond (Octopia)', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/'
     'ss_c3e35bbd8e25af924b3b9cbf087f1f0c77dcf68a.1920x1080.jpg', (0, 0, 1296, 907), 162.0),
    ('Eastward: ledges and a stair (Octopia)', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/'
     'ss_f5788b1d4ade71e0cdb1e0110debfad3b32ca51c.1920x1080.jpg', (200, 380, 1496, 1080), 162.0),
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


# Where the pilot is measured with the detail bar: (region to search, kind, what). Faces are
# measured on the best 50 x 34 box of rock face inside the region; the rest on fixed boxes.
PILOT_FACES = (
    ((0, 560, 150, 900), 'stone-wall', 'the west crags: a cliff band'),
    ((0, 560, 150, 900), 'face', 'the west crags: a cliff band'),
    ((500, 560, 640, 900), 'stone-wall', 'the east crags: a cliff band'),
    ((180, 200, 440, 400), 'stone-wall', 'the headwall'),
    ((0, 100, 640, 200), 'stone-wall', 'the far range, under its haze'),
    ((430, 940, 560, 1020), 'stone-wall', 'face A beside its ramp'),
)
PILOT_BOXES = (
    ((330, 816, 398, 852), 'stair', 'ramp B and its retaining wall'),
    ((420, 860, 510, 950), 'ground', 'alpine turf on bench 1'),
    ((200, 440, 320, 496), 'water', 'the tarn'),
    ((176, 690, 226, 760), 'stream', 'the meltwater on the hut bench'),
)


def face_box(R, region, w=50, h=34, avoid=None):
    """The box of w x h inside region that holds the most rock face (none of it ice)."""
    x0, y0, x1, y1 = region
    fc = R.face.copy()
    if avoid is not None:
        fc &= ~np.asarray(avoid, bool)
    ii = np.pad(np.cumsum(np.cumsum(fc.astype(np.int32), 0), 1), ((1, 0), (1, 0)))
    best = None
    for y in range(y0, y1 - h, 2):
        for x in range(x0, x1 - w, 2):
            a = ii[y + h, x + w] - ii[y, x + w] - ii[y + h, x] + ii[y, x]
            if best is None or a > best[0]:
                best = (a, (x, y, x + w, y + h))
    return best[1]


def pilot_preview(p, scale=2, people=True):
    """The pilot at `scale`, with residents standing in it for scale (preview only)."""
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in (('hiker', (372, 836)), ('warden', (262, 798)), ('porter', (300, 960)),
                             ('naturalist', (412, 520)), ('forager', (470, 1080))):
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
    """Pilot crops beside official Eastward and Sea of Stars mountain, cliff and snow scenes,
    all at the same character height (an adult 25 px) and the same scale."""
    ours = pilot_preview(p, 1)
    crops = [('ours: the Col hut, ramp B and the crags', ours.crop((200, 690, 400, 830))),
             ('ours: the headwall, its couloirs and the icefall', ours.crop((340, 170, 540, 310))),
             ('ours: the moraine stair, the lip and the tarn', ours.crop((260, 440, 460, 580))),
             ('ours: the west crags and the falls', ours.crop((40, 560, 240, 700))),
             ('ours: the far range and the névé', ours.crop((0, 0, 200, 140)))]
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


def _cliff_tile(seed=3, snowy=True, rows=None):
    """A cliff of three tiers with a spur and a gully, on snow or turf."""
    rows = rows or ['0000000000000000000000',
                    '0000000000000000000000',
                    '1111111111111111111000',
                    '1111111111111111111000',
                    '1111111111111111111000',
                    '2222222222222222220000',
                    '2222222222222222220000',
                    '3333333311133333300000',
                    '3333333311133333300000',
                    '3333333311133333300000',
                    '4444444411144444000000',
                    '4444444411144444000000']
    rows = rows[::-1]
    Hh, Ww = len(rows) * GRID, len(rows[0]) * GRID
    T = np.zeros((Hh, Ww), np.int16)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            T[j * GRID:(j + 1) * GRID, i * GRID:(i + 1) * GRID] = int(ch)
    T = smooth(T, seed)
    R = Relief(T, [0, 32, 64, 96, 128])
    q = Plot(Ww, Hh, 'snow', 3)
    tops = ~R.face
    if snowy:
        snowfield(q, tops, seed)
    else:
        alpine_turf(q, tops, seed)
    rock_faces(q, R, None, seed + 1, snow=0.7 if snowy else 0.2, rim='snow' if snowy else 'turf')
    side_bands(q, R, seed + 2, snowy=tops if snowy else None)
    tier_shadows(q, R)
    talus(q, R, None, seed + 3, snowy=tops if snowy else None)
    return q, R


def pieces():
    """Every piece on its own tile: (group, name, plot, [(box, kind)])."""
    out = []
    q, R = _cliff_tile(3, True)
    out.append(('rock', 'cliff bands on snow: three tiers, a spur, a gully, ledges with snow', q,
                [((8, 34, 76, 70), 'stone-wall'), ((96, 34, 164, 70), 'face')]))
    q, R = _cliff_tile(5, False)
    out.append(('rock', 'cliff bands under turf: grass lips, talus', q, [((8, 34, 76, 70), 'stone-wall')]))
    q = Plot(160, 96, 'snow', 3)
    snowfield(q, q.mask(), 7)
    out.append(('snow', 'snowfield: calm plane, swells, hollows, ripples, sastrugi', q, []))
    q = Plot(160, 96, 'snow', 3)
    alpine_turf(q, q.mask(), 8)
    sn = snow_patches(q, q.mask(), 0.45, 9, 26)
    snowfield(q, sn, 10, sastrugi=0)
    snow_edge(q, sn, None, 11)
    out.append(('snow', 'snow lying on turf: lobed patches, the crisp scalloped edge', q, []))
    q = Plot(160, 80, 'snow', 3)
    snowfield(q, q.mask(), 12, ripples=0.2, sastrugi=0.1)
    for i, (x, y, w) in enumerate(((30, 40, 22), (90, 60, 18))):
        b, bs = boulder(20 + i, w, None, True)
        paste(q, b, x, y, shadow=bs)
        drift(q, x + w // 2, y, max(4, w // 3), 30 + i)
    tracks(q, [(0, 70), (60, 66), (120, 74), (170, 70)], 13, 'boots')
    tracks(q, [(0, 20), (80, 24), (170, 18)], 14, 'sledge')
    out.append(('snow', 'drifts in the lee of boulders, boot prints, a sledge track', q, []))
    q = Plot(128, 96, 'snow', 3)
    alpine_turf(q, q.mask(), 15)
    out.append(('ground', 'alpine turf: tufts, cushion plants, flowers, stones', q, [((10, 10, 120, 88), 'ground')]))
    q = Plot(128, 96, 'snow', 3)
    meadow(q, q.mask(), 16)
    out.append(('ground', 'hay meadow below the treeline', q, [((10, 10, 120, 88), 'ground')]))
    q = Plot(160, 112, 'snow', 3)
    snowfield(q, q.mask(), 17)
    scree_fan(q, (80, 6), 90, 0.8, 18, snowy=q.mask())
    out.append(('ground', 'a scree fan spreading onto the snow', q, [((52, 30, 108, 86), 'foot')]))
    q = Plot(176, 112, 'snow', 3)
    snowfield(q, q.mask(), 19)
    tm = rrect(q, 16, 16, 160, 92, 12, 20, 2.0)
    tarn(q, tm, 21, ice=8)
    out.append(('water', 'the tarn: deep middle, shallows, ice in the shade, a lit south lip', q,
                [((40, 36, 140, 86), 'water')]))
    q, R = _cliff_tile(23, False, ['0000000000000000',
                                   '0000000000000000',
                                   '0000000000000000',
                                   '0000000000000000',
                                   '0000000000000000',
                                   '0000000000000000',
                                   '0000000000000000',
                                   '0000000000000000',
                                   '1111111111111111',
                                   '1111111111111111',
                                   '1111111111111111',
                                   '1111111111111111'])
    channel(q, [(60, -4), (60, 34)], 16, 24)
    fall(q, R, 52, 68, 25)
    channel(q, [(60, 84), (60, 100), (96, 100), (140, 100)], 16, 26)
    out.append(('water', 'meltwater: a channel, a fall as wide as it, a plunge pool', q,
                [((30, 70, 98, 106), 'stream')]))
    q = Plot(176, 120, 'snow', 3)
    snowfield(q, q.mask(), 26)
    gm = (((q.x - 88) / 70.0) ** 2 + ((q.y + 10) / 96.0) ** 2) <= 1
    glacier(q, gm, 28, bare=gm & (q.y > 40), flow=(0.0, 1.0))
    sx_, sy_ = snout(q, gm, 12, 29)
    channel(q, [(sx_, sy_), (sx_, sy_ + 8), (sx_ + 20, 130)], 8, 30)
    out.append(('ice', 'a glacier: névé with crevasses, bare ice with ogives, the snout', q, []))
    q, R = _cliff_tile(30, True)
    ice_faces(q, R, (q.x >= 40) & (q.x < 120), 31)
    out.append(('ice', 'an icefall: the glacier over the tiers as ice cliffs and broken ice', q, []))
    q, R = _cliff_tile(31, False, ['000000000000000000000000',
                                   '000000000000000000000000',
                                   '000000000000000000000000',
                                   '000000000000000000000000',
                                   '000000000000000000000000',
                                   '111111111111111111111111',
                                   '111111111111111111111111',
                                   '111111111111111111111111',
                                   '111111111111111111111111'])
    ramp_along(q, R, 48, 152, 24, 32, rising='east', k=1)
    out.append(('built', 'a ramp along a face: drystone retaining wall, parapet', q,
                [((70, 44, 140, 80), 'stair')]))
    rows = ['000000000000', '000000000000', '000000000000', '111111111111', '111111111111',
            '111111111111', '111111111111']
    T = np.zeros((len(rows) * 8, 96), np.int16)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            T[j * 8:(j + 1) * 8, i * 8:(i + 1) * 8] = int(ch)
    T = smooth(T[::-1].copy(), 33)
    R = Relief(T, [0, 16])
    q = Plot(96, len(rows) * 8, 'snow', 3)
    gravel(q, ~R.face, 34)
    rock_faces(q, R, None, 35, snow=0.4, rim='rock')
    side_bands(q, R, 36)
    tier_shadows(q, R)
    stair(q, R, 24, 40, 37)
    out.append(('built', 'a stair through a low step (the moraine lip)', q, []))
    q = Plot(160, 48, 'snow', 3)
    alpine_turf(q, q.mask(), 38)
    drystone(q, 4, 156, 36, 39, 10, gate=70)
    out.append(('built', 'a drystone wall with its gate', q, []))
    q = Plot(160, 64, 'snow', 3)
    alpine_turf(q, q.mask(), 40)
    trail(q, [(-8, 40), (60, 36), (120, 44), (170, 40)], 16, 41)
    out.append(('built', 'a mountain trail on turf', q, []))
    q = Plot(160, 64, 'snow', 3)
    snowfield(q, q.mask(), 42)
    trail(q, [(-8, 30), (60, 34), (120, 28), (170, 32)], 16, 43, kind='snow')
    out.append(('built', 'a trail trodden in snow', q, []))
    q = Plot(256, 112, 'snow', 3)
    alpine_turf(q, q.mask(), 44)
    hut, hsh, hb = col_hut(1, 0)
    paste(q, hut, 72, 100, shadow=hsh, block=hb)
    nb, nbs = noticeboard(0)
    paste(q, nb, 130, 96, shadow=nbs)
    c, cs = cairn(46)
    paste(q, c, 170, 96, shadow=cs)
    fire_ring(q, 214, 90, 47)
    sl, sls = sledge(0)
    paste(q, sl, 226, 106, shadow=sls)
    out.append(('things', 'the Col hut (house kit, snow on its roof), notice board, cairn, fire ring, sledge', q,
                [((40, 50, 104, 86), 'stone-wall')]))
    q = Plot(256, 112, 'snow', 3)
    alpine_turf(q, q.mask() & (q.x < 128), 48)
    snowfield(q, q.mask() & (q.x >= 128), 49)
    for i, (x, w, sn, bl) in enumerate(((30, 28, False, True), (80, 20, False, False), (160, 30, True, False),
                                        (214, 22, True, True))):
        b, bs = boulder(50 + i, w, None, sn, bl)
        paste(q, b, x, 100, shadow=bs)
    out.append(('things', 'boulders: plain, with the trail blaze, snow-capped', q, []))
    q = Plot(192, 112, 'snow', 3)
    alpine_turf(q, q.mask(), 51)
    for i, (x, h, sn) in enumerate(((32, 92, 0.2), (88, 72, 0.5), (140, 56, 0.8), (176, 40, 0.8))):
        f_, fs = fir(60 + i, h, sn)
        paste(q, f_, x, 108, shadow=fs)
    out.append(('things', 'firs, thinning out with height', q, [((16, 30, 52, 66), 'tree')]))
    return out


def kit_sheet(items, scale=2):
    """Every piece at `scale`, grouped, each labelled with its detail bar result."""
    pad, lab = 10, 30
    groups = ['rock', 'snow', 'ground', 'water', 'ice', 'built', 'things']
    titles = {'rock': 'Rock on the soft grid: cliff bands, ledges, side bands, shadows, talus',
              'snow': 'Snow in the house style: the calm plane, the crisp edge, drifts, tracks',
              'ground': 'Ground: alpine turf, meadow, scree',
              'water': 'Water: the tarn, meltwater, a fall into its pool',
              'ice': 'Ice: glacier, snout, icefall',
              'built': 'Ways up: a ramp with its retaining wall, a stair, a wall and gate, trails',
              'things': 'Things: the Col hut, notice board, cairn, fire ring, sledge, boulders, firs'}
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
    """The kit's contracts on the pilot: the Col Path can be walked from the meadow to the
    tarn's shore; it climbs only by its ramps and the stair (no face is walkable); water,
    ice and the frame stop a walker; the ramps are at least 24 wide and the stair 40 open."""
    faults = []
    if p is None:
        p, parts = pilot()
    R = parts['R']
    a, b = (456, 1140), (414, 486)
    if not p.walk[a[1], a[0]] or not p.walk[b[1], b[0]]:
        faults.append(f'the path ends are not walkable: {bool(p.walk[a[1], a[0]])}, {bool(p.walk[b[1], b[0]])}')
    elif not _reaches(p.walk, a, b):
        faults.append('the Col Path cannot be walked from the meadow to the tarn')
    ways = parts['stair'] | parts['ramps'][0] | parts['ramps'][1] | parts['ramps'][2]
    bad = p.walk & R.face & ~ways
    if bad.any():
        faults.append(f'{int(bad.sum())} face pixels outside the ramps and stair are walkable')
    if (p.walk & p.wet).any():
        faults.append(f'{int((p.walk & p.wet).sum())} water pixels are walkable')
    if (p.walk & p.hazard).any():
        faults.append(f'{int((p.walk & p.hazard).sum())} ice or water pixels are walkable')
    if (p.walk & parts['frame']).any():
        faults.append(f'{int((p.walk & parts["frame"]).sum())} frame pixels are walkable')
    for i, r in enumerate(parts['ramps']):
        cols = r.sum(0)
        if r.any() and np.median(cols[cols > 0]) < 20:
            faults.append(f'ramp {"ABC"[i]} is narrower than 24 px on screen')
    st = parts['stair']
    if st.any():
        xs = np.nonzero(st.any(0))[0]
        if xs.max() - xs.min() + 1 < 40:
            faults.append('the stair is narrower than 40 px open')
    return faults


def main(argv):
    if '--check' in argv:
        faults = check()
        for f in faults:
            print('FAULT:', f)
        print('mountain_kit check:', 'pass' if not faults else f'{len(faults)} faults')
        return 1 if faults else 0
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-mountain-kit')
    os.makedirs(out, exist_ok=True)
    p, parts = pilot()
    p.image().save(os.path.join(out, 'pilot.png'))
    pilot_preview(p, 2).save(os.path.join(out, 'pilot-2x.png'))
    night(pilot_preview(p, 1)).resize((p.w * 2, p.h * 2), Image.NEAREST).save(os.path.join(out, 'pilot-night.png'))
    print('pilot boxes:')
    boxes = [(face_box(parts['R'], reg, avoid=parts['ice'] | p.wet), kind, what) for reg, kind, what in PILOT_FACES]
    for box, kind, what in boxes + list(PILOT_BOXES):
        c, strict, ramp, line = bar_line(p.image(), box, kind)
        print(f'  {what:40s} {line}  isolated {c["isolated"]:.3f} cluster {c["cluster"]:.1f}')
    cmp_ = compare_sheet(p)
    cmp_.save(os.path.join(out, 'compare.png'))
    items = pieces()
    sheet, rows = kit_sheet(items)
    sheet.save(os.path.join(out, 'kit-sheet.png'))
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
