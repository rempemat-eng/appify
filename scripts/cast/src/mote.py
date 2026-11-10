"""Mote: the observatory keeper.  A bald, genderless humanoid with blue-grey skin, a smooth tall
head, quiet amber eyes and a small gold slot glyph on the brow (no mouth, no brows: restrained).
A long navy coat over a darker under-robe, open at the front, edged in gold; the hem breaks into
pointed fragments, each outer one with a glass inlay.  A tall standing collar, two gold crescent
hooks rising from the shoulders, wide gold cuffs.  The core sits on the chest: a gold ring round
a blue glass lens with an amber light inside.  About 77 px tall and slim.

Pass 3: pose-driven on parts.Rig; the coat, collar and head of the approved static design ride
the projected hip / shoulder / head through nix.Sh.  One construction throughout: the hem
fragments only lag (lag) and never detach; the glass inlays stay in their fragments; the core
is always the same chest core.  Aphelion (aphelion 0..1) parts the coat fronts and lifts the
collar flaps so the SAME core is exposed and lit; powered clips keep it open.  The glass shard
Mote throws (primary) forms in the right hand (glass 0..1) and leaves at the release; the
orbiting shards of the powered state are separate effects (out/mote/fx/shard_<n>.png).
Tags: core, hooks, glass.  Anchors: hand_R, hand_L, foot_R, foot_L, core, shard."""
import math
import numpy as np
from ew import Fig, mat
from parts import boot_side, boot_front, Rig
import palette  # noqa: F401
import anim
import surf
import turn
from nix import Sh, skel, legs, add3, nrm

ID = 'mote'
NAME = 'Mote'
BAND = (72, 84)

mat('mt_skin',  ['#3C3C58', '#66688A', '#9496B8', '#C2C4DC'])
mat('mt_robe',  ['#0E1028', '#1A1C42', '#292E5E', '#3E4682'])
mat('mt_under', ['#0A0B1C', '#13142E', '#1C1F44', '#2A2E5C'])
mat('mt_glass', ['#2C4A6E', '#4A7AA8', '#8CC0DC', '#D8F2FA', '#FFFFFF'])

SHW = 9.8
REST_R = (1.0, 31.5, 11.5)
REST_L = (1.0, 31.5, -11.5)


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0,
             footR=(1.5, 0.0), footL=(-1.5, 0.0), stance=4.4,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             aphelion=0.0, glow=0.0, glass=0.0, lag=0.0, blink=False, face=None)
    p.update(k)
    return p


# ------------------------------------------------------------------------------------ pieces
def lamp_eye(f, x, y, blink=False):
    if blink:
        f.detail(f.rect(x, y + 2, x + 2, y + 3), ('mt_skin', 0), tag='face')
        return
    f.detail(f.rect(x, y, x + 2, y + 3), '#1E1917', tag='face')
    f.detail(f.rect(x, y, x + 2, y + 2), ('amber', 2), tag='face')
    f.dot(x, y, ('amber', 3), tag='face')
    f.dot(x + 1, y + 1, ('amber', 1), tag='face')


def glyph(f, x, y):
    f.detail(f.rect(x - 1, y, x + 1, y + 4), ('gold', 2))
    f.detail(f.rect(x - 1, y, x, y + 1), ('gold', 3))
    f.detail(f.rect(x, y + 1, x + 1, y + 3), ('gold', 0))


