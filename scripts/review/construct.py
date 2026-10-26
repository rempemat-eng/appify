"""Construction and common-sense checks on one sprite: what holds it up, how big it is next
to a person, what it is made of, where it grows, what repeats.

world-rules.md 6.9 ("nothing floats or hangs from nothing"), 6.7 (no rows of identical
props), size-guide.md, art-faults.md 5 and 10, and Matt's 25 Oct examples: bushes standing on
three brown stilts, a beech crown floating over its trunk, a birch trunk drawn as a dotted
yellow line, agaves in a temperate wood, head-sized mushrooms in a row.
"""
from __future__ import annotations

import json
import os
import re

import numpy as np
from scipy import ndimage as ndi

from .core import Finding, REPO, lum, regions, slice_box, keys
from . import detail as D
from .objects import tips

GUIDE = json.load(open(os.path.join(REPO, 'scripts', 'art', 'size_guide.json')))
ADULT_WORLD = GUIDE['unit']['adult']        # 25 world px

# asset names -> size-guide kinds (the guide's own kind when the name is one)
ALIASES = {
    'oak': 'broadleaf', 'beech': 'broadleaf', 'hollow_tree': 'veteran_tree', 'pine': 'conifer',
    'mossy_log': 'log', 'flower_tub': 'tub', 'crates': 'crate_stack', 'sacks': 'sack', 'hay': 'haystack',
    'lantern_dark': 'lamp', 'lantern_lit': 'lamp', 'kit_lantern': 'lantern_post', 'notice_board': 'tall_sign',
    'forest_bench': 'bench', 'holly': 'bush', 'bramble': 'bush', 'grindstone': 'small_machine',
    'anvil': 'small_machine', 'waystone': 'standing_stone', 'standing_stone_b': 'standing_stone',
    'standing_stone_low': 'standing_stone', 'coal': 'pile', 'debris': 'pile', 'woodpile': 'woodpile',
    'fern': 'fern', 'boulder': 'boulder', 'stump': 'stump', 'stall': 'stall', 'handcart': 'handcart',
}
# kinds the guide lacks, in world px (adult 25): (h range, w range, reason)
EXTRA = {
    'mushroom': ((1, 3.5), (1, 4), 'a woodland mushroom is 5 to 20 cm: ankle high at most (15 px a metre)'),
    'mushroom_ring': ((1, 4.5), (8, 60), 'a ring of mushrooms is ankle high'),
}
# forms that only grow in some biomes
FORMS = {
    'succulent_rosette': ({'desert', 'arid', 'canyon', 'oasis', 'dry_coast'},
                          'a rosette of thick, straight, pointed leaves is an agave, aloe or yucca: a dry-country plant'),
}
TEMPERATE = {'woodland', 'meadow', 'valley', 'crossroads', 'garden', 'hollow', 'village', 'temperate'}


def kind_of(name: str) -> str:
    base = re.sub(r'(_\d+|_[a-d])$', '', name)
    base = re.sub(r'_(damage|lit|dark|choked|rubble)$', lambda m: m.group(0) if base in ALIASES else '', base) or base
    if name in ALIASES:
        return ALIASES[name]
    if base in ALIASES:
        return ALIASES[base]
    if base in GUIDE['kinds'] or base in EXTRA:
        return base
    return base


def guide_size(kind: str):
    if kind in EXTRA:
        return EXTRA[kind]
    k = GUIDE['kinds'].get(kind)
    if not k:
        return None
    return (tuple(k['h']), tuple(k['w']), k.get('reason', ''))


def bbox(a):
    ys, xs = np.nonzero(a)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


# ------------------------------------------------------------------------------------------
SCATTER = ('debris', 'rubble', 'smoke', 'fx/', 'pile', 'coal', 'crater', '_damage')


