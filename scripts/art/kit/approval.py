"""Approval sheets for the library gate (docs/world-editor.md, "The library gate"): one per material.

    python3 -m scripts.art.kit.approval OUT_DIR [--eastward CROPS_DIR]

Each sheet shows, at 3x: the material's fill; every transition it takes part in (each mask with
its first profile combinations); its dressing decals; Bramble at the same scale; a crop of a test
layout drawn by the reference renderer (the pixels Godot draws, test_kit and the labs hold them
equal); and, when CROPS_DIR is given, the matching Eastward evidence crops
(scripts/art/eastward_study.py crops) scaled to the same character height (our adult 74 art px,
Eastward's 54: 1.37, shown at 4x for 3x of ours). The Eastward crops are local only: never commit
a sheet that carries them.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from scripts.art.kit.build import Kit
from scripts.art.kit import edges as E
from scripts.art.kit.render_zone import render
from scripts.art.kit.schema import ROOT
from scripts.art.native.palette import step, to_rgba

S = 3
BG = (34, 34, 38)
INK = (225, 225, 230)

# material -> (lab zone, crop box in texels, Bramble's foot in the crop, Eastward crops)
SHEETS = {
    'lawn': ('kitlab', (0, 300, 300, 200), (250, 190), ['10-grass-dirt', '17-plants']),
    'path': ('kitlab', (40, 30, 420, 230), (360, 210), ['10-grass-dirt', '05-round-corner']),
    'water': ('kitlab', (560, 280, 400, 272), (378, 196), ['12-bank', '13-pond']),
    'earth_face': ('kitlab_tiers', (60, 50, 600, 300), (40, 290), ['03-ledge', '09-foot', '08-side', '14-stair-farm']),
    'scree': ('woodland_kit', (0, 0, 480, 160), (440, 150), ['07-cliff-face']),
    'worn': ('woodland_kit', (60, 1150, 360, 200), (330, 190), ['10-grass-dirt']),
    'cobble_road': (None, None, None, ['11-grass-cobble']),
}


def bramble() -> Image.Image:
    p = os.path.join(ROOT, 'game', 'assets', 'characters', 'bramble', 'sheets', 'idle_S.png')
    im = Image.open(p).convert('RGBA')
    cell = im.crop((0, 0, 160, 144))
    bb = cell.getbbox()
    return cell.crop(bb)


def tile_rgb(kit, tid, idx, u, lo):
    t = kit.over[tid][idx]
    op, val = t[..., 0], t[..., 1]
    fu = kit.fills[u][96:96 + E.CELL, 96:96 + E.CELL]
    fl = kit.fills[lo][96:96 + E.CELL, 96:96 + E.CELL]
    code = fl.copy()
    code = np.where(op == E.OP_UPPER, step(fu, val - 128), code)
    code = np.where(op == E.OP_DELTA, step(code, val - 128), code)
    code = np.where(op == E.OP_ABS, val, code)
    return Image.fromarray(to_rgba(code)[..., :3])


def big(im: Image.Image, s: int = S) -> Image.Image:
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def sheet(kit: Kit, mid_name: str, eastward: str | None) -> Image.Image:
    mid = kit.ids[mid_name]
    lab, box, foot, ew = SHEETS[mid_name]
    parts = []           # (title, image)
    fill = kit.fills[mid][:96, :192]
    if mid in kit.strip:
        fill = kit.fills[mid][:kit.strip[mid], :192]
    parts.append(('fill (periodic, %d px)' % kit.period, big(Image.fromarray(to_rgba(fill)[..., :3]))))
    for t in kit.man['transitions']:
        if mid_name not in (t['upper'], t['lower']):
            continue
        u = kit.ids[t['upper']]
        lo = kit.ids[t['lower']] if t['lower'] in kit.ids else u
        layout = E.layout(t['variants'])
        per = {}
        for idx, k, prof, v in layout:
            per.setdefault(k, []).append(idx)
        cols = 6
        row_h = (E.CELL + 2) * S
        im = Image.new('RGB', (cols * (E.CELL + 2) * S, 14 * row_h), BG)
        for r, k in enumerate(range(1, 15)):
            for c, idx in enumerate(per[k][:cols]):
                im.paste(big(tile_rgb(kit, t['id'], idx, u, lo)), (c * (E.CELL + 2) * S, r * row_h))
        parts.append(('%s over %s: 14 masks x first 6 profile sets (%d tiles in all)' % (t['upper'], t['lower'], len(layout)), im))
    dec = set()
    for t in kit.man['transitions']:
        if mid_name in (t['upper'], t['lower']) and t.get('dressing'):
            for side in ('south', 'north', 'side'):
                dec |= set(t['dressing'].get(side) or [])
    if dec:
        ds = sorted(dec)
        w = sum(kit.decals[d][0].shape[1] + 4 for d in ds)
        h = max(kit.decals[d][0].shape[0] for d in ds)
        im = Image.new('RGB', (w, h), (120, 150, 90))
        x = 0
        for d in ds:
            dc = kit.decals[d][0]
            rgba = Image.fromarray(np.where((dc >= 0)[..., None], to_rgba(np.maximum(dc, 0)), 0).astype(np.uint8), 'RGBA')
            im.paste(rgba, (x, h - dc.shape[0]), rgba)
            x += dc.shape[1] + 4
        parts.append(('dressing decals', big(im)))
    if lab:
        im = render(lab, sprites=True).crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
        br = bramble()
        im.alpha_composite(br, (foot[0] - br.width // 2, foot[1] - br.height))
        parts.append(('test layout: %s (the renderer Godot matches), Bramble for scale' % lab, big(im)))
    if eastward:
        for name in ew:
            p = os.path.join(eastward, name + '.png')
            if os.path.exists(p):
                e = Image.open(p).convert('RGB')
                parts.append(('Eastward %s (local reference, same character height: 4x of native)' % name, big(e, 4)))
    W = max(p[1].width for p in parts) + 40
    H = sum(p[1].height + 40 for p in parts) + 60
    out = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(out)
    approval = kit.meta[mid]['approval']
    d.text((20, 16), '%s  (material %d, %s)  library gate sheet, 3x' % (mid_name, mid, approval), fill=INK)
    y = 60
    for title, im in parts:
        d.text((20, y - 18), title, fill=INK)
        out.paste(im.convert('RGB'), (20, y))
        y += im.height + 40
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--eastward')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    kit = Kit()
    for m in SHEETS:
        if m in kit.ids:
            sheet(kit, m, a.eastward).save(os.path.join(a.out, 'approval_%s.png' % m))
            print('wrote', os.path.join(a.out, 'approval_%s.png' % m))
    return 0


if __name__ == '__main__':
    sys.exit(main())
