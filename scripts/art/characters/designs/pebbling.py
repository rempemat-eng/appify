"""The Pebbling, the FOCUS Grassling (species CUBE): three familiar design options (Claude J lane).

Main question: a cube-ish pebble creature with focus. Stone family, grass accents, small,
round-cornered, light grey-blue (slate, never Cairn's grey stone with moss or Tuff's
basalt), big eyes or a focused squint that reads at 2 device px on grass.

Today's identity (scripts/art/pets.py, `pebbling`): a rounded stone block on two stubby
feet, round reading glasses, a sprout on top where growth comes out, a little reading
lamp. Each option keeps a piece of it:

    A  Reading pebble: one rounded cube, round brass reading glasses over big eyes, a
       single grass leaf on a short stem, stub feet.
    B  Lamp-stone stack: a big head pebble on a small body pebble, a grass collar tuft
       between them, a lamp-lit facet on the forehead, a calm focused squint.
    C  Bowl-cut block: a squarer soft cube with a grass fringe cut straight above big
       eyes, tiny legs and nub arms.

Views (familiar rules, batch 3): S idle, E idle, W idle, S hop (airborne), S nap (curled),
E perch and W perch (16 px, its own drawing in a 24 x 24 cell, foot (12, 22)). W is drawn
with its own light from the upper left, never mirrored pixels.

Run from the repo root:
    CHAR_VIEWS=<dir> python3 scripts/art/characters/designs/pebbling.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sheetkit as sk  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT_PNG = os.path.join(ROOT, 'docs/vision/characters/designs/pebbling-options.png')
OUT_JSON = os.path.join(ROOT, 'docs/vision/characters/designs/pebbling.json')
OUT_FINAL = os.path.join(ROOT, 'docs/vision/characters/designs/pebbling-final.png')
SCRATCH = os.path.join(os.environ.get('CHAR_VIEWS', os.path.join(ROOT, '.char-views')), 'pebbling')

W, H = 32, 32
AX, AY = 16, 28            # foot anchor: soles fill row 27, their outline lands on row 28
SOLE = AY - 1
PW, PH = 24, 24            # perch cell
PX, PY = 12, 22
PSOLE = PY - 1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
STONE = 'slate'            # light grey-blue pebble (Cairn is stone, Tuff basalt)


# --- painting helpers (local to this design; sheetkit stays untouched) -----------------
def tone(fig, p):
    v = fig.px.get(p)
    return v[1] if v and isinstance(v[1], int) else None


def fam_at(fig, p):
    v = fig.px.get(p)
    return v[0] if v else None


def blob(fig, cx, cy, rx, ry, e=2.0):
    """Superellipse mask: e=2 a pebble, e=3 a rounded cube, e=4.5 a soft box."""
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = abs((x + 0.5 - cx) / rx), abs((y + 0.5 - cy) / ry)
            if u ** e + v ** e <= 1.0 and fig.inside(x, y):
                out.add((x, y))
    # no one-pixel nubs: drop pixels with nothing above and below (the widest row's tips)
    out = {p for p in out if (p[0], p[1] - 1) in out or (p[0], p[1] + 1) in out}
    return out


def pebble(fig, mask, fam=STONE, cap=0.40, crescent=1.05, glint=True, top_plane=0):
    """A round part shaded as a form: a warm lit cap offset to the upper left, the body,
    a cool dark crescent at the lower right that follows the outline, and a cool
    underside row. `top_plane` rows at the top are lifted to the lit tone (the flat top
    of a rounded cube), so the cube reads as a top plane over a west and south face."""
    mask = set(mask)
    if not mask:
        return mask
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    rx, ry = max(1.0, (max(xs) - min(xs) + 1) / 2), max(1.0, (max(ys) - min(ys) + 1) / 2)
    top = {}
    for (x, y) in mask:
        top[x] = min(top.get(x, 99), y)
    for (x, y) in mask:
        u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        f, t = fam + '_warm', 3
        if (u + 0.40) ** 2 + (v + 0.48) ** 2 < cap:
            f, t = fam + '_warm', 4
        elif top_plane and y - top[x] < top_plane and u < 0.55:
            f, t = fam + '_warm', 4
        if (u + 0.30) ** 2 + (v + 0.30) ** 2 > crescent:
            f, t = fam, 2
        if (x, y + 1) not in mask and u > -0.45:
            f, t = fam + '_cool', 1
        fig.put(x, y, f, t)
    if glint:
        lit = sorted((p for p in mask if fam_at(fig, p) == fam + '_warm'),
                     key=lambda p: (p[0] - cx) / rx * 0.6 + (p[1] - cy) / ry)
        if lit:
            g = lit[0]
            fig.put(g[0], g[1], fam + '_warm', 5)
            nb = (g[0] + 1, g[1]) if (g[0] + 1, g[1]) in mask else (g[0], g[1] + 1)
            fig.put(nb[0], nb[1], fam + '_warm', 5)
    return mask


def pits(fig, pts, fam=STONE):
    """Pebble texture: a few 2 px pits (a dark pixel and its lit lower lip), only on the
    body tone, never as speckle."""
    body = (fam + '_warm', 3)
    for (x, y, horiz) in pts:
        a, b = (x, y), ((x + 1, y) if horiz else (x, y + 1))
        if fig.px.get(a) == body and fig.px.get(b) == body:
            fig.put(a[0], a[1], fam, 2)
            fig.put(b[0], b[1], fam, 2)
            lip = (a[0], a[1] + 1) if horiz else (a[0] - 1, a[1])
            lip2 = (b[0], b[1] + 1) if horiz else (b[0] - 1, b[1])
            if fig.px.get(lip) == body and fig.px.get(lip2) == body:
                fig.put(lip[0], lip[1], fam + '_warm', 4)
                fig.put(lip2[0], lip2[1], fam + '_warm', 4)


def blades(fig, mask, lit='grass', dark='leaf'):
    """Grass in directional strands: a warm lit west band, the body, the shaded east band
    in leaf, the tips (lowest pixel of each column) a tone down; every third column a
    darker strand, two or three pixels long, so the fringe reads as combed blades."""
    mask = set(mask)
    rows, cols = {}, {}
    for (x, y) in mask:
        rows.setdefault(y, []).append(x)
        cols.setdefault(x, []).append(y)
    for (x, y) in mask:
        xl, xr = min(rows[y]), max(rows[y])
        span = max(1, xr - xl)
        u = (x - xl) / span
        f, t = lit, 3
        if u < 0.3:
            f, t = lit, 4
        if y == min(cols[x]) and u < 0.75:
            f, t = lit + '_warm', 4
        if u > 0.72:
            f, t = dark, 3
        if y == max(cols[x]):
            f, t = (dark, 2) if u > 0.4 else (lit, 2)
        fig.put(x, y, f, t)
    # combed strands: a two-pixel darker stroke above every fourth tip
    for x, ys in sorted(cols.items()):
        if x % 4 == 1 and len(ys) >= 5:
            yb = max(ys)
            for y in (yb - 2, yb - 1):
                if (x, y) in mask and fig.px[(x, y)][0] == lit:
                    fig.put(x, y, lit, 2)
    return mask


def leaf(fig, pts, keep=None):
    """A leaf from a list of (x, y, role): 'l' lit, 'b' body, 'd' dark, 'r' midrib."""
    tones = {'l': ('grass_warm', 4), 'b': ('grass', 3), 'd': ('leaf', 2), 'r': ('leaf', 3), 's': ('leaf', 2)}
    for (x, y, r) in pts:
        f, t = tones[r]
        fig.put(x, y, f, t)


def despeckle(fig, keep):
    """No speckle (house-style 4): a pixel unlike all four neighbours takes its most common
    neighbour, unless it is an eye, a glint or a gem (`keep`). Deterministic tie-break."""
    for _ in range(2):
        changes = {}
        for p in sorted(fig.px):
            v = fig.px[p]
            if p in keep or v[0] in ('ink', '_edge', '_lit') or p in fig.fixed:
                continue
            nb = [fig.px.get((p[0] + dx, p[1] + dy)) for dx, dy in N4]
            if any(n is None for n in nb):
                continue
            if all(n != v for n in nb):
                pool = [n for n in nb if n[0] not in ('ink', '_edge', '_lit')]
                if not pool:
                    continue
                changes[p] = max(sorted(set(pool), key=str), key=pool.count)
        for p, v in changes.items():
            fig.px[p] = v


def finish(fig, keep):
    fig.outline()
    despeckle(fig, keep)
    return fig


# --- faces -------------------------------------------------------------------------
def lens(fig, cx, cy, keep, side=0, shut=False, small=False):
    """A round reading-glasses lens: a brass ring lit at the upper left, a snow lens a tone
    down on the shaded side, and the pupil (ink 2 x 2, a one-pixel glint) looking a
    little toward the facing. `small` is the perch lens (4 x 4)."""
    if small:
        ring = [(0, -1), (1, -1), (-1, 0), (2, 0), (-1, 1), (2, 1), (0, 2), (1, 2)]
        glass = [(0, 0), (1, 0), (0, 1), (1, 1)]
    else:
        ring = [(-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), (2, 1),
                (-1, 2), (0, 2), (1, 2)]
        glass = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    for (dx, dy) in ring:
        t = 4 if (dx < 0 and dy <= 0) or dy == min(r[1] for r in ring) and dx <= 0 else 2 if (dx > 0 and dy > 0) else 3
        fig.put(cx + dx, cy + dy, 'brass', t)
    shade_lens = 3 if side <= 0 else 2
    for (dx, dy) in glass:
        t = 4 if (dx + dy) < (0 if not small else 1) and side <= 0 else shade_lens
        if shut:
            t = 2
        fig.put(cx + dx, cy + dy, 'snow', t)
    if shut:
        if small:
            fig.put(cx, cy + 1, 'ink', 0)
            fig.put(cx + 1, cy + 1, 'ink', 0)
            keep |= {(cx, cy + 1), (cx + 1, cy + 1)}
        else:
            for p in ((cx - 1, cy), (cx, cy + 1), (cx + 1, cy)):
                fig.put(p[0], p[1], 'ink', 0)
                keep.add(p)
        return
    if small:
        px = cx + (1 if side > 0 else 0)
        for p in ((px, cy), (px, cy + 1)):
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
        return
    ox = 0 if side >= 0 else -1
    pup = [(cx + ox, cy), (cx + ox + 1, cy), (cx + ox, cy + 1), (cx + ox + 1, cy + 1)]
    for p in pup:
        fig.put(p[0], p[1], 'ink', 0)
        keep.add(p)
    g = (cx + ox, cy)
    fig.put(g[0], g[1], 'snow', 5)
    keep.add(g)


def big_eye(fig, x, y, keep, w=4, h=5, shut=False):
    """A big ink eye, `w` x `h` with knocked corners, a 1 x 2 snow glint at the upper left
    (a two-pixel cluster, inset from the edge)."""
    if shut:
        for dx in range(w):
            p = (x + dx, y + h - 2 + (1 if 0 < dx < w - 1 else 0))
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
        return
    for dy in range(h):
        for dx in range(w):
            if dy in (0, h - 1) and dx in (0, w - 1):
                continue
            fig.put(x + dx, y + dy, 'ink', 0)
            keep.add((x + dx, y + dy))
    for p in ((x + 1, y + 1), (x + 1, y + 2)) if h >= 4 else ((x + 1, y),):
        fig.put(p[0], p[1], 'snow', 5)
        keep.add(p)


def squint(fig, x, y, keep, w=4, shut=False, brow_in=1):
    """The calm focused squint: a flat lid (slate tone 1) over a short ink eye with a glint
    at its upper left; a short brow slants down toward the nose (`brow_in` is +1 when the
    nose is to the east of this eye)."""
    for dx in range(w):
        fig.put(x + dx, y - 1, STONE + '_cool', 1)
    if shut:
        for dx in range(w):
            fig.put(x + dx, y, 'ink', 0)
            keep.add((x + dx, y))
        return
    for dx in range(w):
        fig.put(x + dx, y, 'ink', 0)
        keep.add((x + dx, y))
    for dx in range(1, w - 1):
        fig.put(x + dx, y + 1, 'ink', 0)
        keep.add((x + dx, y + 1))
    g = (x + 1, y)
    fig.put(g[0], g[1], 'snow', 5)
    keep.add(g)
    # brow: two pixels, the inner one a row lower (off by default: a calm squint)
    if brow_in == 0:
        return
    if brow_in > 0:
        bp = [(x + w - 2, y - 3), (x + w - 1, y - 2)]
    else:
        bp = [(x, y - 2), (x + 1, y - 3)]
    for p in bp:
        fig.put(p[0], p[1], STONE + '_cool', 1)


def mouth(fig, x, y, w=2):
    for dx in range(w):
        fig.put(x + dx, y, STONE + '_cool', 0)


# =====================================================================================
# Option A: the reading pebble
# =====================================================================================
def a_sprout(fig, x, y, lean=1, stem=2):
    """A stem from (x, y) up `stem` pixels and a single leaf leaning to the `lean` side."""
    fig.put(x, y, 'leaf', 2)
    if stem == 2:
        fig.put(x, y - 1, 'leaf', 3)
    y += 2 - stem
    if lean >= 0:
        leaf(fig, [(x + 1, y - 4, 'l'), (x + 2, y - 4, 'l'), (x, y - 3, 'l'), (x + 1, y - 3, 'b'), (x + 2, y - 3, 'b'),
                   (x + 3, y - 3, 'd'), (x, y - 2, 'b'), (x + 1, y - 2, 'r'), (x + 2, y - 2, 'd'), (x + 3, y - 2, 'd'),
                   (x + 4, y - 4, 'd')])
    else:
        leaf(fig, [(x - 2, y - 4, 'l'), (x - 1, y - 4, 'l'), (x - 3, y - 3, 'l'), (x - 2, y - 3, 'b'), (x - 1, y - 3, 'b'),
                   (x, y - 3, 'b'), (x - 3, y - 2, 'b'), (x - 2, y - 2, 'r'), (x - 1, y - 2, 'd'), (x, y - 2, 'd'),
                   (x - 4, y - 4, 'l')])


def a_feet(fig, xs, y=SOLE, w=3):
    for x0 in xs:
        m = fig.rect(x0, y - 1, x0 + w - 1, y)
        for (x, yy) in m:
            t = 3 if x == x0 else 2
            if yy == y:
                t = 1 if x > x0 else 2
            fig.put(x, yy, STONE + ('_cool' if t <= 2 else ''), t)


def option_a(view):
    perch = view in ('Ep', 'Wp')
    fig = sk.Fig(PW, PH) if perch else sk.Fig(W, H)
    keep = set()
    d = {'E': 1, 'W': -1, 'Ep': 1, 'Wp': -1}.get(view, 0)
    if perch:
        cx = PX
        body = blob(fig, cx, PSOLE - 4.5, 7.0, 5.5, 3.0)
        pebble(fig, body, top_plane=2)
        pits(fig, [(cx - 4 + (1 if d < 0 else 0), PSOLE - 2, True)])
        a_sprout(fig, cx - d, PSOLE - 11, lean=d, stem=1)
        ex = cx + 2 * d
        ey = PSOLE - 6
        lens(fig, cx + 3 * d, ey, keep, side=d)
        far = cx - 3 * d
        for dy in (-1, 0, 1):
            fig.put(far - d, ey + dy, 'brass', 3 if d > 0 else 4)
        for dy in (0, 1):
            fig.put(far, ey + dy, 'ink', 0)
            keep.add((far, ey + dy))
        for x in range(min(far, cx + 3 * d) + 2, max(far, cx + 3 * d) - 1):
            fig.put(x, ey - 1, 'brass', 3)
        return finish(fig, keep)
    if view == 'nap':
        body = blob(fig, AX, SOLE - 5.0, 11.0, 6.0, 2.6)
        pebble(fig, body, top_plane=2)
        pits(fig, [(7, SOLE - 3, True), (22, SOLE - 7, True), (12, SOLE - 9, True)])
        # leaf droops over the left side, stem from the top
        fig.put(AX - 2, SOLE - 11, 'leaf', 3)
        leaf(fig, [(AX - 3, SOLE - 12, 'l'), (AX - 4, SOLE - 12, 'l'), (AX - 5, SOLE - 11, 'l'), (AX - 4, SOLE - 11, 'b'),
                   (AX - 3, SOLE - 11, 'r'), (AX - 6, SOLE - 10, 'b'), (AX - 5, SOLE - 10, 'd'), (AX - 4, SOLE - 10, 'd')])
        # glasses slid low, eyes shut behind them
        lens(fig, AX - 4, SOLE - 5, keep, shut=True)
        lens(fig, AX + 3, SOLE - 5, keep, side=1, shut=True)
        fig.put(AX - 1, SOLE - 6, 'brass', 3)
        fig.put(AX, SOLE - 6, 'brass', 2)
        return finish(fig, keep)
    lift = 3 if view == 'hop' else 0
    rx, ry = (9.5, 8.5) if view != 'hop' else (9.0, 8.6)
    if d:
        rx -= 1.0
    base = SOLE - 2 - lift
    cy = base - ry + 1
    body = blob(fig, AX, cy, rx, ry, 3.0)
    if view == 'hop':
        a_feet(fig, (AX - 5, AX + 2), y=base + 2, w=3)
    elif d:
        a_feet(fig, (AX - 4, AX + 1), w=3)
    else:
        a_feet(fig, (AX - 6, AX + 3), w=3)
    pebble(fig, body, top_plane=2)
    top = min(p[1] for p in body)
    pits(fig, [(AX - 6, cy + 4, True), (AX + 5, cy - 4, False), (AX - 2, cy + 6, True)])
    a_sprout(fig, AX - (1 if d >= 0 else -1) * (1 if d else 0), top - 1, lean=(-1 if view == 'hop' else (d or 1)))
    ey = int(cy) - 1
    if d == 0:
        lens(fig, AX - 4, ey, keep)
        lens(fig, AX + 3, ey, keep, side=1)
        fig.put(AX - 1, ey - 1, 'brass', 3)
        fig.put(AX, ey - 1, 'brass', 3)
        fig.put(AX + 1, ey - 1, 'brass', 2)
        if view == 'hop':
            for p in ((AX - 1, ey + 4), (AX, ey + 4), (AX - 1, ey + 5), (AX, ey + 5)):
                fig.put(p[0], p[1], STONE + '_cool', 0)
        else:
            mouth(fig, AX - 1, ey + 4)
    else:
        near = AX + 3 * d
        lens(fig, near, ey, keep, side=d)
        # far lens: three pixels of rim and a pupil column at the far cheek
        fx = AX - 3 * d
        for dy in (-1, 0, 1):
            fig.put(fx - d, ey + dy, 'brass', 3 if d > 0 else 4)
            fig.put(fx, ey + dy, 'ink', 0)
            keep.add((fx, ey + dy))
        fig.put(fx + d, ey - 1, 'brass', 3)
        fig.put(near - 2 * d, ey - 1, 'brass', 3)
        fig.put(near - 3 * d, ey - 1, 'brass', 3)
        fig.put(near - 2 * d + (0), ey + 5, STONE + '_cool', 0)
        fig.put(near - 1 * d, ey + 5, STONE + '_cool', 0)
    return finish(fig, keep)


# =====================================================================================
# Option B: the lamp-stone stack
# =====================================================================================
def b_gem(fig, x, y, keep, lit=True):
    """The forehead facet, a 3 x 4 lamp-lit diamond (a light source: never outlined)."""
    pts = [(x, y, 5), (x, y + 1, 5), (x - 1, y + 1, 4), (x - 1, y + 2, 4), (x + 1, y + 1, 3), (x + 1, y + 2, 3),
           (x, y + 2, 2), (x, y + 3, 2)]
    for (px, py, t) in pts:
        fig.glow(px, py, 'lamp', t if lit else max(1, t - 2))
        keep.add((px, py))


def b_collar(fig, cx, y, half, d=0):
    """The grass tuft between the pebbles: a band two rows deep with blades hanging over
    the body pebble in 2 px points."""
    m = set()
    for x in range(cx - half, cx + half + 1):
        m.add((x, y))
        m.add((x, y + 1))
        if (x - cx + half) % 3 != 2 and abs(x - cx) < half:
            m.add((x, y + 2))
    blades(fig, m)
    return m


def option_b(view):
    perch = view in ('Ep', 'Wp')
    fig = sk.Fig(PW, PH) if perch else sk.Fig(W, H)
    keep = set()
    d = {'E': 1, 'W': -1, 'Ep': 1, 'Wp': -1}.get(view, 0)
    if perch:
        cx = PX
        low = blob(fig, cx, PSOLE - 2.5, 4.5, 3.0, 2.2)
        pebble(fig, low, glint=False)
        head = blob(fig, cx + d * 0.5, PSOLE - 9.5, 6.5, 5.5, 2.3)
        pebble(fig, head)
        b_collar(fig, cx, PSOLE - 5, 4)
        b_gem(fig, cx + 2 * d, PSOLE - 14, keep)
        ex = cx + 2 * d - (1 if d < 0 else 0)
        for p in ((ex - 1, PSOLE - 9), (ex, PSOLE - 9), (ex + 1, PSOLE - 9)):
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
        fig.put(ex, PSOLE - 8, 'ink', 0)
        keep.add((ex, PSOLE - 8))
        for x in (ex - 1, ex, ex + 1):
            fig.put(x, PSOLE - 10, STONE + '_cool', 1)
        far = cx - 3 * d
        fig.put(far, PSOLE - 9, 'ink', 0)
        fig.put(far - d, PSOLE - 9, 'ink', 0)
        keep |= {(far, PSOLE - 9), (far - d, PSOLE - 9)}
        return finish(fig, keep)
    if view == 'nap':
        # curled: the body pebble lies behind, the head pebble rolled down in front of it,
        # the collar tuft fanned up out of the join, the facet dimmed
        low = blob(fig, AX + 5, SOLE - 5.0, 6.5, 5.0, 2.2)
        pebble(fig, low, glint=False)
        pits(fig, [(AX + 7, SOLE - 3, True)])
        tuft = set()
        for (x, h) in ((AX + 3, 3), (AX + 4, 4), (AX + 5, 5), (AX + 6, 4), (AX + 7, 2)):
            for k in range(h):
                tuft.add((x, SOLE - 8 - k))
        head = blob(fig, AX - 3, SOLE - 5.5, 8.0, 6.0, 2.3)
        pebble(fig, head)
        blades(fig, tuft)
        pits(fig, [(AX - 8, SOLE - 3, True)])
        b_gem(fig, AX - 4, SOLE - 11, keep, lit=False)
        squint(fig, AX - 8, SOLE - 5, keep, w=3, shut=True)
        squint(fig, AX - 2, SOLE - 5, keep, w=3, shut=True)
        return finish(fig, keep)
    lift = 3 if view == 'hop' else 0
    base = SOLE - lift
    lrx = 6.0 if d else 7.0
    low = blob(fig, AX, base - 3.5, lrx, 4.5 if view != 'hop' else 4.0, 2.2)
    # nub feet
    if view != 'hop':
        for fx in ((AX - 4, AX + 2) if d == 0 else (AX - 3, AX + 1)):
            for (x, y) in ((fx, base), (fx + 1, base)):
                low.add((x, y))
    pebble(fig, low, glint=False)
    pits(fig, [(AX - 4, base - 3, True), (AX + 3, base - 2, True)])
    hrx, hry = (9.0, 7.5) if not d else (8.0, 7.5)
    hy = base - 13.5 - (1 if view == 'hop' else 0)
    head = blob(fig, AX + d * 0.5, hy, hrx, hry, 2.4)
    pebble(fig, head, cap=0.42)
    pits(fig, [(AX + 6 - (2 if d else 0), int(hy) - 3, False), (AX - 6, int(hy) + 4, True)])
    b_collar(fig, AX, base - 8, 6 if not d else 5)
    if view == 'hop':
        # arms out: two nub pebbles at the collar
        for sx in (-1, 1):
            nub = blob(fig, AX + sx * 8.0, base - 7.0, 2.0, 1.6, 2.0)
            pebble(fig, nub, glint=False)
    ey = int(hy) + 1
    if d == 0:
        b_gem(fig, AX - 1, int(hy) - 6, keep)
        squint(fig, AX - 6, ey, keep, w=4, brow_in=0)
        squint(fig, AX + 2, ey, keep, w=4, brow_in=0)
        if view == 'hop':
            for p in ((AX - 1, ey + 3), (AX, ey + 4), (AX + 1, ey + 3)):
                fig.put(p[0], p[1], STONE + '_cool', 0)
        else:
            mouth(fig, AX - 1, ey + 3, 2)
    else:
        b_gem(fig, AX + 2 * d - (1 if d < 0 else 0), int(hy) - 6, keep)
        nx = AX + 2 * d - (2 if d < 0 else 1)
        squint(fig, nx, ey, keep, w=4, brow_in=0)
        # far eye: a short slit at the far cheek
        fx = AX - 5 * d - (1 if d > 0 else 0)
        fig.put(fx, ey, 'ink', 0)
        fig.put(fx + 1, ey, 'ink', 0)
        fig.put(fx, ey - 1, STONE + '_cool', 1)
        fig.put(fx + 1, ey - 1, STONE + '_cool', 1)
        keep |= {(fx, ey), (fx + 1, ey)}
        mouth(fig, AX + 4 * d - (1 if d < 0 else 0), ey + 3, 2)
    return finish(fig, keep)


# =====================================================================================
# Option C: the bowl-cut block
# =====================================================================================
def c_fringe(fig, body, cut_y, tufts, d=0):
    """The bowl cut: the body's top above `cut_y`, its lower edge cut straight in 2 px
    steps (blade tips), and short tufts sticking up from the crown."""
    m = {p for p in body if p[1] < cut_y}
    xs = sorted({p[0] for p in m})
    for x in xs:
        if ((x - xs[0]) // 2) % 2 == 0 and (x, cut_y) in body:
            m.add((x, cut_y))
    # sides hang a row lower at the far ends (the bowl curves round the cheeks)
    for x in xs[:2] + xs[-2:]:
        for y in (cut_y, cut_y + 1, cut_y + 2):
            if (x, y) in body:
                m.add((x, y))
    for (tx, h) in tufts:
        top = min(p[1] for p in m if p[0] == tx) if any(p[0] == tx for p in m) else cut_y
        for k in range(1, h + 1):
            m.add((tx, top - k))
            if k < h:
                m.add((tx + 1, top - k))
    blades(fig, m)
    return m


def c_legs(fig, xs, y=SOLE, h=3):
    for x0 in xs:
        for yy in range(y - h + 1, y + 1):
            fig.put(x0, yy, STONE, 3 if yy < y else 2)
            fig.put(x0 + 1, yy, STONE + '_cool', 2 if yy < y else 1)


def c_arm(fig, x, y, d):
    """A nub arm, 2 x 3, lit on its west column."""
    for yy in (y, y + 1, y + 2):
        fig.put(x, yy, STONE + ('_warm' if d < 0 else ''), 4 if d < 0 else 3)
        fig.put(x + 1, yy, STONE + '_cool', 2)
    fig.put(x + 1, y + 2, STONE + '_cool', 1)


def option_c(view):
    perch = view in ('Ep', 'Wp')
    fig = sk.Fig(PW, PH) if perch else sk.Fig(W, H)
    keep = set()
    d = {'E': 1, 'W': -1, 'Ep': 1, 'Wp': -1}.get(view, 0)
    if perch:
        cx = PX
        body = blob(fig, cx, PSOLE - 6.0, 6.0, 6.0, 4.0)
        pebble(fig, body, cap=0.30, top_plane=0, glint=False)
        c_fringe(fig, body, PSOLE - 9, [(cx - 3, 2), (cx + 1, 3)])
        ex = cx + 1 if d > 0 else cx - 4
        big_eye(fig, ex, PSOLE - 7, keep, w=3, h=4)
        fx = cx - 4 * d - (0 if d > 0 else 1)
        for p in ((fx, PSOLE - 7), (fx, PSOLE - 6), (fx + (1 if d < 0 else -1) * 0, PSOLE - 5)):
            fig.put(p[0], p[1], 'ink', 0)
            keep.add(p)
        return finish(fig, keep)
    if view == 'nap':
        body = blob(fig, AX, SOLE - 5.0, 10.0, 6.0, 4.0)
        pebble(fig, body, cap=0.30, glint=False)
        # the fringe flops forward over the shut eyes
        c_fringe(fig, body, SOLE - 5, [(AX - 5, 2), (AX + 3, 2)])
        for x0 in (AX - 6, AX + 3):
            for p in ((x0, SOLE - 3), (x0 + 1, SOLE - 3), (x0 + 2, SOLE - 3)):
                fig.put(p[0], p[1], 'ink', 0)
                keep.add(p)
        # nub arm tucked in front
        c_arm(fig, AX - 1, SOLE - 3, -1)
        return finish(fig, keep)
    lift = 3 if view == 'hop' else 0
    base = SOLE - 3 - lift
    rx = 8.5 if not d else 7.5
    ry = 8.0 if view != 'hop' else 8.6
    cy = base - ry + 1
    body = blob(fig, AX, cy, rx, ry, 4.5)
    if view == 'hop':
        c_legs(fig, (AX - 4, AX + 2), y=base + 2, h=2)
    elif d:
        c_legs(fig, (AX - 3 + d, AX + 1 + d), y=SOLE, h=3)
    else:
        c_legs(fig, (AX - 4, AX + 2), y=SOLE, h=3)
    pebble(fig, body, cap=0.30, glint=False)
    pits(fig, [(AX - 6 + (1 if d else 0), base - 3, True), (AX + 4, base - 2, True)])
    cut = int(cy) - 3
    c_fringe(fig, body, cut, [(AX - 4, 2), (AX + (1 if d >= 0 else -2), 3)] if view != 'hop' else
             [(AX - 5, 3), (AX - 1, 4), (AX + 3, 3)])
    ey = cut + 2
    if view == 'hop':
        c_arm(fig, AX - int(rx) - 2, int(cy) - 1, -1)
        c_arm(fig, AX + int(rx) + 1, int(cy) - 1, 1)
    elif d == 0:
        c_arm(fig, AX - int(rx) - 2, int(cy) + 2, -1)
        c_arm(fig, AX + int(rx) - 0, int(cy) + 2, 1)
    else:
        c_arm(fig, AX - (1 if d < 0 else 1) - (0), int(cy) + 3, -d)
    if d == 0:
        big_eye(fig, AX - 5, ey, keep)
        big_eye(fig, AX + 1, ey, keep)
        if view == 'hop':
            for p in ((AX - 1, ey + 6), (AX, ey + 6), (AX - 1, ey + 7), (AX, ey + 7)):
                fig.put(p[0], p[1], STONE + '_cool', 0)
        else:
            mouth(fig, AX - 1, ey + 6, 2)
    else:
        ex = AX + 1 if d > 0 else AX - 5
        big_eye(fig, ex, ey, keep)
        fx = AX - 4 if d > 0 else AX + 3
        for dy in (1, 2, 3):
            fig.put(fx, ey + dy, 'ink', 0)
            keep.add((fx, ey + dy))
        mouth(fig, AX + 3 * d - (1 if d < 0 else 0), ey + 6, 2)
    return finish(fig, keep)


# --- the sheet -----------------------------------------------------------------------
VIEWS = (('S', 'S idle'), ('E', 'E idle'), ('W', 'W idle'), ('hop', 'S hop'), ('nap', 'S nap'),
         ('Ep', 'E perch'), ('Wp', 'W perch'))

OPTIONS = [
    dict(
        label='A', name='Reading pebble: one rounded cube, round brass reading glasses, a single leaf',
        question='Focus as the bookworm: today\'s round reading glasses kept, over big eyes, on one rounded slate cube.',
        fn=option_a, palette=['slate', 'snow', 'brass', 'grass', 'leaf'],
        pose='Squares up a step behind its folk, glasses straight, leaf upright: a small scholar paying close attention.',
        parts=[
            'feet x2 (slate stubs): layer 0; foot; 6-frame shuffle, tucked under the body in hop, hidden in nap',
            'body (slate rounded cube, lit top plane, pits): layer 1; foot; breath 1 px squash, stretch on hop, flattens to a loaf in nap',
            'glasses (brass rims, snow lenses, ink pupils): layer 2; head (body face); near lens and a far rim in E/W, slide low in nap, flash in IN THE ZONE',
            'leaf (grass on a leaf stem): layer 3; head top; sways a frame late in walk, flicks back in hop, droops in nap; growth stage swaps it',
            'perch: a 16 px redraw (lower cube, the near lens full size, the far pupil and rim, a one-pixel stem): rides the shoulder in fight E/W',
        ],
        notes=[
            'Works: the glasses are the one face read at 2 px (two pale rings), they carry today\'s identity, and nobody else wears them.',
            'Risk: the lenses are light on the face, so in E view the near lens sits on the dark side; it drops a tone there to keep W-E positive.',
            'Compared with Eastward 05: Sam\'s small head at about this height (big pale mass, 3-4 tones, 1-2 px dark eyes), here a round cube.',
        ]),
    dict(
        label='B', name='Lamp-stone stack: head pebble on a body pebble, grass collar, lamp facet, focused squint',
        question='Focus as calm concentration: a forehead facet lit like today\'s reading lamp and a level squint.',
        fn=option_b, palette=['slate', 'grass', 'leaf', 'snow'], glow=['lamp'],
        pose='Sits low and steady, eyes narrowed in a calm squint, the forehead lamp lit: the folk\'s quiet study buddy.',
        parts=[
            'body pebble (slate, nub feet): layer 0; foot; waddles side to side in the 6-frame walk, stays put in hop (lifts with the head)',
            'grass collar (grass, leaf tips): layer 1; chest (the join); blades bob a frame after each step, fan out in nap',
            'head pebble (slate, big): layer 2; chest; bobs 1 px on the step, tucks beside the body in nap',
            'arms (slate nubs): layer 3; chest; hidden at idle, pop out in hop, cheer and cast',
            'lamp facet (lamp glow) and squint (ink under a flat slate lid, no brow): layer 4; head; the facet dims in nap and flares in IN THE ZONE',
            'perch: a 16 px redraw (head pebble on a stub, the collar, the facet and the near squint)',
        ],
        notes=[
            'Works: a snowman stack of two round stones with a glowing diamond is a silhouette no folk has; the squint says focus.',
            'Risk: stacked stones point at Cairn, so it is kept round, blue-grey and grass-collared, never moss; the squint is small at 2 px.',
            'Compared with Eastward 05: the stacked heads of the townsfolk (head as wide as the body) and its lamp glows as light, not paint.',
        ]),
    dict(
        label='C', name='Bowl-cut block: soft slate box, grass fringe cut straight above big eyes, tiny legs',
        question='Focus as the earnest student: big eyes under a neat bowl cut of grass, a squarer soft cube on two little legs.',
        fn=option_c, palette=['slate', 'grass', 'leaf', 'snow'],
        pose='Bright-eyed and upright on two tiny legs, nub arms at its sides, fringe neat: ready for the lesson.',
        parts=[
            'legs x2 (slate, 2 x 3): layer 0; hip; the 6-frame walk swings them, tucked to 2 px in hop',
            'body (slate soft box, pits): layer 1; hip; breath 1 px, stretch on hop, loaf in nap',
            'arms x2 (slate nubs): far behind (layer 0), near in front (layer 3); chest; swing in walk, up in hop and cheer',
            'fringe (grass bowl cut, leaf shade, crown tufts): layer 2; head top; bounces a frame late, flops over the eyes in nap; growth adds tufts',
            'eyes (ink, snow glints): layer 3; head',
            'perch: a 16 px redraw (box, fringe with two tufts, one big eye and the far eye)',
        ],
        notes=[
            'Works: the flat bowl cut over a box is the cutest read at 2 px, and big eyes survive at any size.',
            'Risk: green on top is closest to the Mossling and to Cairn\'s moss; the fringe stays short and cut straight so it reads as hair.',
            'Compared with Eastward 05: the curly woman\'s hair mass (lit band at the parting, darker tips), here as combed grass strands.',
        ]),
]


def height(im):
    a = im.getchannel('A')
    ys = [y for y in range(im.height) if any(a.getpixel((x, y)) for x in range(im.width))]
    return ys[-1] - ys[0] + 1 if ys else 0


# =====================================================================================
# FINAL (revision round, 21 Oct): option A, the reading pebble, with grafts.
#   - the stone modelled as a rounded cube: a lit top plane (tone 4), a lit west face,
#     the south face, a shaded east face (tone 2), a contact-dark underside, a two-pixel
#     glint at the upper-left corner and mineral speckle as 2 px sibling clusters.
#   - shared familiar marks: one head-top leaf (the growth anchor), eyes 3 x 3 ink with a
#     2 px glint (behind the lenses, from C), a pale muzzle, the same foot line.
#   - from B: nub arms, hidden at idle, out for hop, react, cling, cheer and special.
#   - from B: the lamp facet on the forehead, lit only in the special (IN THE ZONE).
#   - profiles as forms: the face plane is its own face of the cube, the glasses sit
#     proud of it (a far rim edge-on), a temple arm runs back, a brow line and a cheek.
#   - the perch is a 16 px redraw that turns toward the foe in E and in W.
# =====================================================================================
FS = 'slate'


def fcube(fig, x0, y0, x1, y1, d=0, top_rows=4, knock=3, fw=6, east=2):
    """The rounded cube. d=0 faces S (south face in front); d=+1/-1 turns the face plane
    to the east/west end, `fw` px wide. Light from the upper left in every facing."""
    m = fig.rect(x0, y0, x1, y1, knock=knock)
    m = {p for p in m if (p[0], p[1] - 1) in m or (p[0], p[1] + 1) in m}
    top, bot, xl, xr = {}, {}, {}, {}
    for (x, y) in m:
        top[x] = min(top.get(x, 99), y)
        bot[x] = max(bot.get(x, -1), y)
        xl[y] = min(xl.get(y, 99), x)
        xr[y] = max(xr.get(y, -1), x)
    for (x, y) in m:
        r = y - y0
        if r < top_rows:
            f, t = FS + '_warm', 4
            if xr[y] - x < 2 or (r == top_rows - 1 and xr[y] - x < 4):
                f, t = FS + '_warm', 3          # the top plane rolls off at the east corner
        else:
            f, t = FS + '_warm', 3              # the south face
            if x - xl[y] < 2:
                f, t = FS, 4                    # the lit west face
            if xr[y] - x < east:
                f, t = FS, 2                    # the shaded east face
                if east > 2 and xr[y] == x:
                    f, t = FS + '_cool', 1      # its far edge turns under
            if d > 0 and x > xr[y] - fw:
                f, t = (FS, 2)                  # E: the face plane is the east face
            if d < 0 and x < xl[y] + fw:
                f, t = (FS, 4) if x - xl[y] < fw - 1 else (FS + '_warm', 4)   # W: the face plane is lit
            if y == bot[x] - 1 and xr[y] - x < 5:
                f, t = FS, 2
        if y == bot[x]:
            f, t = FS + '_cool', 1              # contact-dark underside
        fig.put(x, y, f, t)
    # two-pixel glint at the upper-left corner of the top plane
    tl = sorted((p for p in m if p[1] - top[p[0]] == 1), key=lambda p: p[0])
    if len(tl) > 2:
        for p in tl[1:3]:
            fig.put(p[0], p[1], FS + '_warm', 5)
    return m, dict(x0=x0, y0=y0, x1=x1, y1=y1, top=y0 + top_rows)


def minerals(fig, pts):
    """Mineral speckle: 2 px clusters a sibling tone off the plane they sit on."""
    for (x, y, horiz) in pts:
        q = (x + 1, y) if horiz else (x, y + 1)
        a, b = fig.px.get((x, y)), fig.px.get(q)
        if not a or a != b or a[0] in ('ink', '_edge', '_lit'):
            continue
        fam, t = a
        if t == 4:
            nv = (FS + '_cool', 3)
        elif t == 3:
            nv = (FS + '_cool', 2)
        else:
            continue
        fig.put(x, y, *nv)
        fig.put(q[0], q[1], *nv)


RING = [(-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2)]
EYES = {
    'open': ['XXX', 'XXX', 'XXX'],
    'happy': ['...', 'XXX', 'X.X'],
    'shut': ['...', 'X.X', 'XXX'],
    'squeezeL': ['...', 'XXX', '...'],
    'squeezeR': ['...', 'XXX', '...'],
}


def flens(fig, cx, cy, keep, eye='open', flash=False, glass=4):
    """A 5 x 5 round brass lens over a 3 x 3 ink eye with a 2 px snow glint; where the eye
    is shut the snow glass shows (lit at its upper left)."""
    for (dx, dy) in RING:
        t = 4 if (dx < 0 and dy <= 0) or (dy == -2 and dx <= 0) else 2 if (dx > 0 and dy > 0) or (dx == 2 and dy == 1) else 3
        fig.put(cx + dx, cy + dy, 'brass', t)
    if flash:
        fig.put(cx - 1, cy - 2, 'brass', 5)
        fig.put(cx, cy - 2, 'brass', 5)
    pat = EYES[eye]
    for j in range(3):
        for i in range(3):
            p = (cx - 1 + i, cy - 1 + j)
            if pat[j][i] == 'X':
                fig.put(p[0], p[1], 'ink', 0)
            else:
                fig.put(p[0], p[1], 'snow', glass)
            keep.add(p)
    if eye == 'open':
        for p in ((cx - 1, cy - 1), (cx - 1, cy)):
            fig.put(p[0], p[1], 'snow', 5)


def fglasses(fig, geo, d, keep, eye='open', flash=False):
    """Glasses and face: S has two lenses and a bridge; E/W one lens on the face plane,
    the far rim edge-on beyond the face (the face step), a temple arm back to the side,
    a brow line over the lens and a lit cheek under it. Returns the lens centres."""
    x0, x1, cy = geo['x0'], geo['x1'], geo['top'] + 2
    if d == 0:
        mid = (x0 + x1) / 2
        lx, rx = int(mid - 3.5 + 0.5), int(mid + 3.5 + 0.5)
        eL = eye if not eye.startswith('squeeze') else 'squeezeL'
        eR = eye if not eye.startswith('squeeze') else 'squeezeR'
        flens(fig, lx, cy, keep, eL, flash)
        flens(fig, rx, cy, keep, eR, flash)
        for x in range(lx + 3, rx - 2):
            fig.put(x, cy - 1, 'brass', 3)
        return [lx, rx], cy
    if d > 0:
        cx = x1 - 2
        e = 'squeezeR' if eye.startswith('squeeze') else eye
    else:
        cx = x0 + 2
        e = 'squeezeL' if eye.startswith('squeeze') else eye
    # brow: a dark line under the top plane's lip, over the lens
    for x in (cx - 1, cx, cx + 1):
        if fig.px.get((x, cy - 3)) and fig.px[(x, cy - 3)][0] not in ('ink',):
            fig.put(x, cy - 3, *((FS + '_cool', 1) if d > 0 else (FS, 2)))
    flens(fig, cx, cy, keep, e, flash, glass=(2 if e.startswith('squeeze') else 3) if d > 0 else 4)
    # the far lens edge-on, proud of the face plane
    fx = cx + 3 * d
    for dy in (-1, 0, 1):
        fig.put(fx, cy + dy, 'brass', 3 if d < 0 else 2)
    # temple arm back to the side of the head
    for k in range(3, 7):
        fig.put(cx - k * d, cy - 1, 'brass', 3 if d > 0 else 2)
    # cheek: a lit cluster under the back of the lens
    for x in (cx - 2 * d, cx - 3 * d):
        fig.put(x, cy + 3, FS + '_warm', 4 if d > 0 else 3)
    return [cx], cy


def fmuzzle(fig, cx, cy, rx, ry, mouth='line', d=0):
    """The pale muzzle (the family's pale face): snow, lit at its upper left, a cool lower
    right; the mouth in deep slate."""
    m = blob(fig, cx, cy, rx, ry, 2.0)
    m = {p for p in m if fig.px.get(p) and fig.px[p][0].startswith(FS)}
    xs = [p[0] for p in m] or [0]
    ys = [p[1] for p in m] or [0]
    for (x, y) in m:
        u = (x - min(xs)) / max(1, max(xs) - min(xs))
        v = (y - min(ys)) / max(1, max(ys) - min(ys))
        t = 2 if u + v < 0.9 else 1
        if d < 0:
            t += 1
        fig.put(x, y, 'snow', t)
    mx, my = int(cx), int(round(cy))
    if mouth == 'line':
        fig.put(mx - 1 + (1 if d > 0 else 0), my, FS + '_cool', 0)
        fig.put(mx + (1 if d > 0 else 0), my, FS + '_cool', 0)
    elif mouth == 'open':
        for p in ((mx - 1, my), (mx, my), (mx - 1, my + 1), (mx, my + 1)):
            fig.put(p[0], p[1], FS + '_cool', 0)
    return m


def ffeet(fig, xs, y=SOLE):
    for x0 in xs:
        for x in (x0, x0 + 1, x0 + 2):
            fig.put(x, y - 1, FS, 3 if x == x0 else 2)
            fig.put(x, y, FS + '_cool', 2 if x == x0 else 1)


def farm(fig, x, y):
    """A nub arm, a 3 x 2 pill: a lit top row, a shaded underside row."""
    for dx in range(3):
        fig.put(x + dx, y, FS + '_warm', 4)
        fig.put(x + dx, y + 1, FS, 2)


def solid_leaf(fig, pts):
    """A leaf as one solid cluster (no holes): the top pixel of each column lit warm, the
    bottom pixel of each column and the east column in leaf shade, the rest grass."""
    pts = set(pts)
    cols = {}
    for (x, y) in pts:
        cols.setdefault(x, []).append(y)
    xe = max(cols)
    for (x, y) in pts:
        f, t = 'grass', 3
        if y == min(cols[x]):
            f, t = 'grass_warm', 4
        if y == max(cols[x]) and len(cols[x]) > 1:
            f, t = 'leaf', 2
        if x == xe and y != min(cols[x]):
            f, t = 'leaf', 2
        fig.put(x, y, f, t)


def fleaf(fig, x, y, mode='right', stem=2):
    """The head-top growth (the family mark): a stem from the crown at (x, y) and one
    leaf. Modes: right, left (lean), up (cheer, hop), swept_e/swept_w (blown back in
    cling), droop (nap)."""
    fig.put(x, y, 'leaf', 2)
    if stem == 2:
        fig.put(x, y - 1, 'leaf', 3)
    b = y - stem
    if mode in ('right', 'left'):
        s = 1 if mode == 'right' else -1
        solid_leaf(fig, [(x, b), (x + s, b - 1), (x + 2 * s, b - 1), (x + 3 * s, b - 1),
                         (x + 2 * s, b - 2), (x + 3 * s, b - 2), (x + 4 * s, b - 2), (x + 4 * s, b - 3)])
    elif mode == 'up':
        solid_leaf(fig, [(x, b), (x - 1, b - 1), (x, b - 1), (x + 1, b - 1), (x - 1, b - 2), (x, b - 2),
                         (x + 1, b - 2), (x, b - 3), (x + 1, b - 3)])
    elif mode in ('swept_e', 'swept_w'):
        s = 1 if mode == 'swept_e' else -1
        solid_leaf(fig, [(x + s, b + 1), (x + 2 * s, b + 1), (x + 3 * s, b + 1), (x + s, b), (x + 2 * s, b),
                         (x + 3 * s, b), (x + 4 * s, b + 1)])
    if mode in ('right', 'left', 'up'):
        fig.put(x, b, 'leaf', 2)        # the leaf's base joins the stem in one cluster
    if mode == 'droop':
        solid_leaf(fig, [(x - 1, b + 1), (x - 2, b + 1), (x - 1, b + 2), (x - 2, b + 2), (x - 3, b + 2),
                         (x - 3, b + 3), (x - 4, b + 3)])


def fbody(fig, box, d, keep, eye='open', mouth='line', top_rows=4, minerals_at=(), flash=False, fw=6, east=2):
    x0, y0, x1, y1 = box
    m, geo = fcube(fig, x0, y0, x1, y1, d, top_rows=top_rows, fw=fw, east=east)
    minerals(fig, minerals_at)
    xs, cy = fglasses(fig, geo, d, keep, eye, flash)
    my0 = cy + 3
    if d == 0:
        mcx = (x0 + x1 + 1) / 2
        fmuzzle(fig, mcx, (my0 + y1 - 1) / 2 + 0.5, 3.2, max(1.2, (y1 - 1 - my0) / 2), mouth)
    else:
        mcx = xs[0] + 0.5 + (0.5 if d > 0 else -0.5)
        fmuzzle(fig, mcx, (my0 + y1 - 1) / 2 + 0.5, 2.4, max(1.2, (y1 - 1 - my0) / 2), mouth, d)
    return geo


def f_world(view):
    """S/E/W idle, the 4-frame hop (S), react (S) and nap (S), in the 32 x 32 cell."""
    fig = sk.Fig(W, H)
    keep = set()
    d = {'E': 1, 'W': -1}.get(view, 0)
    if view == 'nap':
        x0, y0, x1, y1 = 4, 16, 27, SOLE
        fcube(fig, x0, y0, x1, y1, 0, top_rows=3)
        minerals(fig, [(8, 23, True), (22, 22, True), (18, 17, True)])
        # glasses pushed up onto the top plane, seen from above: two flat rims and a bridge
        for gx in (10, 17):
            for (dx, dy) in ((0, 0), (1, 0), (2, 0), (3, 0), (-1, 1), (4, 1), (0, 2), (1, 2), (2, 2), (3, 2)):
                fig.put(gx + dx, 15 + dy, 'brass', 4 if dy == 0 and dx < 2 else 2 if dy == 2 and dx > 1 else 3)
            for dx in (0, 1, 2, 3):
                fig.put(gx + dx, 16, 'snow', 4 if dx < 2 else 3)
        fig.put(15, 16, 'brass', 3)
        fig.put(16, 16, 'brass', 3)
        # shut eyes on the face, the pale muzzle under them
        for ex in (9, 20):
            for p in ((ex, 20), (ex + 2, 20), (ex, 21), (ex + 1, 21), (ex + 2, 21)):
                pass
            for p in ((ex, 20), (ex + 1, 21), (ex + 2, 20), (ex, 21), (ex + 2, 21)):
                fig.put(p[0], p[1], 'ink', 0)
                keep.add(p)
        fmuzzle(fig, 16, 23.5, 4.0, 1.5, 'line')
        fleaf(fig, 23, 15, 'droop', stem=1)
        return finish(fig, keep)
    lift = 0
    if view in ('S', 'E', 'W'):
        box = (7, 10, 24, 25) if d == 0 else (8, 10, 23, 25)
        feet = (9, 20) if d == 0 else ((10, 17) if d > 0 else (12, 19))
    elif view == 'hop1':       # crouch: squash, feet planted
        box, feet = (6, 13, 25, 25), (8, 21)
    elif view == 'hop2':       # rise: stretch, feet still on the line
        box, feet = (8, 8, 23, 24), (10, 19)
    elif view == 'hop3':       # airborne: lifted, feet tucked, arms out
        box, feet = (7, 8, 24, 22), (9, 20)
        lift = 3
    elif view == 'hop4':       # land: squash, arms out for balance
        box, feet = (6, 12, 25, 25), (8, 21)
    elif view == 'react':      # the happy frame: up, arms up, eyes closed happy, mouth open
        box, feet = (7, 8, 24, 22), (9, 20)
        lift = 3
    x0, y0, x1, y1 = box
    cx = (x0 + x1 + 1) // 2
    ffeet(fig, feet, y=SOLE - lift if lift else SOLE)
    if view == 'hop2':
        for fx in feet:          # the stretched step: feet a row longer
            fig.put(fx, SOLE - 2, FS, 3)
            fig.put(fx + 1, SOLE - 2, FS, 2)
    arms = view in ('hop3', 'hop4', 'react')
    if arms:
        ay = y0 + 4 if view != 'react' else y0 - 1
        farm(fig, x0 - 2, ay)
        farm(fig, x1, ay)
    top_rows = 4 if (y1 - y0) >= 14 else 3
    eye = 'happy' if view == 'react' else 'open'
    mouth = 'open' if view in ('react', 'hop3') else 'line'
    mins = [(x0 + 4, y1 - 2, True), (x1 - 5, y0 + top_rows + 7, False), (x0 + 6, y0 + 1, True)]
    fbody(fig, box, d, keep, eye=eye, mouth=mouth, top_rows=top_rows, minerals_at=mins, fw=7)
    mode = 'right' if d == 0 else ('left' if d > 0 else 'right')
    if view in ('hop2', 'hop3', 'react'):
        mode = 'up'
    lx = cx if d == 0 else cx - d
    fleaf(fig, lx, y0 - 1, mode, stem=1)
    return finish(fig, keep)


def f_perch(view):
    """The 16 px perch redraw in the 24 x 24 cell, foot (12, 22), facing the foe."""
    d = 1 if view.startswith('E') else -1
    state = view[1:]
    fig = sk.Fig(PW, PH)
    keep = set()
    eye, mouth, flash, leafm = 'open', 'line', False, ('left' if d > 0 else 'right')
    box = (6, 12, 17, PSOLE)
    if state == 'cling':
        box = (5, 13, 18, PSOLE)
        eye, leafm = 'squeeze', ('swept_w' if d > 0 else 'swept_e')
    elif state == 'cheer':
        eye, mouth = 'happy', 'open'
    elif state == 'special':
        flash = True
    x0, y0, x1, y1 = box
    cx = (x0 + x1 + 1) // 2
    if state == 'cling':        # arms gripping the shoulder, low at both sides
        farm(fig, x0 - 2, y1 - 1)
        farm(fig, x1, y1 - 1)
    tr = 2 if state == 'cling' else 4 if state == 'special' else 3
    mins = [(x0 + 3, y1 - 2, True), (x0 + 4, y0, True)]
    fbody(fig, box, d, keep, eye=eye, mouth=mouth, top_rows=tr, minerals_at=mins, flash=flash, fw=5,
          east=(4 if state in ('cheer', 'special') else 3) if d < 0 else 2)
    if state == 'cheer':        # arms up over the top corners
        farm(fig, x0 - 2, y0 - 2)
        farm(fig, x1, y0 - 2)
    if state == 'special':      # one arm out toward the foe, the lamp facet lit on the brow
        farm(fig, x1 + 1 if d > 0 else x0 - 3, y0 + 5)
        b_gem(fig, x1 - 5 if d > 0 else x0 + 5, y0, keep)
    lx = cx - d
    fleaf(fig, lx, y0 - 1, leafm, stem=1)
    return finish(fig, keep)


FINAL_VIEWS = (
    ('S idle', lambda: f_world('S')), ('E idle', lambda: f_world('E')), ('W idle', lambda: f_world('W')),
    ('hop 1', lambda: f_world('hop1')), ('hop 2', lambda: f_world('hop2')), ('hop 3', lambda: f_world('hop3')),
    ('hop 4', lambda: f_world('hop4')), ('S react', lambda: f_world('react')), ('S nap', lambda: f_world('nap')),
    ('E perch', lambda: f_perch('Eperch')), ('E cling', lambda: f_perch('Ecling')),
    ('E cheer', lambda: f_perch('Echeer')), ('E special', lambda: f_perch('Especial')),
    ('W perch', lambda: f_perch('Wperch')), ('W cling', lambda: f_perch('Wcling')),
    ('W cheer', lambda: f_perch('Wcheer')), ('W special', lambda: f_perch('Wspecial')),
)

FINAL = dict(
    label='A final', chosen='A',
    name='Reading pebble (final): a rounded slate cube, round brass glasses over big eyes, one leaf, nub arms',
    grafts=[
        'From B: nub arms, hidden at idle, out for hop 3 and 4, react, cling, cheer and special, so the perched cheer and the special have a real action pose.',
        'From B: the lamp facet on the forehead, lit only in the special (IN THE ZONE) with a brass flash on the rims; a light source, never painted.',
        'From C: bigger eyes behind the lenses: 3 x 3 ink with a 2 px snow glint (the shared familiar eye).',
    ],
    palette=['slate', 'snow', 'brass', 'grass', 'leaf'], glow=['lamp'],
    pose='A small scholar a step behind its folk: square on its stub feet, glasses straight, leaf up, paying close attention.',
    parts=[
        'body (slate rounded cube: lit top plane, lit west face, shaded east face, contact-dark underside, mineral clusters): layer 1; anchor foot; changes in S/E/W (E/W turn the face plane to that end); squash in hop 1/4, stretch in hop 2, loaf in nap',
        'feet x2 (slate stubs, the shared foot line): layer 0; anchor foot; S/E/W (staggered in profile); a row longer in hop 2, tucked in hop 3 and react, hidden in nap and on the perch',
        'face block (snow muzzle, 3 x 3 ink eyes with a 2 px glint): layer 2; anchor head (body face plane); S/E/W; eye states open, happy, shut, squeeze',
        'glasses (species part: brass rims, snow glass, bridge; in E/W one lens, the far rim edge-on and a temple arm): layer 3; anchor head; S/E/W; pushed up onto the top plane in nap, rims flash in special',
        'head-top growth (one grass leaf on a leaf stem): layer 3; anchor head top (growthAnchor); leans back in E/W, up in hop 2/3, react, cheer, special; swept back in cling; droops in nap',
        'arms x2 (slate nubs, from B): layer 4 near, 0 far; anchor chest (body sides); hidden at idle; out in hop 3/4, up in react and cheer, gripping in cling, one forward in special',
        'lamp facet (species part, lamp glow, from B): layer 5; anchor head (the top plane, over the face); special only',
    ],
    growth_anchor=dict(S=[16, 9], E=[15, 9], W=[17, 9], perch_E=[11, 11], perch_W=[13, 11],
                       note='the stem pixel on the crown, one row above the top plane; stages swap the leaf there'),
    perch_anchor=dict(cell=[PW, PH], foot=[PX, PY],
                      note='the body\'s underside row 21 sits on the folk\'s perch anchor, on the shoulder away from the foe; the arms grip there in cling'),
    notes=[
        'Stone: modelled as a rounded cube (top plane tone 4 with a 2 px glint at the upper-left corner, west face 4, south face 3, east face 2, underside 1) with mineral speckle as 2 px clusters of the cool sibling.',
        'Profiles: in E/W the face plane is the end of the cube, the lens sits on it, the far rim stands proud of it edge-on (the face step), a temple arm runs back, with a brow line above and a lit cheek below.',
        'Perch: a 16 px redraw (one lens, the far rim, a one-pixel stem) that turns to face the foe in E and in W; cling squashes and grips, cheer stretches with arms up, special lights the facet.',
        'Growth stages (rig variants of the same poses): stage 1 one leaf; stage 2 a second smaller leaf opposite on the same stem; stage 3 a closed bud at the stem top (the reading lamp of today\'s sprite).',
        'Compared with Eastward 05: Sam and the townsfolk at about this height (a big pale head mass in 3 to 4 tones, 1 to 2 px dark eyes, a lit top and a dark contact row) and Eastward 05\'s lamp glow as light, not paint.',
    ],
)


def build_final():
    views, nums, ok = [], {}, True
    for cap, fn in FINAL_VIEWS:
        im = fn().image()
        views.append((cap, im))
        im.save(os.path.join(SCRATCH, 'final-' + cap.replace(' ', '-') + '.png'))
        m = sk.measure(im)
        g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.04,
                 colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
        ok &= all(g.values())
        print(f"final {cap:10s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
              f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
              f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
        nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
        nums[cap]['height_px'] = height(im)
    entry = dict(label=FINAL['label'], name=FINAL['name'], views=views, parts=FINAL['parts'],
                 palette=FINAL['palette'], pose=FINAL['pose'], notes=FINAL['notes'])
    sk.design_sheet('The Pebbling final (FOCUS Grassling): A, the reading pebble, with grafts', [entry], OUT_FINAL,
                    note='Familiar about 24 art px, cell 32 x 32, foot (16, 28). World: S/E/W idle, the 4-frame hop, '
                         'react, nap. Perch 16 px in 24 x 24, foot (12, 22): perch, cling, cheer, special, E and W.')
    return dict(chosen=FINAL['chosen'], name=FINAL['name'], grafts=FINAL['grafts'], parts=FINAL['parts'],
                palette=FINAL['palette'], glow=FINAL['glow'], pose=FINAL['pose'],
                growthAnchor=FINAL['growth_anchor'], perchAnchor=FINAL['perch_anchor'], measure=nums,
                notes=FINAL['notes'], _ok=ok)



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
            g = dict(on_house=m['on_house'] >= 1.0, west_east=m['west_east'] > 0, lone=m['isolated'] <= 0.06,
                     colours=m['colours'] <= 64, outline_dark=m.get('outline_dark', 0) >= 0.95)
            ok &= all(g.values())
            print(f"{o['label']} {cap:8s} h {height(im):2d}  on house {100*m['on_house']:5.1f}%  W-E {m['west_east']:+5.1f}  "
                  f"lone {100*m['isolated']:4.1f}%  colours {m['colours']:2d}  outline dark {100*m.get('outline_dark', 0):5.1f}%"
                  f"  {'ok' if all(g.values()) else 'MISS ' + ','.join(k for k, b in g.items() if not b)}")
            nums[cap] = {k: (round(v2, 4) if isinstance(v2, float) else v2) for k, v2 in m.items()}
            nums[cap]['height_px'] = height(im)
        out.append(dict(label=o['label'], name=o['name'], question=o['question'], parts=o['parts'],
                        palette=o['palette'], glow=o.get('glow', []), pose=o['pose'], notes=o['notes'], measure=nums))
    sk.design_sheet('The Pebbling (FOCUS Grassling, CUBE): a cube-ish pebble with focus', OPTIONS, OUT_PNG,
                    note='Familiar, about 24 art px, cell 32 x 32, foot (16, 28); perch 16 px in 24 x 24, foot (12, 22). '
                         'Views: S, E, W idle, S hop, S nap, E and W perch.')
    final = build_final()
    ok &= final.pop('_ok')
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w') as f:
        json.dump(dict(id='pebbling', species='CUBE', family='FOCUS', height_art_px=24, cell=[W, H], foot=[AX, AY],
                       perch=dict(height_art_px=16, cell=[PW, PH], foot=[PX, PY]),
                       question='A cube-ish pebble creature with focus: stone family with grass accents, small, '
                                'round-cornered, light grey-blue, big eyes or a focused squint.',
                       options=out, final=final), f, indent=2)
    print('gates', 'ok' if ok else 'MISS')


if __name__ == '__main__':
    main()
