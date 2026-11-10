"""Tam: mature male ice monk in orange robes (redesign, Matt 25 Oct 10:29).

Built from real monastic dress, described in words (no images copied):
  - Theravada: a lower wrap from waist to calf, an upper robe wrapped round the body that leaves
    the RIGHT shoulder bare and is draped over the LEFT shoulder, its end thrown back to hang down
    the back, and a cloth belt; the drape makes long diagonal folds from the left shoulder toward
    the right hip.
  - Shaolin: a cross-collared under-jacket (left panel over right), wide trousers bound at the
    shin with cloth leg wraps, flat dark cloth shoes, and a sash knotted at the waist.
Tam combines them: an ochre cross-collared under-robe (its sleeve shows on the bare right side),
wide ochre trousers, a saffron outer robe draped over the LEFT shoulder and wrapped diagonally to
the right hip, falling as a panel to the knee, its end hanging down the back from the left
shoulder; a dark burnt-orange sash knotted at the LEFT hip with two weighted ends; cool pale
grey-blue hand and leg wraps; dark cloth shoes.  v3 (Matt, 26 Oct: bald, a touch cooler, a strong profile): a shaved head, heavy dark brows, a
high-bridged nose and a short squared chin beard; the under-robe and trousers deep maroon under the
saffron, a slate-blue sash.  The cool accents (wraps, the ice-blue guru bead and tassel of the mala, and the ice
of Glacier Form) stand against the orange.
Gear, each exactly once:
  - wraps round both forearms and palms (fingers free) and both shins;
  - one mala (bead cord): a closed loop round the neck to mid chest, the guru bead and tassel at
    the bottom; it passes behind the neck, so the back view shows the cord at the nape;
  - the sash's two weighted ends at the left hip.
Glacier Form (special and every powered clip): ice grows round the SAME forearms (elbow to
wrist; the open palms stay bare) and the same shins (ankle up to the knee).  P['ice'] 0..1.
About 73 px tall.

Pass 2: pose-driven on parts.Rig, with designer 1's Shift kit from morel.py.
Equipment tags: beads, sash, robe, ice."""
import math
import numpy as np
from ew import Fig, mat
from parts import eye, EYE, Rig
import turn
import palette  # noqa: F401
import anim
from morel import Shift, add3, sub3, mul3, nrm, sdir, frame, legs, boot, arm_z, open_hand, up_z, reach

ID = 'tam'
NAME = 'Tam'
HEIGHT = 73
SCALE = 1.05                    # 26 Oct: with the neck the head sits lower (69 px); drawn 5 % larger to the adult 72 to 73
BAND = (67, 78)

mat('saffron', ['#6E2A0A', '#B04A12', '#E87A1E', '#FFAE48'])       # outer robe
mat('ochre_t', ['#240A10', '#4A1822', '#7A2C3A', '#AC5462'])       # v3: the darker under-robe and trousers (deep maroon)
mat('sash_t',  ['#161C28', '#283448', '#3E5070', '#5E769A'])       # v3: slate-blue sash (a cool accent, the Frostline)
mat('beard_t', ['#141218', '#24202A', '#38323E', '#504858'])       # v3: brows and the short chin beard
mat('wrapc',   ['#4E5A68', '#7E8C9C', '#B4C0CC', '#E0E8F0'])       # cool hand and leg wraps
mat('bead_t',  ['#2A1810', '#4A2C1C', '#70462C', '#986840', '#C89A68'])
mat('shoe',    ['#18161C', '#28252E', '#3A3642', '#524C5A'])
mat('crop_t',  ['#3A3840', '#5E5B64', '#8A8790', '#B0ADB4'])       # close-cropped grey hair
mat('ice_t',   ['#2A5A8E', '#4C8CC8', '#86C4EE', '#C8ECFC', '#F4FEFF'])

SHW = 12.5
REST_R = (3.5, 26.0, 13.8)                 # v4: hands a little forward and ready, not hanging
REST_L = (3.0, 26.5, -13.8)
HANG = (0.35, -1.0, 0.0)


def P0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, lag=0.0,
             footR=(0.5, 0.0), footL=(3.5, 0.6), stance=6.4,       # v4 (26 Oct): weight on the right leg, the left relaxed ahead, heel light
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             fingR=HANG, fingL=HANG, ice=0.0, blink=False, brow=0, face=None)
    p.update(k)
    return p


