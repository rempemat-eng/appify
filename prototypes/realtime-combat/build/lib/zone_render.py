"""Render a zone at 1x art pixels: ground + objects (painter's order by foot y) + top layer."""
import os, re, sys
from PIL import Image

WT = (os.environ.get('NAPATTACK_REPO') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..')))


def zone_objects(zone):
    src = open(os.path.join(WT, 'lib/zone-maps.ts')).read()
    start = src.index(f'\n  {zone}: {{\n    objects: [')
    end = src.index('\n    ],', start)
    out = []
    for m in re.finditer(r"\['([^']+)', '([^']+)', (-?\d+), (-?\d+), (\d+), (\d+)", src[start:end]):
        out.append((m.group(1), m.group(2), *map(int, m.groups()[2:])))
    return out


def down(path, s=4):
    im = Image.open(path).convert('RGBA')
    return im.resize((im.width // s, im.height // s), Image.NEAREST)


def render(zone, with_top=True):
    g = down(os.path.join(WT, f'assets/zones/{zone}/ground.png'))
    objs = zone_objects(zone)
    objs.sort(key=lambda o: o[3] + o[5])
    for (oid, kind, x, y, w, h) in objs:
        p = os.path.join(WT, f'assets/zones/props/{kind}.png')
        if not os.path.exists(p):
            continue
        im = down(p)
        g.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else g.paste(im, (x, y), im)
    top = os.path.join(WT, f'assets/zones/{zone}/top.png')
    if with_top and os.path.exists(top):
        t = down(top)
        g.alpha_composite(t, (0, 0))
    return g, objs


if __name__ == '__main__':
    for z in sys.argv[1:]:
        im, objs = render(z)
        im.save(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f'look_full_{z}.png'))
        print(z, im.size, len(objs))
