"""Props for the Tidebloom Isles (world-atlas.md, "The connected world"; Matt, 18 Oct
19:07, following Codex's drawing): a dormant volcanic island off Driftwood Harbour,
its rainforest, the waterfall at the headwaters, the lagoon with its ferry landing and a
black-sand cove. Wet, deep green and warm; natural, not borrowed from anyone's culture.

Same rules as every prop (art-style.md): light from the upper left, canopies as a few
big leaf masses (garden_props.canopy), materials from materials.py. Run directly for a
contact sheet.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, disc, noise2, oval  # noqa: E402
import detail  # noqa: E402
import style  # noqa: E402
from garden_props import PAD, canopy, plane, rect_set, topdown_gable, topdown_roof  # noqa: E402
from materials import MATERIALS, WOOD, STONE, GOLD, RED, WTR, SLATE  # noqa: E402

# the rainforest's leaves: deeper and bluer than the valley's, with a wet bright top
JUNGLE = ['#14301F', '#1F4A2C', '#2E6638', '#4A8A44', '#7DB85A']
BASALT = MATERIALS['basalt']
CREAM = MATERIALS['cream']


def jungle_tree() -> Canvas:
    """A rainforest giant, 84 x 112: a broad, layered crown of leaf masses over a pale
    trunk with buttress roots flaring at its foot and a vine hanging down."""
    w, h = 84, 112
    cv = Canvas(w, h, pad=PAD)
    cx = w / 2
    tw = 11
    tx = int(cx - tw / 2)
    bark = ['#4A3E34', '#6E6052', '#948470', '#B4A48C', '#CFC2A8']
    style.trunk(cv, tx, 40, h, tw, bark)
    for side in (-1, 1):  # buttress roots: thin flared fins out from the foot
        for k in range(12):
            y = h - 12 + k
            x0 = int(cx + side * (tw / 2 + k * k * 0.06))
            for x in range(min(int(cx), x0), max(int(cx), x0) + 1):
                if abs(x - cx) > tw / 2 - 1:
                    cv.set(x, y, bark[3] if side < 0 else bark[1])
    # an emergent's crown: wide and layered, broader than it is tall
    lobes = [(cx - 28, 30, 14), (cx + 28, 28, 14), (cx - 12, 20, 16), (cx + 12, 18, 16), (cx - 26, 44, 12),
             (cx + 26, 44, 12), (cx, 34, 17)]
    shape = canopy(cv, lobes, JUNGLE, seed=31, clumps=True)
    style.trunk(cv, tx, 52, h, tw, bark, shape)
    for t in range(40):  # a vine hanging from the crown on the lit side
        x = int(cx - 20 + math.sin(t / 6) * 2)
        y = 56 + t
        if y < h - 8 and not (tx <= x < tx + tw):
            cv.set(x, y, JUNGLE[3] if t % 4 else JUNGLE[4])
    return cv


def tree_fern() -> Canvas:
    """A tree fern, 44 x 58: a slim furred trunk and a crown of long arching fronds."""
    w, h = 44, 58
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    for y in range(20, h):
        for dx in range(-2, 3):
            c = WOOD[2] if dx < 0 else WOOD[1]
            if (y + dx) % 3 == 0:
                c = WOOD[3] if dx < 0 else WOOD[0]
            cv.set(cx + dx, y, c)
    # fronds radiate all round the crown (seen from above and the side): a rosette of
    # long feathered leaves, the back ones darker, the lit front ones bright
    order = sorted(range(12), key=lambda k: math.sin(2 * math.pi * k / 12))  # back to front
    for k in order:
        a = 2 * math.pi * k / 12 + 0.2
        front = math.sin(a) > 0
        for t in range(20):
            x = cx + math.cos(a) * t
            y = 18 + math.sin(a) * t * 0.45 + (t * t) * 0.02
            lit = math.cos(a) < 0.3
            c = (JUNGLE[4] if t % 3 == 0 else JUNGLE[3]) if lit and front else JUNGLE[2] if front or lit else JUNGLE[1]
            cv.set(int(x), int(y), c)
            if 3 < t < 18:  # the leaflets either side of the midrib
                px, py = -math.sin(a), math.cos(a) * 0.45
                for side in (-1, 1):
                    cv.set(int(x + px * side * 1.6), int(y + py * side * 1.6 + 0.5), JUNGLE[2] if lit else JUNGLE[1])
    for (x, y) in disc(cx, 18, 2.2):
        cv.set(x, y, JUNGLE[1])
    return cv


def monstera() -> Canvas:
    """A clump of big split leaves, 40 x 30, glossy on their upper sides."""
    cv = Canvas(40, 30, pad=PAD)
    for (lx, ly, r, a) in ((12, 16, 9, -0.5), (27, 14, 10, 0.4), (20, 20, 9, 0.0), (8, 23, 7, -0.9), (32, 23, 7, 0.9)):
        leaf = oval(lx, ly, r, r * 0.7)
        for (x, y) in leaf:
            # the leaf's splits: thin gaps radiating from its middle
            ang = math.atan2(y - ly, x - lx)
            if int((ang + math.pi) * 5) % 4 == 0 and math.hypot(x - lx, y - ly) > r * 0.5:
                continue
            lit = (x - lx) + (y - ly) < 0
            cv.set(x, y, JUNGLE[4] if lit and (x + y) % 5 == 0 else JUNGLE[3] if lit else JUNGLE[2])
        cv.set(lx, ly, JUNGLE[1])
    return cv


def hibiscus() -> Canvas:
    """A flowering shrub, 34 x 28: a dark bush with big red flowers, gold at their hearts."""
    cv = Canvas(34, 28, pad=PAD)
    canopy(cv, [(10, 16, 9), (24, 15, 9), (17, 10, 9)], JUNGLE, seed=33)
    for (fx, fy) in ((8, 10), (20, 6), (26, 14), (13, 18), (22, 20)):
        for (x, y) in disc(fx, fy, 2.2):
            cv.set(x, y, RED[4] if (x - fx) + (y - fy) < 0 else RED[3])
        cv.set(fx, fy, GOLD[4])
    return cv


# The boathouse stands on piles at the lagoon's edge, its boat end over the water (Matt's
# World Logic answer 16): its piles hold it up, not the ground in front of its boat doors.
PLACEMENT = {'boathouse': 'supported'}


def boathouse() -> Canvas:
    """The ferry's boathouse at the lagoon's edge, 88 x 116 (size guide: 64 to 112 wide,
    80 to 112 tall, one storey and a loft, boat doors 40 wide at the water, a slipway 24 to
    40 wide running at least 16 into the water; Matt's World Logic answer 16). How it is
    built: a timber shed of upright boards on a timber frame, its back on the sand (the
    keeper's door is in the back wall, toward the trail) and its boat end standing out over
    the shallows on piles braced against each other; a shingled roof with its gable to the
    water, a loft door in the gable under a hoist beam with its block; the boat doors
    folded back against the front to open the boat bay 40 wide, the slip's two runners
    going down inside past a dinghy on its cradle and a lamp; out of the doors the slipway,
    28 wide, planked across its runners with cleats, running down at 1 in 3 into the
    lagoon, its lower half under the water. Oars racked on the west wall, a net drying, a
    lifebuoy, a lit window in the east bay, a ladder down to the water."""
    w, h = 88, 116
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y, wall_top, wall_bottom = 43.5, 12, 34, 34, 76
    SHINGLE = ['#2E2420', '#4A3A30', '#6A5444', '#8A7058', '#A88A6C']
    left, right, edge_y = topdown_roof(cv, ridge, apex_y, eave_y, 3, 84, SHINGLE, seed=905, moss=None)
    # re-lay its surface in whole shingles (calmer than single-pixel grain): courses 3 deep,
    # shingles 4 wide from two timbers, each course's lower edge lit, the shade slope a step
    # darker, moss in clusters near the eaves, the ridge capped with a board
    SILVER_R = ['#3A3632', '#56504A', '#766E64', '#968C80', '#B4AA9C']
    roof_px = [(x, y) for y in range(0, eave_y + 1) for x in range(0, w) if cv.get(x, y)[3]]
    roof_set = set(roof_px)
    FRESH = [WOOD[0], WOOD[1], WOOD[2], WOOD[3], WOOD[4]]  # shingles split new from the log, not yet silvered
    LICHEN = ['#7E8A70', '#A4AE90']  # grey-green lichen rosettes on the old shingles
    cuts = {}  # shingles are split by hand, 4 to 7 px wide, so each course is laid in its own widths
    for row in range(eave_y // 4 + 2):
        x, sh, line = -int(noise2(row, 0, 916) * 5), 0, {}
        while x < w:
            wd = 4 + int(noise2(sh, row, 917) * 4)
            for q in range(wd):
                line[x + q] = (sh + row * 40, q, wd)
            x, sh = x + wd, sh + 1
        cuts[row] = line
    for (x, y) in roof_px:
        if (x - 1, y) not in roof_set or (x + 1, y) not in roof_set or (x, y - 1) not in roof_set:
            continue  # (the roof's outline and verge stay as drawn)
        shade = x > ridge
        row, r = y // 4, y % 4
        sh, q, wd = cuts[row][x]  # which shingle in the course, where across it, and how wide it is
        n = noise2(sh, row, 910)
        ramp = FRESH if n > 0.9 else SILVER_R if n > 0.6 else SHINGLE
        t = (3 if n < 0.3 or n > 0.9 else 2) - (1 if shade else 0)
        c = ramp[t]
        if r == 3:
            c = ramp[max(0, t - 2)]  # the shadow each course throws on the one below, whole across
        elif q == wd - 1:
            c = ramp[max(0, t - 1)]  # the gap between two shingles, three rows long
        elif r == 0 and not shade:
            c = ramp[min(4, t + 1)]  # the course's butt edge, lit along the sunny plane
        elif r == 2 and q in (1, 2) and noise2(sh, row, 914) > 0.35:
            c = ramp[max(0, t - 1)]  # a split weathered into the shingle's foot
        if r in (1, 2) and q in (2, 3) and wd > 4 and ramp is not FRESH and noise2(sh, row, 915) > 0.66:
            c = LICHEN[1 if not shade and r == 1 else 0]  # a lichen rosette, two by two
        if y > eave_y - 9 and r in (1, 2) and q in (0, 1, 2) and noise2(sh, row, 911) > 0.6:
            c = JUNGLE[3 if r == 1 and not shade else 2] if not shade else JUNGLE[1 if r == 2 else 2]  # moss in the damp near the eaves, on whole shingles
        if abs(x - ridge) < 1.5:
            c = WOOD[4] if x < ridge else WOOD[2]  # the ridge board
        cv.set(x, y, c)
    gable = topdown_gable(cv, edge_y, 6, 81, apex_y, wall_top, WOOD, boards=True)
    for (x, y) in sorted(gable):  # the gable's boards: some bleached silver, nailed to two rails, a knot here and there
        bd, q = (x - 6) // 5, (x - 6) % 5
        if noise2(bd, 3, 918) > 0.6 and 0 < q < 4 and (x, y - 3) in gable:
            c = cv.get(x, y)
            lum = sum(c[:3]) / 3
            cv.set(x, y, SILVER_R[min(4, max(1, int(lum // 40)))])
        if q == 2 and y in (wall_top - 4, wall_top - 3, wall_top - 13, wall_top - 12) and (x, y - 2) in gable:
            cv.set(x, y, MATERIALS['iron'][2] if y % 2 else MATERIALS['iron'][1])  # a nail's head and its rust
        elif q in (1, 2) and y == wall_top - 8 and noise2(bd, 4, 919) > 0.55 and (x, y - 2) in gable:
            cv.set(x, y, WOOD[0])  # a knot
    SILVER = ['#3E3A36', '#5E5850', '#7E766A', '#A0968A', '#C0B6A8']  # boards bleached by sun and salt
    for x in range(6, 82):  # upright boards, each its own timber, lit on its west edge, a gap between
        bd = (x - 6) // 4
        n = noise2(bd, 0, 907)
        PAINTED = ['#22364A', '#34506A', '#4A6E8A', '#6A8EA8', '#90B0C4']  # boards once painted blue, peeling
        ramp = SILVER if n > 0.62 else PAINTED if n < 0.16 else WOOD
        t = 3 if n > 0.8 or 0.16 <= n < 0.3 else 2
        for y in range(wall_top, wall_bottom):
            c = ramp[t]
            if (x - 6) % 4 == 0:
                c = ramp[0]  # the gap
            elif (x - 6) % 4 == 1:
                c = ramp[min(4, t + 1)]
            if y > wall_bottom - 8:
                c = ramp[max(0, t - 1)] if (x - 6) % 4 else ramp[0]  # damp and dark low down, where the spray reaches
            if y in (wall_top + 8, wall_bottom - 10) and (x - 6) % 4 == 2:
                c = MATERIALS['iron'][2]  # nail heads on the rails behind
            if noise2(x // 2, y // 3, 908) > 0.84 and (x - 6) % 4 > 1:
                c = ramp[max(0, t - 1)]  # a knot, a stain
            elif ramp is PAINTED and noise2(x // 2, y // 2, 912) > 0.7 and (x - 6) % 4 > 1:
                c = WOOD[2]  # bare wood where the paint has flaked
            elif y > wall_bottom - 14 and noise2(x // 2, y // 2, 913) > 0.86 and (x - 6) % 4 > 1:
                c = '#D8D4C8'  # salt dried white where the spray reaches
            cv.set(x, y, c)
    # the loft door in the gable, the hoist beam over it with its block and rope
    for (x, y) in rect_set(38, 20, 12, 12):
        cv.set(x, y, WOOD[1] if 39 <= x <= 48 and y > 21 else WOOD[4] if y == 20 else WOOD[2])
    cv.hline(40, 25, 8, WOOD[0])
    for x in range(40, 50):
        cv.set(x, 16, WOOD[4]); cv.set(x, 17, WOOD[2])
    cv.set(48, 18, MATERIALS['iron'][3]); cv.set(48, 19, MATERIALS['iron'][2])
    for y in range(20, 30):
        cv.set(48, y, MATERIALS['rope'][2])
    # the boat bay: 40 wide, open on the dark inside, the slip's runners going down past a dinghy
    bx0, bx1, by0 = 24, 64, wall_bottom - 32
    lx_, ly_ = 31, by0 + 7  # the lamp hung inside: its light falls off across the back wall and the floor
    DUSK = ['#140E0C', '#1C1410', '#261C16', '#30241C', '#3E2E22']  # the boathouse's timber in its own dark
    for y in range(by0, wall_bottom):
        for x in range(bx0, bx1):
            d = math.hypot((x - lx_) * 0.7, y - ly_)
            lit = 4 if d < 6 else 3 if d < 11 else 2 if d < 17 else 1 if d < 26 else 0
            c = DUSK[lit]
            if (x - bx0) % 5 == 0 and y < by0 + 20:
                c = DUSK[max(0, lit - 1)]  # the back wall's boards, their joints
            elif (x - bx0) % 5 == 1 and y < by0 + 20 and lit >= 3:
                c = WOOD[1]  # a board's edge catching the lamp
            if y in (by0 + 9, by0 + 10) and lit >= 2:
                c = WOOD[1] if y == by0 + 9 else DUSK[lit - 1]  # the rail the tools hang from
            if y >= by0 + 20:
                c = DUSK[max(0, lit - 1)] if (y - by0) % 3 else DUSK[max(0, lit - 2)]  # the floor's planks, going back
            if x in (bx0 + 10, bx0 + 11, bx1 - 12, bx1 - 11) and y >= by0 + 18:
                c = WOOD[2] if x in (bx0 + 10, bx1 - 12) and lit >= 1 else WOOD[1] if lit >= 1 else DUSK[2]  # the runners, lit on top
            cv.set(x, y, c)
    for (x, y) in rect_set(bx1 - 10, by0 + 11, 2, 7):  # a paddle on the rail, its blade down
        cv.set(x, y, WOOD[2] if x == bx1 - 10 else WOOD[1])
    for (x, y) in rect_set(bx1 - 11, by0 + 16, 4, 4):
        cv.set(x, y, '#3A6A8A' if x < bx1 - 9 else '#2A4E68')
    for (x, y) in oval(bx1 - 4, by0 + 14, 2.5, 2.5):  # a coil of rope hung on the back wall
        cv.set(x, y, MATERIALS['rope'][2] if y < by0 + 14 else MATERIALS['rope'][1])
    for (x, y) in ((bx1 - 4, by0 + 14), ):
        cv.set(x, y, DUSK[1])
    for k, fx_ in enumerate((bx1 - 17, bx1 - 15)):  # floats hung on a nail
        for (x, y) in rect_set(fx_, by0 + 11, 2, 2):
            cv.set(x, y, ('#E8962A' if k else '#C8463A') if y == by0 + 11 else ('#B86A1A' if k else '#9A3028'))
    for (x, y) in rect_set(bx0 + 15, by0 + 11, 5, 2):  # a saw on two pegs
        cv.set(x, y, STONE[3] if y == by0 + 11 else STONE[2])
    cv.set(bx0 + 20, by0 + 11, WOOD[2]); cv.set(bx0 + 20, by0 + 12, WOOD[1])
    for (x, y) in rect_set(bx0 + 2, by0 + 5, 2, 14):  # an oar leaning in the corner
        cv.set(x, y, WOOD[3] if x == bx0 + 2 else WOOD[1])
    for (x, y) in rect_set(bx0 + 4, by0 + 15, 6, 4):  # a pot of tar and a crate by the corner
        cv.set(x, y, '#2A2420' if x < bx0 + 7 else (WOOD[2] if y == by0 + 15 else WOOD[1]))
    cv.hline(bx0 + 4, by0 + 15, 3, '#5A4A3A')
    hull_ = oval(44, wall_bottom - 8, 9, 3.5)
    for (x, y) in hull_:  # the dinghy on its cradle: white hull, a blue sheer strake, its gunwale lit
        top = y < wall_bottom - 8
        c = CREAM[3] if top and x < 44 else CREAM[2] if top else CREAM[1]
        if y == wall_bottom - 8:
            c = '#3A6A8A' if x < 46 else '#2A4E68'
        cv.set(x, y, c)
    for (x, y) in oval(44, wall_bottom - 10, 6, 1.4):  # inside the boat, its bottom boards in shade
        cv.set(x, y, WOOD[1] if x < 44 else DUSK[4])
    cv.hline(42, wall_bottom - 10, 3, WOOD[3])  # the thwart
    cv.hline(37, wall_bottom - 11, 15, WOOD[3])
    for ox_ in (37, 51):
        cv.set(ox_, wall_bottom - 12, MATERIALS['iron'][3])  # the rowlocks
    for (x, y) in rect_set(38, wall_bottom - 4, 2, 4):  # the cradle's chocks under it
        cv.set(x, y, WOOD[2] if x == 38 else WOOD[1])
    for (x, y) in rect_set(49, wall_bottom - 4, 2, 4):
        cv.set(x, y, WOOD[2] if x == 49 else WOOD[1])
    for (x, y) in rect_set(lx_, ly_ - 1, 3, 4):  # the lamp, its glow on the beam above
        cv.set(x, y, GOLD[4] if y < ly_ + 1 else GOLD[3])
    cv.set(lx_ + 1, ly_ - 2, MATERIALS['iron'][2])
    cv.hline(lx_ - 2, by0 + 3, 7, WOOD[2])
    cv.hline(bx0 - 2, by0 - 2, bx1 - bx0 + 4, WOOD[4]); cv.hline(bx0 - 2, by0 - 1, bx1 - bx0 + 4, WOOD[1])  # its lintel
    for (dx0, dx1) in ((bx0 - 12, bx0 - 2), (bx1 + 2, bx1 + 12)):  # the doors folded back against the front: ledged and braced
        west = dx0 < bx0
        for y in range(by0, wall_bottom):
            for x in range(dx0, dx1):
                bd = (x - dx0) // 5
                n = noise2(bd + (0 if west else 7), 5, 920)
                ramp = SILVER_R if n > 0.55 else WOOD
                t = 3 if west else 2
                c = ramp[t] if (x - dx0) % 5 else ramp[t - 2]  # each board its own timber, a dark joint between
                if (x - dx0) % 5 == 1:
                    c = ramp[min(4, t + 1)] if west else ramp[t]
                if y in (by0 + 4, by0 + 5, wall_bottom - 6, wall_bottom - 5):
                    c = WOOD[3 if y in (by0 + 4, wall_bottom - 6) else 1] if west else WOOD[2 if y in (by0 + 4, wall_bottom - 6) else 0]  # the ledges, lit along their tops
                elif by0 + 5 < y < wall_bottom - 6 and abs((x - dx0) - (y - by0 - 6) * (dx1 - dx0 - 1) / (wall_bottom - by0 - 12)) < 1:
                    c = WOOD[2] if west else WOOD[1]  # the brace, climbing to the hinge side
                if y > wall_bottom - 9 and noise2(x // 2, y // 2, 921) > 0.72 and (x - dx0) % 5 > 1:
                    c = '#D8D4C8'  # salt dried white low down
                cv.set(x, y, c)
        hx = dx1 - 3 if west else dx0
        for hy in (by0 + 4, wall_bottom - 6):  # the strap hinges, iron, with their nail heads
            cv.hline(hx, hy, 3, MATERIALS['iron'][3]); cv.hline(hx, hy + 1, 3, MATERIALS['iron'][1])
    for k in range(4):  # a string of net floats hung on the west door, cork and painted glass
        fx_, fy_ = bx0 - 11 + k * 2, by0 + 14 + k * 3
        cv.set(fx_ + 1, fy_ - 1, MATERIALS['rope'][2])
        for (x, y) in rect_set(fx_, fy_, 2, 2):
            cv.set(x, y, (('#E8962A', '#B86A1A'), ('#C8463A', '#9A3028'), ('#D8D0BC', '#A89E88'), ('#5A9AB8', '#3A6A8A'))[k][0 if y == fy_ else 1])
    tb0 = by0 + 12  # the ferry's times on a board nailed to the east door: cream, ruled in black
    for (x, y) in rect_set(bx1 + 4, tb0, 7, 8):
        c = '#E8DCC0' if x < bx1 + 10 else '#C8BC9C'
        if y == tb0:
            c = '#2E5A7A'
        elif (y - tb0) % 2 == 0 and bx1 + 5 <= x <= bx1 + 8:
            c = '#3A3028'
        cv.set(x, y, c)
    cv.set(bx1 + 4, tb0 + 8, WOOD[0]); cv.set(bx1 + 10, tb0 + 8, WOOD[0])

    # the east bay's window, lamplit; oars racked and a net drying on the west
    wx, wy = 72, wall_top + 8
    for y in range(wy, wy + 12):
        for x in range(wx, wx + 8):
            c = GOLD[3] if y < wy + 5 else GOLD[2]
            if x in (wx, wx + 7) or y in (wy, wy + 11) or y == wy + 5:
                c = WOOD[4] if x == wx or y == wy else WOOD[1]
            cv.set(x, y, c)
    cv.hline(wx - 1, wy + 12, 10, WOOD[4])
    for k, ox_ in enumerate((8, 11, 14)):  # oars, blades up
        for y in range(wall_top + 6, wall_bottom - 4):
            cv.set(ox_, y, WOOD[4] if k % 2 else WOOD[3])
        for (x, y) in rect_set(ox_ - 1, wall_top + 3, 3, 4):
            cv.set(x, y, '#3A6A8A' if k != 1 else '#C8463A')
    for y in range(wall_top + 4, wall_top + 16):  # a net hung to dry, its floats
        for x in range(16, 22):
            if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                cv.set(x, y, '#C8BC98' if y < wall_top + 10 else '#A89A74')
    for fx in (17, 20):
        cv.set(fx, wall_top + 15, '#E8962A')
    for (x, y) in disc(76, wall_bottom - 8, 3):  # a lifebuoy on the east wall
        d = math.hypot(x - 76, y - wall_bottom + 8)
        if d > 1.3:
            q = (x >= 76) ^ (y >= wall_bottom - 8)
            cv.set(x, y, ('#F2ECDE' if y < wall_bottom - 8 else '#C8C0B0') if q else (RED[3] if y < wall_bottom - 8 else RED[2]))
    for x in list(range(6, bx0 - 1)) + list(range(bx1 + 1, 82)):  # green weed where the spray keeps the boards wet, in clumps
        for y in range(wall_bottom - 4, wall_bottom):
            n = noise2(x // 3, (y - wall_bottom) // 2, 922)
            if n > 0.5 - (y - (wall_bottom - 4)) * 0.08:
                cv.set(x, y, JUNGLE[2] if y < wall_bottom - 2 and n > 0.65 else JUNGLE[1])
    cv.hline(74, wall_bottom - 4, 5, MATERIALS['iron'][3]); cv.hline(75, wall_bottom - 3, 3, MATERIALS['iron'][1])  # a cleat by the ladder
    for (x, y) in oval(77, wall_bottom - 2, 3, 1.2):  # the mooring line coiled on it
        cv.set(x, y, MATERIALS['rope'][3] if y < wall_bottom - 2 else MATERIALS['rope'][1])
    for (x, y) in rect_set(17, wall_bottom - 6, 4, 5):  # a bailing bucket on the sill, hooped
        c = WOOD[3] if x < 19 else WOOD[1]
        if y in (wall_bottom - 5, wall_bottom - 2):
            c = MATERIALS['iron'][2]
        cv.set(x, y, c)
    cv.hline(17, wall_bottom - 7, 4, '#24343A')
    for (x, y) in rect_set(30, wall_top + 2, 28, 5):  # the ferry's name board over the bay, painted
        c = '#2E5A7A' if 30 < x < 57 and wall_top + 2 < y < wall_top + 6 else '#E8DCC0'
        if c == '#2E5A7A' and (x // 2) % 3 and y == wall_top + 4:
            c = '#F2ECDA'  # its lettering, abstract strokes
        cv.set(x, y, c)
    for (x, y) in rect_set(66, wall_top + 2, 3, 4):  # a storm lantern on a bracket by the window
        cv.set(x, y, GOLD[4] if y < wall_top + 4 else GOLD[3])
    cv.hline(65, wall_top + 1, 5, MATERIALS['iron'][2])
    detail.overhang_shadow(cv, 6, 82, wall_top, lambda x: 3, k=2, cap=1)
    # the sill beam the front stands on, and the piles into the shallows, cross-braced
    cv.hline(5, wall_bottom, 78, WOOD[4]); cv.hline(5, wall_bottom + 1, 78, WOOD[2]); cv.hline(5, wall_bottom + 2, 78, WOOD[0])
    pile_bot = wall_bottom + 14
    for sx in (7, 20, 66, 79):
        for y in range(wall_bottom + 3, pile_bot):
            cv.set(sx, y, WOOD[3]); cv.set(sx + 1, y, WOOD[2]); cv.set(sx + 2, y, WOOD[1])
            if y > pile_bot - 4:
                cv.set(sx, y, '#3A5A54'); cv.set(sx + 1, y, '#2A4A44'); cv.set(sx + 2, y, '#24403C')  # the wet, weeded foot
            elif y > pile_bot - 7 and (y + sx) % 3 == 0:
                cv.set(sx, y, '#D8D0BC'); cv.set(sx + 1, y, '#B8B0A0')  # barnacles above the waterline
        for x in range(sx - 2, sx + 5):  # the ring the water makes round it
            cv.set(x, pile_bot, '#8ACCC8' if x in (sx - 2, sx + 4) else '#5AA8A8')
    for (a0, a1) in ((7, 20), (66, 79)):  # the braces between the piles
        for t in range(a1 - a0):
            cv.set(a0 + 2 + t, wall_bottom + 4 + t * 8 // (a1 - a0), WOOD[2])
    for y in range(wall_bottom + 3, pile_bot):  # the dark under the floor, between the piles
        for x in range(23, 66):
            if cv.get(x, y)[3] == 0:
                cv.set(x, y, '#13403E' if y < wall_bottom + 8 else '#1A5452')
    for y in range(wall_bottom - 2, pile_bot + 2):  # a ladder down the east pile to the water
        cv.set(83, y, WOOD[3]); cv.set(86, y, WOOD[1])
        if (y - wall_bottom) % 3 == 0:
            cv.hline(84, y, 2, WOOD[4])
    # the slipway: 28 wide, planked across two runners, down out of the doors into the lagoon
    s0, s1 = 30, 58
    for y in range(wall_bottom + 1, h - 2):
        k = (y - wall_bottom) / (h - 2 - wall_bottom)
        for x in range(s0, s1):
            pr = SILVER if noise2((y - wall_bottom) // 4, 1, 909) > 0.55 else WOOD
            c = pr[3] if (y - wall_bottom) % 4 else pr[1]  # the planks, each its own timber, their joints
            if (y - wall_bottom) % 4 == 1:
                c = pr[4]
            elif (y - wall_bottom) % 4 == 3:
                c = pr[2]
            if x in (s0 + 4, s0 + 5, s1 - 6, s1 - 5):
                c = WOOD[2] if (y - wall_bottom) % 4 else WOOD[0]  # the runners
            if x in (s0, s1 - 1):
                c = WOOD[1]
            if (y - wall_bottom) % 8 == 2 and x in (s0 + 13, s0 + 14):
                c = MATERIALS['iron'][3]  # a cleat
            if k > 0.45:  # under the water: the planks seen through the lagoon, green and dimmer as it deepens
                deep = k > 0.75
                SUNK = ('#5AAEA6', '#48A09C', '#3A9294') if not deep else ('#44A8A8', '#3A9EA0', '#329496')
                c = SUNK[0] if (y - wall_bottom) % 4 == 1 else SUNK[2] if (y - wall_bottom) % 4 == 0 or x in (s0 + 4, s0 + 5, s1 - 6, s1 - 5) else SUNK[1]
            cv.set(x, y, c)
    for y in range(wall_bottom + int(0.45 * (h - 2 - wall_bottom)) + 2, h - 2, 3):  # ripples lapping along its sunk edges
        for (x, d) in ((s0 - 1, -1), (s1, 1)):
            cv.set(x, y, '#8ACCC8'); cv.set(x + d, y, '#5AA8A8')
    for x in range(s0, s1):  # its far end fading into the lagoon
        if (x // 3) % 2:
            cv.set(x, h - 3, '#3A9EA0')
    for x in range(s0 - 1, s1 + 1):  # where the slip goes under, a lip of foam
        y = wall_bottom + int(0.45 * (h - 2 - wall_bottom)) + 1
        cv.set(x, y, '#D8F0EC' if x % 3 else '#A8DCD8')
    return cv


def ferry() -> Canvas:
    """The little island ferry from the side, 90 x 40, bow to the left, for the
    side-on ferry journey (journey.py): a white wooden hull with a blue stripe, a cabin
    with round windows and a short funnel. Moored in a zone it is `ferry_moored`."""
    w, h = 90, 40
    cv = Canvas(w, h, pad=PAD)
    hull = set()
    for y in range(22, 36):
        t = (y - 22) / 13
        x0 = int(4 + t * 10 + (1 - t) * 0)
        x1 = int(86 - t * 4)
        for x in range(x0, x1):
            hull.add((x, y))
    for (x, y) in hull:
        c = CREAM[3] if y < 28 else CREAM[2]
        if y in (28, 29):
            c = WTR[2]
        if y > 32:
            c = WTR[0]
        cv.set(x, y, c)
    for x in range(4, 86):
        cv.set(x, 22, WOOD[3])  # the rail
    for y in range(8, 22):  # the cabin
        for x in range(30, 72):
            c = CREAM[3] if x < 34 else CREAM[2]
            if y == 8:
                c = RED[3]
            cv.set(x, y, c)
    for wx in (38, 48, 58):
        for (x, y) in disc(wx, 14, 2.6):
            cv.set(x, y, '#9FC7E6' if (x - wx) + (y - 14) < 0 else WTR[1])
    for y in range(0, 8):  # the funnel
        for x in range(60, 66):
            cv.set(x, y, RED[3] if y > 2 else MATERIALS['iron'][1])
    return cv


def ferry_moored() -> Canvas:
    """The little island ferry moored at the pier, 92 x 46, bow to the left, in the same three-quarter view
    as the buildings (art-faults.md, rule 4): the planked deck seen from above inside a
    white gunwale, the hull's side below it with a blue stripe at the waterline, a cabin
    with a lit red roof and round windows in its front, a short funnel."""
    w, h = 92, 46
    cv = Canvas(w, h, pad=PAD)
    cy, sq = 24, 0.5  # the deck's centre line and how far its plan is foreshortened

    def half(x):  # the hull's half-width in plan: a fine bow, a full stern
        t = (x - 3) / 30
        return 14 * math.sqrt(max(0.0, min(1.0, t))) * (1 - max(0.0, (x - 84) / 20))

    deck, side = set(), set()
    for x in range(3, 89):
        hw = half(x) * sq
        if hw < 0.6:
            continue
        top, bot = int(cy - hw), int(cy + hw)
        for y in range(top, bot + 1):
            deck.add((x, y))
        for y in range(bot + 1, bot + 9 - int(max(0, 18 - x) * 0.3)):  # the side below its front edge
            side.add((x, y))
    for (x, y) in side:
        d = y - min(yy for (xx, yy) in side if xx == x)
        c = CREAM[3] if d < 2 else CREAM[2]
        if d in (4, 5):
            c = WTR[2]
        elif d >= 6:
            c = WTR[1] if x < 60 else WTR[0]
        if x > 70 and d < 4:
            c = CREAM[2] if d < 2 else CREAM[1]  # the stern turning out of the light
        cv.set(x, y, c)
    for (x, y) in deck:
        edge = (x, y - 1) not in deck or (x, y + 1) not in deck or (x - 1, y) not in deck or (x + 1, y) not in deck
        if edge:
            cv.set(x, y, CREAM[3] if y < cy else CREAM[2])  # the gunwale
        else:
            cv.set(x, y, WOOD[1] if (y - cy) % 3 == 0 else WOOD[3] if x < 64 else WOOD[2])
    # the cabin: roof (top face) and front face, the left end lit
    x0, x1, roof0, roof1, front1 = 40, 70, 9, 15, 23
    for y in range(roof0, front1):
        for x in range(x0, x1):
            if y < roof1:
                c = RED[4] if y == roof0 or x == x0 else RED[3] if x < x1 - 4 else RED[2]
            else:
                c = CREAM[3] if x < x0 + 3 else CREAM[2] if x < x1 - 2 else CREAM[1]
                if y == front1 - 1:
                    c = WOOD[1]
            cv.set(x, y, c)
    for wx in (46, 54, 62):
        for (x, y) in disc(wx, 19, 2.1):
            cv.set(x, y, '#9FC7E6' if (x - wx) + (y - 19) < 0 else WTR[1])
    for x in range(x0, x1):  # the roof's shadow on the deck behind
        if (x + 2, front1) in deck:
            r, g, b, a = cv.get(x + 2, front1)
            cv.set(x + 2, front1, (int(r * 0.7), int(g * 0.7), int(b * 0.78), a))
    # the funnel: a short cylinder on the roof, lit on its left, dark mouth on top
    for y in range(1, 11):
        for x in range(58, 65):
            cv.set(x, y, RED[4] if x < 60 else RED[3] if x < 63 else RED[2])
    for (x, y) in oval(61, 1.5, 3.4, 1.4):
        cv.set(x, y, MATERIALS['iron'][0] if y > 1 else MATERIALS['iron'][1])
    for x in range(58, 65):
        cv.set(x, 6, '#2E3A48')  # a band round it
    for px in range(10, 86, 9):  # rail posts along the near gunwale
        hw = half(px) * sq
        if hw > 2:
            cv.set(px, int(cy + hw) - 1, WOOD[0])
    return cv


def canoe() -> Canvas:
    """A dugout canoe drawn up on the sand, 52 x 14, a paddle across it."""
    cv = Canvas(52, 14, pad=PAD)
    for (x, y) in oval(26, 7, 25, 5):
        inside = ((x - 26) / 22) ** 2 + ((y - 6) / 3) ** 2 < 1
        cv.set(x, y, WOOD[1] if inside else WOOD[3] if y < 7 else WOOD[2])
    for t in range(30):
        cv.set(12 + t, 4 + t // 10, WOOD[4])
    for (x, y) in oval(43, 7, 4, 2):
        cv.set(x, y, WOOD[3])
    return cv


def black_rock(big: bool = True) -> Canvas:
    """A rounded boulder of dark volcanic rock (40 x 26, or 22 x 14), wet on its shadowed side."""
    w, h = (40, 26) if big else (22, 14)
    cv = Canvas(w, h, pad=PAD)
    pts = oval(w / 2, h / 2 + 1, w / 2 - 1, h / 2 - 1.4) | oval(w / 2 - 5, h / 2 + 2, w / 3, h / 2.6)
    pts = {(x, y) for (x, y) in pts if 0 <= x < w and 0 <= y < h}
    style.facet_stone(cv, pts, BASALT, seed=w + 7, outline=None)
    return cv


def sea_turtle() -> Canvas:
    """A green sea turtle resting on the sand, 30 x 22, head toward the sea."""
    cv = Canvas(30, 22, pad=PAD)
    shell = oval(15, 11, 10, 7)
    SHELL = ['#3A4A2A', '#5A6A38', '#7A8A4A', '#A0A868']
    for (fx, fy) in ((6, 6), (24, 6), (7, 17), (23, 17)):  # flippers
        for (x, y) in oval(fx, fy, 4, 2):
            cv.set(x, y, '#6E7E5A')
    for (x, y) in shell:
        cell = (int((x - 15) / 4) + int((y - 11) / 3)) % 2
        lit = (x - 15) + (y - 11) < 0
        cv.set(x, y, SHELL[3] if lit and cell else SHELL[2] if lit else SHELL[1] if cell else SHELL[0])
    for (x, y) in oval(15, 2, 3, 2.4):  # the head
        cv.set(x, y, '#8E9E6E' if x < 15 else '#6E7E5A')
    cv.set(14, 1, MATERIALS['iron'][0])
    return cv


def pandanus() -> Canvas:
    """A screwpine of the sandy coasts, 44 x 58: a slim ringed trunk standing on a cone
    of stilt roots, a ragged crown of long strap leaves that droop at their tips."""
    w, h = 44, 58
    cv = Canvas(w, h, pad=PAD)
    cx = w // 2
    bark = ['#4A3E34', '#6E6052', '#948470', '#B4A48C']
    for y in range(22, h - 10):  # the trunk, ringed with old leaf scars
        lean = int((y - 22) * 0.12)
        for dx in range(-2, 2):
            c = bark[2] if dx < 0 else bark[1]
            if y % 4 == 0:
                c = bark[0] if dx >= 0 else bark[1]
            cv.set(cx + dx + lean, y, c)
    base = cx + int((h - 32) * 0.12)
    for k in range(-3, 4):  # stilt roots splaying into the sand
        if k == 0:
            continue
        for t in range(12):
            x = base + int(k * t * 0.55)
            y = h - 12 + t
            cv.set(x, y, bark[3] if k < 0 else bark[1])
            if t % 4 == 0:
                cv.set(x, y, bark[0])
    order = sorted(range(14), key=lambda k: math.sin(2 * math.pi * k / 14))  # back to front
    for k in order:
        a = 2 * math.pi * k / 14 + 0.3
        lit = math.cos(a) < 0.2 and math.sin(a) < 0.6
        L = 15 + int(noise2(k, 3, 41) * 6)
        for t in range(L):
            x = cx + math.cos(a) * t
            y = 20 + math.sin(a) * t * 0.5 + (t * t) * 0.035  # drooping at the tip
            c = JUNGLE[4] if lit and t % 5 == 0 else JUNGLE[3] if lit else JUNGLE[2] if math.sin(a) > 0 else JUNGLE[1]
            cv.set(int(x), int(y), c)
            cv.set(int(x), int(y) + 1, JUNGLE[1] if not lit else JUNGLE[2])
    for (x, y) in disc(cx, 20, 2.4):
        cv.set(x, y, JUNGLE[1])
    for (fx, fy) in ((cx - 3, 24), (cx + 2, 25)):  # a hanging fruit, like a pine cone
        for (x, y) in disc(fx, fy, 2.2):
            cv.set(x, y, GOLD[3] if (x - fx) + (y - fy) < 0 else GOLD[2])
    return cv


def banana() -> Canvas:
    """A clump of wild banana, 40 x 48: two green stems and broad paddle leaves, one of
    them torn by the wind, a flower bud hanging purple under the crown."""
    w, h = 40, 48
    cv = Canvas(w, h, pad=PAD)
    for sx in (17, 23):  # the stems
        for y in range(24, h):
            cv.set(sx, y, JUNGLE[3] if sx == 17 else JUNGLE[2])
            cv.set(sx + 1, y, JUNGLE[2] if sx == 17 else JUNGLE[1])
    leaves = [(-1, 16, 17, -0.7), (1, 18, 18, -0.4), (-1, 26, 15, 0.45), (1, 27, 15, 0.6), (0, 16, 12, -1.2)]
    for k, (side, ly, L, tilt) in enumerate(leaves):
        x0 = 20
        for t in range(L):
            x = x0 + side * t if side else x0 + int(t * 0.2)
            y = ly + int(t * tilt * 0.6) - (0 if side else t)
            half = 5.2 * math.sin(math.pi * (t + 1) / (L + 1)) + 0.6
            for d in range(-int(half), int(half) + 1):
                if k == 2 and d > 0 and t % 3 == 0:
                    continue  # the torn leaf
                lit = d < 0
                cv.set(int(x), int(y + d), JUNGLE[4] if lit and abs(d) == int(half) else JUNGLE[3] if lit else JUNGLE[2])
            cv.set(int(x), int(y), JUNGLE[1])  # the midrib
    for (x, y) in oval(25, 34, 2, 3):  # the bud
        cv.set(x, y, '#6A3A5A' if x < 25 else '#4A2A44')
    return cv


def bird_of_paradise() -> Canvas:
    """A clump of bird-of-paradise, 30 x 26: stiff blue-green leaves and three flowers,
    orange crests on beaked purple bracts."""
    cv = Canvas(30, 26, pad=PAD)
    BG = ['#1E3A34', '#2E5A4E', '#4A7E6A', '#7AAE90']
    for k, (a, L) in enumerate(((-1.9, 14), (-1.3, 16), (-0.9, 12), (-2.3, 12), (-1.6, 18))):
        for t in range(L):
            x, y = 15 + math.cos(a) * t, 24 + math.sin(a) * t
            for d in (-1, 0, 1):
                cv.set(int(x) + d, int(y), BG[3] if d < 0 and t % 2 else BG[2] if d <= 0 else BG[1])
    for (fx, fy) in ((8, 8), (20, 5), (24, 12)):
        for t in range(6):  # the beak
            cv.set(fx + t, fy + 2, '#5A3A6A' if t < 4 else '#3A2A4A')
        for t in range(4):  # the crest
            cv.set(fx + 1 + t, fy + 1 - t // 2, RED[4] if t % 2 else GOLD[4])
            cv.set(fx + 1 + t, fy - t // 2, GOLD[3])
        cv.set(fx + 4, fy + 1, '#4A6AB8')  # a blue tongue
    return cv


def crab() -> Canvas:
    """A small red crab on the sand, 12 x 8, claws raised."""
    cv = Canvas(12, 8, pad=PAD)
    for (x, y) in oval(6, 4.5, 3.5, 2.4):
        cv.set(x, y, RED[4] if y < 4 else RED[3])
    for (x, y) in ((1, 2), (2, 1), (10, 2), (9, 1)):
        cv.set(x, y, RED[4])
    for (x, y) in ((1, 6), (2, 7), (10, 6), (9, 7), (3, 7), (8, 7)):
        cv.set(x, y, RED[2])
    cv.set(5, 3, '#1E1917'); cv.set(7, 3, '#1E1917')
    return cv


def rain_shelter() -> Canvas:
    """A walkers' rain shelter on the upland, 60 x 56: four timber posts under a
    shingled roof, a plank bench inside, a water jug on it. Modest and made here, not
    borrowed from anyone's temple or resort."""
    w, h = 60, 56
    cv = Canvas(w, h, pad=PAD)
    ridge, apex_y, eave_y = 29.5, 6, 26
    topdown_roof(cv, ridge, apex_y, eave_y, 2, 58, SLATE, seed=911, moss=JUNGLE)
    for y in range(eave_y + 1, h - 4):  # the dark under the roof
        for x in range(6, 54):
            cv.set(x, y, WOOD[0] if y < eave_y + 5 else '#2A3A2A')
    for x in range(10, 50):  # the bench
        for y in range(h - 16, h - 12):
            cv.set(x, y, WOOD[4] if y == h - 16 else WOOD[3] if (x % 6) else WOOD[1])
        cv.set(x, h - 12, WOOD[1])
    for lx in (14, 44):
        for y in range(h - 12, h - 7):
            cv.set(lx, y, WOOD[1])
    for (x, y) in oval(38, h - 19, 2.5, 3):  # a water jug
        cv.set(x, y, '#B86A44' if x < 38 else '#8A4A30')
    for px_ in (4, 54):  # posts, lit on their left
        for y in range(eave_y - 2, h - 2):
            cv.set(px_, y, WOOD[3]); cv.set(px_ + 1, y, WOOD[2]); cv.set(px_ + 2, y, WOOD[1])
        cv.rect(px_ - 1, h - 3, 5, 2, STONE[2])  # its stone footing
    detail.overhang_shadow(cv, 6, 54, eave_y + 1, lambda x: 3, k=2, cap=1)
    return cv


def props() -> dict[str, Canvas]:
    return {
        'jungle_tree': jungle_tree(), 'tree_fern': tree_fern(), 'monstera': monstera(), 'hibiscus': hibiscus(),
        'boathouse': boathouse(), 'island_ferry': ferry_moored(), 'canoe': canoe(), 'black_rock': black_rock(True),
        'black_rock_small': black_rock(False), 'sea_turtle': sea_turtle(),
        'pandanus': pandanus(), 'banana': banana(), 'bird_of_paradise': bird_of_paradise(), 'crab': crab(),
        'rain_shelter': rain_shelter(),
    }


if __name__ == '__main__':
    from PIL import Image
    items = {k: style.finalize(v, name=k) for k, v in props().items()}
    pad = 6
    width = sum(v.w for v in items.values()) + pad * (len(items) + 1)
    height = max(v.h for v in items.values()) + 2 * pad
    out = Image.new('RGBA', (width, height), (214, 196, 150, 255))
    x = pad
    for key, cv in items.items():
        out.alpha_composite(cv.img, (x, height - pad - cv.h))
        x += cv.w + pad
    out = out.resize((width * 4, height * 4), Image.NEAREST)
    out.save(os.environ.get('ISLE_PREVIEW', '/tmp/isle-props.png'))
    print('ok', list(items))
