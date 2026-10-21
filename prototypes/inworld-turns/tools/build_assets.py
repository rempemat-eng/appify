"""Build the prototype's embedded art: every picture as a data: URI in assets.json.

Reads the woodland zone (ground, flow, props) from the fights worktree at 1x, Bramble's production
frames, the Mossling familiar frames, and draws the Glare and the Static Storm with the turn mock's
glare.py. Run: python3 -I build_assets.py (writes ../build/assets.json next to this folder).
"""
import base64
import io
import json
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

# The repository root (for the woodland zone, icons and fonts) and the character pipeline's out/ folder
# (bramble/, familiars/), which is not in the repository yet. See ../../README.md.
WT = (os.environ.get('NAPATTACK_REPO') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
CHAR = os.environ.get('NAPATTACK_CHARART', '')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'build')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, TOOLS)
import glare as gl  # noqa: E402


def uri(im):
    b = io.BytesIO()
    im.save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def down(path, s=4):
    im = Image.open(path).convert('RGBA')
    return im.resize((im.width // s, im.height // s), Image.NEAREST)


def hexc(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


assets = {}

# --- the woodland zone ----------------------------------------------------------------------------
ground = down(f'{WT}/assets/zones/woodland/ground.png')
assets['ground'] = uri(ground)
flow = Image.open(f'{WT}/assets/zones/woodland/flow.png').convert('RGBA')
assets['flow'] = uri(flow)
assets['flowRect'] = [3, 0, 317, 315]

src = open(f'{WT}/lib/zone-maps.ts').read()
s = src.index('\n  woodland: {\n    objects: [')
e = src.index('\n    ],', s)
objs = [(m.group(1), m.group(2), *map(int, m.groups()[2:]))
        for m in re.finditer(r"\['([^']+)', '([^']+)', (-?\d+), (-?\d+), (\d+), (\d+)", src[s:e])]
# the arena's markers: a signpost at the fork and two banner poles at the ring's mouth (props
# from other zones, placed for the prototype only)
objs += [
    ('arena-sign', 'signpost', 148, 330, 30, 36),
    ('arena-flag-1', 'banner_pole', 88, 337, 15, 47),
]
kinds = sorted({o[1] for o in objs})
props = {}
for k in kinds:
    p = f'{WT}/assets/zones/props/{k}.png'
    if os.path.exists(p):
        props[k] = uri(down(p))
assets['props'] = props
assets['objects'] = [list(o) for o in objs if o[1] in props]

# the walk grid (4 px cells, 80 x 144), with the water blocked except under the footbridge
w = src.index('walk: [', e)
we = src.index('],', w)
rows = [re.sub(r'(\d+)([.#])', lambda m: m.group(2) * int(m.group(1)), r)
        for r in re.findall(r"'([^']*)'", src[w:we])]
g = ground.load()
water = [[False] * 80 for _ in range(144)]
for cy in range(144):
    for cx in range(80):
        n = 0
        for yy in range(cy * 4, cy * 4 + 4):
            for xx in range(cx * 4, cx * 4 + 4):
                r_, g_, b_, a_ = g[xx, yy]
                if b_ > r_ + 40 and b_ > g_ + 10:
                    n += 1
        water[cy][cx] = n >= 6
BRIDGE = (119, 284, 140, 312)  # x0, y0, x1, y1 in zone px
grid = []
for cy in range(144):
    row = ''
    for cx in range(80):
        x, y = cx * 4 + 2, cy * 4 + 2
        on_bridge = BRIDGE[0] <= x <= BRIDGE[2] and BRIDGE[1] <= y <= BRIDGE[3]
        blocked = rows[cy][cx] == '#' or (water[cy][cx] and not on_bridge)
        row += '#' if blocked else '.'
    grid.append(row)
# the new posts block their foot cells
for (_, kind, x, y, ow, oh) in objs[-2:]:
    for yy in range(y + oh - 4, y + oh):
        for xx in range(x + ow // 2 - 4, x + ow // 2 + 4):
            cy, cx = yy // 4, xx // 4
            grid[cy] = grid[cy][:cx] + '#' + grid[cy][cx + 1:]
assets['walk'] = grid
water_rows = [''.join('w' if water[cy][cx] else '.' for cx in range(80)) for cy in range(144)]
assets['water'] = water_rows
assets['bridge'] = BRIDGE
# a debug picture of the grid
dbg = ground.convert('RGB').copy()
dd = ImageDraw.Draw(dbg, 'RGBA')
for cy in range(144):
    for cx in range(80):
        if grid[cy][cx] == '#':
            dd.rectangle([cx * 4, cy * 4, cx * 4 + 3, cy * 4 + 3], fill=(0, 0, 0, 110))
dbg.resize((640, 1152), Image.NEAREST).save(os.path.join(OUT, 'walk_debug.png'))


# --- Bramble and the Mossling ----------------------------------------------------------------------
def atlas(files, cell):
    """Pack frames in one row-major atlas; returns (image, {name: index})."""
    cols = 16
    rows_ = (len(files) + cols - 1) // cols
    im = Image.new('RGBA', (cols * cell[0], rows_ * cell[1]), (0, 0, 0, 0))
    idx = {}
    for i, (name, f) in enumerate(files):
        fr = f if isinstance(f, Image.Image) else Image.open(f).convert('RGBA')
        im.alpha_composite(fr, ((i % cols) * cell[0], (i // cols) * cell[1]))
        idx[name] = i
    return im, idx


bdata = json.load(open(f'{CHAR}/bramble/data.json'))
files = []
for act, spec in bdata['actions'].items():
    for fc in spec['facings']:
        for n in range(len(spec['ms'])):
            p = f'{CHAR}/bramble/frames/{act}_{fc}_{n}.png'
            if os.path.exists(p):
                files.append((f'{act}_{fc}_{n}', p))
im, idx = atlas(files, (48, 48))
assets['bramble'] = {'img': uri(im), 'idx': idx, 'cell': [48, 48], 'anchor': bdata['anchor'],
                     'actions': {k: v['ms'] for k, v in bdata['actions'].items()}}

ffiles = sorted(f for f in os.listdir(f'{CHAR}/familiars/frames') if f.startswith('BLOB'))
im, idx = atlas([(f[5:-4], f'{CHAR}/familiars/frames/{f}') for f in ffiles], (24, 24))
assets['moss'] = {'img': uri(im), 'idx': idx, 'cell': [24, 24], 'anchor': [12, 22]}

# --- the Glare and the Static Storm (mock art, glare.py) -------------------------------------------
COLD = list(gl.COLD)
WARM = list(gl.WARM)


def lerp_hex(a, b, t):
    ca, cb = hexc(a), hexc(b)
    return '#%02X%02X%02X' % tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


MID = ['#F4FAFF', '#CFE6F2', '#A3C6DD', '#7AA2C2', '#557BA3', '#3B5683']  # dimmer, less saturated blue
STORM = ['#FFFFFF', '#EEE6FF', '#C9B8FF', '#9C86F2', '#6D58CF', '#463494']


def body(tones, **kw):
    gl.COLD[:] = tones
    try:
        return gl.body(calm=False, **kw)
    finally:
        gl.COLD[:] = COLD


def calm_body(**kw):
    return gl.body(calm=True, eyes='closed', **kw)


def flash(im, amount=0.75):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g_, b, a = px[x, y]
            if a:
                px[x, y] = (int(r + (255 - r) * amount), int(g_ + (255 - g_) * amount), int(b + (255 - b) * amount), a)
    return out


def haloed(b, color):
    return gl.halo(b, color)


GF = []  # (name, image 28 x 34)
for i, sw in enumerate((1.0, 0.5, -0.5, -1.0)):
    GF.append((f'cold{i}', haloed(body(COLD, sway=sw), '#A6E2FF')))
GF.append(('coldSquint', haloed(body(COLD, eyes='squint', scale=0.95), '#A6E2FF')))
GF.append(('coldFlash', flash(haloed(body(COLD, eyes='squint', scale=0.95), '#FFFFFF'))))
GF.append(('coldBig', haloed(body(COLD, sway=0.2, scale=1.07), '#DDF5FF')))
for i, sw in enumerate((1.0, -1.0)):
    GF.append((f'mid{i}', haloed(body(MID, sway=sw), '#FFE7B0')))
GF.append(('midSquint', haloed(body(MID, eyes='squint', scale=0.95), '#FFE7B0')))
GF.append(('midBig', haloed(body(MID, sway=0.2, scale=1.07), '#FFF3D0')))
for i, sw in enumerate((1.0, -1.0)):
    GF.append((f'calm{i}', haloed(calm_body(sway=sw, scale=0.9), '#FFD27A')))
# the storm's pieces after it splits: a core and two shards (violet static)
for i, sw in enumerate((1.0, -1.0)):
    GF.append((f'core{i}', haloed(body(STORM, sway=sw), '#C9B8FF')))
GF.append(('coreSquint', haloed(body(STORM, eyes='squint', scale=0.95), '#C9B8FF')))
GF.append(('coreBig', haloed(body(STORM, sway=0.2, scale=1.07), '#EEE6FF')))
for i, sw in enumerate((1.0, -1.0)):
    GF.append((f'shard{i}', haloed(body(STORM, sway=sw, scale=0.78, badge=False), '#C9B8FF')))
GF.append(('shardSquint', haloed(body(STORM, eyes='squint', scale=0.74, badge=False), '#C9B8FF')))
GF.append(('shardBig', haloed(body(STORM, sway=0.2, scale=0.84, badge=False), '#EEE6FF')))
for i, sw in enumerate((1.0, -1.0)):
    GF.append((f'shardCalm{i}', haloed(calm_body(sway=sw, scale=0.74), '#FFD27A')))
# plain bodies (no halo) for the water reflections
for name, b in (('reflCold', body(COLD)), ('reflMid', body(MID)), ('reflCalm', calm_body(scale=0.9)),
                ('reflCore', body(STORM)), ('reflShard', body(STORM, scale=0.78, badge=False))):
    c = Image.new('RGBA', (28, 34), (0, 0, 0, 0))
    c.alpha_composite(b, (2, 2))
    GF.append((name, c))
im, idx = atlas(GF, (28, 34))
assets['glare'] = {'img': uri(im), 'idx': idx, 'cell': [28, 34], 'center': [13, 19]}


# The Static Storm, whole: a knot of three violet glares bound by crackling static (48 x 44)
def knot(seed, eyes='open', big=False, calm=False):
    rnd = random.Random(seed)
    W, H = 52, 46
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sc = 1.07 if big else 1.0
    if calm:
        left = calm_body(sway=1.0, scale=0.8)
        right = calm_body(sway=-1.0, scale=0.8).transpose(Image.FLIP_LEFT_RIGHT)
        mid = calm_body(sway=0.4 * (1 if seed % 2 else -1), scale=0.95)
    else:
        left = body(STORM, sway=1.0 if seed % 2 else 0.6, scale=0.8 * sc, eyes='squint' if eyes == 'squint' else 'open', badge=False)
        right = body(STORM, sway=-1.0 if seed % 2 else -0.6, scale=0.8 * sc, eyes='squint' if eyes == 'squint' else 'open', badge=False).transpose(Image.FLIP_LEFT_RIGHT)
        mid = body(STORM, sway=0.4 * (1 if seed % 2 else -1), scale=1.0 * sc, eyes=eyes)
    im.alpha_composite(left, (4, 12))
    im.alpha_composite(right, (24, 12))
    im.alpha_composite(mid, (14, 2))
    if not calm:
        d = ImageDraw.Draw(im)
        # crackle: jagged static arcs between the three wisps, upper-left lit (white then violet)
        for (x0, y0, x1, y1) in ((12, 30, 26, 22), (26, 22, 40, 30), (14, 36, 38, 36)):
            pts = []
            n = 6
            for k in range(n + 1):
                t = k / n
                pts.append((round(x0 + (x1 - x0) * t + rnd.randint(-1, 1)), round(y0 + (y1 - y0) * t + rnd.randint(-2, 2))))
            for (a, b) in zip(pts, pts[1:]):
                d.line([(a[0], a[1] + 1), (b[0], b[1] + 1)], fill=hexc('#463494'))
                d.line([a, b], fill=hexc('#FFF6C2'))
        for _ in range(5):  # loose static sparks round the knot
            x, y = rnd.randint(2, W - 3), rnd.randint(2, H - 3)
            if im.getpixel((x, y))[3] == 0:
                d.point((x, y), fill=hexc('#FFF6C2'))
    return gl.halo(im, '#FFD27A' if calm else '#C9B8FF')


SF = [(f'knot{i}', knot(i)) for i in range(4)]
SF.append(('knotSquint', knot(7, eyes='squint')))
SF.append(('knotFlash', flash(knot(7, eyes='squint'))))
SF.append(('knotBig', knot(9, big=True)))
SF.append(('knotCalm', knot(3, calm=True)))
plain = Image.new('RGBA', (56, 50), (0, 0, 0, 0))
plain.alpha_composite(knot(0).copy(), (0, 0))
SF.append(('knotRefl', plain))
im, idx = atlas(SF, (56, 50))
assets['storm'] = {'img': uri(im), 'idx': idx, 'cell': [56, 50], 'center': [28, 28]}

# a contact sheet to look at
sheet = Image.new('RGBA', (28 * len(GF), 34 + 50), (70, 110, 70, 255))
for i, (_, f) in enumerate(GF):
    sheet.alpha_composite(f, (28 * i, 0))
for i, (_, f) in enumerate(SF):
    sheet.alpha_composite(f, (56 * i, 34))
sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(OUT, 'foes_sheet.png'))


# --- card illustrations and icons (16 x 16, the mock's and the game's) -----------------------------
sys.path.insert(0, TOOLS)
import sprites  # noqa: E402

cardart = json.load(open(f'{TOOLS}/cardart.json'))


def card_px(id_):
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for p in cardart[id_]:
        im.putpixel((p['x'], p['y']), hexc(p['color']))
    return im


OUTLINE = (0x1E, 0x19, 0x17, 255)


def arrow_art():
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(2, 13):  # a diagonal arrow, shaft lower-left to head upper-right
        d.point((k, 15 - k), fill=hexc('#8F6A2A'))
        d.point((k + 1, 15 - k), fill=OUTLINE)
    for (x, y) in ((12, 2), (13, 2), (13, 3), (12, 3), (11, 2), (13, 4)):
        d.point((x, y), fill=hexc('#C6C4BE'))
    d.point((13, 1), fill=OUTLINE)
    d.point((14, 2), fill=OUTLINE)
    d.point((14, 3), fill=OUTLINE)
    for (x, y) in ((1, 13), (2, 14), (1, 12), (3, 14)):
        d.point((x, y), fill=hexc('#86AAD0'))
    d.point((2, 12), fill=hexc('#5D86B6'))
    return im


def long_shot_art():
    a = arrow_art()
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    im.alpha_composite(a, (0, 0))
    im.alpha_composite(a.transpose(Image.FLIP_LEFT_RIGHT), (0, 0))
    return im


icons = {
    'loose': arrow_art(), 'longshot': long_shot_art(), 'cover': sprites.icon('shield'),
    'stretch': card_px('stretch'),
}
for n in ('close', 'moon', 'energy', 'settings', 'home', 'missions', 'nap', 'arena', 'shop', 'heart', 'eye', 'sun', 'check', 'signpost', 'sprout'):
    icons[n] = sprites.icon(n)
im, idx = atlas(list(icons.items()), (16, 16))
assets['icons'] = {'img': uri(im), 'idx': idx}

# --- fonts ---------------------------------------------------------------------------------------
FONTS = f'{WT}/node_modules/@expo-google-fonts'
for key, path in (('pxBold', 'pixelify-sans/700Bold/PixelifySans_700Bold.ttf'),
                  ('pxMed', 'pixelify-sans/500Medium/PixelifySans_500Medium.ttf'),
                  ('pxDisplay', 'press-start-2p/400Regular/PressStart2P_400Regular.ttf')):
    assets[key] = 'data:font/ttf;base64,' + base64.b64encode(open(os.path.join(FONTS, path), 'rb').read()).decode()

json.dump(assets, open(os.path.join(OUT, 'assets.json'), 'w'))
print('assets.json', os.path.getsize(os.path.join(OUT, 'assets.json')) // 1024, 'KB;',
      len(assets['objects']), 'objects;', len(props), 'prop kinds')