def core(f, x, y, z, side=False, k=0.0, glow=0.0):
    """Gold ring, blue glass lens, an amber light inside.  k (Aphelion) brightens the lens and
    adds a lit rim; glow (a pulse) lights the centre."""
    with f.tagging('core'):
        if not side:
            if k > 0.05:
                f.add(f.ell(x, y, 5.6 + 1.0 * k, 5.4 + 1.0 * k) & ~f.ell(x, y, 4.6, 4.4), 'amber', z=z - 0.05, flat=3,
                      line=None, clean=False)
            f.add(f.ell(x, y, 4.8, 4.6), 'gold', z=z, rl=1.4, rs=2.0, line='hard', cast=(1, 1, 1))
            f.add(f.ell(x, y, 2.8, 2.7), 'mt_glass', z=z + 0.1, rl=1.2, rs=1.4, line='soft')
            c = ('amber', 3) if (k > 0.5 or glow > 0.5) else ('amber', 2)
            f.detail(f.rect(x - 0.5 - (1 if k > 0.5 else 0), y - 0.5 - (1 if k > 0.5 else 0), x + 1.5, y + 1.5), c, z=z + 0.1)
            f.dot(x - 1.5, y - 1.5, ('mt_glass', 4), z=z + 0.1)
            f.dot(x - 0.5, y - 0.5, ('amber', 3), z=z + 0.1)
        else:
            if k > 0.05:
                f.add(f.ell(x + 0.6, y, 3.4 + 0.8 * k, 5.4 + 1.0 * k) & ~f.ell(x, y, 2.6, 4.6), 'amber', z=z - 0.05, flat=3,
                      line=None, clean=False)
            f.add(f.ell(x, y, 2.6, 4.6), 'gold', z=z, rl=1.2, rs=1.6, line='hard', cast=(1, 1, 1))
            f.add(f.ell(x + 1.1, y, 1.4, 2.7), 'mt_glass', z=z + 0.1, rl=1, rs=1.2, line='soft')
            f.detail(f.rect(x + 1, y - (1 if k > 0.5 else 0), x + 2, y + 1), ('amber', 3 if (k > 0.5 or glow > 0.5) else 2), z=z + 0.1)


def hook(f, s, x, y, z, dim=0, kx=1.0):
    """Gold crescent rising from the shoulder at (x, y) and curling outward (s = +1 screen right)."""
    s = s * kx
    m = (f.cap(x, y, x + 1.4 * s, y - 6.0, 1.3) | f.cap(x + 1.4 * s, y - 6.0, x + 4.6 * s, y - 8.4, 1.15)
         | f.cap(x + 4.6 * s, y - 8.4, x + 7.4 * s, y - 7.0, 1.05) | f.cap(x + 7.4 * s, y - 7.0, x + 7.6 * s, y - 4.4, 0.95))
    f.add(m, 'gold', z=z, rl=1, rs=1.2, dim=dim, line='hard', tag='hooks')


def _hem_pts(x0, x1, y, n, depth, phase=0.0):
    pts = []
    for i in range(n):
        a = x0 + (x1 - x0) * i / n
        c = x0 + (x1 - x0) * (i + 0.5) / n
        d = depth * (1.0 if (i + int(phase)) % 2 == 0 else 0.55)
        pts += [(a, y), (c, y + d)]
    pts.append((x1, y))
    return pts


def trim(f, mask, z=0, w=1.0):
    from scipy import ndimage as ndi
    inner = ndi.binary_erosion(mask, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]], iterations=int(w))
    return mask & ~inner


def shard(f, x, y, z, s=1.0, ang=0.6):
    """A glass shard: a slim lens-blue diamond with a white glint."""
    c, si = math.cos(ang), math.sin(ang)
    L, W = 4.2 * s, 1.6 * s
    pts = [(x + c * L, y + si * L), (x - si * W, y + c * W), (x - c * L * 0.8, y - si * L * 0.8), (x + si * W, y - c * W)]
    f.add(f.poly(pts), 'mt_glass', z=z, rl=1, rs=1.2, line='hard', tag='glass')
    f.dot(x + c * L * 0.3, y + si * L * 0.3 - 1, ('mt_glass', 4), z=z, tag='glass')


