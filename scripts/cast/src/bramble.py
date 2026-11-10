"""Bramble: older human ranger.  Grey curly hair and full beard, short green mantle over a cream
shirt, brown strap and belt with a gold buckle, brown trousers and boots.  He is a left-handed
archer (pass 2 decision, so the bow is the near hand facing east, as in Codex's art): the recurve
bow is in his RIGHT hand, he draws with the LEFT, the quiver rides over the LEFT shoulder, the
billhook hangs at the RIGHT hip (used by the right hand once the bow is stowed) and the folding
buckler doubles as the bracer on the RIGHT (bow) forearm.  About 74 px tall on the 960x540 grid.

Pass 2: one pose-driven build for all four facings.  A pose (P0) places the body, feet, hands
and gear in body space (parts.Rig); the same pose renders S, N, E and W, so an animation is a
table of poses (anim_bramble.py).  Body 12% wider than pass 1, head 1 px wider each side.

Equipment tags (checked per frame by checks.py): bow, quiver, billhook, buckler, arrow."""
import math
import numpy as np
from ew import Fig
from parts import eye, boot_side, boot_front, EYE, Rig, proj, FLIP, FACINGS8
import palette  # noqa: F401
import anim

ID = 'bramble'
NAME = 'Bramble'
SHW = 13.5                      # shoulder half-width (lat)
REST_R = (8.5, 28.5, 14.0)      # right hand at rest (fwd, up, lat), holding the bow low
REST_L = (1.0, 25.5, -14.5)     # left hand at rest


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, tilt=0.0,
             footR=(2.5, 0.0), footL=(-2.5, 0.0), stance=6.0,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             bow='hand', bowu=None, bown=None, draw=0.0, nock=None, bowz=None,
             arrow=False, qarrow=False, shot=None,
             hook='hip', hookdir=(0.25, 1.0, 0.0), buckler=0.0, briar=0.0,
             lag=0.0, hair=0.0, twist=0.0, blink=False, brow=0, face=None, fx=None)
    p.update(k)
    return p


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def nrm(v):
    v = np.array(v, float)
    return v / (np.linalg.norm(v) or 1.0)


# ------------------------------------------------------------------------------------ gear
BOW_HALF = 26.0                 # v2 (Matt 25 Oct: "make the bow a bit more interesting/ bigger"): 52 px


def _reach(sh3, h3, L=17.0, k=1.03):
    v = np.subtract(h3, sh3)
    d = float(np.linalg.norm(v))
    if d <= L * k:
        return h3
    return tuple(np.add(sh3, v * (L * k / d)))


def _clear_ground(g3, u3, L=BOW_HALF, margin=2.5):
    """The bigger bow (v2) must not dig into the ground: when its lower tip would come below
    `margin` px above the ground (a crouch, a hit, a kneel), the top tips forward until it
    clears, as an archer lifts the bow off the ground."""
    u = np.array(nrm(u3))
    for _ in range(40):
        if g3[1] - u[1] * L >= margin:
            break
        u = np.array(nrm(tuple(u + np.array([0.12, -0.03, 0.0]))))
    return tuple(u)


def bow3(f, R, g3, u3, n3, draw, z, half=BOW_HALF, nock3=None, arrow=False, briar=0.0):
    """Carved recurve bow gripped at g3 (v2: 52 px, about 70% of his height).  u3: bottom->top
    limb direction, n3: toward the target (the belly faces it).  draw 0..1 bends the limbs.
    Thick riser with a wrapped leather grip and gold wrap bands, limbs that taper and carry a
    carved light ridge on the back and notches, recurved tips with horn caps, a 1 px string with
    a brass nock point.  Returns the 3D nock point."""
    u3, n3 = nrm(u3), nrm(n3)
    bend = 5.6 + 3.0 * draw
    L = half * (1 - 0.08 * draw)
    pts3 = []
    N = 37
    for i in range(N):
        u = -1 + 2 * i / (N - 1)
        off = bend * (1 - u * u)
        if abs(u) > 0.80:
            off += 3.6 * ((abs(u) - 0.80) / 0.20) ** 1.6       # the recurve: tips curl toward the target
        pts3.append(tuple(np.array(g3) + u3 * u * L + n3 * (off - bend)))
    pts = [R.p(q) for q in pts3]
    m = None
    gx, gy = R.p(g3)
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts[:-1], pts[1:])):
        u = abs(-1 + 2 * (i + 0.5) / (N - 1))
        r = 2.0 if u < 0.16 else (1.75 - 0.75 * (u - 0.16) / 0.84)
        c = f.cap(x0, y0, x1, y1, max(1.0, r))
        m = c if m is None else m | c
    f.add(m, 'bow', z=z, rl=1.0, rs=1.6, line='hard', tag='bow')
    # carving: a light ridge along the back of each limb and dark notches across it
    with f.tagging('bow'):
        for i in list(range(7, 15)) + list(range(22, 30)):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            f.detail(f.seg(x0, y0, x1, y1) & m, ('bow', 3), solid=False, z=z + 0.005)
        for i in (9, 12, 24, 27):
            x, y = pts[i]
            f.detail(f.pixels([(x, y)]) & m, ('bow', 0), solid=False, z=z + 0.006)
        for i in (1, N - 2):                                      # horn tip caps
            x, y = pts[i]
            f.add(f.ell(x, y, 1.4, 1.4), 'fletch', z=z + 0.006, rl=0.8, rs=1.0, line='hard')
    # wrapped grip: leather with two gold bands
    a3, b3 = np.array(g3) - u3 * 3.4, np.array(g3) + u3 * 3.4
    (ax, ay), (bx, by) = R.p(a3), R.p(b3)
    f.add(f.cap(ax, ay, bx, by, 2.1), 'leather', z=z + 0.01, rl=1.0, rs=1.2, line='hard', tag='bow')
    for t in (-3.4, 3.4):
        cx, cy = R.p(tuple(np.array(g3) + u3 * t))
        f.add(f.ell(cx, cy, 2.2, 1.1), 'gold', z=z + 0.012, flat=2, line=None, tag='bow')
    if nock3 is None:
        nock3 = tuple(np.array(g3) - n3 * (bend + 0.8 + 11 * draw))
    nx, ny = R.p(nock3)
    top, bot = pts[-2], pts[1]
    sm = f.seg(top[0], top[1], nx, ny) | f.seg(nx, ny, bot[0], bot[1])
    f.add(sm & ~m, 'string', z=z - 0.02, flat=1, line=None, clean=False, noout=True, tag='bow')
    if not arrow:
        f.detail(f.pixels([(nx, ny)]) & ~m, ('gold', 3), solid=False, z=z, tag='bow')
    if briar > 0:
        # Briarshot: a living briar winds round the same bow; leaves and thorns bud along it
        vm = None
        for i in range(3, N - 3, 2):
            u = -1 + 2 * i / (N - 1)
            if abs(u) > 0.25 + 0.75 * min(1.0, briar):
                continue
            w = 1.6 * math.sin(i * 1.3)
            q = np.array(pts3[i]) + np.cross(u3, n3) * 0 + n3 * w * 0.6
            x, y = R.p(q)
            c = f.ell(x + w * 0.5, y, 1.3, 1.3)
            vm = c if vm is None else vm | c
        if vm is not None:
            f.add(vm, 'mantle', z=z + 0.02, rl=0.8, rs=1.0, line='shade', tag='bow')
        nleaf = int(round(5 * min(1.0, briar)))
        for j, i in enumerate((6, 30, 11, 25, 18)[:nleaf]):
            x, y = pts[i]
            s = -1 if j % 2 else 1
            f.add(f.ell(x + 2.4 * s, y - 0.5, 2.5, 1.5), 'leafg', z=z + 0.03, rl=1, rs=1, line='hard', tag='bow')
        if briar >= 0.99:
            for i in (2, N - 3):
                x, y = pts[i]
                f.dot(x, y - 1, ('bloom', 3), tag='bow')
    if arrow:
        arrow3(f, R, nock3, n3, z + 0.05)
    return nock3


