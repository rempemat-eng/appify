"""python3 squint.py out.png <id> [...]: the back-view squint test (CONTRACT V2.12).  Per character, the S, N
and NE idle heads at 1x, 2x and blurred to a thumbnail: no back view may share the front view's face
layout (a dark band over a coloured patch).  A look test, not a pass/fail check."""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import anim
cids = sys.argv[2:]
out = sys.argv[1]
rows = []
for cid in cids:
    mod = importlib.import_module(cid); A = importlib.import_module('anim_' + cid); anim.add_powered(A)
    ims = []
    for fc in ('S', 'N', 'NE'):
        a = mod.draw(fc, mod.P0(**A.TABLE['idle'][0][0])).render()
        im = Image.fromarray(a)
        bb = im.getbbox()
        top = bb[1]
        crop = im.crop((40, top - 2, 120, top + 48))
        bg = Image.new('RGBA', crop.size, (126, 159, 80, 255)); bg.alpha_composite(crop)
        ims.append(bg)
    rows.append((cid, ims))
W, H = 80, 50
sheet = Image.new('RGBA', (90 + 3 * (W + 2 * W + W * 2 + 30), len(rows) * (2 * H + 10) + 10), (40, 42, 46, 255))
d = ImageDraw.Draw(sheet)
for r, (cid, ims) in enumerate(rows):
    y = 10 + r * (2 * H + 10)
    d.text((6, y + 40), cid, fill=(230, 226, 214))
    x = 90
    for k, im in enumerate(ims):
        sheet.alpha_composite(im, (x, y)); x += W + 4                        # 1x
        sheet.alpha_composite(im.resize((2 * W, 2 * H), Image.NEAREST), (x, y)); x += 2 * W + 4   # 2x
        sq = im.resize((W // 2, H // 2), Image.BOX).filter(ImageFilter.GaussianBlur(1.0)).resize((2 * W, 2 * H), Image.BILINEAR)
        sheet.alpha_composite(sq, (x, y)); x += 2 * W + 22                    # squint
sheet.save(out)
