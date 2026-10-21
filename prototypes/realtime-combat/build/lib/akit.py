"""Shared kit for the real-time fight mocks: the woodland at fight zoom with Bramble's
production frames, Glares, ground telegraphs, and the floating controls.

Device scale S = 3 (a 402 x 874 phone saved at 3x). The world is drawn at K = 6 device px per
art px (2 CSS px: one whole step in from the walk's 4), so every art pixel stays crisp."""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fightkit as fk  # noqa: E402
import glare as gl  # noqa: E402
import zone_render  # noqa: E402

CHARART = os.environ.get('NAPATTACK_CHARART', '')  # the character pipeline's out/ folder
FRAMES = os.path.join(CHARART, 'bramble/frames')
OUT = os.path.dirname(HERE)
S = fk.S
U = fk.U
W, H = 402 * S, 874 * S
K = 6
hexc = fk.hexc
INK, BUTTON_INK, OUTLINE = fk.INK, fk.BUTTON_INK, fk.OUTLINE


def css(v):
    return int(round(v * S))


# ----------------------------------------------------------------------------- sprites

_cache = {}


def bramble(action, facing, i):
    key = (action, facing, i)
    if key not in _cache:
        _cache[key] = Image.open(os.path.join(FRAMES, f'{action}_{facing}_{i}.png')).convert('RGBA')
    return _cache[key]


MINI = """
...ooooo...
..oRRwRRo..
.oRwRRRRwo.
.oDDDDDDDo.
..oLLGGGo..
.oLGeGeGGo.
.oGGpGGGdo.
.oGGGGGddo.
..oddddoo..
...ooooo...
"""
MINI_PAL = {'o': '#1E1B22', 'R': '#CC5A47', 'w': '#FFF4E0', 'D': '#73272A', 'L': '#C4E59B',
            'G': '#86C46C', 'g': '#57A055', 'd': '#3B7A46', 'e': '#2A2A2E', 'p': '#F09A8C'}


def mossling():
    rows = MINI.strip('\n').split('\n')
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in MINI_PAL:
                im.putpixel((x, y), hexc(MINI_PAL[ch]))
    return im


MOSS = mossling()


def alpha(im, a):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, al = px[x, y]
            if al:
                px[x, y] = (r, g, b, int(al * a))
    return out


def desat(im, amount=0.6, tint=(0x9F, 0x8C, 0xD3), tint_amount=0.18):
    """The held-breath look for plan mode: colours drained towards grey and a nap-violet wash."""
    out = im.convert('RGBA').copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            l = int(0.3 * r + 0.59 * g + 0.11 * b)
            r, g, b = (int(c + (l - c) * amount) for c in (r, g, b))
            r, g, b = (int(c + (t - c) * tint_amount) for c, t in zip((r, g, b), tint))
            px[x, y] = (r, g, b, a)
    return out


# ----------------------------------------------------------------------------- the world


class Scene:
    """A zone at 1x with ground decals, sprites in painter's order by foot y, and overlays."""

    def __init__(self, zone, freeze=False):
        self.zone = zone
        self.freeze = freeze
        g, objs = zone_render.render(zone, with_top=False)
        self.ground = zone_render.down(os.path.join(zone_render.WT, f'assets/zones/{zone}/ground.png'))
        self.objs = objs
        self.decals = []  # callables(img) on the zone-size ground, before sprites
        self.items = []  # (foot_y, image, x, y)
        self.overlays = []  # callables(img) on the zone canvas, after sprites

    def add(self, im, x, y, foot=None):
        """Paste im with its top-left at (x, y); foot is its painter's-order y."""
        self.items.append((foot if foot is not None else y + im.height, im, int(x), int(y)))

    def add_frame(self, im, ax, ay, anchor=(24, 44), foot=None):
        self.add(im, ax - anchor[0], ay - anchor[1], foot if foot is not None else ay)

    def render(self, view):
        x0, y0, w, h = view
        H0 = self.ground.height
        canvas = Image.new('RGBA', (self.ground.width, H0 + 120), (0, 0, 0, 0))
        ground = desat(self.ground) if self.freeze else self.ground
        canvas.alpha_composite(ground, (0, 0))
        fill = ground.crop((0, H0 - 60, self.ground.width, H0))
        for k in range(3):
            canvas.alpha_composite(fill, (0, H0 + 60 * k - 0))
        for fx in self.decals:
            fx(canvas)
        items = list(self.items)
        for (oid, kind, x, y, ow, oh) in self.objs:
            p = os.path.join(zone_render.WT, f'assets/zones/props/{kind}.png')
            if os.path.exists(p):
                items.append((y + oh, _prop(p, self.freeze), x, y))
        items.sort(key=lambda t: t[0])
        for _, im, x, y in items:
            canvas.paste(im, (x, y), im) if (x < 0 or y < 0) else canvas.alpha_composite(im, (x, y))
            if x < 0 or y < 0:
                pass
        for fx in self.overlays:
            fx(canvas)
        return canvas.crop((x0, y0, x0 + w, y0 + h))


