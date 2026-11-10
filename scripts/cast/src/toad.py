"""Bramble toad (shooter): a squat, warty woodland toad grown over with a bramble that roots in its
back, shardstruck.  Olive-brown skin with darker warts, a cream belly and throat, big bulging gold
eyes on top of the head, the bramble's thorny canes arching over its back with two leaves.  The
Starfall shard sits in its back, and the bramble roots around it.  About 24 px tall, 30 wide.

Reads by silhouette as the round, low one that keeps its distance.  Telegraph (0.95 s): it rears
on its front legs, the throat sac swells, the shard brightens and a glint gathers at its lips: a
sighting pose along its facing.  Attack: it spits one thorn seed (the projectile is the
runtime's), mouth wide, rocking back.  Freed: the shard pops out of its back, it blinks, settles
and hops away."""
import math
import numpy as np
from ew import mat
import critter as C
from critter import add3

mat('toad',      ['#1C2414', '#34401E', '#56632E', '#7E8844', '#A6AE64'])
mat('toad_wart', ['#14180E', '#262E16', '#3C4622', '#56602E'])
mat('toad_belly', ['#6E6038', '#A8965E', '#D6C48A', '#F0E2B0'])
mat('toad_eye',  ['#5A3A08', '#9A6A10', '#D8A428', '#F6D670'])
mat('toad_sac',  ['#6E3A3A', '#A86058', '#D88E7C', '#F2BCA4'])

ID = 'toad'
NAME = 'Bramble toad'
HEIGHT = 41
BAND = (36, 52)
ONE_BODY = True
DETACHED_OK = ('shard', 'shardglow', 'cream', 'gold', 'tell')
SCALE = 1.45


def P0(**k):
    return C.P0(**dict(dict(sac=0.0, glint=0.0), **k))


