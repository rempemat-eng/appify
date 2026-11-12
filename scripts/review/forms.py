"""Form and consistency checks from Matt's 12 Nov Frostline misses (#478 at bf525d25, and the
round 4 and 5 heads 0b122ffe and 0ef53b94). The independent detail-auditor passed that art and
Matt failed it on sight: "the trees look a bit off and so does the river. the bridge looks very
flat. the river in the second photo and the frozen water fall also dont really seem right. why
is one part frozen and the other isnt."

Each check answers one fault in calibration_set.json (F1 to F13) and was measured against the
reviewer-approved art on main, the pilot golden and Eastward before its line was drawn (the
numbers are beside each constant). They only add findings; no existing threshold moves.

  snow_stamp      asset, screen  snow on a crown drawn as one stamped chip (a left- or right-justified
                                 tapering wedge) repeated on every bough
  tree_pole       asset          a tree far taller and thinner than any approved tree
  deck_upright    asset          a bridge or deck drawn front-on: its boards stand upright the full
                                 face like a fence, with no top plane to walk on
  masonry_rock    asset          natural rock drawn as masonry: a regular grid of straight joints, or
                                 one stone shape repeated at a fixed pitch (pillow stones)
  stair_read      asset          a stair that does not read as steps: risers drawn as lines (a ladder of
                                 strips), or every step split into staggered bricks (a wall)
  fall_slab       asset          a fall or icefall cut as a rectangle (straight sides, full box)
  water_state     screen         one water body both frozen and open (a frozen section beside open water)

Sizes are fractions of the character height H; luminance in L units (core.lum).
"""
from __future__ import annotations

import re

import numpy as np
from scipy import ndimage as ndi

from .core import Finding, hsv, lum, regions, slice_box
from . import detail as D

# ------------------------------------------------------------------------------------------
# Names. Every check here but snow_stamp and water_state is keyed to the asset's file name: a
# name is split into whole word parts (letters only: "frost_pine_squat_2" is frost, pine, squat), and
# a check runs when one part is one of its words, so "fir" never matches fire_ring nor "oak" cloak.
# A piece named outside these words (a stair called *_climb) is not judged by them: the auditors are.
TREE_WORDS = frozenset(('pine', 'spruce', 'fir', 'larch', 'conifer', 'yew', 'cedar', 'cypress', 'poplar',
                        'oak', 'beech', 'birch', 'willow', 'ash', 'alder', 'rowan', 'tree', 'krummholz'))
BRIDGE_WORDS = frozenset(('bridge', 'footbridge', 'deck', 'jetty', 'boardwalk', 'pier'))
# natural rock only: worked stone (walls, standing stones, stairs, chimneys) may be coursed
ROCK_WORDS = frozenset(('rockface', 'crag', 'cliff', 'scarp', 'escarpment', 'ledge', 'outcrop', 'headwall',
                        'bluff', 'tor', 'face'))
STAIR_WORDS = frozenset(('stair', 'stairs', 'steps', 'step'))
FALL_WORDS = frozenset(('icefall', 'waterfall', 'fall', 'falls', 'cascade'))


def _base(subject: str) -> str:
    return subject.split('/')[-1].split(':')[-1]


def name_parts(subject: str) -> set:
    """The whole word parts of an asset's name ('kit/frost_rock_face_b' -> frost, rock, face, b)."""
    parts = {w for w in re.split(r'[^a-z]+', _base(subject).lower()) if w}
    if {'rock', 'face'} <= parts:
        parts.add('rockface')
    return parts


def named(subject: str, words) -> bool:
    """The asset's name holds one of the words, and it is not a shadow picture."""
    parts = name_parts(subject)
    return 'shadow' not in parts and bool(parts & words)


def _bbox(m):
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def is_tree(subject: str) -> bool:
    return named(subject, TREE_WORDS)


