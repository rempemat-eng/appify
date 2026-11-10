"""Cairn: the moss-covered stone golem (pass 2: rounder, after Codex's design).  Built from
rounded, weathered granite boulders with dark joint gaps: two great round shoulder boulders,
a deep chest boulder over a belly stone, big round fists that hang to the knees, thick stubby
legs on flat stone feet, and a small recessed wedge head set low between the shoulders with
amber eye slits.  Turf caps the shoulders, chest and head; a sprout grows on the LEFT
shoulder; two pebbles float over the RIGHT shoulder.  About 90 px tall, 78 wide: the biggest.

Pose-driven like bramble.py (parts.Rig).  Pose: bob, crouch, lean, footR/L, handR/L (fist
centres), pebbles (phase).  Tags: fist (the two fists), pebbles."""
import math
import numpy as np
from ew import Fig
from parts import Rig, FLIP
import palette  # noqa: F401
import anim

ID = 'cairn'
NAME = 'Cairn'
SCALE = 1.063                   # 26 Oct scale audit: Cairn is 1.2x the hero (about 89 px of body, 83 to 95);
                                # 25 Oct's 1.2 x the old 87 px rig measured 101 (1.36x).  Proportions unchanged
HEIGHT = 89
BAND = (86, 104)                # at SCALE 1.063 (26 Oct); the turned drawings show the floating pebbles higher
SHW = 20.5                      # 25 Oct (Matt): shoulders a touch narrower
# 27 Oct (Matt 11:03, "his arms seem to have unequal length"): the rest hands hang the same distance
# from their shoulders (the right one a step ahead, as the shoulders turn), so both arms read the
# same length in S and N; ARM holds the one set of segment lengths both arms use (checks.arm_symmetry)
REST_R = (10.0, 22.0, 25.0)
REST_L = (6.0, 22.0, -25.0)
ARM = dict(upper=19.0, fore=18.5, socket=4.0)
# 27 Oct (Matt 09:23, "a bit less hunched and a touch more upright, not completely"): the torso
# leans forward about half as far, the shoulder line sits higher, the head rides on top of the
# chest instead of in front of it, and the back boulder sits under the shoulders, not over them
UPRIGHT = dict(lean=2.25, sh_up=1.5, head_up=4.5, side_head=6.0, q_head=7.0, chest_fwd=4.5, back=(-9.0, -11.0))
# 27 Oct (Matt 11:03, "his chest stone is too wide, chest to back"): the torso is about 21 % shallower
# front to back (the chest stone 21 -> 16.5 deep in profile, the belly 16 -> 13, the pelvis 13.5 -> 12, the
# back boulder 15 -> 12 and 4 px further in; in the three-quarter turns the chest's projected width
# 21 -> 18.9, which is the same depth seen at 45 degrees); the width across the shoulders and the heights stay.  The shoulder sockets
# sit 2 px further forward and the shoulders turn less (P0 turn 2), so they stay over the chest.
# 27 Oct (Matt 11:05, golem proportions, "similar to the clash of clans golem", proportions and
# construction only): top-heavy, short stumpy legs set apart.  The hips sit 3 px lower (HIP 25 -> 22),
# the thigh and foot stones are squatter, the stance 1 px narrower (shoulders 1.6 x the hips' span
# across the thighs), and the rest hands come down with them so the hands still hang to the knee.
LEGS = dict(hip=22.0, thigh_ry=8.6, foot_ry=6.2, foot_y=5.0, stance=9.5)
DEPTH = dict(chest=16.5, chest_q=18.9, belly=13.0, pelvis=12.0, back=12.0, back_q=15.0, socket=-4.0)
HAND_K = 1.4                    # golem hands (26 Oct): about 30 % smaller than the old round fists