def floating_parts(alpha, H, subject):
    """Parts of a sprite that hang in the air: an opaque component (at least 3 % of the sprite)
    that neither reaches the ground line nor rests on another component below it."""
    fs = []
    if any(k in subject for k in SCATTER):
        return fs          # pieces lying about or puffs of smoke: separate by nature
    total = alpha.sum()
    x0, y0, x1, y1 = bbox(alpha)
    # a gap across the whole sprite: rows with (almost) nothing in them between an upper mass
    # and the part that stands on the ground (a crown hovering over its trunk)
    rows = alpha.sum(1)
    empty = [y for y in range(y0 + 1, y1 - max(2, int(0.05 * H))) if rows[y] <= 2]
    if empty:
        yg = min(empty)
        above = alpha[:yg].sum()
        if above >= 0.1 * total:
            run = [y for y in empty if y >= yg]
            gap = 1
            while yg + gap in empty:
                gap += 1
            if gap >= 2:
                bx = bbox(alpha[:yg])
                fs.append(Finding('logic.floating_part', 'blocker', (bx[0], bx[1], bx[2], yg + gap),
                                  f'{subject}: the upper {above / total:.0%} of the sprite hovers {gap} px above the rest: '
                                  'nothing joins it to what should hold it up',
                                  'join it to its support: a crown sits on its trunk and covers the trunk top, a roof on '
                                  'its posts, a bucket on a rope (world-rules.md 6.9)', score=float(gap), threshold=2,
                                  subject=subject, extra={'needs_alpha': True}))
                return fs
    lab, regs = regions(alpha, min_area=1, connectivity=2)
    if len(regs) < 2:
        return fs
    ground = y1 - max(2, int(0.04 * H))
    for lid, sl, a in regs:
        if a < 0.1 * total:
            continue
        b = slice_box(sl)
        if b[3] >= ground:
            continue
        comp = lab == lid
        # anything opaque just below its lowest pixels, column by column?
        below = 0
        for x in range(b[0], b[2]):
            ys = np.nonzero(comp[:, x])[0]
            if len(ys):
                y = ys.max()
                seg = alpha[y + 1:y + 5, x] & ~comp[y + 1:y + 5, x]
                below += int(seg.any())
        if below < 2:
            fs.append(Finding('logic.floating_part', 'blocker', b,
                              f'{subject}: a part ({a} px, {a / total:.0%} of the sprite) hangs in the air, '
                              f'{(y1 - b[3])} px above the ground line, touching nothing below',
                              'join it to what holds it up: a crown sits on its trunk and covers the trunk top, '
                              'a bucket hangs from a rope on a windlass, a sign from a bracket (world-rules.md 6.9)',
                              score=float(y1 - b[3]), threshold=0, subject=subject, extra={'needs_alpha': True}))
    return fs


def stilts(rgb, alpha, H, subject):
    """A mass standing on separate thin legs: the bottom band holds two or more narrow runs of
    wood under a mass at least three times wider (Matt: 'bushes standing on three brown stilts')."""
    x0, y0, x1, y1 = bbox(alpha)
    fam = D.family_map(rgb)
    if (alpha & (fam == 1)).sum() < 0.5 * alpha.sum():
        return []                       # posts under a bench or a fence are meant
    y = y1 - 1
    legs = []
    while y > y0:
        runs = _runs(alpha[y])
        if len(runs) >= 2 and all(r[1] - r[0] <= 0.15 * H for r in runs):
            legs.append((y, runs))
            y -= 1
        else:
            break
    best = None
    # the legs: the bottom rows where the outline splits into thin separate runs (stems, not lace)
    while legs and sum(r[1] - r[0] for r in legs[-1][1]) < 0.6 * sum(r[1] - r[0] for r in legs[0][1]):
        legs.pop()
    if len(legs) >= max(3, int(0.05 * H)):
        yt = legs[-1][0]
        runs = legs[0][1]
        legw = sum(r[1] - r[0] for r in runs)
        rows_above = [np.nonzero(alpha[yy])[0] for yy in range(max(y0, yt - int(0.4 * H)), yt)]
        above = max([int(r[-1] - r[0] + 1) for r in rows_above if len(r)] or [0])
        woody = np.isin(fam[legs[0][0], alpha[legs[0][0]]], (0, 3, 4, 9)).mean()
        if above >= 3 * legw and woody >= 0.5:
            best = (yt, runs, above, legw)
    if best is None:
        return []
    band = y1 - best[0]
    y, runs, above, legw = best
    return [Finding('logic.stilts', 'fault', (x0, y - band, x1, y1),
                    f'{subject}: the mass stands on {len(runs)} separate thin legs ({legw} px of legs under a '
                    f'{above} px wide mass)',
                    'a bush grows from the ground: let the foliage come down to a dark, grassed base with only a '
                    'stem or two glimpsed in the shade, and a contact shadow under it (no stilts)',
                    score=float(len(runs)), threshold=2, subject=subject, extra={'needs_alpha': True})]


def _runs(row):
    r = []
    x = 0
    n = len(row)
    while x < n:
        if row[x]:
            s = x
            while x < n and row[x]:
                x += 1
            r.append((s, x))
        else:
            x += 1
    return r


