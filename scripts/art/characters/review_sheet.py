"""One review sheet per batch of folk (Claude J): the chosen design for each, in every
view the rig must serve, and the batch side by side at game scale on house grass.

    python3 scripts/art/characters/review_sheet.py [1 2]      # one sheet per batch
Reads the views each designs/<id>.py saved, and writes
docs/vision/characters/review-batch-<n>.png. Review material only: production frames
come from the shared rig.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from sheetkit import GRASS, PAPER, TEXT, _font  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

BATCHES = {
    1: ['bramble', 'puffcap', 'velvet', 'tally', 'tam', 'puddle'],
    2: ['cairn', 'pendle', 'mirra', 'ashe', 'tuff', 'nix'],
    3: ['bunk', 'mote', 'mossling', 'roamling', 'pebbling'],
}
FAMILIARS = {'mossling', 'roamling', 'pebbling'}
FAMILIAR_VIEWS = ['S-idle', 'E-idle', 'W-idle', 'hop-1', 'hop-2', 'hop-3', 'hop-4', 'S-react', 'S-nap',
                  'E-perch', 'E-cling', 'E-cheer', 'E-special', 'W-perch', 'W-cling', 'W-cheer', 'W-special']


def views_for(cid: str) -> list:
    return FAMILIAR_VIEWS if cid in FAMILIARS else VIEWS
VIEWS = ['S-idle', 'E-idle', 'W-idle', 'S-fidget', 'nap-S', 'E-ready', 'E-strike', 'E-cast', 'E-hit',
         'E-sit', 'E-cheer', 'W-ready', 'W-strike']
DESIGNS = os.path.join(ROOT, 'docs', 'vision', 'characters', 'designs')


def views_dir() -> str:
    return os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views'))


def load(cid: str, view: str) -> Image.Image:
    return Image.open(os.path.join(views_dir(), cid, f'final-{view}.png')).convert('RGBA')


def on_grass(im: Image.Image, scale: int) -> Image.Image:
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    tile = Image.new('RGB', big.size, GRASS)
    tile.paste(big, (0, 0), big)
    return tile


def build(ids, out, title):
    f_t, f_h, f_b = _font(26), _font(16), _font(13)
    scale = 3
    folk = [c for c in ids if c not in FAMILIARS] or ids
    cw = max(load(c, v).width for c in folk for v in views_for(c))
    ch = max(load(c, v).height for c in folk for v in views_for(c))
    cell_w, cell_h = cw * scale, ch * scale
    ncols = max(len(views_for(c)) for c in ids)
    pad = 14
    fam_w = 32 * 6 + 6
    W = pad + max(len(VIEWS) * (cell_w + 6), max((len(views_for(c)) * fam_w for c in ids if c in FAMILIARS), default=0)) + pad
    del ncols
    row_h = 30 + cell_h + 22 + 3 * 17 + pad
    lineup_h = ch * 2 + 70
    H = 70 + lineup_h + len(ids) * row_h + 40
    sheet = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), title, fill=TEXT, font=f_t)
    d.text((pad, 46), 'Density 2 (an adult about 50 art px). Views at 3x on house grass; the lineup at game scale '
           '(2 device px a texel). Stand-in Mossling on the fight perch. Our own art only.', fill=TEXT, font=f_b)
    # lineup at game scale
    y = 70
    d.text((pad, y), 'The batch at game scale, S idle and E ready', fill=TEXT, font=f_h)
    y += 24
    x = pad
    for cid in ids:
        for v in (('S-idle', 'E-perch') if cid in FAMILIARS else ('S-idle', 'E-ready')):
            t = on_grass(load(cid, v), 2)
            sheet.paste(t, (x, y))
            x += t.width + 2
        x += 12
    y += ch * 2 + 40
    for cid in ids:
        meta = json.load(open(os.path.join(DESIGNS, f'{cid}.json')))
        fin = meta.get('final', {})
        name = fin.get('name') or fin.get('option') or ''
        chosen = str(fin.get('chosen', fin.get('option', '')))
        label = name if name.startswith(chosen) else f'{chosen}, {name}'
        d.text((pad, y), f'{cid.capitalize()}: option {label}'.strip(),
               fill=TEXT, font=f_h)
        y += 26
        x = pad
        rs = 6 if cid in FAMILIARS else scale
        step = 32 * 6 if cid in FAMILIARS else cell_w
        for v in views_for(cid):
            im = load(cid, v)
            t = on_grass(im, rs)
            ox = x + (step - t.width) // 2
            sheet.paste(t, (ox, y + cell_h - t.height))
            d.text((x, y + cell_h + 2), v, fill=TEXT, font=f_b)
            x += step + 6
        y += cell_h + 22
        pose = fin.get('pose', '')
        grafts = fin.get('grafts') or fin.get('grafts_applied') or ''
        if isinstance(grafts, list):
            grafts = '; '.join(grafts)
        d.text((pad, y), f'Personality: {pose}'[:230], fill=TEXT, font=f_b)
        y += 17
        d.text((pad, y), f'Grafts: {grafts}'[:230], fill=TEXT, font=f_b)
        y += 17
        pal = fin.get('palette', [])
        d.text((pad, y), 'Palette: ' + ', '.join(p if isinstance(p, str) else str(p) for p in pal)[:200],
               fill=TEXT, font=f_b)
        y += 17 + pad
    sheet = sheet.crop((0, 0, W, y + 10))
    sheet.save(out)
    return sheet


TITLES = {1: 'NapAttack folk, batch 1: the first six (Claude J, 21 Oct)',
          2: 'NapAttack folk, batch 2: nights 7 to 12 (Claude J, 21 Oct)',
          3: 'NapAttack folk and familiars, batch 3: Bunk, Mote and the three Grasslings (Claude J, 21 Oct)'}

if __name__ == '__main__':
    for n in ([int(a) for a in sys.argv[1:]] or sorted(BATCHES)):
        out = os.path.join(ROOT, 'docs', 'vision', 'characters', f'review-batch-{n}.png')
        s = build(BATCHES[n], out, TITLES[n])
        print(out, s.size)
