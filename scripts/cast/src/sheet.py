"""Quick clip review: python3 sheet.py <char> <clip> [facings] [zoom] -> scratch/lead/sheet.png"""
import sys, importlib
from PIL import Image, ImageDraw
from ew import to_img, zoom
cid, clip = sys.argv[1], sys.argv[2]
fcs = sys.argv[3] if len(sys.argv) > 3 else 'SNEW'
z = int(sys.argv[4]) if len(sys.argv) > 4 else 3
mod = importlib.import_module(cid)
A = importlib.import_module('anim_' + cid)
rows = []
for fc in fcs:
    rows.append([to_img(mod.draw(fc, mod.P0(**P)).render()).crop((15, 20, 145, 144)) for P, _ in A.TABLE[clip]])
w, h = rows[0][0].size
n = len(rows[0])
bg = Image.new('RGBA', (w * n, h * len(rows)), (126, 159, 80, 255))
d = ImageDraw.Draw(bg)
for r, row in enumerate(rows):
    for i, im in enumerate(row):
        bg.alpha_composite(im, (i * w, r * h))
        d.line([(i * w, r * h + 116), (i * w + w, r * h + 116)], fill=(100, 130, 64, 255))
zoom(bg, z).save(sys.argv[5] if len(sys.argv) > 5 else '/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/lead/sheet.png')
