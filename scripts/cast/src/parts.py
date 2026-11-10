"""Shared parts for every character: two-segment limbs, eyes, boots, hands, the walk table."""
import math

EYE = '#1E1917'
GLINT = '#FFFDF5'


def knee(ax, ay, bx, by, l1, l2, bend):
    """Middle joint of a two-segment limb from a to b; bend > 0 pushes it toward +x (screen)."""
    dx, dy = bx - ax, by - ay
    d = max(1e-6, math.hypot(dx, dy))
    dc = min(d, l1 + l2 - 0.01)
    a = (l1 * l1 - l2 * l2 + dc * dc) / (2 * dc)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    mx, my = ax + a * dx / d, ay + a * dy / d
    nx, ny = -dy / d, dx / d
    if nx * bend < 0 or (nx == 0 and ny * bend < 0):
        nx, ny = -nx, -ny
    return mx + h * nx, my + h * ny


def limb(f, a, b, l1, l2, r0, r1, r2, bend):
    """Mask of a tapered two-segment limb and its middle joint."""
    kx, ky = knee(a[0], a[1], b[0], b[1], l1, l2, bend)
    return f.cap(a[0], a[1], kx, ky, r0, r1) | f.cap(kx, ky, b[0], b[1], r1, r2), (kx, ky)


def eye(f, x, y, h=3, glint=True, w=2):
    """Eastward eye: a 2 px wide dark bar, a warm glint at its upper left (light side)."""
    f.detail(f.rect(x, y, x + w, y + h), EYE, tag='face')
    if glint:
        f.dot(x, y, GLINT, tag='face')


def boot_side(f, x, y, mat, z, dim=0, toe=1.6, h=7):
    """Side-view boot: rounded toe forward (+x), flat sole."""
    m = f.ell(x + toe, y - 2.6, 5.0, 2.9) | f.rect(x - 3.2, y - h, x + 2.4, y - 2)
    m &= f.Y < y
    return f.add(m, mat, z=z, rl=1.6, rs=2.2, dim=dim, line='hard')


def boot_front(f, x, y, mat, z, dim=0):
    m = f.ell(x, y - 2.6, 4.6, 3.0) | f.rect(x - 3.6, y - 8, x + 3.6, y - 2)
    m &= f.Y < y
    return f.add(m, mat, z=z, rl=1.6, rs=2.2, dim=dim, line='hard')


# Walk: 8 drawings (contact, down, passing, up, then the other foot).  The planted foot moves
# back 3.5 px a drawing, so the body travels 3.5 px per drawing with no foot slide.
#            near (x, lift)   far (x, lift)   body bob (+ = down)
WALK = [((7.0, 0), (-7.0, 0), 0),
        ((3.5, 0), (-6.0, 1.5), 1),
        ((0.0, 0), (-1.0, 3.5), 0),
        ((-3.5, 0), (3.5, 2.5), -1),
        ((-7.0, 0), (7.0, 0), 0),
        ((-6.0, 1.5), (3.5, 0), 1),
        ((-1.0, 3.5), (0.0, 0), 0),
        ((3.5, 2.5), (-3.5, 0), -1)]
WALK_MS = [100] * 8
WALK_STEP = 3.5


# ================================================================================ 3D pose rig
# Body space (art pixels, origin at the ground pivot under the feet):
#   fwd = toward where the character faces, up = height above the ground, lat = toward the
#   character's anatomical RIGHT.  A pose places joints and hands in body space; proj() turns
#   a body-space point into pivot-space screen coordinates for one facing, plus a depth
#   (larger = nearer the camera).  West is drawn on Fig(flip=True), so its screen x is the
#   east x and the Fig mirrors it; only the depth changes (the left side is near).
#
#   S: the character faces the camera.  Its right is on the viewer's left.
#   N: back to the camera.  Its right is on the viewer's right.
#   E: profile to the right.  Its right side is near.
#   W: profile to the left.  Its left side is near.
#
# The camera looks down at about 3/4, so ground distance toward or away from the camera is
# shown at K of its length (a foot stepping toward the camera drops K px per px).
K = 0.35
SKEW = 0.10        # in profile the far shoulder shows a little ahead of the near one


# Contract v2: eight facings.  The facing's ground direction is at angle ANG (degrees, 0 = east,
# + toward the camera).  SW, W and NW are drawn on a mirrored grid (Fig(flip=True)) from the
# SE, E and NE geometry with the lateral axis negated, so the left side is the near one and
# one-sided gear stays on its real side (never a flipped image).
FACINGS8 = ('S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW')
ANG = {'E': 0.0, 'SE': 45.0, 'S': 90.0, 'NE': -45.0, 'N': -90.0}
MIRROR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}
FLIP = set(MIRROR)
BACK = {'N', 'NE', 'NW'}             # the back is toward the camera
DIAG = {'SE', 'NE', 'SW', 'NW'}
# screen direction of each facing (x right, y down), for runtime aim and release directions
VEC = {'E': (1.0, 0.0), 'W': (-1.0, 0.0), 'S': (0.0, 1.0), 'N': (0.0, -1.0),
       'SE': (0.7071, 0.7071), 'SW': (-0.7071, 0.7071), 'NE': (0.7071, -0.7071), 'NW': (-0.7071, -0.7071)}


