"""Small boats for the harbour (Claude B; wave 2), drawn new to the house standard: the
rowing boats (`boat_red`, `boat_blue`) and the moored sailing dinghy (`sailboat`). The asset
ledger graded the old ones REWORK: the rowing boats were flat plans with a wheelhouse, no
hull side and no mooring (prop audit: "lit gunwale over a dark hull side, thwarts, oars, a
painter rope"), the dinghy a flat side-on sail (audit: "hull in three-quarter view with
deck; sail furled when moored").

Both are seen in the game's three-quarter view, bow to the east, lit from the upper left,
in the house palette: the hull is built in plan (its half-beam along its length, the sheer
rising to the bow) and projected, so we look down into it over the far gunwale and see the
near side below the near gunwale. Clinker strakes, each lapped over the one below with a lit
lip; frames inside every five pixels; the stem post and the transom; everything a boat that
size carries, and nothing it would not:

- the rowing boat: two thwarts with their rowlocks on the gunwale, the oars shipped fore and
  aft along the sides with their blades forward, bottom boards with rainwater lying aft, the
  anchor line coiled between the thwarts with its grapnel, the painter made fast to the stem
  ring and running down into the water toward its mooring;
- the dinghy: a varnished foredeck with a cleat, the cockpit with its side benches, the mast
  with its forestay and the near shroud, the mainsail furled on the boom with its ties, the
  jib rolled on the forestay, the rudder and the tiller lashed amidships, a burgee at the
  masthead, and the mooring line from the bow to its buoy.

Each sits on the water: a dark line where the hull meets it, ripples lit where they catch the
light, its reflection in two broken bands (all under half alpha, so they are water, not boat).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval  # noqa: E402
import garden_props as gp  # noqa: E402
from style_sheet import T, outline, sib, step  # noqa: E402

PAD = 16


def _water(cv: Canvas, x0: int, x1: int, wl: int, seed: int):
    """Where the hull meets the water: a dark contact line, then ripples and the hull's
    broken reflection, all translucent so the zone's water shows through."""
    for x in range(x0, x1):
        if not cv.get(x, wl + 1)[3]:
            cv.set(x, wl + 1, (24, 34, 64, 120))
        if noise2(x // 3, 0, seed) > 0.45 and not cv.get(x, wl + 2)[3]:
            cv.set(x, wl + 2, (24, 34, 64, 70))
    for (rx, ry, n) in ((x0 - 3, wl + 3, 5), (x0 + 9, wl + 4, 4), (x1 - 12, wl + 3, 6), (x1 + 1, wl + 1, 4)):
        for k in range(n):
            if not cv.get(rx + k, ry)[3]:
                cv.set(rx + k, ry, (232, 240, 248, 100))


def _hull(cv: Canvas, x0: int, L: int, wl: int, bmax: float, fb: tuple, paint: str, sq: float = 0.75,
          deck_to: float = 0.0, seed: int = 0, trim: str | None = None, lining: str | None = None):
    """A clinker hull from x0 (the transom) to x0 + L (the stem), its waterline on row wl.
    fb = (freeboard at the transom, at the bow). Returns per x the rows of the far gunwale,
    the near gunwale and the centre line, and the set of inside pixels."""
    rows = {}
    inside = set()

    def half(t):  # the half-beam in plan: a narrow transom, full at 35 %, a fine entry to the stem
        if t < 0.35:
            return bmax * (0.58 + 0.42 * math.sin(t / 0.35 * math.pi / 2))
        return bmax * math.sqrt(max(0.0, 1 - ((t - 0.35) / 0.65) ** 1.8))

    def rocker(t):  # the keel sweeps up at the forefoot to the stem head, a little under the transom
        if t < 0.12:
            return 1.4 * (1 - t / 0.12)
        if t < 0.55:
            return 0.0
        return (fb[1] - 1) * ((t - 0.55) / 0.45) ** 2.2

    for x in range(x0, x0 + L + 1):
        t = (x - x0) / L
        b = half(t)
        f = fb[0] + (fb[1] - fb[0]) * t ** 2  # the sheer rises toward the bow
        near = int(round(wl - f))
        cyl = near - b * sq
        far = int(round(cyl - b * sq))
        rows[x] = (far, near, int(round(cyl)))
        if b < 0.8:
            continue
        # the inside, seen over the near gunwale: the far gunwale's lit rail, the far side's
        # inner face (it looks up and toward us, so it takes the light) with a frame every
        # five pixels, and the bottom in the hull's own shade, its boards lighter between frames
        for y in range(far, near):
            d = y - far
            rib = (x - x0) % 5 == 0
            if d == 0:
                c = T('timber', 5 if t < 0.45 else 4)
            elif y < cyl:
                c = T(sib('timber', 0.1 if noise2(d // 3, (x - x0) // 10, seed + 3) < 0.6 else 0.5), 1 if rib else 2)
                if lining and not rib:
                    c = T(sib(lining, noise2(d // 3, (x - x0) // 10, seed + 3), 0.3), 2)  # the inside painted buff
            else:
                c = T('timber_cool', 0 if rib else 1)
                if 0.14 < t < 0.3 and y >= near - 2 and not rib:
                    c = T('water', 3 if (y == near - 2 and (x // 2) % 3 == 0) else 2)  # rainwater lying aft in the bilge
            if t > deck_to or y >= cyl:
                cv.set(x, y, c)
                inside.add((x, y))
        # the near side: the gunwale rail, then the strakes, each lapped with a lit lip
        bottom = min(int(round(wl - rocker(t))), wl)
        bottom = max(bottom, near + 1)
        for y in range(near, bottom + 1):
            d = y - near
            if d == 0:
                c = T('timber', 5 if t < 0.45 else 4)  # the near gunwale's rail, its top in the light
            elif d == 1:
                c = T('timber', 2)  # the rail's face, in its own shadow
            elif y >= bottom - 1 and bottom - near > 3:
                c = T('soot', 2 if t < 0.6 else 1)  # the wet, dark boot-top at the waterline
            else:
                s_, r = divmod(d - 2, 2)
                k = 4 if r == 0 else 3  # each strake: a lit lip over its body
                if s_ >= 2:
                    k -= 1  # the turn of the bilge, away from the light
                if t > 0.72:
                    k -= 1  # the bow quarter turning out of the light
                elif t < 0.3:
                    k += 1  # the quarter by the transom, full in the western light
                c = T(sib(paint, noise2(s_, x // 11, seed + 1), 0.25), k)
                if trim and s_ == 0 and r == 0:
                    c = T(trim, k)  # the sheer strake picked out in a second colour
                if r == 0 and noise2(x // 2, s_, seed + 9) > 0.86:
                    c = T('bleached', 3)  # the paint worn back to the wood on a strake's lap
            cv.set(x, y, c)
    # the stem post up the bow's leading edge, lit, and the transom's edge in shade
    for x in range(x0 + L - 2, x0 + L + 1):
        far, near, _ = rows[x]
        t = (x - x0) / L
        for y in range(near - 1, int(round(wl - rocker(t))) + 1):
            if cv.get(x, y)[3] and not cv.get(x + 1, y)[3]:
                cv.set(x, y, T('timber', 4)); cv.set(x - 1, y, T('timber', 2))
    for y in range(rows[x0][0], wl):
        step(cv, x0, y, -1, floor=1)
    return rows, inside


def _undouble_and_outline(cv: Canvas, w: int, h: int) -> Canvas:
    solid = Canvas(w, h, pad=PAD)  # detail in clusters: lone pixels take their neighbours' tone
    for y in range(-PAD, h + PAD):
        for x in range(-PAD, w + PAD):
            c = cv.get(x, y)
            if c[3] == 255:
                solid.set(x, y, c)
    gp.despeckle(solid, passes=2)
    for y in range(-PAD, h + PAD):
        for x in range(-PAD, w + PAD):
            if cv.get(x, y)[3] == 255:
                cv.set(x, y, solid.get(x, y))
    out = Canvas(w + 2, h + 2, pad=PAD)
    for y in range(-PAD, h + PAD):
        for x in range(-PAD, w + PAD):
            c = cv.get(x, y)
            if c[3] == 255 and -1 <= x <= w and -1 <= y <= h:
                out.set(x + 1, y + 1, c)
    outline(out)
    for y in range(-PAD, h + PAD):  # the water's translucent marks go in after the outline
        for x in range(-PAD, w + PAD):
            c = cv.get(x, y)
            if 0 < c[3] < 255 and not out.get(x + 1, y + 1)[3]:
                out.set(x + 1, y + 1, c)
    return out


def rowing_boat(L: int = 54, paint: str = 'berry', seed: int = 0, trim: str | None = None,
                lining: str | None = None) -> Canvas:
    """A clinker rowing boat at its mooring, L long, painted `paint` outside (its sheer strake
    picked out in `trim`, its inside painted `lining` or left varnished)."""
    w, h = L + 12, 24
    cv = Canvas(w, h, pad=PAD)
    wl = h - 6
    x0 = 4
    rows, inside = _hull(cv, x0, L, wl, 7.5, (6, 9), paint, seed=seed, trim=trim, lining=lining)
    # the thwarts across the boat, their rowlocks on the gunwales, the stern sheets
    for tt in (0.36, 0.62):
        tx = x0 + int(L * tt)
        far, near, _ = rows[tx]
        for y in range(far + 1, near):
            cv.set(tx, y, T('timber', 5 if y == far + 1 else 4)); cv.set(tx + 1, y, T('timber', 2))
        if tt == 0.36:  # the rowlocks for the oarsman on the forward thwart
            cv.set(tx + 2, far, T('iron', 4)); cv.set(tx + 3, far, T('iron', 2))
            cv.set(tx + 2, near, T('iron', 4)); cv.set(tx + 3, near, T('iron', 2))
    sx = x0 + 2
    far, near, _ = rows[sx]
    for y in range(far + 1, near):  # the stern sheets, a seat across the transom
        cv.hline(sx, y, 4, T('timber', 4 if y == far + 1 else 3))
        cv.set(sx + 4, y, T('timber', 2))
    # the oars shipped fore and aft along each side, looms on the thwarts, blades forward
    for (k, side) in ((0, 0), (1, 1)):
        xa, xb = x0 + 7 + 3 * k, x0 + int(L * 0.7) + 3 * k
        for x in range(xa, xb):
            far, near, cyl = rows[x]
            y = (far + 2) if side == 0 else (near - 2)
            cv.set(x, y, T('bleached', 4 if x < x0 + L * 0.45 else 3))
            if x == x0 + int(L * 0.36) + 2:
                cv.set(x, y, T('timber', 1))  # the leather where it lies in the rowlock
        far, near, cyl = rows[xb]
        y = (far + 2) if side == 0 else (near - 2)
        for (x, yy) in oval(xb + 3, y, 3.5, 1.2):  # the blade
            if rows.get(x) and rows[x][0] < yy < rows[x][1]:
                cv.set(x, yy, T('bleached', 4 if x < xb + 3 else 3))
    # the anchor line coiled on the bottom boards between the thwarts, its little grapnel on top
    kx = x0 + int(L * 0.47)
    _, near, cyl = rows[kx]
    for (x, y) in oval(kx, cyl + 2, 3.2, 1.8):
        if rows[x][2] <= y < rows[x][1]:
            r = math.hypot((x + 0.5 - kx) / 3.2, (y + 0.5 - cyl - 2) / 1.8)
            cv.set(x, y, T('sand_cool', 1) if r < 0.45 else T('sand', 4 if (x < kx and y <= cyl + 2) else 3 if r < 0.8 else 2))
    cv.set(kx + 1, cyl + 1, T('iron', 4)); cv.set(kx + 2, cyl + 1, T('iron', 2)); cv.set(kx + 2, cyl + 2, T('iron', 1))
    # the painter: made fast to the stem ring, it runs down into the water toward its mooring
    sx = x0 + L
    _, near, _ = rows[sx - 2]
    cv.set(sx, near - 1, T('iron', 4)); cv.set(sx + 1, near - 1, T('iron', 2))
    for k in range(7):
        cv.set(sx + 1 + k // 2, near + k, T('sand_cool', 4 if k % 2 else 3))
    _water(cv, x0, x0 + L + 2, wl, 401 + seed)
    return _undouble_and_outline(cv, w, h)


def sailboat_dinghy() -> Canvas:
    """The sailing dinghy moored off the harbour wall, its sail furled."""
    w, h = 64, 76
    cv = Canvas(w, h, pad=PAD)
    wl = h - 6
    x0, L = 4, 54
    deck_to = 0.62  # the foredeck covers the boat forward of the mast
    # the mast first, behind the far gunwale where it is stepped
    mt = deck_to
    mx = x0 + int(L * mt) - 1
    rows0 = {}
    rows, inside = _hull(cv, x0, L, wl, 11.0, (8, 11), 'plaster', deck_to=deck_to, seed=7)
    rows0.update(rows)
    for (x, y) in inside:  # the cockpit is open to the sky: its varnish catches more light than a rowing boat's bilge
        step(cv, x, y, 1)
    # the foredeck: varnished planks laid fore and aft, a caulked seam between each pair, its
    # king plank, a mooring cleat and the mast partner
    for x in range(x0 + int(L * deck_to), x0 + L):
        far, near, cyl = rows[x]
        for y in range(far, near):
            d = y - far
            k = 4 if d == 0 else 3 if (d % 2) else 2
            if y == cyl:
                k = 3  # the king plank down the middle
            if x > x0 + L * 0.8:
                k -= 1  # the foredeck curving down to the stem, out of the light
            cv.set(x, y, T(sib('timber', noise2(d // 2, x // 13, 71), 0.3), k))
    for x in range(x0 + int(L * deck_to), x0 + L - 1):  # the coaming at the cockpit's forward end
        pass
    far, near, cyl = rows[x0 + int(L * deck_to)]
    for y in range(far, near + 1):
        cv.set(x0 + int(L * deck_to), y, T('timber', 4)); cv.set(x0 + int(L * deck_to) - 1, y, T('timber', 1))
    clx = x0 + int(L * 0.86)
    _, _, cyl = rows[clx]
    cv.hline(clx - 1, cyl, 4, T('iron', 4)); cv.hline(clx, cyl + 1, 2, T('iron', 2))
    # the cockpit's side benches along the inside of each side
    for x in range(x0 + 4, x0 + int(L * deck_to) - 1):
        far, near, cyl = rows[x]
        cv.set(x, far + 2, T('timber', 4)); cv.set(x, far + 3, T('timber', 3))
        cv.set(x, near - 2, T('timber', 4)); cv.set(x, near - 1, T('timber', 2))
    # the sheer stripe in blue under the gunwale, and the boot-top in red over the waterline
    for x in range(x0, x0 + L):
        far, near, cyl = rows[x]
        t = (x - x0) / L
        for d in (1, 2):
            hit = cv.get(x, near + d)
            if hit[3]:
                cv.set(x, near + d, T('sky', (4 if d == 1 else 3) - (1 if t > 0.72 else 0)))
        if cv.get(x, wl - 2)[3]:
            cv.set(x, wl - 2, T('berry', 3 if t < 0.6 else 2))
    # the rudder hung on the transom, the tiller lashed amidships
    for y in range(rows[x0][1], wl + 3):
        cv.set(x0 - 1, y, T('timber', 3)); cv.set(x0 - 2, y, T('timber', 4 if y < wl else 2))
    _, _, cyl = rows[x0 + 1]
    for k in range(9):
        cv.set(x0 - 1 + k, cyl - 2 + k // 6, T('timber', 4 if k < 6 else 3))
    cv.hline(x0 + 6, cyl - 1, 2, T('sand_cool', 3))  # its lashing
    # the mast, stepped through the partner at the deck's after end
    _, _, cyl = rows[mx]
    top = 4
    for y in range(top, cyl):
        cv.set(mx, y, T('timber', 4)); cv.set(mx + 1, y, T('timber', 2))
    cv.hline(mx - 1, cyl - 1, 4, T('timber', 1))  # the partner
    # the masthead: its sheave box and the burgee flying east
    cv.set(mx, top - 1, T('iron', 3)); cv.set(mx + 1, top - 1, T('iron', 1))
    for y in range(top - 3, top):
        cv.set(mx, y, T('iron', 4))
    for (k, n) in ((0, 6), (1, 5), (2, 3)):
        cv.hline(mx + 1, top - 3 + k, n, T('berry', 4 if k == 0 else 3))
    # the forestay from the masthead to the stem, the jib rolled on it
    sx = x0 + L
    _, snear, _ = rows[sx - 1]
    sy = snear - 3
    n = sy - top
    for i in range(n):
        y = top + 1 + i
        x = mx + 2 + int(i * (sx - mx - 2) / n)
        cv.set(x, y, T('iron', 3 if i / n <= 0.6 else 2))
        if 0.6 < i / n < 0.94:  # the jib rolled round the stay's foot, its cloth lit on the west
            cv.set(x - 1, y, T('plaster', 4)); cv.set(x + 1, y, T('plaster', 1))
    # the near shroud from the hounds to its chainplate on the near gunwale, and the halyards
    _, mnear, _ = rows[mx - 3]
    for i in range(mnear - top - 6):
        y = top + 6 + i
        x = mx - int(i * 3 / (mnear - top - 6))
        cv.set(x - 1, y, T('iron', 2))
    for y in range(top + 2, cyl - 4):
        if y % 5 == 0:
            cv.set(mx - 1, y, T('sand_cool', 3))  # the halyard slapping down the mast's lee
    # the boom from the gooseneck aft, the mainsail furled on it with its ties
    by = cyl - 7
    bx0 = x0 + 2
    for x in range(bx0, mx):
        cv.set(x, by, T('timber', 4)); cv.set(x, by + 1, T('timber', 2))
    for x in range(bx0 + 2, mx - 1):  # the furled sail: a long roll of cloth on the boom, lit on top
        u = (x - bx0) / (mx - bx0)
        th = 2 + int(3 * math.sin(min(1.0, u * 1.15) * math.pi * 0.5 + 0.2))
        for k in range(th):
            y = by - 1 - k
            kk = 3 if k == 0 else 4 if k < th - 1 else 5
            if (x - bx0) % 7 in (0, 1):
                kk = 2 if k < th - 1 else 3  # a sail tie cinched round the roll
            cv.set(x, y, T(sib('plaster', noise2((x - bx0) // 7, k, 77), 0.25), kk))
    # the boom crutch at the transom: two short spars crossed, the boom resting in their fork
    far0, near0, _ = rows[x0 + 3]
    for k in range(near0 - by - 1):
        cv.set(x0 + 1 + k // 3, by + 2 + k, T('timber', 4)); cv.set(x0 + 6 - k // 3, by + 2 + k, T('timber', 2))
    for (x, y) in ((bx0 + 9, by + 2), (bx0 + 9, by + 3), (bx0 + 10, by + 4)):
        cv.set(x, y, T('sand_cool', 3))  # the mainsheet down to its block
    # the mooring line from the stemhead down to its buoy ahead
    for k in range(6):
        cv.set(sx + 1 + k, sy + 2 + k, T('sand_cool', 4 if k % 2 else 3))
    bxb, byb = sx + 7, wl - 1
    for (x, y) in oval(bxb, byb, 2.6, 2.4):
        cv.set(x, y, T('clay', 4 if x < bxb and y < byb else 3 if x <= bxb else 1))
    cv.hline(bxb - 2, byb + 2, 5, T('clay', 2))
    _water(cv, x0 - 2, x0 + L + 10, wl, 411)
    return _undouble_and_outline(cv, w, h)


def boat_red() -> Canvas:
    return gp.keep_foot(rowing_boat(50, 'berry', 0), 56, 30)


def boat_blue() -> Canvas:
    return gp.keep_foot(rowing_boat(58, 'sky', 5, trim='plaster', lining='sand'), 64, 30)


def sailboat() -> Canvas:
    """Re-seated so its waterline and middle stand where the old dinghy's did (valley_zones
    places it by the old 40 x 52 box)."""
    return gp.keep_foot(sailboat_dinghy(), 40, 52, dx=-12)


def props() -> dict[str, Canvas]:
    return {'boat_red': boat_red(), 'boat_blue': boat_blue(), 'sailboat': sailboat()}
