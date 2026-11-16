"""The library's bell cupola and its bell (Matt, 13 Nov, decision (d): "the bell tower is optional, and
its cupola is drawn, so that paying visibly changes the square"; docs/vision/decisions-2026-11-13.md).

Three pictures, drawn in the frame of the library's own picture (`town.build` places them on the
library's foot, the cupolas three texels in front of it and their shadow two, so they sort with the
building over its damage overlay):

- `cupola(..., hung=False)`: the storm's state. The bell is gone (it lies in the street below; the bell
  look line in game/data/dialogue/crossroads.json), the old oak headstock snapped: one half still in the
  west side of the arch, hanging down at an angle with its splintered end and a strap; the frame's iron
  brackets empty on the far posts; pigeons nesting in the west corner of the bare floor.
- `cupola(..., hung=True)`: after the restore (`bell_tower`, 50 Glint): the bell back in a new frame (a
  fresh-sawn headstock across the arch, iron straps down to the canons, the bronze bell), its rope down
  to the floor's hatch.
- the cast shadow on the roof, the same for both: the roof's own codes (the library's, with its damage
  overlay over them) a tone down, two in its core, east and down of the cupola by the one sun.

The two cupolas share their outline and every texel outside the arch except the storm's marks on the
empty one, which lie inside that outline (town.build checks the outlines match): four slates gone from
the base's west half over dark battens, one slipped; the flashing's low west corner lifted as a flap;
a dent in the dome's lit side. Paying hangs the bell and mends those. The
cupola itself: a base of hung slate astride the ridge (courses 4 texels deep, slates 5 to 7 wide with
staggered joints, the head of each lit on its west, its butt turning under over the course's underline, the library roof's slate ramp, one clump of moss), its
lead flashing down the two slopes (a lit lip on the west arm only, the east arm deeper over a slate
drip line) and a lead ledge on top; an open belfry of painted
upright boards (weathered along the grain, nailed to a frieze board) between two bare oak corner posts
(grain, pegs, a capital and a plinth block each), a round arch with its voussoirs and keystone, a sill
rail; the far wall in the shade, the floor near the sill in some light; a moulded cornice in lengths over
dentils; a low lead dome on twelve rolls, each a meridian to the boss, lit on its west edge on the lit
half and dark on its east, the sheets between in the lead's middle tones (2 lit, 1 turning, 0 shade) with
the core shadow right of centre in the slate's deep blue and a reflected east rim, every other sheet
weathered to the slate's ramp at about the same lightness, two laps with iron clips where they cross the
rolls, three bloom runs under the lower lap and one small glint high on the west; a brass ball, and on
the rod an arrow vane pivoted about 40 % from its head: a sharp head pointing west and a swallowtail
flag at its east end, the bigger mass. Lead is the snow_cool ramp held to its middle tones (LEAD).
Lit from the upper left, every part with its thickness.

`bell_fallen(w, h, seed)`: the same bell, from the same profile (bell_profile: canons, a 13 wide shoulder,
the waist, the flare to a 24 wide lip, all at 1:1), on its side in the street where it came down, its
axis 50 degrees off the horizontal, the crown and the headstock's stub to the north-west, the mouth to
the south-south-east.

Sizes (world px, `q` makes texels; docs/vision/size-guide.md: a bell turret stands 32 to 64 over a
chapel's ridge, a landmark; this is a library's small cupola): the base 16 wide, 5 high at the ridge;
the belfry 15; the dome 5 over its foot. The bell 23 texels from canons to lip and 24 across the lip
(about 0.55 m: a small cupola's bell, 0.31 A).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

from . import village as V
from .palette import step

q, code, fill, Pic, finish, grid, paint, lam, bar = V.q, V.code, V.fill, V.Pic, V.finish, V.grid, V.paint, V.lam, V.bar

PAD = 160            # texels added above the building's picture: the cupola stands over its top row
CAST = (0.46, 0.22)  # game/data/sun.json `cast`: a texel h above the ground lands this far east and south


def _tri(X, Y, p0, p1, p2):
    """Inside the triangle p0 p1 p2 (texel centres)."""
    def side(a, b):
        return (X - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (Y - b[1])
    d1, d2, d3 = side(p0, p1), side(p1, p2), side(p2, p0)
    neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
    pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    return ~(neg & pos)


def _marks(a, m, rng, n, fam_dark, fam_lit=None, length=(2, 4), vertical=False):
    """Wear in clusters of two texels or more, tied to the material: `n` short marks inside m, each a
    run a tone down (a crack in the paint, a seam, a stain) with a lit texel pair over its west end
    when `fam_lit` is given (the lip that catches the light)."""
    ys, xs = np.nonzero(m)
    if ys.size == 0:
        return
    for _ in range(n):
        i = int(rng.integers(0, ys.size))
        y, x = int(ys[i]), int(xs[i])
        L_ = int(rng.integers(length[0], length[1] + 1))
        for j in range(L_):
            yy, xx = (y + j, x) if vertical else (y, x + j)
            if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and m[yy, xx] and a[yy, xx] >= 0:
                a[yy, xx] = np.maximum((a[yy, xx] // 8) * 8, a[yy, xx] - 1) if fam_dark is None else code(*fam_dark)
        if fam_lit is not None:
            yy, xx = (y, x - 1) if vertical else (y - 1, x)
            for j in range(2):
                y2, x2 = (yy + j, xx) if vertical else (yy, xx + j)
                if 0 <= y2 < a.shape[0] and 0 <= x2 < a.shape[1] and m[y2, x2] and a[y2, x2] >= 0:
                    a[y2, x2] = code(*fam_lit)


def geometry(info: dict, depth_world: float, spec: dict) -> dict:
    """Where the cupola stands on a front-gable roof (houses.gable_roof's info['gable']), in the
    building picture's texels: the ridge's centre column, the slope's fall per texel across it, how
    much a world px of depth rises on the roof, and the parts' lines."""
    g = info['gable']
    xc = float(g['xc'])
    ys, _xs = np.nonzero(g['ridge'])
    back, apex = int(ys.min()), int(g['y_apex'])
    k = (apex - back) / max(1.0, q(depth_world))                    # texels of rise per texel of depth
    off = np.asarray(g['off'], float)
    hw = q(spec.get('w', 16) / 2.0)
    ci = int(round(xc))
    sl = (off[ci] - off[ci - hw]) / hw                              # the slope's fall per texel from the ridge
    s0 = spec.get('at', 0.55)                                       # how far back along the ridge (0 front, 1 back)
    yR = apex - s0 * (apex - back)
    G = dict(cx=xc, k=k, sl=sl, hw=hw, yR=yR)
    G['hdp'] = hw * k                                               # half its depth, as the roof shows it
    G['yfb0'] = yR + G['hdp']                                       # the base's front foot at the ridge
    G['yft'] = G['yfb0'] - q(spec.get('base_h', 5))                 # the base's top front arris
    G['ledge'] = max(2, int(round(q(1.2) * k)))
    G['hwb'] = hw - q(1)                                            # the belfry, set in from the base
    G['ybb'] = G['yft'] - G['ledge']                                # the belfry's foot
    G['ybt'] = G['ybb'] - q(spec.get('belfry_h', 15))               # its top
    G['hwc'] = hw + q(0.6)                                          # the cornice
    G['corn'] = q(1.7)
    G['hwr'] = hw - q(0.4)                                          # the dome's foot
    G['yce'] = G['ybt'] - G['corn'] + q(0.7)
    G['cap_h'] = q(spec.get('cap_h', 5))                             # the dome's height over its foot
    G['pw'] = q(2.3)                                                # a corner post
    G['sill'] = q(1.7)
    G['r'] = G['hwb'] - G['pw']                                     # the arch's radius: the opening's half width
    G['crown'] = G['ybt'] + q(1.6)                                  # the arch's crown
    G['spring'] = G['crown'] + G['r']
    return G


LEAD = 'snow_cool'   # the lead of the dome, its rolls and the flashing: a pale blue-white ramp, apart from the slate


def bell_profile():
    """The one bell, at 1:1 in texels (the hung bell and the bell in the street are drawn from it): the
    canons on the crown, the crown rounding to a 13 wide shoulder, the waist, the flare to a 24 wide lip.
    Returns (rows, half): rows from the top of the canons, the half width at each row (0 above the body),
    and the row where the body starts (under the canons)."""
    canon_h, body_h = 3, 20
    half = []
    for r in range(canon_h):
        half.append(2.0)                                           # the canons, a loop 4 wide
    for r in range(body_h):
        t = r / (body_h - 1)
        h = 6.5 + 0.5 * math.sin(math.pi * t) + 5.25 * t ** 3      # shoulder 13, waist, lip 24
        if r == 0:
            h -= 2.0                                               # the crown rounding over the shoulder
        elif r == 1:
            h -= 0.8
        half.append(h)
    return canon_h + body_h, np.array(half), canon_h


def bell_bands(u):
    """The bronze across the bell's form in clean bands (west rim, lit band, body, core shadow, the east
    rim's bounce), u -1 (west) .. 1 (east)."""
    t = np.full(np.shape(u), 3.0)
    t = np.where(u < -0.55, 3.0, t)
    t = np.where((u >= -0.55) & (u < -0.1), 4.0, t)
    t = np.where((u >= -0.1) & (u < 0.3), 3.0, t)
    t = np.where((u >= 0.3) & (u < 0.82), 1.0, t)
    t = np.where(u >= 0.82, 2.0, t)
    return t


BRONZE = ('timber_warm', 'brass', 'brass')
BANDS = (8, 15)      # the two cast bands, rows of the body from the crown (the waist, and over the soundbow)


def cupola(base: np.ndarray, damage, info: dict, depth_world: float, spec: dict, hung: bool, seed: int, debug=None):
    """The cupola on the building whose picture codes are `base` (and its damage overlay's, `damage`,
    or None), and its cast shadow on the roof: two Pics the width of the building's picture and PAD
    texels taller, their rows offset by PAD (row PAD is the building's row 0), anchor (0, 0), and the
    geometry. town.build crops them and sets their feet. The shadow is the roof's own codes (the
    library's, with its damage overlay over them) a tone down, two in its core.

    The two states share their outline and every texel outside the arch except the storm's marks on the
    empty one (slates gone from the base, a lifted corner of the flashing, a dent in the dome), which
    all lie inside that outline: so one shadow serves both, and paying swaps
    what hangs in the arch and mends the marks. Each part draws from its own random stream, so the
    outside does not change with what hangs inside."""
    G = geometry(info, depth_world, spec)

    def rs(k):
        return np.random.default_rng(seed * 1000 + k)
    Hb, Wb = base.shape
    a = np.full((Hb + PAD, Wb), -1, np.int32)
    Yp, X = grid(a)
    Y = Yp - PAD                                                    # the building's own rows
    cx, k, sl, hw = G['cx'], G['k'], G['sl'], G['hw']
    dxa = np.abs(X - cx)
    Xi, Yi = np.floor(X).astype(int), np.floor(Y).astype(int)

    # --- the base: hung slate astride the ridge ----------------------------------------------------
    # courses 4 texels deep, slates 5 to 7 wide with staggered joints, each course's butt a dark
    # underline; the library roof's own slate ramp, lit to the west, turning away to the east
    rng = rs(1)
    yfb = G['yfb0'] + sl * dxa                                      # its foot down the two slopes
    bm = (dxa <= hw) & (Y >= G['yft']) & (Y < yfb)
    y0 = int(math.floor(G['yft']))
    t = np.zeros(a.shape)
    fam = np.full(a.shape, 'slate', dtype=object)
    x0, x1 = int(cx - hw) - 1, int(cx + hw) + 2
    for ci, cy in enumerate(range(y0, int(G['yfb0'] + sl * hw) + 2, 4)):
        xs = x0 - int(rng.integers(0, 6))
        n_ = 0
        while xs < x1:
            w_ = int(rng.integers(5, 8))
            mid = xs + w_ / 2.0
            ts = 3 if mid < cx + hw * 0.35 else 2                  # lit to the west, turning away to the east
            sib = 'slate_warm' if (n_ + ci) % 3 == 2 else 'slate'  # every third a sibling at the same lightness
            sel = bm & (Xi >= xs) & (Xi < xs + w_) & (Yi >= cy) & (Yi < cy + 3)
            t[sel] = ts
            fam[sel] = sib
            t[sel & (Yi == cy + 2)] = ts - 1                      # its butt turning under, over the underline
            head = sel & (Yi == cy) & (Xi < xs + 3) & (Xi > xs)  # its lit head: the west 2 texels of its top row
            t[head] = ts + 1
            j_ = bm & (Xi == xs) & (Yi >= cy) & (Yi < cy + 3)      # the joint at its west edge
            t[j_] = 1
            fam[j_] = 'slate'
            xs += w_
            n_ += 1
        ul = bm & (Yi == cy + 3)                                   # the course's underline
        t[ul] = 1
        fam[ul] = 'slate_cool'
    for f_ in ('slate', 'slate_warm', 'slate_cool'):
        m_ = bm & (fam == f_)
        paint(a, m_, f_, np.clip(t, 0, 5))
    # moss: one clump over the flashing at the low west corner
    mx_, my_ = int(cx - hw + 3), int(G['yfb0'] + sl * (hw - 3)) - 3
    moss = bm & (np.abs(Xi - mx_) <= 1) & (Yi >= my_) & (Yi < my_ + 2)
    paint(a, moss, ('leaf_cool', 'leaf', 'leaf'), np.where(Yi == my_, 3, 2))
    # the lead flashing down both slopes under it: its body in shade, a lit lip on the west arm only,
    # the east arm a tone deeper, a slate drip line under it
    fl = (dxa <= hw + 1) & (Y >= yfb - q(1.0)) & (Y < yfb + 1)
    lip = Yi == np.floor(yfb - q(1.0)).astype(int)
    a[fl] = code(LEAD, 1)
    a[fl & (X > cx)] = code(LEAD, 0)
    a[fl & lip & (X < cx - 1)] = code(LEAD, 3)
    a[fl & (Y >= yfb)] = code('slate_cool', 1)
    # its top: a lead ledge, the top plane, its front edge in shade
    ledge = (dxa <= hw) & (Y >= G['ybb']) & (Y < G['yft'])
    a[ledge] = code(LEAD, 2)
    a[ledge & (X > cx + hw * 0.35)] = code(LEAD, 1)                    # its east end turning from the light
    a[ledge & (X < cx - hw * 0.35)] = code(LEAD, 3)                    # its west end in the light (three planes)
    a[(dxa <= hw) & (Yi == int(G['yft']))] = code(LEAD, 0)

    # --- the belfry: two corner posts, a round arch between them, a sill rail ----------------------
    rng = rs(2)
    hwb, pw, r = G['hwb'], G['pw'], G['r']
    ybt, ybb = G['ybt'], G['ybb']
    face = (dxa <= hwb) & (Y >= ybt) & (Y < ybb)
    yspr = G['spring']
    dyc = np.maximum(0.0, yspr - Y)
    arch_half = np.sqrt(np.clip(r * r - dyc * dyc, 0, None))
    opening = face & (dxa < arch_half) & (Y >= G['crown']) & (Y < ybb - G['sill'])
    boards = face & ~opening
    # painted boards, upright, lit west of each joint; the east a tone down
    bj = q(2.2)
    col = np.floor((X - (cx - hwb)) / bj).astype(int)
    jx = (X - (cx - hwb)) / bj - col
    t = 3.4 + rng.uniform(-0.3, 0.3, 64)[col % 64]
    t = np.where(jx < 1.0 / bj, t - 1.4, t)
    t = np.where((jx >= 1.0 / bj) & (jx < 2.0 / bj), t + 0.7, t)
    t = t + 0.6 * (X < cx - hwb + pw) - 1.1 * (X > cx + hwb - pw) - 0.5 * (X > cx + r * 0.4)
    paint(a, boards, ('plaster', 'plaster', 'plaster_warm'), t)
    _marks(a, boards & (jx >= 2.0 / bj), rng, 34, None, ('plaster_warm', 5), length=(2, 3), vertical=True)
    fz0, fz1 = ybt + q(1.0), ybt + q(2.3)
    frz = boards & (Y >= fz0) & (Y < fz1) & (dxa < hwb - pw)
    paint(a, frz, ('plaster', 'plaster', 'plaster_warm'), 3.6 + 1.1 * (Y < fz0 + 1) - 1.6 * (Y >= fz1 - 1) - 1.0 * (X > cx + r * 0.4))
    _marks(a, frz & (Y >= fz0 + 1) & (Y < fz1 - 1), rng, 5, None, None, length=(2, 3))
    for nyy in (ybt + q(2.6), ybb - G['sill'] - q(1.6)):
        for cc in range(int(2 * hwb / bj) + 1):
            nx_ = int(cx - hwb + cc * bj + bj * 0.55)
            ny_ = int(nyy) + PAD
            if 0 <= ny_ < a.shape[0] - 1 and boards[ny_, nx_] and boards[ny_ + 1, nx_ + 1]:
                a[ny_:ny_ + 2, nx_:nx_ + 2] = code('iron', 2)
                a[ny_, nx_] = code('iron', 4)
    oak = ('timber_cool', 'timber', 'timber_warm')
    for x0p in (cx - hwb, cx + hwb - pw):
        pm = face & (X >= x0p) & (X < x0p + pw)
        tp = 3.2 - 1.2 * (x0p > cx)
        paint(a, pm, oak, tp + 1.3 * (X < x0p + 1) - 1.5 * (X >= x0p + pw - 1) + 0.4 * (X < x0p + 2))
        _marks(a, pm & (X > x0p + 1) & (X < x0p + pw - 1), rng, 15, None, None, length=(3, 6), vertical=True)
        _marks(a, pm & (X > x0p) & (X < x0p + 3), rng, 4, None, ('timber_warm', 5), length=(2, 3), vertical=True)
        for (yy0, hh) in ((ybt + q(0.9), q(1.3)), (ybb - q(1.6), q(1.6))):              # a capital and a plinth block
            cb = (X >= x0p - 1) & (X < x0p + pw + 1) & (Y >= yy0) & (Y < yy0 + hh) & (dxa <= hwb + 1)
            paint(a, cb, oak, tp + 0.5 + 1.2 * (Y < yy0 + 1) - 1.6 * (Y >= yy0 + hh - 1) - 0.8 * (X >= x0p + pw))
        for py_ in (ybt + q(3.0), ybb - q(3.0)):                                          # the pegs
            pg = (X >= x0p + q(0.8)) & (X < x0p + q(0.8) + 2) & (Y >= py_) & (Y < py_ + 2) & pm
            a[pg] = code('timber', 1)
            a[pg & (Xi == int(x0p + q(0.8))) & (Yi == int(py_))] = code('timber_warm', 4)
    # the arch's trim: a moulded band round the opening, lit on its lower west curve, shaded east
    ring = face & ~opening & (dxa < arch_half + q(0.9)) & (Y >= G['crown'] - q(0.9)) & (Y < ybb - G['sill'])
    ang = np.arctan2(Y - yspr, X - cx)
    paint(a, ring, ('plaster', 'plaster', 'plaster_warm'), 4.2 - 1.6 * (X > cx + 1) + 0.6 * (np.sin(ang) < -0.5) * (X < cx))
    # its voussoirs: radial joints, a tone down in the light and two down on the east half
    vf = ((ang + math.pi) / (math.pi / 9)) % 1.0
    vj = ring & (Y < yspr) & (vf < 0.16)
    dv = np.where(X > cx, 2, 1)
    a[vj] = np.maximum((a[vj] // 8) * 8, a[vj] - dv[vj])
    ks = face & (dxa < q(1.0) + (G['crown'] - Y) * 0.25) & (Y >= G['crown'] - q(2.0)) & (Y < G['crown'] + 1)
    paint(a, ks, ('plaster', 'plaster', 'plaster_warm'), 4.4 - 1.5 * (X > cx) + 0.6 * (Y < G['crown'] - q(2.0) + 1))
    sr = face & (dxa < hwb - 1) & (Y >= ybb - G['sill']) & (Y < ybb - G['sill'] + q(1.0))
    paint(a, sr, ('timber_cool', 'timber', 'timber_warm'), 3.3 + 1.2 * (Y < ybb - G['sill'] + 1) - 0.9 * (X > cx + r * 0.5))

    # --- inside the arch: the floor in the cap's shade, the far wall, the far posts ----------------
    rng = rs(3)
    inner = opening
    dep = (ybb - G['sill'] - Y) / max(1.0, (ybb - G['sill']) - G['crown'])    # 0 at the sill, 1 at the crown
    fb = q(1.6)
    plank = np.floor((Y - G['crown']) / fb).astype(int)
    pj = ((Y - G['crown']) / fb - plank) < 1.0 / fb
    near = dep < 0.3
    tin = np.where(near, 2.4 - 3.0 * dep - 0.7 * pj + rng.uniform(-0.25, 0.25, 64)[plank % 64], 0.6 - 0.4 * dep)
    tin = tin - 0.5 * (X > cx + r * 0.3) + 0.5 * (X < cx - r * 0.4) * near
    paint(a, inner, ('soot', 'timber_cool', 'timber'), tin, lo=0, hi=3)
    far = inner & ~near
    fbj = q(2.0)
    fcol = np.floor((X - (cx - r)) / fbj).astype(int)
    fjx = (X - (cx - r)) / fbj - fcol
    tf = 1.4 + rng.uniform(-0.3, 0.3, 64)[fcol % 64] - 1.0 * (fjx < 1.0 / fbj) + 0.6 * ((fjx >= 1.0 / fbj) & (fjx < 2.0 / fbj))
    tf = tf - 0.8 * (Y < G['crown'] + q(2.6)) - 0.6 * (X > cx + arch_half - q(1.6))
    paint(a, far, ('soot', 'soot', 'timber_cool'), tf, lo=0, hi=3)
    a[inner & (Y < G['crown'] + q(1.0))] = code('soot', 0)
    for bx_ in (cx - r + q(1.2), cx + r - q(1.2) - q(1.0)):                     # the frame's iron brackets
        brk = inner & (X >= bx_) & (X < bx_ + q(1.0)) & (Y >= G['crown'] + q(2.0)) & (Y < G['crown'] + q(3.6))
        paint(a, brk, 'iron', 2.2 + 1.2 * (Y < G['crown'] + q(2.0) + 1) - 0.8 * (bx_ > cx))
    # the trap hatch the bell rope comes up through, east of the bell's lip, its lit far edge
    hx0, hy0 = cx + q(3.2), ybb - G['sill'] - q(2.4)
    hatch = inner & (X >= hx0) & (X < cx + r - 1) & (Y >= hy0) & (Y < hy0 + q(1.5))
    paint(a, hatch, 'soot', 0.3 + 1.4 * (Y < hy0 + 1))
    _marks(a, inner & near & ~hatch, rng, 8, None, ('timber', 3), length=(2, 3))
    for sx, w_ in ((cx - r, q(1.2)), (cx + r - q(1.2), q(1.2))):
        fp = inner & (X >= sx) & (X < sx + w_) & (Y < ybb - G['sill'] - q(3.0))
        paint(a, fp, 'soot', 2.4 - 0.8 * (sx > cx))

    hang = np.zeros(a.shape, bool)
    if hung:
        rng = rs(4)
        # the rope first, behind the bell: from the headstock's east end straight down into the hatch,
        # two texels wide, lit on its west, its knot at the hatch
        hy0h, hy1h = G['crown'] + q(0.7), G['crown'] + q(2.2)
        rx = int(hx0 + (cx + r - 1 - hx0) / 2.0) - 1
        rope = inner & (Xi >= rx) & (Xi < rx + 2) & (Y >= hy1h) & (Y < hy0 + 1)
        paint(a, rope, 'sand', np.where(Xi == rx, 4, 2))
        a[inner & (Xi >= rx - 1) & (Xi < rx + 3) & (Yi == int(hy0) - 1)] = code('sand', 3)
        hang |= rope
        # the new frame: a fresh-sawn headstock across under the crown, its iron straps
        hs = inner & (Y >= hy0h) & (Y < hy1h)
        paint(a, hs, ('timber', 'timber_warm', 'timber_warm'), 3.3 + 1.3 * (Y < hy0h + 1) - 1.4 * (Y >= hy1h - 1) - 0.8 * (X > cx + r * 0.5))
        for gx in (cx - q(3.4), cx + q(2.6)):
            a[hs & (np.abs(X - gx) < 1.0)] = code('timber_warm', 2)
        hang |= hs
        # the bell, from the one profile: canons up into the headstock, the body in clean bands
        rows, half, cr = bell_profile()
        bt = int(hy1h) - 1
        bell = np.zeros(a.shape, bool)
        tb = np.zeros(a.shape)
        canon = np.zeros(a.shape, bool)
        for i in range(rows):
            yy = bt + i + PAD
            if yy >= a.shape[0]:
                break
            row_x = X[yy] - cx
            u = row_x / half[i]
            m_ = np.abs(u) <= 1
            if i < cr:
                canon[yy] = m_
                continue
            bell[yy] = m_
            tb[yy] = bell_bands(u)
        bell &= inner
        rb = Yi - bt                                                        # the row in the profile
        tb = np.where(rb == cr, tb + 1, tb)                                 # the crown turned up to the light
        for band in (cr + BANDS[0], cr + BANDS[1]):
            tb = np.where(rb == band, np.maximum(0, tb - 2), tb)            # two cast bands round it
        tb = np.where(rb == rows - 2, np.minimum(4, tb + 1), tb)            # the soundbow's lit roll
        tb = np.where(rb == rows - 1, np.maximum(0, tb - 1), tb)            # the lip's under edge
        paint(a, bell, BRONZE, tb, lo=0, hi=4)
        paint(a, canon & inner, 'iron', np.where(X < cx, 3.4, 1.8))
        hang |= bell | canon
    else:
        rng = rs(5)
        # pigeons have moved in: a nest of twigs 7 x 4 in the west corner of the bare floor, its twigs in
        # three tones of timber, three lit ends sticking out at odd angles, a dark cup on top
        nx0, ny0 = int(cx - r + q(1.0)), int(ybb - G['sill'] - q(1.8))
        nest = inner & (Xi >= nx0) & (Xi < nx0 + 7) & (Yi >= ny0) & (Yi < ny0 + 4)
        nest &= ~(((Xi == nx0) | (Xi == nx0 + 6)) & (Yi == ny0))             # rounded top corners
        tw = np.array([2, 3, 3, 1])[(Xi * 2 + Yi * 3) % 4]                   # twigs laid across in three tones
        a[nest] = (V.FI['timber'] * 8 + tw)[nest]
        for (ex, ey) in ((nx0 - 1, ny0 + 1), (nx0 + 7, ny0 + 2), (nx0 + 5, ny0 - 1)):
            if 0 <= ey + PAD < a.shape[0] and inner[ey + PAD, ex]:
                a[ey + PAD, ex] = code('timber_warm', 4)
                nest[ey + PAD, ex] = True
        a[(Yi == ny0) & (Xi >= nx0 + 2) & (Xi < nx0 + 5) & inner] = code('soot', 0)
        hang |= nest
        # the old headstock, snapped: its west half still in the arch's west side, hanging down to the
        # east, its splintered end lit against the floor darkened round it; a strap dangling from it
        x0b, y0b = cx - r + 1, G['crown'] + q(3.0)
        x1b, y1b = cx + q(1.6), G['crown'] + q(7.6)
        dark_round = inner & (((X - x1b) / q(3.0)) ** 2 + ((Y - y1b) / q(2.4)) ** 2 <= 1)
        a[dark_round] = np.maximum((a[dark_round] // 8) * 8, a[dark_round] - 1)
        hb = bar(a, x0b, y0b + PAD, x1b, y1b + PAD, q(1.0), 'timber', 3, where=inner)
        hb &= inner
        ux, uy = (x1b - x0b), (y1b - y0b)
        L_ = math.hypot(ux, uy)
        along_ = ((X - x0b) * ux + (Y - y0b) * uy) / L_
        acr = (-(X - x0b) * uy + (Y - y0b) * ux) / L_
        tt = 3.0 + 1.3 * (acr < -q(0.4)) - 1.2 * (acr > q(0.45)) - 0.5 * (along_ > L_ * 0.6)
        paint(a, hb, ('timber_cool', 'timber', 'timber_warm'), tt)
        # the break: three jagged fibres sticking out along the grain, lit, a dark split between them
        brk = hb & (along_ > L_ - 2.0)
        a[brk] = code('timber', 1)
        ex, ey = x1b, y1b
        for k2, (off_, ln) in enumerate(((-1.4, 3), (0.0, 2), (1.3, 4))):
            for j2 in range(ln):
                xx = int(round(ex + ux / L_ * j2 - uy / L_ * off_))
                yy = int(round(ey + uy / L_ * j2 + ux / L_ * off_)) + PAD
                if 0 <= yy < a.shape[0] and inner[yy, xx]:
                    a[yy, xx] = code('timber_warm', 4)
                    hb[yy, xx] = True
        split = hb & (np.abs(acr) < 0.6) & (along_ > L_ - q(1.6))
        a[split] = code('soot', 1)
        sx0 = x0b + (x1b - x0b) * 0.62
        sy0 = y0b + (y1b - y0b) * 0.62 + 1
        st = inner & (X >= sx0) & (X < sx0 + 2) & (Y >= sy0) & (Y < sy0 + q(3.4))
        a[st] = code('iron', 2)
        a[inner & (X >= sx0) & (X < sx0 + 2) & (Yi == int(sy0 + q(3.4)))] = code('iron', 4)
        hang |= hb | st
    if hang.any():
        sh = np.zeros(a.shape, bool)
        sh[2:, 3:] = hang[:-2, :-3]
        sh &= inner & ~hang & (Y > G['crown'] + q(2.2))
        a[sh] = np.where(a[sh] % 8 > 0, a[sh] - 1, a[sh])

    # --- the cornice -------------------------------------------------------------------------------
    rng = rs(6)
    hwc, corn = G['hwc'], G['corn']
    cm = (dxa <= hwc) & (Y >= ybt - corn) & (Y < ybt)
    cy_ = (Y - (ybt - corn)) / max(1, corn)
    ct = 3.4 + 1.4 * (Y < ybt - corn + 1) - 0.4 * (cy_ > 0.35) - 1.0 * (cy_ > 0.6) - 0.8 * (Y >= ybt - 1)
    ct = ct + 0.9 * ((cy_ > 0.55) & (cy_ < 0.75)) - 1.0 * (X > cx + hwc * 0.55) + 0.5 * (X < cx - hwc * 0.6)
    seg = q(1.6)
    sc_ = np.floor((X - (cx - hwc)) / seg).astype(int)
    sf_ = (X - (cx - hwc)) / seg - sc_
    ct = ct + rng.uniform(-0.35, 0.35, 64)[sc_ % 64] - 0.9 * ((sf_ < 1.0 / seg) & (cy_ > 0.3)) + 0.5 * ((sf_ >= 1.0 / seg) & (sf_ < 2.0 / seg) & (cy_ > 0.3))
    paint(a, cm, ('plaster', 'plaster', 'plaster_warm'), ct)
    fil = cm & (Yi == int(ybt - corn + q(0.7)))
    a[fil] = np.where(a[fil] % 8 > 1, a[fil] - 2, a[fil])
    _marks(a, cm & (Y > ybt - corn + q(0.8)) & (Y < ybt - 2), rng, 6, None, ('plaster_warm', 5), length=(2, 3))
    dn = face & (Y >= ybt) & (Y < ybt + q(0.9)) & (((X - cx + 99 * q(1.2)) // q(1.2)) % 2 == 0) & ~opening
    paint(a, dn, ('plaster', 'plaster', 'plaster_warm'), 2.9 - 0.8 * (X > cx) + 1.0 * ((X - cx + 99 * q(1.2)) % q(1.2) < 1))
    under = face & (Y >= ybt) & (Y < ybt + q(1.3)) & ~dn
    a[under] = np.where(a[under] % 8 > 0, a[under] - 1, a[under])

    # --- the cap: a low lead dome on ten rolls -------------------------------------------------------
    rng = rs(7)
    hwr, yce = G['hwr'], G['yce']
    R, Hd = float(hwr), float(G['cap_h'])
    yc0 = yce - R * k
    ss = np.arange(-R, R + 0.01, 0.3)
    sx_, sd_ = np.meshgrid(ss, ss)
    rr = (sx_ / R) ** 2 + (sd_ / R) ** 2
    ins = rr <= 1.0
    sx_, sd_, rr = sx_[ins], sd_[ins], rr[ins]
    sz = Hd * np.power(np.clip(1 - rr, 0, 1), 0.62)
    py_ = np.floor(yc0 - sd_ * k - sz + PAD).astype(int)
    px_ = np.floor(cx + sx_).astype(int)
    ok = (py_ >= 0) & (py_ < a.shape[0]) & (px_ >= 0) & (px_ < a.shape[1])
    sx_, sd_, sz, rr, py_, px_ = sx_[ok], sd_[ok], sz[ok], rr[ok], py_[ok], px_[ok]
    pix = py_ * a.shape[1] + px_
    order = np.lexsort((sd_, pix))
    first = np.ones(order.size, bool)
    first[1:] = pix[order][1:] != pix[order][:-1]
    sel = order[first]
    dome = np.zeros(a.shape, bool)
    dome.flat[pix[sel]] = True
    NROLL = 12
    phi = np.arctan2(sd_[sel], sx_[sel])
    rho = np.sqrt(sx_[sel] ** 2 + sd_[sel] ** 2)
    dphi = (phi / (2 * math.pi / NROLL) + 0.5) % 1.0 - 0.5
    rollm = np.zeros(a.shape, bool)
    rollm.flat[pix[sel]] = (np.abs(dphi) * (2 * math.pi / NROLL) * rho < 1.3) & (rho > q(0.8))
    hzm = np.zeros(a.shape)
    hzm.flat[pix[sel]] = sz[sel] / max(1.0, Hd)
    # the sheets in clean bands across the dome, in the lead's middle tones: lit 2 on the west half,
    # turning 1, shade 0, the core shadow right of centre in the slate's deep blue, a reflected east rim
    uu = (X - cx) / R
    td = np.where(uu < -0.05, 2.0, np.where(uu < 0.3, 1.0, np.where(uu < 0.62, -1.0, 0.0)))
    east_rim = dome & ~np.roll(dome, -1, axis=1)
    td = np.where(east_rim & (uu > 0.3), 1.0, td)
    lap = dome & ((np.abs(hzm - 0.3) < 0.035) | (np.abs(hzm - 0.62) < 0.035)) & ~rollm
    td = np.where(lap & (td >= 1), td - 1, td)                              # two laps round it, a tone down
    sheet = dome & ~rollm
    a[sheet & (td >= 0)] = (V.FI[LEAD] * 8 + np.clip(td, 0, 5).astype(int))[sheet & (td >= 0)]
    a[sheet & (td < 0)] = code('slate_cool', 2)
    # every other sheet weathered apart: the slate's ramp at about the lead's lightness
    panel = np.zeros(a.shape, int)
    panel.flat[pix[sel]] = np.floor((phi + math.pi) / (2 * math.pi / NROLL)).astype(int)
    alt = sheet & (panel % 2 == 1) & (a // 8 == V.FI[LEAD]) & (a % 8 <= 2)
    a[alt] = V.FI['slate'] * 8 + 3 + a[alt] % 8
    # the rolls: each a meridian to the boss, the sheet's tone, its west 2 texels lit (3) on the lit half
    # only, a dark texel east of it
    a[rollm] = (V.FI[LEAD] * 8 + np.clip(td + (uu >= 0), 0, 5).astype(int))[rollm]   # proud of the sheet in the shade
    a[rollm & (td < 0)] = code(LEAD, 0)
    lit2 = rollm & (~np.roll(rollm, 1, axis=1) | ~np.roll(rollm, 2, axis=1)) & (uu < 0)
    a[lit2] = code(LEAD, 3)
    darke = dome & ~rollm & np.roll(rollm, 1, axis=1)
    a[darke & (uu < 0.3)] = code(LEAD, 0)
    a[darke & (uu >= 0.3)] = code('slate_cool', 1)
    # where each lap crosses a roll, the lead dressed over it: a clip of iron, lit on the west
    tuck = rollm & (np.roll(lap, 1, axis=1) | np.roll(lap, -1, axis=1))
    a[tuck & (uu < 0)] = code('iron', 4)
    a[tuck & (uu >= 0)] = code('iron', 2)
    # bloom: three runs under the lap on the lit sheets, 2 wide and 4 to 6 long
    ys_, xs_ = np.nonzero(lap & (uu < -0.1) & ~rollm & ~np.roll(rollm, -1, axis=1))
    if ys_.size:
        picks = rng.choice(ys_.size, size=min(3, ys_.size), replace=False)
        for i in picks:
            L_ = int(rng.integers(4, 7))
            for j in range(1, L_ + 1):
                for dx2 in (0, 1):
                    yy, xx = ys_[i] + j, xs_[i] + dx2
                    if yy < a.shape[0] and dome[yy, xx] and not rollm[yy, xx]:
                        a[yy, xx] = code(LEAD, 3)
    # a glint high on the top-left: four texels
    gys, gxs = np.nonzero(sheet & (uu < -0.35) & (uu > -0.65) & (hzm > 0.7))
    if gys.size:
        g0 = np.argmin(gys * 1000 + gxs)
        a[gys[g0]:gys[g0] + 2, gxs[g0]:gxs[g0] + 2] = code(LEAD, 4)
    # the dome's foot: a lead roll round it, lit 2 on the west, 0 on the east
    footr = (dxa <= R) & (np.abs(Y - (yc0 + k * np.sqrt(np.clip(R * R - (X - cx) ** 2, 0, None)))) < q(0.6)) & (Y > yc0)
    a[footr & ~opening] = code(LEAD, 1)
    a[footr & ~opening & (X < cx - R * 0.3)] = code(LEAD, 2)
    a[footr & ~opening & (X > cx + R * 0.3)] = code(LEAD, 0)
    yap = yc0 - Hd
    cs = cm & (Y >= ybt - corn) & (Y < ybt - corn + q(0.8)) & ~dome
    a[cs] = np.where(a[cs] % 8 > 1, a[cs] - 2, a[cs])

    # --- the finial: a lead boss, a brass ball, an iron rod and the vane ----------------------------
    br = q(1.2)
    by = yap - q(1.0)
    bm_ = ((X - cx) / br) ** 2 + ((Y - by) / br) ** 2 <= 1
    nxb, nyb = (X - cx) / br, (Y - by) / br
    paint(a, bm_, ('brass', 'brass', 'brass_warm'), 2.8 + 2.4 * lam(nxb, nyb * 0.6, np.sqrt(np.clip(1 - nxb * nxb - nyb * nyb, 0, 1))))
    boss = (dxa < q(1.0)) & (Y >= yap - q(0.3)) & (Y < yap + q(0.8))
    a[boss] = code(LEAD, 1)
    a[boss & (X < cx)] = code(LEAD, 2)
    bg = boss & (X < cx - 1)                                          # its glint: two texels
    bgy, bgx = np.nonzero(bg)
    if bgy.size:
        a[bgy.min(), bgx.min():bgx.min() + 2] = code(LEAD, 4)
    # the vane: an arrow on the rod, pivoted about 40 % from its head so the tail is the bigger mass:
    # a sharp head 5 long and 5 tall pointing west, a one-texel shaft, a swallowtail flag 9 wide and 7
    # tall with a V notch 3 deep at its east end; top edges lit, the body mid, the undersides dark
    vy = int(by - br - q(4.6))                                       # the shaft's row
    rod = (Xi >= int(cx) - 1) & (Xi < int(cx) + 1) & (Yi >= vy) & (Y < by - br + 1)
    paint(a, rod, 'iron', np.where(Xi < int(cx), 3.6, 1.8))
    tip = int(cx) - 9
    hx1 = tip + 5
    tx0 = int(cx) + 4
    shaft = (Yi == vy) & (Xi >= hx1) & (Xi < tx0)
    a[shaft] = code('iron', 3)
    head = np.zeros(a.shape, bool)
    for i_ in range(5):                                              # the head: columns widening from the tip
        hh = min(2, (i_ + 1) // 2)
        head |= (Xi == tip + i_) & (Yi >= vy - hh) & (Yi <= vy + hh)
    paint(a, head, 'iron', np.where(Yi < vy, 4, np.where(Yi == vy, 3, 1)))
    tail = (Xi >= tx0) & (Xi < tx0 + 9) & (Yi >= vy - 3) & (Yi <= vy + 3)
    notch = (Xi >= tx0 + 6) & (np.abs(Yi - vy) <= (Xi - (tx0 + 6)))   # the V, 3 deep at the east end
    tail &= ~notch
    tt_ = np.where(Yi == vy - 3, 4, np.where(Yi == vy + 3, 1, 3))
    tt_ = np.where(tail & (Yi > vy) & (np.abs(Yi - vy) == (Xi - (tx0 + 6)) + 1), 1, tt_)   # the notch's lower lip dark
    paint(a, tail, 'iron', tt_)

    # --- the storm's marks on the empty cupola, inside the shared outline ------------------------
    if not hung:
        rng = rs(8)
        # slates gone from the base's west half: dark holes with the battens across them
        for (hx, hy) in ((cx - hw + 4, G['yft'] + 2), (cx - hw + 12, G['yft'] + 7), (cx - 8, G['yft'] + 3),
                         (cx - hw + 7, G['yft'] + 11)):
            hole = bm & (X >= hx) & (X < hx + 6) & (Y >= hy) & (Y < hy + 4) & (Y < yfb - q(1.2))
            a[hole] = code('soot', 0)
            bat = hole & (Yi == int(hy) + 2)
            a[bat] = code('timber', 2)
            a[bat & (Xi == int(hx))] = code('timber', 3)
        # a slipped slate hanging askew under one hole
        sl_ = bm & (Xi >= int(cx - hw + 12)) & (Xi < int(cx - hw + 17)) & (Yi >= int(G['yft'] + 11)) & (Yi < int(G['yft'] + 13))
        paint(a, sl_, 'slate', np.where(Yi == int(G['yft'] + 11), 4, 2))
        # the flashing's low west corner lifted: a flap 4 x 3 bent up off the slates, its top the lead's
        # body with the lit lip, its underside a tone down, the dark gap under it
        fx0 = int(cx - hw)
        fy_ = int(math.floor(G['yfb0'] + sl * (hw - 2) - q(1.0))) - 3     # the flap's top row
        for dy2, c_ in ((0, (LEAD, 3)), (1, (LEAD, 1)), (2, (LEAD, 0)), (3, ('slate_cool', 0))):
            yy = fy_ + dy2 + PAD
            for xx in range(fx0, fx0 + 4):
                if 0 <= yy < a.shape[0] and a[yy, xx] >= 0:
                    a[yy, xx] = code(*c_)
        # a dent in the dome's lit west half, 5 x 4: a dark crescent on its upper-left inner wall two
        # tones down, a lit rim on its lower right, the roll crossing it kinked a texel east
        dcx, dcy = cx - R * 0.42, yc0 - Hd * 0.45 + PAD
        ell = ((X - dcx) / 3.1) ** 2 + ((Yp - dcy) / 2.6) ** 2 <= 1
        ell &= dome
        roll_in = ell & rollm
        kink = np.roll(roll_in, 1, axis=1) & ell
        a[roll_in & ~kink] = (V.FI[LEAD] * 8 + np.clip(td, 0, 5).astype(int))[roll_in & ~kink]
        a[kink] = code(LEAD, 3)
        cres = ell & (((X - dcx) + (Yp - dcy)) < -1.2)
        a[cres] = code('slate_cool', 1)                                  # two tones under the sheet
        rimd = dome & ~ell & (np.roll(ell, 1, axis=1) | np.roll(ell, 1, axis=0)) & ((X - dcx) + (Yp - dcy) > 1.0)
        a[rimd] = code(LEAD, 3)

    p = Pic(Wb, Hb + PAD, 0, 0)
    p.a = a
    finish(p)
    if debug is not None:
        # the parts' masks in this canvas, for measuring them (the review's own sheets work on the picture)
        debug.update(dome=dome | footr | boss, base=bm | fl | ledge, head=head, tail=tail)
        if not hung:
            debug.update(dent=ell, flap_top=fy_, nest=nest)

    # --- its shadow on the roof: east and down, onto what the library and its damage draw there ----
    body = p.a >= 0
    comp = base.copy()
    if damage is not None:
        comp = np.where(damage >= 0, damage, comp)
    roof = np.zeros(a.shape, bool)
    roof[PAD:, :] = info['roof'] if info.get('roof') is not None and np.shape(info['roof']) == base.shape else (comp >= 0)
    ys_, xs_ = np.nonzero(body)
    yfoot = G['yfb0'] + sl * np.abs(xs_ + 0.5 - cx) + PAD
    hgt = np.maximum(0.0, yfoot - (ys_ + 0.5))
    gx = xs_ + CAST[0] * hgt
    gy = yfoot + CAST[1] * hgt * k + sl * CAST[0] * hgt * (xs_ + CAST[0] * hgt > cx)
    sm = np.zeros(a.shape, bool)
    ok = (gx >= 0) & (gx < Wb) & (gy >= 0) & (gy < Hb + PAD)
    sm[gy[ok].astype(int), gx[ok].astype(int)] = True
    kk = q(2)
    sm = ndi.binary_dilation(sm, iterations=kk)
    sm = ndi.binary_fill_holes(sm)
    sm = ndi.binary_erosion(sm, iterations=kk)
    sm &= ~body & roof
    sm[:PAD] = False
    core = ndi.binary_erosion(sm, iterations=q(1.3))
    full = np.full(a.shape, -1, np.int32)
    full[PAD:] = comp
    sc = full.copy()
    sel = sm & (sc >= 0)
    sc[sel] = step(sc[sel], -1)
    sel2 = core & (sc >= 0)
    sc[sel2] = step(sc[sel2], -1)
    shadow = Pic(Wb, Hb + PAD, 0, 0)
    shadow.a = np.where(sm & (full >= 0), sc, -1).astype(np.int32)
    return p, shadow, G


def bell_fallen(w, h, seed, hd=False):
    """The bell where it came down, on its side in the street under the library's east window: the same
    bell as the hung one, from the one profile at 1:1 (bell_profile), its axis 50 degrees off the
    horizontal, the crown and the snapped stub of its headstock to the north-west, the mouth turned to
    the south-south-east. Its tones run in bands round its circumference, as on the hung bell: a
    highlight band along the lit upper-west flank from crown to lip, then the lit, body and turning
    tones, the core shadow along its underside with a texel of reflected light over where it rests. The
    two cast bands go round it as curved lines, a dark texel with a lit one under it. The mouth is an
    ellipse: dark inside, the far inner wall a lit band at its top, the clapper's ball low in it, the
    lip's rim lit on its upper and west arc. Two short runs of greyed green under the bands on the
    shaded side. Foot: the middle of its lowest row."""
    rng = np.random.default_rng(seed)
    rows, half, cr = bell_profile()
    body_rows = rows - cr
    L_ = float(body_rows)
    hp = half[cr:]
    Rl = float(hp[-1])
    W, H = 90, 90
    ax, ay = 40, 66
    p = Pic(W, H, ax, ay)
    a = p.a
    Y, X = grid(a)
    Xi, Yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    ang = math.radians(50.0)
    dx_, dy_ = math.cos(ang), math.sin(ang)                         # the axis on the ground: east, south
    px_, py_ = -dy_, dx_                                            # across it on the ground
    e0, n0 = ax - L_ * 0.5 * dx_, ay - 4.0 - L_ * 0.5 * dy_

    def prof(s_):
        return np.interp(s_, np.arange(body_rows), hp)
    ss = np.arange(0.0, L_, 0.2)
    th = np.arange(0, 2 * math.pi, 0.015)
    S, T = np.meshgrid(ss, th)
    rho = prof(S)
    za = prof(S * 0) + (Rl - prof(S * 0)) * (S / L_)
    cr_, sr_ = np.cos(T), np.sin(T)
    E = e0 + S * dx_ + rho * cr_ * px_
    N = n0 + S * dy_ + rho * cr_ * py_
    Z = za + rho * sr_
    # the light by the angle round the axis only, so the bands run from crown to lip
    li = lam(cr_ * px_, cr_ * py_, sr_)
    tone = np.select([li > 0.85, li > 0.78, li > 0.68, li > 0.45], [5.0, 4.0, 3.0, 2.0], 1.0)
    tone = np.where((sr_ < -0.82) & (Z < 2.5), 2.0, tone)            # reflected light over where it rests
    ring = np.zeros(S.shape, bool)
    for band in BANDS:
        ring |= np.abs(S - band) < 0.45
    # the founder's letters round the shoulder between the crown and the waist band, raised: each a lit
    # block a tone up with its shade a tone down under it, on the side towards the light
    let = (S > 3.2) & (S < 5.2) & ((np.floor(T / 0.2) % 3) != 2) & (li > 0.3)
    tone = np.where(let, np.minimum(5.0, tone + 1), tone)
    tone = np.where((S >= 5.2) & (S < 6.0) & ((np.floor(T / 0.2) % 3) != 2) & (li > 0.3), np.maximum(1.0, tone - 1), tone)
    sx = np.floor(E).astype(int)
    sy = np.floor(N - Z).astype(int)
    ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx, sy, N_, Z_, tone_, ring_, S_ = sx[ok], sy[ok], N[ok], Z[ok], tone[ok], ring[ok], S[ok]
    pix = sy * W + sx
    near = N_ + Z_
    order = np.lexsort((-near, pix))
    first = np.ones(order.size, bool)
    first[1:] = pix[order][1:] != pix[order][:-1]
    sel = order[first]
    body = np.zeros(a.shape, bool)
    body.flat[pix[sel]] = True
    tmap = np.zeros(a.shape)
    tmap.flat[pix[sel]] = tone_[sel]
    rmap = np.zeros(a.shape, bool)
    rmap.flat[pix[sel]] = ring_[sel]
    paint(a, body, BRONZE, tmap, lo=0, hi=5)
    # the cast bands: a dark texel, a lit one under it
    a[rmap] = code('timber_warm', 1)
    below = np.roll(rmap, 1, axis=0) & body & ~rmap
    a[below] = np.where(a[below] // 8 == V.FI['brass'], np.minimum(a[below] + 1, V.FI['brass'] * 8 + 5), code('brass', 2))
    # the mouth: the lip's circle projected, filled dark; the far inner wall lit at its top; the
    # clapper low in it; the rim lit on its upper and west arc
    # the lip's circle is an ellipse on screen: centre C, axes U (across, on the ground) and V (up)
    Rm = Rl - 0.5
    Cx, Cy = e0 + L_ * dx_, n0 + L_ * dy_ - Rl
    Ux, Uy, Vx, Vy = Rm * px_, Rm * py_, 0.0, -Rm
    det = Ux * Vy - Vx * Uy
    qx, qy = X - Cx, Y - Cy
    cc = (qx * Vy - Vx * qy) / det
    sc = (Ux * qy - qx * Uy) / det
    mouth = cc * cc + sc * sc <= 1.0
    rim = mouth & ~ndi.binary_erosion(mouth)
    inside = mouth & ~rim
    # inside, in rings by depth: the far inner wall at the top a lit band, the near wall dark, the wall
    # going down into the bell a tone deeper, the hollow soot
    rr_ = np.sqrt(cc * cc + sc * sc)
    a[inside] = code('soot', 0)
    a[inside & (rr_ > 0.55)] = code('timber_warm', 0)
    ys_, xs_ = np.nonzero(inside)
    mcx, mcy = xs_.mean(), ys_.mean()
    top_ = ys_.min()
    farw = inside & (rr_ > 0.62) & (Y < mcy) & (Y < top_ + 4.5)
    a[farw] = code('timber_warm', 1)
    a[farw & (Y < top_ + 2.5)] = code('brass', 1)
    a[farw & (Y < top_ + 1.5) & (X < mcx)] = code('brass', 2)          # the far wall's lip, catching the most
    # the near wall: dark, a thread of light reflected along it just inside the rim
    nearw = inside & (rr_ > 0.86) & (Y > mcy + 2)
    a[nearw] = code('timber_warm', 1)
    clx, cly = mcx + 1.0, ys_.max() - 2.5
    clap = inside & (((X - clx) / 2.3) ** 2 + ((Y - cly) / 2.1) ** 2 <= 1)
    a[clap] = code('iron', 2)
    a[clap & (X < clx) & (Y < cly)] = code('iron', 3)
    rim_lit = rim & ((Y < mcy) | (X < mcx - 1))
    a[rim] = code('brass', 2)
    a[rim_lit] = code('brass', 3)
    # greyed green: two runs under the bands, two texels wide, on the shaded underside only
    shade = body & ~mouth & (tmap <= 2) & ~rmap
    n_runs = 0
    for band in BANDS:
        cand = np.nonzero(below & shade & ~np.roll(rmap, 2, axis=0))
        if cand[0].size == 0 or n_runs >= 2:
            continue
        k2 = int(rng.integers(0, cand[0].size))
        yy, xx = cand[0][k2], cand[1][k2]
        for j in range(int(rng.integers(3, 5))):
            for d2 in (0, 1):
                if yy + j < H and shade[yy + j, xx + d2]:
                    a[yy + j, xx + d2] = code('leaf_cool', 1)
        n_runs += 1
    # the canons at the crown and the stub of the old headstock strapped to them, pointing north-west,
    # its break jagged fibres with a dark split
    ce, cn = e0 - 1.5 * dx_, n0 - 1.5 * dy_
    cz = prof(0) * 0.9
    cx0, cy0 = ce, cn - cz
    can = (((X - cx0) / 2.4) ** 2 + ((Y - cy0) / 2.0) ** 2 <= 1) & ~body
    paint(a, can, 'iron', np.where(X < cx0, 3.4, 1.8))
    x1b, y1b = cx0 - 9.0 * math.cos(math.radians(20)), cy0 - 9.0 * math.sin(math.radians(20))
    stub = bar(a, cx0 - 1, cy0, x1b, y1b, 1.8, 'timber', 3) & ~body
    ux_, uy_ = x1b - cx0, y1b - cy0
    Ls = math.hypot(ux_, uy_)
    al = ((X - cx0) * ux_ + (Y - cy0) * uy_) / Ls
    ac = (-(X - cx0) * uy_ + (Y - cy0) * ux_) / Ls
    paint(a, stub, ('timber_cool', 'timber', 'timber_warm'), 3.0 + 1.2 * (ac < -0.7) - 1.3 * (ac > 0.7))
    a[stub & (al > Ls - 1.5)] = code('timber', 1)
    for off_, ln in ((-1.2, 3), (0.3, 2), (1.4, 3)):
        for j2 in range(ln):
            xx = int(round(x1b + ux_ / Ls * j2 - uy_ / Ls * off_))
            yy = int(round(y1b + uy_ / Ls * j2 + ux_ / Ls * off_))
            if 0 <= yy < H and 0 <= xx < W:
                a[yy, xx] = code('timber_warm', 4)
    a[stub & (np.abs(ac) < 0.5) & (al > Ls - 2.5)] = code('soot', 1)
    # its grain: two dark lines along it, broken
    for off_ in (-0.6, 0.7):
        gr = stub & (np.abs(ac - off_) < 0.45) & (al > 1.5) & (al < Ls - 2.5) & (((al * 1.7).astype(int) % 4) != 3)
        a[gr] = code('timber', 1 if off_ > 0 else 2)
    strap = stub & (np.abs(al - Ls * 0.4) < 1.0)
    a[strap] = np.where(ac[strap] < 0, code('iron', 4), code('iron', 2))
    # the bolt through strap and stub, its head lit on the upper left
    bys, bxs = np.nonzero(strap)
    if bys.size:
        by_, bx_ = int(bys.mean()), int(bxs.mean())
        a[by_:by_ + 2, bx_:bx_ + 2] = code('iron', 1)
        a[by_, bx_] = code('iron', 5)
    # the canons' loop: the hole through it dark
    a[(((X - cx0) / 1.0) ** 2 + ((Y - cy0) / 0.8) ** 2 <= 1) & can] = code('soot', 0)
    finish(p)
    ys_, xs_ = np.nonzero(p.a >= 0)
    x0, y0, x1, y1 = xs_.min(), ys_.min(), xs_.max() + 1, ys_.max() + 1
    out = Pic(x1 - x0, y1 - y0, (x1 - x0) // 2, y1 - y0)            # its foot: the middle of its lowest row
    out.a = p.a[y0:y1, x0:x1].copy()
    return out
