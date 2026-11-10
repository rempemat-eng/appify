"""Shared builder for the village folk (Hale, Moss, Ada Fern): one pose-driven body on parts.Rig,
dressed by a per-character look (cfg).  The same pose renders S, N, E and W, like the cast.

cfg keys: rest ((right hand, left hand) at rest, body space), skin, hair, hair_style ('curly', 'bun', 'bob'), top, sleeve, forearm ('sleeve' or
'skin'), legs, boots, skirt (None or dict(mat, hem)), apron (None or dict(mat, top, hem)),
shawl (None or mat), belt (None or mat), band (headband mat or None), SHW (shoulder half-width),
TW (torso half-width), HW (hip half-width), head (head radius scale), gear (callback that draws
held items: gear(f, R, P, ctx)), hand_r (hand radius).
Pose fields: bob, breath, lean, crouch, hipx, twist, footR, footL, stance, handR, handL, poleR,
poleL, zR, zL, blink, face ('talk' opens the mouth, 'shut' closes the eyes), lag, plus any
character fields the gear reads."""
import math
import contextlib
import numpy as np
from parts import eye, boot_side, EYE, Rig, FLIP
import anim
import turn
import surf


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def nrm(v):
    v = np.array(v, float)
    return v / (np.linalg.norm(v) or 1.0)


def pose0(**k):
    p = dict(bob=0, breath=0, lean=0.0, crouch=0.0, hipx=0.0, twist=0.0,
             footR=(1.5, 0.0), footL=(-1.5, 0.0), stance=4.8,
             handR=None, handL=None, poleR=None, poleL=None, zR=None, zL=None,
             blink=False, face=None, lag=0.0, fx=0)
    p.update(k)
    return p


