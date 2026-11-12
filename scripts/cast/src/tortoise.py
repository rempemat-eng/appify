"""Mossback tortoise (shield): an old wood tortoise with a high domed bark-brown shell grown over
with moss, a heavy brow plate over a beaked head, stubby scaled legs.  The Starfall shard is
lodged in the crown of the shell, in the moss.  About 30 px tall, 44 long; slow and wide.

Reads by silhouette as the dome.  Its front is guarded (the brow plate and the shell lip).
Telegraph (0.95 s): it draws its head in under the brow plate and rears its front off the ground
(the stomp's wind-up, matching the ring on the ground).  Attack: the slam, front feet down, a
dust ring and a short shove.  Freed: the shard pops out of the moss, it pokes its head out, blinks
and plods off."""
import math
import numpy as np
from ew import mat
import critter as C
from critter import add3

mat('shell',    ['#24160E', '#43291A', '#6A4428', '#8E643A', '#B0844E'])
mat('scale',    ['#26231A', '#423C2A', '#625A3E', '#847A56', '#A69A72'])
mat('beak',     ['#3A3020', '#665838', '#948254', '#BEAE7C'])

ID = 'tortoise'
NAME = 'Mossback tortoise'
HEIGHT = 41
BAND = (36, 52)
ONE_BODY = True
DETACHED_OK = ('shard', 'shardglow', 'cream', 'gold', 'tell', 'soil', 'dirt', 'lamp')
SCALE = 1.22


def P0(**k):
    return C.P0(**dict(dict(neck=1.0), **k))


