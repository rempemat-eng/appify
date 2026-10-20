"""The house style sheet (docs/vision/house-style.md): one NapAttack look in every setting.

Draws, at native pixels and saved at 3x:

1. the house palette (art/house-palette.json): core ramps, setting accents, glows;
2. one material swatch per item of the vocabulary (wood, stone, brick, metal, glass,
   cloth, foliage, water, snow, regolith), each drawn with the kit below;
3. one exemplar per setting, today's version (cut from the current sprites and zones)
   beside the same subject redrawn to the house style, at the same scale (an adult is
   25 px; a door 14 x 28 to 32, a window 12 to 16 wide).

The kit is small on purpose: every surface is built from `part()` (a chunky piece lit on
its top and left, dark on its bottom and right, its corners knocked off), laid in courses,
boards or panels; every tone comes from a house ramp and moves along it with `step()`; the
outline is the material's own edge tone (`outline()`); shadows step the ground down its own
ramp (`cast()`). Lanes can copy these recipes; nothing in the game reads this file.

Run:
    python3 scripts/art/style_sheet.py [OUT_DIR]
writes OUT_DIR/sheet.png and OUT_DIR/pairs/<setting>.png (default: napattack-house-style in the
system's temp folder, never the repository), prints the style lint for each exemplar and,
when detail_bar.py is importable (the terrace toolkit), the detail bar counts.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import house_palette as hp  # noqa: E402
from pixel import Canvas, disc, noise2, smooth_noise  # noqa: E402

PAL = hp.load()
R = PAL['ramps']
EDGES = PAL['edges']
INK = PAL['ink']
LOOK = hp.colours(PAL)
SCALE = 3


# --- the kit -------------------------------------------------------------------------------
def T(name: str, i: int) -> str:
    """Tone i of a house ramp, held to 0..5."""
    return R[name][max(0, min(5, i))]


def sib(name: str, n: float, share: float = 0.28) -> str:
    """One of a material's three ramps by a number in 0..1: the body ramp most often, its
    warm sibling below `share` and its cool sibling above 1 - share."""
    if name not in R or f'{name}_warm' not in R:
        return name
    return f'{name}_warm' if n < share else f'{name}_cool' if n > 1 - share else name


def tone_at(cv: Canvas, x: int, y: int):
    c = cv.get(x, y)
    return LOOK.get(c[:3]) if c[3] else None


def step(cv: Canvas, x: int, y: int, k: int, floor: int = 0):
    """Move a pixel k tones along its own ramp (negative is darker). Colours stay on the
    palette, so shade keeps the material's hue and leans to dusk on its own."""
    hit = tone_at(cv, x, y)
    if hit and hit[1] >= 0 and hit[0] != 'ink':
        cv.set(x, y, T(hit[0], max(floor, hit[1] + k)))


def rect(x0, y0, w, h):
    return {(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)}


def part(cv: Canvas, x0: int, y0: int, w: int, h: int, ramp: str, base: int = 3, seam: str | None = None,
         clip=None, glint: bool = True, corners: bool = True):
    """The house's one building block: a chunky piece (a brick, a stone, a board, a plate,
    a slate). Lit top row (+1), the body, a dark bottom row (-1); a part four or more rows
    tall also has a lit left and a dark right column and, eight or more wide, a two-pixel
    glint (+2) at its top left. Corners are knocked off to the seam, so every part reads
    soft and rounded. Pixels outside `clip` (a set) are left alone."""
    big = h >= 4 and w >= 4
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if clip is not None and (x, y) not in clip:
                continue
            top, bot = y == y0, y == y0 + h - 1
            left, right = x == x0, x == x0 + w - 1
            if corners and (top or bot) and (left or right) and w > 2 and h > 1:
                if seam:
                    cv.set(x, y, seam)
                continue
            k = base
            if bot or (right and big):
                k = base - 1
            elif (top and (big or x < x0 + w * 0.6)) or (left and big):
                k = base + 1   # a small part's top catches the light only towards its left
            if glint and top and big and w >= 8 and x in (x0 + 1, x0 + 2):
                k = base + 2
            cv.set(x, y, T(ramp, k))


def courses(cv: Canvas, x0, y0, w, h, choose, course: int = 5, lengths=(6, 12), seam: str = None,
            seed: int = 0, clip=None):
    """Parts laid in courses with staggered joints. `choose(ci, si)` gives (ramp, base) for
    each part, so one wall can mix two or three sibling ramps (the detail comes from many
    parts, each one a little different, not from noise)."""
    area = rect(x0, y0, w, h) if clip is None else clip & rect(x0, y0, w, h)
    for (x, y) in area:
        cv.set(x, y, seam)
    y, ci = y0, 0
    while y < y0 + h:
        ch = min(course, y0 + h - y)
        x = x0 - int(noise2(ci, seed, 1) * lengths[1] * 0.7)
        si = 0
        while x < x0 + w:
            ln = lengths[0] + int(noise2(ci, si, seed + 2) * (lengths[1] - lengths[0] + 1))
            ramp, base = choose(ci, si)
            part(cv, x, y, ln - 1, ch - 1, ramp, base, seam, clip=area)
            x += ln
            si += 1
        y += ch
        ci += 1


def boards(cv: Canvas, x0, y0, w, h, choose, board: int = 4, seed: int = 0, clip=None,
           joints=(14, 30), grain: float = 0.10, nails: bool = True):
    """Lapped boards: a shadow line under the board above, a lit lip, the body, grain in
    two- and three-pixel streaks, the odd knot, butt joints with nail heads beside them.
    `choose(bi, si)` gives (ramp, base) for each length of board."""
    area = rect(x0, y0, w, h) if clip is None else clip & rect(x0, y0, w, h)
    for (x, y) in sorted(area):
        bi, r = divmod(y - y0, board)
        span = joints[0] + int(noise2(bi, seed, 6) * (joints[1] - joints[0]))
        off = int(noise2(bi, seed, 7) * span)
        si, j = divmod(x - x0 + off, span)
        ramp, base = choose(bi, si)
        if r == 0:
            k = base - 2                                   # the shadow under the board above
        elif r == 1:
            k = base + 1                                   # the lit lip
        elif r == board - 1:
            k = base - 1
        else:
            k = base
        if r > 0 and j == 0:
            k = base - 2                                   # a butt joint
        elif r > 1 and j == 1:
            k = base + 1
        elif r >= 2 and noise2((x - x0 + off) // 3, y, seed + 9) < grain:
            k = base - 1                                   # grain, three pixels long
        cv.set(x, y, T(ramp, k))
        if nails and r == 2 and j in (2,) and noise2(bi, si, seed + 4) < 0.7:
            cv.set(x, y, T('iron', 1))
            cv.set(x, y - 1, T('iron', 4))                  # a nail head lit on top
    # knots: a dark eye with a lit rim above it, two pixels each
    for bi in range(h // board):
        if noise2(bi, seed, 11) < 0.35:
            kx = x0 + 3 + int(noise2(bi, seed, 12) * max(1, w - 8))
            ky = y0 + bi * board + 2
            if (kx, ky) in area and (kx + 1, ky) in area:
                hit = tone_at(cv, kx, ky)
                if hit:
                    cv.set(kx, ky, T(hit[0], 1)); cv.set(kx + 1, ky, T(hit[0], 1))
                    cv.set(kx, ky - 1, T(hit[0], 4)) if (kx, ky - 1) in area else None


def roof_rows(cv: Canvas, x0, y0, w, h, ramp: str, base: int = 3, row: int = 5, tile=(6, 8), seed: int = 0,
              moss: bool = False, clip=None, lip_round: bool = True):
    """Tiles or slates seen from above: rows that overlap. Each tile: the shadow of the row
    above along its top, a lit left edge and a dark right one, a lit lower lip with its two
    ends rounded off, a dark joint to its neighbour. Each tile is one of the material's three
    ramps, the odd one a tone off; moss sits in the odd lower corner."""
    area = rect(x0, y0, w, h) if clip is None else clip & rect(x0, y0, w, h)
    for (x, y) in area:
        ri, r = divmod(y - y0, row)
        span = tile[0] + int(noise2(ri, seed, 3) * (tile[1] - tile[0] + 1))
        si, j = divmod(x - x0 + (span // 2 if ri % 2 else 0), span)
        n = noise2(ri, si, seed)
        b = base + (1 if n > 0.9 else -1 if n < 0.1 else 0)
        rp = sib(ramp, noise2(ri, si, seed + 8))
        if r == 0:
            k = b - 2
        elif j == 0:
            k = b - 2
        elif r == row - 1:
            k = b - 1 if lip_round and j in (1, span - 1) else b + 1
        elif j == 1:
            k = b + 1 if r < row - 2 else b
        elif j == span - 1:
            k = b - 1
        else:
            k = b
        cv.set(x, y, T(rp, k))
        if moss and r == row - 2 and j in (2, 3) and noise2(ri, si, seed + 5) < 0.12:
            cv.set(x, y, T('leaf', 3 if j == 2 else 2))


SHAPES = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)),
          ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1)))