# ------------------------------------------------------------------------------------ coat
def coat_front(f, b, ub, back=False, ap=0.0, lag=0.0):
    hem = min(-10 + b, -4.0)          # kneeling: the hem pools on the ground, never below it
    L = _hem_pts(-14.5 - lag * 0.5, -1.0 if not back else 0.0, hem, 3, 3.4 + abs(lag) * 0.3, 0)
    R = [(-x, y) for (x, y) in reversed(_hem_pts(-14.5 - lag * 0.5, -1.0 if not back else 0.0, hem, 3, 3.4 + abs(lag) * 0.3, 1))]
    neck = [(-9.6, -47 + ub), (9.6, -47 + ub)] if back else [(-9.6, -47 + ub), (-4.0, -47 + ub), (0.0, -42.5 + ub), (4.0, -47 + ub), (9.6, -47 + ub)]
    outline = neck + [(10.4, -36 + ub), (14.5 + lag * 0.5, hem)] + R + L[::-1][1:] + [(-14.5 - lag * 0.5, hem), (-10.4, -36 + ub)]
    coat = f.poly(outline)
    if back:
        f.add(coat, 'mt_robe', z=20, rl=2.0, rs=3.4, vgrad=0.35, line='hard', tonemap=lambda X, Y, t: _back_seam(X, Y, t, ub))
        edge = trim(f, coat) & (f.Y > hem - 3.0)
        vent = f.poly([(-0.8, -25 + b), (0.8, -25 + b), (2.2, hem + 2), (-2.2, hem + 2)]) & coat
        f.add(vent, 'mt_under', z=20.5, rl=1, rs=1.6, line='soft')
        f.add((f.cap(-1.2, -25 + b, -2.6, hem + 2, 0.6) | f.cap(1.2, -25 + b, 2.6, hem + 2, 0.6)) & coat, 'gold', z=21, flat=2, line=None)
        f.add(edge, 'gold', z=21, rl=1, rs=1, tl=0.2, line=None)
        _glass_inlays(f, b)
        return
    f.add(coat, 'mt_robe', z=20, rl=2.0, rs=3.4, vgrad=0.35, line='hard')
    g = 2.6 + 3.0 * ap                       # Aphelion parts the fronts from the chest down
    gap = f.poly([(-g, -44 + ub), (g, -44 + ub), (4.4 + ap, hem + 3), (-4.4 - ap, hem + 3)]) & coat
    f.add(gap, 'mt_under', z=21, rl=1.4, rs=2.4, vgrad=0.3, line='soft', tonemap=lambda X, Y, t: _under_fold(X, Y, t, b))
    for s in (-1, 1):
        f.add(f.cap((g + 0.3) * s, -44 + ub, (4.7 + ap) * s, hem + 1.5, 0.75) & coat, 'gold', z=22, flat=2, line=None)
    edge = trim(f, coat) & (f.Y > hem - 3.0) & ~gap
    f.add(edge, 'gold', z=21.5, rl=1, rs=1, tl=0.2, line=None)
    _glass_inlays(f, b)


def _glass_inlays(f, b):
    hem = min(-10 + b, -4.0)          # kneeling: the hem pools on the ground, never below it
    for s in (-1, 1):
        x = 11.5 * s
        f.add(f.poly([(x - 1.2, hem - 3.0), (x + 1.2, hem - 3.0), (x, hem + 0.6)]), 'mt_glass', z=22.5, rl=1, rs=1, line=None,
              clean=False)
        f.dot(x - (0 if s > 0 else 1), hem - 3, ('mt_glass', 4), z=22.5)


def _under_fold(X, Y, t, b):
    out = t.copy()
    out[(abs(X) < 0.6) & (Y > -24 + b)] = 0
    return out


def _back_seam(X, Y, t, ub):
    out = t.copy()
    m = (abs(X) < 0.6) & (Y > -44 + ub) & (Y < -26 + ub)
    out[m & (t >= 1)] = 0
    return out


def coat_side(f, b, ub, ap=0.0, lag=0.0):
    hem = min(-10 + b, -4.0)          # kneeling: the hem pools on the ground, never below it
    back = _hem_pts(-14.0 - lag, 1.0, hem, 3, 3.2 + abs(lag) * 0.3, 0)
    outline = [(-3.0, -48 + ub), (4.5, -48 + ub), (7.0 + ap, -38 + ub), (8.0, -26 + b), (9.0 - lag * 0.3, hem)] + \
              [(x - lag * 0.3, y) for (x, y) in reversed(_hem_pts(1.0, 9.0, hem, 2, 3.0, 1))][1:] + back[::-1][1:] + [(-9.0, -36 + ub)]
    coat = f.poly(outline)
    f.add(coat, 'mt_robe', z=20, rl=2.0, rs=3.4, vgrad=0.35, line='hard')
    gx = 6.0 - 1.5 * ap
    gap = f.poly([(gx, -44 + ub), (7.6 + ap, -44 + ub), (9.2, hem + 2), (6.0, hem + 2)]) & coat
    f.add(gap, 'mt_under', z=21, rl=1, rs=1.8, line='soft')
    f.add(f.cap(gx - 0.4, -44 + ub, 6.2, hem + 1.5, 0.7) & coat, 'gold', z=22, flat=2, line=None)
    f.add(trim(f, coat) & (f.Y > hem - 3.0) & ~gap, 'gold', z=21.5, rl=1, rs=1, tl=0.2, line=None)
    x = -9.5 - lag * 0.7
    f.add(f.poly([(x - 1.2, hem - 3.0), (x + 1.2, hem - 3.0), (x, hem + 0.6)]), 'mt_glass', z=22.5, rl=1, rs=1, line=None, clean=False)
    f.dot(x - 1, hem - 3, ('mt_glass', 4), z=22.5)


