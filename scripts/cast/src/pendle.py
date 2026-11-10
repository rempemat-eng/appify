"""Pendle: the robot gunslinger (pass 2).  A cattleman hat with a pinched crown and a brass
concho, a rounded slate head with two round amber lamp eyes, a red bandana tied over the lower
face, a long brown duster with a shoulder capelet and a back vent, a gunmetal body with a brass
chest plate, segmented brass arms on dark ball joints, brass knee caps and shin guards, gunmetal
boots with brass toe caps.  One revolver in the holster on the RIGHT hip (grip, cylinder and
trigger guard visible), and one marksman rifle with a brass scope slung across the back: stock
low at the right hip, barrel up past the LEFT shoulder.  No clock motif.  About 74 px with hat.

Pose-driven like bramble.py (parts.Rig): the same pose renders S, N, E and W.
Equipment tags: revolver, rifle, hat."""
import math
import numpy as np
from ew import Fig
from parts import boot_side, Rig, proj
import palette  # noqa: F401
import anim
import surf
import turn

ID = 'pendle'
NAME = 'Pendle'
SHW = 14.0
REST_R = (3.0, 26.0, 17.0)
REST_L = (1.5, 25.0, -16.0)
RL = 40.0                         # rifle length, butt to muzzle


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, twist=0.0,
             footR=(2.0, 0.0), footL=(-2.0, 0.0), stance=5.5,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             revolver='holster', aim=(1.0, 0.0, 0.0), roll=0.0, cyl=0.0, rounds=6, shells=None, flash=0,
             rifle='back', rt=0.0, rdir=(1.0, 0.0, 0.0), rgrip=8.0, rfore=23.0, lever=0.0,
             lag=0.0, blink=False, fx=None)
    p.update(k)
    return p


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def nrm(v):
    v = np.array(v, float)
    return v / (np.linalg.norm(v) or 1.0)


def lamp(f, x, y, off=False):
    """Round eye lamp, 3x3: bright core at the upper left, warm rim, a dim bottom-right pixel."""
    if off:
        f.detail(f.rect(x, y + 1, x + 3, y + 2), ('glow', 0), tag='face')
        return
    f.detail(f.rect(x, y, x + 3, y + 3), ('glow', 2), tag='face')
    f.detail(f.rect(x, y, x + 1, y + 1), ('glow', 1), tag='face')          # rounded corner
    f.detail(f.rect(x + 2, y + 2, x + 3, y + 3), ('glow', 1), tag='face')
    f.detail(f.rect(x + 1, y, x + 2, y + 2), ('glow', 3), tag='face')      # hot core


def revolver_holstered(f, R, hip3, z, dim=0, gun=True):
    """Holster on the right hip; with gun, the revolver's grip, hammer and cylinder show above
    the holster mouth (without, the holster is empty: the revolver is in his hand)."""
    g3 = add3(hip3, (-0.5, 1.0, 11.5))
    x, y = R.p(g3)
    sgn = 1 if R.facing in 'EW' else (-1 if R.facing == 'S' else 1)
    hol = f.poly([(x - 2.6, y - 1), (x + 2.6, y - 1), (x + 2.0, y + 9), (x - 1.6, y + 9.5)])
    f.add(hol, 'leather', z=z, rl=1, rs=1.6, dim=dim, line='hard', tag='holster')
    if not gun:
        f.add(f.rect(x - 2.0, y - 1, x + 2.0, y + 0.5), 'leather', z=z + 0.06, flat=0, dim=dim, line=None, tag='holster')
        f.add(f.rect(x - 2.4, y + 4, x + 2.4, y + 5) & hol, 'brass', z=z + 0.05, flat=1, dim=dim, line=None)
        return
    f.add(f.rect(x - 2.4, y + 4, x + 2.4, y + 5) & hol, 'brass', z=z + 0.05, flat=1, dim=dim, line=None)
    # grip angled back, cylinder above the holster mouth
    gx = -2.0 if R.facing in 'EW' else 0.0
    grip = f.poly([(x - 1.5, y - 1), (x + 1.5, y - 1), (x + 1.0 + gx, y - 6), (x - 1.8 + gx, y - 5.5)])
    f.add(grip, 'rifle', z=z + 0.1, rl=1, rs=1.4, dim=dim, line='hard', tag='revolver')
    f.add(f.ell(x + 0.8, y - 1.6, 2.0, 1.6), 'gunmetal', z=z + 0.2, rl=1, rs=1.2, dim=dim, line='hard', tag='revolver')


