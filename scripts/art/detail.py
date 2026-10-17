"""Material detail: the texture and depth rules every prop shares (coherence plan, 6c).

Matt (17 Oct): the house and most props read flat, the beds are boxes. Clean planes
alone are not enough at this density; each material needs its own small structure,
lit from the upper left, and every overhang and recess needs its shadow:

- shingles: courses with a dark seam under each one, staggered joints, lit tips and
  rounded corners, a few shingles a tone lighter or darker;
- boards (siding, planks, planters): a lit top edge, a shadow edge, grain streaks
  and butt joints;
- stones: irregular stones, each lit on its top left and shaded on its bottom
  right, set in dark mortar, the odd one mossy;
- recesses (windows, doors) are shaded along their top and left inside edges;
  overhangs (eaves, sills, rims) cast a band of shadow below and to the right.

Shading never invents colours: `shade` steps a pixel down its own ramp, so shadows
stay in the material's hue family (the ramps are hue-shifted: cool in the shadows,
warm in the light).
"""
from __future__ import annotations

from materials import MATERIALS
from pixel import Canvas, noise2

_LOOKUP: dict[tuple[int, int, int], tuple[list, int]] = {}
for _ramp in MATERIALS.values():
    for _i, _c in enumerate(_ramp):
        _LOOKUP.setdefault(tuple(int(_c[k:k + 2], 16) for k in (1, 3, 5)), (_ramp, _i))


def tone(ramp, i: int) -> str:
    return ramp[max(0, min(len(ramp) - 1, i))]


def shade(cv: Canvas, x: int, y: int, k: int = 1):
    """Step the pixel at (x, y) k tones down (or up, for negative k) its own ramp.
    Pixels whose colour is not on a ramp are left alone."""
    c = cv.get(x, y)
    if not c[3]:
        return
    hit = _LOOKUP.get(c[:3])
    if hit:
        ramp, i = hit
        cv.set(x, y, tone(ramp, i - k))


def shade_set(cv: Canvas, pts, k: int = 1):
    for (x, y) in pts:
        shade(cv, x, y, k)


def _var(*key) -> int:
    """A stable per-element tone variation: mostly 0, sometimes one step either way."""
    n = noise2(*key)
    return -1 if n < 0.18 else 1 if n > 0.84 else 0