# ------------------------------------------------------------------------------------ arms
def sleeve(f, R, sh3, h3, pole, z, dim):
    up, lo, el3 = R.limb(sh3, h3, 8.4, 7.4, 3.6, 3.6, 4.0, pole)
    f.add(up | lo, 'mt_robe', z=z, rl=1.6, rs=2.6, dim=dim, line='hard', cast=(1, 1, 1))
    hx, hy = R.p(h3)
    ex, ey = R.p(el3)
    L = math.hypot(hx - ex, hy - ey) or 1.0
    ux, uy = (hx - ex) / L, (hy - ey) / L
    f.add(lo & (((f.X - hx) * ux + (f.Y - hy) * uy) > -2.4), 'gold', z=z + 0.1, rl=1, rs=1.4, dim=dim, line='soft')
    px, py = hx + ux * 2.6, hy + uy * 2.6
    f.add(f.ell(px, py, 2.8, 3.0), 'mt_skin', z=z + 0.2, rl=1.2, rs=1.8, dim=dim, line='hard')
    return px, py


# ------------------------------------------------------------------------------------ build
def build(f, facing, P):
    R = Rig(f, facing)
    S = skel(R, P, sh_up=44.0, head_up=17.0)
    T, b, ub = S['T'], S['b'], S['ub']
    side = R.side
    ap = P['aphelion']
    f.anchor('origin', 0.0, 0.0)
    # -------------------------------------------------- legs (mostly under the coat)
    for lat, key in ((P['stance'], 'footR'), (-P['stance'], 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.3, foot3[1] + 5.5, lat)
        hp3 = add3(S['hip3'], (0.0, 0.0, lat * 0.9))
        up, lo, kn3 = R.limb(hp3, ank3, 8.6, 8.2, 3.4, 3.2, 3.0, (1.0, 0.0, 0.1 * np.sign(lat)))
        far = R.far(lat)
        z = R.zleg(foot3)
        f.add(up | lo, 'mt_skin', z=z, rl=1.4, rs=2.2, dim=1 if far else 0, line='hard')
        fx, fy = R.p(foot3)
        if R.diag:                                   # contract v2: the three-quarter boot
            surf.boot_3q(f, R, foot3, 'mt_under', z + 1, dim=1 if far else 0, cuff=False)
        elif side:
            boot_side(f, fx, fy, 'mt_under', z=z + 1, dim=1 if far else 0, toe=1.2, h=6)
        else:
            boot_front(f, fx, fy, 'mt_under', z=z + 1)
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    sh3 = S['sh3']
    hands = {}
    for key, lat, rest in (('R', 1, REST_R), ('L', -1, REST_L)):
        h3 = add3(P['hand' + key] or rest, S['body_off'])
        z = P['z' + key] if P['z' + key] is not None else R.zarm(h3)
        if z < 20 and not side:
            z = 4.0
        hands[key] = (lat, h3, z)
    # -------------------------------------------------- coat, collar, core
    vf = ('N' if R.back else 'S') if R.diag else facing      # turn in-betweens: the S or N coat turned onto the body
    tw_ = turn.Warp(f, R, (S['sx'] + S['hx']) / 2, 10.5, 8.0, vf) if R.diag else None
    if tw_:
        tw_.__enter__()
    if vf == 'S':
        col = T.poly([(-8.0, -54 + ub), (-6.0, -56 + ub), (6.0, -56 + ub), (8.0, -54 + ub), (9.0, -45 + ub), (-9.0, -45 + ub)])
        T.add(col, 'mt_robe', z=1, rl=1.4, rs=2.4, line='hard')
        T.add(T.poly([(-6.0, -54 + ub), (6.0, -54 + ub), (6.5, -46 + ub), (-6.5, -46 + ub)]), 'mt_under', z=1.1, flat=0, line=None)
        coat_front(T, b, ub, ap=ap, lag=P['lag'])
        T.detail(T.seg(-2.5, -37 + ub, 0, -31 + ub) | T.seg(2.5, -37 + ub, 0, -31 + ub), ('steel', 3), solid=False, z=29)
        T.dot(0, -30 + ub, ('steel', 2), z=29)
        cx, cy = T._x(0, -41 + ub - ap), -41 + ub - ap
        core(f, cx, cy, 30, k=ap, glow=P['glow'])
        T.add(T.rect(-2.0, -53 + ub, 2.0, -44 + ub), 'mt_skin', z=19, flat=1, line='hard')
    elif vf == 'N':
        coat_front(T, b, ub, back=True, lag=P['lag'])
        cx, cy = T._x(0, -41 + ub), -41 + ub
    else:
        coat_side(T, b, ub, ap=ap, lag=P['lag'])
        T.detail(T.seg(6.5, -37 + ub, 7.0, -31 + ub), ('steel', 3), solid=False, z=29)
        cx, cy = T._x(7.4 + ap * 0.8, -41 + ub - ap), -41 + ub - ap
        core(f, cx, cy, 30, side=True, k=ap, glow=P['glow'])
        T.add(T.poly([(-6.0, -57 + ub), (-1.0, -55 + ub), (1.5, -47 + ub), (-6.5, -45 + ub)]), 'mt_robe', z=27, rl=1.4, rs=2.4,
              line='hard', cast=(1, 1, 1))
        T.add(T.cap(1.0, -49 + ub, 3.5, -48 + ub, 2.4), 'mt_skin', z=24, rl=1, rs=1.6, line='hard')
    if tw_:
        tw_.__exit__(None, None, None)
        cx, cy = tw_.fwd(cx, cy)[:2]
    f.anchor('core', cx, cy)
    # -------------------------------------------------- sleeves, hooks, hands
    for key in ('R', 'L'):
        lat, h3, z = hands[key]
        far = R.far(lat)
        shp = add3(sh3, (0.3, 0.0, SHW * lat))
        pole = P['pole' + key] or (-1.0, -0.2, 0.7 * lat)
        px, py = sleeve(f, R, shp, h3, pole, z, 1 if far else 0)
        f.anchor('hand_' + key, px, py)
        if key == 'R' and P['glass'] > 0.05:
            shard(f, px + 0.5, py - 4.5, z + 0.9, s=0.7 + 0.7 * min(1.0, P['glass']), ang=-1.2)
            f.anchor('shard', px + 0.5, py - 4.5)
        sx, sy = R.p(add3(sh3, (0.3, -2.0, (SHW - 1.0) * lat)))
        if side:
            hook(f, 1 if not far else -1, sx - 0.4, sy, 33 if not far else 2, dim=1 if far else 0, kx=0.35)
        else:
            hook(f, 1 if sx > S['sx'] else -1, sx, sy, 28)
    # -------------------------------------------------- head
    H, hy = S['H'], S['qy']
    if R.diag:
        head_3q(H, P, hy, R.back, ub, T)
    elif facing == 'S':
        head_south(H, P, hy)
    elif facing == 'N':
        head_north(H, P, hy, ub, T)
    else:
        head_side(H, P, hy)


def skull(f, x, hy, z, side=False):
    if side:
        m = f.ell(x, hy - 1.4, 7.4, 8.6) | f.ell(x + 2.4, hy + 3.8, 5.0, 5.6)
    else:
        m = f.ell(x, hy - 1.4, 7.2, 8.6) | f.ell(x, hy + 3.6, 5.6, 5.8)
    f.add(m, 'mt_skin', z=z, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1), tonemap=lambda X, Y, t: _skull(X, Y, t, hy, x, _west(f)))


