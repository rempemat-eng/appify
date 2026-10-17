"""NapAttack's world-art style rules as reusable drawing functions.

The look (see docs/vision/art-style.md): a muted, earthy palette with
hue-shifted ramps, a near-black outline around every object, four or five
tones per material lit from the upper left, foliage built from scalloped leaf
clusters, raised turf with a dark lip where it drops onto paths and water,
and hard cast shadows that darken whatever ground they fall on.
"""
from __future__ import annotations

import math

from pixel import Canvas, disc, noise2, smooth_noise, hex_rgba
from materials import INK

# Cast shadows multiply the ground they fall on, cooling it slightly.
SHADOW_MUL = (0.68, 0.72, 0.80)
# Forest shade: the dark under a canopy (reference forests read near-black).
FOREST_DARK = '#262B26'


def _rgb(c):
    return hex_rgba(c) if isinstance(c, str) else c


def darken(cv: Canvas, x: int, y: int, mul=SHADOW_MUL):
    if 0 <= x < cv.w and 0 <= y < cv.h:
        r, g, b, a = cv.get(x, y)
        if a:
            cv.px[x, y] = (int(r * mul[0]), int(g * mul[1]), int(b * mul[2]), a)


def cast_shadow(cv: Canvas, cx: float, cy: float, rx: float, ry: float, mul=SHADOW_MUL):
    """A hard-edged elliptical shadow that darkens the ground beneath it."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                darken(cv, x, y, mul)


def dither_dark(cv: Canvas, x0: int, y0: int, w: int, h: int, strength: float, color=FOREST_DARK):
    """Checker dithering towards forest shade; strength 0..1 picks the density."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if not (0 <= x < cv.w and 0 <= y < cv.h):
                continue
            if strength >= 1:
                cv.set(x, y, color)
            elif strength >= 0.75:
                if (x + y) % 2 == 0 or (x % 2 == 0 and y % 2 == 0):
                    cv.set(x, y, color)
            elif strength >= 0.5:
                if (x + y) % 2 == 0:
                    cv.set(x, y, color)
            elif strength >= 0.25:
                if x % 2 == 0 and y % 2 == 0:
                    cv.set(x, y, color)


def light_value(x: float, y: float, cx: float, cy: float, rx: float, ry: float) -> float:
    """-1 (shadowed, lower right) .. +1 (lit, upper left) on an ellipsoid."""
    nx, ny = (x - cx) / max(1, rx), (y - cy) / max(1, ry)
    return max(-1.0, min(1.0, -0.55 * nx - 0.85 * ny))


def foliage(cv: Canvas, centres, ramp, r: float = 3.2, seed: int = 0, outline=INK,
            box=None, ground_dark: int = 0) -> set:
    """Scalloped leaf clusters, stacked like scales.

    Clusters are painted from the bottom of the mass upwards, so every upper
    cluster sits in front of the ones below it and its dark lower rim lands on
    their bodies: that rim is the scallop line that makes foliage read as
    clumps. Each cluster's tone comes from its place on the whole mass (upper
    left lit, lower right and bottom rows in shade); lit clusters get a light
    cap along their upper-left edge. Returns the silhouette.
    ramp: 5 tones dark..light.
    """
    xs = [c[0] for c in centres]
    ys = [c[1] for c in centres]
    bx0, bx1 = (min(xs) - r, max(xs) + r) if box is None else (box[0], box[2])
    by0, by1 = (min(ys) - r, max(ys) + r) if box is None else (box[1], box[3])
    mcx, mcy = (bx0 + bx1) / 2, (by0 + by1) / 2
    mrx, mry = (bx1 - bx0) / 2, (by1 - by0) / 2
    solid = set()
    order = sorted(enumerate(centres), key=lambda ic: (-ic[1][1], ic[1][0]))
    for i, (cx, cy) in order:
        lv = light_value(cx, cy, mcx - mrx * 0.2, mcy - mry * 0.25, mrx, mry)
        depth = (cy - by0) / max(1, by1 - by0)
        lv -= max(0, depth - 0.55) * 1.4 + ground_dark * 0.2
        tone = 4 if lv > 0.4 else 3 if lv > 0.0 else 2 if lv > -0.42 else 1
        rr = r + (noise2(i, seed, 41) - 0.5) * 0.5
        pts = {(x, y) for (x, y) in disc(cx, cy, rr) if 0 <= x < cv.w and 0 <= y < cv.h}
        # (body, scallop rim, lit cap) per tone: two steps of contrast in the
        # light, one step in the shade, like the reference bushes
        body, rim, cap = {4: (3, 2, 4), 3: (2, 1, 3), 2: (1, 0, 2), 1: (1, 0, 1)}[tone]
        for (x, y) in pts:
            cv.set(x, y, ramp[body])
        for (x, y) in pts:
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            lower_rim = (x, y + 1) not in pts and dy > -0.5
            upper_left = ((x - 1, y) not in pts or (x, y - 1) not in pts) and dx < 0.5 and dy < 0.5
            if lower_rim:
                cv.set(x, y, ramp[rim])
            elif dy > rr * 0.45 and (x + 1, y + 1) not in pts:
                cv.set(x, y, ramp[max(rim, body - 1)])
            elif upper_left:
                cv.set(x, y, ramp[cap])
        solid |= pts
    if outline:
        cv.outline(outline, solid)
    return solid


