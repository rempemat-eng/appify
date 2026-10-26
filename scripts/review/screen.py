"""Whole-screen detectors: the scene gate's image half. They need only the picture (a Godot
screenshot, a zone composite or someone's crop), brought to its art grid by core.to_native.

  water        stair-stepped banks, ruler channels, flat or unfed falls, bridges short of a bank
  shadows      cast shadows with no caster at their head, or far larger than what touches them
  artefacts    thin isolated lines and dotted lines that belong to nothing
  repetition   identical stamps (tufts, clumps) repeated across the ground at an even density
  flats        large smooth single-tone areas inside objects (not the calm ground, not water)
  mesh         canopies drawn as networks of 1 px dark contour strokes
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .core import Finding, keys, hsv, lum, regions, slice_box, merge_findings, water_mask
from . import water as W
from .objects import ground_palette
from . import detail as D
from . import bands as B


def calm_ground(native, comp, H) -> bool:
    """A large calm area that is a ground plane drawn to Eastward's ground band (bands.ground_plane:
    drawn texture a patch, quiet contrast between its pieces). Eastward's dungeon floors are dark,
    calm fields; the prop rule (few tones, two covering most) would call them flat."""
    if comp.sum() < GROUND_PLANE_MIN * H * H:
        return False
    ys, xs = np.nonzero(comp)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    if min(y1 - y0, x1 - x0) < 0.5 * H:          # a strip (a wall face, a ledge) is not a plane
        return False
    r = B.ground_plane(native[y0:y1, x0:x1, :3], comp[y0:y1, x0:x1], H)
    return bool(r.get('passed'))


def piece_of_ground(native, comp, g, H) -> bool:
    """A small calm patch set in the ground (a flag a tone off its neighbours, a patch of damp): its
    ring is mostly the screen's ground, and it differs from that ring by no more than Eastward's
    ground pieces differ from each other (2.5 spreads of the ground band's contrast, in L, and a
    little hue).
    A thing stands out further: a prop, a boulder, a slab of Matt's terrazzo (U1) does."""
    ring = ndi.binary_dilation(comp, iterations=2) & ~comp
    if not ring.any() or g[ring].mean() < 0.5:          # as flats(): a ring at least half ground
        return False
    band = B.load_bands().get('groups', {}).get('ground')
    if not band:
        return False
    a = np.median(native[..., :3][comp].astype(float), axis=0)
    b = np.median(native[..., :3][ring & g].astype(float), axis=0)
    wl = np.array([0.299, 0.587, 0.114])
    dl = abs(float(a @ wl - b @ wl))
    dc = float(np.linalg.norm((a - a @ wl) - (b - b @ wl)))
    return dl <= PIECE_SPREAD * band['max_contrast'] and dc <= PIECE_HUE


def ground_planes(native, H, ignore) -> np.ndarray:
    """Every calm ground plane on the screen (calm_ground) as one mask: the regions off the
    screen's ground palette (after a 3 x 3 opening) that pass the ground band."""
    k, ground = ground_palette(native)
    obj = ndi.binary_opening(~np.isin(k, ground) & ~ignore, structure=np.ones((3, 3)))
    lab, regs = regions(obj, min_area=int(GROUND_PLANE_MIN * H * H))
    out = np.zeros(obj.shape, bool)
    for lid, sl, a in regs:
        c = lab == lid
        if calm_ground(native, c, H):
            out |= c
    return out

SHADOW_MIN_AREA = 0.35        # H^2
SHADOW_CONTACT = 0.35         # a caster must touch at least this share of the shadow's width
LINE_MIN_LEN = 0.35           # H: a thin line this long that belongs to nothing is an artefact
REPEAT_MIN = 12               # identical tuft stamps on one screen
REPEAT_DENSITY = 1.0          # exact repeats of a tuft stamp (12 px or more) per H^2 above this is wallpaper
FLAT_MIN = 0.14               # H^2: a smooth single-tone area inside an object this large is flat
GROUND_PLANE_MIN = 1.0        # H^2: an area this large may be a ground plane, judged by the ground band
PIECE_HUE = 32.0              # RGB units off grey: a ground piece's hue may differ this much from its ground
#                               (light turns a floor warm in a pool and cool in the shade, as Eastward's 06 does)
PIECE_SPREAD = 2.5            # a ground piece may sit this many of Eastward's piece spreads (std) off its ground