# ------------------------------------------------------------------------------------------
# Snow chips stamped on a crown
STAMP_MIN = 12          # chips on one crown before a stamp can be judged
STAMP_SHARE = 0.4       # share of chips drawn as a tapering wedge (one side straight, rows narrowing). Measured: the bf525d25
#                         pine 0.64, squat pine 0.70, spruce 0.68 (Matt's F1); their round 4/5
#                         redraws 0.06 to 0.14; approved crowns carry no snow chips (0 chips)


def _wedge(m: np.ndarray) -> bool:
    """A chip drawn as one stamp: rows anchored on one side, each no wider than the row above,
    the top the widest (a right triangle hanging under a bough)."""
    hh, ww = m.shape
    if hh < 3 or ww < 3:
        return False
    w = m.sum(1)
    first = [int(np.argmax(r)) for r in m]
    last = [ww - 1 - int(np.argmax(r[::-1])) for r in m]
    if not all(w[k] == last[k] - first[k] + 1 for k in range(hh)):
        return False
    if not (all(w[k] >= w[k + 1] for k in range(hh - 1)) and w[0] > w[-1]):
        return False
    return len(set(first)) == 1 or len(set(last)) == 1


def snow_chips(rgb: np.ndarray, opaque: np.ndarray):
    """Snow chips lying on foliage: small near-white blobs mostly ringed by green. Returns
    (label image, list of (slice, is_wedge))."""
    h, s, v = hsv(rgb)
    fam = D.family_map(rgb)
    green = opaque & (fam == 1)
    snow = opaque & (v > 0.72) & (s < 0.25) & (fam != 1)
    lab, n = ndi.label(snow, structure=np.ones((3, 3)))
    chips = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if sl is None:
            continue
        m = lab[sl] == i
        if m.sum() < 5 or m.sum() > 60:
            continue
        y0, y1 = max(0, sl[0].start - 1), sl[0].stop + 1
        x0, x1 = max(0, sl[1].start - 1), sl[1].stop + 1
        big = lab[y0:y1, x0:x1] == i
        ring = ndi.binary_dilation(big, iterations=1) & ~big
        if green[y0:y1, x0:x1][ring].mean() < 0.25:
            continue
        chips.append((sl, _wedge(m)))
    return chips


def _stamp_finding(chips, subject, box):
    n = len(chips)
    w = sum(1 for _, t in chips if t)
    share = w / max(n, 1)
    if n < STAMP_MIN or share < STAMP_SHARE:
        return []
    return [Finding('detail.snow_stamp', 'fault', box,
                    f'{subject}: {w} of {n} snow chips on the crown are tapering wedges ({share:.0%}): '
                    'one chip shape stamped on every bough (Matt, 12 Nov: "the trees look a bit off")',
                    'lay snow as soft loads that follow each bough: lit caps of varied width and thickness, '
                    'sagging between needle tips, thicker on the upper, sheltered side, with blue shade under '
                    'them and gaps where branches shed it; no two the same', score=share, threshold=STAMP_SHARE,
                    subject=subject, extra=dict(chips=n, wedges=w))]


def snow_stamp(rgb, alpha, H, subject) -> list[Finding]:
    """Asset: the crown's snow chips as a whole."""
    if not alpha.any():
        return []
    return _stamp_finding(snow_chips(rgb, alpha), subject, _bbox(alpha))


