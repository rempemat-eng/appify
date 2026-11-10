"""Hale: the village smith (Crossroads).  A broad, strong woman in her forties: dark skin, short
black curls under an ochre head-scarf band, a soot-grey work shirt with the sleeves rolled to the
elbow (bare forearms), a heavy oiled-leather apron from chest to knee with a pocket, dark
trousers, stout boots.  One cross-peen hammer, always in her RIGHT hand (hanging at rest, raised
when she works).  A soot smudge on her right cheek.  About 74 px.

Distinct from the fourteen: no armour, no hat, no long hair; the only smith.  Built on folk.py.
Pose fields: hammer (direction from the grip to the head, body space), bar (a glowing workpiece
on the anvil held by tongs in the left hand, 0/1), sparks (None or 0..1 burst phase)."""
import math
import numpy as np
from ew import Fig, mat
import anim
import palette  # noqa: F401
import folk

mat('hale_hair',  ['#141016', '#221A22', '#342834', '#4A3C46'])
mat('hale_shirt', ['#2C3038', '#454B56', '#646B78', '#8A92A0'])
mat('hale_band',  ['#6A3A10', '#A8641C', '#D89A34', '#F2C468'])
mat('hale_pants', ['#2A2328', '#463B42', '#605259', '#7C6B70'])   # v2: a step lighter, so the trousers show three lit planes

ID = 'hale'
NAME = 'Hale'
SCALE = 1.09                     # drawn at this scale (folk.py's body is about 68 px)
HEIGHT = 74
BAND = (70, 80)
REST_R = (2.0, 26.0, 15.0)
REST_L = (1.0, 26.0, -14.5)


def P0(**k):
    return folk.pose0(**dict(dict(hammer=(0.15, -1.0, 0.0), bar=0, sparks=None), **k))


def hammer(f, R, P, ctx):
    """The hammer in the right hand: an ash handle from the fist, an iron head across its end
    (one face, one peen).  Tongs and a glowing bar in the left hand when she works."""
    hh, z, far, _ = ctx['arms']['R']
    d = folk.nrm(P['hammer'])
    a3 = np.array(hh) - d * 2.0
    b3 = np.array(hh) + d * 10.0
    (ax, ay), (bx, by) = R.p(tuple(a3)), R.p(tuple(b3))
    dim = 1 if far else 0
    hd = ctx['head3']
    if b3[1] > hd[1] - 12 and R.d(tuple(b3)) >= R.d(hd) - 0.5:
        z = 46.5                                  # raised beside the head, nearer than it
    with f.tagging('hammer'):
        f.add(f.cap(ax, ay, bx, by, 1.15), 'bow', z=z + 0.5, rl=1, rs=1.2, dim=dim, line='hard')
        # the head: perpendicular to the handle in the plane of the swing (fwd/up)
        side3 = np.cross(d, (0.0, 0.0, 1.0))
        if np.linalg.norm(side3) < 0.2:
            side3 = np.array([1.0, 0.0, 0.0])
        side3 = side3 / np.linalg.norm(side3)
        h0, h1 = b3 + side3 * 3.6, b3 - side3 * 2.6
        (cx, cy), (dx, dy) = R.p(tuple(h0)), R.p(tuple(h1))
        f.add(f.cap(cx, cy, dx, dy, 1.9, 1.3), 'gunmetal', z=z + 0.55, rl=1, rs=1.4, dim=dim, line='hard')
    f.anchor('hammer_face', *R.p(tuple(h0)))
    if P['bar']:
        hl, zl, farl, _ = ctx['arms']['L']
        dl = (1.0, 0.0, 0.25)
        t0, t1 = np.array(hl), np.array(hl) + np.array(dl) * 9.0
        (tx0, ty0), (tx1, ty1) = R.p(tuple(t0)), R.p(tuple(t1))
        f.add(f.cap(tx0, ty0, tx1, ty1, 0.8), 'gunmetal', z=zl + 0.5, flat=1, dim=1 if farl else 0, line='hard', tag='tongs')
        e0 = np.array(t1)
        e1 = e0 + np.array([3.5, 0.0, 0.6])
        (ex0, ey0), (ex1, ey1) = R.p(tuple(e0)), R.p(tuple(e1))
        f.add(f.cap(ex0, ey0, ex1, ey1, 1.1), 'glow', z=zl + 0.6, rl=1, rs=0.8, line='hard', tag='bar')
        f.anchor('bar', *R.p(tuple(e1)))


def sparks(f, R, P, ctx):
    if P['sparks'] is None:
        return
    x, y = f.anchors.get('hammer_face', (0, 0))
    if f.flip:
        x = -x
    t = P['sparks']
    for i, (vx, vy) in enumerate(((-5, -6), (4, -7), (7, -3), (-7, -2), (1, -9))):
        px, py = x + vx * (0.4 + t), y + vy * (0.4 + t) + 3 * t * t
        f.dot(px, py, ('glow', 3 if (i + int(t * 3)) % 2 else 2), z=15 if R.facing == 'N' else 60, tag='sparks')


def soot(f, P, x0, hy, fc):
    if fc == 'S':
        f.detail(f.rect(x0 - 7, hy + 2, x0 - 5, hy + 3), ('hale_pants', 1))
    else:
        f.detail(f.rect(x0 + 2, hy + 2, x0 + 4, hy + 3), ('hale_pants', 1))


CFG = dict(rest=(REST_R, REST_L), skin='skin_d', hair='hale_hair', hair_style='curly', band='hale_band',
           top='hale_shirt', sleeve='hale_shirt', forearm='skin', legs='hale_pants', boots='leather',
           skirt=None, apron=dict(mat='leather', top=1.0, hem=11.0, pocket=True), shawl=None, belt=None,
           SHW=12.5, TW=12.0, HW=11.0, arm_r=3.9, leg_r=4.4, hand_r=3.3, head=1.0,
           gear=hammer, fx=sparks, face_extra=soot)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')), scale=SCALE)
    f.despeckle = True
    folk.build(f, facing, P, CFG)
    return f
