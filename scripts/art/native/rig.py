"""The character rig: one set of proportions, a skeleton, four facings and the frame timing for
every folk and familiar (docs/vision/cast.md: fourteen folk, each with the Grassling a step
behind). Bramble and the Mossling are its first instances.

Units: one unit is one texel at density 2 (an adult 50 units, feet to crown); a folk's own
height scales its gait (`Folk.height`). Facings S, N, E, W are all drawn: W is drawn from the
E geometry on a mirrored grid (so the light stays upper left) with the instance's asymmetric
parts (a satchel on one hip, a strap over one shoulder) moved to the side they are really on.

    TIMING['walk'] -> frames and ms per frame; TIMING['idle'] the same
    pose(folk, action, facing, i) -> Pose: the skeleton for that frame (shared by every folk)
    frame(folk, d, action, facing, i) -> RGBA image, foot at (W / 2, H - pad)
    sheet(folk, d) -> (image, meta): rows = facing x action, columns = frames

A new folk is a Folk with its proportions, families and a draw function per facing (front,
back, profile) that hangs its parts on the Pose's joints.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from . import raster as pk

FACINGS = ('S', 'N', 'E', 'W')
# frame timing shared by every folk and familiar (anticipate, act, settle: the idle breath
# lingers at rest; the walk is an even six-step cycle at the zones' walking speed)
TIMING = {
    'idle': {'frames': 4, 'ms': [420, 260, 420, 260]},
    'walk': {'frames': 6, 'ms': [110] * 6},
}


@dataclass
class Pose:
    """The skeleton for one frame, in units from the feet's centre (y up is negative)."""
    bob: float = 0.0          # body lift (negative = up)
    breath: float = 0.0       # chest rise
    foot_a: tuple = (0.0, 0.0)   # near/left foot (x offset, lift)
    foot_b: tuple = (0.0, 0.0)
    arm_a: float = 0.0        # swing of each arm (units, forward positive)
    arm_b: float = 0.0
    sway: float = 0.0
    lag: float = 0.0          # follow-through for tails, capes and ears (-1..1)
    squash: float = 0.0       # 0..1, for familiars that hop
    lift: float = 0.0         # a hop's height


@dataclass
class Folk:
    name: str
    height: float                    # units, feet to crown (ear tips)
    frame: tuple = (64, 60)          # frame size in units
    pad: float = 4                   # units of ground under the soles
    gait: str = 'walk'               # 'walk' (two legs) or 'hop' (a familiar)
    draw: dict = field(default_factory=dict)   # facing kind ('front', 'back', 'side') -> fn(sp, pose, d, facing)


def _px(d, u):
    """A motion of u units as whole texels at density d (at least one texel when u != 0)."""
    s = d / 2.0
    v = u * s
    if v == 0:
        return 0
    r = int(round(v))
    if r == 0:
        r = 1 if v > 0 else -1
    return r / s


def pose(folk: Folk, d: float, action: str, facing: str, i: int) -> Pose:
    """The shared gait. Walk: a six-step cycle, the body up a texel on the passing frames, feet
    lifting 4 units and striding 1.6 (front/back) or 6.4 (profile), arms swinging against the
    legs, a tail or cape lagging 0.9 rad behind. Idle: four frames, the chest rising on the
    middle two. Hop (familiars): lift on the airborne frames, squash on the landings."""
    k = folk.height / 50.0
    n = TIMING[action]['frames']
    ph = 2 * math.pi * i / n
    side = facing in ('E', 'W')
    if folk.gait == 'hop':
        if action == 'walk':
            return Pose(lift=_px(d, 2.0 * k) if i in (1, 2, 4, 5) else 0, squash=1.0 if i in (0, 3) else 0.0,
                        foot_a=(1.4 * math.cos(ph), 0), foot_b=(-1.4 * math.cos(ph), 0), lag=math.sin(ph))
        return Pose(squash=1.0 if i in (1, 2) else 0.0)
    if action == 'walk':
        bob = -(_px(d, 1.0) if (i % 3) != 0 else 0)
        if side:
            st = 6.4 * k
            fa = (math.cos(ph) * st, -max(0.0, -math.sin(ph)) * 4.0 * k)
            fb = (-math.cos(ph) * st, -max(0.0, math.sin(ph)) * 4.0 * k)
            arm_a, arm_b = -math.cos(ph) * 4.0 * k, math.cos(ph) * 4.0 * k
        else:
            fa = (math.cos(ph) * 1.6 * k, -max(0.0, -math.sin(ph)) * 4.0 * k)
            fb = (-math.cos(ph) * 1.6 * k, -max(0.0, math.sin(ph)) * 4.0 * k)
            arm_a, arm_b = -math.cos(ph) * 3.0 * k, math.cos(ph) * 3.0 * k
        return Pose(bob=bob, foot_a=fa, foot_b=fb, arm_a=arm_a, arm_b=arm_b, sway=math.sin(ph), lag=math.sin(ph - 0.9))
    return Pose(breath=_px(d, 1.0) if i in (1, 2) else 0, foot_a=(1.2 * k, 0) if side else (0, 0),
                foot_b=(-1.6 * k, 0) if side else (0, 0), lag=0.6 if i in (1, 2) else 0.0)


