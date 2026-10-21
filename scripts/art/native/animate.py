"""The world's animators, shared by every native screen.

Each animator returns a finite loop of frames that hold only the texels that change (the still
picture stays the ground), drawn on the palette: a streak is the water's own tone a step up, a
glint a pair of light texels, foam the snow family, the fall's ribbons a tone up and down. The
renderer shows one frame at a time on the shared clock and holds frame 0 when motion is reduced
or the screen is inactive (AGENTS.md: effects are finite, respect reduced motion, stop when
their screen is inactive).

Memory: frames are packed in a grid (`pack`, cols x rows) so no picture passes 4096 px; a 2x
woodland's water box is about 600 x 630 texels, 8 frames in 2 x 4 = 1200 x 2520, about 12 MiB
decoded at one image px a texel.

    frames = water(F, T, water_mask, still_mask, s, fall_boxes, n=8)
    img, box, cols = pack(frames)
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
if ART not in sys.path:
    sys.path.insert(0, ART)
import water_flow  # noqa: E402  (the flow direction: the structure tensor of the water's shape)

from . import terrain as TR  # noqa: E402

cc = TR.cc
FRAMES = 8
FRAME_MS = 150            # the zones' clock (lib/zone-maps.ts FLOW_FRAME_MS)


def _h(*v):
    return water_flow._hash(*v)


def water(F, T, mask, still, s, falls=(), n=FRAMES, foam_fid=None):
    """Frames of moving water as (family, tone) changes. Running water: streaks 4 to 10 texels
    along the flow in one lane in three, drifting downstream by 4 world px a frame (a loop of
    32 world px); still water (a pool): glints that come and go in pairs; banks: foam that
    laps along the edge; falls: light ribbons sliding down the sheet. Returns n RGBA arrays."""
    H, W = mask.shape
    ys, xs = np.mgrid[0:H, 0:W]
    fx, fy, coh = water_flow._flow(mask)
    depth = water_flow._depth(mask)
    run = mask & ~still & (depth >= 1)
    shift = int(round(4 * s))
    period = int(round(32 * s))
    lane_w = max(2, int(round(1.5 * s)))
    u = (xs * fx + ys * fy) // 256
    v = (-xs * fy + ys * fx) // 256
    lane = v // lane_w
    lh = _h(lane, np.zeros_like(lane) + 3)
    lane_on = (lh % 3) == 0
    phase = ((lh >> np.uint32(4)) % np.uint32(period)).astype(np.int64)
    length = (2 + (lh >> np.uint32(9)) % 4).astype(np.int64) * max(1, int(round(s)))
    gh = _h(xs // (3 * max(1, int(s))), ys // (2 * max(1, int(s))), np.zeros_like(xs) + 11)
    glint = still & (depth >= 2) & ((gh % 23) == 0) & (xs % 2 == 0)
    g_phase = ((gh >> np.uint32(6)) % np.uint32(n)).astype(np.int64)
    shore = mask & (depth == 0)
    foam_fid = cc.FID['snow'] if foam_fid is None else foam_fid
    out = []
    lut = cc.LUT
    for f in range(n):
        dT = np.zeros((H, W), np.int32)
        fam = F.copy()
        pos = (u + phase - f * shift) % period
        streak = run & lane_on & (pos < length)
        head = streak & (pos == 0)
        dT[streak] = 1
        dT[head] = 2
        age = (f - g_phase) % n
        g = glint & (age < 2)
        g2 = np.zeros_like(g)
        g2[:, 1:] = g[:, :-1]
        dT[(g | g2) & still] = 2
        lap = shore & ((((xs + ys) // max(2, int(2 * s)) + f) % 4) == 0)
        dT[lap] = np.maximum(dT[lap], 1)
        # falls: ribbons sliding down the sheet, the white water where it lands churning
        for (x0, y0, x1, y1) in falls:
            box = (xs >= x0) & (xs < x1) & (ys >= y0) & (ys <= y1 + int(2 * s)) & mask
            col_ph = (_h(xs // max(1, int(s)), np.zeros_like(xs) + 5) % np.uint32(period)).astype(np.int64)
            fp = (ys - f * shift * 2 + col_ph) % (period // 2)
            light = box & (fp < 3 * s) & (T < 5)
            dark = box & (fp >= period // 4) & (fp < period // 4 + 2 * s) & (T > 2)
            dT[light] = 1
            dT[dark] = -1
        sel = dT != 0
        tt = np.clip(T + dT, 0, 5)
        rgb = lut[fam, tt]
        fr = np.zeros((H, W, 4), np.uint8)
        fr[sel, :3] = rgb[sel]
        fr[sel, 3] = 255
        out.append(fr)
    return out


def pack(frames, cols=2):
    """The frames cropped to the box where anything moves and packed in a grid: (image, box
    (x, y, w, h) in texels, cols)."""
    moving = np.zeros(frames[0].shape[:2], bool)
    for fr in frames:
        moving |= fr[..., 3] > 0
    if not moving.any():
        return None
    yy, xx = np.nonzero(moving)
    x0, x1, y0, y1 = int(xx.min()), int(xx.max()) + 1, int(yy.min()), int(yy.max()) + 1
    # whole world px: even texels at 2x
    x0 -= x0 % 2
    y0 -= y0 % 2
    x1 += x1 % 2
    y1 += y1 % 2
    bw, bh = x1 - x0, y1 - y0
    n = len(frames)
    rows = (n + cols - 1) // cols
    sheet = np.zeros((rows * bh, cols * bw, 4), np.uint8)
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * bh:(r + 1) * bh, c * bw:(c + 1) * bw] = fr[y0:y1, x0:x1]
    return Image.fromarray(sheet, 'RGBA'), (x0, y0, bw, bh), cols


def lantern(d, lit_frames=4):
    """The lantern flame's frames are its glass's tones (the props.lantern_post 'lit' picture):
    the flame's brightest cluster moves a texel up and back (anticipate, act, settle). Kept
    for the night layer: (offset_y texels per frame, ms per frame)."""
    return [(0, 400), (-1, 300), (0, 500), (1, 300)][:lit_frames]
