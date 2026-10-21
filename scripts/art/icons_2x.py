"""The interface's 2x icons (Claude M, 21 Oct): the HUD and hotbar icons redrawn on a 32x32
grid for art density 2 (lib/art-density.ts, lib/pixel-scale.ts `interfaceGrid`).

They are shown at the same size as the 16x16 set (16 interface px), so each texel is half an
interface pixel: 2 device px on a 3x phone, the same texel as the world's art at density 2.
Screens where an interface pixel does not split evenly (a 2x iPhone SE, an S25 Ultra at QHD+)
keep the 16x16 set, so every 2x icon is the same design as its 1x one, drawn finer: the
same silhouette, palette ramps and light from the upper left, a 1 texel outline tinted by
the part's material (half the 1x weight, like the world's 2x art), one-texel lit and shaded
bands, and a little detail the 1x grid had no room for (shingle rows, a door knob, a map's
route and mark, the moon's craters, a sword's fuller, the coin's glint, the hourglass sand).
Detail sits in clusters of two or more texels, except highlights and the shading bands.

Drawn by scripts/art/icons.py, which writes them into lib/icon-art.ts as `iconRows2x`.
"""
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, RED, STONE, WOOD, WTR
from pixel import Canvas

GRID = 32
PATH = MATERIALS['path']


