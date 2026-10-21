"""The city kit: the ground every town of the world is laid with.

Claude C's lane (Neon Harbour and its old town on the Falls Rock, Lullford, Gullwick;
docs/vision/rebuild-plan.md, section 3: "City kit: streets, quays, stairs between levels, the
falls in the city", from facade.py and the house kits). Nothing in the game reads it yet: it
proves the look before a town is rebuilt from it. No old asset is reused (AGENTS.md).

The city is built on the soft grid at its own measure (verticality.md, the Neon brief's
section 4): a tier is a 40 px south face, its ends 5 px side bands, its cast shadow 8 px; the
quays are one tier below the streets and reached by ramps; stair streets climb the fall line
in flights 40 open between cheeks; the falls of the Glint step down the tiers beside them.
Built edges are straighter than the coast's but never ruled across a screen: walls jog,
buttress and turn, and every edge is dressed (Matt, 21 Oct: edges are drawn as Eastward
draws them, so this kit is compared with Eastward's town screens only).

The pieces (each with a seed, all deterministic), drawn in the house style (every pixel a
tone of a house ramp or a family's edge tone, clusters of two or more, light from the upper
left, shadows two tones down their own ramp):
- ground: `asphalt()` (a worn road: patched squares, sealed cracks, wheel tracks, oil,
  faded paint, a manhole and gully grates), `flags()` (pavement flagstones in courses, one
  cracked here and there), `kerb()` (long granite stones with their lit arris and the
  gutter), the coast kit's `setts()` for the old town's streets and the quays, `tram_rails()`
  (two grooved rails with setts between), `tree_pit()` (an iron grille round a street
  tree's foot), `manhole()`, `gully()`.
- built faces: `brick_wall()` (a 40 px retaining wall in weathered brick, whole brick by
  whole brick, the parts kept from #138: soot, hotter-fired bricks, a repair in buff stock,
  repointing, salt and moss low down, pilasters of ashlar, weep holes), `ashlar_wall()`
  (dressed courses), `railing()` (an iron railing along a top's rim), `parapet()`.
- water: `glint()` (the river in a stone-lined channel), `cascade()` (its falls down the
  tiers into a churned basin), `harbour()` (the ria's water along a quay wall: the wall's dark
  reflection, ripples, a calm plane).
- ways: the coast kit's `stair()` and `ramp_along()` (with `stepped_tread`), `stair_street()`.
- the quay: the coast kit's `masonry()` sea wall, `setts()`, bollards, coils and fish boxes.
- buildings: `house_front()` takes a front from house_kits.py (#121) in a colourway and sets
  it on its street with its outline and shadow.

The shared core (the plot, clusters, outline, shadow, sprites, the relief and its lattice,
the ways) is the coast kit's (#162), so this module is stacked on it.

Run:
    python3 scripts/art/city_kit.py --check     (walk contracts; exits non-zero on a fault)
    python3 scripts/art/city_kit.py [OUT_DIR]
writes OUT_DIR/corner.png (the Falls Rock corner: the old town's street, a stair street down
its retaining wall, the high street with its tram, a ramp down to the quay, the Glint's falls
into the ria; 640 x 640 at 1x), corner-2x.png (with residents), corner-night.png,
corner-flow.gif, kit-sheet.png (every piece at 2x with its detail bar result) and
compare.png (crops beside Eastward's town screens at the same character height, when the
screenshots are in REF_DIR). Default OUT_DIR: napattack-city-kit in the temp folder.
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
import coast_kit as ck  # noqa: E402
from coast_kit import (IDX, EDGE_T, Plot, Relief, hash01, fbm, shift, dilate, stamp, base, texture, _pt, DOMINOES,  # noqa: E402
                       _scatter, paste, lattice, tier_shadows, bands, dist_to, SMALL, FLAT, stair, ramp_along,
                       stepped_tread, masonry, setts, bollard, coil, fish_crate, net_heap, ripples, _from_canvas,
                       _label, bar_line, _reaches)

FACE_CITY = 40
E_CITY = [0, 40, 80, 120]   # the ria, the quay, the high street, the old town on the Falls Rock


# --- ground ------------------------------------------------------------------------------------
def asphalt(p: Plot, m, seed=0, along='x', lanes=None):
    """A worn town road: asphalt in calm patches, darker where it is newer; square patches of
    repair with a crisp sealed edge; cracks sealed with tar in a meandering dark line; two
    wheel tracks a tone lighter along each lane; oil stains in the lanes' middles; the
    centre line in faded paint dashes; walkable."""
    m = np.asarray(m, bool)
    base(p, m, [('asphalt', 0.5), ('asphalt_cool', 0.3), ('asphalt_warm', 0.2)], seed, 16, tone=3, light=0.75, dark=0.3)
    texture(p, m, seed + 1, swaps=0.05, ups=0.02, downs=0.02, shapes=FLAT)
    ys = np.nonzero(m.any(1))[0]
    xs = np.nonzero(m.any(0))[0]
    if not len(ys):
        return
    u = (p.y - ys.min()) if along == 'x' else (p.x - xs.min())
    span = (ys.max() - ys.min() + 1) if along == 'x' else (xs.max() - xs.min() + 1)
    lanes = lanes or (span / 4.0, span * 3 / 4.0)
    for c in lanes:
        for off in (-7, 6):
            tr = m & (np.abs(u - c - off + (fbm(p.x, p.y, 30, seed + 2) - 0.5) * 2) < 2.2)
            p.step(tr & (hash01(p.x // 3, p.y // 2, seed + 3) < 0.8), 1)
        oil = m & (np.abs(u - c) < 3) & (fbm(p.x, p.y, 6, seed + 4) > 0.72)
        p.step(oil, -1, lo=0)
    for (x, y) in _scatter(m, 2600, seed + 5, margin=6):           # patches of repair
        w, h = 10 + int(hash01(x, y, seed) * 18), 6 + int(hash01(x, y, seed + 1) * 8)
        pm = m & (p.x >= x) & (p.x < x + w) & (p.y >= y) & (p.y < y + h)
        p.put(pm, 'asphalt_cool', 2)
        p.put(pm & ~shift(pm, 0, 1, False), 'asphalt', 3)
        stamp(p, pm, 0.06, seed + 6, FLAT, dt=1)
    crack = m & (np.abs(fbm(p.x, p.y, 14, seed + 7) - 0.5) < 0.012) & (fbm(p.x, p.y, 40, seed + 8) > 0.55)
    p.put(crack, 'asphalt', 0)
    centre = (u >= span / 2.0 - 1) & (u < span / 2.0 + 1) & m
    dash = centre & ((((p.x if along == 'x' else p.y) // 8) % 2) == 0) & (hash01((p.x if along == 'x' else p.y) // 16, 0, seed + 9) < 0.8)
    p.put(dash, 'plaster', 4)
    p.put(dash & (hash01(p.x // 2, p.y, seed + 10) < 0.35), 'plaster', 3)     # the paint worn
    p.walk |= m & ~p.hazard
    p.solid &= ~m


def manhole(p: Plot, x, y, r=4):
    """A cast-iron cover set flush in the road: a ring lit on its upper west, a cross-hatch."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dx, dy)
            if d > r + 0.3:
                continue
            t = 3 if d > r - 1.2 and (dx + dy) < 0 else (1 if d > r - 1.2 else (2 if (dx + dy) % 3 else 3))
            p.put(_pt(p, x + dx, y + dy), 'iron', t)


