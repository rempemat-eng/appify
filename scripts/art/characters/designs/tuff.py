"""Tuff, the basalt golem of the Tidebloom Isles' dormant volcano: three design options
(Claude J lane, batch 2).

Main question: how hex columns make a low, wide body.

    A  Causeway block: the body is a squat cluster of short hex columns, the tallest in the
       middle carrying the face and a broad flat top where the turtle sleeps; two shoulder
       columns, two hanging column-arms, two stump legs. A stepped skyline silhouette.
    B  Shell of columns: a crouching tortoise-like golem whose back is a low dome of hex
       column tops (a honeycomb), a small round boulder head poking out at the front and
       four stubby column legs. The sleeping turtle rides on the crown of the dome.
    C  Boulder on stumps: one wide glossy boulder for the body on two stubby column legs,
       short column-arms, and a crown of short hex columns at the back of the top; the
       turtle sleeps in the gap of the crown like a nest.

All three: glossy basalt (hexagon tops tone 4 with a crisp tone 5 glint, west facets 3,
south facets 2, east facets 1, the joints tone 0), dormant ember eyes (lava glow, the only
light source), sea thrift in berry tufts on leaf cushions along the base, and a turtle in
lagoon and leaf asleep on his back. No moss anywhere (that is Cairn's).

Views: S idle, E idle, W idle (W is laid out and lit on its own, never mirrored pixels)
and the S key pose of his fidget. Design sheets are review material; production frames
come from the shared rig.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/tuff.py
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
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/tuff-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/tuff.json')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'tuff')

W, H = 80, 80
AX, AY = 40, 74          # foot anchor: soles fill row 73, their outline lands on row 74
SOLE = AY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
ROCK = 'basalt'


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def is_rock(fig, p):
    f = fam_at(fig, p)
    return f is not None and sk.family_of(f) == ROCK


def rnd(v):
    return int(math.floor(v + 0.5))


def hexprof(w, th):
    """Half-depth of a hexagon top seen from the south, per column: zero at the west and
    east points, the full half-depth along the flat back and front edges."""
    half = (th - 1) / 2
    q = max(1, rnd(w * 0.28))
    return [half * min(1.0, (min(i, w - 1 - i) + 0.5) / q) for i in range(w)], q


def column(fig, x0, w, foot, height, fam=ROCK, joints=(), keep=None, seam=True, th=None,
           glint=True, sheen=True):
    """One glossy hex column, lit from the upper left. `foot` is the lowest row of its
    south facet, `height` its whole height in rows. The top hexagon is tone 4 with a crisp
    two-pixel tone 5 glint at its upper left; the west facet is 3 with a bright ridge, the
    south facet 2 with a gloss streak, the east facet 1. `joints` are cross joints (rows
    down the side) that follow the hexagon's curve. Where the column overlaps rock drawn
    before it, the meeting line is darkened to a tone 0 joint."""
    if th is None:
        th = max(3, rnd(w * 0.5))
    prof, q = hexprof(w, th)
    top = foot - height + 1
    mid = top + (th - 1) / 2
    h = height - th
    topm, side = set(), {}
    for i in range(w):
        x = x0 + i
        a, b = rnd(mid - prof[i] - 0.01), rnd(mid + prof[i] - 0.01)
        if i >= w / 2:
            a, b = rnd(mid - prof[i] + 0.01), rnd(mid + prof[i] + 0.01)
        for y in range(a, b + 1):
            topm.add((x, y))
        for k, y in enumerate(range(b + 1, b + 1 + h)):
            side[(x, y)] = (i, k)
    mask = topm | set(side)
    if seam:
        for (x, y) in mask:
            for dx, dy in ((-1, 0), (1, 0), (0, -1)):
                n = (x + dx, y + dy)
                if n not in mask and is_rock(fig, n) and not (keep and n in keep):
                    fig.put(n[0], n[1], fig.px[n][0], 0)
    for (x, y) in topm:
        i = x - x0
        fig.put(x, y, fam, 3 if i >= w - q else 4)
    for (x, y), (i, k) in side.items():
        if i < q:
            t = 3
            if i == q - 1 and k < max(2, h * 0.6):
                t = 4                       # the bright ridge between west and south facets
        elif i >= w - q:
            t = 1
        else:
            t = 2
            if sheen and i == q + 1 and 1 <= k < max(2, h * 0.5):
                t = 3                       # a gloss streak down the south facet
        if k == h - 1 and h >= 4:
            t = min(t, 1)
        fig.put(x, y, fam, t)
    for j in joints:
        for (x, y), (i, k) in side.items():
            if k == j:
                fig.put(x, y, fam, 0 if i >= w - q else 1)
            elif k == j + 1 and i < w - q:
                fig.put(x, y, fam, 4 if i < q else 3)
    if glint:
        gl = sorted(topm, key=lambda p: (p[1], p[0]))
        gl = [p for p in gl if p[0] - x0 >= q][:2]
        for p in gl:
            fig.put(p[0], p[1], fam, 5)
            if keep is not None:
                keep.add(p)
    return mask, topm


def pillow(fig, mask, fam, glint=2, keep=None, cap=0.42, crescent=1.05, tones=(4, 3, 2)):
    """A round glossy form: the lit cap is a disc offset to the upper left, the dark
    crescent the outside of a larger offset disc, so the terminator follows the form."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    best = []
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = tones[1]
        d = (u + 0.42) ** 2 + (v + 0.5) ** 2
        if d < cap:
            t = tones[0]
        if (u + 0.28) ** 2 + (v + 0.32) ** 2 > crescent:
            t = tones[2]
        if (x, y + 1) not in mask and u > -0.3:
            t = min(t, 1 if u > 0.2 else 2)
        fig.put(x, y, fam, t)
        best.append((d, y, x))
    if glint:
        best.sort()
        # a crisp horizontal glint in the middle of the lit cap
        _, gy, gx = best[0]
        for k in range(glint):
            if (gx + k, gy) in mask:
                fig.put(gx + k, gy, fam, 5)
                if keep is not None:
                    keep.add((gx + k, gy))


def seam_around(fig, mask, keep=None):
    """Darken rock already drawn that touches a new front part: the joint between them."""
    for (x, y) in mask:
        for dx, dy in N4:
            n = (x + dx, y + dy)
            if n not in mask and is_rock(fig, n) and not (keep and n in keep):
                fig.put(n[0], n[1], fig.px[n][0], 0)


