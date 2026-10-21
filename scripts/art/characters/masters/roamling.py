"""Roamling's 1x master (Claude J, NapAttack, 21 Oct): the chosen 2x design drawn at density 1.

Matt's rule (21 Oct 18:17): the 1x design is the master and every density draws the same
design. Roamling is drawn by hand at 1x as a
familiar (16 x 16, foot (8, 14), 12 px) and as the 8 px perch sprite (12 x 12, foot
(6, 11)): a path-furred jerboa with big round grass-lined ears, the three-blade grass
crest, ink eyes, plaster muzzle and belly, a clay nose, long feet and the curled tail
with its grass leaf tuft.
Fill pixels are placed one by one below; the outline is each material's edge tone with
the lit break (sheetkit.Fig.outline). Nothing here is a downscale of the 2x art.

The agreement check: the 2x final view's alpha is reduced by 2 (a texel is solid when at
least 2 of its 4 pixels are), aligned at the foot anchor (the cells are exactly half, so
the anchors coincide), and compared with the 1x alpha (IoU); the house families of both
are compared, glows and ink aside.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/masters/roamling.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
import house_palette as hp  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ID = 'roamling'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}-1x.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}.json')

CELL, FOOT, FOOT2 = (16, 16), (8, 14), (16, 28)        # familiar idle (2x foot (16, 28))
PCELL, PFOOT, PFOOT2 = (12, 12), (6, 11), (12, 22)     # familiarPerch, 8 px (2x foot (12, 22))
GLOWS = {'lamp', 'glowflora', 'neon_pink', 'neon_cyan', 'lava'}
PALETTE = ['path', 'plaster', 'grass', 'clay']

LEGEND = {
    'H': ('path_warm', 4), 'h': ('path', 3), 'j': ('path_cool', 2), 'i': ('path_cool', 1),
    'P': ('plaster_warm', 4), 'p': ('plaster', 3), 'q': ('plaster_cool', 2),
    'G': ('grass_warm', 4), 'g': ('grass_warm', 3), 'f': ('grass_cool', 2),
    'C': ('clay', 3),
    'k': ('ink', 0),
}

# Each view: (row, first column, pixels); '.' leaves a pixel empty.
VIEWS = {
    'S-idle': [
        (2, 3, 'HH...G..hh'),
        (3, 2, 'HggH.GG.hgfh'),
        (4, 2, 'HggHHHHhhgfh'),
        (5, 3, 'HHHHHHhhhh'),
        (6, 4, 'HHkHHkhh'),
        (7, 4, 'HHkHHkhhGG'),
        (8, 4, 'hhPCCPhhgg'),
        (9, 5, 'hPPPPh.j'),
        (10, 6, 'hqqj..j'),
        (11, 5, 'HhPPjj.j'),
        (12, 5, 'Hhppjjjj'),
        (13, 5, 'ii..ii'),
    ],
    'E-idle': [
        (1, 8, 'GG'),
        (2, 7, 'HHhh'),
        (3, 6, 'Hggfh'),
        (4, 6, 'Hgffh'),
        (5, 7, 'HHHHh'),
        (6, 6, 'HHHhkhh'),
        (7, 2, 'GG..HHHhkhCC'),
        (8, 2, 'gg.hhhhjjpp'),
        (9, 3, 'jHHiiiiqq'),
        (10, 3, 'jHHhppq'),
        (11, 3, 'jHhhppq'),
        (12, 3, 'jhhhppq'),
        (13, 5, 'PPpqq'),
    ],
    'W-idle': [
        (1, 6, 'GG'),
        (2, 5, 'HHhh'),
        (3, 5, 'Hggfh'),
        (4, 5, 'Hgffh'),
        (5, 4, 'HHHHHh'),
        (6, 3, 'HHkHHhh'),
        (7, 2, 'CCHkHHhh..GG'),
        (8, 3, 'PPhhhhjj.gg'),
        (9, 4, 'ppiiiiHHj'),
        (10, 6, 'ppphHHj'),
        (11, 6, 'ppphhHj'),
        (12, 6, 'ppphhhj'),
        (13, 6, 'PPPpp'),
    ],
    'E-perch': [
        (3, 4, 'HGGh'),
        (4, 4, 'Hggh'),
        (5, 4, 'HHHk'),
        (6, 1, 'GG.HHHkCC'),
        (7, 1, 'gg.hhiipp'),
        (8, 2, 'j.HHpp'),
        (9, 2, 'jjHHpp'),
        (10, 3, 'hhPPp'),
    ],
    'W-perch': [
        (3, 4, 'HGGh'),
        (4, 4, 'Hggh'),
        (5, 4, 'kHHh'),
        (6, 2, 'CCkHHh.gg'),
        (7, 2, 'PPiiHh.ff'),
        (8, 4, 'PPHh.j'),
        (9, 4, 'ppHhjj'),
        (10, 4, 'PPPhh'),
    ],
}

SIMPLIFIED = [
    'Eyes: the 3 x 3 ink eye with a 2 px glint is a 1 x 2 ink eye at 1x (no glint).',
    'Crest: the three grass blades are a 3 px tuft (S) or a 2 px pair (E, W); on the 8 px perch the crest is the bright green row on the ear top.',
    'Tail: the 2 px stem is 1 px and the two tip leaves a 2 x 2 tuft (lit over shade); in E and W the stem lies against the back (the 2x gap does not survive).',
    'Forepaws and cheek tufts merge into the plaster chest and the head outline.',
    'Ear lining is 2 x 2 (S, E, W) and 2 x 1 on the perch.',
]
NOTES = [
    'The W perch tuft is drawn a tone down (grass_warm 3 over grass_cool 2): it sits behind the body on the shaded side, which keeps W minus E positive.',
    'Families compared without ink; a colour two ramps share goes to the family the design names.',
]


# --- shared master machinery (the same in every masters/<id>.py) -----------------------
def pick(pool):
    """Deterministic tie-break: the most common, ties broken by sorted string order."""
    return max(sorted(set(pool), key=str), key=pool.count)


def draw(rows, cell, legend):
    fig = sk.Fig(*cell)
    for y, x0, run in rows:
        for i, ch in enumerate(run):
            if ch == '.':
                continue
            spec = legend[ch]
            if spec[0] == 'glow':
                fig.glow(x0 + i, y, spec[1], spec[2])
            else:
                fig.put(x0 + i, y, spec[0], spec[1])
    fig.outline()
    return fig.image()


_PAL = hp.load()
_CANDS: dict = {}
for _n, _r in _PAL['ramps'].items():
    for _i, _c in enumerate(_r):
        _CANDS.setdefault(hp.hex_rgb(_c), []).append(_n)
for _n, _c in _PAL['edges'].items():
    _CANDS.setdefault(hp.hex_rgb(_c), []).append(_n)


def families(img, prefer):
    """House families of an image's opaque pixels, glows and ink aside. A colour two ramps
    share goes to the family the design names (prefer), else by the tie-break."""
    out = set()
    ink = hp.hex_rgb(_PAL['ink'])
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if a < 255 or (r, g, b) == ink:
                continue
            names = _CANDS.get((r, g, b))
            if not names:
                out.add('off-palette')
                continue
            fams = [hp.family(n) for n in names]
            liked = [f for f in fams if f in prefer]
            out.add(pick(liked) if liked else pick(fams))
    return sorted(out - GLOWS)


def half_alpha(img):
    w, h = img.width // 2, img.height // 2
    a = img.getchannel('A').load()
    return {(x, y) for y in range(h) for x in range(w)
            if sum(a[2 * x + i, 2 * y + j] == 255 for i in (0, 1) for j in (0, 1)) >= 2}


def alpha(img):
    a = img.getchannel('A').load()
    return {(x, y) for y in range(img.height) for x in range(img.width) if a[x, y] == 255}


def iou(img1, img2, foot1, foot2):
    m2 = half_alpha(img2)
    dx, dy = foot1[0] - foot2[0] // 2, foot1[1] - foot2[1] // 2
    m2 = {(x + dx, y + dy) for x, y in m2}
    m1 = alpha(img1)
    return len(m1 & m2) / max(1, len(m1 | m2))


def check(views, cells, prefer):
    """views: {view: (cell, foot)} -> per-view results, images."""
    res, ims = {}, {}
    for view, rows in views.items():
        cell, foot, foot2 = cells[view]
        im1 = draw(rows, cell, LEGEND)
        im2 = Image.open(os.path.join(VIEWS_DIR, f'final-{view}.png')).convert('RGBA')
        m = sk.measure(im1)
        f1, f2 = families(im1, prefer), families(im2, prefer)
        res[view] = {
            'iou': round(iou(im1, im2, foot, foot2), 4),
            'families_1x': f1, 'families_2x': f2, 'families_match': f1 == f2,
            'measure': {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()},
        }
        ims[view] = (im1, im2)
    return res, ims


def sheet(title, ims, res, out_path):
    big, pad = 8, 14
    f_title, f_body = sk._font(18), sk._font(12)
    tile_w = max(im1.width * big for im1, _ in ims.values())
    tile_h = max(im1.height * big for im1, _ in ims.values())
    col_w = 2 * tile_w + pad
    game_h = max(im1.height * 2 for im1, _ in ims.values())
    W = pad + len(ims) * (col_w + 2 * pad)
    H = 44 + tile_h + 26 + game_h + 44
    out = Image.new('RGB', (W, H), sk.PAPER)
    d = ImageDraw.Draw(out)
    d.text((pad, 12), title, fill=sk.TEXT, font=f_title)

    def put(im, s, x, y):
        g = im.resize((im.width * s, im.height * s), Image.NEAREST)
        tile = Image.new('RGB', g.size, sk.GRASS)
        tile.paste(g, (0, 0), g)
        out.paste(tile, (x, y))
        return g.width

    for i, (view, (im1, im2)) in enumerate(ims.items()):
        x0, y = pad + i * (col_w + 2 * pad), 44
        put(im1, big, x0, y)
        put(im2, big // 2, x0 + tile_w + pad, y)
        r = res[view]
        d.text((x0, y + tile_h + 4),
               f"{view}  IoU {r['iou']:.2f}  families {'match' if r['families_match'] else 'DIFFER'}  "
               f"lone {100 * r['measure'].get('isolated', 0):.1f}%", fill=sk.TEXT, font=f_body)
        gy = y + tile_h + 24
        w = put(im1, 2, x0, gy)
        put(im2, 1, x0 + w + 8, gy)
    d.text((pad, H - 22), 'Each view: 1x at 8x | 2x final at 4x (same size). Below: game scale, '
           '1x at 2 px a texel | 2x at 1 px a texel, on house grass.', fill=sk.TEXT, font=f_body)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.save(out_path)


def main():
    cells = {v: ((PCELL, PFOOT, PFOOT2) if 'perch' in v else (CELL, FOOT, FOOT2)) for v in VIEWS}
    prefer = set(PALETTE)
    res, ims = check(VIEWS, cells, prefer)
    os.makedirs(VIEWS_DIR, exist_ok=True)
    for view, (im1, _) in ims.items():
        im1.save(os.path.join(VIEWS_DIR, f'master-{view}.png'))
    sheet(f'{ID}: 1x master beside the 2x final (idle 12 px, perch 8 px)', ims, res, OUT_PNG)
    data = {'id': ID, 'cell': list(CELL), 'foot': list(FOOT), 'perch_cell': list(PCELL),
            'perch_foot': list(PFOOT), 'views': res, 'simplified': SIMPLIFIED, 'notes': NOTES}
    with open(OUT_JSON, 'w') as f:
        json.dump(data, f, indent=1)
        f.write('\n')
    for view, r in res.items():
        print(f"{ID} {view}: IoU {r['iou']:.3f} families {'ok' if r['families_match'] else r['families_1x'] + ['vs'] + r['families_2x']} "
              f"lone {100 * r['measure'].get('isolated', 0):.1f}% W-E {r['measure'].get('west_east', 0):+.1f}")


if __name__ == '__main__':
    main()