def snow_stamp_screen(native, H, ignore) -> list[Finding]:
    """Screen: per crown (a green region of at least 1 H^2), the same rule."""
    rgb = native[..., :3]
    fam = D.family_map(rgb)
    green = ndi.binary_closing((fam == 1) & ~ignore, iterations=2)
    lab, regs = regions(green, min_area=int(1.0 * H * H))
    if not regs:
        return []
    chips = snow_chips(rgb, ~ignore)
    crown = ndi.grey_dilation(lab, size=5)
    fs = []
    for lid, sl, a in regs:
        mine = [(c, t) for c, t in chips if crown[(c[0].start + c[0].stop) // 2, (c[1].start + c[1].stop) // 2] == lid]
        fs += _stamp_finding(mine, 'crown', slice_box(sl))
    return fs


# ------------------------------------------------------------------------------------------
# A tree drawn as a pole
POLE_ASPECT = 2.75      # opaque height over width. Approved trees: woodland pine 2.42, birch 2.33,
#                         the rest 0.84 to 1.57; the bf525d25 spruce Matt saw 3.03 (F2)
POLE_CROWN = 2.3        # green crown height over width: approved pine 2.01, birch 1.45; spruce 2.48


def tree_pole(rgb, alpha, H, subject) -> list[Finding]:
    if not is_tree(subject) or alpha.sum() < 0.3 * H * H:
        return []
    x0, y0, x1, y1 = _bbox(alpha)
    asp = (y1 - y0) / max(1, x1 - x0)
    g = alpha & (D.family_map(rgb) == 1)
    if not g.any():
        return []
    gx0, gy0, gx1, gy1 = _bbox(g)
    casp = (gy1 - gy0) / max(1, gx1 - gx0)
    if asp <= POLE_ASPECT or casp <= POLE_CROWN:
        return []
    return [Finding('logic.tree_pole', 'fault', (x0, y0, x1, y1),
                    f'{subject}: {asp:.2f} times as tall as it is wide (crown {casp:.2f}); every approved tree is '
                    f'at most 2.42 (the woodland pine): it reads as a pole beside a house',
                    'widen the crown to the approved pine\'s proportion (about 2 : 1 crown, 2.4 : 1 overall) or '
                    'lower it; a conifer\'s lower boughs reach out a third of its height', score=asp,
                    threshold=POLE_ASPECT, subject=subject, extra=dict(crown_aspect=casp))]


# ------------------------------------------------------------------------------------------
# A deck drawn front-on
DECK_SEAM = 0.4         # H: a dark board seam running unbroken this far down the face
DECK_COLUMNS = 8        # columns with such a seam. bf525d25 footbridge 17 (F7); its round 4 redraw 0,
#                         footbridge_2 0, footbridge_4 1, the stall 3, benches and fences 0


def _vertical_runs(m: np.ndarray) -> np.ndarray:
    best = np.zeros(m.shape[1], int)
    run = np.zeros(m.shape[1], int)
    for row in m:
        run = np.where(row, run + 1, 0)
        best = np.maximum(best, run)
    return best


def deck_upright(rgb, alpha, H, subject) -> list[Finding]:
    if not named(subject, BRIDGE_WORDS):
        return []
    fam = D.family_map(rgb)
    L = lum(rgb).astype(float)
    wood = ndi.binary_closing(alpha & np.isin(fam, (0, 3, 4, 7)), iterations=1)
    lp = np.pad(L, ((0, 0), (1, 1)), mode='edge')
    seam = wood & (((L < lp[:, :-2] - 8) & (L < lp[:, 2:] - 8)) | (fam == 0))
    runs = _vertical_runs(seam)
    cols = int((runs >= DECK_SEAM * H).sum())
    if cols < DECK_COLUMNS:
        return []
    return [Finding('logic.deck_upright', 'fault', _bbox(alpha),
                    f'{subject}: {cols} board seams run unbroken {runs.max()} px ({runs.max() / H:.2f} H) down the face: '
                    'the boards stand upright like a fence or a wall, a front-on view (Matt, 12 Nov: "the bridge looks very flat")',
                    'draw it in the 3/4 top-down projection: the walk as a lit top plane of boards no deeper than the '
                    'walk is wide, a thin dark fascia under its near edge, rails on posts along both sides, abutments '
                    'seen from above (eastward-edges.md, bridges)', score=cols, threshold=DECK_COLUMNS, subject=subject,
                    extra=dict(longest=int(runs.max())))]


# ------------------------------------------------------------------------------------------
# Natural rock drawn as masonry
GAP_SHARE = 0.62        # a joint is darker than 0.62 of the 0.5 H median around it
JOINT_RUN = 0.12        # H: a joint pixel on a straight horizontal or vertical run this long is ruled
GRID_SHARE = 0.5        # share of joint pixels on ruled runs, measured as the gate sees the piece (on neutral
#                         grey): the brick-grid faces of rounds 4 and 5 (F12) 0.57 to 0.75, main's twelve
#                         frost_rockface pieces 0.61 to 0.75; bf525d25's pillow faces 0.45 to 0.59 (the pitch
#                         half below catches the two under 0.5). Passing rock: the Frostline crags 0.15 and
#                         0.26, boulder_52 0.39, the standing stones 0.31 to 0.41 (Eastward's ledge faces,
#                         JPEG crops, 0.24 to 0.37)
GRID_DENSITY = 250      # ruled joint px per H^2 of rock, the same way: F12's faces 360 to 976. A boulder or a
#                         standing stone's ruled outline also measures 198 to 604, so this line only keeps a
#                         small, sparse part from tripping; the share above is what separates them
PITCH_PEAK = 0.28       # autocorrelation of the rock's tone at a stone pitch of 0.15 to 0.7 H along the
#                         face: the pillow face 0.39, its siblings 0.28 to 0.33; Eastward faces 0.0,
#                         crags 0.0 to 0.10, boulder_52 0.23. Tight: the line sits on the lowest failed
#                         measurement (bf525d25 rockface_short_plain 0.28), so a face a hair more regular
#                         than that would pass this half (the ruled-joint half may still catch it); lowering
#                         it needs more passing faces than the boulder to set it from


def _ruled(m: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros_like(m)
    for t in (False, True):
        mm = m.T if t else m
        o = np.zeros_like(mm)
        for i, row in enumerate(mm):
            j, w = 0, len(row)
            while j < w:
                if row[j]:
                    k = j
                    while k < w and row[k]:
                        k += 1
                    if k - j >= n:
                        o[i, j:k] = True
                    j = k
                else:
                    j += 1
        out |= o.T if t else o
    return out


def pitch_peak(L: np.ndarray, m: np.ndarray, H: float) -> float:
    """The strongest repeat of the tone along the face (x) at a stone's pitch, from the middle
    70 % of its rows (the snow lip and the foot are left out)."""
    x0, y0, x1, y1 = _bbox(m)
    hh = y1 - y0
    y0, y1 = y0 + int(0.15 * hh), y1 - int(0.15 * hh)
    sub, mm = L[y0:y1, x0:x1].astype(float), m[y0:y1, x0:x1]
    if sub.size == 0 or not mm.any():
        return 0.0
    sub = np.where(mm, sub, sub[mm].mean())
    sub = sub - sub.mean()
    F = np.fft.rfft2(sub, s=(2 * sub.shape[0], 2 * sub.shape[1]))
    ac = np.fft.irfft2(F * np.conj(F))[:sub.shape[0], :sub.shape[1]]
    if ac[0, 0] <= 1e-9:
        return 0.0
    ac = ac / ac[0, 0]
    nx = sub.shape[1]
    lo, hi = int(0.15 * H), min(int(0.7 * H), nx // 2)
    if hi - lo < 3:
        return 0.0
    r = ac[0, lo:hi] * nx / (nx - np.arange(lo, hi))
    best = 0.0
    for i in range(1, len(r) - 1):
        if r[i] >= r[i - 1] and r[i] >= r[i + 1]:
            best = max(best, float(r[i]))
    return best


def masonry_rock(rgb, alpha, H, subject) -> list[Finding]:
    if not named(subject, ROCK_WORDS) or alpha.sum() < 0.5 * H * H:
        return []
    L = lum(rgb).astype(float)
    med = ndi.median_filter(L, size=int(0.5 * H) | 1)
    gap = alpha & (L < GAP_SHARE * med)
    area = alpha.sum() / (H * H)
    ruled = _ruled(gap, max(6, int(round(JOINT_RUN * H))))
    share = ruled.sum() / max(1, gap.sum())
    density = ruled.sum() / area
    fs = []
    box = _bbox(alpha)
    if share >= GRID_SHARE and density >= GRID_DENSITY:
        fs.append(Finding('detail.masonry_rock', 'fault', box,
                          f'{subject}: {share:.0%} of the joints are ruled straight lines ({density:.0f} px a H^2): '
                          'natural rock drawn as a regular brick grid',
                          'break the face into irregular blocks and slabs along a bedding plane and joints that run at '
                          'angles, with chipped edges, overhangs, ledges catching snow and dark crevices of varied width; '
                          'no course runs straight across (Eastward\'s ledge faces measure 4 to 15 ruled px a H^2)',
                          score=density, threshold=GRID_DENSITY, subject=subject, extra=dict(share=round(share, 2))))
    peak = pitch_peak(L, alpha, H)
    if peak >= PITCH_PEAK:
        fs.append(Finding('detail.masonry_rock', 'fault', box,
                          f'{subject}: the face repeats one stone at a fixed pitch (autocorrelation {peak:.2f}): '
                          'a wall of same-size rounded "pillow" stones or bricks, not rock',
                          'draw rock as a few large masses split by joints of different lengths and angles, the stones of '
                          'very different sizes, some faces flat and lit, some in shadow; no stone shape repeats across '
                          'the face (Eastward\'s faces 0.0, the approved boulder 0.23)', score=peak, threshold=PITCH_PEAK,
                          subject=subject))
    return fs


# ------------------------------------------------------------------------------------------
# Stairs that do not read as steps
RISER_SHARE = 0.38      # the shaded riser's share of a step's pitch. Eastward's stairs 0.43 to 0.53, the
#                         kit's log steps 0.42 to 0.50; the round 4 stair 0.34 and round 5 0.19 (risers drawn
#                         as lines: a ladder of strips, F11). Raised from 0.36 in the #481 audit, a tightening:
#                         it catches strictly more (a 10/6 tread/riser stair, 0.375, now trips), and every
#                         correct-stair probe (9/7, 10/8, 11/7, 12/8, with and without texture), Eastward's
#                         four stairs and main's log steps still pass
BOND_JOINTS = 2         # vertical joints across a step, staggered from the step above, in at least
BOND_STEPS = 0.5        # half the steps: a brick bond (the bf525d25 stair, F10); Eastward's stairs 0


def _step_profile(L, m):
    x0, y0, x1, y1 = _bbox(m)
    w = x1 - x0
    c0, c1 = x0 + int(0.2 * w), x1 - int(0.2 * w)
    prof = []
    for y in range(y0, y1):
        r = m[y, c0:c1]
        prof.append(float(np.median(L[y, c0:c1][r])) if r.any() else np.nan)
    return np.array(prof), (x0, y0, x1, y1)


def _pitch(prof: np.ndarray):
    p = np.nan_to_num(prof - np.nanmean(prof))
    ac = np.correlate(p, p, 'full')[len(p) - 1:]
    if ac[0] <= 1e-9:
        return None
    ac = ac / ac[0]
    for lag in range(4, len(p) // 3):
        if ac[lag] > ac[lag - 1] and ac[lag] >= ac[min(lag + 1, len(ac) - 1)] and ac[lag] > 0.2:
            return lag
    return None


def stair_read(rgb, alpha, H, subject) -> list[Finding]:
    if not named(subject, STAIR_WORDS) or alpha.sum() < 0.3 * H * H:
        return []
    L = lum(rgb).astype(float)
    # the step profile: each row's median tone across the middle 60 % of the flight (its cheeks left out)
    prof, (x0, y0, x1, y1) = _step_profile(L, alpha)
    T = _pitch(prof)
    if not T:
        return []
    n = len(prof) // T
    if n < 3:
        return []
    shares, bonds, prev = [], [], None
    fam = D.family_map(rgb)
    for k in range(n):
        seg = prof[k * T:(k + 1) * T]
        seg = seg[~np.isnan(seg)]
        if len(seg) < 3:
            continue
        lo, hi = np.percentile(seg, 10), np.percentile(seg, 90)
        mid = (lo + hi) / 2
        shares.append(float(np.mean(seg < mid)))
        # vertical joints across this step's band: columns darker than both neighbours (or outline)
        # through at least 45 % of the band's rows
        ys = slice(y0 + k * T, y0 + (k + 1) * T)
        band = L[ys, x0:x1]
        lp = np.pad(band, ((0, 0), (1, 1)), mode='edge')
        dark = (((band < lp[:, :-2] - 12) & (band < lp[:, 2:] - 12)) | (fam[ys, x0:x1] == 0)) & alpha[ys, x0:x1]
        cols = np.nonzero(dark.mean(0) >= 0.45)[0]
        # inner joints only (not the cheeks): away from the flight's two sides
        w = x1 - x0
        cols = [c for c in cols if 0.08 * w < c < 0.92 * w]
        joints = []
        for c in cols:
            if not joints or c - joints[-1] > 1:
                joints.append(c)
        # staggered: most of this step's joints are off every joint of the step above
        off = [min([abs(j - q) for q in prev] or [99]) > 2 for j in joints] if prev is not None else []
        staggered = bool(off) and np.mean(off) > 0.5
        bonds.append(len(joints) >= BOND_JOINTS and (prev is None or staggered))
        prev = joints
    fs = []
    box = (x0, y0, x1, y1)
    if shares:
        rs = float(np.median(shares))
        if rs < RISER_SHARE:
            fs.append(Finding('detail.stair_read', 'fault', box,
                              f'{subject}: the shaded riser is {rs:.0%} of each step\'s {T} px pitch: the risers are '
                              'lines, so the flight reads as a ladder of strips',
                              'give every step a lit tread and a riser in shade of about the same depth (Eastward\'s '
                              'stairs: risers 43 to 53 % of the pitch), the nosing lit, the riser darkest under it, '
                              'a contact shadow where it meets the tread below', score=rs, threshold=RISER_SHARE,
                              subject=subject, extra=dict(pitch=T)))
    if bonds and np.mean(bonds) >= BOND_STEPS:
        fs.append(Finding('detail.stair_read', 'fault', box,
                          f'{subject}: {sum(bonds)} of {len(bonds)} steps are split by staggered vertical joints: '
                          'a brick bond, so the flight reads as a wall, not steps',
                          'draw each step as one long tread (or two or three long slabs) with a lit top, a shaded '
                          'riser and a lit nosing; joints, if any, line up from step to step and never stagger like '
                          'courses of bricks', score=float(np.mean(bonds)), threshold=BOND_STEPS, subject=subject))
    return fs


# ------------------------------------------------------------------------------------------
# A fall cut as a rectangle
SLAB_FILL = 0.95        # opaque share of the fall's box: the Frostline icefall 0.99 (F13, every round);
#                         the approved kit waterfalls 0.47 to 0.89
SLAB_SIDE = 0.9         # share of rows whose edge sits on one column: icefall 0.99 to 1.0; approved 0.25 to 0.74


def fall_slab(alpha, H, subject) -> list[Finding]:
    if not named(subject, FALL_WORDS) or alpha.sum() < 0.2 * H * H:
        return []
    x0, y0, x1, y1 = _bbox(alpha)
    sub = alpha[y0:y1, x0:x1]
    fill = float(sub.mean())
    rows = [r for r in sub if r.any()]
    left = np.array([int(np.argmax(r)) for r in rows])
    right = np.array([len(r) - 1 - int(np.argmax(r[::-1])) for r in rows])

    def straight(e):
        _, c = np.unique(e, return_counts=True)
        return c.max() / len(e)
    sl, sr = straight(left), straight(right)
    if fill < SLAB_FILL or sl < SLAB_SIDE or sr < SLAB_SIDE:
        return []
    return [Finding('detail.fall_slab', 'fault', (x0, y0, x1, y1),
                    f'{subject}: the fall fills {fill:.0%} of its box with ruler-straight sides: a rectangle cut out of '
                    'the face, not water or ice falling over a lip',
                    'let the fall narrow and widen over the lip, its edges ragged where it meets the rock, the rock\'s '
                    'own face and lip showing on both sides; an icefall hangs as columns and curtains of different '
                    'lengths, thickest at the lip, fused at the foot', score=fill, threshold=SLAB_FILL,
                    subject=subject, extra=dict(left=round(float(sl), 2), right=round(float(sr), 2)))]


# ------------------------------------------------------------------------------------------
# Frozen and open in one water body
WINTER_SNOW = 0.15      # a screen with at least this share of snow (v > 0.8, s < 0.12) is a winter scene
STATE_MIN = 0.5         # H^2: the frozen part and the open part each at least this large
STATE_CONTACT = 0.3     # the share of the frozen part's rim against open water: shore ice lies along the
#                         bank (much of its rim is open water); a frozen section (a frozen tarn feeding an
#                         open stream, an icefall over an open pool) meets it only across the channel.
#                         Matt's fall step: 0.14 (tarn) and 0.03 (icefall); old snow zones: none found
#                         Untested on real passing art: no clean winter screen with shore ice was found,
#                         so only the synthetic rim test (Forms) holds the passing side


def water_state(native, H, ignore) -> list[Finding]:
    rgb = native[..., :3]
    h, s, v = hsv(rgb)
    snow = (v > 0.8) & (s < 0.12) & ~ignore
    if snow.mean() < WINTER_SNOW:
        return []
    blue = (h >= 190) & (h <= 235) & ~ignore
    open_ = ndi.binary_opening(blue & (s >= 0.46) & (v >= 0.25) & (v < 0.7), iterations=2)
    ice = blue & (s >= 0.1) & (s < 0.46) & (v >= 0.64)
    ice = ndi.binary_opening(ndi.binary_closing(ice, iterations=2), iterations=2)
    olab, on = ndi.label(open_)
    if not on:
        return []
    oarea = ndi.sum(open_, olab, range(1, on + 1))
    lab, regs = regions(ice, min_area=int(STATE_MIN * H * H))
    fs = []
    for lid, sl, a in regs:
        c = lab == lid
        ring = ndi.binary_dilation(c, iterations=2) & ~c
        ids = [i for i in np.unique(olab[ring & open_]) if i and oarea[i - 1] >= STATE_MIN * H * H]
        if not ids:
            continue
        contact = float((ring & open_).sum() / max(1, ring.sum()))
        if contact >= STATE_CONTACT:
            continue
        both = c | np.isin(olab, ids)
        fs.append(Finding('logic.water_state', 'fault', slice_box(ndi.find_objects(both.astype(int))[0]),
                          f'a frozen section ({a / (H * H):.1f} H^2) meets open water across the channel '
                          f'({contact:.0%} of its rim): one water body both frozen and flowing (Matt, 12 Nov: '
                          '"why is one part frozen and the other isnt")',
                          'give each water body one state for the season: all frozen (ice with snow drifts, cracks and '
                          'pressure ridges, the fall an icefall with no open pool under it) or all open (dark, cold water '
                          'with shore ice only as a thin rim along the banks); a spring or a fast riffle that stays open '
                          'needs a visible reason and steam', score=contact, threshold=STATE_CONTACT, subject='water',
                          extra=dict(ice_box=list(slice_box(sl)))))
    return fs


# ------------------------------------------------------------------------------------------
def check_named(rgb, alpha, H, subject) -> list[Finding]:
    """The name-keyed checks (tree_pole, deck_upright, masonry_rock, stair_read, fall_slab). They run on
    every asset whatever its opacity (assets.review_rgba calls them before the ground/sprite split), so
    trimming a picture's transparent margin cannot route a cut-out fall or a rock face around them."""
    fs = []
    fs += tree_pole(rgb, alpha, H, subject)
    fs += deck_upright(rgb, alpha, H, subject)
    fs += masonry_rock(rgb, alpha, H, subject)
    fs += stair_read(rgb, alpha, H, subject)
    fs += fall_slab(alpha, H, subject)
    return fs


def check_asset(rgb_n, alpha, H, subject) -> list[Finding]:
    """The sprite-only check (snow_stamp; assets.review_rgba)."""
    return snow_stamp(rgb_n, alpha, H, subject)


def check_screen(native, H, ignore) -> list[Finding]:
    """The screen checks above (screen.review_screen)."""
    return snow_stamp_screen(native, H, ignore) + water_state(native, H, ignore)