# ------------------------------------------------------------------------------------ ice
def ice_shell(f, a, b, r, z, dim=0, seed=0):
    """A faceted ice sleeve from screen point a to b, radius r: a capsule with a few crystal
    points along it and a bright facet line on the lit (upper left) side."""
    m = f.cap(a[0], a[1], b[0], b[1], r, r * 0.92)
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    px, py = -uy, ux
    n = max(1, int(L / 3.5))
    for i in range(n):
        t = (i + 0.5) / n
        s = 1 if (i + seed) % 2 else -1
        cx, cy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        tipx, tipy = cx + px * s * (r + 1.1), cy + py * s * (r + 1.1)
        m |= f.poly([(cx - ux * 1.2 + px * s * r * 0.6, cy - uy * 1.2 + py * s * r * 0.6), (tipx, tipy), (cx + ux * 1.2 + px * s * r * 0.6, cy + uy * 1.2 + py * s * r * 0.6)])
    f.add(m, 'ice_t', z=z, rl=1.4, rs=1.6, tl=0.5, line='hard', dim=dim, tag='ice',
          tonemap=lambda X, Y, t: np.where((np.abs((X - a[0]) * 0.7 + (Y - a[1]) * 0.7 - 1.0) < 0.5) & (t >= 2), 3, t))


# ------------------------------------------------------------------------------------ mala, sash
def _bead_row(f, pts, z):
    for x, y in pts:
        f.add(f.ell(x, y, 1.3, 1.3), 'bead_t', z=z + 0.01, rl=0.8, rs=1.0, line='hard')


def _pendant(f, x, y, z):
    """The guru bead (ice blue) and its short tassel, lying on the chest."""
    f.add(f.ell(x, y, 1.5, 1.5), 'ice_t', z=z + 0.02, rl=1, rs=1.2, line='hard')
    f.add(f.poly([(x - 1.0, y + 1.4), (x + 1.0, y + 1.4), (x + 1.5, y + 4.6), (x - 1.5, y + 4.6)]), 'ice_t', z=z + 0.03, rl=1, rs=1.4,
          line='hard')


def beads_front(f, sy, z):
    """The mala lies on the chest: from both sides of the neck down to a point at the breastbone."""
    with f.tagging('beads'):
        pts = []
        for s_ in (-1, 1):
            for i in range(6):
                t = i / 5
                pts.append((s_ * 4.6 * (1 - t) ** 0.9, sy - 2.2 + 9.0 * t ** 0.95))
        f.add(f.seg(-4.6, sy - 2.2, 0, sy + 6.8) | f.seg(4.6, sy - 2.2, 0, sy + 6.8), 'bead_t', z=z, flat=1, line=None, clean=False)
        _bead_row(f, pts, z)
        _pendant(f, 0.0, sy + 8.2, z)


def beads_side(f, tx, sy, z):
    """In profile the loop runs from the neck down the front of the chest; the pendant lies on it."""
    with f.tagging('beads'):
        x0, y0, x1, y1 = 4.2 + tx, sy - 2.6, 7.8 + tx, sy + 6.0
        f.add(f.seg(x0, y0, x1, y1), 'bead_t', z=z, flat=1, line=None, clean=False)
        _bead_row(f, [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)], z)
        _pendant(f, x1 - 0.2, y1 + 1.4, z)


def sash(f, x0, x1, hy, z, knot_x=None, lag=0.0, dim=0, tails=True):
    """The slate-blue sash at the waist; knotted at one hip, two tails that swing with the walk."""
    with f.tagging('sash'):
        f.add(f.rect(x0, hy - 6.0, x1, hy - 2.6), 'sash_t', z=z, rl=1.2, rs=1.8, line='hard', dim=dim,
              tonemap=lambda X, Y, t: np.where((np.abs(Y - hy + 4.4 - (X * 0.12)) < 0.5) & (t >= 2), 1, t))
        if knot_x is None:
            return
        f.add(f.ell(knot_x, hy - 4.3, 2.4, 2.1), 'sash_t', z=z + 0.03, rl=1, rs=1.4, line='hard', dim=dim)
        if tails:
            for dx, L in ((-1.0, 12.0), (1.4, 9.5)):
                sw = lag * 0.45
                e = f.poly([(knot_x + dx - 1.3, hy - 3.0), (knot_x + dx + 1.3, hy - 3.0), (knot_x + dx + 1.5 - sw, hy - 3 + L),
                            (knot_x + dx - 1.3 - sw, hy - 3 + L)])
                f.add(e, 'sash_t', z=z + (0.01 if dx < 0 else 0.02), rl=1, rs=1.6, line='hard', dim=dim)
                f.add(f.rect(knot_x + dx - 1.4 - sw, hy - 4 + L, knot_x + dx + 1.6 - sw, hy - 2.6 + L), 'sash_t', z=z + 0.025, flat=3,
                      line=None, dim=dim)


# ------------------------------------------------------------------------------------ head
def _brow(P):
    return {0: 0, 1: 1, 2: -1}.get(P['brow'], 0)


def _dome(X, Y, t, cx, cy):
    """The shaved scalp: a small shine up and to the left (the light)."""
    out = t.copy()
    out[((X - cx + 2.6) ** 2 / 7.0 + (Y - cy + 5.2) ** 2 / 3.2 < 1.0) & (t >= 2)] = 3
    return out