def rim_centres(cx: float, cy: float, rx: float, ry: float, r: float, spacing: float):
    """Clusters along an ellipse's edge, so the silhouette is a run of bumps."""
    out = []
    perimeter = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
    n = max(6, int(perimeter / spacing))
    for k in range(n):
        a = 2 * math.pi * k / n
        out.append((cx + (rx - r * 0.55) * math.cos(a), cy + (ry - r * 0.55) * math.sin(a)))
    return out


def blob_centres(shape, spacing: float, seed: int = 0, vertical: float | None = None):
    """Staggered cluster centres filling a shape (a set of pixels).

    spacing is the horizontal gap between clusters in a row; rows are
    `vertical` apart (default 0.62 * spacing) and offset by half a cluster, so
    each cluster's scalloped lower rim shows as its own U between two below.
    """
    xs = [p[0] for p in shape]
    ys = [p[1] for p in shape]
    dy = vertical if vertical is not None else spacing * 0.62
    out = []
    row = 0
    y = min(ys) + dy * 0.6
    while y <= max(ys):
        offset = (spacing / 2) if row % 2 else 0
        x = min(xs) + offset + spacing * 0.3
        while x <= max(xs) + 1:
            jx = (noise2(int(x), int(y), seed) - 0.5) * spacing * 0.18
            jy = (noise2(int(x), int(y), seed + 1) - 0.5) * dy * 0.25
            px, py = x + jx, y + jy
            if (int(px), int(py)) in shape:
                out.append((px, py))
            x += spacing
        y += dy
        row += 1
    return out


