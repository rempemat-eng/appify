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


# density 3 and up: one trunk painter for every crowned tree (compose.foliage_sprite_hd)
BARK = {
    # family, its base tone, the marks: plates (oak, pine), smooth (beech), dashes (birch)
    'oak': ('timber_cool', 3, 'plates'),
    'pine': ('timber_warm', 2, 'plates'),
    'beech': ('stone', 2, 'smooth'),
    'birch': ('plaster', 3, 'dashes'),
    'sapling': ('timber_cool', 3, 'smooth'),
}


def trunk4(d, length=24.0, trunk_w=8.0, seed=11, bark='oak', flare=1.0, hollow=False):
    """A trunk length world px tall (its top hidden under the crown), trunk_w wide, flaring into
    roots at the ground (flare 0 for a thin stem). Bark lit on the left (a cylinder's ramp), its
    marks per bark kind: broken vertical plates (oak, pine), a few soft rings (beech), dark
    horizontal dashes on pale bark (birch); a knot; roots that meet the ground with their own
    shaded undersides. Returns (img, anchor at the foot, alpha)."""
    fam, base, kind = BARK.get(bark, BARK['oak'])
    L, tw = length * 2, trunk_w * 2
    fl = flare * tw / 22.0
    half = tw / 2
    sp = _sprite(d, tw + 30 * fl + 8, L + 8, (tw + 30 * fl + 8) / 2, 3)
    g = sp.g
    rng = np.random.default_rng(seed)
    top = -L
    pts = [(-half * 0.86, top), (half * 0.86, top), (half, -16 * max(fl, 0.4))]
    if fl > 0.05:
        pts += [(half + 0.8 * fl, -9 * fl), (half + 2.4 * fl, -4.5 * fl), (half + 7 * fl, -0.4), (half + 1.5 * fl, -1.4),
                (2, 0), (-3, -1.0), (-half - 1.5 * fl, -1.4), (-half - 7 * fl, -0.3), (-half - 2.4 * fl, -4.5 * fl),
                (-half - 0.8 * fl, -9 * fl)]
    else:
        pts += [(half, 0), (-half, 0)]
    pts += [(-half, -16 * max(fl, 0.4))]
    tr = pk.round_mask(g.poly(pts), 1)
    sp.add('trunk', tr, fam, base=base, lo=0 if fam.startswith('timber') else 1, hi=min(5, base + 2), z=1, mode='cyl',
           k=1.0)
    if kind == 'plates':
        for j in range(int(5 + tw / 3 + L / 14)):
            x = rng.uniform(-half + 1.5, half - 1.5)
            y0 = rng.uniform(top + 4, -8)
            ln = rng.uniform(5, 11)
            sp.mark('trunk', g.capsule(x, y0, x + rng.uniform(-0.6, 0.6), y0 + ln, 0.6), -1)
            if x < half * 0.3:
                sp.mark('trunk', g.capsule(x - 1.4, y0 + 1, x - 1.4, y0 + ln * 0.6, 0.55), 1)
            else:
                # on the shaded side the plates catch a little reflected light (the bark is never one flat tone)
                sp.mark('trunk', g.capsule(x - 1.2, y0 + 1.5, x - 1.2, y0 + ln * 0.5, 0.6), 1)
        # a cylinder: the core shadow right of centre, the rim beyond it in reflected light; the
        # shaded bark in plates of three tones (reflected light, shade, a dark crack), so the dark
        # side is never one flat tone
        sp.mark('trunk', g.rect(half * 0.35, top, half * 0.7, -3) & tr, -1)
        k = 0
        for yb_ in np.arange(top + 2, -3, 4.5):
            for c, (xa_, xb_) in enumerate(((half * 0.55, half * 0.8), (half * 0.8, half + 2))):
                v = (1, 0, -1)[(k + 2 * c) % 3]
                if v:
                    sp.mark('trunk', g.rect(xa_, yb_ + 0.6 * c, xb_, yb_ + 3.6 + 0.6 * c) & tr, v)
            k += 1
        # the shaded side's bark: short plates in reflected light and dark cracks between them
        for j in range(int(16 + L / 1.5)):
            x = rng.uniform(half * 0.55, half - 0.3)
            y0 = rng.uniform(top + 4, -6)
            ln = rng.uniform(3, 8)
            sp.mark('trunk', g.capsule(x, y0, x, y0 + ln, 1.3), 1 if j % 2 else -1)
    elif kind == 'smooth':
        for j in range(int(2 + L / 22)):
            y = rng.uniform(top + 6, -10)
            sp.mark('trunk', g.ellipse(rng.uniform(-half * 0.3, half * 0.3), y, half * 0.9, 0.7), -1)
        sp.mark('trunk', g.rect(-half - 2, top, -half + max(1.5, tw * 0.18), 0) & tr, 1)
    elif kind == 'dashes':
        # the white bark as a cylinder: a lit band left of centre, a grey core shade on the right,
        # papery patches, then the dark lenticels
        sp.mark('trunk', g.rect(-half * 0.55, top, -half * 0.1, 0) & tr, 1)
        sp.mark('trunk', g.rect(half * 0.35, top, half + 2, 0) & tr, -1)
        for j in range(int(3 + L / 10)):
            y = rng.uniform(top + 3, -4)
            x = rng.uniform(-half, half * 0.2)
            sp.mark('trunk', g.ellipse(x, y, rng.uniform(1.2, 2.2), rng.uniform(0.7, 1.4)) & tr, -1)
        for j in range(int(4 + L / 6)):
            y = rng.uniform(top + 3, -4)
            x = rng.uniform(-half, half * 0.6)
            sp.detail(g.rect(x, y, x + rng.uniform(2.5, 5.5), y + 1.1) & tr, pk.rgb('stone', 1))
    if fl > 0.05:
        for (x0, x1) in ((-half + 1, -half - 6 * fl), (half - 1, half + 6 * fl)):
            sp.mark('trunk', g.capsule(x0, -3, x1, -1.0, 0.8), 1 if x1 < 0 else -1)
    sp.mark('trunk', g.rect(-tw, top - 2, tw, top + 7), -1)        # in the crown's shade at its top
    if hollow:
        # a hollow low in the trunk: a dark opening, its lit lower lip and shaded upper rim, and
        # two eyes watching from inside
        hw, hh = half * 0.42, min(-top * 0.16, half * 0.75)
        hy = -hh - 5
        sp.detail(g.ellipse(0.5, hy, hw + 1.2, hh + 1.2), pk.rgb(fam, 1))
        sp.detail(g.ellipse(0.5, hy + 0.6, hw, hh), pk.rgb('soot', 0))
        sp.detail(g.ellipse(0.5, hy + hh + 0.8, hw * 0.8, 0.8) & ~g.ellipse(0.5, hy + 0.6, hw, hh), pk.rgb(fam, 4))
        for ex_ in (-hw * 0.35, hw * 0.35 + 1):
            sp.detail(g.rect(ex_ - 0.6, hy - 0.6, ex_ + 0.6, hy + 0.6), pk.rgb('brass', 5))
    img, anc, al = _out(sp)
    if kind == 'plates':
        # the shaded side's bark in plates: where the shade is one flat tone, plates of its
        # neighbouring tones in a brick pattern (reflected light, the shade, a dark crack)
        a = np.asarray(img).copy()
        c0, c1, c2 = (np.array(pk.rgb(fam, t)) for t in (0, 1, 2))
        flat = al & (a[..., :3] == c1).all(-1)
        yy, xx = np.nonzero(flat)
        cx_ = anc[0]
        ph = max(2, int(round(1.6 * d)))
        for y, x in zip(yy, xx):
            if x < cx_:
                continue
            q = ((y // (2 * ph)) + (x + (y // (2 * ph)) % 2 * ph) // ph) % 3
            if q == 0:
                a[y, x, :3] = c2
            elif q == 2:
                a[y, x, :3] = c0
        img = Image.fromarray(a)
    return img, anc, al


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
    the lower one west; grain, nail heads, carved marks; a tuft at the foot. At density 3 and up:
    signpost_hd."""
    if d >= 2.5:
        return signpost_hd(d, seed=seed)
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


def _board_hd(F, m, ang, rng, z, fam='timber', s=3.0, seam=True, letters=True):
    """A sawn sign board as a form: its top arris lit, the face in the light with grain running
    along it (broken dashes, a knot), a seam between its two planks, the lower arris and the
    board's thickness in shade, nails with rust runs, carved letters (a dark groove with a lit
    lower lip), a worn pale patch where hands touch it."""
    Y, X = np.mgrid[0:F.h, 0:F.w] + 0.5
    c_, s_ = math.cos(ang), math.sin(ang)
    u = X * c_ + Y * s_
    v = -X * s_ + Y * c_
    um, vm = u[m], v[m]
    u0, u1, v0, v1 = um.min(), um.max(), vm.min(), vm.max()
    fv = (v - v0) / max(1.0, v1 - v0)
    fu = (u - u0) / max(1.0, u1 - u0)
    t = np.full(m.shape, 3.0)
    t = np.where(fv < 0.3, 4, t)
    t = np.where(v - v0 < 1.0, 5, t)
    t = np.where(fv > 0.78, 2, t)
    t = np.where(v1 - v < 1.0, 1, t)
    t = np.where(fu < 0.04, t + 1, t)                                # the lit end grain
    t = np.where(fu > 0.96, t - 1, t)
    # grain along the board, broken
    for k in range(5):
        vg = v0 + (v1 - v0) * rng.uniform(0.18, 0.72)
        wav = 0.6 * np.sin(u / (2.5 * s) + rng.uniform(0, 6))
        run = np.sin(u / rng.uniform(2.0, 3.5) / s + rng.uniform(0, 6)) > -0.2
        t = np.where((np.abs(v - vg - wav) < 0.5) & run & (fv > 0.12) & (fv < 0.75), t - 1, t)
    if seam:
        vs = v0 + (v1 - v0) * 0.5
        t = np.where(np.abs(v - vs) < 0.5, 1, t)
        t = np.where((v - vs >= 0.5) & (v - vs < 1.5), np.minimum(t + 1, 5), t)
    ku = u0 + (u1 - u0) * rng.uniform(0.55, 0.8)
    kv = v0 + (v1 - v0) * rng.uniform(0.25, 0.4)
    kd = np.hypot((u - ku) / (1.3 * s), (v - kv) / (0.8 * s))
    t = np.where(kd < 1, np.where(kd < 0.45, 1, 4), t)
    wp = np.hypot((u - (u0 + (u1 - u0) * 0.3)) / (4 * s), (v - (v0 + (v1 - v0) * 0.55)) / (1.6 * s)) < 1
    t = np.where(wp & (rng.random(m.shape) < 0.5) & (t == 3), 4, t)
    if letters:
        # carved letters: short strokes cut into the face, each a dark groove with a lit lip
        cu = u0 + (u1 - u0) * 0.18
        vl = v0 + (v1 - v0) * 0.38
        for k in range(int(rng.integers(5, 8))):
            w_ = rng.uniform(0.6, 1.6) * s
            tall = rng.random() < 0.5
            gm = (u >= cu) & (u < cu + (0.6 * s if tall else w_)) & (v >= vl) & (v < vl + (1.8 * s if tall else 0.7 * s))
            lip = (u >= cu) & (u < cu + (0.6 * s if tall else w_) + 1) & (v >= vl + (1.8 * s if tall else 0.7 * s)) & \
                  (v < vl + (1.8 * s if tall else 0.7 * s) + 1)
            t = np.where(gm & m, 1, t)
            t = np.where(lip & m, 5, t)
            cu += (0.6 * s if tall else w_) + rng.uniform(0.6, 1.2) * s
    tt = np.clip(np.round(t), 0, 5).astype(int)
    F.put(m, np.where(tt >= 4, fam + '_warm' if fam == 'timber' else fam, np.where(tt <= 1, 'timber_cool', fam)), tt, z)
    for fu_ in (0.07, 0.86):
        nu = u0 + (u1 - u0) * fu_
        nv = v0 + (v1 - v0) * 0.5
        nm_ = (np.abs(u - nu) < 0.55 * s) & (np.abs(v - nv) < 0.55 * s) & m
        F.put(nm_, 'iron', 2, z + 0.1)
        F.put(nm_ & (u < nu) & (v < nv), 'iron', 4, z + 0.11)
        rs = (np.abs(u - nu) < 0.3 * s) & (v > nv + 0.5 * s) & (v < nv + rng.uniform(1.2, 2.2) * s) & m
        F.put(rs, 'fox', 2, z + 0.1)


def signpost_hd(d, seed=91):
    """The signpost at density 3 (fix queue 2): a squared post lit on its west face and shaded on
    the east, its grain, a weathered dark foot set in a tuft and the boards' shadows across it;
    two broad boards (east and west) and a short third arm slanting down to the south-west, each a
    sawn two-plank board with its arrises, grain, a knot, carved names and rusting nails."""
    rng = np.random.default_rng(seed)
    s = d / 2                                     # px per unit (units are half world px)
    W, Hh = int(math.ceil(64 * s)), int(math.ceil(76 * s))
    ox, oy = round(30 * s), Hh - max(1, int(round(3 * s)))
    F = _Form(Hh, W)
    Y, X = np.mgrid[0:Hh, 0:W] + 0.5
    ux, uy = (X - ox) / s, (Y - oy) / s
    post = (np.abs(ux) <= 2.8) & (uy >= -62) & (uy <= 0)
    u = ux / 2.8
    tp = np.where(u < -0.75, 3, np.where(u < -0.1, 4, np.where(u < 0.4, 3, np.where(u < 0.8, 2, 1))))   # a round post
    tp = np.where((uy < -60.5) & (u < 0.4), 5, tp)                   # its cut top catching the light
    for k in range(6):
        gx = rng.uniform(-2.0, 2.0)
        g0 = rng.uniform(-58, -12)
        tp = np.where((np.abs(ux - gx) < 0.45) & (uy > g0) & (uy < g0 + rng.uniform(6, 14)), tp - 1, tp)
    tp = np.where(uy > -5, tp - 1, tp)                                # weathered foot
    for (y0b, y1b) in ((-56, -52), (-33, -29)):
        tp = np.where((uy > y0b) & (uy < y1b), tp - 1, tp)            # the boards' shadows on the post
    tp = np.clip(tp, 0, 5)
    F.put(post, np.where(tp >= 4, 'timber_warm', np.where(tp <= 1, 'timber_cool', 'timber')), tp, 1)
    # (scale gate, 26 Oct: the arms span at most 81 art px, about 1.2 to 1.8 m: each a little shorter)
    b1 = _poly_mask([(ox + x * s, oy + y * s) for x, y in [(-19, -68), (19, -68), (26, -62), (19, -56), (-19, -56)]], X, Y)
    b2 = _poly_mask([(ox + x * s, oy + y * s) for x, y in [(19, -45), (-19, -45), (-26, -39), (-19, -33), (19, -33)]], X, Y)
    b3 = _poly_mask([(ox + x * s, oy + y * s) for x, y in SIGN3], X, Y)
    _board_hd(F, b1, 0.0, rng, 2, 'timber', s)
    _board_hd(F, b2, 0.0, rng, 2, 'timber', s)
    a3 = math.atan2(-19.6 + 28.0, -11.5 - 2.5)
    _board_hd(F, b3, a3 + math.pi, rng, 2.5, 'timber', s, seam=False, letters=False)
    # a tuft at the foot, blades lit on their tips
    for k in range(9):
        bx = ox + rng.uniform(-6, 6) * s
        L = rng.uniform(3, 7) * s
        lean = rng.uniform(-0.5, 0.5)
        for j in range(int(L)):
            yy_, xx_ = int(oy - j), int(bx + lean * j)
            if 0 <= yy_ < Hh and 0 <= xx_ < W:
                m1 = np.zeros((Hh, W), bool)
                m1[yy_, xx_] = True
                F.put(m1, 'leaf', 4 if j > L * 0.6 else (3 if lean < 0 else 2), 3)
    F.tidy()
    img = Image.fromarray(F.image())
    return img, (ox, oy), np.asarray(img)[..., 3] > 0


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
        sp.add('gate', gp, 'timber', base=4 if d >= 2.5 else 3, lo=1, hi=5, z=3, mode='cyl', k=1.1 if d >= 2.5 else 0.8)
        sp.mark('gate', g.rect(0, -40, 13, -38.8), 1)
        for k in range(3):
            gy = rng.uniform(-34, -6)
            sp.mark('gate', g.rect(3 + k * 3.0, gy, 4 + k * 3.0, gy + rng.uniform(5, 9)), -1)
        if d >= 2.5:
            # density 3 (fix queue 2): the post's grain runs its whole height, in long checks and
            # a lighter streak of sapwood, a knot with its dark heart, the foot weathered dark
            rng2 = np.random.default_rng(seed + 7)
            for k in range(7):
                gx = rng2.uniform(2.5, 9.5)
                gy = rng2.uniform(-38, -10)
                sp.mark('gate', g.rect(gx, gy, gx + 0.7, gy + rng2.uniform(8, 16)), -1 if k % 3 else 1)
            sp.mark('gate', g.ellipse(6.5, -22, 1.6, 1.2), -1)
            sp.mark('gate', g.ellipse(6.3, -22.3, 0.7, 0.5), -2)
            sp.mark('gate', g.rect(0, -4, 12, 0), -1)
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
    """A short marker post with a cap (stair heads): 12 world px tall (17 at density 3: the scale
    gate, 26 Oct, a post reaches a person's chest, level with a fence's top rail)."""
    t = 34.0 if d >= 2.5 else 22.0
    sp = _sprite(d, 14, t + 8, 7, 2)
    g = sp.g
    sp.add('post', g.rrect(-2.8, -t, 2.8, 0, 1.0), 'timber', base=3, lo=1, hi=5, z=1, mode='cyl')
    sp.add('cap', g.rrect(-3.6, -t - 3, 3.6, -t + 1, 1.4), 'timber_warm', base=4, lo=2, hi=5, z=2)
    sp.mark('post', g.rect(-4, -t + 8, 4, -t + 9), -1)
    if d >= 2.5:
        rng = np.random.default_rng(seed + 3)
        for k in range(4):
            gx, gy = rng.uniform(-1.6, 1.6), rng.uniform(-t + 4, -4)
            sp.mark('post', g.rect(gx, gy, gx + 0.6, gy + rng.uniform(4, 9)), -1)
        sp.mark('post', g.rect(-3, -3, 3, 0), -1)
    return _out(sp)


def stump4(d, seed=61):
    """The 1x stump (21 x 16 world px): a lit cut top with rings and a crack, bark sides lit on
    the left, root lobes flaring, a tuft at the base. From density 3: stump_hd."""
    if d >= 2.5:
        return stump_hd(d, seed=seed)
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
    over the side, a pale bracket fungus low on its flank. From density 3: log_hd."""
    if d >= 2.5:
        return log_hd(d, length=length, thick=thick, seed=seed)
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
    caps with a pale band on the east, in a ring on a slightly darker patch of grass. At density 3
    and up: mushroom_ring_hd."""
    if d >= 2.5:
        return mushroom_ring_hd(d, w=w, seed=seed, n=n + 4)
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


def boulder4(d, w=21, h=13, seed=31, fam='stone', moss='top'):
    """r7/r8: the 1x grey stone (21 x 13 world px) as two or three chunks of pixel-art stone (Matt:
    rocks read vector-like). r8: rounded chunk outlines, a top plane tilted 5 to 20 degrees, a
    two-tone step from top to side, one crack per stone and no mark crossing it. Each chunk has a flat lit top (tone 4, mottled), a bright rim along
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
        n = 9
        pts = []
        for q in range(n):
            a_ = math.pi + q * math.pi / (n - 1) + rng.uniform(-0.12, 0.12)   # the upper half, left to right
            r_ = rng.uniform(0.86, 1.08)
            r_ = r_ if q not in (2, 3, 4) else min(r_, 0.97)      # a flatter crown: the top is a shelf
            pts.append((cx + math.cos(a_) * cw / 2 * r_, base - ch * 0.45 + math.sin(a_) * ch * 0.55 * r_))
        pts = [(pts[0][0], base - ch * 0.45 + ch * 0.12)] + pts + [(pts[-1][0], base - ch * 0.45 + ch * 0.12)]
        pts += [(cx + cw * 0.46, base - 0.3 * d), (cx + cw * 0.2, base), (cx - cw * 0.25, base), (cx - cw * 0.47, base - 0.4 * d)]
        m = _poly_mask(pts, xx + 0.5, yy + 0.5)
        m = ndi.gaussian_filter(m.astype(float), 0.9 * d) > 0.5          # r8: round the corners
        chunks.append(dict(m=m, cx=cx, cw=cw, ch=ch, base=base, top=base - ch * 1.24))
    t = np.zeros((Hp, Wp), int)
    crack = np.zeros((Hp, Wp), bool)
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
        slope = np.tan(np.radians(rng.uniform(5, 20))) * rng.choice([-1, 1])   # r8: a tilted top plane
        topline = y0 + hh * rng.uniform(0.40, 0.48) + steps - steps[int(min(Wp - 1, max(0, c['cx'])))] \
            + slope * (np.arange(Wp) - c['cx'])
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
        # r8: the step from top to side in two tones: the top's last row and the side's first row
        # a tone 3 band (4 -> 3 -> 2), not a hard edge
        stp = side & np.roll(top, 1, 0)
        stp2 = side & np.roll(stp, 1, 0) & (rel > -0.55)
        tt[stp & (tt == 2)] = 3
        tt[stp2 & (tt == 2) & (rng.random(tt.shape) < 0.5)] = 3
        # one crack per stone (on its first chunk): from the top's front edge down the side, with
        # a lit lip on its left
        cand = np.nonzero(stp & (np.abs(rel) < 0.5))
        if ci == 0 and len(cand[0]):
            q = int(rng.integers(0, len(cand[0])))
            y, x = cand[0][q] - int(1 * d), cand[1][q]
            for _ in range(int(rng.uniform(3, 5.5) * d)):
                if 0 <= y < Hp and 0 <= x < Wp and m[y, x]:
                    tt[y, x] = 0
                    crack[y, x] = True
                    if x - 1 >= 0 and m[y, x - 1] and tt[y, x - 1] > 0:
                        tt[y, x - 1] = min(5, tt[y, x - 1] + 1)
                y += 1
                if rng.random() < 0.35:
                    x += 1 if rng.random() < 0.6 else -1
        # moss on the top's back half ('top'); on a standing stone ('lichen') small patches of
        # lichen on its lit upper flank instead, never a cap on its tip
        if moss == 'lichen':
            ys_, xs_ = np.nonzero(m)
            if len(ys_):
                for _ in range(int(rng.integers(7, 12))):
                    q = int(rng.integers(0, len(ys_)))
                    if ys_[q] < y0 + hh * 0.18 or ys_[q] > y0 + hh * 0.8 or rel[ys_[q], xs_[q]] > 0.25:
                        continue
                    rb = rng.uniform(0.5, 1.0) * d
                    mb = m & ((yy - ys_[q]) ** 2 / 0.6 + (xx - xs_[q]) ** 2 <= rb * rb)
                    fm[mb] = 2
                    tt[mb] = 3
                    tt[mb & ~np.roll(mb, -1, 0)] = 2
            # a standing stone's weathered face: small pits and flakes on its lit planes too
            wy_, wx_ = np.nonzero(m & (tt >= 3))
            for _ in range(int(len(wy_) / (3.5 * d * d))):
                q = int(rng.integers(0, len(wy_)))
                y_, x_ = wy_[q], wx_[q]
                for (dy, dx) in ((0, 0), (0, 1)) if rng.random() < 0.6 else ((0, 0), (1, 0)):
                    if 0 <= y_ + dy < Hp and 0 <= x_ + dx < Wp and m[y_ + dy, x_ + dx] and fm[y_ + dy, x_ + dx] != 2:
                        tt[y_ + dy, x_ + dx] = max(1, tt[y_ + dy, x_ + dx] - 1)
        if top.any() and moss == 'top':
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
        near = ndi.binary_dilation(crack, iterations=2) & ~crack & m & top
        tt[near & (tt == 3)] = 4                    # r8: no worn dash crosses the crack (it read as a '+')
        if d >= 2.5:
            # density 3 (fix queue 2): the stone's own structure at Eastward's detail: a second
            # plane on the front where the face turns (a lit arris then the darker flank), bedding
            # lines across the side with a lit lip under each, a warm iron stain, pits with a lit
            # rim, flecks of quartz on the lit top, lichen rosettes in two greens
            ang_ = rng.uniform(-0.5, 0.5)
            fac = side & ((rel + ang_ * (yy - c['base']) / max(1.0, c['ch'])) > rng.uniform(0.05, 0.25))
            arr = fac & ~np.roll(fac, 1, 1)
            tt[fac & (tt >= 2)] -= 1
            tt[arr & (tt <= 3)] = np.minimum(4, tt[arr & (tt <= 3)] + 2)
            blo, bhi = topline.mean() + 1.5 * d, c['base'] - 1.5 * d
            for _ in range(int(rng.integers(1, 3)) if bhi > blo else 0):       # (a low chunk has no room for beds)
                by_ = rng.uniform(blo, bhi)
                wob = 0.6 * d * np.sin(xx / (2.3 * d) + rng.uniform(0, 6))
                bed = side & (np.abs(yy - by_ - wob - (xx - c['cx']) * rng.uniform(-0.15, 0.15)) < 0.5)
                lipb = side & np.roll(bed, 1, 0) & ~bed
                tt[bed] = np.maximum(0, tt[bed] - 1)
                tt[lipb & (tt <= 3)] += 1
            st_ = m & (fm == 0) & ((xx - c['cx'] - rng.uniform(-0.3, 0.3) * c['cw'] / 2) ** 2 / (1.6 * d) ** 2
                                   + (yy - c['base'] + c['ch'] * 0.35) ** 2 / (1.1 * d) ** 2 < 1)
            fm[st_ & (rng.random(st_.shape) < 0.8)] = 3
            wy2, wx2 = np.nonzero(m & (fm != 2))
            for _ in range(int(len(wy2) / (2.2 * d * d))):
                q2 = int(rng.integers(0, len(wy2)))
                y_, x_ = wy2[q2], wx2[q2]
                if crack[y_, x_]:
                    continue
                if top[y_, x_]:
                    if x_ + 1 < Wp and m[y_, x_ + 1]:
                        tt[y_, x_] = 5
                        tt[y_, x_ + 1] = min(5, tt[y_, x_ + 1] + 1)
                else:
                    tt[y_, x_] = max(0, tt[y_, x_] - 2)
                    if y_ + 1 < Hp and m[y_ + 1, x_]:
                        tt[y_ + 1, x_] = min(4, tt[y_ + 1, x_] + 1)
            ly_, lx_ = np.nonzero(m & (fm != 2) & ~crack)
            for _ in range(int(rng.integers(3, 6))):
                q2 = int(rng.integers(0, len(ly_)))
                if rel[ly_[q2], lx_[q2]] > 0.5:
                    continue
                lr = rng.uniform(0.6, 1.0) * d
                lm_ = m & ((yy - ly_[q2]) ** 2 / 0.5 + (xx - lx_[q2]) ** 2 <= lr * lr)
                fm[lm_] = 4
                tt[lm_] = 3
                tt[lm_ & ~np.roll(lm_, 1, 0)] = 4
                tt[lm_ & ~np.roll(lm_, -1, 0)] = 2
        tt[~m] = 0
        t[m] = tt[m]
        fm[m & (fm != 2)] = np.where(rel[m & (fm != 2)] > 0.15, 1, 0)
    # the crevice: the back chunk darkens along the front chunk's edge
    for ci in range(len(chunks)):
        front = own == ci
        ring = ndi.binary_dilation(front) & ~front & allm & (own < ci)
        if front.any():
            ring &= yy < np.nonzero(front)[0].mean()       # r9: an arc over the front chunk, never a ring round it
        t[ring] = 0
    # small pits on the sides
    sy_, sx_ = np.nonzero(allm & (t >= 2) & (t <= 3) & ~ndi.binary_dilation(crack, iterations=3))
    for _ in range(int(len(sy_) / ((5 if moss == 'lichen' else 20) * d * d))):
        q = int(rng.integers(0, len(sy_)))
        y, x = sy_[q], sx_[q]
        t[y, x] = max(1, t[y, x] - 2)
        if x + 1 < Wp and allm[y, x + 1]:
            t[y, x + 1] = max(1, t[y, x + 1] - 1)
    # the outline: dark on the right and the bottom only
    P_ = np.pad(allm, 1)
    rb_ = allm & (~P_[2:, 1:-1] | ~P_[1:-1, 2:])
    out = np.zeros((Hp, Wp, 4), np.uint8)
    names = [fam, fam + '_cool', 'grass_cool', fam + '_warm' if d >= 2.5 else fam, 'leaf']
    for y, x in zip(*np.nonzero(allm)):
        if rb_[y, x] and fm[y, x] != 2:
            out[y, x, :3] = pk.rgb(fam + '_cool', 0)
        else:
            out[y, x, :3] = pk.rgb(fam if (t[y, x] >= 5 and fm[y, x] == 1) else names[fm[y, x]], int(t[y, x]))   # r8: no stone_cool 5
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
    tone down, short pale rib stripes across the leaves, outlined. size 1.23 is the 1x 27 x 17.
    At density 3 and up the fern is drawn as fronds of paired leaflets (fern_hd; fix queue 2: the
    pointed-leaf crown read as an agave)."""
    if d >= 2.5:
        return fern_hd(d, seed=seed, size=size)
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


# ------------------------------------------------------------------------------------------------
# density 3 and up: the woodland's low plants and mushrooms (25 Oct)
# ------------------------------------------------------------------------------------------------
def _rgba(h, w):
    return np.zeros((h, w, 4), np.uint8)


def _put(a, y, x, fam, t):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x, :3] = pk.rgb(fam, t)
        a[y, x, 3] = 255


def _finish(a):
    img = Image.fromarray(a, 'RGBA')
    al = a[..., 3] > 0
    ys, xs = np.nonzero(al)
    return img, ((xs.min() + xs.max() + 1) / 2.0, ys.max() + 1.0), al


def mushrooms_hd(d, n=5, seed=0, kind='brown'):
    """A cluster of n mushrooms at ankle height (1.5 to 4 world px), the tallest at the back,
    leaning a little apart: a pale stem lit on the left, a domed cap lit at its upper left with
    a dark gill line under its rim (and white flecks on the red kind)."""
    rng = np.random.default_rng(seed)
    Wd, Hd = int(10 * d), int(7 * d)
    a = _rgba(Hd, Wd)
    caps = {'brown': ('clay', 'brass_warm'), 'red': ('berry', 'berry')}[kind]
    items = []
    for k in range(n):
        x = Wd / 2 + rng.uniform(-3.4, 3.4) * d
        h = rng.uniform(1.5, 3.8) * d
        cw = rng.uniform(1.8, 3.2) * d
        items.append((h, x, cw))
    items.sort(key=lambda t: -t[0])                    # tall ones behind
    for j, (h, x, cw) in enumerate(items):
        foot = Hd - 1 - int(rng.integers(0, max(1, int(1.6 * d))))
        top = int(foot - h)
        sw = max(1, int(round(0.55 * d)))
        lean = rng.uniform(-0.12, 0.12)
        for y in range(top, foot + 1):
            xc = int(round(x + lean * (foot - y)))
            for i in range(sw + 1):
                _put(a, y, xc - sw // 2 + i, 'plaster', 4 if i == 0 else (3 if i < sw else 2))
        xc = int(round(x + lean * (foot - top)))
        ch = max(2, int(round(cw * 0.55)))
        fam = caps[j % 2]
        for yy in range(ch):
            half = cw / 2 * np.sqrt(max(0.0, 1 - ((ch - 1 - yy) / ch) ** 2)) + 0.4
            for xx in range(int(round(xc - half)), int(round(xc + half)) + 1):
                u = (xx - (xc - half)) / max(1.0, 2 * half)
                t = 4 if (yy < ch * 0.45 and u < 0.45) else (3 if u < 0.8 else 2)
                _put(a, top - ch + 1 + yy, xx, fam, t)
        for xx in range(int(round(xc - cw / 2)), int(round(xc + cw / 2)) + 1):
            _put(a, top + 1, xx, fam, 1)               # the gills' dark line under the rim
        if kind == 'red':
            _put(a, top - ch + 2, int(xc - cw / 5), 'plaster', 5)
            _put(a, top - 1, int(xc + cw / 5), 'plaster', 5)
    return _finish(a)


def _mushroom(a, x, foot, h, cw, fam, red, rng):
    """One mushroom at ankle height: a pale stem lit on its west side with a dark foot, a domed cap
    lit at its upper left, its rim's underside (the gills) a dark line, white flecks on a red one."""
    top = int(round(foot - h))
    sw = max(2, int(round(0.55 * cw / 2.4 * 2)))
    lean = rng.uniform(-0.15, 0.15)
    for y in range(top, foot + 1):
        xc = int(round(x + lean * (foot - y)))
        for i in range(sw):
            t = 5 if i == 0 else (4 if i < sw - 1 else 2)
            if y >= foot - 1:
                t = max(1, t - 2)
            _put(a, y, xc - sw // 2 + i, 'plaster', t)
    xc = x + lean * (foot - top)
    ch = max(2, int(round(cw * 0.5)))
    for yy in range(ch):
        half = cw / 2 * np.sqrt(max(0.0, 1 - ((ch - 1 - yy) / ch) ** 2)) + 0.4
        for xx in range(int(round(xc - half)), int(round(xc + half)) + 1):
            u = (xx - (xc - half)) / max(1.0, 2 * half)
            t = 5 if (yy < ch * 0.35 and 0.15 < u < 0.4) else (4 if (yy < ch * 0.6 and u < 0.5) else (3 if u < 0.78 else 2))
            _put(a, top - ch + 1 + yy, xx, fam, t)
    for xx in range(int(round(xc - cw / 2)), int(round(xc + cw / 2)) + 1):
        _put(a, top + 1, xx, fam, 1)
    if red:
        for (fx, fy) in ((-0.22, 0.3), (0.18, 0.55), (-0.02, 0.75))[:int(rng.integers(2, 4))]:
            _put(a, top - int(ch * fy), int(round(xc + fx * cw)), 'plaster', 5)


def mushroom_ring_hd(d, w=41, seed=85, n=12):
    """A fairy ring at density 3: ankle-high mushrooms (1.5 to 4 world px) standing round a ring
    w world px across, seen at the view's slant, at uneven spacing: some alone, some in twos and
    threes, the young ones small, each its own size and lean; red caps with white flecks on the
    west side, tan caps on the east. No painted patch: the ring is the mushrooms."""
    rng = np.random.default_rng(seed)
    Wd = int((w + 6) * d)
    ry = (w / 2 - 3) * 0.42
    Hd = int((2 * ry + 7) * d)
    a = _rgba(Hd, Wd)
    rx = (w / 2 - 3) * d
    cy = Hd - 1 - (ry + 1) * d
    items = []
    tops = []
    ang = rng.uniform(0, 2 * np.pi)
    tries = 0
    while len(items) < n and tries < 400:
        tries += 1
        ang += rng.uniform(0.25, 0.8)
        grp = int(rng.choice([1, 1, 2]))
        for g_ in range(grp):
            aa = ang + g_ * rng.uniform(0.16, 0.22)
            rr = rng.uniform(0.9, 1.08)
            x = Wd / 2 + np.cos(aa) * rx * rr
            foot = int(cy + np.sin(aa) * ry * d * rr)
            h = rng.uniform(1.1, 2.1) * d * (0.75 if g_ else 1.0)
            cw = rng.uniform(1.8, 2.8) * d * (0.8 if g_ else 1.0)
            top = int(round(foot - h)) - max(2, int(round(cw * 0.5))) + 1
            # no three caps on one line (a grown ring, not a planted row) and none on another's spot
            if any(abs(t - top) <= 2 for t in tops):
                continue
            if any(abs(it[1] - x) < (cw + it[3]) / 2 + 2 and abs(it[0] - foot) < 6.5 * d for it in items):
                continue
            tops.append(top)
            items.append((foot, x, h, cw))
    items.sort()
    for (foot, x, h, cw) in items:
        red = x < Wd * 0.48 or (x < Wd * 0.58 and rng.random() < 0.4)
        _mushroom(a, x, foot, h, cw, 'berry' if red else 'clay', red, rng)
    return _finish(a)


def fern_hd(d, seed=0, size=1.0):
    """A fern (knee high, 8 to 16 world px across): fronds arching up out of one crown and
    bending down at their tips, each a midrib with leaflets in pairs that shorten to the tip and
    point out along it; the fronds at the back in shade, those facing the upper left lit."""
    rng = np.random.default_rng(seed)
    Wd, Hd = int(15 * size * d), int(10 * size * d)          # (scale gate: about 0.5 A across, Eastward 0.37 to 0.46)
    a = _rgba(Hd, Wd)
    bx, by = Wd / 2, Hd - 1.5
    n = int(rng.integers(7, 10))
    fronds = []
    for k in range(n):
        f = (k + rng.uniform(-0.25, 0.25)) / (n - 1)          # 0 west .. 1 east
        dirx = (f - 0.5) * 2
        el = np.radians(80 - 55 * abs(dirx) + rng.uniform(-6, 6))
        L = rng.uniform(5.2, 6.8) * size * d * (0.85 if abs(dirx) < 0.3 else 1.0)
        back = abs(dirx) < 0.35
        fronds.append((0 if back else 1, dirx, el, L))
    fronds.sort(key=lambda q: (q[0], -abs(q[1])))
    for (front, dirx, el, L) in fronds:
        sx_ = 1 if dirx >= 0 else -1
        P0 = np.array([bx, by])
        P1 = P0 + np.array([dirx * L * 0.3 + sx_ * L * 0.1, -L * 1.5 * np.sin(el)])
        P2 = P0 + np.array([dirx * L * 0.95 + sx_ * L * 0.22, -L * 0.45 * np.sin(el)])
        lit = dirx < 0.25
        base_t = 3 if (lit and front) else 2
        steps = int(L * 2)
        notch = max(2, int(round(0.8 * d)))
        for i in range(steps):
            t = i / max(1, steps - 1)
            pt = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * P1 + t * t * P2
            tg = 2 * (1 - t) * (P1 - P0) + 2 * t * (P2 - P1)
            tg = tg / max(1e-6, np.hypot(*tg))
            nrm = np.array([-tg[1], tg[0]])
            half = (0.25 + 0.75 * np.sin(np.pi * min(1.0, t * 1.15))) * 1.5 * size * d
            if (i // notch) % 2:
                half *= 0.6                                 # the gaps between leaflets
            for q in np.arange(-half, half + 0.01, 0.5):
                pq = pt + nrm * q
                up = (nrm * np.sign(q))[1] < 0 if q != 0 else False
                tt = base_t + (1 if (up and abs(q) > half * 0.35) else 0) - (1 if abs(q) < 0.5 else 0)
                _put(a, int(pq[1]), int(pq[0]), 'leaf', int(np.clip(tt, 1, 4)) if front else int(np.clip(tt - 1, 0, 3)))
    for k in range(int(2.5 * d)):
        _put(a, int(by), int(bx - 1.2 * d + k), 'leaf', 0)
        _put(a, int(by) - 1, int(bx - 0.8 * d + k * 0.7), 'leaf', 1)
    return _finish(a)


def foxglove_hd(d, seed=0, size=1.0):
    """A foxglove: a rosette of broad leaves on the ground and a spike (12 to 18 world px) hung
    with pink bells down one side, the lowest open (a dark mouth with a pale lip), buds at the
    top; the spike lit on its left."""
    rng = np.random.default_rng(seed)
    Wd, Hd = int(12 * d), int(19 * size * d)
    a = _rgba(Hd, Wd)
    cx = Wd / 2
    top = int(Hd - 17 * size * d)
    for y in range(top, Hd - 1):                        # the stem
        _put(a, y, int(cx), 'leaf', 2)
    nb = int(rng.integers(5, 8))
    for i in range(nb):                                 # the bells, low ones open
        y = int(Hd - 6 * d - i * (11 * size * d - 2) / nb)
        side = 1 if i % 2 else -1
        rows = [max(2, int(round(1.0 * d))), max(3, int(round(1.4 * d))), max(3, int(round(1.4 * d))), max(4, int(round(1.8 * d)))]
        if i >= nb - 2:
            rows = rows[:2]                             # buds at the top
        for r_, bw in enumerate(rows):
            x0 = int(cx + 1) if side > 0 else int(cx - bw)
            for xx in range(bw):
                t = 4 if xx == (0 if side < 0 else 0) and r_ < 2 else 3
                if r_ == len(rows) - 1 and len(rows) == 4:
                    t = 1 if 0 < xx < bw - 1 else 3
                _put(a, y + r_, x0 + xx, 'berry', t)
        if len(rows) == 4:
            x0 = int(cx + 1) if side > 0 else int(cx - rows[3])
            _put(a, y + 4, x0 + rows[3] // 2, 'plaster', 5)
    for k in range(5):                                  # the rosette
        ang = np.radians(-180 + 45 * k + rng.uniform(-10, 10))
        L = rng.uniform(4.5, 6.5) * d
        for q in range(int(L)):
            w = max(1, int((1 - abs(q / L - 0.45) * 1.6) * 1.6 * d))
            x = cx + np.cos(ang) * q
            y = Hd - 2 + np.sin(ang) * q * 0.4
            for j in range(w):
                _put(a, int(y - j * 0.5), int(x), 'leaf', 3 if (k < 2 and j == w - 1) else 2)
    return _finish(a)


# ------------------------------------------------------------------------------------------------
# density 3 and up: the woodland's stump and fallen log drawn as forms (26 Oct, fix queue)
# ------------------------------------------------------------------------------------------------
# Matt, 26 Oct: "make sure you get the 3d effect right every time" (a lit top and face, a form
# shadow, contact, thickness and depth overlap). These painters shade every pixel from the
# form's own normal against the house light (upper left and above), then lay the material's
# structure (bark plates and furrows, rings and checks, moss cushions) on top as tone steps,
# and close the silhouette in each material's own edge tone. Density 2 keeps stump4 and log4
# (the approved pilot golden).
LIGHT3 = (-0.55, -0.30, 0.78)          # towards the light: west, north, up (east, south, up axes)


class _Form:
    """A small painter in (family, tone) per pixel with a z-buffer (larger z is nearer)."""

    def __init__(self, h, w):
        self.h, self.w = h, w
        self.tone = np.full((h, w), -1, int)
        self.fam = np.full((h, w), -1, int)
        self.z = np.full((h, w), -1e9)
        self.fams: list = []

    def fi(self, f):
        if f not in self.fams:
            self.fams.append(f)
        return self.fams.index(f)

    def put(self, mask, fam, tone, z=0.0):
        """Paint `mask` (bool array) in `fam` (a name, or a per-pixel array of names) at `tone`
        (an int or an array) where nothing nearer is already drawn."""
        sel = mask & (z >= self.z)
        if not sel.any():
            return
        t = np.broadcast_to(np.asarray(tone), mask.shape)
        self.tone[sel] = np.clip(t[sel], 0, 5)
        if isinstance(fam, str):
            self.fam[sel] = self.fi(fam)
        else:
            for f in np.unique(fam[sel]):
                s2 = sel & (fam == f)
                self.fam[s2] = self.fi(str(f))
        self.z[sel] = z

    def step(self, mask, dt, lo=0, hi=5):
        sel = mask & (self.tone >= 0)
        self.tone[sel] = np.clip(self.tone[sel] + dt, lo, hi)

    def tidy(self, mc=2):
        """No lone pixels: a tone patch smaller than mc takes its commonest neighbour."""
        solid = self.tone >= 0
        for _ in range(2):
            for f in np.unique(self.fam[solid]):
                part = solid & (self.fam == f)
                for tv in np.unique(self.tone[part]):
                    sel = part & (self.tone == tv)
                    lab, n = ndi.label(sel)
                    if not n:
                        continue
                    sizes = ndi.sum(sel, lab, range(1, n + 1))
                    for k, sz in enumerate(sizes, 1):
                        if sz >= mc:
                            continue
                        blob = lab == k
                        ring = ndi.binary_dilation(blob) & ~blob & part
                        if ring.any():
                            v, c = np.unique(self.tone[ring], return_counts=True)
                            self.tone[blob] = v[c.argmax()]

    def image(self, outline=True):
        H, W = self.h, self.w
        out = np.zeros((H, W, 4), np.uint8)
        solid = self.tone >= 0
        for y, x in zip(*np.nonzero(solid)):
            out[y, x, :3] = pk.rgb(self.fams[self.fam[y, x]], int(self.tone[y, x]))
            out[y, x, 3] = 255
        if outline:
            ring = ndi.binary_dilation(solid, ndi.generate_binary_structure(2, 1)) & ~solid
            for y, x in zip(*np.nonzero(ring)):
                best = None
                for dx, dy, lit in ((0, 1, True), (1, 0, True), (-1, 0, False), (0, -1, False)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and solid[yy, xx]:
                        best = (yy, xx, lit)
                        break
                yy, xx, lit = best
                f = self.fams[self.fam[yy, xx]]
                out[y, x, :3] = pk.rgb(f, 1) if (lit and self.tone[yy, xx] >= 4) else pk.rgb(f, 6)
                out[y, x, 3] = 255
        return out


def _lambert(nx, ny, nz):
    """Light on a normal (east, south, up) from the house light: -1 .. 1."""
    lx, ly, lz = LIGHT3
    return nx * lx + ny * ly + nz * lz


def _bark_fam(t):
    """Bark in three hues: warm where lit, the body, cool in shade (hue-shifted ramps)."""
    return np.where(t >= 4, 'timber_warm', np.where(t <= 1, 'timber_cool', 'timber'))


def _moss(F, cx, cy, r, z, rng, s):
    """A moss cushion: a dome of short leaf clusters, lit cap upper left, a dark tuck under it."""
    Y, X = np.mgrid[0:F.h, 0:F.w]
    ang = np.arctan2(Y - cy, X - cx)
    rr = r * (1 + 0.16 * np.sin(5 * ang + rng.uniform(0, 6)) + 0.08 * np.sin(9 * ang + rng.uniform(0, 6)))
    dx, dy = (X - cx) / rr, (Y - cy) / (rr * 0.8)
    m = dx * dx + dy * dy <= 1.0
    if not m.any():
        return m
    nz = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1))
    I = _lambert(dx, dy * 0.6, nz)
    t = np.clip(np.round(1.6 + I * 2.6), 1, 5).astype(int)
    # leaf-scale clusters: a lit tip in each small clump
    q = max(2, int(round(0.9 * s)))
    cl = ((X // q + (Y // q) * 3 + int(rng.integers(0, 5))) % 4 == 0) & (t >= 3)
    t = np.where(cl, np.minimum(5, t + 1), t)
    F.put(m, np.where(t >= 4, 'leaf_warm', 'leaf'), t, z)
    tuck = ndi.binary_dilation(m, iterations=1) & ~m & (np.roll(m, 2, axis=0) | np.roll(m, 1, axis=0)) & (F.tone >= 0)
    F.step(tuck & (F.z < z), -2, lo=0)
    return m


def stump_hd(d, seed=61):
    """The woodland stump (21 x 16 world px) at density 3 and up: a cut top lit as a plane (rings,
    a dark heart, radial checks, a pale sapwood band and the bark's rim showing its thickness), a
    bark cylinder lit on the left with its core shadow right of centre and a faint bounce at the
    right edge, furrowed plates that wrap round the form, roots flaring out with lit tops and
    shaded undersides, a moss cushion at the shaded foot and ambient occlusion where it meets
    the ground."""
    s = d
    rng = np.random.default_rng(seed)
    R, ry, ht = 7.6 * s, 2.9 * s, 8.6 * s           # body radius, top ellipse half height, side height
    W, Hh = int(round(2 * R + 13 * s)), int(round(ht + 2 * ry + 4.5 * s))
    F = _Form(Hh, W)
    cx = W / 2.0
    base = Hh - 1.6 * s                              # the centre of the base ellipse
    top = base - ht
    Y, X = np.mgrid[0:Hh, 0:W] + 0.5
    # the side: a cylinder flaring over its lowest 3 world px
    hgt = np.clip((base - Y) / ht, -0.5, 1.5)
    flare = 1.0 + 0.2 * np.clip(1 - (base - Y) / (3.2 * s), 0, 1) ** 2
    r = R * flare
    u = (X - cx) / r
    inside = np.abs(u) <= 1
    arc = ry * np.sqrt(np.clip(1 - u * u, 0, 1))
    h_on = base + arc - Y                            # height on the surface above the ground line
    side = inside & (h_on >= 0) & (h_on <= ht + arc)
    nzs = np.sqrt(np.clip(1 - u * u, 0, 1))
    I = _lambert(u, nzs, 0.12)
    t = 2.8 + 2.6 * I
    t = t + np.where(u > 0.82, 0.6, 0)               # bounce light on the far right rim
    # furrows: grooves at fixed angles that wrap with the cylinder (narrow towards the rims)
    phis = np.sort(rng.uniform(-1.45, 1.45, 9))
    ang = np.arcsin(np.clip(u, -1, 1))
    groove = np.zeros_like(side)
    core = np.zeros_like(side)
    litwall = np.zeros_like(side)
    for k, ph in enumerate(phis):
        wob = 0.05 * np.sin(h_on / (1.7 * s) + k * 1.7)
        dist = (ang - ph - wob) * r
        hw = 0.28 * s * np.cos(ph) + 0.3
        top_k = ht * rng.uniform(0.55, 1.0)
        run = side & (h_on < top_k + arc)
        groove |= run & (np.abs(dist) < hw)
        core |= run & (np.abs(dist) < 0.5)
        litwall |= run & (dist >= hw) & (dist < hw + 1.2)
    # plate breaks: short horizontal checks between furrows
    breaks = np.zeros_like(side)
    for _ in range(7):
        ph = rng.uniform(-1.2, 1.2)
        hh = rng.uniform(0.18, 0.8) * ht
        breaks |= side & (np.abs(ang - ph) < 0.22) & (np.abs(h_on - arc - hh) < 0.5)
    t = t - 1.2 * groove - 1.0 * core + 0.9 * (litwall & ~groove) - 1.0 * breaks
    t = t - np.where(h_on < 0.9 * s, 1.0, 0) - np.where(h_on < 0.45 * s, 0.6, 0)   # occlusion at the foot
    # in the core shadow the furrows read as dark seams between the plates
    seam = (np.round(ang * r / max(2.0, 0.9 * s)) % 3 == 0) & (np.round(h_on) % 5 != 0)
    t = np.where((t < 1.6) & seam, 0, t)
    ts = np.clip(np.round(t), 0, 5).astype(int)
    F.put(side, _bark_fam(ts), ts, z=1)
    # roots: lobes that leave the base and taper into the ground, lit on top, dark below
    for (sx, ln, dy0, rw) in ((-1, 3.4, 0.2, 2.3), (1, 3.0, 0.0, 2.1), (-0.35, 2.0, 1.0, 1.7), (0.55, 2.2, 0.9, 1.6)):
        x0 = cx + sx * R * 0.92 if abs(sx) == 1 else cx + sx * R
        y0 = base + dy0 * s + (0.6 * s if abs(sx) < 1 else -0.6 * s)
        x1 = x0 + np.sign(sx) * ln * s
        y1 = y0 + 0.9 * s + 0.6 * s * (abs(sx) < 1)
        tt = np.clip(((X - x0) * (x1 - x0) + (Y - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2), 0, 1)
        px, py = x0 + tt * (x1 - x0), y0 + tt * (y1 - y0)
        rad = rw * s * (1 - 0.6 * tt ** 1.5) + 0.4
        dd = np.hypot(X - px, (Y - py) * 1.25)
        m = dd <= rad
        v = np.clip((Y - py) / np.maximum(rad, 1e-3), -1, 1)   # -1 top .. 1 underside
        It = _lambert(np.sign(sx) * 0.25 * tt, 0.3 * v, np.sqrt(np.clip(1 - v * v, 0, 1)) * (v < 0.3))
        tr = np.clip(np.round(2.2 + 2.3 * It - 1.2 * (v > 0.45) - 0.9 * (sx > 0)), 0, 5).astype(int)   # east roots in the stump's shade
        F.put(m & (F.z < 1.5), _bark_fam(tr), tr, z=0.8 + 0.1 * (abs(sx) < 1))
    # the cut top: a lit plane, rings round a dark heart, checks, the sapwood and the bark rim
    tcx, tcy = cx - 0.15 * s, top
    du, dv = (X - tcx) / R, (Y - tcy) / ry
    rho = np.sqrt(du * du + dv * dv)
    topm = rho <= 1.0
    th = np.arctan2(dv, du)
    rho_w = rho * (1 + 0.035 * np.sin(3 * th + 1.1) + 0.02 * np.sin(7 * th))
    # a weathered top domes a little: lit to the upper left, a tone down to the lower right
    tt = 4.0 + 0.7 * np.clip(-(du + dv * 0.5), 0, 1) - 1.3 * np.clip(du + dv * 0.5, 0, 1)
    rings = np.zeros_like(topm)
    for rk in (0.2, 0.36, 0.5, 0.63, 0.74):
        rings |= np.abs(rho_w - rk) < 0.04 + 0.6 / R
    tt = tt - 1.6 * rings
    tt = np.where(rho_w < 0.1, 2.0, tt)                                     # the heart
    sap = (rho_w > 0.8) & (rho_w <= 0.87)
    tt = np.where(sap, 5.0, tt)
    checks = np.zeros_like(topm)
    for a0 in (rng.uniform(-0.6, 0.0), rng.uniform(2.2, 2.8), rng.uniform(0.8, 1.4)):
        checks |= (np.abs(np.angle(np.exp(1j * (th - a0)))) < 0.05 + 0.4 / (rho * R + 1)) & (rho_w > 0.12) & (rho_w < 0.78)
    tt = tt - 1.6 * checks
    ttop = np.clip(np.round(tt), 1, 5).astype(int)
    famt = np.where(ttop >= 5, 'plaster', np.where(ttop <= 1, 'plaster_cool', 'plaster_warm'))
    F.put(topm & (rho_w <= 0.87), famt, ttop, z=3)
    bark_rim = topm & (rho_w > 0.87)
    rim_t = np.where(dv < 0, 4, np.where(du < -0.2, 3, 2))                  # the back rim lit, the near rim in shade
    F.put(bark_rim, _bark_fam(rim_t), rim_t, z=3)
    # moss: a cushion at the damp west foot and a smaller one on the east root
    _moss(F, cx - 0.6 * R, base + 0.3 * s, 2.2 * s, 2.5, rng, s)
    _moss(F, cx + 0.95 * R + 1.6 * s, base + 0.9 * s, 1.2 * s, 2.5, rng, s)
    F.tidy(2)
    return _finish(F.image())


def log_hd(d, length=54, thick=15, seed=71):
    """The woodland's fallen log (length x thick/2 world px) at density 3 and up: a bark cylinder
    lying east-west, lit along its upper back, its core shadow on the near flank, a bounce of
    light under it and occlusion at the ground; furrowed plates running along it with lit lips,
    a knot and a branch stub; the sawn end facing west and lit (rings, checks, sapwood, the bark's
    thickness round it); the east end broken off in splinters; moss in cushions along the top
    with drips down the flank; a bracket fungus in two shelves on the shaded side."""
    s = d
    rng = np.random.default_rng(seed)
    Lw, Dm = length * s, thick * s                   # the log's length and its drawn depth (world px)
    R = Dm / 2.0
    W, Hh = int(round(Lw + 6 * s)), int(round(Dm + 5 * s))
    F = _Form(Hh, W)
    x0, x1 = 3.0 * s, 3.0 * s + Lw                   # west and east ends
    cy = Hh - 2.2 * s - R                            # the axis on screen
    Y, X = np.mgrid[0:Hh, 0:W] + 0.5
    yn = (Y - cy) / R                                # -1 top edge .. 1 bottom edge
    th = np.radians(45) + np.arcsin(np.clip(yn, -1, 1))     # the surface angle: 0 straight up, 90 facing south
    # the east end broken off in 3 to 5 splinters (#288 second review S1: four equal symmetric
    # cones read as stakes): bands of unequal width, each splinter's point off its centre so it
    # leans, lengths from stubby to long, and the roots at different depths so the break has a
    # hollow among them
    ns = int(rng.integers(3, 6))
    bands = np.concatenate([[0.0], np.cumsum(rng.dirichlet(np.full(ns, 1.6)))])
    bands[-1] = 1.0
    lens = rng.permutation(np.linspace(1.0, 5.6, ns) * rng.uniform(0.85, 1.15, ns)) * s
    pkv = rng.uniform(0.2, 0.8, ns)                     # where along its band each point sits
    root = rng.uniform(-1.4, 0.4, ns) * s                # the depth each splinter breaks from
    vv = np.clip((Y - (cy - R)) / (2 * R), 0, 1)
    bi = np.clip(np.searchsorted(bands, vv, side='right') - 1, 0, ns - 1)
    b0, b1 = bands[bi], bands[np.minimum(bi + 1, ns)]
    fr_ = (vv - b0) / np.maximum(1e-3, b1 - b0)
    pkb = pkv[bi]
    tip = np.where(fr_ < pkb, fr_ / pkb, (1 - fr_) / (1 - pkb))         # 0 at a splinter's sides, 1 at its point
    upper = fr_ < pkb                                                    # its upper facet (towards the light)
    jag = x1 - 2.4 * s + root[bi] + lens[bi] * np.clip(tip, 0, 1) ** 0.7
    body = (np.abs(yn) <= 1) & (X >= x0) & (X <= jag)
    I = _lambert(-0.12 * (X - (x0 + x1) / 2) / Lw, np.sin(th), np.cos(th))
    t = 2.3 + 2.4 * I
    t = t + np.where((yn > 0.62) & (yn < 0.84), 0.7, 0)                  # bounce light under the flank
    t = t - np.where(yn > 0.9, 1.0, 0)                                  # occlusion on the ground
    t = t + np.where((yn > 0.86) & (np.sin(X / (1.9 * s)) + 0.6 * np.sin(X / (0.8 * s) + 1.0) > 0.7), 0.8, 0)  # bark lumps catch the bounce
    # bark: furrows along the log, wavy, broken into plates; the lip below each lit
    groove = np.zeros_like(body)
    core = np.zeros_like(body)
    lip = np.zeros_like(body)
    for k, a in enumerate(np.linspace(-0.75, 0.82, 6)):
        wv = 0.05 * np.sin(X / (6.0 * s) + k * 1.3) + 0.03 * np.sin(X / (2.1 * s) + k)
        dd = (yn - a - wv) * R                                    # texels from the furrow's line
        cut = np.sin(X / (rng.uniform(2.4, 3.6) * s) + rng.uniform(0, 6)) > -0.55
        groove |= body & cut & (np.abs(dd) < 1.0)
        core |= body & cut & (np.abs(dd) < 0.5)
        lip |= body & cut & (dd >= 1.0) & (dd < 2.2)
    t = t - 1.2 * groove - 1.2 * core + 0.8 * (lip & ~groove)
    # the plates between the furrows vary a little in tone (weathered and fresh bark), long and thin
    pn = ndi.gaussian_filter(rng.random((Hh, W)), (0.5 * s, 2.2 * s))
    pn = (pn - pn.mean()) / max(1e-6, pn.std())
    t = t + 0.55 * np.clip(pn, -1.5, 1.5) * ~groove
    # in the core shadow the furrows read as dark seams between the plates
    seam = (np.round(Y + 0.6 * np.sin(X / (2.3 * s))) % 3 == 0) & (np.sin(X / (1.7 * s) + Y) > -0.6)
    t = np.where((t < 1.6) & seam & (yn < 0.9), 0, t)
    # a knot (a ring with a dark heart) and a branch stub with a pale cut end
    kx, ky = x0 + 0.62 * Lw, cy + 0.25 * R
    kd = np.hypot((X - kx) / (1.6 * s), (Y - ky) / (1.15 * s))
    t = np.where(body & (kd < 1.0), np.where(kd < 0.45, 0.5, np.where(kd < 0.75, 3.6, 1.6)), t)
    ts = np.clip(np.round(t), 0, 5).astype(int)
    F.put(body, _bark_fam(ts), ts, z=1)
    # a broken branch stub rising from the top: a short cylinder lit on its left, its torn end pale
    sx_, sw_, sh_ = x0 + 0.37 * Lw, 1.3 * s, 3.2 * s
    sbase = cy - 0.72 * R
    us = (X - sx_) / sw_
    stub = (np.abs(us) <= 1) & (Y <= sbase) & (Y >= sbase - sh_)
    tsb = np.clip(np.round(2.6 + 2.4 * _lambert(us, np.sqrt(np.clip(1 - us * us, 0, 1)), 0.1)), 1, 5).astype(int)
    F.put(stub, _bark_fam(tsb), tsb, z=2)
    sc = ((X - sx_) / sw_) ** 2 + ((Y - (sbase - sh_)) / (0.6 * s)) ** 2 <= 1
    F.put(sc, 'plaster_warm', np.where(X < sx_, 4, 3), z=2.2)
    F.step(body & (np.abs(X - sx_ - 0.6 * s) < 1.4 * s) & (Y > sbase) & (Y < sbase + 1.0 * s) & (F.z < 2), -1)
    # the sawn end facing west: lit, rings round a dark heart, checks, sapwood, the bark rim
    ex, erx = x0, 0.42 * R
    eu, ev = (X - ex) / erx, (Y - cy) / R
    er = np.sqrt(eu * eu + ev * ev)
    endm = er <= 1.0
    eth = np.arctan2(ev, eu)
    erw = er * (1 + 0.04 * np.sin(3 * eth + 0.4))
    # the face a tone lighter than the bark, lit to the upper left; three rings, a dark heart and
    # one check crack (#288 review S1)
    te = np.full(endm.shape, 4.0) - 0.8 * np.clip(ev, 0, 1) + 0.5 * np.clip(-ev - 0.3, 0, 1)
    for rk in (0.3, 0.55, 0.76):
        te = te - 1.0 * (np.abs(erw - rk) < 0.06 + 0.7 / R)
    te = np.where(erw < 0.13, 2.0, te)
    te = np.where((erw > 0.84) & (erw <= 0.88), 5.0, te)
    te = te - 1.6 * ((np.abs(np.angle(np.exp(1j * (eth - 0.7)))) < 0.08 + 0.6 / (er * R + 1)) & (erw > 0.15) & (erw < 0.82))
    tend = np.clip(np.round(te), 1, 5).astype(int)
    F.put(endm & (erw <= 0.88), np.where(tend >= 5, 'plaster', np.where(tend <= 2, 'plaster_cool', 'plaster_warm')), tend, z=3)
    rimt = np.where(ev < -0.2, 4, np.where(ev < 0.5, 3, 2))
    F.put(endm & (erw > 0.88), _bark_fam(rimt), rimt, z=3)
    # the broken east end: each splinter's pale wood in shade, its upper facet lit, its lower side
    # dark, a dark hollow at the root of the break
    # the splinters keep their bark on the outside; the torn wood shows only on the break face, a
    # strip just inside each splinter's edge (lit on its upper facet, shaded on its lower), and
    # where two splinters part the break goes dark into a hollow
    rx_ = x1 - 2.4 * s + root[bi]                                       # this splinter's root
    face_w = (0.7 + 0.6 * (1 - tip)) * s
    spl = body & (X > jag - face_w) & (X > rx_ - 0.6 * s) & (F.z <= 1)
    tsp = np.where(upper, 3, 2)
    tsp = np.where(X >= jag - 0.9, tsp - 1, tsp)                         # the torn tip edge
    tsp = np.where((tip < 0.3) & (X < rx_ + 1.2 * s), 0, tsp)          # the hollow where splinters part
    F.put(spl, np.where(tsp >= 3, 'plaster_warm', 'plaster'), tsp, z=1.2)
    # moss: one mantle along the top, uneven in width, draping over the near flank in two or
    # three rounded lobes; leaf clusters lit on top, a dark tuck where it overhangs (no stems)
    th_ = (0.9 + 0.8 * np.sin(X / (5.3 * s) + rng.uniform(0, 6)) + 0.5 * np.sin(X / (2.1 * s) + rng.uniform(0, 6))) * s
    xa_, xb_ = x0 + 0.12 * Lw, x0 + 0.9 * Lw
    edge_ = np.clip(np.minimum(X - xa_, xb_ - X) / (2.5 * s), 0, 1)
    hump = (0.5 + 0.45 * np.sin(X / (1.7 * s) + rng.uniform(0, 6)) + 0.3 * np.sin(X / (0.9 * s))) * s   # a cushioned top
    mant = (Y >= cy - R - hump * edge_) & (Y <= cy - R + 0.6 * s + th_ * edge_) & (X >= xa_) & (X <= xb_) & (edge_ > 0)
    for _ in range(int(rng.integers(2, 4))):
        dxp = rng.uniform(xa_ + 2 * s, xb_ - 2 * s)
        mant |= (((X - dxp) / (1.6 * s)) ** 2 + ((Y - (cy - R + 1.8 * s)) / (2.2 * s)) ** 2 <= 1) & (Y >= cy - R)
    mant = ndi.binary_opening(mant, iterations=1)
    dmy = np.zeros_like(mant)
    dmy[1:] = mant[:-1]
    top_ = mant & ~np.roll(mant, 2, axis=0)
    low_ = mant & ~np.roll(mant, -2, axis=0)
    q = max(2, int(round(0.9 * s)))
    cn = ndi.gaussian_filter(rng.random(mant.shape), 0.8 * s)
    clump = cn > np.percentile(cn, 70)                                    # leaf clusters, not a grid
    tm = np.where(top_, 4, np.where(low_, 2, 3)) + (clump & ~low_ & ~top_)
    tm = np.where(X > x0 + 0.8 * Lw, tm - 1, tm)
    F.put(mant, np.where(tm >= 4, 'leaf_warm', 'leaf'), tm, z=3.5)
    tuck = ndi.binary_dilation(mant, iterations=1) & ~mant & (Y > cy - R) & body
    F.step(tuck & (F.z < 3.5), -2, lo=0)
    # a bracket fungus in two shelves on the shaded flank: each a half disc standing out from the
    # bark, its top lit with growth bands, a dark rim of thickness under it and its shade below
    for (fx, fy, fw) in ((x0 + 0.22 * Lw, cy + 0.42 * R, 2.6 * s), (x0 + 0.22 * Lw + 2.4 * s, cy + 0.68 * R, 2.0 * s)):
        e = ((X - fx) / fw) ** 2 + ((Y - fy) / (1.1 * s)) ** 2
        sh = (e <= 1) & (Y >= fy - 0.2 * s)
        band = np.where(e > 0.55, 3, 4) - (X > fx + 0.45 * fw)
        F.put(sh, np.where(band >= 4, 'plaster_warm', 'plaster'), band, z=4)
        rim = ndi.binary_dilation(sh, iterations=1) & ~sh & (Y > fy + 0.5 * s)
        F.put(rim, 'clay' if 'clay' in pk.RAMPS else 'plaster_cool', 1, z=4)
        shade = ndi.binary_dilation(sh, iterations=int(round(1.1 * s))) & ~sh & ~rim & (Y > fy + 0.9 * s) & body
        F.step(shade & (F.z < 4), -1)
    F.tidy(2)
    return _finish(F.image())
