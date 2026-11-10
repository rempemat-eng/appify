"""Brine: human coastal diver.  Sealed copper helmet (front faceplate, side ports, bolted brass
neck ring and corselet), cream canvas suit reinforced with olive (yoke, knee pads, cuffs, weight
belt), navy rubber gloves and weighted boots.  A compact olive air pack on the back with ONE
breathing hose: it leaves the pack's top right valve and runs to the regulator on the helmet's
right rear.  One harpoon gun (wooden stock, gunmetal body, brass reel on the gun's right side
under the barrel, harpoon in the muzzle, a short tether from the reel to the harpoon's eye),
right hand on the pistol grip, left hand on the fore grip.  About 73 px tall.

Pass 2: one pose-driven build for all four facings (parts.Rig), like bramble.py.  A pose places
the body, feet, hands and the gun in body space (fwd, up, lat; lat + = his RIGHT).  The gun is
given by its grip point (the right hand) and its barrel direction; the left hand follows the
fore grip or the reel.  When the harpoon has been fired (loaded=False), the tether that runs out
of the muzzle is a scene effect anchored at the 'muzzle' anchor, never part of the body.

Pressure Brace (special): the left hand opens the regulator valve on the helmet, the suit
pressurises (the faceplate and port glass light up, the pack gauge shows), and he holds a lower,
braced stance; the same gun, pack, hose and helmet throughout.

Equipment tags: harpoon_gun, pack, hose, helmet, regulator."""
import math
import numpy as np
from ew import Fig, mat
from parts import boot_side, boot_front, Rig
import palette  # noqa: F401
import anim
import surf
import turn

ID = 'brine'
NAME = 'Brine'
HEIGHT = 73
BAND = (70, 79)

mat('brine_copper', ['#5A2214', '#9A3C1C', '#D2662C', '#F49A50', '#FFDDA6'])
mat('brine_glass',  ['#0C2232', '#15405A', '#22688C', '#58A8C8', '#E6F6FF'])
mat('brine_glow',   ['#155C6A', '#2A9AA8', '#6ADCD8', '#C4FFF4', '#FFFFFF'])
mat('brine_olive',  ['#252C18', '#3C4824', '#5C6A34', '#85944A'])
mat('brine_rubber', ['#16182A', '#262A42', '#3A4064', '#58608A'])
mat('brine_canvas', ['#76665E', '#B49C82', '#E0CCA8', '#F6EBD0'])

SHW = 11.0
ARM = (9.2, 8.8)
GRIP0 = (3.0, 31.0, 7.0)                 # right hand on the pistol grip at rest
AIM0 = (1.0, -0.10, -0.95)               # low ready, turned a little to his left


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0,
             footR=(1.5, 0.0), footL=(-1.5, 0.0), stance=5.8,
             grip=None, aim=None, loaded=True, handL=None, handR=None, lmode='fore', crank=0.0,
             poleR=None, poleL=None, twist=None, press=0.0, recoil=0.0, gun='hand', fx=None)
    p.update(k)
    return p


# ------------------------------------------------------------------------------------ vectors
def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def sc3(a, k):
    return tuple(x * k for x in a)


def nrm(v):
    v = np.array(v, float)
    return v / (np.linalg.norm(v) or 1.0)


