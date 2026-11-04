"""Building volume and shadows: the rules that make a house front read as a solid (Matt, 4 Nov
11:45: "one thing i really want you to perfect are the shadows so that 2d houses at least look a
little 3d"), measured from Eastward in docs/vision/eastward-edges.md, section 11.

Every house that `houses.building` paints gets these as rules, never hand-painted per sprite:

- the eave band (11.1): under the fascia (or the thatch's edge) a one-texel soffit line, the
  wall's darkest, then a core two ramp tones down, then a softer band one tone down whose lower
  edge is broken by the courses and leans down to the east;
- recesses (11.2): an opening's head and west reveal in shade, its east reveal lit;
- the corners (11.3): the west arris lit, the wall turning away towards the east corner in two
  steps, the last two texels a step deeper still;
- the foot (11.4): the wall a tone down in a band over the plinth, which ends in the contact line;
- protrusions (11.5): a sign, a pipe, a plate or a bundle hung on the wall throws an L of shade one
  tone down, east of it and under it, offset by how far it stands off the wall;
- the ground cast shadow (11.6): the house as a box with its roof and stacks, projected on the
  ground east and a little north (`KX`, `KY` per world px of height), a column beside the east
  wall that follows the roof's silhouette, its core two tones down and its outer `RIM` one.

Shadows are ramp steps on the house palette (house-style.md 6): a pixel moves down its own
family's ramp, so a shadow stays on the palette and turns violet by the ramps' own lean. No colour
arithmetic, no dither: clean bands and clusters, which `finish` keeps free of lone texels.

Sizes are world px (q makes texels at the render density). The cast shadow's geometry
(`house_cast`) needs only the look and the density, so the kit index and the zone painter can
call it without drawing the house.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

# --- measured rules (eastward-edges.md 11; E native px at an adult of 54, ours world px at 25) ----
EAVE_TOP = (1, 2)        # the brightest tone left in the core and in the softer band
SOFFIT = 1               # texels: the soffit line under the fascia (E 1 to 2 px, L 33 to 79)
EAVE_CORE = 2.0          # world px two tones down (E 2 to 5 px, 28 to 60 % darker)
EAVE_SOFT = {'slate': 5.0, 'shingle': 5.0, 'thatch': 6.6}   # world px to the band's broken lower edge
EAVE_BREAK = (1.0, 1.6, 3.0, 5.0)   # world px: bumps up to +-1.0 deep, 1.6 to 5 long (E 2 to 3 every 10 to 15)
EAVE_LEAN = 1.2          # world px the band's edge drops from the west end to the east
ARRIS = 2                # texels lit at the west arris (E 1 to 3 px)
CORNER_E = 2.4           # world px of the wall turning away at the east corner (E about 5 px, one step)
CORNER_DEEP = 2          # texels a step deeper still at the very corner (the dark seam)
FOOT_AO = 3.0            # world px of wall a tone down over the plinth (E 4 to 14 px, one step)
PROTRUDE = (0.8, 1.2)    # world px of a protrusion's shade east and under it (E 1 to 3 px)
RECESS = (1.0, 0.6)      # world px of an opening's head and west reveal held in shade (E 2 and 1 to 2 px)
KX, KY = 0.19, -0.10     # the ground cast shadow per world px of height: east, a little north
RIM = 2.0                # world px of the cast shadow's outer rim, one tone (the rest two)
GLOWS = ('lamp', 'lava', 'glowflora')
# timber keeps its modelling in the shade: a beam, a post or a board is stepped down, never
# flattened (a lintel or a corner post under the eave still shows its lit arris and dark underside)
KEEP_FORM = ('timber', 'timber_warm', 'timber_cool')


def _V():
    from . import village as V
    return V


def _glow(a):
    from .palette import FI
    g = np.zeros(a.shape, bool)
    for fam in GLOWS:
        if fam in FI:
            g |= (a // 8) == FI[fam]
    return g


def step(a, m, d, lo=0, hi=5):
    """Move the texels under m by d along each family's own ramp (glows keep their light)."""
    sel = m & (a >= 0) & (a % 8 <= 5) & ~_glow(a)
    a[sel] = (a[sel] // 8) * 8 + np.clip(a[sel] % 8 + d, lo, hi)


def _form(a):
    from .palette import FI
    g = np.zeros(a.shape, bool)
    for fam in KEEP_FORM:
        if fam in FI:
            g |= (a // 8) == FI[fam]
    return g


def clamp(a, m, lo=0, hi=5, form=False):
    """Hold the texels under m between tones lo and hi (an idempotent shade or light). Unless form,
    timber keeps its own modelling (KEEP_FORM)."""
    sel = m & (a >= 0) & (a % 8 <= 5) & ~_glow(a)
    if not form:
        sel &= ~_form(a)
    a[sel] = (a[sel] // 8) * 8 + np.clip(a[sel] % 8, lo, hi)


def _grid(a):
    H, W = a.shape
    return np.mgrid[0:H, 0:W]


# ------------------------------------------------------------------------------------------------
# on the front
# ------------------------------------------------------------------------------------------------
def eave_band(a, L, R, y_top, roof, rng):
    """11.1: the shadow the eave throws on the wall under it. y_top is the first wall row under the
    fascia, gutter or thatch. A soffit line (two tones down, to tone 0 at most), the core two tones
    down, then one tone down to a lower edge broken by the courses and leaning down to the east.
    Returns the band's mask (for the tests)."""
    q = _V().q
    Y, X = _grid(a)
    inw = (X >= L) & (X < R)
    core = q(EAVE_CORE)
    soft = q(EAVE_SOFT.get(roof, EAVE_SOFT['slate']))
    amp, l0, l1 = EAVE_BREAK[0], EAVE_BREAK[2], EAVE_BREAK[3]
    edge = np.full(a.shape[1], y_top + soft, float)
    x = L
    while x < R:
        w = q(rng.uniform(l0, l1))
        edge[x:x + w] += int(rng.integers(-q(amp), q(amp) + 1))
        x += w
    edge += (np.arange(a.shape[1]) - L) / max(1, R - L) * q(EAVE_LEAN)
    edge = np.maximum(edge.astype(int), y_top + SOFFIT + core + 2)
    soffit = inw & (Y >= y_top) & (Y < y_top + SOFFIT)
    deep = inw & (Y >= y_top + SOFFIT) & (Y < y_top + SOFFIT + core)
    band = inw & (Y >= y_top) & (Y < edge[None, :])
    # in the shade the wall's own highlights go out: the band is a calm field, not the lit
    # texture darkened (E: the band's texture keeps its joints, its lit tops are gone)
    step(a, band, -1)
    clamp(a, band, hi=EAVE_TOP[1])
    step(a, deep | soffit, -1)
    clamp(a, deep, hi=EAVE_TOP[0])
    clamp(a, soffit, hi=0, form=True)
    return band


def corners(a, L, R, y_top, y_bot):
    """11.3: the front as a plane that turns at its ends: the west arris catching the light, the
    east end turning away in a band and a step deeper at the very corner."""
    q = _V().q
    Y, X = _grid(a)
    rows = (Y >= y_top) & (Y < y_bot)
    step(a, rows & (X >= L) & (X < L + ARRIS) & (Y > y_top + q(4)), +1)
    east = rows & (X >= R - q(CORNER_E)) & (X < R)
    step(a, east, -1)
    clamp(a, east, hi=3)
    step(a, rows & (X >= R - CORNER_DEEP) & (X < R), -1)


def foot(a, L, R, y_plinth):
    """11.4: the wall a tone down in a band over the plinth (the plinth ends in the contact line)."""
    q = _V().q
    Y, X = _grid(a)
    band = (X >= L) & (X < R) & (Y >= y_plinth - q(FOOT_AO)) & (Y < y_plinth)
    # (the darks stay where they are, so a board's or a course's own joints keep their depth)
    sel = band & (a % 8 >= 2)
    step(a, sel, -1)
    clamp(a, band, hi=3)


def recess(a, box):
    """11.2: an opening set into the wall: its head and its west reveal held in shade (tone 1 and 2
    at most), its east reveal's sliver lit (tone 3 at least). Idempotent, so an opening that
    already draws its reveals keeps them; one that does not gets them."""
    q = _V().q
    x0, y0, x1, y1 = (int(v) for v in box)
    Y, X = _grid(a)
    inside = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    clamp(a, inside & (Y < y0 + q(RECESS[0])), hi=1, form=True)
    clamp(a, inside & (X < x0 + q(RECESS[1])) & (Y >= y0 + q(RECESS[0])), hi=2, form=True)
    clamp(a, inside & (X == x1 - 1) & (Y >= y0 + q(RECESS[0])), lo=3, form=True)


def protrusion(a, made, wall, standoff=1.0):
    """11.5: what stands off the wall (made: its texels) throws an L of shade one tone down on the
    wall (wall: where shade may fall) east of it and under it, as far as it stands off."""
    q = _V().q
    if not made.any():
        return
    dx, dy = q(PROTRUDE[0] * standoff), q(PROTRUDE[1] * standoff)
    sh = np.zeros_like(made)
    sh[dy:, dx:] |= made[:-dy or None, :-dx or None]
    sh[:, dx:] |= made[:, :-dx or None]
    sh[dy:, :] |= made[:-dy or None, :]
    step(a, sh & ~made & wall, -1)


# ------------------------------------------------------------------------------------------------
# on the ground
# ------------------------------------------------------------------------------------------------
def volume_of(spec: dict) -> dict:
    """The house as solids in world px, from its look (the same defaults as houses.building):
    x from the west wall, g the ground line (0 the front foot, -depth the back), h the height."""
    w, dep = spec['w'], spec['depth']
    wall_h = spec.get('wall_h', 40)
    roof_h = spec.get('roof_h', round(dep * 0.55 + 10))
    ov = spec.get('overhang', 3)
    hip = spec.get('hip', 0)
    thatch = spec.get('roof', 'slate') == 'thatch'
    ext = ov + (1.5 if thatch else 0)
    h_eave = wall_h - (4 if thatch else 0.5)
    h_ridge = max(h_eave + 2, wall_h + roof_h - dep / 2)
    parts = [
        # the walls
        [(x, g, h) for x in (0, w) for g in (-dep, 0) for h in (0, wall_h)],
        # the roof: the eave's rectangle and the ridge (shortened by the hips)
        [(x, g, h_eave) for x in (-ext, w + ext) for g in (-dep - 1, 1.5 if thatch else 0.5)]
        + [(x, -dep / 2, h_ridge) for x in (-ext + hip, w + ext - hip)],
    ]
    chim = spec.get('chimney_h', 14)
    cw = spec.get('chimney_w', 9)
    for cx in spec.get('chimney') or []:
        top = wall_h + roof_h + chim - dep / 2
        parts.append([(x, g, h) for x in (cx - cw / 2, cx + cw / 2) for g in (-dep / 2 - cw / 3, -dep / 2 + cw / 3)
                      for h in (h_eave, top)])
    return {'w': w, 'depth': dep, 'parts': parts}


def house_cast(spec: dict, d: float, kx: float = KX, ky: float = KY):
    """11.6: the house's cast shadow on the ground, as (levels, ox, oy): an uint8 picture (2 the
    core, two tones down; 1 the outer rim, one tone) and its top-left corner in texels from the
    house's foot (the middle of its front foot line). Each solid is projected (x + kx h, g + ky h)
    and filled as its convex hull; the union is the shadow, under the house where it is hidden and
    east of it as a column that follows the roof."""
    vol = volume_of(spec)
    w = vol['w']
    polys = []
    for pts in vol['parts']:
        pp = np.array([((x - w / 2 + kx * h) * d, (g + ky * h) * d) for (x, g, h) in pts])
        polys.append(_hull(pp))
    allp = np.vstack(polys)
    pad = 2
    x0, y0 = int(np.floor(allp[:, 0].min())) - pad, int(np.floor(allp[:, 1].min())) - pad
    x1, y1 = int(np.ceil(allp[:, 0].max())) + pad, int(np.ceil(allp[:, 1].max())) + pad
    Y, X = np.mgrid[y0:y1, x0:x1] + 0.5               # texel centres
    m = np.zeros(X.shape, bool)
    for p in polys:
        m |= _inside(p, X, Y)
    # nothing falls before the lit front: the ground south of the foot line stays in the light
    m[max(0, -y0):, :] = False
    core = ndi.binary_erosion(m, iterations=max(1, int(round(RIM * d))))
    return np.where(core, 2, np.where(m, 1, 0)).astype(np.uint8), x0, y0


def cast_at(levels, ox, oy, foot, W, H):
    """A house_cast laid on a W x H ground at the house's foot: (shadow mask, core mask)."""
    m = np.zeros((H, W), np.uint8)
    h, w = levels.shape
    X0, Y0 = int(foot[0]) + ox, int(foot[1]) + oy
    xs, ys = slice(max(0, X0), min(W, X0 + w)), slice(max(0, Y0), min(H, Y0 + h))
    if xs.start < xs.stop and ys.start < ys.stop:
        m[ys, xs] = levels[ys.start - Y0:ys.stop - Y0, xs.start - X0:xs.stop - X0]
    return m > 0, m > 1


def _inside(poly, X, Y):
    """Texel centres inside a convex polygon given counter-clockwise (in y-down texels)."""
    inside = np.ones(X.shape, bool)
    n = len(poly)
    if n < 3:
        return np.zeros(X.shape, bool)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        inside &= (bx - ax) * (Y - ay) - (by - ay) * (X - ax) >= 0
    return inside


def _hull(p):
    """Convex hull of 2D points (monotone chain), counter-clockwise."""
    pts = sorted(set(map(tuple, np.round(p, 4))))
    if len(pts) <= 2:
        return np.array(pts)

    def cross(o, a_, b):
        return (a_[0] - o[0]) * (b[1] - o[1]) - (a_[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for pt in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], pt) <= 0:
            lo.pop()
        lo.append(pt)
    for pt in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], pt) <= 0:
            up.pop()
        up.append(pt)
    return np.array(lo[:-1] + up[:-1])


def bake_cast(casts: list, entry: dict, at, W: int, H: int) -> bool:
    """For the kit's bake: a house's volume shadow (its index entry carries the mask the kit index
    wrote from house_cast) added to casts. True when the piece was a house (the caller skips the
    other shadow kinds), False otherwise."""
    sh = (entry or {}).get('shadow') or {}
    if sh.get('kind') != 'volume':
        return False
    from PIL import Image
    import os
    from scripts.art.kit.schema import ROOT
    mk = sh['mask']
    arr = np.asarray(Image.open(os.path.join(ROOT, 'game', mk['png'][len('res://'):])))
    m, _core = cast_at(arr, mk['offset'][0], mk['offset'][1], at, W, H)
    casts.append(m)
    return True
