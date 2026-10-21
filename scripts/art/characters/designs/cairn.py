"""Cairn, the standing stone of the woodland circle that woke: three design options
(Claude J lane, batch 2).

Main question: how a standing stone becomes a body.

    A  Menhir: one tall weathered slab is torso and head together, a face carved by
       weather in its top third, a ring carved on the chest, boulder shoulders and fists
       and two boulder feet. Moss caps the crown; a fern grows behind his left ear.
    B  Cairn stack: a pile of rounded stones (feet, hips, belly, chest, head) under a
       wide flat capstone that shades his eyes like a brim, arms of three stacked
       pebbles, moss in the joints between the stones.
    C  Moss-mantled giant: a broad boulder body with a smaller head sunk between the
       shoulders, a mantle of moss over the shoulders (not a hood: the head stays bare),
       long arms of stacked slabs that hang to the knee, short pillar legs.

Views: S idle, E idle, W idle (W is drawn with its own light, never mirrored pixels)
and the S key pose of his fidget (each option tries one of the three beats). Design
sheets are review material; production frames come from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/cairn.py
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/cairn-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/cairn.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'cairn')

W, H = 80, 80
AX, AY = 40, 74          # foot anchor: soles fill row 73, their outline lands on row 74
SOLE = AY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
SKIP = ('ink', '_edge', '_lit')


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def base_fam(f):
    return sk.family_of(f) if f else f


def hsh(x, y, seed=0):
    """A fixed hash for placing texture clusters (deterministic, no RNG state)."""
    return ((x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)) & 0xFFFF


def ell(fig, cx, cy, rx, ry):
    return {p for p in fig.ellipse(cx, cy, rx, ry) if p[1] <= SOLE}


def box(fig, x0, y0, x1, y1, knock=0):
    return fig.rect(min(x0, x1), y0, max(x0, x1), y1, knock=knock)


def sib_clusters(fig, mask, fam, seed=0, rate=4):
    """Texture as 2-4 px sibling clusters at the same tone (house-style 4): warm on the
    lit half, cool on the shaded half. They add shape without value noise."""
    mask = set(mask)
    if not mask:
        return
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    for y in range(min(ys) + 1, max(ys), 3):
        for x in range(min(xs) + 1 + (y // 3) % 2 * 2, max(xs), 4):
            h = hsh(x, y, seed)
            if h % rate:
                continue
            blk = [(x, y), (x + 1, y)] + ([(x, y + 1), (x + 1, y + 1)] if h & 16 else [])
            if not all(p in mask for p in blk):
                continue
            ts = {tone(fig, p) for p in blk}
            fs = {fam_at(fig, p) for p in blk}
            if len(ts) != 1 or fs != {fam}:
                continue
            t = ts.pop()
            if t is None or t >= 5 or t <= 0:
                continue
            sib = '_warm' if (x - cx) + (y - cy) < 0 else '_cool'
            if fam.endswith(sib):
                sib = ''
            for p in blk:
                fig.put(p[0], p[1], base_fam(fam) + sib, t)


def rock(fig, mask, fam='stone', keep=None, dark=0, glint=True, sib=True, seed=0):
    """A rounded stone (house-style 3, 4): the lit cap is a disc offset to the upper left,
    the dark crescent the outside of a larger offset disc, so the terminator follows the
    form; the underside row is a tone down again; a two-pixel glint at the top left."""
    mask = set(mask)
    if not mask:
        return mask
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 3
        if (u + 0.42) ** 2 + (v + 0.5) ** 2 < 0.40:
            t = 4
        if (u + 0.28) ** 2 + (v + 0.32) ** 2 > 1.05:
            t = 2
        if (x, y + 1) not in mask and u > -0.35:
            t = min(t, 1 if u > 0.15 else 2)
        fig.put(x, y, fam, max(1, t - dark))
    if sib and len(mask) > 30:
        sib_clusters(fig, mask, fam, seed)
    if glint and not dark and len(mask) > 16:
        p0 = min(mask, key=lambda p: (0.55 * (p[0] + 0.5 - cx) / rx + 0.85 * (p[1] + 0.5 - cy) / ry, p[0], p[1]))
        q = (p0[0] + 1, p0[1]) if (p0[0] + 1, p0[1]) in mask else (p0[0], p0[1] + 1)
        for p in (p0, q):
            fig.put(p[0], p[1], fam, 5)
            if keep is not None:
                keep.add(p)
    return mask


def slab(fig, mask, fam='stone', keep=None, dark=0, glint=True, sib=True, seed=0, band=0.2):
    """A slab or a column (house-style 3, 4): a lit top plane, a lit west face, the south
    face as body, the east face shaded, the underside row a tone down, as vertical bands
    (one hard step each), a two-pixel glint at the top left."""
    mask = set(mask)
    if not mask:
        return mask
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    for (x, y) in mask:
        xl, xr = min(rows[y]), max(rows[y])
        rel = (x - xl) / max(1, xr - xl)
        t = 3
        if rel < band:
            t = 4
        elif rel > 0.84:
            t = 2
        top = min(cols[x])
        if y - top < 2 and rel <= 0.84:
            t = 4
        if y == max(cols[x]):
            t = 1 if rel > 0.3 else 2
        fig.put(x, y, fam, max(1, t - dark))
    if sib and len(mask) > 30:
        sib_clusters(fig, mask, fam, seed)
    if glint and not dark:
        y0 = min(rows)
        x0 = min(rows[y0])
        pts = [(x0 + 1, y0), (x0 + 2, y0)] if (x0 + 2, y0) in mask else [(x0, y0), (x0, y0 + 1)]
        for p in pts:
            if p in mask:
                fig.put(p[0], p[1], fam, 5)
                if keep is not None:
                    keep.add(p)
    return mask


def path4(pts):
    """A 4-connected pixel path through the points (no diagonal-only steps, so a 1 px
    stroke never breaks into lone pixels)."""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        x, y = x0, y0
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(1, n + 1):
            tx = round(x0 + (x1 - x0) * i / n)
            ty = round(y0 + (y1 - y0) * i / n)
            if tx != x and ty != y:
                out.append((tx, y))
            x, y = tx, ty
            out.append((x, y))
    res = [pts[0]]
    for p in out:
        if p != res[-1]:
            res.append(p)
    return res


def crack(fig, pts):
    """A weathering crack: the groove a dark run (tone 1 of the stone it cuts), its
    lower lip one tone lit (it faces up, into the light)."""
    pp = path4(pts)
    for (x, y) in pp:
        f = fam_at(fig, (x, y))
        if f and f not in SKIP and base_fam(f) == 'stone':
            fig.put(x, y, f, 1)
    for (x, y) in pp:
        q = (x, y + 1)
        f = fam_at(fig, q)
        if q not in pp and f and base_fam(f) == 'stone' and (tone(fig, q) or 0) in (2, 3):
            fig.put(q[0], q[1], f, tone(fig, q) + 1)


def lichen(fig, x, y, shape=((0, 0), (1, 0), (0, 1), (1, 1))):
    """A lichen crust: a 2-4 px cluster one tone up on the warm sibling."""
    for dx, dy in shape:
        p = (x + dx, y + dy)
        f = fam_at(fig, p)
        if f and base_fam(f) == 'stone' and (tone(fig, p) or 0) in (2, 3):
            fig.put(p[0], p[1], 'stone_warm', tone(fig, p) + 1)


# Moss lobe stamps (house foliage recipe at small size): a = warm lit cap, b = body,
# c = cool shade, d = its deepest corner.
LOBE_BIG = ('.aab.',
            'abbcb',
            'bbccc',
            '.ccd.')
LOBE_SMALL = ('aa.',
              'abc',
              '.cd')
LOBE_TONE = {'a': ('leaf_warm', 4), 'b': ('leaf', 3), 'c': ('leaf_cool', 2), 'd': ('leaf_cool', 1)}


def moss(fig, lobes, shift=0):
    """Moss as clumped lobes, painted back (top) to front (bottom), each with a lit cap
    at its upper left and a dark crescent at its lower right."""
    mine = set()
    for (cx, cy, r) in sorted(lobes, key=lambda l: (l[1], l[0])):
        st = LOBE_BIG if r >= 2.5 else LOBE_SMALL
        ox = round(cx) - len(st[0]) // 2
        oy = round(cy) - len(st) // 2
        for j, row in enumerate(st):
            for i, ch in enumerate(row):
                if ch == '.':
                    continue
                f, t = LOBE_TONE[ch]
                fig.put(ox + i, oy + j, f, max(1, t + shift))
                mine.add((ox + i, oy + j))
    return mine


LOBE_FLAT = ('.aaab.',
             'abbbbc',
             '.bccd.')


def moss_mass(fig, mask, seed=0, step=(4, 3), dark=0):
    """A mass of moss (the mantle, a cushion on a cap): a shaded base, then lobes tiled
    through it back to front, each with a warm lit cap and a cool crescent, the lobes at
    the mass's lower right a tone down. The lower edge scallops where lobes hang over."""
    mask = set(mask)
    if not mask:
        return mask
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    for (x, y) in mask:
        ng = 0.55 * (x - cx) / rx + 0.85 * (y - cy) / ry
        fig.put(x, y, 'leaf' if ng < 0.3 else 'leaf_cool', max(1, 2 - dark))
    row = 0
    for y in range(min(ys) + 1, max(ys) + 1, step[1]):
        off = (row % 2) * (step[0] // 2) + (seed % 2)
        for x in range(min(xs) + off, max(xs) + 1, step[0]):
            if (x, y) not in mask:
                continue
            ng = 0.55 * (x - cx) / rx + 0.85 * (y - cy) / ry
            st = LOBE_FLAT if hsh(x, y, seed) % 3 == 0 else LOBE_BIG
            sh = (-1 if ng > 0.45 else 0) - dark
            ox, oy = x - len(st[0]) // 2, y - len(st) // 2
            for j, r in enumerate(st):
                for i, ch in enumerate(r):
                    if ch == '.':
                        continue
                    p = (ox + i, oy + j)
                    if p not in mask and not (j == len(st) - 1 and (p[0], p[1] - 1) in mask):
                        continue
                    f, t = LOBE_TONE[ch]
                    fig.put(p[0], p[1], f, max(1, t + sh))
        row += 1
    return mask


def fern(fig, spine, width=2.0, dark=0, keep=None):
    """A fern frond as a blade (grass): a 4-connected midrib (tone 2) with leaflets that
    swell every third pixel, so the edge is notched; the upper-left side of the blade lit
    (4), the other side 3, the tip warm. Never a wire."""
    stem = path4(spine)
    n = len(stem)
    blade = {}
    for i, (sx, sy) in enumerate(stem):
        t = i / max(1, n - 1)
        r = width * 0.75 * (1 - t) ** 0.6 + 0.4 + (1.3 * (1 - 0.5 * t) if i % 3 == 1 and t < 0.85 else 0)
        for y in range(int(sy - r) - 1, int(sy + r) + 2):
            for x in range(int(sx - r) - 1, int(sx + r) + 2):
                if math.hypot(x - sx, y - sy) <= r:
                    if (x, y) not in blade:
                        blade[(x, y)] = i
    for (x, y), i in blade.items():
        sx, sy = stem[i]
        lit = (x - sx) + (y - sy) < 0
        t = (4 if lit else 3) - dark
        fig.put(x, y, 'grass' if lit else 'grass_cool', max(1, t))
    for (x, y) in stem[:-2]:
        fig.put(x, y, 'grass', max(1, 2 - dark))
    tx, ty = stem[-1]
    fig.put(tx, ty, 'grass_warm', max(1, 4 - dark))
    return set(blade)


def rim(fig, mask, under):
    """A joint (house-style 4): where a part lies over another part, its edge on that
    side drops a tone (two on the shaded east and south), so the joint reads as a recess."""
    for (x, y) in mask:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in mask or q not in under:
                continue
            f, t = fig.px.get((x, y), (None, None))
            if not f or f in SKIP or not isinstance(t, int) or (x, y) in fig.fixed:
                continue
            fig.put(x, y, f, max(1, min(t, 2) if dx == -1 or dy == -1 else 1))
            break


def over(fig, painter, mask, *a, **kw):
    """Paint a part over what is there and darken its edge where it meets that part."""
    under = set(fig.px)
    m = painter(fig, mask, *a, **kw)
    rim(fig, m, under - m)
    return m


def drip(fig, x, y0, n, n2=None):
    """Moss running down a stone: two columns, the left a tone lit, the right shaded."""
    n2 = n - 1 if n2 is None else n2
    for i in range(n):
        fig.put(x, y0 + i, 'leaf', 3 if i < n - 1 else 2)
    for i in range(n2):
        fig.put(x + 1, y0 + i, 'leaf_cool', 2)


def frond(fig, pts, fam='grass', dark=0, step=2):
    """A fern frond: a 4-connected stem (tone 2) with paired leaflets every other pixel,
    each two pixels long, set across the stem (lit 4 on the upper or left side, 3 on the
    other), shortening to the tip."""
    stem = path4(pts)
    n = len(stem)
    for (x, y) in stem:
        fig.put(x, y, fam, max(1, 2 - dark))
    for i, (x, y) in enumerate(stem):
        if i < 2 or i % step or i >= n - 1:
            continue
        px_, py_ = stem[i - 1]
        vert = abs(y - py_) >= abs(x - px_)
        ln = 2 if i < n - 3 else 1
        for k in range(1, ln + 1):
            if vert:
                a, b = (x - k, y), (x + k, y)
            else:
                a, b = (x, y - k), (x, y + k)
            if a not in stem and fig.px.get(a) is None:
                fig.put(a[0], a[1], fam, max(1, 4 - dark))
            if b not in stem and fig.px.get(b) is None:
                fig.put(b[0], b[1], fam, max(1, 3 - dark))
    tip = stem[-1]
    fig.put(tip[0], tip[1], fam, max(1, 3 - dark))
    return stem


def eye(fig, x, y, keep, w=3, look=0, shut=False):
    """A carved eye socket (ink) with a faint glowflora light inside: 1 x 2 at its centre,
    or 2 x 1 low at one side when he looks down that way."""
    if shut:
        for i in range(w):
            fig.put(x + i, y + 1, 'ink', 0)
        return
    for i in range(w):
        for j in range(2):
            fig.put(x + i, y + j, 'ink', 0)
    if look == 0:
        gx = x + (w - 1) // 2 if w > 2 else (x + 1 if w == 2 else x)
        fig.glow(gx, y, 'glowflora', 4)
        fig.glow(gx, y + 1, 'glowflora', 3)
    elif look in (-1, 1):   # down to that side
        gx = x if look < 0 else x + w - 2
        fig.glow(gx, y + 1, 'glowflora', 4)
        fig.glow(gx + 1, y + 1, 'glowflora', 3)
    else:                   # 'f': forward in profile, the light at the front column
        gx = x + w - 1 if look == 2 else x
        fig.glow(gx, y, 'glowflora', 4)
        fig.glow(gx, y + 1, 'glowflora', 3)


def recolour(fig, mask, fam_from, fam_to=None, dt=0, lo=1, hi=4):
    for p in mask:
        f, t = fig.px.get(p, (None, None))
        if f and f not in SKIP and isinstance(t, int) and base_fam(f) == fam_from:
            fig.put(p[0], p[1], fam_to or f, max(lo, min(hi, t + dt)))


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most
    common neighbour (deterministic tie-break), unless it is an eye, a glint or a nail."""
    for _ in range(2):
        changes = {}
        for p in sorted(fig.px):
            v = fig.px[p]
            if p in keep or p in fig.fixed or v[0] in SKIP:
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if all(n != v for n in nb):
                pool = [n for n in nb if n[0] not in SKIP]
                if not pool:
                    continue
                changes[p] = max(sorted(set(pool), key=str), key=pool.count)
        for p, v in changes.items():
            fig.px[p] = v


def finish(fig, keep):
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


def Ux(d):
    return lambda dx: AX + d * dx


# =====================================================================================
# Option A: Menhir. One slab is torso and head; the face is carved by weather.
# =====================================================================================
def a_slab_mask(fig, d=0):
    """S: a tall slab, rounded at the top, widening a little to the foot.
    E/W: the same slab side-on, thinner, with the face stepping out at the front."""
    m = set()
    for y in range(20, 63):
        if d == 0:
            c = 40 - (62 - y) * 0.02
            hw = 10.5 * math.sqrt(max(0.0, 1 - ((29 - y) / 9.6) ** 2)) if y < 29 else 10.5 + (y - 29) * 0.06
            xl, xr = round(c - hw), round(c + hw) - 1
        else:
            hw = 7.4 * math.sqrt(max(0.0, 1 - ((28 - y) / 8.6) ** 2)) if y < 28 else 7.4 + (y - 28) * 0.04
            back, front = -hw - 0.3, hw
            # the face steps out at the front: brow, nose, a notch for the mouth, the chin
            if 26 <= y <= 27:
                front += 1
            if 29 <= y <= 33:
                front += 2 if 30 <= y <= 32 else 1
            if y == 35:
                front -= 1
            a, b = AX + d * back, AX + d * front
            xl, xr = round(min(a, b)), round(max(a, b)) - 1
        for x in range(xl, xr + 1):
            m.add((x, y))
    return m


def a_face_s(fig, keep, look=0, brow_dy=0, mouth='smile'):
    by = 27 + brow_dy
    for x in range(32, 48):
        fig.put(x, by, 'stone', 4)
        fig.put(x, by + 1, 'stone_cool', 1)
    eye(fig, 33, 29, keep, w=3, look=look)
    eye(fig, 44, 29, keep, w=3, look=look)
    # the nose: a ridge, lit west, shaded east, a shadow under it
    for y in range(29, 35):
        fig.put(39, y, 'stone', 4)
        fig.put(40, y, 'stone', 3)
        fig.put(41, y, 'stone', 2)
    for x in (39, 40, 41, 42):
        fig.put(x, 35, 'stone_cool', 1)
    if mouth == 'smile':
        for x in range(37, 43):
            fig.put(x, 37, 'stone_cool', 1)
        for x in (35, 36, 43, 44):
            fig.put(x, 36, 'stone_cool', 1)
        for x in range(37, 43):
            fig.put(x, 38, 'stone_warm', 4)
    else:   # a small 'o': he has noticed something
        for x in (39, 40):
            for y in (37, 38):
                fig.put(x, y, 'stone_cool', 0)
        fig.put(39, 39, 'stone_warm', 4)
        fig.put(40, 39, 'stone_warm', 4)
    # cheek bumps under the eyes, lit on their tops
    for x in (33, 34):
        fig.put(x, 32, 'stone_warm', 4)
    for x in (45, 46):
        fig.put(x, 32, 'stone', 3)


def a_ring(fig, cx, cy, r=3.2):
    """The circle's mark carved on his chest: the groove dark at its upper left (in its
    own shadow), shaded at its lower right, a lit lip outside the lower right."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dd = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r - 1.0 <= dd < r:
                up = (x + 0.5 - cx) + (y + 0.5 - cy) < 0
                fig.put(x, y, 'stone_cool', 1 if up else 2)
            elif r <= dd < r + 0.9 and (x + 0.5 - cx) + (y + 0.5 - cy) > 1:
                fig.put(x, y, 'stone_warm', 4)


