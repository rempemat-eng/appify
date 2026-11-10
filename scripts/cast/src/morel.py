"""Morel: older, clean-shaven human alchemist.  Receding grey hair (bald crown, side tufts),
rolled cream sleeves, an ochre bib apron split from the belt down, grey-brown trousers and
brown boots.  Gear, each exactly once:
  - one fitted mask (dark rubber, blue lenses, brass filter): carried on the chest from a strap
    round the neck; the special moves the same mask to the face (strap round the head) and the
    exit moves it back;
  - one blue reagent flask held by the neck in the RIGHT hand (the throwing hand) in every
    facing; after a throw the right hand draws the next flask from the closed reagent case on
    the RIGHT hip (nothing inside shows, so only one flask is ever in sight);
  - two belt vials (blue, amber) in loops at the front of the belt;
  - the catalyst apparatus (brass chamber, glass bulb, copper coil) clipped at the LEFT hip; the
    secondary lifts it on its strap with the LEFT hand and flares the bulb.
About 73 px tall.

Pass 2: one pose-driven build for all four facings on parts.Rig (as bramble.py).  The torso and
head art of pass 1 is reused through Shift(), which moves the Fig origin to the projected hip or
head, so each view's drawing follows the pose.  The rig helpers at the top (Shift, legs, arm
segments, hands) are shared by velvet.py, tam.py and mirra.py.

Equipment tags: flask, mask, catalyst, case."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, boot_side, boot_front, EYE, Rig
import palette  # noqa: F401
import anim
import turn
import surf

ID = 'morel'
NAME = 'Morel'
HEIGHT = 73
SCALE = 1.05                    # 26 Oct scale audit: his stoop measured 69 px (adults 70 to 78); drawn 5 % larger, proportions unchanged
BAND = (68, 79)

mat('apron',   ['#4A1A16', '#7A2C22', '#A8452E', '#D0704A'])
mat('rubber',  ['#16161C', '#26262E', '#3A3A44', '#56566A'])
mat('lens',    ['#0E2E5A', '#1A5AA0', '#3A96E0', '#9AD8FA', '#F0FCFF'])
mat('reagent', ['#0E2E5A', '#1A5AA0', '#3A8ED8', '#8CD0F4', '#EAF8FF'])
mat('amberliq', ['#6A3A0E', '#A86A18', '#E0A030', '#F6D670', '#FFF6D0'])
mat('glass',   ['#5E7A86', '#8EAAB4', '#C6DCE0', '#EEF8F8', '#FFFFFF'])
mat('copper',  ['#4A1E12', '#7E3A1E', '#B8622E', '#E8945A', '#FFD0A0'])
mat('cork',    ['#4E3424', '#7A5438', '#A47A52', '#C8A27A'])
mat('greyhair', ['#3A3644', '#5E5A68', '#8A8690', '#BAB6B6'])


# ================================================================== rig helpers (designer 1 kit)
class Shift:
    """with Shift(f, dx, dy): moves the Fig origin so pass-1 art drawn round x = 0 lands at the
    projected point (dx, dy) of this pose.  Works on flipped (west) figures.  Anchors must not be
    recorded inside."""

    def __init__(self, f, dx, dy=0.0):
        self.f, self.dx, self.dy = f, dx, dy

    def __enter__(self):
        f = self.f
        self.prev = (f.gx, f.gy, f.X, f.Y)
        sx = -1 if f.flip else 1
        f.gx = f.gx + sx * self.dx
        f.gy = f.gy + self.dy
        f.X = f.X - self.dx
        f.Y = f.Y - self.dy
        return f

    def __exit__(self, *a):
        self.f.gx, self.f.gy, self.f.X, self.f.Y = self.prev


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def sub3(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def mul3(a, k):
    return tuple(x * k for x in a)


def nrm(v):
    v = np.array(v, float)
    return tuple(v / (np.linalg.norm(v) or 1.0))


def sdir(R, p3, d3, k=1.0):
    """Screen direction (unit, and projected length per unit) of a body-space direction at p3."""
    a = R.p(p3)
    b = R.p(add3(p3, mul3(nrm(d3), k)))
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dx / L, dy / L) if L > 1e-6 else (0.0, 1.0), L / k


def frame(P, HIP=22.0, SH=20.0, HEAD=16.0):
    """Hip, shoulder and head centres in body space for a pose (as bramble.build)."""
    b, cr, lean = P['bob'], P['crouch'], P['lean']
    hip3 = (P['hipx'], HIP - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + SH + P['breath'] - max(0.0, cr * 0.15), 0.0)
    head3 = (sh3[0] + lean * 0.35, sh3[1] + HEAD, 0.0)
    return hip3, sh3, head3


def legs(f, R, P, hip3, draw_leg, l1=8.7, l2=8.5):
    """Both legs from the pose's feet: draw_leg(f, R, up, lo, knee3, foot3, lat, far, z) draws
    trousers and boots.  The far leg first.  Records foot anchors."""
    stance = P['stance']
    order = sorted(((stance, 'footR'), (-stance, 'footL')), key=lambda t: R.d((0, 0, t[0])))
    for lat, key in order:
        ft = P[key]
        foot3 = (ft[0], ft[1], ft[2] if len(ft) > 2 else lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.5, foot3[2])
        hp3 = add3(hip3, (0.0, 0.0, lat * 0.85))
        up, lo, kn3 = R.limb(hp3, ank3, l1, l2, 4.6, 4.2, 3.8, (1.0, 0.0, 0.12 * np.sign(lat)))
        far = R.far(lat)
        z = R.zleg(foot3)
        draw_leg(f, R, up, lo, kn3, foot3, lat, far, z)
        fx, fy = R.p(foot3)
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)


def boot(f, R, foot3, mat_, z, far, shaft=0):
    """Boot at foot3: side boot in E/W (toe forward), front boot in S/N.  shaft: extra height
    of a tall boot shaft (px)."""
    fx, fy = R.p(foot3)
    dim = 1 if far else 0
    if R.diag:                                   # contract v2: the three-quarter boot (turn in-betweens)
        surf.boot_3q(f, R, foot3, mat_, z + 1, dim=dim, cuff=False)
        return fx, fy
    if R.side:
        boot_side(f, fx, fy, mat_, z=z + 1, dim=dim)
        if shaft:
            f.add(f.rect(fx - 3.6, fy - 7 - shaft, fx + 2.8, fy - 6), mat_, z=z + 1.1, rl=1.4, rs=2.2, dim=dim, line='hard')
            f.add(f.rect(fx - 4.0, fy - 7.5 - shaft, fx + 3.2, fy - 5.5 - shaft), mat_, z=z + 1.2, flat=3 if not dim else 2, line='hard')
    else:
        boot_front(f, fx, fy, mat_, z=z + 1, dim=dim)
        if shaft:
            f.add(f.rect(fx - 3.8, fy - 7 - shaft, fx + 3.8, fy - 6) | f.ell(fx, fy - 7 - shaft, 3.8, 1.6), mat_, z=z + 1.1,
                  rl=1.4, rs=2.2, line='hard')
            f.add(f.rect(fx - 4.2, fy - 7.5 - shaft, fx + 4.2, fy - 5.5 - shaft), mat_, z=z + 1.2, flat=3, line='hard')
    return fx, fy


def arm_z(R, P, key, h3):
    """An arm's depth.  A pose's zR/zL override is a hint for S, E and W; N always uses the
    rig's depth, so a hand reaching across the chest is never painted over the back."""
    if P.get('z' + key) is not None and not R.back:
        return P['z' + key]
    return R.zarm(h3)