def revolver_hand(f, R, h3, d3, z, dim=0, cyl=0.0, rounds=6):
    """Revolver held at h3, barrel along d3.  cyl 0..1 swings the cylinder out to the gun's
    LEFT on its crane (the reload); rounds = cartridges showing in the open cylinder.
    Returns the muzzle (pivot space)."""
    d3 = nrm(d3)
    hx, hy = R.p(h3)
    upv = np.array([0.0, 1.0, 0.0])
    m3 = np.array(h3) + d3 * 9.0 + upv * 1.8
    c3 = np.array(h3) + d3 * 2.5 + upv * 1.8
    mx, my = R.p(m3)
    cx, cy = R.p(c3)
    L = math.hypot(mx - cx, my - cy)
    with f.tagging('revolver'):
        f.add(f.cap(cx, cy, mx, my, 1.1) if L > 1.5 else f.ell(mx, my, 1.4, 1.4), 'gunmetal', z=z, rl=1, rs=1, dim=dim, line='hard')
        f.add(f.ell(cx, cy, 1.9, 1.6), 'gunmetal', z=z + 0.05, rl=1, rs=1.2, dim=dim, line='hard')        # frame
        f.add(f.cap(hx, hy, hx - (mx - cx) * 0.15, hy + 3.0, 1.3), 'rifle', z=z - 0.1, rl=1, rs=1.2, dim=dim, line='hard')
        # the cylinder: in the frame when closed, out to the gun's left on the crane when open
        side3 = np.cross(d3, upv)                      # the gun's right
        o3 = c3 - side3 * 3.0 * cyl - upv * 3.2 * cyl          # out and down, clear of the frame
        ox, oy = R.p(tuple(o3))
        f.add(f.ell(ox, oy, 2.3 + 0.9 * cyl, 2.0 + 1.0 * cyl), 'gunmetal', z=z + 0.1 + 0.6 * cyl, rl=1, rs=1.2, dim=dim, line='hard')
        if cyl > 0.5:
            f.detail(f.seg(cx, cy + 1, ox, oy + 1), ('gunmetal', 1), z=z + 0.12)                         # crane
            for i in range(6):
                a = i * math.pi / 3
                c = ('brass', 3) if i < rounds else ('gunmetal', 0)
                f.dot(ox + round(math.cos(a) * 1.7), oy + round(math.sin(a) * 1.6), c, z=z + 0.8)
    return mx, my


def flash(f, x, y, ux, uy, n, z=58):
    """Muzzle flash along the barrel direction (ux, uy): n = 1 full, 2 fading."""
    r = 3.2 if n == 1 else 2.0
    m = f.ell(x + ux * r, y + uy * r, r, r) | f.cap(x, y, x + ux * r * 2.6, y + uy * r * 2.6, 0.9)
    m |= f.cap(x + ux * r - uy * r * 1.2, y + uy * r + ux * r * 1.2, x + ux * r + uy * r * 1.2, y + uy * r - ux * r * 1.2, 0.6)
    f.add(m, 'glow', z=z, rl=1.2, rs=0.8, line=None, tag='flash')
    f.dot(x + ux * 1.5, y + uy * 1.5, ('glow', 3), z=z + 0.5)


def shells(f, x, y, n, t):
    """n spent cases tumbling from (x, y) downward; t 0..1 is how far they have fallen."""
    for i in range(n):
        sx = x + (i - n / 2) * 1.6
        sy = y + 3 + t * (10 + i * 2.5)
        f.detail(f.rect(sx, sy, sx + 1, sy + 2), ('brass', 3 if i % 2 else 2), tag='shells')


def rifle(f, R, s3, u3, zf):
    """The one marksman rifle, RL long from the butt s3 along u3: stock, receiver, barrel,
    fore-end and a brass scope on top.  zf(p3) gives depths, so a stock behind the body hides.
    Returns the muzzle (pivot space)."""
    u3 = nrm(u3)
    s3 = np.array(s3, float)
    upv = np.array([0.0, 1.0, 0.0])
    side = np.cross(u3, upv)
    top = np.cross(side, u3)                       # the rifle's top (scope side)
    if np.linalg.norm(top) < 1e-3:
        top = np.array([1.0, 0, 0])
    top = top / np.linalg.norm(top)

    def at(t, up=0.0):
        return R.p(tuple(s3 + u3 * t + top * up))
    (sx, sy), (kx, ky), (bx, by) = at(0), at(11), at(RL)
    (tx, ty) = at(0, -3.2)
    (t2x, t2y) = at(11, -1.4)
    zs, zb = zf(tuple(s3 + u3 * 5)), zf(tuple(s3 + u3 * 26))
    with f.tagging('rifle'):
        stock = f.poly([at(0, 0.8), (tx, ty), (t2x, t2y), at(11, 0.8)])
        f.add(stock, 'rifle', z=zs, rl=1.2, rs=1.8, line='hard', cast=(1, 1, 1) if zs > 20 else None)
        f.add(f.cap(kx, ky, *at(17), 1.5), 'gunmetal', z=zb, rl=1, rs=1.2, line='hard')            # receiver
        f.add(f.cap(*at(16), bx, by, 1.0), 'gunmetal', z=zb + 0.05, rl=1, rs=1.2, line='hard')     # barrel
        f.add(f.cap(*at(19, -1.3), *at(28, -1.3), 1.0), 'rifle', z=zb + 0.06, rl=1, rs=1.2, line='hard')  # fore-end
        f.add(f.cap(*at(11.5, 2.6), *at(20, 2.6), 1.25), 'brass', z=zb + 0.1, rl=1, rs=1.2, line='hard')  # scope
    return bx, by