def proj(facing, p):
    """Body space -> (pivot-space x before the Fig's mirror, y, depth toward the camera).
    General camera: the ground point (fwd, lat) is rotated by the facing angle a; the part of it
    toward the camera (gy) is foreshortened by K on screen and is the depth.  The cardinal facings
    are exactly pass 2's (a pure profile keeps no lateral foreshortening, only the shoulder SKEW)."""
    fwd, up, lat = p
    if facing in MIRROR:
        facing, lat = MIRROR[facing], -lat
    if facing == 'S':
        return -lat, -up + K * fwd, fwd
    if facing == 'N':
        return lat, -up - K * fwd, -fwd
    if facing == 'E':
        return fwd - SKEW * lat, -up, lat
    a = math.radians(ANG[facing])
    c, s = math.cos(a), math.sin(a)
    gx = fwd * c - lat * s
    gy = fwd * s + lat * c
    return gx - SKEW * lat * c, -up + K * gy, gy


def v3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def ik3(a, b, l1, l2, pole):
    """Middle joint of a two-bone chain from a to b in 3D, bending toward the pole direction."""
    d = np.subtract(b, a).astype(float)
    dist = max(1e-6, float(np.linalg.norm(d)))
    u = d / dist
    dc = min(dist, l1 + l2 - 0.01)
    x = (l1 * l1 - l2 * l2 + dc * dc) / (2 * dc)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    pv = np.array(pole, float)
    pv = pv - u * pv.dot(u)
    n = np.linalg.norm(pv)
    if n < 1e-6:
        pv = np.array([0.0, 0.0, 1.0]) - u * u[2]
        n = np.linalg.norm(pv) or 1.0
    pv /= n
    j = np.array(a, float) + u * x + pv * h
    return tuple(j)


class Rig:
    """Projects body-space points for one figure and facing, and picks depths (z) for limbs."""

    def __init__(self, f, facing):
        self.f, self.facing = f, facing
        self.side = facing in ('E', 'W')
        self.diag = facing in DIAG
        self.back = facing in BACK
        self.base = MIRROR.get(facing, facing)     # the unmirrored geometry (SE for SW ...)

    def vis(self, n3):
        """How much a surface with body-space normal n3 faces the camera (-1..1)."""
        v = np.array(n3, float)
        v = v / (np.linalg.norm(v) or 1.0)
        return self.d(tuple(v))

    def p(self, p3):
        x, y, _ = proj(self.facing, p3)
        return x, y

    def d(self, p3):
        return proj(self.facing, p3)[2]

    body_half = 9.5          # half the torso's width (lat); a hand inside it is over or behind the torso

    def zarm(self, p3, near=30.0, far=6.0):
        """Arms: in front of the torso unless the hand is clearly behind the body plane.  From
        behind (N), a hand in front of the chest and within the torso's width (a cross-body
        reach, a two-handed grip) is hidden by the back, so the arm takes the far depth."""
        dd = self.d(p3)
        if self.facing in BACK and p3[0] > 0.5 and abs(p3[2]) < self.body_half and p3[1] < 50:
            return far + 0.05 * dd
        if dd >= -3.5:
            # a hand above the shoulders passes over the head; one raised to chest height on
            # the near side passes over the beard and collar
            if p3[1] > 50 or (p3[1] > 37 and dd > 3.0 and p3[0] > 6.0):
                return 46.0 + 0.05 * dd
            return near + 0.05 * dd
        return far + 0.05 * dd

    def zleg(self, p3):
        return 10 + 0.1 * self.d(p3)

    def far(self, lat):
        """Is a point on this lateral side the far side (dimmed) in this facing?"""
        if self.facing in ('E', 'SE', 'NE'):
            return lat < 0
        if self.facing in ('W', 'SW', 'NW'):
            return lat > 0
        return False

    def limb(self, a3, b3, l1, l2, r0, r1, r2, pole):
        j3 = ik3(a3, b3, l1, l2, pole)
        # reach ratio of this limb (> 1: the end is past full extension and the limb stretches)
        self.f.__dict__.setdefault('reach', []).append(float(np.linalg.norm(np.subtract(b3, a3))) / (l1 + l2))
        a, j, b = self.p(a3), self.p(j3), self.p(b3)
        f = self.f
        up = f.cap(a[0], a[1], j[0], j[1], r0, r1)
        lo = f.cap(j[0], j[1], b[0], b[1], r1, r2)
        return up, lo, j3


import numpy as np  # noqa: E402
