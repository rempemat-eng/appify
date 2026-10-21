"""Inline the packed art and fonts into template.html and write ../index.html.

With build/assets.json (written by build_assets.py) it uses that. Without it (assets.json is not kept
in the repository), it takes the packed art and fonts from the current ../index.html, so the game code
in template.html can be edited and rebuilt without the character pipeline.
"""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(os.path.dirname(H), 'index.html')
packed = os.path.join(H, 'assets.json')
if os.path.exists(packed):
    A = json.load(open(packed))
    fonts = A.pop('fonts')
    bold, medium = fonts['bold'], fonts['medium']
    assets = json.dumps(A, separators=(',', ':'))
else:
    old = open(out).read()
    bold = re.search(r"font-weight: 700; src: url\((data:[^)]+)\)", old).group(1)
    medium = re.search(r"font-weight: 500; src: url\((data:[^)]+)\)", old).group(1)
    i = old.index('const ASSETS = ') + len('const ASSETS = ')
    _, end = json.JSONDecoder().raw_decode(old, i)
    assets = old[i:end]
s = open(H + '/template.html').read()
s = s.replace('/*FONT_BOLD*/', bold).replace('/*FONT_MEDIUM*/', medium)
s = s.replace('/*ASSETS*/', assets)
open(out, 'w').write(s)
print(out, os.path.getsize(out) // 1024, 'KB')