def rifle_back3(hip3, sh3):
    """Butt and direction of the slung rifle: stock low behind the right hip, barrel up past the
    left shoulder."""
    s3 = np.array(add3(hip3, (-8.5, 2.0, 10.0)))
    b3 = np.array(add3(sh3, (-11.0, 20.0, -24.0)))
    return s3, nrm(b3 - s3)


def brass_arm(f, R, sh3, h3, z, pole, far):
    dim = 1 if far else 0
    up, lo, el3 = R.limb(sh3, h3, 8.8, 8.6, 3.5, 3.1, 2.8, pole)
    f.add(up, 'brass', z=z, rl=1.3, rs=2.0, dim=dim, line='hard', cast=(1, 1, 1))
    f.add(lo, 'brass', z=z + 0.1, rl=1.3, rs=2.0, dim=dim, line='hard', cast=(1, 1, 1))
    (ex, ey) = R.p(el3)
    f.add(f.ell(ex, ey, 1.9, 1.9), 'robo', z=z + 0.2, rl=1, rs=1.4, dim=dim, line='hard')     # elbow ball
    sx, sy = R.p(sh3)
    f.add(f.ell(sx, sy, 3.3, 3.1), 'robo', z=z - 0.1, rl=1.2, rs=1.6, dim=dim, line='hard')   # shoulder ball
    # segment bands on the forearm
    hx, hy = R.p(h3)
    mx, my = ex + (hx - ex) * 0.5, ey + (hy - ey) * 0.5
    L = math.hypot(hx - ex, hy - ey) or 1
    ux, uy = (hx - ex) / L, (hy - ey) / L
    f.detail(f.seg(mx - uy * 2.2, my + ux * 2.2, mx + uy * 2.2, my - ux * 2.2), ('brass', 0))
    return el3


def gun_hand(f, x, y, z, far=False):
    f.add(f.ell(x, y + 0.5, 2.9, 2.9), 'gunmetal', z=z, rl=1.4, rs=2.0, dim=1 if far else 0, line='hard')


