"""Ada Fern: the first villager to come home (the Ferns' cottage).  A young woman in her
twenties: fair freckled skin, a copper chin-length bob with a fringe under a blue head band, a
pale-blue dress to mid-calf with a fern-green knitted cardigan (its sleeves), a brown belt,
brown boots.  A birch broom, held upright in her RIGHT hand at rest and in both hands to sweep.
About 70 px.

Distinct from the fourteen: no weapon, no braid, no headwrap; the slice's young homecomer.
Pose fields: broom ('rest' upright in the right hand; 'sweep' in both hands, the handle running
from the right hand through the left), bgrip (right hand's distance from the bristles' end)."""
import numpy as np
from ew import Fig, mat
import anim
import palette  # noqa: F401
import folk

mat('ada_hair',  ['#5A1E10', '#9A3A18', '#CC6228', '#EE9452'])
mat('ada_dress', ['#3A5068', '#56769A', '#7EA2C4', '#AECAE2'])
mat('ada_knit',  ['#203A22', '#33582E', '#4E7E3C', '#78A456'])
mat('ada_band',  ['#1E2E5A', '#2E4A8A', '#4A6EBE', '#7A9ADE'])

ID = 'ada'
NAME = 'Ada Fern'
SCALE = 1.06                     # drawn at this scale (folk.py's body is about 68 px)
HEIGHT = 70
BAND = (66, 76)
REST_R = (4.0, 27.0, 12.5)
REST_L = (1.0, 26.0, -12.0)
BROOM = 46.0


def P0(**k):
    return folk.pose0(**dict(dict(broom='rest', bgrip=14.0), **k))


def broom(f, R, P, ctx):
    hh, z, far, _ = ctx['arms']['R']
    if P['broom'] == 'rest':
        u = np.array([0.08, 1.0, 0.0])
        g = 25.0
    else:                                               # both hands on the handle: it runs through them
        hl = ctx['arms']['L'][0]
        u = folk.nrm(np.subtract(hl, hh))
        g = P['bgrip']
    u = u / np.linalg.norm(u)
    foot3 = np.array(hh) - u * g                        # the bristles' end
    top3 = foot3 + u * BROOM
    b0 = foot3 + u * 9.0
    (fx, fy), (tx, ty), (bx, by) = R.p(tuple(foot3)), R.p(tuple(top3)), R.p(tuple(b0))
    dd = R.d(tuple(foot3 + u * 25))
    zb = z + 0.5 if dd >= -3.5 else 6.0
    with f.tagging('broom'):
        f.add(f.cap(bx, by, tx, ty, 1.0), 'bow', z=zb, rl=1, rs=1.2, line='hard')
        L = np.hypot(bx - fx, by - fy) or 1.0
        ux, uy = (bx - fx) / L, (by - fy) / L
        px, py = -uy, ux
        brush = f.poly([(bx - px * 1.6, by - py * 1.6), (bx + px * 1.6, by + py * 1.6), (fx + px * 3.6, fy + py * 3.6), (fx - px * 3.6, fy - py * 3.6)])
        f.add(brush, 'hay' if 'hay' in _mats() else 'gold', z=zb + 0.05, rl=1, rs=1.4, line='hard')
        f.add(f.cap(bx - px * 1.8, by - py * 1.8, bx + px * 1.8, by + py * 1.8, 0.8), 'leather', z=zb + 0.1, flat=1, line='hard')
    f.anchor('broom_foot', fx, fy)


def _mats():
    from ew import MATS
    return MATS


def freckles(f, P, x0, hy, fc):
    pts = [(x0 - 6, hy + 3), (x0 - 4, hy + 4), (x0 + 4, hy + 3), (x0 + 6, hy + 4)] if fc == 'S' else [(x0 + 3, hy + 3), (x0 + 5, hy + 4)]
    for x, y in pts:
        f.dot(x, y, ('skin', 1))


CFG = dict(rest=(REST_R, REST_L), skin='skin', hair='ada_hair', hair_style='bob', band='ada_band',
           top='ada_dress', sleeve='ada_knit', forearm='sleeve', legs='trouser', boots='brownb',
           skirt=dict(mat='ada_dress', hem=10.5), apron=None, shawl=None, belt='leather',
           SHW=10.5, TW=10.0, HW=10.0, arm_r=3.2, head=1.0, hand_r=2.9, gear=broom, face_extra=freckles)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')), scale=SCALE)
    f.despeckle = True
    folk.build(f, facing, P, CFG)
    return f