def cushion(mask, ybot, lift=2, slope=0.0):
    """The part of a stone's top where moss sits: the stone above `ybot` (lower on the
    shaded right by `slope` px per px), plus up to `lift` rows of moss piled on top."""
    mask = set(mask)
    cols = {}
    for (x, y) in mask:
        cols.setdefault(x, []).append(y)
    x0, x1 = min(cols), max(cols)
    out = set()
    for x, ys in cols.items():
        yb = ybot + slope * (x - x0)
        top = min(ys)
        out |= {(x, y) for y in ys if y <= yb}
        rel = (x - x0) / max(1, x1 - x0)
        if 0.1 < rel < 0.92:
            out.add((x, top - 1))
        if 0.25 < rel < 0.75:
            out.add((x, top - 2))
    return out


def a_crown_moss(fig, body, d=0):
    if d == 0:
        # moss keeps to the shaded crown: the lit upper left of the dome stays bare stone
        moss_mass(fig, {p for p in cushion(body, 21, slope=0.18) if (p[0] - 37) - 1.2 * (p[1] - 20) >= 0}, seed=1)
        drip(fig, 48, 24, 7, 5)
        drip(fig, 50, 24, 3, 2)
        drip(fig, 33, 22, 2, 1)
    else:
        U = Ux(d)
        moss_mass(fig, {p for p in cushion(body, 21, slope=0.15 * d)
                        if (p[0] - (AX - 3 * d)) * d * -1 - 1.2 * (p[1] - 20) >= -2 or p[1] >= 21}, seed=2)
        x = min(U(-7), U(-6))
        drip(fig, x, 23, 7, 5)


