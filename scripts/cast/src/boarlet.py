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
DETACHED_OK = ('shard', 'shardglow', 'cream', 'gold', 'tell', 'soil', 'dirt', 'lamp')
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
    if facing == 'N':
        # from behind: a small curl (12 Nov audit, polish: the old blob read as a hole)
        k_ = f.scale
        tone_ = {'l': (L['dark'], 3), 'm': (L['dark'], 2), 'd': (L['dark'], 1)}
        bx_, by_ = math.floor(tx * k_) - 2, math.floor(ty * k_) - 2
        for j_, row_ in enumerate(_TAIL_N):
            for c_, ch_ in enumerate(row_):
                if ch_ in tone_:
                    f.detail(f.pixels([((bx_ + c_) / k_, (by_ + j_) / k_)]), tone_[ch_], z=31)
    else:
        f.add(f.ell(tx, ty, 1.8, 1.6) | f.cap(tx, ty, tx - 1.5, ty - 3.0, 0.9), L['dark'], z=15, flat=1, line='hard')
    # body
    # one volume: the barrel and the heavy shoulder hump over the front legs (high in front)
    hd_ = P['head'] if facing in 'EW' else hd
    head3 = add3(front3, (10.0 + hd_[0], 2.5 + hd_[1], 0.0))
    parts = [(add3(body3, (-2.5, -1.0, 0.0)), 26.0, 17.0, 15.0), (add3(front3, (0.5, 2.5, 0.0)), 15.0, 18.0, 19.0)]
    if facing in 'EW':
        # side on, the head is one silhouette with the shoulders: a neck carries it down and forward
        neck3 = tuple((a + b) / 2 for a, b in zip(add3(front3, (3.0, 3.0, 0.0)), head3))
        parts += [(neck3, 14.0, 14.0, 15.0)]
    # face-on (S) the head, ears and shoulders crowd one small patch: coat meets coat in the shade
    # tone instead of an ink line, and the fur is sparser, so the face reads by its parts and not
    # by grain (10 Nov audit, N1: cluster noise in S)
    calm = facing == 'S'
    cline = 'shade' if calm else 'hard'
    C.volume(f, R, parts, L['coat'], 20, ang=ang, rl=2.4, rs=3.6, vgrad=0.5, line=cline,
             tonemap=C.fur(seed=0.5, density=(0.3, 0.2, 0.05, 0.0) if calm else (0.8, 0.62, 0.3, 0.0)))
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
    if facing == 'N':
        _mane_from_behind(f, R, ridge, L['dark'], L['coat'])
    else:
        C.thorns(f, R, ridge, (-0.3, 1.0, 0.0), L['ridge'] * (0.55 if facing in 'SN' else 1.0), 24, m=L['dark'])
    # head: drops and comes forward with P['head']
    zh = 26 if facing != 'N' else 14
    sn3 = add3(head3, (8.0, -2.5, 0.0))
    C.volume(f, R, [(head3, 15.0, 13.5, 13.0), (add3(head3, (4.5, -1.8, 0.0)), 9.0, 9.0, 8.0)], L['coat'], zh, rl=2.0, rs=2.8, vgrad=0.4, line=cline,
             tonemap=C.fur(seed=1.5, density=(0.3, 0.2, 0.05, 0.0) if calm else (0.6, 0.35, 0.1, 0.0)))
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
    # kicked dust (10 Nov audit B4, 12 Nov B4r): round path-toned puffs that rise, drift back and
    # break up, kicked out behind the hind hooves with a gap, under the body (z 5); in S and N
    # beside the hind hooves, outside the body, where they show
    if P.get('dust') is not None and P['dust'] < 1:
        hx_, hy_ = feet[2]
        hl = feet[3]
        if facing in 'EW':
            pts = [(hx_ - 6.0, hy_, 2.2), (hx_ - 10.0, hy_ + 0.3, 1.8), (hx_ - 3.0, hy_ - 0.5, 1.4)]
            C.puffs(f, pts, P['dust'], 'dirt', z=5, drift=-1.0)
        else:
            s_ = 1 if hx_ > hl[0] else -1
            pts = [(hx_ + s_ * 6.5, hy_, 2.0), (hl[0] - s_ * 6.5, hl[1], 1.7)]
            C.puffs(f, pts, P['dust'], 'dirt', z=5 if facing == 'S' else 30, drift=0.0)
    if P.get('stars') is not None:
        x, y = R.p(add3(head3, (-5.0, 8.0, 0.0)))       # over the brow, toward the light
        C.stars(f, x, y, P['stars'], tip=f.anchors.get('shard'))
    f.anchor('strike', *R.p(add3(sn3, (4.0, 0.0, 0.0))))


# bristle tufts seen from behind, in screen pixels, rump (small) to ears (spikes): '.' none, 'l' the
# lit upper-left pair (the coat's light tone, lighter than the coat beside it), 'm' the mane's mid,
# 'd' its dark right side (the E/W mane's family, never ink)
_TUFTS = (('l.', 'lm', 'md'),                                     # the rump: 2 px
          ('.l.', 'llm', 'lmd', '.md'),
          ('.l.', 'llm', 'lmd', 'lmd'),
          ('.l..', 'llm.', 'lmmd', 'lmmd', '.mdd'),
          ('.l..', 'llm.', 'lmmd', 'lmmd', '.mdd'),                 # the two between the ears stand
          ('..l.', '.llm', 'llmd', 'lmmd', '.mdd'))                 # above the back as spikes


def _mane_from_behind(f, R, ridge, m, coat):
    """From behind (N) the bristle ridge is a row of six separate tufts from the rump to the ears,
    growing from 2 px at the rump to 4 x 5 spikes that stand above the back between the ears, each
    lit on its upper left (lighter than the coat) and dark on its right (10 Nov audit B2, 12 Nov
    B2r).  Explicit pixels on the screen grid, so each tuft keeps its shape at the figure's scale."""
    k = f.scale
    tone = {'d': (m, 1), 'm': (m, 3), 'l': (coat, 4)}
    a, b = R.p(ridge[0]), R.p(ridge[-1])                    # the rump end and the ears end
    a = (a[0] + (a[0] - b[0]) * 0.15, a[1] + (a[1] - b[1]) * 0.15)
    b = (b[0] + (b[0] - a[0]) * 0.32, b[1] + (b[1] - a[1]) * 0.32)   # on past the ears: the last two break the outline
    n = len(_TUFTS)
    for i, rows in enumerate(_TUFTS):
        t = i / (n - 1.0)
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        w = max(len(r) for r in rows)
        sx = math.floor(x * k) - w // 2 + (1 if i % 2 else 0)        # staggered a pixel either side of the spine
        sy = math.floor(y * k) - len(rows) + 2
        for j, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch in tone:
                    f.detail(f.pixels([((sx + c) / k, (sy + j) / k)]), tone[ch], z=24.5 if i < n - 2 else 40)


# the tail seen from behind: a 2 px curl in the mane's dark tones with one lit pixel
_TAIL_N = ('.lm.', 'm..d', 'd.m.', '.d..')


def _bristles(X, Y, t):
    out = t.copy()
    m = ((np.floor(X) * 3 + np.floor(Y) * 2) % 7 == 0) & (t >= 2)
    out[m] = t[m] - 1
    return out


def draw(facing='S', P=None, W=None, H=None):
    return C.draw_fig(build, facing, P or P0(), SCALE)