def P0(**k):
    p = dict(bob=0, breath=0, lean=4.5, crouch=0.0, hipx=0.0, turn=2.0,
             footR=(1.0, 0.0), footL=(-1.0, 0.0), stance=LEGS['stance'],
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             pebbles=0.0, lag=0.0, blink=False, fx=None,
             rock=None, growth=0.0, chips=None, crack=0.0, gripR=0.15, gripL=0.15)
    p.update(k)
    return p


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def boulder(f, x, y, rx, ry, z, ang=0.0, dim=0, cracks=(), cast=(1, 2, 1), tag=None, flat_bottom=None):
    """A weathered granite boulder: rounded mass, upper-left light, a lower-right shadow, a
    deep crevice tone where it is darkest, optional crack strokes (angles in radians from its
    centre, as (a0, r0, a1, r1) in units of the radii)."""
    m = f.rell(x, y, rx, ry, ang)
    if flat_bottom is not None:
        m &= f.Y < flat_bottom

    def tm(X, Y, t):
        out = t.copy()
        for (a0, r0, a1, r1) in cracks:
            x0, y0 = x + math.cos(a0) * rx * r0, y + math.sin(a0) * ry * r0
            x1, y1 = x + math.cos(a1) * rx * r1, y + math.sin(a1) * ry * r1
            d = np.abs((X - x0) * (y1 - y0) - (Y - y0) * (x1 - x0)) / max(1e-6, math.hypot(x1 - x0, y1 - y0))
            tt = ((X - x0) * (x1 - x0) + (Y - y0) * (y1 - y0)) / max(1e-6, (x1 - x0) ** 2 + (y1 - y0) ** 2)
            out[(d < 0.55) & (tt >= 0) & (tt <= 1)] = 0
        return out
    return f.add(m, 'granite', z=z, rl=2.4, rs=4.4, ts=0.36, vgrad=0.25, line='hard', cast=cast,
                 tonemap=tm if cracks else None, deep=True, dim=dim, tag=tag)


def moss_cap(f, x, y, rx, ry, cut, z, drips=(), dim=0, ang=0.0):
    """Turf over the top of a mass: the boulder's ellipse above the line y < cut, plus drips."""
    m = f.rell(x, y, rx + 0.6, ry + 0.6, ang) & (f.Y < cut)
    for (dx, dy, r) in drips:
        m |= f.ell(x + dx, cut + dy, r, r * 1.25) & f.rell(x, y, rx + 0.6, ry + 0.6, ang)
    f.add(m, 'moss', z=z, rl=1.8, rs=2.2, ts=0.3, line='shade', dim=dim, cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _tufts(X, Y, t), deep=bool(dim))   # 27 Oct: deep when dimmed, so the far cap's tufts (one step down) survive the dim


def _tufts(X, Y, t):
    out = t.copy()
    m = ((np.floor(X) % 5 <= 1) & (np.floor(Y) % 3 == 1)) & (t == 2)       # 2 px tuft strokes, never a lone pixel
    out[m] = 1
    return out


def sprout(f, x, y, z):
    f.add(f.cap(x, y, x - 0.5, y - 5, 0.8), 'moss', z=z, flat=2, line='hard')
    f.add(f.ell(x - 3.0, y - 6, 2.8, 1.5), 'leafg', z=z + 0.1, rl=1, rs=1, line='hard')
    f.add(f.ell(x + 2.4, y - 7.2, 2.6, 1.4), 'leafg', z=z + 0.1, rl=1, rs=1, line='hard')


def splints(f, a, b, z, g, dim=0, w=5.5, two=True):
    """Old Growth: two living wooden splints braced along a limb from a to b (screen points),
    bound by a root band, grown to fraction g of their length."""
    if g <= 0.02:
        return
    ax, ay = a
    bx, by = b
    L = math.hypot(bx - ax, by - ay) or 1.0
    ux, uy = (bx - ax) / L, (by - ay) / L
    px, py = -uy, ux
    ex, ey = ax + (bx - ax) * g, ay + (by - ay) * g
    with f.tagging('growth'):
        for k in ((-1, 1) if two else (-1,)):
            f.add(f.cap(ax + px * w * k, ay + py * w * k, ex + px * w * k, ey + py * w * k, 1.2), 'leather', z=z, rl=1, rs=1.2, dim=dim, line='hard')
        if g > 0.5:
            mx, my = ax + (bx - ax) * 0.55, ay + (by - ay) * 0.55
            band = f.cap(mx - px * (w + 1), my - py * (w + 1), mx + px * (w + 1), my + py * (w + 1), 1.0)
            f.add(band, 'leather', z=z + 0.05, rl=1, rs=1, dim=dim, line='hard')
            f.add(f.ell(mx + px * (w + 1.5), my + py * (w + 1.5) - 1.5, 2.2, 1.3), 'leafg', z=z + 0.1, rl=1, rs=1, dim=dim, line='hard')


