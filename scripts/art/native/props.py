"""r1 props: the 1x scene's own designs (Matt's master) drawn natively at 1.5x and 2x with
Eastward's level of detail. Same silhouette, type, colours and proportions as the 1x sprite of
each object; more detail at the higher levels. Units: 1 unit = 1 px at density 2 (0.5 world px).

Each function returns (img, anchor, alpha) with the anchor the ground point under the object.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from . import raster as pk

# r6 style constants (the 2x kit reads these)
STONE4 = dict(cap=0.86, body=0.62, shade=0.36, light=(-0.55, -0.62, 0.56))   # r6: the grey stone's ramp
SIGN3 = [(3, -29), (3, -19), (-11, -11), (-16.5, -14.5), (-12, -20.5)]   # the third arm (units)

# wood closes in a dark brown (the 1x sprites' outline), not near-black: native/accents.json 'edges'


def _sprite(d, wu, hu, ax_u, pad_u=2):
    s = d / 2
    W = int(math.ceil(wu * s))
    H = int(math.ceil(hu * s))
    ox = round(ax_u * s)
    oy = H - max(1, int(round(pad_u * s)))
    return pk.Sprite(W, H, s, ox, oy)


def _out(sp, **kw):
    img = sp.render(**kw)
    a = np.asarray(img)[..., 3] > 0
    return img, (sp.g.ox, sp.g.oy), a


# ------------------------------------------------------------------------------------------------
# trees: the trunk (crowns are painted from their 1x master, foliage.py)
# ------------------------------------------------------------------------------------------------
def oak4(d, w=65, h=78, trunk_w=11, crown_h=50, seed=11):
    """The 1x oak's trunk under a crown (w world px wide, crown_h tall; the crown itself is
    painted from the 1x master by foliage.py, compose.foliage_sprite): a thick, straight trunk
    (trunk_w wide) that flares at the root; bark lit on the left, broken plates, a knot, a dark
    band right under the crown. w, h in world px (the 1x sprite's box)."""
    W, Hh, tw, ch = w * 2, h * 2, trunk_w * 2, crown_h * 2
    sp = _sprite(d, W + 10, Hh + 8, (W + 10) / 2, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    top_trunk = -(Hh - ch) - 4
    half = tw / 2
    tr = g.poly([(-half * 0.72, top_trunk - 6), (half * 0.72, top_trunk - 6), (half, -16), (half + 0.8, -9), (half + 2.4, -4.5), (half + 6, -0.5),
                 (half + 1, -1.5), (2, 0), (-3, -1.0), (-half - 1, -1.5), (-half - 6, -0.3), (-half - 2.4, -4.5),
                 (-half - 0.8, -9), (-half, -16)])
    tr = pk.round_mask(tr, 1)
    sp.add('trunk', tr, 'timber_cool', base=3, lo=0, hi=4, z=1, mode='cyl', k=1.0)
    for j in range(int(6 + tw / 4)):
        x = rng.uniform(-half + 2, half - 2)
        y0 = rng.uniform(top_trunk, -12)
        ln = rng.uniform(5, 10)
        sp.mark('trunk', g.capsule(x, y0, x + rng.uniform(-0.6, 0.6), y0 + ln, 0.6), -1)
        if x < 0:
            sp.mark('trunk', g.capsule(x - 1.4, y0 + 1, x - 1.4, y0 + ln * 0.6, 0.55), 1)
    kx, ky = rng.uniform(-half * 0.3, half * 0.4), rng.uniform(top_trunk * 0.6, top_trunk * 0.3)
    sp.mark('trunk', g.ellipse(kx, ky, 1.8, 1.4), -2)
    sp.mark('trunk', g.rect(kx - 1.6, ky - 2.4, kx + 0.6, ky - 1.4), 1)
    for (x0, x1) in ((-half + 1, -half - 5), (half - 1, half + 5)):
        sp.mark('trunk', g.capsule(x0, -3, x1, -1.2, 0.8), 1 if x1 < 0 else -1)
    sp.mark('trunk', g.rect(-W, top_trunk - 8, W, top_trunk + 6), -1)
    sp.mark('trunk', g.rect(-W, top_trunk - 8, W, top_trunk + 1), -1)
    return _out(sp)


# ------------------------------------------------------------------------------------------------
def bench4(d, seed=41):
    """The 1x bench (34 x 16 world px), seen from the front: two grey iron end frames (an upright,
    an armrest bar, a foot), a backrest of two slats, the seat as two slats seen from above
    (lighter, in front of the backrest) with a shaded front edge, and the dark shade under the
    seat between the legs. Grain, nail heads, bolts."""
    sp = _sprite(d, 72, 36, 36, 3)
    g = sp.g
    L = 31.0
    rng = np.random.default_rng(seed)
    fams = ['timber', 'timber_warm', 'timber_cool']
    # the shade under the seat, between the legs (the 1x's dark band)
    sp.add('under', g.rect(-L + 3, -9.0, L - 3, -6.6), 'timber_cool', base=0, lo=0, hi=1, z=0.5, flat=True,
           outline=False, casts=False)
    slats = [(-29.0, -24.6, 3, 'back'), (-23.4, -19.0, 3, 'back'), (-17.6, -14.2, 4, 'seat'), (-14.2, -10.8, 4, 'seat'),
             (-10.8, -9.0, 2, 'edge')]
    for j, (y0, y1, bt, kind) in enumerate(slats):
        nm = f'slat{j}'
        m = g.rect(-L + 3, y0, L - 3, y1)
        p = sp.add(nm, m, fams[j % 3], base=bt, lo=max(0, bt - 2), hi=5, z=2 + j * 0.1, flat=True)
        jx = rng.uniform(-10, 10)
        p.famarr = np.where(g.X < jx, fams[j % 3], fams[(j + 1) % 3]).astype(object)
        if kind != 'edge':
            sp.mark(nm, g.rect(-L, y0, L, y0 + 1.0), 1)
            sp.mark(nm, g.rect(-L, y1 - 1.0, L, y1), -1)
            sp.mark(nm, g.rect(L - 9, y0, L, y1), -1)
            for k in range(3):
                gx = rng.uniform(-L + 6, L - 12)
                gy = rng.uniform(y0 + 1.5, max(y0 + 1.6, y1 - 2.0))
                sp.mark(nm, g.rect(gx, gy, gx + rng.uniform(4, 9), gy + 1.0), -1)
            for x in (-L + 6, L - 6):
                sp.detail(g.rect(x - 0.5, (y0 + y1) / 2 - 0.5, x + 0.5, (y0 + y1) / 2 + 0.5), pk.rgb('iron', 1))
    sp.mark('slat2', g.ellipse(-6, -15.8, 10, 1.6) | g.ellipse(10, -15.8, 8, 1.6), 1)   # the worn seat
    # iron end frames: an upright to the backrest top, an armrest bar, a foot
    for side in (-1, 1):
        x = side * (L - 1.5)
        nm = f'frame{side}'
        m = g.rect(x - 1.8, -30.5, x + 1.8, 0) | g.rrect(x - 2.4, -31.5, x + 2.4, -28.5, 1.0)
        m |= g.rect(min(x, x + side * 4.0) - 0.2, -19.6, max(x, x + side * 4.0) + 0.2, -17.4)
        m |= g.rect(x - 3.0, -1.6, x + 3.0, 0)
        sp.add(nm, m, 'iron', base=3, lo=1, hi=5, z=4, mode='cyl', k=1.2)
        sp.mark(nm, g.rect(x - 5, -31.5, x + 5, -30.5) | g.rect(x - 5, -19.6, x + 5, -18.8), 1)
        for yy in (-27.0, -21.4, -16.0, -12.6):
            sp.detail(g.rect(x - 0.5, yy, x + 0.5, yy + 1.0), pk.rgb('iron', 5 if side < 0 else 4))
    img, anc, a = _out(sp)
    return img, anc, a


def lantern4(d, seed=0):
    """The 1x lantern (16 x 37 world px): a timber post on the west with a short arm at its top,
    a box lantern fixed on the post's east side under a green cap, warm panes in a dark frame,
    a vine at the post's foot."""
    sp = _sprite(d, 36, 80, 8, 3)
    g = sp.g
    post = g.rect(-2.6, -70, 2.6, 0) | g.rrect(-3.8, -4, 3.8, 0, 1)
    sp.add('post', post, 'timber', base=3, lo=1, hi=5, z=1, mode='cyl')
    for y in (-58, -36, -20):
        sp.mark('post', g.rect(-4, y, 4, y + 1), -1)
    sp.add('arm', g.rrect(-3.2, -73, 9, -69, 1.0), 'timber', base=3, lo=1, hi=5, z=1.5)
    sp.mark('arm', g.rect(-4, -73, 10, -72), 1)
    c = 10.0
    sp.add('capL', g.rrect(c - 6.5, -67.5, c + 6.5, -63, 1.4), 'leaf', base=3, lo=1, hi=5, z=3)
    sp.mark('capL', g.rect(c - 7, -67.5, c + 7, -66.4), 1)
    glass = g.rect(c - 5.6, -64, c + 5.6, -43)
    sp.add('glass', glass, 'lamp', base=4, lo=2, hi=5, z=2.5, flat=True, casts=False)  # noqa
    sp.mark('glass', g.ellipse(c - 1.0, -52, 2.6, 5.0), 1)
    sp.mark('glass', g.rect(c - 5, -63, c + 5, -61), -1)
    frame = (g.rect(c - 6.0, -63, c - 4.6, -43) | g.rect(c + 4.6, -63, c + 6.0, -43) | g.rect(c - 0.6, -63, c + 0.6, -44)
             | g.rect(c - 6.0, -44.4, c + 6.0, -42.6))
    sp.add('frame', frame, 'iron', base=2, lo=0, hi=3, z=3.2, flat=True)
    sp.add('bracket', g.rect(2.6, -60, c - 4.6, -58.4) | g.rect(2.6, -48, c - 4.6, -46.4), 'iron', base=2, z=2.6, flat=True)
    # r5: the box hangs from the arm on a short iron hanger (a ring under the arm, a stem to the cap)
    sp.add('hanger', g.rect(c - 1.0, -69.5, c + 1.0, -67.0) | g.rect(c - 2.2, -70.0, c + 2.2, -68.8), 'iron', base=2,
           lo=0, hi=4, z=3.3, flat=True)
    sp.mark('hanger', g.rect(c - 2.2, -70.0, c - 0.2, -68.8), 1)
    vine = g.stroke([(-1.5, 0), (-3.5, -4), (-1, -8), (-3.2, -12), (-1.5, -15)], 0.9)
    for (lx, ly) in ((-4.5, -5), (-0.5, -9), (-4.2, -13), (1.2, -3)):
        vine |= g.ellipse(lx, ly, 1.6, 1.1)
    sp.add('vine', vine, 'leaf', base=3, lo=1, hi=4, z=4)
    return _out(sp)


def signpost4(d, seed=91):
    """The 1x signpost (30 x 36 world px): two broad boards on a post, the top one pointing east,
    the lower one west; grain, nail heads, carved marks; a tuft at the foot."""
    sp = _sprite(d, 64, 76, 30, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    post = g.rect(-2.6, -60, 2.6, 0) | g.rrect(-3.8, -4, 3.8, 0, 1)
    sp.add('post', post, 'timber', base=3, lo=1, hi=5, z=1, mode='cyl')
    b1 = g.poly([(-22, -68), (22, -68), (29, -62), (22, -56), (-22, -56)])
    b2 = g.poly([(22, -45), (-22, -45), (-29, -39), (-22, -33), (22, -33)])
    for nm, m, f, y0, y1 in (('b1', b1, 'timber_warm', -68, -56), ('b2', b2, 'timber', -45, -33)):
        sp.add(nm, pk.round_mask(m, 1), f, base=3, lo=1, hi=5, z=2, flat=True)
        sp.mark(nm, g.rect(-30, y0, 30, y0 + 1.0), 1)
        sp.mark(nm, g.rect(-30, y1 - 1.0, 30, y1), -1)
        sp.mark(nm, g.rect(-30, y0 + 1.0, 30, y0 + 2.0), 1)
        for k in range(4):
            gx = rng.uniform(-20, 14)
            gy = rng.uniform(y0 + 3, y1 - 3)
            sp.mark(nm, g.rect(gx, gy, gx + rng.uniform(5, 10), gy + 1.0), -1)
        cy = (y0 + y1) / 2
        sp.mark(nm, g.rect(-12, cy - 0.5, -4, cy + 0.5) | g.rect(-1, cy - 0.5, 9, cy + 0.5), -2)   # carved names
        for x in (-18, 18):
            sp.detail(g.rect(x - 0.5, cy - 0.5, x + 0.5, cy + 0.5), pk.rgb('iron', 4))
    # r3: a third arm, short, pointing south-west down the main path (the fork has three ways);
    # no weed scribble at the foot
    # r4: it slants down and to the left, towards the viewer and the main path south
    b3 = g.poly(SIGN3)
    sp.add('b3', pk.round_mask(b3, 1), 'timber_warm', base=3, lo=1, hi=5, z=2.5, flat=True)
    sp.mark('b3', g.stroke([(2.5, -28.0), (-11.5, -19.6)], 0.9), 1)
    sp.mark('b3', g.stroke([(2.5, -19.8), (-11.0, -11.8)], 0.8), -1)
    sp.mark('b3', g.stroke([(-1.5, -21.6), (-6.5, -18.8)], 0.5), -2)
    sp.detail(g.rect(0.0, -23.0, 1.0, -22.0), pk.rgb('iron', 4))
    return _out(sp)


def fence4(d, length=66, posts=None, seed=101, gate_post=True, n_pickets=7):
    """The 1x palisade (20 world px tall): a tall gate post at the west end braced into the first
    bay, then slim pickets (3 world px) behind two rails that run across in front of them, nail
    heads on the rails, a vine on one picket. length in world px, running east from the anchor."""
    Lu = length * 2
    sp = _sprite(d, Lu + 10, 44, 6, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    x0 = 18.0 if gate_post else 4.0
    pitch = (Lu - x0 - 4) / max(1, n_pickets - 1)
    for k in range(n_pickets):
        x = x0 + 2 + k * pitch
        hgt = 34 + (k % 2) * 1.0
        nm = f'p{k}'
        sp.add(nm, g.rrect(x - 3.0, -hgt, x + 3.0, 0, 1.2), ('timber', 'timber_cool')[k % 2], base=3, lo=1, hi=5, z=1,
               mode='cyl', k=1.0)
        sp.mark(nm, g.rect(x - 4, -hgt, x + 4, -hgt + 1.2), 1)
        gy = rng.uniform(-hgt + 6, -6)
        sp.mark(nm, g.rect(x - 0.5, gy, x + 0.5, gy + rng.uniform(4, 8)), -1)
    xl = x0 + 2 + (n_pickets - 1) * pitch + 3.5
    for j, (y0, y1) in enumerate(((-29, -25), (-14, -10))):
        nm = f'rail{j}'
        sp.add(nm, g.rect(x0 - 2, y0, xl, y1), 'timber_warm', base=3, lo=1, hi=5, z=2 + j * 0.1, flat=True)
        sp.mark(nm, g.rect(0, y0, Lu, y0 + 1.0), 1)
        sp.mark(nm, g.rect(0, y1 - 1.0, Lu, y1), -1)
        for k in range(n_pickets):
            x = x0 + 2 + k * pitch
            sp.detail(g.rect(x - 0.5, (y0 + y1) / 2 - 0.5, x + 0.5, (y0 + y1) / 2 + 0.5), pk.rgb('iron', 4))
    if gate_post:
        gp = g.rrect(0, -40, 12, 0, 1.4)
        sp.add('gate', gp, 'timber', base=3, lo=1, hi=5, z=3, mode='cyl', k=0.8)
        sp.mark('gate', g.rect(0, -40, 13, -38.8), 1)
        for k in range(3):
            gy = rng.uniform(-34, -6)
            sp.mark('gate', g.rect(3 + k * 3.0, gy, 4 + k * 3.0, gy + rng.uniform(5, 9)), -1)
        brace = g.stroke([(12, -12), (x0 + 2 + pitch - 3, -27)], 1.3)
        sp.add('brace', brace, 'timber_warm', base=3, lo=1, hi=4, z=2.5, flat=True)
        sp.mark('brace', g.stroke([(12, -13), (x0 + 2 + pitch - 3, -28)], 0.5), 1)
    vx = x0 + 2 + pitch
    vine = g.stroke([(vx, 0), (vx + 1.5, -6), (vx - 1, -12), (vx + 1, -18)], 0.8)
    for (lx, ly) in ((vx + 2.6, -4), (vx - 2.2, -10), (vx + 2.4, -15)):
        vine |= g.ellipse(lx, ly, 1.7, 1.1)
    sp.add('vine', vine, 'leaf', base=3, lo=1, hi=4, z=4)
    img, anc, a = _out(sp)
    return img, anc, a


def fence_side4(d, length=36, seed=103, top_post=True, bottom_post=True, rail_end=0.0):
    """The palisade running north-south, seen from the 3/4 view: its two rails as thin parallel
    lines (lit west, dark east) going up the screen, the picket tops as short lit stubs every
    8 world px, a corner post at each end. length in world px, running north from the anchor."""
    Lu = length * 2
    sp = _sprite(d, 18, Lu + 46, 9, 3)
    g = sp.g
    top = -Lu - 30
    re_ = -10 - rail_end
    # r4: one wooden rail running up the screen (its lit top on the west, a dark east side), no
    # beaded pair of strings; the picket tops stand on it every 4 world px
    sp.add('rail', g.rect(-2.0, top, 2.0, re_), 'timber', base=3, lo=1, hi=5, z=0.5, flat=True, outline=False)
    sp.mark('rail', g.rect(-2.0, top, 0.0, re_), 1)
    sp.mark('rail', g.rect(0.0, top, 2.0, re_), -2)
    pitch = 14.0
    n = max(2, int(round(Lu / pitch)) + 1)
    for k in range(n - 1, -1, -1):
        y = -k * Lu / (n - 1)
        end = (k == 0 and bottom_post) or (k == n - 1 and top_post)
        if k == n - 1 and not top_post:
            continue
        if end:
            m = g.rrect(-3.8, y - 40, 3.8, y, 1.4)
            sp.add(f'post{k}', m, 'timber', base=3, lo=1, hi=5, z=2 + (n - k) * 0.01, mode='cyl')
            sp.mark(f'post{k}', g.rect(-5, y - 40, 5, y - 38), 1)
        else:
            m = g.rect(-2.0, y - 34, 2.0, y - 30)
            sp.add(f'stub{k}', m, 'timber_warm', base=5, lo=1, hi=5, z=1 + (n - k) * 0.01, flat=True, outline=False)
            sp.mark(f'stub{k}', g.rect(0.0, y - 34, 2.0, y - 30), -1)
    return _out(sp)


def gateleaf4(d, seed=105):
    """The gate leaf hung on the gate post and swung out about 45 degrees to the north-west:
    three pickets and two rails, foreshortened."""
    sp = _sprite(d, 36, 52, 32, 3)
    g = sp.g
    # r3: four pickets on a 45-degree line from the hinge, the gap's full 16 world px
    pts = [(-4.5, -3.2), (-10.5, -7.6), (-16.5, -12.0), (-22.0, -16.0)]
    for k, (x, y) in enumerate(pts):
        sp.add(f'p{k}', g.rrect(x - 2.6, y - 30, x + 2.6, y, 1.0), ('timber', 'timber_cool')[k % 2], base=3, lo=1, hi=5,
               z=1 + k * -0.1, mode='cyl')
        sp.mark(f'p{k}', g.rect(x - 4, y - 30, x + 4, y - 28.8), 1)
    for (yo, nm) in ((-24, 'r0'), (-10, 'r1')):
        sp.add(nm, g.stroke([(-1.5, yo - 1), (-23, yo - 16.5)], 1.4), 'timber_warm', base=3, lo=1, hi=5, z=2, flat=True)
    return _out(sp)


def post4(d, seed=0):
    """A short marker post with a cap (stair heads): 12 world px tall."""
    sp = _sprite(d, 14, 30, 7, 2)
    g = sp.g
    sp.add('post', g.rrect(-2.8, -22, 2.8, 0, 1.0), 'timber', base=3, lo=1, hi=5, z=1, mode='cyl')
    sp.add('cap', g.rrect(-3.6, -25, 3.6, -21, 1.4), 'timber_warm', base=4, lo=2, hi=5, z=2)
    sp.mark('post', g.rect(-4, -14, 4, -13), -1)
    return _out(sp)


def stump4(d, seed=61):
    """The 1x stump (21 x 16 world px): a lit cut top with rings and a crack, bark sides lit on
    the left, root lobes flaring, a tuft at the base."""
    sp = _sprite(d, 50, 38, 25, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    side = g.rrect(-15, -22, 15, -2, 3) | g.poly([(-15, -7), (-21, -0.5), (-10, -2)]) | g.poly([(15, -8), (20, -0.5), (10, -2)]) \
        | g.poly([(2, -3), (6, 0), (-2, 0)])
    side = pk.round_mask(side, 1)
    sp.add('bark', side, 'timber_cool', base=3, lo=0, hi=4, z=1, mode='cyl')
    for x in (-10, -5, 1, 6, 11):
        y0 = -18 + rng.uniform(-1, 2)
        sp.mark('bark', g.capsule(x, y0, x + rng.uniform(-0.5, 0.5), y0 + rng.uniform(5, 10), 0.6), -1)
    top = g.ellipse(0, -22, 15, 6.0)
    sp.add('top', top, 'plaster_warm' if 'plaster_warm' in pk.RAMPS else 'plaster', base=3, lo=1, hi=5, z=2, flat=True)
    for (a, b) in ((10.5, 4.0), (6.5, 2.4), (3.0, 1.1)):
        sp.mark('top', g.ellipse(0.5, -21.8, a, b) & ~g.ellipse(0.5, -21.8, a - 1.3, b - 0.6), -1)
    sp.mark('top', g.ellipse(-5, -24, 6.0, 1.6) & top, 1)
    sp.mark('top', g.stroke([(2, -22), (11, -19.5)], 0.5), -2)
    sp.mark('top', top & ~g.ellipse(0, -22.4, 13.8, 5.0), -1)
    return _out(sp)


def log4(d, length=54, thick=15, seed=71):
    """The 1x mossy log (54 x 16 world px): a thick bark cylinder lying east-west, the sawn end
    (rings, a lit rim) facing west, diagonal grain, moss along the top in three greens drooping
    over the side, a pale bracket fungus low on its flank."""
    Lu, Tu = length * 2, thick * 2
    sp = _sprite(d, Lu + 10, Tu + 12, Lu / 2 + 5, 3)
    g = sp.g
    L = Lu / 2
    rng = np.random.default_rng(seed)
    body = g.rrect(-L + 4, -Tu - 1, L, -1, 2) & ~g.poly([(L + 1, -Tu - 2), (L - 3, -Tu * 0.7), (L + 1, -Tu * 0.5)]) \
        & ~g.poly([(L + 1, -Tu * 0.35), (L - 2.5, -Tu * 0.2), (L + 1, -2)])
    sp.add('bark', body, 'timber_cool', base=3, lo=0, hi=4, z=1, k=1.0)
    # r3: bark plates: broken lines running along the log, 6 to 12 px long and staggered, a lit
    # edge above the upper ones; one knot (a small ring) and a short branch stub
    rows = np.linspace(-Tu + 6, -5, 5)
    for j, yv in enumerate(rows):
        x = -L + 10 + rng.uniform(0, 8)
        while x < L - 6:
            ln = rng.uniform(6, 12)
            yy_ = yv + rng.uniform(-0.6, 0.6)
            sp.mark('bark', g.stroke([(x, yy_), (min(L - 4, x + ln), yy_ + rng.uniform(-0.5, 0.5))], 0.5), -1)
            if j < 2:
                sp.mark('bark', g.stroke([(x + 1, yy_ - 1.1), (min(L - 4, x + ln - 1), yy_ - 1.1)], 0.45), 1)
            x += ln + rng.uniform(4, 9)
    kx, ky = L * 0.42, -Tu * 0.55
    sp.mark('bark', g.ellipse(kx, ky, 2.4, 1.8) & ~g.ellipse(kx, ky, 1.2, 0.8), -2)
    sp.mark('bark', g.ellipse(kx - 0.6, ky - 0.6, 0.8, 0.6), 1)
    sx_, sy_ = -L * 0.08, -Tu * 0.45
    sp.add('stub', g.ellipse(sx_, sy_, 3.4, 2.8), 'timber_cool', base=3, lo=1, hi=4, z=1.8)
    sp.add('stubend', g.ellipse(sx_ - 0.4, sy_ - 0.3, 1.9, 1.5), 'plaster', base=3, lo=2, hi=4, z=1.9, flat=True)
    end = g.ellipse(-L + 5, -Tu / 2 - 1, Tu * 0.24, Tu / 2)
    sp.add('end', end, 'plaster_warm' if 'plaster_warm' in pk.RAMPS else 'plaster', base=3, lo=1, hi=5, z=1.5, flat=True)
    for f in (0.74, 0.46):
        sp.mark('end', g.ellipse(-L + 5, -Tu / 2 - 1, Tu * 0.24 * f, Tu / 2 * f) &
                ~g.ellipse(-L + 5, -Tu / 2 - 1, Tu * 0.24 * f - 1.0, Tu / 2 * f - 1.0), -2)
    sp.mark('end', g.ellipse(-L + 5, -Tu / 2 - 1, 1.0, 1.2), -2)
    sp.mark('end', g.stroke([(-L + 5, -Tu / 2 - 1), (-L + 6.5, -Tu + 3)], 0.45), -1)
    sp.mark('end', end & (g.X < -L + 3.4), 1)
    moss = g.rrect(-L + 9, -Tu - 2.5, L - 2, -Tu + 4, 2.0) & ~g.ellipse(-L + 5, -Tu / 2 - 1, Tu * 0.3, Tu / 2 + 2)
    for x in rng.uniform(-L + 12, L - 6, 5):
        moss |= g.capsule(x, -Tu + 2, x + rng.uniform(-0.5, 0.5), -Tu + rng.uniform(5, 8), 1.2)
    moss &= body | g.rect(-L, -Tu - 3, L, -Tu)
    sp.add('moss', moss, 'leaf_warm', base=3, lo=1, hi=5, z=2, k=1.1)
    br = g.ellipse(L * 0.1, -2.5, 8.5, 3.2) & g.rect(L * 0.1 - 9, -6, L * 0.1 + 9, -1.5)
    sp.add('bracket', br, 'plaster', base=4, lo=2, hi=5, z=2.5)
    return _out(sp)


def mushroom_ring4(d, w=41, h=20, seed=85, n=10):
    """The 1x fairy ring: about ten mushrooms, red caps with white spots on the west half and tan
    caps with a pale band on the east, in a ring on a slightly darker patch of grass."""
    sp = _sprite(d, 2 * w + 10, 2 * h + 10, w + 5, 2)
    g = sp.g
    rng = np.random.default_rng(seed)
    rx, ry = w - 9, h - 9
    sp.add('patch', g.ellipse(0, -ry - 2, rx * 0.9, ry * 0.8), 'grass', base=2, lo=2, hi=2, z=0, flat=True, outline=False,
           casts=False)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2)
        pts.append((math.cos(a) * rx, -ry + math.sin(a) * ry * 0.95 - 2, math.cos(a)))
    pts.sort(key=lambda p: p[1])
    for k, (x, yb, ca) in enumerate(pts):
        red = x < -2 or (abs(x) <= 2 and k % 2 == 0)
        hgt = rng.uniform(7, 10) if red else rng.uniform(6, 9)
        r = rng.uniform(5.8, 7.2) if red else rng.uniform(5.4, 6.6)
        z = 1 + k
        sp.add(f'st{k}', g.rrect(x - 2.2, yb - hgt + 1, x + 2.2, yb, 1.0), 'plaster', base=4, lo=2, hi=5, z=z, mode='cyl')
        cap = g.ellipse(x, yb - hgt, r, r * 0.72) & g.rect(x - r - 1, yb - hgt - r, x + r + 1, yb - hgt + r * 0.3)
        sp.add(f'cap{k}', cap, 'berry' if red else 'clay', base=3 if red else 4, lo=1, hi=5, z=z + 0.5)
        sp.mark(f'cap{k}', g.rect(x - r - 1, yb - hgt - 0.2, x + r + 1, yb - hgt + r * 0.3) & cap, -1)
        if red:
            for (sx, sy) in ((-0.4, -0.35), (0.35, -0.5), (0.1, 0.05)):
                sp.add(f'sp{k}{sx}', g.ellipse(x + sx * r, yb - hgt + sy * r, 0.9, 0.7) & cap, 'plaster', fixed=5, z=z + 0.6,
                       outline=False)
        else:
            sp.add(f'band{k}', g.rect(x - r, yb - hgt - 0.2, x + r, yb - hgt + 1.0) & cap, 'plaster', fixed=4, z=z + 0.6,
                   outline=False)
    return _out(sp)


def _poly_mask(pts, X, Y):
    """Pixels whose centres (X, Y) lie inside the polygon pts (even-odd rule)."""
    inside = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if y1 == y2:
            continue
        cross = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / (y2 - y1) + x1)
        inside ^= cross
    return inside


def boulder4(d, w=21, h=13, seed=31, fam='stone'):
    """r7: the 1x grey stone (21 x 13 world px) as two or three chunks of pixel-art stone (Matt:
    rocks read vector-like). Each chunk has a flat lit top (tone 4, mottled), a bright rim along
    its upper-left edge, a hard step down to its sides (the front a tone 2 lit on the left, the
    right side darker), a base band in tone 1, and one crack with a lit lip. The chunks stand in
    a crevice of tone 0; the outline is dark on the right and bottom only; moss sits on the tops;
    a few pebbles spill at the foot."""
    s_ = d / 2
    Wp, Hp = int(math.ceil((w * 2 + 16) * s_)), int(math.ceil((h * 2 + 10) * s_))
    ax, ay = Wp / 2 - 2 * s_, Hp - max(1, int(round(3 * s_)))
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(float)
    W_, H_ = w * d, h * d * 1.05
    k = 3 if rng.random() < 0.6 else 2
    # (centre x as a share of the width, base y above the foot, width, height) per chunk, back first
    spec = [(-0.16, 0.10, 0.66, 0.96), (0.24, 0.0, 0.54, 0.70)]
    if k == 3:
        spec.append((-0.33, -0.02, 0.32, 0.42))
    chunks = []
    for (cxf, byf, wf, hf) in spec:
        cx = ax + cxf * W_ + rng.uniform(-0.04, 0.04) * W_
        base = ay - byf * H_
        cw, ch = wf * W_ * rng.uniform(0.94, 1.06), hf * H_ * rng.uniform(0.94, 1.06)
        n = 7
        pts = []
        for q in range(n):
            a_ = math.pi + q * math.pi / (n - 1) + rng.uniform(-0.12, 0.12)   # the upper half, left to right
            r_ = rng.uniform(0.86, 1.08)
            r_ = r_ if q not in (2, 3, 4) else min(r_, 0.97)      # a flatter crown: the top is a shelf
            pts.append((cx + math.cos(a_) * cw / 2 * r_, base - ch * 0.45 + math.sin(a_) * ch * 0.55 * r_))
        pts = [(pts[0][0], base - ch * 0.45 + ch * 0.12)] + pts + [(pts[-1][0], base - ch * 0.45 + ch * 0.12)]
        pts += [(cx + cw * 0.46, base - 0.3 * d), (cx + cw * 0.2, base), (cx - cw * 0.25, base), (cx - cw * 0.47, base - 0.4 * d)]
        m = _poly_mask(pts, xx + 0.5, yy + 0.5)
        chunks.append(dict(m=m, cx=cx, cw=cw, ch=ch, base=base, top=base - ch * 1.24))
    t = np.zeros((Hp, Wp), int)
    fm = np.zeros((Hp, Wp), int)          # 0 stone, 1 stone_cool, 2 moss
    own = np.full((Hp, Wp), -1)
    for ci, c in enumerate(chunks):
        own[c['m']] = ci
    allm = own >= 0
    for ci, c in enumerate(chunks):
        m = own == ci
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        y0 = ys.min()
        hh = ys.max() - y0 + 1
        # the flat top: above a line that steps (hard, a px at a time) across the chunk
        steps = np.cumsum(rng.choice([-1, 0, 0, 0, 1], Wp)) * 0.5
        topline = y0 + hh * rng.uniform(0.40, 0.48) + steps - steps[int(min(Wp - 1, max(0, c['cx'])))]
        top = m & (yy < topline[None, :])
        side = m & ~top
        tt = np.where(top, 4, 2)
        # the front lit on the left, the right side darker
        rel = (xx - c['cx']) / (c['cw'] / 2)
        tt[side & (rel < -0.55)] = 3
        tt[side & (rel > 0.45)] = 1
        # the base band
        tt[side & (yy > c['base'] - 1.6 * d)] = np.minimum(tt[side & (yy > c['base'] - 1.6 * d)], 1)
        # mottling: soft blobs a tone up or down, so no tone covers the whole face
        for _ in range(int(m.sum() / (9 * d * d)) + 1):
            q = int(rng.integers(0, len(ys)))
            rb = rng.uniform(0.9, 1.8) * d
            bb = m & ((yy - ys[q]) ** 2 + (xx - xs[q]) ** 2 <= rb * rb)
            if top[ys[q], xs[q]]:
                if rng.random() < 0.5:
                    continue
                ln = int(rng.integers(2, 4))
                bb = top & (yy == ys[q]) & (xx >= xs[q]) & (xx < xs[q] + ln)     # a short worn dash
                tt[bb] = 3
                continue
            dt = 1 if rel[ys[q], xs[q]] < -0.3 else -1
            bb &= side
            tt[bb] = np.clip(tt[bb] + dt, 1, 4)
        # the bright upper-left rim of the top
        P_ = np.pad(m, 1)
        upl = m & (~P_[:-2, 1:-1] | ~P_[1:-1, :-2])
        tt[upl & top] = 5
        tt[upl & side & (rel < 0)] = 3
        # the step from top to side: the first side row a tone darker
        stp = side & np.roll(top, 1, 0)
        tt[stp] = np.maximum(1, tt[stp] - 1)
        # one crack: from the top's front edge down the side, with a lit lip on its left
        cand = np.nonzero(stp & (np.abs(rel) < 0.5))
        if len(cand[0]):
            q = int(rng.integers(0, len(cand[0])))
            y, x = cand[0][q] - int(1 * d), cand[1][q]
            for _ in range(int(rng.uniform(3, 5.5) * d)):
                if 0 <= y < Hp and 0 <= x < Wp and m[y, x]:
                    tt[y, x] = 0
                    if x - 1 >= 0 and m[y, x - 1] and tt[y, x - 1] > 0:
                        tt[y, x - 1] = min(5, tt[y, x - 1] + 1)
                y += 1
                if rng.random() < 0.35:
                    x += 1 if rng.random() < 0.6 else -1
        # moss on the top's back half
        if top.any():
            ty_, tx_ = np.nonzero(top)
            for _ in range(int(rng.integers(3, 6))):
                q = int(rng.integers(0, len(ty_)))
                if ty_[q] > y0 + hh * 0.22 or abs(rel[ty_[q], tx_[q]]) > 0.6:
                    continue
                rb = rng.uniform(1.2, 2.0) * d
                mb = m & ((yy - ty_[q] + 0.5 * d) ** 2 / 0.45 + (xx - tx_[q]) ** 2 <= rb * rb) & (yy < topline[None, :] - 0.5 * d)
                fm[mb] = 2
                tt[mb] = 3
                low = mb & ~np.roll(mb, -1, 0)
                tt[low] = 2
                hi = mb & ~np.roll(mb, 1, 0)
                tt[hi] = 4
        tt[~m] = 0
        t[m] = tt[m]
        fm[m & (fm != 2)] = np.where(rel[m & (fm != 2)] > 0.15, 1, 0)
    # the crevice: the back chunk darkens along the front chunk's edge
    for ci in range(len(chunks)):
        front = own == ci
        ring = ndi.binary_dilation(front) & ~front & allm & (own < ci)
        t[ring] = 0
    # small pits on the sides
    sy_, sx_ = np.nonzero(allm & (t >= 2) & (t <= 3))
    for _ in range(int(len(sy_) / (20 * d * d))):
        q = int(rng.integers(0, len(sy_)))
        y, x = sy_[q], sx_[q]
        t[y, x] = max(1, t[y, x] - 2)
        if x + 1 < Wp and allm[y, x + 1]:
            t[y, x + 1] = max(1, t[y, x + 1] - 1)
    # the outline: dark on the right and the bottom only
    P_ = np.pad(allm, 1)
    rb_ = allm & (~P_[2:, 1:-1] | ~P_[1:-1, 2:])
    out = np.zeros((Hp, Wp, 4), np.uint8)
    names = [fam, fam + '_cool', 'grass_cool']
    for y, x in zip(*np.nonzero(allm)):
        if rb_[y, x] and fm[y, x] != 2:
            out[y, x, :3] = pk.rgb(fam + '_cool', 0)
        else:
            out[y, x, :3] = pk.rgb(names[fm[y, x]], int(t[y, x]))
        out[y, x, 3] = 255
    # pebbles spilling at the foot
    for (pxf, pr) in ((0.52, 1.5), (-0.5, 1.1), (0.66, 0.9))[:int(rng.integers(2, 4))]:
        px_, py_ = ax + pxf * W_ + rng.uniform(-1, 1) * d, ay - 0.6 * d
        pm = ((xx + 0.5 - px_) / (pr * 1.25 * d)) ** 2 + ((yy + 0.5 - py_) / (pr * 0.85 * d)) ** 2 <= 1
        pm &= ~allm
        for y, x in zip(*np.nonzero(pm)):
            up = yy[y, x] < py_
            out[y, x, :3] = pk.rgb(fam, 4 if (up and xx[y, x] < px_) else (3 if up else 1))
            out[y, x, 3] = 255
    img = Image.fromarray(out)
    return img, (ax, ay), out[..., 3] > 0


def fern4(d, seed=51, size=1.0):
    """The 1x fern: a broad, squat crown of pointed leaves (three rising in a V, the others
    spreading level to both sides) round a dark slot at the base; mid green, the east leaves a
    tone down, short pale rib stripes across the leaves, outlined. size 1.23 is the 1x 27 x 17."""
    sp = _sprite(d, 52 * size, 40 * size, 26 * size, 2)
    g = sp.g
    rng = np.random.default_rng(seed)
    k = size
    leaves = [(-148, 18, 3.6), (-118, 17, 3.2), (-96, 21, 3.4), (-78, 20, 3.4), (-60, 17, 3.2), (-32, 18, 3.6),
              (-172, 15, 3.0), (-8, 15, 3.0)]
    order = sorted(range(len(leaves)), key=lambda i: -abs(leaves[i][0] + 90))
    for n_, i in enumerate(order):
        a0, ln, wd = leaves[i]
        a = math.radians(a0 + rng.uniform(-4, 4))
        tx, ty = math.cos(a) * ln * k, math.sin(a) * ln * k * 1.1 - 2 * k
        bx, by = math.cos(a) * 2 * k, -2 * k
        m = g.capsule(bx, by, (bx + tx) / 2, (by + ty) / 2, wd * k * 0.75, wd * k * 0.6) | \
            g.capsule((bx + tx) / 2, (by + ty) / 2, tx, ty, wd * k * 0.6, 0.4)
        east = tx > 2
        nm = f'lf{i}'
        sp.add(nm, m, ('grass_cool', 'leaf', 'grass_cool')[i % 3], base=2 if east else 3, lo=1, hi=4, z=1 + n_ * 0.1, k=0.9)
        # pale rib stripes across the leaf
        for t in (0.35, 0.55, 0.75):
            px_, py_ = bx + (tx - bx) * t, by + (ty - by) * t
            st = g.capsule(px_ - math.sin(a) * 1.8 * k, py_ + math.cos(a) * 1.8 * k,
                           px_ + math.sin(a) * 1.8 * k, py_ - math.cos(a) * 1.8 * k, 0.5) & m
            sp.mark(nm, st, 2)
    # r3: the heart of the crown in the fronds' own shade (no black slot), behind the leaves
    sp.add('slot', g.ellipse(0, -2.0 * k, 4.6 * k, 2.4 * k), 'leaf', base=1, lo=1, hi=2, z=0.5, flat=True, outline=False)
    return _out(sp)


def flowers4(d, seed, kind='white', n=3):
    """Eastward's daisies: small four-petal crosses lying flat on the grass in a group of 2 to 4,
    each with one shade pixel to its lower right; one group in three stands up on a thin stem.
    No leaf block, no outline."""
    rng = np.random.default_rng(seed)
    s = d / 2
    W = int(math.ceil(24 * s)) | 1
    H = int(math.ceil(16 * s))
    out = np.zeros((H, W, 4), np.uint8)
    fam = {'white': 'plaster', 'yellow': 'brass', 'violet': 'dusk', 'red': 'berry', 'blue': 'sky'}[kind]
    upright = rng.random() < 0.33
    cx0, cy0 = W // 2, H - max(1, int(round(1 * s))) - 1
    pr = 1 if d < 2.5 else 2
    def put(y, x, c):
        if 0 <= y < H and 0 <= x < W:
            out[y, x, :3] = c
            out[y, x, 3] = 255
    for k in range(int(rng.integers(1, 5)) if n else 1):
        ang = rng.uniform(0, 2 * math.pi)
        rad = rng.uniform(0.0, 4.5) if k else 0.0
        ox = int(round(math.cos(ang) * rad * s * 1.3))
        oy = -int(round((math.sin(ang) * 0.5 + 0.5) * rad * s))
        x, y = cx0 + ox, cy0 + oy
        if upright and k == 0:
            stem_h = max(2, int(round(5 * s)))
            for j in range(1, stem_h + 1):
                put(y - j + 1, x, pk.rgb('leaf', 2))
            put(y, x + 1, pk.rgb('leaf', 3))
            y -= stem_h
        put(y + 1, x + 1, pk.rgb('grass_cool', 1))
        for (dy, dx) in ((0, -pr), (0, pr), (-pr, 0), (pr, 0)):
            for t in range(pr):
                yy, xx = y + (dy // pr) * (t + 1) if dy else y, x + (dx // pr) * (t + 1) if dx else x
                put(yy, xx, pk.rgb(fam, 5 if (dy < 0 or dx < 0) else 4))
        put(y, x, pk.rgb('brass', 4) if fam == 'plaster' else pk.rgb('plaster', 5))
    return Image.fromarray(out, 'RGBA')