def grain(cv: Canvas, pts, density: float = 0.08, seed: int = 0, shapes=SHAPES, lit=None, swap: float = 0.5,
          up: float = 0.3, down: float = 0.3):
    """Texture as small clusters (two to four pixels, never one): each cluster takes the
    tone under its first pixel and moves it one step up or down (more often up where `lit`
    says the surface faces the light) or over to a sibling ramp. This is how a surface gets
    Eastward's many small shapes and tones without speckle."""
    pts = set(pts)
    for (x, y) in sorted(pts):
        n = noise2(x, y, seed)
        if n >= density:
            continue
        hit = tone_at(cv, x, y)
        if not hit or hit[1] < 0 or hit[0] == 'ink':
            continue
        name, k = hit
        shp = shapes[int(noise2(x, y, seed + 1) * len(shapes))]
        l = lit(x, y) if lit else 0.5
        m = noise2(x, y, seed + 2)
        if m < up * (0.5 + l):
            dk = 1
        elif m > 1 - down * (1.5 - l):
            dk = -1
        else:
            dk = 0
        fam = hp.family(name)
        ramp = sib(fam, noise2(x, y, seed + 3)) if noise2(x, y, seed + 4) < swap else name
        if dk == 0 and ramp == name:
            ramp = sib(fam, 0.1 if name != f'{fam}_warm' else 0.9)
        col = T(ramp, k + dk)
        for dx, dy in shp:
            p = (x + dx, y + dy)
            if p in pts:
                h2 = tone_at(cv, *p)
                if h2 and hp.family(h2[0]) == fam and abs(h2[1] - k) <= 1:
                    cv.set(p[0], p[1], col)


def soft_patches(cv: Canvas, pts, seed: int, scale: float = 5, light: float = 0.62, dark: float = 0.30):
    """Large calm patches on a flat surface (plaster, ground): a tone up where the noise is
    high and the light is (upper left), a tone down where it is low. Clusters, never specks."""
    pts = set(pts)
    for (x, y) in pts:
        n = smooth_noise(x, y, scale, seed)
        if n > light:
            step(cv, x, y, 1)
        elif n < dark:
            step(cv, x, y, -1)
    # remove any lone pixel the patches left (a cluster is at least two pixels)
    for (x, y) in pts:
        c = cv.get(x, y)
        nb = [cv.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in pts]
        if len(nb) == 4 and all(n != c for n in nb):
            cv.set(x, y, max(set(nb), key=nb.count))


def outline(cv: Canvas, solid=None, lit_break: bool = True):
    """The house outline: one pixel outside the silhouette, in the edge tone of the material
    it closes. Where it closes a lit top or left edge (tone 4 or 5), it breaks to that
    ramp's tone 1, so the light seems to wrap round the form. Glows get no outline."""
    if solid is None:
        solid = {(x, y) for y in range(cv.h) for x in range(cv.w) if cv.get(x, y)[3] == 255}
    ring = {}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in solid or not (0 <= n[0] < cv.w and 0 <= n[1] < cv.h):
                continue
            hit = tone_at(cv, x, y)
            if hit is None or hit[0] == 'ink':
                col = INK
            elif hp.family(hit[0]) not in EDGES:
                continue                                   # a glow: light needs no line
            elif lit_break and (dx, dy) in ((-1, 0), (0, -1)) and hit[1] >= 4:
                col = T(hit[0], 1)
            else:
                col = EDGES[hp.family(hit[0])]
            if n not in ring or col == INK:
                ring[n] = col
    for (x, y), col in ring.items():
        cv.set(x, y, col)
    return set(ring)


def cast(cv: Canvas, pts, k: int = 2, floor: int = 0):
    """A cast shadow: the ground under it steps k tones down its own ramp (2 by default,
    3 on the airless moon). Hard-edged, on the palette, violet by the ramps' own lean."""
    for (x, y) in pts:
        step(cv, x, y, -k, floor)


def ground(cv: Canvas, x0, y0, w, h, ramp: str, base: int = 3, seed: int = 0, scale: float = 6,
           density: float = 0.16, contrast: float = 0.12, share: float = 0.16):
    """Walkable ground: calm, light, one ramp and its siblings in broad soft patches, with
    small clusters over them (clods, blades, grit). Most clusters only swap to a sibling
    ramp at the same tone, so the ground gets many small shapes without value noise; only
    `contrast` of them step a tone up or down."""
    pts = rect(x0, y0, w, h)
    for (x, y) in pts:
        n = smooth_noise(x, y, scale * 1.7, seed + 7)
        cv.set(x, y, T(sib(ramp, n, share), base))
    soft_patches(cv, pts, seed, scale, light=0.7, dark=0.25)
    grain(cv, pts, density, seed + 3, lit=lambda x, y: 1 - (x - x0 + y - y0) / (w + h), swap=0.9,
          up=contrast, down=contrast)
    return pts


def tuft(cv: Canvas, x, y, ramp='grass', base=3):
    """Blades in a cluster: dark roots, a lit tip on each blade."""
    for dx, dy, k in ((0, 0, -1), (2, 0, -1), (1, 0, -2), (0, -1, 0), (2, -1, 0), (0, -2, 1), (2, -2, 2), (1, -1, -1)):
        cv.set(x + dx, y + dy, T(ramp, base + k))


def pebble(cv: Canvas, x, y, ramp='stone', base=3, big=False):
    """A small stone: lit top left, dark lower right, a hard shadow pixel pair beside it."""
    w = 3 if big else 2
    cv.hline(x, y, w, T(ramp, base + 1)); cv.set(x, y, T(ramp, base + 2))
    cv.hline(x, y + 1, w, T(ramp, base - 1))
    step(cv, x + w, y + 1, -2); step(cv, x + 1, y + 2, -2)
    if big:
        step(cv, x + w, y + 2, -2)


def leafy(cv: Canvas, cx, cy, rx, ry, seed=0, ramp='leaf'):
    """A crown of leaf clumps: a sphere in four bands, clumps one tone above their band
    with a light cap and a dark U under each, a sunny yellow-green rim on the lit edge."""
    shape = set()
    for y in range(int(cy - ry) - 3, int(cy + ry) + 3):
        for x in range(int(cx - rx) - 3, int(cx + rx) + 3):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            wob = 0.12 * math.sin(math.atan2(v, u) * 7 + seed)
            if u * u + v * v <= (1 + wob) ** 2:
                shape.add((x, y))

    def band(x, y):
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        lv = -0.6 * u - 0.75 * v + 0.25 * math.sqrt(max(0, 1 - min(1, u * u + v * v)))
        return 4 if lv > 0.5 else 3 if lv > 0.05 else 2 if lv > -0.45 else 1
    for (x, y) in shape:
        cv.set(x, y, T(ramp, band(x, y)))
    r = 2.6
    centres, row, y = [], 0, cy - ry + 2
    while y < cy + ry - 1:
        x = cx - rx + (3.2 if row % 2 else 0.6)
        while x < cx + rx:
            centres.append((x + (noise2(int(x * 3), int(y * 3), seed) - 0.5) * 1.4, y))
            x += 6.4
        y += 4.2
        row += 1
    for (ccx, ccy) in sorted(centres, key=lambda c: -c[1]):
        if (int(ccx), int(ccy)) not in shape:
            continue
        b = band(ccx, ccy)
        if b <= 1:
            continue
        pts = {p for p in disc(ccx, ccy, r) if p in shape}
        rp = sib(ramp, noise2(int(ccx * 7), int(ccy * 7), seed + 5), 0.3)
        for (x, y) in pts:
            cv.set(x, y, T(rp, min(5, b + 1) if b < 4 else 4))
        for (x, y) in pts:
            dy = y + 0.5 - ccy
            if (x, y + 1) not in pts and dy > 0:
                cv.set(x, y, T(rp, b - 1))
            elif ((x - 1, y) not in pts or (x, y - 1) not in pts) and x + 0.5 < ccx and dy < 0.3 and b >= 3:
                cv.set(x, y, T(rp, 5) if b == 4 else T(rp, b + 2))
    for (x, y) in shape:                                     # the sunny rim
        if ((x - 1, y) not in shape or (x, y - 1) not in shape) and band(x, y) >= 4:
            cv.set(x, y, T('grass', 5))
    return shape


def glass(cv: Canvas, x0, y0, w, h, lit: bool = False, seed: int = 0):
    """A pane in its recess. Lit from inside: lamp light, brightest low in the middle, the
    frame's shadow along its top and left. By day: the sky in it, darker at the top, one
    diagonal glint in two-pixel steps at its upper left."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            fy = (y - y0) / max(1, h - 1)
            if lit:
                k = 2 if fy < 0.2 else 3 if fy < 0.45 else 4
                if abs(x - (x0 + w / 2)) < w * 0.22 and fy > 0.55:
                    k = 5
                cv.set(x, y, T('lamp', k))
            else:
                k = 1 if fy < 0.3 else 2
                cv.set(x, y, T('slate', k))
    if lit:
        for x in range(x0, x0 + w):
            cv.set(x, y0, T('lamp', 1))
        for y in range(y0, y0 + h):
            cv.set(x0, y, T('lamp', 2))
    else:
        for i in range(0, min(w, h) - 1, 1):
            gx, gy = x0 + 1 + i, y0 + h - 2 - i * 2
            if gy >= y0 + 1 and gx < x0 + w - 1 and i < 3:
                cv.set(gx, gy, T('slate', 4)); cv.set(gx, gy - 1, T('slate', 4))
        for x in range(x0, x0 + w):
            cv.set(x, y0, T('slate', 0))
        for y in range(y0, y0 + h):
            cv.set(x0, y, T('slate', 0) if y < y0 + 2 else T('slate', 1))


def frame(cv: Canvas, x0, y0, w, h, ramp='timber', base=3, t=1):
    """A frame t px thick round a w x h opening (outer size): lit top and left members,
    dark bottom and right."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            inner = x0 + t <= x < x0 + w - t and y0 + t <= y < y0 + h - t
            if inner:
                continue
            if y < y0 + t:
                k = base + 1
            elif y >= y0 + h - t:
                k = base - 1
            elif x < x0 + t:
                k = base + 1 if t == 1 else base
            else:
                k = base - 1
            cv.set(x, y, T(ramp, k))


