"""Review helper: python3 look.py <module> [facings] [zoom] [pose-expr] -> scratch/lead/look.png"""
import sys, importlib
from PIL import Image
from ew import to_img, zoom
mod = importlib.import_module(sys.argv[1])
fcs = sys.argv[2] if len(sys.argv) > 2 else 'SNEW'
z = int(sys.argv[3]) if len(sys.argv) > 3 else 5
P = mod.P0(**eval('dict(%s)' % sys.argv[4])) if len(sys.argv) > 4 else None
ims = [to_img(mod.draw(fc, P).render()).crop((20, 0, 140, 144)) for fc in fcs]
w, h = ims[0].size
bg = Image.new('RGBA', (w * len(ims), h), (126, 159, 80, 255))
for i, im in enumerate(ims):
    bg.alpha_composite(im, (w * i, 0))
import numpy as np
a = np.array(bg)[..., :3]
diff = (np.abs(a.astype(int) - [126, 159, 80]).sum(-1) > 0)
ys = np.where(diff.any(1))[0]
bg = bg.crop((0, max(0, ys.min() - 3), bg.width, min(h, ys.max() + 4)))
out = sys.argv[5] if len(sys.argv) > 5 else '/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/lead/look.png'
zoom(bg, z).save(out)
