"""Pendle, 1x master (Claude J, 21 Oct): the station master drawn at density 1.

The 1x design is the master; the chosen 2x final (docs/vision/characters/designs/pendle-final.png)
draws the same design with more detail. Each view below is hand-placed pixel art on the house
palette (sheetkit), one character a texel, written as (y, x0, row) runs. 'o' is the outline: it
takes the edge tone of the fill it closes and breaks to that family's tone 1 where it closes a
lit (tone 4-5) top or left edge, as Fig.outline does. 'i' is ink (eyes, clock hands).

Run:  CHAR_VIEWS=<dir with pendle/final-*.png> python3 scripts/art/characters/masters/pendle.py
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

ID = 'pendle'
CELL = (32, 36)
FOOT = (16, 33)
VIEWS = ('S-idle', 'E-idle', 'W-idle')
GLOW_FAMS = {'lava'}
GLOW: dict = {}   # char -> (family, tone) light sources, never outlined

LEGEND = {
    # soot: coat, cap, boots
    'a': ('soot', 1), 'b': ('soot', 2), 'c': ('soot', 3), 'd': ('soot', 4),
    # soot_warm: the coat skirt plate
    'e': ('soot_warm', 2), 'f': ('soot_warm', 3),
    # brass: bezel, band, badge, porthole rim, cuffs, toe caps, bob
    'g': ('brass', 2), 'h': ('brass', 3), 'j': ('brass', 4),
    # brass_cool: the dial's drum (profile)
    'm': ('brass_cool', 2), 'n': ('brass_cool', 3), 'p': ('brass_cool', 4),
    # plaster: the dial face
    'q': ('plaster', 2), 'r': ('plaster', 3), 't': ('plaster', 4), 'T': ('plaster', 5),
    # copper (verdigris): shoulders, chest panel, mitts, legs
    'v': ('copper', 2), 'w': ('copper', 3), 'x': ('copper', 4), 'y': ('copper', 1),
    # slate: the porthole glass
    'G': ('slate', 2), 'H': ('slate', 3), 'K': ('slate', 4),
}

ART = {
    'S-idle': [
        (7, 13, 'ooooooo'),
        (8, 12, 'oddddcbbo'),
        (9, 12, 'occjjccbo'),
        (10, 12, 'ojjhhhggo'),
        (11, 12, 'oaaaaaaao'),
        (12, 13, 'ojjhhgo'),
        (13, 12, 'ojjTiTggo'),
        (14, 11, 'ojTTTiTTrgo'),
        (15, 11, 'ojTTTiiTrgo'),
        (16, 11, 'ohtitttirgo'),
        (17, 11, 'ohtitttirgo'),
        (18, 12, 'ohhrrrggo'),
        (19, 13, 'ohggggo'),
        (20, 10, 'ooo.oaaao.ooo'),
        (21, 9, 'oxxwcccccbbwwvo'),
        (22, 9, 'oxwwcwxxwwbwvvo'),
        (23, 9, 'ocbbcwjjjwbbbao'),
        (24, 9, 'ocbbchGGGgbbbao'),
        (25, 9, 'ocbbchGhGgbbbao'),
        (26, 9, 'ocbbchHHGgbbbao'),
        (27, 9, 'oxxwffhhheewwvo'),
        (28, 9, 'owwwfffaeeewvvo'),
        (29, 10, 'ooofffaeeeooo'),
        (30, 13, 'owwovvo'),
        (31, 13, 'ohhoggo'),
        (32, 12, 'occcobbbo'),
        (33, 13, 'ooo.ooo'),
    ],
    'E-idle': [
        (7, 13, 'oooooo'),
        (8, 12, 'odddccco'),
        (9, 12, 'occcjjco'),
        (10, 12, 'ojjhhggoo'),
        (11, 12, 'onnhhhbbbo'),
        (12, 11, 'onnjjhhggo'),
        (13, 10, 'opnhTTiTTgo'),
        (14, 10, 'opnhTTiTTgo'),
        (15, 10, 'onnhTTiiTgo'),
        (16, 10, 'onnhtittigo'),
        (17, 10, 'ommhrirrigo'),
        (18, 11, 'ommrrrrggo'),
        (19, 12, 'ommgggo'),
        (20, 13, 'oaaao'),
        (21, 12, 'occxxbwo'),
        (22, 12, 'occwwbwo'),
        (23, 12, 'ocbvvbho'),
        (24, 12, 'ocbaabho'),
        (25, 12, 'ocbwwbGo'),
        (26, 11, 'offexxbGo'),
        (27, 11, 'ofeewweeo'),
        (28, 11, 'ofeeeeeeo'),
        (29, 12, 'oovvwwo'),
        (30, 13, 'ovvwwo'),
        (31, 13, 'ogghho'),
        (32, 13, 'obbccco'),
        (33, 14, 'ooooo'),
    ],
    'W-idle': [
        (7, 13, 'oooooo'),
        (8, 12, 'odddccco'),
        (9, 12, 'ojjcccco'),
        (10, 11, 'oojjhhggo'),
        (11, 10, 'obbbjhhmmo'),
        (12, 11, 'ojjhhhgmmo'),
        (13, 11, 'ojTTiTTgnmo'),
        (14, 11, 'ojTTiTTgnmo'),
        (15, 11, 'ohTTiiTgnmo'),
        (16, 11, 'ohtittignmo'),
        (17, 11, 'ohrirrigmmo'),
        (18, 11, 'ohhrrrrmmo'),
        (19, 13, 'ogggmmo'),
        (20, 14, 'oaaao'),
        (21, 12, 'oxcxxbbo'),
        (22, 12, 'oxcwwbbo'),
        (23, 12, 'ojcvvbbo'),
        (24, 12, 'ojcaabbo'),
        (25, 12, 'oHcwwbbo'),
        (26, 12, 'oHcxxeeeo'),
        (27, 12, 'offwweeeo'),
        (28, 12, 'offfeeeeo'),
        (29, 13, 'owwvvoo'),
        (30, 13, 'owwvvo'),
        (31, 13, 'ohhggo'),
        (32, 12, 'occcbbo'),
        (33, 13, 'ooooo'),
    ],
}

SIMPLIFIED = [
    'Dial face: the 3, 6 and 9 ticks are dropped at 1x so the two 2 px eyes read; the 12 tick and the L of the hands stay.',
    'Coat buttons and panel rivets are dropped (1 px details at 1x); the near arm in E/W keeps one soot elbow collar.',
    'Brass toe caps become the brass boot-top band, so the boots stay solid 2 px blocks.',
    'The porthole is 5 x 5: a brass ring round 3 x 3 slate glass, lit at the lower left, with a 1 px brass bob; in E/W it is a 1 px column of rim and glass at the coat front.',
]
NOTES = [
    'Same families as the 2x: soot (with the warm skirt sibling), copper, brass (with the cool drum sibling), plaster, slate.',
    'Light from the upper left in every facing; W is drawn, not mirrored: the face sits on the lit side and the drum on the shaded side.',
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
