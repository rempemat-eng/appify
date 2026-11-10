"""Boarlet (rusher): a young wild boar of the valley woods, shardstruck.  Russet-brown bristly
coat with a dark bristle ridge, a pale snout with two small cream tusks, short legs on dark
hooves, a curled tail.  A violet Starfall shard is lodged in its right shoulder blade, standing up out of the hump, glowing.  About
30 px tall, 44 long.

Reads by silhouette as the low, long, charging one.  Telegraph (0.95 s): head drops, rump rises,
the front right hoof paws the ground and kicks dust, the tusks come forward.  Attack: the charge,
body stretched low.  Freed: the shard pops out, it shakes itself, sits, and trots off."""
import math
import numpy as np
from ew import mat
import critter as C
from critter import add3

mat('boar',     ['#2A1610', '#4E2C1C', '#7A4A2C', '#A46E44', '#C8946A'])
mat('boar_dk',  ['#1A0E0C', '#2E1A14', '#46281C', '#5E3A28'])
mat('snout',    ['#5A2E2A', '#8E5446', '#BA7C66', '#DCA68A'])

ID = 'boarlet'
NAME = 'Boarlet'
HEIGHT = 41
BAND = (36, 50)
ONE_BODY = True
DETACHED_OK = ('shard', 'shardglow', 'cream', 'gold', 'tell')
SCALE = 1.3


def P0(**k):
    return C.P0(**k)


LOOK = dict(coat='boar', dark='boar_dk', snout='snout', tusk=2.5, ridge=4.0, canes=False, back_shard=False)


GROUND_SN = 2.0     # a big boar end-on: its near hooves (toward the camera) project well below the
                    # pivot, so the whole drawing sits this much higher in S and N


