"""One ground for a region (Matt, 19 Oct: "it just looks attached together but not
seamlessly"; docs/vision/art-faults.md, rule 1). The turf of the whole valley is painted
from the valley's own coordinates, so its patches, tufts and blades run on across every
zone's edge, and the kinds of ground (meadow, forest floor, alpine turf) blend into each
other over about a hundred pixels instead of changing at a tile line. Zones paint their
paths, water and buildings on top as before.

`valley(cv, zone, frame)` replaces `worlds.grass(cv, frame, ramp)` in every valley zone;
garden.py can call it with zone 'garden' so the garden's meadow is the same meadow."""
from __future__ import annotations

import detail
import garden as g
from pixel import noise2, smooth_noise

W, H = 320, 576
# zones whose ground is drawn elsewhere and does not blend toward its neighbours yet
# (the garden: garden.py, Claude B's)
FIXED = {'garden'}
BLEND = 64  # half the width of the band where one kind of ground gives way to the next

MEADOW = g.G
FOREST = ['#24382A', '#40603A', '#577A44', '#668A4E', '#8EAE68']
ALPINE = ['#2F4E3E', '#4F7A5A', '#6A9468', '#78A06E', '#A3C38C']

# what each valley zone's ground is (the town's square and the harbour's quay are drawn
# on top; this is the turf round them)
VALLEY_GROUND = {
    'woodland': FOREST, 'ridge': ALPINE, 'hollow': ALPINE,
}


def _layout():
    import zones
    return zones.LAYOUT['valley']


def _inside(gx: float, gy: float, col: int, row: int) -> float:
    """How far a point lies inside a zone's rectangle (negative outside), in px."""
    x0, y0 = col * W, row * H
    return min(gx - x0, x0 + W - gx, gy - y0, y0 + H - gy)


def kind_at(gx: int, gy: int):
    """The ground's ramp at a point: each nearby zone pulls toward its own kind of ground
    with a weight that fades in over the blend band, and a slow patchy noise picks among
    them, so the change is a ragged interlocking edge that wanders, never a line."""
    lay = _layout()
    col, row = gx // W, gy // H
    weights = {}
    for z, (c, r) in lay.items():
        if abs(c - col) > 1 or abs(r - row) > 1:
            continue
        d = _inside(gx, gy, c, r)
        w = max(0.0, min(1.0, (d + BLEND) / (2 * BLEND)))
        if w <= 0:
            continue
        ramp = VALLEY_GROUND.get(z, MEADOW)
        if z in FIXED:
            w *= 6  # (its own drawing does not blend back: its neighbours meet it whole)
        weights[id(ramp)] = (weights.get(id(ramp), (ramp, 0.0))[0], weights.get(id(ramp), (ramp, 0.0))[1] + w)
    if not weights:
        return MEADOW
    total = sum(w for _r, w in weights.values())
    u = smooth_noise(gx, gy, 11, 901) * 0.7 + noise2(gx // 2, gy // 2, 902) * 0.3
    acc = 0.0
    for ramp, w in sorted(weights.values(), key=lambda rw: rw[0][0]):
        acc += w / total
        if u < acc:
            return ramp
    return list(weights.values())[-1][0]


def valley(cv, zone: str, frame: int = 0):
    """Paint this zone's turf from the valley's coordinates."""
    col, row = _layout()[zone]
    ox, oy = col * W, row * H
    ramps = {}
    for y in range(H):
        for x in range(W):
            gx, gy = x + ox, y + oy
            G = kind_at(gx, gy)
            ramps[(x, y)] = G
            n = smooth_noise(gx, gy, 22, 11)
            cv.set(x, y, G[2] if n < 0.62 else G[3])
    # tufts, in clusters that wander across the valley (never thicker at a tile's edge)
    for ty in range(0, H, 6):
        for tx in range(0, W, 6):
            gx, gy = tx + ox, ty + oy
            x, y = tx + int(noise2(gx, gy, 4) * 6), ty + int(noise2(gx, gy, 5) * 6)
            if not (0 <= x < W and 0 <= y < H - 2):
                continue
            cluster = smooth_noise(gx, gy, 25, 63) > 0.57
            density = 0.36 if cluster else 0.14
            if noise2(gx, gy, 3) < density:
                G = ramps[(x, y)]
                ground = 3 if cv.get(x, y)[:3] == tuple(int(G[3][k:k + 2], 16) for k in (1, 3, 5)) else 2
                detail.grass_tuft(cv, x, y + 2, int(noise2(gx, gy, 8) * 6), G, ground)
    # the grain: short two-pixel blades everywhere (art-style.md, detail target)
    for y in range(2, H - 1):
        for x in range(W):
            gx, gy = x + ox, y + oy
            if noise2(gx, gy, 9) > 0.055:
                continue
            G = ramps[(x, y)]
            lit, mid = _hex(G[3]), _hex(G[2])
            c = cv.get(x, y)[:3]
            below = cv.get(x, y + 1)[:3]
            if c == lit and below == lit:
                cv.set(x, y, G[4]); cv.set(x, y + 1, G[2])
            elif c == mid and below == mid:
                cv.set(x, y, G[3]); cv.set(x, y + 1, G[1])


def _hex(c):
    return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))
