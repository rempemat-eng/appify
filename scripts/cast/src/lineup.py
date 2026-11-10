"""review/lineup_all.png: every character module present in src/, idle in S N E W, at 4x, feet on
one ground line per row, with 48 / 74 / 90 px guide lines (bench, average adult, oak scale)."""
import importlib
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ew import to_img

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ['bramble', 'iona', 'pendle', 'cairn', 'morel', 'velvet', 'tam', 'mirra',
         'brine', 'ashe', 'clack', 'nix', 'rook', 'mote']
Z = 4
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
FONT_S = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
BG = (118, 150, 84, 255)


def figure(mod, fc):
    f = mod.draw(fc)
    a = f.render()
    op = a[..., 3] > 0
    ys, xs = np.where(op)
    top = f.gy + 1 - ys.min()           # height above the ground line (incl. outline)
    im = to_img(a).crop((xs.min() - 2, ys.min(), xs.max() + 3, f.gy + 1))
    return im, top


def main(out=None):
    cast = [c for c in ORDER if os.path.exists(os.path.join(ROOT, 'src', c + '.py'))]
    rows = []
    for cid in cast:
        try:
            mod = importlib.import_module(cid)
            figs = [figure(mod, fc) for fc in 'SNEW']
            rows.append((getattr(mod, 'NAME', cid.title()), figs, max(t for _, t in figs)))
        except Exception as e:                      # a designer's module mid-edit should not stop the sheet
            print('skip', cid, e)
    cols = 2
    per = (len(rows) + cols - 1) // cols
    gap = 10 * Z
    colw = max(sum(im.width * Z + gap for im, _ in figs) for _, figs, _ in rows) + 60
    rowh = [max(h for _, _, h in rows[i::per]) for i in range(per)] if False else None
    H_row = max(h for _, _, h in rows) * Z + 70
    W = 40 + cols * colw
    H = 90 + per * H_row
    S = Image.new('RGBA', (W, H), (34, 36, 40, 255))
    d = ImageDraw.Draw(S)
    d.text((40, 24), 'Cast lineup, idle S N E W at 4x.  Guides: 48 px (bench), 74 px (average adult), 90 px.',
           font=FONT, fill=(230, 226, 214))
    for k, (name, figs, h) in enumerate(rows):
        c, r = divmod(k, per)
        x = 40 + c * colw
        y = 90 + r * H_row
        gy = y + H_row - 24
        d.rectangle((x - 10, y + 30, x + colw - 50, gy + 8), fill=BG)
        for g in (48, 74, 90):
            d.line([(x - 10, gy - g * Z), (x + colw - 50, gy - g * Z)], fill=(98, 128, 66, 255), width=1)
            d.text((x + colw - 92, gy - g * Z - 20), str(g), font=FONT_S, fill=(70, 96, 50))
        d.text((x, y + 4), '%s   (%d px)' % (name, max(t for _, t in figs)), font=FONT_S, fill=(236, 230, 210))
        for im, t in figs:
            big = im.resize((im.width * Z, im.height * Z), Image.NEAREST)
            S.alpha_composite(big, (x, gy - big.height))
            x += big.width + gap
    out = out or os.path.join(ROOT, 'review', 'lineup_all.png')
    S.convert('RGB').save(out)
    print(out, S.size, [r[0] for r in rows])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