def hud_mask(native: np.ndarray) -> np.ndarray:
    """Overlay text (HP, Glint, the debug label) in the top and bottom bands: near-white or
    near-black glyph clusters. Masked so it is never reviewed as art."""
    h, s, v = hsv(native)
    m = np.zeros(v.shape, bool)
    band = max(12, native.shape[0] // 20)
    for sl in (slice(0, band), slice(native.shape[0] - band, native.shape[0])):
        t = (v[sl] > 0.85) & (s[sl] < 0.15)
        m[sl] = ndi.binary_dilation(t, iterations=3)
    return m


def objects_mask(native, ground):
    k = keys(native, 32)
    g = np.isin(k, ground)
    o = ~g
    o = ndi.binary_opening(o, structure=np.ones((3, 3)))
    return o


def shadows(native, H, ignore) -> list[Finding]:
    k, ground = ground_palette(native)
    g = np.isin(k, ground)
    h, s, v = hsv(native)
    # the lawn: the single most common colour; a cast shadow is the lawn two ramp steps down
    vals, cnt = np.unique(k, return_counts=True)
    top = vals[np.argmax(cnt)]
    lm = k == top
    lh, ls, lv = float(np.median(h[lm])), float(np.median(s[lm])), float(np.median(v[lm]))
    ratio = v / max(lv, 1e-3)
    dh = np.abs(((h - lh) + 180) % 360 - 180)
    w = water_mask(native)
    cand = (ratio >= 0.45) & (ratio <= 0.86) & (dh <= 40) & ~w & ~ignore & (s >= 0.15)
    cand = ndi.binary_closing(cand, structure=np.ones((3, 3)), iterations=2)
    obj = objects_mask(native, ground) & ~cand & ~w
    # the body of a cast shadow: what survives an opening of 0.07 H (tufts, contact strips
    # and the shade lines under objects drop away)
    rr = max(2, int(0.1 * H))
    disk = np.hypot(*np.mgrid[-rr:rr + 1, -rr:rr + 1]) <= rr
    cand = ndi.binary_opening(cand, structure=disk)
    lab, regs = regions(cand, min_area=int(SHADOW_MIN_AREA * H * H))
    fs = []
    for lid, sl, area in regs:
        x0, y0, x1, y1 = slice_box(sl)
        comp = lab == lid
        bw = x1 - x0
        if bw < 0.5 * H:
            continue
        # compact blobs only (a shaded forest floor band is not a cast shadow)
        if area / max(1, bw * (y1 - y0)) < 0.45:
            continue
        ring = ndi.binary_dilation(comp, iterations=3) & ~comp
        # an island on the lawn: most of what surrounds it is open ground
        island = float(np.isin(k[ring], ground).mean())
        touch = ring & obj
        head = np.zeros_like(touch)
        head[:, :x0 + bw // 2] = True
        head[:y0 + (y1 - y0) // 2] |= True
        cols = np.nonzero((touch & head).any(0))[0]
        contact = len(cols) / max(1, bw)
        if island < 0.5:
            continue
        if contact < SHADOW_CONTACT:
            fs.append(Finding('logic.shadow_orphan', 'fault', (x0, y0, x1, y1),
                              f'a cast shadow {bw} px wide ({bw / H:.1f} H) with nothing standing at its head: what '
                              f'touches it covers {contact:.0%} of its width',
                              'every cast shadow starts at the foot of the thing that casts it and matches its size and '
                              'shape, thrown east and down (eastward-edges.md 7); remove the blob or give it its caster',
                              score=contact, threshold=SHADOW_CONTACT, subject='shadow'))
    return fs


def artefacts(native, H, ignore) -> list[Finding]:
    """Thin isolated lines: a component at most 2 px thick and at least LINE_MIN_LEN H long,
    in a colour unlike the ground around it, touching no larger object; and dotted lines:
    four or more small dots stacked on one column with even gaps."""
    k, ground = ground_palette(native)
    g = np.isin(k, ground)
    h, s, v = hsv(native)
    fs = []
    # dots and thin strokes of a saturated or bright colour off the ground palette
    foreign = ~g & ~ignore & (s >= 0.45) & (v >= 0.55) & ~water_mask(native)
    fam = D.family_map(native)
    foreign &= ~np.isin(fam, (1,))          # not greens (tufts, leaves)
    # a dotted or thin stray line: bright off-palette marks joined along one axis into a stroke
    # at most 0.1 H wide and at least 0.6 H long, broken (20 to 85 % filled), with nothing of
    # its colour beside it (JPEG texture, tufts and flowers never line up like this)
    lab0, regs0 = regions(foreign, min_area=1, connectivity=2)
    dots = np.zeros_like(foreign)
    for lid, sl, a in regs0:
        if a <= 0.02 * H * H:
            dots[sl] |= lab0[sl] == lid
    darkish = (v < 0.3)
    for axis in (0, 1):
        st = np.ones((7, 1), bool) if axis == 0 else np.ones((1, 7), bool)
        joined = ndi.binary_closing(dots, structure=st)
        lab, regs = regions(joined, min_area=int(0.1 * H), connectivity=2)
        for lid, sl, area in regs:
            bx = slice_box(sl)
            ln = (bx[3] - bx[1]) if axis == 0 else (bx[2] - bx[0])
            wd = (bx[2] - bx[0]) if axis == 0 else (bx[3] - bx[1])
            if ln < 0.7 * H or wd > 0.15 * H:
                continue
            comp = lab == lid
            fill = (dots & comp).sum() / max(1, comp.sum())
            if not 0.2 <= fill <= 0.85:
                continue
            # belongs to nothing: what surrounds it is ground (or its shade), not an object's edge
            ring = ndi.binary_dilation(comp, iterations=2) & ~comp
            iso = (g[ring] | (~darkish[ring] & (s[ring] < 0.45))).mean()
            if iso < 0.6:
                continue
            # dotted: the marks break into at least three gaps of 2 px or more along the stroke
            prof = (dots & comp).any(1 if axis == 0 else 0)
            prof = prof[(bx[1] if axis == 0 else bx[0]):(bx[3] if axis == 0 else bx[2])]
            gaps = [len(r) for r in ''.join('1' if p else '0' for p in prof).split('1') if len(r) >= 2]
            if len(gaps) < 3:
                continue
            # drawn, not compressed: one or two exact colours make most of the dots
            kk = keys(native, 32)[dots & comp]
            _, cc = np.unique(kk, return_counts=True)
            if np.sort(cc)[::-1][:2].sum() < 0.6 * cc.sum():
                continue
            f = int(np.bincount(fam[dots & comp]).argmax())
            fs.append(Finding('logic.stray_line', 'fault', (bx[0] - 3, bx[1] - 3, bx[2] + 3, bx[3] + 3),
                              f'a broken {D.FAMILY[f]} line {ln} px long and {wd} px wide that belongs to nothing: '
                              'a stray dotted line', 'find the sprite that draws it (a trunk, a rope, a post?) and draw it '
                              'as one solid shaded form, or remove it', score=float(ln / H), threshold=0.7,
                              subject='artefact'))
    return fs


def repetition(native, H, ignore) -> list[Finding]:
    """Stamped ground dressing: the lit blades of tufts (green or straw pixels 12 L above the
    local field) whose exact shape recurs. More than REPEAT_DENSITY exact repeats per H^2 of
    the picture is wallpaper (Matt: 'uniform repeated grass'). Blades of 12 px or more and 4
    rows or taller only (small specks repeat by chance). The approved pilot golden measures
    0.0, Eastward 0.0 to 0.7, the woodland and Crossroads ground pictures 1.6 and 2.1."""
    L = lum(native)
    fam = D.family_map(native)
    loc = ndi.median_filter(L, size=int(0.3 * H) | 1)
    blade = (L > loc + 12) & np.isin(fam, (1, 7)) & ~ignore
    lab, regs = regions(blade, min_area=4, connectivity=2)
    sig = {}
    for lid, sl, a in regs:
        b = slice_box(sl)
        if a > 0.03 * H * H or a < 12 or b[3] - b[1] < 4:
            continue
        m = (lab == lid)[sl]
        sig.setdefault((m.shape, m.tobytes()), []).append(slice_box(sl))
    reps = [v for v in sig.values() if len(v) >= 3]
    n = sum(len(v) for v in reps)
    area = native.shape[0] * native.shape[1] / (H * H)
    density = n / max(area, 1e-6)
    fs = []
    if density > REPEAT_DENSITY and n >= REPEAT_MIN:
        top = max(reps, key=len)
        fs.append(Finding('detail.repetition', 'fault', (0, 0, native.shape[1], native.shape[0]),
                          f'{n} tuft blades repeat an exact stamp ({len(reps)} stamps, the commonest {len(top)} times): '
                          f'{density:.1f} repeats per H^2 (the pilot golden 0.0, Eastward 0.0 to 0.7); the grass reads as wallpaper',
                          'ground is a calm field with a few soft patches and clumped tufts of varied size, shape and tone, '
                          'denser at edges and under things, sparse where people walk; draw tufts from several designs '
                          'and vary each (eastward-edges.md 5.5)', score=density, threshold=REPEAT_DENSITY,
                          subject='ground dressing', extra=dict(stamps=len(reps), repeats=n,
                                                                commonest=[list(b) for b in top[:12]])))
    return fs


def flats(native, H, ignore) -> list[Finding]:
    k, ground = ground_palette(native)
    g = np.isin(k, ground)
    L = lum(native)
    sm = D.smooth_mask(L) & ~g & ~ignore
    fam = D.family_map(native)
    sm &= ~np.isin(fam, (0,))
    kk = keys(native, 32)
    # paths and open dirt are ground: large brown fields without an outline
    dirt = ndi.binary_closing(np.isin(fam, (3, 7)), structure=np.ones((3, 3)), iterations=2)
    dl, dregs = regions(dirt, min_area=int(1.5 * H * H))
    path = np.zeros_like(dirt)
    L2 = lum(native)
    for lid, sl, a in dregs:
        comp = dl == lid
        edge = ndi.binary_dilation(comp, iterations=1) & ~comp
        if (L2[edge] < 60).mean() < 0.3:
            path |= comp
    sm &= ~path & ~np.isin(fam, (2,))
    fs = []
    planes = ground_planes(native, H, ignore)
    lab, regs = regions(sm, min_area=int(FLAT_MIN * H * H))
    for lid, sl, a in regs:
        comp = lab == lid
        b = slice_box(sl)
        # one tone: the smooth patch is (nearly) one colour
        v, c = np.unique(kk[comp], return_counts=True)
        if c.max() < 0.8 * a:
            continue
        f = int(np.bincount(fam[comp]).argmax())
        name = D.FAMILY[f]
        # a calm patch of ground (bordered mostly by the ground palette) is meant to be calm
        ring = ndi.binary_dilation(comp, iterations=2) & ~comp
        if g[ring].mean() >= 0.5:
            continue
        if planes[comp].mean() > 0.5 or piece_of_ground(native, comp, g, H):   # a flag of a calm floor
            continue
        sev = 'fault'
        det = 'detail.water_flat' if f == 2 else 'detail.flat'
        fs.append(Finding(det, sev, b,
                          f'a flat {name} area of one tone, {a} px ({a / (H * H):.2f} H^2)',
                          'draw the material and its form: 4 to 5 tones of its ramp in clusters (planks, staves, '
                          'courses, ripples), a lit top plane and a shaded side', score=a / (H * H), threshold=FLAT_MIN,
                          subject=name))
    return fs


def mesh(native, H, ignore) -> list[Finding]:
    """Canopies as contour mesh: in large foliage regions, the share of 1 px dark strokes."""
    fam = D.family_map(native)
    fol = np.isin(fam, (1, 0)) & ~ignore
    fol = ndi.binary_closing(fol, iterations=2)
    fol = ndi.binary_opening(fol, structure=np.ones((5, 5)))
    lab, regs = regions(fol, min_area=int(0.6 * H * H))
    fs = []
    for lid, sl, a in regs:
        comp = lab == lid
        td = D.thin_dark(native, comp)
        if td > 0.17:
            b = slice_box(sl)
            fs.append(Finding('detail.mesh', 'fault', b,
                              f'foliage drawn as a contour mesh: {td:.0%} of it is 1 px dark strokes',
                              'build crowns from leaf clusters lit at the top left, with dark gaps between them and no '
                              'outline round every blob (art-style.md 4)', score=td, threshold=0.17, subject='canopy'))
    return fs


INTERIOR = {'cellar', 'interior', 'undercroft', 'cave', 'dungeon', 'house', 'shop'}


def flat_objects(native, H, ignore) -> list[Finding]:
    """Objects drawn as flat shapes: a thing that is not ground (off the screen's ground
    palette, at least 0.06 H^2 after a 3 x 3 opening) painted in four tones or fewer with
    two of them covering three quarters of it. Eastward's shots hold 0 to 3 a screen (JPEG
    counted fairly at 16 levels), the pilot golden 2, Matt's flagged Undercroft 52. A ground plane
    (at least 1 H^2 and 0.5 H across) is judged by Eastward's ground band instead (calm_ground)."""
    k, ground = ground_palette(native)
    g = np.isin(k, ground)
    obj = ndi.binary_opening(~g & ~ignore, structure=np.ones((3, 3)))
    kk = keys(native, 16)
    lab, regs = regions(obj, min_area=int(0.06 * H * H))
    out = []
    for lid, sl, a in regs:
        c = lab == lid
        v, cnt = np.unique(kk[c], return_counts=True)
        tones = int((cnt >= 3).sum())
        top2 = float(np.sort(cnt)[::-1][:2].sum() / a)
        if tones <= 4 and top2 >= 0.75 and not calm_ground(native, c, H) and not piece_of_ground(native, c, g, H):
            out.append((a, slice_box(sl), tones, top2))
    out.sort(key=lambda t: -t[0])
    fs = []
    for a, b, tones, top2 in out[:12]:
        fs.append(Finding('detail.flat', 'fault', b,
                          f'a thing drawn flat: {tones} tones, two cover {top2:.0%} ({a / (H * H):.2f} H^2)',
                          'give it form and material: a lit top plane, a mid front and a dark side (a cylinder: a '
                          'highlight band and a core shadow), occlusion where it meets the floor, its texture in '
                          'clusters', score=top2, threshold=0.75, subject='flat object'))
    return fs


def falloff(native, H, ignore, biome) -> list[Finding]:
    """Interiors need light: pools from the light sources, falloff into the corners and
    occlusion at wall bases. The spread of the luminance blurred at 0.5 H, against its mean:
    Eastward's interiors 0.39 to 0.56, Matt's flagged Undercroft 0.26."""
    if biome not in INTERIOR:
        return []
    L = lum(native)
    bl = ndi.gaussian_filter(L, 0.5 * H)
    fo = float(bl.std() / max(bl.mean(), 1))
    if fo < 0.33:
        return [Finding('detail.no_falloff', 'fault', (0, 0, native.shape[1], native.shape[0]),
                        f'the interior is lit evenly: large-scale light varies only {fo:.2f} of its mean (Eastward\'s '
                        'interiors 0.39 to 0.56)', 'light the room from its sources: pools under lamps and openings, '
                        'falloff into corners, a dark occlusion band along every wall base and under objects, warm '
                        'light against cool shade (art-style.md, Eastward: light as a material)', score=fo,
                        threshold=0.33, subject='lighting')]
    return []


def debug_overlay(native, H, ignore) -> list[Finding]:
    """A flat-coloured translucent polygon laid over the art (a telegraph or hitbox drawn as a
    debug shape): a saturated orange or red region of at least 1.5 H^2, almost perfectly convex
    (solidity 0.95 and up). Roofs, autumn trees and lamplight in Eastward are far less regular."""
    from scipy.spatial import ConvexHull
    h, s, v = hsv(native)
    fs = []
    for lo, hi, name in ((12, 38, 'orange'), (340, 360, 'red'), (0, 12, 'red')):
        m = (h >= lo) & (h <= hi) & (s >= 0.5) & (v >= 0.5) & ~ignore
        m = ndi.binary_fill_holes(ndi.binary_closing(m, iterations=2))
        lab, regs = regions(m, min_area=int(1.5 * H * H))
        for lid, sl, a in regs:
            ys, xs = np.nonzero(lab == lid)
            try:
                sol = a / ConvexHull(np.c_[xs, ys]).volume
            except Exception:
                continue
            if sol >= 0.95:
                fs.append(Finding('detail.debug_overlay', 'fault', slice_box(sl),
                                  f'a flat {name} polygon ({a / (H * H):.1f} H^2, solidity {sol:.2f}) laid over the art: '
                                  'it reads as a debug shape, not part of the world',
                                  'draw the telegraph in the world\'s language: cracks or glowing runes spreading on the '
                                  'floor, dust lifting, a ground shadow growing; finite, readable, and under reduced '
                                  'motion still clear', score=float(sol), threshold=0.95, subject='overlay'))
    return fs


def flat_lines(native, H, ignore) -> list[Finding]:
    """A long ruler line of one colour (a channel, a pipe, a rail drawn as a 1 to 3 px stroke):
    at least 1.2 H straight along x or y, one 16-level colour for 90 % of it, standing out from
    both sides by 25 L, with no shading along it."""
    L = lum(native)
    kk = keys(native, 16)
    fs = []
    run = int(1.2 * H)
    for axis in (0, 1):
        A = L if axis == 0 else L.T
        K = kk if axis == 0 else kk.T
        IG = ignore if axis == 0 else ignore.T
        for y in range(3, A.shape[0] - 3):
            row = K[y]
            same = (row[1:] == row[:-1])
            # runs of one colour
            x = 0
            n = len(row)
            while x < n - run:
                if not same[x]:
                    x += 1
                    continue
                x0 = x
                while x < n - 1 and same[x]:
                    x += 1
                if x - x0 >= run and not IG[y, x0:x].any():
                    seg = A[y, x0:x + 1]
                    for th in (1, 2, 3):
                        above = A[y - 1 - (th - 1) - 1:y - (th - 1), x0:x + 1].mean() if y - th - 1 >= 0 else seg.mean()
                        below = A[y + th:y + th + 1, x0:x + 1].mean()
                        if abs(seg.mean() - above) >= 25 and abs(seg.mean() - below) >= 25:
                            box = (x0, y - 2, x + 1, y + 3) if axis == 0 else (y - 2, x0, y + 3, x + 1)
                            fs.append(Finding('detail.flat_line', 'fault', box + (int(row[x0]),) if False else box,
                                              f'a ruler line of one colour {x - x0} px long ({(x - x0) / H:.1f} H)',
                                              'draw the thing it stands for with depth: a channel cut into the floor with '
                                              'a lit lip, a dark inner wall and water lower than the rim; a pipe with a '
                                              'highlight and joints', score=(x - x0) / H, threshold=1.2,
                                              subject='line', extra=dict(key=int(row[x0]), axis=axis, at=y,
                                                                         span=[x0, x])))
                            break
                x += 1
    # a lone line: rails, courses, kerbs and planks come in parallel sets of one colour
    lone = []
    for f in fs:
        e = f.extra
        par = [g for g in fs if g is not f and g.extra['axis'] == e['axis'] and g.extra['key'] == e['key']
               and 2 <= abs(g.extra['at'] - e['at']) <= 0.4 * H
               and min(g.extra['span'][1], e['span'][1]) - max(g.extra['span'][0], e['span'][0]) > 0.3 * H]
        if not par and f.score >= 2.5:
            lone.append(f)
    from .core import merge_findings
    return merge_findings(lone, 0.1)


def void(native, H, ignore) -> list[Finding]:
    """The camera showing outside the world: a large flat near-black field (at least 5 % of the
    screen) that is not the HUD (art-faults rule 13: the camera never shows outside the world)."""
    h, s, v = hsv(native)
    m = (v < 0.06) & ~ignore
    lab, regs = regions(m, min_area=int(0.05 * native.shape[0] * native.shape[1]))
    return [Finding('logic.void', 'blocker', slice_box(sl),
                    f'the screen shows {a / m.size:.0%} empty black outside the world',
                    'clamp the camera to the zone bounds from the first frame (snap it to the spawn before damping) and '
                    'draw the world past every edge the camera can reach', score=a / m.size, threshold=0.05,
                    subject='camera') for lid, sl, a in regs]


def review_screen(native: np.ndarray, H: float, biome: str = '', subject: str = 'screen', ignore=None,
                  experimental: bool = False) -> dict:
    if ignore is None:
        ignore = hud_mask(native)
    fs = []
    fs += W.check_banks(native, H)
    fs += W.check_falls(native, H)
    fs += W.check_bridges(native, H)
    fs += void(native, H, ignore)
    fs += artefacts(native, H, ignore)
    fs += repetition(native, H, ignore)
    fs += flats(native, H, ignore)
    fs += flat_objects(native, H, ignore)
    fs += flat_lines(native, H, ignore)
    fs += falloff(native, H, ignore, biome)
    fs += debug_overlay(native, H, ignore)
    if experimental:
        # image-only shadow and mesh guesses: too many false positives on Eastward to gate on
        # (calibrate.py); the scene gate checks shadows from the zone's own data instead
        fs += shadows(native, H, ignore)
        fs += mesh(native, H, ignore)
    fs = merge_findings(fs, iou=0.3)
    return dict(subject=subject, H=H, findings=[f.to_json() for f in fs], _objs=fs)
