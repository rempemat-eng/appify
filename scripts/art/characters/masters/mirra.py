"""Mirra, 1x master (Claude J, 21 Oct): the cone-hat pilgrim drawn at density 1.

The 1x design is the master; the chosen 2x final (docs/vision/characters/designs/mirra-final.png)
draws the same design with more detail. Each view below is hand-placed pixel art on the house
palette (sheetkit), one character a texel, written as (y, x0, row) runs. 'o' is the outline: it
takes the edge tone of the fill it closes and breaks to that family's tone 1 where it closes a
lit (tone 4-5) top or left edge, as Fig.outline does. 'i' is ink (the eyes).

Run:  CHAR_VIEWS=<dir with mirra/final-*.png> python3 scripts/art/characters/masters/mirra.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ID = 'mirra'
CELL = (32, 36)
FOOT = (16, 33)
VIEWS = ('S-idle', 'E-idle', 'W-idle')
GLOW_FAMS = {'lava'}
GLOW: dict = {}   # char -> (family, tone) light sources, never outlined

LEGEND = {
    # bleached straw: the cone hat
    'g': ('bleached', 1), 'h': ('bleached', 2), 'H': ('bleached', 3), 'J': ('bleached', 4),
    # sand: skin, tail, feet
    'r': ('sand', 1), 's': ('sand', 2), 'S': ('sand', 3), 'T': ('sand', 4),
    # adobe: the wrap in fold bands
    'b': ('adobe', 2), 'c': ('adobe', 3), 'd': ('adobe', 4),
    # timber: the twig, the knot, the cork
    'm': ('timber', 2), 'n': ('timber', 3),
    # water: the big flask
    'w': ('water', 2), 'x': ('water', 3), 'y': ('water', 4), 'z': ('water', 5),
}

ART = {
    'S-idle': [
        (12, 15, 'mm'),
        (13, 14, 'oJHo'),
        (14, 13, 'oJJHHo'),
        (15, 12, 'oJJJHHHo'),
        (16, 11, 'oJJJJHHHHo'),
        (17, 11, 'oggggggggo'),
        (18, 10, 'oSiiTTTSiiso'),
        (19, 10, 'oSiiTSSSiiso'),
        (20, 9, 'm.m.oTrrSSo'),
        (21, 10, 'm.oddccbbo'),
        (22, 10, 'moSdbccbbso'),
        (23, 9, 'oTSSdbccbbso'),
        (24, 9, 'oTSddbccbbso'),
        (25, 10, 'ooHHHHHmmso'),
        (26, 11, 'oddbczzxwo'),
        (27, 10, 'odddbcxxxwo'),
        (28, 10, 'odccbcowwoSo'),
        (29, 12, 'oSsoSsooSso'),
        (30, 12, 'oSsoSso.oso'),
        (31, 12, 'oSsoSsoosso'),
        (32, 11, 'oSSsoSSSooo'),
        (33, 12, 'ooo.ooo'),
    ],
    'E-idle': [
        (11, 16, 'o'),
        (12, 15, 'omo'),
        (13, 14, 'oJmHo'),
        (14, 13, 'oJJJHHo'),
        (15, 12, 'oJJJJHHHo'),
        (16, 11, 'oJJJJJHHHHo'),
        (17, 12, 'oggggggoo'),
        (18, 12, 'oTTSiiSSo'),
        (19, 12, 'oSSSiiSSso'),
        (20, 13, 'oSSSrrsso'),
        (21, 12, 'oddcccbo'),
        (22, 12, 'odbcTSbo'),
        (23, 12, 'odbcTSbo'),
        (24, 12, 'odbcTSbo'),
        (25, 12, 'oHHHSSmmo'),
        (26, 11, 'oddbcczxxwo'),
        (27, 11, 'oddbcczxxwo'),
        (28, 11, 'occbccxxwwo'),
        (29, 10, 'oSSSrTSowwo'),
        (30, 9, 'oSsoorTSooo'),
        (31, 9, 'ossssrTSo'),
        (32, 10, 'ooorrTSSo'),
        (33, 13, 'ooooo'),
    ],
    'W-idle': [
        (11, 15, 'o'),
        (12, 14, 'omo'),
        (13, 13, 'oJmHo'),
        (14, 12, 'oJJJHHo'),
        (15, 11, 'oJJJJHHHo'),
        (16, 10, 'oJJJJJHHHHo'),
        (17, 11, 'ooggggggo'),
        (18, 11, 'oTTiiSSso'),
        (19, 10, 'oSSSiiSSso'),
        (20, 10, 'oSSrrSSSo'),
        (21, 11, 'omddccbbo'),
        (22, 11, 'omdTScbbo'),
        (23, 11, 'omdTScbbo'),
        (24, 11, 'oSSSScbbo'),
        (25, 11, 'ommHHHHHo'),
        (26, 10, 'ozxxwccbbbo'),
        (27, 10, 'ozxxwccbbbo'),
        (28, 10, 'oxxwwccbcco'),
        (29, 11, 'owwoTSrssso'),
        (30, 12, 'oooTSroosso'),
        (31, 14, 'oTSrsssso'),
        (32, 13, 'oTSSrrooo'),
        (33, 14, 'ooooo'),
    ],
}

SIMPLIFIED = [
    'Cone hat: the radial plaits and rolled rim become a lit-left / shaded-right split over a dark underside row; the timber knot stays at the tip.',
    'Wrap: the four fold bands become two (one dark band each side of a lit front) and the scalloped hem a two-tone hem row; the crossover is dropped.',
    'Flask strap: the 1 px timber belly strap is dropped; the flask hangs at the bleached sash with its timber cork.',
    'Twig: the Y twig is a 3 x 3 px Y in timber 2 with no outline (the dark timber is its own edge); in E it is in the far hand (hidden) and in W a 3 px stick in the near hand.',
    'Tail: the banded tail is plain sand at 1x, curled round the heel as in the 2x.',
]
NOTES = [
    'Same families as the 2x: sand, adobe, bleached, water, timber.',
    'Light from the upper left in every facing; W is drawn, not mirrored: the snout, flask and twig sit on the lit front.',
]


# --- shared master machinery (identical in each master script) ------------------------------
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
D4 = ((1, 1), (-1, -1), (1, -1), (-1, 1))


def pick(pool):
    return max(sorted(set(pool), key=str), key=pool.count)


def draw(view: str) -> sk.Fig:
    fig = sk.Fig(*CELL)
    outline = set()
    for y, x0, run in ART[view]:
        for k, ch in enumerate(run):
            x = x0 + k
            if ch == '.':
                continue
            assert fig.inside(x, y), (view, x, y)
            assert (x, y) not in fig.px and (x, y) not in outline, (view, 'twice', x, y)
            if ch == 'o':
                outline.add((x, y))
            elif ch == 'i':
                fig.put(x, y, 'ink', 0)
            elif ch in GLOW:
                fig.glow(x, y, *GLOW[ch])
            else:
                fig.put(x, y, *LEGEND[ch])
    fills = {p: v for p, v in fig.px.items() if v[0] != 'ink'}
    common = pick([sk.family_of(f) for f, _ in fills.values()])
    for q in sorted(outline):
        edge, lit = [], []
        for dx, dy in N4:
            p = (q[0] - dx, q[1] - dy)          # the fill this outline pixel closes
            if p not in fills or p in fig.fixed:
                continue
            fam, tone = fills[p]
            if (dx == -1 or dy == -1) and tone >= 4:
                lit.append(fam)
            else:
                edge.append(fam)
        if edge:
            fig.px[q] = ('_edge', pick(edge))
        elif lit:
            fig.px[q] = ('_lit', pick(lit))
        else:
            diag = [fills[(q[0] + dx, q[1] + dy)][0] for dx, dy in D4 if (q[0] + dx, q[1] + dy) in fills]
            fig.px[q] = ('_edge', pick(diag) if diag else common)
    return fig


def families_fig(fig: sk.Fig) -> list:
    return sorted({sk.family_of(f) for f, _ in fig.px.values()
                   if f not in ('ink', '_edge', '_lit') and sk.family_of(f) not in GLOW_FAMS})


_RAMP_RGB = {}
for _f, _r in sk.RAMPS.items():
    for _h in _r:
        _RAMP_RGB.setdefault(sk.hp.hex_rgb(_h), set()).add(sk.family_of(_f))


def families_img(img: Image.Image) -> list:
    out = set()
    im = img.convert('RGBA')
    px = im.load()
    for r, g, b, a in (px[x, y] for y in range(im.height) for x in range(im.width)):
        if a >= 128 and (r, g, b) in _RAMP_RGB:
            out |= _RAMP_RGB[(r, g, b)]
    return sorted(out - GLOW_FAMS)


def iou(one: Image.Image, two: Image.Image, foot2) -> float:
    a1 = one.getchannel('A').load()
    a2 = two.getchannel('A').load()
    dx, dy = FOOT[0] - foot2[0] // 2, FOOT[1] - foot2[1] // 2
    s1 = {(x, y) for y in range(one.height) for x in range(one.width) if a1[x, y] >= 128}
    s2 = set()
    for y in range(two.height // 2):
        for x in range(two.width // 2):
            n = sum(1 for i in (0, 1) for j in (0, 1) if a2[2 * x + i, 2 * y + j] >= 128)
            if n >= 2:
                s2.add((x + dx, y + dy))
    return len(s1 & s2) / max(1, len(s1 | s2))


def on_grass(img: Image.Image, k: int) -> Image.Image:
    big = img.resize((img.width * k, img.height * k), Image.NEAREST)
    tile = Image.new('RGB', big.size, sk.GRASS)
    tile.paste(big, (0, 0), big)
    return tile


def main():
    views_dir = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(REPO, '.char-views')), ID)
    out_dir = os.path.join(REPO, 'docs', 'vision', 'characters', 'masters')
    os.makedirs(views_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(REPO, 'docs', 'vision', 'characters', 'designs', ID + '.json')) as f:
        foot2 = tuple(json.load(f)['foot'])
    rows, data = [], {}
    for v in VIEWS:
        fig = draw(v)
        one = fig.image()
        one.save(os.path.join(views_dir, f'master-{v}.png'))
        two = Image.open(os.path.join(views_dir, f'final-{v}.png')).convert('RGBA')
        m = sk.measure(one)
        data[v] = {'iou': round(iou(one, two, foot2), 3), 'families_1x': families_fig(fig),
                   'families_2x': families_img(two),
                   'measure': {k: (round(val, 4) if isinstance(val, float) else val) for k, val in m.items()}}
        rows.append((v, one, two))
    # the sheet: 1x at 8x beside 2x at 4x, then the game-scale row (1x at 2, 2x at 1)
    pad, f_head, f_body = 16, sk._font(18), sk._font(12)
    tw, th = CELL[0] * 8, CELL[1] * 8
    W = pad + len(rows) * (2 * tw + 8 + pad * 2)
    H = 50 + th + 40 + CELL[1] * 2 + 40 + 18 * (len(SIMPLIFIED) + 2) + pad
    sheet = Image.new('RGB', (W, H), sk.PAPER)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), f'{ID.title()}: 1x master (8x) beside the 2x final (4x), then game scale', fill=sk.TEXT, font=f_head)
    x = pad
    for v, one, two in rows:
        y = 50
        sheet.paste(on_grass(one, 8), (x, y))
        sheet.paste(on_grass(two, 4), (x + tw + 8, y))
        y += th + 4
        r = data[v]
        same = 'same' if r['families_1x'] == r['families_2x'] else 'DIFFER'
        d.text((x, y), f"{v}: IoU {r['iou']:.2f}, families {same}, lone {100 * r['measure']['isolated']:.1f}%",
               fill=sk.TEXT, font=f_body)
        y += 30
        sheet.paste(on_grass(one, 2), (x, y))
        sheet.paste(on_grass(two, 1), (x + CELL[0] * 2 + 8, y))
        x += 2 * tw + 8 + pad * 2
    y = 50 + th + 40 + CELL[1] * 2 + 16
    for line in ['Simplified at 1x:'] + ['- ' + s for s in SIMPLIFIED]:
        d.text((pad, y), line, fill=sk.TEXT, font=f_body)
        y += 18
    sheet.save(os.path.join(out_dir, f'{ID}-1x.png'))
    with open(os.path.join(out_dir, f'{ID}.json'), 'w') as f:
        json.dump({'id': ID, 'views': data, 'simplified': SIMPLIFIED, 'notes': NOTES}, f, indent=2)
        f.write('\n')
    for v in VIEWS:
        r = data[v]
        print(f"{ID} {v}: iou {r['iou']:.3f} fam1 {r['families_1x']} fam2 {r['families_2x']} "
              f"lone {100 * r['measure']['isolated']:.1f}% W-E {r['measure']['west_east']:+.1f} "
              f"dark {100 * r['measure'].get('outline_dark', 0):.0f}%")


if __name__ == '__main__':
    main()
