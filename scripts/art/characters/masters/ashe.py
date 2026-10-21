"""Ashe, 1x master (Claude J, 21 Oct): the half-plate drake drawn at density 1.

The 1x design is the master; the chosen 2x final (docs/vision/characters/designs/ashe-final.png)
draws the same design with more detail. Each view below is hand-placed pixel art on the house
palette (sheetkit), one character a texel, written as (y, x0, row) runs. 'o' is the outline: it
takes the edge tone of the fill it closes and breaks to that family's tone 1 where it closes a
lit (tone 4-5) top or left edge, as Fig.outline does. 'i' is ink (the eyes). '*' is the ember
glow at the tail tip (lava, a light source: never outlined, left out of the family check).

Run:  CHAR_VIEWS=<dir with ashe/final-*.png> python3 scripts/art/characters/masters/ashe.py
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

ID = 'ashe'
CELL = (32, 36)
FOOT = (16, 33)
VIEWS = ('S-idle', 'E-idle', 'W-idle')
GLOW_FAMS = {'lava'}
GLOW: dict = {'*': ('lava', 3)}   # char -> (family, tone) light sources, never outlined

LEGEND = {
    # clay: ember scales (tones 1-3 lead; 4 only on the snout ridge and knuckles)
    'q': ('clay', 1), 'r': ('clay', 2), 's': ('clay', 3), 't': ('clay', 4),
    # slate: breastplate, pauldron, greaves
    'A': ('slate', 2), 'B': ('slate', 3), 'C': ('slate', 4),
    # slate_cool: bracers, boots
    'D': ('slate_cool', 2), 'E': ('slate_cool', 3), 'F': ('slate_cool', 4),
    # ashlar: the quilted gambeson
    'g': ('ashlar', 2), 'h': ('ashlar', 3), 'j': ('ashlar', 4),
    # ashlar_cool: breeches
    'u': ('ashlar_cool', 2), 'v': ('ashlar_cool', 3),
    # ash: horns, belt, the greying patch
    'w': ('ash', 2), 'x': ('ash', 3), 'y': ('ash', 4),
    # brass: the big bedtime bell
    'm': ('brass', 2), 'n': ('brass', 3), 'p': ('brass', 4),
}

ART = {
    'S-idle': [
        (5, 10, 'o'),
        (6, 9, 'oyo.........o'),
        (7, 8, 'oyyo........oyo'),
        (8, 8, 'oyyxoooooooxyyo'),
        (9, 9, 'oyxxtsssssxxo'),
        (10, 10, 'oxttsssssxwo'),
        (11, 11, 'osissssiro'),
        (12, 11, 'osisttsiro'),
        (13, 9, 'orrsssqqssrro'),
        (14, 10, 'ooorrssrroo'),
        (15, 13, 'orrrro.CCo'),
        (16, 12, 'oorrrroCCBBo'),
        (17, 10, 'otsCCCBBBCBBBAo'),
        (18, 9, 'otssCCBBBACBBBAo'),
        (19, 9, 'otssCBBBBACBBAAo'),
        (20, 9, 'osssCBAABACBBAAo'),
        (21, 9, 'osssCBBBBAAAAAAo'),
        (22, 9, 'oFEDhhhhhhhFEDo'),
        (23, 9, 'oFEDxxxxxxxFEDo'),
        (24, 9, 'osssshhhnnmssro'),
        (25, 9, 'osssshhpnnmssro'),
        (26, 10, 'ooggggpnnmoorro'),
        (27, 11, 'ovvuommmmrrro'),
        (28, 12, 'ovuoovvrrrro'),
        (29, 12, 'oCBBACBrro'),
        (30, 12, 'oCBBACBoo'),
        (31, 12, 'oFEEoEDo'),
        (32, 12, 'oFEEoEDo'),
        (33, 13, 'ooo.oo'),
    ],
    'E-idle': [
        (5, 10, 'oo'),
        (6, 9, 'oyyo'),
        (7, 8, 'oyyyxo'),
        (8, 10, 'oyxxoooo'),
        (9, 11, 'oxssssso'),
        (10, 10, 'otttsssrro'),
        (11, 11, 'ottsssissso'),
        (12, 11, 'ossrrrisssro'),
        (13, 10, 'orsrrrrrqqqro'),
        (14, 12, 'orrrrqqqqqo'),
        (15, 13, 'orrrooooo'),
        (16, 10, 'oCBBrrro'),
        (17, 9, 'oCCBAswsBAo'),
        (18, 9, 'oCBBAswsBAo'),
        (19, 10, 'oBBAssrBAAo'),
        (20, 10, 'oBBAssrBAAo'),
        (21, 11, 'oBAFEDBAo'),
        (22, 9, 'o*shhFEDggo'),
        (23, 9, 'ossxxFEDwwwo'),
        (24, 8, 'osrohhtssggno'),
        (25, 9, 'osohhtssggnno'),
        (26, 9, 'osrggggggnnmo'),
        (27, 9, 'osrrrACBBmmmmo'),
        (28, 10, 'ooooACBBoooo'),
        (29, 13, 'oACBBo'),
        (30, 13, 'oACBBo'),
        (31, 13, 'oDDEEEDo'),
        (32, 13, 'oDDEEDDo'),
        (33, 14, 'oooooo'),
    ],
    'W-idle': [
        (5, 20, 'oo'),
        (6, 19, 'oyyo'),
        (7, 18, 'oyyxxo'),
        (8, 14, 'ooooyyyo'),
        (9, 13, 'osssssyo'),
        (10, 12, 'ossssssrro'),
        (11, 10, 'otttissssro'),
        (12, 9, 'ostssissrrro'),
        (13, 9, 'osqqqssrrrrro'),
        (14, 9, 'oqqqqqrrrro'),
        (15, 10, 'ooooorrrCCo'),
        (16, 14, 'orrrCCBo'),
        (17, 12, 'oCByxwCBBAo'),
        (18, 12, 'oCByxwCBBAo'),
        (19, 11, 'oCBByxwCBAo'),
        (20, 11, 'oCBBxxwCBAo'),
        (21, 12, 'oBBFEDCBo'),
        (22, 12, 'ohhFEDhhr*o'),
        (23, 11, 'oxxxFEDxxrro'),
        (24, 11, 'onhhtsshhorro'),
        (25, 10, 'onnhhtsshhoro'),
        (26, 10, 'onnmggggggrro'),
        (27, 9, 'ommmmCBBArrrro'),
        (28, 10, 'ooooCBBAoooo'),
        (29, 13, 'oCBBAo'),
        (30, 13, 'oCBBAo'),
        (31, 11, 'oFEEDDDo'),
        (32, 11, 'oFEEDDDo'),
        (33, 12, 'oooooo'),
    ],
}

SIMPLIFIED = [
    'Eyes: the amber glint is dropped; each eye is a 1 x 2 ink stroke so it reads at 1x.',
    'Breastplate: the ridge and brass rivets are dropped; the one dent stays as a 2 px dark mark (S); the pauldron lame is its dark bottom row.',
    'Gambeson: the quilted channels become a lit row over a hem row; the brass belt buckle and the ash claws are dropped.',
    'The ash strap over the bare shoulder (E) is a 2 px stroke; the bell clapper is folded into the bell body (top, body, rim).',
    'Tail: the ember tip is one lava glow texel in E/W (hidden behind the leg in S, as in the 2x).',
]
NOTES = [
    'Same families as the 2x: clay, slate (with the cool sibling for bracers and boots), ashlar (with the cool sibling for the breeches), ash, brass; lava is the glow.',
    'Light from the upper left in every facing; W is drawn, not mirrored: the snout and bell sit on the lit front, the pauldron and tail on the shaded back.',
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