def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    b = P['bob']
    cr = P['crouch']
    lean = P['lean']
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 19.0 + P['breath'], 0.0)
    head3 = (sh3[0] + lean * 0.3, sh3[1] + 13.5, 0.0)
    off = (P['hipx'], -cr - b, 0.0)
    th = P['twist'] / SHW                             # shoulders turned (+ = right shoulder back)
    shR = add3(sh3, (0.3 - SHW * math.sin(th), -1.5, SHW * math.cos(th)))
    shL = add3(sh3, (0.3 + SHW * math.sin(th), -1.5, -SHW * math.cos(th)))
    hR = add3(P['handR'] or REST_R, off)
    hL = add3(P['handL'] or REST_L, off)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    # ---------------------------------------- the rifle: slung, being drawn, or in both hands
    bs3, bu3 = rifle_back3(hip3, sh3)
    rz = (lambda p3: 28.5) if R.back else (lambda p3: 1.0)
    rifle_s3 = None
    if P['rifle'] == 'back':
        rifle_s3, rifle_u3 = bs3, bu3
    else:
        hu3 = nrm(P['rdir'])
        hs3 = np.array(hR) - hu3 * P['rgrip']
        t = P['rt'] if P['rifle'] == 'pull' else 1.0
        rifle_s3 = bs3 + (hs3 - bs3) * t
        rifle_u3 = nrm(bu3 + (hu3 - bu3) * t)
        if t > 0.3:
            def rz(p3):
                d = R.d(p3)
                return 35.0 + 0.05 * d if d >= -3.5 else 8.0 + 0.05 * d
        hL = tuple(rifle_s3 + rifle_u3 * P['rfore'])
        f.anchor('hand_L', *R.p(hL))
    muzzle = rifle(f, R, rifle_s3, rifle_u3, rz)
    if P['rifle'] != 'back':
        f.anchor('muzzle', *muzzle)
    # ---------------------------------------- legs
    st = P['stance']
    for lat, key in ((st, 'footR'), (-st, 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.0, lat)
        hp3 = add3(hip3, (0, 0, lat * 0.9))
        far = R.far(lat)
        dim = 1 if far else 0
        up, lo, kn3 = R.limb(hp3, ank3, 8.4, 8.2, 3.6, 3.3, 3.0, (1.0, 0.0, 0.1 * np.sign(lat)))
        z = R.zleg(foot3)
        f.add(up | lo, 'robo', z=z, rl=1.4, rs=2.0, dim=dim, line='hard')
        kx, ky = R.p(kn3)
        f.add(f.ell(kx + (1.2 if side else 0), ky, 3.0 if not side else 2.4, 2.6), 'brass', z=z + 0.3, rl=1.2, rs=1.6, dim=dim, line='hard')
        ax_, ay_ = R.p(ank3)
        f.add(f.cap(kx, ky + 2.5, ax_, ay_ - 0.5, 2.9, 2.6) & (f.Y > ky + 3.5), 'brass', z=z + 0.2, rl=1.2, rs=1.8, dim=dim, line='hard')
        fx, fy = R.p(foot3)
        if R.diag:                                  # contract v2: the three-quarter boot
            surf.boot_3q(f, R, foot3, 'gunmetal', z + 1, dim=dim, cuff=False)
        elif side:
            boot_side(f, fx, fy, 'gunmetal', z=z + 1, dim=dim, toe=2.0)
            f.add(f.ell(fx + 4.4, fy - 2.4, 2.4, 2.4) & (f.Y < fy - 0.5), 'brass', z=z + 1.2, rl=1, rs=1.2, dim=dim, line='hard')
        else:
            m = (f.ell(fx, fy - 2.6, 4.6, 3.0) | f.rect(fx - 3.7, fy - 7, fx + 3.7, fy - 2)) & (f.Y < fy)
            f.add(m, 'gunmetal', z=z + 1, rl=1.6, rs=2.2, line='hard')
            if facing == 'S':
                f.add(f.ell(fx, fy - 2.0, 2.6, 1.6), 'brass', z=z + 1.2, rl=1, rs=1.2, line='hard')
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    # ---------------------------------------- duster, body, belt
    lag = P['lag']
    if side:
        coat = f.poly([(sx - 8.5, sy), (sx + 7.0, sy), (hx + 9.5, hy - 2), (hx + 9.5, hy + 9.5), (hx + 4, hy + 10.5),
                       (hx - 5, hy + 11.5), (hx - 13.5 - lag, hy + 11), (hx - 11.5 - lag * 0.4, hy - 2)])
        f.add(coat, 'duster', z=20, rl=2, rs=3.4, vgrad=0.4, line='hard',
              tonemap=lambda X, Y, t: _lines(X, Y, t, [(hx - 4.5, hy - 1, -0.32, hy + 1), (hx + 1.5, hy, -0.12, hy + 3)]))
        front = f.poly([(sx + 5.5, sy + 1), (sx + 8.5, sy + 1), (hx + 9.5, hy - 2), (hx + 9.5, hy + 3), (hx + 7.0, hy + 3)])
        f.add(front, 'robo', z=21, rl=1.2, rs=2, line='hard')
        f.add(f.poly([(sx + 5, sy + 2), (sx + 8.4, sy + 2), (sx + 8.6, sy + 9), (sx + 5.5, sy + 9)]), 'brass', z=21.5, rl=1, rs=1.4, line='hard')
        f.add(f.poly([(hx - 10, hy - 6), (hx + 9.8, hy - 6), (hx + 9.8, hy - 3), (hx - 10, hy - 3)]), 'leather', z=24, rl=1, rs=1.2, line='soft')
        for i in range(4):
            f.add(f.rect(hx - 8 + i * 3, hy - 5.5, hx - 7 + i * 3, hy - 3.5), 'brass', z=24.5, flat=2, line=None)
        f.add(f.rect(hx + 7, hy - 7, hx + 10, hy - 2), 'brass', z=25, rl=1, rs=1.4, line='hard')
        cap = f.poly([(sx - 9, sy - 2), (sx - 2, sy - 4), (sx + 6, sy - 3), (sx + 8.5, sy + 1), (sx + 6, sy + 6),
                      (sx - 3, sy + 7.5), (sx - 10.5 - lag * 0.6, sy + 6)])
        f.add(cap, 'duster', z=27, rl=1.8, rs=2.6, vgrad=0.3, line='hard', cast=(0, 1, 1))
    else:
        vf = ('N' if R.back else 'S') if R.diag else facing      # turn in-betweens: the S or N duster turned
        tw_ = turn.Warp(f, R, (sx + hx) / 2, 12.0, 9.0, vf) if R.diag else None
        if tw_:
            tw_.__enter__()
        coat = f.poly([(sx - 11.5, sy), (sx + 11.5, sy), (hx + 13, hy - 2), (hx + 15.0, hy + 10.5), (hx + 9.5, hy + 11.5),
                       (hx + 3.5, hy + 10.0), (hx - 3.5, hy + 10.0), (hx - 9.5, hy + 11.5), (hx - 15.0, hy + 10.5), (hx - 13, hy - 2)])
        if vf == 'N':
            f.add(coat, 'duster', z=20, rl=2, rs=3.4, vgrad=0.4, line='hard',
                  tonemap=lambda X, Y, t: _vent(X, Y, t, hx, hy))
            f.add(f.rect(hx - 12.5, hy - 6, hx + 12.5, hy - 3.5), 'duster', z=24, flat=1, line='soft')       # back belt
            for s in (-1, 1):
                f.add(f.rect(hx + 3 * s - 1, hy - 6.5, hx + 3 * s + 1, hy - 3), 'brass', z=24.5, flat=2, line=None)
        else:
            f.add(coat, 'duster', z=20, rl=2, rs=3.4, vgrad=0.4, line='hard',
                  tonemap=lambda X, Y, t: _lines(X, Y, t, [(hx - 9.5, hy, 0.14, hy + 1), (hx + 9.5, hy, -0.14, hy + 1)]))
            torso = f.poly([(sx - 5, sy), (sx + 5, sy), (hx + 4, hy + 10), (hx - 4, hy + 10)])
            f.add(torso, 'robo', z=21, rl=1.4, rs=2.4, line='hard')
            f.add(f.poly([(sx - 4.5, sy + 2), (sx + 4.5, sy + 2), (sx + 3.5, sy + 10), (sx - 3.5, sy + 10)]), 'brass', z=21.5, rl=1.2, rs=1.8, line='hard')
            f.add(f.rect(sx - 0.5, sy + 3, sx + 0.5, sy + 9), 'brass', z=21.6, flat=1, line=None)
            f.add(f.rect(hx - 13, hy - 6, hx + 13, hy - 3), 'leather', z=24, rl=1, rs=1.2, line='soft')
            for i in (-9, -6, 6, 9):
                f.add(f.rect(hx + i - 0.5, hy - 5.5, hx + i + 0.5, hy - 3.5), 'brass', z=24.5, flat=2, line=None)
            f.add(f.rect(hx - 2.5, hy - 7, hx + 2.5, hy - 2), 'brass', z=25, rl=1, rs=1.4, line='hard')
            for s in (-1, 1):
                f.add(f.poly([(sx + 5 * s, sy), (sx + 9 * s, sy), (sx + 5.5 * s, sy + 10), (sx + 4.2 * s, sy + 7)]), 'duster', z=26, rl=1.2, rs=1.6, line='soft')
        cap = f.ell(sx, sy + 1, 13.0, 6.0) & (f.Y > sy - 3)
        cap |= f.poly([(sx - 13, sy + 1), (sx - 11, sy + 7), (sx - 6, sy + 6), (sx, sy + 8 if vf == 'N' else sy + 4),
                       (sx + 6, sy + 6), (sx + 11, sy + 7), (sx + 13, sy + 1)])
        if vf == 'S':
            cap &= ~f.poly([(sx - 5, sy - 4), (sx + 5, sy - 4), (sx, sy + 6)])
        f.add(cap, 'duster', z=27, rl=1.8, rs=2.6, vgrad=0.3, line='hard', cast=(0, 1, 1))
        if tw_:
            tw_.__exit__(None, None, None)
    # ---------------------------------------- holster (right hip)
    hd = R.d(add3(hip3, (0, 0, 12)))
    revolver_holstered(f, R, hip3, 26 if hd > -2 else 12, dim=1 if R.far(1) else 0, gun=P['revolver'] == 'holster')
    # ---------------------------------------- arms
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        far = R.far(lat)
        pole = P['pole' + key] or (-1.0, -0.2, 0.6 * lat)
        z = P['z' + key] if P['z' + key] is not None else R.zarm(hh)
        brass_arm(f, R, sh, hh, z, pole, far)
        hx_, hy_ = R.p(hh)
        if key == 'R' and P['revolver'] == 'hand':
            mz = revolver_hand(f, R, hh, P['aim'], z + 0.4, dim=1 if far else 0, cyl=P['cyl'], rounds=P['rounds'])
            f.anchor('muzzle', *mz)
            if P['flash']:
                L = math.hypot(mz[0] - hx_, mz[1] - hy_) or 1.0
                flash(f, mz[0], mz[1], (mz[0] - hx_) / L, (mz[1] - hy_) / L, P['flash'],
                      z=58 if R.d(add3(hh, tuple(nrm(P['aim']) * 10))) > -4 else 5)
            if P['shells']:
                shells(f, hx_, hy_, *P['shells'])
        gun_hand(f, hx_, hy_ + 1, z + 0.6, far)
    if P['rifle'] != 'back' and P['flash']:
        (ax, ay) = R.p(tuple(rifle_s3))
        L = math.hypot(muzzle[0] - ax, muzzle[1] - ay) or 1.0
        flash(f, muzzle[0], muzzle[1], (muzzle[0] - ax) / L, (muzzle[1] - ay) / L, P['flash'],
              z=58 if R.d(tuple(rifle_s3 + rifle_u3 * RL)) > -4 else 5)
    # ---------------------------------------- head, bandana, hat
    x0, y0 = R.p(head3)
    if R.diag:
        head_3q(f, P, x0, y0, R.back)
    else:
        head(f, facing, P, x0, y0)


def head_3q(f, P, x0, hy, back):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW mirrored): the slate dome turned, the
    visor band and both lamps toward the facing (front), the ear bolt and the bandana's knot (back)."""
    h = f.ell(x0 + 0.8, hy, 8.4, 8.0) | f.rect(x0 - 7.4, hy - 2, x0 + 9.0, hy + 4)
    f.add(h, 'robo', z=40, rl=1.8, rs=2.6, line='hard', cast=(0, 2, 1))
    if back:
        f.add(f.ell(x0 + 8.8, hy + 1, 1.6, 2.4), 'brass', z=39, rl=1, rs=1.2, line='hard')
        back_of_head(f, P, x0 + 0.5, hy, w=8.0)
        hat(f, x0 + 0.5, hy, 0, 'N')
        return
    f.add(f.ell(x0 - 7.4, hy + 1, 2.0, 2.6), 'brass', z=41.5, rl=1, rs=1.2, line='hard')          # near ear bolt
    f.dot(x0 - 7.4, hy + 1, ('brass', 0))
    f.add(f.rect(x0 - 3.0, hy - 2.5, x0 + 9.0, hy + 2.5) & h, 'gunmetal', z=41, flat=0, line=None)
    lamp(f, x0 - 1, hy - 2, P['blink'])
    lamp(f, x0 + 5, hy - 2, P['blink'])
    band = f.poly([(x0 - 7.8, hy + 2), (x0 + 9.4, hy + 2), (x0 + 9.0, hy + 7), (x0 + 5.5, hy + 12), (x0 + 2.5, hy + 13.5),
                   (x0 - 1.0, hy + 11.5), (x0 - 7.4, hy + 7)])
    f.add(band, 'bandana', z=42, rl=1.4, rs=2.4, line='hard', cast=(0, 1, 1), tag='face',
          tonemap=lambda X, Y, t: _band_planes(_lines(X, Y, t, [(x0 - 1, hy + 4, 0.35, hy + 5), (x0 + 5, hy + 4, -0.35, hy + 5)]), X, Y,
                                               x0 + 1.0, hy))
    hat(f, x0 + 0.8, hy, 0, 'S')