def ember_eyes(fig, xs, y, keep, state='open', brow=True):
    """Dormant ember eyes: a tone 0 socket under a lit brow ledge, a 2 x 2 lava glow in it.
    'shut' is a dim slit, 'up' looks up (the glow in the top row of the socket)."""
    for x in xs:
        for yy in range(y - 1, y + 3):
            for xx in range(x - 1, x + 3):
                if is_rock(fig, (xx, yy)):
                    fig.put(xx, yy, fig.px[(xx, yy)][0], 0)
        if brow:
            for xx in range(x - 1, x + 3):
                if is_rock(fig, (xx, y - 2)):
                    fig.put(xx, y - 2, fig.px[(xx, y - 2)][0], 4)
        if state == 'open':
            cells = [((x, y), 4), ((x + 1, y), 4), ((x, y + 1), 3), ((x + 1, y + 1), 3)]
        elif state == 'up':
            cells = [((x, y - 1), 4), ((x + 1, y - 1), 4), ((x, y), 3), ((x + 1, y), 3)]
        elif state == 'down':
            cells = [((x, y + 1), 4), ((x + 1, y + 1), 4), ((x, y + 2), 3), ((x + 1, y + 2), 3)]
        else:
            cells = [((x, y + 1), 2), ((x + 1, y + 1), 2)]
        for (p, t) in cells:
            fig.glow(p[0], p[1], 'lava', t)
            keep.add(p)


def _rows(spec):
    return [(cx, cy) for cy, (a, b) in spec.items() for cx in range(a, b + 1)]


TURTLE_HEAD = {
    # (dx, dy) from the neck root at the shell's rim, for a head pointing east; awake lifts it
    'shut': _rows({-3: (2, 4), -2: (1, 5), -1: (0, 5), 0: (0, 1)}),
    'up': _rows({-4: (3, 5), -3: (2, 6), -2: (1, 6), -1: (0, 2), 0: (0, 1)}),
}


SHELL, SKIN = 'lagoon_cool', 'lagoon_warm'


def turtle(fig, x, base, d, keep, eye='shut'):
    """The sea turtle asleep on his back: a low lagoon shell with a central scute, side
    scutes and a dark marginal rim, splayed flippers and a head in pale warm lagoon on a short neck.
    `x` is the shell's centre, `base` the row its rim rests on, `d` the way the head points
    (+1 east, -1 west). eye: 'shut', 'open' (awake: lifted, a glint) or 'peek'."""
    awake = eye in ('open', 'peek')
    # contact shadow on the rock under the rim
    for xx in range(x - 7, x + 8):
        if is_rock(fig, (xx, base)):
            fig.put(xx, base, fig.px[(xx, base)][0], 1)
    # flippers, splayed at the four corners, behind the shell
    fl = {(x - 8, base - 1), (x - 7, base - 1), (x - 8, base), (x + 7, base - 1), (x + 8, base - 1), (x + 8, base)}
    for p in sorted(fl):
        fig.put(p[0], p[1], SKIN, 2 if p[1] < base else 1)
    shell = {p for p in fig.ellipse(x, base - 1.5, 7.8, 4.6) if p[1] <= base - 1}
    pillow(fig, shell, SHELL, glint=0, cap=0.6, crescent=1.2)
    top = min(p[1] for p in shell)
    for (sx, sy) in shell:
        u = sx - x
        t = fig.px[(sx, sy)][1]
        if sy == base - 1:
            t = 1 if (u + 1) % 3 == 0 else 2                 # marginal scutes, a dark rim
        elif sy == base - 2:
            t = min(t, 3)
        elif abs(u + (1 if u > 0 else 0)) == 3 and sy >= top + 1:
            t = max(1, t - 1)                                # the seams of the side scutes
        fig.put(sx, sy, SHELL, t)
    for p in ((x - 2, top + 1), (x - 1, top + 1)):
        fig.put(p[0], p[1], SHELL, 5)
        keep.add(p)
    # neck and head, out past the rim toward d, over the rim
    cells = TURTLE_HEAD['up' if awake else 'shut']
    nx = x + d * 7
    head = {(nx + d * cx, base - 1 + cy) for (cx, cy) in cells}
    ys = [p[1] for p in head]
    for (px_, py) in head:
        t = 3
        if py == min(ys) or (px_ - 1, py) not in head:
            t = 4
        elif py == max(ys) or (px_ + 1, py) not in head:
            t = 2
        fig.put(px_, py, SKIN, t)
    if eye == 'shut':
        for cx in (4, 5):
            p = (nx + d * cx, base - 3)
            fig.put(p[0], p[1], SKIN, 1)
            keep.add(p)
    else:
        for p in ((nx + d * 5, base - 4), (nx + d * 5, base - 3)):
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
        if eye == 'open':
            p = (nx + d * 4, base - 4)
            fig.put(p[0], p[1], SKIN, 5)
            keep.add(p)
    return shell | head


def thrift(fig, x, base, heads, keep, cushion=3, bloom=None):
    """A sea thrift tuft: a leaf cushion with berry pompom heads on short stems.
    heads: [(dx, stem)]; bloom: index of a head drawn wide open (fidget)."""
    cush = fig.ellipse(x + 0.5, base - 0.5, cushion + 0.5, 1.6)
    for (cx, cy) in cush:
        t = 3 if cx <= x else 2
        if cy == min(p[1] for p in cush):
            t = 4 if cx <= x else 3
        fig.put(cx, cy, 'leaf', t)
    for k, (dx, stem) in enumerate(heads):
        hx = x + dx
        top = base - 1 - stem
        for yy in range(top + 1, base - 1):
            fig.put(hx, yy, 'leaf', 2)
        if bloom == k:
            # wide open: a 5 x 4 pompom with a crisp glint, a stem a pixel taller
            top -= 1
            fig.put(hx, top + 1, 'leaf', 2)
            rows = {top - 3: (-1, 1, (4, 4, 3)), top - 2: (-2, 2, (4, 4, 4, 3, 3)),
                    top - 1: (-2, 2, (3, 4, 3, 3, 2)), top: (-1, 1, (2, 2, 1))}
            for yy, (a0, a1, ts) in rows.items():
                for i, xx in enumerate(range(hx + a0, hx + a1 + 1)):
                    fig.put(xx, yy, 'berry', ts[i])
            for p in ((hx - 1, top - 2), (hx, top - 2)):
                fig.put(p[0], p[1], 'berry', 5)
                keep.add(p)
        elif bloom is not None and bloom == -1 - k:
            # a closed bud before it pops
            fig.put(hx, top, 'berry', 3)
            fig.put(hx, top - 1, 'berry', 4)
            fig.put(hx + 1, top, 'berry', 2)
        else:
            for (p, t) in {(hx - 1, top - 1): 4, (hx, top - 1): 4, (hx + 1, top - 1): 3,
                           (hx - 1, top): 3, (hx, top): 3, (hx + 1, top): 2}.items():
                fig.put(p[0], p[1], 'berry', t)


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour (deterministic tie-break), unless it is an eye, a glint or a glow (`keep`)."""
    for _ in range(2):
        changes = {}
        for p, v in sorted(fig.px.items()):
            if p in keep or p in fig.fixed or v[0] in ('ink', '_edge', '_lit'):
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if all(n != v for n in nb):
                pool = [n for n in nb if n[0] not in ('ink', '_edge', '_lit')]
                if not pool:
                    continue
                same = [n for n in pool if sk.family_of(n[0]) == sk.family_of(v[0])] or pool
                changes[p] = max(sorted(set(same), key=str), key=same.count)
        for p, v in changes.items():
            fig.px[p] = v


def mirror_x(x0, w):
    """W layout from an E layout: the part's west edge moves, the drawing does not flip."""
    return W - x0 - w