def up_z(R, z, far):
    """The far upper arm in profile stays behind the torso; only the forearm comes round in
    front of the chest when the hand does."""
    return min(z, 6.0) if (R.side and far) else z


def reach(sh3, h3, L, k=0.98):
    """Keep a hand within the arm's reach (k of full length), so no limb ever stretches."""
    v = np.subtract(h3, sh3)
    d = float(np.linalg.norm(v))
    if d <= L * k:
        return h3
    return tuple(np.add(sh3, v * (L * k / d)))


def fist(f, x, y, z, skin, dim=0, grip=None, r=3.1):
    """Closed hand.  grip: screen direction of the held neck or handle; a deep-tone finger
    crease is drawn across it so the hand reads as closed round it."""
    f.add(f.ell(x, y, r, r * 0.97), skin, z=z, rl=1.4, rs=2.0, line='hard', dim=dim)
    if grip is not None:
        ux, uy = grip
        L = math.hypot(ux, uy) or 1
        ux, uy = ux / L, uy / L
        f.detail(f.seg(x - uy * 1.5 + ux * 0.7, y + ux * 1.5 + uy * 0.7, x + uy * 1.5 + ux * 0.7, y - ux * 1.5 + uy * 0.7),
                 (skin, 0), z=z + 0.01)


def open_hand(f, R, w3, fing3, z, skin, dim=0, thumb3=None, wrap=None, size=1.0):
    """Open hand from the wrist w3: palm and fingers together along fing3 (body space), the
    thumb apart toward thumb3.  Seen edge-on the palm narrows (the hand turned in profile).
    wrap: a material for a cloth wrap round the palm below the fingers (Tam)."""
    wx, wy = R.p(w3)
    (ux, uy), Lp = sdir(R, w3, fing3)
    L = (2.2 + 3.4 * min(1.0, Lp)) * size
    tip = (wx + ux * L, wy + uy * L)
    palm = f.cap(wx + ux * 0.6, wy + uy * 0.6, tip[0], tip[1], 2.5 * size, 2.0 * size)
    if thumb3 is not None:
        (tx, ty), tl = sdir(R, w3, thumb3)
        if tl > 0.25:
            bx, by = wx + ux * 1.6, wy + uy * 1.6
            th = f.cap(bx, by, bx + tx * 2.6 * size + ux * 1.2, by + ty * 2.6 * size + uy * 1.2, 1.2 * size)
            f.add(th, skin, z=z - 0.01, rl=1, rs=1.2, line='hard', dim=dim)
    f.add(palm, skin, z=z, rl=1.4, rs=1.8, line='hard', dim=dim)
    if wrap:
        f.add(palm & f.cap(wx, wy, wx + ux * L * 0.5, wy + uy * L * 0.5, 3.0), wrap, z=z + 0.01, rl=1, rs=1.4, line=None, dim=dim)
    # one finger seam along the fingers
    f.detail(f.seg(wx + ux * L * 0.62, wy + uy * L * 0.62, tip[0] - ux * 0.6, tip[1] - uy * 0.6), (skin, 1), solid=False, z=z + 0.02)
    return tip


# ================================================================================ gear
def flask(f, R, g3, d3, z, dim=0):
    """Round-bottomed reagent flask held by the neck at g3; d3 points from the neck to the body
    (down when it hangs from the fist).  The cork shows past the fist on the other side."""
    (ux, uy), Lp = sdir(R, g3, d3)
    gx, gy = R.p(g3)
    s = max(0.45, Lp)
    cx, cy = gx + ux * (-3.6 * s), gy + uy * (-3.6 * s)
    f.add(f.cap(cx, cy, gx - ux * 2.4 * s, gy - uy * 2.4 * s, 1.2), 'cork', z=z, rl=1, rs=1, line='hard', dim=dim, tag='flask')
    f.add(f.cap(gx - ux * 2.4 * s, gy - uy * 2.4 * s, gx + ux * 3.5 * s, gy + uy * 3.5 * s, 1.4), 'glass', z=z, rl=1, rs=1.2,
          line='hard', dim=dim, tag='flask')
    bx, by = gx + ux * 7.0 * s, gy + uy * 7.0 * s
    body = f.ell(bx, by, 4.2, 4.0)
    f.add(body, 'glass', z=z + 0.01, rl=1.3, rs=1.8, line='hard', dim=dim, tag='flask')
    f.add(body & (f.Y > by - 1.0 + (1.5 if uy < -0.5 else 0)), 'reagent', z=z + 0.02, rl=1.2, rs=1.8, line=None, dim=dim, tag='flask')
    f.dot(bx - 2, by - 2, ('glass', 4), solid=False, z=z + 0.03, tag='flask')
    f.dot(bx - 1, by - 3, ('glass', 4), solid=False, z=z + 0.03, tag='flask')
    return bx, by


def vial(f, x, y, liq, z):
    """A small belt vial in a leather loop: cork, glass, liquid."""
    f.add(f.rect(x - 1, y - 6, x + 1, y - 4.5), 'cork', z=z, flat=2, line='hard')
    f.add(f.rect(x - 1.6, y - 4.5, x + 1.6, y + 1.5) | f.ell(x, y + 1.5, 1.6, 1.2), 'glass', z=z, rl=1, rs=1, line='hard')
    f.add(f.rect(x - 1.6, y - 2, x + 1.6, y + 2) & (f.rect(x - 1.6, y - 4.5, x + 1.6, y + 1.5) | f.ell(x, y + 1.5, 1.6, 1.2)),
          liq, z=z + 0.01, rl=1, rs=1.2, line=None)
    f.add(f.rect(x - 2.2, y - 3, x + 2.2, y - 1.5), 'leather', z=z + 0.02, flat=1, line='soft')
    f.dot(x - 1, y - 4, ('glass', 4), solid=False, z=z + 0.03)