def _slab_facets(X, Y, t, x, y):
    """26 Oct (asset gate): the torn slab in flat facets - a lit top plane, the face, a shaded
    underside and right flank - with two strata lines across its face."""
    out = t.copy()
    body = t >= 1
    out[body] = 2
    out[body & (Y < y - 5.0)] = 3
    out[body & ((Y > y + 1.5) | ((X - x) > 9.0))] = 1
    for yy, x0, x1 in ((y - 2.5, x - 11, x + 4), (y + 0.5, x - 6, x + 10)):
        out[body & (np.abs(Y - yy) < 0.5) & (X > x0) & (X < x1)] = 1
    return out


def held_rock(f, x, y, z):
    """The slab he tears from the ground and throws (one rock, carried between the fists): an
    angular, flat-topped slab wider than it is tall, a torn root-ball of earth underneath with
    hanging roots and crumbs, a moss patch on its top edge.  No crack across its face, so it never
    reads as a second head."""
    slab = f.poly([(x - 15, y - 1), (x - 11, y - 8.5), (x + 1, y - 9.5), (x + 12, y - 7.5), (x + 15.5, y + 0.5),
                   (x + 11, y + 6), (x - 9, y + 6.5)])
    f.add(slab, 'granite', z=z, rl=2.0, rs=3.0, ts=0.36, line='hard', deep=True, tag='rock', cast=(1, 2, 1),
          tonemap=lambda X, Y, t: _slab_facets(X, Y, t, x, y))
    f.add(f.poly([(x - 10, y - 8), (x + 1, y - 9.5), (x + 9, y - 8), (x + 2, y - 6.2), (x - 7, y - 6)]) & slab,
          'moss', z=z + 0.1, rl=1, rs=1, line=None, tag='rock')
    earth = f.ell(x - 1, y + 6, 11.0, 3.0) & (f.Y > y + 4.5)
    f.add(earth, 'leather', z=z + 0.05, rl=1, rs=1.4, line='hard', tag='rock')
    for dx, L in ((-4, 4), (1, 6), (5, 3)):
        f.detail(f.seg(x + dx, y + 7, x + dx + 1, y + 7 + L), ('leather', 1), tag='rock')
    for dx, dy in ((-8, 9), (3, 11), (8, 8)):
        f.dot(x + dx, y + dy, ('leather', 2), tag='rock')


def impact(f, x, y, ph, crack):
    """Slam contact: angular chips thrown up and a short fissure in the ground at (x, y)."""
    if crack > 0:
        pts = [(x - 14 * crack, y - 1), (x - 7 * crack, y - 2), (x - 2, y - 1), (x + 5 * crack, y - 2), (x + 13 * crack, y - 1)]
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            f.detail(f.seg(a, b, c, d), ('crack', 0), tag='impact')
    if ph is not None:
        for i, (dx, dy) in enumerate(((-9, -6), (8, -8), (-4, -12), (12, -3), (-13, -2))):
            t = 0.6 + 0.4 * ph
            cx, cy = x + dx * t, min(y - 2.5, y + dy * t + 3 * ph * ph)
            f.add(f.poly([(cx - 1.5, cy), (cx, cy - 1.5), (cx + 1.5, cy + 0.5), (cx, cy + 1.5)]), 'granite', z=61 + i * 0.01, rl=1, rs=1, line='hard', tag='impact')


