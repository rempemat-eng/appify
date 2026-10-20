"""The dry and fire kit: the pieces Sunstone Reach and the fire country are painted with.

Claude D's lane (Sunstone Reach, Hearthold and the fire country). World plan v5.1 (PR #96,
arrangement A, Matt 20 Oct): Sunstone is the rain shadow of the Ember arc, west of the home
valley. East to west it opens from meadow to steppe, steppe to scrub with snowmelt oases
(Palm Spring, Dust Gulch on the Amber's fan), badlands and mesas where the Amber and the Rift
cut down, the salt lake where the Amber ends, then desert and the dune sea. Mount Ember
stands on the south-west coastal arc: ash blown north and thinning, old crusted flows with
scrub on them, cinder cones and a fumarole field on the north flank, a dead forest where a
flow ran through the coastal woods, hot springs on the seaward side, and two young flows as
the barrier. Matt, 20 Oct 14:45 and 15:50: transitions "right" and "distinct", verticality
"super important", "a decent amount of things in each of the major biomes", obstacles to go
round and little paths. This module is the kit those places are drawn with; nothing in the
game reads it yet (the zones wire it in once the v5.1 layouts land).

Everything is drawn in the house style (docs/vision/house-style.md, PR #121): every pixel is
a tone of a house ramp (art/house-palette.json) or a family's edge tone; shade and light move
along the ramps (no RGB arithmetic); texture is clusters of two to four pixels (no speckle);
walkable ground stays calm (body tone 3, patches a tone off, mostly sibling swaps); light
comes from the upper left; cast shadows step the ground two tones down and throw a little
longer in the desert sun. The Reach builds with its three accents (bleached, adobe, cactus)
and the core families (sand, path, earth, clay, stone, grass, leaf, plaster); the fire
country with its own (ash, basalt) and the lava glow.

Verticality is the soft grid's (verticality.md 4f, terrace.py on PR #90): a tier is one face,
40 px for a mesa (size guide: "Tier face, city, mesa 40") and 32 elsewhere; only the south
face is a face; west and east ends are 5 px side bands, lit on the west and in the two
darkest tones on the east; a face's foot is dark and gathers talus; cast shadows fall down
and to the right. `tiers()` builds that from a plan height map (one integer a pixel, the tier
each patch of ground stands on), so mesas, buttes, canyon walls and lava terraces share one
construction. Sizes follow docs/vision/size-guide.md (PR #124): an adult 25 px, a canyon floor
48 to 96, a palm 56 to 104, a saguaro 36 to 72, a bush 12 to 28, a boulder 16 to 32, a snag
32 to 80, basalt columns 8 to 12 across, lava channels 24 to 64 with a crust band of 4 to 8
and ash 16 to 32 before any plant, nothing green within 64 of lava.

The model is Claude E's river kit's (#133, scripts/art/river_kit.py): a `Plot` holds the
house ramp and tone of every pixel, pieces paint masks into it, standing things are
`Sprite`s pasted with an edge-tone outline and a cast shadow. The shared core (noise, the
plot, clusters, outline, shadow, sprites, bands) is copied here so the two kits stay
independent until both land; once they do, it can move into one module both import.

The pieces (each with a seed, all deterministic):
- dry grounds: `steppe()` short straw grass with bunchgrass and bare patches; `scrub()`
  sage and creosote over hardpan; `hardpan()` cracked clay plates; `gravel()` desert
  pavement; `dunes()` transverse dunes with crisp crests, lit windward slopes and shaded
  slip faces; `salt_pan()` crust polygons with raised rims and a damp margin; `badlands()`
  banded rilled slopes; `wash()` a dry wash with braided gravel bars and a low cut bank.
- standing things: `palm()`, `saguaro()`, `barrel()`, `prickly_pear()`, `sage()`,
  `creosote()`, `rabbitbrush()`, `reeds()`, `boulder()`, `snag()`, `fireweed()`, `log()`.
- height: `tiers()` (mesas and buttes with layered strata in stepped faces, canyon walls,
  lava terraces), `talus()` at every foot, `stair()` cut through a face.
- water in the desert: `oasis()` a spring pool with reeds and palms, an adobe-lined
  irrigation channel, the green fading downstream.
- the fire country: `ash()` ash ground thinning over what lies under it; `old_flow()`
  crusted ropy basalt with lichen and scrub at its edges; `young_flow()` dark crust plates
  with glowing cracks and an open channel (moving through water_flow.py's lava path:
  `lava_frames()`); `columns()` basalt columns and `causeway()` a path of column tops;
  `cinder_cone()`; `fumarole()` with steam (`steam_frames()`); `hot_spring()` travertine
  terraces; `dead_forest()`.
- transitions: `blend()` mixes two grounds over a band with outliers on both sides;
  `steppe_to_desert()` and `scrub_to_ash()` are the two bands.

Motion is finite and respects reduced motion: lava and steam are overlay frames (8 frames,
150 ms) that the renderer holds on frame 0 with reduced motion or when the screen is
inactive (water_flow.py's contract).

Run:
    python3 scripts/art/dry_kit.py --check     (walk and heat contracts; exits non-zero on a fault)
    python3 scripts/art/dry_kit.py [OUT_DIR]
writes OUT_DIR/kit-sheet.png (every piece at 2x, labelled with its detail bar result),
OUT_DIR/compare-eastward.png (each measured piece beside an official Eastward crop of the
same kind at the same character height, when the reference screenshots are in REF_DIR),
OUT_DIR/sample.png and sample-2x.png (a canyon descent to an oasis under a mesa, 640 x 576),
OUT_DIR/sample-motion.gif, and prints the bar and lone-pixel counts for every piece. Default
OUT_DIR: napattack-dry-kit in the system's temp folder, never the repository.
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

# The soft grid (verticality.md 4f; terrace.py on PR #90)
GRID = 8
FACE = 32          # a tier's face in the open country
FACE_MESA = 40     # a mesa's or canyon's face (size guide: "Tier face, city, mesa 40")
STRIP = 5          # a side band: 0.2 of an adult
DESERT_THROW = 1.3  # desert shadows throw a little longer (house rule 6)


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


def dist_to(m, cap=64):
    """Px from each pixel to the nearest pixel of m (0 inside), capped; a chamfer walk."""
    big = cap + 1.0
    d = np.where(np.asarray(m, bool), 0.0, big)
    for _ in range(2):
        for (dx, dy, c) in ((1, 0, 1), (0, 1, 1), (1, 1, 1.414), (-1, 1, 1.414)):
            for _r in range(cap):
                n = np.minimum(shift(d, dx, dy, big), shift(d, -dx, -dy, big)) + c
                nd = np.minimum(d, n)
                if (nd == d).all():
                    break
                d = nd
    return np.minimum(d, cap)


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
        return (self.f.copy(), self.t.copy(), self.solid.copy(), self.walk.copy())

    def restore(self, s, m=None):
        if m is None:
            self.f[:], self.t[:], self.solid[:], self.walk[:] = s
        else:
            for a, v in zip(('f', 't', 'solid', 'walk'), s):
                getattr(self, a)[m] = v[m]


# Cluster shapes: two to four pixels, never one (house rule 4).
DOMINOES = (((0, 0), (1, 0)), ((0, 0), (0, 1)))
SMALL = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)),
         ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1)))
FLAT = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1)))
BLADES = (((0, 0), (0, -1)), ((0, 0), (0, -1), (0, -2)), ((0, 0), (0, -1), (1, -2)),
          ((0, 0), (0, -1), (-1, -2)), ((0, 0), (1, 0), (0, -1)))


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


def lone_share(p: Plot, m=None) -> float:
    key = p.f.astype(np.int32) * 8 + p.t
    nb = [shift(key, dx, dy, -1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    lone = np.all([key != n for n in nb], axis=0)
    m = np.ones(key.shape, bool) if m is None else m
    return float(lone[m].mean())


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
    pts = []
    for gy in range(0, h, cell):
        for gx in range(0, w, cell):
            x = gx + int(hash01(gx, gy, seed) * cell)
            y = gy + int(hash01(gx, gy, seed + 1) * cell)
            if x < w and y < h and m[y, x]:
                pts.append((x, y))
    return pts


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
        nx = np.clip((xs + z * k * DESERT_THROW).astype(int), 0, self.w - 1)
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


def plant(p: Plot, m, every, makers, seed, density=None, taken=None, gap=3, k=2):
    """Scatter sprites over a mask, about one per `every` px, keeping a clear gap round each;
    `density` (an array 0..1) thins them where it is low. Returns the feet."""
    feet = []
    taken = np.zeros(p.f.shape, bool) if taken is None else taken
    for i, (x, y) in enumerate(_scatter(m, every, seed)):
        if density is not None and hash01(x, y, seed + 1) > density[y, x]:
            continue
        if taken[y, x] or p.solid[y, x]:
            continue
        mk = makers[int(hash01(x, y, seed + 2) * len(makers))]
        made = mk(seed + i)
        sp, sh = made[0], made[1]
        full = paste(p, sp, x, y, shadow=sh, k=k, block=made[2] if len(made) > 2 else None)
        taken |= dilate(full, gap)
        feet.append((x, y))
    return feet


# --- small ground things ----------------------------------------------------------------------
def pebble(p: Plot, x, y, ramp='stone', w=3, h=2, shadow=True, k=2):
    """A pebble or cobble drawn into the ground: lit top-left, body, dark lower-right, its
    shadow a short step on the ground to the right and below. Never smaller than 2 x 2."""
    w, h = max(2, w), max(2, h)
    pts = []
    for j in range(h):
        for i in range(w):
            if (i == 0 or i == w - 1) and (j == 0 or j == h - 1) and w > 2 and h > 2:
                continue                                   # corners knocked off
            pts.append((i, j))
    sel = np.zeros(p.f.shape, bool)
    for (i, j) in pts:
        px, py = x + i, y + j
        if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
            tone = 4 if (i + j == 0 or (j == 0 and i < w // 2) or (i == 0 and j < h // 2 and h > 2)) else \
                2 if (i == w - 1 or j == h - 1) else 3
            if w == 2 and h == 2:
                tone = (4, 3, 3, 2)[i + 2 * j]
            p.f[py, px], p.t[py, px] = IDX[ramp], tone
            sel[py, px] = True
    if shadow and sel.any():
        sh = (shift(sel, 1, 0, False) | shift(sel, 1, 1, False)) & ~sel
        cast(p, sh & ~shift(sel, 0, -1, False), 1 if k < 2 else 2)
    return sel


def tussock(p: Plot, x, y, seed=0, tips='sand', body='grass_warm', w=None):
    """A bunchgrass clump: a fountain of blades, straw tips lit on the west, a dark base and
    its own shade to the east."""
    w = w or 5 + int(hash01(x, y, seed) * 3)
    for i in range(w):
        hgt = 2 + int(3 * math.sin(math.pi * (i + 0.5) / w)) + int(hash01(x + i, y, seed + 1) * 2)
        for j in range(hgt):
            px, py = x + i, y - j
            if 0 <= px < p.w and 0 <= py < p.h and not p.solid[py, px]:
                k = 1 if j == 0 else 2 if i > w * 0.6 else 3
                fam = body
                if j >= hgt - 2:
                    fam, k = tips, (4 if i < w * 0.6 else 3)
                p.f[py, px], p.t[py, px] = IDX[fam], k
    for i in range(1, w + 2):
        if 0 <= y + 1 < p.h and 0 <= x + i < p.w and not p.solid[y + 1, x + i]:
            p.step(_pt(p, x + i, y + 1), -1)


def voronoi(p: Plot, cell, seed, jitter=0.85):
    """Cells of a jittered grid: for every pixel the distance to its nearest centre (d1) and
    second nearest (d2), the cell's id and the vector from its centre to the neighbour's."""
    gx, gy = np.floor(p.x / cell).astype(int), np.floor(p.y / cell).astype(int)
    d1 = np.full(p.f.shape, 1e9)
    d2 = np.full(p.f.shape, 1e9)
    c1x = np.zeros(p.f.shape)
    c1y = np.zeros(p.f.shape)
    c2x = np.zeros(p.f.shape)
    c2y = np.zeros(p.f.shape)
    cid = np.zeros(p.f.shape, np.int64)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = gx + ox, gy + oy
            px = (cx + 0.5 + (hash01(cx, cy, seed) - 0.5) * jitter) * cell
            py = (cy + 0.5 + (hash01(cx, cy, seed + 1) - 0.5) * jitter) * cell
            d = np.hypot(p.x + 0.5 - px, p.y + 0.5 - py)
            closer = d < d1
            second = ~closer & (d < d2)
            d2 = np.where(closer, d1, np.where(second, d, d2))
            c2x = np.where(closer, c1x, np.where(second, px, c2x))
            c2y = np.where(closer, c1y, np.where(second, py, c2y))
            d1 = np.where(closer, d, d1)
            c1x = np.where(closer, px, c1x)
            c1y = np.where(closer, py, c1y)
            cid = np.where(closer, (cx * 7919 + cy * 104729) & 0xFFFFF, cid)
    return d1, d2, cid, c2x - c1x, c2y - c1y


# --- dry grounds -------------------------------------------------------------------------------
def steppe(p: Plot, m, seed=1, tussocks=True):
    """The steppe (Rift country): short grass yellowing to straw, pale green in the hollows,
    bunchgrass tussocks, blades in strokes with lit tips, small bare trodden patches."""
    m = np.asarray(m, bool)
    base(p, m, [('grass_warm', 0.45), ('sand_cool', 0.12), ('bleached_warm', 0.15), ('sand', 0.28)], seed, 12,
         light=0.74, dark=0.24)
    texture(p, m, seed + 1, swaps=0.14, ups=0.02, downs=0.02)
    stamp(p, m, 0.03, seed + 2, BLADES, ramp='sand', tone=4, same_family=False)
    stamp(p, m, 0.018, seed + 3, BLADES, ramp='grass_cool', tone=3, same_family=False)
    stamp(p, m, 0.012, seed + 4, BLADES, ramp='grass_warm', tone=4, same_family=False)
    bare = m & (fbm(p.x, p.y, 11, seed + 5) > 0.70) & erode(m, 4)
    bare = dilate(erode(bare, 1), 1)
    p.put(bare, 'path_warm', 3)
    stamp(p, bare, 0.16, seed + 6, FLAT, swap='mix')
    stamp(p, bare, 0.03, seed + 7, FLAT, dt=-1)
    p.step(bare & ~shift(bare, 0, 1, False), -1)              # the grass's lip over the bare patch
    if tussocks:
        for (x, y) in _scatter(m & ~bare, 300, seed + 8):
            tussock(p, x, y, seed + x)
    for (x, y) in _scatter(m & erode(bare, 1), 140, seed + 9):
        pebble(p, x, y, ('stone', 'adobe_cool', 'stone_warm')[(x + y) % 3], 2 + (x % 2), 2, k=1)
    despeckle(p, m & ~p.solid)


def hardpan_ground(p: Plot, m, seed=2, ramp='path'):
    """Packed desert hardpan without its cracks: pale, calm, a little gravel."""
    m = np.asarray(m, bool)
    base(p, m, [(f'{ramp}_warm', 0.3), ('sand_cool', 0.25), (ramp, 0.25), ('sand', 0.2)], seed, 11)
    texture(p, m, seed + 1, swaps=0.12, ups=0.025, downs=0.03, shapes=FLAT)


def scrub_plants(p: Plot, m, seed=3, every=520, density=None):
    makers = [sage, sage, creosote, rabbitbrush, prickly_pear, sage, creosote, tussock_sprite]
    return plant(p, m, every, makers, seed, density=density)


def scrub(p: Plot, m, seed=3, every=900):
    """Sage scrub on hardpan: silver sage and dark creosote in loose groups (more where the
    ground holds water), rabbitbrush in flower, prickly pear, dry grass between, gravel."""
    m = np.asarray(m, bool)
    hardpan_ground(p, m, seed)
    grassy = m & (fbm(p.x, p.y, 16, seed + 2) > 0.5)
    stamp(p, grassy, 0.03, seed + 3, BLADES, ramp='grass_warm', tone=3, same_family=False)
    stamp(p, grassy, 0.02, seed + 4, BLADES, ramp='sand', tone=4, same_family=False)
    for (x, y) in _scatter(m, 150, seed + 5):
        pebble(p, x, y, ('stone', 'adobe_cool', 'basalt_warm', 'stone_cool')[(x * 3 + y) % 4], 2 + (x % 2), 2, k=1)
    clump = np.clip(fbm(p.x, p.y, 44, seed + 6) * 2.4 - 0.75, 0.02, 1)
    scrub_plants(p, m, seed + 7, every, density=clump)
    despeckle(p, m & ~p.solid)


def hardpan(p: Plot, m, seed=4, cell=15, ramp='adobe'):
    """A cracked clay pan: plates 10 to 20 px, each a sibling, curling up at their edges
    (the north-west lip lit, the south-east lip in shade), the cracks between dark, finer
    cracks inside the larger plates, a little blown sand gathered in the cracks."""
    m = np.asarray(m, bool)
    d1, d2, cid, vx, vy = voronoi(p, cell, seed)
    pick = hash01(cid, 0, seed + 1)
    fam = np.where(pick < 0.33, IDX[f'{ramp}_warm'], np.where(pick < 0.66, IDX[ramp], IDX['path_warm']))
    p.f[m] = fam[m]
    p.t[m] = 3
    gap = d2 - d1
    crack = m & (gap < 1.15)
    rim = m & ~crack & (gap < 3.0)
    # A plate curls up at its edges. Where the crack lies to its south-east the lip rises
    # towards it and faces the light (lit); where the crack lies to its north-west the lip
    # faces away (shaded).
    se = (vx + vy) > 0
    p.step(rim & se & (gap < 2.2), 1)
    p.step(rim & ~se & (gap < 2.2), -1)
    inner = m & ~crack & ~rim
    stamp(p, inner, 0.08, seed + 2, FLAT, swap='mix')
    stamp(p, inner, 0.02, seed + 3, FLAT, dt=1)
    # fine cracks inside big plates
    fine = m & ~crack & (np.abs(fbm(p.x, p.y, 7, seed + 4) - 0.5) < 0.018) & (d1 > 4)
    p.step(fine, -1)
    p.put(crack, 'earth_cool', 2)
    p.put(crack & (gap < 0.55), 'earth_cool', 1)
    sandy = crack & (hash01(p.x // 3, p.y // 3, seed + 5) < 0.35)
    p.put(sandy, 'sand_cool', 2)
    despeckle(p, m)


def gravel(p: Plot, m, seed=5, every=40):
    """Desert pavement: packed sand between a loose mosaic of pebbles and cobbles, brown
    with desert varnish on their tops, a few pale where they were turned over, grit in
    pairs between them."""
    m = np.asarray(m, bool)
    base(p, m, [('sand_warm', 0.3), ('adobe_cool', 0.2), ('sand', 0.3), ('sand_cool', 0.2)], seed, 9)
    texture(p, m, seed + 1, swaps=0.10, ups=0.02, downs=0.035, shapes=FLAT)
    rams = ('adobe_cool', 'stone_warm', 'adobe', 'earth_warm', 'stone', 'clay_cool', 'adobe_cool', 'bleached')
    for (x, y) in _scatter(m, every, seed + 2, margin=2):
        r = hash01(x, y, seed + 3)
        w = 2 + int(r * 4)
        h = 2 + int(hash01(x, y, seed + 4) * 2)
        pebble(p, x, y, rams[int(hash01(x, y, seed + 5) * len(rams))], w, h)
    despeckle(p, m & ~p.solid)


def dunes(p: Plot, m, seed=6, wave=46, wind=(1.0, 0.25)):
    """Transverse dunes (the dune sea): the wind from the west builds long gentle windward
    slopes, lit, with ripples across them; each crest is a crisp line, lit on its windward
    lip; the slip face beyond falls steep into shade (the hard terminator), lightening to
    its toe; crests wander and fork. Dune crests stop a walker (the sea is seen, not crossed)."""
    m = np.asarray(m, bool)
    wx, wy = wind
    nrm = math.hypot(wx, wy)
    wx, wy = wx / nrm, wy / nrm
    along = p.x * wx + p.y * wy
    across = -p.x * wy + p.y * wx
    warp = (fbm(across * 0.9, along * 0.15, 46, seed) - 0.5) * 70 + (fbm(p.x, p.y, 14, seed + 1) - 0.5) * 8
    lam = wave * (0.85 + 0.35 * fbm(across, 0, 90, seed + 2))
    ph = ((along + warp) / lam) % 1.0
    crest_at = 0.76
    wind_side = ph < crest_at
    slip = ~wind_side
    sp = np.where(wind_side, ph / crest_at, (ph - crest_at) / (1 - crest_at))
    f = np.where(fbm(p.x, p.y, 9, seed + 3) < 0.5, IDX['sand'], IDX['sand_warm'])
    f = np.where(fbm(p.x, p.y, 30, seed + 4) > 0.6, IDX['sand_cool'], f)
    f = np.where(fbm(p.x, p.y, 22, seed + 14) > 0.68, IDX['adobe_warm'], f)     # redder sand in the swales
    tone = np.full(p.f.shape, 3, np.int8)
    tone = np.where(wind_side & (sp > 0.55), 4, tone)
    tone = np.where(wind_side & (sp > 0.93), 5, tone)          # the crest's lit lip
    tone = np.where(slip & (sp < 0.45), 1, tone)               # the slip face's shade core
    tone = np.where(slip & (sp >= 0.45) & (sp < 0.8), 2, tone)
    tone = np.where(wind_side & (sp < 0.12), 2, tone)          # the trough where two dunes meet
    p.f[m] = f[m]
    p.t[m] = tone[m]
    # ripples on the windward slopes: lines across the wind, one tone up, in the lit sibling
    rip = wind_side & (sp > 0.2) & (sp < 0.85) & (((along + warp * 0.6) / 7.0 + fbm(p.x, p.y, 13, seed + 5) * 1.6) % 1.0 < 0.2)
    p.step(m & rip & (tone == 3), 1)
    p.step(m & rip & (tone == 4), -1)
    stamp(p, m & wind_side & (tone >= 3), 0.12, seed + 6, FLAT, swap='mix')
    stamp(p, m & slip & (tone == 2), 0.06, seed + 7, DOMINOES, dt=-1)
    # avalanche streaks down the slip faces, grains in pairs, dune grass in the troughs
    av = m & slip & (sp > 0.1) & (sp < 0.85) & (((across * 0.5 + fbm(p.x, p.y, 7, seed + 8) * 6) % 5) < 1)
    p.step(av & (p.t <= 2), 1)
    stamp(p, m & wind_side & (sp < 0.6), 0.03, seed + 9, DOMINOES, dt=-1)
    stamp(p, m & wind_side & (sp < 0.3), 0.05, seed + 15, FLAT, ramp='adobe', tone=3, same_family=False)
    stamp(p, m & wind_side & (sp > 0.85), 0.08, seed + 16, DOMINOES, ramp='plaster', tone=5, same_family=False)
    stamp(p, m & slip & (sp > 0.7), 0.06, seed + 17, FLAT, ramp='sand_cool', tone=3, same_family=False)
    trough = m & wind_side & (sp < 0.12) & (fbm(p.x, p.y, 25, seed + 10) > 0.55)
    stamp(p, trough, 0.05, seed + 11, BLADES, ramp='grass_warm', tone=3, same_family=False)
    stamp(p, trough, 0.03, seed + 12, BLADES, ramp='sand_warm', tone=4, same_family=False)
    crest = m & wind_side & (sp > 0.93)
    p.walk &= ~(m & dilate(crest, 1))
    despeckle(p, m)


def salt_pan(p: Plot, m, seed=7, cell=19):
    """A salt pan where the Amber ends: a white crust in polygons 14 to 24 px across with
    raised pressure ridges (the north-west side of each ridge lit, the south-east side in
    blue-violet shade), flat cells with faint bloom, and a damp brown margin with mud cracks
    where the crust thins at the shore."""
    m = np.asarray(m, bool)
    d1, d2, cid, vx, vy = voronoi(p, cell, seed, 0.9)
    pick = hash01(cid, 1, seed + 1)
    fam = np.where(pick < 0.55, IDX['snow_warm'], np.where(pick < 0.8, IDX['snow'], IDX['snow_cool']))
    p.f[m] = fam[m]
    p.t[m] = np.where(pick > 0.8, 3, 4)[m]
    p.put(m & (pick > 0.92), 'plaster_cool', 4)                  # a cell stained by brine
    p.put(m & (pick < 0.08), 'plaster', 5)                       # fresh bloom
    gap = d2 - d1 + (fbm(p.x, p.y, 6, seed + 9) - 0.5) * 1.2
    ridge = m & (gap < 2.0)
    se = (vx + vy) > 0                    # neighbour south-east: this half faces north-west, lit
    p.put(ridge & se, 'plaster', 5)
    p.put(ridge & se & (hash01(cid, 4, seed + 18) < 0.45), 'snow_warm', 5)
    p.put(ridge & ~se, 'snow_cool', 3)
    p.put(ridge & ~se & (gap < 0.9), 'snow_cool', 2)
    flat = m & ~ridge
    stamp(p, flat, 0.12, seed + 2, FLAT, swap='mix')
    stamp(p, flat & (d1 > cell * 0.3), 0.04, seed + 3, FLAT, dt=-1)
    stamp(p, flat, 0.03, seed + 13, DOMINOES, ramp='plaster', tone=5, same_family=False)
    # young cracks splitting the larger polygons, a hairline with a lit lip
    sub = flat & (np.abs(fbm(p.x, p.y, 8, seed + 12) - 0.5) < 0.02) & (d1 > 4)
    p.put(sub, 'snow_cool', 2)
    p.step(shift(sub, 0, 1, False) & flat & ~sub, 1)
    # sand blown onto the crust in small drifts, and brine seeping up dark in a few cells
    blown = flat & (fbm(p.x, p.y, 14, seed + 14) > 0.62)
    stamp(p, blown, 0.12, seed + 15, FLAT, ramp='sand_cool', tone=4, same_family=False)
    stamp(p, blown, 0.05, seed + 16, DOMINOES, ramp='sand', tone=3, same_family=False)
    brine = flat & (hash01(cid, 3, seed + 17) < 0.10) & (d1 < cell * 0.32)
    p.put(brine, 'water_cool', 4)
    p.put(brine & ~shift(brine, 0, -1, False), 'snow_cool', 2)
    # the damp margin
    ed = edge_dist(m, 18)
    wob = (fbm(p.x, p.y, 10, seed + 4) - 0.5) * 10
    damp = m & (ed + wob < 9)
    if damp.any():
        dd1, dd2, dcid, dvx, dvy = voronoi(p, 9, seed + 5)
        p.put(damp, np.where(hash01(dcid, 0, seed + 6) < 0.5, IDX['sand_cool'], IDX['earth_warm']), 3)
        p.step(damp & (dd2 - dd1 < 1.1), -2)
        p.step(damp & (dd2 - dd1 >= 1.1) & (dd2 - dd1 < 2.2) & ((dvx + dvy) > 0), 1)
        crust = damp & (ed + wob > 6) & (hash01(p.x // 3, p.y // 2, seed + 7) < 0.4)
        p.put(crust, 'snow_cool', 3)
    despeckle(p, m)


def badland_mound(seed=0, w=None, h=None):
    """One badland haystack (an obstacle to walk round): soft rock rounded by rain, banded in
    bentonite colours (rust, cream, grey, ochre) that lie level, so each band follows the
    mound's front foot round; lit on the west in hard steps and shaded on the east; rills
    running straight down it as dark creases with a lit west lip; popcorn crust on the clay."""
    w = w or 30 + int(hash01(seed, 0, 30) * 26)
    h = h or int(w * (0.45 + 0.2 * hash01(seed, 1, 30)))
    d = max(4, int(w * 0.16))
    W, H = w + 4, h + d + 4
    sp = Sprite(W, H, W // 2, H - 2)
    cx = sp.fx
    u = (sp.x + 0.5 - cx) / (w / 2)
    au = np.clip(np.abs(u), 0, 1)
    yb = sp.fy - d * (1 - np.sqrt(1 - au * au))
    lump = 1 + 0.10 * np.sin(u * 5 + seed) + 0.06 * np.sin(u * 11 + seed * 2)
    yt = sp.fy - d - h * (1 - au ** 2.2) ** 0.7 * lump
    shape = (np.abs(u) < 1) & (sp.y + 0.5 >= yt) & (sp.y + 0.5 <= yb)
    z = yb - (sp.y + 0.5)
    bands = ('clay_cool', 'adobe', 'plaster_cool', 'ash_warm', 'adobe_warm', 'clay', 'sand_cool', 'adobe_cool',
             'plaster', 'clay_warm')
    zz = z + (vnoise(sp.x, 0, 7, seed + 2) - 0.5) * 2.5
    edges, acc, k = [], 0.0, 0
    while acc < h + d + 4:
        acc += 2 + hash01(k, seed, 31) * 4
        edges.append(acc)
        k += 1
    bi = np.searchsorted(np.array(edges), zz)
    order = [int(hash01(i, seed, 32) * len(bands)) for i in range(len(edges) + 1)]
    fam = np.array([IDX[bands[order[min(i, len(order) - 1)]]] for i in range(len(edges) + 1)])[np.clip(bi, 0, len(edges))]
    tone = np.full(sp.m.shape, 3, np.int8)
    tone = np.where(u < -0.4, 4, tone)
    tone = np.where(u > 0.35, 2, tone)
    tone = np.where(u > 0.75, 1, tone)
    tone = np.where((sp.y + 0.5 - yt < 3) & (u < 0.35), 4, tone)
    tone = np.where((sp.y + 0.5 - yt < 1.5) & (u < -0.1), 5, tone)
    sp.put(shape, fam, tone)
    # the band boundaries: a harder band stands proud (lit lip), a soft one is recessed
    bedge = shape & (shift(bi, 0, 1, -1) != bi) & (hash01(bi, 0, seed + 3) < 0.5)
    sp.step(bedge, 1)
    sp.step(shift(bedge, 0, 1, False) & shape, -1, lo=1)
    # rills
    K = max(5, w // 6)
    ru = u * (1 + 0.12 * z / (h + d))
    rill = shape & (np.abs((ru * K / 2 + (vnoise(sp.y, 0, 9, seed + 4) - 0.5) * 0.4) % 1.0 - 0.5) < 0.09) & \
        (sp.y + 0.5 - yt > 3)
    sp.step(rill, -1, lo=1)
    sp.step(shift(rill, -1, 0, False) & shape & ~rill, 1)
    pop = shape & ~rill & (hash01(sp.x // 2, sp.y // 2, seed + 5) < 0.10)
    sp.f[pop] = np.where(hash01(sp.x // 2, sp.y // 2, seed + 6)[pop] < 0.5, WARM[sp.f[pop]], COOL[sp.f[pop]])
    block = shape & (sp.y > yb - d - 6)
    shadow = blob(cx + w * 0.22, sp.fy - d * 0.4, w * 0.55, d * 0.9 + 2, sp.m.shape, seed, wob=0.08) & \
        (sp.x > cx - w * 0.1)
    return sp, shadow, block


def badlands(p: Plot, m, seed=8, every=2600):
    """Badlands where the canyon cuts soft rock: banded haystack mounds to walk round, with
    aprons of washed-down clay at their feet and small gullies running off across the
    hardpan between them."""
    m = np.asarray(m, bool)
    hardpan_ground(p, m, seed, ramp='adobe')
    # gullies: dendritic creases running down the screen (south), a lit west lip
    for i, (x, y) in enumerate(_scatter(m, 900, seed + 1)):
        xx = float(x)
        for j in range(18 + int(hash01(i, seed, 33) * 20)):
            yy = y + j
            xx += (vnoise(i * 31, j, 5, seed + 2) - 0.5) * 1.6
            xi = int(round(xx))
            if 0 <= xi < p.w - 1 and 0 <= yy < p.h and m[yy, xi] and not p.solid[yy, xi]:
                p.step(_pt(p, xi, yy), -2)
                if xi > 0:
                    p.step(_pt(p, xi - 1, yy), 1)
    feet = []
    for i, (x, y) in enumerate(_scatter(m, every, seed + 3, margin=20)):
        sp, sh, blk = badland_mound(seed + i * 7)
        if (dilate(p.solid, 6))[max(0, y - 4):y + 2, max(0, x - sp.w // 2):x + sp.w // 2].any():
            continue
        apron = blob(x + 2, y + 2, sp.w * 0.52, 7, p.f.shape, seed + i, wob=0.15) & m & ~p.solid
        p.put(apron, 'adobe_cool', 3)
        stamp(p, apron, 0.12, seed + 4 + i, FLAT, swap='mix')
        paste(p, sp, x, y, shadow=sh, block=blk)
        feet.append((x, y))
    despeckle(p, m & ~p.solid)
    return feet


def wash(p: Plot, pts, width=48, seed=9, logs=2):
    """A dry wash: a sandy bed with braided gravel bars drawn out along the flow, dried
    threads of silt with curled mud between them, a low cut bank on the north side (its
    face lit, a lip of grass over it) and a contact line under the south bank's rim;
    driftwood and a boulder left by the last flood. Walkable."""
    ch = Channel(p, pts, reach=width)
    bed = ch.band(width / 2, wob=5, seed=seed)
    base(p, bed, [('sand', 0.4), ('sand_warm', 0.35), ('sand_cool', 0.25)], seed, 8)
    s_, n_ = ch.s, ch.n
    flow = fbm(s_ * 0.22, n_ * 0.9, 9, seed + 1)
    bars = bed & (flow > 0.56)
    threads = bed & (flow < 0.38)
    p.put(threads, 'path_cool', 3)
    stamp(p, threads, 0.06, seed + 2, FLAT, swap='mix')
    curls = threads & (hash01(p.x // 3, p.y // 2, seed + 3) < 0.18)
    p.put(curls & (hash01(p.x, p.y, seed + 4) < 0.6), 'clay_cool', 4)
    p.step(curls & ~shift(curls, 0, -1, False), -2)
    p.put(bars, 'sand_cool', 3)
    texture(p, bed & ~threads, seed + 12, swaps=0.14, ups=0.03, downs=0.04, shapes=FLAT)
    ripple = bed & ~bars & ~threads & ((ch.s.astype(int) + (fbm(p.x, p.y, 6, seed + 13) * 5).astype(int)) % 6 == 0)
    p.step(ripple, -1)
    rams = ('stone', 'adobe_cool', 'stone_warm', 'adobe', 'stone_cool', 'clay_cool')
    for (x, y) in _scatter(bars, 16, seed + 5, margin=1):
        pebble(p, x, y, rams[int(hash01(x, y, seed + 6) * len(rams))], 2 + int(hash01(x, y, 3) * 3), 2)
    # banks: the north bank's face, the south bank's rim
    face = bed & (shift(~bed, 0, 1, False) | shift(~bed, 0, 2, False) | shift(~bed, 0, 3, False))
    face &= ~(bed & shift(~bed, 0, -1, False))
    p.put(face, 'earth_warm', 3)
    p.put(face & shift(~bed, 0, 1, False), 'earth_warm', 4)
    p.put(face & shift(~bed, 0, 3, False) & ~shift(~bed, 0, 2, False), 'earth', 1)
    p.step(face & (hash01(p.x // 2, p.y, seed + 7) < 0.3), -1)
    lip = ~bed & shift(bed, 0, -1, False) & ~p.solid
    p.put(lip, 'sand_warm', 4)
    p.put(lip & (hash01(p.x // 2, 0, seed + 8) < 0.4), 'grass_warm', 4)
    rim = ~bed & shift(bed, 0, 1, False)
    p.step(rim, 1)
    contact = bed & shift(~bed, 0, -1, False)
    p.step(contact, -2)
    for i in range(logs):
        at = int(ch.length * (0.3 + 0.4 * i / max(1, logs)))
        cx, cy = ch.c[min(at, ch.length - 1)]
        sp, sh = log(seed + 30 + i)
        paste(p, sp, int(cx + (hash01(i, 0, seed) - 0.5) * width * 0.4), int(cy), shadow=sh)
    despeckle(p, bed)
    p.walk[bed] = True
    return ch, bed


# --- standing things ---------------------------------------------------------------------------
def light_of(u, v, lift=0.3):
    """Light on a rounded form at (u, v) from its centre (radius 1): the upper left lit."""
    r2 = np.clip(u * u + v * v, 0, 1)
    return -0.6 * u - 0.75 * v + lift * np.sqrt(1 - r2)


def tone_of(lam, cuts=(0.45, 0.0, -0.45)):
    """Hard steps of light (one hard terminator, house rule 3): 4, 3, 2, 1."""
    return np.where(lam > cuts[0], 4, np.where(lam > cuts[1], 3, np.where(lam > cuts[2], 2, 1)))


def bush(sp: Sprite, cx, cy, rx, ry, ramp, seed=0, clump=2.2, wob=0.16, lobes=6, rim='grass'):
    """A rounded bush of leaf clumps (the house foliage recipe at a shrub's size): light in
    four bands from the upper left, clumps a tone above their band with a dark U under each,
    clumps from all three siblings, a lit rim on the upper-left edge, the deep band quiet."""
    u, v = (sp.x + 0.5 - cx) / rx, (sp.y + 0.5 - cy) / ry
    ang = np.arctan2(v, u)
    r = 1 + wob * np.sin(ang * lobes + seed) + 0.06 * np.sin(ang * 11 + seed * 2)
    shape = u * u + v * v <= r * r
    band = tone_of(light_of(u, v, 0.25), (0.5, 0.05, -0.45))
    sp.put(shape, ramp, band)
    fam0 = hp.family(ramp)
    yy, row = cy - ry + 1.5, 0
    while yy < cy + ry:
        xx = cx - rx + (clump * 1.2 if row % 2 else 0.8)
        while xx < cx + rx:
            jx = (hash01(int(xx * 5), int(yy * 5), seed) - 0.5) * 1.2
            ccx, ccy = xx + jx, yy
            ix, iy = int(ccx), int(ccy)
            if 0 <= ix < sp.w and 0 <= iy < sp.h and shape[iy, ix] and band[iy, ix] > 1:
                b = band[iy, ix]
                pts = shape & ((sp.x + 0.5 - ccx) ** 2 + (sp.y + 0.5 - ccy) ** 2 <= clump * clump)
                nm = hash01(ix * 7, iy * 7, seed + 5)
                rp = f'{fam0}_warm' if nm < 0.33 else f'{fam0}_cool' if nm > 0.66 else fam0
                sp.put(pts, rp, min(4, b + 1))
                low = pts & ~shift(pts, 0, -1, False) & (sp.y + 0.5 > ccy)
                sp.put(low, rp, max(1, b - 1))
                cap = pts & (sp.y + 0.5 < ccy - clump * 0.4) & (sp.x + 0.5 < ccx + 0.5) & (b >= 3)
                sp.put(cap, rp, 5 if b == 4 else 4)
            xx += clump * 2.3
        yy += clump * 1.5
        row += 1
    if rim:
        edge = shape & (~shift(shape, 1, 0, False) | ~shift(shape, 0, 1, False)) & (band >= 4)
        sp.put(edge, rim, 5 if rim == 'grass' else 4)
    return shape


def stems(sp: Sprite, x, y0, n, spread, h, ramp='timber_cool', seed=0):
    """Woody stems fanning up from a shrub's foot."""
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) / max(1, n - 1) * spread
        for j in range(h):
            px = int(round(x + math.cos(a) * j * 0.9))
            py = int(round(y0 + math.sin(a) * j))
            sp.px(px, py, ramp, 2 if j > 1 else 1)


