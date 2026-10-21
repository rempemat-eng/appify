"""Tam's 1x master (Claude J, 21 Oct): the chosen 2x design (option C, the bothy keeper)
redrawn at density 1 as pixel art, never a downscale (Matt, 21 Oct 18:17: the 1x design
is the master and every density draws the same design).

Run from the repo root:
    CHAR_VIEWS=<dir with tam/final-*.png> python3 scripts/art/characters/masters/tam.py
Writes docs/vision/characters/masters/tam-1x.png (1x at 8x beside 2x at 4x, then the
game-scale row) and tam.json (silhouette IoU against the 2x final, families, measure),
and each 1x view as $CHAR_VIEWS/tam/master-<view>.png.

Cell folk 32 x 36, foot (16, 33); heightWorld 19.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ID = 'tam'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}-1x.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}.json')

CELL = (32, 36)
FOOT = (16, 33)
FOOT_2X = (32, 66)

# --- the drawing: one letter a texel, (family, tone) on the house palette ----------------
# Outline comes from Fig.outline() (each material's edge tone, lit break at the top left);
# ('edge', family) letters are drawn edge tones laid after it (a seam, a dark gap).
LEGEND = {
    # leaf knit: beanie, ear flaps, scarf
    'A': ('leaf', 4), 'B': ('leaf', 3), 'C': ('leaf', 2), 'D': ('leaf', 1),
    # plaster: bobble and muzzle
    'U': ('plaster', 5), 'V': ('plaster', 4), 'v': ('plaster', 3), 'u': ('plaster', 2),
    # path fur, path_warm belly, path_cool legs and paws
    'P': ('path', 4), 'p': ('path', 3), 'q': ('path', 2), 'Q': ('path', 1),
    'R': ('path_warm', 4), 'r': ('path_warm', 3),
    'L': ('path_cool', 4), 'l': ('path_cool', 3), 'j': ('path_cool', 2),
    # plaster_cool felt mat, iron kettle, timber belt
    'M': ('plaster_cool', 4), 'm': ('plaster_cool', 3), 'n': ('plaster_cool', 2),
    'I': ('iron', 4), 'i': ('iron', 3), 'y': ('iron', 2), 'Y': ('iron', 1),
    'T': ('timber', 3), 't': ('timber', 2),
    'K': ('ink', 0),
    '#': ('edge', 'leaf'), '%': ('edge', 'path'),
}
X0, Y0 = 6, 15

VIEWS = {
    'S-idle': [
        '.........VV..........',
        '........vvuu.........',
        '......AABBBBCC.......',
        '.....ABCBCBCBCC......',
        '.....ABCBCBCBCCD.....',
        '.....BCqqqqqqqCD.....',
        '.....BCPKpppKqCD.....',
        '.....BCPKVVvKqCD.....',
        '.....BCPVVKvvqCD.....',
        '.....BCPVvvvvqCD.....',
        '....ppAAABBBBBCpq....',
        '....pqBBBCCCCCCpqLlm.',
        '.mLLpqABCRRRrqppqLlm.',
        '.mLLqqABCRRrrqIIIiiyy',
        '.nnnqqCCCTTIttIiiiyy.',
        '....qqqLLlqLLjiiyyYY.',
        '.......LLl.LLj.yyYY..',
        '.......LL..LL........',
    ],
    'E-idle': [
        '.........VV..........',
        '........vvuu.........',
        '......AABBBBBCC......',
        '.....ABCBCBCBCBC.....',
        '.....ABCBCBCBCBC.....',
        '......DDDDDDDDD......',
        '......ABCPPKqvvvK....',
        '......ABCPPKqvvv.....',
        '......ACCqqqquuu.....',
        '......AABBBBBCC......',
        '.....pCCCCCCC........',
        '...mtPPPPppBCr.......',
        '..mmtPPPPpqBCr.......',
        '.IImqqpppqqCCr.......',
        'IiiiTTTTTttttt.......',
        'Iiyyqqpppqqqq........',
        '.yYY.jjj.LLl.........',
        '.....jjj.Lll.........',
    ],
    'W-idle': [
        '.........VV..........',
        '........vvuu.........',
        '.....AABBBBBCC.......',
        '....ABCBCBCBCBC......',
        '....ABCBCBCBCBC......',
        '.....DDDDDDDDD.......',
        '...KVVVPKpqBCD.......',
        '....VVVPKpqBCD.......',
        '....vvvqqqqBCD.......',
        '.....AABBBBBCC.......',
        '......CCCCCCCC.......',
        '......RRPPppqqqtm....',
        '......RRPPppqqqtmm...',
        '......rrppppqqqIIm...',
        '.....TTTTTttttIiiy...',
        '......ppqqqqqIIiyy...',
        '.......LLl.jjjyyYY...',
        '.......Lll.jjj.......',
    ],
}

SIMPLIFIED = [
    'Knit: the 2x dome ribs and cuff blocks become two rows of 1 px leaf3/leaf2 rib columns; the dark '
    'cuff underside is one leaf1 row.',
    'Eyes: the 2 x 2 eyes with a plaster glint become 1 x 2 ink eyes; the brow is dropped (the cuff '
    'shadow row stands in for it).',
    'Mat: the felt roll and its timber ties become a 2-3 px plaster_cool end disc (S both ends, E/W one); '
    'the ties are dropped.',
    'Kettle: dents and the handle are dropped; the lit sheen is two iron4 texels, the spout one texel.',
    'Belt buckle: one iron texel (S); the belt is a single timber row.',
]
NOTES = [
    'Same design as the 2x final (option C): green knit beanie with bobble and ear flaps, scarf with '
    'its tail on her right chest (S viewer left, E front, hidden in W), kettle at the left hip (S viewer '
    'right, E behind, W in front), mat end at the small of the back.',
    'W is drawn, not mirrored: the light stays upper left; in E the muzzle and front are a tone down, in '
    'W the muzzle is lit and the back is shaded.',
    'Compared with Matt\'s 1x Bramble at 8x: three tones a material plus the edge tone, solid ink eyes, '
    'clusters of 2+ texels (lone texels at most 2%).',
]


# --- shared master harness (same in every masters/<id>.py) -------------------------------
def draw(rows):
    """Fill, then Fig.outline(); legend entries ('edge', fam) are drawn edge tones laid
    after the outline (seams, a dark gap), and glow families are lights (never outlined)."""
    fig = sk.Fig(*CELL)
    post = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            fam, tone = LEGEND[ch]
            if fam == 'edge':
                post.append((X0 + i, Y0 + j, tone))
            elif fam in _GLOW:
                fig.glow(X0 + i, Y0 + j, fam, tone)
            else:
                fig.put(X0 + i, Y0 + j, fam, tone)
    fig.outline()
    for x, y, fam in post:
        fig.px[(x, y)] = ('_edge', fam)
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
    H = 50 + th + 22 + gh + 40 + 16 * (len(SIMPLIFIED) + 2) + pad
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
    for s in SIMPLIFIED:
        y += 16
        d.text((pad + 12, y), '- ' + s[:150], fill=sk.TEXT, font=f_b)
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
