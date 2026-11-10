"""Shared builder pieces for the woodland creatures (shardstruck enemies): rounded body volumes
projected through parts.Rig, four short legs, eyes, the lodged Starfall shard, thorns.

Body space as the cast: (fwd, up, lat), lat + = the creature's right; S faces the camera.
A creature pose (P) uses: bob, pitch (body nose-down +, screen radians in profile), crouchF and
crouchH (front and hind lowering), gait (0..1 phase, None standing), stride (px), head
(fwd, up offset of the head), mouth (0..1), shard (None lodged, or 0..1 how far it has popped
out), calm (0..1: eyes soften, glow fades), blink, shake (px, a side-to-side shiver), fx.
Every volume is shaded by ew with an upper-left light, so each reads with a lit top, a mid tone
and a dark underside; the runtime adds the soft contact shadow under the feet."""
import math
import numpy as np
from ew import mat
from parts import Rig, K
import palette  # noqa: F401
import anim

# the Starfall shard: violet glass with a hot white core (one ramp for every creature)
mat('shard',  ['#24164E', '#4C30A2', '#8A66EA', '#CDB8FF', '#FFFFFF'])
mat('shardglow', ['#3C2C86', '#6A52CE', '#A890FF', '#E4DAFF', '#FFFFFF'])
mat('thorn',  ['#24160E', '#432A1A', '#684428', '#8E643C'])
mat('tell',   ['#7A2E06', '#C4560C', '#F28A1E', '#FFC060', '#FFF0C0'])   # the reserved telegraph colour


def P0(**k):
    p = dict(bob=0.0, pitch=0.0, crouchF=0.0, crouchH=0.0, gait=None, stride=5.0, lift=2.5,
             head=(0.0, 0.0), mouth=0.0, shard=None, calm=0.0, blink=False, shake=0.0, fx=0,
             tell=0.0, lat=0.0)
    p.update(k)
    return p


def add3(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def blob_mask(f, R, c3, L, W, H, ang=0.0):
    x, y = R.p(c3)
    if R.facing in 'EW':
        return f.rell(x, y, L / 2.0 + 0.1 * W / 2.0, H / 2.0, ang)
    return f.ell(x, y, W / 2.0, math.sqrt((H / 2.0) ** 2 + (K * L / 2.0) ** 2))


def px(f, tm):
    """A texture tonemap in screen pixels: at a larger Fig scale the tufts, warts and plates stay
    the same pixel size and there are more of them (detail, not an upscale)."""
    if tm is None or f.scale == 1:
        return tm
    k = f.scale
    return lambda X, Y, t: tm(X * k, Y * k, t)


def planes(f, mask, tonemap=None, lit=0.30, dark=0.70):
    """'Nothing flat': a tonemap giving a large volume a lit upper-left plane, the mid plane and a
    dark lower plane across its interior (ew's shading alone lights only the rims)."""
    ys, xs = np.where(mask)
    if not len(ys):
        return tonemap
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    w, h = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:f.H, 0:f.W]          # masks are in screen space, so W needs no mirroring
    lx, ly = x0 + 0.36 * w, y0 + 0.30 * h
    litm = ((xx - lx) / (0.30 * w)) ** 2 + ((yy - ly) / (0.24 * h)) ** 2 < 1.0
    darkm = (yy - y0) > dark * h + 0.06 * h * np.sin((xx - x0) * 0.7)

    # reflected light: a thin band just inside the lower edge, bounced up from the ground,
    # one tone above the dark belly it sits in
    below2 = np.zeros_like(mask)
    below2[:-2] = mask[2:]
    below1 = np.zeros_like(mask)
    below1[:-1] = mask[1:]
    refl = mask & below1 & ~below2 & ((yy - y0) > 0.55 * h)

    def tm(X, Y, t):
        t = t.copy()
        t[litm & (t == 2)] = 3
        t[darkm & (t == 2)] = 1
        if tonemap:
            t = tonemap(X, Y, t)
        r = refl & (t <= 1)
        t[r] = 2
        return t
    return tm


