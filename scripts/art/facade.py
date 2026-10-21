"""Facades at Eastward's level of detail: walls in courses, deep windows, the things people
fix to a building, and the weather on it (Claude C: the city, Cogsworth and the isles).

art-style.md, "Eastward's level of detail is required" (Matt, 20 Oct): per 16 x 16 px
patch at the same character height our facades must carry as many tones, shapes and
dressing pieces as Eastward's town fronts (detail_bar.py --kind facade), and stay clean:
detail in clusters of two or more pixels, never single-pixel speckle. So every surface
here is built from small whole pieces, each lit from the upper left:

- walls in courses: brick in running bond (each brick its own fired tone, its top course
  catching the light, a shadowed mortar bed under it), glazed tile, precast panels with
  their board marks and joints, render with its patched and stained areas, dressed ashlar;
- windows set in a reveal: a stone lintel, a painted frame lit on its top and west side,
  glass that reflects the sky above and shows the room below (curtains, a lamp, a plant,
  blinds), a sill that casts its shadow and the rain streaks under its ends;
- what people fix to a wall: downpipes on brackets with their hoppers, air conditioners
  with their grilles and drips, vents, cable runs on clips, flower boxes, awnings,
  shutters, security bars, meter boxes and posters;
- weather: soot under every ledge and cornice in blotches, damp at the foot, grime in
  clusters, and the east end of a front a step darker than the west.

Colours step with `step`, a stride wide enough to survive the bar's 16-level colour
quantisation, so a shade is a tone the eye (and the count) can tell apart.
"""
from __future__ import annotations

from pixel import Canvas, noise2, smooth_noise

WARM = ['#4A2A08', '#9A5A10', '#E8962A', '#FFC766', '#FFE9B0']   # lamplit rooms
COOL = ['#0C2A3A', '#11506A', '#1F8AA8', '#6FD0E6', '#C8F4FF']   # screens and offices
METAL = ['#1A1E26', '#2A303C', '#3C4452', '#56606E', '#76808E', '#A0A8B4']
STONE_T = ['#2C2A30', '#46424A', '#615C64', '#7E7880', '#A29BA0', '#C8C0BE']  # lintels, sills, bands
SKY = ['#141A30', '#22304E', '#34507A', '#5478A6', '#8AACD0']    # the dusk sky in a pane
FABRIC = (['#3A1820', '#6A2A36', '#9A4450', '#C46A70'],            # curtains: wine,
          ['#1E2A3A', '#2E4462', '#4A6A90', '#7494B8'],            # blue,
          ['#3A3418', '#6A5A26', '#9A8440', '#C8B062'],            # ochre,
          ['#1E3428', '#2E5440', '#4A7A5C', '#74A482'])            # green
LEAF = ['#16281C', '#24402A', '#36603A', '#4E844C', '#78AE62']
BLOOM = ('#D8506A', '#E8A040', '#E8E0D0', '#B070C8')
POSTER = (('#C8463A', '#E8D8B0', '#2A2A3A'), ('#3A78B8', '#F0E8D0', '#E8A030'),
          ('#2E7A5A', '#E8E0C8', '#C83A5A'), ('#E8B83A', '#2A2A3A', '#C8463A'))


def rgb(c):
    if isinstance(c, str):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    return tuple(c[:3])


def hexs(t) -> str:
    return '#%02X%02X%02X' % tuple(max(0, min(255, int(v))) for v in t[:3])


def step(c, k: float) -> str:
    """A colour k steps darker (k > 0) or lighter (k < 0); a step is about 16 % of the way
    to black or to white, wide enough to read as its own tone after quantisation."""
    r = rgb(c)
    if k >= 0:
        f = (1 - 0.16) ** k
        return hexs(tuple(v * f for v in r))
    f = 1 - (1 - 0.16) ** -k
    return hexs(tuple(v + (255 - v) * f for v in r))


