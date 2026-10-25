"""The Thornback, the Undercroft's boss (docs/vision/vertical-slice.md beat 6): a great boar turned wild
by a splinter of the starfall shard lodged in the bramble shell that grew over its back. It is freed,
never killed: when its strength runs out the shell cracks and falls away, the splinter goes dark and
the boar lies down calm.

Drawn with the raster kit (form shading lit from the upper left, contact shade, the house outline,
no lone pixels) in four facings: S, N and E are drawn, W is the east geometry on a mirrored grid so
the light stays upper left (SB-03). About 1.8 times a person's height (the cast is 74 texels at
density 3; the Thornback stands about 130 with its shell up).

    python3 -m scripts.art.native.thornback --out game/bosses/thornback/art --density 3 [--preview DIR]

writes sheets/<clip>_<F>.png (one strip per clip and facing, FW x FH cells, the foot at PIVOT),
thorn.png (the volley's thorn in eight directions) and manifest.json (clips, per-frame durations,
loop flags, the release frame of each attack, the pivot and the frame size). The game builds its
SpriteFrames from the manifest (game/bosses/thornback_sprite.gd).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.art.native import ctx  # noqa: E402

FACINGS = ('S', 'N', 'E', 'W')
FW, FH = 288, 208          # the cell at density 3 (texels)
PIVOT = (144, 196)

# clip: (frames, seconds per frame, loop, release frame or None). Wind-up clips are stretched by the
# game to the wind-up's length; their own timing only orders the drawings.
CLIPS = {
    'idle': (4, 0.22, True, None),
    'move': (6, 0.10, True, None),
    'charge_windup': (4, 0.20, False, None),
    'charge': (4, 0.07, True, None),
    'volley_windup': (4, 0.22, False, None),
    'volley': (3, 0.10, False, 0),
    'slam_windup': (4, 0.24, False, None),
    'slam': (3, 0.10, False, 1),
    'recover': (2, 0.25, True, None),
    'hurt': (2, 0.10, False, None),
    'stagger': (4, 0.20, True, None),
    'freed': (8, 0.16, False, None),
    'calm': (4, 0.40, True, None),
}


def pose(clip: str, i: int) -> dict:
    """The pose parameters of drawing i of a clip."""
    P = dict(bob=0.0, head=0.0, gait=None, spines=1.0, glow=4, rear=0.0, crouch=0.0, eyes='wild', shell=0.0,
             lie=0.0, paw=0.0, flinch=0.0, stars=False, dust=0.0, mouth=0.0)
    if clip == 'idle':
        P['bob'] = (0, 1, 2, 1)[i]
        P['spines'] = 1.0 + (0, 0.05, 0.1, 0.05)[i]
    elif clip == 'move':
        P['gait'] = i / 6 * 2 * math.pi
        P['bob'] = (0, 2, 1, 0, 2, 1)[i]
    elif clip == 'charge_windup':
        P['crouch'] = (0.3, 0.6, 0.85, 1.0)[i]
        P['head'] = (3, 6, 8, 9)[i]
        P['paw'] = (0, 1, 0, 1)[i]
        P['spines'] = 1.15
        P['glow'] = 5
        P['mouth'] = 1
    elif clip == 'charge':
        P['gait'] = i / 4 * 2 * math.pi
        P['head'] = 9
        P['bob'] = (0, 3, 0, 3)[i]
        P['spines'] = 1.1
        P['dust'] = 1
    elif clip == 'volley_windup':
        P['spines'] = (1.2, 1.45, 1.7, 1.9)[i]
        P['crouch'] = (0.1, 0.25, 0.4, 0.5)[i]
        P['bob'] = (0, 1, 2, 2)[i]
        P['glow'] = 5
    elif clip == 'volley':
        P['spines'] = (0.8, 0.9, 1.0)[i]
        P['bob'] = (-2, 0, 0)[i]
        P['glow'] = (5, 4, 4)[i]
    elif clip == 'slam_windup':
        P['rear'] = (0.25, 0.55, 0.85, 1.0)[i]
        P['spines'] = 1.2
        P['glow'] = 5
        P['mouth'] = 1
    elif clip == 'slam':
        P['rear'] = (0.2, -0.15, 0.0)[i]
        P['dust'] = (0.5, 1.0, 0.6)[i]
        P['bob'] = (0, 3, 1)[i]
    elif clip == 'recover':
        P['bob'] = (1, 2)[i]
        P['head'] = (2, 3)[i]
        P['spines'] = 0.95
    elif clip == 'hurt':
        P['flinch'] = (1.0, 0.5)[i]
        P['eyes'] = 'squint'
    elif clip == 'stagger':
        P['head'] = 10
        P['crouch'] = 0.6
        P['bob'] = (0, 1, 2, 1)[i]
        P['eyes'] = 'dazed'
        P['stars'] = i
        P['spines'] = 0.7
        P['glow'] = 3
    elif clip == 'freed':
        t = i / 7
        P['shell'] = min(1.0, t * 1.4)
        P['lie'] = max(0.0, (t - 0.3) / 0.7)
        P['eyes'] = 'wild' if t < 0.15 else ('squint' if t < 0.55 else 'closed')
        P['glow'] = 5 if t < 0.15 else (2 if t < 0.5 else 0)
        P['spines'] = max(0.4, 1 - t)
    elif clip == 'calm':
        P['shell'] = 1.0
        P['lie'] = 1.0
        P['eyes'] = 'closed'
        P['bob'] = (0, 1, 1, 0)[i]
        P['glow'] = 0
    return P


# ------------------------------------------------------------------------------------------------
# drawing
# ------------------------------------------------------------------------------------------------
def _sprite(d, mirror=False):
    from scripts.art.native import raster as R
    s = d / 3.0
    return R.Sprite(int(round(FW * s)), int(round(FH * s)), s, PIVOT[0] * s, PIVOT[1] * s, mirror=mirror)


def _thorn_tris(g, pts, out_c, length, every=9.0, w=2.6, side=1):
    """Thorns along a cane: small triangles pointing away from out_c."""
    m = np.zeros((g.h, g.w), bool)
    acc = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = math.hypot(bx - ax, by - ay)
        n = 0
        while acc + n * every < seg:
            t = (acc + n * every) / max(seg, 1e-6)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            nx, ny = x - out_c[0], y - out_c[1]
            L = math.hypot(nx, ny) or 1
            nx, ny = nx / L, ny / L
            tx, ty = -ny, nx
            m |= g.poly([(x + tx * w, y + ty * w), (x - tx * w, y - ty * w),
                         (x + nx * length + tx * 0.6, y + ny * length + ty * 0.6)])
            n += 1
        acc = (acc + n * every) - seg
    return m


def draw(facing: str, P: dict, d: float = 3.0) -> Image.Image:
    mirror = facing == 'W'
    f = 'E' if facing == 'W' else facing
    sp = _sprite(d, mirror)
    g = sp.g
    lie = P['lie']
    bob = P['bob'] + lie * 22
    crouch = P['crouch']
    rear = P['rear']
    fl = P['flinch'] * 5
    head_dy = P['head'] + lie * 8
    fur, fur_dark, mane = 'earth', 'earth_cool', 'earth_cool'
    gait = P['gait']

    def leg_feet(n):
        out = []
        for k in range(n):
            if gait is None:
                lift = P['paw'] * 6 if k == 0 else 0
                out.append((0.0, -lift))
            else:
                ph = gait + (0, math.pi, math.pi * 0.5, math.pi * 1.5)[k]
                out.append((math.cos(ph) * 9, -max(0.0, math.sin(ph)) * 7))
        return out

    feet = leg_feet(4)
    shell_on = P['shell'] < 1.0
    drop = P['shell'] * 34          # the shell's pieces fall and spread as it cracks
    spread = P['shell'] * 18

    if f == 'E':
        tilt = rear * 26             # the front rises when rearing
        by = -62 + bob + crouch * 6
        # legs: thigh to knee to hoof (far pair first, darker, behind the body)
        legs = [('leg_hf', -34, 'earth_cool', 0.5, feet[1], False), ('leg_ff', 28, 'earth_cool', 0.6, feet[3], True),
                ('leg_hn', -46, fur, 2.5, feet[0 if gait is not None else 2], False),
                ('leg_fn', 40, fur, 2.6, feet[2 if gait is not None else 0], True)]
        for name, x, fam, z, (dx, lift), front in legs:
            top_y = by + 12 - (tilt if front else -tilt * 0.2)
            fx = x + dx + (crouch * 6 if front else -crouch * 4)
            fy = -lift - (tilt * 1.2 if front and rear > 0.05 else 0)
            if lie > 0:
                fx = x + (18 if front else -12) * lie + dx * (1 - lie)
                fy = fy * (1 - lie) - 4 * lie
                top_y = top_y + 8 * lie
            k = 1.0 if name.endswith('n') else 0.85
            kx = (x + fx) / 2 + (3 if front else -7) * (1 - lie) + (8 if front else -10) * lie
            ky = (top_y + fy) / 2 + 2
            base = 2 if fam == fur else 1
            sp.add(name, g.capsule(x, top_y, kx, ky, 15 * k, 8 * k), fam, base=base, z=z)
            sp.add(name + '_shin', g.capsule(kx, ky, fx, fy - 6, 7 * k, 5 * k), fam, base=base, z=z + 0.02)
            sp.add(name + '_hoof', g.rrect(fx - 6 * k, fy - 8, fx + 6.5 * k, fy + 0.5, 2), 'soot', base=2, z=z + 0.05)
        # the body: rump, barrel, the high shoulder hump of a boar
        sp.add('rump', g.ellipse(-46, by + 6 + tilt * 0.3, 30, 30), fur, base=3, z=1.0)
        sp.add('barrel', g.ellipse(-6, by + 4 + tilt * 0.1, 56, 32, rot=-tilt * 0.35), fur, base=3, z=1.1)
        sp.add('shoulder', g.ellipse(26, by - 6 - tilt * 0.7, 38, 40), fur, base=3, z=1.2)
        sp.add('belly', g.ellipse(-4, by + 26 + tilt * 0.1, 44, 9) & ~g.ellipse(-4, by + 40, 60, 12), fur_dark, base=2, z=1.15)
        # head: a long wedge, low and forward, the snout disc and the tusks
        hx, hy = 64 - fl - crouch * 2, by + 10 - tilt * 1.3 + head_dy
        sp.add('head', g.ellipse(hx, hy, 32, 25, rot=22 + head_dy), fur, base=3, z=2.0)
        sp.add('cheek', g.ellipse(hx - 4, hy + 10, 18, 12), fur_dark, base=3, z=2.01)
        sx, sy = hx + 30, hy + 18 + head_dy * 0.3
        sp.add('snout', g.capsule(hx + 10, hy + 6, sx, sy, 14, 10), fur, base=3, z=2.1)
        sp.add('nose', g.ellipse(sx + 6, sy + 1, 5, 10), 'clay', base=3, z=2.2)
        sp.add('nostril', g.ellipse(sx + 7, sy + 2, 1.6, 2.8), 'clay_cool', base=1, z=2.25, fixed=1)
        sp.add('jaw', g.ellipse(hx + 16, hy + 20, 16, 7) & ~g.ellipse(hx + 16, hy + 12, 18, 8), fur_dark, base=2, z=2.05)
        if P['mouth']:
            sp.add('mouth', g.capsule(hx + 12, hy + 18, sx + 2, sy + 9, 1.6, 1.2), 'berry_cool', base=1, z=2.3, fixed=1)
        sp.add('ear', g.ellipse(hx - 16, hy - 24, 8, 14, rot=-25 - fl * 3), fur_dark, base=2, z=1.9)
        sp.add('ear_in', g.ellipse(hx - 15, hy - 24, 3.4, 8, rot=-25 - fl * 3), 'clay_cool', base=2, z=1.95, fixed=2)
        sp.add('tusk', g.capsule(sx - 3, sy + 6, sx + 9, sy - 12, 3.8, 1.6) | g.capsule(sx + 9, sy - 12, sx + 4, sy - 19, 1.6, 0.8),
               'plaster', base=4, z=2.4, k=0.6)
        # the mane: a crest of bristles along the spine, standing up over the hump
        mpts = [(-66, by - 18 + tilt * 0.3), (-46, by - 26), (-24, by - 30), (0, by - 38 - tilt * 0.4),
                (16, by - 44 - tilt * 0.7), (32, by - 40 - tilt), (hx - 20, hy - 22)]
        if lie < 0.5:
            sp.add('mane', g.stroke(mpts, 4.5) & ~g.ellipse(-6, by + 14, 70, 40), mane, base=2, z=1.25, k=0.6)
        eye_c = (hx + 8, hy - 6)
        sp.add('tail', g.capsule(-74, by - 4, -82, by + 12, 2.4, 1.6), fur_dark, base=2, z=0.9)
        shell_c = (-10, by - 4 - tilt * 0.4)
        shell_r = (52, 40)
        shell_a = (192, 348)
    elif f == 'S':
        by = -56 + bob + crouch * 4
        lift_front = rear * 22
        for name, x, fam, z, (dx, lift) in (('leg_hl', -40, 'earth_cool', 0.5, feet[1]), ('leg_hr', 40, 'earth_cool', 0.5, feet[3]),
                                            ('leg_fl', -26, fur, 2.6, feet[0]), ('leg_fr', 26, fur, 2.6, feet[2])):
            front = abs(x) < 30
            fy = -lift - (lift_front * 1.3 if front else 0)
            fx = x * (1 + 0.25 * lie)
            top = by + 20 - (lift_front if front else 0) + 6 * lie
            fy = fy * (1 - lie) - 3 * lie
            sp.add(name, g.capsule(x, top, fx, fy - 6, 10, 7), fam, base=2 if fam == fur else 1, z=z)
            sp.add(name + '_hoof', g.rrect(fx - 7, fy - 7, fx + 7, fy + 0.5, 2), 'soot', base=2, z=z + 0.05)
        sp.add('rump', g.ellipse(0, by - 12, 50, 26), fur_dark, base=2, z=0.8)
        sp.add('barrel', g.ellipse(0, by + 2 - lift_front * 0.6, 54, 34), fur, base=3, z=1.1)
        hx, hy = 0, by + 10 - lift_front * 1.2 + head_dy - fl * 0.5
        sp.add('head', g.ellipse(hx, hy, 34, 28), fur, base=3, z=2.0)
        sp.add('brow', g.ellipse(hx, hy - 10, 26, 10), fur_dark, base=3, z=2.02)
        sp.add('snout', g.ellipse(hx, hy + 16, 16, 13), fur, base=3, z=2.1)
        sp.add('nose', g.ellipse(hx, hy + 22, 11, 7), 'clay', base=3, z=2.2)
        sp.add('nostril', g.ellipse(hx - 4, hy + 23, 1.8, 2.2) | g.ellipse(hx + 4, hy + 23, 1.8, 2.2), 'clay_cool', base=1, z=2.25,
               fixed=1)
        if P['mouth']:
            sp.add('mouth', g.capsule(hx - 9, hy + 31, hx + 9, hy + 31, 1.4), 'berry_cool', base=1, z=2.3, fixed=1)
        for sgn in (-1, 1):
            sp.add('ear%d' % sgn, g.ellipse(hx + sgn * 26, hy - 18, 8, 12, rot=sgn * (35 + fl * 3)), fur_dark, base=2, z=1.9)
            sp.add('tusk%d' % sgn, g.capsule(hx + sgn * 13, hy + 26, hx + sgn * 21, hy + 10, 3.4, 1.4) |
                   g.capsule(hx + sgn * 21, hy + 10, hx + sgn * 19, hy + 4, 1.4, 0.8), 'plaster', base=4, z=2.4, k=0.6)
        sp.add('mane', g.stroke([(-6, by - 30), (0, by - 34), (6, by - 30)], 6), mane, base=2, z=1.3)
        eye_c = None
        shell_c = (0, by - 6)
        shell_r = (52, 30)
        shell_a = (190, 350)
    else:  # N
        by = -60 + bob + crouch * 4
        lift_front = rear * 22
        for name, x, fam, z, (dx, lift) in (('leg_fl', -26, 'earth_cool', 0.5, feet[0]), ('leg_fr', 26, 'earth_cool', 0.5, feet[2]),
                                            ('leg_hl', -36, fur, 2.6, feet[1]), ('leg_hr', 36, fur, 2.6, feet[3])):
            back = abs(x) < 30
            fy = -lift - (lift_front * 1.3 if back else 0)
            fx = x * (1 + 0.25 * lie)
            fy = fy * (1 - lie) - 3 * lie
            top = by + 18 - (lift_front if back else 0) + 6 * lie
            sp.add(name, g.capsule(x, top, fx, fy - 6, 10, 7), fam, base=2 if fam == fur else 1, z=z)
            sp.add(name + '_hoof', g.rrect(fx - 7, fy - 7, fx + 7, fy + 0.5, 2), 'soot', base=2, z=z + 0.05)
        hx, hy = 0, by - 18 - lift_front * 1.2 + head_dy * 0.5
        sp.add('head', g.ellipse(hx, hy, 26, 18), fur_dark, base=2, z=0.7)
        for sgn in (-1, 1):
            sp.add('ear%d' % sgn, g.ellipse(hx + sgn * 22, hy - 10, 7, 11, rot=sgn * 30), fur_dark, base=2, z=0.75)
        sp.add('barrel', g.ellipse(0, by, 54, 34), fur, base=3, z=1.1)
        sp.add('rump', g.ellipse(0, by + 12, 44, 26), fur, base=3, z=1.3)
        sp.add('tail', g.capsule(0, by + 20, 3, by + 36, 2.6, 1.8), fur_dark, base=2, z=1.4)
        sp.add('tuft', g.ellipse(3, by + 38, 3.4, 4.2), mane, base=1, z=1.45)
        eye_c = None
        shell_c = (0, by - 4)
        shell_r = (50, 32)
        shell_a = (185, 355)

    # the bramble shell: canes arched over the back, crossing canes, thorns, leaves, berries and the
    # splinter of the shard; when freed it cracks into pieces that fall and spread
    if P['shell'] < 0.9:
        cx, cy = shell_c
        rx, ry = shell_r
        a0, a1 = shell_a
        canes = []
        for k in range(5):
            sc = 0.62 + 0.11 * k
            pts = []
            for j in range(15):
                a = math.radians(a0 + (a1 - a0) * j / 14)
                wob = math.sin(j * 1.1 + k * 1.7) * 3
                pts.append((cx + math.cos(a) * (rx * sc + wob), cy + math.sin(a) * (ry * sc + wob) - 6))
            canes.append(pts)
        for k in range(3):
            j0 = 2 + k * 4
            p0 = canes[0][j0]
            p1 = canes[4][min(14, j0 + 3)]
            canes.append([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 8), p1])
        shell_mask = np.zeros((g.h, g.w), bool)
        cane_masks = []
        # the tangle under the canes: a dome over the back with a ragged fringe of cane ends
        dome = g.ellipse(cx, cy - 8, rx * 1.1, ry * 0.78)
        for j in range(9):
            a = math.radians(a0 - 8 + (a1 - a0 + 16) * j / 8)
            ex, ey = cx + math.cos(a) * rx * 1.08, cy - 8 + math.sin(a) * ry * 0.7
            dome |= g.ellipse(ex, ey + 7 + (j % 3) * 3, 6 + (j % 2) * 2, 7)
        # vines hanging over the flanks from the rim, ending in hooked tips
        hang = []
        for j in range(7):
            a = math.radians(a0 + 6 + (a1 - a0 - 12) * j / 6)
            ex, ey = cx + math.cos(a) * rx * 1.05, cy - 8 + math.sin(a) * ry * 0.55 + 10
            L = 10 + (j * 7) % 9
            hang.append([(ex, ey - 4), (ex + 2, ey + L * 0.6), (ex - 1 + (j % 2) * 4, ey + L)])
        for pts in hang:
            canes.append(pts)
        canes.insert(0, None)
        for k, pts in enumerate(canes):
            if pts is None:
                cane_masks.append(dome)
                continue
            r = 5.6 if k <= 5 else (4.0 if k <= 8 else 2.4)
            m = g.stroke(pts, r)
            cane_masks.append(m)
            shell_mask |= m
        # freed: the shell cracks; the tangle splits in three and every cane falls its own way
        if P['shell'] > 0:
            def shift(m, dx, dy):
                return np.roll(np.roll(m, int(round(dy * g.s)), 0), int(round(dx * g.s * (-1 if mirror else 1))), 1)
            parts = []
            for t3 in range(3):
                x0 = cx - rx * 1.2 + t3 * rx * 0.8 + math.sin(t3 * 2.3) * 4
                sel = cane_masks[0] & (g.X >= x0) & (g.X < x0 + rx * 0.8 + (99 if t3 == 2 else 0))
                parts.append(shift(sel, (t3 - 1) * spread, drop * (0.8 + 0.2 * t3)))
            moved = [parts[0] | parts[1] | parts[2]]
            for k, m in enumerate(cane_masks[1:]):
                moved.append(shift(m, ((k % 3) - 1) * spread * 1.3, drop * (0.6 + 0.12 * k)))
            cane_masks = moved
        canes = [c for c in canes if c is not None]
        zs = -1.35 if f == 'S' else 0.0          # seen from the front, the shell is behind the head
        sp.add('tangle', cane_masks[0], 'leaf_cool', base=1, z=2.9 + zs, k=0.9, lo=0, hi=2)
        for k, m in enumerate(cane_masks[1:]):
            fam = ('leaf_cool', 'berry_cool')[k % 2]
            zz = 3.0 + k * 0.02 + (0.3 if 5 <= k < 8 else 0) - (0.2 if k >= 8 else 0)
            sp.add('cane%d' % k, m, fam, base=3 if P['shell'] < 0.5 else 2, z=zz + zs, line=True, k=0.7)
        if P['shell'] < 0.35:
            th = np.zeros((g.h, g.w), bool)
            for k, pts in enumerate(canes[:5]):
                th |= _thorn_tris(g, pts, (cx, cy + 24), 8 * P['spines'] + k * 0.6, every=12 - k, w=2.6)
            th &= ~shell_mask
            sp.add('thorns', th, 'sand', base=4, z=2.95 + zs, k=0.5, lo=3, hi=5)
            lv = np.zeros((g.h, g.w), bool)
            be = np.zeros((g.h, g.w), bool)
            for k, (pts, j) in enumerate(((canes[1], 4), (canes[3], 9), (canes[2], 12), (canes[4], 6), (canes[0], 10))):
                x, y = pts[j]
                if k % 2 == 0:
                    lv |= g.ellipse(x + 3, y - 3, 5, 2.6, rot=-30 + k * 25)
                else:
                    be |= g.ellipse(x, y - 1, 2.6, 2.6) | g.ellipse(x + 4, y + 1, 2.4, 2.4)
            sp.add('leaves', lv, 'leaf', base=3, z=3.4 + zs, k=0.6)
            sp.add('berries', be, 'berry', base=3, z=3.45 + zs, k=0.6)
        # the splinter of the shard, lodged at the top of the shell
        top = canes[2][7 if f != 'N' else 6]
        sdy = drop * 1.2
        spl = g.poly([(top[0] - 6, top[1] + 4 + sdy), (top[0] - 2, top[1] - 22 + sdy), (top[0] + 7, top[1] - 28 + sdy),
                      (top[0] + 6, top[1] + 4 + sdy)])
        glow = P['glow']
        if glow > 0:
            sp.add('splinter', spl, 'sky', base=glow, z=3.6 + zs, fixed=glow, glow=True)
            core = g.poly([(top[0] - 2, top[1] - 1 + sdy), (top[0] + 1, top[1] - 20 + sdy), (top[0] + 4, top[1] - 1 + sdy)])
            sp.add('splinter_core', core, 'sky', base=5, z=3.65 + zs, fixed=min(5, glow + 1), glow=True)
        else:
            sp.add('splinter', spl, 'sky_cool', base=2, z=3.6 + zs, k=0.6)

    if P['shell'] >= 0.9:
        # the shell lies broken beside it: two cane scraps and the splinter, dark now
        sc1 = g.stroke([(-70, -6), (-56, -12), (-40, -8)], 3.6)
        sc2 = g.stroke([(50, -4), (64, -10), (78, -5)], 3.2)
        sp.add('scrap1', sc1, 'berry_cool', base=2, z=0.3, k=0.7)
        sp.add('scrap2', sc2, 'leaf_cool', base=2, z=0.3, k=0.7)
        sp.add('splinter', g.poly([(84, -2), (96, -10), (99, -7), (87, 1)]), 'sky_cool', base=2, z=0.35, k=0.6)

    # the eyes: wild (glowing shard-blue), squinting, dazed or closed in calm sleep
    def eye(cx, cy):
        e = P['eyes']
        if e == 'wild':
            sp.detail(g.ellipse(cx, cy, 2.6, 2.2), _rgb('sky', 5))
            sp.detail(g.ellipse(cx + 1, cy + 1, 1.2, 1.0), _rgb('sky', 3))
        elif e == 'squint':
            sp.detail(g.capsule(cx - 3, cy, cx + 3, cy - 1, 1.0), _rgb('earth_cool', 0))
        elif e == 'dazed':
            sp.detail(g.ellipse(cx, cy, 2.6, 2.6) & ~g.ellipse(cx, cy, 1.2, 1.2), _rgb('sand', 4))
        else:
            sp.detail(g.capsule(cx - 3, cy + 1, cx + 3, cy + 1, 0.9), _rgb('earth_cool', 0))

    if f == 'E':
        eye(*eye_c)
    elif f == 'S':
        eye(hx - 12, hy - 4)
        eye(hx + 12, hy - 4)
    if P['stars'] is not False:
        for k in range(3):
            a = P['stars'] * 0.8 + k * 2.1
            sx, sy = (hx if f != 'N' else 0) + math.cos(a) * 22, (hy if f != 'N' else by - 40) - 34 + math.sin(a) * 6
            sp.detail(g.ellipse(sx, sy, 2.4, 2.4) | g.rect(sx - 4, sy - 0.6, sx + 4, sy + 0.6) | g.rect(sx - 0.6, sy - 4, sx + 0.6, sy + 4),
                      _rgb('lamp', 5), inside=False)
    _fur(sp, g)
    img = sp.render()
    if P['dust'] > 0:
        img = _dust(img, sp, P['dust'], f)
    return img


def _fur(sp, g):
    """Bristles: short strokes a tone darker over the coat, combed back and down (clusters of two or
    more texels, never specks)."""
    rng = np.random.default_rng(3)
    for p in sp.parts:
        if p.fam not in ('earth', 'earth_cool') or p.name.endswith('hoof'):
            continue
        ys, xs = np.nonzero(p.mask)
        if len(ys) < 40:
            continue
        m = np.zeros(p.mask.shape, bool)
        for k in rng.choice(len(ys), size=max(2, len(ys) // 70), replace=False):
            x, y = (xs[k] - g.ox) / g.s, (ys[k] - g.oy) / g.s
            if g.mirror:
                x = -x
            m |= g.capsule(x, y, x - 4, y + 3, 0.7)
        sp.mark(p.name, m, -1)


def _rgb(fam, t):
    from scripts.art.native.palette import rgb
    return rgb(fam, t)


def _dust(img, sp, k, f):
    """Puffs of dust at the feet (charge and slam): pale clods lit on their upper left, outlined."""
    from scripts.art.native import raster as R
    s2 = R.Sprite(sp.w, sp.h, sp.s, sp.g.ox, sp.g.oy)
    g = s2.g
    for j, (x, r) in enumerate(((-58, 9), (-34, 7), (40, 8), (64, 10))):
        if f != 'E' and abs(x) > 50:
            x = x * 0.8
        s2.add('d%d' % j, g.ellipse(x * (1 + 0.2 * k), -6 - 3 * k, r * k, r * 0.6 * k), 'path', base=4, z=j, k=0.8)
    over = s2.render()
    out = over.copy()
    out.alpha_composite(img)
    return out


def thorn_sheet(d: float) -> Image.Image:
    """The volley's thorn: a hooked spine with a lit edge, in eight directions (E, SE, S, SW, W, NW, N,
    NE), 24 x 24 texels at density 3, drawn natively per direction."""
    from scripts.art.native import raster as R
    n = int(round(24 * d / 3))
    sheet = Image.new('RGBA', (n * 8, n))
    for k in range(8):
        a = k * math.pi / 4
        sp = R.Sprite(n, n, d / 3, n / 2, n / 2)
        g = sp.g
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        body = g.poly([(-8 * ux + 3 * vx, -8 * uy + 3 * vy), (9 * ux, 9 * uy), (-8 * ux - 3 * vx, -8 * uy - 3 * vy)])
        sp.add('thorn', body, 'sand', base=3, k=0.6)
        sp.add('base', g.ellipse(-7 * ux, -7 * uy, 3.4, 3.4), 'berry_cool', base=2, z=1)
        sheet.paste(sp.render(), (k * n, 0))
    return sheet


INPUTS = ('thornback.py', 'raster.py', 'palette.py', 'ctx.py')


def input_hash(density: float) -> str:
    h = hashlib.sha256(('density %g\n' % density).encode())
    for f in [os.path.join(HERE, x) for x in INPUTS] + [os.path.join(ROOT, 'art', 'house-palette.json')]:
        h.update(os.path.relpath(f, ROOT).encode() + b'\0')
        h.update(open(f, 'rb').read())
    return h.hexdigest()


def build(out: str, d: float, preview: str | None = None) -> dict:
    sheets = os.path.join(out, 'sheets')
    os.makedirs(sheets, exist_ok=True)
    fw, fh = int(round(FW * d / 3)), int(round(FH * d / 3))
    man = dict(id='thornback', name='The Thornback', directions=list(FACINGS), frame_size=[fw, fh],
               foot_pivot=[int(round(PIVOT[0] * d / 3)), int(round(PIVOT[1] * d / 3))], density=d,
               inputs=input_hash(d), clips={})
    rows = []
    for clip, (n, dur, loop, rel) in CLIPS.items():
        man['clips'][clip] = dict(frames=n, durations=[dur] * n, loop=loop, release_frame=rel)
        for fc in FACINGS:
            strip = Image.new('RGBA', (fw * n, fh))
            for i in range(n):
                strip.paste(draw(fc, pose(clip, i), d), (i * fw, 0))
            strip.save(os.path.join(sheets, '%s_%s.png' % (clip, fc)), optimize=True)
            if preview and fc in ('S', 'E'):
                rows.append(strip)
    thorn_sheet(d).save(os.path.join(out, 'thorn.png'), optimize=True)
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    if preview:
        os.makedirs(preview, exist_ok=True)
        W = max(r.width for r in rows)
        img = Image.new('RGBA', (W, fh * len(rows)), (40, 36, 44, 255))  # noqa: preview background only
        for k, r in enumerate(rows):
            img.alpha_composite(r, (0, k * fh))
        img.save(os.path.join(preview, 'thornback_sheet.png'))
    return dict(clips=len(CLIPS), facings=len(FACINGS), frame=[fw, fh])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--density', type=float, default=3.0)
    ap.add_argument('--preview', default=None)
    ap.add_argument('--only', default=None, help='clip:facing:frame, writes one drawing to --preview')
    a = ap.parse_args(argv)
    ctx.configure(a.density)
    if a.only:
        c, fc, i = a.only.split(':')
        os.makedirs(a.preview, exist_ok=True)
        img = draw(fc, pose(c, int(i)), a.density)
        img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(os.path.join(a.preview, 'tb_%s_%s_%s.png' % (c, fc, i)))
        return 0
    print(json.dumps(build(a.out, a.density, a.preview)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