def hash2(ix, iy, seed=0.0):
    """A repeatable pseudo-random value in [0, 1) per integer cell (no visible grid)."""
    v = np.sin(ix * 12.9898 + iy * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


def fur(cw=4, ch=3, dark_from=1, seed=0.0, density=(0.8, 0.62, 0.3, 0.0)):
    """Directional fur: short strokes in scattered clusters that follow the form. On the lit top
    plane they lie flat along the spine and are sparse (none where the light is strongest); on the
    mid flank they slant down and back; in the shade they hang steeper and crowd together. Each
    stroke is one tone darker than the plane it lies on; a few lit flanks get a light tip."""
    def tm(X, Y, t):
        xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
        cy = yi // ch
        jitter = np.floor(hash2(cy, 0, seed) * cw).astype(int)
        cx = (xi + jitter) // cw
        lx = (xi + jitter) % cw
        ly = yi % ch
        r = hash2(cx, cy, seed)
        dens = np.select([t <= 1, t == 2, t == 3], list(density[:3]), density[3])
        on = r < dens
        # the stroke: 3 px flat on the lit plane, 2 px and a step down on the flank, a short
        # steep hook in the shade (4-connected, so the despeckle keeps them)
        flat = (ly == 1) & (lx <= 2)
        slant = ((ly == 1) & (lx <= 1)) | ((ly == 2) & (lx == 1))
        steep = ((lx == 1) & (ly >= 0)) | ((ly == 2) & (lx == 0))
        shape = np.where(t >= 3, flat, np.where(t == 2, slant, steep))
        stroke = on & shape & (t >= dark_from) & (t <= 3)
        out = t.copy()
        out[stroke] = t[stroke] - 1
        tip = on & (t == 2) & (ly == 0) & (lx == 2) & (r < dens * 0.35)
        out[tip] = 3
        return out
    return tm


def warts(seed=0.0, n_per=0.16):
    """A few irregular warts: 1-3 px bumps scattered at random, one tone darker with a lit pixel
    on the upper left; more of them on the shaded flank."""
    def tm(X, Y, t):
        xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
        cx, cy = xi // 3, yi // 3
        r = hash2(cx, cy, seed)
        size = 2 + (hash2(cx, cy, seed + 3.1) * 1.6).astype(int)        # 2..3 px
        ox = (hash2(cx, cy, seed + 1.7) * 2).astype(int)
        oy = (hash2(cx, cy, seed + 2.3) * 2).astype(int)
        lx, ly = xi % 3 - ox, yi % 3 - oy
        dens = np.where(t <= 2, n_per * 1.6, n_per * 0.6)
        bump = (r < dens) & (lx >= 0) & (ly >= 0) & (lx < size) & (ly < size - (lx == size - 1))
        out = t.copy()
        m = bump & (t >= 1) & (t <= 3)
        out[m] = t[m] - 1
        lit = bump & (lx == 0) & (ly == 0) & (size >= 2) & (t >= 2) & (t <= 3)
        out[lit] = t[lit] + 1
        return out
    return tm


def volume(f, R, parts3, m, z, ang=0.0, rl=2.0, rs=3.0, vgrad=0.45, tag=None, tonemap=None, dim=0, cast=(1, 2, 1)):
    """Several ellipsoids [(c3, L, W, H)] merged into one shaded volume (no seams between them),
    with lit, mid and dark planes."""
    mask = None
    for c3, L, W, H in parts3:
        mm = blob_mask(f, R, c3, L, W, H, ang)
        mask = mm if mask is None else mask | mm
    zz = z + 0.03 * R.d(parts3[0][0])
    return f.add(mask, m, z=zz, rl=rl, rs=rs, vgrad=vgrad, line='hard', cast=cast, deep=True, tag=tag,
                 tonemap=planes(f, mask, px(f, tonemap)), dim=dim)


def blob(f, R, c3, L, W, H, m, z, ang=0.0, rl=2.0, rs=3.0, vgrad=0.45, tag=None, tonemap=None, dim=0, cast=(1, 2, 1), deep=True):
    """An ellipsoid L long (fwd), W wide (lat), H tall, centred at c3, as one shaded volume."""
    x, y = R.p(c3)
    if R.facing in 'EW':
        rx, ry = L / 2.0 + 0.1 * W / 2.0, H / 2.0
        mask = f.rell(x, y, rx, ry, ang if R.facing == 'E' else ang)
    else:
        rx = W / 2.0
        ry = math.sqrt((H / 2.0) ** 2 + (K * L / 2.0) ** 2)
        mask = f.ell(x, y, rx, ry)
    zz = z + 0.03 * R.d(c3)
    return f.add(mask, m, z=zz, rl=rl, rs=rs, vgrad=vgrad, line='hard', cast=cast, deep=deep, tag=tag, tonemap=px(f, tonemap), dim=dim), (x, y)


def legs(f, R, P, hips, foot_fwd, m, z0, r0=2.6, r1=2.0, hoof=None, length=None, tonemap=None):
    """Four legs: hips = [(fwd, up, lat) x4] in body space (FR, FL, HR, HL); feet under them,
    stepping with P['gait'] (diagonal pairs) or planted.  Returns the feet (pivot space)."""
    feet = []
    for i, h3 in enumerate(hips):
        front = i < 2
        fwd = foot_fwd[i]
        lift = 0.0
        if P['gait'] is not None:
            ph = (P['gait'] + (0.0 if i in (0, 3) else 0.5)) % 1.0
            fwd -= P['stride'] * math.cos(2 * math.pi * ph)        # stance half (ph .5..1) sweeps back
            lift = max(0.0, P['lift'] * math.sin(2 * math.pi * ph))
        lift += (P.get('lifts') or (0, 0, 0, 0))[i]
        foot3 = (fwd, lift + P.get('ground', 0.0), h3[2])
        hx, hy = R.p(h3)
        fx, fy = R.p(foot3)
        fy -= 1.0 / f.scale                         # the sole's outline lands on the pivot row
        far = R.far(h3[2])
        dim = 1 if far else 0
        zl = z0 + 0.1 * R.d(foot3) - (3.0 if (R.facing == 'N' and front) or (R.facing == 'S' and not front) else 0.0)
        f.add(f.cap(hx, hy, fx, fy - 1.0, r0, r1) & (f.Y < fy + 1.0 / f.scale), m, z=zl, rl=1.2, rs=1.8, vgrad=0.6, deep=True, dim=dim, line='hard', tonemap=px(f, tonemap))   # legs darken toward the hoof; the far pair dimmer
        if hoof:
            f.add(f.ell(fx, fy - 1.2, r1 + 0.6, 1.4) & (f.Y < fy), hoof, z=zl + 0.1, rl=1, rs=1, dim=dim, line='hard')
        feet.append((fx, fy))
        f.anchor(('foot_R', 'foot_L', 'hind_R', 'hind_L')[i], fx, fy)
    return feet


def eye(f, x, y, calm=0.0, blink=False, glow=True, size=2):
    """A creature eye: shardstruck eyes glow violet at the rim; freed (calm 1) they turn soft and
    dark with a white glint."""
    if blink:
        f.detail(f.rect(x - 1, y + 1, x + size, y + 2), ('crack', 0))
        return
    f.detail(f.rect(x - 1, y - 1, x + size, y + size), ('crack', 0))
    if glow and calm < 0.5:
        f.dot(x, y, ('shardglow', 3))
    else:
        f.dot(x, y - 1, ('fletch', 3))


def shard(f, R, root3, axis3, size, P, z):
    """The lodged Starfall shard: a faceted crystal standing out of root3 along axis3, size px
    long, with a glow ring.  P['shard'] (0..1) pops it out: it rises, tumbles and is gone by 1."""
    t = P['shard']
    a = np.array(axis3, float)
    a /= np.linalg.norm(a) or 1.0
    base = np.array(root3, float)
    spin = 0.0
    if t is not None:
        # freed: the shard works loose (it rises a little out of the wound, still touching) and is
        # gone by t 0.3; its flight is a separate effect the runtime spawns at the 'shard' anchor
        if t >= 0.3:
            f.anchor('shard', *R.p(tuple(base + a * size)))
            return
        base = base + a * (3.0 * t / 0.3)
    tip = base + a * size
    (bx, by), (tx, ty) = R.p(tuple(base)), R.p(tuple(tip))
    dx, dy = tx - bx, ty - by
    if spin:
        c, s = math.cos(spin), math.sin(spin)
        dx, dy = dx * c - dy * s, dx * s + dy * c
        tx, ty = bx + dx, by + dy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    w = size * 0.32
    poly = [(bx - px * w * 0.6, by - py * w * 0.6), (bx + ux * L * 0.55 - px * w, by + uy * L * 0.55 - py * w), (tx, ty),
            (bx + ux * L * 0.55 + px * w, by + uy * L * 0.55 + py * w), (bx + px * w * 0.6, by + py * w * 0.6)]
    zz = z if t is None else 62
    # clean facets: the crystal in its mid tone with one rim (the outline), the face toward the
    # light one tone up, the base half of the far face one tone down, one glint
    mid = (bx + ux * L * 0.55, by + uy * L * 0.55)
    left = (mid[0] - px * w, mid[1] - py * w)
    right = (mid[0] + px * w, mid[1] + py * w)
    b0 = (bx - px * w * 0.6, by - py * w * 0.6)
    b1 = (bx + px * w * 0.6, by + py * w * 0.6)
    lit_left = (px * 0.6 + py * 0.8) > 0          # which side faces the upper-left light
    with f.tagging('shard'):
        f.add(f.poly(poly), 'shard', z=zz, flat=2, line='hard', deep=False)
        axis = [(bx, by), (tx, ty)]
        if lit_left:
            litf = f.poly([b0, left, (tx, ty)] + axis[:1][::-1])
            darkf = f.poly([(bx, by), b1, right, mid])
        else:
            litf = f.poly([b1, right, (tx, ty), (bx, by)])
            darkf = f.poly([(bx, by), b0, left, mid])
        f.detail(litf & f.poly(poly), ('shard', 3), z=zz + 0.05)
        f.detail(darkf & f.poly(poly), ('shard', 1), z=zz + 0.05)
        gx, gy = bx + ux * L * 0.62 + (-px if lit_left else px) * w * 0.35, by + uy * L * 0.62 + (-py if lit_left else py) * w * 0.35
        f.dot(gx, gy, ('shard', 4), z=zz + 0.1)
    f.anchor('shard', tx, ty)


def thorns(f, R, pts3, up3, length, z, m='thorn', tag=None):
    """Thorns standing out of a ridge: one small triangle per point, pointing along up3."""
    u = np.array(up3, float)
    u /= np.linalg.norm(u) or 1.0
    for p3 in pts3:
        b = np.array(p3, float)
        (bx, by), (tx, ty) = R.p(tuple(b)), R.p(tuple(b + u * length))
        L = math.hypot(tx - bx, ty - by) or 1.0
        px, py = -(ty - by) / L, (tx - bx) / L
        tri = f.poly([(bx - px * 1.6, by - py * 1.6), (tx, ty), (bx + px * 1.6, by + py * 1.6)])
        f.add(tri, m, z=z + 0.02 * R.d(p3), rl=0.8, rs=1, line='hard', tag=tag, deep=False)


def dust(f, x, y, t, z=58):
    """A kicked-up dust puff at ground point (x, y), t 0..1 (finite: gone by 1)."""
    if t is None or t >= 1:
        return
    for i, (dx, dy) in enumerate(((-4, 0), (-7, -1), (-2, -1), (-9, 0))):
        r = 0.7 + 0.9 * t
        f.add(f.ell(x + dx * (0.5 + t), y + dy * (0.5 + t), r, r * 0.8), 'cream', z=z + i * 0.01, rl=1, rs=1, line=None, deep=False)


def stars(f, x, y, t, z=60):
    """Dazed: three small sparks circling over the head (stagger)."""
    for i in range(3):
        a = 2 * math.pi * (t + i / 3)
        f.dot(x + 6 * math.cos(a), y + 2.0 * math.sin(a), ('gold', 2 if i == 0 else 1), z=z)


def draw_fig(build, facing, P, scale=1.0):
    from ew import Fig
    f = Fig(anim.CELL[0], anim.CELL[1], gx=anim.PIVOT[0], gy=anim.FIG_GY, flip=(facing == 'W'), scale=scale)
    f.despeckle = True
    build(f, facing, P)
    return f