def _block(f, c, u, p, a0, a1, b0, b1, z, dim, tag, ch=0.9, taper=1.0):
    """One big faceted stone of Cairn's hand (26 Oct: few, big, chunky blocks, the arms' value): a
    chamfered quad from a0 to a1 along u and b0 to b1 across p around c, narrowing to `taper` of its
    width at the a1 end (a wedge).  Facets only, no lines inside: the stone's face in the arms'
    mid tone, one step up on the edge facing the light (upper left, mirrored on the flipped grid),
    one to two steps down on the edges turned away; a dark joint round the block, so a line shows
    only where two blocks meet."""
    def pt(a, b):
        return (c[0] + u[0] * a + p[0] * b, c[1] + u[1] * a + p[1] * b)
    def w_at(a):
        t = (a - a0) / max(1e-6, a1 - a0)
        return 1.0 + (taper - 1.0) * t
    def q(a, b):                                                   # a point of the (tapered) quad
        return pt(a, b * w_at(a))
    poly = [q(a0 + ch, b0), q(a1 - ch, b0), q(a1, b0 + ch), q(a1, b1 - ch), q(a1 - ch, b1), q(a0 + ch, b1), q(a0, b1 - ch), q(a0, b0 + ch)]
    m = f.poly(poly)
    e = 0.8
    rim = f.poly([q(a0 + ch - e * 0.4, b0 - e), q(a1 - ch + e * 0.4, b0 - e), q(a1 + e, b0 + ch - e * 0.4), q(a1 + e, b1 - ch + e * 0.4),
                  q(a1 - ch + e * 0.4, b1 + e), q(a0 + ch - e * 0.4, b1 + e), q(a0 - e, b1 - ch + e * 0.4), q(a0 - e, b0 + ch - e * 0.4)])
    f.add(rim & ~m, 'granite', z=z - 0.004, flat=0, line=None, dim=0, tag=tag)
    base = 1 if dim else 2
    f.add(m, 'granite', z=z, flat=base, line=None, dim=0, tag=tag)
    L = (0.6, -0.8) if f.flip else (-0.6, -0.8)                 # the light, upper left on the screen, in drawing coordinates
    for (q0, q1, inward) in (((a0, b0), (a1, b0), (0, 1)), ((a1, b0), (a1, b1), (-1, 0)), ((a1, b1), (a0, b1), (0, -1)),
                             ((a0, b1), (a0, b0), (1, 0))):
        nx = -(u[0] * inward[0] + p[0] * inward[1])
        ny = -(u[1] * inward[0] + p[1] * inward[1])
        d = nx * L[0] + ny * L[1]
        if abs(d) < 0.35:
            continue
        bw = 1.0 if d > 0 else 2.2                                # a thin lit top facet, a broad shaded side facet
        band = f.poly([q(*q0), q(*q1), q(q1[0] + inward[0] * bw, q1[1] + inward[1] * bw), q(q0[0] + inward[0] * bw, q0[1] + inward[1] * bw)])
        tone = min(base + 1, 3) if d > 0 else max(base - 1, 0)
        f.add(band & m, 'granite', z=z + 0.01, flat=tone, line=None, dim=0, tag=tag)
    return m


