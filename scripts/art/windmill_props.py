"""Tower windmills (Claude B; wave 2 and to-b-0120), drawn new to the house standard: the
home valley's drainage mill at the halt (it replaces valley_props' old windmill, which the
asset ledger graded REWORK: off the house palette, speckled, its foot off the grid) and the
coal hills' corn mill for Cogsworth (props.md section 3: "windmill").

One builder, two mills, each built from the house kit's own pieces (house_kits.py: walls in
courses or brick, doorways, casements; style_sheet.py: parts, boards, roof rows, the house
outline in each material's edge tone), in the house palette with light from the upper left,
at the size guide's tower mill (112 to 160 tall, sails 96 across, a door 32 with its step),
on a footing of whole 8 px cells. Every part is there for what it does:

- the footing course, wider than the tower, that carries it and keeps the wet off its foot;
- the tower in three storeys of 32, tapering, round (each course stepped lighter on the
  west and darker toward the east, so it reads as a drum and not a wall);
- one window to a storey, staggered up the tower as the stairs inside climb;
- the stage (gallery) at the second floor, on its braces, where the miller reaches the
  sails to set or furl the cloths and works the brake;
- the cap, turned into the wind by the fantail behind it, the windshaft's poll end at its
  front carrying the stocks and the four sails;
- the sails: lattice frames of bars between a whip and a hemlath; on the valley mill all four
  carry their cloths, one pair spread full and one pair with its cloth eased into loose folds
  at the leech (the miller sets the cloth to the wind's strength), on the Cogsworth mill
  they are patent sails, rows of hinged shutters opened and closed together by a rod;
- what the mill is for at its foot: the valley's drainage mill lifts the field drains'
  water with a scoop wheel in a boarded case into the outfall; Cogsworth's corn mill has its
  sacks of flour at the door, the hand cart that takes them down the hill and a gas lamp.

Three frames a twelfth of a turn apart loop (four sails repeat every quarter turn).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, oval  # noqa: E402
import garden_props as gp  # noqa: E402
import house_kits as hk  # noqa: E402
from style_sheet import T, boards, outline, part, rect, roof_rows, sib, step, tone_at  # noqa: E402

PAD = 16
STOREY = 32


def _drum(cv: Canvas, cx: float, ttop: int, tbot: int, r_top: float, r_bot: float, kind: str, seed: int) -> set:
    """The tower: a wall of `kind` from the house kit, cut to the taper and shaded round.
    Returns the set of its pixels."""
    w = int(2 * r_bot) + 4
    x0 = int(cx - r_bot) - 2
    tmp = Canvas(w, tbot - ttop)
    hk.wall(tmp, 0, 0, w, tbot - ttop, kind, seed=seed)
    pts = set()
    for y in range(ttop, tbot):
        r = r_top + (y - ttop) / max(1, tbot - ttop - 1) * (r_bot - r_top)
        xa, xb = int(round(cx - r)), int(round(cx + r))
        for x in range(xa, xb + 1):
            c = tmp.get(x - x0, y - ttop)
            if not c[3]:
                continue
            cv.set(x, y, c)
            f = (x + 0.5 - (cx - r)) / (2 * r + 1)
            k = 1 if f < 0.2 else 0 if f < 0.52 else -1 if f < 0.78 else -2
            if k:
                step(cv, x, y, k, floor=1)
            pts.add((x, y))
    return pts


def _cap(cv: Canvas, cx: float, ttop: int, r: float, kind: str, seed: int):
    """The cap over the curb: a boat-shaped dome of shingles (timber) or an ogee of copper
    sheet in standing seams, lit on the west, the curb's lit rail and the band it throws on
    the tower's top course; a finial on the crown."""
    half = r + 5
    ch = 18 if kind == 'shingle' else 20
    dome = set()
    for y in range(ttop - ch, ttop):
        v = (ttop - y) / ch  # 0 at the curb, 1 at the crown
        if kind == 'shingle':
            hw = half * math.sqrt(max(0.0, 1 - v ** 2.2))
        else:  # an ogee: full at the curb, pinched in its upper third, a point at the top
            hw = half * (1 - v ** 1.6) * (1 + 0.18 * math.sin(v * math.pi * 1.5))
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
            dome.add((x, y))
    if kind == 'shingle':
        roof_rows(cv, int(cx - half) - 1, ttop - ch, int(2 * half) + 3, ch, 'timber', 3, row=4, tile=(5, 7),
                  seed=seed, clip=dome)
    else:
        for (x, y) in dome:  # copper sheet in standing seams, each sheet a sibling, verdigris in the seams' feet
            u = x - (cx - half)
            seam = int(u) % 6 == 0
            fam = sib('copper', noise2(int(u) // 6, 0, seed), 0.3)
            k = 2 if seam else 3
            if seam and y > ttop - 4:
                fam = 'lagoon'
            cv.set(x, y, T(fam, k))
    for (x, y) in dome:  # round: lit west, shaded east
        rr = max(1.0, half * 1.0)
        f = (x + 0.5 - (cx - rr)) / (2 * rr)
        k = 1 if f < 0.28 else 0 if f < 0.55 else -1 if f < 0.8 else -2
        if k:
            step(cv, x, y, k, floor=1)
    for x in range(int(round(cx - half)) - 1, int(round(cx + half)) + 2):  # the curb rail, its band on the tower
        cv.set(x, ttop, T('timber', 4 if x < cx else 3)); cv.set(x, ttop + 1, T('timber', 2))
        step(cv, x, ttop + 2, -2, floor=1); step(cv, x, ttop + 3, -1, floor=1)
    fx = int(round(cx))
    for (x, y) in oval(fx, ttop - ch - 2, 2.2, 2.2):  # the finial
        cv.set(x, y, T('brass', 5 if x < fx and y < ttop - ch - 2 else 4 if x <= fx else 2))
    cv.set(fx, ttop - ch, T('brass', 3))


def _fantail(cv: Canvas, cx: float, ttop: int):
    """The fantail on its frame behind the cap: six vanes on a hub, turning the cap into the
    wind through gearing to the curb. Seen over the cap's back, above its crown."""
    fx, fy = int(round(cx)) + 4, ttop - 27
    for k in range(10):  # the frame's two struts from the cap's back
        cv.set(fx - 3 + k // 4, ttop - 17 - k, T('timber', 3)); cv.set(fx + 4 - k // 4, ttop - 17 - k, T('timber', 2))
    for i in range(6):
        a = i * math.pi / 3 + 0.3
        for t in range(2, 7):
            x, y = int(round(fx + t * math.cos(a))), int(round(fy + t * math.sin(a) * 0.9))
            cv.set(x, y, T('plaster', 4 if math.cos(a) < 0.2 else 3))
            x2, y2 = int(round(fx + t * math.cos(a + 0.25))), int(round(fy + t * math.sin(a + 0.25) * 0.9))
            if t > 3:
                cv.set(x2, y2, T('plaster', 2))
    cv.set(fx, fy, T('iron', 3)); cv.set(fx + 1, fy, T('iron', 1))


def _sails(cv: Canvas, hx: float, hy: float, turn: float, R: int, kind: str) -> set:
    """Four sails on two stocks through the poll end. Each sail: the whip (its spar) lit on
    its upper-left face, sail bars across it every four pixels to a hemlath at the trailing
    edge, and, set or not, its cloth (common sails) or its shutters (patent sails). The sails
    turn clockwise, so each one's frame trails on its anticlockwise side. Each pixel is
    mapped back into the sail's own frame, so bars and shutters stay clean lines at any angle."""
    drawn = set()
    sq = 0.94  # the sails' plane faces south; seen a little from above it is barely foreshortened
    for i in range(4):
        a = turn + math.pi / 4 + i * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -math.sin(a), math.cos(a)
        lit_neg = (-vx - vy) > 0       # is the whip's -v face the one toward the upper left?
        hem_lit = (vx + vy) < 0        # does the hemlath's outer face look up-left?
        clothed = kind == 'common'
        for y in range(int(hy) - R - 4, int(hy) + R + 5):
            for x in range(int(hx) - R - 4, int(hx) + R + 5):
                dx, dy = x + 0.5 - hx, (y + 0.5 - hy) / sq
                u = dx * ux + dy * uy
                v = dx * vx + dy * vy
                if u < -1 or u > R + 0.5:
                    continue
                c = None
                if abs(v) <= 1.6:  # the whip: a squared spar, lit on the face toward the light
                    if abs(v) < 0.55:
                        c = T('timber', 3)
                    else:
                        c = T('timber', 4 if (v < 0) == lit_neg else 2)
                    if u > R - 1:
                        c = T('timber', 2)
                elif u >= 11 and 1.6 < v <= 10.5:
                    hem = v > 9.2
                    bar = (u - 11) % 5 < 1.05
                    tip = u > R - 1.1 or u < 12.1
                    if hem or tip:
                        c = T('timber', 4 if hem_lit else 3)
                    elif kind == 'patent':
                        # shutters: boards between the bars, either side of the striking rod
                        # that opens them all together, each with a lit lip and its body
                        r_ = (u - 11) % 5
                        if r_ < 1.05:
                            c = T('timber', 1)
                        elif 5.3 < v < 6.7:
                            c = T('iron', 3 if lit_neg else 2)
                        else:
                            c = T('plaster', 4 if r_ < 2.1 else 3)
                    elif clothed:
                        # the cloth: folds along the whip as bands, a seam every ten, the bars
                        # showing faintly through
                        band = v - 1.6
                        k = 2 if band < 1 else 4 if band < 3 else 3 if band < 6 else 2 if band < 8 else 3
                        if (u - 11) % 10 < 1:
                            k = max(1, k - 1)
                        elif bar and 3 < band < 7:
                            k = max(2, k - 1)
                        if i % 2 and band > 6.2 and (u - 11) % 10 < 4:
                            k = max(1, k - 1)  # the reefed pair: the cloth gathered in loose folds at its leech
                        c = T(sib('plaster', noise2(int((u - 11) // 10), i, 81), 0.3), k)
                    elif bar:
                        c = T('timber', 4 if hem_lit else 3)
                if c is not None:
                    cv.set(x, y, c)
                    drawn.add((x, y))
    hxi, hyi = int(round(hx)), int(round(hy))
    for (x, y) in oval(hxi, hyi, 3.6, 3.6):  # the poll end: the cast-iron canister the stocks pass through
        d = (x - hx) + (y - hy)
        cv.set(x, y, T('iron', 4 if d < -2 else 3 if d < 1 else 1))
        drawn.add((x, y))
    cv.set(hxi - 1, hyi - 1, T('iron', 5)); cv.set(hxi - 2, hyi - 1, T('iron', 5))
    return drawn


def _stage(cv: Canvas, cx: float, sy: int, r: float, kind: str, seed: int):
    """The stage at the second floor: its deck on braces from the wall, the rail on posts
    standing in front of the tower, and the band the deck throws on the wall below."""
    half = int(round(r)) + 8
    x0, x1 = int(round(cx)) - half, int(round(cx)) + half
    fam = 'timber' if kind == 'timber' else 'iron'
    for x in range(x0 + 2, x1 - 1):  # the deck's shadow on the tower under it
        for (dy, k) in ((3, -2), (4, -2), (5, -1)):
            if tone_at(cv, x + 1, sy + dy):
                step(cv, x + 1, sy + dy, k, floor=1)
    for bx in range(x0 + 3, x1 - 2, 9):  # the braces under the deck, back to the wall (none over the door)
        wall = int(round(cx + (bx - cx) * 0.55))
        if -14 < min(bx, wall) - cx < 9 or -14 < max(bx, wall) - cx < 9:
            continue
        for k in range(7):
            x = bx + (wall - bx) * k // 7
            cv.set(x, sy + 3 + k, T(fam, 3)); cv.set(x + 1, sy + 3 + k, T(fam, 1))
    if fam == 'timber':
        boards(cv, x0, sy, x1 - x0, 3, lambda bi, si: (sib('timber', noise2(si, bi, seed), 0.3), 3), board=3,
               seed=seed, joints=(8, 14), nails=False)
        for x in range(x0, x1):
            cv.set(x, sy, T('timber', 4 if x < cx + 4 else 3))
    else:
        for x in range(x0, x1):
            cv.set(x, sy, T('iron', 4 if x < cx + 4 else 3)); cv.set(x, sy + 1, T('iron', 3)); cv.set(x, sy + 2, T('iron', 1))
            if (x - x0) % 6 == 2:
                cv.set(x, sy + 1, T('iron', 5))  # rivets along the deck plate
    for px in range(x0 + 1, x1, 7):  # the rail's posts and its two rails
        for y in range(sy - 8, sy):
            cv.set(px, y, T(fam, 4 if fam == 'timber' else 3)); cv.set(px + 1, y, T(fam, 2 if px + 2 < x1 else 3))
    for x in range(x0, x1):
        cv.set(x, sy - 9, T(fam, 4 if x < cx else 3)); cv.set(x, sy - 8, T(fam, 2))
        if fam == 'iron' and (x - x0) % 3 == 1:
            cv.set(x, sy - 4, T('iron', 2))  # the iron rail's lower bar in short balusters' shadow
        elif fam == 'timber':
            cv.set(x, sy - 4, T('timber', 3 if x < cx else 2))
    if fam == 'iron':
        for x in range(x0, x1):
            cv.set(x, sy - 5, T('iron', 3))
    return x0, x1


def tower_mill(turn: float = 0.0, spec: str = 'valley') -> Canvas:
    valley = spec == 'valley'
    W, H = 112, 158
    cv = Canvas(W, H, pad=PAD)
    cx = 51.0
    foot = H - 1
    R = 48
    r_bot, r_top = 22.0, 14.0
    plinth_h = 6
    ftop = foot - plinth_h + 1
    tbot = ftop
    ttop = tbot - 3 * STOREY
    hub = (cx, ttop - 7)
    seed = 11 if valley else 23
    wall_kind = 'drystone' if valley else 'brick_soot'
    # behind everything: the fantail on its frame over the cap's back
    _fantail(cv, cx, ttop)
    # the footing: a course of big stones, wider than the tower, its top lit
    px0, pw = int(cx) - 24, 62 if valley else 56
    hk.plinth(cv, px0, foot - plinth_h + 1, pw, plinth_h, 'stone', seed)
    for x in range(px0, px0 + pw):
        step(cv, x, foot - plinth_h + 1, 1)
    # the tower
    tower = _drum(cv, cx, ttop, tbot, r_top, r_bot, wall_kind, seed)

    def r_at(y):
        return r_top + (y - ttop) / (tbot - ttop - 1) * (r_bot - r_top)

    # the windows, one to a storey, staggered as the stair climbs; the door on the foot storey
    panes = []
    for (wy, dx, ww, wh) in ((tbot - STOREY + 6, -15, 8, 10), (tbot - 2 * STOREY + 8, -10, 8, 10),
                             (tbot - 3 * STOREY + 9, 3, 7, 9)):
        wx = int(round(cx + dx - ww / 2))
        hk.casement(cv, wx, wy, ww, wh, frame_fam='timber', cols=1, rows=2, sill='stone',
                        lintel='brick' if not valley else 'stone', seed=seed)
        panes.append((wx + 2, wy + 2, ww - 4, wh - 4))
    dx0 = int(round(cx)) - 9
    hk.doorway(cv, dx0, foot, 14, 32, 'timber', 'ledged', 'stone' if valley else 'timber', seed=seed,
               lintel='stone' if valley else None, step_fam='stone')
    # the stage at the second floor
    sy = tbot - STOREY - 3
    sx0, sx1 = _stage(cv, cx, sy, r_at(sy), 'timber' if valley else 'iron', seed)
    # the cap and the sails
    _cap(cv, cx, ttop, r_top, 'shingle' if valley else 'copper', seed)
    sail_px = _sails(cv, hub[0], hub[1], turn, R, 'common' if valley else 'patent')
    # the sails' shadow thrown on the tower, down and to the east
    for (x, y) in sail_px:
        q = (x + 3, y + 4)
        if q in tower and q not in sail_px:
            step(cv, q[0], q[1], -1, floor=1)
    # the foot of the mill: what it is for
    if valley:
        # the scoop wheel's case against the east side, boarded, its rounded top over the wheel
        hx0, hx1, htop = int(cx) + 16, int(cx) + 34, foot - 30
        mid, rad = (hx0 + hx1) / 2, (hx1 - hx0) / 2
        case = {(x, y) for (x, y) in rect(hx0, htop, hx1 - hx0, foot - 5 - htop)
                if not (y < htop + 9 and (y - htop) < 9 * (1 - math.sqrt(max(0.0, 1 - ((x + 0.5 - mid) / rad) ** 2))))}
        for (x, y) in case:  # upright boards, 3 wide: a lit west edge, the body, a dark joint
            j = (x - hx0) % 3
            k = 4 if j == 0 else 3 if j == 1 else 1
            fam = sib('timber', noise2((x - hx0) // 3, 0, 71), 0.3)
            if noise2((x - hx0) // 3, y // 6, 72) > 0.85 and j == 1:
                k = 2  # a board gone dark with wet
            cv.set(x, y, T(fam, k))
        for (x, y) in case:  # round: the hood turns out of the light toward the east
            f = (x + 0.5 - hx0) / (hx1 - hx0)
            if f > 0.6:
                step(cv, x, y, -1 if f < 0.85 else -2, floor=1)
        for k in range(40):  # an iron strap over the hood's curve, bolted at its feet
            a = math.pi * (1 - k / 39)
            x = int(round(mid + (rad - 1.5) * math.cos(a)))
            y = int(round(htop + 9 - 8 * math.sin(a))) + 2
            if (x, y) in case:
                cv.set(x, y, T('iron', 4 if x < mid else 2))
        for x in range(hx0 + 3, hx1 - 2):  # the wheel's rim in its slot, a scoop's edge every third
            cv.set(x, htop + 13, T('timber', 1)); cv.set(x, htop + 14, T('timber', 1) if x % 3 else T('timber', 3))
        cv.vline(hx1 - 1, htop + 4, foot - 9 - htop, T('timber', 2))  # the case's corner post
        cv.vline(hx0, htop + 4, foot - 9 - htop, T('timber', 4))
        for x in range(hx0 + 2, hx1):  # the outfall: a stone lip, the water lifted into it
            cv.set(x, foot - 5, T('stone', 4 if x < hx0 + 8 else 3)); cv.set(x, foot - 4, T('stone', 2))
        for x in range(hx0 + 4, hx1 - 1):
            ph = int(turn * 24 / math.pi)
            cv.set(x, foot - 7, T('water', 4 if (x + ph) % 5 < 2 else 3)); cv.set(x, foot - 6, T('water', 2))
        for y in range(foot - 11, foot - 6):  # the sluice board, water lit where it tips over
            cv.set(hx0 + 2, y, T('timber', 4)); cv.set(hx0 + 3, y, T('timber', 2))
        cv.hline(hx0 + 4, foot - 8, 3, T('water', 5))
        for y in range(foot - 20, foot - 4):  # the level post at the outfall, marked in feet
            cv.set(hx1 + 1, y, T('bleached', 4)); cv.set(hx1 + 2, y, T('bleached', 2))
            if (y - foot) % 4 == 0:
                cv.set(hx1 + 1, y, T('berry', 3)); cv.set(hx1 + 2, y, T('berry', 2))
        # the bench by the door, where the miller watches the sky
        bx = int(cx) - 21
        part(cv, bx, foot - 10, 10, 3, 'timber', 4)
        for lx in (bx + 1, bx + 7):
            part(cv, lx, foot - 7, 2, 5, 'timber', 2, glint=False, corners=False)
        # the brake rope down from the stage, belayed on a cleat by the door
        for y in range(sy + 3, foot - 14):
            cv.set(sx0 + 4, y, T('sand_cool', 4 if y % 3 else 3))
        part(cv, sx0 + 2, foot - 14, 5, 2, 'timber', 3, glint=False)
    else:
        # sacks of flour by the door and the hand cart that takes them down the hill
        for (sx, sh) in ((int(cx) - 20, 9), (int(cx) - 15, 8), (int(cx) + 8, 9)):
            for y in range(foot - sh, foot):
                cv.hline(sx, y, 5, T('sand_cool', 4 if y < foot - sh + 2 else 3 if y < foot - 2 else 2))
            cv.hline(sx + 1, foot - sh - 1, 3, T('sand_cool', 3))
            cv.set(sx + 2, foot - sh, T('timber', 1))  # the sack's tie
        cx0 = int(cx) + 18
        part(cv, cx0, foot - 12, 14, 7, 'timber', 3)
        for x in range(cx0 + 1, cx0 + 13):
            cv.set(x, foot - 13, T('sand_cool', 4 if x % 4 else 3))
        for (x, y) in oval(cx0 + 4, foot - 3, 3.2, 3.2):  # the cart's wheel, iron-tyred
            d = math.hypot(x + 0.5 - cx0 - 4, y + 0.5 - foot + 3)
            cv.set(x, y, T('iron', 4 if (x < cx0 + 4 and y < foot - 3) else 2) if d > 2.2 else T('timber', 3 if d > 0.8 else 1))
        for k in range(8):  # its handles
            cv.set(cx0 + 13 + k, foot - 9 + k // 3, T('timber', 3))
        # soot settles on the brick under the stage and the cap; a gas lamp on a bracket
        lx = int(cx) + 8
        part(cv, lx, foot - 30, 4, 5, 'lamp', 4, glint=False)
        cv.hline(lx - 1, foot - 31, 6, T('iron', 3)); cv.hline(lx - 3, foot - 28, 3, T('iron', 2))  # its bracket back to the wall
    # grass at the footing's ends, kept inside the foot
    for gx in (px0 + 1, px0 + 2, px0 + pw - 3, px0 + pw - 2):
        cv.set(gx, foot - plinth_h, T('grass', 4 if gx < cx else 3))
    gp.despeckle(cv, passes=1)
    _smooth_silhouette(cv)
    out = Canvas(W + 2, H + 2, pad=PAD)
    for y in range(-PAD, H + PAD):
        for x in range(-PAD, W + PAD):
            c = cv.get(x, y)
            if c[3] and -1 <= x <= W and -1 <= y <= H:
                out.set(x + 1, y + 1, c)
    ring = outline(out)
    _open_corners(out, ring)
    undouble(out)
    _fold_rare(out, 120)
    for (gx, gy, gw, gh) in panes:
        gp.WINDOWS.append((out, (gx + 1, gy + 1, gw, gh)))
    for x in range(px0 + 1, px0 + pw + 4):  # the contact shadow, down and to the east of the footing
        for (dy, a) in ((2, 110), (3, 60)):
            if not out.get(x, foot + dy)[3]:
                out.set(x, foot + dy, (24, 18, 30, a))
    return out


def _smooth_silhouette(cv: Canvas, passes: int = 3):
    """A turned sail's edge is a staircase of uneven steps; a notch one pixel deep would take
    a doubled outline. Notches (a clear pixel with three drawn neighbours) are filled from
    their neighbours and lone spurs (a drawn pixel with one) are cleared, so the outline is
    one clean ring."""
    p = cv.pad
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for _ in range(passes):
        fill, clear = [], []
        for y in range(-p + 1, cv.h + p - 1):
            for x in range(-p + 1, cv.w + p - 1):
                c = cv.get(x, y)
                ns = [cv.get(x + dx, y + dy) for dx, dy in N4]
                drawn = [n for n in ns if n[3] == 255]
                if c[3] == 0 and len(drawn) >= 3:
                    fill.append((x, y, max(drawn, key=drawn.count)))
                elif c[3] == 255 and len(drawn) <= 1:
                    clear.append((x, y))
        for (x, y, c) in fill:
            cv.set(x, y, c)
        for (x, y) in clear:
            cv.set(x, y, (0, 0, 0, 0))
        if not fill and not clear:
            break


def _open_corners(cv: Canvas, ring: set):
    """Where the outline turns an inside corner (a lattice sail's open bays, a staircase on a
    turned edge) it closes on itself into a block two pixels thick; the corner pixel, walled in
    by outline and touching the air only across its diagonal, is cleared so the line stays one
    pixel."""
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    D4 = ((1, 1), (-1, 1), (1, -1), (-1, -1))
    for (x, y) in sorted(ring):
        ns = [(x + dx, y + dy) for dx, dy in N4]
        if all(cv.get(*n)[3] == 255 for n in ns) and sum(n in ring for n in ns) >= 2 \
                and any(cv.get(x + dx, y + dy)[3] == 0 for dx, dy in D4):
            cv.set(x, y, (0, 0, 0, 0))


def undouble(cv: Canvas):
    """The house outline is one ring: where a thin dark member (a whip's shaded face, a
    brace) runs right against it at nearly its lightness, with lighter fill behind, it reads
    as a second ring; that member steps one tone up its own ramp."""
    import house_palette as hp
    p = cv.pad
    solid = {(x, y) for y in range(-p, cv.h + p) for x in range(-p, cv.w + p) if cv.get(x, y)[3] == 255}
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    ring = {q for q in solid if any((q[0] + dx, q[1] + dy) not in solid for dx, dy in N4)}
    L = {}

    def lum(q):
        if q not in L:
            L[q] = hp.to_oklab(cv.get(*q)[:3])[0]
        return L[q]
    for (x, y) in ring:
        for dx, dy in N4:
            n, m2 = (x + dx, y + dy), (x + 2 * dx, y + 2 * dy)
            if n in solid and n not in ring and m2 in solid and abs(lum(n) - lum((x, y))) < 0.05 \
                    and lum(n) <= 0.45 and lum(m2) > lum((x, y)) + 0.12:
                step(cv, n[0], n[1], 1)
                L.pop(n, None)


def _fold_rare(cv: Canvas, limit: int):
    """Keep a building under the style's colour budget: the rarest tones take the nearest
    tone already used more widely (in Oklab)."""
    import house_palette as hp
    p = cv.pad
    count = {}
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            c = cv.get(x, y)
            if c[3] == 255:
                count[c] = count.get(c, 0) + 1
    if len(count) <= limit:
        return
    keep = sorted(count, key=count.get, reverse=True)[:limit]
    lab = {c: hp.to_oklab(c) for c in count}
    remap = {c: min(keep, key=lambda k: sum((a - b) ** 2 for a, b in zip(lab[c], lab[k]))) for c in count if c not in keep}
    for y in range(-p, cv.h + p):
        for x in range(-p, cv.w + p):
            c = cv.get(x, y)
            if c in remap:
                cv.set(x, y, remap[c])


def windmill(turn: float = 0.0) -> Canvas:
    """The halt's drainage mill, re-seated so its tower stands where the old sprite's did:
    valley_zones places it by the old 64 x 104 box, the tower's axis at x 32 and its foot on
    the box's bottom row, so the halt's track, stand and walk grid still meet it."""
    return gp.keep_foot(tower_mill(turn, 'valley'), 64, 104, dx=32 - 52)


def cogsworth_windmill(turn: float = 0.0) -> Canvas:
    return tower_mill(turn, 'cogsworth')


def props() -> dict[str, Canvas]:
    return {
        'windmill': windmill(), 'windmill_f1': windmill(math.pi / 6), 'windmill_f2': windmill(math.pi / 3),
    }
