"""The home valley's places: the town, the harbour and the headland, the riverside and the park, the ridge cabin, the halt and the woodland.

Split out of zones.py (19 Oct) so one worker can own this district's drawing while
others work on the rest of the world. It draws with zones.py's helpers; zones.py
imports it just before main()."""
from __future__ import annotations

import functools  # noqa: F401
import math  # noqa: F401

from zones import *  # noqa: F401,F403  (zones.py registers itself under that name)
from zones import _decal, _rgb  # noqa: F401
import ground  # noqa: F401

__all__ = ['town', 'harbour', 'headland', 'riverside', 'park', 'ridge', 'halt', 'woodland']


# ---------------------------------------------------------------------------------------
# Natural shapes and small living things drawn into the ground (docs/vision/art-faults.md,
# rules 3, 9 and 11: no perfect shapes in nature, every surface has its material, drawn
# to the detail target from the first draw). Each is lit from the upper left and sits on
# the ground with a contact shadow.
# ---------------------------------------------------------------------------------------
LEAF = MATERIALS['leaf']
WTR = MATERIALS['water']
FOAM = '#EEF5F8'


def blob(cx: float, cy: float, rx: float, ry: float, seed: int = 0, rough: float = 0.18) -> set:
    """An organic closed shape: an ellipse whose radius wanders with the angle in a few
    slow lobes, so ponds, clearings and rocks never read as a drawn ellipse."""
    ph = [noise2(seed, k, 771) * 6.283 for k in range(4)]
    pts = set()
    span = 1 + rough * 1.3
    for y in range(int(cy - ry * span) - 2, int(cy + ry * span) + 3):
        for x in range(int(cx - rx * span) - 2, int(cx + rx * span) + 3):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            a = math.atan2(dy, dx)
            r = 1 + rough * (0.55 * math.sin(2 * a + ph[0]) + 0.35 * math.sin(3 * a + ph[1])
                             + 0.2 * math.sin(5 * a + ph[2]) + 0.1 * math.sin(8 * a + ph[3]))
            if dx * dx + dy * dy <= r * r:
                pts.add((x, y))
    return pts


