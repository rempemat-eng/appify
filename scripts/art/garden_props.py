"""Garden props at the step-6 density (docs/vision/coherence-plan.md).

Sizes follow the proportions table, in art pixels, against a 32 x 32 companion that
stands about 26 pixels tall: the hut is three and a half companions tall, its door
just taller than the companion, trees tower over it, bushes and rocks stay below it.

Shading rules: light from the upper left; each surface is a clean plane of one or
two tones (no dither noise); edges catching the light get one lighter row, edges
turning away one darker; cast shadows are baked into the ground by garden.py; every
silhouette gets a material-tinted outline from style.close_outline afterwards.
Colours come only from the canonical ramps in art/materials.json.
"""
from __future__ import annotations

import math

import style
import detail
from materials import CREAM, GOLD, LEAF, MATERIALS, NAP, PLASTER, RED, SAND, SLATE, STONE, WOOD, WTR
from pixel import Canvas, disc, noise2, oval

G = MATERIALS['grass']
# Working room around every prop: art may stray past its nominal box and is kept
# (style.finalize trims it and records the offset), so nothing is ever cut off.
PAD = 16
PATH = MATERIALS['path']
PINE = ['#1F2E2A', '#2F4A3C', '#46664B', '#5E8253', '#86A766']
AUTUMN = ['#4A2A22', '#7A4030', '#A8623E', '#CB8650', '#E8B575']


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