def dotted(rgb, alpha, H, subject):
    """A part drawn as a broken column of bright dots (Matt: a birch trunk as a stray dotted
    yellow line): saturated, light, non-green marks joined along one axis into a stroke at least
    0.4 H long and at most 0.15 H wide, broken by three or more gaps."""
    from .core import hsv
    h, s_, v = hsv(rgb)
    fam = D.family_map(rgb)
    marks = alpha & (s_ >= 0.45) & (v >= 0.55) & ~np.isin(fam, (1, 2))
    fs = []
    for axis in (0, 1):
        st = np.ones((7, 1), bool) if axis == 0 else np.ones((1, 7), bool)
        joined = ndi.binary_closing(marks, structure=st)
        lab, regs = regions(joined, min_area=6, connectivity=2)
        for lid, sl, a in regs:
            b = slice_box(sl)
            ln = (b[3] - b[1]) if axis == 0 else (b[2] - b[0])
            wd = (b[2] - b[0]) if axis == 0 else (b[3] - b[1])
            if ln < 0.4 * H or wd > 0.15 * H:
                continue
            comp = lab == lid
            fill = (marks & comp).sum() / max(1, comp.sum())
            prof = (marks & comp).any(1 if axis == 0 else 0)
            prof = prof[(b[1] if axis == 0 else b[0]):(b[3] if axis == 0 else b[2])]
            gaps = [r for r in ''.join('1' if q else '0' for q in prof).split('1') if len(r) >= 2]
            ring = ndi.binary_dilation(comp, iterations=2) & ~comp
            loose = float((~alpha[ring]).mean()) if ring.any() else 0.0
            if 0.2 <= fill <= 0.9 and len(gaps) >= 3 and loose >= 0.4:
                fs.append(Finding('logic.dotted_line', 'fault', b,
                                  f'{subject}: a part drawn as a broken line of bright dots ({ln} px, {len(gaps)} gaps): '
                                  'it reads as a stray dotted line, not a solid thing',
                                  'draw the part as one solid, outlined, shaded form (a trunk with bark, lit left, dark '
                                  'right, joined to its crown) or remove it', score=float(len(gaps)), threshold=3,
                                  subject=subject, extra={'needs_alpha': True}))
    return fs


def scale(alpha, H, kind, subject, density=3.0):
    g = guide_size(kind)
    if not g:
        return []
    (h0, h1), (w0, w1), why = g
    x0, y0, x1, y1 = bbox(alpha)
    hw = (y1 - y0) / density
    ww = (x1 - x0) / density
    tol = GUIDE.get('tolerance', 2)
    fs = []
    if hw > h1 + tol or hw < h0 - tol:
        fs.append(Finding('logic.scale', 'fault' if (hw > 1.25 * h1 + tol or hw < 0.75 * h0 - tol) else 'polish',
                          (x0, y0, x1, y1),
                          f'{subject}: {hw:.0f} world px tall ({hw / ADULT_WORLD:.2f} of an adult); the size guide gives '
                          f'{h0} to {h1} for a {kind} ({why})',
                          f'redraw it {h0} to {h1} world px tall ({h0 * density:.0f} to {h1 * density:.0f} texels at density '
                          f'{density:g}) and stand it next to Bramble to check', score=hw, threshold=float(h1), subject=subject))
    return fs


