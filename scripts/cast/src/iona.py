"""Iona: adult storm-lancer.  Dark violet hair with side-swept bangs, tied in one long braid
down her back; a magenta scarf wound at the neck with one tail; a berry-red split traveller's
coat (fitted bodice, knee-length skirt split at the front and the back vent) over taupe side
panels and sleeves; a brown carrying harness (a strap from the RIGHT shoulder to the LEFT hip,
crossing a second strap on the back, with a gold ring at the crossing); brown belt with a gold
buckle, violet trousers, brown boots.  About 75 px tall.

The spear is ONE continuous shaft, 92 px: steel leaf blade, gold collar, gold-banded brass
shaft, steel butt spike.  It is held in the RIGHT hand; for two-handed actions the LEFT hand
grips the same shaft further along it (pose field gripL), so both grips sit on the one line
and the spear keeps its length and head in every drawing.

Pass 2: pose-driven on parts.Rig like bramble.py (the same pose renders S, N, E and W).
Pose fields beyond the common ones: spu (butt -> tip direction, body space), sps (distance of
the right grip from the butt), gripL (distance of the left grip from the butt, or None for a
free left hand), storm (0..1 charge: a storm-blue rim on the blade and sparks), arc (lightning
drawing index or None), wind (scarf and braid streaming, px).
Equipment tags: spear, harness, braid."""
import math
import numpy as np
from ew import Fig
from parts import eye, boot_side, EYE, Rig
import palette  # noqa: F401
import anim
import surf
import turn

ID = 'iona'
NAME = 'Iona'
HEIGHT = 75
BAND = (88, 104)                 # idle height: the upright spear (92 px) is the top; 3 px higher in the NW turn drawing
SHW = 11.0
SPEAR = 92.0
REST_R = (3.0, 28.5, 13.5)       # right hand on the upright spear (the shaft passes the
                                 # head between ear and eye in E, over the cheek)
REST_L = (1.5, 27.0, -13.0)


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, twist=0.0,
             footR=(1.5, 0.0), footL=(-1.5, 0.0), stance=4.6,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             spu=(0.02, 1.0, 0.0), sps=None, lift=1.0, gripL=None,
             storm=0.0, arc=None, wind=0.0, lag=0.0, blink=False, face=None, brow=0, fx=None)
    p.update(k)
    return p


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def nrm(v):
    v = np.array(v, float)
    return v / (np.linalg.norm(v) or 1.0)


# ------------------------------------------------------------------------------------ spear
def spear(f, R, butt3, u3, P, zf):
    """The one spear from the butt along u3.  zf(p3) gives the depth for each third of the
    shaft, so a shaft passing behind the body is hidden there and shows in front elsewhere.
    Returns the blade tip (pivot space)."""
    u3 = nrm(u3)
    b3 = np.array(butt3, float)

    def at(s):
        return R.p(tuple(b3 + u3 * s))
    L = SPEAR
    cuts = [3.0, 30.0, 58.0, L - 10.5]
    tip = at(L)
    with f.tagging('spear'):
        for s0, s1 in zip(cuts[:-1], cuts[1:]):
            (x0, y0), (x1, y1) = at(s0), at(s1)
            z = zf(tuple(b3 + u3 * (s0 + s1) / 2))
            f.add(f.cap(x0, y0, x1, y1, 1.2), 'brass', z=z, rl=1.0, rs=1.3, line='hard')
            for s in np.arange(s0 + 9, s1 - 2, 14.0):          # gold bands
                (bx, by), (cx, cy) = at(s), at(s + 1.0)
                Lb = math.hypot(cx - bx, cy - by)
                if Lb > 0.5:
                    qx, qy = -(cy - by) / Lb, (cx - bx) / Lb
                    f.detail(f.seg(bx - qx, by - qy, bx + qx, by + qy), ('brass', 1), z=z + 0.02)
        zt = zf(tuple(b3 + u3 * (L - 5)))
        zb = zf(tuple(b3 + u3 * 2))
        # leaf blade with a gold collar
        (cx, cy), (wx, wy) = at(L - 10.5), at(L - 5.0)
        dx, dy = tip[0] - cx, tip[1] - cy
        Lp = math.hypot(dx, dy)
        if Lp > 3.0:
            ux, uy = dx / Lp, dy / Lp
            px, py = -uy, ux
            k = min(1.0, Lp / 10.5)
            w = 2.6
            blade = f.poly([(cx + ux * 1.5, cy + uy * 1.5), (wx + px * w, wy + py * w), (tip[0] + ux * 0.6, tip[1] + uy * 0.6),
                            (wx - px * w, wy - py * w)])
            f.add(blade, 'steel', z=zt + 0.1, rl=1.2, rs=1.4, line='hard')
            f.detail(f.seg(cx + ux * 3, cy + uy * 3, tip[0] - ux * 2.5 * k, tip[1] - uy * 2.5 * k), ('steel', 1), z=zt + 0.15)
            f.add(f.cap(cx - ux * 0.5, cy - uy * 0.5, cx + ux * 1.5, cy + uy * 1.5, 1.9), 'gold', z=zt + 0.2, rl=1, rs=1, line='hard')
        else:                                                   # pointing at the camera or away
            f.add(f.ell(tip[0], tip[1], 2.6, 2.6), 'steel', z=zt + 0.1, rl=1, rs=1.2, line='hard')
            f.add(f.ell(cx, cy, 1.8, 1.8), 'gold', z=zt + 0.2, rl=1, rs=1, line='hard')
            ux, uy = 0.0, 1.0
        # butt spike
        (ax, ay), (ex, ey) = at(0.0), at(4.0)
        f.add(f.cap(ax, ay, ex, ey, 0.7, 1.4), 'steel', z=zb + 0.05, rl=1, rs=1, line='hard')
    if P['storm'] > 0.05:
        storm_blade(f, R, b3, u3, P, zt)
    return tip