def case(f, R, p3, z, dim=0):
    """Reagent case on the right hip: a closed, stiff leather box with a lid flap and a brass
    clasp.  The next flask comes out of it after a throw; nothing inside shows, so the held
    flask is the only flask in sight."""
    x, y = R.p(p3)
    w = 2.6 if R.side else 3.0
    with f.tagging('case'):
        f.add(f.rect(x - w, y - 2.5, x + w, y + 6) | f.ell(x, y + 6, w, 1.2), 'leather', z=z, rl=1.2, rs=1.8, line='hard', dim=dim,
              cast=(1, 1, 1) if not dim else None)
        f.add(f.rect(x - w, y - 2.5, x + w, y + 0.5) | f.ell(x, y + 0.5, w, 1.0), 'leather', z=z + 0.01, flat=1, line='soft', dim=dim)
        f.add(f.rect(x - 0.8, y + 0.5, x + 0.8, y + 2), 'brass', z=z + 0.02, flat=2, line=None, dim=dim)


def catalyst(f, R, clip3, top3, base3, z, dim=0, glow=0):
    """Catalyst apparatus: brass chamber from base3 to top3 wound with a copper coil, the glass
    bulb on top glowing amber (glow 0 faint, 1 lit, 2 flare), a strap from the belt clip clip3
    to the chamber base.  At rest the chamber hangs from the clip."""
    with f.tagging('catalyst'):
        cx, cy = R.p(clip3)
        tx, ty = R.p(top3)
        bx, by = R.p(base3)
        f.add(f.rect(cx - 1.2, cy - 1, cx + 1.2, cy + 2), 'leather', z=z - 0.02, flat=1, line='hard', dim=dim)
        if math.hypot(bx - cx, by - cy) > 3.0:
            f.add(f.seg(cx, cy + 1, bx, by), 'leather', z=z - 0.03, flat=1, line=None, clean=False, dim=dim)
        L = math.hypot(tx - bx, ty - by) or 1
        ux, uy = (tx - bx) / L, (ty - by) / L
        ch = f.cap(bx, by, tx - ux * 1.5, ty - uy * 1.5, 2.8, 2.6)
        f.add(ch, 'brass', z=z, rl=1.2, rs=1.8, line='hard', dim=dim)
        for k in (0.35, 0.62):
            px, py = bx + (tx - bx) * k, by + (ty - by) * k
            f.add(f.cap(px - uy * 3.2, py + ux * 3.2, px + uy * 3.2, py - ux * 3.2, 0.7) & f.cap(bx, by, tx, ty, 3.3), 'copper',
                  z=z + 0.02, flat=2 if not dim else 1, line=None, dim=dim)
        bulb = f.ell(tx, ty, 2.2, 2.0)
        if glow >= 2:
            f.add(bulb, 'amberliq', z=z + 0.03, rl=0.8, rs=0.8, line='hard', dim=dim)
            f.dot(tx - 0.5, ty - 0.5, ('amberliq', 4), z=z + 0.04)
            f.dot(tx + 0.5, ty - 0.5, ('amberliq', 4), z=z + 0.04)
        else:
            f.add(bulb, 'glass', z=z + 0.03, rl=1, rs=1, line='hard', dim=dim)
            f.dot(tx, ty, ('amberliq', 3 if glow else 2), solid=False, z=z + 0.04)
        f.dot(bx - uy * 2 - ux, by + ux * 2 - uy, ('brass', 4), solid=False, z=z + 0.05)


def mask_front(f, cx, cy, z):
    """The fitted mask seen face-on (hanging on the chest or held): rubber shell, two blue
    lenses in brass rims, a brass filter can below."""
    with f.tagging('mask'):
        shell = f.ell(cx, cy, 5.2, 3.6)
        f.add(shell, 'rubber', z=z, rl=1.4, rs=2.0, line='hard', cast=(0, 1, 1))
        for s in (-1, 1):
            f.add(f.ell(cx + 2.5 * s, cy - 0.4, 1.9, 1.9), 'brass', z=z + 0.01, flat=2, line=None)
            f.add(f.ell(cx + 2.5 * s, cy - 0.4, 1.1, 1.1) | f.rect(cx + 2.5 * s - 1, cy - 1.4, cx + 2.5 * s + 1, cy + 0.6),
                  'lens', z=z + 0.02, flat=2, line=None)
            f.dot(cx + 2.5 * s - 1, cy - 1.4, ('lens', 4), solid=False, z=z + 0.03)
        can = f.rect(cx - 2, cy + 2.2, cx + 2, cy + 5.6) | f.ell(cx, cy + 5.6, 2, 0.9)
        f.add(can, 'brass', z=z + 0.03, rl=1, rs=1.4, line='hard')
        f.detail(f.rect(cx - 2, cy + 3.6, cx + 2, cy + 4.4), ('brass', 0), z=z + 0.04)


def mask_side(f, cx, cy, z, dim=0):
    """The mask in profile: shell, one lens, filter pointing down-forward."""
    with f.tagging('mask'):
        f.add(f.ell(cx, cy, 3.0, 3.6), 'rubber', z=z, rl=1.3, rs=1.8, line='hard', cast=(0, 1, 1), dim=dim)
        f.add(f.ell(cx + 1.0, cy - 0.6, 1.6, 1.6), 'brass', z=z + 0.01, flat=2, line=None, dim=dim)
        f.add(f.ell(cx + 1.0, cy - 0.6, 0.9, 0.9) | f.rect(cx + 0.5, cy - 1.4, cx + 1.8, cy + 0.4), 'lens', z=z + 0.02, flat=2, line=None, dim=dim)
        f.dot(cx + 0.5, cy - 1.5, ('lens', 4), solid=False, z=z + 0.03)
        f.add(f.cap(cx + 1.5, cy + 3.0, cx + 2.8, cy + 5.5, 1.8), 'brass', z=z + 0.03, rl=1, rs=1.3, line='hard', dim=dim)


def mask_back(f, cx, cy, z):
    """The mask held up with its back (inner rim) toward the camera: a rubber oval with the
    darker inside and the strap ends."""
    with f.tagging('mask'):
        f.add(f.ell(cx, cy, 5.0, 3.6), 'rubber', z=z, rl=1.0, rs=2.4, line='hard')
        f.add(f.ell(cx, cy + 0.3, 3.4, 2.2), 'rubber', z=z + 0.01, flat=0, line=None)