def _west(f):
    while not hasattr(f, 'flip') and hasattr(f, 'f'):
        f = f.f
    return bool(getattr(f, 'flip', False))


def _skull(X, Y, t, hy, x0=0.0, west=False):
    """Three planes on the dome, lit from the upper left: lit crown, base, dark jaw side; then the shine."""
    out = t.copy()
    u, v = (X - x0) / 7.2, (Y - hy + 1.4) / 8.6
    d = (0.55 if west else -0.55) * u - 0.85 * v      # the mirrored grid keeps the light at the upper left
    body = t >= 1
    out[body] = 1
    out[body & (d > 0.18)] = 2
    out[body & (d < -0.55)] = 0
    m = (((X - x0 + (-2.4 if west else 2.4)) / 2.4) ** 2 + ((Y - hy + 6.6) / 1.4) ** 2 <= 1.0)
    out[m & (out == 2)] = 3
    return out


def head_south(f, P, hy):
    f.add(f.ell(-7.0, hy + 1.6, 1.2, 2.0) | f.ell(7.0, hy + 1.6, 1.2, 2.0), 'mt_skin', z=39, rl=1, rs=1.2, line='hard')
    skull(f, 0, hy, 40)
    x0 = round(f._x(0, hy))
    g = f.f
    glyph(g, x0, round(hy - 7))
    ey = round(hy + 0.6)
    lamp_eye(g, x0 - 5, ey, P['blink'] or P['face'] == 'shut')
    lamp_eye(g, x0 + 3, ey, P['blink'] or P['face'] == 'shut')
    g.detail(g.rect(x0 - 5, ey - 1, x0 - 3, ey), ('mt_skin', 1))
    g.detail(g.rect(x0 + 3, ey - 1, x0 + 5, ey), ('mt_skin', 1))
    g.detail(g.rect(x0, round(hy) + 4, x0 + 1, round(hy) + 5), ('mt_skin', 1))


