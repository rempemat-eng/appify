"""Drawing kit for the fight mock and storyboard: the world crop with fighters in painter's
order (art pixels), the pixel frames and pixel fonts of the interface (device pixels)."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprites  # noqa: E402
import zone_render  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WT = (os.environ.get('NAPATTACK_REPO') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..')))
FONTS = os.path.join(WT, 'node_modules/@expo-google-fonts')
OUTLINE = (0x1E, 0x19, 0x17, 255)


def hexc(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


TONES = {  # components/pixel-frame.tsx frameTones
    'paper': dict(fill='#FBF4E4', light='#FFFDF5', dark='#E1D2B6', base='#B8A586', outline='#1E1917'),
    'parchment': dict(fill='#F3E6C8', light='#FFF7E2', dark='#DCC9A2', base='#B39A70', outline='#1E1917'),
    'leaf': dict(fill='#6FB35E', light='#A5D77F', dark='#4F8D45', base='#2F5A2C', outline='#24361F'),
    'gold': dict(fill='#E6BC5C', light='#F8DD8F', dark='#BF8F36', base='#7F5B1E', outline='#3B2A14'),
    'nap': dict(fill='#9F8CD3', light='#CBBDF0', dark='#7663B0', base='#4C3F80', outline='#2A2244'),
    'danger': dict(fill='#D47A5C', light='#F0A688', dark='#AE5A40', base='#6E3424', outline='#3A1B13'),
    'night': dict(fill='#3C4168', light='#5A608F', dark='#2B2F50', base='#191B30', outline='#0F1020'),
    'inset': dict(fill='#F7EDD9', light='#E1D2B6', dark='#FFFDF5', base=None, outline='#796650'),
    'disabled': dict(fill='#D9D1BF', light='#ECE6D8', dark='#C1B7A2', base='#9C927C', outline='#5E544A'),
}
INK = hexc('#4A3B35')
BUTTON_INK = hexc('#2F251F')

S = 3  # device pixels per CSS pixel (a 402 x 874 phone at 3x)
U = 4  # device pixels per frame unit (the walk's art pixel: 1.33 CSS px)


def font(kind, css):
    path = {
        'bold': 'pixelify-sans/700Bold/PixelifySans_700Bold.ttf',
        'medium': 'pixelify-sans/500Medium/PixelifySans_500Medium.ttf',
        'display': 'press-start-2p/400Regular/PressStart2P_400Regular.ttf',
    }[kind]
    return ImageFont.truetype(os.path.join(FONTS, path), int(css * S))


def frame(img, x, y, w, h, tone='paper', depth=1, outline=None, fill=None):
    """A pixel frame in device px: notched corners, a 1-unit outline, a lit top and left edge,
    a shaded bottom and right edge and an optional raised base (pixel-frame.tsx)."""
    t = TONES[tone]
    d = ImageDraw.Draw(img)
    o = hexc(outline or t['outline'])
    if depth and t['base']:
        b = hexc(t['base'])
        d.rectangle([x + U, y + h, x + w - U - 1, y + h + depth * U - 1], fill=b)
        d.rectangle([x + U, y + h + depth * U, x + w - U - 1, y + h + (depth + 1) * U - 1], fill=o)
        d.rectangle([x, y + h - U, x + U - 1, y + h + depth * U - 1], fill=o)
        d.rectangle([x + w - U, y + h - U, x + w - 1, y + h + depth * U - 1], fill=o)
    d.rectangle([x + U, y, x + w - U - 1, y + U - 1], fill=o)
    d.rectangle([x + U, y + h - U, x + w - U - 1, y + h - 1], fill=o)
    d.rectangle([x, y + U, x + U - 1, y + h - U - 1], fill=o)
    d.rectangle([x + w - U, y + U, x + w - 1, y + h - U - 1], fill=o)
    d.rectangle([x + U, y + U, x + w - U - 1, y + h - U - 1], fill=hexc(fill or t['fill']))
    d.rectangle([x + U, y + U, x + w - U - 1, y + 2 * U - 1], fill=hexc(t['light']))
    d.rectangle([x + U, y + U, x + 2 * U - 1, y + h - U - 1], fill=hexc(t['light']))
    d.rectangle([x + U, y + h - 2 * U, x + w - U - 1, y + h - U - 1], fill=hexc(t['dark']))
    d.rectangle([x + w - 2 * U, y + 2 * U, x + w - U - 1, y + h - U - 1], fill=hexc(t['dark']))


def text(img, x, y, s, kind='bold', css=12, color=INK, anchor='la', width=None, spacing=1.25):
    d = ImageDraw.Draw(img)
    f = font(kind, css)
    if width is None:
        d.text((x, y), s, font=f, fill=color, anchor=anchor)
        return y + int(css * S * spacing)
    words, line, lines = s.split(), '', []
    for wd in words:
        trial = (line + ' ' + wd).strip()
        if d.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = wd
    lines.append(line)
    for ln in lines:
        d.text((x, y), ln, font=f, fill=color, anchor=anchor)
        y += int(css * S * spacing)
    return y


def paste_scaled(img, im, x, y, k):
    img.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST), (int(x), int(y)))


# ----------------------------------------------------------------------------- the world

ZONE = 'town'
GROUND, OBJECTS = None, None
# lib/zone-maps.ts objects without the props that stand in the ring's view but are drawn
# in front of the fighters by foot y (posts on the south side are)


def place(layer, im, x, foot_y):
    """Paste a sprite with its lowest opaque row on foot_y and its centre on x."""
    bbox = im.getbbox()
    layer.append((foot_y, im, int(x - im.width / 2), int(foot_y - bbox[3])))


def world(view, fighters, effects=()):
    """view: (x0, y0, w, h) in zone art px. fighters: list of (image, x_centre, foot_y).
    effects: callables drawing on the 1x art canvas after everything (in view coords)."""
    x0, y0, w, h = view
    base = GROUND.copy()
    items = []
    for (oid, kind, x, y, ow, oh) in OBJECTS:
        p = os.path.join(WT, f'assets/zones/props/{kind}.png')
        if os.path.exists(p):
            items.append((y + oh, zone_render.down(p), x, y))
    for im, cx, foot in fighters:
        place(items, im, cx, foot)
    items.sort(key=lambda t: t[0])
    canvas = Image.new('RGBA', (GROUND.width, GROUND.height + 200), (0, 0, 0, 0))
    canvas.alpha_composite(base, (0, 0))
    # below the zone (hidden by the tray anyway): carry the grass on
    fill = base.crop((0, GROUND.height - 40, GROUND.width, GROUND.height))
    for k in range(5):
        canvas.alpha_composite(fill, (0, GROUND.height + 40 * k))
    for _, im, x, y in items:
        if x >= 0 and y >= 0:
            canvas.alpha_composite(im, (x, y))
        else:
            canvas.paste(im, (x, y), im)
    out = canvas.crop((x0, y0, x0 + w, y0 + h))
    for fx in effects:
        fx(out, x0, y0)
    return out


def flash(im, amount=0.6):
    """The hit flash: the sprite washed towards white (Pet's hit flash in game-ui.tsx)."""
    px = im.load()
    out = im.copy()
    po = out.load()
    for yy in range(im.height):
        for xx in range(im.width):
            r, g, b, a = px[xx, yy]
            if a:
                po[xx, yy] = (int(r + (255 - r) * amount), int(g + (255 - g) * amount), int(b + (255 - b) * amount), a)
    return out


def spark(cx, cy, size=1):
    """A hit spark at 1x: a four-point star with a gold ring, outlined (drawn, not a glow)."""
    def draw(img, x0, y0):
        d = ImageDraw.Draw(img)
        x, y = cx - x0, cy - y0
        gold, light, white = hexc('#E6BC5C'), hexc('#F8DD8F'), hexc('#FFFDF5')
        r = 5 * size
        for k in range(-r, r + 1):
            for (a, b) in ((k, 0), (0, k)):
                d.point((x + a + 1, y + b + 1), fill=OUTLINE)
        for k in range(-r, r + 1):
            col = white if abs(k) < 2 else light if abs(k) < r - 1 else gold
            d.point((x + k, y), fill=col)
            d.point((x, y + k), fill=col)
        for (a, b) in ((-2, -2), (2, -2), (-2, 2), (2, 2), (-3, -3), (3, 3), (3, -3), (-3, 3)):
            d.point((x + a, y + b), fill=gold if max(abs(a), abs(b)) == 3 else light)
    return draw


def glint(cx, cy, rx, ry):
    """The timing cue: a dashed gold ring closing on the target (one frame of it)."""
    import math

    def draw(img, x0, y0):
        d = ImageDraw.Draw(img)
        n = int(2 * math.pi * max(rx, ry))
        for k in range(n):
            a = 2 * math.pi * k / n
            if (k // 3) % 2:
                continue
            x = round(cx - x0 + rx * math.cos(a))
            y = round(cy - y0 + ry * math.sin(a))
            d.point((x, y + 1), fill=hexc('#7F5B1E'))
            d.point((x, y), fill=hexc('#F8DD8F'))
    return draw


def flying_card(cx, cy):
    def draw(img, x0, y0):
        d = ImageDraw.Draw(img)
        x, y = cx - x0, cy - y0
        d.rectangle([x - 4, y - 5, x + 4, y + 5], fill=OUTLINE)
        d.rectangle([x - 3, y - 4, x + 3, y + 4], fill=hexc('#FBF4E4'))
        d.rectangle([x - 3, y - 4, x + 3, y - 2], fill=hexc('#5FA35A'))
        d.point((x, y + 1), fill=hexc('#80573A'))
    return draw


def leaf_guard(cx, cy):
    """The REST assist's effect: a ring of leaves round the guarded fighter (one frame)."""
    import math

    def draw(img, x0, y0):
        d = ImageDraw.Draw(img)
        for k in range(10):
            a = 2 * math.pi * k / 10
            x = round(cx - x0 + 14 * math.cos(a))
            y = round(cy - y0 + 17 * math.sin(a))
            d.rectangle([x - 1, y - 1, x + 1, y], fill=hexc('#24361F'))
            d.point((x, y - 1), fill=hexc('#A5D77F'))
            d.point((x - 1, y), fill=hexc('#6FB35E'))
            d.point((x, y), fill=hexc('#4F8D45'))
    return draw


def shadow_under(cx, foot, w=12):
    def draw(img, x0, y0):
        pass
    return draw


# ----------------------------------------------------------------------------- interface

CARD_ART = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cardart.json')))
HABIT = {  # habit-cards.tsx: band colour and label
    'stretch': ('#D8AF5E', 'FOCUS'), 'short_walk': ('#5FA35A', 'ROAM'),
    'glass_of_water': ('#D9B48F', 'CARE'), 'deep_breath': ('#CDBFE3', 'REST'),
}


def card_art(id_, k):
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for p in CARD_ART[id_]:
        im.putpixel((p['x'], p['y']), hexc(p['color']))
    return im.resize((16 * k, 16 * k), Image.NEAREST)


def icon(name, k):
    im = sprites.icon(name)
    return im.resize((16 * k, 16 * k), Image.NEAREST)


def energy_badge(img, x, y, cost):
    frame(img, x, y, 30 * S, 26 * S, 'paper', depth=0)
    img.alpha_composite(icon('energy', 3), (x + 3 * S, y + 5 * S))
    text(img, x + 21 * S, y + 4 * S, str(cost), 'bold', 13, BUTTON_INK)


def tile(img, x, y, w, h, title, band, label, cost, effect, art, selected=False, tone='paper',
         outline=None, dim=False):
    frame(img, x, y, w, h, tone, depth=1, outline=('#3E7D44' if selected else outline))
    if selected:  # the lifted card's moss outline, two units thick
        d = ImageDraw.Draw(img)
        d.rectangle([x + U, y + U, x + w - U - 1, y + 2 * U - 1], fill=hexc('#3E7D44'))
        d.rectangle([x + U, y + U, x + 2 * U - 1, y + h - U - 1], fill=hexc('#3E7D44'))
        d.rectangle([x + w - 2 * U, y + U, x + w - U - 1, y + h - U - 1], fill=hexc('#3E7D44'))
    d = ImageDraw.Draw(img)
    d.rectangle([x + 3 * U, y + 3 * U, x + w - 3 * U - 1, y + 3 * U + 22 * S], fill=hexc(band))
    text(img, x + 3 * U + 4 * S, y + 3 * U + 5 * S, label, 'bold', 10, BUTTON_INK)
    energy_badge(img, x + w - 3 * U - 30 * S, y + 3 * U - 2 * S, cost)
    well = 52 * S
    wx, wy = x + (w - well) // 2, y + 3 * U + 28 * S
    frame(img, wx, wy, well, well, 'inset', depth=0)
    img.alpha_composite(art, (wx + (well - art.width) // 2, wy + (well - art.height) // 2))
    ty = wy + well + 5 * S
    ty = text(img, x + w // 2, ty, title, 'bold', 10.5, BUTTON_INK, anchor='ma', width=w - 8 * U, spacing=1.15)
    text(img, x + w // 2, ty + 1 * S, effect, 'medium', 10, INK, anchor='ma', width=w - 8 * U, spacing=1.15)
    if dim:
        veil = Image.new('RGBA', (w, h), (251, 244, 228, 110))
        img.alpha_composite(veil, (x, y))


def plate(img, cx, bottom, name, hp, hpmax, tone='paper', guard=False):
    """The over-head plate: a name and an HP bar, anchored above a fighter's head."""
    w, h = 104 * S, 34 * S
    x, y = int(cx - w / 2), int(bottom - h)
    frame(img, x, y, w, h, tone, depth=0)
    text(img, x + 4 * U, y + 3 * U, name, 'bold', 9.5, BUTTON_INK)
    text(img, x + w - 4 * U, y + 3 * U, f'{hp}/{hpmax}', 'bold', 9.5, BUTTON_INK, anchor='ra')
    d = ImageDraw.Draw(img)
    bx0, by0, bx1, by1 = x + 3 * U, y + h - 3 * U - 7 * S, x + w - 3 * U, y + h - 3 * U
    d.rectangle([bx0, by0, bx1, by1], fill=hexc('#796650'))
    d.rectangle([bx0 + U // 2 * 1, by0 + 2, bx1 - 2, by1 - 2], fill=hexc('#E1D2B6'))
    fillw = int((bx1 - bx0 - 4) * hp / hpmax)
    col = '#3E7D44' if hp >= hpmax * 0.5 else '#D8AF5E' if hp >= hpmax * 0.25 else '#973D35'
    d.rectangle([bx0 + 2, by0 + 2, bx0 + 2 + fillw, by1 - 2], fill=hexc(col))
    d.rectangle([bx0 + 2, by0 + 2, bx0 + 2 + fillw, by0 + 2 + S], fill=hexc('#7FBF6A' if col == '#3E7D44' else '#F8DD8F'))
    if guard:
        img.alpha_composite(icon('shield', 3), (x - 22 * S, y + 4 * S))


def bubble(img, cx, bottom, icon_name, value, tone='parchment'):
    """The rival's intent: an icon and a number in a speech frame with a stepped tail."""
    w, h = 64 * S, 30 * S
    x, y = int(cx - w / 2), int(bottom - h - 8 * S)
    frame(img, x, y, w, h, tone, depth=0)
    d = ImageDraw.Draw(img)
    t = TONES[tone]
    tx = int(cx)
    for k, half in enumerate((3, 2, 1)):
        yy = y + h - U + k * U
        d.rectangle([tx - (half + 1) * U, yy, tx + (half + 1) * U - 1, yy + U - 1], fill=hexc(t['outline']))
        d.rectangle([tx - half * U, yy, tx + half * U - 1, yy + U - 1], fill=hexc(t['fill']))
    img.alpha_composite(icon(icon_name, 4), (x + 4 * U, y + (h - 64) // 2))
    text(img, x + 4 * U + 70, y + 7 * S, value, 'display', 11, BUTTON_INK)


def stamp(img, cx, cy, word, tone='gold', css=12):
    f = font('display', css)
    d = ImageDraw.Draw(img)
    tw = d.textlength(word, font=f)
    w, h = int(tw + 10 * U), int(css * S + 8 * U)
    frame(img, int(cx - w / 2), int(cy - h / 2), w, h, tone, depth=1)
    text(img, cx, cy - css * S / 2 + 2, word, 'display', css, BUTTON_INK, anchor='ma')


def damage(img, cx, cy, value, css=16):
    f = font('display', css)
    d = ImageDraw.Draw(img)
    for dx, dy in ((-S, 0), (S, 0), (0, -S), (0, S), (S, S), (2 * S, 2 * S)):
        d.text((cx + dx, cy + dy), value, font=f, fill=OUTLINE, anchor='ma')
    d.text((cx, cy), value, font=f, fill=hexc('#FFFDF5'), anchor='ma')


def pips(img, x, y, n, of, on='#E6BC5C', off='#E1D2B6', size=12, gap=4, icon_name=None):
    d = ImageDraw.Draw(img)
    for k in range(of):
        px = x + k * (size + gap) * S
        if icon_name and k < n:
            img.alpha_composite(icon(icon_name, 3 if size <= 16 else 4), (px - 2 * S, y - 2 * S))
            continue
        d.rectangle([px, y, px + size * S - 1, y + size * S - 1], fill=OUTLINE)
        d.rectangle([px + S, y + S, px + size * S - 1 - S, y + size * S - 1 - S], fill=hexc(on if k < n else off))
        if k < n:
            d.rectangle([px + S, y + S, px + size * S - 1 - S, y + 2 * S], fill=hexc('#F8DD8F' if on == '#E6BC5C' else '#CBBDF0'))