def arrow3(f, R, nock3, n3, z, length=21, tag='arrow'):
    """Arrow from its nock along n3: fletching, shaft, steel head.  Returns the tip (pivot)."""
    n3 = nrm(n3)
    tip3 = np.array(nock3) + n3 * length
    x0, y0 = R.p(nock3)
    x1, y1 = R.p(tip3)
    dx, dy = x1 - x0, y1 - y0
    Lp = math.hypot(dx, dy)
    ux, uy = (dx / Lp, dy / Lp) if Lp > 1e-3 else (0.0, 1.0)
    if Lp > 4:
        f.detail(f.seg(x0 + ux * 2, y0 + uy * 2, x1 - ux * 2.5, y1 - uy * 2.5), ('bow', 3), solid=True, tag=tag, z=z)   # v2: depth-aware, so a shaft behind the head stays behind it
        head = f.poly([(x1 - ux * 3 - uy * 1.6, y1 - uy * 3 + ux * 1.6), (x1 + ux, y1 + uy),
                       (x1 - ux * 3 + uy * 1.6, y1 - uy * 3 - ux * 1.6)])
    else:
        head = f.ell(x1, y1, 1.6, 1.6)
    f.add(head, 'steel', z=z, rl=1, rs=1, line='hard', tag=tag)
    fl = f.poly([(x0 - uy * 2, y0 + ux * 2), (x0 + ux * 4, y0 + uy * 4), (x0 + uy * 2, y0 - ux * 2)]) | f.cap(x0, y0, x0 + ux * 4, y0 + uy * 4, 0.9)
    f.add(fl, 'fletch', z=z, rl=1, rs=1.3, line='soft', tag=tag)
    return x1 + ux, y1 + uy


def billhook(f, R, g3, d3, z, dim=0):
    """Billhook gripped at g3, handle along d3 (grip -> blade).  The hook curls forward (toward
    the character's facing).  Returns the blade tip (pivot space)."""
    d3 = nrm(d3)
    a3 = np.array(g3) - d3 * 3.0
    b3 = np.array(g3) + d3 * 7.0
    (ax, ay), (bx, by) = R.p(a3), R.p(b3)
    f.add(f.cap(ax, ay, bx, by, 1.25), 'leather', z=z, rl=1, rs=1.5, dim=dim, tag='billhook')
    L = math.hypot(bx - ax, by - ay) or 1
    ux, uy = (bx - ax) / L, (by - ay) / L
    # the hook's sharp inside faces forward: choose the perpendicular that points forward
    fx3 = R.p(add3(tuple(b3), (3.0, 0, 0)))
    px, py = -uy, ux
    if (fx3[0] - bx) * px + (fx3[1] - by) * py < 0:
        px, py = -px, -py
    if abs(fx3[0] - bx) + abs(fx3[1] - by) < 1.2 and R.facing in 'SN':
        px, py = (-uy, ux) if R.facing == 'S' else (uy, -ux)
    B = [(bx - px * 1.8, by - py * 1.8), (bx + ux * 6 - px * 2.0, by + uy * 6 - py * 2.0),
         (bx + ux * 9 + px * 0.5, by + uy * 9 + py * 0.5), (bx + ux * 8 + px * 3.5, by + uy * 8 + py * 3.5),
         (bx + ux * 6.5 + px * 1.6, by + uy * 6.5 + py * 1.6), (bx + px * 1.6, by + py * 1.6)]
    f.add(f.poly(B), 'steel', z=z + 0.1, rl=1.2, rs=2.0, dim=dim, line='hard', tag='billhook')
    return bx + ux * 8 + px * 3.5, by + uy * 8 + py * 3.5


def buckler(f, R, elbow3, hand3, open_, z, dim=0):
    """Folding buckler on the right forearm.  Folded: a stack of leaves along the forearm.
    Open: a round shield centred just behind the wrist, facing out along the forearm normal."""
    e, h = np.array(elbow3), np.array(hand3)
    c3 = e + (h - e) * 0.62
    cx, cy = R.p(c3)
    ex, ey = R.p(e)
    hx_, hy_ = R.p(h)
    ang = math.atan2(hy_ - ey, hx_ - ex)
    if open_ <= 0.05:
        m = f.rell(cx, cy, 3.6, 2.2, ang)
        f.add(m, 'gunmetal', z=z, rl=1.0, rs=1.4, dim=dim, line='hard', tag='buckler')
        f.add(f.rell(cx, cy, 1.0, 1.0, ang), 'brass', z=z + 0.05, flat=2, dim=dim, line=None, tag='buckler')
        return
    # the face points along the forearm's outward normal in 3D: forward when the arm is raised
    fwd = nrm((0.7, 0.1, 0.7))
    _, _, dd = proj(R.facing, tuple(fwd))
    r = 3.6 + 4.2 * min(1.0, open_)
    minor = max(1.8, r * min(1.0, abs(dd) * 0.9 + 0.25))
    n2 = R.p(tuple(fwd))
    a2 = math.atan2(n2[1], n2[0]) + math.pi / 2
    m = f.rell(cx, cy, r, minor, a2)
    f.add(m, 'gunmetal', z=z, rl=1.4, rs=2.2, dim=dim, line='hard', tag='buckler')
    f.add(f.rell(cx, cy, r * 0.42, minor * 0.42, a2), 'brass', z=z + 0.05, rl=1, rs=1.2, dim=dim, line='hard', tag='buckler')
    if open_ < 0.95:     # leaves still fanning: ribs
        for k in (-1, 1):
            a = a2 + k * 0.9
            f.detail(f.seg(cx, cy, cx + math.cos(a) * r * 0.9, cy + math.sin(a) * minor * 0.9), ('gunmetal', 0), tag='buckler')