def storm_blade(f, R, b3, u3, P, z):
    """Storm charge: a blue rim round the blade and sparks along the head (finite pixels)."""
    st = P['storm']
    tip = R.p(tuple(b3 + u3 * SPEAR))
    c = R.p(tuple(b3 + u3 * (SPEAR - 6)))
    ring = f.ell(c[0], c[1], 5.5 + st, 5.5 + st) | f.ell(tip[0], tip[1], 3.5, 3.5)
    ring &= ~(f.ell(c[0], c[1], 3.6, 3.6) | f.ell(tip[0], tip[1], 1.8, 1.8))
    ph = int(P.get('fx') or 0)
    rnd = np.random.RandomState(7 + ph)
    keep = rnd.rand(*ring.shape) < 0.25 + 0.25 * st
    f.detail(ring & keep, ('storm', 2), z=z + 0.3, tag='storm')
    for i in range(int(2 + 3 * st)):
        s = SPEAR - 14 - 9 * i - (ph % 3) * 2
        x, y = R.p(tuple(b3 + u3 * s))
        sx = 2 if (i + ph) % 2 else -2
        f.detail(f.seg(x, y, x + sx, y - 2), ('storm', 3), z=z + 0.3, tag='storm')
    f.dot(tip[0], tip[1], ('storm', 4), z=z + 0.4, tag='storm')


def bolt(f, x0, y0, x1, y1, seed, z=60):
    """A jagged lightning stroke between two pivot points (3 to 5 bends)."""
    rnd = np.random.RandomState(seed)
    n = 5
    pts = [(x0, y0)]
    for i in range(1, n):
        t = i / n
        pts.append((x0 + (x1 - x0) * t + rnd.uniform(-3, 3), y0 + (y1 - y0) * t + rnd.uniform(-3, 3)))
    pts.append((x1, y1))
    pts = [(max(-74.0, min(74.0, x)), y) for x, y in pts]          # stay inside the cell
    for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
        f.detail(f.seg(a, b, c, d), ('storm', 3), z=z, tag='storm')
    f.detail(f.pixels([pts[2]]), ('storm', 4), z=z, tag='storm')


