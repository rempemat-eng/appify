"""Wayside and garden props at density 3 (Claude B, lane B; to-all-assignments-1025: "design the
wayside and garden prop set at density 3 ... troughs, stiles, signposts, gates, beehives, garden
furniture ... each prop must pass review:asset").

Drawn the way the village kit draws (village.py): palette codes on a texel canvas, world px in
(`q` makes texels at ctx.D), every piece a volume lit from the upper left (a lit top and west
face, a mid front, a dark east side and foot), timber as sawn boards with grain, end grain,
splits and nails, stone in courses with moss in the joints, iron with a rust streak. So the
props sit beside Crossroads' approved pieces (the fence, the handcart, the well) at the same
detail, and each passes `npm run review:asset` (its detail bar at least 0.45 of Eastward's prop
band, no flat or 2D part).

    prop(kind, seed) -> village.Pic        kinds in KINDS, each at its size-guide size
    python3 -m scripts.art.native.props_wayside OUT_DIR    writes every kind at density 3 and a sheet

The density must be set (ctx.configure) before this module is imported, as for village.py.
Sizes in world px (footprint w x depth h, standing `up` tall), from the size guide against
Bramble's 25: a stile 28 wide and 17 tall, a fingerpost 26 tall, a field gate 36 x 15, a hive
13 x 19, the potting table 30 x 17, the timber trough 30 x 12, the stone trough 28 x 13,
a skep 12 x 13, the garden bench 32 x 16 (its back two over the guide's 13), a chair 11 x 18. Decorative only: none of them
adds a reward, a cost or a chore.
"""
from __future__ import annotations

import os
import sys

import numpy as np

from . import ctx

if __name__ == '__main__' and not ctx._configured:     # run as a script: draw at the game's density
    from . import load_biome
    ctx.configure(3.0, load_biome('meadow'), {})

from . import village as V  # noqa: E402  (village sizes itself from ctx.D when imported)
from .palette import FI  # noqa: E402
from .village import (_pic, _rect, bar, blob, board, code, ellipse_mask, fill, finish,  # noqa: E402
                      nail, prism, q)

WOOD = ('timber', 'timber_warm', 'timber_cool')