# --- option A: causeway block ---------------------------------------------------------
def option_a(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        column(fig, 24, 10, SOLE, 12, keep=keep, joints=(4,))            # stump legs
        column(fig, 46, 10, SOLE, 12, keep=keep, joints=(4,))
        column(fig, 13, 11, 66, 22, fam='basalt_cool', keep=keep, joints=(8,))   # shoulders
        column(fig, 56, 11, 66, 21, fam='basalt_cool', keep=keep, joints=(8,))
        column(fig, 8, 8, 68, 17, keep=keep, joints=(7,))                # column-arms
        column(fig, 64, 8, 68, 16, keep=keep, joints=(6,))
        column(fig, 20, 11, 67, 29, keep=keep, joints=(15,))             # flank columns
        column(fig, 49, 11, 67, 28, keep=keep, joints=(14,))
        column(fig, 30, 20, 69, 34, fam='basalt_warm', keep=keep, joints=(15,))   # face column
        ember_eyes(fig, (34, 42), 50, keep, state='up' if view == 'Sf' else 'open')
        thrift(fig, 17, 71, [(-2, 2), (2, 3)], keep)
        thrift(fig, 40, 73, [(-4, 2), (0, 3), (4, 2)], keep, cushion=5)
        thrift(fig, 62, 71, [(-2, 3), (2, 2)], keep)
        thrift(fig, 16, 48, [(0, 2)], keep, cushion=2)
        turtle(fig, 41, 43, -1, keep, eye='open' if view == 'Sf' else 'shut')
    else:
        d = 1 if view == 'E' else -1

        def X(x0, w):
            return x0 if d == 1 else mirror_x(x0, w)
        column(fig, X(24, 10), 10, SOLE - 1, 11, keep=keep, joints=(4,))          # far leg
        column(fig, X(10, 11), 11, 65, 21, fam='basalt_cool', keep=keep, joints=(8,))
        column(fig, X(18, 11), 11, 67, 29, keep=keep, joints=(15,))
        column(fig, X(27, 16), 16, 68, 33, fam='basalt_warm', keep=keep, joints=(16,))
        column(fig, X(42, 10), 10, SOLE, 11, keep=keep, joints=(4,))              # near leg
        column(fig, X(42, 14), 14, 69, 24, fam='basalt_warm', keep=keep, joints=(11,))   # face column
        column(fig, X(53, 5), 5, 57, 7, fam='basalt_warm', keep=keep)             # the brow knob
        ember_eyes(fig, (X(48, 2),), 56, keep)
        column(fig, X(33, 8), 8, 70, 17, keep=keep, joints=(7,))                  # near arm
        thrift(fig, X(18, 1), 70, [(-2, 2), (2, 3)], keep)
        thrift(fig, X(56, 1), 72, [(-2, 2), (2, 3)], keep)
        thrift(fig, X(13, 1), 47, [(0, 2)], keep, cushion=2)
        turtle(fig, X(34, 1), 41, d, keep)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- option B: shell of columns -------------------------------------------------------
def b_dome(fig, keep, xo=0):
    """The back: a honeycomb of hex column tops rising to a low dome, back rows first, over
    a dark core that fills the joints between them."""
    core = fig.ellipse(40 + xo, 56, 27, 11)
    fig.fill(core, ROCK, 0)
    rows = [
        # (x0, w, foot, height)
        [(28, 12, 50, 18), (41, 12, 50, 19)],
        [(17, 12, 56, 17), (34, 13, 56, 21), (50, 12, 56, 17)],
        [(10, 11, 63, 14), (22, 12, 64, 18), (46, 12, 64, 18), (59, 11, 63, 14)],
    ]
    for r, row in enumerate(rows):
        for (x0, w, foot, ht) in row:
            fam = ('basalt_cool', ROCK, 'basalt_warm')[r]
            column(fig, x0 + xo, w, foot, ht, fam=fam, keep=keep, joints=(ht - 9,) if ht > 15 else ())


def option_b(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        column(fig, 15, 9, SOLE - 1, 11, keep=keep, joints=(3,))
        column(fig, 56, 9, SOLE - 1, 11, keep=keep, joints=(3,))
        b_dome(fig, keep)
        # front legs, in front of the skirt
        column(fig, 18, 10, SOLE, 9, fam='basalt_warm', keep=keep)
        column(fig, 52, 10, SOLE, 9, fam='basalt_warm', keep=keep)
        # the small boulder head poking out under the front columns
        hy = 63 if view == 'S' else 64
        head = fig.ellipse(40, hy, 8.5, 6.2)
        seam_around(fig, head, keep)
        pillow(fig, head, 'basalt_warm', glint=2, keep=keep)
        ember_eyes(fig, (35, 43), hy, keep, state='down' if view == 'Sf' else 'open', brow=True)
        thrift(fig, 11, 66, [(-2, 2), (2, 3)], keep)
        thrift(fig, 67, 66, [(-2, 3), (2, 2)], keep)
        thrift(fig, 31, 73, [(0, 2)], keep, cushion=2, bloom=0 if view == 'Sf' else None)
        thrift(fig, 49, 73, [(-2, 3), (2, 2)], keep)
        thrift(fig, 23, 48, [(0, 2)], keep, cushion=2)
        turtle(fig, 41, 36, -1, keep)
    else:
        d = 1 if view == 'E' else -1
        def X(x0, w):
            return x0 if d == 1 else mirror_x(x0, w)
        column(fig, X(14, 9), 9, SOLE - 1, 11, keep=keep, joints=(3,))
        column(fig, X(46, 9), 9, SOLE - 1, 11, keep=keep, joints=(3,))
        xo = -4 if d == 1 else 4
        b_dome(fig, keep, xo=xo)
        column(fig, X(19, 10), 10, SOLE, 9, fam='basalt_warm', keep=keep)
        column(fig, X(50, 10), 10, SOLE, 9, fam='basalt_warm', keep=keep)
        # the head pokes out toward the facing, with a brow and a snout step
        hcx = 64 if d == 1 else W - 64
        head = fig.ellipse(hcx, 60, 7.5, 6.0) | fig.ellipse(hcx + 4 * d, 61.5, 5.0, 4.0)
        seam_around(fig, head, keep)
        pillow(fig, head, 'basalt_warm', glint=2, keep=keep)
        ex = hcx + 2 if d == 1 else hcx - 4
        ember_eyes(fig, (ex,), 57, keep)
        thrift(fig, X(10, 1), 66, [(-2, 2), (2, 3)], keep)
        thrift(fig, X(34, 1), 73, [(-2, 2), (2, 3)], keep)
        thrift(fig, X(20, 1), 48, [(0, 2)], keep, cushion=2)
        turtle(fig, X(36, 1), 36, d, keep)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- option C: boulder on stumps, column crown -----------------------------------------
def option_c(view):
    fig = sk.Fig(W, H)
    keep = set()
    if view in ('S', 'Sf'):
        # crown columns behind the top of the boulder
        for (x0, w, foot, ht, fam) in ((18, 8, 50, 13, 'basalt_cool'), (25, 9, 48, 17, ROCK),
                                       (46, 9, 48, 17, ROCK), (54, 8, 50, 13, 'basalt_cool')):
            column(fig, x0, w, foot, ht, fam=fam, keep=keep)
        column(fig, 26, 11, SOLE, 12, keep=keep, joints=(4,))
        column(fig, 43, 11, SOLE, 12, keep=keep, joints=(4,))
        body = fig.ellipse(40, 56, 25.5, 13.5)
        seam_around(fig, body, keep)
        pillow(fig, body, 'basalt_warm', glint=3, keep=keep, cap=0.5, crescent=1.0, tones=(4, 3, 1))
        # cooling cracks as short joint clusters
        for (cx, cy) in ((22, 60), (23, 61), (56, 63), (57, 62), (44, 66), (45, 66)):
            fig.put(cx, cy, fig.px[(cx, cy)][0], 0)
        ember_eyes(fig, (32, 46), 54, keep, state='up' if view == 'Sf' else 'open')
        for (x0, foot, ht) in ((9, 68, 16), (62, 68, 16)):
            column(fig, x0, 9, foot, ht, keep=keep, joints=(6,))
        thrift(fig, 19, 72, [(-2, 2), (2, 3)], keep)
        thrift(fig, 61, 72, [(-2, 3), (2, 2)], keep)
        thrift(fig, 40, 73, [(0, 2)], keep, cushion=2)
        thrift(fig, 21, 49, [(0, 2)], keep, cushion=2)
        if view == 'Sf':
            # the turtle wakes and leans over the brow to peer down at him
            turtle(fig, 40, 45, 1, keep, eye='open')
        else:
            turtle(fig, 39, 44, -1, keep)
    else:
        d = 1 if view == 'E' else -1
        def X(x0, w):
            return x0 if d == 1 else mirror_x(x0, w)
        for (x0, w, foot, ht, fam) in ((14, 8, 50, 13, 'basalt_cool'), (21, 9, 48, 17, ROCK),
                                       (41, 9, 48, 16, ROCK)):
            column(fig, X(x0, w), w, foot, ht, fam=fam, keep=keep)
        column(fig, X(22, 11), 11, SOLE - 1, 11, keep=keep, joints=(4,))
        column(fig, X(44, 11), 11, SOLE, 12, keep=keep, joints=(4,))
        cx = 38 if d == 1 else W - 38
        body = fig.ellipse(cx, 56, 24.5, 13.5)
        # a brow and snout step on the facing side
        # a blunt face: a flat front under a brow, the cheek stepping back below it
        body |= fig.rect(cx + (13 if d == 1 else -27), 50, cx + (27 if d == 1 else -13), 63, knock=4)
        seam_around(fig, body, keep)
        pillow(fig, body, 'basalt_warm', glint=3, keep=keep, cap=0.5, crescent=1.0, tones=(4, 3, 1))
        for (bx, by) in ((cx - 15 * d, 61), (cx - 14 * d, 62), (cx + 3 * d, 66), (cx + 4 * d, 66)):
            fig.put(bx, by, fig.px[(bx, by)][0], 0)
        ex = cx + 21 if d == 1 else cx - 23
        ember_eyes(fig, (ex,), 55, keep)
        # the brow ledge runs out to the face's edge, a lit top over a dark under-cut
        for k in range(0, 6):
            bx = ex + 3 + k if d == 1 else ex - 2 - k
            if is_rock(fig, (bx, 53)):
                fig.put(bx, 53, 'basalt_warm', 4 if d == -1 or k < 3 else 3)
                fig.put(bx, 54, 'basalt_warm', 0)
        for k in range(0, 4):                                  # the cheek steps back
            bx = ex + 5 + k if d == 1 else ex - 4 - k
            if is_rock(fig, (bx, 60)):
                fig.put(bx, 60, 'basalt_warm', 0)
        column(fig, X(31, 9), 9, 69, 16, keep=keep, joints=(6,))
        thrift(fig, X(18, 1), 72, [(-2, 2), (2, 3)], keep)
        thrift(fig, X(57, 1), 72, [(-2, 3), (2, 2)], keep)
        thrift(fig, X(17, 1), 49, [(0, 2)], keep, cushion=2)
        turtle(fig, X(32, 1), 44, d, keep)
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('Sf', 'S fidget'))

OPTIONS = [
    dict(
        label='A', name='Causeway block: a squat cluster of short hex columns, the turtle on the flat middle top',
        question='The body is the columns: a tall face column in the middle, shoulder columns either side, '
                 'column-arms hanging at the ends and two stump legs; a stepped skyline silhouette.',
        fn=option_a, palette=['basalt', 'berry', 'leaf', 'lagoon'],
        pose='Planted like a headland, arms hanging, a patient bulwark that the sea has given up arguing with.',
        parts=[
            'legs x2 (basalt stump columns): layer 0; foot; 6-frame shuffle, each stump lifts 2 px, the body sways 1 px',
            'shoulder columns x2 (basalt_cool): layer 1; hip; breath sinks them 1 px after the body',
            'arm columns x2 (basalt): far layer 1, near 3; shoulder; swing 2 px in walk, raised as a block in guard, a slam in strike',
            'face column (basalt_warm, ember eyes, broad top): layer 2; hip; breath 1 px, the head of every pose',
            'thrift tufts (berry on leaf): layer 4; foot (base) and shoulder; grow one layer per still turn (Overgrow), one flies off on a heavy hit',
            'turtle (lagoon_cool shell, lagoon_warm head and flippers): layer 5; back (the face column top); sleeps, wakes in the fidget, tucks in on hit',
        ],
        notes=[
            'Works: a flat-topped stepped block reads at once as a giant\'s causeway and nothing else in the cast is rectangular and dark.',
            'Risk: the face is on the body (no separate head), so the head-third rule is met by the face column, not a neck.',
            'Compared with Eastward 05 (night camp), scaled to his height: trailers and crates carry a lit top plane, two side tones and a dark seam, as each column does here.',
        ]),
    dict(
        label='B', name='Shell of columns: a tortoise-like dome of hex tops, a small boulder head poking out',
        question='The body is a low dome made of a honeycomb of hex column tops, crouched on four stubby column legs, '
                 'with a small round head at the front: turtle on a tortoise.',
        fn=option_b, palette=['basalt', 'berry', 'leaf', 'lagoon'],
        pose='Crouched low and content, head barely out of the shell, as slow as a tide coming in.',
        parts=[
            'legs x4 (basalt stump columns, back pair one tone cooler): layer 0/2; foot; diagonal pairs step in the walk',
            'dome (basalt honeycomb, three rows of columns): layer 1; hip; breath lifts the middle row 1 px',
            'head (basalt_warm boulder, ember eyes): layer 3; chest; pokes out 2 px to strike, pulls in for guard and nap',
            'thrift tufts (berry on leaf): layer 4; foot and dome rim; Overgrow layers sprout between the columns',
            'turtle (lagoon_cool plated shell, sand skin): layer 5; back (the dome crown); turtle on a tortoise, it holds on in the walk',
        ],
        notes=[
            'Works: the honeycomb back is the clearest read of hex columns, and the dome is a silhouette no other folk has.',
            'Risk: four legs and a head-out pose are a quadruped; fight poses must happen with the head and front legs.',
            'Compared with Eastward 05: the cliff-edge rock clumps, a hard lit cap and dark crescent per lump, as on each hex top and the head.',
        ]),
    dict(
        label='C', name='Boulder on stumps: one wide glossy boulder, column legs and arms, a crown of columns',
        question='The body is a single glossy boulder; the columns are his stump legs, his arms and a crown at the '
                 'back of the top, with the turtle nested in the crown\'s gap.',
        fn=option_c, palette=['basalt', 'berry', 'leaf', 'lagoon'],
        pose='A round, heavy, gentle lump with his chin down, watching the tide line without blinking.',
        parts=[
            'legs x2 (basalt stump columns): layer 0; foot; short waddle, the boulder rocks 1 px side to side',
            'crown columns x4 (basalt, the outer pair cool): layer 1; back of the body; rattle a frame late on hops',
            'boulder body (basalt_warm, brow, ember eyes): layer 2; hip; breath swells 1 px',
            'arm columns x2 (basalt): layer 1 far / 3 near; shoulder; swing, punch, guard',
            'thrift tufts (berry on leaf): layer 4; foot and shoulder; Overgrow layers',
            'turtle (lagoon_cool plated shell, sand skin): layer 5; back (the crown nest); peers over the brow in the fidget',
        ],
        notes=[
            'Works: the biggest, simplest silhouette; the gloss on one big boulder reads strongest at 2 px.',
            'Risk: only the crown and limbs say "hex columns"; from the front it is closest to a generic rock golem.',
            'Compared with Eastward 05: the folk there are about 32 native px with 2 x 2 eyes; his ember eyes match that read at 2 px.',
        ]),
]


# =====================================================================================
# FINAL (revision round, 21 Oct): option A, the causeway block, with grafts.
#   - from B: a small round boulder head poking out at the front, with the ember eyes,
#     so he is a creature, not furniture; in profile it has a brow, a cheek and a snout step.
#   - from C: hex faceting on the shoulders; the back shoulder is a flat-topped column,
#     the familiar's perch, kept apart from the turtle's place on the middle column.
#   - the turtle redrawn: a head, a plated shell lit at the upper left, four flippers and
#     a closed eye.
#   - thrift heads at least 3 x 3 berry clusters, so they read at game scale.
#   - side views about 60 px wide; about 44 art px tall.
# =====================================================================================
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/tuff-final.png')
FSHELL, FSKIN = 'lagoon_cool', 'sand'


def f_turtle(fig, x, base, d, keep, eye='shut'):
    """The sea turtle, readable at 2 px: a plated shell (three vertebral plates over a rim
    of marginal plates) lit as a cap at the upper left, four flippers, a head on a neck.
    eye: 'shut' (asleep), 'open' (awake, head raised) or 'tucked' (head pulled in: hit)."""
    for xx in range(x - 8, x + 9):                      # contact shadow on the rock
        if is_rock(fig, (xx, base)):
            fig.put(xx, base, fig.px[(xx, base)][0], 1)
    # flippers: a front pair toward d and a back pair, splayed, 3 x 2 each
    for fx, fy, back in ((x + d * 6, base, False), (x - d * 8, base, True)):
        cells = [(fx, fy - 1), (fx + d, fy - 1), (fx + d, fy), (fx + 2 * d, fy)] if not back else \
                [(fx, fy - 1), (fx - d, fy - 1), (fx - d, fy), (fx - 2 * d, fy)]
        for (px_, py) in cells:
            fig.put(px_, py, FSKIN, 3 if py < fy else 2)
    shell = {p for p in fig.ellipse(x, base - 1.0, 8.5, 5.6) if p[1] <= base - 1}
    pillow(fig, shell, FSHELL, glint=0, cap=0.75, crescent=1.25)
    top = min(p[1] for p in shell)
    for (sx, sy) in shell:
        u = sx - x
        t = fig.px[(sx, sy)][1]
        if sy == base - 1:
            t = 1 if (u + 8) % 3 == 0 else 2           # marginal plates: a notched dark rim
        elif sy == base - 2:
            t = 1                                        # the seam over the rim
        elif u in (-3, 3) or (sy == top + 1 and abs(u) <= 1):
            t = 1 if t <= 3 else 2                       # seams between the vertebral plates
        fig.put(sx, sy, FSHELL, t)
    # the lit cap of the west plate, a crisp glint
    for p in ((x - 6, top + 2), (x - 5, top + 2)):
        if p in shell:
            fig.put(p[0], p[1], FSHELL, 5)
            keep.add(p)
    if eye == 'tucked':
        fig.put(x + d * 8, base - 2, FSKIN, 2)
        fig.put(x + d * 8, base - 1, FSKIN, 1)
        return shell
    awake = eye == 'open'
    nx = x + d * 7
    spec = ({-5: (2, 5), -4: (1, 6), -3: (0, 6), -2: (-1, 3), -1: (-1, 2)} if awake else
            {-4: (2, 5), -3: (1, 6), -2: (0, 7), -1: (-1, 6)})
    head = {(nx + d * cx, base + cy) for cy, (a, b) in spec.items() for cx in range(a, b + 1)}
    ys = [p[1] for p in head]
    for (px_, py) in head:
        t = 3
        if py == min(ys) or (px_ - 1, py) not in head:
            t = 4
        elif py == max(ys) or (px_ + 1, py) not in head:
            t = 2
        fig.put(px_, py, FSKIN, t)
    ey = base - (4 if awake else 3)
    if awake:
        for p in ((nx + d * 4, ey), (nx + d * 4, ey - 1)):
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
    else:
        for p in ((nx + d * 3, ey), (nx + d * 4, ey)):
            fig.put(p[0], p[1], FSKIN, 0)              # the closed eye, a dark lid line
            keep.add(p)
    return shell | head


def f_thrift(fig, x, base, heads, keep, cushion=3, bloom=None):
    """Sea thrift: a leaf cushion with berry pompoms, each at least 3 x 3, on short stems."""
    cush = fig.ellipse(x + 0.5, base - 0.5, cushion + 0.5, 1.7)
    ytop = min(p[1] for p in cush)
    for (cx, cy) in cush:
        t = (4 if cx <= x else 3) if cy == ytop else (3 if cx <= x else 2)
        fig.put(cx, cy, 'leaf', t)
    for k, (dx, stem) in enumerate(heads):
        hx = x + dx
        top = base - 1 - stem
        for yy in range(top + 1, base - 1):
            fig.put(hx, yy, 'leaf', 2)
        if bloom == k:
            rows = {top - 4: (-1, 1, (4, 4, 3)), top - 3: (-2, 2, (4, 4, 4, 3, 3)),
                    top - 2: (-2, 2, (4, 4, 3, 3, 2)), top - 1: (-2, 2, (3, 3, 3, 2, 2)),
                    top: (-1, 1, (2, 2, 1))}
            glint = ((hx - 1, top - 3), (hx, top - 3))
        else:
            rows = {top - 2: (-1, 1, (4, 4, 3)), top - 1: (-1, 1, (4, 3, 2)), top: (-1, 1, (3, 2, 1))}
            glint = ()
        for yy, (a0, a1, ts) in rows.items():
            for i, xx in enumerate(range(hx + a0, hx + a1 + 1)):
                fig.put(xx, yy, 'berry', ts[i])
        for p in glint:
            fig.put(p[0], p[1], 'berry', 5)
            keep.add(p)


def f_head(fig, cx, cy, d, keep, eyes='open', rx=9.0, ry=6.6):
    """The small boulder head (from B). d=0 faces S; d=+1/-1 is a profile with a brow
    ledge, a cheek and a snout step toward d, lit from the upper left in both."""
    if d == 0:
        head = fig.ellipse(cx, cy, rx, ry)
        seam_around(fig, head, keep)
        pillow(fig, head, 'basalt_warm', glint=2, keep=keep, cap=0.5, crescent=1.0, tones=(4, 3, 1))
        ember_eyes(fig, (cx - 5, cx + 3), cy - 1, keep, state=eyes)
        # a mouth seam under the eyes, a short dark crease
        for xx in range(cx - 2, cx + 2):
            if is_rock(fig, (xx, cy + 3)):
                fig.put(xx, cy + 3, 'basalt_warm', 1)
        return head
    skull = fig.ellipse(cx - d, cy, rx - 1.5, ry)
    # the snout: a blunt block stepping forward below the eye
    sx0, sx1 = (cx + 2, cx + 10) if d == 1 else (cx - 10, cx - 2)
    snout = fig.rect(sx0, cy, sx1, cy + 4, knock=2)
    head = skull | snout
    seam_around(fig, head, keep)
    pillow(fig, skull, 'basalt_warm', glint=2, keep=keep, cap=0.5, crescent=1.0, tones=(4, 3, 1))
    for (x, y) in snout:
        if (x, y) in skull and y < cy + 2:
            continue
        r = y - cy
        t = 4 if r == 0 else (1 if r == 4 else 3 if (x - d, y) in skull or d == -1 else 2)
        fig.put(x, y, 'basalt_warm', t)
    fx = sx1 if d == 1 else sx0
    for y in range(cy + 1, cy + 4):                      # the snout's end face
        fig.put(fx, y, 'basalt_warm', 1 if d == 1 else 3)
    ex = cx + (3 if d == 1 else -4)
    ember_eyes(fig, (ex,), cy - 2, keep, state=eyes, brow=True)
    # the brow ledge runs from the eye to one pixel past the skull's front: a lit top
    front = max(x for (x, y) in skull if y == cy - 4) if d == 1 else min(x for (x, y) in skull if y == cy - 4)
    for bx in range(min(ex + 2, front + d), max(ex - 1, front + d) + 1):
        if (bx, cy - 4) not in keep:
            fig.put(bx, cy - 4, 'basalt_warm', 4)
            head.add((bx, cy - 4))
    # the cheek crease where the skull meets the snout
    for y in range(cy + 1, cy + 4):
        x = cx + d * 1
        if is_rock(fig, (x, y)):
            fig.put(x, y, 'basalt_warm', 1)
    return head


def hprism(fig, xa, xb, y, d, keep, thick=8, fam=ROCK):
    """A column lying on its side (an arm thrust out or held up across): a lit top plane,
    a south face with a gloss line, a dark underside and a hexagonal end cap at the fist."""
    x0, x1 = min(xa, xb), max(xa, xb)
    mask = set()
    for yy in range(y, y + thick):
        for xx in range(x0, x1 + 1):
            if (yy in (y, y + thick - 1)) and xx in (x0, x1):
                continue
            mask.add((xx, yy))
    seam_around(fig, mask, keep)
    fist = xb
    for (xx, yy) in mask:
        r = yy - y
        t = 4 if r < 3 else (1 if r == thick - 1 else 2)
        if r == 4:
            t = 3                                        # gloss line along the side
        if abs(xx - fist) <= 2:                          # the hex end cap
            t = (3 if r < 3 else 2) if d == 1 else (4 if r < thick - 2 else 3)
            if abs(xx - fist) == 2:
                t = 0 if d == 1 else 1                   # the joint between cap and side
        fig.put(xx, yy, fam, t)
    mid = (x0 + x1) // 2
    for yy in range(y, y + thick):                       # a cross joint
        if (mid, yy) in mask and abs(mid - fist) > 4:
            fig.put(mid, yy, fam, 0 if yy - y >= 3 else 1)
            if (mid + 1, yy) in mask:
                fig.put(mid + 1, yy, fam, 4 if yy - y < 3 else 3)
    for p in sorted(mask, key=lambda q: (q[1], q[0]))[1:3]:
        fig.put(p[0], p[1], fam, 5)
        keep.add(p)
    return mask


def mossling(fig, cx, base, d, keep, curled=False):
    """Stand-in familiar (24 art px): a round leaf-green blob, two ink eyes, a sprout."""
    if curled:
        body = fig.ellipse(cx, base - 5, 7.5, 5.5)
        pillow(fig, body, 'leaf', glint=0)
        for x in (cx - 3, cx + 1):
            fig.put(x, base - 6, 'ink', 0)
            fig.put(x + 1, base - 6, 'ink', 0)
            keep |= {(x, base - 6), (x + 1, base - 6)}
        for (x, y, t) in ((cx + 4, base - 11, 4), (cx + 5, base - 11, 4), (cx + 6, base - 10, 3), (cx + 5, base - 12, 4)):
            fig.put(x, y, 'leaf_warm', t)
        return body
    body = fig.ellipse(cx, base - 9, 8, 9)
    seam_around(fig, body, keep)
    pillow(fig, body, 'leaf', glint=0)
    ey = base - 11
    for ex in ((cx, cx + 4) if d == 1 else (cx - 5, cx - 1)):
        for p in ((ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)):
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
    top = base - 18
    fig.put(cx, top, 'leaf_warm', 3)
    fig.put(cx, top - 1, 'leaf_warm', 3)
    for (x, y, t) in ((cx - 1, top - 2, 4), (cx - 2, top - 2, 4), (cx - 2, top - 3, 4),
                      (cx + 1, top - 2, 3), (cx + 2, top - 2, 2), (cx + 2, top - 3, 3)):
        fig.put(x, y, 'leaf_warm', t)
    return body


def finish(fig, keep):
    fig.outline()
    despeckle(fig, keep)
    despeckle(fig, keep)
    return fig


# --- front ---------------------------------------------------------------------------
def final_front(view):
    """S idle ('S') and the fidget key pose ('Sf': the turtle wakes, lifts its head and
    blinks while Tuff holds still and rolls his eyes up to it)."""
    fig = sk.Fig(W, H)
    keep = set()
    column(fig, 23, 11, SOLE, 12, keep=keep, joints=(4,))                 # stump legs
    column(fig, 46, 11, SOLE, 12, keep=keep, joints=(4,))
    column(fig, 9, 13, 60, 17, fam='basalt_cool', keep=keep, joints=(9,))  # flat shoulders
    column(fig, 58, 13, 60, 17, fam='basalt_cool', keep=keep, joints=(9,))
    column(fig, 7, 9, 69, 19, keep=keep, joints=(7,))                      # column-arms
    column(fig, 64, 9, 69, 19, keep=keep, joints=(7,))
    column(fig, 18, 12, 66, 29, keep=keep, joints=(14,))                   # flank columns
    column(fig, 50, 12, 66, 28, keep=keep, joints=(13,))
    column(fig, 28, 24, 64, 32, fam='basalt_warm', keep=keep, joints=(12,), th=10)   # the turtle's column
    f_head(fig, 40, 58, 0, keep, eyes='up' if view == 'Sf' else 'open')
    f_thrift(fig, 16, 72, [(-2, 2), (2, 3)], keep)
    f_thrift(fig, 40, 74, [(-4, 2), (0, 3), (4, 2)], keep, cushion=5)
    f_thrift(fig, 63, 72, [(-2, 3), (2, 2)], keep)
    f_thrift(fig, 13, 45, [(0, 2)], keep, cushion=2)
    f_turtle(fig, 40, 41, -1, keep, eye='open' if view == 'Sf' else 'shut')
    return finish(fig, keep)


def final_nap():
    """nap_c: he settles like a rock: legs folded away, arms tucked, the head pulled down
    to the ground, eyes shut; the turtle sleeps on; the familiar curls against his right."""
    fig = sk.Fig(W, H)
    keep = set()
    mossling(fig, 66, SOLE + 1, 1, keep, curled=True)
    column(fig, 10, 13, 70, 14, fam='basalt_cool', keep=keep, joints=(7,))
    column(fig, 54, 13, 70, 13, fam='basalt_cool', keep=keep, joints=(7,))
    column(fig, 17, 12, 71, 25, keep=keep, joints=(12,))
    column(fig, 49, 12, 71, 24, keep=keep, joints=(12,))
    column(fig, 27, 24, 70, 31, fam='basalt_warm', keep=keep, joints=(13,), th=10)
    f_head(fig, 40, 66, 0, keep, eyes='shut', ry=6.0)
    f_thrift(fig, 13, 74, [(-2, 2), (2, 3)], keep)
    f_thrift(fig, 58, 74, [(0, 2)], keep, cushion=2)
    f_turtle(fig, 39, 48, -1, keep)
    return finish(fig, keep)


# --- profiles and fight poses ---------------------------------------------------------
# pose: (bx forward, by down, arm, legs, eyes, turtle, head dx, head dy)
POSES = {
    'idle':   (0, 0, 'hang', 'stand', 'open', 'shut', 0, 0),
    'ready':  (1, 1, 'forward', 'wide', 'open', 'shut', 1, 1),
    'strike': (3, 1, 'reach', 'lunge', 'open', 'shut', 2, 1),
    'cast':   (0, 0, 'up', 'wide', 'up', 'open', 0, -1),
    'hit':    (-2, 0, 'back', 'stumble', 'shut', 'tucked', -2, -1),
    'sit':    (0, 5, 'rest', 'sit', 'shut', 'shut', 1, 1),
    'cheer':  (0, -3, 'up', 'tuck', 'up', 'open', 0, -1),
}


def final_side(d, pose='idle', familiar=False):
    bx, by, arm, legs, eyes, teye, hdx, hdy = POSES[pose]
    fig = sk.Fig(W, H)
    keep = set()

    def X(x0, w):           # an E-facing layout's west edge, moved for W (not flipped)
        x0 = x0 + bx
        return x0 if d == 1 else W - x0 - w

    def U(x):               # an E-facing point, moved for W
        x = x + bx
        return x if d == 1 else W - 1 - x
    # legs: far stump first, then near (a tone warmer)
    lift = {'stand': (0, 0), 'wide': (0, 0), 'lunge': (0, 0), 'stumble': (0, 2), 'tuck': (3, 3), 'sit': None}[legs]
    lx = {'stand': (20, 39), 'wide': (18, 41), 'lunge': (16, 43), 'stumble': (17, 37), 'tuck': (21, 38)}.get(legs)
    if lift is not None:
        column(fig, X(lx[0], 11), 11, SOLE - 1 - lift[0], 11, keep=keep, joints=(4,))
    # the back shoulder: a flat-topped hex column, the familiar's perch, away from the foe
    sh = (X(9, 14), 14, 61 + by, 19)
    column(fig, sh[0], sh[1], sh[2], sh[3], fam=ROCK if d == 1 else 'basalt_cool', keep=keep, joints=(10,), th=6)
    perch = (sh[0] + 7, sh[2] - sh[3] + 4)
    if familiar:
        mossling(fig, perch[0] + (-1 if d == 1 else 1), perch[1] + 1, d, keep)
    column(fig, X(19, 12), 12, 65 + by, 28, keep=keep, joints=(13,))
    column(fig, X(27, 22), 22, 66 + by, 33, fam='basalt_warm', keep=keep, joints=(13,), th=9)
    if lift is not None:
        column(fig, X(lx[1], 11), 11, SOLE - lift[1], 12, fam='basalt_warm', keep=keep, joints=(4,))
    else:   # sitting: the stumps stick out in front, hex ends toward us
        column(fig, X(44, 10), 10, SOLE, 7, keep=keep)
        column(fig, X(51, 10), 10, SOLE, 6, fam='basalt_warm', keep=keep)
    # the boulder head pokes out in front, low under the turtle's column
    f_head(fig, U(57 + hdx), 55 + by + hdy, d, keep, eyes=eyes)
    # thrift at the base (fixed to the feet) and on the back shoulder's rim
    f_thrift(fig, U(15), 72, [(-2, 2), (2, 3)], keep)
    if pose not in ('strike', 'sit'):
        f_thrift(fig, U(52), 73, [(-2, 3), (2, 2)], keep)
    if pose == 'hit':                                  # a heavy hit knocks the top layer off
        for (p, t) in (((U(52), 30), 4), ((U(53), 30), 4), ((U(51), 31), 4), ((U(52), 31), 3), ((U(53), 31), 2),
                       ((U(51), 32), 3), ((U(52), 32), 2), ((U(53), 32), 1), ((U(50), 33), 2), ((U(49), 34), 2)):
            fig.put(p[0], p[1], 'berry', t)
    f_turtle(fig, U(37), 40 + by, d, keep, eye=teye)
    # the near arm last, in front
    if arm == 'hang':
        column(fig, X(35, 10), 10, 70 + by, 20, keep=keep, joints=(8,))
    elif arm == 'rest':
        column(fig, X(35, 10), 10, 72, 15, keep=keep, joints=(6,))
    elif arm == 'back':
        column(fig, X(22, 10), 10, 69, 19, keep=keep, joints=(8,))
    elif arm == 'up':
        column(fig, X(45, 9), 9, 53 + by, 26, keep=keep, joints=(10,))
        if pose == 'cast':                            # Overgrow: a frond and a flower burst on the fist
            fx = U(49)
            ftop = 53 + by - 26
            f_thrift(fig, fx, ftop + 1, [(-3, 2), (1, 4)], keep, cushion=3, bloom=1)
    elif arm == 'forward':
        hprism(fig, U(40), U(62), 60 + by, d, keep, thick=7)
    elif arm == 'reach':
        hprism(fig, U(40), U(74), 61 + by, d, keep, thick=7)
    return finish(fig, keep), perch


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
    label='A final', chosen='A',
    name='Causeway block with a boulder head: short glossy hex columns, the turtle on the middle top',
    grafts=[
        'From B: a small round boulder head poking out at the front, low under the turtle\'s column, with the ember eyes; '
        'in profile a brow ledge, a cheek and a snout step, lit from the upper left.',
        'From C: hex faceting on the shoulders; the back shoulder is a flat-topped column, the familiar\'s perch in every '
        'fight frame, apart from the turtle on the middle column.',
        'Turtle redrawn: a pale sand head on a neck (it read as part of the shell in lagoon), a plated shell (three vertebral plates, notched marginal rim) with a lit cap and '
        'glint at the upper left, four flippers, a closed eye (open in the fidget, tucked in on a hit).',
        'Thrift heads are 3 x 3 berry clusters (5 x 5 when one blooms in the cast).',
    ],
    palette=['basalt', 'berry', 'leaf', 'lagoon', 'sand'],
    pose='Planted like a headland, arms hanging, head low and patient: the sea gave up arguing with him long ago.',
    parts=[
        'legs x2 (basalt stump columns, near one basalt_warm): layer 0 far / 3 near; foot; all facings; 6-frame shuffle, a stump lifts 2 px',
        'back shoulder (basalt on the lit west in E, basalt_cool on the east in W; flat hex top = familiar perch): layer 1; chest; E/W swap sides (the shoulder away from the foe); breath 1 px late',
        'flank column (basalt): layer 1; hip; all facings',
        'turtle column (basalt_warm, broad hex top): layer 2; hip; all facings; breath 1 px',
        'head (basalt_warm boulder, ember eyes in lava glow, brow, mouth seam): layer 4; chest; S front, E/W profile with snout step; pokes forward 2 px in strike',
        'near arm (basalt column; a lying column with a hex end cap when thrust): layer 6; shoulder; hangs, thrusts in ready/strike, up in cast/cheer, back in hit',
        'thrift tufts (berry 3 x 3 heads on leaf cushions): layer 5; foot and shoulder; Overgrow adds a layer per still turn, a hit throws the top one off',
        'turtle (lagoon_cool plated shell, sand skin): layer 5; back (the turtle column top); sleeps; wakes in the fidget, cast and cheer; tucks in on hit',
        'familiar (stand-in Mossling, 24 art px): layer 1.5; back shoulder top; fight poses only',
    ],
    notes=[
        'Works: the stepped block of glossy columns says "basalt causeway" and is nothing like Cairn\'s tall mossy slab; the head makes him a creature.',
        'Fights: the near arm is the only moving limb (hang, thrust as a lying column, raised), so every key pose is a rigid offset of parts.',
        'Width: E/W span about 60 px, so the back shoulder runs about 27 px behind the foot, a little over the 24 px follower margin.',
        'Compared with Eastward 05 (night camp, about 32 native px folk): 2 x 2 eyes, lit top planes and dark seams; '
        'and with the camp\'s cliff-edge rock clumps for the lit cap and crescent on the head.',
    ],
)


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
        print(f"final {cap:9s} {width(im):2d}x{height(im):2d}  on house {100*m['on_house']:5.1f}%  "
              f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
              f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
        nums[cap]['width_px'] = width(im)
        if perch:
            perches[cap] = list(perch)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('Tuff final (folk 11, the Tidebloom Isles): A, the causeway block, with grafts', [entry], OUT_FINAL,
                    note='About 44 art px, cell 80 x 80, foot (40, 74). World S/E/W, fidget, nap; fight E and W with '
                         'the stand-in Mossling on the back shoulder.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], glow='lava (eyes, light source only)', pose=FINAL['pose'],
                perch_anchor=perches, measure=nums, notes=FINAL['notes'], _ok=ok)



def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


def width(im):
    a = im.getchannel('A')
    xs = [x for x in range(im.width) if any(a.getpixel((x, y)) for y in range(im.height))]
    return xs[-1] - xs[0] + 1 if xs else 0


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
            print(f"{o['label']} {cap:9s} {width(im):2d}x{height(im):2d}  on house {100*m['on_house']:5.1f}%  "
                  f"W-E {m['west_east']:+5.1f}  lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  "
                  f"outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
            nums[cap]['height_px'] = height(im)
            nums[cap]['width_px'] = width(im)
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], glow='lava (eyes, light source only)', pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('Tuff (folk 11, the Tidebloom Isles): how hex columns make a low, wide body', OPTIONS, OUT_PNG,
                    note='About 44 art px tall, 60 wide; cell 80 x 80, foot (40, 74). Views: S, E, W idle and the S '
                         'fidget key pose (the turtle wakes, or a thrift flower pops).')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='tuff', height_art_px=44, width_art_px=60, cell=[W, H], foot=[AX, AY],
                       question='How hex columns make a low, wide body.',
                       options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
