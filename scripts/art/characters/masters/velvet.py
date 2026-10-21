"""Velvet's 1x master (Claude J, 21 Oct): the chosen 2x design (option C, ruff and
swallowtail coat, lamp at the right hip) redrawn at density 1 as pixel art, never a
downscale (Matt, 21 Oct 18:17: the 1x design is the master and every density draws the
same design).

Run from the repo root:
    CHAR_VIEWS=<dir with velvet/final-*.png> python3 scripts/art/characters/masters/velvet.py
Writes docs/vision/characters/masters/velvet-1x.png (1x at 8x beside 2x at 4x, then the
game-scale row) and velvet.json (silhouette IoU against the 2x final, families, measure),
and each 1x view as $CHAR_VIEWS/velvet/master-<view>.png.

Cell folk 32 x 36, foot (16, 33); heightWorld 23.
"""
from __future__ import annotations

import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ID = 'velvet'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}-1x.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}.json')

CELL = (32, 36)
FOOT = (16, 33)
FOOT_2X = (32, 66)

# --- the drawing: one letter a texel, (family, tone) on the house palette ----------------
# Outline comes from Fig.outline() (each material's edge tone, lit break at the top left).
# 'L' is the lamp's glow (never outlined).
LEGEND = {
    'A': ('plaster', 5), 'P': ('plaster', 4), 'p': ('plaster', 3), 'n': ('plaster', 2),
    'f': ('plaster_cool', 3),
    'W': ('snow', 5), 'S': ('snow', 4), 's': ('snow', 3), 'z': ('snow', 2), 'Z': ('snow_cool', 1),
    'D': ('dusk', 3), 'd': ('dusk', 2), 'v': ('dusk', 1), 'k': ('dusk', 0),
    'u': ('dusk_warm', 2),
    'Y': ('brass', 4), 'y': ('brass', 3), 'b': ('brass', 2),
    'I': ('iron', 4), 'i': ('iron', 3), 'j': ('iron', 2), 'J': ('iron', 1),
    'L': ('lamp', 2), 'K': ('ink', 0),
}
X0, Y0 = 8, 10

VIEWS = {
    'S-idle': [
        '...AAAA...PPPP...',
        '..A....A.P....P..',
        '.A....PPppp....p.',
        '.....PPPpppn.....',
        '.....pWKpWKn.....',
        '.....pKKpKKn.....',
        '....SppPPnnns....',
        '...SSSnnnnnss....',
        '....SSzzzzzzs....',
        '...SSSssssssszz..',
        '...SSsssssszz....',
        '....ssZZssZZ.....',
        '....DDddkddv.....',
        '....PPddkddv.....',
        '....yyYYyybb.....',
        '....DDddkdppv....',
        '..yyDDddkddvv....',
        '.YYyyDddkddvv....',
        '.IiiJdddkdvvv....',
        '.ILiJdddkdvvvu...',
        '.IiiJvvvkvvvvu...',
        '..yyvvvvkvvvvu...',
        '......IIIjj..u...',
    ],
    'E-idle': [
        '....AAA..........',
        '...A...AA........',
        '..A.fff.PPPp.....',
        '..A.f.PPppppn....',
        '......PpppWKn....',
        '......PpppKKpp...',
        '....SSppppppp....',
        '....Sssnnnn......',
        '....Ssszzzz......',
        '....SSsssssszz...',
        '....SSssssssz....',
        '....ZZssZZss.....',
        '.....DDdddvv.....',
        '.....DDdddvv.....',
        '.....yyYYyyy.....',
        '....DDdddppv.....',
        '....DDYYydvv.....',
        '....DDIIJdvv.....',
        '....DDIIJdvv.....',
        '...uDDILJvvvv....',
        '..uuDDIIJvvvv....',
        '.uuuuvyyyvvv.....',
        '.u...IIIjj.......',
    ],
    'W-idle': [
        '..........AAA....',
        '........AA...A...',
        '.....PPPp.fff.A..',
        '....PPppppn.f.A..',
        '....PWKpppn......',
        '...PPKKpppn......',
        '....Pppppppss....',
        '......nnnnsss....',
        '....SSzzzzzs.....',
        '...SSSssssszz....',
        '....SSsssssz.....',
        '....ZZssZZss.....',
        '.....DDdddvv.....',
        '.....DDdddvv.....',
        '.....yyYYyyy.....',
        '....ppDDddvv.....',
        '....DDDDddvvYYy..',
        '....DDDdddvvIIJ..',
        '....DDDdddvvvIJ..',
        '....DDddvvvvvIJ..',
        '....DDvvvvvvvjj..',
        '....vvvvvvvvyyuu.',
        '.....IIIjj....uu.',
    ],
}