def _shade_under(a, x0, y0, x1, y1, k=1):
    """Darken what is already drawn in a band (the shade a board throws on what is behind it)."""
    sh = _rect(a.shape, x0, y0, x1, y1) & (a >= 0)
    a[sh] = np.maximum((a[sh] // 8) * 8, a[sh] - k)


def _east_dark(a, x0, x1, y0, y1, frac=0.3, k=1):
    """The east `frac` of what is drawn in a box a step darker (turned from the light)."""
    xe = int(x1 - (x1 - x0) * frac)
    _shade_under(a, xe, y0, x1, y1, k)


def _tuft(a, x, yb, rng, n=5, fam='grass', h=3.0):
    """A clump of grass blades at a foot: each blade 1 texel wide, lit tip, dark base."""
    for i in range(n):
        bx = int(x + (i - n / 2) * q(0.7) + rng.integers(-1, 2))
        L = q(rng.uniform(h * 0.5, h))
        lean = rng.choice([-1, 0, 1])
        for k in range(L):
            xx = bx + (lean * k) // max(1, L // 2 + 1)
            t = 1 if k < L // 3 else (3 if k < 2 * L // 3 else 4)
            fill(a, xx, yb - k, xx + 1, yb - k + 1, code(fam, t))


def _post(a, x0, x1, ytop, yb, rng, fam='timber', t=3, cap=True):
    """A square sawn post: a lit west face, a shaded east side, weathered top, grain and a check."""
    w = x1 - x0
    prism(a, x0, ytop, x1, yb, max(2, q(1.0)), fam, t, side=max(2, w // 3))
    lit = _rect(a.shape, x0 + 1, ytop + max(2, q(1.0)) + 1, x0 + max(2, w // 3), yb - 1) & (a == code(fam, t))
    a[lit] = code(fam, min(5, t + 1))
    # the east side face: not a flat dark strip but grain and checks in three tones, its foot in
    # reflected light from the ground
    side = _rect(a.shape, x1 - max(2, w // 3), ytop + max(2, q(1.0)), x1, yb - q(1.5)) & (a == code(fam, max(0, t - 2)))
    ys_, xs_ = np.nonzero(side)
    for y_, x_ in zip(ys_, xs_):
        r = (y_ * 7 + x_ * 3) % 11
        if r < 3:
            a[y_, x_] = code(fam, max(0, t - 3))
        elif r > 8:
            a[y_, x_] = code(fam, max(0, t - 1))
    refl = side & _rect(a.shape, x1 - max(2, w // 3), yb - q(5), x1, yb - q(1.5))
    a[refl] = code(fam, max(0, t - 1))
    for _ in range(max(1, (yb - ytop) // q(5))):
        gx = int(rng.integers(x0 + 1, max(x0 + 2, x1 - w // 3)))
        gy = int(rng.integers(ytop + q(1.5), max(ytop + q(1.6), yb - q(2))))
        fill(a, gx, gy, gx + 1, gy + q(rng.uniform(1.5, 3.0)), code(fam, max(0, t - 1)))
    cx = int(rng.integers(x0 + 1, max(x0 + 2, x1 - w // 3)))
    fill(a, cx, ytop + q(2), cx + 1, ytop + q(2) + q(rng.uniform(3, 6)), code(fam, max(0, t - 2)))  # a check
    if cap:
        fill(a, x0, ytop, x1 - w // 3, ytop + 1, code(fam, min(5, t + 2)))
    fill(a, x0, yb - q(1.5), x1, yb, code(fam, max(0, t - 2)))          # damp at the foot
    fill(a, x0, yb - q(1.5), x1, yb - q(1.5) + 1, code(fam, max(0, t - 1)))      # its tide line
    for xx in range(x0 + 1, x1, 3):                                       # streaks of wet in the damp
        fill(a, xx, yb - q(1.5) + 1, xx + 1, yb - 1, code(fam, max(0, t - 3)))


# ------------------------------------------------------------------------------------------------
def p_stile(seed=0, w=28.0):
    """A step stile in a post and rail fence: the fence's two rails run between its end posts; in the
    middle two taller stile posts carry a lower top rail to step over, and in front of them one wide
    step board on two stubs, seen from above the front (its top a deep lit plane worn pale where feet
    land, its front edge in shade with end grain at each end, the shade it throws under it); nails
    with rust streaks at every joint, tufts at each foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, 8, up=17, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    sa, sb = cx - q(4.6), cx + q(2.4)                  # the stile posts
    # the fence: end posts, two rails each side of the stile, a lower rail across the gap
    for yy, (lx0, lx1) in ((yb - q(12), (x0, sa + q(1))), (yb - q(12), (sb + q(1), x1)),
                           (yb - q(6.5), (x0, x1))):
        board(a, lx0, yy, lx1 - lx0, q(1.7), 0, WOOD[int(rng.integers(0, 3))], 3, rng)
        _shade_under(a, lx0, yy + q(1.7), lx1, yy + q(2.3))
    board(a, sa + q(1), yb - q(9.6), sb - sa, q(1.7), 0, 'timber_warm', 4, rng, split=True)   # the step-over rail
    _shade_under(a, sa + q(1), yb - q(9.6) + q(1.7), sb + q(1), yb - q(9.6) + q(2.3))
    for px_, top_ in ((x0, 14.5), (x1 - q(2.6), 14.0)):
        _post(a, px_, px_ + q(2.6), yb - q(top_), yb, rng, t=3)
    for px_ in (sa, sb):
        _post(a, px_, px_ + q(2.6), yb - q(16.5), yb, rng, t=3)
    # the step: a wide board seen from above the front, on two stubs
    tx0, tx1 = sa - q(2.4), sb + q(5.0)
    ty, depth, th = yb - q(4.2), q(3.6), q(1.3)
    for sx in (tx0 + q(1), tx1 - q(3)):
        _post(a, sx, sx + q(2), ty + th, yb, rng, fam='timber_cool', t=2, cap=False)
    fill(a, tx0, ty - depth, tx1, ty, code('timber_warm', 4))
    fill(a, tx0, ty - depth, tx1, ty - depth + 1, code('timber_warm', 5))
    for k in range(1, 3):                                             # the boards of the step's top
        fill(a, tx0, ty - depth + k * depth // 3, tx1, ty - depth + k * depth // 3 + 1, code('timber', 3))
    worn = ellipse_mask(a.shape, (tx0 + tx1) / 2, ty - depth / 2, (tx1 - tx0) * 0.26, depth * 0.42)
    a[worn & (a == code('timber_warm', 4))] = code('plaster_warm', 4)
    for _ in range(4):
        gx = int(rng.integers(tx0 + 2, tx1 - q(3)))
        gy = int(rng.integers(ty - depth + 1, ty - 1))
        fill(a, gx, gy, gx + q(rng.uniform(1.5, 3)), gy + 1, code('timber_warm', 3))
    board(a, tx0, ty, tx1 - tx0, th, 0, 'timber', 3, rng, split=True)
    fill(a, tx0, ty - depth, tx0 + q(0.8), ty + th, code('timber_warm', 5))      # end grain, lit
    fill(a, tx1 - q(0.8), ty - depth, tx1, ty + th, code('timber', 2))           # end grain, shaded
    _shade_under(a, tx0, ty + th, tx1, ty + th + q(1.0), k=2)
    for nx in (tx0 + q(1.4), tx1 - q(2.4)):
        nail(a, nx, ty + 1, rng=rng)
    for px_ in (x0, sa, sb, x1 - q(2.6)):
        nail(a, px_ + q(0.8), yb - q(11.6), rng=rng)
        nail(a, px_ + q(0.8), yb - q(6.1), rng=rng)
    for fx in (x0 + q(1), sa + q(1.4), sb + q(2.2), x1 - q(1)):
        _tuft(a, fx, yb - 1, rng, n=4)
    return finish(p)


def p_fingerpost(seed=0, arms=(('e', 0), ('w', 1), ('e', 2))):
    """A fingerpost: a tall square post with a pyramid cap and a ball finial, arms of sawn board
    pointing east or west at staggered heights (each with its pointed end, a lit top arris, a shaded
    underside, carved letters in short dark groups and a lit lower lip, the bolt that holds it), a
    diagonal spur where the post meets its stone footing, moss and lichen on the north face."""
    rng = np.random.default_rng(seed)
    p = _pic(8, 6, up=30, side=13)
    a, cx, yb = p.a, p.ax, p.ay
    # the footing: three rough stones round the post foot
    for (dx, w_, h_, t) in ((-q(4.5), q(4.2), q(3.2), 3), (q(1.6), q(4.6), q(3.6), 2), (-q(1.2), q(3.4), q(2.4), 4)):
        V.stone_chunk(a, cx + dx, yb - h_, w_, h_, ('stone', 'stone_warm', 'stone_cool')[t % 3], t, rng)
    px0, px1 = cx - q(1.4), cx + q(1.6)
    _post(a, px0, px1, yb - q(27), yb - q(1.5), rng, t=3, cap=False)
    # the cap: a little pyramid with its lit west slope, and a turned ball
    for i in range(q(1.6)):
        fill(a, px0 - q(0.4) + i, yb - q(27) - i, px1 + q(0.4) - i, yb - q(27) - i + 1,
             code('timber_warm', 4 if i < q(0.8) else 3))
    fill(a, cx, yb - q(27) - q(1.6), cx + q(0.6), yb - q(27), code('timber_warm', 2))
    ball = ellipse_mask(a.shape, cx + 0.5, yb - q(29.2), q(1.1), q(1.1))
    blob(a, ball, 'timber_warm', 3)
    # the arms
    for side, k in arms:
        ay = yb - q(24) + k * q(4.4)
        L = q(rng.uniform(10.5, 12.5))
        th = q(2.6)
        if side == 'e':
            ax0 = px1 - q(0.4)
            board(a, ax0, ay, L, th, 0, ('timber_warm', 'timber')[k % 2], 3 - k % 2, rng, split=k == 1)
            tip = ax0 + L
            for i in range(th):                                         # the pointed end
                c = min(i, th - 1 - i)
                fill(a, tip, ay + i, tip + c + 1, ay + i + 1, code('timber', 3 if i < th / 2 else 2))
            lx0, lx1 = ax0 + q(1.6), tip - q(2)
        else:
            ax0 = px0 + q(0.4) - L
            board(a, ax0, ay, L, th, 0, ('timber_warm', 'timber')[k % 2], 4, rng, split=k == 1)
            for i in range(th):
                c = min(i, th - 1 - i)
                fill(a, ax0 - c - 1, ay + i, ax0, ay + i + 1, code('timber_warm', 5 if i < th / 2 else 3))
            lx0, lx1 = ax0 + q(1.4), px0 - q(1.2)
        _shade_under(a, ax0, ay + th, ax0 + L, ay + th + q(0.8))
        # carved letters: groups of short strokes, dark with a lit lower lip
        x = lx0
        while x < lx1 - q(1):
            word = int(rng.integers(2, 5))
            for _ in range(word):
                if x >= lx1 - 1:
                    break
                hgt = int(rng.choice([q(1.2), q(1.2), q(0.8)]))
                y0 = ay + q(0.7)
                fill(a, x, y0, x + 1, y0 + hgt, code('timber', 0))
                fill(a, x + 1, y0 + hgt - 1, x + 2, y0 + hgt, code('timber_warm', 5))
                if rng.random() < 0.35:
                    fill(a, x, y0, x + 2, y0 + 1, code('timber', 0))
                x += 2 + int(rng.integers(0, 2))
            x += q(0.9)
        fill(a, (px0 + px1) // 2, ay + th // 2 - 1, (px0 + px1) // 2 + 2, ay + th // 2 + 1, code('iron', 4))  # the bolt
        fill(a, (px0 + px1) // 2 + 1, ay + th // 2, (px0 + px1) // 2 + 2, ay + th // 2 + 1, code('iron', 1))
    # moss on the post's foot and lichen spots on the arms
    blob(a, ellipse_mask(a.shape, px0 + q(0.6), yb - q(3.5), q(1.2), q(2.2)) & (a >= 0), 'leaf', 3)
    for _ in range(4):
        m = ellipse_mask(a.shape, cx + rng.uniform(-q(10), q(10)), yb - q(rng.uniform(15, 24)), q(0.7), q(0.5))
        m &= (a >= 0) & (a // 8 != V.FI['iron'])
        a[m] = code('plaster_warm', 3)
    _tuft(a, cx - q(5), yb - 1, rng, n=5)
    _tuft(a, cx + q(5), yb - 1, rng, n=4)
    return finish(p)


def p_field_gate(seed=0, w=36.0):
    """A five-bar field gate between its posts: the hanging post thicker, the latch post square,
    five sawn bars (the top one deepest), the diagonal brace rising from the hanging foot, an upright
    batten in the middle, iron strap hinges with their pins, a latch with its ring; the ground shows
    between the bars; a worn earth patch where it swings, tufts at the posts."""
    rng = np.random.default_rng(seed)
    p = _pic(w, 6, up=17, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    hp0, lp0 = x0, x1 - q(3)
    gx0, gx1 = hp0 + q(4.2), lp0 - q(0.6)
    bars = [(yb - q(14), q(2.4)), (yb - q(11), q(1.8)), (yb - q(8.4), q(1.8)), (yb - q(5.8), q(1.8)), (yb - q(3.2), q(1.8))]
    # the brace and the batten, behind the bars
    bar(a, gx0 + q(1), yb - q(3.0), gx1 - q(3), yb - q(13), max(1.6, q(0.8)), 'timber_cool', 3)
    prism(a, (gx0 + gx1) // 2 - q(1), yb - q(14), (gx0 + gx1) // 2 + q(1), yb - q(2.4), 1, 'timber_cool', 3, side=2)
    # the gate's stiles at each end
    prism(a, gx0, yb - q(14.4), gx0 + q(2), yb - q(2.4), 1, 'timber', 3, side=2)
    prism(a, gx1 - q(2), yb - q(14.4), gx1, yb - q(2.4), 1, 'timber', 3, side=2)
    for k, (by, th) in enumerate(bars):
        board(a, gx0, by, gx1 - gx0, th, 0, WOOD[(k + seed) % 3], (5, 4, 4, 3, 3)[k], rng, split=k in (1, 3))
        for _ in range(3):                                               # weathered streaks along the bar
            sx = int(rng.integers(gx0 + q(2), gx1 - q(5)))
            fill(a, sx, by + th // 2, sx + q(rng.uniform(2, 4)), by + th // 2 + 1, code(WOOD[(k + seed) % 3], 2))
        _east_dark(a, gx0, gx1, by, by + th, frac=0.33)
        _shade_under(a, gx0, by + th, gx1, by + th + q(0.6))
        nail(a, gx0 + q(0.6), by + 1, rng=rng)
        nail(a, (gx0 + gx1) // 2 - q(0.4), by + 1, rng=rng)
        nail(a, gx1 - q(1.4), by + 1, rng=rng)
    _east_dark(a, gx0, gx1, yb - q(14.4), yb - q(2.4), frac=0.15)
    # posts in front
    _post(a, hp0, hp0 + q(4), yb - q(17), yb, rng, t=3)
    _post(a, lp0, lp0 + q(3), yb - q(16), yb, rng, t=3)
    # hinges: iron straps over the top and bottom bars, pins on the hanging post
    for (by, th) in (bars[0], bars[4]):
        fill(a, hp0 + q(3.2), by, gx0 + q(6), by + max(2, q(0.8)), code('iron', 2))
        fill(a, hp0 + q(3.2), by, gx0 + q(6), by + 1, code('iron', 4))
        fill(a, hp0 + q(2.4), by - 1, hp0 + q(3.6), by + max(3, q(1.4)), code('iron', 1))
        fill(a, gx0 + q(5), by + max(2, q(0.8)), gx0 + q(5) + 1, by + max(2, q(0.8)) + q(1.4), code('fox', 2))
    # the latch and its ring
    ly = bars[0][0] + q(2.6)
    fill(a, gx1 - q(3), ly, lp0 + q(1.4), ly + 2, code('iron', 3))
    fill(a, gx1 - q(3), ly, lp0 + q(1.4), ly + 1, code('iron', 5))
    ring = ellipse_mask(a.shape, gx1 - q(1.2), ly + q(1.8), q(0.9), q(1.1)) & ~ellipse_mask(a.shape, gx1 - q(1.2), ly + q(1.8), q(0.45), q(0.6))
    a[ring] = code('iron', 2)
    # tufts
    for fx in (hp0 + q(1), hp0 + q(4.5), lp0, lp0 + q(3.2), (gx0 + gx1) // 2):
        _tuft(a, fx, yb - 1, rng, n=4)
    return finish(p)


def p_beehive(seed=0):
    """A painted bee hive on its stand: splayed legs, a floor with a landing board and its entrance
    slot (bees at it), three lifts of white-painted boards stepping out as they rise (each lit on
    top, shaded on the east, the paint worn to grey at the corners), a gabled roof of boards with its
    ridge, the gable end lit, a brick on the roof to hold it down."""
    rng = np.random.default_rng(seed)
    p = _pic(13, 8, up=20, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    hw = q(6)
    # the stand's legs
    for sx in (-1, 1):
        bar(a, cx + sx * q(5.4), yb - 1, cx + sx * q(4.2), yb - q(3.4), max(1.4, q(0.6)), 'timber_cool', 2 if sx > 0 else 3)
    fill(a, cx - q(6), yb - q(4.2), cx + q(6), yb - q(3.2), code('timber', 2))
    # the floor and landing board
    prism(a, cx - hw, yb - q(5.4), cx + hw, yb - q(4.0), 1, 'timber', 3, side=q(1))
    for i in range(q(1.6)):
        fill(a, cx - q(3.6) - i, yb - q(4.4) + i // 2, cx + q(3.6) + i, yb - q(4.4) + i // 2 + 1, code('timber_warm', 4 - i // 2))
    # three lifts, each a box of painted boards, stepping out
    y = yb - q(5.4)
    for k, (lh, out) in enumerate(((3.6, 0.0), (3.6, 0.6), (3.2, 1.2))):
        h = q(lh)
        lx0, lx1 = cx - hw - q(out), cx + hw + q(out)
        prism(a, lx0, y - h, lx1, y, max(2, q(0.9)), 'plaster', 4, side=q(2.6))
        front = _rect(a.shape, lx0 + 1, y - h + q(1.0), lx1 - q(2.6), y - 1) & (a == code('plaster', 4))
        ys_, xs_ = np.nonzero(front)
        for y_, x_ in zip(ys_, xs_):
            u = (x_ - lx0) / max(1, lx1 - lx0)
            r = (y_ * 5 + x_ * 11) % 13
            if u < 0.25 and r < 6:
                a[y_, x_] = code('plaster', 5)
            elif u > 0.6 and r < 7:
                a[y_, x_] = code('plaster', 3)
            elif r == 12:
                a[y_, x_] = code('plaster_warm', 3)
        # board seams and worn paint
        fill(a, lx0, y - h // 2, lx1 - q(1.6), y - h // 2 + 1, code('plaster', 2))
        for _ in range(3):
            wx = int(rng.integers(lx0 + 1, lx1 - q(2)))
            wy = int(rng.integers(y - h + 2, y - 2))
            fill(a, wx, wy, wx + q(rng.uniform(1, 2.2)), wy + 2, code('stone', 3))
        fill(a, lx0, y - h, lx0 + 1, y, code('stone_warm', 4))
        _shade_under(a, lx0, y, lx1, y + q(0.8))
        if k == 0:                                                     # the entrance slot
            fill(a, cx - q(3), y - q(1.2), cx + q(3), y - 1, code('soot', 0))
        y -= h
    # the roof: two board slopes and a ridge, the gable end lit
    ry, rh = y, q(3.4)
    for i in range(rh):
        ex = q(1.6) + (rh - i) * q(5.2) // rh
        row_x0, row_x1 = cx - ex - q(1.4), cx + ex + q(1.4)
        band = i % q(1.4)
        fill(a, row_x0, ry - i, cx, ry - i + 1, code('slate', (5, 4, 3)[min(2, band)] if band else 2))
        fill(a, cx, ry - i, row_x1, ry - i + 1, code('slate', (3, 2, 1)[min(2, band)] if band else 0))
        for j in range(row_x0 + 2 + (i % 3), row_x1 - 2, q(2.6)):           # board ends along each course
            fill(a, j, ry - i, j + 1, ry - i + 1, code('slate', 1 if j > cx else 2))
    fill(a, cx - q(8), ry, cx + q(8), ry + q(0.8), code('timber', 2))   # the eave board
    fill(a, cx - q(8), ry, cx + q(8), ry + 1, code('timber', 4))
    fill(a, cx - q(1.6), ry - rh - 1, cx + q(1.6), ry - rh + 1, code('timber_warm', 3))
    # the brick on the roof
    prism(a, cx + q(1), ry - rh + q(0.6), cx + q(4.2), ry - rh + q(2.4), 1, 'clay', 3, side=2)
    # bees: dark specks with a lit wing, round the entrance
    for _ in range(5):
        bx = int(cx + rng.uniform(-q(6), q(6)))
        by = int(yb - q(rng.uniform(4.5, 8)))
        fill(a, bx, by, bx + 2, by + 1, code('brass', 2))
        fill(a, bx, by - 1, bx + 1, by, code('sky', 4))
    _tuft(a, cx - q(6.5), yb - 1, rng, n=5)
    _tuft(a, cx + q(6.2), yb - 1, rng, n=4)
    return finish(p)


def p_potting_table(seed=0, w=30.0):
    """A potting table against a garden wall: a top of boards seen from above (soil spilled on it,
    a stack of clay pots, a seed tray of seedlings, a trowel), a lower shelf with pots and a coiled
    hose, four legs with a rail, a watering can at its foot."""
    rng = np.random.default_rng(seed)
    p = _pic(w, 8, up=18, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    top_y = yb - q(11)
    # legs and the shelf
    for lx in (x0 + q(1), x1 - q(3)):
        prism(a, lx, top_y, lx + q(2), yb, 1, 'timber_cool', 3, side=2)
    sy = yb - q(4)
    fill(a, x0 + q(1), sy - q(1.6), x1 - q(1), sy, code('timber', 3))
    fill(a, x0 + q(1), sy - q(1.6), x1 - q(1), sy - q(1.6) + 1, code('timber', 4))
    fill(a, x0 + q(1), sy, x1 - q(1), sy + q(0.8), code('timber', 1))
    # on the shelf: pots upside down and a hose
    for k in range(3):
        px = x0 + q(4) + k * q(3.4)
        prism(a, px, sy - q(1.6) - q(3), px + q(3), sy - q(1.6), 1, 'clay', 3 + (k % 2), side=2)
    hose = ellipse_mask(a.shape, x1 - q(8), sy - q(3.4), q(4), q(1.9)) & ~ellipse_mask(a.shape, x1 - q(8), sy - q(3.4), q(2.6), q(1.0))
    blob(a, hose, 'grass_cool', 2)
    for i in range(3):
        m = ellipse_mask(a.shape, x1 - q(8), sy - q(3.4), q(4 - i * 0.45), q(1.9 - i * 0.3)) & hose
        a[m & ((np.arange(a.shape[1])[None, :] + i) % 3 == 0)] = code('grass_cool', 1)
    # the top: boards seen from above, its front edge, soil, pots, tray, trowel
    for k in range(3):
        yy = top_y - q(5.4) + k * q(1.8)
        board(a, x0, yy, x1 - x0, q(1.8) - 1, 0, WOOD[(k + seed) % 3], 4, rng, split=k == 1, grain=True)
    fill(a, x0, top_y, x1, top_y + q(1.4), code('timber', 2))
    fill(a, x0, top_y, x1, top_y + 1, code('timber', 3))
    _shade_under(a, x0, top_y + q(1.4), x1, top_y + q(2.4), k=2)
    soil = ellipse_mask(a.shape, cx + q(2), top_y - q(2.4), q(5), q(1.4))
    for _ in range(2):
        soil |= ellipse_mask(a.shape, cx + q(rng.uniform(-2, 6)), top_y - q(rng.uniform(1.5, 3.5)), q(1.6), q(0.8))
    blob(a, soil & (a >= 0), 'earth', 2)
    # a stack of pots
    for k in range(3):
        bx0 = x0 + q(2.5) - k * 0
        by = top_y - q(3.2) - k * q(1.6)
        prism(a, bx0 + k, by - q(2.4), bx0 + q(4) - k, by, 1, 'clay', 4 - (k % 2), side=2)
        fill(a, bx0 + k, by - q(2.4), bx0 + q(4) - k, by - q(2.4) + 1, code('clay', 5))
    # the seed tray of seedlings
    tx0, tx1 = cx + q(4), x1 - q(2)
    prism(a, tx0, top_y - q(4.6), tx1, top_y - q(1.2), q(1.8), 'timber_cool', 3, side=2)
    fill(a, tx0 + 1, top_y - q(4.4), tx1 - 2, top_y - q(3.0), code('earth', 1))
    for sx in range(tx0 + q(0.8), tx1 - q(1), q(1.4)):
        fill(a, sx, top_y - q(5.2), sx + 2, top_y - q(4.2), code('leaf', 4))
        fill(a, sx, top_y - q(5.2), sx + 1, top_y - q(4.8), code('leaf', 5))
        fill(a, sx + 1, top_y - q(4.4), sx + 2, top_y - q(3.4), code('leaf', 2))
    # the trowel
    bar(a, cx - q(4.5), top_y - q(2.2), cx - q(1.2), top_y - q(1.6), max(1, q(0.4)), 'iron', 4)
    bar(a, cx - q(7.5), top_y - q(2.4), cx - q(4.6), top_y - q(2.2), max(1, q(0.5)), 'timber_warm', 3)
    # the watering can at its foot
    can_x = x0 - q(1)
    prism(a, can_x, yb - q(5), can_x + q(4.4), yb, 1, 'iron', 3, side=2)
    bar(a, can_x + q(4.2), yb - q(2.4), can_x + q(7.4), yb - q(5.4), max(1, q(0.4)), 'iron', 3)
    fill(a, can_x + q(7), yb - q(6), can_x + q(8.2), yb - q(5.2), code('iron', 4))
    arc = ellipse_mask(a.shape, can_x + q(2.2), yb - q(5), q(2), q(1.6)) & ~ellipse_mask(a.shape, can_x + q(2.2), yb - q(5), q(1.2), q(1.0))
    a[arc & (np.arange(a.shape[0])[:, None] < yb - q(5))] = code('iron', 2)
    _tuft(a, x0 + q(2), yb - 1, rng, n=4)
    _tuft(a, x1 - q(1.5), yb - 1, rng, n=5)
    return finish(p)


def p_trough_timber(seed=0, w=30.0):
    """A plank trough on two sleepers at a wayside spring: horizontal boards with their seams and
    grain, end boards showing their end grain, two iron bands with rivets and rust, the top rim a lit
    plane round the water (the far wall lit inside, the water darker toward the near rim, a band of
    sky, a floating leaf), moss along the waterline at the shaded end, a wet dark patch below the
    east end where it leaks, a spout pipe from the west on a post."""
    rng = np.random.default_rng(seed)
    p = _pic(w, 6, up=14, side=5)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    # the wet patch under the east end
    wet = ellipse_mask(a.shape, x1 - q(4), yb - q(0.6), q(5), q(1.2))
    a[wet] = code('earth', 1)
    # sleepers
    for sx in (x0 + q(2), x1 - q(8)):
        prism(a, sx, yb - q(2.4), sx + q(6), yb, 1, 'timber_cool', 2, side=2)
    body_top, body_bot = yb - q(5.4), yb - q(2.0)
    V.planks(a, x0, body_top, x1, body_bot, rng, fams=WOOD, base=3, width=2.2, vertical=False)
    fill(a, x1 - q(2.4), body_top, x1, body_bot, code('timber', 2))              # the east end in shade
    fill(a, x0, body_top, x0 + q(1.6), body_bot, code('timber_warm', 4))        # the west end board lit
    for gy in range(body_top + 2, body_bot - 1, q(2)):
        fill(a, x0 + q(0.4), gy, x0 + q(1.2), gy + 1, code('timber_warm', 3))    # its end grain rings
    for bx in (x0 + q(6), x1 - q(8)):
        fill(a, bx, body_top, bx + q(1.6), body_bot, code('iron', 2))
        fill(a, bx, body_top, bx + 1, body_bot, code('iron', 4))
        for ry in (body_top + q(1.6), body_bot - q(1.8)):
            fill(a, bx + q(0.4), ry, bx + q(0.4) + 2, ry + 2, code('iron', 5))
            fill(a, bx + q(0.4) + 1, ry + 2, bx + q(0.4) + 2, ry + 2 + q(1.2), code('fox', 2))
    # the rim and the water
    rim_y0, rim_y1 = body_top - q(6.4), body_top
    fill(a, x0, rim_y0, x1, rim_y1, code('timber_warm', 4))
    fill(a, x0, rim_y0, x1, rim_y0 + 1, code('timber_warm', 5))
    fill(a, x1 - q(2), rim_y0, x1, rim_y1, code('timber_warm', 3))
    fill(a, x0, rim_y1 - q(1.2), x1, rim_y1, code('timber', 3))                   # the near rim's face
    ix0, ix1, iy0, iy1 = x0 + q(1.4), x1 - q(2.2), rim_y0 + q(1.0), rim_y1 - q(1.4)
    fill(a, ix0, iy0, ix1, iy0 + q(0.8), code('timber', 4))                       # the far wall inside
    for yy in range(iy0 + q(0.8), iy1):
        f = (yy - iy0) / max(1, iy1 - iy0)
        fill(a, ix0, yy, ix1, yy + 1, code('water', 3) if f < 0.35 else (code('water', 2) if f < 0.7 else code('water_cool', 1)))
    fill(a, ix0, iy0 + q(0.8), ix1, iy0 + q(0.8) + 1, code('water', 4))           # the waterline
    fill(a, ix0 + q(3), iy0 + q(1.6), ix0 + q(10), iy0 + q(1.6) + 1, code('sky', 4))
    fill(a, ix0 + q(13), iy0 + q(2.2), ix1 - q(3), iy0 + q(2.2) + 1, code('sky', 3))
    for _ in range(3):                                                             # ripples under the spout
        rx = ix0 + q(1) + int(rng.integers(0, q(3)))
        fill(a, rx, iy0 + q(1.2), rx + q(1.6), iy0 + q(1.2) + 1, code('water', 5))
    lf = ellipse_mask(a.shape, ix1 - q(6), iy0 + q(2.0), q(1.2), q(0.6))
    a[lf] = code('clay', 4)
    fill(a, ix1 - q(6), iy0 + q(1.8), ix1 - q(5), iy0 + q(2.0), code('clay', 2))
    blob(a, _rect(a.shape, ix1 - q(5), iy1 - q(0.8), ix1, iy1), 'leaf', 3)         # moss at the shaded end
    # the spout: a pipe from the west on a short post, its trickle
    _post(a, x0 - q(4), x0 - q(1.6), rim_y0 - q(1.6), yb, rng, t=3)
    fill(a, x0 - q(2), rim_y0 - q(1.2), x0 + q(2.6), rim_y0 - q(0.2), code('iron', 3))
    fill(a, x0 - q(2), rim_y0 - q(1.2), x0 + q(2.6), rim_y0 - q(1.2) + 1, code('iron', 5))
    fill(a, x0 + q(1.6), rim_y0 - q(0.2), x0 + q(2.4), iy0 + q(1.6), code('water', 4))
    fill(a, x0 + q(1.6), rim_y0 - q(0.2), x0 + q(1.6) + 1, iy0 + q(1.6), code('water', 5))
    _tuft(a, x0 - q(5), yb - 1, rng, n=5)
    _tuft(a, x1 + q(1), yb - 1, rng, n=5, fam='grass_cool')
    return finish(p)


def p_trough_stone(seed=0, w=28.0):
    """A hewn stone trough at a spring: one block, its rim a deep lit plane seen from above round the
    water (worn rounded at the corners, a chip out of the near lip), the front face dressed in short
    diagonal chisel strokes with a lit west arris, the east end in shade, moss along the foot and up
    the shaded corner, lichen on the rim, a worn notch where the overflow runs and its wet streak,
    the water deep under the near lip with the sky's band on it and a leaf afloat."""
    rng = np.random.default_rng(seed)
    p = _pic(w, 8, up=13, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    face_top, top_y = yb - q(6.2), yb - q(12.6)
    side_w = q(2.6)
    # the front face: tooled stone, its east end turned from the light
    front = (X >= x0) & (X < x1 - side_w) & (Y >= face_top) & (Y < yb)
    tt = np.full(a.shape, 3)
    for _ in range(int(w * 1.4)):                                     # chisel marks in clusters
        mx, my = int(rng.integers(x0 + 2, x1 - side_w - 2)), int(rng.integers(face_top + 2, yb - q(1.8)))
        L_ = int(rng.integers(2, 4))
        for k in range(L_):
            if face_top <= my + k < yb:
                tt[my + k, mx + k: mx + k + 2] = 2
        tt[my, mx - 1: mx] = 4
    for _ in range(2):                                                # two cracks running down
        cx_ = int(rng.integers(x0 + q(4), x1 - side_w - q(4)))
        y_ = face_top
        while y_ < yb - q(1.6):
            tt[y_, cx_] = 1
            tt[y_, cx_ - 1] = 4
            y_ += 1
            cx_ += int(rng.choice([-1, 0, 0, 1]))
    tt[(X < x0 + q(1.0))] = 4
    tt[(Y >= yb - q(1.6))] = 2
    a[front] = FI['stone'] * 8 + tt[front]
    sidef = (X >= x1 - side_w) & (X < x1) & (Y >= face_top - q(0.8) + (X - (x1 - side_w)) * 0) & (Y < yb)
    st = np.where(((X + 2 * Y) % 5) == 0, 0, 1)
    a[sidef] = FI['stone_cool'] * 8 + st[sidef]
    # the rim: a deep top plane, lit, its corners rounded, its far edge brightest
    rim = (X >= x0) & (X < x1) & (Y >= top_y) & (Y < face_top)
    for (cxr, cyr) in ((x0, top_y), (x1 - 1, top_y)):
        rim &= ~((np.abs(X - cxr) + np.abs(Y - cyr)) < q(1.2))
    a[rim] = code('stone_warm', 4)
    a[rim & (Y == top_y)] = code('stone_warm', 5)
    a[rim & (X >= x1 - side_w)] = code('stone_warm', 3)
    a[rim & (Y >= face_top - 1)] = code('stone', 5)                         # the near arris catches the light
    # the opening and the water
    ix0, ix1, iy0, iy1 = x0 + q(2.0), x1 - q(3.2), top_y + q(1.4), face_top - q(1.6)
    fill(a, ix0, iy0, ix1, iy0 + q(1.0), code('stone', 2))                   # the far inner wall in shade
    fill(a, ix0, iy0, ix0 + q(0.8), iy1, code('stone', 3))                   # the west inner wall
    for yy in range(iy0 + q(1.0), iy1):
        f = (yy - iy0) / max(1, iy1 - iy0)
        steps = (('water', 3), ('water', 2), ('water_cool', 2), ('water', 1), ('water_cool', 1), ('water_cool', 0))
        fam_, t_ = steps[min(len(steps) - 1, int(f * len(steps)))]
        fill(a, ix0 + q(0.8), yy, ix1, yy + 1, code(fam_, t_))
    # the rim's reflection under the far wall and the west wall's reflection in the water
    fill(a, ix0 + q(0.8), iy0 + q(1.0) + 2, ix1, iy0 + q(1.0) + 3, code('stone', 2))
    fill(a, ix0 + q(0.8), iy0 + q(1.6), ix0 + q(1.6), iy1, code('water_cool', 2))
    fill(a, ix0 + q(0.8), iy0 + q(1.0), ix1, iy0 + q(1.0) + 1, code('water', 4))
    fill(a, ix0 + q(3), iy0 + q(2.0), ix0 + q(11), iy0 + q(2.0) + 1, code('sky', 4))
    fill(a, ix0 + q(13), iy0 + q(2.8), ix1 - q(2), iy0 + q(2.8) + 1, code('sky', 3))
    lf = ellipse_mask(a.shape, ix1 - q(5), iy0 + q(2.4), q(1.2), q(0.6))
    a[lf] = code('clay', 4)
    for (cxr, cyr) in ((ix0 + q(0.8), iy0 + q(1.0)), (ix1 - 1, iy0 + q(1.0)), (ix0 + q(0.8), iy1 - 1), (ix1 - 1, iy1 - 1)):
        a[(np.abs(X - cxr) + np.abs(Y - cyr) < q(1.0)) & (a // 8 == FI['water']) | ((np.abs(X - cxr) + np.abs(Y - cyr) < q(1.0)) & (a // 8 == FI['water_cool']))] = code('stone', 3)
    for xx in range(ix0 + q(1), ix1 - q(1), q(1.6)):                 # the waterline wobbles
        if rng.random() < 0.5:
            fill(a, xx, iy0 + q(1.0) + 1, xx + q(0.8), iy0 + q(1.0) + 2, code('water', 4))
    for _ in range(4):                                                # glints
        gx, gy = int(rng.integers(ix0 + q(2), ix1 - q(2))), int(rng.integers(iy0 + q(2.2), iy1 - 2))
        fill(a, gx, gy, gx + 2, gy + 1, code('water', 5))
    # the chip out of the near lip, the overflow notch and its wet streak
    chx = x0 + q(rng.uniform(5, 9))
    fill(a, chx, face_top - q(0.8), chx + q(2.2), face_top + q(0.6), code('stone', 2))
    fill(a, chx, face_top - q(0.8), chx + q(2.2), face_top - q(0.8) + 1, code('stone', 1))
    nx = x1 - side_w - q(4.5)
    fill(a, nx, face_top - q(1.0), nx + q(1.8), face_top, code('water', 3))
    fill(a, nx, face_top, nx + q(1.4), yb - q(1), code('stone', 1))
    fill(a, nx, face_top, nx + 1, yb - q(1), code('water', 2))
    # moss at the foot and up the shaded corner, lichen on the rim
    for _ in range(6):
        mx = x0 + q(rng.uniform(0, w))
        m = ellipse_mask(a.shape, mx, yb - q(rng.uniform(0.4, 1.4)), q(rng.uniform(1.2, 2.6)), q(rng.uniform(0.7, 1.2)))
        blob(a, m & (a >= 0), 'leaf', 3)
    blob(a, ellipse_mask(a.shape, x1 - q(1.2), yb - q(3.5), q(1.0), q(2.6)) & (a >= 0), 'leaf', 2)
    for _ in range(4):
        lx = x0 + q(rng.uniform(1, w - 4))
        m = ellipse_mask(a.shape, lx, top_y + q(rng.uniform(0.4, 0.9)), q(0.9), q(0.45)) & rim
        a[m] = code('plaster_warm', 3)
        a[m & (X < lx)] = code('grass_warm', 4)
    _tuft(a, x0 - q(1), yb - 1, rng, n=5)
    _tuft(a, x1 + q(0.5), yb - 1, rng, n=4, fam='grass_cool')
    return finish(p)


def p_skep(seed=0):
    """A straw bee skep on a flat stone: a dome of coiled straw rope, each coil a band lit on its
    upper edge and dark in the groove below, the coils stitched with split bramble in short dark
    dashes, the dome lit on its upper left and in shade round its east side; a hackle (a straw cap)
    on top, the entrance arch at its foot with bees, the stone slab under it seen from above."""
    rng = np.random.default_rng(seed)
    p = _pic(12, 8, up=13, side=3)
    a, cx, yb = p.a, p.ax, p.ay
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]] + 0.5
    # the slab
    sl_y = yb - q(2.6)
    slab = (np.abs(X - cx) < q(7.5)) & (Y >= sl_y - q(2.0)) & (Y < yb)
    a[slab] = code('stone', 3)
    a[slab & (Y < sl_y)] = code('stone_warm', 4)
    a[slab & (Y < sl_y - q(2.0) + 1)] = code('stone_warm', 5)
    a[slab & (X > cx + q(5.5))] = code('stone_cool', 2)
    for _ in range(3):
        sx_ = int(cx + rng.uniform(-q(6.5), q(5)))
        for k in range(q(1.8)):
            yy_ = int(sl_y - q(2.0) + 1 + k)
            a[yy_, sx_ + (k // 2)] = code('stone', 1)
            a[yy_, sx_ + (k // 2) - 1] = code('stone_warm', 5)
    for _ in range(4):
        lx_ = int(cx + rng.uniform(-q(7), q(6)))
        fill(a, lx_, yb - q(1.6), lx_ + q(1.2), yb - q(1.0), code('stone', 2))
    fill(a, int(cx - q(7.5)), int(sl_y - q(2.0)), int(cx - q(6.2)), int(sl_y - q(1.0)), code('grass_warm', 4))
    # the dome
    rx, ry, base = q(6.2), q(9.6), sl_y - q(0.8)
    u, v = (X - cx) / rx, (base - Y) / ry
    dome = (v >= 0) & (u * u + v * v <= 1.0)
    coil = max(3, q(1.25))
    band = ((base - Y) // coil).astype(int)
    pos = ((base - Y) % coil) / coil                                 # 0 at the groove, 1 at the coil's top
    light = -u * 0.8 + v * 0.5                                        # upper left lit
    t = np.full(a.shape, 3)
    t[light > 0.25] = 4
    t[light > 0.6] = 5
    t[light < -0.25] = 2
    t[light < -0.6] = 1
    t[pos < 0.28] -= 2                                                # the groove under each coil
    t[(pos > 0.8)] += 1
    t = np.clip(t, 0, 5)
    fam = np.where(light < -0.3, FI['sand_cool'], np.where(band % 3 == 0, FI['sand_warm'], FI['sand']))
    a[dome] = fam[dome] * 8 + t[dome]
    # stitches: short dark dashes across the coils, staggered
    for b_ in range(0, int(ry // coil) + 1):
        yy = int(base - b_ * coil - coil * 0.55)
        for xx in range(int(cx - rx), int(cx + rx), q(2.4)):
            xs = xx + (b_ % 2) * q(1.2)
            if 0 <= yy < a.shape[0] and 0 <= xs < a.shape[1] and dome[yy, xs]:
                fill(a, xs, yy - 1, xs + 1, yy + 1, code('timber', 1))
    # the hackle on top
    hk = ellipse_mask(a.shape, cx, base - ry + q(0.4), q(2.6), q(1.4))
    blob(a, hk, 'sand_warm', 4)
    fill(a, cx - q(0.4), base - ry - q(1.4), cx + q(0.4), base - ry + q(0.4), code('sand', 5))
    # the entrance arch with bees
    ent = ellipse_mask(a.shape, cx - q(1.0), base, q(1.8), q(1.4)) & (Y < base)
    a[ent] = code('soot', 0)
    for _ in range(5):
        bx = int(cx + rng.uniform(-q(5), q(4)))
        by = int(base - q(rng.uniform(0.5, 4)))
        fill(a, bx, by, bx + 2, by + 1, code('brass', 2))
        fill(a, bx, by - 1, bx + 1, by, code('sky', 4))
    _tuft(a, cx - q(7.5), yb - 1, rng, n=5)
    _tuft(a, cx + q(7.2), yb - 1, rng, n=4)
    return finish(p)


def _painted_slats(a, x0, y0, x1, n, th, gap, fam, t, rng, worn=0.2):
    """n painted slats across, each lit on top and shaded under, the paint worn to the timber at the
    edges in places; returns the y below the last slat."""
    y = y0
    for k in range(n):
        board(a, x0, y, x1 - x0, th, 0, fam, t, rng, split=False, grain=True)
        for _ in range(int((x1 - x0) * worn / q(4))):
            wx = int(rng.integers(x0 + 1, x1 - q(2)))
            fill(a, wx, y + th - 2, wx + q(rng.uniform(1, 2.5)), y + th - 1, code('timber', 3))
        y += th + gap
    return y


def p_garden_bench(seed=0, w=32.0):
    """A garden bench painted blue-grey (seat at 7 world px as the size guide's bench; its back at 15, two world px over the guide's 13 so the back slats show above the deep seat plane):
    two solid end frames (a scrolled arm on top, a foot rail at the ground, lit on the west, the east
    end in shade), three back slats with the ground showing between them, the seat of four slats
    seen from above (a deep lit plane, the paint worn to bare timber where people sit), its front
    rail in shade and the shade under the seat; a cushion forgotten at one end."""
    rng = np.random.default_rng(seed)
    p = _pic(w, 8, up=16, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(w / 2), cx + q(w / 2)
    G = 'slate'
    sy, sd = yb - q(7.0), q(3.2)                                      # seat front edge, seat depth
    # the back: three slats on the end frames, gaps left open
    for k, by in enumerate((yb - q(15.2), yb - q(13.2), yb - q(11.2))):
        board(a, x0 + q(2), by, x1 - x0 - q(4), q(1.2), 0, G, 4 - (k == 2), rng, split=False)
        for _ in range(2):
            wx = int(rng.integers(x0 + q(3), x1 - q(5)))
            fill(a, wx, by + q(1.2) - 1, wx + q(rng.uniform(1, 2.2)), by + q(1.2), code('timber', 3))
        _shade_under(a, x0 + q(2), by + q(1.2), x1 - q(2), by + q(1.2) + 1)
    # the far stretcher low down, in shade between the frames
    fill(a, x0 + q(2.5), yb - q(2.2), x1 - q(2.5), yb - q(1.4), code(G, 1))
    # the seat: four slats seen from above with dark gaps, then the front rail
    a[_rect(a.shape, x0 + q(0.6), sy - sd, x1 - q(0.6), sy)] = code(G, 1)
    yy = sy - sd
    for k in range(4):
        th = sd // 4 - 1
        board(a, x0 + q(0.6), yy, x1 - x0 - q(1.2), th, 0, G, 4, rng, split=False)
        yy += th + 1
    worn = ellipse_mask(a.shape, cx - q(6), sy - sd / 2, q(4.5), q(1.4)) | ellipse_mask(a.shape, cx + q(5), sy - sd / 2, q(3.5), q(1.2))
    a[worn & (a // 8 == FI[G]) & (a % 8 >= 3)] = code('timber_warm', 4)
    fill(a, x0 + q(0.6), sy, x1 - q(0.6), sy + q(1.3), code(G, 2))
    fill(a, x0 + q(0.6), sy, x1 - q(0.6), sy + 1, code(G, 3))
    _shade_under(a, x0 + q(2.5), sy + q(1.3), x1 - q(2.5), yb - q(2.3), k=0)
    under = _rect(a.shape, x0 + q(2.5), sy + q(1.3), x1 - q(2.5), sy + q(2.4)) & (a < 0)
    a[under] = code(G, 0)                                              # the dark under the seat's lip
    # the end frames: solid scrolled panels, the west lit, the east in shade
    for (fx0, t) in ((x0, 3), (x1 - q(2.6), 2)):
        prism(a, fx0, yb - q(15.6), fx0 + q(2.6), yb - q(9.5), q(0.9), G, t, side=1)   # the back post
        prism(a, fx0, yb - q(10.2), fx0 + q(2.6), yb, q(0.9), G, t, side=1)
        cut = ellipse_mask(a.shape, fx0 + q(1.3), yb - q(3.6), q(0.7), q(1.8))  # a pierced heart in the panel
        a[cut] = -1
        fill(a, fx0 - q(0.4), yb - q(1.2), fx0 + q(3.0), yb, code(G, max(0, t - 1)))   # the foot rail
        fill(a, fx0 - q(0.4), yb - q(1.2), fx0 + q(3.0), yb - q(1.2) + 1, code(G, t + 1))
        arm = ellipse_mask(a.shape, fx0 + q(1.3), yb - q(10.2), q(1.9), q(0.9))
        blob(a, arm, G, min(5, t + 1))
        fill(a, fx0, yb - q(9.0), fx0 + 1, yb - q(1.4), code(G, min(5, t + 1)))
    # a cushion at the east end
    cu = ellipse_mask(a.shape, x1 - q(8), sy - q(2.0), q(3.4), q(1.6))
    a[cu] = code('berry', 3)
    a[cu & (np.arange(a.shape[0])[:, None] < sy - q(2.4))] = code('berry', 4)
    a[cu & (np.arange(a.shape[1])[None, :] > x1 - q(6))] = code('berry', 2)
    fill(a, x1 - q(8.2), sy - q(3.2), x1 - q(7.6), sy - q(0.8), code('berry', 2))
    _tuft(a, x0 + q(1.3), yb - 1, rng, n=4)
    _tuft(a, cx, yb - 1, rng, n=5)
    _tuft(a, x1 - q(1.3), yb - 1, rng, n=4)
    return finish(p)


def p_garden_chair(seed=0):
    """The bench's chair: the same blue-grey paint, a back of two slats between posts, a seat of three
    slats seen from above with its front rail, four legs (the far two showing between the near
    ones), the paint worn on the seat's front edge."""
    rng = np.random.default_rng(seed)
    p = _pic(11, 8, up=18, side=2)
    a, cx, yb = p.a, p.ax, p.ay
    x0, x1 = cx - q(5.5), cx + q(5.5)
    G = 'slate'
    for lx in (x0 + q(1.6), x1 - q(3.0)):                              # the far legs
        prism(a, lx, yb - q(9), lx + q(1.4), yb - q(1.6), 1, G, 1, side=1)
    for px_ in (x0, x1 - q(2.2)):
        prism(a, px_, yb - q(17.5), px_ + q(2.2), yb - q(8.6), q(0.8), G, 2, side=q(0.8))
    _painted_slats(a, x0 + q(1.2), yb - q(16.6), x1 - q(1.2), 2, q(1.8), q(1.0), G, 3, rng, worn=0.4)
    sy = yb - q(10.6)
    a[_rect(a.shape, x0, sy, x1, sy + q(3.4))] = code(G, 1)
    yy = sy
    for k in range(3):
        board(a, x0, yy, x1 - x0, q(1.0), 0, G, 4, rng, split=False)
        yy += q(1.0) + 1
    fill(a, x0, yy, x1, yy + q(1.3), code(G, 2))
    fill(a, x0, yy, x1, yy + 1, code(G, 3))
    for wx in range(x0 + q(1), x1 - q(1), q(2.2)):
        fill(a, wx, yy, wx + q(0.8), yy + 1, code('timber_warm', 4))
    _shade_under(a, x0, yy + q(1.3), x1, yy + q(2.4), k=2)
    for lx in (x0, x1 - q(1.8)):                                       # the near legs
        prism(a, lx, yy + q(1.3), lx + q(1.8), yb, 1, G, 2 if lx > cx else 3, side=1)
        fill(a, lx, yb - q(1.2), lx + q(1.8), yb, code(G, 1))
    _tuft(a, x0 - q(0.5), yb - 1, rng, n=3)
    _tuft(a, x1 + q(0.5), yb - 1, rng, n=4)
    return finish(p)


KINDS = {
    'stile': p_stile,
    'fingerpost': p_fingerpost,
    'field_gate': p_field_gate,
    'beehive': p_beehive,
    'potting_table': p_potting_table,
    'trough_timber': p_trough_timber,
    'trough_stone': p_trough_stone,
    'skep': p_skep,
    'garden_bench': p_garden_bench,
    'garden_chair': p_garden_chair,
}
REVIEW_KIND = {'stile': 'fence', 'fingerpost': 'signpost', 'field_gate': 'fence', 'beehive': 'beehive',
               'potting_table': 'table', 'trough_timber': 'trough', 'trough_stone': 'trough', 'skep': 'beehive',
               'garden_bench': 'bench', 'garden_chair': 'chair'}


def prop(kind: str, seed: int = 0):
    return KINDS[kind](seed=seed)


def write_all(out_dir: str, seed: int = 0) -> list:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for k in KINDS:
        p_ = os.path.join(out_dir, f'{k}.png')
        prop(k, seed).rgba().save(p_)
        paths.append(p_)
    return paths


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join('artifacts', 'review', 'wayside')
    for p_ in write_all(out):
        print(p_)
