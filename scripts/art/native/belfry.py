"""The library's bell cupola and its bell (Matt, 13 Nov, decision (d): "the bell tower is optional, and
its cupola is drawn, so that paying visibly changes the square"; docs/vision/decisions-2026-11-13.md).

Three pictures, drawn in the frame of the library's own picture (`town.build` places them on the
library's foot, the cupolas three texels in front of it and their shadow two, so they sort with the
building over its damage overlay):

- `cupola(..., hung=False)`: the storm's state. The bell is gone (it stands in the street below; the bell
  look line in game/data/dialogue/crossroads.json), the old oak headstock snapped: one half still in the
  west side of the arch, hanging down at an angle with its splintered end and a strap; the frame's iron
  brackets empty on the far posts; pigeons nesting in the west corner of the bare floor.
- `cupola(..., hung=True)`: after the restore (`bell_tower`, 50 Glint): the bell back in a new frame (a
  fresh-sawn headstock across the arch, iron straps down to the canons, the bronze bell), its rope down
  to the floor's hatch.
- the cast shadow on the roof, the same for both: the roof's own codes (the library's, with its damage
  overlay over them) a tone down, two in its core, east and down of the cupola by the one sun.

The two cupolas share every texel outside the arch, so paying swaps only what hangs inside it. The cupola
itself: a slate-hung base astride the ridge (chipped slates, moss in its low courses), its lead flashing
down the two slopes and a lead ledge on top; an open belfry of painted upright boards (weathered along
the grain, nailed to a frieze board) between two bare oak corner posts (grain, pegs, a capital and a
plinth block each), a round arch with its voussoirs and keystone, a sill rail; the far wall in the
shade, the floor near the sill in some light; a moulded cornice in lengths over dentils; a lead dome on
twelve rolls, its sheets lapped and blooming white; a brass ball, an iron rod and a vane pointing west.
Lit from the upper left, every part with its thickness.

`bell_fallen(w, h, seed)`: the same bell where it came down, standing askew on its lip in the street.

Sizes (world px, `q` makes texels; docs/vision/size-guide.md: a bell turret stands 32 to 64 over a
chapel's ridge, a landmark; this is a library's small cupola): the base 16 wide, 5 high at the ridge;
the belfry 15; the dome 7 over its foot; about 37 from the ridge to the vane in all. The bell 7.8 tall
and 7.8 across its mouth hung, 8.0 by 8.2 on the setts (about 0.55 m: a small cupola's bell, 0.32 A).
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


def _paint_courses(a, m, X, Y, along, period, joint, rng, base, fams, lit=1.2, butt_axis='y', extra=None):
    """Slates (or boards) in courses over mask m: each course `period` texels deep along `along`, its
    butt row lit, its head row in the shade of the course over it; joints every `joint` texels across,
    staggered by half a slate each course; each slate its own small tone offset."""
    c = np.floor(along / period).astype(int)
    fr = along / period - c
    across = X if butt_axis == 'y' else Y
    jf = (across + (c % 2) * joint / 2.0) / joint
    jidx = np.floor(jf).astype(int)
    t = base + np.zeros(m.shape) + (0 if extra is None else extra)
    t = t + rng.uniform(-0.45, 0.45, 4096)[(c * 31 + jidx * 7) % 4096]
    t = np.where(fr > 1 - 1.0 / period, t + lit, t)                     # the butt catches the light
    t = np.where(fr < 1.0 / period, t - 1.1, t)                         # the head in the course's shade
    t = np.where(jf - jidx < 1.0 / joint, t - 1.0, t)                   # the joint between two slates
    paint(a, m, fams, t)


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
    G['cap_h'] = q(spec.get('cap_h', 7))                             # the dome's height over its foot
    G['pw'] = q(2.3)                                                # a corner post
    G['sill'] = q(1.7)
    G['r'] = G['hwb'] - G['pw']                                     # the arch's radius: the opening's half width
    G['crown'] = G['ybt'] + q(1.6)                                  # the arch's crown
    G['spring'] = G['crown'] + G['r']
    return G


def cupola(base: np.ndarray, damage, info: dict, depth_world: float, spec: dict, hung: bool, seed: int):
    """The cupola on the building whose picture codes are `base` (and its damage overlay's, `damage`,
    or None), and its cast shadow on the roof: two Pics the width of the building's picture and PAD
    texels taller, their rows offset by PAD (row PAD is the building's row 0), anchor (0, 0), and the
    geometry. town.build crops them and sets their feet. The shadow is the roof's own codes (the
    library's, with its damage overlay over them) a tone down, two in its core; the same for both
    states, since the two cupolas share their outline."""
    rng = np.random.default_rng(seed)
    G = geometry(info, depth_world, spec)
    Hb, Wb = base.shape
    a = np.full((Hb + PAD, Wb), -1, np.int32)
    Yp, X = grid(a)
    Y = Yp - PAD                                                    # the building's own rows
    cx, k, sl, hw = G['cx'], G['k'], G['sl'], G['hw']
    dxa = np.abs(X - cx)

    # --- the base: slate-hung, astride the ridge ----------------------------------------------------
    yfb = G['yfb0'] + sl * dxa                                      # its foot down the two slopes
    bm = (dxa <= hw) & (Y >= G['yft']) & (Y < yfb)
    _paint_courses(a, bm, X, Y, Y - G['yft'], q(1.3), q(2.0), rng, 2.6, ('slate_cool', 'slate', 'slate_warm'),
                   extra=-0.8 * (X > cx + hw * 0.55) + 0.5 * (X < cx - hw * 0.6))
    # chipped slate corners catching the light, and moss in the low courses over the flashing
    _marks(a, bm & (Y < yfb - q(2.0)), rng, 22, None, ('slate_warm', 5), length=(2, 2))
    _marks(a, bm & (Y > yfb - q(3.4)) & (Y < yfb - q(1.0)), rng, 11, ('leaf_cool', 2), ('leaf', 3), length=(2, 3))
    # the lead flashing down both slopes under it: a lit upper lip, its body, a dark drip on the slates
    fl = (dxa <= hw + 1) & (Y >= yfb - q(1.0)) & (Y < yfb + 1)
    paint(a, fl, 'iron', 3.0 + 1.0 * (Y < yfb - q(1.0) + 1) - 0.8 * (X > cx) - 1.2 * (Y >= yfb))
    # its top: a lead ledge, the top plane in the light
    ledge = (dxa <= hw) & (Y >= G['ybb']) & (Y < G['yft'])
    paint(a, ledge, 'iron', 4.0 - 0.8 * (X > cx + hw * 0.5) + 0.6 * (Y < G['ybb'] + 1))
    fill(a, int(cx - hw), int(G['yft']) + PAD, int(cx + hw) + 1, int(G['yft']) + PAD + 1, code('iron', 2))   # its front arris's shade

    # --- the belfry: two corner posts, a round arch between them, a sill rail ----------------------
    hwb, pw, r = G['hwb'], G['pw'], G['r']
    ybt, ybb = G['ybt'], G['ybb']
    face = (dxa <= hwb) & (Y >= ybt) & (Y < ybb)
    yspr = G['spring']
    dyc = np.maximum(0.0, yspr - Y)
    arch_half = np.sqrt(np.clip(r * r - dyc * dyc, 0, None))
    opening = face & (dxa < arch_half) & (Y >= G['crown']) & (Y < ybb - G['sill'])
    boards = face & ~opening
    # painted boards, upright, lit west of each joint; the east post a tone down, the west one up
    bj = q(2.2)
    col = np.floor((X - (cx - hwb)) / bj).astype(int)
    jx = (X - (cx - hwb)) / bj - col
    t = 3.4 + rng.uniform(-0.3, 0.3, 64)[col % 64]
    t = np.where(jx < 1.0 / bj, t - 1.4, t)
    t = np.where((jx >= 1.0 / bj) & (jx < 2.0 / bj), t + 0.7, t)
    t = t + 0.6 * (X < cx - hwb + pw) - 1.1 * (X > cx + hwb - pw) - 0.5 * (X > cx + r * 0.4)
    paint(a, boards, ('plaster', 'plaster', 'plaster_warm'), t)
    # the paint weathered along the grain: short cracks a tone down with a lit lip, and nail heads in pairs
    _marks(a, boards & (jx >= 2.0 / bj), rng, 34, None, ('plaster_warm', 5), length=(2, 3), vertical=True)
    # a frieze board across the top of the boards, under the cornice: its lit top, its lower arris dark
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
    # the corner posts: square oak, left bare, standing proud of the boards: a lit west arris, a dark
    # east one, the grain running down them in long checks, a peg at the head and foot of each
    oak = ('timber_cool', 'timber', 'timber_warm')
    for x0 in (cx - hwb, cx + hwb - pw):
        pm = face & (X >= x0) & (X < x0 + pw)
        tp = 3.2 - 1.2 * (x0 > cx)
        paint(a, pm, oak, tp + 1.3 * (X < x0 + 1) - 1.5 * (X >= x0 + pw - 1) + 0.4 * (X < x0 + 2))
        _marks(a, pm & (X > x0 + 1) & (X < x0 + pw - 1), rng, 15, None, None, length=(3, 6), vertical=True)
        _marks(a, pm & (X > x0) & (X < x0 + 3), rng, 4, None, ('timber_warm', 5), length=(2, 3), vertical=True)
        for (yy0, hh) in ((ybt + q(0.9), q(1.3)), (ybb - q(1.6), q(1.6))):              # a capital and a plinth block
            cb = (X >= x0 - 1) & (X < x0 + pw + 1) & (Y >= yy0) & (Y < yy0 + hh) & (dxa <= hwb + 1)
            paint(a, cb, oak, tp + 0.5 + 1.2 * (Y < yy0 + 1) - 1.6 * (Y >= yy0 + hh - 1) - 0.8 * (X >= x0 + pw))
        for py_ in (ybt + q(3.0), ybb - q(3.0)):                                          # the pegs
            pg = (X >= x0 + q(0.8)) & (X < x0 + q(0.8) + 2) & (Y >= py_) & (Y < py_ + 2) & pm
            a[pg] = code('timber', 1)
            a[pg & (np.floor(X) == int(x0 + q(0.8))) & (np.floor(Y) == int(py_))] = code('timber_warm', 4)
    # the arch's trim: a moulded band round the opening, lit on its lower west curve, shaded east
    ring = face & ~opening & (dxa < arch_half + q(0.9)) & (Y >= G['crown'] - q(0.9)) & (Y < ybb - G['sill'])
    ang = np.arctan2(Y - yspr, X - cx)
    paint(a, ring, ('plaster', 'plaster', 'plaster_warm'), 4.2 - 1.6 * (X > cx + 1) + 0.6 * (np.sin(ang) < -0.5) * (X < cx))
    # its voussoirs: the joints between the blocks of the ring, radial, a tone down with the lit edge west
    vf = ((ang + math.pi) / (math.pi / 9)) % 1.0
    vj = ring & (Y < yspr) & (vf < 0.16)
    a[vj] = np.where(a[vj] % 8 > 0, a[vj] - 1, a[vj])
    # the keystone over the crown
    ks = face & (dxa < q(1.0) + (G['crown'] - Y) * 0.25) & (Y >= G['crown'] - q(2.0)) & (Y < G['crown'] + 1)
    paint(a, ks, ('plaster', 'plaster', 'plaster_warm'), 4.4 - 1.5 * (X > cx) + 0.6 * (Y < G['crown'] - q(2.0) + 1))
    # the sill rail across the foot of the opening: a lit top, its front face, its shade on the boards under it
    sr = face & (dxa < hwb - 1) & (Y >= ybb - G['sill']) & (Y < ybb - G['sill'] + q(1.0))
    paint(a, sr, ('timber_cool', 'timber', 'timber_warm'), 3.3 + 1.2 * (Y < ybb - G['sill'] + 1) - 0.9 * (X > cx + r * 0.5))

    # --- inside the arch: the floor in the cap's shade, the far posts --------------------------------
    inner = opening
    dep = (ybb - G['sill'] - Y) / max(1.0, (ybb - G['sill']) - G['crown'])    # 0 at the sill, 1 at the crown
    fb = q(1.6)
    plank = np.floor((Y - G['crown']) / fb).astype(int)
    pj = ((Y - G['crown']) / fb - plank) < 1.0 / fb
    near = dep < 0.3                                                          # the floor near the sill, in some light
    tin = np.where(near, 2.4 - 3.0 * dep - 0.7 * pj + rng.uniform(-0.25, 0.25, 64)[plank % 64], 0.6 - 0.4 * dep)
    tin = tin - 0.5 * (X > cx + r * 0.3) + 0.5 * (X < cx - r * 0.4) * near
    paint(a, inner, ('soot', 'timber_cool', 'timber'), tin, lo=0, hi=3)
    # the far wall above the floor, in the cap's shade: upright boards, their joints a tone down and the
    # west edge of each catching what light comes in; darkest under the crown and down the east side
    far = inner & ~near
    fbj = q(2.0)
    fcol = np.floor((X - (cx - r)) / fbj).astype(int)
    fjx = (X - (cx - r)) / fbj - fcol
    tf = 1.4 + rng.uniform(-0.3, 0.3, 64)[fcol % 64] - 1.0 * (fjx < 1.0 / fbj) + 0.6 * ((fjx >= 1.0 / fbj) & (fjx < 2.0 / fbj))
    tf = tf - 0.8 * (Y < G['crown'] + q(2.6)) - 0.6 * (X > cx + arch_half - q(1.6))
    paint(a, far, ('soot', 'soot', 'timber_cool'), tf, lo=0, hi=3)
    a[inner & (Y < G['crown'] + q(1.0))] = code('soot', 0)
    # the old frame's iron brackets on the far posts, where the headstock sat
    for bx_ in (cx - r + q(1.2), cx + r - q(1.2) - q(1.0)):
        brk = inner & (X >= bx_) & (X < bx_ + q(1.0)) & (Y >= G['crown'] + q(2.0)) & (Y < G['crown'] + q(3.6))
        paint(a, brk, 'iron', 2.2 + 1.2 * (Y < G['crown'] + q(2.0) + 1) - 0.8 * (bx_ > cx))
    # the trap hatch in the floor the bell rope comes up through, its lit far edge; dust on the boards
    hx0, hy0 = cx + q(1.8), ybb - G['sill'] - q(2.6)
    hatch = inner & (X >= hx0) & (X < hx0 + q(3.0)) & (Y >= hy0) & (Y < hy0 + q(1.6))
    paint(a, hatch, 'soot', 0.4 + 1.2 * (Y < hy0 + 1))
    _marks(a, inner & near & ~hatch, rng, 8, None, ('timber', 3), length=(2, 3))
    # the far posts, a strip of each inside the opening's sides, in the dark
    for sx, w_ in ((cx - r, q(1.2)), (cx + r - q(1.2), q(1.2))):
        fp = inner & (X >= sx) & (X < sx + w_) & (Y < ybb - G['sill'] - q(3.0))
        paint(a, fp, 'soot', 2.4 - 0.8 * (sx > cx))

    hang = np.zeros(a.shape, bool)
    if hung:
        # the new frame: a fresh-sawn headstock across under the crown, pale, its iron straps
        hy0, hy1 = G['crown'] + q(0.7), G['crown'] + q(2.2)
        hs = inner & (Y >= hy0) & (Y < hy1)
        paint(a, hs, ('timber', 'timber_warm', 'timber_warm'), 3.3 + 1.3 * (Y < hy0 + 1) - 1.4 * (Y >= hy1 - 1) - 0.8 * (X > cx + r * 0.5))
        for gx in (cx - q(3.4), cx + q(2.6)):                                     # end grain at a joint and a peg
            a[hs & (np.abs(X - gx) < 1.0)] = code('timber_warm', 2)
        hang |= hs
        # the bell: crown and canons, shoulder, waist, the flare to its lip, as a bronze form
        bt, bb = hy1 - 1, hy1 - 1 + q(7.8)
        f = np.clip((Y - bt) / max(1, bb - bt), 0, 1)
        half = q(3.9) * (0.46 + 0.10 * np.sin(np.clip(f / 0.18, 0, 1) * math.pi / 2) + 0.44 * f ** 2.3)
        u = (X - cx) / np.maximum(1.0, half)
        bell = (np.abs(u) <= 1) & (Y >= bt + q(0.8)) & (Y < bb)
        nz = np.sqrt(np.clip(1 - u * u, 0, 1))
        tb = 1.1 + 2.3 * lam(u, -nz * 0.35, nz * 0.9) + 0.7 * (u > 0.82)
        tb = tb + 0.8 * ((Y < bt + q(1.6)) & (u < 0.2))                          # the crown's lit shoulder
        lip = bell & (Y >= bb - q(1.1))
        tb = np.where(lip, tb + 0.7 - 0.6 * (Y >= bb - 1), tb)                   # the soundbow, thick and lit
        for by in (bt + q(2.4), bb - q(1.6)):                                    # two cast bands round it
            tb = np.where(bell & (np.floor(Y) == int(by)), tb - 1.3, tb)
            tb = np.where(bell & (np.floor(Y) == int(by) - 1) & (u < 0.4), tb + 0.6, tb)
        paint(a, bell, ('timber_warm', 'brass', 'brass'), tb, lo=0, hi=4)
        a[bell & (u < -0.3) & (u > -0.55) & (Y > bt + q(2.8)) & (Y < bb - q(2.4))] = code('brass', 5)   # the glint
        # the canons: an iron loop and straps up into the headstock
        cn = (np.abs(X - cx) < q(1.3)) & (Y >= hy1 - 1) & (Y < bt + q(1.2))
        paint(a, cn, 'iron', 3.0 - 1.2 * (X > cx))
        for sx in (cx - q(2.0), cx + q(1.6)):
            st = inner & (X >= sx) & (X < sx + 2) & (Y >= hy0) & (Y < bt + q(1.6))
            a[st] = code('iron', 2 if sx > cx else 4)
        hang |= bell | cn
        # the rope, down from the wheel's side to the floor east of the bell
        rx = cx + q(4.6)
        rope = inner & (X >= rx) & (X < rx + 2) & (Y >= hy1) & (Y < ybb - G['sill'])
        paint(a, rope, 'sand', 3.6 - 1.2 * (X >= rx + 1))
        hang |= rope
    else:
        # pigeons have moved in: a nest of straw and twigs in the west corner of the bare floor
        nx0, ny0 = cx - r + q(1.2), ybb - G['sill'] - q(2.2)
        nest = inner & (((X - nx0 - q(1.6)) / q(1.8)) ** 2 + ((Y - ny0 - q(0.7)) / q(0.9)) ** 2 <= 1)
        tn = 2.4 + 1.2 * (Y < ny0 + q(0.5)) - 1.0 * (X > nx0 + q(2.4)) + rng.uniform(-0.6, 0.6, nest.shape) * 0
        paint(a, nest, ('earth', 'sand_cool', 'sand'), tn)
        _marks(a, nest, rng, 6, ('timber', 2), ('sand', 4), length=(2, 3))
        hang |= nest
        # the old headstock, snapped: its west half still in the arch's west side, hanging down to the
        # east with a splintered end; a strap dangling from it; the floor bare
        x0b, y0b = cx - r + 1, G['crown'] + q(3.0)
        x1b, y1b = cx + q(1.6), G['crown'] + q(7.6)
        hb = bar(a, x0b, y0b + PAD, x1b, y1b + PAD, q(1.0), 'timber', 3, where=inner)
        hb &= inner
        ux, uy = (x1b - x0b), (y1b - y0b)
        L_ = math.hypot(ux, uy)
        along_ = ((X - x0b) * ux + (Y - y0b) * uy) / L_
        acr = (-(X - x0b) * uy + (Y - y0b) * ux) / L_
        tt = 3.0 + 1.3 * (acr < -q(0.4)) - 1.2 * (acr > q(0.45)) - 0.5 * (along_ > L_ * 0.6)
        paint(a, hb, ('timber_cool', 'timber', 'timber_warm'), tt)
        # the splinters at the broken end: a few pale slivers
        for dd, sp in ((0.0, 1.0), (2.0, -1.0)):
            sx_ = x1b + 1 + dd * 0.4
            sy_ = y1b - 1 + sp
            sm = inner & (np.abs(Y - sy_ - (X - sx_) * 0.55) < 0.8) & (X >= sx_ - 1) & (X < sx_ + q(0.7) + dd * 0.4)
            a[sm] = code('plaster_warm', 3)
        a[hb & (along_ > L_ - q(0.7))] = code('plaster_warm', 2)                        # the raw break
        # the strap, hanging from where the bell's canons were
        sx0 = x0b + (x1b - x0b) * 0.62
        sy0 = y0b + (y1b - y0b) * 0.62 + 1
        st = inner & (X >= sx0) & (X < sx0 + 2) & (Y >= sy0) & (Y < sy0 + q(3.4))
        a[st] = code('iron', 2)
        a[inner & (X >= sx0) & (X < sx0 + 2) & (np.floor(Y) == int(sy0 + q(3.4)))] = code('iron', 4)
        hang |= hb | st
    # the shade of whatever hangs, on the floor east and down of it
    if hang.any():
        sh = np.zeros(a.shape, bool)
        sh[2:, 3:] = hang[:-2, :-3]
        sh &= inner & ~hang & (Y > G['crown'] + q(2.2))
        a[sh] = np.where(a[sh] % 8 > 0, a[sh] - 1, a[sh])

    # --- the cornice -------------------------------------------------------------------------------
    hwc, corn = G['hwc'], G['corn']
    cm = (dxa <= hwc) & (Y >= ybt - corn) & (Y < ybt)
    cy_ = (Y - (ybt - corn)) / max(1, corn)                                       # 0 at its top, 1 at its foot
    ct = 3.4 + 1.4 * (Y < ybt - corn + 1) - 0.4 * (cy_ > 0.35) - 1.0 * (cy_ > 0.6) - 0.8 * (Y >= ybt - 1)
    ct = ct + 0.9 * ((cy_ > 0.55) & (cy_ < 0.75)) - 1.0 * (X > cx + hwc * 0.55) + 0.5 * (X < cx - hwc * 0.6)   # the slab, its cove, a lit bead
    # in lengths: each a little off the next in tone, the joints a tone down with a lit west edge beside
    seg = q(1.6)
    sc_ = np.floor((X - (cx - hwc)) / seg).astype(int)
    sf_ = (X - (cx - hwc)) / seg - sc_
    ct = ct + rng.uniform(-0.35, 0.35, 64)[sc_ % 64] - 0.9 * ((sf_ < 1.0 / seg) & (cy_ > 0.3)) + 0.5 * ((sf_ >= 1.0 / seg) & (sf_ < 2.0 / seg) & (cy_ > 0.3))
    paint(a, cm, ('plaster', 'plaster', 'plaster_warm'), ct)
    fil = cm & (np.floor(Y) == int(ybt - corn + q(0.7)))                        # the fillet's groove
    a[fil] = np.where(a[fil] % 8 > 1, a[fil] - 2, a[fil])
    _marks(a, cm & (Y > ybt - corn + q(0.8)) & (Y < ybt - 2), rng, 6, None, ('plaster_warm', 5), length=(2, 3))
    # dentils under it: little blocks in the cornice's shade on the boards
    dn = face & (Y >= ybt) & (Y < ybt + q(0.9)) & (((X - cx + 99 * q(1.2)) // q(1.2)) % 2 == 0) & ~opening
    paint(a, dn, ('plaster', 'plaster', 'plaster_warm'), 2.9 - 0.8 * (X > cx) + 1.0 * ((X - cx + 99 * q(1.2)) % q(1.2) < 1))
    under = face & (Y >= ybt) & (Y < ybt + q(1.3)) & ~dn
    a[under] = np.where(a[under] % 8 > 0, a[under] - 1, a[under])

    # --- the cap: a lead dome on eight ribs ---------------------------------------------------------
    hwr, yce = G['hwr'], G['yce']
    R, Hd = float(hwr), float(G['cap_h'])
    yc0 = yce - R * k                                               # the dome's foot circle's centre on screen
    ss = np.arange(-R, R + 0.01, 0.34)
    sx_, sd_ = np.meshgrid(ss, ss)
    rr = (sx_ / R) ** 2 + (sd_ / R) ** 2
    ins = rr <= 1.0
    sx_, sd_, rr = sx_[ins], sd_[ins], rr[ins]
    sz = Hd * np.power(np.clip(1 - rr, 0, 1), 0.62)                 # a little fuller than a sphere at the shoulder
    py_ = np.floor(yc0 - sd_ * k - sz + PAD).astype(int)
    px_ = np.floor(cx + sx_).astype(int)
    ok = (py_ >= 0) & (py_ < a.shape[0]) & (px_ >= 0) & (px_ < a.shape[1])
    sx_, sd_, sz, rr, py_, px_ = sx_[ok], sd_[ok], sz[ok], rr[ok], py_[ok], px_[ok]
    pix = py_ * a.shape[1] + px_
    order = np.lexsort((sd_, pix))                                  # per texel, the nearest point first
    first = np.ones(order.size, bool)
    first[1:] = pix[order][1:] != pix[order][:-1]
    sel = order[first]
    nx_, nd_, nz_ = sx_[sel] / R ** 2, sd_[sel] / R ** 2, sz[sel] / max(1.0, Hd) ** 2 + 1e-6
    nn = np.sqrt(nx_ ** 2 + nd_ ** 2 + nz_ ** 2)
    td = 2.2 + 2.6 * lam(nx_ / nn, -nd_ / nn, nz_ / nn)
    phi = np.arctan2(sd_[sel], sx_[sel])
    fr = (phi / (math.pi / 6)) % 1.0
    rib = (fr < 0.07) | (fr > 0.93)
    ribl = (fr >= 0.07) & (fr < 0.14)
    td = np.where(rib, td + 1.1 * (sx_[sel] < 0) - 0.3, td)
    td = np.where(ribl, td - 0.7, td)                               # each roll's shade on the sheet beside it
    hz = sz[sel] / max(1.0, Hd)
    seam = (np.abs(hz - 0.42) < 0.03) | (np.abs(hz - 0.76) < 0.03)
    td = np.where(seam & ~rib, td - 0.9, td)                        # the sheets' drips, across
    panel = np.floor((phi + math.pi) / (math.pi / 6)).astype(int)
    td = td + np.array([0.2, -0.1, 0.15, -0.2, 0.1, 0.0, -0.15, 0.2, -0.05, 0.25, -0.2, 0.05])[panel % 12] * (~rib)
    lap = (np.abs(hz - 0.22) < 0.025) | (np.abs(hz - 0.58) < 0.025)
    td = np.where(lap & ~rib & ~seam, td + 0.8, td)                 # the lit lip of each sheet's lap
    td = np.where(rr[sel] > 0.86, td - 0.6 * (sx_[sel] > 0), td)    # the east rim turning away
    dome = np.zeros(a.shape, bool)
    dome.flat[pix[sel]] = True
    tdm = np.zeros(a.shape)
    tdm.flat[pix[sel]] = td
    paint(a, dome, ('slate_cool', 'slate', 'slate_warm'), tdm + 0.4)
    # the lead's white bloom in runs down the sheets under the laps, and a few dents
    _marks(a, dome, rng, 18, ('stone_cool', 5), None, length=(2, 3), vertical=True)
    _marks(a, dome, rng, 8, None, ('slate_warm', 5), length=(2, 2))
    # the dome's foot: a lead roll round it, lit on its west
    foot = (dxa <= R) & (np.abs(Y - (yc0 + k * np.sqrt(np.clip(R * R - (X - cx) ** 2, 0, None)))) < q(0.6)) & (Y > yc0)
    paint(a, foot & ~opening, 'iron', 3.4 - 1.6 * (X > cx + R * 0.3) + 0.6 * (X < cx - R * 0.5))
    yap = yc0 - Hd
    # its shade on the cornice under the eave
    cs = cm & (Y >= ybt - corn) & (Y < ybt - corn + q(0.8)) & ~dome
    a[cs] = np.where(a[cs] % 8 > 1, a[cs] - 2, a[cs])
    # the finial: a lead boss, a brass ball, an iron rod and a vane pointing west
    br = q(1.3)
    by = yap - q(1.1)
    bm_ = ((X - cx) / br) ** 2 + ((Y - by) / br) ** 2 <= 1
    nxb, nyb = (X - cx) / br, (Y - by) / br
    paint(a, bm_, ('brass', 'brass', 'brass_warm'), 2.8 + 2.4 * lam(nxb, nyb * 0.6, np.sqrt(np.clip(1 - nxb * nxb - nyb * nyb, 0, 1))))
    boss = (np.abs(X - cx) < q(1.0)) & (Y >= yap - q(0.3)) & (Y < yap + q(0.8))
    paint(a, boss, 'iron', 3.0 - 1.2 * (X > cx))
    rod_top = by - br - q(4.4)
    rod = (X >= cx - 1) & (X < cx + 1) & (Y >= rod_top) & (Y < by - br + 1)
    paint(a, rod, 'iron', 3.4 - 1.4 * (X >= cx))
    vy = rod_top - 1
    vane = (Y >= vy) & (Y < vy + 2) & (X >= cx - q(2.6)) & (X < cx + q(2.3))
    paint(a, vane, 'iron', 3.6 - 1.4 * (Y >= vy + 1))
    head = _tri(X, Y, (cx - q(2.6) - q(1.2), vy + 1), (cx - q(2.6) + 1, vy - q(0.8)), (cx - q(2.6) + 1, vy + 2 + q(0.8)))
    paint(a, head, 'iron', 3.2 - 1.0 * (Y > vy + 1))
    tail = _tri(X, Y, (cx + q(2.3) - 1, vy + 1), (cx + q(2.3) + q(1.3), vy - q(1.1)), (cx + q(2.3) + q(1.3), vy + 2 + q(1.1)))
    tail &= ~((X - (cx + q(2.3))) > (np.abs(Y - vy - 1) * 0.9 + q(0.8)))
    paint(a, tail, 'iron', 2.8 - 0.8 * (Y > vy + 1))

    p = Pic(Wb, Hb + PAD, 0, 0)
    p.a = a
    finish(p)

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
    """The bell where it came down, in the street below its cupola: it landed on its lip and stands
    there a little askew, a crack running up from the lip where it struck the setts; the snapped stub of
    its old headstock still bolted on its crown, splintered, its strap twisted; dents from the fall and
    green running down from its bands where it has stood out in the rain since. Bronze as a form: lit
    down the west and over the shoulder, the core shadow east of the middle, a bounce at the east rim;
    three cast bands with their lit lips, the soundbow thick
    over the lip, whose front edge curves round the mouth below. A slate and a splinter it brought down
    lie by it. Foot: the middle of its lip on the setts."""
    rng = np.random.default_rng(seed)
    W, H = q(w + 8), q(h + 12)
    ax, ay = W // 2, H - q(1.4)
    p = Pic(W, H, ax, ay)
    a = p.a
    Y, X = grid(a)
    Hb, R = q(8.0), q(4.1)
    ry = R * 0.34                                                    # the lip's circle, seen from above
    top = ay - ry - Hb
    lean = 0.07                                                      # it stands a little askew, its crown east
    cxs = ax + (ay - Y) * lean
    f = np.clip((Y - top) / Hb, 0, 1)
    half = R * (0.44 + 0.10 * np.sin(np.clip(f / 0.18, 0, 1) * math.pi / 2) + 0.46 * f ** 2.4)
    u = (X - cxs) / np.maximum(1.0, half)
    ub = np.clip(u, -1, 1)
    yb = ay - ry + ry * np.sqrt(1 - ub * ub)                         # the lip's front edge
    body = (np.abs(u) <= 1) & (Y >= top + q(0.6)) & (Y < yb)
    # the crown, a dome over the shoulder
    crown = (((X - (ax + Hb * lean)) / (R * 0.44)) ** 2 + ((Y - (top + q(0.7))) / q(1.3)) ** 2 <= 1) & (Y < top + q(0.8))
    # the light across the form in clean bands (the west rim, the lit band, the highlight, the body, the
    # core shadow, the bounce at the east rim), each band a tone, so the bronze reads smooth and round
    edges_u = (-1.01, -0.55, 0.05, 0.50, 1.01)
    tones_u = (3.0, 4.0, 3.0, 2.0)
    t = np.zeros(a.shape)
    for (u0, u1), tv in zip(zip(edges_u[:-1], edges_u[1:]), tones_u):
        t = np.where((u >= u0) & (u < u1), tv, t)
    t = t + 0.6 * (f < 0.25) * (u < 0.3)                             # the shoulder turned up to the light
    bands = (q(2.4), Hb - q(1.8))
    for bs in bands:
        yy_ = top + bs
        t = np.where((Y >= yy_ - 0.5) & (Y < yy_ + 1.5), t - 1.0, t)       # a cast band, two rows
    t = np.where((Y >= yb - q(1.2)), t + 0.5 - 1.2 * (Y >= yb - 1), t)          # the soundbow, and the lip's under edge
    bronze = ('timber_warm', 'brass', 'brass')
    paint(a, body, bronze, t, lo=0, hi=4)
    tc = 2.2 + 2.0 * lam((X - (ax + Hb * lean)) / (R * 0.44), 0.0, 0.8)
    paint(a, crown & ~body, bronze, tc, lo=0, hi=4)
    # the casting's skin: patches of the warm sibling at the same tone (shape, not value: house-style 4)
    for _ in range(16):
        ys_, xs_ = np.nonzero(body & (np.abs(u) < 0.85) & (f > 0.15) & (f < 0.9))
        if ys_.size == 0:
            break
        i = int(rng.integers(0, ys_.size))
        y_, x_ = int(ys_[i]), int(xs_[i])
        blk_ = np.zeros(a.shape, bool)
        blk_[y_:y_ + 2, x_:x_ + int(rng.integers(2, 4))] = True
        blk_ &= body & (a // 8 == V.FI['brass'])
        a[blk_] = V.FI['brass_warm'] * 8 + a[blk_] % 8
    # green run down from the bands, on the shaded side
    for _ in range(2):
        gx = ax + rng.uniform(0.25, 0.6) * R
        gy = top + bands[int(rng.integers(0, len(bands)))] + 1
        run = body & (np.abs(X - gx - (ay - Y) * lean) < 1.0) & (Y >= gy) & (Y < gy + q(rng.uniform(0.8, 1.8)))
        a[run] = code('leaf_cool', 2)
    # dents from the fall: a dark pit, a lit lip over it
    _marks(a, body & (f > 0.45) & (f < 0.9) & (u < 0.2) & (u > -0.7), rng, 2, ('timber_warm', 1), ('brass', 4), length=(2, 2))
    # the crack up from the lip where it struck, zigzag, its west edge lit
    cxk, cyk = ax - R * 0.05, ay - 1
    for k in range(4):
        cyk -= 2
        cxk += (1 if k % 3 == 0 else (-1 if k % 3 == 1 else 0))
        for (dx_, c_) in ((0, ('timber_warm', 1)),):
            yy, xx = int(cyk), int(cxk) + dx_
            for d_ in (0, 1):
                if 0 <= yy + d_ < H and 0 <= xx < W and body[yy + d_, xx]:
                    a[yy + d_, xx] = code(*c_)
    # the stub of the old headstock still bolted on the crown, snapped, its strap twisted
    cx0, cy0 = ax + Hb * lean, top
    x0b, y0b, x1b, y1b = cx0 + q(0.8), cy0 - q(0.3), cx0 - q(3.4), cy0 - q(1.4)
    stub = bar(a, x0b, y0b, x1b, y1b, q(0.7), 'timber', 3)
    ux_, uy_ = x1b - x0b, y1b - y0b
    Ls = math.hypot(ux_, uy_)
    al = ((X - x0b) * ux_ + (Y - y0b) * uy_) / Ls
    ac = (-(X - x0b) * uy_ + (Y - y0b) * ux_) / Ls
    paint(a, stub, ('timber_cool', 'timber', 'timber_warm'), 2.8 + 1.3 * (ac > q(0.35)) - 1.2 * (ac < -q(0.4)) + 0.4 * (al > Ls * 0.5))
    _marks(a, stub & (al < Ls - q(1.0)), rng, 3, None, None, length=(2, 3))
    a[stub & (al > Ls - q(0.6))] = code('plaster_warm', 2)                            # the raw break
    for sp in (-1.0, 1.0):                                                             # its splinters
        sm = (np.abs(ac - sp * q(0.5)) < 0.7) & (al > Ls - q(0.4)) & (al < Ls + q(0.9))
        a[sm & (a < 0)] = code('plaster_warm', 3)
    strap = stub & (np.abs(al - Ls * 0.28) < 1.0)
    a[strap] = code('iron', 2)
    a[strap & (ac > 0)] = code('iron', 4)
    can = (np.abs(X - cx0) < q(1.1)) & (Y >= cy0 - q(1.0)) & (Y < cy0 + q(0.6)) & ~stub
    paint(a, can, 'iron', 3.0 - 1.4 * (X > cx0))
    # a slate shard and a splinter it brought down
    sl_ = (X >= ax + q(5.6)) & (X < ax + q(7.8)) & (Y >= ay - q(1.2)) & (Y < ay - q(0.2)) & ((X - ax - q(5.6)) > (Y - ay + q(1.2)) * 0.8)
    paint(a, sl_, 'slate', 3.4 - 1.6 * (Y >= ay - q(0.2) - 1))
    spl = (X >= ax - q(8.0)) & (X < ax - q(5.2)) & (Y >= ay - 3) & (Y < ay - 1)
    paint(a, spl, 'plaster_warm', 3.0)
    finish(p, keep=None)
    # trimmed to what is drawn, its foot kept
    ys_, xs_ = np.nonzero(p.a >= 0)
    x0, y0, x1, y1 = xs_.min(), ys_.min(), xs_.max() + 1, max(ys_.max() + 1, ay)
    out = Pic(x1 - x0, y1 - y0, ax - x0, ay - y0)
    out.a = p.a[y0:y1, x0:x1].copy()
    return out