def golem_hand(f, R, hx, hy, ux, uy, z, dim, grip, inner, tag='fist'):
    """26 Oct (Matt's reference for the construction only: few, BIG, chunky blocks): Cairn's hand
    is five big faceted stones - a back-of-hand slab, three thick blunt finger wedges and a separate
    thumb wedge - in the same stone and value as his arms, a dark gap only between the blocks and a
    bit of moss in one joint.  The fist is four blocks bunched: the slab, two knuckle blocks and
    the thumb wedge across them.  (ux, uy): the forearm's screen direction; inner: the thumb's
    screen side.  Returns the striking point (the knuckles)."""
    k_ = HAND_K
    u = (ux, uy)
    p = (-uy, ux)
    g = max(0.0, min(1.0, grip))
    hx, hy = hx + ux * 0.5, hy + uy * 0.5
    _block(f, (hx, hy), u, p, -4.4 * k_, 3.8 * k_, -5.6 * k_, 5.6 * k_, z, dim, tag, ch=1.8)           # the back-of-hand slab
    root = (hx + ux * 3.2 * k_, hy + uy * 3.2 * k_)
    tips = []
    if g < 0.5:                                                   # open: three thick blunt wedges hang on
        for j, (off, L) in enumerate(((-3.7 * k_, 4.4 * k_), (0.0, 4.9 * k_), (3.7 * k_, 4.2 * k_))):
            bc = (root[0] + p[0] * off, root[1] + p[1] * off)
            _block(f, bc, u, p, 0.0, L, -2.0 * k_, 2.0 * k_, z + 0.3 + 0.02 * j, dim, tag, ch=1.1, taper=0.8)
            tips.append((bc[0] + u[0] * L, bc[1] + u[1] * L))
    else:                                                         # fist: two big knuckle blocks bunched forward
        for j, off in enumerate((-2.9 * k_, 2.9 * k_)):
            bc = (root[0] + p[0] * off, root[1] + p[1] * off)
            _block(f, bc, u, p, -1.0, 3.4 * k_, -2.9 * k_, 2.9 * k_, z + 0.3 + 0.02 * j, dim, tag, ch=1.4, taper=0.9)
            tips.append((bc[0] + u[0] * 3.4 * k_, bc[1] + u[1] * 3.4 * k_))
    f.add(f.ell(root[0] - u[0] * 0.6, root[1] - u[1] * 0.6, 1.8, 1.1), 'moss', z=z + 0.35, rl=1, rs=1, line=None, dim=dim, tag=tag)   # moss in the joint
    tb = (hx + p[0] * inner * 5.4 * k_, hy + p[1] * inner * 5.4 * k_)
    if g >= 0.5:
        tu = (p[0] * -inner * 0.75 + u[0] * 0.66, p[1] * -inner * 0.75 + u[1] * 0.66)
    else:
        tu = (u[0] * 0.9 + p[0] * inner * 0.44, u[1] * 0.9 + p[1] * inner * 0.44)
    n_ = math.hypot(*tu) or 1.0
    tu = (tu[0] / n_, tu[1] / n_)
    _block(f, tb, tu, (-tu[1], tu[0]), -0.6, 4.4 * k_, -2.0 * k_, 2.0 * k_, z + 0.5, dim, tag, ch=1.2, taper=0.75)   # the thumb wedge
    if g >= 0.5:
        return (root[0] + ux * 3.4 * k_, root[1] + uy * 3.4 * k_)
    return (sum(t[0] for t in tips) / 3, sum(t[1] for t in tips) / 3)


def eyes_slits(f, xs, y, blink=False, ws=None):
    for k, x in enumerate(xs):
        w = ws[k] if ws else 4
        if blink:
            f.detail(f.rect(x, y + 1, x + w, y + 2), ('amber', 0), tag='face')
        else:
            f.detail(f.rect(x, y, x + w, y + 2), ('amber', 2), tag='face')
            f.detail(f.rect(x, y, x + 2, y + 1), ('amber', 3), tag='face')


def _mark(f, name, i0):
    """Name the parts added since i0 (the proportion diagram and checks.arm_symmetry measure them)."""
    f.__dict__.setdefault('groups', {}).setdefault(name, []).extend(range(i0, len(f.parts)))