def _ear(f, x, y, z=39.5, flip=1):
    f.add(f.ell(x, y, 1.7, 2.5), 'skin', z=z, rl=1, rs=1.2, line='hard')
    f.dot(x + 0.4 * flip, y + 0.4, ('skin', 1), z=z)


def _neck(f, hy, cx=0.0, w=3.6, back=False):
    """26 Oct (Matt: "the monk's head is floating"): a real neck from under the jaw down into the
    robe's neckline, shaded under the chin (front) or with the nape's crease (back)."""
    neck = f.rect(cx - w, hy + 3.0, cx + w, hy + 13.0) | f.ell(cx, hy + 12.5, w + 1.2, 2.2)
    f.add(neck, 'skin', z=20.2, rl=1.4, rs=2.2, line='hard',
          tonemap=lambda X, Y, t: _neck_shade(X, Y, t, hy, cx, back))


def _neck_shade(X, Y, t, hy, cx, back):
    out = t.copy()
    if not back:
        out[(Y < hy + 10.5) & (t >= 1)] = np.minimum(out[(Y < hy + 10.5) & (t >= 1)], 1)    # under the jaw: in its shadow
    out[(X - cx < -2.0) & (Y > hy + 9.0) & (t >= 2)] = 3                                    # the lit side of the throat / nape
    return out


def head_south(f, P, hy):
    """v4 (26 Oct review): a round shaved head, level brows, calm eyes, a defined jaw with a short
    neat beard that follows it, the mouth showing between moustache and chin."""
    _ear(f, -8.3, hy + 1.6, flip=1)
    _ear(f, 8.3, hy + 1.6, flip=-1)
    _neck(f, hy)
    skull = f.ell(0, hy - 0.8, 8.2, 8.0)
    jaw = f.poly([(-7.8, hy + 1.0), (7.8, hy + 1.0), (7.0, hy + 5.5), (3.2, hy + 9.0), (-3.2, hy + 9.0), (-7.0, hy + 5.5)])
    f.add(skull | jaw, 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1), tonemap=lambda X, Y, t: _dome(X, Y, t, 0.0, hy))
    ey = hy + 1
    lift = _brow(P)
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(-5, ey + 2, -3, ey + 3), EYE)
        f.detail(f.rect(3, ey + 2, 5, ey + 3), EYE)
    else:
        eye(f, -5, ey, 3)
        eye(f, 3, ey, 3)
    f.detail(f.rect(-6, ey - 2 + lift, -2, ey - 1 + lift), ('beard_t', 2))
    f.detail(f.rect(2, ey - 2 + lift, 6, ey - 1 + lift), ('beard_t', 2))
    f.detail(f.rect(-1, hy + 3, 1, hy + 5), ('skin', 3))                                   # the nose's lit ridge
    f.detail(f.rect(0, hy + 5, 2, hy + 6), ('skin', 1))
    beard = f.poly([(-7.4, hy + 3.0), (-6.2, hy + 3.0), (-5.6, hy + 6.0), (-2.6, hy + 8.0), (2.6, hy + 8.0), (5.6, hy + 6.0),
                    (6.2, hy + 3.0), (7.4, hy + 3.0), (7.2, hy + 6.0), (3.4, hy + 9.8), (0, hy + 10.6), (-3.4, hy + 9.8), (-7.2, hy + 6.0)])
    beard |= f.rect(-3.2, hy + 6.0, 3.2, hy + 7.0)                                            # the moustache
    f.add(beard, 'beard_t', z=44.5, rl=1.0, rs=1.6, line='hard')
    f.detail(f.rect(-2, hy + 7, 2, hy + 8), ('skin', 0))                                   # the mouth