# --- shapes on the 32 grid ----------------------------------------------------------------
def R(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def disc(cx, cy, r):
    return {(x, y) for y in range(GRID) for x in range(GRID)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def oval(cx, cy, rx, ry):
    return {(x, y) for y in range(GRID) for x in range(GRID)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1}


def poly(points):
    """Texels whose centres fall inside the polygon (even-odd rule)."""
    out = set()
    for y in range(GRID):
        for x in range(GRID):
            px, py = x + 0.5, y + 0.5
            inside = False
            for i in range(len(points)):
                (x0, y0), (x1, y1) = points[i], points[i - 1]
                if (y0 > py) != (y1 > py) and px < (x1 - x0) * (py - y0) / (y1 - y0) + x0:
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def mirror(pts):
    return {(GRID - 1 - x, y) for (x, y) in pts}


def clip(pts, y_max=GRID - 3):
    """Keep a texel of room for the outline on every side."""
    return {(x, y) for (x, y) in pts if 1 <= x <= GRID - 2 and 1 <= y <= y_max}


def diagonal(x0, y0, length, width=3):
    """A stroke down and to the right, `width` texels across."""
    return {(x0 + i + k, y0 + i) for i in range(length) for k in range(width)}


# --- the icons ----------------------------------------------------------------------------
def home(cv, part, dots):
    part(cv, R(21, 4, 4, 8), STONE, 2)
    part(cv, R(21, 3, 4, 1), STONE, 3, highlight=False)  # the chimney's cap
    part(cv, R(5, 15, 22, 13), CREAM, 2)
    part(cv, poly([(1.5, 16), (16, 2.2), (30.5, 16)]), RED, 2)
    # shingle rows: short dark dashes, staggered, inside the roof
    for y, xs in ((7, (13, 18)), (10, (9, 14, 19)), (13, (6, 11, 16, 21))):
        dots(cv, {(x + i, y) for x in xs for i in range(2)}, RED[1])
    dots(cv, {(x, 16) for x in range(6, 26)}, CREAM[1])  # shade under the eaves
    part(cv, R(16, 20, 6, 8), WOOD, 2, highlight=False)  # door
    dots(cv, {(20, 24), (20, 25)}, GOLD[3])  # knob
    part(cv, R(8, 19, 5, 5), WTR, 3)  # window
    dots(cv, {(10, y) for y in range(19, 24)} | {(x, 21) for x in range(8, 13)}, CREAM[2])


def missions(cv, part, dots):
    part(cv, R(2, 6, 10, 20), CREAM, 3)
    part(cv, R(12, 4, 10, 20), CREAM, 2)
    part(cv, R(22, 6, 8, 20), CREAM, 3)
    dots(cv, {(4, 8), (5, 8), (6, 8), (4, 9), (5, 9), (4, 10)}, LEAF[3])  # a wood
    dots(cv, {(14, 7), (15, 7), (16, 7), (16, 8), (17, 8), (17, 9)}, WTR[3])  # a lake
    # the dashed route to the mark
    dots(cv, {(4, 22), (5, 22), (8, 20), (9, 20), (12, 18), (13, 18), (16, 17), (17, 17),
              (20, 16), (21, 15)}, RED[2])
    dots(cv, {(24, 9), (25, 10), (26, 11), (27, 12), (27, 9), (26, 10), (25, 11), (24, 12)},
         RED[1])  # the mark


def nap(cv, part, dots):
    moon = disc(15, 17, 12.4) - disc(21.2, 12.8, 10.4)
    part(cv, clip(moon), GOLD, 3)
    dots(cv, {(6, 18), (7, 18), (6, 19), (10, 25), (11, 25), (11, 26)}, GOLD[2])  # craters
    part(cv, {(25, 20), (24, 21), (25, 21), (26, 21), (25, 22), (25, 19), (25, 23), (23, 21),
              (27, 21)}, CREAM, 3, highlight=False)
    dots(cv, {(26, 6), (27, 6)}, CREAM[3])


def sword(tip_left=True):
    blade = diagonal(3, 3, 16) | {(2, 2), (3, 2), (2, 3)}
    # a short crossguard square to the blade where it ends, then the grip and the pommel
    guard = {(21 + t + j, 19 - t) for t in range(-3, 4) for j in range(2)}
    grip = diagonal(22, 21, 4, 2)
    pommel = R(25, 25, 3, 3) - {(27, 25), (25, 27)}
    parts = [blade, guard, grip, pommel]
    return parts if tip_left else [mirror(p) for p in parts]


def arena(cv, part, dots):
    for side in (True, False):
        blade, guard, grip, pommel = sword(side)
        part(cv, blade | guard | grip | pommel, STONE, 3)
        fuller = {(4 + i + 1, 4 + i) for i in range(13)}
        dots(cv, fuller if side else mirror(fuller), STONE[4])
        top = min(guard)
        for (x, y) in guard:
            cv.set(x, y, GOLD[4] if (x, y) == top else GOLD[3] if (x + y) % 2 else GOLD[2])
        dots(cv, grip, WOOD[3])
        dots(cv, pommel, GOLD[2])


def shop(cv, part, dots):
    part(cv, clip(oval(15, 21.5, 11.6, 8.6)), WOOD, 3)
    part(cv, poly([(9.5, 3.5), (13, 6), (16, 3.5), (19, 6), (22.5, 3.5), (20.5, 12), (11.5, 12)]),
         WOOD, 3)
    part(cv, R(10, 12, 12, 2), RED, 3, highlight=False)  # the tie
    dots(cv, {(13, 18), (14, 18), (13, 19)}, WOOD[4])  # a lit fold
    part(cv, disc(23.4, 23.4, 5.4), GOLD, 3)
    ring = disc(23.4, 23.4, 3.6) - disc(23.4, 23.4, 2.4)
    dots(cv, ring, GOLD[2])
    dots(cv, {(21, 21), (22, 21), (21, 22)}, CREAM[3])


def shield(cv, part, dots):
    part(cv, poly([(3.5, 3.5), (28.5, 3.5), (28.5, 17), (16, 29.6), (3.5, 17)]), GOLD, 3)
    part(cv, poly([(7, 7), (25, 7), (25, 16.4), (16, 25), (7, 16.4)]), LEAF, 3)
    glint = {(19 - i + k, 10 + i) for i in range(8) for k in range(2)}
    part(cv, glint, CREAM, 2, ring=False)
    dots(cv, {(5, 5), (26, 5)}, GOLD[1])  # rivets
    dots(cv, {(6, 5), (27, 5)}, GOLD[4])


def heart(cv, part, dots):
    shape = disc(10.4, 12.4, 6.6) | disc(21.6, 12.4, 6.6) | poly([(3.8, 14), (28.2, 14), (16, 27.6)])
    part(cv, clip(shape), RED, 3)
    dots(cv, {(8, 9), (9, 9), (8, 10)}, CREAM[3])
    dots(cv, {(10, 9), (8, 11), (7, 11)}, RED[4])


def dream_dust(cv, part, dots):
    bulb = clip(disc(13, 20.8, 8.8))
    part(cv, bulb, NAP, 3)
    part(cv, R(10, 8, 6, 6), NAP, 3, highlight=False)  # neck
    part(cv, R(8, 6, 10, 2), NAP, 4, highlight=False)  # lip
    part(cv, R(10, 2, 6, 4), WOOD, 3, highlight=False)  # cork
    dust = {(x, y) for (x, y) in bulb if y >= 21 + (x - 12) ** 2 / 10}
    for (x, y) in sorted(dust):
        top = (x, y - 1) not in dust
        left = (x - 1, y) not in dust
        low = (x, y + 1) not in dust or (x + 1, y) not in dust
        cv.set(x, y, GOLD[4 if top else 2 if low and not left else 3])
    dots(cv, {(10, 23), (11, 23), (16, 25), (17, 25), (12, 27), (13, 27)}, CREAM[3])
    dots(cv, {(8, 16), (8, 17)}, CREAM[3])  # glint on the glass
    dots(cv, {(14, 16), (15, 16), (10, 14), (11, 14)}, GOLD[4])  # dust afloat
    part(cv, {(25, 8), (24, 9), (25, 9), (26, 9), (25, 10), (25, 7), (25, 11), (23, 9), (27, 9)},
         GOLD, 4, highlight=False)
    dots(cv, {(25, 9)}, CREAM[3])
    dots(cv, {(21, 3), (22, 3), (28, 18), (28, 19)}, GOLD[3])


def time(cv, part, dots):
    part(cv, R(4, 6, 2, 20), WOOD, 2, highlight=False)
    part(cv, R(26, 6, 2, 20), WOOD, 2, highlight=False)
    glass = poly([(7, 6), (25, 6), (25, 8.5), (17.6, 16), (25, 23.5), (25, 26), (7, 26),
                  (7, 23.5), (14.4, 16), (7, 8.5)])
    part(cv, glass, WTR, 4)
    sand_top = {(x, y) for (x, y) in glass if 10 <= y <= 13}
    dots(cv, sand_top, GOLD[3])
    dots(cv, {(x, 10) for (x, y) in sand_top if y == 10}, GOLD[4])
    dots(cv, {(15, y) for y in range(14, 22)} | {(16, y) for y in range(14, 22)}, GOLD[3])
    heap = {(x, y) for (x, y) in glass if y >= 22 and abs(x - 15.5) <= (y - 20) * 2.2}
    dots(cv, heap, GOLD[2])
    dots(cv, {(x, y) for (x, y) in heap if (x, y - 1) not in heap}, GOLD[3])
    part(cv, R(3, 2, 26, 4), WOOD, 3)
    part(cv, R(3, 26, 26, 4), WOOD, 3)


def menu(cv, part, dots):
    for y in (4, 14, 24):
        part(cv, R(4, y, 24, 4), WOOD, 3, highlight=False)
        dots(cv, {(5, y), (6, y)}, WOOD[4])


def companion(cv, part, dots):
    part(cv, clip(oval(16, 22.6, 7.6, 5.6)), PATH, 3)
    for (x, y) in ((5.6, 14.6), (12.2, 8.4), (19.8, 8.4), (26.4, 14.6)):
        part(cv, oval(x, y, 2.5, 3.3), PATH, 3, highlight=False)


ICONS_2X = {
    'home': home, 'missions': missions, 'nap': nap, 'moon': nap, 'arena': arena,
    'shop': shop, 'shield': shield, 'heart': heart, 'dreamDust': dream_dust,
    'time': time, 'menu': menu, 'companion': companion,
}


def draw(fn, part, dots):
    cv = Canvas(GRID, GRID, density=2)
    fn(cv, part, dots)
    return cv
