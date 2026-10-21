"""Border blockers for the rebuilt home valley's grass and woods, wave 1 batch 3 (Claude B;
docs/vision/regions/props.md section 4 on PR #96; Claude A's to-b-2245): thicket, bramble,
gorse, a fallen tree and boulders, each in three sizes for the edge layers (fade clumps
in front, the wall behind), so the edge can be built of uneven patches with no two the
same in a row.

Drawn to the wayside kit's standard (wayside_props.py: house palette ramps and siblings,
light from the upper left, footings on whole 8 px cells, 2 to 4 px clusters, every part
with a reason). Foliage is the house canopy (garden_props.canopy: lobes lit as spheres,
rims, leaf bumps) with leaf clusters laid over it the way Eastward builds its bushes.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval  # noqa: E402
import garden_props as gp  # noqa: E402
import valley_named_props  # noqa: E402,F401  (adds the sand, lamp and sibling ramps to H)
from wayside_props import H, PAD, T, clean, shade_under, stone_px, tuft  # noqa: E402

H.update({
    'berry_warm': ['#3E021E', '#70082F', '#9D243E', '#C1494E', '#DC6858', '#E98B6A'],
    'grass_warm': ['#47420B', '#63641C', '#7E8733', '#99A94D', '#BFC060', '#DFD581'],
    'grass_cool': ['#0F3C26', '#305D37', '#507D49', '#729D5C', '#99B56B', '#BEC883'],
})

CLUMP = ('.###.', '#####', '#####', '.###.')
SMALL = ('##', '##')


def _index(fams):
    at = {}
    for fam in fams:
        for i, hx in enumerate(H[fam]):
            at[tuple(int(hx[k:k + 2], 16) for k in (1, 3, 5))] = i
    return at


def clumps(cv: Canvas, shape, fams, seed: int = 0, pattern=CLUMP, step=(5, 4)):
    """Leaf clusters over a canopy's lobes: clumps on a staggered, jittered grid, each lit
    along its top and west and shaded along its underside from the lobe's own tone at that
    spot, some in a sibling ramp so the bush holds sun-struck and shaded leaves."""
    at = _index(fams)
    pts = set(shape)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    sx, sy = step
    ph, pw = len(pattern), len(pattern[0])
    for gy in range(min(ys), max(ys), sy):
        row = (gy - min(ys)) // sy
        for gx in range(min(xs) + (row % 2) * (sx // 2), max(xs), sx):
            ox = gx + int(noise2(gx, gy, seed) * 2)
            oy = gy + int(noise2(gy, gx, seed + 1) * 2)
            if (ox + pw // 2, oy + ph // 2) not in pts:
                continue
            base = at.get(tuple(cv.get(ox + pw // 2, oy + ph // 2)[:3]))
            if base is None:
                continue
            n = noise2(ox // 10, oy // 8, seed + 2)  # siblings in broad patches, not clump by clump
            fam = fams[0] if n < 0.7 else fams[1 % len(fams)] if n < 0.9 else fams[2 % len(fams)]
            for r, line in enumerate(pattern):
                for c, ch in enumerate(line):
                    x, y = ox + c, oy + r
                    if ch != '#' or (x, y) not in pts:
                        continue
                    i = base + (1 if r == 0 or (r == 1 and c == 0) else -1 if r == ph - 1 else 0)
                    cv.set(x, y, T(fam, max(0, min(5, i))))


def lift_rim(cv: Canvas, fams):
    """Foliage pixels on the silhouette keep a step above the outline (tone 2 at least),
    so the edge reads as one dark line, never a doubled one."""
    at = {}
    for fam in fams:
        for i, hx in enumerate(H[fam]):
            at[tuple(int(hx[k:k + 2], 16) for k in (1, 3, 5))] = (fam, i)
    p = cv.pad
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            c = cv.get(x, y)
            if not c[3]:
                continue
            hit = at.get(tuple(c[:3]))
            if hit and hit[1] < 2 and any(not cv.get(x + dx, y + dy)[3] for dx, dy in ((1, 0), (-1, 0), (0, -1))):
                cv.set(x, y, T(hit[0], 2))


def _lobes(w: int, h: int, n: int, seed: int, rmin: float, rmax: float):
    """A low mound of n lobes across the sprite, the back row higher, listed back to front."""
    out = []
    for k in range(n):
        u = (k + 0.5) / n
        r = rmin + (rmax - rmin) * noise2(k, 1, seed)
        x = 2 + r + u * (w - 4 - 2 * r)
        back = k % 2 == 0
        y = h - 2 - r - (r * 0.55 if back else 0) - noise2(k, 2, seed) * 2
        out.append((round(x), round(y), round(r)))
    out.sort(key=lambda c: c[1])
    return out


# ---- thicket ----------------------------------------------------------------------------

def thicket(size: int = 1) -> Canvas:
    """A thicket of hawthorn and hazel, too dense to push through (the wall layer, and its
    fade clumps in front): low dark lobes in the cool leaf ramp with brighter clusters where
    the sun catches them, the dark mouths under the bushes where stems show, a few haws in
    small red clusters, nettles and grass at the foot. Sizes 0, 1, 2: 24, 40 and 56 wide."""
    w, h = {0: (24, 20), 1: (40, 28), 2: (56, 36)}[size]
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    lobes = _lobes(w, h + 1, {0: 4, 1: 6, 2: 8}[size], 301 + size, 5.0 + size, 7.0 + size * 1.5)
    shape = gp.canopy(cv, lobes, H['leaf_cool'], seed=302 + size, clumps=True)
    clumps(cv, shape, ('leaf_cool', 'leaf', 'leaf_warm'), seed=303 + size)
    for k in range(2 + size * 2):  # a spray of hazel catching the sun on top, a fresher green
        hx = min(p[0] for p in shape) + 3 + int(noise2(k, 9, 305 + size) * max(1, w - 12))
        hy = min(p[1] for p in shape if p[0] == hx) + 1 if any(p[0] == hx for p in shape) else 3
        for (dx, dy, c) in ((0, 0, 5), (1, 0, 4), (0, 1, 4), (1, 1, 3), (2, 1, 3)):
            if (hx + dx, hy + dy) in shape:
                cv.set(hx + dx, hy + dy, T('grass', c))
    for (x, y) in shape:  # the dark mouth under the bushes where it meets the ground, a stem or two showing in it
        if y >= foot - 2 and (x, y + 1) not in shape or y >= foot - 1:
            stem = (x * 7 + size) % 9 == 0
            cv.set(x, y, T('earth', 2) if stem else T('leaf_cool', 0 if y >= foot - 1 else 1))
    lift_rim(cv, ('leaf_cool', 'leaf', 'leaf_warm'))
    for k in range(3 + size * 3):  # haws, in twos and threes
        x = 3 + int(noise2(k, 0, 304 + size) * (w - 6))
        y = 3 + int(noise2(k, 1, 304 + size) * (h - 10))
        if (x, y) in shape and (x + 1, y) in shape and (x, y + 1) in shape:
            cv.hline(x, y, 2, T('berry', 4)); cv.set(x, y + 1, T('berry', 2))
    tuft(cv, 1, foot, 3); tuft(cv, w - 2, foot, 1)
    return cv


# ---- bramble ----------------------------------------------------------------------------

def bramble(size: int = 1) -> Canvas:
    """A bramble patch, low and sprawling: arching canes in a dark red-purple, lit along
    their tops, rooting again where they touch the ground, under a mat of dark leaves in
    clusters; white flowers and blackberries ripening from red to black in small clusters
    (August in the valley). Sizes 0, 1, 2: 24, 32 and 48 wide, knee to hip high."""
    w, h = {0: (24, 14), 1: (32, 18), 2: (48, 22)}[size]
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    lobes = _lobes(w, h + 2, {0: 3, 1: 4, 2: 6}[size], 311 + size, 4.0, 6.0 + size)
    shape = gp.canopy(cv, lobes, H['leaf'], seed=312 + size, clumps=True)
    clumps(cv, shape, ('leaf', 'leaf_cool', 'grass_cool'), seed=313 + size, pattern=('.##.', '####', '.##.'), step=(4, 3))
    lift_rim(cv, ('leaf', 'leaf_cool', 'grass_cool'))
    xs = [p[0] for p in shape]
    for (side, x0) in ((-1, min(xs) + 2), (1, max(xs) - 2)):  # a cane arching out of each side and rooting at its tip
        span = 4 + size * 2
        for t in range(span):
            x = x0 + side * t
            y = foot - 5 - size + int((t / span) ** 2 * (5 + size))
            if 0 <= x < w and y <= foot:
                cv.set(x, y, T('berry_warm', 2 if side < 0 else 1))
    for k in range(2 + size):  # canes arching over the top of the mat, dark against the leaves, lit on their crowns
        x0 = min(xs) + 2 + int(noise2(k, 7, 316 + size) * max(1, (max(xs) - min(xs) - 12)))
        span = 8 + size * 2
        for t in range(span):
            x = x0 + t
            y = min(p[1] for p in shape) + 3 + int((2 * t / span - 1) ** 2 * 4)
            if (x, y) in shape:
                cv.set(x, y, T('berry_warm', 3 if t < span // 2 else 2))
    for k in range(14 + size * 4):  # flowers and fruit in twos
        x = 2 + int(noise2(k, 2, 315 + size) * (w - 5))
        y = 2 + int(noise2(k, 3, 315 + size) * (h - 6))
        if (x, y) in shape and (x + 1, y) in shape:
            kind = k % 3
            c = (T('plaster', 5), T('plaster', 4)) if kind == 0 else (T('berry', 3), T('berry', 2)) if kind == 1 else (T('slate', 2), T('slate', 0))
            cv.set(x, y, c[0]); cv.set(x + 1, y, c[1])
    tuft(cv, 0, foot, 3); tuft(cv, w - 1, foot, 5)
    return cv


# ---- gorse ------------------------------------------------------------------------------

def gorse(size: int = 1) -> Canvas:
    """Gorse on the open grazing: a dense spiny dome, its dark green made of short needle
    strokes rather than leaves, lit on the upper west, thick with yellow flowers in small
    clusters on the sunny side, dead grey spines low in its heart. Sizes 0, 1, 2: 16, 24
    and 40 wide."""
    w, h = {0: (16, 14), 1: (24, 20), 2: (40, 28)}[size]
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    lobes = _lobes(w, h + 1, {0: 3, 1: 3, 2: 5}[size], 321 + size, 3.5 if size == 0 else 4.5, 5.0 if size == 0 else 6.0 + size * 1.5)
    shape = gp.canopy(cv, lobes, H['leaf_cool'], seed=322 + size, clumps=False)
    lift_rim(cv, ('leaf_cool', 'grass_cool', 'leaf'))
    clumps(cv, shape, ('leaf_cool', 'grass_cool', 'leaf'), seed=323 + size, pattern=('.##.', '####', '.##.') if size != 1 else ('##.', '###', '.##'), step=(4, 3) if size != 1 else (3, 3))
    xs = [p[0] for p in shape]
    cx = (min(xs) + max(xs)) / 2
    for k in range(6 + size * 14):  # flowers in small clusters, more on the sunny side
        x = min(xs) + int(noise2(k, 0, 324 + size) ** 1.4 * (max(xs) - min(xs)))
        y = 1 + int(noise2(k, 1, 324 + size) * (h - 6))
        if (x, y) in shape and (x + 1, y) in shape and (x, y + 1) in shape:
            cv.hline(x, y, 2, T('brass', 5 if x < cx else 4)); cv.hline(x, y + 1, 2, T('brass', 3))
    lift_rim(cv, ('leaf_cool', 'grass_cool', 'leaf'))
    for x in range(int(cx) - 2, int(cx) + 2) if size else ():  # dead grey spines low in its heart
        cv.set(x, foot - 2, T('bleached', 2)); cv.set(x + 1, foot - 3, T('bleached', 3))
    tuft(cv, 1, foot, 3); tuft(cv, w - 2, foot, 1)
    return cv


# ---- fallen tree ------------------------------------------------------------------------

def fallen_tree(size: int = 1) -> Canvas:
    """A fallen tree across the way, lying west to east: its trunk a cylinder of oak bark
    in plates, lit along its upper west, shaded underneath, moss along its top and a
    bracket fungus; size 0 a broken limb with the splintered break pale, size 1 a sawn log
    whose west end shows its rings, size 2 the whole trunk thrown by a gale with its root
    plate stood up on end, earth and stones caught in the roots, the hole it left."""
    w, h = {0: (32, 10), 1: (56, 16), 2: (88, 32)}[size]
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 2, w, foot)
    r = {0: 3, 1: 5, 2: 7}[size]
    x0 = {0: 2, 1: 1, 2: 22}[size]
    x1 = w - 2
    cy = foot - r - 1
    for x in range(x0, x1):  # the trunk, tapering a little to the east
        rr = r - (1 if size and x > x1 - (x1 - x0) // 3 else 0)
        for y in range(cy - rr, cy + rr + 1):
            v = (y - cy) / rr
            i = 4 if v < -0.55 else 3 if v < 0.1 else 2 if v < 0.6 else 1
            if noise2((x - x0) // 3, y, 331 + size) > 0.74 and i > 1:
                i -= 1  # a fissure between bark plates
            fam = 'earth_warm' if noise2((x - x0) // 6, (y - cy) // 3, 335 + size) < 0.6 else 'timber_cool'  # bark weathered in patches
            cv.set(x, y, T(fam, i))
        if noise2(x // 2, 0, 332 + size) > 0.5:
            cv.set(x, cy - rr, T('leaf', 3))  # moss along the top
    if size == 0:  # the broken end, splintered and pale, where it tore from the tree
        for y in range(cy - r, cy + r + 1):
            cv.hline(x0 - 1 - (y % 2), y, 2 + (y % 2), T('bleached', 5 if y < cy else 4))
    if size >= 1:  # the sawn or torn west end: its rings
        for (x, y) in oval(x0 + 1, cy, 1.6, r + 0.4):
            d = abs(y - cy)
            cv.set(x, y, T('sand_warm', 4 if d % 2 == 0 else 3) if d < r else T('earth_warm', 3))
        cv.set(x0 + 1, cy, T('earth_warm', 2))
    for k in range(1 + size):  # stubs of branches snapped off along its top, their ends lit
        bx = x0 + (x1 - x0) * (k + 1) // (2 + size)
        for t in range(3 + size):
            cv.hline(bx + t // 2, cy - r - 1 - t, 2, T('earth_warm', 4 if t < 2 + size else 5))
    for k in range(2 + size * 2):  # moss cushions on its top and down its north flank
        mx = x0 + 2 + int(noise2(k, 5, 336 + size) * (x1 - x0 - 6))
        cv.hline(mx, cy - r, 3, T('leaf', 4)); cv.hline(mx, cy - r + 1, 3, T('leaf', 2))
    for k in range(3 + size * 5):  # grey-green lichen in patches on the bark's flank
        lx = x0 + 3 + int(noise2(k, 8, 338 + size) * (x1 - x0 - 8))
        ly = cy - 1 + int(noise2(8, k, 338 + size) * r)
        cv.hline(lx, ly, 2, T('stone_cool', 4)); cv.set(lx + 1, ly + 1, T('stone_cool', 3))
    for k in range(size):  # a woodpecker's hole, dark, its lower lip lit
        hx = x0 + (x1 - x0) * (k + 1) // 3 + 3
        cv.hline(hx, cy - 2, 2, T('earth', 0)); cv.hline(hx, cy - 1, 2, T('earth_warm', 4))
    for k in range(1 + size):  # a little cluster of toadstools in its shade at the foot
        fx = x0 + 4 + int(noise2(k, 6, 337 + size) * (x1 - x0 - 10))
        cv.hline(fx, foot - 1, 2, T('clay', 4)); cv.set(fx + 2, foot - 1, T('sand_warm', 4)); cv.set(fx, foot, T('plaster', 3))
    for (ex, side) in ((x1 + 1, 1),):  # a fern grown up against its east end
        for k in range(4):
            cv.set(ex + k // 2, foot - 1 - k, T('leaf_warm', 4 - k // 2)); cv.set(ex + 1 + k // 2, foot - 1 - k, T('leaf_warm', 2))
    if size >= 1:  # a bracket fungus on its flank
        fx = x0 + (x1 - x0) * 2 // 3
        cv.hline(fx, cy + 1, 3, T('sand_warm', 4)); cv.hline(fx, cy + 2, 3, T('sand_warm', 2))
    if size == 2:  # the root plate stood on end, its earth face to the south, roots torn through it
        pcx, pcy, prx, pry = 13, 15, 10, 13
        plate = set()
        for (x, y) in oval(pcx, pcy, prx + 1, pry + 1):
            a = math.atan2(y + 0.5 - pcy, x + 0.5 - pcx)
            edge = 1 + 0.1 * math.sin(a * 5 + 1) + 0.07 * math.sin(a * 11)
            if ((x + 0.5 - pcx) / prx) ** 2 + ((y + 0.5 - pcy) / pry) ** 2 <= edge * edge and y < foot - 1:
                plate.add((x, y))
        for (x, y) in plate:  # earth in clods, lit on the upper west
            u, v = (x + 0.5 - pcx) / prx, (y + 0.5 - pcy) / pry
            i = 4 if u + v < -0.5 else 3 if u + v < 0.5 else 2
            if (x // 3 + y // 2) % 3 == 0 and y % 2 == 0 and i < 5:
                i += 1  # a clod's lit top
            cv.set(x, y, T('earth' if noise2(x // 3, y // 3, 334) < 0.6 else 'earth_warm', i))
        for k in range(9):  # roots torn out, radiating from where the trunk joined
            a = -math.pi * 0.9 + k * math.pi * 1.6 / 8
            for t in range(4, 15):
                x = int(pcx + 4 + math.cos(a) * t * 0.9)
                y = int(pcy + math.sin(a) * t * 1.05)
                if (x, y) in plate:
                    cv.set(x, y, T('earth_warm', 4 if math.sin(a) < 0 else 3))
        for (sx, sy) in ((7, 9), (15, 6), (9, 19), (17, 21), (5, 15)):  # stones caught in the roots
            cv.hline(sx, sy, 2, stone_px(sx, sy, 4, 333)); cv.hline(sx, sy + 1, 2, stone_px(sx, sy, 2, 333))
        for k in range(6):  # ivy that was climbing the trunk, still clinging to the plate's east side
            ix, iy = pcx + 6 - k // 3, pcy - 6 + k * 3
            if (ix, iy) in plate:
                cv.hline(ix, iy, 2, T('leaf_cool', 4)); cv.set(ix, iy + 1, T('leaf_cool', 2))
        for (x, y) in plate:  # the turf still on its top edge
            if (x, y - 1) not in plate and y < pcy - 4:
                cv.set(x, y, T('grass', 4)); cv.set(x, y - 1, T('grass', 3)) if x % 3 == 0 else None
        for x in range(3, 26):  # the hole it left, dark
            cv.set(x, foot, T('earth', 0)); cv.set(x, foot - 1, T('earth', 1))
    tuft(cv, x0, foot, 3); tuft(cv, w - 3, foot, 1)
    return cv


# ---- boulders ---------------------------------------------------------------------------

def boulders(size: int = 1) -> Canvas:
    """Boulders left by the old ice: rounded granite, lit on the upper west with a hard
    terminator, a darker skirt where they sit in the turf, lichen in yellow and grey
    patches and moss on their north faces; size 0 one stone, 1 a pair, 2 a group of three
    with a small one in front."""
    w, h = {0: (16, 12), 1: (32, 20), 2: (48, 30)}[size]
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    shade_under(cv, 1, w, foot)
    stones = {0: [(8, 6.5, 6.5, 5)], 1: [(11, 10, 9.5, 8), (24, 13, 7, 5.5)],
              2: [(16, 15, 13, 12), (35, 17, 11, 10), (26, 24, 6, 4.5)]}[size]
    for si, (sx, sy, rx, ry) in enumerate(stones):
        fam = ('stone', 'stone_warm', 'stone_cool')[si % 3]
        for (x, y) in oval(sx, sy, rx, ry):
            u, v = (x + 0.5 - sx) / rx, (y + 0.5 - sy) / ry
            d = u * 0.7 + v
            i = 5 if d < -0.75 else 4 if d < -0.15 else 3 if d < 0.35 else 2 if d < 0.8 else 1
            if v > 0.7:
                i = min(i, 1)  # the skirt in the turf
            if size and noise2(x // 3, y // 2, 341 + si) > 0.8 and 1 < i < 5:
                i -= 1  # a hollow in the granite
            cv.set(x, y, T(fam, i))
        for k in range(2 + size):  # lichen patches
            lx = int(sx - rx * 0.5 + noise2(k, si, 342) * rx)
            ly = int(sy - ry * 0.6 + noise2(si, k, 343) * ry * 0.8)
            c = T('sand_warm', 4) if k % 2 else T('snow', 2)
            cv.hline(lx, ly, 2, c); cv.set(lx, ly + 1, c)
        if rx > 6:  # a frost crack across its face, dark with a lit lip above
            for t in range(int(rx)):
                x = int(sx - rx * 0.4 + t)
                y = int(sy - ry * 0.1 + t * 0.4 + math.sin(t) * 0.8)
                cv.set(x, y, T(fam, 1)); cv.set(x, y - 1, T(fam, 4))
        for x in range(int(sx + rx * 0.2), int(sx + rx * 0.8)):  # moss on the north-east shoulder
            y = int(sy - math.sqrt(max(0.0, 1 - ((x + 0.5 - sx) / rx) ** 2)) * ry) + 1
            cv.set(x, y, T('leaf', 2)); cv.set(x, y + 1, T('leaf', 1))
    for k in range(size * 2):  # grass grown up round their feet
        tuft(cv, 4 + k * (w - 8) // max(1, size * 2 - 1), foot, k % 6)
    tuft(cv, 1, foot, 3); tuft(cv, w - 2, foot, 5)
    return cv


def props() -> dict[str, Canvas]:
    return {k: clean(cv) for k, cv in _props().items()}


def _props() -> dict[str, Canvas]:
    out = {}
    for s, tag in ((0, 'small'), (1, 'mid'), (2, 'big')):
        out[f'thicket_{tag}'] = thicket(s)
        out[f'bramble_{tag}'] = bramble(s)
        out[f'gorse_{tag}'] = gorse(s)
        out[f'fallen_tree_{tag}'] = fallen_tree(s)
        out[f'boulders_{tag}'] = boulders(s)
    return out