def mix(a, b, t: float) -> str:
    a, b = rgb(a), rgb(b)
    return hexs(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def darken(cv: Canvas, x: int, y: int, k: float = 1, clip=None):
    """Step the pixel already there k steps darker (a shadow or a stain on it)."""
    if clip and not (clip[0] <= x < clip[1] and clip[2] <= y < clip[3]):
        return
    c = cv.get(x, y)
    if c[3]:
        cv.set(x, y, step(c, k))


def guard(cv: Canvas, x0: int, x1: int, y0: int, y1: int):
    """Remember the pixels beside a facade (west of x0, east of x1 - 1, rows y0 - 4 to
    y1 + 8) and return a function that puts them back, so fixtures near a front's end never
    spill past the building's own sides."""
    keep = {}
    for y in range(y0 - 4, y1 + 8):
        for x in list(range(x0 - 8, x0)) + list(range(x1, x1 + 8)):
            keep[(x, y)] = cv.get(x, y)

    def restore():
        p = cv.pad
        for (x, y), c in keep.items():
            if -p <= x < cv.w + p and -p <= y < cv.h + p:
                cv.img.putpixel((x + p, y + p), c)
    return restore


def _box(cv, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            cv.set(x, y, c)


# ---- walls ------------------------------------------------------------------------------

def wall(cv: Canvas, x0: int, x1: int, y0: int, y1: int, kind: str, ramp, seed: int = 0,
         mortar=None, soot: bool = True):
    """A wall face from (x0, y0) to (x1, y1), in courses of its material, weathered.
    ramp: the material, dark to light (at least five tones)."""
    r = list(ramp)
    mortar = mortar or [mix(r[1], '#8A8890', 0.35), mix(r[2], '#B0ACA8', 0.45)]
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = _course(x - x0, y - y0, kind, r, mortar, seed)
            if soot:  # grime by whole bricks, tiles and blocks, so it stays in clusters
                cx, cy = _cell(x - x0, y - y0, kind)
                n = smooth_noise(cx * 1.0, cy * 0.6, 5, 3150 + seed)
                foot = (y - y0) / max(1, y1 - y0)
                if n > 0.72 - 0.08 * foot:
                    c = step(c, 0.8 if n < 0.8 else 1.4)
            cv.set(x, y, c)


def _cell(u: int, v: int, kind: str):
    """The middle of the brick, tile or block a pixel belongs to (the whole of it weathers
    alike); smooth walls weather pixel by pixel."""
    if kind == 'brick':
        row = v // 3
        off = 2 if row % 2 else 0
        return ((u + off) // 5) * 5 - off + 2, row * 3 + 1
    if kind == 'tile':
        row = v // 4
        off = 2 if row % 2 else 0
        return ((u + off) // 5) * 5 - off + 2, row * 4 + 1
    if kind == 'ashlar':
        row = v // 5
        return (u // 8) * 8 + 4, row * 5 + 2
    return (u // 2) * 2, (v // 2) * 2


def _course(u: int, v: int, kind: str, r, mortar, seed: int) -> str:
    if kind == 'brick':  # running bond: a brick 4 x 2, its mortar joint and bed 1 px
        row, rv = divmod(v, 3)
        off = 2 if row % 2 else 0
        col, ru = divmod(u + off, 5)
        if rv == 2 or ru == 4:
            return mortar[0]  # the bed and the joints, one run of mortar
        n = noise2(col, row, 3100 + seed)
        c = r[3] if n < 0.42 else r[2] if n < 0.6 else r[4] if n < 0.74 else mix(r[3], '#2A2030', 0.35) if n < 0.86 \
            else mix(r[3], '#D8B080', 0.3)
        if rv == 0 and noise2(col, row, 3101 + seed) > 0.45:
            c = step(c, -1)  # the brick's top arris catching the light
        return c
    if kind == 'tile':  # glazed tile 4 x 3 in a grout grid, the glossier ones lit along the top
        row, rv = divmod(v, 4)
        col, ru = divmod(u + (2 if row % 2 else 0), 5)
        if rv == 3 or ru == 4:
            return mortar[0]
        n = noise2(col, row, 3110 + seed)
        c = r[3] if n < 0.5 else r[2] if n < 0.72 else r[4] if n < 0.88 else mix(r[3], '#E8E0D0', 0.25)
        if rv == 0 and noise2(col, row, 3111 + seed) > 0.5:
            c = step(c, -1.2)
        return c
    if kind == 'panel':  # precast concrete: panels with joints, board marks in each
        pw = 16 + int(noise2(seed, 7, 3120) * 3) * 4
        col, ru = divmod(u, pw)
        if v % 32 in (0, 1) or ru == 0:
            return r[1] if v % 32 == 1 or ru == 0 else r[4]  # the joint: a lit lip, then its shadow
        n = noise2(col, v // 32, 3121 + seed)
        base = r[3] if n < 0.3 else r[2] if n < 0.55 else mix(r[3], '#C8B8A0', 0.22) if n < 0.75 else \
            mix(r[3], '#7A90B0', 0.2) if n < 0.9 else r[4]
        vv = v % 32
        if ru in (2, 3) and vv in (3, 4):
            return '#9A98A0' if vv == 3 else '#4A4850'  # a fixing bolt
        if ru in (2, 3) and 5 <= vv < 5 + int(noise2(col, v // 32, 3125 + seed) * 9):
            return mix(base, '#8A4A2A', 0.4 if ru == 2 else 0.25)  # the rust run from it
        row, rv = divmod(v, 3)
        seg = (u + noise2(row, col, 3122 + seed) * 9) // (4 + int(noise2(row, 5, 3123 + seed) * 5))
        mark = noise2(int(seg), row, 3124 + seed)
        if rv == 0 and mark > 0.55:
            return step(base, -0.8)  # a board's lit edge
        if rv == 2 and mark < 0.3:
            return step(base, 0.8)
        return base
    if kind == 'render':  # stucco: worn into patches, with the odd repair
        n = smooth_noise(u, v, 6, 3130 + seed)
        m = smooth_noise(u + 40, v, 3, 3131 + seed)
        c = r[3] if n < 0.45 else r[4] if n < 0.62 else r[2] if n > 0.74 else mix(r[3], r[4], 0.5)
        if m > 0.72:
            c = step(c, 0.7)
        return c
    if kind == 'ashlar':  # dressed stone: blocks 7 x 4 in courses, lit top and west
        row, rv = divmod(v, 5)
        off = 4 if row % 2 else 0
        bw = 7 + (row % 3 == 1)
        col, ru = divmod(u + off, bw + 1)
        if rv == 4 or ru == bw:
            return mortar[0]
        n = noise2(col, row, 3140 + seed)
        c = r[3] if n < 0.45 else r[2] if n < 0.65 else r[4] if n < 0.85 else mix(r[3], '#7A8A5A', 0.25)
        if rv == 0:
            c = step(c, -1)
        elif rv == 3 or ru == bw - 1:
            c = step(c, 0.9)
        return c
    return r[3]


def weather(cv: Canvas, x0: int, x1: int, y0: int, y1: int, seed: int, amount: float = 1.0):
    """Grime in clusters (never single pixels): blotches where water runs and soot settles,
    heavier toward the foot."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            n = smooth_noise(x * 1.0, y * 0.6, 5, 3150 + seed)
            foot = (y - y0) / max(1, y1 - y0)
            if n > 0.74 - 0.08 * foot * amount:
                darken(cv, x, y, 0.8 if n < 0.82 else 1.4)


def soot_band(cv: Canvas, x0: int, x1: int, y: int, seed: int, depth: int = 3):
    """The dark drip under a ledge: a strip darkest at the top, ragged in runs below."""
    for x in range(x0, x1):
        run = 1 + int(noise2(x // 2, y, 3160 + seed) * depth)
        for d in range(run):
            darken(cv, x, y + d, 1.5 if d == 0 else 0.8)


def ledge(cv: Canvas, x0: int, x1: int, y: int, ramp=STONE_T, seed: int = 0, deep: bool = False):
    """A string course or cornice: a lit top, its face in blocks, its shadow and soot under."""
    for x in range(x0, x1):
        blk = (x - x0 + seed) // 9
        n = noise2(blk, y, 3170 + seed)
        cv.set(x, y, ramp[5] if n > 0.3 else ramp[4])
        cv.set(x, y + 1, ramp[3] if (x - x0 + seed) % 9 else ramp[2])
        if deep:
            cv.set(x, y + 2, ramp[2] if n > 0.5 else ramp[1])
    soot_band(cv, x0, x1, y + (3 if deep else 2), seed)


def east_shade(cv: Canvas, x0: int, x1: int, y0: int, y1: int):
    """The light comes from the upper left: the front's east end a step darker, its corner
    darker still, its west arris lit."""
    for y in range(y0, y1):
        darken(cv, x1 - 1, y, 1.6)
        darken(cv, x1 - 2, y, 1.6)
        c = cv.get(x0, y)
        if c[3]:
            cv.set(x0, y, step(c, -1))


# ---- windows ----------------------------------------------------------------------------

def window(cv: Canvas, x: int, y: int, w: int, h: int, wall_c, lit=None, seed: int = 0,
           frame=None, bars: str = 'sash', lintel: str = 'stone', sill_ramp=STONE_T, room: bool = True,
           extras: bool = True):
    """A window in its reveal, w x h overall (the frame included). lit: None (a dark room
    reflecting the dusk), WARM or COOL. bars: 'sash', 'casement', 'grid' or 'none'."""
    frame = frame or ['#2A2630', '#5A5460', '#9A949C', '#D8D2D0']
    fab = FABRIC[int(noise2(seed, 1, 3200) * len(FABRIC))]
    # the lintel over the reveal
    if lintel == 'stone':
        for xx in range(x - 1, x + w + 1):
            cv.set(xx, y - 2, sill_ramp[5] if xx < x + w else sill_ramp[4])
            cv.set(xx, y - 1, sill_ramp[3] if (xx - x) % 5 else sill_ramp[2])
    elif lintel == 'soldier':  # a course of bricks on end
        for xx in range(x - 1, x + w + 1):
            k = (xx - x + 1) // 2
            c = (wall_c[3], wall_c[4], wall_c[2])[int(noise2(k, y, 3201) * 3)] if isinstance(wall_c, list) else wall_c
            cv.set(xx, y - 3, step(c, -1)); cv.set(xx, y - 2, c)
            cv.set(xx, y - 1, step(c, 0.6) if (xx - x + 1) % 2 else c)
    # the frame: lit on its top and west side
    for xx in range(x, x + w):
        cv.set(xx, y, frame[3]); cv.set(xx, y + h - 1, frame[1])
    for yy in range(y, y + h):
        cv.set(x, yy, frame[3] if yy < y + h - 1 else frame[2]); cv.set(x + w - 1, yy, frame[1])
    gx0, gx1, gy0, gy1 = x + 1, x + w - 1, y + 1, y + h - 1
    mid = gy0 + (gy1 - gy0) * 2 // 5
    for yy in range(gy0, gy1):
        for xx in range(gx0, gx1):
            u, v = xx - gx0, yy - gy0
            gw = gx1 - gx0
            if lit is None:
                if yy < mid:  # the upper pane reflects the dusk sky, a glint across it
                    d = (u + v) % 11
                    c = SKY[4] if d in (3, 4) and u > 0 else SKY[3] if d in (2, 5) else SKY[2] if v < 2 else SKY[1]
                else:  # the dark room: curtains each side, a shape or two inside
                    c = '#14121E' if v > mid - gy0 + 3 else '#1C1A2A'
                    if room:
                        if u < 2 or u >= gw - 2:
                            c = fab[1] if (u in (0, gw - 1)) else fab[0]
                        elif noise2(seed, 4, 3202) > 0.5 and gw // 2 - 1 <= u <= gw // 2 and yy >= gy1 - 4:
                            c = '#2A2838'  # a chair back
            else:
                if yy < mid:
                    c = lit[3] if v < 1 else lit[2] if (u + v) % 9 not in (4, 5) else lit[3]
                else:
                    depth_ = (yy - mid) / max(1, gy1 - mid)
                    c = lit[2] if depth_ < 0.5 else step(lit[2], 0.8)
                    if room:
                        if u < 2 or u >= gw - 2:
                            c = step(fab[3], -0.3) if u in (0, gw - 1) else fab[2]
            cv.set(xx, yy, c)
    gw, gh = gx1 - gx0, gy1 - gy0
    if lit is not None and room and gw >= 6:
        k = int(noise2(seed, 5, 3203) * 3)
        if k == 0:  # a lamp: its shade lit, its stand
            lx = gx0 + 2 + int(noise2(seed, 6, 3204) * max(1, gw - 6))
            _box(cv, lx, mid + 1, lx + 3, mid + 3, lit[4])
            cv.set(lx + 1, mid + 3, lit[1]); cv.set(lx + 1, mid + 4, lit[1])
        elif k == 1:  # a plant on the inside sill
            px = gx0 + 2 + int(noise2(seed, 6, 3205) * max(1, gw - 6))
            _box(cv, px, gy1 - 4, px + 3, gy1 - 2, LEAF[2]); _box(cv, px + 1, gy1 - 5, px + 3, gy1 - 4, LEAF[3])
            _box(cv, px, gy1 - 2, px + 3, gy1, '#6A3A24')
        else:  # a figure at the window, against the light
            px = gx0 + 2 + int(noise2(seed, 6, 3206) * max(1, gw - 6))
            _box(cv, px, mid + 1, px + 2, mid + 3, step(lit[1], 0.5))
            _box(cv, px - 1, mid + 3, px + 3, gy1, step(lit[1], 0.5))
    if lit is not None and noise2(seed, 7, 3207) > 0.6:  # a blind half down
        for yy in range(gy0, mid):
            for xx in range(gx0, gx1):
                cv.set(xx, yy, '#E8D8B0' if (yy - gy0) % 2 == 0 else '#B8A480')
    # glazing bars
    if bars in ('sash', 'grid'):
        for xx in range(gx0, gx1):
            cv.set(xx, mid, frame[2]); cv.set(xx, mid + 1, frame[1])
    if bars in ('casement', 'grid') and gw >= 6:
        for yy in range(gy0, gy1):
            cv.set(gx0 + gw // 2, yy, frame[2])
    # the reveal's shade inside the frame's top and west edges
    for xx in range(gx0, gx1):
        darken(cv, xx, gy0, 1)
    for yy in range(gy0 + 1, gy1):
        darken(cv, gx0, yy, 1)
    # the sill: lit top, dark nose, its shadow on the wall and streaks under its ends
    sy = y + h
    for xx in range(x - 1, x + w + 1):
        cv.set(xx, sy, sill_ramp[5] if xx < x + w - 1 else sill_ramp[4])
        cv.set(xx, sy + 1, sill_ramp[2])
    for xx in range(x, x + w + 2):
        darken(cv, xx, sy + 2, 1.6)
    darken(cv, x + w + 1, sy + 1, 1.6)
    for ex in (x, x + w - 2):
        ln = 2 + int(noise2(ex, sy, 3208 + seed) * 5)
        for d in range(ln):
            darken(cv, ex, sy + 3 + d, 0.8); darken(cv, ex + 1, sy + 3 + d, 0.8)
    if not extras:
        return
    pick = noise2(seed, 8, 3209)
    if pick > 0.72 and w >= 8:  # a flower box on the sill
        for xx in range(x, x + w):
            cv.set(xx, sy - 1, '#6A3A24'); cv.set(xx, sy, '#8A5234')
            cv.set(xx, sy + 1, '#4A2818')
            if (xx - x) % 3 != 2:
                cv.set(xx, sy - 2, LEAF[2] if (xx - x) % 3 == 0 else LEAF[3])
                cv.set(xx, sy - 3, LEAF[1] if (xx + seed) % 2 else LEAF[3])
        for k in range(0, w - 2, 4):
            b = BLOOM[int(noise2(seed, k, 3210) * len(BLOOM))]
            cv.set(x + 1 + k, sy - 3, b); cv.set(x + 2 + k, sy - 3, b)
    elif pick > 0.5:  # shutters folded back, slatted
        sh = FABRIC[int(noise2(seed, 9, 3211) * len(FABRIC))]
        for side in (x - 4, x + w + 1):
            for yy in range(y, y + h):
                for xx in range(side, side + 3):
                    c = sh[2] if (yy - y) % 2 == 0 else sh[1]
                    if xx == side:
                        c = sh[3] if side < x else sh[1]
                    cv.set(xx, yy, c)
            for yy in range(y + 1, y + h + 1):
                darken(cv, side + 3, yy, 1.4)


def awning(cv: Canvas, x0: int, x1: int, y: int, ramp, depth: int = 5):
    """A striped canvas awning sloping out toward us: lit on its slope, a scalloped
    valance, and its shadow over whatever is under it."""
    for yy in range(y, y + depth):
        for xx in range(x0, x1):
            st = ((xx - x0) // 3) % 2
            top = yy - y < depth - 2
            c = (ramp[3] if st else '#E8E0D0') if top else (ramp[2] if st else '#B8B0A8')
            if yy == y:
                c = step(c, -0.8)
            cv.set(xx, yy, c)
    for xx in range(x0, x1):
        if (xx - x0) % 3 != 2:
            cv.set(xx, y + depth, ramp[1] if ((xx - x0) // 3) % 2 else '#8A8078')
        for d in (1, 2):
            darken(cv, xx + 1, y + depth + d, 1.2 if d == 1 else 0.7)


# ---- fixtures ---------------------------------------------------------------------------

def downpipe(cv: Canvas, x: int, y0: int, y1: int, ramp=METAL, seed: int = 0):
    """A rainwater pipe: a hopper at the top, brackets every few courses, lit on its west
    side, its shadow beside it, a damp streak at its shoe."""
    _box(cv, x - 1, y0, x + 3, y0 + 3, ramp[3])
    for xx in range(x - 1, x + 3):
        cv.set(xx, y0, ramp[5]); cv.set(xx, y0 + 3, ramp[1])
    for yy in range(y0 + 3, y1):
        cv.set(x, yy, ramp[4]); cv.set(x + 1, yy, ramp[2])
        darken(cv, x + 2, yy, 1.5)
        if (yy - y0) % 9 == 4:
            for xx in range(x - 1, x + 3):
                cv.set(xx, yy, ramp[1] if xx > x else ramp[3])
    for d in range(4):
        darken(cv, x - 1, y1 - 1 - d, 0.8); darken(cv, x + 2, y1 - 1 - d, 0.8)


def ac_unit(cv: Canvas, x: int, y: int, ramp=METAL, seed: int = 0):
    """An air conditioner on brackets: a lit lid, grille rows, its fan, a dark belly,
    its shadow down to the right and a rust drip below."""
    w, h = 9, 6
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            r = yy - y
            c = ramp[5] if r == 0 else ramp[1] if r == h - 1 else (ramp[3] if r % 2 else ramp[4])
            if xx == x + w - 1 and 0 < r < h - 1:
                c = ramp[2]
            cv.set(xx, yy, c)
    _box(cv, x + 5, y + 1, x + 8, y + 5, ramp[1])
    cv.set(x + 6, y + 2, ramp[3]); cv.set(x + 6, y + 3, ramp[3])
    cv.set(x + 1, y + h, ramp[2]); cv.set(x + w - 2, y + h, ramp[2])
    for xx in range(x + 1, x + w + 1):
        darken(cv, xx, y + h + 1, 1.4)
    for yy in range(y + 1, y + h + 1):
        darken(cv, x + w, yy, 1.4)
    for d in range(2 + int(noise2(x, y, 3220 + seed) * 4)):
        cv.set(x + 2, y + h + 2 + d, mix(cv.get(x + 2, y + h + 2 + d), '#8A4A2A', 0.45))
        cv.set(x + 3, y + h + 2 + d, mix(cv.get(x + 3, y + h + 2 + d), '#8A4A2A', 0.3))


def vent(cv: Canvas, x: int, y: int, ramp=METAL):
    """A louvred vent: a frame and three slats, lit from above."""
    for yy in range(y, y + 5):
        for xx in range(x, x + 5):
            c = ramp[4] if yy == y or xx == x else ramp[1] if yy == y + 4 or xx == x + 4 else \
                (ramp[3] if (yy - y) % 2 else ramp[1])
            cv.set(xx, yy, c)
    for yy in range(y + 1, y + 6):
        darken(cv, x + 5, yy, 1.3)


def cable(cv: Canvas, x0: int, x1: int, y: int, sag: int = 2, color='#1A1820', seed: int = 0):
    """A cable run clipped along a wall, sagging between its clips in steps of 2 px or more."""
    span = 12 + int(noise2(x0, y, 3230 + seed) * 8)
    for xx in range(x0, x1):
        t = ((xx - x0) % span) / span
        d = round(sag * 4 * t * (1 - t))
        cv.set(xx, y + d, color)
        if (xx - x0) % span == 0:
            cv.set(xx, y - 1, '#8A8890'); cv.set(xx + 1, y - 1, '#8A8890')


def meter_box(cv: Canvas, x: int, y: int):
    """A grey meter cabinet with its little window and a pipe down from it."""
    for yy in range(y, y + 8):
        for xx in range(x, x + 6):
            c = '#8A8E96' if yy == y or xx == x else '#3A3E46' if xx == x + 5 or yy == y + 7 else '#5E626C'
            cv.set(xx, yy, c)
    _box(cv, x + 2, y + 2, x + 4, y + 4, '#C8E0D8')
    for yy in range(y + 1, y + 9):
        darken(cv, x + 6, yy, 1.4)


def poster(cv: Canvas, x: int, y: int, w: int = 5, h: int = 7, seed: int = 0):
    """A poster pasted on a wall: a field, a block of image, glyph lines, a torn corner."""
    a, b, c = POSTER[int(noise2(x, y, 3240 + seed) * len(POSTER))]
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            r = yy - y
            col = a if r < h // 2 else b
            if r >= h // 2 + 1 and (xx - x) % 4 != 3 and r % 2 == 0:
                col = c
            cv.set(xx, yy, col)
    cv.set(x + w - 1, y + h - 1, step(b, 1)); cv.set(x + w - 2, y + h - 1, step(b, 1))


def tag(cv: Canvas, x: int, y: int, seed: int = 0):
    """A painted tag: a few strokes 2 px wide (glyph-like, never words)."""
    col = ('#C83A8A', '#3AA8C8', '#E8C03A', '#E8E8E8')[int(noise2(x, y, 3250 + seed) * 4)]
    for k in range(3):
        n = noise2(k, seed, 3251)
        xx, yy = x + k * 3, y + int(n * 3)
        for d in range(2 + int(n * 3)):
            cv.set(xx, yy + d, col); cv.set(xx + 1, yy + d, col)
    for d in range(8):
        cv.set(x + d, y + 5, col)


def bird(cv: Canvas, x: int, y: int):
    """A pigeon on a ledge: a grey body, a lighter head."""
    cv.set(x, y, '#6A6870'); cv.set(x + 1, y, '#6A6870'); cv.set(x + 2, y, '#6A6870')
    cv.set(x, y - 1, '#9A98A0'); cv.set(x + 1, y - 1, '#9A98A0')


def curtain_wall(cv: Canvas, x0: int, x1: int, y0: int, y1: int, ramp, seed: int = 0, floor: int = 32,
                 mull: int = 12):
    """A glass curtain wall, floor by floor: a louvred spandrel lit on its top edge, mullions
    lit on their west face, a transom, and panes that each show something: the dusk sky with
    a cloud, the street's skyline mirrored with its lit windows, a glint running across on a
    slant, or an office behind (its ceiling lights, desks and screens, a plant, someone at
    work), or blinds drawn."""
    for y in range(y0, y1):
        f = (y1 - 1 - y) // floor
        fy = y1 - (f + 1) * floor
        r = y - fy
        for x in range(x0, x1):
            u = x - x0
            col, pane = u % mull, u // mull
            if r < 6:  # the spandrel
                c = METAL[4] if r == 0 else METAL[1] if r == 5 else (METAL[3] if r % 2 else METAL[2])
                if r in (2, 3) and col in (mull // 2, mull // 2 + 1):
                    c = METAL[5] if r == 2 else METAL[1]  # a bolt head
            elif col == 0:
                c = METAL[4]
            elif col == 1:
                c = METAL[2]
            elif r == 19:
                c = METAL[3]
            else:
                c = _pane(u, r, col, pane, f, ramp, seed, mull, x, y)
            cv.set(x, y, c)


def _office(r, col, mull, L, dim: bool):
    """What is behind a pane: a ceiling with its light strips, the back wall, a desk with a
    screen, a chair, someone at work, a plant in its pot, a bookcase."""
    if r in (7, 8):
        c = L[4] if col % 4 in (2, 3) else L[1]
    elif r == 9:
        c = step(L[2], -0.6) if col % 4 in (1, 2, 3, 4) else L[2]
    elif 3 <= col <= 4 and 18 <= r <= 26:
        c = '#0A1418' if r > 20 else '#3A2A2A'  # someone at work
    elif col >= mull - 3 and r >= 24:
        c = (LEAF[3] if (col + r) % 2 else LEAF[2]) if r < 29 else '#3A2418'  # a plant in a pot
    elif 23 <= r <= 25 and 6 <= col <= mull - 4:
        c = COOL[3] if r == 23 and col % 3 else '#2A303C' if r > 23 else '#56606E'  # a desk, a screen
    elif r > 26:
        c = '#24160E' if col % 6 in (0, 1) else step(L[1], 0.6)
    elif col >= mull - 4 and 12 <= r < 24:
        c = '#5A3A2A' if r % 3 else '#7A4E34'  # a bookcase
    else:
        c = L[3] if r < 13 else L[2] if r < 20 else step(L[2], 0.6)
    return step(c, 2.5) if dim else c


def _pane(u, r, col, pane, f, ramp, seed, mull, x, y):
    mode = noise2(pane, f * 2 + (r > 19), 3300 + seed)
    if mode > 0.8:  # an office lit warm
        return _office(r, col, mull, WARM, False)
    if mode > 0.7:  # an office lit cool
        return _office(r, col, mull, COOL, False)
    if mode > 0.64:  # blinds, one slat lit in two
        return '#C8B898' if r % 2 == 0 else '#8A7C68'
    # reflections over a dark office: each pane its own tilt of the sky
    tilt = noise2(pane, f, 3305 + seed)
    rr = [step(c, 1) for c in ramp] if tilt < 0.25 else [step(c, -1) for c in ramp] if tilt > 0.8 else \
        [mix(c, '#6A4A8A', 0.25) for c in ramp] if tilt > 0.6 else list(ramp)
    inside = _office(r, col, mull, (WARM, COOL)[pane % 2], True)
    sky = 7 + int(smooth_noise(x, 0, 9, 3310 + seed) * 10)
    line = 12 - int(smooth_noise(x, 1, 7, 3311 + seed) * 10)
    if r >= 20 and (r - 20) > line:
        # the street's skyline in the glass, with its lit windows and a sign's glow
        if r % 4 == 1 and col % 4 in (2, 3) and noise2(x // 4, r // 4 + f * 9, 3312 + seed) > 0.55:
            return WARM[2] if noise2(x // 4, r, 3314 + seed) > 0.3 else COOL[3]
        return rr[0] if (r - 20) > line + 1 else mix(rr[0], rr[1], 0.5)
    d = (u + y) % 37
    if d in (0, 1, 2):
        return rr[4]
    if d == 3:
        return rr[5] if len(rr) > 5 else rr[4]
    if r < sky and smooth_noise(x, y, 4, 3313 + seed) > 0.58:
        return mix(rr[3], '#C8A8C0', 0.35 if smooth_noise(x, y, 4, 3313 + seed) < 0.66 else 0.6)  # a cloud
    if 10 <= r < 14 and noise2(pane, f, 3315 + seed) > 0.7:
        return mix(rr[2], ('#E85AA0', '#4AD0E8')[pane % 2], 0.4)  # a neon sign across the street
    refl = rr[3] if r < 10 else rr[2] if r < 16 else mix(rr[2], rr[1], 0.5) if r < 24 else rr[1]
    return mix(refl, inside, 0.45)


# ---- signs ------------------------------------------------------------------------------

_STROKES = (((0, 0), (3, 0)), ((0, 2), (3, 2)), ((0, 4), (3, 4)), ((0, 0), (0, 4)), ((3, 0), (3, 4)),
            ((1, 0), (1, 4)), ((0, 0), (0, 2)), ((3, 2), (3, 4)), ((0, 2), (0, 4)), ((3, 0), (3, 2)))


def tube_glyph(cv: Canvas, x: int, y: int, seed: int, color, h: int = 5) -> set:
    """A sign glyph bent from neon tube: three straight strokes on a 4 x 5 grid, never a
    lone pixel and never real lettering. Returns its pixels."""
    pts = set()
    for k in range(3):
        (a, b), (c, d) = _STROKES[int(noise2(seed, k, 3400) * len(_STROKES))]
        b, d = b * (h - 1) // 4, d * (h - 1) // 4
        for t in range(max(abs(c - a), abs(d - b)) + 1):
            pts.add((x + a + (c - a > 0) * t, y + b + (d - b > 0) * t))
    for p in pts:
        cv.set(p[0], p[1], color)
    return pts


def sign_box(cv: Canvas, x0: int, y0: int, x1: int, y1: int, ramp, seed: int, vertical: bool = False,
             face='#0E0C16'):
    """A lit sign with depth: a box whose top edge catches the light and whose east side
    and underside are in shade, a frame of tube round its face, glyphs inside with a halo
    on the face only, its brackets and its shadow on the wall."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            cv.set(x, y, face)
    for x in range(x0, x1):
        cv.set(x, y0, '#8A8698'); cv.set(x, y1 - 1, '#24202E')
    for y in range(y0, y1):
        cv.set(x1 - 1, y, '#24202E'); cv.set(x1 - 2, y, '#3A3646')
    tubes = set()
    if vertical:
        for x in range(x0 + 1, x1 - 2):
            tubes |= {(x, y0 + 1), (x, y1 - 2)}
    for y in range(y0 + 1, y1 - 1):
        tubes |= {(x0 + 1, y), (x1 - 3, y)}
    for p in tubes:
        cv.set(p[0], p[1], ramp[2])
    glyphs = set()
    if vertical:
        for k, gy in enumerate(range(y0 + 3, y1 - 8, 7)):
            glyphs |= tube_glyph(cv, x0 + (x1 - x0 - 4) // 2 - 1, gy, seed * 11 + k, ramp[3])
    else:
        gh = min(5, y1 - y0 - 2)
        for k, gx in enumerate(range(x0 + 4, x1 - 8, 6)):
            if noise2(seed, k, 3401) > 0.2:
                glyphs |= tube_glyph(cv, gx, y0 + 1, seed * 7 + k, ramp[3], h=gh)
    lit = tubes | glyphs
    for y in range(y0 + 1, y1 - 1):  # the halo, on the sign's own face
        for x in range(x0 + 2, x1 - 3):
            if (x, y) not in lit and any((x + dx, y + dy) in glyphs for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                cv.set(x, y, mix(face, ramp[1], 0.7))
    for (x, y) in glyphs:
        if (x - 1, y) in glyphs and (x + 1, y) in glyphs and noise2(x, y, 3402) > 0.6:
            cv.set(x, y, ramp[4] if len(ramp) > 4 else ramp[3])
    for y in range(y0 + 1, y1 + 1):  # its shadow on the wall
        darken(cv, x1, y, 1.6)
    for x in range(x0 + 1, x1 + 1):
        darken(cv, x, y1, 1.6)
    return lit


def wall_lamp(cv: Canvas, x: int, y: int, light=WARM):
    """A lamp on a bracket: a dark cap, a lit glass, the warm pool it throws on the wall
    round it (two rings, so it reads as light, not as a hole)."""
    for dy in range(-4, 7):
        for dx in range(-4, 7):
            d = (dx - 1) ** 2 + (dy - 1) ** 2
            if d <= 30:
                c = cv.get(x + dx, y + dy)
                if c[3]:
                    cv.set(x + dx, y + dy, mix(c, light[2], 0.38 if d <= 12 else 0.2))
    cv.set(x - 1, y - 1, '#2A2630'); cv.set(x, y - 1, '#2A2630'); cv.set(x + 1, y - 1, '#2A2630')
    for dy in range(3):
        for dx in range(3):
            cv.set(x + dx - 1 + 1, y + dy, light[4] if dy < 2 else light[3])
    cv.set(x - 2, y + 1, '#2A2630'); cv.set(x - 1, y + 1, '#2A2630')


def plaque(cv: Canvas, x: int, y: int, color='#2E5A9A'):
    """An enamel house number: a white rim and a number in two strokes."""
    for yy in range(y, y + 4):
        for xx in range(x, x + 5):
            cv.set(xx, yy, '#E8E4DC' if yy in (y, y + 3) or xx in (x, x + 4) else color)
    cv.set(x + 2, y + 1, '#E8E4DC'); cv.set(x + 2, y + 2, '#E8E4DC')
    for yy in range(y + 1, y + 5):
        darken(cv, x + 5, yy, 1.4)


GOODS = {
    'grocer': ('#C8463A', '#E8A040', '#8AC050', '#E8D850', '#6A3A8A', '#E87050'),
    'books': ('#8A2A2A', '#2E4A7A', '#2A6A4A', '#C8A040', '#6A4A8A', '#D8D0C0'),
    'bottles': ('#2E6A4A', '#8A5A20', '#C8D8C8', '#6A1A2A', '#3A8AA0', '#E8C060'),
    'gadgets': ('#1F8AA8', '#6FD0E6', '#2A303C', '#A0A8B4', '#E85AA0', '#E8E4DC'),
    'flowers': ('#D8506A', '#E8A040', '#E8E0D0', '#B070C8', '#4E844C', '#78AE62'),
}


def shop_window(cv: Canvas, x0: int, y0: int, x1: int, y1: int, seed: int, light=WARM):
    """A shop window's inside, as you see it from the pavement: a lit back wall lined with
    shelves on uprights, the shop's goods on them in their own colours (each lit along its
    top), hanging stock, the shopkeeper behind the counter, a display on the window bed,
    and the glass's glint laid over it all."""
    kind = tuple(GOODS)[int(noise2(seed, 1, 3500) * len(GOODS))]
    pal = GOODS[kind]
    wood = ['#2A1810', '#4A2C1C', '#6A4228', '#8A5A36', '#AA7A4C']
    for y in range(y0, y1):
        for x in range(x0, x1):
            v = y - y0
            c = light[3] if v < 3 else light[2] if v < (y1 - y0) * 2 // 3 else step(light[2], 0.6)
            if (x - x0) % 9 in (0, 1):
                c = wood[2] if (x - x0) % 9 == 0 else wood[1]  # the uprights
            cv.set(x, y, c)
    shelves = list(range(y0 + 6, y1 - 4, 5))
    for sy in shelves:
        for x in range(x0, x1):
            cv.set(x, sy, wood[3]); cv.set(x, sy + 1, wood[1])
        x = x0 + 2
        while x < x1 - 2:
            if (x - x0) % 9 in (0, 1):
                x += 1
                continue
            g = pal[int(noise2(x, sy, 3501 + seed) * len(pal))]
            tall = 2 + int(noise2(x, sy, 3502 + seed) * 3)
            wide = 2 + (noise2(x, sy, 3503 + seed) > 0.7)
            for d in range(tall):
                for e in range(wide):
                    if x + e < x1 and (x + e - x0) % 9 not in (0, 1):
                        cv.set(x + e, sy - 1 - d, step(g, -0.7) if d == tall - 1 else g if e < wide - 1 or wide == 2 and e == 0 else step(g, 0.7))
            x += wide + (1 if noise2(x, sy, 3504 + seed) > 0.4 else 0)
    if x1 - x0 >= 14 and noise2(seed, 2, 3500) > 0.35:  # the shopkeeper behind the counter
        kx = x0 + 4 + int(noise2(seed, 3, 3500) * (x1 - x0 - 10))
        top = y1 - 13
        for y in range(top, y1 - 4):
            for x in range(kx, kx + 4):
                c = '#E8B890' if y < top + 3 and kx < x < kx + 3 else '#3A2A2A' if y < top + 3 else \
                    ('#2E4A7A', '#8A2A2A', '#2A6A4A')[seed % 3]
                if y >= top + 3 and x == kx + 3:
                    c = step(c, 1)
                cv.set(x, y, c)
        cv.set(kx + 1, top - 1, '#3A2A2A'); cv.set(kx + 2, top - 1, '#3A2A2A')
    for x in range(x0, x1):  # the counter, the window bed with its display
        cv.set(x, y1 - 4, wood[4]); cv.set(x, y1 - 3, wood[3]); cv.set(x, y1 - 2, wood[2])
        cv.set(x, y1 - 1, wood[1])
    for k, x in enumerate(range(x0 + 2, x1 - 4, 7)):
        g = pal[int(noise2(k, 9, 3505 + seed) * len(pal))]
        for (dx, dy) in ((0, 0), (1, 0), (2, 0), (3, 0), (1, -1), (2, -1)):
            cv.set(x + dx, y1 - 5 + dy, step(g, -0.6) if dy < 0 else g)
    for y in range(y0, y1):  # the glint on the glass
        for x in range(x0, x1):
            if (x - x0 + y - y0) % 23 in (4, 5, 6):
                cv.set(x, y, mix(cv.get(x, y), '#FFF4D8', 0.45))


# ---- flat roofs seen from above -------------------------------------------------------

def roof(cv: Canvas, x0: int, x1: int, y0: int, y1: int, kind: str, ramp, seed: int = 0):
    """A flat roof's surface at Eastward's level of detail ('roof' on the bar): membrane laid
    in strips with lapped seams, its grit, repairs and ponded rain reflecting the sky; gravel
    in stones of four tones; a timber deck in boards with grain, gaps and nails; a sedum roof
    in clumps of greens and reds with flowers; or solar panels in their cells and frames."""
    r = list(ramp)
    strip = 9 + int(noise2(seed, 1, 3600) * 6)
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, v = x - x0, y - y0
            cx, cy = u // 2, v // 2
            n = noise2(cx, cy, 3601 + seed)
            if kind == 'membrane':
                k, su = divmod(u, strip)
                base = (r[2], mix(r[2], r[3], 0.5), step(r[2], 0.6), mix(r[2], '#6A5A48', 0.3))[
                    int(noise2(k, v // 12, 3602 + seed) * 4)]
                c = base
                if su == 0 or v % 12 == 0:
                    c = r[3]  # the lap's lit lip
                elif su == 1 or v % 12 == 1:
                    c = r[0]  # its shadow
                elif n > 0.66:
                    c = step(base, -0.8) if n < 0.86 else step(base, -1.6)  # grit
                elif n < 0.24:
                    c = step(base, 0.8)
                elif 0.45 < n < 0.49:
                    c = '#7A7A3A' if cx % 2 else '#5A6A3A'  # lichen
                elif 0.5 < n < 0.53:
                    c = '#6A4A2A'  # leaf litter blown into the corner of a lap
                m = smooth_noise(u, v * 1.4, 6, 3603 + seed)
                if m > 0.76:  # ponded rain: the dusk sky in it, a dark rim
                    c = mix(SKY[2], base, 0.35) if m > 0.79 and (u + v) % 7 not in (2, 3) else \
                        mix(SKY[3], base, 0.3) if m > 0.79 else step(base, 1.2)
            elif kind == 'gravel':
                # pale gravel in broad soft patches a tone apart, stones in 2 px clusters, lit on
                # top and shaded below, moss only in a damp clump here and there (calm, 20 Oct)
                p_ = smooth_noise(u, v, 7, 3625 + seed)
                c = step(r[2], 0.5) if p_ < 0.2 else r[2] if p_ < 0.45 else mix(r[2], r[3], 0.5) if p_ < 0.7 else r[3] if p_ < 0.88 else step(r[3], -0.5)
                g = noise2(cx, cy, 3604 + seed)
                if g > 0.86:
                    c = mix(r[3], '#B0A890', 0.35) if v % 2 == 0 else step(r[2], 0.7)  # a pale stone: its lit top, its shaded foot
                elif g > 0.78:
                    c = mix(r[3], '#9AA0A8', 0.4) if v % 2 == 0 else step(r[2], 1.0)  # a grey flint
                elif g < 0.08:
                    c = mix(r[2], '#8A6A4A', 0.35) if v % 2 == 0 else step(r[2], 1.2)  # a brown one
                elif g < 0.12:
                    c = r[1] if v % 2 == 0 else r[0]  # a hollow where a stone has gone
                elif g < 0.18:
                    c = mix(r[3], '#C08A5A', 0.4) if v % 2 == 0 else mix(r[2], '#6A4A3A', 0.4)  # a rust-red pebble
                if smooth_noise(u, v, 5, 3616 + seed) > 0.8 and noise2(cx, cy, 3626 + seed) > 0.4:
                    c = '#5A6A3A' if v % 2 else '#7A7A3A'  # moss in a damp clump
            elif kind == 'deck':
                row, rv = divmod(v, 3)
                seg = (u + int(noise2(row, 0, 3605 + seed) * 20)) // 13
                wood = ('#5E3D2E', '#80573A', '#6E4A32', '#946A44')
                c = wood[int(noise2(seg, row, 3606 + seed) * 4)]
                if rv == 2:
                    c = '#2A1A14'  # the gap between boards
                elif rv == 0:
                    c = step(c, -0.7)  # the board's lit edge
                elif noise2(u // 3, row, 3608 + seed) > 0.72:
                    c = step(c, 0.8)  # grain
                elif noise2(u // 2, row, 3617 + seed) > 0.95:
                    c = '#3A2418'  # a knot
                if rv < 2 and noise2(cx, row, 3618 + seed) > 0.88:
                    c = ('#9A7A3A', '#6A5A2A', '#7A3A2A')[int(noise2(cx, row, 3619) * 3)]  # leaves blown in
                elif rv == 1 and (u + row * 3) % 11 in (4, 5):
                    c = '#9A8A74'  # a pair of nail heads
                if (u + int(noise2(row, 0, 3605 + seed) * 20)) % 13 in (0,) and rv < 2:
                    c = '#2A1A14'  # the board ends
            elif kind == 'green':
                # sedum in clumps a few px across, each a green a step from its neighbours,
                # red sedum in its own clumps, rosettes lit on top, flowers as pairs (calm, 20 Oct)
                greens = ('#2A4A38', '#3A6446', '#4E6E44', '#6A8A4A')
                q_ = smooth_noise(u, v, 4, 3627 + seed)
                c = greens[min(3, int(q_ * 4))]
                if smooth_noise(u + 40, v, 5, 3628 + seed) > 0.74:
                    c = '#7A4A4A' if q_ > 0.5 else '#5E3A3E'  # a clump of red sedum
                elif noise2(cx, cy, 3609 + seed) > 0.66:
                    c = greens[min(3, int(q_ * 4) + 1)] if v % 2 == 0 else greens[max(0, int(q_ * 4) - 1)]  # a rosette: lit top, shaded foot
                if v % 2 == 0 and noise2(cx, cy, 3610 + seed) > 0.92:
                    c = ('#C8A040', '#B8608A', '#C8C0B0')[int(noise2(cx, cy, 3611) * 3)]  # sedum in flower, a pair of heads
                if v % 14 in (7, 8):
                    c = r[3] if v % 14 == 7 else r[2]  # a gravel path across the sedum
            elif kind == 'solar':
                row, rv = divmod(v, 8)
                if rv >= 6 or u % 24 in (22, 23):
                    c = (r[2], r[3])[int(n * 2)]  # the walkway's gravel
                else:
                    cu, cvv = u % 24, rv
                    cell = cu // 4 + (u // 24) * 6
                    c = ('#1E3A6A', '#22406E', '#1A3460')[int(noise2(cell, row, 3615 + seed) * 3)] \
                        if cu % 4 != 3 else '#56606E'
                    if cvv == 0:
                        c = '#76808E'  # the frame's lit top
                    elif cvv == 5:
                        c = '#2A303C'  # its foot in shadow
                    elif (cell + row) % 5 == 2 and cu % 4 != 3:
                        c = '#4A70A8' if cvv < 3 else '#3A5A90'  # the sky's glint
            else:
                c = r[2]
            cv.set(x, y, c)
    if kind == 'membrane':  # repairs: patches of new sheet, lit on their top and west edges
        for k in range(1 + (x1 - x0) * (y1 - y0) // 500):
            px = x0 + 3 + int(noise2(seed, k, 3611) * max(1, x1 - x0 - 10))
            py = y0 + 3 + int(noise2(seed, k, 3612) * max(1, y1 - y0 - 8))
            pw, ph = 4 + int(noise2(seed, k, 3613) * 4), 3 + int(noise2(seed, k, 3614) * 3)
            for y in range(py, min(y1 - 2, py + ph)):
                for x in range(px, min(x1 - 2, px + pw)):
                    c = r[1] if (x + y) % 5 else step(r[1], 0.6)
                    if y == py or x == px:
                        c = r[3]
                    cv.set(x, y, c)

    roof_clutter(cv, x0, x1, y0, y1, kind, r, seed)


def mushroom_vent(cv: Canvas, x: int, y: int):
    """A soil-stack vent seen from above: a round cap lit on its top-left, its shadow."""
    pts = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3)]
    for (dx, dy) in pts:
        cv.set(x + dx, y + dy, METAL[5] if dx + dy < 2 else METAL[4] if dx + dy < 4 else METAL[2])
    for (dx, dy) in ((4, 2), (4, 3), (3, 3), (2, 4), (3, 4)):
        darken(cv, x + dx, y + dy, 1.6)


def roof_clutter(cv: Canvas, x0: int, x1: int, y0: int, y1: int, kind: str, r, seed: int):
    """What lives on a flat roof besides its big plant: a pipe run on its blocks, soil-stack
    vents, a skylight lit from the room below; on a deck, the pots and chairs of a terrace
    and a string of lights."""
    W, H = x1 - x0, y1 - y0
    if H >= 12 and noise2(seed, 1, 3620) > 0.3:  # a pipe run on its blocks
        py = y0 + 3 + int(noise2(seed, 2, 3620) * (H - 8))
        for x in range(x0 + 2, x1 - 2):
            cv.set(x, py, METAL[4]); cv.set(x, py + 1, METAL[2])
            darken(cv, x + 1, py + 2, 1.4)
            if (x - x0) % 9 == 4:
                for d in (2, 3):
                    cv.set(x, py + d, '#7A7470'); cv.set(x + 1, py + d, '#5A5450')
    for k in range(max(1, W * H // 1000)):  # a few soil-stack vents, not a field of them
        vx = x0 + 3 + int(noise2(seed, k, 3621) * max(1, W - 8))
        vy = y0 + 2 + int(noise2(seed, k, 3622) * max(1, H - 7))
        mushroom_vent(cv, vx, vy)
    if W >= 30 and H >= 16 and noise2(seed, 3, 3620) > 0.4:  # a skylight: a glazed hip, lit below
        sx = x0 + 4 + int(noise2(seed, 4, 3620) * (W - 18))
        sy = y0 + 3 + int(noise2(seed, 5, 3620) * (H - 12))
        for y in range(sy, sy + 7):
            for x in range(sx, sx + 11):
                e = x in (sx, sx + 10) or y in (sy, sy + 6)
                c = METAL[4] if e and (x == sx or y == sy) else METAL[1] if e else \
                    (WARM[3] if y < sy + 3 else WARM[2]) if (x - sx) % 5 else METAL[3]
                cv.set(x, y, c)
        for x in range(sx + 1, sx + 12):
            darken(cv, x, sy + 7, 1.5)
    if kind == 'deck':
        for k in range(1 + W // 20):  # pots along the deck's edges, a chair or two
            px = x0 + 3 + int(noise2(seed, k, 3623) * max(1, W - 8))
            py = y0 + 2 + int(noise2(seed, k, 3624) * max(1, H - 8))
            for (dx, dy) in ((0, 2), (1, 2), (2, 2), (0, 3), (1, 3), (2, 3)):
                cv.set(px + dx, py + dy, '#A0583C' if dy == 2 else '#6A3222')
            for (dx, dy, c) in ((0, 0, LEAF[3]), (1, 0, LEAF[4]), (1, 1, LEAF[2]), (2, 1, LEAF[3]),
                                (0, 1, LEAF[2]), (2, 0, LEAF[1]), (-1, 1, LEAF[1]), (3, 1, LEAF[2])):
                cv.set(px + dx, py + dy, c)
            for d in (1, 2, 3):
                darken(cv, px + 3, py + d + 1, 1.4)
            cx = px + 6
            if cx + 4 < x1:
                for (dx, dy) in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)):
                    cv.set(cx + dx, py + 1 + dy, '#C8C0B0' if dy == 0 else '#8A8478')
                cv.set(cx, py + 3, '#4A4640'); cv.set(cx + 2, py + 3, '#4A4640')
        ly = y0 + 2
        for x in range(x0 + 2, x1 - 2):  # a string of lights over the terrace
            t = ((x - x0) % 16) / 16
            yy = ly + round(3 * 4 * t * (1 - t))
            cv.set(x, yy, '#2A2420'); cv.set(x + 1, yy, '#2A2420')
            if (x - x0) % 4 == 2:
                cv.set(x, yy + 1, WARM[4]); cv.set(x + 1, yy + 1, WARM[3])
