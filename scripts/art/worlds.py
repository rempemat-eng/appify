"""Mission worlds for NapAttack: Park Patrol, Book Club town, Mountain Retreat.

Run: python3 scripts/art/worlds.py   (or `npm run art`)
Writes assets/worlds/<id>/*.png and lib/world-maps.ts (objects, walk grid,
exploration route, visitor spot, water overlays) in art pixels. Step 7 of the
coherence plan re-laid the worlds at the shared density (320 x 296), drew their
props in world_props.py and moved them to the flat 3/4 view with a camera.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval, shade_blob, smooth_noise  # noqa: E402
import garden as g  # noqa: E402  (shared palette keeps one art style)
import style  # noqa: E402
import world_props as wp  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'worlds')
W, H, SCALE, CELL = 320, 296, 4, 4
INK = g.INK
from materials import SLATE, ROOF, SNOW  # noqa: E402
MOSSROCK = ['#4B5548', '#646F5E', '#808C78', '#A2AD97', '#C8D0BC']


# ---- terrain ----------------------------------------------------------------
def thick(points, radius, seed=0):
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (smooth_noise(cx, cy, 9, seed) - 0.5) * (2.4 if seed else 0)
            pts |= disc(cx, cy, r)
    return {(x, y) for (x, y) in pts if 0 <= x < W and 0 <= y < H}


def grass(cv: Canvas, frame=0, tone=None):
    G = tone or g.G
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 22, 11)
            cv.set(x, y, G[2] if n < 0.62 else G[3])
    for ty in range(0, H, 6):
        for tx in range(0, W, 6):
            x, y = tx + int(noise2(tx, ty, 4) * 6), ty + int(noise2(tx, ty, 5) * 6)
            edge = min(x, W - x, y, H - y) < 24
            clearing = ((x - 160) / 73) ** 2 + ((y - 180) / 63) ** 2 < 1
            cluster = smooth_noise(x, y, 25, 63) > 0.57
            density = 0.06 if clearing else 0.5 if edge else 0.36 if cluster else 0.14
            if noise2(tx, ty, 3) < density:
                # tufts in the garden's shapes (scripts/art/detail.py); the ground is still
                import detail
                ground = 3 if cv.get(x, y)[:3] == tuple(int(G[3][k:k + 2], 16) for k in (1, 3, 5)) else 2
                detail.grass_tuft(cv, x, y + 2, int(noise2(tx, ty, 8) * 6) if not clearing else 3, G, ground)
            elif edge and noise2(tx, ty, 7) < 0.15:
                cv.set(x, y, G[4])


def edge(mask, x, y):
    return any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def paint_dirt(cv, mask):
    """Dirt sits below the turf: a dark lip and shadow line along its top edge."""
    for (x, y) in mask:
        cv.set(x, y, g.P[3] if smooth_noise(x, y, 7, 40) > 0.7 else g.P[2])
    for i in range(120):
        x, y = int(noise2(i, 0, 51) * W), int(noise2(i, 1, 51) * H)
        if (x, y) in mask and (x + 1, y) in mask and (x, y + 1) in mask:
            cv.set(x, y, g.P[1])
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, g.P[0])
            if (x, y + 1) in mask:
                cv.set(x, y + 1, g.P[1])
            cv.set(x, y - 1, g.G[1])
        elif edge(mask, x, y):
            cv.set(x, y, g.P[1])
        if (x, y + 1) not in mask:
            cv.set(x, y + 1, g.G[3])


def paint_paving(cv, mask, seed=0):
    """Light square paving stones with mortar lines and the odd darker slab."""
    for (x, y) in mask:
        mortar = x % 12 == 0 or y % 9 == 0 or (y // 9) % 2 and (x + 6) % 12 == 0
        slab = (x // 12 + y // 9 + seed) % 7 == 0
        col = '#A9A28F' if mortar else ('#C9C1AA' if slab else '#DCD4BC')
        if not mortar and (x % 12 == 1 or y % 9 == 1):
            col = '#E8E1CB'
        cv.set(x, y, col)
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, '#8C8574')
        elif edge(mask, x, y):
            cv.set(x, y, '#B3AB94')


def paint_cobbles(cv, mask):
    """Rounded cobbles: each cell gets a lit top-left and a dark gap."""
    for (x, y) in mask:
        cx, cy = x % 10, (y + (x // 10) % 2 * 4) % 8
        gap = cx == 0 or cy == 0
        n = noise2(x // 10, (y + (x // 10) % 2 * 4) // 8, 81)
        base = SLATE[3] if n < 0.5 else '#A7A291'
        col = SLATE[1] if gap else (SLATE[4] if (cx <= 2 and cy <= 2) else SLATE[2] if (cx >= 8 or cy >= 6) else base)
        cv.set(x, y, col)
    for (x, y) in mask:
        if (x, y - 1) not in mask:
            cv.set(x, y, SLATE[0])


def paint_water(cv, mask, frame=0, center=None):
    bank = set()
    for (x, y) in mask:
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                n = (x + dx, y + dy)
                if n not in mask and 0 <= n[0] < W and 0 <= n[1] < H:
                    bank.add(n)
    for (x, y) in bank:
        cv.set(x, y, g.SAND[1] if noise2(x, y, 21) < 0.8 else g.SAND[2])
    for (x, y) in mask:
        col = g.WTR[1] if all((x + dx, y + dy) in mask for dx, dy in ((-4, 0), (4, 0), (0, -3), (0, 3))) else g.WTR[2]
        if (x, y - 1) not in mask:
            col = g.WTR[0]
        elif (x, y - 2) not in mask:
            col = g.WTR[1]
        cv.set(x, y, col)
    # Jittered little arcs share stable roots between poses. Keep the bank
    # still, instead of making the whole stream appear to slide sideways.
    for ty in range(0, H, 6):
        for tx in range(0, W, 7):
            if noise2(tx, ty, 37) > 0.48:
                continue
            x = tx + int(noise2(tx, ty, 38) * 5)
            y = ty + int(noise2(tx, ty, 39) * 4)
            shift = frame if noise2(tx, ty, 40) < 0.4 else 0
            if all((x + dx, y) in mask for dx in (-1, 0, 1, 2, 3, 4)) and (x, y - 2) in mask:
                cv.hline(x + shift, y, 3, g.WTR[3])
                if noise2(tx, ty, 41) < 0.22:
                    cv.set(x + shift, y - 1, g.WTR[4])
    return bank


def flowerbed(cv, x, y, w, h, seed=0):
    """The garden's raised flower planters (garden_meadow.flower_planter)."""
    import garden_meadow
    garden_meadow.flower_planter(cv, x, y, w, max(h, 18), seed=seed)