def head_side(f, P, hy, hx):
    """v4 profile: a round skull, a clear brow, a straight nose, the mouth and a jaw line running
    back to the ear, which sits just behind the jaw hinge at eye height; a short beard follows
    the jaw."""
    face = f.poly([(hx + 6.8, hy - 2.6), (hx + 8.0, hy - 0.4), (hx + 8.2, hy + 0.6), (hx + 10.2, hy + 4.0), (hx + 8.6, hy + 4.8),
                   (hx + 8.9, hy + 6.4), (hx + 8.4, hy + 8.6), (hx + 5.6, hy + 9.6), (hx + 2.2, hy + 7.6), (hx - 2.0, hy + 4.0)])
    skull = f.ell(hx + 0.6, hy - 0.8, 7.9, 8.0)
    _neck(f, hy, cx=hx + 1.4, w=3.4)
    f.add(f.poly([(hx - 3.0, hy + 9.0), (hx + 1.0, hy + 9.0), (hx - 1.0, hy + 14.0), (hx - 7.5, hy + 14.0)]), 'skin', z=20.15, rl=1.2,
          rs=2.0, line='hard')                                                                  # the nape's slope into the back
    f.add(skull | face, 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1), tonemap=lambda X, Y, t: _dome(X, Y, t, hx + 0.6, hy))
    _ear(f, hx - 0.4, hy + 2.0, z=40.5, flip=-1)
    ey = hy + 1
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(hx + 5, ey + 2, hx + 7, ey + 3), EYE)
    else:
        eye(f, hx + 5, ey, 3)
    f.detail(f.rect(hx + 4, ey - 2 + _brow(P), hx + 8, ey - 1 + _brow(P)), ('beard_t', 2))
    beard = f.poly([(hx + 1.6, hy + 4.6), (hx + 3.0, hy + 5.4), (hx + 5.8, hy + 7.4), (hx + 8.6, hy + 7.2), (hx + 8.8, hy + 6.2),
                    (hx + 7.0, hy + 6.0), (hx + 9.0, hy + 6.3), (hx + 8.7, hy + 9.0), (hx + 5.6, hy + 10.4), (hx + 2.0, hy + 7.8),
                    (hx + 0.6, hy + 5.2)])
    f.add(beard, 'beard_t', z=44.5, rl=1.0, rs=1.6, line='hard')
    f.detail(f.rect(hx + 7, hy + 7, hx + 9, hy + 8), ('skin', 0))                          # the mouth's corner line


def head_north(f, P, hy):
    _ear(f, -8.3, hy + 1.6, flip=1)
    _ear(f, 8.3, hy + 1.6, flip=-1)
    _neck(f, hy, back=True)
    f.add(f.ell(0, hy - 0.8, 8.2, 8.0) | f.ell(0, hy + 3.6, 6.4, 5.4), 'skin', z=40, rl=2.0, rs=3.0, line='hard',
          tonemap=lambda X, Y, t: _dome(X, Y, t, 0.0, hy))
    f.add(f.ell(-6.4, hy + 6.0, 1.4, 2.4) | f.ell(6.4, hy + 6.0, 1.4, 2.4), 'beard_t', z=39.6, rl=1, rs=1.2, line='hard')  # the beard's edge
    f.detail(f.rect(-3, hy + 7, 3, hy + 8), ('skin', 1))                                   # the nape crease
    f.add(f.rect(-4.5, hy + 9.2, 4.5, hy + 10.4), 'bead_t', z=41.5, flat=1, line='hard', tag='beads')


def head_3q(f, P, hy, back):
    """Contract v2 three-quarter head (SE / NE drawn, SW / NW mirrored) for the turn in-betweens."""
    if back:
        _ear(f, 7.4, hy + 1.8, z=39, flip=-1)
        _neck(f, hy, cx=1.2, back=True)
        f.add(f.ell(0.6, hy - 0.8, 8.2, 8.0) | f.ell(1.6, hy + 3.6, 6.2, 5.4), 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1),
              tonemap=lambda X, Y, t: _dome(X, Y, t, 0.6, hy))
        f.add(f.poly([(5.6, hy + 4.0), (8.0, hy + 4.4), (7.6, hy + 8.4), (5.4, hy + 9.0)]), 'beard_t', z=39.5, rl=1, rs=1.2, line='hard')
        f.detail(f.rect(-3, hy + 7, 3, hy + 8), ('skin', 1))
        f.add(f.rect(-4.0, hy + 9.2, 5.0, hy + 10.4), 'bead_t', z=41.5, flat=1, line='hard', tag='beads')
        return
    _ear(f, -6.0, hy + 1.8, z=39, flip=1)
    _neck(f, hy, cx=1.6)
    skull = f.ell(0.6, hy - 0.8, 8.2, 8.0)
    jaw = f.poly([(-6.6, hy + 1.0), (8.6, hy + 1.0), (8.2, hy + 5.2), (5.2, hy + 9.0), (0.2, hy + 9.0), (-5.2, hy + 5.2)])
    f.add(skull | jaw, 'skin', z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1), tonemap=lambda X, Y, t: _dome(X, Y, t, 0.6, hy))
    ey = hy + 1
    lift = _brow(P)
    if P['blink'] or P['face'] == 'shut':
        f.detail(f.rect(-1, ey + 2, 1, ey + 3), EYE)
        f.detail(f.rect(5, ey + 2, 7, ey + 3), EYE)
    else:
        eye(f, -1, ey, 3)
        eye(f, 5, ey, 3)
    f.detail(f.rect(-2, ey - 2 + lift, 2, ey - 1 + lift), ('beard_t', 2))
    f.detail(f.rect(4, ey - 2 + lift, 8, ey - 1 + lift), ('beard_t', 2))
    f.detail(f.rect(3, hy + 3, 5, hy + 5), ('skin', 3))
    f.detail(f.rect(4, hy + 5, 6, hy + 6), ('skin', 1))
    beard = f.poly([(-5.6, hy + 3.0), (-4.4, hy + 3.0), (-3.0, hy + 6.0), (0.6, hy + 8.0), (5.6, hy + 8.0), (7.8, hy + 5.6),
                    (8.4, hy + 3.0), (8.6, hy + 5.6), (6.0, hy + 9.8), (2.6, hy + 10.6), (-0.6, hy + 9.6), (-5.0, hy + 5.6)])
    beard |= f.rect(0.4, hy + 6.0, 6.6, hy + 7.0)
    f.add(beard, 'beard_t', z=44.5, rl=1.0, rs=1.6, line='hard')
    f.detail(f.rect(1, hy + 7, 5, hy + 8), ('skin', 0))


