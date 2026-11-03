"""Fence cells for the kit: wattle hurdles and a whitewashed picket that close into loops
(docs/vision/placement-logic.md, "Fences, walls and hedges"; Matt, 2 Nov: "what is the point of
fences if they don't enclose anything?").

    python3 -m scripts.art.kit.fences            # pictures and pieces (pieces kept unless --force)
    python3 -m scripts.art.kit.fences --check    # exit 1 if a committed picture is not what this draws

**The cell model.** A fence is laid one soft-grid cell at a time. Every cell has a node: the middle
of the cell's south line (the piece's foot, on the grid: x on a half cell, y on a cell line). A run
leaves the node by up to four arms, each half a cell long: west and east along the cell's south
line, north and south along the cell's middle. Two cells join when their arms meet (an east arm
meets the next cell's west arm), so a loop is a ring of cells whose every arm is met; a gate is
three cells wide with a post near each end. The pieces are named by the arms they have, in n e s w
order: `fence_wattle_ew` (a straight run along x), `fence_wattle_ns` (along y), `fence_wattle_es`
(a corner), `fence_wattle_esw` (a T), `fence_wattle_e` (an end post), `fence_wattle_gate_ew`.

**How the pictures tile.** Each piece is drawn inside its neighbourhood (the runs continuing from
every arm), from boxes in the house's three-quarter view (a voxel at ground (x, y), height z lands
at (x, y - z)), back to front, and only the pixels its own boxes win are kept. The outline is drawn
on the whole neighbourhood, so where two pieces meet there is no seam: placed side by side the
pieces give back the picture of the whole run, and the zone's y-sort by the foot puts each cell in
front of the one north of it, as the boxes were drawn.

**The styles** (placement-logic: "wattle hurdles (sheep) ... low mesh or wattle with a coop
(chickens) ... wattle, picket ... (kitchen gardens) ... low picket (front gardens)"):
- wattle: hazel rods woven between stakes a half cell apart (in front of one stake, behind the
  next, the next course the other way), a twisted binding rod along the top, the stakes' cut tops
  standing proud and a thicker post at corners, ends and Ts; a hurdle gate on two gate posts;
- picket: pointed palings a third of a cell apart nailed to two rails, whitewashed, posts at the
  corners, ends, Ts and gates (and a straight variant with a post); a ledged and braced gate.

Heights (art px at density 3, A = 74): wattle 42 to the binding, stakes 48, posts 54 (0.57 to
0.73 A: a hurdle 1 to 1.2 m, size-guide "fence" 41 to 67); picket 42, posts 50.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

from scripts.art.kit import build as _B  # noqa: F401  (configures the density)
from scripts.art.kit.schema import PIECES, ROOT
from scripts.art.native import village as V
from scripts.art.native.palette import FI, to_rgba

ART = os.path.join(ROOT, 'game', 'kit', 'props', 'art', 'fence')
RES = 'res://kit/props/art/fence/'
CELL = 24
HALF = 12
SIDES = 'nesw'
VEC = {'n': (0, -1), 'e': (1, 0), 's': (0, 1), 'w': (-1, 0)}
OPP = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}

STYLES = {
    'wattle': dict(panel=42, stake=48, post=54, gate_post=58, thick=4, name='Wattle hurdle',
                   encloses=['sheep', 'chickens', 'crops'], material='hazel'),
    'picket': dict(panel=42, stake=0, post=50, gate_post=54, thick=3, name='Picket fence',
                   encloses=['flowers', 'crops'], material='whitewashed timber'),
}


def C(fam, t):
    return FI[fam] * 8 + int(max(0, min(5, round(t))))


def ramp(fams, t):
    """Tones (float array) as codes in a (cool, body, warm) triple: warm where lit, cool in shade."""
    t = np.clip(np.round(np.asarray(t, float)), 0, 5).astype(int)
    cool, body, warm = (FI[f] for f in fams)
    fa = np.where(t >= 4, warm, np.where(t <= 1, cool, body))
    return fa * 8 + t


HAZEL = ('timber_cool', 'timber', 'timber_warm')
WASH = ('plaster_warm', 'plaster', 'plaster')


def _hash(x, y, k=0):
    """A stable pseudo-random value in [0, 1) per pixel (for flecks that must tile)."""
    v = np.sin(np.asarray(x, float) * 12.9898 + np.asarray(y, float) * 78.233 + k * 37.719) * 43758.5453
    return v - np.floor(v)


# ------------------------------------------------------------------------------------------------
# the box renderer
# ------------------------------------------------------------------------------------------------
class Scene:
    """Boxes in the three-quarter view, drawn back to front by their ground rows, each pixel
    remembering which owner's box won it."""

    def __init__(self, W, H, ox, oy):
        self.code = np.full((H, W), -1, np.int32)
        self.own = np.full((H, W), -1, np.int32)
        self.ox, self.oy = ox, oy
        self.boxes = []

    def box(self, x0, x1, y0, y1, z0, z1, owner, front, top=None, order=0):
        """A box over ground x0..x1, y0..y1 (local texels from the node), heights z0..z1.
        front(X, Z) and top(X, Y) return codes (-1: nothing there)."""
        x0, x1, y0, y1 = int(math.floor(x0)), int(math.ceil(x1)), int(math.floor(y0)), int(math.ceil(y1))
        if x1 > x0 and y1 > y0 and z1 > z0:
            self.boxes.append((y0, y1, order, len(self.boxes), x0, x1, int(z0), int(z1), owner, front, top or front))

    def stamp(self, pts, code, owner):
        """Loose pixels drawn last (tufts at a post's foot): (x, y) local texels."""
        self.boxes.append((10 ** 6, 10 ** 6 + 1, 0, len(self.boxes), 0, 0, 0, 0, owner, ('stamp', pts, code), None))

    def render(self):
        H, W = self.code.shape
        rows = sorted({y for b in self.boxes for y in range(b[0], b[1])})
        for y in rows:
            for (y0, y1, _o, _i, x0, x1, z0, z1, owner, front, top) in sorted(self.boxes, key=lambda b: (b[2], b[3])):
                if not (y0 <= y < y1):
                    continue
                if isinstance(front, tuple):
                    for (px, py) in front[1]:
                        X, Y = px + self.ox, py + self.oy
                        if 0 <= X < W and 0 <= Y < H:
                            self.code[Y, X] = front[2]
                            self.own[Y, X] = owner
                    continue
                xs = np.arange(x0, x1)
                cols = xs + self.ox
                ok = (cols >= 0) & (cols < W)
                # the face towards the viewer (its rows z0 .. z1-2), then the top pixel (z1-1)
                zs = np.arange(z0, z1 - 1)
                if len(zs):
                    Xg, Zg = np.meshgrid(xs, zs)
                    codes = np.asarray(front(Xg, Zg, y), np.int32)
                    rr = y - Zg + self.oy
                    m = (codes >= 0) & ok[None, :] & (rr >= 0) & (rr < H)
                    self.code[rr[m], (Xg + self.ox)[m]] = codes[m]
                    self.own[rr[m], (Xg + self.ox)[m]] = owner
                tc = np.asarray(top(xs, np.full(xs.shape, y), z1 - 1), np.int32)
                r = y - (z1 - 1) + self.oy
                if 0 <= r < H:
                    m = (tc >= 0) & ok
                    self.code[r, cols[m]] = tc[m]
                    self.own[r, cols[m]] = owner
        return self

    def outline(self):
        """The house outline round the whole neighbourhood; each outline pixel belongs to the box
        it closes (so no piece shows a seam where it meets the next)."""
        a = self.code.copy()
        before = a >= 0
        V.tidy(a)
        V.outline(a)
        V.tidy(a, passes=1)
        new = (a >= 0) & ~before
        own = self.own.copy()
        H, W = a.shape
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            src = np.full(own.shape, -1, np.int32)
            ys = slice(max(0, dy), H + min(0, dy))
            yd = slice(max(0, -dy), H + min(0, -dy))
            xs = slice(max(0, dx), W + min(0, dx))
            xd = slice(max(0, -dx), W + min(0, -dx))
            src[yd, xd] = self.own[ys, xs]
            pick = new & (own < 0) & (src >= 0)
            own[pick] = src[pick]
        self.code, self.own = a, own
        return self