def head_north(f, P, hy, ub, T):
    f.add(f.ell(-7.0, hy + 1.6, 1.2, 2.0) | f.ell(7.0, hy + 1.6, 1.2, 2.0), 'mt_skin', z=39, rl=1, rs=1.2, line='hard')
    skull(f, 0, hy, 40)
    col = T.poly([(-7.0, -54 + ub), (-3.0, -55.5 + ub), (3.0, -55.5 + ub), (7.0, -54 + ub), (9.0, -45 + ub), (-9.0, -45 + ub)])
    T.add(col, 'mt_robe', z=41, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1))
    T.add(trim(T, col) & (T.Y < -52.5 + ub), 'gold', z=41.5, flat=2, line=None)


def head_3q(f, P, hy, back, ub, T):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW mirrored) for the turn in-betweens."""
    if back:
        f.add(f.ell(6.4, hy + 1.6, 1.2, 2.0), 'mt_skin', z=39, rl=1, rs=1.2, line='hard')
        skull(f, 0.4, hy, 40)
        col = T.poly([(-6.0, -54 + ub), (-2.0, -55.5 + ub), (4.0, -55.5 + ub), (8.0, -54 + ub), (9.0, -45 + ub), (-8.0, -45 + ub)])
        T.add(col, 'mt_robe', z=41, rl=1.6, rs=2.6, line='hard', cast=(0, 1, 1))
        T.add(trim(T, col) & (T.Y < -52.5 + ub), 'gold', z=41.5, flat=2, line=None)
        return
    f.add(f.ell(-6.0, hy + 1.6, 1.2, 2.0), 'mt_skin', z=39, rl=1, rs=1.2, line='hard')
    skull(f, 0.8, hy, 40, side=True)
    x0 = round(f._x(0, hy))
    g = f.f
    glyph(g, x0 + 3, round(hy - 7))
    ey = round(hy + 0.6)
    lamp_eye(g, x0 - 1, ey, P['blink'] or P['face'] == 'shut')
    lamp_eye(g, x0 + 5, ey, P['blink'] or P['face'] == 'shut')
    g.detail(g.rect(x0 - 1, ey - 1, x0 + 1, ey), ('mt_skin', 1))
    g.detail(g.rect(x0 + 5, ey - 1, x0 + 7, ey), ('mt_skin', 1))
    g.detail(g.rect(x0 + 3, round(hy) + 4, x0 + 4, round(hy) + 5), ('mt_skin', 1))


def head_side(f, P, hy):
    skull(f, 0.4, hy, 40, side=True)
    f.add(f.ell(-2.4, hy + 1.8, 1.0, 1.8), 'mt_skin', z=41, rl=1, rs=1.2, line='shade')
    x0 = round(f._x(0, hy))
    g = f.f
    ry = round(hy)
    g.detail(g.rect(x0 + 6, ry - 7, x0 + 7, ry - 3), ('gold', 2))
    g.dot(x0 + 6, ry - 7, ('gold', 3))
    lamp_eye(g, x0 + 4, ry + 1, P['blink'] or P['face'] == 'shut')
    g.detail(g.rect(x0 + 4, ry, x0 + 7, ry + 1), ('mt_skin', 1))
    f.add(f.ell(7.6, hy + 2.8, 1.1, 1.3), 'mt_skin', z=40.2, rl=1, rs=1, line='hard')


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f