# ------------------------------------------------------------------------------------ torso
def _skirt_folds(X, Y, t, top, xs):
    """Vertical folds in the hanging cloth: a shaded trough with a lit ridge on its left."""
    out = t.copy()
    for xf in xs:
        xx = xf + (Y - top) * 0.07 * np.sign(xf)
        out[(np.abs(X - xx) < 0.55) & (Y > top + 1.5) & (t >= 1)] = 1
        out[(np.abs(X - xx + 1.1) < 0.55) & (Y > top + 2.5) & (t >= 2)] = 3
    return out


def _chest(f, sy, hy, w=12.0, wa=7.4, cx=0.0, z=20):
    """The under-robe's body: a broad chest tapering to a narrow waist."""
    m = f.ell(cx, sy + 4.5, w, 7.6) | f.poly([(cx - w + 0.5, sy + 2), (cx + w - 0.5, sy + 2), (cx + wa, hy - 3.5), (cx - wa, hy - 3.5)])
    m |= f.poly([(cx - 4.6, sy - 4.4), (cx + 4.6, sy - 4.4), (cx + w - 1.0, sy + 1.0), (cx - w + 1.0, sy + 1.0)])    # trapezius (26 Oct)
    f.add(m, 'ochre_t', z=z, rl=2.0, rs=3.4, vgrad=0.25, line='hard', tonemap=lambda X, Y, t: _chest_planes(X, Y, t, cx, sy, w, _west(f)))
    return m


def _west(f):
    while not hasattr(f, 'flip') and hasattr(f, 'f'):
        f = f.f
    return bool(getattr(f, 'flip', False))


def _chest_planes(X, Y, t, cx, sy, w, west):
    """26 Oct (asset gate): the under-robe's chest in three planes, lit up-left (mirrored on the
    flipped grid), so the maroon never reads flat from behind or turned."""
    out = t.copy()
    d = ((X - cx) * (0.55 if west else -0.55) - (Y - sy - 4.0) * 0.85) / w
    lit, dark = (d > 0.2) & (t >= 1), (d < -0.25) & (t >= 1)
    out[lit] = np.minimum(t[lit] + 1, 3)
    out[dark] = np.maximum(t[dark] - 1, 0)
    core = (d < -0.75) & (t >= 1)                     # the core shadow low on the far flank
    out[core] = 0
    return out


def _drape_folds(f, pts, z, tone=1):
    for (x0, y0, x1, y1) in pts:
        f.detail(f.seg(x0, y0, x1, y1), ('saffron', tone), solid=False, z=z)


def _skirt(f, hy, x0, x1, xb0, xb1, z=22.0, folds=(-5.0, 0.0, 5.0), back_lag=0.0, kneel=0.0, side=False):
    """The saffron's lower wrap from the waist to the knee, over the maroon under-robe's hem.
    kneel (0..1, 26 Oct): in a deep kneel the cloth drapes forward over the thighs (side) or
    spreads over the knees (front, back) and rides up, instead of hanging as a stiff box."""
    if kneel > 0:
        if side:
            xb0, xb1 = xb0 + 6.5 * kneel, xb1 + 6.5 * kneel
        else:
            xb0, xb1 = xb0 - 2.0 * kneel, xb1 + 2.0 * kneel
        hy = hy - 3.0 * kneel
    hem = f.poly([(xb0 + 0.6, hy + 6.6), (xb1 - 0.6, hy + 6.6), (xb1 - 0.2, hy + 10.4), (xb0 + 0.2 - back_lag * 0.3, hy + 10.8)])
    f.add(hem, 'ochre_t', z=z - 0.5, rl=1.2, rs=1.8, line='hard',
          tonemap=lambda X, Y, t: _skirt_folds(X, Y, t, hy + 6.6, folds[::2]))
    sk = f.poly([(x0, hy - 3.2), (x1, hy - 3.2), (xb1, hy + 7.4), (xb0 - back_lag * 0.5, hy + 7.8)])
    f.add(sk, 'saffron', z=z, rl=1.8, rs=2.8, vgrad=0.3, line='hard', cast=(0, 1, 1), tag='robe',
          tonemap=lambda X, Y, t: _skirt_folds(X, Y, t, hy - 3.2, folds))


