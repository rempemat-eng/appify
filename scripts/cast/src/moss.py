"""Moss: keeps the market stall at Crossroads, the town's voice.  A round, warm woman in her
sixties: rosy fair skin, chestnut hair going grey drawn back to a bun, a sage-green dress to the
ankle, a mustard knitted shawl pinned with a brass brooch, a cream apron with a deep pocket,
brown boots.  A wicker basket of apples and greens on her LEFT forearm.  About 72 px.

Distinct from the fourteen: no headwrap or robe; the only round, older market woman.  On folk.py.
Pose fields: apple (None, or the body-space point of the apple she is moving with her right hand),
basket ('arm' on the left forearm)."""
import numpy as np
from ew import Fig, mat
import anim
import palette  # noqa: F401
import folk

mat('moss_hair',  ['#4A3A36', '#7A6058', '#A88878', '#CDB4A2'])
mat('moss_dress', ['#24382C', '#3A5642', '#577A5A', '#7E9E74'])
mat('moss_shawl', ['#6A4A14', '#A87A22', '#D6A83C', '#F0D27A'])
mat('moss_apple', ['#5A1414', '#92241E', '#C8402C', '#EE7A52'])

ID = 'moss'
NAME = 'Moss'
SCALE = 1.02                     # drawn at this scale (folk.py's body is about 68 px)
HEIGHT = 72
BAND = (68, 78)
REST_R = (2.5, 25.5, 13.5)
REST_L = (6.0, 30.0, -11.5)          # forearm bent, carrying the basket


def P0(**k):
    return folk.pose0(**dict(dict(apple=None, poleL=(-1.0, -0.6, -0.4)), **k))


def basket(f, R, P, ctx):
    hl, zl, farl, el3 = ctx['arms']['L']
    c3 = np.array(el3) * 0.45 + np.array(hl) * 0.55 + np.array([0.5, -5.0, 0.0])   # hangs from the forearm
    cx, cy = R.p(tuple(c3))
    dim = 1 if farl else 0
    z = zl + 0.3
    with f.tagging('basket'):
        body = f.ell(cx, cy + 1.5, 6.4, 4.2) & (f.Y > cy - 1.0)
        f.add(body, 'bow', z=z, rl=1.2, rs=1.8, dim=dim, line='hard',
              tonemap=lambda X, Y, t: _weave(X, Y, t, cx, cy))
        hx0, hy0 = R.p(tuple(np.array(c3) + np.array([0, 2.0, 0])))
        f.add(f.ell(cx, cy - 1.0, 5.8, 5.6) & ~f.ell(cx, cy - 1.0, 4.6, 4.4) & (f.Y < cy - 1.0), 'bow', z=z + 0.4, flat=1, dim=dim, line='hard')
        for i, (dx, dy, m) in enumerate(((-3.0, -1.5, 'moss_apple'), (0.5, -2.2, 'moss_apple'), (3.4, -1.2, 'leafg'))):
            f.add(f.ell(cx + dx, cy + dy, 2.0, 1.8), m, z=z + 0.2 + i * 0.01, rl=1, rs=1, dim=dim, line='hard')
    if P['apple'] is not None:
        hr, zr, farr, _ = ctx['arms']['R']
        a3 = P['apple'] if P['apple'] != 'hand' else tuple(np.array(hr) + np.array([0.8, 1.5, 0.0]))
        ax, ay = R.p(tuple(a3))
        f.add(f.ell(ax, ay, 2.0, 1.8), 'moss_apple', z=zr + 0.9, rl=1, rs=1, line='hard', tag='apple')
        f.dot(ax, ay - 2, ('leafg', 2), z=zr + 1.0)


def _weave(X, Y, t, cx, cy):
    out = t.copy()
    m = ((np.floor(X - cx) + np.floor(Y - cy)) % 3 == 0) & (t >= 2)
    out[m] = 1
    return out


CFG = dict(rest=(REST_R, REST_L), skin='skin', hair='moss_hair', hair_style='bun', band=None,
           top='moss_dress', sleeve='moss_dress', forearm='sleeve', legs='trouser', boots='brownb',
           skirt=dict(mat='moss_dress', hem=13.0), apron=dict(mat='cream', top=9.0, hem=11.0, pocket=True),
           shawl='moss_shawl', belt=None, SHW=11.5, TW=11.5, HW=11.0, arm_r=3.5, head=1.03, hand_r=3.0,
           gear=basket)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    f = Fig(W or anim.CELL[0], H or anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')), scale=SCALE)
    f.despeckle = True
    folk.build(f, facing, P, CFG)
    return f
