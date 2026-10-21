"""Cairn's 1x master (Claude J, 21 Oct): the chosen 2x design (option C, the moss-mantled giant)
redrawn at density 1 as pixel art, never a downscale (Matt, 21 Oct 18:17: the 1x design
is the master and every density draws the same design).

Run from the repo root:
    CHAR_VIEWS=<dir with cairn/final-*.png> python3 scripts/art/characters/masters/cairn.py
Writes docs/vision/characters/masters/cairn-1x.png (1x at 8x beside 2x at 4x, then the
game-scale row) and cairn.json (silhouette IoU against the 2x final, families, measure),
and each 1x view as $CHAR_VIEWS/cairn/master-<view>.png.

Cell folkLarge 40 x 40, foot (20, 37); heightWorld 29.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ID = 'cairn'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
VIEWS_DIR = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), ID)
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}-1x.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/masters', f'{ID}.json')

CELL = (40, 40)
FOOT = (20, 37)
FOOT_2X = (40, 74)

# --- the drawing: one letter a texel, (family, tone) on the house palette ----------------
# Outline comes from Fig.outline() (each material's edge tone, lit break at the top left);
# ('edge', family) letters are drawn edge tones laid after it (a crack, a dark gap).
# Glowflora texels (eyes, the ring groove) are lights: never outlined.
LEGEND = {
    # stone body boulder and arms
    'A': ('stone', 4), 'B': ('stone', 3), 'C': ('stone', 2), 'D': ('stone', 1),
    # stone_warm head
    'W': ('stone_warm', 4), 'w': ('stone_warm', 3), 'x': ('stone_warm', 2), 'X': ('stone_warm', 1),
    # stone_cool capstone and legs
    'S': ('stone_cool', 4), 's': ('stone_cool', 3), 't': ('stone_cool', 2), 'T': ('stone_cool', 1),
    # leaf moss mantle
    'L': ('leaf_warm', 4), 'l': ('leaf', 3), 'm': ('leaf', 2), 'n': ('leaf_cool', 2),
    # grass fern behind his left ear
    'F': ('grass', 4), 'f': ('grass_cool', 3), 'g': ('grass', 2),
    # glowflora lights: eyes and the ring groove
    'O': ('glowflora', 4), 'o': ('glowflora', 3), 'e': ('glowflora', 1),
    'K': ('ink', 0),
    '%': ('edge', 'stone'),
}
X0, Y0 = 6, 7

VIEWS = {
    'S-idle': [
        '.............................',
        '.........SSSSSSSS...F........',
        '........sssssssstt.FF........',
        '..........TTTTTTT.FFfg.......',
        '.........WxxxxxxxFFfFg.......',
        '.........WWoKwwoKxFfgg.......',
        '.........WWWwWXwxx.fg........',
        '.........wwwwWXxxx...........',
        '.......lllwwxxxxllmn.........',
        '....LLLlmLLlmmLLlmmmmnn......',
        '...ABlllmmllmmmlllmmmnnBC....',
        '...ABmmLLlmmLLlmmLLmnnnBC....',
        '...ABmmlllmmllmmmllmnnnBC....',
        '...ABmmmmmmmmmmmmmnnnnnBC....',
        '...ABBm.AAAABBBBBBBC..BCC....',
        '...ABB.AAAAABDDDBBBCC.BCC....',
        '.......AAAABDBBBeBBCC........',
        '....SSt.AAABDBBBeBBC..stt....',
        '...SSst.ABBBDBBBeBCC.ssttT...',
        '...SSst.BBBBBeeeBCCC.ssttT...',
        '...Ssst.BBBBBBBBBCCC.ssttT...',
        '...Ssst.BBCBBBBBCCCC.ssttT...',
        '....ttt.BBCBBBBCCCCD..ttT....',
        '.........CCCCCCCCllD.........',
        '.........Ssst..sstT..........',
        '.........Ssst..sstT..........',
        '.........Ssst..sstT..........',
        '........SSsst..ssstt.........',
        '........Sssst..sssTT.........',
        '.........tttt...ttTT.........',
    ],
    'E-idle': [
        '.............................',
        '...........F..SSSSSS.........',
        '...........FFssssssstt.......',
        '.........FFFg.TTTTTTT........',
        '..........FFgwxxxxxx.........',
        '..........FggWWWWKowx........',
        '...........ggWWWWwwxx........',
        '.........LLmmwwwwwxx.........',
        '.......mLLlmLLlmmxx..........',
        '......mllllmlllmmnn..........',
        '......mmLLlmWWxmmnnn.........',
        '......mmlllmWwxmnnnn.........',
        '......mllmmmWwxnnnnn.........',
        '......mmmmmmWwxBBCtT.........',
        '.......mAAAAWwxBBCtT.........',
        '.......AAAAAWwxBBCtT.........',
        '.......AAAABXXXBBCtT.........',
        '.......BBBBBSstBCCtT.........',
        '.......BBBBBSstBCCtT.........',
        '.......BBBBCSstCCCtT.........',
        '.......BBBBCTTTCCCtT.........',
        '........CCCCsstCCtT..........',
        '........CCCCsstCCtT..........',
        '.........DDDtttDDD...........',
        '...........ttSsst............',
        '...........ttSsst............',
        '...........ttSsst............',
        '............SSssstt..........',
        '...........ssssssttt.........',
        '...........tttttTTT..........',
    ],
    'W-idle': [
        '.............................',
        '........SSSSSS..F............',
        '......sssssssttFF............',
        '.......TTTTTTT.FFFg..........',
        '........wxxxxxxFFg...........',
        '.......WWoKWWwwFgg...........',
        '.......WWWWwwxxgg............',
        '........wwwwwxxmmlm..........',
        '.........wwmLLlmmllmn........',
        '.........LLlllmlllmmmn.......',
        '........LLlmmWWxmlllmn.......',
        '........llmmmWwxmmllmn.......',
        '........mmmmmWwxmmmmnn.......',
        '........WwAAAWwxmmmmnn.......',
        '........WwAAAWwxnBBBn........',
        '........WwAAAWwxBBBCC........',
        '........WwAABXXXBBBCC........',
        '........WwAABSstBBCCC........',
        '........WwAABSstBBCCC........',
        '........WwABBSstBCCCC........',
        '........WwABBTTTBCCCC........',
        '.........WwBBSstCCCC.........',
        '.........WwBBsstCCCC.........',
        '..........DDDtttDDD..........',
        '...........Sssttt............',
        '...........Sssttt............',
        '...........Sssttt............',
        '.........SSssstt.............',
        '........ssssssttt............',
        '.........tttttTTT............',
    ],
}

SIMPLIFIED = [
    'Ring rune: a 5 x 5 ring, stone1 groove on the top and left, glowflora1 light on the right and bottom (S only, as the 2x).',
    'Cracks and lichen: one 2 texel crack and a 2 texel lichen spot (S); E/W keep the slab seams as single dark rows.',
    'Moss mantle: lobes as 2-3 texel leaf_warm4 highlights over leaf3/leaf2, leaf_cool2 on the shaded side; the 2 px drips become one texel.',
    'Fern: a few 2-4 texel grass fronds; the 2x frond veins are dropped.',
    'Eyes: one glowflora3 light beside one ink texel per socket.',
]
NOTES = [
    'Same design as the 2x final (option C): flat stone_cool capstone with its two-row shadow over the glowing eyes, '
    'stone_warm head with nose lump, fern behind his left ear (S viewer right, E behind, W over the back), '
    'moss mantle, broad stone boulder, slab arms with stone_cool hand slabs, pillar legs and boulder feet.',
    'E/W: the near arm hangs as three slabs in front of the body; the front plane is shaded in E and lit (stone_warm) in W, '
    'as the 2x. W is drawn, not mirrored.',
    'Glowflora texels are lights (never outlined) and are left out of the family check, as the brief says.',
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