SIMPLIFIED = [
    'Antennae: the combed 2x plumes become 1 px plaster arcs without comb teeth (plaster 5 on '
    'the lit one), the far one a short plaster_cool stroke in E/W.',
    'Eyes: the big round 2x eyes become 2 x 2 ink with a 1 px snow glint; brow and cheek tufts '
    'are dropped; the muzzle is a lit 2 px step.',
    'Ruff: the downward fur strokes become three snow tones with a scalloped hem (snow_cool '
    'pairs); the chin shadow stays.',
    'Coat: the fold bands become 2 px dusk bands (lit left, deep right) either side of the dark '
    'front seam (S); the '
    'chevron margin and the faint eye-spot on the tails are dropped, the swallowtail tips stay '
    'as dusk_warm texels.',
    'Lamp: shutter slats become an iron box with a brass cap, handle and foot and a single '
    'lamp-glow texel (S, E); in W it sits behind the coat with no glow.',
]
NOTES = [
    'Same design as the 2x final (option C): a pale moth head with two swept antennae and big '
    'eyes, a wide snow ruff, a narrow dusk swallowtail coat with a brass belt, the shuttered lamp '
    'at her right hip (screen left in S, in front in E, behind in W), iron feet.',
    'W is drawn, not mirrored: the light stays at the upper left, and the lamp moves to the far '
    'side instead of reflecting.',
    'Compared with Matt\'s 1x Bramble: three tones a material plus the edge tone, solid ink '
    'eyes, chunky clusters.',
]


# --- shared master harness (same in every masters/<id>.py) -------------------------------
def draw(rows):
    fig = sk.Fig(*CELL)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            fam, tone = LEGEND[ch]
            if fam in _GLOW or fam == '_edge':   # light sources and drawn seams: no outline
                fig.glow(X0 + i, Y0 + j, fam, tone)
            else:
                fig.put(X0 + i, Y0 + j, fam, tone)
    fig.outline()
    return fig


_PAL = sk._PAL
_GLOW = {f for f in _PAL['ramps'] if not _PAL['edges'].get(sk.family_of(f))}
_REV: dict = {}
for _f, _r in _PAL['ramps'].items():
    for _c in _r:
        _REV.setdefault(sk.hp.hex_rgb(_c), set()).add(sk.family_of(_f))


def families(img) -> list:
    """House families an image uses (exact palette colours; edges, ink and glows aside).
    A colour two families share counts for one already present, else the first by name."""
    a = img.convert('RGBA')
    px = a.load()
    cols = {px[x, y][:3] for y in range(a.height) for x in range(a.width) if px[x, y][3] == 255}
    sure, shared = set(), []
    for c in cols:
        fams = {f for f in _REV.get(c, set()) if f not in _GLOW}
        if len(fams) == 1:
            sure |= fams
        elif fams:
            shared.append(fams)
    for fams in shared:
        if not fams & sure:
            sure.add(sorted(fams)[0])
    return sorted(sure)