def sage(seed=0):
    """Big sagebrush (size guide bush: 12 to 28 tall): a rounded silver-green mound of small
    clumps on short grey stems, its foot dark."""
    w = 18 + int(hash01(seed, 0, 1) * 6)
    hgt = 11 + int(hash01(seed, 1, 1) * 4)
    sp = Sprite(w + 4, hgt + 3, (w + 4) // 2, hgt + 1)
    stems(sp, sp.fx, sp.fy, 4, 1.4, 5, 'stone_cool', seed)
    bush(sp, sp.fx, sp.fy - hgt * 0.55, w * 0.5, hgt * 0.5, 'cactus_cool', seed, 2.0, rim='bleached')
    return sp, sp.blob_shadow(w * 0.42, 3)


def creosote(seed=0):
    """Creosote bush: an open vase of dark stems with small olive clumps at their tips, the
    ground showing through it."""
    w = 20 + int(hash01(seed, 0, 2) * 6)
    hgt = 15 + int(hash01(seed, 1, 2) * 5)
    sp = Sprite(w + 4, hgt + 3, (w + 4) // 2, hgt + 1)
    n = 5
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) / (n - 1) * 1.25 + (hash01(i, seed, 3) - 0.5) * 0.2
        ln = hgt * (0.7 + 0.3 * hash01(i, seed, 4))
        tip = None
        for j in range(int(ln)):
            px = int(round(sp.fx + math.cos(a) * j))
            py = int(round(sp.fy + math.sin(a) * j))
            sp.px(px, py, 'timber_cool', 2 if j % 4 else 1)
            sp.px(px + 1, py, 'timber_cool', 1)
            tip = (px, py)
        if tip:
            bush(sp, tip[0] + 0.5, tip[1] + 1.5, 4.2 + hash01(i, seed, 5) * 1.5, 3.4, 'leaf_cool', seed + i, 1.8,
                 wob=0.25, rim=None)
    return sp, sp.blob_shadow(w * 0.4, 3)


def rabbitbrush(seed=0):
    """Rabbitbrush in flower: a yellow-green mound topped with flat yellow flower heads."""
    w = 16 + int(hash01(seed, 0, 6) * 5)
    hgt = 12 + int(hash01(seed, 1, 6) * 3)
    sp = Sprite(w + 4, hgt + 3, (w + 4) // 2, hgt + 1)
    stems(sp, sp.fx, sp.fy, 3, 1.2, 4, 'stone_cool', seed)
    shape = bush(sp, sp.fx, sp.fy - hgt * 0.5, w * 0.5, hgt * 0.48, 'grass_cool', seed, 2.0, rim=None)
    tops = shape & (sp.y < sp.fy - hgt * 0.45) & (hash01(sp.x // 2, sp.y // 2, seed + 3) < 0.55)
    sp.put(tops & ~shift(tops, 0, -2, False), 'brass_warm', 4)
    sp.put(tops & shift(tops, 0, -2, False) & (sp.x < sp.fx), 'brass', 5)
    sp.put(tops & shift(tops, 0, -2, False) & (sp.x >= sp.fx), 'brass_cool', 3)
    return sp, sp.blob_shadow(w * 0.42, 3)


def tussock_sprite(seed=0):
    """A bunchgrass clump as a small standing thing (in scrub, between the bushes)."""
    w = 8 + int(hash01(seed, 0, 7) * 4)
    sp = Sprite(w + 2, 9, (w + 2) // 2, 7)
    for i in range(w):
        hgt = 3 + int(4 * math.sin(math.pi * (i + 0.5) / w)) + int(hash01(i, seed, 8) * 2)
        lean = (i - w / 2) / w * 2
        for j in range(hgt):
            px = 1 + i + int(round(lean * j / 3))
            k = 1 if j == 0 else 2 if i > w * 0.6 else 3
            fam = 'grass_warm'
            if j >= hgt - 2:
                fam, k = 'sand', (4 if i < w * 0.6 else 3)
            sp.px(px, 7 - j, fam, k)
    return sp, sp.blob_shadow(w * 0.45, 2)


def saguaro(seed=0, arms=None):
    """A saguaro (size guide cactus: 36 to 72): a ribbed column lit on its west, the ribs as
    grooves a tone down, spines catching the light along the ribs in short pairs, one or two
    arms that turn up, a rounded crown."""
    H = 44 + int(hash01(seed, 0, 9) * 18)
    W = 30
    sp = Sprite(W, H + 3, W // 2, H)
    cx = W // 2 - 4

    def column(x0, y0, y1, w):
        for y in range(y0, y1 + 1):
            top = y - y0
            inset = 2 if top == 0 else 1 if top == 1 else 0
            for i in range(inset, w - inset):
                k = (4, 4, 3, 3, 3, 2, 2, 1, 1)[min(8, int(i * 9 / w))]
                fam = 'cactus_warm' if i < w * 0.3 else 'cactus' if i < w * 0.7 else 'cactus_cool'
                if i in (2, 5) and top > 1:
                    k = max(1, k - 1)
                if top <= 1 and i < w - 2:
                    k = min(5, k + 1)
                sp.px(x0 + i, y, fam, k)
            # spines along the lit ribs: short pairs
            if top > 3 and (y + seed) % 5 == 0:
                for i in (1, 4):
                    if i < w - 3:
                        sp.px(x0 + i, y, 'plaster', 4)
                        sp.px(x0 + i, y + 1, 'plaster', 4)
    column(cx, 2, H, 8)
    n_arms = arms if arms is not None else 1 + int(hash01(seed, 1, 9) * 2)
    for a in range(n_arms):
        side = -1 if a == 0 else 1
        ay = int(H * (0.45 + 0.15 * hash01(seed, a, 10)))
        reach = 5 + int(hash01(seed, a, 11) * 3)
        up = 10 + int(hash01(seed, a, 12) * 8)
        x_out = cx - reach - 3 if side < 0 else cx + 8 + reach - 3
        # the elbow: a horizontal run out of the trunk
        for y in range(ay, ay + 5):
            xs = range(x_out, cx) if side < 0 else range(cx + 8, x_out + 6)
            for x in xs:
                k = 4 if y == ay else 3 if y < ay + 3 else 2
                sp.px(x, y, 'cactus' if y < ay + 4 else 'cactus_cool', k)
        column(x_out, ay - up, ay + 4, 6)
    sh = sp.thrown(0.5)
    return sp, sh


def barrel(seed=0):
    """A barrel cactus: a squat ribbed drum, red spines in stripes along the ribs, a crown
    of yellow fruit."""
    W, H = 14, 14
    sp = Sprite(W + 2, H + 2, (W + 2) // 2, H)
    cx, cy = sp.fx, H - 6
    u, v = (sp.x + 0.5 - cx) / 6.5, (sp.y + 0.5 - cy) / 7.0
    shape = (u * u + v * v <= 1) & (sp.y <= H)
    rib = (np.abs(((sp.x - cx) / 2.0) % 1.0 - 0.5) < 0.2)
    sp.put(shape, 'cactus', tone_of(light_of(u, v, 0.3)))
    sp.step(shape & rib, -1, lo=1)
    sp.put(shape & rib & (sp.y % 3 == 0) & (sp.y > cy - 4), 'clay_warm', 3)
    for (dx, dy) in ((-2, -6), (-1, -6), (1, -7), (2, -7), (0, -6)):
        sp.px(cx + dx, cy + dy, 'brass', 4 if dx < 1 else 3)
    return sp, sp.blob_shadow(5.5, 2.5)


def prickly_pear(seed=0):
    """Prickly pear: flat oval pads stacked on each other, lit on their upper-left rims,
    areoles in pairs, red fruit on the top pads' rims."""
    sp = Sprite(26, 22, 13, 20)
    pads = [(8, 16, 4.5, 5.5), (17, 16, 4.0, 5.0), (12, 9, 4.2, 5.4), (19, 7, 3.4, 4.3), (6, 8, 3.2, 4.0)]
    if hash01(seed, 0, 13) < 0.5:
        pads = pads[:4]
    for i, (px, py, rx, ry) in enumerate(pads):
        u, v = (sp.x + 0.5 - px) / rx, (sp.y + 0.5 - py) / ry
        shape = u * u + v * v <= 1
        fam = ('cactus', 'cactus_warm', 'cactus_cool')[i % 3]
        sp.put(shape, fam, tone_of(light_of(u, v, 0.35), (0.55, 0.05, -0.5)))
        ring = shape & ~erode(shape, 1)
        sp.put(ring & (u + v > 0.2), fam, 1)
        are = shape & erode(shape, 1) & ((sp.x + sp.y * 2 + i) % 4 == 0) & (sp.y % 3 == 0)
        sp.put(are, 'plaster_cool', 3)
        sp.put(shift(are, 0, 1, False) & shape, fam, 2)
        if i >= 2:
            for (dx, dy) in ((-1, -int(ry)), (0, -int(ry)), (int(rx) - 1, -int(ry) + 1)):
                sp.px(px + dx, py + dy - 1, 'berry_warm', 3)
                sp.px(px + dx, py + dy - 2, 'berry_warm', 4)
    return sp, sp.blob_shadow(10, 3)


def palm(v=0, seed=0):
    """A date palm (size guide: 56 to 104; a small palm 32 to 56): a leaning trunk patterned
    by old leaf bases in offset rows, lit on the west; a crown of feathered fronds radiating
    and drooping, the back ones in shade, the front ones lit on their upper side; a skirt of
    dead fronds; dates hanging under the crown."""
    H = (76 + int(hash01(seed, 0, 14) * 16)) if v == 0 else (40 + int(hash01(seed, 0, 14) * 10))
    L = 24 if v == 0 else 16
    W = L * 2 + 14
    sp = Sprite(W, H + 3, W // 2, H)
    lean = (hash01(seed, 1, 14) - 0.5) * (14 if v == 0 else 8)
    top_y = int(L * 0.55) + 2
    trunk_len = H - top_y

    def xc(y):
        t = (H - y) / trunk_len
        return sp.fx + lean * t * t
    for y in range(top_y, H + 1):
        t = (H - y) / trunk_len
        w = 5 if t < 0.85 else 4
        if v == 1:
            w = 4
        flare = 2 if y >= H - 1 else 1 if y >= H - 3 else 0
        x0 = int(round(xc(y) - w / 2)) - flare
        row = (H - y) // 3
        for i in range(w + 2 * flare):
            k = (4, 3, 3, 2, 1, 1, 1, 1, 1)[min(8, int(i * 5 / (w + 2 * flare)))]
            fam = 'bleached' if t < 0.55 else 'timber_warm'
            # leaf bases: each row a ledge, offset every other row
            if (H - y) % 3 == 0:
                k = max(1, k - 1)
            elif ((x0 + i + (row % 2) * 2) % 4 == 0) and (H - y) % 3 == 1:
                k = min(5, k + 1)
            sp.px(x0 + i, y, fam, k)
    cx, cy = xc(top_y) + 0.5, top_y + 0.5

    def frond(a, ln, droop, lit, fam, dead=False):
        steps = int(ln * 1.6)
        for s in range(steps + 1):
            t = s / steps
            x = cx + math.cos(a) * ln * t
            y = cy + math.sin(a) * ln * t * 0.62 + droop * t * t * ln
            # tangent and the side facing up-left
            dx = math.cos(a) * ln
            dy = math.sin(a) * ln * 0.62 + 2 * droop * t * ln
            nl = math.hypot(dx, dy) or 1
            nx, ny = -dy / nl, dx / nl
            if nx + ny > 0:
                nx, ny = -nx, -ny                       # (nx, ny) points to the upper left
            half = (3.4 if v == 0 else 2.6) * math.sin(math.pi * min(1, t * 1.15)) + 0.6
            if dead:
                half = 1.2
            for o in np.arange(-half, half + 0.01, 0.5):
                if abs(o) > 1 and (int(s + (o > 0) * 1) % 2 == 1) and abs(o) > half - 1:
                    continue                            # serrated leaflet tips
                px, py = int(round(x + nx * o)), int(round(y + ny * o))
                k = lit + (1 if o > 0.6 else -1 if o < -0.6 else 0)
                if t > 0.85:
                    k -= 1
                sp.px(px, py, fam, int(np.clip(k, 1, 5 if not dead else 4)))
            sp.px(int(round(x)), int(round(y)), fam, max(1, lit - 1) if not dead else 2)
    n = 12 if v == 0 else 9
    order = []
    for i in range(n):
        a = -math.pi + (i + 0.5) / n * 2 * math.pi + (hash01(i, seed, 15) - 0.5) * 0.3
        order.append(a)
    # dead fronds first, hanging under the crown
    for i in range(3 if v == 0 else 1):
        a = math.pi / 2 + (i - 1) * 0.5
        frond(a, L * 0.55, 0.15, 2, 'bleached_cool' if i % 2 else 'timber_warm', dead=True)
    # back fronds (pointing up, behind the crown), then sides, then front
    for a in sorted(order, key=lambda a: math.sin(a)):
        up = math.sin(a) < -0.3
        right = math.cos(a) > 0.3
        lit = 2 if up and right else 3 if (up or right) else 4
        if math.cos(a) < -0.3 and not up:
            lit = 4
        fam = ('cactus', 'leaf', 'cactus_warm', 'leaf_warm')[int(hash01(int(a * 100), seed, 16) * 4)]
        ln = L * (0.8 + 0.25 * hash01(int(a * 100), seed, 17))
        frond(a, ln, 0.38 + 0.2 * hash01(int(a * 100), seed, 18), lit, fam)
    if v == 0:
        for i, dx in enumerate((-4, 3)):
            for j in range(4):
                for q in range(3 - (j == 3)):
                    sp.px(int(cx) + dx + q, int(cy) + 3 + j, 'brass_warm' if (q + j) % 2 else 'clay_warm',
                          4 if q == 0 else 3)
    for (dx, dy) in ((-1, 0), (0, 0), (1, 0), (0, 1), (-1, 1)):
        sp.px(int(cx) + dx, int(cy) + dy, 'timber', 1)
    # leaflets in groups: each pair of leaflets a sibling, a few lit tips, a few shaded midribs
    crown_m = sp.m & (sp.y < cy + L * 0.7) & ~GLOW[sp.f]
    g = hash01(sp.x // 2, sp.y // 2, seed + 30)
    sw = crown_m & (g < 0.35)
    sp.f[sw] = np.where(g[sw] < 0.17, WARM[sp.f[sw]], COOL[sp.f[sw]])
    tip = crown_m & (hash01(sp.x // 2, sp.y, seed + 31) < 0.12) & (sp.t >= 3)
    sp.step(tip, 1, hi=5)
    dk = crown_m & (hash01(sp.x, sp.y // 2, seed + 32) < 0.1) & (sp.t >= 2)
    sp.step(dk, -1, lo=1)
    return sp, sp.thrown(0.45)


def boulder(seed=0, ramp='adobe', w=None, h=None):
    """A boulder (size guide 16 to 32): a rounded mass with flat-ish facets, lit upper left
    in hard steps, a crack or two with a lit lower lip, bedding lines in sandstone, lichen
    on basalt, a dark contact at its foot."""
    w = w or 16 + int(hash01(seed, 0, 19) * 12)
    h = h or int(w * (0.62 + 0.15 * hash01(seed, 1, 19)))
    sp = Sprite(w + 4, h + 4, (w + 4) // 2, h + 1)
    cx, cy = sp.fx, sp.fy - h * 0.48
    u, v = (sp.x + 0.5 - cx) / (w / 2), (sp.y + 0.5 - cy) / (h / 2)
    ang = np.arctan2(v, u)
    r = 1 + 0.10 * np.sin(ang * 3 + seed) + 0.05 * np.sin(ang * 7 + seed)
    shape = (u * u + v * v <= r * r) & (sp.y <= sp.fy)
    fam = hp.family(ramp)
    # facets: the light quantised per facet, so the boulder reads as broken rock
    fac = (np.floor((ang + seed) / 1.1)).astype(int)
    lam = light_of(u, v, 0.35) + 0.15 * (hash01(fac, 0, seed + 2) - 0.5)
    tone = tone_of(lam, (0.42, -0.02, -0.45))
    pick = hash01(fac, 1, seed + 3)
    famr = np.where(pick < 0.33, IDX[f'{fam}_warm'], np.where(pick < 0.66, IDX[fam], IDX[f'{fam}_cool']))
    sp.put(shape, famr, tone)
    sp.put(shape & (tone == 4) & (lam > 0.62), famr, 5)
    if fam in ('adobe', 'sand', 'clay', 'path', 'bleached'):
        bed = shape & (((sp.y + int(seed)) % 4) == 0) & (tone <= 3)
        sp.step(bed, -1, lo=1)
    if fam in ('basalt', 'stone', 'ash'):
        lich = shape & (tone >= 3) & (hash01(sp.x // 2, sp.y // 2, seed + 4) < 0.18)
        sp.put(lich, 'brass_cool' if fam == 'basalt' else 'grass_cool', 4)
    for c in range(1 + int(hash01(seed, 2, 19) * 2)):
        x0 = int(cx - w * 0.2 + c * w * 0.3)
        for j in range(int(h * 0.5)):
            x = x0 + (j // 2) * (1 if c % 2 else -1)
            y = int(cy - h * 0.25) + j
            if 0 <= x < sp.w and 0 <= y < sp.h and shape[y, x]:
                sp.t[y, x] = 1
                if 0 <= y + 1 < sp.h and x - 1 >= 0 and shape[y + 1, x - 1]:
                    sp.t[y + 1, x - 1] = min(5, sp.t[y + 1, x - 1] + 1)
    sp.put(shape & (sp.y >= sp.fy - 1), famr, 1)
    return sp, sp.blob_shadow(w * 0.55, max(3, h * 0.3))


def snag(seed=0, kind='charred'):
    """A dead tree (size guide snag: 32 to 80): a bare trunk and a few broken limbs. Charred:
    black char in blocks with grey lit edges on the west. Bleached: silver-grey wood with
    long splits."""
    H = 40 + int(hash01(seed, 0, 20) * 30)
    W = 34
    sp = Sprite(W, H + 3, W // 2, H)
    fam = 'basalt' if kind == 'charred' else 'bleached'
    lean = (hash01(seed, 1, 20) - 0.5) * 6
    top = 4 + int(hash01(seed, 2, 20) * 6)
    for y in range(top, H + 1):
        t = (H - y) / (H - top)
        w = 5 if t < 0.5 else 4 if t < 0.8 else 3
        flare = 2 if y >= H - 1 else 1 if y >= H - 3 else 0
        x0 = int(round(sp.fx + lean * t - w / 2)) - flare
        for i in range(w + 2 * flare):
            k = (4, 3, 2, 2, 1, 1, 1, 1, 1)[min(8, int(i * 5 / (w + 2 * flare)))]
            if kind == 'charred':
                k = 3 if i == 0 else 2 if i == 1 else 1
                if ((y // 3 + (x0 + i) // 2) % 3 == 0) and 0 < i < w - 1:
                    k = max(0, k - 1)
                ramp = 'ash' if i == 0 else fam
            else:
                ramp = fam if i < w - 1 else 'bleached_cool'
                if i == w // 2 and (y + seed) % 9 < 5:
                    k = 1
            sp.px(x0 + i, y, ramp, k)
    # limbs: up and out, broken off
    n = 2 + int(hash01(seed, 3, 20) * 3)
    for b in range(n):
        side = -1 if b % 2 == 0 else 1
        by = int(top + (H - top) * (0.15 + 0.5 * hash01(seed, b, 21)))
        ln = 10 + int(hash01(seed, b, 22) * 10)
        a = -math.pi / 2 + side * (0.6 + 0.5 * hash01(seed, b, 23))
        bx = sp.fx + lean * (H - by) / (H - top)
        fork = int(ln * 0.55)
        for j in range(ln):
            x = int(round(bx + math.cos(a) * j))
            y = int(round(by + math.sin(a) * j))
            if j > fork and j < fork + 6:              # a twig forking up from the limb
                tx, ty = int(round(bx + math.cos(a) * fork)), int(round(by + math.sin(a) * fork))
                sp.px(tx + side * 0 + (j - fork) * (1 if side < 0 else -1) // 3, ty - (j - fork), fam, 2)
            th = 2 if j < ln * 0.6 else 1
            for q in range(th):
                k = (3 if kind != 'charred' else 2) if q == 0 else 1
                if j == ln - 1:
                    k = 4 if kind != 'charred' else 3
                sp.px(x + q, y, 'ash' if (kind == 'charred' and q == 0 and j % 3 == 0) else fam, k)
    return sp, sp.thrown(0.5)


def fireweed(seed=0):
    """Fireweed, first to grow on burnt ground and old flows: a few tall slim stems, narrow
    leaves angled up from them, a magenta flower spike at the top of each, lit on its west
    side, buds paler at the tip."""
    n = 3 + int(hash01(seed, 0, 24) * 3)
    H = 16 + int(hash01(seed, 1, 24) * 6)
    sp = Sprite(12, H + 2, 6, H)
    for i in range(n):
        x = 2 + int(i * 7 / max(1, n - 1)) + int((hash01(i, seed, 25) - 0.5) * 2)
        top = 1 + int(hash01(i, seed, 26) * 6)
        lean = (x - 6) * 0.08
        for y in range(top + 4, H + 1):
            sp.px(int(round(x + lean * (H - y))), y, 'grass_cool', 2 if y > H - 2 else 3)
        hx = int(round(x + lean * (H - top)))
        for y in range(top, top + 5):
            sp.px(hx, y, 'berry_warm', 4 if y < top + 2 else 3)
            sp.px(hx + 1, y + 1, 'berry', 2)
        sp.px(hx, top - 1, 'berry_warm', 5)
        for y in range(top + 7, H - 2, 4):
            xx = int(round(x + lean * (H - y)))
            sp.px(xx - 1, y, 'leaf', 3)
            sp.px(xx - 2, y - 1, 'leaf', 4)
            sp.px(xx + 1, y + 1, 'leaf_cool', 2)
    return sp, sp.blob_shadow(4, 2)


def log(seed=0, kind='bleached'):
    """A fallen log: a cylinder lying east and west, lit along its top, its sawn or broken
    west end showing rings; charred logs crack into blocks."""
    L = 18 + int(hash01(seed, 0, 27) * 10)
    sp = Sprite(L + 4, 9, 2, 7)
    fam = 'bleached' if kind == 'bleached' else 'basalt'
    for x in range(2, L + 2):
        for j, k in enumerate((4, 3, 3, 2, 1)):
            kk = k
            if kind == 'charred' and (x // 3 + j) % 3 == 0:
                kk = max(1, k - 1)
            if kind != 'charred' and j == 2 and (x + seed) % 7 < 3:
                kk = 2
            sp.px(x, 2 + j, fam if x < L else f'{fam}_cool', kk)
    for j, k in enumerate((4, 5, 4, 3)):
        sp.px(1, 2 + j, 'plaster' if kind != 'charred' else 'ash', k if j != 2 else 3)
    sp.px(1, 6, 'timber' if kind != 'charred' else 'ash', 2)
    for (x, y) in ((L // 2, 1), (L // 2 + 1, 1), (L // 2 + 1, 0)):
        sp.px(x, y, fam, 3)
    sh = np.zeros(sp.m.shape, bool)
    sh[6:9, 3:L + 4] = True
    return sp, sh


def reeds(kind='reed', seed=15, n=5):
    """A clump of 3 to 6 reeds at the water (size guide: 14 to 32 tall), blades lit on the
    west, dark at the foot, purple-brown plumes."""
    H = 26
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
            sp.px(x, y, 'grass_warm' if i % 3 else 'leaf_warm', k)
        hx = int(round(bx + lean * (H - top)))
        if kind == 'reed':
            for y in range(top - 4, top):
                sp.px(hx - 1, y, 'dusk_warm', 3)
                sp.px(hx, y, 'timber_warm', 2)
        if i % 2 == 1:
            for j in range(5):
                lx, ly = bx + j - 2 + (1 if j > 2 else 0), H - 8 - j + (j * j) // 4
                sp.px(lx, ly, 'grass', 3)
    sh = np.zeros(sp.m.shape, bool)
    sh[H - 1:H + 2, 6:20] = True
    return sp, sh


# --- height: the soft grid's tiers -------------------------------------------------------------
def from_cells(rows, cell=GRID, seed=0, round_r=6, wob=1.5):
    """A screen tier map from text, one character a cell ('0' to '9'), as terrace.py reads a
    zone: the tops as the camera sees them. Corners are rounded by about a cell and edges
    wander a pixel or two inside their edge cells, so straight runs stay on the grid and
    nothing reads as a ruled line."""
    rows = [r for r in (rows.strip('\n').split('\n') if isinstance(rows, str) else rows)]
    h, w = len(rows) * cell, max(len(r) for r in rows) * cell
    T = np.zeros((h, w), np.int8)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch.isdigit():
                T[j * cell:(j + 1) * cell, i * cell:(i + 1) * cell] = int(ch)
    return smooth_tiers(T, seed, round_r, wob)


def smooth_tiers(T, seed=0, round_r=6, wob=1.5):
    """Round a tier map's corners (close, then open, per level) and let its edges wander.
    One wander for every level, and each level kept inside the one below it, so where the
    ground drops two tiers at once the two edges stay one edge (no slivers of the tier
    between)."""
    y, x = np.mgrid[0:T.shape[0], 0:T.shape[1]]
    n = (fbm(x, y, 9, seed) - 0.5) * 2 * wob
    top = int(T.max())
    masks = {}
    for k in range(top, 0, -1):
        m = T >= k
        r = max(1, round_r // 2)
        m = erode(dilate(m, r), r)
        m = dilate(erode(m, r), r)
        if wob:
            d_in = edge_dist(m, 4)
            d_out = edge_dist(~m, 4)
            m = (m & ~((d_in <= 2) & (n < -(d_in - 0.5)))) | (~m & (d_out <= 2) & (n > d_out - 0.5))
        if k < top:
            m |= masks[k + 1]
        masks[k] = m
    out = np.zeros_like(T)
    for k in range(1, top + 1):
        out[masks[k]] = k
    return out


class Layout:
    """Where every tier's top is seen and where faces hang (the soft grid, south faces only):
    `face` the face pixels, `kf` the tier of the rim each hangs from, `depth` rows below
    that rim, `fh` the face's full height there, `T` the tier of each top."""

    def __init__(self, T, F=FACE_MESA):
        self.T = np.asarray(T, np.int8)
        self.F = F
        h, w = self.T.shape
        self.face = np.zeros((h, w), bool)
        self.kf = np.zeros((h, w), np.int8)
        self.depth = np.zeros((h, w), np.int16)
        self.fh = np.zeros((h, w), np.int16)
        top = int(self.T.max())
        for k in range(top, 0, -1):
            below = shift(self.T, 0, -1, 99)               # the tier just south of each pixel
            rim = (self.T == k) & (below < k) & ~self.face
            if not rim.any():
                continue
            fhk = np.where(rim, (k - np.minimum(below, k)) * F, 0).astype(np.int16)
            for d in range(1, (k * F) + 1):
                rd = shift(rim, 0, d, False)
                hd = shift(fhk, 0, d, 0)
                cand = rd & (hd >= d) & ~self.face & (self.T < k)
                self.face |= cand
                self.kf[cand] = k
                self.depth[cand] = d - 1
                self.fh[cand] = hd[cand]
        self.rim = (self.T >= 1) & shift(self.face, 0, -1, False) & ~self.face

    def top(self, k):
        return (self.T == k) & ~self.face

    def tier_seen(self):
        return np.where(self.face, -1, self.T)


# The Sunstone column, bottom up: (thickness, ramp, hard). Hard beds stand as ledges of
# jointed blocks; soft beds weather back into slopes with fine bedding and rills. Beds lie
# level, so the same bed runs at the same height through every mesa and canyon wall.
STRATA = (
    (9, 'clay_cool', False),       # red mudstone, slope-forming
    (6, 'adobe_warm', True),       # a sandstone ledge
    (4, 'clay', False),
    (5, 'plaster_cool', False),    # a pale ash bed
    (8, 'adobe', True),            # cliff-forming sandstone
    (4, 'clay_cool', False),
    (6, 'sand_warm', True),        # the caprock
    (3, 'adobe_cool', False),
)


def stratum(elev, strata=STRATA, seed=0):
    """The bed at each elevation (px above tier 0's ground), its row from its top and its
    thickness: the column repeats upward, each bed a pixel or two thicker or thinner."""
    elev = np.asarray(elev)
    edges, beds = [0], []
    i = 0
    while edges[-1] < int(elev.max()) + 2:
        th, ramp, hard = strata[i % len(strata)]
        th = th + int((hash01(i, 0, seed) - 0.5) * 3)
        edges.append(edges[-1] + max(2, th))
        beds.append((ramp, hard))
        i += 1
    e = np.array(edges)
    bi = np.clip(np.searchsorted(e, elev, side='right') - 1, 0, len(beds) - 1)
    top_of = e[bi + 1]
    th = e[bi + 1] - e[bi]
    return bi, beds, top_of - 1 - elev, th


def draw_faces(p: Plot, L: Layout, strata=STRATA, seed=0, earth=False):
    """Paint every south face of a layout: beds of rock lying level across the face (hard
    beds as ledges of jointed blocks, lit along their top, an overhang shadow under them;
    soft beds with fine bedding, rills and talus streaks), desert varnish hanging in dark
    streaks from the ledges, a lit lip along the rim with chips out of it, the west end
    wrapping round into the light and the east end into shade, a dark foot."""
    fc = L.face
    if not fc.any():
        return
    elev = (L.kf.astype(int) * L.F - L.depth - 1)
    elev = np.where(fc, elev, 0)
    bi, beds, row, th = stratum(elev, strata, seed)
    rams = np.array([IDX[r] for r, _h in beds])
    hard = np.array([h for _r, h in beds])
    fam = rams[bi]
    # Hard beds break into blocks along joints: blocks 8 to 24 px wide, each a sibling,
    # their corners knocked off, joints that do not line up from bed to bed and sometimes
    # stop short; the ledge's lit top wanders a pixel where blocks have spalled.
    jit = (vnoise(p.x, bi * 13, 6, seed + 1) * 16).astype(int)
    bwid = 8 + (hash01(bi, 0, seed + 1) * 10).astype(int)
    blk = (p.x + jit + (hash01(bi, 1, seed + 2) * 30).astype(int)) // np.maximum(bwid, 1)
    sib = hash01(blk, bi, seed + 3)
    fam = np.where(sib < 0.33, WARM[fam], np.where(sib > 0.66, COOL[fam], fam))
    hb = hard[bi]
    edge_l = blk != shift(blk, 1, 0, -1)                 # the first column of a block
    tone = np.full(p.f.shape, 3, np.int8)
    spall = hb & (row == 0) & (hash01(blk, bi, seed + 9) < 0.3)
    tone = np.where(hb & (row == 0), 4, tone)                              # a ledge's lit top
    tone = np.where(hb & (row == 1) & (sib < 0.5), 4, tone)
    tone = np.where(spall, 2, tone)                                        # a spalled block sits back
    tone = np.where(hb & (row == th - 1), 2, tone)                         # its underside
    short = hash01(blk, bi, seed + 10) < 0.35                              # a joint that stops short
    joint = hb & edge_l & (row > 0) & ~(short & (row > th // 2))
    tone = np.where(joint, 1, tone)
    tone = np.where(hb & shift(joint, -1, 0, False) & (row > 0), np.minimum(tone + 1, 4), tone)   # lit lip west of a joint
    corner = hb & (edge_l | shift(edge_l, -1, 0, False)) & ((row == 0) | (row == th - 1))
    tone = np.where(corner, 2, tone)
    # broad light over the face: patches a tone up towards the west, down towards the east
    broad = fbm(p.x, p.y, 22, seed + 11)
    tone = np.where(~hb & (broad > 0.64) & (tone == 3), 4, tone)
    tone = np.where(~hb & (broad < 0.30) & (tone == 3), 2, tone)
    # long fractures down through several beds
    frac = fc & (hash01(p.x // 1, 0, seed + 12) < 0.012) & (vnoise(p.x, p.y, 30, seed + 13) > 0.45)
    # under a hard bed: the soft bed is recessed in its shadow
    above_hard = np.zeros(p.f.shape, bool)
    for d in (1, 2):
        above_hard |= shift(fc & hb & (row == th - 1), 0, d, False)
    soft = fc & ~hb
    tone = np.where(soft & above_hard, 2, tone)
    tone = np.where(soft & shift(fc & hb & (row == th - 1), 0, 1, False), 1, tone)
    # soft beds: fine bedding broken into short lengths, and rills
    bedding = soft & (row % 3 == 1) & (hash01(p.x // 5, elev, seed + 4) < 0.45)
    tone = np.where(bedding & (tone == 3), 2, tone)
    rill = soft & ((p.x * 7 + bi * 3 + jit) % 13 == 0) & (row > 0)
    tone = np.where(rill & (tone >= 2), tone - 1, tone)
    tone = np.where(frac, 1, tone)
    tone = np.where(shift(frac, -1, 0, False) & fc & ~frac, np.minimum(tone + 1, 4), tone)
    p.f[fc] = fam[fc]
    p.t[fc] = tone[fc]
    # grain: sibling clusters along the beds, and in the hard beds weathering pockets
    # (tafoni): a dark hollow with its lower lip lit
    body = fc & (L.depth > 1) & (L.depth < L.fh - 2)
    stamp(p, body & ~hb, 0.10, seed + 14, FLAT, swap='mix')
    stamp(p, body & hb & (row > 0) & (row < th - 1), 0.07, seed + 15, DOMINOES, swap='mix')
    pock = body & hb & (row > 1) & (row < th - 2) & (hash01(p.x // 3, p.y // 2, seed + 16) < 0.10) & \
        ~joint & ~shift(joint, 1, 0, False) & ~shift(joint, -1, 0, False)
    pock = pock & (p.x % 3 == 0)
    pock2 = pock | shift(pock, 1, 0, False)
    p.t[pock2 & fc] = 1
    lipp = shift(pock2, 0, 1, False) & fc & hb & ~pock2
    p.t[lipp] = np.minimum(p.t[lipp] + 1, 4)
    lip_r = fc & (L.depth == 0)
    p.step(shift(rill, -1, 0, False) & soft & ~rill & ~lip_r, 1)
    # desert varnish: dark streaks hanging from the ledges
    vstart = fc & hb & (row == th - 1) & (hash01(p.x // 2, bi, seed + 5) < 0.22)
    vlen = (3 + hash01(p.x // 2, bi, seed + 6) * 9).astype(int)
    var = np.zeros(p.f.shape, bool)
    for d in range(1, 13):
        var |= shift(vstart & (vlen >= d), 0, d, False)
    var &= fc & ~hb
    var |= shift(var, 1, 0, False) & fc & ~hb             # streaks two px wide
    p.f[var] = COOL[p.f[var]]
    p.step(var & (p.t >= 2), -1)
    # the rim: a lit lip, chips out of it, an odd glint; the top's edge above it lit too
    p.t[lip_r] = 4
    p.step(L.rim & ~p.solid, 1)
    glint = lip_r & (hash01(p.x // 2, p.y, seed + 7) < 0.25) & shift(lip_r, 1, 0, False)
    p.t[glint] = 5
    chip = fc & (L.depth == 1) & (hash01(p.x // 3, p.y, seed + 8) < 0.3)
    p.t[chip] = 4
    # the foot: dark, the contact line
    foot = fc & (L.depth >= L.fh - 2)
    p.step(foot, -1, lo=1)
    p.t[fc & (L.depth == L.fh - 1)] = np.minimum(p.t[fc & (L.depth == L.fh - 1)], 1)
    # the face's ends: the west end wraps into the light, the east end into shade
    w_end = fc & ~shift(fc, 1, 0, False)
    e_end = fc & ~shift(fc, -1, 0, False)
    for i in range(3):
        we = shift(w_end, i, 0, False) & fc
        ee = shift(e_end, -i, 0, False) & fc
        p.step(we & (p.t < 4), 1 if i < 2 else 0)
        p.step(ee, -1 if i < 2 else -1, lo=1 if i else 0)
    despeckle(p, fc & ~lip_r & ~glint)
    p.solid |= fc
    p.walk &= ~fc


def draw_bands(p: Plot, L: Layout, seed=0):
    """The side bands (soft grid: 5 px): where a top ends to the west or east above lower
    ground, its last 5 px are the slope seen edge-on, a column of lumps in the top's own
    ground, lit when it faces west and in its two darkest tones when it faces east, with a
    dark line where it meets the ground below. Back rims (a top's north edge over lower
    ground) get a lit lip and a hidden drop that stops a walker."""
    T = L.T
    seen = L.tier_seen()
    band_w = np.zeros(p.f.shape, bool)
    band_e = np.zeros(p.f.shape, bool)
    for k in range(1, int(T.max()) + 1):
        topk = L.top(k)
        low = (seen >= 0) & (seen < k)
        for i in range(1, STRIP + 1):
            band_w |= topk & shift(low, i, 0, False)
            band_e |= topk & shift(low, -i, 0, False)
        back = topk & shift(low, 0, 1, False)                # the north edge of a top
        p.step(back, 1)
        drop = low & shift(topk, 0, -1, False) & ~L.face     # the edge it drops away behind
        p.t[drop] = EDGE_T
        p.step(low & shift(topk, 0, -2, False) & ~L.face & ~drop, -1)
        p.walk &= ~(dilate(back, 1) & topk)
        p.walk &= ~(topk & (shift(low, 0, 1, False) | shift(low, 0, 2, False) | shift(low, 0, 3, False)))
    lump = ((p.y // 3 + p.x // 2) % 2 == 0)
    bw = band_w & ~band_e
    p.t[bw] = np.where(lump[bw], 4, 3)
    p.f[bw & lump] = WARM[p.f[bw & lump]]
    p.t[band_e] = np.where(lump[band_e], 2, 1)
    p.f[band_e & lump] = COOL[p.f[band_e & lump]]
    # the outer edge of each band: a dark line on the ground side
    edge_w = shift(bw, -1, 0, False) & ~bw & ~L.face
    edge_e = shift(band_e, 1, 0, False) & ~band_e & ~L.face
    p.t[edge_w] = np.minimum(p.t[edge_w], 1)
    p.t[edge_e] = EDGE_T
    p.solid |= bw | band_e
    p.walk &= ~(bw | band_e)
    return bw, band_e


def tier_shadows(p: Plot, L: Layout, k_tones=2, throw=8):
    """Each tier throws its shadow down and to the right onto lower ground (soft grid: 8 px
    whatever the height, a little longer in the desert): two tones down, one at its tail."""
    T, seen = L.T, L.tier_seen()
    n = int(round(throw * DESERT_THROW))
    for k in range(1, int(T.max()) + 1):
        body = (T >= k) | (L.face & (L.kf >= k))
        sh = np.zeros(p.f.shape, bool)
        tail = np.zeros(p.f.shape, bool)
        for i in range(1, n + 1):
            s = shift(body, i, i // 3, False)
            (sh if i <= n - 3 else tail)[...] |= s
        low = (seen >= 0) & (seen < k) & ~p.solid
        cast(p, sh & low, k_tones)
        cast(p, tail & ~sh & low, 1)


def talus(p: Plot, L: Layout, seed=0, every=36, ramp='adobe', reach=7):
    """Talus at every face's foot: a skirt of fallen rock in the beds' colours, cobbles and a
    boulder now and then against the foot (an obstacle; paths keep their distance)."""
    foot = shift(L.face & (L.depth == L.fh - 1), 0, 1, False) & ~L.face & ~p.solid
    zone = np.zeros(p.f.shape, bool)
    for d in range(reach):
        zone |= shift(foot, 0, d, False)
    zone &= ~L.face & ~p.solid
    wob = fbm(p.x, p.y, 7, seed) * reach
    dd = np.zeros(p.f.shape)
    for d in range(reach, 0, -1):
        dd = np.where(shift(foot, 0, d - 1, False), d, dd)
    zone &= dd <= wob + 1
    p.put(zone & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.6), f'{ramp}_cool', 3)
    p.step(zone & shift(foot, 0, 0, False), -1)
    rams = (ramp, f'{ramp}_warm', 'clay_cool', 'sand_warm', 'stone_warm')
    stamp(p, zone, 0.12, seed + 8, FLAT, swap='mix')
    stamp(p, zone, 0.03, seed + 9, BLADES, ramp='grass_warm', tone=3, same_family=False)
    for (x, y) in _scatter(zone, 14, seed + 2, margin=0):
        pebble(p, x, y, rams[int(hash01(x, y, seed + 3) * len(rams))], 2 + int(hash01(x, y, 4) * 3), 2)
    for i, (x, y) in enumerate(_scatter(dilate(foot, 1) & ~L.face, every * every // 3, seed + 5, margin=0)):
        if hash01(x, y, seed + 6) < 0.55 or p.solid[max(0, y - 2):y + 3, max(0, x - 8):x + 8].any():
            continue
        sp, sh = boulder(seed + i, rams[i % len(rams)], 12 + int(hash01(i, seed, 7) * 10))
        paste(p, sp, x + 4, y + sp.h - 4, shadow=sh, block=sp.m & (sp.y > sp.fy - 5))
    return zone


def stair(p: Plot, L: Layout, x0, width=40, seed=0, ramp='adobe', k=None):
    """A stair cut through a face (soft grid: 40 px open between 4 px cheeks, 4 px risers):
    the treads lit along their nose, each riser a dark line, worn in the middle, the west
    cheek lit and the east cheek dark. Its column is opened to a walker."""
    col = (p.x >= x0) & (p.x < x0 + width + 8) & L.face
    if k is not None:
        col &= L.kf == k
    if not col.any():
        return np.zeros(p.f.shape, bool)
    cheek_w = col & (p.x < x0 + 4)
    cheek_e = col & (p.x >= x0 + width + 4)
    run = col & ~cheek_w & ~cheek_e
    d = L.depth
    r = d % 4
    p.put(run, ramp, 3)
    # each tread laid in slabs 8 to 14 long, the joints offset from tread to tread
    sw = 8 + (hash01(d // 4, 0, seed) * 7).astype(int)
    slab = (p.x - x0 + (hash01(d // 4, 1, seed) * 9).astype(int)) // sw
    sib = hash01(slab, d // 4, seed)
    p.f[run & (sib < 0.4)] = IDX[f'{ramp}_warm']
    p.f[run & (sib > 0.7)] = IDX[f'{ramp}_cool']
    p.t[run & (r == 0)] = 4                       # the nose of each tread
    p.t[run & (r == 3)] = 1                       # the riser under the next tread
    p.t[run & (r == 2)] = 2
    sj = run & (slab != shift(slab, 1, 0, -1)) & (r < 3)
    p.t[sj] = 2
    p.t[run & (r == 2) & (sib > 0.85)] = 3
    chip = run & (r == 1) & (hash01(p.x // 2, d // 4, seed + 3) < 0.18)
    p.t[chip | (shift(chip, 1, 0, False) & run & (r == 1))] = 2
    grit = run & (r < 2) & (hash01(p.x // 2, d, seed + 4) < 0.12)
    p.f[grit] = IDX['sand_cool']
    worn = run & (np.abs(p.x - (x0 + 4 + width / 2)) < width * 0.22) & (r == 1)
    p.t[worn] = 4
    p.put(cheek_w, f'{ramp}_warm', 4)
    p.t[cheek_w & (p.x == x0 + 3)] = 3
    p.t[cheek_w & (p.x == x0)] = 1
    p.put(cheek_e, f'{ramp}_cool', 1)
    p.t[cheek_e & (p.x == x0 + width + 4)] = 2
    p.walk[run] = True
    p.solid[run] = False
    # open the back rim above the stair and the bands round its head
    head = (p.x >= x0 + 4) & (p.x < x0 + width + 4) & ~L.face
    for dd in range(1, 6):
        p.walk |= head & shift(run & (L.depth == 0), 0, -dd, False)
    return run


def rimrock(p: Plot, L: Layout, seed=0, reach=14):
    """Bare rock along every top's edge where it drops away (rims, side bands, back rims):
    the caprock shows through the thin soil there, so each tier reads by its pale rocky
    edge, as mesas and canyon rims do. Returns the mask painted."""
    seen = L.tier_seen()
    m = np.zeros(p.f.shape, bool)
    for k in range(1, int(L.T.max()) + 1):
        topk = L.top(k)
        low = L.face | ((seen >= 0) & (seen < k))
        d = dist_to(low, reach + 4)
        wob = fbm(p.x, p.y, 11, seed + k) * reach
        m |= topk & (d <= 2 + wob) & ~p.solid
    caprock(p, m, seed)
    return m


def caprock(p: Plot, m, seed=0, ramp='sand'):
    """A mesa's or butte's top: the caprock bare in broad slabs split by joints (each slab a
    sibling, its north-west edge lit, its joints dark and holding blown sand), pockets of
    sand and a little scrub where soil has gathered."""
    m = np.asarray(m, bool)
    d1, d2, cid, vx, vy = voronoi(p, 22, seed, 0.8)
    pick = hash01(cid, 0, seed + 1)
    fam = np.where(pick < 0.33, IDX[f'{ramp}_warm'], np.where(pick < 0.66, IDX['adobe_warm'], IDX[f'{ramp}_cool']))
    p.f[m] = fam[m]
    p.t[m] = 3
    gap = d2 - d1 + (fbm(p.x, p.y, 5, seed + 2) - 0.5) * 1.4
    joint = m & (gap < 1.2)
    p.step(m & ~joint & (gap < 2.6) & ((vx + vy) > 0), 1)
    p.step(m & ~joint & (gap < 2.6) & ((vx + vy) <= 0), -1)
    p.put(joint, 'adobe_cool', 2)
    p.put(joint & (gap < 0.5), 'adobe_cool', 1)
    p.put(joint & (hash01(p.x // 2, p.y // 2, seed + 3) < 0.5), 'sand_cool', 2)
    inner = m & ~joint & (gap >= 2.6)
    stamp(p, inner, 0.08, seed + 4, FLAT, swap='mix')
    pocket = m & (fbm(p.x, p.y, 14, seed + 5) > 0.68) & erode(m, 3)
    base(p, pocket, [('sand', 0.5), ('sand_warm', 0.5)], seed + 6, 6)
    stamp(p, pocket, 0.03, seed + 7, BLADES, ramp='grass_warm', tone=3, same_family=False)
    despeckle(p, m)
    return pocket


# --- paths and water in the desert -------------------------------------------------------------
def trail(p: Plot, pts, width=16, seed=0, ramp='path'):
    """A trodden trail (size guide: a mountain trail 16): packed earth worn lighter along the
    middle where feet go, its edges ragged into the ground beside it, gravel kicked to the
    sides, a step down at the edge of each top it leaves. Walkable."""
    ch = Channel(p, pts, reach=width)
    hw = width / 2
    wob = (fbm(ch.s, np.sign(ch.n), 14, seed) - 0.5) * 4
    m = ch.near & (np.abs(ch.n) <= hw + wob) & ~p.solid & ~dilate(p.wet, 3)
    edge = m & (np.abs(ch.n) > hw + wob - 2.5)
    rag = edge & (hash01(p.x // 2, p.y // 2, seed + 1) < 0.45)
    m &= ~rag
    base(p, m, [(f'{ramp}_warm', 0.35), (ramp, 0.4), ('sand_cool', 0.25)], seed + 2, 7)
    worn = m & (np.abs(ch.n) < hw * 0.45) & (fbm(p.x, p.y, 9, seed + 3) > 0.42)
    p.step(worn, 1)
    stamp(p, m, 0.06, seed + 4, FLAT, swap='mix')
    ring = dilate(m, 1) & ~m & ~p.solid
    p.step(ring & (hash01(p.x, p.y, seed + 5) < 0.6), -1)
    for (x, y) in _scatter(edge & m, 40, seed + 6, margin=0):
        pebble(p, x, y, ('stone', 'adobe_cool', 'stone_warm')[(x + y) % 3], 2, 2, k=1)
    despeckle(p, m)
    p.walk |= m & ~p.solid
    return ch, m


def lush(p: Plot, m, seed=0):
    """The oasis's green: irrigated grass and clover, bright under the palms, with a few
    flowers, never a flat fill."""
    m = np.asarray(m, bool)
    base(p, m, [('grass', 0.4), ('grass_warm', 0.3), ('grass_cool', 0.3)], seed, 9)
    texture(p, m, seed + 1, swaps=0.14, ups=0.03, downs=0.03)
    stamp(p, m, 0.03, seed + 2, BLADES, ramp='grass_warm', tone=4, same_family=False)
    stamp(p, m, 0.02, seed + 3, BLADES, ramp='leaf', tone=2, same_family=False)
    stamp(p, m & (fbm(p.x, p.y, 15, seed + 4) > 0.6), 0.012, seed + 5, DOMINOES, ramp='plaster', tone=5,
          same_family=False)
    stamp(p, m & (fbm(p.x, p.y, 15, seed + 6) > 0.62), 0.01, seed + 7, DOMINOES, ramp='berry_warm', tone=4,
          same_family=False)
    despeckle(p, m)


def pool(p: Plot, cx, cy, rx, ry, seed=0, bank=3):
    """A spring pool, its surface a few px below the land: the north bank's face in damp
    earth under a lip of grass, the water dark under that bank and in the middle, lighter
    over the sandy shallows to the south, lit streaks lying across it, glints in pairs, the
    spring's stones at its head. Water blocks a walker."""
    w = blob(cx, cy, rx, ry, p.f.shape, seed, wob=0.12, lobes=5)
    face = w & ~shift(w, 0, bank, False)            # the top `bank` rows under the north shore
    water = w & ~face
    ed = edge_dist(water, 10)
    v = (p.y + 0.5 - (cy - ry)) / (2 * ry)
    tone = np.where(ed <= 2, 3, np.where(ed <= 5, 2, 1))
    tone = np.where((v > 0.72) & (ed <= 4), 4, tone)            # the shallows to the south
    tone = np.where(shift(face, 0, 1, False) & water, 1, tone)  # dark under the north bank
    fam = np.where(fbm(p.x, p.y, 12, seed + 1) > 0.55, IDX['water_cool'], IDX['water'])
    fam = np.where((v > 0.72) & (ed <= 4), IDX['lagoon'], fam)
    p.f[water] = fam[water]
    p.t[water] = tone[water]
    streak = water & (ed > 3) & ((p.y + seed) % 7 == 0) & (hash01(p.x // 6, p.y, seed + 2) < 0.3)
    p.step(streak, 1)
    glint = water & (ed > 3) & (hash01(p.x // 2, p.y // 2, seed + 3) < 0.025) & (p.x % 2 == 0)
    p.t[glint | (shift(glint, 1, 0, False) & water)] = 5
    p.put(face, 'earth_warm', 3)
    p.t[face & ~shift(face, 0, 1, False)] = 4
    p.t[face & ~shift(face, 0, -1, False)] = 1
    stamp(p, face, 0.2, seed + 4, DOMINOES, swap='mix')
    lip = shift(face, 0, -1, False) & ~w
    p.put(lip, 'grass_warm', 4)
    rim_s = ~w & shift(water, 0, -1, False)
    p.put(rim_s, 'sand_warm', 4)
    # algae and weed in the shallows, a pale reflection of the sky in the open water
    shallow = water & (ed <= 4) & (ed > 1)
    stamp(p, shallow & (fbm(p.x, p.y, 8, seed + 5) > 0.6), 0.10, seed + 6, SMALL, ramp='grass_cool', tone=2,
          same_family=False)
    # the spring's clear water shows its bed: weed beds dark, sandy hollows paler
    weed = water & (ed > 3) & (fbm(p.x, p.y, 11, seed + 11) > 0.64)
    weed = dilate(erode(weed, 1), 1)
    p.put(weed, 'lagoon_cool', 1)
    sandy = water & (ed > 3) & (fbm(p.x, p.y, 14, seed + 13) < 0.3) & ~weed
    sandy = dilate(erode(sandy, 1), 1) & water & ~weed
    p.put(sandy, 'water', 3)
    sky = water & (ed > 4) & (fbm(p.x, p.y, 12, seed + 7) > 0.6) & ~weed
    sky = dilate(erode(sky, 1), 1) & water & ~weed
    p.put(sky, 'water_warm', 3)
    p.wet |= water
    p.walk &= ~w
    p.solid |= face
    return w


def ditch(p: Plot, pts, seed=0, width=6, lining='adobe'):
    """An irrigation channel (acequia): water a hand's width wide in an adobe-lined cut, the
    north lining's face lit, a coping along each side, the water dark under the north side,
    a plank bridge where a path crosses. Water blocks a walker except at the planks."""
    ch = Channel(p, pts, reach=width + 6)
    hw = width / 2
    cut = ch.near & (np.abs(ch.n) <= hw + 2)
    water = ch.near & (np.abs(ch.n) <= hw - 0.5)
    coping = cut & ~water
    p.put(coping, lining, 3)
    sib = hash01((ch.s // 11).astype(int), np.sign(ch.n).astype(int), seed)
    p.f[coping & (sib < 0.4)] = IDX[f'{lining}_warm']
    p.f[coping & (sib > 0.75)] = IDX[f'{lining}_cool']
    p.t[coping & ~shift(cut, 0, 1, False)] = 2
    p.t[coping & ~shift(cut, 0, -1, False)] = 4
    p.t[coping & (((ch.s.astype(int)) % 11) == 0)] = 2
    p.put(water, 'water', 2)
    p.t[water & ~shift(water, 0, 1, False)] = 3
    p.t[water & ~shift(water, 0, -1, False)] = 1
    st = water & ((ch.s.astype(int) + seed) % 9 < 2) & (np.abs(ch.n) < 1)
    p.step(st, 2)
    p.wet |= water
    p.walk &= ~water
    return ch, water


def oasis(p: Plot, m, pool_at, channel, seed=0, reach=46, palms=7):
    """An oasis edge (Palm Spring): a spring pool, lush grass round it under date palms and
    a ring of reeds in the shallows, an irrigation channel leading the water away, and the
    green fading downstream: wide and bright by the pool, a narrowing strip along the
    channel, tongues and islands of green out in the scrub, then scrub. Returns the pool."""
    m = np.asarray(m, bool)
    cx, cy, rx, ry = pool_at
    u, v = (p.x + 0.5 - cx) / rx, (p.y + 0.5 - cy) / ry
    dp = (np.sqrt(u * u + v * v) - 1) * min(rx, ry)
    ch = Channel(p, channel, reach=60)
    frac = np.clip(ch.s / max(1, ch.length), 0, 1)
    dc = np.where(ch.near, np.abs(ch.n), 999)
    wet = np.maximum(np.clip(1 - dp / reach, 0, 1),
                     np.clip(1 - dc / (6 + 26 * (1 - frac) ** 1.4), 0, 1) * (1 - frac * 0.6))
    t = 1 - wet
    snap = p.snap()

    def pa(q, mm):
        lush(q, mm, seed + 1)

    def pb(q, mm):
        q.restore(snap)
    green = ~blend(p, m, np.clip(t * 1.15 - 0.05, 0, 1), pa, pb, seed + 2, warp=0.35, outliers=0.12)
    green &= m
    ditch(p, channel, seed + 3)
    w = pool(p, cx, cy, rx, ry, seed + 4)
    # reeds in the shallows round the south and west of the pool
    ring = w & ~erode(w, 3) & ~p.solid & (v > -0.3)
    for i, (x, y) in enumerate(_scatter(ring, 60, seed + 5, margin=0)):
        if hash01(x, y, seed + 9) < 0.45:
            continue
        sp, sh = reeds('reed', seed + 30 + i, 4 + i % 3)
        paste(p, sp, x, y, shadow=sh)
    # palms round the pool and up the channel
    feet = []
    ringp = m & (dp > 8) & (dp < reach * 0.8) & green & ~p.solid
    for i, (x, y) in enumerate(_scatter(ringp, 900, seed + 6, margin=2)):
        if len(feet) >= palms:
            break
        if any(abs(x - fx) < 22 and abs(y - fy) < 16 for fx, fy in feet):
            continue
        sp, sh = palm(0 if i % 3 else 1, seed + 40 + i)
        paste(p, sp, x, y, shadow=sh, block=None)
        feet.append((x, y))
    return w, ch, green, feet


# --- transitions: bands, not lines ---------------------------------------------------------------
def blend(p: Plot, m, t, paint_a, paint_b, seed=40, warp=0.75, outliers=0.18):
    """Two grounds mixed over a band, never along a line (world plan 5.1: bands, not lines).
    `t` runs 0 (all A) to 1 (all B) across the band; the edge between them is warped at two
    scales, so tongues of each reach into the other, and islands of each (outliers) lie
    beyond it on both sides. Returns the mask that took B."""
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
    for attr in ('solid', 'walk'):
        av, bv = getattr(a, attr), getattr(b, attr)
        cur = getattr(p, attr)
        cur[m] = np.where(sel, bv, av)[m] if attr == 'solid' else (cur & np.where(sel, bv, av))[m]
    seam = m & dilate(sel, 2) & ~erode(sel, 2) & ~p.solid
    spill = seam & (hash01(p.x // 2, p.y // 2, seed + 4) < 0.35)
    src_b = spill & ~sel & ~b.solid
    src_a = spill & sel & ~a.solid
    p.f[src_b], p.t[src_b] = b.f[src_b], b.t[src_b]
    p.f[src_a], p.t[src_a] = a.f[src_a], a.t[src_a]
    despeckle(p, seam)
    return sel


# --- the sample scene: a canyon descent to an oasis under a mesa --------------------------------
SAMPLE_W, SAMPLE_H = 640, 576
TRAIL = [(318, -12), (300, 60), (334, 120), (306, 176), (288, 214), (288, 300), (300, 352), (352, 384),
         (384, 420), (378, 470), (412, 512), (470, 538), (520, 590)]
WASH = [(-16, 344), (90, 336), (180, 350), (262, 340), (350, 352), (410, 380), (432, 420)]
CHANNEL = [(492, 486), (540, 500), (590, 520), (660, 548)]
POOL = (456, 452, 44, 26)


def sample_tiers(seed=1):
    """The tier map (tops as seen): the plateau at tier 2 north of the canyon and on its
    south-west side, a mesa at tier 3 on the plateau, the canyon floor and the plain at 0,
    and a butte (tier 2) standing at the canyon's mouth."""
    W, H = SAMPLE_W, SAMPLE_H
    y, x = np.mgrid[0:H, 0:W]
    T = np.zeros((H, W), np.int8)
    rim = 216 + 8 * np.sin(x / 61.0) + 5 * np.sin(x / 23.0 + 1)
    rim = np.where(x > 392, rim - (x - 392) * 0.72, rim)
    T[y < rim] = 2
    south = (y > 398 + 6 * np.sin(x / 40.0)) & (x < np.where(y < 476, 296, 280))
    T[south] = 2
    mesa = blob(156, 92, 118, 52, (H, W), seed, wob=0.10, lobes=4) & (y < 150)
    T[mesa] = 3
    butte = blob(588, 330, 30, 22, (H, W), seed + 2, wob=0.08, lobes=5)
    T[butte] = 2
    # the soft grid: snap to 8 px cells, then round and let the edges wander
    cells = T[4::GRID, 4::GRID]
    T = np.kron(cells, np.ones((GRID, GRID), np.int8))[:H, :W]
    return smooth_tiers(T, seed, 6, 1.5)


def sample(seed=1):
    W, H = SAMPLE_W, SAMPLE_H
    p = Plot(W, H)
    L = Layout(sample_tiers(seed), FACE_MESA)
    t0, t2, t3 = L.top(0), L.top(2), L.top(3)
    # grounds, tier by tier
    scrub(p, t0, seed + 1, every=1300)
    hardpan_ground(p, t2, seed + 2, ramp='sand')
    hardpan(p, t2 & (fbm(p.x, p.y, 40, seed + 3) > 0.6) & erode(t2, 10), seed + 4)
    rimrock(p, L, seed + 5)
    clump = np.clip(fbm(p.x, p.y, 50, seed + 17) * 2.2 - 0.7, 0.0, 1)
    scrub_plants(p, t2 & ~p.solid, seed + 18, 1500, density=clump)
    caprock(p, t3, seed + 5)
    plant(p, t3 & erode(t3, 8), 2200, [sage, tussock_sprite], seed + 6)
    # the canyon floor: a dry wash down its middle, gravel and badlands at its mouth
    ch, bed = wash(p, WASH, 44, seed + 7, logs=1)
    mouth = t0 & (p.x > 300) & (p.x < 420) & (p.y > 470) & ~p.solid
    gravel(p, mouth & (fbm(p.x, p.y, 30, seed + 8) > 0.5), seed + 9)
    badlands(p, t0 & (p.x > 140) & (p.x < 300) & (p.y > 300) & (p.y < 330) & ~bed, seed + 10, every=99999)
    # the oasis at the canyon's mouth
    oasis(p, t0 & (p.y > 360) & (p.x > 330), POOL, CHANNEL, seed + 11, reach=64, palms=7)
    # height
    draw_faces(p, L, seed=seed + 12)
    draw_bands(p, L, seed + 13)
    tier_shadows(p, L)
    talus(p, L, seed + 14)
    st = stair(p, L, 266, 40, seed + 15, k=2)
    # the trail: from the plateau's north edge down the stair, across the wash, to the pool
    trail(p, TRAIL, 16, seed + 16)
    for (x, y) in ((402, 300), (240, 168), (360, 120), (196, 470), (560, 420)):
        sp, sh = boulder(seed + x, 'adobe')
        if not p.solid[max(0, y - 10):y + 2, max(0, x - 12):x + 12].any():
            paste(p, sp, x, y, shadow=sh, block=sp.m & (sp.y > sp.fy - 6))
    for (x, y) in ((356, 70), (230, 250), (520, 300)):
        sp, sh = saguaro(seed + x)
        if not p.solid[max(0, y - 4):y + 2, max(0, x - 6):x + 6].any():
            paste(p, sp, x, y, shadow=sh)
    return p, {'layout': L, 'wash': ch, 'stair': st}


# --- the fire country --------------------------------------------------------------------------
def ash_ground(p: Plot, m, seed=0):
    """Deep ash: a calm grey plane in broad patches of the ash ramp and its siblings, drifts
    combed by the sea wind into soft ridges (lit on the windward west), lapilli of cinder in
    pairs, a few dead grass tufts sticking through."""
    m = np.asarray(m, bool)
    base(p, m, [('ash', 0.4), ('ash_warm', 0.3), ('ash_cool', 0.3)], seed, 12)
    along = p.x * 0.35 + p.y
    drift = ((along + (fbm(p.x, p.y, 30, seed + 1) - 0.5) * 40) / 9.0) % 1.0
    p.step(m & (drift < 0.16), 1)
    p.step(m & (drift > 0.16) & (drift < 0.26), -1)
    texture(p, m, seed + 2, swaps=0.09, ups=0.015, downs=0.02, shapes=FLAT)
    for (x, y) in _scatter(m, 90, seed + 3, margin=1):
        pebble(p, x, y, ('basalt', 'basalt_warm', 'clay_cool')[(x + 2 * y) % 3], 2, 2, k=1)
    stamp(p, m & (fbm(p.x, p.y, 20, seed + 4) > 0.72), 0.006, seed + 5, BLADES, ramp='bleached', tone=3,
          same_family=False)
    despeckle(p, m & ~p.solid)


def ash(p: Plot, m, t, seed=0):
    """Ash blown north by the sea wind, thinning over whatever lies beneath (`t` from 0, a
    dusting, to 1, deep ash): deep ash buries the ground and the small plants; thinner ash
    lies in drifts and tongues with the ground showing through; at the thin end only a grey
    dust in clusters, and the bushes and grass greyed where it settled on their tops."""
    m = np.asarray(m, bool)
    t = np.broadcast_to(np.asarray(t, float), p.f.shape)
    snap = p.snap()

    def pa(q, mm):
        q.restore(snap)

    def pb(q, mm):
        ash_ground(q, mm, seed)
    deep = blend(p, m, np.clip(t * 1.4 - 0.4, 0, 1), pa, pb, seed + 1, warp=0.5, outliers=0.15)
    thin = m & ~deep
    dust = thin & (fbm(p.x, p.y, 6, seed + 2) < t * 0.9) & ~p.solid
    stamp(p, dust, np.clip(t * 0.5, 0, 0.5)[...], seed + 3, FLAT, ramp='ash_warm', tone=3, same_family=False)
    stamp(p, dust, np.clip(t * 0.2, 0, 0.2)[...], seed + 4, DOMINOES, ramp='ash', tone=4, same_family=False)
    on_plants = thin & p.solid & (p.t >= 3) & (p.t < EDGE_T) & ~GLOW[p.f] & \
        (hash01(p.x, p.y, seed + 5) < t * 0.7) & ~shift(p.solid, 0, -1, False) | \
        (thin & p.solid & (p.t >= 3) & (p.t < EDGE_T) & (hash01(p.x // 2, p.y, seed + 6) < t * 0.35))
    p.f[on_plants] = np.where(hash01(p.x, p.y, seed + 7)[on_plants] < 0.5, IDX['ash_warm'], IDX['ash'])
    return deep


def old_flow(p: Plot, m, seed=0, flow=(0.3, 1.0), toe=5):
    """An old crusted lava flow: weathered basalt in ropy folds (arcs bowed downstream, lit
    on their upper side), pressure ridges split by cracks, grey-green and ochre lichen in
    clusters, ash in its hollows, a raised blocky edge whose south face shows, and scrub
    and fireweed rooting along its margins. Walkable on its back, not up its face."""
    m = np.asarray(m, bool)
    fx, fy = flow
    nn = math.hypot(fx, fy)
    fx, fy = fx / nn, fy / nn
    along = p.x * fx + p.y * fy
    across = -p.x * fy + p.y * fx
    base(p, m, [('basalt_warm', 0.35), ('basalt', 0.35), ('ash_cool', 0.3)], seed, 10)
    lobe = fbm(p.x, p.y, 40, seed + 1)
    rope = ((along - 0.012 * (across - across.mean()) ** 2 * (0.6 + lobe) + (fbm(p.x, p.y, 16, seed + 2) - 0.5) * 18)
            / 4.0) % 1.0
    zone = m & erode(m, 2)
    p.step(zone & (rope < 0.22), 1)
    p.step(zone & (rope > 0.22) & (rope < 0.4), -1)
    d1, d2, cid, vx, vy = voronoi(p, 26, seed + 3)
    crack = zone & (d2 - d1 < 1.1) & (fbm(p.x, p.y, 13, seed + 4) > 0.45)
    p.t[crack] = 1
    p.step(shift(crack, 1, 1, False) & zone & ~crack, 1)
    hollow = zone & (fbm(p.x, p.y, 11, seed + 5) > 0.68)
    p.put(hollow, 'ash_warm', 3)
    stamp(p, hollow, 0.1, seed + 6, FLAT, swap='mix')
    lich = zone & ~hollow & (fbm(p.x, p.y, 9, seed + 7) > 0.6)
    stamp(p, lich, 0.05, seed + 8, SMALL, ramp='grass_cool', tone=4, same_family=False)
    stamp(p, lich, 0.03, seed + 9, SMALL, ramp='brass_cool', tone=4, same_family=False)
    stamp(p, zone, 0.06, seed + 10, FLAT, swap='mix')
    # the flow's edge: a blocky toe whose south face shows
    toe_m = m & ~shift(m, 0, -toe, False)
    p.put(toe_m, 'basalt', 2)
    blocks = (p.x // 4 + (p.y // 3) * 3) % 5
    p.t[toe_m & (blocks == 0)] = 3
    p.t[toe_m & ~shift(toe_m, 0, 1, False)] = 3
    p.t[toe_m & ~shift(m, 0, -1, False)] = 1
    p.t[toe_m & ((p.x + seed) % 6 == 0)] = 1
    side = m & ~erode(m, 1) & ~toe_m
    p.step(side, -1)
    despeckle(p, m)
    p.solid |= toe_m
    p.walk &= ~toe_m
    # life at the margins: scrub, fireweed
    marg = dilate(m, 10) & ~m & ~p.solid
    inner = m & ~erode(m, 12) & ~toe_m & ~dilate(toe_m, 3)
    plant(p, marg, 700, [fireweed, sage, fireweed, tussock_sprite], seed + 11)
    plant(p, inner, 900, [fireweed, tussock_sprite], seed + 12)
    return toe_m


def young_flow(p: Plot, m, seed=0, channel=None, width=28, crust=6):
    """A young lava flow, the barrier: dark crust plates (each a sibling of basalt, its
    north-west edge lit, the plates tilted against each other) with cracks that glow from
    the lava beneath, an open channel down the middle running bright between levees of
    fresh crust (4 to 8 px), and a margin of hot grey rubble. Nothing walks on it except a
    causeway; nothing green grows within 64 px of it (`--check`)."""
    m = np.asarray(m, bool)
    d1, d2, cid, vx, vy = voronoi(p, 13, seed, 0.9)
    pick = hash01(cid, 0, seed + 1)
    fam = np.where(pick < 0.4, IDX['basalt'], np.where(pick < 0.75, IDX['basalt_cool'], IDX['basalt_warm']))
    p.f[m] = fam[m]
    p.t[m] = np.where(pick > 0.85, 2, 1)[m]
    gap = d2 - d1
    se = (vx + vy) > 0
    p.step(m & (gap < 3.2) & (gap >= 1.2) & se, 1)
    p.step(m & (gap < 2.2) & (gap >= 1.2) & se & (pick < 0.5), 1)
    stamp(p, m & (gap > 3), 0.14, seed + 2, FLAT, swap='mix')
    # ropy wrinkles on each plate's skin, lit on their upper side
    wr = m & (gap > 2.2) & (((p.y + (vnoise(p.x, cid, 5, seed + 9) * 4).astype(int)) % 3) == 0) & \
        (hash01(cid, 2, seed + 10) < 0.7)
    p.step(wr, 1, hi=3)
    stamp(p, m & (gap > 3), 0.04, seed + 11, DOMINOES, ramp='ash_cool', tone=2, same_family=False)
    crack = m & (gap < 1.2) & (fbm(p.x, p.y, 10, seed + 3) > 0.38)
    p.put(crack, 'lava', 2)
    p.put(crack & (gap < 0.5) & (fbm(p.x, p.y, 7, seed + 4) > 0.55), 'lava', 3)
    p.lava |= crack
    ch = None
    if channel is not None:
        ch = Channel(p, channel, reach=width)
        hw = width / 2
        open_ = m & ch.near & (np.abs(ch.n) <= hw - crust)
        lev = m & ch.near & (np.abs(ch.n) <= hw) & ~open_
        p.put(lev, 'basalt', 1)
        p.t[lev & (np.abs(ch.n) > hw - 2)] = 2
        p.t[lev & (np.abs(ch.n) <= hw - crust + 1.5)] = 3
        p.f[lev & (hash01(p.x // 3, p.y // 2, seed + 5) < 0.4)] = IDX['basalt_warm']
        p.put(lev & (np.abs(ch.n) <= hw - crust + 1.5) & (ch.n < 0), 'basalt_warm', 4)
        depth = hw - crust - np.abs(ch.n)
        tone = np.where(depth > 5, 4, np.where(depth > 2, 3, 2))
        p.put(open_, 'lava', tone)
        vein = open_ & (((ch.s * 0.5 + (fbm(p.x, p.y, 8, seed + 6) - 0.5) * 6) % 5) < 1.2) & (depth > 2)
        p.step(vein, 1, hi=5)
        skin = open_ & (fbm(ch.s, ch.n, 6, seed + 7) > 0.66) & (depth > 1)
        p.put(skin, 'basalt_cool', 1)
        p.put(skin & shift(~skin, 1, 1, False) & open_, 'lava', 2)
        p.lava |= open_ & ~skin
        p.lava |= skin & ~erode(skin, 1)
    edge = m & ~erode(m, 3)
    p.put(edge & (hash01(p.x // 2, p.y // 2, seed + 8) < 0.6), 'ash_cool', 2)
    p.solid |= m
    p.walk &= ~m
    return ch


def lava_frames(p: Plot):
    """The moving lava, as water_flow.py draws it for the zones (slow bright veins creeping
    with the flow), recoloured onto the lava glow ramp: a changed pixel moves one tone up
    its own ramp. 8 frames of 150 ms; the renderer holds frame 0 with reduced motion or when
    the screen is inactive. Returns (frames, box)."""
    import water_flow
    img = p.image()
    lava = {(int(x), int(y)) for y, x in zip(*np.nonzero(p.lava))}
    res = water_flow.sheet(img, set(), lava)
    if res is None:
        return [img], None
    stack, (x0, y0, bw, bh) = res
    a = np.asarray(stack)
    out = []
    for fi in range(water_flow.FRAMES):
        fr = a[fi * bh:(fi + 1) * bh]
        on = fr[..., 3] > 0
        q = Plot(p.w, p.h)
        q.f, q.t = p.f.copy(), p.t.copy()
        sel = np.zeros(p.f.shape, bool)
        sel[y0:y0 + bh, x0:x0 + bw] = on
        sel &= p.lava
        q.f[sel & ~GLOW[q.f]] = IDX['lava']
        q.t[sel] = np.clip(q.t[sel] + 1, 2, 5)
        out.append(q.image())
    return out, (x0, y0, bw, bh)


def columns(seed=0, size=11):
    """Basalt columns (size guide: a crag 40 to 96 tall, columns 8 to 12 across): hexagonal
    columns on a honeycomb, the back row standing tallest and the front rows stepping down
    like a stair, so every top shows: each top a hexagon lit to the upper left with its
    rim catching the light, each side in three facets (west lit, front body, east in
    shade), cross-joints across the sides, lichen on a few tops."""
    rows = ((3, 34, 44), (4, 20, 28), (3, 8, 14))
    cols = []
    for gy, (n, lo, hi) in enumerate(rows):
        for gx in range(n):
            cx = 6 + gx * (size - 1) + (size // 2 if gy % 2 else 0) + gy * 2
            hgt = lo + int(hash01(gx, gy, seed) * (hi - lo))
            cols.append((cx, gy * 6, hgt))
    W = 12 + 4 * size + size
    H = max(c[1] + c[2] for c in cols) + 14
    sp = Sprite(W, H, W // 2, H - 3)
    base_y = H - 4 - 12
    half = size // 2
    for (cx, cy, hgt) in sorted(cols, key=lambda c: (c[1], c[0])):
        foot = base_y + cy
        top = foot - hgt
        for y in range(top + 4, foot + 1):
            for dx in range(-half, half + 1):
                if dx < -half + 3:
                    fam, k = 'basalt_warm', 3
                elif dx < half - 2:
                    fam, k = 'basalt', 2
                else:
                    fam, k = 'basalt_cool', 1
                if (y - top + cx * 3) % 9 == 0 and -half < dx < half:
                    k = max(0, k - 1)                     # a cross-joint
                if dx in (-half + 3, half - 2):
                    k = max(0, k - 1)                     # the arrises between facets
                if y > foot - 2:
                    k = max(0, k - 1)
                sp.px(cx + dx, y, fam, k)
        for j in range(6):                                # the hexagonal top
            inset = (3, 1, 0, 0, 1, 3)[j]
            for dx in range(-half + inset, half + 1 - inset):
                k = 3
                if j <= 1 or dx <= -half + inset:
                    k = 4
                if (j == 0 or (j == 1 and dx <= -half + inset + 1)) and dx < 1:
                    k = 5
                if j == 5 or dx >= half - inset:
                    k = 2
                sp.px(cx + dx, top + j, 'ash_warm' if k >= 4 else 'basalt_warm', k)
        if hash01(cx, cy, seed + 2) < 0.4:
            for (dx, dy) in ((-1, 2), (0, 2), (0, 3)):
                sp.px(cx + dx, top + dy, 'grass_cool', 4)
    block = sp.m & (sp.y > base_y - 8)
    return sp, sp.thrown(0.5), block


def causeway(p: Plot, pts, width=24, seed=0, edge=4):
    """A basalt causeway across a flow or water: a path of column tops at one height, each a
    rough hexagon (a sibling of basalt, its north-west edge lit, its joints dark), the
    columns' sides showing along the south edge. Walkable; the only way over the young
    flow besides a bridge."""
    ch = Channel(p, pts, reach=width)
    m = ch.near & (np.abs(ch.n) <= width / 2)
    d1, d2, cid, vx, vy = voronoi(p, 9, seed, 0.35)
    pick = hash01(cid, 0, seed + 1)
    fam = np.where(pick < 0.33, IDX['basalt_warm'], np.where(pick < 0.66, IDX['basalt'], IDX['ash_cool']))
    p.f[m] = fam[m]
    p.t[m] = np.where(pick > 0.8, 4, 3)[m]
    gap = d2 - d1
    joint = m & (gap < 1.0)
    p.step(m & ~joint & (gap < 2.2) & ((vx + vy) > 0), 1)
    p.step(m & ~joint & (gap < 2.2) & ((vx + vy) <= 0), -1)
    p.t[joint] = 1
    side = shift(m, 0, edge, False) & ~m
    for d in range(1, edge + 1):
        row = shift(m, 0, d, False) & ~m
        p.f[row & side] = IDX['basalt']
        p.t[row & side] = 2 if d < edge else 1
    p.t[side & ((p.x + seed) % 9 == 0)] = 1
    p.lava &= ~(m | side)
    p.solid &= ~m
    p.solid |= side
    p.walk |= m
    p.walk &= ~side
    return m


def cinder_cone(seed=0, w=None):
    """A cinder cone (a parasitic cone on the north flank): a steep cone of loose red and
    black cinders, lit on its west flank and shaded on its east in hard steps, gullies
    raying down its sides, a crater at its top whose far inner wall catches the light."""
    w = w or 70 + int(hash01(seed, 0, 40) * 30)
    h = int(w * 0.42)
    W, H = w + 6, h + 14
    sp = Sprite(W, H, W // 2, H - 3)
    cx = sp.fx
    foot = sp.fy
    u = (sp.x + 0.5 - cx) / (w / 2)
    au = np.abs(u)
    crater_w = 0.34
    top_y = foot - h
    yt = top_y + (np.clip(au - crater_w, 0, 1) / (1 - crater_w)) ** 0.7 * h * 0.95
    yt = yt + (vnoise(sp.x, 0, 6, seed) - 0.5) * 2
    yb = foot - 3 * np.sqrt(np.clip(1 - au * au, 0, 1))
    shape = (au < 1) & (sp.y + 0.5 >= yt) & (sp.y + 0.5 <= yb + 3)
    hgt01 = np.clip((foot - sp.y) / h, 0, 1)
    red = (fbm(sp.x, sp.y, 7, seed + 1) + hgt01 * 0.45) > 0.78        # oxidised cinders near the top
    fam = np.where(red, IDX['clay_cool'], np.where(fbm(sp.x, sp.y, 5, seed + 2) > 0.5, IDX['basalt_warm'],
                                                     IDX['basalt']))
    tone = np.where(u < -0.45, 4, np.where(u < 0.05, 3, np.where(u < 0.5, 2, 1)))
    sp.put(shape, fam, tone)
    clumps = shape & (hash01(sp.x // 2, sp.y, seed + 8) < 0.22)
    sp.f[clumps] = np.where(hash01(sp.x, sp.y, seed + 9)[clumps] < 0.5, WARM[sp.f[clumps]], COOL[sp.f[clumps]])
    sp.step(clumps & (hash01(sp.x, sp.y // 2, seed + 10) < 0.3), -1, lo=1)
    gul = shape & (np.abs((u * 6 + vnoise(sp.y, 0, 7, seed + 3) * 0.6) % 1.0 - 0.5) < 0.08) & (sp.y > top_y + 4)
    sp.step(gul, -1, lo=1)
    sp.step(shift(gul, -1, 0, False) & shape & ~gul, 1)
    # the crater: an ellipse at the top; its south inner wall hidden, its north inner wall lit
    cr = ((sp.x + 0.5 - cx) / (w * crater_w * 0.5)) ** 2 + ((sp.y + 0.5 - (top_y + 4)) / 4.5) ** 2 <= 1
    sp.put(cr & shape | cr, 'basalt', 1)
    far = cr & (sp.y + 0.5 < top_y + 3.5)
    sp.put(far, 'clay_cool', 3)
    sp.put(far & (sp.x < cx), 'clay_cool', 4)
    rim = dilate(cr, 1) & ~cr & (sp.y + 0.5 > top_y + 4)
    sp.put(rim & (sp.x < cx), 'basalt_warm', 4)
    sp.put(rim & (sp.x >= cx), 'basalt_warm', 3)
    block = shape & (sp.y > foot - 10)
    sh = blob(cx + w * 0.3, foot - 2, w * 0.55, 8, sp.m.shape, seed, wob=0.05) & (sp.x > cx - 4)
    return sp, sh, block


def fumarole(p: Plot, x, y, seed=0, size=10):
    """A fumarole: a low mound of altered rock round a dark vent, crusted with yellow
    sulphur in clusters, the ground round it stained ochre and white; steam rises from it
    (`steam_frames`). The vent blocks a walker."""
    mound = blob(x, y, size, size * 0.6, p.f.shape, seed, wob=0.2, lobes=5)
    p.put(mound, 'ash_warm', 3)
    u, v = (p.x + 0.5 - x) / size, (p.y + 0.5 - y) / (size * 0.6)
    p.t[mound] = tone_of(light_of(u, v, 0.5), (0.4, -0.1, -0.6))[mound]
    stain = blob(x + 2, y + 3, size * 2.0, size * 1.1, p.f.shape, seed + 1, wob=0.25) & ~mound & ~p.solid
    stamp(p, stain, 0.22, seed + 2, SMALL, ramp='brass_cool', tone=3, same_family=False)
    stamp(p, stain, 0.08, seed + 3, SMALL, ramp='plaster', tone=4, same_family=False)
    stamp(p, mound, 0.25, seed + 4, SMALL, ramp='brass', tone=4, same_family=False)
    stamp(p, mound, 0.08, seed + 5, DOMINOES, ramp='brass_warm', tone=5, same_family=False)
    vent = blob(x, y - 1, size * 0.32, size * 0.22, p.f.shape, seed + 2, wob=0.1)
    p.put(vent, 'basalt', 0)
    p.put(shift(vent, 0, -1, False) & ~vent & mound, 'brass', 5)
    p.put(shift(vent, 0, 1, False) & ~vent & mound, 'ash_cool', 2)
    p.walk &= ~mound
    p.solid |= vent
    p.vents.append((x, y - 2, size))
    return mound


def steam_frames(p: Plot, frames=8):
    """Steam from every vent: puffs that rise, grow, drift east with the sea wind and fade
    by thinning out (pixels drop away in clusters, no transparency), on the snow ramp, lit
    on their upper left. 8 frames of 150 ms, a finite loop; the renderer holds frame 0 with
    reduced motion or when the screen is inactive. Returns RGB frames of the whole plot."""
    out = []
    for fi in range(frames):
        q = Plot(p.w, p.h)
        q.f, q.t = p.f.copy(), p.t.copy()
        for vi, (x, y, size) in enumerate(p.vents):
            for k in range(3):
                age = ((fi + k * frames / 3) % frames) / frames       # 0 born .. 1 gone
                r = 2.2 + age * size * 0.55
                cx = x + age * size * 0.9 + (hash01(vi, k, 5) - 0.5) * 2
                cy = y - 2 - age * size * 2.4
                puff = blob(cx, cy, r, r * 0.8, q.f.shape, vi * 7 + k, wob=0.2)
                keep = hash01(q.x // 2, q.y // 2, vi * 13 + k + fi) > age * 0.85
                puff &= keep
                if not puff.any():
                    continue
                u, v = (q.x + 0.5 - cx) / r, (q.y + 0.5 - cy) / (r * 0.8)
                tone = np.where(u + v < -0.5, 5, np.where(u + v < 0.4, 4, 3))
                q.f[puff] = np.where(u[puff] + v[puff] < 0, IDX['snow_warm'], IDX['snow'])
                q.t[puff] = tone[puff]
        out.append(q.image())
    return out


def hot_spring(p: Plot, x, y, seed=0, n=4, w=56):
    """A hot spring on travertine terraces (Cinder Springs): rimstone pools stepping down to
    the south, each a curved dam of cream travertine with a lit lip and a short face of
    dripstone below it, the water bright turquoise over the white floor, deeper blue at the
    source, orange and brown mats where the overflow runs, steam from the top pool. Pools
    block a walker; their rims are the way round."""
    whole = np.zeros(p.f.shape, bool)
    yy = y
    for i in range(n):
        ww = w * (0.55 + 0.15 * i) * (0.9 + 0.2 * hash01(i, 0, seed))
        hh = 10 + i * 2
        cx = x + (hash01(i, 1, seed) - 0.5) * 10 + i * 3
        dam = blob(cx, yy, ww / 2, hh / 2, p.f.shape, seed + i, wob=0.14, lobes=6)
        # the dam's south front: a face of dripstone 4 px under its lip
        face = shift(dam, 0, 4, False) & ~dam & ~whole
        p.put(face, 'plaster_cool', 3)
        drip = face & ((p.x + i) % 3 == 0)
        p.t[drip] = 2
        p.t[face & ~shift(face, 0, 1, False)] = 2
        p.t[face & ~shift(dam | face, 0, -1, False)] = 2
        mat = face & (hash01(p.x // 3, p.y, seed + i) < 0.35)
        p.put(mat, 'clay_warm', 3)
        p.put(mat & shift(mat, 0, 1, False), 'adobe_warm', 4)
        water = erode(dam, 2)
        rim = dam & ~water
        p.put(rim, 'plaster', 4)
        p.t[rim & ~shift(dam, 0, 1, False)] = 3
        p.t[rim & ~shift(dam, 1, 0, False) & (p.x < cx)] = 5
        p.t[rim & ~shift(dam, 0, -1, False) & (p.x > cx)] = 3
        ed = edge_dist(water, 6)
        tone = np.where(ed <= 1, 4, np.where(ed <= 3, 3, 2))
        p.put(water, np.where(i == 0, IDX['water'], IDX['lagoon']), tone)
        p.t[water & shift(rim, 0, 1, False) & (ed <= 1)] = 2          # dark under the north rim
        gl = water & (ed > 2) & (hash01(p.x // 2, p.y // 2, seed + 10 + i) < 0.06) & (p.x % 2 == 0)
        p.t[gl | (shift(gl, 1, 0, False) & water)] = 5
        p.wet |= water
        p.walk &= ~water
        p.solid |= face
        whole |= dam | face
        yy += hh * 0.65 + 4
    apron = dilate(whole, 6) & ~whole & ~p.solid
    stamp(p, apron, 0.25, seed + 20, SMALL, ramp='plaster_cool', tone=3, same_family=False)
    stamp(p, apron & (p.y > y + 10), 0.15, seed + 21, SMALL, ramp='clay_warm', tone=3, same_family=False)
    p.vents.append((x - 4, y - 2, 12))
    return whole


def dead_forest(p: Plot, m, seed=0, every=1100):
    """The dead forest where the east flow ran through the coastal woods: charred snags
    standing in ash with silver ones at the edge, fallen black logs, stumps, the first
    fireweed in drifts."""
    m = np.asarray(m, bool)
    ash_ground(p, m, seed)
    soil = m & (fbm(p.x, p.y, 18, seed + 1) > 0.6)
    p.put(soil, 'earth_cool', 3)
    stamp(p, soil, 0.1, seed + 2, FLAT, swap='mix')
    plant(p, m & (fbm(p.x, p.y, 20, seed + 3) > 0.58), 900, [fireweed], seed + 4)
    plant(p, m, every, [lambda s: snag(s, 'charred'), lambda s: snag(s, 'charred'), lambda s: snag(s, 'bleached'),
                        lambda s: log(s, 'charred')], seed + 5, gap=6)
    despeckle(p, m & ~p.solid)


# --- the two transition strips -------------------------------------------------------------------
def steppe_to_desert(p: Plot, m, t, seed=0):
    """Steppe into desert over a band (`t` 0 to 1 across it): the straw grass thins to scrub
    on hardpan, then to bare sand and gravel; tussocks fade out, sage comes in and goes,
    the first saguaro and prickly pear stand out ahead of the change, a green tongue
    follows a hollow into the dry side. No line: tongues and islands both ways."""
    m = np.asarray(m, bool)
    t = np.broadcast_to(np.asarray(t, float), p.f.shape)
    steppe(p, m, seed, tussocks=False)
    snap = p.snap()

    def pa(q, mm):
        q.restore(snap)

    def pb(q, mm):
        hardpan_ground(q, mm, seed + 1)
    blend(p, m, np.clip(t * 2.0 - 0.3, 0, 1), pa, pb, seed + 2, warp=0.5, outliers=0.2)
    snap2 = p.snap()

    def pc(q, mm):
        q.restore(snap2)

    def pd(q, mm):
        gravel(q, mm, seed + 3, every=60)
    blend(p, m, np.clip(t * 2.0 - 1.1, 0, 1), pc, pd, seed + 4, warp=0.45, outliers=0.15)
    for (x, y) in _scatter(m & (t < 0.55), 320, seed + 5):
        if hash01(x, y, seed + 6) < 1 - t[y, x] * 1.6:
            tussock(p, x, y, seed + x)
    plant(p, m, 900, [sage, sage, rabbitbrush, tussock_sprite], seed + 7,
          density=np.clip(1 - np.abs(t - 0.45) * 3.0, 0, 1))
    plant(p, m, 1800, [prickly_pear, barrel, prickly_pear, lambda s: saguaro(s, 1)], seed + 8,
          density=np.clip(t * 1.4 - 0.5, 0, 0.6))
    despeckle(p, m & ~p.solid)


def scrub_to_ash(p: Plot, m, t, seed=0):
    """Scrub into the ash fields over a band (`t` 0 to 1): grey dust settling on the bushes'
    tops and between them, then drifts and tongues of ash with the hardpan showing through,
    fireweed coming in on the ash, the scrub thinning to charred snags, then deep ash with
    cinder lapilli."""
    m = np.asarray(m, bool)
    t = np.broadcast_to(np.asarray(t, float), p.f.shape)
    hardpan_ground(p, m, seed)
    scrub_plants(p, m, seed + 1, 700, density=np.clip(1.1 - t * 1.3, 0, 1))
    ash(p, m, t, seed + 2)
    plant(p, m & ~p.solid, 1100, [fireweed], seed + 3, density=np.clip(1 - np.abs(t - 0.6) * 3.5, 0, 0.8))
    plant(p, m & ~p.solid, 2600, [lambda s: snag(s, 'charred')], seed + 4, density=np.clip(t * 1.5 - 0.6, 0, 1))
    despeckle(p, m & ~p.solid)


# --- the kit sheet, the bar and the comparisons --------------------------------------------------
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
RAMP_TONES = 0.85     # house-style ruling (cea6bae): ramp-built art passes tones at 85 %


def _ground(w, h, fn, seed=0, **kw):
    p = Plot(w, h)
    fn(p, p.mask(), seed, **kw)
    return p


def _on(fn, ground=None, w=None, h=None, seed=0, pad=10):
    """A standing thing on its own ground tile, its foot near the bottom middle."""
    made = fn()
    sp, sh = made[0], made[1]
    w = w or max(64, sp.w + 2 * pad)
    h = h or sp.h + pad + 6
    p = Plot(w, h)
    (ground or hardpan_ground)(p, p.mask(), seed)
    paste(p, sp, w // 2, h - 6, shadow=sh, block=made[2] if len(made) > 2 else None)
    ys, xs = np.nonzero(sp.m)
    return p, sp, (w // 2 - sp.fx, h - 6 - sp.fy)


def _box_on(sp, off, frac=(0.15, 0.1, 0.85, 0.7), size=36):
    """A measuring box of `size` inside a sprite's body (None if it is too small)."""
    ys, xs = np.nonzero(sp.m)
    if len(xs) == 0 or xs.max() - xs.min() < size or ys.max() - ys.min() < size:
        return None
    cx = int(np.median(xs)) + off[0]
    cy = int(np.percentile(ys, 40)) + off[1]
    return (cx - size // 2, cy - size // 2, cx + size // 2 + 2, cy + size // 2 + 2)


def _tier_tile(rows, F=FACE_MESA, seed=0, top=None, ground=None, stair_at=None, rim=True):
    T = from_cells(rows, seed=seed)
    L = Layout(T, F)
    p = Plot(T.shape[1], T.shape[0])
    (ground or scrub)(p, L.top(0), seed + 1)
    for k in range(1, int(T.max()) + 1):
        (top or hardpan_ground)(p, L.top(k), seed + 2 + k)
    if rim:
        rimrock(p, L, seed + 6)
    draw_faces(p, L, seed=seed + 3)
    draw_bands(p, L, seed + 4)
    tier_shadows(p, L)
    talus(p, L, seed + 5)
    if stair_at is not None:
        stair(p, L, stair_at, 40, seed + 7, k=int(T.max()))
    return p, L


MESA = """
00000000000000000000000
00000333333333000000000
00003333333333330000000
00003333333333330000000
00003333333333330000000
00002222222222222000000
00002222222222222000000
00001111111111111000000
00001111111111111000000
00000000000000000000000
00000000000000000000000
00000000000000000000000
00000000000000000000000
00000000000000000000000
00000000000000000000000
"""

BUTTE = """
000000000000
000002220000
000022222000
000022222000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
000000000000
"""

CANYON = """
2222222222222222222222222
2222222222222222222222222
2222222222222222222222222
2222222222222222222222222
2222222222222222222222222
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
0000000000000000000000000
2222222222222222222222222
2222222222222222222222222
"""


def pieces():
    """Every piece on its own tile: (group, name, plot, bar box or None, bar kind)."""
    out = []
    # dry grounds
    for name, fn, kw in (('steppe', steppe, {}), ('sage scrub', scrub, {'every': 700}),
                         ('hardpan, cracked clay', hardpan, {}), ('gravel desert pavement', gravel, {}),
                         ('dunes: crests, lee shade', dunes, {}), ('salt pan: crust polygons', salt_pan, {}),
                         ('ash field (deep)', ash_ground, {})):
        p = _ground(128, 112, fn, 3, **kw)
        out.append(('ground', name, p, (10, 10, 118, 102), 'ground'))
    # standing things
    for name, fn, kind, gr in (('date palm', lambda: palm(0, 1), 'tree', None), ('young palm', lambda: palm(1, 2), 'tree', None),
                               ('saguaro', lambda: saguaro(3), None, None), ('barrel cactus', barrel, None, None),
                               ('prickly pear', prickly_pear, None, None), ('sagebrush', sage, 'hedge', None),
                               ('creosote', creosote, None, None), ('rabbitbrush', rabbitbrush, None, None),
                               ('bunchgrass', tussock_sprite, None, steppe),
                               ('sandstone boulder', lambda: boulder(1, 'adobe', 30), None, None),
                               ('basalt boulder', lambda: boulder(2, 'basalt', 26), None, ash_ground),
                               ('charred snag', lambda: snag(4, 'charred'), None, ash_ground),
                               ('bleached snag', lambda: snag(5, 'bleached'), None, None),
                               ('fireweed', fireweed, None, ash_ground), ('driftwood log', log, None, None),
                               ('reeds', reeds, None, lush)):
        p, sp, off = _on(fn, gr)
        box = _box_on(sp, off, size=34) if kind else None
        if kind == 'tree' and box:
            ys, xs = np.nonzero(sp.m)
            cy = int(np.percentile(ys, 12)) + off[1]
            cx = int(np.median(xs)) + off[0]
            box = (cx - 18, cy - 10, cx + 18, cy + 26)
        out.append(('plants', name, p, box, kind or 'by eye'))
    # height: mesa, butte, canyon, badlands, talus, stair
    p, L = _tier_tile(MESA, seed=11, top=caprock, stair_at=None)
    fbox = _face_box(L, 34)
    out.append(('height', 'stepped mesa: 3 tiers of 40, strata, side bands', p, fbox, 'face'))
    ys, xs = np.nonzero(L.face & (p.x > 60) & (p.x < 110))
    fy = int(ys.max())
    out.append(('height', '(talus at the mesa foot, measured)', p, (66, fy - 18, 102, fy + 18), 'foot'))
    p, L = _tier_tile(BUTTE, seed=12, top=caprock)
    out.append(('height', 'butte (2 tiers)', p, _face_box(L, 34), 'face'))
    p, L = _tier_tile(CANYON, seed=13, top=lambda q, m, s: scrub(q, m, s, every=900),
                      ground=lambda q, m, s: hardpan_ground(q, m, s), stair_at=72)
    wash(p, [(-10, 120), (90, 112), (210, 124)], 40, 14, logs=1)
    out.append(('height', 'canyon: wall with stair, floor with wash, talus', p, _face_box(L, 34, avoid=(72, 120)), 'face'))
    st = (p.x >= 76) & (p.x < 116) & L.face
    ys, xs = np.nonzero(st)
    out.append(('height', '(the stair, measured)', p, (int(xs.min()), int(ys.min()) + 2, int(xs.min()) + 36,
                                                       int(ys.min()) + 38), 'stair'))
    p = Plot(176, 112)
    badlands(p, p.mask(), 15, every=1500)
    out.append(('height', 'badlands: banded mounds, rills, aprons', p, _solid_box(p, 34), 'face'))
    # water in the desert
    p = Plot(176, 112)
    scrub(p, p.mask(), 16, every=1200)
    wash(p, [(-10, 44), (70, 60), (186, 50)], 46, 17)
    out.append(('water', 'dry wash: braided gravel, cut bank', p, (20, 38, 160, 80), 'ground'))
    p = Plot(224, 144)
    scrub(p, p.mask(), 18, every=1100)
    oasis(p, p.mask(), (74, 62, 46, 27), [(116, 78), (160, 94), (236, 120)], 19, reach=52, palms=4)
    out.append(('water', 'oasis edge: pool, reeds, palms, channel, green fading', p, (48, 30, 88, 66), 'water'))
    p = Plot(176, 64)
    base(p, p.mask(), [('path_warm', 0.4), ('sand_cool', 0.3), ('path', 0.3)], 20, 14)   # a tilled field edge
    stamp(p, p.mask(), 0.05, 21, FLAT, swap='mix')
    ditch(p, [(-10, 30), (90, 34), (186, 28)], 21)
    out.append(('water', 'irrigation channel (acequia)', p, (20, 14, 160, 48), 'stream'))
    # the fire country
    p = Plot(176, 112)
    hardpan_ground(p, p.mask(), 22)
    of = blob(88, 52, 80, 40, p.f.shape, 23, wob=0.15)
    old_flow(p, of, 24)
    out.append(('fire', 'old crusted flow: ropes, lichen, scrub at its edge', p, (40, 26, 130, 74), 'ground'))
    p = Plot(176, 120)
    ash_ground(p, p.mask(), 25)
    yf = blob(88, 58, 84, 50, p.f.shape, 26, wob=0.1)
    young_flow(p, yf, 27, channel=[(80, -10), (92, 60), (86, 130)])
    out.append(('fire', 'young flow: crust plates, glowing cracks, open channel', p, (14, 24, 74, 92), 'ground'))
    p = Plot(176, 96)
    ash_ground(p, p.mask(), 28)
    yf = (p.y > 20) & (p.y < 76)
    young_flow(p, yf, 29)
    causeway(p, [(60, -10), (84, 48), (100, 110)], 24, 30)
    out.append(('fire', 'basalt causeway over a young flow', p, None, 'by eye'))
    p, sp, off = _on(lambda: columns(31), ash_ground, w=96)
    out.append(('fire', 'basalt columns', p, None, 'by eye'))
    p, sp, off = _on(lambda: cinder_cone(32), ash_ground, w=128)
    out.append(('fire', 'cinder cone', p, None, 'by eye'))
    p = Plot(128, 96)
    ash_ground(p, p.mask(), 33)
    fumarole(p, 40, 52, 34, 11)
    fumarole(p, 92, 34, 35, 8)
    fumarole(p, 88, 78, 36, 7)
    out.append(('fire', 'fumaroles (steam moves: steam_frames)', p, None, 'by eye'))
    p = Plot(144, 120)
    hardpan_ground(p, p.mask(), 37, ramp='sand')
    hot_spring(p, 70, 28, 38, n=4, w=80)
    out.append(('fire', 'hot spring: travertine terraces', p, (40, 38, 104, 80), 'water'))
    p = Plot(176, 120)
    dead_forest(p, p.mask(), 39)
    out.append(('fire', 'dead forest', p, None, 'by eye'))
    # transitions
    p = Plot(352, 112)
    steppe_to_desert(p, p.mask(), np.clip((p.x - 50) / 250.0, 0, 1), 40)
    out.append(('band', 'steppe into desert (a band, no line)', p, (130, 8, 230, 104), 'ground'))
    p = Plot(352, 112)
    scrub_to_ash(p, p.mask(), np.clip((p.x - 50) / 250.0, 0, 1), 41)
    out.append(('band', 'scrub into the ash fields (a band, no line)', p, (130, 8, 230, 104), 'ground'))
    return out


def _face_box(L, size=34, avoid=None):
    """A box inside the tallest stretch of face, clear of a stair at `avoid` (x0, x1)."""
    fc = L.face.copy()
    if avoid:
        fc[:, avoid[0]:avoid[1]] = False
    best = None
    h, w = fc.shape
    ii = np.cumsum(np.cumsum(fc.astype(np.int32), 0), 1)

    def area(x0, y0, x1, y1):
        a = ii[y1 - 1, x1 - 1]
        if x0 > 0:
            a -= ii[y1 - 1, x0 - 1]
        if y0 > 0:
            a -= ii[y0 - 1, x1 - 1]
        if x0 > 0 and y0 > 0:
            a += ii[y0 - 1, x0 - 1]
        return a
    for y0 in range(0, h - size, 2):
        for x0 in range(0, w - size, 2):
            if area(x0, y0, x0 + size, y0 + size) == size * size:
                return (x0, y0, x0 + size, y0 + size)
            a = area(x0, y0, x0 + size, y0 + size)
            if best is None or a > best[0]:
                best = (a, (x0, y0, x0 + size, y0 + size))
    return best[1] if best else None


def _solid_box(p, size=34):
    class _L:
        pass
    q = _L()
    q.face = p.solid & ~p.walk
    return _face_box(q, size)


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


REF_FOR = {'stream': 'eastward-13-canal', 'ground': 'eastward-08-verge-patches', 'hedge': 'eastward-17-bushes',
           'tree': 'eastward-13-pine', 'water': 'eastward-17-pond', 'face': 'eastward-12-cliff-face',
           'stair': 'eastward-13-stair', 'foot': 'eastward-13-foot', 'side': 'eastward-12-cliff-side'}


def _label(img, text, xy, fill=(240, 236, 228)):
    d = ImageDraw.Draw(img)
    x, y = xy
    d.text((x + 1, y + 1), text, fill=(20, 16, 20))
    d.text((x, y), text, fill=fill)


def judge(c, kind):
    """(strict pass, pass under the ramp ruling): the ruling passes tones at 85 % for art
    drawn only in house ramps; shapes, dressing and both cleanliness tests stay in full."""
    import detail_bar as db
    ref = db.bar(kind)
    rest = (c['shapes'] >= db.TOLERANCE * ref['shapes'] and c['dressing'] >= db.TOLERANCE * ref['dressing']
            and c['isolated'] <= ref['isolated'] + db.ISOLATED_MARGIN and c['cluster'] >= db.CLUSTER_SHARE * ref['cluster'])
    return rest and c['tones'] >= db.TOLERANCE * ref['tones'], rest and c['tones'] >= RAMP_TONES * ref['tones']


def bar_rows(items):
    import detail_bar as db
    rows = []
    for (group, name, p, box, kind) in items:
        if box is None or kind == 'by eye':
            rows.append((name, kind, None, None, None, lone_share(p)))
            continue
        ok, c, lines = db.check_image(p.image(), box, kind)
        strict, ramp = judge(c, kind)
        rows.append((name, kind, strict, ramp, c, lone_share(p)))
    return rows


def kit_sheet(items, rows, scale=2):
    """Every piece at `scale`, grouped, each labelled with its detail bar result."""
    import detail_bar as db
    pad, lab = 10, 30
    groups = ['ground', 'plants', 'height', 'water', 'fire', 'band']
    titles = {'ground': 'Dry grounds: steppe, scrub, hardpan, gravel, dunes, salt, ash',
              'plants': 'Standing things: palms, cacti, scrub, rocks, snags (by eye unless boxed)',
              'height': 'Height on the soft grid: mesa, butte, canyon, stair, talus, badlands',
              'water': 'Water in the desert: dry wash, oasis, irrigation channel',
              'fire': 'The fire country: flows, causeway, columns, cone, fumaroles, hot spring, dead forest',
              'band': 'Transitions: bands, not lines'}
    maxw = 1500
    layout, y = [], 0
    for g in groups:
        y += 30
        x, rowh = pad, 0
        for it, r in zip(items, rows):
            if it[0] != g or it[1].startswith('('):
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
    extra = {it[1]: (it, r) for it, r in zip(items, rows) if it[1].startswith('(')}
    for (g, it, r, x, y0) in layout:
        if g not in seen:
            _label(sheet, titles[g], (pad, y0 - 22), (250, 214, 140))
            seen.add(g)
        img = it[2].image(scale)
        sheet.paste(img, (x, y0))
        boxes = [(it[3], r)]
        if it[1].startswith('canyon'):
            boxes += [(extra[k][0][3], extra[k][1]) for k in extra if 'stair' in k]
        if it[1].startswith('stepped mesa'):
            boxes += [(extra[k][0][3], extra[k][1]) for k in extra if 'talus' in k]
        subs = []
        for box, rr in boxes:
            if box:
                d.rectangle([x + box[0] * scale, y0 + box[1] * scale, x + box[2] * scale - 1, y0 + box[3] * scale - 1],
                            outline=(250, 214, 140))
            name, kind, strict, ramp, c, lone = rr
            if c:
                ref = db.bar(kind)
                subs.append(f'{kind} t{c["tones"]:.0f}/{ref["tones"]:.0f} s{c["shapes"]:.0f}/{ref["shapes"]:.0f} '
                            f'd{c["dressing"]:.0f}/{ref["dressing"]:.0f} '
                            f'{"PASS" if strict else "PASS@85" if ramp else "FAIL"}')
        _label(sheet, it[1][:int(img.width / 6)], (x, y0 + img.height + 2))
        _label(sheet, ('  '.join(subs) if subs else 'judged by eye')[:int(img.width / 6)], (x, y0 + img.height + 15),
               (200, 200, 210))
    return sheet


def compare_sheet(items, rows, scale=4):
    """Each measured piece beside an official Eastward crop of the same kind of surface at
    the same character height (an adult 25 px), both at `scale`."""
    import detail_bar as db
    tiles = []
    for it, r in zip(items, rows):
        if it[3] is None or r[4] is None or it[4] not in REF_FOR:
            continue
        x0, y0, x1, y1 = it[3]
        rb = db.load()['baselines'][REF_FOR[it[4]]]
        rw = int((rb['box'][2] - rb['box'][0]) * 25 / rb['adult_px'])
        rh = int((rb['box'][3] - rb['box'][1]) * 25 / rb['adult_px'])
        w, h = min(48, x1 - x0, rw), min(48, y1 - y0, rh)
        ours = it[2].image().crop((x0, y0, x0 + w, y0 + h))
        ref = eastward_crop(REF_FOR[it[4]], (w, h))
        tiles.append((it[1], it[4], ours, ref, r))
    if not tiles:
        return None
    tw = max(o.width + (rf.width if rf is not None else 0) for (_n, _k, o, rf, _r) in tiles) * scale + 24
    th = max(max(o.height, rf.height if rf is not None else 0) for (_n, _k, o, rf, _r) in tiles) * scale + 36
    cols = 3
    rows_n = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw + 10, rows_n * th + 10), (46, 40, 52))
    for i, (name, kind, ours, ref, r) in enumerate(tiles):
        x, y = 10 + (i % cols) * tw, 10 + (i // cols) * th
        sheet.paste(ours.resize((ours.width * scale, ours.height * scale), Image.NEAREST), (x, y))
        hh = ours.height
        if ref is not None:
            sheet.paste(ref.resize((ref.width * scale, ref.height * scale), Image.NEAREST),
                        (x + ours.width * scale + 6, y))
            hh = max(hh, ref.height)
        c, b = r[4], db.bar(kind)
        _label(sheet, f'{name[:34]} | Eastward {REF_FOR[kind][9:]}', (x, y + hh * scale + 2))
        _label(sheet, f'tones {c["tones"]:.1f}/{b["tones"]:.1f}  shapes {c["shapes"]:.1f}/{b["shapes"]:.1f}  '
               f'dressing {c["dressing"]:.1f}/{b["dressing"]:.1f}', (x, y + hh * scale + 15), (200, 200, 210))
    return sheet


def sample_preview(p, scale=2, people=True):
    """The sample at `scale` with residents standing in it for scale (preview only)."""
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in (('hiker', (300, 196)), ('angler', (420, 498)), ('gardener', (286, 330))):
            path = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')
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
    """The kit's contracts: faces, water and young lava block a walker; a stair and a
    causeway open a way; nothing green grows within 64 px of lava; the sample's trail runs
    from the plateau down the stair to the oasis without touching water."""
    faults = []
    p, L = _tier_tile(CANYON, seed=13, top=lambda q, m, s: hardpan_ground(q, m, s),
                      ground=lambda q, m, s: hardpan_ground(q, m, s))
    if _reaches(p.walk, (20, 8), (20, 100)):
        faults.append('a canyon wall without a stair can be walked down')
    p2, L2 = _tier_tile(CANYON, seed=13, top=lambda q, m, s: hardpan_ground(q, m, s),
                        ground=lambda q, m, s: hardpan_ground(q, m, s), stair_at=72)
    if not _reaches(p2.walk, (96, 8), (96, 100)):
        faults.append('the stair through the canyon wall cannot be walked')
    if (p2.walk & L2.face & ~((p2.x >= 76) & (p2.x < 116))).any():
        faults.append('face pixels outside the stair are walkable')
    q = Plot(128, 96)
    ash_ground(q, q.mask(), 1)
    yf = (q.y > 20) & (q.y < 76)
    young_flow(q, yf, 2)
    if _reaches(q.walk, (64, 8), (64, 90)):
        faults.append('a young flow can be walked across without a causeway')
    causeway(q, [(60, -10), (64, 48), (66, 110)], 24, 3)
    if not _reaches(q.walk, (64, 8), (64, 90)):
        faults.append('the causeway does not cross the young flow')
    s, parts = sample()
    a, b = (300, 6), (500, 570)
    if not _reaches(s.walk, a, b):
        faults.append('the sample trail cannot be walked from the plateau to the oasis')
    if (s.walk & s.wet).any():
        faults.append(f'{int((s.walk & s.wet).sum())} wet pixels in the sample are walkable')
    for name, plot in (('young flow tile', q),):
        green = np.isin(FAMILY[plot.f], [IDX['grass'], IDX['leaf'], IDX['cactus']])
        near = dist_to(plot.lava, 64) < 64
        if (green & near & ~plot.lava).any():
            faults.append(f'{name}: green within 64 px of lava')
    return faults


def main(argv):
    if '--check' in argv:
        faults = check()
        for f in faults:
            print('FAULT:', f)
        print('dry_kit check:', 'pass' if not faults else f'{len(faults)} faults')
        return 1 if faults else 0
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-dry-kit')
    os.makedirs(out, exist_ok=True)
    items = pieces()
    rows = bar_rows(items)
    kit_sheet(items, rows).save(os.path.join(out, 'kit-sheet.png'))
    cmp = compare_sheet(items, rows)
    if cmp is not None:
        cmp.save(os.path.join(out, 'compare-eastward.png'))
    print(f'{"piece":56s} {"kind":7s} tones  shapes dressing isolated cluster  lone   result')
    for (name, kind, strict, ramp, c, lone) in rows:
        if c is None:
            print(f'{name:56s} {kind:7s} (judged by eye)                              {lone:.3f}')
            continue
        res = 'PASS' if strict else 'PASS@85' if ramp else 'FAIL'
        print(f'{name[:56]:56s} {kind:7s} {c["tones"]:5.1f} {c["shapes"]:6.1f} {c["dressing"]:7.1f} '
              f'{c["isolated"]:8.3f} {c["cluster"]:7.1f}  {lone:.3f}  {res}')
    p, parts = sample()
    p.image().save(os.path.join(out, 'sample.png'))
    sample_preview(p, 2).save(os.path.join(out, 'sample-2x.png'))
    night = Image.fromarray((np.asarray(p.image()).astype(np.float32) * np.array([0.42, 0.45, 0.68])).astype(np.uint8))
    night.resize((p.w * 2, p.h * 2), Image.NEAREST).save(os.path.join(out, 'sample-night-preview.png'))
    import detail_bar as db
    print('sample boxes:')
    for name, box, kind in (('canyon wall', (40, 236, 120, 290), 'face'), ('plateau scrub', (420, 20, 520, 120), 'ground'),
                            ('canyon floor and wash', (20, 320, 120, 380), 'ground'),
                            ('oasis pool', (424, 438, 482, 470), 'water'),
                            ('mesa face', (90, 140, 150, 176), 'face')):
        ok, c, lines = db.check_image(p.image(), box, kind)
        strict, ramp = judge(c, kind)
        print(f'  {name:24s} {kind:7s} ' + '; '.join(lines) + f'  {"PASS" if strict else "PASS@85" if ramp else "FAIL"}')
    # motion: the fire tile's lava and the fumaroles' steam
    lt = [it for it in items if it[1].startswith('young flow')][0][2]
    frames, box = lava_frames(lt)
    big = [f.resize((f.width * 2, f.height * 2), Image.NEAREST) for f in frames]
    big[0].save(os.path.join(out, 'lava-flow.gif'), save_all=True, append_images=big[1:], duration=150, loop=0)
    ft = [it for it in items if it[1].startswith('fumaroles')][0][2]
    st = steam_frames(ft)
    big = [f.resize((f.width * 2, f.height * 2), Image.NEAREST) for f in st]
    big[0].save(os.path.join(out, 'steam.gif'), save_all=True, append_images=big[1:], duration=150, loop=0)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