def mask_worn_south(f, hy):
    """The mask on the face: lenses over the eyes, the shell over nose and mouth, the filter
    under the chin, the strap round the head above the ears."""
    with f.tagging('mask'):
        f.add(f.rect(-8.6, hy - 1.5, 8.6, hy + 0.3), 'rubber', z=44.5, flat=1, line='hard')
        shell = f.ell(0, hy + 3.6, 6.4, 5.6) | f.ell(0, hy + 0.2, 7.0, 3.0)
        f.add(shell, 'rubber', z=46, rl=1.4, rs=2.2, line='hard', cast=(0, 1, 1))
        for s in (-1, 1):
            x = 3.4 * s
            f.add(f.ell(x, hy + 0.4, 2.4, 2.4), 'brass', z=46.1, flat=2, line=None)
            f.add(f.ell(x, hy + 0.4, 1.5, 1.5), 'lens', z=46.2, flat=2, line=None)
            f.dot(x - 1, hy - 0.6, ('lens', 4), solid=False, z=46.3)
        can = f.rect(-2.4, hy + 6.5, 2.4, hy + 10) | f.ell(0, hy + 10, 2.4, 1.0)
        f.add(can, 'brass', z=46.3, rl=1, rs=1.4, line='hard')
        f.detail(f.rect(-2, hy + 8, 2, hy + 8.8), ('brass', 0), z=46.4)


def mask_worn_side(f, hy, hx):
    with f.tagging('mask'):
        f.add(f.cap(hx - 6.0, hy - 1.5, hx + 4.0, hy + 0.5, 0.9), 'rubber', z=45.6, flat=1, line='hard')
        f.add(f.ell(hx + 6.4, hy + 3.4, 3.8, 5.6) | f.ell(hx + 5.0, hy + 0.5, 3.6, 2.8), 'rubber', z=46, rl=1.3, rs=2.0, line='hard',
              cast=(0, 1, 1))
        f.add(f.ell(hx + 7.0, hy + 0.2, 2.2, 2.2), 'brass', z=46.1, flat=2, line=None)
        f.add(f.ell(hx + 7.4, hy + 0.2, 1.2, 1.4), 'lens', z=46.2, flat=2, line=None)
        f.dot(hx + 6.5, hy - 0.8, ('lens', 4), solid=False, z=46.3)
        f.add(f.cap(hx + 8.0, hy + 7.0, hx + 10.0, hy + 9.5, 2.0), 'brass', z=46.3, rl=1, rs=1.3, line='hard')


def mask_worn_north(f, hy):
    """From behind only the strap round the back of the head shows (and the shell's edges)."""
    with f.tagging('mask'):
        f.add(f.rect(-8.8, hy - 1.5, 8.8, hy + 0.3), 'rubber', z=45.5, flat=1, line='hard')
        for s in (-1, 1):
            f.add(f.ell(8.8 * s, hy + 3.0, 1.4, 3.0), 'rubber', z=38.5, rl=1, rs=1, line='hard')


# ================================================================================ head
def head_south(f, P, hy):
    f.add(f.ell(-9.0, hy + 1.5, 2.2, 3.0) | f.ell(9.0, hy + 1.5, 2.2, 3.0), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 0.5, 8.6, 9.6), 'skin', z=40, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _crown_shine(X, Y, t, 0, hy))
    tufts = (f.ell(-8.4, hy - 2.5, 3.0, 5.2) | f.ell(-9.2, hy + 1, 2.4, 3.6) |
             f.ell(8.4, hy - 2.5, 3.0, 5.2) | f.ell(9.2, hy + 1, 2.4, 3.6))
    tufts &= ~f.ell(0, hy - 0.5, 6.6, 9.0)
    f.add(tufts, 'greyhair', z=44, rl=1.3, rs=2.0, line='hard', cast=(1, 1, 1),
          tonemap=lambda X, Y, t: _tuft_strands(X, Y, t, hy))
    ey = hy - 0.5
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    if P['mask'] == 'face':
        mask_worn_south(f, hy)
        f.detail(f.rect(-6, ey - 3 + lift, -2, ey - 1 + lift), ('greyhair', 1))
        f.detail(f.rect(2, ey - 3 + lift, 6, ey - 1 + lift), ('greyhair', 1))
        return
    if P['face'] == 'shut' or P['blink']:
        f.detail(f.rect(-5, ey + 2, -3, ey + 3), EYE)
        f.detail(f.rect(3, ey + 2, 5, ey + 3), EYE)
    else:
        eye(f, -5, ey, 3)
        eye(f, 3, ey, 3)
    f.detail(f.rect(-6, ey - 3 + lift, -2, ey - 1 + lift) & ~f.rect(-3, ey - 3 + lift, -2, ey - 2 + lift), ('greyhair', 1))
    f.detail(f.rect(2, ey - 3 + lift, 6, ey - 1 + lift) & ~f.rect(2, ey - 3 + lift, 3, ey - 2 + lift), ('greyhair', 1))
    f.detail(f.rect(-2, hy - 6, 2, hy - 5), ('skin', 1))
    f.detail(f.rect(-1, hy + 2, 1, hy + 3), ('skin', 3))
    f.detail(f.rect(-1, hy + 3, 2, hy + 4), ('skin', 1))
    if P['face'] == 'shut' or P['brow'] == 2:
        f.detail(f.rect(-1, hy + 6, 2, hy + 7) | f.rect(-2, hy + 7, -1, hy + 8) | f.rect(2, hy + 7, 3, hy + 8), ('skin', 0))
    else:
        f.detail(f.rect(-1, hy + 6, 2, hy + 7), ('skin', 0))
    f.detail(f.rect(-8, hy + 3, -6, hy + 4), ('blush', 2))
    f.detail(f.rect(6, hy + 3, 8, hy + 4), ('blush', 2))


def head_north(f, P, hy):
    f.add(f.ell(-9.0, hy + 1.5, 2.2, 3.0) | f.ell(9.0, hy + 1.5, 2.2, 3.0), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(0, hy + 0.5, 8.8, 9.6), 'skin', z=40, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _crown_shine(X, Y, t, 0, hy))
    ring = f.ell(0, hy + 1.0, 9.4, 8.8) & ~f.ell(0, hy - 7.0, 7.2, 5.6)
    ring |= f.ell(-8.4, hy - 2.5, 3.0, 5.2) | f.ell(8.4, hy - 2.5, 3.0, 5.2)
    ring &= f.Y < hy + 8.5
    f.add(ring, 'greyhair', z=44, rl=1.3, rs=2.2, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _back_strands(X, Y, t, hy))
    if P['mask'] == 'face':
        mask_worn_north(f, hy)
    else:
        # the mask strap round the nape (the mask itself is on the chest or in the hand)
        f.add(f.rect(-6, hy + 9, 6, hy + 10.2), 'rubber', z=45, flat=2, line='hard', tag='mask')