def half_alpha(img2):
    """2x alpha downscaled by 2: a texel is solid when at least 2 of its 4 pixels are."""
    a = img2.convert('RGBA').getchannel('A').load()
    w, h = img2.size
    out = set()
    for y in range(0, h - 1, 2):
        for x in range(0, w - 1, 2):
            n = sum(1 for dx in (0, 1) for dy in (0, 1) if a[x + dx, y + dy] == 255)
            if n >= 2:
                out.add((x // 2, y // 2))
    return out


def iou(img1, img2) -> float:
    a1 = img1.getchannel('A').load()
    m1 = {(x, y) for y in range(img1.height) for x in range(img1.width) if a1[x, y] == 255}
    dx, dy = FOOT[0] - FOOT_2X[0] // 2, FOOT[1] - FOOT_2X[1] // 2
    m2 = {(x + dx, y + dy) for (x, y) in half_alpha(img2)}
    return len(m1 & m2) / max(1, len(m1 | m2))


def on_grass(im, scale):
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    tile = Image.new('RGB', big.size, sk.GRASS)
    tile.paste(big, (0, 0), big)
    return tile


def sheet(results):
    pad = 16
    f_t, f_b = sk._font(18), sk._font(12)
    tiles = []
    for v, im1, im2, r in results:
        tiles.append((v, on_grass(im1, 8), on_grass(im2, 4), on_grass(im1, 2), on_grass(im2, 1), r))
    col = max(t[1].width + t[2].width for t in tiles) + 3 * pad
    W = pad + col * len(tiles)
    th = max(t[1].height for t in tiles)
    gh = max(t[3].height for t in tiles)
    lines = [ln for s in SIMPLIFIED for ln in textwrap.wrap('- ' + s, 150, subsequent_indent='  ')]
    H = 50 + th + 22 + gh + 40 + 16 * (len(lines) + 2) + pad
    out = Image.new('RGB', (W, H), sk.PAPER)
    d = ImageDraw.Draw(out)
    d.text((pad, 14), f'{ID}: 1x master (8x) beside the 2x final (4x); game scale below',
           fill=sk.TEXT, font=f_t)
    x = pad
    for v, a, b, ga, gb, r in tiles:
        out.paste(a, (x, 50))
        out.paste(b, (x + a.width + pad, 50))
        y = 50 + th + 4
        d.text((x, y), f"{v}  IoU {r['iou']:.3f}  families {'=' if r['families_match'] else '!='}  "
               f"lone {100 * r['measure']['isolated']:.1f}%", fill=sk.TEXT, font=f_b)
        y += 18
        out.paste(ga, (x, y))
        out.paste(gb, (x + ga.width + pad, y))
        x += col
    y = 50 + th + 22 + gh + 12
    d.text((pad, y), 'Simplified at 1x:', fill=sk.TEXT, font=f_b)
    for ln in lines:
        y += 16
        d.text((pad + 12, y), ln, fill=sk.TEXT, font=f_b)
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    out.save(OUT_PNG)


def main():
    os.makedirs(VIEWS_DIR, exist_ok=True)
    results, views = [], {}
    for v, rows in VIEWS.items():
        im1 = draw(rows).image()
        im1.save(os.path.join(VIEWS_DIR, f'master-{v}.png'))
        im2 = Image.open(os.path.join(VIEWS_DIR, f'final-{v}.png')).convert('RGBA')
        f1, f2 = families(im1), families(im2)
        m = sk.measure(im1)
        r = {'iou': round(iou(im1, im2), 4), 'families_1x': f1, 'families_2x': f2,
             'families_match': f1 == f2, 'measure': {k: (round(val, 4) if isinstance(val, float) else val)
                                                     for k, val in m.items()}}
        views[v] = r
        results.append((v, im1, im2, r))
        print(f"{v}: IoU {r['iou']:.3f}  families {f1} vs {f2}  lone {100 * m['isolated']:.1f}%  "
              f"W-E {m['west_east']:+.1f}  colours {m['colours']}")
    sheet(results)
    with open(OUT_JSON, 'w') as fh:
        json.dump({'id': ID, 'cell': list(CELL), 'foot': list(FOOT), 'views': views,
                   'simplified': SIMPLIFIED, 'notes': NOTES}, fh, indent=1)
        fh.write('\n')


if __name__ == '__main__':
    main()