def quiver(f, R, sh3, z, lag=0.0):
    """Back quiver over the left shoulder, slanting down to the right hip; three fletchings."""
    top3 = add3(sh3, (-6.5 - lag * 0.6, 9.0 - abs(lag) * 0.15, -9.5))
    bot3 = add3(sh3, (-6.0, -11.0, 1.5))
    (tx, ty), (bx, by) = R.p(top3), R.p(bot3)
    q = f.cap(bx, by, tx, ty, 3.0, 3.3)
    f.add(q, 'leather', z=z, rl=1.5, rs=2.2, line='hard', cast=(1, 1, 1) if z > 20 else None, tag='quiver')
    mid = (tx + (bx - tx) * 0.25, ty + (by - ty) * 0.25)
    f.add(f.cap(mid[0], mid[1], mid[0] + (bx - tx) * 0.1, mid[1] + (by - ty) * 0.1, 3.4) & q, 'gold', z=z + 0.05, flat=1, line=None, tag='quiver')
    L = math.hypot(tx - bx, ty - by) or 1
    ux, uy = (tx - bx) / L, (ty - by) / L
    px, py = -uy, ux
    for i, (o, h) in enumerate(((-2.4, 3.0), (0.2, 5.0), (2.6, 3.5))):
        x, y = tx + px * o + ux * 1.5, ty + py * o + uy * 1.5
        fl = f.poly([(x - 1.3, y), (x + ux * h - 0.2, y + uy * h - 0.2), (x + 1.3, y), (x + 1.0, y + 2), (x - 1.0, y + 2)])
        f.add(fl, 'fletch', z=z + 0.1 + i * 0.01, rl=1.2, rs=1.6, line='soft', tag='quiver')


def hand(f, x, y, z, r=3.4, dim=0, grip=None):
    """Mitten hand.  grip: screen direction (ux, uy) of a held shaft: draws the finger crease
    across it so the hand reads as closed round the shaft."""
    f.add(f.ell(x, y, r, r), 'skin', z=z, rl=1.6, rs=2.0, dim=dim, line='hard')
    if grip is not None:
        ux, uy = grip
        L = math.hypot(ux, uy) or 1
        ux, uy = ux / L, uy / L
        f.detail(f.seg(x - uy * 1.6 + ux * 0.8, y + ux * 1.6 + uy * 0.8, x + uy * 1.6 + ux * 0.8, y - ux * 1.6 + uy * 0.8), ('skin', 1))


