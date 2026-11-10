"""review/<id>_clips.png: every clip of one character as a row of its exported drawings (one
facing, default E, 3x), with drawing numbers, ms and the release / hold marks.
python3 clipsheet.py <id> [facing]"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import anim

cid = sys.argv[1] if len(sys.argv) > 1 else 'bramble'
fc = sys.argv[2] if len(sys.argv) > 2 else 'E'
od = os.path.join(anim.ROOT, 'out', cid)
man = json.load(open(os.path.join(od, 'manifest.json')))
Z = 3
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
FONTB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
x0, x1, y0, y1 = 22, 138, 34, anim.PIVOT[1] + 4
cw, ch = (x1 - x0) * Z, (y1 - y0) * Z
clips = list(man['clips'])
nmax = max(man['clips'][c]['frame_count'] for c in clips)
lab = 170
W = lab + nmax * (cw + 4)
H = 50 + len(clips) * (ch + 26)
S = Image.new('RGB', (W, H), (36, 38, 42))
d = ImageDraw.Draw(S)
d.text((10, 12), '%s, all clips, facing %s, 3x. Pink marks: release drawing; yellow: guard hold.' % (man['name'], fc),
       font=FONTB, fill=(232, 228, 216))
for r, c in enumerate(clips):
    e = man['clips'][c]
    y = 50 + r * (ch + 26)
    d.text((10, y + ch // 2 - 20), c, font=FONTB, fill=(232, 228, 216))
    d.text((10, y + ch // 2 + 6), '%.2f s%s' % (e['duration'], ' loop' if e['loop'] else ''), font=FONT, fill=(180, 176, 166))
    for i, fr in enumerate(e['facings'][fc]['frames']):
        im = Image.open(os.path.join(od, fr['file'])).convert('RGBA').crop((x0, y0, x1, y1))
        cell = Image.new('RGBA', im.size, (126, 159, 80, 255))
        cell.alpha_composite(im)
        X = lab + i * (cw + 4)
        S.paste(cell.resize((cw, ch), Image.NEAREST).convert('RGB'), (X, y))
        col = (255, 120, 210) if e['release_frame'] == i else ((255, 214, 90) if e.get('hold_frame') == i else (200, 196, 186))
        if col != (200, 196, 186):
            d.rectangle((X, y, X + cw - 1, y + ch - 1), outline=col, width=3)
        d.text((X + 4, y + ch + 3), '%d  %d ms' % (i, round(e['durations'][i] * 1000)), font=FONT, fill=col)
out = os.path.join(anim.ROOT, 'review', '%s_clips%s.png' % (cid, '' if fc == 'E' else '_' + fc))
S.save(out)
print(out, S.size)
