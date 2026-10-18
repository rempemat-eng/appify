"""The journeys between regions (world-atlas.md, "Seamless travel"): between regions
the trip itself is the transition. Each destination gets three scrolling layers seen
from the carriage window (sky, far land, near land with the line) that loop across,
plus the vehicle. Run: python3 scripts/art/journey.py  (JOURNEY_PREVIEW=dir for a sheet)
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, smooth_noise  # noqa: E402
import style  # noqa: E402
import steampunk_props as sp  # noqa: E402
from materials import MATERIALS, G, STONE, WOOD, SNOW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'journeys')
W, H, SCALE = 320, 160, 4  # one loop of each layer; the app repeats it side by side

M = MATERIALS
THEMES = {
    # destination: sky top/bottom, far ramp, near ramp, extras
    'valley': {'sky': ('#7FB4E6', '#D8ECF6'), 'far': ['#5E8A8E', '#77A0A0', '#94B8B0'], 'near': G, 'kind': 'meadow'},
    'steam': {'sky': ('#B8A890', '#E8D8B8'), 'far': ['#6E5A50', '#8A7060', '#A08878'], 'near': M['brick'], 'kind': 'town'},
    'west': {'sky': ('#E8A060', '#FBE0A8'), 'far': M['adobe'], 'near': M['desert'], 'kind': 'mesa'},
    'lava': {'sky': ('#2A0E0A', '#7A2A10'), 'far': M['basalt'], 'near': M['ash'], 'kind': 'lava'},
    'neon': {'sky': ('#140E28', '#3A1E4A'), 'far': M['night'], 'near': M['night'], 'kind': 'city'},
    'space': {'sky': ('#05060C', '#141A30'), 'far': M['hull'], 'near': M['hull'], 'kind': 'space'},
    'moon': {'sky': ('#05060C', '#0B0E1C'), 'far': M['regolith'], 'near': M['regolith'], 'kind': 'moon'},
}


def lerp(a: str, b: str, t: float) -> tuple:
    ca = [int(a[k:k + 2], 16) for k in (1, 3, 5)]
    cb = [int(b[k:k + 2], 16) for k in (1, 3, 5)]
    return tuple(int(ca[i] + (cb[i] - ca[i]) * t) for i in range(3)) + (255,)


def sky(theme) -> Canvas:
    top, bottom = theme['sky']
    cv = Canvas(W, H)
    for y in range(H):
        t = y / (H - 1)
        band = round(t * 6) / 6  # stepped bands, dithered at the joins
        for x in range(W):
            tt = band if (x + y) % 2 or abs(t - band) > 0.03 else t
            cv.set(x, y, lerp(top, bottom, tt))
    if theme['kind'] in ('neon', 'space', 'lava', 'moon') or theme['kind'] == 'city':
        for i in range(70 if theme['kind'] in ('space', 'moon') else 30):
            x, y = int(noise2(i, 0, 501) * W), int(noise2(i, 1, 501) * H * 0.7)
            cv.set(x, y, '#FFFFFF' if theme['kind'] != 'lava' else '#FFB648')
    else:
        for (cx, cy, r) in ((60, 30, 14), (210, 22, 18), (290, 44, 10)):  # soft clouds
            for (x, y) in oval(cx, cy, r * 1.8, r * 0.6):
                cv.set(x % W, y, '#FFFFFF' if y < cy else '#EAF2F8')
    if theme['kind'] == 'moon':
        for (x, y) in disc(250, 46, 26):  # the planet, far behind now
            band = int((y + math.sin(x / 7) * 2) / 4) % 3
            cv.set(x, y, ('#3E6AA8', '#5A8AC4', '#E6EEF6')[band] if (x - 250) + (y - 46) < 20 else '#2C4A78')
    if theme['kind'] == 'space':
        for (x, y) in disc(240, 150, 70):  # the planet below
            if 0 <= y < H:
                band = int((y + math.sin(x / 9) * 2) / 5) % 3
                cv.set(x, y, ('#3E6AA8', '#5A8AC4', '#E6EEF6')[band])
    return cv


def ridge(cv: Canvas, ramp, base: int, amp: float, freq: float, seed: int, lit: bool = True):
    """A loopable skyline of land: height from sines with whole periods across W."""
    for x in range(W):
        top = base - int(amp * (0.6 * math.sin(2 * math.pi * x * freq / W + seed) + 0.4 * math.sin(2 * math.pi * x * (freq * 2) / W + seed * 2)))
        for y in range(top, H):
            k = y - top
            c = ramp[2] if k < 2 and lit else ramp[1] if k < 10 else ramp[0]
            cv.set(x, y, c)


def _rgb(c):
    return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5)) if isinstance(c, str) else tuple(c[:3])


def haze(sprite: Canvas, colour: str, t: float) -> Canvas:
    """A copy of a sprite pulled toward the air's colour (distance), alpha kept."""
    out = Canvas(sprite.w, sprite.h)
    tr = _rgb(colour)
    for y in range(sprite.h):
        for x in range(sprite.w):
            c = sprite.get(x, y)
            if c[3]:
                out.set(x, y, tuple(int(c[i] + (tr[i] - c[i]) * t) for i in range(3)) + (c[3],))
    return out