def mushrooms(rgb, alpha, H, subject, density=3.0):
    """Individual mushrooms: a cap (red or tan) over a pale stem. Each must be ankle high, and
    three or more identical ones in a row are a planted grid, not a ring that grew. Only for
    assets named as mushrooms (windows and roof tiles look like caps too)."""
    if 'mush' not in subject:
        return []
    from .core import hsv
    fam = D.family_map(rgb)
    sat = hsv(rgb)[1]
    cap = alpha & (np.isin(fam, (4, 8)) | ((fam == 3) & (sat >= 0.45)))
    lab, regs = regions(cap, min_area=4)
    caps = []
    for lid, sl, a in regs:
        b = slice_box(sl)
        # a stem: pale pixels right under the cap
        below = alpha[b[3]:min(alpha.shape[0], b[3] + int(0.25 * H)), b[0]:b[2]]
        from .core import hsv
        _, ss, vv = hsv(rgb[b[3]:min(alpha.shape[0], b[3] + int(0.25 * H)), b[0]:b[2]])
        pale = (ss < 0.4) & (vv >= 0.6)
        stem_rows = (below & pale).any(1)
        if stem_rows.sum() >= 2:
            stem_end = b[3] + int(np.nonzero(stem_rows)[0].max()) + 1
            caps.append((b, stem_end, ((lab == lid)[sl]).tobytes() + bytes(str((lab == lid)[sl].shape), 'ascii')))
    fs = []
    if len(caps) < 2:
        return fs
    hs = [(se - b[1]) for b, se, _ in caps]
    big = [h for h in hs if h / density > EXTRA['mushroom'][0][1] + 1]
    xs0 = min(c[0][0] for c in caps); ys0 = min(c[0][1] for c in caps)
    xs1 = max(c[0][2] for c in caps); ys1 = max(c[1] for c in caps)
    if big:
        fs.append(Finding('logic.scale', 'fault', (xs0, ys0, xs1, ys1),
                          f'{subject}: {len(big)} of {len(caps)} mushrooms stand {np.median(big) / density:.0f} world px tall '
                          f'({np.median(big) / H:.2f} H): head-sized next to a person',
                          'mushrooms are ankle high: at most 3 to 4 world px with the cap, in clusters of different sizes '
                          'and ages (size-guide.md)', score=float(np.median(big) / H), threshold=0.06, subject=subject))
    # rows: caps whose tops line up
    tops = sorted(c[0][1] for c in caps)
    rows = []
    for t in tops:
        same = [c for c in caps if abs(c[0][1] - t) <= 1]
        if len(same) >= 3:
            rows.append(len(same))
    widths = [c[0][2] - c[0][0] for c in caps]
    from collections import Counter
    stamps = Counter(c[2] for c in caps)
    same_cap = max(stamps.values())
    if rows or same_cap >= 3 or (np.std(widths) <= 1 and len(caps) >= 4):
        fs.append(Finding('logic.prop_row', 'fault', (xs0, ys0, xs1, ys1),
                          f'{subject}: {len(caps)} mushrooms from {len(stamps)} cap stamps (one used {same_cap} times), '
                          f'{max(rows) if rows else 0} on one baseline: copies set out in rows, not a ring that grew',
                          'grow them as a cluster or an irregular ring: varied sizes, ages and lean, some half hidden in '
                          'grass, none on a shared baseline (world-rules.md 6.7)', score=float(max(rows) if rows else 0),
                          threshold=3, subject=subject))
    return fs


def biome_form(rgb, alpha, H, subject, biome):
    fam = D.family_map(rgb)
    if (alpha & (fam == 1)).sum() < 0.6 * alpha.sum():
        return []
    x0, y0, x1, y1 = bbox(alpha)
    if (y1 - y0) > 0.9 * H:
        return []
    sub = alpha[y0:y1, x0:x1]
    t = tips(sub, prominence=0.18)
    if t >= 4 and 0.35 <= sub.mean() <= 0.75:
        allowed, why = FORMS['succulent_rosette']
        if biome and biome not in allowed:
            return [Finding('logic.biome', 'fault', (x0, y0, x1, y1),
                            f'{subject}: a succulent rosette ({t} thick pointed leaves from one base) in a {biome} biome: {why}',
                            'in a temperate wood draw a fern (arching fronds of small leaflets, soft tips), foxgloves, '
                            'bracken or a low bush; keep rosettes for the desert (world-rules.md 10)',
                            score=float(t), threshold=4, subject=subject)]
    return []


def crown_holes(rgb, alpha, H, subject):
    """A crown drawn as outlined blobs with the ground showing between them (contour mesh)."""
    fam = D.family_map(rgb)
    fol = alpha & np.isin(fam, (0, 1))
    if (alpha & (fam == 1)).sum() < 0.3 * H * H:
        return []
    r = max(2, int(0.05 * H))
    p = r + 1
    filled = ndi.binary_fill_holes(ndi.binary_closing(np.pad(fol, p), structure=np.ones((3, 3)), iterations=r))[p:-p, p:-p]
    holes = 1 - fol.sum() / max(1, filled.sum())
    if holes > 0.15:
        x0, y0, x1, y1 = bbox(filled)
        return [Finding('detail.mesh', 'fault', (x0, y0, x1, y1),
                        f'{subject}: the foliage is a see-through mesh: {holes:.0%} of the crown is gaps between '
                        'outlined blobs',
                        'paint the crown as one mass of leaf clusters (Eastward): lit clumps on top, a darker band under '
                        'them, a dark interior showing through narrow gaps, no ground visible through the crown and no '
                        'outline round every blob (art-style.md 4)', score=float(holes), threshold=0.15, subject=subject, extra={'needs_alpha': True})]
    return []