def _kneel(P):
    return float(np.clip((P['crouch'] - 5.0) / 7.0, 0.0, 1.0))


def torso_south(f, P, b, ub):
    sy, hy, lag = -42 + ub, -22 + b, P['lag']
    _chest(f, sy, hy)
    # the under-robe's crossed collar (left panel over right) at the throat
    f.add(f.poly([(-3.4, sy - 2.6), (3.4, sy - 2.6), (0, sy + 3.6)]), 'skin', z=20.4, rl=1, rs=1.6, line='hard')
    f.add(f.poly([(3.4, sy - 3.0), (5.2, sy - 2.4), (-0.4, sy + 5.0), (-1.8, sy + 3.8)]), 'ochre_t', z=20.6, flat=3, line='soft')
    # the saffron drape: over the LEFT shoulder (screen right), across the chest to the right hip
    drape = f.poly([(1.2, sy - 3.2), (7.0, sy - 3.8), (12.6, sy - 0.6), (12.4, sy + 5.0), (7.6, hy - 3.6), (-7.6, hy - 3.6),
                    (-8.2, hy - 7.0)])
    f.add(drape, 'saffron', z=22, rl=2.0, rs=3.2, vgrad=0.25, line='hard', cast=(0, 1, 1), tag='robe')
    f.detail(f.seg(1.4, sy - 2.6, -7.8, hy - 6.6), ('saffron', 3), solid=False, z=22.1)            # the lit rolled edge
    _drape_folds(f, [(9.5, sy + 0.5, -2.5, hy - 4.4), (11.5, sy + 3.5, 3.0, hy - 4.2), (6.0, sy - 1.6, -6.0, hy - 5.6)], 22.1)
    sash(f, -7.8, 7.8, hy, 24, knot_x=5.6, lag=lag)
    _skirt(f, hy, -7.4, 7.4, -9.2, 9.2, kneel=_kneel(P))
    beads_front(f, sy, 26.5)


def torso_north(f, P, b, ub):
    sy, hy, lag = -42 + ub, -22 + b, P['lag']
    _chest(f, sy, hy)
    drape = f.poly([(-1.2, sy - 3.2), (-7.0, sy - 3.8), (-12.6, sy - 0.6), (-12.4, sy + 5.0), (-7.6, hy - 3.6), (7.6, hy - 3.6),
                    (8.2, hy - 7.0)])
    f.add(drape, 'saffron', z=22, rl=2.0, rs=3.2, vgrad=0.25, line='hard', tag='robe')
    _drape_folds(f, [(-9.5, sy + 0.5, 2.5, hy - 4.4), (-6.0, sy - 1.6, 6.0, hy - 5.6)], 22.1)
    sash(f, -7.8, 7.8, hy, 24, knot_x=-5.6, lag=lag)
    _skirt(f, hy, -7.4, 7.4, -9.2, 9.2, kneel=_kneel(P))
    # the robe's end, thrown back over the left shoulder, hangs down the back and sways
    end = f.poly([(-11.4, sy - 2.4), (-5.2, sy - 3.0), (-4.8 - lag * 0.3, hy + 6.0), (-10.8 - lag, hy + 5.0)])
    f.add(end, 'saffron', z=27, rl=1.6, rs=2.8, vgrad=0.3, line='hard', cast=(1, 1, 1), tag='robe',
          tonemap=lambda X, Y, t: _skirt_folds(X, Y, t, sy, (-8.0,)))