def back_of_head(f, P, x0, hy, w=8.6):
    """Seen from behind (26 Oct reviews and squint test: the back must not read as a face, dark or
    blank): a gunslinger's back.  The duster's collar is turned up high at the back and the hat's
    back brim sits low, so only a narrow band of the steel back plate shows between them, with a
    seam; the bandana is only a small knot off-centre at his right on that band, its tails hanging
    over the collar to that side.  The hat shows its crown dent and band from behind (hat())."""
    plate = f.ell(x0 + 0.3, hy - 0.5, 7.0, 6.8) & (f.Y < hy + 4.5)
    f.add(plate, 'steel', z=41, rl=1.4, rs=2.0, line='hard', tag='headplate')
    f.detail(f.rect(x0, hy - 3, x0 + 1, hy + 3) & plate, ('steel', 1))                         # seam
    collar = f.poly([(x0 - w - 1.5, hy + 9.5), (x0 - w - 0.8, hy + 2.6), (x0 - 4.0, hy + 1.4), (x0 + 4.0, hy + 1.4),
                     (x0 + w + 0.8, hy + 2.6), (x0 + w + 1.5, hy + 9.5)])
    f.add(collar, 'duster', z=43, rl=1.6, rs=2.4, line='hard', cast=(0, 1, 1), tag='collar',
          tonemap=lambda X, Y, t: _collar_fold(X, Y, t, x0, hy))
    kx = x0 + 5.0
    f.add(f.ell(kx, hy + 1.6, 1.5, 1.3), 'bandana', z=43.6, rl=1, rs=1.0, line='hard', tag='bandana')     # small knot, off-centre
    tails = (f.poly([(kx - 0.5, hy + 2.2), (kx + 1.0, hy + 2.2), (kx + 2.6, hy + 7.0), (kx + 1.3, hy + 7.3)])
             | f.poly([(kx + 0.5, hy + 2.0), (kx + 1.5, hy + 1.8), (kx + 4.2, hy + 5.4), (kx + 3.2, hy + 5.8)]))
    f.add(tails, 'bandana', z=43.5, rl=1, rs=1.2, line='hard', tag='bandana')