# ------------------------------------------------------------------------------------ build
def build(f, facing, P):
    R = Rig(f, facing)
    a0, a1 = R.p((0.0, 0.0, 0.0)), R.p((P['hair'], 0.0, 0.0))
    HV[0] = (a1[0] - a0[0], a1[1] - a0[1])
    side = R.side
    b = P['bob']
    cr = P['crouch']
    lean = P['lean']
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 20.0 + P['breath'] - max(0.0, cr * 0.15), 0.0)
    head3 = (sh3[0] + lean * 0.35, sh3[1] + 16.0, 0.0)
    body_off = (P['hipx'], -cr - b, 0.0)
    # v2 twist (radians): the shoulders turn about the spine, the right (bow) shoulder forward, as an
    # archer stands side-on to the target, so the drawn arrow lies along the facing
    tw = P['twist']
    shR = add3(sh3, (0.5 + SHW * math.sin(tw), -1.0, SHW * math.cos(tw)))
    shL = add3(sh3, (0.5 - SHW * math.sin(tw), -1.0, -SHW * math.cos(tw)))
    hR = add3(P['handR'] or REST_R, body_off)
    hL = add3(P['handL'] or REST_L, body_off)
    hR, hL = _reach(shR, hR), _reach(shL, hL)       # v2 aims: a hand never leaves its arm's reach
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    tilt = P['tilt']                                      # side views: extra forward slant (px)
    # -------------------------------------------------- back gear
    qz = 28.0 if R.back else 2.0
    quiver(f, R, sh3, qz, P['lag'])
    if P['bow'] == 'back':
        # slung flat across the back, top over the left shoulder, its curve in the plane of the back
        g3 = add3(sh3, (-9.5, -6.0, 0.0))
        bz = 28.4 if R.back else 1.5
        bow3(f, R, g3, (0.0, 0.6, -0.8), (0.0, 0.8, 0.6), 0.0, bz, briar=P['briar'])
    if P['bow'] == 'ground':
        g = (7.0, 1.6, 15.0)          # dropped beside his right knee, lying across
        bow3(f, R, g, (0.35, 0.0, 1.0), (-1.0, 0.0, 0.35), 0.0, 30 if R.d(g) > 0 else 9.5,
             briar=P['briar'])
    # -------------------------------------------------- legs
    stance = P['stance']
    for lat, key in ((stance, 'footR'), (-stance, 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], ft[2] if len(ft) > 2 else lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.5, foot3[2])
        hp3 = add3(hip3, (0.0, 0.0, lat * 0.85))
        up, lo, kn3 = R.limb(hp3, ank3, 8.7, 8.5, 4.8, 4.3, 3.9, (1.0, 0.0, 0.12 * np.sign(lat)))
        far = R.far(lat)
        z = R.zleg(foot3)
        f.add(up | lo, 'trouser', z=z, rl=2, rs=3, vgrad=0.3, dim=1 if far else 0, line='hard')
        fx, fy = R.p(foot3)
        if R.diag:
            boot_3q(f, R, foot3, 'leather', z + 1, dim=1 if far else 0)
        elif side:
            boot_side(f, fx, fy, 'leather', z=z + 1, dim=1 if far else 0)
            f.add(f.cap(fx - 0.8, fy - 7.5, fx - 0.2, fy - 7.5, 3.8) & (f.Y > fy - 9.5), 'leather', z=z + 1.5, flat=1, line='soft',
                  dim=1 if far else 0)
        else:
            m = f.ell(fx, fy - 2.6, 4.9, 3.0) | f.rect(fx - 3.9, fy - 8, fx + 3.9, fy - 2)
            m &= f.Y < fy
            f.add(m, 'leather', z=z + 1, rl=1.6, rs=2.2, line='hard')
            f.add(f.rect(fx - 4.3, fy - 9, fx + 4.3, fy - 6) & f.ell(fx, fy - 7.5, 4.9, 3), 'leather', z=z + 1.5, flat=1, line='soft')
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    # seat / crotch joining the legs under the shirt
    if side:
        f.add(f.ell(hx + 0.5, hy - 1.0, 8.6, 4.4), 'trouser', z=19, rl=2, rs=3, line='hard')
    elif R.diag:
        h0, h1 = extremes(R, (hip3[0], 0, 0), hip3[1], HW - 1.0, HD - 0.5)
        f.add(f.rect(h0, hy - 6, h1, hy + 1.5) | f.ell((h0 + h1) / 2, hy, (h1 - h0) / 2, 4.2), 'trouser', z=13, rl=2, rs=3.5, vgrad=0.5, line='hard')
    else:
        f.add(f.rect(hx - 10.5, hy - 6, hx + 10.5, hy + 1.5) | f.ell(hx, hy, 10.5, 4.2), 'trouser', z=13, rl=2, rs=3.5, vgrad=0.5, line='hard')
    # -------------------------------------------------- arms behind the body (far side / reaching back)
    arms = []
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        pole = P['pole' + key] or (-1.0, -0.2, 0.7 * lat)
        z = P['z' + key] if P['z' + key] is not None else R.zarm(hh)
        arms.append((key, sh, hh, lat, pole, z))
    # -------------------------------------------------- torso
    if R.diag:
        torso_3q(f, R, P, hip3, sh3)
    elif side:
        tx = sx - hx
        body = f.ell(sx + 1.0 - tx * 0.3, sy + 6.5, 9.6, 11.5) | f.poly([(hx - 8.2, hy - 3), (sx - 8.4, sy + 2), (sx + 9.4, sy + 2), (hx + 10.0, hy - 3)])
        body &= f.Y < hy - 2.5
        f.add(body, 'cream', z=20, rl=2, rs=4, vgrad=0.4, line='hard')
        f.add(f.poly([(hx - 8.6, hy - 6), (hx + 10.2, hy - 6), (hx + 10.2, hy - 2), (hx - 8.6, hy - 2)]), 'leather', z=22, rl=1, rs=1.2, line='soft')
        f.add(f.rect(hx + 7.0, hy - 7, hx + 10.0, hy - 1), 'gold', z=23, rl=1.2, rs=1.6, line='hard')
        # pouch on the left hip: shows on the near side facing west
        if facing == 'W':
            f.add(f.rect(hx - 1.5, hy - 3, hx + 3.5, hy + 4) | f.ell(hx + 1, hy + 4, 2.5, 1.5), 'leather', z=23, rl=1.4, rs=2.0, line='hard', cast=(1, 1, 1))
            f.add(f.rect(hx, hy - 2, hx + 2, hy), 'gold', z=24, flat=2, line=None)
        # quiver strap: over the left shoulder, across the chest to the right hip
        if facing == 'W':
            f.add(f.poly([(sx - 2.5, sy - 4), (sx + 1, sy - 4), (hx + 9.5, hy - 8), (hx + 6.3, hy - 7)]), 'leather', z=25, rl=1, rs=1.4, line='soft')
        else:
            f.add(f.poly([(sx - 2.5, sy - 4), (sx + 1, sy - 4), (sx + 2, sy - 2), (sx - 1, sy - 2)]), 'leather', z=31.5, flat=1, line='soft')
        lag = P['lag']
        man = f.poly([(sx - 9.5, sy - 5), (sx - 3, sy - 8), (sx + 4, sy - 8), (sx + 9.0, sy - 4), (sx + 10.0, sy + 2),
                      (sx + 6.5, sy + 5), (sx + 1, sy + 3.5), (sx - 4, sy + 6.5), (sx - 11.0 - lag, sy + 10 + abs(lag) * 0.3),
                      (sx - 11.4 - lag * 0.5, sy + 2)])
        f.add(man, 'mantle', z=26, rl=2, rs=3.2, vgrad=0.6, line='hard', cast=(0, 1, 1), deep=True,
              tonemap=lambda X, Y, t: _fold_line(X, Y, t, sx - 5, sy, -0.35, sy - 1))
    else:
        W2 = 12.8
        body = f.ell(sx, sy + 6, W2, 12) | f.poly([(sx - 11.8, sy + 2), (sx + 11.8, sy + 2), (hx + 11.6, hy - 3), (hx - 11.6, hy - 3)])
        body &= f.Y < hy - 2.5
        f.add(body, 'cream', z=20, rl=2, rs=4, vgrad=0.4, line='hard')
        f.add(f.rect(hx - 11.8, hy - 6, hx + 11.8, hy - 2), 'leather', z=22, rl=1, rs=1.2, line='soft')
        if facing == 'S':
            f.add(f.rect(hx - 2.5, hy - 7, hx + 2.5, hy - 1), 'gold', z=23, rl=1.2, rs=1.6, line='hard')
            f.add(f.rect(hx + 4.5, hy - 3, hx + 10.5, hy + 4) | f.ell(hx + 7.5, hy + 4, 3, 1.6), 'leather', z=23, rl=1.4, rs=2.0, line='hard', cast=(1, 1, 1))
            f.add(f.rect(hx + 6.5, hy - 2, hx + 8.5, hy), 'gold', z=24, flat=2, line=None)
            f.add(f.poly([(sx + 11, sy - 4), (sx + 7.5, sy - 4), (hx - 10, hy - 6), (hx - 6.5, hy - 6)]), 'leather', z=25, rl=1, rs=1.4, line='soft')
            V = f.poly([(sx - 3.8, sy - 6), (sx + 3.8, sy - 6), (sx, sy + 5)])
            man = f.ell(sx, sy, 15.2, 7.5) | f.rect(sx - 15.2, sy - 1, sx + 15.2, sy + 4)
            hem = f.poly([(sx - 15.7, sy + 2), (sx - 12, sy + 10), (sx - 7.5, sy + 6), (sx - 3, sy + 5), (sx + 3, sy + 5),
                          (sx + 7.5, sy + 6), (sx + 12, sy + 10), (sx + 15.7, sy + 2)])
            man = ((man | hem) & (f.Y < sy + 10.5)) & ~V
            f.add(man, 'mantle', z=26, rl=2, rs=3.2, vgrad=0.6, line='hard', cast=(0, 1, 1), deep=True)
            f.add(f.poly([(sx - 3.2, sy - 5), (sx + 3.2, sy - 5), (sx, sy + 2)]), 'cream', z=27, rl=1, rs=1.5, line=None)
        else:
            f.add(f.poly([(sx - 11, sy - 4), (sx - 7.5, sy - 4), (hx + 10, hy - 6), (hx + 6.5, hy - 6)]), 'leather', z=27, rl=1, rs=1.4, line='soft')
            man = f.ell(sx, sy, 15.2, 7.5) | f.rect(sx - 15.2, sy - 1, sx + 15.2, sy + 4)
            man |= f.poly([(sx - 15.7, sy + 2), (sx - 13, sy + 11), (sx - 6.5, sy + 9), (sx, sy + 12), (sx + 6.5, sy + 9),
                           (sx + 13, sy + 11), (sx + 15.7, sy + 2)])
            f.add(man, 'mantle', z=26, rl=2, rs=3.2, vgrad=0.7, line='hard', cast=(0, 1, 1), deep=True,
                  tonemap=lambda X, Y, t: _cape_folds(X, Y, t, sx, sy))
    # -------------------------------------------------- billhook at the right hip (or in hand)
    if P['hook'] == 'hip':
        g3 = add3(hip3, (-1.5 if not (side or R.diag) else -4.5, 3.5, 12.6 if not (side or R.diag) else 11.5))
        dd = R.d(g3)
        z = 24.5 if dd > 2 else 13
        t = min(1.0, max(0.0, (19.0 - hip3[1]) / 8.0))     # v2: kneeling, the blade swings back off the ground
        hd = tuple(np.array((-0.15, -1.0, 0.0)) * (1 - t) + np.array((-1.0, -0.3, 0.1)) * t)
        billhook(f, R, g3, hd, z, dim=1 if R.far(1) else 0)
    # -------------------------------------------------- arms
    out = {}
    for key, sh, hh, lat, pole, z in arms:
        far = R.far(lat)
        up, lo, el3 = R.limb(sh, hh, 8.6, 8.4, 3.7, 3.3, 3.0, pole)
        f.add(up, 'cream', z=z, rl=1.6, rs=2.4, dim=1 if far else 0, line='hard', cast=(1, 1, 1))
        f.add(lo, 'cream', z=z + 0.1, rl=1.6, rs=2.4, dim=1 if far else 0, line='hard', cast=(1, 1, 1))
        px, py = R.p(sh)
        f.add(f.ell(px - 0.5, py + 0.5, 4.9, 4.7) & (f.Y < py + 3.2), 'mantle', z=max(31, z + 0.2) if not far else z + 0.2,
              rl=1.6, rs=2.4, line='soft', dim=1 if far else 0)
        out[key] = (el3, hh, z, far)
    # buckler on the right forearm
    el3, hh, z, far = out['R']
    buckler(f, R, el3, hh, P['buckler'], z + 0.3, dim=1 if far else 0)
    # hands and what they hold
    for key in ('R', 'L'):
        el3, hh, z, far = out[key]
        hxp, hyp = R.p(hh)
        grip = None
        if key == 'R' and P['bow'] == 'hand':
            u3 = P['bowu'] or (0.18, 1.0, 0.0)
            u3 = _clear_ground(hh, u3)
            n3 = P['bown'] or (0.62, 0.0, 0.78)
            bz = P['bowz'] if P['bowz'] is not None else z + 0.5
            nk3 = hL if P['nock'] == 'hand' else P['nock']      # v2: the string is drawn to the draw hand
            nk = bow3(f, R, hh, u3, n3, P['draw'], bz, nock3=nk3, arrow=P['arrow'], briar=P['briar'])
            g2 = R.p(add3(hh, tuple(nrm(u3))))
            grip = (g2[0] - hxp, g2[1] - hyp)
            if P['arrow']:
                tip = R.p(add3(nk, tuple(nrm(n3) * 21)))
                f.anchor('arrow_tip', *tip)
        if key == 'R' and P['hook'] == 'hand':
            d3 = P['hookdir']
            tip = billhook(f, R, hh, d3, z + 0.4, dim=1 if far else 0)
            f.anchor('strike', *tip)
            g2 = R.p(add3(hh, tuple(nrm(d3))))
            grip = (g2[0] - hxp, g2[1] - hyp)
        if key == 'L' and P['qarrow']:
            arrow3(f, R, add3(hh, (0.3, 9.0, 0.0)), (0.1, -1.0, 0.0), z + 0.6, length=19)
        hand(f, hxp, hyp, z + 0.8, r=3.4 if not far else 3.2, dim=1 if far else 0, grip=grip)
    # -------------------------------------------------- head
    hx2, hy2 = R.p(head3)
    if R.diag:
        head_3q(f, R, P, head3)
    elif facing == 'S':
        head_south(f, P, hx2, hy2)
    elif facing == 'N':
        head_north(f, P, hx2, hy2)
    else:
        head_side(f, P, hx2, hy2)
    if P['shot']:
        x, y = R.p(P['shot'])
        arrow3(f, R, P['shot'], (1.0, 0.0, 0.0), 45, tag='arrow')