def edge_of(mask: set) -> set:
    return {(x, y) for (x, y) in mask if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def contact(cv: Canvas, cx: float, cy: float, rx: float, ry: float):
    """A hard contact shadow on the ground, offset down and right."""
    style.cast_shadow(cv, cx + 1, cy + 1, rx, ry)


def boulder(cv: Canvas, cx: float, base: float, w: float, h: float, seed: int, moss: bool = True,
            ramp=None) -> set:
    """One stone lying on the ground: a lumpy mass with a lit top plane, a mid front, a
    dark right flank and base, a crack or two and moss on its top (style.facet_stone),
    on its own contact shadow. Returns its pixels."""
    ramp = ramp or STONE
    pts = blob(cx, base - h / 2, w / 2, h / 2, seed=seed, rough=0.16)
    pts = {(x, y) for (x, y) in pts if y < base}
    contact(cv, cx + 1, base - 1, w / 2 + 1, max(2, h / 5))
    style.facet_stone(cv, pts, ramp, moss=LEAF if moss else None, seed=seed)
    return pts


def outcrop(cv: Canvas, stones, seed: int = 0, moss: bool = True) -> set:
    """Several boulders heaped together, drawn back to front, with dark crevices
    between them: a rock face with form rather than a dithered oval.
    `stones` are (cx, base, w, h)."""
    pts = set()
    for i, (cx, base, w, h) in enumerate(sorted(stones, key=lambda s: s[1])):
        pts |= boulder(cv, cx, base, w, h, seed + i * 7, moss=moss)
    return pts


def fern(cv: Canvas, x: int, y: int, seed: int = 0, size: float = 1.0):
    """A fern growing from (x, y): seven arching fronds fanning up and out, each a
    spine with paired leaflets shrinking to its tip; the upper leaflets lit, the lower
    ones in shade, the back fronds darker, on a small shadow."""
    contact(cv, x + 1, y, 6 * size, 2)
    fronds = [(-160, 0.7, 1), (-20, 0.7, 1), (-125, 1.0, 2), (-55, 1.0, 2), (-100, 0.95, 3), (-78, 0.9, 3),
              (-140, 0.8, 3), (-38, 0.8, 3)]
    for k, (deg, ln, tier) in enumerate(fronds):
        a = math.radians(deg + (noise2(seed, k, 781) - 0.5) * 16)
        L = (8 + noise2(seed, k, 782) * 3) * ln * size
        steps = int(L * 1.6)
        for s in range(steps):
            t = s / max(1, steps - 1)
            px = x + math.cos(a) * L * t
            py = y + math.sin(a) * L * t + 5 * size * t * t * (0.6 if abs(math.cos(a)) > 0.5 else 0.3)
            ix, iy = int(round(px)), int(round(py))
            cv.set(ix, iy, LEAF[1 + (tier > 1)])
            if s % 2 == 0 and t < 0.92:
                leaf = max(1, int((1 - t) * 3 * size + 0.5))
                nx, ny = -math.sin(a), math.cos(a)
                for side in (-1, 1):
                    for q in range(1, leaf + 1):
                        lx, ly = int(round(px + nx * q * side)), int(round(py + ny * q * side - q * 0.4))
                        up = (ny * side) < 0  # this leaflet faces up, toward the light
                        c = LEAF[min(4, tier + 1)] if up else LEAF[max(1, tier - 1)]
                        if up and q == leaf and tier == 3:
                            c = LEAF[4]
                        cv.set(lx, ly, c)
    cv.set(x, y, LEAF[0]); cv.set(x + 1, y, LEAF[0])


def mushroom(cv: Canvas, x: int, y: int, size: int, seed: int = 0, cap=('#7A2A26', '#B0403A', '#D45E4A', '#F08A6E')):
    """A toadstool standing at (x, y): a pale stem, a domed cap lit on its upper left
    with white spots, a dark gill line under the rim and a contact shadow."""
    contact(cv, x + 1, y, size * 0.7 + 1, 1)
    hgt = size + 1
    for k in range(hgt):
        cv.set(x, y - k, '#E8DCC8' if k < hgt - 1 else '#C9B89C')
        if size > 2:
            cv.set(x + 1, y - k, '#C9B89C')
    top = y - hgt
    rx = size * 0.8 + 0.6
    for dy in range(-size // 2 - 1, 1):
        for dx in range(-int(rx) - 1, int(rx) + 2):
            if (dx / (rx + 0.3)) ** 2 + (dy / (size / 2 + 0.8)) ** 2 <= 1:
                lit = dx < 0 and dy < -size // 4
                c = cap[3] if lit and dx < -1 else cap[2] if dx <= 0 else cap[1]
                if dy == 0:
                    c = cap[0]
                cv.set(x + dx + (size > 2) // 2, top + dy, c)
    if size >= 2:
        cv.set(x - 1, top - size // 2, '#F7F2E8')
        if size >= 3:
            cv.set(x + 1 + (seed % 2), top - 1, '#F7F2E8')


def waterfall(cv: Canvas, x0: int, w: int, y0: int, y1: int, seed: int = 0):
    """A narrow fall of water from a lip at y0 to a pool at y1: a lit curl over the lip,
    streaks running down (lighter on the left, toward the light), a darker right edge,
    and white water where it lands."""
    for y in range(y0, y1):
        for x in range(x0, x0 + w):
            f = (x - x0) / max(1, w - 1)
            c = WTR[3] if f < 0.7 else WTR[2]
            if f < 0.2:
                c = WTR[4]
            run = (y - y0 + int(noise2(x, seed, 783) * 9)) % 7
            if 0.2 <= f < 0.7 and run < 3:
                c = WTR[4] if (x + seed) % 2 else FOAM
            if f >= 0.85:
                c = WTR[1]
            cv.set(x, y, c)
    cv.hline(x0 - 1, y0, w + 2, WTR[4]); cv.hline(x0, y0 - 1, w, FOAM)
    for k in range(w + 6):  # where it lands: white water in a broken crescent
        xx = x0 - 3 + k
        cv.set(xx, y1 + (k % 3 == 0), FOAM if k % 4 else WTR[4])
        if 1 < k < w + 4:
            cv.set(xx, y1 + 1 + (k % 2), WTR[4])
    for k in range(4):  # spray
        cv.set(x0 - 4 + k * (w + 6) // 3, y1 - 2 - (k % 2), FOAM)


def water_body(cv: Canvas, water: set, deep=None, seed: int = 0, glints: int = 40):
    """Still or slow water in an organic shape: a dark band under its near (north) bank
    where the bank casts its shadow, deeper colour toward the middle, short highlights
    on the open water and a lit wet edge along the far (south) bank."""
    deep = deep or set()
    water = set(water) | {(x, y) for x in range(-3, W + 3) for y in (-3, -2, -1, H, H + 1, H + 2)
                          if (min(max(x, 0), W - 1), min(max(y, 0), H - 1)) in water}  # it runs on past the edge
    water |= {(x, y) for y in range(H) for x in (-3, -2, -1, W, W + 1, W + 2) if (min(max(x, 0), W - 1), y) in water}
    for (x, y) in water:
        c = WTR[1] if (x, y) in deep else WTR[2]
        if (x, y) in deep and smooth_noise(x, y, 7, seed + 1) > 0.66:
            c = WTR[2]
        if (x, y - 1) not in water or (x, y - 2) not in water:
            c = WTR[0]
        elif (x, y - 3) not in water:
            c = WTR[1]
        cv.set(x, y, c)
    for (x, y) in water:
        if (x, y + 1) not in water and (x, y - 3) in water:
            cv.set(x, y, WTR[3])  # the wet edge catching the light
    for i in range(glints):
        x = int(noise2(i, seed, 784) * 400)
        y = int(noise2(seed, i, 785) * 700)
        if all((x + t, y) in water and (x + t, y - 3) in water and (x + t, y + 2) in water for t in range(-1, 5)):
            cv.hline(x, y, 3 + (i % 2), WTR[3])
            if i % 3 == 0:
                cv.set(x + 1, y, WTR[4])
    water_detail(cv, water, seed)


def _mix(a, b, t):
    a, b = _rgb(a), _rgb(b)
    return '#%02X%02X%02X' % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def water_detail(cv: Canvas, water: set, seed: int = 0):
    """The water's detail at Eastward's bar (art-style.md, 20 Oct; detail_bar 'water'),
    always in clusters of two or more pixels, never speckle: the near bank mirrored dark
    and green in a broken band under it; the body in clumps of four depths between the
    ramp's tones; the current drawn as short lit streaks each over its own shadow; small
    bright glints in pairs; and in the shallows by the far bank, a paler band where the
    bottom shows, with stones lying under the water."""
    inside = {(x, y) for (x, y) in water if 0 <= x < W and 0 <= y < H}
    depth = {}
    for (x, y) in inside:
        up = next((k for k in range(1, 9) if (x, y - k) not in water), 9)
        dn = next((k for k in range(1, 9) if (x, y + k) not in water), 9)
        depth[(x, y)] = (up, dn)
    MID = [_mix(WTR[1], WTR[2], 0.35), _mix(WTR[1], WTR[2], 0.7), _mix(WTR[2], WTR[3], 0.3)]
    REFL = [_mix(WTR[0], G[1], 0.3), _mix(WTR[1], G[2], 0.22), _mix(WTR[0], SOIL_R[2], 0.25)]
    SHALLOW = [_mix(WTR[2], SOIL_R[4], 0.22), _mix(WTR[3], SOIL_R[4], 0.18)]
    for (x, y), (up, dn) in depth.items():
        cell = smooth_noise(x, y * 3, 14, seed + 901)  # long soft bands lying with the flow
        if up <= 4 and up >= 2:  # the bank's reflection, broken in clumps
            if noise2(x // 8, 0, seed + 902) > 0.3:
                cv.set(x, y, REFL[0] if up == 2 else REFL[1] if noise2(x // 11, 1, seed + 903) > 0.4 else REFL[2])
        elif dn <= 2 and up > 4:  # the shallows by the far bank, the bottom showing
            cv.set(x, y, SHALLOW[0] if dn == 2 else SHALLOW[1])
        elif up > 4 and dn > 2:
            if cell > 0.72:
                cv.set(x, y, MID[2] if dn > 4 else MID[1])
            elif cell < 0.22:
                cv.set(x, y, MID[0] if up < 7 or dn < 7 else _mix(WTR[0], WTR[1], 0.55))  # darkest where it is deepest
            elif up > 6 and dn > 6 and smooth_noise(x, y * 2, 10, seed + 908) > 0.7:
                cv.set(x, y, _mix(WTR[1], WTR[2], 0.5))  # a slow eddy turning in the deep water
    # stones lying on the bottom in the shallows, two or three pixels each
    for (x, y), (up, dn) in depth.items():
        if dn in (3, 4) and up > 5 and noise2(x // 2, y // 2, seed + 904) > 0.96 and x % 2 == 0 and y % 2 == 0:
            for (a, b) in ((0, 0), (1, 0), (0, 1)):
                if (x + a, y + b) in inside:
                    cv.set(x + a, y + b, _mix(WTR[2], STONE[2], 0.45) if (a, b) != (0, 0) else _mix(WTR[3], STONE[3], 0.4))
    # the current: short streaks lit on top with their own shadow under them
    for (x, y), (up, dn) in depth.items():
        if up > 4 and dn > 3 and noise2(x // 6, y // 3, seed + 905) > 0.9 and (x + y * 3) % 9 == 0:
            n = 4 + int(noise2(x, y, seed + 906) * 4)
            if all((x + t, y) in inside and (x + t, y + 1) in inside for t in range(n)):
                for t in range(n):
                    cv.set(x + t, y, WTR[3] if 0 < t < n - 1 else MID[2])
                    cv.set(x + t, y + 1, WTR[1])
    # glints in pairs where the light catches it
    for (x, y), (up, dn) in depth.items():
        if up > 5 and dn > 3 and noise2(x, y, seed + 907) > 0.993 and (x + 1, y) in inside:
            cv.set(x, y, WTR[4]); cv.set(x + 1, y, _mix(WTR[3], WTR[4], 0.5))
    # no lone pixels (detail comes in clusters): a pixel unlike all four neighbours takes
    # the colour most of them share
    for _ in range(2):
        fix = {}
        for (x, y) in inside:
            c = cv.get(x, y)[:3]
            nb = [cv.get(x + a, y + b)[:3] for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + a, y + b) in inside]
            if len(nb) == 4 and all(n != c for n in nb):
                best = max(set(nb), key=nb.count)
                if nb.count(best) >= 2:
                    fix[(x, y)] = best
        for (x, y), c in fix.items():
            cv.set(x, y, '#%02X%02X%02X' % c)


def bank(cv: Canvas, water: set, keep=frozenset(), seed: int = 0, sandy: bool = False):
    """The ground round water: on the far (south) side a lit lip of earth or sand
    dropping to the water; on the near (north) side the turf overhangs as a dark lip
    with a mossy shadow; pebbles and the odd reed clump at the waterline."""
    ring = set()
    for (x, y) in water:
        for dx, dy in ((0, -1), (0, -2), (0, 1), (0, 2), (-1, 0), (1, 0), (-2, 0), (2, 0)):
            q = (x + dx, y + dy)
            if q not in water and q not in keep:
                ring.add(q)
    for (x, y) in ring:
        below_water = any((x, y + k) in water for k in (1, 2))
        above_water = any((x, y - k) in water for k in (1, 2))
        if below_water:  # the north bank: turf breaking over the water
            c = G[1] if (x, y + 1) in water else G[2]
            if (x, y + 1) in water and noise2(x, y, seed + 786) > 0.6:
                c = LEAF[1]
        elif above_water:  # the south bank: a lit lip of earth or sand
            c = (SAND_R[2] if (x, y - 1) in water else SAND_R[1]) if sandy else (SOIL_R[5] if (x, y - 1) in water else SOIL_R[4])
        else:
            c = SOIL_R[4] if not sandy else SAND_R[1]
        cv.set(x, y, c)
    for (x, y) in ring:
        if noise2(x, y, seed + 787) > 0.965 and (x, y - 1) in water:
            detail.pebble(cv, x, y, STONE, big=noise2(x, y, seed + 788) > 0.5)
    return ring


SAND_R = MATERIALS['sand']
SOIL_R = MATERIALS['soil']  # (earth banks: kept off the path colours, so the lint reads them as ground)


def earth_bluff(cv: Canvas, x: int, top: int, h: int, gx: int, built: bool = False) -> set:
    """One column of the river's north bank in Claude B's natural earth treatment (B12,
    garden_meadow.draw_bluff, agreed for the woodland and the riverside, E19): a turf lip
    hanging over the edge in scallops, roots trailing from it, a face of earth in lumps
    lit on their upper left with the odd stone bedded in it, wet and darkest at the foot.
    `gx` is the garden's x for the same column, so the noise runs on across the seams;
    the earth is drawn in the soil ramp (one step for each of the garden's path tones),
    so the bank never reads as a path. `built` lays it in dressed courses instead, where
    people use the bank. Returns the column's pixels."""
    out = set()
    lip = 2 + (1 if noise2(gx // 3, 11, 94) > 0.55 else 0) + (1 if noise2(gx, 12, 94) > 0.9 else 0)
    root = noise2(gx, 13, 94) > 0.86 and not built
    stone = noise2(gx // 4, 14, 94) > 0.78 and not built
    for k in range(h):
        y = top + k
        if k == 0:
            c = G[3]
        elif k < lip and not built:
            c = G[2] if k == 1 else G[1]
        elif built:
            si = (gx + int(noise2(gx // 6, 1, 95) * 6)) // 6
            col = (gx + int(noise2(gx // 6, 1, 95) * 6)) % 6
            row, r = divmod(k - 2 + (si % 2) * 2, 4)
            base = 3 if noise2(si, row, 97) > 0.45 else 2
            c = STONE[0] if col == 5 or r == 3 else STONE[base + 1] if col == 0 or r == 0 else STONE[base - 1] if col == 4 else STONE[base]
            if k == 1:
                c = STONE[4]
        else:
            lx = gx + int(noise2(gx // 5, k // 3, 99) * 3)
            cell = (lx // 5, (k + (lx // 5) % 2) // 3)
            u, v = lx % 5, (k + (lx // 5) % 2) % 3
            t = 2 if noise2(*cell, 98) > 0.5 else 1
            if u == 0 or v == 0:
                t += 1
            if u == 4 and noise2(*cell, 96) > 0.4:
                t = 0
            c = SOIL_R[t + 2]
            if k == lip:
                c = SOIL_R[2]  # the shadow under the hanging turf
            if stone and 3 <= k <= 5:
                c = STONE[3] if k == 3 else STONE[2] if k == 4 else STONE[1]
            if root and lip <= k < lip + 3:
                c = WOOD[1] if k < lip + 2 else WOOD[2]
        if k >= h - 2 and not built:
            c = SOIL_R[1] if k == h - 1 else SOIL_R[2]
        elif k == h - 1:
            c = STONE[1]
        cv.set(x, y, c)
        out.add((x, y))
    return out


def door_front(key: str, x: int, y: int):
    """Where a building's door meets the ground, in zone px, for a building placed at
    (x, y) as in a zone's objects (the same reckoning build() uses for its door check)."""
    sp = sprites()[key]
    return x + sp.ox + int(sp.w * DOORS[key]), y + sp.oy + sp.h


def _disc(r: int):
    return [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if dx * dx + dy * dy <= r * r + r]


def lay_road(cv: Canvas, mask, seed: int = 0, avoid=frozenset(), doors=(), worn: float = 1.0) -> set:
    """Paint a path the way paths wear (research/placement-paths-verticality.md, section
    2.2, steps 5 and 6) and return the pixels it covers:
    - door aprons: where a door's front lies within reach of the path, the path widens
      into a small trodden apron before it, because people stop at a door;
    - junction fillets: inside corners where paths meet are worn round (a closing of the
      mask), so a T or a Y reads as feet cutting the corner, not a ruled join;
    - worn verges: a band of trampled, paler grass up to six pixels wide along the
      edges (about a walk cell or two), patchy, heaviest at the junctions and the aprons.
    `avoid` are pixels the path must not spread onto (water, walls, fields)."""
    mask = set(mask)
    avoid = set(avoid)
    aprons = set()
    for k, (dx, dy) in enumerate(doors):
        if any((dx + i, dy + j) in mask for i in range(-10, 11) for j in range(-2, 18)):
            aprons |= {(x, y) for (x, y) in blob(dx, dy + 5, 10, 5, seed=seed + 31 + k, rough=0.14)
                       if y >= dy - 1 and (x, y) not in avoid}
    mask |= aprons
    grown = {(x + a, y + b) for (x, y) in mask for (a, b) in _disc(5)}
    closed = {p for p in grown if all((p[0] + a, p[1] + b) in grown for (a, b) in _disc(5))}
    fillets = {(x, y) for (x, y) in closed - mask if (x, y) not in avoid and 0 <= x < W and 0 <= y < H}
    mask |= fillets
    paint_road(cv, mask)
    if worn <= 0:
        return mask
    hot = fillets | aprons
    near_hot = {(x + a, y + b) for (x, y) in hot for (a, b) in _disc(5)}
    WORN = (0xB4, 0xAA, 0x78)  # trodden, dried grass: never one of the path's own colours
    ring = {}
    frontier = set(mask)
    for d in range(1, 7):
        nxt = set()
        for (x, y) in frontier:
            for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + a, y + b)
                if q not in mask and q not in ring and q not in avoid and 0 <= q[0] < W and 0 <= q[1] < H:
                    ring[q] = d
                    nxt.add(q)
        frontier = nxt
    for (x, y), d in ring.items():
        if d == 1 and (x, y - 1) in mask:
            continue  # the turf's lit lip under the path stays
        t = (0.5, 0.42, 0.34, 0.25, 0.16, 0.1)[d - 1] * worn
        if (x, y) in near_hot:
            t += 0.18
        n = smooth_noise(x, y, 5, seed + 977)
        if n < 0.42 - 0.08 * (d == 1):
            continue
        c = cv.get(x, y)
        if c is None or (len(c) > 3 and c[3] == 0):
            continue
        t = min(0.7, t * (0.6 + n))
        rgb = tuple(int(c[i] + (WORN[i] - c[i]) * t) for i in range(3))
        hexc = '#%02X%02X%02X' % rgb
        if hexc.upper() in {p.upper() for p in P}:
            continue
        cv.set(x, y, hexc)
    return mask


def reeds(cv: Canvas, x: int, y: int, seed: int = 0, n: int = 6):
    """A clump of reeds standing in the shallows: blades of different heights, lit on
    the left, two brown seed heads."""
    for k in range(n):
        bx = x + k * 2 - n + int(noise2(seed, k, 789) * 2)
        h = 6 + int(noise2(k, seed, 790) * 6)
        lean = 1 if k > n // 2 else -1 if k < n // 3 else 0
        for t in range(h):
            xx = bx + (lean if t > h * 0.6 else 0)
            cv.set(xx, y - t, LEAF[3] if k % 2 == 0 and t > 1 else LEAF[2] if t > 1 else LEAF[1])
        if k in (1, n - 2):
            cv.vline(bx + lean, y - h - 2, 3, WOOD[1]); cv.set(bx + lean, y - h - 2, WOOD[2])
    cv.hline(x - n, y + 1, 2 * n, WTR[3])


def town(frame: int = 0):
    cv = Canvas(W, H)
    ground.valley(cv, 'town', frame)  # one turf across the valley (ground.py)
    # the road from the garden gate, then cobbled streets and the paved square
    # the garden's main path (36 px wide, centred on x = 160) crosses the border unchanged
    road = worlds.thick([(160, -4), (160, 24)], 18, seed=0) | worlds.thick([(160, 20), (158, 60), (164, 130), (160, 240)], 15, seed=5)
    road |= {(x, y) for (x, y0) in road if y0 == 0 for y in range(-12, 0)}
    # the square, laid to the fronts round it (Claude A's E1): one straight kerb along the
    # library's steps and the red house's lane, straight sides, the corners cut where the
    # lanes come in, and the east street leaving its east side
    square = poly([(52, 232), (270, 232), (284, 246), (284, 322), (268, 338), (232, 348), (92, 350), (60, 338), (46, 318), (46, 248)])
    # one rule by grade (E2): the square is paved; the roads between places, the street
    # east to the park's bridge among them, are trodden earth like the rest of the valley
    east = worlds.thick([(276, 300), (W + 4, 300)], 13)
    # the lane west to the Valley Halt, at the same height and width as the halt's lane
    west = worlds.thick([(-12, 300), (12, 300)], 11) | worlds.thick([(10, 300), (76, 296)], 11, seed=8)
    road |= west | {(x, y) for (x0, y) in west if x0 == 0 for x in range(-12, 0)}
    road |= east | {(x, y) for (x0, y) in east if x0 == W - 1 for x in range(W, W + 12)}
    # the road south to Driftwood Harbour, the same width and x as the harbour's road
    south = worlds.thick([(160, 340), (156, 470), (160, 560)], 15, seed=6) | worlds.thick([(160, 552), (160, H + 4)], 18)
    south |= worlds.thick([(150, 400), (104, 436), (78, 456)], 7, seed=7)  # a side path to the ring's opening (a grade-2 branch off the road)
    # the town grows down the road toward the harbour: lanes to the houses' doors
    south |= worlds.thick([(160, 424), (230, 426), (276, 424)], 6, seed=71)
    south |= worlds.thick([(160, 524), (200, 526), (228, 522)], 6, seed=72)
    south |= worlds.thick([(236, 244), (250, 222), (254, 204)], 6, seed=73)  # to the red house's door
    road |= south | {(x, y) for (x, y0) in south if y0 == H - 1 for y in range(H, H + 12)}
    # one network, laid as it wears: aprons at the doors, worn corners, trodden verges
    rcx, rcy = 76, 486
    doors = [door_front(k, x, y) for (k, x, y) in (('library', 6, 130), ('house_red', 214, 124), ('house_blue', 236, 344),
                                                   ('house_red', 188, 444), ('cafe', 200, 318))]
    lay_road(cv, road, seed=70, avoid=set(oval(rcx, rcy, 56, 28)), doors=doors)
    worlds.paint_paving(cv, square, seed=3)
    # a ring of darker setts round the well, centred on its basin
    WX, WY = 164, 297
    for (x, y) in square:
        d = ((x - WX) / 30) ** 2 + ((y - WY) / 17) ** 2
        if 0.76 < d < 1.0:
            cv.set(x, y, '#8C8574' if (x + y) % 3 else '#A9A28F')
        elif 1.0 <= d < 1.12:
            cv.set(x, y, '#D4CBB3')
    # the kerb: long dressed stones round the square, lit on top with a joint every 8 px,
    # its face and a shadow on the turf below the south side; where a road comes in the
    # kerb is dropped flush and the paving meets the earth
    kerb = {}
    for (x, y) in square:
        out = [(a, b) for (a, b) in ((0, 1), (0, -1), (1, 0), (-1, 0)) if (x + a, y + b) not in square]
        if out and not any((x + a, y + b) in road for (a, b) in out):
            kerb[(x, y)] = out
    for (x, y), out in kerb.items():
        for (a, b) in out:  # the joint between the kerb and the paving, a pixel in
            if (x - a, y - b) in square and (x - a, y - b) not in kerb:
                cv.set(x - a, y - b, '#8C8574')
        along = x if (0, 1) in out or (0, -1) in out else y
        cv.set(x, y, STONE[1] if along % 8 == 0 else STONE[4] if (0, -1) in out or (-1, 0) in out else STONE[3])
        if (0, 1) in out and y + 2 < H:
            cv.set(x, y + 1, STONE[1])
            style.darken(cv, x, y + 2)
    # the sparring ring: trodden earth edged with stones
    rcx, rcy = 76, 486
    ring = blob(rcx, rcy, 52, 24, seed=486, rough=0.1)
    for (x, y) in ring:
        cv.set(x, y, P[3] if smooth_noise(x, y, 6, 9) > 0.55 else P[2])
    detail.grass_edge(cv, set(ring), G, P, seed=35)
    def ring_r(a):  # the ring's edge at angle a: follows the trodden earth, not a compass
        return 1 + 0.07 * (smooth_noise(int(a * 40), 0, 23, 487) - 0.5) * 2
    for k in range(26):
        a = 2 * math.pi * k / 26
        detail.pebble(cv, int(rcx + 54 * ring_r(a) * math.cos(a)), int(rcy + 26 * ring_r(a) * math.sin(a)), STONE, big=k % 2 == 0)
    # posts round the ring on its edge, a rope run from post to post sagging between them
    # at about knee height, and one gap only, a post's width either side of the path
    # coming in at the north (Claude A after #70)
    NP = 36
    posts = []
    for k in range(NP):
        a = 2 * math.pi * k / NP
        posts.append(None if k == 27 else (int(rcx + 58 * ring_r(a) * math.cos(a)), int(rcy + 28 * ring_r(a) * math.sin(a))))
    for p0, p1 in zip(posts, posts[1:] + posts[:1]):
        if p0 is None or p1 is None:
            continue
        (x0, y0), (x1, y1) = p0, p1
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            t = i / n
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t - 9 + 2.5 * math.sin(math.pi * t))  # 9 px up its posts, sagging
            cv.set(x, y - 1, '#E2D2A6')  # the rope's lit top
            cv.set(x, y, '#B89A62')
            cv.set(x, y + 1, '#6E5434')  # its shaded underside
            style.darken(cv, x + 1, y + 4)  # and its shadow on the ground below
    for fb in ((258, 196, 40, 16, 2),):  # a planter by the red house's door
        meadow.flower_planter(cv, *fb)
    objects = [
        # the treeline either side of the road from the garden
        # (no prop crosses a border: the garden's meadow runs on above these)
        ('pine-n0', 'pine', 4, 6), ('tree-n1', 'tree', 40, 14), ('pine-n2', 'pine', 92, 4),
        ('pine-n3', 'pine', 200, 2), ('tree-n4', 'tree_autumn', 228, 12), ('pine-n5', 'pine', 280, 8),
        ('tree-n6', 'tree_small', 100, 96), ('bush-n7', 'bush', 196, 112), ('signpost', 'signpost', 192, 150),
        ('lamp-r1', 'lamp', 132, 168), ('lamp-r2', 'lamp', 178, 168),
        # buildings on the square's north side, facing south
        ('library', 'library', 6, 130), ('house-red', 'house_red', 214, 124),
        ('pot-lib-1', 'potted_plant', 28, 214), ('pot-lib-2', 'potted_plant', 112, 214),
        # the square
        ('well', 'well', 144, 262), ('board', 'notice_board', 230, 252),
        ('lamp-s1', 'lamp', 60, 300), ('lamp-s2', 'lamp', 270, 248),  # on the square's north-east corner, clear of the blue house's roof (A after #98)
        ('bench-s1', 'bench_east', 100, 272), ('cafe-1', 'cafe', 200, 318),  # the bench turned to face the well (E3)
        # Moss's stall on the square's south-west corner, with its stock
        ('stall', 'stall', 2, 338), ('crate-1', 'crate', 92, 386), ('barrel-1', 'barrel', 108, 384),
        ('sack-1', 'sack', 6, 398),
        # the second street of houses, east
        ('house-blue', 'house_blue', 236, 344), ('pot-hb', 'potted_plant', 288, 404),  # beside the door, off its lane
        # the ring and its spectators
        ('bench-r1', 'bench', 106, 424), ('pole', 'pennant', 8, 430),  # the bench on the ring's north side, looking onto it (E3)
        # trees framing the road south (no hedge along the border: open land runs on)
        ('tree-s1', 'tree_small', 20, 500), ('bush-s2', 'bush', 250, 540), ('tree-w1', 'tree', 2, 196),
        ('house-s1', 'house_red', 188, 444), ('pot-s1', 'potted_plant', 252, 504), ('tree-e1', 'tree', 280, 446),
        ('bush-e2', 'bush', 286, 228), ('bush-w4', 'bush', 182, 396),
        # trees across the borders: the woods of the halt and the park reach into the town
        ('tree-x1', 'tree_small', -22, 120), ('tree-x2', 'tree', 284, 112),
        ('cat', 'cat', 182, 352),
    ]
    objects += [(f'ring-post-{k}', 'ring_post', p[0] - 3, p[1] - 14) for k, p in enumerate(posts) if p]
    stands = {
        'garden': (160, 18), 'library': (70, 238), 'well': (160, 316), 'stall': (60, 424),
        'ring': (76, 486), 'park': (306, 300), 'harbour': (160, 540), 'halt': (8, 300),
    }
    return cv, objects, stands


def west_shore(y: int) -> int:
    """Where Driftwood's west shore runs (harbour x): the open sea lies west of it, past
    the valley's edge, and the land rises from it in rocks. Not a straight band: a rocky
    cove bites in below cottage 1, the beach lies in a shallow bay, and points run out
    between them (Claude A's review after #52)."""
    def bump(c, w):
        return math.exp(-((y - c) / w) ** 2)
    return int(min(y / 2, 2) + 30 * bump(128, 30) + 16 * bump(334, 32) + smooth_noise(0, y, 23, 941) * 7
               + (smooth_noise(1, y, 6, 942) - 0.5) * 4)


SHORE_STONES = [STONE, ['#2F2C34', '#47444D', '#66636B', '#88868A', '#AEACA8'],
                ['#3E3A36', '#5C5650', '#7C766E', '#A09A90', '#C4BEB2']]  # cool, dark and warm stones


def shore_rocks(cv: Canvas, line, seed: int = 0, step: int = 11, clusters: bool = False, avoid=frozenset()) -> set:
    """Boulders along a rocky shore, `line` being (x, y) points on the waterline: big
    ones and small ones in no order, some in pairs, a gap now and then where the
    shingle shows, the surf working round their feet. With `clusters` the rocks lie in
    heaps of a few with stretches of shingle between (Claude A's E11: not one column
    the length of the shore), the heaps biggest at the points."""
    pts = set()
    i, k = 0, 0
    while i < len(line):
        x, y = line[i]
        heap = smooth_noise(0, y, 26, seed + 40)
        if clusters and heap < 0.54:  # a stretch of open shingle
            for q in range(2):
                detail.pebble(cv, x + 1 + int(noise2(k, 40 + q, seed) * 6), y + int(noise2(k, 50 + q, seed) * 6),
                              SHORE_STONES[(k + q) % len(SHORE_STONES)], big=q == 0)
            i += 6
            k += 1
            continue
        n = noise2(k, 0, seed)
        big = n > (0.55 if clusters and heap > 0.62 else 0.78)
        w = (16 + int(noise2(k, 1, seed) * 8)) if big else (7 + int(noise2(k, 1, seed) * 8))
        h = (10 + int(noise2(k, 2, seed) * 4)) if big else (5 + int(noise2(k, 2, seed) * 4))
        clear = not any((x + a, y + b) in avoid for a in range(-2, w + 3, 2) for b in range(-2, h + 2, 2))
        if noise2(k, 3, seed) > 0.12 and clear:
            ramp = SHORE_STONES[int(noise2(k, 10, seed) * len(SHORE_STONES))]
            pts |= boulder(cv, x + w // 2 - 3 + int(noise2(k, 4, seed) * 6), y + h // 2, w, h, seed + k,
                           moss=noise2(k, 5, seed) > 0.55, ramp=ramp)
        for q in range(3):  # shingle in the gaps
            px, py = x + 2 + int(noise2(k, 20 + q, seed) * 10), y + int(noise2(k, 30 + q, seed) * 8)
            detail.pebble(cv, px, py, SHORE_STONES[q % len(SHORE_STONES)], big=q == 0)
        if noise2(k, 6, seed) > (0.4 if clusters else 0.7) and not any((x + w + a, y + b) in avoid for a in range(-2, 12, 2) for b in range(-6, 6, 2)):  # a small one beside it, further up the shore
            pts |= boulder(cv, x + w + 2, y + 3, 6 + int(noise2(k, 7, seed) * 4), 4 + int(noise2(k, 8, seed) * 3), seed + k + 99, moss=False)
        i += max(5, int(h * (0.6 if clusters else 0.9) + noise2(k, 9, seed) * 6))
        k += 1
    return pts


def coast_top(gx: int) -> int:
    """Where the sea cliffs' turf lip runs, in the valley's x (harbour 0-319, headland
    320-639): low at Driftwood's east shore, swinging south round the Headland, and
    turning down out through the Headland's bottom edge near its east side."""
    x = gx - 320
    n = (smooth_noise(gx, 0, 9, 951) - 0.5) * 8 + (smooth_noise(gx, 3, 31, 952) - 0.5) * 10
    if x < 0:
        return 300 + int(n * 0.4)

    def g(c, w):
        return math.exp(-((x - c) / w) ** 2)
    # coves and points at the scale of the down (Claude A's E14), not one smooth sweep:
    # a cove under the bridge's path, points either side of the viewpoint, a cove where
    # the coast turns south, a last point under the trees
    bays = min(1.0, x / 30) * (-18 * g(40, 13) + 14 * g(96, 12) + 20 * g(152, 15) - 8 * g(196, 13)
                               + 18 * g(234, 11) - 22 * g(282, 13) + 14 * g(314, 9))
    if x < 120:
        u = x / 120
        return int(300 + 172 * u * u * (3 - 2 * u) + n * (0.4 + u) + bays)
    if x < 250:
        return int(472 + math.sin(x / 23) * 8 + n + bays)
    return int(472 + (x - 250) * 1.9 + n + bays)


def coast_height(gx: int) -> int:
    return 22 + int(smooth_noise(gx, 1, 18, 953) * 14)


BREAKWATER = [(166, 478), (196, 476), (224, 471), (246, 463), (258, 446), (272, 420), (286, 396), (298, 372), (308, 350), (314, 334)]


@functools.lru_cache(maxsize=1)
def _coast_cells():
    """How far the sea off Driftwood and the Headland lies from land, on a 4 px grid in
    the valley's x (0-639), measured from one outline of both zones' shores, so the
    water deepens the same way on both sides of their border."""
    from collections import deque
    C = 4
    cw, ch = 640 // C, H // C
    land = set()
    for gx in range(0, 640, 2):  # the cliffs' feet, and the land above them
        if gx >= 292:
            foot = coast_top(gx) + coast_height(gx)
            for y in range(0, min(H, foot), C):
                land.add((gx // C, y // C))
    for y in range(0, H, 2):
        bx = int(100 - (y - 296) * 0.26 - math.sin((y - 296) / 70) * 12) if y >= 296 else 100
        for x in range(0, bx, C):
            land.add((x // C, y // C))
    for x in range(0, 292, C):  # the quay and the village above it
        for y in range(0, 306, C):
            land.add((x // C, y // C))
    for (x, y) in blob(16, 540, 62, 74, seed=972, rough=0.14):  # the west point
        if x >= 0 and y < H:
            land.add((x // C, y // C))
    for (ax, ay), (bx, by) in zip(BREAKWATER, BREAKWATER[1:]):  # the breakwater and its root
        for k in range(12):
            land.add((int(ax + (bx - ax) * k / 12) // C, int(ay + (by - ay) * k / 12) // C))
    for (x, y) in blob(294, 366, 22, 28, seed=0, rough=0.0):
        land.add((x // C, y // C))
    dist, q = {}, deque()
    for c in land:
        dist[c] = 0
        q.append(c)
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if 0 <= n[0] < cw and 0 <= n[1] < ch and n not in dist:
                dist[n] = dist[(cx, cy)] + 1
                q.append(n)
    return dist


class coast_depth:
    """Depth for one zone's sea, read from the shared outline (zone x + ox)."""
    def __init__(self, ox: int):
        self.ox = ox
        self.cells = _coast_cells()

    def __call__(self, x, y):
        gx = x + self.ox
        a = self.cells.get((gx // 4, y // 4), 0)
        b = self.cells.get(((gx + 3) // 4, (y + 3) // 4), a)
        return (a + b) * 2


def jetty(cv: Canvas, x0: int, w: int, y0: int, y1: int, water: set, ladder: bool = True) -> set:
    """A timber jetty out over the water: weathered planks laid across, a lit stringer
    along its west side and a shaded one along its east, piles under its sides and its
    end standing in rings of ripples, its shadow on the water, and a ladder down into
    the water at its end. Returns the deck (walkable)."""
    BL = MATERIALS['bleached']
    deck = {(x, y) for x in range(x0, x0 + w) for y in range(y0, y1)}
    for (x, y) in deck:
        r = (y - y0) % 3
        pk = (y - y0) // 3
        t = 4 + (1 if noise2(pk, x0, 961) > 0.82 else -1 if noise2(pk, x0, 961) < 0.18 else 0)
        c = detail.tone(BL, t + 1) if r == 0 else detail.tone(BL, t) if r == 1 else BL[1]
        if r == 1 and noise2(x // 4, pk, 962) < 0.15:
            c = detail.tone(BL, t - 1)
        if x == x0:
            c = BL[5] if r != 2 else BL[3]
        elif x == x0 + w - 1:
            c = BL[2] if r != 2 else BL[0]
        if r == 1 and x in (x0 + 2, x0 + w - 3):
            c = STONE[1]  # nails over the stringers
        cv.set(x, y, c)
    for y in range(y0 + 8, y1, 14):  # piles along each side, seen past the deck's edge
        for (px, dx) in ((x0 - 1, -1), (x0 + w, 1)):
            cv.vline(px, y, 5, WOOD[2] if dx < 0 else WOOD[1])
            cv.set(px, y + 5, WTR[4]); cv.set(px + dx, y + 5, WTR[3])
    for x in range(x0, x0 + w):  # the end: a beam, and piles going down into the water
        cv.set(x, y1, BL[1]); cv.set(x, y1 + 1, WOOD[1] if x in (x0, x0 + 1, x0 + w - 2, x0 + w - 1) else WTR[0])
        cv.set(x, y1 + 2, WOOD[0] if x in (x0, x0 + 1, x0 + w - 2, x0 + w - 1) else WTR[1])
    for (px) in (x0, x0 + w - 2):
        cv.hline(px - 1, y1 + 3, 4, WTR[4])
    if ladder:
        lx = x0 + w // 2 - 2
        for k in range(1, 8):
            cv.set(lx, y1 + k, WOOD[3]); cv.set(lx + 4, y1 + k, WOOD[2])
            if k % 2 == 0:
                cv.hline(lx + 1, y1 + k, 3, WOOD[2])
        cv.hline(lx - 1, y1 + 8, 7, WTR[3])
    for y in range(y0, y1 + 3):  # the deck's shadow on the water, down and right
        for x in range(x0 + w + 1, x0 + w + 4):
            if (x, y) in water and (x, y) not in deck:
                style.darken(cv, x, y)
    return deck


def pier_head(cv: Canvas, x0: int, x1: int, y0: int, h: int, water: set) -> set:
    """The T-head of a pier, running east-west where a boat lies alongside: planks laid
    north-south, a lit north edge where the boat's fenders rub, a heavy beam along its
    front with piles going down into the water at intervals, and its shadow on the water.
    Returns the deck (walkable)."""
    BL = MATERIALS['bleached']
    deck = {(x, y) for x in range(x0, x1) for y in range(y0, y0 + h)}
    for (x, y) in deck:
        r = (x - x0) % 3
        pk = (x - x0) // 3
        t = 4 + (1 if noise2(pk, y0, 963) > 0.82 else -1 if noise2(pk, y0, 963) < 0.18 else 0)
        c = detail.tone(BL, t + 1) if r == 0 else detail.tone(BL, t) if r == 1 else BL[1]
        if y == y0:
            c = BL[5]
        if r == 1 and y in (y0 + 2, y0 + h - 3):
            c = STONE[1]
        cv.set(x, y, c)
    for x in range(x0, x1):
        cv.set(x, y0 + h, WOOD[2]); cv.set(x, y0 + h + 1, WOOD[1])  # the front beam
        pile = (x - x0) % 16 in (0, 1)
        for k in range(2, 6):
            if (x, y0 + h + k) in water:
                cv.set(x, y0 + h + k, WOOD[0] if pile else (WTR[0] if k < 4 else WTR[1]))
        if pile:
            cv.set(x, y0 + h + 6, WTR[4])
    for y in range(y0, y0 + h + 4):
        for x in range(x1, x1 + 3):
            if (x, y) in water and (x, y) not in deck:
                style.darken(cv, x, y)
    return deck


def breakwater(cv: Canvas, pts, seed: int = 0) -> set:
    """A rubble breakwater (Claude A's E13: not an even band ruled from end to end): a
    capped wall of big dressed blocks whose width swells and narrows as it was built out
    in seasons, with a dog-leg where it turns, rooted in the rocks fallen from the cliff;
    its seaward face in courses; armour boulders tipped against its sea side in heaps,
    thickest at the turn and the head; a round head with a small beacon on it. Returns
    everything it covers."""
    cover = set()
    line = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)))
        for k in range(n):
            line.append((ax + (bx - ax) * k / n, ay + (by - ay) * k / n))
    cy = {}
    for (x, y) in line:
        cy.setdefault(int(x), y)
    xs = sorted(cy)
    half = {x: 3 + int(smooth_noise(x, 0, 23, seed + 9) * 4.2) for x in xs}  # the cap's half-width, 3-6 px
    # armour boulders first along the seaward foot (behind the cap when drawn after), in
    # heaps: a few together, then a stretch where the face shows to the water
    turn = 250  # the dog-leg
    i, k = 0, 0
    while i < len(xs):
        x = xs[i]
        y = cy[x]
        heap = smooth_noise(x, 1, 30, seed + 11) + (0.35 if abs(x - turn) < 18 or i < 26 else 0)
        if heap > 0.55:
            for q in range(1 + (noise2(k, 5, seed) > 0.5) + (heap > 0.85)):
                cover |= boulder(cv, x + 3 + q * 7 + int(noise2(k, q, seed) * 4), y + half[x] + 13 + q * 2 + int(noise2(k, 1, seed) * 3),
                                 10 + int(noise2(k, 2 + q, seed) * 9), 7 + int(noise2(k, 3, seed) * 5), seed + k * 3 + q, moss=False)
            i += 6 + int(noise2(k, 6, seed) * 5)
        else:
            i += 4
        k += 1
    for x in xs:
        y = int(cy[x])
        hw = half[x]
        for yy in range(y - hw, y + hw):  # the cap's top: big slabs, jointed
            j = (x + (0 if ((yy - y + hw) // 4) % 2 else 6)) % 12
            c = STONE[4] if yy == y - hw else STONE[3] if j else STONE[1]
            if (yy - y + hw) % 4 == 3 and j:
                c = STONE[2]
            if noise2(x // 3, yy // 3, seed + 12) > 0.9:
                c = STONE[2]  # a block of another season's stone
            cv.set(x, yy, c)
            cover.add((x, yy))
        for k in range(8):  # the seaward face in courses
            yy = y + hw + k
            c = STONE[2] if (x + (k // 4) * 5) % 10 else STONE[0]
            if k % 4 == 3:
                c = STONE[0]
            if k >= 6:
                c = STONE[1] if k == 6 else '#2E4A3A'
            cv.set(x, yy, c)
            cover.add((x, yy))
        cv.set(x, y - hw - 1, STONE[1])  # the lip on the harbour side, lapped by the water
        cover.add((x, y - hw - 1))
    hx, hy = xs[0], cy[xs[0]]  # the head: a round drum
    head = blob(hx, hy, 11, 8, seed=seed + 50, rough=0.04)
    for (x, y) in head:
        cv.set(x, y, STONE[4] if (x - hx) + (y - hy) < -6 else STONE[3] if (x - hx) < 4 else STONE[2])
    for x in range(int(hx) - 11, int(hx) + 12):
        bot = max((yy for (xx, yy) in head if xx == x), default=None)
        if bot is None:
            continue
        for k in range(1, 9):
            cv.set(x, bot + k, STONE[2] if k < 4 else STONE[1] if k < 7 else '#2E4A3A')
            cover.add((x, bot + k))
    cover |= head
    # the beacon on the head: a short white iron column with a red band, its lamp on top
    bx, by = int(hx) + 1, int(hy) + 1
    for k in range(13):
        for d in (0, 1, 2):
            c = '#F2EEE2' if d < 2 else '#B8B4AC'
            if 5 <= k <= 7:
                c = RED[3] if d < 2 else RED[1]
            cv.set(bx + d, by - k, c)
    cv.hline(bx - 1, by - 13, 5, STONE[1]); cv.hline(bx - 1, by - 14, 5, STONE[0])
    cv.set(bx, by - 15, '#F8E6A0'); cv.set(bx + 1, by - 15, '#F2C94C'); cv.set(bx + 2, by - 15, STONE[0])  # its lamp
    cv.hline(bx, by - 16, 3, STONE[0])
    style.darken(cv, bx + 3, by); style.darken(cv, bx + 4, by + 1)
    return cover


def rail_fence(cv: Canvas, pts, seed: int = 0, gap=None) -> set:
    """A post-and-rail fence along a line of points (its foot): weathered posts every six
    pixels, two rails between them, lit on top, its shadow down and right on the ground.
    `gap` (x, y, r) leaves a gateway. Returns the pixels it stands on (they block a walk)."""
    BL = MATERIALS['bleached']
    foot = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay), 1))
        foot += [(round(ax + (bx - ax) * k / n), round(ay + (by - ay) * k / n)) for k in range(n)]
    foot.append(tuple(pts[-1]))
    if gap is not None:
        foot = [(x, y) for (x, y) in foot if math.hypot(x - gap[0], y - gap[1]) > gap[2]]
    out = set()
    for i, (x, y) in enumerate(foot):
        for r in (7, 3):  # the rails
            cv.set(x, y - r, BL[4] if r == 7 else BL[3])
            cv.set(x, y - r + 1, BL[1])
        out |= {(x, y), (x, y - 1)}
        style.darken(cv, x + 1, y + 1)
    for i, (x, y) in enumerate(foot):
        if i % 6 == 0 or i == len(foot) - 1:  # a post, a little taller than the top rail
            for k in range(0, 9):
                cv.set(x, y - k, BL[4] if k == 8 else BL[3] if k > 5 else BL[2])
                cv.set(x + 1, y - k, BL[1] if k < 8 else BL[3])
            style.darken(cv, x + 2, y)
            style.darken(cv, x + 2, y + 1)
    return out


def harbour(frame: int = 0):
    """Driftwood Harbour: the road from Crossroads Town comes down between whitewashed
    cottages to a stone quay and the fish market. Two timber jetties run out from the
    quay with boats moored at their ends and ladders down to the water; a curving
    breakwater of big blocks reaches out from the eastern rocks to shelter the basin;
    across the mouth, the lighthouse stands on the rocks of the west point, where the
    beach of drying nets and rock pools ends. The cliff path climbs away east to the
    Headland. Past the breakwater the sea opens to the south."""
    BLEACHED = MATERIALS['bleached']
    cv = Canvas(W, H)
    ground.valley(cv, 'harbour', frame)  # one turf across the valley (ground.py)
    QX0, QX1, QY0, QY1 = 96, 272, 226, 296  # the quay's paved top
    # the shore: the beach's waterline curves from the slipway to the west point; past
    # the quay the eastern rocks rise to the sea cliffs that run on round the Headland
    def beach_x(y):
        return int(100 - (y - 296) * 0.26 - math.sin((y - 296) / 70) * 12 + (smooth_noise(0, y, 12, 971) - 0.5) * 6)
    point = {(x, y) for (x, y) in blob(16, 540, 62, 74, seed=972, rough=0.14) if x >= west_shore(y) + 2 and y < H + 8}
    sand_top = {x: 214 + int((smooth_noise(x, 0, 16, 973) - 0.5) * 14) for x in range(W)}
    beach = {(x, y) for y in range(200, H) for x in range(west_shore(y) + 2, QX0 + 8) if y >= sand_top[x] and (y < 296 or x <= beach_x(y))} - point
    cliff_t = {x: coast_top(x) for x in range(304, W)}
    cliff_h = {x: coast_height(x) for x in range(304, W)}
    river, rdeep, _rl = river_in('harbour')  # the valley's river, coming out into the basin
    water = {(x, y) for y in range(H) for x in range(0, west_shore(y))}  # the open sea off the west shore
    for y in range(QY1 + 9, H):
        for x in range(W):
            if (x, y) in beach or (x, y) in point:
                continue
            if x >= 304 and y < cliff_t[x] + cliff_h[x]:
                continue
            water.add((x, y))
    # the river's mouth (Claude A's E12): the sea runs up into it in a bight, not across a
    # ruled row, so the two waters meet on a curve
    mouth = {(x, y) for (x, y) in river if y >= QY1 - 2 + int(10 * abs((x - 290) / 18) ** 1.6)}
    water |= mouth
    estuary = set(river) - water
    # the sand: dry and pale up the beach, darker and wet at the waterline, ripples
    for (x, y) in beach:
        n = smooth_noise(x, y, 7, 974)
        c = SAND_R[2] if n > 0.42 else SAND_R[1]
        wet = any((x + d, y) in water for d in (1, 2, 3, 4)) or any((x + d, y + 3) in water for d in (1, 3))
        if wet:
            c = SAND_R[0] if (x + y) % 3 else SAND_R[1]
        elif y > 300 and (y + int(math.sin(x / 6) * 2)) % 7 == 0 and n < 0.6:
            c = SAND_R[1]  # the ripples the tide left
        cv.set(x, y, c)
    for (x, y) in beach:  # the turf's edge onto the sand: dune grass in tufts
        if y == sand_top[x]:
            cv.set(x, y - 1, G[1])
            if noise2(x, y, 975) > 0.5:
                detail.grass_tuft(cv, x, y + 1, int(noise2(x, 0, 976) * 6), G, 2)
        elif noise2(x // 3, y // 3, 977) > 0.985:
            cv.set(x, y, '#F2EEE2'); cv.set(x + 1, y, SAND_R[0])  # a shell
    # rock pools left by the tide, each a ring of stones round still water
    pools = set()
    for (px, py, rx, ry, sd) in ((44, 336, 10, 5, 1), (12, 438, 7, 4, 3)):
        pool = blob(px, py, rx, ry, seed=978 + sd, rough=0.25)
        for (x, y) in pool:
            cv.set(x, y, WTR[0] if (x, y - 1) not in pool else WTR[2] if (x + y) % 5 else WTR[3])
        for (x, y) in edge_of(pool):
            if (x, y - 1) not in pool:
                cv.set(x, y, WTR[0])
        for k, (x, y) in enumerate(sorted(edge_of(blob(px, py, rx + 2, ry + 2, seed=978 + sd, rough=0.25)))):
            if k % 3 == 0:
                detail.pebble(cv, x, y, STONE, big=k % 2 == 0)
        pools |= pool
    # the sea: calm inside the breakwater, surf on the beach and under the cliffs
    calm = {(x, y) for (x, y) in water if y < 440 - max(0, 120 - x) and x > 80}
    sea(cv, water, seed=979, calm=calm, depth=coast_depth(0), open_edges='ws')
    bank(cv, estuary, keep=water, seed=976)
    water_body(cv, estuary, set(rdeep) & estuary, seed=977, glints=12)
    water |= estuary
    lpath0 = worlds.thick([(40, 372), (28, 392), (24, 452), (24, 500), (30, 528), (46, 530), (51, 522)], 5, seed=986)
    west_rocks = shore_rocks(cv, [(west_shore(y), y) for y in range(-4, H, 1) if not (470 < y)], seed=943, clusters=True,
                             avoid={(x + a, y + b) for (x, y) in lpath0 for (a, b) in ((0, 0), (3, 0), (-3, 0))})
    # the quay: dressed stone with a lit kerb and a front face in courses down to the
    # water, a slipway down onto the beach at its west end, the eastern rocks at its east
    quay = {(x, y) for x in range(QX0, QX1) for y in range(QY0, QY1)}
    # its east end runs on to the river and returns along its bank as a wall (E12), so
    # the paving never stops on a ruled line against the grass
    quay |= {(x, y) for y in range(QY0, QY1) for x in range(QX1, W) if all((x + d, y) not in river for d in range(0, 5))
             and any((x + d, y) in river for d in range(5, 60))}
    worlds.paint_paving(cv, quay, seed=9)
    for (x, y) in quay:
        if (x + 1, y) not in quay and x + 1 < W:  # the return wall's lit kerb, its face down to the river
            cv.set(x, y, STONE[4])
            for k in range(1, 5):
                if (x + k, y) in river:
                    cv.set(x + k, y, STONE[2] if (y + (k // 2) * 3) % 4 else STONE[0])
                    if k == 4:
                        cv.set(x + k, y, '#2E4A3A')
    cv.hline(QX0, QY1 - 1, QX1 - QX0, STONE[4])
    detail.stones(cv, QX0, QY1, QX1 - QX0, 8, STONE, seed=980, course=4, base=2)
    cv.hline(QX0, QY1 + 8, QX1 - QX0, '#2E4A3A')
    for x in range(QX0, QX1):  # weed and wet at the waterline
        if (x + 1) % 3:
            cv.set(x, QY1 + 7, STONE[1])
    for y in range(QY0 + 2, QY1 + 9):  # the quay's west end: a stone slipway down onto the sand
        for k in range(10):
            x = QX0 - 10 + k
            c = STONE[4] if (y - QY0) % 6 == 0 else STONE[3] if k < 7 else STONE[2]
            if k == 0:
                c = STONE[2]
            cv.set(x, y, c)
    for y in range(QY0 + 2, QY1 + 9):
        cv.set(QX0 - 1, y, STONE[1])
    for x in range(QX0, QX1):  # the kerb along the back
        cv.set(x, QY0, STONE[1]); cv.set(x, QY0 + 1, STONE[4])
    # cottage 4's back yard (E10): a post-and-rail fence round the grass behind it, the
    # washing hung east-west across it in the sun, a basket of pegged-out washing below
    # (A after #98: the taller roof covers the ground behind the house, so the drying green
    # is beside it, on the west, the line run from a post to the house's west wall)
    yard_fence = rail_fence(cv, [(222, 142), (180, 142), (180, 198), (222, 198)], seed=990)
    for (x, y, c) in ((186, 186, None),):
        for i in range(8):
            for j in range(5):
                cv.set(x + i, y + j, WOOD[3] if j == 0 else WOOD[2] if (i + j) % 2 else WOOD[1])
        for i in range(1, 7):
            cv.set(x + i, y - 1, '#F2EEE2' if i % 3 else '#9CC0E0')  # the folded washing in it
        style.darken(cv, x + 8, y + 3); style.darken(cv, x + 8, y + 4)
    # the eastern rocks: boulders heaped from the quay's end up to the cliffs
    rocks = outcrop(cv, [(274, 310, 12, 9), (268, 322, 10, 7), (312, 300, 16, 12), (306, 318, 12, 9)], seed=981, moss=True)
    face = cliff(cv, cliff_t, cliff_h, seed=982)
    # the breakwater reaches out from the cliff's foot round the basin
    spur = outcrop(cv, [(298, 352, 26, 22), (288, 372, 22, 16), (306, 340, 14, 14), (276, 388, 16, 12),
                        (300, 384, 18, 12)], seed=988, moss=True)  # rocks fallen from the cliff: the breakwater's root
    bw = breakwater(cv, BREAKWATER, seed=983)
    # the west point: a rocky knoll with pines on it, the lighthouse on its tip
    for (x, y) in point:
        n = smooth_noise(x, y, 9, 984)
        cv.set(x, y, G[2] if n > 0.45 else G[1])
    # the lighthouse's round plinth (Claude B's #58) stands on the knoll's crown; the keeper's
    # path comes down the neck west of the tower and round to its door on the south side
    knoll = outcrop(cv, [(52, 510, 24, 11), (70, 560, 28, 20), (40, 574, 30, 14), (6, 484, 14, 10), (76, 500, 10, 14),
                         (14, 556, 14, 12)], seed=985, moss=True)
    lpath = worlds.thick([(40, 372), (28, 392), (24, 452), (24, 500), (30, 528), (46, 530), (51, 522)], 5, seed=986)
    lpath = {(x, y) for (x, y) in lpath if (x, y) not in water and (x, y) not in knoll and (x, y) not in west_rocks and (x, y) not in pools}
    for (x, y) in point:
        if y < 470 and (x, y) not in knoll and noise2(x, y, 986) > 0.92:
            detail.grass_tuft(cv, x, y, int(noise2(x, y, 987) * 6), G, 2)
    # a short jetty for the fishing boats, and the ferry pier: a broad timber pier out
    # from the quay's east end to a T-head where the island ferry lies alongside, with a
    # ladder down to the water (play-test 18 Oct, finding 15)
    decks = set()
    decks |= jetty(cv, 146, 14, QY1 - 2, 340, water)
    decks |= jetty(cv, 228, 18, QY1 - 2, 404, water, ladder=False)
    decks |= pier_head(cv, 138, 246, 402, 12, water)
    # the road down from the town, the lanes to the cottages, the cliff path east
    road = worlds.thick([(160, -4), (160, 24)], 18) | worlds.thick([(160, 20), (152, 120), (166, 230)], 14, seed=16)
    road |= worlds.thick([(154, 120), (110, 118), (76, 108)], 8, seed=17)  # to cottage 1's door (a T off the road)
    d3x, d3y = door_front('cottage_c', 44, 140)
    # (it runs in front of the cottage, below its foot, so it is seen to reach the door)
    road |= worlds.thick([(160, 176), (142, 204), (124, d3y + 5), (d3x + 8, d3y + 5), (d3x, d3y + 2)], 6, seed=18)  # down to cottage 3's door
    road |= worlds.thick([(d3x + 2, d3y + 6), (90, d3y + 14)], 5, seed=21)  # and on down to the beach
    road |= worlds.thick([(156, 70), (196, 94), (240, 100), (290, 102), (W + 6, 110)], 8, seed=19)  # past cottage 2: the cliff path, a Y off the road above the T
    road |= worlds.thick([(164, 212), (230, 224), (262, 222)], 7, seed=20)  # to cottage 4's door
    hdoors = [door_front(k, x, y) for (k, x, y) in (('cottage', 42, 26), ('cottage_b', 210, 26), ('cottage_c', 44, 140),
                                                    ('cottage_d', 224, 140))]
    lay_road(cv, (road - quay) | {(x, y) for (x, y0) in road if y0 == 0 for y in range(-12, 0)}
             | {(x, y) for (x0, y) in road if x0 == W - 1 for x in range(W, W + 12)},
             seed=75, avoid=quay | water | beach | point, doors=hdoors)
    paint_road(cv, lpath)  # the keeper's path over the sand and the point
    objects = [
        # four households, four cottages: a net on the wall, shutters, a porch, a net shed
        ('cottage-1', 'cottage', 42, 26), ('cottage-2', 'cottage_b', 210, 26), ('cottage-3', 'cottage_c', 44, 140),
        ('cottage-4', 'cottage_d', 224, 140),
        # the washing line across cottage 4's back yard, east-west, in the sun
        ('washing', 'washing_line', 178, 150),
        # the net rack before cottage 4's net shed, where the nets are mended (E10)
        ('nets-1', 'net_rack', 266, 186),
        # the quay: the fish market, pots and the spare anchor by the chandler's corner
        ('market', 'fish_stall', 104, 226), ('pots-1', 'lobster_pots', 196, 236), ('pots-2', 'lobster_pots', 228, 240),
        ('anchor', 'anchor', 210, 262), ('bollard-1', 'bollard', 132, 284), ('bollard-2', 'bollard', 250, 284),
        # the beach: pots stacked by the slipway, two chairs up on the dry sand facing the sea (E11)
        ('pots-3', 'lobster_pots', 56, 272),
        ('chair-1', 'deck_chair', 26, 244), ('chair-2', 'deck_chair_b', 48, 250),
        # the boats: each at a jetty's end, one on its buoy in the basin, a sail beyond
        ('boat-1', 'boat_blue', 83, 318), ('boat-2', 'boat_red', 248, 348), ('boat-3', 'boat_blue', 150, 430),
        # the ferry to Lagoon Landing, moored port side to the pier's head, and its ladder
        ('ferry', 'harbour_ferry', 137, 362), ('ladder', 'pier_ladder', 238, 413),
        ('buoy-1', 'buoy', 252, 404), ('buoy-2', 'buoy', 112, 440), ('sail', 'sailboat', 238, 506),
        # the lighthouse on the west point's rocks, lighting the harbour mouth
        ('lighthouse', 'lighthouse', 30, 380),
    ]
    quay_face = {(x, y) for x in range(QX0, QX1) for y in range(QY1, QY1 + 9)}
    blocked = ((water | face | rocks | spur | bw | knoll | pools | west_rocks | quay_face) - decks - quay) | yard_fence
    stands = {'town': (160, 18), 'market': (150, 288), 'jetty': (196, 408), 'beach': (34, 380), 'castle': (304, 106),
              'lighthouse': (52, 532)}
    return cv, objects, stands, blocked


def headland(frame: int = 0):
    """The Headland, east of the harbour (Matt, 18 Oct: the castle moved to the fire
    country): the cliff path from the harbour comes in at the west edge and climbs the
    open down to the lookout tower that watches the sea from the cliff top. Sheep graze
    in a fold walled with dry stone, with a stile where the path passes; hives stand in
    the lee of its wall. The path ends at a flagged viewpoint on the cliff's edge with
    a bench beside it looking out to sea. The cliffs drop away south round the down,
    and turn inland at its east side under the trees."""
    cv = Canvas(W, H)
    ground.valley(cv, 'headland', frame)  # one turf across the valley (ground.py)
    top = {x: coast_top(x + W) for x in range(W)}
    hgt = {x: coast_height(x + W) for x in range(W)}
    sea_px = {(x, y) for x in range(W) for y in range(top[x] + hgt[x], H)}
    sea(cv, sea_px, seed=991, depth=coast_depth(W))
    face = cliff(cv, {x: t for x, t in top.items() if t < H}, {x: min(hgt[x], H - top[x]) for x in range(W) if top[x] < H}, seed=982)
    river, rdeep, _rl = river_in('headland')  # the valley's river, on its way down to Driftwood
    river = set(river) - sea_px - face
    bank(cv, river, seed=1501)
    water_body(cv, river, set(rdeep) & river, seed=1502, glints=30)
    # boulders fallen from the cliff, lying in the surf at its foot
    talus = set()
    for i, gx in enumerate(range(18, 300, 37)):
        by = top[gx] + hgt[gx] + 4 + int(noise2(i, 0, 992) * 6)
        if by < H - 4:
            talus |= boulder(cv, gx + int(noise2(i, 1, 992) * 12), by, 10 + int(noise2(i, 2, 992) * 8), 7 + int(noise2(i, 3, 992) * 4), 993 + i, moss=False)
    # rock shelves running out from the cliff's foot at the points, the sea washing over
    # their ends: flat beds of the same stone, lit on top, cracked along the bedding
    for (sx, sw) in ((96, 14), (152, 18), (234, 13), (314, 8)):
        fy = top[sx] + hgt[sx]
        if fy + 6 >= H:
            continue
        shelf = {(x, y) for (x, y) in blob(sx, fy + 4, sw, 4, seed=sx, rough=0.25) if (x, y) in sea_px}
        for (x, y) in shelf:
            c = STONE[3] if (x, y - 1) in shelf or (x, y - 1) not in sea_px else STONE[4]
            if (x * 3 + y) % 11 == 0:
                c = STONE[1]  # a crack along the bedding
            if (x, y + 1) not in shelf:
                c = '#2E4A3A'  # wet and weedy at the water
            cv.set(x, y, c)
        for (x, y) in edge_of(shelf):
            if (x, y + 2) in sea_px and (x, y + 2) not in shelf and noise2(x, y, 999) > 0.5:
                cv.set(x, y + 2, '#E8F0F2')  # the wash over its end
    # the cliff path from the harbour up the down to the tower, then on to the viewpoint
    path = worlds.thick([(-6, 110), (58, 112)], 8) | worlds.thick(
        [(56, 112), (66, 150), (80, 222), (140, 300), (176, 368), (206, 404), (227, 418)], 8, seed=19)
    # (Claude A's E17: one way to the tower's door, and one branch off it to the viewpoint,
    # not two paths side by side)
    path |= worlds.thick([(150, 318), (134, 360), (124, 400), (122, 434)], 6, seed=23)
    path |= worlds.thick([(88, 240), (150, 216), (210, 196), (214, 186)], 6, seed=998)  # a spur from the path up to the fold's gate
    lay_road(cv, (path - river) | {(x, y) for (x0, y) in path if x0 == 0 for x in range(-12, 0)}, seed=76,
             avoid=river | sea_px | face | {(x + a, y + b) for (x, y) in poly_field([(142, 76), (280, 58), (294, 168), (152, 188)], seed=996)
                                             for (a, b) in ((0, 0), (-3, 0), (3, 0), (0, -3), (0, 4))},
             doors=[door_front('lookout_tower', 198, 300)])
    bspan = [x for (x, y) in river if y == 110]
    bridge = stone_bridge(cv, 0, max(bspan) + 8, 103, 118, river)  # the cliff path's bridge over the river
    view = blob(122, 440, 20, 9, seed=994, rough=0.1)  # the viewpoint: flags laid on the cliff top
    worlds.paint_paving(cv, view, seed=995)
    for (x, y) in edge_of(view):
        cv.set(x, y, STONE[1] if (x, y + 1) not in view else STONE[4] if (x, y - 1) not in view else STONE[2])
    # the sheep fold: a dry stone wall round a rough field on the down, open at a stile
    # (a four-sided fold walled along the lie of the down, not a compass ellipse)
    fold = poly_field([(142, 76), (280, 58), (294, 168), (152, 188)], seed=996)
    posts = []
    # its gateway in the south wall, which the camera sees face on (in the west wall,
    # seen edge-on, the piers stacked into one pillar: Claude A after #70)
    wall = drystone_loop(cv, fold, gap=(214, 180, 7), seed=997, ends=posts)
    # the gateway's piers: squared stone a little taller than the wall (Claude A after #64:
    # the 26 px gateposts read as chimneys over a wall this low), each with a capstone
    for (px, py) in posts:
        pier = {(x, y) for x in range(px - 2, px + 3) for y in range(py - 11, py + 9)}
        for (x, y) in pier:
            c = STONE[3] if x < px + 2 else STONE[1]
            if y == py - 11:
                c = STONE[4]  # the capstone's lit top
            elif y == py - 10:
                c = STONE[2]
            elif (y - py) % 3 == 0:
                c = STONE[1]  # a joint between courses
            cv.set(x, y, c)
        for y in range(py - 10, py + 11):
            style.darken(cv, px + 3, y)  # its shadow to the right
        wall |= pier
    objects = [
        ('tower', 'lookout_tower', 198, 300),
        ('sheep-1', 'sheep', 176, 104), ('sheep-2', 'sheep_left', 236, 128), ('sheep-3', 'sheep_lying', 188, 132), ('lamb-1', 'lamb_left', 254, 136),  # inside, off the gate (E15)
        ('sheep-4', 'sheep_left', 236, 96),  # inside, off the east wall (A after #98)
        # the gate (Claude B's low field gate, #82) hung on the west pier and shut against
        # the east one, its row 11 on the piers' foot row
        *([('fold-gate', 'field_gate_low', min(posts)[0] + 2, min(posts)[1] + 8 - 11)] if posts else []),
        ('hive-1', 'beehive', 100, 112), ('hive-2', 'skep', 120, 106),  # in the lee of the fold's west wall
        ('bush-1', 'bush', 270, 230), ('bush-2', 'bush', 66, 262),
        ('bench', 'bench', 146, 418), ('stone-1', 'stone', 278, 400), ('stone-2', 'stone', 60, 380),
        # the down falls to trees on the east, running on into the woods beyond
        ('pine-e1', 'pine', 280, 296), ('tree-e2', 'tree', 252, 376), ('tree-e3', 'tree_small', 272, 452), ('bush-e4', 'bush', 292, 360),
    ]
    blocked = sea_px | face | wall | talus | (river - bridge)
    stands = {'harbour': (14, 112), 'tower': (228, 430), 'bench': (124, 440), 'down': (150, 280), 'fold': (212, 198)}
    return cv, objects, stands, blocked


def drystone_loop(cv: Canvas, field: set, gap=(0, 0), seed: int = 0, ends=None) -> set:
    """A dry stone wall round a field: rough stones of every size laid in two courses
    with a row of upright coping stones, lit on their tops, dark in the joints, lichen
    here and there, the turf growing up against its foot; `gap` is the stretch of its
    length (in px, from its westmost point, clockwise) left open as a stile. If `ends`
    is a list, the wall's two points either side of the gap are appended to it (for the
    gateposts that stand there)."""
    ring = edge_of(field)
    cx = sum(x for x, _ in ring) / len(ring)
    cy = sum(y for _, y in ring) / len(ring)
    order = sorted(ring, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    start = min(range(len(order)), key=lambda i: order[i][0])
    order = order[start:] + order[:start]
    if len(gap) == 3:  # (x, y, half-width): the gap where the wall passes nearest that point
        gi = min(range(len(order)), key=lambda i: math.hypot(order[i][0] - gap[0], order[i][1] - gap[1]))
        line = [p for i, p in enumerate(order) if min(abs(i - gi), len(order) - abs(i - gi)) > gap[2]]
        if ends is not None:
            ends += [order[(gi - gap[2] - 1) % len(order)], order[(gi + gap[2] + 1) % len(order)]]
    else:
        line = [p for i, p in enumerate(order) if not (gap[0] <= i < gap[1])]
    top = set()
    for (x, y) in line:  # a wall about five stones' width across its top
        top |= {(x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 2) if dx * dx + dy * dy <= 5}
    wall = set(top)
    # (Claude A's E15: a 3-4 px line does not read as a wall) the coping: a row of stones
    # set on edge along its top, lit on their tops, dark between, standing a pixel proud
    def along(x, y):  # how far along the wall: x where it runs across the view, y where down it
        return x if (x - 3, y) in top and (x + 3, y) in top else y
    for (x, y) in top:
        a = along(x, y) + int(noise2(along(x, y) // 3, 0, seed) * 2)
        c = STONE[4] if a % 3 == 0 else STONE[3] if noise2(a // 3, 1, seed) > 0.3 else STONE[2]
        if a % 3 == 2:
            c = STONE[1]  # the gap between two coping stones
        if (x, y + 1) not in top and c != STONE[1]:
            c = STONE[2]  # the coping's shaded front
        cv.set(x, y, c)
    for (x, y) in top:
        if (x, y - 1) not in top and along(x, y) % 3 == 0:
            cv.set(x, y - 1, STONE[3])
            wall.add((x, y - 1))
    for (x, y) in top:  # its face toward us, eight pixels down to the turf: three courses
        if (x, y + 1) in top:
            continue
        for k in range(1, 9):
            row = (k - 1) // 3
            bx = (x + row * 2 + int(noise2(x // 4, row, seed) * 2)) // 4
            st = noise2(bx, row, seed + 4)
            c = STONE[3] if st > 0.62 else STONE[2] if st > 0.2 else STONE[1]
            if (k - 1) % 3 == 0:
                c = STONE[min(4, [STONE[1], STONE[2], STONE[3]].index(c) + 2)] if c != STONE[1] else STONE[2]  # a stone's lit top
            if (k - 1) % 3 == 2 or (x + row * 2 + int(noise2(x // 4, row, seed) * 2)) % 4 == 3:
                c = STONE[0]  # the joints
            if k == 1:
                c = STONE[1]  # under the coping's overhang
            if k in (3, 4, 5, 6) and noise2(x, y + k, seed + 1) > 0.93:
                c = '#B8B47A'  # lichen
            cv.set(x, y + k, c)
            wall.add((x, y + k))
        for d in (9, 10):
            style.darken(cv, x + 1, y + d)  # its shadow on the turf at its foot
        if noise2(x, y, seed + 3) > 0.7:
            detail.grass_tuft(cv, x, y + 10, int(noise2(x, 1, seed) * 6), G, 2)
    return wall


def riverside(frame: int = 0):
    """The Riverside, east of the garden: the garden's stream comes in at the west edge
    exactly where it leaves the garden (same line, width and bluff) and widens into a
    slow river. It runs east past the watermill, whose wheel turns in a stone race off
    the north bank with a towpath along the mill's front, then swings south through the
    lower meadow toward the park. Stepping stones cross where it is still narrow; willows
    lean over its west bank, where a path ends at a fishing platform; reeds grow in the
    shallows at its banks and a heron wades at the outer bend (no lilies: the water
    flows). Hay is made on the north meadow by the hives, and old trees close in on the
    east under the forest. The miller works at the mill's door, the angler on the bank."""
    cv = Canvas(W, H)
    ground.valley(cv, 'riverside', frame)  # one turf across the valley (ground.py)
    # the garden's forest-edge shade carried round its north-east corner into the first
    # rows, thinning east (Claude B's garden_meadow.riverside_edge_shade, #75), so the
    # garden|riverside seam meets in one tone
    import garden_meadow
    for y in range(0, 28):
        for x in range(0, 90):
            sh = garden_meadow.riverside_edge_shade(x, y)
            if sh > 0.12:
                style.darken(cv, x, y)
            if sh > 0.55:
                style.darken(cv, x, y, (0.78, 0.8, 0.84))
    river, deep, line = river_in('riverside')
    river, deep = set(river), set(deep)
    top = {}
    for (x, y) in river:
        if y < 360:
            top[x] = min(top.get(x, 999), y)
    # the north bank, as in the garden: Claude B's natural earth bank (B12, E19), sinking
    # into the meadow as the river turns away south; dressed stone only under the mill's
    # towpath and landing, where people use the bank
    bluff = set()
    for x in range(0, 240):
        if x not in top:
            continue
        h = int((7 + int(smooth_noise(x + 320, 3, 9, 92) * 3)) * min(1.0, max(0.0, (240 - x) / 80)))
        if h > 0:
            bluff |= earth_bluff(cv, x, top[x] - h, h, x + 320, built=112 <= x < 214)
    bank(cv, river, keep=bluff, seed=1402)
    water_body(cv, river, deep, seed=1403, glints=90)
    # the stepping stones where it is still narrow, steps cut down the bluff to them
    sx0 = 46
    ys = sorted(y for (x, y) in river if x == sx0)
    for k, sy in enumerate(range(ys[0] + 2, ys[-1], 6)):
        sx = sx0 - 2 + (3 if k % 2 else -2)
        for (x, y) in blob(sx, sy, 4, 2.5, seed=1404 + k, rough=0.15):
            cv.set(x, y, STONE[4] if (x - sx) + (y - sy) < -1 else STONE[3] if (x - sx) + (y - sy) < 2 else STONE[2])
        cv.hline(sx - 4, sy + 3, 9, WTR[4])
    stones = {(x, y) for x in range(38, 54) for y in range(ys[0] - 2, ys[-1] + 3)}
    # the steps cut down through the bluff (Claude A's E4: they read as more wall): a
    # flight of treads worn pale in the middle, each with its dark riser below, between
    # the cut's cheeks, the east cheek in shadow
    steps = {(x, y) for (x, y) in bluff if 38 <= x < 54}
    for (x, y) in steps:
        k = (y - top[x]) % 3
        if x == 38:
            c = STONE[3]
        elif x == 53:
            c = STONE[0]
        elif k == 1:
            c = STONE[1]  # the riser, in shadow
        elif k == 2:
            c = P[3] if 42 <= x <= 49 else STONE[4]  # the tread, worn to earth in its middle
        else:
            c = STONE[3]  # the tread's front edge
        cv.set(x, y, c)
    stones |= steps
    # the mill on the north bank: its race off the river to the wheel, and a towpath of
    # flags along its front, where its door opens, joining the lane from the garden
    mx = 218
    mt = top.get(mx, 300)
    # the mill's water (Claude A after #73, Claude B's edge-on wheel #77): a brook comes
    # down off the wooded slope in the north-east into a small millpond behind the mill;
    # a stone-lined headrace leaves the pond by a sluice and drops into the wheel pit's
    # north end at about axle height (breastshot, the wheel turning north side down); the
    # pit runs south between coursed stone walls and its tailrace spills into the river
    # (Claude A after #86: not out of the world's edge) the brook rises at a spring in the
    # zone's north-east corner, welling up into a small pool at the foot of a heap of
    # mossy boulders, and runs down wide enough to read
    # (A after #109: further in from the world's edge, its pool a cell or two across)
    spring_pool = blob(282, 76, 12, 6, seed=1409, rough=0.2)
    brook = worlds.thick([(284, 80), (288, 98), (286, 118), (270, 178), (248, 202)], 3.5, seed=1410)
    pond = blob(236, 206, 19, 9, seed=1411, rough=0.18)
    lead = {(x, y) for x in range(mx - 2, mx + 12) for y in range(212, mt - 30)}
    millwater = (brook | pond | spring_pool) - lead
    bank(cv, millwater, seed=1412)
    water_body(cv, millwater, set(pond) | set(spring_pool), seed=1413, glints=10)
    spring_rocks = outcrop(cv, [(270, 70, 16, 12), (298, 72, 18, 13), (284, 66, 22, 14), (292, 56, 14, 10), (274, 58, 12, 9)],
                           seed=1408, moss=True)
    for k in range(5):  # the water welling out from under the stones
        cv.set(278 + k * 2, 71, WTR[4] if k % 2 else '#E8F0F2')
    race = {(x, y) for x in range(mx - 6, mx + 16) for y in range(214, mt + 2)}
    for (x, y) in race:
        inner = mx - 3 <= x < mx + 13
        if not inner:  # its walls: coursed stone, lit on the west face's top, dark joints
            k = (y + (x // 3) * 2) % 4
            c = STONE[1] if k == 0 else STONE[3] if x < mx else STONE[2]
            if x in (mx - 6, mx + 15):
                c = STONE[0]
        else:  # the water: running south in streaks, white where it falls off the wheel
            streak = (y * 2 - x // 2 + int(noise2(x, y // 4, 1414) * 6)) % 9
            c = WTR[3] if streak == 0 else WTR[1] if streak in (4, 5) else WTR[2]
            if mt - 8 <= y < mt - 2 and noise2(x, y, 1415) > 0.55:
                c = '#E8F0F2'  # foam at the wheel's foot
        cv.set(x, y, c)
    for x in range(mx - 3, mx + 13):  # the sluice board across the headrace by the pond
        cv.set(x, 222, WOOD[2]); cv.set(x, 223, WOOD[0])
    for y in range(219, 226):
        cv.set(mx - 4, y, WOOD[1]); cv.set(mx + 13, y, WOOD[1])
    race |= millwater | spring_rocks
    towpath = {(x, y) for x in range(118, mx - 6) for y in range(mt - 20, mt - 6)}
    # the lane to the mill, in from the garden's footpath at the same rows and width at
    # the seam (garden rows 112-119, Claude B's #75), then down the meadow to the mill yard
    # (Claude A's E4: no ruled X where the ways meet) the cart track forks off it in a Y
    # at about (60, 190) for the hay field, and the stepping stones' path comes up from
    # the river to meet it in a T at about (66, 214)
    path = worlds.thick([(-8, 116), (14, 116)], 4) | worlds.thick([(12, 116), (34, 132), (52, 166), (62, 194), (76, 226), (118, mt - 11)], 7, seed=21)
    deck_x = min(x for (x, y) in river if y == 432) - 6
    path |= worlds.thick([(8, 402), (60, 398), (110, 418), (200, 430), (deck_x + 2, 432)], 8, seed=22)  # the west bank walk
    path |= blob(110, 280, 22, 8, seed=1406, rough=0.15)  # the mill yard by the sacks, where the lane comes in
    path |= worlds.thick([(46, ys[0] - 2), (46, 262), (48, 240), (56, 224), (68, 216)], 7, seed=23)  # the stepping stones' path up to the lane
    path |= worlds.thick([(46, ys[-1] + 2), (46, 360), (40, 398)], 5, seed=24)  # and down to the bank walk
    path |= worlds.thick([(204, 432), (230, 458), (236, 486)], 5, seed=25) | blob(236, 490, 8, 6, seed=1416, rough=0.2)  # to a trodden patch at the bench's front, between it and the bend (E3; A after #109)
    path |= worlds.thick([(58, 186), (88, 184), (122, 178), (156, 172), (176, 166)], 6, seed=26)  # the cart track up to the hay field's gateway
    path |= {(x, y) for (x0, y) in path if x0 == 0 for x in range(-12, 0)}  # runs on across the seam
    lay_road(cv, {(x, y) for (x, y) in path if (x, y) not in river and (x, y) not in bluff}, seed=77,
             avoid=river | bluff | race | towpath | stones)
    worlds.paint_paving(cv, towpath, seed=1405)
    for x in range(118, mx - 6):
        cv.set(x, mt - 6, STONE[1]); cv.set(x, mt - 5, STONE[0])  # its kerb above the water
    # a landing out over the race before the mill's door, so the door opens onto room to
    # stand and load, not a ledge (Claude A after #64/#68): flags on a stone pier with its
    # lit kerb lower down and its shadow on the water
    landing = {(x, y) for x in range(158, 206) for y in range(mt - 7, mt + 4)}
    worlds.paint_paving(cv, landing, seed=1407)
    for x in range(158, 206):
        cv.set(x, mt + 3, STONE[1]); cv.set(x, mt + 4, STONE[0])
        for k in (5, 6):
            if (x, mt + k) in river:
                style.darken(cv, x, mt + k)
    for y in range(mt - 5, mt + 4):
        cv.set(157, y, STONE[1]); cv.set(206, y, STONE[0])
    for px in (160, 180, 200):  # stone piers under its front, standing in the water
        for y in range(mt + 5, mt + 10):
            for x in range(px, px + 4):
                cv.set(x, y, STONE[2] if x < px + 3 else STONE[0])
            cv.set(px, y, STONE[3])
        for k, y in enumerate(range(mt + 5, mt + 10)):  # its cutwater, pointed upstream (E5)
            for x in range(px - min(k, 4 - k) - 1, px):
                cv.set(x, y, STONE[3] if y < mt + 7 else STONE[1])
        cv.hline(px - 3, mt + 10, 8, WTR[4])  # the ripple round its foot
        cv.set(px + 4, mt + 7, '#E8F0F2'); cv.set(px + 5, mt + 8, WTR[4])  # the water breaking past it
    towpath |= landing
    # the fishing platform at the end of the bank walk, out over the slack water
    deck = dipping_deck(cv, deck_x, 424, 16, 14, river)  # out to mid-stream, not across it
    for (rx, ry, n) in ((deck_x - 18, 460, 6), (300, 330, 5), (250, 520, 7), (120, 310, 5), (180, 318, 4)):
        if (rx, ry) in river or any((rx + d, ry) in river for d in (-3, 3)):
            reeds(cv, rx, ry, seed=rx, n=n)
    for i in range(160):  # wildflowers on the north meadow, thickest by the hives
        x, y = 14 + int(noise2(i, 0, 530) * 120), 30 + int(noise2(i, 1, 530) * 110)
        col = ('#F2D27A', '#E8A0BC', '#FFFFFF', '#B8A0E8')[i % 4]
        cv.set(x, y, col); cv.set(x, y + 1, '#447A50')
    # the hay meadow above the mill (Claude A's E6): mown along its length, the stubble in
    # pale and darker swathes as the mower went up and back, the cut grass raked into
    # windrows across it, the bales made lying on the rows; the bees work the uncut
    # margin. Its south side runs level by the gateway, where the cart track comes in.
    hay = poly_field([(130, 72), (246, 50), (276, 132), (204, 152), (150, 158)], seed=1201)
    HG = (128, 72)

    def along(x, y):  # distance across the rows: the rows run with the field's north side
        return y - HG[1] + 0.19 * (x - HG[0])

    def row(x0, n, w=20):  # the foot row of a bale w wide set at x0 on the n-th windrow
        return int(HG[1] + 12 * n + 10 - 0.19 * (x0 + w // 2 - HG[0]))
    for (x, y) in hay:
        v = along(x, y)
        sw = int(v) % 12
        c = G[3] if (int(v) // 6) % 2 else G[4]  # the stubble, a swathe each way
        if (x + 2 * y) % 5 == 0:
            c = G[2]  # its cut stalks in short rows
        if sw == 9:
            c = '#D9C67A' if (x // 2) % 3 else '#C9B66A'  # the windrow's lit top
        elif sw == 10:
            c = '#B39E58'
        elif sw == 11:
            c = '#8E7C44' if x % 2 else G[2]  # its shade on the stubble
        cv.set(x, y, c)
    margin(cv, hay, seed=1203)  # the uncut margin under the hedge
    # its hedge, stood up with a face toward us, and a field gate hung on timber posts in
    # the gateway on the level south side (the cart track arrives in front of it)
    GX, GY = 176, 157  # the gateway's middle on the south side
    fold_wall = hedgerow(cv, hay, gap=(GX, GY, 12), seed=1204, tall=8)
    gate_posts = [(GX - 11, GY + 1), (GX + 11, GY + 1)]  # (x, foot row) of each post
    for (px, fy) in gate_posts:
        for y in range(fy - 19, fy + 1):
            for x in range(px - 1, px + 2):
                cv.set(x, y, WOOD[3] if x == px - 1 else WOOD[1] if x == px + 1 else WOOD[2])
        cv.hline(px - 1, fy - 19, 3, WOOD[4])  # its sawn top, lit
        for y in range(fy - 18, fy + 1):
            style.darken(cv, px + 2, y + 1)
        fold_wall |= {(x, y) for x in range(px - 1, px + 2) for y in range(fy - 19, fy + 1)}
    lc = [(x, y) for (x, y, h) in line]
    # the heron's feet in the edge of the water at the outer bend (the sprite's feet are
    # 9 px in and at its foot row), a stride inside the bank's lip
    heron_x, heron_y = next((x - 24, y - 30) for y in range(330, 360) for x in range(300, 240, -1)
                            if (x, y) in river and (x + 1, y) not in river)
    objects = [
        ('mill', 'water_mill', 140, mt - 104), ('willow-1', 'willow', 176, 300), ('willow-2', 'willow', 96, 470),
        ('heron', 'heron', heron_x, heron_y),  # wading in the shallows at the outer bank
        ('tree-1', 'tree', 66, 306), ('bush-1', 'bush', 40, 500),  # off the stepping stones, on the south bank
        ('bench', 'bench_east', 200, 472),  # on the bank above the bend, turned to look out over the water (E3)
        ('sack-1', 'sack', 146, mt - 28), ('barrel-m', 'barrel', 200, mt - 32),
        # old trees on the east bank, running on into the forest beyond
        ('pine-e2', 'pine', 280, 470), ('tree-e3', 'tree_autumn', 260, 226),
        ('bush-e4', 'bush', 286, 540),
        # the bales lying on the windrows, where the baler dropped them along a row
        *[(f'bale-{k + 1}', key, bx, row(bx, n) - h) for k, (key, bx, n, h) in enumerate(
            (('round_bale', 160, 2, 26), ('round_bale_side', 210, 5, 21), ('round_bale', 236, 2, 26)))],
        ('hay-gate', 'field_gate', gate_posts[0][0] + 1, gate_posts[0][1] - 24), ('hive-1', 'beehive', 40, 40), ('hive-2', 'beehive_b', 66, 46),
    ]
    blocked = ((river | bluff | race) - stones - deck - towpath) | fold_wall
    blocked |= {(x, y) for x in range(gate_posts[0][0], gate_posts[1][0]) for y in range(GY - 3, GY + 2)}  # the gate, shut
    stands = {'garden-north': (8, 116), 'garden-south': (8, 402), 'mill': (190, mt - 14), 'hayfield': (GX, GY + 12), 'stones': (46, (ys[0] + ys[-1]) // 2),
              'willows': (120, 426), 'platform': (deck_x + 8, 430)}
    return cv, objects, stands, blocked


def dipping_deck(cv: Canvas, x0: int, y0: int, w: int, h: int, water: set) -> set:
    """A small timber platform built out over the edge of a pond, where a path ends:
    planks laid east-west, a lit front edge and two posts into the water, its shadow on
    the water. Returns its pixels (walkable)."""
    BL = MATERIALS['bleached']
    deck = {(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)}
    for (x, y) in deck:
        r = (y - y0) % 3
        c = BL[4] if r == 0 else BL[3] if r == 1 else BL[1]
        if x == x0 + w - 1:
            c = BL[2]
        cv.set(x, y, c)
    for x in range(x0, x0 + w):
        cv.set(x, y0 + h, BL[1]); cv.set(x, y0 + h + 1, WOOD[0] if x in (x0 + 1, x0 + w - 2) else WTR[0])
    for (px) in (x0 + 1, x0 + w - 2):
        cv.set(px, y0 + h + 2, WOOD[0]); cv.hline(px - 1, y0 + h + 3, 3, WTR[4])
    for y in range(y0, y0 + h + 2):
        for x in range(x0 + w, x0 + w + 3):
            if (x, y) in water:
                style.darken(cv, x, y)
    return deck


def park(frame: int = 0):
    """The Town Park, east of Crossroads Town: the river comes down from the riverside
    along the park's west side, and the town's street crosses it on a stone bridge into
    the park, then runs on to the fountain plaza, where benches look onto the fountain
    and the ice cream cart stands at its edge. North of the plaza a ring of paths goes
    round the bandstand; south, a path goes down through the lawns to a timber platform
    on the river bank, with a willow leaning over the water and a pair of mallards
    dabbling in the slack water by the platform (no lilies: the river flows). Trees
    gather in clumps, thickest on the east toward the old forest."""
    cv = Canvas(W, H)
    ground.valley(cv, 'park', frame)  # one turf across the valley (ground.py)
    river, deep, line = river_in('park')
    river, deep = set(river), set(deep)
    PX, PY = 200, 322  # the fountain plaza

    def on(y):  # the river's middle at row y (for things that float on it)
        return int(river_at('park', y))
    RX, RY = 222, 150  # the bandstand's ring
    paths = worlds.thick([(-8, 300), (100, 300)], 13)  # the town's street, unchanged, over the bridge
    paths |= worlds.thick([(96, 300), (PX - 30, 304)], 11, seed=27)
    paths |= {(x, y) for (x, y) in oval(RX, RY, 76, 46)} - {(x, y) for (x, y) in oval(RX, RY, 60, 33)}
    paths |= worlds.thick([(PX, PY - 20), (RX - 4, RY + 50)], 9, seed=29)  # plaza to the ring
    paths |= {(x, y) for (x, y) in oval(PX, PY, 44, 26)}
    deck_y = 436
    dx = max(x for (x, y) in river if y == deck_y + 6) - 4
    paths |= worlds.thick([(PX - 20, PY + 22), (150, 400), (dx + 20, deck_y + 6)], 8, seed=28)  # down to the river
    bridge_rows = range(290, 312)
    bx0 = min(x for (x, y) in river if y in bridge_rows) - 6
    bx1 = max(x for (x, y) in river if y in bridge_rows) + 7
    paths -= river
    # the town's street comes in as trodden earth, as it left the town, and the park's
    # paving starts at the bridge (one rule by grade, Claude A's E2)
    street = {(x, y) for (x, y) in paths if x < bx0 and 288 <= y <= 314}
    lay_road(cv, street | {(x, y) for (x0, y) in street if x0 == 0 for x in range(-12, 0)}, seed=78, avoid=river, worn=0.6)
    worlds.paint_paving(cv, paths - street, seed=11)
    ring = bank(cv, river, seed=1101)
    water_body(cv, river, deep, seed=1104, glints=60)
    for (x, y) in sorted(ring):
        if (x, y - 1) in river and noise2(x, y, 1105) > 0.9:
            detail.pebble(cv, x, y, STONE)
    bridge = stone_bridge(cv, bx0, bx1, 291, 310, river)
    deck = dipping_deck(cv, dx, deck_y, 18, 12, river)
    for (ry, side, n) in ((520, 1, 6), (60, -1, 5), (470, -1, 5), (180, 1, 4)):
        # reeds in the shallows at a bank, never mid-channel
        xs = [x for (x, y) in river if y == ry]
        reeds(cv, (max(xs) - 1) if side > 0 else (min(xs) + 1), ry, seed=ry, n=n)
    for fb in ((bx1 + 4, 268, 40, 16, 1), (bx1 + 4, 316, 40, 16, 2)):  # flanking the street at the bridge
        meadow.flower_planter(cv, *fb)
    objects = [
        ('bandstand', 'bandstand', RX - 39, RY - 50), ('fountain', 'fountain', PX - 27, PY - 32),
        # the willow on the east bank, leaning out over the water; the mallards in the
        # slack water off the platform, where people stop and bread comes their way
        ('willow', 'willow', 70, 466),
        ('duck-1', 'duck', dx - 22, deck_y + 2), ('duck-2', 'duck', on(deck_y + 18) - 4, deck_y + 9), ('heron', 'heron', max(x for (x, y) in river if y == 524) - 15, 494),  # wading, its feet in the shallows
        # trees in clumps round the lawns, thickest on the east
        ('tree-1', 'tree', 230, 10), ('tree-1b', 'tree_small', 196, 24), ('tree-2', 'tree_autumn', 260, 200),
        ('tree-3', 'tree', 4, 110), ('tree-4', 'tree_small', 275, 420), ('tree-5', 'tree', 260, 470),
        ('tree-6', 'tree_small', 200, 480), ('tree-7', 'pine', 284, 300), ('tree-8', 'tree', 176, 470),
        # benches looking onto the fountain and the river
        ('bench-1', 'bench', PX - 52, PY - 66), ('bench-2', 'bench', PX + 20, PY - 66),
        # lamps beside the walks, each clear of the planters and the cart
        ('lamp-1', 'lamp', bx1 + 46, 250), ('lamp-2', 'lamp', PX - 56, 306), ('lamp-3', 'lamp', 178, 400),
        ('icecream', 'ice_cream_cart', PX + 44, PY - 6), ('bush-1', 'bush', 160, 100), ('bush-2', 'bush', 288, 90),
        ('bush-3', 'bush', 230, 540), ('bush-4', 'bush', 284, 548),
    ]
    stands = {'town': (8, 300), 'bandstand': (RX, RY + 56), 'fountain': (PX, PY + 34), 'pond': (dx + 8, deck_y + 6)}
    return cv, objects, stands, (river - bridge - deck)


def ridge(frame: int = 0):
    """The Snowy Ridge, north of the garden: the trail comes up out of the garden's
    treeline at the bottom (the same x, through the same dark forest floor), climbs
    through thinning pines onto an alpine meadow with an open tarn and cairns, then
    by steps up a stone face to the terrace where the cabin stands under the peaks.
    Snow lies only above the face (world logic): the pines, the tarn and the meadow
    below it are clear of it."""
    SNOWm, STONEm = MATERIALS['snow'], MATERIALS['stone']
    cv = Canvas(W, H)
    alpine = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']
    ground.valley(cv, 'ridge', frame)  # one turf across the valley (ground.py)
    # the terrace: everything above the face is high ground under snow
    def rim(x):
        # (Claude A's E20: not an even garden wall) the terrace's edge comes forward and
        # goes back in buttresses and bays
        return 210 + int(math.sin(x / 27) * 5 + math.sin(x / 61 + 0.4) * 9 + noise2(x // 6, 0, 442) * 6)
    FACE_H = 24

    def face_h(x):
        # the face tapers out toward the west edge: Fir Hollow beyond lies at the
        # meadow's level, so the rock foot sinks and a snow bank runs down to the grass
        # instead of ending in a cut at the seam (Claude A's review, 15:54)
        t = min(1.0, max(0.0, (x - 10) / 44))
        return int((FACE_H - 1) * (t * t * (3 - 2 * t)))
    for x in range(W):
        r = rim(x)
        bank_to = r + (FACE_H - 1 - face_h(x))  # the snow bank's foot where the face is low
        for y in range(0, bank_to):  # snow: soft drifts, wind ripples, blue in the hollows
            if y >= r and smooth_noise(x, y, 5, 449) > 0.82 and y > bank_to - 3:
                continue  # the bank's lower edge frays into the turf
            n = smooth_noise(x, y, 18, 443)
            c = SNOWm[3] if n > 0.4 else SNOWm[2] if n > 0.22 or (x + y) % 2 else SNOWm[1]
            rip = (y * 2 + int(math.sin(x / 13 + y / 31) * 4)) % 9
            if rip == 0 and n > 0.3:
                c = SNOWm[2]  # sastrugi: the wind's ripples
            elif rip == 1 and n > 0.3:
                c = SNOWm[3]
            cv.set(x, y, c)
        for d in range(3 if face_h(x) >= 3 else 0):
            if (x + d) % 2 or d == 0:
                style.darken(cv, x, r + FACE_H + d)
    for i in range(26):  # rocks poking through the snow, each with snow on its top
        x, y = int(noise2(i, 0, 447) * W), 70 + int(noise2(i, 1, 447) * 130)
        if y < rim(x) - 6:
            detail.pebble(cv, x, y, STONEm, big=i % 3 == 0)
            cv.set(x, y - 1, SNOWm[3]); cv.set(x + 1, y - 1, SNOWm[3])
    # along the top: the stepped rock shoulders up to the Snow Saddle, one band with the
    # saddle's (frost_zones.shoulders), open where the switchback comes down
    shoulder = shoulders(cv, 'ridge')
    # the terrace's face: stacked blocks with lit ledges and snow on them, not bands
    snow_lip = [SNOWm[0], SNOWm[0], SNOWm[1], SNOWm[2], SNOWm[3]]
    tall = [x for x in range(W) if face_h(x) >= 3]
    # the face in strata: long beds of rock dipping gently east, not blocks laid as a wall
    cliff(cv, {x: rim(x) + FACE_H - face_h(x) for x in tall}, {x: face_h(x) for x in tall}, seed=446, lip=snow_lip,
          cw=26, ch=5, dip=0.09)
    for x in tall:  # the snow's lip: a cornice hanging over the edge, deeper in some places
        t0 = rim(x) + FACE_H - face_h(x)
        hang = int(smooth_noise(x, 0, 7, 455) * 5) + (2 if noise2(x // 3, 1, 456) > 0.8 else 0)
        for k in range(hang):
            cv.set(x, t0 + k, SNOWm[3] if k < hang - 1 else SNOWm[1])
        style.darken(cv, x, t0 + hang)  # the cornice's blue shadow on the rock
    # scree: fans of broken stone below the face where it has come down
    for (sx, sw) in ((40, 18), (96, 14), (236, 22), (300, 16)):
        if sx not in tall:
            continue
        fy = rim(sx) + FACE_H
        for i in range(34):
            t = noise2(i, 0, 457 + sx)
            px = sx + int((noise2(i, 1, 457 + sx) - 0.5) * sw * (0.3 + t))
            py = fy + 1 + int(t * 12)
            detail.pebble(cv, px, py, STONEm, big=noise2(i, 2, 457 + sx) > 0.75)
    for x in range(W):  # snow lying on the ledges
        for k in range(2, FACE_H - 4):
            y = rim(x) + 1 + k
            if cv.get(x, y)[:3] == _rgb(STONEm[4]) and noise2(x // 2, y, 448) > 0.45:
                cv.set(x, y, SNOWm[3] if (x + y) % 3 else SNOWm[2])
    # the alpine tarn below the face, open water (no snow lies down here)
    WTR = MATERIALS['water']
    tarn = blob(232, 404, 38, 15, seed=1301, rough=0.18)
    for (x, y) in tarn:
        d = math.hypot((x - 232) / 38, (y - 404) / 15)
        c = WTR[1] if d < 0.6 else WTR[2]
        if (x, y - 1) not in tarn or (x, y - 2) not in tarn:
            c = STONEm[1]
        cv.set(x, y, c)
    for (x, y) in blob(232, 405, 43, 19, seed=1301, rough=0.18):
        if (x, y) not in tarn:
            cv.set(x, y, STONEm[3] if (x + y) % 3 else STONEm[2])  # a stony shore
    for k in range(5):
        gx = 206 + k * 11
        if (gx, 400 + k % 2) in tarn:
            cv.hline(gx, 400 + k % 2, 3, WTR[4])
    # the trail: up from the garden, round the tarn, steps up the face, to the cabin
    trail = worlds.thick([(206, H + 12), (206, H - 40), (190, 470), (150, 400), (130, 330), (150, 270), (150, 220)], 9.5, seed=29)
    trail |= worlds.thick([(150, 220), (150, 170), (120, 140)], 8, seed=30)
    # on up through the gap to the Snow Saddle, and west across the terrace to Fir Hollow
    # the switchback up past the cabin's east end to the saddle (Codex: it "reveals the
    # cabin roof"), and west across the meadow to Fir Hollow at its port
    trail |= gthick('ridge', [(150, -382), (214, -380), (262, -396), (274, -446), (258, -514), (204, -546), (204, -586)], 8)
    # (the switchback runs clear of the cabin's east end, so it reads all the way down;
    # Claude A after #70) and a trodden way from the stair top to the cabin's door
    cdx, cdy = door_front('cabin', 150, 80)
    trail |= worlds.thick([(156, 196), (cdx - 2, cdy + 12), (cdx, cdy + 2)], 6, seed=31)
    trail |= gthick('ridge', [(132, -240), (60, -228), (-10, -228)], 8)
    on_terrace = {(x, y) for (x, y) in trail if y < rim(x)}
    lay_road(cv, {(x, y) for (x, y) in trail if y >= rim(x) + FACE_H} | {(x, y) for (x0, y) in trail if y == H - 1 for x in [x0] for y in range(H, H + 12)},
             seed=78, avoid={(x, y) for x in range(W) for y in range(0, rim(x) + FACE_H)})
    # the bottom: the forest floor in the shade of the two clumps of pines either side of
    # the trail, darkest under their crowns, with a ragged edge, deepening toward the
    # garden's treeline below (no ruled band)
    clumps = [(36, H - 46, 64, 52), (100, H - 34, 34, 30), (272, H - 50, 64, 56), (300, H - 120, 34, 40), (16, H - 120, 34, 36)]
    for y in range(H - 200, H):
        for x in range(W):
            if (x, y) in trail:
                continue
            sh = max(1 - math.hypot((x - cx) / rx, (y - cy) / ry) for (cx, cy, rx, ry) in clumps)
            sh += (smooth_noise(x, y, 8, 449) - 0.5) * 0.5 + max(0, (y - (H - 26)) / 26) * 0.6
            if sh > 0.12:
                style.darken(cv, x, y)
            if sh > 0.55:
                style.darken(cv, x, y, (0.78, 0.8, 0.84))
    for (x, y) in trail:  # the trail under the trees in dappled shade
        if y > H - 60 and smooth_noise(x, y, 5, 450) > 0.55:
            style.darken(cv, x, y, (0.85, 0.86, 0.9))
    # the trodden path in the snow: a darker worn centre and footprints along it
    tc = {}
    for (x, y) in on_terrace:
        tc.setdefault(y, []).append(x)
    def depth(x, y):  # how far in from the trodden way's edge (each branch on its own)
        for r in (1, 2, 3):
            if any((x + a, y + b) not in on_terrace for (a, b) in ((r, 0), (-r, 0), (0, r), (0, -r))):
                return r
        return 4
    for (x, y) in on_terrace:
        dd = depth(x, y)
        c = SNOWm[0] if dd >= 3 and (x + y) % 3 else SNOWm[1] if dd >= 2 else SNOWm[2]
        cv.set(x, y, c)
    for y, xs in tc.items():
        if y % 6 == 0:
            mid = (min(xs) + max(xs)) // 2 + (1 if (y // 6) % 2 else -2)
            cv.set(mid, y, '#7E8FA6'); cv.set(mid + 1, y, '#7E8FA6')
    # the steps cut into the face: treads lit, risers in shade, a cheek wall each side
    # the stair up the face, a flight 34 px wide (E20: not a ladder), its treads level
    # across its width
    steps = set()
    for (x, y) in trail:
        if rim(x) <= y < rim(x) + FACE_H + 1:
            steps.add((x, y))
    SX = sorted(steps)[len(steps) // 2][0] if steps else 150
    for x in range(SX - 17, SX + 18):
        steps |= {(x, y) for y in range(min(rim(x), rim(SX)), rim(x) + FACE_H + 1)}
    sx = {}
    for (x, y) in steps:
        sx.setdefault(y, []).append(x)
    for (x, y) in steps:
        k = (y - rim(SX)) % 5
        c = STONEm[4] if k == 0 else STONEm[3] if k == 1 else STONEm[2] if k == 2 else STONEm[1]
        if k == 4:
            c = STONEm[0]
        if noise2(x // 3, y // 5, 451) > 0.85 and k in (0, 1):
            c = SNOWm[2]  # snow drifted onto a tread
        cv.set(x, y, c)
    for y, xs in sx.items():
        for (cxw, lit) in ((min(xs) - 1, True), (min(xs) - 2, True), (max(xs) + 1, False), (max(xs) + 2, False)):
            cv.set(cxw, y, STONEm[3] if lit else STONEm[1])
        cv.set(min(xs) - 3, y, STONEm[0]); cv.set(max(xs) + 3, y, STONEm[0])
    objects = [
        # two clumps of pines either side of the trail, running down into the garden's treeline
        ('pine-b1', 'pine', 0, H - 96), ('pine-b2', 'pine', 34, H - 82), ('pine-b3', 'pine', 70, H - 112),
        ('pine-b7', 'pine', 18, H - 140), ('pine-b4', 'pine', 238, H - 88), ('pine-b5', 'pine', 270, H - 108),
        ('pine-b6', 'pine', 284, H - 150), ('pine-b8', 'pine', 252, H - 160),
        ('pine-m1', 'pine', 14, 392), ('pine-m2', 'pine', 270, 440), ('pine-m3', 'pine', 270, 250),
        ('pine-m4', 'pine', 60, 250), ('cairn-1', 'cairn', 100, 360),
        ('cairn-2', 'cairn', 176, 250), ('boulder-1', 'boulder', 20, 430), ('stone-1', 'stone', 280, 470),
        ('cabin', 'cabin', 150, 80), ('campfire', 'campfire', 110, 176), ('pine-t1', 'snowy_pine', 10, 120),
        ('pine-t3', 'snowy_pine', 40, 118),
        ('woodpile', 'woodpile', 122, 138), ('sled', 'sled', 214, 190), ('snowman', 'snowman', 90, 96),
        ('marmot', 'marmot_rock', 220, 470),
        ('cotton-1', 'cotton_grass', 196, 380), ('cotton-2', 'cotton_grass', 270, 398), ('cotton-3', 'cotton_grass', 210, 418),
    ]
    face = {(x, y) for x in range(W) for y in range(rim(x) + FACE_H - face_h(x) - 1, rim(x) + FACE_H) if face_h(x) >= 3}
    stands = {'garden': (206, H - 8), 'tarn': (186, 424), 'cabin': (200, 176), 'campfire': (146, 204),
              'saddle': (204, 6), 'hollow': (4, 348)}
    return cv, objects, stands, (face - steps) | shoulder | tarn


def shore_distance(water: set, cap: int = 90) -> dict:
    """How far each water pixel lies from the nearest land, in px (up to `cap`)."""
    from collections import deque
    dist, q = {}, deque()
    for (x, y) in water:
        if any((x + dx, y + dy) not in water and 0 <= x + dx < W and 0 <= y + dy < H
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            dist[(x, y)] = 0
            q.append((x, y))
    while q:
        x, y = q.popleft()
        d = dist[(x, y)]
        if d >= cap:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in water and n not in dist:
                dist[n] = d + 1
                q.append(n)
    return dist


def sea(cv: Canvas, water: set, seed: int = 0, calm=frozenset(), surf: bool = True, depth=None, open_edges=''):
    """The sea: pale over the sand in the shallows, deepening in broad soft-edged
    bands away from land to the open sea's deep blue with long swells (the same water
    as beyond-sea, so it runs on past the valley); a broken line of foam where it
    meets the shore and a second line of surf coming in. `calm` water (inside the
    harbour) has no surf, only a dark lap at the wall."""
    dist = shore_distance(water)
    ox = depth.ox if depth else 0
    for (x, y) in water:
        gx = x + ox
        d = (depth(x, y) if depth else dist.get((x, y), 90)) + (smooth_noise(gx, y, 26, 979) - 0.5) * 22
        if (x, y) in calm:
            d = min(d, 36)
        # where the world's sea runs on past the zone's edge (beyond-sea), the water at
        # the edge is the open sea's, so the two meet without a seam
        e = min([x for c in 'w' if c in open_edges] + [W - 1 - x for c in 'e' if c in open_edges]
                + [H - 1 - y for c in 's' if c in open_edges] + [999])
        d = max(d, 76 - e * 2.2)
        chk = (x // 2 + y // 2) % 2
        if d < 5:
            c = WTR[3]
        elif d < 8:
            c = WTR[3] if chk else WTR[2]
        elif d < 26:
            c = WTR[2]
        elif d < 32:
            c = WTR[2] if chk else WTR[1]
        elif d < 60:
            c = WTR[1]
        else:
            n = smooth_noise(gx, y, 40, 861)
            c = WTR[0] if n > 0.55 else WTR[1]
            if d < 66 and chk:
                c = WTR[1]
        sw = (y + int(math.sin(gx / 23) * 4 + smooth_noise(gx, y, 60, 862) * 8)) % 19
        if (x, y) in calm:
            sw = -1
        if d > 46 and sw == 0 and noise2(gx // 9, y // 19, 864) > 0.25:
            c = WTR[2] if d > 56 else WTR[3]
        elif d > 50 and sw == 1 and noise2(gx // 5, y // 19, 863) > 0.8:
            c = '#F4F8F8'  # a whitecap out on the open sea
        cv.set(x, y, c)
    for (x, y) in water:  # the waterline
        dd = dist.get((x, y), 90)
        if (x, y) in calm:
            if dd == 0:
                cv.set(x, y, WTR[0])
            elif dd == 1 and (x + y) % 3:
                cv.set(x, y, WTR[1])
            continue
        if not surf:
            continue
        wob = int((smooth_noise(x, y, 5, seed + 1) - 0.5) * 3)
        if dd == 0 or (dd == 1 and (x + y) % 3):
            cv.set(x, y, FOAM)
        elif dd == 2 and (x // 2 + y) % 3:
            cv.set(x, y, WTR[4])
        elif dd == 6 + wob and smooth_noise(x, y, 9, seed + 2) > 0.45:
            cv.set(x, y, WTR[4] if (x + y) % 4 else FOAM)  # the next wave coming in
        elif dd == 7 + wob and smooth_noise(x, y, 9, seed + 2) > 0.5 and (x + y) % 2:
            cv.set(x, y, WTR[3])
    return dist


def cliff(cv: Canvas, top: dict, height: dict, seed: int = 0, lip=None, cw: int = 11, ch: int = 7, dip: float = 0.0) -> set:
    """A rock face seen from the front, from its turf lip at `top[x]` down `height[x]`
    px: stacked irregular blocks, each with a lit ledge along its top, a dark crevice
    under it and down its right side, the odd one mossy or darker; wet and dark with
    weed at its foot. The lip is turf breaking over the edge in tufts. `cw` x `ch` is
    the blocks' size; long low blocks with a `dip` lay the rock in tilted strata."""
    lip = lip or G
    face = {(x, y) for x, t in top.items() for y in range(t, t + height[x])}
    if not face:
        return face
    seeds = {}

    def cell(x, y):
        return x // cw, int(y + dip * x) // ch

    def seed_of(gx, gy):
        return (gx * cw + noise2(gx, gy, seed) * (cw - 1), gy * ch + noise2(gx, gy, seed + 1) * (ch - 1))
    owner = {}
    for (x, y) in face:
        gx, gy = cell(x, y)
        best, bd = None, 1e9
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                sd = seeds.get((gx + ox, gy + oy))
                if sd is None:
                    sd = seeds[(gx + ox, gy + oy)] = seed_of(gx + ox, gy + oy)
                d = ((x - sd[0]) / (1.5 * cw / 11)) ** 2 + (y + dip * x - sd[1]) ** 2
                if d < bd:
                    best, bd = (gx + ox, gy + oy), d
        owner[(x, y)] = best
    for (x, y) in face:
        b = owner[(x, y)]
        k = y - top[x]
        t = 3 if noise2(b[0], b[1], seed + 2) > 0.55 else 2
        if noise2(b[0], b[1], seed + 3) > 0.9:
            t = 1
        up, dn, rt, lf = owner.get((x, y - 1)), owner.get((x, y + 1)), owner.get((x + 1, y)), owner.get((x - 1, y))
        if up != b:
            c = STONE[min(4, t + 1)] if up is not None else STONE[4]
        elif dn != b and dn is not None:
            c = STONE[0]
        elif rt != b and rt is not None:
            c = STONE[0] if (x + y) % 3 else STONE[1]
        elif lf != b and lf is not None:
            c = STONE[t + 1] if t < 3 else STONE[3]
        else:
            c = STONE[t]
            if noise2(x, y, seed + 4) > 0.93:
                c = STONE[t - 1]  # a pit in the stone
        if up != b and noise2(b[0], b[1], seed + 5) > 0.7 and (x + b[0]) % 3:
            c = LEAF[2] if (x + y) % 2 else LEAF[3]  # moss on the ledge
        foot = height[x] - k
        if foot <= 4:
            c = STONE[1] if c in (STONE[2], STONE[3], STONE[4]) else c
            if foot <= 2:
                c = '#2E4A3A' if (x + y) % 2 else STONE[0]  # weed and wet rock at the waterline
        cv.set(x, y, c)
    for x, t in top.items():  # the turf lip breaking over the edge
        cv.set(x, t - 1, lip[1])
        cv.set(x, t - 2, lip[3] if x % 3 else lip[4])
        if noise2(x // 2, t, seed + 6) > 0.5:
            cv.set(x, t, lip[2]); 
            if noise2(x, t, seed + 7) > 0.6:
                cv.set(x, t + 1, lip[1])
    return face


# ---------------------------------------------------------------------------------------
# The valley's river, in the valley's own coordinates (world-ports.md, "the valley's
# water"; Matt, 19 Oct: "the world does not need to be divided into screen sized
# sections"). The garden's stream leaves the garden at the riverside's west edge, runs
# east past the mill, swings south through the riverside's lower meadow, down the park's
# west side under the town street's bridge, along the Headland's west edge under the cliff
# path's bridge, and out into Driftwood's basin by the quay's east end. Every zone it
# crosses cuts its own part from the one line, so it meets itself at every border.
# ---------------------------------------------------------------------------------------
def _catmull(pts, step: float = 1.0):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


@functools.lru_cache(maxsize=1)
def river_course():
    """The river's centre line, sampled every pixel, with its half-width there."""
    pts = [(320 + x, meadow.stream_centre(x + 320) + x * 0.06) for x in range(0, 101, 20)]
    pts += [(470, 309), (536, 312), (584, 340), (600, 404), (582, 470), (536, 520), (498, 556), (488, 580),
            (476, 620), (450, 680), (420, 760), (396, 840), (384, 920), (376, 1020), (368, 1110), (366, 1160),
            (366, 1230), (365, 1300), (360, 1356), (346, 1390), (322, 1402), (302, 1410), (288, 1430), (281, 1452),
            (279, 1470)]
    line = _catmull(pts)
    out = []
    total = len(line)
    for i, (x, y) in enumerate(line):
        t = i / total
        if 400 < y < 1350:  # meanders on its way south, straightening where it crosses a border
            seam = min(y % 576, 576 - y % 576)
            x += 8 * math.sin(y / 38 + 1.3) * min(1.0, seam / 70) * min(1.0, (y - 400) / 60)
        if x < 380 and y < 400:  # still the garden's stream, as it leaves the garden
            h = 9 + (smooth_noise(x, 0, 13, 91) - 0.5) * 2.4 + max(0, x - 320) / 60 * 2
        else:
            h = 11 + 5 * min(1, t * 2) + (smooth_noise(i, 0, 60, 1401) - 0.5) * 9 + max(0, t - 0.88) * 30
        out.append((x, y, h))
    return out


@functools.lru_cache(maxsize=None)
def river_in(zone: str):
    """The river's water in one zone's pixels, its deep channel, and its centre points."""
    col, row = LAYOUT['valley'][zone]
    ox, oy = col * W, row * H
    water, deep, line = set(), set(), []
    for (x, y, h) in river_course():
        lx, ly = x - ox, y - oy
        if -40 <= lx < W + 40 and -40 <= ly < H + 40:
            line.append((lx, ly, h))
            for (px, py) in disc(lx, ly, h):
                if 0 <= px < W and 0 <= py < H:
                    water.add((px, py))
                    if math.hypot(px - lx, py - ly) < h * 0.45:
                        deep.add((px, py))
    return frozenset(water), frozenset(deep), tuple(line)


def river_at(zone: str, y: int):
    """The river's centre x in a zone at row y (None if it does not cross that row)."""
    best = None
    for (x, yy, h) in river_in(zone)[2]:
        if abs(yy - y) < 0.7:
            best = x
    return best


def stone_bridge(cv: Canvas, x0: int, x1: int, y0: int, y1: int, water: set, horizontal: bool = True):
    """A stone bridge carrying a road east-west over the river (Claude A's E16: built,
    not a flat slab): a paved deck between two parapets of coursed stone under a lit
    coping, a pier standing a little proud at each end; on the downstream (south) face,
    an arch ring of voussoirs round the arch's dark mouth with its keystone proud at the
    crown, coursed spandrels either side, the abutments carried down to the banks, wing
    walls splaying out along them, and pointed cutwaters at the arch's feet in the water,
    the arch's reflection below. Returns the deck (walkable)."""
    deck = {(x, y) for x in range(x0, x1) for y in range(y0, y1)}
    worlds.paint_paving(cv, deck, seed=x0)
    span = [x for x in range(x0, x1) if any((x, y1 + 8 + k) in water for k in range(3))]
    a, b = (min(span), max(span)) if span else (x0, x1)
    cx, r = (a + b) / 2, max(4, (b - a) / 2)
    rise = max(5, int(r * 0.55))  # a segmental arch, lower than a half circle
    spring = y1 + 12  # the springing line, at the water
    FACE = range(y1 + 3, spring + 3)
    for x in range(x0 - 4, x1 + 4):
        # the spandrel's coursed face, then the arch cut out of it
        for y in FACE:
            k = y - y1
            c = STONE[2] if (x + ((k - 3) // 3) * 5) % 9 else STONE[1]
            if (k - 3) % 3 == 2:
                c = STONE[1]
            elif (k - 3) % 3 == 0 and (x + ((k - 3) // 3) * 5) % 9:
                c = STONE[3]
            if k == 3:
                c = STONE[1]  # the string course's shadow under the parapet
            cv.set(x, y, c)
    for x in range(int(cx - r) - 2, int(cx + r) + 3):  # the arch: its ring of voussoirs, its mouth
        d = (x - cx) / (r + 2)
        if abs(d) > 1:
            continue
        ring_top = spring - int(math.sqrt(1 - d * d) * (rise + 2))
        d2 = (x - cx) / r
        mouth_top = spring - int(math.sqrt(max(0, 1 - d2 * d2)) * rise) if abs(d2) <= 1 else spring
        for y in range(ring_top, mouth_top):
            vou = int(math.degrees(math.atan2(spring - y, x - cx)) // 12)  # a wedge every 12 degrees
            cv.set(x, y, STONE[1] if (y - ring_top == 0 and False) else (STONE[3] if vou % 2 else STONE[2]))
            if math.degrees(math.atan2(spring - y, x - cx)) % 12 < 2:
                cv.set(x, y, STONE[0])  # the joint between two voussoirs
        for y in range(mouth_top, spring + 3):
            cv.set(x, y, WTR[0] if y > mouth_top + 1 else '#1C2A3A')  # the dark under the arch
    for dx in (-1, 0, 1):  # the keystone, proud at the crown
        x = int(cx) + dx
        top_y = spring - rise - 4
        for y in range(top_y, spring - rise + 1):
            cv.set(x, y, STONE[4] if dx < 1 else STONE[2])
    cv.set(int(cx) - 1, spring - rise - 4, '#F2EEE2')
    for (fx, sgn) in ((a, -1), (b, 1)):  # cutwaters at its feet, pointed into the stream
        for k in range(5):
            for w in range(4 - k // 2):
                x = fx + sgn * w
                y = spring + 2 + k
                if (x, y) in water:
                    cv.set(x, y, STONE[2] if w < 2 else STONE[1])
        cv.hline(fx - 3, spring + 7, 7, WTR[4])  # the ripple round it
    for x in range(int(cx - r), int(cx + r) + 1):  # the arch's reflection
        for k in range(3, 6):
            if (x, spring + k) in water and abs(x - cx) < r - 1:
                cv.set(x, spring + k, WTR[1] if (x + k) % 3 else WTR[2])
    # the abutments and their wing walls, carried down onto the banks either side
    for (ex, sgn) in ((x0 - 4, -1), (x1 + 3, 1)):
        for k in range(0, 9):
            for w in range(0, 3):
                x = ex + sgn * (k // 2 + w)
                y = spring - 6 + k
                if (x, y) not in water and 0 <= x < W:
                    cv.set(x, y, STONE[2] if w == 1 else STONE[3] if w == 0 else STONE[1])
            style.darken(cv, ex + sgn * (k // 2 + 3), spring - 6 + k)
    for x in range(x0 - 4, x1 + 4):  # the parapets: coursed stone under a lit coping
        for (py, lit) in ((y0 - 4, True), (y1, False)):
            for k in range(4):
                c = STONE[2] if (x + k * 3) % 7 else STONE[1]
                if k == 0:
                    c = STONE[4] if lit else STONE[3]  # the coping's top
                    if x % 8 == 0:
                        c = STONE[2]  # a joint in the coping
                elif k == 1:
                    c = STONE[1]  # the coping's drip, in shadow
                cv.set(x, py + k, c)
    for ex in (x0 - 4, x1 + 1):  # a pier at each end, a little taller than the parapet
        for py in (y0 - 4, y1):
            for x in range(ex, ex + 3):
                cv.set(x, py - 1, STONE[4] if x < ex + 2 else STONE[2])
                for k in range(0, 4):
                    cv.set(x, py + k, STONE[3] if x == ex else STONE[2] if x == ex + 1 else STONE[1])
    return deck


def poly_field(pts, seed: int = 0) -> set:
    """A field laid out by hand along the lie of the land: a four-sided plot whose sides
    run at their own angles (fields are rarely square to anything), each side wandering a
    pixel or two with the ground (point-in-polygon on a slightly jittered point)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    out = set()
    for y in range(min(ys) - 3, max(ys) + 4):
        for x in range(min(xs) - 3, max(xs) + 4):
            jx = x + (smooth_noise(x, y, 11, seed) - 0.5) * 4
            jy = y + (smooth_noise(x, y, 11, seed + 1) - 0.5) * 4
            inside = False
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                if (ay > jy) != (by > jy) and jx < ax + (jy - ay) * (bx - ax) / (by - ay):
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def poly(pts) -> set:
    """The pixels inside a polygon, its sides ruled straight (built things: a square's
    kerb, a yard's wall), where poly_field lets a side wander with the ground."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    out = set()
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            jx, jy = x + 0.5, y + 0.5
            inside = False
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                if (ay > jy) != (by > jy) and jx < ax + (jy - ay) * (bx - ax) / (by - ay):
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def hedgerow(cv: Canvas, mask: set, gap=None, seed: int = 0, sides=None, tall: int = 0) -> set:
    """A hedge laid round a field (the field edge Claude A asked for after #56/#59): a band
    of hawthorn and hazel five to seven pixels deep along the field's edge, bumpy on top,
    lit from the upper left and dark under its south face, with its shadow on the grass.
    `gap` (x, y, r) leaves a gateway open; `sides` limits it to edge pixels for which
    sides(x, y) is true. Returns the hedge's pixels (they block a walk).
    `tall` > 0 stands the hedge up (Claude A's E6: a flat band reads as a painted line):
    its crown is lifted that many pixels and the face toward us hangs below it to the
    ground, darker and dappled, its foot ragged, the shadow on the grass at its foot."""
    LEAFR = ['#24402A', '#33552F', '#4A6E38', '#628A42', '#80A552']
    edge = [p for p in edge_of(mask) if (sides is None or sides(*p))]
    if gap is not None:
        edge = [(x, y) for (x, y) in edge if math.hypot(x - gap[0], y - gap[1]) > gap[2]]
    hedge = set()
    for (x, y) in edge:
        for (a, b) in _disc(3):
            hedge.add((x + a, y + b - 2 - tall))
        if tall and noise2(x // 4, y // 4, seed + 7) > 0.5:  # its top in rounded bushes
            hedge |= {(x + a, y - 6 - tall + b) for (a, b) in _disc(2)}
    face = set()
    if tall:
        for (x, y) in hedge:
            if (x, y + 1) not in hedge:
                foot = tall + (1 if noise2(x, y, seed + 5) > 0.6 else 0)
                face |= {(x, y + k) for k in range(1, foot + 1)}
        face -= hedge
        for (x, y) in face:
            n = noise2(x // 2, y // 2, seed + 6)
            c = LEAFR[1] if n > 0.55 else LEAFR[0] if n < 0.2 else '#2B4A2C'
            if (x, y - 1) in hedge or (x, y - 2) in hedge:
                c = '#1C3322'  # deep in the shade of the crown's overhang
            if (x, y + 1) not in face:
                c = '#1C3322'
            elif (x - 1, y) not in face and (x - 1, y) not in hedge:
                c = LEAFR[2]  # the face's lit west end
            cv.set(x, y, c)
    for (x, y) in sorted(hedge, key=lambda p: p[1]):
        n = noise2(x // 2, y // 2, seed)
        up, down = (x, y - 1) not in hedge, (x, y + 1) not in hedge
        left = (x - 1, y) not in hedge
        c = LEAFR[3] if n > 0.5 else LEAFR[2]
        if up:
            c = LEAFR[4] if n > 0.35 else LEAFR[3]
        elif left and n > 0.4:
            c = LEAFR[3]
        if down and not tall:
            c = LEAFR[0]
        elif (x, y + 2) not in hedge and not tall:
            c = LEAFR[1]
        elif down:
            c = LEAFR[3] if n > 0.3 else LEAFR[2]  # the crown's rounded lip over the face
        if noise2(x, y, seed + 1) > (0.992 if tall else 0.96):
            c = '#E8E2D0'  # a may blossom
        cv.set(x, y, c)
    hedge |= face
    shade = {(x + 1, y + k) for (x, y) in hedge for k in (1, 2)} - hedge - (set() if tall else mask)
    for q in shade:
        if 0 <= q[0] < W and 0 <= q[1] < H:
            style.darken(cv, *q)
    return hedge


def field_mask(x0: int, y0: int, x1: int, y1: int, seed: int = 0) -> set:
    """A worked field: a plot set out by hand, roughly rectangular, with corners rounded
    where the plough turned and sides that wander a pixel or two with the ground."""
    pts = set()
    r = 9
    for y in range(y0, y1):
        wl = int((smooth_noise(0, y, 14, seed) - 0.5) * 4)
        wr = int((smooth_noise(1, y, 14, seed) - 0.5) * 4)
        for x in range(x0 + wl, x1 + wr):
            dx = max(x0 + r - x, 0, x - (x1 - r))
            dy = max(y0 + r - y, 0, y - (y1 - r))
            if dx * dx + dy * dy <= r * r:
                pts.add((x, y))
    return pts


def tilled(cv: Canvas, mask: set, row: int = 9, seed: int = 0, ridged: bool = True):
    """Ploughed earth in east-west rows: each ridge lit along its top, the furrow beside
    it in shade, clods and the odd stone; or (unridged) dug earth in soft patches."""
    S = MATERIALS['soil']
    y0 = min(y for _, y in mask)
    for (x, y) in mask:
        if ridged:
            r = (y - y0) % row
            c = S[4] if r == 0 else S[3] if r < 3 else S[2] if r < row - 2 else S[1]
            if r in (1, 2) and noise2(x // 2, y, seed) > 0.85:
                c = S[4]  # a clod catching the light
        else:
            n = smooth_noise(x, y, 5, seed)
            c = S[3] if n > 0.55 else S[2]
            if noise2(x // 2, y // 2, seed + 1) > 0.9:
                c = S[4]
        cv.set(x, y, c)


def rows_of(mask: set, row: int, step: int, seed: int = 0):
    """Plant positions along a field's ridges: set out by hand, so evenly spaced but
    each a little off its mark, and now and then one missing."""
    y0 = min(y for _, y in mask)
    xs = [x for x, _ in mask]
    out = []
    k = 0
    for y in range(y0 + 4, max(y for _, y in mask) - 2, row):
        off = (step // 2) * ((y - y0) // row % 2)
        for x in range(min(xs) + 5 + off, max(xs) - 3, step):
            k += 1
            if noise2(x, y, seed) < 0.06:
                continue
            cx, cy = x + int((noise2(x, y, seed + 1) - 0.5) * 2), y
            if all((cx + dx, cy + dy) in mask for dx in (-4, 4) for dy in (-3, 3)):
                out.append((cx, cy, k))
    return out


def cabbage_head(cv: Canvas, cx: int, cy: int, r: float, seed: int = 0):
    """A cabbage on its ridge: a ring of loose outer leaves, darker and veined, round a
    pale tight head lit on its upper left, on its own small shadow."""
    contact(cv, cx + 1, cy + 1, r + 1.5, r * 0.6 + 0.5)
    outer = blob(cx, cy, r + 1.4, (r + 1.4) * 0.8, seed=seed, rough=0.25)
    for (x, y) in outer:
        cv.set(x, y, LEAF[2] if (x - cx) + (y - cy) < 0 else LEAF[1])
    for (x, y) in edge_of(outer):
        if y >= cy:
            cv.set(x, y, LEAF[0])
        elif (x + y) % 2:
            cv.set(x, y, LEAF[3])
    head = disc(cx - 0.3, cy - 0.6, r * 0.8)
    for (x, y) in head:
        d = (x - cx) + (y - cy)
        cv.set(x, y, '#C9E0A0' if d < -r * 0.6 else '#A8C878' if d < r * 0.3 else '#86A85E')
    cv.set(int(cx), int(cy - 0.6), '#86A85E')  # the head's fold


WHEAT = ['#6E4F1E', '#A87E2C', '#C99A3C', '#E2BC5E', '#F2D27A', '#F8E6A0']


def wheat_field(cv: Canvas, mask: set, seed: int = 0):
    """Standing wheat seen from above and a little in front: a dense pile of ears in
    staggered rows, each ear lit on its top, the stems in shade between them; long
    swathes where the wind has laid it lighter; stalks showing along the front edge and
    heads breaking over the back edge; a shaded right side."""
    xs = [x for x, _ in mask]
    x1 = max(xs)
    for (x, y) in mask:  # the shade down among the stalks
        cv.set(x, y, WHEAT[1] if (x + y // 2) % 3 else WHEAT[2])
    ys = [y for _, y in mask]
    for gy in range(min(ys) - 1, max(ys) + 1, 3):
        for gx in range(min(xs) + (gy // 3 % 2) * 2, x1 + 1, 4):
            if noise2(gx, gy, seed) < 0.08:
                continue
            ex = gx + int((noise2(gx, gy, seed + 1) - 0.5) * 3)
            ey = gy + int((noise2(gx, gy, seed + 2) - 0.5) * 2)
            wind = smooth_noise(ex + ey * 0.5, ey, 10, seed + 3) > 0.6
            lean = 1 if wind else 0
            shade = 1 if ex > x1 - 5 else 0
            ear = [(ex + lean, ey, WHEAT[5 - shade] if not wind else WHEAT[5]), (ex, ey + 1, WHEAT[4 - shade]),
                   (ex + 1, ey + 1, WHEAT[3 - shade]), (ex, ey + 2, WHEAT[3 - shade]), (ex + 1, ey + 2, WHEAT[2 - shade])]
            for (px, py, c) in ear:
                if (px, py) in mask:
                    cv.set(px, py, c)
    for (x, y) in edge_of(mask):
        if (x, y + 1) not in mask:  # the front edge: stalks standing on the ground
            for k in range(1, 3):
                if (x, y + k) not in mask and x % 2 == 0:
                    cv.set(x, y + k, WHEAT[1] if k == 1 else WHEAT[0])
        if (x, y - 1) not in mask and x % 2:  # the back edge: ears nodding over it
            cv.set(x, y - 1, WHEAT[4])
            cv.set(x, y, WHEAT[5])


PUMPKIN = ['#6A2E12', '#A44C1A', '#D46E26', '#EE9840', '#FFC97A']


def pumpkin(cv: Canvas, cx: int, cy: int, w: int, seed: int = 0):
    """A pumpkin lying on the earth: a squat ribbed round, lit on its upper left, a dark
    groove between the ribs, a woody stalk, and its shadow."""
    h = max(3, int(w * 0.7))
    contact(cv, cx + 1, cy + h // 2, w / 2 + 1, 1.5)
    pts = blob(cx, cy, w / 2, h / 2, seed=seed, rough=0.06)
    for (x, y) in pts:
        f = (x - cx) / (w / 2) + (y - cy) / (h / 2) * 0.8
        c = PUMPKIN[4] if f < -0.95 else PUMPKIN[3] if f < -0.2 else PUMPKIN[2] if f < 0.6 else PUMPKIN[1]
        if abs((x - cx) % max(3, w // 3)) == 0 and abs(x - cx) < w / 2 - 1 and f > -0.9:
            c = PUMPKIN[1] if f > -0.2 else PUMPKIN[2]  # the grooves between the ribs
        cv.set(x, y, c)
    for (x, y) in edge_of(pts):
        if y >= cy:
            cv.set(x, y, PUMPKIN[0])
    top = min(y for _, y in pts)
    cv.set(cx, top - 1, WOOD[2]); cv.set(cx + 1, top - 1, WOOD[1]); cv.set(cx, top, WOOD[1])


def pumpkin_patch(cv: Canvas, mask: set, seed: int = 0):
    """Pumpkins growing on the dug earth: vines wandering across it with broad leaves
    in clumps, and pumpkins of every size lying along them."""
    xs, ys = [x for x, _ in mask], [y for _, y in mask]
    vines = []
    for v in range(7):
        x, y = min(xs) + 6 + v * (max(xs) - min(xs) - 12) // 6, min(ys) + 6 + int(noise2(v, 0, seed) * 8)
        a = noise2(v, 1, seed) * 6.28
        for t in range(70):
            a += (noise2(v, t, seed + 1) - 0.5) * 0.9
            x += math.cos(a) * 1.1
            y += abs(math.sin(a)) * 0.6 + 0.25
            if (int(x), int(y)) not in mask:
                break
            cv.set(int(x), int(y), LEAF[2])
            vines.append((int(x), int(y), v, t))
    for (x, y, v, t) in vines:
        if t % 9 == 4:  # a broad leaf
            for (lx, ly) in blob(x, y, 3, 2.2, seed=v * 31 + t, rough=0.3):
                if (lx, ly) in mask:
                    cv.set(lx, ly, LEAF[3] if (lx - x) + (ly - y) < 0 else LEAF[2])
            cv.set(x - 1, y - 1, LEAF[4]); cv.set(x + 1, y + 2, LEAF[1])
    spots = [(x, y, v) for (x, y, v, t) in vines if t % 19 == 11]
    for (x, y, v) in sorted(spots, key=lambda s: s[1]):
        w = 8 + int(noise2(x, y, seed + 2) * 6)
        if all((x + dx, y + dy) in mask for dx in (-w // 2 - 1, w // 2 + 1) for dy in (-3, 3)):
            pumpkin(cv, x, y, w, seed=v)


def margin(cv: Canvas, mask: set, seed: int = 0):
    """The uncut margin round a field: long grass tufts along its edge, thickest at the
    corners, the odd poppy and cornflower in it."""
    for (x, y) in edge_of(mask):
        q = [(x + dx, y + dy) for dx, dy in ((0, 2), (0, -2), (2, 0), (-2, 0)) if (x + dx, y + dy) not in mask]
        if not q or noise2(x, y, seed) > 0.42:
            continue
        gx, gy = q[0]
        detail.grass_tuft(cv, gx, gy + 1, int(noise2(x, y, seed + 1) * 6), G, 3)
        n = noise2(x, y, seed + 2)
        if n > 0.93:
            cv.set(gx, gy - 2, '#D8463A'); cv.set(gx + 1, gy - 2, '#B0303A')  # a poppy
        elif n < 0.05:
            cv.set(gx, gy - 2, '#5A7AD0')  # a cornflower


def halt(frame: int = 0):
    """The Valley Halt, west of Crossroads Town and south of the Woodland: the lane from
    the town comes in at the east edge and opens on the platform, where the little stone
    station faces the line under its canopy; the rails run west out of the valley (the
    train to Cogsworth) and stop at a buffer before the town. A windmill turns on the
    meadow to the north under the woodland's edge; south of the line, behind a fence, a
    small farm: cabbages, wheat with a scarecrow, a pumpkin patch, haystacks and a red
    barn, reached by a track down the east side."""
    cv = Canvas(W, H)
    ground.valley(cv, 'halt', frame)  # one turf across the valley (ground.py)
    # (the woodland's forest floor reaches down over the top: ground.py blends it)
    lane = worlds.thick([(W + 12, 300), (W - 12, 300)], 11) | worlds.thick([(W - 10, 300), (230, 296), (190, 290)], 11, seed=31)
    lane |= {(x, y) for (x0, y) in lane if x0 == W - 1 for x in range(W, W + 12)}
    # the platform: dressed slabs with a white edge over the line
    plat = {(x, y) for x in range(64, 236) for y in range(282, 318)}
    worlds.paint_paving(cv, plat, seed=13)
    cv.hline(64, 316, 172, '#F4F0E6'); cv.hline(64, 317, 172, STONE[1])
    for y in range(282, 318):  # the platform's west end: a ramp down, edged
        cv.set(64, y, STONE[1]); cv.set(65, y, STONE[3])
    paint_rails(cv, 322)
    # west of the platform the line runs into a cutting through the rising ground, out of
    # the valley under the trees: a retaining wall on its north side, a grassy bank on
    # its south, both closing in toward the edge
    cut = set()
    for x in range(0, 62):
        depth = 4 + int((62 - x) / 62 * 10)
        top = 318 - depth
        detail.stones(cv, x, top, 1, depth + 1, STONE, seed=461 + x // 9, course=4, base=2)
        cv.set(x, top - 1, G[1]); cv.set(x, top - 2, G[3] if x % 3 else G[4])
        for y in range(top, 319):
            cut.add((x, y))
        bank_h = 3 + int((62 - x) / 62 * 8)
        for k in range(bank_h):  # the south bank: turf falling to the ballast
            y = 339 + k - bank_h + 3
            c = G[1] if k == bank_h - 1 else G[2] if k > 1 else G[3]
            if k == 0:
                c = LEAF[1]
            cv.set(x, y, c)
            cut.add((x, y))
        for k in range(2):
            style.darken(cv, x + 1, 320 + k)  # the wall's shadow on the ballast
    for y in range(316, 344):  # the line ends at a buffer before the town
        for x in range(246, W):
            cv.set(x, y, G[2] if (x + y) % 3 else G[3])
    for x in range(232, 244):
        cv.vline(x, 320, 18, WOOD[2] if x % 2 else WOOD[1])
    cv.hline(232, 320, 12, RED[3])
    # a farm track south from the lane, down the east side to the farmyard
    # (the farm ends at its yard: past it, to the south, the old forest begins, so
    # nothing runs off the edge into it; world-rules.md, every path ends at a node)
    # past the farm the land ends at a low sea cliff (the open sea lies south of the halt)
    # its line: coves and points at the scale of the farm, not a straight edge (Claude
    # A's review after #52): a cove at the west corner and one between the pumpkins and
    # the barn, points below the patch and the barn
    def hb(c, w, x):
        return math.exp(-((x - c) / w) ** 2)
    htop = {x: min(558, int(550 - 28 * hb(0, 26, x) + 10 * hb(78, 26, x) - 16 * hb(134, 15, x) + 10 * hb(216, 30, x)
                         + math.sin(x / 41 + 0.7) * 3 + (smooth_noise(x, 0, 13, 455) - 0.5) * 8)) for x in range(W)}
    # at the east the coast turns south to the valley's corner, so the halt's sea meets
    # Driftwood's west shore there and the town's ground stays land (no sea against the
    # town at the seam)
    htop = {x: t + int(max(0, x - 250) ** 2 / 110) for x, t in htop.items()}
    hh = {x: 11 + int(smooth_noise(x, 1, 9, 456) * 5) for x in range(W)}
    hsea = {(x, y) for x in range(W) for y in range(htop[x] + hh[x], H)}
    sea(cv, hsea, seed=457, open_edges='s')
    hface = cliff(cv, {x: t for x, t in htop.items() if t < H}, {x: min(hh[x], H - htop[x]) for x in range(W) if htop[x] < H}, seed=458)
    track = worlds.thick([(298, 300), (304, 360), (300, 440), (292, 492), (262, 526)], 8, seed=33)
    # the farmyard: trodden earth from the track's end along the front of the barn, so its
    # doors open onto the yard (they face south, toward the cliff top)
    yard = blob(236, 526, 64, 14, seed=459, rough=0.15) | blob(196, 532, 52, 9, seed=460, rough=0.12)
    yard = {(x, y) for (x, y) in yard if y < htop[x] - 1}
    # the fields behind the fence: worked plots with softened corners, their rows set out
    # east-west by hand; a margin of long grass round each, where the plough turned
    SOILm = MATERIALS['soil']
    # (each plot set out along the lie of the land, not square to the map: Claude A's
    # review after #56/#59)
    cabbage = poly_field([(16, 378), (138, 370), (144, 462), (12, 470)], seed=81)
    wheat = poly_field([(162, 376), (280, 368), (284, 428), (166, 442)], seed=82)
    patch = poly_field([(20, 486), (106, 480), (112, 528), (22, 522)], seed=83)
    tilled(cv, cabbage, row=9, seed=84)
    tilled(cv, patch, row=11, seed=85, ridged=False)
    for (cx, cy, k) in rows_of(cabbage, row=9, step=8, seed=86):
        cabbage_head(cv, cx, cy, 2.2 + noise2(cx, cy, 87) * 1.3, seed=k)
    wheat_field(cv, wheat, seed=88)
    pumpkin_patch(cv, patch, seed=89)
    for mask in (cabbage, wheat, patch):
        margin(cv, mask, seed=90)
    # a hedge between the line and the fields, where the fence was: it keeps stock and
    # people off the rails, and ends at the farm track and at the cutting
    # (Claude A's E7: one hedge, unbroken from the cutting's wall at the west edge to the
    # farm track, not a stub on each field)
    lineside = hedgerow(cv, poly_field([(-6, 356), (291, 352), (291, 420), (-6, 420)], seed=95), seed=94,
                        sides=lambda x, y: y < 362 and x <= 289, tall=6)
    # the windmill grinds the farm's wheat: a cart track up from the lane to its door,
    # and a cobbled apron round its foot
    mill_track = worlds.thick([(266, 294), (272, 240), (258, 190)], 6, seed=91)
    # the lane, the farm track and the mill track as one network (the platform stays paved)
    lay_road(cv, (lane | track | yard | mill_track) - plat, seed=80,
             avoid=plat | cabbage | wheat | patch | lineside | hface | hsea | {(x, y) for x in range(W) for y in range(310, 344)},
             doors=[door_front('barn', 150, 438)])
    # the mill's apron (Claude A's E9): cobbles laid from its door out to the cart track,
    # narrow at the door and splaying where the carts turn, worn to the earth along the
    # line feet and wheels take, its edge stones sunk unevenly into the turf
    apron = poly([(249, 170), (266, 170), (276, 192), (238, 192)])
    apron = {(x, y) for (x, y) in apron if not (y > 186 and noise2(x // 3, 0, 921) > 0.6 and (x < 244 or x > 270))}
    for (x, y) in apron:
        r = y // 3
        cx = (x + (r % 2) * 2) // 4
        n = noise2(cx, r, 922)
        c = STONE[4] if n > 0.7 else STONE[3] if n > 0.3 else STONE[2]
        if (x + (r % 2) * 2) % 4 == 3 or y % 3 == 2:
            c = STONE[1]  # the joints
        wear = abs(x - (257 + (y - 170) * 0.1)) < 5 - (y - 170) * 0.08
        if wear and noise2(x, y, 923) > 0.45:
            c = P[3] if noise2(x, y, 924) > 0.5 else P[2]  # trodden to earth between the setts
        if (x, y + 1) not in apron:
            c = STONE[1]
        cv.set(x, y, c)
    for (x, y) in apron:
        if (x, y + 1) not in apron and y + 1 < H:
            style.darken(cv, x, y + 1)
    objects = [
        ('station', 'station_house', 66, 204), ('signal', 'semaphore', 40, 244), ('bench-p', 'bench', 190, 280),
        ('lamp-p1', 'lamp', 70, 268), ('pine-c1', 'pine', 0, 228), ('lamp-p2', 'lamp', 220, 268), ('sack-p', 'sack', 178, 300), ('crate-p', 'crate', 160, 298),
        ('pine-n1', 'pine', 10, 20), ('tree-n2', 'tree', 90, 30), ('pine-n3', 'pine', 150, 14),
        ('mill', 'windmill', 226, 70), ('sack-m', 'sack', 276, 160), ('bush-1', 'bush', 286, 200), ('bush-2', 'bush', 6, 200),
        ('scarecrow', 'scarecrow', 204, 384), ('barn', 'barn', 150, 438),
        # the hay stacked against the barn's west wall, by the pumpkin patch, out of the rain
        # (one stack, nothing pasted on its foot; no trough where no stock is kept: E8)
        ('hay-1', 'haystack', 118, 474),
        ('wood-f', 'woodpile', 276, 508), ('barrel-f', 'barrel', 258, 506),
        ('tree-s2', 'tree_autumn', 150, 160),
    ]
    rails = {(x, y) for x in range(0, 246) for y in range(319, 338)}
    stands = {'town': (312, 300), 'platform': (130, 300), 'station': (118, 292), 'mill': (258, 186),
              'farm': (262, 530)}
    return cv, objects, stands, rails | cut | cabbage | wheat | patch | hsea | hface | lineside


def footbridge(cv: Canvas, x0: int, w: int, y0: int, y1: int, water: set):
    """A plank footbridge carrying a path north-south over a stream, in the same
    three-quarter view as the buildings: planks laid across on two log stringers, each
    plank lit along its top edge with grain and a nail at each end, a rail on posts
    along each side (the west rail lit, the east in shade, throwing its shadow on the
    water), and stone abutments on both banks, the south one showing its face."""
    for y in range(y0, y1):
        r = (y - y0) % 3
        pk = (y - y0) // 3
        for x in range(x0, x0 + w):
            t = 3 + (1 if noise2(pk, 0, 791) > 0.8 else -1 if noise2(pk, 0, 791) < 0.2 else 0)
            c = detail.tone(WOOD, t + 1) if r == 0 else detail.tone(WOOD, t) if r == 1 else WOOD[1]
            if r == 1 and noise2(x // 3, pk, 792) < 0.2:
                c = detail.tone(WOOD, t - 1)  # grain
            if x in (x0 + 1, x0 + w - 2) and r == 1:
                c = STONE[1]  # nail heads over the stringers
            cv.set(x, y, c)
    # the stone abutments: a step of dressed stones at each end, the south face lit
    for x in range(x0 - 3, x0 + w + 3):
        for k in range(3):
            y = y0 - 1 - k
            if (x, y) not in water:
                cv.set(x, y, STONE[3] if k == 2 else STONE[2] if (x + k) % 5 else STONE[1])
        for k in range(4):
            y = y1 + k
            c = STONE[4] if k == 0 else STONE[3] if (x + (k // 2) * 3) % 6 else STONE[1]
            if k == 3:
                c = STONE[1]
            cv.set(x, y, c)
    # rails on posts: posts stand at the ends and the middle, the rail runs over them
    for (rx, lit) in ((x0 - 1, True), (x0 + w, False)):
        for y in range(y0 - 4, y1 - 2):
            cv.set(rx, y, WOOD[4] if lit else WOOD[2])
            if not lit:
                cv.set(rx + 1, y, WOOD[1])
        for py in (y0 - 1, (y0 + y1) // 2, y1 - 1):
            for k in range(4):
                cv.set(rx, py - k, WOOD[3] if lit else WOOD[1])
                cv.set(rx + (1 if lit else -1), py - k, WOOD[2] if lit else WOOD[1]) if k == 3 else None
    for y in range(y0 - 2, y1 + 2):  # the bridge's shadow on the water, down and right
        for x in range(x0 + w + 2, x0 + w + 5):
            if (x, y) in water:
                style.darken(cv, x, y)


def woodland(frame: int = 0):
    """The Woodland, west of the garden: the garden's stream is born here. It leaves the
    east edge exactly where it enters the garden, and upstream it springs from a heap of
    mossy boulders, falling in a white ribbon into a rock pool. Old trees close in at
    the edges with the floor going dark under them, light comes through in dappled
    pools, a path winds over a plank bridge to a sunlit glade round the hollow oak, where
    a ring of toadstools has come up in the grass, and south of the stream to the old
    stone circle. Ferns grow where it is damp and shaded."""
    GOLDm = MATERIALS['gold']
    cv = Canvas(W, H)
    ground.valley(cv, 'woodland', frame)  # one turf across the valley (ground.py)
    OFF = -meadow.W

    def centre(x):
        return meadow.stream_centre(x + OFF)

    def half(x):
        # (Claude A after #109: the garden's own width at the seam, not 3 px wider) a
        # trickle of 3 px at the spring widening to the garden stream's half-width
        full = 9 + (smooth_noise(x + OFF, 0, 13, 91) - 0.5) * 2.4
        t = min(1.0, max(0.0, (x - 96) / 120))
        return (full * t + 3 * (1 - t)) * (x >= 96)

    spring_x = 96
    cy = int(centre(spring_x))
    river = {(x, y) for x in range(spring_x, W) for y in range(int(centre(x) - half(x)), int(centre(x) + half(x)) + 1)}
    # the rock pool: an organic basin under the fall, its outlet narrowing into the stream
    pool = blob(spring_x - 10, cy + 1, 22, 11, seed=61, rough=0.2)
    water = river | pool
    deep = {(x, y) for (x, y) in pool if math.hypot((x - spring_x + 12) / 15, (y - cy) / 6) < 1}
    deep |= {(x, y) for (x, y) in river if half(x) > 8 and abs(y - centre(x)) < half(x) * 0.35}
    # the spring's rocks: a heap of mossy boulders behind (north of) the pool, the fall
    # coming down a cleft between them; the meltwater brook from Fir Hollow (frost_zones
    # FALLS_X) runs to the top of the heap under the trees
    fx = spring_x - 16
    brook = worlds.thick([(FALLS_X, -4), (62, 60), (54, 140), (62, 214), (fx + 2, cy - 40)], 3)
    rocks = [(fx - 30, cy - 9, 30, 22), (fx + 22, cy - 9, 28, 20), (fx - 14, cy - 22, 26, 22),
             (fx + 13, cy - 24, 24, 22), (fx - 2, cy - 36, 22, 16), (fx + 32, cy - 20, 16, 12),
             (fx - 40, cy - 20, 18, 13), (fx + 4, cy + 1 - 22 + 22, 1, 1)]
    rocks = [r for r in rocks if r[2] > 2]
    bank(cv, water, keep=set(brook), seed=62)
    water_body(cv, water, deep, seed=63, glints=60)
    for (x, y) in brook:
        if y > cy - 46:
            continue
        c = WTR[2] if (x + y // 2) % 4 else WTR[3]
        if (x - 1, y) not in brook:
            c = WTR[0]
        elif (x + 1, y) not in brook:
            c = WTR[1]
        cv.set(x, y, c)
    for (x, y) in brook:  # mossy stones along the brook
        if (x + 1, y) not in brook and y < cy - 46 and noise2(x, y, 428) > 0.55:
            cv.set(x + 1, y, STONE[2] if (x + y) % 3 else LEAF[2])
        if (x - 1, y) not in brook and y < cy - 46 and noise2(x, y, 429) > 0.7:
            cv.set(x - 1, y, LEAF[1])
    rock = outcrop(cv, rocks, seed=64)
    waterfall(cv, fx - 1, 6, cy - 40, cy - 2, seed=65)
    # moss and drips round the cleft, ferns in the damp at the heap's foot
    for k in range(9):
        cv.set(fx - 3 - (k % 3), cy - 36 + k * 4, LEAF[3] if k % 2 else LEAF[2])
        cv.set(fx + 6 + (k % 2), cy - 34 + k * 4, LEAF[1])
    water = water | {p for p in brook if p not in rock}
    # the path from the garden's west side into the trees and the glade
    # (the garden's orchard walk runs on across the border at the same height and width)
    path = worlds.thick([(W + 12, meadow.ORCHARD_WALK_Y), (250, meadow.ORCHARD_WALK_Y)], 8.5) | worlds.thick([(254, meadow.ORCHARD_WALK_Y), (190, 420), (150, 380), (130, 330)], 9, seed=25)
    path |= worlds.thick([(130, 270), (150, 200), (124, 150)], 9, seed=26)
    path |= worlds.thick([(130, 334), (130, 306)], 7) | worlds.thick([(130, 274), (130, 296)], 7)  # onto the bridge
    # the glade: a sunlit hollow in the trees round the oak, with a wandering edge
    glade = blob(112, 136, 58, 38, seed=66, rough=0.24)
    for (x, y) in glade:
        n = smooth_noise(x, y, 14, 425)
        e = min(math.hypot(x - ex, y - ey) for (ex, ey) in ((112, 136),)) / 60
        if (x, y) not in path:
            c = G[3] if n > 0.42 else G[2]
            if e > 0.75 and (x // 2 + y // 2) % 2 and n < 0.5:
                c = FOREST_FLOOR[3]
            cv.set(x, y, c)
    for (x, y) in edge_of(glade):  # the glade's edge frays into the forest floor in clumps
        if noise2(x // 2, y // 2, 667) > 0.45:
            cv.set(x, y, FOREST_FLOOR[2])
    spur = worlds.thick([(152, 386), (118, 408)], 5, seed=27)  # to the stone circle
    lay_road(cv, spur | {(x, y) for (x, y) in path if (x, y) not in water} | {(x, y) for (x0, y) in path if x0 == W - 1 for x in range(W, W + 12)},
             seed=79, avoid=set(water))
    # the garden's bluff on the north bank runs on and sinks into the ground upstream
    # (in Claude B's natural earth, B12 and E19, so the bank runs on unchanged at the seam)
    nbank, bank_band = set(), set()
    for x in range(150, W):
        bh = int((7 + int(smooth_noise(x + OFF, 3, 9, 92) * 3)) * min(1.0, (x - 150) / 150))
        top = int(centre(x) - half(x))
        if bh > 0:
            nbank |= earth_bluff(cv, x, top - bh, bh, x + OFF)
        bank_band |= {(x, y) for y in range(top - bh - 26, top)}  # the turf just above the bank stays out of the sun pools
    # the stone circle in its own small clearing: a ring of reddish trodden earth round
    # muted grass, the stones standing in it (the reference Matt chose as the bar)
    SX, SY, SRX, SRY = 78, 410, 44, 24
    ring_out = blob(SX, SY, SRX + 2, SRY + 2, seed=68, rough=0.12)
    ring_in = blob(SX, SY, SRX * 0.7, SRY * 0.68, seed=69, rough=0.14)
    for (x, y) in ring_out:
        if (x, y) in ring_in:
            n = smooth_noise(x, y, 9, 428)
            cv.set(x, y, '#86A755' if n > 0.42 else '#76984A')
        else:
            n = noise2(x // 2, y // 2, 429)
            c = '#AE7E64' if n > 0.35 else '#9A6A52'
            if any((x + d, y) in ring_in for d in (-1, 1)) and (x + y) % 2:
                c = '#76984A'  # the grass fraying onto the earth
            cv.set(x, y, c)
    for (x, y) in edge_of(ring_out):
        if (x, y + 1) not in ring_out:
            cv.set(x, y, '#C29A7E')  # the lit outer lip
        elif noise2(x, y, 670) > 0.5:
            cv.set(x, y, '#76984A')
    # where the canopy closes in at the outer edges the floor goes into shade: two calm
    # steps of shadow in broad soft-edged pools (no checker), darkest in the far corner
    keep = set(path) | water | rock | glade | ring_out | nbank
    for y in range(H):
        for x in range(W):
            if (x, y) in keep:
                continue
            d = min(x + 6, y + 18)
            s = (1 - d / 64 + (smooth_noise(x, y, 16, 431) - 0.5) * 0.7) * min(1.0, (H - y) / 70)
            if s > 0.12:
                style.darken(cv, x, y)
            if s > 0.55:
                style.darken(cv, x, y, (0.8, 0.82, 0.86))
    # dappled light through the canopy, and the glade in full sun
    for i in range(10):
        lx, ly = 20 + int(noise2(i, 0, 426) * 290), 170 + int(noise2(i, 1, 426) * 380)
        light_pool(cv, lx, ly, 10 + i % 3 * 4, 5 + i % 2 * 3, GOLDm[2], water | rock | path | nbank | bank_band)  # (never on the bank's face: A after #109)
    sun = blob(108, 128, 40, 24, seed=72, rough=0.3)  # the sun on the glade, in a ragged patch
    for (x, y) in sun - path:
        if smooth_noise(x, y, 6, 673) > 0.35 or (x + y) % 2 == 0:
            c = cv.get(x, y)
            cv.set(x, y, tuple(int(c[i] + (_rgb(G[4])[i] - c[i]) * 0.3) for i in range(3)) + (255,))
    # the fairy ring: toadstools come up in a broken ring in the glade, the grass
    # inside it greener where the ring has fed it (not a grid of one mushroom)
    RX, RY = 154, 162
    for k in range(13):
        a = 2 * math.pi * k / 13 + noise2(k, 0, 671) * 0.4
        rr = 1 + (noise2(k, 1, 671) - 0.5) * 0.25
        mx, my = int(RX + 15 * rr * math.cos(a)), int(RY + 8 * rr * math.sin(a))
        if noise2(k, 2, 671) < 0.15:
            continue
        for (gx, gy) in disc(mx, my, 2.5):
            if (gx, gy) not in path:
                cv.set(gx, gy, G[1] if (gx + gy) % 2 else G[2])
    shrooms = []
    for k in range(13):
        a = 2 * math.pi * k / 13 + noise2(k, 0, 671) * 0.4
        rr = 1 + (noise2(k, 1, 671) - 0.5) * 0.25
        if noise2(k, 2, 671) < 0.15:
            continue
        shrooms.append((int(RX + 15 * rr * math.cos(a)), int(RY + 8 * rr * math.sin(a)), 2 + int(noise2(k, 3, 671) * 3), k))
    for (mx, my, sz, k) in sorted(shrooms, key=lambda m: m[1]):
        mushroom(cv, mx, my, sz, seed=k)
    # ferns where it is damp and shaded: by the spring, along the stream, at the trees' feet
    for (x, y, s) in ((44, 272, 1.1), (fx + 46, cy - 6, 0.9), (180, 352, 1.0), (262, 412, 1.1), (98, 322, 0.9),
                      (154, 244, 1.0), (30, 470, 1.2), (228, 266, 0.85), (20, 330, 1.0), (206, 520, 1.0),
                      (120, 228, 0.8), (290, 350, 0.9), (60, 250, 1.0), (250, 300, 0.9), (300, 470, 1.0), (20, 560, 1.1),
                      (110, 524, 0.9), (270, 236, 0.9), (204, 176, 0.8), (60, 170, 0.9), (16, 404, 1.0), (292, 560, 1.0)):
        if all((x + dx, y + dy) not in path and (x + dx, y + dy) not in water for dx in range(-16, 17, 2) for dy in range(-14, 4, 2)):
            fern(cv, x, y, seed=x * 7 + y, size=s * 1.5)
    for (x, y) in ((fx - 46, cy + 4), (fx + 44, cy + 8), (196, int(centre(196) + half(196)) + 1)):
        reeds(cv, x, y, seed=x)
    # a few fallen leaves gathered in drifts under the deciduous trees
    for i in range(70):
        bx, by = ((200, 150), (60, 500), (250, 520), (30, 220), (230, 340))[i % 5]
        x, y = bx + int((noise2(i, 0, 421) - 0.5) * 50), by + int((noise2(i, 1, 421) - 0.5) * 30)
        if (x, y) in keep:
            continue
        col = ('#B8703A', '#8A4A2A', '#D2A04E')[i % 3]
        cv.set(x, y, col); cv.set(x + 1, y, col); cv.set(x + 1, y + 1, '#4A2E1E')
    objects = [
        # the stone circle
        ('stone-1', 'standing_stone', SX - 10, SY - SRY - 26), ('stone-2', 'standing_stone_b', SX + 26, SY - SRY - 18),
        ('stone-3', 'standing_stone_low', SX + SRX - 8, SY - 10), ('stone-4', 'standing_stone', SX + 22, SY + SRY - 26),
        ('stone-5', 'standing_stone_b', SX - 34, SY + SRY - 28), ('stone-6', 'standing_stone_low', SX - SRX - 4, SY - 14),
        ('stone-7', 'standing_stone_low', SX - 38, SY - SRY - 12),
        ('stump-1', 'stump', 166, 232), ('stump-2', 'stump', 40, 340), ('stump-3', 'stump', 236, 120),
        ('pine-6', 'pine', 0, 110), ('pine-7', 'pine', 110, -44), ('tree-8', 'tree_small', -2, 380),
        ('bush-2', 'bush', 4, 250), ('bush-3', 'bush', 160, 40),
        # old trees closing in round the edges (none crosses the east border into the garden)
        ('tree-1', 'tree', -3, -30), ('pine-1', 'pine', 50, -40), ('tree-2', 'tree', 200, -26), ('pine-2', 'pine', 250, -36),
        ('tree-3', 'tree', -3, 200), ('pine-3', 'pine', 0, 330), ('tree-4', 'tree', 230, 160),
        ('tree-5', 'tree_small', 196, 300), ('pine-4', 'pine', 20, 470), ('tree-6', 'tree', 60, 480),
        ('pine-5', 'pine', 150, 490), ('tree-7', 'tree_small', 250, 504),
        ('oak', 'hollow_tree', 70, 30), ('log-1', 'mossy_log', 200, 230),
        ('log-2', 'mossy_log', 128, 468), ('bench', 'forest_bench', 150, 186),
        ('willow', 'willow', 220, 340), ('bush-1', 'bush', 286, 380),
    ]
    # the plank footbridge where the path crosses the young stream
    by0, by1 = int(centre(130) - half(130)) - 2, int(centre(130) + half(130)) + 3
    plank = {(x, y) for x in range(122, 138) for y in range(by0 - 3, by1 + 4)}
    footbridge(cv, 123, 14, by0, by1, water)
    stands = {'garden': (304, meadow.ORCHARD_WALK_Y), 'clearing': (110, 160), 'spring': (100, int(centre(96)) + 18),
              'stones': (SX, SY + 4)}
    # (Claude A's E18: 17 trees is a parkland, not a wood) the wood itself: belts two or
    # three trees deep along the north, west and south edges, clumps of three to seven
    # standing in the middle ground, young trees and bushes between, about half the floor
    # under crowns; the glade, the circle, the spring, the stream and the paths stay open
    # (no fruit trees in the wild wood: pines and the small wild broadleaf for now)
    spr = sprites()
    def swap(o, key):  # the same tree's foot, drawn as another kind
        oid, k, x, y = o
        a, b = spr[k], spr[key]
        return (oid, key, x + (a.ox + a.w // 2) - (b.ox + b.w // 2), y + (a.oy + a.h) - (b.oy + b.h))
    # the old trees round the edges are oaks and beeches, the small ones birches (Claude B's
    # wild broadleaves, #108, none of them in fruit)
    objects = [swap(o, 'oak') if o[1] == 'tree' else swap(o, ('birch', 'beech')[i % 2]) if o[1] == 'tree_small' else o
               for i, o in enumerate(objects)]
    clear = set(path) | water | set(rock) | set(glade) | set(ring_out) | plank | set(spur)
    clear = {(x + a, y + b) for (x, y) in clear for (a, b) in ((0, 0), (6, 0), (-6, 0), (0, 5), (0, -4))}
    feet = []
    for (_, k, x, y) in objects:
        sp = spr[k]
        feet.append((x + sp.ox + sp.w / 2, y + sp.oy + sp.h))
    wood = []
    for gy in range(-36, H - 20, 12):
        for gx in range(-14, 300, 12):
            jx = gx + int((noise2(gx, gy, 1601) - 0.5) * 10)
            jy = gy + int((noise2(gx, gy, 1602) - 0.5) * 8)
            edge = min(jx + 20, jy + 50, H - jy)
            clump = smooth_noise(jx, jy, 46, 1603)
            if not (edge < 34 and noise2(jx, jy, 1604) > 0.3 or edge < 60 and noise2(jx, jy, 1604) > 0.72
                    or clump > 0.74 and noise2(jx, jy, 1604) > 0.45):
                continue
            r = noise2(jx, jy, 1605)
            key = ('pine' if r < 0.26 else 'oak' if r < 0.44 else 'beech' if r < 0.6 else 'birch' if r < 0.74
                   else 'sapling' if r < 0.82 else 'holly' if r < 0.89 else 'bramble' if r < 0.96 else 'stump')
            sp = spr[key]
            x, y = jx - sp.ox - sp.w // 2, jy - sp.oy - sp.h
            fx, fy = jx, jy
            if not (4 <= fx <= 296 and 8 <= fy < H - 2):
                continue
            if any((fx + a, fy + b) in clear for a in range(-8, 9, 4) for b in range(-6, 3, 3)):
                continue
            if any(math.hypot(fx - ax, fy - ay) < (12 if key in ('sapling', 'holly', 'bramble', 'stump') else 18) for (ax, ay) in feet):
                continue
            if any(math.hypot(fx - sx_, fy - sy_) < 22 for (sx_, sy_) in stands.values()):
                continue
            bx0, by0_, bx1, by1_ = x + sp.ox, y + sp.oy, x + sp.ox + sp.w, y + sp.oy + sp.h
            # nothing stands in front of the ways, the water or the circle and hides them
            seen = [(a, b) for a in range(bx0, bx1, 3) for b in range(by0_, by1_, 3)]
            if sum((a, b) in clear for (a, b) in seen) > 0.06 * len(seen):
                continue
            if bx1 > 150 and bx0 < 244 and by1_ > 132 and by0_ < 182:
                continue  # clear of the forager's round, so nobody walks behind a trunk
            if fx > 250 and abs(fy - meadow.ORCHARD_WALK_Y) < 60:
                continue  # the way in from the garden stays open
            feet.append((fx, fy))
            wood.append((f'wood-{len(wood) + 1}', key, x, y))
    objects += wood
    return cv, objects, stands, (water | rock) - plank