def _collar_fold(X, Y, t, x0, hy):
    """The turned-up collar's centre-back crease and its lit left wing."""
    out = t.copy()
    m = (np.abs(X - x0 - 0.5) < 0.5) & (Y > hy + 3.0)
    out[m & (t >= 1)] = np.maximum(t[m & (t >= 1)] - 1, 0)
    lit = (X < x0 - 3.0) & (Y < hy + 5.0) & (t == 2)
    out[lit] = 3
    return out


def head(f, facing, P, x0, hy):
    side = facing in 'EW'
    if not side:
        h = f.ell(x0, hy, 8.4, 8.0) | f.rect(x0 - 8.2, hy - 2, x0 + 8.2, hy + 4)
        f.add(h, 'robo', z=40, rl=1.8, rs=2.6, line='hard', cast=(0, 2, 1))
        for s in (-1, 1):
            f.add(f.ell(x0 + 8.8 * s, hy + 1, 1.7, 2.4), 'brass', z=39, rl=1, rs=1.2, line='hard')
        if facing == 'S':
            f.add(f.rect(x0 - 6.5, hy - 2.5, x0 + 6.5, hy + 2.5), 'gunmetal', z=41, flat=0, line=None)
            lamp(f, x0 - 5, hy - 2, P['blink'])
            lamp(f, x0 + 2, hy - 2, P['blink'])
            # bandana tied over the lower face, its point down the chest
            band = f.poly([(x0 - 8.6, hy + 2), (x0 + 8.6, hy + 2), (x0 + 8, hy + 7), (x0 + 3, hy + 12), (x0, hy + 14),
                           (x0 - 3, hy + 12), (x0 - 8, hy + 7)])
            f.add(band, 'bandana', z=42, rl=1.4, rs=2.4, line='hard', cast=(0, 1, 1), tag='face',
                  tonemap=lambda X, Y, t: _band_planes(_lines(X, Y, t, [(x0 - 3, hy + 4, 0.35, hy + 5), (x0 + 3, hy + 4, -0.35, hy + 5)]), X, Y, x0, hy))
        else:
            back_of_head(f, P, x0, hy)
        hat(f, x0, hy, 0, facing)
    else:
        h = f.ell(x0 + 1.5, hy, 8.0, 8.0) | f.rect(x0 - 6, hy - 2, x0 + 8.8, hy + 4)
        f.add(h, 'robo', z=40, rl=1.8, rs=2.6, line='hard', cast=(0, 2, 1))
        f.add(f.rect(x0 + 3, hy - 2.5, x0 + 9.5, hy + 2.5) & h, 'gunmetal', z=41, flat=0, line=None)
        lamp(f, x0 + 5, hy - 2, P['blink'])
        f.add(f.ell(x0 - 2.0, hy + 1, 2.2, 2.6), 'brass', z=41.5, rl=1, rs=1.2, line='hard')       # ear bolt
        f.dot(x0 - 2.0, hy + 1, ('brass', 0))
        band = f.poly([(x0 - 4, hy + 3), (x0 + 9.5, hy + 2), (x0 + 10, hy + 7), (x0 + 6, hy + 12), (x0 + 3, hy + 12.5), (x0 - 4.5, hy + 7)])
        f.add(band, 'bandana', z=42, rl=1.4, rs=2.4, line='hard', cast=(0, 1, 1), tag='face')
        f.add(f.poly([(x0 - 4, hy + 4), (x0 - 2, hy + 5), (x0 - 7 - P['lag'], hy + 9), (x0 - 8 - P['lag'], hy + 6.5)]), 'bandana', z=41.8, rl=1, rs=1.6, line='hard')
        hat(f, x0 + 1.0, hy, 1, facing)


