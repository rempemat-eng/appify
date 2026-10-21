"""The moor kit: the Brackens' own ground, edges and standing things (Claude F, lane F).

The Brackens are a low heather ridge west of the home valley (brief: regions/home-valley-
frostline-brackens.md; plan: art/regions/brackens.json). Matt, 21 Oct 10:08: "the edge of the
grass biome should look different from an edge in the mountain ... but do make sure everything
has the same sort of soft grid and the visual art style is consistent". So the moor draws its
own edges (peat banks and gritstone, not the meadow's turf banks or the highland's boulder
cliffs) on the shared grammar: the 8 px soft grid, 32 px tiers, eastward-edges.md's lip, rim
line, under-lip shade, body, dark foot and side bands, light from the upper left, the house
palette's ramps (art/house-palette.json), clusters of two to four pixels and no speckle.

It builds on the river and meadow kit (river_kit.py: `Plot`, ramps, noise, `stamp`, `base`,
`heath`, `track`, `paste`, `crown`, `shrub`, `birch`), so the moor's ground meets the valley's
meadow with the same vocabulary, and adds:

- ground: `moor()` heather in drifts over peat, bilberry, bracken, short sheep-bitten turf,
  grey grit in the turf where it is thin; `flush()` a wet flush of rushes and cotton grass;
  `turf()` the gap's short yellowing turf.
- edges (eastward-edges 2, 3): `peat_face()` a 32 px south face of peat between tiers (a clean
  1 px darker turf lip, rim line, under-lip shade, peat in cut turves marked across, heather
  roots, a dark foot with grit and weeds over it); `grit_face()` the bluffs' gritstone (under-
  lip shade, a streak zone, rounded masses with horizontal bedding, lit top left);
  `side_bands()` where a tier ends west or east (eastward 3.3: a 3 px band, lit facing west,
  dark facing east, a broken ink line; 8 px of the edge kept off the walk, on the 8 px lines);
  `stair()` stone steps through a face, top flush with the upper floor, bottom on the path.
- paths: `trod()` a sheep trod with a frayed edge (eastward 5.1: no outline, no dither);
  the Drover's Road is river_kit's `track()` at road width.
- standing things: `gritstone()` boulders and tors, `scots_pine()`, gorse and birch from
  river_kit, and story props drawn into the ground: `fire_ring()`, `hoofprints()`,
  `cart_wreck()`, `boot()`, `hat()`, `bell()`.

Run: python3 scripts/art/moor_kit.py [OUT_DIR]  (the kit sheet and a sample at 1x and 3x with
the detail bar and the lint, to napattack-moor-kit in the system's temp folder)
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import river_kit as rk  # noqa: E402
from river_kit import (BLADES, DOMINOES, EDGE_T, IDX, SMALL, Plot, Sprite, base, crown, despeckle,  # noqa: E402
                       dilate, erode, fbm, hash01, paste, shift, stamp, texture, tree_shadow, trunk, vnoise)

FACE = 32
FACE_FAMILY = 'earth'      # peat: the earth ramp's dark, cool end


# --- ground -----------------------------------------------------------------------------------
def moor(p: Plot, m, seed=60, heather=0.62, bracken=0.18, grit=0.06):
    """Heather moor, calm enough to walk on (house rule 8): ling in broad drifts, purple-brown
    (berry_cool and dusk_warm), its low mounds lit on their top left and shaded at their foot
    two tones apart at most, flowering in small clusters on the crowns; short turf on the
    sheep's ways between the drifts; bracken in drifts on the deeper ground; bilberry's
    green inside the heather; grey grit where the peat is thin. Returns the heather mask."""
    m = np.asarray(m, bool)
    turf(p, m, seed + 40, yellow=0.25)
    z = fbm(p.x, p.y, 46, seed) + 0.18 * (fbm(p.x, p.y, 11, seed + 1) - 0.5)
    hm = m & (z > 1 - heather - 0.12)
    br = m & ~hm & (fbm(p.x, p.y, 34, seed + 2) < bracken + 0.12)
    # heather: small tufts of ling packed close, each lit along its top left; half the tufts
    # brown, half mauve (more mauve where the drift is in flower), so up close it is plants
    # and from afar one purple-brown; the gaps between tufts in deep shade
    base(p, hm, 'earth', seed + 3, scale=9, tone=1, light=2.0, dark=-1.0, warm=0.0, cool=0.0)
    inside, du, dv, cid = rk.clumps(p, hm, 4, 1.9, 2.8, seed + 5)
    tuft_m = hm & inside
    share = 0.3 + 0.4 * fbm(p.x, p.y, 34, seed + 4)
    pick = hash01(cid, 7, seed + 4)
    mauve = tuft_m & (pick < share)
    brown = tuft_m & ~mauve
    p.f[mauve] = IDX['dusk_warm']
    p.f[brown] = np.where(pick > 0.85, IDX['earth'], IDX['earth_warm'])[brown]
    lv = -du - dv
    p.t[tuft_m] = np.where(lv > 0.7, 3, 2)[tuft_m]
    tip = mauve & (lv > 1.05) & (hash01(cid, 8, seed + 6) < 0.6)
    p.f[tip], p.t[tip] = IDX['berry_cool'], 4
    # many small parts, no more contrast: sibling swaps across the tufts, a few a tone up
    texture(p, hm, seed + 19, swaps=0.14, ups=0.03, downs=0.02)
    # bilberry: some tufts bright green among the heather where the drift is shadier
    bil = tuft_m & (hash01(cid, 9, seed + 7) < 0.25 * fbm(p.x, p.y, 40, seed + 8))
    p.f[bil] = IDX['leaf']
    # bracken
    p.f[br] = np.where(hash01(p.x // 4, p.y // 3, seed + 10) < 0.5, IDX['grass_warm'], IDX['leaf_warm'])[br]
    p.t[br] = 3
    stamp(p, br, 0.10, seed + 11, (((0, 0), (1, -1), (2, -1)), ((0, 0), (-1, -1), (-2, -1)), ((0, 0), (0, -1), (1, -2))), dt=1)
    stamp(p, br, 0.05, seed + 12, (((0, 0), (1, 0)), ((0, 0), (0, 1))), dt=-1)
    stamp(p, br & (fbm(p.x, p.y, 21, seed + 13) > 0.6), 0.04, seed + 14, DOMINOES, ramp='clay', tone=3,
          same_family=False)
    # grit
    gm = m & ~hm & ~br & (fbm(p.x, p.y, 9, seed + 15) > 1 - grit)
    base(p, gm, 'stone', seed + 16, scale=4, tone=3)
    rk.pebbles(p, gm, seed + 17, 0.03)
    despeckle(p, m)
    return hm


def turf(p: Plot, m, seed=70, yellow=0.5):
    """Short sheep-bitten turf yellowing towards the steppe (the gap): grass and sand
    siblings in broad patches, tormentil and eyebright in drifts, the odd molehill."""
    m = np.asarray(m, bool)
    base(p, m, 'grass', seed, scale=7, warm=0.3 + 0.4 * yellow, cool=0.95)
    dry = m & (fbm(p.x, p.y, 14, seed + 1) < yellow * 0.6)
    p.f[dry] = np.where(hash01(p.x // 3, p.y // 2, seed + 2) < 0.6, IDX['sand_warm'], IDX['grass_warm'])[dry]
    texture(p, m, seed + 3, swaps=0.10, ups=0.03, downs=0.03)
    stamp(p, m, 0.015, seed + 4, BLADES, dt=1)
    # clover and moss in small clusters, a few bare earth scrapes where the sheep lie
    stamp(p, m, 0.012, seed + 6, SMALL, ramp='leaf', tone=3, same_family=False)
    stamp(p, m & (fbm(p.x, p.y, 19, seed + 7) > 0.66), 0.02, seed + 8, SMALL, ramp='earth_warm', tone=3,
          same_family=False)
    rk.flowers(p, m, seed + 5, (('brass', 4, 0.6), ('dusk', 3, 0.4)), 0.004)
    despeckle(p, m)


def flush(p: Plot, m, seed=80):
    """A wet flush: dark rushes in tussocks, cotton grass's white tufts, sphagnum's warm
    red-green, a glint of standing water."""
    m = np.asarray(m, bool)
    base(p, m, 'leaf', seed, scale=5, warm=0.4, cool=0.6)
    sph = m & (fbm(p.x, p.y, 6, seed + 1) > 0.62)
    p.f[sph] = IDX['clay_cool']
    p.t[sph] = 3
    stamp(p, m, 0.10, seed + 2, BLADES, ramp='leaf_cool', tone=2, same_family=False)
    stamp(p, m, 0.05, seed + 3, BLADES, ramp='leaf_cool', tone=4, same_family=False)
    stamp(p, m & ~sph, 0.025, seed + 4, (((0, 0), (1, 0), (0, -1)), ((0, 0), (0, -1))), ramp='plaster', tone=5,
          same_family=False)
    pool = m & (fbm(p.x, p.y, 5, seed + 5) > 0.8)
    p.f[pool], p.t[pool] = IDX['sky_cool'], 3
    rim = pool & ~shift(pool, 0, 1, False)
    p.f[rim], p.t[rim] = IDX['earth_cool'], 1
    despeckle(p, m)


# --- edges --------------------------------------------------------------------------------------
def face_depth(tier: np.ndarray, face_h: int = FACE):
    """For a screen tier map (one value a pixel), where the south faces hang: returns
    (face mask, depth below the rim, the face's height, the upper tier) for every pixel.
    A face hangs face_h px a tier under a rim (64 px when two tiers drop at once)."""
    h, w = tier.shape
    face = np.zeros((h, w), bool)
    depth = np.zeros((h, w), np.int16)
    height = np.zeros((h, w), np.int16)
    upper = tier.copy()
    top = int(tier.max() - tier.min())
    for d in range(1, top * face_h + 1):
        up = np.vstack([tier[:1].repeat(d, 0), tier[:-d]])
        drop = up - tier
        hit = (drop * face_h >= d) & ~face
        # the rim is the nearest row above where the tier changes: d counts from it
        rim_here = hit & (np.vstack([tier[:1].repeat(d - 1, 0), tier[:-(d - 1)]]) if d > 1 else tier) == tier
        rim_here = hit
        face |= hit
        depth[hit] = d - 1
        height[hit] = (drop * face_h)[hit]
        upper[hit] = up[hit]
    return face, depth, height, upper


def lumps(x, j, sx, sy, seed):
    """Rounded lumps over a face, laid on a jittered grid in (x, depth) with cells sx by sy,
    so they never line up in courses: for every pixel the lump's id, its offset from the
    lump's centre in units of its half-size (du, dv) and whether it lies in a crevice
    between two lumps."""
    x, j = np.asarray(x, np.int64), np.asarray(j, np.int64)
    gx, gy = np.floor_divide(x, sx), np.floor_divide(j, sy)
    d1 = np.full(np.shape(x), 9e9)
    d2 = np.full(np.shape(x), 9e9)
    du = np.zeros(np.shape(x))
    dv = np.zeros(np.shape(x))
    lid = np.zeros(np.shape(x), np.int64)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx, cy = gx + ox, gy + oy
            # rows shift by half a cell so lumps stagger like a bank's clods
            px = (cx + 0.5 * (cy % 2) + 0.15 + 0.7 * hash01(cx, cy, seed)) * sx
            py = (cy + 0.2 + 0.6 * hash01(cx, cy, seed + 1)) * sy
            rx = sx * (0.55 + 0.25 * hash01(cx, cy, seed + 2))
            ry = sy * (0.55 + 0.2 * hash01(cx, cy, seed + 3))
            u, v = (x + 0.5 - px) / rx, (j + 0.5 - py) / ry
            d = u * u + v * v
            better = d < d1
            d2 = np.where(better, d1, np.minimum(d2, d))
            d1 = np.where(better, d, d1)
            du = np.where(better, u, du)
            dv = np.where(better, v, dv)
            lid = np.where(better, cx * 7919 + cy * 104729, lid)
    crev = (np.sqrt(d2) - np.sqrt(d1)) < 0.16
    return lid, du, dv, crev


def lip(p: Plot, rim_row_mask, seed=90):
    """Eastward 3.1: the top ground ends in one row a step darker (no teeth), with a lit row
    two rows behind it here and there."""
    p.step(rim_row_mask, -1, lo=1)
    behind = shift(rim_row_mask, 0, -2, False) & (hash01(p.x // 3, p.y, seed) < 0.45)
    p.step(behind & (p.t < 4), 1)


def peat_face(p: Plot, face, depth, height, seed=100, east=None):
    """A south face of peat between two tiers (eastward 2.2 scaled to a 32 px tier, values
    2.5): the rim line (edge tone), the under-lip line (tone 0), two rows of shade (1, 2),
    the body of cut turves marked across (wider than tall, each lit along its top, dark along
    its bottom, siblings swapped), heather roots hanging from under the lip, grit and small
    stones, and a dark foot (tone 1) 3 px deep with pebbles. `east`: pixels facing east
    (a tone darker)."""
    if not face.any():
        return
    j = depth
    H = height
    fam_base = FACE_FAMILY
    rimline = face & (j == 0)
    under = face & (j == 1)
    shade = face & (j >= 2) & (j <= 3)
    foot = face & (j >= H - 3)
    body = face & (j >= 4) & ~foot
    p.f[rimline], p.t[rimline] = IDX[fam_base], EDGE_T
    p.f[under], p.t[under] = IDX[fam_base + '_cool'], 0
    p.f[shade], p.t[shade] = IDX[fam_base + '_cool'], np.where(j == 2, 1, 2)[shade]
    # clods: rounded lumps of peat wider than tall (eastward 2.4: marks across, never in
    # stripes), each lit on its top left and dark along its underside, dark creases between
    lid, du, dv, crev = lumps(p.x, j, 9, 5, seed)
    pick = hash01(lid, 1, seed + 1)
    fam = np.where(pick < 0.3, IDX[fam_base + '_warm'], np.where(pick > 0.72, IDX[fam_base + '_cool'], IDX[fam_base]))
    lv = -0.45 * du - 0.9 * dv
    k = np.where(lv > 0.75, 3, 2)
    k = np.where((lv > 1.05) & (hash01(lid, 2, seed + 2) < 0.5), 4, k)
    k = np.where(crev & (dv > 0), 1, k)
    fam = np.where(pick > 0.9, IDX['clay_cool'], fam)                       # red-brown sphagnum peat
    p.f[body], p.t[body] = fam[body], k[body]
    texture(p, body, seed + 9, swaps=0.16, ups=0.03, downs=0.03)
    # moss and bilberry on the lumps' lit tops, in small caps
    moss = body & (lv > 0.8) & (hash01(lid, 6, seed + 10) < 0.22) & ~crev
    p.f[moss] = np.where(hash01(lid, 7, seed + 11) < 0.5, IDX['leaf_cool'], IDX['leaf'])[moss]
    p.t[moss] = np.where(lv > 1.1, 4, 3)[moss]
    # heather roots from under the lip: short dark threads, 2 to 5 px
    rl = 2 + (hash01(p.x, 7, seed + 3) * 4).astype(int)
    roots = face & (j >= 1) & (j <= rl) & (hash01(p.x // 2, 9, seed + 4) < 0.18) & (p.x % 2 == 0)
    p.f[roots], p.t[roots] = IDX['leaf_cool'], 1
    # grit and stones in the face, lit top left
    st = body & (hash01(p.x // 3, j // 2, seed + 5) < 0.035)
    p.f[st], p.t[st] = IDX['stone'], 3
    p.t[st & ~shift(st, 0, 1, False)] = 4
    # the foot: dark, stony, grown over from below
    p.f[foot], p.t[foot] = IDX[fam_base + '_cool'], 1
    peb = foot & (hash01(p.x // 2, j, seed + 6) < 0.18)
    p.f[peb], p.t[peb] = IDX['stone_cool'], 2
    p.t[peb & ~shift(peb, 0, 1, False)] = 3
    weeds = face & (j >= H - 3) & (hash01(p.x // 2, 11, seed + 7) < 0.3) & (j >= H - 1 - (hash01(p.x, 12, seed) * 3).astype(int))
    p.f[weeds], p.t[weeds] = IDX['grass_cool'], np.where(j == H - 1, 2, 3)[weeds]
    if east is not None:
        p.step(face & east & ~rimline, -1, lo=0)
    despeckle(p, face & (j >= 4))


def grit_face(p: Plot, face, depth, height, seed=120):
    """The bluffs' gritstone (eastward 2.3 with the house boulders): rim line, an under-lip
    shade 4 px in two values, a streak zone of marks across, then rounded masses 10 to 18 px
    with horizontal bedding, each lit at its top left and dark below, dark gaps between them,
    a dark foot with fallen blocks."""
    if not face.any():
        return
    j = depth
    H = height
    rimline = face & (j == 0)
    shade = face & (j >= 1) & (j <= 4)
    streak = face & (j >= 5) & (j <= 8)
    foot = face & (j >= H - 3)
    body = face & (j >= 9) & ~foot
    p.f[rimline], p.t[rimline] = IDX['stone'], EDGE_T
    p.f[shade], p.t[shade] = IDX['stone_cool'], np.where(j <= 2, 0, 1)[shade]
    sm = streak & (hash01(p.x // 4, j, seed) < 0.55)
    p.f[streak], p.t[streak] = IDX['stone_cool'], 2
    p.f[sm], p.t[sm] = IDX['stone'], 3
    # masses: rounded gritstone lumps 12 to 20 px across, 8 to 11 deep, on a jittered grid,
    # each lit at its top left and dark below, with a bedding parting across the big ones
    jj = j - 9
    lid, mu, mv, crev = lumps(p.x, jj, 12, 8, seed)
    lv = -0.62 * mu - 0.78 * mv
    k = np.where(lv > 0.65, 4, np.where(lv > -0.05, 3, np.where(lv > -0.7, 2, 1)))
    pick = hash01(lid, 3, seed + 3)
    fam = np.where(pick < 0.4, IDX['stone_warm'], np.where(pick > 0.8, IDX['bleached_cool'], IDX['stone']))
    p.f[body], p.t[body] = fam[body], k[body]
    g = body & crev
    p.f[g], p.t[g] = IDX['stone_cool'], 0
    glint = body & ~crev & (lv > 1.0) & (hash01(lid, 4, seed + 4) < 0.7)
    p.t[glint] = 5
    bed = body & ~crev & (np.abs(mv - 0.1) < 0.09) & (hash01(lid, 5, seed + 5) < 0.5)
    p.step(bed, -1, lo=1)
    # lichen and moss in clusters on lit tops
    texture(p, body & ~crev, seed + 8, swaps=0.16, ups=0.03, downs=0.03)
    lich = body & (k >= 3) & (hash01(p.x // 2, p.y // 2, seed + 6) < 0.05)
    p.f[lich], p.t[lich] = IDX['bleached'], 4
    p.f[foot], p.t[foot] = IDX['stone_cool'], 1
    peb = foot & (hash01(p.x // 3, j, seed + 7) < 0.25)
    p.f[peb], p.t[peb] = IDX['stone'], 2
    p.t[peb & ~shift(peb, 0, 1, False)] = 3
    despeckle(p, face & (j >= 5))


def side_bands(p: Plot, T, face, rockpx, seed):
    """Eastward 3.3: where a tier ends west or east, a 3 px band on its own edge: lit facing
    west, dark facing east, with a broken ink line where it meets the lower ground. Returns
    the band (blocked, a face in the tier rows)."""
    west = np.zeros(T.shape, bool)
    east = np.zeros(T.shape, bool)
    hi_w = T > shift(T, 1, 0, 99)      # the pixel to the west is lower
    hi_e = T > shift(T, -1, 0, 99)     # the pixel to the east is lower
    for d in range(3):
        west |= shift(hi_w, d, 0, False)
        east |= shift(hi_e, -d, 0, False)
    west &= ~face
    east &= ~face
    for m, lit in ((west, True), (east, False)):
        rkm = m & rockpx
        pe = m & ~rockpx
        p.f[pe] = IDX['earth' if lit else 'earth_cool']
        p.t[pe] = (np.where(hash01(p.x, p.y // 3, seed) < 0.5, 3, 2) if lit else np.where(hash01(p.x, p.y // 3, seed) < 0.5, 1, 2))[pe]
        p.f[rkm] = IDX['stone']
        p.t[rkm] = 3 if lit else 1
    ink = ((hi_w | hi_e) & ~face) & (hash01(p.x // 4, p.y // 4, seed + 1) < 0.85)
    p.f[ink], p.t[ink] = IDX['ink'], 0
    # the band's cells: 8 px of the higher tier's edge are kept off (the walk and the tier
    # rows' 'f'), so the blocked edge lies on the 8 px lines
    hold_w = np.zeros(T.shape, bool)
    hold_e = np.zeros(T.shape, bool)
    for d in range(8):
        hold_w |= shift(hi_w, d, 0, False)
        hold_e |= shift(hi_e, -d, 0, False)
    # a band never runs on straight under a face (a face is 32 px, then ground, then the band
    # carries on): keep it 8 px clear below every face's foot
    under = np.zeros(T.shape, bool)
    for d in range(1, 9):
        under |= shift(face, 0, d, False)
    hold = (hold_w | hold_e) & ~face
    return hold, hold & ~under


def stair(p: Plot, x, y_top, y_bot, width=40, seed=160):
    """Stone steps through a face (eastward 6.1): treads of 5 or 6 px (a lit front row, the
    tread, a dark riser), the top tread flush with the upper ground at y_top, the bottom on
    the path at y_bot, the turf lip turning down either side as a 2 px cheek. Returns the
    walkable pixels."""
    x0, x1 = int(x - width // 2), int(x + width // 2)
    m = np.zeros((p.h, p.w), bool)
    m[max(0, y_top):min(p.h, y_bot + 1), max(0, x0):min(p.w, x1)] = True
    rel = p.y - y_top
    pitch = 5 if (y_bot - y_top) > 36 else 6
    sj = rel % pitch
    step_i = rel // pitch
    off = (hash01(step_i, p.x // 9, seed) * 3).astype(int)
    slab = (p.x + off) // 9
    pick = hash01(slab, step_i, seed + 1)
    fam = np.where(pick < 0.35, IDX['stone_warm'], np.where(pick > 0.75, IDX['stone_cool'], IDX['stone']))
    k = np.where(sj == 0, 4, np.where(sj >= pitch - 2, np.where(sj == pitch - 1, 1, 2), 3))
    k = np.where(((p.x + off) % 9 == 8) & (sj < pitch - 2), 2, k)
    p.f[m], p.t[m] = fam[m], k[m]
    cheek = m & ((p.x < x0 + 2) | (p.x >= x1 - 2))
    p.f[cheek] = IDX['earth_cool']
    p.t[cheek] = np.where(p.x < x0 + 2, 3, 1)[cheek]
    ink = np.zeros_like(m)
    ink[max(0, y_top):min(p.h, y_bot), max(0, x0 - 1):max(0, x0)] = True
    ink[max(0, y_top):min(p.h, y_bot), min(p.w - 1, x1):min(p.w, x1 + 1)] = True
    p.f[ink], p.t[ink] = IDX['earth_cool'], EDGE_T
    walk = m & ~cheek
    return walk


# --- paths --------------------------------------------------------------------------------------
def polyline_dist(p: Plot, pts, reach):
    """Distance from each pixel to a polyline (within reach; inf beyond) and the arc along it."""
    best = np.full((p.h, p.w), np.inf)
    arc = np.zeros((p.h, p.w))
    done = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay) or 1.0
        x0, x1 = int(max(0, min(ax, bx) - reach)), int(min(p.w, max(ax, bx) + reach + 1))
        y0, y1 = int(max(0, min(ay, by) - reach)), int(min(p.h, max(ay, by) + reach + 1))
        if x0 >= x1 or y0 >= y1:
            done += L
            continue
        X, Y = p.x[y0:y1, x0:x1] + 0.5, p.y[y0:y1, x0:x1] + 0.5
        t = np.clip(((X - ax) * (bx - ax) + (Y - ay) * (by - ay)) / (L * L), 0, 1)
        d = np.hypot(X - ax - t * (bx - ax), Y - ay - t * (by - ay))
        sub = best[y0:y1, x0:x1]
        sel = d < sub
        sub[sel] = d[sel]
        arc[y0:y1, x0:x1][sel] = (done + t * L)[sel]
        done += L
    return best, arc


def trod(p: Plot, pts, width=24, seed=180, ground_mask=None):
    """A sheep trod: bare earth and grit worn into the turf, its edge frayed in a 2 to 3 px
    band with a bite or a tuft every 16 px or so and dark crumbs along it (eastward 5.1), no
    outline. Returns its mask."""
    d, arc = polyline_dist(p, pts, width)
    hw = width / 2 - 3
    fray = (vnoise(arc, 0 * arc, 6, seed) - 0.5) * 3 + (hash01((arc // 16).astype(int), 0, seed + 1) < 0.25) * \
        np.where(hash01((arc // 16).astype(int), 1, seed + 1) < 0.5, 3, -3) * (np.abs((arc % 16) - 8) < 3)
    m = d < hw + fray
    if ground_mask is not None:
        m &= ground_mask
    base(p, m, 'path', seed + 2, scale=5)
    texture(p, m, seed + 3, swaps=0.08, ups=0.015, downs=0.02)
    rk.pebbles(p, m, seed + 4, 0.015)
    worn = m & (d < hw * 0.45)
    p.step(worn & (hash01(p.x // 2, p.y // 2, seed + 5) < 0.4), -1, lo=2)
    edge = m & ~erode(m, 1)
    crumbs = edge & (hash01(p.x // 2, p.y // 2, seed + 6) < 0.25)
    p.f[crumbs], p.t[crumbs] = IDX['path_cool'], 1
    despeckle(p, m)
    p.walk |= m
    return m


# --- standing things ----------------------------------------------------------------------------
def gritstone(size=1, seed=200):
    """A gritstone boulder or a small tor (size 0, 1, 2): rounded blocks stacked on their
    bedding planes, each lit at its top left, lichen on the tops, a dark crease under each
    block, heather tucked at the foot."""
    W = (18, 30, 46)[size]
    H = (12, 20, 32)[size]
    sp = Sprite(W + 4, H + 4, W // 2 + 2, H + 2)
    blocks = []
    rows = (1, 2, 3)[size]
    y = H + 2
    for r in range(rows):
        bh = 7 + int(hash01(r, 0, seed) * 4)
        n = max(1, int((W - r * 6) / (10 + hash01(r, 1, seed) * 8)))
        span = W - r * 7
        x = 2 + r * 3 + int(hash01(r, 2, seed) * 3)
        for i in range(n):
            bw = span // n + (1 if i % 2 else 0)
            blocks.append((x, y - bh, bw, bh))
            x += bw
        y -= bh - 1
    for (bx, by, bw, bh) in blocks:
        u = (sp.x + 0.5 - (bx + bw / 2)) / (bw / 2)
        v = (sp.y + 0.5 - (by + bh / 2)) / (bh / 2)
        inside = (np.abs(u) <= 1) & (np.abs(v) <= 1) & ~((np.abs(u) > 0.75) & (np.abs(v) > 0.6))
        lv = -0.6 * u - 0.8 * v
        k = np.where(lv > 0.6, 4, np.where(lv > -0.1, 3, np.where(lv > -0.7, 2, 1)))
        fam = 'stone_warm' if hash01(bx, by, seed + 3) < 0.5 else 'stone'
        sp.put(inside, fam, k)
        crease = inside & (v > 0.8)
        sp.put(crease, 'stone_cool', 1)
        gl = inside & (lv > 1.05)
        sp.put(gl, fam, 5)
    li = sp.m & (sp.t >= 3) & (hash01(sp.x // 2, sp.y // 2, seed + 4) < 0.08)
    sp.put(li, 'bleached', 4)
    sh = rk.blob(sp.fx + W * 0.25, sp.fy, W * 0.55, 3, sp.m.shape, seed, wob=0.1) & ~sp.m
    return sp, sh


def scots_pine(seed=220, scale=1.0):
    """A Scots pine on the moor (size guide: a conifer 60 to 110): a bare, leaning trunk,
    orange-red where the bark flakes in the upper half, and a flat umbrella of dark blue-green
    clumps held out on crooked limbs."""
    H = int(78 * scale)
    W = int(56 * scale)
    sp = Sprite(W, H, W // 2, H - 2)
    lean = 3 if hash01(seed, 0, 1) < 0.5 else -3
    for y in range(int(H * 0.30), H - 1):
        t = (y - H * 0.30) / (H * 0.7)
        cx = W // 2 + int(lean * (1 - t))
        upper = t < 0.55
        for dx in range(-1, 3):
            k = 4 if dx == -1 else 1 if dx == 2 else 3 if dx == 0 else 2
            fam = 'clay_warm' if upper else 'timber_cool'
            sp.put(rk._one(sp, cx + dx, y), fam, k)
    crowns = [(W // 2 + lean - 8, int(H * 0.22), 13, 6), (W // 2 + lean + 9, int(H * 0.27), 11, 5),
              (W // 2 + lean, int(H * 0.12), 12, 6)]
    for i, (cx, cy, rx, ry) in enumerate(crowns):
        crown(sp, cx, cy, rx * scale, ry * scale, seed + i, 'leaf_cool', clump=2.0, lobes=9, wob=0.22, rim=False)
    return sp, tree_shadow(sp, W // 2 + 2, 16, 5)


def sprite_despeckle(sp: Sprite, passes=2):
    """No lone pixels inside a sprite (house rule 4): a pixel unlike its four neighbours takes
    the colour two of them share."""
    key = np.where(sp.m, sp.f.astype(np.int32) * 8 + sp.t, -1)
    for _ in range(passes):
        nb = [shift(key, dx, dy, -1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        lone = sp.m & np.all([key != n for n in nb], axis=0)
        pick = np.full(key.shape, -1)
        for i in range(4):
            for j in range(i + 1, 4):
                pick = np.where((nb[i] == nb[j]) & (nb[i] >= 0), nb[i], pick)
        ok = lone & (pick >= 0)
        sp.f[ok], sp.t[ok] = pick[ok] // 8, pick[ok] % 8
        key = np.where(sp.m, sp.f.astype(np.int32) * 8 + sp.t, -1)


def _gorse_one(seed, w=28, h=20):
    """One gorse bush: a dark spiny mound of short needle clumps lit on its top left, its
    flowers in small clusters (two or three pixels: a lit petal pair over a shaded one),
    more on the sunny side, never single pixels (house rule 4)."""
    sp = Sprite(w, h, w // 2 - 1, h - 2)
    crown(sp, w / 2, h * 0.55, w / 2 - 2, h * 0.4, seed, 'leaf_cool', clump=2.9, lobes=10, wob=0.2, rim=False)
    sprite_despeckle(sp)
    lit = sp.m & (sp.t >= 3)
    seeds = lit & (hash01(sp.x // 2, sp.y // 2, seed + 2) < 0.16) & (sp.x % 2 == 0) & (sp.y % 2 == 0)
    pair = seeds | (shift(seeds, 1, 0, False) & sp.m)
    sp.put(pair, 'brass', 4)
    sp.put(seeds & (sp.x < w * 0.5), 'brass', 5)
    under = shift(seeds, 0, 1, False) & sp.m & ~pair
    sp.put(under, 'brass', 2)
    return sp


def gorse(seed=240, size=1):
    """A gorse bush (size 0 small, 1, 2 a big clump of two) with its blob shadow."""
    if size < 2:
        w, h = (22, 16) if size == 0 else (28, 20)
        sp = _gorse_one(seed, w, h)
        return sp, tree_shadow(sp, w // 2 + 1, w // 2 - 2, 4)
    big = Sprite(46, 28, 22, 26)
    for dx, dy, s in ((0, 6, seed), (16, 8, seed + 1)):
        a = _gorse_one(s)
        ys, xs = np.nonzero(a.m)
        big.f[ys + dy, xs + dx] = a.f[ys, xs]
        big.t[ys + dy, xs + dx] = a.t[ys, xs]
        big.m[ys + dy, xs + dx] = True
    return big, tree_shadow(big, 24, 20, 5)


# --- pasting and painting in windows (a region is millions of pixels; river_kit's pieces work
# on the whole plot they are given) ----------------------------------------------------------
class Window(Plot):
    """A rectangle of a plot, sharing its arrays (numpy views), so river_kit's pieces can draw
    into a small part of a big plot at the cost of the part. Its x and y are its own."""

    def __init__(self, p: Plot, x0, y0, x1, y1):
        self.w, self.h = x1 - x0, y1 - y0
        for a in ('f', 't', 'wet', 'solid', 'walk', 'crossing'):
            setattr(self, a, getattr(p, a)[y0:y1, x0:x1])
        self.y, self.x = np.mgrid[0:self.h, 0:self.w]
        self.x0, self.y0 = x0, y0


def run_windowed(p: Plot, mask, fn, size=256, pad=12):
    """Paint fn(window_plot, window_mask) over a big plot one window at a time, skipping
    windows the mask does not reach. Each window is painted on its own small plot (the
    window plus `pad` px round it, its pixel coordinates the big plot's, so hash noise runs
    on without a seam) and only its core is copied back."""
    mask = np.asarray(mask, bool)
    for y0 in range(0, p.h, size):
        for x0 in range(0, p.w, size):
            y1, x1 = min(p.h, y0 + size), min(p.w, x0 + size)
            if not mask[y0:y1, x0:x1].any():
                continue
            a0, b0 = max(0, x0 - pad), max(0, y0 - pad)
            a1, b1 = min(p.w, x1 + pad), min(p.h, y1 + pad)
            q = Plot(a1 - a0, b1 - b0)
            q.f[:], q.t[:] = p.f[b0:b1, a0:a1], p.t[b0:b1, a0:a1]
            q.y, q.x = np.mgrid[b0:b1, a0:a1]
            fn(q, mask[b0:b1, a0:a1])
            cy0, cx0 = y0 - b0, x0 - a0
            p.f[y0:y1, x0:x1] = q.f[cy0:cy0 + (y1 - y0), cx0:cx0 + (x1 - x0)]
            p.t[y0:y1, x0:x1] = q.t[cy0:cy0 + (y1 - y0), cx0:cx0 + (x1 - x0)]


def in_box(p: Plot, pts, reach, fn):
    """Run fn(window, local_pts) on the window round a polyline (plus reach), in the window's
    own coordinates (river_kit's channels index pixels by position). Returns the window's
    top-left and fn's result."""
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    x0, y0 = max(0, int(min(xs) - reach)), max(0, int(min(ys) - reach))
    x1, y1 = min(p.w, int(max(xs) + reach)), min(p.h, int(max(ys) + reach))
    win = Window(p, x0, y0, x1, y1)
    return x0, y0, fn(win, [(q[0] - x0, q[1] - y0) for q in pts])


def paste_at(p: Plot, sp: Sprite, x, y, shadow=None, outline=True, block=None):
    """river_kit.paste in a window round the sprite: returns (mask, x0, y0), the pixels the
    sprite covers in the window and the window's top-left."""
    x0, y0 = max(0, x - sp.fx - 3), max(0, y - sp.fy - 3)
    x1, y1 = min(p.w, x - sp.fx + sp.w + 14), min(p.h, y - sp.fy + sp.h + 10)
    if x0 >= x1 or y0 >= y1:
        return np.zeros((0, 0), bool), x0, y0
    win = Window(p, x0, y0, x1, y1)
    full = paste(win, sp, x - x0, y - y0, outline=outline, shadow=shadow, block=block)
    return full, x0, y0


# --- story props drawn into the ground ----------------------------------------------------------
def _sprite_from(rows, palette, fx, fy):
    h, w = len(rows), max(len(r) for r in rows)
    sp = Sprite(w, h, fx, fy)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in palette:
                fam, k = palette[ch]
                sp.put(rk._one(sp, x, y), fam, k)
    return sp


FIRE_RING = [
    '..aAAa..',
    '.aCcccAa',
    'aCceeccA',
    'ACcEecc1',
    '.1Cccc1.',
    '..1111..',
]


def fire_ring(lit=False, seed=260):
    """A cold fire ring (story prop): a ring of grey stones lit on their tops round ash and
    charcoal; `lit`, the hermit's fire: embers glowing in the middle."""
    pal = {'a': ('stone', 4), 'A': ('stone', 3), 'C': ('stone_cool', 2), '1': ('stone_cool', 1),
           'c': ('ash', 2), 'e': ('soot', 1), 'E': ('soot', 2)}
    if lit:
        pal.update({'e': ('lava', 3), 'E': ('lava', 5)})
    sp = _sprite_from(FIRE_RING, pal, 4, 5)
    return sp, None


def hoofprints(p: Plot, m, seed=280):
    """Tracks: pairs of cloven prints pressed into soft ground (each print's top in shade,
    its lower lip lit), in a loose drift along the way."""
    seeds = m & (hash01(p.x // 4, p.y // 3, seed) < 0.10) & (p.x % 4 == 0) & (p.y % 3 == 0)
    a = seeds
    b = shift(seeds, 2, 0, False)
    for s in (a, b):
        p.step(s & m, -2, lo=1)
        p.step(shift(s, 0, 1, False) & m, 1)


BOOT = ['.11..', '.21..', '.221.', '22211', '11111']
HAT = ['..111..', '.12221.', '1223321', '.11111.']
BELL = ['..1..', '.343.', '.332.', '43321', '11111']


def boot(seed=300):
    return _sprite_from(BOOT, {'1': ('timber_cool', 1), '2': ('timber_cool', 2)}, 2, 4), None


def hat(seed=310):
    return _sprite_from(HAT, {'1': ('slate_cool', 1), '2': ('slate', 2), '3': ('slate', 3)}, 3, 3), None


def bell(seed=320):
    """The buried bell's lip showing through the turf: bronze, its top lit, green with age."""
    return _sprite_from(BELL, {'1': ('copper', 1), '2': ('copper', 2), '3': ('copper', 3), '4': ('copper', 4)}, 2, 4), None


CART = [
    '.....1111111111....',
    '....122222222221...',
    '...12333333333321..',
    '...1222222222222...',
    '..1.1...1...1..1...',
    '.111....1.......111',
    '1.2.1..........1.2.',
    '1222............111',
    '.111...............',
]


def cart_wreck(seed=340):
    """A cart with a broken wheel (story prop): the bed tipped on its side, one wheel lying
    flat in the turf."""
    pal = {'1': ('timber_cool', 1), '2': ('timber', 2), '3': ('timber', 4)}
    return _sprite_from(CART, pal, 9, 8), None


# --- the sheet --------------------------------------------------------------------------------
def sample(seed=1):
    """A 320 x 288 sample: a heather tier above a peat face over the road, a gritstone bluff,
    a stair, a trod, gorse, a pine and the story props."""
    W, H = 320, 288
    p = Plot(W, H)
    tier = np.zeros((H, W), np.int16)
    # an organic upper tier: rim along y ~ 110 with jogs, a bluff tier 2 in the middle
    rim = (110 + 8 * np.round((fbm(np.arange(W), 0 * np.arange(W), 40, seed) - 0.5) * 2)).astype(int)
    for x in range(W):
        tier[:rim[x], x] = 1
    tier[:, :24] = np.where(np.arange(H)[:, None] < 150, 1, 0)
    bl = (p.x >= 150) & (p.x < 230) & (p.y < 92)
    tier[bl] = 2
    face, depth, height, upper = face_depth(tier)
    top = ~face
    moor(p, top & (tier >= 1), seed)
    turf(p, top & (tier == 0), seed + 5, yellow=0.6)
    rimrow = top & (shift(face, 0, -1, False))
    lip(p, rimrow, seed)
    rock = face & (upper == 2)
    grit_face(p, rock, depth, height, seed)
    peat_face(p, face & ~rock, depth, height, seed)
    sb, _ = side_bands(p, tier, face, (tier == 2) | rock, seed=seed)
    road = [(0, 200), (80, 196), (150, 210), (230, 220), (320, 214)]
    rk.track(p, road, width=32, seed=seed + 7, puddles=1)
    tm = trod(p, [(90, 186), (96, 150), (104, 128), (120, 96), (150, 70)], 24, seed + 8, ground_mask=~face)
    st = stair(p, 104, 108, 140, 40, seed + 9)
    for i, (x, y) in enumerate(((40, 60), (70, 90), (260, 80), (280, 150), (20, 250))):
        sp, sh = gorse(seed + i, size=i % 3)
        paste(p, sp, x, y, shadow=sh)
    sp, sh = scots_pine(seed + 3)
    paste(p, sp, 290, 60, shadow=sh)
    for i, (x, y) in enumerate(((180, 40), (60, 170))):
        sp, sh = gritstone(i + 1, seed + i)
        paste(p, sp, x, y, shadow=sh)
    for mk, (x, y) in ((fire_ring, (40, 240)), (cart_wreck, (130, 250)), (boot, (200, 245)), (hat, (230, 260)),
                       (bell, (260, 250))):
        sp, sh = mk()
        paste(p, sp, x, y, outline=False)
    return p


BAR_BOXES = (('heather', (30, 4, 94, 68), 'ground'), ('heather 2', (232, 4, 296, 68), 'ground'),
             ('turf', (200, 236, 296, 284), 'ground'), ('peat face', (236, 110, 300, 144), 'face'),
             ('gritstone', (158, 92, 222, 126), 'face'))


def main(argv) -> int:
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-moor-kit')
    os.makedirs(out, exist_ok=True)
    p = sample()
    img = p.image()
    img.save(os.path.join(out, 'sample.png'))
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(os.path.join(out, 'sample-3x.png'))
    import detail_bar as db
    for name, box, kind in BAR_BOXES:
        ok, c, lines = db.check_image(img, box, kind)
        print(f'{name:12s} {kind:7s} {"PASS" if ok else "FAIL"}  ' + '; '.join(lines))
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