def shoulders(sh3, hR, hL, shw, L, twist=None, maxt=40):
    """Shoulder joints turned about the vertical by `twist` degrees (+ brings the LEFT shoulder
    forward).  twist=None picks the smallest turn that keeps both hands within reach (arm length
    L), so a cross-body or two-handed hold turns the shoulders instead of stretching an arm."""
    def at(t):
        r = math.radians(t)
        return (add3(sh3, (-shw * math.sin(r), -0.5, shw * math.cos(r))),
                add3(sh3, (shw * math.sin(r), -0.5, -shw * math.cos(r))))
    if twist is not None:
        return at(twist) + (twist,)
    best = None
    for k in range(0, 2 * (maxt // 5) + 1):
        t = 5 * ((k + 1) // 2) * (1 if k % 2 else -1)
        sR, sL = at(t)
        reach = max(math.dist(sR, hR), math.dist(sL, hL)) / L
        if reach <= 0.97:
            return sR, sL, t
        if best is None or reach < best[0]:
            best = (reach, sR, sL, t)
    return best[1], best[2], best[3]


def gun_frame(aim):
    """Barrel direction D, 'down' across the barrel Dn (toward the grip) and the gun's right Rt."""
    D = nrm(aim)
    w = np.array([0.0, -1.0, 0.0])
    Dn = w - D * w.dot(D)
    if np.linalg.norm(Dn) < 1e-3:
        Dn = np.array([-1.0, 0.0, 0.0])
    Dn = nrm(Dn)
    Rt = np.cross(D, -Dn)
    return D, Dn, Rt


def limb2(f, R, a3, b3, l1, l2, r0, r1, r2, pole):
    up, lo, j3 = R.limb(a3, b3, l1, l2, r0, r1, r2, pole)
    return up, lo, j3


def zdepth(R, p3, front=30.0, back=6.0, lim=-3.5):
    """Simple z for arm segments and held gear: in front of the torso unless clearly behind."""
    dd = R.d(p3)
    if p3[1] > 52 and dd > -6:
        return 46.0 + 0.05 * dd
    return (front if dd >= lim else back) + 0.05 * dd


# ------------------------------------------------------------------------------------ hose
def bez(pts, n=24):
    """Points along a quadratic or cubic bezier."""
    out = []
    for i in range(n + 1):
        t = i / n
        if len(pts) == 3:
            (x0, y0), (x1, y1), (x2, y2) = pts
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2
            y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2
        else:
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
            u = 1 - t
            x = u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3
            y = u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3
        out.append((x, y))
    return out


def hose(f, pts, z, r=2.0, dim=0, tag='hose'):
    """The one breathing hose: a corrugated rubber tube along a bezier (rings every 3 px)."""
    P = bez(pts)
    m = None
    for (x0, y0), (x1, y1) in zip(P[:-1], P[1:]):
        c = f.cap(x0, y0, x1, y1, r)
        m = c if m is None else m | c
    L = np.cumsum([0] + [math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(P[:-1], P[1:])])
    rings = []
    for s in np.arange(3.0, L[-1] - 2, 3.0):
        i = int(np.searchsorted(L, s)) - 1
        x0, y0 = P[i]
        x1, y1 = P[i + 1]
        rings.append((x0, y0, x1, y1))
    flip = f.flip

    def tm(X, Y, t):
        out = t.copy()
        XX = -X if flip else X
        XX = X
        for x0, y0, x1, y1 in rings:
            dx, dy = x1 - x0, y1 - y0
            d = math.hypot(dx, dy) or 1
            along = ((XX - x0) * dx + (Y - y0) * dy) / d
            across = abs((XX - x0) * dy - (Y - y0) * dx) / d
            k = (abs(along) < 0.55) & (across < r - 0.3)
            out[k & (t >= 1)] = np.maximum(out[k & (t >= 1)] - 1, 0)
        return out
    f.add(m, 'brine_rubber', z=z, rl=1.0, rs=1.4, dim=dim, line='hard', tonemap=tm, clean=False, tag=tag)
    return P


def rivet(f, x, y, z=None):
    f.dot(x, y, ('brass', 3), z=z)
    f.dot(x, y + 1, ('brass', 0), z=z)


# ------------------------------------------------------------------------------------ gun
def harpoon_gun(f, R, grip3, aim, z, loaded=True, dim=0):
    """The harpoon gun in 3D: grip3 is the right hand on the pistol grip, aim the barrel
    direction.  Returns key points in pivot space (fore grip, reel, muzzle) and 3D points."""
    D, Dn, Rt = gun_frame(aim)
    O = np.array(grip3) - Dn * 2.6 + D * 0.2

    def p3(a, d=0.0, r=0.0):
        return tuple(O + D * a + Dn * d + Rt * r)

    def at(a, d=0.0, r=0.0):
        return R.p(p3(a, d, r))
    # how much of the barrel's length shows (1 = in profile)
    x0, y0 = at(0)
    x1, y1 = at(10)
    fs = math.hypot(x1 - x0, y1 - y0) / 10.0
    rdep = R.d(tuple(Rt))                      # >0: the gun's right side (the reel) faces us
    with f.tagging('harpoon_gun'):
        f.add(f.cap(*at(-9, 0.6), *at(-1, -0.4), 2.5, 1.8), 'rifle', z=z, rl=1.2, rs=1.6, dim=dim, line='hard')
        f.add(f.cap(*at(-2, -0.8), *at(5, -0.8), 2.3), 'gunmetal', z=z + 0.1, rl=1.2, rs=1.6, dim=dim, line='hard')
        f.add(f.cap(*at(4, -0.8), *at(17, -0.8), 1.6), 'gunmetal', z=z + 0.12, rl=1.0, rs=1.3, dim=dim, line='hard')
        mz = at(17.5, -0.8)
        tip_out = R.d(p3(17.5, -0.8)) > R.d(p3(0, -0.8))      # muzzle nearer the camera than the grip
        ez = 0.9 if (tip_out and fs < 0.6) else 0.3      # end-on toward us: over the fore glove
        f.add(f.cap(*at(16, -0.8), *mz, 2.1 + (1.0 - min(1.0, fs)) * 1.0), 'brass', z=z + (ez if tip_out else 0.14),
              rl=1.0, rs=1.2, dim=dim, line='hard')
        if fs < 0.55:                             # end-on: the bore shows in the ring
            f.add(f.ell(mz[0], mz[1], 3.0, 2.4), 'brass', z=z + (ez - 0.01 if tip_out else 0.13), rl=1, rs=1.4, dim=dim, line='hard')
            f.add(f.ell(mz[0], mz[1], 1.2, 1.0), 'gunmetal', z=z + (ez + 0.01 if tip_out else 0.15), flat=0, dim=dim, line=None)
        f.add(f.cap(*at(0.5, 0.8), *at(-0.8, 5.0), 1.5), 'rifle', z=z + 0.05, rl=1, rs=1.3, dim=dim, line='hard')
        if loaded:
            hz = z + (ez + 0.05 if tip_out else 0.13)
            f.add(f.cap(*at(17.5, -0.8), *at(22, -0.8), 0.8), 'steel', z=hz, rl=1, rs=1, dim=dim, line='hard')
            head = f.poly([at(21.5, -3.0), at(26.5, -0.8), at(21.5, 1.4), at(22.6, -0.8)])
            if fs < 0.5:
                cx_, cy_ = at(24, -0.8)
                head |= f.poly([(cx_ - 3.0, cy_), (cx_, cy_ - 1.5), (cx_ + 3.0, cy_), (cx_, cy_ + 3.5)])
            f.add(head, 'steel', z=hz + 0.02, rl=1.0, rs=1.2, dim=dim, line='hard')
        # brass reel on the gun's right side under the barrel; a disc facing along Rt
        rc = at(8.5, 3.0, 1.6)
        nx, ny = R.p(tuple(Rt))
        n2 = math.hypot(nx, ny)
        ang = math.atan2(ny, nx) + math.pi / 2 if n2 > 0.05 else 0.0
        minor = 3.3 * max(0.45, min(1.0, abs(rdep)))
        if rdep > -0.15:
            rz = z + 0.2
            f.add(f.rell(rc[0], rc[1], 3.3, minor, ang), 'brass', z=rz, rl=1.3, rs=1.8, dim=dim, line='hard')
            f.add(f.ell(rc[0], rc[1], 1.2, 1.2), 'gunmetal', z=rz + 0.05, flat=1, dim=dim, line=None)
            if loaded and fs > 0.5:
                f.add(f.seg(*at(10.5, 1.4, 1.0), *at(18.5, 0.6)), 'string', z=rz + 0.02, flat=1, line=None, clean=False,
                      noout=True, dim=dim)
        else:
            f.add(f.rell(rc[0], rc[1], 3.3, minor, ang), 'brass', z=z - 0.05, rl=1.3, rs=1.8, dim=dim + 1, line='hard')
    return dict(fore3=p3(10.5, 1.6), reel3=p3(8.5, 3.0, 4.2), muzzle=mz, fs=fs,
                handle3=p3(8.5, 3.0, 3.4), tip=at(26.5, -0.8) if loaded else mz)


# ------------------------------------------------------------------------------------ helmet
def _copper_sheen(X, Y, t, cx, hy):
    out = t.copy()
    r = ((X - cx + 3.5) / 4.2) ** 2 + ((Y - hy + 5.5) / 2.6) ** 2
    out[(r < 1.0) & (t >= 2)] = 3
    return out


def helmet_front(f, x0, hy, back=False, glass='brine_glass'):
    """Copper helmet seen from the front (or back), centred at (x0, hy)."""
    f.add(f.ell(x0, hy - 0.5, 12.3, 11.6), 'brine_copper', z=40, rl=2.2, rs=3.4, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _copper_sheen(X, Y, t, x0, hy))
    f.add(f.rect(x0 - 8.5, hy + 8.5, x0 + 8.5, hy + 11.5) & f.ell(x0, hy + 9.5, 9, 3), 'brass', z=41, rl=1, rs=1.4, line='hard')
    for x in (-6, -2, 2, 6):
        f.dot(x0 + x, hy + 9, ('brass', 3), z=41)
    f.add(f.ell(x0, hy - 12, 2.6, 1.8), 'brass', z=39.5, rl=1, rs=1.2, line='hard')
    if back:
        return
    for s in (-1, 1):
        f.add(f.ell(x0 + 10.0 * s, hy + 0.5, 2.2, 3.6), 'brass', z=41, rl=1, rs=1.4, line='hard')
        f.add(f.ell(x0 + 10.2 * s, hy + 0.5, 1.0, 2.4), glass, z=41.2, flat=1, line=None)
    f.add(f.ell(x0, hy + 0.5, 6.6, 6.3), 'brass', z=42, rl=1.3, rs=1.8, line='hard')
    gl = f.ell(x0, hy + 0.5, 4.8, 4.5)
    f.add(gl, glass, z=43, rl=1.6, rs=2.2, line='hard', tag='face')        # the faceplate window
    f.detail(f.rect(x0 - 0.5, hy - 4, x0 + 1, hy + 5) & gl, ('brass', 2), z=43)
    f.detail(f.rect(x0 - 4.5, hy + 0, x0 + 5, hy + 1.5) & gl, ('brass', 2), z=43)
    f.dot(x0 - 3, hy - 2, (glass, 4), z=43)
    f.dot(x0 - 2, hy - 3, (glass, 4), z=43)
    f.dot(x0 - 3, hy - 3, (glass, 3), z=43)
    for x, y in ((-5, hy - 5), (4, hy - 5), (-6, hy + 5), (5, hy + 5)):
        f.dot(x0 + x, y, ('brass', 3), z=42)


def helmet_side(f, hx, hy, glass='brine_glass'):
    f.add(f.ell(hx, hy - 0.5, 11.8, 11.6), 'brine_copper', z=40, rl=2.2, rs=3.4, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _copper_sheen(X, Y, t, hx, hy))
    f.add(f.rect(hx - 8.5, hy + 8.5, hx + 8.5, hy + 11.5) & f.ell(hx, hy + 9.5, 9, 3), 'brass', z=41, rl=1, rs=1.4, line='hard')
    for x in (hx - 5, hx - 1, hx + 3):
        f.dot(x, hy + 9, ('brass', 3), z=41)
    f.add(f.ell(hx - 0.5, hy - 12, 2.6, 1.8), 'brass', z=39.5, rl=1, rs=1.2, line='hard')
    f.add(f.ell(hx + 11.3, hy + 0.5, 2.4, 5.6), 'brass', z=42, rl=1.2, rs=1.6, line='hard')
    f.add(f.ell(hx + 12.1, hy + 0.5, 1.0, 4.0), glass, z=42.5, flat=2, line=None)
    f.dot(hx + 12, hy - 2, (glass, 4), z=42.5)
    px, py = hx + 3.5, hy + 0.5
    f.add(f.ell(px, py, 4.6, 4.6), 'brass', z=42, rl=1.3, rs=1.8, line='hard')
    gl = f.ell(px, py, 3.1, 3.1)
    f.add(gl, glass, z=43, rl=1.4, rs=2.0, line='hard', tag='face')
    f.detail(f.rect(px - 0.5, py - 3.5, px + 1, py + 3.5) & gl, ('brass', 2), z=43)
    f.detail(f.rect(px - 3.5, py - 0.5, px + 3.5, py + 1) & gl, ('brass', 2), z=43)
    f.dot(px - 2, py - 2, (glass, 4), z=43)
    for x, y in ((px - 4, py - 4), (px + 3, py - 4), (px - 4, py + 3), (px + 3, py + 3)):
        f.dot(x, y, ('brass', 3), z=42)


def helmet_3q(f, hx, hy, back, glass='brine_glass'):
    """Contract v2: the copper helmet turned three-quarter (SE / NE drawn, SW / NW mirrored): the
    faceplate turned toward the facing, the near side port, the far one at the rim."""
    f.add(f.ell(hx + 0.4, hy - 0.5, 12.2, 11.6), 'brine_copper', z=40, rl=2.2, rs=3.4, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _copper_sheen(X, Y, t, hx, hy))
    f.add(f.rect(hx - 8.5, hy + 8.5, hx + 9.0, hy + 11.5) & f.ell(hx + 0.3, hy + 9.5, 9.2, 3), 'brass', z=41, rl=1, rs=1.4, line='hard')
    for x in (-5, -1, 3, 7):
        f.dot(hx + x, hy + 9, ('brass', 3), z=41)
    f.add(f.ell(hx, hy - 12, 2.6, 1.8), 'brass', z=39.5, rl=1, rs=1.2, line='hard')
    if back:
        f.add(f.ell(hx + 10.6, hy + 0.5, 1.6, 3.4), 'brass', z=41, rl=1, rs=1.4, line='hard')        # the near port at the rim
        return
    f.add(f.ell(hx - 8.8, hy + 0.5, 2.2, 3.6), 'brass', z=41, rl=1, rs=1.4, line='hard')            # near side port
    f.add(f.ell(hx - 9.0, hy + 0.5, 1.0, 2.4), glass, z=41.2, flat=1, line=None)
    f.add(f.ell(hx + 11.4, hy + 0.5, 1.2, 3.2), 'brass', z=41, rl=1, rs=1.2, line='hard')           # far port, edge on
    px, py = hx + 4.0, hy + 0.5
    f.add(f.ell(px, py, 5.8, 6.0), 'brass', z=42, rl=1.3, rs=1.8, line='hard')
    gl = f.ell(px, py, 4.1, 4.3)
    f.add(gl, glass, z=43, rl=1.6, rs=2.2, line='hard', tag='face')
    f.detail(f.rect(px - 0.5, py - 4, px + 1, py + 4.5) & gl, ('brass', 2), z=43)
    f.detail(f.rect(px - 4.5, py - 0.5, px + 4.5, py + 1) & gl, ('brass', 2), z=43)
    f.dot(px - 2.5, py - 2, (glass, 4), z=43)
    f.dot(px - 1.5, py - 3, (glass, 4), z=43)
    for x, y in ((px - 5, py - 4.5), (px + 4, py - 4.5), (px - 5, py + 4.5), (px + 4, py + 4.5)):
        f.dot(x, y, ('brass', 3), z=42)


# ------------------------------------------------------------------------------------ body bits
def corselet(f, cx, cy, rx=13.5):
    f.add(f.ell(cx, cy, rx, 5.6) & (f.Y > cy - 4.5), 'brass', z=36, rl=1.6, rs=2.4, line='hard', cast=(0, 1, 1))
    for x in np.arange(cx - rx + 4, cx + rx - 2, 4.5):
        rivet(f, int(round(x)), int(cy + 2), z=36)


def weight_belt(f, y, x0, x1, buckle_x, weights, z=24):
    f.add(f.rect(x0, y - 4, x1, y), 'brine_olive', z=z, rl=1, rs=1.4, line='soft')
    for wx in weights:
        f.add(f.rect(wx - 2, y - 5, wx + 2, y + 1), 'gunmetal', z=z + 0.5, rl=1, rs=1.4, line='hard')
    if buckle_x is not None:
        f.add(f.rect(buckle_x - 2, y - 5, buckle_x + 2, y + 1), 'brass', z=z + 1, rl=1, rs=1.4, line='hard')
        f.add(f.rect(buckle_x - 0.5, y - 3, buckle_x + 0.5, y - 1), 'brine_olive', z=z + 1.1, flat=0, line=None)


def heavy_boot_front(f, x, y, z, dim=0):
    boot_front(f, x, y, 'brine_rubber', z=z, dim=dim)
    f.add(f.rect(x - 4.6, y - 2, x + 4.6, y) & f.ell(x, y - 2.6, 5.0, 3.4), 'gunmetal', z=z + 0.2, flat=1, dim=dim, line='soft')
    f.add(f.ell(x, y - 3.5, 2.6, 1.6), 'brass', z=z + 0.3, rl=1, rs=1.2, dim=dim, line='hard')


def heavy_boot_back(f, x, y, z, dim=0):
    boot_front(f, x, y, 'brine_rubber', z=z, dim=dim)
    f.add(f.rect(x - 4.6, y - 2, x + 4.6, y) & f.ell(x, y - 2.6, 5.0, 3.4), 'gunmetal', z=z + 0.2, flat=1, dim=dim, line='soft')
    f.add(f.rect(x - 4.6, y - 5, x + 4.6, y - 3), 'brine_rubber', z=z + 0.25, flat=1, dim=dim, line='soft')


def heavy_boot_side(f, x, y, z, dim=0):
    boot_side(f, x, y, 'brine_rubber', z=z, dim=dim, toe=2.0)
    f.add(f.rect(x - 3.4, y - 2, x + 7.2, y) & f.ell(x + 2.0, y - 2.6, 5.6, 3.6), 'gunmetal', z=z + 0.2, flat=1, dim=dim, line='soft')
    f.add(f.ell(x + 4.6, y - 3.6, 1.8, 1.6), 'brass', z=z + 0.3, rl=1, rs=1.2, dim=dim, line='hard')


def glove(f, x, y, z, dim=0, r=3.2):
    f.add(f.ell(x, y, r, r), 'brine_rubber', z=z, rl=1.4, rs=2.0, dim=dim, line='hard')


def _chest_seam(X, Y, t, x0, y0, y1):
    out = t.copy()
    out[(abs(X - x0) < 0.6) & (Y > y0) & (Y < y1) & (t >= 2)] = 1
    return out


# ------------------------------------------------------------------------------------ build
def build(f, facing, P):
    R = Rig(f, facing)
    side = R.side
    b, cr, lean = P['bob'], P['crouch'], P['lean']
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 20.0 + P['breath'], 0.0)
    head3 = (sh3[0] + lean * 0.3, sh3[1] + 16.0, 0.0)
    off = (P['hipx'], -cr - b, 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    glass = 'brine_glow' if P['press'] > 0.5 else 'brine_glass'
    # ---------------------------------------------------------------- gun and hands
    grip3 = add3(P['grip'] or GRIP0, (off[0] + 0.8 * lean, off[1], 0.0))      # the gun follows the lean
    aim = P['aim'] or AIM0
    D, Dn, Rt = gun_frame(aim)
    if P['recoil']:
        grip3 = add3(grip3, tuple(-D * P['recoil']))
    if P['gun'] == 'left':                 # the left hand alone holds it by the fore grip
        grip3 = tuple(np.array(add3(P['handL'], off)) - D * 10.7)
    mid3 = tuple(np.array(grip3) + D * 6)
    gz = zdepth(R, mid3, 31.0, 5.0, -4.5)
    if not R.back and gz > 15 and np.array(grip3)[1] + np.array(nrm(aim))[1] * 14.0 > 47.0:
        gz = 46.0                          # v2: aimed up on the near side, the gun is in front of the helmet
    if P['gun'] == 'hand':
        hR = grip3
    else:
        hR = add3(P['handR'], off)
    # left hand: fore grip, reel crank, or free
    tmp = Fig(8, 8)                        # dry run for the gun's key points
    k3 = harpoon_gun(tmp, Rig(tmp, facing), grip3, aim, gz, P['loaded'])
    if P['lmode'] == 'fore':
        hL = tuple(np.array(k3['fore3']) + Dn * 1.0)
    elif P['lmode'] == 'reel':
        a = P['crank'] * 2 * math.pi
        hL = tuple(np.array(k3['handle3']) + (Dn * math.cos(a) - D * math.sin(a)) * 2.0 + Rt * 1.5)
    else:
        hL = add3(P['handL'], off)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    # ---------------------------------------------------------------- pack, hose, regulator
    packc = add3(sh3, (-11.0, -3.0, 0.0))
    valve3 = add3(sh3, (-10.0, 4.5, 7.5))
    reg3 = add3(head3, (-6.0, -4.5, 11.0))
    pcx, pcy = R.p(packc)
    vx, vy = R.p(valve3)
    pz = 28.0 if R.back else 1.0
    with f.tagging('pack'):
        if side or (R.diag and not R.back):
            pk = f.rect(pcx - 5.5, pcy - 11, pcx + 5.5, pcy + 11) & f.ell(pcx, pcy, 7.5, 14)
        else:
            pk = f.rect(pcx - 8.5, pcy - 12, pcx + 8.5, pcy + 11) & f.ell(pcx, pcy, 10.5, 14.5)
        f.add(pk, 'brine_olive', z=pz, rl=1.8, rs=3.0, vgrad=0.3, line='hard', cast=(1, 1, 1) if R.back else None,
              tonemap=(lambda X, Y, t: _chest_seam(X, Y, t, pcx, pcy - 11, pcy + 10)) if R.back else None)
        for dy in (-5, 5):
            f.add(f.rect(pcx - 9, pcy + dy, pcx + 9, pcy + dy + 2) & pk, 'brass', z=pz + 0.5, rl=1, rs=1.2, line='soft')
        f.add(f.ell(vx, vy, 2.2, 1.7), 'brass', z=pz + 1, rl=1, rs=1, line='hard')
        if R.back and P['press'] > 0.2:     # pack gauge
            f.add(f.ell(pcx - 4, pcy - 8, 1.8, 1.8), 'string', z=pz + 1.2, flat=2, line='hard')
            f.dot(pcx - 4, pcy - 8, ('rifle', 0), z=pz + 1.2)
    # the one hose: valve -> out to his right and up -> into the regulator
    c1 = add3(valve3, (-7.0 - P['lag'], -1.0, 19.0))
    c2 = add3(reg3, (-9.0 - P['lag'], 9.0, 9.0))
    pts = [R.p(valve3), R.p(c1), R.p(c2), R.p(reg3)]
    hzz = 29.5 if R.back else (3.0 if facing == 'S' else 3.5)
    west = facing in ('W', 'SW', 'NW')                   # his right side (hose, regulator) is the far one
    hose(f, pts, z=hzz, dim=1 if west else 0)
    rgx, rgy = R.p(reg3)
    if not west:
        rz = 39.0 if facing == 'S' else 41.5
        hx_, hy_ = R.p(hR)
        if math.hypot(hx_ - rgx, hy_ - rgy) < 12.0:      # the glove turns the valve from behind its knob
            rz = 46.6
        f.add(f.ell(rgx, rgy, 2.3, 2.7), 'brass', z=rz, rl=1, rs=1.3, line='hard', tag='regulator')
        f.dot(rgx - 1, rgy - 1, ('brass', 4), z=rz, tag='regulator')
    # ---------------------------------------------------------------- legs
    for lat, key in ((P['stance'], 'footR'), (-P['stance'], 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.5, lat)
        hp3 = add3(hip3, (0.0, 0.0, lat * 0.95))
        up, lo, kn3 = R.limb(hp3, ank3, 8.2, 8.0, 4.8, 4.3, 4.1, (1.0, 0.0, 0.1 * np.sign(lat)))
        far = R.far(lat)
        dim = 1 if far else 0
        z = 10 + 0.1 * R.d(foot3)
        f.add(up | lo, 'brine_canvas', z=z, rl=1.8, rs=2.8, vgrad=0.3, dim=dim, line='hard')
        kx, ky = R.p(add3(kn3, (1.2, 0, 0)))
        f.add(f.ell(kx, ky, 3.2 if not side else 2.6, 3.0), 'brine_olive', z=z + 0.2, rl=1, rs=1.6, dim=dim, line='hard')
        fx, fy = R.p(foot3)
        ax_, ay_ = R.p(ank3)
        f.add(f.cap(ax_, ay_ - 1.5, ax_, ay_ + 0.5, 4.6 if not side else 4.4) & (f.Y > ay_ - 2.5), 'brine_olive', z=z + 0.3,
              flat=1, dim=dim, line='soft')
        if R.diag:                                  # contract v2: the three-quarter boot
            surf.boot_3q(f, R, foot3, 'brine_rubber', z + 1, dim=dim, cuff=False)
        elif side:
            heavy_boot_side(f, fx, fy, z + 1, dim=dim)
        elif facing == 'S':
            heavy_boot_front(f, fx, fy, z + 1)
        else:
            heavy_boot_back(f, fx, fy, z + 1)
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    vf = ('N' if R.back else 'S') if R.diag else facing      # turn in-betweens: the S or N body turned
    tw_ = turn.Warp(f, R, (sx + hx) / 2, 12.0, 9.0, vf) if R.diag else None
    if tw_:
        tw_.__enter__()
    if side:
        f.add(f.ell(hx + 0.5, hy - 1.0, 9.0, 4.4), 'brine_canvas', z=19, rl=2, rs=3, line='hard')
    else:
        f.add(f.rect(hx - 10.5, hy - 6, hx + 10.5, hy + 1.5) | f.ell(hx, hy, 10.5, 4.2), 'brine_canvas', z=13, rl=2, rs=3.4,
              vgrad=0.4, line='hard')
    # ---------------------------------------------------------------- torso
    if side:
        body = f.ell(sx + 0.5, sy + 7, 9.5, 11.5) | f.poly([(hx - 8.5, hy - 2), (sx - 8.5, sy + 2), (sx + 9.5, sy + 2), (hx + 10, hy - 2)])
        body &= f.Y < hy - 1.5
        f.add(body, 'brine_canvas', z=20, rl=2, rs=4, vgrad=0.4, line='hard')
        strap = f.poly([(sx - 7.5, sy - 3), (sx - 4.5, sy - 3), (hx - 5, hy - 7), (hx - 8, hy - 7)])
        f.add(strap, 'brine_olive', z=22, rl=1, rs=1.4, line='soft')
        weight_belt(f, hy - 3, hx - 9, hx + 10.5, hx + 8.5, (hx - 5.5, hx + 2.0))
        corselet(f, sx + 0.5, sy - 5, rx=11.5)
    else:
        body = f.ell(sx, sy + 6, 12.0, 12) | f.poly([(sx - 11, sy + 2), (sx + 11, sy + 2), (hx + 11, hy - 3), (hx - 11, hy - 3)])
        body &= f.Y < hy - 1.5
        f.add(body, 'brine_canvas', z=20, rl=2, rs=4, vgrad=0.4, line='hard',
              tonemap=(lambda X, Y, t: _chest_seam(X, Y, t, (sx + hx) / 2, sy, hy - 4)) if vf == 'S' else None)
        if vf == 'S':
            for s in (-1, 1):
                f.add(f.poly([(sx + 6 * s, sy - 3), (sx + 9.5 * s, sy - 3), (hx + 8.0 * s, hy - 7), (hx + 5.0 * s, hy - 7)]),
                      'brine_olive', z=22, rl=1, rs=1.4, line='soft')
            weight_belt(f, hy - 3, hx - 11.5, hx + 11.5, hx, (hx - 7.5, hx + 7.5))
        else:
            weight_belt(f, hy - 3, hx - 11.5, hx + 11.5, None, (hx - 8, hx + 8))
        corselet(f, sx, sy - 5)
    if tw_:
        tw_.__exit__(None, None, None)
    # ---------------------------------------------------------------- arms, gun, gloves
    arms = []
    sRj, sLj, _ = shoulders(sh3, hR, hL, SHW, sum(ARM), P['twist'])
    for key, hh, lat, shp in (('R', hR, 1, sRj), ('L', hL, -1, sLj)):
        pole = P['pole' + key] or (-0.6, -1.0, 0.5 * lat)
        up, lo, el3 = R.limb(shp, hh, ARM[0], ARM[1], 3.8, 3.4, 3.0, pole)
        far = R.far(lat)
        zu = zdepth(R, el3, 29.0, 5.0)
        zl = zdepth(R, hh, 30.0, 5.5)
        if far and hh[1] < 50:
            zu, zl = 4.5, 5.0
        arms.append((key, shp, hh, lat, up, lo, el3, far, zu, zl))
    if P['gun'] == 'hand':
        k = harpoon_gun(f, R, grip3, aim, gz, P['loaded'])
    else:
        k = harpoon_gun(f, R, grip3, aim, gz, P['loaded'])
    f.anchor('muzzle', *k['muzzle'])
    if P['loaded']:
        f.anchor('harpoon_tip', *k['tip'])
    for key, shp, hh, lat, up, lo, el3, far, zu, zl in arms:
        dim = 1 if far else 0
        f.add(up, 'brine_canvas', z=zu, rl=1.6, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1) if not far else None)
        f.add(lo, 'brine_canvas', z=zl, rl=1.6, rs=2.4, dim=dim, line='hard', cast=(1, 1, 1) if not far else None)
        ex, ey = R.p(el3)
        f.add(f.ell(ex, ey, 2.4, 2.4) & (up | lo), 'brine_olive', z=max(zu, zl) + 0.05, rl=1, rs=1.4, dim=dim, line='soft')
        hx2, hy2 = R.p(hh)
        dx, dy = hx2 - ex, hy2 - ey
        d = math.hypot(dx, dy) or 1
        cx, cy = hx2 - dx / d * 2.4, hy2 - dy / d * 2.4
        f.add(f.cap(cx - dx / d, cy - dy / d, cx + dx / d * 0.6, cy + dy / d * 0.6, 3.2), 'brine_olive', z=zl + 0.06,
              rl=1, rs=1.4, dim=dim, line='soft')
        holds = (key == 'R' and P['gun'] == 'hand') or (key == 'L' and P['lmode'] in ('fore', 'reel'))
        gzl = max(zl, gz + 0.6) if holds and zl > 15 else zl + 0.1
        glove(f, hx2, hy2, gzl, dim=dim)
        spx, spy = R.p(shp)
        f.add(f.ell(spx, spy - 0.5, 4.4, 4.0) & (f.Y < spy + 1.5), 'brine_olive', z=31.5 if not far else 5.2, rl=1.2, rs=1.8,
              line='soft', dim=dim)
    # ---------------------------------------------------------------- helmet
    hx3, hy3 = R.p(head3)
    with f.tagging('helmet'):
        if R.diag:
            helmet_3q(f, hx3, hy3, R.back, glass=glass)
        elif facing == 'S':
            helmet_front(f, hx3, hy3, glass=glass)
        elif facing == 'N':
            helmet_front(f, hx3, hy3, back=True)
        else:
            helmet_side(f, hx3 + 1.5, hy3, glass=glass)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')))
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f