def overhang(cv: Canvas, x0, x1, y, depth=3):
    """The band an overhang throws on the wall below: two tones down in its first row, one
    in the rest, a row deeper towards the east."""
    for x in range(x0, x1):
        d = depth + (1 if (x - x0) > (x1 - x0) * 0.6 else 0)
        for i in range(d):
            step(cv, x, y + i, -2 if i == 0 else -1)


def cylinder(cv: Canvas, x0, y0, w, h, ramp='iron', base=3):
    """A pipe, post or column: a highlight band in the left third, dark at the right."""
    for x in range(x0, x0 + w):
        f = (x - x0 + 0.5) / w
        k = base + 2 if 0.2 < f < 0.42 else base + 1 if f <= 0.2 else base if f < 0.7 else base - 1
        for y in range(y0, y0 + h):
            cv.set(x, y, T(ramp, k))


# --- the material swatches (48 x 48) -------------------------------------------------------
SW = 48
H_GRAIN = (((0, 0), (1, 0)), ((0, 0), (1, 0), (2, 0)), ((0, 0), (1, 0), (2, 0), (3, 0)))
V_GRAIN = (((0, 0), (0, 1)), ((0, 0), (0, 1), (0, 2)))


def wall_light(x0, y0, w, h):
    """How much a wall faces the light at a point: more at its upper left."""
    return lambda x, y: max(0.0, min(1.0, 1 - 0.6 * (x - x0) / max(1, w) - 0.4 * (y - y0) / max(1, h)))


def sw_wood():
    cv = Canvas(SW, SW)
    pick = lambda bi, si: (sib('timber' if noise2(bi, si, 2) < 0.7 else 'bleached', noise2(bi, si, 3), 0.33),
                           3 + (1 if noise2(bi, si, 4) > 0.85 else -1 if noise2(bi, si, 4) < 0.1 else 0))
    boards(cv, 0, 0, SW, SW, pick, board=5, seed=11)
    grain(cv, rect(0, 0, SW, SW), 0.07, 12, shapes=H_GRAIN, lit=wall_light(0, 0, SW, SW))
    return cv


def stone_pick(fams=('stone', 'ashlar'), seed=5):
    return lambda ci, si: (sib(fams[int(noise2(ci, si, seed) * len(fams))], noise2(ci, si, seed + 1)),
                           3 + (1 if noise2(ci, si, seed + 2) > 0.85 else -1 if noise2(ci, si, seed + 2) < 0.15 else 0))