def despeckle(cv: Canvas, keep=frozenset(), passes: int = 2) -> Canvas:
    """Detail comes in clusters of two or more pixels, never single-pixel noise (art-style.md,
    the detail bar's cleanliness counts): a drawn pixel whose colour differs from all four
    of its drawn neighbours takes the commonest of theirs. Pixels in `keep` (an eye, a
    glint) stay as drawn; edge pixels with fewer than three drawn neighbours are left, so
    silhouettes keep their tips."""
    p = cv.pad
    for _ in range(passes):
        changed = []
        for y in range(-p, cv.h + p):
            for x in range(-p, cv.w + p):
                c = cv.get(x, y)
                if not c[3] or (x, y) in keep:
                    continue
                ns = [cv.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                ns = [n for n in ns if n[3]]
                if len(ns) >= 3 and all(n != c for n in ns):
                    changed.append((x, y, max(ns, key=ns.count)))
        for (x, y, c) in changed:
            cv.set(x, y, c)
        if not changed:
            break
    return cv


def draw_rows(cv: Canvas, rows, inks: dict, x0: int = 0, y0: int = 0, flip: bool = False):
    """Hand-placed pixel art: each character of `rows` is one pixel, '.' left clear and
    any other character the colour `inks` gives it, drawn with its top-left at (x0, y0)
    (mirrored east to west when `flip`). Small props drawn this way keep every mark a
    cluster of two or more pixels, as the detail bar's cleanliness counts ask."""
    for y, row in enumerate(rows):
        for x, ch in enumerate(row[::-1] if flip else row):
            if ch != '.':
                cv.set(x0 + x, y0 + y, inks[ch])


def keep_foot(cv: Canvas, w: int, h: int, dx: int | None = None) -> Canvas:
    """Re-seat a prop drawn at its true size (verticality.md 5, the scale table) in the
    nominal w x h box it had before, so its foot stays where the zones place it: the
    drawing's bottom row lands on the box's bottom row, centred (or moved right by dx).
    A taller prop rises above the box into the padding, a smaller one sits inside it;
    style.finalize trims it either way and placement adds the offset. Window panes
    recorded for the drawing (WINDOWS) move with it."""
    sx = (w - cv.w) // 2 if dx is None else dx
    sy = h - cv.h
    pad = max(cv.pad, cv.pad - sy + 2, cv.pad + abs(sx) + 2)
    out = Canvas(w, h, pad=pad, density=getattr(cv, 'density', 1))
    p = cv.pad
    src = cv.img.load()
    for y in range(cv.h + 2 * p):
        for x in range(cv.w + 2 * p):
            c = src[x, y]
            if c[3]:
                out.set(x - p + sx, y - p + sy, c)
    for i, (c, (gx, gy, gw, gh)) in enumerate(WINDOWS):
        if c is cv:
            WINDOWS[i] = (out, (gx + sx, gy + sy, gw, gh))
    return out


# the warm yellow-green the sun leaves on the outermost leaves (Cainos' and Eastward's
# trees: a highlight hue, not just a lighter green); per leaf ramp
LEAF_SUN = {'#A1C068': '#D2DC86', '#E8B575': '#F6D99A'}


def canopy(cv: Canvas, lobes, ramp, seed: int = 0, clumps: bool = False) -> set:
    """Foliage as a few large leaf masses (Matt's references): each lobe is shaded as a
    sphere lit from the upper left in clean bands, a lobe in front casts a dark rim on
    the one behind it, the silhouette is scalloped by small leaf bumps, and a sparse
    scatter of leaf ticks gives texture without noise. Lobes are listed back to front."""
    shape = set()
    owner = {}
    for i, (cx, cy, r) in enumerate(lobes):
        pts = set(disc(cx, cy, r))
        # leaf bumps around the lobe's upper and side rim
        n = max(6, int(2 * math.pi * r / 3.2))
        for k in range(n):
            a = 2 * math.pi * (k + 0.4 * noise2(k, seed + i, 7)) / n
            bx, by = cx + r * 0.94 * math.cos(a), cy + r * 0.94 * math.sin(a)
            if math.sin(a) > 0.55:
                continue
            pts |= set(disc(bx, by, 1.9))
        for p in pts:
            owner[p] = i
        shape |= pts
    for (x, y) in shape:
        cx, cy, r = lobes[owner[(x, y)]]
        nx, ny = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
        nz = math.sqrt(max(0.0, 1 - min(1.0, nx * nx + ny * ny)))
        lv = -0.55 * nx - 0.75 * ny + 0.4 * nz
        tone = 4 if lv > 0.82 else 3 if lv > 0.3 else 2 if lv > -0.25 else 1
        cv.set(x, y, ramp[tone])
    # a front lobe darkens the rim of the lobe behind it, which separates the masses
    for (x, y) in shape:
        i = owner[(x, y)]
        for dx, dy in ((0, -1), (-1, 0), (1, 0)):
            n = (x + dx, y + dy)
            if n in owner and owner[n] > i and dy <= 0:
                cv.set(x, y, ramp[1])
                break
    # leaf ticks: a light mark over a dark one, only on lit and mid tones
    xs = [x for x, _ in shape]
    ys = [y for _, y in shape]
    for k in range(len(shape) // 26):
        x = min(xs) + int(noise2(k, seed, 31) * (max(xs) - min(xs) + 1))
        y = min(ys) + int(noise2(k, seed, 32) * (max(ys) - min(ys) + 1))
        if (x, y) in shape and (x + 1, y + 1) in shape and owner.get((x, y)) == owner.get((x + 1, y + 1)):
            cur = cv.get(x, y)
            if cur[:3] in (tuple(int(ramp[3][i:i + 2], 16) for i in (1, 3, 5)),
                           tuple(int(ramp[2][i:i + 2], 16) for i in (1, 3, 5))):
                cv.set(x, y, ramp[4] if cur[:3] == tuple(int(ramp[3][i:i + 2], 16) for i in (1, 3, 5)) else ramp[3])
                cv.set(x + 1, y + 1, ramp[1] if cur[:3] != tuple(int(ramp[3][i:i + 2], 16) for i in (1, 3, 5)) else ramp[2])
    if clumps:
        leaf_clumps(cv, shape, owner, lobes, ramp, seed)
    return shape


def leaf_clumps(cv: Canvas, shape: set, owner: dict, lobes, ramp, seed: int):
    """The art-style detail pass for a crown (art-style.md, detail target): every lobe is
    built of smaller leaf clusters, each a little sphere of its own lit from the upper
    left, so the crown reads as clusters within masses (Cainos' and Eastward's trees)
    rather than as smooth balls. Clusters are drawn back to front; a front cluster's
    dark underside lands on the one behind it. The sunniest clusters take the warm
    yellow-green highlight on their upper-left crescent. Clusters stay inside their
    lobe, so the dark line where one lobe passes in front of another survives, and the
    shade side keeps fewer, darker clusters so it stays quiet at phone size."""
    sun = LEAF_SUN.get(ramp[4], ramp[4])
    clusters = []
    for i, (cx, cy, r) in enumerate(lobes):
        sub = r * 0.46
        n = 6 if r > 11 else 5
        for k in range(n):
            a = 2 * math.pi * (k + 0.35 * noise2(k, seed + i, 71)) / n - math.pi / 2
            d = r * (0.48 + 0.12 * noise2(k, seed + i, 72))
            clusters.append((cx + d * math.cos(a), cy + d * math.sin(a) * 0.9, sub * (0.9 + 0.25 * noise2(k, i, 73)), i))
        clusters.append((cx - r * 0.12, cy - r * 0.15, sub * 1.05, i))  # the lit middle
    def band(px, py, i):
        cx, cy, rr = lobes[i]
        nx, ny = (px + 0.5 - cx) / rr, (py + 0.5 - cy) / rr
        nz = math.sqrt(max(0.0, 1 - min(1.0, nx * nx + ny * ny)))
        lv = -0.55 * nx - 0.75 * ny + 0.4 * nz
        return 4 if lv > 0.82 else 3 if lv > 0.3 else 2 if lv > -0.25 else 1
    for (ccx, ccy, rr, i) in sorted(clusters, key=lambda c: (c[1], c[0])):
        pts = {p for p in disc(ccx, ccy, rr) if p in shape and owner.get(p) == i}
        if not pts:
            continue
        t = band(ccx, ccy, i)
        for (x, y) in pts:
            nx, ny = (x + 0.5 - ccx) / rr, (y + 0.5 - ccy) / rr
            lv = -0.6 * nx - 0.8 * ny
            tone = t + (1 if lv > 0.45 else 0 if lv > -0.35 else -1)
            tone = max(0 if t <= 1 else 1, min(4, tone))
            cv.set(x, y, ramp[tone])
        for (x, y) in pts:
            nx, ny = (x + 0.5 - ccx) / rr, (y + 0.5 - ccy) / rr
            if (x, y + 1) not in pts and ny > 0.2:
                # the cluster's dark underside, notched so it reads as leaves, not a line
                cv.set(x, y, ramp[max(0, t - 2)])
                if (x + int(ccx * 3)) % 3 == 0 and (x, y - 1) in pts:
                    cv.set(x, y - 1, ramp[max(0, t - 2)])
            elif t >= 3 and -0.95 < nx < -0.15 and -0.95 < ny < -0.2 and nx * nx + ny * ny > 0.45:
                cv.set(x, y, sun if t == 4 else ramp[4])  # its sunlit crescent
        # leaf ticks: a few two-pixel leaves across the cluster, light on the lit side
        # and dark on the shade side, so its surface has a grain at phone size
        for q in range(max(1, len(pts) // 14)):
            lx = int(ccx + (noise2(q, int(ccx), seed + 81) - 0.5) * rr * 1.4)
            ly = int(ccy + (noise2(q, int(ccy), seed + 82) - 0.5) * rr * 1.2)
            if (lx, ly) in pts and (lx + 1, ly) in pts and (lx, ly + 1) in pts:
                nx, ny = (lx + 0.5 - ccx) / rr, (ly + 0.5 - ccy) / rr
                lit = -0.6 * nx - 0.8 * ny > 0
                if lit and t >= 2:
                    cv.set(lx, ly, ramp[min(4, t + 1)] if t < 4 else sun)
                    cv.set(lx + 1, ly, ramp[min(4, t)])
                elif not lit:
                    cv.set(lx, ly + 1, ramp[max(0, t - 2)])


def plane(cv: Canvas, pts, ramp, base: int, lit_edge: bool = True, dark_edge: bool = True):
    """A clean plane: one tone, a lit top/left edge row and a shaded bottom/right row."""
    pts = set(pts)
    top = len(ramp) - 1
    for (x, y) in pts:
        tone = base
        if dark_edge and ((x + 1, y) not in pts or (x, y + 1) not in pts):
            tone = base - 1
        if lit_edge and ((x - 1, y) not in pts or (x, y - 1) not in pts):
            tone = base + 1
        cv.set(x, y, ramp[max(0, min(top, tone))])


def planks(cv: Canvas, x0, y0, w, h, ramp, step=4, vertical=True, base=2):
    """Boards with a lit left/top edge and a dark seam, and a knot here and there."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            k = (x - x0) if vertical else (y - y0)
            pos = k % step
            col = ramp[base]
            if pos == 0:
                col = ramp[min(len(ramp) - 1, base + 1)]
            elif pos == step - 1:
                col = ramp[max(0, base - 1)]
            cv.set(x, y, col)
    for i in range(0, w * h // 90):
        kx = x0 + int(noise2(i, x0, 11) * (w - 2)) + 1
        ky = y0 + int(noise2(i, y0, 12) * (h - 2)) + 1
        cv.set(kx, ky, ramp[max(0, base - 1)])


def stone_blocks(cv: Canvas, x0, y0, w, h, block=8):
    """A course of dressed stones: lit top edge, shaded right edge, alternating tones."""
    for i, x in enumerate(range(x0, x0 + w, block)):
        bw = min(block, x0 + w - x)
        base = 3 if i % 2 else 2
        for yy in range(y0, y0 + h):
            for xx in range(x, x + bw):
                col = STONE[base]
                if yy == y0:
                    col = STONE[base + 1]
                elif xx == x + bw - 1 or yy == y0 + h - 1:
                    col = STONE[base - 1]
                cv.set(xx, yy, col)


# ---- the nap hut -----------------------------------------------------------
# Every window drawn, as (canvas, glass rect): zones.py turns these into the panes
# that light up at night (lib/zone-maps.ts, zoneWindows).
WINDOWS: list = []


def window(cv: Canvas, x: int, y: int, w: int = 16, h: int = 14, shutters=NAP, curtain=PLASTER,
           sill: bool = True, warm: bool = False):
    """A deep window: a trim lit on its top and left, glass that reflects the sky at the
    top and darkens toward the room, a curtain valance and tied-back curtains, glazing
    bars, a glint, painted slatted shutters and a sill that casts its shadow."""
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            cv.set(xx, yy, WOOD[2])
    cv.hline(x, y, w, WOOD[4]); cv.vline(x, y, h, WOOD[3])
    cv.hline(x + 1, y + h - 1, w - 1, WOOD[1]); cv.vline(x + w - 1, y + 1, h - 1, WOOD[1])
    gx, gy, gw, gh = x + 2, y + 2, w - 4, h - 4
    WINDOWS.append((cv, (gx, gy, gw, gh)))
    glass = rect_set(gx, gy, gw, gh)
    for (xx, yy) in glass:
        k = yy - gy
        if warm:  # lamplight inside: brightest low in the room, the frame's shadow above
            cv.set(xx, yy, GOLD[3] if k < 2 else GOLD[4] if k < gh - 2 else GOLD[3])
        else:
            cv.set(xx, yy, WTR[2] if k < 2 else WTR[1] if k < gh - 3 else WTR[0])
    # a scalloped valance and curtains tied back two thirds of the way down
    for xx in range(gx, gx + gw):
        cv.set(xx, gy, curtain[4] if (xx - gx) % 2 == 0 else curtain[3])
    tie = gy + (gh * 2) // 3
    for yy in range(gy + 1, gy + gh):
        reach = 1 if yy == tie else 2
        for i in range(reach):
            cv.set(gx + i, yy, curtain[4] if i == 0 else curtain[3])
            cv.set(gx + gw - 1 - i, yy, curtain[3] if i == 0 else curtain[2])
    cv.set(gx + 1, tie, RED[3]); cv.set(gx + gw - 2, tie, RED[2])
    # glazing bars
    mx, my = gx + gw // 2, gy + gh // 2
    cv.vline(mx, gy + 1, gh - 1, WOOD[2]); cv.hline(gx + 2, my, gw - 4, WOOD[2])
    cv.set(mx, my, WOOD[3])
    # glints: a short diagonal in each upper pane
    for px in (gx + 4, mx + 3):
        if not warm:
            cv.set(px, gy + 2, WTR[4]); cv.set(px - 1, gy + 3, WTR[3])
    detail.recess(cv, glass, depth=1, k=1)
    if shutters:
        for sx, lit in ((x - 4, True), (x + w, False)):
            for yy in range(y, y + h):
                for i in range(4):
                    slat = shutters[3] if (yy - y) % 2 == 0 else shutters[2]
                    if i == 0:
                        slat = shutters[4] if lit else shutters[2]
                    elif i == 3:
                        slat = shutters[1]
                    cv.set(sx + i, yy, slat)
            cv.hline(sx, y, 4, shutters[4] if lit else shutters[3])
            cv.hline(sx, y + h - 1, 4, shutters[1])
    if sill:
        cv.hline(x - 1, y + h, w + 2, WOOD[4]); cv.hline(x - 1, y + h + 1, w + 2, WOOD[1])
        detail.overhang_shadow(cv, x, x + w + 2, y + h + 2, lambda xx: 1 if xx < x + 4 else 2, k=2)


def topdown_roof(cv: Canvas, ridge: float, apex_y: int, eave_y: int, left_x: int, right_x: int,
                 ramp, hole=frozenset(), offset=None, seed: int = 31, moss=LEAF, lit_base: int = 3,
                 shade_base: int = 2, barge=WOOD):
    """A gable roof seen steeply from above (the hut's rule, shared by every building):
    two slate planes falling left and right of a ridge that runs back from the front
    gable's apex, the far edge peaking at the ridge, rounded ridge caps, eaves that show
    their thickness and thick bargeboards along the gable. Returns the planes and the
    bargeboard line, so callers can lay the gable and the front wall under it."""
    slope = (eave_y - apex_y) / (ridge - left_x)

    def edge_y(x):
        return apex_y + abs(x + 0.5 - ridge) * slope

    def back_y(x):
        return 1 + abs(x + 0.5 - ridge) * slope

    left = {(x, y) for x in range(left_x, int(ridge) + 1) for y in range(0, eave_y + 1)
            if back_y(x) <= y <= edge_y(x)} - set(hole)
    right = {(x, y) for x in range(int(ridge) + 1, right_x + 1) for y in range(0, eave_y + 1)
             if back_y(x) <= y <= edge_y(x)} - set(hole)
    detail.slate_plane(cv, left, ramp, lit_base, ridge, -1, seed=seed, moss=moss, skew=slope, offset=offset)
    detail.slate_plane(cv, right, ramp, shade_base, ridge, 1, seed=seed + 1, moss=moss, skew=slope, offset=offset)
    rx = int(ridge) - 2
    for y in range(0, apex_y + 2):
        k = y % 4
        cv.set(rx, y, ramp[1]); cv.set(rx + 1, y, ramp[4] if k else ramp[3])
        cv.set(rx + 2, y, ramp[3] if k else ramp[2]); cv.set(rx + 3, y, ramp[2] if k else ramp[1]); cv.set(rx + 4, y, ramp[0])
    for x in range(left_x, right_x + 1):
        by = int(back_y(x))
        if (x, by) in left:
            cv.set(x, by, ramp[4])
        elif (x, by) in right:
            cv.set(x, by, ramp[3])
    for y in range(0, eave_y + 1):
        if (left_x, y) in left:
            cv.set(left_x, y, ramp[4])
        if (right_x, y) in right:
            cv.set(right_x, y, ramp[1])
    for x in range(left_x - 1, right_x + 2):
        ey = int(edge_y(x))
        lit = x < ridge
        cv.set(x, ey, barge[4] if lit else barge[3]); cv.set(x, ey + 1, barge[3] if lit else barge[2])
        cv.set(x, ey + 2, barge[1])
    return left, right, edge_y


def topdown_gable(cv: Canvas, edge_y, x0: int, x1: int, apex_y: int, wall_top: int, ramp=WOOD,
                  boards: bool = True) -> set:
    """The gable under a top-down roof: boards (or plaster), shaded under the bargeboards."""
    gable = {(x, y) for x in range(x0, x1 + 1) for y in range(apex_y, wall_top) if y > edge_y(x) + 2}
    if boards:
        detail.boards(cv, gable, ramp, 2, apex_y, board=5, vertical=True, x0=x0, joints=False, grain=0.05)
    else:
        for (x, y) in gable:
            cv.set(x, y, ramp[4] if x < (x0 + x1) / 2 else ramp[3])
    for (x, y) in gable:
        if (x, y - 1) not in gable or (x, y - 2) not in gable:
            detail.shade(cv, x, y, 2 if (x, y - 1) not in gable else 1)
    return gable


def arched_door(cv: Canvas, dx0: int, dy0: int, dw: int = 16, dh: int = 28, porthole: bool = True) -> set:
    """A round-topped plank door recessed in a stone arch, with iron straps; returns the
    arch's pixels (it stands proud of the wall)."""
    door = {(x, y) for (x, y) in disc(dx0 + dw / 2, dy0 + dw / 2, dw / 2) if y < dy0 + dh}
    door |= rect_set(dx0, dy0 + dw // 2, dw, dh - dw // 2)
    arch = set()
    for (x, y) in door:
        for ax, ay in ((-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1), (-2, 0), (2, 0), (0, -2), (-2, -1), (2, -1)):
            if (x + ax, y + ay) not in door and y + ay < dy0 + dh:
                arch.add((x + ax, y + ay))
    for (x, y) in arch:
        k = int(((x - dx0 - dw / 2) * 0.9 + (y - dy0) * 0.6) // 3)
        cv.set(x, y, STONE[(3 if k % 2 else 2) - (1 if x > dx0 + dw / 2 + 1 else 0)])
    for (x, y) in arch:
        if (x - 1, y) not in arch and (x, y - 1) not in arch:
            cv.set(x, y, STONE[4])
    detail.boards(cv, door, WOOD, 3, dy0, board=4, vertical=True, x0=dx0, joints=False, grain=0.06)
    for sy in (dy0 + dh // 2 - 1, dy0 + dh - 5):
        cv.hline(dx0 + 1, sy, dw - 7, SLATE[1]); cv.hline(dx0 + 1, sy - 1, dw - 7, SLATE[2])
        cv.set(dx0 + 3, sy - 1, SLATE[4])
    if porthole:
        for (x, y) in disc(dx0 + dw / 2, dy0 + 7, 2.8):
            cv.set(x, y, WOOD[1])
        for (x, y) in disc(dx0 + dw / 2, dy0 + 7, 1.9):
            cv.set(x, y, WTR[2])
    detail.recess(cv, door, depth=2, k=1)
    cv.set(dx0 + dw - 4, dy0 + dh * 2 // 3, GOLD[4]); cv.set(dx0 + dw - 4, dy0 + dh * 2 // 3 + 1, GOLD[2])
    return arch


# The hut's outside, chosen while decorating (coherence plan, B1): the door's paint as
# (ramp, base tone), and what sits under each window. The defaults are the hut as drawn
# before the choices, which the vignettes still use.
HUT_DOORS = {'oak': (WOOD, 3), 'red': (RED, 2), 'violet': (NAP, 2), 'green': (LEAF, 2)}
HUT_SILLS = ('sill', 'flowers', 'herbs')


def window_box(cv: Canvas, x0: int, y0: int, planting: str, seed: int, shift: int = 0):
    """A planter 18 x 4 hung under a window, its top edge lit, with flowers (bloom heads
    over leaves) or kitchen herbs (round basil, thin rosemary, chives in lilac flower)."""
    detail.boards(cv, rect_set(x0, y0, 18, 4), WOOD, 2, y0, board=4, seed=seed)
    cv.hline(x0, y0, 18, WOOD[4]); cv.hline(x0, y0 + 3, 18, WOOD[1])
    if planting == 'flowers':
        blooms = (RED[3], GOLD[3], NAP[4], RED[4], PLASTER[5], NAP[3])
        for i, x in enumerate(range(x0 + 1, x0 + 17, 3)):
            cv.set(x, y0 - 1, LEAF[2]); cv.set(x + 1, y0 - 1, LEAF[3]); cv.set(x + 1, y0 - 2, LEAF[4])
            petal = blooms[(i + shift) % len(blooms)]
            cv.set(x, y0 - 3, petal); cv.set(x + 1, y0 - 3, petal); cv.set(x, y0 - 4, petal)
        return
    for i, x in enumerate(range(x0 + 1, x0 + 17, 3)):
        kind = (i + shift) % 3
        if kind == 0:  # basil: a round clump, lit on its upper left
            cv.set(x, y0 - 1, LEAF[2]); cv.set(x + 1, y0 - 1, LEAF[2])
            cv.set(x, y0 - 2, LEAF[4]); cv.set(x + 1, y0 - 2, LEAF[3]); cv.set(x, y0 - 3, LEAF[3])
        elif kind == 1:  # rosemary: dark needles, taller and thin
            cv.set(x, y0 - 1, LEAF[1]); cv.set(x, y0 - 2, LEAF[2]); cv.set(x + 1, y0 - 3, LEAF[2])
            cv.set(x, y0 - 4, LEAF[3]); cv.set(x, y0 - 5, LEAF[2])
        else:  # chives, flowering
            cv.set(x, y0 - 1, LEAF[2]); cv.set(x + 1, y0 - 1, LEAF[3]); cv.set(x, y0 - 2, LEAF[3])
            cv.set(x + 1, y0 - 3, LEAF[4]); cv.set(x + 1, y0 - 4, NAP[4]); cv.set(x, y0 - 4, NAP[3])


def hut(door: str = 'oak', sills: tuple = ('sill', 'flowers')) -> Canvas:
    """The nap hut in the steep top-down view (Matt's references, 17 Oct), 104 x 92: a
    slate roof seen from above whose ridge runs back from a timber front gable, the lit
    left plane and the shaded right plane, a stone chimney showing its cap, a painted
    front 44 px to the eaves with a recessed round-topped door 16 x 32 (the scale table,
    verticality.md 5: a 25 px adult walks through it), shuttered windows 16 tall, a
    lantern by the door, ivy on the lit corner and a fieldstone footing. The sprite keeps
    its 104 x 92 box and its foot: the walls grew into the roof's old depth. `door` is the door's paint (HUT_DOORS) and `sills` what sits
    under the left and the right window: a plain sill or a box of flowers or herbs."""
    w, h = 104, 92
    cv = Canvas(w, h, pad=PAD)
    paint, tone0 = HUT_DOORS[door]
    ridge = 51.5
    apex_y, eave_y = 16, 40  # the front gable's apex, and the eaves at the roof's front corners
    left_x, right_x = 5, 98  # the roof's side eaves (it overhangs the walls)
    wall_l, wall_r, wall_top, wall_bottom = 12, 91, 40, 84
    slope = (eave_y - apex_y) / (ridge - left_x)

    def edge_y(x):  # the bargeboards' line at column x
        return apex_y + abs(x + 0.5 - ridge) * slope

    def back_y(x):  # the roof's far edge: the ridge is highest, the back eaves lower
        return 1 + abs(x + 0.5 - ridge) * slope

    # the gable and the front wall first; the roof overhangs them
    gable = {(x, y) for x in range(wall_l, wall_r + 1) for y in range(apex_y, wall_top)
             if y > edge_y(x) + 2}
    detail.boards(cv, gable, WOOD, 2, apex_y, board=5, vertical=True, x0=12, joints=False, grain=0.05)
    for (x, y) in gable:  # shaded under the bargeboards
        if (x, y - 1) not in gable or (x, y - 2) not in gable:
            detail.shade(cv, x, y, 2 if (x, y - 1) not in gable else 1)
    for (x, y) in oval(ridge, 29, 5.5, 4.4):  # an oval vent in a lit frame, the crescent sign
        cv.set(x, y, WOOD[4] if x + 0.4 * y < ridge + 11.5 else WOOD[1])
    for (x, y) in oval(ridge, 29, 4.2, 3.2):
        cv.set(x, y, NAP[0])
    for (x, y) in disc(ridge - 0.7, 28.6, 2.2) - disc(ridge + 0.6, 28.0, 1.8):
        cv.set(x, y, GOLD[3])
    detail.boards(cv, rect_set(wall_l, wall_top, wall_r - wall_l + 1, wall_bottom - wall_top), PLASTER, 4,
                  wall_top, seed=4, joints=False)
    posts = set()
    for x0 in (wall_l, wall_r - 2):
        for y in range(apex_y + 10, wall_bottom):
            if (x0, y) in gable or y >= wall_top:
                cv.set(x0, y, WOOD[3]); cv.set(x0 + 1, y, WOOD[4]); cv.set(x0 + 2, y, WOOD[2] if x0 == wall_l else WOOD[1])
                posts |= {(x0, y), (x0 + 1, y), (x0 + 2, y)}
    # door: 16 x 32, round top, recessed in a stone arch
    dx0, dy0, dw, dh = 44, 52, 16, 32
    door = {(x, y) for (x, y) in disc(dx0 + dw / 2, dy0 + dw / 2, dw / 2) if y < dy0 + dh}
    door |= rect_set(dx0, dy0 + dw // 2, dw, dh - dw // 2)
    arch = set()
    for (x, y) in door:
        for ax, ay in ((-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1), (-2, 0), (2, 0), (0, -2), (-2, -1), (2, -1)):
            if (x + ax, y + ay) not in door and y + ay < dy0 + dh:
                arch.add((x + ax, y + ay))
    for (x, y) in arch:
        k = int(((x - dx0 - dw / 2) * 0.9 + (y - dy0) * 0.6) // 3)
        base = (3 if k % 2 else 2) - (1 if x > dx0 + dw / 2 + 1 else 0)
        cv.set(x, y, STONE[base])
    for (x, y) in arch:
        if (x - 1, y) not in arch and (x, y - 1) not in arch:
            cv.set(x, y, STONE[4])
    detail.boards(cv, door, paint, tone0, dy0, board=4, vertical=True, x0=dx0, joints=False, grain=0.06)
    for sy in (dy0 + 14, dy0 + 27):
        cv.hline(dx0 + 1, sy, 9, SLATE[1]); cv.hline(dx0 + 1, sy - 1, 9, SLATE[2])
        cv.set(dx0 + 3, sy - 1, SLATE[4]); cv.set(dx0 + 7, sy - 1, SLATE[4])
    for (x, y) in disc(dx0 + dw / 2, dy0 + 7, 2.8):
        cv.set(x, y, paint[1])
    for (x, y) in disc(dx0 + dw / 2, dy0 + 7, 1.9):
        cv.set(x, y, WTR[2])
    cv.set(dx0 + 7, dy0 + 6, WTR[4])
    detail.recess(cv, door, depth=2, k=1)
    cv.set(dx0 + 12, dy0 + 20, GOLD[4]); cv.set(dx0 + 12, dy0 + 21, GOLD[2]); cv.set(dx0 + 13, dy0 + 21, GOLD[1])
    WY, WH = 56, 16  # the windows' top and height
    proud = posts | arch | rect_set(16, WY, 4, WH) | rect_set(34, WY, 4, WH) | rect_set(66, WY, 4, WH)
    proud |= rect_set(84, WY, 4, WH)
    for wx, sill in zip((20, 70), sills):
        window(cv, wx, WY, 14, WH, sill=sill == 'sill')
        for (x, y) in rect_set(wx - 5, WY - 3, 24, 3):  # the head board over window and shutters
            cv.set(x, y, WOOD[4] if y == WY - 3 else WOOD[3] if y == WY - 2 else WOOD[1])
        proud |= rect_set(wx - 5, WY - 3, 24, 3)
        proud |= rect_set(wx - 1, WY + WH, 16, 2) if sill == 'sill' else rect_set(wx - 2, WY + WH, 18, 4)
    for i, (wx, sill) in enumerate(zip((20, 70), sills)):
        if sill != 'sill':
            window_box(cv, wx - 2, WY + WH, sill, seed=8 if i else 7, shift=0 if i else 3)
    # a lantern on a bracket right of the door, and a horseshoe over it for luck
    cv.hline(62, 54, 4, SLATE[1]); cv.set(65, 55, SLATE[1])
    cv.rect(64, 56, 3, 5, GOLD[3]); cv.set(64, 56, GOLD[4]); cv.hline(64, 55, 3, SLATE[2]); cv.hline(64, 61, 3, SLATE[1])
    proud |= rect_set(62, 54, 5, 8)
    for (x, y) in ((50, 48), (51, 47), (52, 47), (53, 47), (54, 48)):
        cv.set(x, y, SLATE[3] if x < 52 else SLATE[2])
    detail.cast(cv, proud, 1, 1, k=2, on=PLASTER, reach=2)
    for y in range(wall_top, wall_bottom):
        detail.shade(cv, wall_l + 3, y, 1); detail.shade(cv, wall_r - 3, y, 1)
    for x in range(wall_l, wall_r + 1):
        detail.shade(cv, x, wall_bottom - 1, 1)
    # the roof: two slate planes seen from above, the right one turned from the light;
    # the chimney's shadow falls on the right plane
    chim = rect_set(70, 10, 10, 14)

    def roof_shadow(x, y):
        return -1 if 80 <= x <= 84 and 12 <= y <= 28 else 0

    left = {(x, y) for x in range(left_x, int(ridge) + 1) for y in range(0, eave_y + 1)
            if back_y(x) <= y <= edge_y(x)}
    right = {(x, y) for x in range(int(ridge) + 1, right_x + 1) for y in range(0, eave_y + 1)
             if back_y(x) <= y <= edge_y(x)}
    detail.slate_plane(cv, left, NAP, 3, ridge, -1, seed=31, moss=LEAF, skew=slope)
    detail.slate_plane(cv, right - chim, NAP, 2, ridge, 1, seed=32, offset=roof_shadow, moss=LEAF, skew=slope)
    for y in range(0, apex_y + 2):  # the ridge cap: rounded capping tiles, lit on the left
        k = y % 4
        cv.set(49, y, NAP[1]); cv.set(50, y, NAP[4] if k else NAP[3]); cv.set(51, y, NAP[3] if k else NAP[2])
        cv.set(52, y, NAP[2] if k else NAP[1]); cv.set(53, y, NAP[0])
    for x in range(left_x, right_x + 1):  # the far edge shows the roof's thickness
        by = int(back_y(x))
        if (x, by) in left:
            cv.set(x, by, NAP[4])
        elif (x, by) in right:
            cv.set(x, by, NAP[3])
    for y in range(0, eave_y + 1):  # the side eaves
        if (left_x, y) in left:
            cv.set(left_x, y, NAP[4])
        if (right_x, y) in right:
            cv.set(right_x, y, NAP[1])
    # bargeboards: thick boards along the gable, a lit upper face over a dark underside
    for x in range(left_x - 1, right_x + 2):
        ey = int(edge_y(x))
        lit = x < ridge
        cv.set(x, ey, WOOD[4] if lit else WOOD[3]); cv.set(x, ey + 1, WOOD[3] if lit else WOOD[2])
        cv.set(x, ey + 2, WOOD[1])
    cv.vline(51, apex_y - 4, 4, WOOD[3]); cv.set(52, apex_y - 4, WOOD[2]); cv.set(51, apex_y - 5, WOOD[4])
    # the chimney: a cap seen from above, its stone face, standing on the right plane
    detail.stones(cv, 70, 14, 10, 10, STONE, seed=33, course=4)
    cv.vline(70, 14, 10, STONE[3]); cv.vline(79, 14, 10, STONE[1])
    cv.rect(69, 9, 12, 5, STONE[3]); cv.hline(69, 9, 12, STONE[4]); cv.vline(69, 9, 5, STONE[4])
    cv.rect(72, 10, 6, 3, NAP[0]); cv.hline(69, 13, 12, STONE[1])
    # eave shadows on the front: under the side eaves at the wall's top corners
    detail.overhang_shadow(cv, wall_l, wall_r + 1, wall_top,
                           lambda x: (4 if x < wall_l + 6 or x > wall_r - 6 else 2) + (x - wall_l) // 40, k=2, cap=1)
    # ivy on the lit corner, and the footing with a step and a mat
    for (ix, iy) in ((14, 46), (13, 50), (15, 54), (13, 58), (15, 62), (13, 66), (15, 70), (13, 74), (14, 78)):
        cv.vline(ix + 1, iy, 4, LEAF[1])
        cv.set(ix, iy, LEAF[4]); cv.set(ix + 1, iy, LEAF[3]); cv.set(ix, iy + 1, LEAF[3]); cv.set(ix + 2, iy + 2, LEAF[2])
    detail.stones(cv, 10, wall_bottom, 84, 6, STONE, seed=9, course=3, moss=LEAF)
    cv.rect(41, wall_bottom, 22, 3, STONE[3]); cv.hline(41, wall_bottom, 22, STONE[4]); cv.hline(41, wall_bottom + 2, 22, STONE[1])
    cv.rect(43, 89, 18, 3, NAP[2]); cv.hline(43, 89, 18, NAP[3]); cv.hline(43, 91, 18, NAP[1])
    for x in range(44, 60, 2):
        cv.set(x, 90, NAP[4])
    return cv


# ---- Moss's stall ----------------------------------------------------------
def awning(cv: Canvas, x0: int, w: int, y0: int, slope: int, valance: int, ramp_a, ramp_b, stripe: int = 8):
    """A striped canvas awning in the steep top-down view: the sloped top seen from above
    (`slope` rows from y0), each stripe sagging between ribs, lit on its left and along the
    back edge; then a valance of rounded folds (`valance` rows) with a scalloped hem. The
    two stripe colours are ramps."""
    for y in range(y0, y0 + slope + valance):
        for x in range(x0, x0 + w):
            f = (x - x0) % stripe
            ramp = ramp_a if ((x - x0) // stripe) % 2 == 0 else ramp_b
            top = len(ramp) - 1
            if y < y0 + slope:
                t = top if f in (1, 2) else top - 1 if f < stripe - 2 else top - 2
                if y > y0 + slope * 2 // 3:
                    t -= 1  # the slope turns slightly from the light toward its front
                if f == stripe - 1:
                    t = top - 3  # the rib between two stripes
            else:
                t = top - 1 if f in (1, 2) else top - 2 if f in (0, 3, 4) else top - 3
                if y > y0 + slope + valance - 3:
                    t -= 1
            cv.set(x, y, ramp[max(0, t)])
    for x in range(x0, x0 + w):
        a = ((x - x0) // stripe) % 2 == 0
        cv.set(x, y0, (ramp_a if a else ramp_b)[-1])
        cv.set(x, y0 + slope - 1, (ramp_a if a else ramp_b)[1])  # the eave's rolled edge
        f = (x - x0) % stripe
        ramp = ramp_a if a else ramp_b
        top = len(ramp) - 1
        hy = y0 + slope + valance
        if 1 <= f <= stripe - 2:
            cv.set(x, hy, ramp[top - 2] if f < stripe // 2 else ramp[top - 3])
        if 2 <= f <= stripe - 3:
            cv.set(x, hy + 1, ramp[top - 3])


def stall() -> Canvas:
    """Moss's hat stall at the scale table's size (verticality.md 5: 48 wide, the counter top
    13 above the ground, the canopy's top 40): a striped awning seen from above over a
    shaded recess with a shelf of hats, round posts lit from the left, a planked counter
    whose top shows its thickness with a ledger, a hat stand and a seedling on it, bolts of
    fabric and a crate at its foot and a little sign with a hat on the awning's ridge. It is
    re-seated in the old 88 x 72 box (keep_foot), so its foot stays where it was."""
    w, h = 48, 48
    cv = Canvas(w, h, pad=PAD)
    foot = h - 1
    ctop = foot - 13  # the counter's top
    # the recess under the awning: dark boards, darkest under the awning, and a shelf
    detail.boards(cv, rect_set(4, 22, 40, ctop - 22), WOOD, 1, 22, board=5, vertical=True, x0=4, joints=False)
    for x in range(4, 44):
        for y in range(22, 27):
            detail.shade(cv, x, y, 2 if y < 25 else 1)
    cv.hline(4, 29, 40, WOOD[3]); cv.hline(4, 30, 40, WOOD[1])  # the shelf, lit along its edge
    # on the shelf: a cap, a top hat, a straw hat
    for (x, y) in oval(11, 28, 4, 1.6) | rect_set(8, 25, 6, 3):
        cv.set(x, y, WTR[2] if y < 27 else WTR[1])
    cv.hline(8, 25, 5, WTR[3]); cv.hline(9, 29, 6, WTR[0])
    for y in range(23, 29):
        cv.hline(20, y, 5, STONE[1] if y < 28 else STONE[0])
    cv.vline(20, 23, 5, STONE[2]); cv.hline(20, 27, 5, RED[2]); cv.hline(18, 28, 9, STONE[0])
    for (x, y) in oval(33, 28, 5, 1.6):
        cv.set(x, y, SAND[2] if y < 28 else SAND[1])
    for (x, y) in oval(33, 26.5, 2.5, 1.8):
        cv.set(x, y, SAND[2] if x < 33 else SAND[1])
    cv.hline(31, 27, 5, RED[3])
    # posts: round, lit from the left, standing in front of the recess
    posts = set()
    for x in (1, 44):
        for y in range(18, foot):
            cv.set(x, y, WOOD[3]); cv.set(x + 1, y, WOOD[4]); cv.set(x + 2, y, WOOD[1])
            posts |= {(x + i, y) for i in range(3)}
    detail.cast(cv, posts, 1, 1, k=1, on=WOOD, reach=2)
    # counter: a lit top that shows its thickness, a planked front shaded under the lip
    cv.rect(0, ctop, 48, 2, WOOD[4]); cv.hline(0, ctop + 2, 48, WOOD[2])
    cv.set(0, ctop, WOOD[3])
    detail.boards(cv, rect_set(1, ctop + 3, 46, foot - ctop - 3), WOOD, 2, ctop + 3, board=6, vertical=True, x0=1,
                  grain=0.06, joints=False)
    for x in range(1, 47):
        detail.shade(cv, x, ctop + 3, 2); detail.shade(cv, x, ctop + 4, 1)
        if x % 6 == 2 and x < 44:
            cv.set(x, ctop + 4, SLATE[1])  # nail heads along the top board
    cv.hline(1, foot, 46, WOOD[0]); cv.hline(1, foot - 1, 46, WOOD[1])
    # on the counter: a ledger, a hat on a stand, a seedling
    cv.rect(28, ctop - 2, 8, 2, NAP[1]); cv.hline(29, ctop - 2, 6, CREAM[3]); cv.set(32, ctop - 2, CREAM[1])
    cv.vline(15, ctop - 5, 5, WOOD[2]); cv.hline(13, ctop - 1, 5, WOOD[1])
    for (x, y) in oval(15, ctop - 6, 4, 1.5):
        cv.set(x, y, NAP[3] if x < 15 else NAP[2])
    cv.rect(14, ctop - 9, 3, 3, NAP[3]); cv.set(14, ctop - 9, NAP[4]); cv.hline(14, ctop - 7, 3, GOLD[3])
    cv.rect(40, ctop - 4, 4, 4, RED[2]); cv.hline(40, ctop - 4, 4, RED[3]); cv.set(43, ctop - 3, RED[1])
    cv.set(41, ctop - 6, LEAF[3]); cv.set(42, ctop - 7, LEAF[4]); cv.set(40, ctop - 5, LEAF[2]); cv.set(43, ctop - 5, LEAF[2])
    # bolts of fabric leaning at the counter's foot
    for (bx, ramp) in ((4, NAP), (12, WTR)):
        cv.rect(bx, foot - 4, 7, 4, ramp[2]); cv.hline(bx, foot - 4, 7, ramp[4]); cv.hline(bx, foot - 3, 7, ramp[3])
        cv.hline(bx, foot - 1, 7, ramp[1]); cv.vline(bx, foot - 4, 4, ramp[1])
    awning(cv, -1, 50, 7, 11, 4, LEAF, PLASTER)
    # a little sign on the awning's ridge, with a hat painted on it
    cv.rect(16, 0, 16, 6, WOOD[3]); cv.hline(16, 0, 16, WOOD[4]); cv.hline(16, 5, 16, WOOD[1])
    cv.vline(16, 0, 6, WOOD[4]); cv.vline(31, 1, 5, WOOD[2])
    cv.rect(21, 1, 6, 2, NAP[3]); cv.hline(19, 3, 10, NAP[1]); cv.hline(21, 1, 6, NAP[4])
    cv.vline(18, 6, 2, WOOD[1]); cv.vline(29, 6, 2, WOOD[1])
    return keep_foot(cv, 88, 72)


# ---- trees -------------------------------------------------------------------
def tree(big: bool = True, autumn: bool = False) -> Canvas:
    """A round broadleaf: 64 x 88 (or 48 x 64), a canopy of a few big leaf masses over
    a flared trunk."""
    w, h = (64, 88) if big else (48, 64)
    cv = Canvas(w, h, pad=PAD)
    ramp = AUTUMN if autumn else LEAF
    cx = w / 2
    tw = 10 if big else 7
    tx = int(cx - tw / 2)
    trunk_top = h - (34 if big else 24)
    style.trunk(cv, tx, trunk_top - 6, h, tw, WOOD)
    k = 1.0 if big else 0.74
    lobes = [(cx + 11 * k, 20 * k, 15 * k), (cx - 12 * k, 22 * k, 15 * k), (cx + 2 * k, 13 * k, 15 * k),
             (cx - 9 * k, 36 * k, 14 * k), (cx + 10 * k, 37 * k, 14 * k), (cx, 30 * k, 14 * k)]
    shape = canopy(cv, lobes, ramp, seed=9 if autumn else 2 + big, clumps=True)
    style.trunk(cv, tx, trunk_top, h, tw, WOOD, shape)
    if not autumn and big:  # ripe apples on the lit side
        for fx, fy in ((cx - 18, 18), (cx + 6, 9), (cx - 8, 31), (cx + 16, 27), (cx - 3, 18)):
            fx, fy = int(fx), int(fy)
            cv.rect(fx, fy, 3, 3, RED[2]); cv.set(fx, fy, RED[4]); cv.set(fx + 1, fy, RED[3])
            cv.set(fx + 2, fy + 2, RED[1]); cv.set(fx + 1, fy - 1, LEAF[1])
    if autumn:  # the copper tree keeps its weathered birdhouse, nailed to the trunk
        bx, by = tx - 2, h - 30
        plane(cv, rect_set(bx, by + 4, 13, 11), WOOD, 3)
        for i in range(8):
            cv.hline(bx - 1 + i, by + 4 - i // 2 - 1, 15 - 2 * i, NAP[2] if i else NAP[1])
        for i in range(0, 8, 2):
            cv.hline(bx - 1 + i, by + 4 - i // 2 - 1, 2, NAP[3])
        for (x, y) in disc(bx + 6.5, by + 9, 2.2):
            cv.set(x, y, WOOD[0])
        cv.hline(bx + 4, by + 13, 6, WOOD[1]); cv.set(bx + 4, by + 12, WOOD[4])
    return cv


def pine() -> Canvas:
    """A tiered conifer, 36 x 76: cone-shaded tiers with light clumps on the lit flank."""
    w, h = 36, 76
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2 - 0.5
    style.trunk(cv, int(cx) - 2, h - 16, h, 5, WOOD)
    tiers = ((1, 14, 6.0), (10, 16, 9.5), (20, 17, 12.5), (31, 17, 15.0), (42, 18, 17.0))
    for t, (ty, th, half) in enumerate(tiers):
        tier = {}
        for y in range(ty, ty + th):
            frac = (y - ty + 1) / th
            span = half * (0.28 + 0.72 * frac)
            for x in range(int(cx - span), int(cx + span) + 2):
                if not (0 <= x < w):
                    continue
                if y == ty + th - 1 and (x + t) % 4 == 0:
                    continue  # sawtooth hem
                side = (x + 0.5 - cx) / max(1.0, span)
                lv = -0.8 * side - 0.5 * (frac - 0.4)
                tier[(x, y)] = 3 if lv > 0.45 else 2 if lv > -0.05 else 1 if lv > -0.6 else 0
        for (x, y), tone in tier.items():
            cv.set(x, y, PINE[tone])
        for (x, y), tone in tier.items():
            if (x, y + 1) not in tier:
                cv.set(x, y, PINE[max(0, tone - 1)])
        for k in range(3 + t):
            yy = ty + 3 + int(noise2(k, t, 61) * max(1, th - 6))
            span = half * (0.28 + 0.72 * (yy - ty + 1) / th)
            xx = int(cx - span * (0.2 + 0.6 * noise2(k, t, 62)))
            if (xx, yy) in tier and (xx + 3, yy) in tier and tier[(xx, yy)] >= 2:
                cv.hline(xx, yy, 3, PINE[4])
                cv.set(xx + 3, yy, PINE[3])
                cv.hline(xx, yy + 1, 4, PINE[1])
    cv.set(int(cx), 0, PINE[3])
    return cv


def bush() -> Canvas:
    """A round shrub, 32 x 24, below companion height; stems peek out underneath."""
    w, h = 32, 24
    cv = Canvas(w, h, pad=PAD)
    for x in (9, 14, 19):
        cv.rect(x, h - 4, 3, 3, WOOD[1]); cv.set(x, h - 4, WOOD[2])
    canopy(cv, [(10, 10, 8), (22, 10, 8), (16, 8, 8), (16, 13, 7.5)], LEAF, seed=5)
    for x, y in ((9, 6), (18, 4), (13, 12)):
        cv.set(x, y, CREAM[3]); cv.set(x + 1, y + 1, GOLD[3])
    return cv


def rock(n: int) -> Canvas:
    """A field stone, 20 x 14: faceted planes, moss on the second one."""
    cv = Canvas(20, 14, pad=PAD)
    pts = {(x, y) for (x, y) in (oval(10.5, 7.5, 8.6, 5.6) | oval(7, 8.5, 5.6, 4.6))
           if 0 <= x < 20 and 0 <= y < 14}
    style.facet_stone(cv, pts, STONE, moss=LEAF if n else None, seed=n + 2, outline=None)
    return cv


# ---- small props -------------------------------------------------------------
def post(cv: Canvas, x: int, y0: int, y1: int, w: int = 3, ramp=WOOD, cap: bool = True):
    """A round post: a lit stripe left of centre, the far side dark, a lit cap on top."""
    for y in range(y0, y1):
        for i in range(w):
            t = 3 if i == 0 else 4 if i == 1 else 2 if i < w - 1 else 1
            cv.set(x + i, y, ramp[t])
    if cap:
        cv.hline(x, y0, w, ramp[4]); cv.set(x + w - 1, y0, ramp[3])


def reading_nook() -> Canvas:
    """The reading bench, 44 x 28: slats that show their lit tops and darker fronts, the
    backrest's shadow across the seat, a plump cushion, books and a warm mug."""
    w, h = 44, 28
    cv = Canvas(w, h, pad=PAD)
    for x in (3, 38):
        post(cv, x, 1, 19)
    for y in (2, 6, 10):  # backrest slats: a lit top, a face, a dark underside
        cv.hline(2, y, 40, WOOD[4]); cv.hline(2, y + 1, 40, WOOD[3]); cv.hline(2, y + 2, 40, WOOD[1])
        cv.set(2, y, WOOD[3])
    # seat: three planks seen from above, then its front edge and the legs
    for y in range(13, 19):
        for x in range(1, 43):
            r = (y - 13) % 2
            cv.set(x, y, WOOD[4] if r == 0 and y < 17 else WOOD[3] if r == 0 else WOOD[2])
    for x in range(1, 43):
        detail.shade(cv, x, 13, 1); detail.shade(cv, x + 1, 14, 1)  # the backrest's shadow
    cv.hline(1, 19, 42, WOOD[2]); cv.hline(1, 20, 42, WOOD[0])
    for x in (3, 37):
        post(cv, x, 21, 28, w=4, cap=False)
        cv.hline(x, 21, 4, WOOD[1])  # shaded under the seat
    # cushion: puffed, lit on its upper left, with a button
    for (x, y) in oval(15, 14, 9, 3.2):
        nx, ny = (x + 0.5 - 15) / 9, (y + 0.5 - 14) / 3.2
        lit = -0.6 * nx - 0.8 * ny
        cv.set(x, y, NAP[4] if lit > 0.5 else NAP[3] if lit > -0.3 else NAP[2])
    cv.set(15, 14, NAP[1]); cv.set(14, 13, NAP[4])
    for x in range(7, 24):
        detail.shade(cv, x, 17, 1)  # the cushion's shadow on the seat
    # two books (spines, page edges) and a mug with a curl of steam
    cv.rect(27, 13, 10, 3, RED[2]); cv.hline(27, 13, 10, RED[3]); cv.vline(27, 13, 3, RED[4])
    cv.hline(28, 14, 8, PLASTER[5]); cv.hline(28, 15, 8, RED[1])
    cv.rect(28, 10, 9, 3, WTR[2]); cv.hline(28, 10, 9, WTR[3]); cv.vline(28, 10, 3, WTR[4])
    cv.hline(29, 11, 7, PLASTER[5]); cv.hline(29, 12, 7, WTR[1])
    cv.rect(32, 5, 4, 5, PLASTER[4]); cv.vline(32, 5, 5, PLASTER[5]); cv.vline(35, 5, 5, PLASTER[2])
    cv.hline(32, 5, 4, PLASTER[3]); cv.hline(33, 5, 2, WOOD[1])
    cv.set(36, 6, PLASTER[3]); cv.set(37, 7, PLASTER[2]); cv.set(36, 8, PLASTER[2])
    cv.set(33, 3, PLASTER[5]); cv.set(34, 2, PLASTER[4]); cv.set(33, 1, PLASTER[5])
    return cv


def lantern() -> Canvas:
    """A leaf lantern on a bent post, 14 x 40: taller than the companion."""
    w, h = 14, 40
    cv = Canvas(w, h, pad=PAD)
    post(cv, 2, 6, 39)
    cv.hline(1, 39, 5, WOOD[1])
    detail.base_tufts(cv, (1, 5), 39, G)
    cv.hline(3, 5, 7, WOOD[4]); cv.hline(3, 6, 7, WOOD[2]); cv.hline(3, 7, 7, WOOD[1]); cv.vline(9, 7, 3, WOOD[2])
    # glass housing with a warm glow: brightest at the flame, darker toward the frame
    cv.rect(6, 10, 7, 12, WOOD[1]); cv.vline(6, 10, 12, WOOD[2])
    for (x, y) in rect_set(7, 11, 5, 10):
        d = abs(x - 9) + abs(y - 16) * 0.6
        cv.set(x, y, GOLD[4] if d < 1.5 else GOLD[3] if d < 3.2 else GOLD[2])
    cv.vline(7, 11, 9, GOLD[4]); cv.set(9, 16, PLASTER[5])
    cv.vline(9, 11, 10, WOOD[1])  # the glazing bar
    cv.hline(5, 9, 9, LEAF[2]); cv.hline(6, 8, 7, LEAF[3]); cv.hline(7, 7, 5, LEAF[4]); cv.set(5, 9, LEAF[3])
    cv.hline(6, 22, 7, WOOD[3]); cv.hline(7, 23, 5, WOOD[1])
    cv.set(1, 30, LEAF[2]); cv.set(0, 29, LEAF[3]); cv.set(5, 33, LEAF[2]); cv.set(6, 32, LEAF[3])
    return cv


def mailbox() -> Canvas:
    """A red mailbox on a post, 18 x 32: a rounded tin box lit along its left, a door
    in a frame, the flag up and a postcard peeking out."""
    w, h = 18, 32
    cv = Canvas(w, h, pad=PAD)
    post(cv, 7, 15, 31, w=4)
    cv.hline(5, 31, 8, WOOD[1])
    detail.base_tufts(cv, (5, 9, 12), 31, G)
    body = rect_set(1, 4, 15, 12) | rect_set(2, 2, 13, 2) | rect_set(3, 1, 11, 1)
    for (x, y) in body:
        t = 4 if x in (2, 3) else 3 if x < 9 else 2 if x < 14 else 1
        if y >= 14:
            t -= 1
        cv.set(x, y, RED[max(0, t)])
    cv.hline(3, 1, 11, RED[4]); cv.hline(2, 2, 3, RED[4])
    cv.hline(1, 8, 15, RED[1]); cv.hline(1, 9, 15, RED[3])  # the lid's seam
    cv.rect(4, 11, 9, 3, PLASTER[4]); cv.hline(4, 11, 9, PLASTER[5]); cv.hline(4, 13, 9, PLASTER[2])
    cv.set(7, 12, RED[2]); cv.set(8, 12, NAP[3])
    cv.vline(16, 3, 8, GOLD[2]); cv.rect(16, 2, 2, 3, GOLD[3]); cv.set(16, 2, GOLD[4])
    detail.cast(cv, rect_set(1, 4, 15, 12), 1, 1, k=1, on=WOOD, reach=2)
    return cv


def arrow_board(cv: Canvas, y: int, left: bool):
    """A plank arrow: lit top edge, grain, a darker bottom edge showing its thickness,
    nail heads, and its shadow on the post below."""
    board = rect_set(3, y, 22, 8)
    tip = [(25, y + 1), (25, y + 2), (25, y + 3), (25, y + 4), (25, y + 5), (25, y + 6),
           (26, y + 2), (26, y + 3), (26, y + 4), (26, y + 5), (27, y + 3), (27, y + 4)]
    if left:
        tip = [(27 - x, yy) for (x, yy) in tip]
    board |= set(tip)
    detail.boards(cv, board, WOOD, 3, y, board=4, seed=y, joints=False, grain=0.08)
    for (x, yy) in board:
        if (x, yy - 1) not in board:
            cv.set(x, yy, WOOD[4])
        elif (x, yy + 1) not in board:
            cv.set(x, yy, WOOD[1])
    cv.hline(8, y + 3, 5, WOOD[1]); cv.hline(14, y + 3, 4, WOOD[1]); cv.hline(8, y + 5, 8, WOOD[1])
    nx = 5 if not left else 22
    cv.set(nx, y + 2, STONE[4]); cv.set(nx, y + 3, STONE[1])


def signpost() -> Canvas:
    """Two arrow boards on a post, 28 x 36: to the missions and back home."""
    w, h = 28, 36
    cv = Canvas(w, h, pad=PAD)
    post(cv, 12, 6, 35, w=4)
    cv.hline(10, 35, 8, WOOD[1])
    detail.base_tufts(cv, (10, 15, 18), 35, G)
    for (y, left) in ((2, False), (14, True)):
        arrow_board(cv, y, left)
        cv.hline(12, y + 8, 4, WOOD[0]); cv.hline(13, y + 9, 3, WOOD[1])  # its shadow on the post
    return cv


def watering_can() -> Canvas:
    """A painted watering can, 18 x 14."""
    w, h = 18, 14
    cv = Canvas(w, h, pad=PAD)
    body = rect_set(3, 5, 9, 8) | rect_set(4, 4, 7, 1)
    plane(cv, body, WTR, 3)
    for i in range(5):
        cv.set(12 + i, 7 - i // 2, WTR[2]); cv.set(12 + i, 8 - i // 2, WTR[1])
    cv.rect(16, 3, 2, 3, WTR[3]); cv.set(17, 3, WTR[4])
    for (x, y) in ((4, 3), (5, 2), (6, 1), (7, 1), (8, 1), (9, 2), (10, 3)):
        cv.set(x, y, STONE[2])
    cv.hline(4, 9, 7, WTR[4])
    return cv


def bowl() -> Canvas:
    """The food bowl, 18 x 10, seen from above and in front: a lit rim around a heap of
    seeds, the inside of the far wall in shadow, and the outer wall turning darker below."""
    w, h = 18, 10
    cv = Canvas(w, h, pad=PAD)
    outer = oval(9, 5.5, 8.5, 4.4)
    for (x, y) in outer:  # the outer wall: lit on the left, darker toward the bottom right
        t = 3 if x < 6 else 2 if x < 13 else 1
        if y >= 8:
            t -= 1
        cv.set(x, y, RED[max(0, t)])
    rim = oval(9, 4.2, 8.2, 3.2)
    for (x, y) in rim:
        cv.set(x, y, RED[4] if x < 9 else RED[3])
    inner = oval(9, 4.4, 6.6, 2.3)
    for (x, y) in inner:
        cv.set(x, y, RED[1] if (x, y - 1) not in inner else GOLD[2])
    for (x, y) in oval(9, 4.8, 5.4, 1.8):  # the heap of seeds, lit on its upper left
        cv.set(x, y, GOLD[4] if x < 8 and y < 5 else GOLD[3] if (x * 3 + y) % 4 else GOLD[2])
    cv.set(6, 4, GOLD[4]); cv.set(10, 4, GOLD[4]); cv.set(12, 5, GOLD[1])
    return cv


def bed() -> Canvas:
    """The nap cushion by the hut, 30 x 16: a raised lavender rim around a soft well,
    a cream pillow and a folded blanket."""
    w, h = 30, 16
    cv = Canvas(w, h, pad=PAD)
    rim = oval(15, 8.5, 14.5, 7.4)
    well = oval(15, 8.2, 11.0, 4.6)
    for (x, y) in rim:
        nx = (x + 0.5 - 15) / 14.5
        ny = (y + 0.5 - 8.5) / 7.4
        cv.set(x, y, NAP[4] if -0.6 * nx - 0.8 * ny > 0.55 else NAP[3] if ny < 0.45 else NAP[2])
    for (x, y) in well:
        cv.set(x, y, NAP[1] if y < 7 else NAP[2])
    plane(cv, oval(9, 8.4, 4.2, 2.6), CREAM, 2)
    plane(cv, rect_set(15, 7, 10, 5), CREAM, 2)
    cv.hline(15, 9, 10, NAP[3]); cv.hline(15, 10, 10, NAP[3])
    cv.rect(19, 7, 3, 2, RED[4])  # a mended patch
    return cv


def meadow_sign() -> Canvas:
    """The meadow's hand-painted sign, 22 x 28."""
    w, h = 22, 28
    cv = Canvas(w, h, pad=PAD)
    post(cv, 9, 12, 27, w=4)
    cv.hline(7, 27, 8, WOOD[1])
    detail.base_tufts(cv, (7, 12, 15), 27, G)
    board = rect_set(1, 2, 20, 11)
    detail.boards(cv, board, WOOD, 3, 2, board=4, seed=5, joints=False, grain=0.06)
    cv.hline(1, 2, 20, WOOD[4]); cv.vline(1, 2, 11, WOOD[4]); cv.hline(1, 12, 20, WOOD[1]); cv.vline(20, 3, 10, WOOD[2])
    cv.vline(5, 5, 6, LEAF[2]); cv.set(4, 6, LEAF[3]); cv.set(6, 7, LEAF[3]); cv.set(4, 9, LEAF[4])
    cv.set(5, 4, RED[3]); cv.set(4, 4, RED[4]); cv.set(6, 4, RED[3]); cv.set(5, 3, RED[4])
    cv.hline(9, 5, 9, WOOD[1]); cv.hline(9, 8, 7, WOOD[1])
    cv.hline(9, 13, 4, WOOD[0]); cv.hline(10, 14, 3, WOOD[1])
    return cv


def fence_h(length: int, strainer: str | None = None) -> Canvas:
    """A post-and-rail fence segment, 18 tall: round posts lit on the left with cut tops,
    every 10 pixels, two rails that show a lit top and a dark underside with grain, a
    knot now and then and a nail head where each rail meets a post, the rails' shadows on
    the posts, lichen low on a few posts and bindweed climbing two of them. `strainer`
    ('w' or 'e') ends the run at that end on a stout strainer post with a diagonal brace,
    so a fence never just stops in the grass (Matt, 19 Oct 22:40, B9; world-references 3)."""
    h = 18
    cv = Canvas(length, h, pad=PAD)
    for ry in (5, 11):
        for x in range(length):
            sag = 1 if 0.3 < noise2(x // 10, ry, 931) < 0.4 and x % 10 in (4, 5, 6) else 0
            cv.set(x, ry + sag, WOOD[4]); cv.set(x, ry + 1 + sag, WOOD[3]); cv.set(x, ry + 2 + sag, WOOD[1])
            if noise2(x // 3, ry, 932) > 0.78:
                cv.set(x, ry + 1 + sag, WOOD[2])  # grain
        for x in range(6, length, 23):
            cv.set(x, ry + 1, WOOD[1]); cv.set(x + 1, ry + 1, WOOD[2])  # a knot
    posts = list(range(1, length - 4, 10))
    if strainer == 'e':
        posts = [p for p in posts if p < length - 12]
    if strainer == 'w':
        posts = [p for p in posts if p > 8]
    for x in posts:
        for y in range(1, 17):
            for i in range(5):
                t = 3 if i == 0 else 4 if i == 1 else 3 if i == 2 else 2 if i == 3 else 1
                if i == 2 and noise2(x, y // 3, 933) > 0.8:
                    t = 2  # a split in the post
                cv.set(x + i, y, WOOD[t])
        cv.hline(x, 1, 5, WOOD[4]); cv.set(x + 4, 1, WOOD[3]); cv.hline(x + 1, 2, 3, WOOD[2])  # cut top
        for ry in (8, 14):
            cv.hline(x + 1, ry, 4, WOOD[1])  # the rail's shadow on the post
        for ry in (6, 12):
            cv.set(x + 2, ry, SLATE[1])  # the nail head
        cv.hline(x, 16, 5, WOOD[1])
        if noise2(x, 7, 934) > 0.6:
            cv.set(x + 1, 14, LICHEN_G); cv.set(x + 2, 15, LICHEN_G)  # lichen low on the post
    if strainer:  # the stout end post, taller than the rest, braced back to its neighbour
        sx = length - 7 if strainer == 'e' else 0
        for y in range(-2, 17):
            for i in range(7):
                t = 3 if i == 0 else 4 if i in (1, 2) else 3 if i == 3 else 2 if i < 6 else 1
                cv.set(sx + i, y, WOOD[t])
        cv.hline(sx, -2, 7, WOOD[4]); cv.hline(sx + 1, -1, 5, WOOD[2]); cv.set(sx + 6, -2, WOOD[3])
        for y in range(2, 16, 4):
            cv.set(sx + 4, y, WOOD[2])  # its grain
        cv.hline(sx, 16, 7, WOOD[1])
        for ry in (6, 12):
            cv.set(sx + 3, ry, SLATE[1])
        for k in range(10):
            bx = sx - 1 - k if strainer == 'e' else sx + 7 + k
            by = 2 + int(k * 1.3)
            cv.set(bx, by, WOOD[4]); cv.set(bx, by + 1, WOOD[2])
        cv.set(sx + 1, 15, LICHEN_G); cv.set(sx + 2, 14, LEAF[2])
    for x in (16, length - 24):
        cv.vline(x, 7, 9, LEAF[1])
        for dx, y in ((-1, 8), (1, 10), (-1, 12), (1, 14)):
            cv.hline(x + dx, y, 2, LEAF[2]); cv.set(x + dx, y - 1, LEAF[3])
        cv.set(x + 1, 6, NAP[4])
    return cv


LICHEN_G = '#9EA86A'  # grey-green lichen on old timber


def gate() -> Canvas:
    """The garden gate, 48 x 44: fieldstone pillars with capstones that show their tops,
    an arched beam with a lit upper face, and the arena's pennant in soft folds."""
    w, h = 48, 44
    cv = Canvas(w, h, pad=PAD)
    for x in (2, 39):
        detail.stones(cv, x, 11, 7, 32, STONE, seed=x, course=4)
        detail.shade_set(cv, {(xx, yy) for xx in (x + 5,) for yy in range(11, 43)}, 1)
        cv.vline(x, 11, 32, STONE[3]); cv.vline(x + 6, 11, 32, STONE[1])
        cv.rect(x - 1, 6, 9, 5, STONE[3])
        cv.hline(x - 1, 6, 9, STONE[4]); cv.hline(x - 1, 7, 9, STONE[4]); cv.set(x + 7, 7, STONE[3])
        cv.hline(x - 1, 9, 9, STONE[2]); cv.hline(x - 1, 10, 9, STONE[1])
        cv.hline(x, 11, 7, STONE[0])  # the capstone's shadow on the pillar
    for x in range(6, 42):
        y = 3 + int(((x - 23.5) / 18) ** 2 * 5)
        cv.set(x, y, WOOD[4]); cv.set(x, y + 1, WOOD[4] if x < 24 else WOOD[3]); cv.set(x, y + 2, WOOD[2]); cv.set(x, y + 3, WOOD[1])
    pennant = rect_set(18, 8, 12, 12) | {(x, y) for y in range(20, 24) for x in range(18 + (y - 20) * 2 - 1, 30 - (y - 20) * 2 + 1) if 18 <= x < 30}
    for (x, y) in pennant:
        f = (x - 18) % 6
        t = 3 if f in (1, 2) else 2 if f in (0, 3) else 1
        cv.set(x, y, RED[t])
    cv.hline(18, 8, 12, RED[4])
    for i in range(6):
        cv.set(21 + i, 11 + i, PLASTER[5]); cv.set(26 - i, 11 + i, PLASTER[4])
    cv.vline(23, 6, 3, WOOD[1]); cv.vline(24, 6, 3, WOOD[1])
    return cv


def frog() -> Canvas:
    """The pond's shy resident, 12 x 9."""
    cv = Canvas(12, 9, pad=PAD)
    for (x, y) in oval(6, 5.5, 5.4, 3.2):
        cv.set(x, y, LEAF[3] if y < 5 else LEAF[2])
    for ex in (3, 8):
        for (x, y) in disc(ex + 0.5, 2.5, 1.6):
            cv.set(x, y, LEAF[3])
        cv.set(ex, 2, CREAM[3]); cv.set(ex + 1, 2, STONE[0])
    cv.hline(4, 6, 4, LEAF[1]); cv.set(1, 7, LEAF[2]); cv.set(10, 7, LEAF[2])
    return cv


def bridge(w: int, h: int) -> Canvas:
    """The bridge deck (a flat decal) at Eastward's detail (world-references: uneven
    planks, a lit deck edge and a dark front, posts set in the water): planks across the
    stream of slightly different lengths whose ends stick out past the stringers, each
    with a lit leading edge, grain, a knot now and then and two nail heads, a paler worn
    track down the middle where feet go, dark gaps between; handrails on capped posts
    that show their lit tops and darker inner faces, moss where the rails meet the posts;
    and the deck's thickness at its southern end, where it rests on the bank."""
    cv = Canvas(w, h, pad=PAD)
    for py in range(0, h - 4, 4):  # the planks, their ends ragged past the rails
        pi = py // 4
        ext_l = int(noise2(pi, 3, 43) * 3)
        ext_r = int(noise2(pi, 4, 43) * 3)
        for x in range(3 - ext_l, w - 3 + ext_r):
            for r in range(4):
                y = 2 + py + r
                if y >= h - 2:
                    continue
                t = 2 + (1 if noise2(pi, 1, 41) > 0.8 else -1 if noise2(pi, 2, 41) < 0.15 else 0)
                if r == 3:
                    t = 0  # the gap between planks
                elif r == 0:
                    t += 1
                elif noise2(x // 4, y, 42) < 0.08:
                    t -= 1  # grain
                if r in (1, 2) and abs(x - w / 2) < 9 + noise2(pi, 5, 43) * 3:
                    t += 1  # the worn track down the middle
                cv.set(x, y, WOOD[max(0, min(4, t))])
        for nx in (7, w - 8):
            cv.set(nx, 3 + py, STONE[4]); cv.set(nx, 4 + py, WOOD[1])  # nail heads over the stringers
        if noise2(pi, 6, 43) > 0.75:
            kx = 12 + int(noise2(pi, 7, 43) * (w - 24))
            cv.set(kx, 3 + py, WOOD[1]); cv.set(kx + 1, 3 + py, WOOD[2])  # a knot
    for x in range(3, w - 3):
        cv.set(x, h - 2, WOOD[1]); cv.set(x, h - 1, WOOD[0])  # the deck's southern edge, its thickness
    for x0, lit in ((1, True), (w - 5, False)):  # handrails along both sides
        for y in range(0, h):
            cv.set(x0, y, WOOD[3] if lit else WOOD[2]); cv.set(x0 + 1, y, WOOD[4] if lit else WOOD[3])
            cv.set(x0 + 2, y, WOOD[3] if lit else WOOD[2]); cv.set(x0 + 3, y, WOOD[1])
            if noise2(x0, y // 3, 44) > 0.85:
                cv.set(x0 + 2, y, WOOD[1])  # a crack along the rail
        for py in (0, h // 2 - 2, h - 4):
            cv.rect(x0 - 1, py, 6, 4, WOOD[3]); cv.hline(x0 - 1, py, 6, WOOD[4]); cv.hline(x0 - 1, py + 1, 6, WOOD[4])
            cv.set(x0 + 4, py, WOOD[3]); cv.hline(x0 - 1, py + 3, 6, WOOD[1])
            cv.set(x0 - 1, py + 4, LEAF[2]); cv.set(x0, py + 4, LEAF[3])  # moss where the rail meets the post
    for y in range(2, h - 2):  # the rails' shadow on the deck
        detail.shade(cv, 5, y, 1); detail.shade(cv, w - 6, y, 1)
    return cv


# ---- clutter: small things that sit against walls (Matt's references) -------
def crate() -> Canvas:
    """A wooden crate at the scale table's size (verticality.md 5: 11 tall, 12 wide), seen
    steeply from above: a lid of three boards lit from the upper left, a front face of
    planks with grain between corner battens, nail heads, and the right side turned from
    the light. Re-seated in the old 16 x 16 box (keep_foot)."""
    cv = Canvas(12, 11, pad=PAD)
    for y in range(0, 4):  # the lid, seen from above: three boards with gaps
        for x in range(12):
            cv.set(x, y, WOOD[4] if y == 0 else WOOD[3] if y != 2 else WOOD[2])
    cv.set(3, 1, WOOD[2]); cv.set(8, 3, WOOD[2])  # grain on the lid
    for y in range(4, 11):  # the front face: two planks
        for x in range(12):
            cv.set(x, y, WOOD[2] if y < 7 or y > 7 else WOOD[1])
    cv.hline(0, 4, 12, WOOD[1])  # the lid's shadow line
    for x in (0, 1):
        cv.vline(x, 4, 7, WOOD[3] if x == 0 else WOOD[2])  # the lit corner batten
    for x in (10, 11):
        cv.vline(x, 4, 7, WOOD[1] if x == 10 else WOOD[0])  # the batten turned from the light
    cv.set(5, 5, WOOD[1]); cv.set(6, 5, WOOD[1]); cv.set(7, 9, WOOD[3])  # grain
    for (x, y) in ((1, 5), (1, 9), (10, 5), (10, 9), (1, 1), (10, 1)):
        cv.set(x, y, SLATE[1])  # nail heads
    cv.hline(0, 10, 12, WOOD[0])
    return keep_foot(cv, 16, 17)


def barrel() -> Canvas:
    """A barrel at the scale table's size (verticality.md 5: 14 tall, 11 wide): a lid of
    boards seen from above inside its rim, bellied staves lit on the left with their
    joints, two iron hoops that catch the light, a darker bottom chime. Re-seated in the
    old 14 x 18 box (keep_foot)."""
    cv = Canvas(11, 14, pad=PAD)
    body = {(x, y) for y in range(3, 14) for x in range(11)
            if abs(x + 0.5 - 5.5) <= 5 + (0.5 if 5 <= y <= 10 else 0)}
    for (x, y) in body:
        t = 3 if x < 3 else 4 if x == 3 else 2 if x < 8 else 1
        if x % 3 == 1:
            t -= 1  # the joints between staves
        cv.set(x, y, WOOD[max(0, t)])
    for hy in (5, 11):
        for x in range(11):
            if (x, hy) in body:
                cv.set(x, hy, SLATE[3] if x < 4 else SLATE[2] if x < 8 else SLATE[1])
        cv.set(2, hy, SLATE[4])  # a glint on the hoop
    for x in range(11):
        if (x, 13) in body:
            cv.set(x, 13, WOOD[0])
    for (x, y) in oval(5.5, 2.5, 5.5, 2.5):
        cv.set(x, y, WOOD[3])
    for (x, y) in oval(5.5, 2.5, 4, 1.6):
        cv.set(x, y, WOOD[2] if (x + 1) % 3 else WOOD[1])  # the lid's boards
    cv.hline(3, 1, 5, WOOD[4])  # the lit back of the rim
    return keep_foot(cv, 14, 19)


def potted_plant() -> Canvas:
    """A clay pot, 14 x 18, with a leafy plant and two blooms."""
    cv = Canvas(14, 18, pad=PAD)
    for y in range(10, 18):
        half = 5 - (y - 10) * 0.3
        for x in range(14):
            if abs(x + 0.5 - 7) <= half:
                cv.set(x, y, RED[3] if x < 6 else RED[2] if x < 10 else RED[1])
    cv.rect(1, 9, 12, 2, RED[4]); cv.hline(1, 10, 12, RED[2])
    canopy(cv, [(5, 6, 3.4), (9, 5, 3.2), (7, 3, 3.0)], LEAF, seed=77)
    cv.set(4, 3, RED[4]); cv.set(5, 3, RED[3]); cv.set(10, 2, GOLD[4]); cv.set(10, 3, GOLD[3])
    return cv


def sack() -> Canvas:
    """A sack of seed, 12 x 12, tied at the top, lit on its left."""
    cv = Canvas(12, 12, pad=PAD)
    for (x, y) in oval(6, 7.5, 5.5, 4.5):
        cv.set(x, y, SAND[2] if x < 5 and y < 8 else SAND[1] if x < 9 else SAND[0])
    cv.rect(4, 1, 4, 3, SAND[1]); cv.hline(4, 1, 4, SAND[2]); cv.hline(3, 3, 6, WOOD[1])
    cv.set(6, 7, SAND[0]); cv.set(7, 8, SAND[0])
    return cv


def props() -> dict[str, Canvas]:
    return {
        'crate': crate(), 'barrel': barrel(), 'potted_plant': potted_plant(), 'sack': sack(),
        'tree': tree(True), 'tree_small': tree(False), 'tree_autumn': tree(True, True),
        'pine': pine(), 'hut': hut(), 'bed': bed(), 'mailbox': mailbox(), 'stall': stall(),
        'signpost': signpost(), 'bowl': bowl(), 'bush': bush(), 'rock0': rock(0), 'rock1': rock(1),
        'gate': gate(), 'reading_nook': reading_nook(), 'watering_can': watering_can(),
        'lantern': lantern(), 'frog': frog(), 'meadow_sign': meadow_sign(),
    }


if __name__ == '__main__':
    import os
    from PIL import Image
    sheet_items = props()
    sheet_items = {k: style.finalize(v, name=k) for k, v in sheet_items.items()}
    pad = 6
    width = sum(v.w for v in sheet_items.values()) + pad * (len(sheet_items) + 1)
    height = max(v.h for v in sheet_items.values()) + 2 * pad + 40
    out = Image.new('RGBA', (width, height), tuple(int(G[2][i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    x = pad
    # a companion-sized marker (32 x 26) for scale
    for key, cv in sheet_items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((out.width * 3, out.height * 3), Image.NEAREST)
    path = os.environ.get('SHEET', '/tmp/props.png')
    out.save(path)
    print('sheet', path, out.size)