WATER_HOLDERS = ('well', 'trough', 'tub', 'bucket', 'fountain', 'basin', 'pond', 'pool', 'cistern', 'channel')


def holds_water(subject: str) -> bool:
    return any(k in subject for k in WATER_HOLDERS)


def glyphs(rgb, alpha, H, subject):
    """A painted mark or sign face drawn as a flat saturated shape on its body: it reads as an
    interface icon stuck on the art (Matt: 'a waystone reading as a UI block')."""
    if holds_water(subject):
        return []
    fs = []
    for f, pm, pb in D.parts(rgb, alpha, H):
        if f not in (2, 4, 8):
            continue
        m = D.part_metrics(rgb, pm, H)
        if m['area_h'] < 0.008:
            continue
        from .core import hsv
        sat = float(hsv(rgb)[1][pm].mean())
        if m['tones'] <= 3 and m['flat'] >= 0.45 and sat >= 0.35 and (f != 4 or sat >= 0.5):
            fs.append(Finding('detail.glyph', 'fault', pb,
                              f'{subject}: a flat {D.FAMILY[f]} mark of {m["tones"]} tones on the body reads as an interface '
                              'icon, not something carved, painted or worn into the material',
                              'cut or paint it into the surface: a carved groove with a lit lower lip and a dark upper '
                              'edge, worn paint with chips, moss in the cut; tone it to the material and the light',
                              score=m['flat'], threshold=0.45, subject=subject))
    return fs