def head_side(f, P, hy, hx):
    f.add(f.ell(hx + 2.0, hy + 0.5, 7.6, 9.6), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _crown_shine(X, Y, t, hx, hy))
    f.add(f.ell(hx + 9.6, hy + 2.6, 1.9, 1.8), 'skin', z=40.5, rl=1, rs=1.2, line='hard')
    f.add(f.ell(hx + 6.5, hy + 8.0, 2.4, 2.0), 'skin', z=40.4, rl=1, rs=1.2, line='hard')
    hair = f.ell(hx - 4.5, hy - 2.0, 4.0, 5.6) | f.ell(hx - 3.0, hy + 2.0, 3.6, 4.0) | f.ell(hx - 1.5, hy - 5.5, 3.2, 2.6)
    hair &= ~f.ell(hx + 3.0, hy - 4.0, 7.0, 6.4)
    hair &= f.ell(hx + 2.0, hy + 0.5, 8.6, 10.6)
    f.add(hair, 'greyhair', z=44, rl=1.3, rs=2.0, line='hard', cast=(1, 1, 1),
          tonemap=lambda X, Y, t: _tuft_strands(X, Y, t, hy))
    f.add(f.ell(hx - 0.6, hy + 1.2, 1.9, 2.7), 'skin', z=45, rl=1, rs=1.2, line='hard')
    f.dot(hx - 0.6, hy + 1.2, ('skin', 1))
    ey = hy - 0.5
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    f.detail(f.rect(hx + 4, ey - 3 + lift, hx + 8, ey - 1 + lift) & ~f.rect(hx + 7, ey - 3 + lift, hx + 8, ey - 2 + lift), ('greyhair', 1))
    f.detail(f.rect(hx + 4, hy - 6, hx + 7, hy - 5), ('skin', 1))
    if P['mask'] == 'face':
        mask_worn_side(f, hy, hx)
        return
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(hx + 5, ey + 2, hx + 7, ey + 3), EYE)
    else:
        eye(f, hx + 5, ey, 3)
    f.detail(f.rect(hx + 7, hy + 6, hx + 9, hy + 7), ('skin', 0))
    f.detail(f.rect(hx + 3, hy + 3, hx + 5, hy + 4), ('blush', 2))


def _hair_planes(X, Y, t, hy):
    """v2 (asset gate, volume): the hair ring from behind: its upper-left lit, its lower right in shade."""
    out = t.copy()
    lit = (X < -2.0) & (Y < hy + 2.0) & (t == 2)
    dark = (X > 3.0) & (Y > hy + 3.0) & (t == 2)
    out[lit] = 3
    out[dark] = 1
    return out