# ------------------------------------------------------------------------------------------------
# materials
# ------------------------------------------------------------------------------------------------
def wattle_front(ph, seed):
    """Hazel rods woven between stakes every half cell, seen from the south: courses 4 texels
    apart, each rod lit where it bows out in front of a stake and shaded where it passes behind,
    its upper edge catching the light and a dark gap under it; a twisted binding along the top."""
    def f(X, Z, y=None):
        X = np.asarray(X, float)
        Z = np.asarray(Z, float)
        k = np.floor(Z / 4.0)
        r = Z - 4 * k
        d = np.cos(math.pi * (X - 6) / HALF + math.pi * k)    # +1 in front of a stake, -1 behind
        t = 2.8 + 1.1 * d + 0.9 * (r == 3) - 1.4 * (r == 0) + 0.35 * np.sin(X * math.pi / HALF + k * 2.3)
        t = t - 0.7 * (Z < 4) - 0.4 * (Z < 8)
        fleck = _hash(np.mod(X, CELL), Z, 3) < 0.05
        t = t - 0.8 * fleck
        bind = Z >= ph - 3
        tb = np.where(((X + 2 * Z) // 3) % 2 == 0, 4.2, 2.6) - 0.8 * (Z == ph - 3)
        t = np.where(bind, tb, t)
        return ramp(HAZEL, t)
    return f


def wattle_top(seed):
    def f(X, Y, z=None):
        X = np.asarray(X, float)
        Y = np.asarray(Y, float)
        return ramp(HAZEL, np.where(((X + 2 * Y) // 3) % 2 == 0, 4.6, 3.4))
    return f


def wattle_top_ns(gx):
    """The binding of a run along y seen from above: the twist runs down it, lit on its west edge."""
    def f(X, Y, z=None):
        X = np.asarray(X, float)
        Y = np.asarray(Y, float)
        t = np.where(((Y + 2 * X) // 3) % 2 == 0, 4.0, 3.0) + 0.9 * (X <= gx - 2) - 1.4 * (X >= gx + 1)
        return ramp(HAZEL, t)
    return f


def wattle_end(X, Z, y=None):
    """A run's cut end: the rods' ends, round and lit on top."""
    Z = np.asarray(Z, float)
    return ramp(HAZEL, np.where(Z % 4 == 3, 4.0, np.where(Z % 4 == 0, 1.2, 2.6)) - 0.6 * (Z < 4))


def stake_front(x0, w, ph=None, weave=None, fam=HAZEL, base=3.0):
    """A stake or post: lit west face, mid body, shaded east column, bark rings; behind the rods
    that bow out in front of it (so the weave passes in front of it on alternate courses)."""
    def f(X, Z, y=None):
        X = np.asarray(X, float)
        Z = np.asarray(Z, float)
        t = base + 1.2 * (X == x0) - 1.3 * (X == x0 + w - 1) + 0.0 * Z
        t = t - 0.9 * (((Z * 5 + (X - x0) * 3) % 13) == 0) - 0.8 * (Z < 2)
        c = ramp(fam, t)
        if weave:
            k = np.floor(Z / 4.0)
            d = np.cos(math.pi * (X - 6) / HALF + math.pi * k)
            front_rod = (Z < ph) & (d > -0.2)
            c = np.where(front_rod, -1, c)
        return c
    return f


def cut_top(x0, w, fam=('timber_warm', 'sand_warm', 'sand_warm')):
    def f(X, Y, z=None):
        X = np.asarray(X, float)
        return ramp(fam, 4.0 + 0.8 * (X == x0) - 1.0 * (X == x0 + w - 1))
    return f


def wash_front(x0, w, base=4.0, seed=0):
    """Whitewashed timber: a lit west edge, the body, a shaded east edge, earth splashed at the
    foot, here and there the wash worn off to the grain."""
    def f(X, Z, y=None):
        X = np.asarray(X, float)
        Z = np.asarray(Z, float)
        t = base + 1.0 * (X == x0) - 1.2 * (X == x0 + w - 1) - 0.6 * (Z < 4) - 0.8 * (Z < 2)
        c = ramp(WASH, t)
        worn = (_hash(X, Z, seed) < 0.035) & (Z > 3)
        c = np.where(worn, C('timber', 3), c)
        c = np.where(Z < 2, C('earth', 2), c)
        return c
    return f


def wash_top(X, Y, z=None):
    return np.full(np.shape(X), C('plaster', 5))


# ------------------------------------------------------------------------------------------------
# the parts of a cell
# ------------------------------------------------------------------------------------------------
def _stake(sc, x, y, h, w, owner, ph=None, weave=False, fam=HAZEL, cap=None):
    x0 = int(round(x - w / 2))
    sc.box(x0, x0 + w, y - w // 2, y - w // 2 + w, 0, h, owner, stake_front(x0, w, ph, weave, fam), cut_top(x0, w), order=2)
    if cap:
        sc.box(x0 - 1, x0 + w + 1, y - w // 2 - 1, y - w // 2 + w + 1, h, h + 2, owner,
               lambda X, Z, y_=None: ramp(fam, np.full(np.shape(X), 3.0) + 1.2 * (np.asarray(X) == x0 - 1)), cut_top(x0 - 1, w + 2), order=3)


def _wash_post(sc, x, y, h, w, owner, seed):
    x0 = int(round(x - w / 2))
    sc.box(x0, x0 + w, y - w // 2, y - w // 2 + w, 0, h, owner, wash_front(x0, w, 4.0, seed), wash_top, order=2)
    # the cap: a little pyramid, its lit west slope and shaded east
    for k in range(3):
        sc.box(x0 + k, x0 + w - k, y - w // 2 + k, y - w // 2 + w - k, h + k, h + k + 1, owner,
               wash_front(x0 + k, w - 2 * k, 4.6, seed), lambda X, Y, z=None: np.full(np.shape(X), C('plaster', 5)), order=3)


def _tufts(sc, x, y, owner, seed):
    """A few grass blades at a post's foot, in front of it (the fence stands in turf)."""
    rng = np.random.default_rng(seed)
    for j in range(int(rng.integers(2, 4))):
        bx = x + int(rng.integers(-5, 6))
        h = int(rng.integers(3, 7))
        lean = rng.choice([-1, 0, 1])
        pts = [(bx + (lean if k > h // 2 else 0), y + 2 - k) for k in range(h)]
        sc.stamp(pts[: h // 2], C('grass_cool', 2), owner)
        sc.stamp(pts[h // 2:], C('grass', 4), owner)


def arm_x(sc, style, xa, xb, y, owner, seed, node=0, posted=False):
    """A run along x from xa to xb (local texels) on the ground line y."""
    S = STYLES[style]
    if style == 'wattle':
        ph = S['panel']
        sc.box(xa, xb, y - 2, y + 1, 0, ph, owner, wattle_front(ph, seed), wattle_top(seed), order=1)
        # a stake a quarter cell either side of the node (none in a cell with a post): never on a
        # cell's edge, so every stake belongs to one cell and the weave crosses the joints
        if not posted:
            for x in (node - 6, node + 6):
                if xa < x < xb:
                    _stake(sc, x, y, S['stake'] + (1 if x > node else -1), 4, owner, ph, True)
    else:
        ph = S['panel']
        for zr in (11, 29):                                     # the rails behind the palings
            sc.box(xa, xb, y - 3, y - 1, zr, zr + 4, owner,
                   lambda X, Z, y_=None, zr=zr: ramp(WASH, np.where(np.asarray(Z) == zr + 3, 4.6, np.where(np.asarray(Z) == zr, 2.4, 3.6))),
                   wash_top, order=1)
        for px in range(xa - ((xa - 6) % 8) - 8, xb, 8):           # palings at x = 6 (mod 8): they tile
            if px + 4 <= xa or px >= xb:
                continue
            p0, p1 = max(px, xa), min(px + 4, xb)

            def front(X, Z, y_=None, px=px):
                X = np.asarray(X)
                Z = np.asarray(Z)
                c = wash_front(px, 4, 4.0, seed)(X, Z)
                tip = Z >= ph - 2
                c = np.where(tip & ((X == px) | (X == px + 3)), -1, c)
                return c
            sc.box(p0, p1, y - 1, y + 2, 0, ph, owner, front,
                   lambda X, Y, z=None, px=px: np.where((np.asarray(X) == px) | (np.asarray(X) == px + 3), -1, C('plaster', 5)), order=2)


def arm_y(sc, style, ya, yb, x, owner, seed, node=0, posted=False):
    """A run along y from ya to yb (local texels) on the line x: seen end on, its top running down
    the picture with the stakes' or palings' tops standing out of it."""
    S = STYLES[style]
    if style == 'wattle':
        ph = S['panel']
        sc.box(x - 2, x + 2, ya, yb, 0, ph, owner, wattle_end, wattle_top_ns(x), order=1)
        if not posted:
            for yy in (node - 6, node + 6):
                if ya < yy < yb:
                    _stake(sc, x, yy, S['stake'] + (1 if yy > node else -1), 4, owner)
    else:
        ph = S['panel']
        for zr in (11, 29):
            sc.box(x + 1, x + 3, ya, yb, zr, zr + 4, owner,
                   lambda X, Z, y_=None: ramp(WASH, np.full(np.shape(X), 3.0)), lambda X, Y, z=None: ramp(WASH, np.full(np.shape(X), 3.4)), order=1)
        for py in range(ya - ((ya - 6) % 8) - 8, yb, 8):
            if py + 4 <= ya or py >= yb:
                continue
            p0, p1 = max(py, ya), min(py + 4, yb)
            # each paling seen edge on: its pointed top along y, its south face (a few rows show
            # before the next paling covers it)
            for yy in range(p0, p1):
                tipped = yy in (py, py + 3)
                sc.box(x - 1, x + 2, yy, yy + 1, 0, ph - (2 if tipped else 0), owner,
                       wash_front(x - 1, 3, 3.6, seed),
                       lambda X, Y, z=None: ramp(WASH, 5.0 - 1.2 * (np.asarray(X) == x + 1)), order=2)


def node_post(sc, style, x, y, owner, seed, kind='post'):
    S = STYLES[style]
    if style == 'wattle':
        if kind == 'stake':
            _stake(sc, x, y, S['stake'] + 1, 4, owner, S['panel'], True)
        else:
            _stake(sc, x, y, S['post'], 6, owner, cap=None)
    else:
        _wash_post(sc, x, y, S['post'], 6, owner, seed)


# ------------------------------------------------------------------------------------------------
# pieces
# ------------------------------------------------------------------------------------------------
def joins_name(joins) -> str:
    return ''.join(s for s in SIDES if s in joins)


def cell_pieces():
    """Every cell piece of a style: straights, corners, Ts, a cross and ends."""
    out = []
    for mask in range(1, 16):
        js = [s for i, s in enumerate(SIDES) if mask & (1 << i)]
        out.append(joins_name(js))
    return out


def _draw_cell(sc, style, joins, owner, seed, at=(0, 0), post=None):
    """One cell's arms and its node (local texels, node at `at`)."""
    nx, ny = at
    js = set(joins)
    straight = js in ({'e', 'w'}, {'n', 's'})
    if post is None:
        post = not straight
    if 'n' in js:
        arm_y(sc, style, ny - HALF, ny, nx, owner, seed, ny, post)
    if 'w' in js:
        arm_x(sc, style, nx - HALF, nx, ny, owner, seed, nx, post)
    if 'e' in js:
        arm_x(sc, style, nx, nx + HALF, ny, owner, seed, nx, post)
    if 's' in js:
        arm_y(sc, style, ny, ny + HALF, nx, owner, seed, ny, post)
    if post:
        node_post(sc, style, nx, ny, owner, seed)
        if style == 'wattle' or 'e' in js or 'w' in js:
            _tufts(sc, nx, ny, owner, seed + 5)


GATE = 3                         # cells a gate spans along its run
GATE_POST = 31                   # its posts, from its middle (texels): inside the opening's ends,
                                 # beside the neighbours' end stakes at 36


def _draw_gate(sc, style, axis, owner, seed, state, at=(0, 0)):
    """A gate three cells wide (a 1.3 m opening, wide enough for a barrow): a post near each end,
    the leaf between them, shut or swung open inside. Its foot is the middle cell's node: axis
    'ew' lies along x, 'ns' along y."""
    S = STYLES[style]
    gx, gy = at
    gp = S['gate_post']
    if axis == 'ew':
        posts = [(gx - GATE_POST, gy), (gx + GATE_POST, gy)]
    else:
        posts = [(gx, gy - GATE_POST), (gx, gy + GATE_POST)]
    for (px, py) in posts:
        if style == 'wattle':
            _stake(sc, px, py, gp, 6, owner, cap=None)
        else:
            _wash_post(sc, px, py, gp, 6, owner, seed)
            # a ball on the gatepost's cap
            sc.box(px - 2, px + 2, py - 2, py + 2, gp + 3, gp + 6, owner, wash_front(px - 2, 4, 4.4, seed), wash_top, order=4)
    lift = 2
    a = -GATE_POST + 4
    b = GATE_POST - 4
    L = b - a
    if state == 'shut':
        if axis == 'ew':
            _leaf_x(sc, style, gx + a, gx + b, gy, owner, seed, lift)
        else:
            _leaf_y(sc, style, gy + a, gy + b, gx, owner, seed, lift)
    elif axis == 'ew':                           # swung north on the west post, lying along y
        _leaf_y(sc, style, gy - 3 - L, gy - 3, gx + a, owner, seed, lift)
    elif state == 'open_e':                      # swung on the north post, lying along x
        _leaf_x(sc, style, gx + 4, gx + 4 + L, gy + a - 1, owner, seed, lift)
    else:
        _leaf_x(sc, style, gx - 4 - L, gx - 4, gy + a - 1, owner, seed, lift)


def _leaf_x(sc, style, xa, xb, y, owner, seed, lift):
    S = STYLES[style]
    ph = S['panel'] - 2
    if style == 'wattle':
        # a hurdle: its two end sails and the weave between, hung a little off the ground
        sc.box(xa, xb, y - 2, y + 1, lift, ph, owner, wattle_front(ph, seed + 3), wattle_top(seed), order=1)
        for x in (xa + 1, xb - 2):
            sc.box(x - 1, x + 2, y - 2, y + 2, lift - 1, ph + 3, owner, stake_front(x - 1, 3, base=3.4), cut_top(x - 1, 3), order=2)
        # the rope loop of the latch over the gatepost
        sc.box(xb - 1, xb + 3, y - 1, y + 2, ph - 8, ph - 5, owner,
               lambda X, Z, y_=None: np.full(np.shape(X), C('sand', 3)), lambda X, Y, z=None: np.full(np.shape(X), C('sand', 4)), order=5)
    else:
        for px in range(xa, xb - 3, 6):
            sc.box(px, px + 4, y, y + 3, lift, ph, owner, wash_front(px, 4, 4.0, seed + 1),
                   lambda X, Y, z=None, px=px: np.where((np.asarray(X) == px) | (np.asarray(X) == px + 3), -1, C('plaster', 5)), order=2)
        # ledges and the brace on the gate's face (in front of the palings)
        for zl in (9, ph - 12):
            sc.box(xa, xb, y + 3, y + 4, zl, zl + 4, owner,
                   lambda X, Z, y_=None, zl=zl: ramp(WASH, np.where(np.asarray(Z) == zl + 3, 4.8, 3.4) - 1.0 * (np.asarray(Z) == zl)),
                   wash_top, order=3)
        L = xb - xa

        def brace(X, Z, y_=None):
            X = np.asarray(X, float)
            Z = np.asarray(Z, float)
            zc = 12 + (X - xa) * (ph - 26) / max(1, L)
            on = np.abs(Z - zc) <= 1.5
            return np.where(on, ramp(WASH, 3.8 + 0.9 * (Z > zc)), -1)
        sc.box(xa + 2, xb - 2, y + 4, y + 5, 10, ph - 10, owner, brace, lambda X, Y, z=None: np.full(np.shape(X), -1), order=4)


def _leaf_y(sc, style, ya, yb, x, owner, seed, lift):
    S = STYLES[style]
    ph = S['panel'] - 2
    if style == 'wattle':
        sc.box(x - 2, x + 2, ya, yb, lift, ph, owner, wattle_end, wattle_top_ns(x), order=1)
        for yy in (ya + 1, yb - 2):
            sc.box(x - 2, x + 2, yy - 1, yy + 2, lift - 1, ph + 3, owner, stake_front(x - 2, 4, base=3.4), cut_top(x - 2, 4), order=2)
    else:
        for py in range(ya, yb - 3, 6):
            for yy in range(py, py + 4):
                tipped = yy in (py, py + 3)
                sc.box(x - 1, x + 2, yy, yy + 1, lift, ph - (2 if tipped else 0), owner, wash_front(x - 1, 3, 3.6, seed),
                       lambda X, Y, z=None: ramp(WASH, 5.0 - 1.2 * (np.asarray(X) == x + 1)), order=2)


# The neighbourhood: every arm continues into a straight run two cells long, so the piece is drawn
# among the pixels that will stand round it in a zone.
PAD = 84


def render_piece(style, joins=None, gate=None, state='shut', post=None, seed=0):
    """(Pic, foot, owned mask) for one piece: a cell (joins) or a gate (gate='ew' or 'ns')."""
    S = STYLES[style]
    top = max(S['gate_post'], S['post']) + 10
    W, H = 2 * PAD + 1, 2 * PAD + top + 1
    sc = Scene(W, H, PAD, PAD + top)
    ME = 0
    # the neighbours first, this piece last: where two pieces draw the same stake (the end stake
    # both arms of a joint carry) this piece keeps it, so either may be drawn over the other
    if gate is None:
        for nb, s in enumerate(joins, start=1):
            dx, dy = VEC[s]
            for k in (1, 2):
                _draw_cell(sc, style, [s, OPP[s]], nb, seed + 17 * k, at=(dx * CELL * k, dy * CELL * k), post=False)
        _draw_cell(sc, style, joins, ME, seed, post=post)
    else:
        for k in (2, 3):
            if gate == 'ew':
                _draw_cell(sc, style, ['e', 'w'], 1, seed + k, at=(-CELL * k, 0), post=False)
                _draw_cell(sc, style, ['e', 'w'], 2, seed + k, at=(CELL * k, 0), post=False)
            else:
                _draw_cell(sc, style, ['n', 's'], 1, seed + k, at=(0, -CELL * k), post=False)
                _draw_cell(sc, style, ['n', 's'], 2, seed + k, at=(0, CELL * k), post=False)
        _draw_gate(sc, style, gate, ME, seed, state)
    sc.render().outline()
    mine = sc.own == ME
    a = np.where(mine, sc.code, -1)
    ys, xs = np.nonzero(a >= 0)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    crop = a[y0:y1, x0:x1]
    pic = V.Pic(crop.shape[1], crop.shape[0], sc.ox - x0, sc.oy - y0)
    pic.a[:] = crop
    return pic


def _pieces_for(style):
    """(id, kwargs, variants, joins, gate axis) for every piece of a style."""
    out = []
    for jn in cell_pieces():
        js = list(jn)
        straight = set(js) in ({'e', 'w'}, {'n', 's'})
        vs = [('plain', dict(joins=js, post=False if straight else None))]
        if straight:
            vs.append(('post', dict(joins=js, post=True)))
        out.append(('fence_%s_%s' % (style, jn), vs, js, None))
    out.append(('fence_%s_gate_ew' % style, [('open', dict(gate='ew', state='open')), ('shut', dict(gate='ew', state='shut'))], ['e', 'w'], 'ew'))
    out.append(('fence_%s_gate_ns' % style, [('open_e', dict(gate='ns', state='open_e')), ('open_w', dict(gate='ns', state='open_w')),
                                              ('shut', dict(gate='ns', state='shut'))], ['n', 's'], 'ns'))
    return out


def _collision(js, gate):
    """The solid line in world px from the foot: the run's arms, a world px either side."""
    if gate:
        return {'shape': 'none'}
    x0 = -4.0 if 'w' in js else -1.5
    x1 = 4.0 if 'e' in js else 1.5
    y0 = -4.0 if 'n' in js else -1.5
    y1 = 4.0 if 's' in js else 1.0
    return {'shape': 'rect', 'rect': [x0, y0, x1 - x0, y1 - y0]}


def piece_json(style, pid, variants, js, gate, sizes):
    S = STYLES[style]
    name = S['name'] + (', gate along %s' % ('x' if gate == 'ew' else 'y') if gate else ', ' + {
        1: 'end post', 2: 'straight' if set(js) in ({'e', 'w'}, {'n', 's'}) else 'corner', 3: 'T', 4: 'cross'}[len(js)])
    w, h, foot = sizes
    gate_note = ('a gate stands where the path its owner walks crosses the fence (placement-logic rule 2); the trodden way runs '
                 'through it')
    req = [{'rel': 'on', 'what': 'route', 'note': gate_note}] if gate else []
    forb = [] if gate else [{'rel': 'on', 'what': 'route'}, {'rel': 'on', 'what': 'water'}]
    if gate == 'ew':
        fp = [[-1, -1], [0, -1], [1, -1]]
    elif gate == 'ns':
        fp = [[0, -2], [0, -1], [0, 0]]
    else:
        fp = [[0, -1]]
    purpose = 'contain' if style == 'wattle' else 'mark'
    return {
        'schema': 'napattack.piece/1', 'id': pid, 'name': name, 'kind': 'prop', 'biomes': ['village', 'valley'], 'version': 1,
        'variants': [{'id': vid, 'weight': 1.0 if vid in ('plain', 'open', 'open_e') else 0.5,
                      'png': RES + '%s_%s.png' % (pid, vid), 'foot': list(sizes_v)}
                     for (vid, _kw), sizes_v in zip(variants, foot)],
        'approval': {'state': 'candidate', 'by': None, 'at': None, 'standard': 'art-style.md (Eastward\'s level of detail), placement-logic.md',
                     'note': 'Modular fence cell (scripts/art/kit/fences.py): closes loops with its neighbours, gates on the path.'},
        'geometry': {'size_px': [w, h], 'size_cells': [GATE if gate == 'ew' else 1, GATE if gate == 'ns' else 1], 'z_sort': 'foot',
                     'height_px': S['gate_post'] if gate else (S['post'] if len(js) != 2 or set(js) not in ({'e', 'w'}, {'n', 's'}) else S['panel']),
                     'collision': _collision(js, gate), 'foot': list(foot[0]), 'footprint': fp},
        'placement': {'snap': 'cell', 'purpose': purpose, 'role': 'gate' if gate else 'boundary', 'composition': 'edge',
                      **({'requires': req} if req else {}), **({'forbids': forb} if forb else {}),
                      'boundary': {'style': style, 'joins': list(js), 'gate': bool(gate), 'span_cells': GATE if gate else 1,
                                   'encloses': list(S['encloses'])}},
        'rendering': {'cast_shadow': {'shape': 'ellipse', 'size': [8 if gate != 'ew' else 22, 3], 'dir': [1, 1]}, 'contact_ao': True},
        'function': {'interact': {'verb': 'open', 'triggers': []}} if gate else {},
        'story': {'owner': None},
        'gameplay': {'blocks_move': not gate, 'blocks_shots': False},
        'audit': {'size_class': 'fence', 'eastward_ref': '17 (the farm: rail fence and gate, 40 E = 0.75 A), 12 and 38 (palisades)',
                  'painter': {'module': 'scripts.art.kit.fences', 'fn': 'render_piece', 'args': {'style': style}},
                  'seeded_from': 'scripts/art/kit/fences.py', 'todo': []},
    }


def build(write=True, force=False):
    """Draw every piece; write the pictures (and the pieces, kept if they exist unless force).
    Returns {png path: rgba array} for --check."""
    out = {}
    for style in STYLES:
        for k, (pid, variants, js, gate) in enumerate(_pieces_for(style)):
            pics = []
            for j, (vid, kw) in enumerate(variants):
                pic = render_piece(style, seed=101 + 7 * k + j if style == 'wattle' else 3 + k, **kw)
                pics.append((vid, pic))
                out[os.path.join(ART, '%s_%s.png' % (pid, vid))] = to_rgba(pic.a)
            sizes = (max(p.W for _v, p in pics), max(p.H for _v, p in pics), [(p.ax, p.ay) for _v, p in pics])
            if write:
                d = os.path.join(PIECES, 'prop')
                path = os.path.join(d, pid + '.json')
                if force or not os.path.exists(path):
                    json.dump(piece_json(style, pid, variants, js, gate, sizes), open(path, 'w'), indent=1)
                    open(path, 'a').write('\n')
    if write:
        os.makedirs(ART, exist_ok=True)
        for p, a in out.items():
            Image.fromarray(a, 'RGBA').save(p, optimize=True)
    return out


def check() -> int:
    bad = []
    for p, a in build(write=False).items():
        if not os.path.exists(p) or not np.array_equal(np.asarray(Image.open(p).convert('RGBA')), a):
            bad.append(os.path.relpath(p, ROOT))
    if bad:
        print('fences: stale pictures %s (run python3 -m scripts.art.kit.fences)' % ', '.join(bad[:6]))
        return 1
    print('fences: pictures current')
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    if a.check:
        return check()
    n = len(build(force=a.force))
    print('fences: %d pictures' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
