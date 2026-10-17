"""The way beyond the garden gate as a real place (living-world plan, L1).

Run: python3 scripts/art/mission_map.py
Writes assets/missions/map.png (one still image) and lib/mission-map.ts (the places'
tap areas, the points where the companion stands, and the frame size).

The garden gate stands at the bottom; sandy roads branch to the park's fountain, the
library, the mountain cabin, Moss's stall (the shop) and the sparring ring (the
battle zone). Everything is drawn with the garden's rules (detail.py): the steep
top-down buildings, ragged turf on the roads, silhouette shadows and tufts. The
map is scenery: the app lays its tap areas and name tags over it.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval, smooth_noise  # noqa: E402
import detail  # noqa: E402
import garden_props as gp  # noqa: E402
import world_props as wp  # noqa: E402
import style  # noqa: E402
from materials import G, P, STONE, WOOD, RED, LEAF, SNOW, SAND, WTR  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'missions')
W, H, SCALE = 320, 300, 4

# Where each place stands: its landmark's prop, the landmark's centre-x and foot, the
# point the companion walks to, the tap area (x, y, w, h) and the name tag's top centre,
# in map pixels. Tags sit inside the part of the map every phone shows.
PLACES = {
    'book': {'prop': 'library', 'cx': 84, 'foot': 118, 'stand': (84, 132), 'tap': (22, 30, 124, 104), 'label': (84, 40)},
    'mountain': {'prop': 'cabin', 'cx': 254, 'foot': 112, 'stand': (236, 118), 'tap': (198, 26, 112, 100), 'label': (232, 40)},
    'park': {'prop': 'fountain', 'cx': 62, 'foot': 226, 'stand': (96, 232), 'tap': (20, 172, 96, 70), 'label': (62, 176)},
    'shop': {'prop': 'stall', 'cx': 262, 'foot': 214, 'stand': (238, 226), 'tap': (214, 138, 98, 84), 'label': (238, 142)},
    'arena': {'prop': None, 'cx': 222, 'foot': 270, 'stand': (204, 270), 'tap': (178, 236, 92, 50), 'label': (222, 238)},
    'garden': {'prop': 'gate', 'cx': 140, 'foot': 296, 'stand': (140, 284), 'tap': (112, 252, 56, 48), 'label': (140, 254)},
}
CROSS = (140, 182)


def road(points, radius):
    pts = set()
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = radius + (noise2(int(cx) // 6, int(cy) // 6, 3) - 0.5) * 1.6
            for y in range(int(cy - r) - 1, int(cy + r) + 2):
                for x in range(int(cx - r) - 1, int(cx + r) + 2):
                    if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and 0 <= x < W and 0 <= y < H:
                        pts.add((x, y))
    return pts


# The mountain is a raised terrace in the top-right corner: alpine ground with rock and
# snow, peaks behind the cabin, and a stone face where it drops to the meadow. The road
# climbs the face as steps. Snow only lies up here.
FACE = 12


def terrace_edge(x: int) -> int | None:
    """The terrace's lip (the top of its stone face) at column x, or None off the terrace."""
    if x < 178:
        return None
    wobble = int((noise2(x // 5, 3, 83) - 0.5) * 3)
    if x < 206:
        return 120 - int((206 - x) * 2.0) + wobble
    return 120 + wobble


def on_terrace(x: int, y: int) -> bool:
    edge = terrace_edge(x)
    return edge is not None and y < edge


def peaks(cv: Canvas):
    """Two rock peaks behind the cabin: a lit west face and a shaded east face split at
    the ridge, ledges across both, a snow cap with a zigzag hem, an outline."""
    mask = {}
    for (ax, ay, half, base) in ((292, 2, 50, 62), (226, -6, 46, 56)):
        for y in range(max(0, ay), base):
            spread = (y - ay) / (base - ay) * half
            ridge = ax + int((y - ay) * 0.18)
            for x in range(int(ax - spread), int(ax + spread * 0.9) + 1):
                if not (0 <= x < W):
                    continue
                lit = x < ridge
                ledge = (y - ay + (x if lit else -x) // 4) % 9 == 0 and noise2(x // 5, y // 9, 85) < 0.6
                c = STONE[(3 if noise2(x // 6, y // 6, 86) > 0.3 else 2) if lit else 1]
                if ledge:
                    c = STONE[1] if lit else STONE[0]
                hem = ay + 18 + abs((x + ax) % 8 - 4) + int(noise2(x // 8, ax, 87) * 5)
                if y < hem:
                    c = SNOW[3] if lit else SNOW[1]
                elif y == hem:
                    c = SNOW[1] if lit else SNOW[0]
                mask[(x, y)] = c
    for (x, y), c in mask.items():
        if (x - 1, y) not in mask or (x + 1, y) not in mask or (y > 0 and (x, y - 1) not in mask):
            c = STONE[0]
        cv.set(x, y, c)


def mountain_terrace(cv: Canvas, roads: set):
    peaks_mask = set()
    for y in range(H):
        for x in range(W):
            if not on_terrace(x, y) or (x, y) in roads:
                continue
            rock = smooth_noise(x, y, 9, 81) > 0.55
            snow = smooth_noise(x, y, 11, 82) > 0.3 + y / 120 * 0.4
            if snow:
                c = SNOW[3] if smooth_noise(x, y, 4, 87) > 0.45 else SNOW[2]
                if not on_terrace(x, y + 1) or smooth_noise(x, y + 1, 11, 82) <= 0.3 + (y + 1) / 120 * 0.4:
                    c = SNOW[1]
            elif rock:
                c = STONE[2]
                if smooth_noise(x, y - 1, 9, 81) <= 0.55:
                    c = STONE[4]
                elif smooth_noise(x, y + 1, 9, 81) <= 0.55:
                    c = STONE[1]
                elif noise2(x, y, 88) < 0.12:
                    c = STONE[3]
            else:
                c = G[2] if smooth_noise(x, y, 6, 89) > 0.4 else G[1]
                if noise2(x, y, 90) < 0.05:
                    c = G[3]
            cv.set(x, y, c)
    for (x, y) in roads:
        if on_terrace(x, y):
            cv.set(x, y, STONE[3] if smooth_noise(x, y, 5, 91) > 0.55 else STONE[2])
    peaks(cv)
    # the face: stacked stones under a lit lip, steps where the road climbs it
    for x in range(178, W):
        top = terrace_edge(x)
        col = (x + int(noise2(x // 6, 1, 92) * 6)) % 6
        si = (x + int(noise2(x // 6, 1, 92) * 6)) // 6
        for k in range(FACE):
            y = top + k
            if not (0 <= y < H):
                continue
            if (x, y) in roads or (x, top - 1) in roads and (x, top + FACE) in roads:
                c = STONE[4] if k % 3 == 0 else STONE[2] if k % 3 == 1 else STONE[1]
                if (x - 1, y) not in roads or (x + 1, y) not in roads:
                    c = STONE[0]
            elif k == 0:
                c = STONE[4]
            else:
                row = (k - 1 + (si % 2) * 2) // 4
                r = (k - 1 + (si % 2) * 2) % 4
                base = 3 if noise2(si, row, 93) > 0.45 else 2
                if col == 5 or r == 3:
                    c = STONE[0]
                elif col == 0 or r == 0:
                    c = STONE[base + 1]
                elif col == 4:
                    c = STONE[base - 1]
                else:
                    c = STONE[base]
                if k == FACE - 1 and col != 5:
                    c = STONE[1]
            cv.set(x, y, c)
        for k in range(2):  # the face's shadow on the meadow below
            y = top + FACE + k
            if 0 <= y < H and (k == 0 or x % 2 == 0):
                style.darken(cv, x, y)


def ground() -> tuple[Canvas, set]:
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            n = smooth_noise(x, y, 30, 11)
            light = n > 0.66 or (n > 0.62 and (x + y) % 2 == 0)
            cv.set(x, y, G[3] if light else G[2])
    for ty in range(0, H, 6):
        for tx in range(0, W, 6):
            x, y = tx + int(noise2(tx, ty, 4) * 6), ty + int(noise2(tx, ty, 5) * 6)
            if noise2(tx, ty, 3) < 0.3:
                g = 3 if cv.get(x, y)[:3] == tuple(int(G[3][k:k + 2], 16) for k in (1, 3, 5)) else 2
                detail.grass_tuft(cv, x, y, int(noise2(tx, ty, 8) * 6), G, g)
            elif noise2(tx, ty, 7) < 0.06:
                cv.set(x, y, '#E9E4CF'); cv.set(x, y + 1, G[1])
    roads = set()
    roads |= road([PLACES['garden']['stand'], (140, 250), CROSS], 12)
    roads |= road([CROSS, (120, 160), PLACES['book']['stand']], 10)
    roads |= road([CROSS, (190, 150), PLACES['mountain']['stand']], 10)
    roads |= road([CROSS, (110, 206), PLACES['park']['stand']], 10)
    roads |= road([CROSS, (196, 200), PLACES['shop']['stand']], 10)
    roads |= road([(146, 240), PLACES['arena']['stand']], 9)
    # where the roads meet: one trodden clearing rather than a bare X
    roads |= road([CROSS, (CROSS[0], CROSS[1] + 2)], 17)
    for (x, y) in roads:
        cv.set(x, y, P[4] if smooth_noise(x, y, 7, 40) > 0.7 else P[3])
    for i in range(120):
        x, y = int(noise2(i, 0, 52) * W), int(noise2(i, 1, 52) * H)
        if all((x + dx, y + dy) in roads for dx in (-2, 0, 3) for dy in (-2, 0, 3)):
            detail.pebble(cv, x, y, STONE, big=i % 4 == 0)
    detail.grass_edge(cv, roads, G, P, seed=31)
    mountain_terrace(cv, roads)
    # the sparring ring: a trodden circle edged with stones, two turf mounds
    ax, ay = PLACES['arena']['cx'], PLACES['arena']['foot'] - 10
    ring = oval(ax, ay, 34, 14)
    for (x, y) in ring:
        cv.set(x, y, P[3] if smooth_noise(x, y, 6, 9) > 0.55 else P[2])
    detail.grass_edge(cv, ring, G, P, seed=33)
    for k in range(18):
        a = 2 * math.pi * k / 18
        sx, sy = int(ax + 36 * math.cos(a)), int(ay + 15.5 * math.sin(a))
        detail.pebble(cv, sx, sy, STONE, big=k % 2 == 0)
    return cv, roads


def ts_object(value, depth=0) -> str:
    """A dict of ints as TypeScript, laid out the way oxfmt formats it."""
    if not isinstance(value, dict):
        return str(value)
    pad = '  ' * (depth + 1)
    rows = [f'{pad}{key}: {ts_object(item, depth + 1)},' for key, item in value.items()]
    return '{\n' + '\n'.join(rows) + '\n' + '  ' * depth + '}'


def main():
    os.makedirs(OUT, exist_ok=True)
    cv, roads = ground()
    sprites = []

    def place(sprite_raw, cx, foot):
        s = style.finalize(sprite_raw, name='map-prop')
        sprites.append((s, int(round(cx - sprite_raw.w / 2)) + s.ox, foot - sprite_raw.h + s.oy))

    props = {'library': wp.library, 'cabin': wp.cabin, 'fountain': wp.fountain, 'stall': gp.stall, 'gate': gp.gate}
    for pid, p in PLACES.items():
        if p['prop']:
            place(props[p['prop']](), p['cx'], p['foot'])
    # the arena's mounds and a pennant pole
    for dx in (-18, 18):
        mound = Canvas(30, 12)
        for (x, y) in oval(15, 6, 14, 5):
            mound.set(x, y, G[4] if y < 5 and x < 15 else G[3] if y < 7 else P[1])
        place(mound, PLACES['arena']['cx'] + dx, PLACES['arena']['foot'] - 6)
    pole = Canvas(16, 34)
    gp.post(pole, 1, 4, 34, w=3)
    for y in range(5, 14):
        for x in range(4, 4 + max(1, 12 - (y - 5))):
            pole.set(x, y, RED[3] if y < 9 else RED[2])
    pole.hline(4, 5, 11, RED[4])
    place(pole, PLACES['arena']['cx'] + 40, PLACES['arena']['foot'] - 2)
    # framing: trees, pines, bushes, lamps, benches, crates
    for (key, cx, foot) in (('tree', 14, 92), ('tree_small', 168, 74), ('pine', 186, 112), ('pine', 306, 126),
                            ('tree', 6, 262), ('bush', 120, 248), ('bush', 168, 246), ('tree_small', 300, 280),
                            ('pine', 18, 160), ('bush', 196, 136), ('lamp', 112, 226), ('bench', 30, 252),
                            ('barrel', 304, 222), ('crate', 210, 220), ('potted_plant', 40, 130),
                            ('potted_plant', 128, 130), ('boulder', 290, 150), ('stone', 196, 100), ('signpost', 114, 188)):
        source = {'tree': lambda: gp.tree(True), 'tree_small': lambda: gp.tree(False), 'pine': gp.pine,
                  'bush': gp.bush, 'lamp': wp.lamp, 'bench': wp.bench, 'barrel': gp.barrel,
                  'crate': gp.crate, 'potted_plant': gp.potted_plant,
                  'signpost': gp.signpost, 'boulder': wp.boulder, 'stone': lambda: wp.boulder(False)}[key]
        place(source(), cx, foot)
    shade = set()
    for s, x, y in sprites:
        shade |= detail.silhouette_shadow(s, x, y)
    for (sx, sy) in shade:
        style.darken(cv, sx, sy)
    for s, x, y in sorted(sprites, key=lambda item: item[2] + item[0].h):
        cv.paste(s, x, y)
    cv.save(os.path.join(OUT, 'map.png'), SCALE)
    places = {pid: {'stand': {'x': p['stand'][0], 'y': p['stand'][1]},
                    'tap': dict(zip(('x', 'y', 'w', 'h'), p['tap'])),
                    'label': {'x': p['label'][0], 'y': p['label'][1]}} for pid, p in PLACES.items()}
    with open(os.path.join(ROOT, 'lib', 'mission-map.ts'), 'w') as f:
        f.write('\n'.join([
            '// Generated by scripts/art/mission_map.py. Do not edit by hand.',
            "import type { ImageSourcePropType } from 'react-native';",
            "import mapImage from '@/assets/missions/map.png';",
            f'export const missionMap = {{ width: {W}, height: {H} }} as const;',
            '/** Where the roads meet; walks between places pass through it. */',
            f'export const missionMapCross = {{ x: {CROSS[0]}, y: {CROSS[1]} }} as const;',
            'export const missionMapImage: ImageSourcePropType = mapImage;',
            f'export const missionMapPlaces = {ts_object(places)} as const;',
            '',
        ]))
    preview = os.environ.get('MAP_PREVIEW')
    if preview:
        cv.save(preview, 2)
    print('ok mission map', W, H)


if __name__ == '__main__':
    main()