def build(f, facing, P):
    R = C.Rig(f, facing)
    lat = P['lat'] + P['shake']
    base = 7.5 - P['bob']
    cf, ch = P['crouchF'], P['crouchH']
    if facing in 'SN':
        cf = cf * 0.5          # end-on a rear lifts the shell less than it shows from the side
    front3 = (7.0, base - cf, lat)
    hind3 = (-7.0, base - ch, lat)
    body3 = (0.0, (front3[1] + hind3[1]) / 2, lat)
    ang = math.atan2(cf - ch, 14.0) + P['pitch']
    hips = [add3(front3, (2.0, 1.0, 8.0)), add3(front3, (2.0, 1.0, -8.0)), add3(hind3, (-1.0, 1.0, 8.0)), add3(hind3, (-1.0, 1.0, -8.0))]   # hips well up inside the shell
    foot_fwd = [P.get('fFR', 9.5), P.get('fFL', 9.5), P.get('fHR', -8.0), P.get('fHL', -8.0)]
    feet = C.legs(f, R, P, hips, foot_fwd, 'scale', 10, r0=3.6, r1=3.0, hoof='crack', tonemap=C.warts(seed=2.0, n_per=0.3))
    # claws: three pale claws at the front of each near foot
    for i, (fx, fy) in enumerate(feet):
        if R.far(hips[i][2]) and facing in 'EW':
            continue
        if facing in 'EW':
            pts = [(fx + 2.5, fy - 1), (fx + 3.5, fy - 1)]
        elif facing == 'S':
            pts = [(fx - 2, fy - 1), (fx, fy - 1), (fx + 2, fy - 1)]
        else:
            continue
        for (cx, cy) in pts:
            f.dot(cx, cy, ('cream', 2), z=11 + 0.1 * i, tag='claw')
    # head and neck: out (neck 1) or drawn in under the brow plate (neck 0)
    nk = P['neck']
    hd = P['head']
    head3 = add3(front3, (7.0 + 6.0 * nk + hd[0], (1.0 if facing in 'EW' else 3.5) + hd[1], 0.0))
    zh = 24 if facing != 'N' else 12
    if nk > 0.15:
        (nx, ny), (hx, hy) = R.p(add3(front3, (5.0, 2.0, 0.0))), R.p(head3)
        f.add(f.cap(nx, ny, hx, hy, 3.4, 3.0), 'scale', z=zh - 0.5, rl=1.2, rs=1.8, line='hard')
    _, (hx, hy) = C.blob(f, R, head3, 9.5, 8.5, 8.0, 'scale', zh, rl=1.2, rs=1.8, vgrad=0.3, cast=None, tonemap=C.warts(seed=3.0, n_per=0.3))
    bx, by = R.p(add3(head3, (3.8, -0.8, 0.0)))
    if facing in 'EW':
        f.add(f.poly([(bx - 2.5, by - 3.0), (bx + 3.0, by - 0.5), (bx + 0.5, by + 1.0), (bx - 2.0, by + 2.5)]), 'beak', z=zh + 0.2, rl=1, rs=1, line='hard')
    elif facing == 'S':
        f.add(f.poly([(bx - 2.5, by), (bx + 2.5, by), (bx, by + 3)]), 'beak', z=zh + 0.2, rl=1, rs=1, line='hard')
    if facing != 'N':
        if facing == 'S':
            for s in (1, -1):
                x, y = R.p(add3(head3, (2.0, 1.2, 2.6 * s)))
                C.eye(f, x, y, P['calm'], P['blink'], size=1)
        else:
            x, y = R.p(add3(head3, (2.0, 1.0, 3.5)))
            C.eye(f, x, y, P['calm'], P['blink'], size=1)
            mx, my = R.p(add3(head3, (2.5, -2.0, 3.5)))
            f.detail(f.seg(mx - 2, my, mx + 3, my + 1), ('scale', 0), z=zh + 0.3)
    f.anchor('strike', *R.p(add3(head3, (5.0, -3.0, 0.0))))
    # the shell: a high dome with a darker lip, scutes, moss over the crown
    sc3 = add3(body3, (0.0, 6.5, 0.0))
    shell_m = C.blob_mask(f, R, sc3, 30.0, 27.0, 22.0, ang)
    lip_y = R.p(add3(body3, (0.0, 1.0, 0.0)))[1]
    zs = 20
    shm = shell_m & (f.Y < lip_y + 4.5)
    f.add(shm, 'shell', z=zs, rl=2.4, rs=3.4, vgrad=0.5, line='hard', cast=(1, 2, 1), deep=True,
          tonemap=C.planes(f, shm, C.px(f, _scutes_at(*[v * f.scale for v in R.p(sc3)], calm=(facing == 'S'))), dark=0.6), tag='shell')
    # the shell's rim: marginal plates along its lower edge, notched, one tone darker, and a stub of
    # tail at the back
    rim_y = lip_y + 4.5
    rim = shell_m & (f.Y < rim_y) & (f.Y >= rim_y - 2.6)
    notch = (np.floor(f.X * f.scale) % 5 == 0)
    f.detail(rim & ~notch, ('shell', 1), z=zs + 0.2, tag='shell')
    f.detail(rim & notch, ('shell', 0), z=zs + 0.2, tag='shell')
    tl3 = add3(hind3, (-9.0, 1.0, 0.0))
    tx, ty = R.p(tl3)
    f.add(f.poly([(tx - 1.6, ty - 1.2), (tx + 1.6, ty - 1.2), (tx, ty + 1.8)]) if facing in 'SN' else
          f.poly([(tx + 2.0, ty - 1.4), (tx - 2.5, ty + 0.5), (tx + 2.0, ty + 1.2)]),
          'scale', z=(zs + 0.3 if facing == 'N' else 9), rl=1, rs=1, line='hard')
    # the guarded front: a brow plate over the head (a heavy lip on the shell's front)
    pl3 = add3(front3, (6.5, 6.0, 0.0))
    _, _ = C.blob(f, R, pl3, 6.0, 15.0, 6.5, 'shell', zh + (0.5 if facing != 'N' else -1), ang=ang, rl=1.4, rs=2.0, vgrad=0.4, cast=None, tag='shell')
    # moss over the crown, with a ragged lower edge
    top_y = R.p(add3(sc3, (0.0, 11.0, 0.0)))[1]
    edge = top_y + 5.0 + 1.4 * np.sin(f.X * 0.9) + 1.0 * np.sin(f.X * 2.3 + 1.0)
    f.add(shell_m & (f.Y < edge), 'moss', z=zs + 0.5, rl=1.6, rs=2.4, vgrad=0.4, line='soft', deep=True, tag='moss',
          tonemap=C.px(f, _tufts))
    # the shard in the crown, in the moss
    C.shard(f, R, add3(sc3, (-1.0, 9.0, 1.0)), (-0.1, 1.0, 0.2), 8.0, P, 22)
    # the stomp's dust (attack; 10 Nov K1, 12 Nov K1r): round earth-toned puffs thrown out along the
    # forefeet's ground line, rising and breaking up over the four drawings, with a few pebbles.
    # Near the camera they sit in front of the feet, over only their bottom rows; the far side's
    # go behind the legs and show beside the shell. From behind (N) the forefeet are the far pair.
    if P.get('dust') is not None and P['dust'] < 1:
        t = P['dust']
        for i in (0, 1):
            fx, fy = feet[i]
            far = R.far(hips[i][2]) or facing == 'N'
            gy = (max(q[1] for q in feet) if facing == 'N' else fy) + (1.4 if not far else 0.0)
            if facing in 'EW':
                pts = [(fx + 5.5, gy, 2.3), (fx - 5.0, gy, 2.0), (fx + 1.0, gy + 0.6, 1.6)]
                drift = 1.0
            else:
                s_ = 1 if fx > 0 else -1
                ox = 11.0 if facing == 'N' else 3.0
                pts = [(fx + (ox + 2.5) * s_, gy, 2.3), (fx + (ox - 1.0) * s_, gy + 0.6, 1.8)]
                drift = 0.6 * s_
            if far:
                pts = pts[:2]
            C.puffs(f, pts, t, 'soil', z=(5 if far else 58), drift=drift, rise=1.2,
                    pebbles=() if far else [(fx + 2.0, gy - 0.5), (fx - 2.0, gy - 0.3)])
    if P.get('stars') is not None:
        x, y = R.p(add3(sc3, (0, 15, 0)))
        C.stars(f, x, y, P['stars'], tip=f.anchors.get('shard'))