def facet_stone(cv: Canvas, pts: set, ramp, moss=None, seed: int = 0, outline=INK):
    """Chunky stone: lit top plane, mid front, dark right flank, cracks and moss."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    top_h = max(2, int(h * 0.38))
    for (x, y) in pts:
        fx = (x - x0) / max(1, w - 1)
        fy = (y - y0) / max(1, h - 1)
        if y - y0 < top_h - int(abs(fx - 0.45) * 2):
            tone = 3 if fx < 0.7 else 2
        elif fx > 0.72:
            tone = 1
        else:
            tone = 2 if fy < 0.85 else 1
        cv.set(x, y, ramp[tone])
    # rim lights on the top edge, ambient occlusion along the base
    for (x, y) in pts:
        if (x, y - 1) not in pts and (x - x0) / max(1, w) < 0.75:
            cv.set(x, y, ramp[4])
        if (x, y + 1) not in pts:
            cv.set(x, y, ramp[0])
    # a couple of cracks
    for i in range(max(1, w // 8)):
        cx = x0 + 2 + int(noise2(i, seed, 51) * max(1, w - 4))
        cy = y0 + top_h + int(noise2(i, seed, 52) * max(1, h - top_h - 2))
        for s in range(3):
            if (cx + s // 2, cy + s) in pts:
                cv.set(cx + s // 2, cy + s, ramp[0])
    if moss:
        for (x, y) in pts:
            if y - y0 < top_h and smooth_noise(x, y, 3, seed + 9) > 0.55:
                cv.set(x, y, moss[3] if (x, y - 1) not in pts or y - y0 < 2 else moss[2])
                # drips
                if noise2(x, y, seed + 3) < 0.18:
                    for d in range(1, 3):
                        if (x, y + d) in pts:
                            cv.set(x, y + d, moss[1])
    if outline:
        cv.outline(outline, pts)


def tuft(cv: Canvas, x: int, y: int, dark: str, light: str, tall: int = 2):
    """Three blades: dark roots, light tips (the reference's grass ticks)."""
    cv.set(x, y, dark); cv.set(x + 2, y, dark); cv.set(x + 1, y + 1, dark)
    cv.set(x, y - 1, light)
    cv.set(x + 2, y - 1, light)
    if tall > 2:
        cv.set(x + 1, y - 1, dark); cv.set(x + 1, y - 2, light)

def leafy(cv: Canvas, cx: float, cy: float, rx: float, ry: float, ramp, r: float = 2.6,
          seed: int = 1, bump: float | None = None, flat_bottom: float = 0.75) -> set:
    """Clean foliage: a shaded ellipsoid with spaced leaf clumps and a scalloped rim.

    1. The silhouette is an ellipse plus a ring of small bumps around its edge.
    2. The base is shaded as a sphere lit from the upper left: four clean bands.
    3. Leaf clumps sit on a staggered grid, spaced so each keeps its own shape:
       body one tone lighter than the band under it, a light cap on its upper
       left and a dark rim along its bottom (the reference's U-shaped scallop).
    The deepest band gets no clumps, so the shade side stays quiet. Returns the
    silhouette; outline it afterwards together with anything else in the sprite.
    """
    bump = bump or r * 1.05
    shape = set()
    for y in range(cv.h):
        for x in range(cv.w):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                shape.add((x, y))
    per = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
    n = max(8, int(per / (bump * 1.7)))
    for k in range(n):
        a = 2 * math.pi * (k + 0.5 * noise2(k, seed, 3)) / n
        bx, by = cx + rx * 0.93 * math.cos(a), cy + ry * 0.93 * math.sin(a)
        if by > cy + ry * flat_bottom:
            continue
        shape |= {p for p in disc(bx, by, bump) if 0 <= p[0] < cv.w and 0 <= p[1] < cv.h}

    def base_tone(x: float, y: float) -> int:
        nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        nz = math.sqrt(max(0.0, 1 - min(1, nx * nx + ny * ny)))
        lv = -0.55 * nx - 0.7 * ny + 0.35 * nz - 0.1
        return 3 if lv > 0.38 else 2 if lv > -0.02 else 1 if lv > -0.5 else 0

    for (x, y) in shape:
        cv.set(x, y, ramp[base_tone(x, y)])
    sx, sy = 2 * r + 1.2, r * 1.55
    centres = []
    row = 0
    y = cy - ry + r * 0.4
    while y < cy + ry - r * 0.6:
        x = cx - rx + (sx / 2 if row % 2 else 0) + 1
        while x < cx + rx:
            jx = (noise2(int(x * 5), int(y * 5), seed) - 0.5) * 1.2
            centres.append((x + jx, y))
            x += sx
        y += sy
        row += 1
    for (ccx, ccy) in sorted(centres, key=lambda c: -c[1]):
        if (int(ccx), int(ccy)) not in shape:
            continue
        t = base_tone(ccx, ccy)
        if t == 0:
            continue
        pts = {p for p in disc(ccx, ccy, r) if p in shape}
        body, cap, rim = min(4, t + 1), min(4, t + 2), max(0, t - 1)
        for (x, y) in pts:
            cv.set(x, y, ramp[body])
        for (x, y) in pts:
            dx, dy = x + 0.5 - ccx, y + 0.5 - ccy
            if (x, y + 1) not in pts and dy > 0:
                cv.set(x, y, ramp[rim])
            elif ((x - 1, y) not in pts or (x, y - 1) not in pts) and dx < 0 and dy < 0.3 and t >= 2:
                cv.set(x, y, ramp[cap])
    return shape


def trunk(cv: Canvas, x: int, top: int, bottom: int, width: int, ramp, canopy: set | None = None):
    """A cylinder trunk lit from the left, with bark marks, root flare and canopy shade."""
    for y in range(top, bottom):
        for xx in range(x, x + width):
            f = (xx - x) / max(1, width - 1)
            cv.set(xx, y, ramp[3] if f < 0.3 else ramp[2] if f < 0.7 else ramp[1])
    for y in range(top + 2, bottom - 2, 3):
        cv.set(x + width // 2, y, ramp[1])
    cv.set(x - 1, bottom - 2, ramp[2]); cv.set(x - 2, bottom - 1, ramp[2])
    cv.set(x + width, bottom - 2, ramp[1]); cv.set(x + width + 1, bottom - 1, ramp[1])
    cv.hline(x - 1, bottom - 1, width + 2, ramp[1])
    if canopy:
        for xx in range(x, x + width):
            for y in range(top, bottom):
                if (xx, y) not in canopy:
                    cv.set(xx, y, ramp[0])
                    if y + 1 < bottom:
                        cv.set(xx, y + 1, ramp[1])
                    break


# Outlines take the darkest tone of the material they enclose (deep brown on wood,
# dark olive on leaves, slate on stone), as in Matt's shading references, rather
# than one near-black for everything. They still close every silhouette.
OUTLINE_DEEP = (36, 23, 15)


OUTLINE_MAX_LUM = 58  # an outline is never lighter than this, even around cream or white


def outline_tone(c, amount: float = 0.74):
    """The outline colour for a material: its own colour pulled most of the way to a
    warm near-black, so it reads as an outline but keeps the material's hue."""
    while True:
        t = (
            round(c[0] + (OUTLINE_DEEP[0] - c[0]) * amount),
            round(c[1] + (OUTLINE_DEEP[1] - c[1]) * amount),
            round(c[2] + (OUTLINE_DEEP[2] - c[2]) * amount),
            255,
        )
        if _lum(t) <= OUTLINE_MAX_LUM or amount >= 1:
            return t
        amount = min(1.0, amount + 0.04)


def specks(solid: set, largest: int = 3) -> set:
    """Pixels in tiny detached clusters (spray, petals, sparkles): left unoutlined.
    Diagonal contact counts as attached, so leaf tips still get outlined."""
    seen, out = set(), set()
    for p in solid:
        if p in seen:
            continue
        group, stack = {p}, [p]
        seen.add(p)
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (x + dx, y + dy)
                if n in solid and n not in seen:
                    seen.add(n)
                    group.add(n)
                    stack.append(n)
        if len(group) <= largest:
            out |= group
    return out


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def close_outline(cv: Canvas, ink=INK, dark_below: float = 70.0) -> Canvas:
    """Give a sprite a complete, material-tinted 1 px outline (coherence plan, step 2).

    1. Every solid pixel on the silhouette edge must be dark. Where an edge pixel is
       still a light or mid tone, an outline pixel is added just outside it; where
       the sprite touches its own canvas border, the edge pixel itself is darkened.
       No sprite changes size or position, and outlines never double up.
    2. Silhouette outline pixels drawn in the shared ink are re-tinted to the
       material they enclose. Interior ink (eyes, window panes) is left alone.
    """
    ink_rgba = hex_rgba(ink) if isinstance(ink, str) else ink
    solid = {(x, y) for y in range(cv.h) for x in range(cv.w) if cv.px[x, y][3] == 255}
    tiny = specks(solid)
    added = {}
    for (x, y) in solid:
        c = cv.px[x, y]
        if _lum(c) < dark_below or (x, y) in tiny:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in solid:
                continue
            if 0 <= n[0] < cv.w and 0 <= n[1] < cv.h:
                added.setdefault(n, outline_tone(c))
            else:
                added[(x, y)] = outline_tone(c)
    for (x, y), col in added.items():
        cv.px[x, y] = col
    solid |= set(added)

    def edge(x, y):
        return any((x + dx, y + dy) not in solid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    retint = {}
    for (x, y) in solid:
        if cv.px[x, y][:3] != ink_rgba[:3] or not edge(x, y):
            continue
        # the material this outline encloses: the nearest solid, non-ink, non-outline pixel
        for r in (1, 2, 3):
            near = [cv.px[x + dx, y + dy] for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                    if (x + dx, y + dy) in solid and (x + dx, y + dy) not in added
                    and cv.px[x + dx, y + dy][:3] != ink_rgba[:3] and _lum(cv.px[x + dx, y + dy]) >= dark_below]
            if near:
                near.sort(key=_lum)
                retint[(x, y)] = outline_tone(near[len(near) // 2])
                break
    for (x, y), col in retint.items():
        cv.px[x, y] = col
    return cv


def finalize(cv: Canvas, ink=INK, keep_size: bool = False, name: str = 'sprite') -> Canvas:
    """The sprite contract (docs/vision/art-pipeline.md): nothing is ever cut off.

    1. Art may stray past its nominal canvas into the padding; if it reaches the
       padding's own edge, drawing really was cut off and this raises.
    2. The art is copied onto a canvas with one free pixel on every side, so the
       outline always has room, and given its complete tinted outline.
    3. It is trimmed to the outlined art. ox, oy say where the trimmed top-left sits
       relative to the nominal origin; placement adds them.
    keep_size keeps the nominal canvas (growth stages and decals anchored to a fixed
    box): the art must then fit inside it with room for its outline, except along
    the bottom row, where things stand on the ground.
    """
    p = cv.pad
    full_w, full_h = cv.w + 2 * p, cv.h + 2 * p
    solid = [(x - p, y - p) for y in range(full_h) for x in range(full_w) if cv.get(x - p, y - p)[3]]
    if not solid:
        raise ValueError(f'{name}: empty sprite')
    xs = [x for x, _ in solid]
    ys = [y for _, y in solid]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if p and (x0 <= -p or y0 <= -p or x1 >= cv.w + p - 1 or y1 >= cv.h + p - 1):
        raise ValueError(f'{name}: art reaches the edge of its padding and was cut off')
    if keep_size:
        if x0 < 1 or y0 < 1 or x1 > cv.w - 2 or y1 > cv.h - 1:
            raise ValueError(f'{name}: art leaves no room for its outline in a fixed {cv.w}x{cv.h} box '
                             f'(art spans x {x0}..{x1}, y {y0}..{y1})')
        out = Canvas(cv.w, cv.h)
        for (x, y) in solid:
            out.px[x, y] = cv.get(x, y)
        close_outline(out, ink)
        return out
    out = Canvas(x1 - x0 + 3, y1 - y0 + 3)
    for (x, y) in solid:
        out.px[x - x0 + 1, y - y0 + 1] = cv.get(x, y)
    close_outline(out, ink)
    # trim to the outlined art
    opaque = [(x, y) for y in range(out.h) for x in range(out.w) if out.px[x, y][3]]
    tx0 = min(x for x, _ in opaque)
    ty0 = min(y for _, y in opaque)
    tx1 = max(x for x, _ in opaque)
    ty1 = max(y for _, y in opaque)
    final = Canvas(tx1 - tx0 + 1, ty1 - ty0 + 1)
    for (x, y) in opaque:
        final.px[x - tx0, y - ty0] = out.px[x, y]
    final.ox = x0 - 1 + tx0
    final.oy = y0 - 1 + ty0
    return final