def shrink(sprite: Canvas, f: float) -> Canvas:
    """A sprite at a fraction of its size (far away), nearest-neighbour."""
    from PIL import Image
    w, h = max(1, int(sprite.w * f)), max(1, int(sprite.h * f))
    img = sprite.img.resize((w, h), Image.NEAREST)
    out = Canvas(w, h)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 128:
                out.set(x, y, px[x, y][:3] + (255,))
    return out


def stamp(cv: Canvas, sprite: Canvas, x: int, foot: int):
    """Paste a sprite with its foot at `foot`, wrapping across the loop's seam."""
    for dx in (0, -W, W):
        cv.paste(sprite, x + dx, foot - sprite.h)


def far_land(cv: Canvas, ramp, base: int, amp: float, freq: float, seed: int, cap=None, cap_above: int = 0):
    """A loopable band of distant land: lit along its crest, deeper below, snow on the
    highest crests if `cap` is given."""
    for x in range(W):
        top = base - int(amp * (0.6 * math.sin(2 * math.pi * x * freq / W + seed) + 0.4 * math.sin(2 * math.pi * x * (freq * 2) / W + seed * 2)))
        for y in range(top, H):
            k = y - top
            c = ramp[2] if k < 2 else ramp[1] if k < 12 or (k < 16 and (x + y) % 2) else ramp[0]
            if cap and top < cap_above and k < (cap_above - top) * 0.7 + 2:
                c = cap[0] if (x - W // 2) % 37 < 18 else cap[1]  # snow, shaded on one flank
            cv.set(x, y, c)


def telegraph(cv: Canvas, spacing: int = 80, top: int = 44, foot: int = 116, wood=WOOD):
    """Telegraph poles with a crossarm and wires sagging between them."""
    for px in range(10, W, spacing):
        for y in range(top, foot):
            cv.set(px, y, wood[3]); cv.set(px + 1, y, wood[1])
        cv.hline(px - 6, top + 4, 14, wood[2]); cv.hline(px - 6, top + 5, 14, wood[1])
        for gx in (px - 5, px + 6):
            cv.set(gx, top + 3, '#E6EEF6')
    for wire in (0, 1):
        for x in range(W):
            t = ((x - 10) % spacing) / spacing
            sag = int(math.sin(t * math.pi) * 7)
            gx = -5 if wire == 0 else 6
            cv.set((x + gx) % W, top + 3 + sag, '#3A3034')


def far(theme) -> Canvas:
    cv = Canvas(W, H)
    kind = theme['kind']
    air = theme['sky'][1]
    if kind == 'space':
        return cv  # the void; the planet is in the sky layer
    if kind == 'moon':  # the moon's grey mountains coming up to meet the shuttle
        ridge(cv, theme['far'], 110, 22, 2, 4)
        ridge(cv, [theme['far'][1], theme['far'][2], theme['far'][3]], 130, 10, 3, 6)
        return cv
    if kind == 'meadow':
        import garden_props as gp
        import valley_props as vp
        import harbour_props as hbp
        far_land(cv, ['#7E98B0', '#93AEC2', '#AFC6D4'], 70, 18, 3, 2, cap=('#F4F7FA', '#D6E0EA'), cap_above=60)
        far_land(cv, ['#5E8A6A', '#6E9A70', '#8AB27E'], 98, 9, 2, 5)
        for i in range(14):  # hedgerows along the hills
            x0 = int(noise2(i, 0, 520) * W)
            for x in range(x0, x0 + 30):
                y = 104 + int(noise2(i, 1, 520) * 10) + int(math.sin(x / 9) * 1.5)
                cv.set(x % W, y, '#4E7A50'); cv.set(x % W, y + 1, '#3E6A4A')
        tree = haze(shrink(style.finalize(gp.tree(True), name='jt'), 0.42), air, 0.35)
        pine = haze(shrink(style.finalize(gp.pine(), name='jp'), 0.42), air, 0.35)
        mill = haze(shrink(style.finalize(vp.windmill(), name='jm'), 0.5), air, 0.3)
        home = haze(shrink(style.finalize(hbp.cottage(80, 0), name='jc'), 0.4), air, 0.3)
        for (spr, x, foot) in ((tree, 20, 104), (pine, 34, 103), (tree, 96, 102), (mill, 150, 104), (home, 186, 106),
                               (home, 214, 104), (tree, 236, 105), (pine, 268, 102), (tree, 290, 104)):
            stamp(cv, spr, x, foot)
        return cv
    if kind == 'town':
        import steampunk_props as stp
        far_land(cv, ['#8A7A6C', '#9A8A7A', '#B2A28E'], 92, 8, 2, 3)
        clock = haze(shrink(style.finalize(stp.clock_tower(), name='jk'), 0.6), air, 0.4)
        shop = haze(shrink(style.finalize(stp.workshop(96, 'gear'), name='jw'), 0.5), air, 0.4)
        for i in range(9):  # factory chimneys with slow smoke
            x0 = i * 36 + int(noise2(i, 0, 521) * 10)
            hgt = 34 + int(noise2(i, 1, 521) * 26)
            for y in range(H - 50 - hgt, H):
                for x in range(x0, x0 + 6):
                    cv.set(x % W, y, '#8A6A5A' if x < x0 + 2 else '#7A5A4C')
            for k in range(4):
                for (x, y) in disc(x0 + 3 + k * 4, H - 56 - hgt - k * 5, 3 + k):
                    cv.set(x % W, y, '#D8CCBC' if (x + y) % 3 else '#C8BCAC')
        for (spr, x, foot) in ((shop, 6, 118), (clock, 110, 118), (shop, 160, 120), (shop, 250, 118)):
            stamp(cv, spr, x, foot)
        return cv
    if kind == 'mesa':
        A = theme['far']
        for (base, ramp, step) in ((70, ['#C89A7A', '#D8AE8E', '#E8C4A4', '#F2D4B4'], 110), (92, A, 80)):
            for x in range(W):  # flat-topped mesas and buttes, banded strata, lit tops
                seg = (x + step // 3) % step
                top = base if 12 < seg < step * 0.62 else base + 34
                if 6 < seg <= 12 or step * 0.62 <= seg < step * 0.62 + 6:
                    top = base + 12  # talus slopes
                for y in range(top, H):
                    c = ramp[3] if y < top + 2 else ramp[2] if ((y - top) // 5) % 2 else ramp[1]
                    if seg > step * 0.5 and y > top + 2:
                        c = ramp[1] if ((y - top) // 5) % 2 else ramp[0]  # the shaded flank
                    cv.set(x, y, c)
        return cv
    if kind == 'lava':
        LAVA = M['lava']
        far_land(cv, theme['far'], 96, 14, 3, 1)
        for x in range(W):  # the volcano, glowing at its lip, a plume over it
            cx = 160
            top = 46 + int(abs(x - cx) * 0.9)
            if abs(x - cx) < 64:
                for y in range(top, H):
                    c = theme['far'][2] if x < cx else theme['far'][1]
                    if y < top + 3 and abs(x - cx) < 10:
                        c = LAVA[4] if y == top else LAVA[3]
                    elif noise2(x // 2, y // 6, 523) > 0.86 and y > top + 6:
                        c = LAVA[2]  # a seam running down
                    cv.set(x, y, c)
        for k in range(10):
            for (x, y) in disc(160 + int(math.sin(k) * 6) + k * 2, 40 - k * 4, 4 + k * 0.8):
                cv.set(x, y, '#5A2A20' if (x + y) % 2 else '#7A3A28')
        return cv
    # the city: towers with lit windows, neon strips, blinking tips
    for i in range(16):
        x0 = i * 20 + int(noise2(i, 0, 502) * 6)
        hgt = 40 + int(noise2(i, 1, 502) * 60)
        for y in range(H - hgt, H):
            for x in range(x0, x0 + 16):
                cv.set(x % W, y, theme['far'][2] if x < x0 + 3 else theme['far'][1])
        for wy in range(H - hgt + 4, H - 4, 6):
            for wx in range(x0 + 2, x0 + 14, 4):
                if noise2(wx, wy, 503) > 0.55:
                    cv.set(wx % W, wy, ('#FFC766', '#6FE6F2', '#FF7EC2')[(wx + wy) % 3])
        if i % 3 == 0:  # a vertical neon sign
            col = (M['neon_pink'], M['neon_cyan'], M['neon_amber'])[i % 3 // 1 % 3]
            for y in range(H - hgt + 8, H - hgt + 30):
                cv.set((x0 + 15) % W, y, col[3] if y % 4 else col[4])
        cv.vline((x0 + 8) % W, H - hgt - 6, 6, theme['far'][2]); cv.set((x0 + 8) % W, H - hgt - 7, '#FF5A5A')
    return cv


def near(theme) -> Canvas:
    cv = Canvas(W, H)
    ramp = theme['near']
    kind = theme['kind']
    if kind == 'moon':  # regolith and craters rushing past under the shuttle
        for y in range(128, H):
            for x in range(W):
                n = smooth_noise(x, y, 12, 509)
                cv.set(x, y, ramp[3] if n > 0.45 else ramp[2])
        for i in range(8):
            cx = i * 40 + int(noise2(i, 0, 510) * 10)
            for (x, y) in oval(cx, 144, 10, 4):
                cv.set(x % W, y, ramp[1] if (x - cx) + (y - 144) * 2 > 0 else ramp[4])
        return cv
    if kind == 'space':
        for x in range(W):  # the elevator's cable rushing past
            if x % 80 in (38, 39):
                for y in range(0, H):
                    cv.set(x, y, M['hull'][3] if x % 80 == 38 else M['hull'][2])
        return cv
    for y in range(112, H):  # the embankment: calm bands, tufts along its top
        for x in range(W):
            n = smooth_noise(x, y, 14, 506)
            c = ramp[2] if n > 0.45 or (n > 0.4 and (x + y) % 2) else ramp[1]
            if y > 140:
                c = ramp[1] if n > 0.5 else ramp[0]
            cv.set(x, y, c)
        if y == 112:
            for x in range(W):
                cv.set(x, y, ramp[3])
    for y in range(118, 130):  # ballast under the line
        for x in range(W):
            if y > 118 + abs(((x * 7) % 5) - 2) // 2:
                cv.set(x, y, STONE[3] if noise2(x, y, 524) > 0.5 else STONE[2] if (x + y) % 3 else STONE[1])
    if kind == 'meadow':
        import garden_props as gp
        import detail
        for t in range(40):
            detail.grass_tuft(cv, int(noise2(t, 0, 525) * W), 113 + int(noise2(t, 1, 525) * 4), t % 6, G, 2)
        for t in range(18):  # flowers in the verge
            x = int(noise2(t, 0, 526) * W)
            cv.set(x, 114 + t % 3, ('#F7F2E8', '#F2D27A', '#E8A0BC')[t % 3])
        for px in range(0, W, 16):  # a post-and-wire fence
            for y in range(100, 114):
                cv.set(px, y, WOOD[3]); cv.set(px + 1, y, WOOD[1])
        for wy in (103, 108):
            for x in range(W):
                cv.set(x, wy, '#6A5A4A' if x % 16 > 1 else WOOD[3])
        telegraph(cv)
        tree = style.finalize(gp.tree(True), name='jnt')
        tree_s = style.finalize(gp.tree(False), name='jns')
        pine = style.finalize(gp.pine(), name='jnp')
        bush = style.finalize(gp.bush(), name='jnb')
        for (spr, x, foot) in ((tree, 30, 116), (bush, 104, 116), (pine, 140, 116), (tree_s, 214, 116), (bush, 262, 117)):
            stamp(cv, spr, x, foot)
    elif kind == 'town':
        import steampunk_props as stp
        BR = M['brick']
        for y in range(96, 113):  # a low brick wall along the line, coped in stone
            for x in range(W):
                course = (y - 96) // 4
                c = BR[2] if ((x + (course % 2) * 5) // 10 + course) % 3 else BR[3]
                if (y - 96) % 4 == 3 or (x + (course % 2) * 5) % 10 == 0:
                    c = BR[1]
                cv.set(x, y, c)
        for x in range(W):
            cv.set(x, 95, STONE[4]); cv.set(x, 96, STONE[3]); cv.set(x, 97, STONE[2])
        lamp = style.finalize(stp.gas_lamp(), name='jgl')
        for x in (20, 120, 220):
            stamp(cv, lamp, x, 100)
        telegraph(cv, spacing=106, top=40, foot=96, wood=M['iron'])
    elif kind == 'mesa':
        import western_props as wsp
        telegraph(cv, spacing=106, top=46)
        tall = style.finalize(wsp.saguaro(True), name='jst')
        short = style.finalize(wsp.saguaro(False), name='jss')
        weed = style.finalize(wsp.tumbleweed(), name='jtw')
        rocks = style.finalize(wsp.sandstone_outcrop(0), name='jro')
        scrub = style.finalize(wsp.desert_scrub(0), name='jsc')
        for (spr, x, foot) in ((tall, 34, 116), (scrub, 90, 116), (short, 150, 116), (rocks, 196, 117), (weed, 250, 116),
                               (tall, 280, 116)):
            stamp(cv, spr, x, foot)
    elif kind == 'lava':
        import caldera_props as cdp
        LAVA = M['lava']
        for x in range(W):  # a lava channel beside the line, crusted at its edges
            if (x // 80) % 2 == 0:
                for y in range(106, 112):
                    c = LAVA[4] if y == 107 and x % 9 < 4 else LAVA[3] if y < 110 else LAVA[2]
                    if y in (106, 111):
                        c = M['basalt'][1]
                    cv.set(x, y, c)
        cols = style.finalize(cdp.basalt_columns(3, 7), name='jbc')
        obs = style.finalize(cdp.obsidian_rock(False), name='job')
        snag = style.finalize(cdp.charred_snag(), name='jcs')
        for (spr, x, foot) in ((cols, 10, 116), (snag, 120, 114), (obs, 168, 116), (cols, 210, 116), (snag, 296, 115)):
            stamp(cv, spr, x, foot)
    elif kind == 'city':
        import cyber_props as cyp
        for i in range(4):  # pillars of the elevated line with neon strips
            x = i * 80 + 30
            for y in range(56, 114):
                for dx in range(10):
                    cv.set((x + dx) % W, y, M['night'][4] if dx < 2 else M['night'][3] if dx < 7 else M['night'][2])
            for y in range(66, 92):
                cv.set((x + 4) % W, y, M['neon_pink'][3] if i % 2 else M['neon_cyan'][3])
        for x in range(W):  # the deck above
            for y in range(50, 56):
                cv.set(x, y, M['night'][4] if y == 50 else M['night'][3] if y < 54 else M['night'][1])
        light = style.finalize(cyp.street_light(), name='jsl')
        board = style.finalize(cyp.holo_board(), name='jhb')
        for (spr, x, foot) in ((light, 6, 114), (board, 100, 114), (light, 170, 114), (board, 250, 114)):
            stamp(cv, spr, x, foot)
    for x in range(W):  # sleepers and the rail
        if x % 6 < 3:
            for y in range(120, 126):
                cv.set(x, y, WOOD[2] if y < 123 else WOOD[1])
        cv.set(x, 120, STONE[4]); cv.set(x, 121, STONE[2])
    return cv


def carriage() -> Canvas:
    """A passenger carriage, 72 x 40, side on: a varnished body with warm windows."""
    w, h = 72, 40
    cv = Canvas(w, h, pad=4)
    for x in range(2, w - 2):
        for y in range(6, 32):
            cv.set(x, y, WOOD[3] if y < 9 else WOOD[2] if y < 26 else WOOD[1])
    cv.rect(0, 3, w, 4, M['iron'][3]); cv.hline(0, 3, w, M['iron'][4])
    for wx in range(8, w - 12, 14):
        for (x, y) in ((xx, yy) for xx in range(wx, wx + 10) for yy in range(11, 20)):
            cv.set(x, y, M['lamplight'][3] if y < 14 else M['lamplight'][2])
    for wxx in (14, w - 14):
        for (x, y) in disc(wxx, 34, 5):
            cv.set(x, y, M['red'][2] if x < wxx else M['red'][1])
        cv.set(wxx, 34, M['brass'][4])
    cv.hline(0, 30, w, M['iron'][1])
    return cv


def capsule() -> Canvas:
    """The space elevator's capsule, 48 x 56: a rounded white pod with a viewport ring
    and the cable through its spine."""
    w, h = 48, 56
    cv = Canvas(w, h, pad=4)
    for (x, y) in oval(24, 28, 20, 26):
        k = (x - 4) / 40
        cv.set(x, y, '#F4F6FA' if k < 0.35 else '#D2D8E4' if k < 0.7 else '#A9B2C4')
    for (x, y) in oval(24, 26, 12, 8):
        cv.set(x, y, '#5A8AC4' if y < 26 else '#2C4A78')
    cv.set(19, 22, '#E6F2FF')
    for y in range(0, h):
        cv.set(24, y, M['hull'][2]) if not (2 < y < 54) else None
    for y in (44, 46):
        cv.hline(10, y, 28, M['neon_cyan'][3])
    return cv


TOP, FOOT = 40, 40  # room added above (sky) and below (the nearest ground) the 160-high scene
FULL_H = H + TOP + FOOT


def tall_sky(theme) -> Canvas:
    """The sky with more of it above: the top colour, a few high clouds (or stars)."""
    out = Canvas(W, FULL_H)
    top = theme['sky'][0]
    for y in range(TOP + 1):
        for x in range(W):
            out.set(x, y, top)
    out.paste(sky(theme), 0, TOP)
    for y in range(TOP + H, FULL_H):  # and below, the sky's foot (seen only where nothing stands)
        for x in range(W):
            out.set(x, y, theme['sky'][1])
    if theme['kind'] in ('space', 'moon', 'city', 'lava'):
        for i in range(24):
            out.set(int(noise2(i, 0, 530) * W), int(noise2(i, 1, 530) * TOP), '#FFFFFF' if theme['kind'] != 'lava' else '#FFB648')
    else:
        for (cx, cy, r) in ((120, 14, 10), (260, 26, 7)):  # high wisps
            for (x, y) in oval(cx, cy, r * 2.4, r * 0.35):
                out.set(x % W, y, '#FFFFFF' if (x + y) % 3 else '#EAF2F8')
    return out


def tall(layer: Canvas) -> Canvas:
    out = Canvas(W, FULL_H)
    out.paste(layer, 0, TOP)
    return out


def foot(theme, cv: Canvas):
    """The nearest ground, below the embankment (y from TOP + H - 8 down): what lies
    beside the line in each land, rushing past fastest."""
    kind, ramp = theme['kind'], theme['near']
    y0 = TOP + H - 8
    if kind == 'space':
        return
    for y in range(y0, FULL_H):  # the ground continues
        for x in range(W):
            n = smooth_noise(x, y, 16, 531)
            cv.set(x, y, ramp[1] if n > 0.5 or (n > 0.45 and (x + y) % 2) else ramp[0])
    if kind == 'moon':
        for i in range(6):
            cx, cy = i * 54 + int(noise2(i, 0, 532) * 12), y0 + 18 + int(noise2(i, 1, 532) * 10)
            for (x, y) in oval(cx, cy, 12, 5):
                cv.set(x % W, y, ramp[1] if (x - cx) + (y - cy) * 2 > 0 else ramp[4])
        return
    wy = y0 + 22  # a band of water (or lava, or street) beside the line
    if kind == 'meadow':
        W_ = M['water']
        for x in range(W):
            for y in range(wy, wy + 10):
                cv.set(x, y, W_[2] if (x // 7 + y) % 5 else W_[3])
            cv.set(x, wy, W_[0]); cv.set(x, wy - 1, G[1])
            if x % 23 < 3:
                cv.hline(x, wy + 4 + x % 3, 3, W_[4])  # glints flowing
        for i in range(16):  # reeds on the far bank
            x = int(noise2(i, 0, 533) * W)
            for y in range(wy - 7, wy):
                cv.set(x, y, G[3] if y < wy - 4 else G[2])
            cv.set(x, wy - 8, '#6E4A2E')
    elif kind == 'town':
        W_ = M['water']
        for x in range(W):
            for y in range(wy - 6, wy):  # the towpath, cobbled
                cv.set(x, y, STONE[3] if (x // 4 + y // 3) % 2 else STONE[2])
            cv.set(x, wy - 7, STONE[4])
            for y in range(wy, wy + 12):  # the canal, green and still
                cv.set(x, y, '#2E4A44' if (x // 9 + y) % 4 else '#3E5E54')
            cv.set(x, wy, '#1E302C')
            if x % 31 < 4:
                cv.hline(x, wy + 5, 4, '#6E8A7A')
        for x in range(0, W, 40):  # mooring rings
            cv.set(x, wy - 3, M['iron'][4]); cv.set(x + 1, wy - 3, M['iron'][2])
    elif kind == 'mesa':
        D = M['desert']
        for x in range(W):  # a dry wash: pale sand, cracks, pebbles
            for y in range(wy - 2, wy + 10):
                c = D[4] if (x + y) % 7 else D[3]
                if (x * 3 + y * 5) % 23 == 0:
                    c = D[2]
                cv.set(x, y, c)
            cv.set(x, wy - 3, D[1])
        for i in range(20):
            px, py = int(noise2(i, 0, 534) * W), wy + int(noise2(i, 1, 534) * 8)
            cv.set(px, py, M['adobe'][4]); cv.set(px + 1, py, M['adobe'][2])
    elif kind == 'lava':
        LAVA = M['lava']
        for x in range(W):
            for y in range(wy, wy + 9):
                n = smooth_noise(x, y, 6, 535)
                c = LAVA[3] if n > 0.45 else LAVA[2]
                if n > 0.75:
                    c = LAVA[4]
                cv.set(x, y, c)
            cv.set(x, wy, LAVA[5] if x % 5 else LAVA[4]); cv.set(x, wy - 1, M['basalt'][0])
            cv.set(x, wy + 9, M['basalt'][0])
    elif kind == 'city':
        N = M['night']
        for x in range(W):  # a wet street with the signs doubled in it
            for y in range(wy - 4, wy + 14):
                cv.set(x, y, N[1] if (x + y) % 3 else N[0])
            cv.set(x, wy - 5, N[4])
        for (sx, col) in ((40, M['neon_pink']), (130, M['neon_cyan']), (220, M['neon_amber']), (290, M['neon_cyan'])):
            for y in range(wy - 2, wy + 13, 2):
                cv.hline(sx + int(noise2(sx, y, 536) * 3) - 1, y, 3, col[2])


def main():
    os.makedirs(OUT, exist_ok=True)
    preview = os.environ.get('JOURNEY_PREVIEW')
    sheet = Canvas(W * 2, FULL_H * len(THEMES)) if preview else None
    for i, (dest, theme) in enumerate(THEMES.items()):
        near_l = tall(near(theme))
        foot(theme, near_l)
        layers = {'sky': tall_sky(theme), 'far': tall(far(theme)), 'near': near_l}
        for name, cv in layers.items():
            cv.save(os.path.join(OUT, f'{dest}-{name}.png'), SCALE)
        if sheet:
            for k in range(2):
                for name in ('sky', 'far', 'near'):
                    sheet.paste(layers[name], k * W, i * FULL_H)
    import cyber_props as cyp
    import space_props as spp
    from PIL import Image as _Image
    mag = style.finalize(cyp.maglev(), name='journey-maglev')
    mag_l = Canvas(mag.w, mag.h)  # mirrored: every vehicle leads to the left
    mag_l.img = mag.img.transpose(_Image.FLIP_LEFT_RIGHT)
    mag_l._px = mag_l.img.load(); mag_l.px = mag_l._px
    cart = sp.coal_cart()
    carts = Canvas(96, 24, pad=4)  # three coal tubs coupled, as the mine line runs them
    for k in range(3):
        carts.paste(style.finalize(cart, name='journey-cart'), k * 32, 2)
        if k:
            carts.hline(k * 32 - 6, 16, 7, M['iron'][1])
    carts_f = style.finalize(carts, name='journey-carts')
    ship = style.finalize(spp.shuttle(), name='journey-shuttle')
    mag_l.save(os.path.join(OUT, 'maglev.png'), SCALE)
    carts_f.save(os.path.join(OUT, 'carts.png'), SCALE)
    ship.save(os.path.join(OUT, 'shuttle.png'), SCALE)
    engine = style.finalize(sp.locomotive(), name='journey-engine')
    coach = style.finalize(carriage(), name='journey-carriage')
    pod = style.finalize(capsule(), name='journey-capsule')
    engine.save(os.path.join(OUT, 'engine.png'), SCALE)
    coach.save(os.path.join(OUT, 'carriage.png'), SCALE)
    pod.save(os.path.join(OUT, 'capsule.png'), SCALE)
    if sheet:
        for i in range(len(THEMES)):
            if list(THEMES)[i] not in ('space', 'moon'):  # the engine faces left and leads; the coach follows
                sheet.paste(engine, 120, i * FULL_H + TOP + 72)
                sheet.paste(coach, 226, i * FULL_H + TOP + 82)
            else:
                sheet.paste(pod, 140, i * FULL_H + TOP + 40)
        sheet.save(os.path.join(preview, 'journeys.png'), 2)
    ident = lambda k: k[0].upper() + k[1:]  # noqa: E731
    lines = [
        '// Generated by scripts/art/journey.py. Do not edit by hand.',
        "import type { ImageSourcePropType } from 'react-native';",
        *[f"import {d}{ident(n)} from '@/assets/journeys/{d}-{n}.png';" for d in THEMES for n in ('sky', 'far', 'near')],
        "import engine from '@/assets/journeys/engine.png';",
        "import carriage from '@/assets/journeys/carriage.png';",
        "import capsule from '@/assets/journeys/capsule.png';",
        "import maglev from '@/assets/journeys/maglev.png';",
        "import carts from '@/assets/journeys/carts.png';",
        "import shuttle from '@/assets/journeys/shuttle.png';",
        f'export const JOURNEY = {{ width: {W}, height: {FULL_H}, rail: {TOP + 120} }} as const;',
        '/** Sky, far land and near land for the trip to each region; each loops across. `above` and',
        ' * `below` fill the screen past the band (the sky\'s top, the ground\'s foot). */',
        'export const journeyLayers: Record<string, { sky: ImageSourcePropType; far: ImageSourcePropType; near: ImageSourcePropType; above: string; below: string }> = {',
        *[f"  {d}: {{ sky: {d}Sky, far: {d}Far, near: {d}Near, above: '{t['sky'][0]}', below: '{'#05060C' if d == 'space' else t['near'][0]}' }}," for d, t in THEMES.items()],
        '};',
        'export const journeyVehicles: Record<string, { source: ImageSourcePropType; w: number; h: number }> = {',
        f'  engine: {{ source: engine, w: {engine.w}, h: {engine.h} }},',
        f'  carriage: {{ source: carriage, w: {coach.w}, h: {coach.h} }},',
        f'  capsule: {{ source: capsule, w: {pod.w}, h: {pod.h} }},',
        f'  maglev: {{ source: maglev, w: {mag_l.w}, h: {mag_l.h} }},',
        f'  carts: {{ source: carts, w: {carts_f.w}, h: {carts_f.h} }},',
        f'  shuttle: {{ source: shuttle, w: {ship.w}, h: {ship.h} }},',
        '};',
        '',
    ]
    target = os.path.join(ROOT, 'lib', 'journey-assets.ts')
    with open(target, 'w') as f:
        f.write('\n'.join(lines))
    import subprocess
    subprocess.run(['npx', 'oxfmt', '--write', target], cwd=ROOT, check=False, capture_output=True)
    print('ok journeys', ', '.join(THEMES))


if __name__ == '__main__':
    main()