# ------------------------------------------------------------------------------------ heads
HV = [(0.0, 0.0)]             # hair / beard sway offset of the drawing being built (set in build)


def hair_clumps(f, clumps, z0, line_first=3):
    for i, (cx, cy, r) in enumerate(clumps):
        if i >= line_first:          # the outer and lower clumps trail (secondary motion)
            cx, cy = cx + HV[0][0] * 0.6, cy + HV[0][1] * 0.6
        f.add(f.ell(cx, cy, r, r * 0.92), 'grey', z=z0 + i * 0.01, rl=1.3, rs=2.0, ts=0.30,
              line=None if i >= line_first else 'hard', cast=(1, 1, 1) if i >= line_first else None)


def _brows(f, xs, ey, P, w=4):
    lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)    # 1: set (frown, lower), 2: raised (hurt)
    for x in xs:
        f.detail(f.rect(x, ey - 2 + lift, x + w, ey - 1 + lift), ('grey', 1))


def head_south(f, P, x0, hy):
    f.add(f.ell(x0 - 10.4, hy + 1, 2.2, 3.0) | f.ell(x0 + 10.4, hy + 1, 2.2, 3.0), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy + 0.5, 9.8, 9.6), 'skin', z=40, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1))
    beard = f.ell(x0, hy + 8, 9.2, 7.2) | f.ell(x0 - 7.6, hy + 4.5, 2.9, 4.2) | f.ell(x0 + 7.6, hy + 4.5, 2.9, 4.2)
    beard &= f.Y > hy + 2.5
    beard &= ~f.ell(x0, hy + 2.6, 5.6, 3.2)
    beard |= f.poly([(x0 - 4.5, hy + 12), (x0 + 4.5, hy + 12), (x0 + 1 + HV[0][0], hy + 17 + HV[0][1]), (x0 - 1 + HV[0][0], hy + 17 + HV[0][1])])
    f.add(beard, 'grey', z=41, rl=1.6, rs=3.2, vgrad=0.5, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _beard_strands(X, Y, t, hy, x0s=(x0 - 5, x0 - 1.5, x0 + 2.5, x0 + 5.5)))
    f.add(f.ell(x0 - 2.9, hy + 5.4, 3.5, 1.8), 'grey', z=43, rl=1.2, rs=1.6, line='shade')
    f.add(f.ell(x0 + 2.9, hy + 5.4, 3.5, 1.8), 'grey', z=43, rl=1.2, rs=1.6, line='shade')
    hair_clumps(f, [(x0 - 6.5, hy - 9.5, 4.2), (x0 + 1, hy - 10.6, 4.5), (x0 + 7.5, hy - 8.5, 4.0),
                    (x0 - 10.4, hy - 4, 3.5), (x0 + 10.4, hy - 3.5, 3.5),
                    (x0 - 4.8, hy - 5.2, 4.1), (x0 + 3.2, hy - 5.8, 4.3),
                    (x0 - 11.2, hy + 0.8, 2.4), (x0 + 11.2, hy + 0.8, 2.4)], 44)
    ey = hy - 1
    e1, e2 = x0 - 5, x0 + 3
    if P['face'] == 'shut':
        f.detail(f.rect(e1, ey + 1, e1 + 3, ey + 2), EYE)
        f.detail(f.rect(e2 - 1, ey + 1, e2 + 2, ey + 2), EYE)
    elif not P['blink']:
        eye(f, e1, ey, 3)
        eye(f, e2, ey, 3)
    else:
        f.detail(f.rect(e1, ey + 2, e1 + 2, ey + 3), EYE)
        f.detail(f.rect(e2, ey + 2, e2 + 2, ey + 3), EYE)
    _brows(f, (x0 - 6, x0 + 2), ey, P)
    f.detail(f.rect(x0 - 1, hy + 2, x0 + 1, hy + 3), ('skin', 3))
    f.detail(f.rect(x0, hy + 3, x0 + 2, hy + 4), ('skin', 1))
    f.detail(f.rect(x0 - 8, hy + 2, x0 - 6, hy + 3), ('blush', 2))
    f.detail(f.rect(x0 + 6, hy + 2, x0 + 8, hy + 3), ('blush', 2))