def torso_side(f, P, b, ub, tx, west):
    sy, hy, lag = -42 + ub, -22 + b, P['lag']
    chest = f.ell(1.4 + tx, sy + 4.6, 8.4, 7.6) | f.poly([(-6.4 + tx, sy + 1.5), (9.0 + tx, sy + 2.5), (6.4, hy - 3.5), (-5.4, hy - 3.5)])
    chest |= f.poly([(-2.6 + tx, sy - 4.2), (4.4 + tx, sy - 4.0), (8.6 + tx, sy + 1.5), (-6.4 + tx, sy + 1.5)])    # trapezius (26 Oct)
    if not west:
        sash(f, -5.4, 7.0, hy, 6, knot_x=-3.0, lag=lag, dim=1)                                # knot at the far (left) hip, behind
        f.add(f.poly([(-5.8 + tx, sy - 2.0), (-3.2 + tx, sy - 2.6), (-4.4 - lag * 0.4, hy + 4.0), (-6.8 - lag, hy + 3.6)]),
              'saffron', z=7, rl=1.4, rs=2.4, dim=1, line='hard', tag='robe')                 # the robe's end down the back
    f.add(chest, 'ochre_t', z=20, rl=2.0, rs=3.4, vgrad=0.25, line='hard')
    if not west:
        # right side near: the shoulder is bare of the robe; the saffron crosses the front from
        # the far shoulder down to this hip
        drape = f.poly([(3.0 + tx, sy - 3.2), (8.4 + tx, sy + 0.2), (9.6 + tx, sy + 5.0), (6.6, hy - 3.6), (-5.6, hy - 3.6),
                        (-6.0, hy - 6.6)])
        folds = [(8.4 + tx, sy + 2.0, 0.0, hy - 4.6), (9.2 + tx, sy + 5.5, 4.0, hy - 4.2)]
        edge = (3.2 + tx, sy - 2.6, -5.6, hy - 6.2)
    else:
        drape = f.poly([(-6.6 + tx, sy - 1.0), (-2.0 + tx, sy - 3.8), (5.0 + tx, sy - 3.2), (8.8 + tx, sy + 0.6), (9.6 + tx, sy + 5.0),
                        (6.6, hy - 3.6), (-5.6, hy - 3.6), (-6.6 + tx, sy + 8.0)])
        folds = [(2.0 + tx, sy - 2.0, -2.0, hy - 4.4), (6.0 + tx, sy - 1.0, 3.0, hy - 4.2), (-3.0 + tx, sy - 1.6, -5.0, hy - 5.0)]
        edge = None
    f.add(drape, 'saffron', z=22, rl=2.0, rs=3.2, vgrad=0.25, line='hard', cast=(0, 1, 1), tag='robe')
    if edge:
        f.detail(f.seg(*edge), ('saffron', 3), solid=False, z=22.1)
    _drape_folds(f, folds, 22.1)
    sash(f, -5.6, 7.2, hy, 24, knot_x=3.0 if west else None, lag=lag)
    _skirt(f, hy, -5.6, 7.2, -7.4, 8.4, folds=(-2.0, 3.0), back_lag=lag, kneel=_kneel(P), side=True)
    if west:
        f.add(f.poly([(-7.0 + tx, sy - 2.6), (-3.2 + tx, sy - 3.2), (-4.6 - lag * 0.4, hy + 5.0), (-8.6 - lag, hy + 4.4)]),
              'saffron', z=26.5, rl=1.6, rs=2.8, vgrad=0.3, line='hard', cast=(1, 1, 1), tag='robe',
              tonemap=lambda X, Y, t: _skirt_folds(X, Y, t, sy, (-5.5,)))
    beads_side(f, tx, sy, 26.8)


# ------------------------------------------------------------------------------------ build
def _bands(X, Y, t, a, b):
    out = t.copy()
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    u = ((X - a[0]) * dx + (Y - a[1]) * dy) / L
    v = ((X - a[0]) * -dy + (Y - a[1]) * dx) / L
    out[(np.abs(((u + v * 0.5) % 2.6) - 1.3) > 0.9) & (t >= 2)] = 1
    return out


def _leg_planes(X, Y, t, kx, west):
    """26 Oct (asset gate): the trouser leg rounds - a lit edge toward the light, the shade and a
    core shadow on the far edge (mirrored on the flipped grid)."""
    out = t.copy()
    u = (X - kx) * (-1 if west else 1)
    out[(u < -2.0) & (t >= 1)] = np.minimum(t[(u < -2.0) & (t >= 1)] + 1, 3)
    out[(u > 1.5) & (t >= 1)] = np.maximum(t[(u > 1.5) & (t >= 1)] - 1, 0)
    out[(u > 3.2) & (t >= 1)] = 0
    return out


def _leg_fn(ice):
    def _leg(f, R, up, lo, kn3, foot3, lat, far, z):
        dim = 1 if far else 0
        kx = R.p(kn3)[0]
        f.add(up | lo, 'ochre_t', z=z, rl=1.8, rs=2.8, vgrad=0.2, dim=dim, line='hard',
              tonemap=lambda X, Y, t: _leg_planes(X, Y, t, kx, _west(f)))
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.0, foot3[2])
        w3 = add3(kn3, mul3(sub3(ank3, kn3), 0.3))
        a, bb = R.p(w3), R.p(ank3)
        f.add(f.cap(a[0], a[1], bb[0], bb[1], 3.4, 3.1), 'wrapc', z=z + 0.5, rl=1.4, rs=2.0, dim=dim, line='hard',
              tonemap=lambda X, Y, t: _bands(X, Y, t, a, bb))
        fx, fy = boot(f, R, foot3, 'shoe', z, far)                      # dark cloth shoes, the wraps tied over the instep
        f.add(f.rect(fx - 3.0, fy - 5.0, fx + 3.0, fy - 3.8), 'wrapc', z=z + 1.5, flat=1, dim=dim, line=None)
        if ice > 0.02:
            top3 = add3(ank3, mul3(sub3(kn3, ank3), min(1.0, ice)))
            a2 = R.p(add3(ank3, (0.0, -1.0, 0.0)))
            t2 = R.p(top3)
            ice_shell(f, a2, t2, 4.1 * (0.7 + 0.3 * min(1.0, ice)), z + 1.6, dim=dim, seed=int(lat > 0))
    return _leg


