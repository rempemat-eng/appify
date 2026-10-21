"""House-style drawing helpers for lane D's Sunstone and fire-country sprites.

Every redrawn sprite in `western_props` and `caldera_props` is drawn from the house
palette's ramps (art/house-palette.json) with the house kit (`style_sheet`): parts lit on
their top and left, sibling ramps for many-part surfaces, texture in clusters of two to
four pixels, a one-pixel outline in each material's own edge tone with the lit break
(docs/vision/house-style.md). Nothing here mixes colours in RGB: shade and light move a
pixel along its own ramp.

The helpers below are only the shapes those sprites share (wheels seen in three-quarter
view, rope, pegs, the clean-up of lone pixels); the materials come from `style_sheet`.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import style_sheet as ss  # noqa: E402
from style_sheet import T, sib, part, rect, step, tone_at, frame, cylinder, overhang  # noqa: E402,F401
from pixel import Canvas, noise2, smooth_noise  # noqa: E402,F401

H_GRAIN = ss.H_GRAIN
V_GRAIN = ss.V_GRAIN
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def ellipse(cx: float, cy: float, rx: float, ry: float) -> set:
    """The pixels inside an ellipse (centred between pixels when cx, cy end in .5)."""
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def wheel(cv: Canvas, cx: float, cy: float, rx: float, ry: float, spokes: int = 10, wood: str = 'timber',
          tyre: str = 'iron', seed: int = 0):
    """A spoked cart wheel facing the viewer in three-quarter view (an ellipse a little
    lower than it is wide): an iron tyre whose upper left catches the light, a felloe of
    jointed wood, straight spokes lit on their upper left, an iron-banded hub."""
    outer = ellipse(cx, cy, rx, ry)
    tyre_px = outer - ellipse(cx, cy, rx - 1.2, ry - 1.2)
    felloe = ellipse(cx, cy, rx - 1.2, ry - 1.2) - ellipse(cx, cy, rx - 2.9, ry - 2.9)
    for (x, y) in tyre_px:
        a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)   # 0 east, pi/2 south (screen)
        lit = -math.cos(a + math.pi / 4)              # +1 at the upper left
        cv.set(x, y, T(tyre, 4 if lit > 0.55 else 3 if lit > -0.1 else 2 if lit > -0.7 else 1))
    joints = [2 * math.pi * (k + 0.5) / 5 + seed for k in range(5)]
    for (x, y) in felloe:
        a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
        lit = -math.cos(a + math.pi / 4)
        k = 4 if lit > 0.5 else 3 if lit > -0.3 else 2
        if any(abs((a - j + math.pi) % (2 * math.pi) - math.pi) < 0.09 for j in joints):
            k = 1                                     # the joint between two felloe pieces
        cv.set(x, y, T(wood, k))
    inner = ellipse(cx, cy, rx - 2.9, ry - 2.9)
    for (x, y) in inner:                               # the gap behind the spokes: the shade under the cart
        cv.set(x, y, T('earth_cool', 0))
    for k in range(spokes):                            # spokes: straight, the upper-left ones lit
        a = 2 * math.pi * (k + 0.25) / spokes
        lit = -math.cos(a + math.pi / 4)
        ex, ey = cx + math.cos(a) * (rx - 2.6), cy + math.sin(a) * (ry - 2.6)
        n = int(max(abs(ex - cx), abs(ey - cy)) * 2) + 1
        for t in range(n + 1):
            p = (int(math.floor(cx + (ex - cx) * t / n)), int(math.floor(cy + (ey - cy) * t / n)))
            if p in inner:
                cv.set(p[0], p[1], T(wood, 4 if lit > 0.35 else 3 if lit > -0.35 else 2))
    hx, hy = int(math.floor(cx)), int(math.floor(cy))
    for (x, y) in ellipse(cx, cy, 2.2, 2.0):           # the hub
        cv.set(x, y, T(wood, 3))
    cv.set(hx - 1, hy - 1, T(tyre, 4)); cv.set(hx, hy - 1, T(tyre, 4))
    cv.set(hx - 1, hy, T(tyre, 3)); cv.set(hx, hy, T(tyre, 1))
    return outer


def rope(cv: Canvas, a, b, sag: float = 0.0, fam: str = 'sand', base: int = 3):
    """A rope from a to b hanging in a shallow curve, lit in runs along its length."""
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
    pts = []
    for t in range(n + 1):
        u = t / n
        p = (round(x0 + (x1 - x0) * u), round(y0 + (y1 - y0) * u + math.sin(u * math.pi) * sag))
        if not pts or pts[-1] != p:
            pts.append(p)
    for i, (x, y) in enumerate(pts):
        cv.set(x, y, T(fam, base + (1 if i % 4 < 2 else 0)))
    return pts


def peg(cv: Canvas, x: int, y: int, fam: str = 'timber'):
    """A tent peg driven in: a lit head over a dark shank, two pixels each."""
    cv.set(x, y, T(fam, 4)); cv.set(x + 1, y, T(fam, 4))
    cv.set(x, y + 1, T(fam, 2)); cv.set(x + 1, y + 1, T(fam, 2))


def kit_sprite(sp, w: int, h: int, foot) -> Canvas:
    """A standing thing drawn by a kit (`dry_kit.Sprite`: ramp, tone and mask arrays) set on
    a prop canvas with its foot at `foot`, on the same house ramps, so a prop and the kit's
    piece are one drawing. The caller finishes it (outline, clean-up)."""
    import dry_kit as dk
    cv = Canvas(w, h, pad=4)
    ox, oy = foot[0] - sp.fx, foot[1] - sp.fy
    for y in range(sp.h):
        for x in range(sp.w):
            if sp.m[y, x]:
                r, g, b = (int(v) for v in dk.COL[sp.f[y, x], min(int(sp.t[y, x]), dk.EDGE_T)])
                cv.set(ox + x, oy + y, (r, g, b, 255))
    return cv


def solid(cv: Canvas) -> set:
    return {(x, y) for y in range(cv.h) for x in range(cv.w) if cv.get(x, y)[3] == 255}


def despeckle(cv: Canvas, pts, keep=()):
    """Turn lone pixels (unlike all four neighbours) into their commonest neighbour,
    except where a lone pixel means something (a rivet, a nail head, a glint: `keep`)."""
    pts = set(pts)
    keep = set(keep)
    for (x, y) in sorted(pts):
        if (x, y) in keep:
            continue
        c = cv.get(x, y)
        if not c[3]:
            continue
        nb = [cv.get(x + dx, y + dy) for dx, dy in N4]
        if all(n[3] for n in nb) and all(n != c for n in nb):
            cv.set(x, y, max(nb, key=nb.count))


def tidy(cv: Canvas, keep=(), passes: int = 2):
    """After the outline: a pixel inside the silhouette that is unlike all four neighbours
    (speckle, house-style rule 4) takes the colour of a neighbour that is not outline,
    preferring the one above or below, so thin stems and posts read as runs of one tone.
    `keep` holds the lone pixels that mean something (rivets, nail heads, glints, eyes)."""
    keep = set(keep)
    for _ in range(passes):
        sol = solid(cv)
        ring = {p for p in sol if any((p[0] + dx, p[1] + dy) not in sol for dx, dy in N4)}
        changed = False
        for (x, y) in sorted(sol - ring):
            if (x, y) in keep:
                continue
            c = cv.get(x, y)
            nbp = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
            if any(cv.get(*n) == c for n in nbp):
                continue
            for n in nbp:
                if n not in ring:
                    cv.set(x, y, cv.get(*n))
                    changed = True
                    break
        if not changed:
            break


def gaps(cv: Canvas):
    """Outline pixels the silhouette closed round (a gap between two stems, under a rope)
    are not edges any more: each becomes the deepest shade (tone 1) of the material beside
    it, so no second dark ring sits inside the first (house-style rule 2)."""
    edges = {ss.hp.hex_rgb(c) for c in list(ss.EDGES.values()) + [ss.INK]}
    sol = solid(cv)
    for (x, y) in sorted(sol):
        if cv.get(x, y)[:3] not in edges:
            continue
        if any((x + dx, y + dy) not in sol for dx, dy in N4):
            continue
        for dx, dy in N4:
            hit = tone_at(cv, x + dx, y + dy)
            if hit and hit[0] != 'ink' and hit[1] >= 0:
                cv.set(x, y, T(hit[0], 1))
                break


def finish(cv: Canvas, keep=()):
    """Clean lone pixels, then the house outline (edge tones, lit break), then the gaps it
    closed and the pixels it left lone."""
    despeckle(cv, solid(cv), keep)
    ss.outline(cv)
    gaps(cv)
    tidy(cv, keep)
    return cv