def head_north(f, P, x0, hy):
    f.add(f.ell(x0 - 10.4, hy + 1, 2.2, 3.0) | f.ell(x0 + 10.4, hy + 1, 2.2, 3.0), 'skin', z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0 - 7.2, hy + 6, 3.2, 3.5) | f.ell(x0 + 7.2, hy + 6, 3.2, 3.5), 'grey', z=40, rl=1.2, rs=2.2, line='hard')
    f.add(f.ell(x0, hy, 10.4, 9.6), 'grey', z=41, rl=2, rs=3.2, line='hard', cast=(0, 2, 1))
    hair_clumps(f, [(x0 - 6.5, hy - 9.5, 4.2), (x0 + 1, hy - 10.6, 4.5), (x0 + 7.5, hy - 8.5, 4.0),
                    (x0 - 10.4, hy - 4, 3.5), (x0 + 10.4, hy - 3.5, 3.5),
                    (x0 - 4.8, hy - 4, 4.4), (x0 + 3.2, hy - 4.8, 4.6), (x0 + 8.8, hy + 0.5, 3.1), (x0 - 9.0, hy + 1.5, 3.1),
                    (x0 - 1.5, hy + 2.2, 4.2), (x0 + 4.8, hy + 3.2, 3.5)], 44)


def head_side(f, P, x0, hy):
    hx = x0
    f.add(f.ell(hx + 2.2, hy + 0.4, 8.2, 9.4), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(hx + 9.8, hy + 2.0, 1.8, 1.7), 'skin', z=40.5, rl=1, rs=1.2, line='hard')
    beard = f.ell(hx + 3.8, hy + 8.2, 6.8, 6.8) | f.ell(hx - 1.8, hy + 4.5, 3.0, 4.5)
    beard &= f.Y > hy + 2.6
    beard &= ~f.ell(hx + 7.0, hy + 3.0, 3.9, 2.6)
    beard |= f.poly([(hx + 1, hy + 12), (hx + 8.5, hy + 12), (hx + 5.5 + HV[0][0], hy + 16.5 + HV[0][1]), (hx + 3.5 + HV[0][0], hy + 16.5 + HV[0][1])])
    f.add(beard, 'grey', z=41, rl=1.6, rs=3.0, vgrad=0.5, line='hard', cast=(0, 2, 1),
          tonemap=lambda X, Y, t: _beard_strands(X, Y, t, hy, x0s=(hx + 1, hx + 4, hx + 6.5)))
    f.add(f.ell(hx + 7.4, hy + 5.4, 3.5, 1.8), 'grey', z=43, rl=1.2, rs=1.6, line='shade')
    hair_clumps(f, [(hx - 4.5, hy - 9.5, 4.2), (hx + 2, hy - 10.6, 4.4), (hx + 7.0, hy - 8, 3.6),
                    (hx - 8.6, hy - 4, 3.8), (hx - 8.0, hy + 1.5, 3.3),
                    (hx - 2.5, hy - 5.2, 4.1), (hx + 4.4, hy - 5.8, 3.7), (hx + 8.2, hy - 4.4, 2.5),
                    (hx - 4.8, hy + 1, 2.9)], 44)
    f.add(f.ell(hx - 1.8, hy + 1.0, 2.0, 2.8), 'skin', z=45, rl=1, rs=1.2, line='hard')
    f.dot(hx - 1.8, hy + 1, ('skin', 1))
    ey = hy - 1
    ex = hx + 5
    if P['face'] == 'shut':
        f.detail(f.rect(ex - 1, ey + 1, ex + 2, ey + 2), EYE)
    elif not P['blink']:
        eye(f, ex, ey, 3)
    else:
        f.detail(f.rect(ex, ey + 2, ex + 2, ey + 3), EYE)
    _brows(f, (ex - 1,), ey, P)
    f.detail(f.rect(hx + 4.5, hy + 2, hx + 6.5, hy + 3), ('blush', 2))


# ------------------------------------------------------------------------------------ folds
def _fold_line(X, Y, t, x0, y0, slope, ymin):
    out = t.copy()
    m = (abs(X - x0 - (Y - y0) * slope) < 0.6) & (Y > ymin)
    out[m & (t >= 2)] = 1
    return out


def _beard_strands(X, Y, t, hy, x0s):
    out = t.copy()
    for x0 in x0s:
        m = (abs(X - x0 - (Y - hy) * 0.06) < 0.5) & (Y > hy + 9) & (Y < hy + 13)
        out[m & (t >= 2)] = 1
    return out


def _cape_folds(X, Y, t, sx, sy):
    out = t.copy()
    for k in (-1, 1):
        m = (abs(X - sx - 6.5 * k - (Y - sy - 4) * 0.25 * k) < 0.6) & (Y > sy + 2)
        out[m & (t >= 1)] = np.maximum(out[m & (t >= 1)] - 1, 1)
    return out


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in FLIP))
    f.despeckle = True               # v2: no lone rim or shade pixels (checks.py lone)
    build(f, facing, P)
    return f


# ================================================================== contract v2: 3/4 facings
# SE, NE (and their mirrored SW, NW) are built from the same 3D body: the torso is an elliptic
# cylinder (half width W across, half depth D front to back); every feature on it (buckle, pouch,
# strap, mantle hem, V neck) is a point on that surface, projected, and drawn only where its
# surface faces the camera.  The head is a sphere carrying the S and N heads' clumps and features.
TW, TD = 12.8, 9.6             # torso half width (lat) and half depth (fwd) at the chest
HW, HD = 11.6, 9.0             # at the hips
MW, MD = 15.2, 11.5            # mantle over the shoulders


def ring(R, c3, up, w, d, th):
    """Screen point and facing (vis) of the cylinder surface point at angle th (0 = front,
    + toward the right side) at height up above c3."""
    p3 = (c3[0] + d * math.cos(th), up, c3[2] + w * math.sin(th))
    return R.p(p3), R.vis((math.cos(th) / d, 0.0, math.sin(th) / w))