def head_3q(f, P, hy, back):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW on the mirrored grid), for the turn
    in-betweens: the profile head turned a quarter back toward the camera.  Front: the near ear and
    tuft behind the cheek, both eyes (the far one near the cheek's edge), the nose inside the face.
    Back: the bald crown and the hair ring with only the near ear."""
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
    if back:
        f.add(f.ell(7.8, hy + 1.8, 2.0, 2.8), 'skin', z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(0.6, hy + 0.5, 8.6, 9.6), 'skin', z=40, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1),
              tonemap=lambda X, Y, t: _crown_shine(X, Y, t, 0.6, hy))
        ring = f.ell(0.6, hy + 1.0, 9.2, 8.8) & ~f.ell(0.0, hy - 7.0, 7.4, 5.8)
        ring |= f.ell(-7.4, hy - 2.5, 2.8, 5.0) | f.ell(8.2, hy - 2.5, 3.0, 5.2)
        ring &= f.Y < hy + 8.5
        f.add(ring, 'greyhair', z=44, rl=1.3, rs=2.2, line='hard', cast=(0, 1, 1),
              tonemap=lambda X, Y, t: _hair_planes(X, Y, _back_strands(X, Y, t, hy), hy))
        if P['mask'] == 'face':
            with f.tagging('mask'):
                f.add(f.rect(-8.0, hy - 1.5, 9.4, hy + 0.3), 'rubber', z=45.5, flat=1, line='hard')
                f.add(f.ell(9.2, hy + 3.0, 1.4, 3.0), 'rubber', z=38.5, rl=1, rs=1, line='hard')
        else:
            f.add(f.rect(-5, hy + 9, 7, hy + 10.2), 'rubber', z=45, flat=2, line='hard', tag='mask')
        return
    f.add(f.ell(1.2, hy + 0.5, 8.2, 9.6), 'skin', z=40, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _crown_shine(X, Y, t, 0.0, hy))
    f.add(f.ell(7.0, hy + 8.0, 2.2, 1.8), 'skin', z=40.4, rl=1, rs=1.2, line='hard')        # chin
    tuft = (f.ell(-6.4, hy - 2.0, 3.4, 5.4) | f.ell(-6.0, hy + 2.0, 3.0, 3.8)) & ~f.ell(1.5, hy - 3.5, 7.0, 6.6)
    tuft &= f.ell(1.2, hy + 0.5, 9.4, 10.6)
    f.add(tuft, 'greyhair', z=44, rl=1.3, rs=2.0, line='hard', cast=(1, 1, 1),
          tonemap=lambda X, Y, t: _tuft_strands(X, Y, t, hy))
    f.add(f.ell(9.0, hy - 1.5, 1.2, 3.4) & ~f.ell(1.2, hy + 0.5, 8.2, 9.6), 'greyhair', z=39.5, rl=1, rs=1.2, line='hard')   # far tuft
    f.add(f.ell(-3.4, hy + 1.6, 1.8, 2.6), 'skin', z=45, rl=1, rs=1.2, line='hard')            # near ear
    f.dot(-3.4, hy + 1.6, ('skin', 1))
    ey = hy - 0.5
    f.detail(f.rect(0, ey - 3 + lift, 3, ey - 1 + lift) & ~f.rect(2, ey - 3 + lift, 3, ey - 2 + lift), ('greyhair', 1))
    f.detail(f.rect(5, ey - 3 + lift, 8, ey - 1 + lift) & ~f.rect(7, ey - 3 + lift, 8, ey - 2 + lift), ('greyhair', 1))
    f.detail(f.rect(2, hy - 6, 6, hy - 5), ('skin', 1))
    if P['mask'] == 'face':
        with f.tagging('mask'):
            f.add(f.cap(-7.5, hy - 1.0, 3.0, hy - 0.5, 0.9), 'rubber', z=44.5, flat=1, line='hard')
            shell = f.ell(4.6, hy + 3.6, 5.4, 5.6) | f.ell(4.2, hy + 0.2, 6.0, 3.0)
            f.add(shell, 'rubber', z=46, rl=1.4, rs=2.2, line='hard', cast=(0, 1, 1))
            for x, r in ((1.6, 2.3), (6.6, 1.9)):
                f.add(f.ell(x, hy + 0.4, r, r), 'brass', z=46.1, flat=2, line=None)
                f.add(f.ell(x, hy + 0.4, r - 0.9, r - 0.9), 'lens', z=46.2, flat=2, line=None)
            f.dot(0.6, hy - 0.6, ('lens', 4), solid=False, z=46.3)
            can = f.rect(3.2, hy + 6.5, 7.6, hy + 10) | f.ell(5.4, hy + 10, 2.2, 1.0)
            f.add(can, 'brass', z=46.3, rl=1, rs=1.4, line='hard')
            f.detail(f.rect(3.4, hy + 8, 7.4, hy + 8.8), ('brass', 0), z=46.4)
        return
    if P['face'] == 'shut' or P['blink']:
        f.detail(f.rect(1, ey + 2, 3, ey + 3), EYE)
        f.detail(f.rect(6, ey + 2, 8, ey + 3), EYE)
    else:
        eye(f, 1, ey, 3)
        eye(f, 6, ey, 3)
    f.detail(f.rect(4, hy + 2, 5, hy + 3), ('skin', 3))
    f.detail(f.rect(4, hy + 3, 6, hy + 4), ('skin', 1))
    if P['face'] == 'shut' or P['brow'] == 2:
        f.detail(f.rect(3, hy + 6, 6, hy + 7) | f.rect(2, hy + 7, 3, hy + 8) | f.rect(6, hy + 7, 7, hy + 8), ('skin', 0))
    else:
        f.detail(f.rect(3, hy + 6, 6, hy + 7), ('skin', 0))
    f.detail(f.rect(-2, hy + 3, 0, hy + 4), ('blush', 2))


def _crown_shine(X, Y, t, hx, hy):
    out = t.copy()
    r = ((X - hx + 2.5) / 3.0) ** 2 + ((Y - hy + 6.5) / 1.8) ** 2
    out[(r < 1.0) & (t >= 2)] = 3
    return out


def _tuft_strands(X, Y, t, hy):
    out = t.copy()
    m = (np.abs(((X * 0.6 + Y - hy) % 3.2) - 1.6) < 0.45) & (t == 2)
    out[m] = 1
    return out


def _back_strands(X, Y, t, hy):
    out = t.copy()
    lit = -X * 0.55 - (Y - hy) * 0.85            # 26 Oct (asset gate at SCALE): the lit upper-left plane of the fringe
    out[(lit > 3.2) & (t == 2)] = 3
    out[(lit < -5.5) & (t >= 1)] = np.minimum(out[(lit < -5.5) & (t >= 1)], 1)
    for k in (-4.5, 4.5):
        m = (np.abs(X - k - (Y - hy) * 0.2 * np.sign(k)) < 0.6) & (Y > hy + 1) & (Y < hy + 6)
        out[m & (t >= 2)] = 1
    return out


def _apron_fold(X, Y, t, s, b):
    out = t.copy()
    m = (np.abs(X - 6.5 * s - (Y + 20 - b) * 0.15 * s) < 0.55) & (Y > -24 + b) & (Y < -12 + b)
    out[m & (t >= 2)] = 1
    return out


# ================================================================================ torso
def torso_south(f, P, b, ub):
    body = f.ell(0, -36 + ub, 11.8, 12) | f.rect(-11, -40 + ub, 11, -26 + b)
    f.add(body, 'cream', z=20, rl=2, rs=4, vgrad=0.4, line='hard')
    bib = f.poly([(-6.5, -47 + ub), (6.5, -47 + ub), (8.5, -28 + b), (-8.5, -28 + b)])
    f.add(bib, 'apron', z=22, rl=1.8, rs=3.0, vgrad=0.3, line='hard')
    for s in (-1, 1):
        leaf = f.poly([(1.0 * s, -28 + b), (11.5 * s, -28 + b), (12.5 * s, -10 + b), (1.0 * s, -10.5 + b)])
        f.add(leaf, 'apron', z=21, rl=1.8, rs=3.0, vgrad=0.5, line='hard',
              tonemap=lambda X, Y, t, s=s: _apron_fold(X, Y, t, s, b))
    f.add(f.rect(-3.5, -40 + ub, 3.5, -35 + ub), 'apron', z=22.5, rl=1, rs=1.6, line='soft')
    f.add(f.rect(1, -43 + ub, 2, -39 + ub), 'cork', z=22.4, flat=2, line='hard')
    for s in (-1, 1):
        f.add(f.cap(5.5 * s, -46 + ub, 4.0 * s, -50 + ub, 1.1), 'apron', z=21.5, flat=1, line='hard')
    f.add(f.rect(-11.5, -30 + b, 11.5, -26.5 + b), 'leather', z=24, rl=1, rs=1.2, line='soft')
    f.add(f.rect(-1.5, -30.5 + b, 1.5, -26 + b), 'brass', z=24.5, rl=1, rs=1.2, line='hard')
    vial(f, -6.0, -24 + b, 'reagent', z=25)
    vial(f, 4.0, -24 + b, 'amberliq', z=25)


def torso_north(f, P, b, ub):
    f.add(f.ell(0, -24 + b, 10.4, 5) | f.rect(-10.4, -28 + b, 10.4, -24 + b), 'trouser', z=11, rl=2, rs=3, line='hard',
          tonemap=lambda X, Y, t: np.where((np.abs(X) < 0.5) & (Y > -24 + b), 1, t))
    for s in (-1, 1):
        f.add(f.poly([(9 * s, -28 + b), (11.5 * s, -28 + b), (12.5 * s, -10 + b), (9.5 * s, -10.5 + b)]), 'apron', z=12,
              rl=1.4, rs=2.4, vgrad=0.5, line='hard')
    body = f.ell(0, -36 + ub, 11.8, 12) | f.rect(-11, -40 + ub, 11, -28 + b)
    f.add(body, 'cream', z=20, rl=2, rs=4, vgrad=0.4, line='hard',
          tonemap=lambda X, Y, t: np.where((np.abs(X) < 0.5) & (Y > -44 + ub) & (Y < -32 + ub) & (t >= 2), 1, t))
    for s in (-1, 1):
        f.add(f.poly([(-5.5 * s, -50 + ub), (-3.5 * s, -50 + ub), (9.5 * s, -29 + b), (7.0 * s, -29 + b)]), 'apron', z=22,
              rl=1, rs=1.4, line='soft')
    f.add(f.rect(-11.5, -30 + b, 11.5, -27 + b), 'apron', z=23, rl=1, rs=1.2, line='soft')
    f.add(f.rect(-11.8, -31 + b, 11.8, -28.5 + b) & ~f.rect(-11, -31 + b, 11, -26 + b), 'leather', z=23.5, flat=1, line='soft')
    bow = f.ell(-2.6, -29 + b, 2.6, 1.8) | f.ell(2.6, -29 + b, 2.6, 1.8)
    f.add(bow, 'apron', z=24, rl=1, rs=1.4, line='hard')
    f.add(f.ell(0, -29 + b, 1.2, 1.4), 'apron', z=24.2, flat=1, line='hard')
    f.add(f.poly([(-1, -28 + b), (-3, -21 + b), (-1.5, -21 + b), (0, -27 + b)]) | f.poly([(1, -28 + b), (3.4, -22 + b), (2, -22 + b), (0, -27 + b)]),
          'apron', z=23.8, rl=1, rs=1.2, line='hard')


def _west_planes(X, Y, t, x0, front):
    """v2 (asset gate, light): seen from the west the front of the body faces the upper-left
    light and the back faces away; the E drawing mirrored would light the back.  front: lift the
    forward half one tone; else shade the back half."""
    out = t.copy()
    if front:
        m = (X > x0) & (t >= 1) & (t <= 2)
        out[m] = t[m] + 1
    else:
        m = (X < x0) & (t >= 2)
        out[m] = t[m] - 1
    return out


def _skirt_planes(X, Y, t, b, west):
    """v2 (asset gate, volume): the apron's lower panel shows three planes: the panel toward the
    light (behind the fold in E, in front of it in W) one tone up, the far edge one down."""
    out = t.copy()
    fold = 5 + (Y + 20 - b) * 0.15
    lit = ((X > fold + 1.0) if west else ((X < fold - 1.0) & (X > fold - 6.0))) & (t == 2) & (Y > -26 + b)
    out[lit] = 3
    return out


def torso_side(f, P, b, ub, tx, west):
    body = f.ell(0.8 + tx, -35 + ub, 9.4, 11.8) | f.poly([(-8 + tx * 0.5, -25 + b), (-8 + tx, -40 + ub), (9 + tx, -40 + ub), (10 + tx * 0.5, -25 + b)])
    f.add(body, 'cream', z=20, rl=2, rs=4, vgrad=0.4, line='hard',
          tonemap=(lambda X, Y, t: _west_planes(X, Y, t, tx - 1.0, False)) if west else None)
    f.add(f.ell(0.5, -23 + b, 8.4, 4.2), 'trouser', z=19, rl=2, rs=3, line='hard')
    bib = f.poly([(4.5 + tx, -47 + ub), (8.2 + tx, -45 + ub), (10.6 + tx * 0.5, -28 + b), (4.0 + tx * 0.5, -28 + b)])
    f.add(bib, 'apron', z=22, rl=1.6, rs=2.6, line='hard', tonemap=(lambda X, Y, t: _west_planes(X, Y, t, 6.0 + tx * 0.7, True)) if west else None)
    skirt = f.poly([(-4.5, -28 + b), (10.6, -28 + b), (12.5, -10 + b), (8.5, -9.5 + b), (-3.0, -10.5 + b)])
    f.add(skirt, 'apron', z=21, rl=1.8, rs=3.0, vgrad=0.5, line='hard',
          tonemap=lambda X, Y, t: _skirt_planes(X, Y, np.where((np.abs(X - 5 - (Y + 20 - b) * 0.15) < 0.55) & (Y > -24 + b) & (Y < -11 + b) & (t >= 2), 1, t), b, west))
    f.add(f.cap(5.5 + tx, -46 + ub, 0.0 + tx, -50 + ub, 1.1), 'apron', z=21.5, flat=1, line='hard')
    f.add(f.poly([(-8.4, -30 + b), (10.8, -30 + b), (10.8, -26.5 + b), (-8.4, -26.5 + b)]), 'leather', z=24, rl=1, rs=1.2, line='soft')
    f.add(f.rect(9.0, -30.5 + b, 11.2, -26 + b), 'brass', z=24.5, rl=1, rs=1.2, line='hard')
    vial(f, 6.5, -24 + b, 'amberliq' if west else 'reagent', z=25)


# ================================================================================ build
SHW = 12.0
ARM = 7.4 + 9.2
REST_R = (2.5, 24.5, 14.0)        # right hand at rest (fwd, up, lat), the flask hanging from it
REST_L = (1.5, 24.0, -14.0)
CLIP = (-2.5, 27.5, -9.5)         # catalyst belt clip on the left hip (standing body space)
CASE = (-4.5, 26.0, 12.0)         # flask case on the right hip


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0,
             footR=(2.0, 0.0), footL=(-2.0, 0.0), stance=5.6,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             flask='hand', fdir=(0.0, -1.0, 0.0), fly=False,   # 'hand', 'none' (thrown, hand empty); fly: just left the hand
             openR=None, openL=None,                   # open hand: finger direction (body space)
             mask='chest',                             # 'chest', 'hand' (left hand), 'face'
             cat=None, catglow=0,                      # cat: chamber direction when held in the left hand
             blink=False, brow=0, face=None)
    p.update(k)
    return p


def _leg(f, R, up, lo, kn3, foot3, lat, far, z):
    dim = 1 if far else 0
    f.add(up | lo, 'trouser', z=z, rl=2, rs=3, vgrad=0.3, dim=dim, line='hard')
    boot(f, R, foot3, 'leather', z, far)


def _arm(f, R, sh3, h3, pole, z, far):
    """Rolled cream sleeve to the elbow, bare forearm, the roll at the elbow."""
    up, lo, el3 = R.limb(sh3, h3, 7.4, 9.2, 3.7, 3.0, 2.6, pole)
    dim = 1 if far else 0
    f.add(lo, 'skin', z=z - 0.1, rl=1.4, rs=2.0, line='hard', dim=dim)
    zu = up_z(R, z, far)
    f.add(up, 'cream', z=zu, rl=1.6, rs=2.4, line='hard', dim=dim, cast=None if dim else (1, 1, 1))
    ex, ey = R.p(el3)
    f.add(f.ell(ex, ey + 0.3, 3.7, 2.1), 'cream', z=zu + 0.05, rl=1.2, rs=1.6, line='soft', dim=dim,
          tonemap=lambda X, Y, t: np.where((np.abs(Y - ey - 0.5) < 0.5) & (t >= 2), 1, t))
    return el3


def build(f, facing, P):
    R = Rig(f, facing)
    if facing in ('NE', 'SW'):        # v2: the far side faces the upper-left light here, so it is not dimmed
        R.far = lambda lat: False
    side = R.side
    west = facing == 'W'
    hip3, sh3, head3 = frame(P, 22.0, 20.0, 16.0)
    body_off = (P['hipx'], -P['crouch'] - P['bob'], 0.0)
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    b = hy + 22.0
    ub = sy + 42.0
    tx = sx - hx
    shR = add3(sh3, (0.0, -1.0, SHW))
    shL = add3(sh3, (0.0, -1.0, -SHW))
    hR = add3(P['handR'] or REST_R, body_off)
    hL = add3(P['handL'] or REST_L, body_off)
    hR = reach(shR, hR, ARM)
    hL = reach(shL, hL, ARM)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    clip3 = add3(CLIP, body_off)
    case3 = add3(CASE, body_off)
    if R.diag:                     # the turned hip is narrower than the profile: the case sits on it
        case3 = (case3[0] + 1.5, case3[1], case3[2] - 2.5)
    # ---------------------------------------------------------------- legs
    legs(f, R, P, hip3, _leg)
    # ---------------------------------------------------------------- torso
    with Shift(f, hx, 0):
        if R.diag:                       # contract v2 turn in-betweens: the S or N torso turned onto the body
            vf = 'N' if R.back else 'S'
            with turn.Warp(f, R, tx * 0.5, 12.3, 9.2, vf):
                (torso_north if R.back else torso_south)(f, P, b, ub)
        elif facing == 'S':
            torso_south(f, P, b, ub)
        elif facing == 'N':
            torso_north(f, P, b, ub)
        else:
            torso_side(f, P, b, ub, tx, west)
    # flask case (right hip, a little behind) and the catalyst (left hip)
    dcase = R.d(case3)
    case(f, R, case3, 25.5 if dcase > 2 else 15.5, dim=1 if R.far(1) else 0)
    if P['cat'] is None:
        top3 = add3(clip3, (0.0, -1.5, 0.0))
        base3 = add3(clip3, (0.0, -10.0, 0.0))
        zc = 26 if R.d(clip3) > 2 else 14
        catalyst(f, R, clip3, top3, base3, zc, dim=1 if (R.far(-1) or facing == 'N') else 0, glow=P['catglow'])
    # ---------------------------------------------------------------- arms
    out = {}
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        pole = P['pole' + key] or (-1.0, -0.25, 0.6 * lat)
        z = arm_z(R, P, key, hh)
        far = R.far(lat)
        el3 = _arm(f, R, sh, hh, pole, z, far)
        out[key] = (el3, hh, z, far)
    # mask on the chest (before the hands, so a hand reaching for it covers it)
    if P['mask'] in ('chest', 'hand'):
        zs = 34.0 if not R.back else 19.5
        with Shift(f, sx, 0):
            if P['mask'] == 'chest' and R.diag and not R.back:
                with turn.Warp(f, R, 0.0, 12.3, 9.2, 'S'):
                    for s in (-1, 1):
                        f.add(f.seg(4.5 * s, -42 + ub, 3.5 * s, -47 + ub), 'rubber', z=zs, flat=2, line=None, clean=False, tag='mask')
                    mask_front(f, 0, -39.5 + ub, z=zs + 1)
            elif P['mask'] == 'chest':
                if facing == 'S':
                    for s in (-1, 1):
                        f.add(f.seg(4.5 * s, -42 + ub, 3.5 * s, -47 + ub), 'rubber', z=zs, flat=2, line=None, clean=False, tag='mask')
                    mask_front(f, 0, -39.5 + ub, z=zs + 1)
                elif side:
                    f.add(f.seg(7, -42 + ub, 4, -48 + ub), 'rubber', z=zs, flat=2, line=None, clean=False, tag='mask')
                    mask_side(f, 9.5, -38.5 + ub, z=zs + 1)
    # ---------------------------------------------------------------- hands and what they hold
    for key in ('R', 'L'):
        el3, hh, z, far = out[key]
        hxp, hyp = R.p(hh)
        dim = 1 if far else 0
        skin_z = z + 0.8
        grip = None
        if key == 'R' and P['flask'] == 'hand':
            fd = P['fdir']
            bx, by = flask(f, R, hh, fd, z + 0.4, dim=dim)
            f.anchor('flask', bx, by)
            grip, _ = sdir(R, hh, fd)
        if key == 'R' and P['flask'] == 'none' and P.get('fly'):
            # the release drawing: the flask has just left the open hand, a little ahead of it along
            # the throw (the release anchor is on it, in every facing and aim)
            fwd = nrm(P['openR'] or (1.0, 0.0, 0.0))
            c3 = add3(hh, mul3(fwd, 3.0))                 # its neck just past the fingers, the body leading
            bx, by = flask(f, R, c3, tuple(fwd), max(z + 0.6, 46.5), dim=0)
            f.anchor('flask', bx, by)
        if key == 'L' and P['cat'] is not None:
            u = nrm(P['cat'])
            top3 = add3(hh, mul3(u, 4.5))
            base3 = add3(hh, mul3(u, -4.0))
            cz = z + (1.0 if R.d(tuple(u)) > 0.3 else 0.4)        # pointed at the camera: the chamber and bulb are nearer than the fist
            catalyst(f, R, clip3, top3, base3, cz, dim=dim, glow=P['catglow'])
            f.anchor('catalyst', *R.p(add3(top3, mul3(u, 2.0))))      # the bulb's front, where the flare leaves
            grip, _ = sdir(R, hh, u)
        if key == 'L' and P['mask'] == 'hand':
            mx, my = R.p(add3(hh, (0.0, 0.5, 0.0)))
            if facing == 'S' or (R.diag and not R.back):
                mask_front(f, mx, my, z=z + 0.4)
            elif R.back:
                mask_back(f, mx, my, z=z + 0.4)
            else:
                mask_side(f, mx + 1.0, my, z=z + 0.4)
            # the strap from the mask up round the neck: it stays on him
            nx, ny = R.p(add3(sh3, (0.0, 3.0, 0.0)))
            f.add(f.seg(mx, my - 2, nx, ny), 'rubber', z=z + 0.3, flat=2, line=None, clean=False, tag='mask')
        o = P['open' + key]
        if o is not None and grip is None:
            open_hand(f, R, hh, o, skin_z, 'skin', dim=dim, thumb3=(0.0, 1.0, 0.0))
        else:
            fist(f, hxp, hyp, skin_z, 'skin', dim=dim, grip=grip, r=3.0)
    # ---------------------------------------------------------------- head
    hx2, hy2 = R.p(head3)
    hx2, hy2 = float(round(hx2)), float(round(hy2))      # v2 polish: the head on whole pixels (no boiling)
    if R.diag:
        with Shift(f, hx2, 0):
            head_3q(f, P, hy2, R.back)
    elif facing == 'S':
        with Shift(f, hx2, 0):
            head_south(f, P, hy2)
    elif facing == 'N':
        with Shift(f, hx2, 0):
            head_north(f, P, hy2)
    else:
        with Shift(f, hx2, 0):
            head_side(f, P, hy2, 0.0)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')), scale=SCALE)
    f.despeckle = True                              # v2 polish: no lone pixels (clean pixels, as bramble.py)
    build(f, facing, P)
    return f