def moss_joints(cv, x0, y0, w, h, course, seed, rate=0.3):
    for ci in range(h // course):
        for si in range(max(1, w // 14)):
            if noise2(ci, si, seed) < rate * (1 + ci / max(1, h // course)):
                x = x0 + int(noise2(ci, si, seed + 1) * max(1, w - 5))
                y = y0 + ci * course + course - 1
                cv.hline(x + 1, y - 1, 2, T('leaf', 3)); cv.hline(x, y, 4, T('leaf', 2))


def sw_stone():
    cv = Canvas(SW, SW)
    courses(cv, 0, 0, SW, SW, stone_pick(), course=7, lengths=(8, 15), seam=T('stone_cool', 0), seed=21)
    grain(cv, rect(0, 0, SW, SW), 0.06, 22, lit=wall_light(0, 0, SW, SW))
    moss_joints(cv, 0, 0, SW, SW, 7, 23)
    return cv


def brick_pick(seed=7, soot_rows=0, base=3):
    def pick(ci, si):
        n = noise2(ci, si, seed)
        soot = ci < soot_rows and noise2(ci, si, seed + 1) < 0.7 - ci * 0.2
        return (sib('soot' if soot else 'clay', noise2(ci, si, seed + 2)),
                base + (1 if n > 0.88 else -1 if n < 0.14 else 0))
    return pick


def sw_brick():
    cv = Canvas(SW, SW)
    courses(cv, 0, 0, SW, SW, brick_pick(31, 3), course=4, lengths=(8, 8), seam=T('clay_cool', 1), seed=31)
    return cv


def rivets(cv, x0, x1, y, every=5, ramp='hull'):
    for x in range(x0, x1, every):
        cv.set(x, y, T(ramp, 5)); cv.set(x, y + 1, T('panel', 1))


def plates(cv, x0, y0, w, h, ramp, seed, pw=14, ph=12, other=None, lift=0):
    """Metal plates: square corners (machined, not worn), each plate one of three ramps; a
    seam is a dark line with a lit line under it (the next plate's edge catching the light);
    a slow sheen down the plate, lighter at its upper left."""
    for (x, y) in rect(x0, y0, w, h):
        ri, r = divmod(y - y0, ph)
        ci, c = divmod(x - x0 + (pw // 2 if ri % 2 else 0), pw)
        fam = other if other and noise2(ri, ci, seed + 1) < 0.25 else ramp   # the odd plate replaced in primer
        rp = sib(fam, noise2(ri, ci, seed), 0.36)
        f = (r / ph + c / pw) / 2
        k = 4 if f < 0.22 else 3 if f < 0.62 else 2
        if r == 0:
            k = 1
        elif r == 1:
            k = 4
        elif c == 0:
            k = 1
        elif c == 1:
            k = 4 if r < ph - 1 else 3
        cv.set(x, y, T(rp, k + lift))


def sw_metal():
    cv = Canvas(SW, SW)
    plates(cv, 0, 0, 30, SW, 'hull', 41, pw=15, ph=12)
    for y in range(0, SW, 12):
        rivets(cv, 4, 28, y + 3)
    grain(cv, rect(0, 0, 30, SW), 0.05, 43, shapes=H_GRAIN[:2], swap=0.6, up=0.05, down=0.4)
    part(cv, 4, 30, 10, 5, 'plaster', 4, glint=False)   # a label plate and a warning triangle
    cv.hline(5, 32, 8, T('plaster', 2))
    for i in range(5):
        cv.hline(20 - i, 34 - i, 2 * i + 1, T('brass', 4 if i < 4 else 3))
    cv.set(20, 32, T('iron', 1)); cv.set(20, 31, T('iron', 1))
    grain(cv, rect(0, 0, 30, SW), 0.03, 42, shapes=H_GRAIN, up=0.1, down=0.4)
    cylinder(cv, 32, 0, 7, SW, 'iron', 3)
    cylinder(cv, 41, 0, 6, SW, 'brass', 3)
    for y in (10, 30):
        part(cv, 31, y, 9, 4, 'iron', 2)
        part(cv, 40, y + 4, 8, 4, 'brass', 2)
    return cv


def plaster(cv, x0, y0, w, h, seed, ramp='plaster'):
    pts = rect(x0, y0, w, h)
    for (x, y) in pts:
        cv.set(x, y, T(sib(ramp, smooth_noise(x, y, 9, seed), 0.15), 3))
    soft_patches(cv, pts, seed + 1, scale=4, light=0.7, dark=0.2)
    grain(cv, pts, 0.05, seed + 2, lit=wall_light(x0, y0, w, h), up=0.25, down=0.15)
    return pts


def window(cv, wx, wy, w=18, h=16, lit=False, ramp='timber', curtain=True):
    """A window in its frame: two by two panes, a mullion and a transom, a curtain to one
    side, a stone sill with its shadow under it."""
    frame(cv, wx, wy, w, h, ramp, 3, t=2)
    mx = wx + w // 2 - 1
    ty = wy + 2 + (h - 4) // 2 - 1
    glass(cv, wx + 2, wy + 2, mx - wx - 2, ty - wy - 2, lit); glass(cv, mx + 1, wy + 2, wx + w - 3 - mx, ty - wy - 2, lit)
    glass(cv, wx + 2, ty + 1, mx - wx - 2, wy + h - 3 - ty, lit); glass(cv, mx + 1, ty + 1, wx + w - 3 - mx, wy + h - 3 - ty, lit)
    cv.vline(mx, wy + 2, h - 4, T(ramp, 2)); cv.hline(wx + 2, ty, w - 4, T(ramp, 4))
    if curtain:
        for y in range(wy + 2, ty):
            cv.set(wx + 2, y, T('plaster', 5)); cv.set(wx + 3, y, T('plaster', 4))
    part(cv, wx - 2, wy + h, w + 4, 3, 'stone', 3)
    overhang(cv, wx - 1, wx + w + 2, wy + h + 3, 2)


def sw_glass():
    cv = Canvas(SW, SW)
    plaster(cv, 0, 0, SW, SW, 51)
    window(cv, 4, 6, 18, 22, False)
    window(cv, 26, 6, 18, 22, True)
    return cv


def sw_cloth():
    cv = Canvas(SW, SW)
    for y in range(4, 26):  # an awning in two stripes, folds as lit and shaded bands
        for x in range(0, SW):
            stripe = 'berry' if (x // 6) % 2 == 0 else 'plaster'
            f = (x % 6)
            k = 4 if f == 0 else 3 if f < 3 else 2 if f < 5 else 1
            if y < 7:
                k += 1
            cv.set(x, y, T(stripe, k))
    for x in range(0, SW):  # a scalloped hem
        d = 2 if (x % 6) in (2, 3) else 1 if (x % 6) in (1, 4) else 0
        for y in range(26, 26 + d + 1):
            cv.set(x, y, T('berry' if (x // 6) % 2 == 0 else 'plaster', 2 if y < 26 + d else 1))
    banner(cv, 10, 34, 26, 14)
    return cv


def banner(cv, bx, by, w, h, ramp='dusk'):
    """A hanging banner: a pole, cloth falling in two folds, a swallowtail, the moon."""
    cv.hline(bx - 1, by - 2, w + 2, T('timber', 4)); cv.hline(bx - 1, by - 1, w + 2, T('timber', 1))
    for y in range(by, by + h):
        for x in range(bx, bx + w):
            f = (x - bx) / w
            k = 4 if f < 0.12 else 3 if f < 0.45 else 4 if f < 0.55 else 3 if f < 0.8 else 2
            cv.set(x, y, T(ramp, k))
    for x in range(bx, bx + w):   # the swallowtail
        for y in range(by + h, by + h + 4):
            if abs(x + 0.5 - (bx + w / 2)) > (y - by - h + 1) * w / 8:
                cv.set(x, y, T(ramp, 2))
    cx, cy, r = bx + w / 2, by + h * 0.4, min(w, h) * 0.28
    for (x, y) in disc(cx, cy, r):
        cv.set(x, y, T('brass', 4 if x + y < cx + cy else 3))
    for (x, y) in disc(cx + r * 0.45, cy - r * 0.3, r * 0.8):
        if (x, y) in disc(cx, cy, r + 0.5):
            hit = tone_at(cv, x, y)
            cv.set(x, y, T(ramp, 3))


def sw_foliage():
    cv = Canvas(SW, SW)
    ground(cv, 0, 0, SW, SW, 'grass', 3, seed=61)
    shp = leafy(cv, 23, 22, 18, 15, seed=2)
    outline(cv, shp)
    cast(cv, {(x + 4, y + 3) for (x, y) in shp if y > 28 and (x + 4, y + 3) not in shp and y + 3 < SW})
    for (x, y) in ((4, 44), (36, 45), (42, 41)):
        tuft(cv, x, y)
    return cv


def water(cv, x0, y0, w, h, seed, bank=True):
    """Water in a channel: dark under the near bank, depth in soft bands lying with the
    flow, the current as short lit streaks over their own shadow, glints in pairs."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            d = (y - y0) / max(1, h)
            band = d + 0.18 * math.sin(x * 0.18 + y * 0.07 + seed) + 0.1 * smooth_noise(x, y, 6, seed)
            k = 1 if y < y0 + 3 else 2 if band < 0.42 else 3
            cv.set(x, y, T(sib('water', smooth_noise(x, y, 8, seed + 1)), k))
    for i in range(int(w * h / 90)):
        x = x0 + int(noise2(i, 1, seed) * (w - 8)); y = y0 + 4 + int(noise2(i, 2, seed) * (h - 7))
        ln = 3 + int(noise2(i, 3, seed) * 3)
        hit = tone_at(cv, x, y)
        k = hit[1] if hit else 2
        cv.hline(x, y, ln, T('water', k + 2)); cv.hline(x + 1, y + 1, ln, T('water_cool', k - 1))
        if i % 3 == 0:
            cv.hline(x + ln + 2, y - 1, 2, T('water', 5))


def sw_water():
    cv = Canvas(SW, SW)
    ground(cv, 0, 0, SW, 8, 'grass', 3, seed=71)
    for x in range(SW):  # the bank: a dark lip, earth, the near water dark under it
        cv.set(x, 8, T('grass', 1)); cv.set(x, 9, T('earth', 2)); cv.set(x, 10, T('earth', 1))
        if noise2(x // 3, 0, 72) < 0.3:
            cv.set(x, 9, T('earth', 3))
    water(cv, 0, 11, SW, SW - 11, 73)
    return cv


def drift(cv, cx, cy, rx, ry, ramp='snow'):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if u * u + v * v <= 1:
                lv = -0.5 * u - 0.9 * v
                cv.set(x, y, T(ramp, 5 if lv > 0.5 else 4 if lv > -0.15 else 2))
    for x in range(int(cx - rx * 0.6), int(cx + rx * 0.9)):   # its shadow on the snow beyond
        cv.set(x, int(cy + ry) + 1, T('snow_cool', 2))


def sw_snow():
    cv = Canvas(SW, SW)
    ground(cv, 0, 0, SW, SW, 'snow', 3, seed=91, density=0.22, share=0.3, contrast=0.3)
    for i, y in enumerate(range(4, SW - 2, 5)):   # a line of footprints, pressed in and shaded
        x = 40 - i * 2 + (2 if i % 2 else 0)
        cv.hline(x, y, 2, T('snow_cool', 1)); cv.hline(x, y + 1, 2, T('snow', 2))
    for (x, y) in ((4, 8), (26, 44), (44, 20)):   # grass tips through the snow
        cv.set(x, y, T('grass', 2)); cv.set(x + 2, y, T('grass', 2)); cv.set(x + 1, y + 1, T('grass', 1))
    for d in ((14, 16, 12, 6), (34, 30, 13, 7), (12, 40, 9, 5)):
        drift(cv, *d)
    for (x, y) in ((30, 6), (40, 14), (6, 28)):  # stones through the snow
        pebble(cv, x, y, 'stone', 2, big=True)
    for (x, y) in ((22, 12), (38, 26), (18, 37)):  # sparkle pairs
        cv.set(x, y, T('snow', 5)); cv.set(x + 1, y, T('snow', 5))
    return cv


def crater(cv: Canvas, cx, cy, rx, ry, ramp='regolith', hard=True):
    """A crater lit from the upper left: the raised rim lit on its outer upper left and
    dark on its outer lower right; inside, the wall below the lit rim in hard shadow, the
    far wall (facing the light) bright, the floor flat between with a few clods."""
    for y in range(int(cy - ry) - 3, int(cy + ry) + 4):
        for x in range(int(cx - rx) - 3, int(cx + rx) + 4):
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = math.sqrt(u * u + v * v)
            lv = -0.6 * u - 0.8 * v
            if d <= 0.8:
                if d > 0.42 and lv > 0.15:
                    k = 0 if hard else 1
                elif d > 0.5 and lv > -0.05:
                    k = 1
                elif d > 0.48 and lv < -0.3:
                    k = 4
                else:
                    k = 2
                cv.set(x, y, T(ramp, k))
            elif d <= 1.0:
                cv.set(x, y, T(ramp, 5 if lv > 0.4 else 4 if lv > -0.25 else 2))
            elif d <= 1.28 and lv < -0.3:
                step(cv, x, y, -1)


def regolith(cv, x0, y0, w, h, seed, contrast=0.2):
    pts = ground(cv, x0, y0, w, h, 'regolith', 3, seed=seed, scale=7, density=0.2, share=0.3, contrast=contrast)
    for i in range(int(w * h / 260)):   # grit and small stones, each with its hard shadow
        x = x0 + int(noise2(i, 5, seed) * (w - 4)); y = y0 + int(noise2(i, 6, seed) * (h - 4))
        pebble(cv, x, y, sib('regolith', noise2(i, 7, seed)), 3, big=noise2(i, 8, seed) < 0.25)
    return pts


def sw_regolith():
    cv = Canvas(SW, SW)
    regolith(cv, 0, 0, SW, SW, 81, contrast=0.3)
    crater(cv, 26, 24, 13, 9)
    return cv


SWATCHES = [('wood', sw_wood), ('stone', sw_stone), ('brick', sw_brick), ('metal', sw_metal),
            ('glass', sw_glass), ('cloth', sw_cloth), ('foliage', sw_foliage), ('water', sw_water),
            ('snow', sw_snow), ('regolith', sw_regolith)]


# --- the exemplars (72 x 72, an adult 25 px tall) ------------------------------------------
EX = 72


def lawn(cv, x0, y0, w, h, seed):
    ground(cv, x0, y0, w, h, 'grass', 3, seed=seed, scale=5)
    for i in range(int(w * h / 150)):
        x = x0 + 1 + int(noise2(i, 1, seed) * (w - 4)); y = y0 + 3 + int(noise2(i, 2, seed) * (h - 3))
        tuft(cv, x, y)


def ex_valley():
    """A cottage's front by the lane: clay tiles at the eave, lime plaster, a 16 x 14 window
    with dusk-violet shutters, sill and flower box, a 14 x 28 door, a dry-stone plinth."""
    cv = Canvas(EX, EX)
    lawn(cv, 0, 60, EX, 12, 101)
    plaster(cv, 0, 16, EX, 38, 102)
    for y in range(16, 54):   # the wall's east end turns from the light
        for x in range(60, EX):
            step(cv, x, y, -1)
    roof_rows(cv, 0, 0, EX, 13, 'clay', 3, row=5, tile=(6, 8), seed=103, moss=True)
    for x in range(EX):
        cv.set(x, 13, T('timber', 4)); cv.set(x, 14, T('timber', 2)); cv.set(x, 15, T('timber', 1))
    overhang(cv, 0, EX, 16, 3)
    wx, wy = 10, 24
    for sx in (wx - 6, wx + 18):
        boards(cv, sx, wy, 6, 16, lambda b, s: ('dusk', 3), board=4, seed=104 + sx, nails=False, grain=0, joints=(40, 41))
        for y in range(wy, wy + 16):
            cv.set(sx + 5, y, T('dusk', 1))
            cv.set(sx, y, T('dusk', 4))
    window(cv, wx, wy, 18, 16, False)
    part(cv, wx - 1, wy + 19, 20, 4, 'timber', 2)   # the flower box
    overhang(cv, wx - 1, wx + 20, wy + 23, 2)
    for i, fx in enumerate(range(wx, wx + 18, 3)):
        cv.hline(fx, wy + 19, 3, T('leaf', 3)); cv.set(fx + 1, wy + 18, T('leaf', 4)); cv.set(fx + 2, wy + 19, T('leaf', 2))
        col = ('berry', 'brass', 'plaster', 'dusk')[i % 4]
        y = wy + 17 + (i % 2)
        cv.hline(fx, y, 2, T(col, 4)); cv.set(fx, y, T(col, 5)); cv.set(fx + 1, y + 1, T(col, 2))
    dx, dy = 44, 26   # the door, deep in a stone surround
    frame(cv, dx - 2, dy - 2, 18, 30, 'stone', 3, t=2)
    boards(cv, dx, dy, 14, 28, lambda b, s: (sib('sky', noise2(b, s, 2)), 3), board=7, seed=105, nails=False, grain=0, joints=(40, 41))
    for y in range(dy, dy + 28):
        cv.set(dx, y, T('sky', 1)); cv.set(dx + 13, y, T('sky', 2))
    for x in range(dx, dx + 14):
        cv.set(x, dy, T('sky', 0))
    cv.set(dx + 10, dy + 15, T('brass', 5)); cv.set(dx + 10, dy + 16, T('brass', 2))
    for i in range(22):   # a climbing rose up the wall beside the door, leaves in clusters
        y = 54 - i * 1.6
        x = 63 + int(2.5 * math.sin(i * 0.7))
        if y < 22:
            break
        cv.hline(x, int(y), 2, T(sib('leaf', noise2(i, 0, 3)), 3 if i % 3 else 4)); cv.set(x + 1, int(y) + 1, T('leaf', 1))
        if i % 4 == 1:
            cv.hline(x - 1, int(y) - 1, 2, T('berry', 4)); cv.set(x - 1, int(y) - 1, T('berry', 5))
    part(cv, 37, 30, 4, 6, 'iron', 2)   # a lantern by the door
    glass(cv, 38, 31, 2, 4, True)
    cv.hline(37, 29, 4, T('iron', 4))
    pick = stone_pick(('stone', 'ashlar'), 7)
    courses(cv, 0, 54, 42, 6, pick, course=3, lengths=(5, 9), seam=T('stone_cool', 1), seed=106)
    courses(cv, 60, 54, 12, 6, pick, course=3, lengths=(5, 9), seam=T('stone_cool', 1), seed=107)
    part(cv, 41, 56, 20, 4, 'stone', 4)
    overhang(cv, 41, 61, 60, 1)
    cast(cv, rect(0, 60, 41, 2) | rect(61, 60, 11, 3))
    return cv


def ex_cogsworth():
    """A workshop's corner: verdigris copper at the eave, brick with soot high up, a cast
    iron downpipe on brackets, a sash under a stone lintel, a gas lamp, setts below."""
    cv = Canvas(EX, EX)
    courses(cv, 0, 58, EX, 14, lambda ci, si: (sib('slate', noise2(ci, si, 9)), 3), course=6, lengths=(8, 10),
            seam=T('slate_cool', 1), seed=111)
    grain(cv, rect(0, 58, EX, 14), 0.05, 117, swap=0.9, up=0.1, down=0.1)
    for x in range(EX):  # copper roof: standing seams every 6 px, weathered in patches
        for y in range(0, 12):
            j = x % 6
            k = 4 if j == 0 else 3 if j < 3 else 2 if j < 5 else 1
            if y < 2:
                k += 1
            cv.set(x, y, T(sib('copper', smooth_noise(x, y, 5, 118)), k))
    for x in range(EX):
        cv.set(x, 12, T('copper', 1)); cv.set(x, 13, T('iron', 2))
    courses(cv, 0, 14, EX, 44, brick_pick(112, 3), course=4, lengths=(8, 8), seam=T('clay_cool', 1), seed=112)
    overhang(cv, 0, EX, 14, 3)
    wx, wy = 30, 22   # the sash window under a stone lintel
    part(cv, wx - 3, wy - 4, 20, 4, 'ashlar', 4)
    frame(cv, wx, wy, 14, 20, 'plaster', 4, t=1)
    glass(cv, wx + 1, wy + 1, 12, 8, True); glass(cv, wx + 1, wy + 10, 12, 9, True)
    cv.hline(wx + 1, wy + 9, 12, T('plaster', 4)); cv.vline(wx + 6, wy + 1, 18, T('plaster', 3))
    for y in range(wy + 1, wy + 9):   # a plant on the sill, seen against the light
        if y > wy + 5:
            cv.hline(wx + 2, y, 3, T('leaf', 1))
    part(cv, wx - 2, wy + 20, 18, 3, 'ashlar', 3)
    overhang(cv, wx - 2, wx + 16, wy + 23, 2)
    cylinder(cv, 8, 14, 4, 42, 'iron', 3)   # the downpipe, brackets, a shoe
    for by in (20, 34, 48):
        part(cv, 7, by, 6, 3, 'iron', 2)
        step(cv, 13, by + 3, -2); step(cv, 13, by + 4, -1)
    part(cv, 6, 54, 8, 4, 'iron', 3)
    for y in range(16, 54):
        step(cv, 12, y, -1); step(cv, 13, y, -2)
    cv.hline(54, 26, 8, T('iron', 2)); cv.hline(54, 25, 8, T('iron', 4))   # the gas lamp
    part(cv, 59, 27, 7, 3, 'iron', 3)
    glass(cv, 60, 30, 5, 7, True)
    for y in range(30, 37):
        cv.set(59, y, T('iron', 4)); cv.set(65, y, T('iron', 1))
    part(cv, 59, 37, 7, 2, 'brass', 3)
    for (x, y) in rect(52, 28, 18, 16):   # its warm light on the brick round it
        if (x - 62) ** 2 + (y - 34) ** 2 < 60 and tone_at(cv, x, y) and hp.family(tone_at(cv, x, y)[0]) in ('clay', 'soot'):
            if (x + y) % 3 == 0 or (x - 62) ** 2 + (y - 34) ** 2 < 30:
                step(cv, x, y, 1)
    cast(cv, rect(0, 58, EX, 3) | rect(14, 58, 3, 6))
    return cv


def ex_reach():
    """A false front in Dust Gulch: sun-bleached boards of three woods, a sign with a mug
    painted on and worn back to the wood in places, a corrugated-iron porch roof on posts
    and the deep shade under it, a boardwalk on sand."""
    cv = Canvas(EX, EX)
    ground(cv, 0, 64, EX, 8, 'sand', 3, seed=121, scale=4)
    woods = lambda bi, si: (sib('bleached' if noise2(bi, si, 3) < 0.75 else 'timber', noise2(bi, si, 4)),
                            3 + (1 if bi < 2 else 0) - (1 if noise2(bi, si, 5) < 0.12 else 0))
    boards(cv, 0, 0, EX, 40, woods, board=4, seed=122)
    grain(cv, rect(0, 0, EX, 40), 0.05, 129, shapes=H_GRAIN, lit=wall_light(0, 0, EX, 40))
    sx0, sx1, sy0, sy1 = 8, 64, 4, 16   # the sign
    boards(cv, sx0, sy0, sx1 - sx0, sy1 - sy0, lambda b, s: (sib('berry', noise2(b, s, 1)), 3), board=4, seed=123, nails=False, grain=0.04)
    for (x, y) in rect(sx0, sy0, sx1 - sx0, sy1 - sy0):
        if smooth_noise(x, y, 2.5, 124) > 0.8 and (y - sy0) % 4 in (1, 2):
            cv.set(x, y, T('bleached', 4 if (y - sy0) % 4 == 1 else 3))   # paint worn back to the wood
    frame(cv, sx0 - 1, sy0 - 1, sx1 - sx0 + 2, sy1 - sy0 + 2, 'bleached', 2, t=1)
    mx = (sx0 + sx1) // 2
    for y in range(8, 14):   # the mug
        cv.hline(mx - 3, y, 5, T('brass', 4 if y > 9 else 5))
    cv.hline(mx - 3, 7, 5, T('plaster', 5)); cv.set(mx - 4, 8, T('plaster', 5))
    cv.vline(mx + 2, 9, 3, T('plaster', 5)); cv.vline(mx + 3, 9, 3, T('plaster', 5))
    cv.vline(mx - 1, 10, 3, T('brass', 2))
    for dx in (-12, 12):
        for (x, y) in ((0, 0), (-1, 1), (1, 1), (0, 2)):
            cv.set(mx + dx + x, 9 + y, T('plaster', 5))
    window(cv, 28, 20, 16, 15, False, ramp='bleached', curtain=False)
    for y in range(40, 46):   # the porch roof: corrugated iron, rust in patches, lit crests
        for x in range(EX):
            j = x % 4
            k = 4 if j == 0 else 3 if j == 1 else 2
            if y == 40:
                k = 5 if j == 0 else 4
            if y == 45:
                k = 1
            rust = smooth_noise(x // 2, y, 5, 125) > 0.7 and 41 < y < 45
            cv.set(x, y, T('clay_cool', k - 1) if rust else T('iron', k))
    for y in range(46, 62):   # under the porch: the shop front in shade, boards two tones down
        boards(cv, 0, 46, EX, 16, lambda b, s: (sib('bleached', noise2(b, s, 6)), 1), board=4, seed=126, nails=False)
        break
    frame(cv, 25, 47, 22, 15, 'timber', 2, t=1)
    for (x, y) in rect(26, 48, 20, 14):
        cv.set(x, y, T('earth_cool', 0))
    for (sx, sw) in ((27, 8), (37, 8)):   # the batwing doors
        boards(cv, sx, 51, sw, 8, lambda b, s: ('bleached', 2), board=4, seed=127 + sx, nails=False, grain=0, joints=(40, 41))
        cv.vline(sx + sw - 1, 51, 8, T('bleached', 0))
    for px in (2, 66):
        cylinder(cv, px, 46, 4, 16, 'bleached', 2)
    for x in range(EX):   # the boardwalk
        for y in range(62, 65):
            cv.set(x, y, T(sib('timber', noise2(x // 8, 0, 9)), 4 if y == 62 else 3 if y == 63 else 1))
        if x % 8 == 0:
            cv.set(x, 63, T('timber', 1)); cv.set(x, 62, T('timber', 2))
    cast(cv, rect(0, 65, EX, 2) | rect(6, 65, 3, 4) | rect(70, 65, 2, 4))
    for (x, y) in ((10, 69), (44, 70), (58, 68)):
        pebble(cv, x, y, 'sand', 3)
    return cv


def ex_castle():
    """Hearthold's gate: dressed stone in courses, an arch of wedge stones with a keystone,
    a studded oak door set deep in it, a dusk banner with the moon, flagstones, moss low."""
    cv = Canvas(EX, EX)
    courses(cv, 0, 0, EX, 60, stone_pick(('ashlar', 'ashlar', 'stone'), 9), course=6, lengths=(9, 15), seam=T('stone_cool', 1), seed=131)
    grain(cv, rect(0, 0, EX, 60), 0.05, 136, lit=wall_light(0, 0, EX, 60))
    moss_joints(cv, 0, 0, EX, 60, 6, 132, rate=0.12)
    courses(cv, 0, 60, EX, 12, stone_pick(('stone',), 11), course=6, lengths=(10, 16), seam=T('stone_cool', 1), seed=134)
    cx, top, half, foot = 42, 14, 15, 60
    spring = top + half
    opening = {(x, y) for x in range(cx - half, cx + half) for y in range(top, foot)
               if y >= spring or (x + 0.5 - cx) ** 2 + (y + 0.5 - spring) ** 2 <= half * half}
    outer = half + 6
    ring = {(x, y) for x in range(cx - outer, cx + outer) for y in range(top - 6, spring + 1)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - spring) ** 2 <= outer * outer} - opening
    for x in (cx - outer, cx - outer + 1, cx - outer + 2, cx - outer + 3, cx - outer + 4, cx - outer + 5):
        for y in range(spring, foot):   # the jambs, in tall blocks
            ring.add((x, y)); ring.add((2 * cx - x - 1, y))
    nseg = 9
    for (x, y) in ring:
        if y >= spring:
            ci = (y - spring) // 8
            r_ = (y - spring) % 8
            k = 3 + (1 if (x < cx and x == cx - outer) else 0) - (1 if x >= cx + half + 4 else 0)
            col = T('stone_cool', 1) if r_ == 7 else T(sib('ashlar', noise2(ci, x > cx, 2)), k + (1 if r_ == 0 else 0))
            cv.set(x, y, col)
            continue
        a = math.atan2(-(y + 0.5 - spring), x + 0.5 - cx)   # 0 at the east springer, pi at the west
        f = a / math.pi * nseg
        idx = int(f)
        r = math.hypot(x + 0.5 - cx, y + 0.5 - spring)
        joint = abs(f - round(f)) < 0.09 * outer / max(r, 1)
        lv = math.cos(a - 2.3)   # wedges facing the upper left are lit
        k = 3 + (1 if lv > 0.3 else 0) - (1 if lv < -0.4 else 0) + (1 if idx == nseg // 2 else 0)
        if r > outer - 1.2:
            k += 1 if lv > 0 else 0
        if r < half + 1.2:
            k -= 1
        cv.set(x, y, T('stone_cool', 1) if joint else T(sib('ashlar', noise2(idx, 0, 4)), k))
    for (x, y) in opening:   # the deep reveal: the soffit in shade, the door set back
        cv.set(x, y, T('stone_cool', 1))
    door = {(x, y) for (x, y) in opening if cx - half + 3 <= x < cx + half - 1 and
            (y >= spring or (x + 0.5 - cx) ** 2 + (y + 0.5 - spring) ** 2 <= (half - 3) ** 2)}
    xs = [p[0] for p in door]
    for (x, y) in door:   # oak planks, vertical, each its own ramp
        pi_, j = divmod(x - min(xs), 6)
        rp = sib('timber', noise2(pi_, 0, 135))
        k = 3 if j == 1 else 1 if j == 5 else 0 if j == 0 else 2
        cv.set(x, y, T(rp, k))
    grain(cv, door, 0.06, 137, shapes=V_GRAIN)
    for sy in (top + 12, top + 26, top + 38):   # iron straps with studs
        for x in range(min(xs), max(xs) + 1):
            if (x, sy) in door:
                cv.set(x, sy, T('iron', 3)); cv.set(x, sy + 1, T('iron', 1))
                if x % 5 == 2:
                    cv.set(x, sy - 1, T('iron', 4))
    for (x, y) in opening - door:
        if x < cx - half + 3:
            cv.set(x, y, T('stone', 2))   # the west reveal catches a little light
    banner(cv, 5, 18, 12, 28)
    for y in range(18, 50):
        step(cv, 17, y + 1, -2); step(cv, 18, y + 2, -1)
    cast(cv, rect(cx - outer, 60, 2 * outer, 2))
    return cv


def ex_neon():
    """A shopfront in Neon Harbour at night: concrete over a steel shopfront, a lit flat
    window above, the shop window lit from inside with shelves and jars, a neon sign (a
    crescent and a cup, no words) with its glow laid on the fascia in bands, an air
    conditioner, cables, the wet street doubling the light."""
    cv = Canvas(EX, EX)
    courses(cv, 0, 0, EX, 22, lambda ci, si: (sib('concrete', noise2(ci, si, 4)), 2 + (1 if noise2(ci, si, 5) > 0.7 else 0)),
            course=11, lengths=(18, 24), seam=T('asphalt', 1), seed=141)
    grain(cv, rect(0, 0, EX, 22), 0.06, 143, lit=wall_light(0, 0, EX, 22), up=0.15, down=0.4)
    for x in range(0, EX):   # rain streaks down the concrete
        if noise2(x, 0, 144) < 0.12:
            for y in range(1, 8 + int(noise2(x, 1, 144) * 10)):
                step(cv, x, y, -1)
    window(cv, 8, 3, 14, 13, True)
    for (x, y) in rect(1, 2, 5, 18):   # a vertical blade sign in cyan, abstract marks
        k = 1 if x in (1, 5) or y in (2, 19) else 4 if (y % 4 == 0 or (x == 3 and y % 4 == 2)) else 2
        cv.set(x, y, T('neon_cyan', k))
    for y in range(4, 18):
        step(cv, 6, y, 1); step(cv, 7, y, 1)
    cv.hline(10, 14, 4, T('leaf', 3)); cv.hline(11, 13, 2, T('leaf', 4))   # a plant on the sill
    for (px, py, pw, ph, rp) in ((26, 5, 7, 9, 'plaster'), (34, 7, 6, 8, 'sky'), (25, 13, 6, 6, 'berry')):
        part(cv, px, py, pw, ph, rp, 3, glint=False)   # old posters, layered, peeling
        cv.hline(px + 1, py + 2, pw - 2, T(rp, 1)); cv.hline(px + 1, py + 4, pw - 3, T(rp, 2))
        cv.set(px + pw - 1, py + ph - 1, T('concrete', 2))
    cylinder(cv, 66, 0, 3, 22, 'iron', 2)   # a drainpipe
    part(cv, 46, 6, 14, 9, 'panel', 3)   # an air conditioner with its grille
    for x in range(48, 58, 2):
        cv.vline(x, 8, 5, T('panel', 1))
    cv.vline(53, 15, 7, T('iron', 1))
    for x in range(EX):   # a cable sagging across
        cv.set(x, 1 + int(2.5 * math.sin(x / EX * math.pi)), T('iron', 0))
    for x in range(EX):   # the fascia, in small glazed tiles
        for y in range(22, 30):
            k = 3 if y == 22 else 1 if y == 29 else 2
            if 23 <= y <= 28 and (x % 4 == 0 or y == 25):
                k = 1
            cv.set(x, y, T(sib('asphalt', noise2(x // 4, (y - 23) // 3, 7), 0.35), k))
    tube = set()   # a crescent and a steaming cup: a night cafe, no words
    tube |= {(x, y) for (x, y) in disc(40, 25.5, 3.6) if (x + 0.5 - 41.8) ** 2 + (y + 0.5 - 24.6) ** 2 > 7.5}
    tube |= {(47, y) for y in range(24, 29)} | {(52, y) for y in range(24, 29)} | {(x, 28) for x in range(47, 53)}
    tube |= {(53, 25), (54, 25), (54, 26), (53, 27), (49, 22), (50, 23), (50, 21)}
    for (x, y) in tube:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                p = (x + dx, y + dy)
                if p not in tube and 22 < p[1] < 29:
                    hit = tone_at(cv, *p)
                    if hit and hit[0] == 'asphalt':
                        cv.set(*p, T('neon_pink', 0 if abs(dx) + abs(dy) > 2 else 1))
    for (x, y) in tube:
        cv.set(x, y, T('neon_pink', 4))
    for (x, y) in ((38, 24), (39, 23), (47, 25), (52, 26)):
        cv.set(x, y, T('neon_pink', 5))
    for (x, y) in rect(0, 30, EX, 28):   # the shopfront
        cv.set(x, y, T('iron', 2))
    glass(cv, 4, 32, 40, 26, True)
    for (x, y) in rect(5, 33, 38, 24):   # the room behind the glass: a back wall, a floor
        k = 2 if y < 35 else 1 if y > 53 else 3 if (x // 9) % 2 else 4
        cv.set(x, y, T('lamp', k))
    for (x, y) in disc(14, 35, 2.2):   # a pendant lamp and its pool
        cv.set(x, y, T('lamp', 5))
    cv.vline(14, 33, 1, T('iron', 1))
    for sy in (40, 48):   # shelves with jars and boxes, in clusters
        cv.hline(5, sy, 38, T('timber', 2)); cv.hline(5, sy + 1, 38, T('timber', 0))
        for i, x in enumerate(range(7, 42, 5)):
            col = ('lagoon', 'berry', 'brass', 'plaster', 'sky', 'leaf')[(i + sy) % 6]
            hgt = 3 + (i % 2)
            cv.vline(x, sy - hgt, hgt, T(col, 3)); cv.vline(x + 1, sy - hgt, hgt, T(col, 2))
            cv.set(x, sy - hgt, T(col, 4))
    for y in range(32, 58):
        cv.set(24, y, T('iron', 3)); cv.set(25, y, T('iron', 1))
    frame(cv, 48, 32, 20, 26, 'iron', 3, t=2)
    glass(cv, 50, 34, 16, 24, True)
    cv.set(52, 46, T('brass', 5)); cv.set(52, 47, T('brass', 2))
    for (x, y) in rect(51, 36, 14, 8):   # a blind half down the door's glass
        cv.set(x, y, T('plaster', 4 if (y - 36) % 2 == 0 else 3))
    for x in range(EX):   # the kerb
        for y in range(58, 62):
            cv.set(x, y, T(sib('concrete', noise2(x // 9, 0, 3)), 3 if y == 58 else 2 if y < 61 else 1))
        if x % 9 == 0:
            for y in range(59, 62):
                cv.set(x, y, T('concrete', 0))
    ground(cv, 0, 62, EX, 10, 'asphalt', 2, seed=142, scale=3, density=0.14)
    for x in range(34, 68):   # a puddle doubling the sign and the window in broken bands
        for y in range(64, 71):
            u, v = (x - 51) / 17, (y - 67.5) / 3.6
            if u * u + v * v <= 1:
                cv.set(x, y, T('asphalt', 1))
                if (y // 2) % 2 == 0 and any((x, ty) in tube for ty in range(21, 29)):
                    cv.set(x, y, T('neon_pink', 2))
                if (y // 2) % 2 == 1 and 52 <= x <= 64 and x % 3 < 2:
                    cv.set(x, y, T('lamp', 1))
    for x in range(6, 32, 3):   # the lit window spills onto the pavement
        cv.hline(x, 63, 2, T('asphalt', 4))
    for y in range(52, 62):   # an A-board with a chalk menu: a cup and three lines
        for x in range(26, 34):
            cv.set(x, y, T('timber', 3 if x == 26 or y == 52 else 2 if x < 33 else 1))
        if 53 <= y <= 59 and y % 2 == 1:
            cv.hline(28, y, 4, T('plaster', 4 if y < 56 else 3))
    for (x, y) in disc(5, 54, 3.4):   # a potted fern
        cv.set(x, y, T(sib('leaf', noise2(x, y, 3), 0.35), 4 if x + y < 59 else 2))
    part(cv, 2, 56, 7, 5, 'clay', 3)
    return cv


def ex_station():
    """A pressure module on Lumen: a white shell with panel seams and rivets, its lit top,
    a round hatch in a frame with a handwheel, hazard bands, a radiator, a cable run,
    footings, and the hard airless shadow on the regolith."""
    cv = Canvas(EX, EX)
    regolith(cv, 0, 50, EX, 22, 151)
    plates(cv, 4, 6, 50, 10, 'hull', 150, pw=12, ph=10, other='panel', lift=1)   # the top of the shell, lit
    rivets(cv, 7, 52, 9, every=6)
    cv.hline(4, 15, 50, T('hull', 2))
    for (x, y) in rect(28, 7, 12, 6):   # a solar strip on the roof, its cells catching the sky
        cv.set(x, y, T('void', 3 if (x - 28) % 4 == 0 or y == 7 else 2) if (x, y) != (29, 8) else T('sky', 4))
    cv.hline(29, 8, 3, T('sky', 4))
    part(cv, 8, 7, 8, 5, 'panel', 3)   # a vent box and a beacon on a stub mast
    cv.hline(9, 9, 6, T('panel', 1))
    cv.vline(46, 3, 5, T('iron', 3)); cv.hline(46, 2, 2, T('berry', 5)); cv.set(47, 3, T('berry', 3))
    plates(cv, 4, 16, 50, 28, 'hull', 152, pw=16, ph=10, other='panel')
    for y in (18, 28, 38):
        rivets(cv, 7, 50, y, every=6)
    grain(cv, rect(4, 6, 50, 40), 0.03, 153, shapes=H_GRAIN, up=0.1, down=0.45)
    for y in range(16, 46):   # the east end turns away from the light
        for x in range(46, 54):
            step(cv, x, y, -1 if x < 50 else -2)
    hx, hy = 22, 31   # the hatch
    for (x, y) in disc(hx, hy, 10):
        cv.set(x, y, T('panel', 4 if (x - hx) + (y - hy) < -4 else 3 if (x - hx) + (y - hy) < 4 else 2))
    for (x, y) in disc(hx, hy, 7.5):
        cv.set(x, y, T('panel', 1))
    for (x, y) in disc(hx, hy, 6.5):
        lv = -(x + 0.5 - hx) - (y + 0.5 - hy)
        cv.set(x, y, T('hull', 4 if lv > 3 else 3 if lv > -3 else 2))
    for (x, y) in disc(hx, hy, 3):
        cv.set(x, y, T('brass', 3))
    for (x, y) in disc(hx, hy, 1.6):
        cv.set(x, y, T('brass', 1))
    for (dx, dy) in ((0, -4), (0, 3), (-4, 0), (3, 0)):
        cv.set(hx + dx, hy + dy, T('brass', 4 if dx <= 0 and dy <= 0 else 2))
    cv.hline(hx - 1, hy - 4, 2, T('brass', 5))
    cv.hline(36, 22, 2, T('glowflora', 4))   # the status light, green: the dome is at pressure
    part(cv, 36, 26, 12, 7, 'panel', 3)   # a service panel: a grille, a label plate, a valve
    for x in range(38, 46, 2):
        cv.vline(x, 28, 3, T('panel', 1))
    part(cv, 8, 20, 8, 4, 'brass', 4, glint=False)
    cv.hline(9, 21, 6, T('brass', 2))
    for x in range(36, 50):   # a stencilled band, berry, with its scuffs
        for y in range(36, 39):
            cv.set(x, y, T('berry', 3 if y == 37 else 4 if y == 36 else 2))
    grain(cv, rect(4, 34, 50, 10), 0.08, 154, shapes=H_GRAIN[:2], swap=0.3, up=0.05, down=0.6)
    for (x, y) in rect(4, 36, 46, 8):   # moon dust kicked up onto the lower plates, in clusters
        if smooth_noise(x, y, 3, 155) > 0.66 and tone_at(cv, x, y) and hp.family(tone_at(cv, x, y)[0]) in ('hull', 'panel'):
            cv.set(x, y, T(sib('regolith', noise2(x, y, 156)), 4 if y < 40 else 3))
    for x in range(4, 54):   # hazard bands on the sill
        for y in range(44, 47):
            cv.set(x, y, T('brass', 4 if y == 44 else 3) if ((x + y) // 3) % 2 else T('iron', 1))
    for x in range(56, 70):   # the radiator, a fin array on a post
        for y in range(8, 34):
            f = (x - 56) % 3
            cv.set(x, y, T('panel', 4 if f == 0 else 3 if f == 1 else 1))
    cv.hline(56, 8, 14, T('panel', 5)); cv.hline(56, 33, 14, T('panel', 1))
    for y in (3, 4):   # a pipe along the roof, copper with brass collars, and its clamps
        cv.hline(6, y, 46, T('copper', 4 if y == 3 else 2))
    for x in range(10, 52, 12):
        cv.vline(x, 2, 4, T('brass', 4)); cv.vline(x + 1, 2, 4, T('brass', 2))
    cylinder(cv, 61, 34, 3, 16, 'iron', 3)
    for fx in (8, 40):
        part(cv, fx, 46, 8, 5, 'iron', 3)
    solid = {(x, y) for y in range(0, 51) for x in range(EX) if cv.get(x, y)[3] == 255}
    outline(cv, solid)
    sh = set()   # the hard shadow: the module thrown down and to the right, three tones down
    for (x, y) in solid:
        if y > 30:
            for k in range(1, 6):
                sh.add((x + k + (y - 30) // 4, 51 + (y - 30) // 3 + k // 3))
    cast(cv, {p for p in sh if 51 <= p[1] < EX and 0 <= p[0] < EX and p not in solid}, k=3)
    for x in range(14, 62):   # the cable run on the ground
        y = 53 + (1 if 30 < x < 50 else 0)
        cv.set(x, y, T('berry', 3)); cv.set(x, y + 1, T('berry', 1))
    for i, x in enumerate(range(2, 40, 7)):   # bootprints, in pairs
        y = 64 + (i % 2) * 3
        cv.hline(x, y, 2, T('regolith', 1)); cv.hline(x, y + 1, 2, T('regolith', 2))
    return cv


def ex_moon():
    """Lumen's ground: regolith grey to brown-grey in calm patches with grit, a crater with
    a raised rim and a hard shadow inside, ejecta, boulders with black shadows, a rover track."""
    cv = Canvas(EX, EX)
    regolith(cv, 0, 0, EX, EX, 161)
    crater(cv, 34, 30, 20, 14)
    crater(cv, 60, 62, 7, 5)
    crater(cv, 10, 58, 5, 3.5)
    for i in range(14):
        a = i * 0.48 + 0.2
        rr = 24 + 7 * noise2(i, 1, 162)
        x, y = int(34 + rr * math.cos(a)), int(30 + rr * 0.72 * math.sin(a))
        if 0 <= x < EX - 2 and 0 <= y < EX:
            cv.hline(x, y, 2, T('regolith_warm', 4))
    for (bx, by, r) in ((8, 8, 4), (62, 14, 3), (22, 64, 3)):   # boulders with black shadows
        pts = disc(bx, by, r)
        for (x, y) in pts:
            lv = -(x + 0.5 - bx) - (y + 0.5 - by)
            cv.set(x, y, T('stone_cool', 4 if lv > r * 0.6 else 3 if lv > -r * 0.4 else 1))
        for (x, y) in pts:
            for k in (1, 2, 3):
                if (x + k, y + 1) not in pts:
                    step(cv, x + k, y + 1, -3)
    for x in range(0, EX):   # a rover track: two ribbed lines
        for ty in (46, 51):
            y = ty + int(3 * math.sin(x * 0.05))
            hit = tone_at(cv, x, y)
            if hit and hp.family(hit[0]) == 'regolith':
                cv.set(x, y, T('regolith', 2 if x % 3 else 1))
    return cv


EXEMPLARS = [('valley', 'A cottage front', ex_valley), ('cogsworth', 'Brick and iron', ex_cogsworth),
             ('reach', 'A desert false front', ex_reach), ('castle', 'The castle gate', ex_castle),
             ('neon', 'A neon shopfront', ex_neon), ('station', 'A station module', ex_station),
             ('moon', 'Regolith and a crater', ex_moon)]


# --- today's versions, cut from the current art --------------------------------------------
def _sprite(mod: str, key: str):
    import importlib
    import style
    return style.finalize(importlib.import_module(mod).props()[key], name=key).img


def _on(img, bg, at=(0, 0)):
    out = Image.new('RGBA', (EX, EX), bg)
    out.alpha_composite(img, at)
    return out


def today() -> dict:
    """The same subjects as they are drawn today (main), at the same scale."""
    grey = (110, 116, 98, 255)
    out = {}
    cot = _sprite('harbour_props', 'cottage')
    out['valley'] = _on(cot.crop((4, cot.height - EX, 4 + EX, cot.height)), grey)
    ws = _sprite('steampunk_props', 'workshop')
    out['cogsworth'] = _on(ws.crop((0, ws.height - EX, EX, ws.height)), grey)
    sal = _sprite('western_props', 'saloon')
    out['reach'] = _on(sal.crop((16, 10, 16 + EX, 10 + EX)), (214, 180, 132, 255))
    gh = _sprite('castle_props', 'gatehouse')
    out['castle'] = _on(gh.crop((25, gh.height - EX, 25 + EX, gh.height)), grey)
    cb = _sprite('cyber_props', 'city_b0')
    out['neon'] = _on(cb.crop((0, cb.height - EX, EX, cb.height)), (40, 38, 60, 255))
    lumen = os.path.join(HERE, '..', '..', 'assets', 'zones', 'lumen', 'ground.png')
    gnd = Image.open(lumen).convert('RGBA')
    gnd = gnd.resize((gnd.width // 4, gnd.height // 4), Image.NEAREST)
    am = _sprite('space_props', 'airlock_module')
    st = gnd.crop((120, 200, 120 + EX, 200 + EX))
    st.alpha_composite(am, ((EX - am.width) // 2, EX - am.height - 6))
    out['station'] = st
    out['moon'] = gnd.crop((0, 100, EX, 100 + EX))
    return out


# --- the sheet -----------------------------------------------------------------------------
def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _big(cv_or_img, s=SCALE):
    img = cv_or_img.img if isinstance(cv_or_img, Canvas) else cv_or_img
    return img.resize((img.width * s, img.height * s), Image.NEAREST)


def palette_strip(width: int) -> Image.Image:
    names = [n for n in R if not PAL['kinds'][n].startswith('sibling')]
    cell = 14 * SCALE // 3 * 2
    per_row = max(1, (width - 20) // (cell * 7 + 20))
    rows = (len(names) + per_row - 1) // per_row
    im = Image.new('RGBA', (width, rows * (cell + 18) + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = _font(12)
    for i, n in enumerate(names):
        r, c = divmod(i, per_row)
        x0, y0 = 10 + c * (cell * 7 + 20), 4 + r * (cell + 18)
        kind = PAL['kinds'][n].replace('accent:', '')
        d.text((x0, y0), f'{n}  ({kind}{", +warm, +cool" if f"{n}_warm" in R else ""})', fill=(236, 230, 214, 255), font=f)
        for j, col in enumerate(R[n]):
            d.rectangle([x0 + j * cell, y0 + 14, x0 + (j + 1) * cell - 2, y0 + 14 + cell - 4], fill=col)
        if n in EDGES:
            d.rectangle([x0 + 6 * cell + 4, y0 + 14, x0 + 7 * cell, y0 + 14 + cell - 4], fill=EDGES[n])
    return im


def build(out_dir: str):
    os.makedirs(os.path.join(out_dir, 'pairs'), exist_ok=True)
    swatches = [(n, f()) for n, f in SWATCHES]
    for n, cv in swatches:
        assert cv.w == SW and cv.h == SW, n
    house = [(k, t, f()) for k, t, f in EXEMPLARS]
    now = today()
    bg = (52, 48, 58, 255)
    fg = (236, 230, 214, 255)
    pad = 10 * SCALE
    col_w = EX * SCALE + pad
    width = pad + len(house) * col_w
    pal = palette_strip(width)
    f_title, f_lab = _font(26), _font(15)
    title_h = 60
    sw_h = SW * SCALE + 30
    row_h = EX * SCALE + 34
    height = title_h + pal.height + 20 + sw_h + 30 + 2 * row_h + 40
    sheet = Image.new('RGBA', (width, height), bg)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 14), 'NapAttack house style: one game, every setting (3x; an adult is 25 px)', fill=fg, font=f_title)
    y = title_h
    sheet.alpha_composite(pal, (0, y))
    y += pal.height + 20
    sw_col = (width - pad) // len(swatches)
    for i, (n, cv) in enumerate(swatches):
        x = pad + i * sw_col
        sheet.alpha_composite(_big(cv), (x, y))
        d.text((x, y + SW * SCALE + 6), n, fill=fg, font=f_lab)
    y += sw_h + 30
    for label, imgs in (('today (main)', [now[k] for k, _t, _c in house]), ('house style', [c for _k, _t, c in house])):
        d.text((pad, y - 22), label, fill=fg, font=f_lab)
        for i, img in enumerate(imgs):
            x = pad + i * col_w
            sheet.alpha_composite(_big(img), (x, y))
            if label == 'house style':
                d.text((x, y + EX * SCALE + 6), house[i][1], fill=fg, font=f_lab)
        y += row_h
    sheet.save(os.path.join(out_dir, 'sheet.png'))
    for k, t, cv in house:   # before and after, side by side
        pair = Image.new('RGBA', (2 * EX * SCALE + 3 * pad, EX * SCALE + 50), bg)
        dp = ImageDraw.Draw(pair)
        pair.alpha_composite(_big(now[k]), (pad, 36))
        pair.alpha_composite(_big(cv), (2 * pad + EX * SCALE, 36))
        dp.text((pad, 10), f'{t}: today', fill=fg, font=f_lab)
        dp.text((2 * pad + EX * SCALE, 10), 'house style', fill=fg, font=f_lab)
        pair.save(os.path.join(out_dir, 'pairs', f'{k}.png'))
    return swatches, house, now


def report(swatches, house, now):
    import style_lint
    print('\nstyle lint (report only), today -> house, on each exemplar as a whole 72 x 72 crop:')
    print(f'{"exemplar":12s} {"colours":>15s} {"on house":>15s} {"lone px":>15s} {"W-E light":>15s}')
    for k, _t, cv in house:
        a, b = style_lint.measure(now[k]), style_lint.measure(cv.img)
        print(f'{k:12s} {a["colours"]:6d} -> {b["colours"]:5d} {100 * a["on_house"]:5.0f}% -> {100 * b["on_house"]:4.0f}% '
              f'{100 * a["isolated"]:5.1f}% -> {100 * b["isolated"]:4.1f}% {a["west_east"]:+6.1f} -> {b["west_east"]:+5.1f}')
    try:
        import detail_bar
    except ImportError:
        print('\n(detail_bar.py is not on this branch: the counts against Eastward are skipped)')
        return
    kinds = {'wood': 'wood-front', 'stone': 'stone-wall', 'brick': 'stone-wall', 'metal': 'machinery',
             'foliage': 'tree', 'water': 'water', 'regolith': 'ground', 'snow': 'ground'}
    print('\ndetail bar (Eastward, same character height):')
    for n, cv in swatches:
        if n in kinds:
            ok, _c, lines = detail_bar.check_image(cv.img.convert('RGB'), (0, 0, SW, SW), kinds[n])
            print(f'  {n:9s} {kinds[n]:11s} {"PASS" if ok else "FAIL"}  ' + '; '.join(lines))
    ex_kinds = {'valley': ('facade', (0, 16, 72, 54)), 'cogsworth': ('facade', (0, 14, 72, 58)),
                'reach': ('wood-front', (0, 0, 72, 40)), 'castle': ('stone-wall', (0, 0, 72, 60)),
                'neon': ('facade', (0, 0, 72, 62)), 'station': ('machinery', (4, 6, 54, 46)),
                'moon': ('ground', (0, 0, 72, 72))}
    for k, _t, cv in house:
        kind, box = ex_kinds[k]
        ok, _c, lines = detail_bar.check_image(cv.img.convert('RGB'), box, kind)
        ok0, _c0, lines0 = detail_bar.check_image(now[k].convert('RGB'), box, kind)
        print(f'  {k:9s} {kind:11s} today {"PASS" if ok0 else "FAIL"}  house {"PASS" if ok else "FAIL"}  ' + '; '.join(lines))


def main(argv) -> int:
    import tempfile
    out = argv[0] if argv else os.path.join(tempfile.gettempdir(), 'napattack-house-style')
    sw, house, now = build(out)
    print('wrote', os.path.join(out, 'sheet.png'), 'and', len(house), 'pairs in', os.path.join(out, 'pairs'))
    report(sw, house, now)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
