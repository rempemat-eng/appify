"""Moving water and lava for the world's zones (Matt, 19 Oct 22:40: "water should have
flowing animations"; Eastward's water moves with drifting highlights and lapping edges).

The ground stays one still picture. Each zone with water or lava gets one extra picture:
FRAMES overlay frames stacked top to bottom, covering only the box round its water, with
nothing but the pixels that change: light streaks that drift downstream along a river or
a race, slow glints that come and go on open water (the sea, a lake, a pond), a little foam
that laps along the banks, and on lava slow bright veins that creep with the flow.

How the flow is found: from the water's own shape. The mask is blurred and its structure
tensor taken; along a channel the water runs across the strongest gradient, and where the
tensor has no dominant direction (wide open water) there is no current, only glints. The
current runs downhill, which in this world is down the screen (toward the sea), and east
where a channel runs level. Everything is deterministic (numpy, no randomness), so the
pictures reproduce byte for byte.

The renderer (components/atlas-walk.tsx) shows one frame at a time, FRAME_MS apart, and
holds frame 0 with reduced motion or when the screen is inactive.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

FRAMES = 8
FRAME_MS = 150          # 8 frames: a 1.2 s loop (divides the renderer's 36 s clock)
PERIOD = 32             # px between streak repeats along the flow; FRAMES must divide it
SHIFT = PERIOD // FRAMES  # px a streak drifts per frame (4 px / 150 ms, ~27 px/s)
LAVA_SHIFT = 1          # lava creeps (a loop of 8 px)
LAVA_PERIOD = FRAMES * LAVA_SHIFT * 2

WATER_LIGHT = np.array([214, 232, 242], dtype=np.float32)
LAVA_LIGHT = np.array([255, 226, 128], dtype=np.float32)


def _blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """A separable Gaussian blur with edge padding (numpy only)."""
    r = max(1, int(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2).astype(np.float64)
    k /= k.sum()
    p = np.pad(a.astype(np.float64), ((0, 0), (r, r)), mode='edge')
    a = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
    p = np.pad(a, ((r, r), (0, 0)), mode='edge')
    return sum(k[i] * p[i:i + a.shape[0], :] for i in range(2 * r + 1))


def _depth(mask: np.ndarray, cap: int = 8) -> np.ndarray:
    """How many px each masked pixel is from the bank (0 on the edge), capped."""
    d = np.zeros(mask.shape, dtype=np.int32)
    cur = mask.copy()
    for i in range(cap):
        inner = cur.copy()
        inner[1:, :] &= cur[:-1, :]
        inner[:-1, :] &= cur[1:, :]
        inner[:, 1:] &= cur[:, :-1]
        inner[:, :-1] &= cur[:, 1:]
        d[inner] = i + 1
        cur = inner
        if not cur.any():
            break
    return d


def _flow(mask: np.ndarray):
    """Per pixel: the unit vector the current runs along, and how channel-like the water is
    there (0 open water .. 1 a clear channel)."""
    m = _blur(mask.astype(np.float64), 2.0)
    gy, gx = np.gradient(m)
    jxx, jxy, jyy = _blur(gx * gx, 7.0), _blur(gx * gy, 7.0), _blur(gy * gy, 7.0)
    tr = jxx + jyy
    det = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2)
    coherence = np.where(tr > 1e-9, det / np.maximum(tr, 1e-9), 0.0)
    # the strongest gradient's direction (across the channel); the flow is at right angles
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    # quantised to whole steps (1/256 and 1/1000) so a last-bit difference in sin, cos or a
    # sum on another machine can't flip a pixel: the pictures must reproduce byte for byte
    fx = np.rint(-np.sin(theta) * 256).astype(np.int64)
    fy = np.rint(np.cos(theta) * 256).astype(np.int64)
    # downhill: down the screen, and east where the channel runs level
    flip = (fy < -64) | ((np.abs(fy) <= 64) & (fx < 0))
    fx, fy = np.where(flip, -fx, fx), np.where(flip, -fy, fy)
    return fx, fy, np.rint(coherence * 1000).astype(np.int64)


def _hash(*v: np.ndarray) -> np.ndarray:
    h = np.zeros(v[0].shape, dtype=np.uint32)
    for i, a in enumerate(v):
        h ^= (a.astype(np.int64) * (0x9E3779B1 + 0x85EBCA77 * i) & 0xFFFFFFFF).astype(np.uint32)
        h = ((h ^ (h >> np.uint32(15))) * np.uint32(0x2C1B3C6D)) & np.uint32(0xFFFFFFFF)
        h ^= h >> np.uint32(12)
    return h


def sheet(ground: Image.Image, water: set, lava: set):
    """The overlay frames for one zone: (PIL image FRAMES boxes tall, (x, y, w, h)) or None."""
    w, h = ground.size
    base = np.asarray(ground.convert('RGBA'), dtype=np.float32)
    wm = np.zeros((h, w), dtype=bool)
    lm = np.zeros((h, w), dtype=bool)
    for (x, y) in water:
        if 0 <= x < w and 0 <= y < h:
            wm[y, x] = True
    for (x, y) in lava:
        if 0 <= x < w and 0 <= y < h:
            lm[y, x] = True
    if wm.sum() < 60 and lm.sum() < 60:
        return None
    ys, xs = np.mgrid[0:h, 0:w]
    out = np.zeros((FRAMES, h, w, 4), dtype=np.uint8)
    for mask, light, shift, period, lane_w in ((wm, WATER_LIGHT, SHIFT, PERIOD, 3),
                                               (lm, LAVA_LIGHT, LAVA_SHIFT, LAVA_PERIOD, 4)):
        if mask.sum() < 60:
            continue
        lava_pass = light is LAVA_LIGHT
        fx, fy, coh = _flow(mask)
        depth = _depth(mask)
        u = (xs * fx + ys * fy) // 256   # along the flow (whole px)
        v = (-xs * fy + ys * fx) // 256  # across it
        lane = v // lane_w
        lh = _hash(lane, np.zeros_like(lane) + (7 if lava_pass else 3))
        lane_on = (lh % 3) == 0
        phase = (lh >> np.uint32(4)) % period
        length = 2 + (lh >> np.uint32(9)) % 4                       # 2-5 px streaks
        # a channel is narrow water with one clear direction; wide water (the sea, a lake)
        # has no current, only glints, however straight its shore
        deep = _depth(mask, cap=24)
        widest = deep.copy()  # the deepest point within 20 px: half the water's local width
        for _ in range(20):
            widest[1:, :] = np.maximum(widest[1:, :], widest[:-1, :])
            widest[:-1, :] = np.maximum(widest[:-1, :], widest[1:, :])
            widest[:, 1:] = np.maximum(widest[:, 1:], widest[:, :-1])
            widest[:, :-1] = np.maximum(widest[:, :-1], widest[:, 1:])
        narrow = widest <= 20  # a stream or river up to ~40 px wide; wider is a lake or the sea
        channel = mask & narrow & (coh > 500) & (depth >= 1)
        open_w = mask & ~channel & (depth >= 2)
        gh = _hash(xs // 5, ys // 3, np.zeros_like(xs) + 11)
        glint = open_w & ((gh % 41) == 0)
        g_phase = (gh >> np.uint32(6)) % FRAMES
        shore = mask & (depth == 0)
        for f in range(FRAMES):
            pos = (u + phase.astype(np.int64) - f * shift) % period
            streak = channel & lane_on & (pos < length)
            head = streak & (pos == 0)
            lit = np.zeros((h, w), dtype=np.float32)
            lit[streak] = 0.36
            lit[head] = 0.55
            if not lava_pass:
                # glints on open water: a short bright dash for two frames in eight, widening
                age = (f - g_phase.astype(np.int64)) % FRAMES
                for dx, g in ((0, glint & (age < 2)), (1, glint & (age < 2)), (2, glint & (age == 0))):
                    gg = np.zeros_like(g)
                    gg[:, dx:] = g[:, :w - dx] if dx else g
                    gg &= mask
                    lit[gg] = np.maximum(lit[gg], 0.42 if dx == 1 else 0.3)
                # foam lapping on the banks: a broken edge that steps along
                foam = shore & ((((xs + ys) // 2 + f) % 4) == 0)
                lit[foam] = np.maximum(lit[foam], 0.28)
            sel = lit > 0
            if not sel.any():
                continue
            rgb = base[..., :3] + (light - base[..., :3]) * lit[..., None]
            out[f][sel, :3] = np.clip(np.rint(rgb[sel]), 0, 255).astype(np.uint8)
            out[f][sel, 3] = 255
    moving = out[..., 3].any(axis=0)
    if not moving.any():
        return None
    yy, xx = np.nonzero(moving)
    x0, x1, y0, y1 = int(xx.min()), int(xx.max()) + 1, int(yy.min()), int(yy.max()) + 1
    bw, bh = x1 - x0, y1 - y0
    stack = np.zeros((bh * FRAMES, bw, 4), dtype=np.uint8)
    for f in range(FRAMES):
        stack[f * bh:(f + 1) * bh] = out[f, y0:y1, x0:x1]
    return Image.fromarray(stack, 'RGBA'), (x0, y0, bw, bh)