_props = {}


def _prop(p, freeze=False):
    if (p, freeze) not in _props:
        im = zone_render.down(p)
        _props[(p, freeze)] = desat(im) if freeze else im
    return _props[(p, freeze)]


def to_screen(art, k=K):
    img = art.resize((art.width * k, art.height * k), Image.NEAREST)
    return img.crop((0, 0, W, H)).convert('RGBA')


def scr(view, x, y, k=K):
    """Zone art px to device px on screen."""
    return (x - view[0]) * k, (y - view[1]) * k


# ----------------------------------------------------------------------------- world art: glares, telegraphs


def glare_shadow(cx, foot, warm=False, light=True):
    """A Glare floats: a small shadow on the ground and the cold light it throws round it."""
    def draw(img):
        px = img.load()
        col = (0xFF, 0xE9, 0xA8) if warm else (0xC9, 0xF0, 0xFF)
        if light:
            for yy in range(-9, 10):
                for xx in range(-17, 18):
                    d = (xx / 17) ** 2 + (yy / 9) ** 2
                    if d <= 1 and (xx + yy) % 2 == 0:
                        X, Y = cx + xx, foot + yy
                        if 0 <= X < img.width and 0 <= Y < img.height:
                            r, g, b, a = px[X, Y]
                            k = 0.32 * (1 - d)
                            px[X, Y] = (int(r + (col[0] - r) * k), int(g + (col[1] - g) * k), int(b + (col[2] - b) * k), a)
        for yy in range(-1, 2):
            for xx in range(-5, 6):
                if (xx / 5.5) ** 2 + (yy / 1.6) ** 2 <= 1:
                    X, Y = cx + xx, foot + yy
                    r, g, b, a = px[X, Y]
                    px[X, Y] = (int(r * 0.62), int(g * 0.66), int(b * 0.7), a)
    return draw