def arc(R, c3, up, w, d, n=48, vmin=0.0, ths=None):
    """Visible part of a ring as screen points, in order of th."""
    out = []
    for th in (ths if ths is not None else np.linspace(-math.pi, math.pi, n)):
        (x, y), v = ring(R, c3, up, w, d, th)
        if v >= vmin:
            out.append((th, x, y, v))
    return out


def extremes(R, c3, up, w, d):
    xs = [ring(R, c3, up, w, d, th)[0][0] for th in np.linspace(-math.pi, math.pi, 72)]
    return min(xs), max(xs)


def band(f, R, c3, up0, up1, w, d, vmin=-0.02):
    """Polygon of the visible band of the cylinder between heights up0 < up1."""
    top = arc(R, c3, up1, w, d, 64, vmin)
    bot = arc(R, c3, up0, w, d, 64, vmin)
    if len(top) < 2:
        return None
    # the visible arc can wrap round th = +-pi: order by screen x instead
    top = sorted(top, key=lambda q: q[1])
    bot = sorted(bot, key=lambda q: q[1])
    pts = [(x, y) for _, x, y, _ in top] + [(x, y) for _, x, y, _ in reversed(bot)]
    return f.poly(pts)


def path_on(R, c3, w, d, a, b, n=14):
    """Points along the surface from a = (th, up) to b = (th, up), with their visibility."""
    out = []
    for i in range(n + 1):
        t = i / n
        th = a[0] + (b[0] - a[0]) * t
        up = a[1] + (b[1] - a[1]) * t
        out.append(ring(R, c3, up, w, d, th))
    return out


def strap_3q(f, R, pts, z, r=1.5, vmin=0.05):
    m = None
    for ((x0, y0), v0), ((x1, y1), v1) in zip(pts[:-1], pts[1:]):
        if min(v0, v1) < vmin:
            continue
        c = f.cap(x0, y0, x1, y1, r)
        m = c if m is None else m | c
    if m is not None:
        f.add(m, 'leather', z=z, rl=1, rs=1.4, line='soft')


def torso_3q(f, R, P, hip3, sh3):
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    hup, sup = hip3[1], sh3[1]
    cs = (sh3[0], 0, 0)
    ch = (hip3[0], 0, 0)
    x0, x1 = extremes(R, cs, sup - 6, TW, TD)
    h0, h1 = extremes(R, ch, hup + 3, HW, HD)
    ex, ey = (x0 + x1) / 2, sy + 6
    body = f.ell(ex, ey, (x1 - x0) / 2, 12) | f.poly([(x0 + 1, sy + 2), (x1 - 1, sy + 2), (h1, hy - 3), (h0, hy - 3)])
    body &= f.Y < hy - 2.5
    f.add(body, 'cream', z=20, rl=2, rs=4, vgrad=0.4, line='hard')
    belt = band(f, R, ch, hup + 2, hup + 6, HW + 0.3, HD + 0.3)
    if belt is not None:
        f.add(belt & (f.Y < hy - 1.5), 'leather', z=22, rl=1, rs=1.2, line='soft')
    # buckle at the front, pouch on the left hip
    (bx, by), bv = ring(R, ch, hup + 4, HW + 0.4, HD + 0.4, 0.0)
    if bv > 0.15:
        w = 2.5 * min(1.0, 0.35 + bv)
        f.add(f.rect(bx - w, by - 3, bx + w, by + 3), 'gold', z=23, rl=1.2, rs=1.6, line='hard')
    (px, py), pv = ring(R, ch, hup + 3, HW + 0.8, HD + 0.8, -0.62)
    if pv > 0.05:
        w = 3.0 * min(1.0, 0.3 + pv)
        f.add(f.rect(px - w, py, px + w, py + 7) | f.ell(px, py + 7, w, 1.6), 'leather', z=23, rl=1.4, rs=2.0, line='hard', cast=(1, 1, 1))
        f.add(f.rect(px - 1, py + 1, px + 1, py + 3), 'gold', z=24, flat=2, line=None)
    # quiver strap: left shoulder -> right hip, on the front and on the back
    strap_3q(f, R, path_on(R, cs, TW + 0.6, TD + 0.6, (-1.05, sup + 1), (0.95, hup + 5)), 25)
    strap_3q(f, R, path_on(R, cs, TW + 0.6, TD + 0.6, (-math.pi + 1.05, sup + 1), (-math.pi - 0.95, hup + 5)), 27)
    # mantle: a short cape over the shoulders, longer at the back, a V at the throat
    m0, m1 = extremes(R, cs, sup, MW, MD)
    mx = (m0 + m1) / 2
    man = f.ell(mx, sy, (m1 - m0) / 2, 7.5) | f.rect(m0, sy - 1, m1, sy + 4)
    hem = []
    for th in np.linspace(-math.pi, math.pi, 49):
        (x, y), v = ring(R, cs, sup - 2, MW + 0.5, MD + 0.5, th)
        if v < -0.05:
            continue
        a = abs(th)
        drop = 4.5 + 6.0 * min(1.0, a / 2.2) + 2.0 * (abs(math.sin(th * 3.0)) > 0.85)
        if a < 0.35:
            drop = 5.0
        hem.append((x, y + drop, x, y))
    hem.sort(key=lambda q: q[0])
    if len(hem) > 2:
        man |= f.poly([(x, y0) for x, _, _, y0 in hem] + [(x, y) for x, y, _, _ in reversed(hem)])
        man |= f.poly([(x, y) for x, y, _, _ in hem] + [(hem[-1][0], sy), (hem[0][0], sy)])
    man &= f.Y < sy + 12
    (vx, vy), vv = ring(R, cs, sup + 5, MW, MD, 0.0)
    V = None
    if vv > 0.2:
        w = 3.8 * min(1.0, vv + 0.2)
        V = f.poly([(vx - w, vy - 1), (vx + w, vy - 1), (vx, vy + 10)])
        man &= ~V
    f.add(man, 'mantle', z=26, rl=2, rs=3.2, vgrad=0.6, line='hard', cast=(0, 1, 1), deep=True,
          tonemap=lambda X, Y, t: _cape_folds_3q(X, Y, t, R, cs, sup))
    if V is not None:
        w = 3.2 * min(1.0, vv + 0.2)
        f.add(f.poly([(vx - w, vy), (vx + w, vy), (vx, vy + 7)]), 'cream', z=27, rl=1, rs=1.5, line=None)


def _cape_folds_3q(X, Y, t, R, cs, sup):
    out = t.copy()
    for th in (-2.3, -1.4, 1.4, 2.3):
        (x, y), v = ring(R, cs, sup - 4, MW, MD, th)
        if v < 0.15:
            continue
        m = (abs(X - x - (Y - y) * 0.2 * np.sign(th)) < 0.6) & (Y > y)
        out[m & (t >= 1)] = np.maximum(out[m & (t >= 1)] - 1, 1)
    return out