def canvas(folk: Folk, d: float, mirror=False) -> pk.Sprite:
    s = d / 2.0
    fw, fh = folk.frame
    W = int(math.ceil(fw * s / 2)) * 2
    H = int(math.ceil(fh * s / 2)) * 2
    oy = H - max(2, int(round(folk.pad * s / 2)) * 2)
    return pk.Sprite(W, H, s, W / 2, oy, mirror)


def frame(folk: Folk, d: float, action: str, facing: str, i: int) -> Image.Image:
    kind = {'S': 'front', 'N': 'back', 'E': 'side', 'W': 'side'}[facing]
    sp = canvas(folk, d, mirror=(facing == 'W'))
    folk.draw[kind](sp, pose(folk, d, action, facing, i), d, facing)
    return sp.render()


def sheet(folk: Folk, d: float):
    """Every frame in one picture: a row per (facing, action) in FACINGS x TIMING order, one
    column per frame. Returns (image, meta) with the frame size and the foot anchor in texels."""
    rows = [(f, a) for f in FACINGS for a in TIMING]
    cols = max(TIMING[a]['frames'] for a in TIMING)
    probe = canvas(folk, d)
    fw, fh = probe.w, probe.h
    out = Image.new('RGBA', (cols * fw, len(rows) * fh), (0, 0, 0, 0))
    for r, (f, a) in enumerate(rows):
        for i in range(TIMING[a]['frames']):
            out.alpha_composite(frame(folk, d, a, f, i), (i * fw, r * fh))
    meta = dict(frame=[fw, fh], anchor=[fw // 2, int(probe.g.oy)], rows=[f'{f}_{a}' for f, a in rows],
                timing={a: TIMING[a] for a in TIMING}, density=d)
    return out, meta


# ------------------------------------------------------------------------------------------------
# shared part helpers
# ------------------------------------------------------------------------------------------------
def eye(sp, cx, cy, d, wide=1.0):
    """An eye: ink, about 2 x 3 texels at 2x, with a glint at its upper left (on the light side
    whichever way the face turns)."""
    g = sp.g
    s = sp.s
    w = max(1, int(round(2.0 * s * wide)))
    h = max(2, int(round(3.0 * s))) if d >= 1.75 else 2
    x0, y0 = g.px(cx, cy)
    x0 -= w // 2
    y0 -= h // 2
    m = np.zeros((g.h, g.w), bool)
    m[y0:y0 + h, x0:x0 + w] = True
    sp.detail(m, pk.ink())
    if w >= 2 and h >= 2:
        gl = np.zeros_like(m)
        gl[y0, x0] = True
        sp.detail(gl, pk.rgb('snow', 5), inside=False)
    return m


def limb(hip, foot, l1, l2, bend):
    """The knee for a two-segment limb (bend > 0 bends it forward, +x)."""
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    dist = max(1e-6, math.hypot(dx, dy))
    dist_c = min(dist, l1 + l2 - 1e-3)
    a = (l1 * l1 - l2 * l2 + dist_c * dist_c) / (2 * dist_c)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    mx, my = hx + a * dx / dist, hy + a * dy / dist
    nx, ny = -dy / dist, dx / dist
    if nx * bend < 0:
        nx, ny = -nx, -ny
    return (mx + h * nx, my + h * ny)