_FIELD = {}
BIG_S = 1.4         # S: the plates face-on, larger and fewer (10 Nov audit, N1)


def _scute_field(big=1.0):
    """Seams and lit rims of the shell plates on a fixed grid (computed once): an offset grid of
    cells, the seam where the nearest and second nearest centres are about equally far.  big > 1
    draws larger plates (the shell's front, seen face-on in S)."""
    if big in _FIELD:
        return _FIELD[big]
    V, U = np.mgrid[-100:60, -100:100].astype(float) + 0.5
    d1 = np.full(U.shape, 1e9)
    d2 = np.full(U.shape, 1e9)
    near = np.zeros(U.shape + (2,))
    for j in range(-18, 12):
        for i in range(-12, 13):
            cx, cy = (i * 9.0 + (4.5 if j % 2 else 0.0)) * big, j * 6.0 * big
            d = np.hypot((U - cx) / 1.1, V - cy)
            m2 = d < d1
            d2 = np.where(m2, d1, np.minimum(d2, d))
            near[m2] = np.stack([U - cx, V - cy], -1)[m2]
            d1 = np.where(m2, d, d1)
    seam = d2 - d1 < 1.1
    rim = ~seam & (d2 - d1 < 2.4) & (near[..., 0] + near[..., 1] < 0)
    _FIELD[big] = (seam, rim)
    return _FIELD[big]


def _scutes_at(ox, oy, calm=False):
    """Shell plates fixed to the shell (origin at its projected centre), so they move with it.
    calm (the S facing, where the shell's front fills the drawing): the lit rim steps up only on
    the lit and mid planes and the seams step down only out of the light, so the plates follow the
    form instead of reading as grain (10 Nov audit, N1)."""
    def tm(X, Y, t):
        seam_f, rim_f = _scute_field(BIG_S if calm else 1.0)
        iu = np.clip(np.floor(X - ox).astype(int) + 100, 0, seam_f.shape[1] - 1)
        iv = np.clip(np.floor(Y - oy).astype(int) + 100, 0, seam_f.shape[0] - 1)
        seam = seam_f[iv, iu] & (t >= 1) & ((t <= 2) if calm else True)
        rim = rim_f[iv, iu] & ((t >= 2) if calm else (t >= 1)) & (t < 4)
        out = t.copy()
        out[seam] = t[seam] - 1
        out[rim] = t[rim] + 1
        return out
    return tm


def _tufts(X, Y, t):
    out = t.copy()
    m = (((np.floor(X) * 3 + np.floor(Y) * 5) % 9) == 0) & (t <= 3)
    out[m] = t[m] + 1
    return out


def draw(facing='S', P=None, W=None, H=None):
    return C.draw_fig(build, facing, P or P0(), SCALE)