def shingles(cv: Canvas, pts, ramp, base: int, y0: int, course: int = 4, width: int = 7,
             seed: int = 0, offset=None):
    """A shingled roof plane over the points `pts`. Courses run from y0. Each course has
    a dark seam along its top (the course above overlaps and shades it), dark joints
    between shingles and a lit lower lip (the shingle's thick edge), so every course
    reads as raised. One shingle in ten is a step lighter and one in twelve a step
    darker, so the roof reads as many shingles without turning to noise. `offset(x, y)`
    adds a tone offset (cast shadows on the roof)."""
    for (x, y) in pts:
        ci, r = divmod(y - y0, course)
        shift = (width // 2) if ci % 2 else 0
        si, c = divmod(x + shift, width)
        n = noise2(ci, si, seed)
        t = base + (1 if n > 0.9 else -1 if n < 0.08 else 0)
        if r == 0:
            t -= 2
        elif c == 0 and r < course - 1:
            t -= 2
        elif r == course - 1:
            t = t - 1 if c == 0 else t + 1
        if offset:
            t += offset(x, y)
        cv.set(x, y, tone(ramp, t))


def boards(cv: Canvas, pts, ramp, base: int, y0: int, board: int = 4, seed: int = 0,
           vertical: bool = False, x0: int = 0, offset=None, grain: float = 0.0,
           joints: bool = True):
    """Siding or planks: each board has a lit leading edge and a shadow edge, and the
    odd butt joint (a dark seam with a lit pixel after it); `grain` adds sparse streaks.
    Horizontal boards run along x; vertical boards along y."""
    pts = set(pts)
    for (x, y) in pts:
        along, across = (y, x - x0) if vertical else (x, y - y0)
        bi, r = divmod(across, board)
        t = base
        if r == 0:
            t += 1
        elif r == board - 1:
            t -= 1
        inner = 0 < r < board - 1
        span = 30 + int(noise2(bi, seed, 6) * 24)
        j = (along + int(noise2(bi, seed, 7) * span)) % span
        if joints and inner and j == 0:
            t -= 1
        elif joints and inner and j == 1:
            t += 1
        elif inner and grain and noise2(x // 3, y, seed + 9) < grain:
            t -= 1  # a grain streak, three pixels long
        if offset:
            t += offset(x, y)
        cv.set(x, y, tone(ramp, t))


def stones(cv: Canvas, x0: int, y0: int, w: int, h: int, ramp, seed: int = 0, course: int = 4,
           moss=None, base: int = 2):
    """Irregular dressed stones in courses, each lit on its top left and shaded on its
    bottom right, in dark mortar; the odd stone on the top course carries moss."""
    mortar = tone(ramp, base - 2)
    y = y0
    ci = 0
    while y < y0 + h:
        ch = min(course, y0 + h - y)
        x = x0 - int(noise2(ci, seed, 1) * 4)
        si = 0
        while x < x0 + w:
            sw = 4 + int(noise2(ci, si, seed + 2) * 6)
            t = base + _var(ci, si, seed + 3)
            for yy in range(y, y + ch):
                for xx in range(max(x, x0), min(x + sw, x0 + w)):
                    r, c = yy - y, xx - x
                    if r == ch - 1 or c == sw - 1:
                        col = mortar
                    elif (r == 0 and c == 0) or (r == ch - 2 and c == sw - 2):
                        col = mortar  # rounded corners
                    elif r == 0 or c == 0:
                        col = tone(ramp, t + 1)
                    elif r == ch - 2 or c == sw - 2:
                        col = tone(ramp, t - 1)
                    else:
                        col = tone(ramp, t)
                    cv.set(xx, yy, col)
            if moss and ci == 0 and noise2(si, seed, 4) < 0.3:
                for k in range(1, min(4, sw - 1)):
                    cv.set(x + k, y, moss[3] if k % 2 else moss[2])
            x += sw
            si += 1
        y += ch
        ci += 1


def bricks(cv: Canvas, x0: int, y0: int, w: int, h: int, ramp, seed: int = 0, base: int = 2):
    """Bricks three rows tall and six wide, staggered, each with a lit top edge."""
    mortar = tone(ramp, base - 2)
    for y in range(y0, y0 + h):
        ci, r = divmod(y - y0, 3)
        shift = 3 if ci % 2 else 0
        for x in range(x0, x0 + w):
            bi, c = divmod(x - x0 + shift, 6)
            t = base + _var(ci, bi, seed)
            if r == 2 or c == 5:
                col = mortar
            elif r == 0:
                col = tone(ramp, t + 1)
            else:
                col = tone(ramp, t)
            cv.set(x, y, col)


def recess(cv: Canvas, pts, depth: int = 2, k: int = 1):
    """The inside of a frame: its top rows and left columns fall in the frame's shadow
    (light from the upper left)."""
    pts = set(pts)
    for (x, y) in pts:
        d = min(next((i for i in range(1, depth + 1) if (x, y - i) not in pts), depth + 1),
                next((i for i in range(1, depth + 1) if (x - i, y) not in pts), depth + 1))
        if d <= depth:
            shade(cv, x, y, k + (1 if d == 1 and depth > 1 else 0))


def overhang_shadow(cv: Canvas, x0: int, x1: int, y: int, depth, k: int = 1, cap: int | None = None):
    """The band an overhang casts on the surface below it: `depth(x)` rows deep (deeper
    to the right, where the light falls), one tone darker again in its first row. With
    `cap`, every pixel in the band is also held at or below that ramp index, so a deep
    shadow reads as one calm band rather than stripes of the surface under it."""
    for x in range(x0, x1):
        d = depth(x) if callable(depth) else depth
        for i in range(d):
            yy = y + i
            c = cv.get(x, yy)
            hit = _LOOKUP.get(c[:3]) if c[3] else None
            if not hit:
                continue
            ramp, t = hit
            t -= k + (1 if i == 0 else 0)
            if cap is not None:
                t = min(t, cap - (1 if i == 0 else 0))
            cv.set(x, yy, tone(ramp, t))


def pebble(cv: Canvas, x: int, y: int, ramp, big: bool = False):
    """A small stone lying on the ground: lit top left, dark underside."""
    if big:
        cv.hline(x, y, 3, tone(ramp, 2)); cv.hline(x - 1, y + 1, 5, tone(ramp, 2))
        cv.set(x, y, tone(ramp, 4)); cv.set(x + 1, y, tone(ramp, 3)); cv.set(x - 1, y + 1, tone(ramp, 3))
        cv.hline(x, y + 2, 3, tone(ramp, 1))
    else:
        cv.set(x, y, tone(ramp, 3)); cv.set(x + 1, y, tone(ramp, 2))
        cv.hline(x, y + 1, 2, tone(ramp, 1))


# Grass tufts: small clumps of blades with dark roots and lit tips, in a few shapes so
# the meadow reads as grass rather than a stamp. 'd' root (two tones below the ground),
# 'm' blade (one below), 'l' tip (one above), 'L' bright tip (two above).
TUFTS = [
    ['l.l', 'm.m', '.d.'],
    ['.l..', 'l.l.', 'm.ml', '.dd.'],
    ['..l..', 'l.L.l', 'm.m.m', '.ddd.'],
    ['l.', 'ml', 'd.'],
    ['.l...l.', '.m.L.m.', 'm.dmd.m', '.ddddd.'],
    ['L..', 'm.l', 'dm.'],
]


def grass_tuft(cv: Canvas, x: int, y: int, kind: int, ramp, ground: int):
    """A tuft whose roots sit at (x, y) on grass of ramp index `ground`."""
    rows = TUFTS[kind % len(TUFTS)]
    h = len(rows)
    offs = {'d': -1 if ground <= 2 else -2, 'm': -1, 'l': 1, 'L': 2}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in offs:
                cv.set(x + c - len(row) // 2, y - (h - 1) + r, tone(ramp, ground + offs[ch]))


def cast(cv: Canvas, pts, dx: int = 1, dy: int = 1, k: int = 1, on=None, reach: int = 1):
    """Something standing in front of a surface casts a shadow onto it, offset down and
    to the right (light from the upper left), `reach` pixels long. Only pixels on the
    `on` ramp (the surface) are shaded, so neighbouring props are left alone."""
    pts = set(pts)
    done = set()
    on_rgb = {tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in on} if on else None
    for (x, y) in pts:
        for step in range(1, reach + 1):
            p = (x + dx * step, y + dy * step)
            if p in pts or p in done:
                continue
            c = cv.get(*p)
            if on_rgb is not None and c[:3] not in on_rgb:
                continue
            done.add(p)
            shade(cv, p[0], p[1], k)


# Light comes from the upper left and a little behind, so a shadow is the object's own
# silhouette thrown down and to the right along the ground: each pixel's height above
# the object's foot moves it SHADOW_RUN to the right and SHADOW_DROP down per pixel.
SHADOW_RUN, SHADOW_DROP = 0.45, 0.07


def silhouette_shadow(sprite: Canvas, x0: int, y0: int, foot: int | None = None) -> set:
    """The ground pixels a sprite standing at (x0, y0) shades: its silhouette thrown down
    and to the right from its foot (its bottom row unless `foot` is given). A tall house
    throws a long, roof-shaped shadow, a post a thin line, a tree a canopy-shaped pool
    beside its trunk, which is what makes things stand up off the ground."""
    base = y0 + sprite.h - 1 if foot is None else foot
    pts = set()
    for sy in range(sprite.h):
        for sx in range(sprite.w):
            if not sprite.get(sx, sy)[3]:
                continue
            hgt = base - (y0 + sy)
            if hgt < 0:
                continue
            gx = x0 + sx + hgt * SHADOW_RUN
            gy = base + hgt * SHADOW_DROP
            pts.add((int(round(gx)), int(round(gy))))
            pts.add((int(round(gx)) + 1, int(round(gy))))
    return pts


def base_tufts(cv: Canvas, xs, y: int, ramp, ground: int = 3):
    """Grass growing in front of a base: small tufts with their roots on the sprite's
    bottom row, so posts and walls sit in the grass instead of ending on a hard line."""
    for i, x in enumerate(xs):
        grass_tuft(cv, x, y, (0, 3, 5)[i % 3], ramp, ground)
