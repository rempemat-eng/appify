"""The river and meadow kit: the pieces the home valley and the great river are painted with.

Claude E's lane (the home valley's places). Matt, 20 Oct 14:45, on world plan v5: "it is
important that you get the transitions from one zone into the other right. while staying
relatively realistic make them distinct and interesting from a game play perspective ...
also getting the verticality right in different parts of the map is super important".
The Sleepwater runs from the Frostline through the valley to Driftwood's cove; the Lull runs
east through the Narrows and Lullford to its delta. This module is the kit both are drawn
with; nothing in the game reads it yet (zones wire it in once the v5.1 layouts land).

Everything is drawn in the house style (docs/vision/house-style.md, PR #121): every pixel is
a tone of a house ramp (art/house-palette.json) or a family's edge tone, shade and light move
along the ramps (no RGB arithmetic), texture is clusters of two to four pixels (no speckle),
walkable ground stays calm (body tone 3, patches one tone off, mostly sibling swaps), light
comes from the upper left and cast shadows step the ground two tones down. Sizes follow
docs/vision/size-guide.md (PR #124): an adult 25 px, a stream 16 to 24, a river 40 to 64, a
canal 40 with a towpath 16 to 24, a ford 24 to 32 with stepping stones 8 to 12 apart, a farm
track 24 with two ruts, a hedgerow 14 to 20 tall and 8 to 16 deep, a field gate 32 to 48
between heavier posts, a willow 72 to 110, reeds 14 to 32 in clumps of 3 to 6.

The model. A `Plot` is a ground canvas held as two arrays: the house ramp of each pixel and
its tone (0 deepest .. 5 highlight, 6 the ramp's edge tone). Pieces paint masks into it, so
they compose: lay the ground (meadow, pasture, plough, crop, heath, woodland floor), then
water (`river`, `race`, `canal`) which cuts its own banks, then linear things (`track`,
`hedgerow`), then standing things (`willow`, `alder`, `reeds`, `gate`), each sprite with its
edge-tone outline and its cast shadow. `Plot.image()` turns it into pixels.

Verticality in the water pieces is real: the water surface lies below the land (a cut bank
7 px, a stone revetment 10, a canal's coping 6, a point bar 1), so a north bank shows its
face (earth with roots and slumped clods, or coursed stone) and a south bank only its lip
with the water dark beneath it, as in Eastward's canals and Sea of Stars' rivers.

The pieces (each with a variant/seed argument, all deterministic):
- water: `river(plot, centreline, width)` a channel whose banks differ by side of the bend
  (cut bank with an earth face on the outside, sand and gravel point bar on the inside),
  pools at bends and riffles at the crossings between them; `ford()` at a riffle with
  stepping stones; `race()` a mill race in a stone revetment; `canal()` a canal edge with
  coping and towpath; `flow_frames()` the moving water through water_flow.py, recoloured
  onto the water ramp.
- water's edge: `reeds()`, `marginals()` (flag iris, meadowsweet, loosestrife, marsh
  marigold), `lilies()`, `willow()`, `alder()`.
- farmland: `hay_meadow()`, `pasture()`, `plough()` and `crop()` (rows along the contours of
  a height field), `margin()` (an uncut field margin), `hedgerow()` (gaps and a `gate()`),
  `track()` (a farm track: two ruts, a grass crown, puddles).
- transitions: `heath()` (the Brackens: heather, bracken, gorse, sandy ground, birches),
  `wood_floor()` and `wood_edge()` (the Fern hills: a fringe of tall herbs and bramble,
  shrubs, oaks, ferns and bluebells in their shade), and `blend()`, which mixes two grounds
  over a band with outliers on both sides, so a region change reads without a line.

Water blocks a walker unless a crossing is declared: `river(ford_at=...)` marks its ford's
shallows in `Plot.crossing`, and `track()` opens water only there, so painting a track over a
river never makes a crossing by itself (`--check` holds the kit to this).

Run:
    python3 scripts/art/river_kit.py --check     (the crossing contract; exits non-zero on a fault)
    python3 scripts/art/river_kit.py [OUT_DIR]
writes OUT_DIR/kit-sheet.png (every piece at 2x, labelled), OUT_DIR/sample.png (a bend of
the Sleepwater with a ford, a meadow, a hedged field and the heath edge, 640 x 576, at 1x and
2x), OUT_DIR/sample-flow.gif (its water moving) and prints the detail bar (detail_bar.py)
and the style lint counts for every piece. Default OUT_DIR: napattack-river-kit in the
system's temp folder, never the repository.
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


# --- noise (deterministic, numpy) ---------------------------------------------------------
def hash01(x, y, seed=0):
    """Hash noise in [0, 1) on integer coordinates."""
    x = np.asarray(x, np.int64) & 0xFFFFFFFF
    y = np.asarray(y, np.int64) & 0xFFFFFFFF
    h = (x * 374761393 + y * 668265263 + (seed * 2246822519 & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / float(0x1000000)


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


def disc(cx, cy, r, shape):
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    return (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r


def blob(cx, cy, rx, ry, shape, seed=0, wob=0.18, lobes=7):
    """A soft natural shape: an ellipse with a wobbling rim (never a perfect ellipse)."""
    h, w = shape
    y, x = np.mgrid[0:h, 0:w]
    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    ang = np.arctan2(v, u)
    r = 1 + wob * (0.6 * np.sin(ang * lobes + seed) + 0.4 * np.sin(ang * (lobes + 4) + seed * 1.7))
    return u * u + v * v <= r * r


# --- the plot: ramps and tones ------------------------------------------------------------
class Plot:
    """A ground canvas as house ramp indices (f) and tones (t, 0..5, 6 the edge tone)."""

    def __init__(self, w, h, ramp='grass', tone=3):
        self.w, self.h = w, h
        self.f = np.full((h, w), IDX[ramp], np.int16)
        self.t = np.full((h, w), tone, np.int8)
        self.wet = np.zeros((h, w), bool)      # water surface pixels (for water_flow)
        self.solid = np.zeros((h, w), bool)    # sprites: what stands up (outlined, blocks)
        self.walk = np.ones((h, w), bool)      # walkable on foot
        self.crossing = np.zeros((h, w), bool)  # water declared crossable (a ford's shallows)
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

    def sib(self, m, which):
        """Swap pixels to their family's warm or cool sibling (or back to the body ramp)."""
        m = np.asarray(m, bool)
        table = {'warm': WARM, 'cool': COOL, 'body': FAMILY}[which]
        self.f[m] = table[self.f[m]]

    def fam(self, name):
        return FAMILY[self.f] == IDX[name]

    def image(self, scale=1):
        rgb = COL[self.f, np.clip(self.t, 0, EDGE_T)]
        img = Image.fromarray(rgb, 'RGB')
        return img.resize((self.w * scale, self.h * scale), Image.NEAREST) if scale != 1 else img

    def crop(self, x0, y0, x1, y1):
        p = Plot(x1 - x0, y1 - y0)
        for a in ('f', 't', 'wet', 'solid', 'walk'):
            setattr(p, a, getattr(self, a)[y0:y1, x0:x1].copy())
        return p


# Cluster shapes: two to four pixels, never one (house rule 4).
DOMINOES = (((0, 0), (1, 0)), ((0, 0), (0, 1)))
SMALL = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)),
         ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1)))
BLADES = (((0, 0), (0, -1)), ((0, 0), (0, -1), (0, -2)), ((0, 0), (0, -1), (1, -2)),
          ((0, 0), (0, -1), (-1, -2)), ((0, 0), (1, 0), (0, -1)))


def stamp(p: Plot, m, density, seed, shapes=SMALL, ramp=None, dt=0, swap=None, same_family=True,
          tone=None):
    """Clusters over a mask: at seeds (hash < density) each stamps one of `shapes` with the
    seed pixel's ramp moved `dt` tones (an int or an array per pixel), swapped to a sibling
    ('warm', 'cool', 'mix') or set to `ramp`/`tone`. With same_family, a cluster only
    covers pixels of the seed's family within one tone of it, so clusters stay inside their
    surface. Returns the pixels changed."""
    m = np.asarray(m, bool)
    seeds = m & (hash01(p.x, p.y, seed) < density)
    k = (hash01(p.x, p.y, seed + 1) * len(shapes)).astype(int)
    if ramp is not None:
        nf = np.full(p.f.shape, IDX[ramp] if isinstance(ramp, str) else 0, np.int16)
        if not isinstance(ramp, str):
            nf = np.asarray(ramp, np.int16)
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
            tgt = shift(s, dx, dy, False) & m
            sf, st = shift(seed_fam, dx, dy, -1), shift(seed_t, dx, dy, -9)
            fnew, tnew = shift(nf, dx, dy, 0), shift(nt, dx, dy, 0)
            if same_family:
                tgt &= (FAMILY[p.f] == sf) & (np.abs(p.t - st) <= 1) & (p.t < EDGE_T)
            p.f[tgt], p.t[tgt] = fnew[tgt], tnew[tgt]
            changed |= tgt
    return changed