def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    b = P['bob']
    cr = P['crouch']
    U = UPRIGHT
    lean = P['lean'] - U['lean']
    hip3 = (P['hipx'], LEGS['hip'] - cr - b, 0.0)
    ch3 = (hip3[0] + lean * 0.6, hip3[1] + 22.0 + P['breath'], 0.0)        # chest centre
    sh3 = (hip3[0] + lean, hip3[1] + 35.0 + U['sh_up'] + P['breath'], 0.0)              # shoulder line
    off = (P['hipx'], -cr - b, 0.0)
    hR = add3(P['handR'] or REST_R, off)
    hL = add3(P['handL'] or REST_L, off)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    # ---------------------------------------- legs: thigh stone, foot stone
    st = P['stance']
    for lat, key in ((st, 'footR'), (-st, 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        far = R.far(lat)
        dim = 1 if far else 0
        z = R.zleg(foot3)
        hp3 = add3(hip3, (0, -2, lat * 0.8))
        kn = tuple(np.add(hp3, foot3) * 0.5 + np.array([1.5, 1.5, 0.0]))
        # a deep crouch with the lower hips (LEGS) would sink the thigh stone into the ground
        kn = (kn[0], max(kn[1], foot3[1] + LEGS['thigh_ry'] - 1.0), kn[2])
        kx, ky = R.p(kn)
        i0 = len(f.parts)
        boulder(f, kx, ky - 1, 10.0 if not side else 9.0, LEGS['thigh_ry'], z, dim=dim, cracks=((-2.2, 0.2, -1.4, 0.8),))
        fx, fy = R.p(foot3)
        if side:
            boulder(f, fx + 3.0, fy - LEGS['foot_y'], 11.5, LEGS['foot_ry'], z + 0.5, dim=dim, flat_bottom=fy, cast=None)
        else:
            boulder(f, fx, fy - LEGS['foot_y'], 10.4, LEGS['foot_ry'], z + 0.5, dim=dim, flat_bottom=fy, cast=None)
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
        _mark(f, 'leg_R' if lat > 0 else 'leg_L', i0)
        f.__dict__.setdefault('knee', {})['R' if lat > 0 else 'L'] = (kx, ky)
        splints(f, (fx, fy - 6), (kx, ky - 6), z + 0.6, P['growth'], dim=dim, w=7.0, two=False)
    # ---------------------------------------- pelvis, belly, chest
    hx, hy = R.p(hip3)
    cx, cy = R.p(ch3)
    sx, sy = R.p(sh3)
    sy0 = sy
    i0 = len(f.parts)
    if side:
        boulder(f, hx - 1, hy, DEPTH['pelvis'], 9.0, 12, cracks=((-0.5, 0.3, 0.6, 0.9),))
        boulder(f, cx + 4, cy + 7, DEPTH['belly'], 10.5, 15)
        i1 = len(f.parts)
        boulder(f, cx + U['chest_fwd'], cy - 4, DEPTH['chest'], 17.0, 16, ang=-0.3, cracks=((-2.5, 0.4, -1.8, 0.95), (0.4, 0.3, 1.0, 0.9)))
    else:
        boulder(f, hx, hy, 15.5, 9.0, 12, cracks=((-1.6, 0.2, -1.5, 0.9),))
        boulder(f, cx, cy + 7, 16.5, 10.5, 15, cracks=((0.3, 0.5, 0.9, 0.95),))
        i1 = len(f.parts)
        boulder(f, cx, cy - 4, DEPTH['chest_q'] if R.diag else 21.0, 16.0, 16, cracks=((-1.57, 0.95, -1.57, 0.3), (1.57, 0.3, 1.57, 0.95), (-2.7, 0.5, -2.2, 0.9)))
    _mark(f, 'torso', i0)
    _mark(f, 'chest', i1)
    # the great back boulder behind the shoulders (his hunched profile; the back from behind)
    bk3 = add3(sh3, (U['back'][0], U['back'][1], 0.0))
    bx_, by_ = R.p(bk3)
    front = facing in ('S', 'SE', 'SW')
    i0 = len(f.parts)
    if facing != 'S':
        zb = 19.0 if R.back else 11.0
        brx = DEPTH['back'] if side else (DEPTH['back_q'] if R.diag else 17.0)
        boulder(f, bx_, by_, brx, 13.5, zb, cracks=((-2.0, 0.3, -1.2, 0.9),))
        if not R.back:      # from behind the upright back shows bare stone under the head (no second moss cap below it)
            moss_cap(f, bx_, by_, brx, 13.5, by_ - 5, zb + 0.3, drips=((-6, 0.5, 2.0), (3, 1.2, 2.4)))
        else:
            moss_cap(f, bx_, by_, brx, 13.5, by_ - 9, zb + 0.3, drips=((-5, 0.6, 1.4),))
    _mark(f, 'back', i0)
    if front:
        moss_cap(f, cx, cy - 4, 21.0, 16.0, cy - 14, 17, drips=((-12, 0.5, 2.0), (-4, 1.5, 2.4), (6, 0.8, 2.0), (13, 0.2, 1.6)))
    # ---------------------------------------- head: a small wedge set low between the shoulders
    def head():
        i0 = len(f.parts)
        _head()
        _mark(f, 'head', i0)

    def _head():
        sy = sy0 - U['head_up']
        if facing == 'S':
            f.add(f.ell(sx, sy - 2, 9.0, 6.5), 'crack', z=17.5, flat=1, line='hard')            # socket
            hm = f.poly([(sx - 7, sy - 9), (sx + 7, sy - 9.5), (sx + 7.8, sy - 1), (sx + 4.5, sy + 4), (sx - 4.5, sy + 4), (sx - 7.8, sy - 1)])
            f.add(hm, 'granite', z=18, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 2), deep=True)
            moss_cap(f, sx, sy - 6, 7.4, 4.0, sy - 7.5, 18.5, drips=((-3, 0.4, 1.4), (3.5, 0.2, 1.2)))
            eyes_slits(f, (sx - 5.5, sx + 1.5), sy - 2, P['blink'])
        elif facing in ('SE', 'SW'):
            # v2 three-quarter: the wedge turned toward the facing, the far eye foreshortened
            hx_ = R.p(add3(sh3, (U['q_head'], 0.0, 0.0)))[0]
            hm = f.poly([(hx_ - 6.5, sy - 9), (hx_ + 6, sy - 9.5), (hx_ + 8, sy - 1.5), (hx_ + 5, sy + 4), (hx_ - 4, sy + 4.5), (hx_ - 7, sy - 0.5)])
            f.add(hm, 'granite', z=18, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 2), deep=True)
            moss_cap(f, hx_ + 0.5, sy - 6, 7.2, 4.0, sy - 7.5, 18.5, drips=((-3, 0.4, 1.4), (3.5, 0.2, 1.2)))
            eyes_slits(f, (hx_ - 4.0, hx_ + 2.5), sy - 2, P['blink'], ws=(4, 3))
        elif R.back:
            hx_ = R.p(add3(sh3, (6.0, 0.0, 0.0)))[0] if facing != 'N' else sx
            f.add(f.ell(hx_, sy - 5, 7.5, 5.5), 'granite', z=17.5, rl=1.6, rs=2.6, line='hard')
            moss_cap(f, hx_, sy - 5, 7.5, 5.5, sy - 4, 18.0, drips=((-3, 0.5, 1.4), (3, 0.5, 1.4)))
        else:
            hx_ = sx + U['side_head']
            hm = f.poly([(hx_ - 6, sy - 8.5), (hx_ + 4, sy - 8), (hx_ + 9, sy - 2), (hx_ + 8, sy + 4), (hx_ - 1, sy + 5), (hx_ - 6, sy + 1)])
            f.add(hm, 'granite', z=18, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 2), deep=True)
            moss_cap(f, hx_ + 1, sy - 5, 7.0, 4.0, sy - 6.5, 18.5, drips=((-2, 0.4, 1.4),))
            eyes_slits(f, (hx_ + 3.5,), sy - 2, P['blink'])
    if R.back:
        head()
    # ---------------------------------------- arms: shoulder boulder, upper arm stone, fist
    arms = []
    for key, hh, lat in (('R', hR, 1), ('L', hL, -1)):
        far = R.far(lat)
        shp = add3(sh3, (DEPTH['socket'] + P['turn'] * lat, 0.0, SHW * lat))
        z = P['z' + key] if P['z' + key] is not None else (R.zarm(hh, near=22, far=5) if (side or R.diag) else 22)
        arms.append((key, shp, hh, lat, far, z))
    for key, shp, hh, lat, far, z in arms:
        dim = 1 if far else 0
        pole = P['pole' + key] or (-1.0, 0.0, 0.5 * lat)
        sock3 = add3(shp, (0, -ARM['socket'], 0))
        up, lo, el3 = R.limb(sock3, hh, ARM['upper'], ARM['fore'], 1, 1, 1, pole)
        i0 = len(f.parts)
        (ax, ay), (ex, ey), (fx, fy) = R.p(shp), R.p(el3), R.p(hh)
        # for checks.arm_symmetry: the rig points (body space) and the drawn ones of this arm
        f.__dict__.setdefault('arms', {})[key] = dict(rig=(sock3, el3, hh), px=(R.p(sock3), (ex, ey), (fx, fy)), hand=HAND_K)
        mx, my = (ax + ex) / 2, (ay + ey) / 2 + 2
        boulder(f, mx, my, 9.8, 10.6, z, ang=math.atan2(ey - ay, ex - ax), dim=dim)
        lx, ly = (ex + fx) / 2, (ey + fy) / 2
        boulder(f, lx, ly, 8.8, 9.4, z + 0.5, dim=dim)
        L_ = math.hypot(fx - ex, fy - ey) or 1.0
        ux, uy = (fx - ex) / L_, (fy - ey) / L_
        inner = (-1.0 if lat > 0 else 1.0) * (1 if facing in ('S', 'SE', 'SW') else -1) if not side else -1.0
        _mark(f, 'arm_' + key, i0)
        i0 = len(f.parts)
        strike = golem_hand(f, R, fx, fy, ux, uy, z + 1.0, dim, P['grip' + key], inner)
        f.anchor('fist_R' if lat > 0 else 'fist_L', *strike)
        _mark(f, 'hand_' + key, i0)
        splints(f, (fx, fy), (ex, ey), z + 1.1, P['growth'], dim=dim, w=6.5)
        # the shoulder boulder sits over the top of the arm
        szo = z + 2 if (not side or not far) else z + 2
        sr = 12.0 if not far else 11.0
        i0 = len(f.parts)
        boulder(f, ax, ay, sr, 11.2, szo, dim=dim, cracks=((2.4, 0.4, 2.0, 0.95),))
        moss_cap(f, ax, ay, sr, 11.2, ay - 2 + (2 if facing == 'N' else 0), szo + 0.3, dim=dim,
                 drips=((-7, 0.5, 2.2), (-1, 1.8, 2.6), (6, 0.8, 2.0)))
        _mark(f, 'shoulder_' + key, i0)
        if lat < 0:
            spx, spy = R.p(add3(shp, (-4.0, 0.0, -3.0)))
            sprout(f, spx, ay - 12, szo + 0.5)
        else:
            ph = P['pebbles']
            for i, (dx, dy, r) in enumerate(((-6, -19, 1.9), (3, -23, 1.5))):
                yy = ay + dy + round(math.sin(ph * 2 * math.pi + i * 2.1) * 1.0)
                f.add(f.ell(ax + dx, yy, r + 0.6, r), 'granite', z=60, rl=1, rs=1.4, line='hard', tag='pebbles')
    if not R.back:
        head()
    if P['rock'] is not None:
        r3 = add3(add3(P['rock'], (0.0, 9.0, 0.0)), off)        # resting on top of the fists
        rx, ry = R.p(r3)
        d = R.d(r3)
        held_rock(f, rx, ry, 50.0 if d > -8 else 4.0)    # between the fists, over the arms
        f.anchor('rock', rx, ry)
    if P['chips'] is not None or P['crack'] > 0:
        cx_, cy_ = R.p((P['hipx'] + 10.0, 0.0, 0.0))
        impact(f, cx_, cy_, P['chips'], P['crack'])
    if P['growth'] > 0.5:                      # leaves bud from the shoulder turf
        for lat in (1, -1):
            x, y = R.p(add3(sh3, (DEPTH['socket'] + P['turn'] * lat, 9.0, SHW * lat)))
            for k, (dx, dy) in enumerate(((-6, 1), (5, -1), (0, -3))):
                f.add(f.ell(x + dx, y + dy, 2.4, 1.4), 'leafg', z=40 + k * 0.01, rl=1, rs=1, line='hard', tag='growth',
                      dim=1 if R.far(lat) else 0)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in FLIP), scale=SCALE)
    f.despeckle = True              # merge lone rim and shade pixels on the boulder edges (ew.despeckle)
    build(f, facing, P)
    return f
