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


def ndi_close(m, n):
    from scipy import ndimage
    return ndimage.binary_closing(m, iterations=n)


def ndi_dilate(m, n):
    from scipy import ndimage
    return ndimage.binary_dilation(m, iterations=n)


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
    fur, fur_dark, mane = 'timber_warm', 'timber_warm', 'timber_warm'
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
    spread = P['shell'] * 3            # the shell slips off whole, cracking as it goes

    if f == 'E':
        tilt = rear * 26             # the front rises when rearing
        by = -62 + bob + crouch * 6
        # legs: thigh to knee to hoof (far pair first, darker, behind the body)
        legs = [('leg_hf', -34, fur_dark, 0.5, feet[1], False), ('leg_ff', 28, fur_dark, 0.6, feet[3], True),
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
        body = (g.ellipse(-46, by + 6 + tilt * 0.3, 30, 30) | g.ellipse(-6, by + 4 + tilt * 0.1, 56, 32, rot=-tilt * 0.35)
                | g.ellipse(26, by - 6 - tilt * 0.7, 38, 40))
        sp.add('body', body, fur, base=3, z=1.1, k=0.8)
        sp.mark('body', g.Y > by + 18 + tilt * 0.1, -1)                  # the belly in its own shade
        sp.mark('body', (g.Y > by + 28) & (g.X > -40) & (g.X < 40), -1)
        sp.mark('body', g.ellipse(26, by - 26 - tilt * 0.7, 26, 10), 1)  # the lit hump
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
        shell_r = (56, 54)
        shell_a = (192, 348)
    elif f == 'S':
        by = -56 + bob + crouch * 4
        lift_front = rear * 22
        for name, x, fam, z, (dx, lift) in (('leg_hl', -40, fur_dark, 0.5, feet[1]), ('leg_hr', 40, fur_dark, 0.5, feet[3]),
                                            ('leg_fl', -26, fur, 2.6, feet[0]), ('leg_fr', 26, fur, 2.6, feet[2])):
            front = abs(x) < 30
            fy = -lift - (lift_front * 1.3 if front else 0)
            fx = x * (1 + 0.25 * lie)
            top = by + 20 - (lift_front if front else 0) + 6 * lie
            fy = fy * (1 - lie) - 3 * lie
            sp.add(name, g.capsule(x, top, fx, fy - 6, 10, 7), fam, base=2 if fam == fur else 1, z=z)
            sp.add(name + '_hoof', g.rrect(fx - 7, fy - 7, fx + 7, fy + 0.5, 2), 'soot', base=2, z=z + 0.05)
        sp.add('body', g.ellipse(0, by - 12, 50, 26) | g.ellipse(0, by + 2 - lift_front * 0.6, 54, 34), fur, base=3, z=1.1, k=0.8)
        sp.mark('body', g.Y > by + 22, -1)
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
        shell_r = (58, 46)
        shell_a = (190, 350)
    else:  # N
        by = -60 + bob + crouch * 4
        lift_front = rear * 22
        for name, x, fam, z, (dx, lift) in (('leg_fl', -26, fur_dark, 0.5, feet[0]), ('leg_fr', 26, fur_dark, 0.5, feet[2]),
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
        sp.add('body', g.ellipse(0, by, 54, 34) | g.ellipse(0, by + 12, 44, 26), fur, base=3, z=1.1, k=0.8)
        sp.mark('body', g.Y > by + 26, -1)
        sp.add('tail', g.capsule(0, by + 20, 3, by + 36, 2.6, 1.8), fur_dark, base=2, z=1.4)
        sp.add('tuft', g.ellipse(3, by + 38, 3.4, 4.2), mane, base=1, z=1.45)
        eye_c = None
        shell_c = (0, by - 4)
        shell_r = (56, 48)
        shell_a = (185, 355)

    # the bramble shell: canes arched over the back, crossing canes, thorns, leaves, berries and the
    # splinter of the shard; when freed it cracks into pieces that fall and spread
    if P['shell'] < 0.9:
        cx, cy = shell_c
        rx, ry = shell_r
        a0, a1 = shell_a
        canes = []
        NA = 8
        for k in range(NA):
            sc = 0.42 + 0.095 * k
            pts = []
            for j in range(15):
                a = math.radians(a0 - 8 + (a1 - a0 + 16) * j / 14)
                wob = math.sin(j * 1.1 + k * 1.7) * 3
                pts.append((cx + math.cos(a) * (rx * sc + wob), cy + math.sin(a) * (ry * sc + wob) - 6))
            canes.append(pts)
        for k in range(3):
            j0 = 2 + k * 4
            p0 = canes[0][j0]
            p1 = canes[NA - 1][min(14, j0 + 3)]
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
        dome_fill = True
        for k, pts in enumerate(canes):
            if pts is None:
                cane_masks.append(dome)
                continue
            r = 5.2 if k <= NA else (4.2 if k <= NA + 3 else 2.4)
            m = g.stroke(pts, r)
            cane_masks.append(m)
            shell_mask |= m
        # the tangle only shows in the gaps between the canes (no solid dome)
        weave = np.zeros_like(shell_mask)
        for m in cane_masks[1:NA + 4]:
            weave |= m
        cane_masks[0] = ndi_close(weave, 6 if P['shell'] == 0 else 11) & ~weave
        # freed: the shell cracks; the tangle splits in three and every cane falls its own way
        if P['shell'] > 0:
            def shift(m, dx, dy):
                return np.roll(np.roll(m, int(round(dy * g.s)), 0), int(round(dx * g.s * (-1 if mirror else 1))), 1)
            # the mass breaks in three clumps, each falling whole (canes, tangle and all)
            def split3(m):
                acc = np.zeros_like(m)
                for t3 in range(3):
                    x0 = cx - rx * 1.2 + t3 * rx * 0.8 + math.sin(t3 * 2.3) * 4
                    sel = m & (g.X >= x0 - (99 if t3 == 0 else 0)) & (g.X < x0 + rx * 0.8 + (99 if t3 == 2 else 0))
                    acc |= shift(sel, (t3 - 1) * spread, drop * (0.9 + 0.05 * t3))
                return acc
            cane_masks = [split3(m) for m in cane_masks[:NA + 4]]
        else:
            def split3(m):
                return m
        canes = [c for c in canes if c is not None]
        zs = -1.35 if f == 'S' else 0.0          # seen from the front, the shell is behind the head
        live = P['shell'] < 0.5
        # the tangle's depths between the canes, in deep shade
        sp.add('tangle', cane_masks[0], 'leaf_cool', base=2, z=2.9 + zs, k=0.9, lo=2, hi=2, outline=False)
        arcs, cross, hang = cane_masks[1:NA + 1], cane_masks[NA + 1:NA + 4], cane_masks[NA + 4:]
        # woody canes: grey-brown bark, round in section; knots a tone darker
        for k, m in enumerate(arcs):
            fam = ('leaf', 'leaf_cool')[k % 2]
            sp.add('cane%d' % k, m, fam, base=2, z=3.0 + k * 0.02 + zs, k=0.7, hi=3)
            if live:
                kn = np.zeros_like(m)
                for (x, y) in canes[k][2::3]:
                    kn |= g.ellipse(x, y, 2.2, 2.2)
                sp.mark('cane%d' % k, kn, -1)
        # crossing canes woven through them: over one arc, under the next
        for j, m in enumerate(cross):
            sp.add('cross%d' % j, m, 'leaf_warm', base=2, z=3.3 + j * 0.01 + zs, k=0.7, hi=3)
            for k, am in enumerate(arcs):
                if (k + j) % 2 == 0:
                    over = am & ndi_dilate(m, 3)
                    if over.any():
                        sp.add('weave%d_%d' % (j, k), over, ('leaf', 'leaf_cool')[k % 2], base=2,
                               z=3.4 + zs + k * 0.001, k=0.7, hi=3)
        for j, m in enumerate(hang):
            sp.add('vine%d' % j, m, 'earth_warm', base=2, z=2.95 + zs, k=0.7)
        if P['shell'] < 0.9:
            th = np.zeros((g.h, g.w), bool)
            for k, pts in enumerate(canes[:NA + 3]):
                th |= _thorn_tris(g, pts, (cx, cy + 24), 4.5 * P['spines'] + (k % 3) * 0.6, every=7.5 + (k % 3), w=1.8)
            th &= ~shell_mask
            if P['shell'] < 0.35:
                sp.add('thorns', th, 'sand', base=4, z=2.95 + zs, k=0.5, lo=3, hi=5)
            lv = np.zeros((g.h, g.w), bool)
            lv2 = np.zeros((g.h, g.w), bool)
            be = np.zeros((g.h, g.w), bool)
            for k, pts in enumerate(canes[2:NA]):
                for j in range(1 + k % 2, len(pts) - 1, 3):
                    x, y = pts[j]
                    rot = -40 + ((j * 37 + k * 23) % 80)
                    leaf = g.ellipse(x + 3, y - 3, 5.2, 2.4, rot=rot)
                    if (j + k) % 3 == 0:
                        lv2 |= leaf
                    else:
                        lv |= leaf
                    if (j + k) % 7 == 0:
                        be |= g.ellipse(x - 3, y + 1, 2.2, 2.2) | g.ellipse(x + 1, y + 2, 2.0, 2.0)
            lv, lv2, be = split3(lv), split3(lv2), split3(be)
            sp.add('leaves', lv, 'leaf', base=3, z=3.5 + zs, k=0.6)
            sp.add('leaves2', lv2 & ~lv, 'leaf_cool', base=3, z=3.45 + zs, k=0.6)
            sp.add('berries', be, 'berry', base=3, z=3.55 + zs, k=0.6)
        # the splinter of the shard, lodged at the top of the shell
        top = canes[NA - 2][7 if f != 'N' else 6]
        sdy = drop * 1.2
        spl = g.poly([(top[0] - 6, top[1] + 4 + sdy), (top[0] - 2, top[1] - 22 + sdy), (top[0] + 7, top[1] - 28 + sdy),
                      (top[0] + 6, top[1] + 4 + sdy)])
        sp.add('socket', g.ellipse(top[0] + 1, top[1] + 3 + sdy, 8, 3.4), 'soot', base=1, z=3.58 + zs, fixed=1)
        glow = P['glow']
        # the starfall crystal's own violet (the woodland shard's ramp, and the tells' pulse colour),
        # cut in facets: the face towards the light lit, a bright core along the ridge, the far
        # face a step down, so it reads as a crystal and not as a trickle of water
        far = g.poly([(top[0] + 2, top[1] + 4 + sdy), (top[0] + 2.5, top[1] - 24 + sdy), (top[0] + 7, top[1] - 28 + sdy),
                      (top[0] + 6, top[1] + 4 + sdy)]) & spl
        if glow > 0:
            lit = min(glow, 4)
            sp.add('splinter', spl, 'dusk', base=lit, z=3.6 + zs, fixed=lit, glow=True)
            sp.add('splinter_far', far, 'dusk', base=max(1, lit - 2), z=3.62 + zs, fixed=max(1, lit - 2), glow=True)
            # a step facet across the lit face's foot, a tone down, and a fracture running up it
            band = g.poly([(top[0] - 7, top[1] + 4 + sdy), (top[0] - 6, top[1] - 7 + sdy), (top[0] + 2, top[1] - 12 + sdy),
                           (top[0] + 2, top[1] + 4 + sdy)]) & spl & ~far
            sp.add('splinter_band', band, 'dusk', base=max(1, lit - 1), z=3.63 + zs, fixed=max(1, lit - 1), glow=True)
            core = g.poly([(top[0] - 2, top[1] - 4 + sdy), (top[0] + 1, top[1] - 22 + sdy), (top[0] + 2, top[1] - 4 + sdy)])
            sp.add('splinter_core', core, 'dusk', base=5, z=3.65 + zs, fixed=min(5, glow + 1), glow=True)
            frac = g.stroke([(top[0] - 4, top[1] + 1 + sdy), (top[0] - 3, top[1] - 8 + sdy), (top[0] - 1, top[1] - 14 + sdy)], 0.9)
            sp.add('splinter_fracture', frac & spl & ~far & ~core, 'dusk', base=max(1, lit - 2), z=3.66 + zs,
                   fixed=max(1, lit - 2), glow=True)
        else:
            sp.add('splinter', spl, 'dusk', base=2, z=3.6 + zs, k=0.6)
            sp.add('splinter_far', far, 'dusk', base=1, z=3.62 + zs, k=0.6)

    if P['shell'] >= 0.9:
        # the shell lies broken beside it: two cane scraps and the splinter, dark now
        sc1 = g.stroke([(-70, -6), (-56, -12), (-40, -8)], 3.6)
        sc2 = g.stroke([(50, -4), (64, -10), (78, -5)], 3.2)
        sp.add('scrap1', sc1, 'berry_cool', base=2, z=0.3, k=0.7)
        sp.add('scrap2', sc2, 'leaf_cool', base=2, z=0.3, k=0.7)
        sp.add('splinter', g.poly([(84, -2), (96, -10), (99, -7), (87, 1)]), 'dusk', base=2, z=0.35, k=0.6)

    if P['lie'] > 0.3:
        # where the shell lay: flattened, parted fur, a few torn leaves still caught in it, old scratches
        rng = np.random.default_rng(11)
        body = None
        for p in sp.parts:
            if p.name == 'body':
                body = p
        if body is not None:
            ys, xs = np.nonzero(body.mask)
            top = body.mask & (np.mgrid[0:body.mask.shape[0], 0:body.mask.shape[1]][0] < ys.min() + (ys.max() - ys.min()) * 0.45)
            ty, tx = np.nonzero(top)
            caught = np.zeros_like(body.mask)
            scr = np.zeros_like(body.mask)
            for k in range(22):
                i = int(rng.integers(0, len(ty)))
                X, Y = (tx[i] - g.ox) / g.s, (ty[i] - g.oy) / g.s
                if g.mirror:
                    X = -X
                if k % 2 == 0:
                    caught |= g.ellipse(X, Y, 3.2, 1.6, rot=float(rng.uniform(-40, 40)))
                else:
                    scr |= g.capsule(X - 4, Y - 1, X + 4, Y + 2, 0.7)
            sp.add('caught_leaves', caught & body.mask, 'leaf_cool', base=3, z=1.6, k=0.6)
            sp.mark('body', scr, -1)
            sp.mark('body', g.capsule(-30, ys.min() / 1.0 * 0 - 50, 20, -54, 1.0) & body.mask, 1)

    # the eyes: wild (glowing with the shard's violet), squinting, dazed or closed in calm sleep
    def eye(cx, cy):
        e = P['eyes']
        if e == 'wild':
            sp.detail(g.ellipse(cx, cy, 2.6, 2.2), _rgb('dusk', 5))
            sp.detail(g.ellipse(cx + 1, cy + 1, 1.2, 1.0), _rgb('dusk', 4))
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
    _volume(sp)
    _fur(sp, g)
    img = sp.render()
    if P['dust'] > 0:
        img = _dust(img, sp, P['dust'], f)
    return img


def _volume(sp):
    """Every coat part as a solid lit from the upper left: the kit's contour shading (a lit rim along
    the upper left, shade and core shadow along the lower right) taken wide, plus the back a tone up
    and the belly a tone down along curves that follow the part's own outline."""
    from scipy import ndimage as _ndi
    for p in sp.parts:
        if p.fam not in ('earth', 'earth_cool', 'timber_warm') or p.name.endswith('hoof') or p.mask.sum() < 60:
            continue
        p.flat = False
        p.k = 1.5
        p.lo, p.hi = 1, 5            # the coat's deepest shade stays a colour, never the outline's near-black
        d_top = _ndi.distance_transform_edt(p.mask)                    # depth inside the part
        ys, xs = np.nonzero(p.mask)
        y0, y1 = ys.min(), ys.max() + 1
        Y = np.mgrid[0:p.mask.shape[0], 0:p.mask.shape[1]][0]
        v = (Y - y0) / max(1, y1 - y0)
        rel = np.zeros(p.mask.shape, int)
        rel[(v < 0.32) & (d_top > 1)] += 1
        rel[v > 0.66] -= 1
        p.rel = rel if p.rel is None else p.rel + rel


def _fur(sp, g):
    """Bristles: short strokes a tone darker over the coat, combed back and down (clusters of two or
    more texels, never specks)."""
    rng = np.random.default_rng(3)
    for p in sp.parts:
        if p.fam not in ('earth', 'earth_cool', 'timber_warm') or p.name.endswith('hoof'):
            continue
        ys, xs = np.nonzero(p.mask)
        if len(ys) < 40:
            continue
        m = np.zeros(p.mask.shape, bool)
        lit = np.zeros(p.mask.shape, bool)
        for j, k in enumerate(rng.choice(len(ys), size=max(2, len(ys) // 17), replace=False)):
            x, y = (xs[k] - g.ox) / g.s, (ys[k] - g.oy) / g.s
            if g.mirror:
                x = -x
            stroke = g.capsule(x, y, x - 4, y + 3, 0.7)
            if j % 3 == 2:
                lit |= stroke            # a lighter tip among the dark strokes, so the shade side has fur too
            else:
                m |= stroke
        sp.mark(p.name, m, -1)
        sp.mark(p.name, lit & ~m, 1)


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
