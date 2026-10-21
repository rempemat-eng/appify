"""The Glare: a will-o'-wisp of screen light that drifts in from Neon Harbour (mock art, 1x).

A flame-shaped wisp, cold blue-white at the core, with a little lit screen for a face, a red
notification dot and a flickering tail. Calmed, it turns warm amber, closes its eyes and loses
the dot. Drawn procedurally so the frames stay on one pixel grid; light from the upper left
(the darker bands sit lower right), clean clusters, a deep outline.
"""
import math

from PIL import Image

COLD = ['#FFFFFF', '#DDF5FF', '#A6E2FF', '#64BDF2', '#3B83CF', '#2B55A3']
WARM = ['#FFFBEA', '#FFEDB8', '#FFD27A', '#F2A64A', '#CF7A30', '#94502A']
OUT_COLD = '#182046'
OUT_WARM = '#3A2114'


def hexc(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _inside(x, y, sway, scale):
    # body: a circle; tip: a tapering flame that sways
    cx, cy, r = 11.0, 17.0, 7.6 * scale
    if (x - cx) ** 2 + ((y - cy) * 1.05) ** 2 <= r * r:
        return True
    top = 17 - 15 * scale
    if top <= y <= 17:
        t = (y - top) / (17 - top)
        mid = cx + sway * math.sin((1 - t) * 2.6) * 3.2 + (1 - t) * 1.0
        w = 7.4 * scale * (t ** 0.85)
        return abs(x + 0.5 - mid) < w
    return False


def body(calm=False, sway=1.0, scale=1.0, face=True, eyes='open', badge=True):
    W, H = 24, 30
    tones = WARM if calm else COLD
    out = hexc(OUT_WARM if calm else OUT_COLD)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    inside = [[_inside(x, y, sway, scale) for x in range(W)] for y in range(H)]
    # a tail of three wisps trailing down and to the right (it drifts west, towards you)
    # a flicker of hem under the body: three small licks, the wisp's 'feet'
    for (tx, ty, tr) in ((7.5, 23.6, 1.5), (11.5, 24.6, 1.6), (15.0, 23.2, 1.3)):
        for y in range(H):
            for x in range(W):
                if (x - tx) ** 2 + (y - ty) ** 2 <= tr * tr * scale:
                    inside[y][x] = True
    core = (9.5, 16.0)
    px = im.load()
    for y in range(H):
        for x in range(W):
            if not inside[y][x]:
                continue
            # emissive: bright core, darker outward, biased lower right (upper-left light)
            d = math.hypot((x - core[0]) * 1.0, (y - core[1]) * 0.9)
            d += 0.35 * ((x - core[0]) + (y - core[1])) * 0.5
            k = 0 if d < 2.2 else 1 if d < 4.2 else 2 if d < 6.2 else 3 if d < 8.0 else 4 if d < 10.5 else 5
            px[x, y] = hexc(tones[k])
    # outline: outside pixels touching the shape (4-neighbour), none on the far upper-left
    # rim pixels of the tip so the flame stays soft at its point
    for y in range(H):
        for x in range(W):
            if inside[y][x]:
                continue
            n = any(0 <= x + dx < W and 0 <= y + dy < H and inside[y + dy][x + dx]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if n:
                px[x, y] = out
    if face:
        # the little screen: a 9 x 6 lit rectangle with a darker bezel
        sx, sy, sw, sh = 6, 14, 10, 7
        bez = hexc(tones[4])
        glass = hexc(tones[1])
        for y in range(sy, sy + sh):
            for x in range(sx, sx + sw):
                edge = y in (sy, sy + sh - 1) or x in (sx, sx + sw - 1)
                corner = (y in (sy, sy + sh - 1)) and (x in (sx, sx + sw - 1))
                if corner:
                    continue
                px[x, y] = bez if edge else glass
        # a glint on the glass, upper left
        px[sx + 1, sy + 1] = hexc(tones[0])
        px[sx + 2, sy + 1] = hexc(tones[0])
        eye = out
        if eyes == 'open':  # wide, staring, a little too awake: tall pupils, brows tilted in
            for ex in (sx + 3, sx + 6):
                px[ex, sy + 2] = eye
                px[ex, sy + 3] = eye
            px[sx + 2, sy + 1] = eye
            px[sx + 7, sy + 1] = eye
        elif eyes == 'squint':  # dazzled, blinking
            for ex in (sx + 2, sx + 6):
                px[ex, sy + 3] = eye
                px[ex + 1, sy + 3] = eye
        else:  # closed, content: little arcs
            for ex in (sx + 2, sx + 6):
                px[ex, sy + 3] = eye
                px[ex + 1, sy + 4] = eye
                px[ex + 2, sy + 3] = eye
        if eyes != 'closed':
            px[sx + 4, sy + 5] = eye  # a tight, wobbly mouth
            px[sx + 5, sy + 4] = eye
            px[sx + 6, sy + 5] = eye
        if badge and not calm:
            # the notification dot, top right of the screen, outlined
            bx, by = sx + sw - 2, sy - 2
            for y in range(by - 1, by + 4):
                for x in range(bx - 1, bx + 4):
                    if (x in (bx - 1, bx + 3)) and (y in (by - 1, by + 3)):
                        continue
                    px[x, y] = out
            for y in range(by, by + 3):
                for x in range(bx, bx + 3):
                    px[x, y] = hexc('#E8434F')
            px[bx, by] = hexc('#FF9A9A')
            px[bx + 2, by + 2] = hexc('#A82832')
    return im


def sparks(img, x, y, calm=False, phase=0):
    """Loose sparks trailing behind it (east), drawn at 1x onto img at the wisp's top-left x, y."""
    tones = WARM if calm else COLD
    pts = [(21, 19), (23, 24), (19, 27)] if phase == 0 else [(22, 21), (20, 25), (24, 28)]
    px = img.load()
    for k, (sx, sy) in enumerate(pts):
        X, Y = x + sx, y + sy
        big = k == 0
        for dx, dy in ((0, 0),) + (((1, 0), (-1, 0), (0, 1), (0, -1)) if big else ()):
            if 0 <= X + dx < img.width and 0 <= Y + dy < img.height:
                px[X + dx, Y + dy] = hexc(tones[0] if (dx, dy) == (0, 0) else tones[2])


def halo(im, color='#A6E2FF', alpha=70):
    """A one-pixel soft rim of light round the outline (screen glow), then a second fainter one."""
    W, H = im.width + 4, im.height + 4
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    base.alpha_composite(im, (2, 2))
    a = base.split()[3].load()
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = glow.load()
    c = hexc(color)
    for ring, al in ((1, alpha), (2, alpha // 2)):
        for y in range(H):
            for x in range(W):
                if a[x, y]:
                    continue
                near = any(0 <= x + dx < W and 0 <= y + dy < H and a[x + dx, y + dy]
                           for dx in range(-ring, ring + 1) for dy in range(-ring, ring + 1)
                           if abs(dx) + abs(dy) == ring)
                if near and not g[x, y][3]:
                    g[x, y] = c[:3] + (al,)
    glow.alpha_composite(base)
    return glow


def ground_glow(img, cx, cy, rx, ry, color='#9FE0FF', strength=0.32):
    """Light thrown on the ground under the wisp: two stepped bands, added onto the art."""
    c = hexc(color)
    px = img.load()
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if not (0 <= x < img.width and 0 <= y < img.height):
                continue
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1:
                continue
            s = strength if d < 0.45 else strength * 0.5
            r, g, b, a = px[x, y]
            px[x, y] = (int(r + (c[0] - r) * s), int(g + (c[1] - g) * s), int(b + (c[2] - b) * s), a)


def reflection(im, alpha=0.45, squash=2):
    """Its reflection on water: flipped, squashed, rows shifted for ripples, faint."""
    f = im.transpose(Image.FLIP_TOP_BOTTOM)
    f = f.resize((f.width, max(1, f.height // squash)), Image.NEAREST)
    out = Image.new('RGBA', (f.width + 2, f.height), (0, 0, 0, 0))
    for y in range(f.height):
        row = f.crop((0, y, f.width, y + 1))
        dx = (0, 1, 0, -1)[y % 4] + 1
        out.alpha_composite(row, (dx, y))
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (r, g, b, int(a * alpha * (1 - y / out.height * 0.6)))
    return out


if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    frames = [body(), body(sway=-1.0), body(eyes='squint', scale=0.95), body(calm=True, eyes='closed', scale=0.85)]
    sheet = Image.new('RGBA', (34 * len(frames), 40), (70, 110, 70, 255))
    for i, f in enumerate(frames):
        sheet.alpha_composite(halo(f, '#FFD27A' if i == 3 else '#A6E2FF'), (34 * i + 3, 3))
        sparks(sheet, 34 * i + 5, 5, calm=(i == 3), phase=i % 2)
    sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).save(os.path.join(here, 'look_glare.png'))