def construction(rgb, alpha, H, subject, kind):
    """Kind-specific construction: a well's bucket needs a windlass with a crank to be raised."""
    fs = []
    if kind == 'well' and 'choked' not in subject:
        fam = D.family_map(rgb)
        wood = alpha & np.isin(fam, (3, 0))
        cols = wood.sum(0)
        x0, y0, x1, y1 = bbox(alpha)
        # the beam: the widest wooden row in the upper two thirds
        rows = [(int(wood[y].sum()), y) for y in range(y0, y0 + (y1 - y0) * 2 // 3)]
        if rows:
            w, yb = max(rows)
            xs = np.nonzero(wood[yb])[0]
            post_out = [xs.min(), xs.max()]
            # a crank: wood or dark metal sticking out past the beam end and down (a handle)
            band = alpha[max(0, yb - 3):yb + int(0.15 * H)]
            left = band[:, :max(0, post_out[0] - 1)].sum()
            right = band[:, post_out[1] + 2:].sum()
            if max(left, right) < 6:
                fs.append(Finding('logic.construction', 'fault', (x0, max(0, yb - 6), x1, yb + int(0.2 * H)),
                                  f'{subject}: the bucket hangs from a plain beam: no windlass drum and no crank, so '
                                  'nothing could wind it up',
                                  'draw a windlass: a round drum on the beam with the rope wrapped on it, an iron crank '
                                  'handle out past one post, and a rope of 2 px with a lit side down to the bucket',
                                  score=float(max(left, right)), threshold=6, subject=subject))
    return fs


def water_shape(rgb, alpha, H, subject):
    """Water seen from above inside a well, trough or tub: a flat half disc (a straight top edge
    and nothing above it but dark) or a plain rectangle of one tone."""
    if not holds_water(subject):
        return []
    from .core import hsv
    hh, ss, vv = hsv(rgb)
    w = alpha & (hh >= 180) & (hh <= 250) & (ss >= 0.08) & (vv >= 0.2)
    lab, regs = regions(w, min_area=int(0.01 * H * H))
    fs = []
    for lid, sl, a in regs:
        b = slice_box(sl)
        comp = lab == lid
        top_row = comp[b[1]]
        width = b[2] - b[0]
        straight_top = top_row.sum() >= 0.7 * width
        rows = comp[b[1]:b[3]].sum(1)
        inner = rows[1:-1] if len(rows) > 3 else rows
        rect = inner.std() / max(1, inner.mean()) < 0.08 or ((b[3] - b[1]) <= 0.15 * H and width >= 8 * (b[3] - b[1]))
        k = keys(rgb, 16)[comp]
        tones = len(np.unique(k))
        if ((straight_top and tones <= 4) or (rect and tones <= 6)) and width >= 0.12 * H:
            shape = 'rectangle' if rect else 'half disc'
            fs.append(Finding('detail.water_flat', 'fault', b,
                              f'{subject}: the water is a flat {shape} of {tones} tones with a ruler-straight edge',
                              'show depth: the opening as an ellipse from above with its inner wall (lit on the far side, '
                              'shaded on the near), the water lower than the rim, darker under the near rim, a 1 px light '
                              'line and a glint (eastward-edges.md 5.3)', score=float(tones), threshold=4, subject=subject))
    return fs


def object_light(rgb, alpha, H, subject):
    L = lum(rgb)
    fam = D.family_map(rgb)
    m = alpha & (fam != 0) & ndi.binary_erosion(alpha, iterations=1)
    if m.sum() < 0.04 * H * H:
        return []
    ys, xs = np.nonzero(m)
    A = np.vstack([xs - xs.mean(), ys - ys.mean(), np.ones(len(xs))]).T
    coef, *_ = np.linalg.lstsq(A, L[m], rcond=None)
    gx = coef[0] * H
    if gx > 30:
        x0, y0, x1, y1 = bbox(alpha)
        return [Finding('detail.light', 'fault', (x0, y0, x1, y1),
                        f'{subject}: lit from the right: luminance rises {gx:.0f} L per H to the east',
                        'relight from the upper left: lit faces west and up, shade east and down, the cast shadow east',
                        score=float(gx), threshold=30, subject=subject)]
    return []


def repeated_parts(rgb, alpha, H, subject):
    """Identical copies inside one sprite (the same mushroom, tuft or plank stamped again)."""
    lab, regs = regions(alpha, min_area=max(6, int(0.004 * H * H)), connectivity=2)
    if len(regs) < 3:
        return []
    k = keys(rgb, 32)
    sigs = {}
    for lid, sl, a in regs:
        comp = (lab == lid)[sl]
        sig = (comp.shape, comp.tobytes(), np.where(comp, k[sl], -1).tobytes())
        sigs.setdefault(sig, []).append(slice_box(sl))
    fs = []
    for sig, bs in sigs.items():
        if len(bs) >= 3:
            b = (min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs))
            fs.append(Finding('detail.repetition', 'fault', b,
                              f'{subject}: {len(bs)} pixel-identical copies of one part',
                              'vary every copy: size, lean, tone, a missing or extra detail; nature never stamps',
                              score=float(len(bs)), threshold=3, subject=subject))
    return fs


ROUND = ('stump', 'pillar', 'column', 'barrel', 'post', 'lamp', 'lantern', 'urn', 'churn', 'keg', 'tower', 'trunk')


def cylinder(rgb, alpha, H, subject):
    """Round upright things (pillars, barrels, posts, lamp feet, urns) need cylinder shading
    across their width: a highlight band left of centre and a core shadow toward the right,
    spanning at least 25 L. A flat or banded profile reads as a cut-out."""
    base = subject.split('/')[-1]
    if not any(k in base for k in ROUND):
        return []
    fam = D.family_map(rgb)
    body = alpha & (fam != 0) & ndi.binary_erosion(alpha, iterations=1)
    if body.sum() < 0.03 * H * H:
        return []
    L = lum(rgb)
    ys = np.nonzero(body.any(1))[0]
    # the widest band of rows: the shaft
    widths = body.sum(1)
    rows = widths >= 0.7 * widths.max()
    xs = np.nonzero(body[rows].any(0))[0]
    if len(xs) < 6:
        return []
    prof = np.array([L[rows, x][body[rows, x]].mean() if body[rows, x].any() else np.nan for x in range(xs.min(), xs.max() + 1)])
    prof = prof[~np.isnan(prof)]
    rng = float(prof.max() - prof.min())
    n = len(prof)
    hi, lo = int(np.argmax(prof)), int(np.argmin(prof))
    ok = rng >= 25 and hi < 0.6 * n and lo > 0.5 * n
    if not ok:
        x0, y0, x1, y1 = bbox(body)
        return [Finding('detail.volume', 'fault', (x0, y0, x1, y1),
                        f'{subject}: no cylinder shading across the shaft (luminance spread {rng:.0f} L, brightest at '
                        f'{hi / max(1, n - 1):.0%} of its width, darkest at {lo / max(1, n - 1):.0%})',
                        'shade it as a cylinder lit from the upper left: a highlight band left of centre, the body, a core '
                        'shadow toward the right edge with a little reflected light at the rim, an elliptical top face '
                        'and occlusion where it meets the floor', score=rng, threshold=25, subject=subject)]
    return []