# ------------------------------------------------------------------------------------ hair
def braid3(f, R, nape3, lag, wind, z, dim=0):
    """The one braid from the nape down her back to the hips, swinging with lag."""
    m = None
    pts = []
    n = 9
    for i in range(n):
        t = i / (n - 1)
        p3 = add3(nape3, (-1.5 - 2.5 * t - (lag + wind) * t ** 1.4, -4.0 * i, -2.0 * t))
        x, y = R.p(p3)
        x += 0.9 if i % 2 else -0.9
        pts.append((x, y))
        e = f.ell(x, y, 3.0 - i * 0.12, 2.6)
        f.add(e, 'braid', z=z + i * 0.01, rl=1.2, rs=1.6, line='shade' if i else 'hard', dim=dim, cast=(0, 1, 1), tag='braid')
    xe, ye = pts[-1]
    f.add(f.rect(xe - 1.6, ye + 2, xe + 1.6, ye + 4), 'gold', z=z + 0.5, rl=1, rs=1, line='hard', tag='braid')
    f.add(f.poly([(xe - 2.2, ye + 4), (xe + 2.2, ye + 4), (xe + 1.2, ye + 9), (xe - 1.4, ye + 8)]), 'braid', z=z + 0.4,
          rl=1, rs=1.5, line='hard', dim=dim, tag='braid')


def hair_front(f, x0, hy, side=0):
    """Hair cap with side-swept bangs and a sheen arc.  side: 0 front, 1 profile."""
    if side == 0:
        cap = f.ell(x0, hy - 3.0, 9.8, 8.6) | f.ell(x0 - 8.8, hy + 3.0, 2.5, 7.0) | f.ell(x0 + 8.8, hy + 3.0, 2.5, 7.0)
        cap &= ~(f.ell(x0, hy + 2.5, 7.3, 6.5) & (f.Y > hy - 1.5))
        bangs = f.poly([(x0 - 8.5, hy - 6), (x0 - 7.5, hy + 1.5), (x0 - 5, hy - 2.5), (x0 - 2.5, hy + 0.5), (x0 + 0.5, hy - 3),
                        (x0 + 3, hy - 0.5), (x0 + 5.5, hy - 3.5), (x0 + 8.0, hy - 1.5), (x0 + 8.5, hy - 7)])
    else:
        cap = f.ell(x0 - 0.5, hy - 3.0, 9.2, 8.6) | f.ell(x0 - 6.5, hy + 2, 3.6, 6.4)
        cap &= ~(f.ell(x0 + 4.8, hy + 2.8, 6.0, 6.4) & (f.Y > hy - 2.0))
        bangs = f.poly([(x0 + 0.5, hy - 7), (x0 + 2.0, hy - 1), (x0 + 4.0, hy - 3.5), (x0 + 6.0, hy + 0.5), (x0 + 8.0, hy - 3.5),
                        (x0 + 8.8, hy - 7)])
    f.add(cap | bangs, 'braid', z=44, rl=1.8, rs=2.6, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _sheen(X, Y, t, x0, hy, side))


def _sheen(X, Y, t, x0, hy, side):
    out = t.copy()
    out[(Y > hy + 1.5) & (t >= 1)] = np.minimum(out[(Y > hy + 1.5) & (t >= 1)], 1)     # v2: the lower hair turns into shade
    cx = x0 + (-1.5 if side == 0 else -2.0)
    r = ((X - cx) / 7.0) ** 2 + ((Y - hy + 2.0) / 6.4) ** 2
    m = (r > 1.0) & (r < 1.38) & (Y < hy - 6.0) & (X < cx + 5.5)
    out[m & (t == 2)] = 3
    return out


def _eyes(f, P, xs, ey):
    for x in xs:
        if P['face'] == 'shut':
            f.detail(f.rect(x - 0.5, ey + 2, x + 2.5, ey + 3), EYE)
        elif P['blink']:
            f.detail(f.rect(x, ey + 3, x + 2, ey + 4), EYE)
        else:
            eye(f, x, ey, 4)
        lift = {1: 1, 2: -1}.get(P['brow'], 0)
        if P['brow']:
            f.detail(f.rect(x - 0.5, ey - 1 + lift, x + 2.5, ey + lift), ('braid', 1))


