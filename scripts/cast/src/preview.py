import sys, numpy as np
from PIL import Image
from ew import to_img, zoom
import importlib
mod = importlib.import_module(sys.argv[1]); facings = sys.argv[2].split(',') if len(sys.argv)>2 else ['S']
out = sys.argv[3] if len(sys.argv)>3 else '/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/ew/prev.png'
ims=[]
for fc in facings:
    a = mod.draw(fc).render(); ims.append(a)
W=sum(a.shape[1] for a in ims); H=ims[0].shape[0]
bg=Image.new('RGBA',(W,H),(126,159,80,255)); x=0
for a in ims: bg.alpha_composite(to_img(a),(x,0)); x+=a.shape[1]
big=zoom(bg,5)
# also 2x actual size strip at the side
small=zoom(bg,2)
canvas=Image.new('RGBA',(big.width, big.height+small.height+10),(40,40,40,255)); canvas.paste(big,(0,0)); canvas.paste(small,(0,big.height+10))
canvas.save(out); print(out)