def a_fern(fig, d=0, dark=0):
    """The fern behind his LEFT ear: screen right in S, the far side in E, the near
    side in W. One anchor (the back of the head, ear height), one layer per facing."""
    if d == 0:
        fern(fig, [(49, 30), (52, 26), (54, 21), (54, 17)], dark=dark)
        fern(fig, [(50, 31), (54, 29), (57, 26), (59, 22)], width=1.6, dark=dark)
    else:
        U = Ux(d)
        fern(fig, [(U(-5), 29), (U(-8), 25), (U(-10), 20), (U(-10), 16)], dark=dark)
        fern(fig, [(U(-6), 30), (U(-10), 28), (U(-13), 25), (U(-15), 21)], width=1.6, dark=dark)


def option_a(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        rock(fig, ell(fig, 34.5, 68.5, 5.6, 5.4), 'stone_cool', keep, seed=1)
        rock(fig, ell(fig, 45.5, 68.5, 5.6, 5.4), 'stone_cool', keep, seed=2)
        a_fern(fig, 0)
        lift = 1 if view == 'Sf' else 0
        rock(fig, ell(fig, 28.5, 38.5 - lift, 4.6, 5.0), 'stone_warm', keep, seed=4)
        rock(fig, ell(fig, 51.5, 38.5, 4.6, 5.0), 'stone', keep, seed=6)
        body = over(fig, slab, a_slab_mask(fig), 'stone', keep, seed=3, band=0.16)
        a_ring(fig, 40, 47)
        crack(fig, [(47, 52), (46, 54), (46, 56), (45, 58)])
        crack(fig, [(33, 55), (35, 57)])
        lichen(fig, 34, 41)
        lichen(fig, 44, 55, ((0, 0), (1, 0), (2, 0)))
        lichen(fig, 37, 58, ((0, 0), (1, 0), (1, 1)))
        a_crown_moss(fig, body)
        moss(fig, [(45, 61, 2), (48, 61.5, 2)])          # moss in the low joint over the feet
        if view == 'S':
            a_face_s(fig, keep)
        else:   # fidget: a new tuft has grown on his right shoulder; he looks down at it
            a_face_s(fig, keep, look=-1, brow_dy=-1, mouth='o')
        over(fig, rock, ell(fig, 27, 50, 5.0, 4.6), 'stone', keep, seed=5)
        over(fig, rock, ell(fig, 53, 50, 5.0, 4.6), 'stone_cool', keep, seed=7)
        if view == 'Sf':
            moss(fig, [(25, 34, 2), (27.5, 33.5, 2)])
            for y in (30, 31, 32):                # the new sprout, two leaves
                fig.put(26, y, 'grass', 3)
            for (x, y, t) in ((24, 29, 4), (25, 29, 4), (25, 30, 4), (27, 29, 3), (28, 29, 3), (27, 30, 3)):
                fig.put(x, y, 'grass', t)
        return finish(fig, keep)
    d = 1 if view == 'E' else -1
    U = Ux(d)
    rock(fig, ell(fig, U(-3.5), 68.5, 5.4, 5.2), 'stone_cool', keep, dark=1, seed=1)
    rock(fig, ell(fig, U(-6.5), 49, 4.4, 4.4), 'stone', keep, dark=1, seed=2)
    if d == 1:
        a_fern(fig, d, dark=1)
    rock(fig, ell(fig, U(2), 68.5, 5.6, 5.4), 'stone_cool', keep, seed=3)
    m = slab(fig, a_slab_mask(fig, d), 'stone', keep, seed=4, band=0.2)
    # profile face: brow ledge lit on top, shadow under it, the nose lit on top
    fx = max(p[0] for p in m if p[1] == 30) if d == 1 else min(p[0] for p in m if p[1] == 30)
    browx = max(p[0] for p in m if p[1] == 26) if d == 1 else min(p[0] for p in m if p[1] == 26)
    for k in range(5):
        fig.put(browx - d * k, 26, 'stone', 4)
        fig.put(browx - d * k, 27, 'stone', 3 if k else 2)
        fig.put(browx - d * k, 28, 'stone_cool', 1)
    for k in range(3):
        fig.put(fx - d * k, 29, 'stone', 4)
        fig.put(fx - d * k, 30, 'stone', 3)
        fig.put(fx - d * k, 33, 'stone_cool', 1)
    fig.put(fx, 31, 'stone', 3 if d == -1 else 2)
    fig.put(fx, 32, 'stone', 2)
    ex = fx - d * 4
    eye(fig, min(ex, ex - d), 29, keep, w=2, look=2 if d == 1 else 3)
    mx = max(p[0] for p in m if p[1] == 36) if d == 1 else min(p[0] for p in m if p[1] == 36)
    for k in range(3):
        fig.put(mx - d * k, 35, 'stone_cool', 1)
    for k in range(2):
        fig.put(mx - d * k, 36, 'stone_warm', 4)
    fig.put(fx - d * 3, 32, 'stone_warm', 4)   # cheek
    fig.put(fx - d * 4, 32, 'stone_warm', 4)
    crack(fig, [(U(-3), 50), (U(-2), 53), (U(-2), 56)])
    lichen(fig, round(U(-4)), 42)
    a_crown_moss(fig, m, d)
    moss(fig, [(U(-5), 61, 2), (U(-2), 61.5, 2)])
    if d == -1:
        a_fern(fig, d)
    over(fig, rock, ell(fig, U(-1), 39, 4.4, 4.8), 'stone_warm', keep, seed=5)
    over(fig, rock, ell(fig, U(0.5), 50, 4.8, 4.4), 'stone', keep, seed=6)
    return finish(fig, keep)


# =====================================================================================
# Option B: Cairn stack. Rounded stones piled up, a capstone for a brim.
# =====================================================================================
CAP = ((-11, 20), (-4, 18.5), (7, 19), (12, 21), (12.5, 24), (5, 25), (-10, 24.5), (-12, 23))


def b_cap(fig, keep, d, dy=0, ox=0):
    """The capstone: a flat, uneven stone laid on his head, a little longer at the front
    in profile; lit on its top plane, a shaded east end, a dark underside."""
    sx = (lambda x: AX + x - 0.5) if d == 0 else Ux(d)
    pts = [(sx(x + (0 if d else ox)), y + dy) for (x, y) in CAP] if d else \
          [(AX + x * 0.98, y + dy) for (x, y) in ((-12, 20), (-4, 18.5), (5, 18.5), (11.5, 20), (12, 23.5),
                                                    (4, 24.5), (-6, 24.5), (-12.5, 23))]
    m = fig.poly(pts)
    slab(fig, m, 'stone_cool', keep, seed=11, band=0.12)
    moss_mass(fig, {p for p in cushion(m, min(p[1] for p in m) + 1, lift=2)}, seed=5)
    return m


def b_brim_shadow(fig, head, cap):
    """The capstone throws a hard shadow on the face: two rows under its lower edge."""
    low = {}
    for (x, y) in cap:
        low[x] = max(low.get(x, y), y)
    for (x, y) in head:
        if x in low and fam_at(fig, (x, y)) and base_fam(fam_at(fig, (x, y))) == 'stone':
            k = y - low[x]
            if k == 1:
                fig.put(x, y, 'stone_cool', 1)
            elif k == 2:
                fig.put(x, y, 'stone_cool', 2)


def b_arms_s(fig, keep, dy):
    for side, fams in ((-1, ('stone_cool', 'stone', 'stone_warm')), (1, ('stone', 'stone_cool', 'stone'))):
        for i, (ox, oy, rx, ry) in enumerate(((13.5, 41, 3.8, 3.4), (15, 47, 3.7, 3.3), (15.5, 53.5, 4.5, 4.0))):
            over(fig, rock, ell(fig, 40 + side * ox, oy + dy, rx, ry), fams[i], keep, seed=20 + i + side)


def option_b(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        f = view == 'Sf'
        dh, dc, db = (3, 2, 1) if f else (0, 0, 0)
        rock(fig, ell(fig, 33.5, 70.5, 6.2, 3.7), 'stone_cool', keep, seed=1)
        rock(fig, ell(fig, 46.5, 70.5, 6.2, 3.7), 'stone', keep, seed=2)
        over(fig, rock, ell(fig, 40, 63.5 + (0.4 if f else 0), 10.2, 4.5 - (0.4 if f else 0)), 'stone_cool', keep, seed=3)
        moss(fig, [(45, 59.5, 2), (48, 60, 2)])
        over(fig, rock, ell(fig, 40, 53 + db, 12.6 + (0.8 if f else 0), 7.0 - (0.6 if f else 0)), 'stone', keep, seed=4)
        crack(fig, [(46, 51 + db), (47, 53 + db), (49, 54 + db)])
        lichen(fig, 32, 51 + db)
        moss(fig, [(32, 47 + dc, 2), (35, 47.5 + dc, 2)])
        over(fig, rock, ell(fig, 40, 43 + dc, 10.4, 4.9 - (0.3 if f else 0)), 'stone_warm', keep, seed=5)
        b_arms_s(fig, keep, dc)
        fern(fig, [(49, 29 + dh), (52, 25 + dh), (54, 21 + dh), (55, 16 + dh)])
        fern(fig, [(50, 30 + dh), (54, 28 + dh), (57, 25 + dh), (59, 21 + dh)], width=1.6)
        head = over(fig, rock, ell(fig, 40, 30.5 + dh, 11, 8.4), 'stone_warm', keep, seed=6, glint=False)
        cap = b_cap(fig, keep, 0, dy=dh)
        b_brim_shadow(fig, head, cap)
        drip(fig, 50, 24 + dh, 3, 2)
        ey = 28 + dh
        if f:   # settling: eyes shut in content, a pebble or two shaken loose
            eye(fig, 34, ey, keep, shut=True)
            eye(fig, 43, ey, keep, shut=True)
            for x in range(38, 42):
                fig.put(x, 34 + dh, 'stone_cool', 1)
            fig.put(36, 33 + dh, 'stone_cool', 1)
            fig.put(37, 33 + dh, 'stone_cool', 1)
            fig.put(42, 33 + dh, 'stone_cool', 1)
            fig.put(43, 33 + dh, 'stone_cool', 1)
            for (px, py) in ((23, 71), (56, 71)):
                rock(fig, box(fig, px, py, px + 2, py + 1), 'stone', keep, glint=False, sib=False)
                fig.put(px, py, 'stone', 4)
                fig.put(px + 1, py, 'stone', 4)
        else:
            eye(fig, 34, ey, keep)
            eye(fig, 43, ey, keep)
            for x in range(38, 42):
                fig.put(x, 34, 'stone_cool', 1)
                fig.put(x, 35, 'stone_warm', 4)
        for x in (33, 34):       # cheek tops lit, below the brim shadow
            fig.put(x, 31 + dh, 'stone_warm', 4)
        return finish(fig, keep)
    d = 1 if view == 'E' else -1
    U = Ux(d)
    rock(fig, ell(fig, U(-3), 70.5, 5.6, 3.6), 'stone_cool', keep, dark=1, seed=1)
    rock(fig, ell(fig, U(-7.5), 47, 3.3, 3.1), 'stone', keep, dark=1, seed=2)
    rock(fig, ell(fig, U(-8), 53.5, 4.0, 3.6), 'stone', keep, dark=1, seed=3)
    if d == 1:
        fern(fig, [(U(-6), 28), (U(-9), 24), (U(-11), 20), (U(-11), 16)], dark=1)
        fern(fig, [(U(-7), 29), (U(-11), 27), (U(-14), 24), (U(-16), 20)], width=1.6, dark=1)
    rock(fig, ell(fig, U(2.5), 70.5, 6.2, 3.7), 'stone', keep, seed=4)
    over(fig, rock, ell(fig, U(-0.5), 63.5, 8.2, 4.5), 'stone_cool', keep, seed=5)
    moss(fig, [(U(-5), 59.5, 2), (U(-2), 60, 2)])
    over(fig, rock, ell(fig, U(0), 53, 9.6, 7.0), 'stone', keep, seed=6)
    crack(fig, [(U(-3), 51), (U(-4), 54), (U(-6), 55)])
    over(fig, rock, ell(fig, U(0.5), 43, 8.2, 4.9), 'stone_warm', keep, seed=7)
    head = over(fig, rock, ell(fig, U(1.5), 30.5, 9.2, 8.4), 'stone_warm', keep, seed=8, glint=False)
    # face step: a nose stone at the front, lit on top
    nose = over(fig, rock, ell(fig, U(10.5), 31, 2.0, 2.0), 'stone_warm', keep, glint=False, sib=False)
    cap = b_cap(fig, keep, d)
    b_brim_shadow(fig, head | nose, cap)
    drip(fig, min(U(-9), U(-8)), 25, 3, 2)
    eye(fig, min(U(6), U(7)), 28, keep, w=2, look=2 if d == 1 else 3)
    for k in range(3):
        fig.put(U(8) - d * k, 35, 'stone_cool', 1)
    fig.put(U(6), 31, 'stone_warm', 4)
    fig.put(U(5), 31, 'stone_warm', 4)
    if d == -1:
        fern(fig, [(U(-6), 28), (U(-9), 24), (U(-11), 20), (U(-11), 16)])
        fern(fig, [(U(-7), 29), (U(-11), 27), (U(-14), 24), (U(-16), 20)], width=1.6)
    for i, (ox, oy, rx, ry, fam) in enumerate(((0.5, 41, 3.8, 3.4, 'stone'), (1.5, 47, 3.7, 3.3, 'stone_cool'),
                                                (2, 53.5, 4.5, 4.0, 'stone'))):
        over(fig, rock, ell(fig, U(ox), oy, rx, ry), fam, keep, seed=30 + i)
    return finish(fig, keep)


# =====================================================================================
# Option C: Moss-mantled giant. A broad boulder, a small sunk head, slab arms.
# =====================================================================================
MANTLE_S = [(22, 36), (26, 31), (33, 31), (37, 33.5), (43, 33.5), (47, 31), (54, 31), (58, 36), (58, 40), (54.5, 42.5),
            (50, 39.5), (45, 41.5), (40, 40), (35, 41.5), (30, 39.5), (25.5, 42.5), (22, 40)]


def c_mantle_s(fig):
    m = moss_mass(fig, fig.poly(MANTLE_S), seed=3, step=(6, 4))
    drip(fig, 31, 40, 4, 3)
    drip(fig, 50, 41, 3, 2)
    return m


def c_arm_s(fig, side, keep, seeds):
    sx = (lambda x: x) if side < 0 else (lambda x: 79 - x)
    fams = ('stone_warm', 'stone', 'stone_cool') if side < 0 else ('stone', 'stone_cool', 'stone')
    for i, (x0, y0, x1, y1, kn) in enumerate(((19, 33, 25, 43, 1), (18, 44, 25, 53, 1), (17, 54, 25, 61, 2))):
        over(fig, slab, box(fig, sx(x0), y0, sx(x1), y1, knock=kn), fams[i], keep, seed=seeds + i, band=0.25)


def c_face_s(fig, head, keep, look=0, mouth='line'):
    """A heavy brow ledge, glowing sockets, a lump of a nose, a small mouth."""
    for x in range(33, 48):
        if (x, 24) in head:
            fig.put(x, 23, 'stone_warm', 4)
            fig.put(x, 24, 'stone_cool', 1)
    eye(fig, 34, 25, keep, w=3, look=look)
    eye(fig, 43, 25, keep, w=3, look=look)
    over(fig, rock, ell(fig, 40.5, 28.6, 2.0, 2.0), 'stone_warm', keep, glint=False, sib=False)
    fig.put(39, 27, 'stone_warm', 5)
    keep.add((39, 27))
    if mouth == 'o':
        for x in (39, 40, 41):
            fig.put(x, 32, 'stone_cool', 1)
        fig.put(38, 31, 'stone_cool', 1)
        fig.put(37, 31, 'stone_cool', 1)
    else:
        for x in range(38, 43):
            fig.put(x, 32, 'stone_cool', 1)


def option_c(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        for x0 in (31, 43):
            slab(fig, box(fig, x0, 60, x0 + 6, 69), 'stone_cool', keep, seed=x0, band=0.3)
        over(fig, rock, ell(fig, 33.5, 71, 5.6, 3.1), 'stone', keep, seed=1)
        over(fig, rock, ell(fig, 46.5, 71, 5.6, 3.1), 'stone_cool', keep, seed=2)
        torso = fig.poly([(27, 30), (53, 30), (57.5, 35), (56, 48), (51, 63), (29, 63), (24, 48), (22.5, 35)])
        over(fig, rock, torso, 'stone', keep, seed=3, glint=False)
        crack(fig, [(46, 47), (47, 50), (46, 53), (47, 55)])
        crack(fig, [(32, 52), (35, 53)])
        lichen(fig, 30, 45)
        lichen(fig, 41, 58, ((0, 0), (1, 0), (2, 0)))
        if view == 'S':
            c_arm_s(fig, -1, keep, 10)
        c_arm_s(fig, 1, keep, 20)
        moss(fig, [(46, 61.5, 2), (49, 61, 2)])
        fern(fig, [(47, 26), (50, 23), (52, 19), (52, 15)])
        fern(fig, [(48, 27), (51, 25), (54, 23), (57, 20)], width=1.6)
        head = over(fig, rock, ell(fig, 40, 26, 8.6, 8.2), 'stone_warm', keep, seed=4)
        moss(fig, [(38, 18.5, 2.6), (42, 18.5, 2)])
        c_face_s(fig, head, keep, look=-1 if view == 'Sf' else 0, mouth='o' if view == 'Sf' else 'line')
        c_mantle_s(fig)
        if view == 'Sf':
            # his right arm comes up slow, palm flat; a wren has landed on it
            over(fig, slab, box(fig, 19, 33, 25, 44, knock=1), 'stone_warm', keep, seed=10, band=0.25)
            over(fig, slab, box(fig, 21, 45, 31, 50, knock=1), 'stone', keep, seed=11, band=0.25)
            over(fig, slab, box(fig, 29, 44, 38, 49, knock=2), 'stone_cool', keep, seed=12, band=0.25)
            wren(fig, 28, 37, keep)
        return finish(fig, keep)
    d = 1 if view == 'E' else -1
    U = Ux(d)
    # far arm's hand peeks out behind the back, far leg a tone back
    slab(fig, box(fig, U(-11), 53, U(-6), 60, knock=2), 'stone', keep, dark=1, seed=1)
    slab(fig, box(fig, U(-5), 60, U(1), 69), 'stone_cool', keep, dark=1, seed=2)
    rock(fig, ell(fig, U(-1), 71, 5.2, 3.0), 'stone_cool', keep, dark=1, seed=3)
    fr = ([(U(-2), 24), (U(-5), 21), (U(-7), 17), (U(-8), 15)], [(U(-3), 25), (U(-6), 23), (U(-9), 21), (U(-12), 19)])
    if d == 1:
        fern(fig, fr[0], dark=1)
        fern(fig, fr[1], width=1.6, dark=1)
    over(fig, slab, box(fig, U(0), 60, U(6), 69), 'stone_cool', keep, seed=4, band=0.3)
    over(fig, rock, ell(fig, U(4), 71, 5.8, 3.1), 'stone', keep, seed=5)
    torso = fig.poly([(U(-6), 30), (U(4), 30), (U(9), 36), (U(9), 48), (U(7), 63), (U(-7), 63), (U(-10), 48), (U(-11.5), 36)])
    over(fig, rock, torso, 'stone', keep, seed=6, glint=False)
    crack(fig, [(U(3), 49), (U(4), 52), (U(3), 55)])
    lichen(fig, round(U(-6)), 44)
    moss(fig, [(U(-5), 61.5, 2), (U(-2), 61, 2)])
    head = over(fig, rock, ell(fig, U(4), 27, 8.0, 7.8), 'stone_warm', keep, seed=7)
    # profile face: the brow juts, the nose is a lump at the front, a short mouth line
    hx = max(p[0] for p in head if p[1] == 26) if d == 1 else min(p[0] for p in head if p[1] == 26)
    for k in range(-1, 5):
        fig.put(hx - d * k, 23, 'stone_warm', 4)
        fig.put(hx - d * k, 24, 'stone_cool', 1)
    fig.put(hx + d, 23, 'stone_warm', 4)
    fig.put(hx + d, 24, 'stone_warm', 2)
    over(fig, rock, ell(fig, hx + d * 0.5 + 0.5, 28.5, 2.0, 2.1), 'stone_warm', keep, glint=False, sib=False)
    eye(fig, min(hx - d * 4, hx - d * 3), 25, keep, w=2, look=2 if d == 1 else 3)
    for k in range(1, 4):
        fig.put(hx - d * k, 32, 'stone_cool', 1)
    moss(fig, [(U(1.5), 19.5, 2.6), (U(-1.5), 20.5, 2)])
    mant = fig.poly([(U(-12.5), 34), (U(-7), 28.5), (U(1), 30), (U(6), 32), (U(9), 36), (U(6.5), 39.5), (U(2), 38),
                     (U(-2), 40.5), (U(-6), 39.5), (U(-9), 41.5), (U(-12.5), 40)])
    moss_mass(fig, mant, seed=7, step=(6, 4))
    drip(fig, min(U(-9), U(-8)), 41, 5, 4)
    drip(fig, min(U(-3), U(-2)), 40, 3, 2)
    if d == -1:
        fern(fig, fr[0])
        fern(fig, fr[1], width=1.6)
    for i, (a, y0, b, y1, kn, fam) in enumerate(((-3, 34, 3, 43, 1, 'stone_warm'), (-2, 44, 4, 53, 1, 'stone'),
                                                  (-2, 54, 5, 61, 2, 'stone_cool'))):
        over(fig, slab, box(fig, U(a), y0, U(b), y1, knock=kn), fam, keep, seed=20 + i, band=0.25)
    moss(fig, [(U(-1.5), 33, 2.6), (U(2), 33.5, 2)])   # the mantle rolls over the near shoulder
    return finish(fig, keep)


WREN = ('..AAA......',
        '.ABBBA...UU',
        'kBEBBBAATT.',
        '.pBBBBBBT..',
        '.ppBBBBBD..',
        '..ppqBBD...',
        '...qqDD....')
WREN_TONE = {'U': ('earth', 3), 'T': ('earth', 2), 'A': ('earth', 4), 'B': ('earth', 3), 'D': ('earth', 2),
             'p': ('path', 4), 'q': ('path', 3), 'E': ('ink', 0), 'k': ('clay', 3)}


def wren(fig, x, y, keep):
    """A wren on his palm (the fidget's guest): earth back, a pale path breast, a cocked
    tail, an ink eye and a 1 px beak (nail-sized details)."""
    under = set(fig.px)
    mine = set()
    for j, row in enumerate(WREN):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            f, t = WREN_TONE[ch]
            fig.put(x + i, y + j, f, t)
            mine.add((x + i, y + j))
    rim(fig, mine - {(x, y + 2), (x + 2, y + 2)}, under - mine)
    keep |= {(x, y + 2), (x + 2, y + 2)}


# =====================================================================================
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Menhir: one weathered slab is body and head, boulder hands and feet',
        question='The standing stone stays one stone: the slab itself stands up, a face carved by weather in its '
                 'top third and the circle\'s ring carved on its chest; the limbs are boulders that came with it.',
        fn=option_a, palette=['stone', 'leaf', 'grass'],
        pose='Upright and patient as the stone he was, hands hanging, face kind; the fidget: a new moss tuft '
             'sprouts on his shoulder and he looks down at it, brows up, mouth a small o.',
        parts=[
            'familiar perch: the crown, on the moss cap (S/E/W the same anchor; the slab top is flat enough)',
            'far foot / far fist (stone_cool / stone, a tone back): layer 0; hip / chest; E/W only',
            'fern behind his LEFT ear (grass, two fronds): layer 1 in S and E (behind the slab), 4 in W (over the '
            'back of the head); head; sways a frame late on walk and hop',
            'feet x2 (stone_cool boulders): layer 2; hip; 6-frame walk as a slow rock-and-shuffle, 1 px lift',
            'slab (stone, lichen clusters, carved ring, cracks): layer 3; hip; breath 1 px, leans 1 px into '
            'the walk; bends only at the foot (hop is a 2 px rise and a dust puff)',
            'face (brow ledge, glowflora eyes in ink sockets, nose ridge, crack mouth): painted on the slab; '
            'head; blink = glow off for 140 ms; looks by moving the glow in the socket',
            'moss cap and drips (leaf lobes): layer 4; head; grows a tuft in the fidget',
            'shoulder boulders x2 and fists x2 (stone siblings): layer 5; chest / hand; swing in walk, the fists '
            'raise to guard (Bedrock), the shoulder leads the special shoulder charge',
        ],
        notes=[
            'Works: the tallest, plainest silhouette in the cast, a tombstone with a fern, readable in two values '
            'at game scale; the slab face says "standing stone" before anything else.',
            'Risk: one slab has no neck or waist, so walk and fight lean on the boulder limbs and 1 px leans; '
            'the face must stay in the top third or he reads as a sign post.',
            'Compared with Eastward 05 (John, the heavy-set tallest figure, 3-4 tones a garment) and the mossy '
            'rocks of its world shots: lichen as 2-4 px clusters, a lit lip under every crack.',
        ]),
    dict(
        label='B', name='Cairn stack: piled round stones under a wide capstone brim',
        question='A woken cairn: each body part is a stone set on the one below (feet, hips, belly, chest, '
                 'head), the capstone on top shades his eyes like a brim, the arms are three pebbles each.',
        fn=option_b, palette=['stone', 'leaf', 'grass'],
        pose='Comfortable and heavy, belly stone forward, eyes glowing from under the brim; the fidget: he '
             'settles, every stone crunching a little lower, eyes shut, a pebble shaken loose.',
        parts=[
            'familiar perch: on the capstone (a flat shelf, the best perch in the cast)',
            'far foot and far arm pebbles (a tone back): layer 0; hip / chest; E/W only',
            'fern behind his LEFT ear (grass): layer 1 under the capstone in S/E, 4 in W; head',
            'feet x2 (flat stones): layer 2; hip; 6-frame walk as stepping stones',
            'hip stone, belly stone, chest stone (stone siblings, moss in the joints): layers 3-5; hip / chest; '
            'each lags the one below by a frame in walk and hop (a gentle stack wobble), squash 1 px in breath',
            'head stone (stone_warm, glowflora eyes under the brim shadow): layer 6; chest',
            'capstone (stone_cool slab, moss cap, drip): layer 7; head; tilts 1 px in hit and cheer',
            'arm pebbles x3 a side (the last one the fist): layer 6; chest / hand; a chain that swings, the '
            'fists close together in guard; the shoulder charge throws the chest stone first',
        ],
        notes=[
            'Works: the capstone brim gives the cast a second hat shape (no hood, no nightcap) and a hard '
            'shadow over the eyes, so the glow reads; the stack shows "built of a place" at once.',
            'Risk: many round parts make a lumpy outline; the stack wobble costs extra rig layers. Close to '
            'Tuff in spirit, so Tuff keeps hex columns and stays low and wide.',
            'Compared with Eastward 05: the brim shadow on hats and the curly-haired woman\'s lobes (each stone a '
            'lobe with a lit cap and a dark crescent).',
        ]),
    dict(
        label='C', name='Moss-mantled giant: broad boulder body, sunk head, long slab arms',
        question='A stone that grew a body: a broad boulder with a smaller head sunk between the shoulders, '
                 'a thick moss mantle over the shoulders, arms of stacked slabs hanging to the knee.',
        fn=option_c, palette=['stone', 'leaf', 'grass', 'earth', 'path'],
        pose='A gentle giant with his shoulders up and arms long, slow and careful; the fidget: a wren lands '
             'on his raised palm and he holds very still, eyes on it.',
        parts=[
            'familiar perch: the near shoulder, in the moss mantle',
            'far hand slab and far leg (a tone back): layer 0; chest / hip; E/W only',
            'fern behind his LEFT ear (grass): layer 1 in S/E, 5 in W; head',
            'legs x2 (stone_cool pillars) and feet (boulders): layer 2; hip; short 6-frame stomp',
            'body boulder (stone, cracks, lichen): layer 3; hip; breath 1 px, sways into the walk',
            'head (stone_warm, brow ledge, glowflora eyes, nose lump): layer 4; chest; sunk, turns 1 px',
            'moss mantle (leaf lobes, drips): layer 5; chest; follows the body a frame late, tuft grows on rest',
            'arms x2: upper, fore and hand slabs (stone siblings): layer 6; chest / hand; long swing, the two '
            'hand slabs cross as a wall in guard; the shoulder charge leads with the mantle shoulder',
            'wren (earth, path): fidget prop only, lands on the near hand slab',
        ],
        notes=[
            'Works: the widest shoulders in the cast and arms that reach the knee give a gentle-giant read; the '
            'moss mantle is the most moss of the three and reads at 2 device px.',
            'Risk: the mantle over the shoulders must never close over the head (Nix owns the hood); the head '
            'is small, so the face leans on the glow.',
            'Compared with Eastward 05 (John: big shoulders, small head, long arms) for the mass, and the mossy '
            'world rocks for the moss lobes over stone.',
        ]),
]


# =====================================================================================
# FINAL (revision round, 21 Oct): option C, the moss-mantled giant, with grafts.
#   - from A: the circle's ring carved on his chest (its lower groove a faint glowflora),
#     and the brow set higher so the face fills the head.
#   - from B: a flat capstone on his head, its hard shadow over the glowing eyes; moss
#     only at its shaded east/back end, never a full green cap (Tam's beanie).
#   - E/W rebuilt with the body's depth: the same broad boulder side-on, a side plane and
#     a narrow front plane (lit facing W, shaded facing E), and the shoulder top plane.
#   - stone 58 px (capstone top to sole), grey; Tuff stays low, wide, black and glossy.
# =====================================================================================
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/cairn-final.png')
CAP_S = [(29.5, 18), (36, 17), (45, 17), (51, 18), (52, 20.5), (46, 21.5), (34, 21.5), (29, 20.5)]
# side-on capstone, (dx forward, y) about the head centre; it overhangs the face by 2 px
CAP_P = [(-9, 19), (-3, 18), (6, 18), (11, 19), (12, 21), (6, 22.5), (-6, 22.5), (-9.5, 21.5)]


def f_ring(fig, cx, cy, r=3.3, lit=False):
    """The circle's mark carved on his chest (graft from A): the groove's upper left in
    its own shadow (stone_cool 1), its lower right a faint glowflora (brighter in a cast),
    a lit lip outside the lower right."""
    keep = set()
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dd = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            s = (x + 0.5 - cx) + (y + 0.5 - cy)
            if r - 1.0 <= dd < r:
                if s < 0:
                    fig.put(x, y, 'stone_cool', 1)
                else:
                    fig.glow(x, y, 'glowflora', 3 if lit else 1)
                    keep.add((x, y))
            elif r <= dd < r + 0.9 and s > 1:
                fig.put(x, y, 'stone_warm', 4)
    return keep


def f_cap_moss(fig, cap, back):
    """Moss only along the capstone's shaded back end: a lobe and a short drip."""
    xs = sorted({p[0] for p in cap})
    if back > 0:
        x_end = xs[-1]
        moss(fig, [(x_end - 2, min(p[1] for p in cap if p[0] == x_end - 2) + 1, 2)])
        drip(fig, x_end - 2, max(p[1] for p in cap if p[0] == x_end - 2) + 1, 2, 1)
    else:
        x_end = xs[0]
        moss(fig, [(x_end + 2, min(p[1] for p in cap if p[0] == x_end + 2) + 1, 2)])
        drip(fig, x_end + 1, max(p[1] for p in cap if p[0] == x_end + 1) + 1, 2, 1)


def f_brim(fig, head, cap):
    low = {}
    for (x, y) in cap:
        low[x] = max(low.get(x, y), y)
    for (x, y) in head:
        if x in low and fam_at(fig, (x, y)) and base_fam(fam_at(fig, (x, y))) == 'stone':
            k = y - low[x]
            if k == 1:
                fig.put(x, y, 'stone_cool', 1)
            elif k == 2:
                fig.put(x, y, 'stone_cool', 2)


def limb(fig, a, b, w, fam, keep, dark=0, seed=0, glint=True):
    """A slab segment from a to b, w px thick (rotated as the pose needs), shaded as a
    slab: lit top and west, shaded east, a dark underside; laid over with a dark joint."""
    (ax, ay), (bx, by) = a, b
    L = max(0.01, math.hypot(bx - ax, by - ay))
    nx, ny = -(by - ay) / L * w / 2, (bx - ax) / L * w / 2
    m = fig.poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    m |= ell(fig, ax, ay, w / 2, w / 2) | ell(fig, bx, by, w / 2, w / 2)
    return over(fig, slab, m, fam, keep, dark=dark, seed=seed, band=0.25, glint=glint)


def f_arm(fig, sh, el, wr, keep, dark=0, d=1, seed=0):
    """Upper slab, fore slab, then a broad hand slab past the wrist."""
    fams = ('stone_warm', 'stone', 'stone_cool')
    limb(fig, sh, el, 7, fams[0], keep, dark=dark, seed=seed)
    limb(fig, el, wr, 7, fams[1], keep, dark=dark, seed=seed + 1, glint=False)
    vx, vy = wr[0] - el[0], wr[1] - el[1]
    L = max(0.01, math.hypot(vx, vy))
    tip = (wr[0] + vx / L * 5, wr[1] + vy / L * 5)
    limb(fig, wr, tip, 9, fams[2], keep, dark=dark, seed=seed + 2, glint=False)


def mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = ell(fig, cx, base - 5.5, 7.5, 5.5)
        rock(fig, body, 'leaf', keep, sib=False)
        for x in (cx - 4, cx - 1):
            fig.put(x, base - 6, 'ink', 0)
            fig.put(x + 1, base - 6, 'ink', 0)
        for (x, y, t) in ((cx + 3, base - 12, 4), (cx + 4, base - 12, 4), (cx + 4, base - 13, 3), (cx + 5, base - 13, 3)):
            fig.put(x, y, 'leaf_warm', t)
        return
    under = set(fig.px)
    body = ell(fig, cx, base - 9, 8, 9)
    rock(fig, body, 'leaf', keep, sib=False)
    rim(fig, body, under - body)
    ey = base - 11
    for ex in ((cx, cx + 4) if d == 1 else (cx - 5, cx - 1)):
        for (x, y) in ((ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)):
            fig.put(x, y, 'ink', 0)
    top = base - 18
    fig.put(cx, top, 'leaf_warm', 3)
    fig.put(cx, top - 1, 'leaf_warm', 3)
    for (x, y, t) in ((cx - 1, top - 2, 4), (cx - 2, top - 2, 4), (cx - 2, top - 3, 4),
                      (cx + 1, top - 2, 3), (cx + 2, top - 2, 2), (cx + 2, top - 3, 3)):
        fig.put(x, y, 'leaf_warm', t)


def f_face_s(fig, head, keep, dy=0, look=0, eyes='open', mouth='line'):
    """The front face, set high: the cap's shadow is the brow; eyes at y 24, a lit cheek
    under the west eye, a nose lump, a mouth line."""
    ey = 24 + dy
    if eyes == 'shut':
        eye(fig, 34, ey, keep, shut=True)
        eye(fig, 43, ey, keep, shut=True)
    else:
        eye(fig, 34, ey, keep, w=3, look=look)
        eye(fig, 43, ey, keep, w=3, look=look)
    for x in (33, 34, 35):
        fig.put(x, ey + 2, 'stone_warm', 4)
    over(fig, rock, ell(fig, 40.5, 28 + dy, 2.0, 2.2), 'stone_warm', keep, glint=False, sib=False)
    fig.put(39, 26 + dy, 'stone_warm', 5)
    keep.add((39, 26 + dy))
    if mouth == 'o':
        for x in (39, 40, 41):
            fig.put(x, 32 + dy, 'stone_cool', 1)
        fig.put(37, 31 + dy, 'stone_cool', 1)
        fig.put(38, 31 + dy, 'stone_cool', 1)
    elif mouth == 'smile':
        for x in range(38, 43):
            fig.put(x, 32 + dy, 'stone_cool', 1)
        for x in (36, 37, 43, 44):
            fig.put(x, 31 + dy, 'stone_cool', 1)
    else:
        for x in range(38, 43):
            fig.put(x, 32 + dy, 'stone_cool', 1)


def f_head_s(fig, keep, dy=0, **face):
    fern(fig, [(48, 25 + dy), (51, 22 + dy), (53, 19 + dy), (54, 17 + dy)])
    fern(fig, [(49, 26 + dy), (52, 25 + dy), (55, 23 + dy), (57, 21 + dy)], width=1.6)
    head = over(fig, rock, ell(fig, 40, 28.5 + dy, 10, 9), 'stone_warm', keep, seed=4, glint=False)
    cap = over(fig, slab, fig.poly([(x, y + dy) for (x, y) in CAP_S]), 'stone_cool', keep, seed=11, band=0.12)
    f_brim(fig, head, cap)
    f_cap_moss(fig, cap, 1)
    f_face_s(fig, head, keep, dy=dy, **face)
    return head, cap


def final_front(view):
    fig = sk.Fig(W, H)
    keep = set()
    for x0 in (31, 43):
        slab(fig, box(fig, x0, 60, x0 + 6, 69), 'stone_cool', keep, seed=x0, band=0.3)
    over(fig, rock, ell(fig, 33.5, 71, 5.6, 3.1), 'stone', keep, seed=1)
    over(fig, rock, ell(fig, 46.5, 71, 5.6, 3.1), 'stone_cool', keep, seed=2)
    torso = fig.poly([(27, 30), (53, 30), (57.5, 35), (56, 48), (51, 63), (29, 63), (24, 48), (22.5, 35)])
    over(fig, rock, torso, 'stone', keep, seed=3, glint=False)
    crack(fig, [(47, 47), (48, 50), (47, 53), (48, 55)])
    crack(fig, [(31, 54), (34, 55)])
    lichen(fig, 30, 45)
    lichen(fig, 41, 59, ((0, 0), (1, 0), (2, 0)))
    keep |= f_ring(fig, 40, 50, r=4.2)
    if view == 'S':
        c_arm_s(fig, -1, keep, 10)
    c_arm_s(fig, 1, keep, 20)
    moss(fig, [(46, 61.5, 2), (49, 61, 2)])
    f_head_s(fig, keep, look=-1 if view == 'Sf' else 0, mouth='o' if view == 'Sf' else 'line')
    c_mantle_s(fig)
    if view == 'Sf':
        over(fig, slab, box(fig, 19, 33, 25, 44, knock=1), 'stone_warm', keep, seed=10, band=0.25)
        over(fig, slab, box(fig, 21, 45, 31, 50, knock=1), 'stone', keep, seed=11, band=0.25)
        over(fig, slab, box(fig, 29, 44, 38, 49, knock=2), 'stone_cool', keep, seed=12, band=0.25)
        wren(fig, 28, 37, keep)
    return finish(fig, keep)


#          body bx/by  head hx/hy  legs     near elbow / wrist (from the shoulder)  far elbow / wrist    eyes
POSES = {
    'idle':   (0, 0,   0, 0,   'stand', (0, 10), (1, 19),     None, None,         'open'),
    'ready':  (1, 1,   1, 0,   'wide',  (5, 8), (12, 4),      (4, 8), (10, 6),    'open'),
    'strike': (3, 1,   2, 1,   'lunge', (9, 2), (18, 3),      (-6, 6), (-10, 12), 'open'),
    'cast':   (0, 0,   0, -1,  'wide',  (9, -2), (17, -7),    (4, 7), (9, 9),     'bright'),
    'hit':    (-3, 0,  -2, 1,  'stand', (-5, 6), (-9, 13),    (5, 6), (9, 11),    'squeeze'),
    'sit':    (0, 8,   0, 0,   'sit',   (4, 7), (10, 11),     (3, 7), (9, 10),    'open'),
    'cheer':  (0, -2,  0, -1,  'hop',   (8, -6), (14, -13),   (-5, -6), (-9, -13), 'happy'),
}


def f_body_side(fig, d, keep, bx, by):
    """The broad boulder side-on: 26 px deep, the side plane facing the viewer shaded as a
    round mass, a 4 px front plane (facing d: lit when it faces W, shaded when it faces
    E) split from it by one hard step, the top plane of the shoulders lit under the moss."""
    U = Ux(d)
    pts = [(-10, 30), (6, 30), (11, 35), (12.5, 47), (9, 62), (-9, 62), (-13, 48), (-14, 36)]
    torso = fig.poly([(U(x + bx), y + by) for (x, y) in pts])
    over(fig, rock, torso, 'stone', keep, seed=6, glint=False)
    rows = {}
    for (x, y) in torso:
        rows.setdefault(y, []).append(x)
    for y, xs in rows.items():
        front = max(xs) if d == 1 else min(xs)
        for k in range(4):
            x = front - d * k
            if (x, y) in torso and y > min(rows) + 1 and y < max(rows):
                t = (2 if k else 1) if d == 1 else (4 if k < 3 else 3)
                fig.put(x, y, 'stone_cool' if d == 1 else 'stone_warm', t)
        if y < min(rows) + 4:                    # the shoulders' top plane
            for x in xs:
                if fam_at(fig, (x, y)) and tone(fig, (x, y)) in (2, 3):
                    fig.put(x, y, 'stone', tone(fig, (x, y)) + 1)
    crack(fig, [(U(-2 + bx), 49 + by), (U(-1 + bx), 52 + by), (U(-2 + bx), 55 + by)])
    lichen(fig, round(U(-7 + bx)), 44 + by)
    lichen(fig, round(U(-4 + bx)), 57 + by, ((0, 0), (1, 0), (2, 0)))
    return torso


def f_legs_side(fig, d, keep, mode, by):
    U = Ux(d)
    if mode == 'sit':
        # sitting: legs forward along the ground, feet up at the front
        for far, (y0, k) in enumerate(((65, 0), (64, 1))):
            dx0 = -2 if far else 0
            leg = box(fig, U(dx0 + 2), y0 + 1, U(dx0 + 15), y0 + 7)
            (slab if far else over)(*((fig, leg, 'stone_cool', keep) if far else (fig, slab, leg, 'stone_cool', keep)),
                                    **(dict(dark=1, seed=40) if far else dict(seed=41)))
            ft = ell(fig, U(dx0 + 16), y0 + 2, 3.2, 5.2)
            if far:
                rock(fig, ft, 'stone', keep, dark=1, seed=42)
            else:
                over(fig, rock, ft, 'stone', keep, seed=43)
        return
    lift = 2 if mode == 'hop' else 0
    near, far = {'stand': ((0, 6), (-6, 0)), 'hop': ((0, 6), (-6, 0)), 'wide': ((2, 8), (-8, -2)),
                 'lunge': ((5, 11), (-11, -5))}[mode]
    slab(fig, box(fig, U(far[0]), 60 - lift, U(far[1]), 69 - lift), 'stone_cool', keep, dark=1, seed=2)
    rock(fig, ell(fig, U(far[0] + 5), 71 - lift, 5.2, 3.0), 'stone_cool', keep, dark=1, seed=3)
    over(fig, slab, box(fig, U(near[0]), 60 - lift, U(near[1]), 69 - lift), 'stone_cool', keep, seed=4, band=0.3)
    over(fig, rock, ell(fig, U(near[0] + 4), 71 - lift, 5.8, 3.1), 'stone', keep, seed=5)


def f_head_side(fig, d, keep, hx, hy, eyes, far_fern):
    U = Ux(d)
    cx, cy = 5 + hx, 28 + hy
    fr = ([(U(cx - 6), 25 + hy), (U(cx - 9), 22 + hy), (U(cx - 11), 19 + hy), (U(cx - 12), 17 + hy)],
          [(U(cx - 7), 26 + hy), (U(cx - 10), 24 + hy), (U(cx - 13), 22 + hy), (U(cx - 15), 20 + hy)])
    if far_fern:
        fern(fig, fr[0], dark=1)
        fern(fig, fr[1], width=1.6, dark=1)
    head = over(fig, rock, ell(fig, U(cx), cy, 8.2, 8.4), 'stone_warm', keep, seed=7, glint=False)
    # the face step: the brow line under the cap, a cheek, the nose lump at the front
    hxf = max(p[0] for p in head if p[1] == cy) if d == 1 else min(p[0] for p in head if p[1] == cy)
    nose = over(fig, rock, ell(fig, hxf + d * 0.8 + 0.5, cy + 0.5, 2.0, 2.2), 'stone_warm', keep, glint=False, sib=False)
    cap = over(fig, slab, fig.poly([(U(cx + x), cy - 28 + y) for (x, y) in CAP_P]), 'stone_cool', keep, seed=12, band=0.12)
    f_brim(fig, head | nose, cap)
    ex = hxf - d * 4
    ey = cy - 4
    if eyes == 'squeeze':
        for k in range(3):
            fig.put(ex - d * k + d, ey + 1, 'ink', 0)
    elif eyes == 'happy':
        fig.put(ex, ey, 'ink', 0)
        fig.put(ex - d, ey, 'ink', 0)
        fig.put(ex + d, ey + 1, 'ink', 0)
        fig.put(ex - 2 * d, ey + 1, 'ink', 0)
    else:
        eye(fig, min(ex, ex - d), ey, keep, w=2, look=2 if d == 1 else 3)
        if eyes == 'bright':
            for (x, y) in ((max(ex, ex - d) if d == 1 else min(ex, ex - d), ey),):
                fig.glow(x, y, 'glowflora', 5)
    for k in range(2, 5):                                   # cheek, lit on top
        fig.put(hxf - d * k, ey + 2, 'stone_warm', 4)
    for k in range(1, 4):                                   # mouth
        fig.put(hxf - d * k, cy + 4, 'stone_cool', 1)
    if eyes == 'happy':
        fig.put(hxf - d * 4, cy + 3, 'stone_cool', 1)
    f_cap_moss(fig, cap, -d)
    if not far_fern:
        fern(fig, fr[0])
        fern(fig, fr[1], width=1.6)
    return head


def f_mantle_side(fig, d, bx, by):
    U = Ux(d)
    pts = [(-15, 34), (-10, 29), (0, 30), (7, 31), (11.5, 35), (8.5, 39.5), (3, 38), (-2, 40.5), (-7, 39.5),
           (-11, 42), (-15, 40)]
    mant = fig.poly([(U(x + bx), y + by) for (x, y) in pts])
    moss_mass(fig, mant, seed=7, step=(6, 4))
    drip(fig, min(U(-12 + bx), U(-11 + bx)), 41 + by, 4, 3)
    drip(fig, min(U(-4 + bx), U(-3 + bx)), 40 + by, 3, 2)


def final_side(d, pose, familiar=False):
    fig = sk.Fig(W, H)
    keep = set()
    U = Ux(d)
    bx, by, hx, hy, legs, ne, nw, fe, fw, eyes = POSES[pose]
    sh = (U(bx - 1), 35 + by)
    far_sh = (U(bx + 2), 34 + by)
    if fe:
        f_arm(fig, far_sh, (far_sh[0] + d * fe[0], far_sh[1] + fe[1]), (far_sh[0] + d * fw[0], far_sh[1] + fw[1]),
              keep, dark=1, d=d, seed=50)
    f_legs_side(fig, d, keep, legs, by)
    f_body_side(fig, d, keep, bx, by)
    if pose == 'cast':
        keep |= f_ring_side(fig, d, bx, by)
    moss(fig, [(U(bx - 6), 61.5 + by, 2), (U(bx - 3), 61 + by, 2)])
    f_head_side(fig, d, keep, bx + hx, by + hy, eyes, far_fern=(d == 1))
    f_mantle_side(fig, d, bx, by)
    perch = None
    if familiar:
        perch = (round(U(bx - 9)), 31 + by)
        mossling(fig, perch[0], perch[1], d, keep)
    f_arm(fig, sh, (sh[0] + d * ne[0], sh[1] + ne[1]), (sh[0] + d * nw[0], sh[1] + nw[1]), keep, d=d, seed=60)
    moss(fig, [(U(bx - 1.5), 33 + by, 2.6), (U(bx + 2), 33.5 + by, 2)])   # the mantle over the near shoulder
    return finish(fig, keep), perch


def f_ring_side(fig, d, bx, by):
    """In a cast the ring's glow shows on the front plane, seen edge-on: a short arc."""
    U = Ux(d)
    keep = set()
    x = round(U(bx + 11.5)) - (1 if d == 1 else 0)
    for y in range(47 + by, 53 + by):
        fig.glow(x, y, 'glowflora', 4 if y in (49 + by, 50 + by) else 3)
        keep.add((x, y))
    return keep


def final_nap():
    """Curled up facing S: he sits hunched until he is a boulder again, head bowed under
    the capstone, hands folded, the moss mantle over his back, the familiar curled
    against his west side."""
    fig = sk.Fig(W, H)
    keep = set()
    body = rock(fig, ell(fig, 40, 61, 17, 12.5), 'stone', keep, seed=3, glint=False)
    crack(fig, [(50, 60), (51, 63), (50, 66)])
    lichen(fig, 30, 62)
    moss_mass(fig, fig.poly([(25, 56), (30, 50), (40, 48.5), (50, 50), (55, 56), (55, 59), (50, 60), (45, 58),
                              (40, 59.5), (35, 58), (30, 60), (25, 59)]), seed=9, step=(6, 4))
    drip(fig, 51, 59, 4, 3)
    # the bowed head: low at the front, eyes shut, the capstone still level on it
    head = over(fig, rock, ell(fig, 37, 59, 7.6, 6.8), 'stone_warm', keep, seed=4, glint=False)
    cap = over(fig, slab, fig.poly([(28.5, 52), (34, 50.5), (42, 50.5), (46, 52), (46.5, 54.5), (41, 55.5),
                                    (32, 55.5), (28, 54.5)]), 'stone_cool', keep, seed=11, band=0.12)
    f_brim(fig, head, cap)
    f_cap_moss(fig, cap, 1)
    for x in (32, 33, 34, 39, 40, 41):
        fig.put(x, 59, 'ink', 0)
    for x in (36, 37, 38):
        fig.put(x, 63, 'stone_cool', 1)
    # folded hands at the front
    over(fig, slab, box(fig, 27, 66, 36, 72, knock=2), 'stone', keep, seed=21, band=0.25)
    over(fig, slab, box(fig, 34, 67, 44, 73, knock=2), 'stone_cool', keep, seed=22, band=0.25)
    mossling(fig, 18, SOLE + 1, 1, keep, curled=True)
    return finish(fig, keep)


FINAL_VIEWS = (
    ('S idle', lambda: (final_front('S'), None)),
    ('E idle', lambda: final_side(1, 'idle')),
    ('W idle', lambda: final_side(-1, 'idle')),
    ('S fidget', lambda: (final_front('Sf'), None)),
    ('nap S', lambda: (final_nap(), None)),
    ('E ready', lambda: final_side(1, 'ready', True)),
    ('E strike', lambda: final_side(1, 'strike', True)),
    ('E cast', lambda: final_side(1, 'cast', True)),
    ('E hit', lambda: final_side(1, 'hit', True)),
    ('E sit', lambda: final_side(1, 'sit', True)),
    ('E cheer', lambda: final_side(1, 'cheer', True)),
    ('W ready', lambda: final_side(-1, 'ready', True)),
    ('W strike', lambda: final_side(-1, 'strike', True)),
)

FINAL = dict(
    label='C final', name='Moss-mantled giant (final): broad boulder, capstone brow, ring on the chest',
    chosen='C',
    grafts=[
        'From A: the circle\'s ring carved on his chest; its lower groove is a faint glowflora that brightens '
        'in a cast (seen edge-on on the front plane in E/W).',
        'From A: the brow set higher; the face now fills the head under the cap (eyes at y 24, not 25-26).',
        'From B: a flat capstone on his head with its hard two-row shadow over the glowing eyes; moss only '
        'at its shaded back end with a 2 px drip, never a full cap (Tam\'s beanie).',
        'E/W rebuilt with depth: the same broad boulder side-on (26 px deep), a side plane, a 4 px front plane '
        'split by one hard step (lit facing W, shaded facing E) and a lit shoulder top plane under the moss.',
    ],
    palette=['stone', 'leaf', 'grass', 'earth', 'path'],
    pose='A gentle giant, shoulders up and arms long, slow and careful; a wren lands on his palm and he holds '
         'still. In a fight he plants and punches with the hand slab; his ring glows when he casts.',
    parts=[
        'familiar perch: the back shoulder on the moss mantle (E: x smaller, W: x larger); layer 0.5; chest',
        'far arm (upper, fore, hand slabs, a tone back): layer 0; chest / hand; E/W fight poses',
        'far leg (stone_cool pillar, boulder foot, a tone back): layer 1; hip; all facings',
        'near leg (pillar, boulder foot): layer 2; hip; short 6-frame stomp, forward in sit, lifted 2 px in hop',
        'body boulder (stone; side plane plus front plane in E/W; cracks, lichen; the ring rune with a '
        'glowflora groove): layer 3; hip; breath 1 px, leans up to 3 px in strike and hit',
        'fern behind his LEFT ear (grass): layer 3.5 (S, E: behind the head), 5.5 in W (over its back); head',
        'head (stone_warm, nose lump, glowflora eyes in ink sockets, mouth line): layer 4; chest; '
        'blink = glow off 140 ms, looks by moving the glow',
        'capstone (stone_cool slab, moss at the back end): layer 4.5; head; stays level in every pose',
        'moss mantle (leaf lobes, drips): layer 5; chest; one painter, shifts with the body (no lag frames)',
        'near arm (upper, fore, hand slabs, rotated per pose): layer 6; chest / hand; swing, guard (hand slab '
        'up), strike (full reach), cast (raised), cheer (both up); Bedrock shoulder charge leads with the mantle',
        'wren (earth, path): fidget prop only, on the near hand slab',
    ],
    notes=[
        'Compared side by side with Eastward 05 at the same height: John (broad shoulders, a small head, '
        'long arms, 3-4 tones a material), the hard shadow under hat brims, and the mossy world rocks.',
        'Apart from Tuff: Cairn is tall (58 px), grey and matte, upright, with moss and a fern; Tuff stays low, '
        'wide, black basalt hex columns, glossy, no moss.',
        'Open: the capstone is the natural perch, but a 24 px familiar on it would leave the 80 px cell '
        '(stone top at y 17); it perches on the back shoulder until the familiar size is settled.',
        'Lone pixels and W-E are within the gates in every view; the cheer stays inside the cell.',
    ],
)


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


def build_final():
    views, nums, perches, ok = [], {}, {}, True
    for cap, fn in FINAL_VIEWS:
        fig, perch = fn()
        im = fig.image()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        print(f"final {cap:9s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Cairn final (folk 7, the woodland circle): C, the moss-mantled giant, with grafts', [entry],
                    OUT_FINAL, note='58 art px (stone), cell 80 x 80, foot (40, 74). World S/E/W, fidget, nap; '
                                    'fight E and W with the stand-in Mossling on the back shoulder.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'] + ['glowflora (glow: eyes, the ring groove)'], pose=FINAL['pose'],
                perch_anchor=perches, measure=nums, notes=FINAL['notes'], _ok=ok)


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    out = []
    ok = True
    for o in OPTIONS:
        o['views'] = []
        nums = {}
        for v, cap in VIEWS:
            im = o['fn'](v).image()
            o['views'].append((cap, im))
            im.save(os.path.join(SCRATCH, f"{o['label']}-{cap.replace(' ', '-')}.png"))
            m = sk.measure(im)
            g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                     colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
            ok &= all(g.values())
            a = im.getchannel('A')
            ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
            print(f"{o['label']} {cap:9s} h {ys[-1] - ys[0] + 1:2d} on house {100*m['on_house']:5.1f}%  "
                  f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'] + ['glowflora (glow: the eyes, 2 px each)'], pose=o['pose'],
                        notes=o['notes'], measure=nums))
    sk.design_sheet('Cairn (folk 7, the woodland circle): how a standing stone becomes a body', OPTIONS, OUT_PNG,
                    note='58 art px (the tallest folk), cell 80 x 80, foot (40, 74). Views: S, E, W idle and the S '
                         'fidget key pose.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='cairn', height_art_px=58, cell=[W, H], foot=[AX, AY],
                       question='How a standing stone becomes a body.', options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