def gully(p: Plot, x, y, w=8):
    """A gully grate in the gutter: an iron frame and its slots."""
    for i in range(w):
        for j in range(4):
            t = 3 if j == 0 else (1 if (i % 2 and 0 < j < 3) else 2)
            p.put(_pt(p, x + i, y + j), 'iron', t)


def flags(p: Plot, m, seed=0, course=7, ramps=('ashlar', 'ashlar_cool', 'stone_warm', 'concrete_warm')):
    """Pavement flagstones in courses (7 px) of slabs 9 to 15 px long in broken bond: each slab
    lit along its upper west arris, its joints a tone down, its body in one of the paving
    stones; a slab cracked across now and then, one sunk a tone darker, grass in a joint."""
    m = np.asarray(m, bool)
    row = p.y // course
    off = (hash01(row, 0, seed) * 13).astype(int)
    ln = 9 + (hash01((p.x + off) // 12, row, seed + 1) * 7).astype(int)
    idx = (p.x + off) // ln
    fam = np.array([IDX[r] for r in ramps])[(hash01(idx, row, seed + 2) * len(ramps)).astype(int)]
    r = p.y % course
    first = idx != shift(idx, 1, 0, -1)
    last = idx != shift(idx, -1, 0, -1)
    hb = hash01(idx, row, seed + 3)
    body = np.where(hb < 0.2, 2, np.where(hb > 0.8, 4, 3))
    t = np.where(r == 0, 4, np.where(r == course - 1, 1, body))
    t = np.where(first & (r > 0) & (r < course - 1), 4, t)
    t = np.where(last, 1, t)
    p.f[m] = fam[m]
    p.t[m] = t[m]
    crack = m & (hash01(idx, row, seed + 4) < 0.1) & (np.abs((p.x - idx * ln - off) - (p.y % course) * 1.2 - 3) < 0.6)
    p.t[crack] = 1
    joint = m & ((r == course - 1) | last) & (hash01(p.x // 2, p.y, seed + 5) < 0.06)
    p.put(joint, 'grass_cool', 3)
    stain = m & (fbm(p.x, p.y, 9, seed + 6) > 0.72) & ~((r == course - 1) | last)
    p.step(stain, -1)
    stamp(p, m & (r > 0) & (r < course - 1) & ~last, 0.05, seed + 7, DOMINOES, swap='mix')
    p.walk |= m & ~p.hazard
    p.solid &= ~m


def kerb(p: Plot, line, seed=0, face_down=True):
    """A kerb of long granite stones along a line mask (2 px): the top lit with a joint every
    20 to 30 px, the face to the road a tone down, the gutter beside it a tone darker."""
    line = np.asarray(line, bool)
    j = (p.x + (hash01(p.y // 3, 0, seed) * 20).astype(int)) % (20 + (hash01(p.y // 3, 1, seed) * 10).astype(int)) == 0
    p.put(line, 'stone', 4)
    p.put(line & j, 'stone', 2)
    lo = shift(line, 0, 1, False) & ~line
    p.put(lo, 'stone_cool', 2)
    gut = shift(lo, 0, 1, False) & ~line & ~lo
    p.step(gut, -1, lo=0)


def tram_rails(p: Plot, y, x0, x1, seed=0, gauge=14):
    """Grooved tram rails along a street (gauge 14): each rail two px of polished iron with its
    groove a dark px, and between and beside them a band of setts the road is laid against."""
    band = (p.y >= y - 4) & (p.y < y + gauge + 4) & (p.x >= x0) & (p.x < x1)
    setts(p, band, seed, ramps=('stone', 'stone_cool', 'ashlar_cool'), course=4)
    for ry in (y, y + gauge):
        p.put((p.y == ry) & (p.x >= x0) & (p.x < x1), 'iron', 5)
        p.put((p.y == ry + 1) & (p.x >= x0) & (p.x < x1), 'iron', 1)
        p.put((p.y == ry - 1) & (p.x >= x0) & (p.x < x1), 'iron', 3)


def tree_pit(p: Plot, x, y, seed=0):
    """A street tree's pit: a square iron grille with its radial slots round a dark trunk."""
    for j in range(-6, 7):
        for i in range(-6, 7):
            if max(abs(i), abs(j)) == 6:
                p.put(_pt(p, x + i, y + j), 'iron', 3 if (i < 0 or j < 0) else 1)
            elif (i + j) % 2 == 0 and max(abs(i), abs(j)) > 2:
                p.put(_pt(p, x + i, y + j), 'iron', 2)
            elif max(abs(i), abs(j)) > 2:
                p.put(_pt(p, x + i, y + j), 'earth', 1)
    for j in range(-2, 3):
        for i in range(-2, 3):
            p.put(_pt(p, x + i, y + j), 'earth', 0 if i + j > 0 else 1)


# --- built faces --------------------------------------------------------------------------------
BRICK = ('clay', 'clay', 'clay_warm', 'clay_cool')


def brick_wall(p: Plot, R: Relief, m, seed=0, ramps=BRICK, pilaster=56):
    """A 40 px retaining wall in weathered town brick, as #138's `weathered_bricks` laid it:
    courses of 3 px, bricks 6 long in stretcher bond, each lit along its top, its east end
    turned from the light, the mortar a dark joint; then whole bricks changed: a hotter-fired
    brick here and there, smoke-blackened ones under the coping, a patch rebuilt in buff
    stock brick, a stretch repointed in pale lime, salt blooming on the lowest courses and
    moss in their joints; pilasters of ashlar every `pilaster` px (lit west, dark east) with
    a coping of long stones, and weep holes near the foot."""
    fc = R.face & np.asarray(m, bool)
    if not fc.any():
        return fc
    d, fh = R.depth, R.fh
    ci = d // 4
    off = np.where(ci % 2 == 1, 4, 0)
    bi = (p.x + off) // 8
    r = d % 4
    c = (p.x + off) % 8
    fam = np.array([IDX[x] for x in ramps])[(hash01(bi, ci, seed) * len(ramps)).astype(int)]
    hb0 = hash01(bi, ci, seed + 11)
    t = np.where(r == 0, np.where(hb0 < 0.3, 4, 3), np.where(r == 3, 1, np.where(hb0 > 0.8, 3, 2)))
    t = np.where((c == 7), 1, t)
    t = np.where((c == 0) & (r < 3), 3, t)
    t = np.where((c == 6) & (r == 2), 1, t)
    p.f[fc] = fam[fc]
    p.t[fc] = t[fc]
    up = fh - 1 - d
    hb = hash01(bi, ci, seed + 1)
    brick = fc & (c < 7) & (r < 3)
    p.put(brick & (hb > 0.94) & (r == 0), 'clay_warm', 3)              # hotter fired
    p.put(brick & (hb > 0.94) & (r > 0), 'clay_warm', 2)
    soot = brick & (hb < 0.04 + 0.14 * (d < 10))
    p.put(soot & (r == 0), 'soot', 3)
    p.put(soot & (r == 1), 'soot', 2)
    stock = brick & (fbm(bi * 8.0, ci * 4.0, 14, seed + 2) > 0.74)
    p.put(stock & (r == 0), 'sand_cool', 4)
    p.put(stock & (r == 1), 'sand_cool', 3)
    repoint = fc & ((c == 7) | (r == 3)) & (fbm(bi * 8.0, ci * 4.0, 12, seed + 3) < 0.25)
    p.put(repoint, 'ashlar', 3)
    damp = fc & (fbm(bi * 8.0, ci * 4.0, 18, seed + 4) > 0.7)
    p.step(damp & (p.t < EDGE_T), -1, lo=0)
    salt = brick & (up < 8) & (r == 1) & (hash01(bi, ci, seed + 5) < 0.4) & (c >= 1) & (c <= 4)
    p.put(salt, 'snow_cool', 3)
    moss = fc & (up < 6) & (r == 3) & (hash01(p.x // 2, ci, seed + 6) < 0.4)
    p.put(moss, 'grass_cool', 2)
    # the pilasters and the coping
    px_ = (p.x + int(hash01(0, 0, seed) * pilaster)) % pilaster
    pil = fc & (px_ < 7)
    p.put(pil, 'ashlar', 3)
    p.put(pil & (px_ < 2), 'ashlar_warm', 4)
    p.put(pil & (px_ >= 5), 'ashlar_cool', 1)
    p.put(pil & ((d % 8) == 7), 'ashlar', 2)
    cop = fc & (d < 4)
    p.put(cop, 'ashlar_warm', 4)
    p.put(cop & (d == 0), 'ashlar_warm', 5)
    p.put(cop & (d == 3), 'ashlar', 1)
    p.put(cop & (((p.x + 5) // 26) != ((p.x + 6) // 26)) & (d < 3), 'ashlar', 2)
    weep = fc & (up >= 4) & (up < 6) & ((p.x % 24) < 2) & ~pil
    p.put(weep, 'soot', 0)
    stain = fc & (up < 4) & (((p.x - 1) % 24) < 3) & ~pil
    p.put(stain & (p.t >= 2), 'grass_cool', 1)
    p.solid |= fc
    p.walk &= ~fc
    return fc


def railing(p: Plot, R: Relief, m, seed=0, gap=None):
    """An iron railing along a top's rim (it stops a walker): a top rail lit on its upper
    edge, square balusters every 3 px, a stouter post every 18 with its cap, the shadow a
    tone down on the coping below."""
    rim = R.rim & np.asarray(m, bool)
    if gap is not None:
        rim &= ~gap
    line = shift(rim, 0, -3, False)
    top = line
    p.put(top, 'iron', 4)
    p.put(shift(top, 0, 1, False) & ~R.face, 'iron', 2)
    bal = (shift(rim, 0, -1, False) | shift(rim, 0, -2, False)) & ((p.x % 3) == 0)
    p.put(bal, 'iron', 2)
    post = (shift(rim, 0, -1, False) | shift(rim, 0, -2, False) | top | shift(rim, 0, -4, False)) & ((p.x % 18) < 2)
    p.put(post, 'iron', 3)
    p.put(post & ((p.x % 18) == 1), 'iron', 1)
    p.walk &= ~(top | bal | post | shift(rim, 0, -1, False) | shift(rim, 0, -2, False))
    p.solid |= top | bal | post


# --- water ------------------------------------------------------------------------------------
def glint(p: Plot, x0, x1, y0, y1, seed=0):
    """The Glint in its stone-lined channel through the town: a lit coping on both banks,
    the channel walls' dark faces inside them, the water quick and streaked with the flow,
    darker under its west wall. Returns the water mask."""
    ch = (p.x >= x0) & (p.x < x1) & (p.y >= y0) & (p.y < y1)
    cop = ch & ((p.x < x0 + 3) | (p.x >= x1 - 3))
    p.put(cop, 'ashlar_warm', 4)
    p.put(cop & ((p.x == x0) | (p.x == x1 - 1)), 'ashlar', 2)
    p.put(cop & (((p.y + 3) // 14) != ((p.y + 4) // 14)), 'ashlar', 2)
    wall_w = ch & ((p.x == x0 + 3) | (p.x == x0 + 4))
    p.put(wall_w, 'ashlar_cool', 1)
    wat = ch & (p.x > x0 + 4) & (p.x < x1 - 3)
    p.put(wat, 'water', 3)
    p.put(wat & (p.x < x0 + 8), 'water', 2)
    streak = wat & (((p.y + (hash01(p.x, 0, seed) * 13).astype(int)) % 11) < 4) & (hash01(p.x // 2, p.y // 11, seed + 1) < 0.5)
    p.put(streak, 'water', 4)
    p.put(shift(streak, 0, 1, False) & wat & ~streak, 'water_cool', 2)
    p.wet |= wat
    p.hazard |= wat
    p.walk &= ~(wat | cop | wall_w)
    p.solid |= cop | wall_w
    return wat


def cascade(p: Plot, R: Relief, x0, x1, seed=0, k=None):
    """The Glint falling down every face it meets between x0 and x1: white where it tips over
    each lip, falling streaks of water and white, spray on the wall beside it, and churned
    white at each foot where it lands."""
    col = (p.x >= x0) & (p.x < x1) & R.face
    if k is not None:
        col &= R.kf == k
    if not col.any():
        return col
    k = (p.x - x0 + (hash01(p.x, 0, seed) * 3).astype(int)) % 4
    ph = ((p.y + (hash01(p.x, 1, seed + 1) * 12).astype(int)) // 3) % 4
    p.put(col, 'water', 3)
    p.t[col & (k == 0)] = 4
    p.put(col & (k == 1) & (ph != 0), 'snow', 5)
    p.put(col & (k == 3) & (ph == 2), 'snow_cool', 4)
    p.t[col & ((p.x == x0) | (p.x == x1 - 1))] = 2
    lip = col & (R.depth <= 1)
    p.put(lip, 'snow', 5)
    foot = col & (R.depth >= R.fh - 3)
    p.put(foot, 'snow', 4)
    land = shift(col & (R.depth == R.fh - 1), 0, 1, False) & ~R.face
    churn = dilate(land, 3) & ~R.face & ~col
    stamp(p, churn & p.wet, 0.5, seed + 2, SMALL, ramp='snow', tone=5, same_family=False)
    spray = R.face & ~col & (np.abs(p.x - (x0 + x1) / 2.0) < (x1 - x0) / 2.0 + 4)
    stamp(p, spray, 0.2, seed + 3, SMALL, ramp='snow_cool', tone=4, same_family=False)
    p.wet |= col
    p.hazard |= col
    p.walk &= ~col
    return col


def harbour(p: Plot, m, seed=0):
    """The ria's water along the town: a calm plane in the lagoon's deep tones, darker in a
    band along the quay wall where the wall's reflection lies, the reflection broken into
    horizontal strokes, a few ripples and glints."""
    m = np.asarray(m, bool)
    d = dist_to(~m, 60)
    p.put(m, 'lagoon_cool', 2)
    p.put(m & (d > 30), 'water', 2)
    p.put(m & (d > 50), 'water_cool', 2)
    q = fbm(p.x, p.y * 1.4, 30, seed)
    p.step(m & (q > 0.72), 1)
    refl = m & (d < 10) & ~shift(m, 0, -10, True)
    p.step(refl, -1, lo=0)
    strokes = refl & (hash01(p.x // 6, p.y, seed + 1) < 0.25)
    p.step(strokes, 1)
    ripples(p, m, seed + 2, every=160)
    p.wet |= m
    p.hazard |= m
    p.walk &= ~m
    p.solid &= ~m


# --- buildings --------------------------------------------------------------------------------
def house_front(env, v, cw=None):
    """A front from the house kits (#121) as a kit sprite: its own colours mapped back to
    their ramps and tones, its foot at the middle of its base, its shadow thrown down and to
    the right, and its footprint a block for walkers (only its lowest 6 rows: the street
    passes in front of it)."""
    import house_kits as hk
    cv = hk.front(env, v, cw)
    sp = _from_canvas(cv)
    sp.fx, sp.fy = sp.w // 2, sp.h - 1
    block = sp.m & (sp.y >= sp.fy - 5)
    return sp, sp.thrown(0.4), block


def roof_behind(env, w, h, seed=0):
    """The roofs behind a front, seen from the south and above (house kits' roof_mass): a
    slate ridge for the old town's houses, a flat roof with its parapet and rooftop things for
    the newer fronts; the townscape that runs back from the street."""
    import house_kits as hk
    from pixel import Canvas
    cv = Canvas(w, h)
    kind, shape = {'valley': ('tiles', 'ridge'), 'neon': ('slate', 'flat'), 'cogsworth': ('slate', 'ridge')}.get(env, ('slate', 'ridge'))
    hk.roof_mass(cv, 0, 0, w, h, kind, shape, seed)
    sp = _from_canvas(cv)
    sp.fx, sp.fy = sp.w // 2, sp.h - 1
    return sp


# --- the composed sample: the Falls Rock corner ---------------------------------------------------
CW, CH = 640, 640


def corner_cells(seed=1):
    """The corner's tiers on the 8 px grid: the old town (3) on the Falls Rock across the
    north, its retaining wall jogging forward at a bastion; the high street (2) under it; the
    quay (1) one tier lower; the ria (0). The Glint's channel cuts down the east side."""
    rows, cols = CH // GRID, CW // GRID
    X, Y = np.meshgrid(np.arange(cols) * GRID + 4.0, np.arange(rows) * GRID + 4.0)
    y3 = np.where(X < 200, 184.0, np.where(X < 216, 184 + (X - 200), np.where(X < 360, 200.0,
                  np.where(X < 376, 200 - (X - 360), 184.0))))
    y3 = np.where((X > 420) & (X < 470), 216.0, y3)                       # the bastion over the stair street
    y2 = np.where(X < 300, 352.0, np.where(X < 316, 352 + (X - 300), 368.0))
    y1 = np.where(X < 120, 488.0, np.where(X < 136, 488 - (X - 120), 472.0))
    y1 = np.where(X > 470, 480.0, y1)
    C = np.zeros((rows, cols), np.int16)
    C[Y < y1] = 1
    C[Y < y2] = 2
    C[Y < y3] = 3
    return C


GRID = 8


def corner(seed=1):
    """The composed sample, 640 x 640: the Falls Rock corner of the old town. A row of fronts
    with their roofs running back on the old town's street of setts along the north; its retaining wall of
    weathered brick, 40 high, with a railing along the top, jogging forward at a bastion
    where a stair street comes down through it; the high street under it, pavements of
    flagstones with granite kerbs and tree pits either side of a worn road with a tram's
    rails; a ramp along the next wall down to the quay (setts, bollards, coils, fish boxes);
    the quay's sea wall into the ria, with a ladder and rings. Down the east side the Glint
    runs in its stone channel and falls down all three walls into the ria. Returns the plot
    and its parts."""
    C = corner_cells(seed)
    T = lattice(C, CW, CH)
    R = Relief(T, E_CITY)
    p = Plot(CW, CH, 'asphalt', 2)
    p.tier = R.seen().astype(np.int8)
    p.walk[:] = False
    tops = ~R.face
    old = tops & (T == 3)
    high = tops & (T == 2)
    quay = tops & (T == 1)
    ria = tops & (T == 0)
    gx0, gx1 = 576, 608                                        # the Glint's channel
    jog = np.where(T >= 3, 0, np.where(T == 2, -10, -4))         # each fall lands a little off the one above
    river = (p.x >= gx0 + jog) & (p.x < gx1 + jog)
    # --- the old town: a street of setts before a row of fronts ------------------------------
    setts(p, old & ~river, seed + 1, ramps=('stone_warm', 'ashlar', 'stone', 'ashlar_warm', 'stone_cool'))
    # --- the high street: pavements, kerbs, the road and the tram ----------------------------
    hs_top = np.nonzero(high.any(1))[0].min()
    pave_n = high & (p.y < np.where(p.x < 400, 236, 252)) & ~river
    road = high & ~pave_n & (p.y < 316) & ~river
    pave_s = high & ~pave_n & ~road & ~river
    flags(p, pave_n, seed + 2)
    flags(p, pave_s, seed + 3)
    asphalt(p, road, seed + 4)
    tram_rails(p, 268, 0, gx0, seed + 5)
    kerb(p, high & ~river & (p.y >= np.where(p.x < 400, 236, 252)) & (p.y < np.where(p.x < 400, 238, 254)), seed + 6)
    kerb(p, high & ~river & (p.y >= 314) & (p.y < 316), seed + 7)
    for x in (60, 220, 520):
        manhole(p, x, 296)
    for x in range(30, gx0 - 20, 90):
        gully(p, x, 309)
    for x in (40, 150, 260, 360, 500):
        tree_pit(p, x, 330 if x < 300 else 340, seed + x)
    # --- the quay ---------------------------------------------------------------------------
    flags(p, quay & ~river, seed + 8, course=10, ramps=('bleached', 'sand_cool', 'ashlar_warm', 'bleached_warm'))
    harbour(p, ria, seed + 9)
    # --- the walls ----------------------------------------------------------------------------
    wall3 = R.face & (R.kf == 3)
    wall2 = R.face & (R.kf == 2)
    wall1 = R.face & (R.kf == 1)
    brick_wall(p, R, wall3 & ~river, seed + 10)
    masonry(p, R, wall2 & ~river, seed + 11, ramps=('stone', 'stone_cool', 'slate', 'stone_warm'))
    masonry(p, R, wall1 & ~river, seed + 12, water=ria)
    bands(p, R, seed + 13, rocks=('ashlar', 'ashlar', 'ashlar_warm', 'ashlar_cool'))
    tier_shadows(p, R)
    # --- the ways -------------------------------------------------------------------------
    st = stair(p, R, 424, 40, seed + 20, k=3)                  # the stair street through the bastion
    ramp = ramp_along(p, R, 330, 470, 24, seed + 21, rising='east', k=2)
    stepped_tread(p, ramp, 'east', seed + 22)
    st2 = stair(p, R, 60, 40, seed + 23, k=1)                   # quay steps down to a landing stage
    railing(p, R, T == 3, seed + 24, gap=(p.x >= 420) & (p.x < 472))
    ys = np.nonzero(R.face[:, 80] & (R.kf[:, 80] == 1))[0]
    pont = ck.pier(p, 56, int(ys.max()) + 1, 108, int(ys.max()) + 26, seed + 25, legs=4)
    # --- the Glint and its falls --------------------------------------------------------------
    wat = np.zeros(p.f.shape, bool)
    fall = np.zeros(p.f.shape, bool)
    for tier, dx in ((3, 0), (2, -10), (1, -4)):
        band = (T == tier) & ~R.face
        ys = np.nonzero(band[:, gx0 + dx:gx1 + dx].any(1))[0]
        if len(ys):
            wat |= glint(p, gx0 + dx, gx1 + dx, int(ys.min()), int(ys.max()) + 1, seed + 30 + tier)
    for k, dx in ((3, 0), (2, -10), (1, -4)):
        col = (p.x >= gx0 + dx + 5) & (p.x < gx1 + dx - 3) & R.face & (R.kf == k)
        if col.any():
            fall |= cascade(p, R, gx0 + dx + 5, gx1 + dx - 3, seed + 31 + k, k=k)
    # the high street crosses the Glint on a stone bridge: a deck of setts between parapets
    bx0, bx1 = gx0 - 10 - 2, gx1 - 10 + 2
    deck = (p.x >= bx0) & (p.x < bx1) & (p.y >= 240) & (p.y < 316) & (T == 2)
    setts(p, deck, seed + 33, ramps=('stone', 'stone_warm', 'ashlar'), course=4)
    for py in (240, 314):
        par = (p.x >= bx0) & (p.x < bx1) & (p.y >= py) & (p.y < py + 3)
        p.put(par, 'ashlar_warm', 4)
        p.put(par & (p.y == py + 2), 'ashlar', 2)
        p.walk &= ~par
        p.solid |= par
    p.wet &= ~deck
    p.hazard &= ~deck
    p.walk |= deck & ~p.solid
    # --- the fronts on the old town's street --------------------------------------------------
    import house_kits as hk
    order = hk.street('neon', 7, seed=seed)
    x = 6
    fronts = []
    for i, (v, cw) in enumerate(order):
        env = 'neon' if i % 3 != 1 else 'valley'
        sp, sh, bl = house_front(env, v, cw)
        if x + sp.w // 2 > gx0 - 8:
            break
        foot = 132
        rb = roof_behind(env if env != 'neon' or i % 2 else 'cogsworth', sp.w - 2, max(8, foot - sp.h + 2), seed + i)
        paste(p, rb, x + sp.w // 2, foot - sp.h + 1, shadow=None, block=rb.m)
        paste(p, sp, x + sp.w // 2, foot, shadow=sh, block=bl)
        fronts.append((env, v, x))
        x += sp.w - 2 + (0 if hash01(i, 0, seed) < 0.6 else 10)
    # --- things on the quay ------------------------------------------------------------------
    for (mk, xx, yy, sd) in ((bollard, 120, 466, 1), (bollard, 300, 460, 2), (bollard, 470, 470, 3), (coil, 200, 456, 4),
                             (fish_crate, 380, 440, 5), (fish_crate, 394, 446, 6), (net_heap, 250, 420, 7)):
        if p.solid[yy, xx] or not quay[yy, xx]:
            continue
        sp_, sh_ = mk(sd)[:2]
        paste(p, sp_, xx, yy, shadow=sh_, block=sp_.m & (sp_.y > sp_.fy - 3))
    ck.ladder(p, R, 220, k=1, seed=seed + 40)
    for xx in (160, 340, 520):
        ys = np.nonzero(R.face[:, xx] & (R.kf[:, xx] == 1))[0]
        if len(ys):
            ck.ring(p, xx, int(ys.min()) + 8)
    parts = dict(R=R, T=T, old=old, high=high, quay=quay, ria=ria, stair=st | st2, ramp=ramp, river=wat, fall=fall, pontoon=pont,
                 fronts=fronts, hs_top=hs_top)
    return p, parts


# --- sheets, the bar, the checks ------------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
REFS = (
    ('Eastward: a street wall, steps and kerbs', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/'
     '977880/ss_5d50545b49db3a8502666b4195d2fabd0e31a29d.1920x1080.jpg', (0, 400, 1100, 1080), 162.0),
    ('Eastward: shopfronts and a stone footing', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/'
     '977880/ss_29d7dd0891c88b08d699556ed62fcc37f1aea47f.1920x1080.jpg', (0, 180, 1100, 700), 162.0),
    ('Eastward: a station, its platform and rails', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/'
     '977880/ss_bf8d65929d363f1b62f632d934eda94ef5188049.1920x1080.jpg', (0, 300, 1100, 1000), 162.0),
    ('Eastward: a canal\'s stone edge (Octopia)', 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/'
     '2305370/ss_f5788b1d4ade71e0cdb1e0110debfad3b32ca51c.1920x1080.jpg', (0, 640, 1100, 1080), 162.0),
)
CORNER_BOXES = (
    ((60, 190, 140, 222), 'stone-wall', 'the old town\'s brick retaining wall'),
    ((230, 330, 300, 366), 'stone-wall', 'the ashlar wall under the high street'),
    ((150, 480, 210, 512), 'stone-wall', 'the quay\'s sea wall'),
    ((20, 140, 180, 180), 'paving', 'the old town\'s setts'),
    ((40, 250, 140, 300), 'paving', 'the high street\'s road and rails'),
    ((150, 226, 230, 262), 'paving', 'the pavement and its kerb'),
    ((80, 400, 200, 450), 'paving', 'the quay\'s setts'),
    ((60, 540, 200, 620), 'water', 'the ria along the quay'),
    ((340, 270, 470, 314), 'stair', 'the ramp down to the quay'),
)


def corner_preview(p, scale=2, people=True):
    img = p.image().convert('RGBA')
    if people:
        for name, (x, y) in (('courier', (300, 250)), ('stroller', (120, 300)), ('vendor', (360, 150)),
                             ('docker', (260, 440)), ('porter', (440, 200))):
            path = os.path.join(ROOT, 'assets', 'residents', f'{name}-0.png')
            if os.path.exists(path):
                r = Image.open(path).convert('RGBA')
                r = r.resize((r.width // 4, r.height // 4), Image.NEAREST)
                img.alpha_composite(r, (x - r.width // 2, y - r.height))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def compare_sheet(p, scale=3, size=(200, 140)):
    """Corner crops beside Eastward's town screens (edges are compared with Eastward only,
    Matt 21 Oct), all at an adult of 25 px."""
    ours = corner_preview(p, 1)
    crops = [('ours: the old town\'s wall and its stair street', ours.crop((340, 120, 540, 260))),
             ('ours: the high street, its kerbs, rails and tree pits', ours.crop((60, 200, 260, 340))),
             ('ours: the ramp down to the quay', ours.crop((300, 300, 500, 440))),
             ('ours: the quay, its sea wall and the ria', ours.crop((60, 400, 260, 540))),
             ('ours: the Glint\'s falls', ours.crop((440, 120, 640, 260)))]
    refs = []
    for (name, url, box, adult) in REFS:
        im = ck.ref_image(url, box, adult)
        if im is not None:
            refs.append((name, im.crop((0, 0, min(im.width, size[0]), min(im.height, size[1])))))
    rows = max(len(crops), len(refs))
    cw, chh = size[0] * scale + 16, size[1] * scale + 30
    sheet = Image.new('RGB', (2 * cw + 16, rows * chh + 40), (46, 40, 52))
    _label(sheet, 'Ours (left) and Eastward (right), all at an adult of 25 px, shown at 3x', (10, 10), (250, 214, 140))
    for i, (name, im) in enumerate(crops):
        sheet.paste(im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST), (10, 36 + i * chh))
        _label(sheet, name, (10, 36 + i * chh + im.height * scale + 2))
    for i, (name, im) in enumerate(refs):
        sheet.paste(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (cw + 16, 36 + i * chh))
        _label(sheet, name, (cw + 16, 36 + i * chh + im.height * scale + 2))
    return sheet


def check(p=None, parts=None) -> list:
    """The kit's contracts on the corner: from the old town's street a walker reaches the
    high street only by the stair street, the quay only by the ramp, and the landing stage
    by the quay steps; no wall is walkable outside them; the river, its falls and the ria
    stop a walker; the stairs are 40 open and the ramp 24 wide or more."""
    faults = []
    if p is None:
        p, parts = corner()
    R = parts['R']
    a = (300, 150)
    for name, b in (('the high street', (200, 290)), ('the quay', (300, 420)), ('the landing stage', (82, 512))):
        if not p.walk[a[1], a[0]] or not p.walk[b[1], b[0]]:
            faults.append(f'{name}: an end is not walkable ({bool(p.walk[a[1], a[0]])}, {bool(p.walk[b[1], b[0]])})')
        elif not _reaches(p.walk, a, b):
            faults.append(f'{name} cannot be reached from the old town')
    ways = parts['stair'] | parts['ramp']
    bad = p.walk & R.face & ~ways
    if bad.any():
        ys, xs = np.nonzero(bad)
        faults.append(f'{int(bad.sum())} wall pixels outside the stairs and ramp are walkable (e.g. {xs[0]}, {ys[0]})')
    wet = p.walk & (p.wet | p.hazard) & ~parts['pontoon']
    if wet.any():
        ys, xs = np.nonzero(wet)
        faults.append(f'{int(len(ys))} water pixels are walkable (e.g. {xs[0]}, {ys[0]})')
    cols = parts['ramp'].sum(0)
    if parts['ramp'].any() and np.median(cols[cols > 0]) < 20:
        faults.append('the ramp is narrower than 24 px on screen')
    return faults


def _flat(w, h, fn, seed=0, **kw):
    q = Plot(w, h, 'asphalt', 2)
    m = np.ones((h, w), bool)
    fn(q, m, seed, **kw)
    return q


def _wall_piece(kind='brick', seed=5):
    rows = ['1111111111111111111111'] * 5 + ['0000000000000000000000'] * 6
    C = np.array([[int(ch) for ch in r] for r in rows], np.int16)
    T = lattice(C)
    R = Relief(T, [0, 40])
    q = Plot(T.shape[1], T.shape[0], 'asphalt', 2)
    top, low = ~R.face & (T == 1), ~R.face & (T == 0)
    setts(q, top, seed)
    flags(q, low, seed + 1)
    if kind == 'brick':
        brick_wall(q, R, R.face, seed + 2)
    else:
        masonry(q, R, R.face, seed + 2)
    railing(q, R, T == 1, seed + 3)
    tier_shadows(q, R)
    stair(q, R, 60, 40, seed + 4, k=1)
    return q, R


def pieces():
    out = []
    q, R = _wall_piece('brick', 5)
    out.append(('built', 'a 40 px retaining wall in weathered brick, pilasters, coping, railing, a stair street', q,
                [((12, 48, 58, 80), 'stone-wall')]))
    q, R = _wall_piece('ashlar', 6)
    out.append(('built', 'the same in dressed ashlar', q, [((12, 48, 58, 80), 'stone-wall')]))
    q = _flat(160, 90, asphalt, 7)
    tram_rails(q, 40, 0, 160, 8)
    manhole(q, 30, 20)
    gully(q, 100, 80)
    out.append(('ground', 'a worn road: patches, sealed cracks, wheel tracks, oil, paint; tram rails, a manhole, a gully',
                q, [((8, 8, 80, 60), 'paving')]))
    q = _flat(140, 80, flags, 9)
    tree_pit(q, 70, 40, 9)
    kerb(q, (q.y >= 74) & (q.y < 76), 10)
    out.append(('ground', 'pavement flagstones, a kerb, a tree pit', q, [((8, 6, 80, 60), 'paving')]))
    return out


def main(argv):
    if '--check' in argv:
        faults = check()
        for f in faults:
            print('FAULT:', f)
        print('city_kit check:', 'pass' if not faults else f'{len(faults)} faults')
        return 1 if faults else 0
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-city-kit')
    os.makedirs(out, exist_ok=True)
    p, parts = corner()
    p.image().save(os.path.join(out, 'corner.png'))
    corner_preview(p, 2).save(os.path.join(out, 'corner-2x.png'))
    ck.night(corner_preview(p, 1)).resize((p.w * 2, p.h * 2), Image.NEAREST).save(os.path.join(out, 'corner-night.png'))
    frames, box = ck.flow_frames(p)
    if box is not None:
        crop = (400, 100, 640, 640)
        fr = [f.crop(crop).resize(((crop[2] - crop[0]) * 2, (crop[3] - crop[1]) * 2), Image.NEAREST) for f in frames]
        fr[0].save(os.path.join(out, 'corner-flow.gif'), save_all=True, append_images=fr[1:], duration=150, loop=0)
    print('corner boxes:')
    for box, kind, what in CORNER_BOXES:
        c, strict, ramp, line = bar_line(p.image(), box, kind)
        print(f'  {what:46s} {line}  isolated {c["isolated"]:.3f} cluster {c["cluster"]:.1f}')
    compare_sheet(p).save(os.path.join(out, 'compare.png'))
    sheet, rows = ck.kit_sheet(pieces(), groups=['built', 'ground'],
                               titles={'built': 'Built: retaining walls of 40 in brick and ashlar, railings, a stair street',
                                       'ground': 'Ground: the road, its rails and fittings; pavements and kerbs'})
    sheet.save(os.path.join(out, 'kit-sheet.png'))
    for name, kind, c, strict, ramp in rows:
        print(f'  {name[:60]:60s} {kind:10s} t{c["tones"]:5.1f} s{c["shapes"]:5.1f} d{c["dressing"]:5.1f} '
              f'iso {c["isolated"]:.3f} cl {c["cluster"]:.1f}  {"PASS" if strict else "PASS@85" if ramp else "FAIL"}')
    faults = check(p, parts)
    print('check:', 'pass' if not faults else '; '.join(faults))
    print('wrote', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