def hat(f, x0, hy, side, facing):
    """Cattleman hat: brim curled up at the sides, pinched crown, dark band with a brass concho."""
    if not side:
        by = hy - (4.8 if facing == 'N' else 6.0)       # from behind the back brim sits low over the turned-up collar
        brim = f.ell(x0, by, 15.5, 3.0 if facing == 'N' else 3.4) | f.ell(x0 - 13.5, hy - 7.6, 3.0, 2.2) | f.ell(x0 + 13.5, hy - 7.6, 3.0, 2.2)
        crown = f.poly([(x0 - 8, hy - 6.5), (x0 - 7.5, hy - 14.5), (x0 - 4, hy - 17), (x0, hy - 15), (x0 + 4, hy - 17),
                        (x0 + 7.5, hy - 14.5), (x0 + 8, hy - 6.5)])
        f.add(brim, 'hat', z=50, rl=1.4, rs=2.0, line='hard', cast=None if facing == 'N' else (0, 2, 2), tag='hat',
              tonemap=lambda X, Y, t: _hat_planes(X, Y, t, x0, by, brim=True))
        f.add(crown, 'hat', z=51, rl=1.8, rs=2.6, line='hard', cast=(0, 1, 1), tag='hat',
              tonemap=lambda X, Y, t: _hat_planes(X, Y, _lines(X, Y, t, [(x0, hy - 15, 0.0, hy - 15.5)], top=hy - 11), x0, hy - 12))
        f.add(f.rect(x0 - 7.8, hy - 9.5, x0 + 7.8, hy - 7) & crown, 'leather', z=51.5, flat=0, line=None, tag='hat')
        if facing == 'S':
            f.add(f.ell(x0 - 4, hy - 8.3, 1.6, 1.3), 'brass', z=51.6, rl=1, rs=1, line=None, tag='hat')
        else:                     # from behind: the crown's dent runs down the back, and the band's tie at his right
            f.detail(f.seg(x0, hy - 15.5, x0 + 0.5, hy - 10.5) & crown, ('hat', 0), tag='hat')
            f.detail(f.rect(x0 + 4.5, hy - 9.5, x0 + 6.5, hy - 6.0) & crown, ('leather', 2), tag='hat')
    else:
        brim = f.ell(x0, hy - 6.2, 14.5, 3.0) | f.ell(x0 + 12.5, hy - 7.6, 2.8, 2.0)
        crown = f.poly([(x0 - 7, hy - 6.5), (x0 - 6, hy - 14.5), (x0 - 1, hy - 17), (x0 + 2, hy - 15.5), (x0 + 6, hy - 15.5),
                        (x0 + 7.5, hy - 6.5)])
        f.add(brim, 'hat', z=50, rl=1.4, rs=2.0, line='hard', cast=(0, 2, 2), tag='hat',
              tonemap=lambda X, Y, t: _hat_planes(X, Y, t, x0, hy - 6.2, brim=True))
        f.add(crown, 'hat', z=51, rl=1.8, rs=2.6, line='hard', cast=(0, 1, 1), tag='hat',
              tonemap=lambda X, Y, t: _hat_planes(X, Y, t, x0, hy - 12))
        f.add(f.rect(x0 - 7, hy - 9.5, x0 + 7.6, hy - 7) & crown, 'leather', z=51.5, flat=0, line=None, tag='hat')
        f.add(f.ell(x0 + 4.5, hy - 8.3, 1.5, 1.3), 'brass', z=51.6, rl=1, rs=1, line=None, tag='hat')