def head_south(f, P, x0, hy):
    f.add(f.ell(x0 - 8.4, hy + 1.5, 1.8, 2.6) | f.ell(x0 + 8.4, hy + 1.5, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy + 1.5, 8.0, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    hair_front(f, x0, hy, 0)
    _eyes(f, P, (x0 - 5, x0 + 3), hy + 0.5)
    f.detail(f.rect(x0 - 1, hy + 6, x0 + 1 + (1 if P['face'] == 'shout' else 0), hy + 7 + (1 if P['face'] == 'shout' else 0)), ('skin', 0))
    f.detail(f.rect(x0 - 7, hy + 4, x0 - 5, hy + 5), ('blush', 2))
    f.detail(f.rect(x0 + 5, hy + 4, x0 + 7, hy + 5), ('blush', 2))
    f.dot(x0, hy + 4, ('skin', 1))


def head_north(f, P, x0, hy):
    f.add(f.ell(x0 - 8.4, hy + 1.5, 1.8, 2.6) | f.ell(x0 + 8.4, hy + 1.5, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy - 1.5, 9.6, 9.8), 'braid', z=41, rl=1.8, rs=3.0, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _back_strands(X, Y, t, x0, hy))
    f.add(f.rect(x0 - 1.8, hy + 6.5, x0 + 1.8, hy + 8.5), 'gold', z=41.5, rl=1, rs=1, line='hard', tag='braid')   # tie


def _back_strands(X, Y, t, x0, hy):
    out = t.copy()
    for k in (-4.5, 4.5):
        m = (abs(X - x0 - k * (1 - (Y - hy + 10) / 20)) < 0.6) & (Y < hy + 6) & (Y > hy - 8)
        out[m & (t >= 2)] = 1
    return out


def head_side(f, P, x0, hy):
    f.add(f.ell(x0 + 1.8, hy + 1.5, 7.2, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(x0 + 8.6, hy + 3.4, 1.4, 1.4), 'skin', z=40.5, rl=1, rs=1, line='hard')
    hair_front(f, x0, hy, 1)
    f.add(f.ell(x0 - 1.8, hy + 2.0, 1.7, 2.5), 'skin', z=45, rl=1, rs=1.2, line='hard')
    _eyes(f, P, (x0 + 4,), hy + 0.5)
    f.detail(f.rect(x0 + 6, hy + 6.5, x0 + 8, hy + 7.5 + (1 if P['face'] == 'shout' else 0)), ('skin', 0))
    f.detail(f.rect(x0 + 3, hy + 4.5, x0 + 5, hy + 5.5), ('blush', 2))


def head_3q(f, P, x0, hy, back):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW mirrored) for the turn in-betweens."""
    if back:
        f.add(f.ell(x0 + 8.0, hy + 1.8, 1.8, 2.6), 'skin', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(x0 + 6.4, hy + 3.4, 3.0, 4.6), 'skin', z=39.5, rl=1, rs=1.4, line='hard')          # the cheek's edge
        f.add(f.ell(x0 - 0.4, hy - 1.5, 9.6, 9.8) & ~(f.ell(x0 + 7.2, hy + 4.0, 2.8, 4.4) & (f.Y > hy + 0.5)), 'braid', z=41, rl=1.8,
              rs=3.0, line='hard', cast=(0, 1, 1), tonemap=lambda X, Y, t: _back_strands(X, Y, t, x0 - 0.4, hy))
        f.add(f.rect(x0 - 2.4, hy + 6.5, x0 + 1.2, hy + 8.5), 'gold', z=41.5, rl=1, rs=1, line='hard', tag='braid')
        return
    f.add(f.ell(x0 + 1.4, hy + 1.5, 7.8, 8.8), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    cap = f.ell(x0 - 0.2, hy - 3.0, 9.6, 8.6) | f.ell(x0 - 7.6, hy + 2.5, 3.0, 6.6)
    cap &= ~(f.ell(x0 + 2.6, hy + 2.5, 6.8, 6.4) & (f.Y > hy - 1.5))
    bangs = f.poly([(x0 - 4.5, hy - 6.5), (x0 - 3.5, hy + 0.5), (x0 - 1.0, hy - 2.5), (x0 + 1.5, hy + 0.5), (x0 + 4.0, hy - 3.0),
                    (x0 + 6.5, hy - 0.5), (x0 + 8.8, hy - 3.5), (x0 + 9.0, hy - 7)])
    f.add(cap | bangs, 'braid', z=44, rl=1.8, rs=2.6, line='hard', cast=(0, 1, 1), tonemap=lambda X, Y, t: _sheen(X, Y, t, x0, hy, 0))
    _eyes(f, P, (x0 - 1, x0 + 5), hy + 0.5)
    f.detail(f.rect(x0 + 2, hy + 6, x0 + 4 + (1 if P['face'] == 'shout' else 0), hy + 7 + (1 if P['face'] == 'shout' else 0)), ('skin', 0))
    f.detail(f.rect(x0 - 3, hy + 4, x0 - 1, hy + 5), ('blush', 2))
    f.detail(f.rect(x0 + 7, hy + 4, x0 + 8, hy + 5), ('blush', 2))
    f.dot(x0 + 3, hy + 4, ('skin', 1))


# ------------------------------------------------------------------------------------ build
def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    b = P['bob']
    cr = P['crouch']
    lean = P['lean']
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 20.0 + P['breath'] - max(0.0, cr * 0.1), 0.0)
    head3 = (sh3[0] + lean * 0.3, sh3[1] + 16.0, 0.0)
    off = (P['hipx'], -cr - b, 0.0)
    tw = P['twist']                                   # shoulders turned (+ = right shoulder back)
    th = tw / SHW                                     # shoulders rotate about the spine
    shR = add3(sh3, (0.3 - SHW * math.sin(th), -1.0, SHW * math.cos(th)))
    shL = add3(sh3, (0.3 + SHW * math.sin(th), -1.0, -SHW * math.cos(th)))
    # the spear: right grip at handR, left grip on the same shaft when gripL is set
    hR = add3(P['handR'] or REST_R, off)
    u3 = nrm(P['spu'])
    sps = P['sps']
    if sps is None:                                   # the butt rests lift px above the ground
        sps = (hR[1] - P['lift']) / u3[1] if u3[1] > 0.3 else 30.0
    butt3 = tuple(np.array(hR) - u3 * sps)
    if P['gripL'] is not None:
        hL = tuple(np.array(butt3) + u3 * P['gripL'])
    else:
        hL = add3(P['handL'] or REST_L, off)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    lag = P['lag'] + P['wind']
    # -------------------------------------------------- braid (behind, except from the back)
    nape3 = add3(head3, (-5.0, -5.0, -1.0))
    braid3(f, R, nape3, P['lag'], P['wind'], 42.5 if R.back else 2.0)
    # -------------------------------------------------- legs
    st = P['stance']
    knees = []
    for lat, key in ((st, 'footR'), (-st, 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.0, lat)
        hp3 = add3(hip3, (0, 0, lat * 0.9))
        far = R.far(lat)
        dim = 1 if far else 0
        up, lo, kn3 = R.limb(hp3, ank3, 8.8, 8.6, 3.9, 3.5, 3.2, (1.0, 0.0, 0.1 * np.sign(lat)))
        z = R.zleg(foot3)
        f.add(up | lo, 'violet', z=z, rl=1.5, rs=2.4, dim=dim, line='hard')
        knees.append(R.p(kn3))
        fx, fy = R.p(foot3)
        if R.diag:                                  # contract v2: the three-quarter boot
            surf.boot_3q(f, R, foot3, 'brownb', z + 1, dim=dim, cuff=False)
        elif side:
            boot_side(f, fx, fy, 'brownb', z=z + 1, dim=dim)
            f.add(f.rect(fx - 1.0, fy - 4.5, fx + 3.5, fy - 3.5), 'brownb', z=z + 1.4, flat=3, dim=dim, line=None)     # v2: the lit toe cap
            f.add(f.rect(fx - 3.5, fy - 1.2, fx + 4.5, fy - 0.2), 'brownb', z=z + 1.4, flat=0, dim=dim, line=None)     # and the dark welt
            f.add(f.cap(fx - 0.8, fy - 7.5, fx - 0.2, fy - 7.5, 3.6) & (f.Y > fy - 9.5), 'brownb', z=z + 1.5, flat=1, line='soft', dim=dim)
        else:
            m = (f.ell(fx, fy - 2.6, 4.4, 3.0) | f.rect(fx - 3.5, fy - 8, fx + 3.5, fy - 2)) & (f.Y < fy)
            f.add(m, 'brownb', z=z + 1, rl=1.6, rs=2.2, line='hard')
            f.add(f.rect(fx - 3.9, fy - 9, fx + 3.9, fy - 6) & f.ell(fx, fy - 7.5, 4.5, 3), 'brownb', z=z + 1.5, flat=1, line='soft')
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    # -------------------------------------------------- coat
    top = hy - 10                      # waist seam (high belt)
    hem = hy + 8.5
    if side:
        kx = [k[0] for k in knees]
        fr = max(hx + 9.5, max(kx) + 4.0)
        bk = min(hx - 10.5 - lag * 0.6, min(kx) - 4.0)
        skirt = f.poly([(hx - 7.5, top), (hx + 8.0, top), (fr, hem - 1), (fr - 6, hem + 0.5), (hx - 3, hem + 1),
                        (bk, hem + 0.5)])
        f.add(skirt, 'berry', z=20, rl=2, rs=3.2, vgrad=0.4, line='hard',
              tonemap=lambda X, Y, t: _planes(_split(X, Y, t, hx + 4.5, hy - 4, 0.12 + 0.02 * (fr - hx - 9.5)), X, hx, -3.0, 6.5, f.flip))
        f.add(f.poly([(hx - 7.5, top), (hx - 4.5, top), (bk + 3.5, hem), (bk, hem + 0.5)]), 'taupe', z=21, rl=1.4, rs=2.2, line='soft')
        body = f.ell(sx + 0.5, sy + 4, 7.8, 9) | f.rect(sx - 7, sy + 2, sx + 8, top + 1)
        f.add(body, 'berry', z=22, rl=2, rs=3.6, vgrad=0.3, line='hard')
        for yy in (sy + 1, sy + 5, sy + 9):
            f.add(f.rect(sx + 6, yy, sx + 8, yy + 2), 'gold', z=23, flat=2, line=None)
        f.add(f.rect(hx - 7.5, top, hx + 8.5, top + 3), 'brownb', z=24, rl=1, rs=1.2, line='soft')
        f.add(f.rect(hx + 5.5, top - 1, hx + 8.5, top + 4), 'gold', z=25, rl=1, rs=1.4, line='hard')
        # harness: across the chest from the right shoulder to the left hip
        with f.tagging('harness'):
            if facing == 'E':
                f.add(f.poly([(sx - 3, sy - 2), (sx + 0.5, sy - 2), (sx + 4.0, sy + 4), (sx + 0.5, sy + 4)]), 'brownb', z=31.5, flat=1, line='soft')
            else:
                f.add(f.poly([(sx - 3, sy - 2), (sx, sy - 2), (hx + 8, top), (hx + 5, top)]), 'brownb', z=25.5, rl=1, rs=1.2, line='soft')
                f.add(f.ell(sx + 3.5, sy + 7, 1.6, 1.6), 'gold', z=25.8, rl=1, rs=1, line='hard')
            f.add(f.poly([(sx - 7.5, sy + 1), (sx - 5.5, sy - 1), (hx - 4, top + 1), (hx - 6.5, top + 1)]), 'brownb', z=22.5, flat=1, line='soft')
    else:
        vf = ('N' if R.back else 'S') if R.diag else facing        # turn in-betweens: the S or N coat turned onto the body
        tw_ = turn.Warp(f, R, (sx + hx) / 2, 11.0, 8.5, vf) if R.diag else None
        if tw_:
            tw_.__enter__()
        lx = [k[0] for k in knees]
        wl = max(12.5, hx - min(lx) + 4.5) if lx else 12.5
        wr = max(12.5, max(lx) - hx + 4.5) if lx else 12.5
        skirt = f.poly([(hx - 9.8, top), (hx + 9.8, top), (hx + wr, hem - 1), (hx + 7, hem + 1), (hx, hem), (hx - 7, hem + 1), (hx - wl, hem - 1)])
        if vf == 'S':
            f.add(skirt & (f.X > hx - 4.5) & (f.X < hx + 4.5), 'taupe', z=19, rl=1.4, rs=2, line=None)
            vee = f.poly([(hx, top + 3), (hx - 4.5, hem + 2), (hx + 4.5, hem + 2)])
            for half in (skirt & (f.X < hx) & ~vee, skirt & (f.X >= hx) & ~vee):
                f.add(half, 'berry', z=20, rl=2, rs=3.2, vgrad=0.4, line='hard')
        else:
            f.add(skirt, 'berry', z=20, rl=2, rs=3.2, vgrad=0.4, line='hard',
                  tonemap=lambda X, Y, t: _vent(X, Y, t, hx, top + 8))
        for s in (-1, 1):
            f.add(f.poly([(hx + 9.8 * s, top), (hx + (wr if s > 0 else wl) * s, hem - 1), (hx + (wr if s > 0 else wl) * s - 3.5 * s, hem),
                          (hx + 7.0 * s, top + 1)]), 'taupe', z=21, rl=1.4, rs=2.2, line='soft')
        body = f.ell(sx, sy + 4, 9.8, 9) | f.rect(sx - 9.2, sy + 2, sx + 9.2, top + 1)
        f.add(body, 'berry', z=22, rl=2, rs=3.6, vgrad=0.3, line='hard')
        f.add(f.rect(hx - 9.8, top, hx + 9.8, top + 3), 'brownb', z=24, rl=1, rs=1.2, line='soft')
        with f.tagging('harness'):
            if vf == 'S':
                for yy in (sy + 1, sy + 5, sy + 9):
                    f.add(f.rect(sx + 1.5, yy, sx + 3.5, yy + 2), 'gold', z=23, flat=2, line=None)
                f.detail(f.rect(sx + 0.5, sy - 1, sx + 1.5, top), ('berry', 0))
                f.add(f.rect(hx - 2, top - 1, hx + 2, top + 4), 'gold', z=25, rl=1, rs=1.4, line='hard')
                # right shoulder (viewer left) to left hip (viewer right)
                f.add(f.poly([(sx - 9, sy - 2), (sx - 5.5, sy - 2), (hx + 9.5, top), (hx + 6, top)]), 'brownb', z=25.5, rl=1, rs=1.2, line='soft')
                f.add(f.ell(sx - 2.5, sy + 4.5, 1.6, 1.6), 'gold', z=25.8, rl=1, rs=1, line='hard')
            else:
                # back: two straps crossing at a gold ring between the shoulder blades
                f.add(f.poly([(sx + 9, sy - 2), (sx + 5.5, sy - 2), (hx - 9.5, top), (hx - 6, top)]), 'brownb', z=25.5, rl=1, rs=1.2, line='soft')
                f.add(f.poly([(sx - 9, sy - 2), (sx - 5.5, sy - 2), (hx + 9.5, top), (hx + 6, top)]), 'brownb', z=25.4, rl=1, rs=1.2, line='soft')
                f.add(f.ell(sx, sy + 6.5, 2.0, 2.0), 'gold', z=25.8, rl=1, rs=1, line='hard')
        if tw_:
            tw_.__exit__(None, None, None)
    # -------------------------------------------------- arms
    def spz(p3):
        d = R.d(p3)
        if d >= -3.5 and p3[1] > head3[1] - 12:      # a near shaft passing the head is in front of it
            return 46.0 + 0.05 * d
        return 30.5 + 0.05 * d if d >= -3.5 else 6.5 + 0.05 * d
    arms = {}
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        far = R.far(lat)
        dim = 1 if far else 0
        pole = P['pole' + key] or (-1.0, -0.2, 0.6 * lat)
        z = P['z' + key] if P['z' + key] is not None else R.zarm(hh)
        up, lo, el3 = R.limb(sh, hh, 8.6, 8.4, 3.3, 3.0, 2.8, pole)
        f.add(up, 'taupe', z=z, rl=1.4, rs=2.2, dim=dim, line='hard', cast=(1, 1, 1))
        f.add(lo, 'taupe', z=z + 0.1, rl=1.4, rs=2.2, dim=dim, line='hard', cast=(1, 1, 1))
        (ex, ey), (hxp, hyp) = R.p(el3), R.p(hh)
        c0 = (ex + (hxp - ex) * 0.6, ey + (hyp - ey) * 0.6)
        c1 = (ex + (hxp - ex) * 0.85, ey + (hyp - ey) * 0.85)
        f.add(f.cap(c0[0], c0[1], c1[0], c1[1], 3.2), 'berry', z=z + 0.2, rl=1, rs=1.6, dim=dim, line='soft')
        px, py = R.p(sh)
        f.add(f.ell(px, py + 0.5, 4.0, 3.8) & (f.Y < py + 3), 'berry', z=max(26, z + 0.15) if not far else z + 0.15,
              rl=1.4, rs=2.2, dim=dim, line='soft')
        arms[key] = (hh, z, far)
    # -------------------------------------------------- spear and hands
    tip = spear(f, R, butt3, u3, P, spz)
    f.anchor('spear_tip', *tip)
    f.anchor('spear_butt', *R.p(butt3))
    g = R.p(add3(hR, tuple(u3)))
    for key in ('R', 'L'):
        hh, z, far = arms[key]
        x, y = R.p(hh)
        held = key == 'R' or P['gripL'] is not None
        grip = (g[0] - R.p(hR)[0], g[1] - R.p(hR)[1]) if held else None
        hz = max(z + 0.8, spz(hh) + 0.3) if held else z + 0.8
        f.add(f.ell(x, y, 3.0, 3.0), 'skin', z=hz, rl=1.4, rs=2.0, dim=1 if far else 0, line='hard')
        if grip is not None and math.hypot(*grip) > 0.2:
            ux, uy = grip
            Lg = math.hypot(ux, uy)
            ux, uy = ux / Lg, uy / Lg
            f.detail(f.seg(x - uy * 1.5 + ux * 0.7, y + ux * 1.5 + uy * 0.7, x + uy * 1.5 + ux * 0.7, y - ux * 1.5 + uy * 0.7), ('skin', 1), z=hz + 0.01)
    # -------------------------------------------------- scarf
    nx_, ny_ = R.p(add3(sh3, (0.5, 3.5, 0)))
    if side:
        f.add(f.ell(nx_ + 1, ny_, 7, 3.4), 'scarf', z=36, rl=1.6, rs=2.2, line='hard', cast=(0, 1, 1))
        f.add(f.poly([(nx_ - 4, ny_ - 0.5), (nx_ - 1, ny_ + 1.5), (nx_ - 6 - lag * 1.2, ny_ + 9 - lag * 0.4),
                      (nx_ - 9 - lag * 1.4, ny_ + 7 - lag * 0.5)]), 'scarf', z=35, rl=1.2, rs=2, line='hard')
    else:
        f.add(f.ell(nx_, ny_, 8, 3.6), 'scarf', z=36, rl=1.6, rs=2.2, line='hard', cast=(0, 1, 1))
        if not R.back:
            f.add(f.poly([(nx_ - 5.5, ny_ + 1.5), (nx_ - 1.5, ny_ + 1.5), (nx_ - 2.5 - lag * 0.2, ny_ + 11.5), (nx_ - 5, ny_ + 10.5)]),
                  'scarf', z=35.5, rl=1.2, rs=2, line='hard', cast=(1, 1, 1))
        else:
            f.add(f.poly([(nx_ + 1.5, ny_ + 1), (nx_ + 5.5, ny_ + 1), (nx_ + 5 + lag * 0.2, ny_ + 10), (nx_ + 2.5, ny_ + 10.5)]),
                  'scarf', z=35.5, rl=1.2, rs=2, line='hard')
    # -------------------------------------------------- head
    x0, y0 = R.p(head3)
    y0 += 2.0
    if R.diag:
        head_3q(f, P, x0, y0, R.back)
    elif facing == 'S':
        head_south(f, P, x0, y0)
    elif facing == 'N':
        head_north(f, P, x0, y0)
    else:
        head_side(f, P, x0, y0)
    if P['arc'] is not None:
        tx, ty = tip
        for k in range(2):
            a = (P['arc'] * 1.7 + k * 2.6)
            bolt(f, tx, ty, tx + math.cos(a) * 12, ty + math.sin(a) * 10 - 4, seed=P['arc'] * 11 + k)


def _planes(t, X, hx, back, front, west=False):
    """v2 volume: three planes on the profile skirt.  The light is upper left on the screen: in E the
    back panel faces it and the front turns away; in W (the mirrored grid) the other way round."""
    out = t.copy()
    lit, dark = ((X > hx + front), (X < hx + back)) if west else ((X < hx + back), (X > hx + front))
    out[lit & (out >= 1)] = 3
    out[dark & (out >= 1)] = 0
    return out


def _split(X, Y, t, x0, y0, slope):
    out = t.copy()
    m = (abs(X - x0 - (Y - y0) * slope) < 0.6) & (Y > y0 + 2)
    out[m] = 0
    return out


def _vent(X, Y, t, hx, y0):
    out = t.copy()
    out[(abs(X - hx) < 0.6) & (Y > y0)] = 0
    return out


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f
