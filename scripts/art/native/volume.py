"""Building volume and shadows: the rules that make a house front read as a solid (Matt, 4 Nov
11:45: "one thing i really want you to perfect are the shadows so that 2d houses at least look a
little 3d"), measured from Eastward in docs/vision/eastward-edges.md, section 11.

Every house that `houses.building` paints gets these as rules, never hand-painted per sprite:

- the eave band (11.1): under the fascia (or the thatch's edge) a soffit row, the wall's darkest,
  then a flat core 45 to 50 % darker, then a fade 18 % darker to a lower edge broken by the courses
  (or the thatch's fringe) and leaning down to the east: 16 art px under slate, 21 under thatch;
- recesses (11.2): an opening's head (round under an arch) and west reveal in shade, its east
  reveal lit; a sill lit on top over its drip;
- the corners (11.3): the west arris lit, the east end turning away and a dark seam at the corner;
- the foot (11.4): the wall 28 % darker in a band over the plinth, which ends in the contact line;
- protrusions (11.5): a sign, a pipe, a plate or a bundle hung on the wall throws an L of shade
  east of it and under it, offset by how far it stands off the wall;
- the ground cast shadow (11.6): the house as solids (walls, a 45 degree roof, its stacks),
  projected on the ground east and a little north (`KX`, `KY` per world px of height), a column
  beside the east wall that ends in its gable's verges, one, two and three tones from its edge in.

Building volume uses the measured depth (eastward-edges 11, house-style 6): each drop is a
luminance ratio read off Eastward, reached by the fewest steps (one to three) down the texel's own
ramp, so it stays on the palette and turns cool by the ramps' lean. No colour
arithmetic, no dither: clean bands and clusters, which `finish` keeps free of lone texels.

Sizes are world px (q makes texels at the render density). The cast shadow's geometry
(`house_cast`) needs only the look and the density, so the kit index and the zone painter can
call it without drawing the house.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

# --- measured rules (eastward-edges.md 11; E native px at an adult of 54, ours world px at 25) ----
# Building volume uses the measured depth (eastward-edges 11, house-style 6): each shadow is a
# luminance drop read off Eastward, reached by the fewest steps (one to three) down the texel's
# own ramp, so it stays on the palette and turns violet by the ramp's lean.
SOFFIT = 1               # texels: the soffit line under the fascia (E 1 to 2 px, L 33 to 79)
SOFFIT_DROP = 0.62       # its drop (B7 L 33 to 42 against about 100)
# the eave band by roof (world px): the core, then a fade to a broken lower edge
# Our fronts are eave sides: the slate and shingle roofs overhang them with a fascia and gutter,
# as B1's slab, B6's eave and B7's sign box do (E 10 to 12 px: core 4, then the fade), not a gable verge (B5's 3 to 4 px, which
# our front view never shows); thatch hangs deepest (B8: E 13 to 15).
EAVE = {
    'slate': dict(core=1.8, fade=3.3, amp=0.6, run=(3.0, 5.0), drop=0.45, top=(1, 2)),
    'shingle': dict(core=1.8, fade=3.3, amp=0.6, run=(3.0, 5.0), drop=0.45, top=(1, 2)),
    'thatch': dict(core=2.3, fade=4.4, amp=1.3, run=(1.6, 3.0), drop=0.50, top=(1, 2)),
}
FADE_DROP = 0.18         # the fade under the core (B1: L 97 to 103 against 111, B8 the ramp back)
EAVE_LEAN = 1.2          # world px the band's edge drops from the west end to the east
ARRIS = 2                # texels lit at the west arris (E 1 to 3 px)
CORNER_E = 3.0           # world px of the wall turning away at the east corner (E about 5 px, and its quoins)
CORNER_DROP = 0.22       # B3: L 122 against 145 next to the corner, 16 %, deepening into the seam
CORNER_DEEP = 2          # texels of the dark seam at the very corner
SEAM_DROP = 0.42         # B3: L 85 to 119 against 145 (18 to 41 %)
FOOT_AO = 3.0            # world px over the plinth (E 4 to 14 px)
FOOT_DROP = 0.28         # B1, B2, B5: 17 to 28 % darker
PROTRUDE = (0.8, 1.2)    # world px of a protrusion's shade east and under it (E 1 to 3 px)
PROTRUDE_DROP = 0.2
RECESS = (1.0, 0.7)      # world px of an opening's dark head and west reveal (E 2 and 1 to 2 px)
HEAD_DROP, REVEAL_DROP = 0.55, 0.4
DRIP = 1.0               # world px of a sill's drip shadow (E 2 to 3 px)
DRIP_DROP = 0.4
KX, KY = 0.19, -0.10     # the ground cast shadow per world px of height: east, a little north
RIM = 3.0                # world px of the cast shadow's outer band, one tone (E fades over 3 to 10 px)
MID = 2.6                # world px of the band two tones down inside it; deeper in, three (B3's core)
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


def _form(a):
    from .palette import FI
    g = np.zeros(a.shape, bool)
    for fam in KEEP_FORM:
        if fam in FI:
            g |= (a // 8) == FI[fam]
    return g


def step(a, m, d, lo=0, hi=5):
    """Move the texels under m by d along each family's own ramp (glows keep their light)."""
    sel = m & (a >= 0) & (a % 8 <= 5) & ~_glow(a)
    a[sel] = (a[sel] // 8) * 8 + np.clip(a[sel] % 8 + d, lo, hi)


_LUM = None


def lum():
    """Luminance (0 to 255) of every palette code."""
    global _LUM
    if _LUM is None:
        from .palette import FAMS, to_rgba
        c = to_rgba(np.arange(len(FAMS) * 8).reshape(1, -1))[0, :, :3].astype(float)
        _LUM = 0.299 * c[:, 0] + 0.587 * c[:, 1] + 0.114 * c[:, 2]
    return _LUM


def darken(a, m, drop, most=3, keep_darks=False):
    """The measured depth: each texel under m moves down its own ramp by the fewest tones (one to
    `most`) that make it at least `drop` darker in luminance (0.45 is 45 % darker). keep_darks
    leaves tones 0 and 1 where they are (a joint or a board's under-lap keeps its depth)."""
    sel = m & (a >= 0) & (a % 8 <= 5) & ~_glow(a)
    if keep_darks:
        sel &= a % 8 >= 2
    if not sel.any():
        return
    L = lum()
    c = a[sel]
    t = c % 8
    base = c - t
    n = np.full(c.shape, most)
    for k in range(most, 0, -1):
        ok = L[base + np.maximum(t - k, 0)] <= L[c] * (1 - drop)
        n = np.where(ok, k, n)
    a[sel] = base + np.maximum(t - n, 0)


def clamp(a, m, hi, form=False):
    """No tone above hi under m: in shade the light's modelling goes, the joints stay (timber
    keeps its own modelling unless form)."""
    sel = m & (a >= 0) & (a % 8 <= 5) & ~_glow(a)
    if not form:
        sel &= ~_form(a)
    a[sel] = (a[sel] // 8) * 8 + np.minimum(a[sel] % 8, hi)


def flat(a, m, t):
    """Every texel under m that is lighter than tone t takes tone t of its own family (a flat field
    of shade with its joints kept); timber is left to keep its modelling."""
    sel = m & (a >= 0) & (a % 8 <= 5) & ~_glow(a) & ~_form(a) & (a % 8 > t)
    a[sel] = (a[sel] // 8) * 8 + t


def _grid(a):
    H, W = a.shape
    return np.mgrid[0:H, 0:W]


def _shift(m, dy, dx):
    """m moved down by dy and right by dx (texels), empty where it came in."""
    out = np.zeros_like(m)
    H, W = m.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = m[ys, xs]
    return out


# ------------------------------------------------------------------------------------------------
# on the front
# ------------------------------------------------------------------------------------------------
def eave_band(a, L, R, y_top, roof, rng):
    """11.1: the shadow the eave throws on the wall under it. y_top is the first wall row under the
    fascia, gutter or thatch. A soffit row, the core at the measured drop, then a fade to a lower
    edge broken by the courses (or by the thatch's fringe of straw) and leaning down to the east:
    3 to 4 E px under a slate eave, 13 to 15 under thatch. Returns the band's mask."""
    q = _V().q
    e = EAVE.get(roof, EAVE['slate'])
    Y, X = _grid(a)
    inw = (X >= L) & (X < R)
    core = q(e['core'])
    edge = np.full(a.shape[1], y_top + SOFFIT + core + q(e['fade']), float)
    x = L
    while x < R:
        w = max(2, q(rng.uniform(*e['run'])))
        edge[x:x + w] += int(rng.integers(-q(e['amp']), q(e['amp']) + 1))
        x += w
    edge += (np.arange(a.shape[1]) - L) / max(1, R - L) * q(EAVE_LEAN)
    edge = np.maximum(edge.astype(int), y_top + SOFFIT + core + 1)
    soffit = inw & (Y >= y_top) & (Y < y_top + SOFFIT)
    deep = inw & (Y >= y_top + SOFFIT) & (Y < y_top + SOFFIT + core)
    band = inw & (Y >= y_top) & (Y < edge[None, :])
    darken(a, soffit, SOFFIT_DROP)
    darken(a, deep, e['drop'])
    darken(a, band & ~deep & ~soffit, FADE_DROP)
    # the band is a calm, flat shade (B1: the core one run at L 79, the fade one at 97 to 103):
    # the stones' and the plaster's own modelling goes, their joints (tone 0) stay; timber keeps
    # its modelling, a step down
    flat(a, deep, e['top'][0])
    flat(a, band & ~deep & ~soffit, e['top'][1])
    return band


def corners(a, L, R, y_top, y_bot):
    """11.3: the front as a plane that turns at its ends: the west arris catching the light, the
    east end turning away (16 % darker) and a dark seam at the very corner (35 %)."""
    q = _V().q
    Y, X = _grid(a)
    rows = (Y >= y_top) & (Y < y_bot)
    step(a, rows & (X >= L) & (X < L + ARRIS) & (Y > y_top + q(4)), +1)
    darken(a, rows & (X >= R - q(CORNER_E)) & (X < R - CORNER_DEEP), CORNER_DROP)
    darken(a, rows & (X >= R - CORNER_DEEP) & (X < R), SEAM_DROP)


def foot(a, L, R, y_plinth):
    """11.4: the wall 25 % darker in a band over the plinth (the plinth ends in the contact line);
    its darks stay, so the lowest board or course keeps its joints."""
    q = _V().q
    Y, X = _grid(a)
    band = (X >= L) & (X < R) & (Y >= y_plinth - q(FOOT_AO)) & (Y < y_plinth)
    darken(a, band, FOOT_DROP, keep_darks=True)


def recess(a, box, arch=False):
    """11.2: an opening set into the wall: a dark head (50 %) that follows its top, round under an
    arch; a dark west reveal (35 %); the east reveal's sliver lit. Returns the opening's mask."""
    q = _V().q
    x0, y0, x1, y1 = (int(v) for v in box)
    Y, X = _grid(a)
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    if arch:
        r = (x1 - x0) / 2
        cx = (x0 + x1) / 2
        m &= ~((Y < y0 + r) & ((((X + 0.5 - cx) / r) ** 2 + ((Y + 0.5 - y0 - r) / r) ** 2) > 1))
    head = m & ~_shift(m, q(RECESS[0]), 0)
    west = m & ~_shift(m, 0, q(RECESS[1])) & ~head
    east = m & ~_shift(m, 0, -1) & ~head
    darken(a, head, HEAD_DROP)
    clamp(a, head, 1, form=True)
    darken(a, west, REVEAL_DROP)
    clamp(a, west, 2, form=True)
    step(a, east, +1)
    return m


def sill(a, x0, x1, y_top, y_bot):
    """11.2: a sill stands proud: its top row catches the light, its drip throws a 40 % band on the
    wall under it, a texel further to the east."""
    q = _V().q
    Y, X = _grid(a)
    step(a, (X >= x0 + 1) & (X < x1 - 1) & (Y == y_top), +1)
    darken(a, (X >= x0 + 1) & (X < x1 + 1) & (Y >= y_bot) & (Y < y_bot + q(DRIP)), DRIP_DROP)


def protrusion(a, made, wall, standoff=1.0):
    """11.5: what stands off the wall (made: its texels) throws an L of shade (20 % darker) on the
    wall (wall: where shade may fall) east of it and under it, as far as it stands off."""
    q = _V().q
    if not made.any():
        return
    dx, dy = q(PROTRUDE[0] * standoff), q(PROTRUDE[1] * standoff)
    sh = _shift(made, dy, dx) | _shift(made, 0, dx) | _shift(made, dy, 0)
    darken(a, sh & ~made & wall, PROTRUDE_DROP, most=2)


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
    # the roof's real profile: a cottage pitch of 45 degrees, so the ridge stands half the depth
    # over the eave (or higher where the drawing's roof is taller); a hip shortens the ridge
    h_ridge = max(h_eave + dep / 2, wall_h + roof_h - dep / 2)
    parts = [
        # the walls
        [(x, g, h) for x in (0, w) for g in (-dep, 0) for h in (0, wall_h)],
        # the roof: the eave's rectangle and the ridge (shortened by the hips), so a gable end
        # throws its slanted verges and a hip its slope
        [(x, g, h_eave) for x in (-ext, w + ext) for g in (-dep - 1, 1.5 if thatch else 0.5)]
        + [(x, -dep / 2, h_ridge) for x in (-ext + hip, w + ext - hip)],
    ]
    chim = spec.get('chimney_h', 14)
    cw = spec.get('chimney_w', 9)
    for cx in spec.get('chimney') or []:
        # a stack: its own solid from the roof up to its pots, chim over the ridge
        top = h_ridge + chim
        parts.append([(x, g, h) for x in (cx - cw / 2, cx + cw / 2) for g in (-dep / 2 - cw / 3, -dep / 2 + cw / 3)
                      for h in (h_eave, top)])
    return {'w': w, 'depth': dep, 'parts': parts}


def house_cast(spec: dict, d: float, kx: float = KX, ky: float = KY):
    """11.6: the house's cast shadow on the ground, as (levels, ox, oy): an uint8 picture of ramp
    steps and its top-left corner in texels from the house's foot (the middle of its front foot
    line). Each solid (the walls, the roof, every stack) is projected (x + kx h, g + ky h) and
    filled as its convex hull, so the column east of the house ends in its gable's slanted verges
    or its hip and a stack beyond the roof's shadow shows as its own notch. The steps follow
    Eastward's soft edge and dark core (B3): the outer RIM one tone, the next MID two, deeper in
    three; nothing falls south of the foot line, before the lit front."""
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
    m[max(0, -y0):, :] = False
    # the soft edge: depth from the shadow's outline, the ground's own row under the foot line
    # counting as inside (the column runs down to the foot, it does not fade there)
    foot_row = max(1, -y0)
    k = int(np.ceil((RIM + MID) * d)) + 2
    tall = np.vstack([m[:foot_row], np.repeat(m[foot_row - 1:foot_row], k, axis=0)])
    dist = ndi.distance_transform_edt(np.pad(tall, 1))[1:-1, 1:-1][:m.shape[0]]
    dist = np.vstack([dist, np.zeros((m.shape[0] - dist.shape[0], m.shape[1]))]) if dist.shape[0] < m.shape[0] else dist
    lv = np.where(dist > (RIM + MID) * d, 3, np.where(dist > RIM * d, 2, 1))
    return np.where(m, lv, 0).astype(np.uint8), x0, y0


def cast_at(levels, ox, oy, foot, W, H):
    """A house_cast laid on a W x H ground at the house's foot: its steps per texel (0 outside)."""
    m = np.zeros((H, W), np.uint8)
    h, w = levels.shape
    X0, Y0 = int(foot[0]) + ox, int(foot[1]) + oy
    xs, ys = slice(max(0, X0), min(W, X0 + w)), slice(max(0, Y0), min(H, Y0 + h))
    if xs.start < xs.stop and ys.start < ys.stop:
        m[ys, xs] = levels[ys.start - Y0:ys.stop - Y0, xs.start - X0:xs.stop - X0]
    return m


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
    casts.append(cast_at(arr, mk['offset'][0], mk['offset'][1], at, W, H) > 0)
    return True