def build(f, facing, P, cfg):
    R = Rig(f, facing)
    side = R.side
    # contract v2: a three-quarter facing draws the S (front) or N (back) pieces turned onto the
    # body (turn.Warp); vf is the flat drawing it starts from
    vf = 'S' if facing in ('SE', 'SW') else ('N' if facing in ('NE', 'NW') else facing)
    SHW, TW, HW = cfg['SHW'], cfg['TW'], cfg['HW']
    R.body_half = TW - 1.0
    b, cr, lean = P['bob'], P['crouch'], P['lean']
    hip3 = (P['hipx'], 22.0 - cr - b, 0.0)
    sh3 = (hip3[0] + lean, hip3[1] + 19.5 + P['breath'], 0.0)
    head3 = (sh3[0] + lean * 0.3, sh3[1] + 15.0, 0.0)
    off = (P['hipx'], -cr - b, 0.0)
    th = P['twist'] / SHW
    shR = add3(sh3, (0.3 - SHW * math.sin(th), -1.0, SHW * math.cos(th)))
    shL = add3(sh3, (0.3 + SHW * math.sin(th), -1.0, -SHW * math.cos(th)))
    rest_r, rest_l = cfg['rest']
    hR = add3(P['handR'] or rest_r, off)
    hL = add3(P['handL'] or rest_l, off)
    f.anchor('hand_R', *R.p(hR))
    f.anchor('hand_L', *R.p(hL))
    hx, hy = R.p(hip3)
    sx, sy = R.p(sh3)
    ctx = dict(R=R, hR=hR, hL=hL, sh3=sh3, hip3=hip3, head3=head3, off=off, cfg=cfg)
    # ---------------------------------------------------------------- back gear
    if cfg.get('back'):
        cfg['back'](f, R, P, ctx)
    # ---------------------------------------------------------------- legs
    st = P['stance']
    knees = []
    for lat, key in ((st, 'footR'), (-st, 'footL')):
        ft = P[key]
        foot3 = (ft[0], ft[1], lat)
        ank3 = (foot3[0] - 0.5, foot3[1] + 6.0, lat)
        hp3 = add3(hip3, (0, 0, lat * 0.9))
        far = R.far(lat)
        dim = _dim(R, far)
        up, lo, kn3 = R.limb(hp3, ank3, 8.3, 8.1, cfg.get('leg_r', 4.0), 3.6, 3.2, (1.0, 0.0, 0.1 * np.sign(lat)))
        z = R.zleg(foot3)
        kx_, _ = R.p(kn3)
        f.add(up | lo, cfg['legs'], z=z, rl=1.5, rs=2.4, dim=dim, line='hard',
              tonemap=lambda X, Y, t, kx_=kx_, s=_ls(f): _cyl(X, Y, t, kx_, s))      # v2: the trouser leg reads round
        knees.append(R.p(kn3))
        fx, fy = R.p(foot3)
        # v2 polish (asset gate, volume): every boot shows a lit plane, its base and its shade
        if side:
            mb = (f.ell(fx + 1.6, fy - 2.6, 5.0, 2.9) | f.rect(fx - 3.2, fy - 7, fx + 2.4, fy - 2)) & (f.Y < fy)
            f.add(mb, cfg['boots'], z=z + 1, rl=1.6, rs=2.2, dim=dim, line='hard',
                  tonemap=lambda X, Y, t, fx=fx, fy=fy: _lit(f, X, Y, t, fx, 1.0, fy - 4.2, 2.6, 1.3))
        elif R.diag:
            surf.boot_3q(f, R, foot3, cfg['boots'], z + 1, dim=dim, cuff=False, shade=dict(rl=1.6))
        else:
            m = (f.ell(fx, fy - 2.6, 4.4, 3.0) | f.rect(fx - 3.5, fy - 7, fx + 3.5, fy - 2)) & (f.Y < fy)
            f.add(m, cfg['boots'], z=z + 1, rl=1.6, rs=2.2, line='hard',
                  tonemap=lambda X, Y, t, fx=fx, fy=fy: _lit(f, X, Y, t, fx, -1.5, fy - 4.0, 1.6, 2.4))
        f.anchor('foot_R' if lat > 0 else 'foot_L', fx, fy)
    # ---------------------------------------------------------------- skirt / hips
    waist = hy - 9.5
    tw = turn.Warp(f, R, (sx + hx) / 2, TW + 0.5, 0.75 * TW, vf) if R.diag else contextlib.nullcontext()
    tw.__enter__()
    kx = [k[0] for k in knees]
    sk = cfg.get('skirt')
    if sk:
        hem = hy + sk['hem']
        if side:
            fr = max(hx + HW, max(kx) + 4.0)
            bk = min(hx - HW - P['lag'] * 0.5, min(kx) - 4.0)
            m = f.poly([(hx - HW + 2, waist), (hx + HW - 1, waist), (fr, hem - 1), (fr - 5, hem + 0.5), (bk + 4, hem + 0.5), (bk, hem - 1)])
        else:
            wl = max(HW + 1.5, hx - min(kx) + 4.5)
            wr = max(HW + 1.5, max(kx) - hx + 4.5)
            m = f.poly([(hx - HW + 0.5, waist), (hx + HW - 0.5, waist), (hx + wr, hem - 1), (hx + wr - 3, hem + 0.5),
                        (hx - wl + 3, hem + 0.5), (hx - wl, hem - 1)])
        f.add(m, sk['mat'], z=20, rl=2, rs=3.2, vgrad=0.4, line='hard',
              tonemap=lambda X, Y, t: _folds(X, Y, t, hx, waist + 4, 3.5 if not side else 4.5))
    else:
        if side:
            f.add(f.ell(hx + 0.5, hy - 2.5, HW - 3.0, 4.5), cfg['legs'], z=19, rl=2, rs=3, line='hard')
        else:
            f.add(f.rect(hx - HW, hy - 7, hx + HW, hy + 1.5) | f.ell(hx, hy, HW, 4.2), cfg['legs'], z=13, rl=2, rs=3.5, vgrad=0.5, line='hard',
                  tonemap=lambda X, Y, t, s=_ls(f): _panels(X, Y, t, hx, 2.5, hy - 7.0, hy + 5.0, s))      # v2: lit and shaded seat planes
    # ---------------------------------------------------------------- torso
    if side:
        body = f.ell(sx + 0.5, sy + 4, TW - 1.0, 9) | f.rect(sx - TW + 2, sy + 2, sx + TW - 0.5, waist + 1.5)
    else:
        body = f.ell(sx, sy + 4, TW + 0.5, 9) | f.rect(sx - TW, sy + 2, sx + TW, waist + 1.5)
    f.add(body, cfg['top'], z=22, rl=2, rs=3.4, vgrad=0.3, line='hard',
          tonemap=(lambda X, Y, t, s=_ls(f): _panels(X, Y, t, sx, TW * 0.35, sy - 2.0, waist + 2.0, s)) )   # v2: lit and shaded chest (or back) planes
    if cfg.get('belt'):
        if side:
            f.add(f.rect(hx - HW + 1.5, waist - 1, hx + HW - 0.5, waist + 2), cfg['belt'], z=23, rl=1, rs=1.2, line='soft')
        else:
            f.add(f.rect(hx - HW - 0.5, waist - 1, hx + HW + 0.5, waist + 2), cfg['belt'], z=23, rl=1, rs=1.2, line='soft')
    ap = cfg.get('apron')
    if ap:
        atop, ahem = sy + ap['top'], hy + ap['hem']
        if vf == 'S':
            m = f.poly([(sx - TW * 0.62, atop), (sx + TW * 0.62, atop), (hx + HW * 0.85, waist), (hx + HW + 1, ahem), (hx - HW - 1, ahem), (hx - HW * 0.85, waist)])
            f.add(m, ap['mat'], z=24, rl=1.6, rs=2.6, vgrad=0.3, line='hard',
                  tonemap=lambda X, Y, t, s=_ls(f): _panels(X, Y, _folds(X, Y, t, hx, waist + 3, 4.0), hx, 4.0, atop + 1.0, ahem, s, not R.diag))
            for s_ in (-1, 1):
                f.add(f.cap(sx + TW * 0.55 * s_, atop, sx + TW * 0.8 * s_, sy - 2, 0.9), ap['mat'], z=24.2, flat=1, line='soft')
            if ap.get('pocket'):
                f.add(f.rect(hx - 4, waist + 3, hx + 4, waist + 7), ap['mat'], z=24.3, flat=1, line='soft')
        elif side:
            front = sx + TW - 2.5                       # just inside the chest's front edge
            fw = hx + HW - 2.5
            fh = max(fw + 1.0, max(kx) + 3.0)            # the hem rides on the front knee
            m = f.poly([(front - 2.5, atop), (front + 0.5, atop), (fw + 0.5, waist), (fh, ahem), (fh - 3.0, ahem + 0.5), (fw - 2.5, waist + 1)])
            f.add(m, ap['mat'], z=24, rl=1.4, rs=2.2, line='hard',
                  tonemap=lambda X, Y, t: _lit(f, X, Y, t, front - 1.0, 0.0, atop + 5.0, 1.8, 4.0))
            f.add(f.cap(sx + TW - 2, atop, sx - 1, sy - 2, 0.9), ap['mat'], z=24.2, flat=1, line='soft')
        else:   # N: the ties at the back of the waist and the neck strap
            f.add(f.ell(hx - 2, waist + 0.5, 2.0, 1.4) | f.ell(hx + 2, waist + 0.5, 2.0, 1.4), ap['mat'], z=24, rl=1, rs=1, line='hard')
            f.add(f.cap(hx - 1, waist + 1, hx - 3, waist + 6, 0.9) | f.cap(hx + 1, waist + 1, hx + 3, waist + 6, 0.9), ap['mat'], z=24.1, flat=1, line='soft')
            f.add(f.rect(hx - HW, waist - 0.5, hx + HW, waist + 1.5), ap['mat'], z=23.9, flat=1, line='soft')
    if cfg.get('torso_extra'):
        cfg['torso_extra'](f, R, P, ctx, (sx, sy, hx, hy, waist))
    tw.__exit__(None, None, None)
    # ---------------------------------------------------------------- arms
    arms = {}
    for key, sh, hh, lat in (('R', shR, hR, 1), ('L', shL, hL, -1)):
        far = R.far(lat)
        dim = _dim(R, far)
        pole = P['pole' + key] or (-1.0, -0.2, 0.6 * lat)
        z = P['z' + key] if P['z' + key] is not None else R.zarm(hh)
        up, lo, el3 = R.limb(sh, hh, 8.6, 8.4, cfg.get('arm_r', 3.4), 3.0, 2.8, pole)
        f.add(up, cfg['sleeve'], z=z, rl=1.4, rs=2.2, dim=dim, line='hard', cast=(1, 1, 1))
        f.add(lo, cfg['sleeve'] if cfg.get('forearm', 'sleeve') == 'sleeve' else cfg['skin'], z=z + 0.1, rl=1.4, rs=2.2, dim=dim, line='hard', cast=(1, 1, 1))
        if cfg.get('forearm') == 'skin':          # rolled sleeves: a cuff at the elbow
            ex, ey = R.p(el3)
            f.add(f.ell(ex, ey, 3.3, 2.6), cfg['sleeve'], z=z + 0.15, rl=1, rs=1.4, dim=dim, line='soft')
        px, py = R.p(sh)
        f.add(f.ell(px, py + 0.5, 4.2, 4.0) & (f.Y < py + 3), cfg['sleeve'], z=max(26, z + 0.15) if not far else z + 0.15,
              rl=1.4, rs=2.2, dim=dim, line='soft')
        arms[key] = (hh, z, far, el3)
    ctx['arms'] = arms
    if cfg.get('shawl'):
        if R.diag:
            with turn.Warp(f, R, sx, TW + 6.0, 0.8 * (TW + 3.5), vf):     # wide enough for the whole shawl
                _shawl(f, vf, sx, sy, cfg['shawl'], TW, P['lag'])
        else:
            _shawl(f, facing, sx, sy, cfg['shawl'], TW, P['lag'])
    if cfg.get('gear'):
        cfg['gear'](f, R, P, ctx)
    for key in ('R', 'L'):
        hh, z, far, _ = arms[key]
        x, y = R.p(hh)
        f.add(f.ell(x, y, cfg.get('hand_r', 3.0), cfg.get('hand_r', 3.0)), cfg['skin'], z=z + 0.8, rl=1.4, rs=2.0, dim=1 if far else 0, line='hard')
    # ---------------------------------------------------------------- head
    x0, y0 = R.p(head3)
    x0, y0 = float(round(x0)), float(round(y0)) + 2.0     # v2 polish: the head on whole pixels, so its 1 to 2 px
                                                          # details (band, eyes, strands) never boil between drawings
    _neck(f, facing, x0, y0, cfg)
    if R.diag:
        _head_3q(f, P, x0, y0, cfg, R.back)
    elif facing == 'S':
        _head_front(f, P, x0, y0, cfg)
    elif facing == 'N':
        _head_back(f, P, x0, y0, cfg)
    else:
        _head_side(f, P, x0, y0, cfg)
    if cfg.get('fx'):
        cfg['fx'](f, R, P, ctx)


