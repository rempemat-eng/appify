"""Tally's 1x master (Claude J, 21 Oct): the chosen 2x design (option B, the collar-bell
puffball: black-faced lamb, round berry cardigan, tally stick behind the ear) redrawn at
density 1 as pixel art, never a downscale (Matt, 21 Oct 18:17: the 1x design is the master
and every density draws the same design).

Run from the repo root:
    CHAR_VIEWS=<dir with tally/final-*.png> python3 scripts/art/characters/masters/tally.py
Writes docs/vision/characters/masters/tally-1x.png (1x at 8x beside 2x at 4x, then the
game-scale row) and tally.json (silhouette IoU against the 2x final, families, measure),
and each 1x view as $CHAR_VIEWS/tally/master-<view>.png.

Cell folk 32 x 36, foot (16, 33); heightWorld 20.
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

ID = 'tally'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}-1x.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}.json')

CELL = (32, 36)
FOOT = (16, 33)
FOOT_2X = (32, 66)

# --- the drawing: one letter a texel, (family, tone) on the house palette ----------------
# Outline comes from Fig.outline() (each material's edge tone, lit break at the top left).
LEGEND = {
    'W': ('snow', 5), 'S': ('snow', 4), 's': ('snow', 3), 'z': ('snow', 2),
    'H': ('slate', 4), 'G': ('slate', 3), 'g': ('slate', 2), 'h': ('slate', 1),
    'K': ('ink', 0), 'r': ('berry', 4),
    'B': ('berry', 4), 'b': ('berry', 3), 'c': ('berry', 2), 'C': ('berry', 1),
    'Y': ('brass', 4), 'y': ('brass', 3), 'q': ('brass', 2),
    'T': ('timber', 4), 't': ('timber', 3), 'u': ('timber', 2),
}
X0, Y0 = 8, 13

VIEWS = {
    'S-idle': [
        '.............T..',
        '......WWSWWssT..',
        '.....SSzSSzst...',
        '....SSszSSzzt...',
        '....ssKGGGKzz...',
        '...HHGKGGGKgg...',
        '...HHGGGGGGgg...',
        '......rGGGr.....',
        '......gggg......',
        '....BBbuubcc....',
        '...BBbbYYbbcC...',
        '...BBbYYqqbcC...',
        '...BBYSsszbcC...',
        '..hhBBSSszbcCh..',
        '...CCCSszzCCCh..',
        '.....SSsszz.....',
        '......Sszz......',
        '......G..G......',
        '......G..G......',
        '......h..h......',
    ],
    'E-idle': [
        '......T.........',
        '......TWWs......',
        '.......SSss.....',
        '......SSszz.....',
        '......sGGKg.....',
        '......sGGKg.....',
        '.....HGGGGGg....',
        '.....HGGGrGg....',
        '.......BBbc.....',
        '......BBbbc.....',
        '.....BBbbbY.....',
        '.....BBbbYYq....',
        '....BBBbbbqq....',
        '....BBBhhccc....',
        '.....CCCCCC.....',
        '.....SSsszz.....',
        '......Sszzz.....',
        '......GG........',
        '......hh........',
    ],
    'W-idle': [
        '...........T....',
        '......WWSSST....',
        '......SSsst.....',
        '......SSsst.....',
        '......GKGs......',
        '.....HGKGGg.....',
        '....HHGGGGgg....',
        '....HHrGGGg.....',
        '.....BBbb.......',
        '......BBbc......',
        '.....YyBBcc.....',
        '.....YyBBbc.....',
        '....qqqBBbcc....',
        '....BBBBhhcc....',
        '.....CCCCCC.....',
        '.....SSsszz.....',
        '......Ssszz.....',
        '.......GG.......',
        '.......hh.......',
    ],
}

SIMPLIFIED = [
    'Fleece crown: the 4-6 px curl lobes with lit caps become 2 px snow lobes (tone 5 caps) on '
    'a three-tone crown.',
    'Eyes: the 3 x 2 ink eyes with a glint and a pale lower lid become 1 x 2 ink; the lid is '
    'dropped. Blush and mouth are single texels.',
    'Cardigan: the rib columns become flat berry tones (lit left, shade right) with a dark rib '
    'hem row; the three brass buttons become one (S) or none (E/W, where the band turns away).',
    'Collar bell: a 4 px brass bell on a 2 px timber strap (S); in E/W the strap is hidden '
    'under the chin.',
    'Tally stick: a 1 px timber diagonal with a lit tip; the notches are dropped.',
]
NOTES = [
    'Same design as the 2x final (option B): a round snow crown over a slate face with side '
    'ears, a round berry cardigan open over the fleece belly, the brass collar bell at the '
    'throat, thin slate legs and hooves, the tally stick behind her left ear (screen right in '
    'S, behind the head in E, over the crown in W).',
    'W is drawn, not mirrored: the light stays at the upper left, the stick crosses the crown '
    'instead of reflecting, and the bell leads on the facing side.',
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