def add_glare(sc, cx, foot, frame=0, mood='cross', flash=0.0, hover=7, im=None):
    g = im or gl.glare(frame, mood, flash)
    sc.decals.append(glare_shadow(cx, foot, warm=(mood == 'calm')))
    sc.add(g, cx - g.width // 2, foot - hover - g.height, foot)
    return (cx, foot - hover - g.height)  # head point


def bramble_shadow(cx, foot):
    def draw(img):
        px = img.load()
        for yy in range(-1, 2):
            for xx in range(-7, 8):
                if (xx / 7.5) ** 2 + (yy / 1.8) ** 2 <= 1:
                    r, g, b, a = px[cx + xx, foot + yy]
                    px[cx + xx, foot + yy] = (int(r * 0.7), int(g * 0.74), int(b * 0.72), a)
    return draw


def add_bramble(sc, cx, foot, action='idle', facing='E', i=0, moss=True, a=1.0, shadow=True):
    im = bramble(action, facing, i)
    if a < 1:
        im = alpha(im, a)
    if shadow:
        sc.decals.append(bramble_shadow(cx, foot))
    sc.add_frame(im, cx, foot)
    if moss:
        # the familiar rides on the back shoulder (cast.md): for an east-facing pose, the west one
        m = MOSS if a >= 1 else alpha(MOSS, a)
        dx = -10 if facing == 'E' else 0
        bob = {('attack', 2): 1, ('attack', 3): 1, ('run', 2): -1, ('run', 5): -1}.get((action, i), 0)
        sc.add(m, cx + dx - 5, foot - 22 + bob, foot + 0.5)
    return (cx, foot - 24)


def lane(x0, y0, x1, y1, width=11, charge=0.6, col=(0xDD, 0xF3, 0xFD)):
    """The FLASH telegraph: a lane of pale screen light on the ground, filling from the Glare
    towards its end as the wind-up runs (charge 0..1). Dashed rim, chevrons along it."""
    def draw(img):
        px = img.load()
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        xs = [x0, x1]
        ys = [y0, y1]
        bx0, bx1 = int(min(xs) - width), int(max(xs) + width)
        by0, by1 = int(min(ys) - width), int(max(ys) + width)
        rim = (0x3B, 0x7C, 0xC2)
        for Y in range(by0, by1 + 1):
            for X in range(bx0, bx1 + 1):
                if not (0 <= X < img.width and 0 <= Y < img.height):
                    continue
                t = (X - x0) * ux + (Y - y0) * uy
                d = (X - x0) * nx + (Y - y0) * ny
                if t < 0 or t > L or abs(d) > width / 2:
                    continue
                r, g, b, a = px[X, Y]
                edge = abs(d) > width / 2 - 1.1 or t > L - 1.1
                if edge:
                    if int(t) // 3 % 2 == 0 or t > L - 1.1:
                        px[X, Y] = rim + (255,)
                    continue
                k = 0.55 if t <= L * charge else 0.2
                # chevrons pointing along the lane
                ch = (t - abs(d) * 0.9) % 9
                if 0 <= ch < 1.6 and t <= L * charge:
                    k = 0.9
                px[X, Y] = (int(r + (col[0] - r) * k), int(g + (col[1] - g) * k), int(b + (col[2] - b) * k), a)
    return draw


def ring(cx, cy, r, inner=None, col=(0xDD, 0xF3, 0xFD)):
    """The PING telegraph: a dotted ring on the ground where a Glare's ping will land, with an
    inner ring closing in (when it meets the rim, it pops)."""
    def draw(img):
        px = img.load()
        rim = (0x3B, 0x7C, 0xC2)
        for Y in range(cy - r - 2, cy + r + 3):
            for X in range(cx - r - 2, cx + r + 3):
                e = math.hypot((X - cx), (Y - cy) * 2)  # flattened: on the ground
                pr, pg, pb, pa = px[X, Y]
                if abs(e - r) < 0.9:
                    ang = math.atan2((Y - cy) * 2, X - cx)
                    if int((ang + math.pi) / (2 * math.pi) * 28) % 2 == 0:
                        px[X, Y] = rim + (255,)
                elif e < r - 0.9:
                    k = 0.22
                    if inner and abs(e - inner) < 0.9:
                        k = 0.85
                    px[X, Y] = (int(pr + (col[0] - pr) * k), int(pg + (col[1] - pg) * k), int(pb + (col[2] - pb) * k), pa)
    return draw


def arrow(x, y, length=8, trail=True):
    """Bramble's blunt hush-arrow in flight, eastward (1x): shaft, a felt tip, blue fletching."""
    def draw(img):
        d = ImageDraw.Draw(img)
        for k in range(-length, 2):
            d.point((x + k, y), fill=hexc('#8F6A2A'))
            d.point((x + k, y + 1), fill=OUTLINE)
        d.point((x + 2, y), fill=hexc('#F3E6C8'))
        d.point((x + 3, y), fill=hexc('#DCC9A2'))
        d.point((x + 2, y - 1), fill=OUTLINE)
        d.point((x + 3, y - 1), fill=OUTLINE)
        d.point((x + 4, y), fill=OUTLINE)
        d.point((x + 2, y + 1), fill=OUTLINE)
        d.point((x + 3, y + 1), fill=OUTLINE)
        for k in (-length, -length + 1):
            d.point((x + k, y - 1), fill=hexc('#86AAD0'))
            d.point((x + k, y + 2), fill=hexc('#5D86B6'))
        if trail:
            for k in range(3, 14, 3):
                d.point((x - length - k, y), fill=hexc('#FFFDF5', 170 - k * 10))
    return draw


def arrow_line(x0, y0, x1, y1, col='#FFFDF5'):
    """A thin streak (1x) for the long shot's path."""
    def draw(img):
        d = ImageDraw.Draw(img)
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for k in range(n):
            X = round(x0 + (x1 - x0) * k / n)
            Y = round(y0 + (y1 - y0) * k / n)
            if k % 4 != 3:
                d.point((X, Y), fill=hexc(col, 220))
    return draw


def spark_fx(cx, cy, size=1):
    f = fk.spark(cx, cy, size)
    return lambda img: f(img, 0, 0)


def motes(cx, cy, n=5, warm=True, spread=10, seed=3):
    """Little drifting light motes (1 px): the Glare's flicker, or the calmed spark's trail."""
    import random
    rnd = random.Random(seed)
    cols = ['#FFF0C2', '#F8DD8F', '#E6BC5C'] if warm else ['#F6FCFF', '#A9E2F6', '#62BCE6']

    def draw(img):
        for k in range(n):
            X = cx + rnd.randint(-spread, spread)
            Y = cy + rnd.randint(-spread, spread // 2)
            img.putpixel((X, Y), hexc(cols[k % 3]))
    return draw


# ----------------------------------------------------------------------------- interface (device px)


def tag_and_caption(img, n, title, caption):
    fk.frame(img, css(8), css(10), css(386), css(44), 'danger', depth=0)
    fk.text(img, css(18), css(16), f'MOCK {n}' + (f' · {title}' if title else ''), 'bold', 11, hexc('#FFF7E2'))
    fk.text(img, css(18), css(33), caption, 'medium', 9.5, hexc('#FFE9DC'))


def hud(img, hp=64, hpmax=80, dust=128, left='2:14', y=62):
    """Today's HUD, unchanged in a fight: the folk's portrait and HP, the shield, Dream Dust,
    the play budget and the menu (game-hud.tsx)."""
    fk.frame(img, css(8), css(y), css(386), css(44), 'paper', depth=1)
    port = Image.open(os.path.join(CHARART, 'bramble/portrait.png')).convert('RGBA')
    fk.frame(img, css(13), css(y + 4), css(36), css(36), 'inset', depth=0)
    img.alpha_composite(port.resize((port.width * 3, port.height * 3), Image.NEAREST), (css(15), css(y + 6)))
    fk.text(img, css(56), css(y + 7), 'BRAMBLE', 'bold', 11, BUTTON_INK)
    img.alpha_composite(fk.icon('heart', 2), (css(56), css(y + 24)))
    d = ImageDraw.Draw(img)
    bx0, by0, bx1, by1 = css(70), css(y + 25), css(150), css(y + 33)
    d.rectangle([bx0, by0, bx1, by1], fill=hexc('#796650'))
    d.rectangle([bx0 + 3, by0 + 3, bx1 - 3, by1 - 3], fill=hexc('#E1D2B6'))
    fw = int((bx1 - bx0 - 6) * hp / hpmax)
    d.rectangle([bx0 + 3, by0 + 3, bx0 + 3 + fw, by1 - 3], fill=hexc('#3E7D44'))
    d.rectangle([bx0 + 3, by0 + 3, bx0 + 3 + fw, by0 + 5], fill=hexc('#7FBF6A'))
    fk.text(img, css(155), css(y + 23), f'{hp}', 'bold', 9.5, INK)
    x = css(186)
    for name, label, w in (('shield', '0:30', 64), ('grass', str(dust), 60), ('time', left, 62)):
        fk.frame(img, x, css(y + 7), css(w), css(28), 'parchment', depth=0)
        img.alpha_composite(fk.icon(name, 2), (x + css(6), css(y + 13)))
        fk.text(img, x + css(26), css(y + 13), label, 'bold', 10, BUTTON_INK)
        x += css(w + 3)
    # the menu sits off the right edge in this narrow mock; the real HUD keeps it


def chip(img, x, y, w, label, icon=None, tone='paper', ink=None, h=28, css_size=10):
    fk.frame(img, css(x), css(y), css(w), css(h), tone, depth=0)
    tx = x + 8
    if icon is not None:
        img.alpha_composite(icon, (css(x + 6), css(y + (h - 16) / 2)))
        tx = x + 26
    fk.text(img, css(tx), css(y + (h - css_size * 1.15) / 2), label, 'bold', css_size, ink or BUTTON_INK)


def pixel_icon(rows, pal, k):
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != '.':
                im.putpixel((x, y), hexc(pal[ch]))
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


ICON_PAL = {'o': '#1E1917', 'w': '#8F6A2A', 'l': '#C99A52', 's': '#F3E6C8', 'b': '#86AAD0',
            'B': '#5D86B6', 'g': '#E6BC5C', 'G': '#F8DD8F', 'L': '#6FB35E', 'D': '#3E7D44',
            'm': '#A5D77F', 'r': '#D47A5C', 'k': '#DCC9A2', 'n': '#9F8CD3', 'N': '#4C3F80',
            'W': '#FFFDF5'}

BOW = [
    "................",
    "......oo........",
    ".....olwo.......",
    ".....owsoo......",
    "....olo.s.o.....",
    "....owo..s.o....",
    "...olo...s..o...",
    "..bowooooookkoo.",
    "..BoloooooookkWo",
    "...olo...s..o...",
    "....owo..s.o....",
    "....olo.s.o.....",
    ".....owsoo......",
    ".....olwo.......",
    "......oo........",
    "................",
]
DODGE = [
    "................",
    "................",
    "................",
    "..oooo...oooo...",
    "...oWWo...oWWo..",
    "....oWWo...oWWo.",
    "oooo.oWWo...oWWo",
    "okkko.oWWo...oWW",
    "oooo.oWWo...oWWo",
    "....oWWo...oWWo.",
    "...oWWo...oWWo..",
    "..oooo...oooo...",
    "................",
    "................",
    "................",
    "................",
]
LONGSHOT = [
    "................",
    "............oo..",
    "...........oWWo.",
    "..........oWWo..",
    ".........owoo...",
    "........owo.....",
    ".......owo......",
    "......owo.......",
    ".....owo........",
    "....owo.........",
    "..bowo..........",
    ".bBoo...........",
    ".bBo............",
    "..o.............",
    "................",
    "................",
]
COVER = [
    "................",
    "...oooooooooo...",
    "..oLLLLmmmmmLo..",
    "..oLmmmmLLLLDo..",
    "..oLmLLLLLLLDo..",
    "..oLmLLLLLLDDo..",
    "..oLLLLLLLLDDo..",
    "...oLLLLLLDDo...",
    "...oLLLLLDDDo...",
    "....oLLLDDDo....",
    ".....oLDDDo.....",
    "......oDDo......",
    ".......oo.......",
    "................",
    "................",
    "................",
]
PAUSE = [
    "................",
    "................",
    "...oooo..oooo...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oWko..oWko...",
    "...oooo..oooo...",
    "................",
    "................",
    "................",
    "................",
]


def perimeter_track(img, x, y, w, h, frac, on='#E6BC5C', off='#5E544A', t=None):
    """A cooldown track round a square button (no round corners in this game): a band outside
    the frame filling clockwise from the top middle."""
    t = t or U
    pts = []
    x0, y0, x1, y1 = x - 2 * t, y - 2 * t, x + w + t, y + h + t  # top-left of each cell
    step = t
    cx = (x0 + x1) // 2
    path = []
    path += [(xx, y0) for xx in range(cx, x1, step)]
    path += [(x1, yy) for yy in range(y0, y1, step)]
    path += [(xx, y1) for xx in range(x1, x0, -step)]
    path += [(x0, yy) for yy in range(y1, y0, -step)]
    path += [(xx, y0) for xx in range(x0, cx, step)]
    d = ImageDraw.Draw(img)
    n = len(path)
    for i, (px_, py_) in enumerate(path):
        col = on if i < frac * n else off
        d.rectangle([px_, py_, px_ + t - 1, py_ + t - 1], fill=hexc(col))


def button(img, x, y, w, h, icon, label=None, tone='paper', cooldown=None, ready=False, sub=None,
           veil_text=None, label_css=10):
    """A pixel button in CSS px; cooldown is 0..1 (1 = ready), drawn as a track round it."""
    X, Y, Wd, Ht = css(x), css(y), css(w), css(h)
    if cooldown is not None:
        perimeter_track(img, X, Y, Wd, Ht + U, cooldown, on='#F8DD8F' if cooldown >= 1 else '#E6BC5C')
    fk.frame(img, X, Y, Wd, Ht, tone, depth=1)
    iy = Y + (Ht - icon.height) // 2 - (css(7) if label else 0)
    img.alpha_composite(icon, (X + (Wd - icon.width) // 2, iy))
    if label:
        fk.text(img, X + Wd // 2, Y + Ht - css(label_css + 8), label, 'bold', label_css, BUTTON_INK, anchor='ma')
    if cooldown is not None and cooldown < 1:
        veil = Image.new('RGBA', (Wd - 2 * U, Ht - 2 * U), (40, 34, 30, 120))
        img.alpha_composite(veil, (X + U, Y + U))
        if veil_text:
            fk.text(img, X + Wd // 2, Y + Ht // 2 - css(9), veil_text, 'display', 12, hexc('#FFFDF5'), anchor='ma')
    if sub:
        fk.text(img, X + Wd // 2, Y + Ht + css(8), sub, 'medium', 9, hexc('#FFFDF5'), anchor='ma')


def outlined_text(img, x, y, s, kind='bold', size=10, col='#FFFDF5', anchor='la'):
    d = ImageDraw.Draw(img)
    f = fk.font(kind, size)
    for dx, dy in ((-S, 0), (S, 0), (0, -S), (0, S), (S, S), (-S, -S), (S, -S), (-S, S)):
        d.text((x + dx, y + dy), s, font=f, fill=OUTLINE, anchor=anchor)
    d.text((x, y), s, font=f, fill=hexc(col), anchor=anchor)


def pixel_circle(img, cx, cy, r, col, unit=U, width=1, dashed=False):
    """A stepped circle on the interface's pixel unit (no anti-aliasing)."""
    d = ImageDraw.Draw(img)
    n = int(r / unit)
    for gy in range(-n - 1, n + 2):
        for gx in range(-n - 1, n + 2):
            e = math.hypot(gx, gy)
            if n - width < e <= n:
                if dashed and int((math.atan2(gy, gx) + math.pi) * 6) % 2:
                    continue
                d.rectangle([cx + gx * unit, cy + gy * unit, cx + gx * unit + unit - 1, cy + gy * unit + unit - 1], fill=col)


def thumb_pad(img, cx, cy, kx, ky, label=None):
    """The floating move pad, drawn where the thumb landed: a stepped ring and the knob."""
    pixel_circle(img, cx, cy, css(42), hexc('#1E1917', 150), width=2)
    pixel_circle(img, cx, cy, css(40), hexc('#FFFDF5', 150), width=1)
    pixel_circle(img, kx, ky, css(16), hexc('#1E1917', 220), width=6)
    pixel_circle(img, kx, ky, css(14), hexc('#FBF4E4', 230), width=5)
    pixel_circle(img, kx - U, ky - U, css(8), hexc('#FFFDF5', 230), width=2)
    if label:
        outlined_text(img, cx, cy + css(50), label, 'bold', 9.5, anchor='ma')


def glare_bar(img, cx, top, n, of=3, warm=False, popping=None, preview=0):
    """Over a Glare: how restless it still is, as segments (no numbers, nothing to read fast)."""
    seg, gap = css(10), css(2)
    w = of * seg + (of - 1) * gap + css(8)
    x0 = int(cx - w / 2)
    fk.frame(img, x0, int(top), w, css(16), 'night', depth=0)
    d = ImageDraw.Draw(img)
    for k in range(of):
        sx = x0 + css(4) + k * (seg + gap)
        sy = int(top) + css(4)
        if k < n:
            col, hi = ('#E6BC5C', '#FFF0C2') if warm else ('#62BCE6', '#DDF3FD')
        elif popping is not None and k == popping:
            col, hi = '#FFFDF5', '#FFFDF5'
        elif k >= of - preview:
            col, hi = '#F8DD8F', '#FFFDF5'
        else:
            col, hi = '#2B2F50', '#2B2F50'
        d.rectangle([sx, sy, sx + seg - 1, sy + css(8) - 1], fill=hexc(col))
        d.rectangle([sx, sy, sx + seg - 1, sy + S - 1], fill=hexc(hi))


def aim_pips(img, cx, top, n, of=3, label='AIM'):
    w = css(30 + of * 13)
    x0 = int(cx - w / 2)
    fk.frame(img, x0, int(top), w, css(18), 'parchment', depth=0)
    fk.text(img, x0 + css(6), int(top) + css(3), label, 'bold', 8.5, BUTTON_INK)
    d = ImageDraw.Draw(img)
    for k in range(of):
        sx = x0 + css(27 + k * 13)
        sy = int(top) + css(5)
        d.rectangle([sx, sy, sx + css(9), sy + css(8)], fill=OUTLINE)
        d.rectangle([sx + S, sy + S, sx + css(9) - S, sy + css(8) - S], fill=hexc('#5D86B6' if k < n else '#FBF4E4'))
        if k < n:
            d.rectangle([sx + S, sy + S, sx + css(9) - S, sy + 2 * S], fill=hexc('#86AAD0'))