# ------------------------------------------------------------------------------- pieces
def _ls(f):
    """The lit plane's screen sign for _lit, taken when the part is added (inside turn.Warp the
    drawing keeps its own sides; on a plain mirrored figure the offset mirrors)."""
    return -1 if (f.flip and getattr(f, '_twin', None) is None) else 1


def _panels(X, Y, t, c0, half, y0, y1, s, dark_side=True):
    """v2 polish (asset gate, volume): a hanging cloth as three planes split at its folds: the panel
    toward the upper-left light one tone up, the panel away one tone down (straight edges, no blobs)."""
    out = t.copy()
    band = (Y >= y0) & (Y <= y1) & (t == 2)
    d = (X - c0) * s
    lit = band & (d < -half - 1.0) & (d > -half - 5.5)  # a 4 to 5 px lit plane inside the fold, base tone either side
    dark = band & (d > half + (0.0 if dark_side else 2.0)) & (d < half + 7.0)    # turned (diagonal): a base strip first
    out[lit] = 3
    out[dark] = 1
    return out


def _dim(R, far):
    """The far side is dimmed only where it turns away from the upper-left light: in NE and SW the
    far side is on the screen's left, toward the light, so it is not dimmed (asset gate: light)."""
    return 1 if far and R.facing not in ('NE', 'SW') else 0