def _arm(f, R, sh3, h3, pole, z, far, ice, lat):
    """The right arm is bare from a short maroon cap sleeve (the under-robe); the left upper arm
    is under the saffron drape.  Both forearms are wrapped, the palms too (his weapon)."""
    up, lo, el3 = R.limb(sh3, h3, 8.8, 8.6, 3.4, 3.0, 2.6, pole)
    dim = 1 if far else 0
    e, w = R.p(el3), R.p(h3)
    f.add(f.cap(e[0], e[1], w[0], w[1], 2.8, 2.4), 'wrapc', z=z - 0.1, rl=1.4, rs=2.0, line='hard', dim=dim,
          tonemap=lambda X, Y, t: _bands(X, Y, t, e, w))
    s = R.p(sh3)
    zu = up_z(R, z, far)
    if lat > 0:
        f.add(f.cap(s[0], s[1], e[0], e[1], 3.5, 3.0), 'skin', z=zu, rl=1.6, rs=2.6, line='hard', dim=dim, cast=(1, 1, 1) if not dim else None)
        cx, cy = s[0] + (e[0] - s[0]) * 0.22, s[1] + (e[1] - s[1]) * 0.22
        f.add(f.ell(cx, cy, 3.7, 3.0), 'ochre_t', z=zu + 0.05, rl=1.2, rs=1.8, line='hard', dim=dim)      # the cap sleeve
    else:
        f.add(f.cap(s[0], s[1], e[0], e[1], 3.6, 3.6), 'saffron', z=zu, rl=1.6, rs=2.6, line='hard', dim=dim,
              cast=(1, 1, 1) if not dim else None, tag='robe')
    if ice > 0.02:
        a = (e[0] + (w[0] - e[0]) * 0.1, e[1] + (w[1] - e[1]) * 0.1)
        bb = (e[0] + (w[0] - e[0]) * (0.1 + 0.78 * min(1.0, ice)), e[1] + (w[1] - e[1]) * (0.1 + 0.78 * min(1.0, ice)))
        ice_shell(f, a, bb, 3.4 * (0.75 + 0.25 * min(1.0, ice)), z + 0.15, dim=dim, seed=0)
    return el3


def build(f, facing, P):
    R = Rig(f, facing)
    west = facing in ('W', 'SW', 'NW')
    hip3, sh3, head3 = frame(P, 26.5, 17.5, 14.8)          # v4: longer legs; the head set down into the neck (26 Oct)
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
    hR = reach(shR, hR, 17.4)
    hL = reach(shL, hL, 17.4)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    ice = P['ice']
    legs(f, R, P, hip3, _leg_fn(ice), 10.8, 10.6)
    with Shift(f, hx, 0):
        if R.diag:                       # contract v2 turn in-betweens: the S or N torso turned onto the body
            with turn.Warp(f, R, tx * 0.5, 12.0, 9.0, 'N' if R.back else 'S'):
                (torso_north if R.back else torso_south)(f, P, b, ub)
        elif facing == 'S':
            torso_south(f, P, b, ub)
        elif facing == 'N':
            torso_north(f, P, b, ub)
        else:
            torso_side(f, P, b, ub, tx, west)
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        pole = P['pole' + key] or (-1.0, -0.25, 0.6 * lat)
        z = arm_z(R, P, key, hh)
        far = R.far(lat)
        _arm(f, R, sh, hh, pole, z, far, ice, lat)
        fing = P['fing' + key]
        thumb = (0.6, 0.2, -0.6 * lat) if fing[1] > -0.5 else (1.0, 0.0, -0.3 * lat)
        tip = open_hand(f, R, hh, fing, z + 0.8, 'skin', dim=1 if far else 0, thumb3=thumb, wrap='wrapc')
        f.anchor('palm_' + key, *tip)
    hx2, hy2 = R.p(head3)
    with Shift(f, hx2, 0):
        if R.diag:
            head_3q(f, P, hy2, R.back)
        elif facing == 'S':
            head_south(f, P, hy2)
        elif facing == 'N':
            head_north(f, P, hy2)
        else:
            head_side(f, P, hy2, 0.0)


def draw(facing='S', P=None, W=None, H=None):
    P = P or P0()
    W = W or anim.CELL[0]
    H = H or anim.CELL[1]
    f = Fig(W, H, gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing in ('W', 'SW', 'NW')), scale=SCALE)
    f.despeckle = True                              # v2 polish: no lone pixels
    build(f, facing, P)
    return f
