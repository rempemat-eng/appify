"""Pack every asset for the action prototype into assets.json (data: URIs + tables)."""
import base64, io, json, os, re, sys
from PIL import Image
# The repository root (for the woodland zone and the fonts) and the character pipeline's out/ folder
# (bramble/, familiars/), which is not in the repository yet. See ../../README.md.
REPO = (os.environ.get('NAPATTACK_REPO') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
CHARART = os.environ.get('NAPATTACK_CHARART', '')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glare as gl
import storm as st
import akit as A
WT = REPO
HERE = os.path.dirname(os.path.abspath(__file__))


def uri(im):
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def down(p, s=4):
    im = Image.open(p).convert('RGBA')
    return im.resize((im.width // s, im.height // s), Image.NEAREST)


out = {}
# ---- zone
out['ground'] = uri(down(WT + '/assets/zones/woodland/ground.png'))
src = open(WT + '/lib/zone-maps.ts').read()
i = src.index('\n  woodland: {\n    objects: [')
end = src.index('\n    ],', i)
objs = [(m.group(1), m.group(2), *map(int, m.groups()[2:])) for m in
        re.finditer(r"\['([^']+)', '([^']+)', (-?\d+), (-?\d+), (\d+), (\d+)", src[i:end])]
props = {}
for (_, kind, x, y, w, h) in objs:
    if kind not in props:
        props[kind] = uri(down(WT + f'/assets/zones/props/{kind}.png'))
out['props'] = props
out['objects'] = [[k, x, y, w, h] for (_, k, x, y, w, h) in objs]
j = src.index('walk: [', i); k = src.index(']', j)
grid = []
for r in re.findall(r"'([^']*)'", src[j:k]):
    grid.append(''.join(c * int(n or 1) for n, c in re.findall(r'(\d*)([.#])', r)))
out['walk'] = grid

# ---- Bramble: 48 x 48 cells
F = CHARART + '/bramble/frames/'
data = json.load(open(CHARART + '/bramble/data.json'))
want = ['idle', 'walk', 'run', 'attack', 'hit', 'faint', 'sleep', 'victory', 'happy']
cells = []
anims = {}
for a in want:
    spec = data['actions'][a]
    for f in spec['facings']:
        n = len(spec['ms'])
        idx = []
        for t in range(n):
            im = Image.open(F + f'{a}_{f}_{t}.png').convert('RGBA')
            if a == 'attack' and t in (4, 5, 6):  # the frame's own arrow hands over to the flying one
                px = im.load()
                for y in range(48):
                    for x in range(48):
                        if (f == 'E' and x >= 34) or (f == 'W' and x <= 13):
                            px[x, y] = (0, 0, 0, 0)
            idx.append(len(cells)); cells.append(im)
        anims[f'{a}_{f}'] = {'f': idx, 'ms': spec['ms'], 'loop': spec['loop']}
cols = 16
atlas = Image.new('RGBA', (48 * cols, 48 * ((len(cells) + cols - 1) // cols)))
for n, im in enumerate(cells):
    atlas.alpha_composite(im, ((n % cols) * 48, (n // cols) * 48))
out['bramble'] = {'atlas': uri(atlas), 'cols': cols, 'cell': 48, 'anchor': data['anchor'], 'anims': anims}
out['portrait'] = uri(Image.open(CHARART + '/bramble/portrait.png').convert('RGBA'))

# ---- Mossling (BLOB): 24 x 24 cells, anchor (12, 22)
M = CHARART + '/familiars/frames/'
mcells, manims = [], {}
for a, n in (('walk', 6), ('curl', 2), ('perch_idle', 4)):
    for f in ('E', 'W'):
        idx = []
        for t in range(n):
            idx.append(len(mcells)); mcells.append(Image.open(M + f'BLOB_{a}_{f}_{t}.png').convert('RGBA'))
        manims[f'{a}_{f}'] = idx
mat = Image.new('RGBA', (24 * len(mcells), 24))
for n, im in enumerate(mcells):
    mat.alpha_composite(im, (n * 24, 0))
out['moss'] = {'atlas': uri(mat), 'cell': 24, 'anims': manims}

# ---- Glares: 17 x 20 cells
gl_frames = {
    'cross0': gl.glare(0), 'cross1': gl.glare(1), 'wind0': gl.glare(0, 'windup'), 'wind1': gl.glare(1, 'windup'),
    'hit': gl.glare(0, flash=0.65), 'calm': gl.glare(0, 'calm'), 'fold': gl.shrink_calm(1),
    'spark0': gl.spark(0), 'spark1': gl.spark(1),
}
def pack(frames, cw, ch):
    names = list(frames)
    at = Image.new('RGBA', (cw * len(names), ch))
    table = {}
    for n, name in enumerate(names):
        im = frames[name]
        x = n * cw + (cw - im.width) // 2
        y = ch - im.height
        at.alpha_composite(im, (x, y))
        table[name] = [n * cw, 0, cw, ch]
    return {'atlas': uri(at), 'frames': table, 'w': cw, 'h': ch}
out['glare'] = pack(gl_frames, 17, 20)
storm_frames = {
    'cross0': st.storm(), 'cross1': st.storm(frame=1), 'wind0': st.storm('windup'), 'wind1': st.storm('windup', 1),
    'hit': st.storm(flash=0.6), 'core0': st.storm('cross', 0, minis=False), 'core1': st.storm('cross', 1, minis=False),
    'corewind': st.storm('windup', 0, minis=False), 'corehit': st.storm(flash=0.6, minis=False),
    'calm': st.storm('calm'), 'fold0': st.fold(0), 'fold1': st.fold(1),
}
out['storm'] = pack(storm_frames, 41, 34)

# ---- signpost (new, for the prototype): a forester's post with a board showing the ring of stones
SIGN = [
    "..oooooooooooo..",
    ".oklllllllllllo.",
    ".olssssssssssLo.",
    ".olsssgggssssLo.",
    ".olssg...gsssLo.",
    ".olsg.....gssLo.",
    ".olsg.....gssLo.",
    ".olssg...gsssLo.",
    ".olsssgggssssLo.",
    ".oLLLLLLLLLLLLo.",
    "..ooooowloooooo.",
    "......owlo......",
    "......owlo......",
    "......owlo......",
    "......owlo......",
    "......owlo......",
    ".....oowloo.....",
    "....ommmmmmo....",
]
SPAL = {'o': '#2A1D16', 'k': '#E2B877', 'l': '#B88552', 'L': '#7C5634', 's': '#E9D3A4', 'g': '#6E7A86',
        'w': '#8F6A3E', 'm': '#4F8D45'}
sg = Image.new('RGBA', (16, len(SIGN)))
for y, r in enumerate(SIGN):
    for x, c in enumerate(r):
        if c in SPAL:
            sg.putpixel((x, y), gl.hexc(SPAL[c]))
out['sign'] = uri(sg)

# ---- icons (16 x 16) for the buttons
def icon(rows):
    im = Image.new('RGBA', (16, 16))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in A.ICON_PAL:
                im.putpixel((x, y), gl.hexc(A.ICON_PAL[c]))
    return uri(im)
out['icons'] = {'bow': icon(A.BOW), 'dodge': icon(A.DODGE), 'pause': icon(A.PAUSE)}

FO = WT + '/node_modules/@expo-google-fonts/pixelify-sans/'
out['fonts'] = {
    'bold': 'data:font/ttf;base64,' + base64.b64encode(open(FO + '700Bold/PixelifySans_700Bold.ttf', 'rb').read()).decode(),
    'medium': 'data:font/ttf;base64,' + base64.b64encode(open(FO + '500Medium/PixelifySans_500Medium.ttf', 'rb').read()).decode(),
}
json.dump(out, open(HERE + '/assets.json', 'w'))
print('assets', os.path.getsize(HERE + '/assets.json') // 1024, 'KB', 'bramble cells', len(cells), 'props', len(props))
# W attack check: body never reaches x <= 13 on the no-arrow frame
im = Image.open(F + 'attack_W_7.png'); print('attack_W_7 bbox', im.getbbox())
