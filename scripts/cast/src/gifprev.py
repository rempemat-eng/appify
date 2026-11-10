import sys; sys.path.insert(0,'.')
from anim_bramble import frames
from ew import to_img, zoom
from PIL import Image
kind=sys.argv[1]
fs,ms=frames(kind)
ims=[]
for i,f in enumerate(fs):
    bg=Image.new('RGBA',(104,104),(126,159,80,255)); bg.alpha_composite(to_img(f.render()))
    ims.append(zoom(bg,4).convert('P',palette=Image.ADAPTIVE))
ims[0].save('/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/ew/%s.gif'%kind,save_all=True,append_images=ims[1:],duration=ms,loop=0)
# also onion-skin: frames side by side large