def build(f, facing, P):
    R = C.Rig(f, facing)
    lat = P['lat'] + P['shake']
    up = 8.8 - P['bob']
    cf, ch = P['crouchF'], P['crouchH']
    if facing in 'SN':
        cf = max(cf, -1.0)     # end-on the sighting rise stays small (no stilted forelegs)
    front3 = (5.0, up - cf, lat)
    rear3 = (-5.0, up - ch, lat)
    body3 = (0.0, (front3[1] + rear3[1]) / 2 + 1.0, lat)
    ang = math.atan2(cf - ch, 10.0) + P['pitch']
    # legs: big folded hind thighs at the sides, short front legs
    for s in (1, -1):
        far = R.far(s)
        th3 = add3(rear3, (0.5, -1.5, 9.0 * s))
        C.blob(f, R, th3, 11.0, 6.0, 8.0, 'toad', 14 + (-4 if far else 2), rl=1.4, rs=2.2, dim=1 if far else 0, cast=None)
        fx, fy = R.p(add3(th3, (4.5, -th3[1], 1.0 * s)))
        fy -= 1.0 / f.scale
        f.add(f.ell(fx, fy - 1.0, 3.2, 1.6) & (f.Y < fy), 'toad', z=14.5 + (-4 if far else 2), flat=1, dim=1 if far else 0, line='hard')
    hips = [add3(front3, (2.0, -2.0 + (1.5 if facing in 'SN' else 0.0), 5.5)), add3(front3, (2.0, -2.0 + (1.5 if facing in 'SN' else 0.0), -5.5))]
    for i, h3 in enumerate(hips):
        foot3 = (h3[0] + (-1.5 if facing in 'SN' else 2.0) + P.get('reach', 0.0), 0.0 if P['gait'] is None else max(0.0, 2.0 * math.sin(2 * math.pi * (P['gait'] + 0.5 * i))), h3[2])
        (hx, hy), (fx, fy) = R.p(h3), R.p(foot3)
        fy -= 1.0 / f.scale
        far = R.far(h3[2])
        z = 12 + 0.1 * R.d(foot3) - (3 if facing == 'N' else 0)
        lr0, lr1 = (3.4, 3.0) if facing in 'SN' else (2.2, 1.6)      # end-on the forelegs are short and splayed
        if facing in 'SN':
            fx += 1.5 * (1 if R.p(add3(h3, (0, 0, 1)))[0] > hx else -1) * (1 if h3[2] > 0 else -1)
        f.add(f.cap(hx, hy, fx, fy - 1, lr0, lr1) & (f.Y < fy + (0.0 if facing in 'SN' else 1.0 / f.scale)), 'toad', z=z, rl=1, rs=1.4, dim=1 if far else 0, line='hard')
        f.add(f.ell(fx + (1 if facing in 'EW' else 0), fy - 0.8, 3.2 if facing in 'SN' else 2.4, 1.1) & (f.Y < fy), 'toad', z=z + 0.1, flat=1, dim=1 if far else 0, line='hard')
        f.anchor('foot_R' if i == 0 else 'foot_L', fx, fy)
    # body and head as one warty volume
    head3 = add3(front3, (6.5 + P['head'][0], 4.0 + P['head'][1], 0.0))
    vol = [(body3, 22.0, 24.0, 16.0), (head3, 12.0, 18.0, 10.0)]
    C.volume(f, R, vol, 'toad', 20, ang=ang, rl=2.4, rs=3.4, vgrad=0.35,
             tonemap=C.warts(seed=1.0))
    bodym = C.blob_mask(f, R, *vol[0], ang) | C.blob_mask(f, R, *vol[1], ang)
    # cream belly and throat (from the front and the side)
    if facing != 'N':
        bx, by = R.p(add3(head3, (3.0, -4.0, 0.0)))
        if facing == 'S':
            belly = f.ell(bx, by + 1.5, 7.5, 3.6)
        else:
            bx2, by2 = R.p(add3(body3, (4.0, -5.5, 0.0)))
            belly = f.ell(bx2, by2, 8.0, 3.0)
        belly &= bodym
        f.add(belly, 'toad_belly', z=21, rl=1.2, rs=1.6, vgrad=0.5, line='soft')
        sac = P['sac']
        if sac > 0.2:
            # the throat sac bulges down from the throat below the jaw line, inside the body's lower
            # edge (it never hangs in front of the mouth)
            sx, sy = R.p(add3(head3, (-0.5, -5.2 - 0.8 * sac, 0.0)))
            r = 2.0 + 2.4 * sac
            jaw_y = R.p(add3(head3, (5.5, -2.0, 0.0)))[1]
            inside = bodym | np.roll(bodym, 1, axis=0)
            sacm = f.ell(sx, sy, r * (1.05 if facing == 'S' else 1.0), r * 0.8) & (f.Y > jaw_y) & inside
            f.add(sacm, 'toad_belly', z=22, rl=1.4, rs=1.8, vgrad=0.5, deep=True, line='hard', tag='sac')
    # wet highlights: a short bright streak on the crown and one on the back (upper left, toward the light)
    if facing != 'N':
        for c3, n in ((add3(head3, (-1.0, 4.0, -2.5)), 3), (add3(body3, (-3.0, 7.0, -3.0)), 4)):
            hx, hy = R.p(c3)
            f.detail(f.rect(hx - n // 2, hy, hx + n - n // 2, hy + 1), ('toad_belly', 3), z=23.8, tag='wet')
            f.dot(hx - n // 2, hy + 1, ('toad', 4), z=23.8)
    # mouth: a line, open when spitting
    if facing in 'SEW':
        if facing == 'S':
            mx, my = R.p(add3(head3, (5.5, -1.5, 0.0)))
            mo = P['mouth']
            f.detail(f.rect(mx - 6, my, mx + 6, my + 1), ('toad_wart', 0), z=23)
            if mo > 0.1:
                f.add(f.ell(mx, my + 1, 4.0, 1.0 + 2.5 * mo), 'toad_sac', z=23.5, flat=0, line='hard')
        else:
            mx, my = R.p(add3(head3, (6.0, -1.5, 3.0)))
            f.detail(f.seg(mx - 7, my - 0.5, mx, my), ('toad_wart', 0), z=23)
            if P['mouth'] > 0.1:
                f.add(f.poly([(mx - 4, my), (mx + 0.5, my - 1.5), (mx + 0.5, my + 2.5 * P['mouth'] + 0.5)]), 'toad_sac', z=23.5, flat=0, line='hard')
    f.anchor('muzzle', *R.p(add3(head3, (7.0, -1.5, 0.0))))
    # the bramble rooted in its back: two arching canes with thorns and leaves
    zb = 24 if facing != 'S' else 19
    for s, (a, b) in ((1, (-6.0, 12.0)), (-1, (-3.0, 10.0))):
        pts = []
        for i in range(7):
            t = i / 6.0
            pts.append(add3(body3, (a + (b - a) * t * 0.6 - 4 * t, 7.5 + 6.0 * math.sin(math.pi * t), 4.0 * s * (1 - t * 0.4))))
        for p, q in zip(pts[:-1], pts[1:]):
            (x0, y0), (x1, y1) = R.p(p), R.p(q)
            f.add(f.cap(x0, y0, x1, y1, 0.9), 'thorn', z=zb + 0.02 * R.d(p), rl=0.8, rs=1, line='hard', tag='bramble')
        C.thorns(f, R, pts[1:6:2], (0.0, 1.0, 0.3 * s), 2.5, zb + 0.1, tag='bramble')
        lx, ly = R.p(pts[4])
        f.add(f.ell(lx + 2.5 * s, ly - 1, 2.4, 1.3), 'leafg', z=zb + 0.2, rl=1, rs=1, line='hard', tag='bramble')
    # eyes: two bulges on top of the head
    for s in (1, -1):
        e3 = add3(head3, (1.0, 5.5, 4.8 * s))
        far = R.far(s)
        if facing == 'N':
            ez = 18
        else:
            ez = 25 if not far else 19
        _, (ex, ey) = C.blob(f, R, e3, 5.5, 5.5, 5.5, 'toad', ez, rl=1, rs=1.4, vgrad=0.2, cast=None, dim=1 if far else 0)
        if facing != 'N' and not (far and facing in 'EW'):
            f.add(f.ell(ex + (0.6 if facing in 'EW' else 0), ey, 2.0, 1.8), 'toad_eye', z=ez + 0.1, flat=2, line='hard')
            C.eye(f, ex + (1 if facing in 'EW' else 0), ey, P['calm'], P['blink'], size=1)
    # the shard lodged in its back, where the bramble roots
    C.shard(f, R, add3(body3, (-2.0, 7.0, 0.0)), (-0.2, 1.0, 0.15), 8.0, P, 24.5 if facing != 'S' else 19.5)
    # the gathering glint at the lips (telegraph): a small four-point star in the telegraph colour
    if P['glint'] > 0.05 and facing != 'N':
        gx, gy = R.p(add3(head3, (7.0, -1.5, 0.0)))          # at the lips (Fig units, like every shape)
        r = (1 + 2.5 * P['glint']) / f.scale
        u = 1.0 / f.scale
        f.detail(f.rect(gx - r, gy, gx + r + u, gy + u) | f.rect(gx, gy - r, gx + u, gy + r + u), ('tell', 3), z=60, tag='glint')
        f.dot(gx, gy, ('tell', 4), z=60.1)
    if P.get('stars') is not None:
        x, y = R.p(add3(head3, (0, 10, 0)))
        C.stars(f, x, y, P['stars'])


def _warts(X, Y, t):
    """Warts: 2x2 bumps on an offset grid, each one tone darker with a lit pixel at its upper left;
    between them a faint mottle of the skin pattern."""
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    row = yi // 5
    lx = (xi + (row % 2) * 3 + (row % 3)) % 6
    ly = yi % 5
    out = t.copy()
    bump = (lx >= 2) & (lx <= 3) & (ly >= 2) & (ly <= 3) & (t >= 1) & (t <= 3)
    lit = (lx == 2) & (ly == 2) & (t >= 2)
    mott = (lx == 5) & (ly == 0) & (t == 2)
    out[bump] = t[bump] - 1
    out[lit] = np.minimum(t[lit] + 1, 4)
    out[mott] = 1
    return out


def draw(facing='S', P=None, W=None, H=None):
    return C.draw_fig(build, facing, P or P0(), SCALE)
