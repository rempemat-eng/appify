import sys; sys.path.insert(0,'.')
from anim_bramble import frames
from ew import to_img, zoom
from PIL import Image
kind=sys.argv[1]; idx=[int(x) for x in sys.argv[2].split(',')]; z=int(sys.argv[3]) if len(sys.argv)>3 else 6
fs,_=frames(kind); ims=[to_img(fs[i].render()).crop((22,18,92,100)) for i in idx]
out=Image.new('RGBA',(70*len(ims),82),(126,159,80,255))
for i,im in enumerate(ims): out.alpha_composite(im,(i*70,0))
zoom(out,z).save('/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/ew/strip.png')