def despeckle(p: Plot, m=None, passes=2):
    """No lone pixels: a pixel unlike all four neighbours takes its neighbours' commonest
    colour, unless it is a deliberate glint (tone 5) or an edge."""
    key = p.f.astype(np.int32) * 8 + p.t
    m = np.ones(key.shape, bool) if m is None else np.asarray(m, bool)
    for _ in range(passes):
        nb = [shift(key, dx, dy, -1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        lone = m & (p.t < 5) & np.all([key != n for n in nb], axis=0)
        if not lone.any():
            break
        # the neighbour that matches another neighbour, else the left one
        pick = nb[1].copy()
        for i in range(4):
            for j in range(i + 1, 4):
                pick = np.where((nb[i] == nb[j]) & (nb[i] >= 0), nb[i], pick)
        pick = np.where(pick < 0, nb[0], pick)
        ok = lone & (pick >= 0)
        p.f[ok], p.t[ok] = pick[ok] // 8, pick[ok] % 8
        key = p.f.astype(np.int32) * 8 + p.t


def lone_share(p: Plot, m=None) -> float:
    key = p.f.astype(np.int32) * 8 + p.t
    nb = [shift(key, dx, dy, -1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    lone = np.all([key != n for n in nb], axis=0)
    m = np.ones(key.shape, bool) if m is None else m
    return float(lone[m].mean())


# --- ground ---------------------------------------------------------------------------------
def base(p: Plot, m, ramp, seed, scale=7.0, tone=3, light=0.70, dark=0.27, warm=0.30, cool=0.70):
    """Calm ground (house rule 8): the body ramp and its siblings in broad soft patches at
    one tone, lighter where the noise is high, a tone down where it is low. No specks."""
    m = np.asarray(m, bool)
    n = fbm(p.x, p.y, scale * 1.7, seed + 7)
    f = np.where(n < warm, IDX[f'{ramp}_warm'], np.where(n > cool, IDX[f'{ramp}_cool'], IDX[ramp]))
    p.f[m] = f[m]
    p.t[m] = tone
    pn = fbm(p.x, p.y, scale, seed)
    p.step(m & (pn > light), 1)
    p.step(m & (pn < dark), -1)
    despeckle(p, m)


def texture(p: Plot, m, seed, swaps=0.10, ups=0.025, downs=0.025, shapes=SMALL):
    """Many small shapes without value noise: clusters that swap to a sibling ramp at the
    same tone, and a few a tone up (more often towards the light) or down."""
    stamp(p, m, swaps, seed, shapes, swap='mix')
    stamp(p, m, ups, seed + 10, shapes, dt=1)
    stamp(p, m, downs, seed + 20, shapes, dt=-1)


def flowers(p: Plot, m, seed, kinds, density):
    """Wild flowers as clusters of two or three pixels: (ramp, tone, share) per kind, set
    in loose drifts (a flower grows where others of its kind do)."""
    drift = fbm(p.x, p.y, 18, seed + 3)
    acc = 0.0
    for i, (ramp, tone, share) in enumerate(kinds):
        r = hash01(p.x // 9, p.y // 9, seed + 40 + i)
        zone = m & (drift > 0.35) & (r < share * 2.2)
        stamp(p, zone, density, seed + 50 + i, DOMINOES + (((0, 0), (1, 0), (0, -1)),), ramp=ramp,
              tone=tone, same_family=False)
        acc += share


HAY_FLOWERS = (('brass', 5, 0.35), ('plaster', 5, 0.25), ('berry', 4, 0.15), ('dusk', 4, 0.15),
               ('clay', 3, 0.10))     # buttercup, ox-eye daisy, red clover, knapweed, sorrel


def hay_meadow(p: Plot, m, seed=1):
    """A hay meadow before mowing: long grass yellowing to seed, combed by the wind into
    lighter swathes, blades in strokes with lit tips, seed heads, flowers in drifts."""
    m = np.asarray(m, bool)
    base(p, m, 'grass', seed, scale=9, warm=0.42, cool=0.80)
    wind = np.sin(p.x * 0.045 + p.y * 0.11 + 3 * fbm(p.x, p.y, 40, seed + 5)) > 0.55
    p.step(m & wind & (fbm(p.x, p.y, 6, seed + 6) > 0.4), 1)
    despeckle(p, m)
    texture(p, m, seed + 100, swaps=0.08, ups=0.0, downs=0.0)
    stamp(p, m, 0.050, seed + 200, BLADES, dt=1)              # lit blade tips
    stamp(p, m, 0.018, seed + 210, BLADES, dt=-1)             # blades in their own shade
    stamp(p, m & (hash01(p.x // 5, p.y // 5, seed) < 0.5), 0.02, seed + 220, DOMINOES[1:],
          ramp='sand_warm', tone=4, same_family=False)        # seed heads
    flowers(p, m, seed + 300, HAY_FLOWERS, 0.012)
    despeckle(p, m)


def pasture(p: Plot, m, seed=2, tussocks=True):
    """Grazed pasture: short even turf, a little bluer and lighter than hay, clover in
    patches, rush tussocks where it is damp, the odd molehill."""
    m = np.asarray(m, bool)
    base(p, m, 'grass', seed, scale=6, warm=0.22, cool=0.62)
    texture(p, m, seed + 100, swaps=0.15, ups=0.012, downs=0.02)
    clover = m & (fbm(p.x, p.y, 14, seed + 8) > 0.62)
    stamp(p, clover, 0.10, seed + 120, SMALL[:3], swap='cool')
    stamp(p, clover, 0.025, seed + 130, DOMINOES, ramp='plaster', tone=4, same_family=False)
    flowers(p, m, seed + 300, (('brass', 4, 1.0),), 0.0015)  # buttercups
    despeckle(p, m)
    if tussocks:
        damp = fbm(p.x, p.y, 30, seed + 9)
        for i, (cx, cy) in enumerate(_scatter(m, 700, seed + 11)):
            if damp[cy, cx] > 0.6:
                tussock(p, cx, cy, seed + i)
        for i, (cx, cy) in enumerate(_scatter(m, 900, seed + 13)):
            molehill(p, cx, cy, seed + i)


def _scatter(m, every, seed, margin=6):
    """Deterministic points over a mask, about one per `every` px, never on its edge."""
    m = erode(np.asarray(m, bool), margin)
    h, w = m.shape
    cell = max(4, int(math.sqrt(every)))
    pts = []
    for gy in range(0, h, cell):
        for gx in range(0, w, cell):
            x = gx + int(hash01(gx, gy, seed) * cell)
            y = gy + int(hash01(gx, gy, seed + 1) * cell)
            if x < w and y < h and m[y, x]:
                pts.append((x, y))
    return pts


def tussock(p: Plot, x, y, seed=0, ramp='leaf_cool'):
    """A rush tussock: a dark clump of upright blades, lit tips on the west, its own shade
    at the foot to the east."""
    w = 5 + int(hash01(x, y, seed) * 3)
    pts = []
    for i in range(w):
        hgt = 2 + int(3 * math.sin(math.pi * (i + 0.5) / w)) + (2 if (i + seed) % 2 else 0) \
            + int(hash01(x + i, y, seed + 1) * 2)
        for j in range(hgt):
            pts.append((x + i, y - j, i, j, hgt))
    for (px, py, i, j, hgt) in pts:
        if 0 <= px < p.w and 0 <= py < p.h:
            k = 1 if j == 0 else 2 if i > w * 0.6 else 3
            if j == hgt - 1 and i < w * 0.6:
                k = 4
            p.f[py, px], p.t[py, px] = IDX[ramp], k
    for i in range(1, w + 1):                                  # shade to the east
        if 0 <= y + 1 < p.h and 0 <= x + i < p.w:
            p.step(_pt(p, x + i, y + 1), -1)


def _pt(p, x, y):
    m = np.zeros((p.h, p.w), bool)
    if 0 <= x < p.w and 0 <= y < p.h:
        m[y, x] = True
    return m


def molehill(p: Plot, x, y, seed=0):
    """A molehill: a small mound of fresh earth, lit on its top left, shadow to the right."""
    rows = ((1, 3), (0, 5), (0, 5))
    for j, (x0, ln) in enumerate(rows):
        for i in range(x0, x0 + ln):
            px, py = x + i, y + j
            if 0 <= px < p.w and 0 <= py < p.h:
                k = 4 if j == 0 and i < 3 else 2 if j == 2 or i == x0 + ln - 1 else 3
                p.f[py, px], p.t[py, px] = IDX['earth_warm' if (i + j) % 3 else 'earth'], k
    for (dx, dy) in ((5, 1), (5, 2), (5, 3), (4, 3), (3, 3)):
        p.step(_pt(p, x + dx, y + dy), -2)


# --- running water --------------------------------------------------------------------------
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
    """Coordinates along a channel for every pixel near it: s (px along the flow from the
    first point), n (px across it, positive on the right bank looking downstream), k (the
    bend's curvature there, positive turning right) and `outer` (True on the outside of the
    bend, where the current cuts the bank)."""

    def __init__(self, p: Plot, pts, reach=60):
        c = spline(pts)
        d = np.gradient(c, axis=0)
        d /= np.maximum(1e-9, np.hypot(d[:, 0], d[:, 1]))[:, None]
        th = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
        k = np.gradient(th)
        win = 31
        ker = np.hanning(win) / np.hanning(win).sum()
        k = np.convolve(np.pad(k, win // 2, mode='edge'), ker, mode='valid')
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
        self.c, self.dir, self.kk = c, d, k
        rx, ry = p.x + 0.5 - c[idx, 0], p.y + 0.5 - c[idx, 1]
        self.s = idx.astype(np.float64)
        self.n = rx * (-d[idx, 1]) + ry * d[idx, 0]
        self.k = k[idx]
        self.tx, self.ty = d[idx, 0], d[idx, 1]
        self.outer = self.n * self.k < 0
        self.length = len(c)

    def bend(self, scale=0.013):
        """How strongly the channel bends here, 0 (a straight crossing) to 1 (a tight bend)."""
        return np.clip(np.abs(self.k) / scale, 0, 1)


def _bank_face(p: Plot, face, depth_row, hgt, seed, stone=False, east_facing=None):
    """A bank face: earth with an overhanging turf lip, clods lit on top, roots, stones and a
    dark wet foot (or, `stone`, coursed rubble with a coping, moss low down)."""
    if not face.any():
        return
    j = depth_row                      # rows down from the land's edge, 0 at the lip
    top = face & (j == 0)
    foot = face & (j >= hgt - 1)
    body = face & ~top & ~foot
    if stone:
        course = 5
        row = j // course
        off = (row % 2) * 6
        u = (p.x + off + (hash01(row, 0, seed) * 9).astype(int))
        brick = u // 11
        pick = hash01(brick, row, seed + 1)
        fam = np.where(pick < 0.3, IDX['stone_warm'], np.where(pick > 0.75, IDX['stone_cool'], IDX['stone']))
        k = np.full(face.shape, 3)
        rj = j % course
        k = np.where(rj == 0, 4, np.where(rj == course - 1, 2, k))
        k = np.where((u % 11) == 10, 1, k)                                  # head joints
        k = np.where((rj == 0) & ((u % 11) < 2), 5, k)                       # a glint on each stone
        p.f[face], p.t[face] = fam[face], k[face]
        joint = face & ((rj == course - 1) | ((u % 11) == 10))
        p.f[joint], p.t[joint] = IDX['stone_cool'], 1
        low = face & (j >= hgt - 3) & joint & (hash01(p.x // 2, j, seed + 2) < 0.6)
        p.f[low], p.t[low] = IDX['leaf'], 2                                  # moss in the low joints
        stain = face & ~joint & (j >= hgt - 2)
        p.step(stain, -1)                                                    # the wet tide line
        if east_facing is not None:
            p.step(face & east_facing, -1)
        return
    # earth: clods in rough courses, each lit along its top
    row = (j + (hash01(p.x // 5, 0, seed) * 3).astype(int)) // 3
    clod = (p.x + (hash01(row, 1, seed) * 7).astype(int)) // (4 + (hash01(row, 2, seed) * 3).astype(int))
    pick = hash01(clod, row, seed + 3)
    fam = np.where(pick < 0.35, IDX['earth_warm'], np.where(pick > 0.72, IDX['earth_cool'], IDX['earth']))
    k = np.where(hash01(clod, row, seed + 4) < 0.25, 2, 3)
    first = shift(row, 0, 1, -1) != row
    k = np.where(first, k + 1, k)
    last = shift(row, 0, -1, -1) != row
    k = np.where(last, k - 1, k)
    p.f[body], p.t[body] = fam[body], np.clip(k, 1, 4)[body]
    if east_facing is not None:
        p.step(body & east_facing, -1)
    # the turf lip: grass hanging over the edge in scallops, its underside dark
    p.f[top], p.t[top] = IDX['grass'], 3
    lit = top & (hash01(p.x // 2, 1, seed + 5) < 0.4)
    p.t[lit] = 4
    drip = face & (j == 1) & (hash01(p.x // 2, 0, seed + 5) < 0.55)
    p.f[drip], p.t[drip] = IDX['grass_cool'], 2
    drip2 = face & (j == 2) & shift(drip, 0, 1, False) & (hash01(p.x // 2, 2, seed + 5) < 0.4)
    p.f[drip2], p.t[drip2] = IDX['grass_cool'], 1
    # roots: thin pale threads hanging from the lip
    roots = body & (j < hgt - 1) & (hash01(p.x, 0, seed + 6) < 0.07) & (j <= 1 + (hash01(p.x, 1, seed) * 4).astype(int))
    p.f[roots], p.t[roots] = IDX['timber_warm'], 2
    # stones in the face, lit top left
    st = body & (hash01(p.x // 3, j // 2, seed + 7) < 0.05) & (j > 1)
    p.f[st], p.t[st] = IDX['stone'], 3
    stt = st & ~shift(st, 0, 1, False)
    p.t[stt] = 4
    p.f[foot], p.t[foot] = IDX['earth_cool'], 1


def river(p: Plot, pts, width=40, seed=3, ford_at=None, ford_width=28, stones_at=None, bar=True,
          high=9, low=1, kind='river'):
    """A river or stream along `pts` (downstream order), `width` px of water.

    Banks differ by side: on the outside of a bend the current cuts a bank `high` px above
    the water (its earth face shows where it faces the camera); on the inside it drops a
    sand and gravel point bar that shelves into the shallows (`low`). Pools lie deep under
    the cut banks, riffles where the channel runs straight between bends (broken water over
    stones). `ford_at` (px along the flow) lays a ford there: the banks shelve to the water
    and the bed shows through; `stones_at` sets a line of stepping stones across.
    Returns the Channel (for placing reeds, trees and the track)."""
    ch = Channel(p, pts, reach=width // 2 + 26)
    hw = width / 2
    bend = ch.bend()
    wob = (fbm(ch.s, 0 * ch.s, 7, seed) - 0.5) * 3 + (fbm(ch.s, 5 + 0 * ch.s, 3, seed + 1) - 0.5) * 1.5
    inner = ~ch.outer
    # the point bar narrows the water on the inside of each bend
    barw = np.where(inner, bend * hw * 0.55, 0) if bar else 0 * bend
    ford = np.zeros(p.f.shape, bool)
    if ford_at is not None:
        out = np.maximum(0, np.abs(ch.n) - hw)
        reach = ford_width / 2 + 3 * vnoise(ch.n, 0 * ch.n, 5, seed) - out * 0.55
        ford = ch.near & (np.abs(ch.s - ford_at) < reach)
        barw = np.where(ford, 0, barw)
    edge = hw + wob
    wet_plan = ch.near & (np.abs(ch.n) < edge - barw)
    # bank height: high on the cut bank, low by the bar, between on straight reaches
    hb = np.where(ch.outer, 2 + np.round((high - 2) * bend), np.where(bend > 0.25, low, 3)).astype(int)
    hb = np.where(ford, 0, hb)
    # the point bar itself: sand and gravel from the water up onto the land
    barm = ch.near & inner & ~wet_plan & (np.abs(ch.n) < edge + 2 + barw * 0.35) & (barw > 1.5)
    # what the camera sees: land at its own place, water `hb` lower (so drawn hb px further
    # down); between the two on a north bank, the bank's face
    rows = np.arange(p.h)[:, None]
    src = np.clip(rows - hb, 0, p.h - 1)
    wet_src = np.take_along_axis(wet_plan, src, axis=0)
    water = wet_plan & wet_src
    face = wet_plan & ~wet_src
    # side faces on a west or east bank: a narrow band, dark facing east, lit facing west
    side_w = np.where(hb >= 3, 2, 0)
    land = ~wet_plan
    west_land = np.zeros_like(land)
    east_land = np.zeros_like(land)
    for dx in (1, 2):
        west_land |= shift(land, dx, 0, False) & (side_w >= dx)
        east_land |= shift(land, -dx, 0, False) & (side_w >= dx)
    side = water & (west_land | east_land) & ch.near
    face |= side
    water &= ~side
    # depth in the face: rows down from the land above
    j = np.zeros(p.f.shape, int)
    run = np.zeros(p.w, int)
    for y in range(p.h):
        run = np.where(face[y], run + 1, 0)
        j[y] = run - 1
    j = np.where(side & ~(wet_plan & ~wet_src), np.minimum(j, 1), j)
    # land first: grass stays, the bar is sand and gravel
    if barm.any():
        sand(p, barm, ch, seed + 10)
    _bank_face(p, face, j, np.maximum(hb, 2), seed + 20, east_facing=west_land & side)
    _water(p, water, ch, hw, seed + 30, ford=ford, kind=kind)
    # the near (south) bank: a lip with the water dark beneath it
    lip = land & shift(water, 0, 1, False) & ~barm
    p.step(lip & ~ford, -1)
    under = water & shift(land & ~barm, 0, -1, False) & ~ford
    p.step(under | (water & shift(under, 0, -1, False)), -1, lo=1)
    # where the water meets the bar and the ford: a wet margin, a darker band of sand
    wetsand = (barm | (ford & land)) & dilate(water, 2)
    p.step(wetsand & (p.fam('sand') | p.fam('stone')), -1, lo=1)
    if ford.any():
        ford_bed(p, ford & ~water & ch.near, ch, seed + 40)
        # the water over the ford: shallowest where the bed is trodden, deepening into the
        # reach on either side through a soft band, gravel showing through, and the water
        # breaking in a broken lit line where it spills off the ford's downstream lip
        fw = water & ch.near & (np.abs(ch.s - ford_at) < ford_width / 2 + 10)
        dfs = np.abs(ch.s - ford_at) / (ford_width / 2) + 0.7 * (fbm(p.x, p.y, 7, seed + 41) - 0.5)
        fam = np.where(hash01(p.x // 2, p.y // 2, seed + 42) < 0.5, IDX['water_warm'], IDX['water'])
        p.f[fw & (dfs < 1.15)] = fam[fw & (dfs < 1.15)]
        p.t[fw & (dfs < 0.75)] = 4
        p.t[fw & (dfs >= 0.75) & (dfs < 1.15)] = 3
        bed = fw & (dfs < 0.85)
        stamp(p, bed, 0.06, seed + 43, DOMINOES + (((0, 0), (1, 0), (1, 1)),), ramp='water_cool', tone=3,
              same_family=False)
        stamp(p, bed, 0.03, seed + 44, DOMINOES, ramp='water_warm', tone=5, same_family=False)
        lip = fw & (dfs > 0.9) & (dfs < 1.05) & (ch.s > ford_at) & \
            (hash01(p.x // 2, p.y // 2, seed + 45) < 0.6)
        p.f[lip], p.t[lip] = IDX['water_warm'], 5
    p.wet |= water
    p.walk &= ~(water & ~ford)
    p.crossing |= water & ford
    if stones_at is not None:
        stepping_stones(p, ch, stones_at, hw, seed + 50)
    riffles(p, ch, water & ~ford, hw, seed + 60)
    despeckle(p, ch.near)
    ch.water, ch.face, ch.bar, ch.hb, ch.ford, ch.edge = water, face, barm, hb, ford, edge
    return ch


def _water(p: Plot, m, ch: Channel, hw, seed, ford=None, kind='river'):
    """The water surface: depth in soft bands lying with the flow (deep under the cut bank,
    shallow over the bar and the riffles), sibling patches stretched downstream, the current
    as 3 to 5 px lit streaks over their own shadow, glints in pairs."""
    bend = ch.bend()
    dn = np.clip(ch.n / max(1, hw), -1.2, 1.2)
    c0 = -np.sign(ch.k) * 0.55 * bend                         # the thalweg leans outward
    depth = 1 - ((dn - c0) / (1 + np.abs(c0))) ** 2
    depth = depth * (0.55 + 0.45 * bend) + 0.12 * (fbm(ch.s, ch.n * 3, 10, seed) - 0.5)
    tone = np.where(depth > 0.78, 1, np.where(depth > 0.42, 2, np.where(depth > 0.14, 3, 4)))
    sibn = fbm(ch.s / 3.0, ch.n * 1.2, 6, seed + 1)
    fam = np.where(sibn < 0.33, IDX['water_warm'], np.where(sibn > 0.68, IDX['water_cool'], IDX['water']))
    p.f[m], p.t[m] = fam[m], tone[m]
    # current streaks along the flow: lanes 3 px apart, segments 3 to 5 px
    lane = np.floor((ch.n + 100) / 3).astype(int)
    on = hash01(lane, 0, seed + 2) < 0.55
    per = 22 + (hash01(lane, 1, seed + 3) * 14).astype(int)
    pos = (ch.s.astype(int) + (hash01(lane, 2, seed + 4) * 40).astype(int)) % per
    ln = 3 + (hash01(lane, 3, seed + 5) * 3).astype(int)
    centre = np.abs(ch.n - (lane * 3 - 100 + 1.5)) < 0.75
    streak = m & on & centre & (pos < ln) & (tone <= 3)
    shadow = shift(streak, 0, 1, False) & m & ~streak
    p.step(shadow, -1, lo=1)
    p.step(streak, 1)
    head = streak & (pos == 0)
    p.step(head & (tone <= 2), 1)
    # glints in pairs on the calmer water
    g = m & (hash01(p.x // 2, p.y, seed + 6) < 0.012) & (tone <= 2) & ~streak & ~shadow
    gg = g | (shift(g, 1, 0, False) & m)
    p.f[gg], p.t[gg] = IDX['water_warm'], 4
    despeckle(p, m)


def sand(p: Plot, m, ch: Channel | None, seed):
    """A sand and gravel bar: pale sand in calm patches, ripple marks with the flow, gravel
    as small stones each lit on its top left with a shadow pair, the odd stick of driftwood."""
    base(p, m, 'sand', seed, scale=5, light=0.72, dark=0.30)
    if ch is not None:
        rip = m & ((np.floor(ch.n * 1.0 + 0.25 * ch.s) % 5) == 0) & (fbm(p.x, p.y, 9, seed + 3) > 0.45)
        p.step(rip & ~shift(rip, 1, 0, False), 1)
    texture(p, m, seed + 5, swaps=0.10, ups=0.03, downs=0.02)
    pebbles(p, m & (fbm(p.x, p.y, 12, seed + 6) > 0.4), seed + 7, 0.035)


def pebbles(p: Plot, m, seed, density=0.03, ramp='stone'):
    """Small stones: a lit top row (tone 4, its left pixel 5 on the bigger ones), a body,
    and two tones of the ground's own shade at the lower right."""
    seeds = m & (hash01(p.x, p.y, seed) < density)
    seeds &= ~dilate(shift(seeds, 1, 1, False) | shift(seeds, -1, 1, False) | shift(seeds, 0, 1, False)
                     | shift(seeds, 1, 0, False), 1)
    big = seeds & (hash01(p.x, p.y, seed + 2) < 0.35)
    pick = hash01(p.x, p.y, seed + 3)
    fam = np.where(pick < 0.3, IDX[f'{ramp}_warm'], np.where(pick > 0.7, IDX[f'{ramp}_cool'], IDX[ramp]))
    for (dx, dy, k, need_big) in ((0, 0, 4, False), (1, 0, 4, False), (2, 0, 3, True), (0, 1, 2, False),
                                  (1, 1, 2, False), (2, 1, 2, True)):
        src = big if need_big else seeds
        tgt = shift(src, dx, dy, False) & m
        ff = shift(fam, dx, dy, 0)
        p.f[tgt], p.t[tgt] = ff[tgt], k
    gl = shift(big, 0, 0, False) & m
    p.t[gl] = 5
    sh = (shift(seeds, 2, 1, False) & ~shift(big, 2, 1, False)) | shift(big, 3, 1, False)
    sh &= m
    p.step(sh & (p.t < 4), -2, lo=0)


def ford_bed(p: Plot, m, ch, seed):
    """The ford's shelving banks: trodden gravel down to the water, cart ruts into it."""
    base(p, m, 'path', seed, scale=5)
    texture(p, m, seed + 1, swaps=0.10, ups=0.02, downs=0.02)
    pebbles(p, m, seed + 2, 0.03)


def stepping_stones(p: Plot, ch: Channel, at, hw, seed, gap=11):
    """Stones across the water a stride apart (size guide: 6 to 10 wide, 8 to 12 apart),
    each a flat-topped block lit on its top left, wet and dark in its lower half, a curl of
    foam on its upstream side and a dark wake below it."""
    i = int(np.clip(at, 0, ch.length - 1))
    cx, cy = ch.c[i]
    tx, ty = ch.dir[i]
    nx, ny = -ty, tx
    span = int(hw + 6)
    for o in range(-span, span + 1, gap):
        sx = int(round(cx + nx * o + tx * (hash01(o, 0, seed) - 0.5) * 3))
        sy = int(round(cy + ny * o + ty * (hash01(o, 1, seed) - 0.5) * 3))
        w = 8 + int(hash01(o, 2, seed) * 3)
        h = 6
        x0, y0 = sx - w // 2, sy - h // 2
        if not (0 <= x0 and x0 + w < p.w and 0 <= y0 - 1 and y0 + h + 2 < p.h):
            continue
        if not p.wet[sy, sx]:
            continue
        pick = 'stone' if hash01(o, 3, seed) < 0.5 else 'stone_warm'
        for yy in range(h):
            for xx in range(w):
                if (yy in (0, h - 1)) and (xx in (0, w - 1)):
                    continue
                k = 4 if yy == 0 else 3 if yy < 2 else 2 if yy < h - 1 else 1
                if yy == 0 and xx in (1, 2):
                    k = 5
                if xx == w - 1 and 0 < yy:
                    k = max(1, k - 1)
                p.f[y0 + yy, x0 + xx], p.t[y0 + yy, x0 + xx] = IDX[pick], k
                p.wet[y0 + yy, x0 + xx] = False
                p.walk[y0 + yy, x0 + xx] = True        # stepping stones are a declared crossing
                p.crossing[y0 + yy, x0 + xx] = True
        # the stone's edge tone under it (it stands in the water) and its wake
        for xx in range(1, w - 1):
            p.f[y0 + h, x0 + xx], p.t[y0 + h, x0 + xx] = IDX['stone'], EDGE_T
            p.f[y0 + h + 1, x0 + xx + 1], p.t[y0 + h + 1, x0 + xx + 1] = IDX['water_cool'], 1
        # foam on the upstream side (the current comes from -t)
        fx, fy = int(round(sx - tx * (w / 2 + 1))), int(round(sy - ty * 3))
        for dx in (0, 1):
            if 0 <= fx + dx < p.w and 0 <= fy < p.h and p.wet[fy, fx + dx]:
                p.f[fy, fx + dx], p.t[fy, fx + dx] = IDX['water_warm'], 5


def riffles(p: Plot, ch: Channel, m, hw, seed):
    """Riffles where the channel runs straight between bends: stones just breaking the
    surface, each with a lit cap and a foam chevron downstream, and broken lighter water."""
    straight = m & (ch.bend() < 0.3) & (np.abs(ch.n) < hw * 0.8)
    if not straight.any():
        return
    broken = straight & (fbm(ch.s / 2, ch.n, 5, seed) > 0.55)
    p.step(broken & (p.t <= 3), 1)
    pts = _scatter(straight, 110, seed + 1, margin=3)
    for i, (x, y) in enumerate(pts):
        if hash01(x, y, seed + 2) < 0.5:
            continue
        for dx, dy, k in ((0, 0, 4), (1, 0, 3), (0, 1, 2), (1, 1, 1)):
            if 0 <= x + dx < p.w and 0 <= y + dy < p.h:
                p.f[y + dy, x + dx], p.t[y + dy, x + dx] = IDX['stone_cool'], k
        tx, ty = ch.tx[y, x], ch.ty[y, x]
        for o in (2, 3):
            for side in (-1, 1):
                qx = int(round(x + tx * o - ty * side * (o - 1)))
                qy = int(round(y + ty * o + tx * side * (o - 1)))
                if 0 <= qx < p.w and 0 <= qy < p.h and m[qy, qx]:
                    p.f[qy, qx], p.t[qy, qx] = IDX['water_warm'], 5 if o == 2 else 4


# --- farmland -------------------------------------------------------------------------------
def _edge_dist(m, cap=12):
    """Px from each masked pixel to the mask's edge (0 on the edge), capped."""
    d = np.zeros(m.shape, int)
    cur = m.copy()
    for i in range(cap):
        cur = erode(cur, 1)
        d[cur] = i + 1
        if not cur.any():
            break
    return d


def plough(p: Plot, m, height, seed=4, spacing=5, headland=8):
    """A ploughed field: ridges and furrows along the contours of `height` (an array, px),
    each ridge lit on its top and its side to the light, the furrow dark; clods along the
    ridges; a headland strip round the edge where the plough turned, its furrows following
    the field's edge."""
    m = np.asarray(m, bool)
    base(p, m, 'earth', seed, scale=8, light=0.75, dark=0.25)
    d = _edge_dist(m, headland + 2)
    c = np.where(d <= headland, d * spacing / 4.0, height)
    ph = np.floor(c).astype(int) % spacing
    clod = (p.x // 4 + (np.floor(c) // spacing).astype(int) * 7)
    fam = np.where(hash01(clod, 0, seed) < 0.3, IDX['earth_warm'],
                   np.where(hash01(clod, 1, seed) > 0.7, IDX['earth_cool'], IDX['earth']))
    k = np.select([ph == 0, ph == 1, ph == spacing - 2, ph == spacing - 1], [4, 3, 2, 1], 3)
    p.f[m], p.t[m] = fam[m], k[m]
    p.step(m & (fbm(p.x, p.y, 20, seed + 3) > 0.68) & (p.t <= 3), 1)    # drier ground
    stamp(p, m & (k >= 3), 0.07, seed + 5, SMALL, swap='mix')
    stamp(p, m & (k == 3), 0.03, seed + 6, SMALL[:3], dt=1)
    pebbles(p, m & (hash01(p.x // 16, p.y // 16, seed) < 0.3), seed + 7, 0.004)
    despeckle(p, m)


def crop(p: Plot, m, height, seed=5, kind='wheat', spacing=5):
    """A crop in rows along the contours. 'wheat' ripe and gold: rows of ears lit on top,
    the shade between rows, ear clusters, tramlines where the sprayer runs, and along the
    field's south edge the stalks' own face, 3 px tall. 'young': green shoots in rows on
    bare earth."""
    m = np.asarray(m, bool)
    ph = np.floor(height).astype(int) % spacing
    row = np.floor(height).astype(int) // spacing
    if kind == 'young':
        base(p, m, 'earth', seed, scale=8)
        rows = m & (ph <= 1)
        p.f[rows] = np.where(hash01(p.x // 3, row, seed) < 0.5, IDX['grass'], IDX['grass_warm'])[rows]
        p.t[rows] = np.where(ph == 0, 4, 3)[rows]
        gap = m & (ph == spacing - 1)
        p.step(gap, -1)
        stamp(p, rows, 0.12, seed + 3, SMALL[:3], swap='mix')
        despeckle(p, m)
        return
    base(p, m, 'sand', seed, scale=10, warm=0.45, cool=0.85)
    k = np.select([ph == 0, ph == 1, ph == spacing - 1], [4, 3, 2], 3)
    p.t[m] = k[m]
    p.step(m & (fbm(p.x, p.y, 16, seed + 2) < 0.3), -1)                # wind-laid patches
    ears = m & (ph >= 1) & (ph <= spacing - 2)
    stamp(p, ears, 0.07, seed + 3, DOMINOES[1:] + (((0, 0), (0, -1), (1, -1)),), ramp='brass',
          tone=4, same_family=False)
    stamp(p, ears, 0.03, seed + 13, DOMINOES[1:], ramp='brass_warm', tone=5, same_family=False)
    stamp(p, ears, 0.08, seed + 4, SMALL[:3], swap='mix')
    stamp(p, m & (k == 2), 0.06, seed + 14, DOMINOES, ramp='timber_warm', tone=3, same_family=False)
    flowers(p, m & (fbm(p.x, p.y, 25, seed + 15) > 0.6), seed + 16, (('berry', 4, 1.0),), 0.006)
    tram = m & ((row % 11) == 3) & (ph >= 1) & (ph <= 2)
    tram &= ph == 1
    p.f[tram], p.t[tram] = np.where(hash01(p.x // 3, p.y, seed + 5) < 0.3, IDX['sand_cool'], IDX['earth_warm'])[tram], 3
    weeds = tram & (hash01(p.x // 2, p.y, seed + 6) < 0.25)
    p.f[weeds], p.t[weeds] = IDX['grass'], 3
    # the stalks' face along the south edge: what you see of a crop from beside it
    face = m & ~shift(m, 0, -3, False) & shift(m, 0, 1, False)
    stalk = face & ((p.x % 2) == 0)
    p.f[face], p.t[face] = IDX['sand_cool'], 2
    p.f[stalk], p.t[stalk] = IDX['sand'], 3
    foot = m & ~shift(m, 0, -1, False)
    p.f[foot], p.t[foot] = IDX['sand_cool'], 1
    despeckle(p, m)


def margin(p: Plot, m, seed=6):
    """An uncut field margin: tall grass and the arable flowers of a field's edge
    (poppies, cornflowers, mayweed), thicker towards the hedge."""
    hay_meadow(p, m, seed)
    flowers(p, m, seed + 70, (('berry', 4, 0.45), ('sky', 4, 0.25), ('plaster', 5, 0.3)), 0.014)
    despeckle(p, m)


def track(p: Plot, pts, width=24, seed=7, puddles=2, ch=None):
    """A farm track (size guide: 24, two worn ruts): bare trodden earth between grassy
    verges, two ruts a cart's gauge apart (each with its shaded north wall and lit south
    lip, stones in its floor), a grass crown between them, and puddles in the low ruts
    with the sky in them. Returns its Channel."""
    ch = ch or Channel(p, pts, reach=width // 2 + 8)
    hw = width / 2
    wob = (fbm(ch.s, 0 * ch.s, 9, seed) - 0.5) * 3
    m = ch.near & (np.abs(ch.n) < hw + wob)
    under_water = m & p.wet
    m &= ~p.wet
    base(p, m, 'path', seed, scale=6)
    texture(p, m, seed + 1, swaps=0.10, ups=0.02, downs=0.03)
    gauge = 6.5
    rut = m & (np.abs(np.abs(ch.n) - gauge) < 2.0 + 0.6 * vnoise(ch.s, ch.n, 4, seed))
    p.f[rut] = np.where(hash01(p.x // 3, p.y // 2, seed + 2) < 0.5, IDX['path_cool'], IDX['path'])[rut]
    p.t[rut] = np.where(fbm(p.x, p.y, 4, seed + 11) > 0.6, 3, 2)[rut]
    north = rut & ~shift(rut, 0, 1, False)
    p.t[north] = 1
    south = m & ~rut & shift(rut, 0, 1, False)
    p.step(south, 1)
    crown = m & (np.abs(ch.n) < 2.6 + 1.2 * vnoise(ch.s, 0 * ch.s, 7, seed + 3)) & ~rut
    p.f[crown] = np.where(hash01(p.x // 2, p.y, seed + 4) < 0.4, IDX['grass_cool'], IDX['grass'])[crown]
    p.t[crown] = np.where(fbm(p.x, p.y, 5, seed + 5) > 0.55, 3, 2)[crown]
    stamp(p, crown, 0.15, seed + 6, BLADES, dt=1)
    # the verges: grass creeping onto the track's edges in tongues
    verge = m & (np.abs(ch.n) > hw - 1.5 + 2.5 * (vnoise(ch.s, ch.n, 3, seed + 7) - 0.3))
    p.f[verge] = IDX['grass']
    p.t[verge] = 3
    stamp(p, verge, 0.12, seed + 8, BLADES, dt=1)
    pebbles(p, rut, seed + 9, 0.02)
    for i in range(puddles):
        si = int(ch.length * (0.25 + 0.5 * hash01(i, 0, seed + 10)))
        side = 1 if hash01(i, 1, seed) < 0.5 else -1
        pm = ch.near & (np.abs(ch.s - si) < 5 + 3 * hash01(i, 2, seed)) & (np.abs(ch.n - side * gauge) < 2.2)
        puddle(p, pm & m, seed + 20 + i)
    despeckle(p, m)
    # where the track runs through a declared crossing (a ford's shallows), its ruts show as
    # darker lanes in the water and the way stays open; anywhere else the water keeps
    # blocking: painting a track never makes a crossing by itself
    ford_water = under_water & p.crossing
    wr = ford_water & (np.abs(np.abs(ch.n) - gauge) < 2.0)
    p.step(wr, -1, lo=2)
    p.walk |= m | ford_water
    ch.mask = m | ford_water
    return ch


def puddle(p: Plot, m, seed=0):
    """Standing water in a rut: the sky in it (light at the far, north edge), a dark rim
    where it meets the earth to the north, a lit wet lip to the south."""
    if not m.any():
        return
    p.f[m], p.t[m] = IDX['sky'], 4
    p.t[m & shift(m, 0, -2, False) & ~shift(m, 0, 2, False)] = 3
    rim = m & ~shift(m, 0, 1, False)
    p.f[rim], p.t[rim] = IDX['path_cool'], 1
    g = m & ~rim & (hash01(p.x // 2, p.y, seed) < 0.15)
    p.f[g], p.t[g] = IDX['sky'], 5
    p.wet |= m & ~rim
    p.crossing |= m          # a puddle is walked through


def hedgerow(p: Plot, pts, height=16, depth=10, seed=8, gaps=(), gate_at=None, gate_width=40):
    """A hedgerow along `pts` (size guide: 14 to 20 tall, 8 to 16 deep): a row of mixed
    shrubs (hawthorn, blackthorn, hazel, field maple, in runs of one kind as a hedge is
    planted and gapped up), each a crown of leaf clumps lit from the upper left, overlapping
    so the near ones stand in front; a bumpy top, a face that falls into shade at the foot,
    dog roses and elder flowers, long grass and cow parsley along the foot, its shadow down
    and to the right. `gaps` (px along it) are worn gaps a walker uses; `gate_at` sets a
    five-bar gate between two posts."""
    ch = Channel(p, pts, reach=depth + 4)
    hd = depth / 2
    gap = np.zeros(p.f.shape, bool)
    for g in gaps:
        gap |= np.abs(ch.s - g) < 7 + 2 * vnoise(ch.n, 0 * ch.n, 4, seed)
    if gate_at is not None:
        gap |= np.abs(ch.s - gate_at) < gate_width / 2 + 1
    foot = ch.near & (np.abs(ch.n) < hd + 1.2 * (vnoise(ch.s, ch.n, 5, seed) - 0.5)) & ~gap
    # raised: the top surface is the footprint lifted by the hedge's height (bumpy, one
    # shrub to the next), the face hangs from it to the foot
    H = (height + 3 * (fbm(ch.s, 0 * ch.s, 13, seed + 2) - 0.5)).astype(int)
    body = foot.copy()
    for z in range(1, height + 3):
        body |= shift(foot & (H >= z), 0, -z, False)
    # a crown of shrubs: clumps over the whole body, and over its top edge, so the skyline
    # is a run of bumps
    inside, du, dv, cid = clumps(p, np.ones(p.f.shape, bool), 5, 2.4, 4.0, seed + 3)
    skyline = dilate(body, 2) & ~body & shift(dilate(body, 0), 0, 3, False)
    body |= skyline & inside & (hash01(cid, 5, seed) < 0.75)
    body = erode(dilate(body, 1), 1) & ~shift(gap & ~dilate(foot, 1), 0, 0, False)
    hgt = np.zeros(p.f.shape, int)
    run = np.zeros(p.w, int)
    for y in range(p.h - 1, -1, -1):
        run = np.where(body[y], run + 1, 0)
        hgt[y] = run
    depth_from_top = np.zeros(p.f.shape, int)
    run = np.zeros(p.w, int)
    for y in range(p.h):
        run = np.where(body[y], run + 1, 0)
        depth_from_top[y] = run
    species = np.floor((ch.s + 40 * hash01(0, 0, seed)) / 30).astype(int)
    pick = hash01(species, 0, seed + 3)
    fam = np.where(pick < 0.3, IDX['leaf_cool'], np.where(pick < 0.55, IDX['leaf_warm'],
                   np.where(pick < 0.68, IDX['grass_cool'], IDX['leaf'])))
    sib_pick = hash01(cid, 1, seed)
    fam = np.where(sib_pick < 0.25, WARM[fam], np.where(sib_pick > 0.8, COOL[fam], fam))
    # light: the top lit, the face falling into shade towards the foot; each clump lit on
    # its own top left and dark at its lower right; the gaps between clumps deep
    top = depth_from_top <= depth
    k = np.where(top, 3, np.where(hgt > height * 0.55, 3, np.where(hgt > 4, 2, 1)))
    lv = -du - dv
    k = np.where(inside & (lv > 0.6), k + 1, np.where(inside & (lv < -0.7), k - 1, k))
    k = np.where(~inside, k - 1, k)
    k = np.where(inside & (lv > 1.0) & top, 5, k)
    p.f[body], p.t[body] = fam[body], np.clip(k, 1, 5)[body]
    sh = shift(body, 4, 3, False) & ~body
    cast(p, sh & ~p.solid & ~p.wet)
    # flowers: dog rose and elder, in clusters of two on lit clumps
    ros = body & inside & (lv > 0.3) & (hash01(species, 1, seed) < 0.5) & (hash01(cid, 2, seed) < 0.08) & \
        (np.abs(du + 0.2) < 0.5) & (np.abs(dv + 0.1) < 0.35)
    p.f[ros], p.t[ros] = IDX['berry_warm'], 4
    eld = body & inside & (hash01(species, 2, seed) < 0.4) & (hash01(cid, 3, seed) < 0.07) & \
        (np.abs(du) < 0.55) & (np.abs(dv + 0.2) < 0.3)
    p.f[eld], p.t[eld] = IDX['plaster'], 4
    despeckle(p, body)
    outline_mask(p, body, seed)
    p.solid |= body
    p.walk &= ~foot                  # a walker is stopped by the footprint, not the drawn height
    species_map = np.floor(p.x / 30).astype(int)
    # long grass along the foot where the hedge meets the field
    fringe = ~body & dilate(body, 3) & shift(dilate(body, 3), 0, -3, False) & ~p.wet & ~p.solid
    stamp(p, fringe, 0.2, seed + 9, BLADES, dt=1, same_family=False)
    parsley = fringe & (hash01(species_map, 3, seed) < 0.5)
    stamp(p, parsley, 0.03, seed + 10, (((0, 0), (1, 0), (2, 0)),), ramp='plaster', tone=4, same_family=False)
    if gate_at is not None:
        i = int(np.clip(gate_at, 0, ch.length - 1))
        gx, gy = ch.c[i]
        gate(p, int(gx - gate_width / 2), int(gy + hd * 0.6), gate_width, seed + 11)
    ch.body, ch.foot = body, ch.near & (np.abs(ch.n) < hd)
    return ch


def outline_mask(p: Plot, m, seed=0):
    """The house outline round a standing mass: one pixel outside it in the edge tone of the
    family it closes; on its lit top and west edges the line breaks to that ramp's tone 1."""
    ring = dilate(m, 1) & ~m
    # (dx, dy): the side of the mass the ring pixel lies on; west and top are lit
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


def cast(p: Plot, m, k=2):
    """A cast shadow: the ground steps k tones down its own ramp (house rule 6)."""
    p.step(np.asarray(m, bool), -k, lo=0)


def gate(p: Plot, x0, yfoot, width=40, seed=0, ramp='timber'):
    """A five-bar field gate (size guide: 32 to 48 wide between heavier posts, 12 to 22
    tall): two square posts lit on the west, the hanging stile, five rails lit on top,
    the brace rising from the hinge foot, a latch; shadows thrown down and to the right."""
    H = 20
    m = np.zeros(p.f.shape, bool)
    t = np.zeros(p.f.shape, np.int8)
    f = np.full(p.f.shape, IDX[ramp], np.int16)

    def put(x, y, k, fam=ramp):
        if 0 <= x < p.w and 0 <= y < p.h:
            m[y, x] = True
            t[y, x] = k
            f[y, x] = IDX[fam]
    # posts: 4 px square, a weathered top
    for px in (x0, x0 + width - 4):
        for y in range(yfoot - H - 3, yfoot + 1):
            for dx in range(4):
                k = 4 if dx == 0 else 3 if dx < 2 else 2 if dx == 2 else 1
                if y == yfoot - H - 3:
                    k = 4
                put(px + dx, y, k, 'timber_cool' if dx == 3 else ramp)
    # rails: five, 2 px deep (top rail 3), lit on top
    gx0, gx1 = x0 + 4, x0 + width - 4
    rails = (yfoot - H, yfoot - H + 5, yfoot - H + 9, yfoot - H + 13, yfoot - H + 17)
    for i, ry in enumerate(rails):
        th = 3 if i == 0 else 2
        for x in range(gx0, gx1):
            for dy in range(th):
                put(x, ry + dy, 4 if dy == 0 else 2, 'timber_warm' if (x // 9 + i) % 3 == 0 else ramp)
    # the hanging stile and the head stile
    for sx in (gx0, gx0 + 1, gx1 - 2, gx1 - 1):
        for y in range(rails[0], rails[-1] + 2):
            put(sx, y, 3 if sx in (gx0, gx1 - 2) else 2)
    # the brace: from the hinge foot to the top rail two thirds along
    bx1 = gx0 + (gx1 - gx0) * 2 // 3
    for y in range(rails[0] + 2, rails[-1] + 1):
        fy = (y - rails[0] - 2) / max(1, rails[-1] - rails[0] - 2)
        x = int(round(bx1 + (gx0 + 2 - bx1) * fy))
        put(x, y, 3)
        put(x + 1, y, 2)
    # the latch: an iron hook on the head post
    put(gx1, rails[1] + 1, 3, 'iron')
    put(gx1 + 1, rails[1] + 1, 2, 'iron')
    p.f[m], p.t[m] = f[m], t[m]
    outline_mask(p, m)
    sh = shift(m, 3, 3, False) & ~m & ~dilate(m, 0)
    sh &= ~p.solid
    cast(p, sh)
    posts = np.zeros_like(m)
    posts[max(0, yfoot - 3):yfoot + 1, max(0, x0):x0 + 4] = True
    posts[max(0, yfoot - 3):yfoot + 1, max(0, x0 + width - 4):x0 + width] = True
    p.solid |= m
    p.walk &= ~(posts | (m & ~shift(m, 0, 0, False)))


# --- standing things: trees, shrubs and plants ----------------------------------------------
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

    def step(self, sel, k, lo=0, hi=5):
        sel = np.asarray(sel, bool) & self.m
        self.t[sel] = np.clip(self.t[sel] + k, lo, hi)


def paste(p: Plot, sp: Sprite, x, y, outline=True, shadow=None, block=None):
    """Set a sprite with its foot at (x, y) on the plot: its cast shadow first (stepping the
    ground two tones down), then the sprite, then its outline in edge tones. `shadow` is a
    mask in the sprite's own pixels (default: none); `block` the pixels (sprite's own) that
    stop a walker (default: a 4 x 3 foot)."""
    ox, oy = x - sp.fx, y - sp.fy
    full = np.zeros(p.f.shape, bool)
    ff = np.zeros(p.f.shape, np.int16)
    tt = np.zeros(p.f.shape, np.int8)
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(sp.w, p.w - ox), min(sp.h, p.h - oy)
    if sx0 >= sx1 or sy0 >= sy1:
        return full
    sl = (slice(oy + sy0, oy + sy1), slice(ox + sx0, ox + sx1))
    ssl = (slice(sy0, sy1), slice(sx0, sx1))
    if shadow is not None:
        sh = np.zeros(p.f.shape, bool)
        sh[sl] = shadow[ssl]
        cast(p, sh & ~p.solid & ~p.wet)
        p.step(sh & p.wet, -1, lo=1)
    full[sl] = sp.m[ssl]
    ff[sl], tt[sl] = sp.f[ssl], sp.t[ssl]
    p.f[full], p.t[full] = ff[full], tt[full]
    if outline:
        outline_mask(p, full)
    p.solid |= full
    if block is None:
        b = np.zeros(p.f.shape, bool)
        b[max(0, y - 2):y + 1, max(0, x - 2):x + 2] = True
    else:
        b = np.zeros(p.f.shape, bool)
        b[sl] = block[ssl]
    p.walk &= ~b
    return full


def crown(sp: Sprite, cx, cy, rx, ry, seed=0, ramp='leaf', hang=0.0, clump=2.6, rim=True, wob=0.12,
          lobes=7):
    """A crown of leaf clumps (house foliage recipe): four light bands lit from the upper
    left, clumps one tone above their band with a light cap and a dark U under each, clumps
    from all three siblings, a yellow-green rim on the lit edge, the deep band quiet.
    `hang` (0..1) draws hanging foliage instead (a willow): clumps drawn out downward into
    strands and a curtain below the crown."""
    u, v = (sp.x + 0.5 - cx) / rx, (sp.y + 0.5 - cy) / ry
    ang = np.arctan2(v, u)
    r = 1 + wob * np.sin(ang * lobes + seed) + 0.05 * np.sin(ang * 13 + seed * 2)
    shape = u * u + v * v <= r * r
    if hang:
        strands = (np.abs(u) < 0.95) & (v > 0) & (v < 1 + hang * (0.9 + 0.5 * hash01(sp.x // 2, 0, seed + 9)))
        strands &= hash01(sp.x // 2, 1, seed + 8) < 0.8
        shape |= strands
    lv = -0.6 * u - 0.75 * v + 0.25 * np.sqrt(np.maximum(0, 1 - np.minimum(1, u * u + v * v)))
    band = np.where(lv > 0.5, 4, np.where(lv > 0.05, 3, np.where(lv > -0.45, 2, 1)))
    sp.put(shape, ramp, band)
    cl = np.zeros(sp.m.shape, bool)
    step_x, step_y = (clump * 2.4, clump * 1.6) if not hang else (clump * 1.6, clump * 2.4)
    yy = cy - ry + 2
    row = 0
    centres = []
    while yy < cy + ry * (1 + hang * 1.6):
        xx = cx - rx + (step_x / 2 if row % 2 else 0.6)
        while xx < cx + rx:
            jx = (hash01(int(xx * 3), int(yy * 3), seed) - 0.5) * 1.4
            centres.append((xx + jx, yy))
            xx += step_x
        yy += step_y
        row += 1
    for (ccx, ccy) in sorted(centres, key=lambda c: c[1]):
        ix, iy = int(ccx), int(ccy)
        if not (0 <= ix < sp.w and 0 <= iy < sp.h) or not shape[iy, ix]:
            continue
        b = band[iy, ix]
        if b <= 1:
            continue
        if hang:
            pts = shape & (np.abs(sp.x + 0.5 - ccx) < clump * 0.6) & (sp.y + 0.5 - ccy > -clump) & \
                (sp.y + 0.5 - ccy < clump * 2.2)
        else:
            pts = shape & ((sp.x + 0.5 - ccx) ** 2 + (sp.y + 0.5 - ccy) ** 2 <= clump * clump)
        nm = hash01(ix * 7, iy * 7, seed + 5)
        fam0 = hp.family(ramp)
        rp = f'{fam0}_warm' if nm < 0.3 else f'{fam0}_cool' if nm > 0.7 else ramp
        sp.put(pts, rp, min(5, b + 1) if b < 4 else 4)
        dy = sp.y + 0.5 - ccy
        low = pts & ~shift(pts, 0, -1, False) & (dy > 0)
        sp.put(low, rp, b - 1)
        capm = pts & (~shift(pts, 1, 0, False) | ~shift(pts, 0, 1, False)) & (sp.x + 0.5 < ccx) & (dy < 0.3) & (b >= 3)
        sp.put(capm, rp, 5 if b == 4 else b + 2)
        cl |= pts
    # small sibling clusters inside the clumps: more leaves, no more contrast
    fam0 = hp.family(ramp)
    sw = shape & (band >= 2) & (hash01(sp.x, sp.y, seed + 11) < 0.05)
    for dx, dy in ((0, 0), (1, 0)):
        tgt = shift(sw, dx, dy, False) & shape
        alt = IDX[f'{fam0}_warm'] if hash01(seed, 0, 3) < 0.5 else IDX[f'{fam0}_cool']
        sp.f[tgt] = np.where(sp.f[tgt] == alt, IDX[fam0], alt)
    if rim:
        edge = shape & (~shift(shape, 1, 0, False) | ~shift(shape, 0, 1, False)) & (band >= 4)
        sp.put(edge, 'grass', 5)
    return shape


def trunk(sp: Sprite, x, y0, y1, w=4, ramp='timber', seed=0, flare=2):
    """A trunk from y0 down to its foot y1: lit west column, dark east column, bark in
    short vertical clusters, the roots flaring at the foot."""
    for y in range(y0, y1 + 1):
        fl = flare if y >= y1 - 1 else (1 if y >= y1 - 3 and flare else 0)
        for dx in range(-fl, w + fl):
            k = 4 if dx <= 0 else 1 if dx >= w - 1 else 3 if dx == 1 else 2
            if 0 <= x + dx < sp.w and 0 <= y < sp.h:
                sp.put(_one(sp, x + dx, y), ramp, k)
    bark = sp.m & (sp.x >= x + 1) & (sp.x < x + w - 1) & (sp.y >= y0) & (sp.y <= y1) & \
        (hash01(sp.x, sp.y // 3, seed) < 0.3)
    sp.step(bark, -1, lo=1)


def _one(sp, x, y):
    m = np.zeros(sp.m.shape, bool)
    if 0 <= y < m.shape[0] and 0 <= x < m.shape[1]:
        m[y, x] = True
    return m


def tree_shadow(sp: Sprite, cx, rx, ry=None):
    """A round thing's blob shadow, thrown down and to the right of its foot."""
    ry = ry or max(3, rx * 0.32)
    return blob(cx + rx * 0.45, sp.fy + ry * 0.55, rx * 0.95, ry, sp.m.shape, 3, wob=0.08) & \
        ~blob(sp.fx - 1, sp.fy - ry * 0.9, rx * 0.4, ry * 0.7, sp.m.shape, 1, wob=0)


def willow(v=0, seed=10):
    """A willow by the water (size guide: 72 to 110 tall, as wide). v=0 a crack willow
    leaning over the water, its silver-green foliage hanging in curtains; v=1 a pollard: a
    thick short bole with a burr at the top and a mop of young shoots, as willows are cut
    along water meadows."""
    if v == 1:
        sp = Sprite(48, 50, 22, 47)
        crown(sp, 23, 14, 19, 12, seed, 'leaf_warm', clump=2.2, wob=0.18, lobes=9)
        tw = sp.m & (hash01(sp.x, sp.y // 2, seed + 7) < 0.12) & (sp.y < 12)
        sp.put(tw & ~shift(tw, 0, 1, False), 'grass_cool', 4)    # this year's shoots, upright
        sp.put(tw & shift(tw, 0, 1, False), 'grass_cool', 3)
        trunk(sp, 19, 24, 47, w=7, ramp='timber_cool', seed=seed)
        burr = (sp.x >= 17) & (sp.x <= 28) & (sp.y >= 22) & (sp.y <= 25)
        sp.put(burr, 'timber', np.where(sp.y == 22, 4, 3))
        sp.step(burr & (sp.x > 25), -1)
        return sp, tree_shadow(sp, 24, 20)
    sp = Sprite(100, 94, 48, 91)
    trunk(sp, 44, 40, 91, w=6, ramp='timber_cool', seed=seed)
    for (x0, y0, x1, y1) in ((47, 46, 66, 24), (46, 48, 30, 26), (48, 42, 52, 14)):    # limbs
        for i in range(0, 41):
            t = i / 40
            x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
            sp.put((np.abs(sp.x - x) <= 1) & (sp.y == y), 'timber_cool', np.where(sp.x < x, 3, 2))
    # the crown as overlapping fountains of hanging shoots: each a small dome of leaf clumps
    # over a curtain of strands two pixels wide; the outer ones lower and shorter, drawn
    # first, the middle ones over them
    lobes = []
    for i, u in enumerate((-0.92, 0.92, -0.6, 0.62, -0.28, 0.3, 0.0)):
        cx = 50 + u * 38
        top = 12 + 14 * u * u + (hash01(i, 0, seed) - 0.5) * 4
        rx = 13 + 3 * hash01(i, 1, seed)
        ln = int(52 - 18 * u * u + (hash01(i, 2, seed) - 0.5) * 8)
        lobes.append((cx, top, rx, ln, i))
    for (cx, top, rx, ln, i) in lobes:
        ry = 9
        dome = crown(sp, cx, top + ry, rx, ry, seed + i, 'leaf_cool' if i % 2 else 'leaf', clump=2.2, lobes=6,
                     wob=0.15, rim=True)
        for x in range(int(cx - rx) + 1, int(cx + rx)):
            if not (0 <= x < sp.w):
                continue
            xs = x - (x % 2)
            uu = (xs - cx) / rx
            if abs(uu) > 0.98:
                continue
            col = np.nonzero(dome[:, x])[0]
            if not len(col):
                continue
            y0 = int(col.max()) - 3
            length = int(ln * (1 - 0.45 * uu * uu) + (hash01(xs, i, seed + 3) - 0.5) * 10)
            lit = 4 if uu < -0.4 else 3 if uu < 0.25 else 2
            if x % 2:
                lit = max(1, lit - 1)
            fam = ('leaf_cool', 'grass_cool', 'leaf', 'leaf_warm')[int(hash01(xs, i, seed + 5) * 4)]
            if abs(uu) > 0.72:
                lit = max(1, lit - 1)              # the fold between two fountains
            for j in range(length):
                y = y0 + j
                if y >= 91:
                    break
                k = lit
                if j > length * 0.5:
                    k = max(1, lit - 1)            # the lower curtain in the crown's own shade
                if (j + xs + i * 3) % 7 in (0, 1):
                    k = min(4, k + 1)
                if j >= length - 2:
                    k = min(4, lit + 1)
                sp.put(_one(sp, x, y), fam, k)
    t2 = Sprite(100, 94, 48, 91)
    trunk(t2, 44, 40, 91, w=6, ramp='timber_cool', seed=seed)
    show = t2.m & (sp.y > 78) & (np.abs(sp.x - 47) <= 3)
    sp.put(show, t2.f, t2.t)
    return sp, tree_shadow(sp, 54, 42, 9)


def alder(seed=11):
    """An alder at the water (alders stand with their roots in the bank): a narrow, dark
    crown, rounded at the top, dark bark, last year's cones in small dark clusters."""
    sp = Sprite(44, 66, 21, 63)
    trunk(sp, 19, 30, 63, w=4, ramp='earth_cool', seed=seed)
    crown(sp, 22, 24, 18, 22, seed, 'leaf_cool', clump=2.8, lobes=6, wob=0.1)
    cones = sp.m & (hash01(sp.x // 2, sp.y // 2, seed + 3) < 0.03) & (sp.t >= 2) & (sp.y < 40) & ((sp.y % 2) == 0)
    sp.put(cones, 'timber_cool', 1)                  # last year's cones, in pairs
    roots = (sp.y >= 60) & (np.abs(sp.x - 21) < 6) & (sp.y - 60 >= np.abs(sp.x - 21) - 3)
    sp.put(roots & ~sp.m, 'earth_cool', 2)
    return sp, tree_shadow(sp, 23, 17)


def oak(seed=12, scale=1.0):
    """A broadleaf at a wood's edge (size guide: 78 to 125): a broad crown of rounded lobes."""
    W = int(84 * scale)
    H = int(96 * scale)
    sp = Sprite(W, H, W // 2, H - 3)
    trunk(sp, W // 2 - 3, int(H * 0.45), H - 3, w=7, ramp='timber', seed=seed, flare=3)
    for i, (dx, dy, rr) in enumerate(((0, 0.30, 0.42), (-0.22, 0.38, 0.28), (0.22, 0.36, 0.3), (0.05, 0.16, 0.3))):
        crown(sp, W / 2 + dx * W, H * dy, W * rr, H * rr * 0.72, seed + i, 'leaf', clump=2.7, lobes=6)
    return sp, tree_shadow(sp, W // 2 + 4, W * 0.42, 10 * scale)


def birch(seed=13):
    """A birch on the heath: a narrow, airy crown of small pale clumps, a white trunk with
    dark bands."""
    sp = Sprite(36, 80, 17, 77)
    trunk(sp, 16, 20, 77, w=3, ramp='plaster', seed=seed, flare=1)
    bands = sp.m & (sp.x >= 16) & (sp.x <= 18) & (hash01(0, sp.y // 2, seed + 4) < 0.28) & (sp.y > 26)
    sp.put(bands, 'iron', 2)
    crown(sp, 18, 26, 14, 24, seed, 'leaf_warm', clump=2.0, lobes=9, wob=0.18)
    peek = (sp.x >= 16) & (sp.x <= 18) & (sp.y >= 40) & (sp.y <= 77) & \
        (hash01(sp.x * 0, sp.y // 5, seed + 5) < 0.5)
    sp.put(peek & (sp.x == 16), 'plaster', 4)
    sp.put(peek & (sp.x == 17), 'plaster', 3)
    sp.put(peek & (sp.x == 18), 'plaster', 1)
    return sp, tree_shadow(sp, 19, 12)


def shrub(kind='hawthorn', seed=14):
    """A shrub: 'hawthorn' (a rounded bush, white may blossom), 'hazel' (several stems, a
    loose light crown), 'gorse' (dark spiny mound sprinkled yellow), 'bramble' (a low tangle
    of arching stems with blackberries)."""
    if kind == 'gorse':
        sp = Sprite(28, 20, 13, 18)
        crown(sp, 14, 11, 12, 8, seed, 'leaf_cool', clump=1.8, lobes=10, wob=0.2, rim=False)
        fl = sp.m & (hash01(sp.x, sp.y, seed + 2) < 0.14) & (sp.t >= 2)
        sp.put(fl, 'brass', 5)
        sp.put(shift(fl, 0, 1, False) & sp.m, 'brass', 3)
        return sp, tree_shadow(sp, 15, 11, 4)
    if kind == 'bramble':
        sp = Sprite(30, 16, 14, 14)
        crown(sp, 15, 10, 13, 5, seed, 'leaf', clump=1.8, lobes=11, wob=0.25, rim=False)
        arcs = (np.abs((sp.x - 15) ** 2 / 120.0 + (sp.y - 13) - 0) < 0.6) & (sp.y < 7)
        sp.put(arcs, 'berry_cool', 2)
        fr = sp.m & (hash01(sp.x // 2, sp.y, seed + 3) < 0.07)
        sp.put(fr, 'dusk_cool', 1)
        sp.put(fr & shift(fr, 1, 0, False), 'berry', 2)
        return sp, tree_shadow(sp, 16, 12, 3)
    if kind == 'hazel':
        sp = Sprite(40, 44, 19, 41)
        for dx in (-5, -1, 3, 6):
            trunk(sp, 19 + dx, 22, 41, w=2, ramp='timber_warm', seed=seed + dx, flare=0)
        crown(sp, 20, 18, 18, 16, seed, 'grass', clump=2.4, lobes=7)
        return sp, tree_shadow(sp, 21, 16)
    sp = Sprite(36, 32, 17, 30)
    trunk(sp, 16, 20, 30, w=3, ramp='timber_cool', seed=seed, flare=1)
    crown(sp, 18, 14, 16, 13, seed, 'leaf', clump=2.4, lobes=8)
    fl = sp.m & (hash01(sp.x // 2, sp.y // 2, seed + 2) < 0.1) & (sp.t >= 3)
    sp.put(fl & ((sp.x + sp.y) % 2 == 0), 'plaster', 5)
    sp.put(fl & ((sp.x + sp.y) % 2 == 1), 'plaster', 4)
    return sp, tree_shadow(sp, 19, 15)


def reeds(kind='reed', seed=15, n=5):
    """A clump of 3 to 6 reeds standing in the shallows (size guide: 14 to 32 tall):
    'reed' common reed with purple-brown plumes, 'mace' reedmace with brown seed heads.
    Blades lit on the west, dark at the water."""
    H = 28
    sp = Sprite(20, H + 2, 10, H)
    for i in range(n):
        bx = 3 + int(i * 14 / max(1, n - 1)) + int((hash01(i, 0, seed) - 0.5) * 2)
        top = 6 + int(hash01(i, 1, seed) * 10)
        lean = (hash01(i, 2, seed) - 0.5) * 0.35
        for y in range(top, H + 1):
            x = int(round(bx + lean * (H - y)))
            k = 1 if y > H - 3 else 3 if i % 2 == 0 else 2
            if y < top + 3:
                k = 4
            sp.put(_one(sp, x, y), 'grass_warm' if i % 3 else 'leaf_warm', k)
        hx = int(round(bx + lean * (H - top)))
        if kind == 'mace' and i % 2 == 0:
            for y in range(top - 5, top):
                sp.put(_one(sp, hx, y), 'timber', 3 if y < top - 2 else 2)
                sp.put(_one(sp, hx + 1, y), 'timber_cool', 1)
            sp.put(_one(sp, hx, top - 6), 'timber', 4)
        elif kind == 'reed':
            for y in range(top - 4, top):
                for dx in (-1, 0):
                    sp.put(_one(sp, hx + dx, y), 'dusk_warm' if dx else 'timber_warm', 3 if dx else 2)
        # a leaf blade arching from the stem
        if i % 2 == 1:
            for j in range(5):
                lx, ly = bx + j - 2 + (1 if j > 2 else 0), H - 8 - j + (j * j) // 4
                if 0 <= lx < sp.w:
                    sp.put(_one(sp, lx, ly), 'grass', 3)
    sh = np.zeros(sp.m.shape, bool)
    sh[H - 1:H + 1, 6:20] = True
    return sp, sh


def marginal(kind='iris', seed=16):
    """Plants of the water's edge: 'iris' (yellow flag: a fan of sword leaves, a yellow
    flower), 'meadowsweet' (cream froth on tall stems), 'loosestrife' (purple spikes),
    'marigold' (marsh marigold: round leaves, gold flowers, low), 'fern' (a fern's fronds,
    for the wood's shade)."""
    if kind == 'iris':
        sp = Sprite(14, 16, 7, 15)
        for i, dx in enumerate((-4, -2, 0, 2, 4)):
            top = 3 + abs(dx)
            for y in range(top, 16):
                x = 7 + int(round(dx * (16 - y) / 14))
                sp.put(_one(sp, x, y), 'leaf' if i % 2 else 'leaf_warm', 4 if y < top + 2 else 2 if y > 13 else 3)
        sp.put((sp.x >= 8) & (sp.x <= 9) & (sp.y >= 2) & (sp.y <= 3), 'brass', 5)
        sp.put((sp.x >= 8) & (sp.x <= 9) & (sp.y == 4), 'brass', 3)
        return sp, None
    if kind == 'meadowsweet':
        sp = Sprite(14, 18, 7, 17)
        for dx, top in ((-3, 5), (0, 2), (3, 4)):
            sp.put((sp.x == 7 + dx) & (sp.y >= top + 2) & (sp.y <= 17), 'grass_cool', 2)
            head = ((sp.x - 7 - dx) ** 2 / 4.0 + (sp.y - top) ** 2 / 2.0) <= 1.6
            sp.put(head, 'plaster', np.where(sp.x < 7 + dx, 5, 4))
            sp.put(head & (sp.y == top + 1) & (sp.x > 7 + dx), 'plaster', 3)
        return sp, None
    if kind == 'loosestrife':
        sp = Sprite(10, 22, 5, 21)
        for dx, top in ((-2, 4), (2, 2)):
            sp.put((sp.x == 5 + dx) & (sp.y >= top) & (sp.y <= 21), 'grass_cool', 2)
            spike = (sp.x >= 5 + dx) & (sp.x <= 6 + dx) & (sp.y >= top) & (sp.y <= top + 6)
            sp.put(spike, 'berry_cool', np.where(sp.x == 5 + dx, 4, 3))
            sp.put(spike & (sp.y == top), 'dusk', 5)
        return sp, None
    if kind == 'fern':
        sp = Sprite(24, 14, 12, 13)
        for i, ang in enumerate((-2.5, -1.9, -1.2, -0.6, 0.0)):
            for side in (-1, 1):
                a = ang * side * 0.5 - math.pi / 2 + side * 0.25 * i
                for r in range(2, 11 - i):
                    x = int(round(12 + math.cos(a + side * 0.6) * r * (1.0 + 0.1 * i)))
                    y = int(round(13 + math.sin(a + side * 0.6) * r * 0.75))
                    if 0 <= x < 24 and 0 <= y < 14:
                        k = 4 if r == 2 else 3 if (r + i) % 2 else 2
                        sp.put(_one(sp, x, y), 'leaf_warm' if side < 0 else 'leaf', k)
                        if r % 2 == 0 and y + 1 < 14:
                            sp.put(_one(sp, x, y + 1), 'leaf_cool', 2)
        return sp, tree_shadow(sp, 13, 10, 3)
    sp = Sprite(14, 9, 7, 8)
    mound = blob(7, 5, 6, 3.5, sp.m.shape, seed, wob=0.15, lobes=5)
    sp.put(mound, 'leaf', np.where(sp.y <= 3, 4, np.where(sp.y >= 7, 2, 3)))
    fl = mound & (hash01(sp.x // 2, sp.y, seed) < 0.3) & (sp.y <= 5)
    sp.put(fl & (sp.x % 2 == 0), 'brass', 5)
    sp.put(fl & (sp.x % 2 == 1), 'brass', 4)
    return sp, None


def lily(p: Plot, x, y, seed=17, flower=False):
    """A water lily pad on a pool: a flat round leaf with its notch, lit on its top left,
    its edge dark on the water; a white flower on some."""
    pad = blob(x + 0.5, y + 0.5, 3.4, 2.2, p.f.shape, seed, wob=0.05)
    pad &= p.wet
    if not pad.any():
        return
    k = np.where(p.y < y, 4, np.where(p.y > y, 2, 3))
    p.f[pad], p.t[pad] = IDX['leaf_warm'], k[pad]
    cut = pad & (p.x == x + 2) & (p.y <= y) & (p.y >= y - 1)
    p.f[cut], p.t[cut] = IDX['water_cool'], 2
    rim = dilate(pad, 1) & ~pad & p.wet & shift(pad, 0, 1, False)
    p.f[rim], p.t[rim] = IDX['water_cool'], 1
    if flower:
        fl = (p.x >= x - 1) & (p.x <= x) & (p.y == y - 1)
        p.f[fl], p.t[fl] = IDX['plaster'], 5
        p.f[fl & (p.x == x)], p.t[fl & (p.x == x)] = IDX['plaster'], 4


# --- built water: the mill race and the canal -----------------------------------------------
def _sunken(p: Plot, wet_plan, hb, side_w=2):
    """What the camera sees of water lying `hb` px below the land: the water drawn hb px
    further down, the north bank's face between, a narrow side face on west and east banks.
    Returns (water, face, rows down the face, west-bank side band)."""
    rows = np.arange(p.h)[:, None]
    src = np.clip(rows - hb, 0, p.h - 1)
    wet_src = np.take_along_axis(wet_plan, src, axis=0)
    water = wet_plan & wet_src
    face = wet_plan & ~wet_src
    land = ~wet_plan
    west = np.zeros_like(land)
    east = np.zeros_like(land)
    for dx in range(1, side_w + 1):
        west |= shift(land, dx, 0, False)
        east |= shift(land, -dx, 0, False)
    side = water & (west | east)
    face |= side
    water &= ~side
    j = np.zeros(p.f.shape, int)
    run = np.zeros(p.w, int)
    for y in range(p.h):
        run = np.where(face[y], run + 1, 0)
        j[y] = run - 1
    return water, face, j, side & west


def coping(p: Plot, m, seed, ramp='stone'):
    """A coping: dressed blocks laid along an edge, each lit on its top and west, a dark
    joint every 9 to 13 px."""
    u = p.x + p.y // 3 * 0
    block = (u + (hash01(p.y, 0, seed) * 5).astype(int)) // 11
    pick = hash01(block, p.y // 4, seed + 1)
    fam = np.where(pick < 0.3, IDX[f'{ramp}_warm'], np.where(pick > 0.7, IDX[f'{ramp}_cool'], IDX[ramp]))
    top = m & ~shift(m, 0, 1, False)
    bot = m & ~shift(m, 0, -1, False)
    k = np.where(top, 4, np.where(bot, 2, 3))
    p.f[m], p.t[m] = fam[m], k[m]
    joint = m & ((u + (hash01(p.y, 0, seed) * 5).astype(int)) % 11 == 0)
    p.f[joint], p.t[joint] = IDX[f'{ramp}_cool'], 1
    gl = top & ((u + (hash01(p.y, 0, seed) * 5).astype(int)) % 11 == 2)
    p.t[gl] = 5


def race(p: Plot, pts, width=24, seed=20, depth=10):
    """A mill race: a straight cut channel in a stone revetment (coursed rubble faces with
    moss in the low joints and a wet tide line, a coping along both edges), its water fast
    and dark with the current running in long streaks."""
    ch = Channel(p, pts, reach=width // 2 + 8)
    hw = width / 2
    wet_plan = ch.near & (np.abs(ch.n) < hw)
    cope = ch.near & (np.abs(ch.n) >= hw) & (np.abs(ch.n) < hw + 3)
    water, face, j, west = _sunken(p, wet_plan, depth)
    coping(p, cope, seed)
    _bank_face(p, face, j, depth, seed + 1, stone=True, east_facing=west)
    _water(p, water, ch, hw, seed + 2)
    fast = water & (hash01(np.floor((ch.n + 50) / 2), 0, seed + 3) < 0.6) & \
        ((ch.s.astype(int) + (hash01(np.floor((ch.n + 50) / 2), 1, seed) * 30).astype(int)) % 14 < 6)
    p.step(fast & (p.t <= 3), 1)
    under = water & shift(cope, 0, -1, False)
    p.step(under | (water & shift(under, 0, -1, False)), -1, lo=1)
    p.wet |= water
    p.walk &= ~(water | face)
    p.solid |= face
    despeckle(p, water)
    ch.water, ch.face = water, face
    return ch


def canal(p: Plot, pts, width=40, seed=21, towpath='north', path_w=20, depth=6):
    """A canal edge (size guide: 40 wide, towpaths 16 to 24): still water between stone
    edges, a coping of dressed blocks along each, the north edge's face showing; the towpath
    of rolled gravel along one side with a worn line where boots and hooves go, grass
    verges, and a mooring bollard."""
    ch = Channel(p, pts, reach=width // 2 + path_w + 8)
    hw = width / 2
    wet_plan = ch.near & (np.abs(ch.n) < hw)
    cope = ch.near & (np.abs(ch.n) >= hw) & (np.abs(ch.n) < hw + 4)
    sgn = -1 if towpath == 'north' else 1
    north_is_neg = np.mean(ch.dir[:, 0]) > 0       # flowing east, the left (negative) bank is north
    tp_side = sgn if north_is_neg else -sgn
    tp = ch.near & (ch.n * tp_side > hw + 4) & (ch.n * tp_side < hw + 4 + path_w + 2 * (vnoise(ch.s, 0 * ch.s, 6, seed) - 0.5))
    base(p, tp, 'path', seed, scale=6, light=0.66)
    texture(p, tp, seed + 1, swaps=0.12, ups=0.03, downs=0.02)
    worn = tp & (np.abs(np.abs(ch.n) - (hw + 4 + path_w * 0.45)) < 2.2 + vnoise(ch.s, 0 * ch.s, 5, seed + 2))
    p.step(worn, 1)
    pebbles(p, tp & ~worn, seed + 3, 0.015)
    verge = tp & (np.abs(ch.n) > hw + 4 + path_w - 3 + 2 * vnoise(ch.s, ch.n, 3, seed + 4))
    p.f[verge], p.t[verge] = IDX['grass'], 3
    stamp(p, verge, 0.15, seed + 5, BLADES, dt=1)
    p.walk |= tp
    water, face, j, west = _sunken(p, wet_plan, depth)
    coping(p, cope, seed + 6, 'stone')
    _bank_face(p, face, j, depth, seed + 7, stone=True, east_facing=west)
    # still water: calm bands, the sky's light along the far side, the coping's reflection
    # a lighter broken band under the north face, glints in pairs
    m = water
    sibn = fbm(ch.s / 4.0, ch.n, 8, seed + 8)
    fam = np.where(sibn < 0.3, IDX['water_warm'], np.where(sibn > 0.7, IDX['water_cool'], IDX['water']))
    k = np.where(np.abs(ch.n) < hw * 0.55, 2, 3)
    p.f[m], p.t[m] = fam[m], k[m]
    refl = m & shift(face, 0, 2, False) & ~face & (hash01(p.x // 3, 0, seed + 9) < 0.7)
    p.t[refl] = 3
    under = m & shift(cope, 0, -1, False)
    p.step(under | (m & shift(under, 0, -1, False)), -1, lo=1)
    g = m & (hash01(p.x // 2, p.y, seed + 10) < 0.008) & ~refl
    gg = g | (shift(g, 1, 0, False) & m)
    p.f[gg], p.t[gg] = IDX['water_warm'], 4
    despeckle(p, m)
    p.wet |= water
    p.walk &= ~(water | face)
    p.solid |= face
    # a bollard on the towpath's coping side
    i = ch.length // 3
    bx, by = ch.c[i] + np.array([-ch.dir[i, 1], ch.dir[i, 0]]) * tp_side * (hw + 7)
    sp = Sprite(6, 8, 2, 7)
    sp.put((sp.x >= 1) & (sp.x <= 4) & (sp.y >= 2), 'iron', np.where(sp.x == 1, 4, np.where(sp.x == 4, 1, 3)))
    sp.put((sp.x >= 0) & (sp.x <= 5) & (sp.y <= 1), 'iron', np.where(sp.y == 0, 4, 2))
    sh = np.zeros(sp.m.shape, bool)
    paste(p, sp, int(bx), int(by), shadow=sh)
    ch.water, ch.face, ch.towpath = water, face, tp
    return ch


# --- the regions beyond: heath and wood -----------------------------------------------------
def heath(p: Plot, m, seed=30, heather=0.55):
    """The Brackens' heath: low mounds of heather in flower (each mound lit on its top left,
    dark at its foot), bracken in drifts, sandy ground and short turf between, the odd
    stone. `heather` is the share of heather against bracken and turf."""
    m = np.asarray(m, bool)
    base(p, m, 'grass', seed, scale=6, warm=0.55, cool=0.9)        # short, yellowing turf
    p.step(m, 0)
    sandy = m & (fbm(p.x, p.y, 10, seed + 1) > 0.66)
    base(p, sandy, 'sand', seed + 2, scale=4)
    texture(p, m, seed + 3, swaps=0.07, ups=0.015, downs=0.015)
    pebbles(p, sandy, seed + 4, 0.02)
    field = fbm(p.x, p.y, 16, seed + 5)
    hm = m & (field > 1 - heather) & ~sandy
    bm = m & (field < 0.3) & ~sandy
    # heather: low mounds of every size, each lit on its top left, flowering on its crown
    inside, du, dv, cid = clumps(p, hm, 6, 3.0, 4.6, seed + 6)
    pick = hash01(cid, 0, seed + 7)
    mound = hm & inside
    p.f[mound] = np.where(pick < 0.4, IDX['dusk_cool'], np.where(pick < 0.85, IDX['dusk'], IDX['berry_cool']))[mound]
    lv = -du - dv
    p.t[mound] = np.where(lv > 0.55, 4, np.where(lv < -0.55, 2, 3))[mound]
    bloom = mound & (lv > 0.9)
    p.t[bloom] = 5
    stem = hm & ~inside
    p.f[stem], p.t[stem] = IDX['leaf_cool'], 2
    foot = mound & (dv > 0.6)
    p.f[foot], p.t[foot] = IDX['leaf_cool'], 2
    # bracken: fronds as arching clusters, green with rust at the tips
    p.f[bm] = np.where(hash01(p.x // 3, p.y // 3, seed + 7) < 0.5, IDX['grass_warm'], IDX['leaf_warm'])[bm]
    p.t[bm] = 3
    stamp(p, bm, 0.12, seed + 8, (((0, 0), (1, -1), (2, -1)), ((0, 0), (-1, -1), (-2, -1)), ((0, 0), (0, -1), (1, -2))), dt=1)
    stamp(p, bm, 0.06, seed + 9, BLADES, dt=-1)
    stamp(p, bm, 0.02, seed + 10, DOMINOES, ramp='clay', tone=3, same_family=False)
    despeckle(p, m)
    return hm, bm


def wood_floor(p: Plot, m, seed=31, shade=1):
    """A broadleaf wood's floor in the shade (`shade` tones down): leaf litter in small
    clusters, moss, bluebells in drifts, dapples of sun, twigs."""
    m = np.asarray(m, bool)
    base(p, m, 'earth', seed, scale=6, warm=0.4, cool=0.75)
    moss = m & (fbm(p.x, p.y, 12, seed + 1) > 0.6)
    base(p, moss, 'leaf', seed + 2, scale=5)
    stamp(p, m & ~moss, 0.10, seed + 3, SMALL, ramp='timber_warm', tone=3, same_family=False)
    stamp(p, m & ~moss, 0.05, seed + 4, SMALL[:3], ramp='earth_warm', tone=4, same_family=False)
    stamp(p, m, 0.08, seed + 5, SMALL, swap='mix')
    bells = m & (fbm(p.x, p.y, 20, seed + 6) > 0.62)
    stamp(p, bells, 0.10, seed + 7, DOMINOES + (((0, 0), (1, 0), (0, -1)),), ramp='dusk_warm', tone=4,
          same_family=False)
    stamp(p, bells, 0.05, seed + 8, DOMINOES, ramp='sky_cool', tone=3, same_family=False)
    p.step(m, -shade, lo=2)
    sun = m & (fbm(p.x, p.y, 7, seed + 9) > 0.7)
    p.step(sun, 1)
    despeckle(p, m)


def clumps(p: Plot, m, spacing, rmin, rmax, seed):
    """Round clumps of varied size scattered over a mask (heather mounds, gorse, moss):
    for each pixel, whether it lies in a clump, its offset from the clump's centre in
    units of the radius (du, dv) and the clump's id."""
    gx, gy = p.x // spacing, p.y // spacing
    best = np.full(p.f.shape, 9.0)
    du = np.zeros(p.f.shape)
    dv = np.zeros(p.f.shape)
    cid = np.zeros(p.f.shape, np.int64)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx_, cy_ = gx + ox, gy + oy
            px = cx_ * spacing + hash01(cx_, cy_, seed) * spacing
            py = cy_ * spacing + hash01(cx_, cy_, seed + 1) * spacing
            r = rmin + (rmax - rmin) * hash01(cx_, cy_, seed + 2)
            u, v = (p.x + 0.5 - px) / r, (p.y + 0.5 - py) / (r * 0.8)
            d = u * u + v * v
            # the nearer clump (lower on screen first) wins, so clumps overlap front to back
            better = (d <= 1) & ((best > 1) | (py > cy_ * 0 + np.where(best <= 1, p.y - dv * 99, -1e9)))
            better = (d <= 1) & ((best > 1) | (d < best))
            best = np.where(better, d, best)
            du = np.where(better, u, du)
            dv = np.where(better, v, dv)
            cid = np.where(better, cx_ * 7919 + cy_, cid)
    return (best <= 1) & m, du, dv, cid


def blend(p: Plot, m, t, paint_a, paint_b, seed=40, warp=0.75, outliers=0.18):
    """Two grounds mixed over a band, never along a line (world plan 5: bands, not lines).
    `t` runs 0 (all A) to 1 (all B) across the band; the edge between them is warped at two
    scales, so tongues of each reach into the other, and islands of each (outliers) lie
    beyond it on both sides. paint_a and paint_b paint a ground into a mask of a plot.
    Returns the mask that took B."""
    m = np.asarray(m, bool)
    big = fbm(p.x, p.y, 52, seed) - 0.5
    small = fbm(p.x, p.y, 9, seed + 1) - 0.5
    v = t + warp * big + 0.16 * small
    sel = v > 0.5
    isl = hash01(p.x // 14, p.y // 14, seed + 2)
    near = np.abs(t - 0.5) < 0.9
    blobs = (fbm(p.x, p.y, 7, seed + 3) > 0.7) & near & (isl < outliers * 4)
    sel = np.where(t < 0.5, sel | blobs, sel & ~blobs)
    sel = erode(dilate(sel, 1), 1)
    sel = dilate(erode(sel, 1), 1) & m
    a = Plot(p.w, p.h)
    paint_a(a, m)
    b = Plot(p.w, p.h)
    paint_b(b, m)
    for attr in ('f', 't'):
        getattr(p, attr)[m] = np.where(sel, getattr(b, attr), getattr(a, attr))[m]
    # the seam: a few clusters of each spill over the other in a 3 px fringe
    seam = m & dilate(sel, 2) & ~erode(sel, 2)
    spill = seam & (hash01(p.x // 2, p.y // 2, seed + 4) < 0.35)
    src_b = spill & ~sel
    src_a = spill & sel
    p.f[src_b], p.t[src_b] = b.f[src_b], b.t[src_b]
    p.f[src_a], p.t[src_a] = a.f[src_a], a.t[src_a]
    despeckle(p, seam)
    return sel


def wood_edge(p: Plot, m, t, seed=50, paint_open=None):
    """The Fern hills' woodland edge, from open meadow (t 0) into the wood (t 1) over a band:
    the meadow's long grass, then a fringe of bramble and tall herbs, then shrubs (hazel,
    hawthorn), then oaks whose shade turns the ground to the wood's floor of litter, moss,
    bluebells and ferns. Lone hawthorns stand out in the meadow and a few shrubs in the
    wood's clearings, so the change has outliers both ways. Returns the wood's ground mask."""
    m = np.asarray(m, bool)
    snap = (p.f.copy(), p.t.copy())

    def pa(q, mm):
        q.f[:], q.t[:] = snap

    def pb(q, mm):
        wood_floor(q, mm, seed + 1)
    floor = blend(p, m, np.clip(t * 1.25 - 0.2, 0, 1), pa, pb, seed + 2, warp=0.5, outliers=0.1)
    fringe = m & (t > 0.12) & (t < 0.5) & ~floor
    hay_meadow(p, fringe & (fbm(p.x, p.y, 12, seed + 3) > 0.4), seed + 4)
    plant(p, m & (t > 0.15) & (t < 0.45), 500, [lambda s: shrub('bramble', s)], seed + 5,
          density=np.clip(1 - np.abs(t - 0.3) * 6, 0, 1))
    plant(p, m & (t > 0.55), 260, [lambda s: marginal('fern', s)], seed + 6, density=np.clip(t * 1.4 - 0.6, 0, 1))
    plant(p, m & (t > 0.3) & (t < 0.8), 1100, [lambda s: shrub('hazel', s), lambda s: shrub('hawthorn', s)],
          seed + 7, density=np.clip(1 - np.abs(t - 0.55) * 3, 0, 1))
    plant(p, m & (t > 0.55), 2400, [lambda s: oak(s, 0.8 + 0.25 * hash01(s, 0, 1))], seed + 8,
          density=np.clip(t * 1.6 - 0.7, 0, 1))
    plant(p, m & (t < 0.2) & (t > 0.02), 9000, [lambda s: shrub('hawthorn', s)], seed + 9)   # outliers
    return floor


def plant(p: Plot, m, every, makers, seed, density=None, foot_clear=None):
    """Scatter sprites over a mask, about one per `every` px, keeping a clear gap round
    each; `density` (an array 0..1) thins them where it is low. Returns the feet."""
    feet = []
    taken = np.zeros(p.f.shape, bool) if foot_clear is None else foot_clear.copy()
    for i, (x, y) in enumerate(_scatter(m, every, seed)):
        if density is not None and hash01(x, y, seed + 1) > density[y, x]:
            continue
        if taken[y, x]:
            continue
        mk = makers[int(hash01(x, y, seed + 2) * len(makers))]
        sp, sh = mk(seed + i)
        full = paste(p, sp, x, y, shadow=sh)
        taken |= dilate(full, 3) if full.sum() < 400 else full
        feet.append((x, y))
    return feet


def flow_frames(p: Plot, frames=None):
    """The moving water, as water_flow.py draws it for the zones (channel streaks drifting
    downstream, glints on open water, foam lapping the banks), recoloured onto the house
    ramps: a changed pixel moves one tone up its own ramp (two at a streak's head) instead
    of being mixed with white. Returns (list of RGB frames, box)."""
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


# --- the sample scene -------------------------------------------------------------------------
SAMPLE_W, SAMPLE_H = 640, 576
SLEEPWATER = [(436, -14), (412, 70), (346, 150), (330, 236), (372, 318), (452, 380), (470, 470), (436, 590)]
LANE = [(-12, 284), (120, 276), (230, 262), (300, 256), (360, 262), (470, 252), (560, 238), (652, 232)]
FIELD_HEDGE = [(-12, 300), (120, 292), (240, 280), (300, 276)]
FIELD_WEST = [(30, 300), (24, 420), (34, 590)]
FIELD_EAST = [(300, 282), (288, 420), (312, 590)]


def sample(seed=1):
    """A bend of the Sleepwater with a ford where the farm lane crosses it, a hay meadow,
    a hedged wheat field, grazing over the water, and the Brackens' heath coming in from the
    west over a band with outliers. 640 x 576 (two phone screens wide, one tall)."""
    W, H = SAMPLE_W, SAMPLE_H
    p = Plot(W, H)
    every = np.ones((H, W), bool)
    # the ground, west to east: heath, the meadow, the river's banks, pasture
    river_ch = Channel(p, SLEEPWATER, reach=60)
    west_of_river = (river_ch.n > 0) if np.mean(river_ch.dir[:, 1]) > 0 else (river_ch.n < 0)
    # rows: north of the lane is the hay meadow, south of it the hedged field
    north = p.y < np.interp(p.x, [q[0] for q in LANE], [q[1] for q in LANE]) - 10
    side_w = np.where(river_ch.near, west_of_river, p.x < 380)
    meadow = north & side_w
    fy = np.interp(p.x, [q[0] for q in FIELD_HEDGE], [q[1] for q in FIELD_HEDGE])
    ex = np.interp(p.y, [q[1] for q in FIELD_EAST], [q[0] for q in FIELD_EAST])
    wx = np.interp(p.y, [q[1] for q in FIELD_WEST], [q[0] for q in FIELD_WEST])
    fieldm = (p.y > fy + 8) & (p.x > wx + 7) & (p.x < ex - 7)
    fieldm = dilate(erode(fieldm, 6), 6) & fieldm           # the corners rounded
    marg = fieldm & ~erode(fieldm, 9)
    wheat = fieldm & ~marg
    east = ~side_w
    pasture(p, every, seed + 1)
    hay_meadow(p, meadow, seed + 2)
    hgt = p.y * 0.8 + 10 * np.sin(p.x / 46.0) + 6 * np.sin(p.y / 33.0 + p.x / 80.0)
    crop(p, wheat, hgt, seed + 3)
    margin(p, marg & (p.y > 290), seed + 4)
    # the heath edge: the Brackens to the west, mixed with the meadow over ~150 px
    t = np.clip((200 - p.x - 30 * np.sin(p.y / 70.0)) / 150.0, 0, 1)
    band = (t > 0) & ~wheat & ~marg
    snap = (p.f.copy(), p.t.copy())

    def pa(q, mm):
        q.f[:], q.t[:] = snap
    hm = {}

    def pb(q, mm):
        hm['h'] = heath(q, mm, seed + 5)
    took = blend(p, band, t, pa, pb, seed + 6)
    # the Fern hills' wood edge in the north-east, over the water
    tw = np.clip(((p.x - 440) * 0.9 - p.y * 0.8 + 70 + 25 * np.sin(p.y / 40.0)) / 130.0, 0, 1)
    woodm = (tw > 0) & ~side_w & (p.y < 230)
    # the river and its ford, then the lane through it
    best = None
    for i, (cx, cy) in enumerate(river_ch.c):
        ly = np.interp(cx, [q[0] for q in LANE], [q[1] for q in LANE])
        if best is None or abs(cy - ly) < best[0]:
            best = (abs(cy - ly), i)
    ford_s = best[1]
    ch = river(p, SLEEPWATER, width=40, seed=seed + 7, ford_at=ford_s, ford_width=30, stones_at=ford_s + 26)
    lane = track(p, LANE, 24, seed + 8, puddles=2)
    hedge = hedgerow(p, FIELD_HEDGE, 16, 10, seed + 9, gaps=(), gate_at=200)
    hedgerow(p, FIELD_WEST, 15, 10, seed + 10, gaps=(150,))
    hedgerow(p, FIELD_EAST, 15, 10, seed + 19, gaps=(120,))
    hedgerow(p, [(452, 238), (560, 222), (652, 214)], 16, 10, seed + 11, gaps=(60,))
    # water's edge: reeds in the still shallows on the inside of the bends, iris and
    # meadowsweet along the banks, lilies on the pool, willows and alders standing at it
    pts = _scatter(dilate(ch.water, 1) & ~erode(ch.water, 3) & ~dilate(ch.ford, 8) & (ch.bend() > 0.3) & ~ch.outer
                   & ~dilate(lane.mask, 10), 160, seed + 12, 0)
    for i, (x, y) in enumerate(pts[:14]):
        sp, sh = reeds('reed' if i % 3 else 'mace', seed + i, 4 + i % 3)
        paste(p, sp, x, y + 3, shadow=sh)
    bank = dilate(ch.water | ch.face, 3) & ~(ch.water | ch.face) & ~p.solid & ~dilate(lane.mask, 4) & ~ch.ford
    for i, (x, y) in enumerate(_scatter(bank, 220, seed + 13, 0)[:22]):
        kind = ('iris', 'meadowsweet', 'loosestrife', 'marigold')[i % 4]
        sp, sh = marginal(kind, seed + i)
        paste(p, sp, x, y, shadow=sh)
    pool = ch.water & (ch.bend() > 0.6) & (p.t <= 2) & erode(ch.water, 4)
    for i, (x, y) in enumerate(_scatter(pool, 90, seed + 14, 0)[:7]):
        lily(p, x, y, seed + i, flower=i % 3 == 0)
    trees = [(willow, 0, (296, 214)), (willow, 1, (402, 214)), (alder, None, (500, 330)),
             (alder, None, (300, 118)), (willow, 1, (520, 420)), (alder, None, (394, 470))]
    for mk, v, (x, y) in sorted(trees, key=lambda q: q[2][1]):
        sp, sh = mk(v, seed) if v is not None else mk(seed + x)
        paste(p, sp, x, y, shadow=sh)
    # the heath's own things: gorse and birches, thicker to the west, with outliers
    gor = took & ~p.solid
    plant(p, gor, 1300, [lambda s: shrub('gorse', s)], seed + 15, density=np.clip(t * 1.1, 0, 0.9))
    plant(p, (took | (t > 0.15)) & ~p.solid & (p.y < 250) & ~p.wet, 3000, [birch], seed + 16,
          density=np.clip(t * 1.2 + 0.1, 0, 1))
    plant(p, meadow & ~took & (t > 0.0) & ~p.solid, 2600, [lambda s: shrub('gorse', s)], seed + 17,
          density=np.clip(t * 2.5, 0, 0.8))
    plant(p, meadow & ~took & (t > 0.05), 9000, [lambda s: shrub('gorse', s)], seed + 17)
    # the meadow's hawthorn, a hedgerow oak at the field corner
    sp, sh = shrub('hawthorn', seed)
    paste(p, sp, 150, 120, shadow=sh)
    sp, sh = oak(seed, 0.85)
    paste(p, sp, 30, 298, shadow=sh)
    sp, sh = shrub('bramble', seed)
    paste(p, sp, 280, 300, shadow=sh)
    wood_edge(p, woodm & ~p.solid & ~p.wet & ~dilate(lane.mask, 4) & ~dilate(ch.water | ch.face, 3), tw, seed + 30)
    for i, (x, y) in enumerate(_scatter(east & ~p.solid & ~p.wet & ~dilate(lane.mask, 6) & (p.y > 300), 6000, seed + 18)):
        tussock(p, x, y, seed + i)
    despeckle(p)
    return p, {'river': ch, 'lane': lane, 'hedge': hedge, 'heath': took, 'meadow': meadow, 'wheat': wheat,
               'margin': marg, 'pasture': east}


# --- the kit sheet, the bar and the comparisons --------------------------------------------
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))


def _meadow_plot(w, h, seed=0, kind='pasture'):
    p = Plot(w, h)
    (pasture if kind == 'pasture' else hay_meadow)(p, np.ones((h, w), bool), seed)
    return p


def pieces():
    """Every piece on its own tile: (group, name, plot, bar box or None, bar kind)."""
    out = []
    W, H = 168, 120
    # water
    p = _meadow_plot(W, H, 1)
    river(p, [(-10, 30), (60, 26), (120, 52), (150, 100), (160, 130)], 40, seed=5)
    out.append(('water', 'river bend: cut bank, point bar, pool', p, (52, 14, 140, 80), 'stream'))
    p = _meadow_plot(W, 96, 2)
    river(p, [(-10, 50), (60, 46), (120, 50), (180, 46)], 24, seed=6, high=5)
    out.append(('water', 'stream riffle (24 wide)', p, (20, 26, 150, 72), 'stream'))
    p = _meadow_plot(W, H, 3)
    river(p, [(-10, 64), (70, 58), (180, 62)], 36, seed=7, ford_at=88, ford_width=30, stones_at=60)
    track(p, [(84, -10), (86, 60), (88, 130)], 24, seed=8, puddles=0)
    out.append(('water', 'ford with stepping stones', p, (40, 38, 150, 86), 'stream'))
    p = _meadow_plot(W, 96, 4)
    race(p, [(-10, 48), (180, 48)], 24, seed=9)
    out.append(('water', 'mill race in a stone revetment', p, (10, 30, 160, 72), 'stream'))
    p = _meadow_plot(W, 128, 5)
    canal(p, [(-10, 76), (180, 76)], 40, seed=10, towpath='north', path_w=20)
    out.append(('water', 'canal: coping, towpath, bollard', p, (10, 26, 160, 100), 'stream'))
    # water's edge plants and trees
    p = _meadow_plot(W, H, 6)
    river(p, [(-10, 80), (180, 80)], 48, seed=11, high=4, bar=False)
    for i, (x, y) in enumerate(((14, 64), (40, 62), (120, 63))):
        sp, sh = reeds(('reed', 'mace', 'reed')[i], 20 + i, 5)
        paste(p, sp, x, y, shadow=sh)
    for i, (k, x) in enumerate((('iris', 66), ('meadowsweet', 86), ('loosestrife', 102), ('marigold', 146), ('iris', 156))):
        sp, sh = marginal(k, 30 + i)
        paste(p, sp, x, 54, shadow=sh)
    for i, (x, y) in enumerate(((40, 92), (60, 98), (100, 90), (130, 96))):
        lily(p, x, y, 40 + i, flower=i % 2 == 0)
    out.append(('edge', 'reeds, reedmace, iris, meadowsweet, loosestrife, marigold, lilies', p, (8, 40, 164, 112), 'stream'))
    for name, mk in (('crack willow', lambda: willow(0)), ('pollard willow', lambda: willow(1)), ('alder', alder),
                     ('oak', lambda: oak(12, 0.9)), ('birch', birch)):
        sp, sh = mk()
        p = _meadow_plot(max(W // 2 + 30, sp.w + 16), sp.h + 14, 7)
        paste(p, sp, p.w // 2, p.h - 8, shadow=sh)
        m = sp.m
        ys, xs = np.nonzero(m)
        x0, y0 = p.w // 2 - sp.fx + int(np.percentile(xs, 15)), p.h - 8 - sp.fy + int(np.percentile(ys, 5))
        box = (x0, y0, x0 + 36, y0 + 36) if sp.w >= 40 else None
        out.append(('edge', name, p, box, 'tree'))
    # farmland
    hgt = None
    for name, fn, kind in (('hay meadow', hay_meadow, 'ground'), ('grazed pasture', pasture, 'ground')):
        p = Plot(96, 96)
        fn(p, np.ones((96, 96), bool), 3)
        out.append(('farm', name, p, (8, 8, 88, 88), kind))
    for name, kind in (('ploughed field', 'plough'), ('wheat (ripe)', 'wheat'), ('young crop', 'young')):
        p = Plot(96, 96)
        hgt = p.y * 0.8 + 9 * np.sin(p.x / 30.0)
        if kind == 'plough':
            plough(p, np.ones((96, 96), bool), hgt, 4)
        else:
            crop(p, np.ones((96, 96), bool), hgt, 5, kind=kind if kind == 'young' else 'wheat')
        out.append(('farm', name, p, (14, 14, 86, 86), 'ground'))
    p = Plot(96, 96)
    margin(p, np.ones((96, 96), bool), 6)
    out.append(('farm', 'field margin', p, (8, 8, 88, 88), 'ground'))
    p = _meadow_plot(W, 72, 8)
    hedgerow(p, [(-10, 44), (60, 42), (180, 46)], 16, 10, seed=12, gaps=(40,))
    out.append(('farm', 'hedgerow with a gap', p, (60, 22, 160, 58), 'hedge'))
    p = _meadow_plot(W, 72, 9)
    hedgerow(p, [(-10, 46), (180, 46)], 16, 10, seed=13, gate_at=90)
    out.append(('farm', 'five-bar gate in a hedge', p, None, 'hedge'))
    p = _meadow_plot(W, 72, 10)
    track(p, [(-10, 40), (80, 34), (180, 40)], 24, seed=14, puddles=2)
    out.append(('farm', 'farm track: ruts, crown, puddles', p, (8, 24, 160, 58), 'ground'))
    # transitions
    p = Plot(336, 112)
    hay_meadow(p, np.ones((112, 336), bool), 15)
    t = np.clip((p.x - 80) / 180.0, 0, 1)
    snap = (p.f.copy(), p.t.copy())

    def pa(q, mm):
        q.f[:], q.t[:] = snap
    took = blend(p, np.ones((112, 336), bool), t, pa, lambda q, mm: heath(q, mm, 16), 17)
    plant(p, took | (t > 0.2), 1300, [lambda s: shrub('gorse', s)], 18, density=np.clip(t * 1.1, 0, 0.9))
    plant(p, (took | (t > 0.3)) & ~p.solid, 2400, [birch], 19, density=np.clip(t * 1.2, 0, 1))
    out.append(('band', 'meadow into the Brackens\' heath', p, (260, 8, 330, 104), 'ground'))
    p = Plot(336, 132)
    hay_meadow(p, np.ones((132, 336), bool), 20)
    t = np.clip((p.x - 60) / 220.0, 0, 1)
    wood_edge(p, np.ones((132, 336), bool), t, 21)
    out.append(('band', 'meadow into the Fern hills\' wood', p, None, 'ground'))
    return out


def eastward_crop(key, size=(64, 64)):
    """A crop of an official reference screenshot at our scale (an adult 25 px, each pixel
    the commonest colour of its block), from a local copy fetched by detail_bar's URLs into
    REF_DIR; None if it is not there. The images never go into the repository."""
    import detail_bar as db
    b = db.load()['baselines'].get(key)
    ref_dir = os.environ.get('REF_DIR', os.path.join(tempfile.gettempdir(), 'napattack-refs'))
    if not b:
        return None
    path = os.path.join(ref_dir, b['url'].rsplit('/', 1)[1])
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert('RGB')
    f = b['adult_px'] / 25.0
    x0, y0 = b['box'][0], b['box'][1]
    w, h = int(size[0] * f), int(size[1] * f)
    crop = im.crop((x0, y0, min(im.width, x0 + w), min(im.height, y0 + h)))
    key_ = db.to_scale(crop, b['adult_px'])
    out = np.zeros(key_.shape + (3,), np.uint8)
    for yy in range(key_.shape[0]):
        for xx in range(key_.shape[1]):
            k = int(key_[yy, xx])
            out[yy, xx] = ((k >> 8) * 16 + 8, ((k >> 4) & 15) * 16 + 8, (k & 15) * 16 + 8)
    return Image.fromarray(out, 'RGB')


REF_FOR = {'stream': 'eastward-13-canal', 'ground': 'eastward-37-lawn-flowers', 'hedge': 'eastward-17-bushes',
           'tree': 'eastward-13-pine', 'water': 'eastward-17-pond'}


def _label(img, text, xy, fill=(240, 236, 228)):
    d = ImageDraw.Draw(img)
    x, y = xy
    d.text((x + 1, y + 1), text, fill=(20, 16, 20))
    d.text((x, y), text, fill=fill)


def bar_rows(items):
    import detail_bar as db
    rows = []
    for (group, name, p, box, kind) in items:
        if box is None:
            rows.append((name, kind, None, None, lone_share(p)))
            continue
        ok, c, lines = db.check_image(p.image(), box, kind)
        rows.append((name, kind, ok, c, lone_share(p)))
    return rows


def kit_sheet(items, rows, scale=2):
    """Every piece at `scale`, grouped, each labelled with its detail bar result."""
    import detail_bar as db
    pad, lab = 10, 28
    groups = ['water', 'edge', 'farm', 'band']
    titles = {'water': 'Water: river, stream, ford, mill race, canal', 'edge': "The water's edge",
              'farm': 'Meadow and farmland', 'band': 'Transitions: bands, not lines'}
    maxw = 1400
    layout, y = [], 0
    for g in groups:
        y += 30
        x, rowh = pad, 0
        for it, r in zip(items, rows):
            if it[0] != g:
                continue
            w, h = it[2].w * scale, it[2].h * scale
            if x + w > maxw:
                x, y = pad, y + rowh + lab + pad
                rowh = 0
            layout.append((g, it, r, x, y))
            x += w + pad
            rowh = max(rowh, h)
        y += rowh + lab + pad
    sheet = Image.new('RGB', (maxw + pad, y + pad), (46, 40, 52))
    d = ImageDraw.Draw(sheet)
    seen = set()
    for (g, it, r, x, y0) in layout:
        if g not in seen:
            _label(sheet, titles[g], (pad, y0 - 22), (250, 214, 140))
            seen.add(g)
        img = it[2].image(scale)
        sheet.paste(img, (x, y0))
        box = it[3]
        if box:
            d.rectangle([x + box[0] * scale, y0 + box[1] * scale, x + box[2] * scale - 1, y0 + box[3] * scale - 1],
                        outline=(250, 214, 140))
        name, kind, ok, c, lone = r
        ref = db.bar(kind) if c else None
        txt = it[1]
        if c:
            sub = (f'{kind} t{c["tones"]:.0f}/{ref["tones"]:.0f} s{c["shapes"]:.0f}/{ref["shapes"]:.0f} '
                   f'd{c["dressing"]:.0f}/{ref["dressing"]:.0f} {"PASS" if ok else "FAIL"}')
        else:
            sub = 'by eye'
        _label(sheet, txt[:int(img.width / 6)], (x, y0 + img.height + 2))
        _label(sheet, sub, (x, y0 + img.height + 14), (200, 200, 210))
    return sheet


def compare_sheet(items, rows, scale=4):
    """Each measured piece beside an official Eastward crop of the same kind of surface at
    the same character height (an adult 25 px), both at `scale`."""
    tiles = []
    for it, r in zip(items, rows):
        if it[3] is None or r[3] is None:
            continue
        import detail_bar as db
        x0, y0, x1, y1 = it[3]
        rb = db.load()['baselines'][REF_FOR[it[4]]]
        rw = int((rb['box'][2] - rb['box'][0]) * 25 / rb['adult_px'])
        rh = int((rb['box'][3] - rb['box'][1]) * 25 / rb['adult_px'])
        w, h = min(64, x1 - x0, rw), min(64, y1 - y0, rh)
        ours = it[2].image().crop((x0, y0, x0 + w, y0 + h))
        ref = eastward_crop(REF_FOR[it[4]], (w, h))
        tiles.append((it[1], it[4], ours, ref, r))
    if not tiles:
        return None
    tw = max(o.width + (r.width if r is not None else 0) for (_n, _k, o, r, _r) in tiles) * scale + 24
    th = max(max(o.height, r.height if r is not None else 0) for (_n, _k, o, r, _r) in tiles) * scale + 36
    cols = 3
    rows_n = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw + 10, rows_n * th + 10), (46, 40, 52))
    import detail_bar as db
    for i, (name, kind, ours, ref, r) in enumerate(tiles):
        x, y = 10 + (i % cols) * tw, 10 + (i // cols) * th
        sheet.paste(ours.resize((ours.width * scale, ours.height * scale), Image.NEAREST), (x, y))
        hh = ours.height
        if ref is not None:
            sheet.paste(ref.resize((ref.width * scale, ref.height * scale), Image.NEAREST),
                        (x + ours.width * scale + 6, y))
            hh = max(hh, ref.height)
        c, b = r[3], db.bar(kind)
        _label(sheet, f'{name[:30]} | Eastward {REF_FOR[kind][9:]}', (x, y + hh * scale + 2))
        _label(sheet, f'tones {c["tones"]:.1f}/{b["tones"]:.1f}  shapes {c["shapes"]:.1f}/{b["shapes"]:.1f}  '
               f'dressing {c["dressing"]:.1f}/{b["dressing"]:.1f}', (x, y + hh * scale + 15), (200, 200, 210))
    return sheet


def sample_preview(p, scale=2, people=True):
    """The sample at `scale` with three residents standing in it for scale (preview only)."""
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in (('angler', (300, 250)), ('hiker', (180, 262)), ('gardener', (226, 248))):
            path = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')  # ledger: compare (scale figures)
            if os.path.exists(path):
                r = Image.open(path).convert('RGBA')
                r = r.resize((r.width // 4, r.height // 4), Image.NEAREST)
                img.alpha_composite(r, (x - r.width // 2, y - r.height))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


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


def check() -> list:
    """The kit's crossing contract: water blocks a walker unless a crossing is declared.
    A track painted over a plain river leaves it blocking; a ford opens it."""
    faults = []
    for ford_at in (None, 88):
        p = Plot(128, 128)
        river(p, [(-24, 64), (152, 64)], width=40, seed=3, ford_at=ford_at)
        before_wet = p.wet.copy()
        crossed_before = _reaches(p.walk, (64, 16), (64, 112))
        track(p, [(64, -24), (64, 152)], width=24, puddles=0, seed=7)
        crossed = _reaches(p.walk, (64, 16), (64, 112))
        reopened = int((p.walk & before_wet & ~p.crossing).sum())
        if ford_at is None:
            if crossed_before or crossed:
                faults.append('a plain river can be walked across (no ford declared)')
            if reopened:
                faults.append(f'a track over a plain river reopened {reopened} wet pixels')
        else:
            if not (crossed_before and crossed):
                faults.append('the declared ford cannot be walked across')
            if reopened:
                faults.append(f'{reopened} wet pixels outside the ford became walkable')
    # the sample: the lane crosses the Sleepwater only at its ford, and no other water opens
    p, parts = sample()
    lane = parts['lane']
    a, b = [tuple(int(v) for v in lane.c[i]) for i in (60, lane.length - 80)]
    if not _reaches(p.walk, a, b):
        faults.append('the sample lane cannot be walked across its ford')
    stray = int((p.walk & p.wet & ~p.crossing).sum())
    if stray:
        faults.append(f'{stray} wet pixels in the sample are walkable outside a declared crossing')
    return faults


def main(argv):
    if '--check' in argv:
        faults = check()
        for f in faults:
            print('FAULT:', f)
        print('river_kit crossing check:', 'pass' if not faults else f'{len(faults)} faults')
        return 1 if faults else 0
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-river-kit')
    os.makedirs(out, exist_ok=True)
    items = pieces()
    rows = bar_rows(items)
    kit_sheet(items, rows).save(os.path.join(out, 'kit-sheet.png'))
    cmp = compare_sheet(items, rows)
    if cmp is not None:
        cmp.save(os.path.join(out, 'compare-eastward.png'))
    print(f'{"piece":58s} {"kind":7s} tones  shapes dressing isolated cluster  lone   result')
    for (name, kind, ok, c, lone) in rows:
        if c is None:
            print(f'{name:58s} {kind:7s} (judged by eye)                              {lone:.3f}')
            continue
        print(f'{name:58s} {kind:7s} {c["tones"]:5.1f} {c["shapes"]:6.1f} {c["dressing"]:7.1f} '
              f'{c["isolated"]:8.3f} {c["cluster"]:7.1f}  {lone:.3f}  {"PASS" if ok else "FAIL"}')
    p, parts = sample()
    p.image().save(os.path.join(out, 'sample.png'))
    sample_preview(p, 2).save(os.path.join(out, 'sample-2x.png'))
    frames, box = flow_frames(p)
    big = [f.resize((f.width, f.height), Image.NEAREST) for f in frames]
    big[0].save(os.path.join(out, 'sample-flow.gif'), save_all=True, append_images=big[1:], duration=150, loop=0)
    import detail_bar as db
    print('sample boxes:')
    ch = parts['river']
    best = None
    for i in range(40, ch.length - 40, 10):
        cx, cy = ch.c[i]
        bx = (int(cx) - 40, int(cy) - 40, int(cx) + 40, int(cy) + 40)
        if bx[0] < 0 or bx[1] < 0 or bx[2] > p.w or bx[3] > p.h:
            continue
        sol = p.solid[bx[1]:bx[3], bx[0]:bx[2]].mean() + (ch.bend()[int(cy), int(cx)] < 0.5)
        if best is None or sol < best[0]:
            best = (sol, bx)
    for name, box, kind in (('the Sleepwater at a bend', best[1], 'stream'),
                            ('hay meadow', (190, 40, 290, 140), 'ground'),
                            ('wheat', (80, 340, 240, 500), 'ground'),
                            ('heath band', (10, 20, 120, 120), 'ground'),
                            ('pasture', (520, 440, 630, 560), 'ground')):
        ok, c, lines = db.check_image(p.image(), box, kind)
        print(f'  {name:28s} {kind:7s} ' + '; '.join(lines) + f'  {"PASS" if ok else "FAIL"}')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