def roof_tiles(cv, mask, ramp, row_height=3):
    """Overlapping clay/slate courses, always lit from the upper left.

    Reuse material construction, not the same roof silhouette. The supplied
    mask remains the owner of the building's shape and size.
    """
    for x, y in mask:
        seam = (x + (y // row_height % 2) * 3) % 7 == 0
        col = ramp[1] if seam else ramp[3] if y % row_height == 0 else ramp[2]
        if (x - 1, y) not in mask:
            col = ramp[0]
        elif (x + 1, y) not in mask:
            col = ramp[1]
        elif (x, y - 1) not in mask:
            col = ramp[4]
        cv.set(x, y, col)


def window(cv, x, y, w, h, warm=False):
    """Recessed glazing: one highlight, a timber sill and a darker right edge."""
    cv.rect(x, y, w, h, g.WOOD[0])
    cv.rect(x + 1, y + 1, w - 2, h - 2, '#D8B86F' if warm else '#6E8FA4')
    cv.vline(x + 1, y + 1, h - 2, '#F7E6AE' if warm else '#BCD6DA')
    cv.hline(x + 1, y + 1, w - 2, '#FFF0C8' if warm else '#DCEBE6')
    if w >= 7:
        cv.vline(x + w // 2, y + 1, h - 2, g.WOOD[2])
    if h >= 10:
        cv.hline(x + 1, y + h // 2, w - 2, g.WOOD[2])
    cv.hline(x - 1, y + h, w + 2, g.WOOD[3])
    cv.hline(x, y + h + 1, w + 1, g.WOOD[1])


# ---- props ------------------------------------------------------------------
# Drawn in world_props.py at the shared density; trees come from the garden.
SPRITES = wp.props()


# ---- worlds -------------------------------------------------------------------
def world_park(frame):
    cv = Canvas(W, H)
    grass(cv, frame)
    plaza = disc(160, 167, 46)
    paths = thick([(160, 300), (160, 167)], 13) | thick([(-6, 167), (333, 167)], 12) | thick([(160, 167), (160, 50)], 10)
    paint_paving(cv, (plaza | paths) & {(x, y) for x in range(W) for y in range(40, H)})
    water = {(x, y) for (x, y) in oval(263, 248, 40, 21)}
    paint_water(cv, water, frame)
    for lx, ly in ((247, 244), (280, 251)):
        for x, y in oval(lx, ly, 4.5, 3):
            cv.set(x, y, g.LEAF[3] if y < ly else g.LEAF[2])
        cv.set(lx + 1, ly - 2, g.WTR[2]); cv.hline(lx - 2, ly, 3, g.LEAF[1])
    cv.set(280, 249, g.NAP[4])
    for x, y in ((231, 236), (290, 236), (295, 256)):
        cv.vline(x, y - 6, 7, g.LEAF[1]); cv.set(x + 1, y - 3, g.LEAF[3]); cv.vline(x + 2, y - 4, 5, g.LEAF[2])
    for x, y in ((235, 265), (270, 271)):
        cv.hline(x, y, 6, g.STONE[1]); cv.hline(x + 1, y - 1, 4, g.STONE[3]); cv.set(x + 1, y - 2, g.STONE[4])
    for fb in ((30, 200, 50, 20, 0), (30, 108, 50, 20, 1), (236, 98, 52, 20, 2)):
        flowerbed(cv, *fb)
    objects = [
        *[(f'pine-{i}', 'pine', x, -34 + (i % 2) * 6) for i, x in enumerate(range(-14, 330, 25))],
        ('tree-0', 'tree', -20, -27), ('tree-1', 'tree_autumn', 250, -30), ('tree-2', 'tree', 284, 34),
        ('tree-3', 'tree', -20, 230), ('tree-4', 'tree_small', 92, 222),
        ('hedge-l', 'hedge', 10, 50), ('hedge-r', 'hedge', 214, 50),
        ('fountain', 'fountain', 132, 127), ('bench-1', 'bench', 60, 124), ('bench-2', 'bench', 216, 124),
        ('lamp-1', 'lamp', 108, 104), ('lamp-2', 'lamp', 198, 104), ('lamp-3', 'lamp', 108, 196), ('lamp-4', 'lamp', 198, 196),
        ('bush-1', 'bush', 46, 254), ('bush-2', 'bush', 196, 252), ('duck', 'duck', 250, 238),
    ]
    route = [(160, 268), (160, 212), (100, 176), (66, 186), (130, 236), (214, 220), (240, 186), (214, 172), (160, 222)]
    return cv, objects, water, route, (226, 214)


def world_town(frame):
    cv = Canvas(W, H)
    grass(cv, frame)
    street = {(x, y) for x in range(W) for y in range(140, 194)}
    lane = thick([(160, 193), (160, 300)], 15)
    paint_cobbles(cv, street | lane)
    paint_paving(cv, {(x, y) for x in range(W) for y in range(117, 140)}, seed=2)
    for x, y in ((10, 135), (303, 135), (40, 190), (287, 188), (132, 258)):
        cv.set(x, y, g.LEAF[2]); cv.set(x + 1, y - 1, g.LEAF[3]); cv.set(x + 2, y, g.LEAF[2])
    for fb in ((17, 214, 37, 17, 1), (266, 214, 37, 17, 3)):
        flowerbed(cv, *fb)
    objects = [
        *[(f'pine-{i}', 'pine', x, -24 + (i % 2) * 6) for i, x in enumerate(range(-14, 330, 25))],
        ('tree-b0', 'tree', 60, -24), ('tree-b1', 'tree_small', 206, -10),
        ('house-l', 'house_red', 0, 44), ('library', 'library', 96, 20), ('house-r', 'house_blue', 240, 44),
        ('lamp-1', 'lamp', 82, 98), ('lamp-2', 'lamp', 225, 98), ('lamp-3', 'lamp', 50, 206), ('lamp-4', 'lamp', 256, 206),
        ('cafe-1', 'cafe', 190, 204), ('cafe-2', 'cafe', 230, 242), ('cart', 'cart', 94, 206),
        ('tree-0', 'tree', -20, 220), ('tree-1', 'tree_small', 104, 228), ('tree-2', 'tree', 276, 232),
        ('bush-1', 'bush', 20, 113), ('bush-2', 'bush', 272, 113),
    ]
    route = [(160, 266), (160, 174), (100, 160), (66, 168), (160, 152), (250, 168), (200, 180), (160, 214)]
    return cv, objects, set(), route, (118, 180)


def world_mountain(frame):
    cv = Canvas(W, H)
    alpine = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
    grass(cv, frame, alpine)
    for y in range(0, 100):  # snowfield at the top
        for x in range(W):
            edge_y = 57 + int(17 * math.sin(x / 32) + 7 * math.sin(x / 12))
            if y < edge_y:
                # calm snow: one bright plane with a few broad, soft drifts
                cv.set(x, y, SNOW[2] if smooth_noise(x, y, 40, 5) < 0.3 else SNOW[3])
                # a blue underside gives the scalloped snow shelf thickness
                if y >= edge_y - 3:
                    cv.set(x, y, SNOW[1] if y < edge_y - 1 else SNOW[0])
    for x, y in ((88, 78), (197, 57), (252, 68)):
        cv.hline(x, y, 10, SNOW[1]); cv.hline(x + 1, y - 1, 8, SNOW[3])
    trail = thick([(117, 300), (123, 250), (183, 207), (167, 160), (110, 133), (143, 87)], 10, seed=3)
    paint_dirt(cv, trail)
    stream = thick([(333, 117), (283, 140), (250, 183), (260, 233), (233, 300)], 8, seed=4)
    paint_water(cv, stream, frame)
    for x, y in ((263, 163), (276, 226), (222, 277)):
        cv.hline(x, y, 8, MOSSROCK[0]); cv.hline(x, y - 1, 7, MOSSROCK[2]); cv.set(x + 1, y - 2, MOSSROCK[4])
    objects = [
        *[(f'pine-{i}', 'pine', x, 30 + (i % 3) * 10) for i, x in enumerate(range(-10, 100, 22))],
        *[(f'pine-r{i}', 'pine', x, 196 + (i % 2) * 14) for i, x in enumerate(range(276, 340, 24))],
        ('cabin', 'cabin', 10, 104), ('campfire', 'campfire', 104, 180), ('cairn', 'cairn', 157, 53),
        ('boulder-1', 'boulder', 196, 104), ('boulder-2', 'boulder', 36, 238), ('stone-1', 'stone', 206, 254),
        ('stone-2', 'stone', 70, 216), ('bridge', 'bridge', 228, 166),
        ('pine-a', 'pine', 172, 214), ('pine-b', 'pine', 134, 226),
    ]
    route = [(123, 272), (150, 228), (184, 204), (167, 164), (124, 184), (112, 140), (143, 100), (160, 104), (133, 128), (167, 172)]
    return cv, objects, stream, route, (172, 112)


WORLDS = {'park': world_park, 'book': world_town, 'mountain': world_mountain}


# ---- horizon backdrops for the 2.5D view -------------------------------------
def sky(cv, horizon, bands):
    for y in range(horizon):
        i = min(len(bands) - 1, int(y / horizon * len(bands)))
        cv.hline(0, y, cv.w, bands[i])
        if i and y == int(i * horizon / len(bands)):
            for x in range(y % 2, cv.w, 2):
                cv.set(x, y, bands[i - 1])


def distant_cloud(cv, cx, cy, scale=1.0):
    cloud = set()
    for dx, dy, rx, ry in ((-9, 2, 8, 3), (-2, -1, 9, 5), (7, 0, 8, 4), (14, 3, 6, 2)):
        cloud |= oval(cx + dx * scale, cy + dy * scale, rx * scale, ry * scale)
    for x, y in cloud:
        cv.set(x, y, '#C9DCE3' if (x, y + 1) not in cloud else '#EEF2E7' if (x, y - 2) in cloud else '#FBF4E4')


def backdrop(kind) -> Canvas:
    bw, bh, horizon = 216, 150, 80
    cv = Canvas(bw, bh)
    sky(cv, horizon, ['#A9D3E6', '#C3E0EA', '#DCEBE6', '#EEF2DF'])
    for cx, cy, scale in ((26, 17, 0.8), (108, 9, 0.65), (179, 23, 0.9)):
        distant_cloud(cv, cx, cy, scale)
    if kind == 'mountain':
        for (px, ph, sw) in ((40, 62, 48), (120, 70, 60), (190, 56, 44)):
            for x in range(bw):
                top = horizon - ph + abs(x - px) * ph / sw
                for y in range(int(top), horizon + 2):
                    # Snow follows broken shelves rather than a checkerboard.
                    snowline = horizon - ph * 0.55 + int(3 * math.sin(x / 6 + px))
                    snow = y < snowline
                    lit = x < px
                    ridge = abs(x - px + (y - horizon + ph) * 0.25) < 1.5
                    cv.set(x, y, (SNOW[3] if lit else SNOW[1]) if snow else SLATE[3] if lit and ridge else '#7D8BA0' if lit else '#5E6B82')
    elif kind == 'book':
        # A distant neighbourhood of gables, not repeated modern tower blocks.
        # Low-contrast silhouettes keep the nearby library the clear landmark.
        for i, x in enumerate(range(-5, bw, 24)):
            hgt = 15 + (i * 7) % 13
            roof_y = horizon - hgt
            for y in range(horizon - hgt, horizon + 2):
                for xx in range(x + 2, x + 21):
                    cv.set(xx, y, '#A2B2AF' if xx < x + 15 else '#8A9CA2')
            for y in range(roof_y - 8, roof_y + 1):
                half = 2 + (y - roof_y + 8) * 1.2
                for xx in range(int(x + 11 - half), int(x + 11 + half)):
                    cv.set(xx, y, '#7B8C9E' if xx < x + 11 else '#6C8091')
            for wy in range(roof_y + 4, horizon - 2, 6):
                for wx in (x + 6, x + 15):
                    cv.rect(wx, wy, 2, 3, '#D6DECF'); cv.set(wx + 1, wy + 2, '#8A9CA2')
            if i % 3 == 0:
                cv.rect(x + 16, roof_y - 7, 3, 7, '#8792A4')
    # Layers share the battle meadow's atmospheric palette. Native clustered
    # canopies soften the world edge without importing foreground tree detail.
    for x in range(bw):
        far = horizon - 12 - int(4 * math.sin(x / 23) + 2 * math.sin(x / 9 + 1))
        for y in range(far, bh):
            cv.set(x, y, '#97BBA6' if y == far else '#A7C7B4')
    for i, x in enumerate(range(-3, bw + 8, 9)):
        base = horizon - 1 + i % 3
        if kind != 'mountain' and i % 3 == 1:
            for px, py in oval(x, base - 8, 5.5, 5.5):
                cv.set(px, py, '#6E9F78' if px < x else '#5B8D6B')
            cv.vline(x, base - 3, 4, '#64765C')
        else:
            hgt = 12 + i * 5 % 8
            for y in range(hgt):
                half = int(y * 0.36) + 1
                for px in range(x - half, x + half + 1):
                    cv.set(px, base - hgt + y, '#547E65' if px < x else '#416C59')
    for x in range(bw):
        near = horizon - 3 - int(2 * math.sin(x / 13) + 2 * math.sin(x / 5))
        for y in range(near, bh):
            cv.set(x, y, '#6E9F6B' if y < horizon + 4 else '#7CAE66')
    return cv


FLAT = {'bridge'}  # drawn into the ground, never layered over characters
SPRITES['bridge'] = wp.bridge(46, 32)


TOPW = 48  # a forest band above each world, so its treeline is drawn whole
WALK_TOP = 72 + TOPW  # the companion's feet stay below the treeline


def forest_band(cv: Canvas, wid: str = ''):
    """Forest floor under the treeline (or snowy rock above the mountain's snowfield):
    deep shade dithering into the ground below."""
    if wid == 'mountain':
        for y in range(TOPW):
            for x in range(W):
                cv.set(x, y, SLATE[1] if y < TOPW - 10 else SNOW[1] if y < TOPW - 4 else SNOW[2])
        style.dither_dark(cv, 0, 0, W, TOPW - 16, 1.0, SLATE[0])
        style.dither_dark(cv, 0, TOPW - 16, W, 6, 0.5, SLATE[0])
        return
    for y in range(TOPW):
        for x in range(W):
            cv.set(x, y, g.G[1] if y < TOPW - 4 else g.G[2])
    style.dither_dark(cv, 0, 0, W, TOPW - 12, 1.0, style.FOREST_DARK)
    style.dither_dark(cv, 0, TOPW - 12, W, 4, 0.75, style.FOREST_DARK)
    style.dither_dark(cv, 0, TOPW - 8, W, 4, 0.5, style.FOREST_DARK)
    style.dither_dark(cv, 0, TOPW - 4, W, 4, 0.25, style.FOREST_DARK)


def shifted(cv: Canvas, wid: str) -> Canvas:
    out = Canvas(W, H + TOPW)
    forest_band(out, wid)
    out.paste(cv, 0, TOPW)
    return out


def main():
    worlds = {}
    all_props = {}
    sprites = {key: style.finalize(sp, name=key) for key, sp in SPRITES.items()}
    water_files = {}
    for wid, fn in WORLDS.items():
        os.makedirs(os.path.join(OUT, wid), exist_ok=True)
        for old in os.listdir(os.path.join(OUT, wid)):
            os.remove(os.path.join(OUT, wid, old))
        frames, (objects, water, route, visitor) = [], (None, None, None, None)
        for frame in (0, 1):
            cv, objects, water, route, visitor = fn(frame)
            frames.append(shifted(cv, wid))
        # nominal boxes in the shifted map, then each trimmed sprite placed by its offset
        objects = [(i, k, x + sprites[k].ox, y + TOPW + sprites[k].oy) for (i, k, x, y) in objects]
        for (i, k, x, y) in objects:
            assert y >= 0, f'{wid}/{i} reaches {-y} px above the world'
        route = [(x, y + TOPW) for (x, y) in route]
        visitor = (visitor[0], visitor[1] + TOPW)
        water = {(x, y + TOPW) for (x, y) in water}
        # flat, walkable decals (bridges) belong to the ground layer (coherence plan, step 1)
        flat = [(sprites[k], x, y) for (_i, k, x, y) in objects if k in FLAT]
        objects = [o for o in objects if o[1] not in FLAT]
        for cv in frames:
            for (decal, fx, fy) in flat:
                cv.paste(decal, fx, fy)
            for (_id, key, x, y) in objects:  # flat cast shadows and contact shade, as in the garden
                sp = sprites[key]
                foot = y + sp.h
                if key in ('tree', 'tree_small', 'tree_autumn'):
                    style.cast_shadow(cv, x + sp.w / 2 + 5, foot - 2, sp.w * 0.46, 6)
                elif key == 'pine':
                    style.cast_shadow(cv, x + sp.w / 2 + 3, foot - 1, sp.w * 0.42, 4.5)
                elif key == 'hedge':
                    for xx in range(x + 2, x + sp.w + 2):
                        for dy in (0, 1, 2):
                            style.darken(cv, xx, foot + dy)
                elif sp.w > 60:  # buildings
                    for yy in range(foot - 4, foot + 4):
                        for xx in range(x + 4 + (yy - foot + 4), x + sp.w + 4):
                            style.darken(cv, xx, yy)
                else:
                    style.cast_shadow(cv, x + sp.w / 2 + 3, foot, max(4.5, sp.w * 0.48), max(2.6, sp.h * 0.1))
                for xx in range(sp.w):
                    if sp.get(xx, sp.h - 1)[3]:
                        style.darken(cv, x + xx, foot)
        frames[0].save(os.path.join(OUT, wid, 'ground.png'), SCALE)
        overlays = []
        if water:
            xs = [x for x, _ in water]
            ys = [y for _, y in water]
            rx, ry = max(0, min(xs) - 4), max(0, min(ys) - 4)
            rw, rh = min(W, max(xs) + 5) - rx, min(H + TOPW, max(ys) + 5) - ry
            for y in range(H + TOPW):
                for x in range(W):
                    if frames[1].get(x, y) != frames[0].get(x, y):
                        assert rx <= x < rx + rw and ry <= y < ry + rh, f'{wid} animates outside its water at {x},{y}'
            for i, fcv in enumerate(frames):
                crop = Canvas(rw, rh)
                for y in range(rh):
                    for x in range(rw):
                        crop.px[x, y] = fcv.get(rx + x, ry + y)
                crop.save(os.path.join(OUT, wid, f'water-{i}.png'), SCALE)
            overlays = [{'x': rx, 'y': ry, 'w': rw, 'h': rh}]
        water_files[wid] = bool(water)
        for (_id, key, x, y) in objects:
            all_props[key] = sprites[key]
        # walk grid: not water, not object footprints, inside the scene margins
        blocked = {(x // CELL, y // CELL) for (x, y) in water}
        for (_id, key, x, y) in objects:
            sp = sprites[key]
            foot = 20 if sp.w > 60 else 10 if key in ('tree', 'tree_small', 'tree_autumn', 'pine') else 7
            for yy in range(y + sp.h - foot, y + sp.h):
                for xx in range(x + 3, x + sp.w - 3):
                    blocked.add((xx // CELL, yy // CELL))
        walk = []
        for r in range((H + TOPW) // CELL):
            row = ''
            for c in range(W // CELL):
                cx, cy = c * CELL + 2, r * CELL + 2
                ok = (c, r) not in blocked and 16 <= cx <= W - 16 and WALK_TOP <= cy <= H + TOPW - 16
                row += '.' if ok else '#'
            walk.append(row)
        bad = [(x, y - TOPW) for (x, y) in route + [visitor] if walk[y // CELL][x // CELL] != '.']
        assert not bad, f'{wid}: route or visitor points not walkable (layout coordinates): {bad}'
        worlds[wid] = {
            'objects': [{'id': i, 'sprite': k, 'x': x, 'y': y, 'w': sprites[k].w, 'h': sprites[k].h} for (i, k, x, y) in objects],
            'walk': walk,
            'route': [{'x': x, 'y': y} for (x, y) in route],
            'visitor': {'x': visitor[0], 'y': visitor[1]},
            'water': overlays,
        }
        prev = Canvas(W, H + TOPW)
        prev.paste(frames[0], 0, 0)
        for (_id, key, x, y) in sorted(objects, key=lambda o: o[3] + sprites[o[1]].h):
            prev.paste(sprites[key], x, y)
        prev.save(os.path.join(os.environ.get('WORLD_PREVIEW', '/tmp'), f'world-{wid}.png'), 2)
    props_dir = os.path.join(OUT, 'props')
    os.makedirs(props_dir, exist_ok=True)
    for old in os.listdir(props_dir):
        os.remove(os.path.join(props_dir, old))
    for key, sp in sorted(all_props.items()):
        sp.save(os.path.join(props_dir, f'{key}.png'), SCALE)
    # Static image imports (React Native needs literal paths), generated so they never drift.
    ident = lambda k: ''.join(p.capitalize() for p in k.split('_'))  # noqa: E731
    imp = [f"import prop{ident(k)} from '@/assets/worlds/props/{k}.png';" for k in sorted(all_props)]
    for wid in WORLDS:
        imp.append(f"import {wid}Ground from '@/assets/worlds/{wid}/ground.png';")
        if water_files[wid]:
            imp += [f"import {wid}Water{i} from '@/assets/worlds/{wid}/water-{i}.png';" for i in (0, 1)]
    assets = [
        '// Generated by scripts/art/worlds.py. Do not edit by hand.',
        '/* eslint-disable */',
        "import type { ImageSourcePropType } from 'react-native';",
        *imp,
        'export const worldProps: Record<string, ImageSourcePropType> = {',
        *[f'  {k}: prop{ident(k)},' for k in sorted(all_props)],
        '};',
        '/** One still ground per world; water animates as two-frame overlays. */',
        'export const worldImages: Record<string, { ground: ImageSourcePropType; water: ImageSourcePropType[] }> = {',
        *[f'  {wid}: {{ ground: {wid}Ground, water: [{f"{wid}Water0, {wid}Water1" if water_files[wid] else ""}] }},' for wid in WORLDS],
        '};',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'world-assets.ts'), 'w') as f:
        f.write('\n'.join(assets))
    ts = [
        '// Generated by scripts/art/worlds.py. Do not edit by hand.',
        '/* eslint-disable */',
        f'export const WORLD = {{ width: {W}, height: {H + TOPW}, top: {TOPW}, scale: {SCALE}, cell: {CELL} }} as const;',
        f'export const worldIds = {json.dumps(list(WORLDS))} as const;',
        'export type WorldId = (typeof worldIds)[number];',
        'export const isWorldId = (value: string): value is WorldId => worldIds.some((id) => id === value);',
        'export type WorldMap = { objects: readonly { id: string; sprite: string; x: number; y: number; w: number; h: number }[]; walk: readonly string[]; route: readonly { x: number; y: number }[]; visitor: { x: number; y: number }; water: readonly { x: number; y: number; w: number; h: number }[] };',
        f'export const worldMaps: Record<WorldId, WorldMap> = {json.dumps(worlds)};',
        '',
    ]
    with open(os.path.join(ROOT, 'lib', 'world-maps.ts'), 'w') as f:
        f.write('\n'.join(ts))
    print('ok', ', '.join(worlds))


if __name__ == '__main__':
    main()