def _cyl(X, Y, t, cx, s, off=1.6, w=0.9):
    """A round limb: a light band left of its centre (screen terms) one tone up, the far edge one down."""
    out = t.copy()
    lit = (np.abs((X - cx) * s + off) < w) & (t >= 1) & (t <= 2)
    out[lit] = t[lit] + 1
    return out


def _lit(f, X, Y, t, c0, dx, cy, rx, ry, shade=False, s=None):
    """v2 polish (asset gate, volume): the plane of a part that faces the upper-left light takes
    the light tone (and with shade, the plane facing away takes the shadow tone), so it shows lit,
    base and shadow planes.  c0 is the part's centre in pivot terms, dx the screen offset of the
    lit plane (- = toward the light); on a mirrored figure the offset is mirrored, so the light
    stays upper left on screen."""
    s = _ls(f) if s is None else s
    out = t.copy()
    m = (((X - (c0 + dx * s)) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1.0) & (t >= 1) & (t <= 2)
    out[m] = t[m] + 1
    if shade:
        m2 = (((X - (c0 - dx * s)) / rx) ** 2 + ((Y - cy - ry * 0.6) / (ry * 1.2)) ** 2 <= 1.0) & (t == 2)
        out[m2] = 1
    return out


def _folds(X, Y, t, x0, y0, dx):
    out = t.copy()
    for k in (-1, 1):
        m = (abs(X - x0 - k * dx - (Y - y0) * 0.18 * k) < 0.55) & (Y > y0)
        out[m & (t >= 2)] = 1
    return out


def _shawl(f, facing, sx, sy, mat, TW, lag):
    w = TW + 3.5
    if facing in 'EW':
        m = f.poly([(sx - w + 3, sy - 4), (sx + w - 4, sy - 4), (sx + w - 2.5, sy + 4), (sx + 1, sy + 7), (sx - w + 1 - lag, sy + 9), (sx - w + 1.5, sy)])
    else:
        m = f.ell(sx, sy, w, 6.5) | f.poly([(sx - w, sy), (sx + w, sy), (sx + w - 2, sy + 7), (sx, sy + 10 if facing == 'S' else sy + 9), (sx - w + 2, sy + 7)])
        if facing == 'S':
            m &= ~f.poly([(sx - 3.5, sy - 6), (sx + 3.5, sy - 6), (sx, sy + 3)])
    f.add(m, mat, z=34, rl=1.8, rs=2.6, vgrad=0.4, line='hard', cast=(0, 1, 1),
          tonemap=lambda X, Y, t: _folds(X, Y, t, sx, sy + 1, 4.5))
    if facing == 'S':
        f.add(f.ell(sx, sy + 3, 1.6, 1.4), 'gold', z=34.5, rl=1, rs=1, line='hard')        # brooch


def _neck(f, facing, x0, y0, cfg):
    f.add(f.rect(x0 - 2.5, y0 + 6, x0 + 2.5, y0 + 11), cfg['skin'], z=30, rl=1, rs=1.4, line='hard')


def _eyes(f, P, xs, ey, h=3):
    for x in xs:
        if P['face'] == 'shut' or P['blink']:
            f.detail(f.rect(x, ey + h - 1, x + 2, ey + h), EYE)
        else:
            eye(f, x, ey, h)


def _mouth(f, P, x, y):
    if P['face'] == 'talk':
        f.detail(f.rect(x - 1, y, x + 1, y + 2), ('skin', 0))
    else:
        f.detail(f.rect(x - 1, y, x + 1, y + 1), ('skin', 0))


def _head_front(f, P, x0, hy, cfg):
    r = cfg.get('head', 1.0)
    sk = cfg['skin']
    f.add(f.ell(x0 - 8.2 * r, hy + 1.5, 1.8, 2.5) | f.ell(x0 + 8.2 * r, hy + 1.5, 1.8, 2.5), sk, z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy + 1.2, 7.9 * r, 8.4), sk, z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    _hair(f, x0, hy, cfg, 'S')
    _eyes(f, P, (x0 - 5, x0 + 3), hy + 0.5)
    _mouth(f, P, x0, hy + 6)
    f.dot(x0, hy + 4, (sk, 1))
    f.detail(f.rect(x0 - 7, hy + 4, x0 - 5, hy + 5), ('blush', 2))
    f.detail(f.rect(x0 + 5, hy + 4, x0 + 7, hy + 5), ('blush', 2))
    if cfg.get('face_extra'):
        cfg['face_extra'](f, P, x0, hy, 'S')


def _head_back(f, P, x0, hy, cfg):
    r = cfg.get('head', 1.0)
    f.add(f.ell(x0 - 8.2 * r, hy + 1.5, 1.8, 2.5) | f.ell(x0 + 8.2 * r, hy + 1.5, 1.8, 2.5), cfg['skin'], z=39, rl=1, rs=1.2, line='hard')
    f.add(f.ell(x0, hy + 1.0, 7.9 * r, 8.4), cfg['skin'], z=40, rl=2.0, rs=3.0, line='hard')
    _hair(f, x0, hy, cfg, 'N')


def _head_side(f, P, x0, hy, cfg):
    r = cfg.get('head', 1.0)
    sk = cfg['skin']
    f.add(f.ell(x0 + 1.6, hy + 1.2, 7.2 * r, 8.4), sk, z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    f.add(f.ell(x0 + 8.4 * r, hy + 3.2, 1.4, 1.4), sk, z=40.5, rl=1, rs=1, line='hard')
    _hair(f, x0, hy, cfg, 'E')
    f.add(f.ell(x0 - 1.8, hy + 2.0, 1.7, 2.5), sk, z=45, rl=1, rs=1.2, line='hard')
    _eyes(f, P, (x0 + 4,), hy + 0.5)
    if P['face'] == 'talk':
        f.detail(f.rect(x0 + 6, hy + 6, x0 + 8, hy + 8), (sk, 0))
    else:
        f.detail(f.rect(x0 + 6, hy + 6.5, x0 + 8, hy + 7.5), (sk, 0))
    f.detail(f.rect(x0 + 3, hy + 4.5, x0 + 5, hy + 5.5), ('blush', 2))
    if cfg.get('face_extra'):
        cfg['face_extra'](f, P, x0, hy, 'E')


def _head_3q(f, P, x0, hy, cfg, back):
    """v2 three-quarter head (drawn for SE / NE; SW / NW on the mirrored grid): the profile head
    turned a quarter back toward the camera.  Front: both eyes (the far one near the cheek's edge),
    the nose inside the face, the near ear moved back, the profile hair.  Back: the back of the
    head with only the near ear."""
    r = cfg.get('head', 1.0)
    sk = cfg['skin']
    if back:
        f.add(f.ell(x0 + 7.6 * r, hy + 1.8, 1.8, 2.5), sk, z=39, rl=1, rs=1.2, line='hard')
        f.add(f.ell(x0 + 0.6, hy + 1.0, 7.9 * r, 8.4), sk, z=40, rl=2.0, rs=3.0, line='hard')
        _hair(f, x0 + 0.6, hy, cfg, 'N')
        return
    f.add(f.ell(x0 + 1.0, hy + 1.2, 7.7 * r, 8.4), sk, z=40, rl=2.0, rs=3.0, line='hard', cast=(0, 2, 1))
    _hair(f, x0 - 0.4, hy, cfg, 'E')
    f.add(f.ell(x0 - 2.8, hy + 2.0, 1.7, 2.5), sk, z=45, rl=1, rs=1.2, line='hard')
    f.dot(x0 - 2.8, hy + 2.0, (sk, 1))
    _eyes(f, P, (x0 + 0.5, x0 + 5), hy + 0.5)
    _mouth(f, P, x0 + 3.5, hy + 6)
    f.dot(x0 + 4, hy + 4, (sk, 1))
    f.detail(f.rect(x0 - 1, hy + 4, x0 + 1, hy + 5), ('blush', 2))
    if cfg.get('face_extra'):
        cfg['face_extra'](f, P, x0 - 1, hy, 'E')


def _hair(f, x0, hy, cfg, fc):
    st = cfg['hair_style']
    hm = cfg['hair']
    if st == 'curly':              # short cropped curls
        if fc == 'S':
            cl = [(x0 - 6, hy - 6.5, 3.6), (x0, hy - 8, 3.9), (x0 + 6, hy - 6.5, 3.6), (x0 - 8.2, hy - 2, 2.8), (x0 + 8.2, hy - 2, 2.8),
                  (x0 - 3, hy - 4.5, 3.2), (x0 + 3, hy - 4.5, 3.2)]
        elif fc == 'N':
            cl = [(x0 - 6, hy - 6.5, 3.6), (x0, hy - 8, 3.9), (x0 + 6, hy - 6.5, 3.6), (x0 - 8, hy - 1.5, 3.2), (x0 + 8, hy - 1.5, 3.2),
                  (x0 - 4, hy - 1, 3.6), (x0 + 4, hy - 1, 3.6), (x0, hy + 2.5, 3.6), (x0 - 6, hy + 3, 2.6), (x0 + 6, hy + 3, 2.6)]
        else:
            cl = [(x0 - 4, hy - 7, 3.6), (x0 + 2, hy - 8, 3.8), (x0 + 6.5, hy - 5.5, 3.0), (x0 - 7, hy - 2.5, 3.2), (x0 - 5.5, hy + 2, 2.8),
                  (x0 - 1, hy - 4.5, 3.1)]
        for i, (cx, cy, rr) in enumerate(cl):
            f.add(f.ell(cx, cy, rr, rr * 0.9), hm, z=44 + i * 0.01, rl=1.2, rs=1.8, ts=0.3, line='hard' if i < 5 else None,
                  cast=(1, 1, 1) if i >= 5 else None)
    elif st == 'bun':               # hair drawn back to a bun on the crown, side parting
        if fc == 'S':
            cap = (f.ell(x0, hy - 2.8, 8.9, 7.8) & (f.Y < hy - 0.5)) | f.ell(x0 - 8.0, hy + 0.5, 2.0, 3.6) | f.ell(x0 + 8.0, hy + 0.5, 2.0, 3.6)
            cap &= ~(f.ell(x0 + 1, hy + 2.2, 7.0, 5.2) & (f.Y > hy - 3.5))
            f.add(cap, hm, z=44, rl=1.6, rs=2.4, line='hard', cast=(0, 1, 1),
                  tonemap=lambda X, Y, t: _strands(X, Y, t, x0 - 2, hy - 9, hy - 3))
            f.add(f.ell(x0, hy - 10.5, 4.2, 3.4), hm, z=43.5, rl=1.4, rs=2.0, line='hard')
        elif fc == 'N':
            f.add(f.ell(x0, hy - 1.0, 8.9, 8.6), hm, z=44, rl=1.6, rs=2.6, line='hard',
                  tonemap=lambda X, Y, t: _strands(X, Y, t, x0, hy - 9, hy + 6))
            f.add(f.ell(x0, hy - 8.5, 4.6, 3.8), hm, z=44.5, rl=1.4, rs=2.0, line='hard', cast=(0, 1, 1))
        else:
            cap = (f.ell(x0 - 0.5, hy - 2.8, 8.5, 7.8) & (f.Y < hy + 0.5)) | f.ell(x0 - 6, hy + 1.5, 3.4, 5.0)
            cap &= ~(f.ell(x0 + 5, hy + 2.6, 5.8, 5.6) & (f.Y > hy - 3.0))
            f.add(cap, hm, z=44, rl=1.6, rs=2.4, line='hard', cast=(0, 1, 1),
                  tonemap=lambda X, Y, t: _strands(X, Y, t, x0 - 1, hy - 9, hy - 2))
            f.add(f.ell(x0 - 5.5, hy - 8.0, 4.0, 3.4), hm, z=44.2, rl=1.4, rs=2.0, line='hard')
    elif st == 'bob':               # a chin-length bob with a fringe
        if fc == 'S':
            cap = f.ell(x0, hy - 2.0, 9.4, 8.6) | f.ell(x0 - 8.0, hy + 4.0, 2.6, 5.0) | f.ell(x0 + 8.0, hy + 4.0, 2.6, 5.0)
            cap &= ~(f.ell(x0, hy + 3.5, 6.6, 6.0) & (f.Y > hy - 1.0))
            fringe = f.poly([(x0 - 8, hy - 4), (x0 - 6.5, hy + 0.5), (x0 - 2, hy - 1.5), (x0 + 2.5, hy), (x0 + 7, hy - 1.5), (x0 + 8, hy - 4)])
            f.add(cap | fringe, hm, z=44, rl=1.8, rs=2.4, line='hard', cast=(0, 1, 1),
                  tonemap=lambda X, Y, t: _strands(X, Y, t, x0 + 1, hy - 9, hy - 2))
        elif fc == 'N':
            f.add(f.ell(x0, hy - 1.0, 9.4, 9.0) | f.rect(x0 - 9.2, hy, x0 + 9.2, hy + 7.5), hm, z=44, rl=1.8, rs=2.6, line='hard',
                  tonemap=lambda X, Y, t: _strands(X, Y, t, x0, hy - 9, hy + 8))
        else:
            cap = f.ell(x0 - 0.5, hy - 2.0, 9.0, 8.6) | f.ell(x0 - 5.5, hy + 3.5, 4.0, 5.2)
            cap &= ~(f.ell(x0 + 5.0, hy + 3.2, 5.8, 6.0) & (f.Y > hy - 1.5))
            fringe = f.poly([(x0 + 1, hy - 7), (x0 + 3, hy - 0.5), (x0 + 6, hy - 1.5), (x0 + 8.8, hy - 5)])
            f.add(cap | fringe, hm, z=44, rl=1.8, rs=2.4, line='hard', cast=(0, 1, 1),
                  tonemap=lambda X, Y, t: _strands(X, Y, t, x0 - 1, hy - 9, hy - 2))
    if cfg.get('band'):
        bm = cfg['band']
        if fc == 'S':
            m = f.rect(x0 - 9, hy - 6.5, x0 + 9, hy - 4.5) & f.ell(x0, hy - 3, 9.6, 9)
        elif fc == 'N':
            m = f.rect(x0 - 9.4, hy - 6.5, x0 + 9.4, hy - 4.5) & f.ell(x0, hy - 2, 9.8, 9.5)
            f.add(f.ell(x0 + 2.5, hy - 4, 1.8, 1.4) | f.cap(x0 + 2.5, hy - 4, x0 + 4.5, hy + 1, 0.9), bm, z=45.6, rl=1, rs=1, line='hard')
        else:
            m = f.rect(x0 - 9, hy - 6.5, x0 + 9, hy - 4.5) & f.ell(x0, hy - 3, 9.4, 9)
        f.add(m, bm, z=45.5, rl=1, rs=1.2, line='hard')


def _strands(X, Y, t, x0, y0, y1):
    out = t.copy()
    for k in (-3.5, 0.5, 4):
        m = (abs(X - x0 - k - (Y - y0) * 0.12) < 0.5) & (Y > y0 + 1) & (Y < y1)
        out[m & (t >= 2)] = 1
    return out
