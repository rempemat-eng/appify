"""Put the embedded art into the page: src/index.src.html + build/assets.json -> index.html.

Without build/assets.json (it is not kept in the repository; tools/build_assets.py writes it), the
embedded art is taken from the current index.html, so src/index.src.html can be edited and rebuilt
without the character pipeline.
"""
import json
import os
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = os.path.join(H, 'index.html')
src = open(os.path.join(H, 'src/index.src.html')).read()
packed = os.path.join(H, 'build/assets.json')
if os.path.exists(packed):
    assets = open(packed).read()
else:
    old = open(page).read()
    i = old.index('const A = ') + len('const A = ')
    _, end = json.JSONDecoder().raw_decode(old, i)
    assets = old[i:end]
out = src.replace('__ASSETS__', assets)
open(page, 'w').write(out)
print('index.html', os.path.getsize(page) // 1024, 'KB')