def build(f, facing, P, look=None):
    L = look or LOOK
    R = C.Rig(f, facing)
    sh = P['shake']
    lat = P['lat'] + sh
    base = 13.0 - P['bob'] + (GROUND_SN if facing in 'SN' and f.scale > 1.5 else 0.0)
    cf, ch = P['crouchF'], P['crouchH']
    hd = P['head']
    if facing in 'SN':
        # seen end-on a dropped head comes toward the camera: keep the drop short so the face
        # stays inside the cell (the read is the raised rump and the lowered brow)
        cf, hd = cf * 0.5, (hd[0], hd[1] * 0.4)
    front3 = (8.0, base - cf, lat)
    hind3 = (-8.0, base - ch, lat)
    body3 = ((front3[0] + hind3[0]) / 2, (front3[1] + hind3[1]) / 2 + 1.0, lat)
    ang = math.atan2(cf - ch, 16.0) + P['pitch']
    # legs first (behind the body)
    hips = [add3(front3, (1.0, -3.0, 5.5)), add3(front3, (1.0, -3.0, -5.5)), add3(hind3, (-1.0, -3.0, 5.5)), add3(hind3, (-1.0, -3.0, -5.5))]
    foot_fwd = [P.get('fFR', 9.0), P.get('fFL', 9.0), P.get('fHR', -8.0), P.get('fHL', -8.0)]
    PL = P
    if facing in 'SN' and f.scale > 1.5:
        # end-on, a big boar's reach toward the camera is foreshortened further so its near
        # hooves stay on the ground band (the stride reads in the side views)
        foot_fwd = [v * 0.6 + (hips[i][0] * 0.4) for i, v in enumerate(foot_fwd)]
        PL = dict(P, stride=P['stride'] * 0.6, ground=GROUND_SN)
    feet = C.legs(f, R, PL, hips, foot_fwd, L['dark'], 10, r0=2.6, r1=1.6, hoof='crack')
    # tail
    tx, ty = R.p(add3(hind3, (-9.5, 3.0, 0.0)))
    f.add(f.ell(tx, ty, 1.8, 1.6) | f.cap(tx, ty, tx - 1.5, ty - 3.0, 0.9), L['dark'], z=15 if facing != 'N' else 30, flat=1, line='hard')
    # body
    # one volume: the barrel and the heavy shoulder hump over the front legs (high in front)
    hd_ = P['head'] if facing in 'EW' else hd
    head3 = add3(front3, (10.0 + hd_[0], 2.5 + hd_[1], 0.0))
    parts = [(add3(body3, (-2.5, -1.0, 0.0)), 26.0, 17.0, 15.0), (add3(front3, (0.5, 2.5, 0.0)), 15.0, 18.0, 19.0)]
    if facing in 'EW':
        # side on, the head is one silhouette with the shoulders: a neck carries it down and forward
        neck3 = tuple((a + b) / 2 for a, b in zip(add3(front3, (3.0, 3.0, 0.0)), head3))
        parts += [(neck3, 14.0, 14.0, 15.0)]
    C.volume(f, R, parts, L['coat'], 20, ang=ang, rl=2.4, rs=3.6, vgrad=0.5, tonemap=C.fur(seed=0.5))
    # guard: the head grows out of the neck and the neck out of the shoulders, so a dropped head
    # never floats free (export fails rather than draw two animals)
    if facing in 'EW':
        shoulder = C.blob_mask(f, R, *parts[1], ang) | C.blob_mask(f, R, *parts[0], ang)
        neck = C.blob_mask(f, R, *parts[2], ang)
        headm = C.blob_mask(f, R, head3, 15.0, 13.5, 13.0)
        joint = min(int((neck & shoulder).sum()), int((neck & headm).sum()))
        if joint < 20 * f.scale * f.scale:
            raise ValueError('boarlet %s: head joins the body over only %d px' % (facing, joint))
    # bristle ridge along the spine
    ridge = [(x, hind3[1] + (front3[1] - hind3[1]) * (x + 8.0) / 16.0 + 6.0 + 0.2 * (x + 10), lat) for x in (-10, -6, -2, 2, 6, 9)]
    C.thorns(f, R, ridge, (-0.3, 1.0, 0.0), L['ridge'] * (0.55 if facing in 'SN' else 1.0), 24, m=L['dark'])
    # head: drops and comes forward with P['head']
    zh = 26 if facing != 'N' else 14
    sn3 = add3(head3, (8.0, -2.5, 0.0))
    C.volume(f, R, [(head3, 15.0, 13.5, 13.0), (add3(head3, (4.5, -1.8, 0.0)), 9.0, 9.0, 8.0)], L['coat'], zh, rl=2.0, rs=2.8, vgrad=0.4,
             tonemap=C.fur(seed=1.5, density=(0.6, 0.35, 0.1, 0.0)))
    _, (sx, sy) = C.blob(f, R, sn3, 5.0, 7.0, 6.0, L['snout'], zh + 0.5, rl=1.2, rs=1.6, vgrad=0.3, cast=None)
    # ears
    for s in (1, -1):
        ex, ey = R.p(add3(head3, (-2.0, 5.0, 4.0 * s)))
        f.add(f.poly([(ex - 2, ey + 1), (ex - 3.5, ey - 4.5), (ex + 1.5, ey)]), L['dark'], z=zh + 0.3 + (0 if not R.far(s) else -1), rl=0.8, rs=1, line='hard',
              dim=1 if R.far(s) else 0)
    # tusks: forward of the snout, curling up
    for s in (1, -1):
        if R.far(s) and facing in 'EW':
            continue
        b3 = add3(sn3, (1.0, -1.5, 2.6 * s))
        (bx, by), (tx2, ty2) = R.p(b3), R.p(add3(b3, (L['tusk'] + P['mouth'], L['tusk'] * 1.1, (1.8 if facing in 'SN' else 0.6) * s)))
        f.add(f.cap(bx, by, tx2, ty2, 0.9, 0.6), 'cream', z=zh + 0.8, rl=1, rs=1, line='hard', tag='tusk')
    # eyes and nostrils
    if facing == 'S':
        for s in (1, -1):
            x, y = R.p(add3(head3, (3.5, 1.5, 3.2 * s)))
            C.eye(f, x, y, P['calm'], P['blink'])
        f.detail(f.rect(sx - 2, sy, sx - 1, sy + 1), ('snout', 0))
        f.detail(f.rect(sx + 1, sy, sx + 2, sy + 1), ('snout', 0))
    elif facing in 'EW':
        x, y = R.p(add3(head3, (3.0, 1.5, 4.0)))
        C.eye(f, x, y, P['calm'], P['blink'])
        f.dot(sx + 2, sy, ('snout', 0))
    # the shard in the right shoulder
    if L['back_shard']:
        # the elite's two shards stand on the spine ridge behind the head, leaning back
        C.shard(f, R, add3(front3, (-4.0, 8.5, 0.8)), (-0.6, 0.8, 0.15), 7.5, P, 25 if facing != 'S' else 21)
    else:
        C.shard(f, R, add3(front3, (-2.5, 9.0, 2.0)), (-0.2, 1.0, 0.35), 8.0, P, 25)
    if L['canes']:
        # the elite: bramble canes grown over its back, rooted around a second, larger shard
        zb = 24.5 if facing != 'S' else 21
        for s, (a, b) in ((1, (-11.0, 9.0)), (-1, (-8.0, 11.0)), (0.3, (-13.0, 4.0))):
            pts = [add3(body3, (a + (b - a) * t, 7.0 + (2.5 if facing in 'SN' else 4.5) * math.sin(math.pi * t) - (cf - ch) * (a + (b - a) * t) / 16.0, 6.0 * s * (1 - 0.5 * t)))
                   for t in [i / 6.0 for i in range(7)]]
            for p, q in zip(pts[:-1], pts[1:]):
                (x0, y0), (x1, y1) = R.p(p), R.p(q)
                f.add(f.cap(x0, y0, x1, y1, 1.0), 'thorn', z=zb + 0.02 * R.d(p), rl=0.8, rs=1, line='hard', tag='bramble')
            C.thorns(f, R, pts[1:7:2], (0.0, 1.0, 0.4 * s), 3.0, zb + 0.1, tag='bramble')
            lx, ly = R.p(pts[3])
            f.add(f.ell(lx + 2 * (1 if s > 0 else -1), ly - 1, 2.4, 1.3), 'leafg', z=zb + 0.2, rl=1, rs=1, line='hard', tag='bramble')
    if L['back_shard']:
        P2 = dict(P, fx=P['fx'] + 1)
        C.shard(f, R, add3(body3, (-6.0, 7.5, -0.8)), (-0.6, 0.8, -0.15), 8.0, P2, 24.8 if facing != 'S' else 20.5)
    # dust from the pawing hoof (telegraph) or the charge
    if P.get('dust') is not None:
        x, y = feet[0]
        C.dust(f, x, y, P['dust'])
    if P.get('stars') is not None:
        x, y = R.p(add3(head3, (-5.0, 8.0, 0.0)))       # over the brow, toward the light
        C.stars(f, x, y, P['stars'])
    f.anchor('strike', *R.p(add3(sn3, (4.0, 0.0, 0.0))))


def _bristles(X, Y, t):
    out = t.copy()
    m = ((np.floor(X) * 3 + np.floor(Y) * 2) % 7 == 0) & (t >= 2)
    out[m] = t[m] - 1
    return out


def draw(facing='S', P=None, W=None, H=None):
    return C.draw_fig(build, facing, P or P0(), SCALE)