def _band_planes(t, X, Y, x0, hy):
    """v2 volume for the bandana's front: lit where it rounds over the left of the jaw, shaded under
    the right, the point darker."""
    out = t.copy()
    out[(X < x0 - 4.5) & (Y < hy + 7) & (t >= 1)] = 3
    out[(X > x0 + 4.5) & (t >= 1)] = 1
    out[(Y > hy + 11) & (t >= 1)] = np.minimum(out[(Y > hy + 11) & (t >= 1)], 1)
    return out


def _hat_planes(X, Y, t, x0, yc, brim=False):
    """v2 volume for the felt hat: the crown's left (lit) face, its right face in shade; the brim's
    top lit toward the light and its rolled underside dark."""
    out = t.copy()
    if brim:
        out[(Y > yc + 0.8) & (t >= 1)] = 0
        out[(Y < yc - 0.8) & (X < x0) & (t >= 1)] = 3
        return out
    m = t >= 1
    out[m & (X < x0 - 2.5)] = 3
    out[m & (X >= x0 - 2.5) & (X <= x0 + 3.5)] = 2
    out[m & (X > x0 + 3.5)] = 1
    out[(t == 0)] = 0
    return out


def _lines(X, Y, t, lines, top=None):
    out = t.copy()
    for (x0, y0, slope, ymin) in lines:
        m = (abs(X - x0 - (Y - y0) * slope) < 0.6) & (Y > ymin)
        if top is not None:
            m &= Y < top
        out[m & (t >= 2)] = 1
    return out


def _vent(X, Y, t, hx, hy):
    out = t.copy()
    out[(abs(X - hx) < 0.6) & (Y > hy + 1)] = 0
    return out


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f