def boot_3q(f, R, foot3, mat_, z, dim=0):
    fx, fy = R.p(foot3)
    tx, ty = R.p(add3(foot3, (2.2, 0.0, 0.0)))
    dx, dy = tx - fx, ty - fy
    m = f.ell(fx + dx, fy - 2.6 + dy * 0.5, 4.9, 3.0) | f.rect(fx - 3.7, fy - 8, fx + 3.7, fy - 2)
    m &= f.Y < fy + max(0.0, dy)
    f.add(m, mat_, z=z, rl=1.6, rs=2.2, dim=dim, line='hard')
    f.add(f.rect(fx - 4.1, fy - 9, fx + 4.1, fy - 6) & f.ell(fx, fy - 7.5, 4.7, 3), mat_, z=z + 0.5, flat=1, line='soft', dim=dim)


def _sph(R, c3, fwd, up, lat):
    p = R.p((c3[0] + fwd, c3[1] + up, c3[2] + lat))
    return p, R.d((fwd, up * 0.0, lat))


def _clumps3(front, back, rr=10.6):
    """S clumps (front hemisphere) and N clumps (back) as 3D sphere points (fwd, up, lat, r)."""
    out = []
    for cx, cy, r in front:
        out.append((math.sqrt(max(0.0, rr * rr - cx * cx - cy * cy)) * 0.8, -cy, -cx, r))
    for cx, cy, r in back:
        out.append((-math.sqrt(max(0.0, rr * rr - cx * cx - cy * cy)) * 0.8, -cy, cx, r))
    return out


HAIR_S = [(-6.5, -9.5, 4.2), (1, -10.6, 4.5), (7.5, -8.5, 4.0), (-10.4, -4, 3.5), (10.4, -3.5, 3.5),
          (-4.8, -5.2, 4.1), (3.2, -5.8, 4.3), (-11.2, 0.8, 2.4), (11.2, 0.8, 2.4)]
HAIR_N = [(-6.5, -9.5, 4.2), (1, -10.6, 4.5), (7.5, -8.5, 4.0), (-10.4, -4, 3.5), (10.4, -3.5, 3.5),
          (-4.8, -4, 4.4), (3.2, -4.8, 4.6), (8.8, 0.5, 3.1), (-9.0, 1.5, 3.1), (-1.5, 2.2, 4.2), (4.8, 3.2, 3.5)]


def head_3q(f, R, P, head3):
    """Bramble's head in SE / NE (SW / NW mirrored) from the sphere: face features where they
    face the camera, the near ear, hair clumps from the S and N heads by depth."""
    c3 = head3
    (x0, hy) = R.p(c3)
    hy = hy                          # head centre on screen
    back = R.back
    near = 1 if not R.far(1) else -1          # lateral sign of the near side
    f.add(f.ell(x0, hy + 0.5, 9.8, 9.6), ('skin' if not back else 'grey'), z=40, rl=2.0, rs=3.2, line='hard', cast=(0, 2, 1))
    # near ear
    (ex, ey), _ = _sph(R, c3, -0.5, -1.0, 10.2 * near)
    f.add(f.ell(ex, ey, 2.0, 2.8), 'skin', z=45, rl=1, rs=1.2, line='hard')
    f.dot(ex, ey, ('skin', 1))
    # beard (front-facing points only)
    parts_ = [((6.6, -8.0, 0.0), 7.6, 6.6), ((4.2, -4.5, 7.4), 3.0, 4.3), ((4.2, -4.5, -7.4), 3.0, 4.3)]
    bm = None
    for (fw, up, lat), rx, ry in parts_:
        (x, y), d = _sph(R, c3, fw, up, lat)
        if d < -2.5:
            continue
        c = f.ell(x, y, rx * (0.8 if abs(lat) < 1 else 1.0), ry)
        bm = c if bm is None else bm | c
    if bm is not None:
        bm &= f.Y > hy + 2.5
        (mx, my), md = _sph(R, c3, 9.0, -2.6, 0.0)
        if md > 0:
            bm &= ~f.ell(mx, my, 4.4, 3.0)
            (gx, gy), _ = _sph(R, c3, 7.0, -12.0, 0.0)
            bm |= f.poly([(gx - 4, gy), (gx + 4, gy), (gx + 1 + HV[0][0], gy + 5 + HV[0][1]), (gx - 1 + HV[0][0], gy + 5 + HV[0][1])])
        f.add(bm, 'grey', z=41 if not back else 39.5, rl=1.6, rs=3.2, vgrad=0.5, line='hard', cast=(0, 2, 1),
              tonemap=lambda X, Y, t: _beard_strands(X, Y, t, hy, x0s=(mx - 3, mx, mx + 3)) if md > 0 else t)
    if not back:
        for lat in (2.9, -2.9):
            (x, y), d = _sph(R, c3, 9.4, -5.4, lat)
            if d > 0:
                f.add(f.ell(x, y, 3.2 if lat * near > 0 else 2.6, 1.8), 'grey', z=43, rl=1.2, rs=1.6, line='shade')
    # hair: a cap over the skull under the clumps, so no skin shows between them
    f.add(f.ell(x0, hy - 5.5, 9.6, 5.6), 'grey', z=43.9, rl=1.3, rs=2.0, ts=0.30, line=None)
    for i, (fw, up, lat, r) in enumerate(sorted(_clumps3(HAIR_S, HAIR_N), key=lambda q: R.d((q[0], 0, q[2])))):
        (x, y), d = _sph(R, c3, fw, up, lat)
        if d < -6.5 and up < 6:
            continue
        if up < 6:
            x, y = x + HV[0][0] * 0.6, y + HV[0][1] * 0.6
        f.add(f.ell(x, y, r, r * 0.92), 'grey', z=44 + i * 0.01, rl=1.3, rs=2.0, ts=0.30,
              line='hard' if i < 3 else None, cast=(1, 1, 1) if i >= 3 else None)
    if back:
        return
    # eyes, brows, nose, blush
    for lat in (4.0, -4.0):
        (x, y), d = _sph(R, c3, 8.6, 1.0, lat)
        if d < 1.0:
            continue
        x = round(x - 1)
        if P['face'] == 'shut':
            f.detail(f.rect(x - 0.5, y + 1, x + 2.5, y + 2), EYE)
        elif not P['blink']:
            eye(f, x, y, 3)
        else:
            f.detail(f.rect(x, y + 2, x + 2, y + 3), EYE)
        lift = {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)
        f.detail(f.rect(x - 1, y - 2 + lift, x + 3, y - 1 + lift), ('grey', 1))
    (nx, ny), _ = _sph(R, c3, 9.8, -2.0, 0.0)
    f.detail(f.rect(nx - 1, ny, nx + 1, ny + 1), ('skin', 3))
    f.detail(f.rect(nx, ny + 1, nx + 2, ny + 2), ('skin', 1))
    (bx, by), _ = _sph(R, c3, 7.5, -2.0, 6.5 * near)
    f.detail(f.rect(bx - 1, by, bx + 1, by + 1), ('blush', 2))
